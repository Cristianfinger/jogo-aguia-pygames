"""Teste de fumaça sem janela: simula 20 níveis com um bot e salva capturas."""
import os, random, sys
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
import pygame
sys.path.insert(0, os.getcwd())
pygame.init()
pygame.display.set_mode((450, 800))
import game
A = game.load_assets()
random.seed(3)
w = game.World(A, 1)
shots = {1: 6, 5: 12, 9: 12, 13: 12, 17: 12, 20: 12}
f = hits = 0
canvas = pygame.Surface((450, 800))
died = 0
while not w.over and f < 60 * 30 * 21:
    f += 1
    # bot: vai para a coluna mais livre à frente
    best, bx = 1e9, w.px
    for x in range(50, 400, 25):
        c = 0
        for e in w.ents:
            if e.k in ("mount", "storm", "hawk", "meteor") and -50 < e.y < w.py + 20:
                c += max(0, 150 - abs(e.x - x)) * (1 + max(0, 1 - abs(e.y - w.py) / 450))
            elif e.k in ("gem", "rabbit") and w.py - 400 < e.y < w.py:
                c -= max(0, 60 - abs(e.x - x))
        c += abs(x - w.px) * .2
        if c < best: best, bx = c, x
    hp0 = w.hp
    w.update(1 / 60, bx, 650)
    if w.hp < hp0: hits += 1
    if f % 60 == 0 and w.level in shots and shots[w.level] > 0 and w.lt > 8:
        w.draw(canvas); pygame.image.save(canvas, f"/home/claude/shot_L{w.level}.png"); shots[w.level] -= 99
    if w.over == "dead":
        died += 1; w.hp = 5; w.over = None   # modo teste: revive para percorrer todos os níveis
print("frames", f, "nivel", w.level, "over", w.over, "score", w.score, "hits", hits, "mortes", died)
