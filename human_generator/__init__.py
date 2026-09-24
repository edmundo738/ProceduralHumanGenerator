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

__version__ = "0.4.0"
__all__ = [
    "CharacterSpec", "BodyParams", "FaceParams", "HairParams",
    "PipelineParams", "ExtrasParams", "load_preset", "list_presets",
    "generate_character", "Anatomy", "__version__",
]


def generate_character(spec=None, **kwargs):
    """Build a character. ``spec`` may be a CharacterSpec or kwargs for one."""
    from .pipeline.assemble import generate_character as _gc
    if spec is None:
        spec = CharacterSpec.from_preset(**kwargs)
    elif isinstance(spec, str):
        spec = CharacterSpec.from_preset(spec, **kwargs)
    elif kwargs:
        spec = spec.merged(kwargs)
    return _gc(spec)


def __getattr__(name):  # lazy: Anatomy pulls in mathutils shim etc.
    if name == "Anatomy":
        from .core.anatomy import Anatomy
        return Anatomy
    raise AttributeError(name)
