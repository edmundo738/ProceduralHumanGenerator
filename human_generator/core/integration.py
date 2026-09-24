# -*- coding: utf-8 -*-
"""S3 — instrumento de integração corporal (python puro, sem ``bpy``).

Mede as propriedades que a pergunta de BUILD 01 exige — *a estrutura corporal
básica forma uma figura humana coerente?* — e que antes eram medidas por
scripts descartáveis em ``/tmp``.  Ver ``docs/S3_BODY_INTEGRATION.md`` §2 para a
definição exacta de cada critério e §3 para o baseline medido.

Tudo aqui é determinístico e independente do backend numérico (nada de
comparações de igualdade sobre floats calculados de formas diferentes): o
critério de espelho usa tolerância explícita, o de fronteira usa o número de
faces por aresta, e o de silhueta usa uma grelha com resolução declarada.

Convenções (as mesmas do resto do projeto):
  * ``builder`` é um ``MeshBuilder`` já *merged* (a personagem inteira);
  * "componente" = componente conexa por faces (união-busca sobre os loops);
  * "flutuante" = componente sem nenhuma outra componente a ≤ ``gap`` mm
    (medida vértice-a-vértice, não por bbox: bboxes que se cruzam podem estar
    longe uma da outra em geometria real).
"""
from __future__ import annotations

import math

import math
from collections import Counter, defaultdict
from math import sqrt

from ._math import Vector

__all__ = [
    "connected_components", "component_labels", "overlap_graph", "floating_components",
    "boundary_edges", "mirror_stats", "structure_mirror_hausdorff",
    "floor_contact", "height_envelope", "silhouette", "integration_report",
    "points_inside", "is_closed", "root_insertion", "foot_metrics",
]


# --------------------------------------------------------------------------- components
def connected_components(builder) -> list[list[int]]:
    """Componentes conexas por faces (união-busca).  Ordenadas por tamanho desc."""
    n = len(builder.verts)
    parent = list(range(n))

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for f in builder.faces:
        a = f[0]
        for i in range(1, len(f)):
            ra, rb = find(a), find(f[i])
            if ra != rb:
                parent[ra] = rb
    groups: dict[int, list[int]] = defaultdict(list)
    for i in range(n):
        groups[find(i)].append(i)
    return sorted(groups.values(), key=len, reverse=True)


def _bbox(verts, ids) -> tuple[float, float, float, float, float, float]:
    xs = [verts[i].x for i in ids]
    ys = [verts[i].y for i in ids]
    zs = [verts[i].z for i in ids]
    return (min(xs), max(xs), min(ys), max(ys), min(zs), max(zs))


def component_labels(builder, comps=None) -> list[str]:
    """Rótulo anatómico de cada componente (maior grupo nomeado, senão região)."""
    comps = comps or connected_components(builder)
    owner: dict[int, str] = {}
    for gname, weights in builder.groups.items():
        for i in weights:
            owner.setdefault(i, gname)
    labels = []
    for ids in comps:
        named = Counter(owner[i] for i in ids if i in owner)
        if named:
            labels.append(named.most_common(1)[0][0])
        else:
            labels.append("region:" + Counter(builder.regions[i] for i in ids).most_common(1)[0][0])
    return labels


def _grid_index(verts, cell: float) -> dict[tuple[int, int, int], list[int]]:
    grid: dict[tuple[int, int, int], list[int]] = defaultdict(list)
    for i, p in enumerate(verts):
        grid[(int(p.x // cell), int(p.y // cell), int(p.z // cell))].append(i)
    return grid


def _sample_points(builder, comps) -> tuple[list, list[int]]:
    """Pontos de amostragem = vértices + centros de face (uma vez por face).

    Medido (S3): só com vértices, componentes que se **interpenetram** podem
    parecer afastadas — a malha do tronco tem ~16 vértices por anel, logo os
    vértices de duas cascas que se cruzam distam centímetros uns dos outros.
    Os centros de face dão uma amostra da superfície com espaçamento da ordem
    do tamanho da face e tornam a adjacência mensurável.
    """
    of = [0] * len(builder.verts)
    for ci, ids in enumerate(comps):
        for i in ids:
            of[i] = ci
    pts: list = list(builder.verts)
    owner: list[int] = list(of)
    for f in builder.faces:
        c = Vector((0.0, 0.0, 0.0))
        for i in f:
            c = c + builder.verts[i]
        pts.append(c / len(f))
        owner.append(of[f[0]])
    return pts, owner


def overlap_graph(builder, gap: float = 0.010, comps=None, labels=None) -> dict:
    """Grafo de adjacência entre componentes, por distância mínima amostrada.

    ``gap`` é a distância (m) abaixo da qual duas componentes contam como
    adjacentes; a grelha de 1 cm com pesquisa 3×3×3 limita ``gap`` a 10 mm
    (validado com ``ValueError`` para não prometer o que não mede).
    """
    if gap > 0.010:
        raise ValueError("gap > 10 mm exceeds the 3x3x3 search of a 10 mm grid")
    comps = comps or connected_components(builder)
    labels = labels or component_labels(builder, comps)
    cell = 0.01
    pts, owner = _sample_points(builder, comps)
    grid: dict[tuple[int, int, int], list[int]] = defaultdict(list)
    for i, p in enumerate(pts):
        grid[(int(p.x // cell), int(p.y // cell), int(p.z // cell))].append(i)
    best: dict[tuple[int, int], float] = {}
    g2 = gap * gap
    for i, p in enumerate(pts):
        key = (int(p.x // cell), int(p.y // cell), int(p.z // cell))
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for dz in (-1, 0, 1):
                    for j in grid.get((key[0] + dx, key[1] + dy, key[2] + dz), ()):
                        if j == i or owner[j] == owner[i]:
                            continue
                        q = pts[j]
                        d2 = (p.x - q.x) ** 2 + (p.y - q.y) ** 2 + (p.z - q.z) ** 2
                        if d2 <= g2:
                            pair = (owner[i], owner[j]) if owner[i] < owner[j] else (owner[j], owner[i])
                            if pair not in best or d2 < best[pair] ** 2:
                                best[pair] = sqrt(d2)
    label_pairs: Counter = Counter()
    for (a, b) in best:
        label_pairs[tuple(sorted((labels[a], labels[b])))] += 1
    return {"n_components": len(comps), "labels": labels, "edges": best,
            "label_edges": dict(label_pairs), "gap": gap,
            "sample_points": len(pts)}


def floating_components(builder, gap: float = 0.010) -> list[dict]:
    """Componentes sem nenhuma vizinha a ≤ ``gap`` mm (o critério I1 do contrato)."""
    comps = connected_components(builder)
    labels = component_labels(builder, comps)
    graph = overlap_graph(builder, gap=gap, comps=comps, labels=labels)
    touched = {c for pair in graph["edges"] for c in pair}
    out = []
    for ci, ids in enumerate(comps):
        if ci not in touched:
            out.append({"label": labels[ci], "n": len(ids),
                        "bbox": _bbox(builder.verts, ids)})
    return out


# --------------------------------------------------------------------------- boundaries
def boundary_edges(builder) -> dict[tuple[str, str], int]:
    """Arestas com uma só face, agrupadas pelo par de regiões (ordenado)."""
    count: Counter = Counter()
    for f in builder.faces:
        n = len(f)
        for i in range(n):
            a, b = f[i], f[(i + 1) % n]
            count[(a, b) if a < b else (b, a)] += 1
    out: Counter = Counter()
    for (a, b), k in count.items():
        if k == 1:
            out[tuple(sorted((builder.regions[a], builder.regions[b])))] += 1
    return dict(out)


# --------------------------------------------------------------------------- mirror
def mirror_stats(builder, tol: float = 1e-5) -> dict:
    """Vértices cujo par espelhado a ``(-x, y, z)`` não existe dentro de ``tol``."""
    pos: dict[tuple[int, int, int], list[int]] = defaultdict(list)
    q = max(tol, 1e-9)
    for i, p in enumerate(builder.verts):
        pos[(round(p.x / q), round(p.y / q), round(p.z / q))].append(i)
    miss_region: Counter = Counter()
    total_region: Counter = Counter()
    misses = 0
    for i, p in enumerate(builder.verts):
        total_region[builder.regions[i]] += 1
        key = (round(-p.x / q), round(p.y / q), round(p.z / q))
        if not pos.get(key):
            misses += 1
            miss_region[builder.regions[i]] += 1
    return {"n": len(builder.verts), "misses": misses,
            "ratio": misses / max(1, len(builder.verts)),
            "tol": tol,
            "misses_by_region": dict(miss_region),
            "total_by_region": dict(total_region)}


def _hausdorff(a: list[tuple[float, float, float]],
               b: list[tuple[float, float, float]]) -> float:
    def one_way(p: list, q: list) -> float:
        worst = 0.0
        for x, y, z in p:
            best = min((x - u) ** 2 + (y - v) ** 2 + (z - w) ** 2 for u, v, w in q)
            worst = max(worst, best)
        return sqrt(worst)
    return max(one_way(a, b), one_way(b, a))


def structure_mirror_hausdorff(builder) -> dict[str, float]:
    """Hausdorff entre cada estrutura ``L.<nome>`` e o espelho de ``R.<nome>``.

    É a medida válida para I6 (a comparação por listas ordenadas é frágil à
    ordem dos anéis — registado em ``docs/S3_BODY_INTEGRATION.md`` §5).
    """
    out: dict[str, float] = {}
    names = {g.split(".", 1)[1] for g in builder.groups if g.startswith("L.")}
    for base in sorted(names):
        L = builder.groups.get(f"L.{base}")
        R = builder.groups.get(f"R.{base}")
        if not L or not R:
            continue
        a = [(builder.verts[i].x, builder.verts[i].y, builder.verts[i].z) for i in L]
        b = [(-builder.verts[i].x, builder.verts[i].y, builder.verts[i].z) for i in R]
        if len(a) > 400:                        # keep the O(n^2) part small
            step = len(a) // 200 + 1
            a, b = a[::step], b[::step]
        out[base] = _hausdorff(a, b)
    return out


# --------------------------------------------------------------------------- inside tests
def _tri_hits_ray(orig, direction, a, b, c, eps=1e-12) -> bool:
    """Möller–Trumbore: o raio ``orig + t*direction`` cruza o triângulo abc?"""
    e1 = (b[0] - a[0], b[1] - a[1], b[2] - a[2])
    e2 = (c[0] - a[0], c[1] - a[1], c[2] - a[2])
    px = direction[1] * e2[2] - direction[2] * e2[1]
    py = direction[2] * e2[0] - direction[0] * e2[2]
    pz = direction[0] * e2[1] - direction[1] * e2[0]
    det = e1[0] * px + e1[1] * py + e1[2] * pz
    if -eps < det < eps:
        return False
    inv = 1.0 / det
    t0 = (orig[0] - a[0], orig[1] - a[1], orig[2] - a[2])
    u = (t0[0] * px + t0[1] * py + t0[2] * pz) * inv
    if u < 0.0 or u > 1.0:
        return False
    qx = t0[1] * e1[2] - t0[2] * e1[1]
    qy = t0[2] * e1[0] - t0[0] * e1[2]
    qz = t0[0] * e1[1] - t0[1] * e1[0]
    v = (direction[0] * qx + direction[1] * qy + direction[2] * qz) * inv
    if v < 0.0 or u + v > 1.0:
        return False
    t = (e2[0] * qx + e2[1] * qy + e2[2] * qz) * inv
    return t > eps


def points_inside(builder, comp_ids, points, direction=(1.0, 0.0, 0.0)) -> list[bool]:
    """Teste de paridade de raio: cada ponto está dentro da casca fechada?

    ``comp_ids`` são os índices de vértices de UMA componente (a casca-mãe).
    Só funciona com cascas fechadas (manifold, sem fronteira) — os olhos, os
    dentes, o tronco e os membros são; cascas abertas devolvem resultado
    indefinido, por isso o chamador deve verificar ``is_closed``.
    """
    verts = builder.verts
    faces = [f for f in builder.faces if all(i in comp_ids for i in f)]
    inside: list[bool] = []
    for p in points:
        hits = 0
        for f in faces:
            n = len(f)
            a = verts[f[0]]
            pa = (a.x, a.y, a.z)
            for k in range(1, n - 1):
                b = verts[f[k]]
                c = verts[f[k + 1]]
                if _tri_hits_ray((p[0], p[1], p[2]), direction, pa,
                                 (b.x, b.y, b.z), (c.x, c.y, c.z)):
                    hits += 1
        inside.append(hits % 2 == 1)
    return inside


def is_closed(builder, comp_ids) -> bool:
    """Casca fechada: toda a aresta da componente tem exactamente 2 faces."""
    counts: Counter = Counter()
    s_ids = set(comp_ids)
    for f in builder.faces:
        if not all(i in s_ids for i in f):
            continue
        n = len(f)
        for i in range(n):
            a, c = f[i], f[(i + 1) % n]
            counts[(a, c) if a < c else (c, a)] += 1
    return bool(counts) and all(k == 2 for k in counts.values())


def root_insertion(builder, comps=None, labels=None) -> dict:
    """Quanto de cada casca-filha está DENTRO da sua casca-mãe (S3 — inserção).

    Medido em S3 (§3): as raízes dos membros ficavam fora dos pais — arm↔tronco
    7.5 mm, perna↔tronco 9.2 mm, cabeça↔tronco 4.0 mm de folga mínima, apesar de
    ``generators/body.py`` documentar "limb roots are *inserted* into the trunk".
    Este é o teste objectivo que faltava: por cada par (mãe, filha) conta quantos
    pontos de amostra da filha caem dentro da mãe.
    """
    comps = comps or connected_components(builder)
    labels = labels or component_labels(builder, comps)
    sizes = [len(c) for c in comps]
    out: dict[str, dict] = {}

    def pick(*sizes_wanted):
        for ci, c in enumerate(comps):
            if len(c) in sizes_wanted:
                return ci
        return None

    trunk = pick(242)
    if trunk is None:
        return out
    pairs = []
    for ci, c in enumerate(comps):
        if ci == trunk:
            continue
        if len(c) in (120, 132, 108, 536):        # arms, legs/hands-pairs, hands, head
            pairs.append(ci)
    if not is_closed(builder, comps[trunk]):
        return {"error": "parent shell is not closed"}
    for ci in pairs:
        pts = [builder.verts[i] for i in comps[ci]]
        step = max(1, len(pts) // 60)
        sample = pts[::step]
        flags = points_inside(builder, set(comps[trunk]), sample)
        out[f"{labels[ci]}#{len(comps[ci])}"] = {
            "n_sampled": len(sample),
            "n_inside": sum(1 for f in flags if f),
            "child_closed": is_closed(builder, comps[ci]),
        }
    return out


# --------------------------------------------------------------------------- envelope
def floor_contact(builder, plane: float = 0.0) -> dict:
    """Contacto com o plano do chão (critério I2)."""
    zs = [(p.z, i) for i, p in enumerate(builder.verts)]
    if not zs:
        return {"min_z": 0.0, "below": 0, "deepest": 0.0, "regions_below": {}}
    min_z, min_i = min(zs)
    below = [i for z, i in zs if z < plane - 1e-12]
    return {"min_z": min_z,
            "min_vertex": min_i,
            "min_region": builder.regions[min_i],
            "below": len(below),
            "deepest": min(0.0, min_z - plane),
            "regions_below": dict(Counter(builder.regions[i] for i in below))}


def height_envelope(builder, anat) -> dict:
    """Alturas medidas vs estações do canon (critérios I3, I4)."""
    zs = [p.z for p in builder.verts]
    top = max(zs)
    scalp = [p.z for i, p in enumerate(builder.verts) if builder.regions[i] == "scalp"]
    out = {"stature": anat.stature,
           "z_min": min(zs), "z_max": top,
           "height": top - min(zs),
           "height_minus_stature": (top - min(zs)) - anat.stature,
           "toe_offset": -min(zs)}
    if scalp:
        out["scalp_z_max"] = max(scalp)
        out["scalp_minus_vertex"] = max(scalp) - anat.z("vertex")
    return out


# --------------------------------------------------------------------------- feet
def foot_metrics(builder, anat, comps=None) -> dict:
    """Métricas do pé no seu PRÓPRIO eixo (S3.6).

    Encontra as cascas do pé (as que tocam o chão e têm tamanho de casca) e mede
    comprimento e largura **perpendiculares ao eixo do pé**, mais o yaw desse eixo
    em relação ao plano sagital.

    Porquê o eixo próprio: o eixo do pé não é paralelo a +y (medido: o ``toe_end``
    do canon está 34 mm medial do tornozelo ⇒ ~7.6° de rotação), e a extensão em x
    de um pé rodado inclui uma parcela do comprimento (``L·sin(yaw)`` ≈ 35 mm).
    Comparar essa extensão com a largura antropométrica (0.055·estatura) seria
    comparar coisas diferentes — foi o que a primeira versão desta métrica fez, e
    está registado como erro meu.  O yaw certo é **toe-out** (dedos para fora) no
    pé esquerdo; a convenção aqui é: positivo = toe-out.

    Referências (antropometria standard): comprimento ≈ 0.152·estatura,
    largura ≈ 0.055·estatura.
    """
    comps = comps or connected_components(builder)
    V = builder.verts
    # "Pé" = TODAS as cascas que tocam o chão desse lado (casca principal + os
    # cinco dedos).  Medido: medir só a casca principal dava 193.9 mm de
    # comprimento (0.75× o canónico) porque os dedos são cascas separadas — o
    # instrumento sub-reportava o pé em ~60 mm.
    cand = [ci for ci, ids in enumerate(comps)
            if len(ids) >= 8 and min(V[i].z for i in ids) <= 0.005]
    sides: dict[str, list[int]] = {"L": [], "R": []}
    for ci in cand:
        cx = sum(V[i].x for i in comps[ci]) / len(comps[ci])
        sides["L" if cx > 0 else "R"].append(ci)
    feet = [ci for side in ("L", "R") for ci in sides[side]]
    if len(sides["L"]) == 0 or len(sides["R"]) == 0:
        return {"n_feet": 0, "error": "expected foot shells on both sides"}
    out: dict = {"n_feet": len(feet),
                 "ref_length": 0.152 * anat.stature,
                 "ref_width": 0.055 * anat.stature}
    per: dict = {}
    for side_name in ("L", "R"):
        ids = [i for ci in sides[side_name] for i in comps[ci]]
        xs = [V[i].x for i in ids]
        ys = [V[i].y for i in ids]
        zs = [V[i].z for i in ids]
        cx = sum(xs) / len(xs)
        cy = sum(ys) / len(ys)
        # eixo longitudinal: PCA 2D (direcção dominante em xy)
        sxx = sum((x - cx) ** 2 for x in xs)
        syy = sum((y - cy) ** 2 for y in ys)
        sxy = sum((xs[k] - cx) * (ys[k] - cy) for k in range(len(xs)))
        theta = 0.5 * math.atan2(2.0 * sxy, sxx - syy)      # ângulo do eixo vs +x
        ax = (math.cos(theta), math.sin(theta))
        px = (-ax[1], ax[0])
        lon = [ (x - cx) * ax[0] + (y - cy) * ax[1] for x, y in zip(xs, ys) ]
        lat = [ (x - cx) * px[0] + (y - cy) * px[1] for x, y in zip(xs, ys) ]
        side = side_name
        # yaw: ângulo entre o eixo (apontando para +y) e +y; toe-out no pé L
        fwd = ax if ax[1] >= 0 else (-ax[0], -ax[1])
        yaw = math.degrees(math.atan2(fwd[0] * (1 if side == "L" else -1), fwd[1]))
        per[side] = {
            "length": max(lon) - min(lon), "width": max(lat) - min(lat),
            "height": max(zs) - min(zs), "yaw_deg": yaw,
            "x_range": (min(xs), max(xs)), "n": len(ids),
        }
        per[side]["length_ratio"] = per[side]["length"] / out["ref_length"]
        per[side]["width_ratio"] = per[side]["width"] / out["ref_width"]
    out["feet"] = per
    left = [i for ci in sides["L"] for i in comps[ci]]
    right = [i for ci in sides["R"] for i in comps[ci]]
    if left and right:
        out["separation"] = min(abs(V[i].x - V[j].x) for i in left for j in right)
    out["n_shells"] = {"L": len(sides["L"]), "R": len(sides["R"])}
    return out


# --------------------------------------------------------------------------- junctions
# S3.7 — métricas de JUNÇÃO.  Tudo aqui é medido por intersecção de planos com a
# superfície (não por bandas de vértices, que são irregulares), e as cascas são
# identificadas pelo REGISTO DE ANÉIS do builder (``trunk.3``, ``arm.L.2``, …) e
# não por heurísticas de posição/simetria — a identidade é explícita.


def part_vertices(builder, *prefixes: str) -> set[int]:
    """Vértices dos anéis registados cujo nome começa por um dos prefixos."""
    out: set[int] = set()
    for name, ids in builder.rings.items():
        for pre in prefixes:
            if name == pre or name.startswith(pre + "."):
                out.update(ids)
                break
    return out


def _face_parts(builder, parts: dict[str, set[int]]) -> list[str | None]:
    """Para cada face, o nome da parte a que pertence (1ª vert)."""
    owner: dict[int, str] = {}
    for name, ids in parts.items():
        for i in ids:
            owner[i] = name
    return [owner.get(f[0]) for f in builder.faces]


def part_distance(builder, a: set[int], b: set[int], samples: bool = True) -> float:
    """Distância mínima entre as superfícies de duas partes (m).

    Amostra faces (vértices + centros de face) das duas partes e devolve a menor
    distância — negativo não existe (distância é sempre ≥ 0), mas o que importa
    é o valor: 0 significa superfícies que se tocam/interpenetram.  Usada para
    verificar que dois membros não se enterram um no outro (ex.: mão ↔ coxa na
    pose pendente).
    """
    V = builder.verts
    cell = 0.02
    pts_a: list = []
    for f in builder.faces:
        if f[0] in a:
            c = Vector((0.0, 0.0, 0.0))
            for i in f:
                pts_a.append(V[i])
                c += V[i]
            pts_a.append(c / len(f))
    pts_b: list = []
    for f in builder.faces:
        if f[0] in b:
            c = Vector((0.0, 0.0, 0.0))
            for i in f:
                pts_b.append(V[i])
                c += V[i]
            pts_b.append(c / len(f))
    if not pts_a or not pts_b:
        return float("inf")
    grid = _grid_index(pts_b, cell)
    best = float("inf")
    for p in pts_a:
        kx, ky, kz = int(p.x / cell), int(p.y / cell), int(p.z / cell)
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for dz in (-1, 0, 1):
                    for qi in grid.get((kx + dx, ky + dy, kz + dz), ()):
                        d = (p - pts_b[qi]).length
                        if d < best:
                            best = d
    return best


def cross_section_width(builder, verts, z: float, axis: str = "x",
                        faces: list | None = None) -> float | None:
    """Largura da secção da casca no plano ``z`` (medida em ``axis``), ou None.

    A secção é o conjunto das intersecções das arestas das faces com o plano:
    é a largura real da superfície naquela cota, independente de haver ou não
    vértices perto de ``z``.

    ``verts`` é o conjunto de vértices da parte medida e **filtra sempre** as
    faces (medido: esquecer o filtro devolvia a largura do corpo inteiro àquela
    cota — 660 mm no punho, 225 mm no tornozelo — em vez da largura da junção).
    """
    V = builder.verts
    if faces is None:
        faces = [f for f in builder.faces if f[0] in verts]
    lo = hi = None
    for f in faces:
        n = len(f)
        for k in range(n):
            p, q = V[f[k]], V[f[(k + 1) % n]]
            if (p.z - z) * (q.z - z) < 0.0:
                t = (z - p.z) / (q.z - p.z)
                r = p + (q - p) * t
                v = r.x if axis == "x" else r.y
                lo = v if lo is None else min(lo, v)
                hi = v if hi is None else max(hi, v)
    return None if lo is None else float(hi - lo)


def width_profile(builder, verts, z0: float, z1: float, step: float = 0.002,
                  axis: str = "x") -> list[tuple[float, float | None]]:
    V = builder.verts
    faces = [f for f in builder.faces if f[0] in verts]
    out = []
    z = z0
    while z <= z1 + 1e-12:
        out.append((z, cross_section_width(builder, verts, z, axis=axis, faces=faces)))
        z += step
    return out


def junction_metrics(build, step: float = 0.002) -> dict:
    """Métricas S3.7: pescoço visível, linha do ombro, degraus, pose dos braços.

    Critérios (contrato ``docs/S3_7_JUNCTIONS.md``):

    * **J1** pescoço: na banda [linha do ombro, queixo] a largura mínima tem de
      ser ≤ 0.80 × largura máxima da cabeça **e** ≤ 0.35 × largura máxima do
      ombro.  (A primeira versão exigia ainda um troço contínuo de ≥ 25 mm com
      |dw/dz| ≤ 1.0; **refutada por medição** — a banda entre a linha do ombro
      (0.812·estatura) e o queixo (0.858·estatura) tem 78 mm e é dominada pela
      rampa do trapézio, pelo que o critério não é satisfazível por um corpo
      plausível.  O troço vertical fica *reportado*, não gated.)
    * **J2** ombro: largura máxima na banda do ombro ≤ 1.20 × biacromial
      canónico (0.2257·estatura).
    * **J3** degraus: |w_pai(z_topo_filho) − w_filho(z_topo_filho)| ≤ 2 mm no
      punho e no tornozelo.
    * **J4** pose: |x_cotovelo − x_acrómio| e |x_punho − x_acrómio| ≤ 0.02·estatura.
    """
    builder, anat = build.builder, build.anatomy
    V = builder.verts
    parts = {
        "trunk": part_vertices(builder, "trunk"),
        "head": part_vertices(builder, "head.skull"),
        "arm.L": part_vertices(builder, "arm.L"), "arm.R": part_vertices(builder, "arm.R"),
        "hand.L": part_vertices(builder, "hand.L"), "hand.R": part_vertices(builder, "hand.R"),
        "leg.L": part_vertices(builder, "leg.L"), "leg.R": part_vertices(builder, "leg.R"),
        "foot.L": part_vertices(builder, "foot.L"), "foot.R": part_vertices(builder, "foot.R"),
    }
    core = parts["trunk"] | parts["head"]
    upper = parts["trunk"] | parts["arm.L"] | parts["arm.R"]

    z_sh, z_chin = anat.z("deltoid_line"), anat.z("chin")
    out: dict = {}

    # J1 — pescoço
    prof = width_profile(builder, core, z_sh, z_chin, step=step)
    vals = [(z, w) for z, w in prof if w is not None]
    head_top = min(z_chin + 0.15 * anat.stature, max(V[i].z for i in parts["head"]))
    hp = [w for _, w in width_profile(builder, parts["head"], z_chin, head_top, step=step) if w]
    neck_min = min(vals, key=lambda t: t[1]) if vals else (0.0, 0.0)
    head_w = max(hp) if hp else 0.0
    # maior troço contínuo com |dw/dz| ≤ 1.0 mm/mm
    run = best = 0.0
    prev = None
    for z, w in vals:
        if prev is not None:
            d = abs(w - prev[1]) / max(1e-9, z - prev[0])
            if d <= 1.0:
                run += z - prev[0]
            else:
                best = max(best, run)
                run = 0.0
        prev = (z, w)
    best = max(best, run)
    shoulder_max = 0.0
    out["neck"] = {
        "band_mm": (z_chin - z_sh) * 1000.0,
        "min_width_mm": neck_min[1] * 1000.0,
        "min_at_mm": neck_min[0] * 1000.0,
        "head_width_mm": head_w * 1000.0,
        "ratio_min_over_head": (neck_min[1] / head_w) if head_w else float("inf"),
        "vertical_run_mm": best * 1000.0,
    }

    # J2 — linha do ombro
    band = [z for z in (z_sh - 0.04, z_sh, z_sh + 0.04)]
    sw = [(z, w) for z, w in ((z, cross_section_width(builder, upper, z)) for z in
                              [z_sh - 0.04 + i * step for i in range(int(0.08 / step) + 1)]) if w]
    biacromial = 0.2257 * anat.stature
    smax = max(sw, key=lambda t: t[1]) if sw else (0.0, 0.0)
    shoulder_max = smax[1]
    out["neck"]["shoulder_width_mm"] = shoulder_max * 1000.0
    out["neck"]["ratio_min_over_shoulder"] = (neck_min[1] / shoulder_max) if shoulder_max else float("inf")
    out["shoulder"] = {
        "max_width_mm": smax[1] * 1000.0,
        "at_mm": smax[0] * 1000.0,
        "biacromial_mm": biacromial * 1000.0,
        "ratio_over_biacromial": smax[1] / biacromial if biacromial else float("inf"),
    }

    # J3 — degraus de junção.
    #
    # Medido na UNIÃO (pai ∪ filho) e não no topo do filho: as cascas são
    # fechadas com ``cap_pole``, logo o "topo" do filho é o ápice do cap (um
    # ponto) e a largura aí é ~0 — medir ali dá o degrau errado (ex.: 21 mm no
    # tornozelo, quando o degrau visível é a diferença entre a perna e o pé na
    # cota de passagem).  O degrau é a variação da largura da união através do
    # ponto de passagem ``z*`` (fundo do pai), numa janela de ±1 mm:
    #   degrau = w_uniao(z* + 1 mm) − w_uniao(z* − 1 mm).
    steps: dict = {}
    for side in ("L", "R"):
        for child, parent in (("hand", "arm"), ("foot", "leg")):
            cv, pv = parts[f"{child}.{side}"], parts[f"{parent}.{side}"]
            if not cv or not pv:
                continue
            union = cv | pv
            z_star = min(V[i].z for i in pv)
            w_above = cross_section_width(builder, union, z_star + 0.001)
            w_below = cross_section_width(builder, union, z_star - 0.001)
            steps[f"{child}.{side}"] = {
                "z_star_mm": z_star * 1000.0,
                "above_mm": None if w_above is None else w_above * 1000.0,
                "below_mm": None if w_below is None else w_below * 1000.0,
                "step_mm": None if (w_above is None or w_below is None)
                else (w_above - w_below) * 1000.0,
            }
    out["steps"] = steps

    # J4 — pose dos braços (deslocamento lateral do cotovelo/punho vs acrómio)
    pose: dict = {}
    for tag in (".L", ".R"):
        acr = anat.landmarks.get("acromion" + tag)
        el = anat.landmarks.get("elbow" + tag)
        wr = anat.landmarks.get("wrist" + tag)
        if acr is None or el is None or wr is None:
            continue
        pose["elbow" + tag] = {"dx_mm": abs(el.x - acr.x) * 1000.0,
                               "limit_mm": 0.020 * anat.stature * 1000.0}
        pose["wrist" + tag] = {"dx_mm": abs(wr.x - acr.x) * 1000.0,
                               "limit_mm": 0.020 * anat.stature * 1000.0}
    out["arm_pose"] = pose

    # J5 — alinhamento dos membros inferiores (joelho vs anca)
    legs: dict = {}
    for tag in (".L", ".R"):
        hip = anat.landmarks.get("hip" + tag)
        knee = anat.landmarks.get("knee" + tag)
        if hip is None or knee is None:
            continue
        legs["knee" + tag] = {"dx_mm": abs(knee.x - hip.x) * 1000.0,
                              "limit_mm": 0.020 * anat.stature * 1000.0}
    out["leg_pose"] = legs

    # J6 — suavidade da rampa do tronco: maior salto de largura entre estações
    # CONSECUTIVAS do próprio gerador (medido nos anéis registados, não no
    # perfil contínuo).  Um "ombro que faz sentido" não pode ter uma parede.
    rings = [(name, ids) for name, ids in builder.rings.items()
             if name.startswith("trunk")]
    rings.sort(key=lambda kv: -sum(V[i].z for i in kv[1]) / len(kv[1]))
    ramp = []
    for (n0, r0), (n1, r1) in zip(rings, rings[1:]):
        w0 = max(V[i].x for i in r0) - min(V[i].x for i in r0)
        w1 = max(V[i].x for i in r1) - min(V[i].x for i in r1)
        z0 = sum(V[i].z for i in r0) / len(r0)
        z1 = sum(V[i].z for i in r1) / len(r1)
        ramp.append({"from": n0, "to": n1, "dw_mm": (w1 - w0) * 1000.0,
                     "dz_mm": (z0 - z1) * 1000.0,
                     "slope": abs(w1 - w0) / max(1e-9, abs(z0 - z1))})
    out["trunk_ramp"] = ramp
    out["trunk_ramp_max_slope"] = max((r["slope"] for r in ramp), default=0.0)
    return out


# --------------------------------------------------------------------------- hands
# S3.8 — métricas da mão.  Como em S3.7, a identidade vem do REGISTO DE ANÉIS
# (palma: ``hand.<lado>.<k>``) e dos GRUPOS por falange (``L.finger.<raio>.<n>``),
# nunca de heurísticas de posição.


def _digit_vertices(builder, side_tag: str, digit: str) -> set[int]:
    """Vértices de um dedo (todas as falanges), pelos grupos registados."""
    out: set[int] = set()
    for name, weights in builder.groups.items():
        if name.startswith(f"{side_tag}.finger.{digit}."):
            out.update(weights.keys())
    return out


def _frame_from(axis: Vector, upref: Vector = None):
    z = Vector(axis).normalized()
    up = Vector(upref) if upref is not None else Vector((0.0, -1.0, 0.0))
    up = up - z * up.dot(z)
    if up.length_squared < 1e-12:
        up = Vector((1.0, 0.0, 0.0))
        up = up - z * up.dot(z)
    y = up.normalized()
    x = y.cross(z).normalized()
    return x, y, z


def hand_metrics(build, side: str = "L", comps=None) -> dict:
    """Comprimento, largura, espessura da mão e folgas entre dedos (m).

    Definições explícitas (as da antropometria, medidas na MALHA):

    * **comprimento** — do ponto articular do punho à ponta mais distal do dedo
      médio, ao longo do eixo punho→média (FAA: prega do punho → ponta do médio);
    * **largura** — extensão da malha da palma ao longo do eixo **2.º↔5.º
      metacarpo** (``hand.<lado>.index.mcp`` → ``hand.<lado>.pinky.mcp``), ou
      seja a largura "nos nós dos dedos" com tecido mole incluído;
    * **espessura** — extensão perpendicular a esse eixo e ao eixo da mão;
    * **folgas** — distância mínima de superfície entre dedos adjacentes.

    As tentativas anteriores mediam a extensão por PCA do anel e davam valores
    inflacionados (66.3 mm e 56.7 mm de espessura) porque os anéis da palma são
    inclinados em relação aos eixos globais; a definição por pontos articulares
    não depende de referencial e é a que a fonte antropométrica usa.
    """
    builder, anat = build.builder, build.anatomy
    V = builder.verts
    tag = side
    lm = anat.landmarks
    try:
        wrist = Vector(lm["wrist." + tag])
        idx = Vector(lm["hand." + tag + ".index.mcp"])
        pky = Vector(lm["hand." + tag + ".pinky.mcp"])
        mid_tip_lm = Vector(lm["hand." + tag + ".middle.tip"])
    except KeyError as e:
        return {"error": "missing landmark %s" % (e,), "side": side}
    palm_ids = [i for k, ids in builder.rings.items()
                if k.startswith("hand." + tag + ".") for i in ids]
    mid = _digit_vertices(builder, tag, "middle")
    if not palm_ids or not mid:
        return {"error": "palm rings or middle finger groups missing", "side": side}

    # O eixo da mão NÃO é a recta punho→ponta (a palma é inclinada e o dedo médio
    # sai desviado): medido, usá-la dava 42.1 mm de espessura para uma geometria
    # de ~29 mm (o desvio mete largura dentro da espessura).  O eixo correcto é a
    # NORMAL DOS ANÉIS da palma (a mesma construção do ``cap_pole``).
    palm_pts = [V[i] for i in palm_ids]
    ring_pts = [[V[i] for i in ids] for k, ids in builder.rings.items()
                if k.startswith("hand." + tag + ".")]
    n_acc = Vector((0.0, 0.0, 0.0))
    for pts in ring_pts:
        c0 = Vector((0.0, 0.0, 0.0))
        for p in pts:
            c0 += p
        c0 /= len(pts)
        for i2 in range(len(pts)):
            n_acc += (pts[i2] - c0).cross(pts[(i2 + 1) % len(pts)] - c0)
    axis = n_acc.normalized() if n_acc.length_squared > 1e-18 else (mid_tip_lm - wrist).normalized()
    breadth_dir = (pky - idx)
    breadth_dir = breadth_dir - axis * breadth_dir.dot(axis)     # no plano do anel
    breadth_dir = (breadth_dir.normalized() if breadth_dir.length_squared > 1e-12
                   else Vector((1.0, 0.0, 0.0)))
    # Espessura = dentro do plano do anel, perpendicular à largura (o ``axis`` é
    # o COMPRIMENTO da palma — usá-lo como espessura media 121 mm, que é a
    # própria extensão longitudinal).
    thick_dir = axis.cross(breadth_dir)
    if thick_dir.length_squared < 1e-12:
        thick_dir = Vector((0.0, 1.0, 0.0))
    thick_dir = thick_dir.normalized()
    c = Vector((0.0, 0.0, 0.0))
    for p in palm_pts:
        c += p
    c /= len(palm_pts)
    pr_b = [(p - c).dot(breadth_dir) for p in palm_pts]
    pr_t = [(p - c).dot(thick_dir) for p in palm_pts]
    # a ponta é o vértice do dedo médio MAIS DISTANTE do punho (usar a projecção
    # no eixo dos anéis depende do sentido da normal, que se inverte no lado
    # direito — medido: dava 90.9 mm em vez de 181.9 mm)
    tip = max((V[i] for i in mid), key=lambda p: (p - wrist).length)
    hand_len = (tip - wrist).length
    width = max(pr_b) - min(pr_b)
    thick = max(pr_t) - min(pr_t)
    fingers = ("index", "middle", "ring", "pinky")
    gaps = {}
    for a, b in zip(fingers, fingers[1:]):
        ia, ib = _digit_vertices(builder, tag, a), _digit_vertices(builder, tag, b)
        if ia and ib:
            gaps[a + "-" + b] = part_distance(builder, ia, ib)
    thumb = _digit_vertices(builder, tag, "thumb")
    if thumb and _digit_vertices(builder, tag, "index"):
        gaps["thumb-index"] = part_distance(builder, thumb,
                                            _digit_vertices(builder, tag, "index"))
    return {
        "side": side,
        "length": hand_len,
        "length_ratio_faa": hand_len / 0.178,
        "width": width,
        "width_ratio_faa": width / 0.076,
        "thickness": thick,
        "thickness_over_length": thick / hand_len,
        "mcp_span": (pky - idx).length,
        "mcp_span_over_length": (pky - idx).length / hand_len,
        "palm_rings": len(palm_ids) // 12,
        "finger_gaps": gaps,
    }


# --------------------------------------------------------------------------- silhouette
def face_metrics(build, comps=None) -> dict:
    """S4 — métricas da FACE, todas por identidade registada.

    Definições (nenhuma medida sem denominador declarado):

    * ``head_breadth`` — extensão em X dos anéis ``head.skull.*`` (latitudes do
      crânio), ou seja a largura máxima do crânio SEM as orelhas.  Canónico
      (FAA/DOT Ap. B, mulher p50): **144 mm**.
    * ``head_depth`` — extensão em Y dos mesmos anéis.  Canónico (comprimento
      craniano glabela→opistocrânio, mulher): **183 mm**.
    * ``head_height`` — ``vertex.z − chin.z`` (altura da cabeça); igual a
      ``H = estatura / head_units`` por construção (226.1 mm).
    * ``interpupillary`` — distância entre os marcos ``eye.L`` e ``eye.R``.
      Canónico (FAA): **62 mm**.
    * ``mouth_width`` — extensão em X da região ``lip`` (malha) e do par de
      marcos ``mouth_corner.*``.  Canónico (ch-ch, mulher): **49.2 mm**
      (Indonesia 2023) / 48.1 mm (caucasiana 2024).
    * ``lip_vermilion`` — altura da malha acima/abaixo do marco ``mouth``.
      Canónico: vermelhão superior **6.5 mm**, inferior **10.0–11.6 mm**.
    * ``eye_aperture`` — extensão (X, Z) da região ``eye`` por lado.
      Canónico (fissura palpebral): **27–30 mm × 8–11 mm**.
    * ``nose_length`` — ``|nose_root.z − nose_tip.z|``; canónico 45.3 mm.
    * ``arch_upper`` / ``arch_lower`` — extensão em X da região ``gum`` acima /
      abaixo de ``mouth.z``; canónico (arco maxilar, mulher): intermolar
      **47.9 mm**, intercanino 34.3 mm (arco mandibular 39.9 / 26.2).
    * ``teeth_span`` — extensão em X da região ``enamel``.
    * ``ear_*`` — por anel registado ``head.ear.<lado>`` (S4.2).
    """
    builder, anat = build.builder, build.anatomy
    V, lm = builder.verts, anat.landmarks
    out: dict = {}

    def _span(ids, ax):
        vals = [V[i][ax] for i in ids]
        return (max(vals) - min(vals)) if ids else None

    skull = sorted({i for name, ids in builder.rings.items()
                    if name.startswith("head.skull.") for i in ids})
    out["head_breadth"] = _span(skull, 0)
    out["head_depth"] = _span(skull, 1)
    out["head_height"] = lm["vertex"].z - lm["chin"].z
    out["interpupillary"] = (lm["eye.L"] - lm["eye.R"]).length

    lip = [i for i, r in enumerate(builder.regions) if r == "lip"]
    out["mouth_width"] = _span(lip, 0)
    out["mouth_width_landmarks"] = abs(lm["mouth_corner.L"].x - lm["mouth_corner.R"].x)
    if lip:
        out["lip_vermilion"] = {
            "upper": max(V[i].z for i in lip) - lm["mouth"].z,
            "lower": lm["mouth"].z - min(V[i].z for i in lip),
            "protrusion": max(V[i].y for i in lip) - lm["mouth"].y,
        }
    else:
        out["lip_vermilion"] = None

    for tag, sgn in (("L", 1), ("R", -1)):
        ids = [i for i, r in enumerate(builder.regions)
               if r == "eye" and (V[i].x > 0) == (sgn > 0)]
        out[f"eye_aperture.{tag}"] = (_span(ids, 0), _span(ids, 2)) if ids else None

    out["nose_length"] = abs(lm["nose_root"].z - lm["nose_tip"].z)
    out["nose_protrusion"] = lm["nose_tip"].y - lm["nose_root"].y
    nost = [i for i, r in enumerate(builder.regions) if r == "nostril"]
    out["nose_breadth"] = _span(nost, 0) if nost else None

    gum = [i for i, r in enumerate(builder.regions) if r == "gum"]
    out["arch_upper"] = _span([i for i in gum if V[i].z > lm["mouth"].z], 0)
    out["arch_lower"] = _span([i for i in gum if V[i].z <= lm["mouth"].z], 0)
    tooth = [i for i, r in enumerate(builder.regions) if r == "enamel"]
    out["teeth_span"] = _span(tooth, 0)

    for tag in ("L", "R"):
        ids = sorted({i for name, ring in builder.rings.items()
                      if name.startswith(f"head.ear.{tag}") for i in ring})
        if ids:
            out[f"ear.{tag}"] = {
                "length": _span(ids, 2),
                "breadth": _span(ids, 1),           # profundidade ântero-posterior
                "protrusion": (max(abs(V[i].x) for i in ids)
                               - abs(lm[f"ear.{tag}"].x)),
                "top_above_eye": max(V[i].z for i in ids) - lm["eye"].z,
                "bottom_above_nose_base": min(V[i].z for i in ids) - lm["nose_base"].z,
            }
        else:
            out[f"ear.{tag}"] = None
    ears = [i for name, ids in builder.rings.items() if name.startswith("head.ear.")
            for i in ids]
    out["bitragion"] = 2.0 * max(abs(V[i].x) for i in ears) if ears else None
    return out


def silhouette(builder, view: str = "front", res: int = 128) -> dict:
    """Silhueta ortográfica rasterizada, com **preenchimento** por scanline.

    A primeira versão marcava só pontos ao longo das arestas; medido, isso
    produzia um contorno de uma célula de espessura com falhas na diagonal e a
    contagem de regiões 2D explodia (52 "regiões" para um cubo fechado — o
    instrumento a medir-se a si próprio).  Preencher cada face projetada com
    regra par-ímpar dá a silhueta real (1 região para o cubo), área em m² e
    linhas vazias que significam lacunas de verdade.
    """
    axes = {"front": (0, 2), "side": (1, 2), "top": (0, 1)}[view]
    ax, ay = axes
    verts = builder.verts
    a0 = min(p[ax] for p in verts)
    a1 = max(p[ax] for p in verts)
    b0 = min(p[ay] for p in verts)
    b1 = max(p[ay] for p in verts)
    # Cell size = extent/res (not (res-1)/extent): the earlier form put the last
    # scanline centre *outside* the geometry, leaving the extreme row empty —
    # measured on a closed cube (1 empty row), fixed here.
    fa = res / max(1e-9, a1 - a0)
    fb = res / max(1e-9, b1 - b0)
    grid = [[0] * res for _ in range(res)]
    for f in builder.faces:
        pts = [(verts[i][ax], verts[i][ay]) for i in f]
        lo = min(y for _, y in pts)
        hi = max(y for _, y in pts)
        r0 = max(0, int((lo - b0) * fb))
        r1 = min(res - 1, int((hi - b0) * fb))
        n = len(pts)
        for row in range(r0, r1 + 1):
            yc = b0 + (row + 0.5) / fb
            xs = []
            for i in range(n):
                x0, y0 = pts[i]
                x1, y1 = pts[(i + 1) % n]
                if (y0 <= yc < y1) or (y1 <= yc < y0):
                    t = (yc - y0) / (y1 - y0)
                    xs.append(x0 + (x1 - x0) * t)
            xs.sort()
            for k in range(0, len(xs) - 1, 2):
                c0 = max(0, min(res - 1, int((xs[k] - a0) * fa)))
                c1 = max(0, min(res - 1, int((xs[k + 1] - a0) * fa)))
                for cell in range(c0, c1 + 1):
                    grid[row][cell] = 1
    seen = [[False] * res for _ in range(res)]
    regions = 0
    area = 0
    for y0 in range(res):
        for x0 in range(res):
            if not grid[y0][x0] or seen[y0][x0]:
                continue
            regions += 1
            stack = [(y0, x0)]
            seen[y0][x0] = True
            while stack:
                y, x = stack.pop()
                area += 1
                for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    yy, xx = y + dy, x + dx
                    if 0 <= yy < res and 0 <= xx < res and grid[yy][xx] and not seen[yy][xx]:
                        seen[yy][xx] = True
                        stack.append((yy, xx))
    widths = [sum(row) for row in grid]
    cell_area = (1.0 / fa) * (1.0 / fb)
    return {"view": view, "res": res, "a_extent": a1 - a0, "b_extent": b1 - b0,
            "area_cells": area, "area_m2": area * cell_area,
            "regions": regions,
            "max_row_width": max(widths) if widths else 0,
            "empty_rows": sum(1 for w in widths if w == 0)}


# --------------------------------------------------------------------------- report
def integration_report(build) -> dict:
    """Relatório completo de integração para um ``BuildResult``."""
    b = build.builder
    anat = build.anatomy if hasattr(build, "anatomy") else None
    comps = connected_components(b)
    labels = component_labels(b, comps)
    graph = overlap_graph(b, comps=comps, labels=labels)
    report = {
        "components": len(comps),
        "component_sizes": [len(c) for c in comps[:12]],
        "component_labels": labels[:12],
        "overlap_edges": len(graph["edges"]),
        "label_edges": {f"{a}|{b}": n for (a, b), n in sorted(graph["label_edges"].items())},
        "floating": floating_components(b),
        "boundary_edges": sum(boundary_edges(b).values()),
        "boundary_by_regions": {f"{a}/{b}": n for (a, b), n in boundary_edges(b).items()},
        "mirror": mirror_stats(b, tol=1e-5),
        "mirror_hausdorff": structure_mirror_hausdorff(b),
        "root_insertion": root_insertion(b, comps=comps, labels=labels),
        "floor": floor_contact(b),
        "silhouette": {v: silhouette(b, v) for v in ("front", "side")},
    }
    if anat is not None:
        report["envelope"] = height_envelope(b, anat)
        report["feet"] = foot_metrics(b, anat, comps=comps)
    return report


# --------------------------------------------------------------------------- openings (S4.2)
def _boundary_loops(builder) -> list[list[int]]:
    """Laços de fronteira (arestas com exactamente uma face), por componentes."""
    from collections import Counter
    cnt: Counter = Counter()
    for f in builder.faces:
        for a, b in zip(f, f[1:] + f[:1]):
            cnt[tuple(sorted((a, b)))] += 1
    adj: dict[int, list[int]] = {}
    for (a, b), n in cnt.items():
        if n == 1:
            adj.setdefault(a, []).append(b)
            adj.setdefault(b, []).append(a)
    seen, loops = set(), []
    for v0 in list(adj):
        if v0 in seen:
            continue
        stack, comp = [v0], []
        seen.add(v0)
        while stack:
            v = stack.pop()
            comp.append(v)
            for w in adj[v]:
                if w not in seen:
                    seen.add(w)
                    stack.append(w)
        loops.append(sorted(comp))
    return loops


def head_openings_metrics(build) -> dict:
    """Aberturas da cabeça (S4.2): laços de fronteira + visibilidade do globo.

    Definições (nenhuma medida sem critério escrito):

    * ``loops`` — laços de fronteira da malha da CABEÇA (``skull.*`` + orelhas),
      classificados por proximidade ao centro declarado da abertura:
      ``orbita.L/R`` (marco ``eye.<lado>``, ≤ 25 mm), ``oral`` (marco ``mouth``,
      ≤ 30 mm) e ``narina.L/R`` (±0.043·H da base do nariz, ≤ 15 mm).
    * ``globe_visible`` — o primeiro toque de um raio lançado do CENTRO do globo
      ao longo do eixo do olho (``eyes.eye_axis``) contra as faces de pele da
      cabeça.  ``None`` = não há pele à frente do globo ⇒ a abertura existe.
      (O critério original A1, "nenhum vértice dentro do cilindro do globo", é
      geometricamente impossível — ver docs/S4_FACE.md §9.)
    * ``mouth_open_mm`` — largura do laço ``oral``; comparada com a distância
      entre as comissuras (``mouth_corner.L``↔``mouth_corner.R``).
    * ``nostril_span_mm`` — distância entre os extremos exteriores dos dois
      laços das narinas; ``nostril_gap_mm`` — folga entre eles.
    """
    # S4.2 — a medição é feita na CASCA DA CABEÇA (`build_head`), não no
    # construtor fundido: no fundido convivem as pálpebras, os lábios e as
    # gengivas, que têm as suas próprias fronteiras abertas perto dos mesmos
    # marcos.  Medido com o construtor fundido: 19 laços dentro do raio de
    # classificação (8 deles das pálpebras/lábios), o que torna a contagem de
    # aberturas ambígua.  A casca da cabeça, isolada, tem exactamente 7 laços:
    # boca (76), orelhas (48 + 48), órbitas (32 + 32) e narinas (10 + 10).
    from ..generators.head import build_head          # noqa: PLC0415  (evita ciclo)
    anat = getattr(build, "anatomy", None) or getattr(build.build, "anatomy", None)
    spec = getattr(build, "spec", None) or getattr(build.build, "spec", None)
    b = build_head(spec, anat).builder
    lm = anat.landmarks
    h = anat.h
    V = b.verts
    loops = _boundary_loops(b)
    out = {"loops": [], "boundary_edges": 0, "globe_visible": {}, "mouth": {}, "nostrils": {}}
    from collections import Counter
    cnt: Counter = Counter()
    for f in b.faces:
        for a, bb in zip(f, f[1:] + f[:1]):
            cnt[tuple(sorted((a, bb)))] += 1
    out["boundary_edges"] = sum(1 for n in cnt.values() if n == 1)

    def bbox(ids):
        xs = [V[i].x for i in ids]; ys = [V[i].y for i in ids]; zs = [V[i].z for i in ids]
        return (max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs))

    def centre(ids):
        n = len(ids)
        return Vector((sum(V[i].x for i in ids) / n, sum(V[i].y for i in ids) / n,
                       sum(V[i].z for i in ids) / n))

    targets = {
        "orbita.L": (Vector(lm["eye.L"]), 0.025),
        "orbita.R": (Vector(lm["eye.R"]), 0.025),
        "oral": (Vector(lm["mouth"]), 0.030),
        "narina.L": (Vector(lm["nose_base"]) + Vector((0.043 * h, 0.002 * h, -0.010 * h)), 0.015),
        "narina.R": (Vector(lm["nose_base"]) + Vector((-0.043 * h, 0.002 * h, -0.010 * h)), 0.015),
    }
    found: dict[str, list[int]] = {}
    for ids in loops:
        if len(ids) < 4:
            continue
        c = centre(ids)
        best = None
        for name, (t, rad) in targets.items():
            d = (c - t).length
            if d < rad and (best is None or d < best[1]):
                best = (name, d)
        if best is None:
            continue
        ext = bbox(ids)
        out["loops"].append({"abertura": best[0], "n": len(ids),
                             "bbox_mm": [round(e * 1000, 1) for e in ext],
                             "centro_mm": [round(v * 1000, 1) for v in c]})
        found.setdefault(best[0], []).append(ids)

    # globo: primeiro toque de pele a partir do centro do globo, ao longo do eixo
    from ..generators.eyes import eye_axis          # noqa: PLC0415  (evita ciclo no import)

    def ray_tri(o, d, p0, p1, p2):
        e1, e2 = p1 - p0, p2 - p0
        pv = d.cross(e2)
        det = e1.dot(pv)
        if abs(det) < 1e-12:
            return None
        inv = 1.0 / det
        tv = o - p0
        u = tv.dot(pv) * inv
        if u < 0.0 or u > 1.0:
            return None
        qv = tv.cross(e1)
        v = d.dot(qv) * inv
        if v < 0.0 or u + v > 1.0:
            return None
        t = e2.dot(qv) * inv
        return t if t > 1e-9 else None

    skin = [(f, m) for f, m in zip(b.faces, b.face_mat) if m == "skin"]
    for side, tag in ((1, "L"), (-1, "R")):
        c = Vector(lm[f"eye.{tag}"])
        ax = eye_axis(anat, side)
        best = None
        for f, _m in skin:
            pts = [V[i] for i in f]
            for k in range(1, len(pts) - 1):
                t = ray_tri(c, ax, pts[0], pts[k], pts[k + 1])
                if t is not None and (best is None or t < best):
                    best = t
        out["globe_visible"][tag] = {
            "primeiro_toque_pele_mm": None if best is None else round(best * 1000.0, 2),
            "raio_globo_mm": round(0.0555 * h * 1000.0, 2),
            "visivel": best is None or best > 0.0555 * h,
        }

    if "oral" in found:
        ids = max(found["oral"], key=len)
        ext = bbox(ids)
        lips = (Vector(lm["mouth_corner.L"]) - Vector(lm["mouth_corner.R"])).length
        out["mouth"] = {"abertura_largura_mm": round(ext[0] * 1000, 1),
                        "abertura_altura_mm": round(ext[2] * 1000, 1),
                        "boca_labios_mm": round(lips * 1000, 1),
                        "menor_que_labios": ext[0] < lips}
    if "narina.L" in found and "narina.R" in found:
        l = max(found["narina.L"], key=len)
        r = max(found["narina.R"], key=len)
        xl = [V[i].x for i in l]
        xr = [V[i].x for i in r]
        gap = min(xl) - max(xr)
        span = max(xl) - min(xr)
        out["nostrils"] = {"largura_L_mm": round((max(xl) - min(xl)) * 1000, 1),
                           "largura_R_mm": round((max(xr) - min(xr)) * 1000, 1),
                           "folga_mm": round(gap * 1000, 1),
                           "vão_exterior_mm": round(span * 1000, 1)}
    return out
