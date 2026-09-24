# -*- coding: utf-8 -*-
"""Renders ortográficos de referência (frente/lado/costas/três-quartos).

Uso:
    python tools/headless_blender.py run tools/render_views.py OUT_DIR [preset] [seed] [--hair] [--full] [--feet] [--hands] [--face] [--hands]

Serve a BUILD 01 (silhueta) e qualquer verificação visual interna: as mesmas
vistas, a mesma câmara, para que duas execuções sejam comparáveis imagem a
imagem (``compare -metric RMSE``).

Notas declaradas de ambiente: EEVEE não corre headless neste contentor
(``libEGL.so.1`` ausente) — usa CYCLES/CPU.  O cabelo é escondido por omissão
porque a franja tapa os olhos (defeito visual conhecido, S4).
"""
from __future__ import annotations

import math
import os
import sys

sys.path.insert(0, ".")

import bpy                     # noqa: E402
from mathutils import Vector   # noqa: E402

from human_generator.pipeline import assemble   # noqa: E402
from human_generator.spec import CharacterSpec  # noqa: E402


def main() -> int:
    args = [a for a in sys.argv[1:]]
    out_dir = args[0] if args else "/tmp/hcg_views"
    preset = "realistic_female"
    seed = 42
    hair = "--hair" in args
    full = "--full" in args
    rest = [a for a in args[1:] if not a.startswith("--")]
    if rest:
        preset = rest[0]
    if len(rest) > 1:
        seed = int(rest[1])
    os.makedirs(out_dir, exist_ok=True)

    spec = CharacterSpec.from_preset(preset, seed=seed)
    res = assemble.generate_character(spec, name=f"view_{preset}", write_blend=False,
                                      save_report=False)
    body = bpy.data.objects[res.objects["body"]]
    hair_ob = bpy.data.objects[res.objects["hair"]]
    hair_ob.hide_render = not hair

    # A cena inicial do Blender traz Cube + Light + Camera.  Medido: o Cube
    # (2 m, topo em z=1.0) ficava entre a câmara e a figura e cortava-a pelas
    # ancas.  Isto é responsabilidade da FERRAMENTA de render: o gerador liga os
    # seus objectos à colecção ``hcg`` e não toca no resto da cena do utilizador.
    for ob in list(bpy.data.objects):
        if ob.name not in (res.objects["body"], res.objects["hair"]):
            bpy.data.objects.remove(ob, do_unlink=True)

    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    sc.cycles.samples = 24
    sc.cycles.use_denoising = True
    sc.render.resolution_x = 640 if full else 512
    sc.render.resolution_y = 900 if full else 512
    sc.world = bpy.data.worlds.new("w")
    sc.world.use_nodes = True
    sc.world.node_tree.nodes["Background"].inputs[0].default_value = (0.05, 0.05, 0.06, 1)

    cam_data = bpy.data.cameras.new("cam")
    cam_data.type = "ORTHO"
    cam_data.ortho_scale = 2.05 if full else 0.75
    cam = bpy.data.objects.new("cam", cam_data)
    sc.collection.objects.link(cam)
    sc.camera = cam

    # orthogonal-ish key + fill
    for name, energy, loc, size in (("key", 900, (2.2, 3.0, 3.2), 3.0),
                                    ("fill", 260, (-2.6, 2.2, 1.6), 3.0)):
        li = bpy.data.lights.new(name, "AREA")
        li.energy = energy
        li.size = size
        ob = bpy.data.objects.new(name, li)
        sc.collection.objects.link(ob)
        # luzes de área são visíveis à câmara no Cycles por omissão: sem isto
        # aparece uma laje branca a tapar metade da figura (medido).
        ob.visible_camera = False
        ob.location = loc
        direction = Vector((0, 0, 0.95)) - Vector(loc)
        ob.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()

    feet = "--feet" in args
    hands = "--hands" in args
    face = "--face" in args
    if feet:
        cam_data.ortho_scale = 0.38
    if face:
        # S4: a face ocupa ~120 mm — enquadramento no plano do rosto, escala
        # medida a partir da distância entre as comissuras (boca) para não
        # depender de um número fixo.
        lm = res.build.anatomy.landmarks
        c = Vector(lm["mouth"]) * 0.35 + Vector(lm["eye"]) * 0.65
        cam_data.ortho_scale = 0.30
        target = c
    elif hands:
        # S3.8: a mão tem ~180 mm de comprimento — o enquadramento é centrado no
        # punho e na ponta do dedo médio, medidos no próprio build (não há valor
        # fixo: a escala é a da figura, 1684 mm).
        lm = res.build.anatomy.landmarks
        w = Vector(lm["wrist.L"])
        tipm = Vector(lm["hand.L.middle.tip"])
        cam_data.ortho_scale = 0.34
        target = (w + tipm) * 0.5
    else:
        target = (Vector((0.0, 0.02, 0.06)) if feet else
                  Vector((0.0, 0.0, 0.95)) if full else Vector((0.0, 0.02, 1.30)))
    dist = 4.0
    views = ({"front": 0.0, "above": 0.5, "side": 1.5708} if feet else
             ({"out": 0.0, "back": 3.1416, "right": 1.5708, "left": -1.5708} if hands else
              ({"front": 0.0, "three_quarter": 0.6, "side": 1.5708} if face else
               {"front": 0.0, "three_quarter": 0.7, "side": 1.5708, "back": 3.1416})))
    for tag, ang in views.items():
        cam.location = (target.x + dist * math.sin(ang),
                        target.y + dist * math.cos(ang), target.z)
        direction = target - cam.location
        cam.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
        sc.render.filepath = os.path.join(out_dir, f"{tag}.png")
        bpy.ops.render.render(write_still=True)
        print("rendered", sc.render.filepath)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
