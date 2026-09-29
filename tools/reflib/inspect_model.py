# -*- coding: utf-8 -*-
"""REFERENCE LIBRARY — inspetor de modelos (bpy): extração geométrica por modelo.

Instrumento de ESTUDO (observação externa; nunca altera o gerador).  Para cada
entrada da biblioteca carrega o ficheiro (.blend/.obj/.fbx) no Blender headless
e extrai o que a API dá com fiabilidade (matriz de capacidades:
docs/REFERENCE_LIBRARY.md §6):

  contagens (verts/arestas/faces/quads/tris/ngons), ilhas (componentes),
  bbox + unidades, arestas de contorno/não-manifold, faces degeneradas,
  estatísticas de densidade (comprimento de aresta), UV, grupos, shape keys,
  modificadores, materiais, armadura, pose_hint (HEURÍSTICA declarada).

Saída: <modelo>/extraction.json.  Proveniência: modelo → dados → transformação
(nenhuma) → métricas → resultado.  Sem interpretação anatômica automática.

Uso:
  python tools/headless_blender.py run tools/reflib/inspect.py -- <dir_do_modelo>
  python tools/headless_blender.py run tools/reflib/inspect.py -- all
"""
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..", "..")
sys.path.insert(0, HERE)
sys.path.insert(0, ROOT)

import bpy  # noqa: E402

import schema  # noqa: E402

LIB = os.path.join(ROOT, "references")
EXTS = (".blend", ".glb", ".obj", ".fbx")


def find_model_file(d):
    """Ficheiro principal: prefere o que tem o nome da pasta; senão .blend>.glb>.obj>.fbx."""
    cand = sorted(f for f in os.listdir(d) if f.lower().endswith(EXTS))
    if not cand:
        return None
    stem = os.path.basename(d)
    same = [f for f in cand if os.path.splitext(f)[0] == stem]
    if same:
        return same[0]
    for ext in (".blend", ".glb", ".obj", ".fbx"):
        for f in cand:
            if f.lower().endswith(ext):
                return f
    return cand[0]


def load_model(path):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    if path.lower().endswith(".blend"):
        bpy.ops.wm.open_mainfile(filepath=path)
    elif path.lower().endswith(".obj"):
        bpy.ops.wm.obj_import(filepath=path)
    elif path.lower().endswith(".fbx"):
        # BUG do importador FBX do bpy 5.0 com ficheiros com LUZES
        # (CyclesLightSettings.cast_shadow foi removido; medido em MPPled.fbx).
        # Patch defensivo: ignora o erro nos settings de sombra da luz (não afeta
        # a geometria, que é o que este inspetor mede).
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
        bpy.ops.import_scene.fbx(filepath=path)
    elif path.lower().endswith(".glb") or path.lower().endswith(".gltf"):
        bpy.ops.import_scene.gltf(filepath=path)
    else:
        raise ValueError(path)
    return [o for o in bpy.data.objects if o.type == "MESH"]


def obj_stats(ob):
    me = ob.data
    me.calc_loop_triangles()
    nv, ne, nf = len(me.vertices), len(me.edges), len(me.polygons)
    quads = sum(1 for p in me.polygons if len(p.vertices) == 4)
    tris = sum(1 for p in me.polygons if len(p.vertices) == 3)
    ngons = nf - quads - tris
    # ilhas por adjacência de arestas (união-find em numpy)
    parent = np.arange(nv)

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    ev = np.empty(ne * 2, dtype=np.int64)
    me.edges.foreach_get("vertices", ev)
    ev = ev.reshape(-1, 2)
    for a, b in ev:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb
    roots = np.array([find(i) for i in range(nv)])
    islands = len(np.unique(roots))
    # contorno / não-manifold via edge_keys (bpy 5.0 removeu MeshEdge.is_boundary;
    # contamos polígonos por aresta: 1 = contorno, >2 = não-manifold)
    from collections import Counter
    ek = Counter()
    for p in me.polygons:
        for k in p.edge_keys:
            ek[k] += 1
    boundary = sum(1 for v in ek.values() if v == 1)
    nonman = sum(1 for v in ek.values() if v > 2)
    degen = 0
    co = np.empty(nv * 3)
    me.vertices.foreach_get("co", co)
    co = co.reshape(-1, 3)
    for p in me.polygons:
        vs = co[list(p.vertices)]
        if len(vs) >= 3:
            n = np.cross(vs[1] - vs[0], vs[2] - vs[0])
            if float(n @ n) < 1e-18:
                degen += 1
    el = np.empty(ne)
    # comprimento de aresta em numpy (calc_length por edge é lento via RNA)
    d = co[ev[:, 0]] - co[ev[:, 1]]
    # bbox e comprimentos em coordenadas de MUNDO (a local pode ter rotação)
    M = np.array(ob.matrix_world)
    cow = co @ M[:3, :3].T + M[:3, 3]
    el = np.linalg.norm(cow[ev[:, 0]] - cow[ev[:, 1]], axis=1)
    sc = float(np.cbrt(abs(np.linalg.det(M[:3, :3]))))
    bb = (cow.min(0), cow.max(0))
    return {
        "object": ob.name, "verts": nv, "edges": ne, "faces": nf,
        "quads": quads, "tris": tris, "ngons": ngons, "islands": islands,
        "boundary_edges": boundary, "non_manifold_edges": nonman,
        "degenerate_faces": degen,
        "edge_len": {"p05": float(np.percentile(el, 5)), "p50": float(np.percentile(el, 50)),
                     "p95": float(np.percentile(el, 95))},
        "bbox_world": [bb[0].tolist(), bb[1].tolist()],
        "scale_factor_object": sc,
        "uv_layers": len(me.uv_layers), "vertex_groups": len(ob.vertex_groups),
        "shape_keys": len(ob.data.shape_keys.key_blocks) if ob.data.shape_keys else 0,
        "modifiers": [m.type for m in ob.modifiers],
        "materials": [m.name for m in ob.data.materials if m],
        "armature": ob.find_armature() is not None,
    }


def pose_hint(stats):
    """HEURÍSTICA declarada: razão largura/altura do maior objeto."""
    main = max(stats, key=lambda s: s["verts"])
    bb = main["bbox_world"]
    w = bb[1][0] - bb[0][0]
    h = bb[1][2] - bb[0][2]
    r = w / h if h else 0.0
    if r > 0.45:
        return "t_pose (envergadura ≈ altura)", round(r, 3)
    if r > 0.30:
        return "a_pose?", round(r, 3)
    return "braços caídos/outra", round(r, 3)


def inspect_dir(d):
    meta = schema.load(d)
    mf = find_model_file(d)
    obs = load_model(os.path.join(d, mf))
    stats = [obj_stats(ob) for ob in obs]
    out = {
        "id": meta["id"], "file": mf,
        "objects": stats,
        "totals": {k: sum(s[k] for s in stats) for k in
                   ("verts", "edges", "faces", "quads", "tris", "ngons", "islands",
                    "boundary_edges", "non_manifold_edges", "degenerate_faces")},
        "pose_hint": pose_hint(stats),
        "pose_hint_basis": "HEURÍSTICA (largura/altura) — confirmar; meta.pose é que manda",
        "units": "UNKNOWN (bbox cru por objeto; escala do objeto registada)",
        "limitations_of_extraction": [
            "sem avaliação de modificadores (cage, não superfície final)",
            "materiais: só nomes (árvore de nodes não extraída ainda)",
            "armadura: só presença (hierarquia de ossos não extraída ainda)",
            "normais/UV: só presença e contagem",
        ],
    }
    p = os.path.join(d, "extraction.json")
    json.dump(out, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("INSPECT", json.dumps({"id": meta["id"], "totals": out["totals"],
                                 "pose_hint": out["pose_hint"]}))
    return out


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    targets = []
    if args and args[0] == "all":
        for sex in ("female", "male"):
            for st in os.listdir(os.path.join(LIB, sex)):
                for part in os.listdir(os.path.join(LIB, sex, st)):
                    base = os.path.join(LIB, sex, st, part)
                    for mid in os.listdir(base):
                        if os.path.exists(os.path.join(base, mid, "meta.json")):
                            targets.append(os.path.join(base, mid))
    else:
        targets = args
    for t in targets:
        inspect_dir(t)


if __name__ == "__main__":
    main()
