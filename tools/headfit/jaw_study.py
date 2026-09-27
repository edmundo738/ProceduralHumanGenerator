"""A3 — estudo da mandíbula lateral (plano lateral + ângulo) nas refs vs A2b.

Referencial HEAD STUDY 01 (mm@H226, z = 0 mentón 45°, y = 0 centro g–op).
* Mapa lateral X(y, z): |x| máximo da superfície (amostragem densa) por célula
  de 2 mm — é o que se vê de lado; a mandíbula aparece como um degrau de X no
  bordo inferior (face → submento/pescoço).
* Cortes horizontais (contorno exterior) em z = 5…55.
Saída: docs/head_phaseA/jaw_study.png + out/headfit/jaw_maps.npz
"""
import os
import sys
import numpy as np

HERE = os.path.dirname(__file__)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "headstudy"))
import target as TG   # noqa: E402
import common as C    # noqa: E402

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt   # noqa: E402

YS = np.arange(-60, 102, 2.0)
ZS = np.arange(-40, 92, 2.0)
NAMES = ["femalebase", "bodytopo", "femalechar", "makehuman", "oursA2"]
DOC = os.path.join(HERE, "..", "..", "docs", "head_phaseA")


def lateral_map(P):
    X = np.full((len(ZS), len(YS)), np.nan)
    iy = np.floor((P[:, 1] - YS[0]) / 2.0 + 0.5).astype(int)
    iz = np.floor((P[:, 2] - ZS[0]) / 2.0 + 0.5).astype(int)
    ok = (iy >= 0) & (iy < len(YS)) & (iz >= 0) & (iz < len(ZS))
    ax = np.abs(P[:, 0])
    for a, b, v in zip(iz[ok], iy[ok], ax[ok]):
        if not (X[a, b] >= v):
            X[a, b] = v
    return X


def main():
    maps, secs = {}, {}
    for nm in NAMES:
        Vn, T, fs, fi, info = C.normalise(nm)
        P = TG.surface_samples(Vn, T, per_mm2=1.5)
        P = P[np.abs(P[:, 0]) < 0.40 * C.H_MM]
        maps[nm] = lateral_map(P)
        secs[nm] = {z: P[np.abs(P[:, 2] - z) < 0.7][:, :2] for z in (5, 15, 25, 35, 45, 55)}
    np.savez(os.path.join(TG.OUT, "jaw_maps.npz"), YS=YS, ZS=ZS, **maps)
    fig, ax = plt.subplots(2, len(NAMES), figsize=(4.2 * len(NAMES), 9.5))
    for c, nm in enumerate(NAMES):
        a = ax[0, c]
        im = a.imshow(maps[nm], origin="lower", extent=(YS[0], YS[-1], ZS[0], ZS[-1]), cmap="viridis",
                      vmin=20, vmax=80)
        a.contour(YS, ZS, np.nan_to_num(maps[nm]), levels=np.arange(20, 81, 5), colors="w", linewidths=0.4)
        a.set_title(f"{nm}: |x| máx (vista lateral)")
        a.set_xlabel("y (frente →)"); a.axhline(0, color="r", lw=0.5)
        b = ax[1, c]
        for z, col in zip((5, 15, 25, 35, 45, 55), plt.cm.plasma(np.linspace(0, 0.9, 6))):
            S = secs[nm][z]
            b.plot(S[:, 0], S[:, 1], ".", ms=0.3, color=col)
            b.plot([], [], color=col, label=f"z {z}")
        b.set_aspect("equal"); b.set_xlim(-85, 85); b.set_ylim(-70, 110); b.grid(alpha=0.3)
        b.set_title(f"{nm}: cortes horizontais"); b.legend(fontsize=7, markerscale=10)
    fig.colorbar(im, ax=ax[0, :].tolist(), shrink=0.6)
    fig.savefig(os.path.join(DOC, "jaw_study.png"), dpi=70)


if __name__ == "__main__":
    main()
