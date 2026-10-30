"""Reduz o peso dos assets (tiles em JPEG, névoa em meia resolução)."""
from pathlib import Path
from PIL import Image
A = Path(__file__).resolve().parent.parent / "assets"
for p in A.glob("tile_*.png"):
    Image.open(p).convert("RGB").save(p.with_suffix(".jpg"), quality=86, optimize=True)
    p.unlink()
h = Image.open(A / "haze.png").convert("RGBA")
h.resize((225, 400), Image.LANCZOS).save(A / "haze.png", optimize=True)
