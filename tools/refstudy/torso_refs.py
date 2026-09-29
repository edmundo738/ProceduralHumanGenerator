# -*- coding: utf-8 -*-
"""T-TORSO SISTEMA — extracção de TODOS os modelos do estudo (biblioteca + nós).

Carrega cada modelo da BIBLIOTECA (caminhos directos, sem out/refs) e o nosso
(geração pela API pública, subsurf nível 1 — a medição do estudo mede o
subsurf) e escreve ``raw_<id>.npz`` + ``lab_<id>.npy`` (+ ``drop_<id>.json``
para os nossos, regra braços/mãos/dedos do comps.py).

Modelos (id → fonte):
  ours      nós, T1 on  (HCG_HEAD=faceB2 HCG_NECK=N1, campo S activo)
  ours0     nós, T1 off (HCG_T1_AMP=0 — mesma topologia)
  femalebase  REF-F-REAL-001 Female base.obj          (realista)
  bodytopo    REF-F-REAL-002 Body Topo.blend Geo body (base mesh, sem pés)
  femalechar  REF-F-REAL-003 FemaleCharacter.blend    (realista estilizada?)
  lucia       REF-F-REAL-004 Lucia_Prototype_v01.fbx  (makehuman)
  real005     REF-F-REAL-005 GLB, pele Std_Skin_*     (ADMITIDA)
  mppled      REF-F-REAL-007 MPPled.fbx               (torso esculpido; escala própria)
  ff11        REF-F-ANIR-001 fffemale 11.obj          (anime_realistic)
  animeF      REF-F-ANIME-002 Base_Female_A.blend     (anime)
  whitewalker REF-M-REAL-001 (masculina, contraste de sexo)

EXCLUÍDA por decisão medida: real006/MOLLY (estilizada — TORSO_STUDY_01 §7.2).
A ORIENTAÇÃO (flip) decide-se por medição sagital (torso_orient.py) — nunca
pelo eixo do ficheiro.

Uso: python tools/headless_blender.py run tools/refstudy/torso_refs.py
"""
import json
import os
import sys

sys.path.insert(0, os.getcwd())
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _paths import WORK  # noqa: E402

import numpy as np  # noqa: E402
import geom  # noqa: E402

import bpy  # noqa: E402

LIB = "references"


def _patch_fbx_lights():
    """BUG bpy 5.0: FBX com luzes (CyclesLightSettings.cast_shadow removido;
    medido em MPPled.fbx). Patch do inspetor (tools/reflib/inspect_model.py):
    ignora o erro nos settings de sombra — não afecta a geometria."""
    try:
        import io_scene_fbx.import_fbx as _IF
        _orig = _IF.blen_read_light

        def _safe_light(*a, **k):
            try:
                return _orig(*a, **k)
            except AttributeError:
                return None
        _IF.blen_read_light = _safe_light
    except Exception:
        pass


def _eval(objs, subsurf_max=1):
    dg = bpy.context.evaluated_depsgraph_get()
    V, T, off = [], [], 0
    for ob in objs:
        for m in ob.modifiers:
            if m.type == "SUBSURF":
                m.levels = min(m.levels, subsurf_max)
        dg.update()
        oe = ob.evaluated_get(dg)
        me = oe.to_mesh()
        me.calc_loop_triangles()
        co = np.empty(len(me.vertices) * 3)
        me.vertices.foreach_get("co", co)
        co = co.reshape(-1, 3)
        M = np.array(ob.matrix_world)
        co = co @ M[:3, :3].T + M[:3, 3]
        t = np.empty(len(me.loop_triangles) * 3, dtype=np.int64)
        me.loop_triangles.foreach_get("vertices", t)
        V.append(co)
        T.append(t.reshape(-1, 3) + off)
        off += len(co)
        oe.to_mesh_clear()
    return np.vstack(V), np.vstack(T)


def _save(name, V, T, drop_rule=False):
    lab = geom.components(V, T)
    np.savez(os.path.join(WORK, f"raw_{name}.npz"), V=V, T=T)
    np.save(os.path.join(WORK, f"lab_{name}.npy"), lab)
    if drop_rule:                      # nossos: cascas braços/mãos/dedos
        drop = [int(c) for c in range(lab.max() + 1)
                if np.abs(V[lab == c][:, 0]).min() > 0.07
                and V[lab == c][:, 2].min() > 0.6 and V[lab == c][:, 2].max() < 1.45]
        json.dump({"drop_labels": drop}, open(os.path.join(WORK, f"drop_{name}.json"), "w"))
    print(f"SAVE {name}: v={len(V)} tris={len(T)} comps={lab.max() + 1}")


def load_ours(amp):
    os.environ["HCG_HEAD"] = "faceB2"
    os.environ["HCG_NECK"] = "N1"
    os.environ["HCG_T1_AMP"] = str(amp)
    import human_generator as hcg
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob, do_unlink=True)
    r = hcg.generate_character("realistic_female", seed=42, name=f"tts_{amp}",
                               write_blend=False, save_report=False)
    print(f"GEN amp={amp} digest={r.digest}")
    V, T = _eval([o for o in bpy.data.objects if o.type == "MESH"])
    _save("ours" if amp else "ours0", V, T, drop_rule=True)


def load_ref(name):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    if name == "femalebase":
        bpy.ops.wm.obj_import(filepath=f"{LIB}/female/realistic/full_body/REF-F-REAL-001/Female base.obj")
        objs = [o for o in bpy.data.objects if o.type == "MESH"]
    elif name == "bodytopo":
        bpy.ops.wm.open_mainfile(filepath=f"{LIB}/female/realistic/full_body/REF-F-REAL-002/Body Topo.blend")
        objs = [bpy.data.objects["Geo body"]]
    elif name == "femalechar":
        bpy.ops.wm.open_mainfile(filepath=f"{LIB}/female/realistic/full_body/REF-F-REAL-003/FemaleCharacter.blend")
        objs = [bpy.data.objects["Plane.003"]]
    elif name == "lucia":
        _patch_fbx_lights()
        bpy.ops.import_scene.fbx(filepath=f"{LIB}/female/realistic/full_body/REF-F-REAL-004/Lucia_Prototype_v01.fbx")
        objs = [bpy.data.objects["female_generic.objMesh"]]
    elif name == "real005":
        bpy.ops.import_scene.gltf(filepath=f"{LIB}/female/realistic/full_body/REF-F-REAL-005/realistic_female_base_mesh__t-pose.glb")
        objs = [o for o in bpy.data.objects if o.type == "MESH"
                and any(m and m.name.startswith("Std_Skin") for m in o.data.materials)]
    elif name == "mppled":
        _patch_fbx_lights()
        bpy.ops.import_scene.fbx(filepath=f"{LIB}/female/realistic/torso/REF-F-REAL-007/MPPled.fbx")
        objs = [o for o in bpy.data.objects if o.type == "MESH"]
    elif name == "ff11":
        bpy.ops.wm.obj_import(filepath=f"{LIB}/female/anime_realistic/full_body/REF-F-ANIR-001/fffemale 11.obj")
        objs = [bpy.data.objects[n] for n in ("body", "head")]
    elif name == "animeF":
        bpy.ops.wm.open_mainfile(filepath=f"{LIB}/female/anime/full_body/REF-F-ANIME-002/Base_Female_A.blend")
        objs = [bpy.data.objects["Base_Female_A"]]
    elif name == "whitewalker":
        bpy.ops.wm.open_mainfile(filepath=f"{LIB}/male/realistic/full_body/REF-M-REAL-001/whitewalker-2016-06-06.blend")
        objs = [bpy.data.objects["Cube"]]
    else:
        raise KeyError(name)
    V, T = _eval(objs)
    _save(name, V, T)


if __name__ == "__main__":
    _patch_fbx_lights()
    load_ours(1)
    load_ours(0)
    for n in ("femalebase", "bodytopo", "femalechar", "lucia", "real005",
              "mppled", "ff11", "animeF", "whitewalker"):
        load_ref(n)
