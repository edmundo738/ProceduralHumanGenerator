# -*- coding: utf-8 -*-
"""Procedural hair: scalp follicles → curve strands (curl, clump, part,
style), lashes from the lid margin polyline, brows from the brow region,
and an optional bun for up-dos (real lofted geometry, not a particle fuzz).

Strand synthesis is pure-python so it can be unit-tested without bpy;
``curves_to_object`` binds them into a bpy Curves datablock with per-point
radius taper (root 1.0 → tip 0.15).
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

from ..core._math import Vector, clamp, mix, smoothstep
from ..core.rng import Rng
from ..core.topology import MeshBuilder


@dataclass
class HairResult:
    strands: list = field(default_factory=list)      # list[list[Vector]]
    lashes: list = field(default_factory=list)
    brows: list = field(default_factory=list)
    bun: MeshBuilder | None = None
    notes: dict = field(default_factory=dict)


_STYLES = {
    "loose": dict(tilt_back=0.30, tilt_down=0.90, amp=1.00, side=0.35, length=1.00, front=0.62),
    "sleek": dict(tilt_back=0.72, tilt_down=0.42, amp=0.35, side=0.10, length=0.88, front=0.30),
    "updo":  dict(tilt_back=0.55, tilt_down=0.15, amp=0.60, side=0.15, length=0.46, front=0.40),
    "short": dict(tilt_back=0.25, tilt_down=0.75, amp=0.80, side=0.30, length=0.16, front=0.16),
    "curly": dict(tilt_back=0.20, tilt_down=0.95, amp=1.90, side=0.55, length=0.92, front=0.70),
}


def _style_defaults(style: str) -> dict:
    return dict(_STYLES.get(style, _STYLES["loose"]))


# ----------------------------------------------------------------------------- roots
def scalp_roots(head_verts, head_regions, head_centre, head_radii, n_target: int,
                part_x: float, rng: Rng, n_per: list | None = None):
    """Distribute strand roots over scalp-tagged vertices.

    Each scalp vert spawns a small poisson-ish cluster; roots near the part
    line fade out (a visible part emerges from absence, not from geometry).
    """
    rx, ry, rz = head_radii
    pts = []
    scalp_idx = [i for i, r in enumerate(head_regions) if r == "scalp"]
    if not scalp_idx:
        return pts
    k = max(1, int(math.ceil(n_target / len(scalp_idx))))
    for i in scalp_idx:
        p = Vector(head_verts[i])
        n = Vector(((p.x - head_centre.x) / rx ** 2,
                    (p.y - head_centre.y) / ry ** 2,
                    (p.z - head_centre.z) / rz ** 2)).normalized()
        t1 = n.orthogonal().normalized()
        t2 = n.cross(t1).normalized()
        # cell size: mean spacing of scalp verts
        cell = 0.0125 * rx * 2.0
        for j in range(k):
            a = rng.uniform(-1, 1) * cell
            b = rng.uniform(-1, 1) * cell
            q = p + t1 * a + t2 * b
            # project back onto the ellipsoid (± 0.5 mm)
            d = Vector(((q.x - head_centre.x) / rx, (q.y - head_centre.y) / ry,
                        (q.z - head_centre.z) / rz)).length
            if d > 1e-9:
                q = head_centre + (q - head_centre) / d
            nn = Vector(((q.x - head_centre.x) / rx ** 2,
                         (q.y - head_centre.y) / ry ** 2,
                         (q.z - head_centre.z) / rz ** 2)).normalized()
            q = q + nn * 0.0004
            # parting fade (only above the trichion on top)
            if q.z > head_centre.z - 0.02 * ry and abs(q.y) < 0.75 * ry:
                w = smoothstep(0.0, 0.0085, abs(q.x - part_x))
                if rng.uniform(0, 1) > w * w:
                    continue
            # nape taper: keep the hairline at the neck clean
            if q.y < head_centre.y - 0.55 * ry and q.z < head_centre.z + 0.10 * rz:
                if rng.uniform(0, 1) > smoothstep(head_centre.z - 0.28 * rz,
                                                  head_centre.z - 0.02 * rz, q.z):
                    continue
            pts.append((q, nn))
            if len(pts) >= n_target:
                return pts
    return pts


# ----------------------------------------------------------------------------- strands
def _grow(root: Vector, nrm: Vector, d0: Vector, length: float, amp: float,
          freq: float, phase: float, frizz: float, rng: Rng, steps: int,
          attract: Vector | None = None) -> list[Vector]:
    """Integrate one strand: fall + travelling curl wave (+ bun attraction)."""
    u = d0.cross(nrm)
    if u.length < 1e-7:
        u = nrm.orthogonal()
    u = u.normalized()
    v = d0.cross(u).normalized()
    pts = [root - nrm * 0.0012]                     # anchor under the scalp
    p = Vector(root)
    d = Vector(d0)
    ds = length / steps
    for i in range(1, steps + 1):
        t = i / steps
        if attract is not None:
            pull = attract - p
            dd = pull.normalized()
            d = (d * (1.0 - 0.30 * t) + dd * (0.30 * t)).normalized()
            d = d + nrm * max(0.0, 0.18 - 0.30 * t)
            d = d.normalized()
        wob = amp * math.sin(2.0 * math.pi * freq * t * 3.0 + phase)
        dirv = (d + u * (wob * 0.55) + v * (wob * 0.42))
        if frizz > 0.0:
            dirv = dirv + Vector((rng.uniform(-1, 1), rng.uniform(-1, 1),
                                  rng.uniform(-1, 1))) * (frizz * 0.16)
        dirv = dirv.normalized()
        p = p + dirv * ds
        d = dirv
        pts.append(Vector(p))
    return pts


def build_hair(spec, anat, head_builder, eye_info: dict | None = None) -> HairResult:
    """Full coiffure: scalp strands + lashes + brows (+ bun for updo)."""
    hp = spec.hair
    h = anat.h
    rng = Rng(spec.seed, salt=404)
    c = anat.head_center()
    rx, ry, rz = anat.head_radii()
    st = _style_defaults(hp.style)

    part_x = hp.part_offset * 0.030 * h + rng.uniform(-0.002, 0.002) * h * spec.face.asymmetry
    n_target = int(hp.strand_count)
    roots = scalp_roots(head_builder.verts, head_builder.regions, c,
                        (rx, ry, rz), n_target, part_x, rng)

    # clumping: strands in a spatial cell share curl phase + lean
    cell = 0.030 * h
    clump_phase: dict = {}
    frizz = hp.frizz * 0.9
    curl = hp.curl
    L0 = hp.hair_length

    front = c.y + 0.30 * ry
    strands = []
    for (p, n) in roots:
        key = (int((p.x) / cell), int((p.y) / cell), int((p.z) / cell))
        ph = clump_phase.get(key)
        if ph is None:
            ph = (rng.uniform(0, 2 * math.pi), Vector((rng.uniform(-1, 1),
                    rng.uniform(-0.2, 0.2), rng.uniform(-1, 1))).normalized() * st["side"] * 0.4)
            clump_phase[key] = ph
        phase, lean = ph
        # length profile: short at the hairline arc, longest at the crown
        f = smoothstep(c.z - 0.30 * h, c.z + 0.35 * h, p.z)
        fr = 1.0 if p.y < front else st["front"]        # fringe shorter
        prof = mix(0.62, 1.10, f) * fr * st["length"]
        L = L0 * prof * (0.85 + 0.30 * rng.uniform(0, 1))
        # initial direction: gravity ∘ back-sweep ∘ normal
        down = Vector((0, 0, -1))
        back = Vector((0, -1, 0))
        d0 = (down * st["tilt_down"] + back * st["tilt_back"] + n * 0.55 + lean)
        if p.y > c.y + 0.2 * ry:                          # fringe falls forward
            d0 = (down * 0.8 + Vector((0, 0.55, 0.15)) + n * 0.25 + lean)
        d0 = d0.normalized()
        amp = curl * 1.15 * st["amp"] * (0.7 + 0.6 * rng.uniform(0, 1))
        freq = mix(0.7, 1.7, curl) * (0.8 + 0.45 * rng.uniform(0, 1))
        attract = None
        if hp.style == "updo" and p.z > c.z - 0.15 * h:
            attract = c + Vector((0, -0.62 * ry, 0.30 * rz))
        segs = 16 if L > 0.10 else 8
        strands.append(_grow(p, n, d0, L, amp, freq, phase, frizz, rng, segs, attract))

    res = HairResult(strands=strands)

    # ---- bun (updo): torus loft on the crown-back ---------------------------------
    if hp.style == "updo":
        b = MeshBuilder("bun")
        bc = c + Vector((0, -0.60 * ry, 0.34 * rz))
        r_path, r_tube = 0.115 * h, 0.052 * h
        rings = []
        pathn = Vector((0, 0.28, 0.96)).normalized()
        t1 = pathn.orthogonal().normalized()
        t2 = pathn.cross(t1).normalized()
        for k in range(14):
            a = 2 * math.pi * k / 14
            centre = bc + t1 * (math.cos(a) * r_path) + t2 * (math.sin(a) * r_path)
            fr = (t1 * (-math.sin(a)) + t2 * math.cos(a)).normalized()
            ring = []
            for j in range(10):
                aa = 2 * math.pi * j / 10
                wob = 1.0 + 0.30 * math.sin(aa * 3.0 + a * 2.0)   # wound-strand look
                ring.append(centre + fr * (math.cos(aa) * r_tube * wob)
                            + pathn * (math.sin(aa) * r_tube * wob * 0.8))
            rings.append(ring)
        b.loft(rings, close=True, region="hair", material="hair",
               uv_rect=(0.0, 1.0, 0.0, 1.0), cap_start="none", cap_end="none")
        b.mirror_merge("X")
        res.bun = b

    # ---- lashes from the lid margin polylines -------------------------------------
    if eye_info:
        for tag in ("L", "R"):
            info = eye_info.get(tag)
            if not info:
                continue
            ce, axx, upv, rt = info["centre"], info["axis"], info["up"], info["r"]
            for which, cnt, lf, upw in (("upper", 2, 1.0, 1.0), ("lower", 1, 0.55, -0.45)):
                pts = info[f"margin_{which}"]
                for mp in pts:
                    for j in range(cnt):
                        outw = (Vector(mp) - ce).normalized()
                        d0 = (outw * 0.55 + upv * (0.85 * upw) + Vector((0, 0, 0.12))).normalized()
                        L = 0.055 * rt * lf * (0.75 + 0.5 * rng.uniform(0, 1))
                        ph = rng.uniform(0, 6.28)
                        s = _grow(Vector(mp), outw, d0, L, 0.55, 0.6, ph, 0.0, rng, 6)
                        # upper lashes curl outward with a fixed handedness per side
                        res.lashes.append(s)
    # ---- brows: an arched line per side, hairs swept toward the tail ---------------
    zb = anat.z("brow") if "brow" in getattr(anat, "_Z", {}) else c.z + 0.128 * h
    zb = c.z + 0.128 * h
    for side in (1.0, -1.0):
        for i in range(46):
            t = i / 45.0 + rng.uniform(-0.012, 0.012)
            x = side * mix(0.030 * h, 0.255 * h, t) * (1.0 + rng.uniform(-0.08, 0.08))
            z = zb + 0.014 * h * math.sin(math.pi * clamp(t * 0.94 + 0.03, 0, 1)) \
                - 0.006 * h + rng.uniform(-0.0018, 0.0018) * h
            y = anat.skull_front_y(x, z) + 0.0012 * h
            n = Vector(((x - c.x) / rx ** 2, (y - c.y) / ry ** 2,
                        (z - c.z) / rz ** 2)).normalized()
            tail = Vector((side * 0.8, 0.28, -0.22 + 0.5 * t))
            d0 = (tail + n * 0.55 + Vector((rng.uniform(-0.18, 0.18), 0,
                                            rng.uniform(-0.14, 0.30)))).normalized()
            L = 0.0135 * h * (0.55 + 0.75 * (1.0 - abs(t - 0.35)) * 1.4)
            res.brows.append(_grow(Vector((x, y, z)), n, d0, max(0.004, L),
                                   0.22, 0.5, rng.uniform(0, 6.28), 0.0, rng, 5))
    res.notes["roots"] = len(strands)
    res.notes["part_x"] = part_x
    return res


# ----------------------------------------------------------------------------- bpy binding
def curves_to_object(res: HairResult, name: str = "hcg:hair", thickness: float = 1.0):
    """Bake strand polylines into one Curves object with tapered bevels."""
    import bpy
    cu = bpy.data.curves.new(name, "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth = 0.0000425 * max(0.35, thickness)   # ~68 µm real strand
    cu.bevel_resolution = 1
    cu.use_fill_caps = True
    for group, taper in ((res.strands, 1.0), (res.lashes, 1.35), (res.brows, 1.6)):
        for strand in group:
            sp = cu.splines.new("POLY")
            n = len(strand)
            sp.points.add(n - 1)
            for k, p in enumerate(strand):
                t = k / max(1, n - 1)
                sp.points[k].co = (p.x, p.y, p.z, 1.0)
                sp.points[k].radius = mix(1.0, 0.14, smoothstep(0.25, 1.0, t)) * taper
    ob = bpy.data.objects.new(name, cu)
    return ob
