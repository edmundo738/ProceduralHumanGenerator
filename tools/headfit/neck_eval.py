"""NECK N1 — avaliação contra docs/NECK_N1_PREREG.md (N-C1 perfil; risco N-C5 transição)."""
import os, sys, json
import numpy as np
HERE = os.path.dirname(__file__); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, "..", "headstudy"))
import neck_study as N   # noqa: E402
import target as TG      # noqa: E402

ZC = (-10, -15, -20, -25, -30, -35)
TOL = 2.0


def main():
    prof = json.load(open(os.path.join(TG.OUT, "neck_profile.json")))
    per = prof["per_ref"]
    lines, res = [], {}
    for nm in ("oursA2", "oursN1"):
        W, T = N.frame(nm)
        ok = 0; rows = []
        for z in ZC:
            o = N.stats(W, T, z)
            refs = [per[r][str(z)] for r in N.REFS]
            marks = []
            for j in range(3):
                lo = min(r[j] for r in refs) - TOL; hi = max(r[j] for r in refs) + TOL
                good = lo <= o[j] <= hi; ok += good; marks.append("✓" if good else "✗")
            rows.append(f"  z{z:4d}: w {o[0]:6.1f}{marks[0]} frente {o[1]:6.1f}{marks[1]} trás {o[2]:7.1f}{marks[2]}"
                        f"   refs w[{min(r[0] for r in refs):.0f},{max(r[0] for r in refs):.0f}] f[{min(r[1] for r in refs):.0f},{max(r[1] for r in refs):.0f}] t[{min(r[2] for r in refs):.0f},{max(r[2] for r in refs):.0f}]")
        # N-C5: declive da frente (mm/mm) entre z −30 e −60 (transição p/ tórax)
        fr = {z: N.stats(W, T, z)[1] for z in range(-30, -66, -5)}
        slopes = [abs(fr[z - 5] - fr[z]) / 5.0 for z in range(-30, -61, -5)]
        res[nm] = {"N_C1_in_range": ok, "front_slope_max": max(slopes), "front": fr}
        lines.append(f"{nm}: N-C1 {ok}/18 dentro (tol {TOL} mm) · declive máx. da frente z −30…−65: {max(slopes):.2f} mm/mm")
        lines += rows
        lines.append("  frente z −30…−65: " + " ".join(f"{fr[z]:.0f}" for z in sorted(fr, reverse=True)))
    txt = "\n".join(lines); print(txt)
    doc = os.path.join(HERE, "..", "..", "docs", "head_phaseA")
    open(os.path.join(doc, "neck_eval_N1.txt"), "w").write(txt + "\n")
    json.dump(res, open(os.path.join(doc, "neck_eval_N1.json"), "w"), indent=1, default=float)


if __name__ == "__main__":
    main()
