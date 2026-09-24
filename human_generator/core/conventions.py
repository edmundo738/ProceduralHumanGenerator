# -*- coding: utf-8 -*-
"""Convention handling between the authoring frame and Blender.

Canonical authoring frame (used by every generator, tests and JSON reports):

    +Z up · +Y **forward** (face) · +X character's left · metres

Blender assets conventionally face ``-Y``.  We bridge the two with a pure
180° rotation on a root empty — **no mirroring**, so hand/foot chirality and
asymmetric marks stay correct, and every generator can keep thinking in the
readable canonical frame.

The optional ``flip_builder`` (mirror + winding fix) is provided for users who
want the baked alternative; it is not used by the default pipeline.
"""
from __future__ import annotations

import math

from ._math import Matrix, Vector

ROOT_EMPTY = "hcg:root"
ROT_Z_PI = math.pi


def ensure_root() -> "object":
    """Create/return the facing empty that bakes −Y into the asset."""
    import bpy
    from .object import get_collection, link_to
    root = bpy.data.objects.get(ROOT_EMPTY)
    if root is None:
        root = bpy.data.objects.new(ROOT_EMPTY, None)
        link_to(root, get_collection(""))
    root.empty_display_type = "PLAIN_AXES"
    root.empty_display_size = 0.25
    root.rotation_euler = (0.0, 0.0, ROT_Z_PI)
    return root


def parent_to_root(obj, root) -> None:
    obj.parent = root
    obj.matrix_parent_inverse = root.matrix_world.inverted()


def parent_many(root, objs) -> None:
    for ob in objs:
        parent_to_root(ob, root)


def to_blender_front(builder) -> None:
    """(Optional) mirror a builder so its data already faces −Y in-place.

    Mirrors Y, reverses winding so normals stay outward, and flips UV ``u``.
    Use only when the root-empty rotation is not wanted (exports a flat mesh).
    """
    flip = Matrix(((1.0, 0.0, 0.0, 0.0),
                   (0.0, -1.0, 0.0, 0.0),
                   (0.0, 0.0, 1.0, 0.0),
                   (0.0, 0.0, 0.0, 1.0)))
    builder.transform(flip)
