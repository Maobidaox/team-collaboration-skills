# 认证授权与前后端集成（Phase 3–4）

## 一、令牌方案：短时效访问令牌 + 服务端刷新令牌

| | 访问令牌（Access） | 刷新令牌（Refresh） |
|---|---|---|
| 时效 | 10–15 分钟 | 7–30 天 |
| 载荷 | userId、role、权限点（够用即可，别塞全量资料） | userId + 令牌族 ID |
| 存放 | 前端内存（变量 / 状态库） | 服务端持久化（DB 或 Redis），前端只持有 HttpOnly Cookie |
| 泄露影响 | 窗口小 | 可撤销 |

**禁止**：令牌写入 `localStorage`（XSS 直接拿走）、令牌放进 URL 查询参数（进浏览器历史与referer、进服务端访问日志）。

### 刷新令牌轮换 + 重用检测

刷新时必须**轮换**（签发新的、作废旧的），并检测重用：若一个已作废的刷新令牌再次出现，说明泄露，立即作废该用户整个令牌族并强制重新登录。

```
POST /auth/refresh
  请求: HttpOnly Cookie 携带 refreshToken
  服务端: 查库 → 已作废? → 是: 作废该用户全部 refresh + 返回 401（疑似泄露）
                        → 否: 作废旧的、签发新的、更新 Cookie
  响应: { accessToken, expiresIn }
```

## 二、中间件顺序（顺序错了认证等于白做）

```
请求 ID / 日志
  → CORS
  → 安全头
  → 限流
  → 解析 body
  → 认证（解析令牌 → 挂 req.user）      ★ 必须在路由前
  → 授权（RBAC 校验角色/权限点）
  → 路由处理（控制器 → 服务 → 仓储）
  → 404 兜底
  → 全局错误处理器                      ★ 必须最后
```

**RBAC 粒度**：先角色后权限点。粗粒度用角色（admin/user），细粒度用权限字符串（`order:write`），权限点挂在令牌或每次查库（权限变更需即时生效时查库）。

**易错点**：只在中路由上加了认证中间件，而新增路由忘了加。做法是「默认全部需要认证 + 显式白名单放行」而不是「默认开放 + 逐个加」。

## 三、前端：401 自动刷新并重放

```ts
let refreshing: Promise<string> | null = null;

export async function api<T>(path: string, init: RequestInit = {}): Promise<T> {
  const res = await fetch(`${import.meta.env.VITE_API_BASE}${path}`, {
    ...init,
    credentials: 'include',               // 带上 HttpOnly 刷新 Cookie
    headers: { 'Content-Type': 'application/json',
               Authorization: `Bearer ${tokenStore.access}`, ...init.headers },
  });

  if (res.status === 401 && !path.startsWith('/auth/')) {
    refreshing ??= refresh().finally(() => { refreshing = null; });
    const next = await refreshing.catch(() => { tokenStore.clear(); gotoLogin(); throw new AuthError(); });
    return api(path, { ...init, headers: { ...init.headers, Authorization: `Bearer ${next}` } }); // 重放
  }
  if (!res.ok) throw new ApiError(await res.json());
  return res.json() as Promise<T>;
}
```

要点：并发 401 时**共用同一个 refreshing Promise**（否则会并发刷新、互相作废）；刷新失败才登出。

## 四、API 客户端方案选型

| 方案 | 适用 | 代价 |
|------|------|------|
| 类型化 fetch 封装 | 小团队、接口少、不想引入框架 | 缓存/重试/失效都要自己写 |
| React Query / SWR | 前端重、需要缓存与失效、乐观更新 | 多一层心智，需理解 key 设计 |
| tRPC | 全栈 TypeScript 同仓 | 绑定 TS，非 TS 客户端难接入 |
| OpenAPI 生成客户端 | 后端已有 OpenAPI、多语言客户端 | 需维护规范与生成步骤 |

**跨端类型安全**：TS 全栈优先共享类型包或从后端导出 DTO 类型；非 TS 后端则维护 OpenAPI 规范并生成。

**Base URL 必须走环境变量**（`VITE_API_BASE` / `NEXT_PUBLIC_API_BASE`），禁止硬编码 `http://localhost:3000`。交付前 Grep 自检。

## 五、错误映射：把后端错误翻成人话

后端统一返回 `{ code, message, requestId }`。前端维护一张映射表：

```ts
const MAP: Record<string, string> = {
  BAD_REQUEST:   '提交的信息有误，请检查后重试',
  INVALID_CREDENTIALS: '账号或密码不正确',
  CONFLICT:      '该记录已存在，请勿重复提交',
  RATE_LIMITED:  '操作过于频繁，请稍后再试',
  INTERNAL_ERROR:'服务开小差了，请稍后重试',
};
const hint = (code: string) => MAP[code] ?? '操作失败，请稍后再试';
```

硬规则：
- **4xx 不重试**（重试也不会成功），**5xx 自动重试最多 3 次**且带指数退避
- 网络层失败（`fetch` reject）→ 显示「网络似乎断开了，请检查连接」，而不是静默或空列表
- 表单类 400 优先展示后端返回的字段级 `details`，而不是笼统一句文案
- **绝不把后端 message 原样裸奔到 UI**（内部措辞可能含技术细节）；映射表兜底

## 六、加载态与错误态（交付前逐页自检）

每个发起请求的视图都要有四种状态，缺一即为未完成：

| 状态 | 表现 |
|------|------|
| loading | 骨架屏或 spinner，**首屏必须有** |
| empty | 空数据插画 + 引导，不能是白屏 |
| error | 可读文案 + 重试按钮 |
| success | 正常渲染 |

Grep 自检清单：
```
grep -rn "localhost:[0-9]" src/            # 硬编码 URL
grep -rn "出错了\|error occurred\|Error!" src/ # 占位错误提示
grep -rn "useState" src/ | wc -l            # 对比请求调用数，判断是否有缺失 loading
```

## 七、文件上传要点

- 不要在请求处理器里做耗时转码/压缩 → 落盘后投递后台任务
- 限制大小、白名单 MIME（**不要只信客户端 Content-Type**， sniff 文件头）
- 上传文件名重命名（防路径穿越与覆盖），原始名存 DB 用作展示
- 直传对象存储时用后端签发的短期预签名 URL，不要暴露长期密钥
- 上传接口同样要鉴权，别因为「是上传接口」就放行
