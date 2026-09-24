# -*- coding: utf-8 -*-
"""Blender-object plumbing shared by every generator.

All data access goes through ``bpy.data`` + bmesh (never edit-mode operators),
so generation is context-free and runs identically headless and interactively.
"""
from __future__ import annotations

from typing import Iterable, Sequence

import bpy

from ._math import Vector, Matrix

ROOT_COLLECTION = "HCG"


# ----------------------------------------------------------------------------- collections
def get_collection(name_path: str) -> "bpy.types.Collection":
    """Ensure ``scene.collection → ROOT_COLLECTION → ... → leaf`` exists."""
    parts = [p for p in name_path.split("/") if p]
    root = bpy.data.collections.get(ROOT_COLLECTION)
    if root is None:
        root = bpy.data.collections.new(ROOT_COLLECTION)
        bpy.context.scene.collection.children.link(root)
    cur = root
    for part in parts:
        nxt = cur.children.get(part)
        if nxt is None:
            nxt = bpy.data.collections.new(part)
            cur.children.link(nxt)
        cur = nxt
    return cur


def purge(prefix: str = "hcg:") -> None:
    """Delete all data blocks whose name starts with ``prefix`` (idempotent reruns)."""
    blocks = (bpy.data.meshes, bpy.data.curves, bpy.data.materials, bpy.data.node_groups,
              bpy.data.armatures, bpy.data.lights, bpy.data.cameras, bpy.data.objects,
              bpy.data.collections, bpy.data.worlds)
    for coll in blocks:
        for b in [x for x in coll if x.name.startswith(prefix)]:
            try:
                coll.remove(b)
            except ReferenceError:
                pass


def link_to(obj: "bpy.types.Object", coll: "bpy.types.Collection") -> None:
    for c in obj.users_collection:
        c.objects.unlink(obj)
    coll.objects.link(obj)


# ----------------------------------------------------------------------------- mesh
def mesh_from_builder(builder, name: str | None = None, *, weld: float = 1e-5) -> bpy.types.Mesh:
    """bmesh → Mesh with UVs, region + crease attributes (from the builder)."""
    bm = builder.to_bmesh(weld=weld)
    me = bpy.data.meshes.new(name or f"hcg:{builder.name}")
    bm.to_mesh(me)
    bm.free()
    me.update()
    return me


def create_object(name: str, me, collection_path: str,
                  *, parent: "bpy.types.Object | None" = None) -> bpy.types.Object:
    ob = bpy.data.objects.new(name, me)
    coll = get_collection(collection_path)
    link_to(ob, coll)
    if parent is not None:
        ob.parent = parent
        ob.matrix_parent_inverse = parent.matrix_world.inverted()
    return ob


def add_vertex_groups(ob: bpy.types.Object, groups: dict[str, dict[int, float]],
                     *, overwrite: bool = False) -> None:
    for gname, weights in groups.items():
        vg = ob.vertex_groups.get(gname)
        if vg is None:
            vg = ob.vertex_groups.new(name=gname)
        elif not overwrite:
            pass
        # batch by quantised weight: vg.add takes one weight per call
        buckets: dict[int, list[int]] = {}
        for vi, w in weights.items():
            buckets.setdefault(int(round(w * 255)), []).append(vi)
        for q, idxs in buckets.items():
            vg.add(idxs, q / 255.0, "REPLACE")


def region_vertex_groups(ob: bpy.types.Object, *, min_verts: int = 3) -> list[str]:
    """Promote the ``hcg_region`` point attribute to vertex groups.

    The skin shader reads these groups as anatomical masks (lips, scalp,
    palms…) — a data channel that survives export better than colours.
    """
    from .topology import REGION_NAMES
    me = ob.data
    attr = me.attributes.get("hcg_region")
    if attr is None:
        return []
    values = [d.value for d in attr.data]
    by_code: dict[float, list[int]] = {}
    for i, v in enumerate(values):
        by_code.setdefault(round(v, 6), []).append(i)
    made = []
    for code, idxs in by_code.items():
        name = REGION_NAMES.get(code)
        if not name or name == "skin" or len(idxs) < min_verts:
            continue
        vg = ob.vertex_groups.get(name) or ob.vertex_groups.new(name=name)
        vg.add(idxs, 1.0, "REPLACE")
        made.append(name)
    return made


def write_refine_attribute(ob: bpy.types.Object, values: Sequence[float]) -> None:
    me = ob.data
    attr = me.attributes.get("hcg_refine")
    if attr is None:
        attr = me.attributes.new("hcg_refine", "FLOAT", "POINT")
    for i, v in enumerate(values):
        attr.data[i].value = float(v)


def store_spec_tag(ob: bpy.types.Object, spec) -> None:
    ob["hcg_seed"] = int(spec.seed)
    ob["hcg_spec"] = spec.fingerprint()


# ----------------------------------------------------------------------------- materials
def material_slot_name(raw_name: str | None) -> str:
    """Map builder material names to hcg material block names."""
    from ..materials import MATERIAL_MAP
    if not raw_name:
        return "hcg:skin"
    key = MATERIAL_MAP.get(raw_name, "skin")
    return f"hcg:{key}"


def assign_materials(ob: bpy.types.Object, names: Sequence[str | None], *,
                     fallback: str = "hcg:skin") -> None:
    """Bind slot list (in builder slot order) to real materials.

    Slots are ordered to match ``builder.materials`` so existing
    ``material_index`` values on faces stay correct.
    """
    ob.data.materials.clear()
    for raw in names:
        mat_name = material_slot_name(raw)
        mat = bpy.data.materials.get(mat_name)
        if mat is None:
            mat = bpy.data.materials.get(fallback)
        if mat is None:
            mat = bpy.data.materials.new(mat_name)
            mat.use_nodes = True
        ob.data.materials.append(mat)
    # face indices were assigned from builder.materials order; ensure slot count
    n = len(getattr(ob.data, "materials", []))
    if n == 0:
        mat = bpy.data.materials.get(fallback)
        if mat:
            ob.data.materials.append(mat)


# ----------------------------------------------------------------------------- misc
def bake_transform(objs: Iterable["bpy.types.Object"], matrix: Matrix) -> None:
    for ob in objs:
        if isinstance(ob.data, bpy.types.Mesh):
            ob.data.transform(matrix)
        elif isinstance(ob.data, bpy.types.Curve):
            for sp in ob.data.splines:
                for pt in sp.points:
                    p = matrix @ Vector((pt.co.x, pt.co.y, pt.co.z))
                    pt.co = (p.x, p.y, p.z, 1.0)
        ob.matrix_world = matrix @ ob.matrix_world
        ob.matrix_basis = ob.matrix_world.copy()


def set_shading(objs: Iterable["bpy.types.Object"], *, smooth: bool = True,
                auto_angle_deg: float | None = 35.0) -> None:
    for ob in objs:
        if not isinstance(ob.data, bpy.types.Mesh):
            continue
        for p in ob.data.polygons:
            p.use_smooth = smooth
        if smooth and auto_angle_deg is not None:
            done = False
            try:
                bpy.context.view_layer.objects.active = ob
                for op in ("object.shade_auto_smooth", "object.shade_smooth_by_angle"):
                    fn = getattr(bpy.ops.object, op, None)
                    if fn is None:
                        continue
                    try:
                        fn(angle=math.radians(auto_angle_deg))
                        done = True
                        break
                    except (RuntimeError, TypeError, AttributeError):
                        continue
            except Exception:
                done = False
            if not done:
                # fallback: keep plain smooth (subsurf removes most artifacts)
                pass


import math  # noqa: E402  (used in set_shading)
