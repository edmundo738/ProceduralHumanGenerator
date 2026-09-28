"""Ajuste dos campos anatómicos da face ao resíduo (alvo facial médio − casca de massas).

Disposição inicial = marcos médios das refs (face_landmarks.json, em X,Z = 100·u).
Limites: cada campo fica numa caixa anatómica em torno da posição inicial (não pode
"fugir" para outra região — lição da Fase A, em que massas mudaram de papel).
Saída: out/face/face_params.json + tabela Python para o gerador.
"""
import os, sys, json, math
import numpy as np
from scipy.optimize import least_squares
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, ROOT); sys.path.insert(0, HERE)
from human_generator.generators import face_fields as FF  # noqa
from face_target import OUT  # noqa

PI2 = math.pi / 2
SIGMA_MM = float(os.environ.get("SIGMA_MM", 20.0))
# nome, tipo, frame, sym, params iniciais, (caixa de posição ±), notas
# blob: x0 z0 a b th A p        ridge: x0 z0 th L c w A0 A1
INIT = [
    # --- terço superior
    ("testa", "blob", "F", 0, [0, 30, 45, 25, 0, 1.0, 2], 10),
    ("glabela", "blob", "F", 0, [0, 8, 10, 7, 0, 2.0, 2], 5),
    ("arco_superciliar", "ridge", "F", 1, [36, 4, -0.12, 22, 0.004, 5, 3, 1], 6),
    ("temporal", "blob", "F", 1, [70, 5, 12, 16, 0, -2, 2], 8),
    # --- órbita (cavidade que emerge da massa: bacia + rebordos; pálpebras = modelo do olho)
    ("orbita", "blob", "F", 1, [39, -14, 21, 15, 0.1, -9, 2.5], 6),
    ("orbita_medial", "blob", "F", 1, [21, -16, 7, 10, 0, -6, 2], 5),
    ("rebordo_lateral", "blob", "F", 1, [62, -17, 5, 11, 0, 2, 2], 5),
    ("sulco_palpebral", "ridge", "F", 1, [39, 0, 0.08, 16, 0.006, 2, -2, -2], 4),
    ("palpebra_inf", "blob", "F", 1, [40, -29, 15, 4, 0.05, 2, 2], 5),
    # --- terço médio
    ("malar", "blob", "F", 1, [53, -36, 15, 14, 0.3, 4, 2], 8),
    ("fossa_canina", "blob", "F", 1, [31, -48, 12, 10, 0, -3, 2], 7),
    ("dorso_nasal", "ridge", "F", 0, [0, -26, PI2, 16, 0.0, 5, 16, 4], 4),
    ("ponta_nasal", "blob", "F", 0, [0, -41, 7, 6, 0, 8, 2], 4),
    ("asa_nasal", "blob", "F", 1, [10, -49, 5, 5, 0, 5, 2], 4),
    ("sulco_alar", "ridge", "F", 1, [14, -48, 1.3, 7, 0.02, 1.5, -2, -2], 4),
    ("narina", "blob", "F", 1, [6, -55, 3, 2, 0, -3, 2], 3),
    ("subnasal", "blob", "F", 0, [0, -59, 5, 3, 0, -3, 2], 3),
    ("sulco_nasolabial", "ridge", "F", 1, [20, -66, -1.16, 16, 0.0, 3, -3, -2], 5),
    # --- boca e queixo
    ("filtro", "blob", "F", 0, [0, -63.5, 2.5, 3, 0, -1, 2], 3),
    ("labio_sup", "blob", "F", 0, [0, -68, 19, 3.5, 0, 3, 3], 3),
    ("estomio", "ridge", "F", 0, [0, -72.2, 0, 22, -0.016, 1.0, -3, -3], 2),
    ("labio_inf", "blob", "F", 0, [0, -75.5, 17, 3.5, 0, 3, 3], 3),
    ("comissura", "blob", "F", 1, [22, -80, 3, 3, 0, -2, 2], 3),
    ("sulco_mentolabial", "ridge", "F", 0, [0, -78, 0, 14, -0.012, 1.5, -2, -2], 3),
    ("mento", "blob", "F", 0, [0, -86, 12, 7, 0, 2, 2], 4),
    # --- orelha (plano lateral Y,V; lado +X espelhado)
    ("orelha_placa", "blob", "S", 1, [-22, -22, 12, 20, 0.2, 8, 4], 8),
    ("helix", "ridge", "S", 1, [-32, -20, PI2, 20, 0.02, 3, 4, 4], 6),
    ("antihelix", "ridge", "S", 1, [-24, -18, PI2, 12, 0.02, 2.5, 2, 2], 5),
    ("concha", "blob", "S", 1, [-16, -29, 6, 7, 0, -5, 2], 5),
    ("tragus", "blob", "S", 1, [-9, -29, 3, 4, 0, 2, 2], 4),
    ("lobulo", "blob", "S", 1, [-19, -47, 6, 6, 0, 4, 2], 6),
]


def prims_of(theta):
    out, k = [], 0
    for nm, kind, fr, sym, p0, _box in INIT:
        n = len(p0)
        out.append((nm, kind, fr, sym, list(theta[k:k + n]))); k += n
    return out


def bounds():
    lo, hi = [], []
    for nm, kind, fr, sym, p0, box in INIT:
        if kind == "blob":
            x0, z0, a, b, th, A, p = p0
            lo += [x0 - box, z0 - box, 0.6 * a, 0.6 * b, th - 0.5, -40, 1.5]
            hi += [x0 + box, z0 + box, 1.5 * a, 1.5 * b, th + 0.5, 40, (5 if nm in ('labio_sup', 'labio_inf', 'orelha_placa') else 3)]
        else:
            x0, z0, th, L, c, w, A0, A1 = p0
            lo += [x0 - box, z0 - box, th - 0.6, 0.6 * L, -0.08, 0.5, -30, -30]
            hi += [x0 + box, z0 + box, th + 0.6, 1.4 * L, 0.08, 2 * w, 30, 30]
    SIGN = {"narina": (-4.0, 0.0), "subnasal": (-6.0, 0.0), "ponta_nasal": (0.0, 20.0), "asa_nasal": (0.0, 12.0),
            "labio_sup": (0.0, 8.0), "labio_inf": (0.0, 8.0), "estomio": (-6.0, 0.0), "orbita": (-20.0, 0.0)}
    k = 0
    for nm, kind, fr, sym, p0, box in INIT:
        if nm in SIGN:
            ia = k + (5 if kind == "blob" else 6)
            idx = [ia] if kind == "blob" else [ia, ia + 1]
            for i in idx:
                lo[i], hi[i] = SIGN[nm]
        k += len(p0)
    if True:  # simétricos com x0 livre não podem atravessar a linha média
        k = 0
        for nm, kind, fr, sym, p0, box in INIT:
            if sym and fr == "F":
                lo[k] = max(lo[k], 1.0)
            if not sym and fr == "F":
                lo[k], hi[k] = -1e-6, 1e-6          # campos de linha média ficam em X = 0
            k += len(p0)
    return np.array(lo, float), np.array(hi, float)


def load(stride=1):
    d = np.load(os.path.join(OUT, "residual.npz"))
    U, base, mean = d["U"][::stride, ::stride], d["base"][::stride, ::stride], d["mean"][::stride, ::stride]
    D = mean - base
    # separação de escalas: a casca de massas fica com a baixa frequência; os campos
    # anatómicos ajustam só o detalhe D − passa-baixo(D) (gaussiana ~SIGMA_MM, sem NaN)
    from scipy.ndimage import gaussian_filter
    sig_bins = SIGMA_MM / (100.0 * np.radians(d["AZ"][1] - d["AZ"][0])) / stride
    valid = np.isfinite(D) & (np.abs(D) < 40)
    num = gaussian_filter(np.where(valid, D, 0.0), sig_bins)
    den = gaussian_filter(valid.astype(float), sig_bins)
    D_low = num / np.maximum(den, 1e-6)
    np.save(os.path.join(OUT, "D_low.npy"), D_low)
    D = D - D_low
    X, Y = 100 * U[..., 0], 100 * U[..., 1]
    # domínio: pele medida acima do mentón (sem pescoço), frente + lados; aberturas (NaN) fora
    zsurf = mean * U[..., 2] + 0.52 * 226.1
    ok = np.isfinite(D) & (zsurf > 2.0) & (np.abs(D) < 40)
    E = json.load(open(os.path.join(OUT, "eye_params.json")))
    Hc, _Yc, Vc, _Xc = FF.coords(np, U[..., 0], U[..., 1], U[..., 2])
    dE, _n = FF.fissure_distance(np, np.abs(Hc), Vc, E)
    ok &= dE > 8.0                                   # zona do olho: modelo próprio (não ajustado)
    face = (Y > 0) & (np.abs(X) < 75) & (100 * U[..., 2] > -85) & (100 * U[..., 2] < 40)
    w = np.where(face, 1.0, 0.5)
    return U, D, ok, w, d


PRIOR_W = float(os.environ.get("PRIOR_W", 12.0))


def prior_sigma():
    sig = []
    for nm, kind, fr, sym, p0, box in INIT:
        if kind == "blob":
            x0, z0, a, b, th, A, p = p0
            sig += [box, box, 0.5 * a, 0.5 * b, 0.5, 10, 3]
        else:
            x0, z0, th, L, c, w, A0, A1 = p0
            sig += [box, box, 0.4, 0.5 * L, 0.03, w, 10, 10]
    return np.array(sig, float)


class Model:
    def __init__(self, U, D, ok, w):
        self.u = U[ok]; self.D = D[ok]; self.w = np.sqrt(w[ok])
        self.C = FF.coords(np, self.u[:, 0], self.u[:, 1], self.u[:, 2])

    def one(self, spec):
        nm, kind, fr, sym, P = spec
        f = FF.blob if kind == "blob" else FF.ridge
        return f(np, fr, sym, P, self.C)

    def res(self, theta):
        F = sum(self.one(s) for s in prims_of(theta))
        return np.concatenate([(F - self.D) * self.w, PRIOR_W * (theta - self.th0) / self.sig])

    def jac(self, theta):
        prims = prims_of(theta)
        J = np.zeros((len(self.D), len(theta)))
        k = 0
        for s in prims:
            base = self.one(s)
            for j in range(len(s[4])):
                h = 1e-4 * max(1.0, abs(s[4][j]))
                P2 = list(s[4]); P2[j] += h
                J[:, k + j] = (self.one((s[0], s[1], s[2], s[3], P2)) - base) / h * self.w
            k += len(s[4])
        return np.vstack([J, np.diag(PRIOR_W / self.sig)])


def main():
    U, D, ok, w, d = load()
    M = Model(U, D, ok, w)
    th0 = np.concatenate([i[4] for i in INIT]).astype(float)
    lo, hi = bounds()
    th0 = np.clip(th0, lo + 1e-9, hi - 1e-9)
    M.th0, M.sig = th0.copy(), prior_sigma()
    print("pontos", len(M.D), "parâmetros", len(th0), "RMS inicial (sem campos)", np.sqrt(np.mean(M.D ** 2)))
    r = least_squares(M.res, th0, jac=M.jac, bounds=(lo, hi), x_scale="jac", max_nfev=int(os.environ.get("NFEV", 60)), verbose=1)
    th = r.x
    e = M.res(th)[:len(M.D)] / M.w
    print("RMS final", np.sqrt(np.mean(e ** 2)), "p90 |e|", np.percentile(np.abs(e), 90))
    prims = prims_of(th)
    json.dump([[nm, kind, fr, sym, [round(float(v), 4) for v in P]] for nm, kind, fr, sym, P in prims],
              open(os.path.join(OUT, "face_params.json"), "w"), indent=0, ensure_ascii=False)
    # mapa ajustado (para figuras)
    Ufull = d["U"]
    F = FF.field(np, prims, Ufull[..., 0], Ufull[..., 1], Ufull[..., 2])
    np.save(os.path.join(OUT, "fitted_F.npy"), F)
    for p in prims:
        print(f"  {p[0]:18s} {[round(v, 2) for v in p[4]]}")


if __name__ == "__main__":
    main()
