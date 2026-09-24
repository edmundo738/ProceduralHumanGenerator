# -*- coding: utf-8 -*-
"""Post-generation pipelines: subdivision, GN, rig, keys, quality, export, assembly.

S0 status: only :mod:`human_generator.pipeline.assemble` exists (public
character API, contract ``hcg-charapi/1.0.0``).  Rig / shape keys / export /
quality passes are still unimplemented — see docs/RESEARCH_COMPARATIVE_01.md
for the slice plan (S3–S5).
"""
from .assemble import (CONTRACT_VERSION, BuildResult, GenerationResult,
                       build_character, generate_character, resolve_spec,
                       validate_overrides)

__all__ = ["CONTRACT_VERSION", "BuildResult", "GenerationResult", "build_character",
           "generate_character", "resolve_spec", "validate_overrides"]
