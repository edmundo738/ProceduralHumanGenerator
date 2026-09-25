"""PRÉ-REGISTO H7a × H4a — definição CONGELADA das métricas + calibração do instrumento.

Não altera o gerador e não executa intervenções.  Só mede o CONTROLO (árvore em
e6e809c) e as referências, para:
  1. fixar a definição exata de cada métrica (classe D / P / C / F, ver doc);
  2. medir o ruído de amostragem (jitter sub-pixel) → tolerâncias;
  3. medir a sensibilidade de cada métrica a translação e rotação rígidas
     (a regra do H3/H2: uma métrica que muda numa região não alterada pode ser
     instrumento/centralização/postura);
  4. obter valores de base (controlo e refs) ANTES de qualquer intervenção.

Uso: HCG_REFSTUDY_WORK=out/rs2 python tools/refstudy2/prereg_metrics.py
Saída: WORK/prereg_baseline.json e tabela no stdout.
"""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "refstudy")); sys.path.insert(0, HERE)
import numpy as np
from scipy.ndimage import gaussian_filter1d
import measure, shape
from _paths import WORK

S = 1700.0
ZS = np.arange(0.44 * S, 0.84 * S + 1e-6, 5.0)
# janelas congeladas (fração da estatura)
W_THORAX, W_LUMBAR, W_PELVIS = (0.70, 0.78), (0.60, 0.68), (0.50, 0.58)
W_CHEST, W_DELT = (0.72, 0.80), (0.79, 0.83)


# ----------------------------------------------------------------------------- instrumento
def slices(V, T, lab):
    rows = []
    for z0 in ZS:
        m, xa, ya = shape.torso_mask(V, T, lab, z0)
        if m is None:
            continue
        r = shape.describe(m, xa, ya); r["z"] = float(z0); rows.append(r)
    return rows


def arr(rows, k):
    return np.array([r[k] for r in rows], float)


def fit_angle(z, y, lo, hi):
    """Ângulo (graus) da reta y(z) na janela; + = a superfície vai para TRÁS (−y) ao subir."""
    m = (z >= lo * S) & (z <= hi * S) & np.isfinite(y)
    if m.sum() < 4:
        return np.nan
    b = np.polyfit(z[m], y[m], 1)[0]
    return float(np.degrees(np.arctan(-b)))


def all_width(V, T_full, lab, lo, hi):
    """Largura máxima do corte com TODAS as peças (bideltoide: braços incluídos)."""
    best = 0.0
    for z0 in np.arange(lo * S, hi * S + 1e-6, 5.0):
        g = measure.slice_grid(V, T_full, lab, z0, (-400, 400), (-300, 300))
        if g is None or not g.any():
            continue
        ix = np.nonzero(g.any(0))[0]
        best = max(best, (ix.max() - ix.min() + 1) * measure.RES)
    return best


def metrics(V, T, lab, *, T_full=None):
    R = slices(V, T, lab)
    z = arr(R, "z")
    mb = gaussian_filter1d(arr(R, "mid_back"), 2.0)
    cy = gaussian_filter1d(arr(R, "cy"), 2.0)
    w, d = arr(R, "width"), arr(R, "depth")
    M = {}
    # ---- classe D: geometria direta, independente do referencial
    # peito AO NÍVEL DO PONTO DO BUSTO (definição ANSUR): cota da profundidade máxima do tórax
    mc = (z >= W_CHEST[0] * S) & (z <= W_CHEST[1] * S)
    k = int(np.argmax(np.where(mc, d, -np.inf)))
    M["D1_chest_breadth"] = float(w[k]); M["D1_chest_z"] = float(z[k])
    M["D2_chest_depth"] = float(d[k])
    mw = (z >= 0.58 * S) & (z <= 0.72 * S); mh = (z >= 0.46 * S) & (z <= 0.58 * S)
    M["D3_waist_depth_min"] = float(np.min(d[mw])); M["D3_buttock_depth_max"] = float(np.max(d[mh]))
    M["D4_hip_breadth_max"] = float(np.max(w[mh]))
    M["D5_chest_over_hip"] = M["D1_chest_breadth"] / M["D4_hip_breadth_max"]
    M["D6_chestdepth_over_waistdepth"] = M["D2_chest_depth"] / M["D3_waist_depth_min"]
    M["D6_buttockdepth_over_waistdepth"] = M["D3_buttock_depth_max"] / M["D3_waist_depth_min"]
    if T_full is not None:
        M["D7_bideltoid"] = all_width(V, T_full, lab, *W_DELT)
        M["D7_chest_over_bideltoid"] = M["D1_chest_breadth"] / M["D7_bideltoid"]
    # ---- classe P: perfil posterior da linha média (imune à massa anterior por construção)
    # marcos: ápice glúteo G, ápice torácico Tt (pontos mais posteriores), ponto lombar L
    # (mais anterior em relação à corda G–Tt).  Ângulos das CORDAS G→L e L→Tt.
    it = int(np.argmin(np.where((z >= 0.68 * S) & (z <= 0.82 * S), mb, np.inf)))
    ig = int(np.argmin(np.where((z >= 0.44 * S) & (z <= 0.58 * S), mb, np.inf)))
    mm = (z > z[ig]) & (z < z[it])
    chord = mb[ig] + (z[mm] - z[ig]) / (z[it] - z[ig]) * (mb[it] - mb[ig])
    kk = int(np.argmax(mb[mm] - chord)); il = int(np.nonzero(mm)[0][kk])
    M["P4_thoracic_apex_z"] = float(z[it]); M["P4_gluteal_apex_z"] = float(z[ig]); M["P5_lumbar_z"] = float(z[il])
    M["P5_lumbar_concavity_vs_chord"] = float((mb[mm] - chord)[kk])
    ang = lambda i, j: float(np.degrees(np.arctan2(mb[j] - mb[i], z[j] - z[i])))   # + = topo mais À FRENTE
    M["P1_pelvic_chord_angle"] = ang(ig, il)            # G→L: + = segmento pélvico inclinado p/ a frente
    M["P2_thoracic_chord_angle"] = -ang(il, it)         # L→Tt: + = segmento torácico inclinado p/ trás
    M["P3_lumbar_bend_angle"] = M["P1_pelvic_chord_angle"] + M["P2_thoracic_chord_angle"]   # invariante rígida
    M["P6_glute_minus_thoracic_apex_y"] = float(mb[ig] - mb[it])   # + = nádega À FRENTE (sensível a rotação)
    tz, ty = z[ig:it + 1], mb[ig:it + 1]
    a2 = np.arctan2(np.diff(ty), np.diff(tz))
    M["P7_back_turning_total_deg"] = float(np.degrees(np.sum(np.abs(np.diff(a2))))) if len(a2) > 2 else np.nan
    # ---- classe C: dependem do centroide (massa anterior incluída)
    M["C1_axis_thorax"] = fit_angle(z, cy, *W_THORAX)
    M["C2_axis_pelvis"] = fit_angle(z, cy, *W_PELVIS)
    M["C3_axis_lumbar"] = fit_angle(z, cy, *W_LUMBAR)
    M["C4_axis_rel_thorax_minus_pelvis"] = M["C1_axis_thorax"] - M["C2_axis_pelvis"]
    # ---- classe F: posições absolutas (dependem do referencial) — só relatório
    M["F1_mid_back_at_thoracic_apex_y"] = float(mb[it]); M["F2_cy_at_chest_y"] = float(cy[k])
    return M


# ----------------------------------------------------------------------------- transformações de teste
def rot_x(V, deg, pivot_z=0.52 * S):
    a = np.radians(deg); c, s = np.cos(a), np.sin(a)
    P = V.copy(); y, zz = P[:, 1], P[:, 2] - pivot_z
    P[:, 1] = c * y - s * zz; P[:, 2] = s * y + c * zz + pivot_z
    return P


def load(name):
    """(V, T do tronco sem as peças descartadas, lab, T completo)."""
    V, T, lab = shape.normalised(name, shape.MODELS[name])
    opt = dict(shape.MODELS[name]); opt.pop("drop", None)
    _, T_full, _ = shape.normalised(name, opt)
    return V, T, lab, T_full


if __name__ == "__main__":
    out = {"windows": dict(thorax=W_THORAX, lumbar=W_LUMBAR, pelvis=W_PELVIS, chest=W_CHEST, deltoid=W_DELT)}
    for name in ("ours", "femalebase", "femalechar", "bodytopo"):
        V, T, lab, T_full = load(name)
        TF = T_full if name == "ours" else None      # refs em T/A-pose: bideltoide inválido
        base = metrics(V, T, lab, T_full=TF)
        rec = {"base": base}
        if name == "ours":
            # ruído de amostragem: jitter sub-pixel (grelha de 2 mm, passos de 5 mm)
            jit = []
            for dx, dy, dz in ((0.5, 0.7, 1.3), (-0.9, 0.3, 2.1), (0.2, -1.1, 3.4), (1.0, 1.0, -1.7)):
                Vj = V + np.array([dx, dy, dz]); jit.append(metrics(Vj, T, lab, T_full=TF))
            rec["jitter_sd"] = {k: float(np.std([j[k] for j in jit] + [base[k]])) for k in base}
            rec["translate_y+25"] = {k: v - base[k] for k, v in metrics(V + np.array([0, 25.0, 0]), T, lab, T_full=TF).items()}
            rec["rotate_x+3deg"] = {k: v - base[k] for k, v in metrics(rot_x(V, 3.0), T, lab, T_full=TF).items()}
        out[name] = rec
        print("done", name, flush=True)
    json.dump(out, open(os.path.join(WORK, "prereg_baseline.json"), "w"), indent=1)
    o = out["ours"]
    keys = list(o["base"].keys())
    print(f"\n{'métrica':36s}{'ours':>9s}{'fbase':>9s}{'fchar':>9s}{'btopo':>9s} | {'jitSD':>6s}{'ΔT+25y':>8s}{'ΔR+3°':>8s}")
    for k in keys:
        refs = [out[n]["base"].get(k, np.nan) for n in ("femalebase", "femalechar", "bodytopo")]
        print(f"{k:36s}{o['base'][k]:9.2f}" + "".join(f"{v:9.2f}" for v in refs)
              + f" | {o['jitter_sd'][k]:6.2f}{o['translate_y+25'][k]:8.2f}{o['rotate_x+3deg'][k]:8.2f}")
