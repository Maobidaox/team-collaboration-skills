#!/usr/bin/env bash
# 把本地技能打包、提交入库，并发布为 GitHub Release。
#
# 安全设计（本脚本可放在公开仓库，本身不含任何凭证）：
#   1. 令牌不硬编码、不写入仓库，仅在运行时从 macOS keychain 或 GH_TOKEN 取得
#   2. 令牌写入 600 权限的临时文件供 curl 以 -H @file 读取，不出现在进程命令行中，
#      因此同机其他用户无法通过 ps 看到令牌
#   3. 令牌不通过环境变量传给子进程，脚本退出时临时文件随临时目录一并删除
#   4. 建议把令牌配置为 fine-grained 且仅对 team-collaboration-skills 仓库授权，
#      这样即使脚本副本被篡改，泄露面也仅限这一个仓库
set -euo pipefail

REPO_OWNER="${REPO_OWNER:-zengshuai2-lgtm}"
REPO_NAME="${REPO_NAME:-team-collaboration-skills}"
BRANCH="main"
SKILLS_HOME="${WORKBUDDY_SKILLS_HOME:-$HOME/.workbuddy/skills}"
PACKAGER="/Applications/WorkBuddy.app/Contents/Resources/app.asar.unpacked/resources/plugins/workbuddy-builtin/skills/skill-creator/scripts/package_skill.py"

usage() {
  cat <<'EOF'
用法:
  ./scripts/release.sh <skill-name> <version> [选项]

参数:
  skill-name            技能名，如 tcs-software-team-sop
                        源码需位于 ~/.workbuddy/skills/<skill-name>/
  version               版本号，格式 vX.Y.Z，如 v0.2.0

选项:
  --source-expert TEXT  来源专家团名，首次收录时必填
  --desc TEXT           一句话说明，首次收录时必填
  --force               同名 Release 已存在时先删除再重建
  -h, --help            显示本帮助

环境变量:
  GH_TOKEN              不设置时自动从 macOS keychain 读取 github.com 令牌
EOF
}

log() { printf '==> %s\n' "$*"; }
die() { printf '错误: %s\n' "$*" >&2; exit 1; }

SKILL=""
VERSION=""
SOURCE_EXPERT=""
DESC=""
FORCE=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --source-expert) SOURCE_EXPERT="${2:-}"; shift 2 ;;
    --desc) DESC="${2:-}"; shift 2 ;;
    --force) FORCE=1; shift ;;
    -h | --help) usage; exit 0 ;;
    -*) die "未知选项: $1" ;;
    *)
      if [[ -z $SKILL ]]; then
        SKILL="$1"
      elif [[ -z $VERSION ]]; then
        VERSION="$1"
      else
        die "多余参数: $1"
      fi
      shift ;;
  esac
done

[[ -n $SKILL && -n $VERSION ]] || { usage >&2; die "缺少技能名或版本号"; }
[[ $SKILL == tcs-* ]] || die "技能名必须以 tcs- 开头: $SKILL"
[[ $VERSION =~ ^v[0-9]+\.[0-9]+\.[0-9]+$ ]] || die "版本号格式须为 vX.Y.Z: $VERSION"
[[ -f "$SKILLS_HOME/$SKILL/SKILL.md" ]] || die "找不到技能源码: $SKILLS_HOME/$SKILL/SKILL.md"

[[ -f $PACKAGER ]] || PACKAGER=""

WORK_DIR="$(mktemp -d)"
trap 'rm -rf "$WORK_DIR"' EXIT
HDR_FILE="$WORK_DIR/gh.header"

# 令牌一律写进临时文件，再交给 curl 的 -H @file 读取；
# printf 是 shell 内建命令，令牌不会出现在任何进程的命令行里。
if [[ -n ${GH_TOKEN:-} ]]; then
  (umask 077; printf 'Authorization: Bearer %s\n' "$GH_TOKEN" > "$HDR_FILE")
else
  command -v security >/dev/null 2>&1 || die "未设置 GH_TOKEN，且本机缺少 security 命令"
  (umask 077; { printf 'Authorization: Bearer '; security find-internet-password -s github.com -w; printf '\n'; } > "$HDR_FILE")
fi
[[ $(wc -c < "$HDR_FILE") -gt 30 ]] || die "取不到 GitHub 令牌，请先设置 GH_TOKEN"

log "打包 $SKILL"
if [[ -n $PACKAGER ]]; then
  python3 "$PACKAGER" "$SKILLS_HOME/$SKILL" "$WORK_DIR" >/dev/null 2>&1 \
    || die "打包校验未通过，请先修复技能结构"
else
  command -v zip >/dev/null 2>&1 || die "缺少 zip，无法打包"
  (cd "$SKILLS_HOME" && zip -q -r "$WORK_DIR/$SKILL.zip" "$SKILL")
fi
PKG="$WORK_DIR/$SKILL.zip"
[[ -f $PKG ]] || die "未生成技能包: $PKG"

SKILL="$SKILL" VERSION="$VERSION" PKG="$PKG" SKILL_DIR="$SKILLS_HOME/$SKILL" \
  REPO_OWNER="$REPO_OWNER" REPO_NAME="$REPO_NAME" BRANCH="$BRANCH" \
  SOURCE_EXPERT="$SOURCE_EXPERT" DESC="$DESC" FORCE="$FORCE" HDR_FILE="$HDR_FILE" \
  python3 - <<'PY'
import base64, json, os, re, subprocess, sys

owner, name = os.environ["REPO_OWNER"], os.environ["REPO_NAME"]
branch = os.environ["BRANCH"]
skill, version = os.environ["SKILL"], os.environ["VERSION"]
pkg, skill_dir = os.environ["PKG"], os.environ["SKILL_DIR"]
hdr_file = os.environ["HDR_FILE"]
force = os.environ["FORCE"] == "1"
source_expert, desc = os.environ.get("SOURCE_EXPERT", ""), os.environ.get("DESC", "")

base = f"https://api.github.com/repos/{owner}/{name}"
# 令牌经 -H @file 传入，进程命令行中不可见
H = ["-H", f"@{hdr_file}", "-H", "Accept: application/vnd.github+json"]


def curl(method, url, data=None, upload=None):
    args = ["curl", "-sS", "-X", method, url, *H]
    if data is not None:
        args += ["-d", json.dumps(data)]
    if upload is not None:
        args += ["-H", "Content-Type: application/zip", "--data-binary", f"@{upload}"]
    r = subprocess.run(args, capture_output=True, text=True)
    out = (r.stdout or "").strip()
    if r.returncode != 0:
        sys.exit(f"请求失败: {method} {url}")
    return json.loads(out) if out else {}


def make_blob(data):
    return curl("POST", f"{base}/git/blobs",
                {"content": base64.b64encode(data).decode(), "encoding": "base64"})["sha"]


# README：已有条目则更新版本，无则插入新行
meta = curl("GET", f"{base}/contents/README.md")
readme = base64.b64decode(meta["content"]).decode() if meta.get("content") else ""

row = next((ln for ln in readme.splitlines() if ln.startswith(f"| [{skill}]({skill}/) |")), None)
if row:
    cells = row.split("|")
    if len(cells) >= 6:
        cells[2] = f" {version} "
        if source_expert:
            cells[3] = f" {source_expert} "
        if desc:
            cells[4] = f" {desc} "
        cells[5] = f" [{skill}.zip](packages/{skill}.zip) "
        readme = readme.replace(row, "|".join(cells), 1)
    source_expert = source_expert or row.split("|")[3].strip()
    desc = desc or row.split("|")[4].strip()
else:
    missing = [f for f, v in (("--source-expert", source_expert), ("--desc", desc)) if not v]
    if missing:
        sys.exit("首次收录需提供: " + "、".join(missing))
    new_row = (f"| [{skill}]({skill}/) | {version} | {source_expert} | {desc} | "
               f"[{skill}.zip](packages/{skill}.zip) |")
    lines = readme.splitlines()
    idx = max((i for i, ln in enumerate(lines) if ln.startswith("| [")), default=None)
    if idx is None:
        idx = next((i for i, ln in enumerate(lines) if re.match(r"^\|[-|\s]+\|$", ln)), None)
    if idx is None:
        sys.exit("README 中找不到收录技能表格，请手动补充后重试")
    lines.insert(idx + 1, new_row)
    readme = "\n".join(lines) + "\n"

entries = []
for root, dirs, files in os.walk(skill_dir):
    dirs[:] = [d for d in dirs if d not in (".git", "__pycache__")]
    for fname in files:
        if fname == ".DS_Store":
            continue
        path = os.path.join(root, fname)
        rel = os.path.relpath(path, skill_dir).replace(os.sep, "/")
        with open(path, "rb") as fh:
            entries.append({"path": f"{skill}/{rel}", "mode": "100644",
                            "type": "blob", "sha": make_blob(fh.read())})

with open(pkg, "rb") as fh:
    entries.append({"path": f"packages/{skill}.zip", "mode": "100644",
                    "type": "blob", "sha": make_blob(fh.read())})
entries.append({"path": "README.md", "mode": "100644", "type": "blob",
                "sha": make_blob(readme.encode("utf-8"))})

# 先检查版本冲突，避免提交了却没有 Release
for existing in curl("GET", f"{base}/releases"):
    if existing.get("tag_name") == version:
        if not force:
            sys.exit(f"Release {version} 已存在，加 --force 覆盖或换版本号")
        curl("DELETE", f"{base}/releases/{existing['id']}")
if curl("GET", f"{base}/git/refs/tags/{version}").get("object"):
    if not force:
        sys.exit(f"标签 {version} 已存在，加 --force 覆盖或换版本号")
    curl("DELETE", f"{base}/git/refs/tags/{version}")

print("==> 提交到 %s/%s (%s)" % (owner, name, branch))
ref = curl("GET", f"{base}/git/ref/heads/{branch}")
base_commit = ref["object"]["sha"]
base_tree = curl("GET", f"{base}/git/commits/{base_commit}")["tree"]["sha"]
tree = curl("POST", f"{base}/git/trees", {"base_tree": base_tree, "tree": entries})
commit = curl("POST", f"{base}/git/commits", {
    "message": f"发布 {skill} {version}", "tree": tree["sha"], "parents": [base_commit]})
curl("PATCH", f"{base}/git/refs/heads/{branch}", {"sha": commit["sha"]})

body = f"技能 `{skill}` {version}"
if source_expert:
    body += f"\n\n来源专家：{source_expert}"
if desc:
    body += f"\n\n{desc}"
body += f"""

## 安装

```bash
mkdir -p ~/.workbuddy/skills
unzip -o {skill}.zip -d ~/.workbuddy/skills
```

或在仓库内执行 `./scripts/install.sh {skill}`，装好后重启会话即可使用。
"""

print("==> 创建 Release %s" % version)
release = curl("POST", f"{base}/releases", {
    "tag_name": version, "name": f"{skill} {version}", "body": body,
    "draft": False, "prerelease": False})
asset = curl("POST",
             f"https://uploads.github.com/repos/{owner}/{name}/releases/{release['id']}"
             f"/assets?name={skill}.zip", upload=pkg)

print()
print("提交:     %s" % commit["sha"][:7])
print("Release:  %s" % release["html_url"])
print("技能包:   %s" % asset.get("browser_download_url", "(上传失败)"))
PY
