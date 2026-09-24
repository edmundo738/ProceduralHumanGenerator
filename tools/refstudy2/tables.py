"""Tabelas de descritores de forma por cota (REF STUDY 02)."""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "refstudy"))
import numpy as np
from _paths import WORK
D = json.load(open(os.path.join(WORK, "shape.json")))
VALID_W = {"femalebase": lambda z: z < 0.74 * 1700, "femalechar": lambda z: z < 0.74 * 1700,
           "bodytopo": lambda z: not (0.47 * 1700 <= z <= 0.64 * 1700), "ours": lambda z: True}
def at(n, f):
    rows = D[n]; return min(rows, key=lambda r: abs(r["z"] - f * 1700))
levels = [0.78, 0.74, 0.72, 0.69, 0.66, 0.635, 0.60, 0.57, 0.545, 0.52]
print("valores por cota (— = inválido por braços/mãos em T/A)")
for key, fmt, needs_w in [("fill", "{:.2f}", True), ("back_groove", "{:.0f}", False), ("back_max_absx", "{:.0f}", True),
                          ("front_ext/back_ext", "{:.2f}", False), ("front_groove", "{:.0f}", True), ("width", "{:.0f}", True), ("depth", "{:.0f}", False)]:
    print(f"\n{key}")
    print("  " + " ".join(f"{f:>7.3f}" for f in levels))
    for n in D:
        cells = []
        for f in levels:
            r = at(n, f)
            if needs_w and not VALID_W[n](r["z"]): cells.append("      —"); continue
            v = r["front_ext"] / r["back_ext"] if key == "front_ext/back_ext" else r[key]
            cells.append(f"{fmt.format(v):>7s}")
        print(f"  {' '.join(cells)}  {n}")
