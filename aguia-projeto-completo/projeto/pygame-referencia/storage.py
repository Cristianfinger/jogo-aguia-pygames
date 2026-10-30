"""Autosave e ranking.

No navegador (pygbag) usa localStorage e a ponte JS definida em index.html
(aguiaSubmit / aguiaRefresh / aguiaTop). No desktop grava arquivos .json.
"""
import json
import os
import sys

WEB = sys.platform == "emscripten"
if WEB:
    import platform

    JS = platform.window


def _get(k):
    try:
        if WEB:
            v = JS.localStorage.getItem(k)
            return None if v is None else str(v)
        with open(f".{k}.json", encoding="utf-8") as f:
            return f.read()
    except Exception:
        return None


def _put(k, v):
    try:
        if WEB:
            JS.localStorage.setItem(k, v)
        else:
            with open(f".{k}.json", "w", encoding="utf-8") as f:
                f.write(v)
    except Exception:
        pass


def _del(k):
    try:
        if WEB:
            JS.localStorage.removeItem(k)
        elif os.path.exists(f".{k}.json"):
            os.remove(f".{k}.json")
    except Exception:
        pass


# ---------- autosave ----------
def load():
    try:
        d = json.loads(_get("aguia_save") or "null")
        ok = isinstance(d, dict) and 1 <= int(d["level"]) <= 20 and 0 <= float(d["t"]) < 600
        return d if ok else None
    except Exception:
        return None


def save(d):
    _put("aguia_save", json.dumps(d))


def clear():
    _del("aguia_save")


# ---------- nome ----------
def name():
    return _get("aguia_name") or ""


def ask_name(force=False):
    n = name()
    if n and not force:
        return n
    if WEB:
        try:
            r = JS.prompt("Seu nome para o ranking (até 12 letras):", n or "")
            r = "" if r is None else str(r).strip()[:12]
            n = r or n
        except Exception:
            pass
    n = n or "Jogador"
    _put("aguia_name", n)
    return n


# ---------- ranking local ----------
def local_top():
    try:
        d = json.loads(_get("aguia_rank") or "[]")
        return [x for x in d if isinstance(x, dict)][:10]
    except Exception:
        return []


def add_local(n, score, level):
    d = local_top() + [{"name": n, "score": int(score), "level": int(level)}]
    d.sort(key=lambda x: -x["score"])
    d = d[:10]
    _put("aguia_rank", json.dumps(d))
    for i, x in enumerate(d):
        if x["name"] == n and x["score"] == int(score):
            return i + 1
    return 0


# ---------- ranking online (opcional) ----------
def submit(n, score, level):
    try:
        if WEB:
            JS.aguiaSubmit(n, int(score), int(level))
    except Exception:
        pass


def refresh():
    try:
        if WEB:
            JS.aguiaRefresh()
    except Exception:
        pass


def online_top():
    try:
        if WEB:
            d = json.loads(str(JS.aguiaTop))
            return [x for x in d if isinstance(x, dict)][:10]
    except Exception:
        pass
    return []
