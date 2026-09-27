"""A3 — cortes coronais (y = const) do terço inferior: refs vs A2b (cabeça e corpo separados).
Saída: docs/head_phaseA/jaw_coronal.png"""
import os, sys
import numpy as np
HERE = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(HERE, "..", "..")); sys.path.insert(0, os.path.join(HERE, "..", "headstudy"))
import common as C   # noqa: E402
geom = C.geom
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt   # noqa: E402

YS = (-10, 5, 20, 35, 50, 65)


def coronal(V, T, y):
    # slice_segments corta em z: roda (x, y, z) → (x, z, y)
    P = V[:, [0, 2, 1]]
    S = np.asarray(geom.slice_segments(P, T, y))
    return S.reshape(-1, 2, 2) if len(S) else np.zeros((0, 2, 2))


def ours_a2():
    os.environ["HCG_HEAD"] = "massA2"; os.environ["HCG_MATHUTILS"] = "0"
    from human_generator.pipeline.assemble import build_character
    from human_generator.core.integration import part_vertices
    b = build_character(preset="realistic_female", seed=42); B = b.builder
    head = part_vertices(B, "head.skull")
    V = np.array([[p.x, p.y, p.z] for p in B.verts]); T = []; th = []
    for f in B.faces:
        f = list(f); ish = all(i in head for i in f)
        for k in range(1, len(f) - 1):
            T.append((f[0], f[k], f[k + 1])); th.append(ish)
    T = np.array(T); th = np.array(th)
    H = 0.2198; zme = V[list(head), 2].max() - H; s = C.H_MM / H
    N = V.copy(); N[:, 2] = (V[:, 2] - zme) * s; N[:, 0] *= s; N[:, 1] *= s
    hh = N[list(head)]; up = hh[:, 2] > 0.55 * C.H_MM
    N[:, 1] -= 0.5 * (hh[up, 1].max() + hh[up, 1].min())
    return N, T[th], T[~th]


def main():
    refs = {n: C.normalise(n)[:2] for n in ("femalebase", "bodytopo", "femalechar")}
    N, Th, Tb = ours_a2()
    cols = {"femalebase": "#ff7f0e", "bodytopo": "#2ca02c", "femalechar": "#9467bd"}
    fig, ax = plt.subplots(1, len(YS), figsize=(3.3 * len(YS), 5.2))
    for a, y in zip(ax, YS):
        for n, (V, T) in refs.items():
            for s in coronal(V, T, y):
                a.plot(s[:, 0], s[:, 1], color=cols[n], lw=0.8)
        for s in coronal(N, Th, y):
            a.plot(s[:, 0], s[:, 1], "k-", lw=1.6)
        for s in coronal(N, Tb, y):
            a.plot(s[:, 0], s[:, 1], color="r", lw=1.0, ls="--")
        a.set_xlim(-80, 80); a.set_ylim(-40, 90); a.set_aspect("equal"); a.grid(alpha=0.3)
        a.axhline(0, color="gray", lw=0.5); a.set_title(f"corte coronal y = {y}")
    ax[0].plot([], [], "k-", label="A2b cabeça"); ax[0].plot([], [], "r--", label="nosso corpo/pescoço")
    for n, c in cols.items():
        ax[0].plot([], [], color=c, label=n)
    ax[0].legend(fontsize=7, loc="upper left")
    fig.suptitle("A3 estudo: terço inferior em cortes coronais (mm@H226, z=0 mentón)", fontsize=10)
    fig.tight_layout(); fig.savefig(os.path.join(HERE, "..", "..", "docs", "head_phaseA", "jaw_coronal.png"), dpi=75)


if __name__ == "__main__":
    main()
