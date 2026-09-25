"""A2 — medição do canto mento–submental nas referências (malhas brutas, não SH).

Referencial HEAD STUDY 01 (mm@H226, z = 0 no mentón pela regra dos 45°,
y = 0 no centro glabela–opistocrânio).  Para cortes x = x0 (faixa ±2 mm):

* perfil inferior z_low(y) = z mínimo da superfície entre −30 e 15 mm (o
  submento visto de baixo), para y entre (cervical + 12) e (mentón − 4);
* recta ajustada z = a + b·(y − y_me): ``a`` = altura do plano submental sob o
  mentón (relativa ao mentón 45°), ``b`` = inclinação (b > 0: desce para trás);
* ``drop6`` = recuo da frente do perfil entre z = 0 e z = −6 (nitidez do canto).

Saída: out/headfit/chin_study.json + resumo impresso.  Nenhum vértice das
referências vai para o gerador: só estes números médios.
"""
import os
import sys
import json
import numpy as np

HERE = os.path.dirname(__file__)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "headstudy"))
import target as TG   # noqa: E402
import common as C    # noqa: E402

XS = (0.0, 10.0, 20.0)


def study(name):
    Vn, T, fs, fi, info = C.normalise(name)
    L, (zs, yf, yb, pts) = C.sagittal_landmarks(Vn, T)
    P = TG.surface_samples(Vn, T, per_mm2=3.0)
    y_me, (yc, zc) = L["menton"][0], L["cervical"]
    k = lambda z: int(np.argmin(np.abs(zs - z)))
    out = {"y_me": y_me, "cervical": [yc, zc], "drop6": float(yf[k(0)] - yf[k(-6)]),
           "drop3": float(yf[k(0)] - yf[k(-3)])}
    for x0 in XS:
        S = P[(np.abs(np.abs(P[:, 0]) - x0) < 2.0) & (P[:, 2] > -30) & (P[:, 2] < 15)]
        ys = np.arange(yc + 12, y_me - 4, 2.0)
        zl = []
        for y in ys:
            m = np.abs(S[:, 1] - y) < 1.0
            zl.append(S[m, 2].min() if m.sum() >= 3 else np.nan)
        zl = np.array(zl)
        g = np.isfinite(zl)
        if g.sum() < 4:
            out[f"x{int(x0)}"] = None
            continue
        b, a = np.polyfit(-(ys[g] - y_me), zl[g], 1)      # z = a + b·(y_me − y)
        out[f"x{int(x0)}"] = {"a": float(a), "slope_deg": float(np.degrees(np.arctan(-b))),
                              "resid": float(np.std(zl[g] - (a + b * -(ys[g] - y_me)))),
                              "n": int(g.sum())}
    return out


def main():
    res = {n: study(n) for n in TG.TARGET_SOURCES + ["oursA", "ours"]}
    for n, r in res.items():
        s = f"{n:11s} y_me {r['y_me']:5.1f} cerv ({r['cervical'][0]:5.1f},{r['cervical'][1]:6.1f}) drop3 {r['drop3']:5.1f} drop6 {r['drop6']:5.1f} |"
        for x0 in XS:
            q = r[f"x{int(x0)}"]
            s += f" x{int(x0)}: " + ("—" if q is None else f"a {q['a']:5.1f} desce {q['slope_deg']:5.1f}° ±{q['resid']:.1f}")
        print(s)
    refs = [res[n] for n in TG.TARGET_SOURCES]
    summ = {}
    for key in ("a", "slope_deg"):
        for x0 in XS:
            v = [r[f"x{int(x0)}"][key] for r in refs if r[f"x{int(x0)}"]]
            summ[f"{key}_x{int(x0)}"] = [float(np.mean(v)), float(np.std(v)), len(v)]
    summ["drop6"] = [float(np.mean([r["drop6"] for r in refs])), float(np.std([r["drop6"] for r in refs]))]
    print(json.dumps(summ, indent=1))
    os.makedirs(TG.OUT, exist_ok=True)
    json.dump({"per_source": res, "refs_mean": summ}, open(os.path.join(TG.OUT, "chin_study.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
