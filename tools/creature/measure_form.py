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
import struct
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
    "F6_gemeo_tendao":    (1.4, 1e9),     # barriga do gémeo / tendão de Aquiles
    "F6b_ante_punho":     (1.5, 1e9),     # barriga flexora / tendão do punho
    "F6c_joelho_coxa":    (0.50, 0.95),   # joelho nunca + largo que o quadríceps
    "F8_olho_assente_mm": (17, 25),
    "T1_torso_px_m":      (1000, 1e9),
    "T2_membros_px_m":    (1000, 1e9),
    "T3_uniformidade":    (0, 2.5),
    # ---- v3.4 SOLDADURA (gate: "ombros = vulcões/canudos")
    "S1a_raiz_braco_dentro": (20, 20),
    "S1b_raiz_braco_r_mm":   (0, 34),
    "S2a_raiz_coxa_dentro":  (20, 20),
    "S2b_raiz_coxa_r_mm":    (0, 46),
    "S3_colar_mind_z":       (1460, 1500),
    "S4_dr_anel_mm":         (0, 12),
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

    # ---- anatómicos v3.3/v3.4: anéis por LINHA ÓSSEA (f = projecção
    #      nos pivôs do rig — robusto à densificação; 13 estações × 20)
    rigj = json.load(open(os.path.join(ROOT, "site", "models", "stalker2_rig.json")))["rig"]
    # pivôs: METROS no frame glTF [−x,z,y] → build frame, ×1000 → MM
    # (read_meshes devolve mm; sem a escala o f era lixo — janelas vazias)
    PVR = {r["name"]: np.array([-r["pivot"][0], r["pivot"][2], r["pivot"][1]], float) * 1000.0
           for r in rigj}

    def f_rings(part, A, B, n=20, nst=13):
        V = M[part][:nst * n]
        out = []
        for i in range(nst):
            rg = V[i * n:(i + 1) * n]
            c = rg.mean(0)
            ab = B - A
            f = float((c - A) @ ab / (ab @ ab))
            out.append((f, float(np.linalg.norm(rg - c, axis=1).mean())))
        return out

    def mrf(part, A, B, f0, f1):
        return [r for f, r in f_rings(part, A, B) if f0 <= f <= f1]

    f5, f6, f6b, f6c = [], [], [], []
    S4max = 0.0
    for sd in ("R", "L"):
        sh, el, wr = PVR[f"upperarm_{sd}"], PVR[f"forearm_{sd}"], PVR[f"hand_{sd}"]
        hip, kn, an = PVR[f"thigh_{sd}"], PVR[f"shin_{sd}"], PVR[f"foot_{sd}"]
        uaR = f_rings(f"upperarm_{sd}", sh, el)
        faR = f_rings(f"forearm_{sd}", el, wr)
        thR = f_rings(f"thigh_{sd}", hip, kn)
        shR = f_rings(f"shin_{sd}", kn, an)
        # F5 redefinido (§v3.4): raio MÁX do braço na janela deltoideu
        # (a raiz agora é TENDÃO enterrado — não conta p/ o contraste)
        f5.append(max(r for f, r in uaR if -0.12 <= f <= 0.45) /
                  np.mean(mrf(f"forearm_{sd}", el, wr, 0.3, 0.6)))
        f6.append(np.mean(mrf(f"shin_{sd}", kn, an, 0.25, 0.45)) /
                  np.mean(mrf(f"shin_{sd}", kn, an, 0.9, 1.05)))
        f6b.append(np.mean(mrf(f"forearm_{sd}", el, wr, -0.05, 0.15)) /
                   np.mean(mrf(f"forearm_{sd}", el, wr, 0.9, 1.05)))
        f6c.append(np.mean(mrf(f"shin_{sd}", kn, an, -0.05, 0.10)) /
                   np.mean(mrf(f"thigh_{sd}", hip, kn, 0.25, 0.45)))
        for ringset in (uaR, faR, thR, shR):
            rs = [r for _, r in ringset]
            S4max = max(S4max, max(abs(rs[i + 1] - rs[i]) for i in range(len(rs) - 1)))
    R["F5_braco_contraste"] = float(np.mean(f5))
    R["F6_gemeo_tendao"] = float(np.mean(f6))
    R["F6b_ante_punho"] = float(np.mean(f6b))
    R["F6c_joelho_coxa"] = float(np.mean(f6c))
    R["S4_dr_anel_mm"] = float(S4max)

    # ---- S1/S2: anel RAIZ (primeiros 20 verts) DENTRO do torso
    _, IDX = read_meshes(os.path.join(ROOT, "site", "models", "stalker2_smooth.glb"),
                         with_index=True)
    TT, TI = M["torso"], IDX["torso"]

    # ray-cast por PARIDADE (Möller–Trumbore, contagem ímpar = dentro):
    # independente do winding — a tampa inferior do torso tem winding
    # invertido (o teste pelo normal do triângulo mais próximo marcava
    # o INTERIOR da pelvis como 'fora')
    _A = TT[TI[:, 0]]
    _B = TT[TI[:, 1]]
    _C = TT[TI[:, 2]]
    _E1, _E2 = _B - _A, _C - _A
    _D = np.array([1.0, 0.0131, 0.0071])
    _D = _D / np.linalg.norm(_D)
    _H = np.cross(_D, _E2)
    _DET = (_E1 * _H).sum(1)
    _OK = np.abs(_DET) > 1e-9
    _F = np.zeros_like(_DET)
    _F[_OK] = 1.0 / _DET[_OK]

    def inside(p):
        s_ = p - _A
        u = (s_ * _H).sum(1) * _F
        q_ = np.cross(s_, _E1)
        v = (_D * q_).sum(1) * _F
        t = (_E2 * q_).sum(1) * _F
        hit = _OK & (u >= 0) & (u <= 1) & (v >= 0) & (u + v <= 1) & (t > 1e-6)
        return float(hit.sum() % 2 == 1)

    R["S1a_raiz_braco_dentro"] = float(sum(inside(v) for v in M["upperarm_R"][:20]))
    R["S1b_raiz_braco_r_mm"] = float(np.linalg.norm(
        M["upperarm_R"][:20] - M["upperarm_R"][:20].mean(0), axis=1).mean())
    R["S2a_raiz_coxa_dentro"] = float(sum(inside(v) for v in M["thigh_R"][:20]))
    R["S2b_raiz_coxa_r_mm"] = float(np.linalg.norm(
        M["thigh_R"][:20] - M["thigh_R"][:20].mean(0), axis=1).mean())
    R["S3_colar_mind_z"] = float(M["head"][:, 2].min())

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

    # ---- T1-T3: densidade de texel (UVs do GLB; tile=250mm, tex 512px)
    GLB = os.path.join(ROOT, "site", "models", "stalker2_smooth.glb")
    b = open(GLB, "rb").read()
    jlen = struct.unpack("<I", b[12:16])[0]
    js = json.loads(b[20:20 + jlen])
    binOff = 20 + jlen
    binOff += (4 - (binOff % 4)) % 4
    blen = struct.unpack("<I", b[binOff:binOff + 4])[0]
    BIN = b[binOff + 8:binOff + 8 + blen]
    UVS = {}
    for m in js["meshes"]:
        pr = m["primitives"][0]
        if "TEXCOORD_0" not in pr["attributes"]:
            continue
        ai = pr["attributes"]["TEXCOORD_0"]
        a = js["accessors"][ai]
        v = js["bufferViews"][a["bufferView"]]
        o0 = v["byteOffset"] + (a.get("byteOffset") or 0)
        UVS[m["name"]] = np.frombuffer(BIN[o0:o0 + a["count"] * 8], np.float32).reshape(-1, 2)
    rigj = json.load(open(os.path.join(ROOT, "site", "models", "stalker2_rig.json")))["rig"]
    # pivôs: METROS no frame glTF [−x, z, y] (comprimentos ósseos T1/T2)
    PVR = {r["name"]: np.array([-r["pivot"][0], r["pivot"][2], r["pivot"][1]], float)
           for r in rigj}
    dens = {}
    tv = UVS["torso"][:, 1]
    dens["torso"] = 512.0 * (tv.max() - tv.min()) / ((T[:, 2].max() - T[:, 2].min()) / 1000.0)
    for s in ("R", "L"):
        for part, A, B in ((f"upperarm_{s}", "upperarm_" + s, "forearm_" + s),
                           (f"forearm_{s}", "forearm_" + s, "hand_" + s),
                           (f"thigh_{s}", "thigh_" + s, "shin_" + s),
                           (f"shin_{s}", "shin_" + s, "foot_" + s)):
            vv = UVS[part][:, 1]
            Lb = np.linalg.norm(PVR[B] - PVR[A])
            dens[part] = 512.0 * (vv.max() - vv.min()) / Lb
    R["T1_torso_px_m"] = float(dens["torso"])
    R["T2_membros_px_m"] = float(min(v for k, v in dens.items() if k != "torso"))
    R["T3_uniformidade"] = float(max(dens.values()) / min(dens.values()))

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
