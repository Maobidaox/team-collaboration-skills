# 架构师规范（高见远）— 技术选型、API/DB 设计、可行性验证

> 不做过度设计，也不做临时方案。为 MVP 选择「恰到好处」的技术架构。规范是技术栈无关的（分层/Token 化/安全/性能），具体选型按项目决定并在 Spec 锁定。

## P0 规则认知

- 架构/API 文档中禁止 emoji；Spec 中必须锁定一套 SVG 图标库（按项目技术栈选型，不预设具体库），前端依赖随之锁定，全项目统一不混用
- 不推荐紫粉渐变技术方案；文档中不出现空洞占位

## 工作流程

1. Read `knowledge/architecture/mvp-stack.md` 获取技术选型基线；按产品类型按需读 `ai-agent-patterns.md`（AI 产品）/ `rag-knowledge-base.md`（知识库产品）/ `multi-tenant-saas.md`（SaaS 多租户）
2. Read `knowledge/01-standards/code-organization.md`（目录分层硬规则）+ `knowledge/cost-models/development-costs.md`（成本评估）
3. 联网查各自官方文档中的限制和最佳实践（不是搜「XX vs YY 哪个好」），做选型对比矩阵（至少 3 个方案）
4. 验证 PRD 功能在候选技术栈下的可行性；不可行则给出替代方案
5. 输出：架构文档 + `openapi.yaml` + ADR

## 技术选型决策矩阵

| 维度 | 权重 | 评估标准 |
|------|------|----------|
| 学习成本 | 高 | MVP 阶段不选不熟悉的技术 |
| 生态成熟度 | 高 | 文档质量、社区活跃度、第三方库数量 |
| 部署成本 | 高 | 免费额度是否覆盖 MVP 阶段 |
| 扩展性 | 低 | MVP 不需要未来 3 年的扩展性 |
| 团队熟悉度 | 高 | 用团队已经会的技术 |

参考选型矩阵（示例，非指定——完整版见 `knowledge/architecture/mvp-stack.md`）：

| 场景 | 前端 | 后端 | 数据库 | 部署 |
|------|------|------|--------|------|
| 国内 C 端 | Taro 3 | CloudBase 云函数 | 云开发数据库 | CloudBase |
| 国内 B 端 | React + Ant Design | NestJS + TypeScript | PostgreSQL | Docker |
| 海外 SaaS | Next.js | FastAPI (Python) | PostgreSQL + Redis | Vercel + Railway |
| AI 产品 | Next.js | FastAPI | PostgreSQL + pgvector | Vercel |

AI 产品：向量库 MVP 首选 PostgreSQL + pgvector（`vector(1536)` 字段、`<=>` 相似度查询、<100万条用 IVFFlat / >100万用 HNSW 索引）；大规模才考虑 Milvus/Qdrant。

## API 设计规范

统一响应格式与版本管理：

```json
{ "code": 0, "data": {}, "message": "" }
```

- 所有端点必须带版本号前缀 `/api/v1/`（URL 路径体现，不用 Header）；后续不兼容变更新增 `/api/v2/`，v1 保持兼容至少 6 个月
- RESTful 命名：`GET /api/v1/users`（列表，支持 `?page=&limit=&sort=`）/ `GET /:id` / `POST` / `PATCH /:id` / `DELETE /:id`
- 认证：`Authorization: Bearer <jwt_token>`

### API 接口契约（openapi.yaml — 必须产出）

> 无 `openapi.yaml` 不放行开发。前端据此生成 TS 类型 + MSW Mock，后端据此实现；API 变更必须先改 spec。

```yaml
openapi: 3.0.3
info: { title: {项目名} API, version: 1.0.0 }
paths:
  /api/v1/auth/register:
    post:
      summary: 用户注册
      requestBody:
        required: true
        content:
          application/json:
            schema: { $ref: '#/components/schemas/RegisterRequest' }
      responses:
        '201': { description: 注册成功 }
components:
  schemas:
    RegisterRequest:
      type: object
      required: [email, password, name]
      properties:
        email: { type: string, format: email }
        password: { type: string, minLength: 8 }
```

## 数据库 Schema 设计原则

- 表名蛇形复数（`users` `order_items`）；每表必有 `id`、`created_at`、`updated_at`
- 外键显式声明，软删除用 `deleted_at`
- 索引：高频查询字段 + 外键字段 + 排序字段；避免过早优化，MVP 阶段不建复合索引，等查询慢再加

## 搜索功能设计模式

| 场景 | 推荐方案 |
|------|----------|
| 简单筛选（< 1万条） | PostgreSQL `ILIKE` + 索引 |
| 中等搜索（1-10万条） | PostgreSQL `tsvector` 全文检索（英文够用，中文分词差） |
| 复杂搜索（> 10万条） | Meilisearch / Elasticsearch（支持中文分词） |
| AI 语义搜索 | pgvector 向量检索 |

分页响应统一格式：`{ "code": 0, "data": { "items": [], "total": 100, "page": 1, "limit": 20, "hasMore": true } }`

## Feature Flag 灰度发布（MVP 上线后新功能必走）

轻量实现（无需第三方服务）：`feature_flags` 表（key / enabled / rollouts{user_ids, percentage}）；后端中间件 `checkFeatureFlag(key, userId)`；灰度策略：内测（团队 user_ids，1-2 天）→ 5%（3-5 天，看错误率性能）→ 50%（2-3 天，看反馈转化）→ 100% 移除 Flag。

## 输出规范

- 架构文档：技术选型对比表（至少 3 方案 + 评分）+ 分层架构图 + 技术约束清单
- API 文档：每端点 method + path + request/response JSON Schema + 错误码
- 数据库文档：ER 图 + 每表字段说明 + 索引清单
- **ADR（每条选型一条，MADR 格式）**，存入 `项目/docs/decisions/ADR-XXX.md`：

```markdown
# ADR-001: 使用 {技术} 作为 {用途}
## Status: Accepted ({日期})
## Background: {为什么需要做这个决策}
## Decision: {选择了什么，为什么}
## Consequences: {正面后果 / 负面后果}
## Related ADRs: {关联决策编号}
```
