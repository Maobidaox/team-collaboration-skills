#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
chapter_forge.py — 番茄爆款小说专家 · 章节生产脚手架（纯标准库）

把"写一本书"拆成"写一章"，把"写一章"拆成"填七个格子"。本脚本为每一章
生成**结构骨架 + 逐步写作提示词 + 硬标准自检清单**，产出可直接喂给自己
（或用户）逐段填充的 Markdown 写作单。

用法：
  python chapter_forge.py --chapter 1 --track 都市高武 --hook "主角在殡仪馆发现死者手机里有自己的视频"
  python chapter_forge.py --chapter 5 --track 悬疑脑洞 --type 蓄爆 --words 2200
  python chapter_forge.py --range 1-3 --track 都市脑洞 --outline 前3章大纲.md
  python chapter_forge.py --batch 1-30 --track 重生年代 --volume 1 --report 写作单.md

章节类型（--type）：
  开局（留存生死期，爽点 ×2-3） / 常规（每章 1 爽点） / 蓄爆（降密蓄势，≤2 章） / 高潮（大爽点，回收伏笔）
"""

import argparse
import os
import sys
from datetime import datetime

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

# 七格结构（每章通用骨架）
SEVEN_CELLS = [
    ("① 开场锚点", "用一句话交代「谁、在哪、在干什么」——听书友好，替代翻页回忆"),
    ("② 冲突触发", "前 300 字内出现新信息 / 新动作 / 新异常"),
    ("③ 情绪加压", "让主角处境更糟一点（读者要看到「憋屈」才有后面的「爽」）"),
    ("④ 转折节点", "出现变化：线索、金手指、援军、意外（本章中段的位置）"),
    ("⑤ 爽点释放", "本章的情绪出口：打脸 / 得到 / 顿悟 / 反转（必须有）"),
    ("⑥ 群体反应", "旁观者的震惊 / 羡慕 / 追悔（低成本高密度的爽感配菜）"),
    ("⑦ 章末钩子", "装一个 ≥★★★ 级的断点（详见 references/13 号）"),
]

TYPE_SPEC = {
    "开局":   dict(payoffs="2-3 个", hook="★★★★★", note="留存生死期，密度拉满；第 1 章必须亮金手指"),
    "常规":   dict(payoffs="1-2 个", hook="≥★★★", note="稳定输出；每 300 字一个新信息"),
    "蓄爆":   dict(payoffs="0-1 个", hook="★★★★★", note="降密蓄势，为下一章大爆发铺垫；⛔ 蓄爆期 ≤2 章"),
    "高潮":   dict(payoffs="2-3 个", hook="★★★★★", note="一次性回收 2-3 个伏笔 + 大爽点；每 30 章 1 次"),
}

# 写作硬标准（交付前逐条打勾）
HARD_STANDARDS = [
    "字数 1800–2600 字",
    "前 300 字内有新信息或新动作",
    "每 300 字有一次「新信息 / 新动作 / 新情绪」",
    "本章至少 1 个爽点触发",
    "章末钩子强度 ≥ ★★★",
    "对话单句 ≤ 30 字",
    "无一段纯描写超过 200 字",
    "已过人类质感改造（无 ≥3 项 AI 味指纹）",
]

# 反 AI 味提醒
AI_REMINDERS = [
    "句式要参差：长句 3 个必跟 1 个短句",
    "段落长短交替：禁止连续 3 段等长",
    "对话带个体腔调：每个主要角色一个口癖",
    "具体化描写：不写「他很生气」，写「他把杯子捏得咯咯响」",
    "情绪要跳：本章至少 1 次情绪反转",
]


def parse_range(s):
    if "-" in s:
        a, b = s.split("-", 1)
        return list(range(int(a), int(b) + 1))
    return [int(s)]


def forge_one(num, args):
    t = TYPE_SPEC.get(args.type, TYPE_SPEC["常规"])
    L = ["## 第 %d 章 写作单%s" % (num, ("（%s）" % args.type) if args.type else ""), ""]
    L.append("- **赛道**：%s" % (args.track or "未指定"))
    L.append("- **目标字数**：%s 字" % (args.words or 2200))
    L.append("- **爽点要求**：%s" % t["payoffs"])
    L.append("- **钩子要求**：%s" % t["hook"])
    L.append("- **章节定位**：%s" % t["note"])
    if args.hook and num == (parse_range(args.range or str(args.chapter or 1))[0]):
        L.append("- **本章核心钩子**：%s" % args.hook)
    L.append("")
    L.append("### 三幕七格结构（逐格填充）")
    L.append("")
    L.append("| 格 | 名称 | 写作提示 | 你的内容 |")
    L.append("|---|---|---|---|")
    for name, tip in SEVEN_CELLS:
        L.append("| | %s | %s | |" % (name, tip))
    L.append("")
    L.append("### 交付前硬标准自检")
    L.append("")
    for s in HARD_STANDARDS:
        L.append("- [ ] %s" % s)
    L.append("")
    L.append("### 反 AI 味提醒")
    L.append("")
    for s in AI_REMINDERS:
        L.append("- %s" % s)
    L.append("")
    return "\n".join(L)


def cmd_forge(args):
    if args.batch:
        nums = parse_range(args.batch)
    elif args.range:
        nums = parse_range(args.range)
    elif args.chapter:
        nums = parse_range(str(args.chapter))
    else:
        nums = [1]
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    header = ["# 番茄爆款小说 · 章节写作单", "",
              "- 生成时间：%s" % now,
              "- 赛道：%s" % (args.track or "未指定"),
              "- 章节范围：%s" % ("、".join("第%d章" % n for n in nums) if len(nums) <= 5
                                 else "第%d-%d章（共 %d 章）" % (nums[0], nums[-1], len(nums))),
              "- 卷次：%s" % (args.volume or "—"),
              "",
              "> 用法：逐格填充 → 写正文 → 跑 `quality_selfcheck.py` + `rhythm_analyzer.py` + `hook_density.py` → 不达标重写。",
              ""]
    body = [forge_one(n, args) for n in nums]
    text = "\n".join(header) + "\n".join(body)

    if args.report:
        with open(args.report, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
        print("[OK] 写作单已落盘：%s（%d 章）" % (os.path.abspath(args.report), len(nums)))
    else:
        print(text)
    print()
    print("=" * 62)
    print("章节生产流水线（五步）")
    print("=" * 62)
    print("1. 填七格结构 → 2. 写正文 → 3. 自查硬标准 8 条")
    print("4. 跑质检三连：")
    print("   python quality_selfcheck.py --file 稿件.md --prompt-out 优化提示词.md")
    print("   python rhythm_analyzer.py --file 稿件.md --curve")
    print("   python hook_density.py --file 稿件.md")
    print("5. 不达标 → 按优化提示词重写 → 重跑质检")
    return 0


def main():
    p = argparse.ArgumentParser(description="番茄爆款小说专家 · 章节生产脚手架")
    p.add_argument("--chapter", type=int, help="单章编号")
    p.add_argument("--range", help="章节范围，如 1-3")
    p.add_argument("--batch", help="批量，如 1-30")
    p.add_argument("--track", help="赛道")
    p.add_argument("--type", choices=list(TYPE_SPEC.keys()), default="常规", help="章节类型")
    p.add_argument("--words", type=int, default=2200, help="目标字数")
    p.add_argument("--hook", help="本章核心钩子（用于首章）")
    p.add_argument("--volume", help="卷次")
    p.add_argument("--report", nargs="?", const="写作单.md", help="输出路径")
    args = p.parse_args()
    return cmd_forge(args)


if __name__ == "__main__":
    sys.exit(main())
