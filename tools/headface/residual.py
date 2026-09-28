"""Resíduo a explicar pelos campos faciais: alvo facial médio − casca de massas (A2b)."""
import os, sys, json
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, ROOT); sys.path.insert(0, HERE)
os.environ.setdefault("HCG_MATHUTILS", "0")
from human_generator.generators import head_mass as HM  # noqa
from face_target import CENTRE, OUT  # noqa

STEP = 0.5


def grid_dirs(AZ, EL):
    AA, EE = np.meshgrid(np.radians(AZ), np.radians(EL))
    return np.stack([np.cos(EE) * np.sin(AA), np.cos(EE) * np.cos(AA), np.sin(EE)], -1)


def build():
    d = np.load(os.path.join(OUT, "face_target.npz"))
    AZ0, EL0 = d["AZ"], d["EL"]
    k = int(round(STEP / (AZ0[1] - AZ0[0])))
    AZ, EL = AZ0[::k], EL0[::k]
    mean, std = d["mean"][::k, ::k], d["std"][::k, ::k]
    U = grid_dirs(AZ, EL)
    old = os.path.join(OUT, "residual.npz")
    if os.path.exists(old) and np.load(old)["base"].shape == mean.shape and not os.environ.get("REBASE"):
        base = np.load(old)["base"]                    # a casca não mudou: reutiliza
    else:
        base = np.array([[HM.radial_cont_a2(tuple(u)) for u in row] for row in U])
    np.savez_compressed(os.path.join(OUT, "residual.npz"), AZ=AZ, EL=EL, U=U, base=base, mean=mean, std=std)
    return AZ, EL, U, base, mean, std


if __name__ == "__main__":
    AZ, EL, U, base, mean, std = build()
    D = mean - base
    print("residual face |az|<70, el -60..40:", np.nanpercentile(np.abs(D[(np.abs(AZ)[None, :] < 70) & ((EL[:, None] > -60) & (EL[:, None] < 40))]), [50, 90, 99]))
    L = json.load(open(os.path.join(OUT, "face_landmarks.json")))["mean"]
    for k_, p in L.items():
        v = np.array(p) - CENTRE; u = v / np.linalg.norm(v)
        print(f"{k_:5s} 100u = X {100*u[0]:6.1f}  Y {100*u[1]:6.1f}  Z {100*u[2]:6.1f}   r {np.linalg.norm(v):6.1f}")
