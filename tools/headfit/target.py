"""HEAD FASE A — alvo estatístico da forma da cabeça a partir das referências.

REFERÊNCIAS → alinhamento (normalização HEAD STUDY 01: mm@H226, z=0 mentón,
y=0 centro glabela–opistocrânio) → mapa radial r(u) visto de um centro comum →
harmónicos esféricos reais (SH) → média + dispersão.

  * r(u): para cada direção u (grelha θ×φ de 3°), o raio do vértice MAIS EXTERIOR
    da pele nessa direção (malha suave densa).
  * Máscaras (declaradas): pescoço (vértice exterior com z < −5 mm) e orelhas
    (|x| > 0.25·H, −40 < y < 25, 60 < z < 150): nestas direções a cabeça é
    interpolada pelo ajuste SH (o crânio por baixo da orelha é liso).
  * SH até grau L com regularização de Tikhonov ∝ l(l+1): grau baixo = massas
    (Fase A), grau alto = detalhe (fases seguintes).

O alvo NÃO é uma malha: é uma função r(u) média de 4 cabeças humanas
(makehuman, femalebase, bodytopo, femalechar).  whitewalker (criatura) e ff11
(traços pintados) ficam de fora — classificação HEAD STUDY 01.
"""
import os
import sys
import json
import numpy as np
from scipy.special import sph_harm_y

HERE = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(HERE, "..", "headstudy"))
import common as C   # noqa: E402

H = C.H_MM
CENTRE = np.array([0.0, 0.0, 0.52 * H])       # centro comum (mm, referencial normalizado)
TARGET_SOURCES = ["makehuman", "femalebase", "bodytopo", "femalechar"]
OUT = os.path.join(HERE, "..", "..", "out", "headfit")
DOC = os.path.join(HERE, "..", "..", "docs", "head_phaseA")
STEP = 3.0


def grid(step=STEP):
    th = np.radians(np.arange(step / 2, 180, step))
    ph = np.radians(np.arange(step / 2, 360, step))
    TH, PH = np.meshgrid(th, ph, indexing="ij")
    return TH, PH


def dirs(TH, PH):
    # φ = 0 aponta para +y (frente), φ = 90° para +x; θ = 0 para +z
    return np.stack([np.sin(TH) * np.sin(PH), np.sin(TH) * np.cos(PH), np.cos(TH)], -1)


def surface_samples(Vn, T, per_mm2=0.7, seed=0):
    """Amostragem densa das faces (medido: só com vértices, as direções sem pele
    exterior eram ganhas por geometria interior — o tubo do pescoço do nosso
    corpo sobe por dentro do crânio até z ≈ topo)."""
    a, b, c = Vn[T[:, 0]], Vn[T[:, 1]], Vn[T[:, 2]]
    area = 0.5 * np.linalg.norm(np.cross(b - a, c - a), axis=1)
    n = np.clip(np.ceil(area * per_mm2).astype(int), 1, 5000)
    idx = np.repeat(np.arange(len(T)), n)
    rng = np.random.default_rng(seed)
    r1 = np.sqrt(rng.random(len(idx))); r2 = rng.random(len(idx))
    P = a[idx] * (1 - r1)[:, None] + b[idx] * (r1 * (1 - r2))[:, None] + c[idx] * (r1 * r2)[:, None]
    return np.vstack([P, Vn[np.unique(T)]])


def radial_map(Vn, T, step=STEP):
    P = surface_samples(Vn, T)
    d = P - CENTRE
    r = np.linalg.norm(d, axis=1)
    u = d / r[:, None]
    th = np.degrees(np.arccos(np.clip(u[:, 2], -1, 1)))
    ph = np.degrees(np.arctan2(u[:, 0], u[:, 1])) % 360
    it = np.minimum((th / step).astype(int), int(180 / step) - 1)
    ip = np.minimum((ph / step).astype(int), int(360 / step) - 1)
    R = np.full((int(180 / step), int(360 / step)), np.nan)
    Z = np.full_like(R, np.nan)
    X = np.full(R.shape + (3,), np.nan)
    lin = it * R.shape[1] + ip
    order = np.argsort(r)                       # o último escrito em cada bin é o mais exterior
    Rf = R.ravel(); Xf = X.reshape(-1, 3)
    Rf[lin[order]] = r[order]
    Xf[lin[order]] = P[order]
    R = Rf.reshape(R.shape); X = Xf.reshape(X.shape)
    return R, X


def masks(X):
    x, y, z = X[..., 0], X[..., 1], X[..., 2]
    neck = z < -5.0
    ear = (np.abs(x) > 0.25 * H) & (y > -40) & (y < 25) & (z > 60) & (z < 150)
    return neck, ear


def sh_basis(TH, PH, L):
    cols, lm = [], []
    for l in range(L + 1):
        for m in range(-l, l + 1):
            Y = sph_harm_y(l, abs(m), TH, PH)
            if m < 0:
                b = np.sqrt(2) * (-1) ** m * Y.imag
            elif m == 0:
                b = Y.real
            else:
                b = np.sqrt(2) * (-1) ** m * Y.real
            cols.append(b.ravel()); lm.append((l, m))
    return np.stack(cols, 1), lm


def sh_fit(R, valid, TH, PH, L, lam=2e-4):
    B, lm = sh_basis(TH, PH, L)
    w = np.sin(TH).ravel()                     # peso de área
    v = valid.ravel() & np.isfinite(R.ravel())
    A = B[v] * w[v, None]
    b = R.ravel()[v] * w[v]
    reg = np.array([l * (l + 1) for l, m in lm], float)
    M = A.T @ A + lam * np.diag(reg) * (A.shape[0])
    c = np.linalg.solve(M, A.T @ b)
    return c, lm


def sh_eval(c, TH, PH, L):
    B, _ = sh_basis(TH, PH, L)
    return (B @ c).reshape(TH.shape)


def build(L_list=(6, 8, 12, 16)):
    os.makedirs(OUT, exist_ok=True); os.makedirs(DOC, exist_ok=True)
    TH, PH = grid()
    res = {}
    for nm in TARGET_SOURCES + ["ours", "whitewalker"]:
        Vn, T, fs, fi, info = C.normalise(nm)
        R, X = radial_map(Vn, T)
        neck, ear = masks(X)
        valid = np.isfinite(R) & ~neck & ~ear
        res[nm] = {"R": R, "X": X, "valid": valid, "neck": neck, "ear": ear, "info": info}
        for L in L_list:
            c, lm = sh_fit(R, valid, TH, PH, L)
            res[nm][f"c{L}"] = c
            fit = sh_eval(c, TH, PH, L)
            e = (fit - R)[valid]
            res[nm][f"rms{L}"] = float(np.sqrt(np.mean(e ** 2)))
        print(nm, "valid", int(valid.sum()), {L: round(res[nm][f"rms{L}"], 2) for L in L_list})
    # alvo = média dos coeficientes (linear ⇒ = média dos mapas ajustados)
    tgt = {}
    for L in L_list:
        Cs = np.stack([res[n][f"c{L}"] for n in TARGET_SOURCES])
        tgt[f"mean{L}"] = Cs.mean(0)
        tgt[f"std_map{L}"] = np.std(np.stack([sh_eval(c, TH, PH, L) for c in Cs]), 0)
    np.savez_compressed(os.path.join(OUT, "target.npz"), TH=TH, PH=PH,
                        **{k: v for k, v in tgt.items()},
                        **{f"{n}_c{L}": res[n][f"c{L}"] for n in res for L in L_list},
                        **{f"{n}_R": res[n]["R"] for n in res},
                        **{f"{n}_valid": res[n]["valid"] for n in res})
    return res, tgt, TH, PH


if __name__ == "__main__":
    res, tgt, TH, PH = build()
    # dispersão entre refs (mm) na região válida comum, grau 8 e 16
    common = np.logical_and.reduce([res[n]["valid"] for n in TARGET_SOURCES])
    for L in (8, 16):
        s = tgt[f"std_map{L}"][common]
        print(f"L{L} desvio-padrão entre refs: mediana {np.median(s):.2f} mm, p90 {np.percentile(s, 90):.2f} mm")
    for n in ("ours", "whitewalker") + tuple(TARGET_SOURCES):
        for L in (8, 16):
            m = sh_eval(tgt[f"mean{L}"], TH, PH, L)
            e = (sh_eval(res[n][f"c{L}"], TH, PH, L) - m)[common]
            print(f"{n:12s} L{L}  vs alvo: RMS {np.sqrt(np.mean(e**2)):.2f}  max|e| {np.abs(e).max():.1f} mm")
