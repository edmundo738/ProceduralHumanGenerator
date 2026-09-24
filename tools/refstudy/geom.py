import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _paths import WORK  # noqa: E402
import numpy as np
def components(V, T):
    n = len(V); p = np.arange(n)
    def find(a):
        while p[a] != a:
            p[a] = p[p[a]]; a = p[a]
        return a
    for a, b in np.vstack([T[:, [0, 1]], T[:, [1, 2]]]):
        ra, rb = find(a), find(b)
        if ra != rb: p[ra] = rb
    roots = np.array([find(i) for i in range(n)])
    _, lab = np.unique(roots, return_inverse=True)
    return lab            # per-vertex label

def slice_segments(V, T, z0):
    z = V[T][:, :, 2] - z0
    s = np.sign(z); s[s == 0] = 1e-9
    m = ~((s > 0).all(1) | (s < 0).all(1))
    P = V[T[m]]; zz = z[m]
    segs = []
    for tri, zt in zip(P, zz):
        pts = []
        for i, j in ((0, 1), (1, 2), (2, 0)):
            if (zt[i] > 0) != (zt[j] > 0):
                t = zt[i] / (zt[i] - zt[j]); pts.append(tri[i] + t * (tri[j] - tri[i]))
        if len(pts) == 2: segs.append((pts[0][:2], pts[1][:2]))
    return np.array(segs)          # (k,2,2)

def fill(segs, x0, y0, res, nx, ny):
    """even-odd scanline fill of one closed shell's section."""
    g = np.zeros((ny, nx), bool)
    if len(segs) == 0: return g
    ys = y0 + (np.arange(ny) + 0.5) * res
    a, b = segs[:, 0], segs[:, 1]
    for r, y in enumerate(ys):
        c = (a[:, 1] > y) != (b[:, 1] > y)
        if not c.any(): continue
        t = (y - a[c, 1]) / (b[c, 1] - a[c, 1]); xs = np.sort(a[c, 0] + t * (b[c, 0] - a[c, 0]))
        for k in range(0, len(xs) - 1, 2):
            i0 = int(np.ceil((xs[k] - x0) / res - 0.5)); i1 = int(np.floor((xs[k + 1] - x0) / res - 0.5))
            if i1 >= i0: g[r, max(i0, 0):min(i1 + 1, nx)] = True
    return g
