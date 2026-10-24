# 前端 React / Vue 配套速查

> 用途：与 Python 后端配套的前端工程规范，覆盖 React 与 Vue 两套主流栈，帮助全栈方案落到可运行代码。

## 一、工程基础（两栈通用）
- 脚手架：React 用 Vite + TypeScript；Vue 用 Vite + TypeScript（官方 create-vue）
- 目录结构：`src/api`（请求）、`src/components`（通用）、`src/views|pages`（页面）、`src/stores`（状态）、`src/types`（接口类型）
- 代码规范：ESLint + Prettier 接入 pre-commit；组件文件命名 PascalCase
- 环境变量：`VITE_*` 前缀，禁在前端代码放密钥（前端一切皆可被看到）

## 二、前后端对接规范
- API 客户端：axios 统一封装（baseURL、超时、拦截器），不用散落的 fetch
- 鉴权：token 存内存/HttpOnly Cookie；请求拦截器自动带 token，401 统一跳登录
- 错误处理：拦截器统一弹错/上报；业务错误码与 HTTP 状态码区分
- 状态管理：服务端状态（列表/详情）尽量用请求缓存（React Query / Vue Query）；客户端状态才用 Zustand/Pinia
- 类型同步：后端 Pydantic/DRF Serializer 字段与前端 TS 类型保持一致（可后端导出 OpenAPI → 前端生成类型）

## 三、React 要点
- Hooks：`useState` 本地状态、`useEffect` 副作用、`useMemo`/`useCallback` 按需使用（勿滥用）
- 性能：列表加 `key`（稳定唯一）；大列表虚拟滚动；组件 `React.memo` + 路由级 `React.lazy` 懒加载
- 闭包陷阱：`useEffect` 依赖数组不全导致读到旧值；定时器/订阅必须在清理函数中释放
- 状态提升：跨组件共享状态上提或进 store，避免 props 层层透传

## 四、Vue 要点
- Composition API：`ref`/`reactive` 声明响应式，`computed` 派生值，`watch` 监听变化
- 组合式函数（composables）：可复用逻辑抽成 `useXxx`，如 `useTable`、`useAuth`
- 状态：Pinia 定义 store（`defineStore`），组件内 `storeToRefs` 解构保持响应式
- 性能：`v-for` 配 `:key`；大列表 `v-memo` 或虚拟滚动；组件异步加载 `defineAsyncComponent`
- 生命周期：`onMounted` 中注册的监听器在 `onUnmounted` 移除

## 五、常见坑
| 坑 | 说明 | 正确做法 |
| --- | --- | --- |
| useEffect 无限循环 | 依赖数组传对象/数组字面量 | 依赖基础值，或用 useMemo 稳定引用 |
| 内存泄漏 | setInterval/监听未清理 | 清理函数移除 |
| 请求竞态 | 快速切换时旧响应覆盖新数据 | 忽略过期请求（请求序号/AbortController） |
| 列表 key 用 index | 增删后状态错乱 | 用业务唯一 id |
| token 存 localStorage | XSS 可窃取 | 优先 HttpOnly Cookie 或内存存储 |
| 打包体积大 | 全量引入 | 按需引入 + 路由懒加载 + 拆包 |

## 六、交付要求
- 全栈方案中前端部分必须给出：目录结构、关键组件/页面代码、API 调用示例、与后端的接口字段约定
- 涉及鉴权、上传、分页、错误处理的代码要可直接运行
