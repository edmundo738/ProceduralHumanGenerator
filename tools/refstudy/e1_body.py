# -*- coding: utf-8 -*-
"""E1 REMAKE — tórax + mama como VOLUMENS (SDF) → malga por marching cubes.

docs/REMAKE_01.md estágio E1.  O corpo deixa de ser "anéis + campos" e passa
a ser uma FUNÇÃO DE DISTÂNCIA: parede torácica (loft polar suave das MESMAS
estações — as proporções medidas mantêm-se; a RESOLUÇÃO passa a ser infinita
e a interpolação suave, sem anéis de 16 pts nem subsurf) ∪ lóbulos mamários
teardrop (união suave smin, k calibrado) − fossa clavicular (peito superior
recuado).  Malha extraída por marching cubes a 1.5 mm.

Uso: python3 tools/refstudy/e1_body.py            → medidas no stdout
     python3 tools/refstudy/e1_body.py --save     → + out/refstudy/raw_e1.npz
"""
import os
import sys

import numpy as np
from scipy.interpolate import PchipInterpolator
from skimage.measure import marching_cubes

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)

from human_generator.pipeline.assemble import resolve_spec  # noqa: E402
from human_generator.core.anatomy import Anatomy  # noqa: E402

# ---------------------------------------------------------------- calibração
CAL = {
    # lóbulos mamários (spec breast_spec_v3: ápice x 69-71, y 79-97, z 1214-1266;
    # gap 7-34; prega 21-79; teardrop subida longa / polo inferior curto)
    "lobe": {"cx": 0.068, "cy": 0.044, "cz": 1.260,
             "rx": 0.057, "ry": 0.050, "rz_up": 0.078, "rz_dn": 0.062,
             "tilt": np.radians(-20.0), "yaw": np.radians(5.0)},
    "k_union": 0.028,          # união suave mama↔parede (mm de fillet)
    # fossa clavicular (f@1350 refs 22-27; parede das estações ~53)
    "fossa": {"cy": 0.098, "cz": 1.352, "rx": 0.125, "ry": 0.069, "rz": 0.060},
    "k_sub": 0.030,
    "grid_mm": 1.5,
}

# ---------------------------------------------------------------- estações → tabelas polares
spec = resolve_spec("realistic_female", seed=42)
anat = Anatomy.from_spec(spec)
SECS = sorted(anat.trunk_sections(), key=lambda s_: s_.center.z)
NA = 512                                   # amostras angulares por estação
R_TAB, C_TAB, Z_ST = [], [], []
for st in SECS:
    P = np.array([(p.x, p.y) for p in st.points(128)])
    c = P.mean(0)
    ang = np.arctan2(P[:, 1] - c[1], P[:, 0] - c[0])
    r = np.hypot(P[:, 0] - c[0], P[:, 1] - c[1])
    o = np.argsort(ang)
    ang, r = ang[o], r[o]
    #unwrap: ang monotónico para convexos; enrola ±π
    ang_u = np.unwrap(ang)
    a_u = np.linspace(-np.pi, np.pi, NA)
    R_TAB.append(np.interp(a_u, ang_u, r))
    C_TAB.append(c)
    Z_ST.append(st.center.z)
Z_ST = np.array(Z_ST)                                    # ascendente
R_TAB = np.array(R_TAB)                                  # (S, NA)
C_TAB = np.array(C_TAB)                                  # (S, 2)
_pR = PchipInterpolator(Z_ST, R_TAB, axis=0)             # suave em z (sem zigzag)
_pC = PchipInterpolator(Z_ST, C_TAB, axis=0)
A_U = np.linspace(-np.pi, np.pi, NA)
print(f"estações: {len(Z_ST)} (z {Z_ST[0]*1000:.0f}..{Z_ST[-1]*1000:.0f} mm)")


def wall_d(x, y, z):
    """Distância (aprox) à parede torácica: loft polar suave das estações."""
    z = np.asarray(z, float)
    zc = np.clip(z, Z_ST[0], Z_ST[-1])
    c = _pC(zc)                                          # (..., 2)
    th = np.arctan2(y - c[..., 1], x - c[..., 0])
    r = np.hypot(x - c[..., 0], y - c[..., 1])
    R = np.interp(th, A_U, np.empty(NA), period=2 * np.pi) if False else None
    # interpolação periódica: deslocar para a grelha A_U
    idx = (th + np.pi) / (2 * np.pi) * (NA - 1)
    i0 = np.floor(idx).astype(int) % NA
    i1 = (i0 + 1) % NA
    t = idx - np.floor(idx)
    Rz = _pR(zc)                                         # (..., NA)
    Rv = Rz[np.arange(np.shape(th)[0]), i0] * (1 - t) + \
        Rz[np.arange(np.shape(th)[0]), i1] * t if Rz.ndim == 2 else None
    d2 = r - Rv
    dz = np.abs(z - zc)
    out = np.abs(dz) > 0
    d = np.where(out, np.hypot(np.maximum(d2, 0.0), dz) * np.sign(d2 + 1e-12), d2)
    return d


def wall_d_slice(x, y, z0):
    """wall_d para um z ESCALAR e grelha x,y (NX, NY) — versão rápida."""
    zc = min(max(z0, Z_ST[0]), Z_ST[-1])
    c = _pC(zc)
    Rz = _pR(zc)                                          # (NA,)
    th = np.arctan2(y - c[1], x - c[0])
    r = np.hypot(x - c[0], y - c[1])
    idx = (th + np.pi) / (2 * np.pi) * (NA - 1)
    i0 = np.floor(idx).astype(int) % NA
    i1 = (i0 + 1) % NA
    t = idx - np.floor(idx)
    Rv = Rz[i0] * (1 - t) + Rz[i1] * t
    d2 = r - Rv
    dz = abs(z0 - zc)
    if dz > 0:
        return np.hypot(np.maximum(d2, 0.0), dz) * np.sign(d2 + 1e-12)
    return d2


def lobe_d(x, y, z, side):
    """Lóbulo mamário teardrop: elipsoide com rz superior longo / inferior
    curto, inclinado (topo para DENTRO da parede), guinado para fora."""
    L = CAL["lobe"]
    px = side * (x - L["cx"])
    py = y - L["cy"]
    pz = z - L["cz"]
    ct, st_ = np.cos(L["yaw"]), np.sin(L["yaw"])          # guinada (plano xy)
    rx_ = px * ct + py * st_
    ry_ = -px * st_ + py * ct
    ct, st_ = np.cos(L["tilt"]), np.sin(L["tilt"])        # inclinação sagital
    ry2 = ry_ * ct - pz * st_
    rz2 = ry_ * st_ + pz * ct
    rz = np.where(rz2 >= 0.0, L["rz_up"], L["rz_dn"])
    q = np.sqrt((rx_ / L["rx"]) ** 2 + (ry2 / L["ry"]) ** 2 + (rz2 / rz) ** 2)
    return (q - 1.0) * min(L["rx"], L["ry"], L["rz_up"])


def fossa_d(x, y, z):
    F = CAL["fossa"]
    q = np.sqrt((x / F["rx"]) ** 2 + ((y - F["cy"]) / F["ry"]) ** 2 +
                ((z - F["cz"]) / F["rz"]) ** 2)
    return (q - 1.0) * min(F["rx"], F["ry"], F["rz"])


def smin(a, b, k):
    h = np.clip(0.5 + 0.5 * (b - a) / k, 0.0, 1.0)
    return b * (1 - h) + a * h


def smax(a, b, k):
    return -smin(-a, -b, k)


_WALL_ONLY = os.environ.get("E1_WALL_ONLY", "") == "1"   # controlo negativo


def sdf_slice(x, y, z0):
    """SDF completo numa fatia z (x,y grelhas)."""
    d = wall_d_slice(x, y, z0)
    if not _WALL_ONLY:
        d = smin(d, lobe_d(x, y, np.full_like(x, z0), +1), CAL["k_union"])
        d = smin(d, lobe_d(x, y, np.full_like(x, z0), -1), CAL["k_union"])
    d = smax(d, -fossa_d(x, y, np.full_like(x, z0)), CAL["k_sub"])
    return d


# ---------------------------------------------------------------- volume + marching cubes
def build():
    g = CAL["grid_mm"] / 1000.0
    xs = np.arange(-0.21, 0.21, g)
    ys = np.arange(-0.17, 0.18, g)
    zs = np.arange(0.82, 1.66, g)
    NX, NY, NZ = len(xs), len(ys), len(zs)
    print(f"grelha {NX}x{NY}x{NZ} = {NX*NY*NZ/1e6:.0f}M células @ {CAL['grid_mm']}mm")
    vol = np.empty((NZ, NY, NX), np.float32)              # (z, y, x) p/ marching
    X, Y = np.meshgrid(xs, ys, indexing="ij")
    Xf, Yf = X.astype(float).ravel(), Y.astype(float).ravel()
    for k, z0 in enumerate(zs):
        d = sdf_slice(Xf, Yf, float(z0))
        vol[k] = d.reshape(NX, NY).T.astype(np.float32)
    V, T, _, _ = marching_cubes(vol, 0.0, spacing=(g, g, g))
    V = V[:, [2, 1, 0]] * 1.0                             # (z,y,x)→(x,y,z) m
    V[:, 0] += xs[0]
    V[:, 1] += ys[0]
    V[:, 2] += zs[0]
    return V, T


# ---------------------------------------------------------------- medidas (instrumento comum)
def measure(V, T):
    import geom
    sys.path.insert(0, HERE)
    from plane_scan import _top_from_segments, repair_front

    Vmm = V * 1000.0
    out = {}

    def sec(z0):
        r = _top_from_segments(Vmm, T, z0, 0, 2, -140.0, 140.0)
        return repair_front(*r) if r[0] is not None else (None, None)

    def front(z0, x0=0.0, xw=15.0):
        xb, y = sec(z0)
        if xb is None:
            return float("nan")
        m = np.abs(xb - x0) <= xw
        return float(np.nanmedian(y[m])) if m.any() else float("nan")

    # ápice
    best = (None, -1e9)
    for z0 in range(1150, 1311, 5):
        xb, y = _top_from_segments(Vmm, T, float(z0), 0, 2, 20.0, 110.0)
        if xb is None or not len(xb):
            continue
        i = int(np.nanargmax(y))
        if y[i] > best[1]:
            best = ((float(xb[i]), float(y[i]), float(z0)), float(y[i]))
    ax, ay, az = best[0]
    out["apex"] = (round(ax, 1), round(ay, 1), round(az, 1))
    xb, y = sec(az)
    out["esterno"] = round(float(np.nanmedian(y[np.abs(xb) <= 8.0])), 1)
    out["gap"] = round(ay - out["esterno"], 1)
    # prega (sagital no x do ápice)
    V2 = np.ascontiguousarray(Vmm[:, [2, 1, 0]])
    r = _top_from_segments(V2, T, ax, 0, 2, az - 170, az + 170)
    if r[0] is not None:
        zb, sy = repair_front(*r)
        low = (zb < az - 25) & (zb > az - 150)
        fold = float(sy[low].min()) if low.any() else float("nan")
        out["prega_prom"] = round(ay - fold, 1)
    out["f1350"] = round(front(1350.0), 1)
    out["f1090"] = round(front(1090.0), 1)
    out["barriga_peito"] = round(out["f1090"] - out["esterno"], 1)
    # secção no z do ápice (curva para inspeção)
    xs_ = np.arange(1, 131, 5.0)
    out["sec1255"] = [int(np.interp(x_, xb, y)) for x_ in xs_]
    return out


if __name__ == "__main__":
    V, T = build()
    m = measure(V, T)
    print("\n=== E1 medidas (frame mm@1700) ===")
    print(f"ápice (x,y,z) = {m['apex']}   [refs x 69-71, y 79-97, z 1214-1266]")
    print(f"esterno = {m['esterno']}        [refs 58-89]")
    print(f"gap = {m['gap']}              [refs 7-34]")
    print(f"prega_prom = {m.get('prega_prom')}       [refs 21-79]")
    print(f"f@1350 = {m['f1350']}             [refs 22-27]")
    print(f"f@1090 (barriga) = {m['f1090']}  · barriga-peito = {m['barriga_peito']} [refs -7..+9]")
    print(f"secção @z_ápice y(x) x=1..131 passo 5: {m['sec1255']}")
    print(f"malha: v={len(V)} tris={len(T)}")
    if "--save" in sys.argv:
        os.makedirs(os.path.join(ROOT, "out", "refstudy"), exist_ok=True)
        np.savez_compressed(os.path.join(ROOT, "out", "refstudy",
                                     "raw_e1n.npz" if _WALL_ONLY else "raw_e1.npz"),
                            V=(V * 1000.0).astype(np.float32), T=T.astype(np.int64))
        print("→ out/refstudy/raw_e1.npz (V em mm)")
