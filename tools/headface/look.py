"""Painel rápido: nossas cabeças vs refs (rasterizador do HEAD STUDY 01)."""
import os, sys
import numpy as np
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "headstudy"))
import figures as FG  # noqa

def panel(names, out, kinds=("front", "q", "side"), px=0.8, loader=None):
    rows = []
    for nm in names:
        Vn, T = loader(nm) if loader and nm not in ("makehuman", "femalebase", "bodytopo", "femalechar") else FG.load_norm(nm)[:2]
        ims = []
        for k in kinds:
            box = {"front": (-100, 100, -40, 235), "side": (-120, 130, -40, 235), "q": (-120, 130, -40, 235)}[k]
            img, _, _ = FG.raster(Vn, T, k, box, px=px)
            ims.append(Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8)))
        W = sum(i.width for i in ims); Hh = max(i.height for i in ims) + 22
        row = Image.new("L", (W, Hh), 255); x = 0
        for i in ims:
            row.paste(i, (x, 22)); x += i.width
        ImageDraw.Draw(row).text((6, 4), nm, fill=0)
        rows.append(row)
    W = max(r.width for r in rows); Hh = sum(r.height for r in rows)
    im = Image.new("L", (W, Hh), 255); y = 0
    for r in rows:
        im.paste(r, (0, y)); y += r.height
    im.save(out)

if __name__ == "__main__":
    panel(sys.argv[2:], sys.argv[1])
