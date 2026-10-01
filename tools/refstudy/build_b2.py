# -*- coding: utf-8 -*-
"""Build swB2 (protótipo C2 · mama estruturada) + swN0 (parede nula) + swV0.

MANDATO RND · docs/BREAST_C2_01.md.  HCG_BREAST2=1 substitui o bump gaussiano
pelo campo estruturado `_structured_breast` (body.py) e densifica o cage
(`_densify_front`).  O controlo N0 usa HCG_BREAST amp 0 SEM breast2 (parede
do H-TT2-parcial).  V0 = mama gaussiana H-TT1 por defeito (sobre a anatomia
actual — o V0 do sweep era pré-fs/bs, digest 8c6f568c, não comparável).

Uso: python3 tools/headless_blender.py run tools/refstudy/build_b2.py
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import bpy  # noqa: E402

from torso_refs import _eval, _save  # noqa: E402


def build(name, breast, breast2):
    os.environ["HCG_HEAD"] = "faceB2"
    os.environ["HCG_NECK"] = "N1"
    os.environ["HCG_T1_AMP"] = "1"
    if breast is None:
        os.environ.pop("HCG_BREAST", None)
    else:
        os.environ["HCG_BREAST"] = json.dumps(breast)
    if breast2:
        os.environ["HCG_BREAST2"] = "1"
    else:
        os.environ.pop("HCG_BREAST2", None)
    import human_generator as hcg
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob, do_unlink=True)
    r = hcg.generate_character("realistic_female", seed=42, name=name,
                               write_blend=False, save_report=False)
    V, T = _eval([o for o in bpy.data.objects if o.type == "MESH"])
    _save(name, V, T, drop_rule=True)
    print(f"BUILD {name}: v={len(V)} digest={r.digest}")
    return r.digest


if __name__ == "__main__":
    d_n0 = build("swN0", {"amp": 0.0}, False)
    d_b2 = build("swB2", {"amp": 0.0}, True)
    # V0 re-build: mama gaussiana H-TT1 SOBRE a anatomia actual (H-TT2-parcial
    # fs/bs waist/navel) — o swV0 do sweep era pré-fs/bs (digest 8c6f568c),
    # logo não comparável com N0/B2 coluna-a-coluna.
    d_v0 = build("swV0", None, False)
    print("OK", d_n0, d_b2, d_v0)
