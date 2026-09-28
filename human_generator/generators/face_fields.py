# -*- coding: utf-8 -*-
"""HEAD FASE B/C/D — campos anatómicos da face (massas, cavidades, traços).

A superfície da cabeça é ``r(u) = r_massas(u) + F(u)`` (raio visto do centro
comum da casca de massas, ``head_mass.CENTRE``).  ``F`` é uma soma de campos
com NOME anatómico — sobrancelha, órbita, pálpebras, dorso/ponta/asas do nariz,
filtro, lábios, sulcos, malar, queixo, orelha … — cada um uma função analítica
da direção ``u`` (coordenadas ``X, Y, Z = 100·u``: "mm a 100 mm do centro").

Os PARÂMETROS vêm do ajuste por mínimos quadrados ao alvo facial estatístico
(média alinhada por marcos de femalebase/bodytopo/femalechar,
``tools/headface/face_target.py`` → ``tools/headface/fit_face.py``).  O gerador
não lê nenhuma malha nem mapa das refs: só esta tabela de parâmetros.

O mesmo código corre em Python puro (gerador) e em numpy (ajuste): as funções
recebem o espaço de nomes ``xp`` (``math``-like ou ``numpy``).

Tipos:
  blob  (frame, sym, x0, z0, a, b, th, A, p)
        A·exp(−d^p), d = distância elíptica rodada (p grande ⇒ planalto de bordo nítido)
  ridge (frame, sym, x0, z0, th, L, c, w, A0, A1)
        crista/sulco ao longo da parábola v = c·u² (|u| ≤ L), secção gaussiana de
        meia-largura w, amplitude linear A0 → A1 ao longo de u
frame "F": plano frontal (X, Z), portão Y > 0 (só a metade da frente)
frame "S": plano lateral (Y, Z) do lado +X (orelhas), portão |X| grande
sym = 1: par espelhado (usa |X|).
"""
from __future__ import annotations

import math


class _PyXP:
    exp = staticmethod(math.exp)
    sqrt = staticmethod(math.sqrt)
    cos = staticmethod(math.cos)
    sin = staticmethod(math.sin)
    abs = staticmethod(abs)

    @staticmethod
    def maximum(a, b):
        return a if a > b else b

    @staticmethod
    def minimum(a, b):
        return a if a < b else b

    @staticmethod
    def clip(a, lo, hi):
        return lo if a < lo else hi if a > hi else a

    arctan2 = staticmethod(math.atan2)

    @staticmethod
    def arcsin(a):
        return math.asin(max(-1.0, min(1.0, a)))

    @staticmethod
    def where(c, a, b):
        return a if c else b


PYXP = _PyXP()

BLOB_KEYS = ("x0", "z0", "a", "b", "th", "A", "p")
RIDGE_KEYS = ("x0", "z0", "th", "L", "c", "w", "A0", "A1")


def _sig(xp, t):
    return 1.0 / (1.0 + xp.exp(-xp.clip(t, -40.0, 40.0)))


def coords(xp, ux, uy, uz):
    """(H, Y, V, X): H = 100·az·cos(el) (frontal desdobrado — não satura nos lados),
    V = 100·el (rad), Y/X = 100·u (para o plano lateral e os portões)."""
    az = xp.arctan2(ux, uy)
    ce = xp.sqrt(ux * ux + uy * uy)
    return 100.0 * az * ce, 100.0 * uy, 100.0 * xp.arcsin(uz), 100.0 * ux


def _frame(xp, frame, sym, C):
    H, Y, V, X = C
    if frame == "F":
        h = xp.sqrt(H * H + 0.04) if sym else H
        return h, V, _sig(xp, (Y - 20.0) / 5.0)          # só a face (az < ~78°)
    # lateral: orelha do lado +X (sym ⇒ ambos)
    s = xp.sqrt(X * X + 0.04) if sym else X
    return Y, V, _sig(xp, (s - 45.0) / 4.0)


def blob(xp, frame, sym, P, C):
    x0, z0, a, b, th, A, p = P
    h, v, g = _frame(xp, frame, sym, C)
    c, s = math.cos(th), math.sin(th)
    du, dv = h - x0, v - z0
    uu = (c * du + s * dv) / a
    vv = (-s * du + c * dv) / b
    d2 = uu * uu + vv * vv
    return A * g * xp.exp(-(d2 + 1e-12) ** (0.5 * p))


def ridge(xp, frame, sym, P, C):
    x0, z0, th, L, c2, w, A0, A1 = P
    h, v, g = _frame(xp, frame, sym, C)
    c, s = math.cos(th), math.sin(th)
    du, dv = h - x0, v - z0
    uu = c * du + s * dv
    vv = -s * du + c * dv
    dist = (vv - c2 * uu * uu) / xp.sqrt(1.0 + 4.0 * c2 * c2 * uu * uu)
    t = uu / L
    win = xp.exp(-(t * t) ** 4)
    amp = A0 + (A1 - A0) * 0.5 * (xp.clip(t, -1.0, 1.0) + 1.0)
    return amp * g * win * xp.exp(-(dist / w) ** 2)


def field(xp, prims, ux, uy, uz):
    """Soma dos campos.  ``prims`` = sequência de (nome, tipo, frame, sym, params)."""
    C = coords(xp, ux, uy, uz)
    total = 0.0
    for _name, kind, frame, sym, P in prims:
        f = blob if kind == "blob" else ridge
        total = total + f(xp, frame, sym, P, C)
    return total


# --------------------------------------------------------------------------- olho
# Globo + fenda palpebral + pálpebras (NÃO ajustado: medido nas refs).
#   globo: esfera de raio EYE_RL (= globo 12.0 + margem 0.5) com centro medido
#          (``tools/headface/globe.py``: esfera R = 12.5 ajustada ao laço da margem
#          palpebral de cada ref; média de 3).
#   fenda: amêndoa entre os cantos interno/externo, limites superior/inferior que
#          passam pelos marcos médios da pálpebra (``face_landmarks.json``), em
#          coordenadas (H, V) do frontal desdobrado.
#   pele:  dentro da fenda fica ATRÁS do globo (o globo vê-se); fora, as pálpebras
#          assentam no globo (+ espessura) e fundem-se no campo da face.
def globe_radius(xp, ux, uy, uz, centre, G, R):
    """Raio (visto do centro comum) da saída do raio na esfera (G, R); continuação
    pelo ponto de maior aproximação quando o raio não a interseta."""
    ox, oy, oz = centre[0] - G[0], centre[1] - G[1], centre[2] - G[2]
    b = -(ox * ux + oy * uy + oz * uz)
    c = ox * ox + oy * oy + oz * oz - R * R
    disc = b * b - c
    return b + xp.sqrt(xp.maximum(disc, 0.0)) - 0.5 * xp.sqrt(xp.maximum(-disc, 0.0))


def fissure_distance(xp, H, V, E):
    """Distância (unidades H,V) para fora da fenda: < 0 dentro."""
    en, ex = E["en"], E["ex"]
    dx, dz = ex[0] - en[0], ex[1] - en[1]
    Lc = math.sqrt(dx * dx + dz * dz)
    tx, tz = dx / Lc, dz / Lc
    ph, pv = H - en[0], V - en[1]
    t = (ph * tx + pv * tz) / Lc
    n = -ph * tz + pv * tx
    tc = xp.clip(t, 1e-4, 1.0 - 1e-4)
    up = E["Hu"] * xp.sin(math.pi * tc ** E["gu"])
    lo = -E["Hl"] * xp.sin(math.pi * tc ** E["gl"])
    d_v = xp.maximum(n - up, lo - n)
    d_t = xp.maximum(-t * Lc, (t - 1.0) * Lc)
    return xp.maximum(d_v, d_t), n


def _canthus_t(xp, H, V, E):
    en, ex = E["en"], E["ex"]
    dx, dz = ex[0] - en[0], ex[1] - en[1]
    Lc = math.sqrt(dx * dx + dz * dz)
    t = ((H - en[0]) * dx + (V - en[1]) * dz) / (Lc * Lc)
    return xp.maximum(xp.maximum(-t * Lc, (t - 1.0) * Lc), 0.0)


def eye_zone_weight(xp, ux, uy, uz, E):
    """1 junto à fenda, 0 a partir de ~1.4·DZ: onde a camada estatística se cala."""
    H, _Y, V, _X = coords(xp, ux, uy, uz)
    d, _n = fissure_distance(xp, xp.sqrt(H * H + 1e-4), V, E)
    t = xp.clip((d - 1.0) / (1.4 * E["DZ"]), 0.0, 1.0)
    return 1.0 - t * t * (3.0 - 2.0 * t)


def eye_blend(xp, r_face, ux, uy, uz, centre, E):
    """Superfície final na região do olho (lado pelo sinal de ux; espelhado)."""
    H, _Y, V, _X = coords(xp, ux, uy, uz)
    Ha = xp.sqrt(H * H + 1e-4)
    G = E["G"]
    uxa = xp.sqrt(ux * ux + 1e-12)
    rg = globe_radius(xp, uxa, uy, uz, centre, G, E["RL"])
    d, n = fissure_distance(xp, Ha, V, E)
    # pálpebra: assenta no globo (espessura T0 na margem, cresce para fora), peso
    # decrescente até DZ (superior) / DZl (inferior)
    dz = xp.where(n > 0, E["DZ"], E["DZl"])
    dpos = xp.maximum(d, 0.0)
    r_lid = rg + E["T0"] + E["T1"] * dpos
    # janela dos cantos: para lá dos cantos não há globo por baixo ⇒ a pálpebra
    # deixa de mandar em ~CW unidades (OBSERVED: estrias laterais em f1_close_b)
    tt = _canthus_t(xp, Ha, V, E)
    W = xp.exp(-(dpos / dz) ** 2) * xp.exp(-(tt / E.get("CW", 2.5)) ** 2)
    r_out = r_face * (1.0 - W) + r_lid * W
    r_in = rg - E["GAP"]
    inside = d < 0
    return xp.where(inside, r_in, r_out), d


# ---------------------------------------------------------------- orelha v2 (CONT1)
# Construção INTEGRADA (docs/HEAD_CONT1.md): a orelha v1 era um planalto
# (blob p=5, bordo nítido = "placa colocada") + 5 campos + K estatístico
# (borrado: orelhas das refs mal alinhadas no interior).
# Medido (tools/headface/continuity.py, secção horizontal z=92.5, mm@H226):
#   turn das refs 571–993° vs nosso 462°  → relevo em falta;
#   protrusão média das refs: pico ~9–10 mm em y≈−25; nosso pico 13 mm em y−33.
# A v2 = JANELA C¹ (smoothstep elíptico: valor e declive nulos no bordo — a
# orelha funde-se na casca sem degrau) × (colina-base recentrada + relevo
# interno com concha mais funda e helix mais definida).  K cala-se na zona
# (ear_zone_weight) — o relevo passa a ser procedural, não estatístico.
EAR_V2 = {
    # janela C¹ em (Y, V): Y=100·uy (frente+), V=100·el[rad]
    "win": {"Yc": -25.0, "Vc": -18.0, "Ya": 24.0, "Va": 38.0},
    # zona onde a camada K se cala (ligeiramente para dentro da janela)
    "kz": {"Yc": -25.0, "Vc": -18.0, "Ya": 20.0, "Va": 33.0},
    "prims": [
        # nome, tipo, frame, sym, params — S: (h, v) = (Y, V)
        ("orelha_base", "blob", "S", 1, (-25.0, -20.0, 16.0, 30.0, 0.0, 6.2, 2.0)),
        ("helix", "ridge", "S", 1, (-33.0, -20.0, 1.6, 24.0, -0.0, 7.0, 3.8, 4.2)),
        ("antihelix", "ridge", "S", 1, (-21.6, -15.9, 1.4, 12.2, 0.0, 5.0, -2.6, -8.0)),
        ("concha", "blob", "S", 1, (-17.1, -26.3, 7.0, 10.5, -0.1, -16.0, 1.5)),
        ("tragus", "blob", "S", 1, (-11.8, -27.4, 3.3, 4.6, 0.1, 6.1, 1.5)),
        ("lobulo", "blob", "S", 1, (-18.0, -52.3, 6.0, 8.7, 0.5, 7.3, 3.0)),
    ],
}


def _ear_t(xp, ux, uy, uz, W):
    _H, Y, V, _X = coords(xp, ux, uy, uz)
    dy = (Y - W["Yc"]) / W["Ya"]
    dv = (V - W["Vc"]) / W["Va"]
    return xp.sqrt(dy * dy + dv * dv)


def ear_window(xp, ux, uy, uz):
    """1 dentro da orelha, 0 fora; smoothstep ⇒ C¹ no bordo (declive nulo)."""
    t = _ear_t(xp, ux, uy, uz, EAR_V2["win"])
    s = xp.clip((t - 0.7) / 0.3, 0.0, 1.0)
    return 1.0 - s * s * (3.0 - 2.0 * s)


def ear_zone_weight(xp, ux, uy, uz):
    """Peso da zona da orelha para onde a camada K se cala."""
    t = _ear_t(xp, ux, uy, uz, EAR_V2["kz"])
    s = xp.clip((t - 0.6) / 0.3, 0.0, 1.0)
    return 1.0 - s * s * (3.0 - 2.0 * s)


def ear_v2_field(xp, ux, uy, uz):
    """Orelha v2: janela C¹ × (base + relevo).  0 EXATO fora da janela."""
    return ear_window(xp, ux, uy, uz) * field(xp, EAR_V2["prims"], ux, uy, uz)
