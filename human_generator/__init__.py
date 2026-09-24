# -*- coding: utf-8 -*-
"""HCG — Human Character Generator.

A modular, deterministic, topology-aware procedural character system for
Blender 4.2 → 5.2 (validated headless against the ``bpy`` 5.0 wheel).

Quick start::

    import human_generator as hcg
    spec = hcg.CharacterSpec.from_preset("realistic_female", seed=1234)
    result = hcg.generate_character(spec, out_dir="out")

Everything (geometry, weights, materials, hair, GN graphs) is derived from
``seed`` — same seed in, same mesh hash out.
"""
from __future__ import annotations

from .spec import (BodyParams, CharacterSpec, FaceParams, HairParams,
                   PipelineParams, ExtrasParams, load_preset, list_presets)
from .pipeline.assemble import CONTRACT_VERSION as API_CONTRACT_VERSION

__version__ = "0.4.0"
__all__ = [
    "CharacterSpec", "BodyParams", "FaceParams", "HairParams",
    "PipelineParams", "ExtrasParams", "load_preset", "list_presets",
    "generate_character", "build_character", "API_CONTRACT_VERSION",
    "Anatomy", "__version__",
]


def generate_character(spec=None, **kwargs):
    """Build a character in the current Blender scene (contract v1.0.0).

    ``spec`` may be a :class:`CharacterSpec`, a preset name, or ``None``.
    Accepts ``seed``, ``preset``, ``overrides``, ``out_dir``, ``name``,
    ``weld``, ``subdivide``, ``write_blend``, ``save_report`` and returns a
    :class:`~human_generator.pipeline.assemble.GenerationResult`.
    Requires the Blender runtime; use :func:`build_character` for the
    geometry-only path.
    """
    from .pipeline.assemble import generate_character as _gc
    return _gc(spec, **kwargs)


def build_character(spec=None, **kwargs):
    """Geometry + hair only, pure Python, no ``bpy`` (contract v1.0.0)."""
    from .pipeline.assemble import build_character as _bc
    return _bc(spec, **kwargs)


def __getattr__(name):  # lazy: Anatomy pulls in mathutils shim etc.
    if name == "Anatomy":
        from .core.anatomy import Anatomy
        return Anatomy
    raise AttributeError(name)
