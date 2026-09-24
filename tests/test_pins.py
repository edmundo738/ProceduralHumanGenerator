# -*- coding: utf-8 -*-
"""S1 — the determinism gate must actually measure geometry.

A pin that never fails is decoration.  These tests prove the gate is wired to
the numbers it claims to protect, and that topology stays constant across
presets (the property the whole rig/shape-key plan depends on).
"""
from __future__ import annotations

import copy

import pytest

import human_generator as hcg

import pins


class TestGateIsLive:
    def test_default_build_passes_its_pins(self, build_default):
        assert pins.check_build(build_default) == []
        assert build_default.contract_version == pins.CONTRACT_VERSION_PIN

    def test_changed_geometry_fails_the_pins(self):
        """Meta-test: move a geometry parameter, the gate must notice."""
        modified = hcg.build_character("realistic_female", seed=42,
                                       overrides={"face.nose_tip_projection": 0.6})
        failures = pins.check_build(modified)
        assert failures, "the pin gate did not notice a changed nose profile"
        assert any("digest" in f for f in failures)

    def test_changed_seed_fails_the_pins(self):
        other = hcg.build_character("realistic_female", seed=43)
        assert pins.check_build(other), "a different seed must not satisfy the pin"
        assert pins.check_build(other) != [], "pin should compare fingerprint/digest"

    @pytest.mark.parametrize("field", ["non_manifold_edges", "degenerate_faces",
                                       "loose_edges", "ngons", "boundary_edges"])
    def test_audit_pins_are_live(self, field):
        """Meta-test: every pinned audit counter must react to a change.

        Values are derived from the pin (pin + 1) rather than hard-coded, so the
        meta-test stays live when the pins are deliberately flipped.
        """
        audit = dict(pins.AUDIT_PINS)
        assert pins.check_audit(audit) == []
        broken = dict(audit, **{field: pins.AUDIT_PINS[field] + 1})
        assert pins.check_audit(broken), f"changing audit[{field}] must fail the pin"

    def test_semantic_pins_are_live(self, build_default):
        """The label populations are pinned, and the gate reacts to drift."""
        assert pins.check_semantics(build_default) == []
        broken = copy.deepcopy(build_default)
        broken.builder.regions[0] = "not-a-region"
        failures = pins.check_semantics(broken)
        assert failures, "a changed region label must fail the semantic pin"
        assert any("regions" in f for f in failures)

    def test_missing_numerics_backend_is_reported(self, build_default):
        class Fake:
            contract_version = pins.CONTRACT_VERSION_PIN
            fingerprint = pins.PINS[("realistic_female", 42)]["fingerprint"]
            verts, faces = 5759, 5608
            digest = "whatever"
            numerics = {}
            hair = type("H", (), {"strands": [0] * 2400})()
        failures = pins.check_build(Fake())
        assert any("numerics" in f for f in failures)


class TestTopologyStability:
    def test_counts_identical_across_presets(self, preset_names):
        """The generated cage must not change size with the preset (G2 property)."""
        got = {}
        for name in preset_names:
            r = hcg.build_character(name, seed=7)
            got[name] = (r.verts, r.faces, len(r.hair.strands))
        assert got == pins.PRESET_COUNTS, got

    def test_counts_identical_under_extremes(self):
        base = hcg.build_character("realistic_female", seed=7)
        extremes = {"face.nose_tip_projection": 1.9, "face.lip_fullness": 0.25,
                    "face.eye_spacing": 1.35, "face.jaw_width": 1.5,
                    "face.ear_size": 0.7, "body.head_units": 6.4,
                    "body.stature": 1.50}
        extreme = hcg.build_character("realistic_female", seed=7, overrides=extremes)
        assert (extreme.verts, extreme.faces) == (base.verts, base.faces)

    def test_geometry_really_changes_under_extremes(self):
        base = hcg.build_character("realistic_female", seed=7)
        extreme = hcg.build_character("realistic_female", seed=7,
                                      overrides={"body.head_units": 6.4})
        assert extreme.digest != base.digest

    @pytest.mark.parametrize("preset", ["realistic_female", "cyber_angel", "neon_idol"])
    def test_every_preset_is_deterministic(self, preset):
        a = hcg.build_character(preset, seed=13)
        b = hcg.build_character(preset, seed=13)
        assert (a.digest, a.fingerprint) == (b.digest, b.fingerprint)
