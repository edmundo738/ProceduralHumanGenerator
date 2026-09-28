# -*- coding: utf-8 -*-
"""TORSO STUDY 01 — painel render comparativo do TRONCO: nós vs refs.

Mesma câmara/luz/material para todas as fontes (método: render como instrumento).
Malhas: out/refstudy/raw_*.npz (normalização do estudo: 1700 mm, chão z=0).
Saídas: docs/head_phaseA/renders_T1_vs_refs.png, out/refstudy/torso_iou.json.

Uso: python tools/headless_blender.py run tools/refstudy/render_torso.py
"""
import json
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from _paths import WORK  # noqa: E402

import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402

ROOT = os.path.join(HERE, "..", "..")
DOCS = os.path.join(ROOT, "docs", "head_phaseA")
SOURCES = [("ours", False), ("femalebase", False), ("femalechar", True), ("bodytopo", True)]
VIEWS = [("front", 0.0, (0.0, 0.0, 1020.0), 1.06),
         ("q", 0.6, (0.0, 0.0, 1020.0), 1.06),
         ("side", 1.5708, (0.0, 0.0, 1020.0), 1.06),
         ("back", 3.1416, (0.0, 0.0, 1020.0), 1.06)]
RES = 520
IOU_BOX = {"front": (-235.0, 235.0, 560.0, 1250.0), "side": (-190.0, 230.0, 560.0, 1250.0)}
BT = json.load(open(os.path.join(WORK, "cfg_bodytopo.json")))
DROP = json.load(open(os.path.join(WORK, "drop_ours.json")))


def load_norm(name, flip):
    d = np.load(os.path.join(WORK, f"raw_{name}.npz"))
    V, T = d["V"].copy(), d["T"]
    lab = np.load(os.path.join(WORK, f"lab_{name}.npy"))
    if name == "bodytopo":
        S, fl = BT["stature_override"], BT["floor_override"]
    else:
        S, fl = V[:, 2].max() - V[:, 2].min(), V[:, 2].min()
    V[:, 2] -= fl
    V[:, 0] -= (V[:, 0].max() + V[:, 0].min()) / 2
    V *= 1700.0 / S
    if flip:
        V[:, 1] *= -1
    keep = ~np.isin(lab, DROP) if name == "ours" else np.ones(len(lab), bool)
    V[:, 1] -= (V[keep][:, 1].max() + V[keep][:, 1].min()) / 2
    return V * 0.001, T[keep[T[:, 0]]] if name == "ours" else T


def build_scene():
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    sc.cycles.samples = 24
    sc.cycles.use_denoising = True
    sc.render.resolution_x = RES
    sc.render.resolution_y = RES
    sc.world = bpy.data.worlds.new("w")
    sc.world.use_nodes = True
    sc.world.node_tree.nodes["Background"].inputs[0].default_value = (0.05, 0.05, 0.06, 1)
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob, do_unlink=True)
    cam_data = bpy.data.cameras.new("cam")
    cam_data.type = "ORTHO"
    cam = bpy.data.objects.new("cam", cam_data)
    sc.collection.objects.link(cam)
    sc.camera = cam
    for nm, energy, loc in (("key", 700, (2.0, 2.4, 3.0)), ("fill", 200, (-2.5, 1.0, 2.0))):
        li = bpy.data.lights.new(nm, "AREA")
        li.energy = energy
        li.size = 3.0
        ob = bpy.data.objects.new(nm, li)
        sc.collection.objects.link(ob)
        ob.visible_camera = False
        ob.location = loc
        ob.rotation_euler = (Vector((0, 0, 1.9)) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    return sc, cam, cam_data


def main():
    os.makedirs(DOCS, exist_ok=True)
    sc, cam, cam_data = build_scene()
    imgs, masks = {}, {}
    for name, flip in SOURCES:
        V, T = load_norm(name, flip)
        me = bpy.data.meshes.new(name)
        me.from_pydata([Vector(v) for v in V], [], [tuple(t) for t in T])
        me.validate()
        for p in me.polygons:
            p.use_smooth = True
        mat = bpy.data.materials.new("hcg_neutral")
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        bsdf.inputs["Base Color"].default_value = (0.55, 0.55, 0.55, 1.0)
        bsdf.inputs["Roughness"].default_value = 0.6
        me.materials.append(mat)
        ob = bpy.data.objects.new(name, me)
        sc.collection.objects.link(ob)
        for view, ang, tgt_mm, ortho in VIEWS:
            t = Vector(tgt_mm) * 0.001
            cam_data.ortho_scale = ortho
            cam.location = (t.x + 4.0 * math.sin(ang), t.y + 4.0 * math.cos(ang), t.z)
            cam.rotation_euler = (t - cam.location).to_track_quat("-Z", "Y").to_euler()
            path = os.path.join(WORK, f"_t1_{name}_{view}.png")
            sc.render.filepath = path
            bpy.ops.render.render(write_still=True)
            imgs[(name, view)] = path
            if view in IOU_BOX:
                from PIL import Image
                im = np.asarray(Image.open(path).convert("L"), float) / 255.0
                m = im > 0.25
                px = RES / ortho
                lo, hi, zlo, zhi = IOU_BOX[view]
                c0 = int(RES / 2 + (lo / 1000.0) * px)
                c1 = int(RES / 2 + (hi / 1000.0) * px)
                r0 = int(RES / 2 - ((zhi - 1020.0) / 1000.0) * px)
                r1 = int(RES / 2 - ((zlo - 1020.0) / 1000.0) * px)
                masks[(name, view)] = m[max(0, r0):min(RES, r1), max(0, c0):min(RES, c1)]
        bpy.data.objects.remove(ob, do_unlink=True)
        bpy.data.meshes.remove(me)
    out = {}
    for view in IOU_BOX:
        refs = [n for n, _ in SOURCES[1:]]
        d = {"ours": {r: float((masks[("ours", view)] & masks[(r, view)]).sum() /
                              max((masks[("ours", view)] | masks[(r, view)]).sum(), 1)) for r in refs}}
        rr = [float((masks[(a, view)] & masks[(b, view)]).sum() /
                    max((masks[(a, view)] | masks[(b, view)]).sum(), 1))
              for i, a in enumerate(refs) for b in refs[i + 1:]]
        d["ref_ref_baseline"] = float(np.mean(rr))
        out[view] = d
    json.dump(out, open(os.path.join(WORK, "torso_iou.json"), "w"), indent=1)
    print(json.dumps(out, indent=1))
    from PIL import Image, ImageDraw
    cols = [v for v, *_ in VIEWS]
    CW, CH, LH = 470, 500, 34
    panel = Image.new("RGB", (CW * len(cols), (CH + LH) * len(SOURCES) + LH), (12, 12, 16))
    dr = ImageDraw.Draw(panel)
    for c, v in enumerate(cols):
        dr.text((c * CW + 12, 8), v, fill=(240, 240, 240))
    for r, (n, _) in enumerate(SOURCES):
        y0 = LH + r * (CH + LH)
        dr.text((12, y0 + 8), n, fill=(240, 240, 240))
        for c, v in enumerate(cols):
            im = Image.open(imgs[(n, v)]).convert("RGB").resize((CW - 12, CH - 8))
            panel.paste(im, (c * CW + 6, y0 + LH))
    panel.save(os.path.join(DOCS, "renders_T1_vs_refs.png"))
    print("painel →", os.path.join(DOCS, "renders_T1_vs_refs.png"))


if __name__ == "__main__":
    main()
