#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
consistency_ledger.py — 番茄爆款小说专家 · 四大台账一致性校对器（纯标准库）

长篇崩盘的三大元凶：人物崩、战力崩、时间线崩。本脚本从稿件中自动抽取
「人物 / 战力 / 物品 / 时间线」四类要素，生成台账骨架，并检测矛盾信号。

用法：
  python consistency_ledger.py --file 稿件.md --all
  python consistency_ledger.py --file 稿件.md --check-name        # 人名一致性
  python consistency_ledger.py --file 稿件.md --check-power       # 战力/等级
  python consistency_ledger.py --file 稿件.md --check-original    # 原创性自检提示
  python consistency_ledger.py --file 稿件.md --ledger 台账.md    # 生成四大台账骨架
"""

import argparse
import os
import re
import sys
from collections import Counter
from datetime import datetime

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

# 等级/战力关键词
POWER_WORDS = ["练气", "筑基", "金丹", "元婴", "化神", "炼虚", "合体", "大乘", "渡劫",
               "一阶", "二阶", "三阶", "四阶", "五阶", "六阶", "七阶", "八阶", "九阶",
               "青铜", "白银", "黄金", "铂金", "钻石", "王者",
               "F级", "E级", "D级", "C级", "B级", "A级", "S级", "SS级", "SSS级",
               "一段", "二段", "三段"]

# 时间标记
TIME_WORDS = ["三年前", "五年前", "十年前", "二十年前", "百年前", "千年前",
              "昨天", "前天", "上周", "上个月", "去年", "半年前", "三个月前",
              "次日", "翌日", "三天后", "一个月后", "一年后"]

# 物品/道具标志词
ITEM_SUFFIX = ["剑", "刀", "枪", "丹", "药", "符", "珠", "戒", "令", "印", "镜",
               "玉", "石", "书", "卷", "碑", "塔", "铃", "匣", "环"]


def read_text(p):
    with open(p, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


# 副词/动词尾缀（常被误并入人名）
ADV_TAIL = set("淡冷轻缓猛忽沉笑恨怒低哑颤森平懒随意漠")
VERB_STOP = set("说道问答喊叫吼叹哼")


def _clean_name(w):
    """去掉尾部副词，并剔除叠字假名。"""
    while len(w) > 2 and w[-1] in ADV_TAIL:
        w = w[:-1]
    # 叠字（如"淡淡""默默"）多为副词，剔除
    if len(w) == 2 and w[0] == w[1]:
        return ""
    if w[-1] in VERB_STOP:
        return ""
    return w


def extract_names(text):
    """抽取疑似人名（2-3 字，出现在对话前后或动作前）。"""
    cand = Counter()
    # 对话归属：X说/X道/X问
    for m in re.finditer(r"([\u4e00-\u9fa5]{2,3})(说|道|问|答|笑|哼|喊|叫|吼|叹)", text):
        w = _clean_name(m.group(1))
        if w:
            cand[w] += 2
    # 姓氏 + 称呼
    for m in re.finditer(r"(老|小|大|阿)([\u4e00-\u9fa5])", text):
        cand[m.group(1) + m.group(2)] += 1
    # 常见姓氏开头 2-3 字
    for m in re.finditer(r"(?<![\u4e00-\u9fa5])([赵钱孙李周吴郑王冯陈褚卫蒋沈韩杨朱秦尤许何吕施张孔曹严华金魏陶姜戚谢邹喻柏水窦章云苏潘葛奚范彭郎鲁韦昌马苗凤花方俞任袁柳][\u4e00-\u9fa5]{1,2})(?![\u4e00-\u9fa5])", text):
        cand[_clean_name(m.group(1))] += 1
    # 过滤非人名
    stop = {"什么", "这个", "那个", "一个", "时候", "问题", "东西", "地方", "事情",
            "大家", "自己", "他们", "我们", "你们", "这里", "那里", "怎么", "没有",
            "他知", "她知", "知道", "父亲", "母亲", "父亲", "男主", "女主"}
    return [(k, v) for k, v in cand.most_common(40) if k and k not in stop and len(k) >= 2]


def extract_items(text):
    cand = Counter()
    for suf in ITEM_SUFFIX:
        for m in re.finditer(r"([\u4e00-\u9fa5]{1,3}" + suf + r")", text):
            w = m.group(1)
            if len(w) >= 2:
                cand[w] += 1
    return [x for x in cand.most_common(30) if x[1] >= 2]


def cmd_check_name(text, args):
    print("=" * 74)
    print("一、人物台账 · 人名一致性")
    print("=" * 74)
    names = extract_names(text)
    if not names:
        print("（未识别到明显人名，请手动建立台账）")
        return []
    print("%-10s %-8s %s" % ("人名", "出现次数", "备注"))
    print("-" * 74)
    suspects = []
    for n, c in names:
        note = ""
        if c >= 30:
            note = "⚠️ 高频，检查是否有名字相近导致混淆"
            suspects.append((n, c))
        print("%-10s %-8d %s" % (n, c, note))
    # 相近名检测（前 2 字相同或编辑距离 1）
    close = []
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            a, b = names[i][0], names[j][0]
            if a != b and (a[:2] == b[:2] or (len(a) == len(b) and sum(1 for x, y in zip(a, b) if x != y) == 1)):
                close.append((a, b))
    if close:
        print("\n🔴 相近人名预警（读者易混淆，建议改名或强化区分）：")
        for a, b in close[:10]:
            print("   · %s ↔ %s" % (a, b))
    else:
        print("\n✅ 未发现明显相近人名")
    return names


def cmd_check_power(text, args):
    print("\n" + "=" * 74)
    print("二、战力台账 · 等级体系一致性")
    print("=" * 74)
    hits = Counter()
    for w in POWER_WORDS:
        c = text.count(w)
        if c:
            hits[w] = c
    if not hits:
        print("（未识别到等级体系词，可能是现实题材或自定义体系）")
        return {}
    print("%-10s %-8s" % ("等级词", "出现次数"))
    print("-" * 74)
    for w, c in hits.most_common():
        print("%-10s %-8d" % (w, c))
    # 体系混乱检测：同时出现多套体系
    systems = []
    if any(k in hits for k in ["练气", "筑基", "金丹", "元婴", "化神"]):
        systems.append("修仙体系")
    if any(k in hits for k in ["F级", "S级", "SSS级"]):
        systems.append("字母等级体系")
    if any(k in hits for k in ["青铜", "白银", "黄金", "砖石", "钻石", "王者"]):
        systems.append("段位体系")
    if any(k in hits for k in ["一阶", "二阶", "三阶", "九阶"]):
        systems.append("阶位体系")
    if len(systems) > 1:
        print("\n⚠️ 检测到多套等级体系并存：%s" % "、".join(systems))
        print("   → 若非有意设计（如双体系对抗），建议统一或明确对应关系")
    else:
        print("\n✅ 等级体系唯一：%s" % (systems[0] if systems else "自定义"))
    return dict(hits)


def cmd_check_time(text, args):
    print("\n" + "=" * 74)
    print("三、时间线台账")
    print("=" * 74)
    hits = Counter()
    for w in TIME_WORDS:
        c = text.count(w)
        if c:
            hits[w] = c
    if not hits:
        print("（未识别到时间标记）")
        return {}
    for w, c in hits.most_common():
        print("  %-10s ×%d" % (w, c))
    # 冲突检测：同时出现"三年前"和"十年前"描述同一事件（简化：只提示）
    if "三年前" in hits and "十年前" in hits:
        print("\n⚠️ 同时出现「三年前」与「十年前」——请核对是否指向同一事件")
    return dict(hits)


def cmd_check_original(text, args):
    print("=" * 74)
    print("四、原创性自检提示（拆结构可以，抄文字不行）")
    print("=" * 74)
    print("请逐条自查：")
    print("  1. 有没有段落「太像某一本爆款」？（逐段读一遍）")
    print("  2. 有没有沿用他人的独创专有名词？（如独特功法名/组织名）")
    print("  3. 情节序列是否与他人作品高度对应？（结构相似=安全；序列对应=危险）")
    print("  4. 素材来源是否都有记录？（URL + 获取日期）")
    print("  5. AI 使用环节是否留痕？（哪些环节、改写了多少）")
    print()
    print("详见 references/40 号（反洗稿公约与原创证据链管理）")
    return 0


def cmd_ledger(text, args):
    names = extract_names(text)
    items = extract_items(text)
    powers = Counter({w: text.count(w) for w in POWER_WORDS if text.count(w)})
    times = Counter({w: text.count(w) for w in TIME_WORDS if text.count(w)})
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    L = ["# 四大台账（自动生成骨架）", "", "- 生成时间：%s" % now, "",
         "> 说明：本文件为自动抽取的**骨架**，请人工补全「首次出现章节 / 状态 / 备注」列。", "",
         "## 一、人物台账", "", "| 姓名 | 身份 | 首次出现 | 当前状态 | 备注 |", "|---|---|---|---|---|"]
    for n, _ in names[:40]:
        L.append("| %s |  |  |  |  |" % n)
    L += ["", "## 二、战力/等级台账", "", "| 等级 | 归属体系 | 首次出现 | 代表人物 | 备注 |", "|---|---|---|---|---|"]
    for w, _ in powers.most_common():
        L.append("| %s |  |  |  |  |" % w)
    L += ["", "## 三、物品/道具台账", "", "| 名称 | 归属 | 首次出现 | 当前状态 | 备注 |", "|---|---|---|---|---|"]
    for w, _ in items[:30]:
        L.append("| %s |  |  |  |  |" % w)
    L += ["", "## 四、时间线台账", "", "| 时间标记 | 对应事件 | 出现章节 | 备注 |", "|---|---|---|---|"]
    for w, _ in times.most_common():
        L.append("| %s |  |  |  |  |" % w)
    L += ["", "> 详细台账方法见 references/18 号（长篇一致性四大台账与防崩盘工程）。"]
    out = args.ledger or "四大台账.md"
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(L) + "\n")
    print("[OK] 台账骨架已生成：%s（人物 %d / 等级 %d / 物品 %d / 时间 %d）"
          % (os.path.abspath(out), len(names[:40]), len(powers), len(items[:30]), len(times)))
    return 0


def main():
    p = argparse.ArgumentParser(description="番茄爆款小说专家 · 四大台账一致性校对器")
    p.add_argument("--file", help="稿件文件")
    p.add_argument("--all", action="store_true", help="全量校对")
    p.add_argument("--check-name", action="store_true")
    p.add_argument("--check-power", action="store_true")
    p.add_argument("--check-original", action="store_true")
    p.add_argument("--ledger", nargs="?", const="四大台账.md", help="生成台账骨架")
    args = p.parse_args()
    if not args.file:
        p.print_help()
        return 0
    if not os.path.exists(args.file):
        print("[ERR] 文件不存在：%s" % args.file)
        return 1
    text = read_text(args.file)
    if args.check_original:
        return cmd_check_original(text, args)
    if args.ledger:
        return cmd_ledger(text, args)
    if args.all or args.check_name:
        cmd_check_name(text, args)
    if args.all or args.check_power:
        cmd_check_power(text, args)
    if args.all:
        cmd_check_time(text, args)
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
