# 验证四步与交付总结（Phase 5）

**顺序不可跳过，前一步不过不进入下一步。**「写完代码看着对」不算完成，四步全过才算。

## 第 1 步：编译检查

```bash
# 后端
npm run build        # 或 tsc --noEmit / go build / mvn compile
# 前端
npm run build        # 或 vite build / next build
```

要求：**零错误**。警告也要看一眼，尤其是类型相关的。

## 第 2 步：启动冒烟（Bash + curl 实测，不是「应该能跑」）

```bash
npm run dev &                      # 或 docker compose up
sleep 3
curl -s localhost:3000/health                       # 期望 200 {"status":"ok"}
curl -s localhost:3000/ready                        # 期望 200（DB 已就绪）
curl -s -X POST localhost:3000/api/auth/login \
     -H 'Content-Type: application/json' \
     -d '{"email":"a@b.com","password":"wrong"}'    # 期望 401 + 规范错误体
```

逐端点验证，至少覆盖：健康检查 ×2、登录成功/失败各一、一个受保护路由（无令牌 → 401；有令牌 → 200）、一个写接口（成功 + 校验失败两种）。

**每测一条都要写清实际返回的 HTTP 状态与响应片段**，不要用「正常」概括。

## 第 3 步：集成检查（前端真能连上后端）

打开前端页面，实际走一遍：
- 页面能加载，无 CORS 报错（控制台无 `blocked by CORS policy`）
- 登录成功 → 拿到令牌 → 访问受保护数据成功
- 令牌过期 → 自动刷新 → 原请求重放成功（把访问令牌时效临时调到 30 秒来测）
- 断网 → 显示离线提示，不是白屏或静默失败

## 第 4 步：实时检查（仅当引入实时能力时）

**双标签页**打开同一页面，在一侧做操作，另一侧应在预期时间内看到变化。再测断线：停掉服务端 → 客户端应有断开提示 → 重启服务端 → 自动重连 → 增量补齐断线期间的数据。

## 交付总结模板

```markdown
## 已实现
- 功能：<功能一句话>
- 端点：
  | 方法 | 路径 | 说明 | 鉴权 |
  |------|------|------|------|
  | POST | /api/auth/login | 登录，返回访问令牌 + 设置刷新 Cookie | 否 |
  | GET  | /api/orders     | 分页订单列表                        | 是 |
  | POST | /api/orders     | 创建订单（事务写入 + 库存扣减）      | 是 |

## 验证结果
- 编译：后端 tsc 通过 / 前端 vite build 通过
- 冒烟：/health 200、/ready 200、登录 200、无令牌访问 /api/orders → 401
- 集成：前端登录→拉列表成功；令牌过期自动刷新并重放成功
- 实时：双标签页同步 <1s；断线 5s 后重连并补齐

## 启动命令
cp .env.example .env   # 填真实值
docker compose up -d   # 起数据库
npm run migrate && npm run dev

## 关键文件
- src/config/env.ts          配置与启动校验
- src/common/errors/         错误体系
- src/features/order/        订单功能（controller/service/repository 三层）

## 遗留与建议
- [ ] 未实现：订单导出（建议用后台任务 + 对象存储，见 realtime-and-hardening.md）
- [ ] 待加固：当前无限流，上线前需加（登录接口优先）
- [ ] 建议：补集成测试，当前仅覆盖冒烟路径
```

## 测试策略

- **单元测试** mock 仓储层，保持快（毫秒级），覆盖服务层业务规则分支
- **集成测试** 用真实数据库（容器或事务回滚），**不要为了速度 mock 服务层** —— mock 掉服务层的集成测试等于什么都没测
- **E2E** 覆盖关键路径（注册→登录→核心操作），数量少而精
- 断言要验证行为与结果，不要为了覆盖率断言「函数被调用过」

```ts
// 反例：为了覆盖率而写
expect(repo.save).toHaveBeenCalled();
// 正例：验证行为
await expect(service.createOrder(input)).rejects.toThrow('INSUFFICIENT_STOCK');
expect(await repo.findStock(skuId)).toBe(stockBefore);   // 事务回滚后库存未变
```

## 常见「假完成」信号（出现即打回）

| 信号 | 说明 |
|------|------|
| 「应该可以」「理论上没问题」 | 没实测，回到第 2 步 |
| 只测了成功路径 | 补失败路径与边界 |
| 未验证 CORS | 前端起来再点一次，看控制台 |
| 令牌相关没测过期 | 把时效调短实测一次 |
| 后端跑起来了但前端没打开过 | 第 3 步没做 |
| 端点清单靠回忆写 | 从路由文件里 Grep 出来 |
