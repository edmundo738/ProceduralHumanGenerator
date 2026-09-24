# -*- coding: utf-8 -*-
"""S1 — ``core/topology.py`` contracts, including the ring-degeneracy guard.

The guard exists because the eye globe's first latitude ring collapses to a
single point (``phi = -pi/2`` ⇒ ``cos(phi) = 6.1e-17``), and ``cap_pole`` then
adds a second collapsed ring on top of it: 26 coincident vertices per eye.  The
global weld hid that by fusing them, at the price of the non-manifold edges
measured in ``docs/RESEARCH_GATE_02.md``.  The pin below is the S2 target.
"""
from __future__ import annotations

import math

import pytest

from human_generator.core._math import Vector
from human_generator.core.topology import REGION_CODES, MeshBuilder, Section
from human_generator.spec import CharacterSpec
from human_generator.core.anatomy import Anatomy
from human_generator.generators.body import build_body
from human_generator.generators.eyes import build_eyes
from human_generator.generators.head import build_head
from human_generator.generators.mouth import build_mouth

import pins


def _ring(cx, cz, radius, n=12, y=0.0):
    return [Vector((cx + radius * math.cos(2 * math.pi * i / n), y,
                    cz + radius * math.sin(2 * math.pi * i / n))) for i in range(n)]


class TestSection:
    def test_point_endpoints_and_count(self):
        s = Section(center=Vector((0, 0, 0)), tangent=Vector((1, 0, 0)),
                    front=Vector((0, 1, 0)), width=0.2, depth=0.1)
        p0, p1 = s.point(0.0), s.point(1.0)
        assert (p0 - p1).length < 1e-12, "t is periodic: point(0) == point(1)"
        assert len(s.points(8)) == 8

    def test_points_are_distinct(self):
        s = Section(center=Vector((0, 0, 0)), tangent=Vector((1, 0, 0)),
                    front=Vector((0, 1, 0)), width=0.2, depth=0.1)
        pts = s.points(16)
        for i in range(len(pts)):
            for j in range(i + 1, len(pts)):
                assert (pts[i] - pts[j]).length > 1e-6

    def test_frame_is_orthonormal(self):
        s = Section(center=Vector((0, 0, 1)), tangent=Vector((1, 0.3, 0.2)),
                    front=Vector((0, 1, 0.1)), width=0.1, depth=0.1)
        assert abs(s.tangent.dot(s.front)) < 1e-12
        assert abs(s.axis.length - 1.0) < 1e-9

    def test_superellipse_clamped_to_ellipse(self):
        s = Section(center=Vector((0, 0, 0)), tangent=Vector((1, 0, 0)),
                    front=Vector((0, 1, 0)), superellipse=0.3)
        assert s.superellipse == pytest.approx(2.0)


class TestLoft:
    def test_counts_and_quads(self):
        b = MeshBuilder("unit")
        rings = [_ring(0, 0, 0.1 * (1 + i * 0.1), y=i * 0.05) for i in range(4)]
        res = b.loft(rings, close=True, region="skin", material="skin",
                     register="unit")
        assert b.stats()["verts"] == 4 * 12
        assert len(res["rings"]) == 4
        assert b.stats()["quad_ratio"] == pytest.approx(1.0)
        assert b.stats()["degenerate"] == 0

    def test_region_material_uv_assigned(self):
        b = MeshBuilder("unit")
        b.loft([_ring(0, 0, 0.1, y=0.0), _ring(0, 0, 0.1, y=0.1)], region="lip",
               material="lip")
        assert set(b.regions) == {"lip"}
        assert b.face_mat and all(m == "lip" for m in b.face_mat)
        assert all(0.0 <= u <= 1.0 and 0.0 <= v <= 1.0 for u, v in b.uvs)

    def test_cap_pole_creates_triangle_fan(self):
        b = MeshBuilder("unit")
        rings = [_ring(0, 0, 0.1, y=0.0), _ring(0, 0, 0.08, y=0.1)]
        b.loft(rings, cap_end="pole", register="cap")
        assert b.stats()["tris"] == 12, "pole cap must be a triangle fan"
        assert b.stats()["degenerate"] == 0

    def test_ring_registry(self):
        b = MeshBuilder("unit")
        b.loft([_ring(0, 0, 0.1, y=0.0), _ring(0, 0, 0.1, y=0.1)], register="unit")
        assert {"unit.0", "unit.1"} <= set(b.rings), "one registry entry per station"
        assert len(b.rings["unit.0"]) == 12
        assert len(b._flatten_ring_ids(b.rings["unit.1"])) == 12


class TestDegeneracyGuard:
    def test_clean_builder_reports_nothing(self):
        b = MeshBuilder("unit")
        b.loft([_ring(0, 0, 0.1, y=0.0), _ring(0, 0, 0.1, y=0.1)], register="ok")
        assert b.rings_degenerate() == {}

    def test_collapsed_ring_is_detected(self):
        b = MeshBuilder("unit")
        collapsed = [Vector((0.0, 0.0, 0.0)) for _ in range(13)]
        b.loft([collapsed, _ring(0, 0, 0.1, y=0.1)], register="bad")
        found = b.rings_degenerate()
        assert found.get("bad.0") == 13 * 12 // 2, f"expected C(13,2) pairs, got {found}"

    def test_body_and_head_are_clean(self):
        spec = CharacterSpec.from_preset("realistic_female", seed=42)
        anat = Anatomy.from_spec(spec)
        assert build_body(spec, anat).builder.rings_degenerate() == {}
        head = build_head(spec, anat).builder
        assert head.rings_degenerate() == {}

    def test_eyes_report_the_documented_defect(self, head_builder):
        """S2 target: fixing eyes.py must flip this pin to ``{}`` deliberately."""
        found = head_builder.rings_degenerate()
        assert found == pins.DEGENERATE_RING_PINS, \
            f"eye-pole pin changed: {found} != {pins.DEGENERATE_RING_PINS}"


class TestMirrorAndTransform:
    def test_mirror_merge_counts_and_groups(self):
        b = MeshBuilder("half")
        b.loft([_ring(0.2, 0, 0.1, y=0.0), _ring(0.2, 0, 0.1, y=0.1)], register="arm.L")
        b.set_group("arm.L", 0, 1.0)
        before = b.stats()["verts"]
        b.mirror_merge("X", group_suffix_map=("L", "R"))
        assert b.stats()["verts"] == before * 2
        assert any(g.endswith(".R") for g in b.groups), list(b.groups)
        assert "arm.R" in b.groups, "L groups must be re-tagged R on the copy"

    def test_transform_with_negative_determinant_flips_winding(self):
        b = MeshBuilder("unit")
        b.loft([_ring(0, 0, 0.1, y=0.0), _ring(0, 0, 0.1, y=0.1)])
        before = [tuple(f) for f in b.faces]
        from human_generator.core._math import Matrix
        b.transform(Matrix.Diagonal((-1.0, 1.0, 1.0, 1.0)))
        after = [tuple(f) for f in b.faces]
        assert before != after, "a mirroring transform must reverse winding"

    def test_bounds_and_stats_keys(self):
        b = MeshBuilder("unit")
        b.loft([_ring(0, 0, 0.1, y=0.0), _ring(0, 0, 0.1, y=0.1)])
        lo, hi = b.bounds()
        assert lo.z <= hi.z
        keys = set(b.stats())
        assert {"verts", "faces", "quad_ratio", "degenerate"} <= keys


class TestRegionCodes:
    def test_codes_unique_and_stable(self):
        values = list(REGION_CODES.values())
        assert len(values) == len(set(values)), "duplicate region codes"
        for name in ("skin", "lip", "enamel", "eye", "scalp"):
            assert name in REGION_CODES
