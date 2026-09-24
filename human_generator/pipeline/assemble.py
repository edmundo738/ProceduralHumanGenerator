# -*- coding: utf-8 -*-
"""S0 — public character API (contract ``hcg-charapi/1.0.0``).

This module is the *single* orchestration path from a :class:`CharacterSpec` to
a built character.  It exists because the package has advertised
``hcg.generate_character(...)`` since the first commit while the module behind
it (``human_generator.pipeline.assemble``) was never written; generation was
only reachable through ``tools/dev_smoke.py``, which duplicated the
orchestration by hand.

CONTRACT (frozen for S0)
------------------------
Input
    ``spec``: a :class:`CharacterSpec`, or a preset name (``str``), or ``None``
    (defaults to the ``realistic_female`` preset, seed 0).
    ``preset``/``overrides``/``seed``: explicit keyword overrides.
Output
    :func:`build_character` → :class:`BuildResult` (pure Python, no ``bpy``:
    geometry, hair, stats, digests).
    :func:`generate_character` → :class:`GenerationResult` (adds Blender data:
    objects, materials, audit, optional ``.blend`` + JSON report on disk).
Determinism
    Identical ``(spec, seed)`` ⇒ identical ``fingerprint`` and mesh ``digest``,
    and identical vertex/face counts and audit numbers **within one numerics
    regime**.  ``core._math`` uses ``mathutils`` (float32) when ``bpy`` is
    already imported and a pure-python stand-in (float64) otherwise, so digests
    are regime-specific: every result carries ``numerics`` describing the
    regime, and the Blender regime raises a warning.  Byte-identical ``.blend``
    files are **not** part of the contract (untested, UNKNOWN).
Errors
    * unknown preset            → ``ValueError``
    * unknown override key/field → ``ValueError``
    * bad ``spec``/``seed`` type → ``TypeError``
    * Blender runtime missing    → ``RuntimeError`` (use ``build_character``)
Version
    ``CONTRACT_VERSION`` — bump on any change to the above.  The version is
    stored on every result and in every JSON report.

Scope note (S0): orchestration only.  No new anatomy, generators, materials,
rig, cloth, animation or optimisation — the same generators ``dev_smoke``
already drove, called in the same order.
"""
from __future__ import annotations

import dataclasses
import json
import os
import time
from typing import Any, Mapping, Sequence

from ..core import _math
from ..core.anatomy import Anatomy
from ..core.rng import Rng
from ..generators.body import build_body
from ..generators.eyes import build_eyes
from ..generators.hair import build_hair
from ..generators.head import build_head
from ..generators.mouth import build_mouth
from ..spec import (BodyParams, CharacterSpec, ExtrasParams, FaceParams, HairParams,
                    PipelineParams, SkinParams, list_presets)

CONTRACT_VERSION = "1.0.0"

DEFAULT_PRESET = "realistic_female"
_TOP_LEVEL_FIELDS = ("seed", "name", "preset")


# ----------------------------------------------------------------------------- spec resolution
def _field_names(cls) -> set[str]:
    return {f.name for f in dataclasses.fields(cls)}


_GROUP_TYPES = {"body": BodyParams, "face": FaceParams, "skin": SkinParams,
                "hair": HairParams, "pipeline": PipelineParams, "extras": ExtrasParams}
_GROUP_FIELDS = {name: _field_names(cls) for name, cls in _GROUP_TYPES.items()}


def validate_overrides(overrides: Mapping[str, Any]) -> dict:
    """Validate ``{"group.field": value}`` (or top-level field) overrides.

    Unknown groups/fields raise ``ValueError`` instead of being silently
    ignored (the pre-S0 wrapper let typo'd keys pass straight through).
    """
    if not isinstance(overrides, Mapping):
        raise TypeError(f"overrides must be a mapping, got {type(overrides).__name__}")
    for key in overrides:
        if not isinstance(key, str):
            raise ValueError(f"override keys must be strings, got {key!r}")
        if "." in key:
            group, field = key.split(".", 1)
            if group not in _GROUP_FIELDS:
                raise ValueError(
                    f"unknown override group {group!r} in {key!r}; "
                    f"valid groups: {', '.join(sorted(_GROUP_FIELDS))}")
            if field not in _GROUP_FIELDS[group]:
                raise ValueError(
                    f"unknown field {field!r} in {key!r}; "
                    f"valid fields: {', '.join(sorted(_GROUP_FIELDS[group]))}")
        elif key not in _TOP_LEVEL_FIELDS:
            raise ValueError(
                f"unknown override key {key!r}; expected one of "
                f"{', '.join(_TOP_LEVEL_FIELDS)} or 'group.field'")
    return dict(overrides)


def resolve_spec(spec: CharacterSpec | str | None = None, *,
                 preset: str | None = None,
                 seed: int | None = None,
                 overrides: Mapping[str, Any] | None = None) -> CharacterSpec:
    """Normalise every accepted input form into a :class:`CharacterSpec`.

    Precedence: explicit ``seed`` > ``overrides['seed']`` > ``spec.seed``;
    explicit ``preset`` > ``spec``'s preset > :data:`DEFAULT_PRESET`.
    """
    overrides = validate_overrides(overrides or {})
    if isinstance(spec, str):
        if preset is not None and preset != spec:
            raise ValueError(f"conflicting presets: spec={spec!r} preset={preset!r}")
        preset, spec = spec, None
    if spec is not None and not isinstance(spec, CharacterSpec):
        raise TypeError(
            "spec must be a CharacterSpec, a preset name str, or None; "
            f"got {type(spec).__name__}")
    if seed is not None:
        if isinstance(seed, bool):
            raise TypeError("seed must be an int, got bool")
        try:
            seed = int(seed)
        except (TypeError, ValueError) as exc:
            raise TypeError(f"seed must be an int, got {seed!r}") from exc

    # identity path: nothing to re-resolve
    if spec is not None and preset is None and seed is None and not overrides:
        return spec

    preset = preset or (spec.preset if spec is not None else DEFAULT_PRESET)
    if not isinstance(preset, str):
        raise TypeError(f"preset must be a str, got {type(preset).__name__}")

    if spec is None:
        from ..spec import load_preset
        try:
            data = dict(load_preset(preset))
        except FileNotFoundError as exc:
            raise ValueError(
                f"unknown preset {preset!r}; available: {', '.join(list_presets())}"
            ) from exc
    else:
        data = spec.to_dict()
    data["preset"] = preset
    if seed is not None:
        data["seed"] = seed
    for key, value in overrides.items():
        if "." in key:
            group, field = key.split(".", 1)
            data.setdefault(group, {})[field] = value
        else:
            data[key] = value
    return CharacterSpec.from_dict(data)


# ----------------------------------------------------------------------------- results
@dataclasses.dataclass
class BuildResult:
    """Pure-Python build output (no ``bpy`` involved)."""

    spec: CharacterSpec
    anatomy: Anatomy
    builder: Any                 # core.topology.MeshBuilder (body+head+bun merged)
    hair: Any                    # generators.hair.HairResult
    eye_info: dict
    stats: dict
    digest: str
    fingerprint: str
    warnings: list[str] = dataclasses.field(default_factory=list)
    timings: dict[str, float] = dataclasses.field(default_factory=dict)
    numerics: dict = dataclasses.field(default_factory=dict)
    contract_version: str = CONTRACT_VERSION

    @property
    def verts(self) -> int:
        return int(self.stats.get("verts", 0))

    @property
    def faces(self) -> int:
        return int(self.stats.get("faces", 0))

    def to_dict(self) -> dict:
        return {
            "contract_version": self.contract_version,
            "fingerprint": self.fingerprint,
            "digest": self.digest,
            "stats": dict(self.stats),
            "warnings": list(self.warnings),
            "timings": dict(self.timings),
            "numerics": dict(self.numerics),
            "hair": {"strands": len(self.hair.strands),
                     "lashes": len(self.hair.lashes),
                     "brows": len(self.hair.brows),
                     "bun": self.hair.bun is not None},
        }


@dataclasses.dataclass
class GenerationResult:
    """Full generation output: build result + Blender data + audit."""

    build: BuildResult
    objects: dict[str, str] = dataclasses.field(default_factory=dict)
    materials: list[str] = dataclasses.field(default_factory=list)
    audit: dict = dataclasses.field(default_factory=dict)
    files: dict[str, str] = dataclasses.field(default_factory=dict)
    elapsed: float = 0.0
    contract_version: str = CONTRACT_VERSION

    # -- passthroughs so callers can treat a GenerationResult as a BuildResult
    @property
    def spec(self) -> CharacterSpec:
        return self.build.spec

    @property
    def builder(self):
        return self.build.builder

    @property
    def fingerprint(self) -> str:
        return self.build.fingerprint

    @property
    def digest(self) -> str:
        return self.build.digest

    @property
    def stats(self) -> dict:
        return self.build.stats

    @property
    def warnings(self) -> list[str]:
        return self.build.warnings

    @property
    def timings(self) -> dict:
        return self.build.timings

    @property
    def numerics(self) -> dict:
        return self.build.numerics

    def to_dict(self) -> dict:
        d = self.build.to_dict()
        d.update({
            "objects": dict(self.objects),
            "materials": list(self.materials),
            "audit": dict(self.audit),
            "files": dict(self.files),
            "elapsed": round(self.elapsed, 3),
            "contract_version": self.contract_version,
        })
        return d


# ----------------------------------------------------------------------------- build (pure)
def build_character(spec: CharacterSpec | str | None = None, *,
                    preset: str | None = None,
                    seed: int | None = None,
                    overrides: Mapping[str, Any] | None = None) -> BuildResult:
    """Build geometry + hair from a spec.  Pure Python; deterministic."""
    t0 = time.perf_counter()
    spec = resolve_spec(spec, preset=preset, seed=seed, overrides=overrides)
    timings: dict[str, float] = {}

    t = time.perf_counter()
    anat = Anatomy.from_spec(spec)
    timings["anatomy"] = time.perf_counter() - t

    t = time.perf_counter()
    body = build_body(spec, anat)
    timings["body"] = time.perf_counter() - t

    t = time.perf_counter()
    head = build_head(spec, anat)
    eye_info = build_eyes(spec, anat, head.builder)
    build_mouth(head.builder, spec, anat)
    timings["head+eyes+mouth"] = time.perf_counter() - t

    t = time.perf_counter()
    body.builder.merge(head.builder, group_prefix="head.")
    timings["merge_head"] = time.perf_counter() - t

    t = time.perf_counter()
    hair = build_hair(spec, anat, head.builder, eye_info)
    if hair.bun is not None:
        body.builder.merge(hair.bun, group_prefix="bun.")
    timings["hair"] = time.perf_counter() - t

    stats = body.builder.stats()
    digest = Rng.mesh_digest(body.builder.verts)

    numerics = {
        "backend": "mathutils" if _math.MATHUTILS else "pure-python",
        "float_precision": 32 if _math.MATHUTILS else 64,
    }
    warnings: list[str] = []
    if _math.MATHUTILS:
        warnings.append(
            "numerics: mathutils (float32) backend — digests are regime-specific and "
            "differ from the pure-python (float64) digest for the same spec; see README")
    if int(stats.get("degenerate", 0)) > 0:
        warnings.append(
            f"build produced {stats['degenerate']} degenerate faces before weld "
            "(weld normally removes them; inspect if > 0 after to_bmesh)")
    if not hair.strands:
        warnings.append("hair: 0 strands generated")

    timings["total_build"] = time.perf_counter() - t0
    return BuildResult(spec=spec, anatomy=anat, builder=body.builder, hair=hair,
                       eye_info=eye_info, stats=stats, digest=digest,
                       fingerprint=spec.fingerprint(), warnings=warnings,
                       timings=timings, numerics=numerics)


# ----------------------------------------------------------------------------- generate (bpy)
def _require_bpy():
    try:
        import bpy  # noqa: F401
    except ImportError as exc:  # pragma: no cover - environment dependent
        raise RuntimeError(
            "generate_character() needs the Blender runtime (bpy). "
            "Use build_character() for the geometry-only path, or run through "
            "tools/headless_blender.py."
        ) from exc


def generate_character(spec: CharacterSpec | str | None = None, *,
                       preset: str | None = None,
                       seed: int | None = None,
                       overrides: Mapping[str, Any] | None = None,
                       out_dir: str | None = None,
                       name: str | None = None,
                       weld: float = 1e-5,
                       subdivide: int | None = None,
                       write_blend: bool = True,
                       save_report: bool = True) -> GenerationResult:
    """Build a character and materialise it in the current Blender scene.

    ``out_dir`` (optional) receives ``<name>.blend`` (if ``write_blend``) and
    ``<name>.report.json`` (if ``save_report``).  Objects land in the
    ``HCG`` collection; their names are returned in ``result.objects``.
    """
    _require_bpy()
    import bmesh
    import bpy

    from ..core import object as obj
    from ..core.topology import audit
    from ..generators.hair import curves_to_object
    from .. import materials as mats

    t0 = time.perf_counter()
    build = build_character(spec, preset=preset, seed=seed, overrides=overrides)
    name = name or f"hcg_{build.spec.preset}_{build.fingerprint[:8]}"

    mat_map = mats.build_all(build.spec, build.anatomy)

    me = obj.mesh_from_builder(build.builder, f"hcg:{name}", weld=weld)
    for poly in me.polygons:
        poly.use_smooth = True

    body_ob = obj.create_object(name, me, "hcg")
    obj.assign_materials(body_ob, build.builder.materials)
    obj.store_spec_tag(body_ob, build.spec)

    levels = build.spec.pipeline.subdiv_render if subdivide is None else int(subdivide)
    if levels > 0:
        mod = body_ob.modifiers.new("hcg_subdiv", "SUBSURF")
        mod.levels = levels
        mod.render_levels = levels

    bm = bmesh.new()
    bm.from_mesh(me)
    topo = audit(bm)
    bm.free()

    hair_ob = curves_to_object(build.hair, f"hcg:hair:{name}", build.spec.hair.thickness)
    hair_mat = bpy.data.materials.get("hcg:hair")
    if hair_mat is not None:
        hair_ob.data.materials.append(hair_mat)
    obj.link_to(hair_ob, obj.get_collection("hcg"))

    warnings = list(build.warnings)
    if int(topo.get("non_manifold_edges", 0)) > 0:
        warnings.append(
            f"audit: {topo['non_manifold_edges']} non-manifold edges — known defect, "
            "root-caused in docs/RESEARCH_GATE_02.md (scheduled for S2)")
    if int(topo.get("degenerate_faces", 0)) > 0:
        warnings.append(f"audit: {topo['degenerate_faces']} degenerate faces after weld")

    files: dict[str, str] = {}
    result = GenerationResult(
        build=build,
        objects={"body": body_ob.name, "hair": hair_ob.name},
        materials=sorted(mat_map),
        audit=topo,
        files=files,
        elapsed=time.perf_counter() - t0,
    )
    result.build.warnings = warnings

    if out_dir:
        out_dir = os.path.abspath(out_dir)
        os.makedirs(out_dir, exist_ok=True)
        if write_blend:
            blend_path = os.path.join(out_dir, f"{name}.blend")
            bpy.ops.wm.save_as_mainfile(filepath=blend_path, compress=True)
            files["blend"] = blend_path
        if save_report:
            report_path = os.path.join(out_dir, f"{name}.report.json")
            with open(report_path, "w") as fh:
                json.dump(result.to_dict(), fh, indent=2, sort_keys=True)
            files["report"] = report_path
    return result


__all__ = [
    "CONTRACT_VERSION", "DEFAULT_PRESET", "BuildResult", "GenerationResult",
    "resolve_spec", "validate_overrides", "build_character", "generate_character",
]
