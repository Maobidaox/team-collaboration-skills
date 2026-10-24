# Team collaboration skills

收录由 WorkBuddy 专家团蒸馏而来的协作类技能，是本库的**总分类入口**。

- `tcs-<name>/` 等子目录：技能源码，可直接复制到 WorkBuddy 技能目录使用
- `packages/`：同样内容打包好的技能包（`.zip`），可直接导入 WorkBuddy
- `scripts/install.sh`：一条命令安装技能
- `scripts/release.sh`：一条命令完成打包、入库与发布 Release

## 命名规范

库内技能统一以 `tcs-` 前缀命名（`tcs` = Team collaboration skills），
形如 `tcs-<skill-name>`。技能最终会平铺安装到 `~/.workbuddy/skills/`，
带前缀才能一眼看出归属，也避免与其他来源的技能重名。

## 收录技能

| 技能 | 版本 | 来源专家 | 说明 | 技能包 |
|------|------|---------|------|--------|
| [tcs-software-team-sop](tcs-software-team-sop/) | v0.1.0 | software-company 软件开发团队 | SOP 驱动的软件开发工作流：需求路由判定（快速模式 / BugFix / 标准 SOP / 部分工作流）、四角色协作规范（产品经理、架构师、工程师、QA）、质量关卡（IS_PASS 全局一致性审查、QA 智能路由、2 轮测试上限、任务分解 ≤ 5） | [tcs-software-team-sop.zip](packages/tcs-software-team-sop.zip) |

## 安装

### 方式一：下载技能包（推荐）

从 [Releases](https://github.com/zengshuai2-lgtm/team-collaboration-skills/releases) 下载
`tcs-software-team-sop.zip`，解压到 WorkBuddy 用户级技能目录：

```bash
mkdir -p ~/.workbuddy/skills
unzip -o tcs-software-team-sop.zip -d ~/.workbuddy/skills
```

### 方式二：用安装脚本

```bash
git clone https://github.com/zengshuai2-lgtm/team-collaboration-skills.git
cd team-collaboration-skills
./scripts/install.sh tcs-software-team-sop           # 从技能包安装
./scripts/install.sh tcs-software-team-sop --source  # 从源码目录安装
./scripts/install.sh --all                           # 安装全部技能
```

### 方式三：手动复制

把 `tcs-software-team-sop/` 整个目录复制到 `~/.workbuddy/skills/`。

安装完成后**重启会话**，说出匹配触发词（如「帮我开发一个贪吃蛇游戏」「写个 PRD」「修复这个 Bug」）即可自动触发。

## 发布与收录规范

- 技能源码结构：`SKILL.md`（触发条件 + 工作流编排）+ `references/`（详细规范，按需加载）
- 技能名、目录名、`packages/<skill>.zip` 三者保持一致，且都以 `tcs-` 开头
- `SKILL.md` 的 frontmatter 必须包含 `name`、`description`（含触发场景与关键词）、`agent_created: true`
- 技能包用 WorkBuddy 的 skill-creator 打包脚本生成，确保结构校验通过

新增技能时按此顺序：以 `tcs-<name>` 放入源码目录 → 生成 `packages/tcs-<name>.zip` →
更新本 README 收录清单 → 打 Release 标签并附上技能包。
这四步可用 `./scripts/release.sh tcs-<name> v<x.y.z>` 一条命令完成。
