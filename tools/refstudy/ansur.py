"""Passo 0: razões ANSUR II (mulheres, n=1986) por estatura -> WORK/ansur_ratios.json.
CSV público (DCPH-A, 'ANSUR II FEMALE Public.csv'); caminho em HCG_ANSUR_CSV."""
import os, sys, csv, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from _paths import WORK
rows = list(csv.DictReader(open(os.environ.get("HCG_ANSUR_CSV", f"{WORK}/ansur_f.csv"), encoding="latin-1")))
num = {k for k in rows[0] if k not in ("SubjectId","Gender","Date","Installation","Component","Branch","PrimaryMOS","SubjectsBirthLocation","Ethnicity","WritingPreference","SubjectNumericRace")}
A = {k: np.array([float(r[k]) for r in rows]) for k in num}
S = A["stature"]; black = A["DODRace"] == 2
out = {"n": len(S), "n_black": int(black.sum()), "stature_mean": S.mean(), "ratios": {}}
for k in sorted(num - {"DODRace","Age","Heightin","Weightlbs","weightkg","stature"}):
    r = A[k] / S
    out["ratios"][k] = dict(mm=A[k].mean(), r=r.mean(), sd=r.std(), p5=np.percentile(r,5), p95=np.percentile(r,95), r_black=r[black].mean())
for a, b in [("chestdepth","chestbreadth"),("waistdepth","waistbreadth"),("buttockdepth","hipbreadth"),("waistbreadth","hipbreadth"),("chestbreadth","hipbreadth"),("waistcircumference","buttockcircumference"),("biacromialbreadth","hipbreadth"),("bideltoidbreadth","hipbreadth")]:
    q = A[a] / A[b]
    out["ratios"][f"{a}/{b}"] = dict(r=q.mean(), sd=q.std(), p5=np.percentile(q,5), p95=np.percentile(q,95), r_black=q[black].mean())
json.dump(out, open(f"{WORK}/ansur_ratios.json", "w"), indent=1, default=float)
print("ANSUR n", len(S), "->", f"{WORK}/ansur_ratios.json")
