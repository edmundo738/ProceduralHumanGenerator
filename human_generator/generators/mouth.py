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
    """Closed curve (x,z offsets) around the mouth centre.

    ``open_amt=0`` → a narrow sealed slit (lips touching); opening grows the
    lower half downward (mandible hinge) far more than the upper.
    """
    h = anat.h
    f = anat.spec.face
    up_amp = (0.030 + 0.075 * open_amt) * half_w + 0.0035 * h * f.lip_fullness
    dn_amp = (0.034 + 0.30 * open_amt) * half_w + 0.0045 * h * f.lip_fullness
    bow = 0.018 * h * f.cupid_bow

    def curve(t: float):
        a = 2.0 * math.pi * t
        x = math.cos(a) * half_w
        s = math.sin(a)
        if s >= 0.0:
            z = s * up_amp * (1.0 + 0.10 * open_amt)
            z += bow * math.exp(-((abs(x) / max(1e-6, half_w * 0.16)) ** 2)) - 0.42 * bow
        else:
            z = s * dn_amp
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
    protr = 0.0195 * h * f.lip_fullness           # vermilion forward reach
    rows: list[list[Vector]] = []
    for k in range(N_T + 1):
        t = k / N_T                                # 0 = wet-line rim, 1 = skin border
        row = []
        for a in range(N_A):
            x, z = curve(a / N_A)
            surf_y = anat.skull_front_y(mouth.x + x, mouth.z + z)
            # lips ride IN FRONT of the raw skull line: the head stack has
            # already lifted the skin a few mm there, so the vermilion must
            # clear it (+6..9 mm at the bulge), while the wet line stays 2 mm
            # under the surface. A closed mouth is a sealed crease, never a
            # tunnel (v1: -20 mm deep hole), never a floating ring either.
            y = mix(surf_y - 0.0020 * h, surf_y + 0.0062 * h, smooth01(t, 0.08, 0.9))
            band = math.sin(math.pi * t) ** 1.25
            lower = 1.0 if z < 0 else 0.74
            row.append(Vector((mouth.x + x, y + band * protr * lower, mouth.z + z)))
        rows.append(row)
    created = into.loft(rows, close=True, region="lip", material="lip",
                        uv_rect=(0.0, 1.0, 0.0, 1.0), register="lips")
    into.crease_ring(created["rings"][0], 0.55)    # wet line holds under subdivision


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

    for sign, z_off in ((1.0, 0.0105 * h), (-1.0, -0.0095 * h)):
        arch = dental_arch(anat, half_w, depth)
        gum_r = 0.0080 * h
        # gum = semicircular tube swept along the arch
        gum = []
        for k in range(14):
            u = mix(-1, 1, k / 13)
            x, yd = arch(u)
            cz = mouth.z + sign * z_off
            cy = min(mouth.y - yd, anat.skull_front_y(x, cz) - 0.016 * h)
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
        # individual crowns — hang from the gum line along ±z, the crown
        # axis leans slightly forward (incisor bevel); width runs along the
        # arch tangent.  (v1 grew crowns along +y, which poked them out of
        # the closed lips — the floating-grill render bug.)
        crowns: list[range] = []
        for ti, (tname, tw, thh, cusps, kind) in enumerate(TOOTH_TYPES):
            for side in (1, -1):
                crown_start = into.n_verts
                u = mix(0.06, 0.98, ti / (len(TOOTH_TYPES) - 1)) * side
                x, yd = arch(u)
                lean = Vector((0.0, 0.30, -sign * 1.0)).normalized()
                bz = mouth.z + sign * (z_off + 0.052 * h * 0.42)
                # arch depth follows the skull: corners recede, teeth must too
                ty_cap = anat.skull_front_y(x, bz) - 0.026 * h
                base = Vector((x, min(mouth.y - yd + 0.0016 * h, ty_cap), bz))
                w = tw * h * 0.5
                d = w * 0.72
                rings = []
                for rk in range(4):
                    t = rk / 3.0
                    rr = 1.0 - 0.18 * t * t
                    cen = base + lean * (thh * h * t)
                    if rk == 3:                       # occlusal: flatten, taper
                        rr *= 0.92
                    sec = make_section(cen, tangent=(1, 0, 0), front=(0, 1, 0),
                                       width=w * rr, depth=d * rr,
                                       superellipse=2.0 + (0.8 if kind == "incisor" else 0.0)
                                       + (0.6 if rk == 3 else 0.0))
                    pts = [Vector(q) for q in sec.points(8)]
                    if kind == "canine" and rk == 3:  # cusp point
                        # S3.1 — a modulação tem de escolher a metade do anel pelo
                        # lado MUNDIAL do dente, não só pelo índice do anel:
                        # ``max(0, cos(2*pi*pi/8))`` não é equivariante sob reflexão
                        # e quebrava o espelho exactamente dos 4 caninos (200 de
                        # 1400 vértices de esmalte, medido).  O dente do lado +x
                        # mantém a geometria bit a bit; o de −x passa a ser o seu
                        # espelho.
                        outward = 1.0 if x >= 0.0 else -1.0
                        pts = [q - Vector((0, 0, sign * 0.0035 * h *
                                           max(0.0, outward * math.cos(2 * math.pi * pi / 8))))
                               for pi, q in enumerate(pts)]
                    if kind in ("molar", "premolar") and rk == 3:
                        pts = [q + Vector((0, 0, sign * 0.0022 * h *
                                           math.cos(2 * math.pi * cusps * pi / 8)))
                               for pi, q in enumerate(pts)]
                    rings.append(pts)
                into.loft(rings, close=True, region="enamel", material="enamel",
                          uv_rect=(0.3, 0.7, 0.0, 0.55),
                          cap_start="pole", cap_end="pole")
                crowns.append(range(crown_start, into.n_verts))
        counts["crowns_rigid"] = _clamp_rigid_groups(into, anat, crowns, 0.0090)
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


def _clamp_rigid_groups(builder, anat, groups, margin: float) -> int:
    """Pull *rigid* groups (one tooth crown each) behind the skull line.

    A per-vertex clamp is the pure function ``y := skull_front_y(x, z) - margin``,
    so any two vertices of the same crown that share (x, z) — measured: occlusal
    cusp vertices and the cap cone, which sit at the ring's own centre line —
    collapse onto the same point (0 -> 32 coincident pairs, all intra-tooth,
    pre-clamp |dy| up to 2.9 mm; docs/RESEARCH_GATE_02.md).  Teeth are rigid
    bodies, so translating the whole crown is both physically right and
    provably coincidence-free: intra-crown distances are preserved, and
    containment still holds because every vertex moves by the group maximum.
    Returns the number of groups moved.
    """
    h = anat.h
    margin *= h
    moved = 0
    for ids in groups:
        need = 0.0
        for i in ids:
            p = builder.verts[i]
            need = max(need, p.y - (anat.skull_front_y(p.x, p.z) - margin))
        if need <= 0.0:
            continue
        for i in ids:
            v = builder.verts[i]
            builder.verts[i] = Vector((v.x, v.y - need, v.z))
        moved += 1
    return moved


def _clamp_behind(builder, anat, regions, margin: float) -> None:
    """Per-vertex pull-back: interior parts may never exceed the skull line.

    Clamping the *bases* is not enough — crown rings have width and lean, and
    the skull surface recedes fast toward the arch corners, so each vertex is
    checked against the surface at its own (x, z).  Bonus: the front row of
    incisors ends up curved along the arch for free.
    """
    h = anat.h
    for i, p in enumerate(builder.verts):
        if builder.regions[i] in regions:
            lim = anat.skull_front_y(p.x, p.z) - margin * h
            if p.y > lim:
                builder.verts[i] = Vector((p.x, lim, p.z))


def build_mouth(into: MeshBuilder, spec, anat, mouth_open: float = 0.0) -> dict:
    build_oral_cavity(into, spec, anat)
    counts = build_teeth(into, spec, anat, mouth_open)
    build_tongue(into, spec, anat, mouth_open)
    build_lips(into, spec, anat, mouth_open)
    # "enamel" is absent on purpose: crowns were already pulled back rigidly,
    # per tooth, inside build_teeth (a per-vertex clamp here would re-collapse
    # vertices that share (x, z)).
    if mouth_open < 0.02:
        _clamp_behind(into, anat, ("gum", "oral"), 0.0090)
        _clamp_behind(into, anat, ("tongue",), 0.0075)
    else:                       # open mouth: teeth may pass the lip line
        _clamp_behind(into, anat, ("gum", "oral"), 0.0090)
        _clamp_behind(into, anat, ("tongue",), 0.0040)
    return counts
