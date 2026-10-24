#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Markdown 一键导出器 —— 把 Markdown 稿件导出为主流文档格式

纯标准库实现（zipfile + xml + re + html），零第三方依赖。

支持导出：
    docx  —— 真实 Word 文档（OOXML），Word / WPS / 腾讯文档可直接打开
    html  —— 自包含网页，内置打印样式（浏览器 Ctrl+P 即可另存 PDF）
    txt   —— 纯文本（去标记）
    md    —— 规范化 Markdown 副本

用法：
    python md_exporter.py 稿件.md                          # 默认导出 docx+html+txt
    python md_exporter.py 稿件.md --to docx                # 只导出 docx
    python md_exporter.py 稿件.md --to docx,html,txt
    python md_exporter.py 书稿目录 --recursive --to docx
    python md_exporter.py 稿件.md --outdir 导出目录
    python md_exporter.py 稿件.md --title "第1章 断脉"
"""
import argparse
import html as html_mod
import os
import re
import sys
import zipfile
from datetime import datetime

# ---------------------------------------------------------------- 内联解析

INLINE_RE = re.compile(
    r"(\*\*\*.+?\*\*\*|\*\*.+?\*\*|__.+?__|\*.+?\*|_.+?_|`[^`]+`|~~.+?~~|\[[^\]]+\]\([^)]+\))"
)


def parse_inline(text):
    """把一行 Markdown 内联语法切成 [(text, style)] 片段。
    style 取值：plain / b / i / bi / code / strike / link
    link 片段带 url，用 dict 返回。"""
    out = []
    pos = 0
    for m in INLINE_RE.finditer(text):
        if m.start() > pos:
            out.append({"t": text[pos:m.start()], "s": "plain"})
        tok = m.group(0)
        if tok.startswith("***") and tok.endswith("***") and len(tok) > 6:
            out.append({"t": tok[3:-3], "s": "bi"})
        elif tok.startswith("**") and tok.endswith("**") and len(tok) > 4:
            out.append({"t": tok[2:-2], "s": "b"})
        elif tok.startswith("__") and tok.endswith("__") and len(tok) > 4:
            out.append({"t": tok[2:-2], "s": "b"})
        elif tok.startswith("~~") and tok.endswith("~~") and len(tok) > 4:
            out.append({"t": tok[2:-2], "s": "strike"})
        elif tok.startswith("`") and tok.endswith("`") and len(tok) > 2:
            out.append({"t": tok[1:-1], "s": "code"})
        elif tok.startswith("[") :
            mm = re.match(r"\[([^\]]+)\]\(([^)]+)\)", tok)
            if mm:
                out.append({"t": mm.group(1), "s": "link", "url": mm.group(2)})
            else:
                out.append({"t": tok, "s": "plain"})
        elif (tok.startswith("*") and tok.endswith("*")) or (tok.startswith("_") and tok.endswith("_")):
            out.append({"t": tok[1:-1], "s": "i"})
        else:
            out.append({"t": tok, "s": "plain"})
        pos = m.end()
    if pos < len(text):
        out.append({"t": text[pos:], "s": "plain"})
    return [s for s in out if s["t"] != ""] or [{"t": "", "s": "plain"}]


# ---------------------------------------------------------------- 块解析

BLOCK_RE_HEAD = re.compile(r"^(#{1,6})\s+(.*)$")
BLOCK_RE_UL = re.compile(r"^\s*[-*+]\s+(.*)$")
BLOCK_RE_OL = re.compile(r"^\s*(\d+)[.)]\s+(.*)$")
BLOCK_RE_HR = re.compile(r"^\s*([-*_])\s*(\1\s*){2,}$")
BLOCK_RE_QUOTE = re.compile(r"^\s*>\s?(.*)$")
BLOCK_RE_TABLE = re.compile(r"^\s*\|.*\|\s*$")


def parse_blocks(md):
    """解析为块列表：[{type, ...}]"""
    lines = md.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    blocks = []
    i = 0
    n = len(lines)
    while i < n:
        ln = lines[i]

        # 代码块
        if ln.strip().startswith("```"):
            lang = ln.strip()[3:].strip()
            i += 1
            buf = []
            while i < n and not lines[i].strip().startswith("```"):
                buf.append(lines[i])
                i += 1
            i += 1
            blocks.append({"type": "code", "lang": lang, "text": "\n".join(buf)})
            continue

        # 空行
        if not ln.strip():
            i += 1
            continue

        # 分割线
        if BLOCK_RE_HR.match(ln):
            blocks.append({"type": "hr"})
            i += 1
            continue

        # 标题
        m = BLOCK_RE_HEAD.match(ln)
        if m:
            blocks.append({"type": "h", "level": len(m.group(1)),
                           "inline": parse_inline(m.group(2).strip())})
            i += 1
            continue

        # 表格
        if BLOCK_RE_TABLE.match(ln):
            tb = []
            while i < n and BLOCK_RE_TABLE.match(lines[i]):
                tb.append(lines[i])
                i += 1
            rows = []
            for r in tb:
                cells = [c.strip() for c in r.strip().strip("|").split("|")]
                rows.append(cells)
            # 去掉分隔行 |---|---|
            rows = [r for r in rows if not all(re.fullmatch(r":?-{2,}:?", c or "-") for c in r)]
            if rows:
                blocks.append({"type": "table", "head": rows[0], "body": rows[1:]})
            continue

        # 引用
        if BLOCK_RE_QUOTE.match(ln):
            buf = []
            while i < n and BLOCK_RE_QUOTE.match(lines[i]):
                buf.append(BLOCK_RE_QUOTE.match(lines[i]).group(1))
                i += 1
            blocks.append({"type": "quote",
                           "inline": parse_inline("\n".join(buf).strip())})
            continue

        # 有序列表
        if BLOCK_RE_OL.match(ln):
            items = []
            while i < n and BLOCK_RE_OL.match(lines[i]):
                mm = BLOCK_RE_OL.match(lines[i])
                items.append(parse_inline(mm.group(2).strip()))
                i += 1
            blocks.append({"type": "ol", "items": items})
            continue

        # 无序列表
        if BLOCK_RE_UL.match(ln):
            items = []
            while i < n and BLOCK_RE_UL.match(lines[i]):
                mm = BLOCK_RE_UL.match(lines[i])
                items.append(parse_inline(mm.group(1).strip()))
                i += 1
            blocks.append({"type": "ul", "items": items})
            continue

        # 段落（连续非空行合并）
        buf = [ln.strip()]
        i += 1
        while i < n and lines[i].strip() and not (
            BLOCK_RE_HEAD.match(lines[i]) or BLOCK_RE_UL.match(lines[i])
            or BLOCK_RE_OL.match(lines[i]) or BLOCK_RE_QUOTE.match(lines[i])
            or BLOCK_RE_HR.match(lines[i]) or BLOCK_RE_TABLE.match(lines[i])
            or lines[i].strip().startswith("```")
        ):
            buf.append(lines[i].strip())
            i += 1
        blocks.append({"type": "p", "inline": parse_inline(" ".join(buf))})
    return blocks


# ---------------------------------------------------------------- HTML 导出

CSS = """
:root{--ink:#1f2328;--sub:#57606a;--line:#d8dee4;--bg:#fff;--accent:#c0392b;--code:#f6f8fa}
*{box-sizing:border-box}
body{margin:0;padding:48px 16px 96px;background:#fafbfc;color:var(--ink);
 font-family:"PingFang SC","Microsoft YaHei","Hiragino Sans GB","Source Han Sans SC",sans-serif;
 font-size:16px;line-height:1.9;-webkit-font-smoothing:antialiased}
.page{max-width:820px;margin:0 auto;background:var(--bg);padding:56px 60px 72px;
 border-radius:6px;box-shadow:0 1px 3px rgba(27,31,36,.09),0 8px 24px rgba(27,31,36,.06)}
h1,h2,h3,h4,h5,h6{line-height:1.4;font-weight:700;margin:1.6em 0 .6em}
h1{font-size:1.85em;border-bottom:2px solid var(--accent);padding-bottom:.3em;margin-top:0}
h2{font-size:1.45em;border-bottom:1px solid var(--line);padding-bottom:.25em}
h3{font-size:1.2em}
h4{font-size:1.05em}
p{margin:.85em 0}
strong{font-weight:700}
em{font-style:italic;color:var(--sub)}
del{color:var(--sub)}
a{color:#0969da;text-decoration:none;border-bottom:1px solid rgba(9,105,218,.3)}
code{background:var(--code);padding:.15em .4em;border-radius:4px;
 font-family:"SFMono-Regular",Consolas,"Liberation Mono",monospace;font-size:.9em}
pre{background:var(--code);padding:16px 18px;border-radius:6px;overflow:auto;
 border:1px solid var(--line)}
pre code{background:none;padding:0;font-size:.86em;line-height:1.65}
blockquote{margin:1em 0;padding:.6em 1.1em;border-left:4px solid var(--accent);
 background:#fdf6f5;color:var(--sub);border-radius:0 4px 4px 0}
blockquote p{margin:.35em 0}
hr{border:0;border-top:1px solid var(--line);margin:2em 0}
ul,ol{padding-left:1.6em;margin:.85em 0}
li{margin:.3em 0}
table{border-collapse:collapse;width:100%;margin:1.2em 0;font-size:.94em}
th,td{border:1px solid var(--line);padding:9px 12px;text-align:left;vertical-align:top}
th{background:#f6f8fa;font-weight:700}
tr:nth-child(even) td{background:#fcfcfd}
.meta{color:var(--sub);font-size:.84em;margin-bottom:2em;padding-bottom:1em;
 border-bottom:1px dashed var(--line)}
@media print{
 body{background:#fff;padding:0;font-size:12pt}
 .page{box-shadow:none;border-radius:0;padding:0;max-width:none}
 pre,blockquote,table{page-break-inside:avoid}
 h1,h2,h3{page-break-after:avoid}
 @page{margin:18mm 16mm}
}
@media (max-width:640px){.page{padding:28px 20px 48px}body{padding:20px 8px 48px}}
"""


def esc(s):
    return html_mod.escape(s, quote=False)


def inline_html(parts):
    out = []
    for p in parts:
        t = esc(p["t"])
        s = p["s"]
        if s == "b":
            out.append("<strong>%s</strong>" % t)
        elif s == "i":
            out.append("<em>%s</em>" % t)
        elif s == "bi":
            out.append("<strong><em>%s</em></strong>" % t)
        elif s == "code":
            out.append("<code>%s</code>" % t)
        elif s == "strike":
            out.append("<del>%s</del>" % t)
        elif s == "link":
            out.append('<a href="%s" target="_blank" rel="noopener">%s</a>'
                       % (esc(p.get("url", "#")), t))
        else:
            out.append(t)
    return "".join(out)


def to_html(md, title=None):
    blocks = parse_blocks(md)
    body = []
    for b in blocks:
        t = b["type"]
        if t == "h":
            lv = b["level"]
            body.append("<h%d>%s</h%d>" % (lv, inline_html(b["inline"]), lv))
        elif t == "p":
            body.append("<p>%s</p>" % inline_html(b["inline"]))
        elif t == "quote":
            body.append("<blockquote><p>%s</p></blockquote>" % inline_html(b["inline"]))
        elif t == "ul":
            body.append("<ul>%s</ul>" % "".join("<li>%s</li>" % inline_html(x) for x in b["items"]))
        elif t == "ol":
            body.append("<ol>%s</ol>" % "".join("<li>%s</li>" % inline_html(x) for x in b["items"]))
        elif t == "hr":
            body.append("<hr>")
        elif t == "code":
            body.append("<pre><code>%s</code></pre>" % esc(b["text"]))
        elif t == "table":
            th = "".join("<th>%s</th>" % esc(c) for c in b["head"])
            trs = "".join("<tr>%s</tr>" % "".join("<td>%s</td>" % esc(c) for c in r)
                          for r in b["body"])
            body.append("<table><thead><tr>%s</tr></thead><tbody>%s</tbody></table>" % (th, trs))
    ttl = title or "文档"
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    return """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>%s</title>
<style>%s</style>
</head>
<body>
<div class="page">
<div class="meta">%s ｜ 导出时间 %s ｜ 用浏览器「打印 → 另存为 PDF」即可得到 PDF</div>
%s
</div>
</body>
</html>
""" % (esc(ttl), CSS, esc(ttl), stamp, "\n".join(body))


# ---------------------------------------------------------------- DOCX 导出

def xe(s):
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            .replace('"', "&quot;"))


def runs_xml(parts, base_size=24, force_mono=False):
    """base_size 为半磅值：24 = 12pt"""
    out = []
    for p in parts:
        t = xe(p["t"])
        s = p["s"]
        rpr = ['<w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman" w:eastAsia="宋体"/>',
               '<w:sz w:val="%d"/><w:szCs w:val="%d"/>' % (base_size, base_size)]
        if s in ("b", "bi"):
            rpr.append("<w:b/>")
        if s in ("i", "bi"):
            rpr.append("<w:i/>")
        if s == "strike":
            rpr.append("<w:strike/>")
        if s == "code" or force_mono:
            rpr[0] = ('<w:rFonts w:ascii="Consolas" w:hAnsi="Consolas" w:eastAsia="宋体"/>')
            rpr.append('<w:shd w:val="clear" w:fill="F2F2F2"/>')
        if s == "link":
            rpr.append('<w:color w:val="0969DA"/><w:u w:val="single"/>')
        out.append("<w:r><w:rPr>%s</w:rPr><w:t xml:space=\"preserve\">%s</w:t></w:r>"
                   % ("".join(rpr), t))
    return "".join(out)


def para_xml(runs, style="Normal", align=None, space_before=0, space_after=120,
             indent=None, border_bottom=False, hanging=None):
    ppr = ['<w:pStyle w:val="%s"/>' % style]
    if align:
        ppr.append('<w:jc w:val="%s"/>' % align)
    ppr.append('<w:spacing w:before="%d" w:after="%d" w:line="360" w:lineRule="auto"/>'
               % (space_before, space_after))
    if indent:
        ppr.append('<w:ind w:firstLineChars="%d"/>' % indent)
    if hanging:
        ppr.append('<w:ind w:leftChars="%d" w:hangingChars="%d"/>' % (hanging, hanging))
    if border_bottom:
        ppr.append('<w:pBdr><w:bottom w:val="single" w:sz="8" w:space="4" w:color="C0392B"/></w:pBdr>')
    return "<w:p><w:pPr>%s</w:pPr>%s</w:p>" % ("".join(ppr), runs)


def to_docx_xml(md, title=None):
    blocks = parse_blocks(md)
    parts = []
    for b in blocks:
        t = b["type"]
        if t == "h":
            lv = b["level"]
            size = {1: 40, 2: 32, 3: 28, 4: 26, 5: 25, 6: 24}.get(lv, 24)
            parts.append(para_xml(runs_xml(b["inline"], size), style="Heading%d" % min(lv, 3),
                                  space_before=240, space_after=140,
                                  border_bottom=(lv == 1)))
        elif t == "p":
            parts.append(para_xml(runs_xml(b["inline"]), indent=200))
        elif t == "quote":
            parts.append(para_xml(runs_xml(b["inline"]), style="Quote",
                                  space_before=120, space_after=160))
        elif t == "ul":
            for it in b["items"]:
                parts.append(para_xml(runs_xml([{"t": "• ", "s": "plain"}] + it),
                                      hanging=200, space_after=60))
        elif t == "ol":
            for idx, it in enumerate(b["items"], 1):
                parts.append(para_xml(runs_xml([{"t": "%d. " % idx, "s": "plain"}] + it),
                                      hanging=200, space_after=60))
        elif t == "hr":
            parts.append('<w:p><w:pPr><w:pBdr><w:bottom w:val="single" w:sz="6" '
                         'w:space="1" w:color="D8DEE4"/></w:pBdr></w:pPr></w:p>')
        elif t == "code":
            for line in (b["text"] or " ").split("\n"):
                parts.append(para_xml(runs_xml([{"t": line or " ", "s": "code"}], 20),
                                      space_after=0, indent=None))
            parts.append(para_xml("", space_after=80))
        elif t == "table":
            cols = max(1, len(b["head"]))
            width = int(9000 / cols)
            grid = "".join('<w:gridCol w:w="%d"/>' % width for _ in range(cols))

            def row(cells, header=False):
                tcs = []
                for c in cells:
                    rpr = ('<w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman" '
                           'w:eastAsia="宋体"/><w:sz w:val="22"/>' + ("<w:b/>" if header else ""))
                    tcs.append('<w:tc><w:tcPr><w:tcW w:w="%d" w:type="dxa"/>%s</w:tcPr>'
                               '<w:p><w:pPr><w:spacing w:before="40" w:after="40"/></w:pPr>'
                               '<w:r><w:rPr>%s</w:rPr><w:t xml:space="preserve">%s</w:t></w:r>'
                               '</w:p></w:tc>'
                               % (width,
                                  '<w:shd w:val="clear" w:fill="F2F2F2"/>' if header else "",
                                  rpr, xe(c)))
                return "<w:tr>%s</w:tr>" % "".join(tcs)

            tbl = ('<w:tbl><w:tblPr><w:tblW w:w="0" w:type="auto"/>'
                   '<w:tblBorders>'
                   '<w:top w:val="single" w:sz="4" w:color="D8DEE4"/>'
                   '<w:left w:val="single" w:sz="4" w:color="D8DEE4"/>'
                   '<w:bottom w:val="single" w:sz="4" w:color="D8DEE4"/>'
                   '<w:right w:val="single" w:sz="4" w:color="D8DEE4"/>'
                   '<w:insideH w:val="single" w:sz="4" w:color="D8DEE4"/>'
                   '<w:insideV w:val="single" w:sz="4" w:color="D8DEE4"/>'
                   '</w:tblBorders></w:tblPr><w:tblGrid>%s</w:tblGrid>%s%s</w:tbl>'
                   % (grid, row(b["head"], True),
                      "".join(row(r) for r in b["body"])))
            parts.append(tbl)
            parts.append('<w:p><w:pPr><w:spacing w:after="120"/></w:pPr></w:p>')
    return "".join(parts)


STYLES_XML = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
<w:docDefaults><w:rPrDefault><w:rPr>
<w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman" w:eastAsia="宋体" w:cs="Times New Roman"/>
<w:sz w:val="24"/><w:szCs w:val="24"/><w:lang w:val="en-US" w:eastAsia="zh-CN"/>
</w:rPr></w:rPrDefault>
<w:pPrDefault><w:pPr><w:spacing w:line="360" w:lineRule="auto"/></w:pPr></w:pPrDefault>
</w:docDefaults>
<w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/>
<w:qFormat/></w:style>
<w:style w:type="paragraph" w:styleId="Heading1"><w:name w:val="heading 1"/><w:basedOn w:val="Normal"/>
<w:next w:val="Normal"/><w:qFormat/><w:pPr><w:outlineLvl w:val="0"/><w:jc w:val="center"/></w:pPr>
<w:rPr><w:b/><w:sz w:val="40"/><w:szCs w:val="40"/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="Heading2"><w:name w:val="heading 2"/><w:basedOn w:val="Normal"/>
<w:next w:val="Normal"/><w:qFormat/><w:pPr><w:outlineLvl w:val="1"/></w:pPr>
<w:rPr><w:b/><w:sz w:val="32"/><w:szCs w:val="32"/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="Heading3"><w:name w:val="heading 3"/><w:basedOn w:val="Normal"/>
<w:next w:val="Normal"/><w:qFormat/><w:pPr><w:outlineLvl w:val="2"/></w:pPr>
<w:rPr><w:b/><w:sz w:val="28"/><w:szCs w:val="28"/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="Quote"><w:name w:val="Quote"/><w:basedOn w:val="Normal"/>
<w:qFormat/><w:pPr><w:ind w:leftChars="200"/></w:pPr>
<w:rPr><w:i/><w:color w:val="57606A"/></w:rPr></w:style>
</w:styles>"""

CONTENT_TYPES = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
<Default Extension="xml" ContentType="application/xml"/>
<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
<Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>
<Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>
<Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>
</Types>"""

RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>
<Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/>
</Relationships>"""

DOC_RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
</Relationships>"""


def docx_bytes(md, title="文档", author="番茄爆款小说专家"):
    now = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
    document = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
                '<w:body>%s'
                '<w:sectPr><w:pgSz w:w="11906" w:h="16838"/>'
                '<w:pgMar w:top="1440" w:right="1418" w:bottom="1440" w:left="1418" '
                'w:header="851" w:footer="992" w:gutter="0"/></w:sectPr>'
                '</w:body></w:document>' % to_docx_xml(md, title))
    core = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" '
            'xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" '
            'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">'
            '<dc:title>%s</dc:title><dc:creator>%s</dc:creator>'
            '<cp:lastModifiedBy>%s</cp:lastModifiedBy>'
            '<dcterms:created xsi:type="dcterms:W3CDTF">%s</dcterms:created>'
            '<dcterms:modified xsi:type="dcterms:W3CDTF">%s</dcterms:modified>'
            '</cp:coreProperties>' % (xe(title), xe(author), xe(author), now, now))
    app = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
           '<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties" '
           'xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes">'
           '<Application>md_exporter (纯标准库)</Application><DocSecurity>0</DocSecurity>'
           '<Lines>1</Lines><Paragraphs>1</Paragraphs></Properties>')

    import io
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", CONTENT_TYPES)
        z.writestr("_rels/.rels", RELS)
        z.writestr("word/_rels/document.xml.rels", DOC_RELS)
        z.writestr("word/document.xml", document)
        z.writestr("word/styles.xml", STYLES_XML)
        z.writestr("docProps/core.xml", core)
        z.writestr("docProps/app.xml", app)
    return buf.getvalue()


# ---------------------------------------------------------------- TXT 导出

def to_txt(md, title=None):
    blocks = parse_blocks(md)
    lines = []
    if title:
        lines += [title, "=" * min(40, len(title) * 2), ""]
    for b in blocks:
        t = b["type"]
        flat = lambda parts: "".join(p["t"] for p in parts)
        if t == "h":
            txt = flat(b["inline"])
            lines += ["", txt, "-" * max(6, len(txt)), ""]
        elif t == "p":
            lines += [flat(b["inline"]), ""]
        elif t == "quote":
            lines += ["> " + x for x in flat(b["inline"]).split("\n")] + [""]
        elif t == "ul":
            lines += ["  · " + flat(x) for x in b["items"]] + [""]
        elif t == "ol":
            lines += ["  %d. %s" % (i, flat(x)) for i, x in enumerate(b["items"], 1)] + [""]
        elif t == "hr":
            lines += ["", "-" * 40, ""]
        elif t == "code":
            lines += ["    " + ln for ln in b["text"].split("\n")] + [""]
        elif t == "table":
            rows = [b["head"]] + b["body"]
            w = [max(len(r[i]) if i < len(r) else 0 for r in rows) for i in range(len(b["head"]))]
            for ri, r in enumerate(rows):
                cells = [(r[i] if i < len(r) else "").ljust(w[i]) for i in range(len(w))]
                lines.append("  | " + " | ".join(cells) + " |")
                if ri == 0:
                    lines.append("  |" + "|".join("-" * (x + 2) for x in w) + "|")
            lines.append("")
    out = "\n".join(lines)
    out = re.sub(r"\n{3,}", "\n\n", out).strip() + "\n"
    return out


# ---------------------------------------------------------------- 主流程

def stamp_name(src, ext, outdir, title=None):
    base = title or os.path.splitext(os.path.basename(src))[0]
    return os.path.join(outdir, "%s.%s" % (base, ext))


def export_one(src, targets, outdir, title=None):
    md = None
    for enc in ("utf-8", "utf-8-sig", "gbk", "gb18030"):
        try:
            with open(src, "r", encoding=enc) as f:
                md = f.read()
            break
        except (UnicodeDecodeError, LookupError):
            continue
    if md is None:
        with open(src, "r", encoding="utf-8", errors="ignore") as f:
            md = f.read()

    os.makedirs(outdir, exist_ok=True)
    ttl = title or os.path.splitext(os.path.basename(src))[0]
    done = []
    for ext in targets:
        ext = ext.strip().lower().lstrip(".")
        dst = stamp_name(src, ext, outdir, title)
        if ext == "md":
            with open(dst, "w", encoding="utf-8") as f:
                f.write(md)
        elif ext == "html":
            with open(dst, "w", encoding="utf-8") as f:
                f.write(to_html(md, ttl))
        elif ext == "txt":
            with open(dst, "w", encoding="utf-8") as f:
                f.write(to_txt(md, ttl))
        elif ext == "docx":
            with open(dst, "wb") as f:
                f.write(docx_bytes(md, ttl))
        else:
            print("  ⚠️ 不支持的格式：%s（支持 docx/html/txt/md）" % ext)
            continue
        done.append((ext, dst, os.path.getsize(dst)))
    return done


def collect_files(path, recursive):
    if os.path.isfile(path):
        return [path]
    out = []
    for root, _, files in os.walk(path):
        for f in files:
            if f.lower().endswith((".md", ".markdown", ".txt")):
                out.append(os.path.join(root, f))
        if not recursive:
            break
    return sorted(out)


def main():
    ap = argparse.ArgumentParser(description="Markdown 一键导出为主流文档格式（纯标准库）")
    ap.add_argument("path", help="Markdown 文件或目录")
    ap.add_argument("--to", default="docx,html,txt",
                    help="目标格式，逗号分隔：docx,html,txt,md（默认 docx,html,txt）")
    ap.add_argument("--outdir", default=None, help="输出目录（默认与源文件同级的 导出/）")
    ap.add_argument("--recursive", action="store_true", help="递归子目录")
    ap.add_argument("--title", default=None, help="指定文档标题（覆盖文件名）")
    args = ap.parse_args()

    files = collect_files(args.path, args.recursive)
    if not files:
        print("未找到 Markdown 文件：%s" % args.path)
        sys.exit(2)

    targets = [x for x in args.to.split(",") if x.strip()]
    outdir = args.outdir or os.path.join(
        os.path.dirname(os.path.abspath(files[0])) if len(files) == 1
        else os.path.abspath(args.path), "导出")

    print("Markdown 一键导出器")
    print("=" * 62)
    print("源文件：%d 份" % len(files))
    print("目标格式：%s" % "、".join(targets))
    print("输出目录：%s" % outdir)
    print("-" * 62)

    total = 0
    for fp in files:
        done = export_one(fp, targets, outdir, args.title if len(files) == 1 else None)
        name = os.path.basename(fp)
        if done:
            print("✅ %s" % name)
            for ext, dst, size in done:
                print("     %-5s → %s  (%.1f KB)" % (ext.upper(), os.path.basename(dst), size / 1024))
                total += 1
    print("-" * 62)
    print("完成：共生成 %d 个文件，输出目录 %s" % (total, outdir))
    print("提示：DOCX 可用 Word / WPS / 腾讯文档打开；HTML 用浏览器打开后 Ctrl+P 可另存为 PDF。")
    sys.exit(0)


if __name__ == "__main__":
    main()
