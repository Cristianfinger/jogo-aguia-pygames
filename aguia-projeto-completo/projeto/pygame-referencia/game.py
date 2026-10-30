"""Núcleo do jogo: níveis, entidades, colisões e desenho (sem dependência de rede)."""
import math
import random

import pygame

W, H = 450, 800
MAX_HP, LEVEL_TIME, LAST = 5, 30, 20
BIOMES = ["campos", "floresta", "deserto", "tundra", "vulcao"]
NEWS = {
    1: "Colete joias e cace coelhos", 3: "Nuvens de tempestade!", 4: "Gaviões à vista!",
    6: "Raios mais rápidos", 9: "Gaviões em bando", 13: "Chuva de meteoros!", 17: "Rajadas de meteoros!",
}
PAUSE_RECT = pygame.Rect(197, 6, 56, 44)


def biome(level):
    return BIOMES[min((level - 1) // 4, 4)]


def clamp(v, a, b):
    return a if v < a else b if v > b else v


def cfg(l):
    """Dificuldade: intervalos de aparição (s) e velocidades, crescentes por nível."""
    return dict(
        speed=min(140 + 14 * l, 430),
        mount=max(2.2 - .07 * l, .95),
        storm=None if l < 3 else max(6 - .22 * l, 2.2),
        hawk=None if l < 4 else max(6.5 - .25 * l, 1.5),
        meteor=None if l < 13 else max(3.2 - .13 * (l - 12), 1.1),
        ring=max(1.25 - .03 * l, .75),
        gem=1.5, rabbit=max(10 - .2 * l, 6),
    )


# ---------- texto ----------
_fonts, _txt = {}, {}


def font(n):
    if n not in _fonts:
        _fonts[n] = pygame.font.Font(None, n)
    return _fonts[n]


def text(surf, s, n, pos, col=(255, 255, 255), anchor="center", out=(20, 32, 56)):
    k = (s, n, col)
    if k not in _txt:
        if len(_txt) > 300:
            _txt.clear()
        _txt[k] = (font(n).render(s, True, col), font(n).render(s, True, out))
    base, edge = _txt[k]
    r = base.get_rect(**{anchor: pos})
    for dx, dy in ((-2, 0), (2, 0), (0, -2), (0, 2), (2, 2), (-2, 2)):
        surf.blit(edge, r.move(dx, dy))
    surf.blit(base, r)
    return r


# ---------- assets ----------
def _load(name, size=None):
    s = pygame.image.load(f"assets/{name}.png").convert_alpha()
    return pygame.transform.smoothscale(s, size) if size else s


def _shadow(s):
    m = pygame.mask.from_surface(s, 40).to_surface(setcolor=(0, 0, 0, 105), unsetcolor=(0, 0, 0, 0))
    w, h = m.get_size()
    small = pygame.transform.smoothscale(m, (max(2, w // 4), max(2, h // 4)))
    return pygame.transform.smoothscale(small, (w, h))


def load_assets():
    A = {"sh": {}, "rot": {}}
    A["eagle"] = [_load("eagle1", (108, 88)), _load("eagle2", (108, 88))]
    A["hawk"] = [pygame.transform.rotate(_load(f"hawk{i}", (92, 75)), 180) for i in (1, 2)]
    A["mount"] = {n: _load("mount", (n, n)) for n in (120, 150, 185)}
    A["storm"], A["cloud"] = _load("storm", (190, 143)), _load("cloud", (190, 143))
    A["gem"] = [_load(f"gem{i}", (30, 30)) for i in range(3)]
    A["rabbit"], A["meteor"] = _load("rabbit", (36, 59)), _load("meteor", (60, 100))
    A["gem_s"] = pygame.transform.smoothscale(A["gem"][0], (22, 22))
    A["heart"] = _load("heart", (26, 24))
    A["heart0"] = A["heart"].copy()
    A["heart0"].set_alpha(70)
    A["haze"] = _load("haze", (W, H))
    A["tile"] = {b: pygame.image.load(f"assets/tile_{b}.jpg").convert() for b in BIOMES}
    g = pygame.Surface((120, 120), pygame.SRCALPHA)
    for r in range(60, 0, -3):
        pygame.draw.circle(g, (200, 220, 255, int(70 * (1 - r / 60) + 8)), (60, 60), r)
    A["glow"] = g
    return A


def shadow(A, s):
    k = id(s)
    if k not in A["sh"]:
        A["sh"][k] = _shadow(s)
    return A["sh"][k]


def rot(A, s, ang, step=6):
    k = (id(s), round(ang / step))
    if k not in A["rot"]:
        if len(A["rot"]) > 400:
            A["rot"].clear()
        A["rot"][k] = pygame.transform.rotate(s, k[1] * step)
    return A["rot"][k]


class E:
    def __init__(s, k, x, y, r, vx=0.0, vy=0.0, **kw):
        s.k, s.x, s.y, s.r, s.vx, s.vy, s.t, s.dead = k, x, y, r, vx, vy, 0.0, False
        s.__dict__.update(kw)


class World:
    def __init__(s, A, level=1, t=0.0, score=0, hp=4, px=W / 2, py=650.0):
        s.A, s.level, s.lt, s.score, s.hp = A, level, t, score, hp
        s.px, s.py, s.vx, s.vy = px, py, 0.0, 0.0
        s.ents, s.texts, s.bolts = [], [], []
        s.ground, s.inv, s.shake, s.anim, s.over = 0.0, 1.8, 0.0, 0.0, None
        s.banner, s.prev, s.fade = 3.0, None, 1.0
        s.c = cfg(level)
        s.timers = {"mount": 1.2, "gem": 0.5, "storm": 3.0, "hawk": 4.0, "meteor": 2.0, "rabbit": 5.0}
        s.hclouds = [[random.uniform(0, W), random.uniform(-200, H), random.uniform(.9, 1.6)] for _ in range(4)]

    # ---------- estado ----------
    def snapshot(s):
        return dict(level=s.level, t=round(s.lt, 1), score=s.score, hp=s.hp, px=round(s.px), py=round(s.py))

    def hurt(s):
        if s.inv > 0:
            return
        s.hp -= 1
        s.inv, s.shake = 1.6, .35
        if s.hp <= 0:
            s.over = "dead"

    def pop(s, msg, x, y, col=(255, 255, 255)):
        s.texts.append([msg, x, y, 1.0, col])

    # ---------- spawn ----------
    def add_mount(s, x, sz):
        s.ents.append(E("mount", x, -sz, sz * .3, sz=sz))

    def spawn(s, k):
        c, L = s.c, s.level
        if k == "mount":
            x = random.uniform(50, W - 50)
            s.add_mount(x, random.choice((120, 150, 185)))
            if random.random() < min(.15 + .03 * L, .6):
                x2 = x + random.choice((-1, 1)) * random.uniform(215, 290)
                if 40 < x2 < W - 40:
                    s.add_mount(x2, random.choice((120, 150)))
        elif k == "gem":
            x, n = random.uniform(60, W - 60), random.randint(3, 5)
            kind = random.choices((0, 1, 2), (70, 22, 8))[0]
            for i in range(n):
                s.ents.append(E("gem", x + math.sin(i * .9) * 26, -30 - i * 38, 13, g=kind))
        elif k == "rabbit":
            s.ents.append(E("rabbit", random.uniform(50, W - 50), -40, 18, vx=random.choice((-1, 1)) * 25,
                            ang=random.uniform(0, 360)))
        elif k == "storm":
            s.ents.append(E("storm", random.uniform(90, W - 90), -90, 42, cd=random.uniform(1.2, 2.2), st=0))
        elif k == "hawk":
            for i in range(2 if L >= 9 and random.random() < .5 else 1):
                s.ents.append(E("hawk", random.uniform(50, W - 50), -50 - i * 70, 20, ph=random.random() * 3))
        elif k == "meteor":
            for _ in range(random.randint(2, 3) if L >= 17 else 1):
                x = random.uniform(30, W - 30)
                s.ents.append(E("meteor", x, -110, 15, vx=random.uniform(-150, 150), vy=330 + 12 * (L - 12),
                                warn=.9, wx=x))
        s.timers[k] = c[k] * random.uniform(.8, 1.25)

    def next_level(s):
        s.score += 200 * s.level
        if s.level >= LAST:
            s.score += 2000
            s.over = "win"
            return
        s.prev, s.fade = biome(s.level), 0.0
        s.level += 1
        s.lt, s.banner, s.c = 0.0, 3.0, cfg(s.level)
        s.pop(f"+{200 * (s.level - 1)}", W / 2, 300, (255, 220, 90))

    # ---------- atualização ----------
    def update(s, dt, tx, ty):
        s.anim += dt
        s.ground += s.c["speed"] * .55 * dt
        s.fade = min(1.0, s.fade + dt / 2)
        s.banner = max(0, s.banner - dt)
        s.inv, s.shake = max(0, s.inv - dt), max(0, s.shake - dt)
        sp = s.c["speed"]
        # águia
        ax, ay = (tx - s.px) * 9, (ty - s.py) * 9
        m = math.hypot(ax, ay)
        if m > 560:
            ax, ay = ax * 560 / m, ay * 560 / m
        k = min(1, dt * 14)
        s.vx += (ax - s.vx) * k
        s.vy += (ay - s.vy) * k
        s.px = clamp(s.px + s.vx * dt, 40, W - 40)
        s.py = clamp(s.py + s.vy * dt, 130, H - 70)
        # spawns
        for k_ in list(s.timers):
            if s.c.get(k_) is None:
                continue
            s.timers[k_] -= dt
            if s.timers[k_] <= 0:
                s.spawn(k_)
        # entidades
        for e in s.ents:
            e.t += dt
            if e.k in ("mount", "gem"):
                e.y += sp * dt
                if e.k == "gem":
                    e.x += math.sin(e.t * 3) * 10 * dt
            elif e.k == "rabbit":
                d = math.hypot(e.x - s.px, e.y - s.py)
                if d < 150:
                    away = math.atan2(e.y - s.py, e.x - s.px)
                    e.vx += math.cos(away) * 400 * dt
                    e.ang = -math.degrees(math.atan2(math.cos(away), -math.sin(away)))
                e.vx = clamp(e.vx * (1 - dt * .8), -170, 170)
                e.x = clamp(e.x + e.vx * dt, 20, W - 20)
                e.y += sp * dt
            elif e.k == "storm":
                e.y += sp * .85 * dt
                s.storm_ai(e, dt)
            elif e.k == "hawk":
                e.vx = clamp((s.px - e.x) * 1.4, -(70 + 4 * s.level), 70 + 4 * s.level)
                e.x += e.vx * dt
                e.y += (sp * .6 + 150 + 5 * s.level) * dt
            elif e.k == "meteor":
                if e.warn > 0:
                    e.warn -= dt
                    e.x = e.wx
                else:
                    e.x += e.vx * dt
                    e.y += e.vy * dt
            if e.y > H + 220 or e.x < -250 or e.x > W + 250:
                e.dead = True
        s.collide()
        s.ents = [e for e in s.ents if not e.dead]
        for b in s.bolts:
            b["t"] -= dt
        s.bolts = [b for b in s.bolts if b["t"] > 0]
        s.dt = dt
        for t in s.texts:
            t[2] -= 40 * dt
            t[3] -= dt
        s.texts = [t for t in s.texts if t[3] > 0]
        s.lt += dt
        if s.lt >= LEVEL_TIME and not s.over:
            s.next_level()

    def storm_ai(s, e, dt):
        if not 20 < e.y < H * .62:
            return
        e.cd -= dt
        if e.st == 0 and e.cd <= 0:
            e.st, e.cd = 1, s.c["ring"]
            e.tx, e.ty = clamp(s.px + s.vx * .25, 40, W - 40), clamp(s.py + s.vy * .25, 140, H - 60)
        elif e.st == 1:
            if e.cd <= 0:
                e.st, e.cd = 0, max(3.4 - .08 * s.level, 1.7)
                pts = [(e.x, e.y)]
                n = 7
                for i in range(1, n + 1):
                    f = i / n
                    pts.append((e.x + (e.tx - e.x) * f + (random.uniform(-16, 16) if i < n else 0),
                                e.y + (e.ty - e.y) * f))
                s.bolts.append(dict(pts=pts, t=.28))
                if math.hypot(e.tx - s.px, e.ty - s.py) < 42 + 8:
                    s.hurt()

    def collide(s):
        for e in s.ents:
            d = math.hypot(e.x - s.px, e.y - s.py)
            if e.k == "gem" and d < e.r + 22:
                e.dead = True
                v = (10, 25, 50)[e.g]
                s.score += v
                s.pop(f"+{v}", e.x, e.y, (140, 230, 255))
            elif e.k == "rabbit" and d < e.r + 22:
                e.dead = True
                s.score += 150
                if s.hp < MAX_HP:
                    s.hp += 1
                s.pop("+1 vida +150", e.x, e.y, (255, 120, 150))
            elif e.k in ("mount", "storm") and d < e.r + 13:
                s.hurt()
                if d > 1:
                    n = e.r + 15
                    s.px = clamp(e.x + (s.px - e.x) / d * n, 40, W - 40)
                    s.py = clamp(e.y + (s.py - e.y) / d * n, 130, H - 70)
            elif e.k in ("hawk", "meteor") and d < e.r + 13 and getattr(e, "warn", 0) <= 0:
                s.hurt()
                e.dead = True

    # ---------- desenho ----------
    def draw_ground(s, scr):
        A, off = s.A, int(s.ground) % 512
        mix = s.prev is not None and s.fade < 1
        for b, a in ([(s.prev, 255), (biome(s.level), int(255 * s.fade))] if mix else [(biome(s.level), 255)]):
            t = A["tile"][b]
            t.set_alpha(a)
            y = off - 512
            while y < H:
                scr.blit(t, (0, y))
                y += 512
        if s.fade >= 1:
            s.prev = None

    def _blit(s, scr, img, x, y, shade=True, off=(14, 22)):
        r = img.get_rect(center=(int(x), int(y)))
        if shade:
            scr.blit(shadow(s.A, img), r.move(*off))
        scr.blit(img, r)

    def draw(s, scr):
        A = s.A
        s.draw_ground(scr)
        for e in s.ents:
            if e.k == "mount":
                s._blit(scr, A["mount"][e.sz], e.x, e.y, off=(16, 20))
            elif e.k == "rabbit":
                s._blit(scr, rot(A, A["rabbit"], e.ang, 10), e.x, e.y, off=(8, 10))
            elif e.k == "gem":
                scr.blit(A["gem"][e.g], A["gem"][e.g].get_rect(center=(int(e.x), int(e.y))))
        for e in s.ents:
            if e.k == "hawk":
                s._blit(scr, A["hawk"][int(s.anim * 8 + e.ph) % 2], e.x, e.y, off=(20, 34))
        for e in s.ents:
            if e.k == "storm":
                s._blit(scr, A["storm"], e.x, e.y, off=(36, 60))
        # águia
        img = rot(A, A["eagle"][int(s.anim * 9) % 2], clamp(-s.vx / 28, -16, 16), 3)
        if s.inv <= 0 or int(s.anim * 16) % 2:
            s._blit(scr, img, s.px, s.py, off=(26, 44))
        # perigos que ficam sobre a águia
        for e in s.ents:
            if e.k == "storm" and e.st == 1:
                p = 1 - e.cd / s.c["ring"]
                scr.blit(A["glow"], A["glow"].get_rect(center=(int(e.tx), int(e.ty))))
                pygame.draw.circle(scr, (255, 225, 77), (int(e.tx), int(e.ty)), int(10 + 32 * p), 2)
                for i in range(0, 20, 2):
                    a0, a1 = i * math.tau / 20, (i + 1) * math.tau / 20
                    pygame.draw.line(scr, (255, 225, 77), (e.tx + 46 * math.cos(a0), e.ty + 46 * math.sin(a0)),
                                     (e.tx + 46 * math.cos(a1), e.ty + 46 * math.sin(a1)), 3)
            elif e.k == "meteor":
                if e.warn > 0:
                    pygame.draw.polygon(scr, (255, 70, 50), [(e.x, 34), (e.x - 14, 8), (e.x + 14, 8)])
                    text(scr, "!", 26, (e.x, 20), (255, 255, 255), out=(120, 0, 0))
                else:
                    ang = math.degrees(math.atan2(e.vx, e.vy))
                    s._blit(scr, rot(A, A["meteor"], ang, 6), e.x, e.y, shade=False)
        for b in s.bolts:
            lay = pygame.Surface((W, H), pygame.SRCALPHA)
            for w, col in ((11, (140, 184, 255, 90)), (5, (219, 233, 255, 220)), (2, (255, 255, 255, 255))):
                pygame.draw.lines(lay, col, False, b["pts"], w)
            scr.blit(lay, (0, 0))
        for hc in s.hclouds:
            c = A["cloud"]
            c.set_alpha(70)
            scr.blit(c, (hc[0] - 95, hc[1] - 70))
            c.set_alpha(255)
            hc[1] += s.c["speed"] * hc[2] * getattr(s, "dt", .016)
            if hc[1] > H + 120:
                hc[0], hc[1] = random.uniform(0, W), -140
        scr.blit(A["haze"], (0, 0))
        for t in s.texts:
            text(scr, t[0], 30, (t[1], t[2]), t[4])
        s.draw_hud(scr)

    def draw_hud(s, scr):
        A = s.A
        for i in range(MAX_HP):
            scr.blit(A["heart"] if i < s.hp else A["heart0"], (10 + i * 29, 10))
        r = text(scr, f"{s.score:,}".replace(",", "."), 30, (W - 10, 22), anchor="midright")
        scr.blit(A["gem_s"], (r.left - 28, r.centery - 11))
        pill = pygame.Surface((96, 26), pygame.SRCALPHA)
        pygame.draw.rect(pill, (27, 42, 68, 170), pill.get_rect(), border_radius=13)
        scr.blit(pill, (W - 106, 40))
        text(scr, f"NÍVEL {s.level}", 22, (W - 58, 53))
        pygame.draw.circle(scr, (27, 42, 68), PAUSE_RECT.center, 17)
        for dx in (-5, 3):
            pygame.draw.rect(scr, (255, 255, 255), (PAUSE_RECT.centerx + dx, PAUSE_RECT.centery - 7, 4, 14))
        bar = s.lt / LEVEL_TIME
        pygame.draw.rect(scr, (27, 42, 68), (10, H - 10, W - 20, 5), border_radius=3)
        pygame.draw.rect(scr, (255, 200, 70), (10, H - 10, int((W - 20) * bar), 5), border_radius=3)
        if s.banner > 0:
            a = min(1, s.banner)
            ov = pygame.Surface((W, 110), pygame.SRCALPHA)
            ov.fill((10, 20, 40, int(150 * a)))
            scr.blit(ov, (0, 250))
            text(scr, f"NÍVEL {s.level}", 54, (W / 2, 288))
            text(scr, NEWS.get(s.level, f"Velocidade {int(s.c['speed'])}"), 26, (W / 2, 330), (255, 220, 120))
