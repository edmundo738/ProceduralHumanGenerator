"""REF STUDY 02 — inventário técnico de TODOS os ficheiros 3D das referências (bpy).

Não mede anatomia: regista o que cada ficheiro realmente contém (objetos, malhas,
modificadores, topologia, esqueleto, materiais) para classificar o que cada
referência pode ensinar.  Saída: WORK/inventory.json

Uso: python tools/headless_blender.py run tools/refstudy2/inspect_assets.py
"""
import json, os, sys
from collections import Counter
import bpy, bmesh

R = os.environ.get("HCG_REF_DIR", "out/refs/treino para o arena")
WORK = os.environ.get("HCG_RS2_WORK", "out/rs2")
os.makedirs(WORK, exist_ok=True)
OURS = os.environ.get("HCG_OURS_BLEND", os.path.join(WORK, "tree", "tree_realistic_female_s42.blend"))

FILES = {
    "ours": ("blend", OURS),
    "femalebase": ("obj", "Female base.obj"),
    "bodytopo": ("blend", "Body Topo.blend"),
    "femalechar": ("blend", "FemaleCharacter.blend"),
    "lucia_fbx": ("fbx", "Lucia_Prototype_v01.fbx"),
    "whitewalker": ("blend", "whitewalker-2016-06-06.blend"),
    "ff11": ("obj", "fffemale 11.obj"),
}


def load(kind, path):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    p = path if os.path.isabs(path) or path.startswith("out/") else os.path.join(R, path)
    if kind == "blend":
        bpy.ops.wm.open_mainfile(filepath=p)
    elif kind == "obj":
        bpy.ops.wm.obj_import(filepath=p)
    elif kind == "fbx":
        bpy.ops.import_scene.fbx(filepath=p)


def mesh_topology(ob):
    me = ob.data
    bm = bmesh.new(); bm.from_mesh(me)
    fs = Counter(min(len(f.verts), 5) for f in bm.faces)
    boundary = sum(1 for e in bm.edges if e.is_boundary)
    nonman = sum(1 for e in bm.edges if not e.is_manifold and not e.is_boundary)
    # valência só em vértices interiores (não fronteira) — poles = valência != 4
    val = Counter()
    for v in bm.verts:
        if v.is_boundary or not v.link_edges:
            continue
        val[min(len(v.link_edges), 8)] += 1
    # ilhas
    seen, islands = set(), 0
    for v in bm.verts:
        if v.index in seen:
            continue
        islands += 1
        stack = [v]
        while stack:
            u = stack.pop()
            if u.index in seen:
                continue
            seen.add(u.index)
            stack.extend(e.other_vert(u) for e in u.link_edges if e.other_vert(u).index not in seen)
    out = {"verts": len(bm.verts), "edges": len(bm.edges), "faces": len(bm.faces),
           "tris": fs.get(3, 0), "quads": fs.get(4, 0), "ngons": fs.get(5, 0),
           "boundary_edges": boundary, "nonmanifold_edges": nonman,
           "valence_interior": {str(k): val[k] for k in sorted(val)}, "islands": islands}
    bm.free()
    return out


def material_info(ob):
    mats = []
    for slot in ob.material_slots:
        m = slot.material
        if not m:
            continue
        imgs = []
        if m.use_nodes and m.node_tree:
            for n in m.node_tree.nodes:
                if n.type == "TEX_IMAGE" and n.image:
                    imgs.append(os.path.basename(n.image.filepath or n.image.name))
        mats.append({"name": m.name, "images": imgs})
    return mats


inv = {}
for key, (kind, path) in FILES.items():
    try:
        load(kind, path)
    except Exception as e:  # registado, não escondido
        inv[key] = {"error": repr(e)}
        continue
    objs = []
    for ob in bpy.data.objects:
        d = {"name": ob.name, "type": ob.type, "parent": ob.parent.name if ob.parent else None,
             "dims": [round(x, 4) for x in ob.dimensions],
             "scale": [round(x, 4) for x in ob.scale]}
        if ob.type == "MESH":
            d["topology"] = mesh_topology(ob)
            d["modifiers"] = [{"type": m.type, "name": m.name,
                               **({"levels": m.levels, "render_levels": m.render_levels}
                                  if m.type == "SUBSURF" else {}),
                               **({"object": m.object.name if getattr(m, "object", None) else None}
                                  if m.type in ("ARMATURE", "MIRROR", "SHRINKWRAP") else {}),
                               **({"use_axis": list(m.use_axis), "use_clip": m.use_clip}
                                  if m.type == "MIRROR" else {})}
                              for m in ob.modifiers]
            d["vertex_groups"] = len(ob.vertex_groups)
            d["vertex_group_sample"] = [g.name for g in ob.vertex_groups][:12]
            sk = ob.data.shape_keys
            d["shape_keys"] = [k.name for k in sk.key_blocks] if sk else []
            d["uv_layers"] = [u.name for u in ob.data.uv_layers]
            d["materials"] = material_info(ob)
        elif ob.type == "ARMATURE":
            bones = ob.data.bones
            d["bones"] = len(bones)
            d["root_bones"] = [b.name for b in bones if b.parent is None][:8]
            d["bone_sample"] = [b.name for b in bones][:40]
        objs.append(d)
    inv[key] = {"file": path, "kind": kind,
                "unit_scale": bpy.context.scene.unit_settings.scale_length,
                "objects": objs,
                "images_in_file": sorted({os.path.basename(i.filepath or i.name) for i in bpy.data.images})}
    print(f"{key:12s} objects={len(objs)} meshes={sum(o['type']=='MESH' for o in objs)}")

json.dump(inv, open(os.path.join(WORK, "inventory.json"), "w"), indent=1)
print("wrote", os.path.join(WORK, "inventory.json"))
