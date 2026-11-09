# -*- coding: utf-8 -*-
"""WAIFU v1 — monta a personagem anime game-ready a partir do blend SimpleRig.

Fonte: references/female/anime/full_body/REF-F-ANIME-001 (pack do dono).
O blend normal traz: corpo meio+Mirror (A-pose, ~40°), EyeBall/MouthPart NO
SÍTIO (olhos: face = −y, PROVA), Hand01 em espaço LOCAL (pulso no origem,
dedos ao longo do braço — PROVA por PCA: eixo principal (0.70,−0.31,−0.64)
≈ direcção do osso bn_hand (0.74,−0.41,−0.54), 8°), pés JÁ no corpo
(277 verts com forma de pé ao rés do chão; Foot0X são substitutos).

Passos:
  1. corpo: aplica Mirror, remove Subsurf (LOW POLY) e Armature (estático);
  2. Hand01: translada para bn_hand.L head (2.761,−0.549,5.912) SEM rotação;
     cópia espelhada para o outro lado;
  3. EyeBall/MouthPart: espelha a metade existente;
  4. cores kawaii (pele/olhos escuros/boca rosa) — UVs intactas;
  5. normaliza 1.58 m (Zelda), pés no chão; exporta GLB;
  6. extrai arrays (frame nosso mm@1700, +y=frente) + measure() p/ corpus.

Uso: LD_LIBRARY_PATH=/tmp/stubs python3 tools/waifu/build_waifu.py
"""
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
BLEND = os.path.join(ROOT, "references", "female", "anime", "full_body",
                     "REF-F-ANIME-001", "Anime_Female_A.blend")
WORK = os.path.join(ROOT, "out", "refstudy")

SKIN = (1.00, 0.84, 0.77, 1.0)     # pele quente clara
EYE = (0.07, 0.08, 0.16, 1.0)      # azul-marinho escuro (leitura anime)
MOUTH = (0.90, 0.50, 0.55, 1.0)    # rosa suave
TARGET_H = 1.58                    # estatura m (estilo Zelda feminino)
HAND_ANCHOR = (2.761, -0.549, 5.912)   # bn_hand.L head (bind)


def mirror_obj(obj):
    for v in obj.data.vertices:
        v.co.x = -v.co.x
    obj.data.update()
    for p in obj.data.polygons:
        p.flip()
    obj.data.update()


def main():
    import bpy
    bpy.ops.wm.open_mainfile(filepath=BLEND)

    body = bpy.data.objects["Anime_Female_A"]
    if body.data.shape_keys:
        body.shape_key_clear()
    for m in list(body.modifiers):
        if m.type == "SUBSURF":
            body.modifiers.remove(m)
    bpy.context.view_layer.objects.active = body
    bpy.ops.object.modifier_apply(modifier="Mirror")
    for m in list(body.modifiers):
        if m.type == "ARMATURE":
            body.modifiers.remove(m)
    print("corpo:", len(body.data.vertices), "verts,", len(body.data.polygons), "faces")

    parts = []
    # olho + boca: metade direita no sítio → espelhar
    for name in ("Anime_Female_A_EyeBall", "Anime_Female_A_MouthPart"):
        o = bpy.data.objects[name]
        o.parent = None
        for m in list(o.modifiers):
            o.modifiers.remove(m)
        copy = o.copy(); copy.data = o.data.copy(); copy.name = name + "_L"
        bpy.context.collection.objects.link(copy)
        mirror_obj(copy)
        parts += [o, copy]
        print(f"{name}: espelhada")
    # mão: transladar para o pulso + espelhar
    hand = bpy.data.objects["Anime_Female_A_Hand01"]
    hand.parent = None
    for m in list(hand.modifiers):
        hand.modifiers.remove(m)
    try:
        bpy.context.scene.collection.objects.link(hand)   # pode estar em colecção fora da view layer
    except RuntimeError:
        pass
    hand.location = HAND_ANCHOR
    for o in bpy.data.objects:
        o.select_set(False)
    hand.select_set(True)
    bpy.context.view_layer.objects.active = hand
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    copy = hand.copy(); copy.data = hand.data.copy(); copy.name = hand.name + "_R"
    bpy.context.collection.objects.link(copy)
    mirror_obj(copy)
    parts += [hand, copy]
    print("Hand01: ancorada em bn_hand.L + espelhada")

    # cores kawaii
    def mat(nome, cor):
        m = bpy.data.materials.new(nome)
        m.use_nodes = True
        bsdf = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
        bsdf.inputs["Base Color"].default_value = cor
        bsdf.inputs["Roughness"].default_value = 0.65
        return m
    m_skin, m_eye, m_mouth = mat("kawaii_skin", SKIN), mat("kawaii_eye", EYE), mat("kawaii_mouth", MOUTH)
    for i in range(len(body.data.materials)):
        body.data.materials[i] = m_skin
    for o in parts:
        target = m_eye if "EyeBall" in o.name else m_mouth if "MouthPart" in o.name else m_skin
        for i in range(len(o.data.materials)):
            o.data.materials[i] = target

    # normaliza estatura, pés no chão (transform_apply exige SELECÇÃO)
    objs = [body] + parts
    zmax = max(max(v.co.z for v in o.data.vertices) for o in objs)
    s = TARGET_H / zmax
    for o in bpy.data.objects:
        o.select_set(False)
    for o in objs:
        try:
            bpy.context.scene.collection.objects.link(o)
        except RuntimeError:
            pass
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    for o in objs:
        o.scale = (s, s, s)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    for o in objs:
        print(f"  {o.name:28} z {min(v.co.z for v in o.data.vertices):7.3f}..{max(v.co.z for v in o.data.vertices):7.3f}")

    # exporta GLB
    for o in bpy.data.objects:
        o.select_set(o in objs)
    out = os.path.join(ROOT, "site", "models")
    os.makedirs(out, exist_ok=True)
    for mesh in ("smooth", "cage"):
        p = os.path.join(out, f"waifu_{mesh}.glb")
        bpy.ops.export_scene.gltf(filepath=p, use_selection=True,
                                  export_format="GLB", export_apply=False)
        print("GLB →", p, f"{os.path.getsize(p)/1e6:.2f} MB")

    # arrays no frame nosso (z↑ mm@1700, +y frente ← blender −y) + medidas
    sys.path.insert(0, os.path.join(ROOT, "tools", "refstudy"))
    os.makedirs(WORK, exist_ok=True)
    from basemesh_proto import measure
    Vs, Ts, off = [], [], 0
    for o in objs:
        me = o.data
        V = np.array([list(v.co) for v in me.vertices]) * (1700.0 / TARGET_H)
        V[:, 1] = -V[:, 1]                      # blender −y frente → nosso +y
        tris = []
        for pg in me.polygons:
            vs = list(pg.vertices)
            for k in range(1, len(vs) - 1):
                tris.append((vs[0], vs[k], vs[k + 1]))
        T = np.array(tris, int) + off
        Vs.append(V); Ts.append(T); off += len(V)
    V = np.vstack(Vs); T = np.vstack(Ts)
    np.savez(os.path.join(WORK, "raw_waifu00.npz"), V=V, T=T)
    med = measure(V, T)
    print("waifu00 medidas:", {k: (tuple(np.round(v, 1)) if isinstance(v, tuple)
                                    else round(float(v), 1)) for k, v in med.items()})
    json.dump({"measures": {k: (list(v) if isinstance(v, tuple) else round(float(v), 2))
                            for k, v in med.items()},
               "verts": int(len(V)), "tris": int(len(T)),
               "skin": list(SKIN), "eye": list(EYE), "mouth": list(MOUTH)},
              open(os.path.join(WORK, "waifu_v1.json"), "w"), indent=1)
    print("json →", os.path.join(WORK, "waifu_v1.json"))


if __name__ == "__main__":
    main()
