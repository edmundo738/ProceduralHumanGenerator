# -*- coding: utf-8 -*-
"""TORSO B — comparação novo vs antes vs bandas das refs (TORSO_STUDY_02)."""
import json, math, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _paths import WORK
import numpy as np

REFS = {"femalebase", "femalechar", "bodytopo", "real005", "ff11", "animeF"}

def load(n):
    return json.load(open(os.path.join(WORK, f"prof_{n}.json")))["prof"]

def metrics(P):
    S = 1700.0
    C = [p for p in P if p["center"] and not math.isnan(p.get("mid_back", float("nan")))]
    cr = max(p["z"] for p in P if not p["center"] and p["z"] < 0.62*S)
    lo = cr/S + 0.005
    m = {}
    B = np.array([(p["z"], p["mid_back"]) for p in C])
    s = B[(B[:,0]>=0.70*S)&(B[:,0]<=0.82*S)]; t = s[np.argmin(s[:,1])] if len(s) else (float('nan'),)*2
    s = B[(B[:,0]>=lo*S)&(B[:,0]<=0.58*S)]; b = s[np.argmin(s[:,1])] if len(s) else (float('nan'),)*2
    seg = B[(B[:,0]<t[0])&(B[:,0]>b[0])]
    if len(seg) > 3:
        yl = b[1]+(seg[:,0]-b[0])/(t[0]-b[0])*(t[1]-b[1])
        m["P1_lombar"] = float(np.max(seg[:,1]-yl))
    m["P2_nadega_toracica"] = float(t[1]-b[1])
    m["P3_apice_toracico_z"] = float(t[0])
    F = np.array([(p["z"], p["front"]) for p in C])
    band = F[(F[:,0]>=0.70*S)&(F[:,0]<=0.79*S)]
    if len(band):
        i = np.argmax(band[:,1])
        ub = min(C, key=lambda r: abs(r["z"]-0.795*S))
        m["P4_mama_z"] = float(band[i,0]); m["P5_saliencia"] = float(band[i,1]-ub["front"])
    ch = max((p for p in C if 0.68*S<=p["z"]<=0.78*S), key=lambda p: p["width"])
    wn = min((p for p in C if 0.58*S<=p["z"]<=0.70*S), key=lambda p: p["width"])
    hb = max((p for p in C if lo*S<=p["z"]<=0.58*S), key=lambda p: p["width"])
    bd = max((p for p in C if lo*S<=p["z"]<=0.58*S), key=lambda p: p["depth"])
    m["P7_cintura_anca"] = wn["width"]/hb["width"]
    m["P8_peito_anca"] = ch["width"]/hb["width"]
    m["P9_larg_peito"] = ch["width"]
    m["P10_prof_peito"] = max(p["depth"] for p in C if 0.68*S<=p["z"]<=0.78*S)
    m["P11_prof_nadega"] = bd["depth"]
    m["P12_niveis"] = f"{wn['z']/S:.2f}/{hb['z']/S:.2f}"
    return m

def sections(P, frac):
    S = 1700.0
    C = [p for p in P if p["center"]]
    r = min(C, key=lambda q: abs(q["z"]-frac*S))
    # secção do próprio perfil: usa width/depth + front/back para share
    return r

new = metrics(load("ours")); old = metrics(load("ours_prev")) if os.path.exists(os.path.join(WORK, "prof_ours_prev.json")) else {}
BANDS = {"P1_lombar": (53.7, 69.7), "P2_nadega_toracica": (-20, -8),
         "P3_apice_toracico_z": (1280, 1335), "P4_mama_z": (1190, 1260),
         "P5_saliencia": (54, 70), "P7_cintura_anca": (0.63, 0.66),
         "P8_peito_anca": (0.78, 0.96), "P9_larg_peito": (252, 316),
         "P10_prof_peito": (218, 236), "P11_prof_nadega": (198, 232)}
print(f"{'padrão':24s} {'antes':>9s} {'NOVO':>9s}  banda refs")
for k, (lo, hi) in BANDS.items():
    v0, v1 = old.get(k), new.get(k)
    ok = "✓" if v1 is not None and lo <= v1 <= hi else "✗"
    print(f"{k:24s} {v0 if v0 is not None else float('nan'):9.1f} {v1:9.1f}  [{lo},{hi}] {ok}")
print(f"{'P12_niveis':24s} {old.get('P12_niveis','-'):>9s} {new['P12_niveis']:>9s}  [0.61-0.70/0.46-0.58]")
# alvo it6 (registado no CHECKPOINT TORSO B) para diagnóstico da reconstrução
TARGET = {"P1_lombar": 54.3, "P2_nadega_toracica": -8.0, "P3_apice_toracico_z": 1310,
          "P4_mama_z": 1230, "P5_saliencia": 64, "P7_cintura_anca": 0.63,
          "P8_peito_anca": 0.80, "P9_larg_peito": 312, "P10_prof_peito": 242,
          "P11_prof_nadega": 202}
print("\nvs ALVO it6 (reconstrução):")
for k, tv in TARGET.items():
    v = new.get(k)
    d = (v - tv) if v is not None else float("nan")
    flag = "OK" if abs(d) < 3 else ("~" if abs(d) < 8 else "DIFF")
    print(f"  {k:24s} alvo={tv:7.1f} agora={v:7.1f} Δ={d:+6.1f} {flag}")
