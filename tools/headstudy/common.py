"""HEAD STUDY 01 — normalização, cortes e marcos (numpy puro).

Referencial comum (declarado): +z = cima, +y = frente, x = lateral.
Escala: altura da cabeça H = vértex − mentón, apresentada em mm a H = 226.1 mm
(a H do nosso realistic_female: estatura 1.70 / 7.52).  Origem: z = 0 no mentón,
y = 0 no ponto médio glabela–opistocrânio, x = 0 no plano sagital.

Os marcos são detetados AUTOMATICAMENTE e da mesma forma em todas as fontes; as
figuras de verificação (fig_landmarks.png) servem para confirmar visualmente.
"""
import os, sys, json
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tools", "refstudy"))
import geom  # noqa: E402

WORK = os.environ.get("HCG_HEAD_WORK", os.path.join(ROOT, "out", "head"))
H_MM = 226.1
NAMES = ["ours", "whitewalker", "makehuman", "femalechar", "bodytopo", "femalebase", "ff11"]
LABEL = {"ours": "NOSSA (e7df112)", "whitewalker": "whitewalker", "makehuman": "MakeHuman (Lucia fbx)",
         "femalechar": "FemaleCharacter", "bodytopo": "Body Topo", "femalebase": "Female base", "ff11": "fffemale 11"}

# orientação: matriz que leva (x,y,z) da fonte para (x',y',z') comum; det = +1
ORIENT = {
    "ours": [[1, 0, 0], [0, 1, 0], [0, 0, 1]],
    "whitewalker": [[-1, 0, 0], [0, -1, 0], [0, 0, 1]],
    "makehuman": [[-1, 0, 0], [0, 0, -1], [0, -1, 0]],
    "femalechar": [[-1, 0, 0], [0, -1, 0], [0, 0, 1]],
    "bodytopo": [[-1, 0, 0], [0, -1, 0], [0, 0, 1]],
    "femalebase": [[1, 0, 0], [0, 1, 0], [0, 0, 1]],
    "ff11": [[1, 0, 0], [0, 1, 0], [0, 0, 1]],
}
# altura aproximada da cabeça em unidades da fonte (só para janelas de procura;
# a H usada é a MEDIDA vértex−mentón)
H0 = {"ours": 0.226, "whitewalker": 0.21, "makehuman": 2.3, "femalechar": 7.5, "bodytopo": 0.22,
      "femalebase": 0.26, "ff11": 1.1}


def ours_skin_components(V, T):
    """Ilhas da NOSSA malha que equivalem à pele das referências.

    FACT (medido): a nossa cabeça é 1 casca craniana + ~40 ilhas (orelhas, globo,
    córnea, 2 pálpebras por olho, lábios, gengiva, arcadas, 28 dentes, língua).
    Nas referências os globos/dentes são objetos à parte (não exportados), logo
    para comparar a PELE mantêm-se: casca, orelhas, pálpebras e lábios.
    Regra: exclui ilhas com centróide a < 3 mm (x,z) do centro de um globo
    (globo, córnea) e as ilhas da boca exceto a mais anterior (lábios)."""
    lab = geom.components(V, T)
    n = lab.max() + 1
    cen = np.array([V[lab == c].mean(0) for c in range(n)])
    top = V[:, 2].max()
    head = [c for c in range(n) if V[lab == c][:, 2].max() > top - 0.30 and V[lab == c][:, 2].min() > top - 0.30]
    big = [c for c in range(n) if V[lab == c][:, 2].max() > top - 0.02]           # casca craniana (e tronco)
    eyes = []
    for sx in (1, -1):
        cand = [c for c in head if abs(cen[c, 0] - sx * 0.0305) < 0.004 and V[lab == c][:, 2].ptp() < 0.030]
        if not cand:
            continue
        globe = max(cand, key=lambda c: (lab == c).sum())          # o globo é a maior ilha do olho
        eyes += [c for c in cand if abs(cen[c, 2] - cen[globe, 2]) < 0.002]   # globo + córnea (pálpebras ficam)
    mouth = [c for c in head if abs(cen[c, 0]) < 0.030 and abs(cen[c, 2] - (top - 0.187)) < 0.010]
    lips = max(mouth, key=lambda c: cen[c, 1]) if mouth else None
    drop = set(eyes) | (set(mouth) - {lips})
    return lab, drop


def load_raw(name, tag="smooth"):
    d = np.load(os.path.join(WORK, f"{name}_{tag}.npz"))
    M = np.array(ORIENT[name], float)
    V = d["V"] @ M.T
    T = d["T"]
    if name == "ours":
        lab, drop = ours_skin_components(d["V"], T)
        keep = ~np.isin(lab, list(drop))
        T = T[keep[T[:, 0]]]
    return V, T, d["fs"], d["fi"]


def front_profile(V, T, lo, hi, step, x_off=None):
    """Perfil sagital: segmentos do corte x = x_off → (y,z); frente = max y por faixa de z.

    O plano fica deslocado 0.001·(hi−lo) da linha média: nas malhas com MIRROR as
    arestas da costura estão EXATAMENTE em x = 0 e o corte perdia segmentos
    (verificado em fig de controlo: whitewalker/FemaleCharacter/Body Topo sem nuca).
    """
    P = V[:, [1, 2, 0]]
    off = (hi - lo) * 1e-3 if x_off is None else x_off
    segs = geom.slice_segments(P, T, off)
    S = np.asarray(segs).reshape(-1, 2, 2) if len(segs) else np.zeros((0, 2, 2))
    pts = S.reshape(-1, 2)
    zs = np.arange(lo, hi, step)
    yf, yb = _cross(S, zs)
    return zs, yf, yb, pts


def _cross(S, zs):
    """Interseção EXATA de cada segmento (y,z) com cada cota z (não só extremidades:
    medido, os segmentos da frente são mais longos que a faixa e o perfil ficava
    com a frente vazia em 105/340 faixas)."""
    yf = np.full(len(zs), np.nan); yb = np.full(len(zs), np.nan)
    if not len(S):
        return yf, yb
    a, b = S[:, 0], S[:, 1]
    zlo, zhi = np.minimum(a[:, 1], b[:, 1]), np.maximum(a[:, 1], b[:, 1])
    for i, z in enumerate(zs):
        m = (zlo <= z) & (zhi >= z) & (zhi - zlo > 1e-12)
        if not m.any():
            continue
        t = (z - a[m, 1]) / (b[m, 1] - a[m, 1])
        y = a[m, 0] + t * (b[m, 0] - a[m, 0])
        yf[i] = y.max(); yb[i] = y.min()
    return yf, yb


def _interp_nan(a):
    a = a.copy(); i = np.arange(len(a)); g = ~np.isnan(a)
    if g.sum() >= 2:
        a[~g] = np.interp(i[~g], i[g], a[g])
    return a


def normalise(name, tag="smooth"):
    """Devolve (V_norm em mm@H226, T, info com marcos sagitais)."""
    V, T, fs, fi = load_raw(name, tag)
    h0 = H0[name]
    top = V[:, 2].max()
    zs, yf, yb, _ = front_profile(V, T, top - 1.45 * h0, top, h0 / 400)
    yf = _interp_nan(yf)
    k = lambda z: int(np.argmin(np.abs(zs - z)))
    # pronasale: máximo da frente na banda média da cabeça
    band = (zs > top - 0.85 * h0) & (zs < top - 0.45 * h0)
    i_prn = int(np.nonzero(band)[0][np.argmax(yf[band])])
    # mentón: descendo a partir de prn − 0.28·H0, o primeiro ponto em que a
    # tangente do perfil passa de 45° (dy/dz > 1): transição queixo → submento
    from scipy.ndimage import gaussian_filter1d
    ys = gaussian_filter1d(yf, 3)
    dy = np.gradient(ys, zs)
    i0 = k(zs[i_prn] - 0.28 * h0)
    i_me = None
    for i in range(i0, 0, -1):
        if dy[i] > 1.0:
            i_me = i; break
    info_fallback = None
    if i_me is None:
        # malha grossa (declarado): sem tangente a 45°, usa-se o declive máximo
        # numa janela de 0.30·H0 abaixo do início da procura
        lo_i = k(zs[i0] - 0.30 * h0)
        i_me = lo_i + int(np.argmax(dy[lo_i:i0])); info_fallback = "max_slope"
    z_me = zs[i_me]
    H = top - z_me
    s = H_MM / H
    Vn = V.copy()
    Vn[:, 2] = (V[:, 2] - z_me) * s
    Vn[:, 0] = V[:, 0] * s
    Vn[:, 1] = V[:, 1] * s
    info = {"H_src_units": float(H), "scale": float(s), "z_menton_src": float(z_me), "menton_rule": info_fallback or "tangent_45"}
    # recorte: cabeça + pescoço (até −0.45 H) e sem ombros (|x| < 0.62 H)
    keep = (Vn[:, 2] > -0.45 * H_MM) & (np.abs(Vn[:, 0]) < 0.62 * H_MM)
    Tk = T[keep[T].all(1)]
    # origem y: ponto médio glabela–opistocrânio (comprimento máximo da cabeça)
    zs2, yf2, yb2, pts = front_profile(Vn, Tk, -0.45 * H_MM, H_MM + 1, 1.0)
    yf2 = _interp_nan(yf2); yb2 = _interp_nan(yb2)
    up = zs2 > 0.55 * H_MM
    L = yf2 - yb2
    i_len = int(np.nonzero(up)[0][np.argmax(np.where(up, L, -1)[up])])
    y0 = 0.5 * (yf2[i_len] + yb2[i_len])
    Vn[:, 1] -= y0
    info["y0_mm_before"] = float(y0)
    return Vn, Tk, fs, fi, info


def sagittal_landmarks(Vn, T):
    """Marcos do perfil médio (mm@H226, z acima do mentón, y à frente do centro craniano)."""
    zs, yf, yb, pts = front_profile(Vn, T, -0.45 * H_MM, H_MM + 1, 1.0)
    yf = _interp_nan(yf); yb = _interp_nan(yb)
    from scipy.ndimage import gaussian_filter1d
    ysm = gaussian_filter1d(yf, 1.5)
    k = lambda z: int(np.argmin(np.abs(zs - z)))
    def arg(fn, lo, hi, arr=ysm):
        m = (zs >= lo) & (zs <= hi)
        idx = np.nonzero(m)[0]
        return int(idx[fn(arr[m])])
    L = {}
    L["vertex"] = (float(np.nan), float(zs[np.nanargmax(np.where(np.isnan(yf), -1e9, zs))]))
    i_prn = arg(np.argmax, 0.30 * H_MM, 0.55 * H_MM); L["pronasale"] = (ysm[i_prn], zs[i_prn])
    i_n = arg(np.argmin, zs[i_prn] + 0.05 * H_MM, zs[i_prn] + 0.30 * H_MM); L["nasion"] = (ysm[i_n], zs[i_n])
    i_g = arg(np.argmax, zs[i_n] + 0.02 * H_MM, zs[i_n] + 0.14 * H_MM); L["glabella"] = (ysm[i_g], zs[i_g])
    i_sn = arg(np.argmin, zs[i_prn] - 0.12 * H_MM, zs[i_prn] - 0.01 * H_MM); L["subnasale"] = (ysm[i_sn], zs[i_sn])
    i_ls = arg(np.argmax, zs[i_sn] - 0.12 * H_MM, zs[i_sn] - 0.01 * H_MM); L["labrale_sup"] = (ysm[i_ls], zs[i_ls])
    i_sto = arg(np.argmin, zs[i_ls] - 0.06 * H_MM, zs[i_ls] - 0.003 * H_MM); L["stomion"] = (ysm[i_sto], zs[i_sto])
    i_li = arg(np.argmax, zs[i_sto] - 0.07 * H_MM, zs[i_sto] - 0.003 * H_MM); L["labrale_inf"] = (ysm[i_li], zs[i_li])
    i_sm = arg(np.argmin, max(zs[i_li] - 0.09 * H_MM, 0.05 * H_MM), zs[i_li] - 0.005 * H_MM); L["sulcus_mentolabial"] = (ysm[i_sm], zs[i_sm])
    i_pg = arg(np.argmax, 0.0, zs[i_sm]); L["pogonion"] = (ysm[i_pg], zs[i_pg])
    L["menton"] = (ysm[k(0.0)], 0.0)
    i_c = arg(np.argmin, -0.30 * H_MM, -0.05 * H_MM); L["cervical"] = (ysm[i_c], zs[i_c])
    # traseira: opistocrânio (máx. comprimento), ínion aproximado e nuca (mais anterior)
    up = zs > 0.55 * H_MM
    i_op = int(np.nonzero(up)[0][np.argmin(yb[up])]); L["opisthocranion"] = (yb[i_op], zs[i_op])
    nk = (zs > -0.30 * H_MM) & (zs < zs[i_op] - 0.1 * H_MM)
    i_nk = int(np.nonzero(nk)[0][np.argmax(yb[nk])]); L["nape_recess"] = (yb[i_nk], zs[i_nk])
    L = {k_: (float(a), float(b)) for k_, (a, b) in L.items()}
    return L, (zs, yf, yb, pts)


def hsection(Vn, T, z):
    segs = geom.slice_segments(Vn, T, z)
    return np.asarray(segs).reshape(-1, 2, 2) if len(segs) else np.zeros((0, 2, 2))


def front_contour(Vn, T, z, xs, ymin=None):
    """y da frente (máximo) do corte horizontal em cada x de ``xs`` (NaN sem pele).
    ``ymin``: só conta pele à frente de ymin (numa abertura sem pele o corte batia
    na nuca — medido: recessos "orbitários" de ~180 mm nas refs com olho à parte)."""
    S = hsection(Vn, T, z)
    out = np.full(len(xs), np.nan)
    if not len(S):
        return out
    a, b = S[:, 0], S[:, 1]
    for i, x in enumerate(xs):
        lo, hi = np.minimum(a[:, 0], b[:, 0]), np.maximum(a[:, 0], b[:, 0])
        m = (lo <= x) & (hi >= x) & (hi - lo > 1e-9)
        if not m.any():
            continue
        t = (x - a[m, 0]) / (b[m, 0] - a[m, 0])
        y = a[m, 1] + t * (b[m, 1] - a[m, 1])
        if ymin is not None:
            y = y[y > ymin]
        if len(y):
            out[i] = y.max()
    return out


def column_profile(Vn, T, x, lo, hi, step=1.0):
    """Perfil vertical da frente num plano sagital deslocado x = const."""
    P = Vn[:, [1, 2, 0]].copy(); P[:, 2] -= x
    segs = geom.slice_segments(P, T, 0.0)
    S = np.asarray(segs).reshape(-1, 2, 2) if len(segs) else np.zeros((0, 2, 2))
    zs = np.arange(lo, hi, step)
    yf, _ = _cross(S, zs)
    return zs, yf
