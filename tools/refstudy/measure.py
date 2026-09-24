"""Perfis por cortes horizontais: largura, profundidade, circunferência, perfil sagital.
Todas as malhas são reescaladas para estatura 1700 mm, chão em z=0, frente = +Y."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _paths import WORK  # noqa: E402
import json
import numpy as np, geom
from scipy import ndimage
from scipy.spatial import ConvexHull
RES = 2.0   # mm
MODELS = {  # name: dict(stature=None->min..max, drop=callable(comp bbox)->bool)
 "ours": {}, "femalebase": {}, "femalechar": {}, "bodytopo": {"no_feet": True},
}
def prep(name):
    d = np.load(WORK + f"/raw_{name}.npz"); V, T = d["V"].copy(), d["T"]
    lab = np.load(WORK + f"/lab_{name}.npy")
    return V, T, lab

def orient_scale(name, V, T, lab):
    zmin, zmax = V[:, 2].min(), V[:, 2].max()
    info = {}
    if name == "bodytopo":
        # sem pés: estatura estimada a partir de (topo - gancho) / 0.5198 (ANSUR: 1 - 0.4802)  [INFERRED]
        info["stature_method"] = "INFERRED (vertex-crotch)/0.5198, ANSUR"
    else:
        info["stature_method"] = "measured (max z - min z)"
    V = V.copy(); V[:, 0] -= (V[:, 0].max() + V[:, 0].min()) / 2
    return V, info, zmin, zmax

def center_mask_components(V, T, lab, drop_labels):
    keep = ~np.isin(lab, list(drop_labels))
    tri_keep = keep[T[:, 0]]
    return T[tri_keep], lab

def slice_grid(V, T, lab, z0, xr=(-320, 320), yr=(-260, 260)):
    nx, ny = int((xr[1]-xr[0])/RES), int((yr[1]-yr[0])/RES)
    g = np.zeros((ny, nx), bool)
    zt = V[T][:, :, 2]
    m = (zt.min(1) <= z0) & (zt.max(1) >= z0)
    if not m.any(): return g
    Tm = T[m]; labs = lab[Tm[:, 0]]
    for c in np.unique(labs):
        segs = geom.slice_segments(V, Tm[labs == c], z0)
        g |= geom.fill(segs, xr[0], yr[0], RES, nx, ny)
    return g

def analyse(name, drop_labels=(), flip_y=False, stature_override=None, floor_override=None):
    V, T, lab = prep(name)
    V = V.copy()
    zmin, zmax = V[:, 2].min(), V[:, 2].max()
    S = (zmax - zmin) if stature_override is None else stature_override
    floor = zmin if floor_override is None else floor_override
    V[:, 2] -= floor
    V[:, 0] -= (V[:, 0].max() + V[:, 0].min()) / 2
    V *= 1700.0 / S
    if flip_y: V[:, 1] *= -1
    keep = ~np.isin(lab, list(drop_labels)); T = T[keep[T[:, 0]]]
    # centre Y on body midline at mid-thigh-ish later; for now use bbox centre
    V[:, 1] -= (V[keep][:, 1].max() + V[keep][:, 1].min()) / 2
    xr, yr = (-320, 320), (-260, 260)
    x_axis = xr[0] + (np.arange(int((xr[1]-xr[0])/RES)) + .5) * RES
    y_axis = yr[0] + (np.arange(int((yr[1]-yr[0])/RES)) + .5) * RES
    prof = []
    top = V[keep][:, 2].max()
    for z0 in np.arange(5, top - 2, 5.0):
        g = slice_grid(V, T, lab, z0, xr, yr)
        L, n = ndimage.label(g)
        comps = []
        for k in range(1, n + 1):
            iy, ix = np.nonzero(L == k)
            if len(ix) < 4: continue
            xs, ys = x_axis[ix], y_axis[iy]
            comps.append(dict(xmin=xs.min(), xmax=xs.max(), ymin=ys.min(), ymax=ys.max(),
                              cx=xs.mean(), area=len(ix) * RES * RES, ix=ix, iy=iy))
        mid = [c for c in comps if c["xmin"] <= 0 <= c["xmax"]]
        row = dict(z=z0, n=len(comps), center=bool(mid))
        if mid:
            c = max(mid, key=lambda c: c["area"])
            xs, ys = x_axis[c["ix"]], y_axis[c["iy"]]
            pts = np.c_[xs, ys]
            try:
                h = ConvexHull(pts); per = h.area   # 2D: .area = perimeter
            except Exception: per = float("nan")
            mids = np.abs(xs) <= 10
            row.update(width=c["xmax"] - c["xmin"] + RES, depth=c["ymax"] - c["ymin"] + RES,
                       front=c["ymax"], back=c["ymin"], area=c["area"], circ=per,
                       mid_front=ys[mids].max() if mids.any() else np.nan,
                       mid_back=ys[mids].min() if mids.any() else np.nan)
        else:
            legs = [c for c in comps if c["area"] > 400]
            if legs:
                row["legs"] = [dict(cx=c["cx"], w=c["xmax"]-c["xmin"]+RES, d=c["ymax"]-c["ymin"]+RES) for c in legs]
        # full silhouette (all comps) extents
        if comps:
            row["sil_xmin"] = min(c["xmin"] for c in comps); row["sil_xmax"] = max(c["xmax"] for c in comps)
            row["sil_ymin"] = min(c["ymin"] for c in comps); row["sil_ymax"] = max(c["ymax"] for c in comps)
        prof.append(row)
    return dict(name=name, S_units=S, top=top, prof=prof)

if __name__ == "__main__":
    name = sys.argv[1]; cfg = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}
    r = analyse(name, **cfg)
    json.dump(r, open(WORK + f"/prof_{name}.json", "w"), default=float)
    print(name, "slices", len(r["prof"]), "S_units", r["S_units"])
