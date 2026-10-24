# Python 安全加固指南（OWASP 实践映射）

> 用途：Python 应用的安全设计、评审与加固清单，按 OWASP Top 10 映射到 Python 具体实践。

## 一、注入类（A03）
- SQL 注入：只用参数化查询 / ORM，禁止 f-string 拼接 SQL；动态排序字段用白名单映射
- 命令注入：`subprocess` 一律传参数列表（`["ls", "-l"]`），禁 `shell=True`；禁 `os.system`/`eval`/`exec` 处理外部输入
- 模板注入：用户输入进 Jinja2 前确认沙箱/转义，不渲染不可信模板
- 反序列化：禁 `pickle` 加载不可信数据（RCE 风险），用 JSON/msgpack

## 二、身份认证与访问控制（A01/A07）
- 密码：bcrypt / argon2 哈希（自带盐），禁 MD5/SHA1 明文存储
- 会话：JWT 设置过期与签名校验，敏感操作要求二次验证；登录失败限速（防爆破）
- 越权：每个资源接口校验"资源归属 == 当前用户"（IDOR），不只靠前端隐藏按钮
- 权限模型：RBAC 统一封装装饰器/依赖，勿散落各处判断

## 三、加密与数据保护（A02）
- 传输：全站 HTTPS（HSTS 头），内部服务间 TLS
- 存储：敏感字段（手机号/身份证）加密或脱敏存储；日志不打印密码、token、完整 PII
- 密钥管理：不入代码/版本库，用环境变量或密钥管理服务（Vault/云 KMS），定期轮换

## 四、安全配置（A05）
- 生产强制：Django `DEBUG=False`、FastAPI 关闭 docs（或加访问控制）
- 默认凭据清零：数据库、Redis（禁 `protected-mode no` 无密码）、管理后台
- 安全响应头：`X-Content-Type-Options`、`Content-Security-Policy`、`X-Frame-Options`、`Referrer-Policy`
- CORS：白名单精确到域名，禁 `*`（尤其携带凭据时）

## 五、依赖与供应链（A06/A08）
- 依赖锁定：锁文件（uv.lock / requirements-lock）入版本库
- 漏洞扫描：`pip-audit` 接 CI，高危 CVE 阻断发布；`bandit` 静态安全扫描
- 镜像与制品：基础镜像锁定 digest，构建产物签名，CI 产物不可信内容不直接执行

## 六、SSRF 与文件安全（A10）
- SSRF：请求外部 URL 前校验协议（仅 http/https）与目标 IP（禁内网/云元数据地址 169.254.169.254）
- 文件上传：白名单扩展名 + 内容嗅探 + 大小限制 + 随机文件名；存储与执行目录隔离
- 路径穿越：拼接用户输入路径时用 `os.path.realpath` 校验前缀；下载文件时校验文件名

## 七、日志与监控（A09）
- 结构化日志（JSON），关键操作留痕：登录、权限变更、删除、导出
- 敏感字段日志脱敏中间件
- 告警：登录失败风暴、5xx 突增、异常提权行为

## 八、评审必查清单
- [ ] 所有 SQL 参数化，无拼接
- [ ] 无 eval/exec/pickle 处理外部输入
- [ ] 密码 bcrypt/argon2，会话有过期
- [ ] 每个接口做了归属校验（防 IDOR）
- [ ] DEBUG 关闭、安全头齐全、CORS 白名单
- [ ] 密钥在环境变量/KMS，不在代码
- [ ] pip-audit 无高危漏洞
- [ ] 上传/下载无路径穿越，SSRF 有防护
