# -*- coding: utf-8 -*-
"""S1 — contracts for ``core/_math.py`` (the "silent zero mask" bug family)."""
from __future__ import annotations

import math

import pytest

from human_generator.core import _math
from human_generator.core._math import Matrix, Vector, clamp, mix, smoothstep


class TestRamps:
    """``smoothstep`` with a > b must still ramp (it silently zeroed every mask)."""

    def test_increasing_edges(self):
        assert smoothstep(0.0, 1.0, -1.0) == 0.0
        assert smoothstep(0.0, 1.0, 0.0) == 0.0
        assert smoothstep(0.0, 1.0, 0.5) == pytest.approx(0.5)
        assert smoothstep(0.0, 1.0, 1.0) == 1.0
        assert smoothstep(0.0, 1.0, 2.0) == 1.0

    def test_decreasing_edges(self):
        """Reversed-edge regression: a=0.8 > b=0.52 used to return 0 everywhere.

        Semantics (documented by the implementation and used by the face masks):
        the value is 1.0 where x is *inside* the mask (x <= b for a > b) and 0.0
        beyond a — at exactly b the mask is already fully applied.
        """
        assert smoothstep(0.8, 0.52, 0.0) == 1.0
        assert smoothstep(0.8, 0.52, 0.52) == 1.0
        assert smoothstep(0.8, 0.52, 0.8) == 0.0
        assert smoothstep(0.8, 0.52, 0.9) == 0.0
        mid = smoothstep(0.8, 0.52, 0.66)
        assert 0.0 < mid < 1.0, f"reversed-edge ramp is flat: {mid}"

    def test_monotonic_both_directions(self):
        up = [smoothstep(0.0, 1.0, i / 20) for i in range(21)]
        assert up == sorted(up)
        down = [smoothstep(1.0, 0.0, i / 20) for i in range(21)]
        assert down == sorted(down, reverse=True), "reversed ramp must be monotone"

    def test_degenerate_edges(self):
        assert smoothstep(0.5, 0.5, 0.4) == 0.0
        assert smoothstep(0.5, 0.5, 0.5) == 1.0
        assert smoothstep(0.5, 0.5, 0.6) == 1.0


class TestScalars:
    def test_clamp(self):
        assert clamp(5.0, 0.0, 1.0) == 1.0
        assert clamp(-5.0, 0.0, 1.0) == 0.0
        assert clamp(0.25, 0.0, 1.0) == 0.25

    def test_mix(self):
        assert mix(2.0, 4.0, 0.0) == 2.0
        assert mix(2.0, 4.0, 1.0) == 4.0
        assert mix(2.0, 4.0, 0.25) == pytest.approx(2.5)


class TestVector:
    def test_basics(self):
        v = Vector((3.0, 4.0, 0.0))
        assert v.length == pytest.approx(5.0)
        assert v.normalized().length == pytest.approx(1.0)
        assert (v + Vector((1, 1, 1))).x == 4.0
        assert (v * 2.0).y == 8.0
        assert v.dot(Vector((0, 1, 0))) == 4.0

    def test_cross_is_right_handed(self):
        x = Vector((1.0, 0.0, 0.0))
        y = Vector((0.0, 1.0, 0.0))
        assert (x.cross(y) - Vector((0.0, 0.0, 1.0))).length < 1e-12

    def test_opposite_vectors_normalise_to_unit(self):
        """``normalized()`` must stay exact at 180° (used for limb frames)."""
        a = Vector((1.0, 0.0, 0.0))
        b = Vector((-1.0, 0.0, 0.0))
        out = b - a * b.dot(a)          # tangential component: exactly zero
        assert out.length == pytest.approx(0.0, abs=1e-12)


class TestMatrix:
    def test_identity_and_apply(self):
        ident = Matrix.Identity(4)
        p = Vector((1.0, 2.0, 3.0))
        assert (ident @ p - p).length < 1e-12

    def test_rotation_about_z(self):
        m = Matrix.Rotation(math.pi / 2, 4, (0.0, 0.0, 1.0))
        p = m @ Vector((1.0, 0.0, 0.0))
        assert (p - Vector((0.0, 1.0, 0.0))).length < 1e-9

    def test_translation(self):
        m = Matrix.Translation(Vector((0.0, 0.0, 1.0)))
        assert (m @ Vector((0.0, 0.0, 0.0))).z == pytest.approx(1.0)

    def test_inverse_round_trip(self):
        m = Matrix.Translation(Vector((1.0, 2.0, 3.0))) @ Matrix.Rotation(0.7, 4, (0.0, 1.0, 0.0))
        p = Vector((0.3, -0.2, 0.5))
        assert ((m.inverted() @ (m @ p)) - p).length < 1e-6


class TestNumericsPolicy:
    """S0 discovery: the backend is import-order dependent, so it must be declared."""

    def test_info_shape(self):
        info = _math.numerics_info()
        assert info["backend"] in ("mathutils", "pure-python")
        assert info["float_precision"] in (32, 64)
        assert info["backend"] == ("mathutils" if info["float_precision"] == 32
                                   else "pure-python")

    def test_env_can_force_pure_backend(self):
        """Verified in a *subprocess*: reloading the module in-process re-binds
        Vector/Matrix classes and poisons every other module holding the old
        ones (measured: 20 spurious failures).  Import-time policy needs a fresh
        interpreter anyway."""
        import os
        import subprocess
        import sys

        code = ("import human_generator.core._math as m; "
                "print(m.numerics_info()['backend'], m.numerics_info()['float_precision'])")
        env = dict(os.environ, HCG_MATHUTILS="0")
        out = subprocess.run([sys.executable, "-c", code], capture_output=True,
                             text=True, env=env, cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        assert out.returncode == 0, out.stderr
        assert out.stdout.split() == ["pure-python", "64"], out.stdout

    def test_auto_is_default(self):
        info = _math.numerics_info()
        assert info["preference"] == "auto" or info["preference"] == ""
