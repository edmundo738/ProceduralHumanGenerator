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
    boundary_edges, connected_components, floating_components, floor_contact,
    height_envelope, integration_report, mirror_stats, overlap_graph,
    silhouette, structure_mirror_hausdorff,
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
