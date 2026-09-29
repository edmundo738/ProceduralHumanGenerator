# -*- coding: utf-8 -*-
"""TORSO TRANSITIONS 01 — continuidade das transições: refs vs nós.

Pergunta do dono (gate TORSO B): a geometria denuncia a construção procedural
(ondas de estações, mamas "aplicadas", lombas de estrada). Este instrumento
MEDE a continuidade das 4 curvas de perfil (frente, costas, largura,
profundidade da linha média) por REGIÃO/JUNÇÃO:

  1. nº de extremos locais (picos+vales com prominence) por região —
     "ondas": refs = poucos e largos; nós = muitos se houver ondas de estação;
  2. energia de curvatura (média |Δ²| por 25 mm) por região;
  3. correlação dos extremos NOSSOS com as cotas das estações;
  4. asimetria da mama (transição superior vs polo inferior);
  5. sulco glúteo (dobragem inferior do contorno posterior);
  6. rampa pescoço→ombro (largura): parabólica vs complexa.

Instrumento COMUM: mesmos parâmetros para refs e nós (grelha 5 mm, suavização
janela 3 fatias = 15 mm, prominence 2 mm, distância 20 mm). Saídas:
docs/head_phaseA/torso_transitions.png + out/refstudy/transitions.json.
"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from _paths import WORK  # noqa: E402

import numpy as np
from scipy.signal import find_peaks

ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
DOCS = os.path.join(ROOT, "docs", "head_phaseA")
S = 1700.0
REFS = ["femalebase", "femalechar", "bodytopo", "real005", "animeF"]
OURS = "ours"

# regiões/junções (fracções da estatura) — curva analisada
REGIONS = [
    ("R1 pescoço_base→clavícula*", 0.800, 0.860, "width"),
    ("R2 clavícula→ombro/axila*", 0.740, 0.812, "width"),
    ("R3 tórax (caixa)*", 0.680, 0.750, "width"),
    ("R4 mama (frente)", 0.680, 0.780, "front"),
    ("R5 mama→abdómen (epigástrio)", 0.580, 0.700, "front"),
    ("R6 cintura (largura)", 0.600, 0.660, "width"),
    ("R7 anca (largura)*", 0.460, 0.580, "width"),
    ("R8 costas tórax/escápula", 0.700, 0.800, "back"),
    ("R9 lombar", 0.550, 0.680, "back"),
    ("R10 sacro→glúteo→coxa", 0.400, 0.560, "back"),
]
# estações do tronco (fracções; anatomy.py TORSO B) para correlação
STATIONS = {"hip": 0.530, "hip_flare": 0.566, "navel": 0.602, "waist": 0.635,
            "inframammary": 0.720, "bust": 0.734, "cifose": 0.764,
            "jugulum": 0.795, "deltoid_line": 0.812}

FIELD = {"front": "front", "back": "mid_back", "width": "width", "depth": "depth"}


def load_curve(name, field):
    P = json.load(open(os.path.join(WORK, f"prof_{name}.json")))["prof"]
    rows = [(p["z"], p[field]) for p in P
            if p.get("center") and p.get(field) is not None
            and not (isinstance(p.get(field), float) and math.isnan(p.get(field)))]
    rows.sort()
    z = np.array([r[0] for r in rows]); v = np.array([r[1] for r in rows])
    # grelha uniforme 5 mm
    zg = np.arange(z.min(), z.max(), 5.0)
    vg = np.interp(zg, z, v)
    # suavização janela 3 (15 mm) — igual para todos
    k = np.ones(3) / 3.0
    return zg, np.convolve(vg, k, mode="same")


def extrema(z, v, z0, z1, prom=2.0, dist=4):
    m = (z >= z0 * S) & (z <= z1 * S)
    zz, vv = z[m], v[m]
    if len(vv) < 6:
        return []
    out = []
    for sgn in (1, -1):
        pk, props = find_peaks(sgn * vv, prominence=prom, distance=dist)
        for i, p in enumerate(pk):
            out.append((float(zz[p]), float(vv[p]), props["prominences"][i]))
    out.sort()
    return out


def wiggle(z, v, z0, z1):
    """média |Δ²| (mm) por fatia de 5 mm dentro da região."""
    m = (z >= z0 * S) & (z <= z1 * S)
    vv = v[m]
    if len(vv) < 5:
        return float("nan")
    d2 = vv[2:] - 2 * vv[1:-1] + vv[:-2]
    return float(np.mean(np.abs(d2)))


def main():
    os.makedirs(DOCS, exist_ok=True)
    curves = {}
    for n in REFS + [OURS]:
        curves[n] = {f: load_curve(n, FIELD[f]) for f in ("front", "back", "width", "depth")}

    res = {"regions": {}, "breast": {}, "glute": {}, "neck_shoulder": {}}
    print("* largura de refs em T-pose inclui braços nos bandos do ombro — ler ESTRUTURA (extremos/wiggle), não absolutos")
    print(f"{'região':34s} {'curva':6s} {'ext refs (med,min-max)':>22s} {'ext nós':>8s} {'wig refs':>9s} {'wig nós':>8s}")
    for label, z0, z1, curve in REGIONS:
        key = f"{label} [{curve}]"
        cnt_refs, wig_refs = [], []
        for n in REFS:
            z, v = curves[n][curve]
            cnt_refs.append(len(extrema(z, v, z0, z1)))
            wig_refs.append(wiggle(z, v, z0, z1))
        z, v = curves[OURS][curve]
        ext = extrema(z, v, z0, z1)
        w = wiggle(z, v, z0, z1)
        res["regions"][key] = {
            "refs_extrema_counts": cnt_refs,
            "refs_extrema_median": float(np.median(cnt_refs)),
            "ours_extrema": [(round(e[0]), round(e[1], 1), round(e[2], 1)) for e in ext],
            "refs_wiggle_median": float(np.median(wig_refs)),
            "ours_wiggle": w,
        }
        print(f"{label:34s} {curve:6s} {np.median(cnt_refs):5.0f} [{min(cnt_refs)}-{max(cnt_refs)}]"
              f" {'':>{max(0, 6 - len(str(max(cnt_refs))))}} {len(ext):8d} {np.median(wig_refs):9.2f} {w:8.2f}")

    # correlação dos extremos nossos com estações (todas as regiões, curvas todas)
    near = []
    for label, z0, z1, curve in REGIONS:
        z, v = curves[OURS][curve]
        for ez, ev, prom in extrema(z, v, z0, z1):
            best = min(STATIONS.items(), key=lambda kv: abs(kv[1] * S - ez))
            gap = best[1] * S - ez
            if abs(gap) <= 18:
                near.append((label.split()[0], curve, round(ez), best[0], round(gap)))
    res["ours_extrema_near_stations"] = near
    print(f"\nextremos NOSSOS a ≤18 mm de uma estação: {len(near)}/{sum(len(res['regions'][k]['ours_extrema']) for k in res['regions'])}")
    for row in near:
        print("   ", row)

    # ---- mama: assimetria superior/inferior.  Ápice procurado SÓ na banda
    # mamária (0.69–0.76); referência acima = mín da frente em 0.77–0.80
    # (parede alta); referência abaixo = mín em 0.62–0.68 (submamária/epigástrio).
    def breast_asym(n):
        z, v = curves[n]["front"]
        band = (z >= 0.60 * S) & (z <= 0.80 * S)
        zz, vv = z[band], v[band]
        m_apex = (zz >= 0.69 * S) & (zz <= 0.76 * S)
        if not m_apex.any():
            return None
        i = int(np.argmax(np.where(m_apex, vv, -1e9)))
        apex, va = zz[i], vv[i]
        hi_band = (zz > 0.77 * S) & (zz < 0.80 * S)
        lo_band = (zz > 0.62 * S) & (zz < 0.68 * S)
        if not hi_band.any() or not lo_band.any():
            return None
        ref_hi = float(vv[hi_band].min())
        ref_lo = float(vv[lo_band].min())
        if va <= max(ref_hi, ref_lo) + 4.0:
            return None  # sem mama discernível (ex. bodytopo)
        # meia-altura acima e abaixo (referências diferentes: parede alta vs submamária)
        half_up = ref_hi + (va - ref_hi) * 0.5
        half_dn = ref_lo + (va - ref_lo) * 0.5
        up = zz[i:][vv[i:] >= half_up]    # ACIMA do ápice (z maior)
        dn = zz[:i][vv[:i] >= half_dn]    # ABAIXO do ápice (z menor)
        if len(up) == 0 or len(dn) == 0:
            return None
        upper, lower = float(up.max() - apex), float(apex - dn.min())
        return {"upper": upper, "lower": lower,
                "ratio": upper / max(1e-9, lower), "apex_z": float(apex)}
    print("\nmama — transição superior / polo inferior (mm; ratio>1 = superior mais longa):")
    for n in REFS + [OURS]:
        r = breast_asym(n)
        if r:
            res["breast"][n] = r
            print(f"  {n:12s} ápice z={r['apex_z']:5.0f} sup={r['upper']:5.0f} inf={r['lower']:5.0f} ratio={r['ratio']:4.2f}")
        else:
            print(f"  {n:12s} (sem mama discernível na banda)")

    # ---- glúteo: a dobra inferior NÃO é mensurável na linha média (o plano
    # médio passa pelo sulco central/entre-coxas, não pelos lóbulos).  A forma
    # dos lóbulos vs centro já está no painel gluteal do torso_system (contorno
    # y(x) no ápice) e no P16.  Registo: instrumento de corte sagital LATERAL
    # (x=±55) fica como ferramenta da fase de implementação.

    # ---- pescoço→ombro: rampa da largura (parabólica vs complexa)
    def neck_shoulder(n):
        z, v = curves[n]["width"]
        m = (z >= 0.775 * S) & (z <= 0.86 * S)
        zz, vv = z[m], v[m]
        i = int(np.argmax(vv))
        w_max, z_max = vv[i], zz[i]
        w_neck = float(np.median(vv[zz > 0.845 * S]))
        # inclinação média da rampa (mm de largura por 100 mm de z)
        span = max(1e-9, (zz[-1] - z_max))
        slope = (w_max - w_neck) / span * 100.0
        ext = extrema(z, v, 0.775, 0.86)
        return {"w_neck": w_neck, "w_max": float(w_max), "z_max": float(z_max),
                "ramp_slope_mm_per_100mm": float(slope), "n_extrema": len(ext)}
    print("\npescoço→ombro (rampa da largura):")
    for n in REFS + [OURS]:
        r = neck_shoulder(n)
        res["neck_shoulder"][n] = r
        print(f"  {n:12s} pescoço={r['w_neck']:5.0f} ombro={r['w_max']:5.0f}@z={r['z_max']:.0f} "
              f"rampa={r['ramp_slope_mm_per_100mm']:5.0f} mm/100mm extremos={r['n_extrema']}")

    # ---- painel
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))
    for ax, curve, ttl in zip(axes.flat, ("front", "back", "width", "depth"),
                              ("frente (linha média)", "costas (linha média)",
                               "largura", "profundidade")):
        grid = np.arange(0.40 * S, 0.87 * S, 5.0)
        band = []
        for n in REFS:
            z, v = curves[n][curve]
            band.append(np.interp(grid, z, v))
        band = np.array(band)
        ax.fill_between(grid, band.min(0), band.max(0), color="#bbbbbb", alpha=.5, label="refs (min–máx)")
        ax.plot(grid, band.mean(0), color="#888888", lw=1, label="refs (média)")
        z, v = curves[OURS][curve]
        ax.plot(z, v, color="#d62728", lw=2.2, label="nós (TORSO B)")
        for label, z0, z1, cv in REGIONS:
            if cv == curve:
                for ez, ev, prom in extrema(z, v, z0, z1):
                    ax.plot(ez, ev, "o", color="#d62728", ms=5)
        for name, fz in STATIONS.items():
            ax.axvline(fz * S, color="#1f77b4", lw=.5, ls=":", alpha=.6)
        ax.set_title(ttl)
        ax.set_xlabel("z (mm @1700)")
        ax.set_ylabel("mm")
        ax.grid(alpha=.3)
        ax.legend(fontsize=8)
    fig.suptitle("TORSO TRANSITIONS — continuidade dos perfis: refs (banda) vs nós; pontos = extremos locais; "
                 "verticais = estações", fontsize=10)
    fig.tight_layout()
    out_png = os.path.join(DOCS, "torso_transitions.png")
    fig.savefig(out_png, dpi=110)
    json.dump(res, open(os.path.join(WORK, "transitions.json"), "w"), indent=1)
    print("\npainel →", out_png)
    print("dados  →", os.path.join(WORK, "transitions.json"))


if __name__ == "__main__":
    main()
