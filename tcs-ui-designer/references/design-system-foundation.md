# 设计系统基础（Step 2 产出模板）

## 1. Design Token 体系

Token 是唯一事实来源。**组件里不写死数值，一律引用 token**，否则暗色主题与品牌换色无从落地。

```css
:root {
  /* —— 颜色：品牌梯度 —— */
  --color-primary-100: #f0f9ff;
  --color-primary-500: #3b82f6;
  --color-primary-600: #2563eb;   /* hover 态，比 500 深一档 */
  --color-primary-900: #1e3a8a;

  /* —— 语义色：含义固定，不随品牌改 —— */
  --color-success: #10b981;
  --color-warning: #f59e0b;
  --color-error:   #ef4444;
  --color-info:    #3b82f6;

  /* —— 中性色：偏向品牌色，不用纯灰 —— */
  --color-neutral-50:  #f9fafb;
  --color-neutral-200: #e5e7eb;
  --color-neutral-500: #6b7280;
  --color-neutral-800: #1f2937;   /* 正文替代 #000 */

  /* —— 字体 —— */
  --font-display: 'Instrument Serif', Georgia, serif;   /* 展示字体，有个性 */
  --font-body:    'Work Sans', system-ui, sans-serif;   /* 正文，克制耐读 */
  --font-mono:    'Geist Mono', ui-monospace, monospace;

  /* —— 字号阶梯（1.125–1.25 模块化比例，用 clamp 流体化）—— */
  --font-size-xs:  0.75rem;    /* 12px */
  --font-size-sm:  0.875rem;   /* 14px */
  --font-size-base:1rem;       /* 16px 正文基准，不小于此值 */
  --font-size-lg:  1.125rem;   /* 18px */
  --font-size-xl:  1.25rem;    /* 20px */
  --font-size-2xl: 1.5rem;     /* 24px */
  --font-size-3xl: clamp(1.75rem, 4vw, 2.25rem);   /* 流体标题 */
  --font-size-4xl: clamp(2rem, 6vw, 3.5rem);

  /* —— 行高：正文 1.5–1.6，标题 1.1–1.25 —— */
  --leading-body: 1.6;
  --leading-heading: 1.15;

  /* —— 间距：4px 基准（8 点栅格）—— */
  --space-1: 0.25rem;  /* 4px  图标与文字间隙 */
  --space-2: 0.5rem;   /* 8px  紧凑内边距 */
  --space-3: 0.75rem;  /* 12px 表单元素 */
  --space-4: 1rem;     /* 16px 卡片内边距 */
  --space-6: 1.5rem;   /* 24px 区块间距 */
  --space-8: 2rem;     /* 32px 大分组 */
  --space-12: 3rem;    /* 48px 段落分隔 */
  --space-16: 4rem;    /* 64px 页面级留白 */

  /* —— 圆角 —— */
  --radius-sm: 0.25rem;  --radius-md: 0.375rem;  --radius-lg: 0.5rem;  --radius-full: 9999px;

  /* —— 阴影：三级足够，层级靠间距 + 阴影组合 —— */
  --shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 0.05);
  --shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.1);
  --shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.1);

  /* —— 过渡：只动 transform/opacity —— */
  --transition-fast:   150ms cubic-bezier(0.16, 1, 0.3, 1);   /* ease-out-expo */
  --transition-normal: 300ms cubic-bezier(0.16, 1, 0.3, 1);
  --transition-slow:   500ms cubic-bezier(0.16, 1, 0.3, 1);
}
```

**要点**：中性色偏品牌色（`--color-neutral-800: #1f2937` 而非 `#000`）；hover 用深一档同色系，不要临时调 opacity；阴影只留三级，层级感主要靠间距与边框。

## 2. 暗色主题

**不要**把亮色反相。暗色下：

- 纯黑背景 `#000` → 换成深灰蓝 `#0b1220` 一类的低饱和深色
- 主色**变浅**（`#3b82f6` → `#60a5fa`），因为暗底上同样色值会显得更重
- 阴影**失效**：暗色下用边框（`1px solid rgb(255 255 255 / 0.08)`）与亮度差表达层级，阴影几乎不可见
- 文字不用纯白 `#fff`，用 `#f9fafb` 并略降对比，减少眩光

```css
[data-theme="dark"] {
  --color-primary-100: #1e3a8a;
  --color-primary-500: #60a5fa;
  --color-primary-900: #dbeafe;
  --color-surface:     #0b1220;
  --color-text:        #f9fafb;
  --shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.4);   /* 加深才有存在感 */
}
```

同时提供跟随系统的入口：`@media (prefers-color-scheme: dark)` 作为未显式选择时的默认值，并保留用户手动切换（存 localStorage，加 `color-scheme` 属性避免表单控件闪白）。

## 3. 基础组件样式骨架

```css
.btn {
  display: inline-flex; align-items: center; justify-content: center;
  gap: var(--space-2);
  font-family: var(--font-body); font-weight: 500;
  border: none; cursor: pointer; user-select: none;
  transition: background var(--transition-fast), transform var(--transition-fast), box-shadow var(--transition-fast);
}
.btn:focus-visible { outline: 2px solid var(--color-primary-500); outline-offset: 2px; }
.btn:disabled { opacity: 0.6; cursor: not-allowed; pointer-events: none; }

.btn--primary { background: var(--color-primary-500); color: #fff; }
.btn--primary:hover:not(:disabled) {
  background: var(--color-primary-600);
  transform: translateY(-1px);          /* 只动 transform，不动画化 margin/top */
  box-shadow: var(--shadow-md);
}

.form-input {
  padding: var(--space-3) var(--space-4);
  border: 1px solid var(--color-neutral-200);
  border-radius: var(--radius-md);
  font-size: var(--font-size-base);      /* ★ 小于 16px 会触发 iOS 自动缩放 */
  transition: border-color var(--transition-fast), box-shadow var(--transition-fast);
}
.form-input:focus {
  outline: none;
  border-color: var(--color-primary-500);
  box-shadow: 0 0 0 3px rgb(59 130 246 / 0.1);   /* 焦点环用 box-shadow，不用 outline 位移 */
}
.form-input[aria-invalid="true"] { border-color: var(--color-error); }
```

**卡片不要默认加阴影**：有边框时配 `--shadow-sm` 足够，hover 才升到 `--shadow-md`。

## 4. 响应式断点与容器查询

| 断点 | 范围 | 布局特征 |
|------|------|---------|
| 移动 | 320–639px（基准设计） | 单列，导航收起，主操作吸底 |
| 平板 | 640–1023px | 2 列，侧边栏可折叠 |
| 桌面 | 1024–1279px | 完整功能，3–4 列栅格 |
| 宽屏 | ≥1280px | 限制内容最大宽度，不为宽而拉长行宽 |

**移动优先**：基准样式写移动端，用 `min-width` 逐级增强。

```css
.card-grid { display: grid; gap: var(--space-4); grid-template-columns: 1fr; }
@container (min-width: 480px) { .card { grid-template-columns: repeat(2, 1fr); } }  /* 组件自适应 */
@media (min-width: 768px)     { .card-grid { grid-template-columns: repeat(3, 1fr); } }
```

- **组件自适应用 `@container`**（同一组件放进侧边栏或主区都能正确表现），**布局切换才用 `@media`**
- 正文行长控制在 **45–75 字符**（`max-width: 65ch`），宽屏下不要一行拉到底
- 移动端**不得隐藏关键功能**，只改变呈现方式（如表格转卡片列表、筛选收进抽屉）

## 5. 可访问性基线（设计阶段就要满足）

| 项 | 标准 |
|----|------|
| 正文对比度 | ≥ 4.5:1 |
| 大字（≥24px 或 ≥18.66px 粗体）/ 图形 / 输入框边框 | ≥ 3:1 |
| 焦点指示 | ≥ 3:1 且可见，不被 `overflow: hidden` 裁掉 |
| 触达区域 | ≥ 44×44px，相邻间隔 ≥8px |
| 动效 | 包裹 `prefers-reduced-motion: reduce` |
| 文本缩放 | 200% 放大不破版、不裁切 |
| 信息传达 | 不靠颜色单独承载状态 |

```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }
}
```

## 6. 落地产出清单

- [ ] token CSS（亮色 + 暗色两套，组件零硬编码值）
- [ ] 字体阶梯与 `clamp()` 流体标题
- [ ] 间距节奏（相邻层级不相等，避免万物等距）
- [ ] 三级阴影 + 边框层级规则
- [ ] 断点表与容器查询用法
- [ ] 焦点态与禁用态样式
- [ ] 对比度自检结果（列出关键组合的实际比值）
