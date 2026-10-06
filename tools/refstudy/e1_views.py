# -*- coding: utf-8 -*-
"""E1 — multi-vista clay (frente / ¾ / perfil / costas) — BODY_SPEC_REMAKE §7.

Roda a malha em torno de z e usa o rig numpy (e1_render) — clay cinzento,
mesma câmara/luz/escala em todos os tiles.  Painel: refs vs E1 vs V0(antigo).

Uso: python3 tools/refstudy/e1_views.py  → docs/head_phaseA/e1_views.png
"""
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)
DOCS = os.path.join(ROOT, "docs", "head_phaseA")

from e1_render import surface, shade, load_mm  # noqa: E402

VIEWS = [("frente", 0.0), ("3/4", 0.6109), ("perfil", 1.5708), ("costas", 3.1416)]
SRCS = [("real005", True), ("femalebase", False), ("V0·antigo", False), ("E1·volumes", False)]


def render_view(V, T, phi):
    """Clay no azimute φ (rad): roda a malha −φ e usa a superfície frontal."""
    c, s = np.cos(-phi), np.sin(-phi)
    Vr = np.empty_like(V)
    Vr[:, 0] = c * V[:, 0] - s * V[:, 1]
    Vr[:, 1] = s * V[:, 0] + c * V[:, 1]
    Vr[:, 2] = V[:, 2]
    g = surface(Vr, T, "front")
    return shade(g, "front")


def main():
    tiles = {}
    for i, (name, flip) in enumerate(SRCS):
        key = "swV0" if name.startswith("V0") else ("e1" if name.startswith("E1") else name)
        V, T = load_mm(key, flip)
        for vname, phi in VIEWS:
            tiles[(name, vname)] = render_view(V, T, phi)
        print(f"render {name} ({len(VIEWS)} vistas) ok")

    TILE, PAD, LH = 300, 10, 26
    W = TILE * len(VIEWS) + PAD * (len(VIEWS) + 1)
    H = (TILE + LH + PAD) * len(SRCS) + 40
    sheet = Image.new("RGB", (W, H), (12, 12, 16))
    dr = ImageDraw.Draw(sheet)
    dr.text((12, 8), "E1 — MULTI-VISTA clay (rig numpy comum) · gate: ler como "
                     "corpo? apontar zona (p.ex. 'E1 costas Z6')", fill=(240, 240, 240))
    for c, (vname, _) in enumerate(VIEWS):
        dr.text((PAD + c * (TILE + PAD) + TILE // 2 - 20, 26), vname,
                fill=(200, 200, 200))
    for r, (name, _) in enumerate(SRCS):
        y0 = 46 + r * (TILE + LH + PAD)
        dr.text((PAD, y0), name, fill=(240, 240, 240))
        for c, (vname, _) in enumerate(VIEWS):
            t = tiles[(name, vname)]
            im = Image.fromarray((np.nan_to_num(t) * 255).clip(0, 255).astype(np.uint8))
            sheet.paste(im.resize((TILE, TILE)), (PAD + c * (TILE + PAD), y0 + LH))
    out = os.path.join(DOCS, "e1_views.png")
    sheet.save(out)
    print("painel →", out)


if __name__ == "__main__":
    main()
