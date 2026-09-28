"""Parâmetros do olho (medidos): globo (globe.json) + fenda (marcos médios) em coords (H, V)."""
import os, sys, json, math
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, ROOT); sys.path.insert(0, HERE)
from human_generator.generators import face_fields as FF
from face_target import OUT, CENTRE


def hv(p):
    v = np.array(p, float) - CENTRE; u = v / np.linalg.norm(v)
    H, Y, V, X = FF.coords(np, *u)
    return float(H), float(V)


def params(T0=0.9, T1=0.35, DZ=7.0, DZl=5.0, GAP=1.2):
    J = json.load(open(os.path.join(OUT, "face_landmarks.json")))
    L = J["mean"]
    G = json.load(open(os.path.join(OUT, "globe.json")))["mean_R12.5"]
    en, ex, ps, pi = (hv(L[k + "_L"]) for k in ("en", "ex", "ps", "pi"))
    dx, dz = ex[0] - en[0], ex[1] - en[1]; Lc = math.hypot(dx, dz); tx, tz = dx / Lc, dz / Lc
    def tn(p):
        ph, pv = p[0] - en[0], p[1] - en[1]
        return (ph * tx + pv * tz) / Lc, -ph * tz + pv * tx
    tu, nu = tn(ps); tl, nl = tn(pi)
    # altura da fenda: femalebase (19.1 mm, ≈ 2× a norma de Farkas ~10.4 mm) é tratada
    # como outlier SÓ nesta medida (o seu laço inclui o rebordo do sulco palpebral —
    # INFERRED); altura = média de bodytopo e femalechar, forma (picos) da média de 3
    hts = {n: J["refs"][n]["ps_L"][2] - J["refs"][n]["pi_L"][2] for n in J["refs"]}
    k_h = np.mean([hts["bodytopo"], hts["femalechar"]]) / np.mean(list(hts.values()))
    nu, nl = nu * k_h, nl * k_h
    print("alturas da fenda (mm)", {k: round(v, 1) for k, v in hts.items()}, "fator", round(k_h, 3))
    gu = math.log(0.5) / math.log(tu); gl = math.log(0.5) / math.log(tl)
    E = {"en": [round(en[0], 3), round(en[1], 3)], "ex": [round(ex[0], 3), round(ex[1], 3)],
         "Hu": round(nu, 3), "Hl": round(-nl, 3), "gu": round(gu, 4), "gl": round(gl, 4),
         "G": [round(g, 3) for g in G], "RL": 12.5, "T0": T0, "T1": T1, "DZ": DZ, "DZl": DZl, "GAP": GAP}
    return E


if __name__ == "__main__":
    E = params(); print(json.dumps(E))
    json.dump(E, open(os.path.join(OUT, "eye_params.json"), "w"))
