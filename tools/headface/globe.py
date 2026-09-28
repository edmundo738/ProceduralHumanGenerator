"""Posição do globo ocular nas refs: esfera (raio livre e fixo 12.5) ajustada ao laço da margem palpebral."""
import os, sys, json
import numpy as np
from scipy.optimize import least_squares
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "headstudy"))
import common as C
from landmarks import boundary_loops
from face_target import REFS, OUT

res = {}
for n in REFS:
    Vn, T, *_ = C.normalise(n)
    for lp in boundary_loops(T):
        P = Vn[lp]; c = P.mean(0)
        if len(lp) < 8 or c[1] < 20 or not (85 < c[2] < 125) or c[0] < 15:
            continue
        f = lambda q: np.linalg.norm(P - q[:3], axis=1) - q[3]
        q0 = np.r_[c[0], c[1] - 10, c[2], 12.5]
        a = least_squares(f, q0).x
        g = lambda q: np.linalg.norm(P - np.r_[q[0], q[1], q[2]], axis=1) - 12.5
        b = least_squares(g, q0[:3]).x
        res[n] = {"free": a.round(2).tolist(), "R12.5": b.round(2).tolist(), "loop_c": c.round(2).tolist()}
        print(n, "livre", a.round(1), "| R=12.5", b.round(1), "| laço", c.round(1))
m = np.mean([res[n]["R12.5"] for n in res], 0)
print("média R12.5", m.round(2))
json.dump({"refs": res, "mean_R12.5": m.round(2).tolist()}, open(os.path.join(OUT, "globe.json"), "w"), indent=1)
