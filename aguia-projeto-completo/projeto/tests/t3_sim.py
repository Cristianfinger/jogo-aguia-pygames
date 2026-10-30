"""Simulação rápida (sem desenhar) dos 20 níveis com um bot, dentro do navegador."""
import json
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from srv import serve
from playwright.sync_api import sync_playwright
BOT = r"""
(() => {
  const G = Aguia.Game;
  function run(H, seed) {
    let s = seed; Math.random = () => (s = s * 16807 % 2147483647) / 2147483647;
    const w = new G.World({}, {H});
    w.hp = 5; w.inv = 1.8;
    const stats = {hits:0, deaths:0, nan:false, maxEnts:0, perLevel:{}, minGap:999, score:0, frames:0};
    let lastHp = w.hp, lvl = 1;
    const hit = {};
    w.emit = (ev) => { if (ev === 'hurt') { stats.hits++; hit[w.level] = (hit[w.level]||0)+1; } };
    const ctl = () => {
      let best = 1e9, bx = w.px;
      for (let x = 50; x <= 400; x += 25) {
        let c = 0;
        for (const e of w.ents) {
          const dy = e.y - w.py;
          if (e.k==='mount'||e.k==='storm'||e.k==='hawk'||e.k==='meteor') {
            if (e.y > -60 && e.y < w.py + 30) { const near = Math.max(0, 1 - Math.abs(dy)/430); c += Math.max(0, (e.r+55) - Math.abs(e.x-x)) * (1 + 3*near); }
            if (e.k==='storm' && e.st===1) { const d = Math.hypot(e.tx-x, e.ty-w.py); if (d < 90) c += (90-d)*6; }
          } else if ((e.k==='gem'||e.k==='rabbit') && e.y > w.py-380 && e.y < w.py+10) c -= Math.max(0, 55-Math.abs(e.x-x)) * .8;
        }
        c += Math.abs(x - w.px) * .15;
        if (c < best) { best = c; bx = x; }
      }
      return bx;
    };
    const total = 20 * 30 * 60 + 60;
    for (let f = 0; f < total && w.over !== 'win'; f++) {
      stats.frames = f;
      w.update(1/60, ctl(), 640);
      if (!isFinite(w.px) || !isFinite(w.py) || !isFinite(w.vx) || !isFinite(w.score)) { stats.nan = true; break; }
      stats.maxEnts = Math.max(stats.maxEnts, w.ents.length);
      if (w.over === 'dead') { stats.deaths++; w.over = null; w.hp = 5; w.inv = 1.8; }
      if (w.level !== lvl) { lvl = w.level; }
    }
    stats.score = w.score; stats.level = w.level; stats.over = w.over; stats.hitsPerLevel = hit;
    return stats;
  }
  return {H800: run(800, 7), H1000: run(1000, 11)};
})()
"""
_srv = serve(); URL = _srv.__enter__()
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(); errs=[]
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.goto(URL); pg.wait_for_function("window.Aguia && Aguia.Game")
    r = pg.evaluate(BOT)
    for k, v in r.items(): print(k, json.dumps(v))
    print("erros de página:", errs); b.close()

_srv.__exit__(None, None, None)
