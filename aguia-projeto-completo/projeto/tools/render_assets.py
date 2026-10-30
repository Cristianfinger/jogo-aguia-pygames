"""Renderiza a arte (SVG com filtros) para PNG usando o Chromium headless.
Uso: python tools/render_assets.py tools/arte.html
"""
import re
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
SRC = Path(sys.argv[1] if len(sys.argv) > 1 else ROOT / "tools" / "arte.html")
OUT = ROOT / "assets"
OUT.mkdir(exist_ok=True)

html = SRC.read_text(encoding="utf-8")
css = re.search(r"<style>(.*?)</style>", html, re.S).group(1)
defs = re.search(r'<svg width="0".*?</svg>', html, re.S).group(0)
script = re.search(r"<script>.*?</script>", html, re.S).group(0)


def use(href, w, h, cls="", style=""):
    return f'<use href="#{href}" class="{cls}" width="{w}" height="{h}" style="{style}"/>'


SPRITES = [
    ("eagle1", 200, 164, use("bird", 200, 164, "eagle")),
    ("eagle2", 200, 164, use("bird2", 200, 164, "eagle")),
    ("hawk1", 200, 164, use("bird", 200, 164, "hawk")),
    ("hawk2", 200, 164, use("bird2", 200, 164, "hawk")),
    ("mount", 200, 200, use("mt", 200, 200)),
    ("storm", 200, 150, use("cloud", 200, 150, "storm")),
    ("cloud", 200, 150, use("cloud", 200, 150, "white")),
    ("gem0", 40, 40, use("gem", 40, 40, style="color:#37d8ff")),
    ("gem1", 40, 40, use("gem", 40, 40, style="color:#ff5fa2")),
    ("gem2", 40, 40, use("gem", 40, 40, style="color:#5ee08a")),
    ("rabbit", 60, 98, use("rabbit", 60, 98)),
    ("meteor", 120, 200, use("meteor", 120, 200)),
    ("heart", 32, 30, use("heart", 32, 30)),
]


def page(w, h, inner, extra_defs=""):
    return (
        f"<!DOCTYPE html><html><head><style>{css}</style>"
        "<style>html,body{background:transparent!important;margin:0;padding:0}</style></head><body>"
        f"{defs}{script}{extra_defs}"
        f'<svg id="t" width="{w}" height="{h}" viewBox="0 0 {w} {h}" style="display:block">{inner}</svg>'
        "</body></html>"
    )


def grab(pg, name, w, h, inner, extra_defs=""):
    pg.set_content(page(w, h, inner, extra_defs))
    pg.wait_for_timeout(200)
    pg.locator("svg#t").screenshot(path=str(OUT / f"{name}.png"), omit_background=True)
    print("ok", name)


def filt(fid, new_id, repl=None):
    f = re.search(rf'<filter id="{fid}".*?</filter>', html, re.S).group(0)
    f = f.replace(f'id="{fid}"', f'id="{new_id}"', 1).replace("<feTurbulence ", '<feTurbulence stitchTiles="stitch" ')
    for a, b in (repl or []):
        f = f.replace(a, b)
    return f


TW, TH = 450, 512
RIVER = "M300 0C380 128 220 384 300 512"
river = "".join(
    f'<g transform="translate(0 {dy})">'
    f'<path d="{RIVER}" fill="none" stroke="#c9b98a" stroke-width="58"/>'
    f'<path d="{RIVER}" fill="none" stroke="#2f7fa8" stroke-width="46"/>'
    f'<path d="{RIVER}" fill="none" stroke="#6cc0e0" stroke-width="26" opacity=".5"/></g>'
    for dy in (-512, 0, 512)
)
fields = (
    '<g filter="url(#ft)" stroke="#3a4a20" stroke-opacity=".5" stroke-width=".8">'
    '<path d="M30 60 130 40 150 110 40 135Z" fill="url(#pf1)"/>'
    '<path d="M40 300 140 280 160 350 50 375Z" fill="url(#pf3)"/>'
    '<path d="M330 150 420 140 435 210 340 225Z" fill="url(#pf2)"/>'
    '<path d="M60 430 150 415 165 480 70 495Z" fill="url(#pf2)"/></g>'
)
R = f'width="{TW}" height="{TH}"'
TILES = {
    "campos": (
        f'<rect {R} fill="#3f7d3a"/><rect {R} filter="url(#t_ter)" opacity=".6"/>'
        f'<rect {R} filter="url(#t_ter2)" opacity=".55"/>{fields}'
        f'<rect {R} filter="url(#t_fo)" opacity=".95"/>{river}'
    ),
    "floresta": f'<rect {R} fill="#1c3f26"/><rect {R} filter="url(#t_ter)" opacity=".4"/><rect {R} filter="url(#t_fo2)"/>',
    "deserto": f'<rect {R} fill="#d9b778"/><rect {R} filter="url(#t_dn)"/>',
    "tundra": f'<rect {R} fill="#9db8d4"/><rect {R} filter="url(#t_sn)" opacity=".92"/>',
    "vulcao": f'<rect {R} fill="#2a1612"/><rect {R} filter="url(#t_lv)"/>',
}
TILE_DEFS = (
    "<svg width='0' height='0' style='position:absolute'><defs>"
    + filt("ter", "t_ter") + filt("ter2", "t_ter2") + filt("fo", "t_fo")
    + filt("fo", "t_fo2", [("4.5 0 0 0 -2.1", "4.5 0 0 0 -1.3")])
    + filt("dn", "t_dn") + filt("sn", "t_sn") + filt("lv", "t_lv")
    + "</defs></svg>"
)

with sync_playwright() as p:
    b = p.chromium.launch()
    ctx = b.new_context(device_scale_factor=2)
    pg = ctx.new_page()
    for name, w, h, inner in SPRITES:
        grab(pg, name, w, h, inner)
    ctx.close()
    ctx = b.new_context(device_scale_factor=1)
    pg = ctx.new_page()
    grab(pg, "haze", 450, 800,
         '<rect width="450" height="800" fill="url(#gHz)"/><rect width="450" height="800" fill="url(#gSun)"/>')
    for name, inner in TILES.items():
        grab(pg, f"tile_{name}", TW, TH, inner, TILE_DEFS)
    b.close()
