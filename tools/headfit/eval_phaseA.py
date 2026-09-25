"""HEAD FASE A — avaliação contra o pré-registo congelado (docs/HEAD_PHASE_A_PREREG.md).

Mesmo instrumento para todas as fontes: normalização HEAD STUDY 01, mapa radial
+ SH grau 16 (target.py), métricas S/W/TR (analyse.py), rasterizador neutro
(figures.py).  Saída: docs/head_phaseA/{eval.json, eval.txt, views.png, profiles.png}
"""
import os
import sys
import json
import numpy as np

HERE = os.path.dirname(__file__)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "headstudy"))
import target as TG        # noqa: E402
import common as C         # noqa: E402
import analyse as A        # noqa: E402
import figures as F        # noqa: E402

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt   # noqa: E402

H = C.H_MM
DOC = os.path.join(HERE, "..", "..", "docs", "head_phaseA")
L = 16


def radial_rms(name, TH, PH, tgt, dom):
    Vn, T, fs, fi, info = C.normalise(name)
    R, X = TG.radial_map(Vn, T)
    neck, ear = TG.masks(X)
    valid = np.isfinite(R) & ~neck & ~ear
    c, _ = TG.sh_fit(R, valid, TH, PH, L)
    e = (TG.sh_eval(c, TH, PH, L) - tgt)[dom]
    return float(np.sqrt(np.mean(e ** 2))), float(np.abs(e).max()), info


def mass_metrics(name):
    """Métricas de massa (sem traços): larguras, comprimento g–op, S5, TR3.
    Para cabeças sem traços os marcos glabela/opistocrânio vêm do mesmo
    sagittal_landmarks (máximos do perfil); nasion/pronasale não são usados."""
    M = A.analyse(name)
    S, W, TR = M["S"], M["W"], M["TR"]
    return {"R_cephalic": W["R_cephalic_breadth_over_length"], "S7_g_op": S["S7_head_length_g_op"],
            "W1_breadth": W["W1_head_breadth_max"], "W3/W2": W["R_minfrontal_over_bizyg"],
            "W0.10H/W2": W["R_jaw_taper_0.10H_over_bizyg"], "S5_glabella": S["S5_glabella_ahead_of_centre"],
            "TR3_submental": TR["TR3_submental_len"], "_M": M}


CRIT = {"R_cephalic": (0.70, 0.79), "S7_g_op": (196, 210), "W1_breadth": (141, 156), "W3/W2": (0.95, 9),
        "W0.10H/W2": (0.62, 0.77), "S5_glabella": (95, 107), "TR3_submental": (55, 999)}


def main():
    os.makedirs(DOC, exist_ok=True)
    d = np.load(os.path.join(TG.OUT, "target.npz"))
    TH, PH = d["TH"], d["PH"]
    tgt = TG.sh_eval(d[f"mean{L}"], TH, PH, L)
    dom = np.logical_and.reduce([d[f"{n}_valid"] for n in TG.TARGET_SOURCES])
    out, lines = {}, []
    names = ["ours", "oursA"] + TG.TARGET_SOURCES
    for nm in names:
        rms, mx, info = radial_rms(nm, TH, PH, tgt, dom)
        try:
            mm = mass_metrics(nm)
        except Exception as exc:          # declarado, não escondido
            mm = {"error": repr(exc)}
        out[nm] = {"C1_rms": rms, "C1_max": mx, "H_src": info["H_src_units"],
                   **{k: v for k, v in mm.items() if not k.startswith("_")}}
    hdr = f"{'critério':16s}" + "".join(f"{n:>12s}" for n in names) + "   alvo"
    lines.append(hdr)
    lines.append(f"{'C1 RMS radial':16s}" + "".join(f"{out[n]['C1_rms']:12.2f}" for n in names) + "   ≤ 2.5")
    lines.append(f"{'C1 máx |e|':16s}" + "".join(f"{out[n]['C1_max']:12.1f}" for n in names))
    for k, (lo, hi) in CRIT.items():
        row = f"{k:16s}"
        for n in names:
            v = out[n].get(k, np.nan)
            ok = "" if n not in ("ours", "oursA") else (" ✓" if lo <= v <= hi else " ✗")
            row += f"{v:10.2f}{ok:2s}"
        lines.append(row + f"   [{lo}, {hi if hi < 900 else '∞'}]")
    txt = "\n".join(lines)
    print(txt)
    open(os.path.join(DOC, "eval.txt"), "w").write(txt + "\n")
    json.dump(out, open(os.path.join(DOC, "eval.json"), "w"), indent=1, default=float)

    # vistas neutras (mesmo rasterizador do estudo): frente, lado, ¾, costas
    show = ["ours", "oursA", "makehuman", "femalebase", "femalechar"]
    kinds = ("front", "side", "q", "back")
    fig, ax = plt.subplots(len(show), 4, figsize=(12.4, 3.4 * len(show)))
    for r, nm in enumerate(show):
        Vn, T, info = F.load_norm(nm)
        for c, kind in enumerate(kinds):
            V2 = Vn.copy()
            k2 = kind
            if kind == "back":
                V2[:, 0] *= -1; V2[:, 1] *= -1; k2 = "front"
            img, _, _ = F.raster(V2, T, k2, F.BOX[k2 if k2 != "q" else "q"])
            ax[r, c].imshow(img, cmap="gray", vmin=0, vmax=1, extent=F.BOX[k2])
            ax[r, c].set_xticks([]); ax[r, c].set_yticks([])
            if c == 0:
                ax[r, c].set_ylabel({"ours": "ANTES (atual)", "oursA": "FASE A (massas)"}.get(nm, nm), fontsize=10)
            if r == 0:
                ax[r, c].set_title({"front": "frente", "side": "lado", "q": "¾", "back": "costas"}[kind])
    fig.suptitle("HEAD FASE A — cinza neutro, sem cabelo/materiais, mm@H226, mesmo rasterizador para todos", fontsize=10)
    fig.tight_layout(rect=(0, 0, 1, 0.985))
    fig.savefig(os.path.join(DOC, "views.png"), dpi=100)
    plt.close(fig)

    # perfis: sagital + larguras
    fig, ax = plt.subplots(1, 2, figsize=(12, 6.2))
    col = {"ours": "#d62728", "oursA": "#111111", "makehuman": "#1f77b4", "femalebase": "#ff7f0e",
           "bodytopo": "#2ca02c", "femalechar": "#9467bd"}
    for nm in ["makehuman", "femalebase", "bodytopo", "femalechar", "ours", "oursA"]:
        Vn, T, fs, fi, info = C.normalise(nm)
        L_, (zs, yf, yb, pts) = C.sagittal_landmarks(Vn, T)
        lw = 2.4 if nm in ("ours", "oursA") else 1.0
        ls = "--" if nm == "ours" else "-"
        ax[0].plot(yf, zs, color=col[nm], lw=lw, ls=ls, label=nm)
        ax[0].plot(yb, zs, color=col[nm], lw=lw * 0.6, ls=":")
        zz = np.arange(-0.2 * H, H, 2.0)
        ax[1].plot([A.width_at(Vn, T, z) for z in zz], zz, color=col[nm], lw=lw, ls=ls, label=nm)
    for a in ax:
        a.set_aspect("equal"); a.grid(alpha=0.3); a.axhline(0, color="k", lw=0.4); a.legend(fontsize=8)
    ax[0].set_title("perfil sagital (frente contínua, costas pontilhado)")
    ax[1].set_title("largura máxima por altura")
    fig.tight_layout()
    fig.savefig(os.path.join(DOC, "profiles.png"), dpi=100)
    plt.close(fig)


if __name__ == "__main__":
    main()
