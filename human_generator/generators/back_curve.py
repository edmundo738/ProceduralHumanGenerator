# -*- coding: utf-8 -*-
"""T1 COSTAS — curva sagital em S do perfil posterior do tronco.

Pré-registo: docs/TORSO_STUDY_01.md §4 (T1).  Execução e medição A/B: §7.
Mecanismo: três janelas C¹ (sacro, lombar, costas altas) deslocam a face
POSTERIOR dos anéis do tronco ao longo do eixo sagital (+y = anterior), com
peso angular (só a metade de trás do anel) e cauda lateral por janela — a
frente e as larguras ficam intocados por construção.

Convenção de cotas (calibração §7.2): as janelas são escritas em FRACÇÕES DA
ESTATURA NOMINAL já multiplicadas por ``_K``.  A malha realiza 1.6824 m para
uma estatura nominal de 1.7 m (k = 0.98965) e as medições vêm do espaço
normalizado a 1700 mm; sem o ×_K as janelas ficam ~1% deslocadas (medido).

Densidade (§7.2): o loft por estações é demasiado esparso para amostrar a
curva — ``subdivide_rings`` insere anéis INTERPOLADOS LINEARMENTE EM PONTOS
(never em parâmetros: interpolar parâmetros de superelipse incha os cantos,
+18 mm medidos no peito) nas zonas da curva.  A subdivisão acontece SEMPRE
(com ou sem campo): é o que garante "mesma topologia" no A/B.

Instrumento A/B (§7.2): ``HCG_T1_AMP=0`` desliga só o CAMPO (a topologia
subdividida mantém-se).  A leitura do env é DINÂMICA (função ``_amp``) para
que variantes com campo on/off coexistam no mesmo processo (export do site).
"""
from __future__ import annotations

import math
import os

# Realização da estatura nominal (medido: 1.6824 / 1.7).
_K = 0.98965

# ---------------------------------------------------------------------------
# Janelas C¹ do S (fracções da estatura nominal × _K; amplitudes × estatura).
# Valores calibrados na execução T1 (docs/TORSO_STUDY_01.md §7) — as medições
# A/B que as fixam estão registadas ali; não mover sem re-medir.
# ---------------------------------------------------------------------------
# sacro: planalto lateral (xfull→xzero) para sobreviver ao Catmull-Clark —
# uma gaussiana estreita morre no subsurf (medido, §7.2).  Pico zp ALTO
# (sacro/ilíaca ~980 mm@1700), calibrado §7: bs@920 = −149, banda nádega
# −6.0 (realização CC do pad ≈ 0.5 — medido).
_SACRAL = {"z0": 0.4982, "zp": 0.5500, "z1": 0.6000, "amp": 0.0240,
           "xfull": 0.0233, "xzero": 0.0466}
# lombar: pico em zp, cauda lateral gaussiana larga (σx).
_LOMBAR = {"z0": 0.6035, "zp": 0.6434, "z1": 0.6928, "amp": 0.0235,
           "sigmax": 0.0524}
# costas altas: rampa z0→plat (ápice aplanado), cauda lateral estreita.
_ALTA = {"z0": 0.7663, "plat": 0.7972, "z1": 0.8263, "amp": 0.0282,
         "sigmax": 0.0233}

# Zonas de subdivisão (lo, hi, passo) em fracções da estatura nominal: nos
# vãos cuja estação INFERIOR está dentro da zona, insere anéis a `passo` de
# intervalo a partir dela, enquanto abaixo de min(estação superior, hi).
# Contagem medida: 10 anéis = +160 vértices/+160 faces (pins).
_ZONES = ((0.5010, 0.6970, 0.0147), (0.7740, 0.8460, 0.0172))


def _amp() -> float:
    """1.0 com o campo activo (omissão), 0.0 com HCG_T1_AMP=0 (controlo A/B)."""
    return 0.0 if os.environ.get("HCG_T1_AMP", "1").strip() == "0" else 1.0


def _ss(t: float) -> float:
    """Smoothstep C¹ (valor e declive nulos nos extremos)."""
    t = 0.0 if t < 0.0 else (1.0 if t > 1.0 else t)
    return t * t * (3.0 - 2.0 * t)


def _bump(z: float, z0: float, zp: float, z1: float) -> float:
    """Janela C¹: subida [z0, zp], descida [zp, z1]; 0 fora de [z0, z1]."""
    if z <= z0 or z >= z1:
        return 0.0
    if z < zp:
        return _ss((z - z0) / max(1e-9, zp - z0))
    return _ss((z1 - z) / max(1e-9, z1 - zp))


def _field(zf: float, x: float, s: float) -> float:
    """Deslocamento sagital (+y) da curva S em (zf = z/s, x), em metros."""
    d = 0.0
    w = _SACRAL
    b = _bump(zf, w["z0"], w["zp"], w["z1"])
    if b > 0.0:
        ax = abs(x) / s
        if ax < w["xzero"]:
            # planalto |x|<=xfull, queda linear até xzero (C0 no planalto é
            # aceitável: a subsequente suavização angular/janela é C¹)
            wx = 1.0 if ax <= w["xfull"] else 1.0 - (ax - w["xfull"]) / (w["xzero"] - w["xfull"])
            d += w["amp"] * s * b * wx
    w = _LOMBAR
    b = _bump(zf, w["z0"], w["zp"], w["z1"])
    if b > 0.0:
        sx = w["sigmax"] * s
        d += w["amp"] * s * b * math.exp(-((x / sx) ** 2))
    w = _ALTA
    b = _bump(zf, w["z0"], w["plat"], w["z1"])
    if b > 0.0:
        sx = w["sigmax"] * s
        d += w["amp"] * s * b * math.exp(-((x / sx) ** 2))
    return d


def _ring_z(pts) -> float:
    return sum(p.z for p in pts) / len(pts)


def subdivide_rings(rings: list, stature: float) -> list:
    """Insere anéis intermédios nas zonas da curva S (interp LINEAR de pontos).

    Recebe os anéis das estações (listas de pontos, ordem DESCendente de z do
    loft) e devolve a lista expandida.  Em cada zona (lo, hi, passo): nos vãos
    cuja estação INFERIOR está dentro da zona, insere anéis a `passo` de
    intervalo a partir dela, enquanto abaixo de min(estação superior, hi).
    A interpolação é sobre os PONTOS dos anéis — a ponte linear entre duas
    superelipses amostradas é a própria superfície; interpolar PARÂMETROS
    re-avalia as superelipses e incha os cantos (+18 mm de profundidade no
    peito, medido na calibração §7.2).  Contagem medida: 10 anéis = +160
    vértices/+160 faces (pins).
    """
    s = stature
    zs = [_ring_z(r) for r in rings]                      # descendente
    out = [rings[0]]
    for k in range(len(rings) - 1):
        a_pts, b_pts = rings[k], rings[k + 1]             # a ACIMA de b (loft desce)
        za, zb = zs[k], zs[k + 1]
        fa, fb = za / s, zb / s                           # frações (fa > fb)
        ins = []
        for lo, hi, step in _ZONES:
            if fb < lo or fb >= hi:                       # estação inferior fora da zona
                continue
            top = min(fa, hi)
            t = fb + step                                 # primeiro alvo acima da estação inferior
            while t < top:
                ins.append(t)
                t += step
        for ft in sorted(set(ins), reverse=True):         # descendente
            tt = (ft * s - zb) / max(1e-9, za - zb)
            out.append([b_pts[i].lerp(a_pts[i], tt) for i in range(len(b_pts))])
        out.append(b_pts)
    return out


def apply_sagittal_back(builder, stature: float) -> None:
    """Aplica o campo da curva S aos anéis do tronco (pós-DeformStack).

    Só os anéis registados ``trunk.k``; o peso angular usa a componente y da
    direcção do vértice relativamente ao centro do anel: 1 no polo posterior,
    0 no anterior (a frente nunca se move).  Deslocamento puramente sagital.
    """
    a = _amp()
    if a == 0.0:
        return
    s = stature
    verts = builder.verts
    for name, ids in builder.rings.items():
        if not name.startswith("trunk."):
            continue
        n = len(ids)
        cx = sum(verts[i].x for i in ids) / n
        cy = sum(verts[i].y for i in ids) / n
        for i in ids:
            v = verts[i]
            dx, dy = v.x - cx, v.y - cy
            r = math.hypot(dx, dy)
            if r < 1e-9:
                continue
            w = -dy / r                                    # +1 atrás, −1 à frente
            if w <= 0.0:
                continue
            d = _field(v.z / s, v.x, s) * a * w
            if d != 0.0:
                verts[i] = v.__class__((v.x, v.y + d, v.z))
