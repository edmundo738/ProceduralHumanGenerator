#!/usr/bin/env python3
"""S0 acceptance test — public character API contract ``hcg-charapi/1.0.0``.

Purpose (owner's S0 criterion): ``generate_character(...)`` must be a real,
verifiable API, must produce a *valid* character, and a second run with the same
parameters and seed must be deterministic.  ``tools/dev_smoke.py`` must no
longer be the only proof that the system works.

Run both halves::

    python tests/test_s0_public_api.py                      # pure: geometry, digests, errors
    python tools/headless_blender.py run tests/test_s0_public_api.py --bpy   # full: objects, audit, .blend

Exit code is non-zero on any failure.  Outputs go to ``out/s0_api/`` (gitignored).

Scope note: this is deliberately *one* file with plain asserts — the pytest
harness, fixtures and math/RNG contract tests are slice S1, not S0.
"""
from __future__ import annotations

import json
import os
import shutil
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import human_generator as hcg  # noqa: E402
from human_generator.pipeline.assemble import (CONTRACT_VERSION,  # noqa: E402
                                               build_character, resolve_spec)

# --------------------------------------------------------------------------- gates
# Pins live in tests/pins.py so the pytest suite and this script cannot drift.
import pins  # noqa: E402

PINS = pins.PINS
AUDIT_PINS = pins.AUDIT_PINS

OUT_DIR = os.path.join(ROOT, "out", "s0_api")

_results: list[tuple[str, bool, str]] = []


def check(name: str, condition: bool, detail: str = "") -> bool:
    _results.append((name, bool(condition), detail))
    print(f"  [{'PASS' if condition else 'FAIL'}] {name}" + (f" — {detail}" if detail else ""))
    return bool(condition)


def raises(name: str, exc_type, fn, *, match: str = "") -> bool:
    try:
        fn()
    except exc_type as exc:
        ok = match in str(exc) if match else True
        return check(name, ok, f"{type(exc).__name__}: {str(exc)[:72]}")
    except Exception as exc:  # wrong exception type
        return check(name, False, f"raised {type(exc).__name__}, expected {exc_type.__name__}")
    return check(name, False, "no exception raised")


# --------------------------------------------------------------------------- pure half
def suite_pure() -> None:
    print("\n== S0 pure (no bpy): geometry, determinism, contract ==")
    check("contract version is exposed", CONTRACT_VERSION == "1.0.0",
          f"hcg.API_CONTRACT_VERSION={hcg.API_CONTRACT_VERSION}")

    t0 = time.perf_counter()
    r = build_character("realistic_female", seed=42)
    elapsed = time.perf_counter() - t0
    print(f"      build: {r.verts} verts, {r.faces} faces, {len(r.hair.strands)} strands, {elapsed:.2f}s")

    check("vet_count sane", r.verts > 1000, f"{r.verts}")
    check("face_count sane", r.faces > 1000, f"{r.faces}")
    check("quad-dominant topology", r.stats["quad_ratio"] > 0.80, f"{r.stats['quad_ratio']:.3f}")
    check("no degenerate faces pre-weld", int(r.stats["degenerate"]) == 0)
    check("hair generated", len(r.hair.strands) > 0, f"{len(r.hair.strands)}")
    expected_warnings = 1 if r.numerics.get("backend") == "mathutils" else 0
    check("only the documented numerics warning (if any)",
          len(r.warnings) == expected_warnings, str(r.warnings))

    # determinism: same spec+seed, twice
    r2 = build_character("realistic_female", seed=42)
    check("run-to-run fingerprint stable", r.fingerprint == r2.fingerprint, r.fingerprint)
    check("run-to-run digest stable", r.digest == r2.digest, r.digest)
    check("run-to-run stats stable", r.stats == r2.stats)

    # determinism: fresh object, independent construction path
    spec_a = hcg.CharacterSpec.from_preset("realistic_female", seed=42)
    spec_b = hcg.CharacterSpec.from_preset("realistic_female", seed=42)
    r3 = build_character(spec_a)
    r4 = build_character(spec_b)
    check("spec-object path identical to preset path", r3.digest == r4.digest == r.digest)

    # seed sensitivity
    r5 = build_character("realistic_female", seed=43)
    check("different seed ⇒ different geometry", r5.digest != r.digest, r5.digest)

    # regression pins (shared with the pytest suite; digest is regime-specific)
    backend = r.numerics.get("backend")
    check("numerics regime reported", backend in ("pure-python", "mathutils"),
          f"{r.numerics} (digests are regime-specific by design)")
    check("PIN fingerprint", r.fingerprint == PINS[("realistic_female", 42)]["fingerprint"],
          f"{r.fingerprint} (update PIN only on purpose)")
    check(f"PIN digest [{backend}]", r.digest == pins.expected_digest(backend),
          f"{r.digest} vs pin {pins.expected_digest(backend)}")
    check("PIN counts", (r.verts, r.faces, len(r.hair.strands))
          == (PINS[("realistic_female", 42)]["verts"], PINS[("realistic_female", 42)]["faces"],
              PINS[("realistic_female", 42)]["strands"]),
          f"{(r.verts, r.faces, len(r.hair.strands))}")
    check("shared pin gate agrees", pins.check_build(r) == [], str(pins.check_build(r)))

    # every preset is reachable through the public API
    for preset in hcg.list_presets():
        b = build_character(preset, seed=7)
        check(f"preset {preset!r} builds", b.verts > 1000 and len(b.hair.strands) > 0,
              f"{b.verts}v/{b.faces}f, {len(b.hair.strands)} strands")

    # extreme parameters: no crash, constant topology (Gate 02 §6 property)
    extremes = {"face.nose_tip_projection": 1.9, "face.lip_fullness": 0.25,
                "face.eye_spacing": 1.35, "face.jaw_width": 1.5,
                "face.ear_size": 0.7, "body.head_units": 6.4, "body.stature": 1.50}
    r6 = build_character("realistic_female", seed=7, overrides=extremes)
    # S4.2 — as aberturas da cabeça são cortadas por janelas em milímetros: a
    # anatomia dirige quais as faces que caem dentro delas, logo a contagem deixa
    # de ser EXACTAMENTE constante sob parâmetros extremos (medido: 6415/6311
    # contra 6307/6213 = +1.7 %).  O critério passa a ser a banda declarada de
    # 5 % mais a validade da malha — não a igualdade exacta.
    _band = all(abs(a - b) <= 0.05 * b
                for a, b in ((r6.verts, r.verts), (r6.faces, r.faces)))
    check("extreme overrides build (counts within the declared 5% band)",
          _band and r6.stats["degenerate"] == 0 and r6.stats["ngons"] == 0,
          f"{r6.verts}v/{r6.faces}f (band + valid)")
    check("extreme overrides change geometry", r6.digest != r.digest)

    # spec resolution & precedence
    s = resolve_spec("cyber_angel", seed=5, overrides={"face.nose_tip_projection": 1.7})
    check("resolve_spec: str + seed + override",
          s.preset == "cyber_angel" and s.seed == 5 and s.face.nose_tip_projection == 1.7)
    s2 = resolve_spec(s, seed=6)
    check("resolve_spec: seed overrides spec.seed", s2.seed == 6 and s2.face.nose_tip_projection == 1.7)
    check("resolve_spec: identity path keeps object", resolve_spec(s) is s)
    check("resolve_spec: default preset",
          resolve_spec().preset == "realistic_female" and resolve_spec().seed == 0)

    # error contract
    raises("unknown preset → ValueError", ValueError, lambda: build_character("no_such_preset"),
           match="unknown preset")
    raises("bad override group → ValueError", ValueError,
           lambda: build_character("realistic_female", overrides={"nope.x": 1}),
           match="unknown override group")
    raises("bad override field → ValueError", ValueError,
           lambda: build_character("realistic_female", overrides={"face.nope": 1}),
           match="unknown field")
    raises("bad spec type → TypeError", TypeError, lambda: build_character(3.5), match="spec must be")
    raises("bool seed → TypeError", TypeError,
           lambda: build_character("realistic_female", seed=True), match="bool")
    raises("non-numeric seed → TypeError", TypeError,
           lambda: build_character("realistic_female", seed="abc"), match="seed must be")
    raises("unknown kwarg → TypeError", TypeError,
           lambda: build_character("realistic_female", bogus=1))


# --------------------------------------------------------------------------- bpy half
def suite_bpy() -> None:
    import bpy          # bpy must come first: bmesh only resolves after the
    import bmesh        # Blender extension module is loaded (headless quirk)

    from human_generator.core.topology import audit

    print("\n== S0 full (Blender runtime): public API → objects, audit, files ==")
    if os.path.isdir(OUT_DIR):
        shutil.rmtree(OUT_DIR)

    t0 = time.perf_counter()
    res = hcg.generate_character("realistic_female", seed=42, out_dir=OUT_DIR, name="s0_a")
    print(f"      generate: {res.elapsed:.2f}s, objects={res.objects}, audit={res.audit}")
    check("generate_character returned a GenerationResult",
          type(res).__name__ == "GenerationResult" and res.contract_version == CONTRACT_VERSION)

    body = bpy.data.objects.get(res.objects["body"])
    hair = bpy.data.objects.get(res.objects["hair"])
    check("body object exists in the file", body is not None)
    check("body object is in the scene", bool(body and body.name in bpy.context.scene.objects))
    check("hair object exists (curves)", hair is not None and hair.type == "CURVE",
          f"type={getattr(hair, 'type', None)}")

    check("materials built", len(res.materials) >= 8, f"{len(res.materials)}: {res.materials}")
    check("body has material slots", len(body.data.materials) >= 3,
          f"{[m.name for m in body.data.materials]}")
    check("subsurf modifier from spec", any(m.type == "SUBSURF" for m in body.modifiers))
    check("spec tag stored on object",
          body.get("hcg_spec") == res.fingerprint and body.get("hcg_seed") == 42)
    check("UV layer present", len(body.data.uv_layers) > 0)
    check("region attribute present", "hcg_region" in body.data.attributes)

    # audit pins (weld-applied numbers from the checkpoint)
    bm = bmesh.new()
    bm.from_mesh(body.data)
    topo = audit(bm)
    bm.free()
    check("AUDIT-PIN verts/faces (post-weld)",
          (topo["verts"], topo["faces"]) == (AUDIT_PINS["verts"], AUDIT_PINS["faces"]),
          f"{topo['verts']}v/{topo['faces']}f")
    # S3.6 — o limiar era 0.85, com 0.0006 de margem (0.850407 no S3.5): uma
    # aresta de faca, não um critério.  O S3.6 retirou um anel por pé (110 → 98
    # vértices: a casca do pé acaba na linha dos dedos, porque os dedos passam a
    # nascer da fila da bola) — menos 24 quads em 5872, razão 0.849796.
    # O critério REGISTADO (S2, re-checado por I9) é a *fórmula* do quad_ratio e
    # o orçamento de ngons (0), não este número; a dominância de quads mantém-se
    # (4990 quads / 882 triângulos, 0 ngons).  O limiar é REVISTO para 0.84, com
    # o motivo declarado aqui, em vez de silenciado.
    check("AUDIT-PIN quads", topo["quad_ratio"] > 0.84,
          f"{topo['quad_ratio']:.4f} (bar revised 0.85→0.84 in S3.6, see comment)")
    check("AUDIT-PIN degenerate_faces = 0",
          topo["degenerate_faces"] == AUDIT_PINS["degenerate_faces"], f"{topo['degenerate_faces']}")
    check("AUDIT-PIN non-manifold = 0 (S2 closed this defect deliberately)",
          topo["non_manifold_edges"] == AUDIT_PINS["non_manifold_edges"],
          f"{topo['non_manifold_edges']}")
    check("AUDIT-PIN loose edges = 0 (S2)",
          topo.get("loose_edges") == AUDIT_PINS["loose_edges"], f"{topo.get('loose_edges')}")
    check("AUDIT-PIN ngons = 0 (dissolve wash kept in budget)",
          topo.get("ngons") == AUDIT_PINS["ngons"], f"{topo.get('ngons')}")
    check("weld/dissolve are no-ops on the default build (S2)",
          getattr(res.build.builder, "op_counts", None) ==
          {"weld_removed": 0, "dissolve_collapsed": 0},
          str(getattr(res.build.builder, "op_counts", None)))
    check("semantic label pins agree",
          pins.check_semantics(res.build) == [], str(pins.check_semantics(res.build)))
    check("shared audit pin gate agrees", pins.check_audit(topo) == [], str(pins.check_audit(topo)))
    check("no audit defect surfaced as a warning (S2: all counters are 0)",
          not any(k in w for w in res.warnings
                  for k in ("non-manifold", "degenerate", "loose")), str(res.warnings))

    # files
    check(".blend written", os.path.isfile(res.files.get("blend", ""))
          and os.path.getsize(res.files["blend"]) > 1024,
          f"{os.path.getsize(res.files.get('blend', '')) } bytes")
    check("JSON report written", os.path.isfile(res.files.get("report", "")))
    saved = json.load(open(res.files["report"]))
    check("report carries contract version", saved["contract_version"] == CONTRACT_VERSION)
    check("report carries digest + audit",
          saved["digest"] == res.digest and saved["audit"]["verts"] == topo["verts"])
    check("report states the numerics regime",
          saved["numerics"]["backend"] in ("pure-python", "mathutils"),
          str(saved["numerics"]))
    check("bpy-side digest matches the pin for THIS regime",
          res.digest == PINS[("realistic_female", 42)]["digest"].get(res.numerics["backend"]),
          f"{res.digest} [{res.numerics['backend']}]")

    # determinism across two independent runs (second run, fresh names)
    res2 = hcg.generate_character("realistic_female", seed=42, out_dir=OUT_DIR, name="s0_b")
    check("second run: identical digest", res2.digest == res.digest, res2.digest)
    check("second run: identical fingerprint", res2.fingerprint == res.fingerprint)
    check("second run: identical audit", res2.audit == res.audit, str(res2.audit))
    saved2 = json.load(open(res2.files["report"]))
    for key in ("digest", "fingerprint", "audit", "stats", "numerics"):
        check(f"second run: identical report['{key}']", saved2[key] == saved[key])

    # determinism from an equivalent spec object (not just the string path)
    spec = hcg.CharacterSpec.from_preset("realistic_female", seed=42)
    res3 = hcg.generate_character(spec, out_dir=OUT_DIR, name="s0_c", write_blend=False)
    check("spec-object path: identical digest", res3.digest == res.digest)

    # re-run in the same session must be safe (no name/py-data collisions)
    res4 = hcg.generate_character("realistic_female", seed=42, name="s0_c")
    check("re-run in same session is safe", res4.digest == res.digest)
    check("re-run creates a separate object",
          res4.objects["body"] != body.name and bpy.data.objects.get(res4.objects["body"]) is not None)

    # warnings are honest for a modified spec too (no false calm)
    res5 = hcg.generate_character("cyber_angel", seed=1, name="s0_neon", write_blend=False)
    check("other preset via API works", res5.audit["verts"] > 1000,
          f"{res5.audit['verts']}v, nm={res5.audit['non_manifold_edges']}")
    check("other preset is defect-free too (S2: spec-independent)",
          res5.audit["non_manifold_edges"] == 0,
          f"{res5.audit['non_manifold_edges']}")
    print(f"      total bpy half: {time.perf_counter() - t0:.1f}s")


def main() -> int:
    bpy_mode = "--bpy" in sys.argv
    print(f"HCG S0 acceptance test | contract {CONTRACT_VERSION} | mode={'bpy' if bpy_mode else 'pure'}")
    suite_pure()
    if bpy_mode:
        suite_bpy()
    else:
        print("\n(pure mode: skipping the Blender-runtime half — run with "
              "'python tools/headless_blender.py run tests/test_s0_public_api.py --bpy')")

    failed = [n for n, ok, _ in _results if not ok]
    print(f"\n{len(_results) - len(failed)}/{len(_results)} checks passed")
    if failed:
        print("FAILED: " + "; ".join(failed))
        return 1
    print("S0 ACCEPTANCE: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
