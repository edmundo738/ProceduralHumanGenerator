# -*- coding: utf-8 -*-
"""Skull + face.

The head starts as a *cube-sphere cage* (six grids projected onto the skull
ellipsoid) — the classic box-modelling base: all quads, three clean poles per
octant, no valence disasters.  Then:

1. sagittal shaping — the anterior-inferior shell is pulled onto
   ``Anatomy.skull_front_y`` (the cranial + midface blend), giving a real
   facial profile instead of an egg;
2. feature rings — faces around eyes/mouth/nose get inset once or twice,
   producing the holding loops that keep apertures crisp under Catmull-Clark;
3. anatomy fields — brow, glabella, malar, mental, nasolabial, philtrum,
   sockets… composed into one DeformStack so everything welds smoothly;
4. ears — a surface-following helix disc + concha socket, merged in;
5. scalp / eyelid / lip / nostril vertex groups for the skin shader masks and
   for the hair scatter.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

from ..core._math import Vector, clamp, mix, smoothstep
from ..core.field import DeformStack, falloff
from ..core.topology import MeshBuilder, make_section
from ..core.rng import Rng


@dataclass
class HeadResult:
    builder: MeshBuilder
    rings: dict = field(default_factory=dict)
    regions: dict = field(default_factory=dict)


# ----------------------------------------------------------------------------- cube sphere
def box_sphere(builder: MeshBuilder, *, center, radii, n: int = 7,
               squash_top: float = 0.06, temple_pull: float = 0.06) -> dict:
    """Closed cube-sphere grid projected onto an ellipsoid (shared edge verts)."""
    rx, ry, rz = radii
    c = Vector(center)
    pos: dict[tuple[int, int, int], Vector] = {}
    axis_dirs = [(1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)]
    for ai, (ax, ay, az) in enumerate(axis_dirs):
        A = Vector((ax, ay, az))
        U = Vector((ay, az, ax))          # any perpendicular pair
        if abs(A.dot(U)) > 0.5:
            U = Vector((az, ax, ay))
        T = A.cross(U).normalized()
        U = T.cross(A).normalized()
        for i in range(n + 1):
            for j in range(n + 1):
                uu = -1.0 + 2.0 * i / n
                vv = -1.0 + 2.0 * j / n
                p = (A + T * uu + U * vv)
                p = p.normalized() if p.length > 1e-9 else A
                key = _qkey(p)
                if key not in pos:
                    pos[key] = p
    # project each cube-surface direction onto the ellipsoid
    verts: dict[tuple, int] = {}
    ids: dict[tuple, int] = {}
    for key, p in pos.items():
        dx, dy, dz = p.x, p.y, p.z
        t = 1.0 / math.sqrt((dx / 1.0) ** 2 + (dy / 1.0) ** 2 + (dz / 1.0) ** 2)
        # ellipsoid intersection of the ray c + s*(dx,dy,dz)
        sx, sy, sz = dx / rx, dy / ry, dz / rz
        s = 1.0 / math.sqrt(sx * sx + sy * sy + sz * sz) if (sx or sy or sz) else rx
        q = c + Vector((dx * s, dy * s, dz * s))
        # temple/jaw taper: narrow the lower half, slight vertical squash
        lower = smoothstep(c.z + 0.05 * ry, c.z - 0.55 * rz, q.z)
        q.x *= mix(1.0, 1.0 - 0.20 - temple_pull, lower)
        q.y += (ry - abs(q.y - c.y)) * 0.0
        if q.z > c.z + 0.62 * rz:  # crown flattening (vertex squash)
            q.z -= squash_top * rz * smoothstep(c.z + 0.62 * rz, c.z + rz, q.z)
        ids[key] = builder.add_vert(q, "skin", (0.5, 0.5))
    # S3.7 — o crânio não registava anéis: o instrumento não tinha como
    # identificar a casca da cabeça sem heurísticas (posição/tamanho).  As
    # latitudes (mesmo z, arredondado) passam a ser anéis nomeados
    # ``skull.<k>`` (o merge do corpo prefixa-os para ``head.skull.<k>``), de cima para baixo.
    bands: dict[float, list[int]] = {}
    for key, vi in ids.items():
        bands.setdefault(round(builder.verts[vi].z, 6), []).append(vi)
    for k, (zq, band) in enumerate(sorted(bands.items(), reverse=True)):
        builder.rings[f"skull.{k}"] = sorted(band)

    # faces: for every grid cell of every axis face
    def face_key(ai, i, j):
        ax, ay, az = axis_dirs[ai]
        A = Vector((ax, ay, az))
        U = Vector((ay, az, ax))
        if abs(A.dot(U)) > 0.5:
            U = Vector((az, ax, ay))
        T = A.cross(U).normalized()
        U = T.cross(A).normalized()
        uu = -1.0 + 2.0 * i / n
        vv = -1.0 + 2.0 * j / n
        p = (A + T * uu + U * vv).normalized()
        return _qkey(p)

    for ai in range(6):
        for i in range(n):
            for j in range(n):
                a = ids.get(face_key(ai, i, j))
                b = ids.get(face_key(ai, i + 1, j))
                cc = ids.get(face_key(ai, i + 1, j + 1))
                d = ids.get(face_key(ai, i, j + 1))
                if None in (a, b, cc, d):
                    continue
                # outward orientation
                builder.add_face((a, b, cc, d), material="skin")
    before = len(builder.faces)
    # Drop collapsed faces AND their material entries together: filtering only
    # ``faces`` desynchronised ``face_mat`` (it stayed longer), which silently
    # shifted the material of every later face in the builder (measured below).
    kept = [(f, m) for f, m in zip(builder.faces, builder.face_mat)
            if len(set(f)) == len(f)]
    builder.faces = [f for f, _ in kept]
    builder.face_mat = [m for _, m in kept]
    return {"n": len(ids), "keys": len(pos), "faces": len(builder.faces),
            "faces_dropped": before - len(builder.faces)}


def _qkey(p: Vector) -> tuple[int, int, int]:
    return (round(p.x * 1e5), round(p.y * 1e5), round(p.z * 1e5))


# ----------------------------------------------------------------------------- feature loops
def add_feature_loops(builder: MeshBuilder, targets: list[tuple[Vector, float, int]],
                      shrink: float = 0.34) -> None:
    """Inset faces near landmark targets (recursively) = holding loops.

    Works directly on the builder (pure python, deterministic): each selected
    quad gets replaced by a centre-shrunk quad plus a 4-quad collar; collars
    are creased so subdivision keeps aperture rims from melting.
    """
    targets = [(Vector(p), r, it) for p, r, it in targets]
    for _ in range(max(it for _, _, it in targets) if targets else 1):
        new_faces = []
        new_mats = []
        changed = 0
        for fi, f in enumerate(builder.faces):
            if len(f) != 4:
                new_faces.append(f)
                new_mats.append(builder.face_mat[fi])
                continue
            ctr = builder.face_centre(fi)
            near = any((ctr - p).length < r for p, r, _ in targets)
            if not near:
                new_faces.append(f)
                new_mats.append(builder.face_mat[fi])
                continue
            mat = builder.face_mat[fi]
            a, b, c, d = f
            pa, pb, pc, pd = (builder.verts[i] for i in (a, b, c, d))
            cen = (pa + pb + pc + pd) / 4
            inner = [builder.add_vert(p + (cen - p) * shrink, builder.regions[v], builder.uvs[v])
                     for p, v in ((pa, a), (pb, b), (pc, c), (pd, d))]
            ia, ib, ic, idd = inner
            new_faces += [(a, b, ib, ia), (b, c, ic, ib), (c, d, idd, ic), (d, a, ia, idd)]
            new_mats += [mat] * 4
            # inner quad handled next pass
            new_faces.append((ia, ib, ic, idd))
            new_mats.append(mat)
            changed += 1
            for pair in ((a, ia), (b, ib), (c, ic), (d, idd)):
                builder.crease(pair[0], pair[1], 0.22)
        builder.faces = new_faces
        builder.face_mat = new_mats
    return changed


# ----------------------------------------------------------------------------- ears
def add_ear(builder: MeshBuilder, anat, side: int, rng: Rng) -> None:
    """Auricle: an ellipsoid-conforming 6×8 patch (so it hugs the skull at
    every proportion), rim creased, concha hollowed by the head field stack."""
    h = anat.h
    c = Vector(anat.landmarks["ear.L" if side > 0 else "ear.R"])
    c0 = anat.head_center()
    rx, ry, rz = anat.head_radii()
    cx = 1.0 if side > 0 else -1.0
    rows, cols = 6, 8
    ear_h = 0.29 * h * anat.spec.face.ear_size
    grid = []
    for ri in range(rows):
        v = ri / (rows - 1)
        row = []
        for ci in range(cols):
            u = -1.0 + 2.0 * ci / (cols - 1)
            z = c.z + (0.5 - v) * ear_h
            y = c.y + u * ear_h * 0.34
            ty = (y - c0.y) / ry
            tz = (z - c0.z) / rz
            s = 1.0 - ty * ty - tz * tz
            s = max(0.04, s)
            x = cx * rx * math.sqrt(s) * 1.006
            # helix rim lifts off the skull toward the middle, rim crest at u≈±0.8
            rim = math.exp(-((abs(u) - 0.78) ** 2) / 0.10) * math.exp(-((v - 0.55) ** 2) / 0.30)
            x += cx * (0.0060 * h + 0.0046 * h * rim)
            # lobe droop: bottom rows relax inward-forward
            if v > 0.82:
                x -= cx * 0.0022 * h * (v - 0.82) / 0.18
            row.append(builder.add_vert(Vector((x, y, z)), "skin", (ci / (cols - 1), v)))
        grid.append(row)
    for ri in range(rows - 1):
        for ci in range(cols - 1):
            a, b = grid[ri][ci], grid[ri][ci + 1]
            cc, d = grid[ri + 1][ci], grid[ri + 1][ci + 1]
            if side > 0:
                builder.add_face((a, b, cc, d), material="skin")
            else:
                builder.add_face((a, d, cc, b), material="skin")
    builder.crease_ring([grid[r][0] for r in range(rows)], 0.30)
    builder.crease_ring([grid[r][-1] for r in range(rows)], 0.30)
    builder.crease_ring(grid[0], 0.26)
    builder.crease_ring(grid[-1], 0.18)


# ----------------------------------------------------------------------------- main
def build_head(spec, anat) -> HeadResult:
    rng = Rng(spec.seed, salt=101)
    b = MeshBuilder("head")
    h = anat.h
    s = spec.stature if hasattr(spec, "stature") else spec.body.stature
    face = spec.face
    c = anat.head_center()
    rx, ry, rz = anat.head_radii()

    # 1) cube-sphere skull
    box_sphere(b, center=c, radii=(rx * 1.015, ry * 1.015, rz * 1.015), n=9,
               squash_top=0.045, temple_pull=0.05)

    # 2) sagittal profile: the anterior shell is set to the *dominant* of the
    #    two skull shells (cranium ∪ midface/mandible block).  This is why
    #    the correction must key off surface comparison, not position: raw
    #    ellipsoid points near the chin have small y exactly where the face
    #    block is largest, and a position-based weight would sink the chin.
    lm = anat.landmarks
    #    The target ``surf = skull_front_y(x, z)`` is a function of the ray
    #    column alone, and ``edge`` depends only on (x, z) too — so blending
    #    each vertex toward it independently made every column that holds two
    #    samples collapse onto a single point wherever the weight reaches 1
    #    (measured: 8 columns -> 16 coincident verts -> 5 zero-area faces in
    #    the builder).  The eligible vertices of a column now translate
    #    rigidly instead: the exposed (front-most) vertex still lands exactly
    #    on ``surf`` — the documented intent — while the column keeps its
    #    internal spacing exactly, because a shared translation cannot change
    #    any distance inside the group.  A column whose front-most vertex is
    #    already at ``surf`` is left alone (the old code used to drag the
    #    vertices behind it onto that same point).
    columns: dict[tuple[float, float], list[int]] = {}
    for i, p in enumerate(b.verts):
        if abs(p.x) < 0.80 * rx and (c.z - 0.72 * h) < p.z < (c.z + 0.56 * h) \
                and p.y > c.y - 0.15 * ry:
            columns.setdefault((round(p.x, 9), round(p.z, 9)), []).append(i)
    for (qx, qz), idxs in columns.items():
        surf = anat.skull_front_y(qx, qz)
        need = surf - max(b.verts[i].y for i in idxs)
        if need <= 0.0002:
            continue
        edge = smoothstep(0.80 * rx, 0.52 * rx, abs(qx)) * \
            smoothstep(c.z - 0.70 * h, c.z - 0.550 * h, qz) * \
            smoothstep(c.z + 0.56 * h, c.z + 0.470 * h, qz)
        shift = need * clamp(edge, 0.0, 1.0)
        if abs(shift) < 1e-12:
            continue
        for i in idxs:
            v = b.verts[i]
            b.verts[i] = Vector((v.x, v.y + shift, v.z))

    # 3) feature loops (holding loops under subdivision)
    lm = anat.landmarks
    targets = [
        (lm["eye.L"], 0.034 * h, 1), (lm["eye.R"], 0.034 * h, 1),
        (lm["mouth"], 0.052 * h, 2), (lm["nose_tip"], 0.048 * h, 1),
        (lm["ear_canal.L"], 0.016 * h, 1), (lm["ear_canal.R"], 0.016 * h, 1),
    ]
    add_feature_loops(b, targets, shrink=0.36)

    # 4) ears (surface patches)
    for side in (1, -1):
        add_ear(b, anat, side, rng)

    # 5) anatomy fields
    stack = DeformStack()
    # brow ridge
    for tag in ("L", "R"):
        stack.bump(lm[f"brow.{tag}"], 0.010 * h * (0.7 + 0.6 * face.brow_thickness),
                   sigma=(0.055 * h, 0.018 * h, 0.020 * h), direction=(0, 1, 0.10))
    stack.bump(lm["glabella"], 0.008 * h, sigma=(0.022 * h, 0.016 * h, 0.016 * h))
    # sockets (shallow)
    for tag in ("L", "R"):
        stack.socket(lm[f"eye.{tag}"], 0.0125 * h * face.eye_depth,
                     radius=0.048 * h)
    # nose — sampled from the cartilage line: skin is lifted onto the
    # root→tip profile (gaussians anchored on the SURFACE, amplitude =
    # landmark-minus-surface, so the field always blends flush at its rim)
    proj = spec.face.nose_tip_projection
    tip_extra = 0.004 * h * proj
    for k, wid in ((0.28, 0.011), (0.52, 0.014), (0.75, 0.016), (1.0, 0.014)):
        q = lm["nose_root"].lerp(lm["nose_tip"], k)
        y0 = anat.skull_front_y(0.0, q.z)
        amp = max(0.0006, q.y - y0) + tip_extra * k * k
        stack.bump(Vector((0.0, y0, q.z)), amp,
                   sigma=((wid + 0.006) * h, 0.5 * h, 0.9 * h * (0.7 + 0.5 * k)),
                   direction=(0, 1, 0.18))
    stack.bump(Vector((0.0, anat.skull_front_y(0.0, lm["nose_tip"].z) - 0.001 * h,
                        lm["nose_tip"].z)), tip_extra + 0.004 * h,
               sigma=(0.016 * h, 0.016 * h, 0.012 * h), direction=(0, 1, -0.30))
    for sx in (1, -1):
        stack.bump(lm["nose_tip"] + Vector((sx * 0.016 * h, -0.006 * h, -0.007 * h)),
                   0.0048 * h * spec.face.nostril_flare,
                   sigma=(0.011 * h, 0.010 * h, 0.009 * h),
                   direction=(sx * 0.45, 0.85, -0.30))
    stack.bump(lm["nose_base"], 0.0040 * h, sigma=(0.020 * h, 0.013 * h, 0.011 * h))
    # cheeks / malar
    for tag in ("L", "R"):
        stack.bump(lm[f"cheek.{tag}"], 0.010 * h * (0.5 + face.cheek_fullness),
                   sigma=(0.050 * h, 0.030 * h, 0.045 * h), direction=(0.25 * (1 if tag == "L" else -1), 0.8, -0.2))
    # chin / jaw
    stack.bump(lm["chin_front"], 0.0090 * h * face.chin_projection,
               sigma=(0.042 * h, 0.024 * h, 0.032 * h), direction=(0, 1, -0.12))
    for tag, sx in (("L", 1), ("R", -1)):
        stack.bump(lm[f"jaw_angle.{tag}"], 0.006 * h,
                   sigma=(0.020 * h, 0.020 * h, 0.030 * h), direction=(sx * 0.4, 0.3, -0.3))
    # lips mound + philtrum groove
    stack.bump(lm["mouth"], 0.0040 * h * face.lip_fullness,
               sigma=(0.055 * h * face.mouth_width, 0.020 * h, 0.026 * h), direction=(0, 1, 0))
    stack.bump(lm["philtrum"], -0.0022 * h * face.philtrum_length,
               sigma=(0.012 * h, 0.016 * h, 0.016 * h), direction=(0, 1, 0))
    # nostril openings + ear conchae
    for sx in (1, -1):
        stack.socket(lm["nose_base"] + Vector((sx * 0.0135 * h, 0.004 * h, -0.010 * h)),
                     0.0045 * h * spec.face.nostril_flare, radius=0.0075 * h)
    for side in (1, -1):
        ec = Vector(anat.landmarks["ear.L" if side > 0 else "ear.R"])
        stack.socket(ec + Vector((-0.010 * h * side * side, 0.006 * h, -0.004 * h)),
                     0.0052 * h, radius=0.020 * h)
        # direction: push skin toward skull (-x·side)
        stack.items[-1].direction = Vector((-side, 0.10, 0.0)).normalized()
        stack.items[-1].sigma = (0.020 * h, 0.020 * h, 0.026 * h)
        stack.items[-1].centre = ec + Vector((-0.002 * h * side, 0.008 * h, -0.006 * h))
    # temple hollow + neck blend
    for tag in ("L", "R"):
        stack.bump(lm[f"temple.{tag}"], -0.0035 * h, sigma=(0.045 * h, 0.030 * h, 0.055 * h))
    stack.bump(Vector((c.x, c.y - 0.10 * h, anat.z("chin") - 0.10 * h)), 0.006 * h,
               sigma=(0.075 * h, 0.05 * h, 0.04 * h), direction=(0, -0.4, -1), mask=None)
    b.verts = stack.apply(b.verts)

    # 6) regions + groups (scalp for hair, masks for shader)
    hairline_z = anat.z("hairline")
    regions = {"scalp": [], "eyelid": [], "brow": [], "lip": [], "nostril": []}
    for i, p in enumerate(b.verts):
        p = Vector(p)
        # scalp: above the hairline arc, behind trichion; excludes forehead
        dz = p.z - hairline_z
        on_top = (dz > -0.012 * h) and ((p - c).z > 0.02 * h or p.y < c.y + 0.15 * ry)
        front_low = p.y > c.y - 0.10 * ry and p.z < hairline_z
        if on_top and not front_low:
            b.regions[i] = "scalp"
            regions["scalp"].append(i)
        for tag in ("L", "R"):
            if (p - lm[f"eye.{tag}"]).length < 0.030 * h and p.y > lm[f"eye.{tag}"].y - 0.02 * h:
                b.regions[i] = "eyelid"
                regions["eyelid"].append(i)
                break
        for tag in ("L", "R"):
            if (p - lm[f"brow.{tag}"]).length < 0.026 * h and p.z > lm["eye"].z:
                b.regions[i] = "brow"
                regions["brow"].append(i)
                break
        if (p - lm["mouth"]).length < 0.058 * h * spec.face.mouth_width and abs(p.y - lm["mouth"].y) < 0.022 * h:
            b.regions[i] = "lip"
            regions["lip"].append(i)
        if (p - lm["nose_base"]).length < 0.020 * h and p.z < lm["nose_base"].z:
            b.regions[i] = "nostril"
            regions["nostril"].append(i)
    for name, idxs in regions.items():
        for i in idxs:
            b.set_group(name, i, 1.0)

    return HeadResult(builder=b, rings={}, regions=regions)
