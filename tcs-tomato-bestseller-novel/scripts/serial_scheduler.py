# -*- coding: utf-8 -*-
"""连载排期与存稿管理器（serial_scheduler）
番茄爆款小说专家 · 内置知识库脚本（口径：2026-09）

输入目标字数、日更量、起始日期与当前存稿，输出：
  ① 连载排期表（阶段目标、里程碑、预计完本日）
  ② 存稿水位预警（红/黄/绿三档）
  ③ 断更风险点与补稿建议
  ④ 全勤达标可行性判定（按 2026-09 口径的门槛字数）

纯标准库实现，零联网、零第三方依赖。

用法：
    python serial_scheduler.py --target-words 1000000 --daily 6000 --stock 20000
    python serial_scheduler.py --target-words 300000 --daily 4000 --start 2026-10-01 --md 排期.md
    python serial_scheduler.py --target-words 1000000 --daily 6000 --stock 40000 --json 排期.json
"""
import argparse
import datetime as dt
import io
import json
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

CAP = "资源库口径：2026-09"

# 2026-09 口径：全勤门槛（字节数按中文 1 字≈1 汉字计，平台按字数计）
DAILY_ATTEND_MIN = 4000       # 日更门槛（保守通用口径）
MONTHLY_ATTEND_MIN = 120000   # 月更新门槛（约 30 天 × 4000）
STOCK_RED = 10000             # 存稿红线
STOCK_YELLOW = 30000          # 存稿黄线
STOCK_TIMES = 5               # 建议安全存稿 = 5 天日更量


def parse_date(s):
    return dt.date.fromisoformat(s)


def build(target, daily, start, stock, min_daily):
    today = dt.date.today()
    if start < today:
        start = today
    total_days = 0 if daily <= 0 else (target + daily - 1) // daily
    finish = start + dt.timedelta(days=total_days)

    lines = []
    lines.append("# 番茄连载排期与存稿管理表")
    lines.append("")
    lines.append("> %s　｜　生成器 serial_scheduler v1.0　｜　生成时间：%s"
                 % (CAP, dt.datetime.now().strftime("%Y-%m-%d %H:%M")))
    lines.append("")
    lines.append("## 一、核心参数")
    lines.append("")
    lines.append("| 参数 | 值 |")
    lines.append("|---|---|")
    lines.append("| 目标总字数 | %s 字 |" % f"{target:,}")
    lines.append("| 日更目标 | %s 字/天 |" % f"{daily:,}")
    lines.append("| 起始日期 | %s |" % start)
    lines.append("| 当前存稿 | %s 字 |" % f"{stock:,}")
    lines.append("| 预计连载天数 | %d 天 |" % total_days)
    lines.append("| 预计完本日期 | %s |" % finish)
    lines.append("")
    lines.append("## 二、阶段排期表")
    lines.append("")

    stage_names = ["开篇期（黄金三章·首秀）", "爬坡期（首月冲榜）", "稳定期（签约巩固）",
                   "爆发期（榜单冲刺）", "收官期（完本续签）"]
    n = len(stage_names)
    seg = max(1, total_days // n)
    lines.append("| 阶段 | 起止日期 | 目标字数 | 阶段天数 | 重点任务 |")
    lines.append("|---|---|---|---|---|")
    tasks = [
        "前 3 章定生死：亮牌、给爽点、留钩子",
        "稳定日更不断更，拉满完读率与追更率",
        "数据稳定后提交签约，守住全勤门槛",
        "对照榜单复盘，做一次节奏与钩子强化",
        "控制节奏收束支线，准备完本与续签",
    ]
    for i, name in enumerate(stage_names):
        s = start + dt.timedelta(days=i * seg)
        e = start + dt.timedelta(days=min(total_days, (i + 1) * seg) - 1)
        w = min(target, (i + 1) * seg * daily) - i * seg * daily
        lines.append("| %s | %s ~ %s | %s 字 | %d 天 | %s |"
                     % (name, s, e, f"{max(0, w):,}", seg, tasks[i]))
    lines.append("")

    # 存稿水位
    lines.append("## 三、存稿水位预警")
    lines.append("")
    if stock >= STOCK_YELLOW or stock >= daily * STOCK_TIMES:
        level, icon = "绿色 · 安全", "🟢"
        advice = "存稿充足，可支撑主动运营（如集中放更、冲榜窗口加更）。"
    elif stock >= STOCK_RED:
        level, icon = "黄色 · 警戒", "🟡"
        advice = "存稿偏薄，建议本周补稿至 %s 字以上，避免突发断更。" % f"{daily * STOCK_TIMES:,}"
    else:
        level, icon = "红色 · 危险", "🔴"
        advice = "存稿过低！断更会直接打断推荐评估。优先补稿，必要时降低日更目标保不断更。"
    lines.append("- 当前水位：%s（存稿 %s 字 / 安全线 %s 字）"
                 % (level, f"{stock:,}", f"{daily * STOCK_TIMES:,}"))
    lines.append("- %s %s" % (icon, advice))
    lines.append("")

    # 全勤可行性
    lines.append("## 四、全勤达标可行性判定")
    lines.append("")
    ok = daily >= min_daily
    lines.append("- 日更门槛（保守口径）：%s 字/天" % f"{min_daily:,}")
    lines.append("- 月度门槛（约 30 天）：%s 字" % f"{MONTHLY_ATTEND_MIN:,}")
    lines.append("- 当前日更目标 %s：**%s**"
                 % (f"{daily:,}", "可达标 ✅" if ok else "不达标 ⚠️（缺口 %s 字/天）" % f"{min_daily - daily:,}"))
    if not ok:
        lines.append("- 建议：日更提至 %s 字以上，或采用‘单双日交替加更’补足月门槛。" % f"{min_daily:,}")
    lines.append("")

    # 断更风险点
    lines.append("## 五、断更风险点与补稿建议")
    lines.append("")
    need = daily * STOCK_TIMES - stock
    lines.append("| 风险点 | 触发条件 | 对策 |")
    lines.append("|---|---|---|")
    lines.append("| 存稿枯竭 | 存稿 < %s 字 | 本次需补稿 %s 字 |"
                 % (f"{STOCK_RED:,}", f"{max(0, need):,}"))
    lines.append("| 卡文断更 | 无细纲就写正文 | 先落 30 章细纲（outline_builder.py）再日更 |")
    lines.append("| 数据下滑 | 追读率连续 3 天走低 | 立即做一次钩子强化（hook_generator.py） |")
    lines.append("| 质量滑坡 | 短期内高频更新 | 每 10 章跑一次质量自检（quality_selfcheck.py） |")
    lines.append("")

    # 关键里程碑日期
    lines.append("## 六、关键里程碑日程（可直接写进日历）")
    lines.append("")
    for d, t in ((0, "开书日：上传第一章"), (3, "黄金三章完成，进入首秀评估"),
                 (7, "首发 7 天数据复盘节点"), (30, "首月复盘：签约与全勤校验"),
                 (int(total_days * 0.5), "半程体检：节奏与留存诊断"),
                 (total_days, "完本日：准备完本续签与 IP 衍生")):
        lines.append("- %s　%s" % (start + dt.timedelta(days=max(0, d)), t))
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("*%s ｜ 平台门槛与收益规则以官方当月公告为准，本表为作战参考。*" % CAP)
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description="连载排期与存稿管理器")
    ap.add_argument("--target-words", type=int, required=True, help="目标总字数")
    ap.add_argument("--daily", type=int, required=True, help="日更字数")
    ap.add_argument("--start", default=None, help="起始日期 YYYY-MM-DD（默认今天）")
    ap.add_argument("--stock", type=int, default=0, help="当前存稿字数")
    ap.add_argument("--min-daily", type=int, default=DAILY_ATTEND_MIN, help="日更门槛口径")
    ap.add_argument("--json", default=None, help="输出 JSON 到指定路径")
    ap.add_argument("--md", default=None, help="输出 Markdown 到指定路径")
    args = ap.parse_args()

    start = parse_date(args.start) if args.start else dt.date.today()
    md = build(args.target_words, args.daily, start, args.stock, args.min_daily)
    print(md)
    if args.md:
        io.open(args.md, "w", encoding="utf-8", newline="\n").write(md)
        print("\n[已写出] %s" % args.md)
    if args.json:
        total_days = 0 if args.daily <= 0 else (args.target_words + args.daily - 1) // args.daily
        io.open(args.json, "w", encoding="utf-8", newline="\n").write(json.dumps({
            "cap": CAP, "targetWords": args.target_words, "daily": args.daily,
            "start": str(start), "stock": args.stock, "totalDays": total_days,
            "finish": str(start + dt.timedelta(days=total_days)),
            "stockLevel": ("green" if args.stock >= max(STOCK_YELLOW, args.daily * STOCK_TIMES)
                           else "yellow" if args.stock >= STOCK_RED else "red"),
        }, ensure_ascii=False, indent=2))
        print("[已写出] %s" % args.json)
    return 0


if __name__ == "__main__":
    sys.exit(main())
