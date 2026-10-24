#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
reader_persona.py — 番茄爆款小说专家 · 读者画像与受众匹配器（纯标准库）

输入赛道 + 主角设定 + 风格，输出：目标读者群、阅读场景、写法建议、风险提示。

用法：
  python reader_persona.py --list
  python reader_persona.py --track 都市脑洞
  python reader_persona.py --track 都市高武 --protagonist "外卖员" --style 爽文

依据：references/34 号（读者画像分群与流量时段策略），口径 2026-09。
"""

import argparse
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

# ============ 四大读者群 ============
PERSONAS = {
    "下沉男性": dict(age="25-45", scene="听书为主（开车/干活背景音）",
                 like="爽点密集、身份反差、打脸", dislike="慢热、文艺、心理描写",
                 key="对话多、单句短、每章一爽点、开头交代谁在哪干什么"),
    "下沉女性": dict(age="25-45", scene="碎片时间、睡前",
                 like="情感张力、逆袭、萌宝/空间", dislike="逻辑过于复杂、多线叙事",
                 key="撕极品要有爽感、日常要有小高潮、情绪要细腻"),
    "年轻女性": dict(age="18-28", scene="通勤 + 睡前",
                 like="无 CP 大女主、发疯文学、甜宠", dislike="憋屈、虐主、爹味",
                 key="拒绝内耗、直接掀桌、极致偏爱、人设要清醒"),
    "高粘性男性": dict(age="20-35", scene="深度阅读",
                 like="都市高武、悬疑脑洞、智斗", dislike="降智、无脑爽",
                 key="逻辑严密、智斗要真、设定要自洽、伏笔要回收"),
}

# ============ 赛道 → 画像映射 ============
TRACK_MAP = {
    "都市高武": ("下沉男性", "高粘性男性", "听书 + 深度阅读", "金手指要反套路；每 3 章 1 小爽点，10 章 1 大高潮"),
    "都市脑洞": ("下沉男性", "高粘性男性", "听书为主", "日常打脸 + 奇葩金手指；第 1 章就暴露金手指"),
    "悬疑脑洞": ("高粘性男性", "下沉男性", "深度阅读", "智斗破局靠逻辑；每章末一个悬念钩子"),
    "悬疑灵异": ("下沉男性", "高粘性男性", "听书 + 深度阅读", "民俗考据要真；氛围靠细节不靠血腥"),
    "玄幻脑洞": ("下沉男性", "高粘性男性", "听书为主", "反套路设定；避免苦修升级流"),
    "传统玄幻": ("下沉男性", "高粘性男性", "听书 + 深度阅读", "力量体系自洽；前 20 万字要早进高潮"),
    "历史古代": ("高粘性男性", "下沉男性", "深度阅读", "考据要严谨；身份局要新鲜"),
    "西幻领主": ("高粘性男性", "下沉男性", "深度阅读", "经营养成感要强；可结合东方元素差异化"),
    "末世囤货": ("下沉男性", "下沉女性", "听书为主", "囤货日常要有爽感；防坏人要有对抗"),
    "规则怪谈": ("高粘性男性", "年轻女性", "深度阅读", "规则要反常识且自洽；破局要合理"),
    "重生年代": ("下沉女性", "年轻女性", "碎片 + 睡前", "撕极品要爽；囤货致富要有细节；萌娃加分"),
    "恶毒女配": ("年轻女性", "下沉女性", "通勤", "掀桌要果断；反转要新；智商在线"),
    "豪门马甲": ("年轻女性", "下沉女性", "睡前", "极致偏爱 + 马甲掉落；拒绝恋爱脑"),
    "现言脑洞": ("年轻女性", "下沉女性", "通勤 + 睡前", "轻松幽默；反差人设要立住"),
    "古风世情": ("年轻女性", "下沉女性", "深度阅读", "大女主搞事业；权谋逻辑要严密"),
    "玄幻言情": ("年轻女性", "下沉女性", "通勤", "反差搭配 + 沙雕互动；人设张力要强"),
    "青春甜宠": ("年轻女性", "下沉女性", "睡前", "情绪要细腻；反差设定要新"),
    "民俗短篇": ("下沉男性", "下沉女性", "碎片", "短平快；单元闭环；第一句就要有异常"),
    "职业反差脑洞": ("下沉男性", "年轻女性", "碎片", "冷门职业 + 诡异；完读率优先"),
    "乡土矛盾短篇": ("下沉女性", "下沉男性", "碎片", "开篇冲突拉满；适配短视频改编"),
}

STYLE_TIPS = {
    "爽文": ["爽点密度拉满：开篇期每章 2-3 个", "憋屈不超过 2 章", "打脸要有旁观者反应"],
    "甜宠": ["极致偏爱：男主无条件站女主", "马甲掉落要分次、要有震惊反应", "拒绝无谓误会拖戏"],
    "悬疑": ["每章末一个悬念", "线索要公平（读者有机会猜到）", "破局靠逻辑不靠巧合"],
    "轻松": ["对话要有梗", "反差人设要立住", "危机要可控（不压抑）"],
    "热血": ["目标要明确", "每 10 章一次实力飞跃", "团队/伙伴要有情义线"],
    "种田": ["日常要有小高潮", "经营要看得见成长", "邻里矛盾要有对抗"],
}


def cmd_list(args):
    print("=" * 78)
    print("读者画像库（口径 2026-09）")
    print("=" * 78)
    for k, v in PERSONAS.items():
        print("【%s】%s 岁 ｜ 场景：%s" % (k, v["age"], v["scene"]))
        print("   偏好：%s" % v["like"])
        print("   不适：%s" % v["dislike"])
        print("   写法要点：%s" % v["key"])
        print()
    print("支持赛道：%s" % "、".join(TRACK_MAP.keys()))
    return 0


def cmd_track(args):
    t = args.track
    if t not in TRACK_MAP:
        print("[ERR] 未找到赛道：%s" % t)
        print("可用赛道：%s" % "、".join(TRACK_MAP.keys()))
        return 1
    main_p, sec_p, scene, tip = TRACK_MAP[t]
    print("=" * 78)
    print("读者画像匹配 · %s" % t)
    print("=" * 78)
    print("主读者群   : %s（%s）" % (main_p, PERSONAS[main_p]["age"]))
    print("次读者群   : %s（%s）" % (sec_p, PERSONAS[sec_p]["age"]))
    print("阅读场景   : %s" % scene)
    print("-" * 78)
    print("【主读者群画像】")
    print("  偏好：%s" % PERSONAS[main_p]["like"])
    print("  不适：%s" % PERSONAS[main_p]["dislike"])
    print("  写法要点：%s" % PERSONAS[main_p]["key"])
    print("-" * 78)
    print("【本赛道写法建议】")
    print("  %s" % tip)
    if args.protagonist:
        print("-" * 78)
        print("【主角设定匹配】%s" % args.protagonist)
        print("  · 处境代入：主角起点要低、困境要具体（有代入感才有人追）")
        print("  · 与该读者群的心理连接：%s" % ("给平凡人一个翻身的机会" if main_p == "下沉男性"
              else ("给受气的人一个出口" if main_p == "下沉女性"
                    else ("给内耗的人一个掀桌的爽感" if main_p == "年轻女性"
                          else "给聪明人一个解谜的快感"))))
    if args.style and args.style in STYLE_TIPS:
        print("-" * 78)
        print("【%s 风格要点】" % args.style)
        for s in STYLE_TIPS[args.style]:
            print("  · %s" % s)
    print("-" * 78)
    print("流量时段建议：")
    print("  ✅ 06:30-08:30 / 12:00-13:30 / 18:00-20:00")
    print("  ❌ 避免 22:00-24:00（审核高峰，防数据腰斩）")
    print()
    print("详见 references/34 号（读者画像分群与流量时段策略）")
    return 0


def main():
    p = argparse.ArgumentParser(description="番茄爆款小说专家 · 读者画像与受众匹配器")
    p.add_argument("--list", action="store_true", help="列出全部画像")
    p.add_argument("--track", help="赛道名")
    p.add_argument("--protagonist", help="主角设定（如：外卖员）")
    p.add_argument("--style", choices=list(STYLE_TIPS.keys()), help="风格")
    args = p.parse_args()
    if args.track:
        return cmd_track(args)
    return cmd_list(args)


if __name__ == "__main__":
    sys.exit(main())
