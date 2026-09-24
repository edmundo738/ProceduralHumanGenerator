# -*- coding: utf-8 -*-
"""S3 — o instrumento de integração tem de medir o que diz medir.

Cada teste constrói uma malha pequena e sintética cujo resultado é conhecido à
mão, porque um instrumento que nunca falha é decoração (a mesma regra do gate de
pinos em S1).
"""
from __future__ import annotations

import math

import pytest

from human_generator.core._math import Vector
from human_generator.core.topology import MeshBuilder
from human_generator.core.integration import (
    boundary_edges, connected_components, cross_section_width, floating_components,
    floor_contact, height_envelope, integration_report, junction_metrics, mirror_stats,
    overlap_graph, part_distance, part_vertices, silhouette, structure_mirror_hausdorff,
    width_profile,
)
from human_generator.spec import CharacterSpec
from human_generator.core.anatomy import Anatomy


def _quad(b: MeshBuilder, x: float, z: float = 0.0, size: float = 0.1, region: str = "skin"):
    ids = [b.add_vert(Vector((x + dx, 0.0, z + dz)), region) for dx, dz in
           ((0, 0), (size, 0), (size, size), (0, size))]
    b.add_face(ids, material="skin")
    return ids


class TestComponents:
    def test_two_disjoint_quads_are_two_components(self):
        b = MeshBuilder("t")
        _quad(b, 0.0)
        _quad(b, 1.0)
        assert [len(c) for c in connected_components(b)] == [4, 4]

    def test_shared_vertices_merge_components(self):
        b = MeshBuilder("t")
        a = _quad(b, 0.0)
        # second quad reusing two of the first quad's vertices
        ids = [a[1], a[2], b.add_vert(Vector((0.2, 0.0, 0.2))), b.add_vert(Vector((0.0, 0.0, 0.2)))]
        b.add_face(ids, material="skin")
        assert [len(c) for c in connected_components(b)] == [6]


class TestFloating:
    def test_far_apart_quad_is_floating(self):
        b = MeshBuilder("t")
        _quad(b, 0.0)
        _quad(b, 1.0)
        found = floating_components(b, gap=0.005)
        assert len(found) == 2, "both quads are isolated at 5 mm"

    def test_interpenetrating_coarse_shells_are_adjacent(self):
        """Vértices esparsos não medem adjacência; a amostra de superfície mede.

        Duas cascas que se cruzam mas cujos vértices distam > 5 mm têm de contar
        como adjacentes (foi exactamente este o caso medido no tronco/pernas).
        """
        b = MeshBuilder("t")
        big = [b.add_vert(Vector((x, 0.0, z)), "skin")
               for x, z in ((0.0, 0.0), (0.6, 0.0), (0.6, 0.6), (0.0, 0.6))]
        b.add_face(big, material="skin")
        small = [b.add_vert(Vector((x, 0.0, z)), "skin")
                 for x, z in ((0.28, 0.28), (0.32, 0.28), (0.32, 0.32), (0.28, 0.32))]
        b.add_face(small, material="skin")
        assert floating_components(b, gap=0.010) == []

    def test_touching_parts_are_not_floating(self):
        b = MeshBuilder("t")
        _quad(b, 0.0, size=0.1)
        _quad(b, 0.105, size=0.1)      # 5 mm apart
        assert floating_components(b, gap=0.01) == []
        assert len(overlap_graph(b, gap=0.01)["edges"]) == 1


class TestBoundary:
    def test_single_quad_has_four_boundary_edges(self):
        b = MeshBuilder("t")
        _quad(b, 0.0)
        assert sum(boundary_edges(b).values()) == 4

    def test_two_quads_sharing_an_edge_have_six(self):
        b = MeshBuilder("t")
        a = _quad(b, 0.0)
        ids = [a[1], a[2], b.add_vert(Vector((0.2, 0.0, 0.2))), b.add_vert(Vector((0.0, 0.0, 0.2)))]
        b.add_face(ids, material="skin")
        assert sum(boundary_edges(b).values()) == 6

    def test_shared_edge_is_not_boundary(self):
        b = MeshBuilder("t")
        a = _quad(b, 0.0)
        b.add_face([a[2], a[3], b.add_vert(Vector((0.0, 0.0, -0.1))),
                    b.add_vert(Vector((0.1, 0.0, -0.1)))], material="skin")
        edges = boundary_edges(b)
        assert edges == {("skin", "skin"): 6}, edges


class TestMirror:
    def test_exact_mirror_has_no_misses(self):
        b = MeshBuilder("t")
        for s in (1, -1):
            b.add_vert(Vector((s * 0.1, 0.0, 0.0)), "skin")
        assert mirror_stats(b, tol=1e-6)["misses"] == 0

    def test_offset_pair_is_detected(self):
        b = MeshBuilder("t")
        b.add_vert(Vector((0.1, 0.0, 0.0)), "skin")
        b.add_vert(Vector((-0.1005, 0.0, 0.0)), "skin")     # 0.5 mm off
        stats = mirror_stats(b, tol=1e-6)
        assert stats["misses"] == 2
        assert stats["misses_by_region"] == {"skin": 2}

    def test_hausdorff_between_structures_is_zero_for_mirrors(self):
        b = MeshBuilder("t")
        for s, tag in ((1, "L"), (-1, "R")):
            for k in range(3):
                i = b.add_vert(Vector((s * 0.1, 0.01 * k, 0.02 * k)), "skin")
                b.set_group(f"{tag}.finger.index.0", i, 1.0)
        assert structure_mirror_hausdorff(b)["finger.index.0"] == pytest.approx(0.0)

    def test_hausdorff_grows_with_real_asymmetry(self):
        b = MeshBuilder("t")
        for s, tag in ((1, "L"), (-1, "R")):
            off = 0.0 if s > 0 else 0.004          # right side 4 mm shorter in z
            for k in range(3):
                i = b.add_vert(Vector((s * 0.1, 0.0, 0.02 * k + off)), "skin")
                b.set_group(f"{tag}.finger.index.0", i, 1.0)
        assert structure_mirror_hausdorff(b)["finger.index.0"] == pytest.approx(0.004, rel=0.05)


class TestEnvelope:
    def test_floor_contact_counts_verts_below_the_plane(self):
        b = MeshBuilder("t")
        _quad(b, 0.0, z=0.0)
        _quad(b, 0.3, z=-0.0077, size=0.02)   # 2 of its 4 verts are below z=0
        f = floor_contact(b)
        assert f["below"] == 2
        assert f["deepest"] == pytest.approx(-0.0077)
        assert f["regions_below"] == {"skin": 2}

    def test_height_envelope_uses_the_anatomy_scale(self):
        """A estação ``vertex`` do canon é a referência do topo do crânio.

        S3.4 reconciliou a tabela com a geometria medida (``vertex`` = 0.991 da
        estatura, não 1.000), por isso o teste usa a estação, não a estatura —
        o valor escalar da estatura deixou de ser a referência do topo.
        """
        spec = CharacterSpec.from_preset("realistic_female", seed=42)
        anat = Anatomy.from_spec(spec)
        b = MeshBuilder("t")
        for z in (0.0, anat.z("vertex")):
            b.add_vert(Vector((0.0, 0.0, z)), "scalp")
        env = height_envelope(b, anat)
        assert env["height"] == pytest.approx(anat.z("vertex"))
        assert env["scalp_minus_vertex"] == pytest.approx(0.0)
        assert anat.z("vertex") < anat.stature, "o canon reconciliado fica abaixo da estatura"


class TestSilhouette:
    def test_closed_box_is_one_region(self):
        b = MeshBuilder("t")
        s = 0.05
        cube = [[(-s, -s, -s), (s, -s, -s), (s, s, -s), (-s, s, -s)],
                [(-s, -s, s), (s, -s, s), (s, s, s), (-s, s, s)]]
        ids = [[b.add_vert(Vector(p), "skin") for p in ring] for ring in cube]
        b.add_face(ids[0], material="skin")
        b.add_face(list(reversed(ids[1])), material="skin")
        for i in range(4):
            j = (i + 1) % 4
            b.add_face([ids[0][i], ids[0][j], ids[1][j], ids[1][i]], material="skin")
        sil = silhouette(b, "front", res=64)
        assert sil["regions"] == 1
        assert sil["empty_rows"] == 0
        assert sil["a_extent"] == pytest.approx(2 * s, rel=1e-6)

    def test_two_spaced_boxes_are_two_regions(self):
        b = MeshBuilder("t")
        for cx in (-0.2, 0.2):
            _quad(b, cx, size=0.02)
        sil = silhouette(b, "front", res=64)
        assert sil["regions"] == 2, sil
        assert sil["empty_rows"] == 0


class TestFeetAreAnthropometric:
    """S3.6 — o critério dos pés como gate permanente.

    Baseline medido antes da correcção: largura 182.8 mm (canonical 93.5 mm,
    +96 %), comprimento 288.6 mm (canonical 258.4 mm, +12 %) e as duas cascas a
    tocarem-se no plano médio (|x| min = 0.2 mm), o que as fundia numa massa só.
    """

    def test_foot_metrics_present(self, build_default):
        """O pé é um conjunto de cascas por lado (casca + cinco dedos + unha)."""
        from human_generator.core.integration import foot_metrics
        m = foot_metrics(build_default.builder, build_default.anatomy)
        assert set(m["feet"]) == {"L", "R"}, m
        assert m["n_shells"]["L"] >= 6, m["n_shells"]   # foot + toes (+nail)
        assert m["n_shells"]["L"] == m["n_shells"]["R"], m["n_shells"]

    def test_foot_width_within_15_percent_of_canon(self, build_default):
        from human_generator.core.integration import foot_metrics
        m = foot_metrics(build_default.builder, build_default.anatomy)
        for side, f in m["feet"].items():
            assert f["width_ratio"] <= 1.15, f"foot {side} width ratio {f['width_ratio']:.3f}"

    def test_foot_length_within_5_percent_of_canon(self, build_default):
        """Banda de dois lados: um pé demasiado CURTO também é defeito."""
        from human_generator.core.integration import foot_metrics
        m = foot_metrics(build_default.builder, build_default.anatomy)
        for side, f in m["feet"].items():
            assert 0.90 <= f["length_ratio"] <= 1.05, \
                f"foot {side} length ratio {f['length_ratio']:.3f}"

    def test_feet_do_not_touch_at_the_midline(self, build_default):
        from human_generator.core.integration import foot_metrics
        m = foot_metrics(build_default.builder, build_default.anatomy)
        assert m["separation"] >= 0.010, \
            f"feet only {m['separation']*1000:.1f} mm apart — they read as one mass"

    def test_foot_height_is_plausible(self, build_default):
        """Altura do pé (tornozelo incluído) ≤ 0.075·estatura ≈ 128 mm."""
        from human_generator.core.integration import foot_metrics
        m = foot_metrics(build_default.builder, build_default.anatomy)
        limit = 0.075 * build_default.anatomy.stature
        for side, f in m["feet"].items():
            assert f["height"] <= limit, f"foot {side} height {f['height']*1000:.1f} mm > {limit*1000:.1f}"


class TestNoCoincidentVertices:
    """S3.6 — guarda contra um defeito medido, não hipotético.

    ``cap_pole`` deslocava o pólo 1.68 mm FIXOS, independentemente do raio do
    anel; na ponta de um dedo (r = 5.5 mm) o pólo caía a 9.2e-6 m de um vértice
    do próprio anel e o ``weld`` por omissão da API pública (``1e-5``) fundia-os
    — 2 arestas non-manifold num build que se dizia limpo.  A propriedade que
    tem de valer é esta: **nenhum par de vértices distintos mais próximo do que
    o weld por omissão**, senão o weld muda a topologia (e o ``weld`` é no-op
    em toda a grelha S2).
    """

    WELD = 1e-5   # default of hcg.generate_character

    @staticmethod
    def _closest_pair(verts):
        cell = TestNoCoincidentVertices.WELD
        buckets: dict = {}
        for i, v in enumerate(verts):
            buckets.setdefault((round(v.x / cell), round(v.y / cell),
                                round(v.z / cell)), []).append(i)
        best = (float("inf"), -1, -1)
        for (kx, ky, kz), ids in buckets.items():
            for dx in (0, 1):
                for dy in (-1, 0, 1):
                    for dz in (-1, 0, 1):
                        if (dx, dy, dz) <= (0, 0, 0):
                            continue
                        other = buckets.get((kx + dx, ky + dy, kz + dz), ())
                        for i in ids:
                            for j in other:
                                d = (verts[i] - verts[j]).length
                                if d < best[0]:
                                    best = (d, i, j)
        return best

    def test_no_two_vertices_are_closer_than_the_default_weld(self, build_default):
        verts = list(build_default.builder.verts)
        d, i, j = self._closest_pair(verts)
        assert d >= self.WELD, (
            f"v{i} and v{j} are {d:.3e} m apart (< weld {self.WELD:g}); the "
            f"default weld would merge them and change the topology")

    def test_weld_is_a_no_op_on_the_default_build(self, build_default):
        """O weld por omissão não pode remover vértices (senão NM sobe).

        Precisa de ``bmesh`` (só existe dentro do Blender): em pytest puro o
        teste é SALTADO com motivo declarado, não silenciado — a propriedade
        equivalente e independente do backend é a do teste anterior e corre
        sempre.
        """
        bmesh_ok = True
        try:
            import bmesh  # noqa: F401
        except ImportError:
            bmesh_ok = False
        if not bmesh_ok:
            import pytest
            pytest.skip("bmesh requires Blender; vertex-pair guard above covers it")
        bm = build_default.builder.to_bmesh(weld=1e-5, dissolve=1e-5)
        n = len(bm.verts)
        bm.free()
        assert n == len(build_default.builder.verts), (
            f"weld+dissolve removed {len(build_default.builder.verts) - n} verts")


class TestJunctionInstrument:
    """S3.7 — o instrumento mede secções por planos e identifica partes por ANEL.

    Todos os valores esperados são derivados à mão da malha construída.
    """

    @staticmethod
    def _box(b: MeshBuilder, *, x0, x1, z0, z1, prefix: str, y0=-0.05, y1=0.05):
        """Caixa fechada (6 faces) com anéis registados por cota."""
        xs, ys, zs = (x0, x1), (y0, y1), (z0, z1)
        ids = {}
        for i, x in enumerate(xs):
            for j, y in enumerate(ys):
                for k, z in enumerate(zs):
                    ids[(i, j, k)] = b.add_vert(Vector((x, y, z)), "skin")
        f = ids
        faces = [
            [(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0)],   # bottom
            [(0, 0, 1), (0, 1, 1), (1, 1, 1), (1, 0, 1)],   # top
            [(0, 0, 0), (0, 1, 0), (0, 1, 1), (0, 0, 1)],
            [(1, 0, 0), (1, 0, 1), (1, 1, 1), (1, 1, 0)],
            [(0, 0, 0), (0, 0, 1), (1, 0, 1), (1, 0, 0)],
            [(0, 1, 0), (1, 1, 0), (1, 1, 1), (0, 1, 1)],
        ]
        for face in faces:
            b.add_face([f[k] for k in face], material="skin")
        b.rings[prefix + ".0"] = [f[(i, j, k)] for i in (0, 1) for j in (0, 1) for k in (0,)]
        b.rings[prefix + ".1"] = [f[(i, j, k)] for i in (0, 1) for j in (0, 1) for k in (1,)]
        return b

    def test_part_vertices_uses_the_ring_registry(self):
        b = MeshBuilder("t")
        self._box(b, x0=0.0, x1=0.1, z0=0.0, z1=0.1, prefix="arm.L")
        self._box(b, x0=0.2, x1=0.3, z0=0.0, z1=0.1, prefix="leg.L")
        # cada caixa regista 2 anéis de 4 vértices = 8
        assert len(part_vertices(b, "arm.L")) == 8
        assert len(part_vertices(b, "leg.L")) == 8
        assert len(part_vertices(b, "arm.L", "leg.L")) == 16
        # prefixos agregam (arm = os dois braços); prefixos que não existem = vazio
        assert len(part_vertices(b, "arm")) == 8
        assert part_vertices(b, "arms") == set()

    def test_cross_section_width_is_a_plane_intersection(self):
        b = MeshBuilder("t")
        self._box(b, x0=0.0, x1=0.2, z0=0.0, z1=0.2, prefix="trunk")
        ids = part_vertices(b, "trunk")
        # a meio da caixa a largura é 0.2, independentemente de haver vértices lá
        assert cross_section_width(b, ids, 0.10) == pytest.approx(0.2, abs=1e-12)
        # fora da caixa não há secção
        assert cross_section_width(b, ids, 0.25) is None
        # e a secção não conta com outras partes
        self._box(b, x0=0.5, x1=0.9, z0=0.0, z1=0.2, prefix="other")
        assert cross_section_width(b, ids, 0.10) == pytest.approx(0.2, abs=1e-12)

    def test_width_profile_steps(self):
        b = MeshBuilder("t")
        self._box(b, x0=0.0, x1=0.2, z0=0.0, z1=0.2, prefix="trunk")
        prof = width_profile(b, part_vertices(b, "trunk"), 0.0, 0.2, step=0.05)
        assert len(prof) == 5
        # nas cotas EXACTAS das tampas o plano é tangente às faces (sem
        # travessia) — a secção só existe a 0.05/0.10/0.15; é o comportamento
        # correcto de uma intersecção por arestas e está medido aqui
        vals = [w for _, w in prof if w is not None]
        assert len(vals) == 3, [w for _, w in prof]
        assert vals == pytest.approx([0.2] * 3, abs=1e-12)

    def test_part_distance_zero_when_touching_and_positive_when_apart(self):
        b = MeshBuilder("t")
        self._box(b, x0=0.0, x1=0.1, z0=0.0, z1=0.1, prefix="a")
        self._box(b, x0=0.1, x1=0.2, z0=0.0, z1=0.1, prefix="b")   # encostadas
        a, c = part_vertices(b, "a"), part_vertices(b, "b")
        assert part_distance(b, a, c) == pytest.approx(0.0, abs=1e-9)
        b2 = MeshBuilder("t2")
        self._box(b2, x0=0.0, x1=0.1, z0=0.0, z1=0.1, prefix="a")
        self._box(b2, x0=0.13, x1=0.2, z0=0.0, z1=0.1, prefix="b")
        a2, c2 = part_vertices(b2, "a"), part_vertices(b2, "b")
        assert part_distance(b2, a2, c2) == pytest.approx(0.03, abs=1e-9)

    def test_junction_metrics_reports_every_criterion(self, build_default):
        m = junction_metrics(build_default)
        for key in ("neck", "shoulder", "steps", "arm_pose", "leg_pose"):
            assert key in m, m.keys()
        for side in ("L", "R"):
            assert f"foot.{side}" in m["steps"], m["steps"]
            assert f"hand.{side}" in m["steps"], m["steps"]
            assert f"knee.{side}" in m["leg_pose"], m["leg_pose"]


class TestS37CriteriaOnRealBuild:
    """S3.7 — os critérios J1..J5, medidos na personagem por omissão."""

    def test_j1_neck_is_narrower_than_head_and_shoulders(self, build_default):
        n = junction_metrics(build_default)["neck"]
        assert n["ratio_min_over_head"] <= 0.80, n
        assert n["ratio_min_over_shoulder"] <= 0.35, n

    def test_j2_shoulder_width_is_within_20_percent_of_biacromial(self, build_default):
        s = junction_metrics(build_default)["shoulder"]
        assert s["ratio_over_biacromial"] <= 1.20, s

    def test_j3_junction_jump_is_a_tenth_of_parent_width(self, build_default):
        m = junction_metrics(build_default)
        for name, st in m["steps"].items():
            limit = 0.10 * st["above_mm"]
            assert abs(st["step_mm"]) <= limit, (name, st, limit)

    def test_j4_arms_hang(self, build_default):
        for name, p in junction_metrics(build_default)["arm_pose"].items():
            assert p["dx_mm"] <= p["limit_mm"], (name, p)

    def test_j5_knees_align_with_hips(self, build_default):
        for name, p in junction_metrics(build_default)["leg_pose"].items():
            assert p["dx_mm"] <= p["limit_mm"], (name, p)

    def test_hand_does_not_penetrate_the_leg(self, build_default):
        """A pose pendente não pode enterrar a mão na coxa (S3.7, medido)."""
        b = build_default.builder
        for tag in ("L", "R"):
            gap = part_distance(b, part_vertices(b, f"hand.{tag}"),
                                part_vertices(b, f"leg.{tag}"))
            assert gap > 0.0, f"hand.{tag} intersects the leg (gap {gap:.4f} m)"


class TestS38CriteriaOnRealBuild:
    """S3.8 — dimensões da mão (fonte FAA/DOT; ver docs/S3_8_HANDS.md)."""

    @staticmethod
    def _m(build_default, side="L"):
        from human_generator.core.integration import hand_metrics
        return hand_metrics(build_default, side)

    def test_h1_hand_length_within_5_percent_of_faa(self, build_default):
        for side in ("L", "R"):
            m = self._m(build_default, side)
            assert 0.95 <= m["length_ratio_faa"] <= 1.05, (side, m)

    def test_h2_hand_width_within_10_percent_of_faa(self, build_default):
        for side in ("L", "R"):
            m = self._m(build_default, side)
            assert 0.90 <= m["width_ratio_faa"] <= 1.10, (side, m)

    def test_h3_palm_thickness_bounded(self, build_default):
        for side in ("L", "R"):
            m = self._m(build_default, side)
            assert m["thickness_over_length"] <= 0.165, (side, m)

    def test_h4_knuckle_span_is_anatomically_placed(self, build_default):
        for side in ("L", "R"):
            m = self._m(build_default, side)
            assert 0.36 <= m["mcp_span_over_length"] <= 0.42, (side, m)

    def test_h5_fingers_are_separated(self, build_default):
        for side in ("L", "R"):
            gaps = self._m(build_default, side)["finger_gaps"]
            for name, g in gaps.items():
                if name == "thumb-index":
                    continue
                assert g >= 0.001, (side, name, g)

    def test_h6_thumb_is_free_of_the_index(self, build_default):
        for side in ("L", "R"):
            g = self._m(build_default, side)["finger_gaps"]["thumb-index"]
            assert g >= 0.005, (side, g)

    def test_hands_are_mirror_identical(self, build_default):
        """O pé/mão direita tem de ser o espelho exacto da esquerda (S3.1)."""
        l, r = self._m(build_default, "L"), self._m(build_default, "R")
        for key in ("length", "width", "thickness", "mcp_span"):
            assert abs(l[key] - r[key]) < 1e-9, (key, l[key], r[key])


class TestS41FaceCriteriaOnRealBuild:
    """S4.1 — proporções da face (fontes em docs/S4_FACE.md §2)."""

    @staticmethod
    def _f(build_default):
        from human_generator.core.integration import face_metrics
        return face_metrics(build_default)

    def test_f1_skull_breadth(self, build_default):
        m = self._f(build_default)
        assert 0.93 <= m["head_breadth"] / 0.144 <= 1.07, m["head_breadth"]

    def test_f2_cranial_depth(self, build_default):
        m = self._f(build_default)
        assert 0.93 <= m["head_depth"] / 0.183 <= 1.07, m["head_depth"]

    def test_f3_mouth_width(self, build_default):
        m = self._f(build_default)
        assert 0.88 <= m["mouth_width"] / 0.0492 <= 1.12, m["mouth_width"]
        # malha e marcos têm de concordar (2 mm)
        assert abs(m["mouth_width"] - m["mouth_width_landmarks"]) < 0.002

    def test_f4_vermilion(self, build_default):
        v = self._f(build_default)["lip_vermilion"]
        assert 0.75 <= v["upper"] / 0.0065 <= 1.35, v["upper"]
        assert 0.75 <= v["lower"] / 0.0100 <= 1.30, v["lower"]

    def test_f6_interpupillary(self, build_default):
        m = self._f(build_default)
        assert 0.94 <= m["interpupillary"] / 0.062 <= 1.06, m["interpupillary"]

    def test_globe_is_covered_by_the_face_surface(self, build_default):
        """O globo não pode sobressair da pele: a córnea é a única parte exposta.

        S4.2 — medido antes do recuo do centro: o globo (r = 12.3 mm) estava
        centrado na própria superfície e 12.3 mm dele ficavam fora da face.
        """
        from human_generator.core._math import Vector  # noqa: F401
        b = build_default.builder
        V = b.verts
        skull = sorted({i for n, ids in b.rings.items()
                        if n.startswith("head.skull.") for i in ids})
        for sgn in (1, -1):
            eye = [i for i, reg in enumerate(b.regions)
                   if reg == "eye" and (V[i].x > 0) == (sgn > 0)]
            over = []
            for i in eye:
                p = V[i]
                cand = [V[j].y for j in skull
                        if abs(V[j].x - p.x) < 0.012 and abs(V[j].z - p.z) < 0.012]
                if cand and p.y > max(cand):
                    over.append(p.y - max(cand))
            assert not over or max(over) <= 0.006, (sgn, max(over) if over else None)


class TestS42HeadOpenings:
    """S4.2 — aberturas da cabeça (contrato docs/S4_FACE.md §8/§9)."""

    @staticmethod
    def _m(build_default):
        from human_generator.core.integration import head_openings_metrics
        return head_openings_metrics(build_default)

    def test_every_declared_opening_exists(self, build_default):
        m = self._m(build_default)
        names = {l["abertura"] for l in m["loops"]}
        for want in ("orbita.L", "orbita.R", "oral", "narina.L", "narina.R"):
            assert want in names, (want, sorted(names))

    def test_mouth_aperture_is_smaller_than_the_lips(self, build_default):
        m = self._m(build_default)["mouth"]
        assert m["menor_que_labios"], m
        assert m["abertura_altura_mm"] <= 8.0, m

    @pytest.mark.xfail(reason="S4.2b: faces grossas da grelha atravessam a abertura "
                              "do olho (medido: primeiro toque de pele a 4.17 mm "
                              "do centro de um globo de raio 12.33 mm); a abertura "
                              "existe e está medida (laço de 32 vértices, 22.9 x "
                              "12.7 mm), falta o recorte das faces que a cruzam",
                       strict=False)
    def test_globe_is_no_longer_covered_by_skin(self, build_default):
        m = self._m(build_default)["globe_visible"]
        for tag in ("L", "R"):
            assert m[tag]["visivel"], (tag, m[tag])

    def test_nostrils_are_two_and_separated(self, build_default):
        n = self._m(build_default)["nostrils"]
        assert n["folga_mm"] >= 5.0, n
        assert n["largura_L_mm"] >= 3.0 and n["largura_R_mm"] >= 3.0, n

    def test_left_and_right_openings_are_mirror_images(self, build_default):
        m = self._m(build_default)
        by = {}
        for l in m["loops"]:
            by.setdefault(l["abertura"], []).append(l)
        # Tolerância MEDIDA, não escolhida: o rebordo é re-amostrado com passo
        # angular uniforme em cada lado e as duas re-amostragens não partilham a
        # fase (o conjunto de vértices de partida não é espelho exacto).  Medido
        # depois da passagem de espelho: órbita 22.9/6.7/12.7 contra
        # 22.8/6.6/12.7 mm; narinas 11.6/11.6 mm de largura, centros a 0.2 mm do
        # espelho.  A simetria EXACTA do rebordo fica para S4.2b (precisa da
        # correspondência de índices antes do corte).
        for a, b in (("orbita.L", "orbita.R"), ("narina.L", "narina.R")):
            assert len(by[a]) == len(by[b]) == 1, (a, b, by)
            assert by[a][0]["n"] == by[b][0]["n"], (a, b)
            for ea, eb in zip(by[a][0]["bbox_mm"], by[b][0]["bbox_mm"]):
                assert abs(ea - eb) < 1.5, (a, b, ea, eb)
            assert abs(by[a][0]["centro_mm"][0] + by[b][0]["centro_mm"][0]) < 1.5, (a, b)

    def test_boundary_accounting_is_exact(self, build_default):
        """A fronteira da casca da cabeça cresce EXACTAMENTE com o corte.

        Medido: 168 arestas de fronteira antes do corte (orelhas incluídas) e
        328 depois — a diferença, 160, é exactamente a soma dos 5 laços do corte
        (32+32+76+10+10).  Nenhum outro buraco pode aparecer sem que este número
        mude.  Nota: a soma dos comprimentos dos laços NÃO é igual ao número de
        arestas de fronteira, porque um vértice de aperto pertence a dois laços
        (medido: 160 contra 328; a contagem de arestas é a que manda).
        """
        m = self._m(build_default)
        assert sum(l["n"] for l in m["loops"]) == 160, m["loops"]
        assert m["boundary_edges"] == 328, m["boundary_edges"]


class TestReportOnRealBuild:
    def test_report_has_all_criteria_and_no_floating_part(self, build_default):
        rep = integration_report(build_default)
        for key in ("components", "floating", "boundary_edges", "mirror", "floor",
                    "silhouette", "overlap_edges", "envelope"):
            assert key in rep, key
        assert rep["components"] > 10, "the character is a union of many shells"
        assert rep["floating"] == [], f"floating shells: {rep['floating']}"
        assert rep["boundary_edges"] > 0, "open rims are expected on a shell union"
        assert rep["silhouette"]["front"]["regions"] >= 1
        assert rep["silhouette"]["front"]["empty_rows"] == 0, \
            "a rasterised front silhouette must not have empty rows"
