# -*- coding: utf-8 -*-
"""T-TORSO — validação de ORIENTAÇÃO por medição (nunca pelo eixo do ficheiro).

Para cada modelo: mede AMBOS os flips com o instrumento comum e reporta os
diagnósticos sagitais. Decisão: a orientação CORRECTA tem concavidade lombar
plausível (≈ banda das refs) e NÁDEGAS atrás das costas torácicas; a
invertida dá lombar ~0 com a barriga atrás (validado na real005,
TORSO_STUDY_01 §7.2). Frente dos homens (sem mamas): o mesmo teste sagital.

Uso: python tools/refstudy/torso_orient.py [nomes...]
"""
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _paths import WORK  # noqa: E402

import numpy as np  # noqa: E402
from measure import analyse  # noqa: E402


def diag_from(r):
    P = r["prof"]
    S = 1700.0
    C = [p for p in P if p["center"] and not math.isnan(p.get("mid_back", float("nan")))]
    B = np.array([(p["z"], p["mid_back"], p["mid_front"]) for p in C])
    cr = max(p["z"] for p in P if not p["center"] and p["z"] < 0.62 * S)
    lo = cr / S + 0.005
    m = {}
    s = B[(B[:, 0] >= 0.70 * S) & (B[:, 0] <= 0.82 * S)]
    t = s[np.argmin(s[:, 1])] if len(s) else (float("nan"),) * 3
    s = B[(B[:, 0] >= lo * S) & (B[:, 0] <= 0.58 * S)]
    b = s[np.argmin(s[:, 1])] if len(s) else (float("nan"),) * 3
    seg = B[(B[:, 0] < t[0]) & (B[:, 0] > b[0])]
    if len(seg) > 3:
        yline = b[1] + (seg[:, 0] - b[0]) / (t[0] - b[0]) * (t[1] - b[1])
        m["lombar"] = float(np.max(seg[:, 1] - yline))
    else:
        m["lombar"] = float("nan")
    m["nadega_vs_toracica"] = float(t[1] - b[1])
    ch = B[(B[:, 0] >= 0.70 * S) & (B[:, 0] <= 0.78 * S)]
    be = B[(B[:, 0] >= 0.58 * S) & (B[:, 0] <= 0.66 * S)]
    if len(ch) and len(be):
        m["frente_peito_menos_barriga"] = float(ch[:, 2].max() - be[:, 2].max())
    hd = B[(B[:, 0] >= 0.88 * S)]
    if len(hd):
        m["cabeca_extensao_frente"] = float(hd[:, 2].max() - hd[:, 2].min())
    return m


def diag(name, flip, drop=()):
    return diag_from(analyse(name, drop_labels=drop, flip_y=flip))


if __name__ == "__main__":
    names = sys.argv[1:] or ["lucia", "ff11", "animeF", "whitewalker",
                             "femalebase", "femalechar"]
    for n in names:
        dp = os.path.join(WORK, f"drop_{n}.json")
        drop = tuple(json.load(open(dp))["drop_labels"]) if os.path.exists(dp) else ()
        try:
            for flip in (False, True):
                m = diag(n, flip, drop)
                print(f"ORIENT {n} flip={int(flip)}: " +
                      " ".join(f"{k}={v:.1f}" for k, v in m.items()))
        except Exception as e:
            print(f"ORIENT {n}: ERRO {e!r}")
