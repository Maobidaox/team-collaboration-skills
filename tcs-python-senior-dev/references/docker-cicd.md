# Docker 与 CI/CD 部署规范

> 用途：Python 服务的容器化、流水线与发布规范。

## 一、Dockerfile 最佳实践
- 多阶段构建：构建阶段（装依赖/编译）与运行阶段分离，最终镜像只含运行所需
- 基础镜像：优先 `python:3.x-slim`（体积/安全平衡），锁定 digest 版本
- 非 root 运行：`USER app`，容器内创建普通用户，禁 root 跑服务
- 依赖层缓存：先 COPY 依赖清单并安装，再 COPY 源码（利用层缓存加速构建）
- `.dockerignore`：排除 `.git`、`__pycache__`、`.venv`、测试与本地配置
- `HEALTHCHECK`：定义健康检查命令（如 curl /api/health），供编排系统探活
- 时区与编码：设置 `TZ`、`PYTHONUNBUFFERED=1`、`PYTHONDONTWRITEBYTECODE=1`

## 二、docker-compose 编排
- 服务拆分：app / db / redis / worker 各自独立服务
- 环境变量：`env_file` 或 `${VAR}` 注入，禁把密钥写进 compose 文件提交仓库
- 卷：数据卷挂载数据库存储，代码目录只读挂载（开发热更新除外）
- 资源限制：`mem_limit` / `cpus` 防止单容器吃满宿主机

## 三、CI 流水线（GitHub Actions / GitLab CI 通用）
- 标准阶段：`lint → test → build → scan → deploy`
- 并行与缓存：依赖缓存（uv/pip 缓存目录）、测试并行分片
- 质量门禁：lint 通过 + 单测全绿 + 覆盖率阈值 + pip-audit 无高危，任一失败即阻断
- 镜像：打 tag 用语义版本或 commit SHA，`latest` 仅用于开发环境
- 制品：镜像推送到私有仓库，部署凭证走 CI Secret，不落日志

## 四、部署策略
| 策略 | 适用 | 要点 |
| --- | --- | --- |
| 滚动更新 | 常规发布 | 分批替换，健康检查通过再继续 |
| 蓝绿 | 大版本/风险高 | 新旧两套环境，切流可秒回滚 |
| 金丝雀 | 灰度验证 | 先放 5%–10% 流量，观察指标再放量 |
| 回滚方案 | 所有发布 | 保留上一版本镜像，一键回滚，数据库变更需兼容新旧代码 |

## 五、环境与密钥管理
- 环境分离：dev / staging / prod 独立配置与数据库，prod 禁联调数据
- 密钥：集中密钥管理（Vault / KMS / CI Secret），应用启动时注入，禁明文落盘
- 数据库迁移：发布流程中先跑迁移再切流（向前兼容），大表迁移分批执行

## 六、可观测性基线
- 健康检查：`/healthz`（存活）与 `/readyz`（就绪，依赖就绪后返回 200）
- 日志：JSON 结构化输出，统一字段（time/level/request_id/service）
- 指标：请求量、延迟分位（P50/P99）、错误率、队列积压，接入监控告警
- 链路：分布式调用加 trace_id 透传，便于跨服务排查
