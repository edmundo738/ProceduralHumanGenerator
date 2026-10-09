# -*- coding: utf-8 -*-
"""BASEMESH A — corpo = base mesh de qualidade + MORPHS paramétricos (caminho A).

Decisão do dono (2026-10-07, REMAKE_01 §10): deixar de gerar geometria do
zero (5 gates, 0 aprovações); a fundação anatómica passa a ser a base mesh
feminina da biblioteca (REF-F-REAL-001 "Female base.obj", CC0) e o PROGRAMA
gera corpos DIFERENTES ao clicar — morphs pequenos, medidos, em bandas.

Pipeline (numpy puro, sem Blender):
  load .obj → orientar (z↑, +y=frente) → normalizar 1700 mm
  → morphs por seed (estatura uniforme + cintura/anca/mama/glúteo/ombro/coxa
    + assimetria ε) → guardar raw_mNN.npz
  → medir (plane_scan v3.2: estatura, cintura, anca, mama)
  → render rig v2 (normais de VÉRTICE interpoladas nos cortes — não gradientes)

Uso: python3 tools/refstudy/basemesh_proto.py
Saídas: out/refstudy/raw_m{00..05}.npz + basemesh_proto.json
        docs/head_phaseA/basemesh_gen.png + basemesh_zoom.png
"""
import json
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)
WORK = os.path.join(ROOT, "out", "refstudy")
DOCS = os.path.join(ROOT, "docs", "head_phaseA")

BASE_OBJ = os.path.join(ROOT, "references", "female", "realistic",
                        "full_body", "REF-F-REAL-001", "Female base.obj")

# ---------------------------------------------------------------- bandas dos morphs [HYPOTHESIS p/ proto]
# A.0 (gate A POSITIVO 2026-10-07, mas dono: "diferenças microscópicas") →
# A.1 alarga as amplitudes ~3× (HCG_BM_WIDE=1).  A base é a fundação; os
# morphs têm licença para variar VISIVELMENTE sem "desenhar anatomia".
BANDS = {
    "stature": (1600.0, 1740.0),     # mm (uniforme — preserva anatomia)
    "waist": (0.93, 1.05),           # × largura da cintura da base
    "hip": (0.98, 1.07),             # × largura da anca
    "breast": (-0.15, 0.30),         # ± fracção da projecção da base (~28 mm)
    "glute": (-0.10, 0.20),
    "shoulder": (0.98, 1.04),
    "thigh": (0.98, 1.06),
    "asym": (0.0, 0.035),            # ε: mama esq mais cheia (directriz §13)
}
BANDS_WIDE = {
    "stature": (1500.0, 1810.0),
    "waist": (0.80, 1.20),
    "hip": (0.94, 1.12),
    "breast": (-0.30, 0.55),
    "glute": (-0.20, 0.35),
    "shoulder": (0.96, 1.08),
    "thigh": (0.95, 1.12),
    "asym": (0.0, 0.06),
}
WIDE = os.environ.get("HCG_BM_WIDE", "") == "1"
if WIDE:
    BANDS = BANDS_WIDE
SEEDS = [101, 202, 303, 404, 505]


def sm01(t):
    t = np.clip(t, 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def band_w(z, lo, hi, ramp=45.0):
    """Janela suave [lo,hi] com rampas de 45 mm."""
    return sm01((z - lo) / ramp) * (1.0 - sm01((z - hi) / ramp))


# ---------------------------------------------------------------- loader + orient
def load_obj(path):
    vs, fs = [], []
    with open(path) as f:
        for ln in f:
            if ln.startswith("v "):
                vs.append([float(x) for x in ln.split()[1:4]])
            elif ln.startswith("f "):
                idx = [int(p.split("/")[0]) - 1 for p in ln.split()[1:]]
                for k in range(1, len(idx) - 1):
                    fs.append([idx[0], idx[k], idx[k + 1]])
    return np.array(vs, float), np.array(fs, int)


def orient(V):
    """Frame mm@1700: z↑, +y=frente, x centrado — mapa EXACTO validado por
    diff directo contra a frame do pipeline das refs (bpy import):
    (x,y,z)_ref = (x_obj, −z_obj, y_obj)·S  (erro 0.1µm; 2026-10-07).
    Nota: y centrado por bbox (frame própria do protótipo; métricas de
    DIFERENÇA — gap, larguras, WHR — são invariantes à translação)."""
    V = V[:, [0, 2, 1]] * np.array([1.0, -1.0, 1.0])
    S = 1700.0 / (V[:, 2].max() - V[:, 2].min())
    V = V * S
    V[:, 2] -= V[:, 2].min()
    V[:, 0] -= (V[:, 0].max() + V[:, 0].min()) / 2
    V[:, 1] -= (V[:, 1].max() + V[:, 1].min()) / 2
    return V


def vertex_normals(V, T):
    a, b, c = V[T[:, 0]], V[T[:, 1]], V[T[:, 2]]
    fn = np.cross(b - a, c - a)
    N = np.zeros_like(V)
    for k in range(3):
        np.add.at(N, T[:, k], fn)
    n = np.linalg.norm(N, axis=1, keepdims=True)
    return N / np.maximum(n, 1e-12)


# ---------------------------------------------------------------- morphs
def morph(V, p):
    """Aplica o conjunto de morphs (frame mm@1700). Devolve V novo."""
    V = V.copy()
    # 1) estatura: escala UNIFORME (anatomia proporcional)
    V *= p["stature"] / 1700.0
    # 2) larguras regionais (laterais + 60% em profundidade)
    for key, (lo, hi, axis) in (("shoulder", (1385, 1470, 0)),
                                ("waist", (1010, 1105, 0)),
                                ("hip", (880, 985, 0)),
                                ("thigh", (690, 880, 0))):
        s = p[key] - 1.0
        if abs(s) < 1e-4:
            continue
        w = band_w(V[:, 2], lo, hi)
        V[:, 0] += s * V[:, 0] * w
        V[:, 1] += 0.6 * s * V[:, 1] * w
    # 3) mama: deslocamento +y com janela |x|, z (base já TEM anatomia)
    if abs(p["breast"]) > 1e-4:
        ax = np.abs(V[:, 0])
        w = band_w(V[:, 2], 1140, 1330, 55.0) * \
            (1.0 - sm01((ax - 125.0) / 40.0)) * sm01((ax - 12.0) / 22.0)
        proj = 28.0
        asym = 1.0 + np.where(V[:, 0] < 0, p["asym"], -p["asym"])
        V[:, 1] += p["breast"] * proj * w * asym
    # 4) glúteo: −y na janela posterior
    if abs(p["glute"]) > 1e-4:
        ax = np.abs(V[:, 0])
        back = V[:, 1] < -20.0
        w = band_w(V[:, 2], 830, 965, 50.0) * \
            (1.0 - sm01((ax - 115.0) / 40.0)) * sm01((ax - 15.0) / 25.0)
        V[:, 1] -= p["glute"] * 30.0 * w * back
    return V


def sample_params(rng):
    p = {}
    for k, (lo, hi) in BANDS.items():
        p[k] = float(rng.uniform(lo, hi))
    return p


# ---------------------------------------------------------------- medidas (instrumento comum)
def measure(V, T):
    from plane_scan import section_top
    out = {}
    out["stature"] = round(float(V[:, 2].max() - V[:, 2].min()), 0)

    def width(z0):
        # bbox de vértices numa banda ±25 mm (robusto: repair_front apara os
        # flancos da curva frontal; braços em T-pose vivem em z~1300-1500,
        # não interferem na cintura/anca)
        m = (V[:, 2] > z0 - 25) & (V[:, 2] < z0 + 25) & (np.abs(V[:, 0]) < 200)
        if not m.any():
            return float("nan")
        return float(V[m, 0].max() - V[m, 0].min())

    out["waist_w"] = round(width(1050.0), 1)
    out["hip_w"] = round(width(930.0), 1)
    out["whr"] = round(out["waist_w"] / out["hip_w"], 3)
    best = (None, -1e9)
    for z0 in range(1150, 1296, 5):    # <1300: exclui ombro/braços (T-pose)
        xb, y = section_top(V, T, float(z0), 20.0, 110.0)
        if xb is None or not len(xb):
            continue
        i = int(np.nanargmax(y))
        if y[i] > best[1]:
            best = ((float(xb[i]), float(y[i]), float(z0)), float(y[i]))
    out["apex"] = best[0] and (round(best[0][0], 0), round(best[0][1], 0),
                               round(best[0][2], 0))
    xb, y = section_top(V, T, float(best[0][2]), 0.0, 140.0)
    est = float(np.nanmedian(y[np.abs(xb) <= 8.0]))
    out["gap"] = round(best[0][1] - est, 1)
    return out


# ---------------------------------------------------------------- render rig v2 (normais de vértice)
L_KEY = np.array([2.0, 2.4, 3.0]); L_KEY /= np.linalg.norm(L_KEY)
L_FILL = np.array([-2.5, 1.0, 2.0]); L_FILL /= np.linalg.norm(L_FILL)


def slicer(V, T, N):
    """Pré-computa por triângulo: zmin/zmax (para activos por linha)."""
    a, b, c = V[T[:, 0]], V[T[:, 1]], V[T[:, 2]]
    return a, b, c, N[T[:, 0]], N[T[:, 1]], N[T[:, 2]], \
        np.minimum(a[:, 2], np.minimum(b[:, 2], c[:, 2])), \
        np.maximum(a[:, 2], np.maximum(b[:, 2], c[:, 2]))


def render_view(V, T, N, span=1900.0, zc=950.0, phi=0.0, res=520):
    """Clay: superfície frontal (max y) por coluna; normais interpoladas."""
    if phi:
        c, s = np.cos(phi), np.sin(phi)
        V = np.stack([c * V[:, 0] - s * V[:, 1], s * V[:, 0] + c * V[:, 1],
                      V[:, 2]], 1)
        N = np.stack([c * N[:, 0] - s * N[:, 1], s * N[:, 0] + c * N[:, 1],
                      N[:, 2]], 1)
    a, b, c_, na, nb, nc, zlo, zhi = slicer(V, T, N)
    g = np.full((res, res), np.nan)
    gn = np.zeros((res, res, 3))
    mm_per_px = span / res
    x_lo = -span / 2
    z_hi = zc + span / 2
    for r in range(res):
        z0 = z_hi - (r + 0.5) * mm_per_px
        act = np.where((zlo <= z0) & (zhi >= z0))[0]
        if not len(act):
            continue
        pts, nrm = [], []
        # intersecção por aresta (vectorizado por aresta)
        for (P, Q, NP, NQ) in ((a[act], b[act], na[act], nb[act]),
                               (b[act], c_[act], nb[act], nc[act]),
                               (c_[act], a[act], nc[act], na[act])):
            za, zb = P[:, 2], Q[:, 2]
            m = (za - z0) * (zb - z0) <= 0
            if not m.any():
                continue
            P, Q, NP, NQ = P[m], Q[m], NP[m], NQ[m]
            t = np.clip((z0 - P[:, 2]) / np.where(Q[:, 2] == P[:, 2],
                                                  1e-9, Q[:, 2] - P[:, 2]),
                        0.0, 1.0)[:, None]
            pts.append(P + (Q - P) * t)
            nrm.append(NP + (NQ - NP) * t)
        if not pts:
            continue
        pts = np.concatenate(pts)
        nrm = np.concatenate(nrm)
        nrm /= np.maximum(np.linalg.norm(nrm, axis=1, keepdims=True), 1e-12)
        # rasteriza: coluna = (x−x_lo)/mm_per_px; vencedor = max y
        col = ((pts[:, 0] - x_lo) / mm_per_px).astype(int)
        ok = (col >= 0) & (col < res)
        for px, py, pn in zip(col[ok], pts[ok, 1], nrm[ok]):
            if np.isnan(g[r, px]) or py > g[r, px]:
                g[r, px] = py
                gn[r, px] = pn
    nd = np.clip(gn @ L_KEY, 0, None)
    nf = np.clip(gn @ L_FILL, 0, None)
    img = 0.55 * (0.06 + 0.95 * nd + 0.20 * nf)
    img[~np.isfinite(g)] = 0.0
    return np.nan_to_num(img, nan=0.0)


# ---------------------------------------------------------------- main
def main():
    os.makedirs(WORK, exist_ok=True)
    V0, T = load_obj(BASE_OBJ)
    V0 = orient(V0)
    print(f"base: v={len(V0)} tris={len(T)} estatura={V0[:,2].max():.0f} mm")
    N0 = vertex_normals(V0, T)

    bodies = [("m00", None)]  # base sempre
    for sid in SEEDS:
        rng = np.random.default_rng(sid)
        pfx = "w" if WIDE else "m"
        bodies.append((f"{pfx}{sid % 100:02d}", sample_params(rng)))

    table = {}
    tiles_full, tiles_zoom, tiles_side = [], [], []
    for name, p in bodies:
        V = V0 if p is None else morph(V0, p)
        N = vertex_normals(V, T)
        np.savez_compressed(os.path.join(WORK, f"raw_{name}.npz"),
                            V=V.astype(np.float32), T=T)
        table[name] = {"params": p, "measures": measure(V, T)}
        tiles_full.append((name, p, render_view(V, T, N, 1900.0, 950.0)))
        tiles_zoom.append((name, p, render_view(V, T, N, 660.0, 1255.0)))
        tiles_side.append((name, p, render_view(V, T, N, 660.0, 1255.0,
                                                phi=np.pi / 2)))
        print(f"{name}: morphs={p is not None} medidas={table[name]['measures']}")

    json.dump(table, open(os.path.join(WORK, "basemesh_proto.json"), "w"),
              indent=1)

    def caption(p):
        if p is None:
            return "m00 · BASE (sem morph)"
        return (f"{p['stature']:.0f}mm · cintura×{p['waist']:.2f} · "
                f"anca×{p['hip']:.2f} · mama{p['breast']:+.2f} · "
                f"glúteo{p['glute']:+.2f}")

    TILE, PAD, LH = 300, 8, 18
    cols = 3
    rows = 2
    W = cols * TILE + (cols + 1) * PAD
    H = 34 + rows * (TILE + LH + PAD)
    sheet = Image.new("RGB", (W, H), (12, 12, 16))
    dr = ImageDraw.Draw(sheet)
    dr.text((10, 8), "CAMINHO A — base mesh + MORPHS: 6 corpos, 1 fundação " + ("· AMPLITUDES LARGAS (A.1) " if WIDE else "") +
                     "(Female base CC0) · rig v2 (normais de vértice)",
            fill=(240, 240, 240))
    for i, (name, p, img) in enumerate(tiles_full):
        r, c = divmod(i, cols)
        x0 = PAD + c * (TILE + PAD)
        y0 = 30 + r * (TILE + LH + PAD)
        dr.text((x0 + 2, y0), caption(p), fill=(230, 230, 230))
        im = Image.fromarray((img * 255).clip(0, 255).astype(np.uint8))
        sheet.paste(im.resize((TILE, TILE)), (x0, y0 + LH))
    out = os.path.join(DOCS, "basemesh_gen2.png" if WIDE else "basemesh_gen.png")
    sheet.save(out)
    print("painel →", out)

    # zoom (mama) — 3 corpos distintos em amplitude de mama
    picks = [tiles_zoom[0], tiles_zoom[3], tiles_zoom[5]]
    picks_s = [tiles_side[0], tiles_side[3], tiles_side[5]]
    W2 = 3 * TILE + 4 * PAD
    H2 = 34 + 2 * (TILE + LH + PAD)
    sheet2 = Image.new("RGB", (W2, H2), (12, 12, 16))
    dr = ImageDraw.Draw(sheet2)
    dr.text((10, 8), "CAMINHO A — zoom 660mm · frente (linha 1) / perfil "
                     "(linha 2) · variação de mama da base", fill=(240, 240, 240))
    for i, (name, p, img) in enumerate(picks):
        x0 = PAD + i * (TILE + PAD)
        y0 = 30
        dr.text((x0 + 2, y0), caption(p), fill=(230, 230, 230))
        im = Image.fromarray((img * 255).clip(0, 255).astype(np.uint8))
        sheet2.paste(im.resize((TILE, TILE)), (x0, y0 + LH))
    for i, (name, p, img) in enumerate(picks_s):
        x0 = PAD + i * (TILE + PAD)
        y0 = 30 + TILE + LH + PAD
        im = Image.fromarray((img * 255).clip(0, 255).astype(np.uint8))
        sheet2.paste(im.resize((TILE, TILE)), (x0, y0 + LH))
    out2 = os.path.join(DOCS, "basemesh_zoom2.png" if WIDE else "basemesh_zoom.png")
    sheet2.save(out2)
    print("painel →", out2)


if __name__ == "__main__":
    main()
