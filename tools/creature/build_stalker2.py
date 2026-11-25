# -*- coding: utf-8 -*-
"""THE STALKER v2 — GEOMETRIA CRIADA DE RAIO (dono: 'cria a forma, não uses
modelos — só para comparação e escala').

Nenhum corpo emprestado: cada anel é gerado aqui. O Michelle (1.66 m) serviu
SÓ de régua de escala — a criatura acorda em ~1.82 m.

Construção (numpy, determinístico, seed fixa):
  - LOFT geral: splines de centro + perfis de raio → anéis → quads→tris;
  - tronco: UMA superfície contínua da bacia ao pescoço, com a coluna
    CORCUNDA (curva, não cilindro) e secções elípticas com ε orgânico;
  - cabeça alongada inclinada; mandíbula separada (pivô próprio = boca
    que ABRE); olhos negros embutidos; cavidade + 2 fileiras de dentes;
  - membros: tubos enraizados DENTRO do tronco (as junções ficam
    escondidas na carne — CARNE LIGADA) + esferas de articulação nos
    pivôs (cobrem a rotação, à moda PSX);
  - braços até ao joelho (0.34+0.36+~0.30); pernas com canela quase
    recta e pé alongado com 3 garras; mãos com 4 dedos + polegar.

Saída:
  site/models/stalker2_smooth.glb (+cage) — meshes NOMEADOS por parte +
  TEXCOORD_0 (UV cilíndrico, texturas tileable do stalker);
  site/models/stalker2_rig.json — hierarquia/pivôs p/ animação procedural
  em three.js (stalker.js v2);
  painel docs/head_phaseA/stalker2_views.png (frente/perfil/costas + zoom
  cabeça) — auto-cheque de silhueta ANTES do site.

Uso: python3 tools/creature/build_stalker2.py
"""
import json
import os
import struct

import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
OUT = os.path.join(ROOT, "site", "models")
DOC = os.path.join(ROOT, "docs", "head_phaseA")
SEED = 13
rng = np.random.default_rng(SEED)

# ---------------------------------------------------------------- primitivas
def sphere(c, r, n=10):
    us = np.linspace(0, np.pi, n)
    vs = np.linspace(0, 2 * np.pi, 2 * n, endpoint=False)
    V, T = [], []
    for i, u in enumerate(us):
        for j, v in enumerate(vs):
            p = c + r * np.array([np.sin(u) * np.cos(v), np.sin(u) * np.sin(v), np.cos(u)])
            V.append(p)
    V = np.array(V)
    nu, nv = len(us), len(vs)
    for i in range(nu - 1):
        for j in range(nv):
            a, b = i * nv + j, i * nv + (j + 1) % nv
            c_, d = (i + 1) * nv + (j + 1) % nv, (i + 1) * nv + j
            T.append((a, b, c_)); T.append((a, c_, d))
    return V, np.array(T)


def cone(c, r, h, dirv, n=8):
    """Cone com base em c (círculo perpendicular a dirv) e ápice c+h*dirv."""
    t = np.asarray(dirv, float); t /= np.linalg.norm(t)
    ref = np.array([0, 0, 1.0]) if abs(t[2]) < 0.9 else np.array([1.0, 0, 0])
    b1 = np.cross(t, ref); b1 /= np.linalg.norm(b1)
    b2 = np.cross(t, b1)
    th = np.linspace(0, 2 * np.pi, n, endpoint=False)
    ring = c + r * (np.cos(th)[:, None] * b1 + np.sin(th)[:, None] * b2)
    apex = np.repeat((c + h * t)[None], n, 0)
    V = np.vstack([ring, apex])
    T = []
    for j in range(n):
        k = (j + 1) % n
        T.append((j, k, n)); T.append((j, n, k))   # base fecha p/ fora
    return V, np.array(T), np.zeros((len(V), 2))


def _G(x, c, w):
    return float(np.exp(-((x - c) / max(w, 1e-6)) ** 2))


def loft(pts, rads, e1=None, e2=None, n=24, caps=True, noise=0.0, mod=None):
    """Tubo ao longo da polilinha pts (N,3); rads (N,) raio base.
    e1/e2: factores elípticos (N,) nos eixos b1/b2. mod(c, v) → fracção
    do raio local (RELEVO: costelas/espinal/órbitas — Gaussiana contínua,
    CARNE LIGADA, nunca degraus). Devolve V,T,UV."""
    N = len(pts)
    e1 = np.ones(N) if e1 is None else e1
    e2 = np.ones(N) if e2 is None else e2
    V, UV = [], []
    # ruído orgânico LIMITADO a ±noise (randn podia dar +4σ e as
    # larguras MAX das fatias inflavam — M12 FAIL medido)
    eps = 1.0 + noise * np.clip(rng.standard_normal((N, 2)), -1.0, 1.0)
    for i in range(N):
        t = pts[min(i + 1, N - 1)] - pts[max(i - 1, 0)]
        t = t / max(np.linalg.norm(t), 1e-9)
        # e1 = LARGURA (X): para t vertical, b1 tem de ser ±X → ref=+Y.
        # (bug v2.0: ref=+X fazia b1≈Y → largura/profundidade TROCADAS;
        #  apanhado pela medição M11/M12: anca 177mm vs ~330 desenhados)
        ref = np.array([0, 1.0, 0]) if abs(t[2]) > 0.9 else np.array([0, 0, 1.0])
        b1 = np.cross(t, ref); b1 /= np.linalg.norm(b1)
        b2 = np.cross(t, b1)
        th = np.linspace(0, 2 * np.pi, n, endpoint=False) + i * 0.13
        r1, r2 = rads[i] * e1[i] * eps[i, 0], rads[i] * e2[i] * eps[i, 1]
        ring = pts[i] + np.cos(th)[:, None] * (r1 * b1) + np.sin(th)[:, None] * (r2 * b2)
        if mod is not None:
            for j in range(n):
                d_ = ring[j] - pts[i]
                n_ = np.linalg.norm(d_)
                if n_ > 1e-9:
                    ring[j] = pts[i] + d_ * (1.0 + mod(pts[i], ring[j]))
        V.append(ring)
        UV.append(np.stack([th / (2 * np.pi), np.full(n, i / max(N - 1, 1))], 1))
    V = np.vstack(V); UV = np.vstack(UV)
    T = []
    for i in range(N - 1):
        for j in range(n):
            k = (j + 1) % n
            a, b = i * n + j, i * n + k
            c_, d = (i + 1) * n + k, (i + 1) * n + j
            T.append((a, b, c_)); T.append((a, c_, d))
    if caps:                                     # tampas em leque
        for (idx, tri) in ((0, (0, 1, 2)), (N - 1, (0, 2, 1))):
            base = idx * n
            for j in range(1, n - 1):
                T.append((base, base + j, base + j + 1) if tri[0] == 0 else
                         (base, base + j + 1, base + j))
    return V, np.array(T), UV


def merge(*parts):
    Vs, Ts, UVs, off = [], [], [], 0
    for V, T, UV in parts:
        Vs.append(V); Ts.append(T + off); UVs.append(UV); off += len(V)
    return np.vstack(Vs), np.vstack(Ts), np.vstack(UVs)


# ---------------------------------------------------------------- anatomia (m, nosso frame: z↑, +y frente)
# ---------------------------------------------------------------- RELEVO
# v3.2 (gate do dono: "a forma/silhueta"): terror PSX lê por RELEVO.
# Frente = +y, costas = -y (o pescoço juta +y; yaw do site aponta +y).
# Gaussiana contínua por vértice — CARNE LIGADA, zero degraus.
def make_torso_mod(stz):
    """stz: z (mm) das estações do loft. RELEVO INDEXADO À ESTAÇÃO: os
    anéis estão INCLINADOS (corcunda) e os verts de um anel espalham-se
    por ±40mm de z — gomos por z-de-vértice acertavam em metade do anel
    e as vértebras (yl<-0.35) apanhavam verts LATERAIS: espinhos de 29mm
    nos flancos (bug apanhado pela medição F1/F1b). Estação = c (centro
    do anel, estável); transição suave entre anéis (Gaussiana em zc);
    sectores angulares por vértice (mundo, imune ao tilt)."""
    # gomos em estações ALTERNADAS (~30mm entre gomos; janela de medição
    # ±16 deixa os vizinhos de fora). Ribs ≥1285: o anel inclinado
    # espalha verts ±20mm — abaixo disso poluía a fatia da cintura (M12)
    rib_z = [z for i, z in enumerate(stz) if i % 2 == 1 and 1285 <= z <= 1452]
    vert_z = [z for i, z in enumerate(stz) if i % 2 == 0 and 1150 <= z <= 1455]

    def torso_mod(c, v):
        d_ = v - c
        n_ = np.linalg.norm(d_)
        if n_ < 1e-9:
            return 0.0
        zc = c[2] * 1000.0                       # ESTAÇÃO (não o vértice!)
        zl = v[2] * 1000.0                       # p/ zonas largas
        yl, xl = d_[1] / n_, d_[0] / n_
        b = -yl                                  # backness (1 = polo costas)
        mm = 0.0
        # costelas: flancos PUROS (|xl|>.55, |yl|<.55), por estação
        if abs(xl) > 0.55 and abs(yl) < 0.55 and rib_z:
            mm += 13.0 * max(_G(zc, z, 8) for z in rib_z)
        # espinal: crista ESTREITA no polo (±0.18 em backness) + vértebras
        mm += 14.0 * _G(b, 1.0, 0.18) * _G(zc, 1290, 170)
        if b > 0.7 and vert_z:
            mm += 18.0 * max(_G(zc, z, 8) for z in vert_z)
        # escápulas (bosses costas-altas) + cristas ilíacas
        mm += 10.0 * _G(zl, 1400, 26) * _G(abs(xl), 0.45, 0.16) * _G(b, 0.55, 0.3)
        mm += 6.0 * _G(zl, 1140, 22) * _G(abs(xl), 0.6, 0.18) * _G(yl, -0.15, 0.4)
        # esterno (goleta) + fossa clavicular + barriga encovada (gaunt)
        mm -= 5.0 * _G(yl, 0.75, 0.25) * _G(zc, 1330, 60)
        mm -= 6.0 * _G(yl, 0.8, 0.2) * _G(zc, 1430, 18)
        mm -= 7.0 * _G(yl, 0.7, 0.3) * _G(zc, 1215, 28)
        return mm / 1000.0 / n_

    return torso_mod


def head_mod(c, v):
    d_ = v - c
    n_ = np.linalg.norm(d_)
    if n_ < 1e-9:
        return 0.0
    zl, yl, xl = v[2] * 1000.0, d_[1] / n_, d_[0] / n_
    mm = 0.0
    mm += 6.0 * _G(yl, 0.55, 0.28) * _G(zl, 1682, 20)          # arcada
    mm -= 7.0 * _G(abs(xl), 0.32, 0.13) * _G(yl, 0.55, 0.25) * (
        _G(zl, 1615, 20) + _G(zl, 1648, 20))                    # órbitas (2 estações)
    mm -= 4.0 * _G(abs(xl), 0.7, 0.14) * _G(zl, 1712, 30)      # têmporas
    mm += 4.0 * _G(abs(xl), 0.55, 0.15) * _G(yl, 0.35, 0.25) * _G(zl, 1580, 16)  # zigomático
    mm -= 6.0 * _G(abs(xl), 0.45, 0.18) * _G(yl, 0.25, 0.25) * _G(zl, 1545, 22)  # bochechas
    mm += 4.0 * _G(abs(xl), 0.0, 0.12) * _G(yl, 0.0, 0.4) * _G(zl, 1747, 30)     # crista sagital
    return mm / 1000.0 / n_


def densify(P, R, E1=None, E2=None, mult=2):
    """Duplica estações (interp linear) + suavização C1 nos interiores:
    resolução z para o RELEVO (costelas/vértebras precisam de ~35mm)."""
    N = len(P)
    u = np.linspace(0.0, 1.0, N)
    uu = np.linspace(0.0, 1.0, mult * N - (mult - 1))
    P2 = np.stack([np.interp(uu, u, P[:, k]) for k in range(3)], 1)
    R2 = np.interp(uu, u, R)
    E12 = np.interp(uu, u, E1) if E1 is not None else None
    E22 = np.interp(uu, u, E2) if E2 is not None else None
    for _ in range(2):
        P2[1:-1] = (P2[:-2] + 2 * P2[1:-1] + P2[2:]) / 4.0
    # NÃO suavizar R/E: os raios das estações são os valores medidos
    # (a suavização achatou o dip da cintura → M12 FAIL, apanhado pela
    # re-medição 17/17)
    return P2, R2, E12, E22


def build():
    parts = {}    # name -> (V, T, UV)
    rig = []      # {name, parent, pivot}

    # ---- tronco (dimensões p/ BANDAS M7, M8, M11-M13; corcunda ≥45mm,
    #      pescoço a ≤100mm do dip, ombro 0.19-0.26·S, cintura magra)
    P = np.array([
        [0.000, 0.012, 1.060],    # bacia
        [0.000, 0.016, 1.135],    # anca
        [0.000, 0.010, 1.220],    # cintura (gaunt)
        [0.000, 0.002, 1.275],    # segura o raio até 1275 (M12: a rampa
                                  # subia cedo e a fatia 1190-1260 apanhava
                                  # anéis já largos — FAIL medido)
        [0.000, -0.008, 1.325],   # costelas
        [0.000, -0.095, 1.405],   # ombros: dip profundo (corcunda)
        [0.000, -0.040, 1.465],
        [0.000, 0.005, 1.500],    # pescoço (retractado: ~95mm acima do dip)
    ])
    R = np.array([0.106, 0.094, 0.0775, 0.079, 0.100, 0.130, 0.145, 0.062])
    E1 = np.array([1.14, 1.20, 1.22, 1.249, 1.26, 1.34, 1.35, 1.05])  # largura x
    E2 = np.array([0.85, 0.82, 0.80, 0.807, 0.82, 0.86, 0.88, 0.92])  # profundidade y
    P, R, E1, E2 = densify(P, R, E1, E2, mult=5)                    # 31 estações
    torso_mod = make_torso_mod([p[2] * 1000 for p in P])
    V, T, UV = loft(P, R, E1, E2, n=28, noise=0.02, mod=torso_mod)
    parts["torso"] = (V, T, UV)
    rig.append({"name": "torso", "parent": None, "pivot": [0, 0, 1.0]})

    # ---- cabeça alongada (M5: 0.115-0.150·S ≈ 210-270mm; M6: 20-40°)
    Hp = np.array([0.000, 0.040, 1.523])          # pivô na base do crânio
    pitch = 0.60                                   # 34.4°
    d = np.array([0.0, np.sin(pitch), np.cos(pitch)])
    P = np.stack([Hp + s_ * d for s_ in (0.00, 0.05, 0.11, 0.18, 0.245)])
    R = np.array([0.070, 0.098, 0.108, 0.092, 0.055])
    E1 = np.array([0.95, 1.05, 1.10, 1.02, 0.85])
    P, R, E1, _ = densify(P, R, E1, None, mult=2)                   # 9 estações
    V, T, UV = loft(P, R, E1, None, n=24, noise=0.02, mod=head_mod)
    parts["head"] = (V, T, UV)
    rig.append({"name": "head", "parent": "torso", "pivot": list(Hp)})

    # ---- mandíbula (M16: 90-140mm) — pivô na dobradiça
    Jp = Hp + 0.10 * d
    P = np.stack([Jp + s_ * d + np.array([0, 0, -0.055]) for s_ in (0.00, 0.045, 0.10, 0.135)])
    R = np.array([0.050, 0.058, 0.050, 0.016])
    E1 = np.array([1.15, 1.2, 1.1, 0.9])
    V, T, UV = loft(P, R, E1, None, n=18, noise=0.02)
    parts["mandible"] = (V, T, UV)
    rig.append({"name": "mandible", "parent": "head", "pivot": list(Jp)})

    # cavidade da boca + dentes (2 fileiras) — filhos da cabeça
    cavity_c = Jp + 0.045 * d + np.array([0, 0.02, -0.01])
    Vc, Tc = sphere(cavity_c, 0.050, 10)
    parts["cavity"] = (Vc, Tc, np.zeros((len(Vc), 2)))
    rig.append({"name": "cavity", "parent": "head", "pivot": list(Hp)})
    teeth = []
    up = Jp + 0.055 * d + np.array([0, 0.025, 0.005])
    for row, dz in ((0, 0.028), (1, -0.036)):
        for i in range(9):
            a = (i / 8 - 0.5) * 1.35
            c = up + np.array([np.sin(a) * 0.036, np.cos(a) * 0.012, dz * (0.7 if row else 1.0)])
            vt = np.array([0.0, 0.0, -1.0]) if row == 0 else np.array([0.0, 0.0, 1.0])
            teeth.append(cone(c, 0.0062, 0.024 if row else 0.020, vt, 6))
    offs = np.cumsum([0] + [len(tv[0]) for tv in teeth[:-1]])
    Tt = np.vstack([tv[1] + int(o) for tv, o in zip(teeth, offs)])
    Vt = np.vstack([tv[0] for tv in teeth])
    parts["teeth"] = (Vt, Tt, np.zeros((len(Vt), 2)))
    rig.append({"name": "teeth", "parent": "head", "pivot": list(Hp)})

    # ---- olhos (M14: interocular 95-115; M15: raio 18-24) — ASSENTES
    #      NA SUPERFÍCIE: v2/v3.0 enterrava-os 43mm dentro da cabeça
    #      (invisíveis; F8 do measure_form apanhou o bug)
    VH = parts["head"][0]
    c_h = Hp + 0.115 * d
    for s, nm in ((1, "R"), (-1, "L")):
        dir_eye = np.array([s * 0.052, 0.060, 0.020])
        dir_eye /= np.linalg.norm(dir_eye)
        sel = (VH[:, 2] > 1.580) & (VH[:, 2] < 1.675) & (VH[:, 0] * s > 0.02)
        u = VH[sel] - c_h
        S = VH[sel][np.argmax(u @ dir_eye)]          # vértice mais externo
        n_ = S - c_h
        n_ /= np.linalg.norm(n_)
        e = S - n_ * 0.021 + np.array([s * 0.002, 0, 0])   # 21mm sob a pele
        # (+2mm lateral: M14 interocular 93.9 < 95 — medido)
        Ve, Te = sphere(e, 0.021, 10)
        parts["eye_" + nm] = (Ve, Te, np.zeros((len(Ve), 2)))
        rig.append({"name": "eye_" + nm, "parent": "head", "pivot": list(Hp)})

    # ---- membros: tubos enraizados DENTRO do tronco + esfera no pivô
    def limb(name, parent, pivot, A, B, r0, r1, n=16, joint=True, root_frac=0.12,
             profile=None):
        # profile: 5 multiplicadores por estação (f=-root,0,0.35,0.7,1) —
        # CONTRASTE DE VOLUME: nó na raiz/junções vs meio-corda fino
        # (terror PSX: deltóide inchado + antebraço de corda)
        dirv = np.asarray(B, float) - np.asarray(A, float)
        P = np.stack([A + (dirv) * f for f in (-root_frac, 0.0, 0.35, 0.7, 1.0)])
        R = np.array([r0, r0 * 0.97, (r0 + r1) / 2, r1 * 1.05, r1])
        if profile:
            R = R * np.asarray(profile, float)
        V, T, UV = loft(P, R, None, None, n=n, noise=0.02)
        if joint:
            Vs, Ts = sphere(np.asarray(A, float), max(r0, r1) * 1.12, 9)
            V, T, UV = merge((V, T, UV), (Vs, Ts, np.zeros((len(Vs), 2))))
        parts[name] = (V, T, UV)
        rig.append({"name": name, "parent": parent, "pivot": list(map(float, pivot))})

    # BRAÇOS até à linha do joelho (M2: punho −20..+60 acima do joelho):
    # joelho z≈0.545 → punho alvo 0.555 (ombro 1.42: 0.40 supra + 0.46 infra)
    for s, nm in ((1, "R"), (-1, "L")):
        sh = np.array([s * 0.170, -0.065, 1.420])
        uaL, faL = (0.400, 0.435) if s == 1 else (0.392, 0.427)   # assim 16mm (M17)
        el = sh + np.array([s * 0.055, -0.095, -uaL])
        wr = el + np.array([s * 0.018, 0.075, -faL])
        limb("upperarm_" + nm, "torso", sh, sh + np.array([s * 0.05, -0.02, 0.06]), el, 0.048, 0.038,
             profile=[1.18, 1.02, 0.92, 1.06, 1.12])   # nó deltoideu + cotovelo
        limb("forearm_" + nm, "upperarm_" + nm, el, el - (el - sh) * 0.05, wr, 0.038, 0.027,
             profile=[1.16, 0.95, 0.88, 1.02, 1.0])    # cotovelo + corda fina
        # mão (M4: 120-180mm): palma 55 + dedos 100-120
        palm_d = (wr - el) / np.linalg.norm(wr - el)
        palm_c = wr + palm_d * 0.045
        hand = []
        Pp = np.stack([palm_c - palm_d * 0.030, palm_c + palm_d * 0.048])
        hand.append(loft(Pp, np.array([0.030, 0.024]), np.array([1.15, 1.1]), np.array([0.55, 0.5]), 12, noise=0.0))
        fl = 1.0 if s == 1 else 0.97
        for k in range(4):
            base = palm_c + palm_d * 0.068 + np.array([s * (k - 1.5) * 0.015, 0, 0.004 * (k % 2)])
            fdir = palm_d + np.array([s * (k - 1.5) * 0.22, 0.18, -0.10])
            fdir /= np.linalg.norm(fdir)
            Pf = np.stack([base - fdir * 0.01, base + fdir * (0.082 - 0.008 * abs(k - 1.5)) * fl])
            hand.append(loft(Pf, np.array([0.0080, 0.0036]), None, None, 8, caps=True))
        base = palm_c - palm_d * 0.018 + np.array([s * 0.024, 0.01, 0.012])
        fdir = np.array([s * 0.8, 0.35, -0.3]); fdir /= np.linalg.norm(fdir)
        hand.append(loft(np.stack([base, base + fdir * 0.062 * fl]), np.array([0.0072, 0.0034]), None, None, 8))
        parts["hand_" + nm] = merge(*hand)
        rig.append({"name": "hand_" + nm, "parent": "forearm_" + nm, "pivot": list(map(float, wr))})

    # PERNAS (M9: coxa/canela 0.90-1.10; M10: pé 200-280mm)
    for s, nm in ((1, "R"), (-1, "L")):
        hip = np.array([s * 0.064, 0.008, 1.060])
        knee = hip + np.array([s * 0.008, -0.045, -0.500])
        ankle = knee + np.array([0, 0.030, -0.475])
        limb("thigh_" + nm, "torso", hip, hip + np.array([0, 0, 0.06]), knee, 0.070, 0.050, root_frac=0.06,
             profile=[1.16, 1.0, 0.97, 1.08, 1.22])    # nó da anca + joelho
        limb("shin_" + nm, "thigh_" + nm, knee, knee - (knee - hip) * 0.04, ankle, 0.048, 0.033,
             profile=[1.24, 0.98, 1.06, 0.95, 0.92])   # bojo do joelho + gémeo + tornozelo fino
        foot = []
        Pd = np.stack([ankle, ankle + np.array([0, 0.105, -0.065]), ankle + np.array([0, 0.185, -0.075])])
        foot.append(loft(Pd, np.array([0.036, 0.030, 0.012]), np.array([1.0, 0.9, 0.8]), np.array([0.75, 0.55, 0.45]), 12))
        for k in range(3):
            b = Pd[2] + np.array([(k - 1) * 0.016, 0.018, 0.002])
            foot.append(cone(b, 0.008, 0.042, np.array([(k - 1) * 0.25, 1, -0.15]), 6))
        parts["foot_" + nm] = merge(*foot)
        rig.append({"name": "foot_" + nm, "parent": "shin_" + nm, "pivot": list(map(float, ankle))})
    return parts, rig


# ---------------------------------------------------------------- GLB multi-part com UV
def write_glb(parts, rig, path):
    def pad(x):
        return x + b"\x00" * ((4 - len(x) % 4) % 4)
    posA, nrmA, uvA, idxA, views, meshes, nodes = [], [], [], [], [], [], []
    binparts, offset = [], 0
    MAT = {"skin": 0, "eye": 1, "cavity": 2, "teeth": 3}
    for name, (V, T, UV) in parts.items():
        P = np.stack([-V[:, 0], V[:, 2], V[:, 1]], 1).astype(np.float32)   # nosso→glTF
        a, b, c = V[T[:, 0]], V[T[:, 1]], V[T[:, 2]]
        fn = np.cross(b - a, c - a)
        N = np.zeros_like(V)
        for k in range(3):
            np.add.at(N, T[:, k], fn)
        N /= np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-12)
        NN = np.stack([-N[:, 0], N[:, 2], N[:, 1]], 1).astype(np.float32)
        UU = np.asarray(UV, np.float32).reshape(-1, 2)
        I = T.astype(np.uint32).ravel()
        for arr in (P, NN, UU, I):
            raw = pad(arr.tobytes())
            views.append({"buffer": 0, "byteOffset": offset, "byteLength": len(arr.tobytes())})
            acc = {"bufferView": len(views) - 1, "count": len(arr)}
            if arr is P:
                acc.update({"componentType": 5126, "type": "VEC3", "min": P.min(0).tolist(), "max": P.max(0).tolist()})
                posA.append(acc)
            elif arr is NN:
                acc.update({"componentType": 5126, "type": "VEC3"}); nrmA.append(acc)
            elif arr is UU:
                acc.update({"componentType": 5126, "type": "VEC2"}); uvA.append(acc)
            else:
                acc.update({"componentType": 5125, "type": "SCALAR"}); idxA.append(acc)
            binparts.append(raw); offset += len(raw)
        mi = MAT["eye"] if name.startswith("eye") else MAT["cavity"] if name == "cavity" \
            else MAT["teeth"] if name == "teeth" else MAT["skin"]
        i = len(meshes)
        meshes.append({"name": name, "primitives": [{"attributes": {
            "POSITION": i, "NORMAL": len(posA) + len(nrmA) - len(nrmA) + i, "TEXCOORD_0": 2 * len(meshes) + i},
            "indices": 3 * len(meshes) + i, "material": mi}]})
        nodes.append({"mesh": i, "name": name})
    bin_ = b"".join(binparts)
    # fix accessors ABSOLUTOS: pos i, norm N+i, uv 2N+i, idx 3N+i
    nM = len(meshes)
    for i, m in enumerate(meshes):
        pr = m["primitives"][0]
        pr["attributes"]["POSITION"] = i
        pr["attributes"]["NORMAL"] = nM + i
        pr["attributes"]["TEXCOORD_0"] = 2 * nM + i
        pr["indices"] = 3 * nM + i
    textures = []
    for si in range(5):
        textures.append({"source": si})
    gltf = {
        "asset": {"version": "2.0", "generator": "hcg stalker2 (geometria própria)"},
        "scene": 0, "scenes": [{"nodes": list(range(len(nodes)))}],
        "nodes": nodes, "meshes": meshes,
        "materials": [
            {"name": "skin", "pbrMetallicRoughness": {"baseColorTexture": {"index": 2},
             "metallicRoughnessTexture": {"index": 3}, "metallicFactor": 0.05},
             "normalTexture": {"index": 1}, "occlusionTexture": {"index": 4, "strength": 0.9}},
            {"name": "eye", "pbrMetallicRoughness": {"baseColorFactor": [0.01, 0.0, 0.0, 1.0],
             "roughnessFactor": 0.12, "metallicFactor": 0.0},
             "emissiveFactor": [0.35, 0.02, 0.02]},
            {"name": "cavity", "pbrMetallicRoughness": {"baseColorFactor": [0.02, 0.0, 0.0, 1.0],
             "roughnessFactor": 0.95, "metallicFactor": 0.0}},
            {"name": "teeth", "pbrMetallicRoughness": {"baseColorFactor": [0.42, 0.36, 0.30, 1.0],
             "roughnessFactor": 0.45, "metallicFactor": 0.0}}],
        "textures": textures, "images": "IMAGES", "accessors": posA + nrmA + uvA + idxA,
        "bufferViews": views, "buffers": [{"byteLength": len(bin_)}],
    }
    return gltf, bin_, pad


def embed_images(gltf, bin_, texdir):
    from PIL import Image
    import io
    imgs = []
    newbin = bytearray(bin_)
    for fn in ("stalker_normal.png", "stalker_rough_metal.png", "stalker_albedo.png",
               "stalker_rough_metal.png", "stalker_ao.png"):
        data = open(os.path.join(texdir, fn), "rb").read()
        # normal e MR referenciados 2x → texturas distintas partilham a MESMA imagem
        imgs.append(("image/png", data))
    # imagens por bufferView novo
    views = []
    for (mime, data) in imgs:
        vi = len(gltf["bufferViews"])
        gltf["bufferViews"].append({"buffer": 0, "byteOffset": len(newbin), "byteLength": len(data)})
        newbin += data + b"\x00" * ((4 - len(data) % 4) % 4)
        views.append(vi)
    # texturas já existem (0..4) → sources correctos
    for i, t in enumerate(gltf["textures"]):
        t["source"] = i
    gltf["images"] = [{"mimeType": m, "bufferView": v} for (m, _), v in zip(imgs, views)]
    gltf["buffers"][0]["byteLength"] = len(newbin)
    return gltf, bytes(newbin)


def write_out(gltf, bin_, path):
    js = json.dumps(gltf).encode()
    js += b" " * ((4 - len(js) % 4) % 4)
    total = 12 + 8 + len(js) + 8 + len(bin_)
    hdr = struct.pack("<III", 0x46546C67, 2, total)
    open(path, "wb").write(hdr + struct.pack("<II", len(js), 0x4E4F534A) + js
                           + struct.pack("<II", len(bin_), 0x004E4942) + bin_)
    return total


def main():
    os.chdir(ROOT)
    parts, rig = build()
    for name, (V, T, UV) in parts.items():
        print(f"  {name:14} v={len(V):5} t={len(T):5}")
    tot_v = sum(len(p[0]) for p in parts.values())
    tot_t = sum(len(p[1]) for p in parts.values())
    print(f"TOTAL: {tot_v} verts, {tot_t} tris — CRIADO DE RAIO (zero modelos)")

    gltf, bin_, _ = write_glb(parts, rig, "")
    gltf, bin_ = embed_images(gltf, bin_, os.path.join(ROOT, "site", "textures"))
    n = write_out(gltf, bin_, os.path.join(OUT, "stalker2_smooth.glb"))
    import shutil
    shutil.copy(os.path.join(OUT, "stalker2_smooth.glb"), os.path.join(OUT, "stalker2_cage.glb"))
    print(f"stalker2_smooth.glb: {n/1e6:.2f} MB")

    # rig json (pivôs em frame GLB)
    rigg = [{"name": r["name"], "parent": r["parent"],
             "pivot": [-r["pivot"][0], r["pivot"][2], r["pivot"][1]]} for r in rig]
    json.dump({"rig": rigg}, open(os.path.join(OUT, "stalker2_rig.json"), "w"), indent=1)

    # ---- validação estrita + volume
    b = open(os.path.join(OUT, "stalker2_smooth.glb"), "rb").read()
    clen, _ = struct.unpack("<II", b[12:20])
    js = json.loads(b[20:20 + clen])
    off = 20 + clen
    blen, _ = struct.unpack("<II", b[off:off + 8])
    buf = b[off + 8:off + 8 + blen]
    for v in js["bufferViews"]:
        assert v["byteOffset"] + v["byteLength"] <= blen
    nT = len(js["textures"])
    for mat in js["materials"]:
        for key, t in list(mat.get("pbrMetallicRoughness", {}).items()) + list(mat.items()):
            if isinstance(t, dict) and "index" in t and "Texture" in key:
                assert t["index"] < nT, key
    print(f"VALIDAÇÃO: {len(js['meshes'])} meshes · {nT} texturas · views OK")

    # ---- painel de silhueta (auto-cheque)
    import sys
    sys.path.insert(0, os.path.join(ROOT, "tools", "refstudy"))
    from basemesh_proto import vertex_normals, render_view
    Vs, Ts, off_v = [], [], 0
    for V, T, UV in parts.values():
        Vs.append(V * 1000); Ts.append(T + off_v); off_v += len(V)
    V = np.vstack(Vs) * (1.0)      # mm
    T = np.vstack(Ts)
    V[:, 2] -= V[:, 2].min()
    N = vertex_normals(V, T)
    tiles = []
    for phi, name in ((0.0, "frente"), (np.pi / 2, "perfil"), (np.pi, "costas")):
        a = render_view(V, T, N, span=2100.0, zc=950.0, phi=phi, res=460)
        tiles.append((Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8), "L"), name))
    head = V[V[:, 2] > 1450]
    if len(head):
        zc = (head[:, 2].max() + 1450) / 2
        a = render_view(V, T, N, span=700.0, zc=zc, phi=0.15, res=460)
        tiles.append((Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8), "L"), "cabeça"))
    H = max(t[0].height for t in tiles) + 34
    W = sum(t[0].width for t in tiles) + 20 * (len(tiles) + 1)
    panel = Image.new("L", (W, H), 24)
    dr = ImageDraw.Draw(panel)
    x = 20
    for img, name in tiles:
        panel.paste(img, (x, 26)); dr.text((x + img.width // 2 - 24, 6), name, fill=230)
        x += img.width + 20
    panel.save(os.path.join(DOC, "stalker2_views.png"))
    print("painel →", os.path.join(DOC, "stalker2_views.png"))
    print(f"estatura construída: {V[:,2].max():.0f} mm (alvo ~1820)")


if __name__ == "__main__":
    main()
