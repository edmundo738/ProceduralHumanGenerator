# -*- coding: utf-8 -*-
"""plane_scan v3.2 — secções por RASTERIZAÇÃO de segmentos (MANDATO RND).

Instrumento de "visão computacional" para comparar malhas sem janelas de
vértices (que MENTEM entre malhas — cobertura topológica varia; memória
MECHANISM_AUDIT_01).  Todos os números de mama/torso vêm daqui.

v3 (binning directo, sem geom.fill): o fill encadeava segmentos em polígonos
e, quando o encadeamento falhava (prega inframamária: a pele DESCE antes de
subir à mama), fechava o polígono errado → topo fantasma +24 mm (medido vs
segmentos crus).  Amostra cada segmento na grelha de colunas (passo RES) e
toma o máx y por coluna.

v3.1: corte com OFFSET sub-bin (z0 + 0.37·RES) — plano EXACTO em coordenada
de vértice dá intersecções degeneradas (medido: swB2 tem vértices em x=±63.0
exactos; o sagital x=63 perdia segmentos ao longo da coluna toda).

v3.2: repair_front — refs fragmentadas (real005: 69 comps, buracos de scan)
deixam colunas só-costas; queda >40 mm da mediana rolante → NaN; buracos
≤25 mm tapados; curva cortada onde a frente termina.

Uso (ver breast_spec.py para a tabela de especificação):
    from plane_scan import load, section_top, section_top_plane
"""
import os

import numpy as np

import geom

RES = 2.0   # mm por coluna


def _top_from_segments(V, T, z0, c0, c1, r_lo, r_hi):
    """Secção no plano 'z'=z0 com colunas em eixo c0 e linhas em eixo c1.

    Devolve (coords_coluna, y_topo) onde y é o 3.º eixo.  r_lo/hi: extent
    das colunas (eixo c0).
    """
    segs = geom.slice_segments(V, T, z0 + 0.37 * RES)   # evita plano degenerado
    if segs is None or len(segs) == 0:
        segs = geom.slice_segments(V, T, z0)
        if segs is None or len(segs) == 0:
            return None, None
    col_lo = np.floor(segs[:, :, 0].min() / RES) * RES
    col_hi = np.ceil(segs[:, :, 0].max() / RES) * RES
    n = max(4, int((col_hi - col_lo) / RES) + 1)
    top = np.full(n, np.nan)
    for s in segs:
        (a0, b0), (a1, b1) = s[0], s[1]
        k = max(2, int(abs(a1 - a0) / RES) + 1)
        cs = np.linspace(a0, a1, k)
        ys = np.linspace(b0, b1, k)
        idx = np.clip(((cs - col_lo) / RES).astype(int), 0, n - 1)
        for j, i in enumerate(idx):
            if np.isnan(top[i]) or ys[j] > top[i]:
                top[i] = ys[j]
    xs = np.arange(n) * RES + col_lo + RES * 0.5
    ok = ~np.isnan(top)
    m = ok & (xs >= r_lo) & (xs <= r_hi)
    return xs[m], top[m]


def fill_gaps(x, y, max_gap=25.0):
    """Interpola buracos ≤ max_gap mm (refs fragmentadas: colunas sem segmento).

    O binning directo (v3) não inventa valores onde a malha tem falhas —
    esta função tapa só os buracos CURTOS; buracos maiores ficam NaN.
    """
    x = np.array(x, dtype=float)
    y = np.array(y, dtype=float)
    bad = np.where(np.isnan(y))[0]
    for i in bad:
        lo = np.where(~np.isnan(y[:i]))[0]
        hi = np.where(~np.isnan(y[i + 1:]))[0] + (i + 1)
        if len(lo) and len(hi) and x[hi[0]] - x[lo[-1]] <= max_gap:
            y[i] = np.interp(x[i], [x[lo[-1]], x[hi[0]]], [y[lo[-1]], y[hi[0]]])
    return x, y


def repair_front(x, y, win=8, drop=40.0, max_gap=25.0):
    """Reparo por contexto da curva frontal (top).

    Colunas cujo topo fica > drop mm ABAIXO da mediana rolante (±win colunas)
    são buracos de scan (só-costas) ou degenerescências → NaN; buracos curtos
    são tapados (fill_gaps); a curva é cortada onde começa/termina a frente
    real.  Medido sem reparo: real005 sagital dava −18@z1230 entre 72@1215 e
    90@1245 (buraco de scan); swN0 secção dava −89@x121 entre 67 e 57.
    """
    x = np.array(x, dtype=float)
    y = np.array(y, dtype=float)
    if len(y) < 3:
        return x, y
    med = np.array([np.nanmedian(y[max(0, i - win):i + win + 1])
                    for i in range(len(y))])
    y[y < med - drop] = np.nan
    x, y = fill_gaps(x, y, max_gap)
    ok = ~np.isnan(y)
    if ok.any():
        i0, i1 = np.where(ok)[0][[0, -1]]
        return x[i0:i1 + 1], y[i0:i1 + 1]
    return x, y


def _swap(V, T, axis):
    """Troca eixos para fatiar num plano que não seja z."""
    if axis == 2:
        return V, T
    if axis == 0:                    # plano x=const: novo z = x
        V2 = V[:, [2, 1, 0]]         # (z→x, y→y, x→z): colunas=z, linhas=y
    else:                            # plano y=const: novo z = y
        V2 = V[:, [0, 2, 1]]
    return np.ascontiguousarray(V2), T


def section_top(V, T, z0, x_lo=-340.0, x_hi=340.0):
    """(x, y_topo) da secção horizontal em z=z0 (frente = topo, reparada)."""
    out = _top_from_segments(V, T, z0, 0, 2, x_lo, x_hi)
    if out[0] is None:
        return out
    return repair_front(*out)


def section_top_plane(V, T, x0, z_lo=600.0, z_hi=1500.0):
    """(z, y_topo) da secção x=x0 (colunas=z, topo=y, reparada)."""
    V2, T2 = _swap(V, T, 0)
    out = _top_from_segments(V2, T2, x0, 2, 0, z_lo, z_hi)
    if out[0] is None:
        return out
    return repair_front(*out)


def normalise(V, flip=False, stature=1700.0):
    V = V.copy()
    S = V[:, 2].max() - V[:, 2].min()
    V[:, 2] -= V[:, 2].min()
    V[:, 0] -= (V[:, 0].max() + V[:, 0].min()) / 2
    V *= stature / S
    if flip:
        V[:, 1] *= -1
    return V


def load(name, flip=False, work=None):
    from _paths import WORK
    w = work or WORK
    d = np.load(os.path.join(w, f"raw_{name}.npz"))
    return normalise(d["V"], flip), d["T"]
