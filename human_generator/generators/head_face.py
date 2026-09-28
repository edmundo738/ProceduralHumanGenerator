# -*- coding: utf-8 -*-
"""HEAD FACE v1 — cabeça com face: massas + campos anatómicos + camada estatística + olhos.

Ativa com ``HCG_HEAD=faceB`` (a build por omissão NÃO muda; pins inalterados).

    r(u) = r_massas(u)            casca de massas R1 + canto mentoniano A2b, com as duas
                                  correções de continuidade (head_mass.radial_cont_a2)
         + F(u)                   campos anatómicos com nome (face_fields; parâmetros
                                  ajustados ao detalhe médio das refs — fit_face.py)
         + K(u)                   camada corretiva estatística: o detalhe médio das refs
                                  (alinhadas por marcos) que os campos ainda não explicam
                                  (data/face_detail_v1.bin; bake_detail.py)
    olho: globo (raio 12 mm, centro medido nas refs) + fenda palpebral em amêndoa (marcos
          médios) + pálpebras que assentam no globo (face_fields.eye_blend).

Malha: cube-sphere GRADUADA — a densidade de nós é escolhida por eixo do cubo (x
concentrado na largura da face, y na frente, z nas alturas da face); as linhas da
grelha são planos coordenados, por isso as faces do cubo partilham as arestas
(100 % quads, sem junções em T).  Nós em x espelhados ⇒ malha simétrica exata.

Referencial igual ao de head_mass (mm@H226, z = 0 mentón, y = 0 centro g–op).
"""
from __future__ import annotations

import json
import math
import os
from array import array

from ..core._math import Vector
from ..core.topology import MeshBuilder
from . import face_fields as FF
from . import head_mass as HM
from .head import HeadResult

DATA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
GRID_N = 72                  # intervalos por eixo (par ⇒ x = 0 é linha de nós)
EYE_R = 12.0                 # globo (FACT: diâmetro axial ≈ 24 mm)
IRIS_DEG = 31.0              # meia-abertura angular da íris (≈ 12 mm de diâmetro)

_CACHE: dict = {}


def _load():
    if "fields" in _CACHE:
        return _CACHE
    cfg = json.load(open(os.path.join(DATA, "face_fields_v1.json"), encoding="utf-8"))
    _CACHE["fields"] = [tuple(p) for p in cfg["fields"]]
    _CACHE["eye"] = cfg["eye"]
    meta = json.load(open(os.path.join(DATA, "face_detail_v1.json"), encoding="utf-8"))
    a = array("h")
    with open(os.path.join(DATA, "face_detail_v1.bin"), "rb") as fh:
        a.frombytes(fh.read())
    if a.itemsize != 2:
        raise RuntimeError("face_detail: int16 esperado")
    import sys
    if sys.byteorder != "little":
        a.byteswap()
    _CACHE["K"] = a
    _CACHE["meta"] = meta
    return _CACHE


def detail(u: tuple) -> float:
    """Camada corretiva K(u) (mm), interpolação bilinear em (az, el)."""
    c = _load()
    m, K = c["meta"], c["K"]
    ux, uy, uz = u
    az = math.degrees(math.atan2(ux, uy))
    el = math.degrees(math.asin(max(-1.0, min(1.0, uz))))
    fa = (az - m["az0"]) / m["step"]
    fe = (el - m["el0"]) / m["step"]
    na, ne = m["n_az"], m["n_el"]
    if fa < 0 or fe < 0 or fa > na - 1 or fe > ne - 1:
        return 0.0
    ia, ie = min(int(fa), na - 2), min(int(fe), ne - 2)
    ta, te = fa - ia, fe - ie
    k0 = ie * na + ia
    k1 = k0 + na
    v = (K[k0] * (1 - ta) + K[k0 + 1] * ta) * (1 - te) + (K[k1] * (1 - ta) + K[k1 + 1] * ta) * te
    return v * m["unit_mm"]


def radial_face(u: tuple) -> float:
    c = _load()
    r = HM.radial_cont_a2(u) + FF.field(FF.PYXP, c["fields"], *u) + detail(u)
    rr, _d = FF.eye_blend(FF.PYXP, r, u[0], u[1], u[2], HM.CENTRE, c["eye"])
    return rr


# --------------------------------------------------------------------------- grelha
def _nodes(n: int, dens, symmetric: bool = False) -> list[float]:
    """n+1 nós em [−1, 1] com densidade ∝ dens(s) (inversão da CDF numérica)."""
    M = 4000
    ss = [-1.0 + 2.0 * i / M for i in range(M + 1)]
    cdf = [0.0]
    for i in range(M):
        cdf.append(cdf[-1] + 0.5 * (dens(ss[i]) + dens(ss[i + 1])) * (ss[i + 1] - ss[i]))
    tot = cdf[-1]
    out, j = [], 0
    for k in range(n + 1):
        t = tot * k / n
        while j < M - 1 and cdf[j + 1] < t:
            j += 1
        f = (t - cdf[j]) / max(1e-15, cdf[j + 1] - cdf[j])
        out.append(ss[j] + f * (ss[j + 1] - ss[j]))
    out[0], out[-1] = -1.0, 1.0
    if symmetric:
        h = n // 2
        for k in range(h + 1):
            v = 0.5 * (out[n - k] - out[k])
            out[n - k], out[k] = v, -v
        out[h] = 0.0
    return out


def _g(s: float, c: float, w: float) -> float:
    return math.exp(-((s - c) / w) ** 2)


# densidades (ENGINEERING JUDGMENT, declarado): picos onde estão olhos, nariz e boca
DENS = {
    0: lambda s: 1.0 + 3.0 * _g(s, 0.0, 0.62),                                   # x: largura da face
    1: lambda s: 1.0 + 2.5 * _g(s, 0.8, 0.35) + 2.5 * _g(s, -0.30, 0.30),        # y: frente + orelha
    2: lambda s: 1.0 + 3.0 * _g(s, -0.45, 0.55),                                 # z: alturas da face
}


def graded_cube_grid(n: int):
    nodes = {k: _nodes(n, DENS[k], symmetric=(k == 0)) for k in range(3)}
    tanv = {k: [math.tan(math.pi / 4 * s) for s in nodes[k]] for k in range(3)}
    keys: dict[tuple, int] = {}
    dirs: list[tuple] = []
    quads: list[tuple] = []
    for ax, sg in [(0, 1), (0, -1), (1, 1), (1, -1), (2, 1), (2, -1)]:
        a1, a2 = (ax + 1) % 3, (ax + 2) % 3
        idx = [[0] * (n + 1) for _ in range(n + 1)]
        for i in range(n + 1):
            for j in range(n + 1):
                p = [0.0, 0.0, 0.0]
                p[ax] = float(sg)
                p[a1] = tanv[a1][i]
                p[a2] = tanv[a2][j]
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
                quads.append(q if sg > 0 else (q[0], q[3], q[2], q[1]))
    return dirs, quads


# --------------------------------------------------------------------------- olhos
def _add_eyeball(b: MeshBuilder, to_world, G: tuple, side: int, nlat: int = 16, nlon: int = 24) -> None:
    """Globo lat/long com o polo na frente (+y); íris = calote frontal (material 'iris');
    córnea: calote de raio 7.8 mm, ~0.7 mm saliente (FACT: raio de curvatura ≈ 7.8 mm)."""
    gx, gy, gz = side * G[0], G[1], G[2]
    rows = []
    for i in range(1, nlat):
        th = math.pi * i / nlat                       # 0 = frente
        row = []
        for j in range(nlon):
            ph = 2 * math.pi * j / nlon
            r = EYE_R
            if th < math.radians(38):                 # córnea (calote que se funde no globo)
                t = 1.0 - th / math.radians(38)
                r += 0.7 * t * t * (3 - 2 * t)
            dx = r * math.sin(th) * math.cos(ph)
            dz = r * math.sin(th) * math.sin(ph)
            dy = r * math.cos(th)
            row.append(b.add_vert(to_world(gx + dx, gy + dy, gz + dz), "eye", (j / nlon, i / nlat)))
        rows.append(row)
    front = b.add_vert(to_world(gx, gy + EYE_R + 0.7, gz), "eye", (0.5, 0.0))
    back = b.add_vert(to_world(gx, gy - EYE_R, gz), "eye", (0.5, 1.0))
    iris_rows = sum(1 for i in range(1, nlat) if math.pi * i / nlat < math.radians(IRIS_DEG))
    for j in range(nlon):
        j2 = (j + 1) % nlon
        b.add_face((front, rows[0][j2], rows[0][j]) if side > 0 else (front, rows[0][j2], rows[0][j]),
                   material="iris")
        for i in range(len(rows) - 1):
            mat = "iris" if i + 1 < iris_rows else "eye"
            b.add_face((rows[i][j], rows[i][j2], rows[i + 1][j2], rows[i + 1][j]), material=mat)
        b.add_face((back, rows[-1][j], rows[-1][j2]), material="eye")


def build_head_face(spec, anat) -> HeadResult:
    c = _load()
    b = MeshBuilder("head")
    h = anat.h
    s = h / HM.H_NORM
    z_men = anat.z("chin")
    y0 = HM.Y0_FRAC * h
    cx, cy, cz = HM.CENTRE

    def to_world(xn, yn, zn):
        return Vector((xn * s, y0 + yn * s, z_men + zn * s))

    dirs, quads = graded_cube_grid(GRID_N)
    ids = []
    rcache: dict = {}
    for d in dirs:
        # simetria exata: avaliar sempre no lado x ≥ 0 e espelhar
        dd = (abs(d[0]), d[1], d[2])
        key = (round(dd[0], 9), round(dd[1], 9), round(dd[2], 9))
        r = rcache.get(key)
        if r is None:
            r = rcache[key] = radial_face(dd)
        xn = math.copysign(r * dd[0], d[0]) if d[0] != 0 else 0.0
        ids.append(b.add_vert(to_world(cx + xn, cy + r * d[1], cz + r * d[2]), "skin", (0.5, 0.5)))
    for q in quads:
        b.add_face(tuple(ids[i] for i in q), material="skin")
    bands: dict[int, list[int]] = {}
    for vi in ids:
        bands.setdefault(int(round(b.verts[vi].z * 1000.0)), []).append(vi)
    for k, (_zq, band) in enumerate(sorted(bands.items(), reverse=True)):
        b.rings[f"skull.{k}"] = sorted(band)
    HM._orient_outward(b, Vector((0.0, y0 + cy * s, z_men + cz * s)))
    n_skin_faces = len(b.faces)

    # regiões (mesma regra das cabeças anteriores; o cabelo usa ``scalp``)
    cc = anat.head_center()
    rx, ry, rz = anat.head_radii()
    hairline_z = anat.z("hairline")
    regions = {"scalp": [], "eyelid": [], "brow": [], "lip": [], "nostril": []}
    for i in list(ids):
        p = b.verts[i]
        dz = p.z - hairline_z
        on_top = (dz > -0.012 * h) and ((p - cc).z > 0.02 * h or p.y < cc.y + 0.15 * ry)
        front_low = p.y > cc.y - 0.10 * ry and p.z < hairline_z
        if on_top and not front_low:
            b.regions[i] = "scalp"
            regions["scalp"].append(i)
    for i in regions["scalp"]:
        b.set_group("scalp", i, 1.0)

    G = tuple(c["eye"]["G"])
    for side in (1, -1):
        _add_eyeball(b, to_world, G, side)
    eye_info = {"eye.L": to_world(G[0], G[1], G[2]), "eye.R": to_world(-G[0], G[1], G[2]),
                "radius": EYE_R * s, "skin_faces": n_skin_faces}
    res = HeadResult(builder=b, rings={}, regions=regions, openings={})
    res.eye_info = eye_info
    return res
