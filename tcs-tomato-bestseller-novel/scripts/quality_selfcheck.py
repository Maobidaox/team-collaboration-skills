#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
番茄爆款小说专家 · 稿件智能质检 + 优化提示词自动生成
------------------------------------------------------
纯标准库实现，零第三方依赖，跨平台。

用途（用户需求「智能质量评估和建立脚本自动优化功能」）：
  专家每次生成正文后运行本脚本，脚本对稿件做多维质检，
  判定质量不达标时**自动生成一段可直接投喂大模型的优化提示词**，
  专家按该提示词重写，直到达标再交付用户。

用法：
  python quality_selfcheck.py 稿件.md                # 质检并输出结果
  python quality_selfcheck.py 稿件.md --json          # 输出 JSON
  python quality_selfcheck.py 稿件.md --prompt-out opt.txt  # 单独导出优化提示词
  python quality_selfcheck.py 稿件.md --threshold 85  # 自定义达标线（默认 85）

退出码：0 = 达标；1 = 未达标（需按优化提示词重写）；2 = 文件错误
"""

import argparse
import json
import os
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

# ---------------- 检测规则 ----------------

# AI 味指纹（参考 references/11）
AI_PATTERNS = [
    ("三段式排比", r"不是[^。]{2,20}[，、][^。]{2,20}[，、]?(而是|更是)[^。]{2,20}"),
    ("强行升华", r"(这一刻|此刻|终于明白|终于懂得|恍然大悟)[^。]{0,30}(意义|道理|真相|真谛)"),
    ("抽象形容词堆砌", r"(深邃|莫测|莫名|某种|仿佛|似乎|宛如)(的)?[^。]{0,10}(气息|眼神|力量|感觉|氛围)"),
    ("无信息过渡", r"(与此同时|另一方面|综上所述|总的来说|不仅仅是)[，、]"),
    ("章末总结", r"(这就是|这便是|由此可见|不得不说)[^。]{0,20}。\s*$"),
    ("万能比喻", r"(如潮水般|如猛兽般|像一头蛰伏|如梦魇般|铺天盖地般)"),
    ("情绪贴标签", r"(愤怒|恐惧|悲伤|激动|震惊|紧张)(地|得)(说|喊|叫|问|颤抖)"),
    ("论文式长句", r"[^。！？；]{60,}[，、][^。！？；]{40,}。"),
]

# 章末钩子信号
HOOK_SIGNALS = [
    (r"[？?]\s*$", "疑问句收尾"),
    (r"[…\.]{3,}\s*$", "省略号留白"),
    (r"[！!]\s*$", "感叹收尾"),
    (r"(突然|忽然|猛地|就在这时|下一秒|紧接着)[^。]{0,25}。\s*$", "突发事件"),
    (r"(不知道|没想到|然而|但是|却)[^。]{0,25}。\s*$", "转折收尾"),
]

GOOD_HOOK_WORDS = ["突然", "忽然", "就在这时", "下一秒", "猛地", "却", "然而", "但是", "没想到"]

# 目标值
TARGET = {
    "min_chars": 2000,        # 单章最少字数
    "max_chars": 6000,        # 单章最多字数
    "dialog_ratio_min": 0.20,  # 对话占比下限
    "dialog_ratio_max": 0.55,  # 对话占比上限
    "max_long_para_ratio": 0.15,  # 超长段落占比上限
    "max_ai_hits": 3,          # AI 味命中上限
    "payoff_density": 800,     # 每 N 字至少一个微爽点/反转
}

PAYOFF_WORDS = ["反", "却", "没想", "忽然", "突然", "竟然", "居然", "原来", "露出", "冷笑", "震惊", "愣", "傻", "脸色", "破防", "打脸", "反转"]


def count_chinese(text):
    return len(re.findall(r"[\u4e00-\u9fa5]", text))


def split_paragraphs(text):
    return [p.strip() for p in re.split(r"\n\s*\n|\n", text) if p.strip()]


def count_dialogue(text):
    """统计中文引号内的字符数占比。"""
    quotes = re.findall(r"[“\"]([^”\"]{1,200})[”\"]", text)
    dlg = sum(len(q) for q in quotes)
    total = count_chinese(text)
    return (dlg / total) if total else 0.0, len(quotes)


def analyze(text, threshold=85):
    paras = split_paragraphs(text)
    total = count_chinese(text)
    dialog_ratio, dialog_count = count_dialogue(text)

    # AI 味
    ai_hits = []
    for name, pat in AI_PATTERNS:
        found = re.findall(pat, text)
        if found:
            ai_hits.append((name, len(found)))
    ai_total = sum(n for _, n in ai_hits)

    # 段落长度
    long_paras = [p for p in paras if count_chinese(p) > 120]
    long_ratio = (len(long_paras) / len(paras)) if paras else 0.0

    # 章末钩子
    tail = text.strip()[-80:] if text.strip() else ""
    hook_found = []
    for pat, desc in HOOK_SIGNALS:
        if re.search(pat, tail, re.M):
            hook_found.append(desc)
    has_hook = bool(hook_found)

    # 爽点密度
    payoff_hits = sum(text.count(w) for w in PAYOFF_WORDS)
    per_payoff = (total / payoff_hits) if payoff_hits else float("inf")

    # -------- 打分（100 分制）--------
    score = 100
    issues = []

    if total < TARGET["min_chars"]:
        score -= 15
        issues.append("字数不足：%d 字（单章建议 %d-%d 字）" % (total, TARGET["min_chars"], TARGET["max_chars"]))
    elif total > TARGET["max_chars"] * 1.5:
        issues.append("单章过长：%d 字，建议拆分（移动端阅读体验）" % total)

    if dialog_ratio < TARGET["dialog_ratio_min"]:
        score -= 15
        issues.append("对话占比偏低：%.1f%%（建议 30%%-45%%，下限 20%%），章节显得干巴" % (dialog_ratio * 100))
    elif dialog_ratio > TARGET["dialog_ratio_max"]:
        score -= 8
        issues.append("对话占比偏高：%.1f%%（上限 55%%），缺少叙事推进" % (dialog_ratio * 100))

    if ai_total > TARGET["max_ai_hits"]:
        score -= min(30, (ai_total - TARGET["max_ai_hits"]) * 4)
        issues.append("AI 味命中 %d 处，超出上限 %d 处" % (ai_total, TARGET["max_ai_hits"]))

    if long_ratio > TARGET["max_long_para_ratio"]:
        score -= 10
        issues.append("超长段落占比 %.1f%%（上限 15%%），移动端阅读压迫感强" % (long_ratio * 100))

    if not has_hook:
        score -= 20
        issues.append("章末未检测到钩子——追更率杀手，必须在最后 100 字内落钩")

    if per_payoff > TARGET["payoff_density"]:
        score -= 10
        issues.append("微爽点/反转密度不足：平均每 %.0f 字才一个（目标 ≤%d 字一个）"
                      % (min(per_payoff, 99999), TARGET["payoff_density"]))

    score = max(0, min(100, score))
    passed = score >= threshold

    return {
        "chars": total,
        "paragraphs": len(paras),
        "dialog_ratio": round(dialog_ratio, 4),
        "dialog_count": dialog_count,
        "long_para_ratio": round(long_ratio, 4),
        "ai_hits": ai_hits,
        "ai_total": ai_total,
        "has_hook": has_hook,
        "hook_types": hook_found,
        "payoff_interval": (round(per_payoff) if per_payoff != float("inf") else None),
        "score": score,
        "threshold": threshold,
        "passed": passed,
        "issues": issues,
    }


def build_prompt(result, src_name):
    """生成可直接投喂大模型的优化提示词（核心能力：自动优化）。"""
    lines = []
    lines.append("【番茄小说稿件优化提示词 · 由 quality_selfcheck.py 自动生成】")
    lines.append("")
    lines.append("目标：把《%s》修订为番茄小说平台霸榜级标准（达标线 %d 分，当前 %d 分）。" %
                 (src_name, result["threshold"], result["score"]))
    lines.append("")
    lines.append("一、必须修复的问题（按优先级）：")
    if result["issues"]:
        for i, s in enumerate(result["issues"], 1):
            lines.append("  %d. %s" % (i, s))
    else:
        lines.append("  无硬性缺陷，做最后一轮质感打磨即可。")
    lines.append("")
    if result["ai_hits"]:
        lines.append("二、AI 味命中明细（逐项改掉，禁止保留）：")
        for name, n in result["ai_hits"]:
            lines.append("  - %s：%d 处 —— 按《11-去AI味与人类质感改造》对应改法重写" % (name, n))
        lines.append("")
    lines.append("三、重写要求：")
    lines.append("  1. 开篇：前 200 字必须出冲突，禁止环境铺垫、禁止回忆杀。")
    lines.append("  2. 节奏：每 800 字至少一个微爽点/反转/信息差；每章至少 2 个钩子。")
    lines.append("  3. 章末：最后 100 字内必须落一个强钩子（危机/反转/身份/倒计时/情感/悬念/利益 七选一）。")
    lines.append("  4. 对话：占比 30%-45%，遮住说话人名字也能认出是谁；去掉'他愤怒地说'式情绪标签，改用动作与生理反应。")
    lines.append("  5. 去水：删掉任何'删掉读者也看得懂'的段落；环境描写全章 ≤150 字。")
    lines.append("  6. 人类质感：用具体数字与名词替代抽象形容词；长段拆短，长短句交错。")
    lines.append("  7. 合规：涉亲密/暴力情节一律留白，不写器官与过程；不写违规内容。")
    lines.append("")
    lines.append("四、交付前复核：")
    lines.append("  改完再次运行 python quality_selfcheck.py <文件>，须达到 %d 分以上方可交付用户。" % result["threshold"])
    lines.append("")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description="番茄小说稿件智能质检 + 优化提示词生成")
    ap.add_argument("file", help="待质检的 Markdown 稿件路径")
    ap.add_argument("--json", action="store_true", help="以 JSON 输出")
    ap.add_argument("--prompt-out", help="把优化提示词单独写入指定文件")
    ap.add_argument("--threshold", type=int, default=85, help="达标线（默认 85）")
    args = ap.parse_args()

    if not os.path.exists(args.file):
        print("[错误] 文件不存在：%s" % args.file)
        sys.exit(2)

    with open(args.file, "r", encoding="utf-8", errors="ignore") as f:
        text = f.read()

    result = analyze(text, args.threshold)
    prompt = build_prompt(result, os.path.basename(args.file))

    if args.json:
        print(json.dumps({"result": result, "optimization_prompt": prompt},
                         ensure_ascii=False, indent=2))
    else:
        print("=" * 62)
        print("番茄爆款小说专家 · 稿件智能质检报告")
        print("=" * 62)
        print("文件         : %s" % os.path.abspath(args.file))
        print("中文字数     : %d" % result["chars"])
        print("段落数       : %d" % result["paragraphs"])
        print("对话占比     : %.1f%%（对话段 %d 处）" % (result["dialog_ratio"] * 100, result["dialog_count"]))
        print("超长段落占比 : %.1f%%" % (result["long_para_ratio"] * 100))
        print("AI 味命中    : %d 处" % result["ai_total"])
        if result["ai_hits"]:
            for name, n in result["ai_hits"]:
                print("               - %s × %d" % (name, n))
        print("章末钩子     : %s %s" % ("有" if result["has_hook"] else "无",
                                        result["hook_types"] if result["hook_types"] else ""))
        print("爽点间隔     : %s 字/个" % (result["payoff_interval"] or "未检出"))
        print("-" * 62)
        print("综合得分     : %d / 100（达标线 %d）" % (result["score"], result["threshold"]))
        print("判定         : %s" % ("✅ 达标，可交付" if result["passed"] else "❌ 未达标，需按优化提示词重写"))
        if result["issues"]:
            print("-" * 62)
            print("问题清单：")
            for s in result["issues"]:
                print("  · %s" % s)
        print("=" * 62)
        if not result["passed"]:
            print("\n【自动生成的优化提示词】（可直接投喂大模型重写）\n")
            print(prompt)

    if args.prompt_out:
        with open(args.prompt_out, "w", encoding="utf-8") as f:
            f.write(prompt)
        print("\n[已导出] 优化提示词 → %s" % os.path.abspath(args.prompt_out))

    sys.exit(0 if result["passed"] else 1)


if __name__ == "__main__":
    main()
