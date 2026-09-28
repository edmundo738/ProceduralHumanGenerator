# -*- coding: utf-8 -*-
"""TORSO STUDY 01 — envelope frontal da banda central (busto sem braços/ombros).

A linha média (mid_front) passa ENTRE as mamas e a silhueta da fatia apanha
braços/ombros; este instrumento mede a frente máxima da banda |x|<120 mm por
altura (tronco apenas) e devolve: nível e frente do ápice, underbust, projeção
(ápice−underbust) e saliência vs parede torácica (0.795·S).

Uso: python tools/refstudy/bust_band.py
"""
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from _paths import WORK  # noqa: E402

S = 1700.0
CFG = {"ours": {}, "femalebase": {}, "femalechar": {"flip": True}, "bodytopo": {}}
BT = json.load(open(os.path.join(WORK, "cfg_bodytopo.json")))
DROP = json.load(open(os.path.join(WORK, "drop_ours.json")))


def main():
    print(f"{'fonte':11s} {'ápice z':>8s} {'(S)':>6s} {'frente':>7s} {'underb z':>9s} "
          f"{'underb f':>9s} {'projeção':>9s} {'parede .795S':>13s}")
    for n, c in CFG.items():
        d = np.load(os.path.join(WORK, f"raw_{n}.npz"))
        V = d["V"].copy()
        lab = np.load(os.path.join(WORK, f"lab_{n}.npy"))
        keep = ~np.isin(lab, DROP) if n == "ours" else np.ones(len(lab), bool)
        if n == "bodytopo":
            S_, fl = BT["stature_override"], BT["floor_override"]
        else:
            S_, fl = V[:, 2].max() - V[:, 2].min(), V[:, 2].min()
        V[:, 2] -= fl
        V[:, 0] -= (V[:, 0].max() + V[:, 0].min()) / 2
        V *= 1700.0 / S_
        if c.get("flip"):
            V[:, 1] *= -1
        V[:, 1] -= (V[keep][:, 1].max() + V[keep][:, 1].min()) / 2
        Vv = V[keep]
        zs = np.arange(0.60 * S, 0.82 * S, 5.0)
        env = []
        for z in zs:
            m = (np.abs(Vv[:, 0]) < 120) & (Vv[:, 2] > z - 6) & (Vv[:, 2] < z + 6)
            env.append(Vv[m][:, 1].max() if m.any() else np.nan)
        env = np.array(env)
        ok = np.isfinite(env)
        zs, env = zs[ok], env[ok]
        i_ap = int(np.argmax(env))
        za, fa = zs[i_ap], env[i_ap]
        below = (zs > za - 110) & (zs < za - 15)
        iu = int(np.argmin(np.where(below, env, 1e9)))
        zu, fu = zs[iu], env[iu]
        i_st = int(np.argmin(np.abs(zs - 0.795 * S)))
        fs = env[i_st]
        print(f"{n:11s} {za:8.0f} {za / S:6.3f} {fa:7.1f} {zu:9.0f} {fu:9.1f} "
              f"{fa - fu:9.1f} {fs:13.1f}")
    print("\nprojeção = mama (ápice−underbust); parede = frente a 0.795·S (esterno alto);")
    print("ápio-parede = saliência do busto vs parede torácica.")


if __name__ == "__main__":
    main()
