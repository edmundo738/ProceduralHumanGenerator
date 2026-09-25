"""HEAD STUDY 01 — exporta a PELE da cabeça de cada fonte (bpy, sem alterar nada).

Para cada fonte: cage (Subdivision 0, modificadores de espelho aplicados) e
superfície (Subdivision 2) → out/head/<nome>_{cage,smooth}.npz com
  V (N×3, mundo), F (faces poligonais: 'fs' tamanhos + 'fi' índices), T (triângulos).
Nenhuma orientação/escala é aplicada aqui (isso é feito em analyse.py, declarado).

A nossa cabeça é gerada em processo por ``hcg.generate_character`` com o
gerador intacto (preset realistic_female, seed 42).  Os olhos, dentes, língua,
cabelo e roupa ficam de fora: só a pele (a cavidade é avaliada na pele).

Uso: python tools/headless_blender.py run tools/headstudy/export_heads.py [nomes...]
"""
import os, sys, json, hashlib, glob
import numpy as np
import bpy

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, ROOT)
R = os.environ.get("HCG_REF_DIR", os.path.join(ROOT, "out", "refs", "treino para o arena"))
OUT = os.environ.get("HCG_HEAD_WORK", os.path.join(ROOT, "out", "head"))
os.makedirs(OUT, exist_ok=True)

# fonte → (tipo, ficheiro, objetos de PELE com cabeça)
SOURCES = {
    "ours": ("gen", None, None),
    "oursA": ("gen", "massA", None),          # HEAD FASE A (HCG_HEAD=massA)
    "whitewalker": ("blend", "whitewalker-2016-06-06.blend", ["Cube"]),
    "makehuman": ("fbx", "Lucia_Prototype_v01.fbx", ["female_generic.objMesh"]),
    "femalechar": ("blend", "FemaleCharacter.blend", ["Plane.003"]),
    "bodytopo": ("blend", "Body Topo.blend", ["Geo body"]),
    "femalebase": ("obj", "Female base.obj", ["Female base"]),
    "ff11": ("obj", "fffemale 11.obj", ["head"]),
}


def src_digest():
    h = hashlib.sha256()
    for p in sorted(glob.glob(os.path.join(ROOT, "human_generator", "**", "*.py"), recursive=True)):
        h.update(open(p, "rb").read())
    return h.hexdigest()[:16]


def evaluate(objs, subsurf):
    dg = bpy.context.evaluated_depsgraph_get()
    Vs, FS, FI, Ts, off = [], [], [], [], 0
    global MAT
    MAT = []
    for ob in objs:
        saved = []
        for m in ob.modifiers:
            if m.type == "SUBSURF":
                saved.append((m, m.levels, m.render_levels))
                m.levels = subsurf
            if m.type == "ARMATURE":          # pose de repouso (sem deformação de rig)
                m.show_viewport = False
        dg.update()
        oe = ob.evaluated_get(dg)
        me = oe.to_mesh()
        n = len(me.vertices)
        co = np.empty(n * 3); me.vertices.foreach_get("co", co); co = co.reshape(-1, 3)
        M = np.array(ob.matrix_world)
        co = co @ M[:3, :3].T + M[:3, 3]
        fs = np.empty(len(me.polygons), dtype=np.int64); me.polygons.foreach_get("loop_total", fs)
        mi = np.empty(len(me.polygons), dtype=np.int64); me.polygons.foreach_get("material_index", mi)
        names = [(s.material.name if s.material else "") for s in ob.material_slots] or [""]
        MAT.append(np.array([names[min(i, len(names) - 1)] for i in mi]))
        fi = np.empty(len(me.loops), dtype=np.int64); me.loops.foreach_get("vertex_index", fi)
        me.calc_loop_triangles()
        t = np.empty(len(me.loop_triangles) * 3, dtype=np.int64); me.loop_triangles.foreach_get("vertices", t)
        Vs.append(co); FS.append(fs); FI.append(fi + off); Ts.append(t.reshape(-1, 3) + off); off += n
        oe.to_mesh_clear()
        for m, lv, rl in saved:
            m.levels = lv
    return np.vstack(Vs), np.concatenate(FS), np.concatenate(FI), np.vstack(Ts), np.concatenate(MAT)


def load(name):
    kind, f, objs = SOURCES[name]
    bpy.ops.wm.read_factory_settings(use_empty=True)
    meta = {"name": name}
    if kind == "gen":
        import human_generator as hcg
        if f:
            os.environ["HCG_HEAD"] = f
        else:
            os.environ.pop("HCG_HEAD", None)
        d0 = src_digest()
        r = hcg.generate_character("realistic_female", seed=42, out_dir=os.path.join(OUT, f"{name}_build"),
                                   name=f"headstudy_{name}")
        os.environ.pop("HCG_HEAD", None)
        meta.update(digest=r.digest, src_before=d0, src_after=src_digest())
        body = [bpy.data.objects[r.objects["body"]]]
        meta["result_objects"] = dict(r.objects)
        meta["objects"] = [o.name for o in body]
        meta["all_mesh_objects"] = [o.name for o in bpy.data.objects if o.type == "MESH"]
        return body, meta
    p = os.path.join(R, f)
    if kind == "blend":
        bpy.ops.wm.open_mainfile(filepath=p)
    elif kind == "obj":
        bpy.ops.wm.obj_import(filepath=p)
    else:
        bpy.ops.import_scene.fbx(filepath=p)
    meta["objects"] = objs
    return [bpy.data.objects[o] for o in objs], meta


def main():
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    names = args or list(SOURCES)
    for name in names:
        objs, meta = load(name)
        for tag, lv in (("cage", 0), ("smooth", 2)):
            V, FS, FI, T, FM = evaluate(objs, lv)
            np.savez_compressed(os.path.join(OUT, f"{name}_{tag}.npz"), V=V, fs=FS, fi=FI, T=T, fmat=FM)
            meta[f"{tag}_verts"] = int(len(V)); meta[f"{tag}_faces"] = int(len(FS))
        json.dump(meta, open(os.path.join(OUT, f"{name}_meta.json"), "w"), indent=1)
        print("HEADEXPORT", json.dumps(meta), flush=True)


main()
