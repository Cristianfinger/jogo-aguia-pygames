"""Gera as saídas do site a partir de web/:

  dist/            pasta pronta para qualquer hospedagem estática (copia web/ como está)
  dist-artifact/   variante para publicar como página no Claude (JS e CSS embutidos, assets em arquivos)

Uso: python3 tools/build_web.py
"""
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WEB = ROOT / "web"
DIST = ROOT / "dist"
ART = ROOT / "dist-artifact"

for d in (DIST, ART):
    if d.exists():
        shutil.rmtree(d)

# 1) site estático
shutil.copytree(WEB, DIST)

# 2) variante do artifact: um único HTML (sem doctype/html/head/body, que a plataforma adiciona)
html = (WEB / "index.html").read_text(encoding="utf-8")
css = (WEB / "css" / "style.css").read_text(encoding="utf-8")
import base64
css = css.replace("url(\"../assets/", "url(\"assets/")
def font_uri(m):
    data = (WEB / "fonts" / m.group(1)).read_bytes()
    return 'url("data:font/woff2;base64,' + base64.b64encode(data).decode() + '")'
css = re.sub(r'url\("\.\./fonts/([^"]+)"\)', font_uri, css)
# o publicador já reserva as áreas seguras do aparelho; zera as nossas para não somar duas vezes
css += "\n:root { --sat: 0px; --sab: 0px; --sal: 0px; --sar: 0px; }\n"

def inline_js(match):
    src = match.group(1)
    code = (WEB / src).read_text(encoding="utf-8")
    assert "</script" not in code
    return "<script>\n" + code + "\n</script>"

body = re.search(r"<body>(.*?)</body>", html, re.S).group(1)
body = re.sub(r'<script src="([^"]+)"></script>', inline_js, body)
body = re.sub(r'<link rel="preload"[^>]*>\n?', '', body)

title = re.search(r"<title>(.*?)</title>", html, re.S).group(0)
page = (
    title + "\n"
    '<meta name="description" content="Voe por 20 céus vistos de cima: desvie de montanhas, raios e meteoros, colete joias e cace coelhos.">\n'
    + "<style>\n" + css + "\n</style>\n" + body.strip() + "\n"
)
ART.mkdir()
(ART / "index.html").write_text(page, encoding="utf-8")
shutil.copytree(WEB / "assets", ART / "assets")

size = sum(p.stat().st_size for p in DIST.rglob("*") if p.is_file())
print(f"dist: {size/1e6:.2f} MB | artifact html: {len(page)/1e3:.0f} KB")
