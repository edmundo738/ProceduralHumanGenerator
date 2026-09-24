# -*- coding: utf-8 -*-
"""The public parameter contract.

A :class:`CharacterSpec` fully describes a character: proportions, facial
morphology, skin, hair, pipeline budget and cosmetic extras.  Everything
downstream (geometry, weights, shaders, GN graphs) is a pure function of the
spec, which makes generation reproducible and diffable.

Ranges used by :meth:`CharacterSpec.randomized` mirror adult anthropometric
distributions — random seeds give *plausible* people, not aliens.
"""
from __future__ import annotations

import dataclasses
import json
import math
import os
from dataclasses import dataclass, field
from typing import Any

PRESET_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "presets")


@dataclass
class BodyParams:
    stature: float = 1.70                    # metres
    head_units: float = 7.65                 # 8-head classical canon
    neck_length: float = 1.0
    shoulder_head_ratio: float = 1.85        # biacromial / head height
    chest_breath: float = 1.0
    bust_relative: float = 1.0               # soft-tissue overhang
    waist_hip_ratio: float = 0.755
    hip_width_scale: float = 1.0
    fat_level: float = 0.30
    muscle_tone: float = 0.45
    limb_length: float = 1.0
    hand_size: float = 1.0
    finger_length: float = 1.0
    palm_breadth: float = 1.0
    foot_size: float = 1.0
    breath_scale: float = 1.0
    posture_lean: float = 0.0                # -1 hunched … +1 chest-up

    @property
    def head_height(self) -> float:
        return self.stature / self.head_units


@dataclass
class FaceParams:
    eye_spacing: float = 1.0
    eye_width: float = 1.0
    eye_depth: float = 1.0                   # socket shallowness
    eyelid_fold: float = 1.0
    brow_thickness: float = 1.0
    brow_height: float = 1.0
    nose_bridge: float = 1.0
    nose_length: float = 1.0
    nose_width: float = 1.0
    nose_tip_projection: float = 1.0
    nostril_flare: float = 1.0
    philtrum_length: float = 1.0
    lip_fullness: float = 1.0
    mouth_width: float = 1.0
    cupid_bow: float = 1.0
    smile_rest: float = 0.15
    jaw_width: float = 1.0
    jaw_projection: float = 1.0
    chin_projection: float = 1.0
    cheekbone_height: float = 1.0
    cheek_fullness: float = 1.0
    ear_size: float = 1.0
    asymmetry: float = 0.25                  # drives hair part / moles / wink


@dataclass
class SkinParams:
    melanin: float = 0.45                    # 0 porcelain … 1 deep
    hemoglobin: float = 0.50                 # ruddiness
    freckle_amount: float = 0.20
    sun_exposure: float = 0.30
    roughness_mid: float = 0.45
    subsurface_strength: float = 0.65
    skin_pores: float = 0.50
    skin_oiliness: float = 0.50
    body_hair_amount: float = 0.15


@dataclass
class HairParams:
    strand_count: int = 2400
    hair_length: float = 0.55                # metres (crown reference)
    curl: float = 0.35                       # 0 straight … 1 tight coil
    frizz: float = 0.25
    density: float = 1.0
    part_offset: float = 0.12                # −1 centred … +1 deep side
    melanin: float = 0.55
    thickness: float = 1.0
    clump: float = 0.40
    style: str = "loose"                     # loose|sleek|updo|short|curly


@dataclass
class PipelineParams:
    subdiv_preview: int = 1
    subdiv_render: int = 2
    adaptive_density: bool = True
    poly_budget: int = 120_000               # tris on the skinned mesh @ render
    micro_detail: float = 0.5
    displacement_scale: float = 0.0006       # metres of true displacement
    make_uvs: bool = True
    make_rig: bool = True
    make_shape_keys: bool = True
    export_glb: bool = True
    export_blend: bool = True
    render_preview: bool = True
    preview_resolution: tuple = (960, 1280)
    preview_samples: int = 24
    fuse: bool = False                       # voxel-remesh fused skin (print)
    quality: bool = True
    shape_keys_mirror: bool = True


@dataclass
class ExtrasParams:
    clothing: str = "bodysuit"               # none|crop_top|bodysuit|dress|armorsuit
    cybernetic: float = 0.0                  # 0..1 plating amount
    neon: float = 0.0                        # 0..1 emissive lines
    angelic: float = 0.0                     # 0..1 wings + halo
    wing_span: float = 1.0
    iris_tint: tuple = (0.34, 0.52, 0.42)    # eye hue hint (0-1 rgb)
    hair_tint: tuple = (0.30, 0.20, 0.14)


# ----------------------------------------------------------------------------- ranges
RANGES: dict[str, tuple[float, float] | None] = {
    "body.stature": (1.56, 1.82), "body.head_units": (7.30, 8.00),
    "body.neck_length": (0.9, 1.15), "body.shoulder_head_ratio": (1.60, 2.10),
    "body.chest_breath": (0.92, 1.10), "body.bust_relative": (0.50, 1.60),
    "body.waist_hip_ratio": (0.68, 0.92), "body.hip_width_scale": (0.90, 1.14),
    "body.fat_level": (0.10, 0.62), "body.muscle_tone": (0.15, 0.90),
    "body.limb_length": (0.96, 1.05), "body.hand_size": (0.93, 1.08),
    "body.finger_length": (0.90, 1.12), "body.palm_breadth": (0.90, 1.12),
    "body.foot_size": (0.93, 1.08), "body.posture_lean": (-0.3, 0.4),
    "face.eye_spacing": (0.92, 1.10), "face.eye_width": (0.86, 1.14),
    "face.eye_depth": (0.7, 1.4), "face.eyelid_fold": (0.5, 1.4),
    "face.brow_thickness": (0.6, 1.6), "face.brow_height": (0.7, 1.3),
    "face.nose_bridge": (0.75, 1.25), "face.nose_length": (0.85, 1.18),
    "face.nose_width": (0.82, 1.22), "face.nose_tip_projection": (0.75, 1.30),
    "face.nostril_flare": (0.6, 1.3), "face.philtrum_length": (0.85, 1.2),
    "face.lip_fullness": (0.60, 1.50), "face.mouth_width": (0.85, 1.18),
    "face.cupid_bow": (0.4, 1.6), "face.smile_rest": (0.0, 0.35),
    "face.jaw_width": (0.85, 1.20), "face.jaw_projection": (0.75, 1.30),
    "face.chin_projection": (0.65, 1.35), "face.cheekbone_height": (0.6, 1.4),
    "face.cheek_fullness": (0.5, 1.4), "face.ear_size": (0.8, 1.2),
    "skin.melanin": (0.12, 0.80), "skin.hemoglobin": (0.25, 0.75),
    "skin.freckle_amount": (0.0, 0.55), "skin.sun_exposure": (0.05, 0.7),
    "skin.roughness_mid": (0.35, 0.60), "skin.subsurface_strength": (0.45, 0.85),
    "skin.skin_pores": (0.2, 0.85), "skin.skin_oiliness": (0.2, 0.8),
    "skin.body_hair_amount": (0.0, 0.5),
    "hair.hair_length": (0.12, 0.85), "hair.curl": (0.05, 0.85),
    "hair.frizz": (0.05, 0.55), "hair.density": (0.7, 1.3),
    "hair.part_offset": (-0.8, 0.8), "hair.melanin": (0.10, 0.92),
    "hair.thickness": (0.7, 1.4), "hair.clump": (0.0, 0.9),
}


# ----------------------------------------------------------------------------- spec
_GROUP_TYPES = {
    "body": BodyParams, "face": FaceParams, "skin": SkinParams,
    "hair": HairParams, "pipeline": PipelineParams, "extras": ExtrasParams,
}


PRESET_FORMAT_VERSION = 1
"""Preset/spec document format version (bumped on incompatible layout changes)."""

_META_KEYS = {"format_version"}
_TOP_KEYS = ("seed", "name", "preset")


class SpecCompatibilityWarning(UserWarning):
    """Emitted when a spec/preset document is unknown, older or newer than this build.

    Policy (adopted from the comparative study, docs/RESEARCH_COMPARATIVE_01.md F8):
    unknown data is *reported*, never silently ignored.
    """


def _warn(message: str) -> None:
    import warnings
    warnings.warn(message, SpecCompatibilityWarning, stacklevel=3)


def _check_document(data: dict, source: str | None) -> None:
    """Report unknown keys/fields and format-version mismatches.

    ``source=None`` marks an internal field dict (``CharacterSpec.to_dict()``
    output): unknown keys are still reported, but a missing ``format_version``
    is not, because a field dict is not a document.
    """
    if not isinstance(data, dict):
        raise TypeError(f"{source}: expected a mapping, got {type(data).__name__}")
    label = source or "spec"
    version = data.get("format_version")
    if version is None:
        if source is not None:
            _warn(f"{source}: does not declare 'format_version'; assuming "
                  f"{PRESET_FORMAT_VERSION}")
    elif isinstance(version, int) and version > PRESET_FORMAT_VERSION:
        _warn(f"{source}: declares format_version {version} but this build "
              f"understands {PRESET_FORMAT_VERSION}; unknown keys will be ignored")
    for key in data:
        if key in _top_group_names() or key in _TOP_KEYS or key in _META_KEYS:
            continue
        _warn(f"{label}: unknown top-level key {key!r} ignored")
    for group in _GROUP_TYPES:
        block = data.get(group)
        if isinstance(block, dict):
            valid = {f.name for f in dataclasses.fields(_GROUP_TYPES[group])}
            for field in block:
                if field not in valid:
                    _warn(f"{label}: unknown field {group + '.' + field!r} ignored")


def _top_group_names():
    return tuple(_GROUP_TYPES)


def _coerce(cls, data: dict):
    keep = {f.name for f in dataclasses.fields(cls)}
    return cls(**{k: v for k, v in data.items() if k in keep})


@dataclass
class CharacterSpec:
    seed: int = 0
    name: str = "character"
    preset: str = "realistic_female"
    body: BodyParams = field(default_factory=BodyParams)
    face: FaceParams = field(default_factory=FaceParams)
    skin: SkinParams = field(default_factory=SkinParams)
    hair: HairParams = field(default_factory=HairParams)
    pipeline: PipelineParams = field(default_factory=PipelineParams)
    extras: ExtrasParams = field(default_factory=ExtrasParams)

    # -- construction -----------------------------------------------------------
    @classmethod
    def from_preset(cls, preset: str = "realistic_female", seed: int = 0,
                    randomize: bool = False, **overrides) -> "CharacterSpec":
        data = dict(load_preset(preset))
        data["preset"] = preset
        data["seed"] = int(seed)
        for key, value in overrides.items():
            if "." in key:
                g, f = key.split(".", 1)
                data.setdefault(g, {})[f] = value
            else:
                data[key] = value
        spec = cls.from_dict(data, source=f"preset:{preset}")
        if randomize:
            spec = spec.randomized(seed=int(seed))
        return spec

    @classmethod
    def from_dict(cls, data: dict, *, source: str | None = None) -> "CharacterSpec":
        _check_document(data, source)
        kwargs: dict[str, Any] = {}
        for g, cls_ in _GROUP_TYPES.items():
            if g in data:
                kwargs[g] = _coerce(cls_, dict(data[g]))
        for f in dataclasses.fields(cls):
            if f.name in ("seed", "name", "preset"):
                kwargs[f.name] = data.get(f.name, getattr(cls, f.name, None)) \
                    if f.name in data else None
        kwargs = {k: v for k, v in kwargs.items() if v is not None}
        return cls(**kwargs)

    @classmethod
    def from_json(cls, path: str) -> "CharacterSpec":
        with open(path, "r") as fh:
            return cls.from_dict(json.load(fh), source=os.path.basename(path))

    def to_dict(self) -> dict:
        d = {"seed": self.seed, "name": self.name, "preset": self.preset}
        for g in _GROUP_TYPES:
            d[g] = dataclasses.asdict(getattr(self, g))
        for k, v in d.items():
            if isinstance(v, dict):
                d[k] = {kk: (list(vv) if isinstance(vv, tuple) else vv)
                        for kk, vv in v.items()}
        return d

    def to_json(self, path: str) -> None:
        """Write a spec document (always carrying ``format_version``)."""
        data = self.to_dict()
        data["format_version"] = PRESET_FORMAT_VERSION
        os.makedirs(os.path.dirname(os.path.abspath(path)) or ".", exist_ok=True)
        with open(path, "w") as fh:
            json.dump(data, fh, indent=2, sort_keys=True)

    @property
    def format_version(self) -> int:
        return PRESET_FORMAT_VERSION

    def merged(self, overrides: dict) -> "CharacterSpec":
        data = self.to_dict()
        for key, value in overrides.items():
            if key in _GROUP_TYPES and isinstance(value, dict):
                data[key].update(value)
            elif "." in key:
                g, f = key.split(".", 1)
                data.setdefault(g, {})[f] = value
            else:
                data[key] = value
        return CharacterSpec.from_dict(data)

    # -- variation ---------------------------------------------------------------
    def randomized(self, seed: int = 0, amount: float = 1.0) -> "CharacterSpec":
        """Draw every ranged parameter from its anthropometric interval."""
        from .core.rng import Rng
        rng = Rng((int(seed) * 7919 + self.seed) & 0xFFFFFFFF)
        data = self.to_dict()
        for key, (lo, hi) in RANGES.items():
            g, f = key.split(".")
            cur = data[g].get(f)
            if cur is None or isinstance(cur, str):
                continue
            sampled = rng.f(lo, hi)
            data[g][f] = cur + (sampled - cur) * max(0.0, min(1.0, amount))
        if rng.bool(0.35):
            data["hair"]["style"] = rng.choice(["loose", "sleek", "short", "updo"])
        return CharacterSpec.from_dict(data)

    # -- helpers -------------------------------------------------------------------
    @property
    def head_height(self) -> float:
        return self.body.stature / self.body.head_units

    def fingerprint(self) -> str:
        blob = json.dumps(self.to_dict(), sort_keys=True, default=str)
        return _blake(blob)


def _blake(s: str) -> str:
    import hashlib
    return hashlib.blake2s(s.encode("utf-8"), digest_size=8).hexdigest()


# ----------------------------------------------------------------------------- presets
def list_presets() -> list[str]:
    if not os.path.isdir(PRESET_DIR):
        return []
    return sorted(os.path.splitext(f)[0] for f in os.listdir(PRESET_DIR) if f.endswith(".json"))


def load_preset(name: str) -> dict:
    path = os.path.join(PRESET_DIR, f"{name}.json")
    if not os.path.isfile(path):
        if name in ("realistic_female", "default", ""):
            return {}
        raise FileNotFoundError(f"unknown preset '{name}' (have: {', '.join(list_presets())})")
    with open(path, "r") as fh:
        return json.load(fh)
