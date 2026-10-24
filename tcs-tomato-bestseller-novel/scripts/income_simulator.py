#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
income_simulator.py — 番茄小说 2026 双模式收益模拟器（纯标准库）

用途：在"连载模式"与"完本模式"之间做收益测算与决策，并给出最优路径建议。

数据口径：2026-09-10（2026年番茄小说福利焕新，10-01 起新版全面生效）
所有金额以番茄作家助手官方后台最终展示为准，本工具为决策参考。

用法：
  # 连载模式：模拟签约后 6 个月的收益
  python income_simulator.py --mode serial --listen-read 800,1500,3000,5000,8000,12000 --words 20,20,20,20,20,20

  # 完本模式：40 万字完本，月听读 2500
  python income_simulator.py --mode finished --words 400000 --listen-read 2500 --months 5

  # 对比两种模式
  python income_simulator.py --compare --listen-read 3000 --words 20 --finished-words 400000 --finished-listen 2500

  # 反推：想拿优质全勤，需要多少听读？
  python income_simulator.py --reverse --target-attend
"""

import argparse
import sys

# ============ 2026 新版规则常量（10-01 生效） ============

# 连载模式·全勤奖（月更制）
SERIAL_ATTEND = {
    1: {"name": "第1自然月", "listen_min": 500, "daily_required": False,
        "tiers": [{"words": 150000, "base": 600, "rate": 0.05, "cap": 1500},
                  {"words": 200000, "base": 800, "rate": 0.05, "cap": 2000}]},
    2: {"name": "第2自然月", "listen_min": 500, "daily_required": True,
        "tiers": [{"words": 150000, "base": 600, "rate": 0.05, "cap": 1500},
                  {"words": 200000, "base": 800, "rate": 0.05, "cap": 2000}]},
}
SERIAL_ATTEND_3PLUS = {
    "name": "第3自然月起·优质全勤", "listen_min": 1500, "daily_required": True,
    "base": 1500, "rate": 0.12, "cap": 8000, "words": 200000
}

# 完本模式·启程奖（签约 30 日内，按累计听读）
QICHENG_AWARD = [(3000, 1000), (1500, 500), (700, 300), (300, 100)]

# 完本模式·续航奖（次月起，按月听读）
XUHANG_AWARD = [(8000, None, 1200), (5000, 0.14, None), (2000, 0.12, None), (300, 0.08, None)]

# 完本模式·作品奖励核算周期（月）
PERIOD_BY_WORDS = [(1000000, 12), (800000, 9), (500000, 7), (300000, 5), (0, 3)]

# 完本模式·品质成就奖
QUALITY_AWARD = [
    (150000, 300000, "10万字读完率≥18%", 800, 1500),
    (300000, 500000, "20万字读完率≥9%", 1300, 2000),
    (500000, 800000, "30万字读完率≥门槛", 2000, 3000),
]

# 星燃计划 / 品质臻选奖
XINGRAN = {"listen_min": 1000, "score_min": 7.0}
ZHENXUAN = {"follow_min": 8000, "score_min": 8.0}


def _fmt(v):
    return f"{v:,.0f}"


def serial_month(month_idx, listen, words, daily_ok=True):
    """计算连载模式某月全勤奖。返回 (档位名, 奖金, 说明)"""
    if month_idx >= 3:
        r = SERIAL_ATTEND_3PLUS
        if listen < r["listen_min"]:
            return ("未达标", 0, f"听读 {_fmt(listen)} < {r['listen_min']} 元（斩杀线）")
        if words < r["words"]:
            return ("未达标", 0, f"月更 {_fmt(words)} < {_fmt(r['words'])} 字")
        if not daily_ok:
            return ("未达标", 0, "非每日更新")
        bonus = r["base"] + listen * r["rate"]
        bonus = min(bonus, r["cap"])
        return (r["name"], bonus, f"{r['base']} + {_fmt(listen)}×12% = {_fmt(r['base'] + listen * r['rate'])}，上限 {r['cap']}")
    cfg = SERIAL_ATTEND[month_idx]
    if listen < cfg["listen_min"]:
        return ("未达标", 0, f"听读 {_fmt(listen)} < {cfg['listen_min']} 元")
    if cfg["daily_required"] and not daily_ok:
        return ("未达标", 0, "非每日更新")
    hit = None
    for t in sorted(cfg["tiers"], key=lambda x: -x["words"]):
        if words >= t["words"]:
            hit = t
            break
    if hit is None:
        return ("未达标", 0, f"月更 {_fmt(words)} < 150,000 字")
    bonus = min(hit["base"] + listen * hit["rate"], hit["cap"])
    raw = hit["base"] + listen * hit["rate"]
    note = f"{hit['base']} + {_fmt(listen)}×5% = {_fmt(raw)}"
    if raw > hit["cap"]:
        note += f"，封顶 {hit['cap']}"
    return (f"{cfg['name']}·{_fmt(hit['words'])}字档", bonus, note)


def finished_awards(words, monthly_listen, months=None, score=7.5, read_rate_ok=True):
    """计算完本模式收益。返回 dict"""
    period = 3
    for threshold, m in PERIOD_BY_WORDS:
        if words >= threshold:
            period = m
            break
    if months is None:
        months = period

    # 启程奖（按累计听读：假设首月听读 = monthly_listen）
    qicheng = 0
    for th, bonus in QICHENG_AWARD:
        if monthly_listen >= th:
            qicheng = bonus
            break

    # 续航奖（次月起，即 months-1 个月）
    xuhang_month = 0
    for th, rate, fixed in XUHANG_AWARD:
        if monthly_listen >= th:
            xuhang_month = fixed if fixed else monthly_listen * rate
            break
    xuhang_total = xuhang_month * max(0, months - 1)

    # 品质成就奖
    quality = 0
    quality_cond = ""
    for lo, hi, cond, bonus, listen_req in QUALITY_AWARD:
        if lo <= words < hi:
            if read_rate_ok and monthly_listen * months >= listen_req:
                quality = bonus
                quality_cond = f"{cond} ✓ / 累计听读需 ≥{_fmt(listen_req)}"
            else:
                quality_cond = f"{cond} ✗ / 累计听读需 ≥{_fmt(listen_req)}"
            break
    if words >= 800000:
        quality_cond = "80万字以上档（金额待官方确认）"

    # 星燃计划
    xingran = 0
    if monthly_listen >= XINGRAN["listen_min"] and score >= XINGRAN["score_min"]:
        xingran = monthly_listen * 0.10 * max(0, months - 1)  # 保守估计月奖金

    return {
        "period": period, "months": months,
        "qicheng": qicheng, "xuhang_month": xuhang_month, "xuhang_total": xuhang_total,
        "quality": quality, "quality_cond": quality_cond,
        "xingran": xingran,
        "total": qicheng + xuhang_total + quality + xingran,
    }


def cmd_serial(args):
    listens = [float(x) for x in args.listen_read.split(",")]
    wordss = [float(x) for x in args.words.split(",")]
    # 支持 words 传 "20" 表示每月 20 万字
    if len(wordss) == 1:
        wordss = wordss * len(listens)
    dailys = [True] * len(listens)
    if args.daily:
        dailys = [x.strip().lower() in ("1", "y", "yes", "true") for x in args.daily.split(",")]

    print("=" * 74)
    print("连载模式 · 收益模拟（2026 新版，10-01 生效）")
    print("=" * 74)
    print(f"{'月份':<6}{'听读(元)':>10}{'月更(万字)':>12}{'档位':<22}{'全勤(元)':>10}")
    print("-" * 74)
    total = 0
    total_listen = 0
    for i, (l, w, d) in enumerate(zip(listens, wordss, dailys), start=1):
        name, bonus, note = serial_month(i, l, w * 10000, d)
        total += bonus
        total_listen += l
        flag = "" if bonus else "  ⚠"
        print(f"第{i}月  {l:>10,.0f}{w:>12,.1f}  {name:<22}{bonus:>10,.0f}{flag}")
        if args.verbose and note:
            print(f"         └ {note}")
    print("-" * 74)
    print(f"{'合计':<6}{total_listen:>10,.0f}{'':>12}{'全勤合计':<22}{total:>10,.0f}")
    print(f"\n听读分成总收入（不含全勤）：{total_listen:,.0f} 元")
    print(f"全勤奖合计：{total:,.0f} 元")
    print(f"★ 综合总收入：{total_listen + total:,.0f} 元（{len(listens)} 个月）")
    print(f"  月均：{(total_listen + total) / len(listens):,.0f} 元")
    _advice_serial(listens, wordss)
    return 0


def _advice_serial(listens, wordss):
    print("\n【诊断与建议】")
    if len(listens) >= 3:
        if listens[2] < 1500:
            gap = 1500 - listens[2]
            print(f"  ⚠️ 第 3 月听读 {listens[2]:,.0f} 元，距优质全勤斩杀线 1500 元还差 {gap:,.0f} 元。")
            print(f"     换算：按万阅读单价 ~200 元估算，需日均阅读 ~5000 人次 / 在读 7 万+。")
            print(f"     建议：① 若第 3 月无把握，考虑转完本模式；② 或换快起量赛道（动漫衍生）。")
        else:
            print(f"  ✅ 第 3 月听读达标，可拿优质全勤（1500 + 听读×12%，上限 8000）。")
    avg_w = sum(wordss) / len(wordss)
    if avg_w < 20:
        print(f"  ⚠️ 月均 {avg_w:.1f} 万字，第 3 月起需 ≥20 万字（≈日更 6667 字）才能拿优质全勤。")
    print(f"  💡 全勤同月仅一部作品可获奖；起笔扬帆奖（完本模式）同月可多部。")


def cmd_finished(args):
    words = float(args.words)
    listen = float(args.listen_read)
    score = args.score
    r = finished_awards(words, listen, args.months, score, not args.no_read_rate)

    print("=" * 74)
    print("完本模式 · 收益模拟（2026-09-07 新规）")
    print("=" * 74)
    print(f"完本字数：{words:,.0f} 字")
    print(f"作品奖励核算周期：{r['period']} 个自然月（本次模拟 {r['months']} 个月）")
    print(f"月听读收益：{listen:,.0f} 元 ／ 作品评分：{score}")
    print("-" * 74)
    print(f"{'启程奖（一次性）':<24}{r['qicheng']:>12,.0f} 元")
    print(f"{'续航奖（每月）':<24}{r['xuhang_month']:>12,.0f} 元")
    print(f"{'续航奖（{n}个月合计）'.format(n=max(0, r['months'] - 1)):<22}{r['xuhang_total']:>12,.0f} 元")
    print(f"{'品质成就奖（一次性）':<24}{r['quality']:>12,.0f} 元   {r['quality_cond']}")
    print(f"{'星燃计划（估）':<24}{r['xingran']:>12,.0f} 元")
    print("-" * 74)
    print(f"{'★ 奖励合计':<24}{r['total']:>12,.0f} 元")
    print(f"{'听读分成合计':<24}{listen * r['months']:>12,.0f} 元")
    print(f"{'★ 综合总收入':<24}{r['total'] + listen * r['months']:>12,.0f} 元")
    print(f"  月均：{(r['total'] + listen * r['months']) / r['months']:,.0f} 元")

    print("\n【诊断与建议】")
    if words < 300000:
        print(f"  💡 当前 {words/10000:.0f} 万字档：读完率门槛 18%（较高），但周期仅 3 个月。")
        print(f"     建议：若首次尝试完本模式，30-50 万字档（门槛 9%、周期 5 个月）性价比更高。")
    elif 300000 <= words < 500000:
        print(f"  ✅ 30-50 万字档：风险收益比最优（读完率门槛降至 9%，周期 5 个月）。")
    if listen >= 1000 and score >= 7.0:
        print(f"  ✅ 满足星燃计划门槛（听读≥1000 + 评分≥7.0）。")
    else:
        print(f"  ⚠️ 未达星燃计划门槛：需 听读≥1000（当前 {listen:,.0f}）且 评分≥7.0（当前 {score}）。")
    print(f"  💡 完本书 = 万能钥匙：可替代 7+ 项征文/短剧激励的字数要求。")
    print(f"  💡 起笔扬帆奖同月可多部获奖 → 批量完本书的收益主要来自「续航奖 × N 部」。")
    return 0


def cmd_compare(args):
    print("=" * 74)
    print("连载 vs 完本 · 模式决策对比")
    print("=" * 74)
    sl = float(args.listen_read)
    sw = float(args.words) * 10000
    fw = float(args.finished_words)
    fl = float(args.finished_listen)

    # 连载：6 个月
    listens = [sl] * 6
    wordss = [sw / 10000] * 6
    s_total_attend = 0
    for i in range(1, 7):
        _, b, _ = serial_month(i, listens[i - 1], wordss[i - 1] * 10000, True)
        s_total_attend += b
    s_total = s_total_attend + sl * 6

    # 完本：5 个月
    r = finished_awards(fw, fl, 5, args.score)
    f_total = r["total"] + fl * 5

    print(f"{'维度':<20}{'连载模式（6个月）':<28}{'完本模式（5个月）':<26}")
    print("-" * 74)
    print(f"{'月更要求':<20}{'15-20 万字/月（日更5-6.7千）':<26}{'无（先写完再签）':<26}")
    print(f"{'听读门槛':<20}{'第3月起 ≥1500 元':<28}{'无硬性门槛':<26}")
    print(f"{'奖励合计':<20}{s_total_attend:>10,.0f} 元{'':<16}{r['total']:>10,.0f} 元")
    print(f"{'听读分成':<20}{sl * 6:>10,.0f} 元{'':<16}{fl * 5:>10,.0f} 元")
    print(f"{'★ 综合收入':<20}{s_total:>10,.0f} 元{'':<16}{f_total:>10,.0f} 元")
    print(f"{'月均':<20}{s_total / 6:>10,.0f} 元{'':<16}{f_total / 5:>10,.0f} 元")
    print("-" * 74)

    print("\n【决策建议】")
    if s_total / 6 > f_total / 5:
        print(f"  → 按当前参数，**连载模式**月均更高（{s_total/6:,.0f} vs {f_total/5:,.0f}）。")
        print(f"     前提：你能稳定日更 {sw/300000*10:.1f} 千字/天，且第 3 月听读能上 1500 元。")
    else:
        print(f"  → 按当前参数，**完本模式**月均更高（{f_total/5:,.0f} vs {s_total/6:,.0f}）。")
        print(f"     且完本模式不逼日更、风险更低，并解锁「万能钥匙」。")
    print(f"\n  ⚠️ 关键提醒：连载模式的收入高度依赖第 3 月起的听读 1500 元斩杀线。")
    print(f"     若你的书属于慢热题材（纯玄幻、种田），强烈建议走完本模式。")
    return 0


def cmd_reverse(args):
    print("=" * 74)
    print("反推测算：达标需要什么数据？")
    print("=" * 74)
    print("\n【优质全勤奖（第 3 自然月起）】")
    print("  门槛：月听读 ≥ 1500 元 + 每日更新 + 月更 ≥ 20 万字")
    print("  换算（按万阅读单价 ~200 元估算）：")
    for unit in (100, 150, 200, 300):
        need_reads = 1500 / unit * 10000
        print(f"    单价 {unit:>3} 元/万阅读 → 需月阅读 {need_reads:>10,.0f} 次（日均 {need_reads/30:>8,.0f}）")
    print("\n  月更 20 万字换算：")
    for days in (28, 30, 31):
        print(f"    {days} 天月 → 日均 {200000/days:>7,.0f} 字")
    print("\n【品质臻选奖】")
    print(f"  门槛：7 日有效追更月末 7 日均值 ≥ {ZHENXUAN['follow_min']:,} 人 + 月末 7 日评分 ≥ {ZHENXUAN['score_min']}")
    print("\n【星燃计划（完本）】")
    print(f"  门槛：月听读 ≥ {XINGRAN['listen_min']:,} 元 + 月末 7 日评分 ≥ {XINGRAN['score_min']}")
    print("\n【品质成就奖 · 读完率要求】")
    for lo, hi, cond, bonus, lr in QUALITY_AWARD:
        print(f"    {lo/10000:.0f}-{hi/10000:.0f} 万字：{cond}，累计听读 ≥{lr:,} 元 → {bonus:,} 元")
    return 0


def main():
    p = argparse.ArgumentParser(description="番茄小说 2026 双模式收益模拟器")
    sub = p.add_subparsers(dest="cmd")

    s = sub.add_parser("serial", aliases=["s"], help="连载模式模拟")
    s.add_argument("--listen-read", required=True, help="月听读收益，逗号分隔（元）")
    s.add_argument("--words", required=True, help="月更新字数（万字），逗号分隔；单值则所有月相同")
    s.add_argument("--daily", help="是否每日更新，逗号分隔 1/0")
    s.add_argument("--verbose", action="store_true")
    s.set_defaults(func=cmd_serial)

    f = sub.add_parser("finished", aliases=["f"], help="完本模式模拟")
    f.add_argument("--words", required=True, help="完本总字数")
    f.add_argument("--listen-read", required=True, help="月听读收益（元）")
    f.add_argument("--months", type=int, help="模拟月数（默认按核算周期）")
    f.add_argument("--score", type=float, default=7.5, help="作品评分（默认 7.5）")
    f.add_argument("--no-read-rate", action="store_true", help="读完率未达标")
    f.set_defaults(func=cmd_finished)

    c = sub.add_parser("compare", aliases=["c"], help="两种模式对比")
    c.add_argument("--listen-read", required=True, help="连载模式月听读（元）")
    c.add_argument("--words", required=True, help="连载模式月更（万字）")
    c.add_argument("--finished-words", default="400000", help="完本总字数")
    c.add_argument("--finished-listen", default="2500", help="完本月听读（元）")
    c.add_argument("--score", type=float, default=7.5)
    c.set_defaults(func=cmd_compare)

    r = sub.add_parser("reverse", aliases=["r"], help="反推达标所需数据")
    r.add_argument("--target-attend", action="store_true")
    r.set_defaults(func=cmd_reverse)

    # 兼容：python income_simulator.py --mode serial ...
    p.add_argument("--mode", help=argparse.SUPPRESS)
    p.add_argument("--compare", action="store_true", help=argparse.SUPPRESS)
    p.add_argument("--reverse", action="store_true", help=argparse.SUPPRESS)

    args = p.parse_args()
    if hasattr(args, "func"):
        return args.func(args)
    if args.reverse:
        return cmd_reverse(args)
    if args.compare:
        return cmd_compare(args)
    if args.mode in ("serial", "s"):
        return cmd_serial(args)
    if args.mode in ("finished", "f"):
        return cmd_finished(args)
    p.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
