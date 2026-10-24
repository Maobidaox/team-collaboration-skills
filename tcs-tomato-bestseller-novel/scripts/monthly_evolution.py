#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
番茄爆款小说专家 · 知识库月度自动进化脚本
------------------------------------------
纯标准库实现，零第三方依赖，跨平台（Windows / macOS / Linux）。

用途：
  1) --check   检查知识库时效（距上次更新是否超过一个自然月）
  2) --report  生成 / 更新《进化报告.md》，列出本次需联网核验的清单
  3) --touch   完成进化后写入新的口径日期（更新 .evolution_state）

建议自动化：每月 1 号 0:00-1:00 执行
  python monthly_evolution.py --check --report 进化报告.md
  （由专家完成联网核验与文件更新后）
  python monthly_evolution.py --touch

退出码：
  0 = 时效正常 / 操作成功
  2 = 已过期，需要进化（供自动化判断是否继续）
"""

import argparse
import json
import os
import sys
from datetime import datetime, date

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATE_FILE = os.path.join(BASE_DIR, ".evolution_state")
CHANGELOG = os.path.join(BASE_DIR, "changelog.md")
DEFAULT_SNAPSHOT = "2026-09"

# 每次进化必须联网核验的十二个项目（v2 升级：8 → 12）
EVOLUTION_ITEMS = [
    ("平台规则", "番茄作家专区最新公告：推荐评估（8 万字）、验证期（7 天）、首秀（10 万字 14 天）是否有调整",
     "https://fanqienovel.com/writer/zone"),
    ("福利政策", "2026-09 福利焕新：全勤三阶段（15 万/20 万/听读 500→1500）、10 月 1 日旧版下线是否按期",
     "https://fanqienovel.com/writer/zone"),
    ("高价值奖项", "品质臻选奖（收益 15%、上限 10 万）、星火计划（收益 10% 不封顶）、星燃计划金额",
     "https://fanqienovel.com/writer/zone"),
    ("完本模式", "完本签约核算周期（3/6/12 个月）、起笔扬帆奖、品质成就奖（读完率 18%）门槛",
     "https://fanqienovel.com/writer/zone"),
    ("榜单规则", "巅峰榜 TOP30、六维评估维度、更新频率与题材分布是否调整",
     "https://fanqienovel.com"),
    ("题材风向", "男频/女频近 3 个月热度排序与新崛起流派（都市高武/悬疑脑洞/西幻领主等）",
     "WebSearch: 番茄小说 2026 热门题材 风向"),
    ("数据红线", "完读率 15%、追读率 35%、吸量 400（S 级）、单章有效阅读 90 秒是否调整",
     "WebSearch: 番茄小说 2026 完读率 追读率 红线"),
    ("内容治理", "低质四类判定、AI 内容标识规则、拒签与下架量级、梯度处置机制",
     "https://fanqienovel.com/writer/zone"),
    ("单价与收益", "eCPM 区间（8-18 元/千次）、有效阅读分成（0.1-0.5 元/千次）是否变化",
     "WebSearch: 番茄小说 2026 听读分成 单价 eCPM"),
    ("IP 变现", "短剧（单书最高 60 万）/漫剧（2400+ 部）/有声改编、百万 IP 护航计划档位",
     "WebSearch: 番茄小说 2026 短剧 改编 版权 奖励"),
    ("竞品玩法", "同类 AI 网文专家的新能力、新范式、用户差评点",
     "WebSearch: AI 网文写作 专家 2026"),
    ("读者口味", "读者对爽点密度、去悬浮、现实共鸣、情绪价值偏好的变化",
     "WebSearch: 网文读者 2026 口味 趋势"),
]


def read_state():
    if not os.path.exists(STATE_FILE):
        return {"snapshot": DEFAULT_SNAPSHOT, "level": "L1", "last_evolved": DEFAULT_SNAPSHOT + "-01"}
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"snapshot": DEFAULT_SNAPSHOT, "level": "L1", "last_evolved": DEFAULT_SNAPSHOT + "-01"}


def write_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def months_between(snapshot_a, snapshot_b):
    """计算两个 YYYY-MM 之间相差的月数。"""
    def to_m(s):
        y, m = s.split("-")[:2]
        return int(y) * 12 + int(m)
    return abs(to_m(snapshot_b) - to_m(snapshot_a))


def cmd_check(state):
    now = date.today()
    current = "%04d-%02d" % (now.year, now.month)
    gap = months_between(state.get("snapshot", DEFAULT_SNAPSHOT), current)
    print("=" * 60)
    print("番茄爆款小说专家 · 知识库时效检查")
    print("=" * 60)
    print("当前日期     : %s" % now.isoformat())
    print("知识库口径   : %s" % state.get("snapshot", DEFAULT_SNAPSHOT))
    print("当前档期     : %s" % current)
    print("距上次进化   : %d 个月" % gap)
    print("进化层级     : %s" % state.get("level", "L1"))
    print("-" * 60)
    if gap >= 1:
        print("[需要进化] 知识库已跨月，请执行八路联网核验后更新 references。")
        print("           建议命令：python monthly_evolution.py --report 进化报告.md")
        return 2
    print("[时效正常] 知识库处于当月最新口径，无需强制进化。")
    return 0


def cmd_report(state, out_path):
    now = datetime.now()
    current = "%04d-%02d" % (now.year, now.month)
    gap = months_between(state.get("snapshot", DEFAULT_SNAPSHOT), current)
    lines = []
    lines.append("# 番茄爆款小说专家 · 知识库进化报告")
    lines.append("")
    lines.append("- 生成时间：%s" % now.strftime("%Y-%m-%d %H:%M"))
    lines.append("- 上次口径：%s（距今 %d 个月）" % (state.get("snapshot", DEFAULT_SNAPSHOT), gap))
    lines.append("- 当前层级：%s" % state.get("level", "L1"))
    lines.append("")
    lines.append("## 一、本次需联网核验清单（十二路）")
    lines.append("")
    lines.append("| # | 项目 | 核验内容 | 信源 | 状态 |")
    lines.append("|---|---|---|---|---|")
    for i, (name, desc, src) in enumerate(EVOLUTION_ITEMS, 1):
        lines.append("| %d | %s | %s | %s | 待核验 |" % (i, name, desc, src))
    lines.append("")
    lines.append("## 二、核验结果记录")
    lines.append("")
    lines.append("（由专家在联网核验后填写：变更项 / 新增项 / 失效项）")
    lines.append("")
    lines.append("| 项目 | 是否变化 | 新口径 | 来源与日期 | 影响文件 |")
    lines.append("|---|---|---|---|---|")
    lines.append("|      |          |        |            |          |")
    lines.append("")
    lines.append("## 三、本次进化动作")
    lines.append("")
    lines.append("- [ ] 更新受影响的 references 文件")
    lines.append("- [ ] 追加 changelog.md 版本条目")
    lines.append("- [ ] 校验专家包（validate_expert.py → register_expert.py）")
    lines.append("- [ ] 重新打包 zip 并版本化归位")
    lines.append("- [ ] 执行 --touch 写入新口径日期")
    lines.append("")
    lines.append("## 四、能力跃迁目标")
    lines.append("")
    lines.append("每次进化至少输出能力提升一个层级：新增/修订知识 ≥2 项，且必须有可验证的新增量")
    lines.append("（新规则 / 新趋势 / 新模板 / 新翻车案例），禁止仅做文字润色。")
    lines.append("")

    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print("[已生成] 进化报告：%s" % os.path.abspath(out_path))
    return 0


def cmd_touch(state, snapshot=None, level=None):
    now = date.today()
    if not snapshot:
        snapshot = "%04d-%02d" % (now.year, now.month)
    state["snapshot"] = snapshot
    state["last_evolved"] = now.isoformat()
    if level:
        state["level"] = level
    else:
        # 自动递增层级 L1 -> L9
        try:
            cur = int(str(state.get("level", "L1")).lstrip("L") or 1)
        except ValueError:
            cur = 1
        state["level"] = "L%d" % min(cur + 1, 9)
    write_state(state)
    print("[已更新] 知识库口径 → %s，层级 → %s" % (state["snapshot"], state["level"]))
    return 0


def main():
    parser = argparse.ArgumentParser(description="番茄爆款小说专家知识库月度进化脚本")
    parser.add_argument("--check", action="store_true", help="检查知识库时效")
    parser.add_argument("--report", nargs="?", const="进化报告.md", help="生成进化报告（可指定文件名）")
    parser.add_argument("--touch", action="store_true", help="完成进化后写入新口径日期")
    parser.add_argument("--snapshot", help="配合 --touch 指定口径日期，如 2026-10")
    parser.add_argument("--level", help="配合 --touch 指定层级，如 L6")
    args = parser.parse_args()

    state = read_state()

    if not (args.check or args.report or args.touch):
        args.check = True

    code = 0
    if args.check:
        code = max(code, cmd_check(state))
    if args.report:
        cmd_report(state, args.report)
    if args.touch:
        cmd_touch(state, args.snapshot, args.level)

    sys.exit(2 if (args.check and code == 2 and not (args.report or args.touch)) else 0)


if __name__ == "__main__":
    main()
