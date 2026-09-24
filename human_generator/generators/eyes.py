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

        def sph(theta: float, phi: float, radius: float) -> Vector:
            # theta: azimuth along `right`, phi: elevation along `upv` from axis
            d = (ax * math.cos(phi) + upv * math.sin(phi))
            d = d.normalized()
            d += right * (theta * math.cos(phi))
            return c + d.normalized() * radius

        # ---- globe: latitude rings from back pole toward the iris --------
        rings = []
        NR, NC = 8, 12
        for k in range(NR + 1):
            phi = mix(-math.pi * 0.5, math.pi * 0.34, k / NR)
            rings.append([sph(mix(-1, 1, j / NC) * math.pi * 0.5, phi, r) for j in range(NC + 1)])
        res = into.loft(rings, close=False, region="eye", material="eye",
                        uv_rect=(0.0, 1.0, 0.0, 1.0), register=f"eye.{tag}",
                        cap_start="pole", cap_end="none")
        ids = res["rings"]
        front_ids = set(ids[-1]) | set(ids[-2])
        for ring in ids:
            for vi in ring:
                d = into.verts[vi] - c
                if d.length < 1e-9:
                    continue
                cosang = d.normalized().dot(ax)
                if cosang > math.cos(math.radians(36)):
                    into.set_group(f"iris.{tag}", vi, 1.0)
                if cosang > math.cos(math.radians(15)):
                    into.set_group(f"cornea.{tag}", vi, 1.0)
        into.rings[f"eye.{tag}.front"] = [i for i in front_ids]

        # ---- cornea cap (protruding shell, glass material) ----------------
        cr = r * 0.64
        cc = c + ax * (r * 0.40)
        cor_rings = []
        for k in range(4):
            phi = mix(math.pi * 0.44, math.pi * 0.06, k / 3)   # base → apex
            cor_rings.append([cc + (ax * math.cos(phi) +
                                    (upv * math.sin(uu) + right * math.cos(uu)) * math.sin(phi)) * cr
                              for uu in [2 * math.pi * j / 10 for j in range(11)]])
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
                    spread = mix(0.0, 1.9 if which == "upper" else 1.05, k / NROW)
                    phi = phi0 + sgn * spread * 0.55
                    rr = r * (1.045 - 0.10 * k / NROW)      # rim tucks under the socket skin
                    p = sph(t * 0.92, phi, rr)
                    if k > 0:
                        p = p - ax * (0.013 * h) * (k / NROW) ** 1.6
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
