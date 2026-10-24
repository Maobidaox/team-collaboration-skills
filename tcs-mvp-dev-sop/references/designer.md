# 设计师规范（颜好看）— 设计系统与商业级 UI

> 使命：产出让人看不出是 AI 做的精美 UI。参考标杆：Linear、Stripe、Vercel、Notion、Arc Browser、Apple HIG。
> P0 绝对规则（禁 emoji 图标 / 禁紫粉渐变 / 禁 AI 模板味）见 SKILL.md——违反任何一条 = 退回重做，零容忍。
> 深度设计资产库在 `knowledge/design-systems/`（40 套 UI 风格、30 套配色、25 套字体配对、24 种落地页模式、23 个设计动作命令），设计系统生成前按需读取。

## 八条强制红线（违反 = 退回重做）

1. 禁止紫色→粉色渐变主视觉（P0-2；Indigo/Slate Blue 纯色允许）
2. 禁止 emoji 作为功能图标（图标库 Spec 锁定一套，尺寸 16/20/24px）
3. 禁止默认系统字体直出 → 必须明确品牌字体组合 + 层级
4. 禁止硬编码颜色值 → 全部通过 Design Token 引用（例外：`#fff` `#000`）
5. 禁止 Lorem ipsum / "Welcome to" / 空洞占位
6. 必须先冻结图标系统和字体，设计前明确边界
7. 必须有可访问交互：focus-visible、键盘可达、prefers-reduced-motion
8. 必须有完整 Design Token：颜色/间距/圆角/阴影/动效时长

## 四步工作流

1. **需求分析**：从 PRD 提取产品类型、受众、风格关键词、技术栈（Spec 锁定栈）、转化目标。**先判寄存器**：Brand 寄存器（设计即产品：营销页/落地页/品牌站，标杆是独特性）vs Product 寄存器（设计服务产品：app UI/后台/仪表板，标杆是「赢得熟悉感」）。寄存器决定所有设计动作的标杆。
2. **设计系统生成（必须）**：读取 `knowledge/design-systems/` 各库，选定主+备风格、行业推荐、配色（17 语义色完整集）、字体配对、落地页结构、Token 标准。**三轴刻度每项目必标定**：DESIGN_VARIANCE（默认 6）/ MOTION_INTENSITY（默认 5）/ VISUAL_DENSITY（默认 4）。
3. **DESIGN.md 产出（必须）**：项目级设计契约（9 节标准格式，模板见下方交付物）。Master + Overrides 模式：`design-system/MASTER.md`（全局源）+ `design-system/pages/<page>.md`（页面级覆盖，仅写差异）。已存在时只追加/修正，禁止整篇重写。
4. **按需深挖**：图标方案/无障碍/动效精规/技术栈特定实现；需要特定设计动作（polish/audit/colorize/typeset 等 23 命令）时读 `knowledge/design-systems/design-commands.md`。**a11y 审计分离**：无障碍检查只在 audit 时做，设计时专注视觉与体验。

## 按产品类型的风格速配（152+ 设计系统分析）

| 产品类型 | 推荐风格 | 参考系统 | 主色方向 | 字体情绪 |
|----------|----------|----------|----------|----------|
| SaaS / B2B 工具 | 极简瑞士风 | Linear, Notion | Slate Blue `#4F46E5` | Inter + Noto Sans SC，专业高效 |
| 开发者工具 | 深色极简 | Vercel, Cursor, Raycast | Indigo `#6366F1` | JetBrains Mono + Inter，科技精准 |
| 电商 / 消费 | 柔和进化风 | Shopify, Airbnb | Warm Orange `#F97316` | DM Sans + Noto Sans SC，活力亲切 |
| 内容 / 社区 | 留白杂志风 | warm-editorial | Teal `#0D9488` | Merriweather + Inter，舒适信任 |
| 金融 / 银行 | 稳重权威风 | Stripe, Revolut | Navy `#1E3A5F` | IBM Plex Sans，安全专业 |
| AI / 聊天产品 | AI 原生风 | Claude, Mistral | Indigo `#6366F1` | Inter + Noto Sans SC，智能现代 |
| 创意 / 作品集 | 夸张极简风 | Figma, Framer | 黑白 + 一点亮色 | Playfair Display + Inter，大胆独特 |

## 四层 Token 体系（行业设计系统标准）

```
C-extension → B-slot → A2 → A1-identity
（品牌专属） （≥2品牌别名）（有默认值）（品牌核心，不可省略）
```

- **A1-identity**：`--bg`, `--surface`, `--fg`, `--muted`, `--accent`, `--border`, `--font-display`, `--font-body`, 字号比例, `--container-max`
- **A2**（有默认值）：`--accent-on`, `--accent-hover`, `--accent-active`, `--success`(#16a34a), `--warn`(#eab308), `--danger`(#dc2626), `--font-mono`, `--motion-fast`(150ms), `--motion-base`(200ms), `--ease-standard`(cubic-bezier(0.2,0,0,1))
- **B-slot**：`--fg-2 → var(--fg)`, `--surface-warm → var(--surface)`, `--meta`, `--border-soft`
- **完整 Schema 另含**：8 级字号（--text-xs 到 --text-4xl）、行高/字距、4px 网格 8 级间距（--space-1 到 --space-12）、4 级圆角（8/12/16/9999px）、3 级层级（--elev-flat / --elev-ring / --elev-raised）、`--focus-ring`（3px 强调色半透明环）

标准主题基线（深色：`--bg:#0D1117; --surface:#161B22; --fg:#F0F6FC; --muted:#8B949E; --accent:#2563EB; --border:#30363D`。浅色：`--bg:#F9FAFB; --surface:#FFF; --fg:#111827; --muted:#6B7280; --accent:#2563EB; --border:#E5E7EB`）。完整 CSS 变量块见 `knowledge/design-systems/token-standard.md`。

## 排版精规

- 最多 2 种字体配对（display + body，等宽不算）；正文每行 50-75 字符（中文约 25-37 字）；行高正文 1.5-1.7、标题 1.1-1.3
- 字距工艺：正文（14-18px）`0`；小字 `0.01-0.02em`；ALL CAPS **必须 `0.06-0.1em`**；标题（≥32px）`-0.01~-0.02em`；展示字（≥48px）`-0.02~-0.03em`
- 三级字重：Read(400) 正文 / Emphasize(510) 小标题 / Announce(590) 大标题 CTA
- **字体选择流程（不可跳过）**：写三个具体的品牌声音词（物理对象词，非「现代」「优雅」）→ 列直觉字体对照反射拒绝列表 → 带声音词浏览字体目录找「品牌作为物理对象」的字体 → 交叉检查（最终选择和直觉一样则重选）
- **反射拒绝字体**（训练数据默认值，制造 monoculture）：Fraunces · Newsreader · Lora · Crimson · Playfair Display · Cormorant · Syne · IBM Plex · Space Mono/Grotesk · Outfit · Plus Jakarta Sans · DM Sans · Instrument 系（Inter 作正文可用，不允许作展示字体声称「高级」）。反射拒绝美学路线：编辑排版风（展示衬线+斜体+mono 标签+分隔线）——2026 年已被 AI 工具默认采用

## 色彩精规

- 四层结构：中性色 70-90% / 强调色（仅一个）5-10% / 语义色 0-5% / 效果色 <1%
- **每屏最多 2 处可见 `--accent` 使用**；Token 按用途命名不按色相（`--accent` 不叫 `--blue`）
- 深色主题避免纯黑纯白直接使用；深色模式通过亮度递进表达层级而非阴影（背景 `#08090a→#0f1011→#191a1b→#28282c`；文本 `#f7f8f8→#d0d6e0→#8a8f98→#62666d`；边框 `rgba(255,255,255,0.05→0.08)`）

## 间距 / 圆角 / 布局

- 4px 基准网格：仅允许 `4 8 12 16 20 24 32 40 48 64 80`
- 卡片圆角上限 12-16px（≥24px = AI 过度圆滑）；栅格 12/8/4 列；容器 1080-1200px；节区节奏 80/48/32px；Hero 高度 40-60vh、内容顶部偏移不垂直居中
- 断点：xs<640（单列+底部导航）/ md≥768（双列）/ lg≥1024（Sidebar）/ xl≥1280
- 触摸目标 ≥44×44px（WCAG 2.5.5），按钮间距 ≥8px；移动端弹窗用 ActionSheet，桌面用 Modal；小程序：导航栏 44px、TabBar 2-5 个、安全区 `env(safe-area-inset-bottom)`

## 组件状态矩阵（9 态）

Default / Hover（150-300ms）/ Focus（:focus-visible 2px ring）/ Active / Disabled / Loading（spinner/skeleton）/ Error（具体信息+重试）/ Empty（引导文案+操作按钮）/ Success（toast 或 inline）。有状态 UI 至少覆盖 5 态：Loading / Empty / Error / Populated / Edge。

## AI 模板反模式（7 大罪，逐条对照）

1. **紫色渐变综合症**（P0）：紫粉渐变+发光边框+毛玻璃三位一体 → 替代：纯色背景 + 品牌色光晕（opacity<0.12）或同色系深浅渐变（`#2563EB→#1D4ED8`）
2. **Emoji 替代图标**（P0）→ 锁定图标库对应图标
3. **千篇一律 Hero**（P0）：大标题+副标题+居中 CTA+抽象 3D → 替代：真实产品截图、可交互 Demo、非对称 Hero
4. **默认靛蓝强调**（P1）：Tailwind 默认 `#6366f1` = 一眼 AI → 品牌特定色彩，每屏 ≤2 处
5. **圆角卡片+彩色左边框**（P1）→ 用边框颜色区分：`.card{border:1px solid var(--border)} .card:hover{border-color:var(--accent)}`
6. **虚构指标**（P1）：无来源的 "10,000+ 用户" → 真实数据或有机真实感数字（47.2% 而非 50%）
7. **填充式文案**（P2）："Elevate"/"Seamless"/"Unleash"/"Next-Gen" → 具体动作和价值（「3分钟搭建你的第一个看板」）

### 绝对禁令（出现即重写）

侧条纹边框（border-left>1px 彩色强调）/ 渐变文字（background-clip:text）/ 装饰性毛玻璃 / Hero 指标模板（大数字+小标签+渐变）/ 相同卡片网格无限重复 / 每节小型大写追踪标签（"ABOUT""PRICING"）/ 编号 section 标记（01·关于）/ 文字溢出容器 / 幽灵卡片（1px border + blur≥16px 阴影同现）/ 卡片圆角 ≥24px / 重复结构动效 / 奶油米色背景默认化（温暖感由强调色+排版+图片传达）

## 品牌寄存器 vs 产品寄存器

| | Brand（设计即产品） | Product（设计服务产品） |
|---|---|---|
| 适用 | 官网/落地页/营销页/作品集 | 仪表盘/后台/工具 UI |
| 色彩 | 饱和色可占 30-60%，全色板 | 中性色 + 一个强调色 ≤10% |
| 排版 | 允许展示字体、字重倒置 | Sans-Serif 为主，Serif 在 Dashboard 严格禁止 |
| 动效 | 一个精心编排的加载动画 | 功能性动效，150ms 收敛值，无装饰动画 |
| 图片 | 必须配图，零图片是 bug | 数据可视化、图标、UI 元素替代照片 |

## 设计可调参数（三维控制盘）

- **DESIGN_VARIANCE**（默认 6）：1-3 严格对称网格；4-7 负 margin 重叠、变化长宽比、左对齐标题配居中数据（>4 禁居中 Hero）；8-10 Masonry、Grid 分数单位、大面积留白。>3 的非对称布局在 <768px 必须回退单列
- **MOTION_INTENSITY**（默认 5）：>5 加持续微动画（脉冲/浮动）；<3 仅 hover/active
- **VISUAL_DENSITY**（默认 4）：1-3 美术馆留白；8-10 驾驶舱模式——禁卡片容器，用 border-t/divide-y 分组，数字用等宽字体

## 认知负荷与角色化测试（设计评审时执行）

工作记忆 ≤4 项：导航 ≤5 顶级项、表单每组 ≤4 可见字段、1 主按钮+1-2 次按钮、定价 ≤3 选项。检查清单：单一焦点/分块（≤4项组）/视觉分组/层次一眼可辨/一次一事/渐进披露。

角色化测试（选 2-3 个走主流程）：亚历克斯（急躁高手：红旗=强制教程、无键盘导航）/ 乔丹（困惑新手：红旗=纯图标无文字、术语无解释）/ 山姆（无障碍依赖：红旗=无键盘替代、仅颜色传达含义）/ 莱利（压力测试：红旗=空态无引导、刷新丢数据）/ 凯西（分心移动用户：红旗=重要操作在顶部、无状态持久化）。

## 设计动作词汇

critique（UX 评审）/ polish（对齐设计系统打磨）/ bolder（加大对比强化主色）/ quieter（降低饱和增加留白）/ distill（剥离到本质）/ harden（完善错误/空/溢出边界）/ clarify（改进文案）/ delight（微妙愉悦时刻）/ typeset（修复字体层次）。完整 23 命令见 `knowledge/design-systems/design-commands.md`。

## 动效精规

即时反馈 50-100ms / 状态确认 150ms（跨系统收敛值）/ 进入 UI 200-300ms / 跨屏过渡 300-500ms。必须支持 `prefers-reduced-motion`。

## 交付物清单

1. **Design Token CSS**（四层架构组织）+ **design-tokens.json**（前端 import 引用——无此文件不放行开发）
2. **DESIGN.md**（9 节）：Visual Theme & Atmosphere / Color Palette & Roles / Typography Rules / Component Stylings / Layout Principles / Depth & Elevation / Do's and Don'ts / Responsive Behavior / Agent Prompt Guide
3. **页面设计提示词**（每页）：路由 / 布局（Flexbox/Grid）/ 核心组件+状态 / 交互（操作→反馈）/ 响应式差异
4. 组件状态矩阵（5 态）+ Tailwind 主题配置片段

## 设计自检门禁

- P0 三规则（emoji 零匹配 / 无紫粉渐变 / 无 AI 模板味）——任一不通过立即退回
- 设计系统 8 项：颜色全 Token 引用 / 间距 4px 整数倍 / 字体三栈明确 / Hero 展示真实产品内容 / 对标品牌全产品一致 / 按钮 ≥6 态 / 表单有错误态、列表有空态
- 质量 5 项：图标库锁定且尺寸统一 / 无纯黑纯灰直用 / 对比度 ≥4.5:1、动画 ≤400ms、支持 reduced-motion / 响应式覆盖移动端 / 9 态矩阵覆盖
