"""NECK N1 — perfil do pescoço superior nas refs (referencial da cabeça, sem recorte).

z = mm abaixo/acima do mentón 45° (mm@H226), y relativo ao centro g–op.
Para cada cota: meia-largura máxima da componente central (|x| < 0.62·H, sem
braços), frente e trás na linha média (|x| < 8).  Saída: out/headfit/neck_profile.json
"""
import os, sys, json
import numpy as np
HERE = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(HERE, "..", "headstudy")); sys.path.insert(0, HERE)
import common as C   # noqa: E402
import target as TG  # noqa: E402
geom = C.geom
REFS = ("femalebase", "bodytopo", "femalechar")
ZS = list(range(-5, -126, -5))


def frame(nm):
    V, T, fs, fi = C.load_raw(nm, "smooth")
    _, _, _, _, info = C.normalise(nm)
    s = info["scale"]
    W = V.copy(); W[:, 2] = (V[:, 2] - info["z_menton_src"]) * s; W[:, 0] *= s; W[:, 1] = V[:, 1] * s - info["y0_mm_before"]
    return W, T


def stats(W, T, z, xl=0.62 * C.H_MM):
    S = np.asarray(geom.slice_segments(W, T, z)).reshape(-1, 2)
    if not len(S):
        return None
    S = S[np.abs(S[:, 0]) < xl]
    mid = S[np.abs(S[:, 0]) < 8]
    if not len(mid):
        return None
    return [float(np.abs(S[:, 0]).max()), float(mid[:, 1].max()), float(mid[:, 1].min())]


def main():
    out = {}
    for nm in REFS:
        W, T = frame(nm)
        out[nm] = {z: stats(W, T, z) for z in ZS}
    mean = {}
    for z in ZS:
        v = [out[n][z] for n in REFS if out[n][z]]
        mean[z] = [float(x) for x in np.mean(v, 0)] + [float(np.std([a[0] for a in v]))]
    print("  z  | " + " | ".join(f"{n:^21s}" for n in REFS) + " | média  w   frente   trás (sd w)")
    for z in ZS:
        print(f"{z:4d} | " + " | ".join(f"{out[n][z][0]:6.1f} {out[n][z][1]:6.1f} {out[n][z][2]:7.1f}" if out[n][z] else f"{'—':^21s}" for n in REFS)
              + f" | {mean[z][0]:6.1f} {mean[z][1]:6.1f} {mean[z][2]:7.1f} ({mean[z][3]:4.1f})")
    json.dump({"per_ref": {n: {str(z): v for z, v in d.items()} for n, d in out.items()},
               "mean": {str(z): v for z, v in mean.items()}}, open(os.path.join(TG.OUT, "neck_profile.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
