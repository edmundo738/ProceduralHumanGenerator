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
        "fingerprint": "db7fb5c42c0523be",
        "verts": 5821,          # pre-weld (pure build)
        "faces": 5642,
        "strands": 2400,
        "digest": {"pure-python": "39ce28298fce36de",
                   "mathutils": "34e746aa4e649945"},
    },
}

# topology must be constant across presets (Gate 02 §6) — seed 7
PRESET_COUNTS = {
    "cyber_angel": (5821, 5642, 2764),
    "neon_idol": (5821, 5642, 3200),
    "realistic_female": (5821, 5642, 2400),
}

# post-weld audit, Blender-side (docs/RESEARCH_GATE_02.md)
AUDIT_PINS = {"verts": 5695, "faces": 5551,
              "non_manifold_edges": 36,   # known defect — S2 target, flip to 0 deliberately
              "degenerate_faces": 0}

# construction guard (S1): rings whose points collapse; documented defect, S2 target
DEGENERATE_RING_PINS = {"eye.L.0": 78, "eye.R.0": 78}


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
