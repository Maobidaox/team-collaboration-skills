#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ip_adaptation.py — 番茄爆款小说专家 · IP 改编适配评估器（纯标准库）

评估一部书稿对「短剧 / 漫剧 / 有声书」三种改编形态的适配度，输出评分与改写建议。

用法：
  python ip_adaptation.py --file 稿件.md --mode 短剧
  python ip_adaptation.py --file 稿件.md --mode 漫剧
  python ip_adaptation.py --file 稿件.md --mode 有声
  python ip_adaptation.py --file 稿件.md --mode all --report 改编适配报告.md
  python ip_adaptation.py --list-modes

评分维度（0-10）：
  短剧：场景可视 / 节奏适配 / 台词质感 / 人物清晰 / 情绪密度
  漫剧：设定奇观 / 画面语言 / 爽点可视 / 人物形象 / 分镜友好
  有声：对话驱动 / 角色口癖 / 信息复述 / 场景交代 / 情节密度
"""

import argparse
import os
import re
import sys
from datetime import datetime

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

VISUAL_SCENES = ["婚礼", "法庭", "拍卖", "病房", "会议室", "宴会", "广场", "天台",
                 "巷子", "教室", "办公室", "餐厅", "车内", "门口", "主席台"]
ACTION_VERBS = ["站起", "转身", "推门", "甩", "抓", "撕", "跪", "扑", "挡", "举",
                "递", "扔", "拽", "踢", "拍", "摔", "指", "拉"]
CLIMAX_WORDS = ["震惊", "全场", "哗然", "死寂", "掌声", "倒吸", "鸦雀无声", "石化",
                "沸腾", "炸开", "屏住呼吸"]
SPECTACLE_WORDS = ["光芒", "爆裂", "化作", "凝结", "虚影", "符文", "光柱", "炸裂",
                   "碎成", "燃烧", "浮现", "扭曲", "蔓延", "异变", "显形", "降临"]
FORMULAIC = ["然而", "不禁", "仿佛", "宛如", "眼中闪过一丝", "嘴角勾起", "空气凝固"]


def read_text(p):
    with open(p, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


def clean(s):
    return re.sub(r"\s+", " ", re.sub(r"[#*>`_~]", " ", s))


def split_chapters(text):
    pat = re.compile(r"(?m)^\s*(第\s*[0-9一二三四五六七八九十百千零两]+\s*章[^\n]*)$")
    idx = [(m.start(), m.group(1).strip()) for m in pat.finditer(text)]
    if not idx:
        return [("（全文）", text)]
    out = []
    for i, (pos, t) in enumerate(idx):
        end = idx[i + 1][0] if i + 1 < len(idx) else len(text)
        out.append((t, text[pos:end]))
    return out


def score_duanju(text, chapters):
    c = clean(text)
    n = len(chapters)
    scene_hits = sum(c.count(w) for w in VISUAL_SCENES)
    action_hits = sum(c.count(w) for w in ACTION_VERBS)
    climax_hits = sum(c.count(w) for w in CLIMAX_WORDS)
    dialogs = len(re.findall(r"[“\"][^”\"]{1,80}[”\"]", c))
    short_lines = len([x for x in re.findall(r"[“\"]([^”\"]{1,80})[”\"]", c) if len(x) <= 30])
    total_lines = max(dialogs, 1)
    # 每 10 章一个大高潮
    climax_per10 = climax_hits / max(n / 10.0, 1)
    return {
        "场景可视": min(10, scene_hits / max(n, 1) * 3.0),
        "节奏适配": min(10, climax_per10 * 3.0),
        "台词质感": min(10, short_lines / total_lines * 12.0),
        "人物清晰": min(10, (dialogs / max(n, 1)) * 2.0),
        "情绪密度": min(10, (action_hits + climax_hits) / max(n, 1) * 1.5),
    }


def score_manju(text, chapters):
    c = clean(text)
    n = len(chapters)
    spec = sum(c.count(w) for w in SPECTACLE_WORDS)
    visual = sum(c.count(w) for w in VISUAL_SCENES)
    climax = sum(c.count(w) for w in CLIMAX_WORDS)
    body_desc = len(re.findall(r"[。！？]", c))
    return {
        "设定奇观": min(10, spec / max(n, 1) * 3.0),
        "画面语言": min(10, (visual + spec) / max(n, 1) * 2.0),
        "爽点可视": min(10, climax / max(n, 1) * 3.0),
        "人物形象": min(10, len(re.findall(r"[他她][^\s，。]{0,4}(穿|戴|拿着|握着)", c)) / max(n, 1) * 3.0),
        "分镜友好": min(10, body_desc / max(n, 1) * 0.6),
    }


def score_yousheng(text, chapters):
    c = clean(text)
    n = len(chapters)
    dialogs = re.findall(r"[“\"][^”\"]{1,80}[”\"]", c)
    with_name = len([d for d in dialogs if re.search(r"[哥姐叔姨爸妈老小]|[，,][^，,]{1,4}(说|道|问)", d)])
    total = max(len(dialogs), 1)
    paraphrase = len(re.findall(r"(也就是说|换句话说|也就是说|意思是|总之|简单说)", c))
    scene_lead = len(re.findall(r"(?m)^\s*[^。“”\n]{0,40}(走进|坐在|站在|回到|来到)", c))
    return {
        "对话驱动": min(10, len(dialogs) / max(n, 1) * 1.5),
        "角色口癖": min(10, with_name / total * 10.0),
        "信息复述": min(10, paraphrase / max(n, 1) * 5.0),
        "场景交代": min(10, scene_lead / max(n, 1) * 3.0),
        "情节密度": min(10, len(re.split(r"[。！？]", c)) / max(n, 1) * 0.3),
    }


SCORERS = {"短剧": score_duanju, "漫剧": score_manju, "有声": score_yousheng}

SUGGEST = {
    "短剧": [
        "增加「能直接拍」的场景（婚礼/法庭/拍卖会/病房），每卷 ≥3 个",
        "每 10 章安排 1 个大高潮（对应短剧一集爆点）",
        "压缩台词长度：单句 ≤30 字，去掉书面语",
        "让人物关系一句话能说清",
    ],
    "漫剧": [
        "强化「设定奇观」：给异能/规则一个可视化的表现形式",
        "多用可视化描写（光芒、异变、显形），少用心理活动",
        "爽点要有画面（境界突破/技能释放）",
        "给主要角色设计外形 / 标志物，便于美术设计",
    ],
    "有声": [
        "对话驱动剧情：把叙述改成对话",
        "给每个角色一个口癖（一听就知道是谁）",
        "关键信息复述一次（听漏了也能接上）",
        "每章开头交代「谁在哪干什么」",
    ],
}


def cmd_list_modes(args):
    print("=" * 66)
    print("IP 改编适配评估 · 三种模式")
    print("=" * 66)
    for m, dims in (("短剧", ["场景可视", "节奏适配", "台词质感", "人物清晰", "情绪密度"]),
                    ("漫剧", ["设定奇观", "画面语言", "爽点可视", "人物形象", "分镜友好"]),
                    ("有声", ["对话驱动", "角色口癖", "信息复述", "场景交代", "情节密度"])):
        print("%s：%s" % (m, " / ".join(dims)))
    print("-" * 66)
    print("用法：python ip_adaptation.py --file 稿件.md --mode 短剧")
    return 0


def run(text, modes, args, src):
    chapters = split_chapters(text)
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    L = ["# IP 改编适配评估报告", "", "- 生成时间：%s" % now, "- 来源：%s" % src,
         "- 章节数：%d" % len(chapters), ""]
    print("=" * 74)
    print("IP 改编适配评估（口径 2026-09）  来源：%s  章节：%d" % (src, len(chapters)))
    print("=" * 74)

    grade_map = []
    for mode in modes:
        dims = SCORERS[mode](text, chapters)
        avg = sum(dims.values()) / len(dims)
        g = "S（易改编）" if avg >= 8 else ("A（可改编）" if avg >= 6.5 else
             ("B（需改造）" if avg >= 5 else "C（不匹配）"))
        grade_map.append((mode, avg, g, dims))
        print("\n【%s】综合 %.1f / 10　评级：%s" % (mode, avg, g))
        print("-" * 74)
        for k, v in dims.items():
            bar = "█" * int(round(v)) + "░" * (10 - int(round(v)))
            print("  %-10s %-12s %.1f" % (k, bar, v))
        L += ["## %s · 综合 %.1f / 10（%s）" % (mode, avg, g), "",
              "| 维度 | 得分 | 条形 |", "|---|---|---|"]
        for k, v in dims.items():
            L.append("| %s | %.1f | %s |" % (k, v, "█" * int(round(v)) + "░" * (10 - int(round(v)))))
        L.append("")

        weak = [k for k, v in dims.items() if v < 6]
        if weak:
            L += ["**改写建议**：", ""]
            for s in SUGGEST.get(mode, []):
                L.append("- %s" % s)
            L.append("")

    best = max(grade_map, key=lambda x: x[1])
    print("\n" + "=" * 74)
    print("最优改编形态：%s（%.1f 分）" % (best[0], best[1]))
    L += ["## 结论", "", "- **最优改编形态**：%s（%.1f 分）" % (best[0], best[1]),
          "- 详见 references/36 号（短剧）、37 号（漫剧/有声）、38 号（版权分账）", "",
          "> **免责**：改编评估为创作辅助参考，具体授权条件以番茄官方活动页与正式合同为准。"]

    out = args.report or "改编适配报告.md"
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(L) + "\n")
    print("[OK] 报告已落盘：%s" % os.path.abspath(out))
    return 0


def main():
    p = argparse.ArgumentParser(description="番茄爆款小说专家 · IP 改编适配评估器")
    p.add_argument("--file", help="稿件文件")
    p.add_argument("--mode", choices=["短剧", "漫剧", "有声", "all"], default="all")
    p.add_argument("--report", nargs="?", const="改编适配报告.md")
    p.add_argument("--list-modes", action="store_true")
    args = p.parse_args()
    if args.list_modes:
        return cmd_list_modes(args)
    if not args.file:
        p.print_help()
        return 0
    if not os.path.exists(args.file):
        print("[ERR] 文件不存在：%s" % args.file)
        return 1
    modes = ["短剧", "漫剧", "有声"] if args.mode == "all" else [args.mode]
    return run(read_text(args.file), modes, args, os.path.basename(args.file))


if __name__ == "__main__":
    sys.exit(main())
