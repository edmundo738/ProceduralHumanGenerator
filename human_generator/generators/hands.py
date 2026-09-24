# -*- coding: utf-8 -*-
"""Anatomical hand: lofted palm + 4 rays + opposable thumb, per-phalanx groups.

Hand space: ``+x`` = thumb side (lateral), ``+y`` = volar (palm normal),
``+z`` = distal.  Built once per side from landmarks so both hands come out
correctly chiral (the side sign flips ``x`` → the merge's matrix handles
winding).  Finger lengths follow the 0.93/1.0/0.96/0.74 ray ratio set, palm
length/finger ≈ 0.52/0.48 of hand length (anthropometric for adults).
"""
from __future__ import annotations

import math

from ..core._math import Matrix, Vector
from ..core.topology import MeshBuilder, make_section
from .digits import DigitPlan, build_digit

RAY_ORDER = ("index", "middle", "ring", "pinky")
RAY_LEN = {"index": 0.93, "middle": 1.0, "ring": 0.96, "pinky": 0.74}
RAY_RAD = {"index": 0.94, "middle": 1.0, "ring": 0.93, "pinky": 0.80}
RAY_FLEX = {"index": (0.16, 0.20, 0.12), "middle": (0.18, 0.23, 0.14),
            "ring": (0.22, 0.26, 0.16), "pinky": (0.26, 0.30, 0.18)}
RAY_SPREAD = {"index": -0.055, "middle": -0.010, "ring": 0.030, "pinky": 0.075}


def _hand_basis(wrist: Vector, distal: Vector, side: int):
    """Referencial local da mão; o lado direito é o **espelho exato** do esquerdo.

    S3.1 — medido: construir o referencial independentemente por lado com
    ``volar0 = (-side*0.30, -0.90, -0.10)`` e ``x0 = volar0.cross(z) * side``
    **não** dá um espelho, porque o produto externo não é equivariante sob
    reflexão (``(Ma) × (Mb) = -M(a × b)`` para um espelho M).  Resultado medido:
    as duas mãos diferiam até 13.4 mm (Hausdorff) e 41.6 % dos vértices da
    personagem não tinham par espelhado (``docs/S3_BODY_INTEGRATION.md`` §3).
    A correcção constrói o referencial no espaço canónico (lado esquerdo) e
    espelha-o explicitamente para o lado direito — o lado esquerdo fica
    exactamente como estava, o direito passa a ser o seu espelho.
    """
    mirror = side < 0
    w = Vector(wrist)
    d = Vector(distal)
    if mirror:                                  # trabalhar no lado canónico
        w = Vector((-w.x, w.y, w.z))
        d = Vector((-d.x, d.y, d.z))
    z = (d - w)
    if z.length_squared < 1e-9:
        z = Vector((0, 0, -1.0))
    z = z.normalized()
    volar0 = Vector((-0.30, -0.90, -0.10)).normalized()
    x0 = volar0.cross(z)
    if x0.length_squared < 1e-9:
        x0 = Vector((1.0, 0.0, 0.0))
    x = x0.normalized()
    y = z.cross(x).normalized()
    rows = ((x.x, y.x, z.x, w.x),
            (x.y, y.y, z.y, w.y),
            (x.z, y.z, z.z, w.z),
            (0.0, 0.0, 0.0, 1.0))
    M = Matrix(rows)
    if mirror:
        M = Matrix(((-1.0, 0.0, 0.0, 0.0), (0.0, 1.0, 0.0, 0.0),
                    (0.0, 0.0, 1.0, 0.0), (0.0, 0.0, 0.0, 1.0))) @ M
        x = Vector((-x.x, x.y, x.z))
        y = Vector((-y.x, y.y, y.z))
        z = Vector((-z.x, z.y, z.z))
    return M, x, y, z


def build_hand(spec, anat, *, side: int, rng) -> tuple[MeshBuilder, dict]:
    tag = "L" if side > 0 else "R"
    lm = anat.landmarks
    wrist = Vector(lm[f"wrist.{tag}"])
    palm_tip = Vector(lm[f"hand.{tag}"])
    H = anat.h
    hand_len = anat.hand_length()
    palm_len = hand_len * 0.52
    finger_len = hand_len * 0.48 * spec.body.finger_length
    # S3.8 — dimensões da palma com fonte (docs/S3_8_HANDS.md §2):
    #   largura da mão (mulher p50) 76 mm = 0.427·comprimento (FAA/DOT Ap. B);
    #   espessura ≤ 0.165·comprimento.
    # BASELINE medido (``6b63242``, instrumento ``core.integration.hand_metrics``):
    # largura 123.6 mm (1.63× os 76 mm canónicos) e espessura 57.2 mm (0.314·L) —
    # a mão lia-se como uma pá.  Mecanismo: ``half_b = 0.285·L`` com factor de
    # anel até 1.163 dava 57.4 mm de MEIA-largura nos nós; ``t_half = 0.118·L``
    # dava ≈ 43 mm geométricos que, somados ao campo tenar do ``body.py``,
    # chegavam aos 57.2 mm medidos.
    # DEPOIS (medido): meia-largura de corpo 0.190·L ⇒ 77.5 mm de largura;
    # espessura de corpo 0.066·L ⇒ 28.7 mm (0.159·L, limite H3 0.165·L).
    half_b = hand_len * 0.190 * spec.body.palm_breadth
    t_half = hand_len * 0.066 * (1.0 + 0.25 * spec.body.fat_level)

    M, x_ax, y_ax, z_ax = _hand_basis(wrist, palm_tip, side)
    volar = y_ax

    b = MeshBuilder(f"hand.{tag}")

    # ---- palm (loft of superelliptic rings) -------------------------------
    rings = []
    N = 8
    for i in range(N + 1):
        t = i / N
        # S3.5 — cintura do punho.  Medido: a raiz da palma tinha 87.5 mm de
        # largura contra 44–49 mm de diâmetro do antebraço, ou seja a mão era
        # mais larga que o braço na junção e a raiz ficava FORA da casca do
        # antebraço (0/12 amostras dentro).  Anatomicamente o punho é uma
        # cintura estreita; ``neck`` estreita as primeiras estações (0.45 na
        # raiz, 1.0 a partir de t=0.25) e a raiz sobe para dentro do antebraço.
        zc = -hand_len * 0.09 + t * (palm_len + hand_len * 0.09)
        neck = 0.45 + 0.55 * min(1.0, t / 0.25)
        taper = 0.80 + 0.20 * math.sin(math.pi * min(1.0, t * 1.12)) if t < 0.9 else 0.86
        w = half_b * (0.84 + 0.30 * t) * (1.0 if t < 1.0 else 1.02) * neck
        d = t_half * (0.92 + 0.16 * math.sin(math.pi * t)) * neck
        # wrist end narrower, knuckle end wide & flat; slight cup toward volar
        y_off = t_half * 0.10 * math.sin(math.pi * t)
        secs = make_section((0.0, y_off, zc), tangent=(1, 0, 0), front=(0, 1, 0),
                            width=w, depth=d, front_scale=1.0 + 0.10 * t,
                            back_scale=1.0 - 0.06 * t, superellipse=2.1 + 0.5 * t)
        pts = [M @ p for p in secs.points(12)]
        rings.append(pts)
    created = b.loft(rings, close=True, region="skin", material="skin",
                     uv_rect=(0.10, 0.90, 0.0, 0.45), register=f"hand.{tag}")
    # palm-side verts get the "palm" region (rougher skin, no hair in shader)
    first_ring = created["rings"][0]
    last_ring = created["rings"][-1]
    n_ring = 12
    for k in range(len(created["rings"])):
        for j, vi in enumerate(created["rings"][k]):
            p = b.verts[vi]
            local = M.inverted() @ p
            if local.y > t_half * 0.30:
                b.regions[vi] = "palm"

    knuckle_z = palm_len
    # S3.8 — espaçamento dos nós: 0.127·L ⇒ índice↔mindinho medido 65.8 mm =
    # 0.365·L (canónico H4 0.36–0.42·L).  Antes: 0.118·L ⇒ 61.2 mm = 0.336·L.
    sp = hand_len * 0.127
    knucklers = {}
    for name in RAY_ORDER:
        idx = RAY_ORDER.index(name)
        xk = (idx - 1.5) * sp
        dome = palm_len + hand_len * 0.030 * (1.0 - abs(idx - 1.5) / 1.5)
        knucklers[name] = (xk, -0.006 * hand_len, dome)

    # crease at knuckle line
    b.crease_ring(last_ring, 0.30)

    # ---- fingers -----------------------------------------------------------
    joints: dict[str, Vector] = {}
    for name in RAY_ORDER:
        xk, yk, zk = knucklers[name]
        flen = finger_len * RAY_LEN[name]
        flexed = RAY_FLEX[name]
        spread = RAY_SPREAD[name] + rng.f(-0.02, 0.02)
        # distal direction in hand space: spread in x-z plane, flex bends to volar
        d0 = Vector((math.sin(spread), 0.0, math.cos(spread)))
        base = Vector((xk, yk, zk))
        seg0, seg1, seg2 = flen * 0.46, flen * 0.31, flen * 0.23
        mcp = M @ (base + d0 * (-hand_len * 0.010))
        p0 = mcp
        p1 = M @ (base + d0 * seg0)
        p2 = M @ (base + d0 * (seg0 + seg1))
        p3 = M @ (base + d0 * (seg0 + seg1 + seg2))
        plan = DigitPlan(kind="finger", name=name, anchors=[p0, p1, p2, p3],
                         # S3.8 — raio dos dedos 0.046·L: com 0.052·L os dedos
                         # encostavam-se (folga medida 0.7 mm no médio↔anelar);
                         # agora 4.3 / 3.1 / 5.4 mm (critério H5: ≥ 1 mm).
                         base_radius=hand_len * 0.046 * RAY_RAD[name],
                         flex=list(flexed), volar=Vector((y_ax.x, y_ax.y, y_ax.z)).normalized(),
                         flatness=0.90, segments=3, ring_n=8, nail=True)
        build_digit(b, plan, material="skin", group_prefix=f"{tag}.")
        joints[f"{name}.mcp"] = p0
        joints[f"{name}.pip"] = p1
        joints[f"{name}.dip"] = p2
        joints[f"{name}.tip"] = p3

    # ---- thumb (opposable: CMC saddle, 2 phalanges) ------------------------
    tb = Vector((half_b * 0.66, -t_half * 0.18, palm_len * 0.26))
    tdir = Vector((0.62, 0.18, 0.76)).normalized()
    tlen = finger_len * 0.62
    cmc = M @ (tb - tdir * hand_len * 0.02)
    mcp = M @ (tb + tdir * tlen * 0.42)
    ip = M @ (tb + tdir * tlen * 0.72)
    tip = M @ (tb + tdir * tlen * 1.0)
    tplan = DigitPlan(kind="finger", name="thumb", anchors=[cmc, mcp, ip, tip],
                      base_radius=hand_len * 0.052, flex=(0.14, 0.20, 0.12),
                      volar=Vector((y_ax.x, y_ax.y, y_ax.z)).normalized(),
                      flatness=0.92, segments=3, ring_n=8, nail=True)
    build_digit(b, tplan, material="skin", group_prefix=f"{tag}.")
    joints["thumb.mcp"] = mcp
    joints["thumb.ip"] = ip
    joints["thumb.tip"] = tip
    # thenar eminence is added by the body-level field stack

    joints["palm_center"] = M @ Vector((0, 0, palm_len * 0.5))
    joints["wrist"] = wrist
    for key in list(joints):
        joints[f"hand.{tag}.{key}"] = joints.pop(key)

    return b, joints
