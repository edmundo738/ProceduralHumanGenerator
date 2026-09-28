import os, sys, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from look import panel
from mapmesh import map_mesh
from face_target import OUT
import plot_res
d = np.load(os.path.join(OUT, "residual.npz")); F = np.load(os.path.join(OUT, "fitted_F.npy"))
tag = sys.argv[1]
Dl = np.load(os.path.join(OUT, "D_low.npy"))
maps = {"alvo (média refs)": d["mean"], "casca + campos": d["base"] + F, "alvo sem baixa freq. (casca + detalhe alvo)": d["mean"] - Dl}
def loader(nm):
    R = maps[nm].copy(); R[:40] = np.nan          # corta o pescoço (el < −60)
    return map_mesh(R, d["AZ"], d["EL"])
panel(list(maps), os.path.join(OUT, f"fit_{tag}.png"), loader=loader)
plot_res.show(d["mean"] - d["base"] - Dl, d["U"], os.path.join(OUT, f"res_{tag}.png"), "", fitted=F)
