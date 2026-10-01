# -*- coding: utf-8 -*-
"""Especificação da mama por CURVAS RASTERIZADAS (plane_scan v3.2).

MANDATO RND · docs/BREAST_C2_01.md.  Substitui o extractor v1 (janelas de
vértices — mentem entre malhas, ver memória/MECHANISM_AUDIT) e a tabela v2
(fill com bug de encadeamento).  Todas as medidas vêm de section_top /
section_top_plane (binning directo + reparo por contexto).

Métricas (frame normalizado 1700, y centrado min/max do corpo):
  barriga   = frente(x∈[−15,15]) @ z=1090  −  frente idem @ z do esterno
  ápice     = (x, y, z) do máx da frente em x∈[20,110], z∈[1150,1310]
  planalto  = gama x com secção @z_ápice ≥ máx−2
  esterno   = mediana da secção @z_ápice para x∈[0,8]
  gap       = y_ápice − esterno
  base      = x_lateral − x_medial a meia-altura (secção @z_ápice)
  f1350     = frente(x∈[−15,15]) @ z=1350

Uso: python3 tools/refstudy/breast_spec.py   → tabela + breast_spec_v3.json
"""
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from plane_scan import load, section_top, section_top_plane  # noqa: E402

MODELS = [
    ("real005", True), ("femalebase", False), ("femalechar", True),
    ("animeF", True), ("swN0", False), ("swV0", False), ("swB2", False),
]


def front_at(V, T, z, x0=0.0, xw=15.0):
    xb, y = section_top(V, T, float(z), x0 - xw, x0 + xw)
    if xb is None or not len(xb):
        return float("nan")
    sel = np.abs(xb - x0) <= xw
    return float(np.nanmedian(y[sel])) if sel.any() else float("nan")


def analyse(V, T):
    # ---- ápice: máx da secção frontal em x 20–110, z 1150–1310
    best = (None, -1e9)
    for z in range(1150, 1311, 5):
        xb, y = section_top(V, T, float(z), 20.0, 110.0)
        if xb is None or not len(xb):
            continue
        i = int(np.nanargmax(y))
        if y[i] > best[1]:
            best = ((float(xb[i]), float(y[i]), float(z)), float(y[i]))
    if best[0] is None:
        return None
    ax, ay, az = best[0]
    # refinamento em z (passo do instrumento = 2 mm)
    for z in np.arange(az - 5, az + 5.1, 2.0):
        xb, y = section_top(V, T, float(z), 20.0, 110.0)
        if xb is None or not len(xb):
            continue
        i = int(np.nanargmax(y))
        if y[i] > ay:
            ax, ay, az = float(xb[i]), float(y[i]), float(z)

    # ---- secção horizontal no z do ápice
    xb, y = section_top(V, T, az, 0.0, 140.0)
    sternum = float(np.nanmedian(y[np.abs(xb) <= 8.0]))
    plat = xb[y >= ay - 2.0]
    plateau = (float(plat.min()), float(plat.max())) if len(plat) else (float("nan"),) * 2
    half = sternum + 0.5 * (ay - sternum)
    im = np.where(y >= half)[0]
    x_med = float(xb[im[0]]) if len(im) else float("nan")
    il = np.where(y >= half)[0]
    x_lat = float(xb[il[-1]]) if len(il) else float("nan")

    # ---- sagital no x do ápice (prega)
    zb, sy = section_top_plane(V, T, ax, az - 170.0, az + 170.0)
    low = (zb < az - 25) & (zb > az - 150)
    fold = float(sy[low].min()) if low.any() else float("nan")

    belly = front_at(V, T, 1090.0)
    return {
        "apex": (round(ax, 1), round(ay, 1), round(az, 1)),
        "barriga_peito": round(belly - sternum, 1),
        "esterno": round(sternum, 1),
        "gap": round(ay - sternum, 1),
        "plateau": [round(plateau[0], 1), round(plateau[1], 1)],
        "base": round(x_lat - x_med, 1) if x_lat == x_lat and x_med == x_med else float("nan"),
        "fold_prom": round(ay - fold, 1) if fold == fold else float("nan"),
        "f1350": round(front_at(V, T, 1350.0), 1),
    }


def main():
    out = {}
    hdr = (f"{'modelo':12s} {'ápice(x,y,z)':>20s} {'barr−peito':>10s} {'esterno':>8s} "
           f"{'gap':>6s} {'planalto':>13s} {'base':>6s} {'prega':>6s} {'f1350':>6s}")
    print(hdr)
    for name, flip in MODELS:
        V, T = load(name, flip)
        r = analyse(V, T)
        out[name] = r
        a = r["apex"]
        print(f"{name:12s} ({a[0]:5.1f},{a[1]:5.1f},{a[2]:5.0f}) {r['barriga_peito']:>10.1f} "
              f"{r['esterno']:>8.1f} {r['gap']:>6.1f} [{r['plateau'][0]:5.1f},{r['plateau'][1]:5.1f}] "
              f"{r['base']:>6.1f} {r['fold_prom']:>6.1f} {r['f1350']:>6.1f}")
    p = os.path.join(os.path.dirname(HERE), "..", "out", "refstudy", "breast_spec_v3.json")
    p = os.path.abspath(p)
    json.dump(out, open(p, "w"), indent=1)
    print("→", p)


if __name__ == "__main__":
    main()
