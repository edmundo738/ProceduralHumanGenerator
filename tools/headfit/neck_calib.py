"""NECK N1 — calibração estação → anel final (automática, determinística).

Mede os anéis finais trunk.2/trunk.3 do builder no referencial da cabeça e
corrige NECK_N1 por alvo − medido (iterações de ponto fixo).  Imprime os valores
a registar em core/anatomy.py.  Alvos fixos no pré-registo (docs/NECK_N1_PREREG.md).
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
os.environ["HCG_NECK"] = "N1"; os.environ["HCG_MATHUTILS"] = "0"
from human_generator.core import anatomy as AN          # noqa: E402
from human_generator.pipeline.assemble import resolve_spec   # noqa: E402
from human_generator.generators.body import build_body  # noqa: E402

TARGET = {"st2": (48.0, 29.8, -71.2), "st3": (75.7, 16.8, -85.3)}
RING = {"st2": "trunk.2", "st3": "trunk.3"}


def measure():
    spec = resolve_spec(None, preset="realistic_female", seed=42); a = AN.Anatomy.from_spec(spec)
    k = 226.1 / a.h; y0 = -0.0398 * a.h; zc = a.z("chin")
    B = build_body(spec, a).builder
    out = {}
    for key, rn in RING.items():
        P = [B.verts[i] for i in B.rings[rn]]
        out[key] = (max(abs(p.x) for p in P) * k, (max(p.y for p in P) - y0) * k, (min(p.y for p in P) - y0) * k,
                    (sum(p.z for p in P) / len(P) - zc) * k)
    return out


if __name__ == "__main__":
    for it in range(4):
        m = measure()
        print(it, {k: tuple(round(v, 2) for v in m[k]) for k in m}, {k: AN.NECK_N1[k] for k in AN.NECK_N1})
        err = max(abs(m[k][j] - TARGET[k][j]) for k in m for j in range(3))
        if err < 0.2:
            break
        AN.NECK_N1 = {k: tuple(round(AN.NECK_N1[k][j] + (TARGET[k][j] - m[k][j]), 2) for j in range(3)) for k in m}
    print("FINAL NECK_N1 =", AN.NECK_N1, "erro máx", round(err, 3))
