# Django 开发速查

> 用途：Django/DRF 项目的开发与评审速查，覆盖 ORM 性能、REST API、安全与迁移。

## 一、项目结构
- 按业务域拆分 app，每个 app 内聚 model/views/serializers/tests
- settings 分层：base.py / dev.py / prod.py，环境变量管理密钥
- 生产强制：`DEBUG=False`、`ALLOWED_HOSTS` 白名单、HTTPS、安全中间件全开

## 二、ORM 高频操作
- 查询集惰性求值：只有迭代/取值时才执行 SQL
- 防 N+1：
  - 正向外键 → `select_related("fk")`（JOIN）
  - 反向/多对多 → `prefetch_related("related")`（批量 IN 查询）
- 聚合：`aggregate(Sum(...))` / `annotate(...)` 在数据库层计算，别在 Python 里循环求和
- 条件更新避免竞态：`update(views=F("views") + 1)`，先取再改有并发丢更新风险
- 分页：DRF `PageNumberPagination` / `CursorPagination`
- 索引：高频过滤/排序字段加 `db_index=True` 或 Meta.indexes 联合索引

## 三、DRF（Django REST Framework）
- Serializer：输出字段显式声明，不直接序列化整表；嵌套用 `SerializerMethodField` 谨慎（易 N+1）
- ViewSet + Router：标准 CRUD 用 ModelViewSet，自定义动作用 `@action`
- 权限：默认 `IsAuthenticated`，逐接口收紧；越权检查（对象级权限）
- 过滤：django-filter 声明过滤字段，避免前端拼接裸查询
- 限流：`Throttling` 按用户/接口配置

## 四、Admin 与安全
- Admin 仅内网/受限访问，登录加二次验证
- 敏感操作（批量删除）要二次确认；自定义 action 检查权限
- 中间件顺序：SecurityMiddleware 最前；CSRF 对 API 用 TokenAuthentication 而非 Session
- 信号（signal）只做轻量联动（缓存失效、日志），重量逻辑放任务队列

## 五、迁移管理
- `makemigrations` 后必须 `migrate` 并 review 生成的 SQL（大表加字段会锁表，用 `--no-input` + 分批或第三方工具）
- 数据迁移（RunPython）要可逆（forward/reverse 都写）
- 迁移文件入版本库，禁止手动改数据库

## 六、常见坑
| 坑 | 说明 | 正确做法 |
| --- | --- | --- |
| N+1 查询 | 列表页循环取关联 | select_related / prefetch_related + `Prefetch` 过滤 |
| 敏感信息入 settings | SECRET_KEY/数据库密码入库 | 环境变量 + `.env`（不入库） |
| 生产开 DEBUG | 泄露堆栈与配置 | 强制 DEBUG=False |
| 查询全表无过滤 | 慢查询 | 索引 + 明确过滤条件 + 分页 |
| 模板渲染重逻辑 | 视图里跑 SQL 循环 | 数据库层聚合 + 缓存 |
