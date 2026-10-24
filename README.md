# Team collaboration skills

收录由 WorkBuddy 专家团蒸馏而来的协作类技能，是本库的**总分类入口**。

- `tcs-<name>/` 等子目录：技能源码，可直接复制到 WorkBuddy 技能目录使用
- `packages/`：同样内容打包好的技能包（`.zip`），可直接导入 WorkBuddy
- `scripts/install.sh`：一条命令安装技能

## 命名规范

库内技能统一以 `tcs-` 前缀命名（`tcs` = Team collaboration skills），
形如 `tcs-<skill-name>`。技能最终会平铺安装到 `~/.workbuddy/skills/`，
带前缀才能一眼看出归属，也避免与其他来源的技能重名。

## 收录技能

| 技能 | 版本 | 来源专家 | 说明 | 技能包 |
|------|------|---------|------|--------|
| [tcs-software-team-sop](tcs-software-team-sop/) | v0.1.0 | software-company 软件开发团队 | SOP 驱动的软件开发工作流：需求路由判定（快速模式 / BugFix / 标准 SOP / 部分工作流）、四角色协作规范（产品经理、架构师、工程师、QA）、质量关卡（IS_PASS 全局一致性审查、QA 智能路由、2 轮测试上限、任务分解 ≤ 5） | [tcs-software-team-sop.zip](packages/tcs-software-team-sop.zip) |
| [tcs-mvp-dev-sop](tcs-mvp-dev-sop/) | v0.1.0 | MVP开发专家团 | MVP 商业级交付 SOP：三级路径路由 + 六阶段流程 + 七角色协作 + Spec 契约与质量门禁 | [tcs-mvp-dev-sop.zip](packages/tcs-mvp-dev-sop.zip) |
| [tcs-senior-developer](tcs-senior-developer/) | v0.1.0 | senior-developer（高级开发工程师） | 高级全栈开发工程师工作流：三阶段铁律工作流（计划→写验报→交付清单）+ 全栈/前端/浏览器自动化三条子能力路由 | [tcs-senior-developer.zip](packages/tcs-senior-developer.zip) |
| [tcs-senior-fullstack-engineer](tcs-senior-fullstack-engineer/) | v0.1.0 | senior-fullstack-engineer（高级全栈工程师） | 端到端软件交付工作流：七步交付链路（对齐目标→拆解→方案→编码→测试→上线→复盘）+ 九项核心能力，面向需求分析、架构设计、多语言实现、性能调优、CI/CD 与线上排障 | [tcs-senior-fullstack-engineer.zip](packages/tcs-senior-fullstack-engineer.zip) |
| [tcs-python-senior-dev](tcs-python-senior-dev/) | v0.1.0 | python-senior-dev（资深 Python 全栈开发专家 xtgxiso） | 资深 Python 全栈开发工作流：17 份领域知识库场景路由（FastAPI/Django/前端/SQL优化/pytest/安全/性能/Docker/AI 六层栈）+ 10 条输出铁律 + 四段式输出 + 代码质量检查清单 | [tcs-python-senior-dev.zip](packages/tcs-python-senior-dev.zip) |
| [tcs-web-dev](tcs-web-dev/) | v0.1.0 | web（网站开发与部署专家 鹏城信息AI专家） | 网站开发与部署工作流：Phase 0-5 六阶段（澄清→选型→编码→调试→质量→部署）+ 框架决策树 + 前端高频陷阱排障 + Core Web Vitals/SEO/a11y 检查清单 + 部署平台对比与回滚预案 | [tcs-web-dev.zip](packages/tcs-web-dev.zip) |
| [tcs-wechat-miniprogram](tcs-wechat-miniprogram/) | v0.1.0 | we-chat-miniprogram-developer（微信小程序开发专家 小程达） | 微信小程序开发与生态集成工作流：平台铁律（域名白名单/HTTPS/主包2MB/无DOM/setData 节制）+ 四步工作流（架构配置→核心开发→性能优化→测试提审）+ 核心代码模板（请求层/支付/性能页），内置小程序框架、Skyline、TDesign 组件库、UI 设计四套按需知识库 | [tcs-wechat-miniprogram.zip](packages/tcs-wechat-miniprogram.zip) |
| [tcs-java-development](tcs-java-development/) | v0.1.0 | java-development-expert（高级 Java 开发工程师 凯文） | 面向真实代码库的高级 Java 开发工作流：首轮项目侦察（先确认版本再给方案）+ 五种任务模式（功能开发/缺陷修复/代码审查/架构设计/诊断）+ 工程标准（DI/事务/迁移兼容/线程池/安全）+ 四层测试策略，附 Java 工程 Playbook 与三套交付模板 | [tcs-java-development.zip](packages/tcs-java-development.zip) |

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

### 安全

发布脚本不放在本仓库，另置于私有仓库：技能库对外可见，但维护者所用的
自动化脚本不外露、也无法被他人提交 PR 篡改。

技能发布所需的令牌是 fine-grained 类型，仅对本仓库授予 Contents 读/写权限，
即便令牌泄露，影响范围也只限这一个仓库。

