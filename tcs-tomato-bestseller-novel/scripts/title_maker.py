#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
title_maker.py — 书名 / 简介 / 标签包装器（纯标准库）

用途：番茄是"书名 + 简介 + 封面"三件套决定点击率的战场。
      本工具按 2026-09 实测榜单命名规律，批量生成书名候选并**打分**，
      同时生成简介模板与标签建议。

命名规律来源：2026-09 首秀 TOP20 实测榜单（男/女频）
  · 冒号结构占比极高：《崩铁：XX》《名义：XX》《鬼灭：XX》
  · 反差/反转词：战损、社恐、炮灰、万人迷、病娇、疯批、禁欲、阴湿
  · 疑问/惊叹式：《火影：什么？这不是玩家的天下吗》《惊！太子爷和我儿子灵魂互换了》
  · 身份前置：《我包工头，忽悠哥莫拉打灰》《变身萌妹，刚穿越就嫁人》

用法：
  python title_maker.py --genre 都市脑洞 --keyword 系统 --count 12
  python title_maker.py --genre 女频·双男主 --keyword 阴湿 --count 10 --with-intro
  python title_maker.py --score "书名"           # 给已有书名打分
  python title_maker.py --score-file titles.txt  # 批量打分
"""

import argparse
import random
import re
import sys

# ============ 命名模板 ============
TEMPLATES = {
    "通用": [
        "{K}：{A}", "{K}{A}", "我的{K}有点{A}", "这个{K}太{A}了",
        "{A}的{K}", "开局{K}，{A}", "重生后，我的{K}{A}", "全城都说我{K}，直到我{A}",
    ],
    "都市脑洞": [
        "全城{K}：只有我{A}", "{K}降临：我{A}", "开局{K}，我{A}了全世界",
        "所有人都在{K}，只有我{A}", "{K}？那我只好{A}了", "我{K}的那些年",
        "震惊！我{K}之后{A}了", "从{K}开始{A}",
    ],
    "动漫衍生": [
        "{IP}：{A}", "{IP}之{K}{A}", "穿成{IP}里的{K}，我{A}",
        "{IP}：什么？{A}", "{IP}：从{K}开始{A}", "{IP}：我{A}了所有人",
        "{IP}：成为{K}，{A}", "{IP}模拟：{A}",
    ],
    "玄幻": [
        "{K}：{A}", "我的{K}能{A}", "开局{K}，{A}诸天", "{A}：从{K}开始",
        "我以{K}证{A}", "全宗门以为我{K}，其实我{A}", "{K}归来，{A}",
    ],
    "女频·双男主": [
        "{A}：{K}他{A2}", "穿成{K}后，{A}他{A2}", "{K}{A}，{A2}他急了",
        "死对头{K}，{A}他却{A2}", "{A}：{K}他假{A2}真{A3}", "{K}：炮灰但{A}",
        "我的{K}有点{A}", "被{K}捡走后，我{A}了",
    ],
    "女频·快穿": [
        "快穿：{K}{A}", "快穿之{K}{A}", "快穿：只{K}不{A}", "{K}：{A}全场",
        "快穿：我{A}了所有{K}", "{K}合集：{A}",
    ],
    "专业流": [
        "{职业}：开局{K}{A}", "{职业}：我{A}了所有人", "我是{职业}，我{A}",
        "{职业}：从{K}开始{A}", "让你{K}，{A}什么鬼",
    ],
    "科幻末世": [
        "末世：{K}{A}", "全球{K}：我{A}", "{K}降临，我{A}", "末世{K}：从{A}开始",
        "转生{K}，我以{A}",
    ],
}

# 高频吸量词库（2026-09 实测）
POWER_WORDS = {
    "反转反差": ["战损", "社恐", "炮灰", "万人迷", "病娇", "疯批", "禁欲", "阴湿", "假高冷", "真大佬",
                 "反派", "恶毒", "团宠", "幼崽", "马甲", "掉马", "躺平", "摆烂", "摆烂式", "强制爱"],
    "情绪": ["后悔", "破防", "哭", "急了", "上头", "心动", "宠", "甜", "虐", "疯", "慌", "跪", "求", "宠疯"],
    "强度": ["无敌", "断层", "横推", "镇压", "碾压", "吊打", "逆袭", "翻盘", "崛起", "登顶", "封神", "炸裂"],
    "悬念": ["什么", "竟然", "居然", "原来", "真相", "秘密", "身份", "失踪", "复活", "重生", "穿越", "穿书"],
    "口语": ["啊", "吧", "吗", "啥", "鬼", "离谱", "绝了", "麻了", "好家伙"],
}

# 2026 实测高频词（加分项）
HOT_2026 = ["战损", "社恐", "炮灰", "万人迷", "病娇", "疯批", "禁欲", "阴湿", "假高冷",
            "模拟", "盘点", "天幕", "观影", "崩铁", "原神", "名义", "斩神", "鬼灭",
            "幼崽", "团宠", "马甲", "功德", "功德金光", "躺平", "摆烂", "强制爱", "双男主"]

INTRO_TEMPLATE = """【简介模板 · {genre}】

{hook}

{setup}

{promise}

——
{tags}
"""


def gen_titles(genre, keyword, count, ip=None):
    tpls = TEMPLATES.get(genre, TEMPLATES["通用"])
    all_words = [w for lst in POWER_WORDS.values() for w in lst]
    out = []
    seen = set()
    tries = 0
    while len(out) < count and tries < count * 30:
        tries += 1
        t = random.choice(tpls)
        a = random.choice(all_words)
        a2 = random.choice(POWER_WORDS["情绪"])
        a3 = random.choice(POWER_WORDS["反转反差"])
        s = t.format(K=keyword, A=a, A2=a2, A3=a3, IP=ip or keyword, 职业=keyword)
        if s in seen:
            continue
        seen.add(s)
        out.append(s)
    return out


def score_title(title, genre=None):
    """给书名打分（0-100）"""
    score = 50.0
    notes = []
    n = len(title)

    # 长度
    if 6 <= n <= 14:
        score += 12
        notes.append(f"长度 {n} 字在黄金区间（6-14）")
    elif 4 <= n < 6 or 14 < n <= 18:
        score += 5
        notes.append(f"长度 {n} 字可接受")
    else:
        score -= 10
        notes.append(f"长度 {n} 字不理想（建议 6-14 字）")

    # 冒号结构（2026 实测高频）
    if "：" in title or ":" in title:
        score += 10
        notes.append("含冒号结构（榜单高频）")

    # 2026 热词命中
    hits = [w for w in HOT_2026 if w in title]
    if hits:
        score += min(15, len(hits) * 6)
        notes.append(f"命中 2026 热词：{'/'.join(hits[:4])}")

    # 情绪/强度词
    emo = [w for w in POWER_WORDS["情绪"] + POWER_WORDS["强度"] if w in title]
    if emo:
        score += min(10, len(emo) * 4)
        notes.append(f"含情绪/强度词：{'/'.join(emo[:3])}")

    # 悬念词
    sus = [w for w in POWER_WORDS["悬念"] if w in title]
    if sus:
        score += min(8, len(sus) * 4)
        notes.append(f"含悬念词：{'/'.join(sus[:3])}")

    # 疑问/惊叹
    if re.search(r"[？?！!]|什么|竟然|居然", title):
        score += 6
        notes.append("含疑问/惊叹（提升点击）")

    # 扣分项
    if re.search(r"^(我的|这个|那个)", title) and n < 8:
        score -= 5
        notes.append("开头过于平淡")
    if len(set(title)) < n * 0.6:
        score -= 5
        notes.append("重复字过多")

    return max(0, min(100, score)), notes


def make_intro(genre, keyword):
    hooks = [
        f"穿越成{keyword}的第一天，所有人都以为他完了。",
        f"他{keyword}了三年，没人知道他到底在等什么。",
        f"全城都在笑他{keyword}，直到那天，有人跪着来求他。",
        f"系统说：你的{keyword}，是这个世界唯一的bug。",
        f"她重活一世，只为一件事——不再做那个{keyword}的人。",
    ]
    setups = [
        "没人知道，他脑子里装着另一个世界的所有知识。",
        "直到某天，那扇门后的人，叫出了他的真名。",
        "而她不知道的是，那个被她救下的人，正在改变一切。",
        "所有人都以为这是巧合。只有他知道，这是必然。",
    ]
    promises = [
        "从今天起，这个世界的规则，由他来写。",
        "这一世，她要把欠她的，连本带利讨回来。",
        "当真相揭开的那一刻，所有人都将跪下。",
        "而这一切，才刚刚开始。",
    ]
    tags = f"#{keyword} #{'爽文' if '女频' not in (genre or '') else '言情'} #{'系统' if '系统' in keyword else '逆袭'} #不虐主 #更新稳定"
    return INTRO_TEMPLATE.format(
        genre=genre or "通用",
        hook=random.choice(hooks),
        setup=random.choice(setups),
        promise=random.choice(promises),
        tags=tags,
    )


def main():
    ap = argparse.ArgumentParser(description="书名/简介/标签包装器")
    ap.add_argument("--genre", default="通用", help="赛道")
    ap.add_argument("--keyword", help="核心关键词/金手指/IP名/职业")
    ap.add_argument("--ip", help="衍生 IP 名（动漫衍生赛道）")
    ap.add_argument("--count", "-c", type=int, default=10, help="生成数量")
    ap.add_argument("--with-intro", action="store_true", help="同时生成简介")
    ap.add_argument("--score", help="给单个书名打分")
    ap.add_argument("--score-file", help="批量打分（每行一个书名）")
    ap.add_argument("--seed", type=int)
    args = ap.parse_args()

    if args.seed is not None:
        random.seed(args.seed)
    else:
        random.seed()

    if args.score:
        s, notes = score_title(args.score, args.genre)
        print("=" * 66)
        print(f"《{args.score}》 评分：{s:.0f} / 100")
        print("=" * 66)
        for n in notes:
            print(f"  · {n}")
        if s >= 80:
            print("\n  ✅ 优质书名，可直接使用")
        elif s >= 65:
            print("\n  🟠 可用，建议按上述维度微调")
        else:
            print("\n  🔴 吸量力不足，建议重新构思")
        return 0

    if args.score_file:
        lines = [l.strip() for l in open(args.score_file, "r", encoding="utf-8", errors="ignore") if l.strip()]
        res = []
        for l in lines:
            s, _ = score_title(l, args.genre)
            res.append((l, s))
        res.sort(key=lambda x: -x[1])
        print(f"{'书名':<34}{'评分':>8}")
        print("-" * 66)
        for t, s in res:
            bar = "█" * int(s / 5)
            print(f"{t[:32]:<34}{s:>6.0f}  {bar}")
        return 0

    if not args.keyword:
        ap.error("生成模式需要 --keyword")

    titles = gen_titles(args.genre, args.keyword, args.count, args.ip)
    scored = [(t,) + score_title(t, args.genre) for t in titles]
    scored.sort(key=lambda x: -x[1])

    print("=" * 70)
    print(f"书名候选（赛道：{args.genre} ｜ 关键词：{args.keyword}）")
    print("=" * 70)
    for i, (t, s, notes) in enumerate(scored, 1):
        mark = "✅" if s >= 80 else ("🟠" if s >= 65 else "🔴")
        print(f"{i:>3}. {mark} {s:>3.0f}  《{t}》")
    print("=" * 70)
    print(f"最优：《{scored[0][0]}》（{scored[0][1]:.0f} 分）")
    print("\n提示：书名决定点击率，建议生成 20+ 候选后挑最优，并对照首秀榜验证。")

    if args.with_intro:
        print("\n" + "=" * 70)
        print(make_intro(args.genre, args.keyword))
        print("=" * 70)
        print("简介三要素：① 前 2 行必须出钩子 ② 中段交代金手指/核心设定 ③ 末段给出'爽的承诺'")
    return 0


if __name__ == "__main__":
    sys.exit(main())
