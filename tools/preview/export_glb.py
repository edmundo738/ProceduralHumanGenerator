"""Mini site de preview — exporta as versões do modelo para GLB (corre dentro do Blender headless).

Uso:
    python tools/headless_blender.py run tools/preview/export_glb.py -- OUT_DIR

Para cada versão (flags de ambiente, mesma seed/preset) gera o personagem, esconde
o cabelo, e exporta o corpo SEM materiais (avaliação neutra) em dois GLB:
  <id>_smooth.glb — malha avaliada com a subdivisão de render (o que os renders mostram)
  <id>_cage.glb   — a malha do gerador sem subdivisão (topologia real)
  <id>_edges.bin  — arestas reais da cage (float32 x,y,z Y-up, pares) para o wireframe
Escreve também OUT_DIR/models.json com estatísticas e digests.
Não altera o gerador; as flags são as mesmas dos estudos (HCG_HEAD / HCG_NECK).
"""
import json
import os
import sys

sys.path.insert(0, ".")
import bpy  # noqa: E402

VARIANTS = [
    {"id": "antes", "label": "ANTES (cabeça antiga)", "env": {}, "commit": "8716b88…de08023"},
    {"id": "faseA", "label": "FASE A (massas R1)", "env": {"HCG_HEAD": "massA"}, "commit": "642cb7f"},
    {"id": "a2b", "label": "A2b (canto mentoniano)", "env": {"HCG_HEAD": "massA2"}, "commit": "5eb8c32"},
    {"id": "n1", "label": "A2b + N1 (pescoço superior)", "env": {"HCG_HEAD": "massA2", "HCG_NECK": "N1"}, "commit": "3ad83da"},
    {"id": "f1", "label": "F1 (face: campos + corretiva)", "env": {"HCG_HEAD": "faceB", "HCG_NECK": "N1"}, "commit": "2d6039f"},
]


def set_env(env):
    for k in ("HCG_HEAD", "HCG_NECK"):
        os.environ.pop(k, None)
    os.environ.update(env)


def export_obj(src, path, evaluated):
    dg = bpy.context.evaluated_depsgraph_get()
    ob_eval = src.evaluated_get(dg) if evaluated else src
    me = bpy.data.meshes.new_from_object(ob_eval, preserve_all_data_layers=False, depsgraph=dg)
    me.materials.clear()
    tmp = bpy.data.objects.new(src.name + ("_s" if evaluated else "_c"), me)
    tmp.matrix_world = src.matrix_world.copy()
    bpy.context.scene.collection.objects.link(tmp)
    for o in bpy.context.view_layer.objects:
        o.select_set(False)
    tmp.select_set(True)
    bpy.context.view_layer.objects.active = tmp
    bpy.ops.export_scene.gltf(filepath=path, use_selection=True, export_format="GLB", export_materials="NONE",
                              export_apply=False, export_yup=True, export_normals=True, export_texcoords=False,
                              export_animations=False, export_skins=False, export_morph=False)
    stats = {"verts": len(me.vertices), "faces": len(me.polygons),
             "quads": sum(1 for p in me.polygons if len(p.vertices) == 4),
             "bytes": os.path.getsize(path)}
    bpy.data.objects.remove(tmp)
    bpy.data.meshes.remove(me)
    return stats


def main():
    args = sys.argv[1:]
    out = args[0] if args else "out/preview/models"
    os.makedirs(out, exist_ok=True)
    import human_generator as hcg
    manifest = []
    for v in VARIANTS:
        bpy.ops.wm.read_factory_settings(use_empty=True)
        set_env(v["env"])
        r = hcg.generate_character("realistic_female", seed=42, name=f"prev_{v['id']}",
                                   write_blend=False, save_report=False)
        body = bpy.data.objects[r.objects["body"]]
        # sem armadura/shape keys na avaliação: só a geometria de repouso + subdivisão
        for m in list(body.modifiers):
            if m.type not in ("SUBSURF",):
                body.modifiers.remove(m)
        if body.data.shape_keys:
            body.shape_key_clear()
        smooth = export_obj(body, os.path.join(out, f"{v['id']}_smooth.glb"), True)
        for m in list(body.modifiers):
            body.modifiers.remove(m)
        cage = export_obj(body, os.path.join(out, f"{v['id']}_cage.glb"), False)
        # arestas REAIS da cage (quads, não a triangulação do GLB), em Y-up: (x, z, −y)
        import array
        mw = body.matrix_world
        co = [mw @ vv.co for vv in body.data.vertices]
        buf = array.array("f")
        for e in body.data.edges:
            for i in e.vertices:
                p_ = co[i]
                buf.extend((p_.x, p_.z, -p_.y))
        with open(os.path.join(out, f"{v['id']}_edges.bin"), "wb") as fh:
            buf.tofile(fh)
        cage["edges"] = len(body.data.edges)
        entry = dict(v, digest=r.digest, smooth=smooth, cage=cage)
        manifest.append(entry)
        print("PREVIEW", json.dumps({"id": v["id"], "digest": r.digest, "smooth": smooth, "cage": cage}))
    set_env({})
    json.dump(manifest, open(os.path.join(out, "models.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
