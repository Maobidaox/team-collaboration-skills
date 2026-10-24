# 开发者交接与设计 QA（Step 4）

## 1. 交付文档模板

```markdown
# [项目名称] UI 设计系统

## 🎨 设计基础

### 颜色系统
- **主色**：#3b82f6（500）/ #2563eb（600，hover）/ #1e3a8a（900）
- **语义色**：success #10b981 · warning #f59e0b · error #ef4444 · info #3b82f6
- **中性色**：#f9fafb / #e5e7eb / #6b7280 / #1f2937（正文，不用纯黑）
- **暗色**：主色 #60a5fa，surface #0b1220，text #f9fafb
- **对比度**：正文 #1f2937 on #ffffff = 14.8:1 ✅；次要文字 #6b7280 on #ffffff = 4.8:1 ✅（AA）

### 字体系统
- **展示字体**：Instrument Serif（仅标题，最大 3 种字重）
- **正文字体**：Work Sans 400/500/600
- **字号阶梯**：12 / 14 / 16 / 18 / 20 / 24 / 30 / 36（标题用 clamp 流体化）
- **行高**：正文 1.6，标题 1.15；正文行长 45–75 字符

### 间距系统
- **基准** 4px；**用量** 4 / 8 / 12 / 16 / 24 / 32 / 48 / 64
- 相邻层级间距不相等，用差异创造节奏

### 阴影与层级
- sm / md / lg 三级；暗色下改用边框 + 亮度差表达层级

## 🧱 组件库

| 组件 | 变体 | 尺寸 | 状态 | 文件 |
|------|------|------|------|------|
| Button | primary/secondary/ghost/danger | sm 32 / md 40 / lg 48 | default·hover·active·focus·disabled·loading | src/components/Button.tsx |
| Input | text/textarea/select | md 40 / lg 48 | + error（aria-invalid） | src/components/Input.tsx |
| Card | elevated/outlined | — | default·hover | src/components/Card.tsx |

**状态覆盖**：loading 用骨架屏；empty 含「为什么空 + 下一步操作」；error 含恢复动作。

## 📱 响应式

- **断点**：640 / 768 / 1024 / 1280
- **栅格**：12 列，gap 16px（移动端 12px）
- **组件自适应**：卡片网格用 `@container`；页面级布局切换用 `@media`
- **移动端**：表格转卡片列表，筛选收进抽屉，**不隐藏任何关键功能**

## ♿ 可访问性

- 对比度：正文 4.5:1 ✅ / 大字 3:1 ✅
- 键盘：全功能可达，Tab 顺序与视觉顺序一致，焦点环 2px offset 2px
- 语义：原生 button/a/table；图标按钮带 aria-label；Modal 焦点陷阱 + Esc 关闭
- 触达：≥44×44px，相邻间隔 ≥8px
- 动效：包裹 prefers-reduced-motion
- 缩放：200% 文本放大不破版

## 📦 交付物

- token 文件：`src/styles/tokens.css`
- 组件源码：`src/components/*`
- 资源：`assets/` 含 @1x/@2x/@3x 位图 + SVG 图标
- 规范文档：本文档
```

## 2. 设计规格要写清的具体数值

开发者最怕「看着调」。以下每一项都要给数字：

| 项 | 示例 |
|----|------|
| 尺寸 | 按钮高 40px、内边距 0 16px、圆角 6px |
| 间距 | 卡片内边距 16px、卡片间距 24px、区块间距 48px |
| 色值 | 主色 #3b82f6、hover #2563eb、边框 #e5e7eb |
| 字号行高 | 标题 24/1.15、正文 16/1.6、辅助 14/1.5 |
| 字重 | 标题 600、正文 400、强调 500 |
| 阴影 | `0 4px 6px -1px rgb(0 0 0 / 0.1)` |
| 动效 | `150ms cubic-bezier(0.16, 1, 0.3, 1)`，`transform: translateY(-1px)` |
| 断点行为 | <640px 单列 / ≥1024px 3 列 |

## 3. 资源导出规范

| 类型 | 规格 |
|------|------|
| 位图 | @1x / @2x / @3x 三套；优先 WebP，提供 PNG 兜底 |
| 图标 | **一律 SVG**（可着色、可缩放）；`currentColor` 填充以便跟随文字色 |
| 插画 | SVG 优先；复杂渐变用 WebP |
| 字体 | 子集化（仅保留用到的字符集）+ `woff2`；`font-display: swap` |
| 命名 | `icon-arrow-right.svg`、`illustration-empty-orders.svg`，kebab-case，全小写 |

性能：**单页图片总量控制在 1MB 内**，首屏关键图 `< 200KB`；图标用 SVG sprite 或 inline，不要几十个独立请求。

## 4. 设计 QA 验收清单（实现完成后逐项过）

**视觉还原**
- [ ] 尺寸、间距、圆角与规格表一致（用开发者工具量，不靠肉眼）
- [ ] 所有色值与 token 一致，无硬编码 hex
- [ ] 字体实际生效（含 fallback 与字重）

**状态完整性**
- [ ] 每个组件五态齐备（default/hover/active/focus/disabled）
- [ ] loading / empty / error / success 四类都有实现，不是留白
- [ ] 禁用态真的不可点击（不只是变灰）

**可访问性**
- [ ] 键盘走完全流程，无焦点陷阱（除 Modal 内的有意为之）
- [ ] 焦点环可见且未被 `overflow: hidden` 裁掉
- [ ] 对比度实测达标（用取色工具实测，不靠估算）
- [ ] 表单错误有 `aria-invalid` + 文字说明
- [ ] 图片有 alt（装饰性图片 `alt=""`）

**响应式**
- [ ] 四个断点逐一检查，无横向滚动条
- [ ] 移动端触达区域 ≥44px，无重叠
- [ ] 文本放大 200% 不破版

**性能**
- [ ] 首屏图片已压缩并指定尺寸（防 CLS）
- [ ] 动画只涉及 transform/opacity，无布局抖动
- [ ] 字体已子集化，有 `font-display`

**一致性**
- [ ] 同类操作在不同页面表现一致（同样的删除流程、同样的错误文案）
- [ ] 全站只有一种主按钮样式
- [ ] 文案术语统一（"删除"不一会儿叫"移除"）

## 5. 常见交接失败点

| 失败点 | 预防 |
|--------|------|
| 只给视觉稿不给数值 | 规格表必须含尺寸/间距/色值/字号 |
| 只画了理想态 | 状态矩阵与空/错/加载态一并交付 |
| 色值写死没走 token | 组件层禁止硬编码，暗色主题才可能做 |
| 图标只给 PNG | 一律 SVG + currentColor |
| 对比度口头说"够了" | 实测比值写进文档 |
| 断点只测了桌面 | 四个断点逐一截图验收 |
| 没有「不要」条款 | 每个组件文档写清禁用场景 |
