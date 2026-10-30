"""Águia — Voo dos 20 Céus. Pygame (pygame-ce) empacotado com pygbag para rodar no navegador."""
import asyncio
import math

import pygame

import storage
from game import H, LAST, PAUSE_RECT, W, World, load_assets, text

SAVE_EVERY = 4.0


async def main():
    pygame.init()
    scr = pygame.display.set_mode((W, H), pygame.SCALED | pygame.RESIZABLE)
    pygame.display.set_caption("Águia — Voo dos 20 Céus")
    canvas = pygame.Surface((W, H))
    A = load_assets()
    clock = pygame.time.Clock()

    bg = World(A, 1)
    bg.banner = 0
    state, world, result, save_t = "menu", None, {}, 0.0
    pos, down, click, keys = (W // 2, H // 2), False, None, set()

    def btn(label, y, primary=False, w=310, h=62):
        r = pygame.Rect(0, 0, w, h)
        r.center = (W // 2, y)
        held = down and r.collidepoint(pos)
        pygame.draw.rect(canvas, (10, 20, 40), r.move(0, 5), border_radius=20)
        col = (255, 196, 60) if primary else (44, 74, 118)
        if held:
            col = tuple(int(c * .85) for c in col)
        pygame.draw.rect(canvas, col, r.move(0, 3 if held else 0), border_radius=20)
        pygame.draw.rect(canvas, (255, 255, 255), r.move(0, 3 if held else 0), 2, border_radius=20)
        text(canvas, label, 34, r.move(0, 3 if held else 0).center, (30, 30, 40) if primary else (255, 255, 255),
             out=(255, 230, 150) if primary else (20, 32, 56))
        return click is not None and r.collidepoint(click)

    def panel(h, y):
        p = pygame.Surface((W - 50, h), pygame.SRCALPHA)
        pygame.draw.rect(p, (12, 24, 48, 215), p.get_rect(), border_radius=24)
        pygame.draw.rect(p, (255, 255, 255, 120), p.get_rect(), 2, border_radius=24)
        canvas.blit(p, (25, y))

    def start(save=None):
        nonlocal world, state, save_t
        if save:
            world = World(A, int(save["level"]), float(save["t"]), int(save["score"]), int(save["hp"]),
                          float(save["px"]), float(save["py"]))
        else:
            storage.clear()
            world = World(A, 1)
        state, save_t = "play", 0.0

    def finish():
        nonlocal state, result
        n = storage.ask_name()
        r = 0
        if world.score > 0:
            r = storage.add_local(n, world.score, world.level)
            storage.submit(n, world.score, world.level)
        storage.clear()
        storage.refresh()
        result = dict(win=world.over == "win", score=world.score, level=world.level, rank=r, name=n)
        state = "over"

    storage.refresh()
    while True:
        dt = min(clock.tick(60) / 1000, 1 / 20)
        click = None
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                return
            elif ev.type == pygame.MOUSEMOTION:
                pos = ev.pos
            elif ev.type == pygame.MOUSEBUTTONDOWN:
                pos, down = ev.pos, True
                if state == "play" and PAUSE_RECT.collidepoint(ev.pos):
                    state, down = "pause", False
            elif ev.type == pygame.MOUSEBUTTONUP:
                pos, down, click = ev.pos, False, ev.pos
            elif ev.type == pygame.KEYDOWN:
                keys.add(ev.key)
                if ev.key in (pygame.K_ESCAPE, pygame.K_p):
                    state = "pause" if state == "play" else "play" if state == "pause" else state
            elif ev.type == pygame.KEYUP:
                keys.discard(ev.key)
            elif ev.type in (pygame.WINDOWFOCUSLOST, pygame.WINDOWHIDDEN) and state == "play":
                state, down = "pause", False

        # ---------------- cenas ----------------
        if state in ("menu", "rank"):
            bg.ground += 70 * dt
            bg.anim += dt
            bg.draw_ground(canvas)
            canvas.blit(A["haze"], (0, 0))
            e = A["eagle"][int(bg.anim * 6) % 2]
            canvas.blit(e, e.get_rect(center=(W // 2 + int(math.sin(bg.anim) * 30), 560)))

        if state == "menu":
            text(canvas, "ÁGUIA", 120, (W // 2, 130))
            text(canvas, "Voo dos 20 Céus", 38, (W // 2, 200), (255, 220, 120))
            sv = storage.load()
            y = 300
            if sv:
                if btn(f"Continuar · Nível {sv['level']}", y, True):
                    start(sv)
                y += 80
            if btn("Novo jogo", y, not sv):
                start()
            if btn("Ranking", y + 80):
                storage.refresh()
                state = "rank"
            n = storage.name()
            if btn(f"Jogador: {n}" if n else "Definir nome", y + 160, w=310, h=46):
                storage.ask_name(force=True)
            text(canvas, "Arraste para voar · colete joias · cace coelhos", 22, (W // 2, H - 40))

        elif state == "play":
            tx, ty = world.px, world.py
            if down:
                tx, ty = pos[0], pos[1] - 70
            kx = (pygame.K_RIGHT in keys or pygame.K_d in keys) - (pygame.K_LEFT in keys or pygame.K_a in keys)
            ky = (pygame.K_DOWN in keys or pygame.K_s in keys) - (pygame.K_UP in keys or pygame.K_w in keys)
            if kx or ky:
                tx, ty = world.px + kx * 220, world.py + ky * 220
            world.update(dt, tx, ty)
            save_t += dt
            if save_t > SAVE_EVERY and not world.over:
                storage.save(world.snapshot())
                save_t = 0.0
            world.draw(canvas)
            if world.over:
                finish()

        elif state == "pause":
            world.draw(canvas)
            ov = pygame.Surface((W, H), pygame.SRCALPHA)
            ov.fill((8, 16, 32, 170))
            canvas.blit(ov, (0, 0))
            text(canvas, "PAUSADO", 70, (W // 2, 250))
            if btn("Continuar", 360, True):
                state = "play"
            if btn("Menu (salva o progresso)", 440):
                storage.save(world.snapshot())
                state = "menu"

        elif state == "over":
            world.draw(canvas)
            ov = pygame.Surface((W, H), pygame.SRCALPHA)
            ov.fill((8, 16, 32, 190))
            canvas.blit(ov, (0, 0))
            panel(330, 150)
            text(canvas, "VITÓRIA!" if result["win"] else "FIM DE JOGO", 66, (W // 2, 205),
                 (255, 220, 90) if result["win"] else (255, 255, 255))
            text(canvas, f"{result['score']:,}".replace(",", ".") + " pontos", 44, (W // 2, 270))
            text(canvas, f"Nível {result['level']} de {LAST}", 30, (W // 2, 315))
            if result["rank"]:
                text(canvas, f"Você é o nº {result['rank']} neste aparelho!", 26, (W // 2, 360), (140, 230, 255))
            text(canvas, result["name"], 26, (W // 2, 400), (255, 220, 120))
            if btn("Jogar de novo", 520, True):
                start()
            if btn("Ranking", 600):
                state = "rank"
            if btn("Menu", 680):
                state = "menu"

        elif state == "rank":
            panel(560, 90)
            online = storage.online_top()
            rows = online or storage.local_top()
            text(canvas, "RANKING", 56, (W // 2, 130))
            text(canvas, "Online" if online else "Neste aparelho", 24, (W // 2, 165), (140, 230, 255))
            if not rows:
                text(canvas, "Nenhuma pontuação ainda", 28, (W // 2, 330))
            for i, r in enumerate(rows[:10]):
                y = 205 + i * 41
                col = (255, 220, 90) if i == 0 else (255, 255, 255)
                text(canvas, f"{i + 1}.", 28, (62, y), col, "midleft")
                text(canvas, str(r.get("name", "?"))[:12], 28, (100, y), col, "midleft")
                text(canvas, f"{int(r.get('score', 0)):,}".replace(",", "."), 28, (W - 60, y), col, "midright")
            if btn("Voltar", 705):
                state = "menu"

        # ---------------- saída ----------------
        sx = sy = 0
        if world and state == "play" and world.shake > 0:
            sx, sy = (int(math.sin(world.anim * 90) * 6), int(math.cos(world.anim * 70) * 6))
        scr.fill((8, 16, 32))
        scr.blit(canvas, (sx, sy))
        pygame.display.flip()
        await asyncio.sleep(0)


asyncio.run(main())
