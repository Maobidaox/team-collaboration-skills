#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
番茄爆款小说专家 · 字数 / 全勤打卡 / 收益测算
----------------------------------------------
纯标准库实现，零第三方依赖，跨平台。

功能：
  1) count   统计稿件（文件或目录）中文字数与章节数
  2) attend  全勤打卡测算：给定日更字数与月份，输出是否达标与预计全勤档位
  3) income  听读分成与全勤收益区间估算（非承诺）

用法：
  python novel_metrics.py count  稿件.md
  python novel_metrics.py count  目录/ --recursive
  python novel_metrics.py attend --daily 4000 --days 30 --listen-read 520
  python novel_metrics.py income --reads 3000 --days 30 --tier 4000
  python novel_metrics.py plan --target-words 100000 --daily 6000

口径：2026-09（全勤 2026 新规）。所有收益为区间估算，非承诺。
"""

import argparse
import os
import re
import sys
from datetime import date

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

# 2026 全勤口径
ATTENDANCE = {
    4000: {"base": 600, "bonus_cap": 1500},
    6000: {"base": 800, "bonus_cap": 2000},
}
LISTEN_READ_THRESHOLD = 500  # 元/月（2026 新规）

# 有效万次阅读收益区间（元），2026-05 调价后
READ_UNIT_MIN, READ_UNIT_MAX = 80, 240


def count_chinese(text):
    return len(re.findall(r"[\u4e00-\u9fa5]", text))


def cmd_count(path, recursive=False):
    files = []
    if os.path.isfile(path):
        files = [path]
    elif os.path.isdir(path):
        if recursive:
            for root, _, names in os.walk(path):
                for n in names:
                    if n.lower().endswith((".md", ".txt")):
                        files.append(os.path.join(root, n))
        else:
            files = [os.path.join(path, n) for n in os.listdir(path)
                     if n.lower().endswith((".md", ".txt"))]
    else:
        print("[错误] 路径不存在：%s" % path)
        return 2

    files.sort()
    total = 0
    chapters = 0
    print("=" * 58)
    print("字数统计（口径：中文字符数）")
    print("=" * 58)
    for f in files:
        with open(f, "r", encoding="utf-8", errors="ignore") as fh:
            t = fh.read()
        c = count_chinese(t)
        ch = len(re.findall(r"^#{1,4}\s*第?\s*\d+\s*章", t, re.M))
        chapters += ch
        total += c
        print("%-46s %7d 字  %2d 章" % (os.path.basename(f)[:44], c, ch))
    print("-" * 58)
    print("%-46s %7d 字  %2d 章" % ("合计", total, chapters))
    print("-" * 58)
    # 里程碑提示
    for milestone, desc in [(80000, "推荐评估节点"), (100000, "首秀节点"),
                            (500000, "中期放量"), (1000000, "长尾流量池")]:
        if total < milestone:
            print("距 %d 字（%s）还差 %d 字" % (milestone, desc, milestone - total))
            break
    else:
        print("已超过 100 万字，进入长尾流量池阶段")
    return 0


def cmd_attend(daily, days, listen_read, words_100k=True):
    print("=" * 58)
    print("全勤打卡测算（2026 口径）")
    print("=" * 58)
    tier = 4000 if daily < 6000 else 6000
    conf = ATTENDANCE[tier]
    print("日更字数     : %d 字 → 判定档位 %d 字档" % (daily, tier))
    print("统计天数     : %d 天" % days)
    print("听读收益     : %.2f 元（门槛 %d 元）" % (listen_read, LISTEN_READ_THRESHOLD))
    print("-" * 58)

    ok_daily = daily >= tier
    ok_listen = listen_read >= LISTEN_READ_THRESHOLD
    print("① 更新门槛   : %s（需每日有效更新 ≥%d 字）" % ("✅ 通过" if ok_daily else "❌ 未达", tier))
    print("② 收益门槛   : %s（需当月听读分成 ≥%d 元）" % ("✅ 通过" if ok_listen else "❌ 未达", LISTEN_READ_THRESHOLD))
    print("③ 字数门槛   : %s（需签约作品有效过审满 10 万字的次月起）"
          % ("✅ 满足" if words_100k else "❌ 不满足"))
    print("-" * 58)

    if ok_daily and ok_listen and words_100k:
        bonus = min(listen_read * 0.05, conf["bonus_cap"])
        total = conf["base"] + bonus
        print("基础全勤     : %d 元" % conf["base"])
        print("5%% 听读加成 : %.2f 元（上限 %d 元）" % (bonus, conf["bonus_cap"]))
        print("预计全勤合计 : %.2f 元/月" % total)
        print("含听读总收入 : %.2f 元/月（区间估算，非承诺）" % (total + listen_read))
        print("\n判定：✅ 符合 2026 全勤获奖条件")
    else:
        print("判定：❌ 不满足全勤条件，缺口见上。")
        if not ok_listen:
            print("      建议：提升完读率与在读人数，先跨过 %d 元听读门槛。" % LISTEN_READ_THRESHOLD)
        if not ok_daily:
            print("      建议：日更提升至 %d 字以上并提前存稿，避免断更。" % tier)
    return 0


def cmd_income(reads, days, tier):
    print("=" * 58)
    print("收益区间估算（2026 口径 · 非承诺）")
    print("=" * 58)
    print("每日在读     : %d 人" % reads)
    print("统计天数     : %d 天" % days)
    print("更新档位     : %d 字/日" % tier)
    print("-" * 58)
    # 有效万次阅读收益区间：按每日有效阅读次数≈在读人数保守估算
    monthly_units = reads * days / 10000.0
    lo = monthly_units * READ_UNIT_MIN
    hi = monthly_units * READ_UNIT_MAX
    print("有效万次阅读 : %.1f 个/月" % monthly_units)
    print("听读分成区间 : %.0f - %.0f 元/月（单价 %d-%d 元/万次）"
          % (lo, hi, READ_UNIT_MIN, READ_UNIT_MAX))
    conf = ATTENDANCE.get(tier, ATTENDANCE[4000])
    if lo >= LISTEN_READ_THRESHOLD:
        bonus_lo = min(lo * 0.05, conf["bonus_cap"])
        bonus_hi = min(hi * 0.05, conf["bonus_cap"])
        print("全勤基础     : %d 元 + 5%% 加成 %.0f-%.0f 元" % (conf["base"], bonus_lo, bonus_hi))
        print("月收入区间   : %.0f - %.0f 元" % (lo + conf["base"] + bonus_lo, hi + conf["base"] + bonus_hi))
        print("\n判定：✅ 大概率跨过 %d 元听读门槛" % LISTEN_READ_THRESHOLD)
    else:
        print("全勤基础     : 不满足（听读收益未达 %d 元门槛）" % LISTEN_READ_THRESHOLD)
        print("月收入区间   : %.0f - %.0f 元" % (lo, hi))
        print("\n判定：❌ 需先提升在读与完读率")
    print("\n⚠️ 测算基于 2026 年公开规则的区间估算，受广告单价、题材、完读率等多重因素影响，非收益承诺。")
    return 0


def cmd_plan(target, daily):
    print("=" * 58)
    print("更新与存稿规划")
    print("=" * 58)
    need_days = target / daily if daily else 0
    print("目标字数     : %d 字" % target)
    print("日更         : %d 字" % daily)
    print("需要天数     : %.1f 天" % need_days)
    print("-" * 58)
    print("建议存稿     : %d 天（%.0f 字）" % (7, daily * 7))
    print("8 万字评估前 : 存稿 ≥7 天")
    print("10 万字首秀前: 存稿 ≥10-14 天（首秀期约 21 天，严禁断更）")
    print("-" * 58)
    print("⚠️ 首秀期（21 天）严禁：断更、大改前 10 章、换封面、重写简介。")
    return 0


def main():
    ap = argparse.ArgumentParser(description="番茄小说字数 / 全勤 / 收益测算")
    sub = ap.add_subparsers(dest="cmd")

    p1 = sub.add_parser("count", help="统计字数")
    p1.add_argument("path")
    p1.add_argument("--recursive", action="store_true")

    p2 = sub.add_parser("attend", help="全勤打卡测算")
    p2.add_argument("--daily", type=int, default=4000)
    p2.add_argument("--days", type=int, default=30)
    p2.add_argument("--listen-read", type=float, default=0)
    p2.add_argument("--no-100k", action="store_true")

    p3 = sub.add_parser("income", help="收益区间估算")
    p3.add_argument("--reads", type=int, default=3000)
    p3.add_argument("--days", type=int, default=30)
    p3.add_argument("--tier", type=int, default=4000, choices=[4000, 6000])

    p4 = sub.add_parser("plan", help="更新与存稿规划")
    p4.add_argument("--target-words", type=int, default=100000)
    p4.add_argument("--daily", type=int, default=6000)

    args = ap.parse_args()
    if not args.cmd:
        ap.print_help()
        return 0

    if args.cmd == "count":
        return cmd_count(args.path, args.recursive)
    if args.cmd == "attend":
        return cmd_attend(args.daily, args.days, args.listen_read, not args.no_100k)
    if args.cmd == "income":
        return cmd_income(args.reads, args.days, args.tier)
    if args.cmd == "plan":
        return cmd_plan(args.target_words, args.daily)
    return 0


if __name__ == "__main__":
    sys.exit(main() or 0)
