#!/usr/bin/env python3
"""Dev smoke: merge body+head into a mesh, audit, clay render two views."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import bpy  # noqa
import bmesh  # noqa
import math, time
from human_generator.spec import CharacterSpec
from human_generator.core.anatomy import Anatomy
from human_generator.generators.body import build_body
from human_generator.generators.head import build_head
from human_generator.generators.eyes import build_eyes
from human_generator.generators.mouth import build_mouth
from human_generator.core import object as obj
from human_generator.core.topology import audit

t0 = time.time()
seed = int(sys.argv[1]) if len(sys.argv) > 1 else 42
spec = CharacterSpec.from_preset("realistic_female", seed=seed)
anat = Anatomy.from_spec(spec)
body = build_body(spec, anat)
head = build_head(spec, anat)
build_eyes(spec, anat, head.builder)
build_mouth(head.builder, spec, anat)
body.builder.merge(head.builder, group_prefix="head.")
print("merged stats:", {k: body.builder.stats()[k] for k in ("verts", "faces", "quad_ratio", "degenerate")})

from human_generator import materials as mats
mats.build_all(spec, anat)
me = obj.mesh_from_builder(body.builder, "hcg:preview")
bm = bmesh.new(); bm.from_mesh(me)
a = audit(bm); bm.free()
print("audit:", a)

sc = bpy.context.scene
ob = bpy.data.objects.new("body", me)
sc.collection.objects.link(ob)

for p in me.polygons: p.use_smooth = True
for raw in body.builder.materials:
    nm = obj.material_slot_name(raw)
    m = bpy.data.materials.get(nm) or bpy.data.materials.new(nm)
    me.materials.append(m)

# subdivision for preview
mod = ob.modifiers.new("ss", "SUBSURF"); mod.levels = 2; mod.render_levels = 2

# camera: front (+Y in canonical) and 3/4
def render(name, loc, lens=85, res=(640, 800)):
    cam_d = bpy.data.cameras.new(name); cam_d.lens = lens
    cam = bpy.data.objects.new(name, cam_d)
    sc.collection.objects.link(cam)
    cam.location = loc
    import mathutils
    target = mathutils.Vector((0, 0.02, 1.45 if name == "face" else 0.95))
    d = target - cam.location
    cam.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    sc.camera = cam
    sc.render.engine = "CYCLES"; sc.cycles.device = "CPU"; sc.cycles.samples = 16
    sc.render.resolution_x, sc.render.resolution_y = res
    w = bpy.data.worlds.new(name); sc.world = w
    w.use_nodes = True
    bg = w.node_tree.nodes.get("Background")
    bg.inputs[0].default_value = (0.9, 0.9, 0.95, 1); bg.inputs[1].default_value = 1.0
    # rim
    la = bpy.data.lights.new(name, "AREA"); la.energy = 220; la.size = 0.8
    lo = bpy.data.objects.new(name, la); sc.collection.objects.link(lo)
    lo.location = (loc[0] + 0.9, loc[1] + 0.6, 1.9); lo.rotation_euler = (0.9, 0, 0.9)
    sc.render.filepath = f"/home/user/ProceduralHumanGenerator/out/{name}.png"
    bpy.ops.render.render(write_still=True)
    print("saved", name)

render("face", (0.0, 0.72, 1.52), 85, (480, 600))
render("full", (1.55, 1.85, 1.25), 60, (480, 640))
print(f"total {time.time()-t0:.1f}s")
