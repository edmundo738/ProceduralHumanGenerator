"""Body Topo não tem pés: estatura INFERRED = (topo - gancho) / 0.5198 (ANSUR: 1 - crotchheight/estatura)."""
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from _paths import WORK
r = json.load(open(f"{WORK}/prof_bodytopo.json")); P = r["prof"]
cz = max(p["z"] for p in P if not p["center"] and p["z"] < 0.75 * r["top"])
V = np.load(f"{WORK}/raw_bodytopo.npz")["V"]; zmin, zmax = V[:, 2].min(), V[:, 2].max()
crotch = zmin + cz / 1700 * (zmax - zmin); S = (zmax - crotch) / 0.5198
json.dump({"stature_override": S, "floor_override": zmax - S, "flip_y": True}, open(f"{WORK}/cfg_bodytopo.json", "w"))
print(f"bodytopo: S_est={S:.4f} u, faltam {((zmin-(zmax-S))/S*1700):.0f} mm abaixo da malha (pés)")
