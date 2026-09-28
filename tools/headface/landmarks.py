"""Marcos faciais automáticos nas refs normalizadas (mm@H226; z=0 mentón; y=0 centro g–op).

  * olhos / boca: laços de fronteira da pele (as refs têm a fenda palpebral aberta)
  * perfil sagital: pronasale, subnasale, lábios, stómio, násio, glabela
"""
import os, sys, json
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "headstudy"))
import common as C  # noqa
import figures as FG  # noqa

REFS = ["makehuman", "femalebase", "bodytopo", "femalechar"]


def boundary_loops(T):
    from collections import defaultdict
    cnt = defaultdict(int)
    for a, b, c in T:
        for e in ((a, b), (b, c), (c, a)):
            cnt[tuple(sorted(e))] += 1
    be = [e for e, k in cnt.items() if k == 1]
    adj = defaultdict(list)
    for a, b in be:
        adj[a].append(b); adj[b].append(a)
    seen, loops = set(), []
    for s in adj:
        if s in seen:
            continue
        comp, st = [], [s]
        while st:
            v = st.pop()
            if v in seen:
                continue
            seen.add(v); comp.append(v); st.extend(adj[v])
        loops.append(comp)
    return loops


def midline_profile(Vn, T, zs):
    """frente (y máx) na faixa |x| < 1.5 mm, por z."""
    sel = np.abs(Vn[:, 0]) < 1.5
    P = Vn[sel]
    out = []
    for z in zs:
        m = np.abs(P[:, 2] - z) < 0.6
        out.append(P[m, 1].max() if m.any() else np.nan)
    return np.array(out)


def find(name, verbose=True):
    Vn, T, fs, fi, info = C.normalise(name)
    loops = boundary_loops(T)
    res = {"loops": []}
    for lp in loops:
        P = Vn[lp]
        c = P.mean(0)
        if c[1] < 20 or c[2] < 0 or c[2] > 200 or len(lp) < 8:
            continue
        res["loops"].append({"n": len(lp), "c": c.round(1).tolist(), "xmin": float(P[:, 0].min()), "xmax": float(P[:, 0].max()),
                             "zmin": float(P[:, 2].min()), "zmax": float(P[:, 2].max()), "ymax": float(P[:, 1].max())})
    zs = np.arange(-5, 200, 0.5)
    yf = midline_profile(Vn, T, zs)
    res["profile"] = (zs.tolist(), yf.tolist())
    if verbose:
        print(name, info["scale"])
        for l in res["loops"]:
            print("  loop", l)
    return res


if __name__ == "__main__":
    for n in REFS:
        find(n)
