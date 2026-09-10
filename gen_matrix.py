# -*- coding: utf-8 -*-
"""生成 Matrix 数字雨 SVG 横幅（自托管，无外部服务依赖）

用法：python gen_matrix.py
输出：assets/matrix-banner.svg  assets/matrix-footer.svg
只用标准库，无需 pip install。
"""
import os
import random

KATAKANA = "アイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨラリルレロワン"
GLYPHS = list("0123456789" * 3 + "ABCDEFGHJKLMNPQRSTUVWXYZ" + "[]{}/|=+*%$@!?" + KATAKANA)

FONT = "'Share Tech Mono','Fira Code','DejaVu Sans Mono','Consolas',monospace"


def build(width, height, title, subtitle, seed,
          col_w=20, row_h=20, n_rows=20, title_size=72, out=None):
    rnd = random.Random(seed)
    n_cols = width // col_w
    span = n_rows * row_h

    p = []
    p.append(
        '<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" '
        'viewBox="0 0 %d %d" role="img" aria-label="%s">'
        % (width, height, width, height, title or subtitle)
    )

    # ---------------- defs ----------------
    p.append("<defs>")
    p.append(
        '<linearGradient id="edge" x1="0" y1="0" x2="0" y2="1">'
        '<stop offset="0%" stop-color="#0D0208" stop-opacity="1"/>'
        '<stop offset="16%" stop-color="#0D0208" stop-opacity="0"/>'
        '<stop offset="84%" stop-color="#0D0208" stop-opacity="0"/>'
        '<stop offset="100%" stop-color="#0D0208" stop-opacity="1"/>'
        "</linearGradient>"
    )
    p.append(
        '<radialGradient id="vig" cx="50%" cy="50%" r="62%">'
        '<stop offset="0%" stop-color="#0D0208" stop-opacity="0.95"/>'
        '<stop offset="55%" stop-color="#0D0208" stop-opacity="0.74"/>'
        '<stop offset="100%" stop-color="#0D0208" stop-opacity="0"/>'
        "</radialGradient>"
    )
    # 副标题暗条：中间实、两端淡出，避免出现生硬的矩形边
    p.append(
        '<linearGradient id="band" x1="0" y1="0" x2="1" y2="0">'
        '<stop offset="0%" stop-color="#0D0208" stop-opacity="0"/>'
        '<stop offset="12%" stop-color="#0D0208" stop-opacity="0.93"/>'
        '<stop offset="88%" stop-color="#0D0208" stop-opacity="0.93"/>'
        '<stop offset="100%" stop-color="#0D0208" stop-opacity="0"/>'
        "</linearGradient>"
    )
    p.append(
        '<filter id="glow" x="-30%" y="-60%" width="160%" height="220%">'
        '<feGaussianBlur stdDeviation="3" result="b"/>'
        "<feMerge><feMergeNode in=\"b\"/><feMergeNode in=\"b\"/>"
        "<feMergeNode in=\"SourceGraphic\"/></feMerge>"
        "</filter>"
    )
    p.append("</defs>")

    # ---------------- style ----------------
    css = (
        ".g{font-family:%s;font-size:16px}"
        "@keyframes fall{from{transform:translateY(%dpx)}to{transform:translateY(%dpx)}}"
        ".col{animation-name:fall;animation-timing-function:linear;"
        "animation-iteration-count:infinite}"
        "@keyframes fk{0%%,100%%{opacity:.85}45%%{opacity:.08}}"
        ".fk{animation:fk 1.1s steps(2,end) infinite}"
        "@keyframes fk2{0%%,100%%{opacity:.55}50%%{opacity:1}}"
        ".fk2{animation:fk2 .55s ease-in-out infinite}"
        "@keyframes cur{0%%,49%%{opacity:1}50%%,100%%{opacity:0}}"
        ".cur{animation:cur 1s steps(1,end) infinite}"
        "@keyframes scan{from{transform:translateY(-8px)}to{transform:translateY(%dpx)}}"
        ".scan{animation:scan 5.5s linear infinite}"
        "@keyframes breathe{0%%,100%%{opacity:.88}50%%{opacity:1}}"
        ".ttl{animation:breathe 3.4s ease-in-out infinite}"
    ) % (FONT, -span, height, height + 8)
    p.append("<style>%s</style>" % css)

    # ---------------- 背景 ----------------
    p.append('<rect width="%d" height="%d" fill="#0D0208"/>' % (width, height))

    # ---------------- 数字雨 ----------------
    # 体积优化：颜色/透明度按 depth 离散成 d0..dN 若干个 class 写进 <style>，
    # 每个 <text> 只留 y 和 class；x 提到外层 g 的 transform 上。
    # 这样单个字符从 ~95 字节降到 ~30 字节。
    def depth_style(depth):
        if depth == 0:
            return "#D8FFE0", 1.0
        if depth == 1:
            return "#7CFFA0", 0.95
        if depth <= 3:
            return "#00FF41", 0.90
        if depth <= 7:
            return "#00C82C", max(0.20, 0.85 - depth * 0.07)
        return "#008F11", max(0.08, 0.60 - depth * 0.045)

    depth_css = []
    for d in range(n_rows):
        fill, op = depth_style(d)
        depth_css.append(".d%d{fill:%s;fill-opacity:%s}" % (d, fill, round(op, 2)))
    p.append("<style>%s</style>" % "".join(depth_css))

    p.append('<g class="g" text-anchor="middle">')
    for c in range(n_cols):
        x = c * col_w + col_w // 2
        dur = round(rnd.uniform(4.2, 11.5), 2)
        delay = round(-rnd.uniform(0, dur), 2)
        # 外层 g 只做定位，内层 g 承担 CSS 动画（CSS transform 会覆盖属性 transform）
        p.append('<g transform="translate(%d,0)">' % x)
        p.append(
            '<g class="col" style="animation-duration:%ss;animation-delay:%ss">'
            % (dur, delay)
        )
        for r in range(n_rows):
            y = r * row_h
            depth = n_rows - 1 - r          # 0 = 最下方，即下落的“头”
            cls = "d%d" % depth
            roll = rnd.random()
            if depth > 2 and roll < 0.12:
                cls += " fk"
            elif depth <= 2 and roll < 0.35:
                cls += " fk2"
            p.append(
                '<text y="%d" class="%s">%s</text>' % (y, cls, rnd.choice(GLYPHS))
            )
        p.append("</g></g>")
    p.append("</g>")

    # ---------------- 边缘淡出 ----------------
    p.append('<rect width="%d" height="%d" fill="url(#edge)"/>' % (width, height))

    # ---------------- 标题区 ----------------
    cy = height // 2
    p.append(
        '<ellipse cx="%d" cy="%d" rx="%d" ry="%d" fill="url(#vig)"/>'
        % (width // 2, cy, int(width * 0.44), int(height * 0.46))
    )
    if title:
        p.append('<g class="g ttl" filter="url(#glow)">')
        p.append(
            '<text x="%d" y="%d" text-anchor="middle" font-size="%d" '
            'font-weight="bold" letter-spacing="4" fill="#00FF41" '
            'fill-opacity="0.10" stroke="#00FF41" stroke-width="1.6">%s</text>'
            % (width // 2, cy, title_size, title)
        )
        p.append("</g>")
        half = int(len(title) * title_size * 0.31)
        p.append(
            '<rect class="cur" x="%d" y="%d" width="15" height="%d" '
            'fill="#00FF41" fill-opacity="0.85"/>'
            % (width // 2 + half + 10, cy - int(title_size * 0.72), int(title_size * 0.78))
        )
        sub_y, sub_size, sub_sp = cy + 42, 14, 4.5
    else:
        sub_y, sub_size, sub_sp = cy + 6, 20, 8

    # 副标题背后的暗条：保证长副标题不被数字雨糊掉
    band_w = int(len(subtitle) * (sub_size * 0.62 + sub_sp)) + 60
    band_w = min(band_w, width - 40)
    p.append(
        '<rect x="%d" y="%d" width="%d" height="%d" fill="url(#band)"/>'
        % (width // 2 - band_w // 2, sub_y - sub_size - 4, band_w, sub_size + 16)
    )
    p.append(
        '<text class="g" x="%d" y="%d" text-anchor="middle" font-size="%d" '
        'letter-spacing="%s" fill="#00FF41" fill-opacity="0.9">%s</text>'
        % (width // 2, sub_y, sub_size, sub_sp, subtitle)
    )
    p.append(
        '<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="#008F11" '
        'stroke-opacity="0.5" stroke-width="1"/>'
        % (width // 2 - 300, sub_y + 16, width // 2 + 300, sub_y + 16)
    )

    # ---------------- CRT 效果 ----------------
    p.append(
        '<rect class="scan" x="0" y="0" width="%d" height="3" fill="#00FF41" '
        'fill-opacity="0.16"/>' % width
    )
    p.append('<g fill="#000000" fill-opacity="0.13">')
    for y in range(0, height, 4):
        p.append('<rect x="0" y="%d" width="%d" height="1.4"/>' % (y, width))
    p.append("</g>")

    # ---------------- 边框 ----------------
    p.append(
        '<rect x="0.5" y="0.5" width="%d" height="%d" fill="none" '
        'stroke="#008F11" stroke-opacity="0.55" stroke-width="1"/>'
        % (width - 1, height - 1)
    )

    p.append("</svg>")
    svg = "".join(p)
    if out:
        with open(out, "w", encoding="utf-8") as f:
            f.write(svg)
    return svg


BASE = "assets"
os.makedirs(BASE, exist_ok=True)

jobs = [
    ("matrix-banner.svg",
     build(1200, 260, "Joseph",
           "MACHINE VISION RESEARCHER  ·  EMBEDDED SOFTWARE ENGINEER",
           seed=47, title_size=80, out=BASE + "/matrix-banner.svg")),
    ("matrix-footer.svg",
     build(1200, 150, "", "FOLLOW  THE  WHITE  RABBIT",
           seed=1999, n_rows=14, out=BASE + "/matrix-footer.svg")),
]
for name, svg in jobs:
    print("%-20s %8d bytes" % (name, len(svg)))
