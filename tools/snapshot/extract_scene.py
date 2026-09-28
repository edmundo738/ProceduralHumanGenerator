# -*- coding: utf-8 -*-
"""SNAPSHOT MÍNIMO (protótipo) — cena Blender → dados reproduzíveis → reconstrução.

Pedido do dono (2026-09-28): instrumento SEPARADO da Reference Library, para
estudar "o que precisa de ser preservado para reproduzir uma cena".  MÍNIMO
declrado: geometria (verts + polígonos), transforms, nomes de
materiais/modificadores, versões e hashes.  NÃO extraído ainda: node trees,
armaduras/skinning, shape keys, texturas, world/lights (evolui conforme
descobrirmos o que é necessário — docs/REFERENCE_LIBRARY.md §8).

Uso (dentro do Blender headless; opcionalmente abre um .blend primeiro):
  python tools/headless_blender.py run tools/snapshot/extract_scene.py -- OUT_DIR [blend]
Escreve OUT_DIR/{manifest.json, scene.json, meshes/*.npz}
"""
import hashlib
import json
import os
import sys

import numpy as np

import bpy



def sha256_bytes(b):
    return hashlib.sha256(b).hexdigest()


def dump_mesh(ob, path):
    me = ob.data
    nv = len(me.vertices)
    co = np.empty(nv * 3)
    me.vertices.foreach_get("co", co)
    V = co.reshape(-1, 3)
    M = np.array(ob.matrix_world)
    Vw = V @ M[:3, :3].T + M[:3, 3]      # mundo — só para o digest
    nl = len(me.loops)
    lv = np.empty(nl, dtype=np.int64)
    me.loops.foreach_get("vertex_index", lv)
    ls = np.empty(len(me.polygons), dtype=np.int64)
    lt = np.empty(len(me.polygons), dtype=np.int64)
    me.polygons.foreach_get("loop_start", ls)
    me.polygons.foreach_get("loop_total", lt)
    uv = None
    if me.uv_layers.active is not None:
        u = np.empty(nl * 2)
        me.uv_layers.active.data.foreach_get("uv", u)
        uv = u.reshape(-1, 2)
    digest = sha256_bytes(Vw.astype(np.float64).tobytes() + lv.astype(np.int64).tobytes()
                          + lt.astype(np.int64).tobytes())
    np.savez_compressed(path, V=V, loop_vert=lv, loop_start=ls, loop_total=lt,
                        UV=uv if uv is not None else np.zeros((0, 2)))
    return {"verts": nv, "polygons": len(me.polygons), "digest": digest}


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    out = args[0] if args else "out/snapshot"
    os.makedirs(os.path.join(out, "meshes"), exist_ok=True)
    if len(args) > 1 and args[1].endswith(".blend"):
        bpy.ops.wm.read_factory_settings(use_empty=True)
        bpy.ops.wm.open_mainfile(filepath=args[1])
    objs = []
    for ob in bpy.data.objects:
        if ob.type != "MESH":
            continue
        name = ob.name.replace("/", "_")
        st = dump_mesh(ob, os.path.join(out, "meshes", f"{name}.npz"))
        objs.append({"name": ob.name, "type": ob.type,
                     "matrix_world": [float(x) for x in np.array(ob.matrix_world).reshape(-1)],
                     "parent": ob.parent.name if ob.parent else None,
                     "modifiers": [{"type": m.type, "name": m.name} for m in ob.modifiers],
                     "materials": [m.name for m in ob.data.materials if m],
                     "mesh_file": f"meshes/{name}.npz", **st})
    manifest = {
        "blender": ".".join(str(x) for x in bpy.app.version),
        "blender_hash": bpy.app.build_hash.decode(),
        "python": sys.version.split()[0],
        "objects": len(objs),
        "note": "SNAPSHOT MÍNIMO (protótipo): geometria+transform+nomes; sem nodes/armadura/texturas (evolui)",
        "reconstruct": "python tools/headless_blender.py run tools/snapshot/reconstruct.py -- " + out,
    }
    json.dump(manifest, open(os.path.join(out, "manifest.json"), "w"), indent=1)
    json.dump({"objects": objs}, open(os.path.join(out, "scene.json"), "w"), indent=1)
    print("SNAPSHOT", json.dumps({"out": out, "objects": len(objs)}))


if __name__ == "__main__":
    main()
