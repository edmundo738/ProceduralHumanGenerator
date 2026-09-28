"""Converte um mapa radial (az, el) em malha triangulada (para ver/rasterizar)."""
import numpy as np
from face_target import from_dir


def map_mesh(R, AZ, EL, stride=1):
    R = R[::stride, ::stride]; AZ = AZ[::stride]; EL = EL[::stride]
    AA, EE = np.meshgrid(AZ, EL)
    P = from_dir(AA, EE, np.nan_to_num(R, nan=0.0)).reshape(-1, 3)
    ok = np.isfinite(R).ravel()
    ne, na = R.shape
    i = np.arange(ne - 1)[:, None] * na + np.arange(na - 1)[None, :]
    i = i.ravel()
    q = np.stack([i, i + 1, i + na + 1, i + na], 1)
    good = ok[q].all(1)
    q = q[good]
    T = np.vstack([q[:, [0, 1, 2]], q[:, [0, 2, 3]]])
    return P, T
