# Team collaboration skills

由 WorkBuddy 专家团蒸馏而来的 Agent Skill 库，收录多智能体团队协作类工作流。
每个子目录是一个独立 skill，遵循标准结构：`SKILL.md`（触发条件 + 工作流编排）+
`references/`（角色/领域详细规范，按需加载）。

## 收录清单

| Skill | 来源专家 | 说明 |
|-------|---------|------|
| [software-team-sop](software-team-sop/) | software-company 软件开发团队 | SOP 驱动的软件开发工作流：需求路由判定（快速模式/BugFix/标准 SOP/部分工作流）、四角色协作规范（产品经理/架构师/工程师/QA）、质量关卡（IS_PASS 全局一致性审查、QA 智能路由、2 轮测试上限、任务分解 ≤5） |

## 安装使用

将某个 skill 目录复制到 WorkBuddy 的用户级 skill 目录即可全局启用：

```bash
git clone https://github.com/zengshuai2-lgtm/team-collaboration-skills.git
cp -r team-collaboration-skills/software-team-sop ~/.workbuddy/skills/
```

重启会话后，说出匹配触发词（如「帮我开发一个贪吃蛇游戏」「写个 PRD」「修复这个 Bug」）即可自动触发。

## 收录规范

- 每个 skill 必须包含 `SKILL.md`，frontmatter 含 `name`、`description`（含触发场景与关键词）、`agent_created: true`
- 详细角色规范、模板放 `references/`，保持 SKILL.md 精简（渐进式披露）
- 新增 skill 时同步更新本 README 的收录清单
