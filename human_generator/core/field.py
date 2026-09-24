# -*- coding: utf-8 -*-
"""Anatomical deformation fields.

Features (bone bumps, soft tissue, eye sockets…) are *fields*: functions of
position that push mesh vertices.  Generators author their base cage with
correct silhouette and then compose a :class:`DeformStack`; because fields are
analytic they weld parts together (adjacent shells get displaced identically
along shared boundaries, hiding seams).
"""
from __future__ import annotations

import math
from typing import Callable, Iterable, Sequence

from ._math import Vector, clamp, mix, smoothstep
from ..core.rng import Rng


# ----------------------------------------------------------------------------- helpers
def falloff(dist: float, radius: float, *, shape: str = "smooth", inside: bool = True) -> float:
    """1 at the centre, 0 at ``radius``. ``dist`` may be negative for a band."""
    if radius <= 0.0:
        return 0.0
    t = min(1.0, abs(dist) / radius)
    if shape == "linear":
        v = 1.0 - t
    elif shape == "gauss":
        v = math.exp(-2.5 * t * t)
    elif shape == "cos":
        v = 0.5 + 0.5 * math.cos(math.pi * t)
    elif shape == "pow":
        v = (1.0 - t) ** 2
    else:  # smooth
        v = 1.0 - t * t * (3.0 - 2.0 * t)
    return v if inside else 1.0 - v


def smooth_min(a: float, b: float, k: float) -> float:
    if k <= 0.0:
        return min(a, b)
    d = abs(b - a)
    if d >= k:
        return min(a, b)
    h = 1.0 - d / k
    return min(a, b) - 0.25 * k * h * h


def smooth_max(a: float, b: float, k: float) -> float:
    return -smooth_min(-a, -b, k)


def ellipsoid_outside(p, centre, radii) -> float:
    """Rough signed distance outside an axis-aligned ellipsoid (0 on surface)."""
    d = 0.0
    for i in range(3):
        r = max(1e-6, radii[i])
        t = (p[i] - centre[i]) / r
        d = max(d, t * t - 1.0)
    return max(0.0, math.sqrt(d)) if d > 0 else d * 0.5


def capsule_distance(p, a, b, r: float = 0.0) -> float:
    ab = b - a
    len2 = ab.length_squared
    t = clamp((p - a).dot(ab) / len2, 0.0, 1.0) if len2 > 1e-12 else 0.0
    return (p - (a + ab * t)).length - r


def segment_closest(p, a, b):
    ab = b - a
    len2 = ab.length_squared
    t = clamp((p - a).dot(ab) / len2, 0.0, 1.0) if len2 > 1e-12 else 0.0
    return a + ab * t, t


# ----------------------------------------------------------------------------- deformers
class Deformer:
    """A single displacement field.

    mode        meaning
    ----        -------
    ``gauss``   anisotropic gaussian bump (push along ``direction`` or radial)
    ``socket``  inward spherical depression (negative gauss along -normal)
    ``ridge``   gaussian ridge along a line (a→b) (nose, nasolabial…)
    ``flatten`` project-and-clamp onto a plane (jaw cut, sole of the foot)
    ``twist``   rotate about an axis with gaussian falloff
    ``capsule`` bulge around a line segment (muscles)
    ``noise``   rng-driven wobble
    """

    __slots__ = ("mode", "centre", "sigma", "amp", "direction", "a", "b",
                 "plane_n", "plane_d", "angle", "freq", "rng", "mask")

    def __init__(self, mode: str, *, centre=None, sigma=(0.05, 0.05, 0.05),
                 amp: float = 0.0, direction=None, a=None, b=None,
                 plane_n=None, plane_d: float = 0.0, angle: float = 0.0,
                 freq: float = 1.0, rng: Rng | None = None,
                 mask: Callable[[Vector], float] | None = None):
        self.mode = mode
        self.centre = Vector(centre) if centre is not None else Vector((0, 0, 0))
        self.sigma = tuple(float(s) for s in sigma)
        self.amp = float(amp)
        self.direction = Vector(direction).normalized() if direction is not None else None
        self.a = Vector(a) if a is not None else None
        self.b = Vector(b) if b is not None else None
        self.plane_n = Vector(plane_n).normalized() if plane_n is not None else None
        self.plane_d = float(plane_d)
        self.angle = float(angle)
        self.freq = float(freq)
        self.rng = rng
        self.mask = mask

    # -- evaluation ---------------------------------------------------------
    def _gauss(self, p: Vector) -> float:
        d = 0.0
        for i in range(3):
            s = max(1e-6, self.sigma[i])
            t = (p[i] - self.centre[i]) / s
            d += t * t
        return math.exp(-0.5 * d)

    def evaluate(self, p: Vector, normal: Vector | None = None) -> Vector:
        mode = self.mode
        if mode == "gauss":
            g = self._gauss(p)
            if g < 1e-4:
                return Vector((0, 0, 0))
            if self.direction is not None:
                return self.direction * (self.amp * g)
            if normal is not None:
                return normal * (self.amp * g)
            v = p - self.centre
            return (v.normalized() if v.length > 1e-9 else Vector((0, 0, 0))) * (self.amp * g)
        if mode == "socket":
            g = self._gauss(p)
            if g < 1e-4:
                return Vector((0, 0, 0))
            d = self.direction if self.direction is not None else (normal or Vector((0, 1, 0)))
            return d * (self.amp * g)  # amp negative → inward
        if mode == "ridge" and self.a is not None and self.b is not None:
            q, _ = segment_closest(p, self.a, self.b)
            d = (p - q).length
            g = falloff(d, max(1e-6, self.sigma[0]), shape="gauss")
            if g < 1e-4:
                return Vector((0, 0, 0))
            dirv = self.direction if self.direction is not None else (p - q).normalized() if d > 1e-9 else Vector((0, 0, 1))
            return dirv * (self.amp * g)
        if mode == "capsule" and self.a is not None and self.b is not None:
            d = capsule_distance(p, self.a, self.b, 0.0)
            g = falloff(d, max(1e-6, self.sigma[0]), shape="smooth")
            if g < 1e-4:
                return Vector((0, 0, 0))
            dirv = self.direction if self.direction is not None else (p - segment_closest(p, self.a, self.b)[0]).normalized()
            return dirv * (self.amp * g)
        if mode == "flatten" and self.plane_n is not None:
            # clamp points that exceed the plane (height > amp) back onto it,
            # softened over ``sigma[0]`` so the silhouette doesn't crease.
            s = p.dot(self.plane_n) - self.plane_d
            over = s - self.amp
            if over <= 0.0:
                return Vector((0.0, 0.0, 0.0))
            soft = max(1e-6, self.sigma[0])
            disp = over * soft / (over + soft)
            return self.plane_n * (-disp)
        if mode == "twist":
            d = p - self.centre
            g = falloff(math.sqrt(d.x * d.x + d.y * d.y), max(1e-6, self.sigma[0]), shape="gauss")
            if g < 1e-4:
                return Vector((0, 0, 0))
            axis = self.direction if self.direction is not None else Vector((0, 0, 1))
            ang = self.angle * g
            c, s = math.cos(ang), math.sin(ang)
            if abs(axis.z) > 0.9:
                x2 = d.x * c - d.y * s
                y2 = d.x * s + d.y * c
                return Vector((x2 - d.x, y2 - d.y, 0.0))
            x2 = d.x * c - d.z * s
            z2 = d.x * s + d.z * c
            return Vector((x2 - d.x, 0.0, z2 - d.z))
        if mode == "noise":
            rng = self.rng or Rng(0)
            n = rng.fbm3((p.x * self.freq, p.y * self.freq, p.z * self.freq), octaves=3)
            dirv = self.direction if self.direction is not None else (normal or Vector((0, 0, 1)))
            return dirv * (self.amp * n)
        return Vector((0, 0, 0))


class DeformStack:
    """Ordered composition of :class:`Deformer` fields."""

    def __init__(self):
        self.items: list[Deformer] = []

    # -- authoring API --------------------------------------------------------
    def add(self, deformer: Deformer) -> Deformer:
        self.items.append(deformer)
        return deformer

    def bump(self, centre, amp: float, radius=0.05, *, direction=None, mask=None,
              sigma=None, mode="gauss") -> Deformer:
        if sigma is None:
            r = radius
            sigma = (r, r, r) if isinstance(r, float) else tuple(r)
        d = Deformer(mode, centre=centre, sigma=sigma, amp=amp, direction=direction, mask=mask)
        return self.add(d)

    def anisotropic(self, centre, amp: float, sigma, *, direction=None, mask=None) -> Deformer:
        return self.add(Deformer("gauss", centre=centre, sigma=sigma, amp=amp,
                                 direction=direction, mask=mask))

    def socket(self, centre, depth: float, radius=0.03, *, direction=None, mask=None) -> Deformer:
        return self.add(Deformer("socket", centre=centre,
                                 sigma=(radius, radius, radius),
                                 amp=-abs(depth), direction=direction, mask=mask))

    def ridge(self, a, b, amp: float, width: float, *, direction=None, mask=None) -> Deformer:
        return self.add(Deformer("ridge", a=a, b=b, sigma=(width, width, width),
                                 amp=amp, direction=direction, mask=mask))

    def muscle(self, a, b, amp: float, radius: float, *, direction=None) -> Deformer:
        return self.add(Deformer("capsule", a=a, b=b, sigma=(radius, radius, radius),
                                 amp=amp, direction=direction))

    def twist(self, centre, angle: float, radius: float, *, axis=None, mask=None) -> Deformer:
        return self.add(Deformer("twist", centre=centre, sigma=(radius, radius, radius),
                                 angle=angle, direction=axis, mask=mask))

    def noise(self, amp: float, freq: float, seed: int, *, direction=None) -> Deformer:
        return self.add(Deformer("noise", amp=amp, freq=freq, rng=Rng(seed),
                                 direction=direction))

    # -- application ----------------------------------------------------------
    def apply(self, points: Sequence[Vector], normals: Sequence[Vector] | None = None) -> list[Vector]:
        if not self.items:
            return [Vector(p) for p in points]
        out = []
        for i, p in enumerate(points):
            n = normals[i] if normals is not None else None
            acc = Vector((0.0, 0.0, 0.0))
            for d in self.items:
                if d.mask is not None and d.mask(p) == 0.0:
                    continue
                delta = d.evaluate(p, n)
                if d.mask is not None:
                    delta = delta * d.mask(p)
                acc += delta
            out.append(p + acc)
        return out

    def apply_mesh(self, verts: list[Vector], faces: list[tuple]) -> None:
        """In-place displacement of a (verts, faces) pair with estimated normals."""
        normals = estimate_normals(verts, faces)
        new = self.apply(verts, normals)
        verts[:] = new


def estimate_normals(verts: Sequence[Vector], faces: Iterable[Sequence[int]]) -> list[Vector]:
    n = [Vector((0.0, 0.0, 0.0)) for _ in verts]
    for f in faces:
        if len(f) < 3:
            continue
        fn = (Vector(verts[f[1]]) - Vector(verts[f[0]])).cross(
              Vector(verts[f[2]]) - Vector(verts[f[0]]))
        for vi in f:
            n[vi] += fn
    return [v.normalized() if v.length_squared > 1e-12 else Vector((0.0, 0.0, 1.0)) for v in n]
