---
name: tcs-ecom-shot-prompts
description: 电商商业摄影提示词工坊。当用户需要电商产品图的出图提示词（不是图本身）时使用——主图、白底图、场景图、平铺图、细节微距、海报 Banner、社媒帖、UGC 买家秀、模特图、前后对比、包装、A+ 信息图、创意概念、尺寸规格、多品套装、直播间、虚拟试穿、拆解图、隐形模特、多角度网格、杂志大片、季节营销、奢华氛围、设备样机、店铺门面、运动广告，共 25 套场景模板，每套预置布光/构图/背景方案与 3–4 个风格变体。关键词：主图、白底图、场景图、详情页、A+、买家秀、UGC、真实感、海报、Banner、平铺、微距、模特、试穿、拆解图、爆炸图、隐形模特、多角度、杂志封面、直播间、门面、运动广告、prompt、提示词、布光、构图。英文触发 hero image、lifestyle、flat lay、macro、poster、social media、UGC、GRWM、ghost mannequin、exploded view、mockup、storefront 同样适用。交付物是可直接粘贴到即梦/Midjourney/豆包/Canva 的 prompt 文本与使用建议，不执行生图、不调 API。仅需整套电商视觉生产方案（含合规文案与成片质检）时改用 tcs-ecom-visual-studio。用户还在定策略阶段（判断成交驱动力、建证据账本、锁 Style Lock、审查已有页面转化与合规）时先走 tcs-ecom-visual-strategy，不要直接给 prompt。
agent_created: true
---

# 电商商业摄影提示词工坊

把卖家一句"帮我出张主图"，翻译成**布光、构图、背景都定好的商业摄影语言**，交出一段能直接粘到任何生图工具里的 prompt。

**交付物是 prompt 文本，不是图片。** 本技能不执行生图、不调 API、不承诺生成效果——只保证 prompt 结构完整、场景匹配、反 AI 清单已过。

## 与其他技能的分工

| 场景 | 用谁 |
|---|---|
| 要**一段 prompt**，自己拿去即梦/MJ/豆包生成 | **本技能** |
| 要**整套视觉生产方案**：商品简报 + 合规文案 + 套图规划 + 质检清单 + 视频脚本 | `tcs-ecom-visual-studio` |
| 已确认要做**真实生成**（有生图能力，要出图并验收） | `tcs-image-video-director` |

三者可串：本技能出 prompt → 粘到生图工具 → 用 `tcs-image-video-director` 的验收清单核对。

## 五步流程

| # | 步骤 | 做什么 |
|---|---|---|
| ① | 接需求 | 提取品类、产品描述、材质、卖点、想要的图、风格偏好、有无产品白底图 |
| ② | 识别场景 | 判断属于 25 类中哪一类；没明说就按用途推断（上架→主图，种草→社媒帖，详情页→信息图） |
| ③ | 匹配模板 | 按下表读**那一个** JSON，不加载全部 |
| ④ | 组装 prompt | 套骨架 → 填变量 → 应用变体 → 叠品类要点 → 精简空字段 |
| ⑤ | 出建议 | 工具选择、要不要传参考图、文字风险、可换的变体 |

**缺关键信息（产品是什么、要什么场景）先问，一次问全，不瞎猜产品细节。** 能推断的（画幅、默认变体、品类要点）不要问。

## 25 套场景路由表

| 触发词 | 模板 |
|---|---|
| 白底图、主图、hero image、packshot、电商主图 | `references/template-01-hero-image.json` |
| 场景图、生活图、lifestyle、使用场景 | `references/template-02-lifestyle-scene.json` |
| 平铺图、flat lay、俯拍、摆拍 | `references/template-03-flat-lay.json` |
| 细节图、微距、macro、特写、材质 | `references/template-04-detail-macro.json` |
| 海报、poster、banner、促销、活动主图 | `references/template-05-poster-banner.json` |
| 社交媒体、小红书、Instagram、TikTok、朋友圈 | `references/template-06-social-media.json` |
| UGC、买家秀、GRWM、真实感、真实用户 | `references/template-07-ugc-style.json` |
| 模特、model、人物展示、上身图 | `references/template-08-model-showcase.json` |
| 对比、before after、前后、效果对比 | `references/template-09-before-after.json` |
| 包装、packaging、礼盒、开箱包装 | `references/template-10-packaging.json` |
| 信息图、A+、详情页、卖点图、infographic | `references/template-11-infographic.json` |
| 创意、概念、creative、视觉冲击 | `references/template-12-creative-concept.json` |
| 尺寸、规格、使用步骤、size chart | `references/template-13-size-spec.json` |
| 套装、组合、bundle、多品 | `references/template-14-multi-product.json` |
| 直播、livestream、直播场景 | `references/template-15-livestream.json` |
| 试穿、融入、try on、场景合成 | `references/template-16-try-on-virtual.json` |
| 拆解图、爆炸图、exploded view、内部结构 | `references/template-17-exploded-view.json` |
| 隐形模特、ghost mannequin、3D 服装、无头模特 | `references/template-18-ghost-mannequin.json` |
| 多角度、网格、grid、多色展示、SKU 图 | `references/template-19-multi-angle-grid.json` |
| 杂志、封面、editorial、magazine、大片 | `references/template-20-magazine-editorial.json` |
| 季节、四季、campaign、春夏秋冬、节日 | `references/template-21-seasonal-campaign.json` |
| 奢华、氛围、烟雾、luxury、atmospheric | `references/template-22-luxury-atmospherics.json` |
| 设备模型、界面、mockup、SaaS、APP | `references/template-23-device-mockup.json` |
| 店铺、门面、空间、storefront、实体店 | `references/template-24-storefront.json` |
| 运动、健身、sports、fitness、户外 | `references/template-25-sports-campaign.json` |
| **无匹配** | 默认 `references/template-01-hero-image.json` |

## 组装五条（顺序不能乱）

1. **取骨架**：`prompt_template` 就是输出结构，不自己另造字段
2. **填变量**：`{product_description}` 等占位符换成真实产品描述，材质写具体（磨砂玻璃、拉丝金属、哑光）
3. **应用变体**：用户指定风格 → 用 `variants.<name>.overrides` 覆盖同名字段；没指定就按品类推荐并说明理由，**一次别叠两个变体**
4. **叠品类要点**：`category_tips.<品类>` 追加为该场景的品类说明，不替换已定好的布光构图
5. **精简**：只留有值的字段，删空值、删模板元数据，输出**一个短 JSON**

> 模型在**简洁聚焦**的 prompt 上表现最好。宁可少写两行，不要堆十几条约束。

细节规则（字段语义、品类键对不上怎么办、常见组装错误）见 `references/assembly-rules.md`。

## 输出格式（固定两块）

```
【出图 Prompt】
{
  "type": "product photography",
  "subject": "磨砂玻璃精华瓶，哑光白盖",
  "background": "clean white background",
  "lighting": "soft diffused studio lighting",
  "composition": "centered, front view",
  "quality": "8K, commercial e-commerce photography",
  "category_note": "emphasize texture and glow"
}

【使用建议】
- 粘到即梦 / Midjourney / 豆包 / Canva 均可直接用
- 有产品白底图就一起上传，产品一致性会明显更好
- 这个场景还能换的变体：luxury（高端）、fresh（清新）、tech（科技）、color（彩色背景）
- （文字类场景才加）AI 生图对文字还原有限，关键文案建议生成后后期叠加
```

prompt 必含三要素：**光照**（方向 + 质感）、**构图**（机位 + 景别）、**背景**。缺一不可。

## 反 AI 感（UGC / 直播 / 社媒 / 杂志大片 强制过清单）

指定机型 → 加可见瑕疵 → 真实环境 → 胶片色调 → 明写 `NOT professional photography`、`NOT AI-generated look`、`NOT retouched`。

**禁用词**：`perfect`、`flawless`、`stunning`、`hyper-realistic`。

完整清单与逐场景写法见 `references/anti-ai-and-compliance.md`。

## 合规红线

- 医疗功效、绝对化承诺（最、第一、彻底、永久）类视觉话术：**提醒风险并改写，不帮忙绕过**
- 前后对比不得暗示不实疗效；食品不得暗示保健功效
- 生成图里的资质徽章、认证标识、检测数据：一律后期合成或删，不让模型"画"出来

## 资源路由

| 需要 | 读取 |
|---|---|
| 组装细则、字段字典、品类键缺失处理 | `references/assembly-rules.md` |
| 反 AI 写法、禁用词、文字场景、合规话术 | `references/anti-ai-and-compliance.md` |
| 画幅平台规格、上架/详情页/社媒套餐组合 | `references/platform-and-ratio.md` |
| 具体场景模板（25 套，按需读其中 1 个） | `references/template-*.json` |

单次只读 1 个模板 + 最多 1 份参考文档。

## 来源与许可

25 套模板与组装方法来自 **buluslan（公众号：新西楼.AI）** 的开源项目 `gpt-image2-ecommerce`（MIT），本技能为其面向团队场景的整理版，保留原许可与署名，见 `LICENSE.md`。模板内容不二次创作布光与构图参数——**不凭印象编参数**。

更多跨境电商 AI 实战：公众号「新西楼.AI」。
