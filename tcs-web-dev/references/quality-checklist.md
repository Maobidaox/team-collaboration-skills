# 质量检查清单（Phase 4）

对照逐项审查，逐项优化并**复测**（用构建产物 + 实际浏览器测量，不只靠肉眼）。

## 一、性能（Core Web Vitals）

诊断指标（取真实用户 p75，实验室数据仅作参考）：

| 指标 | 含义 | 良好阈值 |
|------|------|---------|
| **LCP** | 最大内容渲染时间 | ≤ 2.5s |
| **CLS** | 累积布局偏移 | ≤ 0.1 |
| **INP** | 交互到下次绘制（已取代 FID） | ≤ 200ms |
| TTFB | 首字节时间 | ≤ 800ms |

落地优化手段：

- **图片**：`webp`/`avif` 格式、响应式 `srcset`、显式宽高或 `aspect-ratio`、首屏图 `fetchpriority="high"` 且不懒加载、非首屏 `loading="lazy"`
- **资源**：代码分割（路由级）、第三方脚本 `defer`/`async` 或按需加载、字体 `font-display: swap` 并预加载关键字体
- **传输**：开启压缩（Brotli/gzip）、静态资源长缓存 + 内容哈希、CDN 分发
- **预加载**：关键资源 `<link rel="preload">`、跨源 `<link rel="preconnect">`
- **渲染**：避免阻塞渲染的同步脚本；长任务拆分；虚拟列表处理长列表

复测命令示例：`npx lighthouse <url> --preset=desktop`（或本地构建后用预览服务测量），对比优化前后数值。

## 二、SEO

- [ ] 每个页面唯一且有信息量的 `<title>`（≤ 60 字符）
- [ ] `meta description`（≤ 160 字符，有实际内容）
- [ ] `canonical` 指向规范 URL（防重复内容）
- [ ] Open Graph / Twitter Card（`og:title`、`og:description`、`og:image`、`og:url`）
- [ ] 语义化结构：单一 `<h1>`、标题层级递进、`<nav>` / `<main>` / `<article>` / `<footer>`
- [ ] `sitemap.xml` 与 `robots.txt`；结构化数据（JSON-LD）按需添加
- [ ] SSR/SSG 保证爬虫可抓取纯 HTML 内容（纯 CSR 需预渲染补充）
- [ ] 图片有 `alt`（装饰性图片用 `alt=""`）
- [ ] 链接用 `<a href>`，不用 `<div onclick>` 代替导航

## 三、无障碍 a11y

- [ ] 键盘可达：所有交互元素可 Tab 聚焦、可 Enter/Space 激活、有可见焦点指示（不写 `outline: none` 而不给替代）
- [ ] 色彩对比度：正文 ≥ 4.5:1，大号文本与图形 ≥ 3:1
- [ ] 表单：每个控件有关联 `<label>`（`for`/`id` 或包裹）、错误提示可被读屏播报
- [ ] 图标按钮有无障碍名称（`aria-label`）
- [ ] 动态内容用 `aria-live` 提示更新；弹窗管理焦点（`focus trap`、Esc 关闭）
- [ ] 支持 `prefers-reduced-motion`，动效可关闭
- [ ] 语义化优先于 `div` + ARIA；用原生元素能解决就不造轮子

## 四、安全与合规

- [ ] 客户端无服务端密钥（`NEXT_PUBLIC_*` / `VITE_*` 前缀变量绝不存密）
- [ ] 用户输入渲染处已转义；不用 `innerHTML` 拼接不可信内容
- [ ] Cookie 敏感场景 `Secure` / `HttpOnly` / `SameSite`
- [ ] 依赖无已知严重漏洞；第三方脚本来源可信

## 五、移动端与兼容

- [ ] viewport meta 正确；高度用 `100dvh`
- [ ] 触控目标 ≥ 44×44px；横向无溢出滚动
- [ ] 目标浏览器特性有降级方案（`@supports` 或 polyfill）
