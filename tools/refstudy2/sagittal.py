"""REF STUDY 02 — perfil sagital: pontos de viragem, eixo de massa, base do pescoço.

Referencial: y = 0 no centro da canela a 0.12·S (média das duas pernas) — uma
"linha de prumo" aproximada, independente da caixa envolvente (que o H3/H2
mostrou deslocar-se com a nádega).  Depende da postura de cada malha: declarado.

Uso: HCG_REFSTUDY_WORK=out/rs2 python tools/refstudy2/sagittal.py [OUT_DIR]
"""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "refstudy")); sys.path.insert(0, HERE)
import numpy as np
from scipy.ndimage import gaussian_filter1d
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
import measure, shape
from _paths import WORK
OUT = sys.argv[1] if len(sys.argv) > 1 else "docs/ref_study_02"
C = {"ours": "#d62728", "femalebase": "#1f77b4", "femalechar": "#2ca02c", "bodytopo": "#9467bd"}
S = 1700.0


def shank_y(V, T, lab):
    g = measure.slice_grid(V, T, lab, 0.12 * S, (-320, 320), (-260, 260))
    iy, ix = np.nonzero(g)
    ya = -260 + (np.arange(g.shape[0]) + .5) * 2.0
    return float(ya[iy].mean())


def profile(name):
    V, T, lab = shape.normalised(name, shape.MODELS[name])
    y0 = shank_y(V, T, lab)
    rows = json.load(open(os.path.join(WORK, "shape.json")))[name]
    P = json.load(open(os.path.join(WORK, f"prof_{name}.json")))["prof"]
    # perfis na linha média do REF STUDY 01 (todos os cortes, incl. pescoço/cabeça)
    z = np.array([p["z"] for p in P if p.get("center") and not np.isnan(p.get("mid_back", np.nan))])
    mb = np.array([p["mid_back"] for p in P if p.get("center") and not np.isnan(p.get("mid_back", np.nan))])
    mf = np.array([p["mid_front"] for p in P if p.get("center") and not np.isnan(p.get("mid_back", np.nan))])
    # o prof_ do REF STUDY 01 está centrado pela caixa envolvente; re-referenciar à canela
    zc = np.array([r["z"] for r in rows]); cy = np.array([r["cy"] for r in rows])
    return dict(z=z, mb=mb - y0, mf=mf - y0, zc=zc, cy=cy - y0, y0=y0)


def smooth(y, s=2.0):
    return gaussian_filter1d(y, s)


def extremum(z, y, lo, hi, f):
    m = (z >= lo * S) & (z <= hi * S)
    i = f(y[m]); return float(z[m][i]), float(y[m][i])


def turning(pr):
    z, mb, mf = pr["z"], smooth(pr["mb"]), smooth(pr["mf"])
    t = {}
    t["thoracic_apex"] = extremum(z, mb, 0.68, 0.82, np.argmin)       # costas mais posteriores
    t["gluteal_apex"] = extremum(z, mb, 0.44, 0.58, np.argmin)
    zl, zh = t["gluteal_apex"][0], t["thoracic_apex"][0]
    m = (z > zl) & (z < zh)
    chord = t["gluteal_apex"][1] + (z[m] - zl) / (zh - zl) * (t["thoracic_apex"][1] - t["gluteal_apex"][1])
    k = np.argmax(mb[m] - chord)
    t["lumbar_deepest"] = (float(z[m][k]), float(mb[m][k])); t["lumbar_depth_vs_chord"] = float((mb[m] - chord)[k])
    t["bust_apex"] = extremum(z, mf, 0.68, 0.80, np.argmax)
    t["underbust"] = extremum(z, mf, 0.62, t["bust_apex"][0] / S, np.argmin)
    t["abdomen_low"] = extremum(z, mf, 0.52, 0.62, np.argmax)
    # prega glútea: abaixo do ápice glúteo, onde a curvatura (d2y/dz2) é máxima (virar para dentro)
    m2 = (z < zl) & (z > zl - 0.10 * S)
    d2 = np.gradient(np.gradient(mb, z), z)
    if m2.any():
        k2 = np.argmax(d2[m2]); t["gluteal_fold"] = (float(z[m2][k2]), float(mb[m2][k2]))
    # base do pescoço: coluna do pescoço à cota da largura mínima; desvio de 15 mm
    P = json.load(open(os.path.join(WORK, f"prof_{pr['name']}.json")))["prof"]
    neck = [p for p in P if p.get("center") and 0.80 * S <= p["z"] <= 0.875 * S]
    zn = min(neck, key=lambda p: p["width"])["z"]
    yf = np.interp(zn, z, mf); yb = np.interp(zn, z, mb)
    below = z < zn
    zf = z[below & (mf > yf + 15)]; zb = z[below & (mb < yb - 15)]
    t["neck_z"] = float(zn)
    t["neckbase_front_z"] = float(zf.max()) if len(zf) else np.nan
    t["neckbase_back_z"] = float(zb.max()) if len(zb) else np.nan
    t["neckbase_tilt_dz"] = t["neckbase_back_z"] - t["neckbase_front_z"]
    # eixo de massa (centroide): inclinação por segmento (graus; + = inclinado para a frente a subir)
    zc, cy = pr["zc"], smooth(pr["cy"])
    for seg, (lo, hi) in {"axis_pelvis_0.50-0.58": (0.50, 0.58), "axis_lumbar_0.60-0.68": (0.60, 0.68),
                          "axis_thorax_0.70-0.78": (0.70, 0.78)}.items():
        m = (zc >= lo * S) & (zc <= hi * S)
        if m.sum() > 3:
            b = np.polyfit(zc[m], cy[m], 1)[0]; t[seg] = float(np.degrees(np.arctan(b)))
    return t


if __name__ == "__main__":
    R = {}
    fig, ax = plt.subplots(1, 2, figsize=(14, 11))
    for n, c in C.items():
        pr = profile(n); pr["name"] = n
        t = turning(pr); R[n] = t
        a = ax[0]
        a.plot(pr["mb"], pr["z"], color=c, lw=2.2 if n == "ours" else 1.4, label=n)
        a.plot(pr["mf"], pr["z"], color=c, lw=2.2 if n == "ours" else 1.4)
        for k in ("thoracic_apex", "lumbar_deepest", "gluteal_apex", "bust_apex", "underbust", "abdomen_low", "gluteal_fold"):
            if k in t: a.plot(t[k][1], t[k][0], "o", color=c, ms=5)
        a.plot([np.interp(t["neckbase_front_z"], pr["z"], pr["mf"]), np.interp(t["neckbase_back_z"], pr["z"], pr["mb"])],
               [t["neckbase_front_z"], t["neckbase_back_z"]], "--", color=c, lw=1.2)
        ax[1].plot(pr["cy"], pr["zc"], color=c, lw=2.2 if n == "ours" else 1.4, label=n)
    for a in ax:
        a.axvline(0, color="k", lw=.5); a.set_ylim(0.44 * S, 0.95 * S); a.grid(alpha=.3); a.legend(fontsize=9)
        a.set_ylabel("z (mm @1700)")
    ax[0].set_xlabel("y (mm; 0 = canela a 0.12·S; frente →)"); ax[0].set_title("perfil sagital na linha média (costas e frente)\npontos: viragens; tracejado: base do pescoço (frente→costas)")
    ax[1].set_xlabel("y do centroide do corte (mm)"); ax[1].set_title("eixo de massa do tronco (centroide dos cortes)")
    ax[0].set_xlim(-260, 220); ax[1].set_xlim(-80, 80)
    plt.tight_layout(); plt.savefig(os.path.join(OUT, "fig_sagittal.png"), dpi=70)
    json.dump(R, open(os.path.join(WORK, "sagittal.json"), "w"), indent=1)
    keys = ["thoracic_apex", "lumbar_deepest", "lumbar_depth_vs_chord", "gluteal_apex", "gluteal_fold", "bust_apex", "underbust",
            "abdomen_low", "neck_z", "neckbase_front_z", "neckbase_back_z", "neckbase_tilt_dz",
            "axis_pelvis_0.50-0.58", "axis_lumbar_0.60-0.68", "axis_thorax_0.70-0.78"]
    print(f"{'':26s}" + "".join(f"{n:>22s}" for n in C))
    for k in keys:
        cells = []
        for n in C:
            v = R[n].get(k)
            cells.append(f"{'z=%.0f y=%+.0f' % v:>22s}" if isinstance(v, (tuple, list)) else f"{v:22.1f}" if v is not None else f"{'—':>22s}")
        print(f"{k:26s}" + "".join(cells))
