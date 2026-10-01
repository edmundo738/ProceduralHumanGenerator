# -*- coding: utf-8 -*-
"""The trunk-and-limbs assembly ("anatomical_base").

Limb roots are *inserted* into the trunk (overlapping shells welded by the
same displacement fields), never boolean-joined — the standard trick of
procedural character toolkits: the union silhouette reads as one body while
every shell keeps its clean quad loops.  Soft tissue (bust, glutes, thenar,
trapezius, clavicle ridges) is authored as a :class:`DeformStack` applied to
the *merged* cage so junctions deform coherently.
"""
from __future__ import annotations

import json
import math
import os as _os
from dataclasses import dataclass, field

from ..core._math import Vector
from ..core.field import DeformStack
from ..core.topology import MeshBuilder, spline_rings
from ..core.rng import Rng
from .hands import build_hand
from .feet import build_foot
from .back_curve import apply_sagittal_back


def _breast_params() -> dict:
    """SWEEP modo A (docs/SWEEP_01_BREAST.md) — gancho de busca da mama.

    Default = valores calibrados H-TT1 (digest-pinados; NÃO mudar sem re-medir).
    ``HCG_BREAST='{"amp": 0.86, ...}'`` sobrepõe POR CHAMADA (instrumento A/B
    como HCG_T1_AMP; lido a cada build).  NÃO é parâmetro de spec (directriz
    "sem variável por descoberta"): os vencedores dos sweeps tornam-se os novos
    defaults calibrados, não flags permanentes.
    """
    p = {"amp": 0.86, "sx": 0.048, "sy": 0.040, "sz": 0.055,
         "cy": 0.008, "cz": -0.010, "dirz": -0.18}
    raw = _os.environ.get("HCG_BREAST", "")
    if raw:
        p.update(json.loads(raw))
    return p


@dataclass
class BodyResult:
    builder: MeshBuilder
    joints: dict = field(default_factory=dict)
    notes: list = field(default_factory=list)


def build_body(spec, anat, *, ring_n: int = 16, include_hands: bool = True,
               include_feet: bool = True) -> BodyResult:
    # S3.1 — simetria L/R.  Medido antes da correcção (docs/S3_BODY_INTEGRATION.md
    # §3): um único fluxo ``Rng(spec.seed, salt=17)`` era consumido pelos dois
    # lados, e como ``hands.py`` usa ``rng.f`` para o espalhamento dos dedos e
    # ``feet.py`` para o comprimento dos dedos do pé, o lado direito recebia
    # desenhos diferentes do esquerdo (Hausdorff L↔espelho(R) até 13.4 mm numa
    # mão, 8.3 mm num pé).  Cada lado passa a começar o seu próprio fluxo com o
    # MESMO salt: os dois lados consomem exactamente a mesma sequência (logo a
    # geometria espelha-se) e a assimetria intencional continua a vir dos
    # parâmetros do spec (sobrancelha, mama — anatomia/body, não rng).
    SALT_SIDE = 17          # sal do fluxo por lado (igual nos dois lados, de propósito)
    b = MeshBuilder("body")
    notes: list[str] = []

    # ---------------------------------------------------------------- trunk
    secs = anat.trunk_sections()
    # S3.7 — as estações do tronco têm de estar em ordem DESCENDENTE de z antes
    # do loft.  Medido: não estavam (pré-existente — a linha do deltoide a
    # 1380.4 mm vinha antes do peito superior a 1385.5 mm), e o loft segue a
    # ordem de criação, pelo que o tubo se dobrava sobre si mesmo nesse intervalo.
    # A ordenação é estável e total (z, depois y), pelo que é determinística.
    secs = sorted(secs, key=lambda s_: (-s_.center.z, s_.center.y))
    rings = [s.points(ring_n) for s in secs]
    # H-TT1 (docs/TORSO_TRANSITIONS_01.md §4) — anéis densos por PCHIP dos
    # caminhos dos pontos: substitui a ponte LINEAR do loft (+subdivide_rings,
    # também linear) que deixava a superfície C0 por troços e concentrava a
    # curvatura nas estações ("lombas de estrada": R9 3 extremos vs 1 [1–1]
    # das refs; 6/9 extremos a ≤18 mm de uma estação).  Passagem EXACTA pelas
    # estações (z das estações na grelha); sem overshoot (monotona por
    # componente) — os cantos não incham (interp de PARÂMETROS inchava +18 mm,
    # T1 §7.2).  Topologia idêntica com/sem o campo (instrumento A/B
    # HCG_T1_AMP); o campo sagital corre DEPOIS, por anel registado.
    rings = spline_rings(rings, 0.012 * anat.stature)
    b.loft(rings, close=True, region="skin", material="skin",
           uv_rect=(0.22, 0.78, 0.0, 1.0), register="trunk",
           cap_start="pole", cap_end="pole")

    # ------------------------------------------------------------------ arms
    for side, tag in ((1, "L"), (-1, "R")):
        a_secs = anat.arm_sections(side)
        a_rings = [s.points(12) for s in a_secs]
        # S3.5 — tampas: medido, o tubo do braço era uma casca ABERTA nas duas
        # pontas (a raiz, agora dentro do tronco, e o punho, agora dentro da
        # palma).  As tampas fecham a casca sem custo visível (ambas as pontas
        # estão dentro de outra casca) e eliminam a possibilidade de se ver o
        # interior do membro através de uma fronteira.
        b.loft(a_rings, close=True, region="skin", material="skin",
               uv_rect=(0.0, 1.0, 0.0, 1.0), register=f"arm.{tag}",
               cap_start="pole", cap_end="pole")
        if include_hands:
            hb, hj = build_hand(spec, anat, side=side,
                                rng=Rng(spec.seed, salt=SALT_SIDE))
            b.merge(hb, group_prefix="")
            notes.append(f"hand.{tag} merged")
        for k, v in hj.items():
            anat.landmarks.setdefault(k, v)

    # ------------------------------------------------------------------ legs
    for side, tag in ((1, "L"), (-1, "R")):
        l_secs = anat.leg_sections(side)
        l_rings = [s.points(12) for s in l_secs]
        b.loft(l_rings, close=True, region="skin", material="skin",
               uv_rect=(0.0, 1.0, 0.0, 1.0), register=f"leg.{tag}",
               cap_start="pole", cap_end="pole")
        if include_feet:
            fb, fj = build_foot(spec, anat, side=side,
                                rng=Rng(spec.seed, salt=SALT_SIDE))
            b.merge(fb)
            notes.append(f"foot.{tag} merged")
        for k, v in fj.items():
            anat.landmarks.setdefault(k, v)

    # ------------------------------------------------- soft tissue / volumes
    s = spec.body.stature
    h = anat.h
    lm = anat.landmarks
    fat = spec.body.fat_level
    mus = spec.body.muscle_tone
    stack = DeformStack()

    # TORSO B/H-TT1 — mama = VOLUME LOCALIZADO sobre a parede torácica (a
    # parede é das estações; o bump é a mama).  Parâmetros via _breast_params()
    # (default H-TT1; gancho de sweep HCG_BREAST — modo A, ver docstring).
    bp = _breast_params()
    for tag in ("L", "R"):
        c = Vector(lm[f"bust.{tag}"])
        stack.bump(c + Vector((0, bp["cy"] * s, bp["cz"] * s)),
                   anat.bust_protrusion() * bp["amp"],
                   sigma=(bp["sx"] * s, bp["sy"] * s, bp["sz"] * s),
                   direction=Vector((0, 1, bp["dirz"])))
    # TORSO B — glúteos = LÓBULOS LATERAIS (P16: refs 7–26 mm de sulco);
    # âncoras próprias em ±0.60·hip_half (não o landmark iliac).
    for tag in ("L", "R"):
        side = 1 if tag == "L" else -1
        c = Vector((side * 0.60 * anat.hip_half(), -0.100 * s, 0.512 * s))
        stack.bump(c, 0.013 * s * (0.7 + 1.0 * fat), sigma=(0.055 * s, 0.050 * s, 0.075 * s),
                   direction=Vector((0, -1, -0.12)))
    # trapezius slope plates
    for tag in ("L", "R"):
        c = (Vector(lm["spine_neck"]) + Vector(lm[f"acromion.{tag}"])) / 2 + Vector((0, -0.004 * s, 0.010 * s))
        stack.bump(c, 0.006 * s * (0.6 + mus), sigma=(0.070 * s, 0.030 * s, 0.028 * s),
                   direction=Vector((0.25 * (1 if tag == "L" else -1), -0.35, 0.9)))
    # clavicle ridges
    for tag in ("L", "R"):
        stack.ridge(Vector(lm["jugulum"]) + Vector((0, 0.004 * s, 0.004 * s)),
                    Vector(lm[f"clavicle.{tag}"]) + Vector((0, 0.002 * s, 0.004 * s)),
                    0.0028 * s * (0.7 + 0.7 * mus), 0.016 * s)
    # scapulae
    for tag in ("L", "R"):
        c = Vector(lm[f"acromion.{tag}"]) + Vector((-0.030 * s * (1 if tag == "L" else -1), -0.048 * s, -0.045 * s))
        stack.bump(c, 0.006 * s * (0.5 + mus), sigma=(0.045 * s, 0.028 * s, 0.055 * s),
                   direction=Vector((-0.15 * (1 if tag == "L" else -1), -1, 0.12)))
    # sternum plate (TORSO B: y acompanha a parede nova, mais fina)
    stack.bump(Vector((0, anat.chest_half() * 0.45 + 0.008 * s, anat.z("inframammary") + 0.055 * s)),
               0.0035 * s, sigma=(0.028 * s, 0.020 * s, 0.050 * s))
    # abdominal panel tone (linea alba groove via mild centre damp handled by muscle)
    if mus > 0.55 and fat < 0.42:
        z0 = anat.z("waist") - 0.010 * s
        for row in range(3):
            for col in (-1, 1):
                c = Vector((col * 0.032 * s, anat.waist_half() * 0.72, z0 - row * 0.030 * s))
                stack.bump(c, 0.0022 * s * (mus - 0.55) * 3.0, sigma=(0.022 * s, 0.014 * s, 0.014 * s))
    # thenar eminence (palms) — S3.8, desvio de âmbito declarado
    # (docs/S3_8_HANDS.md §7.1): medido, a amplitude antiga de 0.0060·estatura
    # (10.2 mm) num sigma de (51, 37, 76) mm inflacionava a palma DEPOIS do loft
    # — com as dimensões da mão já corrigidas a espessura media 33.3 mm em vez
    # dos 28.7 mm devidos à geometria. O valor 0.0024·estatura (4.1 mm) é
    # INFERRED do orçamento de espessura; não há fonte recolhida para a altura
    # da eminência tenar (declarado no contrato).
    if include_hands:
        for tag, side in (("L", 1), ("R", -1)):
            c = Vector(lm[f"wrist.{tag}"]) + Vector((side * 0.020 * s, 0.0, -0.045 * s))
            stack.bump(c, 0.0024 * s, sigma=(0.024 * s, 0.018 * s, 0.030 * s))
    # slight organic asymmetry: one breast 3% fuller, one glute rounder (seeded)
    a = spec.face.asymmetry * 0.04
    if a > 0:
        stack.bump(Vector(lm["bust.L"]), anat.bust_protrusion() * 0.05 * a / 0.04 if a else 0.0,
                   sigma=(0.048 * s, 0.040 * s, 0.055 * s), direction=Vector((0, 1, 0)))

    b.verts = stack.apply(b.verts)

    # T1 COSTAS — campo sagital em S sobre os anéis do tronco, DEPOIS do stack
    # (a curva é do tronco, não do tecido mole: busto/glúteos/trapézio já
    # aplicados; o campo só desloca a face posterior, frente/larguras intactas).
    # HCG_T1_AMP=0 desliga o campo (controlo A/B, mesma topologia).
    apply_sagittal_back(b, anat.stature)

    # S3.3 — plano do chão.  Medido antes: min(z) = −7.70 mm (3 vértices do
    # calcanhar).  O clamp que existe em feet.py usa ``Deformer("flatten")`` com
    # o plano em z = +sole_z e uma correcção suavizada que nunca chega ao plano
    # (por construção: disp = over·soft/(over+soft) < over), e só toca a casca do
    # pé — o fundo da perna também passava abaixo de zero.  Aqui o chão é o chão:
    # clamp duro, aplicado à malha final do corpo (depois dos campos, para que
    # nenhum campo possa voltar a empurrar geometria para baixo do plano).  O
    # critério medido é min(z) == 0.0 e nenhum vértice abaixo de zero.
    floor = 0.0
    for i, v in enumerate(b.verts):
        if v.z < floor:
            b.verts[i] = Vector((v.x, v.y, floor))

    # ------------------------------------------------------------- armpit rim
    # crease a subtle lat/anterior axillary fold line? authored by loops: skip
    res = BodyResult(builder=b, joints=dict(anat.landmarks), notes=notes)
    return res
