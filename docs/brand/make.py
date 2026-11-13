"""Headcount's README banner and social preview, with every word as outlines."""
import re
import sys
from pathlib import Path

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont

REPO = Path(sys.argv[1])
FONTS = REPO / "crates/app/resources/fonts"
OUT = REPO / "docs/brand"
OUT.mkdir(parents=True, exist_ok=True)

BG, RAISED, LINE = "#0f1013", "#1e2026", "#2a2d35"
TEXT, TEXT2, TEXT3, ACCENT = "#eceef2", "#a3a7b2", "#7d818c", "#ff3d2e"

_fonts = {}


def font(path, wght):
    key = (path, wght)
    if key not in _fonts:
        f = TTFont(path)
        if "fvar" in f:
            f = instantiateVariableFont(f, {"wght": wght})
        _fonts[key] = f
    return _fonts[key]


def text(s, x, y, size, fill, wght=400, path=FONTS / "InterVariable.ttf", tracking=0.0, anchor="start"):
    """`s` as one <path>, its baseline at y."""
    f = font(path, wght)
    scale = size / f["head"].unitsPerEm
    cmap, glyphs, hmtx = f.getBestCmap(), f.getGlyphSet(), f["hmtx"]
    names = [cmap[ord(c)] for c in s]
    width = sum(hmtx[n][0] for n in names) * scale + tracking * size * (len(s) - 1)
    if anchor == "middle":
        x -= width / 2
    pen = SVGPathPen(glyphs)
    cx = x
    for n in names:
        glyphs[n].draw(TransformPen(pen, (scale, 0, 0, -scale, cx, y)))
        cx += hmtx[n][0] * scale + tracking * size
    return f'<path fill="{fill}" d="{pen.getCommands()}"/>', width


def icon(x, y, size):
    src = (REPO / "packaging/icons/headcount.svg").read_text()
    inner = re.search(r"<svg[^>]*>(.*)</svg>", src, re.S).group(1)
    return f'<g transform="translate({x} {y}) scale({size / 1024})">{inner}</g>'


def pill(label, x, y, h=44, size=19):
    p, w = text(label, 0, 0, size, TEXT2, 500)
    pad = 20
    return (
        f'<g transform="translate({x} {y})">'
        f'<rect width="{w + 2 * pad:.1f}" height="{h}" rx="{h / 2}" fill="{RAISED}" stroke="{LINE}"/>'
        f'<g transform="translate({pad} {h / 2 + size * 0.36:.1f})">{p}</g></g>'
    ), w + 2 * pad


def pills(labels, x, y, gap=12, anchor="start"):
    parts, widths = zip(*(pill(l, 0, 0) for l in labels))
    total = sum(widths) + gap * (len(labels) - 1)
    cx = x - total / 2 if anchor == "middle" else x
    out = []
    for part, w in zip(parts, widths):
        out.append(f'<g transform="translate({cx:.1f} {y})">{part}</g>')
        cx += w + gap
    return "".join(out)


def svg(w, h, body, rx=0):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">'
        f'<rect width="{w}" height="{h}" rx="{rx}" fill="{BG}"/>{body}</svg>\n'
    )


TAGLINE = "Many Roblox accounts on Linux, launched in one click."
FEATURES = ["Macros while you work", "One-click multi-launch", "Sessions in your keyring"]

# README banner: icon left, name and line beside it.
word, _ = text("Headcount", 268, 168, 112, TEXT, 700, tracking=-0.025)
tag, _ = text(TAGLINE, 272, 222, 30, TEXT2, 400)
banner = svg(
    1280, 340,
    icon(64, 70, 172) + word + tag + pills(FEATURES, 272, 256),
    rx=28,
)
(OUT / "banner.svg").write_text(banner)

# Social preview, 1280x640: centred.
word, _ = text("Headcount", 640, 382, 136, TEXT, 700, tracking=-0.025, anchor="middle")
tag, _ = text(TAGLINE, 640, 444, 34, TEXT2, 400, anchor="middle")
url, _ = text("github.com/DamnShabu/headcount", 640, 590, 22, TEXT3, 500,
              path=FONTS / "JetBrainsMono.ttf", anchor="middle")
bar = f'<rect x="0" y="0" width="1280" height="8" fill="{ACCENT}"/>'
social = svg(1280, 640, bar + icon(560, 92, 160) + word + tag + pills(FEATURES, 640, 488, anchor="middle") + url)
(OUT / "social-preview.svg").write_text(social)
print("wrote", OUT)
