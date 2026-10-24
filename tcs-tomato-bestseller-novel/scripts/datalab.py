#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
datalab.py — 番茄爆款小说专家 · 后台数据诊断看板（纯标准库）

把番茄后台的冷数据，转成"下一章改哪里"的热动作。提供三种模式：

  1) 指标诊断（默认）
     python datalab.py --metrics 吸量=300,追读=28,完读10万=12,章均完读=45,时长=75 --track 都市高武
     → 九指标逐项打分 + 归因 + 修复动作 + Markdown 报告落盘

  2) 收益精算
     python datalab.py --revenue --valid-reads 50000 --ecpm 12
     → 听读收益 / 全勤 / 奖励叠加 三层折算

  3) 生成报告
     python datalab.py --metrics ... --report 数据诊断报告.md

2026-09 红线口径：
  吸量 S 级 ≥400　|　前 3 章完读 ≥15%（脑洞）/10%（传统）
  10 万字完读 ≥15%（潜力池）；<8% 失推荐　|　追读率 ≥35%（理想 2:1）
"""

import argparse
import json
import os
import sys
from datetime import datetime

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

# ============ 九指标定义与红线 ============
# key: (中文名, 单位, 红线值, 方向, 权重)
METRICS = [
    ("吸量",      "阅读",   400,   "up", 10),
    ("CTR",       "%",      6,     "up", 8),
    ("前3章完读", "%",      15,    "up", 10),
    ("完读10万",  "%",      15,    "up", 10),
    ("追读",      "%",      35,    "up", 10),
    ("留存",      "%",      35,    "up", 8),
    ("章均完读",  "%",      50,    "up", 8),
    ("在读",      "万",     7,     "up", 6),
    ("时长",      "秒",     90,    "up", 10),
]

# 归因表：指标 → 问题定位 → 修复动作 → 关联知识文件
DIAGNOSIS = {
    "吸量":     ("书名 / 封面 / 简介不抓人", "重做三件套：书名四型公式 + 封面分赛道模板 + 简介三段式",
                 ["09"], ["title_maker.py"]),
    "CTR":      ("曝光转化低，跟吸量同源", "同上；检查书名是否精准筛选目标读者",
                 ["09"], ["title_maker.py"]),
    "前3章完读": ("开篇劝退：前 200 字无冲突 / 慢热 / 信息过载", "重写前 3 章：前 50 字出事 + 首章亮金手指 + 第三章打脸",
                 ["10", "11", "42"], ["hook_density.py"]),
    "完读10万":  ("中段疲软：爽点密度不足 / 支线拖沓 / 主线停滞", "提速档：删过渡章 + 每章一爽点 + 缩短憋屈期",
                 ["12", "45", "43"], ["rhythm_analyzer.py"]),
    "追读":      ("章末钩子失效 / 更新不稳定", "每章末装 ★★★★ 级钩子 + 固定更新时段（避 22-24 点）",
                 ["13", "24"], ["hook_generator.py", "hook_density.py"]),
    "留存":      ("人设不抓人 / 情绪回报不足", "强化主角处境代入 + 每卷 2 个名场面",
                 ["19", "44"], ["rhythm_analyzer.py"]),
    "章均完读":  ("单章结构问题：段落过长 / 对话过少 / 无信息增量", "单章 1800-2600 字，单段 ≤200 字，每 300 字新信息",
                 ["32", "12"], ["rhythm_analyzer.py"]),
    "在读":      ("整体盘子小，需综合提升", "按最低分指标优先修复",
                 ["21"], []),
    "时长":      ("单章过短读不完 / 过长读不到 50%", "单章落在 1800-2600 字最优区间",
                 ["32", "35"], ["rhythm_analyzer.py"]),
}


def _parse_metrics(s):
    d = {}
    for part in s.split(","):
        if "=" not in part:
            continue
        k, v = part.split("=", 1)
        try:
            d[k.strip()] = float(v.strip())
        except ValueError:
            pass
    return d


def _score_one(name, val, redline, direction):
    """0-10 分：达到红线 = 6 分；达到红线 1.5 倍 = 10 分。"""
    if direction == "up":
        if val >= redline * 1.5:
            return 10.0
        if val >= redline:
            return 6.0 + (val - redline) / (redline * 0.5) * 4.0
        return max(0.0, val / redline * 6.0)
    return 6.0


def cmd_metrics(args):
    data = _parse_metrics(args.metrics)
    if not data:
        print("[ERR] --metrics 格式示例：吸量=300,追读=28,完读10万=12")
        return 1
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    L = ["# 番茄爆款小说 · 后台数据诊断报告", "",
         "- 生成时间：%s" % now,
         "- 赛道：%s" % (args.track or "未指定"), "- 口径：2026-09", "",
         "## 一、九指标逐项诊断", "",
         "| 指标 | 当前值 | 红线 | 得分 | 状态 |", "|---|---|---|---|---|"]
    print("=" * 82)
    print("番茄爆款小说 · 数据诊断（口径 2026-09）  赛道：%s" % (args.track or "未指定"))
    print("=" * 82)
    print("%-10s %-10s %-10s %-8s %s" % ("指标", "当前值", "红线", "得分", "状态"))
    print("-" * 82)

    total_w = 0.0
    total_s = 0.0
    problems = []
    for name, unit, redline, direction, weight in METRICS:
        if name not in data:
            continue
        val = data[name]
        sc = _score_one(name, val, redline, direction)
        total_w += weight
        total_s += sc * weight
        if val >= redline:
            st = "✅ 达标"
        elif val >= redline * 0.7:
            st = "⚠️ 临界"
        else:
            st = "🔴 危险"
        if val < redline:
            problems.append((name, val, redline, sc))
        print("%-10s %-10s %-10s %-8.1f %s" % (name, val, redline, sc, st))
        L.append("| %s | %s | %s | %.1f | %s |" % (name, val, redline, sc, st))

    overall = (total_s / total_w) if total_w else 0
    print("-" * 82)
    print("综合得分：%.1f / 10" % overall)
    grade = "S（精品线以上）" if overall >= 8.5 else ("A（稳）" if overall >= 7 else
            ("B（需优化）" if overall >= 5.5 else "C（危险，需救书）"))
    print("评级：%s" % grade)

    L += ["", "## 二、综合评级", "",
          "- **综合得分**：%.1f / 10" % overall, "- **评级**：%s" % grade, ""]

    problems.sort(key=lambda x: x[3])
    L += ["## 三、问题归因与修复动作（按优先级）", ""]
    print("\n" + "=" * 82)
    print("问题归因与修复动作（按优先级）")
    print("=" * 82)
    if not problems:
        print("✅ 全部指标达标——转为冲榜与 IP 变现阶段。")
        L.append("✅ 全部指标达标——转为冲榜与 IP 变现阶段。")
    for i, (name, val, redline, sc) in enumerate(problems[:5], 1):
        cause, fix, refs, tools = DIAGNOSIS.get(name, ("待分析", "按 21 号诊断 SOP 处理", ["21"], []))
        print("%d. 【%s】%s（当前 %s / 红线 %s）" % (i, name, cause, val, redline))
        print("   修复：%s" % fix)
        print("   参考：references/%s 号" % "、".join(refs))
        if tools:
            print("   工具：%s" % "、".join(tools))
        print()
        L += ["### %d. 【%s】" % (i, name), "",
              "- 当前值 %s ／ 红线 %s ／ 得分 %.1f" % (val, redline, sc),
              "- 问题定位：%s" % cause,
              "- 修复动作：%s" % fix,
              "- 参考知识：references/%s 号" % "、".join(refs),
              "- 可用脚本：%s" % ("、".join(tools) if tools else "——"), ""]

    L += ["## 四、30 天救书作战表", "",
          "| 周次 | 重点 | 目标 |", "|---|---|---|"]
    weeks = [("第 1 周", "修复最高优先级指标", "该指标回到红线以上"),
             ("第 2 周", "修复次高优先级指标", "综合分 +1.0"),
             ("第 3 周", "节奏与钩子全面复检", "追读率 ≥35%"),
             ("第 4 周", "数据复盘与切书判定", "综合分 ≥7.0 或启动新书")]
    for w, f_, g in weeks:
        L.append("| %s | %s | %s |" % (w, f_, g))
    L += ["", "> 详细归因树与救书 SOP 见 references/21 号；数据红线口径 2026-09。", "",
          "> **免责**：数据指标以番茄作者后台实际展示为准。"]

    out = args.report or "数据诊断报告.md"
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(L) + "\n")
    print("=" * 82)
    print("[OK] 报告已落盘：%s" % os.path.abspath(out))
    return 0


def cmd_revenue(args):
    vr = args.valid_reads or 0
    ecpm = args.ecpm or 12.0
    # 有效阅读分成按 eCPM 的 1/40 估算（0.1-0.5 元/千次区间中值口径）
    per_k = ecpm / 40.0
    listen = vr / 1000.0 * per_k
    print("=" * 62)
    print("收益精算（口径 2026-09，示意模型）")
    print("=" * 62)
    print("日均有效阅读   : %s" % ("{:,}".format(int(vr)) if vr else "—"))
    print("eCPM（元/千次）: %.1f" % ecpm)
    print("千次有效阅读分成: %.3f 元" % per_k)
    print("-" * 62)
    print("日听读收益     : %.2f 元" % listen)
    print("月听读收益(30天): %.2f 元" % (listen * 30))
    print("-" * 62)
    m = listen * 30
    print("奖励可达性预判：")
    print("  全勤（听读≥500）        : %s" % ("✅" if m >= 500 else "❌"))
    print("  优质全勤（听读≥1500）    : %s" % ("✅" if m >= 1500 else "❌"))
    print("  星火计划（听读≥1000）    : %s" % ("✅" if m >= 1000 else "❌"))
    print("-" * 62)
    print("注：全勤/星火金额另计；本模型仅折算听读分成部分。")
    print("免责：eCPM 个体差异极大，具体以番茄作者后台当月结算为准。")
    return 0


def main():
    p = argparse.ArgumentParser(description="番茄爆款小说专家 · 数据诊断看板")
    p.add_argument("--metrics", help="指标：吸量=300,追读=28,完读10万=12,...")
    p.add_argument("--track", help="赛道")
    p.add_argument("--report", nargs="?", const="数据诊断报告.md", help="输出 Markdown 报告")
    p.add_argument("--revenue", action="store_true", help="收益精算模式")
    p.add_argument("--valid-reads", type=float, help="日均有效阅读量")
    p.add_argument("--ecpm", type=float, help="eCPM（元/千次）")
    args = p.parse_args()
    if args.revenue:
        return cmd_revenue(args)
    if args.metrics:
        return cmd_metrics(args)
    p.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
