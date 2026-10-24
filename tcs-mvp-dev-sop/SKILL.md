---
name: tcs-mvp-dev-sop
description: MVP 商业级交付 SOP 工作流（蒸馏自 MVP开发专家团）。当用户提出需要商业级质量的软件开发需求——开发 MVP 产品、完整 Web 应用、前后端 + 数据库 + 认证系统，或需要 PRD、技术架构、设计系统、Spec 规格契约、质量门禁、测试反作弊、部署交付中的任一环节——时使用本 skill。提供三级路径路由（轻量/迷你/标准）、六阶段流程（需求澄清→并行调研→Spec 契约→设计→开发→测试交付）、P0 绝对规则门禁（禁 emoji 图标/禁紫粉渐变/禁 AI 模板味）、Spec 12 章节契约模板与变更流程、七角色（产品经理/架构师/设计师/前端/后端/QA/运维）产出规范、质量门禁汇总（emoji 扫描/测试反作弊/生产就绪评级/回归集沉淀）。关键词：MVP、商业级交付、专家团、全流程开发、PRD、RICE、Spec、规格契约、设计系统、Design Token、质量门禁、测试反作弊、生产就绪、部署交付。
agent_created: true
---

# MVP 商业级交付 SOP 工作流

## 概述

以「流程即质量」为理念（同模型同需求，无 Harness 完成率 60%，有 Harness 达 98%）：将软件开发任务路由到三条标准路径之一，由七个虚拟角色——项目总监（大湾区靓仔）、产品经理（许清楚）、架构师（高见远）、设计师（颜好看）、前端（贾思敏）、后端（贝洛奇）、QA（严过关）、运维（卜宕机）——按六阶段 SOP 协作完成。本 SKILL.md 定义路由判定、P0 绝对规则、阶段编排与质量门禁；各角色的详细产出规范在 `references/<role>.md`，进入对应阶段时加载；深度知识库在 `references/knowledge/`，按需读取。

方法论支柱：五层工程化体系（需求工程→上下文系统→角色编排→规范约束→可观测性）、DDAD 文档驱动（PRD→架构→UIUX→Spec→代码）、五源对齐（设计变量/元数据/截图/AI 代码/渲染截图交叉对比）、Harness 门禁。

## 第一步：P0 绝对规则（凌驾一切，任何阶段任何产出必须通过）

1. **禁止 emoji 作为功能图标**。图标必须是统一描边、可矢量缩放、语义明确的 SVG 方案；具体图标库在 Spec 中锁定**一套**，全项目统一不混用。图标尺寸：16px（行内）/ 20px（按钮内）/ 24px（独立图标）。emoji 仅允许出现在用户生成内容（UGC）中。
2. **禁止紫色→粉色渐变主视觉**。禁止 `linear-gradient(135deg, #7C3AED→#A855F7→#EC4899)` 及 Indigo→Pink 任意渐变组合（红线是「Indigo→Pink 渐变 + 发光边框 + 毛玻璃」三位一体 AI 模板套路）；Indigo `#6366F1` 与 Slate Blue `#4F46E5` 作为纯色使用允许。
3. **禁止 AI 模板味**。禁止 "Lorem ipsum" / "Welcome to Our App" / "Sign up today" 空洞占位；禁止硬编码颜色值（唯一例外 `#fff` `#000`）；禁止弹跳缓动 `cubic-bezier(0.68, -0.55, 0.265, 1.55)`。

每个 Phase 门禁执行 emoji 扫描：

```bash
grep -rP '[\x{1F300}-\x{1F9FF}\x{2600}-\x{26FF}\x{2700}-\x{27BF}\x{FE00}-\x{FE0F}]' src/ --include='*.tsx' --include='*.jsx' --include='*.vue' --include='*.html' --include='*.svelte'
# 预期零匹配；发现即替换为项目锁定图标库的对应语义图标，零容忍
```

**技术栈选型无关原则**：本 SOP 规定的是规则、规范、质量标准（怎么做才算对），不规定具体选型（用什么）。选型由架构师阶段按项目实际决定并在 Spec 锁定。任何角色文档中的具体技术名称均为落地示例，非指定。

## 第二步：路径路由判定（收到请求时首先执行）

| 项目类型 | 判断条件 | 路径 |
|----------|----------|------|
| 轻量级 | 纯静态展示 / 单页面 / 无后端 | 快速路径：设计→前端开发→部署，跳过架构师/后端/QA |
| 迷你 | 2-3 个页面 + 云函数 | 精简路径：PM 简短调研→设计→前端+云函数开发→部署 |
| 标准 | 需要 API + 数据库 + 用户认证 | 标准路径：完整六阶段流程 |

判断原则：宁选轻不选重，大多数需求不应走标准全流程；需求不明确时先澄清再启动；Bug 修复类请求不走本 SOP（直接定位-修复-回归验证）。

## 第三步：执行模式

### 模式 A：多智能体协作（有 Agent 派发能力时可选）

按工作流阶段依次派发成员，分派时附带完整需求描述 + 前序阶段全部产出作为上下文；成员产出回传后汇总再转交下一阶段；禁止成员互相直连。**若所需角色子代理类型不可用，回退模式 B。**

### 模式 B：单智能体分阶段执行（默认等价实现）

按工作流逐阶段推进；进入某角色阶段前，先读取对应 `references/<role>.md` 作为该阶段的行为规范；每个阶段的输出必须符合该角色的产出模板（PRD → 架构文档 + openapi.yaml + ADR → Spec → 设计系统 + design-tokens.json → 代码 + 自检报告 → 质量报告 → 交付包）；阶段之间显式执行质量关卡自检，未通过不进入下一阶段。

## 六阶段 SOP

### Phase 0：需求澄清（一轮定调）

1. 接收需求后先内部分析：哪些信息已有、哪些不清楚
2. 一轮提问（不分多轮）：用户是谁？场景？不做会怎样？有没有参照？技术约束？
3. 用户回答后总结核心需求为 3 句话，立即进入 Phase 1

### Phase 1：并行调研（三份文档）

依次以三个角色身份调研（可并行）：产品经理（读 `references/pm.md` + `references/knowledge/industries/{对应行业}.md`，联网调研至少 3 个直接竞品 + 2 个替代方案，输出 PRD）；架构师（读 `references/architect.md` + `references/knowledge/architecture/mvp-stack.md`，做选型对比矩阵至少 3 方案，验证可行性，输出架构文档 + ADR）；设计师（读 `references/designer.md`，调研竞品 UI 方案，输出设计方向、对标品牌、配色基调）。

**一致性检查（Phase 1 结束时执行）**：PRD 要求的功能→架构文档有对应 API？架构技术约束→设计系统有对应 Token？设计师对标品牌→与 PM 竞品分析冲突？发现不一致先修正。

**唯一用户交互点**：三文档提交用户确认。确认后自动推进，仅在技术不可行或严重缺陷时通知用户。

### Phase 1.5：Spec 生成（自动，规格即契约）

基于已确认的 PRD + 架构 + UIUX 生成 Spec——锁定范围、功能、API、页面、设计 Token，之后所有阶段以 Spec 为唯一依据。**必须读取 `references/spec-template.md` 按 12 章节模板生成**。生成后直接进入 Phase 2，无需用户介入。

Spec 确认后的变更流程：小改（不新增 API 端点/不新增表/不影响超 2 个页面/不改核心流程）→ 更新变更记录继续开发；大改（任一：新增 API ≥2 个、新增表、影响 >2 页面、改核心用户流程）→ 回 Phase 0 重新澄清。

### Phase 2：设计细化

架构细化（API 端点清单 + DB Schema 详细设计，产出 `openapi.yaml`）与设计细化（读 `references/designer.md`，产出完整设计系统 Token、`design-tokens.json` + `design-tokens.css`、DESIGN.md、每页设计提示词）。

**设计门禁**：emoji 正则扫描设计输出（发现即退回，零容忍）；紫粉渐变 / 千篇一律 Hero / 硬编码颜色 → 退回重做；设计内容不得超出 Spec 范围。
**先写测试**：QA 阶段同步启动（读 `references/qa.md`），基于 Spec 的 EARS 验收标准先编写测试用例，开发按测试实现（写测试的角色 ≠ 写代码的角色）。

### Phase 3：并行开发 + 自检修复

前端（读 `references/frontend.md`）按页面清单 + 设计提示词实现；后端（读 `references/backend.md`）按 API 清单 + DB 表清单实现（先 auth→再用户→再业务）。

- 自检规则：每模块完成后 lint → type-check → test，失败自动修，最多 3 轮
- 代码组织门禁：分层（routes/controllers/services/repositories，依赖只向下）、单文件 ≤ 300 行、入口只装配零业务、单一职责、逻辑下沉 service——任一不合格退回重做
- 前端代码完成后必须执行 emoji 扫描 + 19 项视觉检查清单（见 `references/frontend.md`）
- 开发过程中不新增 Spec 以外功能；前后端完成后联调（前端用 MSW Mock 起步，类型以 openapi.yaml 为契约）
- 已知坑召回：开发开始前扫 `package.json`，从 `项目/.workbuddy/memory/pitfalls.jsonl` 召回技术栈指纹交集的坑注入「已知坑提醒」

### Phase 4：测试与交付

QA（读 `references/qa.md`）：改动影响分析→测试完整性反作弊门（5 类作弊检测）→冒烟→功能→回归→6 类失效模式核对→生产就绪 7×3 评级。**P0 缺陷必须归零才进入部署；未达 Silver 不交付商业生产。**

运维（读 `references/devops.md`）：部署（可回滚、health endpoint、备份策略、环境变量管理、最小权限）→ 部署验证（页面可达 + `/api/health` 200 + 核心流程走通）→ 整合自包含交付包。

## 质量门禁汇总

| Phase | 门禁 | 不通过后果 |
|-------|------|------------|
| 1 | 用户确认三文档（唯一交互点） | 不能进 Phase 1.5 |
| 2 | emoji 正则扫描设计输出 | 发现即退回设计师 |
| 2 | 设计反模式检查（8 红线 + P0 三规则） | 退回重做 |
| 3 | 自检循环 lint/type-check/test | 自动修最多 3 轮 |
| 3 | 代码组织门禁（分层+单文件≤300行+单一职责） | 退回重做 |
| 3 | emoji 正则扫描前端代码 | 立即替换为锁定图标库图标 |
| 3 | UI 视觉检查（19 项清单） | 退回前端重做 |
| 4 | 最终 P0 规则全量扫描（emoji/紫粉渐变/AI 模板味） | 打回对应开发 |
| 4 | P0 缺陷归零 + 生产就绪 ≥ Silver | 不能交付 |
| 4 | 部署验证（health + 核心流程） | 不能交付 |

**打回-重做上限**：最多 3 轮，连续 3 轮无进展即停下升级处理。**诊断式打回**：指明「未满足哪条验收标准 + 证据 + 期望」，不是「去改改」。**过度设计护栏**：只标三类阻断（正确性缺陷 / 需求未满足 / 契约安全数据完整性破坏），不标风格偏好与未被要求的额外特性。

## 记忆沉淀（每个项目执行）

- **踩坑闭环**：开发中遇到 lint/type/test/build/runtime 报错→归类错误家族→生成稳定签名（剥离路径行号版本）→落条 `项目/.workbuddy/memory/pitfalls.jsonl`（同签名只追加 episode 计数，300 条上限）→下次开发按技术栈指纹召回→修好且机械验证通过才标 `validated: true`
- **悬而未决登记册**：出现「定不下来/等外部条件」立即落条 `项目/docs/decisions/OPEN-DECISIONS.md`（只追加+就地关闭，每次 Phase 开始复现未决项，关闭项可升格 ADR）
- **ADR**：每条技术选型产出 MADR 格式 `项目/docs/decisions/ADR-XXX.md`（Status/Background/Decision/Consequences/Related）
- **回归集**：每个 P0 缺陷修复后沉淀为持久回归用例 `tests/regression/<缺陷名>.test.ts`
- 增量纪律：经验文件禁止整篇重写，只追加/修正具体条目

## 角色规范索引（进入阶段时 Read 对应文件）

| 文件 | 内容 | 何时读取 |
|------|------|----------|
| `references/spec-template.md` | Spec 12 章节契约模板 + 变更流程 | Phase 1.5 生成 Spec 前 |
| `references/pm.md` | 需求挖掘、RICE 评分、PRD 模板、数据埋点方案 | Phase 1 产品调研前 |
| `references/architect.md` | 选型矩阵、API/DB 设计规范、openapi.yaml、ADR、Feature Flag | Phase 1 技术调研前 / Phase 2 架构细化前 |
| `references/designer.md` | 8 红线、四层 Token 体系、设计流程、检查清单、AI 反模式 | Phase 1 设计调研前 / Phase 2 设计前 |
| `references/frontend.md` | P0 代码规范、技术栈方案、CSS 工艺、AI 痕迹检测、19 项检查清单 | Phase 3 前端开发前 |
| `references/backend.md` | 分层架构、安全 checklist、性能标准、错误处理、失效模式自检 | Phase 3 后端开发前 |
| `references/qa.md` | 先写测试、反作弊门、测试金字塔、OWASP、质量报告模板 | Phase 2 写测试前 / Phase 4 评级前 |
| `references/devops.md` | 部署方案、备份、监控告警、交付包标准 | Phase 4 部署前 |

## 深度知识库索引（`references/knowledge/`，按需读取）

| 目录 | 内容 | 何时读取 |
|------|------|----------|
| `01-standards/` | 11 篇工程纪律：spec-as-contract、test-discipline、test-integrity-anti-gaming、generated-code-failure-modes、production-readiness-scorecard、code-organization、verifier-critic-pattern、self-improving-memory、open-decisions-register、context-engineering、eval-driven-delivery | 对应角色自检/门禁前 |
| `design-systems/` | 7 篇设计资产：token-standard、design-commands（23 命令）、ui-styles-library（40 套）、color-palettes（30 套）、typography-pairings（25 套）、landing-patterns（24 种）、industry-design-systems（30 行业） | 设计系统生成前 |
| `industries/` | 5 个行业规范：saas-b2b / ecommerce / enterprise / content-platform / ai-native | Phase 1 调研前按产品类型 |
| `architecture/` | mvp-stack 选型矩阵、ai-agent-patterns、rag-knowledge-base、multi-tenant-saas | 技术选型前 / 对应产品类型架构设计时 |
| `platforms/` | wechat-miniprogram、harmonyos 平台规范 | 对应平台开发前 |
| `cost-models/` | development-costs 开发成本参考 | 技术可行性评估时 |

完整索引见 `references/knowledge/README.md`。
