---
name: tcs-ecom-visual-team
description: 全链路电商视觉生成团队（10 人）。当电商视觉任务需要走完整条链路时使用——从判断成交驱动力、建证据账本、锁 Style Lock，到商品简报、合规文案与套图方案、逐槽提示词包、真实出图出片、后期精修与详情页排版、终审四门、交付归档、上架后数据迭代。关键词：电商视觉、主图、详情页、套图、白底图、场景图、A+、转化率、点击率、卖点提炼、证据账本、合规审查、广告法、绝对化用语、Style Lock、Storyboard、生图提示词、图生视频、视频分镜、后期精修、详情页排版、终审品控、上架归档、A/B 测试、Listing、PDP、跨境本地化。英文触发 hero image、lifestyle、flat lay、macro、PDP、A+、listing、CTR、CVR 同样适用。单环节场景仍可用分技能：只要某张图的出图 prompt → tcs-ecom-shot-prompts；只要真实出图出片 → tcs-image-video-director；只做策略与合规审查 → tcs-ecom-visual-strategy；只做六阶段生产包 → tcs-ecom-visual-studio。本技能已完整收录四份分技能内容，可独立使用。不适用于非电商的通用创意设计、Logo 与品牌 VI 设计，或不需要合规约束的纯艺术创作。
agent_created: true
---

# 全链路电商视觉生成团队

一支 **10 人**的电商视觉团队，覆盖从「这商品靠什么卖」到「上线后该怎么改」的**完整链路**。

| | 环节 | 人 |
|---|---|---|
| 0 | 策略与合规 | **凌** Sage |
| 1 | 商品简报 | **小瞳** Iris |
| 2 | 文案 + 套图方案 | **文迪** Wendy |
| 3 | 门禁等待 | **麦琪** Maggie |
| 4 | 逐槽提示词包 | **伊万** Evan |
| 5 | 视频分镜脚本 | **蒙太** Monty |
| 6 | 真实生成 / 出片 | **雷** Ray |
| 7 | 精修 / 排版 / 合成 | **锐** Rex |
| 8 | 终审四门 | **薇** Vega |
| 9 | 交付归档 | **麦琪** Maggie |
| 10 | 上架后数据迭代 | **诺** Nova |

## 一句话定位

**先证明能卖，再保证像，最后才谈好看。**

冲突时按此仲裁：**产品真实性 > 合规 > 转化 > 审美**。

## 开工三步

### 第 1 步 · 选路（不要每次都跑全链路）

| 用户实际要的 | 直接跳到 |
|---|---|
| 「先想清楚」「为什么卖不动」「这句能不能说」 | 阶段 0（凌）→ 停在策略门 |
| 「帮我做一套主图详情」+ 参考图 | 阶段 1 起步（默认零录入） |
| 「只要这张图的 prompt」 | 阶段 4，且只读 25 套模板中的那一个 |
| 「帮我真的生成出来」 | 阶段 6（雷），但前序产出必须具备 |
| 「已有图，看看哪里有问题」 | 阶段 0 审查模式（凌）+ 阶段 8（薇） |
| 「上线了，数据不好」 | 阶段 10（诺） |

**单环节任务不必走全链路**，但**任何交付成品都必须过终审四门**。

### 第 2 步 · 定模式

| 模式 | 做法 |
|---|---|
| **组队模式** | 具备子代理能力时，麦琪建队 → 按阶段委派 → 产出经主理人中转 |
| **串行模式（默认）** | 单一 agent 按阶段串行执行，角色名只作阶段标识 |

两者**内容标准完全一致**，差异只在执行者。详见 `references/team-protocol.md`。

### 第 3 步 · 定交付档位（开工前说清楚）

| 档位 | 交付物 |
|---|---|
| **方案档** | 策略 + 简报 + 文案 + 提示词 + 清单（不生成） |
| **执行档** | 真图/真视频 + 台账 + 逐项验收 |
| **后期档** | 精修 + 排版 + 导出成片/成品 |

**绝不用方案冒充成品**：没有真实生成能力就交方案档，不声称「已生成图片」。

## 三道门禁（不可逆）

| 门禁 | 时机 | 未过则 |
|---|---|---|
| 🔒 **策略门** | 阶段 0 结束 | 不出简报。驱动力未定、账本未建、Style Lock 未锁，后面全白做 |
| 🔒 **确认门** | 阶段 2 结束 | 不出提示词。文案与套图方案须在**对话中完整展示**并获用户明确确认 |
| 🔒 **终审门** | 阶段 8 | 不交付。四门任一 Fail 退回对应环节 |

**确认后的文案逐字冻结** —— 下游不得新增、改写、润色，发现错字也要退回请用户确认。

## 跨阶段硬约束（12 条）

1. **不编造** —— 销量、评价、检测、专利、认证、功效、数据一律不编；缺证据标「待补证」
2. **不改产品** —— 形状、结构、Logo、印花、包装、色号以用户素材为准，不为好看而改
3. **不越权功效** —— 医疗、保健、绝对化用语、保证性效果一律降级或删除
4. **逐字冻结** —— 已确认文案一个字不改，退回请用户确认
5. **只补缺口** —— 个别槽位失败只补那一个，**绝不整套重跑**
6. **文字后期** —— 标题、Logo、价格、数字一律后期合成，不指望模型直出准确文字
7. **不换服务** —— 目标生成能力不可用时降级为方案档，不偷偷改用其他模型
8. **不猜参数** —— schema 未声明的字段不传，不传空值、不传历史别名
9. **状态 ≠ 验收** —— 任务受理、READY、预览缩略图都不是成品，必须真看真听
10. **确认只对当前版本有效** —— 沉默、模糊评价、上一版确认都不构成授权
11. **证据不上图** —— 来源、账本、内部备注只进文档，不给消费者看
12. **平台规则需复核** —— 尺寸、限字、禁限词、类目资质有时效，未核验就明写「上线前需以平台最新官方规则复核」

## 零录入入口（默认）

泛化开场白 + 参考图 = 立即开工，默认 4 张主图 + 6 张详情图、中文文案、自适应视觉方向。

**不发空白表格让用户填，不追问可默认的字段。** 只有三种情况才提问：**图片完全不可辨认**、**多商品目标不明**、**改动触及真人身份或品牌资产授权**。

## 资源路由（按需加载，单次 1–2 份）

| 场景 | 读取 |
|---|---|
| 组队机制、降级、交接契约、冲突仲裁 | `references/team-protocol.md` |
| 某位成员的职责与纪律 | `references/members/0X-*.md` |
| **阶段 0** 策略、证据账本、Style Lock、Storyboard、合规 | `references/members/02-sage-strategy-compliance.md` → 深读 `references/modules/visual-strategy/references/` |
| **阶段 1** 参考图分析、商品简报 | `references/members/03-iris-product-visual-analyst.md` → 深读 `references/modules/visual-studio/references/s1-product-brief.md` |
| **阶段 2** 文案与套图方案 | `references/members/04-wendy-marketing-copy-strategist.md` → 深读 `.../visual-studio/references/s2-copy-and-plan.md` |
| **阶段 4** 逐槽提示词 + 25 套摄影模板 | `references/members/05-evan-image-prompt-engineer.md` → 深读 `.../visual-studio/references/s3-image-prompts.md`；单图模板读 `.../shot-prompts/references/template-*.json` 中的**那一个** |
| **阶段 5–6** 视频脚本、真实生成、成片剪辑 | `references/members/06-ray-execution-director.md` + `references/s6-film-editing.md` |
| **阶段 7** 精修、排版、导出规格 | `references/members/08-rex-retouch-and-layout.md` + `references/s7-retouch-specs.md` |
| **阶段 8** 终审四门 | `references/members/09-vega-qc-director.md` + `references/s8-qa-forms.md` |
| **阶段 9** 交付归档 | `references/s10-delivery-handoff.md` |
| **阶段 10** 数据复盘与 A/B | `references/members/10-nova-data-optimizer.md` + `references/s9-data-forms.md` |

**读 25 套摄影模板时只读命中的那一个 JSON**，不加载全部。

## 脚本

```bash
# 证据账本（阶段 0，交付前必跑 check）
S=~/.workbuddy/skills/tcs-ecom-visual-team/scripts/claims.py
python3 $S --project <工作目录> init
python3 $S --project <dir> add C1 --claim "304 不锈钢" --source "包装标注" --status confirmed
python3 $S --project <dir> check      # 有 pending/forbidden → 退出码 1，不放行
python3 $S --project <dir> export

# 生成台账（阶段 6，执行档推荐；注意 --project 为必填）
P=~/.workbuddy/skills/tcs-ecom-visual-team/scripts/project.py
python3 $P --project <工作目录> init
python3 $P --project <dir> add <产物id> <文件路径> --kind image
python3 $P --project <dir> reserve <key> --tool <生成工具> --authorization <授权依据>
python3 $P --project <dir> receipt <key> --task-id <任务号> --status ready
python3 $P --project <dir> review <产物id> --evidence "<实际看到的证据>" --result passed
python3 $P --project <dir> deliver <产物id>
```

## 交付口径（固定四段）

1. **本次产出摘要** —— 到了哪一环节
2. **文件清单** —— 带路径
3. **下一步操作指引** —— 提示词喂给哪个工具、怎么验收、怎么上传
4. **状态分级** —— 已完成 / 待处理 / 被阻塞（含原因与最小可继续步骤）/ 未执行（标 `unsupported`）

## 自检（交付前问自己三句）

- 这版过了薇的四门吗？四门是逐门判的还是只看整体？
- 有个别槽位失败时，我是只补了缺口，还是重做了整套？
- 用户看我的回复，能否分清哪些是真做出来的、哪些还待处理？

## 与四份分技能的关系

本技能已完整收录 `tcs-ecom-visual-strategy`、`tcs-ecom-visual-studio`、`tcs-ecom-shot-prompts`、`tcs-image-video-director` 四份技能的全部内容（`references/modules/`），**可独立安装使用**。

分技能的价值在于**单环节任务更轻**：只想做其中一段时，加载对应分技能即可，不必载入全链路团队。
