# -*- coding: utf-8 -*-
"""Shared pytest fixtures (S1).

The suite is deliberately **pure Python**: ``bpy`` is only importable with the
headless stubs in place, so anything that needs Blender lives in
``tests/test_s0_public_api.py`` and runs through
``python tools/headless_blender.py run tests/test_s0_public_api.py -- --bpy``.
"""
from __future__ import annotations

import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


@pytest.fixture(scope="session")
def repo_root() -> str:
    return ROOT


@pytest.fixture(scope="session")
def preset_names():
    import human_generator as hcg
    names = hcg.list_presets()
    assert names, "no presets found"
    return names


@pytest.fixture(scope="module")
def build_default():
    """One build of the pinned spec, reused across a module (≈1 s)."""
    import human_generator as hcg
    return hcg.build_character("realistic_female", seed=42)


@pytest.fixture(scope="module")
def head_builder():
    """Head + eyes + mouth builder (the complex one: 3 119 verts)."""
    from human_generator.core.anatomy import Anatomy
    from human_generator.generators.eyes import build_eyes
    from human_generator.generators.head import build_head
    from human_generator.generators.mouth import build_mouth
    from human_generator.spec import CharacterSpec

    spec = CharacterSpec.from_preset("realistic_female", seed=42)
    anat = Anatomy.from_spec(spec)
    head = build_head(spec, anat)
    build_eyes(spec, anat, head.builder)
    build_mouth(head.builder, spec, anat)
    return head.builder
