"""Avaliação do pré-registo H7a × H4a (docs/PREREG_H7A_H4A.md).

Modo "one" (subprocesso, HCG_REFSTUDY_WORK=out/prereg/Ev): métricas congeladas de
``prereg_metrics.metrics`` em DOIS referenciais (REF01 = centrado pela caixa;
BRUTO = coordenadas do gerador, só chão+escala) → WORK/prereg_metrics.json.

Modo "all": prepara cada WORK (componentes, lista de peças a excluir, perfis das refs),
corre o instrumento REF01 sem alterações (measure.py ours + metrics.py), o modo "one",
as verificações de invariância e a avaliação dos critérios congelados.

Uso: python tools/refstudy2/prereg_eval.py all
"""
import json, os, shutil, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
PY = sys.executable
RUNS = ["E0", "E1", "E2", "E3"]
CTRL = os.path.join(ROOT, "out", "rs2")
BASE = os.path.join(ROOT, "out", "prereg")


def one():
    sys.path.insert(0, os.path.join(HERE, "..", "refstudy")); sys.path.insert(0, HERE)
    import numpy as np
    import measure, shape, prereg_metrics as PM
    from _paths import WORK
    V, T, lab = shape.normalised("ours", shape.MODELS["ours"])
    opt = dict(shape.MODELS["ours"]); opt.pop("drop")
    _, T_full, _ = shape.normalised("ours", opt)
    m_ref = PM.metrics(V, T, lab, T_full=T_full)
    # referencial BRUTO: coordenadas do gerador; só chão e escala (sem centrar x/y)
    Vr, Tr, labr = measure.prep("ours")
    Vr = Vr.copy(); zmin, zmax = Vr[:, 2].min(), Vr[:, 2].max()
    Vr[:, 2] -= zmin; Vr *= 1700.0 / (zmax - zmin)
    drop = json.load(open(os.path.join(WORK, "drop_ours.json")))
    keep = ~np.isin(labr, drop); Tk = Tr[keep[Tr[:, 0]]]
    m_raw = PM.metrics(Vr, Tk, labr, T_full=Tr)
    g = measure.slice_grid(Vr, Tk, labr, 0.12 * 1700, (-320, 320), (-260, 260))
    iy, ix = np.nonzero(g)
    shank_y = float((-260 + (iy + .5) * 2.0).mean())
    json.dump(dict(ref01_frame=m_ref, raw_frame=m_raw, raw_zmin=float(zmin), raw_zmax=float(zmax),
                   raw_shank_y=shank_y), open(os.path.join(WORK, "prereg_metrics.json"), "w"), indent=1)


def prepare(v):
    import numpy as np
    sys.path.insert(0, os.path.join(HERE, "..", "refstudy"))
    import geom
    W = os.path.join(BASE, v)
    for f in ("ansur_ratios.json", "cfg_bodytopo.json", "prof_femalebase.json", "prof_femalechar.json", "prof_bodytopo.json"):
        shutil.copy(os.path.join(CTRL, f), W)
    d = np.load(os.path.join(W, "raw_ours.npz")); V, T = d["V"], d["T"]
    lab = geom.components(V, T); np.save(os.path.join(W, "lab_ours.npy"), lab)
    drop = [int(c) for c in range(lab.max() + 1)          # regra IDÊNTICA a tools/refstudy/comps.py
            if np.abs(V[lab == c][:, 0]).min() > 0.07 and V[lab == c][:, 2].min() > 0.6 and V[lab == c][:, 2].max() < 1.45]
    json.dump(drop, open(os.path.join(W, "drop_ours.json"), "w"))
    env = dict(os.environ, HCG_REFSTUDY_WORK=W)
    rs = os.path.join(ROOT, "tools", "refstudy")
    subprocess.run([PY, os.path.join(rs, "measure.py"), "ours", json.dumps({"drop_labels": drop})],
                   env=env, cwd=ROOT, check=True, capture_output=True)
    out = subprocess.run([PY, os.path.join(rs, "metrics.py")], env=env, cwd=ROOT, check=True,
                         capture_output=True, text=True).stdout
    open(os.path.join(W, "metrics.txt"), "w").write(out)
    subprocess.run([PY, __file__, "one"], env=env, cwd=ROOT, check=True)
    return lab, drop


def flatten(d, p=""):
    out = {}
    if isinstance(d, dict):
        for k, v in d.items():
            out.update(flatten(v, f"{p}.{k}" if p else str(k)))
    elif isinstance(d, (list, tuple)):
        for i, v in enumerate(d):
            out.update(flatten(v, f"{p}[{i}]"))
    else:
        out[p] = d
    return out


def invariance(labs):
    import numpy as np
    res = {}
    c0 = np.load(os.path.join(BASE, "E0", "cage_ours.npz"))["V"]
    r0 = np.load(os.path.join(BASE, "E0", "raw_ours.npz"))["V"]
    lab0 = labs["E0"]
    # peça do tronco = componente que contém o vértice mais próximo de (0, 0, 1.2)
    trunk = int(lab0[np.argmin(np.linalg.norm(r0 - np.array([0, 0, 1.2]), axis=1))])
    Z = {"deltoid_line": 1.3804, "jugulum": 1.3515, "bust": 1.2954, "inframammary": 1.224, "waist": 1.0795,
         "navel": 1.0234, "hip_flare": 0.9622, "hip": 0.901, "crotch": 0.833}
    for v in RUNS[1:]:
        rv = np.load(os.path.join(BASE, v, "raw_ours.npz"))["V"]
        cv = np.load(os.path.join(BASE, v, "cage_ours.npz"))["V"]
        same_labels = bool(np.array_equal(labs[v], lab0))
        dm = np.linalg.norm(rv - r0, axis=1)
        per = {}
        for c in range(lab0.max() + 1):
            m = lab0 == c
            per[c] = float(dm[m].max())
        changed = {c: round(x * 1000, 3) for c, x in per.items() if x > 0}
        # cage: tronco por estação mais próxima (pela cota no E0); só vértices do tronco
        # (a cage exportada não tem os rótulos: usa-se a caixa do tronco |x| < 0.25, 0.80 < z < 1.40)
        dc = np.linalg.norm(cv - c0, axis=1)
        tm = (np.abs(c0[:, 0]) < 0.25) & (c0[:, 2] > 0.80) & (c0[:, 2] < 1.40)
        near = {}
        for i in np.nonzero(tm & (dc > 0))[0]:
            k = min(Z, key=lambda s: abs(Z[s] - c0[i, 2]))
            near[k] = max(near.get(k, 0.0), float(dc[i]))
        out_box = float(dc[~tm].max()) if (~tm).any() else 0.0
        res[v] = dict(same_component_labels=same_labels, trunk_component=trunk,
                      components_changed_mm=changed, n_components=int(lab0.max() + 1),
                      cage_changed_by_station_mm={k: round(x * 1000, 3) for k, x in near.items()},
                      cage_max_change_outside_trunk_box_mm=round(out_box * 1000, 4),
                      raw_max_change_non_trunk_mm=round(max([x for c, x in per.items() if c != trunk] + [0]) * 1000, 4))
    return res


def contracts():
    R0 = flatten(json.load(open(os.path.join(BASE, "E0", "integration_report.json"))))
    out = {}
    for v in RUNS[1:]:
        Rv = flatten(json.load(open(os.path.join(BASE, v, "integration_report.json"))))
        diff = {}
        for k in sorted(set(R0) | set(Rv)):
            a, b = R0.get(k), Rv.get(k)
            if a != b:
                if isinstance(a, (int, float)) and isinstance(b, (int, float)) and abs(a - b) < 1e-9:
                    continue
                diff[k] = (a, b)
        out[v] = diff
    return out


def main():
    labs = {}
    for v in RUNS:
        labs[v], _ = prepare(v)
        print("medido", v, flush=True)
    M = {v: json.load(open(os.path.join(BASE, v, "prereg_metrics.json"))) for v in RUNS}
    R = {v: json.load(open(os.path.join(BASE, v, "metrics.json")))["ours"] for v in RUNS}
    inv = invariance(labs)
    con = contracts()
    json.dump(dict(metrics=M, ref01=R, invariance=inv, contracts=con), open(os.path.join(BASE, "results.json"), "w"),
              indent=1, default=str)
    print("ok → out/prereg/results.json")


if __name__ == "__main__":
    one() if sys.argv[1] == "one" else main()
