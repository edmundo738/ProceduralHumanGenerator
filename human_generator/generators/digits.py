# -*- coding: utf-8 -*-
"""Digit (finger / toe) chains built from joint anchors + flex angles.

A digit is a loft of elliptical rings along its phalanges.  Joints receive
edge creases (holding loops under subdivision), the pulp gets a fuller front
scale, an optional dorsal nail plate patch is merged, and one vertex group
per phalanx is authored for the rig.  The same code serves hands and feet.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

from ..core._math import Vector
from ..core.topology import MeshBuilder


@dataclass
class DigitPlan:
    kind: str = "finger"                 # "finger" | "toe"
    name: str = "middle"
    anchors: list = field(default_factory=list)   # joint chain base→tip
    base_radius: float = 0.0095
    taper: float = 0.80
    flex: list = field(default_factory=list)       # radians per joint (n-1)
    volar: Vector = None                           # palm/sole-facing direction
    flatness: float = 0.88                         # depth/width
    pulp: float = 1.07
    segments: int = 3
    ring_n: int = 8
    nail: bool = True


def _frame(dirv: Vector, volar: Vector):
    u = dirv.cross(volar)
    if u.length_squared < 1e-10:
        u = Vector((1.0, 0.0, 0.0))
    u = u.normalized()
    v = u.cross(dirv).normalized()
    if v.dot(volar) < 0.0:
        v = -v
    return u, v


def _rotate_toward(d0: Vector, toward: Vector, ang: float) -> Vector:
    """Rotate ``d0`` toward ``toward`` (within their plane) by ``ang`` rad."""
    axis = d0.cross(toward)
    if axis.length_squared < 1e-10 or abs(ang) < 1e-9:
        return Vector(d0)
    axis = axis.normalized()
    # bending moves distal toward volar → negative rotation sense
    a = -abs(ang)
    c, s = math.cos(a), math.sin(a)
    v = d0 * c + axis.cross(d0) * s + axis * (axis.dot(d0) * (1.0 - c))
    return v.normalized()


def _ring(c: Vector, dirv: Vector, volar: Vector, r: float, plan: DigitPlan,
          front_scale: float = 1.0) -> list[Vector]:
    u, v = _frame(dirv, volar)
    w = r * 1.06
    d = r * plan.flatness
    n = plan.ring_n
    out = []
    for k in range(n):
        a = 2.0 * math.pi * k / n
        s = math.sin(a)
        sc = front_scale if s > 0.0 else 1.0
        out.append(c + u * (math.cos(a) * w) + v * (s * d * sc))
    return out


def digit_rings(plan: DigitPlan, sink_base: float = 0.006) -> list[list[Vector]]:
    anchors = [Vector(a) for a in plan.anchors]
    if len(anchors) < 2:
        return []
    volar = Vector(plan.volar).normalized() if plan.volar is not None else Vector((0, 1, 0))
    nseg = len(anchors) - 1
    flex = list(plan.flex) + [0.0] * max(0, nseg - len(plan.flex))
    rings: list[list[Vector]] = []

    root_dir = (anchors[1] - anchors[0]).normalized()
    c0 = anchors[0] - root_dir * sink_base
    rings.append(_ring(c0, root_dir, volar, plan.base_radius * 1.14, plan))
    cum = 0.0
    for si in range(nseg):
        a0, a1 = anchors[si], anchors[si + 1]
        seg = a1 - a0
        if seg.length_squared < 1e-12:
            continue
        base_dir = seg.normalized()
        for t_i in range(1, plan.segments + 1):
            t = t_i / plan.segments
            dirv = _rotate_toward(base_dir, volar, cum + flex[si] * t)
            c = a0 + seg * t
            taper = plan.taper ** (si + t)
            near_tip = (si == nseg - 1) and t > 0.0
            front = plan.pulp if near_tip else 1.0
            rings.append(_ring(c, dirv, volar, plan.base_radius * taper, plan, front))
        cum += flex[si]
    return rings


def build_digit(builder: MeshBuilder, plan: DigitPlan, *, material: str | None = None,
                crease: float = 0.35, group_prefix: str = "") -> dict:
    """Loft a whole digit into ``builder``; returns ``{"rings","start","end"}``."""
    rings = digit_rings(plan)
    if len(rings) < 2:
        return {"rings": [], "start": [], "end": []}
    res = builder.loft(rings, close=True, region="skin",
                       material=material or "skin",
                       uv_rect=(0.0, 1.0, 0.0, 1.0),
                       cap_start="none", cap_end="pole")
    ids = res["rings"]
    seg = plan.segments + 1  # rings per phalanx after the root
    # joint creases (between phalanges) + per-phalanx groups
    for si in range(len(plan.anchors) - 2):
        boundary = 1 + (si + 1) * seg
        if 0 < boundary < len(ids):
            builder.crease_ring(ids[boundary], crease)
    for ri, ring in enumerate(ids):
        band = max(0, min(len(plan.anchors) - 2, (ri - 1) // seg if ri >= 1 else 0))
        gname = f"{group_prefix}{plan.kind}.{plan.name}.{band}"
        for vi in ring:
            builder.set_group(gname, vi, 1.0)
    if plan.nail:
        add_nail(builder, plan)
    return res


def add_nail(builder: MeshBuilder, plan: DigitPlan) -> None:
    """Curved dorsal nail plate (3×4 grid patch above the distal tip)."""
    anchors = [Vector(a) for a in plan.anchors]
    tip, prev = anchors[-1], anchors[-2]
    dirv = (tip - prev).normalized()
    volar = Vector(plan.volar).normalized() if plan.volar is not None else Vector((0, 1, 0))
    dorsal = -volar
    u, _v = _frame(dirv, volar)
    r = plan.base_radius * plan.taper ** (len(anchors) - 1)
    L = r * (2.3 if plan.kind == "finger" else 1.5)
    W = r * 1.35
    rows: list[list[Vector]] = []
    for ri in range(4):
        t = ri / 3.0
        # S3.6 — defeito medido: a placa ia de −0.28·L a **+0.72·L** a contar da
        # âncora do ápice, ou seja a borda livre ficava 4.1–5.7 mm ALÉM da ponta
        # arredondada do dedo (medido em dedos e dedo do pé grande: unha em
        # +7.1 mm, cap em +3.5 mm).  A unha é agora um prato de comprimento L que
        # acaba no plano do ápice (zc de −L a 0): borda livre na ponta, como
        # anatomicamente.
        zc = -L * (1.0 - t)
        arch = r * (0.34 + 0.42 * math.sin(math.pi * (0.20 + 0.62 * t)))
        width = W * (1.0 - 0.30 * t)
        row = []
        for ci in range(4):
            x = (ci / 3.0 - 0.5) * 2.0 * width
            p = tip + dirv * zc + dorsal * arch + u * x
            row.append(p)
        rows.append(row)
    local = MeshBuilder(f"nail.{plan.name}")
    local.patch_grid(rows, region="nail", material="nail", uv_rect=(0.0, 1.0, 0.0, 1.0))
    builder.merge(local)
