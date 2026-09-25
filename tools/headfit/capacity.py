"""FASE A — teste de CAPACIDADE da representação.

Pergunta: *a família de formas que o gerador atual consegue produzir contém a
forma-alvo?*  Todos os parâmetros da representação ficam LIVRES e são ajustados
por mínimos quadrados ao alvo estatístico (mapa radial médio das refs, SH grau 8
= nível de massas).  O resíduo que sobra depois do ajuste ótimo é o limite da
representação — nenhuma afinação de constantes o baixa.

Representações testadas (mesmo ajuste, mesmo alvo, mesmo domínio):
  R0  atual: elipsoide craniano (box_sphere: taper inferior em x, achatamento do
      topo) + máscara frontal = smooth_max(elipsoide craniano, elipsoide
      "midface/mandíbula"), aplicada em colunas com a janela de bordo do código.
  R1  candidata: construção por massas (ver massmodel.py).
"""
import os
import sys
import json
import numpy as np
from scipy.optimize import least_squares

HERE = os.path.dirname(__file__)
sys.path.insert(0, HERE)
import target as TG      # noqa: E402

H = TG.H


def cube_dirs(n=70):
    g = np.linspace(-1, 1, n + 1)
    U, V = np.meshgrid(g, g, indexing="ij")
    P = []
    for ax in range(3):
        for s in (1, -1):
            p = np.zeros(U.shape + (3,))
            p[..., ax] = s
            p[..., (ax + 1) % 3] = U
            p[..., (ax + 2) % 3] = V
            P.append(p.reshape(-1, 3))
    P = np.unique(np.round(np.vstack(P), 9), axis=0)
    return P / np.linalg.norm(P, axis=1)[:, None]


D = cube_dirs()


def smoothstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


def smooth_max(a, b, k):
    h = np.clip(0.5 + 0.5 * (a - b) / k, 0, 1)
    return b + (a - b) * h + k * h * (1 - h)


# ---------------------------------------------------------------- R0 (atual)
R0_NAMES = ["cy", "cz", "rx", "ry", "rz", "taper", "squash",
            "fdy", "fdz", "frx", "fry", "frz", "k"]
# valores do código (fracções de H; c relativo ao referencial normalizado ≈ 0.52 H)
R0_INIT = np.array([0.0, 0.52, 0.3215 * 1.015, 0.3917 * 1.015, 0.52 * 1.015, 0.25, 0.045,
                    0.055, -0.26, 0.88 * 0.3215, 0.80 * 0.3917, 0.66, 0.010])


def r0_points(p):
    cy, cz, rx, ry, rz, taper, squash, fdy, fdz, frx, fry, frz, k = p * H
    taper /= H; squash /= H
    c = np.array([0.0, cy, cz])
    d = D
    s = 1.0 / np.sqrt((d[:, 0] / rx) ** 2 + (d[:, 1] / ry) ** 2 + (d[:, 2] / rz) ** 2)
    q = c + d * s[:, None]
    lower = smoothstep(c[2] + 0.05 * ry, c[2] - 0.55 * rz, q[:, 2])
    q[:, 0] *= 1.0 + (-taper) * lower
    top = q[:, 2] > c[2] + 0.62 * rz
    q[top, 2] -= squash * rz * smoothstep(c[2] + 0.62 * rz, c[2] + rz, q[top, 2])
    # máscara frontal (skull_front_y), só na metade da frente e na janela de bordo
    x, z = q[:, 0], q[:, 2]
    t = 1 - (x / rx) ** 2 - ((z - c[2]) / rz) ** 2
    ycr = np.where(t > 0, cy + ry * np.sqrt(np.clip(t, 0, None)), cy + ry * 0.35)
    c2y, c2z = cy + fdy, c[2] + fdz
    t2 = 1 - (x / frx) ** 2 - ((z - c2z) / frz) ** 2
    yfa = c2y + fry * np.sqrt(np.clip(t2, 0, None))
    surf = np.where(t2 > 0, smooth_max(ycr, yfa, k), ycr)
    edge = smoothstep(0.80 * rx, 0.52 * rx, np.abs(x)) * \
        smoothstep(c[2] - 0.70 * H, c[2] - 0.55 * H, z) * smoothstep(c[2] + 0.56 * H, c[2] + 0.47 * H, z)
    front = (q[:, 1] > cy - 0.15 * ry) & (np.abs(x) < 0.80 * rx)
    q[:, 1] = np.where(front, q[:, 1] + (surf - q[:, 1]) * edge, q[:, 1])
    return q


def radial_of_points(P, TH, PH):
    R, X = TG.radial_map(P, None) if False else _radial_pts(P)
    return R


def _radial_pts(P, step=TG.STEP):
    d = P - TG.CENTRE
    r = np.linalg.norm(d, axis=1)
    u = d / r[:, None]
    th = np.degrees(np.arccos(np.clip(u[:, 2], -1, 1)))
    ph = np.degrees(np.arctan2(u[:, 0], u[:, 1])) % 360
    it = np.minimum((th / step).astype(int), int(180 / step) - 1)
    ip = np.minimum((ph / step).astype(int), int(360 / step) - 1)
    R = np.full((int(180 / step), int(360 / step)), np.nan)
    lin = it * R.shape[1] + ip
    o = np.argsort(r)
    Rf = R.ravel(); Rf[lin[o]] = r[o]
    return Rf.reshape(R.shape), None


def load_target(L=8):
    d = np.load(os.path.join(TG.OUT, "target.npz"))
    TH, PH = d["TH"], d["PH"]
    tgt = TG.sh_eval(d[f"mean{L}"], TH, PH, L)
    dom = np.logical_and.reduce([d[f"{n}_valid"] for n in TG.TARGET_SOURCES])
    return TH, PH, tgt, dom, d


def region_masks(TH, PH):
    """Regiões pela direção (mm@H226, centro 0.52 H): para ler onde fica o erro."""
    u = TG.dirs(TH, PH)
    P = TG.CENTRE + u * 100.0
    x, y, z = P[..., 0], P[..., 1], P[..., 2]
    face = (u[..., 1] > 0.55) & (z < TG.CENTRE[2] + 25)
    brow = (u[..., 1] > 0.55) & (z >= TG.CENTRE[2] + 25) & (z < TG.CENTRE[2] + 60)
    vault = u[..., 2] > 0.55
    back = u[..., 1] < -0.55
    side = (np.abs(u[..., 0]) > 0.6) & ~vault
    jaw = (u[..., 2] < -0.5) & (u[..., 1] > 0.0)
    return {"face": face, "brow/testa": brow, "abóbada": vault, "occipital": back, "lateral": side, "mandíbula/queixo": jaw}


def fit(model_pts, p0, names, TH, PH, tgt, dom, lo=None, hi=None):
    def resid(p):
        R, _ = _radial_pts(model_pts(p))
        e = R - tgt
        e = np.where(np.isfinite(e), e, 30.0)     # direção sem superfície = penalização
        return e[dom] * np.sqrt(np.sin(TH[dom]))
    r = least_squares(resid, p0, bounds=(lo if lo is not None else -np.inf, hi if hi is not None else np.inf),
                      diff_step=1e-3, max_nfev=400)
    return r


def report(tag, model_pts, p, TH, PH, tgt, dom):
    R, _ = _radial_pts(model_pts(p))
    e = R - tgt
    out = {"rms": float(np.sqrt(np.nanmean(e[dom] ** 2))), "max": float(np.nanmax(np.abs(e[dom]))),
           "p95": float(np.nanpercentile(np.abs(e[dom]), 95))}
    for k, m in region_masks(TH, PH).items():
        mm = m & dom
        out[k] = float(np.sqrt(np.nanmean(e[mm] ** 2))) if mm.any() else None
    print(f"{tag:28s} RMS {out['rms']:.2f}  p95 {out['p95']:.1f}  max {out['max']:.1f}  |  " +
          "  ".join(f"{k} {v:.1f}" for k, v in out.items() if k not in ("rms", "max", "p95") and v is not None))
    return out, e


if __name__ == "__main__":
    TH, PH, tgt, dom, d = load_target(8)
    res = {}
    # referência de escala: quanto é que cada ref se afasta do alvo (mesmo domínio)
    for n in TG.TARGET_SOURCES + ["ours"]:
        Rn = TG.sh_eval(d[f"{n}_c8"], TH, PH, 8)
        e = (Rn - tgt)[dom]
        res[f"ref_{n}"] = {"rms": float(np.sqrt(np.mean(e ** 2))), "max": float(np.abs(e).max())}
        print(f"{'ref ' + n:28s} RMS {res[f'ref_{n}']['rms']:.2f}  max {res[f'ref_{n}']['max']:.1f}")
    out, _ = report("R0 atual (constantes do código)", r0_points, R0_INIT, TH, PH, tgt, dom)
    res["R0_code"] = out
    r = fit(r0_points, R0_INIT, R0_NAMES, TH, PH, tgt, dom)
    out, e0 = report("R0 atual AJUSTADO (ótimo)", r0_points, r.x, TH, PH, tgt, dom)
    res["R0_fit"] = out; res["R0_fit_params"] = dict(zip(R0_NAMES, map(float, r.x)))
    np.save(os.path.join(TG.OUT, "R0_err.npy"), e0)
    json.dump(res, open(os.path.join(TG.OUT, "capacity_R0.json"), "w"), indent=1)


def dims_of_points(P):
    """Largura máx. (0.62–0.90 H), comprimento g–op aproximado (y máx − y mín acima de 0.55 H),
    largura a 0.10 H (mandíbula) e à altura 0.35 H (malar)."""
    def w(z, tol=3.0):
        m = np.abs(P[:, 2] - z) < tol
        return float(np.ptp(P[m, 0])) if m.sum() > 3 else np.nan
    up = P[:, 2] > 0.55 * H
    return {"breadth": max(w(z) for z in np.arange(0.62 * H, 0.90 * H, 3)),
            "length": float(np.ptp(P[up, 1])),
            "w_0.35H": w(0.35 * H), "w_0.10H": w(0.10 * H)}


def fit_individual(model_pts, p0, names, L=16):
    TH, PH, tgt, dom, d = load_target(L)
    out = {}
    for n in TARGET_SOURCES_FIT:
        tn = TG.sh_eval(d[f"{n}_c{L}"], TH, PH, L)
        domn = d[f"{n}_valid"] & dom
        r = fit(model_pts, p0, names, TH, PH, tn, domn)
        o, _ = report(f"  → {n}", model_pts, r.x, TH, PH, tn, domn)
        out[n] = o
    return out


TARGET_SOURCES_FIT = TG.TARGET_SOURCES
