# -*- coding: utf-8 -*-
"""SWEEP 01 — MAMA · modo A (busca guiada pelo dono; docs/SWEEP_01_BREAST.md).

O agente é cego (limite declarado): este instrumento converte a escolha VISUAL
do dono em dados.  Gera N variantes DA MESMA REGIÃO (só muda a mama; resto do
corpo idêntico ao H-TT1), renderiza vistas padronizadas com grelha etiquetada
(modo B: células A–H × 1–8 para apontar) e monta folhas de contacto por vista.

O dono responde p.ex.: "V2 > V6 > V0; V5 rejeitada; no V3 a célula C4 do perfil
é dura"  →  o agente MEDE o que distingue escolhidas de rejeitadas e promove o
vencedor a default calibrado (nunca flag de spec).

Uso: python3 tools/headless_blender.py run tools/refstudy/sweep_breast.py
Saídas: docs/head_phaseA/sweep_breast_{front,q,side}.png
        out/refstudy/sweep_breast.json (parâmetros + coberturas de máscara)
"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from _paths import WORK  # noqa: E402

import numpy as np  # noqa: E402
import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402

from torso_refs import _eval, _save  # noqa: E402  (mesma avaliação/subsurf 1)
from render_torso import build_scene  # noqa: E402  (mesma câmara/luz/material)

ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
DOCS = os.path.join(ROOT, "docs", "head_phaseA")
RES = 520
TILE = 470          # tile no painel (como renders_T1_vs_refs)
VIEWS = [("front", 0.0), ("q", 0.6), ("side", 1.5708)]
REF_TILES = [("R·real005", "real005", True), ("R·femalebase", "femalebase", False)]

# só muda a mama (resto = H-TT1); default completo em body._breast_params()
VARIANTS = [
    ("V0", "baseline H-TT1", {}),
    ("V1", "base larga", {"sx": 0.058, "sy": 0.046}),
    ("V2", "gota (polo inferior longo)", {"sz": 0.065, "cz": -0.016, "dirz": -0.28, "sy": 0.042}),
    ("V3", "transição superior longa", {"sz": 0.050, "cz": -0.004, "dirz": -0.08, "amp": 0.88}),
    ("V4", "integrada na parede", {"amp": 0.76, "sx": 0.054, "sy": 0.046, "sz": 0.060}),
    ("V5", "lateral cheia", {"sx": 0.060, "cz": -0.012}),
    ("V6", "natural (combinação)", {"amp": 0.84, "sx": 0.056, "sy": 0.044, "sz": 0.060, "cz": -0.014, "dirz": -0.24}),
    ("V7", "redonda compacta", {"amp": 0.88, "sx": 0.044, "sy": 0.036, "sz": 0.050, "dirz": -0.12}),
]


def build_variant(vid, params):
    os.environ["HCG_HEAD"] = "faceB2"
    os.environ["HCG_NECK"] = "N1"
    os.environ["HCG_T1_AMP"] = "1"
    if params:
        os.environ["HCG_BREAST"] = json.dumps(params)
    else:
        os.environ.pop("HCG_BREAST", None)
    import human_generator as hcg
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob, do_unlink=True)
    r = hcg.generate_character("realistic_female", seed=42, name=f"sw{vid}",
                               write_blend=False, save_report=False)
    V, T = _eval([o for o in bpy.data.objects if o.type == "MESH"])
    _save(f"sw{vid}", V, T, drop_rule=True)
    print(f"BUILD {vid}: v={len(V)} digest={r.digest}")
    return r.digest


def load_tile(name, flip, drop=None):
    """Normalização idêntica à do render_torso.load_norm (refs e nossos @1700)."""
    d = np.load(os.path.join(WORK, f"raw_{name}.npz"))
    V, T = d["V"].copy(), d["T"]
    lab = np.load(os.path.join(WORK, f"lab_{name}.npy"))
    S, fl = V[:, 2].max() - V[:, 2].min(), V[:, 2].min()
    V[:, 2] -= fl
    V[:, 0] -= (V[:, 0].max() + V[:, 0].min()) / 2
    V *= 1700.0 / S
    if flip:
        V[:, 1] *= -1
    keep = ~np.isin(lab, drop) if drop else np.ones(len(lab), bool)
    V[:, 1] -= (V[keep][:, 1].max() + V[keep][:, 1].min()) / 2
    return V * 0.001, T[keep[T[:, 0]]]


def render_source(sc, cam, cam_data, key, V, T, view, ang):
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
    t = Vector((0.0, 0.0, 1.02))
    cam_data.ortho_scale = 1.06
    cam.location = (t.x + 4.0 * math.sin(ang), t.y + 4.0 * math.cos(ang), t.z)
    cam.rotation_euler = (t - cam.location).to_track_quat("-Z", "Y").to_euler()
    path = os.path.join(WORK, f"_sw_{key}_{view}.png")
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
    bpy.data.objects.remove(ob, do_unlink=True)
    bpy.data.meshes.remove(me)
    return path


def overlay_grid(im):
    """Grelha 8×8 (cols A–H, linhas 1–8) — modo B: referência espacial p/ dono."""
    from PIL import Image, ImageDraw
    im = im.convert("RGBA")
    ov = Image.new("RGBA", im.size, (0, 0, 0, 0))
    dr = ImageDraw.Draw(ov)
    n, step = 8, im.size[0] // 8
    for i in range(1, n):
        dr.line([(i * step, 0), (i * step, im.size[1])], fill=(255, 255, 255, 26), width=1)
        dr.line([(0, i * step), (im.size[0], i * step)], fill=(255, 255, 255, 26), width=1)
    for r in range(n):
        for c in range(n):
            if (r + c) % 2 == 0:
                dr.text((c * step + 3, r * step + 2),
                        f"{'ABCDEFGH'[c]}{r + 1}", fill=(255, 255, 255, 60))
    return Image.alpha_composite(im, ov)


def main():
    os.makedirs(DOCS, exist_ok=True)
    info = {"variants": [], "views": [v for v, _ in VIEWS], "tiles": {}}
    for vid, desc, params in VARIANTS:
        dg = build_variant(vid, params)
        info["variants"].append({"id": vid, "desc": desc, "params": params, "digest": dg})

    sc, cam, cam_data = build_scene()
    sources = [(vid, f"sw{vid}", None,
                json.load(open(os.path.join(WORK, f"drop_sw{vid}.json")))["drop_labels"])
               for vid, _, _ in VARIANTS] + \
              [(lbl, n, fl, None) for lbl, n, fl in REF_TILES]
    imgs = {}
    for lbl, name, flip, drop in sources:
        V, T = load_tile(name, flip, drop)
        for view, ang in VIEWS:
            imgs[(lbl, view)] = render_source(sc, cam, cam_data, lbl, V, T, view, ang)
        print(f"RENDER {lbl} ok")

    from PIL import Image, ImageDraw
    for view, _ in VIEWS:
        cols = 5
        rows = 2
        CW, CH, LH = TILE + 12, TILE + 6, 46
        sheet = Image.new("RGB", (CW * cols, (CH + LH) * rows + 30), (12, 12, 16))
        dr = ImageDraw.Draw(sheet)
        dr.text((12, 8), f"SWEEP 01 MAMA — vista {view} · responde p.ex. 'V2 > V6 > V0' "
                         f"ou aponta células ('V3 perfil C4')", fill=(240, 240, 240))
        for i, (lbl, name, _, _) in enumerate(sources):
            r, c = divmod(i, cols)
            x0, y0 = c * CW + 6, 30 + r * (CH + LH)
            im = Image.open(imgs[(lbl, view)]).convert("RGB").resize((TILE, TILE))
            im = overlay_grid(im).convert("RGB")
            sheet.paste(im, (x0, y0 + LH - 20))
            desc = next((v["desc"] for v in info["variants"] if v["id"] == lbl), "referência externa")
            dr.text((x0 + 4, y0 + 2), f"{lbl} · {desc}", fill=(240, 240, 240))
            # cobertura da máscara (para o agente; sem visão)
            g = np.asarray(Image.open(imgs[(lbl, view)]).convert("L"), float) / 255.0
            m = g > 0.25
            ys, xs = np.where(m)
            if len(xs):
                info["tiles"][f"{lbl}_{view}"] = {
                    "mask_x": [int(xs.min()), int(xs.max())],
                    "mask_y": [int(ys.min()), int(ys.max())],
                    "fill": round(float(m.mean()), 3)}
        out = os.path.join(DOCS, f"sweep_breast_{view}.png")
        sheet.save(out)
        print("folha →", out)
    json.dump(info, open(os.path.join(WORK, "sweep_breast.json"), "w"), indent=1)
    print("dados →", os.path.join(WORK, "sweep_breast.json"))


if __name__ == "__main__":
    main()
