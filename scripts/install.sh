#!/usr/bin/env bash
# 安装本仓库收录的 WorkBuddy 技能。
set -euo pipefail

SKILLS_HOME="${WORKBUDDY_SKILLS_HOME:-$HOME/.workbuddy/skills}"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PACKAGES_DIR="$REPO_ROOT/packages"

usage() {
  cat <<'EOF'
用法:
  ./scripts/install.sh <skill-name> [--source]    安装指定技能
  ./scripts/install.sh --all [--source]           安装全部技能

选项:
  --source               从仓库源码目录复制，而非解压 packages/ 下的技能包
  -h, --help             显示本帮助

安装位置默认为 ~/.workbuddy/skills，可用环境变量 WORKBUDDY_SKILLS_HOME 覆盖。
EOF
}

log() { printf '==> %s\n' "$*"; }
die() { printf '错误: %s\n' "$*" >&2; exit 1; }

ALL=0
SOURCE_MODE=0
NAMES=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --all) ALL=1 ;;
    --source) SOURCE_MODE=1 ;;
    -h | --help) usage; exit 0 ;;
    -*) die "未知选项: $1" ;;
    *) NAMES+=("$1") ;;
  esac
  shift
done

if [[ $ALL -eq 1 ]]; then
  NAMES=()
  if [[ $SOURCE_MODE -eq 1 ]]; then
    for dir in "$REPO_ROOT"/*/; do
      [[ -f "$dir/SKILL.md" ]] && NAMES+=("$(basename "$dir")")
    done
  else
    for zip in "$PACKAGES_DIR"/*.zip; do
      [[ -e "$zip" ]] && NAMES+=("$(basename "$zip" .zip)")
    done
  fi
fi

if [[ ${#NAMES[@]} -eq 0 ]]; then
  usage >&2
  die "未指定要安装的技能"
fi

mkdir -p "$SKILLS_HOME"

for name in "${NAMES[@]}"; do
  if [[ $SOURCE_MODE -eq 1 ]]; then
    src="$REPO_ROOT/$name"
    [[ -f "$src/SKILL.md" ]] || die "找不到技能源码: $src/SKILL.md"
    rm -rf "$SKILLS_HOME/$name"
    cp -R "$src" "$SKILLS_HOME/"
    log "已安装 $name（源码目录）→ $SKILLS_HOME/$name"
  else
    pkg="$PACKAGES_DIR/$name.zip"
    [[ -f "$pkg" ]] || die "找不到技能包: $pkg"
    command -v unzip >/dev/null 2>&1 || die "缺少 unzip，无法解压技能包（可改用 --source）"
    rm -rf "$SKILLS_HOME/$name"
    unzip -q -o "$pkg" -d "$SKILLS_HOME"
    log "已安装 $name（技能包）→ $SKILLS_HOME/$name"
  fi
done

log "完成。重启 WorkBuddy 会话后即可生效。"
