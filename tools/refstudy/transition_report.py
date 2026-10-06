# -*- coding: utf-8 -*-
"""TRANSITION REPORT — continuidade de forma nas cadeias do corpo (§4 BODY_SPEC).

Directriz do dono (docs/BODY_SPEC_REMAKE.md): "A → transição → B", medir
C = f(d, θ, κ).  Este instrumento mede κ(z) dos perfis sagitais (frente e
costas, x≈0) e detecta BREAKPOINTS — mudanças bruscas de curvatura
("linhas de mudança de componente") — por zona anatómica:

  frente: Z1 clavícula→tórax 1330–1430 · Z2 arco costal 1060–1180 ·
          Z3 abdómen→pelve 950–1060
  costas: Z4 cervical→torácica 1380–1480 · Z5 torácica→lombar 1080–1220 ·
          Z6 lombar→sacro 950–1080 · Z7 sacro→glúteo 850–950 ·
          Z8 glúteo→coxa 760–860

Métricas por zona: κ_max (1/m), reversões de κ (sign changes, suavizado),
max|dκ/dz| (1/m²·1e3).  Refs = banda min–max (real005/femalebase/femalechar).

Uso: python3 tools/refstudy/transition_report.py
Saídas: tabela stdout + docs/head_phaseA/transition_kappa.png + out JSON
"""
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)
WORK = os.path.join(ROOT, "out", "refstudy")
DOCS = os.path.join(ROOT, "docs", "head_phaseA")

from plane_scan import load, section_top_plane, repair_front  # noqa: E402

MODELS = [("real005", True), ("femalebase", False), ("femalechar", True),
          ("swV0", False), ("swB2", False), ("e1", False), ("e1n", False)]
ZONES = [  # (nome, lado, z_lo, z_hi)
    ("Z1 clavícula→tórax", "front", 1330, 1430),
    ("Z2 arco costal", "front", 1060, 1180),
    ("Z3 abdómen→pelve", "front", 950, 1060),
    ("Z4 cervical→torácica", "back", 1380, 1480),
    ("Z5 torácica→lombar", "back", 1080, 1220),
    ("Z6 lombar→sacro", "back", 950, 1080),
    ("Z7 sacro→glúteo", "back", 850, 950),
    ("Z8 glúteo→coxa", "back", 760, 860),
]
REFS = ("real005", "femalebase", "femalechar")


def sagittal(V, T, back=False):
    """y(z) do perfil sagital x≈0 (frente=max y; costas=espelho)."""
    Vp = V.copy()
    if back:
        Vp[:, 1] *= -1.0
    out = section_top_plane(Vp, T, 0.0, 760.0, 1500.0)
    if out[0] is None:
        return None, None
    z, y = repair_front(*out)
    if back:
        y = -y
    # grelha 1 mm + suavização gaussiana σ=4 mm (suprimir raster)
    zg = np.arange(800.0, 1471.0, 1.0)
    yg = np.interp(zg, z, y)
    k = np.exp(-0.5 * (np.arange(-12, 13) / 4.0) ** 2)
    k /= k.sum()
    ys = np.convolve(np.pad(yg, 12, mode="edge"), k, mode="valid")
    return zg, ys


def kappa(z, y):
    d1 = np.gradient(y, z)
    d2 = np.gradient(d1, z)
    return d2 / (1.0 + d1 * 1e-3 * d1 * 1e-3) ** 1.5 * 1e6   # d1 em mm→m


def zone_metrics(zg, kap, lo, hi):
    m = (zg >= lo) & (zg <= hi)
    if m.sum() < 20:
        return None
    k = kap[m]
    ks = np.convolve(np.pad(k, 6, mode="edge"),
                     np.ones(13) / 13.0, mode="valid")
    rev = int(np.sum(np.diff(np.sign(ks[10:-10])) != 0))
    dk = np.abs(np.gradient(k)).max()
    return {"kmax": float(np.abs(k).max()), "rev": rev, "dk": float(dk)}


def main():
    curves = {}
    for name, flip in MODELS:
        V, T = load(name, flip) if not name.startswith("e1") else \
            (np.load(os.path.join(WORK, f"raw_{name}.npz"))["V"],
             np.load(os.path.join(WORK, f"raw_{name}.npz"))["T"])
        curves[name] = {"front": sagittal(V, T, False),
                        "back": sagittal(V, T, True)}
        print(f"{name}: sagitais ok")

    report = {}
    print(f"\n{'zona':24s} {'métrica':8s} {'banda refs':>16s} "
          f"{'swV0':>8s} {'swB2':>8s} {'E1':>8s} {'E1N':>8s}")
    for zname, side, lo, hi in ZONES:
        vals = {}
        for name, _ in MODELS:
            zg, ys = curves[name][side]
            if zg is None:
                vals[name] = None
                continue
            vals[name] = zone_metrics(zg, kappa(zg, ys), lo, hi)
        report[zname] = vals
        for met, fmt in (("kmax", "{:8.1f}"), ("rev", "{:8d}"), ("dk", "{:8.1f}")):
            band = [vals[r][met] for r in REFS if vals[r]]
            row = (f"{zname:24s} {met:8s} "
                   f"{min(band):8.1f}..{max(band):<7.1f}" if band else "—")
            for n in ("swV0", "swB2", "e1", "e1n"):
                row += (" " + fmt.format(vals[n][met])) if vals[n] else "        —"
            print(row)

    # ---------------------------------------------------------------- painel κ(z)
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(1, 2, figsize=(13, 7), sharey=False)
    for ax, side, ttl in ((axes[0], "front", "FRENTE (x≈0)"),
                          (axes[1], "back", "COSTAS (x≈0)")):
        for name, col, lw in (("real005", "0.5", 1.6), ("femalebase", "0.5", 1.6),
                              ("femalechar", "0.5", 1.6), ("swV0", "#d62728", 1.4),
                              ("e1", "#1f77b4", 2.2), ("e1n", "#9467bd", 1.1)):
            zg, ys = curves[name][side]
            if zg is None:
                continue
            lbl = name + (" (ref)" if name in REFS else "")
            ax.plot(kappa(zg, ys), zg, color=col, lw=lw,
                    label=lbl, alpha=0.45 if name in REFS else 1.0)
        ax.set_title(f"κ(z) sagital — {ttl}")
        ax.set_xlabel("κ (1/km)")
        ax.set_ylabel("z (mm)")
        ax.set_ylim(760, 1480)
        ax.grid(alpha=0.25)
        ax.legend(fontsize=8, loc="upper right")
    fig.suptitle("TRANSIÇÕES — curvatura dos perfis sagitais (refs cinza · "
                 "V0 vermelho · E1 azul · E1N roxo). Breakpoints = picos estreitos.",
                 fontsize=10)
    fig.tight_layout()
    out = os.path.join(DOCS, "transition_kappa.png")
    fig.savefig(out, dpi=110)
    print("\npainel →", out)
    json.dump({k: {n: v for n, v in val.items()} for k, val in report.items()},
              open(os.path.join(WORK, "transition_report.json"), "w"), indent=1)
    print("dados →", os.path.join(WORK, "transition_report.json"))


if __name__ == "__main__":
    main()
