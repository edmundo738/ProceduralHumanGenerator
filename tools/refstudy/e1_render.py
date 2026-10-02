# -*- coding: utf-8 -*-
"""E1 — micro-gate: render numpy (mesmo rig p/ TODOS) + métricas de imagem.

O Blender 5.0.1 do sandbox exige contexto EGL/GL mesmo em Cycles CPU (crash
epoxy, 2026-10-02) — em vez de lutar, o rig passa a ser NUMPY (Lambert 2
luzes, constantes do render_torso.build_scene) aplicado IDENTICAMENTE a
refs, B2, E1 e E1N (controlo).  Superfície frontal: máx y por (x,z) via
fatiamento de segmentos (plane_scan v3.2); normais por gradientes.

Uso: python3 tools/refstudy/e1_render.py
Saídas: docs/head_phaseA/e1_gate.png, e1_gate_side.png + métricas stdout
"""
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)
WORK = os.path.join(ROOT, "out", "refstudy")
DOCS = os.path.join(ROOT, "docs", "head_phaseA")

import geom  # noqa: E402
from plane_scan import normalise  # noqa: E402

WIN = 660.0            # mm
ZC = 1255.0
N = 520
RES = WIN / N          # mm/px
L_KEY = np.array([2.0, 2.4, 3.0]); L_KEY /= np.linalg.norm(L_KEY)
L_FILL = np.array([-2.5, 1.0, 2.0]); L_FILL /= np.linalg.norm(L_FILL)


def load_mm(name, flip):
    d = np.load(os.path.join(WORK, f"raw_{name}.npz"))
    V, T = d["V"], d["T"]
    if name.startswith("e1"):
        return V.copy(), T          # já em mm@1700 (tronco)
    return normalise(V, flip), T


def surface(V, T, mode="front"):
    """Grelha (N,N): superfície visível (máx y ou máx x) na janela.

    Linhas = z (topo→fundo), colunas = x (front) ou y (side).  NaN fora.
    """
    if mode == "front":
        V2, cols, c_lo = V, V[:, 0], -WIN / 2
    else:                            # side: câmara em +x → superfície = máx x
        V2 = np.ascontiguousarray(V[:, [1, 0, 2]])   # troca x↔y
        cols, c_lo = V2[:, 0], -WIN / 2
    g = np.full((N, N), np.nan)
    z_hi = ZC + WIN / 2
    for r in range(N):
        z0 = z_hi - (r + 0.5) * RES
        segs = geom.slice_segments(V2, T, z0)
        if segs is None or len(segs) == 0:
            continue
        lo = -WIN / 2
        n = N
        top = np.full(n, np.nan)
        for s in segs:
            (a0, b0), (a1, b1) = s[0], s[1]
            k = max(2, int(abs(a1 - a0) / RES) + 1)
            cs = np.linspace(a0, a1, k)
            ys = np.linspace(b0, b1, k)
            idx = np.clip(((cs - lo) / RES).astype(int), 0, n - 1)
            for j, i in enumerate(idx):
                if np.isnan(top[i]) or ys[j] > top[i]:
                    top[i] = ys[j]
        g[r] = top
    return g


def shade(g, mode="front"):
    if mode == "front":
        n = np.stack([-np.gradient(g, RES, axis=1), np.ones_like(g),
                      -np.gradient(g, RES, axis=0)], -1)
    else:
        n = np.stack([np.ones_like(g), -np.gradient(g, RES, axis=1),
                      -np.gradient(g, RES, axis=0)], -1)
    n /= np.linalg.norm(n, axis=-1, keepdims=True) + 1e-12
    nd = np.clip(n @ L_KEY, 0, None)
    nf = np.clip(n @ L_FILL, 0, None)
    c = 0.55 * (0.06 + 0.95 * nd + 0.20 * nf)
    c[~np.isfinite(g)] = 0.0
    return np.nan_to_num(c, nan=0.0)


def render(V, T, mode="front"):
    return shade(surface(V, T, mode), mode)


# ---------------------------------------------------------------- métricas
def grid_box(img):
    """Caixa da mama (x±110, z 1140–1330) em grelha 1 mm."""
    bx = np.arange(-110, 111, 1.0)
    bz = np.arange(1330, 1139, -1.0)
    px = bx / RES + N / 2
    py = (ZC + WIN / 2 - bz) / RES
    ix = np.clip(np.round(px).astype(int), 0, N - 1)
    iy = np.clip(np.round(py).astype(int), 0, N - 1)
    return img[np.ix_(iy, ix)]


def contrast(g):
    m = g > 0.15
    return float(np.std(g[m])) if m.any() else float("nan")


def dl1(A, B, shift=15):
    best = float("inf")
    for dz in range(-shift, shift + 1, 3):
        for dx in range(-shift, shift + 1, 3):
            Bb = np.roll(np.roll(B, dz, 0), dx, 1)
            ma, mb = A > 0.15, Bb > 0.15
            u = ma | mb
            if u.sum() < 100 or (ma & mb).sum() / u.sum() <= 0.5:
                continue
            best = min(best, np.abs(A - Bb)[u].mean())
    return best


def main():
    srcs = [("real005", True), ("femalebase", False), ("swB2", False),
            ("e1", False), ("e1n", False)]
    fronts, sides = {}, {}
    for name, flip in srcs:
        V, T = load_mm(name, flip)
        fronts[name] = render(V, T, "front")
        print(f"render front {name} ok")
    for name, flip in (("real005", True), ("swB2", False), ("e1", False)):
        V, T = load_mm(name, flip)
        sides[name] = render(V, T, "side")
        print(f"render side {name} ok")

    G = {k: grid_box(v) for k, v in fronts.items()}
    print("\n=== caixa da mama (x±110, z1140–1330) — contraste local (std L) ===")
    for k in ("real005", "femalebase", "swB2", "e1n", "e1"):
        print(f"  {k:11s} {contrast(G[k]):.4f}")
    print("=== ΔL1 (alinhado ±15mm; baseline = real005↔femalebase) ===")
    for a, b in (("e1", "real005"), ("e1", "femalebase"), ("swB2", "real005"),
                 ("real005", "femalebase"), ("e1", "e1n")):
        print(f"  {a:9s} vs {b:11s} {dl1(G[a], G[b]):.4f}")

    # ---------------------------------------------------------------- painéis
    TILE = 470
    ROWS = [("real005 · ref", fronts["real005"]),
            ("femalebase · ref", fronts["femalebase"]),
            ("B2 · campo (actual)", fronts["swB2"]),
            ("E1N · parede SDF (controlo)", fronts["e1n"]),
            ("E1 · VOLUMES (novo)", fronts["e1"])]
    sheet = Image.new("RGB", (TILE + 16, (TILE + 30) * len(ROWS) + 56), (12, 12, 16))
    dr = ImageDraw.Draw(sheet)
    dr.text((10, 6), "E1 MICRO-GATE — mama frontal 660mm · rig numpy IDÊNTICO em todos · "
                     "gate: 'E1 lê como volume?' (responde E1>B2 ou células)",
            fill=(240, 240, 240))
    for i, (lbl, t) in enumerate(ROWS):
        y0 = 34 + i * (TILE + 30)
        dr.text((10, y0), lbl, fill=(240, 240, 240))
        im = Image.fromarray((np.nan_to_num(t) * 255).clip(0, 255).astype(np.uint8))
        sheet.paste(im.resize((TILE, TILE)), (8, y0 + 18))
    out = os.path.join(DOCS, "e1_gate.png")
    sheet.save(out)
    print("\npainel →", out)

    sheet2 = Image.new("RGB", (TILE + 16, (TILE + 30) * 3 + 56), (12, 12, 16))
    dr = ImageDraw.Draw(sheet2)
    dr.text((10, 6), "E1 — perfil 660mm (projeção da mama; costas = E2, loft sem curva S — "
                     "esperado)", fill=(240, 240, 240))
    for i, (lbl, t) in enumerate((("real005 · ref", sides["real005"]),
                                  ("B2 · campo", sides["swB2"]),
                                  ("E1 · volumes", sides["e1"]))):
        y0 = 34 + i * (TILE + 30)
        dr.text((10, y0), lbl, fill=(240, 240, 240))
        im = Image.fromarray((np.nan_to_num(t) * 255).clip(0, 255).astype(np.uint8))
        sheet2.paste(im.resize((TILE, TILE)), (8, y0 + 18))
    out2 = os.path.join(DOCS, "e1_gate_side.png")
    sheet2.save(out2)
    print("painel →", out2)


if __name__ == "__main__":
    main()
