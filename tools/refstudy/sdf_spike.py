# -*- coding: utf-8 -*-
"""SPIKE REMAKE — a mama como VOLUME (SDF) vs campo por vértice (B2).

Decisão do dono (2026-10-02): 3 opções; escolha delegada ao agente com a
condição "se sentires que terá diferença e alguma razão".  Este spike É o
teste dessa razão (docs/REMAKE_01.md).

Hipótese [HYPOTHESIS]: o que faz a mama "ler" como volume na vista frontal
não é a saliência (B2 tem 21 mm e é invisível: ΔL1 0.9 vs parede nua) mas a
ESTRUTURA DE VOLUME — massa com prega, intersecção com a parede, gradiente
de sombreado.  Um volume implícito (elipsoide teardrop em união booleana com
a parede torácica das MESMAS estações) deve produzir contraste local de
sombreado próximo das refs, onde o campo por vértice produz ~nada.

Método: torax = estações actuais (mesma parede); mama = 2 lóbulos
elipsoidais teardrop; render ortográfico frontal + perfil (numpy, luz
key/fill igual ao rig dos painéis); medir na caixa da mama (x ±110,
z 1140–1330 mm): contraste local (std L) e ΔL1 vs refs, comparando com os
tiles do painel breast_c2_zoom.png (real005/femalebase/B2/N0).

Uso: python3 tools/refstudy/sdf_spike.py   (puro numpy; sem Blender)
Saídas: docs/head_phaseA/sdf_spike_front.png + números no stdout.
"""
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)

# ---------------------------------------------------------------- estações
from human_generator.pipeline.assemble import resolve_spec  # noqa: E402
from human_generator.core.anatomy import Anatomy  # noqa: E402

spec = resolve_spec("realistic_female", seed=42)
anat = Anatomy.from_spec(spec)
secs = sorted(anat.trunk_sections(), key=lambda s_: -s_.center.z)
RINGS = np.array([[(p.x, p.y) for p in s.points(16)] for s in secs])  # (S,16,2)
ZS = np.array([s.center.z for s in secs])            # descendente
ZA = ZS[::-1]                                        # ascendente
RA = RINGS[::-1]
ORIENT = np.sign(np.sum((RINGS[0][1:, 0] - RINGS[0][:-1, 0]) *
                        (RINGS[0][1:, 1] + RINGS[0][:-1, 1])))
print(f"estações: {len(ZS)}  z {ZS[-1]*1000:.0f}..{ZS[0]*1000:.0f} mm  orient={ORIENT}")


def inside_core(x, y, z):
    """Dentro do tubo das estações (interp linear de polígonos, sem roll).

    z escalar (a grelha é fatiada por z); x/y arrays (NX, NY).
    Teste de CRUZAMENTO (ray cast) — robusto para polígonos não convexos
    (o teste de convexidade/orientação falhou: min(cross) ≈ −0.01 em pontos
    interiores; medido 2026-10-02).
    """
    j = int(np.clip(np.searchsorted(ZA, z), 1, len(ZA) - 1))
    z0, z1 = ZA[j - 1], ZA[j]
    t = float(np.clip((z - z0) / max(1e-9, z1 - z0), 0.0, 1.0))
    P = RA[j - 1] * (1.0 - t) + RA[j] * t            # (16, 2)
    v0, v1 = P, np.roll(P, -1, axis=0)
    y0e = v0[:, 1][:, None, None]
    y1e = v1[:, 1][:, None, None]
    x0e = v0[:, 0][:, None, None]
    dx = (v1[:, 0] - v0[:, 0])[:, None, None]
    dy = (v1[:, 1] - v0[:, 1])[:, None, None]
    with np.errstate(divide="ignore", invalid="ignore"):
        cond1 = (y0e > y[None]) != (y1e > y[None])
        xint = x0e + (y[None] - y0e) * dx / dy
        cond2 = x[None] < xint
    return ((cond1 & cond2).sum(axis=0) % 2) == 1


# ---------------------------------------------------------------- lóbulos mama (SDF booleano)
# spec v3: ápice (~69, 93, ~1255) mm, esterno/parede 77, gap ~16, prega z~1185
LOB = {"cx": 0.063, "cy": 0.045, "cz": 1.268,
       "rx": 0.055, "ry": 0.052, "rz": 0.070, "tilt": np.radians(-20.0)}


def inside_lobe(x, y, z):
    ct, st = np.cos(LOB["tilt"]), np.sin(LOB["tilt"])
    px = x - LOB["cx"]
    py = y - LOB["cy"]
    pz = z - LOB["cz"]
    # rotação em x: leva o topo do lóbulo para DENTRO da parede (teardrop)
    ry_ = py * ct - pz * st
    rz_ = py * st + pz * ct
    return ((px / LOB["rx"]) ** 2 + (ry_ / LOB["ry"]) ** 2 +
            (rz_ / LOB["rz"]) ** 2) <= 1.0


# ---------------------------------------------------------------- grelha + superfícies
RES = 0.0015
xs = np.arange(-0.36, 0.36, RES)
ys = np.arange(-0.20, 0.22, RES)
zs = np.arange(0.95, 1.60, RES)
NX, NY, NZ = len(xs), len(ys), len(zs)
print(f"grelha {NX}x{NY}x{NZ} = {NX*NY*NZ/1e6:.0f}M células")

I = np.zeros((NX, NY, NZ), bool)
X, Y = np.meshgrid(xs, ys, indexing="ij")
for k, z in enumerate(zs):
    I[:, :, k] = inside_core(X, Y, z) | inside_lobe(X, Y, z) | \
        inside_lobe(-X, Y, z)

# frente: y_s(x, z) = max y dentro
rev = I[:, ::-1, :]
jmax = np.argmax(rev, axis=1)
has = rev.max(axis=1)
ys_f = np.where(has, ys[::-1][np.minimum(jmax, NY - 1)], np.nan)
# perfil direito: x_s(y, z) = max x dentro
revx = I[::-1, :, :]
imax = np.argmax(revx, axis=0)
hasx = revx.max(axis=0)
xs_s = np.where(hasx, xs[::-1][np.minimum(imax, NX - 1)], np.nan)


def shade(g, axis_vals, other, vertical, mode):
    """Lambert 2 luzes (rig do build_scene) sobre superfície implícita."""
    dg_du = np.gradient(g, axis_vals, axis=0)
    dg_dv = np.gradient(g, vertical, axis=1)
    if mode == "front":                       # y = g(x, z)
        n = np.stack([-dg_du, np.ones_like(g), -dg_dv], -1)
    else:                                     # x = g(y, z)
        n = np.stack([np.ones_like(g), -dg_du, -dg_dv], -1)
    n /= np.linalg.norm(n, axis=-1, keepdims=True) + 1e-12
    Lk = np.array([2.0, 2.4, 3.0]); Lk /= np.linalg.norm(Lk)
    Lf = np.array([-2.5, 1.0, 2.0]); Lf /= np.linalg.norm(Lf)
    nd = np.clip(n @ Lk, 0, None)
    nf = np.clip(n @ Lf, 0, None)
    c = 0.55 * (0.06 + 0.95 * nd + 0.20 * nf)
    c[~np.isfinite(g)] = 0.0
    return c


Lfront = shade(ys_f, xs, None, zs, "front")
Lside = shade(xs_s, ys, None, zs, "side")

# ---------------------------------------------------------------- render janela 660 mm (igual ao painel)
WIN = 0.66


def render(L, u_vals, v_vals, u_win, v_center, v_span):
    """Amostra L(u, v) numa janela 520px como os tiles (row 0 = z ALTO)."""
    pu = np.linspace(*u_win, 520)
    pv = v_center + np.linspace(v_span / 2, -v_span / 2, 520)   # top→bottom
    U, V = np.meshgrid(pu, pv)
    Lu = np.interp(U, u_vals, np.arange(len(u_vals)))
    Lv = np.interp(V, v_vals, np.arange(len(v_vals)))
    iu = np.clip(np.round(Lu).astype(int), 0, len(u_vals) - 1)
    iv = np.clip(np.round(Lv).astype(int), 0, len(v_vals) - 1)
    img = L[iu, iv]
    img[(Lu < 0) | (Lu > len(u_vals) - 1) | (Lv < 0) | (Lv > len(v_vals) - 1)] = 0.0
    return img


imgF = render(Lfront, xs, zs, (-WIN / 2, WIN / 2), 1.255, WIN)
imgS = render(Lside, ys, zs, (-WIN / 2, WIN / 2), 1.255, WIN)
for nm, im in (("frente", imgF), ("perfil", imgS)):
    print(f"render {nm}: p99={np.nanpercentile(im, 99):.3f} máx={np.nanmax(im):.3f} "
          f"corpo={(im > 0.1).mean()*100:.0f}%")

# ---------------------------------------------------------------- tiles do painel
panel = np.asarray(Image.open(os.path.join(
    ROOT, "docs", "head_phaseA", "breast_c2_zoom.png")).convert("L"), float) / 255.0
TILE, CW, CH, LH = 470, 482, 476, 40
def tile_px(r, c):
    return panel[30 + r * (CH + LH) + LH - 18: 30 + r * (CH + LH) + LH - 18 + TILE,
                 8 + c * CW + 6: 8 + c * CW + 6 + TILE]
TILES = {"real005": tile_px(0, 0), "femalebase": tile_px(1, 0),
         "N0": tile_px(3, 0), "B2": tile_px(5, 0)}
PPMM_T = TILE / (WIN * 1000)     # 0.7121 px/mm
PPMM_S = 520 / (WIN * 1000)      # 0.7879 px/mm


def to_mm_grid(Limg, ppmm, v_top_mm=1585.0, u_center_mm=0.0):
    """L(x, z) numa grelha comum de 1 mm na caixa da mama (x ±110, z 1140–1330)."""
    bx = np.arange(-110, 111, 1.0)          # mm
    bz = np.arange(1330, 1139, -1.0)        # mm, topo→fundo
    px = (bx - u_center_mm) * ppmm + Limg.shape[1] / 2.0
    py = (v_top_mm - bz) * ppmm
    ix = np.clip(np.round(px).astype(int), 0, Limg.shape[1] - 1)
    iy = np.clip(np.round(py).astype(int), 0, Limg.shape[0] - 1)
    return Limg[np.ix_(iy, ix)]


GRIDS = {k: to_mm_grid(t, PPMM_T) for k, t in TILES.items()}
GRIDS["SDF"] = to_mm_grid(imgF / max(1e-9, np.nanpercentile(imgF, 99)), PPMM_S)


def metrics(g):
    m = g > 0.15
    return (float(np.std(g[m])) if m.any() else float("nan"),
            float(m.mean()))


def delta_l1(a, b, shift=15):
    """ΔL1 após alinhar B a A (roll só em B; procura ±15 mm)."""
    La, Lb = GRIDS[a], GRIDS[b]
    best = (None, float("inf"))
    for dz in range(-shift, shift + 1, 3):
        for dx in range(-shift, shift + 1, 3):
            B = np.roll(np.roll(Lb, dz, axis=0), dx, axis=1)
            ma, mb = La > 0.15, B > 0.15
            u = ma | mb
            if u.sum() < 100:
                continue
            iou = (ma & mb).sum() / u.sum()
            d = np.abs(La - B)[u].mean()
            if iou > 0.5 and d < best[1]:
                best = ((dz, dx), d)
    return best


print("\n=== CAIXA DA MAMA (x ±110, z 1140–1330) — contraste local (std L) ===")
for k in ("real005", "femalebase", "N0", "B2", "SDF"):
    s, cov = metrics(GRIDS[k])
    print(f"  {k:11s} contraste={s:.4f}  cobertura={100*cov:.0f}%")
print("\n=== ΔL1 na caixa (após alinhamento ±15 mm) ===")
for a, b in (("B2", "real005"), ("B2", "femalebase"), ("SDF", "real005"),
             ("SDF", "femalebase"), ("N0", "B2"), ("real005", "femalebase")):
    sh, d = delta_l1(a, b)
    print(f"  {a:10s} vs {b:11s} ΔL1={d:.4f} (alinho B {sh})")

# secção do spike a z≈1255 (frente normalizada)
bz = np.arange(1330, 1139, -1.0)
row = np.argmin(np.abs(bz - 1255))
Lrow = GRIDS["SDF"][row]
bx = np.arange(-110, 111, 1.0)
mm = Lrow > 0.15
if mm.any():
    xs_on = bx[mm]
    print(f"\nsecção spike z≈1255: presença x ∈ [{xs_on.min():.0f}, {xs_on.max():.0f}] mm; "
          f"L máx={Lrow[mm].max():.2f}")

# ---------------------------------------------------------------- folha de contacto
CROPS = [("real005 (ref)", "real005"), ("femalebase (ref)", "femalebase"),
         ("B2 · campo (actual)", "B2"), ("SDF · volume (spike)", "SDF")]
W = 221
sheet = Image.new("RGB", (W + 8, (W + 26) * len(CROPS) + 30), (12, 12, 16))
dr = ImageDraw.Draw(sheet)
dr.text((8, 6), "SPIKE REMAKE — mama: campo (B2) vs VOLUME (SDF) · frontal 660mm",
        fill=(240, 240, 240))
for i, (lbl, k) in enumerate(CROPS):
    g = (GRIDS[k] * 255).clip(0, 255).astype(np.uint8)
    im = Image.fromarray(g).resize((W, W))
    y0 = 26 + i * (W + 26)
    dr.text((8, y0 - 2), lbl, fill=(240, 240, 240))
    sheet.paste(im, (4, y0 + 14))
out = os.path.join(ROOT, "docs", "head_phaseA", "sdf_spike_front.png")
sheet.save(out)
print("\nfolha →", out)
