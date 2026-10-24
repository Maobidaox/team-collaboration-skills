#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ai_flavor_remover.py — AI 味专项扫描与改写建议器（纯标准库）

背景：番茄 2026 严打「AI 粗制滥造」，8 月单月拒签 16.3 万本、下架 6.1 万本。
      一旦朱雀 AI 检测判定高比例机器文本：新书在 8 万字三次评估环节被驳回，
      老书触发动态审核、切断自然流量，严重时追回往期稿费。

用途：扫描书稿中的机器味模式，给出**定位 + 原文 + 改写建议**，并计算
      "去味率"与"合规风险等级"。

用法：
  python ai_flavor_remover.py <文件或目录> [--suggest] [--top N] [--json]
  python ai_flavor_remover.py <文件> --scan-only        # 只报分数
  python ai_flavor_remover.py <文件> --check-consistency # 文风一致性（防长篇割裂）

判定逻辑：
  去味率 = (1 - 命中AI味模式数 / 段落数) × 100
  ≥ 85 分：低风险
  70-84 ：中风险（建议改写）
  < 70   ：高风险（强烈建议 ≥70% 人工改写后再发）
"""

import argparse
import json
import os
import re
import sys

# ============ AI 味模式库（规则 + 权重 + 改写建议） ============
PATTERNS = [
    # (正则, 类型, 权重, 问题说明, 改写建议)
    (r"他的眼神中透露出一种?[^。]{0,12}(深邃|复杂|难以言喻)[^。]{0,8}", "抽象情绪填充", 3,
     "用抽象形容词描述眼神/情绪，AI 高发且无信息量",
     "删掉，改为具体动作或生理反应（如：他把脸别开，指节压得发白）"),

    (r"(这一刻|那一刻|此时此刻)[，,][^。]{0,20}(忽然|突然|仿佛|似乎)(明白|懂得|意识到|领悟)[^。]{0,20}", "空洞感悟", 3,
     "角色突然'明白了'——典型 AI 收尾套路",
     "删除；让角色通过行动/选择体现领悟，不要旁白总结"),

    (r"与此同时[，,][^。]{0,30}(另一场|在[^。]{0,10}(深处|远方|角落))[^。]{0,20}(正在|正)", "万能转场", 3,
     "'与此同时，在……另一场风波正在酝酿'——AI 最爱的机械转场",
     "直接切场景，用具体的人物/物件/声音开场，不加'与此同时'"),

    (r"(仿佛|似乎|好像)隐藏着?[^。]{0,15}(无尽的?|无数的?|难以言喻的?)", "空洞修辞", 2,
     "'仿佛隐藏着无尽的秘密'——正确但空洞",
     "换成具体的、可验证的细节（一件旧物、一道疤、一个动作）"),

    (r"这?就是?[^。]{0,8}命运(的安排|的捉弄)", "总结式旁白", 2,
     "作者跳出来做总结", "删除，让情节自己说话"),

    (r"(不是|并非)[^。]{2,20}[，,](而是|而是)[^。]{2,20}", "机械对仗", 2,
     "'不是……而是……'高频连用 = 句式规整信号",
     "打散为两个独立句，或改成口语化表达"),

    (r"(有的人|有的人|有的人)", "重复排比", 2,
     "连续三段以上'有的……有的……'", "改为错落的具体描写"),

    (r"[^。]{0,10}(深深地?|深深地)(看了?|吸了?|呼吸)[^。]{0,10}", "机械动作", 1,
     "高频套路动作", "换为角色独有的习惯动作"),

    (r"整个(场面|空间|房间|大厅)[^。]{0,10}(陷入|归于)[^。]{0,6}(死寂|寂静|沉默)", "套话场景", 2,
     "'整个大厅陷入死寂'——被用滥的场面描写",
     "用具体声音的消失来写（如：连空调的嗡鸣都听得见了）"),

    (r"(嘴角|唇角)(勾起|扬起|泛起)[^。]{0,10}(一丝|一抹)[^。]{0,8}(笑|弧度|冷笑|嘲讽)", "套话表情", 2,
     "嘴角勾起一丝弧度 = 通用表情包", "删除或用具体情境反应替代"),

    (r"心中(五味杂陈|百感交集|翻江倒海|掀起惊涛骇浪)", "成语情绪", 2,
     "成语堆砌情绪，无具体感受", "写出一种具体的感受，而非全部"),

    (r"([^。]{0,15})(不由得|忍不住|不禁)(心头|心中|心里)?[^。]{0,15}", "弱动词填充", 1,
     "'不由得/忍不住'高频 = 词汇贫乏信号",
     "删掉副词，直接写动作"),

    (r"如(同|若)[^。]{0,12}(一般|一样|般)[^。]{0,10}", "机械明喻", 1,
     "'如同……一般'高频比喻", "替换为具体可比物，或直接删"),

    (r"([。！？\n])([^\n。！？]{200,}[。！？])", "超长段落", 1,
     "段落过长（>200字无句号），手机阅读跳出率高",
     "拆分段落，每段 ≤ 3 行"),

    (r"^\s*[-—]{3,}\s*$", "分隔符异常", 1, "异常分隔符", "统一排版"),
]

# 无信息对话模式
DIALOGUE_PATTERNS = [
    (r"^\s*[「\"'](你听说了吗|你知道吗|真的吗|怎么会这样|这怎么可能)[？?]?[」\"']?\s*$", "无信息对话"),
    (r"^\s*[「\"'](嗯|哦|啊|好|知道了|明白)[。！!]?[」\"']?\s*$", "敷衍回应"),
    (r"^\s*[「\"'](我)?(怎么|为什么|什么)[^。？?]{0,8}[？?][」\"']?\s*$", "纯疑问句"),
]

# 文风一致性特征（用于长篇割裂检测）
STYLE_FEATURES = [
    ("平均句长", lambda t: len(re.findall(r"[\u4e00-\u9fa5]", t)) / max(1, len(re.split(r"[。！？\n]", t)) - 1)),
    ("平均段长", lambda t: len(re.findall(r"[\u4e00-\u9fa5]", t)) / max(1, len([p for p in t.split("\n") if p.strip()]))),
    ("对话占比", lambda t: len(re.findall(r"[「\"']", t)) / 2 / max(1, len(re.split(r"[。！？\n]", t)))),
    ("感叹号密度", lambda t: t.count("！") * 100 / max(1, len(re.findall(r"[\u4e00-\u9fa5]", t)))),
    ("书面词密度", lambda t: sum(t.count(w) for w in ["然而", "因此", "尽管", "不仅如此", "与此同时", "总之", "综上所述"]) * 100 / max(1, len(re.findall(r"[\u4e00-\u9fa5]", t)))),
]


def read_files(path):
    if os.path.isfile(path):
        return [(path, _read(path))]
    out = []
    for root, _, files in os.walk(path):
        for fn in files:
            if fn.lower().endswith((".md", ".txt")):
                fp = os.path.join(root, fn)
                out.append((fp, _read(fp)))
    return sorted(out)


def _read(fp):
    for enc in ("utf-8", "utf-8-sig", "gbk", "gb18030"):
        try:
            with open(fp, "r", encoding=enc) as f:
                return f.read()
        except Exception:
            continue
    return ""


def scan(text):
    hits = []
    for pat, kind, weight, problem, advice in PATTERNS:
        for m in re.finditer(pat, text, re.M):
            s = max(0, m.start() - 30)
            e = min(len(text), m.end() + 30)
            ctx = text[s:e].replace("\n", " ")
            line_no = text[:m.start()].count("\n") + 1
            hits.append({
                "kind": kind, "weight": weight, "line": line_no,
                "match": m.group(0)[:60], "context": ctx,
                "problem": problem, "advice": advice,
            })
    # 对话水词
    dlg = 0
    for line in text.split("\n"):
        for dp, dk in DIALOGUE_PATTERNS:
            if re.search(dp, line, re.M):
                dlg += 1
                break
    return hits, dlg


def score(text, hits, dlg):
    paras = [p for p in text.split("\n") if p.strip()]
    sentences = [s for s in re.split(r"[。！？\n]", text) if s.strip()]
    n = max(1, len(paras))
    penalty = sum(h["weight"] for h in hits) + dlg * 2
    raw = 100 - (penalty * 100 / max(20, n))
    raw = max(0, min(100, raw))
    return raw, len(paras), len(sentences)


def consistency(files_texts):
    """文风一致性：按文件（或按 10 万字切片）比较特征，检测割裂"""
    feats = []
    for name, text in files_texts:
        if len(text) < 500:
            continue
        f = {"name": os.path.basename(name), "chars": len(re.findall(r"[\u4e00-\u9fa5]", text))}
        for fname, fn in STYLE_FEATURES:
            f[fname] = round(fn(text), 3)
        feats.append(f)
    return feats


def main():
    ap = argparse.ArgumentParser(description="AI 味专项扫描与改写建议器")
    ap.add_argument("path", help="文件或目录")
    ap.add_argument("--suggest", action="store_true", help="输出逐条改写建议")
    ap.add_argument("--top", type=int, default=20, help="最多显示条数")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--scan-only", action="store_true", help="只输出分数")
    ap.add_argument("--check-consistency", action="store_true", help="文风一致性检测（防长篇割裂）")
    args = ap.parse_args()

    files = read_files(args.path)
    if not files:
        print(f"[ERR] 未找到可扫描文件：{args.path}")
        return 1

    all_hits = []
    total_dlg = 0
    total_score = 0
    for fp, text in files:
        hits, dlg = scan(text)
        sc, paras, sents = score(text, hits, dlg)
        all_hits.extend([dict(h, file=fp) for h in hits])
        total_dlg += dlg
        total_score += sc
        if not args.scan_only and not args.json:
            print(f"\n=== {os.path.basename(fp)} ===")
            print(f"  去味率：{sc:.1f} / 100　段落 {paras}　句 {sents}　AI味命中 {len(hits)}　水对话 {dlg}")

    avg = total_score / len(files)

    if args.scan_only:
        print(f"\n综合去味率：{avg:.1f} / 100")
        _verdict(avg)
        return 0

    if args.json:
        print(json.dumps({"score": round(avg, 1), "hits": all_hits[:args.top],
                          "dialogue_noise": total_dlg}, ensure_ascii=False, indent=2))
        return 0

    print(f"\n" + "=" * 78)
    print(f"综合去味率：{avg:.1f} / 100")
    _verdict(avg)

    # 类型统计
    kinds = {}
    for h in all_hits:
        kinds[h["kind"]] = kinds.get(h["kind"], 0) + 1
    if kinds:
        print(f"\n【AI 味类型分布】")
        for k, v in sorted(kinds.items(), key=lambda x: -x[1]):
            print(f"  {k:<14} {v:>4} 处")

    if args.suggest and all_hits:
        print(f"\n【改写建议（Top {args.top}）】")
        print("-" * 78)
        for h in sorted(all_hits, key=lambda x: -x["weight"])[:args.top]:
            print(f"\n[{h['kind']}] {os.path.basename(h['file'])}:L{h['line']}")
            print(f"  原文：…{h['context']}…")
            print(f"  问题：{h['problem']}")
            print(f"  建议：{h['advice']}")

    if args.check_consistency:
        feats = consistency(files)
        if len(feats) >= 2:
            print(f"\n" + "=" * 78)
            print(f"【文风一致性检测】（防止长篇中途切换 AI 比例导致文风割裂）")
            print(f"{'文件':<26}{'字数':>9}{'句长':>8}{'段长':>8}{'对话%':>8}{'感叹‰':>8}{'书面‰':>8}")
            print("-" * 78)
            for f in feats:
                print(f"{f['name'][:24]:<26}{f['chars']:>9}{f['平均句长']:>8.1f}{f['平均段长']:>8.1f}"
                      f"{f['对话占比'] * 100:>8.1f}{f['感叹号密度']:>8.2f}{f['书面词密度']:>8.2f}")
            print("-" * 78)
            for key in ["平均句长", "平均段长", "书面词密度"]:
                vals = [f[key] for f in feats]
                if len(vals) >= 2:
                    rng = max(vals) - min(vals)
                    avgv = sum(vals) / len(vals)
                    if avgv > 0 and rng / avgv > 0.5:
                        print(f"  ⚠️ 「{key}」波动达 {rng/avgv*100:.0f}%，存在文风割裂风险 —— 平台会抽检原创度，文风突变会触发动态审核。")

    print(f"\n【合规红线提醒】")
    print(f"  🚫 整章节 AI 一键生成 + 少量修改 → 8万字评估驳回，浪费仅有的 3 次推荐名额")
    print(f"  🚫 多账号批量开书凑全勤 → 永久封禁主体资质")
    print(f"  🚫 长篇文风前后割裂 → 切断书城自然流量，严重时追回往期稿费")
    print(f"  ✅ 合规姿势：AI 只做大纲/资料/润色；正文素材稿需 ≥70% 人工改写；对话与核心冲突必须自写")
    return 0


def _verdict(sc):
    if sc >= 85:
        print(f"  判定：🟢 低风险 —— 机器味较少，可进入常规质检流程")
    elif sc >= 70:
        print(f"  判定：🟠 中风险 —— 建议按改写建议处理后再发布")
    else:
        print(f"  判定：🔴 高风险 —— 强烈建议做 ≥70% 人工改写后再发布，否则有被判 AI 粗制滥造的风险")


if __name__ == "__main__":
    sys.exit(main())
