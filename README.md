# ProceduralHumanGenerator

Parametric, deterministic human character generation for Blender, written in Python.
Geometry is **generated from anatomy** (anthropometric landmarks → quad-loft stations →
analytic deformation fields), not morphed from a fixed base mesh: the same spec always
produces the same topology, and different specs produce different *anatomy*, not just
displaced vertices.

Validated headlessly against the `bpy` 5.0.1 wheel (target: Blender 4.2 → 5.2).

---

## Quick start (public API — contract `hcg-charapi/1.0.0`)

```python
import human_generator as hcg

# geometry + procedural hair only — pure Python, no Blender needed
build = hcg.build_character("realistic_female", seed=42)
print(build.verts, build.faces, build.digest, build.numerics)

# full generation inside Blender: objects, materials, audit, .blend + JSON report
res = hcg.generate_character("cyber_angel", seed=7, out_dir="out/my_character")
print(res.objects, res.audit, res.files["blend"])
```

Accepted inputs: a `CharacterSpec`, a preset name (`realistic_female`, `cyber_angel`,
`neon_idol`), or `None` (default). Explicit `seed=`, `preset=`, and
`overrides={"face.nose_tip_projection": 1.7, ...}` are validated — unknown groups,
fields or seeds raise instead of being silently ignored.

## Running headless

```bash
python tools/headless_blender.py build                                    # one-time: stub missing X11/GL libs
python tools/headless_blender.py run tools/dev_smoke.py 42 realistic_female
```

Renders land in `out/`. Budget ≈ 160 s for both views with procedural materials
(Cycles CPU, 480×600 @ 16 spp).

## Acceptance test (S0)

```bash
python tests/test_s0_public_api.py                                        # geometry, digests, error contract
python tools/headless_blender.py run tests/test_s0_public_api.py -- --bpy  # objects, materials, audit, .blend
```

The test pins the spec fingerprint, the mesh digest (per numerics regime), the vertex/face
counts and the audit numbers; if geometry changes, it fails until a human updates the pin
on purpose.

## Architecture

```
CharacterSpec ──► Anatomy ──► generators (body/head/eyes/mouth/hands/feet/digits/hair)
   presets/*.json   landmarks     │
   seed, fingerprint  z-tables    ├── core/topology  MeshBuilder: loft, cap_pole, patch_grid,
                                  │                  mirror_merge, regions, creases, UVs, audit
                                  ├── core/field     DeformStack: gauss/socket/ridge/capsule/…
                                  └── core/object    bpy plumbing: mesh, slots, vertex groups
pipeline/assemble ──► BuildResult (pure) / GenerationResult (Blender + files on disk)
materials/skin ──► procedural PBR node graphs (skin, eye, iris, cornea, hair, enamel, …)
```

## Status (honest)

| Area | State |
|---|---|
| Body, head, face features, hands/feet/digits, eyes, mouth (teeth/gums/tongue), hair | implemented; built and rendered headless |
| Public API, determinism pins, error contract, audit report | implemented + tested (S0, 2026-09-24) |
| Extremes: constant topology (5 821 v) across parameter extremes and all presets | measured |
| Rig / skin weights, shape keys, expression layer, glTF/GLB export, quality passes, UV unwrap beyond per-face rects | **not implemented** |
| Visual realism of fringe hair, mouth corners, eyelids, ears | known defects, see below |

## Known issues (measured, not fixed)

1. **36 non-manifold edges + 2 loose edges** after the weld, introduced by the mouth
   clamp (projection collapsing distinct tooth vertices) and a degenerate eye-pole ring.
   Root-caused with attribution A/B — `docs/RESEARCH_GATE_02.md`. Scheduled: S2.
2. **Numerics regimes**: `core/_math.py` uses `mathutils` (float32) when `bpy` is imported
   *before* the package, and a pure-python stand-in (float64) otherwise. The same
   spec+seed therefore has two legitimate digests. Results carry `numerics` and the
   Blender regime raises a warning; unifying this is an S1/S2 decision.
3. Visual: hair fringe covers the eyes at default length; corner tooth tips can peek past
   the lip band; eyelids read as pale caps; ear patches show shading artifacts.
4. `fbm3`/`ridged3` normalisation is a no-op (`... and 1.0`), so fBm is 1.75× oversized —
   currently latent (no caller uses `DeformStack.noise` yet).

## Docs

- `docs/RESEARCH_GATE_01.md` — checkpoint state + external study (MPFB2, 2026-human-body-generator)
- `docs/RESEARCH_GATE_02.md` — second audit: root causes, measurements, retractions
- `docs/RESEARCH_COMPARATIVE_01.md` — deep comparative investigation + slice plan S1–S6
