"""EXECUÇÃO do pré-registo H7a × H4a (docs/PREREG_H7A_H4A.md, commit 8b6bb79).

Gera UMA variante (E0/E1/E2/E3) com o gerador INTACTO: a intervenção é um
override em tempo de execução, neste processo, de ``Anatomy.trunk_sections``
(pós-processamento das estações devolvidas) e, só no E2, da placa do esterno
(``DeformStack.bump`` com a assinatura exata de generators/body.py:129).
Nada é escrito em human_generator/.  Verificações feitas aqui:
  * SHA-256 de todos os .py do gerador antes e depois == valores de HEAD;
  * registo estação a estação (antes/depois) do que foi alterado;
  * exportação pelo MESMO caminho do instrumento (refload._eval, subsurf 1) e da
    cage (subsurf 0) para as verificações de invariância.

Uso: python tools/headless_blender.py run tools/refstudy2/prereg_run.py -- VARIANT OUT_DIR
"""
import hashlib, glob, json, math, os, sys
ROOT = os.getcwd()
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tools", "refstudy"))
import numpy as np

args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
VARIANT, OUT = args[0], args[1]
os.makedirs(OUT, exist_ok=True)


def src_digest():
    h = hashlib.sha256()
    for p in sorted(glob.glob(os.path.join(ROOT, "human_generator", "**", "*.py"), recursive=True)):
        h.update(p[len(ROOT):].encode()); h.update(open(p, "rb").read())
    return h.hexdigest()


SRC_BEFORE = src_digest()
import bpy                                                     # noqa: E402
import human_generator as hcg                                  # noqa: E402
from human_generator.core import anatomy as A                  # noqa: E402
from human_generator.core import field as F                    # noqa: E402

# ---------------------------------------------------------------- parâmetros CONGELADOS (pré-registo)
DIAG = os.environ.get("HCG_PREREG_DIAG", "")   # "noplate": diagnóstico de atribuição de fugas (E2 sem re-ancorar a placa)
K = 0.85                                   # E2: condição experimental, NÃO proporção anatómica validada
DTH_P, DTH_T = 6.89, 10.85                 # E3: graus (diferença controlo → média das refs em P1/P2)
STATION_KEYS = ["deltoid_line", "jugulum", "bust", "inframammary", "waist", "navel", "hip_flare", "hip", "crotch"]

_orig = A.Anatomy.trunk_sections
LOG = {"variant": VARIANT, "diag": DIAG, "stations": []}


def _identify(anat, secs):
    """Mapeia estação → índice pela cota (mesmas fórmulas de trunk_sections)."""
    s = anat.stature
    zt = {"deltoid_line": anat.z("deltoid_line"), "jugulum": anat.z("jugulum"),
          "bust": anat.z("bust") + 0.004 * s, "inframammary": anat.z("inframammary"),
          "waist": anat.z("waist"), "navel": anat.z("navel"), "hip_flare": anat.z("hip_flare"),
          "hip": anat.z("hip"), "crotch": anat.z("crotch")}
    idx = {}
    for k, z in zt.items():
        cands = [i for i, sc in enumerate(secs) if abs(sc.center.z - z) < 1e-5]
        assert len(cands) == 1, (k, cands)
        idx[k] = cands[0]
    return idx


def _snap(sc):
    return dict(z=sc.center.z, y=sc.center.y, width=sc.width, depth=sc.depth,
                fs=sc.front_scale, bs=sc.back_scale, sup=sc.superellipse)


STERNUM_DY = {"dy": 0.0}


def patched(self, segments: int = 16):
    secs = _orig(self, segments)
    idx = _identify(self, secs)
    before = [_snap(sc) for sc in secs]
    s = self.stature
    if VARIANT == "E1":                         # knock-out diagnóstico da massa anterior do busto
        secs[idx["bust"]].front_scale = 1.0
    elif VARIANT == "E2":                       # tamanho, parede posterior FIXA
        bust = self.bust_protrusion()
        fronts = {}
        for k in ("jugulum", "bust", "inframammary"):
            sc = secs[idx[k]]
            d0, fs0 = sc.depth, sc.front_scale
            front0 = sc.center.y + d0 * fs0
            sc.width *= K
            sc.depth = d0 * K
            if k == "bust":                     # protrusão ABSOLUTA do busto mantida (F3)
                sc.front_scale = 1.0 + bust / sc.depth
            sc.center.y -= (d0 - sc.depth) * sc.back_scale      # costas fixas: c − d·bs constante
            fronts[k] = (sc.center.z, sc.center.y + sc.depth * sc.front_scale - front0)
        # placa do esterno acompanha a parede anterior: Δfront interpolado à cota da placa
        zp = self.z("inframammary") + 0.055 * s
        (zb, db), (zj, dj) = fronts["bust"], fronts["jugulum"]
        t = min(1.0, max(0.0, (zp - zb) / (zj - zb)))
        STERNUM_DY["dy"] = db + (dj - db) * t
        STERNUM_DY["z"] = zp
        # deltoid_line: profundidade chest·0.62 NÃO mexida (congelada no valor do controlo)
    elif VARIANT == "E3":                       # orientação: cisalhamento sagital dos centros
        tp, tt = math.tan(math.radians(DTH_P)), math.tan(math.radians(DTH_T))
        z = {k: secs[idx[k]].center.z for k in STATION_KEYS}
        def dy_raw(zz):                         # sem a descida até ao deltoide
            p = tp * (min(zz, z["waist"]) - z["hip_flare"]) if zz > z["hip_flare"] else 0.0
            t_ = -tt * (zz - z["waist"]) if zz > z["waist"] else 0.0
            return p + t_
        dys = {}
        for k in ("navel", "waist", "inframammary", "bust"):
            dys[k] = dy_raw(z[k])
        frac = (z["deltoid_line"] - z["jugulum"]) / (z["deltoid_line"] - z["bust"])
        dys["jugulum"] = dys["bust"] * frac
        for k, dy in dys.items():
            secs[idx[k]].center.y += dy
        LOG["e3_dy_mm"] = {k: round(v * 1000, 2) for k, v in dys.items()}
        LOG["e3_untouched"] = [k for k in STATION_KEYS if k not in dys] + ["pescoço/cabeça (3 estações)", "rampas do trapézio (2)"]
        LOG["e3_pivot"] = "hip_flare (Δy=0 em hip_flare/hip/crotch; Δy=0 da linha do deltoide para cima)"
    elif VARIANT != "E0":
        raise SystemExit(f"variante desconhecida {VARIANT}")
    after = [_snap(sc) for sc in secs]
    inv = {v: k for k, v in idx.items()}
    for i, (b, a) in enumerate(zip(before, after)):
        ch = {k: (b[k], a[k]) for k in b if abs(b[k] - a[k]) > 1e-9}
        LOG["stations"].append(dict(i=i, name=inv.get(i, f"sec{i}"), z=b["z"], changed=ch))
    return secs


A.Anatomy.trunk_sections = patched

_orig_bump = F.DeformStack.bump


def bump_patched(self, centre, amp, radius=0.05, **kw):
    if VARIANT == "E2" and STERNUM_DY.get("z") is not None and DIAG != "noplate":
        s = 1.7
        sg = kw.get("sigma")
        if (abs(centre.x) < 1e-12 and abs(amp - 0.0035 * s) < 1e-12 and sg is not None
                and all(abs(a - b) < 1e-12 for a, b in zip(sg, (0.028 * s, 0.020 * s, 0.050 * s)))):
            centre = F.Vector((centre.x, centre.y + STERNUM_DY["dy"], centre.z))
            LOG["sternum_plate_dy_mm"] = round(STERNUM_DY["dy"] * 1000, 2)
    return _orig_bump(self, centre, amp, radius, **kw)


F.DeformStack.bump = bump_patched

# ---------------------------------------------------------------- geração (mesma via que gen_blend.py)
for ob in list(bpy.data.objects):
    bpy.data.objects.remove(ob, do_unlink=True)
r = hcg.generate_character("realistic_female", seed=42, out_dir=OUT, name=f"prereg_{VARIANT}")
blend = r.files["blend"]
LOG["digest"], LOG["fingerprint"] = r.digest, r.fingerprint
LOG["audit"] = {k: v for k, v in r.audit.items() if isinstance(v, (int, float, str, bool))}
LOG["numerics"] = r.build.numerics
LOG["warnings"] = r.build.warnings
from human_generator.core import integration as INT   # noqa: E402
_rep = INT.integration_report(r.build)
_rep["junctions"] = INT.junction_metrics(r.build)
_rep["hand_L"], _rep["hand_R"] = INT.hand_metrics(r.build, "L"), INT.hand_metrics(r.build, "R")
json.dump(_rep, open(os.path.join(OUT, "integration_report.json"), "w"), indent=1, default=str)

# ---------------------------------------------------------------- exportação pelo caminho do instrumento
os.environ["HCG_BUILD_BLEND"] = blend
import refload                                                # noqa: E402
refload.BUILD = blend
V, T = refload.load("ours")                                   # subsurf 1 (como o REF01)
np.savez(os.path.join(OUT, "raw_ours.npz"), V=V, T=T)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.wm.open_mainfile(filepath=blend)
Vc, Tc = refload._eval([o for o in bpy.data.objects if o.type == "MESH"], subsurf_max=0)
np.savez(os.path.join(OUT, "cage_ours.npz"), V=Vc, T=Tc)

SRC_AFTER = src_digest()
LOG["src_sha256_before"], LOG["src_sha256_after"] = SRC_BEFORE, SRC_AFTER
LOG["src_unchanged"] = SRC_BEFORE == SRC_AFTER
json.dump(LOG, open(os.path.join(OUT, "run_log.json"), "w"), indent=1, default=str)
print("PREREG", VARIANT, "digest", r.digest, "src_unchanged", LOG["src_unchanged"], "verts", len(V), "cage", len(Vc))
