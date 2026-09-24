"""REF STUDY 02 (bpy): exporta a malha-CAGE (antes da Subdivision; Mirror aplicado)
com polígonos, para análise de topologia.  Saída: WORK/cage_<nome>.npz (V, F flat, Fn)."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "refstudy"))
import numpy as np, bpy
R = os.environ.get("HCG_REF_DIR", "out/refs/treino para o arena")
WORK = os.environ.get("HCG_RS2_WORK", "out/rs2")
SRC = {"ours": ("blend", os.path.join(WORK, "tree", "tree_realistic_female_s42.blend"), None),
       "femalebase": ("obj", "Female base.obj", None),
       "bodytopo": ("blend", "Body Topo.blend", "Geo body"),
       "femalechar": ("blend", "FemaleCharacter.blend", "Plane.003"),
       "makehuman": ("fbx", "Lucia_Prototype_v01.fbx", "female_generic.objMesh"),
       "whitewalker": ("blend", "whitewalker-2016-06-06.blend", "Cube")}
for key, (kind, path, obname) in SRC.items():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    p = path if path.startswith("out/") else os.path.join(R, path)
    {"blend": lambda: bpy.ops.wm.open_mainfile(filepath=p), "obj": lambda: bpy.ops.wm.obj_import(filepath=p),
     "fbx": lambda: bpy.ops.import_scene.fbx(filepath=p)}[kind]()
    obs = [bpy.data.objects[obname]] if obname else [o for o in bpy.data.objects if o.type == "MESH"]
    V, F, Fn, off = [], [], [], 0
    for ob in obs:
        for m in ob.modifiers:
            if m.type == "SUBSURF":
                m.show_viewport = False
        dg = bpy.context.evaluated_depsgraph_get(); dg.update()
        oe = ob.evaluated_get(dg); me = oe.to_mesh()
        M = np.array(ob.matrix_world)
        co = np.array([v.co[:] for v in me.vertices]) @ M[:3, :3].T + M[:3, 3]
        for poly in me.polygons:
            F.extend(i + off for i in poly.vertices); Fn.append(len(poly.vertices))
        V.append(co); off += len(co); oe.to_mesh_clear()
    V = np.vstack(V)
    np.savez(os.path.join(WORK, f"cage_{key}.npz"), V=V, F=np.array(F), Fn=np.array(Fn))
    print(key, "cage v", len(V), "faces", len(Fn))
