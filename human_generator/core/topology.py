# -*- coding: utf-8 -*-
"""Topology-aware mesh construction.

Everything a character needs is built from *quad loops*: a ring of control
vertices per anatomical station, bridged by quads, capped with pole fans.
Catmull-Clark subdivision then turns the coarse cage into a smooth organic
surface.  The builder keeps per-element metadata (region, UV, vertex group,
edge crease, material name) authored *during* construction — so masks, UVs,
skin weights and holding loops exist from the first quad, not patched on
after the fact.

Conventions (canonical authoring frame — see ``core.conventions``):

* ``+Z`` up, ``+Y`` **forward** (face direction), ``+X`` the character's left.
* all units metres.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Iterable, Sequence

from ._math import Vector, Matrix, clamp, mix

bmesh = None  # lazy: see _bmesh()


def _bmesh():
    global bmesh
    if bmesh is None:
        try:
            import bmesh as _b
        except ImportError as e:  # running without Blender
            raise RuntimeError("bmesh requires Blender — run through tools/blender_run.py") from e
        bmesh = _b
    return bmesh


# ----------------------------------------------------------------------------- regions
REGION_CODES: dict[str, float] = {
    "skin": 0.0, "scalp": 0.05, "beard": 0.075, "hair": 0.1, "eyebrow": 0.12,
    "eye": 0.15, "cornea": 0.2, "eyelid": 0.25, "brow": 0.3, "lip": 0.35,
    "nostril": 0.4, "ear_canal": 0.45, "oral": 0.5, "gum": 0.55,
    "enamel": 0.6, "dentin": 0.62, "tongue": 0.65, "nail": 0.7, "palm": 0.75,
    "sole": 0.8, "armpit": 0.85, "nipple": 0.9, "joint": 0.95, "cloth": 1.0,
    "leather": 1.05, "metal": 1.1, "neon": 1.15, "cyber": 1.2,
    "feather": 1.25, "halo": 1.3,
}
REGION_NAMES: dict[float, str] = {v: k for k, v in REGION_CODES.items()}


def _region_code(name: str | None) -> float:
    return REGION_CODES.get(name or "skin", 0.0)


# ----------------------------------------------------------------------------- sections
@dataclass
class Section:
    """One anatomical cross-section loop of the cage."""

    center: Vector
    tangent: Vector              # +width direction (character left)
    front: Vector                # +depth direction (face side), orthogonalised
    width: float = 0.10          # half-width
    depth: float = 0.08          # half-depth
    front_scale: float = 1.0
    back_scale: float = 1.0
    x_offset: float = 0.0        # lateral shift of the ellipse centre
    y_offset: float = 0.0        # front/back shift
    superellipse: float = 2.0    # 2 → ellipse; 3+ → more boxy (jaw, pelvis)
    roll: float = 0.0            # twist applied to sampling angle
    region: str = "skin"

    def __post_init__(self):
        self.center = Vector(self.center)
        self.tangent = Vector(self.tangent).normalized()
        f = Vector(self.front)
        f -= self.tangent * f.dot(self.tangent)
        if f.length_squared < 1e-9:
            f = self.tangent.cross(Vector((0, 0, 1)))
        self.front = f.normalized()
        if abs(self.superellipse) < 1.01:
            self.superellipse = 2.0

    @property
    def axis(self) -> Vector:
        return self.tangent.cross(self.front).normalized()

    @property
    def center_shifted(self) -> Vector:
        return self.center + self.tangent * self.x_offset + self.front * self.y_offset

    def point(self, t: float) -> Vector:
        ang = 2.0 * math.pi * t + self.roll
        c, s = math.cos(ang), math.sin(ang)
        e = self.superellipse
        pw = 2.0 / e
        x = self.width * math.copysign(abs(c) ** pw, c)
        y = self.depth * math.copysign(abs(s) ** pw, s)
        y *= self.front_scale if s >= 0.0 else self.back_scale
        return self.center_shifted + self.tangent * x + self.front * y

    def points(self, n: int, offset: float = 0.0) -> list[Vector]:
        return [self.point(i / n + offset / max(1, n)) for i in range(n)]

    def scaled(self, factor: float, extra: float = 0.0) -> "Section":
        return Section(Vector(self.center), Vector(self.tangent), Vector(self.front),
                       self.width * factor + extra, self.depth * factor + extra,
                       self.front_scale, self.back_scale, self.x_offset, self.y_offset,
                       self.superellipse, self.roll, self.region)


def make_section(center, tangent=(1, 0, 0), front=(0, 1, 0), *, width=0.1, depth=0.08,
                 front_scale=1.0, back_scale=1.0, x_offset=0.0, y_offset=0.0,
                 superellipse=2.0, roll=0.0, region="skin") -> Section:
    return Section(Vector(center), Vector(tangent), Vector(front), width, depth,
                   front_scale, back_scale, x_offset, y_offset, superellipse, roll, region)


# ----------------------------------------------------------------------------- builder
class MeshBuilder:
    """Accumulates verts/faces/metadata; converts to bmesh/mesh at the end."""

    def __init__(self, name: str = "builder"):
        self.name = name
        self.verts: list[Vector] = []
        self.faces: list[tuple[int, ...]] = []
        self.face_mat: list[str | None] = []
        self.regions: list[str] = []
        self.uvs: list[tuple[float, float]] = []
        self.groups: dict[str, dict[int, float]] = {}
        self.creases: dict[tuple[int, int], float] = {}
        self.materials: list[str] = []
        self.rings: dict[str, list[int]] = {}

    # -- primitives -------------------------------------------------------------
    @property
    def n_verts(self) -> int:
        return len(self.verts)

    def add_vert(self, co, region: str = "skin", uv=(0.0, 0.0)) -> int:
        self.verts.append(Vector(co))
        self.regions.append(region)
        self.uvs.append((float(uv[0]), float(uv[1])))
        return len(self.verts) - 1

    def add_face(self, idxs: Sequence[int], material: str | None = None) -> int:
        idxs = tuple(idxs)
        if len(idxs) < 3:
            return -1
        if len(set(idxs)) != len(idxs):
            return -1
        self.faces.append(idxs)
        self.face_mat.append(material)
        if material and material not in self.materials:
            self.materials.append(material)
        return len(self.faces) - 1

    def set_group(self, name: str, idx: int, weight: float = 1.0) -> None:
        self.groups.setdefault(name, {})[idx] = max(0.0, min(1.0, weight))

    def crease(self, a: int, b: int, weight: float) -> None:
        key = (min(a, b), max(a, b))
        self.creases[key] = max(self.creases.get(key, 0.0), weight)

    def crease_ring(self, ring_ids: Sequence[int], weight: float) -> None:
        ids = list(ring_ids)
        n = len(ids)
        for i in range(n):
            self.crease(ids[i], ids[(i + 1) % n], weight)

    def register_ring(self, name: str, ring_ids: Sequence[int]) -> None:
        self.rings[name] = list(ring_ids)

    # -- loft -------------------------------------------------------------------
    def loft(self, rings: list[list[Vector]], *, close: bool = True, region: str = "skin",
             material: str | None = None, uv_rect=(0.0, 1.0, 0.0, 1.0),
             register: str | None = None, cap_start: str = "none", cap_end: str = "none",
             pole_shrink: float = 0.42) -> dict:
        """Bridge a stack of rings (lists of points) with quads.

        Returns ``{"rings": [ids...], "start": ids, "end": ids}``.
        """
        u0, u1, v0, v1 = uv_rect
        created: list[list[int]] = []
        K = max(2, len(rings))
        for k, ring in enumerate(rings):
            v = mix(v0, v1, k / (K - 1))
            n = max(3, len(ring))
            ids = []
            for i, p in enumerate(ring):
                u = mix(u0, u1, i / n) if close else mix(u0, u1, i / max(1, n - 1))
                ids.append(self.add_vert(p, region, (u, v)))
            created.append(ids)
            if register:
                self.register_ring(f"{register}.{k}", ids)
        for k in range(len(created) - 1):
            a, b = created[k], created[k + 1]
            n = min(len(a), len(b))
            pairs = range(n) if close else range(n - 1)
            for i in pairs:
                j = (i + 1) % n if close else i + 1
                self.add_face((a[i], a[j], b[j], b[i]), material=material)
        if cap_start == "pole":
            self.cap_pole(created[0], -1, shrink=pole_shrink, region=region,
                          material=material, uv_v=v0)
        if cap_end == "pole":
            self.cap_pole(created[-1], +1, shrink=pole_shrink, region=region,
                          material=material, uv_v=v1)
        return {"rings": created, "start": created[0], "end": created[-1]}

    def cap_pole(self, ring_ids: Sequence[int], side: int, *, region="skin",
                 material=None, shrink: float = 0.45, uv_v: float = 1.0) -> int:
        """Cap an open ring: a shrunken intermediate ring, then a pole vertex.

        ``side`` (+1/-1) only picks the pole direction from the ring centroid —
        the intermediate ring keeps the loft flowing smoothly into the pole.
        """
        ids = list(ring_ids)
        n = len(ids)
        if n < 3:
            return -1
        c = Vector((0.0, 0.0, 0.0))
        for i in ids:
            c += self.verts[i]
        c /= n
        # ring normal: average of edge cross products
        nr = Vector((0.0, 0.0, 0.0))
        for i in range(n):
            p0, p1 = self.verts[ids[i]], self.verts[ids[(i + 1) % n]]
            nr += (p0 - c).cross(p1 - c)
        if nr.length_squared < 1e-12:
            nr = Vector((0, 0, 1))
        nr = nr.normalized() * (1.0 if side > 0 else -1.0)
        mid_ids = []
        for i in ids:
            p = self.verts[i]
            q = c + (p - c) * shrink
            uv = self.uvs[i]
            mid_ids.append(self.add_vert(q, region, (uv[0], uv[1] + (uv_v - uv[1]) * 0.35)))
        for i in range(n):
            a, b = ids[i], ids[(i + 1) % n]
            d, cc = mid_ids[(i + 1) % n], mid_ids[i]
            self.add_face((a, b, d, cc), material=material)
        pole_uv = (0.5, uv_v)
        pole = self.add_vert(c + nr * (0.004 * max(0.2, shrink)), region, pole_uv)
        for i in range(n):
            a, b = mid_ids[i], mid_ids[(i + 1) % n]
            self.add_face((a, b, pole), material=material)
        return pole

    def patch_grid(self, rows: list[list[Vector]], *, region="skin", material=None,
                   uv_rect=(0.0, 1.0, 0.0, 1.0), register=None,
                   crease_v=0.0) -> dict:
        """Open quad grid (no wrap, no caps) — faces strips, garments panels."""
        u0, u1, v0, v1 = uv_rect
        created: list[list[int]] = []
        R = max(2, len(rows))
        for k, row in enumerate(rows):
            v = mix(v0, v1, k / (R - 1))
            n = max(2, len(row))
            ids = [self.add_vert(p, region, (mix(u0, u1, i / (n - 1)), v)) for i, p in enumerate(row)]
            created.append(ids)
            if register:
                self.register_ring(f"{register}.{k}", ids)
        for k in range(len(created) - 1):
            a, b = created[k], created[k + 1]
            n = min(len(a), len(b)) - 1
            for i in range(n):
                self.add_face((a[i], a[i + 1], b[i + 1], b[i]), material=material)
        if crease_v:
            for ring in (created[0], created[-1]):
                self.crease_ring(ring, crease_v)
        return {"rings": created, "start": created[0], "end": created[-1]}

    def arc_ring(self, radius: float, cx: float = 0.0, cz: float = 0.0,
                 a0: float = 0.0, a1: float = math.pi, n: int = 9,
                 y: float = 0.0) -> list[Vector]:
        """Ring of points along a circular arc in the XZ plane at height ``y``."""
        out = []
        for i in range(n):
            t = mix(a0, a1, i / max(1, n - 1))
            out.append(Vector((cx + math.cos(t) * radius, y, cz + math.sin(t) * radius)))
        return out

    # -- composition --------------------------------------------------------------
    def merge(self, other: "MeshBuilder", matrix: Matrix | None = None,
              group_prefix: str = "", ring_prefix: str | None = None) -> int:
        shift = len(self.verts)
        m = matrix
        for i, (v, reg, uv) in enumerate(zip(other.verts, other.regions, other.uvs)):
            p = (m @ v) if m is not None else v
            self.verts.append(Vector(p))
            self.regions.append(reg)
            self.uvs.append(tuple(uv))
        for f, mat in zip(other.faces, other.face_mat):
            self.faces.append(tuple(i + shift for i in f))
            self.face_mat.append(mat)
        for mat in other.materials:
            if mat not in self.materials:
                self.materials.append(mat)
        for gname, weights in other.groups.items():
            name = f"{group_prefix}{gname}" if group_prefix else gname
            tgt = self.groups.setdefault(name, {})
            for vi, w in weights.items():
                tgt[vi + shift] = w
        for (a, b), w in other.creases.items():
            key = (min(a, b) + shift, max(a, b) + shift)
            self.creases[key] = max(self.creases.get(key, 0.0), w)
        for rname, ids in other.rings.items():
            tag = ring_prefix if ring_prefix is not None else group_prefix
            self.register_ring(f"{tag}{rname}", [i + shift for i in ids])
        return shift

    def transform(self, m: Matrix) -> None:
        """Apply a 4x4 matrix; reverses winding when det < 0 (mirrors)."""
        rows = [[m[i][j] for j in range(3)] for i in range(3)]
        det = (rows[0][0] * (rows[1][1] * rows[2][2] - rows[1][2] * rows[2][1])
               - rows[0][1] * (rows[1][0] * rows[2][2] - rows[1][2] * rows[2][0])
               + rows[0][2] * (rows[1][0] * rows[2][1] - rows[1][1] * rows[2][0]))
        flip = det < 0.0
        self.verts = [m @ v for v in self.verts]
        if flip:
            self.flip_winding()

    def flip_winding(self) -> None:
        self.faces = [tuple(reversed(f)) for f in self.faces]

    def mirror_merge(self, plane: str = "X", *, group_suffix_map=("L", "R"),
                     ring: str | None = None) -> None:
        """Mirror the whole builder across an axis and merge it in.

        For groups/rings named ``...L`` the mirror renames to ``...R`` (and
        vice-versa) so bilateral parts stay addressable.
        """
        idx = {"X": 0, "Y": 1, "Z": 2}[plane.upper()]
        neg = Matrix.Diagonal(tuple(-1.0 if i == idx else 1.0 for i in range(3))).to_4x4()
        other = MeshBuilder(self.name + ".mirror")
        other.verts = [neg @ v for v in self.verts]
        other.regions = list(self.regions)
        other.uvs = [(1.0 - u, v) for (u, v) in self.uvs]
        other.faces = [tuple(reversed(f)) for f in self.faces]  # keeps normals out
        other.face_mat = list(self.face_mat)
        for m in self.materials:
            other.materials.append(m)
        for gname, w in self.groups.items():
            other.groups[gname] = dict(w)
        for k, w in self.creases.items():
            other.creases[k] = w
        for rname, ids in self.rings.items():
            other.rings[rname] = list(ids)
        # swap L/R tags on the copy so bilateral parts stay addressable
        renamed: dict[str, dict[int, float]] = {}
        for gname, w in other.groups.items():
            if gname.endswith(".L"):
                renamed[gname[:-2] + ".R"] = w
            else:
                renamed[gname] = w
        other.groups = renamed
        rr: dict[str, list[int]] = {}
        for rname, ids in other.rings.items():
            rr[rname[:-2] + ".R" if rname.endswith(".L") else rname] = ids
        other.rings = rr
        self.merge(other, group_prefix="", ring_prefix=ring)

    # -- analysis -----------------------------------------------------------------
    def bounds(self) -> tuple[Vector, Vector]:
        if not self.verts:
            z = Vector((0, 0, 0))
            return z, z
        lo = [1e9, 1e9, 1e9]
        hi = [-1e9, -1e9, -1e9]
        for v in self.verts:
            for i in range(3):
                lo[i] = min(lo[i], v[i])
                hi[i] = max(hi[i], v[i])
        return Vector(lo), Vector(hi)

    def stats(self) -> dict:
        quads = sum(1 for f in self.faces if len(f) == 4)
        tris = sum(1 for f in self.faces if len(f) == 3)
        other = len(self.faces) - quads - tris
        n = len(self.verts)
        degenerate = sum(1 for f in self.faces if len(set(f)) != len(f))
        return {
            "verts": n, "faces": len(self.faces), "quads": quads, "tris": tris,
            "ngons": other, "degenerate": degenerate,
            "quad_ratio": quads / max(1, len(self.faces)),
            "groups": len(self.groups), "materials": list(self.materials),
            "creases": len(self.creases),
            "bounds": tuple(round(x, 3) for x in self.bounds()[0].to_tuple()),
            "bounds_hi": tuple(round(x, 3) for x in self.bounds()[1].to_tuple()),
        }

    def face_normal(self, fi: int) -> Vector:
        f = self.faces[fi]
        a, b, c = self.verts[f[0]], self.verts[f[1]], self.verts[f[2]]
        n = (b - a).cross(c - a)
        return n.normalized() if n.length_squared > 1e-12 else Vector((0, 0, 1))

    def face_centre(self, fi: int) -> Vector:
        c = Vector((0.0, 0.0, 0.0))
        for i in self.faces[fi]:
            c += self.verts[i]
        return c / len(self.faces[fi])

    # -- bmesh -------------------------------------------------------------------
    def to_bmesh(self, weld: float = 1e-5):
        """Build a bmesh with UVs, region attribute, crease edge attribute.

        IMPORTANT: all custom-data layers are created *before* geometry —
        creating a layer mid-edit invalidates BMVert references.
        """
        B = _bmesh()
        bm = B.new()
        uv_l = bm.loops.layers.uv.new("UVMap")
        reg_l = bm.verts.layers.float.new("hcg_region")
        cre_l = bm.edges.layers.float.new("crease_edge")
        verts = [bm.verts.new(tuple(v)) for v in self.verts]
        for v, reg in zip(verts, self.regions):
            v[reg_l] = _region_code(reg)
        seen: set[tuple[int, ...]] = set()
        for loop, mat in zip(self.faces, self.face_mat):
            key = tuple(sorted(loop))
            if len(loop) < 3 or key in seen or len(set(loop)) != len(loop):
                continue
            seen.add(key)
            try:
                f = bm.faces.new([verts[i] for i in loop])
            except ValueError:
                continue
            for lv in f.loops:
                lv[uv_l].uv = (self.uvs[lv.vert.index][0], self.uvs[lv.vert.index][1])
            if mat is not None and mat in self.materials:
                f.material_index = self.materials.index(mat)
        # creases
        bm.edges.ensure_lookup_table()
        edge_by_pair = {}
        for e in bm.edges:
            i, j = e.verts[0].index, e.verts[1].index
            edge_by_pair[(min(i, j), max(i, j))] = e
        for (a, b), w in self.creases.items():
            e = edge_by_pair.get((min(a, b), max(a, b)))
            if e is not None:
                e[cre_l] = max(e[cre_l], w)
        if weld and weld > 0.0:
            try:
                B.ops.remove_doubles(bm, verts=bm.verts[:], dist=weld)
            except Exception:
                pass
        try:
            B.ops.recalc_face_normals(bm, faces=bm.faces[:])
        except Exception:
            pass
        return bm


# ----------------------------------------------------------------------------- bmesh checks
def audit(bm) -> dict:
    """Topology audit: manifoldness, boundaries, valence, quad ratio."""
    B = _bmesh()
    bm.verts.ensure_lookup_table()
    bm.faces.ensure_lookup_table()
    boundary = non_manifold = 0
    for e in bm.edges:
        if e.is_boundary:
            boundary += 1
        elif len(e.link_faces) > 2:
            non_manifold += 1
    irregular = sum(1 for v in bm.verts
                    if not v.is_boundary and len(v.link_faces) not in (4, 3, 5)
                    and len(v.link_faces) > 0)
    quads = sum(1 for f in bm.faces if len(f.verts) == 4)
    tris = sum(1 for f in bm.faces if len(f.verts) == 3)
    ngons = len(bm.faces) - quads - tris
    degenerate = 0
    for f in bm.faces:
        if f.calc_area() < 1e-10:
            degenerate += 1
    return {
        "verts": len(bm.verts), "faces": len(bm.faces), "edges": len(bm.edges),
        "quads": quads, "tris": tris, "ngons": ngons,
        "boundary_edges": boundary, "non_manifold_edges": non_manifold,
        "degenerate_faces": degenerate, "irregular_valence_verts": irregular,
        "quad_ratio": quads / max(1, len(bm.faces)),
        "watertight": boundary == 0 and non_manifold == 0,
    }


def estimate_volume(bm) -> float:
    """Signed tet-sum volume of a bmesh (approximate for closed meshes)."""
    V = Vector
    vol = 0.0
    for f in bm.faces:
        p0 = V(f.verts[0].co)
        for i in range(1, len(f.verts) - 1):
            p1 = V(f.verts[i].co)
            p2 = V(f.verts[i + 1].co)
            vol += p0.dot(p1.cross(p2)) / 6.0
    return abs(vol)


def smooth_relax(bm, iterations: int = 1, factor: float = 0.5,
                 select_pred=None) -> None:
    """Laplacian-style relax over all (or selected) verts.

    Used to relax weld pinches without shrinking features: vertices flagged by
    ``select_pred`` (default: none) stay put.
    """
    B = _bmesh()
    for _ in range(max(1, iterations)):
        moves = []
        for v in bm.verts:
            if select_pred is not None and select_pred(v):
                continue
            nb = v.link_verts
            if len(nb) < 2:
                continue
            avg = V = Vector
            c = V((0.0, 0.0, 0.0))
            for w in nb:
                c += V(w.co)
            c /= len(nb)
            moves.append((v, (V(v.co) - c) * factor))
        for v, d in moves:
            v.co -= d
