# -*- coding: utf-8 -*-
"""Deterministic randomness.

All stochastic aspects of the character (phenotype jitter, hair strands,
pore placement…) draw from a seeded :class:`Rng`; no global ``random`` state
is ever touched, so two runs with the same seed are bit-identical.
"""
from __future__ import annotations

import hashlib
import math
import struct
from . import _math as _m

Mask64 = 0xFFFFFFFFFFFFFFFF


def splitmix64(x: int) -> int:
    """The one-liner PRNG — used both as the generator and as a stable hash."""
    x = (x + 0x9E3779B97F4A7C15) & Mask64
    z = x
    z = ((z ^ (z >> 30)) * 0xBF58476D1CE4E5B9) & Mask64
    z = ((z ^ (z >> 27)) * 0x94D049BB133111EB) & Mask64
    return z ^ (z >> 31)


def hash_ints(*parts: int, salt: int = 0) -> int:
    x = salt
    for p in parts:
        x = splitmix64((x ^ (int(p) & Mask64)) & Mask64)
    return x & Mask64


def hash_floats(*vals: float, quant: float = 1e-6, salt: int = 0) -> int:
    ints = tuple(int(round(v / quant)) for v in vals)
    return hash_ints(*ints, salt=salt)


def digest_float(*parts) -> float:
    """Stable 0..1 hash of mixed int/float/str parts (no quantisation issues)."""
    buf = []
    for p in parts:
        if isinstance(p, float):
            buf.append(struct.pack("<d", round(p, 7)))
        elif isinstance(p, int):
            buf.append(struct.pack("<q", p))
        else:
            buf.append(str(p).encode("utf-8"))
    h = hashlib.blake2b(b"|".join(buf), digest_size=8).digest()
    return int.from_bytes(h, "little") / float(1 << 64)


class Rng:
    """Seed-able PRNG: splitmix64 stream + gaussian helpers.

    ``Rng(seed)`` with the same seed produces the same stream regardless of
    platform/python — only float rounding (never) differs.
    """

    def __init__(self, seed: int = 0, salt: int = 0):
        self.seed = int(seed)
        self._state = splitmix64(self.seed) ^ (0xD1B54A32D192ED03 & salt)
        self._spare: float | None = None

    def _next01(self) -> float:
        self._state = splitmix64(self._state)
        return ((self._state >> 11) & ((1 << 53) - 1)) / float(1 << 53)

    def uniform(self, a: float = 0.0, b: float = 1.0) -> float:
        return a + (b - a) * self._next01()

    f = uniform  # short alias used everywhere

    def range(self, a: float, b: float) -> float:
        return a + (b - a) * self._next01()

    def int_range(self, a: int, b: int) -> int:
        return a + int(self._next01() * (b - a + 1) - 1e-9)

    def bool(self, p: float = 0.5) -> bool:
        return self._next01() < p

    def sign(self) -> float:
        return 1.0 if self._next01() < 0.5 else -1.0

    def normal(self, mu: float = 0.0, sigma: float = 1.0) -> float:
        """Marsaglia polar (Box-Muller alternative), with cached spare."""
        if self._spare is not None:
            v, self._spare = self._spare, None
            return mu + sigma * v
        while True:
            u = 2.0 * self._next01() - 1.0
            w = 2.0 * self._next01() - 1.0
            s = u * u + w * w
            if 0.0 < s < 1.0:
                m = math.sqrt(-2.0 * math.log(s) / s)
                self._spare = w * m
                return mu + sigma * u * m

    n = normal

    def gaussian(self, mu: float = 0.0, sigma: float = 1.0) -> float:
        return self.normal(mu, sigma)

    def choice(self, seq):
        return seq[int(self._next01() * len(seq)) % len(seq)]

    def unit_vector(self):
        while True:
            x, y, z = (self.normal() for _ in range(3))
            l = math.sqrt(x * x + y * y + z * z)
            if l > 1e-6:
                return _m.Vector((x / l, y / l, z / l))

    def jitter(self, value: float, amount: float) -> float:
        return value + self.normal(0.0, amount)

    # -- spatial noise ---------------------------------------------------
    def noise3(self, x: float, y: float, z: float) -> float:
        """Hash-based value noise in [-1, 1]; deterministic given the seed."""
        V = _m.Vector
        ix, iy, iz = math.floor(x), math.floor(y), math.floor(z)
        fx, fy, fz = x - ix, y - iy, z - iz

        def corner(dx, dy, dz):
            h = hash_ints(ix + dx, iy + dy, iz + dz, salt=self.seed)
            return ((h >> 13) & 0xFFFF) / 32768.0 - 1.0

        sx = fx * fx * (3 - 2 * fx)
        sy = fy * fy * (3 - 2 * fy)
        sz = fz * fz * (3 - 2 * fz)
        c000, c100 = corner(0, 0, 0), corner(1, 0, 0)
        c010, c110 = corner(0, 1, 0), corner(1, 1, 0)
        c001, c101 = corner(0, 0, 1), corner(1, 0, 1)
        c011, c111 = corner(0, 1, 1), corner(1, 1, 1)
        lerp = _m.mix
        x00 = lerp(c000, c100, sx)
        x10 = lerp(c010, c110, sx)
        x01 = lerp(c001, c101, sx)
        x11 = lerp(c011, c111, sx)
        y0 = lerp(x00, x10, sy)
        y1 = lerp(x01, x11, sy)
        return lerp(y0, y1, sz)

    def fbm3(self, co, octaves: int = 4, lac: float = 2.0, gain: float = 0.5) -> float:
        x, y, z = co[0], co[1], co[2]
        amp, tot, f = 1.0, 0.0, 1.0
        for _ in range(octaves):
            tot += amp * self.noise3(x * f, y * f, z * f)
            f *= lac
            amp *= gain
        return tot / max(1e-6, 1.0 - 0.5 ** octaves and 1.0)

    def ridged3(self, co, octaves: int = 4, lac: float = 2.1, gain: float = 0.5) -> float:
        x, y, z = co[0], co[1], co[2]
        amp, tot, f = 1.0, 0.0, 1.0
        for _ in range(octaves):
            tot += amp * (1.0 - abs(self.noise3(x * f, y * f, z * f)))
            f *= lac
            amp *= gain
        return tot / max(1e-6, 1.0 - 0.5 ** octaves and 1.0)

    # -- mesh hashing (determinism gate) -----------------------------------
    @staticmethod
    def mesh_digest(verts) -> str:
        h = hashlib.blake2s(digest_size=16)
        for p in verts:
            h.update(struct.pack("<3f", round(p[0], 5), round(p[1], 5), round(p[2], 5)))
        return h.hexdigest()[:16]
