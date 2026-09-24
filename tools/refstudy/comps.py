"""Passo 2: componentes conexos por vértice + lista de cascas a excluir no BUILD (braços/mãos/dedos)."""
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, geom
from _paths import WORK
for n in ["ours", "bodytopo", "femalebase", "femalechar"]:
    d = np.load(f"{WORK}/raw_{n}.npz"); V, T = d["V"], d["T"]
    lab = geom.components(V, T); np.save(f"{WORK}/lab_{n}.npy", lab)
    print(n, "components", lab.max() + 1)
d = np.load(f"{WORK}/raw_ours.npz"); V = d["V"]; lab = np.load(f"{WORK}/lab_ours.npy")
drop = [int(c) for c in range(lab.max() + 1)
        if np.abs(V[lab == c][:, 0]).min() > 0.07 and V[lab == c][:, 2].min() > 0.6 and V[lab == c][:, 2].max() < 1.45]
json.dump(drop, open(f"{WORK}/drop_ours.json", "w")); print("ours: drop", len(drop), "arm/hand/finger shells")
