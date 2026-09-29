# -*- coding: utf-8 -*-
"""T-TORSO SISTEMA — análise do torso como SISTEMA (TORSO_STUDY_02).

Lê os perfis do instrumento comum (prof_*.json, @1700 mm) + as malhas cruas
(raw_*.npz) e calcula descritores de SISTEMA por modelo:

  A. sagital   — ápices torácico/lombar/nádega, perfis bs(z)/fs(z) a cotas fixas,
                 CURVATURA κ(z) do perfil posterior (transições/quebras: a lacuna
                 declarada das métricas antigas)
  B. coronal   — vector de proporções (ombro não medível; peito:cintura:anca em
                 largura e profundidade) + níveis; INVARIANTE À ORIENTAÇÃO
  C. secções   — expoente de superelipse + partilha frente/trás a 3 níveis
  D. glúteos   — contorno posterior y(x) no ápice: sulco central vs lóbulos
  E. busto     — nível e saliência da mama (frente), para a decisão T4

Saídas: out/refstudy/torsosystem/system.json + tabelas no stdout +
docs/head_phaseA/torso_system_*.png (painéis comparativos).

Admissões (orientação por MEDIÇÃO, ver TORSO_STUDY_02 §2): sagital admite
femalebase/femalechar/bodytopo/real005/ff11*/animeF (*cautela low-poly);
lucia e whitewalker só coronal (sagital inconclusivo); mppled em frame
próprio (só forma). ours = T1 on; ours0 = T1 off (mesma topologia).

Uso: python tools/refstudy/torso_system.py
"""
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _paths import WORK  # noqa: E402

import numpy as np  # noqa: E402

import geom  # noqa: E402

OUT = os.path.join(WORK, "torsosystem")
DOCS = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "docs", "head_phaseA")

S = 1700.0
SAGITTAL = ["femalebase", "femalechar", "bodytopo", "real005", "ff11", "animeF"]
CORONAL = SAGITTAL + ["lucia", "whitewalker"]
OURS, OURS0 = "ours", "ours0"
REF_STYLE = {"femalebase": "realista", "femalechar": "realista", "bodytopo": "base-mesh",
             "real005": "realista", "ff11": "anime-realista", "animeF": "anime",
             "lucia": "makehuman", "whitewalker": "masculino", "mppled": "torso-sculpt"}
OURS_LABEL = {OURS: "nós T1-on", OURS0: "nós T1-off"}


# ---------------------------------------------------------------- perfis
def prof(name):
    return json.load(open(os.path.join(WORK, f"prof_{name}.json")))["prof"]


def centered(name):
    """linhas do componente central com mid_front/mid_back válidos"""
    return [p for p in prof(name) if p["center"]
            and not math.isnan(p.get("mid_back", float("nan")))]


def at(p, z0):
    """linha mais próxima da cota z0"""
    return min(p, key=lambda r: abs(r["z"] - z0))


def crotch(p):
    try:
        return max(r["z"] for r in p if not r["center"] and r["z"] < 0.62 * S)
    except ValueError:                     # pernas fundas (sem componentes laterais)
        return 0.50 * S                   # fallback declarado (aproximado)


def interp_midback(name, z0):
    C = centered(name)
    zs = np.array([r["z"] for r in C])
    ys = np.array([r["mid_back"] for r in C])
    o = np.argsort(zs)
    return float(np.interp(z0, zs[o], ys[o]))


def interp_front(name, z0):
    C = centered(name)
    zs = np.array([r["z"] for r in C])
    ys = np.array([r["mid_front"] for r in C])
    o = np.argsort(zs)
    return float(np.interp(z0, zs[o], ys[o]))


# ------------------------------------------------------- A. sagital
def sagittal(name):
    p = prof(name)
    C = centered(name)
    cr = crotch(p)
    lo = cr / S + 0.005
    B = np.array([(r["z"], r["mid_back"]) for r in C])
    s = B[(B[:, 0] >= 0.70 * S) & (B[:, 0] <= 0.82 * S)]
    t = s[np.argmin(s[:, 1])] if len(s) else (float("nan"), float("nan"))
    s = B[(B[:, 0] >= lo * S) & (B[:, 0] <= 0.58 * S)]
    b = s[np.argmin(s[:, 1])] if len(s) else (float("nan"), float("nan"))
    seg = B[(B[:, 0] < t[0]) & (B[:, 0] > b[0])]
    m = {"thoracic_z": float(t[0]), "thoracic_y": float(t[1]),
         "buttock_z": float(b[0]), "buttock_y": float(b[1])}
    if len(seg) > 3:
        yline = b[1] + (seg[:, 0] - b[0]) / (t[0] - b[0]) * (t[1] - b[1])
        m["lumbar"] = float(np.max(seg[:, 1] - yline))
        m["lumbar_z"] = float(seg[np.argmax(seg[:, 1] - yline), 0])
    m["buttock_behind_thoracic"] = float(t[1] - b[1])
    # perfil a cotas fixas (sistema, não métrica isolada)
    for z0 in (920, 1000, 1060, 1100, 1160, 1220, 1280, 1340, 1380):
        m[f"bs@{z0}"] = interp_midback(name, z0)
    # E. busto (frente): ápice da FRENTE DO COMPONENTE (a mama é lateral à
    # coluna |x|<=10 — mid_front mede o esterno; medido: femalebase caía no
    # bordo da banda). Banda 0.70–0.79, saliência vs 0.795 (submamário).
    F = np.array([(r["z"], r["front"]) for r in C])
    band = F[(F[:, 0] >= 0.70 * S) & (F[:, 0] <= 0.79 * S)]
    if len(band):
        i = np.argmax(band[:, 1])
        m["breast_z"] = float(band[i, 0])
        ub = min(C, key=lambda r: abs(r["z"] - 0.795 * S))
        m["breast_prom"] = float(band[i, 1] - ub["front"])
    # A2. curvatura κ(z) do perfil posterior (suavizada): transições
    zs = np.array([r["z"] for r in C])
    ys = np.array([r["mid_back"] for r in C])
    o = np.argsort(zs)
    zs, ys = zs[o], ys[o]
    kk = []
    for i in range(1, len(zs) - 1):
        dz1, dz2 = zs[i] - zs[i - 1], zs[i + 1] - zs[i]
        if dz1 <= 0 or dz2 <= 0 or dz1 > 30 or dz2 > 30:
            kk.append((zs[i], float("nan")))
            continue
        d2 = (ys[i + 1] - ys[i]) / dz2 - (ys[i] - ys[i - 1]) / dz1
        kk.append((zs[i], float(d2 / (0.5 * (dz1 + dz2)))))
    kzf = np.array([k[0] for k in kk])
    kv = np.array([k[1] for k in kk])
    m["kappa"] = {"z": kzf.tolist(), "k": kv.tolist()}
    # nº de extremos locais de κ na banda 850–1400 (quebras/transições)
    band = (kzf >= 850) & (kzf <= 1400) & ~np.isnan(kv)
    if band.sum() > 8:
        kvb = kv[band]
        zvb = kzf[band]
        # suavizar κ (janela 3) e contar extremos
        ks = np.convolve(kvb, np.ones(3) / 3, mode="same")
        ext = 0
        ext_z = []
        for i in range(1, len(ks) - 1):
            if (ks[i] - ks[i - 1]) * (ks[i + 1] - ks[i]) < 0 and abs(ks[i]) > 2e-5:
                ext += 1
                ext_z.append(float(zvb[i]))
        m["kappa_extrema_850_1400"] = ext
        m["kappa_extrema_z"] = ext_z
    return m


# ------------------------------------------------------- B. coronal
def coronal(name):
    """Validade declarada por célula: larguras >=600 = saturação da grelha
    (braços T/A-pose no componente central) → None; ff11 = low-poly (cortes
    grosseiros) → None nas larguras; whitewalker EXCLUÍDO (normalização
    quebrada: busto/plinto — z-extent != estatura, medido: depth 520 = grelha)."""
    if name == "whitewalker":
        return {"note": "EXCLUÍDO: normalização quebrada (z-extent != estatura)"}
    p = prof(name)
    C = [r for r in p if r["center"]]
    cr = crotch(p)
    lo = cr / S + 0.005
    ch = max((r for r in C if 0.68 * S <= r["z"] <= 0.78 * S), key=lambda r: r["width"])
    wn = min((r for r in C if 0.58 * S <= r["z"] <= 0.70 * S), key=lambda r: r["width"])
    hb = max((r for r in C if lo * S <= r["z"] <= 0.58 * S), key=lambda r: r["width"])
    bd = max((r for r in C if lo * S <= r["z"] <= 0.58 * S), key=lambda r: r["depth"])
    sat = lambda v: None if (v is None or v >= 600) else float(v)
    lowpoly = (name == "ff11")
    m = {"chest_w": None if lowpoly else sat(ch["width"]), "chest_z": ch["z"],
         "waist_w": None if lowpoly else sat(wn["width"]), "waist_z": wn["z"],
         "hip_w": None if lowpoly else sat(hb["width"]), "hip_z": hb["z"],
         "butt_d": bd["depth"], "butt_z": bd["z"],
         "chest_d": max(r["depth"] for r in C if 0.68 * S <= r["z"] <= 0.78 * S)}
    if m["chest_w"] and m["hip_w"]:
        m["chest/hip"] = m["chest_w"] / m["hip_w"]
    if m["waist_w"] and m["hip_w"]:
        m["waist/hip"] = m["waist_w"] / m["hip_w"]
    m["waist_z_frac"] = m["waist_z"] / S
    m["hip_z_frac"] = m["hip_z"] / S
    m["chest_z_frac"] = m["chest_z"] / S
    return m


# ------------------------------------------- C/D. malha crua (secções, glúteos)
def load_norm(name):
    """malha crua normalizada como o analyse() (com overrides do bodytopo)."""
    d = np.load(os.path.join(WORK, f"raw_{name}.npz"))
    V, T = d["V"].copy(), d["T"]
    lab = np.load(os.path.join(WORK, f"lab_{name}.npy"))
    cfg = {}
    cpath = os.path.join(WORK, f"cfg_{name}.json")
    bpath = os.path.join(WORK, "cfg_bodytopo.json")
    if name == "bodytopo" and os.path.exists(bpath):
        cfg = json.load(open(bpath))
    zmin, zmax = V[:, 2].min(), V[:, 2].max()
    St = cfg.get("stature_override", zmax - zmin)
    fl = cfg.get("floor_override", zmin)
    V[:, 2] -= fl
    V[:, 0] -= (V[:, 0].max() + V[:, 0].min()) / 2
    V *= S / St
    flip = cfg.get("flip_y", name in ("femalechar", "bodytopo", "real005", "ff11", "animeF"))
    if flip:
        V[:, 1] *= -1
    dp = os.path.join(WORK, f"drop_{name}.json")
    if os.path.exists(dp):
        drop = json.load(open(dp))["drop_labels"]
        T = T[~np.isin(lab[T[:, 0]], drop)]
    return V, T, lab


def contour(name, z0, xr=170):
    """contorno do componente central no corte z0: pontos (x, y)."""
    V, T, lab = load_norm(name)
    Tm = T[(V[T][:, :, 2].min(1) <= z0) & (V[T][:, :, 2].max(1) >= z0)]
    segs = geom.slice_segments(V, Tm, z0)
    pts = np.array([( (a[0]+b[0])/2, (a[1]+b[1])/2 ) for a, b in segs]) if len(segs) else np.zeros((0, 2))
    if not len(pts):
        return None
    # componente que contém x≈0
    keep = pts[np.abs(pts[:, 0]) <= xr]
    return keep


def sec_shape(name, z0):
    """expoente de superelipse + partilha frente/trás no corte z0."""
    pts = contour(name, z0)
    if pts is None or len(pts) < 12:
        return None
    a = (pts[:, 0].max() - pts[:, 0].min()) / 2
    b = (pts[:, 1].max() - pts[:, 1].min()) / 2
    yc = (pts[:, 1].max() + pts[:, 1].min()) / 2
    if a < 5 or b < 5:
        return None
    # ajuste de n: |x/a|^n + |y'/b|^n = 1  (y' centrado no centro do contorno)
    xs = (pts[:, 0]) / a
    ys = (pts[:, 1] - yc) / b
    best, bestn = None, 2.0
    for n in (1.6, 1.8, 2.0, 2.2, 2.5, 2.8, 3.2, 3.8, 4.5):
        r = (np.abs(xs) ** n + np.abs(ys) ** n) ** (1 / n)
        err = float(np.mean((r - 1.0) ** 2))
        if best is None or err < best:
            best, bestn = err, n
    ybar = float(np.mean(pts[:, 1]))      # centro de massa do contorno
    front_share = (pts[:, 1].max() - ybar) / max(1e-6, ybar - pts[:, 1].min())
    return {"n": bestn, "fit_err": best, "front_share": front_share, "a": a, "b": b}


def gluteal(name, z0):
    """contorno posterior y(x) no corte z0: sulco central vs lóbulos."""
    pts = contour(name, z0)
    if pts is None:
        return None
    back = pts[pts[:, 1] < 0]
    if len(back) < 8:
        return None
    xs = back[:, 0]
    ys = back[:, 1]
    def yat(x0):
        m = np.abs(xs - x0) <= 8
        return float(ys[m].min()) if m.any() else float("nan")
    y0 = yat(0.0)
    lobes = [yat(x) for x in (55, 70, 85, 100)]
    lobes = [v for v in lobes if not math.isnan(v)]
    if math.isnan(y0) or not lobes:
        return None
    lobe = min(lobes)
    # contorno y(x) (mínimo por bins de 10 mm) para o painel
    bx, by = [], []
    for x0 in np.arange(-120, 121, 10):
        m = np.abs(xs - x0) <= 6
        if m.any():
            bx.append(float(x0)); by.append(float(ys[m].min()))
    return {"y_center": y0, "y_lobe": lobe, "sulcus": lobe - y0,
            "apex_y": float(ys.min()),
            "contour_x": bx, "contour_y": by}


# ------------------------------------------------------------------ main
def band(vals):
    v = [x for x in vals if x is not None and not math.isnan(x)]
    return (min(v), max(v)) if v else (float("nan"),) * 2


def main():
    os.makedirs(OUT, exist_ok=True)
    res = {"sagittal": {}, "coronal": {}, "sections": {}, "gluteal": {}}
    for n in SAGITTAL + [OURS, OURS0]:
        try:
            res["sagittal"][n] = sagittal(n)
        except Exception as e:
            print(f"[sagital] {n}: {e!r}")
    for n in CORONAL + [OURS, OURS0]:
        try:
            res["coronal"][n] = coronal(n)
        except Exception as e:
            print(f"[coronal] {n}: {e!r}")
    for n in SAGITTAL + [OURS, OURS0]:
        res["sections"][n] = {}
        for tag, frac in (("chest", 0.735), ("waist", 0.635), ("hip", 0.53)):
            res["sections"][n][tag] = sec_shape(n, frac * S)
        # glúteos no ápice da nádega (medido no coronal: butt_z)
        bz = res["sagittal"].get(n, {}).get("buttock_z")
        if bz is None or math.isnan(bz):
            bz = res["coronal"].get(n, {}).get("butt_z", 0.52 * S)
        res["gluteal"][n] = gluteal(n, bz)
    # mppled em frame próprio (normalizado pelo seu z-extent; cotas RELATIVAS
    # à própria malha — sem estatura; usado só para FORMA, nunca para níveis)
    d = np.load(os.path.join(WORK, "raw_mppled.npz"))
    V = d["V"].copy()
    z0, z1 = V[:, 2].min(), V[:, 2].max()
    V[:, 2] -= z0
    V[:, 0] -= (V[:, 0].max() + V[:, 0].min()) / 2
    V[:, 1] *= -1          # frente = +Y (mamas+/glúteos−, medido §2)
    V *= S / (z1 - z0)
    np.savez(os.path.join(WORK, "raw_mppled_norm.npz"), V=V, T=d["T"])
    T = d["T"]
    # varre fatias para achar cintura (min largura) e ápice da nádega (max prof.)
    best = {}
    for zf in np.arange(0.08, 0.75, 0.01):
        zz = zf * S
        Tm = T[(V[T][:, :, 2].min(1) <= zz) & (V[T][:, :, 2].max(1) >= zz)]
        segs = geom.slice_segments(V, Tm, zz)
        pts = np.array([((a[0] + b[0]) / 2, (a[1] + b[1]) / 2) for a, b in segs]) if len(segs) else np.zeros((0, 2))
        if len(pts) < 8:
            continue
        w = pts[:, 0].max() - pts[:, 0].min()
        dep = pts[:, 1].max() - pts[:, 1].min()
        if 0.42 < zf < 0.60 and ("waist" not in best or w < best["waist"][1]):
            best["waist"] = (zf, w)
        if zf < 0.40 and ("butt" not in best or dep > best["butt"][1]):
            best["butt"] = (zf, dep)
    res["mppled_frame"] = {k: v for k, v in best.items()}
    # contorno glúteo do mppled no seu ápice
    if "butt" in best:
        zz = best["butt"][0] * S
        Tm = T[(V[T][:, :, 2].min(1) <= zz) & (V[T][:, :, 2].max(1) >= zz)]
        segs = geom.slice_segments(V, Tm, zz)
        pts = np.array([((a[0] + b[0]) / 2, (a[1] + b[1]) / 2) for a, b in segs])
        back = pts[pts[:, 1] < 0]
        if len(back) >= 8:
            def yat(x0):
                m = np.abs(back[:, 0] - x0) <= 8
                return float(back[m, 1].min()) if m.any() else float("nan")
            y0 = yat(0.0)
            lobes = [v for v in (yat(55), yat(70), yat(85), yat(100)) if not math.isnan(v)]
            if not math.isnan(y0) and lobes:
                res["gluteal"]["mppled"] = {"y_center": y0, "y_lobe": min(lobes),
                                            "sulcus": min(lobes) - y0,
                                            "apex_y": float(back[:, 1].min()),
                                            "frame": "próprio (z-extent)"}
    json.dump(res, open(os.path.join(OUT, "system.json"), "w"), default=float)

    # ---------------- tabelas
    print("\n=== A. SAGITAL (refs banda vs nós) ===")
    keys = ["lumbar", "buttock_behind_thoracic", "thoracic_z", "buttock_z", "breast_z",
            "breast_prom", "bs@920", "bs@1060", "bs@1220", "bs@1380", "kappa_extrema_850_1400"]
    hdr = f"{'métrica':26s}" + "".join(f"{n[:9]:>10s}" for n in SAGITTAL) + \
          f"{OURS0[:9]:>10s}{OURS[:9]:>10s}   banda refs"
    print(hdr)
    for k in keys:
        vals = [res["sagittal"][n].get(k, float("nan")) for n in SAGITTAL]
        lo, hi = band(vals)
        row = f"{k:26s}" + "".join(f"{v:10.1f}" for v in vals) + \
              f"{res['sagittal'][OURS0].get(k, float('nan')):10.1f}" + \
              f"{res['sagittal'][OURS].get(k, float('nan')):10.1f}   [{lo:.0f},{hi:.0f}]"
        print(row)

    print("\n=== B. CORONAL (proporções; TODAS as refs) ===")
    keys = ["chest_w", "waist_w", "hip_w", "chest_d", "butt_d", "chest/hip", "waist/hip",
            "chest_z_frac", "waist_z_frac", "hip_z_frac"]
    print(f"{'métrica':26s}" + "".join(f"{n[:9]:>10s}" for n in CORONAL) +
          f"{OURS0[:9]:>10s}{OURS[:9]:>10s}   banda refs")
    def _f(v):
        return float("nan") if v is None else float(v)
    for k in keys:
        vals = [_f(res["coronal"][n].get(k)) for n in CORONAL]
        lo, hi = band(vals)
        row = f"{k:26s}" + "".join(f"{v:10.2f}" for v in vals) + \
              f"{_f(res['coronal'][OURS0].get(k)):10.2f}" + \
              f"{_f(res['coronal'][OURS].get(k)):10.2f}   [{lo:.2f},{hi:.2f}]"
        print(row)

    print("\n=== C. SECÇÕES (superelipse n; partilha frente) ===")
    for tag in ("chest", "waist", "hip"):
        print(f"-- {tag} --")
        for k in ("n", "front_share"):
            vals = [(res["sections"][n][tag] or {}).get(k) for n in SAGITTAL]
            lo, hi = band(vals)
            row = f"  {k:14s}" + "".join(f"{(v if v is not None else float('nan')):8.2f}" for v in vals) + \
                  f"{(res['sections'][OURS0][tag] or {}).get(k, float('nan')):8.2f}" + \
                  f"{(res['sections'][OURS][tag] or {}).get(k, float('nan')):8.2f}   [{lo:.2f},{hi:.2f}]"
            print(row)

    print("\n=== D. GLÚTEOS (contorno posterior no ápice) ===")
    for k in ("y_center", "y_lobe", "sulcus"):
        vals = [(res["gluteal"][n] or {}).get(k) for n in SAGITTAL]
        lo, hi = band(vals)
        row = f"{k:14s}" + "".join(f"{(v if v is not None else float('nan')):8.1f}" for v in vals) + \
              f"{(res['gluteal'][OURS0] or {}).get(k, float('nan')):8.1f}" + \
              f"{(res['gluteal'][OURS] or {}).get(k, float('nan')):8.1f}   [{lo:.1f},{hi:.1f}]"
        print(row)
    print("\nsystem.json →", os.path.join(OUT, "system.json"))

    # ---------------- painéis
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    COLORS = {"femalebase": "#888", "femalechar": "#999", "bodytopo": "#aaa",
              "real005": "#777", "ff11": "#bbb", "animeF": "#ccc"}
    fig, axes = plt.subplots(1, 2, figsize=(13, 6), sharey=True)
    for n in SAGITTAL:
        C = centered(n)
        zs = [r["z"] for r in C]
        axes[0].plot(zs, [r["mid_back"] for r in C], color=COLORS[n], lw=1,
                     label=f"{n} ({REF_STYLE[n]})")
        axes[1].plot(zs, [r["mid_front"] for r in C], color=COLORS[n], lw=1)
    for n, c, lsty in ((OURS0, "#1f77b4", "--"), (OURS, "#d62728", "-")):
        C = centered(n)
        zs = [r["z"] for r in C]
        axes[0].plot(zs, [r["mid_back"] for r in C], color=c, lw=2.2, ls=lsty, label=OURS_LABEL[n])
        axes[1].plot(zs, [r["mid_front"] for r in C], color=c, lw=2.2, ls=lsty)
    axes[0].set_title("perfil posterior (linha média, mm @1700)")
    axes[1].set_title("perfil anterior")
    for ax in axes:
        ax.set_xlim(800, 1450); ax.set_xlabel("z (mm)"); ax.grid(alpha=.3)
    axes[0].set_ylabel("y (mm)")
    axes[0].legend(fontsize=7)
    fig.suptitle("TORSO SISTEMA — sagital: refs (cinza) vs nós (T1-off tracejado, T1-on sólido)")
    fig.tight_layout()
    fig.savefig(os.path.join(DOCS, "torso_system_sagittal.png"), dpi=110)
    print("painel →", os.path.join(DOCS, "torso_system_sagittal.png"))

    fig, ax = plt.subplots(figsize=(9, 6))
    for n in CORONAL:
        if n == "whitewalker":
            continue
        hw = res["coronal"][n].get("hip_w")
        if not hw:
            continue
        C = [r for r in prof(n) if r["center"] and 800 <= r["z"] <= 1500]
        ax.plot([r["z"] for r in C], [r["width"] / hw for r in C],
                color=COLORS.get(n, "#999"), lw=1, label=f"{n} ({REF_STYLE[n]})")
    for n, c, lsty in ((OURS0, "#1f77b4", "--"), (OURS, "#d62728", "-")):
        hw = res["coronal"][n]["hip_w"]
        C = [r for r in prof(n) if r["center"] and 800 <= r["z"] <= 1500]
        ax.plot([r["z"] for r in C], [r["width"] / hw for r in C], color=c, lw=2.2, ls=lsty,
                label=OURS_LABEL[n])
    ax.set_title("largura do tronco normalizada pela anca (coronal; INVARIANTE à orientação)")
    ax.set_xlabel("z (mm)"); ax.set_ylabel("w / w_anca"); ax.grid(alpha=.3)
    ax.set_xlim(800, 1500); ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(os.path.join(DOCS, "torso_system_coronal.png"), dpi=110)
    print("painel →", os.path.join(DOCS, "torso_system_coronal.png"))

    fig, ax = plt.subplots(figsize=(9, 6))
    for n in SAGITTAL + ["mppled"]:
        g = res["gluteal"].get(n)
        if not g or "contour_x" not in g:   # fix: chave é contour_x (painel estava VAZIO)
            continue
        ax.plot(g["contour_x"], g["contour_y"], color=COLORS.get(n, "#999"), lw=1,
                label=f"{n} ({REF_STYLE.get(n, 'torso-sculpt')})")
    for n, c, lsty in ((OURS0, "#1f77b4", "--"), (OURS, "#d62728", "-")):
        g = res["gluteal"].get(n)
        if g and "contour_x" in g:          # fix: idem
            ax.plot(g["contour_x"], g["contour_y"], color=c, lw=2.2, ls=lsty, label=OURS_LABEL[n])
    ax.set_title("contorno glúteo no ápice (y posterior vs x; sulco = centro recuado)")
    ax.set_xlabel("x (mm)"); ax.set_ylabel("y (mm)"); ax.grid(alpha=.3)
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(os.path.join(DOCS, "torso_system_gluteal.png"), dpi=110)
    print("painel →", os.path.join(DOCS, "torso_system_gluteal.png"))

    fig, ax = plt.subplots(figsize=(9, 6))
    for n in SAGITTAL:
        k = res["sagittal"][n].get("kappa")
        if not k:
            continue
        ax.plot(k["z"], np.array(k["k"]) * 1000, color=COLORS[n], lw=1,
                label=f"{n} ({REF_STYLE[n]})")
    for n, c, lsty in ((OURS0, "#1f77b4", "--"), (OURS, "#d62728", "-")):
        k = res["sagittal"][n].get("kappa")
        if k:
            ax.plot(k["z"], np.array(k["k"]) * 1000, color=c, lw=2.2, ls=lsty, label=OURS_LABEL[n])
    ax.set_title("curvatura κ(z) do perfil posterior (transições; mm⁻¹×10⁻³)")
    ax.set_xlabel("z (mm)"); ax.set_ylabel("κ"); ax.grid(alpha=.3)
    ax.set_xlim(800, 1450); ax.set_ylim(-0.6, 0.6); ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(os.path.join(DOCS, "torso_system_curvature.png"), dpi=110)
    print("painel →", os.path.join(DOCS, "torso_system_curvature.png"))


if __name__ == "__main__":
    main()
