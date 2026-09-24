# -*- coding: utf-8 -*-
"""S1 — contracts for ``core/rng.py`` (determinism + noise bounds).

The ``fbm3``/``ridged3`` normalisation used to be ``... / max(1e-6, 1.0 - 0.5 **
octaves and 1.0)``, i.e. ``X and 1.0`` — always 1.0, so the divisor never
normalised anything (fBm was 1.75× oversized at 4 octaves).  No caller used it
(``grep -rn "\\.noise(" human_generator`` → only the ``field.Deformer`` mode,
itself unused), so the fix changes no geometry; these tests freeze the contract.
"""
from __future__ import annotations

import pytest

from human_generator.core.rng import Rng

PROBES = [(i * 0.37, i * 0.11, -i * 0.29) for i in range(600)]


class TestNoise:
    def test_noise3_range(self):
        rng = Rng(0)
        for p in PROBES:
            n = rng.noise3(*p)
            assert -1.0 <= n <= 1.0, f"noise3 out of range at {p}: {n}"

    def test_noise3_is_smooth_between_neighbours(self):
        rng = Rng(1)
        a = rng.noise3(0.5, 0.5, 0.5)
        b = rng.noise3(0.51, 0.5, 0.5)
        assert abs(a - b) < 0.2, "value noise is not interpolating"

    def test_seed_changes_field(self):
        a = [Rng(0).noise3(*p) for p in PROBES[:20]]
        b = [Rng(7).noise3(*p) for p in PROBES[:20]]
        assert a != b


class TestFbmContract:
    @pytest.mark.parametrize("octaves", [1, 2, 3, 4, 6])
    def test_fbm_bounds(self, octaves):
        rng = Rng(0)
        vals = [rng.fbm3(p, octaves=octaves) for p in PROBES]
        assert max(vals) <= 1.0 + 1e-9, f"fbm3 > 1 at octaves={octaves}: {max(vals)}"
        assert min(vals) >= -1.0 - 1e-9, f"fbm3 < -1 at octaves={octaves}: {min(vals)}"

    @pytest.mark.parametrize("octaves", [1, 4])
    def test_ridged_bounds(self, octaves):
        rng = Rng(0)
        vals = [rng.ridged3(p, octaves=octaves) for p in PROBES]
        assert max(vals) <= 1.0 + 1e-9 and min(vals) >= -1e-9, \
            f"ridged3 out of [0,1]: {min(vals)}..{max(vals)}"

    def test_single_octave_matches_noise(self):
        """With one octave the normaliser is 1, so fbm == noise."""
        rng = Rng(3)
        for p in PROBES[:50]:
            assert rng.fbm3(p, octaves=1) == pytest.approx(rng.noise3(*p))

    def test_amplitude_is_normalised(self):
        """At least one octave must reach close to full scale (not a tiny range)."""
        vals = [Rng(0).fbm3(p, octaves=3) for p in PROBES]
        assert max(vals) > 0.5, f"fbm3 under-scaled: max {max(vals)}"


class TestDeterminism:
    def test_same_seed_same_stream(self):
        a, b = Rng(42), Rng(42)
        assert [a.f() for _ in range(20)] == [b.f() for _ in range(20)]

    def test_float_range(self):
        rng = Rng(5)
        vals = [rng.f(-2.0, 3.0) for _ in range(200)]
        assert all(-2.0 <= v <= 3.0 for v in vals)
        assert len({round(v, 6) for v in vals}) > 50

    def test_choice(self):
        rng = Rng(6)
        picks = {rng.choice(["a", "b", "c"]) for _ in range(200)}
        assert picks == {"a", "b", "c"}

    def test_bool(self):
        rng = Rng(8)
        assert all(isinstance(rng.bool(0.5), bool) for _ in range(10))


class TestMeshDigest:
    def test_stable_and_sensitive(self):
        verts = [(0.1, 0.2, 0.3), (1.0, 2.0, 3.0)]
        assert Rng.mesh_digest(verts) == Rng.mesh_digest(list(verts))
        moved = [(0.1, 0.2, 0.3), (1.0, 2.0, 3.001)]
        assert Rng.mesh_digest(verts) != Rng.mesh_digest(moved)

    def test_resolution_is_five_decimals(self):
        """Documents the digest's resolution: sub-1e-5 moves are invisible."""
        a = [(0.1, 0.2, 0.3)]
        b = [(0.1, 0.2, 0.3 + 1e-7)]
        c = [(0.1, 0.2, 0.3 + 1e-3)]
        assert Rng.mesh_digest(a) == Rng.mesh_digest(b)
        assert Rng.mesh_digest(a) != Rng.mesh_digest(c)

    def test_length_and_hex(self):
        d = Rng.mesh_digest([(0.0, 0.0, 0.0)])
        assert len(d) == 16 and int(d, 16) >= 0
