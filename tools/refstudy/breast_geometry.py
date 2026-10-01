# -*- coding: utf-8 -*-
"""[SUPERSEDED — v1] Extractor de propriedades da mama por janelas de vértices.

⚠️ INSTRUMENTO COM ARTEFACTOS CONHECIDOS — não usar para números novos:
  · janelas de vértices (|x−x0|<w) MENTEM entre malhas (cobertura topológica
    varia; "ápice" salta 42↔78);
  · o real005 é fragmentado (69 comps) e as janelas apanhavam fios/comp
    erradas;
  · os primeiros números da especificação da mama saíram daqui e estavam
    contaminados (esterno_gap −0.1 vs 20–34 real).
SUBSTITUÍDO por plane_scan v3.2 + breast_spec.py (curvas rasterizadas).
Mantido por PROVENIÊNCIA (MANDATO RND: resultados e instrumentos negativos
ficam registados).  Ver docs/BREAST_C2_01.md §2.

Uso: python3 tools/refstudy/breast_geometry.py   → tabela + breast_geometry.json
"""
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from _paths import WORK  # noqa: E402

MODELS = [
    ("real005", True), ("femalebase", False), ("femalechar", True),
    ("animeF", True), ("swN0", False), ("swV0", False),
]


def load(name, flip):
    d = np.load(os.path.join(WORK, f"raw_{name}.npz"))
    V, T = d["V"].copy(), d["T"]
    S, fl = V[:, 2].max() - V[:, 2].min(), V[:, 2].min()
    V[:, 2] -= fl
    V[:, 0] -= (V[:, 0].max() + V[:, 0].min()) / 2
    V *= 1700.0 / S
    if flip:
        V[:, 1] *= -1
    return V, T


def ymax(V, mask_extra=None, x_win=8.0, z0=0.0, z_win=8.0, x0=None):
    m = (abs(V[:, 2] - z0) < z_win)
    if x0 is not None:
        m &= (abs(V[:, 0] - x0) < x_win)
    if mask_extra is not None:
        m &= mask_extra
    v = V[m]
    return float(v[:, 1].max()) if len(v) else float("nan")


def analyse(V):
    # ---- 1. ápice: varre x∈[30,110], z∈[1150,1310]
    best = (None, -1e9)
    for x0 in range(30, 111, 4):
        for z0 in range(1150, 1311, 6):
            y = ymax(V, x0=x0, z0=z0, x_win=5.0, z_win=5.0)
            if y > best[1]:
                best = ((x0, z0, y), y)
    ax, az, ay = best[0]
    # refina
    for x0 in np.arange(ax - 5, ax + 5.1, 1.0):
        for z0 in np.arange(az - 5, az + 5.1, 1.0):
            y = ymax(V, x0=float(x0), z0=float(z0), x_win=3.0, z_win=3.0)
            if y > ay:
                ax, az, ay = float(x0), float(z0), y

    # ---- 2. perfil vertical y(z) no plano do ápice
    zs = np.arange(az - 160, az + 161, 2.0)
    prof = np.array([ymax(V, x0=ax, z0=float(z), x_win=8.0, z_win=2.0) for z in zs])

    wall_up = float(np.nanmedian(prof[zs > az + 70]))
    # prega: mínimo local abaixo do ápice
    low = (zs < az - 25) & (zs > az - 150)
    if not low.any():
        return None
    fold_i = np.where(low)[0][np.nanargmin(prof[low])]
    fz, fy = float(zs[fold_i]), float(prof[fold_i])
    prom = ay - fy
    if prom < 12:      # sem mama discernível (parede)
        return {"apex": (ax, az, round(ay, 1)), "prominence": round(float(prom), 1),
                "note": "sem mama discernível"}
    # L_sub: primeiro z acima do ápice com y <= wall_up + 0.15·prom
    thr = wall_up + 0.15 * prom
    up = zs > az
    L_up = float("nan")
    for i in np.where(up)[0][::-1]:          # do topo para baixo
        if prof[i] >= thr:
            L_up = float(zs[i] - az)
            break
    L_dn = az - fz
    d2 = np.abs(np.diff(prof, 2)) * 1e0       # por (2mm)²
    fold_zone = (zs[1:-1] > fz - 24) & (zs[1:-1] < fz + 24)
    up_zone = (zs[1:-1] > az + L_up * 0.3) & (zs[1:-1] < az + L_up * 0.9)
    sharp_fold = float(np.nanmax(d2[fold_zone])) if fold_zone.any() else float("nan")
    sharp_up = float(np.nanmax(d2[up_zone])) if up_zone.any() else float("nan")

    # ---- 3. secção horizontal y(x) no z do ápice
    xs = np.arange(0, 131, 2.0)
    sect = np.array([ymax(V, x0=float(x), z0=az, x_win=2.0, z_win=8.0) for x in xs])
    sternum = float(np.nanmedian(sect[xs < 8]))
    wall_lat = float(np.nanmedian(sect[xs > 105]))
    half_m = sternum + 0.5 * (ay - sternum)
    half_l = wall_lat + 0.5 * (ay - wall_lat)
    x_med = float("nan")
    for i in range(len(xs)):
        if sect[i] >= half_m:
            x_med = float(xs[i]); break
    x_lat = float("nan")
    for i in range(len(xs) - 1, -1, -1):
        if sect[i] >= half_l:
            x_lat = float(xs[i]); break

    return {
        "apex": (round(ax, 1), round(az, 1), round(ay, 1)),
        "x_apex_frac": round(ax / 1700.0, 4), "z_apex_frac": round(az / 1700.0, 4),
        "prominence": round(float(prom), 1),
        "L_up": round(L_up, 1), "L_down": round(L_dn, 1),
        "ratio_up_down": round(L_up / max(1e-9, L_dn), 2),
        "slope_up": round(prom / max(1e-9, L_up), 2),
        "slope_down": round(prom / max(1e-9, L_dn), 2),
        "fold_z_frac": round(fz / 1700.0, 4),
        "fold_sharp": round(sharp_fold, 2), "upper_sharp": round(sharp_up, 2),
        "sternum_gap": round(ay - sternum, 1),
        "x_medial": x_med, "x_lateral": x_lat,
        "base_width": round(x_lat - x_med, 1) if x_lat == x_lat and x_med == x_med else float("nan"),
        "base_over_prom": round((x_lat - x_med) / max(1e-9, prom), 2)
        if x_lat == x_lat and x_med == x_med else float("nan"),
    }


def main():
    out = {}
    print(f"{'modelo':12s} {'x_áp':>6} {'z_áp':>6} {'prom':>6} {'L_sub':>6} {'L_desc':>6} "
          f"{'rácio':>6} {'decl_desc':>9} {'prega|y″|':>9} {'base':>6} {'base/prom':>9}")
    for name, flip in MODELS:
        try:
            r = analyse(load(name, flip)[0])
        except Exception as e:
            print(f"{name:12s} ERRO {e!r}")
            continue
        out[name] = r
        if r is None or "note" in r:
            print(f"{name:12s} {r}")
            continue
        print(f"{name:12s} {r['apex'][0]:6.1f} {r['apex'][1]:6.1f} {r['prominence']:6.1f} "
              f"{r['L_up']:6.1f} {r['L_down']:6.1f} {r['ratio_up_down']:6.2f} "
              f"{r['slope_down']:9.2f} {r['fold_sharp']:9.1f} {r['base_width']:6.1f} "
              f"{r['base_over_prom']:9.2f}")
    json.dump(out, open(os.path.join(WORK, "breast_geometry.json"), "w"), indent=1)
    print("→", os.path.join(WORK, "breast_geometry.json"))


if __name__ == "__main__":
    main()
