# -*- coding: utf-8 -*-
"""CONT1/POST-AUDIT — render COMPARATIVO: nós vs refs, câmara/luz/material idênticos.

O render é instrumento de avaliação (docs/METHOD.md): para cada fonte carregamos
a malha NORMALIZADA do estudo (mm@H226 — mesmo referencial para todos, refs
incluídas) e renderizamos em Cycles cinza neutro, sem cabelo, com a MESMA câmara
e luzes.  Saídas:

  docs/head_phaseA/renders_F2_vs_refs.png  — painel fontes × vistas
  out/face/cont1/render_cmp.npz             — silhuetas (máscaras)
  out/face/cont1/render_iou.json            — IoU de silhueta (proxy medido)

IoU de silhueta (frontal/lado): interseção/união das máscaras recortadas à caixa
da cabeça (mesma caixa em mm para todos).  É um PROXY de forma — não substitui
a leitura visual; serve de número rastreável e de regressão entre versões.
Baseline dado pelos pares ref↔ref (a própria variabilidade entre refs).

Uso:
  python tools/headless_blender.py run tools/headface/render_cmp.py
"""
import json
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..", "..")
sys.path.insert(0, os.path.join(ROOT, "tools", "headstudy"))
os.environ["HCG_KEEP_EYES"] = "1"          # a nossa cabeça mostra os globos
import common as C  # noqa: E402

import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402

SOURCES = ["oursF1", "oursF2", "bodytopo", "femalebase", "femalechar"]
VIEWS = [("front", 0.0, (0.0, 0.0, 112.0), 0.27),
         ("q", 0.7, (0.0, 0.0, 112.0), 0.27),
         ("side", 1.5708, (0.0, 0.0, 112.0), 0.27),
         ("back", 3.1416, (0.0, 0.0, 112.0), 0.27),
         ("ear", 1.5708, (85.0, -25.0, 92.0), 0.14),
         ("earq", 2.23, (85.0, -25.0, 92.0), 0.14)]
RES = 520
IOU_BOX = {"front": (-105.0, 105.0, -15.0, 235.0),   # (xmin,xmax,zmin,zmax) mm
           "side": (-120.0, 130.0, -15.0, 235.0)}     # (ymin,ymax,zmin,zmax)
OUTD = os.path.join(ROOT, "out", "face", "cont1")
DOCS = os.path.join(ROOT, "docs", "head_phaseA")


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
    for name, energy, loc in (("key", 700, (2.0, 2.4, 2.8)), ("fill", 200, (-2.5, 1.0, 1.6))):
        li = bpy.data.lights.new(name, "AREA")
        li.energy = energy
        li.size = 2.5
        ob = bpy.data.objects.new(name, li)
        sc.collection.objects.link(ob)
        ob.visible_camera = False
        ob.location = loc
        ob.rotation_euler = (Vector((0, 0, 1.7)) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    return sc, cam, cam_data


def add_mesh(name):
    Vn, T, fs, fi, info = C.normalise(name)
    V = np.asarray(Vn, float) * 0.001
    T = np.asarray(T, int)
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
    bpy.context.scene.collection.objects.link(ob)
    return ob, me


def render_view(sc, cam, cam_data, tag, ang, target_mm, ortho):
    t = Vector(target_mm) * 0.001
    cam_data.ortho_scale = ortho
    cam.location = (t.x + 4.0 * math.sin(ang), t.y + 4.0 * math.cos(ang), t.z)
    cam.rotation_euler = (t - cam.location).to_track_quat("-Z", "Y").to_euler()
    path = os.path.join(OUTD, f"_tmp_{tag}.png")
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
    return path


def mask_of(path, view, target_mm, ortho):
    from PIL import Image
    im = np.asarray(Image.open(path).convert("L"), float) / 255.0
    m = im > 0.25
    px_per_m = RES / ortho
    tx, _, tz = target_mm
    lo, hi, zlo, zhi = IOU_BOX[view]
    c0 = int(round(RES / 2 + (lo / 1000.0 - 0) * px_per_m))
    c1 = int(round(RES / 2 + (hi / 1000.0) * px_per_m))
    r0 = int(round(RES / 2 - (zhi / 1000.0) * px_per_m))
    r1 = int(round(RES / 2 - (zlo / 1000.0) * px_per_m))
    return m[max(0, r0):min(RES, r1), max(0, c0):min(RES, c1)]


def main():
    os.makedirs(OUTD, exist_ok=True)
    os.makedirs(DOCS, exist_ok=True)
    sc, cam, cam_data = build_scene()
    imgs, masks = {}, {}
    for name in SOURCES:
        ob, me = add_mesh(name)
        for view, ang, tgt, ortho in VIEWS:
            p = render_view(sc, cam, cam_data, f"{name}_{view}", ang, tgt, ortho)
            imgs[(name, view)] = p
            if view in IOU_BOX:
                masks[(name, view)] = mask_of(p, view, tgt, ortho)
        bpy.data.objects.remove(ob, do_unlink=True)
        bpy.data.meshes.remove(me)
    # ---- IoU (frontal/lado), com baseline ref↔ref
    out = {}
    for view in IOU_BOX:
        d = {}
        ours = {n: masks[(n, view)] for n in ("oursF1", "oursF2")}
        refs = {n: masks[(n, view)] for n in SOURCES[2:]}
        for n, m in ours.items():
            d[n] = {r: float((m & q).sum() / max((m | q).sum(), 1)) for r, q in refs.items()}
        rr = [float((a & b).sum() / max((a | b).sum(), 1))
              for i, a in enumerate(list(refs.values())) for b in list(refs.values())[i + 1:]]
        d["ref_ref_baseline"] = float(np.mean(rr))
        out[view] = d
    json.dump(out, open(os.path.join(OUTD, "render_iou.json"), "w"), indent=1)
    print(json.dumps(out, indent=1))
    np.savez_compressed(os.path.join(OUTD, "render_cmp.npz"),
                        **{f"{n}_{v}": m for (n, v), m in masks.items()})
    # ---- painel
    from PIL import Image, ImageDraw
    cols = [v for v, *_ in VIEWS]
    rows = SOURCES
    CW, CH, LH = 430, 460, 34
    panel = Image.new("RGB", (CW * len(cols), (CH + LH) * len(rows) + LH), (12, 12, 16))
    dr = ImageDraw.Draw(panel)
    for c, v in enumerate(cols):
        dr.text((c * CW + 12, 8), v, fill=(240, 240, 240))
    for r, n in enumerate(rows):
        y0 = LH + r * (CH + LH)
        dr.text((12, y0 + 8), n, fill=(240, 240, 240))
        for c, v in enumerate(cols):
            im = Image.open(imgs[(n, v)]).convert("RGB").resize((CW - 12, CH - 8))
            panel.paste(im, (c * CW + 6, y0 + LH))
    panel.save(os.path.join(DOCS, "renders_F2_vs_refs.png"))
    print("painel →", os.path.join(DOCS, "renders_F2_vs_refs.png"))


if __name__ == "__main__":
    main()
