# 脚手架与基础设施清单（Phase 2）

逐项落地。每项给出「做什么 / 为什么 / 验证方式」。骨架搭完再写业务，顺序不要倒。

## 1. 项目结构：按功能组织

```
src/
├── config/           # 集中配置 + 启动校验
├── common/
│   ├── errors/       # 类型化错误体系
│   ├── middleware/   # 错误处理、日志、认证、校验
│   └── logging/      # 结构化日志
├── features/         # ★ 按功能切片，每个功能自闭环
│   └── user/
│       ├── user.controller.ts    # 只做 HTTP 进出
│       ├── user.service.ts       # 业务规则，不 import HTTP 类型
│       ├── user.repository.ts    # 数据访问
│       └── user.dto.ts           # 入参校验 schema
├── db/
│   ├── migrations/   # 可回滚迁移
│   └── pool.ts       # 连接池
├── jobs/             # 后台任务（幂等 + 重试 + 死信）
└── server.ts         # 组装、优雅停机
```

**为什么按功能**：改一个业务只需打开一个目录，跨层跳转成本最低；按技术层平铺（controllers/ services/ repositories/ 三大目录）会让单次改动横跨三处。

## 2. 集中配置 + 启动校验（快速失败）

配置全部来自环境变量，启动时一次性校验，**缺项立即退出**，不要等到运行到某行才炸。

```ts
// config/env.ts
const required = ['DATABASE_URL', 'JWT_SECRET', 'CORS_ORIGIN'] as const;
const env = Object.fromEntries(required.map(k => [k, process.env[k]]));
const missing = required.filter(k => !env[k]);
if (missing.length) {
  console.error(`缺少必需环境变量: ${missing.join(', ')}`);
  process.exit(1);                       // 快速失败
}
export const config = {
  db: env.DATABASE_URL!,
  jwtSecret: env.JWT_SECRET!,
  corsOrigin: env.CORS_ORIGIN!.split(','), // 显式来源，不用 '*'
  port: Number(process.env.PORT ?? 3000),
};
```

Python 侧用 pydantic-settings 的 `BaseSettings` 达到同样效果（字段必填 + 启动时校验）。

**验证**：故意删掉一个变量启动，服务应在 1 秒内退出并打印缺失项，而不是启动成功后首个请求才 500。

## 3. 类型化错误体系 + 全局处理器

```ts
export class AppError extends Error {
  constructor(
    public code: string,          // 'USER_NOT_FOUND' —— 机器可读
    message: string,              // 人可读，可安全展示给前端
    public status: number,        // 400/401/403/404/409/500
    public details?: unknown,     // 仅开发环境回传
  ) { super(message); }
}
export const badRequest = (m: string, d?: unknown) => new AppError('BAD_REQUEST', m, 400, d);
export const notFound   = (m: string) => new AppError('NOT_FOUND', m, 404);
export const conflict   = (m: string) => new AppError('CONFLICT', m, 409);
```

全局处理器（**中间件顺序：日志 → CORS → 认证 → 路由 → 404 → 错误处理器**，错误处理器必须最后注册）：

```ts
app.use((err, req, res, next) => {
  const isApp = err instanceof AppError;
  const status = isApp ? err.status : 500;
  const code   = isApp ? err.code   : 'INTERNAL_ERROR';
  const message = isApp ? err.message : '服务暂时不可用';
  if (status >= 500) logger.error({ requestId: req.id, err });   // 5xx 才打完整堆栈
  else logger.warn({ requestId: req.id, code });
  res.status(status).json({ code, message, requestId: req.id }); // ★ 绝不回传 err.stack
});
```

**验证**：抛一个未捕获异常 → 客户端拿到 500 + `{code:'INTERNAL_ERROR', message:'服务暂时不可用', requestId}` 且**无堆栈**；抛 `notFound` → 404 + 明确文案。

## 4. 结构化 JSON 日志 + 请求 ID

- 请求入口生成 `requestId`（UUID），挂到 `req.id`，写入响应头与每条日志
- 日志用 JSON 行输出，字段固定：`ts / level / requestId / method / path / status / durationMs / msg`
- **脱敏**：密码、令牌、身份证、手机号不落日志；对 `authorization` / `password` / `token` 字段做递归遮蔽
- 级别：5xx 用 error，4xx 用 warn，正常请求用 info

```ts
const REDACT = new Set(['password','token','authorization','secret','idCard','phone']);
const redact = (o: any): any =>
  Array.isArray(o) ? o.map(redact)
  : o && typeof o === 'object'
    ? Object.fromEntries(Object.entries(o).map(([k,v]) => [k, REDACT.has(k.toLowerCase()) ? '***' : redact(v)]))
    : o;
```

## 5. 数据库：迁移 + 连接池 + 事务

- **变更一律走迁移**，每个迁移必须能回滚（`up` / `down` 成对）。禁止手写 SQL 改生产库。
- 连接池显式配置：`max`（并发上限）、`idleTimeout`、`connectionTimeout`；不要把 pool 设成无上限。
- 多步写入包事务；事务内不做网络调用与长耗时操作。
- 避免 N+1：列表查询用 `JOIN` 或批量 `WHERE IN`，不要用循环里单条查。
- 缓存必设 TTL，写入成功后**失效**（而不是更新）对应 key。

## 6. 边界输入校验

所有入参在控制器入口用 schema 校验（zod / Joi / pydantic），校验通过后才进服务层。服务层可以信任入参，因此不必重复校验。

```ts
const CreateUserDto = z.object({ email: z.string().email(), password: z.string().min(8) });
const body = CreateUserDto.parse(req.body);   // 失败由全局处理器转 400
```

## 7. 健康检查：两个端点，语义不同

| 端点 | 检查内容 | 用途 |
|------|---------|------|
| `GET /health` | 进程存活即可（不查依赖） | 负载均衡存活性探针 |
| `GET /ready` | 数据库连通 + 迁移已执行 + 关键依赖可用 | 就绪探针，未就绪不接流量 |

**常见坑**：两个端点都查数据库 → 数据库抖动时存活探针失败 → 容器被反复重启，故障放大。

## 8. 优雅停机

```ts
const server = app.listen(config.port);
for (const sig of ['SIGTERM', 'SIGINT']) {
  process.on(sig, () => {
    logger.info({ msg: 'shutdown: 停止接收新请求' });
    server.close(async () => {          // 先停止接新连接
      await db.pool.end();              // 再释放连接
      await jobQueue.close();           // 收尾后台任务
      logger.info({ msg: 'shutdown: 完成' });
      process.exit(0);
    });
    setTimeout(() => process.exit(1), 30_000);  // 兜底强制退出，避免挂死
  });
}
```

**验证**：`kill -TERM <pid>` → 日志出现停止接新请求 → 在途请求正常返回 → 30 秒内进程退出，无连接泄漏。

## 9. CORS 与安全头

```ts
app.use(cors({
  origin: config.corsOrigin,   // ★ 显式数组，生产绝不用 '*'
  credentials: true,           // 需要带 Cookie/授权头时
  methods: ['GET','POST','PUT','PATCH','DELETE'],
}));
app.use(helmet());             // CSP / HSTS / X-Content-Type-Options 等
```

- 需要携带凭证时 `Access-Control-Allow-Origin` 不能是 `*`，必须回显具体来源
- 生产强制 HTTPS（HSTS）、禁用 `X-Powered-By` 暴露框架版本
- 敏感接口加限流（按 IP + 用户 ID 双维度）

## 10. .env.example（唯一提交进仓库的环境文件）

```
# 复制为 .env 后填入真实值；.env 已在 .gitignore 中
DATABASE_URL=postgres://user:password@localhost:5432/app
JWT_SECRET=change-me
CORS_ORIGIN=http://localhost:5173
PORT=3000
```

提交前自检：`git status` 中**不应出现 `.env`**；`grep -r "JWT_SECRET=" --include="*.ts" .` 应无结果（值不进代码）。

## 落地顺序建议

配置校验 → 错误体系 → 日志 → 迁移+连接池 → 校验中间件 → 认证中间件 → 健康检查 → 优雅停机 → 业务功能。
前八项约占总工作量 20%，但决定了后 80% 的可靠性，不要为了「先看到效果」跳过。
