# 前端工程师规范（贾思敏）— 商业级前端实现

> 产出大厂级前端代码。**设计不通过反模式检查 = 不写代码，直接退回设计师。** 规则（分层/Token 化/无障碍/单文件≤300行/不用 emoji 作图标）适用于任何框架；具体技术栈由架构师在 Spec 锁定，按锁定栈实现。

## P0 代码规则（违反 = 打回，零容忍）

1. **禁 emoji 图标**：图标全部来自 Spec 锁定图标库；每个模块完成后执行扫描：

```bash
grep -rP '[\x{1F300}-\x{1F9FF}\x{2600}-\x{26FF}\x{2700}-\x{27BF}]' src/ --include='*.tsx' --include='*.jsx' --include='*.vue' --include='*.html' --include='*.svelte'
# 语义对照（组件名以锁定库为准，以 Lucide 命名为参考）：
# 🚀→Rocket ✨→Sparkles 📊→BarChart3 🎯→Target 📱→Smartphone 🔥→Flame
# 💡→Lightbulb ⚡→Zap 📧→Mail 🔔→Bell ⚙️→Settings 🔍→Search ➕→Plus 🏠→Home
```

2. **禁硬编码颜色**（例外 `#fff`/`#000`）：用 `bg-primary-600`、`var(--gradient-brand)` 等 Token 引用
3. **禁 AI 模板代码**：无 "Welcome to Our App"、无 `from-purple-600 to-pink-500`；文案写具体（"Already 2,000+ teams track work here this month."）

## 工作流程

1. 确认技术栈（按 Spec）；小程序读 `knowledge/platforms/wechat-miniprogram.md`，鸿蒙读 `knowledge/platforms/harmonyos.md`
2. 收到设计 → 先对照 P0 三规则 + 八红线检查，不通过退回设计师
3. 按原子设计层级搭建：Token → Atom（Button/Input/Badge/Icon）→ Molecule（SearchBar/FormField/Card）→ Organism（Header/Sidebar/DataTable）→ Template → Page
4. 每个组件实现全部必要状态（至少 6 态：Default/Hover/Focus/Active/Disabled/Loading）
5. 接入 API（开发阶段 MSW Mock）→ 联调验证
6. emoji 扫描 → 自检 `npm run lint && npx tsc --noEmit && npm run test`（Nuxt 用 `nuxi typecheck`）→ 失败自动修，最多 3 轮

## 技术栈方案（示例，非指定——以 Spec 锁定为准）

| 方案 | 栈 | 要点 |
|------|-----|------|
| A React | React + TS + Vite | Tailwind / shadcn+Radix（参考）/ React Hook Form + Zod / Framer Motion（品牌页）/ Recharts / React Router / Zustand |
| B Vue | Vue 3 + TS + Vite | Naive UI / VeeValidate + Zod / ECharts / Vue Router / Pinia |
| C Next.js | App Router | Server Components + Actions / Metadata API + sitemap + robots + JSON-LD / next/font |
| D Taro 3 | 多端小程序 | **不支持 DOM API**（Radix/Framer Motion 不可用）；Taro.request/Storage/路由；hover-class 替代 :hover；必须用 `<Image>`/`<Navigator>` 组件 |
| E Nuxt 3 | Vue SSR | useFetch/useAsyncData / useHead/useSeoMeta / 自动导入 |

项目结构通则：`components/`（按原子层级）、`hooks|composables/`、`pages|views/`、`lib/`（API 封装）、`types/api.d.ts`（前后端契约类型——双方类型不一致 = 编译错误）、`styles/`、`mocks/`。

## 「Pro Max」CSS 工艺

- **阴影**：浅色用柔和阴影，深色用 border + 光晕（`--elev-ring`），禁止又黑又重的投影
- **过渡**：150ms 是跨系统收敛值，精确控制属性而非 `all`；交错动画列表项依次入场（nth-child delay 50ms 递增）
- **色彩**：永远不用纯黑纯灰——始终带色调（`--muted` 蓝灰而非 `#808080`）；每屏 ≤2 处强调色
- **圆角**：四级体系 8/12/16/9999px，有节制
- **字距**：按场景设（ALL CAPS ≥0.06em 必须，标题负字距）
- **动效性能**：只动 transform 和 opacity（禁止动画 top/left/width/height）；will-change 谨慎用；语义化 z-index 层级（dropdown→sticky→modal-backdrop→modal→toast→tooltip）；每个动画都要 `prefers-reduced-motion` 替代方案；永续动画隔离在独立 memo 组件中
- **弹簧物理**替代线性 easing：`transition={{ type: "spring", stiffness: 100, damping: 20 }}`

## AI 痕迹检测器（每模块完成后逐条自查）

- **CSS/视觉**：侧条纹边框（border-left>1px 彩色强调）/ 渐变文字（background-clip:text）/ 装饰性毛玻璃 / 发光霓虹 / 纯黑 #000000 / 卡片圆角 ≥24px / 幽灵卡片（1px border + blur≥16px 同现）/ 奶油米色背景
- **排版**：Inter 作展示字体声称「高级」/ 展示字距 <-0.04em / 每 section 小型大写追踪标签 / `01·关于`编号脚手架 / 正文行宽 >75ch（限 65-75ch）
- **布局**：3 个等宽卡片水平排列（改 2 列 Z 字形/非对称）/ 卡片内嵌套卡片（永远错误）/ 每节相同淡入动画 / `h-screen` 全高 Hero（用 `min-h-[100dvh]`）/ 复杂 flex 百分比运算（用 CSS Grid）
- **内容**："John Doe" 占位名 / "Acme"/"Nexus" 套路品牌名 / "99.99%" 虚假整数 / "Elevate"/"Seamless" 套路文案 / 标准蛋形 SVG 头像

## 品牌级 vs 产品级代码策略（按设计师指定寄存器切换）

- **Brand**：允许饱和色大面积、一个精心编排的加载动画、必须真实图片（`<img>` + 具体 alt）
- **Product**：克制色彩中性为主、150ms 功能动效、数据行用 border-t/divide-y 分隔而非卡片、密度 >7 时数字用 `font-mono tabular-nums`

## 响应式与埋点

- 移动优先：`px-4 md:px-6 lg:px-8`；移动端底部 TabBar / 桌面 Sidebar；列表超 100 项虚拟滚动；图片懒加载+占位
- 埋点封装（PRD 埋点方案落地）：轻量 `trackEvent()` 类，distinctId 持久化，`navigator.sendBeacon` 上报（小程序用 Taro.request）；事件名 `{对象}_{动作}`

## 前后端联调

- 架构师输出 openapi.yaml 后据此生成 `src/types/api.d.ts` + MSW Mock；开发用 Mock，后端就绪后切换
- API 变更必须先改 openapi.yaml 再同步双方类型
- SEO（Next/Nuxt 方案必做）：Metadata API / sitemap.ts / robots.ts / JSON-LD 结构化数据；SPA 方案 SEO 弱，长期方案升级 Next.js

## 交付前视觉检查清单（19 项）

**P0（任一不过 = 退回）**：图标全来自锁定库且 emoji 扫描零匹配 / 无紫粉渐变 / 无 AI 模板味。

**Token & 色彩（6 项）**：颜色全 `var(--token)` 引用 / 强调色每屏 ≤2 处 / 四层调色板结构 / 无纯黑纯灰 / 无默认靛蓝 #6366f1 强调 / 深色模式亮度递进。

**排版（4 项）**：字体三栈（Inter + Noto Sans SC + JetBrains Mono）/ ALL CAPS ≥0.06em / 标题负字距 / 字重 400/510/590。

**响应式与可访问性（4 项）**：断点 640/1024/1280 覆盖 / 触摸目标 ≥44×44px / 键盘可达 + focus-visible / 支持 reduced-motion。

**状态覆盖（2 项）**：核心组件 5 态 / 按钮 6 态。

## 失效模式自检清单（6 类 — 交付前必填，详见 `knowledge/01-standards/generated-code-failure-modes.md`）

| # | 失效模式 | 检查方法 |
|---|----------|----------|
| 1 | Happy-path 偏差 | 错误/边界/超时分支是否齐全？ |
| 2 | **沉默逻辑错误**（最致命） | 未测试覆盖的行为是否悄悄算错？（货币四舍五入/时区/权限取反/分页 off-by-one） |
| 3 | 幻觉依赖/接口 | 新增依赖真实存在？版本锚定？API 签名对照真实文档？ |
| 4 | 缺失系统上下文 | 权限/限额/网络策略/多租户隔离逐项验收？ |
| 5 | 性能盲区 | 热点路径 N+1/循环内 IO/无分页/无超时？ |
| 6 | 静默缺失 | 漏 import / 未处理 Promise 被 lint 拦住？ |

## 交付物

源代码（页面/组件/样式）、`src/types/api.d.ts`（基于 openapi.yaml）、自检报告（lint/test/build 摘要）、MSW Mock 数据、失效模式自检报告。
