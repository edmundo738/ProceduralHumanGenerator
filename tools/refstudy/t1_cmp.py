# -*- coding: utf-8 -*-
"""T1 — comparação amp0 vs amp1 contra as bandas pré-registadas (§4/§7).

Lê ``prof_amp0.json``/``prof_amp1.json`` (measure.py) e reporta as três bandas
congeladas no pré-registo T1 + guardas de larguras/circunferências.  As
fórmulas são as MESMAS do metrics.py (instrumento comum; duplicadas aqui para
não obrigar o ANSUR CSV no A/B).
"""
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _paths import WORK  # noqa: E402

import numpy as np  # noqa: E402


def prof(name):
    return json.load(open(os.path.join(WORK, f"prof_{name}.json")))


def metrics(name):
    r = prof(name)
    P = r["prof"]
    S = 1700.0
    C = [p for p in P if p["center"]]
    m = {}
    m["crotchheight"] = max(p["z"] for p in P if not p["center"] and p["z"] < 0.62 * S)
    ch = max((p for p in C if 0.68 * S <= p["z"] <= 0.78 * S), key=lambda p: p["depth"])
    m["chest_z"], m["chestdepth"], m["chestbreadth"], m["chestcircumference"] = (
        ch["z"], ch["depth"], ch["width"], ch["circ"])
    om = min(C, key=lambda p: abs(p["z"] - 0.6017 * S))
    m["waistbreadth"], m["waistcircumference"] = om["width"], om["circ"]
    lo = m["crotchheight"] / S + 0.005
    m["hipbreadth"] = max(p["width"] for p in C if lo * S <= p["z"] <= 0.58 * S)
    m["buttockcircumference"] = max(p["circ"] for p in C if lo * S <= p["z"] <= 0.58 * S)
    nk = min((p for p in C if 0.80 * S <= p["z"] <= 0.875 * S), key=lambda p: p["width"])
    m["neckcircumference"] = nk["circ"]
    # curva sagital (linha média |x|<=10)
    B = [(p["z"], p["mid_back"], p["mid_front"]) for p in C
         if not math.isnan(p.get("mid_back", float("nan")))]
    B = np.array(B)

    def ap(lo_, hi_, col=1, f=np.argmin):
        s = B[(B[:, 0] >= lo_ * S) & (B[:, 0] <= hi_ * S)]
        i = f(s[:, col])
        return s[i]

    t = ap(0.70, 0.82)
    b = ap(lo, 0.58)
    seg = B[(B[:, 0] < t[0]) & (B[:, 0] > b[0])]
    yline = b[1] + (seg[:, 0] - b[0]) / (t[0] - b[0]) * (t[1] - b[1])
    k = int(np.argmax(seg[:, 1] - yline))
    m["lumbar_concavity"] = float((seg[:, 1] - yline)[k])
    m["lumbar_z"] = float(seg[k, 0])
    m["buttock_behind_thoracic"] = float(t[1] - b[1])
    m["thoracic_apex_z"], m["buttock_apex_z"] = float(t[0]), float(b[0])
    N = [p for p in C if 1330 <= p["z"] <= 1640
         and not math.isnan(p.get("mid_back", float("nan")))]
    zN = np.array([p["z"] for p in N])
    bN = np.array([p["mid_back"] for p in N])
    hi = zN > 1520
    zo = zN[hi][np.argmin(bN[hi])]
    bo = bN[hi].min()
    mid = (zN > 1380) & (zN < zo)
    zn = zN[mid][np.argmax(bN[mid])]
    lo_ = zN < zn
    bs = bN[lo_].min()
    m["upper_back_vs_occiput"] = float(bs - bo)
    m["upper_back_z"] = float(zN[lo_][np.argmin(bN[lo_])])
    m["occiput_z"] = float(zo)
    # perfil sagital bs em cotas fixas (controlo visual §7)
    m["bs@920"] = float(min(p["mid_back"] for p in C if abs(p["z"] - 920) <= 5
                            if not math.isnan(p.get("mid_back", float("nan")))))
    m["bs@1100"] = float(min(p["mid_back"] for p in C if abs(p["z"] - 1100) <= 5
                             if not math.isnan(p.get("mid_back", float("nan")))))
    m["bs@1360"] = float(min(p["mid_back"] for p in C if abs(p["z"] - 1360) <= 5
                             if not math.isnan(p.get("mid_back", float("nan")))))
    return m


BANDS = {  # pré-registo T1 (§4): [lo, hi] @1700 mm
    "lumbar_concavity": (40, 75),
    "buttock_behind_thoracic": (-25, -2),
    "upper_back_vs_occiput": (-30, -8),
}

if __name__ == "__main__":
    m0, m1 = metrics("amp0"), metrics("amp1")
    keys = ["lumbar_concavity", "buttock_behind_thoracic", "upper_back_vs_occiput",
            "chestbreadth", "waistbreadth", "hipbreadth", "chestcircumference",
            "waistcircumference", "buttockcircumference", "neckcircumference",
            "crotchheight", "lumbar_z", "thoracic_apex_z", "buttock_apex_z",
            "upper_back_z", "occiput_z", "bs@920", "bs@1100", "bs@1360"]
    print(f"{'métrica @1700mm':30s} {'amp0':>9s} {'amp1':>9s} {'Δ':>8s}  banda")
    for k in keys:
        d = m1[k] - m0[k]
        band = ""
        if k in BANDS:
            lo, hi = BANDS[k]
            ok = lo <= m1[k] <= hi
            band = f"[{lo},{hi}] {'✓' if ok else '✗'}"
        elif "breadth" in k:
            band = "Δ0.0 ✓" if abs(d) < 0.51 else f"Δ{d:+.1f} ✗"
        print(f"{k:30s} {m0[k]:9.1f} {m1[k]:9.1f} {d:+8.1f}  {band}")
