# -*- coding: utf-8 -*-
"""Skull + face.

The head starts as a *cube-sphere cage* (six grids projected onto the skull
ellipsoid) — the classic box-modelling base: all quads, three clean poles per
octant, no valence disasters.  Then:

1. sagittal shaping — the anterior-inferior shell is pulled onto
   ``Anatomy.skull_front_y`` (the cranial + midface blend), giving a real
   facial profile instead of an egg;
2. feature rings — faces around eyes/mouth/nose get inset once or twice,
   producing the holding loops that keep apertures crisp under Catmull-Clark;
3. anatomy fields — brow, glabella, malar, mental, nasolabial, philtrum,
   sockets… composed into one DeformStack so everything welds smoothly;
4. ears — a surface-following helix disc + concha socket, merged in;
5. scalp / eyelid / lip / nostril vertex groups for the skin shader masks and
   for the hair scatter.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

from ..core._math import Vector, clamp, mix, smoothstep
from ..core.field import DeformStack, falloff
from ..core.topology import MeshBuilder, make_section
from ..core.rng import Rng
from .eyes import eye_axis


@dataclass
class HeadResult:
    builder: MeshBuilder
    rings: dict = field(default_factory=dict)
    regions: dict = field(default_factory=dict)
    openings: dict = field(default_factory=dict)   # S4.2: o que o corte removeu


# ----------------------------------------------------------------------------- cube sphere
def box_sphere(builder: MeshBuilder, *, center, radii, n: int = 7,
               squash_top: float = 0.06, temple_pull: float = 0.06) -> dict:
    """Closed cube-sphere grid projected onto an ellipsoid (shared edge verts)."""
    rx, ry, rz = radii
    c = Vector(center)
    pos: dict[tuple[int, int, int], Vector] = {}
    axis_dirs = [(1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)]
    for ai, (ax, ay, az) in enumerate(axis_dirs):
        A = Vector((ax, ay, az))
        U = Vector((ay, az, ax))          # any perpendicular pair
        if abs(A.dot(U)) > 0.5:
            U = Vector((az, ax, ay))
        T = A.cross(U).normalized()
        U = T.cross(A).normalized()
        for i in range(n + 1):
            for j in range(n + 1):
                uu = -1.0 + 2.0 * i / n
                vv = -1.0 + 2.0 * j / n
                p = (A + T * uu + U * vv)
                p = p.normalized() if p.length > 1e-9 else A
                key = _qkey(p)
                if key not in pos:
                    pos[key] = p
    # project each cube-surface direction onto the ellipsoid
    verts: dict[tuple, int] = {}
    ids: dict[tuple, int] = {}
    for key, p in pos.items():
        dx, dy, dz = p.x, p.y, p.z
        t = 1.0 / math.sqrt((dx / 1.0) ** 2 + (dy / 1.0) ** 2 + (dz / 1.0) ** 2)
        # ellipsoid intersection of the ray c + s*(dx,dy,dz)
        sx, sy, sz = dx / rx, dy / ry, dz / rz
        s = 1.0 / math.sqrt(sx * sx + sy * sy + sz * sz) if (sx or sy or sz) else rx
        q = c + Vector((dx * s, dy * s, dz * s))
        # temple/jaw taper: narrow the lower half, slight vertical squash
        lower = smoothstep(c.z + 0.05 * ry, c.z - 0.55 * rz, q.z)
        q.x *= mix(1.0, 1.0 - 0.20 - temple_pull, lower)
        q.y += (ry - abs(q.y - c.y)) * 0.0
        if q.z > c.z + 0.62 * rz:  # crown flattening (vertex squash)
            q.z -= squash_top * rz * smoothstep(c.z + 0.62 * rz, c.z + rz, q.z)
        ids[key] = builder.add_vert(q, "skin", (0.5, 0.5))
    # S3.7 — o crânio não registava anéis: o instrumento não tinha como
    # identificar a casca da cabeça sem heurísticas (posição/tamanho).  As
    # latitudes (mesmo z, arredondado) passam a ser anéis nomeados
    # ``skull.<k>`` (o merge do corpo prefixa-os para ``head.skull.<k>``), de cima para baixo.
    bands: dict[float, list[int]] = {}
    for key, vi in ids.items():
        bands.setdefault(round(builder.verts[vi].z, 6), []).append(vi)
    for k, (zq, band) in enumerate(sorted(bands.items(), reverse=True)):
        builder.rings[f"skull.{k}"] = sorted(band)

    # faces: for every grid cell of every axis face
    def face_key(ai, i, j):
        ax, ay, az = axis_dirs[ai]
        A = Vector((ax, ay, az))
        U = Vector((ay, az, ax))
        if abs(A.dot(U)) > 0.5:
            U = Vector((az, ax, ay))
        T = A.cross(U).normalized()
        U = T.cross(A).normalized()
        uu = -1.0 + 2.0 * i / n
        vv = -1.0 + 2.0 * j / n
        p = (A + T * uu + U * vv).normalized()
        return _qkey(p)

    for ai in range(6):
        for i in range(n):
            for j in range(n):
                a = ids.get(face_key(ai, i, j))
                b = ids.get(face_key(ai, i + 1, j))
                cc = ids.get(face_key(ai, i + 1, j + 1))
                d = ids.get(face_key(ai, i, j + 1))
                if None in (a, b, cc, d):
                    continue
                # outward orientation
                builder.add_face((a, b, cc, d), material="skin")
    before = len(builder.faces)
    # Drop collapsed faces AND their material entries together: filtering only
    # ``faces`` desynchronised ``face_mat`` (it stayed longer), which silently
    # shifted the material of every later face in the builder (measured below).
    kept = [(f, m) for f, m in zip(builder.faces, builder.face_mat)
            if len(set(f)) == len(f)]
    builder.faces = [f for f, _ in kept]
    builder.face_mat = [m for _, m in kept]
    return {"n": len(ids), "keys": len(pos), "faces": len(builder.faces),
            "faces_dropped": before - len(builder.faces)}


def _qkey(p: Vector) -> tuple[int, int, int]:
    return (round(p.x * 1e5), round(p.y * 1e5), round(p.z * 1e5))


# ----------------------------------------------------------------------------- feature loops
def _seg_dist(p: Vector, a: Vector, b: Vector) -> float:
    ab = b - a
    L2 = ab.length_squared
    t = 0.0 if L2 < 1e-18 else max(0.0, min(1.0, (p - a).dot(ab) / L2))
    return (p - (a + ab * t)).length


def poly_dist(p: Vector, pts: list[Vector]) -> float:
    """Distância de um ponto a um polígono convexo (não ao seu centro).

    S4.2 — a selecção por DISTÂNCIA AO CENTRO da face era o bloqueio medido do
    refinamento local: a célula do crânio mede ~25 mm, logo um alvo a 8 mm do
    centro de uma face nunca a seleccionava e o refinamento nunca chegava abaixo
    de uma célula (medido: a janela da fissura palpebral de 30×10 mm continha
    **2 vértices** e a das narinas **0** — sem vértices não há abertura
    possível).  Aqui a distância é a verdadeira distância ao quad: projecção no
    plano quando cai dentro, senão a distância mínima às arestas.
    """
    if len(pts) < 3:
        return min((p - q).length for q in pts)
    n = (pts[1] - pts[0]).cross(pts[2] - pts[0])
    if n.length_squared < 1e-18:
        return min((p - q).length for q in pts)
    n = n.normalized()
    d = (p - pts[0]).dot(n)
    proj = p - n * d
    # dentro? todos os produtos externos com o mesmo sentido da normal
    inside = True
    for k in range(len(pts)):
        a, b = pts[k], pts[(k + 1) % len(pts)]
        if (b - a).cross(proj - a).dot(n) < -1e-12:
            inside = False
            break
    if inside:
        return abs(d)
    return min(_seg_dist(p, pts[k], pts[(k + 1) % len(pts)]) for k in range(len(pts)))


def add_feature_loops(builder: MeshBuilder, targets: list[tuple[Vector, float, int]],
                      shrink: float = 0.34) -> None:
    """Inset faces near landmark targets (recursively) = holding loops.

    Works directly on the builder (pure python, deterministic): each selected
    quad gets replaced by a centre-shrunk quad plus a 4-quad collar; collars
    are creased so subdivision keeps aperture rims from melting.

    S4.2 — a selecção passou a ser por ``poly_dist`` (ver aí o porquê medido) e
    o número de iterações de CADA alvo passa a ser respeitado (antes o ``it``
    por alvo só definia o máximo: um alvo com ``it=1`` era insuflado em todas as
    passagens do alvo com mais iterações, o que não era o contrato declarado).
    """
    targets = [(Vector(p), r, it) for p, r, it in targets]
    npass = max(it for _, _, it in targets) if targets else 1
    for pass_i in range(npass):
        new_faces = []
        new_mats = []
        changed = 0
        for fi, f in enumerate(builder.faces):
            if len(f) != 4:
                new_faces.append(f)
                new_mats.append(builder.face_mat[fi])
                continue
            pts = [builder.verts[i] for i in f]
            near = any(pass_i < it and poly_dist(p, pts) < r for p, r, it in targets)
            if not near:
                new_faces.append(f)
                new_mats.append(builder.face_mat[fi])
                continue
            mat = builder.face_mat[fi]
            a, b, c, d = f
            pa, pb, pc, pd = (builder.verts[i] for i in (a, b, c, d))
            cen = (pa + pb + pc + pd) / 4
            inner = [builder.add_vert(p + (cen - p) * shrink, builder.regions[v], builder.uvs[v])
                     for p, v in ((pa, a), (pb, b), (pc, c), (pd, d))]
            ia, ib, ic, idd = inner
            new_faces += [(a, b, ib, ia), (b, c, ic, ib), (c, d, idd, ic), (d, a, ia, idd)]
            new_mats += [mat] * 4
            # inner quad handled next pass
            new_faces.append((ia, ib, ic, idd))
            new_mats.append(mat)
            changed += 1
            for pair in ((a, ia), (b, ib), (c, ic), (d, idd)):
                builder.crease(pair[0], pair[1], 0.22)
        builder.faces = new_faces
        builder.face_mat = new_mats
    return changed


# ---------------------------------------------------------------------- openings (S4.2)
def _ellipse_q(p: Vector, c: Vector, e1: Vector, e2: Vector, a: float, b: float) -> float:
    """Valor normalizado da elipse ((p−c)·e1/a)² + ((p−c)·e2/b)²."""
    d = p - c
    return (d.dot(e1) / a) ** 2 + (d.dot(e2) / b) ** 2


def cut_openings(builder: MeshBuilder, openings: list[dict]) -> dict:
    """Abre buracos na casca e arruma o builder (S4.2).

    Medido antes desta função (baseline ``0e75a75``): o crânio é um cube-sphere
    FECHADO — não existe um único polígono removido na órbita, na boca ou nas
    narinas — logo o globo ocular, as pálpebras e os lábios estão todos dentro
    da pele.  Esta função:

    1. remove as faces cujo centro cai dentro de uma abertura;
    2. **projecta para a curva da abertura** os vértices que ficam dentro dela,
       para o rebordo ser a elipse declarada e não a fronteira irregular da
       grelha (o rebordo é o que a subdivisão vai segurar);
    3. compacta os vértices que ficaram sem faces e reindexa TODAS as
       estruturas paralelas (faces, região, uv, grupos, creases, anéis) — um
       índice dessincronizado parte o audit de forma silenciosa.
    """
    n_faces0, n_verts0 = len(builder.faces), len(builder.verts)
    drop: dict[str, int] = {}
    keep_faces, keep_mats = [], []
    rim: dict[int, str] = {}
    for f, mat in zip(builder.faces, builder.face_mat):
        # S4.2 — o critério é "QUALQUER vértice dentro" e não "centro dentro":
        # medido, com o centro a órbita ficava com 15.7 mm de largura (o buraco
        # era só o miolo onde havia centros; as pontas da fissura de 30 mm não
        # tinham nenhum centro dentro) e as narinas com 5.9 mm.  Como o rebordo
        # é projectado na elipse declarada, o buraco passa a ser exactamente a
        # elipse.
        # S4.2 — remover se QUALQUER vértice está dentro **ou** o CENTRO da face
        # está dentro (a união dos dois critérios).  Medido: só com "qualquer
        # vértice" ficavam faces-PONTE a atravessar a abertura do olho (todos os
        # vértices fora da fissura, face deitada sobre ela); o raio lançado do
        # centro do globo batia numa dessas faces a 4.2 mm do centro, dentro de
        # um globo de 12.3 mm de raio.  Sozinho, o critério do centro era o que
        # dava uma órbita de 15.7 mm (muito curta).  Juntos: buraco completo.
        hit = None
        ctr = sum((builder.verts[i] for i in f), Vector((0, 0, 0))) / len(f)
        pts_f = [builder.verts[i] for i in f]
        mids = [(pts_f[k] + pts_f[(k + 1) % len(pts_f)]) * 0.5 for k in range(len(pts_f))]
        for op in openings:
            if any(op["inside"](builder.verts[i]) for i in f) or op["inside"](ctr) \
                    or any(op["inside"](m) for m in mids):
                hit = op["name"]
                break
        if hit is None:
            keep_faces.append(f)
            keep_mats.append(mat)
        else:
            drop[hit] = drop.get(hit, 0) + 1
            for i in f:
                rim.setdefault(i, hit)
    builder.faces = keep_faces
    builder.face_mat = keep_mats

    # S4.2 — o rebordo não é o interior: os vértices das faces REMOVIDAS que
    # continuam a ser usados pelas faces vizinhas são exactamente a fronteira do
    # buraco.  Sem os projectar, o laço da órbita media 21.0 × 18.6 mm em vez da
    # fissura declarada de 30 × 10 mm (medido) — o buraco era redondo e não uma
    # fissura.  Projectar o interior *e* o rebordo dá a elipse exacta; como o
    # interior é depois compactado, não há vértices coincidentes.
    projected = 0
    by_name = {op["name"]: op for op in openings}
    for i, name in rim.items():
        op = by_name[name]
        builder.verts[i] = op["project"](builder.verts[i])
        projected += 1

    # S4.2 — ESPAÇAMENTO UNIFORME do rebordo.  Medido: a projecção independente
    # deixava dois vértices vizinhos a ~0.01 mm um do outro (na zona em que a
    # grelha é quase paralela à elipse) e o ``dissolve_degenerate`` do pipeline
    # colapsava essa aresta criando um PENTÁGONO na malha entregue — 2 ngons
    # (5 lados, 24 mm², em ±41.7 mm, 60.0 mm, 1561.9 mm, simétricos).  O
    # rebordo passa a ser reamostrado com passo angular uniforme: o buraco fica
    # a elipse declarada, os vértices ficam separados (o passo mínimo é
    # 2π·a/N ≈ 2.9 mm na órbita) e a malha fica regular para a subdivisão.
    rim_by_name: dict[str, list[int]] = {}
    for i, name in rim.items():
        rim_by_name.setdefault(name, []).append(i)
    for name, ids in rim_by_name.items():
        op = by_name[name]
        pts = sorted(((op["param"](builder.verts[i]), i) for i in ids), key=lambda kv: kv[0])
        n_rim = len(pts)
        for k, (_t, i) in enumerate(pts):
            builder.verts[i] = op["point"](2.0 * math.pi * k / n_rim, builder.verts[i])
        if op.get("sphere") is not None:
            sc, sr = op["sphere"]
            for i in ids:
                d = builder.verts[i] - sc
                if d.length > 1e-9:
                    builder.verts[i] = sc + d * (sr / d.length)

    # S4.2 — SIMETRIA EXACTA do rebordo.  Medido: a re-amostragem independente
    # de cada lado deixava o rebordo esquerdo e o direito diferentes (órbita
    # 22.9 × 6.7 mm contra 22.2 × 5.9; narina 11.6 contra 11.0) porque o
    # conjunto de vértices de partida não é espelho exacto.  As aberturas aos
    # pares (órbita, narina) passam a ser espelhadas: a direita recebe a imagem
    # da esquerda (correspondência pelo vizinho mais próximo do ponto espelhado).
    _mirror_pairs = tuple((a, a.replace(".L", ".R")) for a in rim_by_name
                          if a.endswith(".L") and a.replace(".L", ".R") in rim_by_name)
    for left, right in _mirror_pairs:
        lids, rids = rim_by_name[left], rim_by_name[right]
        if len(lids) != len(rids):
            continue
        pool = [(builder.verts[i], i) for i in lids]
        used = set()
        for ri in rids:
            mp = builder.verts[ri]
            target = Vector((-mp.x, mp.y, mp.z))
            best = None
            for pos, li in pool:
                if li in used:
                    continue
                d = (pos - target).length
                if best is None or d < best[0]:
                    best = (d, li, pos)
            if best is None or best[0] > 0.010:
                continue
            used.add(best[1])
            lp = builder.verts[best[1]]
            builder.verts[ri] = Vector((-lp.x, lp.y, lp.z))

    used = sorted({i for f in builder.faces for i in f})
    remap = {old: new for new, old in enumerate(used)}
    builder.verts = [builder.verts[i] for i in used]
    builder.regions = [builder.regions[i] for i in used]
    builder.uvs = [builder.uvs[i] for i in used]
    builder.faces = [[remap[i] for i in f] for f in builder.faces]
    builder.groups = {n: {remap[i]: w for i, w in d.items() if i in remap}
                      for n, d in builder.groups.items()}
    builder.creases = {tuple(sorted((remap[a], remap[b]))): w
                       for (a, b), w in builder.creases.items() if a in remap and b in remap}
    builder.rings = {n: [remap[i] for i in ids if i in remap]
                     for n, ids in builder.rings.items()}
    return {"faces_removidas": drop, "faces_removidas_total": n_faces0 - len(builder.faces),
            "verts_compactados": n_verts0 - len(builder.verts), "verts_rebordo_projectados": projected,
            "verts_na_janela": sum(1 for op in openings for v in builder.verts if op["inside"](v)),
            "faces": len(builder.faces), "verts": len(builder.verts)}


def head_openings(spec, anat, h: float) -> list[dict]:
    """Aberturas declaradas da cabeça (S4.2): órbita ×2, boca, narinas ×2.

    Tamanhos: fissura palpebral 30 × 10 mm (F5: [24,32] × [7,13]), boca 42 × 5 mm
    (menor que a boca de lábios medida, 49.6 mm — critério A2), narina
    9.8 × 7.2 × 5.8 mm por lado nos centros medidos da base do nariz.
    """
    lm = anat.landmarks
    hc = Vector(anat.head_center())
    ops: list[dict] = []
    for side, tag in ((1, "L"), (-1, "R")):
        c = Vector(lm[f"eye.{tag}"])                 # centro do globo
        # S4.2 — a fissura é uma feição da PELE, não do plano equatorial do
        # globo.  Medido com o plano ⊥ ao eixo do olho: o eixo está inclinado
        # ~38° para fora nesta elipse craniana e o laço da órbita saía com
        # 19.1 × 17.2 × 10.0 mm (uma elipse *de perfil*), em vez da fissura de
        # 30 × 10 mm.  O plano passa a ser o da superfície no ponto do olho:
        # ``right`` horizontal da pele, ``up`` vertical da pele.
        surf = anat.face_front(c.x, c.z, 0.0)
        n = (surf - hc).normalized()
        right = Vector((0, 0, 1.0)).cross(n)
        right = right.normalized() if right.length_squared > 1e-8 else Vector((1.0, 0, 0))
        up = n.cross(right).normalized()
        S = surf + n * 0.002
        # S4.2 — a JANELA DE CORTE é maior que a elipse projectada: as faces
        # caem por "qualquer vértice dentro" e depois o rebordo é projectado na
        # elipse.  Se a janela fosse igual à elipse, as pontas da fissura (onde
        # a face é maior que a elipse) não teriam vértice dentro e o buraco
        # saía curto (medido: 15.7 mm em vez de 30).
        a_cut, b_cut = 0.0210, 0.0095
        a, bb = 0.0150, 0.0050
        reach_in, reach_out = 0.030, 0.008
        # O rebordo não pode estar mais fundo que a órbita declarada: medido,
        # 5 vértices a −10.6 mm (o *inset* das feature loops puxa-os para dentro
        # do crânio) e 1 a +4.3 mm.  Limite: −8.5 mm..+2.5 mm.
        dn_lo, dn_hi = -0.0085, 0.0025

        def inside(p, S=S, n=n, right=right, up=up, ac=a_cut, bc=b_cut,
                   ri=reach_in, ro=reach_out):
            dn = (p - S).dot(n)
            return -ri < dn < ro and _ellipse_q(p, S, right, up, ac, bc) < 1.0

        def project(p, S=S, n=n, right=right, up=up, a=a, bb=bb,
                    lo=dn_lo, hi=dn_hi):
            d = p - S
            q = (d.dot(right) / a) ** 2 + (d.dot(up) / bb) ** 2
            k = 1.0 / math.sqrt(q) if q > 1e-18 else 1.0
            dn = clamp(d.dot(n), lo, hi)
            return S + right * (d.dot(right) * k) + up * (d.dot(up) * k) + n * dn

        def param(p, S=S, right=right, up=up, a=a, bb=bb):
            d = p - S
            return math.atan2(d.dot(up) / bb, d.dot(right) / a)

        def point(t, p, S=S, n=n, right=right, up=up, a=a, bb=bb, lo=dn_lo, hi=dn_hi):
            dn = clamp((p - S).dot(n), lo, hi)
            return S + right * (a * math.cos(t)) + up * (bb * math.sin(t)) + n * dn

        ops.append({"name": f"orbita.{tag}", "inside": inside, "project": project,
                    "param": param, "point": point,
                    # S4.2b — o rebordo do olho assenta na ESFERA da pálpebra
                    # (raio = raio do globo + 1.5 mm, centro no centro do globo):
                    # medido, com o limite de profundidade antigo (−8.5 mm, preso
                    # a uma superfície que já não existe) o rebordo voltava a
                    # ficar dentro do globo (2 vértices a 10.9 e 11.6 mm de um
                    # raio de 12.3).
                    "sphere": (c, 0.0555 * h + 0.0015)})

    mc = Vector(lm["mouth"])
    # idem: a janela de corte tem 12 mm de altura (a boca segue a curvatura da
    # cara; uma janela de 5 mm não apanha as comissuras) e a elipse projectada
    # tem 42 × 5 mm.
    a_mo, b_cut_mo, a_proj, b_proj, depth = 0.0245, 0.0080, 0.0210, 0.0025, 0.020
    ops.append({"name": "oral",
                "inside": lambda p, c=mc, a=a_mo, b=b_cut_mo, d=depth: (
                    p.y > c.y - d and ((p.x - c.x) / a) ** 2 + ((p.z - c.z) / b) ** 2 < 1.0),
                "project": lambda p, c=mc, a=a_proj, b=b_proj: _project_front_ellipse(p, c, a, b),
                "param": lambda p, c=mc, a=a_proj, b=b_proj: math.atan2(
                    (p.z - c.z) / b, (p.x - c.x) / a),
                "point": lambda t, p, c=mc, a=a_proj, b=b_proj: Vector(
                    (c.x + a * math.cos(t), p.y, c.z + b * math.sin(t)))})

    nb = Vector(lm["nose_base"])
    # S4.2 — as narinas estavam a ±0.0135·H (3 mm): dentro da crista do nariz,
    # a 12 mm da pele, e não cortavam uma única face (medido: 0 removidas).
    # Ficam sob as asas, a ±0.043·H (9.6 mm).
    for sx, tag in ((1, "L"), (-1, "R")):
        cen = nb + Vector((sx * 0.043 * h, 0.002 * h, -0.010 * h))
        cut_r = (0.036 * h, 0.030 * h, 0.022 * h)     # janela de corte
        rad = (0.026 * h, 0.020 * h, 0.014 * h)       # elipse projectada

        def inside(p, cen=cen, rad=cut_r):
            d = p - cen
            return (d.x / rad[0]) ** 2 + (d.y / rad[1]) ** 2 + (d.z / rad[2]) ** 2 < 1.0

        def project(p, cen=cen, rad=rad):
            d = p - cen
            q = (d.x / rad[0]) ** 2 + (d.y / rad[1]) ** 2 + (d.z / rad[2]) ** 2
            k = 1.0 / math.sqrt(q) if q > 1e-18 else 1.0
            return cen + Vector((d.x * k, d.y * k, d.z * k))

        def param(p, cen=cen, rad=rad):
            d = p - cen
            return math.atan2(d.z / rad[2], d.x / rad[0])

        def point(t, p, cen=cen, rad=rad):
            return Vector((cen.x + rad[0] * math.cos(t), p.y, cen.z + rad[2] * math.sin(t)))

        ops.append({"name": f"narina.{tag}", "inside": inside, "project": project,
                    "param": param, "point": point})
    return ops


def _project_front_ellipse(p: Vector, c: Vector, a: float, b: float) -> Vector:
    dx, dz = p.x - c.x, p.z - c.z
    q = (dx / a) ** 2 + (dz / b) ** 2
    k = 1.0 / math.sqrt(q) if q > 1e-18 else 1.0
    return Vector((c.x + dx * k, p.y, c.z + dz * k))


# ----------------------------------------------------------------------------- ears
def add_ear(builder: MeshBuilder, anat, side: int, rng: Rng) -> None:
    """Auricle: an ellipsoid-conforming 6×8 patch (so it hugs the skull at
    every proportion), rim creased, concha hollowed by the head field stack."""
    h = anat.h
    c = Vector(anat.landmarks["ear.L" if side > 0 else "ear.R"])
    c0 = anat.head_center()
    rx, ry, rz = anat.head_radii()
    cx = 1.0 if side > 0 else -1.0
    rows, cols = 6, 8
    ear_h = 0.29 * h * anat.spec.face.ear_size
    grid = []
    for ri in range(rows):
        v = ri / (rows - 1)
        row = []
        for ci in range(cols):
            u = -1.0 + 2.0 * ci / (cols - 1)
            z = c.z + (0.5 - v) * ear_h
            y = c.y + u * ear_h * 0.34
            ty = (y - c0.y) / ry
            tz = (z - c0.z) / rz
            s = 1.0 - ty * ty - tz * tz
            s = max(0.04, s)
            x = cx * rx * math.sqrt(s) * 1.006
            # helix rim lifts off the skull toward the middle, rim crest at u≈±0.8
            rim = math.exp(-((abs(u) - 0.78) ** 2) / 0.10) * math.exp(-((v - 0.55) ** 2) / 0.30)
            x += cx * (0.0060 * h + 0.0046 * h * rim)
            # lobe droop: bottom rows relax inward-forward
            if v > 0.82:
                x -= cx * 0.0022 * h * (v - 0.82) / 0.18
            row.append(builder.add_vert(Vector((x, y, z)), "skin", (ci / (cols - 1), v)))
        grid.append(row)
    for ri in range(rows - 1):
        for ci in range(cols - 1):
            a, b = grid[ri][ci], grid[ri][ci + 1]
            cc, d = grid[ri + 1][ci], grid[ri + 1][ci + 1]
            if side > 0:
                builder.add_face((a, b, cc, d), material="skin")
            else:
                builder.add_face((a, d, cc, b), material="skin")
    builder.crease_ring([grid[r][0] for r in range(rows)], 0.30)
    builder.crease_ring([grid[r][-1] for r in range(rows)], 0.30)
    builder.crease_ring(grid[0], 0.26)
    builder.crease_ring(grid[-1], 0.18)


# ----------------------------------------------------------------------------- main
def build_head(spec, anat) -> HeadResult:
    rng = Rng(spec.seed, salt=101)
    b = MeshBuilder("head")
    h = anat.h
    s = spec.stature if hasattr(spec, "stature") else spec.body.stature
    face = spec.face
    c = anat.head_center()
    rx, ry, rz = anat.head_radii()

    # 1) cube-sphere skull
    box_sphere(b, center=c, radii=(rx * 1.015, ry * 1.015, rz * 1.015), n=9,
               squash_top=0.045, temple_pull=0.05)

    # 2) sagittal profile: the anterior shell is set to the *dominant* of the
    #    two skull shells (cranium ∪ midface/mandible block).  This is why
    #    the correction must key off surface comparison, not position: raw
    #    ellipsoid points near the chin have small y exactly where the face
    #    block is largest, and a position-based weight would sink the chin.
    lm = anat.landmarks
    #    The target ``surf = skull_front_y(x, z)`` is a function of the ray
    #    column alone, and ``edge`` depends only on (x, z) too — so blending
    #    each vertex toward it independently made every column that holds two
    #    samples collapse onto a single point wherever the weight reaches 1
    #    (measured: 8 columns -> 16 coincident verts -> 5 zero-area faces in
    #    the builder).  The eligible vertices of a column now translate
    #    rigidly instead: the exposed (front-most) vertex still lands exactly
    #    on ``surf`` — the documented intent — while the column keeps its
    #    internal spacing exactly, because a shared translation cannot change
    #    any distance inside the group.  A column whose front-most vertex is
    #    already at ``surf`` is left alone (the old code used to drag the
    #    vertices behind it onto that same point).
    columns: dict[tuple[float, float], list[int]] = {}
    for i, p in enumerate(b.verts):
        if abs(p.x) < 0.80 * rx and (c.z - 0.72 * h) < p.z < (c.z + 0.56 * h) \
                and p.y > c.y - 0.15 * ry:
            columns.setdefault((round(p.x, 9), round(p.z, 9)), []).append(i)
    for (qx, qz), idxs in columns.items():
        surf = anat.skull_front_y(qx, qz)
        # S4.1/§7.2 — a correcção era só para a FRENTE (``need <= 0`` saía).
        # Medido: o elipsoide era mais gordo que a máscara facial em 108 das 160
        # colunas frontais (até −17.7 mm), e por isso os marcos faciais (olhos,
        # boca, nariz — todos calculados sobre ``skull_front_y``) ficavam **dentro**
        # do crânio: medido, o marco ``eye`` estava 22 mm atrás da superfície e o
        # globo ocular 9.6 mm atrás da pele.  A coluna passa a ser transladada
        # para a máscara com o sinal correcto (o mecanismo de translação rígida
        # por coluna, que evita colapsos internos, mantém-se).
        need = surf - max(b.verts[i].y for i in idxs)
        if abs(need) <= 0.0002:
            continue
        edge = smoothstep(0.80 * rx, 0.52 * rx, abs(qx)) * \
            smoothstep(c.z - 0.70 * h, c.z - 0.550 * h, qz) * \
            smoothstep(c.z + 0.56 * h, c.z + 0.470 * h, qz)
        shift = need * clamp(edge, 0.0, 1.0)
        if abs(shift) < 1e-12:
            continue
        for i in idxs:
            v = b.verts[i]
            b.verts[i] = Vector((v.x, v.y + shift, v.z))

    # 3) feature loops (holding loops under subdivision)
    # S4.2 — os raios passam a COBRIR a abertura que vai ser cortada (a fissura
    # tem 30 mm de extensão, a boca 42 mm): com raio de 0.034·H (7.6 mm) à volta
    # do olho, a abertura ficaria numa única célula de 25 mm.  As iterações são
    # por alvo e explícitas (ver add_feature_loops).
    lm = anat.landmarks
    targets = [
        (lm["eye.L"], 0.070 * h, 2), (lm["eye.R"], 0.070 * h, 2),
        (lm["mouth"], 0.095 * h, 2), (lm["nose_tip"], 0.048 * h, 1),
        (lm["ear_canal.L"], 0.016 * h, 1), (lm["ear_canal.R"], 0.016 * h, 1),
    ]
    for sx in (1, -1):
        targets.append((Vector(lm["nose_base"]) + Vector((sx * 0.043 * h, 0.002 * h, -0.010 * h)),
                        0.034 * h, 2))
    add_feature_loops(b, targets, shrink=0.36)

    # 4) ears (surface patches)
    for side in (1, -1):
        add_ear(b, anat, side, rng)

    # 5) anatomy fields
    stack = DeformStack()
    # brow ridge
    for tag in ("L", "R"):
        stack.bump(lm[f"brow.{tag}"], 0.010 * h * (0.7 + 0.6 * face.brow_thickness),
                   sigma=(0.055 * h, 0.018 * h, 0.020 * h), direction=(0, 1, 0.10))
    stack.bump(lm["glabella"], 0.008 * h, sigma=(0.022 * h, 0.016 * h, 0.016 * h))
    # sockets — S4.2: a pele da pálpebra tem de ficar ao nível da pele da face
    # que a rodeia.  Medido com o socket antigo (0.0125·H, r 0.048·H): a
    # pálpebra ficava **4.9 mm dentro** da cara (y 68.3 contra pele 73.2 na
    # coluna do olho) e o globo só expunha 7 vértices.  A órbita passa a
    # 0.0245·H (5.5 mm) de profundidade com raio 0.055·H, e o rebordo
    # orbitário ganha um anel de relevo (o osso por baixo da pele).
    for tag, sgn in (("L", 1), ("R", -1)):
        stack.socket(lm[f"eye.{tag}"], 0.0245 * h * face.eye_depth,
                     radius=0.055 * h)
        # S4.2b — pálpebra CONCÊNTRICA com o globo.  Medido: sem isto, a pele da
        # cova (fundo a 9.1 mm de um centro de globo de 12.3 mm de raio) fica
        # DENTRO do globo e intersecta-o em volta da abertura — o raio lançado do
        # centro do globo ao longo do eixo do olho batia em 12 faces de pele a
        # 5–9 mm (lado esquerdo) e 4 (direito).  A pálpebra passa a assentar a
        # raio_globo + 0.0015 m (1.5 mm de espessura) dentro de um cilindro de
        # 0.030·H em torno do eixo do olho.
        e_ax = eye_axis(anat, 1 if tag == "L" else -1)
        e_surf = anat.face_front(lm[f"eye.{tag}"].x, lm[f"eye.{tag}"].z, 0.0)
        e_r = Vector((0, 0, 1.0)).cross((e_surf - Vector(anat.head_center())).normalized())
        if e_r.length_squared < 1e-8:
            e_r = Vector((1.0, 0, 0))
        e_r = e_r.normalized()
        e_u = (e_surf - Vector(anat.head_center())).normalized().cross(e_r).normalized()
        # footprint elíptica generosa: cobre a cova (raio 0.055·H = 12.2 mm) e
        # as duas pálpebras; como o conform só empurra para fora, alargar não
        # tem custo (nada acima da esfera se move).
        stack.conform(Vector(lm[f"eye.{tag}"]), 0.0555 * h + 0.0015, e_ax,
                      0.024, width2=0.016, basis=(e_r, e_u))
        stack.bump(lm[f"eye.{tag}"] + Vector((0.0, 0.0, 0.030 * h)),
                   0.0035 * h, sigma=(0.052 * h, 0.024 * h, 0.020 * h),
                   direction=(0.0, 1.0, 0.15))
        stack.bump(lm[f"eye.{tag}"] + Vector((0.0, 0.0, -0.034 * h)),
                   0.0030 * h, sigma=(0.050 * h, 0.022 * h, 0.018 * h),
                   direction=(0.0, 1.0, -0.20))
    # nose — sampled from the cartilage line: skin is lifted onto the
    # root→tip profile (gaussians anchored on the SURFACE, amplitude =
    # landmark-minus-surface, so the field always blends flush at its rim).
    #
    # S4.2 — MEDIDO no baseline (`0e75a75`): com sigma_z = 0.9·H (200 mm) e
    # sigma_x = (wid+0.006)·H ≈ 4 mm, este campo não fazia um nariz — fazia um
    # FOCINHO.  A pele da linha média ficava 25–35 mm À FRENTE da máscara facial
    # em metade da cara (excesso máximo +34.9 mm, medido a z=1509 mm), o que
    # punha os marcos faciais (boca, nariz, globo) DENTRO da cabeça e tornava
    # impossível colocar as aberturas de S4.2 por marcos.  A gaussiana era
    # estreitíssima em x e larguíssima em z — exactamente ao contrário da
    # anatomia.  Agora: sigma_z = 0.10·H (22 mm, o nariz não chega à boca nem à
    # testa) e sigma_x = (0.034 + wid)·H ≈ 8–11 mm (a largura alar canónica é
    # 31–35 mm); as asas do nariz passam a estar a ±0.040·H (8.9 mm) e não a
    # ±0.016·H (3.6 mm, dentro da própria crista).
    proj = spec.face.nose_tip_projection
    tip_extra = 0.004 * h * proj
    # Medido: gaussianas sobrepostas SOMAM — com 4 amostras ao longo de
    # root→tip a crista dava +32 mm na ponta (alvo: +17 mm, a protrusão do
    # marco).  Com DUAS amostras e sigma_z = 0.10·H a soma reproduz o perfil do
    # marco (ponta 18.8 vs 18.2 mm; meio do nariz 10.1 vs 10.2 mm — medido).
    for k, wid in ((0.0, 0.030), (1.0, 0.042)):
        q = lm["nose_root"].lerp(lm["nose_tip"], k)
        y0 = anat.skull_front_y(0.0, q.z)
        amp = max(0.0006, q.y - y0) + tip_extra * k * k
        stack.bump(Vector((0.0, y0, q.z)), amp,
                   sigma=(wid * h, 0.5 * h, 0.10 * h),
                   direction=(0, 1, 0.18))
    stack.bump(Vector((0.0, anat.skull_front_y(0.0, lm["nose_tip"].z) - 0.001 * h,
                        lm["nose_tip"].z)), tip_extra + 0.004 * h,
               sigma=(0.030 * h, 0.016 * h, 0.020 * h), direction=(0, 1, -0.30))
    for sx in (1, -1):
        # S4.2 — asas: medida a largura alar na pele, dava 21.7 mm com as asas a
        # ±0.040·H (canónico F7: 31–35 mm).  Passam a ±0.050·H (11.1 mm) com
        # sigma_x 0.020·H.
        stack.bump(lm["nose_tip"] + Vector((sx * 0.050 * h, -0.006 * h, -0.007 * h)),
                   0.0048 * h * spec.face.nostril_flare,
                   sigma=(0.020 * h, 0.014 * h, 0.013 * h),
                   direction=(sx * 0.45, 0.85, -0.30))
    stack.bump(lm["nose_base"], 0.0040 * h, sigma=(0.040 * h, 0.013 * h, 0.014 * h))
    # cheeks / malar
    for tag in ("L", "R"):
        stack.bump(lm[f"cheek.{tag}"], 0.010 * h * (0.5 + face.cheek_fullness),
                   sigma=(0.050 * h, 0.030 * h, 0.045 * h), direction=(0.25 * (1 if tag == "L" else -1), 0.8, -0.2))
    # chin / jaw
    stack.bump(lm["chin_front"], 0.0090 * h * face.chin_projection,
               sigma=(0.042 * h, 0.024 * h, 0.032 * h), direction=(0, 1, -0.12))
    for tag, sx in (("L", 1), ("R", -1)):
        stack.bump(lm[f"jaw_angle.{tag}"], 0.006 * h,
                   sigma=(0.020 * h, 0.020 * h, 0.030 * h), direction=(sx * 0.4, 0.3, -0.3))
    # lips mound + philtrum groove
    stack.bump(lm["mouth"], 0.0040 * h * face.lip_fullness,
               sigma=(0.055 * h * face.mouth_width, 0.020 * h, 0.026 * h), direction=(0, 1, 0))
    stack.bump(lm["philtrum"], -0.0022 * h * face.philtrum_length,
               sigma=(0.012 * h, 0.016 * h, 0.016 * h), direction=(0, 1, 0))
    # nostril openings + ear conchae
    # S4.2 — os dentes das narinas estavam a ±0.0135·H (3 mm) com raio 1.7 mm:
    # dentro da crista do nariz e sem chegar à pele.  Passam para ±0.043·H
    # (9.6 mm, sob as asas) com raio 0.020·H (4.4 mm).
    for sx in (1, -1):
        stack.socket(lm["nose_base"] + Vector((sx * 0.043 * h, 0.004 * h, -0.010 * h)),
                     0.0055 * h * spec.face.nostril_flare, radius=0.020 * h)
    for side in (1, -1):
        ec = Vector(anat.landmarks["ear.L" if side > 0 else "ear.R"])
        stack.socket(ec + Vector((-0.010 * h * side * side, 0.006 * h, -0.004 * h)),
                     0.0052 * h, radius=0.020 * h)
        # direction: push skin toward skull (-x·side)
        stack.items[-1].direction = Vector((-side, 0.10, 0.0)).normalized()
        stack.items[-1].sigma = (0.020 * h, 0.020 * h, 0.026 * h)
        stack.items[-1].centre = ec + Vector((-0.002 * h * side, 0.008 * h, -0.006 * h))
    # temple hollow + neck blend
    for tag in ("L", "R"):
        stack.bump(lm[f"temple.{tag}"], -0.0035 * h, sigma=(0.045 * h, 0.030 * h, 0.055 * h))
    stack.bump(Vector((c.x, c.y - 0.10 * h, anat.z("chin") - 0.10 * h)), 0.006 * h,
               sigma=(0.075 * h, 0.05 * h, 0.04 * h), direction=(0, -0.4, -1), mask=None)
    b.verts = stack.apply(b.verts)

    # 5b) S4.2 — aberturas da cabeça (órbita, boca, narinas).  Depois dos campos
    #     (o rebordo segue a superfície já deformada) e antes das regiões (a
    #     lista de vértices muda: ``cut_openings`` reindexa tudo).
    openings = head_openings(spec, anat, h)
    cut_info = cut_openings(b, openings)

    # 6) regions + groups (scalp for hair, masks for shader)
    hairline_z = anat.z("hairline")
    regions = {"scalp": [], "eyelid": [], "brow": [], "lip": [], "nostril": []}
    for i, p in enumerate(b.verts):
        p = Vector(p)
        # scalp: above the hairline arc, behind trichion; excludes forehead
        dz = p.z - hairline_z
        on_top = (dz > -0.012 * h) and ((p - c).z > 0.02 * h or p.y < c.y + 0.15 * ry)
        front_low = p.y > c.y - 0.10 * ry and p.z < hairline_z
        if on_top and not front_low:
            b.regions[i] = "scalp"
            regions["scalp"].append(i)
        for tag in ("L", "R"):
            if (p - lm[f"eye.{tag}"]).length < 0.030 * h and p.y > lm[f"eye.{tag}"].y - 0.02 * h:
                b.regions[i] = "eyelid"
                regions["eyelid"].append(i)
                break
        for tag in ("L", "R"):
            if (p - lm[f"brow.{tag}"]).length < 0.026 * h and p.z > lm["eye"].z:
                b.regions[i] = "brow"
                regions["brow"].append(i)
                break
        if (p - lm["mouth"]).length < 0.058 * h * spec.face.mouth_width and abs(p.y - lm["mouth"].y) < 0.022 * h:
            b.regions[i] = "lip"
            regions["lip"].append(i)
        if (p - lm["nose_base"]).length < 0.020 * h and p.z < lm["nose_base"].z:
            b.regions[i] = "nostril"
            regions["nostril"].append(i)
    for name, idxs in regions.items():
        for i in idxs:
            b.set_group(name, i, 1.0)

    return HeadResult(builder=b, rings={}, regions=regions, openings=cut_info)
