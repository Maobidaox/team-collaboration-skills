# FastAPI 后端开发速查

> 用途：FastAPI 项目的架构、写法与常见坑速查，支撑代码生成与评审。

## 一、推荐项目结构
```
app/
  main.py          # 应用入口、路由注册、中间件
  core/            # 配置、安全、依赖
    config.py      # pydantic-settings 配置
  api/v1/          # 路由层（只做参数校验与响应组装）
    routers/       # 按业务域拆分路由
  models/          # SQLAlchemy ORM 模型
  schemas/         # Pydantic 请求/响应模型
  services/        # 业务逻辑层（不感知 HTTP）
  repositories/    # 数据访问层
```

## 二、核心写法
- 路由：`@router.get("/items/{item_id}", response_model=ItemOut, status_code=200)`
- 依赖注入：`Depends(get_db)`、`Depends(get_current_user)`，依赖里做校验与资源获取
- 请求校验：Pydantic 模型（字段类型、约束 `Field(gt=0)`、`validator` / `field_validator`）
- 响应：一律用 `response_model` 控制输出字段，禁止直接返回 ORM 对象
- 配置：`pydantic-settings` 读环境变量，敏感项不入代码
- 异步：IO 操作用 `async def`；同步阻塞库用 `run_in_threadpool` / `anyio.to_thread`
- 后台任务：`BackgroundTasks` 做邮件、通知等轻量任务；重量任务用 Celery/ARQ

## 三、SQLAlchemy 2.0 集成要点
- 声明式：`class Base(DeclarativeBase)`，模型用 `Mapped` + `mapped_column`
- Session：依赖中 `yield` 模式，请求级会话，用完关闭
- 查询：`select(User).where(User.email == email)`，避免裸字符串 SQL
- 关联加载：`selectinload` / `joinedload` 预防 N+1
- 事务：`async with session.begin():`，明确提交/回滚边界

## 四、中间件与异常
- CORS：按域名白名单配置，生产禁 `allow_origins=["*"]`（含凭据时）
- 统一异常：自定义 `HTTPException` handler，返回 `{"code": ..., "message": ...}` 统一结构
- 请求日志：记录 method、path、耗时、状态码，不记录 body 敏感字段
- 限流与超时：网关或中间件层处理

## 五、分页规范
- 小数据量：`offset/limit`（带上限，如 limit ≤ 100）
- 大数据量：游标分页（基于 id/时间戳），避免深 offset
- 统一返回：`{items: [...], total: n, page: p, size: s}`

## 六、常见坑
| 坑 | 说明 | 正确做法 |
| --- | --- | --- |
| 事件循环阻塞 | `async def` 内调同步阻塞 IO | 用 `run_in_threadpool` 或改真异步库 |
| 依赖重复执行 | 多个 `Depends` 同一函数会重复调用 | 用 `Depends(x, use_cache=True)`（默认即缓存） |
| 返回 ORM 对象 | 泄露内部字段/触发懒加载 | 经 Pydantic `response_model` 序列化 |
| 密码明文存储 | | bcrypt/argon2 哈希，绝不明文 |
| 全局可变状态 | 多 worker 下内存态不一致 | 状态放 Redis/数据库 |
