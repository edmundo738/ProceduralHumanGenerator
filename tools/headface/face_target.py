"""FACE TARGET — alvo estatístico da FACE (detalhe) a partir das refs, com alinhamento por marcos.

REFERÊNCIAS (normalizadas HEAD STUDY 01: mm@H226, z=0 mentón, y=0 centro g–op)
  → mapa radial fino r(az, el) visto de CENTRE (o mesmo centro da casca de massas)
  → marcos automáticos (laços de fronteira dos olhos/boca + perfil sagital)
  → cada ref é deformada em (az, el) por thin-plate spline para os marcos MÉDIOS
  → média (nanmean) + desvio-padrão entre refs.

Refs: femalebase, bodytopo, femalechar (makehuman: sem laços de olhos/boca → sem
marcos; já excluída das estatísticas de queixo/pescoço).  É um alvo de CALIBRAÇÃO:
o gerador não lê este ficheiro nem vértices das refs.
"""
import os, sys, json
import numpy as np
from scipy.interpolate import RBFInterpolator, RegularGridInterpolator
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "headstudy"))
sys.path.insert(0, os.path.join(HERE, "..", "headfit"))
import common as C  # noqa
from landmarks import boundary_loops  # noqa
import target as TG  # noqa

REFS = ["femalebase", "bodytopo", "femalechar"]
CENTRE = TG.CENTRE
STEP = 0.5
AZ = np.arange(-120, 120 + 1e-9, STEP)
EL = np.arange(-80, 75 + 1e-9, STEP)
OUT = os.path.join(HERE, "..", "..", "out", "face")


def to_dir(P):
    d = P - CENTRE
    az = np.degrees(np.arctan2(d[..., 0], d[..., 1]))
    el = np.degrees(np.arctan2(d[..., 2], np.hypot(d[..., 0], d[..., 1])))
    return az, el, np.linalg.norm(d, axis=-1)


def from_dir(az, el, r):
    a, e = np.radians(az), np.radians(el)
    return CENTRE + np.stack([r * np.cos(e) * np.sin(a), r * np.cos(e) * np.cos(a), r * np.sin(e)], -1)


def radial_map(Vn, T, per_mm2=6.0):
    P = TG.surface_samples(Vn, T, per_mm2=per_mm2)
    az, el, r = to_dir(P)
    ia = np.round((az - AZ[0]) / STEP).astype(int); ie = np.round((el - EL[0]) / STEP).astype(int)
    ok = (ia >= 0) & (ia < len(AZ)) & (ie >= 0) & (ie < len(EL))
    R = np.full((len(EL), len(AZ)), np.nan)
    lin = ie[ok] * len(AZ) + ia[ok]
    o = np.argsort(r[ok])
    R.ravel()[lin[o]] = r[ok][o]
    # fecho morfológico leve (buracos de amostragem de 1 bin), sem atravessar aberturas grandes
    from scipy.ndimage import generic_filter
    hole = np.isnan(R)
    Rf = generic_filter(np.nan_to_num(R, nan=-1), lambda w: np.max(w), size=3)
    fill = hole & (generic_filter((~hole).astype(float), np.sum, size=3) >= 6)
    R[fill] = Rf[fill]
    return R


def profile(Vn, T, zs, half=0.8):
    P = TG.surface_samples(Vn, T, per_mm2=8.0)
    P = P[(np.abs(P[:, 0]) < half) & (P[:, 1] > 0)]
    y = np.full(len(zs), np.nan)
    for i, z in enumerate(zs):
        m = np.abs(P[:, 2] - z) < 0.5
        if m.any():
            y[i] = P[m, 1].max()
    return y


def landmarks(name):
    Vn, T, fs, fi, info = C.normalise(name)
    L = {}
    loops = [lp for lp in boundary_loops(T) if len(lp) >= 8]
    eyes, mouth = [], None
    for lp in loops:
        P = Vn[lp]; c = P.mean(0)
        if c[1] < 20:
            continue
        if 85 < c[2] < 125 and abs(c[0]) > 15:
            eyes.append(P)
        elif 20 < c[2] < 50 and abs(c[0]) < 2 and (P[:, 0].max() - P[:, 0].min()) > 20:
            mouth = P
    for P in eyes:
        s = "L" if P[:, 0].mean() > 0 else "R"
        ax = np.abs(P[:, 0])
        L[f"en_{s}"] = P[np.argmin(ax)]          # canto interno
        L[f"ex_{s}"] = P[np.argmax(ax)]          # canto externo
        mid = np.abs(ax - ax.mean()) < 0.25 * (ax.max() - ax.min())
        L[f"ps_{s}"] = P[mid][np.argmax(P[mid, 2])]   # pálpebra superior
        L[f"pi_{s}"] = P[mid][np.argmin(P[mid, 2])]   # pálpebra inferior
    L["ch_L"] = mouth[np.argmax(mouth[:, 0])]; L["ch_R"] = mouth[np.argmin(mouth[:, 0])]
    zs = np.arange(-10, 200, 0.5)
    y = profile(Vn, T, zs)
    def arg(lo, hi, f):
        m = (zs > lo) & (zs < hi) & np.isfinite(y)
        i = np.nonzero(m)[0][f(y[m])]
        return np.array([0.0, y[i], zs[i]])
    L["prn"] = arg(55, 95, np.argmax)
    zsto = mouth[:, 2].mean()
    L["sto"] = np.array([0.0, np.nanmin(y[np.abs(zs - zsto) < 1.6]), zsto])
    L["sn"] = arg(L["sto"][2] + 8, L["prn"][2] - 3, np.argmin)
    L["ls"] = arg(L["sto"][2] + 1, L["sn"][2] - 2, np.argmax)
    L["pg"] = arg(3, L["sto"][2] - 12, np.argmax)
    L["li"] = arg(L["pg"][2] + 6, L["sto"][2] - 1, np.argmax)
    L["sl"] = arg(L["pg"][2] + 2, L["li"][2] - 2, np.argmin)
    L["g"] = arg(125, 170, np.argmax)
    L["n"] = arg(L["prn"][2] + 15, L["g"][2] - 2, np.argmin)
    L["me"] = np.array([0.0, y[np.argmin(np.abs(zs))], 0.0])
    return Vn, T, {k: np.asarray(v, float) for k, v in L.items()}


def ear_landmarks(R, L):
    """Marcos da orelha no mapa radial: extremos (cima, baixo, frente, trás) da região
    que sobressai > 2.5 mm do crânio suavizado (mediana 20°), janela lateral."""
    from scipy.ndimage import median_filter, label
    AA, EE = np.meshgrid(AZ, EL)
    Rf = np.where(np.isfinite(R), R, np.nanmedian(R))
    base = median_filter(Rf, size=41)
    for s_, sgn in (("L", 1), ("R", -1)):
        win = (sgn * AA > 70) & (sgn * AA < 125) & (EE > -50) & (EE < 10)
        m = win & np.isfinite(R) & (R - base > 2.5)
        lab, n = label(m)
        if n == 0:
            continue
        k = np.argmax(np.bincount(lab.ravel())[1:]) + 1
        a, e = AA[lab == k], EE[lab == k]
        pts = {"top": (a[np.argmax(e)], e.max()), "bot": (a[np.argmin(e)], e.min()),
               "front": (a[np.argmin(sgn * a)], e[np.argmin(sgn * a)]), "back": (a[np.argmax(sgn * a)], e[np.argmax(sgn * a)])}
        for kk, (aa, ee) in pts.items():
            L[f"ear{kk}_{s_}"] = from_dir(aa, ee, 100.0)


def build():
    os.makedirs(OUT, exist_ok=True)
    maps, lms = {}, {}
    for n in REFS:
        Vn, T, L = landmarks(n)
        maps[n] = radial_map(Vn, T)
        ear_landmarks(maps[n], L)
        lms[n] = L
        print(n, {k: v.round(1).tolist() for k, v in L.items()})
    keys = sorted(k for k in set.intersection(*[set(lms[n]) for n in REFS]) if not k.startswith("earfront"))
    print("marcos usados:", keys)
    mean_L = {k: np.mean([lms[n][k] for n in REFS], 0) for k in keys}
    # âncoras fixas longe da face (crânio/lados/pescoço): a deformação é só facial
    anchors = [(a, e) for a in np.arange(-120, 121, 30) for e in (-80, 70)] + \
              [(a, e) for a in (-120, -90, 90, 120) for e in np.arange(-60, 61, 30)]
    tgt_dir = np.array([to_dir(mean_L[k])[:2] for k in keys] + anchors)
    AA, EE = np.meshgrid(AZ, EL)
    Q = np.stack([AA.ravel(), EE.ravel()], 1)
    warped = []
    for n in REFS:
        src_dir = np.array([to_dir(lms[n][k])[:2] for k in keys] + anchors)
        f = RBFInterpolator(tgt_dir, src_dir - tgt_dir, kernel="thin_plate_spline", smoothing=0.5)
        S = Q + f(Q)
        gi = RegularGridInterpolator((EL, AZ), maps[n], bounds_error=False, fill_value=np.nan)
        W = gi(np.stack([S[:, 1], S[:, 0]], 1)).reshape(AA.shape)
        warped.append(W)
    Wst = np.stack(warped)
    cnt = np.isfinite(Wst).sum(0)
    mean = np.where(cnt >= 2, np.nanmean(np.where(np.isfinite(Wst), Wst, np.nan), 0), np.nan)
    std = np.nanstd(Wst, 0)
    np.savez_compressed(os.path.join(OUT, "face_target.npz"), AZ=AZ, EL=EL, mean=mean, std=std, count=cnt,
                        **{f"w_{n}": w for n, w in zip(REFS, warped)}, **{f"raw_{n}": maps[n] for n in REFS})
    json.dump({"mean": {k: v.round(2).tolist() for k, v in mean_L.items()},
               "refs": {n: {k: v.round(2).tolist() for k, v in lms[n].items()} for n in REFS}},
              open(os.path.join(OUT, "face_landmarks.json"), "w"), indent=1)
    return mean, std, mean_L


if __name__ == "__main__":
    import warnings; warnings.filterwarnings("ignore")
    mean, std, L = build()
    print("MEAN", {k: v.round(1).tolist() for k, v in L.items()})
    fin = np.isfinite(mean)
    print("std median", np.nanmedian(std[fin]), "p90", np.nanpercentile(std[fin], 90))
