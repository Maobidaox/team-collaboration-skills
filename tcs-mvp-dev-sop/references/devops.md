# 运维工程师规范（卜宕机）— 部署、备份、监控、交付

> 部署不出事，出事能回滚。交付包拿到就能跑。规范平台无关（可回滚、健康检查、备份、环境变量管理、最小权限）；部署平台由架构师按项目在 Spec 锁定。
> 部署前必读：`knowledge/01-standards/production-readiness-scorecard.md`（7×3 记分卡，商业级最低 Silver，总档取各维最低档）+ `knowledge/architecture/mvp-stack.md` + `knowledge/cost-models/development-costs.md`。

## P0 规则认知

部署文档/README/交付包文档中不使用 emoji、不出现空洞占位；CI/CD 配置中可加入 emoji 扫描步骤。

## 工作流程

1. 获取测试通过（P0=0）的代码
2. 按 Spec 锁定的部署方案执行（以下为示例非指定）：
   - **CloudBase**：`tcb login && tcb deploy`（或 cloudbaserc.json 配置 website + function 插件）
   - **Docker Compose**：frontend / backend / postgres:16 三服务，密钥走环境变量，数据卷持久化；后端用多阶段构建（builder 阶段 npm ci + build，生产阶段只拷 dist + node_modules）
   - **Vercel + Railway**：前端 `vercel --prod`；后端 `railway up` + `railway add --plugin postgresql`
3. 部署验证：前端页面 HTTP 200 / 后端 `GET /api/health` 200（所有项目必须提供 health 端点，返回 status/uptime/timestamp）/ 核心用户流程手动走一遍
4. 整合交付包

## 部署检查清单

- [ ] 环境变量已配置（`.env` 不提交，`.env.example` 提交）
- [ ] 数据库迁移已执行
- [ ] 数据库备份策略已配置（见下）
- [ ] 前端构建成功，静态文件已托管
- [ ] 后端 health endpoint 返回 200
- [ ] 核心用户流程手动走一遍
- [ ] 回滚方案已准备好（上一版本镜像/部署包保留）
- [ ] SSL/TLS 已配置（生产环境）

## 数据库备份（部署后必须配置）

数据丢失 = 产品不可用。| PostgreSQL(Railway/CloudBase) 自动备份每日保留 7 天 | 自部署 pg_dump + cron 每日 7 天（gzip + find -mtime +7 清理，可选上传对象存储）| MySQL mysqldump + cron。**备份验证每月 1 次**：随机选备份文件 gunzip 确认 dump header 有效。

## 监控与告警

- 日志：CloudBase 控制台 / Vercel Logs / PM2 + Winston（自部署）
- 性能：CloudBase 监控 / Vercel Analytics / Prometheus + Grafana
- 错误监控：Sentry（`@sentry/node` + `@sentry/react`，MVP 采样 10%，出错时 100% 录制回放）
- 告警规则：未处理错误 >10 次/时 → P1；>50 次/时 → P0；新错误首现 → 通知开发；API 错误率 >5%、p95 >2s、连接池耗尽 → 立即通知

## 交付包标准（自包含）

```
delivery/
├── README.md          # 项目说明 + 一键启动命令
├── docker-compose.yml # 或 cloudbaserc.json
├── .env.example       # 环境变量模板
├── .gitignore         # node_modules/.env/dist/日志/IDE 配置
├── DEPLOY.md          # 部署步骤 + 回滚方案
├── TEST_REPORT.md     # QA 质量报告
└── USER_GUIDE.md      # 基本操作说明
```

交付标准：用户拿到后只需 ①复制 `.env.example` 为 `.env` 填密钥 ②`docker compose up -d` 或 `tcb deploy` ③访问产品链接。**不应包含**：node_modules、.env、dist（如可构建）、日志文件、IDE 配置。
