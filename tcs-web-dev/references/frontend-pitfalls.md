# 前端高频陷阱与排障（Phase 3）

排障顺序：**复现 → 读源码定位 → 解释错误原因 → 修复 → 复测**。不先解释原因就改代码是禁止的。

## 1 类型隐式转换

`==` 触发隐式转换，`0 == ''`、`null == undefined` 均为真。→ 一律 `===`；判断空值显式区分 `null` / `undefined` / `''`。

## 2 异步时序

- `forEach` 不等待异步回调：`.forEach(async x => await fn(x))` 不会串行也不会被 await
  → 串行用 `for...of` + `await`；并行用 `Promise.all(items.map(fn))`
- 在循环里 `await` 导致无谓串行 → 无依赖时改 `Promise.all`，并用 `Promise.allSettled` 处理部分失败
- 竞态（Race）：后发请求先返回覆盖正确结果 → 用请求序号或 `AbortController` 取消过期请求
- 并发无上限打爆接口 → 用 `Semaphore` / 分批（p-limit 类工具）控制并发

## 3 状态更新

- 直接修改状态对象/数组不触发更新 → 返回新引用（`setList([...list, item])`）
- 在渲染中直接调用 setState → 放进事件或 effect
- 闭包捕获旧值（stale closure）→ 用函数式更新 `setCount(c => c + 1)`，或把值放进依赖数组
- effect 依赖数组缺失或多余 → 逐项核对依赖；需要「仅一次」时用 ref 守卫而非空依赖数组硬扛

## 4 DOM 空引用

```js
const el = document.querySelector('.target');  // 可能为 null
// ❌ el.classList.add('x')  → TypeError
// ✅ if (el) el.classList.add('x');
```

元素在 DOM 就绪前被查询（脚本位置过早）→ 用 `defer` 属性或 `DOMContentLoaded` 后再查询；列表渲染后查询要等渲染完成。

## 5 CORS

**CORS 是服务端问题，客户端改不了**。表现：`Access-Control-Allow-Origin` 缺失或不匹配、预检（OPTIONS）失败、带凭证请求不允许 `*`。

排查与修复：服务端显式配置允许的 origin（不要通配 + credentials 同时用）、方法与请求头；或走同源代理（开发用构建工具的 proxy，生产用网关 / 反向代理）。

## 6 水合不一致（SSR）

表现为「水合失败 / 内容闪烁」：服务端与客户端渲染结果不同。常见原因：渲染中使用 `Date.now()` / `Math.random()` / `window` / `localStorage`；浏览器扩展注入 DOM。

→ 随机与时间相关的值放到 `useEffect` 内生成；访问 `window` 前判空或置于客户端组件；给动态区域 `suppressHydrationWarning` 仅作兜底，不作为首选方案。

## 7 其他高频坑

- 事件监听 / 定时器 / 订阅未在组件卸载时清理 → effect 返回 cleanup
- 移动端视口用 `100vh` 被地址栏遮挡 → `100dvh`（需 `100vh` 兼容时加 fallback）
- `z-index` 无效 → 元素缺少 `position` 或处于不同层叠上下文
- `calc()` 运算符两侧无空格（`calc(100%-2rem)` 失效）→ `calc(100% - 2rem)`
- 表单默认提交导致页面刷新 → `e.preventDefault()`
- 图片未设宽高导致布局跳动（CLS）→ 显式 `width`/`height` 或 `aspect-ratio`
