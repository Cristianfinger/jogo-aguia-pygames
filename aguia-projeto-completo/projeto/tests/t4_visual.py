import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from srv import serve
from playwright.sync_api import sync_playwright
STEP = """
([L, until]) => {
  const A = Aguia.app; A.startGame(null); const w = A.world; const G = Aguia.Game;
  w.level = L; w.c = G.cfg(L); w.hp = 5; w.inv = 9999; w.prev = null; w.fade = 1; w.lt = 3;
  for (const k in w.timers) w.timers[k] = 0.1;
  for (let f = 0; f < 60*40; f++) {
    w.update(1/60, 225 + Math.sin(f/45)*130, 640); w.inv = 9999; w.lt = Math.min(w.lt, 20);
    if (f > 60*6) {
      if (until === 'bolt' && w.bolts.length) break;
      if (until === 'target' && w.ents.some(e => e.k==='storm' && e.st===1) && w.ents.filter(e=>e.k==='mount').length) break;
      if (until === 'meteor' && w.ents.some(e => e.k==='meteor' && e.warn>0)) break;
      if (until === 'hawk' && w.ents.filter(e => e.k==='hawk').length>=1 && w.ents.some(e=>e.k==='rabbit')) break;
      if (until === 'none' && f > 60*8) break;
    }
  }
  return {level: w.level, ents: w.ents.map(e=>e.k).join(',')};
}
"""
with sync_playwright() as p, serve() as URL:
    b = p.chromium.launch()
    ctx = b.new_context(viewport={"width":390,"height":844}, device_scale_factor=2, is_mobile=True, has_touch=True); pg = ctx.new_page()
    errs=[]; pg.on("pageerror", lambda e: errs.append(str(e))); pg.on("console", lambda m: errs.append(m.text) if m.type=="error" else None)
    pg.goto(URL); pg.wait_for_function("Aguia.app.state==='menu'"); pg.wait_for_timeout(300)
    for name, L, until in [("L3_storm",3,"target"),("L5_forest",5,"none"),("L9_hawk",9,"hawk"),("L12_desert",12,"none"),("L13_meteor",13,"meteor"),("L16_tundra",16,"none"),("L20_volcano",20,"bolt")]:
        r = pg.evaluate(STEP, [L, until]); pg.wait_for_timeout(120)
        # congela o estado atual para a captura (pausa só desenha)
        pg.screenshot(path=f"/home/claude/v_{name}.png"); print(name, r)
    pg.evaluate("Aguia.app.toMenu()"); pg.wait_for_timeout(300)
    pg.tap("#btnHow"); pg.wait_for_timeout(700); pg.screenshot(path="/home/claude/v_how.png")
    ctx.close()
    ctx = b.new_context(viewport={"width":1280,"height":800}); pg = ctx.new_page(); pg.goto(URL); pg.wait_for_function("Aguia.app.state==='menu'")
    pg.click("#btnHow"); pg.wait_for_timeout(700); pg.screenshot(path="/home/claude/v_how_desktop.png", clip={"x":415,"y":0,"width":450,"height":800})
    b.close()
print("erros:", errs)
