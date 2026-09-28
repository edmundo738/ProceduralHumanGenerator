"""Grandes planos da face (frente, ¾, lado) — mesmo rasterizador para nós e refs."""
import os, sys
import numpy as np
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "headstudy"))
import figures as FG  # noqa
BOX = {"front": (-70, 70, 10, 170), "q": (-60, 110, 10, 170), "side": (-40, 140, 10, 170)}


def row(nm, px=0.35):
    Vn, T = FG.load_norm(nm)[:2]
    ims = []
    for k in ("front", "q", "side"):
        img, _, _ = FG.raster(Vn, T, k, BOX[k], px=px)
        ims.append(Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8)))
    W = sum(i.width for i in ims); H = max(i.height for i in ims) + 24
    r = Image.new("L", (W, H), 255); x = 0
    for i in ims:
        r.paste(i, (x, 24)); x += i.width
    ImageDraw.Draw(r).text((6, 5), nm, fill=0)
    return r


if __name__ == "__main__":
    rows = [row(n) for n in sys.argv[2:]]
    W = max(r.width for r in rows); H = sum(r.height for r in rows)
    im = Image.new("L", (W, H), 255); y = 0
    for r in rows:
        im.paste(r, (0, y)); y += r.height
    im.save(sys.argv[1])
