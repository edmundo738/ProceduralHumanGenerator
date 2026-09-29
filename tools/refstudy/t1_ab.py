# -*- coding: utf-8 -*-
"""T1 — instrumento A/B do campo da curva sagital em S (§7.2 TORSO_STUDY_01).

Gera a personagem pela API pública com o campo LIGADO (amp1, omissão) e
DESLIGADO (amp0, ``HCG_T1_AMP=0``) — MESMA topologia (a subdivisão de anéis é
independente do campo) — avalia o corpo com subsurf nível 1 (a medição do
estudo mede o subsurf: cristas estreitas perdem amplitude no Catmull-Clark)
e escreve ``raw_amp{0,1}.npz`` + ``lab_amp{0,1}.npy`` + ``drop_amp{0,1}.json``
no WORK do refstudy.  Depois:

    python tools/refstudy/measure.py amp1 "$(cat out/refstudy/drop_amp1.json)"
    python tools/refstudy/measure.py amp0 "$(cat out/refstudy/drop_amp0.json)"
    python tools/refstudy/t1_cmp.py

A comparação correta é amp0 vs amp1 (amp0 vs baseline mistura artefactos de
amostragem dos novos anéis — medido, §7.2).
"""
import json
import os
import sys

sys.path.insert(0, os.getcwd())
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _paths import WORK  # noqa: E402

import numpy as np  # noqa: E402
import geom  # noqa: E402

os.environ["HCG_HEAD"] = "faceB2"
os.environ["HCG_NECK"] = "N1"

import bpy  # noqa: E402
import human_generator as hcg  # noqa: E402


def evaluated_mesh(subsurf_max=1):
    """(V, T) mundiais de TODOS os objectos MESH, subsurf limitado (refload._eval)."""
    dg = bpy.context.evaluated_depsgraph_get()
    V, T, off = [], [], 0
    for ob in (o for o in bpy.data.objects if o.type == "MESH"):
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


def main():
    for amp in (1, 0):
        for ob in list(bpy.data.objects):      # cena anterior (arranque + amp anterior) fora
            bpy.data.objects.remove(ob, do_unlink=True)
        os.environ["HCG_T1_AMP"] = str(amp)
        r = hcg.generate_character("realistic_female", seed=42, name=f"t1_amp{amp}",
                                   write_blend=False, save_report=False)
        V, T = evaluated_mesh(subsurf_max=1)
        lab = geom.components(V, T)
        # cascas a excluir (braços/mãos/dedos) — mesma regra do comps.py
        drop = [int(c) for c in range(lab.max() + 1)
                if np.abs(V[lab == c][:, 0]).min() > 0.07
                and V[lab == c][:, 2].min() > 0.6 and V[lab == c][:, 2].max() < 1.45]
        np.savez(os.path.join(WORK, f"raw_amp{amp}.npz"), V=V, T=T)
        np.save(os.path.join(WORK, f"lab_amp{amp}.npy"), lab)
        json.dump({"drop_labels": drop}, open(os.path.join(WORK, f"drop_amp{amp}.json"), "w"))
        print(f"GEN amp{amp} digest={r.digest} verts={r.build.verts} faces={r.build.faces} "
              f"mesh_v={len(V)} tris={len(T)} comps={lab.max() + 1} drop={len(drop)}")


if __name__ == "__main__":
    main()
