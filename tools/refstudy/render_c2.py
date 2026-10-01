# -*- coding: utf-8 -*-
"""Renders do protótipo C2 (mama estruturada) — docs/BREAST_C2_01.md.

Painel: refs + N0 (parede) + V0 (H-TT1 gauss) + B2 (C2) × vistas
front/side/q, em duas folhas: zoom 660 mm sobre o busto e corpo-torso
(ortho 1.06).  Grelha A–H × 1–8 (modo B) para o dono apontar células.

Uso: python3 tools/headless_blender.py run tools/refstudy/render_c2.py
Saídas: docs/head_phaseA/breast_c2_zoom.png, breast_c2_torso.png
"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from _paths import WORK  # noqa: E402

import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402

from render_torso import build_scene  # noqa: E402
from sweep_breast import load_tile, overlay_grid  # noqa: E402

ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
DOCS = os.path.join(ROOT, "docs", "head_phaseA")
RES = 520
TILE = 470

SOURCES = [  # (rótulo, nome, flip)
    ("R·real005", "real005", True),
    ("R·femalebase", "femalebase", False),
    ("R·femalechar", "femalechar", True),
    ("N0·parede", "swN0", False),
    ("V0·H-TT1", "swV0", False),
    ("B2·C2", "swB2", False),
]
SHEETS = [("zoom", 0.66, 1255.0), ("torso", 1.06, 1020.0)]
VIEWS = [("front", 0.0), ("q", 0.6), ("side", 1.5708)]


def render_view(sc, cam, cam_data, key, V, T, ang, ortho, z_mm, tag):
    me = bpy.data.meshes.new(key)
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
    ob = bpy.data.objects.new(key, me)
    sc.collection.objects.link(ob)
    t = Vector((0.0, 0.0, z_mm * 0.001))
    cam_data.ortho_scale = ortho
    cam.location = (t.x + 4.0 * math.sin(ang), t.y + 4.0 * math.cos(ang), t.z)
    cam.rotation_euler = (t - cam.location).to_track_quat("-Z", "Y").to_euler()
    path = os.path.join(WORK, f"_c2_{key}_{tag}.png")
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
    bpy.data.objects.remove(ob, do_unlink=True)
    bpy.data.meshes.remove(me)
    return path


def main():
    os.makedirs(DOCS, exist_ok=True)
    sc, cam, cam_data = build_scene()
    for sheet, ortho, z_mm in SHEETS:
        imgs = {}
        for lbl, name, flip in SOURCES:
            drop = None
            dj = os.path.join(WORK, f"drop_{name}.json")
            if os.path.exists(dj):
                drop = json.load(open(dj))["drop_labels"]
            V, T = load_tile(name, flip, drop)
            for view, ang in VIEWS:
                imgs[(lbl, view)] = render_view(
                    sc, cam, cam_data, f"{name}_{view}", V, T, ang, ortho, z_mm, sheet)
            print(f"RENDER {sheet} {lbl} ok")

        from PIL import Image, ImageDraw
        cols, rows = len(VIEWS), len(SOURCES)
        CW, CH, LH = TILE + 12, TILE + 6, 40
        W, H = CW * cols + 8, (CH + LH) * rows + 34
        im_out = Image.new("RGB", (W, H), (12, 12, 16))
        dr = ImageDraw.Draw(im_out)
        dr.text((12, 8),
                f"BREAST C2 — {sheet} · B2=protótipo estruturado (HCG_BREAST2) · "
                f"responde p.ex. 'B2 > V0' ou aponta células ('B2 perfil C4')",
                fill=(240, 240, 240))
        for r, (lbl, name, _) in enumerate(SOURCES):
            for c, (view, _) in enumerate(VIEWS):
                x0 = 8 + c * CW
                y0 = 30 + r * (CH + LH)
                if c == 0:
                    dr.text((x0 + 4, y0 + 2), lbl, fill=(240, 240, 240))
                t = Image.open(imgs[(lbl, view)]).convert("RGB").resize((TILE, TILE))
                t = overlay_grid(t).convert("RGB")
                im_out.paste(t, (x0 + 6, y0 + LH - 18))
        out = os.path.join(DOCS, f"breast_c2_{sheet}.png")
        im_out.save(out)
        print("folha →", out)


if __name__ == "__main__":
    main()
