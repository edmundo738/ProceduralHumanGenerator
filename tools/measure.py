# -*- coding: utf-8 -*-
"""Medições reprodutíveis do gerador (S2/S3) — correr com ``headless_blender.py``.

Uso:
    python tools/headless_blender.py run tools/measure.py pins
    python tools/headless_blender.py run tools/measure.py audit
    HCG_MATHUTILS=0 python tools/headless_blender.py run tools/measure.py pins

Motivo: as medições viviam em scripts descartáveis em ``/tmp``, que
desapareceram com o re-provisionamento do sandbox (limitação de ambiente
declarada).  Aqui ficam versionadas, com o regime numérico impresso em cada
saída — todo o número citado em documentação tem de poder ser reproduzido por
este ficheiro.

``pins``  — contagens, digests, fingerprint, histograma semântico, stats.
``audit`` — grelha weld×dissolve (critérios S2) + relatório de integração (S3).
"""
from __future__ import annotations

import json
import sys
import time
from collections import Counter

sys.path.insert(0, ".")

import bpy  # noqa: F401  (headless: traz bmesh)

from human_generator import build_character                      # noqa: E402
from human_generator.core._math import numerics_info              # noqa: E402
from human_generator.core.topology import audit                   # noqa: E402
from human_generator.core.integration import integration_report    # noqa: E402
from human_generator.pipeline import assemble                      # noqa: E402
from human_generator.spec import CharacterSpec                     # noqa: E402

PRESETS = ("realistic_female", "cyber_angel", "neon_idol")


def _pins() -> None:
    out: dict = {"numerics": numerics_info(), "seed42": {}, "seed7": {},
                 "regions": {}, "groups": {}, "stats": {}}
    for preset in PRESETS:
        r7 = build_character(preset=preset, seed=7)
        out["seed7"][preset] = [r7.verts, r7.faces, len(r7.hair.strands)]
    r = build_character(preset="realistic_female", seed=42)
    out["seed42"] = {
        "verts": r.verts, "faces": r.faces, "strands": len(r.hair.strands),
        "fingerprint": r.fingerprint, "digest": r.digest,
        "backend": r.numerics.get("backend"), "contract": r.contract_version,
        "warnings": list(r.warnings),
    }
    b = r.builder
    out["regions"] = dict(sorted(Counter(b.regions).items()))
    out["groups"] = {k: len(v) for k, v in sorted(b.groups.items())}
    out["stats"] = {k: v for k, v in b.stats().items() if not isinstance(v, (list, tuple))}
    print("PINS " + json.dumps(out, sort_keys=True, default=str))


def _audit() -> None:
    spec = CharacterSpec.from_preset("realistic_female", seed=42)
    grid = {}
    for weld in (0.0, 1e-5):
        for dissolve in (0.0, 1e-5):
            build = assemble.build_character(spec)
            bm = build.builder.to_bmesh(weld=weld, dissolve=dissolve)
            a = audit(bm)
            grid[f"{weld}/{dissolve}"] = {
                k: (round(v, 6) if isinstance(v, float) else v) for k, v in a.items()
            }
            grid[f"{weld}/{dissolve}"]["op_counts"] = dict(build.builder.op_counts)
            bm.free()
    build = assemble.build_character(spec)
    rep = integration_report(build)
    summary = {
        "components": rep["components"],
        "overlap_edges": rep["overlap_edges"],
        "floating": len(rep["floating"]),
        "boundary_edges": rep["boundary_edges"],
        "mirror": {k: rep["mirror"][k] for k in ("misses", "n", "ratio")},
        "mirror_by_region": rep["mirror"]["misses_by_region"],
        "hausdorff_mm": {k: round(v * 1000, 3)
                         for k, v in sorted(rep["mirror_hausdorff"].items())
                         if k.endswith(".0")},
        "floor": rep["floor"],
        "envelope": rep["envelope"],
        "silhouette": rep["silhouette"],
        "label_edges": rep["label_edges"],
    }
    print("AUDIT " + json.dumps({"numerics": numerics_info(), "grid": grid,
                                 "integration": summary}, sort_keys=True, default=str))


def main() -> int:
    mode = sys.argv[1] if len(sys.argv) > 1 else "pins"
    t0 = time.perf_counter()
    if mode == "pins":
        _pins()
    elif mode == "audit":
        _audit()
    else:
        print(f"unknown mode {mode!r}; use 'pins' or 'audit'", file=sys.stderr)
        return 2
    print(f"# elapsed {time.perf_counter() - t0:.1f}s", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
