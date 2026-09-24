# -*- coding: utf-8 -*-
"""Shared geometry pins (S1).

One source of truth for the determinism gate, used by both
``tests/test_s0_public_api.py`` (acceptance, runnable without pytest) and the
pytest suite.  A pin is a deliberate regression barrier: if geometry changes,
the pin MUST fail until a human updates it *on purpose* — see
``tests/test_pins.py`` for the meta-test proving the gate really measures
geometry, and ``docs/RESEARCH_COMPARATIVE_01.md`` §9 for the rationale.

``digest`` is keyed by numerics backend (``core._math`` uses mathutils/float32
inside Blender when bpy is imported first, and a float64 stand-in otherwise).
Set ``HCG_MATHUTILS=0`` to force one digest regardless of import order.
"""
from __future__ import annotations

CONTRACT_VERSION_PIN = "1.0.0"

# ("preset", seed) -> pins
PINS = {
    ("realistic_female", 42): {
        "fingerprint": "db7fb5c42c0523be",   # spec hash: unchanged by S2
        "verts": 5891,          # pre-weld (pure build)
        "faces": 5872,
        "strands": 2400,
        # re-measured in S3.6 (feet: pole-relative length frame, rounded tips,
        # nails ending at the tip apex, sole labelled by world z)
        "digest": {"pure-python": "79bbe2aade711af6",
                   "mathutils": "3192f8da92d56b67"},
    },
}

# topology must be constant across presets (Gate 02 §6) — seed 7
# ``verts/faces`` are S2 numbers; ``strands`` are the *pure-python* regime
# values (pytest runs without bpy).  The strand count is regime-sensitive for
# cyber_angel only (2764 float64 / 2766 float32) and was already so before S2 —
# measured on both trees, see docs/S2_TOPOLOGY.md §5.
PRESET_COUNTS = {
    "cyber_angel": (5891, 5872, 2764),
    "neon_idol": (5891, 5872, 3200),
    "realistic_female": (5891, 5872, 2400),
}

# post-weld audit, Blender-side (docs/S2_TOPOLOGY.md §4).
# S2 flipped these deliberately: the weld and the dissolve wash are now both
# no-ops on the default build (0 vertices removed, 0 edges collapsed), so the
# audited mesh IS the built mesh and every defect counter reads 0.  Measured
# identically in the mathutils (float32) and pure-python (float64) regimes.
AUDIT_PINS = {"verts": 5891, "faces": 5872,
              "non_manifold_edges": 0,
              "degenerate_faces": 0,
              "loose_edges": 0,
              "ngons": 0,
              "boundary_edges": 802}   # S3: limb/foot tubes are capped shells now
# S3.6: ``weld`` and ``dissolve`` are no-ops in ALL FOUR grid combinations in
# both regimes (``ops 0/0``) — the build has no vertex pair closer than the
# default weld (1e-5).  Before the ``cap_pole`` fix, weld=1e-5 merged 2 vertices
# and produced 2 non-manifold edges.

# construction guard (S1): rings whose points collapse.
# S2 fixed eyes.py (the pole is now built by cap_pole only and the limbus ring
# is no longer emitted twice), so the pin is deliberately EMPTY: the guard still
# runs on every build and any future collapsed ring shows up as a new key.
DEGENERATE_RING_PINS: dict[str, int] = {}

# --- semantic vertex labels (S2 criterion 6) ---------------------------------
# A "semantic flip" = any change in the number of vertices carrying a region
# label, or in the size of a named vertex group.  Vertex *ids* are deliberately
# not pinned: ids shift whenever a generator's construction order changes (the
# eyes were rebuilt in S2), and pins must not forbid legitimate construction
# changes — they must catch label drift.
#
# The pins are keyed by numerics backend ON PURPOSE: measured in S2, the
# ``sole``/``palm`` predicates sat exactly on a knife edge (the sole was a flat
# run of vertices and the threshold landed on it), so float32 vs float64 shifted
# those two populations by tens of vertices.  S3.6 removed ONE of the two
# knife edges: ``sole`` is now defined by world z (<= 12 mm) and reads the SAME
# 40 vertices in both regimes.  ``palm`` is still knife-edged (108 pure / 86
# mathutils) and remains the recorded, still-open part of the numerics-regime
# question.
SEMANTIC_PINS = {
    ("realistic_female", 42): {
        "pure-python": {
            "regions": {
                "brow": 2, "cornea": 102, "enamel": 1400,
                "eye": 264, "eyelid": 240, "gum": 196,
                "lip": 96, "nail": 192, "oral": 127,
                "palm": 108, "scalp": 148, "skin": 2976,
                "sole": 40
            },
            "groups": {
                "L.finger.index.0": 40, "L.finger.index.1": 32, "L.finger.index.2": 8,
                "L.finger.middle.0": 40, "L.finger.middle.1": 32, "L.finger.middle.2": 8,
                "L.finger.pinky.0": 40, "L.finger.pinky.1": 32, "L.finger.pinky.2": 8,
                "L.finger.ring.0": 40, "L.finger.ring.1": 32, "L.finger.ring.2": 8,
                "L.finger.thumb.0": 40, "L.finger.thumb.1": 32, "L.finger.thumb.2": 8,
                "L.toe.big.0": 32, "L.toe.big.1": 8, "L.toe.little.0": 32,
                "L.toe.little.1": 8, "L.toe.long.0": 32, "L.toe.long.1": 8,
                "L.toe.second.0": 32, "L.toe.second.1": 8, "L.toe.third.0": 32,
                "L.toe.third.1": 8, "R.finger.index.0": 40, "R.finger.index.1": 32,
                "R.finger.index.2": 8, "R.finger.middle.0": 40, "R.finger.middle.1": 32,
                "R.finger.middle.2": 8, "R.finger.pinky.0": 40, "R.finger.pinky.1": 32,
                "R.finger.pinky.2": 8, "R.finger.ring.0": 40, "R.finger.ring.1": 32,
                "R.finger.ring.2": 8, "R.finger.thumb.0": 40, "R.finger.thumb.1": 32,
                "R.finger.thumb.2": 8, "R.toe.big.0": 32, "R.toe.big.1": 8,
                "R.toe.little.0": 32, "R.toe.little.1": 8, "R.toe.long.0": 32,
                "R.toe.long.1": 8, "R.toe.second.0": 32, "R.toe.second.1": 8,
                "R.toe.third.0": 32, "R.toe.third.1": 8, "head.brow": 2,
                "head.cornea.L": 2, "head.cornea.R": 2, "head.eyelid.L": 100,
                "head.eyelid.R": 100, "head.iris.L": 13, "head.iris.R": 13,
                "head.scalp": 148,
            },
        },
        "mathutils": {
            "regions": {
                "brow": 2, "cornea": 102, "enamel": 1400,
                "eye": 264, "eyelid": 240, "gum": 196,
                "lip": 96, "nail": 192, "oral": 127,
                "palm": 86, "scalp": 148, "skin": 2998,
                "sole": 40
            },
            "groups": {
                "L.finger.index.0": 40, "L.finger.index.1": 32, "L.finger.index.2": 8,
                "L.finger.middle.0": 40, "L.finger.middle.1": 32, "L.finger.middle.2": 8,
                "L.finger.pinky.0": 40, "L.finger.pinky.1": 32, "L.finger.pinky.2": 8,
                "L.finger.ring.0": 40, "L.finger.ring.1": 32, "L.finger.ring.2": 8,
                "L.finger.thumb.0": 40, "L.finger.thumb.1": 32, "L.finger.thumb.2": 8,
                "L.toe.big.0": 32, "L.toe.big.1": 8, "L.toe.little.0": 32,
                "L.toe.little.1": 8, "L.toe.long.0": 32, "L.toe.long.1": 8,
                "L.toe.second.0": 32, "L.toe.second.1": 8, "L.toe.third.0": 32,
                "L.toe.third.1": 8, "R.finger.index.0": 40, "R.finger.index.1": 32,
                "R.finger.index.2": 8, "R.finger.middle.0": 40, "R.finger.middle.1": 32,
                "R.finger.middle.2": 8, "R.finger.pinky.0": 40, "R.finger.pinky.1": 32,
                "R.finger.pinky.2": 8, "R.finger.ring.0": 40, "R.finger.ring.1": 32,
                "R.finger.ring.2": 8, "R.finger.thumb.0": 40, "R.finger.thumb.1": 32,
                "R.finger.thumb.2": 8, "R.toe.big.0": 32, "R.toe.big.1": 8,
                "R.toe.little.0": 32, "R.toe.little.1": 8, "R.toe.long.0": 32,
                "R.toe.long.1": 8, "R.toe.second.0": 32, "R.toe.second.1": 8,
                "R.toe.third.0": 32, "R.toe.third.1": 8, "head.brow": 2,
                "head.cornea.L": 2, "head.cornea.R": 2, "head.eyelid.L": 100,
                "head.eyelid.R": 100, "head.iris.L": 13, "head.iris.R": 13,
                "head.scalp": 148,
            },
        },
    },
}


def expected_digest(backend: str, key=("realistic_female", 42)) -> str:
    return PINS[key]["digest"].get(backend, "")


def check_build(result, key=("realistic_female", 42)) -> list[str]:
    """Return a list of pin violations for a BuildResult/GenerationResult."""
    pin = PINS[key]
    failures: list[str] = []
    if result.contract_version != CONTRACT_VERSION_PIN:
        failures.append(f"contract_version {result.contract_version} != pin "
                        f"{CONTRACT_VERSION_PIN}")
    if result.fingerprint != pin["fingerprint"]:
        failures.append(f"fingerprint {result.fingerprint} != pin {pin['fingerprint']}")
    got = (result.verts, result.faces, len(result.hair.strands))
    want = (pin["verts"], pin["faces"], pin["strands"])
    if got != want:
        failures.append(f"counts {got} != pin {want}")
    backend = result.numerics.get("backend", "")
    if not backend:
        failures.append("result does not declare a numerics backend")
    elif result.digest != expected_digest(backend, key):
        failures.append(f"digest[{backend}] {result.digest} != pin "
                        f"{expected_digest(backend, key)}")
    return failures


def check_audit(audit: dict) -> list[str]:
    """Return a list of post-weld audit pin violations."""
    failures = []
    for field, want in AUDIT_PINS.items():
        got = audit.get(field)
        if got != want:
            failures.append(f"audit[{field}] {got} != pin {want}")
    return failures


def _semantic_histogram(builder) -> dict:
    from collections import Counter
    return {
        "regions": dict(Counter(builder.regions)),
        "groups": {name: len(weights) for name, weights in builder.groups.items()},
    }


def check_semantics(result, key=("realistic_female", 42)) -> list[str]:
    """Return a list of semantic-label violations for a BuildResult.

    A violation is any region population or group size that differs from the
    pin for the *result's own numerics backend*, in either direction (added and
    removed labels both count).  An unpinned backend is reported as a violation
    rather than silently accepted.
    """
    backend = (result.numerics or {}).get("backend", "")
    by_regime = SEMANTIC_PINS[key]
    if backend not in by_regime:
        return [f"semantic pins have no entry for backend {backend!r} "
                f"(pinned: {sorted(by_regime)})"]
    pin = by_regime[backend]
    got = _semantic_histogram(result.builder)
    failures: list[str] = []
    for kind in ("regions", "groups"):
        want_h, got_h = pin[kind], got[kind]
        for name in sorted(set(want_h) | set(got_h)):
            if want_h.get(name) != got_h.get(name):
                failures.append(f"semantic[{kind}][{name}] {got_h.get(name)} != "
                                f"pin {want_h.get(name)}")
    return failures
