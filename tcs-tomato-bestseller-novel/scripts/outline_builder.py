#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
outline_builder.py — 番茄小说分卷大纲与逐章细纲生成器（纯标准库）

用途：把"一个核心设定"自动展开为**可执行的全书结构**——分卷架构、
      逐章细纲、爽点排布、伏笔台账、追更锚点，并输出 Markdown。

设计依据：
  - 承载力公式（参考文件 20）：目标字数 → 反推所需层级/地图数
  - 情绪循环（参考文件 22）：每 10 章一个循环，爽点间隔 ≤ 5 章
  - 名场面密度（参考文件 21）：每 10 章 ≥1 个
  - 完本模式要求（参考文件 14）：结构完整、主线清晰、节奏稳定

用法：
  # 生成全书大纲
  python outline_builder.py --title "书名" --genre "都市脑洞" --words 100 --volumes 8

  # 只生成前 3 卷（黄金开局期）
  python outline_builder.py --title "x" --genre "x" --words 60 --opening-only

  # 生成指定卷的逐章细纲
  python outline_builder.py --title "x" --genre "x" --words 100 --chapters --volume 2

  # 检查已有大纲的伏笔台账
  python outline_builder.py --check-foreshadow outline.md
"""

import argparse
import json
import os
import sys
from datetime import datetime

# ============ 赛道 → 卷结构模板 ============
GENRE_TEMPLATES = {
    "都市脑洞": {"arc": ["规则揭示", "规则利用", "规则升级", "规则源头", "新世界"], "antagonist": ["势利同事", "行业权威", "神秘组织", "规则制定者", "世界意志"],
                 "map": ["小区/公司", "城市", "全国", "全球", "维度外"]},
    "动漫衍生": {"arc": ["原著事件介入", "蝴蝶效应", "原著角色态度转变", "关键悲剧改写", "新结局"],
                 "antagonist": ["原著小反派", "原著大反派", "世界意志", "穿越者同行", "最终 BOSS"],
                 "map": ["原著初始地", "原著主舞台", "原著隐藏区域", "跨作品区", "原著终局"]},
    "玄幻": {"arc": ["宗门崛起", "域外争锋", "上界之谜", "万族大战", "登顶"], "antagonist": ["同门", "敌对宗门", "上界势力", "万族天骄", "天道"],
             "map": ["外门", "内门/秘境", "一域", "上界", "诸天"]},
    "女频·双男主": {"arc": ["初遇与误会", "关系升温", "身份揭示", "外部危机", "双向奔赴"],
                    "antagonist": ["情敌", "家族阻力", "身份阻碍", "共同敌人", "内心恐惧"],
                    "map": ["校园/公司", "社交圈", "家族", "公众视野", "二人世界"]},
    "女频·快穿": {"arc": ["第一个世界", "模式建立", "难度升级", "系统真相", "最终世界"],
                  "antagonist": ["世界主角", "任务对象", "系统干扰", "其他快穿者", "系统本体"],
                  "map": ["世界1", "世界2-3", "世界4-5", "世界6-7", "终局世界"]},
    "专业流": {"arc": ["初露锋芒", "行业认可", "权威挑战", "领域颠覆", "行业标杆"],
               "antagonist": ["质疑者", "同行竞争者", "行业权威", "利益集团", "自我突破"],
               "map": ["基层岗位", "行业圈子", "全国舞台", "国际舞台", "行业之巅"]},
    "科幻末世": {"arc": ["生存", "结盟", "建秩序", "对抗新威胁", "重建文明"],
                 "antagonist": ["感染者", "幸存者势力", "资源垄断者", "新物种", "环境本身"],
                 "map": ["避难所", "城市废墟", "区域", "大陆", "全球"]},
}
DEFAULT_TEMPLATE = {"arc": ["开局立住", "第一次升级", "中段转折", "高潮铺垫", "终局"],
                    "antagonist": ["小反派", "中层反派", "大反派", "幕后黑手", "终极 BOSS"],
                    "map": ["起始地", "进阶地", "中级地", "高级地", "终极地"]}

# ============ 每章功能位（10 章情绪循环） ============
CYCLE_10 = [
    (1, "压抑/困境", "读者心疼，建立共情", "钩子：新危机降临"),
    (2, "转机初现", "金手指第一次小兑现", "钩子：能力有意外副作用"),
    (3, "第一次打脸", "爽点爆发", "钩子：打脸引来更强敌人"),
    (4, "余波与升温", "人物关系推进", "钩子：有人开始怀疑主角"),
    (5, "新的压制", "对手升级", "钩子：主角陷入被动"),
    (6, "绝境", "读者憋屈到极点", "钩子：看似无解"),
    (7, "伏笔兑现", "名场面（绝境反转）", "钩子：反转带来更大麻烦"),
    (8, "高光时刻", "名场面（身份揭露/宣言）", "钩子：身份暴露的后遗症"),
    (9, "甜点/喘息", "情绪缓冲，人物互动", "钩子：短暂的平静被打破"),
    (10, "新危机", "卷级转折或下一循环开启", "钩子：卷末大钩子"),
]


def pick_template(genre):
    for k, v in GENRE_TEMPLATES.items():
        if k in genre or genre in k:
            return v
    return DEFAULT_TEMPLATE


def calc_volumes(words_wan):
    """按字数推荐卷数：每卷约 8-12 万字"""
    if words_wan <= 30:
        return max(3, int(words_wan / 8))
    if words_wan <= 100:
        return max(4, int(words_wan / 12))
    return max(8, int(words_wan / 14))


def build_outline(title, genre, words_wan, volumes=None, opening_only=False):
    tpl = pick_template(genre)
    vols = volumes or calc_volumes(words_wan)
    if opening_only:
        vols = min(3, vols)
    words_per_vol = words_wan * 10000 / vols
    chapters_per_vol = int(words_per_vol / 2200)

    L = [f"# 《{title}》全书大纲",
         f"",
         f"- **赛道**：{genre}",
         f"- **目标字数**：{words_wan} 万字（全书 {vols} 卷，每卷约 {words_per_vol/10000:.1f} 万字 / {chapters_per_vol} 章）",
         f"- **生成时间**：{datetime.now().strftime('%Y-%m-%d')}",
         f"- **生成工具**：`outline_builder.py`（番茄爆款小说专家 · 知识库 {_snapshot()}）",
         f"",
         f"> ⚠️ 本大纲为**结构骨架**，需由作者填充血肉。正文请务必人工主笔（AI 合规要求，见参考文件 15）。",
         f"",
         f"---",
         f"",
         f"## 零、一句话主线（必须先定，全书不得偏离）",
         f"",
         f"**主角要什么**：（待填写）",
         f"**阻碍是什么**：（待填写）",
         f"**代价是什么**：（待填写）",
         f"",
         f"### 核心设定（一句话记忆点）",
         f"> （待填写：必须能一句话说清，且与同类作品有差异）",
         f"",
         f"### 结局（**先写结局，再写开头**）",
         f"> （待填写：结局决定所有伏笔的埋法）",
         f"",
         f"---",
         f""]

    # 卷架构
    L += [f"## 一、分卷架构", f""]
    L += [f"| 卷 | 卷名 | 字数 | 章数 | 核心任务 | 主舞台 | 反派 | 卷末高潮 |",
          f"|---|---|---|---|---|---|---|---|"]
    for v in range(1, vols + 1):
        arc_i = min(v - 1, len(tpl["arc"]) - 1)
        map_i = min(v - 1, len(tpl["map"]) - 1)
        ant_i = min(v - 1, len(tpl["antagonist"]) - 1)
        climax = "名场面·身份揭露" if v % 3 == 0 else ("名场面·绝境反转" if v % 3 == 1 else "名场面·打脸")
        L.append(f"| 第{v}卷 | {tpl['arc'][arc_i]} | {words_per_vol/10000:.1f}万 | {chapters_per_vol} | "
                 f"{tpl['arc'][arc_i]} | {tpl['map'][map_i]} | {tpl['antagonist'][ant_i]} | {climax} |")

    # 逐卷详纲
    L += [f"", f"---", f"", f"## 二、逐卷详纲", f""]
    for v in range(1, vols + 1):
        arc_i = min(v - 1, len(tpl["arc"]) - 1)
        map_i = min(v - 1, len(tpl["map"]) - 1)
        ant_i = min(v - 1, len(tpl["antagonist"]) - 1)
        L += [f"### 第 {v} 卷 · {tpl['arc'][arc_i]}",
              f"",
              f"- **主舞台**：{tpl['map'][map_i]}",
              f"- **主要对手**：{tpl['antagonist'][ant_i]}",
              f"- **本卷目标**：（待填写：本卷结束时主角达成什么）",
              f"- **本卷小高潮**：（待填写：必须自成闭环，读者停在这也满足）",
              f"- **本卷伏笔**：（待填写：本卷埋下什么，计划第几卷回收）",
              f"- **卷末钩子**：（待填写：必须让读者非看下一卷不可）",
              f""]

    # 前 30 章逐章细纲（10 章循环 × 3）
    L += [f"---", f"", f"## 三、前 30 章逐章细纲（情绪循环 × 3）", f"",
          f"> 依据参考文件 22：每 10 章一个情绪循环；爽点间隔 ≤ 5 章；每 10 章 ≥1 个名场面。", f""]
    L += [f"| 章 | 功能位 | 本章任务 | 情绪目标 | 章末钩子 |",
          f"|---|---|---|---|---|"]
    ch = 1
    for cycle in range(3):
        for pos, fn, emo, hook in CYCLE_10:
            L.append(f"| 第{ch}章 | {fn} | （待填写） | {emo} | {hook} |")
            ch += 1

    # 伏笔台账
    L += [f"", f"---", f"", f"## 四、伏笔台账（完本前回收率须 ≥80%）", f"",
          f"| 编号 | 埋设章节 | 伏笔内容 | 级别 | 计划回收章节 | 已回收 |",
          f"|---|---|---|---|---|---|",
          f"| F-001 | 第 3 章 | （待填写） | 长线 | 第 ___ 章 | ☐ |",
          f"| F-002 | 第 8 章 | （待填写） | 中线 | 第 ___ 章 | ☐ |",
          f"| F-003 | 第 15 章 | （待填写） | 中线 | 第 ___ 章 | ☐ |",
          f"| F-004 | 第 25 章 | （待填写） | 长线 | 第 ___ 章 | ☐ |",
          f"| F-005 | 第 30 章 | （待填写） | 短线 | 第 ___ 章 | ☐ |",
          f""]

    # 名场面排布
    L += [f"---", f"", f"## 五、名场面排布表", f"",
          f"> 依据参考文件 21：每 10 章 ≥1 个名场面；每 30 章 ≥1 个全书级名场面。", f"",
          f"| 章节 | 名场面类型 | 内容 | 金句 |",
          f"|---|---|---|---|"]
    ms_types = ["打脸名场面", "绝境反转", "身份揭露", "情感峰值", "金句宣言", "视觉奇观"]
    for i in range(1, min(vols * chapters_per_vol, 300) // 10 + 1):
        chn = i * 10
        mt = ms_types[(i - 1) % len(ms_types)]
        L.append(f"| 第{chn}章 | {mt} | （待填写） | （待填写） |")

    # 自检
    L += [f"", f"---", f"", f"## 六、动笔前自检（参考文件 20 / 14）", f"",
          f"- [ ] 核心设定能一句话说清，且与同类作品有差异？",
          f"- [ ] 力量体系有明确的层级、升级条件、代价、上限？",
          f"- [ ] 目标 {words_wan} 万字所需的层级数是否足够（当前 {vols} 卷 / {len(tpl['arc'])} 阶段）？",
          f"- [ ] 至少有 3 级地图可供切换（当前 {len(tpl['map'])} 级）？",
          f"- [ ] 设计了 3-5 个长线伏笔并有台账？",
          f"- [ ] **结局已经写好**，且倒推验证了伏笔埋设？",
          f"- [ ] 设定符合「三秒可读」原则（番茄 45 岁以上读者占 45.7%）？",
          f"- [ ] 是否踩了内容治理红线（参考文件 13）？",
          f""]

    return "\n".join(L)


def build_chapters(title, genre, words_wan, volume, chapters_per_vol=None):
    tpl = pick_template(genre)
    vols = calc_volumes(words_wan)
    wpv = words_wan * 10000 / vols
    cpv = chapters_per_vol or int(wpv / 2200)
    start = (volume - 1) * cpv + 1
    arc_i = min(volume - 1, len(tpl["arc"]) - 1)

    L = [f"# 《{title}》第 {volume} 卷 · 逐章细纲",
         f"",
         f"- **卷主题**：{tpl['arc'][arc_i]}",
         f"- **章节范围**：第 {start} – {start + cpv - 1} 章（共 {cpv} 章）",
         f"- **生成时间**：{datetime.now().strftime('%Y-%m-%d')}",
         f"",
         f"---",
         f"",
         f"| 章 | 功能位 | 本章任务 | 情绪目标 | 章末钩子 | 名场面 |",
         f"|---|---|---|---|---|---|"]
    for i in range(cpv):
        pos, fn, emo, hook = CYCLE_10[i % 10]
        ms = "★" if (i + 1) % 10 == 0 else ""
        L.append(f"| 第{start+i}章 | {fn} | （待填写） | {emo} | {hook} | {ms} |")
    L += [f"",
          f"---",
          f"",
          f"## 本卷交付物清单",
          f"",
          f"- [ ] 本卷目标已达成（主角获得阶段性成果）",
          f"- [ ] 本卷小高潮自成闭环（读者停在这也满足）",
          f"- [ ] 本卷伏笔已登记到台账",
          f"- [ ] 卷末钩子强度足够（非看下一卷不可）",
          f"- [ ] 每章字数 2000-2500 字，每段 ≤3 行",
          f"- [ ] 每 3-5 章有 1 个追更锚点",
          f""]
    return "\n".join(L)


def check_foreshadow(path):
    text = open(path, "r", encoding="utf-8", errors="ignore").read()
    rows = [l for l in text.split("\n") if l.strip().startswith("| F-")]
    if not rows:
        print("[WARN] 未找到伏笔台账行（以 | F- 开头）")
        return 1
    total = len(rows)
    done = sum(1 for r in rows if "☑" in r or "✅" in r)
    rate = done / total * 100
    print(f"伏笔总数：{total}　已回收：{done}　回收率：{rate:.1f}%")
    if rate >= 80:
        print("✅ 达到完本要求（≥80%）")
    else:
        print(f"⚠️ 未达完本要求，尚有 {total - done} 个伏笔未回收 —— 未回收的核心伏笔是烂尾感的主要来源")
        for r in rows:
            if "☑" not in r and "✅" not in r:
                parts = [x.strip() for x in r.strip().strip("|").split("|")]
                if len(parts) >= 3:
                    print(f"   未回收：{parts[0]} @ {parts[1]} — {parts[2]}")
    return 0


def _snapshot():
    p = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".evolution_state")
    if os.path.exists(p):
        try:
            return json.load(open(p, "r", encoding="utf-8")).get("snapshot", "2026-09")
        except Exception:
            pass
    return "2026-09"


def main():
    ap = argparse.ArgumentParser(description="番茄小说分卷大纲与逐章细纲生成器")
    ap.add_argument("--title", help="书名")
    ap.add_argument("--genre", help="赛道，如 都市脑洞 / 动漫衍生 / 玄幻 / 女频·双男主")
    ap.add_argument("--words", type=float, help="目标字数（万字）")
    ap.add_argument("--volumes", type=int, help="卷数（默认按字数推荐）")
    ap.add_argument("--opening-only", action="store_true", help="只生成前 3 卷")
    ap.add_argument("--chapters", action="store_true", help="生成指定卷的逐章细纲")
    ap.add_argument("--volume", type=int, help="指定卷号（配合 --chapters）")
    ap.add_argument("--output", "-o", help="输出文件路径（默认 stdout）")
    ap.add_argument("--check-foreshadow", help="检查大纲文件的伏笔台账")
    args = ap.parse_args()

    if args.check_foreshadow:
        return check_foreshadow(args.check_foreshadow)

    if not all([args.title, args.genre, args.words]):
        ap.error("需要 --title / --genre / --words")

    if args.chapters:
        out = build_chapters(args.title, args.genre, args.words, args.volume or 1)
    else:
        out = build_outline(args.title, args.genre, args.words, args.volumes, args.opening_only)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(out + "\n")
        print(f"[OK] 已生成：{args.output}（{len(out)} 字符）")
    else:
        print(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
