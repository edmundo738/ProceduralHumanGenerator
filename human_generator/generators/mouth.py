# -*- coding: utf-8 -*-
"""Mouth complex: lips, oral cavity, gingival arches, individual teeth, tongue.

The lips are a tube swept around an almond aperture curve in the **x–z**
plane (the mouth plane), with y = protrusion only — the classic mistake of
mapping "height" to y produces a floating disc, so the axes are pinned here.
Teeth are 14-per-arch (no third molars), modelled as 3-ring lofts with
per-type widths/heights/cusps, rotated along the dental parabola.  The
tongue is a flattened 6-station loft with a central groove crease.
"""
from __future__ import annotations

import math

from ..core._math import Vector, clamp, mix
from ..core.topology import MeshBuilder, make_section


# ----------------------------------------------------------------------------- aperture
def mouth_aperture(anat, half_w: float, open_amt: float = 0.0):
    """Closed curve (x,z,y-plane offsets) around the mouth centre."""
    lm = anat.landmarks["mouth"]
    h = anat.h
    f = anat.spec.face
    up_amp = 0.115 * half_w + 0.006 * h * f.lip_fullness
    dn_amp = 0.150 * half_w + 0.008 * h * f.lip_fullness
    bow = 0.018 * h * f.cupid_bow

    def curve(t: float):
        a = 2.0 * math.pi * t
        x = math.cos(a) * half_w
        s = math.sin(a)
        if s >= 0.0:
            z = s * up_amp * (1.0 + 0.10 * open_amt)
            z += bow * math.exp(-((abs(x) / max(1e-6, half_w * 0.16)) ** 2)) - 0.42 * bow
        else:
            z = s * dn_amp * (1.0 + 1.7 * open_amt)
        return x, z

    return curve


def build_lips(into: MeshBuilder, spec, anat, mouth_open: float = 0.0) -> None:
    h = anat.h
    lm = anat.landmarks
    mouth = Vector(lm["mouth"])
    corners = Vector(lm["mouth_corner.L"])
    half_w = (corners.x - mouth.x) if corners.x != 0 else 0.038 * anat.stature
    curve = mouth_aperture(anat, half_w, mouth_open)
    f = spec.face
    N_A, N_T = 16, 5
    protr = 0.0135 * h * f.lip_fullness           # vermilion forward reach
    in_depth = 0.020 * h                          # inner mucosa depth
    rows: list[list[Vector]] = []
    for k in range(N_T + 1):
        t = k / N_T
        row = []
        for a in range(N_A):
            x, z = curve(a / N_A)
            surf_y = anat.skull_front_y(mouth.x + x, mouth.z + z) - 0.004 * h
            y = mix(mouth.y - in_depth, surf_y, smooth01(t, 0.15, 0.85))
            # vermilion bulge: strongest mid-band, wider on the lower lip
            band = math.sin(math.pi * t) ** 1.3
            lower = 1.0 if z < 0 else 0.72
            bulge = band * protr * lower * (0.75 + 0.65 * f.lip_fullness * 0.5)
            row.append(Vector((mouth.x + x, y + bulge, mouth.z + z)))
        rows.append(row)
    created = into.loft(rows, close=True, region="lip", material="lip",
                        uv_rect=(0.0, 1.0, 0.0, 1.0), register="lips")
    # aperture rim (inner ring) crease holds the dark line
    into.crease_ring(created["rings"][0], 0.40)


def smooth01(x, a, b):
    x = clamp((x - a) / max(1e-6, b - a), 0.0, 1.0)
    return x * x * (3.0 - 2.0 * x)


# ----------------------------------------------------------------------------- teeth
def dental_arch(anat, half_w: float, depth: float):
    """Return fn(u∈[-1,1]) → (x, y_front_offset) for the upper arch parabola."""
    def arch(u: float):
        u = clamp(u, -1.0, 1.0)
        x = u * half_w
        y = depth * (1.0 - 0.62 * u * u)      # molars recede
        return x, y
    return arch


TOOTH_TYPES = [
    # (name, width·h, height·h, cusps, kind)
    ("central", 0.040, 0.052, 2, "incisor"),
    ("lateral", 0.032, 0.044, 2, "incisor"),
    ("canine", 0.031, 0.056, 1, "canine"),
    ("pm1", 0.033, 0.036, 2, "premolar"),
    ("pm2", 0.033, 0.034, 2, "premolar"),
    ("m1", 0.044, 0.030, 4, "molar"),
    ("m2", 0.040, 0.027, 4, "molar"),
]


def build_teeth(into: MeshBuilder, spec, anat, mouth_open: float = 0.0) -> dict:
    h = anat.h
    lm = anat.landmarks
    mouth = Vector(lm["mouth"])
    half_w = 0.5 * (Vector(lm["mouth_corner.L"]).x - Vector(lm["mouth_corner.R"]).x)
    depth = 0.030 * h
    counts = {"crown": 0}

    for sign, z_off in ((1.0, 0.011 * h), (-1.0, -0.010 * h)):
        arch = dental_arch(anat, half_w, depth)
        gum_r = 0.0080 * h
        # gum = semicircular tube swept along the arch
        gum = []
        for k in range(14):
            u = mix(-1, 1, k / 13)
            x, yd = arch(u)
            cy = mouth.y - yd
            cz = mouth.z + sign * z_off
            c = Vector((x, cy, cz))
            ring = []
            for j in range(7):
                a0 = math.pi * (0.05 + 0.90 * j / 6)
                ring.append(c + Vector((math.cos(a0) * gum_r * 1.06,
                                        -math.sin(a0) * gum_r * 0.85 * 1.0,
                                        sign * (math.sin(a0) * gum_r * 1.25 + gum_r * 0.15))))
            gum.append(ring)
        gumres = into.loft(gum, close=False, region="gum", material="gum",
                           uv_rect=(0.0, 1.0, 0.0, 1.0))
        # individual crowns
        for ti, (tname, tw, thh, cusps, kind) in enumerate(TOOTH_TYPES):
            for side in (1, -1):
                u = mix(0.06, 0.98, ti / max(1, len(TOOTH_TYPES) - 1)) * side
                x, yd = arch(u)
                c = Vector((x, mouth.y - yd, mouth.z + sign * (z_off + sign * 0.0 + 0.0035 * h * (1 if sign > 0 else -1))))
                # outward direction (away from cavity centre); crowns angle out
                outw = Vector((x / max(1e-6, half_w) * 0.55, 1.0, 0.0)).normalized()
                w = tw * h * 0.5
                d = w * 0.82
                rings = []
                for rk in range(3):
                    t = rk / 2.0
                    rr = 1.0 - 0.16 * t
                    sec = make_section(c + outw * (0.010 * h * t) + Vector((0, 0, sign * thh * h * (0.5 - t * 1.0))),
                                       tangent=(1, 0, 0), front=tuple(outw),
                                       width=w * rr, depth=d * rr,
                                       superellipse=2.2 + (0.6 if kind == "incisor" else 0.0))
                    pts = sec.points(8)
                    if cusps and rk == 2:
                        pts2 = []
                        for pi, p in enumerate(pts):
                            ang = 2 * math.pi * pi / 8
                            bump = 0.0028 * h * (1.6 if kind in ("molar", "premolar") else 0.7)
                            pts2.append(p + outw * (math.cos(ang * cusps) * bump * 0.4) +
                                        Vector((0, 0, sign * abs(math.sin(ang * 0.5 + math.pi * 0.25)) * bump * (1 if kind in ("canine",) else 0.5))))
                        pts = pts2
                    rings.append(pts)
                into.loft(rings, close=True, region="enamel", material="enamel",
                          uv_rect=(0.3, 0.7, 0.0, 0.55), cap_end="pole")
                counts["crown"] += 1
    return counts


def build_oral_cavity(into: MeshBuilder, spec, anat) -> None:
    """Pouch behind the lips: palate, floor, pharynx cap."""
    h = anat.h
    lm = anat.landmarks
    mouth = Vector(lm["mouth"])
    half_w = 0.5 * (Vector(lm["mouth_corner.L"]).x - Vector(lm["mouth_corner.R"]).x)
    rings = []
    for k in range(5):
        t = k / 4.0
        y = mouth.y - 0.006 * h - t * 0.085 * h
        w = mix(half_w * 0.95, half_w * 0.55, smooth01(t, 0.1, 1.0))
        up = mix(0.030 * h, 0.042 * h, t)
        dn = -mix(0.010 * h, 0.030 * h, t)
        ring = []
        for j in range(10):
            ang = 2 * math.pi * j / 10
            cu, sv = math.cos(ang), math.sin(ang)
            zc = mouth.z + (up if sv > 0 else dn) * 0.5
            rad = w * (1.0 + 0.0) if abs(cu) > abs(sv) else w * 0.72
            z = zc + sv * (up * 0.55 if sv > 0 else -dn * 0.55) * 1.6
            ring.append(Vector((mouth.x + cu * rad, y + sv * 0.004 * h * 0.0, z)))
        rings.append(ring)
    into.loft(rings, close=True, region="oral", material="oral_mucosa",
              uv_rect=(0.0, 1.0, 0.0, 1.0), cap_start="none", cap_end="pole")


def build_tongue(into: MeshBuilder, spec, anat, mouth_open: float = 0.0) -> None:
    h = anat.h
    lm = anat.landmarks
    mouth = Vector(lm["mouth"])
    half_w = 0.052 * h
    rows = []
    for k in range(6):
        t = k / 5.0
        y = mix(mouth.y - 0.078 * h, mouth.y - 0.006 * h, t) + 0.0
        z = mouth.z - 0.014 * h + 0.004 * h * math.sin(math.pi * t) + mouth_open * 0.006 * h * t
        w = mix(0.62, 1.0, math.sin(math.pi * min(1.0, t * 1.12) * 0.92)) * half_w
        th = 0.016 * h * (1.0 - 0.45 * t)
        ring = []
        for j in range(8):
            ang = 2 * math.pi * j / 8
            cu, sv = math.cos(ang), math.sin(ang)
            ring.append(Vector((mouth.x + cu * w, y + sv * th * 1.15,
                                z + sv * th * 0.5 + abs(cu) * 0.0)))
        rows.append(ring)
    res = into.loft(rows, close=True, region="oral", material="tongue",
                    uv_rect=(0.0, 1.0, 0.0, 1.0), cap_start="pole", cap_end="pole")
    # central groove
    for ring in res["rings"]:
        i0 = ring[len(ring) // 2]
        i1 = ring[0]
        into.crease(i0, ring[1], 0.0)
    mid_crease = [i for ring in res["rings"] for i in (ring[0], ring[-1])]


def build_mouth(into: MeshBuilder, spec, anat, mouth_open: float = 0.0) -> dict:
    build_oral_cavity(into, spec, anat)
    counts = build_teeth(into, spec, anat, mouth_open)
    build_lips(into, spec, anat, mouth_open)
    build_tongue(into, spec, anat, mouth_open)
    return counts
