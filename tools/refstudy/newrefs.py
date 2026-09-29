# -*- coding: utf-8 -*-
"""Refs novas do povoamento da biblioteca (REF-F-REAL-005/006) → espaço do estudo.

REF-F-REAL-005 ``realistic_female_base_mesh__t-pose.glb`` (T-pose): mantém SÓ a
pele nua — objectos cujo material começa por ``Std_Skin`` (Arm+Leg+Head+Body =
14474 v; exclui cabelo, olhos, cílios, tearline, unhas, língua, roupa).
REF-F-REAL-006 ``realistic female.blend``: só o objecto principal MOLLY
(avaliado: MIRROR+SUBSURF ⇒ 26435 v).

Orientação: a decisão de ``flip_y`` é VALIDADA pela medição sagital (frente
errada ⇒ lombar ~4 com a barriga atrás; frente certa ⇒ lombar ~56 na banda
das refs e nádegas atrás).  Pés/nariz ficam como relatório de evidência —
o primário "pés" (artelhos ~170 mm vs calcanhar ~70) engana-se nesta malha
porque a banda do pé inclui a canela.
Escreve ``raw_real00X.npz``/``lab_real00X.npy``/``cfg_real00X.json`` (com o
``flip_y`` para o measure.py) e um relatório da orientação.  ``dg.update()``
antes de cada avaliação (determinismo).

Nota (exclusão declarada): real006 é ESTILIZADA (medição: hip 640 > p95+230,
lombar 1.4) — processada para o registo, EXCLUÍDA dos alvos do estudo.
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

R005 = "references/female/realistic/full_body/REF-F-REAL-005/realistic_female_base_mesh__t-pose.glb"
R006 = "references/female/realistic/full_body/REF-F-REAL-006/realistic female.blend"

# Decisão de orientação VALIDADA pela medição sagital (lombar 56.2 na banda das
# refs vs 4.0 invertida; nádegas atrás).  real006: frente já +Y (estilizada,
# processada só para o registo da exclusão).
FLIP = {"real005": True, "real006": False}


def _eval(objs):
    dg = bpy.context.evaluated_depsgraph_get()
    V, T, off = [], [], 0
    for ob in objs:
        for m in ob.modifiers:
            if m.type == "SUBSURF":
                m.levels = min(m.levels, 1)
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


def orient(V, tag):
    """Evidência geométrica (pés + nariz) — RELATÓRIO; a decisão é medida.

    A orientação correcta foi VALIDADA pela medição sagital (a invertida dá
    concavidade lombar ~4 com a barriga atrás; a correcta dá ~56, dentro da
    banda das refs, nádegas atrás).  O primário "pés" engana-se nesta malha:
    a banda z<16% inclui a canela, que enviesa o centróide.
    """
    z0, z1 = V[:, 2].min(), V[:, 2].max()
    h = z1 - z0
    foot = V[V[:, 2] < z0 + 0.16 * h]
    yc = foot[:, 1].mean()
    fwd = foot[:, 1].max() - yc
    back = yc - foot[:, 1].min()
    head = V[(V[:, 2] > z0 + 0.84 * h) & (V[:, 2] < z0 + 0.95 * h)]
    yhc = head[:, 1].mean()
    nose_plus = head[:, 1].max() - yhc > yhc - head[:, 1].min()
    print(f"ORIENT {tag}: evidência pés +Y {fwd * 1000:.0f} vs −Y {back * 1000:.0f} mm "
          f"(canela incluída — não conclusivo), nariz {'+Y' if nose_plus else '−Y'}; "
          f"decisão medida: flip_y={FLIP[tag]}")


def save(name, V, T, flip, note):
    lab = geom.components(V, T)
    np.savez(os.path.join(WORK, f"raw_{name}.npz"), V=V, T=T)
    np.save(os.path.join(WORK, f"lab_{name}.npy"), lab)
    json.dump({"flip_y": flip, "orient": note},
              open(os.path.join(WORK, f"cfg_{name}.json"), "w"))
    print(f"SAVE {name}: v={len(V)} tris={len(T)} comps={lab.max() + 1}")


def main():
    # real005 — pele nua (Std_Skin_*)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=R005)
    skin = [o for o in bpy.data.objects if o.type == "MESH"
            and any(m and m.name.startswith("Std_Skin") for m in o.data.materials)]
    V, T = _eval(skin)
    orient(V, "real005")
    save("real005", V, T, FLIP["real005"], "medida: lombar 56.2 ✓ banda refs")
    # real006 — só o MOLLY (avaliado)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.wm.open_mainfile(filepath=R006)
    V, T = _eval([bpy.data.objects["MOLLY"]])
    orient(V, "real006")
    save("real006", V, T, FLIP["real006"], "estilizada — excluída dos alvos")


if __name__ == "__main__":
    main()
