# 组件库与状态矩阵（Step 3 产出模板）

组件没写完状态矩阵，等于只交付了一半。开发者最常问的正是「加载中长什么样」「没有数据怎么办」。

## 1. 基础组件清单

| 类别 | 组件 |
|------|------|
| 操作 | Button（主/次/文字/危险）、IconButton、Link、SplitButton |
| 表单 | Input、Textarea、Select、Checkbox、Radio、Switch、Slider、DatePicker、FileUpload |
| 导航 | Tabs、Sidebar、Breadcrumb、Pagination、Menu、Stepper |
| 反馈 | Alert、Toast、Modal/Dialog、Tooltip、Popover、Banner |
| 数据展示 | Card、Table、List、Badge、Tag、Avatar、Stat、EmptyState、Skeleton |
| 布局 | Container、Grid、Stack、Divider、Accordion、Drawer |

## 2. 五态矩阵（每个可交互组件必须覆盖）

| 状态 | 视觉规则 |
|------|---------|
| **default** | 基准样式，符合 token |
| **hover** | 主色深一档 + `translateY(-1px)` + 阴影升一级；**触摸设备不保留 hover 残留**（用 `@media (hover: hover)` 包裹） |
| **active** | 按下一瞬：去掉位移回到原位，颜色再深一档，时长 ≤100ms |
| **focus-visible** | `outline: 2px` + `outline-offset: 2px`；**只在键盘聚焦时出现**（`:focus-visible` 而非 `:focus`） |
| **disabled** | `opacity: .6` + `cursor: not-allowed` + `pointer-events: none`；**同时移除 tabindex 或加 `aria-disabled`**，不能只是变灰仍可点 |

```css
@media (hover: hover) { .btn--primary:hover { background: var(--color-primary-600); } }
.btn--primary:active { transform: translateY(0); background: var(--color-primary-700); }
```

**易错点**：把 hover 写成 `.btn:hover` 而不加媒体查询 → 移动端点击后样式残留到下次点击别处。

## 3. 四类非交互状态（最容易漏）

| 状态 | 要求 |
|------|------|
| **loading** | 骨架屏优先于 spinner（减少布局跳动）；按钮 loading 时保持原宽度、禁用点击、文案换成加载中；>1s 才显示（避免闪烁） |
| **empty** | 三要素：说明为什么空 + 引导下一步的主操作 + 插画/图标；**不能只写「暂无数据」** |
| **error** | 人话说明出了什么问题 + 可执行的恢复动作（重试/返回）；表单错误定位到字段下方，带 `aria-invalid` 与 `aria-describedby`；**不展示技术细节** |
| **success** | 明确告知结果，可撤销的操作给「撤销」入口而不是二次确认弹窗 |

## 4. 关键组件规范

**按钮层级**：一屏内**只能有一个主按钮**。次级操作用次级/文字按钮。三个按钮都是主色 = 没有层级。

| 变体 | 用法 |
|------|------|
| primary | 页面最重要且唯一的主行动 |
| secondary | 并列的次要行动 |
| ghost/text | 取消、返回、低优先级 |
| danger | 删除/不可逆操作，需二次确认 |

**表单**：
- 标签在输入框上方（不要纯 placeholder 当标签，聚焦即消失且对比度不足）
- 必填用文字标注「必填」而非只靠红色星号
- 错误提示在字段下方、具体说明原因（"密码至少 8 位"而非"密码有误"）
- 输入框字号 ≥16px，否则 iOS Safari 聚焦时自动放大页面
- 相关联的字段用 `fieldset` + `legend` 分组

**表格**：
- 数字右对齐并等宽（`font-variant-numeric: tabular-nums`）
- 表头吸顶；行数多时分页或虚拟滚动
- 移动端转卡片列表，不要横向滚动

**Modal**：打开时焦点移入、关闭时焦点归还触发元素、`Esc` 关闭、背景滚动锁定、`aria-modal="true"` + 焦点陷阱。

**Toast**：文案 ≤ 一行的长度；自动消失时长按字数给（4–7s）；同一时间最多堆叠 3 条；不用于承载必须阅读的关键信息（用 Modal）。

## 5. 交互与动效约束

- **动效服务于状态变化**，不做无意义装饰动画
- 只动画化 `transform` / `opacity` / `filter`（合成层，不触发布局与重绘）；**不要动画化** `width/height/top/left/margin`
- 缓动用**指数缓出**（`cubic-bezier(0.16, 1, 0.3, 1)`），不用回弹/弹性（显得不稳重）
- 时长：微交互 150ms、进场 300ms、复杂转场 500ms；**超过 500ms 就会让人觉得卡**
- 列表项依次入场时，间隔 ≤50ms，总时长控制在 500ms 内
- 必须包 `@media (prefers-reduced-motion: reduce)`

## 6. 组件文档每段必备

```markdown
### Button / 按钮
**用途**：触发一个动作。一屏最多一个 primary。
**变体**：primary / secondary / ghost / danger × sm(32px) / md(40px) / lg(48px)
**属性**：disabled、loading、iconPosition、fullWidth
**可访问性**：原生 <button>；禁用时 aria-disabled；图标按钮必须有 aria-label
**不要**：用 div 当按钮；用按钮当链接跳转（链接要用 <a>）
**代码**：<Button variant="primary" size="md" loading>提交</Button>
```

「不要」这一栏最重要——它防止组件在错误场景被复用，也是设计债的主要来源。
