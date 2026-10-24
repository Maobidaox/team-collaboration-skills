#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
hook_density.py — 番茄爆款小说专家 · 钩子密度与断点扫描器（纯标准库）

扫描小说稿件的"钩子/爽点/断点"密度，逐章打分，输出可直接执行的补钩清单。

用法：
  python hook_density.py --file 稿件.md
  python hook_density.py --file 稿件.md --mode 开局      # 只扫前 3 章（留存生死期）
  python hook_density.py --file 稿件.md --mode 全篇
  python hook_density.py --file 稿件.md --report 钩子体检报告.md
  python hook_density.py --list-types                     # 查看钩子类型表
  python hook_density.py --text "最后一段正文..."          # 直接分析一段文本

判定口径（2026-09）：
  章末钩子强度 ≥ ★★★ ｜ 每章爽点 ≥1（开篇期 ≥2）｜ 连续 2 章无爽点 = 红线
"""

import argparse
import os
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

# ============ 钩子类型表（强度分级） ============
HOOK_TYPES = [
    ("★★★★★", "生死悬念", ["死了", "喘不上气", "刀", "血", "倒计时", "最后一秒", "来不及"]),
    ("★★★★★", "身份揭示", ["其实我是", "真名", "马甲", "身份", "原来他", "并不是"]),
    ("★★★★", "反转", ["然而", "没想到", "却", "反而", "结果", "真相是"]),
    ("★★★★", "危机逼近", ["脚步声", "越来越近", "正在靠近", "门外", "背后", "回头"]),
    ("★★★★", "新目标/新任务", ["下一个", "目标是", "必须", "只剩", "唯一的机会"]),
    ("★★★", "疑问悬念", ["？", "为什么", "是谁", "怎么", "难道"]),
    ("★★★", "情绪悬念", ["沉默", "愣住", "脸色", "手指", "发抖", "冷汗"]),
    ("★★★", "信息缺口", ["他不知道的是", "与此同时", "另一边", "而在", "没人知道"]),
    ("★★", "预告式", ["即将", "接下来", "马上", "就要"]),
]

# ============ 爽点类型关键词 ============
PAYOFF_KEYWORDS = [
    "打脸", "跪", "震惊", "全场", "目瞪口呆", "不敢置信", "傻眼", "真香",
    "逆袭", "翻身", "无敌", "碾压", "吊打", "反杀", "翻盘",
    "原来", "马甲", "真实身份", "隐藏", "大佬",
    "突破", "进阶", "晋升", "觉醒", "顿悟", "变强",
    "守护", "救下", "护住", "挡在",
    "掌声", "欢呼", "崇拜", "羡慕", "追捧",
    "冷笑", "淡淡道", "轻描淡写", "随手",
]

# ============ AI 味指纹（用于辅助判断） ============
AI_PATTERNS = [
    (r"然而[，,]", "模板转折词「然而」"),
    (r"不禁", "模板词「不禁」"),
    (r"眼中闪过一丝", "模板描写「眼中闪过一丝」"),
    (r"嘴角勾起", "模板描写「嘴角勾起一抹」"),
    (r"空气仿佛凝固", "模板句「空气仿佛凝固」"),
    (r"心中五味杂陈", "模板句「五味杂陈」"),
    (r"深深地看", "模板动作「深深看了一眼」"),
    (r"深吸一口气", "高频动作「深吸一口气」"),
    (r"瞳孔骤缩", "模板反应「瞳孔骤缩」"),
    (r"如同|宛如|仿佛", "堆砌比喻"),
]


def split_chapters(text):
    """按常见章节标题切分。"""
    pat = re.compile(r"(?m)^\s*(第\s*[0-9一二三四五六七八九十百千零两]+\s*章[^\n]*)$")
    idx = [(m.start(), m.group(1).strip()) for m in pat.finditer(text)]
    if not idx:
        pat2 = re.compile(r"(?m)^\s*(#{1,3}\s*第[^\n]*章[^\n]*)$")
        idx = [(m.start(), m.group(1).strip()) for m in pat2.finditer(text)]
    if not idx:
        return [("（全文）", text)]
    out = []
    for i, (pos, title) in enumerate(idx):
        end = idx[i + 1][0] if i + 1 < len(idx) else len(text)
        out.append((title, text[pos:end]))
    return out


def strip_md(s):
    s = re.sub(r"[#*>`_~\-]{1,}", " ", s)
    s = re.sub(r"\s+", " ", s)
    return s.strip()


def hook_strength(tail):
    """给章末文本打钩子强度（0-5 星 + 类型）。"""
    best = 0
    best_type = "无"
    for stars, name, kws in HOOK_TYPES:
        n = int(stars.count("★"))
        for kw in kws:
            if kw in tail:
                if n > best:
                    best, best_type = n, name
                break
    return best, best_type


def count_payoffs(body):
    n = 0
    hits = []
    for kw in PAYOFF_KEYWORDS:
        c = body.count(kw)
        if c:
            n += c
            hits.append("%s×%d" % (kw, c))
    return n, hits


def analyze_chapter(title, body):
    body_clean = strip_md(body)
    words = len(re.sub(r"\s", "", body_clean))
    tail = body_clean[-200:] if len(body_clean) > 200 else body_clean
    stars, htype = hook_strength(tail)
    pay_n, pay_hits = count_payoffs(body_clean)
    paras = [p for p in re.split(r"\n\s*\n", body) if p.strip()]
    par_lens = [len(strip_md(p)) for p in paras] or [0]
    longest = max(par_lens)
    dial = len(re.findall(r"[“\"][^”\"]{1,60}[”\"]", body))
    ai_hits = []
    for pat, desc in AI_PATTERNS:
        if re.search(pat, body_clean):
            ai_hits.append(desc)
    return dict(title=title, words=words, hook=stars, hook_type=htype,
                payoffs=pay_n, payoff_hits=pay_hits, paras=len(paras),
                longest_par=longest, dialogs=dial, ai=ai_hits)


def grade(rec, opening=False):
    """0-10 分。"""
    s = 0.0
    s += min(rec["hook"], 5) * 1.4              # 钩子最多 7 分
    target_pay = 2 if opening else 1
    s += min(rec["payoffs"] / max(target_pay, 1), 2) * 1.0   # 爽点最多 2 分
    if rec["longest_par"] <= 200:
        s += 0.5
    if rec["dialogs"] >= 3:
        s += 0.5
    s -= 0.3 * len(rec["ai"])
    return max(0.0, min(10.0, s))


def cmd_list_types(args):
    print("=" * 70)
    print("章末钩子类型表（强度分级）")
    print("=" * 70)
    for stars, name, kws in HOOK_TYPES:
        print("%s  %-12s  关键词：%s" % (stars, name, "、".join(kws[:6])))
    print("-" * 70)
    print("判定线：章末钩子强度 ≥ ★★★；连续 2 章无爽点 = 红线。")
    return 0


def run(text, args, source_name):
    chapters = split_chapters(text)
    if args.mode == "开局":
        chapters = chapters[:3]
    opening = args.mode == "开局"
    now = __import__("datetime").datetime.now().strftime("%Y-%m-%d %H:%M")

    L = ["# 钩子密度体检报告", "",
         "- 生成时间：%s" % now, "- 来源：%s" % source_name,
         "- 模式：%s" % args.mode, "- 章节数：%d" % len(chapters), "",
         "## 一、逐章诊断", "",
         "| 章节 | 字数 | 章末钩子 | 钩子类型 | 爽点数 | 最长段 | 对话数 | 得分 | 判定 |",
         "|---|---|---|---|---|---|---|---|---|"]

    print("=" * 88)
    print("钩子密度体检（口径 2026-09）  来源：%s" % source_name)
    print("=" * 88)
    print("%-22s %-7s %-9s %-10s %-7s %-7s %-7s %-6s %s"
          % ("章节", "字数", "章末钩子", "类型", "爽点", "最长段", "对话", "得分", "判定"))
    print("-" * 88)

    recs = []
    for title, body in chapters:
        rec = analyze_chapter(title, body)
        sc = grade(rec, opening)
        rec["score"] = sc
        recs.append(rec)
        if sc >= 7.5:
            v = "✅ 优"
        elif sc >= 6:
            v = "⚠️ 及格"
        else:
            v = "🔴 需改"
        print("%-22s %-7d %-9s %-10s %-7d %-7d %-7d %-6.1f %s"
              % (title[:20], rec["words"], "★" * rec["hook"] or "无", rec["hook_type"][:8],
                 rec["payoffs"], rec["longest_par"], rec["dialogs"], sc, v))
        L.append("| %s | %d | %s | %s | %d | %d | %d | %.1f | %s |"
                 % (title, rec["words"], "★" * rec["hook"] or "无", rec["hook_type"],
                    rec["payoffs"], rec["longest_par"], rec["dialogs"], sc, v))

    avg = sum(r["score"] for r in recs) / max(len(recs), 1)
    weak = [r for r in recs if r["score"] < 6]
    no_hook = [r for r in recs if r["hook"] < 3]
    flat = []
    for i in range(len(recs) - 1):
        if recs[i]["payoffs"] == 0 and recs[i + 1]["payoffs"] == 0:
            flat.append(recs[i]["title"])
    ai_all = {}
    for r in recs:
        for a in r["ai"]:
            ai_all[a] = ai_all.get(a, 0) + 1

    print("-" * 88)
    print("平均得分：%.1f / 10　｜　需改章节：%d　｜　钩子不足(＜★★★)：%d" % (avg, len(weak), len(no_hook)))
    if flat:
        print("🔴 连续无爽点段落出现在：%s" % "、".join(flat))
    print()

    L += ["", "## 二、汇总", "",
          "- **平均得分**：%.1f / 10" % avg,
          "- **需改章节**：%d 章" % len(weak),
          "- **章末钩子不足（＜★★★）**：%d 章" % len(no_hook),
          "- **连续无爽点**：%s" % ("、".join(flat) if flat else "无"), ""]

    print("补钩清单（可直接执行）：")
    L += ["## 三、补钩清单（可直接执行）", ""]
    if not weak and not no_hook:
        print("  ✅ 全篇钩子与爽点密度达标")
        L.append("✅ 全篇钩子与爽点密度达标")
    for r in (weak or no_hook)[:10]:
        print("  · %s：钩子 ★%d（%s），爽点 %d → 章末补一个 ★★★★ 级钩子" % (r["title"][:18], r["hook"], r["hook_type"], r["payoffs"]))
        L.append("- **%s**：钩子 ★%d（%s），爽点 %d → 章末补一个 ★★★★ 级钩子（参照 references/13 号）"
                 % (r["title"], r["hook"], r["hook_type"], r["payoffs"]))
    L.append("")

    if ai_all:
        print("\nAI 味提示（建议同步跑 ai_flavor_remover.py）：")
        for a, c in sorted(ai_all.items(), key=lambda x: -x[1]):
            print("  · %s（出现 %d 章）" % (a, c))
        L += ["## 四、AI 味提示", ""]
        for a, c in sorted(ai_all.items(), key=lambda x: -x[1]):
            L.append("- %s（%d 章）" % (a, c))
        L.append("")

    L += ["## 五、行动建议", "",
          "1. 钩子 < ★★★ 的章节 → 按 references/13 号补章末断点；",
          "2. 连续无爽点 → 按 references/45 号切「提速档」；",
          "3. AI 味命中 → 跑 `python ai_flavor_remover.py --file 稿件.md --suggest`；",
          "4. 改完重跑本脚本，直到平均分 ≥7.5。", "",
          "> **免责**：本报告为创作辅助工具输出，不替代平台数据。"]
    out = args.report or "钩子体检报告.md"
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(L) + "\n")
    print("\n[OK] 报告已落盘：%s" % os.path.abspath(out))
    return 0


def main():
    p = argparse.ArgumentParser(description="番茄爆款小说专家 · 钩子密度扫描器")
    p.add_argument("--file", help="稿件文件（.md / .txt）")
    p.add_argument("--text", help="直接分析一段文本")
    p.add_argument("--mode", choices=["开局", "全篇"], default="全篇")
    p.add_argument("--report", nargs="?", const="钩子体检报告.md", help="输出报告路径")
    p.add_argument("--list-types", action="store_true", help="查看钩子类型表")
    args = p.parse_args()

    if args.list_types:
        return cmd_list_types(args)
    if args.text:
        return run(args.text, args, "（命令行文本）")
    if not args.file:
        p.print_help()
        return 0
    if not os.path.exists(args.file):
        print("[ERR] 文件不存在：%s" % args.file)
        return 1
    with open(args.file, "r", encoding="utf-8", errors="ignore") as f:
        text = f.read()
    return run(text, args, os.path.basename(args.file))


if __name__ == "__main__":
    sys.exit(main())
