"""Percorre menu -> jogo -> pausa -> fim -> ranking injetando eventos, sem janela."""
import asyncio, os, runpy, sys
os.environ["SDL_VIDEODRIVER"] = "dummy"; os.environ["SDL_AUDIODRIVER"] = "dummy"
import pygame
sys.path.insert(0, os.getcwd())
for f in (".aguia_save.json", ".aguia_rank.json", ".aguia_name.json"):
    if os.path.exists(f): os.remove(f)
frame = [0]
real_sleep = asyncio.sleep
def ev(t, **k): pygame.event.post(pygame.event.Event(t, **k))
def click(x, y):
    ev(pygame.MOUSEBUTTONDOWN, pos=(x, y), button=1); ev(pygame.MOUSEBUTTONUP, pos=(x, y), button=1)
async def fake_sleep(d):
    frame[0] += 1; n = frame[0]; s = pygame.display.get_surface()
    if n == 5: pygame.image.save(s, "/home/claude/f_menu.png"); click(225, 300)          # Novo jogo
    if n == 40: ev(pygame.MOUSEBUTTONDOWN, pos=(120, 700), button=1)                   # arrastar
    if n == 200: pygame.image.save(s, "/home/claude/f_play.png"); click(225, 28)       # pausa
    if n == 210: pygame.image.save(s, "/home/claude/f_pause.png"); click(225, 360)     # continuar
    if n == 262: pygame.image.save(s, "/home/claude/f_over.png"); click(225, 600)          # Ranking
    if n == 270: pygame.image.save(s, "/home/claude/f_rank.png"); click(225, 705)          # Voltar
    if n == 280: raise SystemExit
    await real_sleep(0)
import game
_orig = game.World.update
def _upd(self, dt, tx, ty):
    _orig(self, dt, tx, ty)
    if frame[0] == 255: self.over = "dead"
game.World.update = _upd
asyncio.sleep = fake_sleep
try:
    runpy.run_path("main.py", run_name="__main__")
except SystemExit:
    pass
print("fluxo ok, frames:", frame[0], "save:", os.path.exists(".aguia_save.json"))
