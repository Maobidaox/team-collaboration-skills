#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
evolution_fetcher.py — 番茄爆款小说专家 · 增强联网情报抓取器（纯标准库，v2 八路版）

定位：本专家的"增强联网搜索"**治理层**。不直接抓取（抓取由 live_research.py 负责），
      而是生成**结构化检索任务清单**交由 Agent（具备 WebSearch/WebFetch）执行，
      并对回收的情报做**差异比对**与**落库建议**，驱动知识库月度进化。

v2 升级：检索矩阵由 5 路扩为 8 路（政策/平台/赛道/算法/方法论/收益/IP/合规），
         高变动核验项由 9 项扩为 12 项，targets 全部对齐 48 份 references 实际文件名。

为什么这样设计：
  - 专家包内的脚本必须零第三方依赖、零机器专属路径、可在任意沙箱运行；
  - 联网动作由宿主 Agent 完成（它有 WebSearch/WebFetch），脚本负责"设计检索 + 治理结果"；
  - 直连抓取能力的补充见同目录 live_research.py（可真实 HTTP 抓取，失败自动降级）。

用法：
  # 生成本月全部检索任务（JSON + Markdown 两种格式）
  python evolution_fetcher.py --plan --month 2026-10

  # 只生成某一路
  python evolution_fetcher.py --plan --track policy
  python evolution_fetcher.py --plan --track trending
  python evolution_fetcher.py --plan --track ip

  # 记录一条回收的情报
  python evolution_fetcher.py --record --track policy --title "xxx" --source "url" --summary "..." --impact 27,30

  # 生成本月进化报告骨架
  python evolution_fetcher.py --report --month 2026-10

  # 查看当前情报台账
  python evolution_fetcher.py --list
"""

import argparse
import json
import os
import sys
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(HERE)
LEDGER = os.path.join(BASE, "evolution_intel.json")

# ============ 八路检索矩阵（每月执行，v2 升级：5 路 → 8 路） ============
TRACKS = {
    "policy": {
        "name": "平台政策路",
        "desc": "番茄官方规则变更：签约、全勤、福利焕新、奖项、治理公告",
        "queries": [
            "番茄小说 {m} 福利 新规 全勤 听读 门槛 调整",
            "番茄小说 完本签约 模式 规则 {y}",
            "番茄小说 品质臻选奖 门槛 金额 {y}",
            "番茄小说 作家专区 公告 {y}年{m月}月",
            "番茄小说 星火计划 星燃计划 档位 {y}",
        ],
        "targets": ["27-2026年9月福利焕新逐条拆解与新旧对比.md", "28-完本签约模式全解与作战手册2026.md",
                    "29-品质臻选奖与高价值奖项作战2026.md", "30-全勤新规三阶段通关与门槛精算2026.md",
                    "31-星火计划与星燃计划收益最大化2026.md", "02-2026签约全勤与收益体系及10月新规切换.md"],
        "sources_hint": ["番茄作家专区 fanqienovel.com/writer/zone", "第一网文报", "今日头条行业号", "网文666"],
    },
    "platform": {
        "name": "平台机制路",
        "desc": "推荐评估 / 验证期 / 首秀 / 签约节点等平台机制变化",
        "queries": [
            "番茄小说 推荐评估 验证期 首秀 机制 {y}",
            "番茄小说 签约 节点 2万 5万 8万 {y}",
            "番茄小说 流量池 分层 三关制 {y}",
        ],
        "targets": ["01-番茄流量池与三关制推荐机制2026.md", "32-后台数据漏斗与九大核心指标精算2026.md"],
        "sources_hint": ["番茄官方帮助中心", "爱企查行业解读", "作者实测经验贴"],
    },
    "trending": {
        "name": "赛道风向路",
        "desc": "巅峰榜 / 阅读榜 / 新书榜实时数据，题材分布与新兴赛道",
        "queries": [
            "番茄小说 {y}年{m}月 巅峰榜 TOP30 题材",
            "番茄小说 {y}年{m}月 首秀榜 男频 女频 TOP20",
            "番茄小说 阅读榜 在读 数据 {y}年{m}月",
            "网文 {y}年{m}月 新书 风向 冷门赛道 机会",
        ],
        "targets": ["06-2026番茄赛道地图与风口雷达.md", "07-男频爆款赛道公式库2026.md",
                    "08-女频爆款赛道公式库2026.md", "46-都市高武与脑洞异能深度拆解2026.md",
                    "47-悬疑无限流与规则怪谈深度拆解2026.md", "48-巅峰榜对标拆书案例库2026-09.md"],
        "sources_hint": ["番茄小说官网巅峰榜 fanqienovel.com", "中国网文研究室", "网文行业公众号"],
    },
    "algorithm": {
        "name": "算法机制路",
        "desc": "推荐算法、流量池权重、完读/追读权重、eCPM 等算法侧变化",
        "queries": [
            "番茄小说 推荐机制 算法 流量池 {y}",
            "番茄小说 完读率 追读率 权重 红线 {y}",
            "番茄小说 eCPM 单价 波动 {y}",
            "番茄小说 老书 限流 新书 倾斜 {y}",
        ],
        "targets": ["01-番茄流量池与三关制推荐机制2026.md", "32-后台数据漏斗与九大核心指标精算2026.md",
                    "33-eCPM广告变现与单价波动应对2026.md"],
        "sources_hint": ["行业分析文章", "作者实测数据贴", "DataEye研究院"],
    },
    "method": {
        "name": "创作方法论路",
        "desc": "网文创作新方法、新结构、新爽点模型、开局技法",
        "queries": [
            "网文 创作 方法论 爽点 节奏 结构 {y}",
            "番茄小说 爆款 拆书 开篇 技巧 {y}",
            "网文 情感 代入感 情绪价值 {y}",
        ],
        "targets": ["05-爆款基因逆向工程六步法.md", "10-黄金三章工程化SOP.md",
                    "42-前200字黄金公式库与开局诊断.md", "43-多线程叙事与伏笔回收工程.md",
                    "44-情绪价值与代入感设计2026.md", "45-爽点密度与节奏变速控制器.md"],
        "sources_hint": ["网文写作教程", "作者经验分享", "行业研究"],
    },
    "income": {
        "name": "收益变现路",
        "desc": "全勤/星火/星燃/臻选金额门槛、单价口径、收益模型",
        "queries": [
            "番茄小说 全勤 优质档 8000 门槛 {y}",
            "番茄小说 听读分成 单价 万字 {y}",
            "番茄小说 福利 拟获奖 公示 {y}年{m月}月",
        ],
        "targets": ["30-全勤新规三阶段通关与门槛精算2026.md", "31-星火计划与星燃计划收益最大化2026.md",
                    "35-万字有效阅读与听读收益精算模型2026.md", "33-eCPM广告变现与单价波动应对2026.md"],
        "sources_hint": ["番茄作者后台结算口径", "作者实测收益贴"],
    },
    "ip": {
        "name": "IP 变现路",
        "desc": "短剧/漫剧/有声/出版改编、版权售卖、IP 扶持计划",
        "queries": [
            "番茄小说 短剧 改编 版权 奖励 {y}",
            "番茄小说 漫剧 改编 数量 增长 {y}",
            "番茄小说 IP 护航计划 版权保底 {y}",
            "番茄小说 短剧 IP 联合征文 {y}",
        ],
        "targets": ["36-短剧改编工业化与爆款之源作战2026.md", "37-漫剧改编与有声书变现2026.md",
                    "38-IP版权售卖分账与百万IP护航计划.md"],
        "sources_hint": ["番茄官方 IP 活动页", "中国发展网/新浪财经行业报道"],
    },
    "compliance": {
        "name": "合规风控路",
        "desc": "内容治理、AI 检测、版权、敏感题材的最新口径",
        "queries": [
            "番茄小说 低质 治理 公告 {y}年{m月}月 拒签 下架",
            "AI 写作 网文平台 检测 处罚 规范 {y}",
            "网络文学 反洗稿 自律公约 {y}",
            "AI 生成内容 标识 办法 文字 {y}",
        ],
        "targets": ["04-内容治理红线与低质判定避坑2026.md", "39-AI痕迹检测维度与反检测生存指南2026.md",
                    "40-反洗稿自律公约与原创证据链管理.md", "41-AI辅助创作合规边界与协作范式2026.md"],
        "sources_hint": ["番茄官方治理公告", "第一财经/界面新闻", "16 家平台自律公约"],
    },
}

# ============ 必须月度核验的"高变动项"（v2：9 → 12 项） ============
HIGH_VOLATILITY = [
    ("全勤奖三阶段门槛与金额", "27/30", "听读门槛、月更字数、分成比例、上限 8000"),
    ("星火/星燃计划档位", "31", "固定奖励金额、收益加成比例、收益门槛 1000"),
    ("品质臻选奖门槛", "29", "听读收益门槛与 15% 比例、10 万上限"),
    ("完本签约核算周期", "28", "完本字数 → 3/6/12 个月周期对应关系"),
    ("起笔扬帆奖 / 品质成就奖", "28", "30 天听读 300 门槛、10 万字完读率 18% 门槛"),
    ("推荐评估与验证期节点", "32", "8 万字评估、7 天验证、10 万首秀是否调整"),
    ("数据红线", "32", "完读率 15%、追读率 35%、吸量 400 是否调整"),
    ("eCPM 单价区间", "33", "千次阅读单价区间是否变化"),
    ("巅峰榜与题材分布", "48", "每周级变化，至少月度更新"),
    ("AI 治理口径与处置量级", "39", "月度公示数据、检测维度、梯度处置"),
    ("短剧/漫剧改编激励", "36/37", "版权奖励金额与条件"),
    ("IP 护航计划档位", "38", "保底金额与申请门槛"),
]


def _now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _month_ctx(month=None):
    if not month:
        now = datetime.now()
        return now.year, now.month
    y, m = month.split("-")[:2]
    return int(y), int(m)


def cmd_plan(args):
    y, m = _month_ctx(args.month)
    tracks = [args.track] if args.track else list(TRACKS.keys())
    plan = {"generated": _now(), "target_month": f"{y}-{m:02d}", "tracks": []}

    lines = [f"# 番茄创作专家 · 月度增强联网检索任务清单",
             f"",
             f"**目标月份**：{y} 年 {m} 月　　**生成时间**：{_now()}",
             f"**执行者**：宿主 Agent（WebSearch / WebFetch）　　**回收**：`evolution_fetcher.py --record`",
             f"",
             f"> 本清单由 `evolution_fetcher.py --plan` 生成，是「增强联网搜索」的**执行脚本**。",
             f"> Agent 应逐条执行检索，回收结果后运行 `--record` 落账，再由 `monthly_evolution.py` 驱动改写。",
             f""]

    for i, tk in enumerate(tracks, 1):
        t = TRACKS[tk]
        lines.append(f"\n## 第 {i} 路 · {t['name']}（{tk}）\n")
        lines.append(f"**目标**：{t['desc']}\n")
        lines.append(f"**建议信源**：{' / '.join(t['sources_hint'])}\n")
        lines.append("**检索词（逐条执行）**：\n")
        qs = []
        for q in t["queries"]:
            qq = q.format(y=y, m=m, m月=m, year=y)
            qs.append(qq)
            lines.append(f"- [ ] `{qq}`")
        lines.append(f"\n**命中后需更新的知识文件**：\n")
        for f in t["targets"]:
            lines.append(f"- `{f}`")
        plan["tracks"].append({"key": tk, "name": t["name"], "queries": qs, "targets": t["targets"]})

    lines.append(f"\n---\n\n## ⚠️ 高变动项强制核验清单（本月必查）\n")
    lines.append(f"| 项目 | 影响文件 | 核验要点 |")
    lines.append(f"|---|---|---|")
    for name, files, note in HIGH_VOLATILITY:
        lines.append(f"| {name} | {files} | {note} |")

    lines.append(f"\n---\n\n## 执行顺序建议（八路）\n")
    lines.append(f"1. 先跑 `policy` 与 `compliance` 两路（规则类，变动影响最大）")
    lines.append(f"2. 再跑 `income` 与 `ip` 两路（钱与变现，用户最关心）")
    lines.append(f"3. 再跑 `trending`（赛道风向，决定创作建议时效性）")
    lines.append(f"4. 最后跑 `platform` / `algorithm` / `method`（机制与方法论类，变动较慢）")
    lines.append(f"5. 可先用 `live_research.py --sniff` 探测直连能力；可直连时用 `live_research.py --crawl` 真抓")
    lines.append(f"6. 每条命中情报执行：`evolution_fetcher.py --record --track <路> --title ... --source ... --summary ... --impact <文件号>`")
    lines.append(f"7. 全部回收后执行：`monthly_evolution.py --touch` 完成口径更新与层级递增")

    md_path = os.path.join(BASE, f"evolution_plan_{y}{m:02d}.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    if args.json:
        jp = os.path.join(BASE, f"evolution_plan_{y}{m:02d}.json")
        with open(jp, "w", encoding="utf-8") as f:
            json.dump(plan, f, ensure_ascii=False, indent=2)
        print(f"[OK] JSON 任务清单：{jp}")

    print(f"[OK] Markdown 任务清单：{md_path}")
    print(f"[OK] 共 {len(tracks)} 路、{sum(len(TRACKS[t]['queries']) for t in tracks)} 条检索词、{len(HIGH_VOLATILITY)} 项高变动核验")
    return 0


def _load_ledger():
    if os.path.exists(LEDGER):
        try:
            with open(LEDGER, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"records": [], "history": []}


def _save_ledger(d):
    with open(LEDGER, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)


def cmd_record(args):
    d = _load_ledger()
    rec = {
        "id": f"INTEL-{len(d['records']) + 1:04d}",
        "date": _now(),
        "track": args.track,
        "title": args.title,
        "source": args.source,
        "summary": args.summary,
        "impact": [x.strip() for x in args.impact.split(",")] if args.impact else [],
        "severity": args.severity,
        "applied": False,
    }
    d["records"].append(rec)
    _save_ledger(d)
    print(f"[OK] 已记录 {rec['id']}：{args.title}")
    print(f"     路向={args.track} 严重度={args.severity} 影响文件={rec['impact']}")
    if args.severity == "critical":
        print(f"     ⚠️ 严重变更：建议立即执行 monthly_evolution.py --apply 更新知识库")
    return 0


def cmd_list(args):
    d = _load_ledger()
    if not d["records"]:
        print("（暂无情报记录）")
        return 0
    print(f"{'ID':<12}{'日期':<12}{'路向':<14}{'级':<8}{'标题'}")
    print("-" * 90)
    for r in d["records"][-50:]:
        sev = {"critical": "🔴严重", "major": "🟠重要", "minor": "🟡一般"}.get(r["severity"], r["severity"])
        print(f"{r['id']:<12}{r['date'][:10]:<12}{r['track']:<14}{sev:<8}{r['title'][:40]}")
    print(f"\n共 {len(d['records'])} 条，未应用 {sum(1 for r in d['records'] if not r['applied'])} 条")
    return 0


def cmd_report(args):
    y, m = _month_ctx(args.month)
    d = _load_ledger()
    recs = [r for r in d["records"] if r["date"].startswith(f"{y}-{m:02d}")]
    path = os.path.join(BASE, f"进化报告_{y}{m:02d}.md")
    L = [f"# 番茄爆款小说专家 · {y} 年 {m} 月进化报告",
         f"",
         f"**生成时间**：{_now()}",
         f"**数据口径**：{y}-{m:02d}",
         f"**本轮情报**：{len(recs)} 条",
         f"",
         f"## 一、本轮检索覆盖",
         f"",
         f"| 路向 | 检索词数 | 命中情报 |",
         f"|---|---|---|"]
    for tk, t in TRACKS.items():
        n = sum(1 for r in recs if r["track"] == tk)
        L.append(f"| {t['name']}（{tk}） | {len(t['queries'])} | {n} |")
    L += [f"", f"## 二、重要变更", f""]
    if recs:
        for r in recs:
            if r["severity"] in ("critical", "major"):
                L.append(f"### {r['id']} · {r['title']}")
                L.append(f"- 来源：{r['source']}（{r['date'][:10]}）")
                L.append(f"- 摘要：{r['summary']}")
                L.append(f"- 影响文件：{', '.join(r['impact']) or '待定'}")
                L.append(f"")
    else:
        L.append(f"（本轮暂无 critical/major 级变更）")
        L.append(f"")
    L += [f"## 三、知识库变更", f"", f"（由 monthly_evolution.py --apply 执行后回填）", f"",
          f"## 四、输出能力提升", f"", f"（本轮进化带来的能力增强）", f"",
          f"## 五、下轮重点", f"",
          f"- 持续核验：{', '.join(n for n, _, _ in HIGH_VOLATILITY[:5])}",
          f""]
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(L) + "\n")
    print(f"[OK] 进化报告骨架：{path}")
    return 0


def main():
    p = argparse.ArgumentParser(description="番茄创作专家·增强联网情报抓取器")
    p.add_argument("--plan", action="store_true", help="生成月度检索任务清单")
    p.add_argument("--record", action="store_true", help="记录一条回收情报")
    p.add_argument("--list", action="store_true", help="查看情报台账")
    p.add_argument("--report", action="store_true", help="生成进化报告骨架")
    p.add_argument("--month", help="目标月份 YYYY-MM")
    p.add_argument("--track", choices=list(TRACKS.keys()), help="指定路向")
    p.add_argument("--title", help="情报标题")
    p.add_argument("--source", help="来源 URL / 媒体")
    p.add_argument("--summary", help="情报摘要")
    p.add_argument("--impact", help="影响的知识文件号，逗号分隔，如 02,03")
    p.add_argument("--severity", choices=["critical", "major", "minor"], default="major")
    p.add_argument("--json", action="store_true", help="同时输出 JSON 清单")
    args = p.parse_args()

    if args.plan:
        return cmd_plan(args)
    if args.record:
        if not all([args.track, args.title, args.summary]):
            print("[ERR] --record 需要 --track / --title / --summary")
            return 1
        return cmd_record(args)
    if args.list:
        return cmd_list(args)
    if args.report:
        return cmd_report(args)
    p.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
