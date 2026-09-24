"""Figura: contornos das secções do tronco (4 malhas) por cota, centrados no centroide."""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "refstudy"))
import numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from _paths import WORK
OUT = sys.argv[1] if len(sys.argv) > 1 else "docs/ref_study_02"
C = {"ours": "#d62728", "femalebase": "#1f77b4", "femalechar": "#2ca02c", "bodytopo": "#9467bd"}
RES = 2.0; xr, yr = (-320, 320), (-260, 260)
xa = xr[0] + (np.arange(int((xr[1]-xr[0])/RES)) + .5) * RES
ya = yr[0] + (np.arange(int((yr[1]-yr[0])/RES)) + .5) * RES
M = {n: np.load(os.path.join(WORK, f"shape_{n}.npz")) for n in C}
levels = sorted(M["ours"].files, key=float, reverse=True)
BAD = {"femalebase": lambda f: f >= 0.74, "femalechar": lambda f: f >= 0.74,     # braços em T ligados
       "bodytopo": lambda f: 0.47 <= f <= 0.64}                                # mãos na anca
fig, ax = plt.subplots(3, 4, figsize=(16, 12.5))
for a, lv in zip(ax.flat, levels):
    f = float(lv)
    for n, c in C.items():
        if lv not in M[n].files: continue
        m = M[n][lv]; iy, ix = np.nonzero(m)
        cx, cy = xa[ix].mean(), ya[iy].mean()
        a.contour(xa - cx, ya - cy, m.astype(float), levels=[0.5], colors=[c],
                  linewidths=2.2 if n == "ours" else 1.4,
                  linestyles=":" if BAD.get(n, lambda f: False)(f) else "-")
    a.set_aspect("equal"); a.set_xlim(-230, 230); a.set_ylim(-170, 170); a.grid(alpha=.3)
    a.axhline(0, color="k", lw=.4); a.axvline(0, color="k", lw=.4)
    a.set_title(f"z = {f:.3f}·S ({f*1700:.0f} mm)", fontsize=10); a.text(-220, 150, "frente ↑", fontsize=8)
for n, c in C.items(): ax[0, 0].plot([], [], color=c, label=n)
ax[0, 0].plot([], [], color="gray", ls=":", label="contaminado (braços/mãos)")
ax[0, 0].legend(fontsize=8, loc="lower left")
fig.suptitle("REF STUDY 02 — secções horizontais do tronco centradas no centroide (@1700 mm; frente = +y)", fontsize=12)
plt.tight_layout(); plt.savefig(os.path.join(OUT, "fig_sections.png"), dpi=70)
print("ok")
