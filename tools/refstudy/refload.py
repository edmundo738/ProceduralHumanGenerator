"""Carrega cada referência como (verts Nx3 mundo, tris Mx3) com Z para cima."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _paths import WORK  # noqa: E402
import bpy, os, numpy as np
R = os.environ.get("HCG_REF_DIR", "out/refs/treino para o arena")
BUILD = os.environ.get("HCG_BUILD_BLEND", os.path.join(WORK, "build", "build02_realistic_female_s42", "hcg_realistic_female_ad620a90.blend"))

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
        n = len(me.vertices)
        co = np.empty(n * 3); me.vertices.foreach_get("co", co); co = co.reshape(-1, 3)
        M = np.array(ob.matrix_world)
        co = co @ M[:3, :3].T + M[:3, 3]
        t = np.empty(len(me.loop_triangles) * 3, dtype=np.int64)
        me.loop_triangles.foreach_get("vertices", t)
        V.append(co); T.append(t.reshape(-1, 3) + off); off += n
        oe.to_mesh_clear()
    return np.vstack(V), np.vstack(T)

def load(name):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    if name == "ours":
        bpy.ops.wm.open_mainfile(filepath=BUILD)
        obs = [o for o in bpy.data.objects if o.type == "MESH"]
        return _eval(obs, subsurf_max=1)
    if name == "bodytopo":
        bpy.ops.wm.open_mainfile(filepath=os.path.join(R, "Body Topo.blend"))
        return _eval([bpy.data.objects["Geo body"]])
    if name == "femalebase":
        bpy.ops.wm.obj_import(filepath=os.path.join(R, "Female base.obj"))
        return _eval([o for o in bpy.data.objects if o.type == "MESH"])
    if name == "ff11":
        bpy.ops.wm.obj_import(filepath=os.path.join(R, "fffemale 11.obj"))
        return _eval([bpy.data.objects[n] for n in ("body", "head")])
    if name == "makehuman":
        bpy.ops.import_scene.fbx(filepath=os.path.join(R, "Lucia_Prototype_v01.fbx"))
        return _eval([bpy.data.objects["female_generic.objMesh"]])
    if name == "femalechar":
        bpy.ops.wm.open_mainfile(filepath=os.path.join(R, "FemaleCharacter.blend"))
        return _eval([bpy.data.objects["Plane.003"]])
    if name == "whitewalker":
        bpy.ops.wm.open_mainfile(filepath=os.path.join(R, "whitewalker-2016-06-06.blend"))
        return _eval([bpy.data.objects["Cube"]])
    raise KeyError(name)

NAMES = ["ours", "bodytopo", "femalebase", "ff11", "makehuman", "femalechar", "whitewalker"]
