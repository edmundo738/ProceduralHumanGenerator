# -*- coding: utf-8 -*-
"""S1 — preset/spec document contract: version, tolerant load, round-trip (F8).

Policy adopted from the comparative study: unknown data is *reported*, never
silently ignored (``SpecCompatibilityWarning``), and every spec document carries
``format_version``.
"""
from __future__ import annotations

import json
import os
import warnings

import pytest

import human_generator as hcg
from human_generator.spec import (PRESET_FORMAT_VERSION, PRESET_DIR,
                                  SpecCompatibilityWarning)


def _load_raw(name: str) -> dict:
    with open(os.path.join(PRESET_DIR, f"{name}.json")) as fh:
        return json.load(fh)


class TestPresetDocuments:
    def test_all_presets_declare_format_version(self, preset_names):
        for name in preset_names:
            data = _load_raw(name)
            assert data.get("format_version") == PRESET_FORMAT_VERSION, \
                f"{name}.json must declare format_version"

    def test_presets_load_without_warnings(self, preset_names):
        for name in preset_names:
            with warnings.catch_warnings():
                warnings.simplefilter("error", SpecCompatibilityWarning)
                spec = hcg.CharacterSpec.from_preset(name, seed=42)
            assert spec.preset == name
            assert spec.format_version == PRESET_FORMAT_VERSION

    def test_preset_without_version_warns(self):
        with pytest.warns(SpecCompatibilityWarning, match="format_version"):
            hcg.CharacterSpec.from_dict({"body": {"stature": 1.7}}, source="unit")

    def test_preset_from_future_warns(self):
        with pytest.warns(SpecCompatibilityWarning, match="understands"):
            hcg.CharacterSpec.from_dict(
                {"format_version": PRESET_FORMAT_VERSION + 1}, source="unit")


class TestTolerantLoading:
    def test_unknown_top_level_key_warns_and_is_ignored(self):
        with pytest.warns(SpecCompatibilityWarning, match="unknown top-level"):
            spec = hcg.CharacterSpec.from_dict(
                {"format_version": PRESET_FORMAT_VERSION, "nonsense": 1}, source="unit")
        assert not hasattr(spec, "nonsense")
        assert spec.body.stature == pytest.approx(1.70)

    def test_unknown_group_field_warns_and_is_ignored(self):
        with pytest.warns(SpecCompatibilityWarning, match=r"unknown field 'face\.bogus'"):
            spec = hcg.CharacterSpec.from_dict(
                {"format_version": PRESET_FORMAT_VERSION, "face": {"bogus": 1, "nose_tip_projection": 1.4}},
                source="unit")
        assert spec.face.nose_tip_projection == pytest.approx(1.4)

    def test_missing_optionals_fall_back_to_defaults(self):
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            spec = hcg.CharacterSpec.from_dict(
                {"format_version": PRESET_FORMAT_VERSION}, source="unit")
        assert [str(w.message) for w in caught] == [], "empty document must load quietly"
        assert spec.body.stature == pytest.approx(1.70)
        assert spec.seed == 0

    def test_non_mapping_raises(self):
        with pytest.raises(TypeError):
            hcg.CharacterSpec.from_dict(["not", "a", "document"], source="unit")


class TestRoundTrip:
    @pytest.mark.parametrize("preset", ["realistic_female", "cyber_angel", "neon_idol"])
    def test_json_round_trip_preserves_fingerprint(self, preset, tmp_path):
        spec = hcg.CharacterSpec.from_preset(preset, seed=7)
        path = tmp_path / f"{preset}.json"
        spec.to_json(str(path))
        written = json.loads(path.read_text())
        assert written["format_version"] == PRESET_FORMAT_VERSION
        with warnings.catch_warnings():
            warnings.simplefilter("error", SpecCompatibilityWarning)
            back = hcg.CharacterSpec.from_json(str(path))
        assert back.fingerprint() == spec.fingerprint()
        assert back.to_dict() == spec.to_dict()

    def test_dict_round_trip(self):
        """Field dicts round-trip without warnings (they are not documents);
        when a source label *is* given, the missing version is reported."""
        spec = hcg.CharacterSpec.from_preset("realistic_female", seed=11)
        data = spec.to_dict()
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            quiet = hcg.CharacterSpec.from_dict(data)
        assert [str(w.message) for w in caught] == []
        assert quiet.fingerprint() == spec.fingerprint()
        with pytest.warns(SpecCompatibilityWarning, match="format_version"):
            hcg.CharacterSpec.from_dict(data, source="roundtrip")

    def test_fingerprint_reacts_to_parameters(self):
        a = hcg.CharacterSpec.from_preset("realistic_female", seed=1)
        b = hcg.CharacterSpec.from_preset("realistic_female", seed=2)
        c = hcg.CharacterSpec.from_preset("realistic_female", seed=1).merged(
            {"face.nose_tip_projection": 1.8})
        assert a.fingerprint() != b.fingerprint()
        assert a.fingerprint() != c.fingerprint()

    def test_merged_keeps_untouched_fields(self):
        import dataclasses
        spec = hcg.CharacterSpec.from_preset("cyber_angel", seed=3)
        other = spec.merged({"body.stature": 1.62})
        assert other.body.stature == pytest.approx(1.62)
        assert dataclasses.asdict(other.face) == dataclasses.asdict(spec.face)
