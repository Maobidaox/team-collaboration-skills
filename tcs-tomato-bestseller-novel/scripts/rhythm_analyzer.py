#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""节奏曲线诊断器 —— 番茄小说节奏质量诊断工具

纯标准库实现，零第三方依赖。

诊断六个维度：
  1. 段落长度分布（是否有"AI 长段病"）
  2. 对话占比（番茄正文健康区间 30%-45%）
  3. 句长方差（句子是否过于整齐 = AI 味）
  4. 章节节奏曲线（每章张力值，看起伏是否单调）
  5. 章末钩子强度（最后 100 字是否能拉追更）
  6. 重复句式检测（机械复用）

用法：
    python rhythm_analyzer.py 稿件.md
    python rhythm_analyzer.py 书稿目录 --recursive
    python rhythm_analyzer.py 稿件.md --json
    python rhythm_analyzer.py 稿件.md --curve          # 只输出节奏曲线
    python rhythm_analyzer.py 稿件.md --top 15         # 问题条数上限
"""
import argparse
import json
import os
import re
import sys

# ---------------------------------------------------------------- 基础工具

CJK = r"\u4e00-\u9fff"
SENT_SPLIT = re.compile(r"[。！？!?…；;]+")
DIALOG_PAT = re.compile(r"[「『“\"][^」』”\"]{2,}[」』”\"]")
CHAPTER_PAT = re.compile(r"^\s{0,3}#{1,4}\s*(.+)$", re.M)

# 钩子信号词（章末出现，说明有意留悬念）
HOOK_WORDS = [
    "突然", "忽然", "却", "竟然", "居然", "怎么会", "为什么", "难道",
    "不可能", "不", "等等", "等等…", "就在这时", "下一刻", "下一秒",
    "他不知道的是", "她不知道的是", "没有人知道", "更可怕", "真正的",
    "与此同时", "然而", "只是", "但是", "可", "直到",
]
# AI 味句式模板
AI_PATTERNS = [
    (r"不是[^，。]{1,12}，而是[^，。]{1,12}(，更是[^，。]{1,12})?", "三段式排比（不是…而是…更是）"),
    (r"仿佛[^，。]{0,16}(一般|一样|似的)", "抽象比喻堆砌（仿佛…一般）"),
    (r"这一刻[，,][^。]{0,24}明白", "总结性升华（这一刻…明白）"),
    (r"这一刻[，,][^。]{0,24}懂", "总结性升华（这一刻…懂）"),
    (r"(深邃|莫测|莫名|意味不明|难以言喻|无法言说)", "抽象形容词（深邃/莫测/莫名）"),
    (r"空气(仿佛)?(都)?(凝固|安静)了", "陈词滥调（空气凝固）"),
    (r"时间(仿佛)?(都)?(静止|停止)了", "陈词滥调（时间静止）"),
    (r"(眼神|目光)(中|里)(透露出|闪过一丝|藏着)", "情绪贴标签（眼神中透露出）"),
    (r"与此同时[，,]", "无信息量过渡（与此同时）"),
    (r"另一方面[，,]", "无信息量过渡（另一方面）"),
    (r"综上所述", "议论体收尾（综上所述）"),
    (r"(不禁|不由自主地)(感到|觉得)", "情绪贴标签（不禁感到）"),
]


def read_text(path):
    for enc in ("utf-8", "utf-8-sig", "gbk", "gb18030"):
        try:
            with open(path, "r", encoding=enc) as f:
                return f.read()
        except (UnicodeDecodeError, LookupError):
            continue
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


def cjk_count(s):
    return len(re.findall(r"[%s]" % CJK, s))


def split_chapters(text):
    """按 Markdown 标题切章；无标题则整篇作一章。"""
    lines = text.splitlines()
    chapters, cur_title, cur_buf = [], None, []
    for ln in lines:
        m = CHAPTER_PAT.match(ln)
        if m and m.group(1).strip():
            if cur_title is not None or cur_buf:
                chapters.append((cur_title or "(开篇)", "\n".join(cur_buf)))
            cur_title, cur_buf = m.group(1).strip(), []
        else:
            cur_buf.append(ln)
    if cur_title is not None or cur_buf:
        chapters.append((cur_title or "(正文)", "\n".join(cur_buf)))
    return [(t, b) for t, b in chapters if cjk_count(b) >= 50] or [("(正文)", text)]


def paragraphs(body):
    out = []
    for raw in re.split(r"\n\s*\n", body):
        p = raw.strip()
        if p and not p.startswith("#") and not p.startswith(">"):
            out.append(p)
    return out


# ---------------------------------------------------------------- 六个维度

def analyze_paragraphs(body):
    ps = paragraphs(body)
    if not ps:
        return {}
    lens = [cjk_count(p) for p in ps]
    lens = [l for l in lens if l > 0]
    if not lens:
        return {}
    long_p = [l for l in lens if l > 120]
    short_p = [l for l in lens if l <= 30]
    avg = sum(lens) / len(lens)
    return {
        "段落数": len(lens),
        "平均段长": round(avg, 1),
        "最长段": max(lens),
        "超长段数(>120字)": len(long_p),
        "短段数(<=30字)": len(short_p),
        "长短比": round(len(short_p) / len(lens) * 100, 1),
    }


def analyze_dialogue(body):
    total = cjk_count(body)
    if not total:
        return {}
    dlg = sum(cjk_count(m) for m in DIALOG_PAT.findall(body))
    ratio = dlg / total * 100
    if ratio < 20:
        verdict = "偏低（叙述过重，读者易累）"
    elif ratio < 30:
        verdict = "略低（可增加对话推进信息）"
    elif ratio <= 45:
        verdict = "健康（番茄最佳区间）"
    elif ratio <= 60:
        verdict = "偏高（注意留叙述空间）"
    else:
        verdict = "过高（像剧本，缺画面感）"
    return {"对话字数": dlg, "对话占比%": round(ratio, 1), "判定": verdict}


def analyze_sentences(body):
    sents = [s for s in SENT_SPLIT.split(body) if cjk_count(s) >= 2]
    if len(sents) < 5:
        return {}
    lens = [cjk_count(s) for s in sents]
    avg = sum(lens) / len(lens)
    var = sum((l - avg) ** 2 for l in lens) / len(lens)
    std = var ** 0.5
    cv = std / avg if avg else 0
    bucket = {}
    for l in lens:
        k = "短(≤10)" if l <= 10 else "中(11-25)" if l <= 25 else "长(>25)"
        bucket[k] = bucket.get(k, 0) + 1
    if cv < 0.45:
        verdict = "过于均匀（典型 AI 味：句子长度整齐）"
    elif cv < 0.62:
        verdict = "偏均匀（可再打散句式）"
    else:
        verdict = "自然（长短参差，人类手感）"
    return {
        "句数": len(sents),
        "平均句长": round(avg, 1),
        "句长标准差": round(std, 1),
        "变异系数": round(cv, 3),
        "句长分布": bucket,
        "判定": verdict,
    }


def analyze_hooks(chapters, per_chapter=True):
    """章末钩子强度：最后 100 字是否有钩子信号。"""
    detail = []
    for title, body in chapters:
        ps = paragraphs(body)
        if not ps:
            continue
        tail = ps[-1]
        tail_cut = tail[-140:]
        hits = [w for w in HOOK_WORDS if w in tail_cut]
        score = 40
        if hits:
            score += min(30, 12 * len(hits))
        if "？" in tail_cut or "?" in tail_cut:
            score += 12
        if "…" in tail_cut or "..." in tail_cut:
            score += 8
        if cjk_count(tail) <= 40:
            score += 10
        score = min(100, score)
        grade = "强" if score >= 75 else "中" if score >= 58 else "弱"
        detail.append({
            "章节": title,
            "钩子信号": hits[:4],
            "钩子强度": score,
            "评级": grade,
            "末段": tail_cut[-60:].replace("\n", " "),
        })
    if not detail:
        return {}
    avg = sum(d["钩子强度"] for d in detail) / len(detail)
    weak = [d["章节"] for d in detail if d["评级"] == "弱"]
    return {
        "平均钩子强度": round(avg, 1),
        "强钩子章数": sum(1 for d in detail if d["评级"] == "强"),
        "弱钩子章数": len(weak),
        "弱钩子章": weak[:10],
        "明细": detail,
    }


def analyze_rhythm(chapters):
    """每章张力值：冲突词 + 转折词 + 爽点词 + 对话密度的综合。"""
    tension_words = [
        "杀", "死", "血", "怒", "吼", "砸", "碎", "冲", "撞", "爆",
        "打", "战", "逃", "追", "危机", "危险", "绝境", "背叛", "失败",
        "震惊", "震撼", "不可能", "愤怒", "绝望", "崩溃", "狂", "狠",
    ]
    pts = []
    for title, body in chapters:
        n = cjk_count(body) or 1
        hits = sum(body.count(w) for w in tension_words)
        dlg = sum(cjk_count(m) for m in DIALOG_PAT.findall(body)) / n * 100
        raw = hits / n * 1000 * 1.6 + dlg * 0.8
        pts.append({"章节": title, "张力": round(raw, 1), "字数": n})
    if not pts:
        return {}
    vals = [p["张力"] for p in pts]
    avg = sum(vals) / len(vals)
    peak = max(vals)
    trough = min(vals)
    # 起伏度：标准差 / 均值
    var = sum((v - avg) ** 2 for v in vals) / len(vals)
    cv = (var ** 0.5) / avg if avg else 0
    if len(vals) >= 4 and cv < 0.18:
        verdict = "曲线过平（连续同强度，读者会疲）"
    elif cv > 0.7:
        verdict = "起伏过陡（注意张弛衔接，避免硬切）"
    else:
        verdict = "起伏健康（有峰有谷）"
    # 单调检测：连续 3 章同方向
    flat_runs = 0
    for i in range(len(vals) - 2):
        a, b, c = vals[i], vals[i + 1], vals[i + 2]
        if (b - a) * (c - b) > 0 and abs(b - a) < avg * 0.12 and abs(c - b) < avg * 0.12:
            flat_runs += 1
    return {
        "章数": len(pts),
        "平均张力": round(avg, 1),
        "最高张力章": max(pts, key=lambda p: p["张力"])["章节"],
        "最低张力章": min(pts, key=lambda p: p["张力"])["章节"],
        "起伏系数": round(cv, 3),
        "判定": verdict,
        "疑似平段数": flat_runs,
        "明细": pts,
    }


def analyze_ai_patterns(body):
    found = []
    for pat, desc in AI_PATTERNS:
        for m in re.finditer(pat, body):
            ctx = body[max(0, m.start() - 14): m.end() + 14].replace("\n", " ")
            found.append({"类型": desc, "样句": ctx})
    agg = {}
    for f in found:
        agg[f["类型"]] = agg.get(f["类型"], 0) + 1
    # 高频复用短句（≥4 字重复 ≥3 次）
    frag = {}
    for s in SENT_SPLIT.split(body):
        s = s.strip()
        if 4 <= cjk_count(s) <= 12:
            frag[s] = frag.get(s, 0) + 1
    reused = sorted([(k, v) for k, v in frag.items() if v >= 3], key=lambda x: -x[1])
    return {
        "AI味命中总数": len(found),
        "按类统计": agg,
        "问题样例": found[:12],
        "高频复用短句": [{"句": k, "次数": v} for k, v in reused[:8]],
    }


# ---------------------------------------------------------------- 综合评分

def score_all(para, dlg, sent, hook, rhythm, ai):
    score = 100
    notes = []
    if dlg:
        r = dlg.get("对话占比%", 0)
        if r < 20:
            score -= 12
            notes.append("对话占比 %.1f%% 偏低（健康区间 30-45%%）" % r)
        elif r > 60:
            score -= 8
            notes.append("对话占比 %.1f%% 过高（健康区间 30-45%%）" % r)
    if sent:
        cv = sent.get("变异系数", 1)
        if cv < 0.45:
            score -= 14
            notes.append("句长过于整齐（变异系数 %.2f），AI 味重" % cv)
        elif cv < 0.62:
            score -= 5
            notes.append("句长偏均匀（变异系数 %.2f），建议打散句式" % cv)
    if para:
        if para.get("超长段数(>120字)", 0) >= 3:
            score -= 8
            notes.append("超长段 %d 处（单段 >120 字，手机阅读易疲劳）" % para["超长段数(>120字)"])
        if para.get("长短比", 100) < 15:
            score -= 6
            notes.append("短段仅占 %.1f%%，缺少节奏呼吸感" % para.get("长短比", 0))
    if hook:
        w = hook.get("弱钩子章数", 0)
        if w >= 2:
            score -= min(16, 5 * w)
            notes.append("%d 个章节章末钩子偏弱（追更转化受损）" % w)
        if hook.get("平均钩子强度", 100) < 60:
            score -= 6
            notes.append("平均钩子强度 %.1f 偏低" % hook.get("平均钩子强度", 0))
    if rhythm:
        if "过平" in rhythm.get("判定", ""):
            score -= 10
            notes.append("节奏曲线过平，缺少张力起伏")
        if rhythm.get("疑似平段数", 0) >= 2:
            score -= 5
            notes.append("存在 %d 处连续同强度平段" % rhythm["疑似平段数"])
    if ai:
        n = ai.get("AI味命中总数", 0)
        if n:
            score -= min(20, n * 2)
            notes.append("AI 味句式命中 %d 处" % n)
        if ai.get("高频复用短句"):
            score -= 4
            notes.append("存在高频复用短句 %d 条" % len(ai["高频复用短句"]))
    return max(0, score), notes


def build_prompt(score, notes, para, dlg, sent, hook, rhythm, ai):
    lines = ["## 优化提示词（可直接粘贴给大模型或作者本人执行）", ""]
    lines.append("我正在写一部番茄小说平台的连载作品，请按以下诊断结论重写/优化：")
    lines.append("")
    lines.append("【当前质量分】%d / 100" % score)
    lines.append("")
    lines.append("【必须修复的问题】")
    for i, n in enumerate(notes, 1):
        lines.append("%d. %s" % (i, n))
    if not notes:
        lines.append("（无结构性硬伤，进入精修阶段）")
    lines.append("")
    lines.append("【改写硬性要求】")
    if dlg and dlg.get("对话占比%", 0) < 30:
        lines.append("- 把对话占比提升到 30%-45%：把大段叙述改写为角色对话交锋，对话要带口癖、断句、不完整句")
    if sent and sent.get("变异系数", 1) < 0.62:
        lines.append("- 打散句长：把整齐的三段式排比拆掉，让句子长度参差（短句 3-8 字与长句 25-40 字交错）")
    if para and para.get("超长段数(>120字)", 0) >= 3:
        lines.append("- 拆分超长段落：单段不超过 80 字，动作/对话/心理分别成段，制造手机阅读节奏")
    if hook and hook.get("弱钩子章数", 0) >= 1:
        lines.append("- 重写弱钩子章节的最后 100 字：必须有悬念/反转/新信息/疑问，禁止平淡收尾")
    if rhythm and "过平" in rhythm.get("判定", ""):
        lines.append("- 制造张力起伏：连续 2 章同强度后必须插入 1 个低谷或高峰（冲突升级/喘息/反转）")
    if ai and ai.get("AI味命中总数", 0):
        lines.append("- 清除 AI 味：删除总结性升华句、抽象形容词（深邃/莫测/仿佛/莫名）、无信息量过渡（与此同时/另一方面）")
    lines.append("- 保持情节不变，只改表达；不追求所谓文采，追求人味与画面感")
    lines.append("")
    lines.append("【交付要求】")
    lines.append("- 直接输出改写后的完整正文，不要输出修改说明")
    lines.append("- 每 800 字至少一个微爽点/反转/信息差")
    lines.append("- 章末必须留钩子")
    return "\n".join(lines)


# ---------------------------------------------------------------- 报告

def bar(v, mx, width=28):
    if mx <= 0:
        return ""
    n = int(round(v / mx * width))
    return "█" * max(1, n) if v > 0 else ""


def render(score, notes, para, dlg, sent, hook, rhythm, ai, curve_only=False, top=10):
    L = []
    if curve_only:
        L.append("节奏曲线")
        L.append("=" * 60)
        if rhythm and rhythm.get("明细"):
            mx = max(p["张力"] for p in rhythm["明细"])
            for p in rhythm["明细"][:40]:
                L.append("  %-22s %6.1f  %s" % (p["章节"][:22], p["张力"], bar(p["张力"], mx)))
            L.append("")
            L.append("  起伏系数 %.3f ｜ %s" % (rhythm["起伏系数"], rhythm["判定"]))
        return "\n".join(L)

    L.append("番茄小说 · 节奏曲线诊断报告")
    L.append("=" * 62)
    L.append("综合质量分：%d / 100   %s" % (score, "达标 ✅" if score >= 85 else "未达标 ⚠️"))
    L.append("")
    L.append("【一、段落节奏】")
    if para:
        L.append("  段落数 %s ｜ 平均段长 %s 字 ｜ 最长段 %s 字" % (para["段落数"], para["平均段长"], para["最长段"]))
        L.append("  超长段(>120字) %s 处 ｜ 短段(<=30字) %s 处 ｜ 短段占比 %s%%"
                 % (para["超长段数(>120字)"], para["短段数(<=30字)"], para["长短比"]))
        if para["超长段数(>120字)"] >= 3:
            L.append("  ⚠️ 超长段过多：手机端单段建议 ≤80 字")
        if para["长短比"] < 15:
            L.append("  ⚠️ 短段过少：缺少呼吸感，建议插入独立短句成段")
    L.append("")
    L.append("【二、对话占比】")
    if dlg:
        L.append("  对话 %s 字 ｜ 占比 %s%% ｜ %s" % (dlg["对话字数"], dlg["对话占比%"], dlg["判定"]))
    L.append("")
    L.append("【三、句长参差度】")
    if sent:
        L.append("  句数 %s ｜ 平均 %s 字 ｜ 标准差 %s ｜ 变异系数 %s"
                 % (sent["句数"], sent["平均句长"], sent["句长标准差"], sent["变异系数"]))
        L.append("  分布：%s" % " ｜ ".join("%s %d" % (k, v) for k, v in sorted(sent["句长分布"].items())))
        L.append("  判定：%s" % sent["判定"])
    L.append("")
    L.append("【四、章节节奏曲线】")
    if rhythm:
        L.append("  章数 %s ｜ 平均张力 %s ｜ 起伏系数 %s ｜ %s"
                 % (rhythm["章数"], rhythm["平均张力"], rhythm["起伏系数"], rhythm["判定"]))
        L.append("  最高张力：《%s》  最低张力：《%s》" % (rhythm["最高张力章"], rhythm["最低张力章"]))
        mx = max(p["张力"] for p in rhythm["明细"])
        for p in rhythm["明细"][:30]:
            L.append("    %-24s %6.1f %s" % (p["章节"][:24], p["张力"], bar(p["张力"], mx, 20)))
    L.append("")
    L.append("【五、章末钩子强度】")
    if hook:
        L.append("  平均强度 %s ｜ 强钩子 %s 章 ｜ 弱钩子 %s 章"
                 % (hook["平均钩子强度"], hook["强钩子章数"], hook["弱钩子章数"]))
        if hook["弱钩子章"]:
            L.append("  需重写章末的章节：%s" % "、".join(hook["弱钩子章"]))
        for d in hook["明细"][:8]:
            L.append("    [%s] %-20s %3d 分  「…%s」" % (d["评级"], d["章节"][:20], d["钩子强度"], d["末段"]))
    L.append("")
    L.append("【六、AI 味句式扫描】")
    if ai:
        L.append("  命中总数 %s" % ai["AI味命中总数"])
        for k, v in sorted(ai["按类统计"].items(), key=lambda x: -x[1]):
            L.append("    · %s × %d" % (k, v))
        for s in ai["问题样例"][:top]:
            L.append("      样例：%s" % s["样句"])
        if ai["高频复用短句"]:
            L.append("  高频复用短句：%s"
                     % " ｜ ".join("%s(×%d)" % (x["句"], x["次数"]) for x in ai["高频复用短句"][:6]))
    L.append("")
    L.append("【七、诊断结论】")
    if notes:
        for i, n in enumerate(notes, 1):
            L.append("  %d. %s" % (i, n))
    else:
        L.append("  无结构性硬伤 ✅")
    L.append("")
    L.append(build_prompt(score, notes, para, dlg, sent, hook, rhythm, ai))
    return "\n".join(L)


# ---------------------------------------------------------------- main

def collect_files(path, recursive):
    if os.path.isfile(path):
        return [path]
    out = []
    for root, _, files in os.walk(path):
        for f in files:
            if f.lower().endswith((".md", ".txt")):
                out.append(os.path.join(root, f))
        if not recursive:
            break
    return sorted(out)


def run_one(path, top=10, curve_only=False, as_json=False):
    text = read_text(path)
    chapters = split_chapters(text)
    if len(chapters) == 1:
        body = chapters[0][1]
    else:
        body = text
    para = analyze_paragraphs(body)
    dlg = analyze_dialogue(body)
    sent = analyze_sentences(body)
    hook = analyze_hooks(chapters) if len(chapters) > 1 else analyze_hooks([("(单章)", body)])
    rhythm = analyze_rhythm(chapters)
    ai = analyze_ai_patterns(body)
    score, notes = score_all(para, dlg, sent, hook, rhythm, ai)
    if as_json:
        return {
            "file": path, "score": score, "notes": notes,
            "paragraphs": para, "dialogue": dlg, "sentences": sent,
            "hooks": {k: v for k, v in (hook or {}).items() if k != "明细"},
            "rhythm": {k: v for k, v in (rhythm or {}).items() if k != "明细"},
            "ai": ai,
        }
    return render(score, notes, para, dlg, sent, hook, rhythm, ai, curve_only, top)


def main():
    ap = argparse.ArgumentParser(description="番茄小说节奏曲线诊断器（纯标准库）")
    ap.add_argument("path", help="文件或目录（.md/.txt）")
    ap.add_argument("--recursive", action="store_true", help="递归子目录")
    ap.add_argument("--json", action="store_true", help="JSON 输出")
    ap.add_argument("--curve", action="store_true", help="只输出节奏曲线")
    ap.add_argument("--top", type=int, default=10, help="样例展示条数上限")
    ap.add_argument("--threshold", type=int, default=85, help="达标线（默认 85，仅影响退出码）")
    args = ap.parse_args()

    files = collect_files(args.path, args.recursive)
    if not files:
        print("未找到 .md/.txt 文件：%s" % args.path)
        sys.exit(2)

    worst = 100
    results = []
    scores = []
    for i, fp in enumerate(files):
        try:
            out = run_one(fp, args.top, args.curve, args.json)
        except Exception as e:  # 单文件失败不影响整体
            print("跳过 %s（%s）" % (fp, e))
            continue
        if args.json:
            results.append(out)
            scores.append(out["score"])
            worst = min(worst, out["score"])
        else:
            if len(files) > 1:
                print("\n" + "#" * 62)
                print("# 文件：%s" % fp)
                print("#" * 62)
            print(out)

    if args.json:
        print(json.dumps(results if len(results) > 1 else results[0],
                         ensure_ascii=False, indent=2))
    elif len(files) > 1:
        print("\n" + "=" * 62)
        print("批量汇总：共 %d 份，最低分 %d" % (len(scores) or len(files), worst))

    sys.exit(0 if worst >= args.threshold else 1)


if __name__ == "__main__":
    main()
