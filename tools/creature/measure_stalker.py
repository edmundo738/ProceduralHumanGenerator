# -*- coding: utf-8 -*-
"""Mede o STALKER — do GLB de saída (nunca dos parâmetros de construção).

Lê site/models/stalker2_smooth.glb, converte para o frame nosso (z↑, mm) e
avalia cada métrica da CREATURE_SPEC_STALKER com PASS/FAIL. Escreve
out/refstudy/stalker_measure.json. Uso: python3 tools/creature/measure_stalker.py
"""
import json
import os
import struct
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
GLB = os.path.join(ROOT, "site", "models", "stalker2_smooth.glb")
OUT = os.path.join(ROOT, "out", "refstudy", "stalker_measure.json")

SPEC = {
    "M1_estatura":            (1750, 1900),
    "M2_punho_acima_joelho":  (-20, 60),
    "M3_alcance_braco_frac":  (0.50, 0.62),
    "M4_mao_mm":              (120, 180),
    "M5_cabeca_frac":         (0.115, 0.150),
    "M6_cabeca_graus":        (20, 40),
    "M7_corcunda_mm":         (45, 1e9),
    "M8_pescoco_retr_mm":     (60, 100),
    "M9_coxa_canela":         (0.90, 1.10),
    "M10_pe_mm":              (200, 280),
    "M11_ombro_frac":         (0.19, 0.26),
    "M12_cintura_frac":       (0.085, 0.115),
    "M13_anca_cintura":       (1.05, 1.30),
    "M14_interocular_mm":     (95, 115),
    "M15_olho_raio_mm":       (18, 24),
    "M16_mandibula_mm":       (90, 140),
    "M17_assim_bracos_mm":    (5, 25),
}


def read_meshes(path, with_index=False):
    b = open(path, "rb").read()
    clen, _ = struct.unpack("<II", b[12:20])
    js = json.loads(b[20:20 + clen])
    off = 20 + clen
    blen, _ = struct.unpack("<II", b[off:off + 8])
    buf = b[off + 8:off + 8 + blen]
    out, idx = {}, {}
    for mesh in js["meshes"]:
        pr = mesh["primitives"][0]
        aP = js["accessors"][pr["attributes"]["POSITION"]]
        v = js["bufferViews"][aP["bufferView"]]
        P = np.frombuffer(buf[v["byteOffset"]:v["byteOffset"] + v["byteLength"]],
                          np.float32).reshape(-1, 3).astype(np.float64) * 1000.0
        P = np.stack([-P[:, 0], P[:, 2], P[:, 1]], 1)     # glTF → nosso (z↑, +y frente)
        out[mesh["name"]] = P
        if with_index:
            aI = js["accessors"][pr["indices"]]
            vI = js["bufferViews"][aI["bufferView"]]
            dt = np.uint16 if aI["componentType"] == 5123 else np.uint32
            I = np.frombuffer(buf[vI["byteOffset"]:vI["byteOffset"] + vI["byteLength"]], dt)
            idx[mesh["name"]] = I.reshape(-1, 3).astype(np.int64)
    return (out, idx) if with_index else out


def pca_axis(V):
    C = V - V.mean(0)
    w, vecs = np.linalg.eigh(C.T @ C)
    ax = vecs[:, np.argmax(w)]
    t = C @ ax
    return ax, t.max() - t.min()


def zwidth(V, z0, z1):
    s = V[(V[:, 2] >= z0) & (V[:, 2] <= z1)]
    return (s[:, 0].max() - s[:, 0].min()) if len(s) else np.nan


def main():
    M = read_meshes(GLB)
    R = {}

    allv = np.vstack(list(M.values()))
    R["M1_estatura"] = float(allv[:, 2].max() - allv[:, 2].min())

    # ---- braços (por lado): fronteiras entre malhas adjacentes
    arm = {}
    for s in ("R", "L"):
        ua, fa, hd = M[f"upperarm_{s}"], M[f"forearm_{s}"], M[f"hand_{s}"]
        knee = (M[f"thigh_{s}"][:, 2].min() + M[f"shin_{s}"][:, 2].max()) / 2
        elbow = (ua[:, 2].min() + fa[:, 2].max()) / 2
        wrist = (fa[:, 2].min() + hd[:, 2].max()) / 2
        shoulder = ua[:, 2].max() - 70        # root sobe ~70mm acima do pivô (esfera junção)
        fingertip = hd[:, 2].min()
        arm[s] = dict(knee=knee, elbow=elbow, wrist=wrist, shoulder=shoulder,
                      reach=shoulder - fingertip,
                      mao=float(hd[:, 2].max() - hd[:, 2].min()))
    R["M2_punho_acima_joelho"] = float(np.mean([arm[s]["wrist"] - arm[s]["knee"] for s in ("R", "L")]))
    R["M3_alcance_braco_frac"] = float(np.mean([arm[s]["reach"] for s in ("R", "L")]) / R["M1_estatura"])
    R["M4_mao_mm"] = float(np.mean([arm[s]["mao"] for s in ("R", "L")]))
    R["M17_assim_bracos_mm"] = float(abs(arm["R"]["reach"] - arm["L"]["reach"]))

    # ---- cabeça
    ax, hl = pca_axis(M["head"])
    R["M5_cabeca_frac"] = float(hl / R["M1_estatura"])
    R["M6_cabeca_graus"] = float(np.degrees(np.arccos(abs(ax[2]) / np.linalg.norm(ax))))

    # ---- torso: CENTRÓIDES DE ANEL pela ordem dos vértices (o loft escreve
    #      n=28 verts por anel, sequencialmente — a topologia da malha É o
    #      dado; gavetas de z mentiriam com anéis inclinados)
    T = M["torso"]
    nr = 28
    rings = [T[i * nr:(i + 1) * nr].mean(0) for i in range(len(T) // nr)]
    dip = min(rings, key=lambda c: c[1])                   # anel do ombro (y mínimo)
    neck = rings[-1]                                        # anel do pescoço
    R["M7_corcunda_mm"] = float(neck[1] - dip[1])          # jut do pescoço após o dip
    R["M8_pescoco_retr_mm"] = float(M["head"][:, 2].min() - dip[2])  # base do crânio acima do dip

    # ---- pernas: comprimentos ÓSSEOS por pivôs do rig (stalker2_rig.json é
    #      saída do construtor e é o que o site usa para animar; extensões de
    #      malha inflariam com as esferas de junção)
    rigj = json.load(open(os.path.join(ROOT, "site", "models", "stalker2_rig.json")))["rig"]
    PV = {r["name"]: np.array(r["pivot"], float) for r in rigj}
    R["M9_coxa_canela"] = float(np.mean([
        np.linalg.norm(PV[f"thigh_{s}"] - PV[f"shin_{s}"]) /
        np.linalg.norm(PV[f"shin_{s}"] - PV[f"foot_{s}"]) for s in ("R", "L")]))
    R["M10_pe_mm"] = float(np.mean([
        M[f"foot_{s}"][:, 1].max() - M[f"foot_{s}"][:, 1].min() for s in ("R", "L")]))

    # ---- larguras (malha torso)
    S = R["M1_estatura"]
    ombro = zwidth(T, 1330, 1440)
    cintura = zwidth(T, 1190, 1260)
    anca = zwidth(T, 1080, 1180)
    R["M11_ombro_frac"] = float(ombro / S)
    R["M12_cintura_frac"] = float(cintura / S)
    R["M13_anca_cintura"] = float(anca / cintura)

    # ---- olhos / mandíbula
    eR, eL = M["eye_R"], M["eye_L"]
    R["M14_interocular_mm"] = float(np.linalg.norm(eR.mean(0) - eL.mean(0)))
    R["M15_olho_raio_mm"] = float(np.mean([
        (e.max(0) - e.min(0)).max() / 2 for e in (eR, eL)]))
    _, jl = pca_axis(M["mandible"])
    R["M16_mandibula_mm"] = float(jl)

    # ---- tabela
    print(f"{'métrica':26} {'valor':>10}   banda            veredicto")
    nfail = 0
    for k, (lo, hi) in SPEC.items():
        v = R[k]
        ok = lo <= v <= hi
        nfail += (not ok)
        print(f"{k:26} {v:10.1f}   [{lo:g}..{hi:g}]   {'PASS' if ok else 'FAIL ✗'}")
    print(f"\n{nfail} FAIL de {len(SPEC)}")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    V = {k: ("PASS" if (R[k] >= v[0] and R[k] <= v[1]) else "FAIL") for k, v in SPEC.items()}
    json.dump({"measures": R, "n_fail": nfail,
               "n_pass": {"pass": len(SPEC) - nfail, "total": len(SPEC)},
               "verdicts": V, "spec": {k: list(v) for k, v in SPEC.items()}},
              open(OUT, "w"), indent=1)
    return nfail


if __name__ == "__main__":
    sys.exit(0 if main() == 0 else 1)
