# 任务台账与验收

生成类任务最容易出的两种事故：**重复提交**（钱花了两次）和**假完成**（状态就绪就说做完了）。本文件用一套最小台账把这两件事堵住。

## 一、状态与阶段

```
阶段：intake → facts → concept → script → assets → prompts → generation → review → assembly → delivery
产物状态：draft | pending | ready | failed | invalidated | accepted
```

规则：每次有效写回 `state_version` 加一；下游只改自己负责的字段，**不得静默改写锁定输入**。

## 二、阶段门（不可跳）

- `facts` 没完成 → 不得确认含事实/声明的正式脚本
- `script` 没确认 → 不得提交高成本生成
- 输入产物不是 `ready/accepted` → 不得供下游提交
- 产物 `ready` → **不等于** 视觉/听觉 `passed`
- 必需视频/声音/字幕未真实装配 → 不得出 `assembly=accepted`
- 有 `pending_actions` 或 `blocked_reason` → 不得标 `delivered`

## 三、确认回执

每次提交付费生成前，必须有一条对应当前版本的明确回执：

```
{ 目标: concept|script_and_shots|generation|retry|delivery,
  版本: N, 用户动作: confirm|revise|cancel|retry, 来源: user_message|confirmation_ui }
```

**不构成确认的东西**：模糊评价（"还行""看看"）、沉默、工具提示、上一版的确认。
用户已经明确说"生成"且范围完整时，直接视为已授权，不重复追问、不主动加积分警告；只有缺关键输入、新增任务、重试、改能力、明显改规格时才补问。

## 四、提交台账

每个确认版本一个唯一键，只提交一次：

```
submission_key = workflow-id:artifact-id:version
{ 工具, 任务号, 状态: not_submitted|submitted|ready|failed|unknown,
  输入产物, 输出产物, submitted_once: true, retry_of: <失败记录键> }
```

- 同一个 key 不得出现两条已提交记录
- 超时/响应丢失 → 键保持 `unknown`，先用原任务号查询；**没有任务号不能凭本地记录断定远端没扣费**
- 重试 = 新键 + `retry_of` + 新回执；旧授权不能自动重跑

## 五、恢复顺序（只回退到最早失效层）

```
工具/权限 → 输入素材 → 事实与锁定项 → 脚本/分镜 → 提示词
        → 单项生成 → 视觉/听觉验收 → 装配 → 导出
```

事实、身份、规格或核心脚本变化 → 沿依赖边把下游标 `invalidated`；纯文字样式或发布时间改动不回退上游。**保留其他已接受的产物，不要整套重做。**

## 六、验收清单

**画面**：主体可辨 → 身份未漂 → 结构/部件/颜色对 → 构图与画幅未截断 → 手部无穿透/多余肢体 → 文字与 Logo 可读且拼写正确 → 运动无伪影跳变 → 产品包装轮廓与开口位置一致 → 卖点是否被真实画面支持

**声音**：旁白可懂、专名与数字准确、原声是否保留、音乐是否盖人声、口型/动作是否同步（仅当模型支持内嵌音频）

**连续性**：上下镜末状态是否接上、共享物件在哪只手、光向是否跨镜一致、同角色是否串脸

**装配**：开头、各切点、字幕窗口、结尾逐段看过；旁白/音乐/环境声实际听过

记录三态：`passed` / `failed` / `不可验证`。**没真的看/听过，不能填 passed。**

## 七、本地台账脚本（可选，执行档推荐）

`scripts/project.py` 是本地防重账本，不联网、不代为提交：

```bash
# 初始化 / 查看
python3 scripts/project.py --project /path/to/proj init
python3 scripts/project.py --project /path/to/proj show

# 登记产物（分镜、参考图、音轨、时间线、成片都算产物）
python3 scripts/project.py --project /path/to/proj add shot-01 /path/clip.mp4 --kind video
python3 scripts/project.py --project /path/to/proj add final /path/final.mp4 --kind assembly --depends-on shot-01 timeline

# 提交前原子占位（同一键二次 reserve 会被拒绝）
python3 scripts/project.py --project /path/to/proj reserve k1 --tool <真实工具名> \
  --inputs brief shot-01 --authorization "用户于 X 确认生成 1 条 5 秒视频"

# 收到真实回执
python3 scripts/project.py --project /path/to/proj receipt k1 --task-id <真实任务号> --status submitted|ready|failed

# 逐项验收（必须写实际证据）
python3 scripts/project.py --project /path/to/proj review shot-01 --result passed --evidence "0.5s/2.8s 抽帧手部无穿透，标签可读"

# 交付（要求 assembly 及其全部依赖都 accepted）
python3 scripts/project.py --project /path/to/proj deliver final

# 待用户决策
python3 scripts/project.py --project /path/to/proj pending "是否接受现有配乐"
python3 scripts/project.py --project /path/to/proj resolve "是否接受现有配乐" --evidence "用户接受"
```

它是**本地防重保护**，不是服务端幂等保证；并发写用排他锁，锁已存在时停止并人工核对。宿主不能跑脚本时，用同结构的 Markdown/JSON 表格代替。

## 八、最终摘要固定六段

工作流与版本 · 已确认产物 · 真实任务/资产状态（含任务号）· 已视觉/听觉检查项 · 未执行层与阻塞原因 · 最终文件或链接 + 下一步。

只有脚本、分镜、提示词或一组未拼接片段时，写"阶段完成"，不能写"成片完成"。
