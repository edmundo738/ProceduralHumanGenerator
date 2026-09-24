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

## Tests

```bash
python -m pytest tests/ -q                                                 # 76 pure-Python checks, ~20 s (no Blender needed)
python tests/test_s0_public_api.py                                         # acceptance: geometry, digests, error contract
python tools/headless_blender.py run tests/test_s0_public_api.py -- --bpy  # acceptance: objects, materials, audit, .blend
```

The pins (``tests/pins.py``) protect the spec fingerprint, the mesh digest (per numerics
regime), vertex/face counts, the pre-weld audit and the construction guard on collapsed
rings; if geometry changes they fail until a human updates the pin on purpose
(``tests/test_pins.py`` proves the gate really measures geometry). Contracts covered:
``core/_math`` ramps (including reversed edges), ``core/rng`` noise bounds and determinism,
preset documents (``format_version`` + tolerant load), and ``core/topology`` invariants.

### Numerics policy

``core/_math`` uses ``mathutils`` (float32) when ``bpy`` is already imported and a
pure-python stand-in (float64) otherwise — so the same spec+seed has two legitimate mesh
digests. Every result declares its regime (``result.numerics``) and the Blender regime
raises a warning. Set ``HCG_MATHUTILS=0`` to force the float64 backend and make the digest
independent of import order.

### Contract stability

The public character API is versioned (``hcg-charapi/<major>.<minor>.<patch>``, exported as
``hcg.API_CONTRACT_VERSION`` and embedded in every JSON report):

* **major** — a caller-visible behaviour change (accepted inputs, return shape, error types,
  determinism guarantees);
* **minor** — additive change (new optional argument, new field in the report);
* **patch** — fix inside the existing behaviour.

Geometry changes never bump the contract by themselves: they are caught by the pins.

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
| pytest suite: math/RNG/topology/spec contracts, preset `format_version` + tolerant loading, meta-test of the pin gate | implemented + tested (S1, 2026-09-24) |
| Noise contracts `\|fbm3\| ≤ 1`, `\|ridged3\| ≤ 1` (divisor was a no-op) | fixed + tested in S1 (latent: no caller) |
| Construction guard: collapsed rings are detected by name | implemented + tested (S1); clean since S2 (pin deliberately empty) |
| Topology defects (non-manifold, loose edges, degenerate faces/rings, coincident verts) | **fixed at the sources + pinned** (S2, 2026-09-24) — see `docs/S2_TOPOLOGY.md` |
| Semantic label pins (region populations + vertex-group sizes) | implemented + tested (S2) |
| Extremes: constant topology (5 759 v) across parameter extremes and all presets | measured |
| Rig / skin weights, shape keys, expression layer, glTF/GLB export, quality passes, UV unwrap beyond per-face rects | **not implemented** (S3–S5) |
| Visual realism of fringe hair, mouth corners, eyelids, ears | known defects, see below |

## Known issues (measured, not fixed)

1. ~~**36 non-manifold edges + 2 loose edges**, 67 degenerate faces, 2 collapsed eye
   rings~~ — **fixed in S2** at the sources (eye pole/limbus/cornea seam, the head
   sagittal pass and the tooth clamp were absolute projections that collapse ray
   columns; both are now order-preserving / rigid). Result: 0 non-manifold, 0 loose,
   0 degenerate, 0 collapsed rings, 0 coincident vertices, identical in all four
   `weld`/`dissolve` regimes and in both numerics regimes. The weld and the
   `dissolve_degenerate` wash are now provably **no-ops** (0 operations) and stay as
   guards. Full measurement tables: `docs/S2_TOPOLOGY.md`.
2. **Numerics regimes**: `core/_math.py` uses `mathutils` (float32) when `bpy` is imported
   *before* the package, and a pure-python stand-in (float64) otherwise. The same
   spec+seed therefore has two legitimate digests. Results carry `numerics` and the
   Blender regime raises a warning; the policy is CONTROLLED (documented), not yet
   resolved.
3. Visual: hair fringe covers the eyes at default length; corner tooth tips can peek past
   the lip band; eyelids read as pale caps; ear patches show shading artifacts.
4. ~~`fbm3`/`ridged3` normalisation is a no-op~~ — fixed in S1 (divisor = sum of octave
   amplitudes, contracts in `tests/test_rng.py`); it stays latent because nothing calls
   `DeformStack.noise` yet.

## Docs

- `docs/RESEARCH_GATE_01.md` — checkpoint state + external study (MPFB2, 2026-human-body-generator)
- `docs/RESEARCH_GATE_02.md` — second audit: root causes, measurements, retractions
- `docs/RESEARCH_COMPARATIVE_01.md` — deep comparative investigation + slice plan S1–S6
- `docs/S2_TOPOLOGY.md` — S2: root causes, fixes, before/after measurement tables, open items
