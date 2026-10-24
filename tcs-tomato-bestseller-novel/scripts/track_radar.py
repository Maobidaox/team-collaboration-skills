#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
track_radar.py — 番茄爆款小说专家 · 2026-09 赛道实时雷达（纯标准库）

内置 2026-09 番茄赛道热度矩阵（男频/女频/短篇），提供：
  - --list        列出全部赛道与四维评分
  - --track X     查看单赛道深度画像（热度/竞争/改编/新人友好 + 打法）
  - --recommend   按作者条件推荐赛道（新人/日更能力/偏好）
  - --hot         只看当前高热赛道
  - --blue        只看蓝海赛道（竞争小）

四维评分（0-10，2026-09 口径）：
  heat 热度（流量天花板） / comp 竞争度（越高越卷） / ip IP改编潜力 / newbie 新人友好度
"""

import argparse
import json
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(HERE)

# ============ 2026-09 赛道热度矩阵 ============
TRACKS = {
    # ---------- 男频 ----------
    "都市高武":       dict(side="男频", heat=10, comp=10, ip=9,  newbie=5,
                       hot=["我不是戏神", "我在精神病院学斩神", "时停起手，邪神也得给我跪下！"],
                       core="现实都市 + 超自然设定 + 反套路金手指 + 强冲突节奏",
                       entry="冷门职业 + 异能（遗物整理师/法医/外卖员）",
                       risk="内卷最重，开篇不达标即首秀扑街"),
    "都市脑洞":       dict(side="男频", heat=10, comp=9,  ip=9,  newbie=8,
                       hot=["摸鱼就能变强", "遗物整理师的阴阳眼"],
                       core="现代背景 + 反套路金手指，每 3 章 1 小爽点、10 章 1 大高潮",
                       entry="反套路金手指（AI 反内卷/摸鱼变强）+ 冷门职业",
                       risk="同质化严重，需强差异化设定"),
    "悬疑脑洞":       dict(side="男频", heat=10, comp=9,  ip=10, newbie=6,
                       hot=["十日终焉（196.9万在读）", "诡舍", "规则怪谈：无所谓，系统会出手"],
                       core="无限流副本 / 规则怪谈，智斗破局 + 强钩子",
                       entry="规则怪谈 + 科学/常识破局",
                       risk="智斗门槛高，逻辑不严即被骂降智"),
    "悬疑灵异":       dict(side="男频", heat=9,  comp=7,  ip=10, newbie=7,
                       hot=["北派盗墓笔记（150万+）", "我以狐仙镇百鬼"],
                       core="民俗风水 + 灵异单元剧",
                       entry="民俗考据 + 都市/乡土背景",
                       risk="涉迷信边界，须写智斗破局"),
    "玄幻脑洞":       dict(side="男频", heat=9,  comp=8,  ip=8,  newbie=6,
                       hot=["开局长生万古，苟到天荒地老", "这个游戏不对劲，我挖矿成神！"],
                       core="传统玄幻骨架 + 反套路设定",
                       entry="苟道流 / 长生流 / 幕后流",
                       risk="读者对传统升级流疲劳，需新意"),
    "传统玄幻":       dict(side="男频", heat=8,  comp=9,  ip=8,  newbie=4,
                       hot=["天渊", "惊鸿", "神通者（216.9万）"],
                       core="力量升级 + 世界观宏大",
                       entry="（基本盘大，但新人极难突围）",
                       risk="长篇门槛高，前 20 万字很难出成绩"),
    "历史古代":       dict(side="男频", heat=8,  comp=7,  ip=9,  newbie=6,
                       hot=["冒姓琅琊（173.3万）", "我祖父是朱元璋"],
                       core="身份局 + 权谋 + 时代红利",
                       entry="穿越 + 身份反差 + 权谋",
                       risk="考据要求高，写错易被喷"),
    "西幻领主":       dict(side="男频", heat=6,  comp=4,  ip=8,  newbie=9,
                       hot=["（蓝海）某西幻领主爆款"],
                       core="领地养成 + 家族成长 + 经营感",
                       entry="领主 + CEO + 大家长；结合东方元素（中式基建/中医）",
                       risk="蓝海但受众窄，天花板低于都市高武"),
    "末世囤货":       dict(side="男频", heat=7,  comp=6,  ip=8,  newbie=8,
                       hot=["（常青）末世囤货流"],
                       core="重生末世前 + 空间囤货 + 生存基建",
                       entry="囤货日常 + 防坏人 + 打脸白眼狼",
                       risk="套路成熟，需新设定破圈"),
    "规则怪谈":       dict(side="男频", heat=9,  comp=9,  ip=10, newbie=7,
                       hot=["规则怪谈：无所谓，系统会出手", "我每天能固化一个物理定律"],
                       core="规则条文 + 违规后果 + 常识破局",
                       entry="规则反常识 + 破局合理化",
                       risk="已大量涌入，需强差异化"),

    # ---------- 女频 ----------
    "重生年代":       dict(side="女频", heat=10, comp=7,  ip=8,  newbie=9,
                       hot=["重生八零：从小山村走出个大富翁（200万）", "恶妻好运连连"],
                       core="重生 70/80 年代 + 空间 + 随军 + 极品打脸 + 囤货致富 + 萌娃",
                       entry="囤货军婚 / 赶山赶海 / 八零当后妈",
                       risk="同质化，靠细节差异化"),
    "恶毒女配":       dict(side="女频", heat=10, comp=8,  ip=9,  newbie=8,
                       hot=["穿成恶毒女配后我洗白了（150万）", "全家反派我苟成团宠"],
                       core="穿书 + 洗白/逆袭 + 掀桌反转",
                       entry="不按原剧情走 + 智商/实力逆袭 + 手撕渣男",
                       risk="反转要新，老梗易疲"),
    "豪门马甲":       dict(side="女频", heat=9,  comp=8,  ip=10, newbie=8,
                       hot=["闪婚禁欲上司，人前不熟人后猛亲", "事可忍叔不可忍"],
                       core="极致偏爱 + 反差感 + 闪婚/离婚带崽/真假千金",
                       entry="先婚后爱 + 女主隐藏身份 + 马甲掉不停",
                       risk="甜宠套路成熟，需人设新"),
    "现言脑洞":       dict(side="女频", heat=9,  comp=8,  ip=9,  newbie=7,
                       hot=["我不过作作妖，怎么就成了白月光", "魔法学校小学妹"],
                       core="反套路甜宠 + 沙雕轻松",
                       entry="作精/白月光反差 + 轻松幽默",
                       risk="脑洞需持续输出"),
    "古风世情":       dict(side="女频", heat=8,  comp=7,  ip=9,  newbie=6,
                       hot=["穿乱世，疯癫公主她靠抢劫建国了"],
                       core="大女主 + 权谋 + 搞事业",
                       entry="疯批人设 + 无 CP / 强势女主",
                       risk="宫斗宅斗要求考据与逻辑"),
    "玄幻言情":       dict(side="女频", heat=8,  comp=7,  ip=8,  newbie=7,
                       hot=["我法师加奶妈，用七把剑不过分吧", "满门反派疯批，唯有师妹逗比"],
                       core="反差搭配 + 群像 + 轻喜剧",
                       entry="反差人设组合 + 沙雕互动",
                       risk="需强人设张力"),
    "青春甜宠":       dict(side="女频", heat=8,  comp=7,  ip=8,  newbie=9,
                       hot=["溯雨信笺", "认路人甲当爹后我喜提反派全家桶"],
                       core="情绪细腻 + 甜宠 + 反差亲情",
                       entry="轻甜 + 反差设定",
                       risk="情绪不够细腻会显平"),

    # ---------- 短篇 ----------
    "民俗短篇":       dict(side="短篇", heat=7,  comp=4,  ip=10, newbie=10,
                       hot=["（短篇风口）民俗单元剧"],
                       core="乡村民俗 + 灵异事件 + 短平快",
                       entry="3-5 万字单本，单元闭环",
                       risk="短篇单价低于长篇，适合试水"),
    "职业反差脑洞":   dict(side="短篇", heat=7,  comp=5,  ip=9,  newbie=10,
                       hot=["（短篇风口）职业 + 诡异"],
                       core="冷门职业 + 诡异事件，完读率高",
                       entry="收破烂/送外卖/法医 + 诡异",
                       risk="题材需新鲜"),
    "乡土矛盾短篇":   dict(side="短篇", heat=6,  comp=4,  ip=8,  newbie=10,
                       hot=["（蓝海）乡村乡土短篇"],
                       core="邻里矛盾 + 建房占地 + 返乡创业",
                       entry="开篇冲突拉满 + 适配短视频改编",
                       risk="受众偏下沉，天花板有限"),
}


def _bar(n):
    return "█" * n + "░" * (10 - n)


def cmd_list(args):
    print("=" * 96)
    print("番茄小说 2026-09 赛道雷达（四维评分，0-10）")
    print("=" * 96)
    print("%-14s %-6s %-14s %-14s %-8s %-8s" % ("赛道", "侧", "热度", "竞争度", "IP力", "新人友好"))
    print("-" * 96)
    for side in ("男频", "女频", "短篇"):
        for name, t in TRACKS.items():
            if t["side"] != side:
                continue
            print("%-14s %-6s %-14s %-14s %-8s %-8s"
                  % (name, t["side"], _bar(t["heat"]), _bar(t["comp"]), t["ip"], t["newbie"]))
        print("-" * 96)
    print("\n热度 = 流量天花板；竞争度 = 越高越卷；IP力 = 改编变现潜力；新人友好 = 越大越适合新人")
    return 0


def cmd_track(args):
    t = TRACKS.get(args.track)
    if not t:
        print("[ERR] 未找到赛道：%s" % args.track)
        print("可用赛道：%s" % "、".join(TRACKS.keys()))
        return 1
    print("=" * 70)
    print("赛道深度画像 · %s（%s）" % (args.track, t["side"]))
    print("=" * 70)
    print("热度      : %s %d/10" % (_bar(t["heat"]), t["heat"]))
    print("竞争度    : %s %d/10" % (_bar(t["comp"]), t["comp"]))
    print("IP 改编力 : %s %d/10" % (_bar(t["ip"]), t["ip"]))
    print("新人友好  : %s %d/10" % (_bar(t["newbie"]), t["newbie"]))
    print("-" * 70)
    print("核心公式  : %s" % t["core"])
    print("切入点    : %s" % t["entry"])
    print("主要风险  : %s" % t["risk"])
    print("在榜样本  : %s" % " / ".join(t["hot"]))
    print("-" * 70)
    print("建议动作  :")
    if t["comp"] >= 9:
        print("  · 本赛道高度内卷 → 必须在前 3 章做出差异化，否则首秀即扑")
        print("  · 用 chapter_forge.py 反复打磨黄金三章")
    if t["newbie"] >= 8:
        print("  · 新人友好 → 适合作为第一本书")
    if t["ip"] >= 9:
        print("  · IP 改编潜力高 → 写作时刻意埋\"可视场景 + 单元结构\"（见 36/37 号）")
    print("  · 详细公式见 references/07、08、46、47 号")
    return 0


def cmd_hot(args):
    items = sorted([(n, t) for n, t in TRACKS.items() if t["heat"] >= 9],
                   key=lambda x: (-x[1]["heat"], x[1]["comp"]))
    print("当前高热赛道（热度 ≥9）：")
    print("-" * 70)
    for n, t in items:
        print("  %-14s 热度 %d  竞争 %d  %s" % (n, t["heat"], t["comp"], t["side"]))
    print("-" * 70)
    print("共 %d 个。高热 = 流量大，但也最卷。" % len(items))
    return 0


def cmd_blue(args):
    items = sorted([(n, t) for n, t in TRACKS.items() if t["comp"] <= 5],
                   key=lambda x: (x[1]["comp"], -x[1]["ip"]))
    print("蓝海赛道（竞争度 ≤5）：")
    print("-" * 70)
    for n, t in items:
        print("  %-14s 竞争 %d  热度 %d  IP %d  %s" % (n, t["comp"], t["heat"], t["ip"], t["side"]))
    print("-" * 70)
    print("共 %d 个。蓝海 = 竞争小，但天花板可能低，适合新人练手或差异化突围。" % len(items))
    return 0


def cmd_recommend(args):
    print("=" * 70)
    print("赛道推荐（按作者条件）")
    print("=" * 70)
    n = args.newbie
    daily = args.daily or "normal"
    side = args.side or "any"
    pool = [(k, v) for k, v in TRACKS.items() if side == "any" or v["side"] == side]

    def score(item):
        k, v = item
        s = v["heat"] * 1.0 + v["ip"] * 0.8 + v["newbie"] * 1.2 - v["comp"] * 0.9
        if n:                      # 新人：加大新人友好权重
            s += v["newbie"] * 0.8
        if daily == "low":         # 日更能力弱：偏好短篇/蓝海
            if v["side"] == "短篇":
                s += 3.0
            s += (10 - v["comp"]) * 0.3
        if daily == "high":        # 日更能力强：偏好长篇高热度
            if v["side"] != "短篇":
                s += 2.0
            s += v["heat"] * 0.3
        return s

    ranked = sorted(pool, key=score, reverse=True)[:5]
    print("条件：新人=%s  日更能力=%s  方向=%s" % ("是" if n else "否", daily, side))
    print("-" * 70)
    for i, (k, v) in enumerate(ranked, 1):
        print("%d. %-14s（%s）  热度 %d / 竞争 %d / 新人友好 %d" % (i, k, v["side"], v["heat"], v["comp"], v["newbie"]))
        print("   切入点：%s" % v["entry"])
        print("   风险：%s" % v["risk"])
    print("-" * 70)
    print("下一步：python topic_score.py --track <赛道>  做十维选题打分（≥80 才开书）")
    return 0


def main():
    p = argparse.ArgumentParser(description="番茄爆款小说专家 · 2026-09 赛道雷达")
    p.add_argument("--list", action="store_true", help="列出全部赛道")
    p.add_argument("--track", help="查看单赛道画像")
    p.add_argument("--hot", action="store_true", help="只看高热赛道")
    p.add_argument("--blue", action="store_true", help="只看蓝海赛道")
    p.add_argument("--recommend", action="store_true", help="按条件推荐赛道")
    p.add_argument("--newbie", action="store_true", help="是新人作者")
    p.add_argument("--daily", choices=["low", "normal", "high"], help="日更能力")
    p.add_argument("--side", choices=["男频", "女频", "短篇", "any"], help="方向")
    args = p.parse_args()

    if args.track:
        return cmd_track(args)
    if args.hot:
        return cmd_hot(args)
    if args.blue:
        return cmd_blue(args)
    if args.recommend:
        return cmd_recommend(args)
    return cmd_list(args)


if __name__ == "__main__":
    sys.exit(main())
