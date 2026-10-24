# 前端开发与动效（Frontend Studio）

适用：落地页 / 营销站 / 富动效产品页、电影感滚动叙事、生成式艺术、需要 AI 生成媒体资产（图片/视频/音频）的页面。

不适用：简单 UI 组件、基础表单页、小幅 CSS 修正、加个按钮或弹窗、标准 CRUD 界面、简单响应式调整（这些直接按主工作流执行）。

> 蒸馏说明：原技能包内的 MiniMax 生成脚本与字体资源未随本包分发。需要生成媒体资产时，改用环境自带的图像/视频生成工具（ImageGen / VideoGen），产出保存到项目本地再引用。

## Workflow

### Phase 1: Design Architecture

1. 分析需求 — 确定页面类型与上下文
2. 规划布局分区，确定资产需求
3. 选择技术方案（设计规则：统一描边 SVG 图标、禁止 emoji 充当功能图标、禁止硬编码颜色值、禁止空洞占位文案）

### Phase 2: Motion Architecture

1. 按分区选择动效工具（见下方工具矩阵）
2. 规划动效序列，遵守性能规则

### Phase 3: Asset Generation

1. 解析资产需求（类型、风格、规格、用途）
2. 编写 Prompt，展示给用户确认后再生成
3. 生成并保存到项目本地
4. **所有资产保存完毕后才进入 Phase 5**；绝不使用占位符 URL

### Phase 4: Copywriting

使用 AIDA / PAS / FAB 框架撰写文案，不使用 Lorem ipsum 等空洞占位。

### Phase 5: Build UI

搭建项目，逐区构建；集成资产与文案，所有媒体引用必须指向本地文件。

### Phase 6: Quality Gates

- [ ] 移动端布局正常
- [ ] `min-h-[100dvh]` 而非 `h-screen`
- [ ] Empty / Loading / Error 状态齐全
- [ ] 动效工具未在同一组件混用
- [ ] `useEffect` 有 cleanup
- [ ] `prefers-reduced-motion` 已处理
- [ ] 无占位符 URL（grep 检查）
- [ ] 所有媒体资产存在于本地
- [ ] 依赖已在 `package.json` 中声明

## Motion Tool Selection Matrix

| 场景 | 工具 |
|------|------|
| UI 进出/布局动画 | **Framer Motion** |
| 滚动叙事（pin, scrub） | **GSAP + ScrollTrigger** |
| 循环图标 | **Lottie**（懒加载） |
| 3D/WebGL | **Three.js / R3F**（隔离 Canvas） |
| Hover/Focus 状态 | **纯 CSS** |
| 原生滚动驱动 | **CSS** `animation-timeline: scroll()` |

**冲突规则**

- ❌ 同一组件不混用 GSAP + Framer Motion
- ❌ R3F 必须隔离在 Canvas wrapper 中
- ❌ 重型库（Lottie/GSAP/Three.js）必须懒加载

## Performance Rules

**只动画 GPU 属性**：`transform`、`opacity`、`filter`、`clip-path`
**绝不动画**：`width`、`height`、`top`、`left`、`margin`、`padding`

**移动端**

- 尊重 `prefers-reduced-motion`
- 粗指针设备禁用视差/3D
- 粒子上限：桌面 800 / 平板 300 / 手机 100

## 资产命名与常用预设

命名规范：`{type}-{descriptor}-{timestamp}.{ext}`

| 预设 | 规格 |
|------|------|
| `hero` | 16:9，电影感，含文字安全区 |
| `thumb` | 1:1，主体居中 |
| `icon` | 1:1，扁平，干净背景 |
| `bg-video` | 768P，6s，静态镜头 |
| `bgm` | 30s，无人声，可循环 |
