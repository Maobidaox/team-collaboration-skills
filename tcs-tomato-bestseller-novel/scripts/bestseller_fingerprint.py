# -*- coding: utf-8 -*-
"""爆款基因拆解器（bestseller_fingerprint）
番茄爆款小说专家 · 内置知识库脚本（口径：2026-09）

把一部在榜爆款（或用户自拟题材）拆成 7 维「爆款基因指纹」，并给出可复刻到
用户自己作品的移植方案。纯标准库实现，零联网、零第三方依赖。

用法：
    python bestseller_fingerprint.py --title "我在精神病院学斩神" --track 都市脑洞
    python bestseller_fingerprint.py --track 豪门虐恋 --list-tracks
    python bestseller_fingerprint.py --title "XX" --track 古言 --json out.json
    python bestseller_fingerprint.py --title "XX" --track 玄幻 --md 指纹报告.md
"""
import argparse
import io
import json
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

CAP = "资源库口径：2026-09"

# ---------------------------------------------------------------- 赛道基因库
# 每赛道给出该赛道「爆款必备基因」与「复刻杠杆」，用于生成移植方案。
TRACKS = {
    "都市脑洞": {
        "core_hook": "现代都市 + 一个不讲道理的设定（系统/直播/整活/规则）",
        "pitch": "开篇 300 字内亮设定，首章必须完成一次‘设定型爽点’",
        "beat": ["设定亮相", "规则试探", "第一次打脸", "能力升级", "势力扩张", "世界真相"],
        "payoff": "信息差爽点 + 打脸爽点 + 扮猪吃虎",
        "hook": "悬念钩（设定未解）+ 冲突钩（对手登场）+ 反转钩",
        "character": "主角：表面废物/实际深藏；对手：傲慢且被打脸",
        "quote": "冷幽默金句 + 装×式短句",
        "clone": "把‘设定’换成用户题材的等价物，保持‘300 字亮牌’节奏不变",
        "risk": "设定过重压死节奏；前 3 章不亮牌必死",
    },
    "高武玄幻": {
        "core_hook": "低武世界 + 清晰可量化的力量体系 + 越级挑战",
        "pitch": "开篇给一次‘以弱胜强’，让读者立刻获得力量想象",
        "beat": ["体系亮相", "废柴受辱", "奇遇/觉醒", "越级打脸", "宗门/势力战", "登顶"],
        "payoff": "越级爽点 + 打脸爽点 + 资源掠夺",
        "hook": "危机钩（强敌压境）+ 悬念钩（体系之谜）",
        "character": "主角：隐忍 + 狠；对手：阶梯式递进",
        "quote": "力量宣言式金句 + 战意短句",
        "clone": "先定‘等级 3 档内可越级’的硬规则，再把打脸对象按阶梯排布",
        "risk": "体系膨胀失控、中期战力崩坏",
    },
    "规则怪谈": {
        "core_hook": "诡异规则 + 逻辑破局 + 生死倒计时",
        "pitch": "首章抛出 3~5 条诡异规则，读者立刻参与推理",
        "beat": ["规则登场", "违规死亡", "找漏洞", "第一次破局", "规则升级", "源头真相"],
        "payoff": "解谜爽点 + 智商碾压 + 幸存者抱团",
        "hook": "悬念钩（规则背后是什么）+ 危机钩（倒计时）",
        "character": "主角：冷静观察者；配角：消耗品与叛徒",
        "quote": "冷峻短句 + 规则复述式压迫感",
        "clone": "保留‘规则—死亡—破局’三段闭环，替换场景与规则来源",
        "risk": "规则自相矛盾即掉分；逻辑漏洞被读者抓包",
    },
    "无限流": {
        "core_hook": "轮回副本 + 能力继承 + 主神/系统悬念",
        "pitch": "首轮副本给完整闭环，末章留‘世界疑点’",
        "beat": ["入局", "副本规则", "团队碰撞", "通关", "能力结算", "幕后初现"],
        "payoff": "通关爽点 + 生存碾压 + 队友羁绊",
        "hook": "悬念钩（幕后）+ 新人钩（新副本）",
        "character": "主角：稳健规划型；队友：功能互补",
        "quote": "结算播报式 + 冷硬独白",
        "clone": "先设计 3 个可复用副本模板，保证 20 章不断档",
        "risk": "副本同质化、队友工具人化",
    },
    "历史穿越": {
        "core_hook": "现代知识 × 古代困局 + 步步为营",
        "pitch": "首章即入局一场必输之局，靠知识翻盘",
        "beat": ["入局危机", "知识破局", "站稳脚跟", "势力上升", "庙堂博弈", "定鼎"],
        "payoff": "智斗爽点 + 阶级跃迁 + 众望所归",
        "hook": "危机钩 + 权谋钩",
        "character": "主角：克制通透；对手：老谋深算",
        "quote": "古白夹杂的谋略金句",
        "clone": "先立‘一条史实硬约束’，全部爽点围绕约束解题",
        "risk": "常识硬伤、节奏拖沓",
    },
    "豪门虐恋": {
        "core_hook": "强强拉扯 + 误会/背叛 + 追妻火葬场",
        "pitch": "首章给一次毁灭性伤害，同时埋‘男主未说出口的真相’",
        "beat": ["虐点起", "误会对立", "真相半露", "追妻反转", "双向救赎", "圆满"],
        "payoff": "虐爽交替 + 身份反转 + 打脸白月光",
        "hook": "悬念钩（真相）+ 情绪钩（虐点）",
        "character": "女主：清醒坚韧；男主：傲慢后破碎",
        "quote": "短句递刀 + 反差独白",
        "clone": "虐点 3 章一小爆、10 章一大爆，节奏表先行",
        "risk": "虐而无脑、女主降智必掉追读",
    },
    "甜宠现言": {
        "core_hook": "高糖日常 + 双向奔赴 + 轻冲突",
        "pitch": "首章给一次心动名场面，糖分立刻到位",
        "beat": ["相遇", "心动", "小冲突", "告白", "并肩", "圆满"],
        "payoff": "甜点爽 + 宠溺 + 小打脸",
        "hook": "情绪钩 + 小悬念钩",
        "character": "女主：可爱但有底线；男主：宠而不油",
        "quote": "糖分金句 + 心动描写",
        "clone": "每章至少 1 个糖点，冲突不过夜",
        "risk": "寡淡无冲突、糖点重复",
    },
    "古言宅斗": {
        "core_hook": "深宅权谋 + 步步反击 + 身份反转",
        "pitch": "首章给一次置之于死地的陷害，女主反手翻盘",
        "beat": ["入局被害", "自证反击", "掌权", "朝堂牵连", "身份揭晓", "登顶"],
        "payoff": "反击爽点 + 智商碾压 + 身份逆袭",
        "hook": "危机钩 + 权谋钩",
        "character": "女主：绵里藏针；对手：层层递进",
        "quote": "古韵金句 + 反击宣言",
        "clone": "建立‘对手阶梯表’：每 8~10 章换一个更强的对手",
        "risk": "套路陈旧、反派降智",
    },
    "穿书快穿": {
        "core_hook": "穿越/穿书 + 已知剧情 + 反套路改写",
        "pitch": "首章点明‘我知道剧情’，制造读者优越感",
        "beat": ["穿书亮相", "改命", "原女主对抗", "世界规则", "真相反转", "收官"],
        "payoff": "碾压原剧情 + 打脸原女主 + 反向养成",
        "hook": "悬念钩（剧情为何偏离）+ 反转钩",
        "character": "女主：清醒且毒舌；原女主：白莲被打脸",
        "quote": "吐槽式金句 + 反差独白",
        "clone": "必须写清‘哪三处剧情会偏离’，否则爽点无根",
        "risk": "剧情依赖原作、原创性不足",
    },
    "年代种田": {
        "core_hook": "物资匮乏年代 + 现代经验 + 家庭逆袭",
        "pitch": "首章给一次家庭危机，靠本事解决",
        "beat": ["危机立", "手艺破局", "家业起飞", "乡邻打脸", "时代机遇", "家国"],
        "payoff": "生活流爽点 + 打脸极品亲戚 + 阶级跃迁",
        "hook": "小悬念 + 情绪钩",
        "character": "女主/男主：能吃苦有算计；亲戚：极品但立得住",
        "quote": "烟火气金句 + 生活细节",
        "clone": "每 5 章解决一件‘家事难题’，形成成就清单",
        "risk": "流水账、细节失真",
    },
    "修仙女强": {
        "core_hook": "女频视角修仙 + 逆天机缘 + 打脸升级",
        "pitch": "首章废除灵根/被弃，立刻埋下逆天转机",
        "beat": ["起点谷底", "机缘觉醒", "打脸同门", "宗门立威", "飞升/大道", "登顶"],
        "payoff": "升级爽点 + 打脸爽点 + 情缘拉扯",
        "hook": "悬念钩 + 危机钩",
        "character": "女主：冷艳强势；男主：并肩不做挂件",
        "quote": "凌厉短句 + 大道感悟",
        "clone": "机缘节奏表先行：每 12 章一次质变",
        "risk": "男主喧宾夺主、升级通胀",
    },
    "复仇爽文": {
        "core_hook": "血仇开局 + 步步复仇 + 打脸清单",
        "pitch": "首章给一次不可饶恕的重创，主角立下复仇誓约",
        "beat": ["血仇立", "隐忍蓄力", "第一次复仇", "清单推进", "幕后黑手", "清算"],
        "payoff": "复仇爽点 + 打脸清单 + 身份反转",
        "hook": "危机钩 + 悬念钩（幕后）",
        "character": "主角：隐忍狠辣；对手：按‘仇恨清单’排列",
        "quote": "冷冽短句 + 复仇宣言",
        "clone": "建立‘仇恨清单表’，每完成一项给一次大爽点",
        "risk": "复仇无终点、情绪透支",
    },
}

FINGERPRINT_DIMS = [
    ("① 核心钩子", "core_hook", "读者为什么在 3 秒内点进来"),
    ("② 首章必胜", "pitch", "首章必须交付什么才算过关"),
    ("③ 结构节拍", "beat", "全书骨架节拍（可复用为分卷）"),
    ("④ 爽点配方", "payoff", "爽点类型组合，决定追读留存"),
    ("⑤ 钩子配置", "hook", "章末钩子类型组合，决定追更率"),
    ("⑥ 人设张力", "character", "人物反差与对手设计"),
    ("⑦ 金句调性", "quote", "语言风格决定读者黏性"),
]


def fingerprint(title, track, extra=None):
    g = TRACKS[track]
    lines = []
    lines.append("# 爆款基因指纹报告 · %s" % (title or "（未命名作品）"))
    lines.append("")
    lines.append("> 赛道：**%s**　｜　%s　｜　生成器：bestseller_fingerprint v1.0" % (track, CAP))
    lines.append("")
    lines.append("## 一、七维爆款基因指纹")
    lines.append("")
    lines.append("| 维度 | 含义 | 本作基因 |")
    lines.append("|---|---|---|")
    for label, key, mean in FINGERPRINT_DIMS:
        v = g[key]
        if isinstance(v, list):
            v = " → ".join(v)
        lines.append("| %s | %s | %s |" % (label, mean, v))
    lines.append("")
    lines.append("## 二、分卷节拍映射（可直接作为分卷骨架）")
    lines.append("")
    for i, b in enumerate(g["beat"], 1):
        lines.append("- **第 %d 卷 / 阶段**：%s" % (i, b))
    lines.append("")
    lines.append("## 三、复刻杠杆（把爆款基因移植到你的题材）")
    lines.append("")
    lines.append("- **可复用**：%s" % g["clone"])
    lines.append("- **不可照搬**：设定名词、专有世界观、人物姓名与独特金句")
    lines.append("- **移植步骤**：① 保留七维骨架 → ② 替换赛道专有名词 → ③ 重写首章 300 字亮牌 → ④ 重新设计对手阶梯 → ⑤ 用自己的语言风格重写金句")
    lines.append("")
    lines.append("## 四、本赛道已知翻车点（必须规避）")
    lines.append("")
    lines.append("- %s" % g["risk"])
    lines.append("")
    if extra:
        lines.append("## 五、用户补充")
        lines.append("")
        lines.append(extra)
        lines.append("")
    lines.append("## 六、下一步建议")
    lines.append("")
    lines.append("1. 用 `topic_score.py` 对本选题做十维打分，确认 ≥80 分再开书。")
    lines.append("2. 用 `title_maker.py` 批量生成书名并做点击率预判。")
    lines.append("3. 用 `outline_builder.py` 落地前 30 章逐章细纲。")
    lines.append("4. 正文成稿后用 `rhythm_analyzer.py` + `quality_selfcheck.py` 双检。")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("*%s ｜ 本节仅为创作方法论拆解，不涉及任何原作品文字复制，规避侵权风险。*" % CAP)
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description="爆款基因拆解器")
    ap.add_argument("--title", default="", help="作品名或自拟题材名")
    ap.add_argument("--track", default=None, help="赛道名")
    ap.add_argument("--list-tracks", action="store_true", help="列出全部赛道")
    ap.add_argument("--extra", default=None, help="补充说明，写入报告第五节")
    ap.add_argument("--json", default=None, help="同时输出 JSON 到指定路径")
    ap.add_argument("--md", default=None, help="输出 Markdown 报告到指定路径")
    args = ap.parse_args()

    if args.list_tracks:
        print("可用赛道（%s，共 %d 个）：" % (CAP, len(TRACKS)))
        for k in TRACKS:
            print("  · %s" % k)
        print("\n提示：赛道名不匹配时会给出最接近的候选。")
        return 0

    if not args.track:
        print("[错误] 必须用 --track 指定赛道，或 --list-tracks 查看清单。")
        return 2

    track = args.track
    if track not in TRACKS:
        cands = [k for k in TRACKS if any(c in k or k in c for c in track)]
        if not cands:
            cands = [k for k in TRACKS if track[:2] in k]
        print("[错误] 未知赛道「%s」。" % track)
        if cands:
            print("最接近的候选：%s" % "、".join(cands))
        print("用 --list-tracks 查看全部赛道。")
        return 2

    md = fingerprint(args.title, track, args.extra)
    print(md)
    if args.md:
        io.open(args.md, "w", encoding="utf-8", newline="\n").write(md)
        print("\n[已写出] %s" % args.md)
    if args.json:
        io.open(args.json, "w", encoding="utf-8", newline="\n").write(
            json.dumps({"title": args.title, "track": track, "cap": CAP,
                        "gene": TRACKS[track]}, ensure_ascii=False, indent=2))
        print("[已写出] %s" % args.json)
    return 0


if __name__ == "__main__":
    sys.exit(main())
