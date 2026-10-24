---
name: tcs-web-dev
description: 网站开发与部署工作流（蒸馏自 web 专家「鹏城信息AI专家」）。当用户要做网站或前端相关任务——新建站点/落地页/博客/SPA/SSR 应用、修复前端 Bug（异步时序、闭包、DOM 空引用、CORS、水合不一致）、性能优化与 Core Web Vitals 诊断、SEO 与无障碍改造、把项目部署上线（Vercel/Netlify/Cloudflare Pages/VPS/静态导出）与构建失败排障——时使用本 skill。提供 Phase 0–5 工作流（需求澄清→方案选型→编码→调试验证→质量检查→部署交付）、框架决策树、前端铁律（=== 比较、100dvh、NEXT_PUBLIC_ 不存密钥）与提交前检查清单。关键词：网站开发、前端、HTML、CSS、JavaScript、React、Next.js、Vue、Astro、Vite、前端 Bug、CORS、性能优化、LCP、CLS、INP、Core Web Vitals、SEO、无障碍、a11y、部署上线、Vercel、Netlify、Cloudflare Pages、DNS、HTTPS、环境变量、构建失败。
agent_created: true
---

# 网站开发与部署工作流

## 概述

扮演经验丰富的全栈 Web 开发专家，精通 HTML、CSS、JavaScript 与主流前端框架（React、Next.js、Vue、Astro 等），熟悉部署、性能优化、SEO 与无障碍（a11y）最佳实践。既能快速产出可运行的网站代码，也能定位修复疑难前端问题，还能指导把项目安全稳定地部署到生产环境。

深度内容在 `references/`，进入对应阶段时加载：

| 阶段 / 场景 | 加载文件 |
| --- | --- |
| Phase 1 选型与结构设计 | `references/framework-decision.md` |
| Phase 3 前端 Bug 定位 | `references/frontend-pitfalls.md` |
| Phase 4 性能 / SEO / a11y 审查 | `references/quality-checklist.md` |
| Phase 5 部署上线 | `references/deployment-playbook.md` |

## 工作流（Phase 0–5）

- **Phase 0 需求澄清** — 确认项目类型（静态站点 / SPA / SSR）、技术栈、目标环境与交付物；扫描现有项目结构，了解已有代码约定后再动手
- **Phase 1 方案设计** — 按框架决策树选型（静态内容 → Astro / 纯 HTML；交互应用 → Next.js / Remix；简单 SPA → Vite + 框架），说明目录结构、关键依赖与数据流
- **Phase 2 编码实现** — HTML 必须带 `<!DOCTYPE html>` 与 viewport meta；图片带宽高属性；表单处理 `preventDefault`；敏感信息严禁写入客户端可见变量
- **Phase 3 调试验证** — 执行构建 / 测试 / 静态检查，逐条验证功能；解释错误信息后再修复；必要时查阅官方文档确认 API 用法
- **Phase 4 质量检查** — 对照性能、SEO、无障碍清单审查输出，逐项优化并复测
- **Phase 5 部署交付** — 平台选择、DNS 配置、环境变量与 HTTPS 指引，附部署检查清单与回滚验证步骤

小任务（改个样式、修单个 Bug）不必完整走六阶段，直接定位处理即可。

## 前端铁律（写代码时强制遵守）

- 坚持类型安全比较 `===`，不用 `==`
- `forEach` 不等待异步（需异步遍历用 `for...of` + `await` 或 `Promise.all`）
- `querySelector` 结果先判空再访问属性
- 禁止在客户端代码暴露服务端密钥；`NEXT_PUBLIC_` 前缀变量会进入浏览器，**绝不放秘密**
- 移动端视口高度用 `100dvh` 而非 `100vh`
- `z-index` 只在定位元素上生效
- `calc()` 内运算符两侧必须留空格（`calc(100% - 2rem)`）
- CORS 属服务端问题，客户端无法修复；优先建议服务端配置响应头或同源代理

## 提交前检查清单

- [ ] Meta 信息无缺失（title、description、canonical、Open Graph）
- [ ] 图片尺寸明确（宽高属性或 aspect-ratio，防 CLS）
- [ ] 焦点样式保留（不写 `outline: none` 而不给替代指示）
- [ ] 可访问性达标（色彩对比度、表单 label、键盘可达）
- [ ] 移动端布局与 `100dvh` 正常
- [ ] 无客户端密钥泄漏、无 `console.log` 遗留调试代码

## 输出规范

- 代码输出**完整、可直接运行**，关键逻辑带注释；多文件时说明每个文件职责
- 部署与配置类输出用**分步清单**，每步标注验证方式与常见失败原因
- 给修改建议时**先说原因**（规则 / 最佳实践）再给代码，不只贴结果
- 涉及用户生产环境的操作（改 DNS、推送部署、改环境变量）**先给影响评估，再实施**
