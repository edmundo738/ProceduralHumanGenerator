# -*- coding: utf-8 -*-
"""``Vector``/``Matrix``: Blender's mathutils when available, otherwise a
minimal pure-python stand-in with the same API subset used by this package.

This lets the anatomy/field/topology layers be unit-tested (and used for
offline previews) without importing ``bpy`` at all.
"""
from __future__ import annotations

import math as _math

try:  # pragma: no cover - exercised inside Blender
    from mathutils import Matrix, Vector  # type: ignore

    MATHUTILS = True
except ImportError:  # pragma: no cover - pure python environments
    MATHUTILS = False

    class Vector:
        __slots__ = ("_c",)

        def __init__(self, co=(), /):
            if isinstance(co, Vector):
                self._c = list(co._c)
            elif isinstance(co, (int, float)):
                self._c = [float(co)] * 3
            else:
                c = [float(x) for x in co]
                if len(c) not in (2, 3, 4):
                    raise ValueError("expected 2/3/4 components")
                if len(c) == 2:
                    c.append(0.0)
                self._c = c

        # -- component access ------------------------------------------------
        @property
        def x(self): return self._c[0]

        @x.setter
        def x(self, v): self._c[0] = float(v)

        @property
        def y(self): return self._c[1]

        @y.setter
        def y(self, v): self._c[1] = float(v)

        @property
        def z(self):
            if len(self._c) < 3:
                return 0.0
            return self._c[2]

        @z.setter
        def z(self, v): self._c[2] = float(v)

        @property
        def w(self): return self._c[3]

        def __getitem__(self, i): return self._c[i]

        def __setitem__(self, i, v): self._c[i] = float(v)

        def __len__(self): return len(self._c)

        def __iter__(self): return iter(self._c)

        def __repr__(self): return f"<Vector ({', '.join(f'{v:.4f}' for v in self._c)})>"

        def to_tuple(self): return tuple(self._c)
        def copy(self): return Vector(self)

        def __hash__(self):
            raise TypeError("unhashable Vector")

        def __eq__(self, other):
            try:
                return all(abs(a - b) < 1e-7 for a, b in zip(self._c, Vector(other)._c))
            except Exception:
                return NotImplemented

        # -- arithmetic ------------------------------------------------------
        def __add__(self, o): return Vector([a + b for a, b in zip(self._c, Vector(o)._c)])
        __radd__ = __add__

        def __sub__(self, o): return Vector([a - b for a, b in zip(self._c, Vector(o)._c)])

        def __rsub__(self, o): return Vector([a - b for a, b in zip(Vector(o)._c, self._c)])

        def __neg__(self): return Vector([-a for a in self._c])

        def __mul__(self, o):
            if isinstance(o, (int, float)):
                return Vector([a * o for a in self._c])
            return Vector([a * b for a, b in zip(self._c, Vector(o)._c)])

        __rmul__ = __mul__

        def __truediv__(self, o):
            if isinstance(o, (int, float)):
                return Vector([a / o for a in self._c])
            return Vector([a / b for a, b in zip(self._c, Vector(o)._c)])

        def __iadd__(self, o):
            self._c = [a + b for a, b in zip(self._c, Vector(o)._c)]
            return self

        def __isub__(self, o):
            self._c = [a - b for a, b in zip(self._c, Vector(o)._c)]
            return self

        def __imatmul__(self, m):
            self._c = list((m @ self)._c)
            return self

        # -- ops -------------------------------------------------------------
        def dot(self, o): return sum(a * b for a, b in zip(self._c, Vector(o)._c))

        def cross(self, o):
            a, b = self._c, Vector(o)._c
            if len(a) != 3 or len(b) != 3:
                raise ValueError("cross needs 3D")
            return Vector((a[1] * b[2] - a[2] * b[1],
                           a[2] * b[0] - a[0] * b[2],
                           a[0] * b[1] - a[1] * b[0]))

        @property
        def length_squared(self): return sum(a * a for a in self._c)

        @property
        def length(self): return _math.sqrt(self.length_squared)

        def normalized(self):
            l = self.length
            return Vector([a / l if l > 1e-12 else 0.0 for a in self._c])

        def normalize(self):
            l = self.length
            if l > 1e-12:
                self._c = [a / l for a in self._c]

        def angle(self, o):
            d = self.normalized().dot(Vector(o).normalized())
            return _math.acos(max(-1.0, min(1.0, d)))

        def projection(self, o):
            o = Vector(o)
            d = o.length_squared
            if d < 1e-16:
                return Vector((0.0, 0.0, 0.0))
            return o * (self.dot(o) / d)

        project = projection

        def lerp(self, other, t):
            o = Vector(other)
            return Vector([x + (y - x) * t for x, y in zip(self._c, o._c)])

        @classmethod
        def lerp_to(cls, a, b, t):  # explicit static variant, same maths
            a, b = Vector(a), Vector(b)
            return Vector([x + (y - x) * t for x, y in zip(a._c, b._c)])

        def __matmul__(self, o):  # vector @ matrix (row-vector convention)
            if isinstance(o, Matrix):
                r = [sum(a * o[r_i][k] for k, a in enumerate(self._c[:o.size[0]])) for r_i in range(o.size[1])]
                if o.size[1] == 4:
                    return Vector(r[:3] + [(sum(a * o[r_i][k] for k, a in enumerate(self._c)) ) and 1.0][:1])
                return Vector(r)
            return self.dot(o)

    class Matrix:
        """Column-major mathutils-style matrix (m @ v transforms v)."""

        __slots__ = ("_rows",)

        def __init__(self, rows):
            if isinstance(rows, int):
                rows = [[1.0 if i == j else 0.0 for j in range(rows)] for i in range(rows)]
            data = [list(map(float, row)) for row in rows]
            self._rows = data

        # -- basics ----------------------------------------------------------
        @property
        def size(self): return (len(self._rows), len(self._rows[0]))

        def __getitem__(self, i):
            row = self._rows[i]
            if isinstance(i, int):
                return Vector(row)
            return [Vector(r) for r in row]

        def __setitem__(self, i, val): self._rows[i] = list(map(float, val))

        def __iter__(self): return iter(Vector(r) for r in self._rows)

        def __len__(self): return len(self._rows)

        def __repr__(self):
            return "<Matrix " + " | ".join(",".join(f"{v:.3f}" for v in r) for r in self._rows) + ">"

        def copy(self): return Matrix([list(r) for r in self._rows])

        def to_4x4(self):
            n = len(self._rows)
            out = [[self._rows[i][j] if i < n and j < n else (1.0 if i == j else 0.0)
                    for j in range(4)] for i in range(4)]
            return Matrix(out)

        # -- constructors ----------------------------------------------------
        @staticmethod
        def Identity(size=4): return Matrix([[1.0 if i == j else 0.0 for j in range(size)] for i in range(size)])

        @staticmethod
        def Translation(v):
            v = Vector(v)
            m = Matrix.Identity(4)
            m._rows[0][3] = v.x
            m._rows[1][3] = v.y
            m._rows[2][3] = v.z
            return m

        @staticmethod
        def Diagonal(diag):
            diag = list(diag)
            n = len(diag)
            return Matrix([[diag[i] if i == j else 0.0 for j in range(n)] for i in range(n)])

        @staticmethod
        def Scale(factor, size, axis=None):
            if axis is None:
                return Matrix.Diagonal([factor] * size)
            n = max(3, size)
            axis = Vector(axis).normalized()
            rows = []
            for i in range(n):
                for j in range(n):
                    pass
            rows = [[(axis[i] * axis[j]) * (factor - 1.0) + (1.0 if i == j else 0.0)
                     for j in range(n)] for i in range(n)]
            return Matrix(rows[:size]) if size != n else Matrix(rows)

        @staticmethod
        def Rotation(angle, size=4, axis=(0.0, 0.0, 1.0)):
            ax = Vector(axis).normalized()
            if ax.dot(ax) < 1e-12:
                ax = Vector((0.0, 0.0, 1.0))
            c, s = _math.cos(angle), _math.sin(angle)
            t = 1.0 - c
            x, y, z = ax.x, ax.y, ax.z
            r = [
                [t * x * x + c, t * x * y - s * z, t * x * z + s * y],
                [t * x * y + s * z, t * y * y + c, t * y * z - s * x],
                [t * x * z - s * y, t * y * z + s * x, t * z * z + c],
            ]
            if size >= 4:
                rows = [[r[i][j] for j in range(3)] + [0.0] for i in range(3)] + [[0.0, 0.0, 0.0, 1.0]]
                return Matrix(rows)
            return Matrix(r)

        # -- ops -------------------------------------------------------------
        @property
        def translation(self):
            if len(self._rows) >= 4:
                return Vector((self._rows[0][3], self._rows[1][3], self._rows[2][3]))
            return Vector((0.0, 0.0, 0.0))

        @translation.setter
        def translation(self, v):
            v = Vector(v)
            self._rows[0][3], self._rows[1][3], self._rows[2][3] = v.x, v.y, v.z

        def __matmul__(self, other):
            if isinstance(other, Vector):
                n = len(self._rows)
                v = list(other._c) + ([1.0] if len(other._c) == 3 and n == 4 else []) + [0.0] * (n - len(other._c) - 1)
                out = [sum(self._rows[i][k] * v[k] for k in range(n)) for i in range(n)]
                m = len(other._c)
                return Vector(out[:m])
            rows_b = other._rows
            rows_a = self._rows
            k = min(len(rows_a[0]), len(rows_b))
            return Matrix([[sum(rows_a[i][t] * rows_b[t][j] for t in range(k)) for j in range(len(rows_b[0]))]
                           for i in range(len(rows_a))])

        def transposed(self):
            rows = self._rows
            return Matrix([[rows[j][i] for j in range(len(rows))] for i in range(len(rows[0]))])

        def inverted(self):
            m = self.to_4x4()
            r = m._rows
            # affine fast path
            lin = [[r[i][j] for j in range(3)] for i in range(3)]
            det = (lin[0][0] * (lin[1][1] * lin[2][2] - lin[1][2] * lin[2][1])
                   - lin[0][1] * (lin[1][0] * lin[2][2] - lin[1][2] * lin[2][0])
                   + lin[0][2] * (lin[1][0] * lin[2][1] - lin[1][1] * lin[2][0]))
            if abs(det) < 1e-12:
                raise ValueError("matrix not invertible")
            inv = [
                [(lin[j][i]) for j in range(3)] for i in range(3)
            ]
            # cofactor inverse of 3x3
            cof = [[0.0] * 3 for _ in range(3)]
            for i in range(3):
                for j in range(3):
                    a1, a2 = (i + 1) % 3, (i + 2) % 3
                    b1, b2 = (j + 1) % 3, (j + 2) % 3
                    cof[i][j] = ((lin[b1][a1] * lin[b2][a2] - lin[b1][a2] * lin[b2][a1])
                                 / det) * (1.0 if (i + j) % 2 == 0 else -1.0)
            out = [[0.0] * 4 for _ in range(4)]
            for i in range(3):
                for j in range(3):
                    out[i][j] = cof[i][j]
                out[i][3] = -sum(cof[i][k] * r[k][3] for k in range(3))
            out[3][3] = 1.0
            if len(self._rows) < 4:
                return Matrix([[out[i][j] for j in range(3)] for i in range(3)])
            return Matrix(out)

        @property
        def is_identity(self):
            n = len(self._rows)
            return all(abs(v - (1.0 if i == j else 0.0)) < 1e-7
                       for i in range(n) for j, v in enumerate(self._rows[i][:n]))

    # bind the helpers on Vector so both styles work
    def _vector_matmul(self, o):  # v @ m == m.transposed() transform (col-vec mathutils style)
        if isinstance(o, Matrix):
            return o @ self
        return self.dot(o)

    Vector.__matmul__ = _vector_matmul


def clamp(v, lo, hi):
    return lo if v < lo else hi if v > hi else v


def mix(a, b, t):
    return a + (b - a) * t


def smoothstep(a, b, x):
    if b <= a:
        return 1.0 if x >= b else 0.0
    t = clamp((x - a) / (b - a), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


__all__ = ["Vector", "Matrix", "clamp", "mix", "smoothstep", "MATHUTILS"]
