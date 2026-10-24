#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
番茄爆款小说专家 · 选题十维评分与赛道匹配
------------------------------------------
纯标准库实现，零第三方依赖，跨平台。

用途：对候选选题做十维打分（≥90 优质 / 80-89 可做 / 70-79 需改造 / <70 换题），
      并给出赛道匹配建议与风险提示。

用法：
  python topic_score.py                       # 交互式逐项打分（1-10）
  python topic_score.py --scores 9,8,7,9,8,9,8,7,6,10
  python topic_score.py --track 男频           # 查看赛道清单与 2026 趋势
"""

import argparse
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

DIMENSIONS = [
    ("赛道量级", 10, "该赛道在读盘子是否足够大（头部赛道更容易出量）"),
    ("趋势契合", 10, "是否符合 2026 风向（男频：都市高武/克苏鲁/无限流+规则怪谈/硬核权谋/苟道流/都市脑洞融合现实）"),
    ("金手指稀缺性", 15, "与同赛道常见金手指标签化区分度是否足够"),
    ("金手指可成长性", 10, "能否支撑 100 万字的升级链而不崩"),
    ("金手指可量化性", 10, "是否可数值化/等级化（直接决定爽点节奏是否好排）"),
    ("开篇爆发力", 15, "前 200 字能否立刻出冲突（决定完读率生死）"),
    ("钩子可持续", 10, "每章能否稳定产出钩子（决定追更率）"),
    ("续航能力", 10, "能否撑到 100 万字仍有新东西"),
    ("改编潜力", 5, "是否适合短剧/漫改（影响巅峰榜第六维 IP 潜力）"),
    ("合规安全", 5, "是否触碰内容红线（一票否决项）"),
]

MALE_TRACKS = ["都市高武", "都市日常", "都市脑洞", "玄幻脑洞", "传统玄幻", "东方仙侠",
               "悬疑脑洞", "悬疑灵异", "历史古代", "历史脑洞", "科幻末世",
               "游戏体育", "都市种田", "西方奇幻"]
FEMALE_TRACKS = ["豪门总裁", "宫斗宅斗", "青春甜宠", "现言脑洞", "玄幻言情",
                 "星光璀璨", "年代", "职场婚恋", "古风世情"]

MALE_TRENDS = ["都市高武断层领先", "克苏鲁元素渗透", "无限流+规则怪谈崛起",
               "历史权谋走硬核路线", "苟道流持续流行", "都市脑洞融合现实"]
FEMALE_TRENDS = ["豪门总裁人气第一", "疯批反派×娇软女主", "玄幻言情萌宝流",
                 "现实向甜宠崛起", "穿书/反套路成标配"]


def ask_scores():
    print("=" * 60)
    print("选题十维评分（每项 1-10 分）")
    print("=" * 60)
    scores = []
    for name, weight, desc in DIMENSIONS:
        print("\n【%s】（权重 %d）" % (name, weight))
        print("  %s" % desc)
        while True:
            raw = input("  评分 (1-10，回车默认 7)：").strip()
            if not raw:
                scores.append(7)
                break
            try:
                v = int(raw)
                if 1 <= v <= 10:
                    scores.append(v)
                    break
            except ValueError:
                pass
            print("  请输入 1-10 的整数")
    return scores


def evaluate(scores):
    print("\n" + "=" * 60)
    print("评分结果（口径：2026-09）")
    print("=" * 60)
    print("| %-14s | %-4s | %-4s | %-6s |" % ("维度", "得分", "权重", "加权"))
    print("|---|---|---|---|")
    total = 0
    for (name, weight, _), s in zip(DIMENSIONS, scores):
        got = s / 10.0 * weight
        total += got
        print("| %-14s | %-4d | %-4d | %-6.1f |" % (name, s, weight, got))
    print("-" * 60)
    print("加权总分：%.1f / 100" % total)
    print("-" * 60)

    if total >= 90:
        verdict = "✅ 优质选题，可直接开工"
    elif total >= 80:
        verdict = "🟡 可做，建议先补强短板维度再动笔"
    elif total >= 70:
        verdict = "🟠 需改造：找出得分最低的 2 个维度重点改造"
    else:
        verdict = "🔴 建议换题：基础盘不成立"

    print("判定：%s" % verdict)

    # 短板定位
    ranked = sorted(zip(DIMENSIONS, scores), key=lambda x: (x[1] / 10.0 * x[0][1]) / x[0][1])
    print("\n最薄弱的三项（优先改造）：")
    for (name, weight, _), s in ranked[:3]:
        print("  · %s：%d 分（权重 %d）—— 每提 1 分，总分 +%.1f" % (name, s, weight, weight / 10.0))

    # 一票否决
    if scores[9] <= 4:
        print("\n⚠️ 合规安全得分过低：如涉及色情/血腥/涉政/侵权等内容，无论总分多高一律不得开工。")
    if scores[5] <= 5:
        print("\n⚠️ 开篇爆发力不足：这是完读率的生死项，建议重新设计第一章开局钩子。")
    if scores[2] <= 5:
        print("\n⚠️ 金手指稀缺性不足：同赛道同质化严重，建议叠加一个差异化元素（如传统题材+克系/规则怪谈）。")
    return total


def show_tracks(which):
    print("=" * 60)
    print("番茄赛道地图（2026-09 口径）")
    print("=" * 60)
    print("\n【男频 14 类】")
    print("  " + " · ".join(MALE_TRACKS))
    print("\n  2026 趋势：")
    for t in MALE_TRENDS:
        print("    - %s" % t)
    print("\n【女频 9 类】")
    print("  " + " · ".join(FEMALE_TRACKS))
    print("\n  2026 趋势：")
    for t in FEMALE_TRENDS:
        print("    - %s" % t)
    print("\n通用新标准：爽点密集，但不能悬浮；读者对脱离现实的剧情容忍度降低。")
    print("核心卖点公式：谁 + 在什么处境 + 靠什么金手指 + 达成什么不可逆的爽")


def main():
    ap = argparse.ArgumentParser(description="番茄小说选题十维评分")
    ap.add_argument("--scores", help="逗号分隔的 10 个分数，如 9,8,7,9,8,9,8,7,6,10")
    ap.add_argument("--track", choices=["男频", "女频", "全部"], help="查看赛道清单与趋势")
    args = ap.parse_args()

    if args.track:
        show_tracks(args.track)
        return 0

    if args.scores:
        parts = [p.strip() for p in args.scores.split(",")]
        if len(parts) != 10:
            print("[错误] 需要 10 个分数，用逗号分隔。")
            return 2
        try:
            scores = [int(p) for p in parts]
        except ValueError:
            print("[错误] 分数必须为整数。")
            return 2
        if any(not (1 <= s <= 10) for s in scores):
            print("[错误] 每个分数必须在 1-10 之间。")
            return 2
    else:
        scores = ask_scores()

    evaluate(scores)
    return 0


if __name__ == "__main__":
    sys.exit(main() or 0)
