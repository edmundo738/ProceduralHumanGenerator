"""REF STUDY 02 — forma do tronco para além das medidas ANSUR (numpy; sem bpy).

Reaproveita a normalização do REF STUDY 01 (estatura 1700 mm, chão z = 0,
frente +Y, x centrado) e os cortes de 2 mm de ``tools/refstudy/measure.py``.
Para cada corte guarda a MÁSCARA do tronco (componente que contém x = 0) e
calcula descritores de forma que o REF STUDY 01 não tinha:

* centroide (cx, cy) e o eixo sagital de massa cy(z);
* extensão à frente / atrás do centroide (assimetria frente–costas);
* preenchimento = área / (largura·profundidade)  (elipse 0.785, retângulo 1.0);
* sulco posterior = costas na linha média − ponto mais posterior do corte
  (sulco da coluna / fenda interglútea) e a |x| desse ponto posterior;
* sulco anterior = frente máxima − frente na linha média (sulco intermamário).

Uso: HCG_REFSTUDY_WORK=out/rs2 python tools/refstudy2/shape.py
Saída: WORK/shape_<nome>.npz (máscaras de cortes selecionados) e WORK/shape.json
"""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "refstudy"))
import numpy as np
from scipy import ndimage
import measure                       # noqa: E402  (slice_grid, prep, RES)
from _paths import WORK              # noqa: E402

MODELS = {
    "ours": dict(drop="drop_ours.json"),
    "femalebase": dict(),
    "femalechar": dict(flip_y=True),
    "bodytopo": dict(cfg="cfg_bodytopo.json"),
}
LEVELS = [0.78, 0.74, 0.72, 0.69, 0.66, 0.635, 0.62, 0.60, 0.57, 0.545, 0.52, 0.50]
RES = measure.RES


def normalised(name, opt):
    V, T, lab = measure.prep(name)
    V = V.copy()
    cfg = {}
    if "cfg" in opt:
        cfg = json.load(open(os.path.join(WORK, opt["cfg"])))
    flip = opt.get("flip_y", cfg.get("flip_y", False))
    zmin, zmax = V[:, 2].min(), V[:, 2].max()
    S = cfg.get("stature_override", zmax - zmin)
    floor = cfg.get("floor_override", zmin)
    V[:, 2] -= floor
    V[:, 0] -= (V[:, 0].max() + V[:, 0].min()) / 2
    V *= 1700.0 / S
    if flip:
        V[:, 1] *= -1
    drop = json.load(open(os.path.join(WORK, opt["drop"]))) if "drop" in opt else []
    keep = ~np.isin(lab, drop)
    T = T[keep[T[:, 0]]]
    V[:, 1] -= (V[keep][:, 1].max() + V[keep][:, 1].min()) / 2
    return V, T, lab


def torso_mask(V, T, lab, z0):
    xr, yr = (-320, 320), (-260, 260)
    g = measure.slice_grid(V, T, lab, z0, xr, yr)
    L, n = ndimage.label(g)
    x_axis = xr[0] + (np.arange(g.shape[1]) + .5) * RES
    y_axis = yr[0] + (np.arange(g.shape[0]) + .5) * RES
    best = None
    for k in range(1, n + 1):
        iy, ix = np.nonzero(L == k)
        xs = x_axis[ix]
        if xs.min() <= 0 <= xs.max() and (best is None or len(ix) > best[0]):
            best = (len(ix), k)
    if best is None:
        return None, x_axis, y_axis
    return L == best[1], x_axis, y_axis


def describe(m, x_axis, y_axis):
    iy, ix = np.nonzero(m)
    xs, ys = x_axis[ix], y_axis[iy]
    cx, cy = xs.mean(), ys.mean()
    w = xs.max() - xs.min() + RES
    d = ys.max() - ys.min() + RES
    area = len(ix) * RES * RES
    mid = np.abs(xs) <= 10
    mf = ys[mid].max() if mid.any() else np.nan
    mb = ys[mid].min() if mid.any() else np.nan
    k = np.argmin(ys)
    kf = np.argmax(ys)
    return dict(cx=float(cx), cy=float(cy), width=float(w), depth=float(d), area=float(area),
                fill=float(area / (w * d)), front_ext=float(ys.max() - cy), back_ext=float(cy - ys.min()),
                front=float(ys.max()), back=float(ys.min()), mid_front=float(mf), mid_back=float(mb),
                back_groove=float(mb - ys.min()), back_max_absx=float(abs(xs[k])),
                front_groove=float(ys.max() - mf), front_max_absx=float(abs(xs[kf])))


if __name__ == "__main__":
    out = {}
    for name, opt in MODELS.items():
        V, T, lab = normalised(name, opt)
        rows, masks = [], {}
        for z0 in np.arange(0.40 * 1700, 0.95 * 1700, 5.0):
            m, xa, ya = torso_mask(V, T, lab, z0)
            if m is None:
                continue
            r = describe(m, xa, ya); r["z"] = float(z0); rows.append(r)
        for f in LEVELS:
            m, xa, ya = torso_mask(V, T, lab, round(f * 1700 / 5) * 5)
            if m is not None:
                masks[f"{f:.3f}"] = m
        np.savez_compressed(os.path.join(WORK, f"shape_{name}.npz"), **masks)
        out[name] = rows
        print(name, len(rows), "cortes;", len(masks), "máscaras")
    json.dump(out, open(os.path.join(WORK, "shape.json"), "w"))
