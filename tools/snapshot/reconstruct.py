# -*- coding: utf-8 -*-
"""SNAPSHOT MÍNIMO (protótipo) — reconstrói a cena dos dados e VERIFICA digests.

Lê OUT_DIR/{manifest.json, scene.json, meshes/*.npz}, reconstrói cada malha
(verts + polígonos, transform, materiais com o nome original como placeholder)
e recalcula o digest de geometria: PASS/FAIL por objeto.

Uso: python tools/headless_blender.py run tools/snapshot/reconstruct.py -- OUT_DIR
"""
import hashlib
import json
import os
import sys

import numpy as np

import bpy
from mathutils import Matrix


def digest_of(V, lv, lt):
    return hashlib.sha256(V.astype(np.float64).tobytes() + lv.astype(np.int64).tobytes()
                          + lt.astype(np.int64).tobytes()).hexdigest()


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    out = args[0] if args else "out/snapshot"
    manifest = json.load(open(os.path.join(out, "manifest.json")))
    scene = json.load(open(os.path.join(out, "scene.json")))
    if ".".join(str(x) for x in bpy.app.version) != manifest["blender"]:
        print("AVISO: versão Blender difere do snapshot:", bpy.app.version, "vs", manifest["blender"])
    bpy.ops.wm.read_factory_settings(use_empty=True)
    results = []
    for o in scene["objects"]:
        d = np.load(os.path.join(out, o["mesh_file"]))
        V, lv, ls, lt = d["V"], d["loop_vert"], d["loop_start"], d["loop_total"]
        faces = [list(map(int, lv[ls[i]:ls[i] + lt[i]])) for i in range(len(ls))]
        me = bpy.data.meshes.new(o["name"])
        me.from_pydata([tuple(map(float, v)) for v in V], [], faces)
        me.validate()
        ob = bpy.data.objects.new(o["name"], me)
        bpy.context.scene.collection.objects.link(ob)
        ob.matrix_world = Matrix(np.array(o["matrix_world"]).reshape(4, 4))
        for mname in o["materials"]:
            mat = bpy.data.materials.get(mname) or bpy.data.materials.new(mname)
            me.materials.append(mat)
        # digest da malha RECONSTRUÍDA em coordenadas de mundo
        M = np.array(ob.matrix_world)
        co = np.empty(len(me.vertices) * 3)
        me.vertices.foreach_get("co", co)
        Vw = co.reshape(-1, 3) @ M[:3, :3].T + M[:3, 3]
        nlv = np.empty(len(me.loops), dtype=np.int64)
        me.loops.foreach_get("vertex_index", nlv)
        nlt = np.empty(len(me.polygons), dtype=np.int64)
        me.polygons.foreach_get("loop_total", nlt)
        got = digest_of(Vw, nlv, nlt)
        ok = got == o["digest"]
        results.append((o["name"], ok))
        print("VERIFY", o["name"], "PASS" if ok else "FAIL")
    n_ok = sum(1 for _, ok in results if ok)
    print("SNAPSHOT-VERIFY", json.dumps({"objects": len(results), "pass": n_ok,
                                         "fail": len(results) - n_ok}))
    sys.exit(0 if n_ok == len(results) else 1)


if __name__ == "__main__":
    main()
