---
name: tcs-wechat-miniprogram
description: 微信小程序开发与生态集成工作流（蒸馏自 we-chat-miniprogram-developer 专家「小程达」）。当用户要做小程序相关任务——新建小程序页面/组件、WXML/WXSS/WXS 开发、微信登录、微信支付、订阅消息、分享与朋友圈、分包与包体积治理、setData 性能优化、Skyline 渲染引擎、TDesign 组件库、云开发、提审被拒排查与合规整改——时使用本 skill。提供平台铁律（域名白名单/HTTPS/主包 2MB/无 DOM/API Promise 化）、项目结构骨架、四步工作流（架构配置→核心开发→性能优化→测试提审）与核心代码模板（统一请求层/支付/性能页）。关键词：微信小程序、小程序、WXML、WXSS、WXS、setData、分包、subpackages、主包 2MB、微信登录、微信支付、requestPayment、订阅消息、模板消息、Skyline、TDesign、云开发、小程序提审、审核被拒、域名白名单、性能评分。
agent_created: true
---

# 微信小程序开发与生态集成

## 概述

小程序不是普通 App，而是深嵌微信社交、支付与十亿级用户习惯的载体。目标是构建**高性能、能过审、能转化**的小程序：既写好页面与组件，也处理好平台约束（包体积、域名白名单、审核政策、隐私合规）。

深度文档在 `references/`，命中场景时按需加载（不预读）：

| 场景 | 加载 |
| --- | --- |
| 框架基础、组件、API、云开发 | `references/wechat-miniprogram/`（`SKILL.md` 为入口，另有 `references/framework.md` 等） |
| Skyline 渲染引擎（组件/动画/路由/样式/worklet/滚动 API） | `references/skyline/`（`SKILL.md` + `references/overview|wxss|route|worklet|components|scroll-api|config/`） |
| TDesign 小程序组件库（60+ 组件、主题定制、暗色模式） | `references/tdesign/`（`SKILL.md` + `references/miniprogram/components/*.md`） |
| UI 设计质量（排版、配色、动效、交互、可用性审查） | `references/impeccable/`（按主题加载，如 `references/typography.md`、`references/color-and-contrast.md`） |
| 请求层 / 支付 / 性能页骨架代码 | `references/snippets-core-templates.md` |
| 专家原始人格 | `references/persona-wechat-miniprogram-developer.md` |

## 平台铁律（不可违反）

- **域名白名单**：所有 API / WebSocket / 上传 / 下载域名必须先在小程序后台登记，否则真机请求失败
- **HTTPS 强制**：每个网络请求必须 HTTPS 且证书有效
- **包体积纪律**：主包 < 2MB，总包（含分包）上限 20MB；接近上限时先规划分包再堆功能
- **隐私合规**：按微信隐私 API 要求，访问敏感数据前必须取得用户授权
- **无 DOM**：双线程架构，不能直接操作 DOM，只能走数据驱动与 `setData`
- **API Promise 化**：把回调式 `wx.*` API 包成 Promise，异步代码才干净
- **生命周期意识**：正确处理 App / Page / Component 生命周期
- **setData 节制**：每次 `setData` 都跨 JS↔原生桥，合并更新、只传视图需要的字段

## 项目结构骨架

```
├── app.js / app.json / app.wxss         # 应用生命周期、全局配置（pages/window/tabBar）、全局样式
├── project.config.json / sitemap.json   # IDE 设置、微信搜索索引配置
├── pages/<page>/                        # 每个页面四个文件：.js / .json / .wxml / .wxss
├── components/<component>/              # 可复用自定义组件（properties / events / slot）
├── utils/                               # request.js（统一请求层）、auth.js（登录与 token）、analytics.js
├── services/                            # 业务逻辑与 API 调用
└── subpackages/                         # 分包（用户中心、营销页等低频功能）
```

## 工作流

### Step 1 架构与配置
1. `app.json` 定义页面路由、tabBar、window 与权限声明
2. 按用户旅程优先级规划主包与分包
3. 在微信后台登记所有请求 / WebSocket / 上传下载域名
4. 配置开发 / 预发 / 生产环境切换

### Step 2 核心开发
1. 组件库：自定义组件明确 properties、事件与 slot
2. 状态管理：`app.globalData` 或 mobx-miniprogram / 自建 store
3. API 集成：统一请求层（鉴权 + 错误处理 + 重试）
4. 微信能力：登录、支付、分享、订阅消息、位置

### Step 3 性能优化
1. 启动优化：精简主包、延迟非关键初始化、配置预加载规则
2. 渲染优化：降低 `setData` 频率与数据量、使用纯数据字段、长列表用虚拟列表
3. 图片优化：CDN + WebP、懒加载、控制尺寸
4. 网络优化：请求缓存、数据预取、弱网可用

### Step 4 测试与提审
1. 功能测试：iOS / Android 微信、不同机型与网络条件
2. 真机调试：开发者工具真机预览与调试
3. 合规检查：隐私政策、授权流程、内容合规
4. 提交审核：备齐材料、预判常见驳回原因

## 沟通与判断（体现生态思维）

- **按约束思考**：「主包已 1.8MB，加这个功能前得先把营销页挪到分包」
- **性能优先**：「三次更新合成一次 `setData`，每次调用都要过桥」
- **平台务实**：「页面上看不到使用场景就申请定位权限，审核会拒」

## 成功指标（自查口径）

启动时间中端安卓 < 1.5s · 主包 < 1.5MB · 首次提审通过率 > 90% · 崩溃率 < 0.1% · 分享打开转化率 > 15% · 7 日留存 > 25% · 开发者工具性能评分 > 90

## 安全与合规

- 敏感数据按微信与《个人信息保护法》要求处理；密钥与签名一律在服务端
- 会话与 token 安全管理，刷新模式可靠
- UGC 内容走 `msgSecCheck` / `imgSecCheck`
- 支付签名服务端生成，退款与回调验签完整
