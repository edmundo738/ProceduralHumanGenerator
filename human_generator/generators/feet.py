# -*- coding: utf-8 -*-
"""Foot + toes.

Foot space: ``+z`` toward the toes (forward), ``+y`` up (dorsum), ``+x``
lateral — so the big toe sits medially (−x for L after side flip).  A
flatten-clamp field guarantees a flat sole (needed for standing), while the
transverse arch and the metatarsal fan do the organic shaping.
"""
from __future__ import annotations

import math

from ..core._math import Matrix, Vector
from ..core.topology import MeshBuilder, make_section
from .digits import DigitPlan, build_digit

TOE_LEN = {"big": 1.0, "long": 0.88, "second": 0.80, "third": 0.70, "little": 0.58}
TOE_RAD = {"big": 1.0, "long": 0.86, "second": 0.78, "third": 0.70, "little": 0.58}


def _foot_basis(ankle: Vector, toe: Vector, side: int) -> Matrix:
    """Referencial local do pé; o lado direito é o **espelho exato** do esquerdo.

    S3.1 — mesma correcção do referencial da mão (``hands.py:_hand_basis``):
    ``x = z.cross(y) * side`` não produz um espelho (o produto externo não é
    equivariante sob reflexão).  Medido antes: 7.5–8.3 mm de Hausdorff entre os
    dedos dos dois pés.  O lado esquerdo mantém-se exactamente como estava.
    """
    mirror = side < 0
    a = Vector(ankle)
    t = Vector(toe)
    if mirror:                                  # trabalhar no lado canónico
        a = Vector((-a.x, a.y, a.z))
        t = Vector((-t.x, t.y, t.z))
    z = (t - a)
    z.y = max(z.y, 0.35 * z.length)             # sempre algum avanço
    z = z.normalized()
    y = Vector((0, 0, 1.0))
    y -= z * y.dot(z)
    y = y.normalized()
    x = z.cross(y)
    if x.length_squared < 1e-9:
        x = Vector((1.0, 0.0, 0.0))
    x = x.normalized()
    y = z.cross(x).normalized()
    rows = ((x.x, y.x, z.x, a.x),
            (x.y, y.y, z.y, a.y),
            (x.z, y.z, z.z, a.z),
            (0.0, 0.0, 0.0, 1.0))
    M = Matrix(rows)
    if mirror:
        M = Matrix(((-1.0, 0.0, 0.0, 0.0), (0.0, 1.0, 0.0, 0.0),
                    (0.0, 0.0, 1.0, 0.0), (0.0, 0.0, 0.0, 1.0))) @ M
    return M


def build_foot(spec, anat, *, side: int, rng) -> tuple[MeshBuilder, dict]:
    tag = "L" if side > 0 else "R"
    lm = anat.landmarks
    ankle = Vector(lm[f"ankle.{tag}"])
    toe = Vector(lm[f"toe_end.{tag}"])
    heel = Vector(lm[f"heel.{tag}"])
    ball = Vector(lm[f"ball.{tag}"])
    M = _foot_basis(ankle, toe, side)
    foot_len = (toe - ankle).length
    sole_drop = ankle.z - 0.004 * anat.stature  # sole plane in world z

    b = MeshBuilder(f"foot.{tag}")
    width_ball = foot_len * 0.31 * (1.0 + 0.25 * spec.body.fat_level)

    # longitudinal stations in foot space (origin at ankle)
    stations = [
        (-foot_len * 0.55, width_ball * 0.52, 0.030, 1.0, 1.0, 2.4),   # behind heel
        (-foot_len * 0.30, width_ball * 0.74, 0.030, 1.02, 0.98, 2.5),  # heel
        (-foot_len * 0.05, width_ball * 0.80, 0.028, 1.02, 0.90, 2.4),  # midfoot (arch high)
        (foot_len * 0.18, width_ball * 0.92, 0.026, 1.0, 0.92, 2.3),    # mid
        (foot_len * 0.34, width_ball * 1.0, 0.024, 0.98, 0.95, 2.2),    # ball (widest)
        (foot_len * 0.42, width_ball * 0.94, 0.022, 0.96, 0.92, 2.1),   # toe pads
        (foot_len * 0.46, width_ball * 0.55, 0.018, 0.9, 0.9, 2.0),    # pad front
    ]
    rings = []
    for (zf, w, hh, fs, bs, e) in stations:
        # lift the arch: y offset of the centreline
        y_off = 0.030 + 0.055 * max(0.0, 1.0 - abs(zf + foot_len * 0.06) / (foot_len * 0.45)) \
            if -foot_len * 0.2 < zf < foot_len * 0.2 else 0.030
        depth = max(0.014, sole_drop * 0.0 + 0.048 * anat.stature * 0.36 + y_off * 0.30)
        secs = make_section((0.0, depth * 0.28 + y_off, zf), tangent=(1, 0, 0), front=(0, 1, 0),
                            width=w, depth=depth, front_scale=fs, back_scale=bs, superellipse=e)
        rings.append([M @ p for p in secs.points(12)])
    # S3.5 — o pé era uma casca ABERTA (24 arestas de fronteira medidas em
    # z 0.012..0.178): via-se o interior através da boca do tornozelo e da ponta.
    created = b.loft(rings, close=True, region="skin", material="skin",
                     uv_rect=(0.05, 0.95, 0.0, 0.4), register=f"foot.{tag}",
                     cap_start="pole", cap_end="pole")
    # sole region on bottom side
    inv = M.inverted()
    for k, ring in enumerate(created["rings"]):
        for vi in ring:
            loc = inv @ b.verts[vi]
            if loc.y < -depth * 0.35:
                b.regions[vi] = "sole"

    joints: dict[str, Vector] = {}
    # toes from the ball row
    ball_row = [M @ Vector((0, 0, foot_len * 0.34))]
    toe_x = [-width_ball * 0.62, -width_ball * 0.30, width_ball * 0.02,
             width_ball * 0.30, width_ball * 0.55]
    volar_foot = Vector((0, -1, 0.05))  # toward sole → toes flex down
    volar_w = (M.to_4x4() @ volar_foot) - (M.to_4x4() @ Vector((0, 0, 0)))
    volar_w = volar_w.normalized()
    for ti, name in enumerate(TOE_LEN.keys()):
        base = M @ Vector((toe_x[ti] * 0.9, -0.004, foot_len * 0.40))
        tl = foot_len * 0.10 * TOE_LEN[name] * (0.9 + 0.2 * rng.f(0.9, 1.1))
        dirv = M.to_4x4() @ Vector((toe_x[ti] * 0.05, 0.02, 1.0)) - M.to_4x4() @ Vector((0, 0, 0))
        dirv = dirv.normalized()
        a0 = base
        a1 = base + dirv * tl * 0.55
        a2 = base + dirv * tl
        plan = DigitPlan(kind="toe", name=name, anchors=[a0, a1, a2],
                         base_radius=foot_len * 0.040 * TOE_RAD[name],
                         flex=(0.05, 0.10), volar=volar_w,
                         flatness=0.85, segments=2, ring_n=8, nail=(ti == 0))
        build_digit(b, plan, material="skin", group_prefix=f"{tag}.")
        joints[f"{name}.mcp"] = a0
        joints[f"{name}.tip"] = a2
    joints["ankle"] = ankle
    joints["heel"] = heel
    joints["toe_end"] = toe
    for key in list(joints):
        joints[f"foot.{tag}.{key}"] = joints.pop(key)

    # ---- clamp sole onto the ground plane (nothing below z≈0) -------------
    from ..core.field import Deformer
    sole_z = 0.0035 * anat.stature
    flat = Deformer("flatten", plane_n=(0.0, 0.0, -1.0), plane_d=-sole_z,
                    amp=0.0, sigma=(0.008, 0.008, 0.008))
    for i, p in enumerate(b.verts):
        d = flat.evaluate(p, None)
        if d.length_squared > 1e-12:
            b.verts[i] = p + d
    return b, joints
