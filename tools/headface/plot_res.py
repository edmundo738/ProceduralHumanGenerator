import os, sys, json
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from face_target import OUT, CENTRE

def show(D, U, out, title, vmax=15, fitted=None):
    X, Y, Z = 100 * U[..., 0], 100 * U[..., 1], 100 * U[..., 2]
    n = 2 if fitted is None else 3
    fig, ax = plt.subplots(2, n, figsize=(6 * n, 11))
    ax = np.atleast_2d(ax)
    L = json.load(open(os.path.join(OUT, "face_landmarks.json")))["mean"]
    maps = [D] if fitted is None else [D, fitted, D - fitted]
    names = ["alvo − casca"] if fitted is None else ["alvo − casca", "campos", "resíduo"]
    for j, (M, nm) in enumerate(zip(maps, names)):
        for i, (fr, m) in enumerate((("F", Y > 0), ("S", X > 20))):
            a = ax[i, j]
            h = X if fr == "F" else -Y
            MM = np.where(m, M, np.nan)
            a.pcolormesh(h, Z, np.ma.masked_invalid(MM), cmap="RdBu_r", vmin=-vmax, vmax=vmax, shading="nearest")
            a.set_aspect("equal"); a.set_title(f"{title} {nm} ({'frente X,Z' if fr=='F' else 'lado −Y,Z'})")
            a.grid(alpha=.3)
            if fr == "F":
                for k, p in L.items():
                    v = np.array(p) - CENTRE; u = 100 * v / np.linalg.norm(v)
                    a.plot(u[0], u[2], "k.", ms=3); a.text(u[0], u[2], k, fontsize=6)
                a.set_xlim(-80, 80); a.set_ylim(-95, 60)
            else:
                a.set_xlim(-100, 90); a.set_ylim(-95, 60)
    plt.tight_layout(); plt.savefig(out, dpi=70)

if __name__ == "__main__":
    d = np.load(os.path.join(OUT, "residual.npz"))
    show(d["mean"] - d["base"], d["U"], sys.argv[1], "")
