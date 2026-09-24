"""REF STUDY 02 — topologia das CAGES (antes da Subdivision): densidade, poles,
orientação das arestas, figuras de edge flow (pintor por profundidade).

Uso: HCG_REFSTUDY_WORK=out/rs2 python tools/refstudy2/topology.py [OUT_DIR]
"""
import json, os, sys
from collections import defaultdict
import numpy as np
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
WORK = os.environ.get("HCG_REFSTUDY_WORK", "out/rs2")
OUT = sys.argv[1] if len(sys.argv) > 1 else "docs/ref_study_02"
S = 1700.0
BODY = {"ours": {}, "femalebase": {}, "bodytopo": {"cfg": "cfg_bodytopo.json"}, "femalechar": {"flip_y": True}}
BANDS = [("pernas", 0.0, 0.47), ("pelve", 0.47, 0.60), ("abdómen/cintura", 0.60, 0.70), ("tórax", 0.70, 0.80),
         ("pescoço/ombro", 0.80, 0.87), ("cabeça", 0.87, 1.01)]


def load(name, opt):
    d = np.load(os.path.join(WORK, f"cage_{name}.npz"))
    V, Fl, Fn = d["V"].copy(), d["F"], d["Fn"]
    faces, i = [], 0
    for n in Fn:
        faces.append(Fl[i:i + n]); i += n
    if opt is None:
        return V, faces
    cfg = json.load(open(os.path.join(WORK, opt["cfg"]))) if "cfg" in opt else {}
    zmin, zmax = V[:, 2].min(), V[:, 2].max()
    Sx = cfg.get("stature_override", zmax - zmin); floor = cfg.get("floor_override", zmin)
    V[:, 2] -= floor; V[:, 0] -= (V[:, 0].max() + V[:, 0].min()) / 2; V *= S / Sx
    if opt.get("flip_y", cfg.get("flip_y", False)):
        V[:, 1] *= -1
    V[:, 1] -= (V[:, 1].max() + V[:, 1].min()) / 2
    return V, faces


def stats(V, faces):
    edges = defaultdict(int)
    for f in faces:
        for a, b in zip(f, np.roll(f, -1)):
            edges[(min(a, b), max(a, b))] += 1
    val = np.zeros(len(V), int); bnd = np.zeros(len(V), bool)
    for (a, b), c in edges.items():
        val[a] += 1; val[b] += 1
        if c == 1: bnd[a] = bnd[b] = True
    E = np.array(list(edges.keys()))
    return val, bnd, E


def face_area_normal(V, f):
    p = V[f]; n = np.zeros(3)
    for i in range(len(f)):
        a, b = p[i], p[(i + 1) % len(f)]
        n += np.array([(a[1] - b[1]) * (a[2] + b[2]), (a[2] - b[2]) * (a[0] + b[0]), (a[0] - b[0]) * (a[1] + b[1])])
    ar = np.linalg.norm(n) / 2
    return ar, (n / (2 * ar) if ar > 0 else n)


def analyse(name, opt):
    V, faces = load(name, opt)
    val, bnd, E = stats(V, faces)
    AN = [face_area_normal(V, f) for f in faces]
    fz = np.array([V[f][:, 2].mean() for f in faces]); fa = np.array([a for a, _ in AN])
    rows = []
    for lab, lo, hi in BANDS:
        mf = (fz >= lo * S) & (fz < hi * S)
        mv = (V[:, 2] >= lo * S) & (V[:, 2] < hi * S) & ~bnd
        ez = V[E].mean(1)[:, 2]; me = (ez >= lo * S) & (ez < hi * S)
        L = np.linalg.norm(V[E[me, 0]] - V[E[me, 1]], axis=1)
        rows.append(dict(band=lab, faces=int(mf.sum()), area_dm2=float(fa[mf].sum() / 1e4),
                         faces_per_dm2=float(mf.sum() / max(1e-9, fa[mf].sum() / 1e4)),
                         edge_med_mm=float(np.median(L)) if len(L) else np.nan,
                         poles3=int(((val == 3) & mv).sum()), poles5p=int(((val >= 5) & mv).sum())))
    # orientação das arestas no tronco (|x| < 0.10·S para evitar braços em T/A)
    c = V[E].mean(1); m = (c[:, 2] > 0.50 * S) & (c[:, 2] < 0.78 * S) & (np.abs(c[:, 0]) < 0.10 * S)
    d = V[E[m, 1]] - V[E[m, 0]]; d /= np.linalg.norm(d, axis=1)[:, None] + 1e-12
    ang = np.degrees(np.arccos(np.clip(np.abs(d[:, 2]), 0, 1)))   # 0 = vertical, 90 = horizontal
    orient = dict(horizontal=float((ang > 70).mean()), vertical=float((ang < 20).mean()),
                  diagonal=float(((ang >= 20) & (ang <= 70)).mean()), n=int(m.sum()))
    return V, faces, val, bnd, AN, rows, orient


def draw(ax, V, faces, val, bnd, AN, view, zlim):
    # view: "front" (olhar de +y para -y), "back", "side" (de +x)
    axes = {"front": (0, 2, 1, 1), "back": (0, 2, 1, -1), "side": (1, 2, 0, 1)}[view]
    u, w, dcol, sgn = axes
    polys, cols, depth = [], [], []
    for f, (ar, n) in zip(faces, AN):
        zc = V[f][:, 2].mean()
        if not (zlim[0] <= zc <= zlim[1]): continue
        vd = n[dcol] * sgn
        if vd <= 0: continue
        P = V[f][:, [u, w]].copy()
        if view == "back": P[:, 0] *= -1
        polys.append(P); depth.append(V[f][:, dcol].mean() * sgn); cols.append(0.35 + 0.6 * vd)
    o = np.argsort(depth)
    pc = PolyCollection([polys[i] for i in o], facecolors=[(cols[i],) * 3 for i in o],
                        edgecolors=(0.1, 0.1, 0.1, 0.55), linewidths=0.25)
    ax.add_collection(pc)
    # poles visíveis (vértices de faces visíveis) — aproximação: vértices com normal média virada à câmara
    for vv, col in ((3, "#1f77ff"), (5, "#ff2a2a")):
        sel = np.nonzero(((val == vv) if vv == 3 else (val >= 5)) & ~bnd & (V[:, 2] >= zlim[0]) & (V[:, 2] <= zlim[1]))[0]
        if len(sel) == 0: continue
        P = V[sel][:, [u, w]].copy()
        facing = V[sel][:, dcol] * sgn > np.median(V[:, dcol] * sgn)
        if view == "back": P[:, 0] *= -1
        ax.plot(P[facing, 0], P[facing, 1], ".", color=col, ms=3.2)
    ax.set_aspect("equal"); ax.autoscale_view(); ax.axis("off")


if __name__ == "__main__":
    res = {}
    fig, axs = plt.subplots(len(BODY), 3, figsize=(15, 6.2 * len(BODY)))
    for i, (n, opt) in enumerate(BODY.items()):
        V, faces, val, bnd, AN, rows, orient = analyse(n, opt)
        res[n] = dict(bands=rows, torso_edge_orientation=orient,
                      valence_hist={int(k): int(v) for k, v in zip(*np.unique(val[~bnd], return_counts=True))})
        for j, view in enumerate(("front", "side", "back")):
            draw(axs[i, j], V, faces, val, bnd, AN, view, (0.44 * S, 0.93 * S))
            axs[i, j].set_title(f"{n} · {view} (cage, sem Subdivision) · azul = pole 3, vermelho = pole 5+", fontsize=9)
    plt.tight_layout(); plt.savefig(os.path.join(OUT, "fig_topology_torso.png"), dpi=62)
    for n in ("makehuman", "whitewalker"):
        V, faces = load(n, None); val, bnd, E = stats(V, faces)
        res[n] = dict(valence_hist={int(k): int(v) for k, v in zip(*np.unique(val[~bnd], return_counts=True))},
                      faces=len(faces))
    json.dump(res, open(os.path.join(WORK, "topology.json"), "w"), indent=1)
    for n in BODY:
        print(f"\n{n}: orientação das arestas no tronco {res[n]['torso_edge_orientation']}")
        for r in res[n]["bands"]:
            print(f"   {r['band']:16s} faces={r['faces']:5d} área={r['area_dm2']:6.1f} dm² densidade={r['faces_per_dm2']:6.1f}/dm² aresta_med={r['edge_med_mm']:5.1f} mm poles3={r['poles3']:4d} poles5+={r['poles5p']:4d}")
