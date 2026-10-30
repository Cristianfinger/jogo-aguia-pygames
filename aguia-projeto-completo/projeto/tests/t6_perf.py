"""Mede o ritmo real de quadros (rAF) em jogo, nível 20, celular em dpr 3 sem GPU (pior caso)."""
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from srv import serve
from playwright.sync_api import sync_playwright
with sync_playwright() as p, serve() as URL:
    b = p.chromium.launch(); ctx = b.new_context(viewport={"width":390,"height":844}, device_scale_factor=3, is_mobile=True, has_touch=True); pg = ctx.new_page()
    errs = []; pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.goto(URL); pg.wait_for_function("Aguia.app.state==='menu'"); pg.tap("#btnNew"); pg.wait_for_function("Aguia.app.state==='play'")
    pg.evaluate("""() => { const w = Aguia.app.world; w.level = 20; w.c = Aguia.Game.cfg(20); w.hp = 5; w.inv = 99999; }""")
    out = []
    for i in range(4):
        r = pg.evaluate("""() => new Promise(res => { let n = 0, t0 = performance.now(), prev = t0, worst = 0;
          function f(t){ n++; worst = Math.max(worst, t - prev); prev = t; if (n < 120) requestAnimationFrame(f); else res({fps: +(n*1000/(t - t0)).toFixed(1), worst: +worst.toFixed(0), canvas: document.getElementById('cv').width + 'x' + document.getElementById('cv').height}); }
          requestAnimationFrame(f); })""")
        out.append(r)
    print(json.dumps(out)); print("erros:", errs); b.close()
