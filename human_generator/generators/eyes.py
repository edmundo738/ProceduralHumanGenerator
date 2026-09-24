# -*- coding: utf-8 -*-
"""Eyeballs (sclera + cornea cap) and eyelids with a palpebral fissure.

The globe is a lat/long sphere welded to a protruding cornea cap (real
corneal radius ≈ 0.65 × globe radius, ~0.7 mm proud of the sclera).
``iris_mask``/``cornea_mask`` vertex groups drive the iris shader — material
layers without material splits.  Eyelids are swept onto a slightly larger
sphere, with the upper margin following an almond curve whose amplitude is
the eye aperture (blink/shape-key friendly); the margin polyline is exported
for the eyelash generator.
"""
from __future__ import annotations

import math

from ..core._math import Vector, clamp, mix
from ..core.topology import MeshBuilder


def eye_axis(anat, side: int) -> Vector:
    """Outward axis of the eye (from globe centre through the cornea)."""
    tag = "L" if side > 0 else "R"
    c = Vector(anat.landmarks[f"eye.{tag}"])
    front = anat.face_front(c.x, c.z, c.y * 0 + 0.05)
    d = front - c
    if d.length_squared < 1e-8:
        d = Vector((0.0, 1.0, 0.0))
    return d.normalized()


def palpebral_fissure(anat, c: Vector, r: float, side: int):
    """Return (upper_fn, lower_fn): margin elevation (rad) as f(x in −1..1)."""
    f = anat.spec.face
    tilt = 0.10 * f.eye_width
    up = 0.175 * (0.85 + 0.30 * f.eye_width)      # aperture half-height, rad
    dn = 0.115 * (0.85 + 0.30 * f.eye_width)

    def _curve(t: float, amp: float) -> float:
        x = clamp(t, -1.0, 1.0)
        return amp * abs(math.cos(x * math.pi * 0.5)) ** 1.35 * math.copysign(1.0, math.cos(x * math.pi * 0.5) or 1.0)

    def upper_fn(t: float) -> float:
        return _curve(t, up) + tilt * t * up + 0.020

    def lower_fn(t: float) -> float:
        return -_curve(t, dn) + tilt * t * dn - 0.015

    return upper_fn, lower_fn


def build_eyes(spec, anat, into: MeshBuilder) -> dict:
    h = anat.h
    r = 0.0555 * h                       # globe radius ≈ 12.2 mm @ 1.70 m
    info: dict[str, dict] = {}
    for side, tag in ((1, "L"), (-1, "R")):
        c = Vector(anat.landmarks[f"eye.{tag}"])
        ax = eye_axis(anat, side)
        up_fn, dn_fn = palpebral_fissure(anat, c, r, side)
        right = ax.cross(Vector((0, 0, 1.0)))
        if right.length_squared < 1e-8:
            right = Vector((1.0, 0.0, 0.0))
        right = right.normalized()
        upv = right.cross(ax).normalized()
        if side < 0:
            # S3.1 — espelho exacto do referencial.  ``ax_R = espelho(ax_L)``
            # (as landmarks já são espelhadas) e o produto externo não é
            # equivariante sob reflexão — ``(Ma)×(Mb) = -M(a×b)`` — logo
            # ``right = ax × z`` saía com o sinal trocado no olho direito:
            # medido, 240 de 240 vértices de pálpebra não tinham par espelhado
            # (a pálpebra direita era a esquerda *sem* espelho).  ``upv`` já
            # saía correcto (dois trocos de sinal cancelam); só ``right`` é
            # invertido, e a parametrização esférica (theta ao longo de
            # ``right``) espelha então exactamente.
            right = Vector((-right.x, right.y, right.z))

        def sph(theta: float, phi: float, radius: float) -> Vector:
            # theta: azimuth along `right`, phi: elevation along `upv` from axis
            d = (ax * math.cos(phi) + upv * math.sin(phi))
            d = d.normalized()
            d += right * (theta * math.cos(phi))
            return c + d.normalized() * radius

        # ---- globe: latitude rings from back pole toward the iris --------
        # k = 0 (phi = -pi/2) IS the back pole: cos(phi) = 6.1e-17, so every one
        # of its 13 points lands on the same spot and cap_pole then stacks a
        # second collapsed ring on top of it (26 coincident verts per eye => 52
        # zero-area faces; docs/RESEARCH_GATE_02.md).  The pole is now built by
        # cap_pole alone.  The globe is a single loft: splitting it into two
        # lofts re-emitted the shared limbus ring (13 more coincident pairs per
        # eye).  Only the face material differs across the limbus, and
        # materials/skin.py:build_iris is driven by object coordinates and
        # normals — not by UVs — so a single uv_rect is exact.
        rings = []
        NR, NC = 8, 12
        face0 = len(into.faces)
        for k in range(1, NR + 1):
            phi = mix(-math.pi * 0.5, math.pi * 0.34, k / NR)
            rings.append([sph(mix(-1, 1, j / NC) * math.pi * 0.5, phi, r) for j in range(NC + 1)])
        res = into.loft(rings, close=False, region="eye", material="eye",
                        uv_rect=(0.0, 1.0, 0.0, 1.0), register=f"eye.{tag}",
                        cap_start="pole", cap_end="none")
        ids = res["rings"]                 # k = 1..8 (k = 0 was the pole)
        # Iris material is assigned STRUCTURALLY — a face is iris iff all of its
        # vertices belong to rings k >= 5 (limbus .. last) — never by position in
        # the face list.  Measured: slicing the last N appended faces instead
        # mis-labels the back pole (it is appended last) as iris and splits one
        # band (10 quads iris / 2 quads eye), even though the per-material totals
        # happen to match.  The pupil-facing pole cap is front-only and is the
        # explicit ``cap_pole`` call further down.
        iris_verts = set(ids[4]) | set(ids[5]) | set(ids[6]) | set(ids[7])
        for fi in range(face0, len(into.faces)):
            if all(v in iris_verts for v in into.faces[fi]):
                into.face_mat[fi] = "iris"
        front_ids = set(ids[4])            # limbus ring (k = 5): eyelid anchor
        for ring in ids[:5]:               # k = 1..5 (the old pass covered k = 0..5)
            for vi in ring:
                d = into.verts[vi] - c
                if d.length < 1e-9:
                    continue
                cosang = d.normalized().dot(ax)
                if cosang > math.cos(math.radians(36)):
                    into.set_group(f"iris.{tag}", vi, 1.0)
                if cosang > math.cos(math.radians(15)):
                    into.set_group(f"cornea.{tag}", vi, 1.0)
        # UVs.  Measured on the pre-S2 tree: the globe loft (6 rings) registered
        # rings 0..5 with v = k/5 and u = i/12, and the iris loft emitted a
        # SECOND, unregistered copy of rings 5..8 carrying the iris rect
        # (u 0.5..1.0, v = 0, 1/3, 2/3, 1).  Removing that duplicate seam leaves
        # one vertex set for those four rings, so a single mapping must be
        # chosen: the sclera rings (1..4, 8 of the 16 surviving ring/eye pairs)
        # keep their pre-S2 values bit for bit, and the limbus..pole rings keep
        # the iris mapping, i.e. the region the iris faces were drawn from
        # before.  The globe copy's v = 1.0 for the limbus no longer exists
        # anywhere, because the vertex that carried it is gone.
        for k in range(0, 4):                       # rings 1..4  -> v = k/5 (pre-S2)
            v = mix(0.0, 1.0, (k + 1) / 5.0)
            for i, vi in enumerate(ids[k]):
                into.uvs[vi] = (mix(0.0, 1.0, i / NC), v)
        for k in range(4, len(ids)):                # rings 5..8  -> iris rect
            v = mix(0.0, 1.0, (k - 4) / (len(ids) - 1 - 4))
            for i, vi in enumerate(ids[k]):
                into.uvs[vi] = (mix(0.5, 1.0, i / NC), v)
        into.cap_pole(ids[-1], +1, region="eye", material="iris", shrink=0.42, uv_v=1.0)
        into.rings[f"eye.{tag}.front"] = [i for i in front_ids]

        # ---- cornea cap (protruding shell, glass material) ----------------
        cr = r * 0.64
        cc = c + ax * (r * 0.40)
        cor_rings = []
        for k in range(4):
            phi = mix(math.pi * 0.44, math.pi * 0.06, k / 3)   # base → apex
            cor_rings.append([cc + (ax * math.cos(phi) +
                                    (upv * math.sin(uu) + right * math.cos(uu)) * math.sin(phi)) * cr
                              for uu in [2 * math.pi * j / 10 for j in range(10)]])
        into.loft(cor_rings, close=True, region="cornea", material="cornea",
                  uv_rect=(0.0, 1.0, 0.0, 1.0), cap_start="none", cap_end="pole")

        # ---- eyelids --------------------------------------------------------
        margin_pts: dict[str, list[Vector]] = {"upper": [], "lower": []}
        for which, fn, sgn in (("upper", up_fn, 1.0), ("lower", dn_fn, -1.0)):
            NROW, NCOL = 5, 9
            rows = []
            for k in range(NROW + 1):
                row = []
                t_list = [mix(-1, 1, j / NCOL) for j in range(NCOL + 1)]
                for t in t_list:
                    phi0 = fn(t)
                    spread = mix(0.0, 2.35 if which == "upper" else 1.25, k / NROW)
                    phi = phi0 + sgn * spread * 0.55
                    rr = r * (1.028 - 0.075 * k / NROW)      # rim tucks under the socket skin
                    p = sph(t * 0.92, phi, rr)
                    if k > 0:
                        p = p - ax * (0.0165 * h) * (k / NROW) ** 1.5
                    row.append(p)
                rows.append(row)
                if k == 0:
                    margin_pts[which] = list(row)
            # loft rows; the rim rows (k=NROW) get tucked and welded by fields
            created = into.loft(rows, close=False, region="eyelid", material="skin",
                                uv_rect=(0.0, 1.0, 0.0, 1.0))
            for ring in created["rings"][1:]:
                for vi in ring:
                    into.set_group(f"eyelid.{tag}", vi, 1.0)
            into.crease_ring(created["rings"][0], 0.28)   # lash line holds
        info[tag] = {"centre": c, "axis": ax, "right": right, "up": upv, "r": r,
                     "margin_upper": margin_pts["upper"], "margin_lower": margin_pts["lower"]}
    return info


def eyelid_lids_anatomy(spec, anat, eye_c: Vector, eye_r: float, side: int):
    """Aperture curve evaluator (shared with shape keys / hair)."""
    return palpebral_fissure(anat, eye_c, eye_r, side)
