# -*- coding: utf-8 -*-
"""CONT1 — close-up NEUTRO da orelha (Cycles, cinza, sem cabelo), mesma câmara
para quaisquer variantes (env HCG_HEAD/HCG_NECK).  Uso:
  HCG_HEAD=faceB2 HCG_NECK=N1 python tools/headless_blender.py run \
      tools/headface/render_ear.py -- OUT_DIR
"""
import math, os, sys
sys.path.insert(0, ".")
import bpy
from mathutils import Vector
import human_generator as hcg
from human_generator.generators import head_mass as HM

_a = [a for a in sys.argv[1:] if not a.startswith("--")]
out = _a[0] if _a else "out/render/ear"
os.makedirs(out, exist_ok=True)
spec = hcg.CharacterSpec.from_preset("realistic_female", seed=42)
res = hcg.generate_character("realistic_female", seed=42, name="ear_view",
                             write_blend=False, save_report=False)
body = bpy.data.objects[res.objects["body"]]
bpy.data.objects[res.objects["hair"]].hide_render = True
for ob in list(bpy.data.objects):
    if ob.name != res.objects["body"]:
        bpy.data.objects.remove(ob, do_unlink=True)
mat = bpy.data.materials.new("hcg_neutral"); mat.use_nodes = True
bsdf = mat.node_tree.nodes.get("Principled BSDF")
bsdf.inputs["Base Color"].default_value = (0.55, 0.55, 0.55, 1.0)
bsdf.inputs["Roughness"].default_value = 0.6
body.data.materials.clear(); body.data.materials.append(mat)

sc = bpy.context.scene
sc.render.engine = "CYCLES"; sc.cycles.device = "CPU"; sc.cycles.samples = 24
sc.cycles.use_denoising = True
sc.render.resolution_x = 620; sc.render.resolution_y = 620
sc.world = bpy.data.worlds.new("w"); sc.world.use_nodes = True
sc.world.node_tree.nodes["Background"].inputs[0].default_value = (0.05, 0.05, 0.06, 1)
anat = res.build.anatomy
h = anat.h; s = h / HM.H_NORM
target = Vector((88.0 * s, HM.Y0_FRAC * h + (-25.0) * s, anat.z("chin") + 92.0 * s))
cam_data = bpy.data.cameras.new("cam"); cam_data.type = "ORTHO"; cam_data.ortho_scale = 0.125
cam = bpy.data.objects.new("cam", cam_data); sc.collection.objects.link(cam); sc.camera = cam
for name, energy, loc in (("key", 700, (2.0, 1.2, 2.6)), ("fill", 200, (-2.5, 0.5, 1.8))):
    li = bpy.data.lights.new(name, "AREA"); li.energy = energy; li.size = 2.5
    ob = bpy.data.objects.new(name, li); sc.collection.objects.link(ob)
    ob.visible_camera = False; ob.location = loc
    ob.rotation_euler = (Vector((0, 0, target.z)) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
for tag, ang in (("side", math.radians(90)), ("qback", math.radians(128))):
    cam.location = (target.x + 4.0 * math.sin(ang), target.y + 4.0 * math.cos(ang), target.z)
    cam.rotation_euler = (target - cam.location).to_track_quat("-Z", "Y").to_euler()
    sc.render.filepath = os.path.join(out, f"{tag}.png")
    bpy.ops.render.render(write_still=True)
    print("rendered", sc.render.filepath)
