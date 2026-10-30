#!/usr/bin/env python3
"""证据账本 — 电商视觉策略的机械门禁。

把「证据优先于一切转化技巧」从口号变成可执行的检查：
最终稿只允许 confirmed / derived；pending 必须降级或补证；forbidden 永不出现。

用法：
  claims.py --project DIR init
  claims.py --project DIR add C1 --claim "承重约 20kg" --source "参数表" --status confirmed
  claims.py --project DIR add C2 --claim "抗菌率 99%" --status pending --note "需检测报告"
  claims.py --project DIR promote C2 --source "SGS SH2024-xxx 报告第 3 页"
  claims.py --project DIR ban C3 --reason "普通食品不得宣称治疗"
  claims.py --project DIR list [--status pending]
  claims.py --project DIR check          # 有 pending/forbidden 时退出码 1
  claims.py --project DIR export         # 输出 Markdown 表

状态：
  confirmed  用户资料/可靠来源直接支持
  derived    可由已确认事实合理翻译，但不得扩大含义
  pending    待补证：需检测、认证、规则或批准范围
  forbidden  禁止：编造、误导、越权功效、虚假背书
"""
import argparse
import json
import os
import sys
from datetime import datetime

STATUSES = ("confirmed", "derived", "pending", "forbidden")
BLOCKING = ("pending", "forbidden")
LABEL = {
    "confirmed": "已确认",
    "derived": "有依据",
    "pending": "待补证",
    "forbidden": "禁止",
}


def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M")


def path_of(root):
    return os.path.join(root, "claims.json")


def load(root):
    p = path_of(root)
    if not os.path.exists(p):
        sys.exit(f"未初始化：{root} 下没有 claims.json，先跑 init")
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def save(root, data):
    data["updated"] = now()
    tmp = path_of(root) + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path_of(root))


def find(data, cid):
    for c in data["claims"]:
        if c["id"] == cid:
            return c
    return None


def touch(c, status, note=""):
    c["status"] = status
    c["history"].append({"at": now(), "status": status, "note": note})


# ---------- 命令 ----------

def cmd_init(a):
    os.makedirs(a.project, exist_ok=True)
    if os.path.exists(path_of(a.project)):
        sys.exit(f"已存在：{path_of(a.project)}（如需重来请先删除）")
    save(a.project, {"created": now(), "claims": []})
    print(f"已初始化证据账本：{path_of(a.project)}")


def cmd_add(a):
    data = load(a.project)
    if find(data, a.id):
        sys.exit(f"宣称编号已存在：{a.id}（改用 promote / ban 更新状态）")
    if a.status in ("confirmed", "derived") and not a.source:
        sys.exit(f"{LABEL[a.status]}状态必须给出 --source，否则无法追溯")
    if a.status == "forbidden" and not a.note:
        sys.exit("禁止状态必须给出 --note 说明原因")
    rec = {
        "id": a.id,
        "claim": a.claim,
        "source": a.source or "",
        "status": a.status,
        "note": a.note or "",
        "history": [{"at": now(), "status": a.status, "note": "创建"}],
    }
    data["claims"].append(rec)
    save(a.project, data)
    print(f"已登记 {a.id} → {LABEL[a.status]}")


def cmd_promote(a):
    data = load(a.project)
    c = find(data, a.id)
    if not c:
        sys.exit(f"未找到宣称：{a.id}")
    if not a.source:
        sys.exit("补证必须给出 --source（来源名称/报告号/条款位置）")
    c["source"] = a.source
    if a.note:
        c["note"] = a.note
    touch(c, "confirmed", "补证通过")
    save(a.project, data)
    print(f"{a.id} → 已确认（来源：{a.source}）")


def cmd_ban(a):
    data = load(a.project)
    c = find(data, a.id)
    if not c:
        sys.exit(f"未找到宣称：{a.id}")
    c["note"] = a.reason
    touch(c, "forbidden", "列入禁止")
    save(a.project, data)
    print(f"{a.id} → 禁止（{a.reason}）")


def cmd_list(a):
    data = load(a.project)
    rows = data["claims"]
    if a.status:
        rows = [c for c in rows if c["status"] == a.status]
    if not rows:
        print("（无匹配条目）")
        return
    for c in rows:
        src = f" | 来源：{c['source']}" if c["source"] else ""
        note = f" | 备注：{c['note']}" if c["note"] else ""
        print(f"[{LABEL[c['status']]}] {c['id']}: {c['claim']}{src}{note}")
    tally = {}
    for c in data["claims"]:
        tally[c["status"]] = tally.get(c["status"], 0) + 1
    print("\n合计：" + "，".join(f"{LABEL[k]} {v}" for k, v in tally.items()))


def cmd_check(a):
    data = load(a.project)
    bad = [c for c in data["claims"] if c["status"] in BLOCKING]
    if not data["claims"]:
        print("⚠️  账本为空：本次输出若含事实/数据/效果/资质宣称，必须先进账本")
        sys.exit(1)
    if bad:
        print("⛔ 门禁未通过，以下宣称不得进入最终稿：\n")
        for c in bad:
            print(f"  [{LABEL[c['status']]}] {c['id']}: {c['claim']}")
        print("\n处理方式：补证后 promote，或改写为中性表达，或删除。")
        sys.exit(1)
    ok = sum(1 for c in data["claims"] if c["status"] in ("confirmed", "derived"))
    print(f"✅ 门禁通过：{ok} 条宣称均可追溯，无待补证/禁止项")


def cmd_export(a):
    data = load(a.project)
    print("| 编号 | 宣称/卖点 | 来源 | 状态 | 最终处理 |")
    print("|---|---|---|---|---|")
    for c in data["claims"]:
        src = c["source"] or "—"
        act = c["note"] or ("可使用" if c["status"] in ("confirmed", "derived") else "—")
        print(f"| {c['id']} | {c['claim']} | {src} | {LABEL[c['status']]} | {act} |")


def main():
    ap = argparse.ArgumentParser(description="电商视觉证据账本")
    ap.add_argument("--project", required=True, help="项目目录")
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("init", help="初始化账本").set_defaults(fn=cmd_init)

    p = sub.add_parser("add", help="登记一条宣称")
    p.add_argument("id")
    p.add_argument("--claim", required=True)
    p.add_argument("--source", default="")
    p.add_argument("--status", choices=STATUSES, default="pending")
    p.add_argument("--note", default="")
    p.set_defaults(fn=cmd_add)

    p = sub.add_parser("promote", help="补证通过 → 已确认")
    p.add_argument("id")
    p.add_argument("--source", required=True)
    p.add_argument("--note", default="")
    p.set_defaults(fn=cmd_promote)

    p = sub.add_parser("ban", help="列入禁止")
    p.add_argument("id")
    p.add_argument("--reason", required=True)
    p.set_defaults(fn=cmd_ban)

    p = sub.add_parser("list", help="列出账本")
    p.add_argument("--status", choices=STATUSES)
    p.set_defaults(fn=cmd_list)

    sub.add_parser("check", help="交付前门禁").set_defaults(fn=cmd_check)
    sub.add_parser("export", help="输出 Markdown 表").set_defaults(fn=cmd_export)

    a = ap.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
