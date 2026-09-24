"""Gera o .blend da árvore de trabalho ATUAL (mesma via da API pública) para medição local.
Não é uma BUILD: é o artefacto intermédio de um experimento.
Uso: python tools/headless_blender.py run tools/refstudy/gen_blend.py OUT_DIR"""
import os, sys, json
sys.path.insert(0, os.getcwd())
import bpy
import human_generator as hcg
for ob in list(bpy.data.objects):          # cena de arranque (Cube/Light/Camera) fora
    bpy.data.objects.remove(ob, do_unlink=True)
r = hcg.generate_character("realistic_female", seed=42, out_dir=sys.argv[1], name="tree_realistic_female_s42")
print("GEN", json.dumps({"blend": r.files["blend"], "digest": r.digest, "fingerprint": r.fingerprint,
                         "audit": {k: r.audit[k] for k in ("verts", "faces", "non_manifold_edges", "degenerate_faces", "loose_edges", "ngons", "boundary_edges")}}))
