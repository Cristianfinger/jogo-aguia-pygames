import sys
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from srv import serve
from playwright.sync_api import sync_playwright
VIEWS = {
  "desktop": dict(viewport={"width":1280,"height":800}),
  "iphone":  dict(viewport={"width":390,"height":844}, device_scale_factor=3, is_mobile=True, has_touch=True),
  "small":   dict(viewport={"width":360,"height":640}, device_scale_factor=2, is_mobile=True, has_touch=True),
}
_srv = serve(); URL = _srv.__enter__()
with sync_playwright() as p:
    b = p.chromium.launch()
    for name, kw in VIEWS.items():
        ctx = b.new_context(**kw); pg = ctx.new_page(); errs = []
        pg.on("console", lambda m: errs.append("console."+m.type+": "+m.text) if m.type in ("error","warning") else None)
        pg.on("pageerror", lambda e: errs.append("pageerror: "+str(e)))
        pg.on("requestfailed", lambda r: errs.append("requestfailed: "+r.url))
        pg.on("response", lambda r: errs.append(f"http {r.status}: {r.url}") if r.status >= 400 else None)
        pg.goto(URL); pg.wait_for_function("window.Aguia && window.Aguia.app && window.Aguia.app.state==='menu'", timeout=15000)
        pg.wait_for_timeout(600)
        info = pg.evaluate("({H:Aguia.app.H, scale:Aguia.app.scale, css:Aguia.app.cssScale, st:getComputedStyle(document.getElementById('stage')).width+'x'+getComputedStyle(document.getElementById('stage')).height, hs: document.documentElement.scrollWidth+'x'+document.documentElement.scrollHeight})")
        print(name, info)
        pg.screenshot(path=f"/home/claude/shot_menu_{name}.png")
        for e in errs: print("   !", e)
        ctx.close()
    b.close()

_srv.__exit__(None, None, None)
