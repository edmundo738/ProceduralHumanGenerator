"""FASE A — ajuste de R1 (massas) ao alvo estatístico e às refs individuais,
com o MESMO domínio, alvo e relatório do teste de capacidade de R0."""
import os
import sys
import json
import numpy as np
from scipy.optimize import least_squares

HERE = os.path.dirname(__file__)
sys.path.insert(0, HERE)
import target as TG        # noqa: E402
import capacity as CP      # noqa: E402
import massmodel as MM     # noqa: E402

H = TG.H


def bounds():
    lo, hi = [], []
    for n in MM.NAMES:
        k = n.split(".")[-1]
        if k in ("e", "n"):
            lo.append(1.6); hi.append(6.0)
        elif k == "k":
            lo.append(0.5); hi.append(15.0)
        elif k in ("cy", "cz"):
            lo.append(-160.0); hi.append(240.0)
        else:
            lo.append(4.0); hi.append(160.0)
    return np.array(lo), np.array(hi)


def fit(tgt, dom, TH, PH, p0, sub=2, nfev=300):
    U = TG.dirs(TH, PH)
    sl = (slice(None, None, sub), slice(None, None, sub))
    Us, ts, ds, ws = U[sl][dom[sl]], tgt[sl][dom[sl]], None, np.sqrt(np.sin(TH[sl][dom[sl]]))

    def resid(p):
        r = MM.radial(p, TG.CENTRE, Us)
        e = np.where(np.isfinite(r), r - ts, 30.0)
        return e * ws
    lo, hi = bounds()
    p0 = np.clip(p0, lo + 1e-6, hi - 1e-6)
    r = least_squares(resid, p0, bounds=(lo, hi), x_scale="jac", diff_step=1e-3, max_nfev=nfev)
    return r.x


def points_of(p, n=60):
    U = CP.cube_dirs(n)
    r = MM.radial(p, TG.CENTRE, U)
    ok = np.isfinite(r)
    return TG.CENTRE + U[ok] * r[ok, None]


def report(tag, p, TH, PH, tgt, dom):
    U = TG.dirs(TH, PH)
    R = MM.radial(p, TG.CENTRE, U.reshape(-1, 3)).reshape(TH.shape)
    e = R - tgt
    out = {"rms": float(np.sqrt(np.nanmean(e[dom] ** 2))), "max": float(np.nanmax(np.abs(e[dom]))),
           "p95": float(np.nanpercentile(np.abs(e[dom]), 95))}
    for k, m in CP.region_masks(TH, PH).items():
        mm = m & dom
        out[k] = float(np.sqrt(np.nanmean(e[mm] ** 2))) if mm.any() else None
    print(f"{tag:28s} RMS {out['rms']:.2f}  p95 {out['p95']:.1f}  max {out['max']:.1f}  |  " +
          "  ".join(f"{k} {v:.1f}" for k, v in out.items() if k not in ("rms", "max", "p95") and v is not None),
          flush=True)
    return out, e


if __name__ == "__main__":
    L = 16
    TH, PH, tgt, dom, d = CP.load_target(L)
    res = {}
    p = fit(tgt, dom, TH, PH, MM.P0)
    out, e = report("R1 ajustado ao ALVO médio", p, TH, PH, tgt, dom)
    res["R1_mean"] = out
    res["R1_mean_params"] = dict(zip(MM.NAMES, map(float, p)))
    res["R1_mean_dims"] = CP.dims_of_points(points_of(p))
    print("   dims", {k: round(v, 1) for k, v in res["R1_mean_dims"].items()})
    np.save(os.path.join(TG.OUT, "R1_mean_params.npy"), p)
    np.save(os.path.join(TG.OUT, "R1_err.npy"), e)
    for n in TG.TARGET_SOURCES:
        tn = TG.sh_eval(d[f"{n}_c{L}"], TH, PH, L)
        domn = d[f"{n}_valid"] & dom
        pn = fit(tn, domn, TH, PH, p, nfev=200)
        o, _ = report(f"  R1 → {n}", pn, TH, PH, tn, domn)
        res[f"R1_{n}"] = o
        res[f"R1_{n}_params"] = dict(zip(MM.NAMES, map(float, pn)))
    # dims das refs (mesmo instrumento, pontos do mapa radial SH)
    for n in TG.TARGET_SOURCES:
        U = TG.dirs(TH, PH)
        Rn = TG.sh_eval(d[f"{n}_c{L}"], TH, PH, L)
        P = (TG.CENTRE + U * Rn[..., None])[d[f"{n}_valid"]]
        res[f"dims_{n}"] = CP.dims_of_points(P)
        print(f"   dims {n}", {k: round(v, 1) for k, v in res[f'dims_{n}'].items()})
    json.dump(res, open(os.path.join(TG.OUT, "capacity_R1.json"), "w"), indent=1)
