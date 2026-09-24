# S2 — topology defects: root causes, fixes, measurements

**Slice S2** of the approved plan (`docs/RESEARCH_COMPARATIVE_01.md` §9).
Method per change: **BASELINE → ALTERAÇÃO → TESTE → MEDIÇÃO → COMPARAÇÃO**.
Every number below was measured in this slice; nothing here is inferred from a
README or from another project.

Instrument: `tools/headless_blender.py` (Blender 5.0.1), preset
`realistic_female`, seed 42, full `build_character` merge.
Two numerics regimes were measured for every headline number:
`mathutils` (float32, bpy imported first) and `pure-python` (float64,
`HCG_MATHUTILS=0`).

---

## 1. Baseline (pre-S2, `aaed798`)

| regime `weld/dissolve` | verts | faces | NM edges | loose | deg faces | quads/tris/ngons | quad_ratio |
|---|---|---|---|---|---|---|---|
| `0 / –` (pure build) | 5821 | 5642 | 0 | 0 | **67** | 4902/740/0 | 0.868841 |
| `0 / 1e-5` | 5749 | 5567 | 0 | **2** | 0 | 4813/744/**10** | 0.864559 |
| `1e-5 / –` (shipped default) | 5695 | 5551 | **36** | **2** | 0 | 4807/744/0 | 0.865970 |
| `1e-5 / 1e-5` | 5695 | 5543 | **36** | **2** | 0 | 4795/738/**10** | 0.865055 |

Definitions (fixed in S2, used everywhere below):

* `quad_ratio = |{f ∈ F : len(f) = 4}| / |F|` over **all** faces of the audited
  mesh (audit key `quad_ratio`). Baseline 0.8688 ⇒ the old "≥ 0.86" target was
  −1.0 percentage point, which is why it is now pinned numerically instead.
* `deg faces` = faces with `calc_area() < 1e-10` (the audit criterion). A
  *different* criterion (min vertex-pair distance < 1e-9) counts 101 on the
  same baseline mesh; the two must never be mixed.
* `NM edges` = edges with > 2 linked faces. `loose edges` = edges with 0 linked
  faces (added to `audit()` in S2 so the criterion is measurable in the API).
* **ngon budget**: ≤ 12 faces that are neither quads nor triangles. This is a
  *working limit*, not a mathematical law: it is the 10 ngons the (measured)
  `dissolve_degenerate` experiment produced on the baseline plus a small margin.
  Angular/sagittal constructions that legitimately need n-gons must raise it
  deliberately and say so here.

## 2. Root causes (each one traced, not guessed)

| # | Defect | Mechanism | Evidence |
|---|---|---|---|
| 1 | 52 of the 67 degenerate faces | `generators/eyes.py`: the latitude loop started at `phi = -π/2`, where `cos(phi) = 6.1e-17`, so **all 13 points of ring 0 are the same point**; `cap_start="pole"` then stacked a second collapsed ring on top (26 coincident verts per eye, 78 pairs per ring) | `rings_degenerate()` = `{"eye.L.0": 78, "eye.R.0": 78}` |
| 2 | limbus pinch | the globe was emitted as **two lofts** (`rings[:6]` + `rings[5:]`) which re-emitted the shared ring k=5: 13 duplicated vertex pairs per eye (id delta 27) | id-delta scan of the eye builder |
| 3 | 10 of the 67 degenerate faces | cornea cap built with `range(11)` points at `2πj/10`, so `pt0 == pt10` (`cos 2π − 1 = 0`, `sin 2π = −2.4e−16`) in a `close=True` ring | id-delta 10 pairs |
| 4 | 5 degenerate skin faces + 16 zero-length face edges (head) | `head.py` step 2 (sagittal profile) projected **every** eligible vertex onto the absolute target `y := skull_front_y(x, z)` with weight `clamp(edge)`; where the weight is 1, all vertices of a ray column sharing `(x, z)` collapse onto one point. 8 columns hold two eligible samples (measured by applying the pipeline stage by stage: 0 coincident groups after `box_sphere`, 8 after `add_feature_loops`, regardless of the later fields) | 8 coincident groups (+16 verts) |
| 5 | the 36 non-manifold edges | `mouth.py:_clamp_behind` pulled **each vertex** onto `y := skull_front_y(x, z) − margin`; a tooth's occlusal ring and its cap share `(x, z)` exactly, so the clamp collapsed them. 315 of 1596 vertices moved; pre-clamp 0 coincident pairs → post-clamp **32 intra-tooth pairs** (|Δy| 1.12–2.87 mm), all on the same `(x, z)` line | measured pair census before/after the clamp |
| 6 | the 2 loose edges | eye back pole (two edges with no linked face) | coordinate match with the eye centre/axis |

Common mechanism of #4 and #5: **an absolute projection `y := f(x, z)` applied
per vertex** is not injective on a column. Both were fixed the same way.

## 3. Changes

| File | Change |
|---|---|
| `generators/eyes.py` | world-space rings `k = 1..8` only (the pole is built by `cap_pole` alone, `region="eye"`); globe is **one** loft (the iris bands are re-materialised by face range — `materials/skin.py:build_iris` is driven by object coordinates and normals, not by UVs); limbus ring id (k=5) kept for the eyelid anchor; explicit `into.cap_pole(ids[-1], +1, material="iris", shrink=0.42)`; cornea rings use `range(10)`; **iris material assigned by ring membership, never by face-list position** (the position-based slice was measured to mis-label the back pole, which is appended last, and to split one band 10/2 — with identical per-material totals, which is exactly why the totals alone were not sufficient evidence); the pre-S2 UV mapping is reproduced structurally for the rings that survive |
| `generators/head.py` | step 2 rewritten as a **column-rigid translation**: eligible vertices are grouped by `(round(x, 9), round(z, 9))`, the shared shift is `need · clamp(edge)` with `need = surf − max(y)`, so the exposed vertex still lands exactly on `surf` while the column keeps its internal spacing exactly (a shared translation cannot change intra-group distances). A column whose front-most vertex is already at `surf` is left alone. Also: `box_sphere` now drops collapsed faces **and their `face_mat` entries together** (filtering `faces` alone desynchronised `face_mat`, a latent material-assignment bug), and returns `n/keys/faces/faces_dropped` for auditing |
| `generators/mouth.py` | `_clamp_rigid_groups()`: each tooth crown (14 groups, 50 verts each) is translated by the group's own maximum overshoot — physically correct (teeth are rigid) and provably collapse-free. The per-vertex clamp still handles the topologically continuous parts (`gum`, `oral`, `tongue`); `enamel` is deliberately excluded from it |
| `core/topology.py` | `to_bmesh(weld=1e-5, dissolve=0.0)`: optional `bmesh.ops.dissolve_degenerate` wash **after** the weld, with `op_counts` telemetry (`weld_removed`, `dissolve_collapsed`); `audit()` gains `loose_edges` |
| `core/object.py`, `pipeline/assemble.py` | `dissolve: float = 1e-5` plumbed through `mesh_from_builder` and `generate_character` (public contract stays backward compatible); audit warnings no longer claim a "known defect" that no longer exists, and warn on loose edges too |
| `tests/pins.py` | pins re-measured; `DEGENERATE_RING_PINS` deliberately flipped to `{}`; new `SEMANTIC_PINS` + `check_semantics()` (region populations + group sizes) |

### The wash is a guard, not the fix

The S2 hypothesis under test was "`weld=0` + `dissolve_degenerate(1e-5)` ⇒
0 NM / 0 deg / 10 ngons". Measured outcome, after the source fixes: **all four
regimes converge to the same mesh** and `op_counts` reads
`{"weld_removed": 0, "dissolve_collapsed": 0}` — i.e. the weld and the wash are
now *no-ops on the default build*. The 10 ngons the hypothesis predicted never
appear because the degenerate geometry they came from is no longer built. The
wash stays in the pipeline as an explicit, telemetrised guard for extreme
parameters and third-party generators, and it is pinned at 0 operations.

## 4. Result (post-S2)

| regime `weld/dissolve` | verts | faces | NM | loose | deg | quads/tris/ngons | quad_ratio | op_counts |
|---|---|---|---|---|---|---|---|---|
| `0 / 0` | 5759 | 5608 | 0 | 0 | 0 | 4870/738/0 | 0.868402 | 0 / 0 |
| `0 / 1e-5` | 5759 | 5608 | 0 | 0 | 0 | 4870/738/0 | 0.868402 | 0 / 0 |
| `1e-5 / 0` | 5759 | 5608 | 0 | 0 | 0 | 4870/738/0 | 0.868402 | 0 / 0 |
| `1e-5 / 1e-5` | 5759 | 5608 | 0 | 0 | 0 | 4870/738/0 | 0.868402 | 0 / 0 |

Identical in both numerics regimes for every field above (including
`boundary_edges` 946, `irregular_valence_verts` 101, `watertight: false`).

Acceptance criteria of S2, one by one:

| Criterion | Baseline | Result | Verdict |
|---|---|---|---|
| non-manifold edges | 36 | 0 | met |
| loose edges | 2 | 0 | met |
| degenerate faces (`calc_area < 1e-10`) | 67 | 0 | met |
| degenerate construction rings | `{eye.L.0: 78, eye.R.0: 78}` | `{}` | met |
| relevant coincidences explained | 76 groups / +124 verts | 0 groups | met (each one attributed above) |
| semantic flips within a numerics regime | – | 0 | met (§5); the *cross-regime* `sole`/`palm` split is pre-existing and is now pinned per regime |
| no regression of counts/contracts that should not change | – | see §5 | met |
| ngons within budget, mathematically explained | 0 | 0 (budget ≤ 12, 0 produced) | met |
| quad proportion with explicit formula | 0.868841 | 0.868402 | met (`quad_ratio` defined in §1; −0.44 pp) |

## 5. What changed and what did not (measured, whole character)

Per-generator census, same build, both trees:

| part | before v/f | after v/f | Δ |
|---|---|---|---|
| body | 2702 / 2516 | 2702 / 2516 | 0 |
| hand.L / hand.R | 633 / 581 | 633 / 581 | 0 |
| foot.L / foot.R | 345 / 321 | 345 / 321 | 0 |
| head | 632 / 604 | 632 / 604 | 0 (positions only) |
| mouth | 1819 / 1936 | 1819 / 1936 | 0 |
| **eyes** | **668 / 586** | **606 / 552** | **−62 / −34** |

* **Semantic labels**: for body, hands, feet, head and mouth the named vertex
  groups are **identical by vertex id** (not merely by size); region-label
  mismatches per vertex: 0 for head (632 verts) and 0 for mouth (1819 verts).
  For the rebuilt eyes the group sizes are identical (`iris.L/R` 13,
  `cornea.L/R` 2, `eyelid.L/R` 100) and the label predicates (angle to the gaze
  axis) still hold. Region populations of the whole character are identical in
  both numerics regimes and are now pinned (`SEMANTIC_PINS`).
* **Eye materials and UVs (measured after the first attempt was found wrong)**:
  `eye` = bands k=1..5 + back-pole cap, `iris` = bands k=5..8 + front-pole cap
  (the same faces the pre-S2 second loft covered).  Pre-S2 the globe registered
  rings 0..5 with `v = k/5` while a second, *unregistered* copy of rings 5..8
  carried the iris rect (`u` 0.5..1.0, `v` = 0, 1/3, 2/3, 1).  Removing that
  duplicate seam leaves one vertex set for those four rings, so one mapping must
  be chosen: the surviving sclera rings (rings 1..4 — 8 of the 16 ring/eye pairs)
  keep their pre-S2 UVs **bit for bit**, the limbus..pole rings keep the iris
  rect (the region the iris faces were drawn from), and the globe copy's
  `v = 1.0` on the limbus no longer exists anywhere because the vertex carrying
  it is gone.  No material samples UVs today (the shaders are object-coordinate
  driven); the front cap inherits these rings through `cap_pole`.
* **Numerics regimes — measured sensitivity, PRE-EXISTING**: the `sole`/`palm`
  label predicates sit exactly on a knife edge (the sole is a flat run of
  vertices and the threshold lands on it), so float32 labels 0 `sole` and 90
  `palm` where float64 labels 102 and 98.  Measured identical on the pre-S2 tree
  and the post-S2 tree ⇒ not an S2 regression.  It is why `SEMANTIC_PINS` is
  keyed by numerics backend, and why an unpinned backend is reported as a
  failure instead of being accepted.  (`mesh_digest` hashes only rounded vertex
  positions, so digest pins are insensitive to materials/UVs by construction.)
* **Scene contracts unchanged**: 58 vertex groups, 430 creases, the same
  material set, spec fingerprint `db7fb5c42c0523be` (the spec hash does not
  depend on geometry), hair strand count 2400 (realistic) / 3200 (neon) /
  2764 (cyber, pure regime).
* **Head geometry**: the exposed shell is unchanged — per `(x, z)` column the
  front-most vertex moves by **7e-6 mm** (float noise of the stored precision);
  40 vertices moved (max 26.8 mm, mean 8.5 mm), all of them *behind* the shell:
  they are the collapsed duplicates that used to be dragged onto the shell
  plane. Their new positions are ≥ 4.0 mm away from every other vertex (no new
  coincidence, no inversion).
* **Known regime sensitivity (pre-existing, not introduced)**: the hair strand
  count for `cyber_angel` is 2766 in the float32 regime and 2764 in float64 —
  measured identically on the pre-S2 tree and the post-S2 tree.
* **Digests**: regime-specific and re-measured deliberately
  (`dfb13c52c84f4982` pure-python, `69a638369e902297` mathutils).

### Visual corroboration (OBSERVED, not a substitute for the measurements)

Cycles/CPU renders of the same camera framing, before/after (body mesh only;
the hair is untouched by S2 and its fringe covers the eyes — a known visual
issue): RMSE 0.0035 (front) / 0.0044 (3/4) of full scale, with 2.8 % / 2.1 % of
pixels differing — the magnitude expected from sampling/denoising noise alone.
No structural difference is visible, which agrees with the measured
"exposed shell unchanged" result. EEVEE cannot run headless in this container
(`libEGL.so.1` missing), so CYCLES/CPU was used — a declared environment
limitation with an objective workaround.

## 6. Still open (not claimed as fixed)

1. Visual realism items from the checkpoint (fringe covering the eyes, corner
   tooth tips, eyelid caps, ear shading) — untouched by S2.
2. The numerics-regime policy is still **CONTROLLED**, not resolved: two
   legitimate digests for one spec+seed remain.
3. `boundary_edges` 946 / `watertight: false`: the character is a union of
   shells, so open rims are expected, but "how many rims and where" has not
   been audited yet.
4. The `sole`/`palm` knife edge above: stabilise the predicate, or accept and
   document the regime split? This is the most concrete case of the open
   numerics-regime question, and it changes *labels*, not geometry — so it must
   be decided deliberately, not by accident.
5. Semantic **vertex identity** across construction changes (needed for UVs,
   weights, morphs, shape keys, rig) is still an open question: S2 proves the
   *populations* are stable and that untouched parts keep their ids, not that
   identity survives an arbitrary rebuild.

## 7. Tests added / flipped

* `tests/test_pins.py`: +5 parametrised audit meta-tests (pin+1), +1 semantic
  pin meta-test (`check_semantics` reacts to a changed region label).
* `tests/test_topology.py`: the eye-pole test is now
  `test_eyes_are_clean_after_the_s2_fix` and asserts an empty guard.
* `tests/test_s0_public_api.py`: +4 checks (loose edges, ngons, weld/dissolve
  no-op telemetry, semantic pins), and the "known defect" checks flipped to
  `== 0` deliberately.
* `tests/pins.py`: `SEMANTIC_PINS` keeps one histogram per numerics backend
  (`pure-python`, `mathutils`) plus the 58 group sizes, and
  `check_semantics()` fails on an unpinned backend.
* Suite: **81 passed** (was 76). Acceptance: 33/33 pure, 72/72 bpy,
  72/72 bpy with the pure-python backend (was 33/68/68).
