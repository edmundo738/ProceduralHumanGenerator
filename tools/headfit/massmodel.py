"""FASE A — R1: cabeça construída por MASSAS (representação candidata).

Construção (ordem de Loomis, MODELING PRACTICE; massas coerentes com P1/P3 do
HEAD STUDY 01): cada massa é um superelipsoide com semi-eixos assimétricos
(frente/trás, cima/baixo) e expoentes próprios (expoente > 2 ⇒ lados mais
planos: o "plano lateral" do crânio).  A superfície é a união suave, em
distância radial a partir de um centro comum, das massas:

    r(u) = k · log Σ_i exp(r_i(u) / k)

onde r_i(u) é a saída mais exterior do raio C + s·u da massa i (ou ausente).

  M1 abóbada craniana     M2 massa frontal/glabelar (sobrancelha óssea)
  M3 occipital            M4 face média (maxila + zigoma)
  M5 mandíbula (largura afunila de cima para baixo) + M6 mento

Todas as medidas em mm@H226 no referencial normalizado (z = 0 mentón,
y = 0 centro glabela–opistocrânio).  Os parâmetros não são escolhidos à mão:
são AJUSTADOS ao alvo estatístico das referências (fit_r1).  Este ficheiro é a
referência numpy; o gerador tem a mesma construção em Python puro.
"""
import numpy as np

# nome, centro(y,z), semi-eixos, expoentes — ver PARAMS
MASSES = ["vault", "frontal", "occipital", "midface", "mandible", "mentum"]

# vetor de parâmetros (mm, salvo expoentes e taper)
SPEC = [
    # vault: cy cz  ax  byf byb czt czb  e  n
    ("vault", ["cy", "cz", "ax", "byf", "byb", "czt", "czb", "e", "n"],
     [0.0, 125.0, 74.0, 96.0, 100.0, 100.0, 70.0, 2.4, 2.2]),
    # frontal: cy cz ax by cz e
    ("frontal", ["cy", "cz", "ax", "by", "cz_", "e"], [72.0, 138.0, 58.0, 30.0, 24.0, 2.4]),
    # occipital
    ("occipital", ["cy", "cz", "ax", "by", "cz_", "e"], [-70.0, 118.0, 58.0, 34.0, 45.0, 2.2]),
    # midface: cy cz ax byf byb czt czb e n
    ("midface", ["cy", "cz", "ax", "byf", "byb", "czt", "czb", "e", "n"],
     [40.0, 78.0, 62.0, 55.0, 40.0, 40.0, 38.0, 2.6, 2.2]),
    # mandible: cy cz ax_top ax_bot byf byb czt czb e n
    ("mandible", ["cy", "cz", "axt", "axb", "byf", "byb", "czt", "czb", "e", "n"],
     [28.0, 34.0, 58.0, 36.0, 55.0, 38.0, 30.0, 34.0, 2.8, 2.4]),
    # mentum: cy cz ax by cz e
    ("mentum", ["cy", "cz", "ax", "by", "cz_", "e"], [70.0, 14.0, 22.0, 16.0, 16.0, 2.2]),
]
GLOBAL = [("k", 3.5)]


def pack():
    names, vals = [], []
    for m, ks, vs in SPEC:
        for k, v in zip(ks, vs):
            names.append(f"{m}.{k}"); vals.append(v)
    for k, v in GLOBAL:
        names.append(k); vals.append(v)
    return names, np.array(vals, float)


NAMES, P0 = pack()


def unpack(p):
    d, i = {}, 0
    for m, ks, _ in SPEC:
        d[m] = {k: p[i + j] for j, k in enumerate(ks)}
        i += len(ks)
    for k, _ in GLOBAL:
        d[k] = p[i]; i += 1
    return d


def _g(m, prm, x, y, z):
    """Função implícita (< 0 dentro) da massa ``m`` num ponto (arrays)."""
    q = prm
    dy = y - q["cy"]; dz = z - q["cz"]
    if m in ("vault", "midface"):
        by = np.where(dy >= 0, q["byf"], q["byb"])
        cz = np.where(dz >= 0, q["czt"], q["czb"])
        ax = q["ax"]
        e, n = q["e"], q["n"]
    elif m == "mandible":
        by = np.where(dy >= 0, q["byf"], q["byb"])
        cz = np.where(dz >= 0, q["czt"], q["czb"])
        t = np.clip((dz + q["czb"]) / (q["czt"] + q["czb"]), 0, 1)      # 0 em baixo, 1 em cima
        ax = q["axb"] + (q["axt"] - q["axb"]) * t
        e, n = q["e"], q["n"]
    else:
        by, cz, ax = q["by"], q["cz_"], q["ax"]
        e = n = q["e"]
    hx = (np.abs(x) / ax) ** e + (np.abs(dy) / by) ** e
    return hx ** (n / e) + (np.abs(dz) / cz) ** n - 1.0


def ray_exit(m, prm, C, U, smax=240.0, nsteps=96, nbis=14):
    """Distância da saída mais exterior do raio C + s·U da massa m (NaN se falha)."""
    s = np.linspace(0.0, smax, nsteps)
    P = C[None, None, :] + s[None, :, None] * U[:, None, :]
    g = _g(m, prm, P[..., 0], P[..., 1], P[..., 2])
    inside = g < 0
    any_in = inside.any(1)
    last = nsteps - 1 - np.argmax(inside[:, ::-1], axis=1)       # último índice dentro
    lo = s[np.clip(last, 0, nsteps - 1)]
    hi = s[np.clip(last + 1, 0, nsteps - 1)]
    for _ in range(nbis):
        mid = 0.5 * (lo + hi)
        Pm = C[None, :] + mid[:, None] * U
        gm = _g(m, prm, Pm[:, 0], Pm[:, 1], Pm[:, 2])
        ins = gm < 0
        lo = np.where(ins, mid, lo); hi = np.where(ins, hi, mid)
    r = 0.5 * (lo + hi)
    return np.where(any_in & (last < nsteps - 1), r, np.nan)


def radial(p, C, U):
    d = unpack(p)
    k = max(d["k"], 0.3)
    R = np.stack([ray_exit(m, d[m], C, U) for m in MASSES], 0)
    mx = np.nanmax(R, 0)
    ex = np.where(np.isnan(R), 0.0, np.exp((R - mx[None]) / k))
    return mx + k * np.log(ex.sum(0))
