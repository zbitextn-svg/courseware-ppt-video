# -*- coding: utf-8 -*-
"""幼儿园课件透明卡片 —— 通用引擎（1920x1080）

用法：
    import kit
    kit.build(CARDS, "out.html")

字体：自动探测系统的中文显示字体（手写体/圆体）。也可用环境变量 CARD_FONT
指定 .ttf/.otf/.ttc，或把字体文件放到 assets/fonts/display.ttf。
"""
import base64
import io
import json
import os

from fontTools import subset
from fontTools.ttLib import TTFont

_HERE = os.path.dirname(os.path.abspath(__file__))
FONT_CANDIDATES = [
    os.environ.get("CARD_FONT"),
    os.path.join(os.path.dirname(_HERE), "assets", "fonts", "display.ttf"),
    os.path.expanduser("~/Library/Fonts/YSHaoShenTi-2.ttf"),
    os.path.expanduser("~/Library/Fonts/YSHaoShenTi.ttf"),
    os.path.expanduser("~/Library/Fonts/YanTi.ttf"),
    "/Library/Fonts/YSHaoShenTi.ttf",
    "/System/Library/Fonts/Supplemental/Songti.ttc",
]


def resolve_font():
    for p in FONT_CANDIDATES:
        if p and os.path.exists(p):
            return p
    raise SystemExit(
        "找不到中文显示字体。请设置环境变量 CARD_FONT 指向 .ttf/.otf，\n"
        "或把字体文件复制到 assets/fonts/display.ttf")


FONT_SRC = resolve_font()

CREAM = "#FAF6EC"
INK = "#2F2C26"
GRAY = "#7D7566"

DUR = 5000
TAIL = 6200

TINT = {}


def tint(hexc, mix=0.13):
    """把颜色混入米白，得到浅底"""
    hexc = hexc.lstrip("#")
    r, g, b = (int(hexc[i:i + 2], 16) for i in (0, 2, 4))
    br, bg, bb = 250, 246, 236
    return "#%02X%02X%02X" % (int(r * mix + br * (1 - mix)),
                             int(g * mix + bg * (1 - mix)),
                             int(b * mix + bb * (1 - mix)))


# ---------------------------------------------------------------- 图标
ICONS = {
    "ask": '''
      <path d="M16 18 C16 10 32 10 32 18 C32 24.5 24 23.5 24 30" stroke="{c}"
            stroke-width="4.2" fill="none" stroke-linecap="round"/>
      <circle cx="24" cy="37.5" r="3.1" fill="{c}"/>''',
    "eye": '''
      <path d="M6.5 24 C12 15.5 17.6 11.5 24 11.5 C30.4 11.5 36 15.5 41.5 24
               C36 32.5 30.4 36.5 24 36.5 C17.6 36.5 12 32.5 6.5 24 Z"
            stroke="{c}" stroke-width="3.1" fill="none" stroke-linejoin="round"/>
      <circle cx="24" cy="24" r="5.4" stroke="{c}" stroke-width="3" fill="none"/>
      <circle cx="24" cy="24" r="1.9" fill="{c}"/>''',
    "hand": '''
      <path d="M17 27.5 V14 a2.9 2.9 0 0 1 5.8 0 V24.5" stroke="{c}" stroke-width="2.9"
            fill="none" stroke-linecap="round" stroke-linejoin="round"/>
      <path d="M22.8 24 V11.8 a2.9 2.9 0 0 1 5.8 0 V24.5" stroke="{c}" stroke-width="2.9"
            fill="none" stroke-linecap="round" stroke-linejoin="round"/>
      <path d="M28.6 24.5 V15.5 a2.9 2.9 0 0 1 5.8 0 V30.5 c0 7.4-4.2 11.8-10.8 11.8
               C17.2 42.3 13 37.6 13 30.8 V27.4" stroke="{c}" stroke-width="2.9" fill="none"
            stroke-linecap="round" stroke-linejoin="round"/>''',
    "talk": '''
      <path d="M9 12.5 H39 V31 H24 L16 38 V31 H9 Z" stroke="{c}" stroke-width="3"
            fill="none" stroke-linejoin="round"/>
      <path d="M16.5 19.5 H31.5 M16.5 25 H26.5" stroke="{c}" stroke-width="2.5"
            stroke-linecap="round" opacity=".55"/>''',
    "check": '''
      <path d="M10 25.5 L19.5 35 L38.5 13" stroke="{c}" stroke-width="4.4" fill="none"
            stroke-linecap="round" stroke-linejoin="round"/>''',
    "cross": '''
      <path d="M13 13 L35 35 M35 13 L13 35" stroke="{c}" stroke-width="4.2"
            stroke-linecap="round"/>''',
    "star": '''
      <path d="M24 7.5 L30.4 20 L44.5 22 L34.2 31.8 L36.7 45.5 L24 38.8
               L11.3 45.5 L13.8 31.8 L3.5 22 L17.6 20 Z" stroke="{c}" stroke-width="3"
            fill="none" stroke-linejoin="round"/>''',
    "drop": '''
      <path d="M24 6.5 C24 6.5 36 21 36 29.5 A12 12 0 0 1 12 29.5 C12 21 24 6.5 24 6.5 Z"
            stroke="{c}" stroke-width="3.1" fill="none" stroke-linejoin="round"/>
      <path d="M18.5 30 A5.5 5.5 0 0 0 24 35.5" stroke="{c}" stroke-width="2.4"
            fill="none" stroke-linecap="round" opacity=".6"/>''',
    "sun": '''
      <circle cx="24" cy="24" r="8.5" stroke="{c}" stroke-width="3" fill="none"/>
      <path d="M24 5 V9.5 M24 38.5 V43 M5 24 H9.5 M38.5 24 H43
               M10.5 10.5 L13.7 13.7 M34.3 34.3 L37.5 37.5
               M37.5 10.5 L34.3 13.7 M13.7 34.3 L10.5 37.5"
            stroke="{c}" stroke-width="3" stroke-linecap="round"/>''',
    "moon": '''
      <path d="M31 8 C21 10 14 17.5 14 26 C14 34 20.5 40.5 29 40.5
               C33 40.5 36.5 39 39 36.5 C28 36.5 22 29.5 22 21.5 C22 16 25 11 31 8 Z"
            stroke="{c}" stroke-width="3" fill="none" stroke-linejoin="round"/>''',
    "leaf": '''
      <path d="M37.5 10.5 C37.5 25 27.5 36.5 12 37.5 C12 23 22 10.5 37.5 10.5 Z"
            stroke="{c}" stroke-width="3.1" fill="none" stroke-linejoin="round"/>
      <path d="M13 36.5 C18.5 30.5 27 21.5 36 12.5" stroke="{c}" stroke-width="2.2"
            opacity=".55" stroke-linecap="round"/>''',
    "tree": '''
      <path d="M24 44 V21" stroke="{c}" stroke-width="4.6" stroke-linecap="round"/>
      <path d="M24 33 C21.5 27.5 18 24 12.5 21" stroke="{c}" stroke-width="3.6"
            fill="none" stroke-linecap="round"/>
      <path d="M24 29 C27 23 31 20 36.5 18.5" stroke="{c}" stroke-width="3.6"
            fill="none" stroke-linecap="round"/>
      <path d="M24 21 C24 15.5 22.5 11.5 20 8.5" stroke="{c}" stroke-width="3" fill="none"
            stroke-linecap="round" opacity=".55"/>
      <path d="M24 21 C25.5 16 28 13 31 11" stroke="{c}" stroke-width="3" fill="none"
            stroke-linecap="round" opacity=".55"/>''',
    "brush": '''
      <path d="M32.5 8.5 L39.5 15.5 L21.5 33.5 L14.5 26.5 Z" stroke="{c}"
            stroke-width="3" fill="none" stroke-linejoin="round"/>
      <path d="M14.5 26.5 L8.5 40 L22 34 Z" stroke="{c}" stroke-width="2.8"
            fill="none" stroke-linejoin="round"/>
      <path d="M27 14 L34 21" stroke="{c}" stroke-width="2" opacity=".45"/>''',
    "palette": '''
      <path d="M24 8 C34.5 8 41 15 41 23.5 C41 30 36.5 32 30.5 31.5 C27 31.2 26.2 33 27.2 36
               C28.2 39.5 24.8 41 21 41 C13.8 41 8 34 8 24 C8 15 15 8 24 8 Z"
            stroke="{c}" stroke-width="3" fill="none" stroke-linejoin="round"/>
      <circle cx="16.5" cy="19" r="2.9" fill="{c}"/>
      <circle cx="24.5" cy="14.5" r="2.9" fill="{c}" opacity=".72"/>
      <circle cx="32" cy="19.5" r="2.9" fill="{c}" opacity=".45"/>''',
    "bin": '''
      <path d="M10.5 14.5 H37.5" stroke="{c}" stroke-width="3.2" stroke-linecap="round"/>
      <path d="M19 14.5 V10.5 H29 V14.5" stroke="{c}" stroke-width="2.8" fill="none"
            stroke-linejoin="round"/>
      <path d="M13.5 14.5 L16 39 H32 L34.5 14.5" stroke="{c}" stroke-width="3"
            fill="none" stroke-linejoin="round"/>
      <path d="M20.5 21 V33 M27.5 21 V33" stroke="{c}" stroke-width="2.4"
            stroke-linecap="round" opacity=".5"/>''',
    "recycle": '''
      <path d="M17 15.5 H31 L38 28" stroke="{c}" stroke-width="3.2" fill="none"
            stroke-linejoin="round" stroke-linecap="round"/>
      <path d="M13.5 34 L24 16 L31 29" stroke="{c}" stroke-width="3.2" fill="none"
            stroke-linejoin="round" stroke-linecap="round" opacity=".55"/>
      <path d="M34 24 L38 28.5 L33 31" stroke="{c}" stroke-width="3" fill="none"
            stroke-linecap="round" stroke-linejoin="round"/>''',
    "earth": '''
      <circle cx="24" cy="24" r="16" stroke="{c}" stroke-width="3" fill="none"/>
      <path d="M8 24 H40 M24 8 C30 14 30 34 24 40 M24 8 C18 14 18 34 24 40"
            stroke="{c}" stroke-width="2.4" fill="none" opacity=".5"/>''',
    "mask": '''
      <path d="M9 19 C9 15.5 39 15.5 39 19 V29 C39 35 9 35 9 29 Z" stroke="{c}"
            stroke-width="3" fill="none" stroke-linejoin="round"/>
      <path d="M9 21.5 L4.5 20 M39 21.5 L43.5 20" stroke="{c}" stroke-width="2.4"
            stroke-linecap="round" opacity=".6"/>
      <path d="M14 22 H34 M14 26 H34" stroke="{c}" stroke-width="2.2" opacity=".45"/>''',
    "bridge": '''
      <path d="M5 26 H43" stroke="{c}" stroke-width="3.2" stroke-linecap="round"/>
      <path d="M9 26 A15 15 0 0 1 39 26" stroke="{c}" stroke-width="3" fill="none"/>
      <path d="M9 26 V39 M39 26 V39 M15 22.5 V39 M24 21 V39 M33 22.5 V39"
            stroke="{c}" stroke-width="2.4" opacity=".55" stroke-linecap="round"/>''',
    "book": '''
      <path d="M24 15 C19 10 11 9.5 6.5 10.5 V34 C11 33 19 33.5 24 38.5
               C29 33.5 37 33 41.5 34 V10.5 C37 9.5 29 10 24 15 Z"
            stroke="{c}" stroke-width="3" fill="none" stroke-linejoin="round"/>
      <path d="M24 15 V38.5" stroke="{c}" stroke-width="2.4" opacity=".45"/>''',
    "music": '''
      <path d="M20 33 V12.5 L36 9 V29.5" stroke="{c}" stroke-width="3" fill="none"
            stroke-linejoin="round" stroke-linecap="round"/>
      <ellipse cx="15.5" cy="34.5" rx="5.5" ry="4.2" stroke="{c}" stroke-width="2.8"
               fill="none"/>
      <ellipse cx="31.5" cy="31" rx="5.5" ry="4.2" stroke="{c}" stroke-width="2.8"
               fill="none"/>''',
    "heart": '''
      <path d="M24 39 C10.5 29 6 22.5 10 16.5 C14 10.5 22 12.5 24 18.5
               C26 12.5 34 10.5 38 16.5 C42 22.5 37.5 29 24 39 Z"
            stroke="{c}" stroke-width="3" fill="none" stroke-linejoin="round"/>''',
    "clock": '''
      <circle cx="24" cy="24" r="16" stroke="{c}" stroke-width="3" fill="none"/>
      <path d="M24 14 V24 L32 28" stroke="{c}" stroke-width="2.8" fill="none"
            stroke-linecap="round" stroke-linejoin="round"/>''',
    "body": '''
      <circle cx="24" cy="11" r="5" stroke="{c}" stroke-width="2.8" fill="none"/>
      <path d="M24 16 V30 M24 20 L14 26 M24 20 L34 26 M24 30 L16 41 M24 30 L32 41"
            stroke="{c}" stroke-width="2.8" fill="none" stroke-linecap="round"
            stroke-linejoin="round"/>''',
    "bulb": '''
      <path d="M24 7 C17 7 12 12 12 18.5 C12 23.5 15 26.5 16.5 30 H31.5
               C33 26.5 36 23.5 36 18.5 C36 12 31 7 24 7 Z"
            stroke="{c}" stroke-width="3" fill="none" stroke-linejoin="round"/>
      <path d="M18 33.5 H30 M19 38 H29" stroke="{c}" stroke-width="2.8"
            stroke-linecap="round"/>''',
    "cup": '''
      <path d="M13 12 H32 V30 C32 35 28 38 22.5 38 C17 38 13 35 13 30 Z"
            stroke="{c}" stroke-width="3" fill="none" stroke-linejoin="round"/>
      <path d="M32 18 H36 C39 18 39 26 32 26" stroke="{c}" stroke-width="2.8"
            fill="none" stroke-linecap="round"/>''',
    "window": '''
      <path d="M9 10 H39 V38 H9 Z" stroke="{c}" stroke-width="3" fill="none"
            stroke-linejoin="round"/>
      <path d="M24 10 V38 M9 24 H39" stroke="{c}" stroke-width="2.6" opacity=".55"/>''',
    "flag": '''
      <path d="M12 42 V8" stroke="{c}" stroke-width="3.2" stroke-linecap="round"/>
      <path d="M12 9 H36 L30 17 L36 25 H12 Z" stroke="{c}" stroke-width="3" fill="none"
            stroke-linejoin="round"/>''',
}


def ico(name, color):
    return ICONS[name].format(c=color)


# ---------------------------------------------------------------- 版式工具
def anim(m="up", d=0):
    return f'data-m="{m}" data-d="{d}"'


def pos_css(d):
    if d.get("pos") == "right":
        return "right:96px"
    if d.get("pos") == "center":
        return "left:0;right:0;margin:0 auto;width:fit-content"
    return "left:96px"


def dir_of(d):
    return {"right": "right", "center": "up"}.get(d.get("pos"), "left")


def head_html(d, cls="gh"):
    kick = f'<i class="{cls}k">{d["kicker"]}</i>' if d.get("kicker") else ""
    return (f'<div class="{cls}head" {anim("up", 130)}>'
            f'<span class="{cls}dot"></span><b>{d["head"]}</b>{kick}</div>')


def card_open(d, extra=""):
    c = d["color"]
    w = f';width:{d["w"]}px' if d.get("w") else ""
    return (f'<div class="card" data-dir="{dir_of(d)}" '
            f'style="{pos_css(d)};--c:{c}{w}{extra}">')


# ---------------------------------------------------------------- 各类卡片
def build_title(d):
    return f'''{card_open(d)}
  <div class="sheet title">
    <div class="kicker" {anim("up", 150)}>{d["kicker"]}</div>
    <div class="h1" {anim("up", 260)}>{d["h1"]}</div>
    <div class="rule" {anim("right", 430)}></div>
    <div class="sub" {anim("up", 520)}>{d["sub"]}</div>
  </div>
</div>'''


def build_flow(d):
    c = d["color"]
    parts = []
    for i, nd in enumerate(d["nodes"]):
        if i:
            parts.append(f'<div class="farrow" {anim("up", 300 + i * 120)}>→</div>')
        parts.append(f'<div class="fnode" {anim("pop", 250 + i * 120)}>{nd}</div>')
    return f'''{card_open(d)}
  <div class="fhead" {anim("up", 130)}><span class="fdot"></span><b>{d["head"]}</b><i>{d["kicker"]}</i></div>
  <div class="frow">{''.join(parts)}</div>
</div>'''


def build_quote(d):
    c = d["color"]
    lines = "".join(f'<div class="ql" {anim("up", 220 + i * 150)}>{ln}</div>'
                    for i, ln in enumerate(d["lines"]))
    return f'''{card_open(d)}
  <div class="sheet quote{" big" if d.get("big") else ""}">
    <div class="qbody">{lines}</div>
    <div class="qsrc" {anim("up", 220 + 150 * len(d["lines"]) + 120)}>{d["src"]}</div>
  </div>
</div>'''


def build_poem(d):
    c = d["color"]
    lines = "".join(f'<div class="pl" {anim("up", 200 + i * 110)}>{ln}</div>'
                    for i, ln in enumerate(d["lines"]))
    src = f'<div class="qsrc" {anim("up", 200 + 110 * len(d["lines"]) + 140)}>{d["src"]}</div>' if d.get("src") else ""
    return f'''{card_open(d)}
  <div class="sheet poem">
    {head_html(d, "gh")}
    <div class="pbody">{lines}</div>
    {src}
  </div>
</div>'''


def build_levels(d):
    c = d["color"]
    cols = d.get("cols", 3)
    cells = []
    for i, row in enumerate(d["rows"]):
        tag, name, desc = row[0], row[1], row[2]
        cells.append(f'''<div class="lcell" {anim("up", 260 + i * 150)}>
      <div class="ltag"><i style="background:{c}"></i>{tag}</div>
      <div class="lname">{name}</div>
      <div class="ldesc">{desc}</div>
    </div>''')
    return f'''{card_open(d)}
  <div class="sheet levels" style="width:100%">
    {head_html(d, "lh")}
    <div class="lrow" style="grid-template-columns:repeat({cols},1fr)">{''.join(cells)}</div>
  </div>
</div>'''


def build_grid(d):
    c = d["color"]
    cols = d.get("cols", 2)
    cells = []
    for i, it in enumerate(d["items"]):
        ic, name, desc = it[0], it[1], it[2]
        col = it[3] if len(it) > 3 else c
        if ic:
            bg, fg = (col, "#FFFFFF") if d.get("icon_solid") else (tint(col), col)
            mark = f'<div class="gico" style="background:{bg}"><svg viewBox="0 0 48 48">{ico(ic, fg)}</svg></div>'
        elif len(it) > 3:
            mark = f'<div class="gnum solid" style="background:{col}">{i + 1:02d}</div>'
        else:
            mark = f'<div class="gnum" style="color:{col};background:{tint(col)}">{i + 1:02d}</div>'
        cells.append(f'''<div class="gcell" {anim("up", 240 + i * 130)}>
      {mark}
      <div class="gtx"><b>{name}</b><span>{desc}</span></div>
    </div>''')
    return f'''{card_open(d)}
  <div class="sheet grid" style="width:100%">
    {head_html(d, "gh")}
    <div class="ggrid" style="grid-template-columns:repeat({cols},1fr)">{''.join(cells)}</div>
  </div>
</div>'''


def build_chips(d):
    c = d["color"]
    chips = "".join(f'<div class="chip" {anim("pop", 220 + i * 80)}>{t}</div>'
                    for i, t in enumerate(d["chips"]))
    return f'''{card_open(d)}
  <div class="sheet chips" style="width:100%">
    {head_html(d, "ch")}
    <div class="cwrap">{chips}</div>
  </div>
</div>'''


def build_steps(d):
    c = d["color"]
    rows = []
    for i, (name, desc) in enumerate(d["steps"]):
        rows.append(f'''<div class="sitem" {anim("up", 250 + i * 140)}>
      <div class="snum">{i + 1:02d}</div>
      <div class="stx"><b>{name}</b><span>{desc}</span></div>
    </div>''')
    return f'''{card_open(d)}
  <div class="sheet steps" style="width:100%">
    {head_html(d, "sh")}
    <div class="slist">{''.join(rows)}</div>
  </div>
</div>'''


def build_stats(d):
    c = d["color"]
    boxes = []
    for i, (num, unit) in enumerate(d["boxes"]):
        boxes.append(f'''<div class="sbox" {anim("pop", 260 + i * 170)}>
      <div class="sbig">{num}</div><div class="sunit">{unit}</div>
    </div>''')
    return f'''{card_open(d)}
  <div class="sheet stats" style="width:100%">
    <div class="slabel" {anim("up", 140)}>{d["label"]}</div>
    <div class="srow">{''.join(boxes)}</div>
    <div class="snote" {anim("up", 640)}>{d["note"]}</div>
  </div>
</div>'''


def build_swatch(d):
    c = d["color"]
    n = len(d["items"])
    cells = []
    for i, (col, name, desc) in enumerate(d["items"]):
        cells.append(f'''<div class="swcell" {anim("up", 260 + i * 130)}>
      <div class="swdot" style="background:{col}"></div>
      <div class="swname">{name}</div>
      <div class="swdesc">{desc}</div>
    </div>''')
    note = f'<div class="swnote" {anim("up", 260 + 130 * n + 120)}>{d["note"]}</div>' if d.get("note") else ""
    return f'''{card_open(d)}
  <div class="sheet swatch" style="width:100%">
    {head_html(d, "gh")}
    <div class="swrow" style="grid-template-columns:repeat({n},1fr)">{''.join(cells)}</div>
    {note}
  </div>
</div>'''


def build_chars(d):
    c = d["color"]
    fs = f' style="font-size:{d["fs"]}px"' if d.get("fs") else ""
    cells = []
    for i, (ch, note) in enumerate(d["items"]):
        cells.append(f'''<div class="charcell" {anim("pop", 240 + i * 130)}>
      <b{fs}>{ch}</b><span>{note}</span>
    </div>''')
    note = f'<div class="swnote" {anim("up", 240 + 130 * len(d["items"]) + 120)}>{d["note"]}</div>' if d.get("note") else ""
    return f'''{card_open(d)}
  <div class="sheet charsheet" style="width:100%">
    {head_html(d, "gh")}
    <div class="charrow">{''.join(cells)}</div>
    {note}
  </div>
</div>'''


def build_compare(d):
    c = d["color"]
    out = []
    for i, (side, tone) in enumerate([(d["left"], d.get("left_tone", "#B9AFA0")),
                                      (d["right"], d.get("right_tone", c))]):
        title, lines = side
        ls = "".join(f'<p>{x}</p>' for x in lines)
        out.append(f'''<div class="ccell" {anim("up", 250 + i * 160)}>
      <div class="ctag"><i style="background:{tone}"></i>{title}</div>
      <div class="ctxt">{ls}</div>
    </div>''')
    note = f'<div class="swnote" {anim("up", 640)}>{d["note"]}</div>' if d.get("note") else ""
    return f'''{card_open(d)}
  <div class="sheet compare" style="width:100%">
    {head_html(d, "gh")}
    <div class="crow">{''.join(out)}</div>
    {note}
  </div>
</div>'''


def build_end(d):
    c = d["color"]
    cells = []
    for i, (num, unit) in enumerate(d["stats"]):
        cells.append(f'''<div class="ecell" {anim("up", 540 + i * 130)}>
      <b>{num}</b><span>{unit}</span></div>''')
    return f'''{card_open(d)}
  <div class="sheet end" style="width:100%">
    <div class="eh1" {anim("up", 200)}>{d["h1"]}</div>
    <div class="esub" {anim("up", 330)}>{d["sub"]}</div>
    <div class="erow">{''.join(cells)}</div>
  </div>
</div>'''


BUILDERS = dict(title=build_title, flow=build_flow, quote=build_quote, poem=build_poem,
                levels=build_levels, grid=build_grid, chips=build_chips, steps=build_steps,
                stats=build_stats, swatch=build_swatch, chars=build_chars,
                compare=build_compare, end=build_end)


# ---------------------------------------------------------------- 字体子集
def collect(o, s):
    if isinstance(o, str):
        s |= set(o)
    elif isinstance(o, (list, tuple)):
        for x in o:
            collect(x, s)
    elif isinstance(o, dict):
        for v in o.values():
            collect(v, s)


def all_text(cards):
    s = set()
    for d in cards:
        collect({k: v for k, v in d.items() if k != "color"}, s)
    s |= set("0123456789·／，。？、（）“”《》 ·—→↓↑ABCDEFGHIJKLMNOPQRSTUVWXYZ")
    return "".join(sorted(s))


def font_b64(text):
    if FONT_SRC.lower().endswith(".ttc"):
        font = TTFont(FONT_SRC, fontNumber=0)
    else:
        font = TTFont(FONT_SRC)
    opt = subset.Options()
    opt.flavor = "woff2"
    opt.desubroutinize = True
    opt.layout_features = ["*"]
    sub = subset.Subsetter(options=opt)
    sub.populate(text=text)
    sub.subset(font)
    buf = io.BytesIO()
    font.flavor = "woff2"
    font.save(buf)
    return base64.b64encode(buf.getvalue()).decode()


# ---------------------------------------------------------------- 装配
DEFAULT_W = dict(grid=900, steps=900, levels=1180, stats=780, compare=940,
                 chars=900, chips=800, swatch=900, poem=940, flow=1200, end=900)


def build(cards, out_html, verbose=True):
    for d in cards:
        if "w" not in d and DEFAULT_W.get(d["t"]):
            d["w"] = DEFAULT_W[d["t"]]
    body = [BUILDERS[d["t"]](d) for d in cards]
    durs = [d.get("dur", DUR) for d in cards]
    if len(durs) and "dur" not in cards[-1]:
        durs[-1] = TAIL
    html = (CSS_HTML
            .replace("__FONT__", font_b64(all_text(cards)))
            .replace("__BODY__", "\n".join(body))
            .replace("__CREAM__", CREAM)
            .replace("__INK__", INK)
            .replace("__GRAY__", GRAY)
            .replace("__DURS__", "[" + ",".join(str(x) for x in durs) + "]"))
    with open(out_html, "w", encoding="utf-8") as f:
        f.write(html)
    # 附带元信息，供 qa_cards.py 推算卡片数/时长
    with open(out_html + ".meta.json", "w", encoding="utf-8") as f:
        json.dump({"n": len(cards), "durs": durs, "inn": 640, "out": 480},
                  f, ensure_ascii=False)
    if verbose:
        print("HTML:", out_html, "%.1f KB" % (os.path.getsize(out_html) / 1024),
              "| 卡片", len(cards), "| 总时长 %.1fs" % (sum(durs) / 1000))
    return durs


CSS_HTML = r'''<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<style>
@font-face {
  font-family: 'SZDisplay';
  src: url(data:font/woff2;base64,__FONT__) format('woff2');
  font-display: block;
}
* { box-sizing: border-box; }
html, body {
  margin: 0; padding: 0; width: 1920px; height: 1080px;
  background: transparent; overflow: hidden;
  -webkit-font-smoothing: antialiased;
  font-family: -apple-system, 'PingFang SC', 'Hiragino Sans GB', sans-serif;
}
.stage { position: relative; width: 1920px; height: 1080px; }
.card { position: absolute; height: 1080px; display: flex; flex-direction: column;
        justify-content: center; align-items: flex-start;
        will-change: transform, opacity; }
.sheet {
  position: relative; background: __CREAM__; border-radius: 28px;
  box-shadow: 0 20px 46px -16px rgba(47,44,38,.42),
              0 4px 12px rgba(47,44,38,.06),
              inset 0 0 0 1px rgba(47,44,38,.06);
}

/* ---- 封面 ---- */
.title { width: 880px; padding: 42px 56px 44px; }
.kicker { font-size: 19px; letter-spacing: 5px; color: __GRAY__; }
.h1 { font-family: 'SZDisplay', sans-serif; font-size: 86px; line-height: 1.1;
      color: __INK__; letter-spacing: 3px; margin-top: 16px; }
.rule { width: 132px; height: 6px; border-radius: 3px; background: var(--c); margin: 26px 0 20px; }
.sub { font-size: 23px; color: __GRAY__; letter-spacing: 1px; }

/* ---- 通用块头 ---- */
.ghhead, .shhead, .chhead, .lhhead { display: flex; align-items: center; gap: 13px;
                      padding: 0 6px 15px; border-bottom: 2px solid rgba(47,44,38,.08); }
.ghdot, .shdot, .chdot, .lhdot { width: 12px; height: 12px; border-radius: 50%;
                                 background: var(--c); flex: none; }
.ghhead b, .shhead b, .chhead b, .lhhead b { font-family: 'SZDisplay', sans-serif; font-size: 36px;
                             color: var(--c); letter-spacing: 1.4px; }
.ghk, .shk, .chk, .lhk { margin-left: auto; font-style: normal; font-size: 13px;
                         letter-spacing: 2.6px; color: __GRAY__; opacity: .62; }

/* ---- 三关 ---- */
.levels { width: 1180px; padding: 26px 34px 30px; }
.lrow { display: grid; gap: 16px; padding-top: 18px; }
.lcell { background: #FFFFFF; border-radius: 22px; padding: 20px 22px 22px;
         box-shadow: 0 2px 10px rgba(47,44,38,.05); }
.ltag { display: flex; align-items: center; gap: 9px; font-size: 15px; letter-spacing: 1.6px;
        color: __GRAY__; }
.ltag i { width: 9px; height: 9px; border-radius: 50%; display: block; flex: none; }
.lname { font-family: 'SZDisplay', sans-serif; font-size: 34px; color: __INK__;
         letter-spacing: 2px; margin-top: 12px; }
.ldesc { font-size: 16px; color: __GRAY__; margin-top: 10px; line-height: 1.35; }

/* ---- 图标列表 ---- */
.grid { width: 900px; padding: 26px 30px 24px; }
.ggrid { display: grid; gap: 14px; padding-top: 16px; }
.gcell { display: flex; gap: 16px; align-items: center; background: #FFFFFF;
         border-radius: 20px; padding: 16px 18px; box-shadow: 0 2px 8px rgba(47,44,38,.05); }
.gico { width: 68px; height: 68px; border-radius: 18px; flex: none;
        display: flex; align-items: center; justify-content: center; }
.gico svg { width: 48px; height: 48px; display: block; }
.gnum { width: 68px; height: 68px; border-radius: 18px; flex: none;
        display: flex; align-items: center; justify-content: center;
        font-family: 'SZDisplay', sans-serif; font-size: 28px; letter-spacing: .5px; }
.gnum.solid { color: #FFFFFF; font-size: 26px; }
.gtx b { display: block; font-size: 25px; font-weight: 600; color: __INK__; line-height: 1.2;
         letter-spacing: .6px; }
.gtx span { display: block; font-size: 17px; color: __GRAY__; margin-top: 6px; line-height: 1.32; }

/* ---- 胶囊 ---- */
.chips { width: 800px; padding: 26px 34px 28px; }
.cwrap { display: flex; flex-wrap: wrap; gap: 12px; padding-top: 18px; }
.chip { background: #FFFFFF; border-radius: 999px; padding: 11px 24px; font-size: 21px;
        color: __INK__; box-shadow: 0 2px 8px rgba(47,44,38,.06);
        will-change: transform, opacity; }

/* ---- 引文 ---- */
.quote { width: max-content; min-width: 780px; padding: 38px 52px 34px 62px; }
.quote::before { content: ''; position: absolute; left: 24px; top: 34px; bottom: 30px;
                 width: 5px; border-radius: 3px; background: var(--c); opacity: .5; }
.quote.big .ql { font-size: 46px; line-height: 1.36; }
.quote.big .qsrc { font-size: 20px; }
.qbody { position: relative; }
.ql { font-family: 'SZDisplay', sans-serif; font-size: 36px; line-height: 1.48;
      color: __INK__; letter-spacing: .4px; white-space: nowrap; }
.qsrc { margin-top: 16px; padding-top: 13px; font-size: 19px; color: __GRAY__;
        border-top: 1.6px solid rgba(47,44,38,.10); line-height: 1.5; white-space: nowrap;
        width: 100%; }

/* ---- 诗歌 / 长段 ---- */
.poem { width: 940px; padding: 30px 44px 28px; }
.pbody { padding: 20px 0 4px; }
.pl { font-family: 'SZDisplay', sans-serif; font-size: 34px; line-height: 1.62;
      color: __INK__; letter-spacing: 1px; }
.poem .qsrc { margin-top: 18px; white-space: normal; font-size: 18px; }

/* ---- 步骤 ---- */
.steps { width: 900px; padding: 26px 34px 22px; }
.slist { padding-top: 6px; }
.sitem { display: flex; gap: 18px; align-items: flex-start; padding: 13px 2px 12px; }
.sitem + .sitem { border-top: 1.6px dashed rgba(125,117,102,.22); }
.snum { width: 40px; height: 40px; border-radius: 50%; flex: none; background: var(--c);
        color: #fff; font-family: 'SZDisplay', sans-serif; font-size: 17px;
        display: flex; align-items: center; justify-content: center; letter-spacing: .5px; }
.stx b { display: block; font-size: 27px; font-weight: 600; color: __INK__; letter-spacing: .6px;
         line-height: 1.25; }
.stx span { display: block; font-size: 18.5px; color: __GRAY__; margin-top: 5px; line-height: 1.35; }

/* ---- 大数字 ---- */
.stats { width: 780px; padding: 32px 40px 28px; }
.slabel { font-size: 17px; letter-spacing: 3px; color: __GRAY__; padding-left: 4px; }
.srow { display: flex; gap: 18px; margin-top: 18px; }
.sbox { flex: 1; background: #FFFFFF; border-radius: 22px; padding: 22px 18px 20px;
        text-align: center; box-shadow: 0 2px 10px rgba(47,44,38,.05); }
.sbig { font-family: 'SZDisplay', sans-serif; font-size: 82px; line-height: 1;
        color: var(--c); letter-spacing: 2px; }
.sunit { font-size: 17px; color: __GRAY__; margin-top: 10px; letter-spacing: 1px; }
.snote { margin-top: 20px; padding-top: 14px; font-size: 17px; color: __GRAY__;
         border-top: 1.6px solid rgba(47,44,38,.10); text-align: center; }

/* ---- 色卡 ---- */
.swatch { width: 900px; padding: 26px 34px 24px; }
.swrow { display: grid; gap: 14px; padding-top: 18px; }
.swcell { background: #FFFFFF; border-radius: 22px; padding: 24px 16px 22px; text-align: center;
          box-shadow: 0 2px 10px rgba(47,44,38,.05); }
.swdot { width: 86px; height: 86px; border-radius: 50%; margin: 0 auto 18px;
         box-shadow: inset 0 0 0 5px rgba(255,255,255,.92), 0 8px 18px -8px rgba(47,44,38,.55); }
.swname { font-family: 'SZDisplay', sans-serif; font-size: 30px; color: __INK__; letter-spacing: 2px; }
.swdesc { font-size: 16px; color: __GRAY__; margin-top: 8px; }
.swnote { margin-top: 18px; padding-top: 13px; font-size: 17px; color: __GRAY__;
          border-top: 1.6px solid rgba(47,44,38,.10); text-align: center; letter-spacing: .8px; }

/* ---- 大字 ---- */
.charsheet { width: 900px; padding: 26px 30px 24px; }
.charrow { display: flex; gap: 10px; padding-top: 18px; justify-content: space-between; }
.charcell { flex: 1; text-align: center; background: #FFFFFF; border-radius: 20px;
            padding: 18px 6px 16px; box-shadow: 0 2px 8px rgba(47,44,38,.05); }
.charcell b { display: block; font-family: 'Songti SC', 'STSong', 'Times New Roman', serif;
              font-size: 74px; font-weight: 700; line-height: 1.16; color: var(--c);
              letter-spacing: 3px; }
.charcell span { display: block; font-size: 15px; color: __GRAY__; margin-top: 10px;
                 line-height: 1.3; }

/* ---- 对比 ---- */
.compare { width: 940px; padding: 26px 34px 24px; }
.crow { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; padding-top: 18px; }
.ccell { background: #FFFFFF; border-radius: 22px; padding: 20px 22px 22px;
         box-shadow: 0 2px 10px rgba(47,44,38,.05); }
.ctag { display: flex; align-items: center; gap: 9px; font-family: 'SZDisplay', sans-serif;
        font-size: 30px; color: __INK__; letter-spacing: 1.4px; }
.ctag i { width: 10px; height: 10px; border-radius: 50%; flex: none; }
.ctxt { margin-top: 12px; }
.ctxt p { margin: 0 0 7px; font-size: 18.5px; line-height: 1.55; color: __GRAY__; }

/* ---- 流程 ---- */
.fhead { display: flex; align-items: center; gap: 12px; margin-bottom: 16px; padding-left: 4px; }
.fdot { width: 11px; height: 11px; border-radius: 50%; background: var(--c); }
.fhead b { font-family: 'SZDisplay', sans-serif; font-size: 26px; color: var(--c);
           letter-spacing: 1.4px; }
.fhead i { font-style: normal; font-size: 13px; letter-spacing: 2.4px; color: __GRAY__; opacity: .6; }
.frow { display: flex; align-items: center; gap: 12px; justify-content: center; width: 100%; }
.flowcard { align-items: stretch !important; }
.flowcard .fhead { justify-content: center; padding-left: 0; }
.fnode { background: __CREAM__; border-radius: 999px; padding: 18px 36px; font-size: 30px;
         color: __INK__; letter-spacing: 1px; white-space: nowrap;
         box-shadow: 0 14px 30px -14px rgba(47,44,38,.42), 0 3px 10px rgba(47,44,38,.05),
                     inset 0 0 0 1px rgba(47,44,38,.06); }
.farrow { color: var(--c); font-size: 24px; opacity: .65; }

/* ---- 结尾 ---- */
.end { width: 900px; padding: 40px 46px 34px; }
.eh1 { font-family: 'SZDisplay', sans-serif; font-size: 62px; line-height: 1.15;
       color: __INK__; letter-spacing: 2.6px; }
.esub { font-size: 21px; color: __GRAY__; margin-top: 14px; letter-spacing: .8px; }
.erow { display: flex; gap: 16px; margin-top: 28px; padding-top: 22px;
        border-top: 1.6px solid rgba(47,44,38,.10); }
.ecell { flex: 1; text-align: center; }
.ecell b { font-family: 'SZDisplay', sans-serif; font-size: 52px; color: var(--c); line-height: 1; }
.ecell span { display: block; font-size: 16px; color: __GRAY__; margin-top: 8px; letter-spacing: .6px; }
</style></head>
<body><div class="stage">
__BODY__
</div>
<script>
const DURS = __DURS__;
const IN = 640, OUT = 480;
const cards = [];
[].slice.call(document.querySelectorAll('.card')).forEach(function (el, idx) {
  el.style.display = 'none';
  cards.push({
    el: el,
    dur: DURS[idx],
    items: [].slice.call(el.querySelectorAll('[data-m]')).map(function (n) {
      return { el: n, m: n.dataset.m, d: parseInt(n.dataset.d || 0, 10) };
    })
  });
});

function clamp01(v) { return v < 0 ? 0 : (v > 1 ? 1 : v); }
function easeOutCubic(t) { return 1 - Math.pow(1 - t, 3); }
function easeOutBack(t) {
  const c1 = 1.34, c3 = c1 + 1;
  return 1 + c3 * Math.pow(t - 1, 3) + c1 * Math.pow(t - 1, 2);
}

window.__render = function (i, t) {
  for (let k = 0; k < cards.length; k++) cards[k].el.style.display = (k === i) ? 'flex' : 'none';
  const c = cards[i], el = c.el, dur = c.dur;
  const oms = Math.min(OUT, dur * 0.16);

  const pIn = clamp01(t / IN), eIn = easeOutCubic(pIn);
  const pOut = clamp01((t - (dur - oms)) / oms), eOut = easeOutCubic(pOut);
  const dir = el.dataset.dir || 'left', dist = 64;
  let tx = 0, ty = 0;
  if (dir === 'left') tx = -dist * (1 - eIn);
  else if (dir === 'right') tx = dist * (1 - eIn);
  else ty = dist * 0.6 * (1 - eIn);
  el.style.transform = 'translate(' + tx.toFixed(2) + 'px,' +
                       (ty - 20 * eOut).toFixed(2) + 'px)';
  el.style.opacity = (eIn * (1 - eOut)).toFixed(4);

  for (let j = 0; j < c.items.length; j++) {
    const a = c.items[j], n = a.el;
    const p = clamp01((t - a.d) / 440);
    let e = easeOutCubic(p), tf = '';
    if (a.m === 'pop') {
      e = easeOutBack(p);
      tf = 'scale(' + (0.55 + 0.45 * e).toFixed(4) + ')';
      n.style.opacity = clamp01(p * 1.7).toFixed(4);
    } else if (a.m === 'up') {
      tf = 'translateY(' + (20 * (1 - e)).toFixed(2) + 'px)';
      n.style.opacity = e.toFixed(4);
    } else if (a.m === 'right') {
      tf = 'translateX(' + (-32 * (1 - e)).toFixed(2) + 'px)';
      n.style.opacity = e.toFixed(4);
    } else if (a.m === 'bean') {
      e = easeOutBack(p);
      tf = 'scale(' + (0.24 + 0.76 * e).toFixed(4) + ') rotate(' +
           (-16 * (1 - e)).toFixed(2) + 'deg)';
      n.style.opacity = clamp01(p * 1.6).toFixed(4);
    } else {
      n.style.opacity = e.toFixed(4);
    }
    n.style.transform = tf;
  }
  return true;
};

window.__meta = { n: cards.length, durs: DURS, inn: IN, out: OUT, live: [] };
window.__render(0, DURS[0] - 600);
</script></body></html>'''
