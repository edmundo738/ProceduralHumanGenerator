#!/usr/bin/env python3
"""INSTRUMENTO v3.2 — mede o RELEVO/FORMA do THE STALKER no GLB.

Spec F1–F8 (docs/CREATURE_SPEC_STALKER.md §v3.2 + refinamentos §v3.2.1,
declarados ANTES de medir). RELEVO ≠ TENDÊNCIA ≠ ELIPSE:
  - F1/F1b: perfil lateral r(z) por anel, DES-TENDENCIADO (±45mm);
  - F2/F3: LINHA DE SILHUETA costas y_back(z) des-tendenciada — a
    elipse (E1>E2) faz o polo ser o ponto +próximo: pole/flanco media
    elipse, não relevo;
  - F4: des-tendência ANGULAR por anel (±0.7rad) — a elipse produzia
    15-25mm de variação angular SEM escápula nenhuma;
  - F5/F6/F6b: anéis do TUBO por topologia (16/anel × 5 estações; a
    esfera de junção vem depois no merge — excluída);
  - F8: RECESSO do globo ocular (10 verts mais próximos da cabeça).
Saída: tabela + out/refstudy/stalker_form.json
"""
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)
from measure_stalker import read_meshes  # noqa: E402

SPEC = {
    "F1_costelas_n":      (5, 1e9),
    "F1b_costelas_amp":   (6, 30),
    "F2_espinha_mm":      (10, 1e9),
    "F3_vertebras_n":     (6, 1e9),
    "F4_escapula_mm":     (6, 1e9),
    "F5_braco_contraste": (1.45, 2.1),
    "F6_joelho_bojo":     (1.2, 1e9),
    "F6b_cotovelo_bojo":  (1.15, 1e9),
    "F8_olho_assente_mm": (17, 25),
}


def detrend_z(zs, ys, win=45.0, zmin=None, zmax=None):
    """Des-tendência por ÍNDICE de anel (±2 anéis): o espaçamento dos
    anéis varia 10-21mm — janela em mm era menor que o espaçamento na
    cintura e cada anel des-tendenciava contra si próprio (tudo 0.0)."""
    zs, ys = np.asarray(zs, float), np.asarray(ys, float)
    o = np.argsort(zs)
    zs, ys = zs[o], ys[o]
    selw = (zs >= (zmin if zmin is not None else -1e9)) & (zs <= (zmax if zmax is not None else 1e9))
    zw, yw = zs[selw], ys[selw]
    out = np.empty_like(yw)
    w = 2
    for i in range(len(yw)):
        lo, hi = max(0, i - w), min(len(yw), i + w + 1)
        out[i] = yw[i] - yw[lo:hi].mean()
    return zw, out


def n_maxima(zs, ys, z0, z1, min_amp=1.5):
    n = 0
    for i in range(1, len(zs) - 1):
        if z0 <= zs[i] <= z1 and ys[i] > ys[i - 1] and ys[i] > ys[i + 1] \
                and ys[i] - min(ys[i - 1], ys[i + 1]) > min_amp:
            n += 1
    return n


def main():
    M = read_meshes(os.path.join(ROOT, "site", "models", "stalker2_smooth.glb"))
    R = {}
    nr = 28
    T = M["torso"]

    # ---- anéis (topologia: 28 verts/anel sequenciais)
    rings = []
    for i in range(len(T) // nr):
        rg = T[i * nr:(i + 1) * nr]
        c = rg.mean(0)
        d = (rg - c) / np.linalg.norm(rg - c, axis=1)[:, None]
        r = np.linalg.norm(rg - c, axis=1)
        rings.append(dict(z=c[2], d=d, r=r, y=rg[:, 1]))

    # F1/F1b: perfil lateral (flancos), des-tendenciado
    lat = [(rg["z"], rg["r"][np.abs(rg["d"][:, 0]) > 0.5].mean()) for rg in rings
           if (np.abs(rg["d"][:, 0]) > 0.5).sum() >= 6]
    zl, ylat = detrend_z([z for z, _ in lat], [y for _, y in lat], 16, 1120, 1460)
    R["F1_costelas_n"] = int(n_maxima(zl, ylat, 1250, 1460, 1.5))
    sel = (zl >= 1250) & (zl <= 1460)
    R["F1b_costelas_amp"] = float(ylat[sel].max() - ylat[sel].min())

    # F2/F3: linha de silhueta costas (5 verts mais recuados por anel)
    back = []
    for rg in rings:
        idx = np.argsort(rg["y"])[:5]
        back.append((rg["z"], -rg["y"][idx].mean()))          # + = protrai
    zb, yback = detrend_z([z for z, _ in back], [y for _, y in back], 16, 1120, 1460)
    R["F2_espinha_mm"] = float(yback[(zb >= 1150) & (zb <= 1460)].max())
    R["F3_vertebras_n"] = int(n_maxima(zb, yback, 1150, 1450, 1.5))

    # F4: des-tendência ANGULAR por anel (sector costas, ±0.7 rad)
    best = 0.0
    for rg in rings:
        if not (1370 <= rg["z"] <= 1425):
            continue
        selb = rg["d"][:, 1] < -0.3
        if selb.sum() < 6:
            continue
        th = np.arctan2(rg["d"][selb, 0], -rg["d"][selb, 1])   # ângulo no sector
        rr = rg["r"][selb]
        o = np.argsort(th)
        th, rr = th[o], rr[o]
        for i in range(len(rr)):
            w = np.abs(th - th[i]) <= 0.7
            v = rr[i] - rr[w].mean()
            best = max(best, v)
    R["F4_escapula_mm"] = float(best)

    # ---- membros: anéis do TUBO (16 verts/anel × 5 estações)
    def tube_rings(part, n=16, nst=5):
        V = M[part][:n * nst]
        return [np.linalg.norm(V[i * n:(i + 1) * n] - V[i * n:(i + 1) * n].mean(0), axis=1).mean()
                for i in range(nst)]

    f5, f6, f6b = [], [], []
    for s in ("R", "L"):
        ua, fa, shn = tube_rings(f"upperarm_{s}"), tube_rings(f"forearm_{s}"), tube_rings(f"shin_{s}")
        f5.append(ua[0] / fa[2])
        f6.append(shn[0] / shn[2])
        f6b.append(fa[0] / fa[2])
    R["F5_braco_contraste"] = float(np.mean(f5))
    R["F6_joelho_bojo"] = float(np.mean(f6))
    R["F6b_cotovelo_bojo"] = float(np.mean(f6b))

    # ---- F8: assentamento do olho = distância à SUPERFÍCIE (mínimo
    #      sobre TRIÂNGULOS da cabeça; mean10-de-verts era artefacto de
    #      densidade da malha — declarado §v3.2.3)
    _, IDX = read_meshes(os.path.join(ROOT, "site", "models", "stalker2_smooth.glb"),
                         with_index=True)
    HF, HI = M["head"], IDX["head"]

    def surf_dist(e):
        best = 1e9
        for tri in HI:
            a, b_, c_ = HF[tri[0]], HF[tri[1]], HF[tri[2]]
            ab, ac = b_ - a, c_ - a
            ap = e - a
            d00, d01, d11 = ab @ ab, ab @ ac, ac @ ac
            apd0, apd1 = ap @ ab, ap @ ac
            den = d00 * d11 - d01 * d01
            v = (d11 * apd0 - d01 * apd1) / den if abs(den) > 1e-12 else 0.0
            w = (d00 * apd1 - d01 * apd0) / den if abs(den) > 1e-12 else 0.0
            v, w = max(0.0, v), max(0.0, w)
            if v + w > 1.0:
                v, w = v / (v + w), w / (v + w)
            p = a + v * ab + w * ac
            best = min(best, np.linalg.norm(e - p))
        return best

    rec = [surf_dist(M["eye_" + s].mean(0)) for s in ("R", "L")]
    R["F8_olho_assente_mm"] = float(np.mean(rec))

    # ---- veredictos
    nfail = 0
    print("métrica                       valor   banda            veredicto")
    for k, (lo, hi) in SPEC.items():
        v = R[k]
        ok = lo <= v <= hi
        nfail += 0 if ok else 1
        print(f"{k:28} {v:<8.1f} [{lo:g}..{hi:g}]   {'PASS' if ok else 'FAIL ✗'}")
    print(f"\n{nfail} FAIL de {len(SPEC)}")
    json.dump({"measures": {k: float(v) for k, v in R.items()},
               "n_fail": nfail, "spec": {k: list(v) for k, v in SPEC.items()}},
              open(os.path.join(ROOT, "out", "refstudy", "stalker_form.json"), "w"), indent=1)
    return nfail


if __name__ == "__main__":
    sys.exit(0 if main() == 0 else 1)
