#!/usr/bin/env python3
"""Dev smoke: build through the **public API**, audit, render two Cycles views.

Usage::

    python tools/headless_blender.py run tools/dev_smoke.py [seed] [preset]

Since S0 this script no longer orchestrates the generators itself — it calls
``human_generator.pipeline.assemble.build_character`` so that the smoke test and
the API can never drift apart (the duplication was how the API stayed broken
undetected).  Acceptance checks for the same path live in
``tests/test_s0_public_api.py``.
"""
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import bpy  # noqa: F401  — must precede bmesh
import bmesh  # noqa: F401
import mathutils

from human_generator.core import object as obj
from human_generator.core.topology import audit
from human_generator import materials as mats
from human_generator.generators.hair import curves_to_object
from human_generator.pipeline.assemble import CONTRACT_VERSION, build_character

t0 = time.time()
seed = int(sys.argv[1]) if len(sys.argv) > 1 else 42
preset = sys.argv[2] if len(sys.argv) > 2 else "realistic_female"

build = build_character(preset, seed=seed)
spec, anat = build.spec, build.anatomy
print(f"api contract {CONTRACT_VERSION} | build:", {k: build.stats[k] for k in
      ("verts", "faces", "quad_ratio", "degenerate")}, "| digest", build.digest,
      "| hair strands", len(build.hair.strands))

mats.build_all(spec, anat)
me = obj.mesh_from_builder(build.builder, "hcg:preview")
bm = bmesh.new()
bm.from_mesh(me)
a = audit(bm)
bm.free()
print("audit:", a)

sc = bpy.context.scene
ob = bpy.data.objects.new("body", me)
sc.collection.objects.link(ob)

for p in me.polygons:
    p.use_smooth = True
obj.assign_materials(ob, build.builder.materials)

# subdivision for preview
mod = ob.modifiers.new("ss", "SUBSURF")
mod.levels = 2
mod.render_levels = 2


def render(name, loc, lens=85, res=(640, 800)):
    cam_d = bpy.data.cameras.new(name)
    cam_d.lens = lens
    cam = bpy.data.objects.new(name, cam_d)
    sc.collection.objects.link(cam)
    cam.location = loc
    target = mathutils.Vector((0, 0.02, 1.45 if name == "face" else 0.95))
    d = target - cam.location
    cam.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    sc.camera = cam
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    sc.cycles.samples = 16
    sc.render.resolution_x, sc.render.resolution_y = res
    w = bpy.data.worlds.new(name)
    sc.world = w
    w.use_nodes = True
    bg = w.node_tree.nodes.get("Background")
    bg.inputs[0].default_value = (0.9, 0.9, 0.95, 1)
    bg.inputs[1].default_value = 1.0
    la = bpy.data.lights.new(name, "AREA")
    la.energy = 220
    la.size = 0.8
    lo = bpy.data.objects.new(name, la)
    sc.collection.objects.link(lo)
    lo.location = (loc[0] + 0.9, loc[1] + 0.6, 1.9)
    lo.rotation_euler = (0.9, 0, 0.9)
    sc.render.filepath = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "out", f"{name}.png")
    bpy.ops.render.render(write_still=True)
    print("saved", name)


hair_obj = curves_to_object(build.hair, "hcg:hair", spec.hair.thickness)
hm = bpy.data.materials.get("hcg:hair")
if hm:
    hair_obj.data.materials.append(hm)
sc.collection.objects.link(hair_obj)
render("face", (0.0, 0.72, 1.52), 85, (480, 600))
render("full", (1.55, 1.85, 1.25), 60, (480, 640))
print(f"total {time.time() - t0:.1f}s")
