# -*- coding: utf-8 -*-
"""HEAD FASE A — casca da cabeça construída por MASSAS (representação R1).

Pré-registo: ``docs/HEAD_PHASE_A_PREREG.md``.  Ativa só com ``HCG_HEAD=massA``
(a build por omissão continua a usar ``head.build_head``; pins inalterados).

Porquê (medido, ``docs/head_phaseA/``): a representação anterior (elipsoide +
máscara frontal + bossas + aberturas cortadas) com TODOS os parâmetros livres
não consegue representar a forma das cabeças de referência sem distorcer a
anatomia (RMS 3.75 mm, máx. 14.3; largura 162 mm; mandíbula 77 mm).  R1 chega a
RMS 1.35 mm (máx. 3.9) com dimensões dentro das referências.

Construção: a superfície é a união suave, em distância radial vista de um
centro comum, de seis massas superelipsoidais (semi-eixos assimétricos
frente/trás e cima/baixo; expoente > 2 ⇒ lados mais planos):

    r(u) = k · log Σ_i exp(r_i(u) / k)

r_i(u) = saída mais exterior do raio C + s·u da massa i.  Os parâmetros NÃO são
escolhidos à mão: vêm do ajuste por mínimos quadrados ao alvo estatístico
(média SH grau 16 de makehuman, femalebase, bodytopo e femalechar normalizadas a
H) — ``tools/headfit/fit_r1.py``.  Nenhum vértice de referência é usado.

Referencial dos parâmetros: mm@H226.1, z = 0 no mentón, y = 0 no centro
glabela–opistocrânio.  Mapeamento para o mundo: escala ``anat.h / 226.1``,
mentón em ``anat.z("chin")`` (topo em mentón + h, como a cabeça anterior), y do
centro glabela–opistocrânio medido na cabeça anterior (−0.0391·h, mantém a
relação com o pescoço — o corpo não muda).

Nota (OBSERVED, declarada): depois do ajuste algumas massas não correspondem ao
nome inicial (o "mentum" ficou a z = 72 mm e faz de protuberância da face
média; o "occipital" é o volume craniano principal).  Para a Fase A (silhueta)
é irrelevante; a Fase B (massas faciais) terá de ancorar massas a marcos.
"""
from __future__ import annotations

import math

from ..core._math import Vector
from ..core.topology import MeshBuilder
from .head import HeadResult

H_NORM = 226.1
CENTRE = (0.0, 0.0, 0.52 * H_NORM)
# y do centro glabela–opistocrânio da cabeça anterior, em fracção de h (medido:
# −8.84 mm para h = 222.2 mm; HEAD STUDY 01, normalise → y0)
Y0_FRAC = -0.0398

# ajuste R1 ao alvo médio (docs/head_phaseA/capacity_R1.json, "R1_mean_params")
R1 = {
    "vault": dict(cy=20.520, cz=99.410, ax=66.527, byf=65.241, byb=66.099, czt=114.640, czb=77.458, e=3.036, n=2.920),
    "frontal": dict(cy=63.048, cz=137.597, ax=47.337, by=37.062, cz_=52.934, e=1.745),
    "occipital": dict(cy=-12.097, cz=133.237, ax=75.624, by=87.760, cz_=90.940, e=2.158),
    "midface": dict(cy=4.308, cz=55.396, ax=50.779, byf=89.111, byb=75.870, czt=51.030, czb=45.323, e=2.545, n=3.567),
    "mandible": dict(cy=43.653, cz=24.518, axt=39.126, axb=24.718, byf=41.089, byb=46.537, czt=29.510, czb=23.744,
                     e=2.075, n=2.467),
    "mentum": dict(cy=76.279, cz=72.401, ax=22.406, by=33.083, cz_=42.506, e=1.690),
}
K_UNION = 8.656
MASSES = ("vault", "frontal", "occipital", "midface", "mandible", "mentum")
GRID_N = 24


def _g(m: str, q: dict, x: float, y: float, z: float) -> float:
    dy = y - q["cy"]
    dz = z - q["cz"]
    if m in ("vault", "midface", "mandible"):
        by = q["byf"] if dy >= 0 else q["byb"]
        cz = q["czt"] if dz >= 0 else q["czb"]
        if m == "mandible":
            t = min(1.0, max(0.0, (dz + q["czb"]) / (q["czt"] + q["czb"])))
            ax = q["axb"] + (q["axt"] - q["axb"]) * t
        else:
            ax = q["ax"]
        e, n = q["e"], q["n"]
    else:
        by, cz, ax = q["by"], q["cz_"], q["ax"]
        e = n = q["e"]
    hx = (abs(x) / ax) ** e + (abs(dy) / by) ** e
    return hx ** (n / e) + (abs(dz) / cz) ** n - 1.0


def _ray_exit(m: str, u: tuple, smax: float = 240.0, nsteps: int = 96, nbis: int = 16):
    q = R1[m]
    cx, cy, cz = CENTRE
    ux, uy, uz = u
    last = -1
    step = smax / (nsteps - 1)
    for i in range(nsteps - 1, -1, -1):            # de fora para dentro: 1.º ponto dentro
        s = i * step
        if _g(m, q, cx + s * ux, cy + s * uy, cz + s * uz) < 0.0:
            last = i
            break
    if last < 0 or last == nsteps - 1:
        return None
    lo, hi = last * step, (last + 1) * step
    for _ in range(nbis):
        mid = 0.5 * (lo + hi)
        if _g(m, q, cx + mid * ux, cy + mid * uy, cz + mid * uz) < 0.0:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def radial(u: tuple) -> float:
    rs = [r for r in (_ray_exit(m, u) for m in MASSES) if r is not None]
    mx = max(rs)
    return mx + K_UNION * math.log(sum(math.exp((r - mx) / K_UNION) for r in rs))


# --------------------------------------------------------------------------- A2b
# Canto mento–submental (``docs/HEAD_PHASE_A2_PREREG.md``, emenda A2b).  A2 (corte
# por um plano) foi REFUTADA: o canto da casca A está SUBPREENCHIDO, não em
# excesso.  A2b une a casca A, localmente, com o envelope mentoniano MÉDIO de
# femalebase/bodytopo/femalechar (``tools/headfit/chin_study.py`` e
# ``out/headfit/chin_front.npz``; referencial mm@H226, z = 0 no mentón 45°,
# y = 0 no centro glabela–opistocrânio).  Só números médios — nenhum vértice das
# refs.  Bloco = { sub_z(x) ≤ z ≤ 15, 0 ≤ y ≤ Yf(x, z) }, |x| ≤ 40.
# Face inferior = plano submental medido: −3.5 mm em x = 0, sobe até +1.4 em
# |x| = 20 (não se extrapola além).  União polinomial local k_c = 4 mm.
SUB_A0 = -3.5
SUB_C = 0.01225
SUB_XMAX = 20.0
SUB_KC = 4.0
CHIN_ZS = (-1.0, 1.0, 3.0, 5.0, 7.0, 9.0, 11.0, 13.0, 15.0)
CHIN_XS = (0.0, 4.0, 8.0, 12.0, 16.0, 20.0, 24.0, 28.0, 32.0, 36.0, 40.0)
CHIN_YF = (
    (78.83, 78.42, 77.41, 74.24, 54.78, 38.50, 33.79, 19.13, 13.07, 7.99, 12.38),
    (80.65, 80.27, 79.51, 77.26, 73.69, 52.81, 36.48, 31.98, 15.84, 9.27, 13.46),
    (81.88, 81.67, 80.84, 79.19, 76.10, 70.90, 49.88, 34.01, 28.77, 11.81, 15.28),
    (82.79, 82.51, 81.75, 80.27, 77.58, 73.67, 52.00, 45.91, 30.86, 24.68, 10.37),
    (83.45, 83.25, 82.48, 80.98, 78.81, 75.36, 70.38, 48.87, 33.06, 27.10, 29.61),
    (83.99, 83.75, 83.02, 81.58, 79.44, 76.51, 72.15, 65.31, 44.60, 29.47, 34.61),
    (84.32, 84.08, 83.36, 81.99, 80.09, 77.21, 73.40, 67.90, 47.18, 38.62, 38.11),
    (84.67, 84.38, 83.68, 82.30, 80.51, 77.95, 74.54, 69.80, 62.76, 42.69, 40.55),
    (84.91, 84.64, 83.93, 82.56, 80.88, 78.44, 75.33, 71.07, 65.57, 44.83, 36.56),
)
CHIN_ZTOP = 15.0


def _sub_z(x: float) -> float:
    xa = min(abs(x), SUB_XMAX)
    return SUB_A0 + SUB_C * xa * xa


def _yf(x: float, z: float) -> float:
    """Frente média do queixo (bilinear); z abaixo de −1 usa a linha −1 (até ao plano)."""
    xa = abs(x)
    zc = min(max(z, CHIN_ZS[0]), CHIN_ZS[-1])
    i = min(int((zc - CHIN_ZS[0]) / 2.0), len(CHIN_ZS) - 2)
    j = min(int(xa / 4.0), len(CHIN_XS) - 2)
    tz = (zc - CHIN_ZS[i]) / 2.0
    tx = (xa - CHIN_XS[j]) / 4.0
    a = CHIN_YF[i][j] * (1 - tx) + CHIN_YF[i][j + 1] * tx
    b = CHIN_YF[i + 1][j] * (1 - tx) + CHIN_YF[i + 1][j + 1] * tx
    return a * (1 - tz) + b * tz


# continuidade (ENGINEERING JUDGMENT, declarado): atrás de y = 45 a face inferior
# do bloco sobe linearmente até +10 mm em y = 25 — o bloco volta a ficar dentro da
# casca A sem degrau.  Essa faixa fica dentro do pescoço do corpo (frente a y ≈ 42),
# que está congelado; é aí que o submento das refs continuaria (cervical y 5–25).
CHIN_Y1, CHIN_Y0 = 45.0, 25.0


def _in_chin(x: float, y: float, z: float) -> bool:
    if abs(x) > CHIN_XS[-1] or z > CHIN_ZTOP or y < CHIN_Y0:
        return False
    zb = _sub_z(x) + max(0.0, (CHIN_Y1 - y) / (CHIN_Y1 - CHIN_Y0)) * (10.0 - SUB_A0)
    if z < zb:
        return False
    return y <= _yf(x, z)


def _chin_exit(u: tuple, smax: float = 240.0, nsteps: int = 480, nbis: int = 16):
    cx, cy, cz = CENTRE
    ux, uy, uz = u
    if uz > -0.05 or uy < 0.0:            # o bloco está à frente e muito abaixo do centro
        return None
    step = smax / nsteps
    last = -1
    for i in range(nsteps, -1, -1):
        s = i * step
        if _in_chin(cx + s * ux, cy + s * uy, cz + s * uz):
            last = i
            break
    if last < 0 or last == nsteps:
        return None
    lo, hi = last * step, (last + 1) * step
    for _ in range(nbis):
        mid = 0.5 * (lo + hi)
        if _in_chin(cx + mid * ux, cy + mid * uy, cz + mid * uz):
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def _smax(a: float, b: float, k: float) -> float:
    h = max(k - abs(a - b), 0.0) / k
    return max(a, b) + h * h * k * 0.25


def radial_a2(u: tuple) -> float:
    r = radial(u)
    rc = _chin_exit(u)
    return r if rc is None else _smax(r, rc, SUB_KC)


def _cube_grid(n: int):
    """Cube-sphere equiangular: direções únicas + quads (índices em ``dirs``)."""
    keys: dict[tuple, int] = {}
    dirs: list[tuple] = []
    quads: list[tuple] = []
    axes = [(0, 1), (0, -1), (1, 1), (1, -1), (2, 1), (2, -1)]
    for ax, sg in axes:
        idx = [[0] * (n + 1) for _ in range(n + 1)]
        for i in range(n + 1):
            for j in range(n + 1):
                a = math.tan(math.pi / 4 * (-1 + 2 * i / n))
                b = math.tan(math.pi / 4 * (-1 + 2 * j / n))
                p = [0.0, 0.0, 0.0]
                p[ax] = float(sg)
                p[(ax + 1) % 3] = a
                p[(ax + 2) % 3] = b
                L = math.sqrt(p[0] ** 2 + p[1] ** 2 + p[2] ** 2)
                d = (p[0] / L, p[1] / L, p[2] / L)
                key = (round(d[0], 9), round(d[1], 9), round(d[2], 9))
                if key not in keys:
                    keys[key] = len(dirs)
                    dirs.append(d)
                idx[i][j] = keys[key]
        for i in range(n):
            for j in range(n):
                q = (idx[i][j], idx[i + 1][j], idx[i + 1][j + 1], idx[i][j + 1])
                # orientação para fora: normal (b−a)×(d−a) deve apontar como a direção
                quads.append(q if sg > 0 else (q[0], q[3], q[2], q[1]))
    return dirs, quads


def build_head_mass(spec, anat, submental: bool = False) -> HeadResult:
    """``submental=True`` ⇒ variante A2b (canto mentoniano); False ⇒ Fase A tal como medida."""
    rfun = radial_a2 if submental else radial
    b = MeshBuilder("head")
    h = anat.h
    s = h / H_NORM                                   # m por unidade normalizada (mm@H226)
    z_men = anat.z("chin")
    y0 = Y0_FRAC * h
    dirs, quads = _cube_grid(GRID_N)
    ids = []
    cx, cy, cz = CENTRE
    for d in dirs:
        r = rfun(d)
        # referencial normalizado → mundo; x do spec é o mesmo eixo lateral
        xn, yn, zn = cx + r * d[0], cy + r * d[1], cz + r * d[2]
        ids.append(b.add_vert(Vector((xn * s, y0 + yn * s, z_men + zn * s)), "skin", (0.5, 0.5)))
    for q in quads:
        b.add_face(tuple(ids[i] for i in q), material="skin")
    # contrato S3.7: a casca da cabeça regista anéis ``skull.<k>`` (o merge prefixa
    # ``head.``), de cima para baixo — os instrumentos J1/F1/F2 identificam a cabeça
    # por este registo.  A grelha cubo-esfera não tem latitudes exactas: as faixas
    # são z quantizado a 1 mm do mundo (identidade explícita, não geometria).
    bands: dict[int, list[int]] = {}
    for vi in ids:
        bands.setdefault(int(round(b.verts[vi].z * 1000.0)), []).append(vi)
    for k, (_zq, band) in enumerate(sorted(bands.items(), reverse=True)):
        b.rings[f"skull.{k}"] = sorted(band)
    # orientação: garantir normais para fora (verifica a 1.ª face; a grelha é consistente)
    _orient_outward(b, Vector((0.0, y0 + cy * s, z_men + cz * s)))

    # regiões: o couro cabeludo segue a mesma regra da cabeça anterior (o cabelo usa-o)
    c = anat.head_center()
    rx, ry, rz = anat.head_radii()
    hairline_z = anat.z("hairline")
    regions = {"scalp": [], "eyelid": [], "brow": [], "lip": [], "nostril": []}
    for i, p in enumerate(b.verts):
        dz = p.z - hairline_z
        on_top = (dz > -0.012 * h) and ((p - c).z > 0.02 * h or p.y < c.y + 0.15 * ry)
        front_low = p.y > c.y - 0.10 * ry and p.z < hairline_z
        if on_top and not front_low:
            b.regions[i] = "scalp"
            regions["scalp"].append(i)
    for i in regions["scalp"]:
        b.set_group("scalp", i, 1.0)
    return HeadResult(builder=b, rings={}, regions=regions, openings={})


def _orient_outward(b: MeshBuilder, centre: Vector) -> None:
    f = b.faces[0]
    a, bb, cc = (b.verts[i] for i in f[:3])
    n = (bb - a).cross(cc - a)
    mid = (a + bb + cc) / 3.0
    if n.dot(mid - centre) < 0:
        b.faces = [tuple(reversed(f)) for f in b.faces]
