#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
live_research.py — 番茄爆款小说专家 · 增强联网检索执行器（纯标准库）

定位：本专家的"增强联网搜索"**执行引擎**（v2 新增，与 evolution_fetcher.py 互补）。
  - evolution_fetcher.py 负责"设计检索任务 + 治理回收情报"；
  - live_research.py 负责"**真的去抓**"——尝试用标准库 urllib 抓取指定信源，
    解析标题/正文摘要/时间戳，落盘为情报卡，并做**时效判定与差异比对**。

设计原则：
  - 纯标准库（urllib / json / re / html / datetime / argparse），零第三方依赖；
  - **零联网也能跑**：网络不可用时自动降级为"生成检索清单 + 离线情报卡骨架"；
  - 无机器专属路径，可在任意沙箱运行。

用法：
  # 1) 探测联网能力
  python live_research.py --sniff

  # 2) 抓取一个信源（真联网）
  python live_research.py --fetch "https://fanqienovel.com/writer/zone" --tag policy

  # 3) 批量抓取内置信源清单
  python live_research.py --crawl --tag policy --limit 5

  # 4) 生成八路检索关键词矩阵（交给宿主 Agent 的 WebSearch 执行）
  python live_research.py --keywords --month 2026-10

  # 5) 查看已落盘情报卡
  python live_research.py --list

  # 6) 时效判定：距上次口径的月份差与是否需进化
  python live_research.py --freshness
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime, date

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(HERE)
INTEL_DIR = os.path.join(BASE, "research_intel")
STATE_FILE = os.path.join(BASE, ".evolution_state")

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/122.0 Safari/537.36")

# ============ 内置信源清单（八路） ============
SOURCES = {
    "policy": [
        ("番茄作家专区", "https://fanqienovel.com/writer/zone"),
        ("番茄小说官网公告", "https://fanqienovel.com/writer/zone/article"),
    ],
    "platform": [
        ("番茄小说首页", "https://fanqienovel.com/"),
    ],
    "trending": [
        ("番茄巅峰榜", "https://fanqienovel.com/rank"),
        ("番茄书城分类榜", "https://fanqienovel.com/library"),
    ],
    "algorithm": [
        ("番茄作者后台帮助", "https://fanqienovel.com/writer/zone/help"),
    ],
    "method": [
        ("中国网文研究室", "https://www.toutiao.com/"),
    ],
    "income": [
        ("番茄福利公告", "https://fanqienovel.com/writer/zone/article"),
    ],
    "ip": [
        ("番茄短剧/漫剧合作", "https://fanqienovel.com/writer/zone"),
    ],
    "compliance": [
        ("番茄低质治理公告", "https://fanqienovel.com/writer/zone/article"),
    ],
}

# ============ 八路检索关键词矩阵（月度执行） ============
KEYWORD_MATRIX = {
    "policy": [
        "番茄小说 {y}年{m}月 福利 新规 全勤 听读 门槛",
        "番茄小说 完本签约 模式 规则 {y}",
        "番茄小说 作家专区 公告 {y}年{m}月",
    ],
    "platform": [
        "番茄小说 推荐评估 验证期 首秀 {y}",
        "番茄小说 签约 节点 2万 5万 8万 {y}",
    ],
    "trending": [
        "番茄小说 {y}年{m}月 巅峰榜 TOP30 题材",
        "番茄小说 首秀榜 男频 女频 {y}年{m}月",
        "网文 {y}年{m}月 新书 风向 冷门赛道",
    ],
    "algorithm": [
        "番茄小说 推荐机制 算法 流量池 {y}",
        "番茄小说 完读率 追读率 权重 {y}",
        "番茄小说 eCPM 单价 波动 {y}",
    ],
    "method": [
        "网文 创作 方法论 爽点 节奏 结构 {y}",
        "番茄小说 爆款 拆书 开篇 技巧 {y}",
        "AI 辅助 网文 写作 合规 玩法 {y}年{m}月",
    ],
    "income": [
        "番茄小说 星火计划 星燃计划 金额 {y}",
        "番茄小说 品质臻选奖 门槛 {y}",
        "番茄小说 全勤 优质档 8000 {y}",
    ],
    "ip": [
        "番茄小说 短剧 改编 版权 奖励 {y}",
        "番茄小说 漫剧 改编 数量 {y}",
        "番茄小说 IP 护航计划 版权保底 {y}",
    ],
    "compliance": [
        "番茄小说 低质 治理 公告 {y}年{m}月",
        "AI 写作 网文平台 检测 处罚 {y}",
        "网络文学 反洗稿 自律公约 {y}",
    ],
}

# ============ 高变动项（每月必查） ============
HIGH_VOLATILITY = [
    ("全勤奖三阶段门槛与金额", "27/30", "听读门槛、月更字数、分成比例、上限 8000"),
    ("星火/星燃计划档位", "31", "固定奖励金额、收益加成比例、收益门槛"),
    ("品质臻选奖门槛", "29", "听读收益门槛与 15% 比例"),
    ("完本签约核算周期", "28", "完本字数 → 3/6/12 个月周期对应关系"),
    ("推荐评估与验证期节点", "32", "8 万字评估、7 天验证、10 万首秀是否调整"),
    ("数据红线", "32", "完读率 15%、追读率 35% 是否调整"),
    ("eCPM 单价区间", "33", "千次阅读单价区间是否变化"),
    ("巅峰榜与题材分布", "48", "每周级变化，至少月度更新"),
    ("AI 治理口径与处置量级", "39", "月度公示数据、检测维度"),
    ("短剧/漫剧改编激励", "36/37", "版权奖励金额与条件"),
]


def _now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _ensure_dir():
    if not os.path.isdir(INTEL_DIR):
        os.makedirs(INTEL_DIR)


def _read_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"snapshot": "2026-09", "level": "L1"}


# ---------------- 1) 联网探测 ----------------
def cmd_sniff(args):
    print("=" * 62)
    print("增强联网能力探测")
    print("=" * 62)
    ok = False
    detail = ""
    try:
        import urllib.request
        req = urllib.request.Request("https://fanqienovel.com/", headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=8) as r:
            data = r.read(2048)
            ok = True
            detail = "HTTP %s，返回 %d 字节" % (getattr(r, "status", "?"), len(data))
    except Exception as e:
        detail = "%s: %s" % (type(e).__name__, str(e)[:120])
    print("直连抓取能力 : %s" % ("✅ 可用" if ok else "❌ 不可用（将降级为检索清单模式）"))
    print("探测详情     : %s" % detail)
    print("降级策略     : 生成结构化检索清单 → 由宿主 Agent(WebSearch/WebFetch) 执行 → 回收落盘")
    print("=" * 62)
    return 0 if ok else 2


# ---------------- 2) 抓取单页 ----------------
def _extract(html_text):
    """从 HTML 中提取 title 与纯文本摘要（纯标准库，无第三方解析器）。"""
    title = ""
    m = re.search(r"<title[^>]*>(.*?)</title>", html_text, re.I | re.S)
    if m:
        title = re.sub(r"\s+", " ", m.group(1)).strip()
    body = re.sub(r"(?is)<(script|style|noscript)[^>]*>.*?</\1>", " ", html_text)
    body = re.sub(r"(?s)<[^>]+>", " ", body)
    body = re.sub(r"&nbsp;", " ", body)
    body = re.sub(r"&amp;", "&", body)
    body = re.sub(r"&lt;", "<", body)
    body = re.sub(r"&gt;", ">", body)
    body = re.sub(r"\s+", " ", body).strip()
    return title, body


def _fetch_one(url):
    import urllib.request
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=12) as r:
        raw = r.read()
    for enc in ("utf-8", "gbk", "gb18030"):
        try:
            return raw.decode(enc)
        except Exception:
            continue
    return raw.decode("utf-8", errors="ignore")


def cmd_fetch(args):
    _ensure_dir()
    url = getattr(args, "fetch", None) or getattr(args, "url", None)
    if not url:
        print("[ERR] 缺少 URL")
        return 1
    tag = getattr(args, "tag", None) or "misc"
    print("[抓取] %s" % url)
    try:
        html_text = _fetch_one(url)
        title, body = _extract(html_text)
        ok = True
        err = ""
    except Exception as e:
        title, body, ok, err = "", "", False, "%s: %s" % (type(e).__name__, str(e)[:160])

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    card = {
        "id": "LR-%s" % stamp,
        "fetched_at": _now(),
        "tag": tag,
        "url": url,
        "ok": ok,
        "error": err,
        "title": title,
        "excerpt": body[:3000],
        "excerpt_len": len(body),
    }
    p = os.path.join(INTEL_DIR, "intel_%s_%s.json" % (tag, stamp))
    with open(p, "w", encoding="utf-8") as f:
        json.dump(card, f, ensure_ascii=False, indent=2)

    md = os.path.join(INTEL_DIR, "intel_%s_%s.md" % (tag, stamp))
    with open(md, "w", encoding="utf-8", newline="\n") as f:
        f.write("# 情报卡 %s\n\n" % card["id"])
        f.write("- 抓取时间：%s\n- 路向：%s\n- 来源：%s\n- 状态：%s\n\n"
                % (card["fetched_at"], tag, url, "成功" if ok else "失败（%s）" % err))
        f.write("## 标题\n\n%s\n\n## 正文摘要\n\n%s\n" % (title or "(未取到)", body[:3000] or "(未取到)"))

    if ok:
        print("[OK] 情报卡：%s（标题：%s，正文 %d 字）" % (md, title[:50] or "(无)", len(body)))
    else:
        print("[降级] 抓取失败：%s" % err)
        print("       已生成离线情报卡骨架：%s" % md)
        print("       请改用宿主 Agent 的 WebSearch/WebFetch 检索该来源，再回填内容。")
    return 0 if ok else 2


def cmd_crawl(args):
    _ensure_dir()
    items = SOURCES.get(args.tag) or [x for v in SOURCES.values() for x in v]
    if args.limit:
        items = items[: args.limit]
    okn = 0
    for name, url in items:
        print("-" * 50)
        print("[%s] %s" % (name, url))
        ns = argparse.Namespace(url=url, tag=args.tag or "misc")
        if cmd_fetch(ns) == 0:
            okn += 1
    print("=" * 50)
    print("[汇总] 共 %d 个来源，成功 %d 个" % (len(items), okn))
    if okn == 0:
        print("[提示] 全部直连失败 → 已降级为离线模式，请用 Agent 联网检索。")
    return 0


# ---------------- 3) 关键词矩阵 ----------------
def cmd_keywords(args):
    m = args.month
    if m:
        y, mm = m.split("-")[:2]
        y, mm = int(y), int(mm)
    else:
        y, mm = datetime.now().year, datetime.now().month
    lines = ["# 番茄爆款小说专家 · 增强联网检索关键词矩阵", "",
             "**目标月份**：%d 年 %d 月　　**生成时间**：%s" % (y, mm, _now()),
             "**执行者**：宿主 Agent（WebSearch / WebFetch）", "",
             "> 逐条执行检索 → 命中后运行 `evolution_fetcher.py --record` 落账 → `monthly_evolution.py --apply` 驱动改写。", ""]
    total = 0
    for i, (tk, qs) in enumerate(KEYWORD_MATRIX.items(), 1):
        lines.append("## 第 %d 路 · %s" % (i, tk))
        lines.append("")
        for q in qs:
            qq = q.format(y=y, m=mm)
            total += 1
            lines.append("- [ ] `%s`" % qq)
        lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## ⚠️ 高变动项强制核验（本月必查）")
    lines.append("")
    lines.append("| 项目 | 影响文件 | 核验要点 |")
    lines.append("|---|---|---|")
    for n, f_, note in HIGH_VOLATILITY:
        lines.append("| %s | %s | %s |" % (n, f_, note))
    lines.append("")
    out = args.out or os.path.join(BASE, "research_keywords_%d%02d.md" % (y, mm))
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")
    print("[OK] 关键词矩阵：%s" % out)
    print("[OK] 共 %d 路、%d 条检索词、%d 项高变动核验" % (len(KEYWORD_MATRIX), total, len(HIGH_VOLATILITY)))
    return 0


# ---------------- 4) 情报卡列表 ----------------
def cmd_list(args):
    if not os.path.isdir(INTEL_DIR):
        print("（暂无情报卡）")
        return 0
    files = sorted([x for x in os.listdir(INTEL_DIR) if x.endswith(".json")])
    if not files:
        print("（暂无情报卡）")
        return 0
    print("%-26s %-12s %-10s %s" % ("ID", "时间", "路向", "标题"))
    print("-" * 90)
    for fn in files[-50:]:
        try:
            with open(os.path.join(INTEL_DIR, fn), "r", encoding="utf-8") as f:
                c = json.load(f)
            print("%-26s %-12s %-10s %s" % (c.get("id", ""), c.get("fetched_at", "")[:10],
                                            c.get("tag", ""), (c.get("title") or "")[:36]))
        except Exception:
            pass
    print("\n共 %d 张情报卡（最近 50 张）" % len(files))
    return 0


# ---------------- 5) 时效判定 ----------------
def cmd_freshness(args):
    st = _read_state()
    snap = st.get("snapshot", "2026-09")
    now = date.today()
    cur = "%04d-%02d" % (now.year, now.month)

    def to_m(s):
        y, m = s.split("-")[:2]
        return int(y) * 12 + int(m)

    gap = abs(to_m(cur) - to_m(snap))
    print("=" * 62)
    print("知识库时效判定")
    print("=" * 62)
    print("当前日期       : %s" % now.isoformat())
    print("知识库口径     : %s" % snap)
    print("当前档期       : %s" % cur)
    print("相差月份       : %d" % gap)
    print("进化层级       : %s" % st.get("level", "L1"))
    print("-" * 62)
    if gap >= 1:
        print("[需要进化] 已跨月 → 执行八路检索 → 更新 references → --touch")
        return 2
    print("[时效正常] 处于当月最新口径")
    return 0


def main():
    p = argparse.ArgumentParser(description="番茄爆款小说专家 · 增强联网检索执行器（纯标准库）")
    p.add_argument("--sniff", action="store_true", help="探测直连抓取能力")
    p.add_argument("--fetch", metavar="URL", help="抓取单个 URL 并落盘情报卡")
    p.add_argument("--crawl", action="store_true", help="批量抓取内置信源")
    p.add_argument("--keywords", action="store_true", help="生成八路检索关键词矩阵")
    p.add_argument("--list", action="store_true", help="查看已落盘情报卡")
    p.add_argument("--freshness", action="store_true", help="时效判定")
    p.add_argument("--tag", help="路向标签（policy/platform/trending/algorithm/method/income/ip/compliance）")
    p.add_argument("--limit", type=int, help="批量抓取上限")
    p.add_argument("--month", help="目标月份 YYYY-MM")
    p.add_argument("--out", help="关键词矩阵输出路径")
    args = p.parse_args()

    if args.sniff:
        return cmd_sniff(args)
    if args.fetch:
        return cmd_fetch(args)
    if args.crawl:
        return cmd_crawl(args)
    if args.keywords:
        return cmd_keywords(args)
    if args.list:
        return cmd_list(args)
    if args.freshness:
        return cmd_freshness(args)
    p.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
