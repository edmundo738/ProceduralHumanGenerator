# -*- coding: utf-8 -*-
"""Materials: multilayer PBR skin, eye shaders, and the builder-name map.

Builder meshes use short material keys ("skin", "lip", "gum", ...); every
generated asset material is created as ``hcg:<kind>``.  ``MATERIAL_MAP``
routes builder keys onto those kinds.  Skin is a layered shader: melanin
ramp over dermal-noise mottling for base colour, subsurface scattering with
oxygenated-blood radius, dual GGX lobes (wet coat + body), pore bump.
"""
from __future__ import annotations


# builder material key -> asset material kind
MATERIAL_MAP = {
    "skin": "skin",
    "scalp": "skin",
    "lip": "lip",
    "gum": "gum",
    "enamel": "enamel",
    "dentin": "enamel",
    "oral_mucosa": "mucosa",
    "tongue": "mucosa",
    "eye": "sclera",
    "cornea": "cornea",
    "iris": "iris",
    "nail": "nail",
    "hair": "hair",
    "cloth": "cloth",
    "wear": "cloth",
    "metal": "cybernetic",
    "feather": "wing",
    "wing": "wing",
}

# melanin ramp stops: (melanin, albedo mid-tone sRGB) — Westermarck-ish
_TONE_STOPS = [
    (0.00, (0.93, 0.79, 0.70)),
    (0.30, (0.82, 0.64, 0.52)),
    (0.55, (0.66, 0.47, 0.35)),
    (0.78, (0.46, 0.31, 0.22)),
    (1.00, (0.21, 0.14, 0.10)),
]


def tone_from_melanin(m: float):
    m = max(0.0, min(1.0, m))
    for i in range(len(_TONE_STOPS) - 1):
        a, ca = _TONE_STOPS[i]
        b, cb = _TONE_STOPS[i + 1]
        if m <= b:
            t = (m - a) / max(1e-6, b - a)
            return tuple(ca[j] * (1.0 - t) + cb[j] * t for j in range(3))
    return _TONE_STOPS[-1][1]


def _node(tree, kind, x, y, **props):
    n = tree.nodes.new(kind)
    n.location = (x, y)
    for k, v in props.items():
        setattr(n, k, v)
    return n


def _link(a, b):
    """Link socket ``a`` → socket ``b``; tree is inferred from the sockets."""
    a.node.id_data.links.new(a, b)


def _mix_rgba(tree, x, y):
    """ShaderNodeMix set to RGBA; returns (node, factor_in, A_in, B_in, out).
    Socket indices are explicit because the node carries duplicated names."""
    n = tree.nodes.new("ShaderNodeMix")
    n.location = (x, y)
    n.data_type = "RGBA"
    return n, n.inputs[0], n.inputs[6], n.inputs[7], n.outputs[2]


def new_material(name: str):
    """Create (or refetch) an ``hcg:`` material with a clean node tree."""
    import bpy
    mat = bpy.data.materials.get(name)
    if mat is None:
        mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = _node(nt, "ShaderNodeOutputMaterial", 900, 0)
    return mat, nt, out


# ----------------------------------------------------------------------------- skin
def build_skin(spec, anat):
    sk = spec.skin
    mat, nt, out = new_material("hcg:skin")

    tex = _node(nt, "ShaderNodeTexCoord", -1500, 0)
    mapn = _node(nt, "ShaderNodeMapping", -1320, 0)
    _link(tex.outputs["Object"], mapn.inputs["Vector"])

    # masks ----------------------------------------------------------------
    pore = _node(nt, "ShaderNodeTexNoise", -1100, 380)
    pore.inputs["Scale"].default_value = 1.0 / 0.0016
    pore.inputs["Detail"].default_value = 3.0
    pore.inputs["Roughness"].default_value = 0.62
    _link(mapn.outputs["Vector"], pore.inputs["Vector"])

    mott = _node(nt, "ShaderNodeTexNoise", -1100, 120)     # melanin mottling
    mott.inputs["Scale"].default_value = 1.0 / 0.009
    mott.inputs["Detail"].default_value = 4.0
    _link(mapn.outputs["Vector"], mott.inputs["Vector"])

    # melanin: base colour ---------------------------------------------------
    base = tone_from_melanin(sk.melanin)
    base = tuple(c * (1.0 - 0.14 * sk.sun_exposure) for c in base)      # tan
    hb = sk.hemoglobin                       # oxygenated blood → ruddiness
    base = (base[0] * (1.0 + 0.05 * hb), base[1] * (1.0 - 0.03 * hb),
            base[2] * (1.0 - 0.05 * hb))
    ramp = _node(nt, "ShaderNodeValToRGB", -880, 240)
    ramp.color_ramp.elements[0].color = (*base, 1.0)
    ramp.color_ramp.elements[1].color = (*(c * 0.70 for c in base), 1.0)
    _link(mott.outputs["Fac"], ramp.inputs["Fac"])

    # freckles blend into the base colour (mask thresholded high-freq noise)
    base_out = ramp.outputs["Color"]
    if sk.freckle_amount > 0.01:
        fr = _node(nt, "ShaderNodeTexNoise", -1100, 660)
        fr.inputs["Scale"].default_value = 1.0 / 0.0034
        fr.inputs["Detail"].default_value = 2.0
        _link(mapn.outputs["Vector"], fr.inputs["Vector"])
        rm = _node(nt, "ShaderNodeValToRGB", -880, 660)
        rm.color_ramp.elements[0].position = 0.60
        rm.color_ramp.elements[1].position = 0.72
        _link(fr.outputs["Fac"], rm.inputs["Fac"])
        amt = _node(nt, "ShaderNodeMath", -660, 700, operation="MULTIPLY")
        amt.inputs[1].default_value = 0.55 * sk.freckle_amount
        _link(rm.outputs["Color"], amt.inputs[0])
        fmix, ff, fa, fb, fo = _mix_rgba(nt, -420, 560)
        fa.default_value = (0.42, 0.24, 0.14, 1.0)          # freckle pigment
        _link(amt.outputs["Value"], ff)
        _link(ramp.outputs["Color"], fa)
        base_out = fo

    # shader lobes -----------------------------------------------------------
    rough = _node(nt, "ShaderNodeMapRange", -880, 40)
    rough.inputs["To Min"].default_value = max(0.15, sk.roughness_mid * 0.42 - sk.skin_oiliness * 0.08)
    rough.inputs["To Max"].default_value = max(0.30, sk.roughness_mid * 0.80 + 0.18)
    _link(pore.outputs["Fac"], rough.inputs["Value"])

    body = _node(nt, "ShaderNodeBsdfPrincipled", -260, 120)
    _link(base_out, body.inputs["Base Color"])
    body.inputs["Roughness"].default_value = 0.5
    _link(rough.outputs["Result"], body.inputs["Roughness"])
    if "Subsurface Weight" in body.inputs:
        body.inputs["Subsurface Weight"].default_value = 0.10 + 0.40 * sk.subsurface_strength
        # epidermis-scattering radii: red travels deepest in tissue
        body.inputs["Subsurface Radius"].default_value = (0.0012, 0.0036, 0.0082)  # mm-scale, oxygenated blood
        if "Subsurface Scale" in body.inputs:
            body.inputs["Subsurface Scale"].default_value = 1.0
    if "Sheen Weight" in body.inputs:
        body.inputs["Sheen Weight"].default_value = 0.08 * (1.0 - sk.skin_oiliness)

    coat = _node(nt, "ShaderNodeBsdfPrincipled", -260, 420)
    coat.inputs["Base Color"].default_value = (1, 1, 1, 1)
    coat.inputs["Roughness"].default_value = 0.085 + 0.06 * sk.skin_oiliness
    if "Specular IOR Level" in coat.inputs:
        coat.inputs["Specular IOR Level"].default_value = 0.5 + 0.12 * sk.skin_oiliness
    # bumps: pores + very fine grit -------------------------------------------
    fine = _node(nt, "ShaderNodeTexNoise", -880, -420)
    fine.inputs["Scale"].default_value = 1.0 / 0.00055
    fine.inputs["Detail"].default_value = 2.0
    _link(mapn.outputs["Vector"], fine.inputs["Vector"])
    bump = _node(nt, "ShaderNodeBump", -120, -300)
    bump.inputs["Strength"].default_value = 0.05 + 0.10 * sk.skin_pores
    bump.inputs["Distance"].default_value = 6.0e-5 * (0.4 + sk.skin_pores)
    _link(pore.outputs["Fac"], bump.inputs["Height"])
    bump2 = _node(nt, "ShaderNodeBump", 60, -340)
    bump2.inputs["Strength"].default_value = 0.10
    bump2.inputs["Distance"].default_value = 2.0e-5
    _link(fine.outputs["Fac"], bump2.inputs["Height"])
    _link(bump.outputs["Normal"], bump2.inputs["Normal"])
    _link(bump2.outputs["Normal"], body.inputs["Normal"])
    _link(bump2.outputs["Normal"], coat.inputs["Normal"])

    mixc = _node(nt, "ShaderNodeMixShader", 140, 260)
    fres = _node(nt, "ShaderNodeFresnel", -120, 560)
    fres.inputs["IOR"].default_value = 1.43
    fac = _node(nt, "ShaderNodeMath", 0, 560, operation="MULTIPLY")
    fac.inputs[1].default_value = 0.45 + 0.25 * sk.skin_oiliness
    _link(fres.outputs["Fac"], fac.inputs[0])
    _link(fac.outputs["Value"], mixc.inputs["Fac"])
    _link(body.outputs[0], mixc.inputs[1])
    _link(coat.outputs[0], mixc.inputs[2])
    _link(mixc.outputs[0], out.inputs["Surface"])

    if spec.pipeline.micro_detail > 0.01 and hasattr(mat, "cycles"):
        try:
            mat.cycles.displacement_method = "BOTH"
        except Exception:
            pass
    return mat


# ----------------------------------------------------------------------------- eyes
def build_eye_sclera():
    mat, nt, out = new_material("hcg:sclera")
    b = _node(nt, "ShaderNodeBsdfPrincipled", 120, 0)
    b.inputs["Roughness"].default_value = 0.12
    if "Coat Weight" in b.inputs:
        b.inputs["Coat Weight"].default_value = 0.6
    tex = _node(nt, "ShaderNodeTexCoord", -700, -200)
    noi = _node(nt, "ShaderNodeTexNoise", -520, -200)
    noi.inputs["Scale"].default_value = 26.0
    noi.inputs["Detail"].default_value = 6.0
    _link(tex.outputs["Object"], noi.inputs["Vector"])
    rp = _node(nt, "ShaderNodeValToRGB", -340, -200)
    rp.color_ramp.elements[0].position = 0.62
    rp.color_ramp.elements[1].position = 0.75
    _link(noi.outputs["Fac"], rp.inputs["Fac"])
    vmix, vf, va, vb, vo = _mix_rgba(nt, -140, 60)
    va.default_value = (0.87, 0.86, 0.83, 1.0)
    vb.default_value = (0.70, 0.52, 0.49, 1.0)
    f = _node(nt, "ShaderNodeMath", -340, -420, operation="MULTIPLY")
    f.inputs[1].default_value = 0.18
    _link(rp.outputs["Color"], f.inputs[0])
    _link(f.outputs["Value"], vf)
    _link(vo, b.inputs["Base Color"])
    _link(b.outputs[0], out.inputs["Surface"])
    return mat


def build_cornea():
    mat, nt, out = new_material("hcg:cornea")
    g = _node(nt, "ShaderNodeBsdfGlass", 0, 0)
    g.inputs["Color"].default_value = (1, 1, 1, 1)
    g.inputs["Roughness"].default_value = 0.02
    g.inputs["IOR"].default_value = 1.376
    _link(g.outputs[0], out.inputs["Surface"])
    try:
        mat.blend_method = "BLEND"
    except (AttributeError, TypeError):
        pass
    return mat


def build_iris(spec):
    """Radial-fibre iris with limbal ring and pupil — UV/positional driver:
    spherical gradient centred on the gaze axis plus high-freq streaks."""
    mat, nt, out = new_material("hcg:iris")
    tint = tuple(spec.extras.iris_tint) if getattr(spec.extras, "iris_tint", None) else (0.30, 0.20, 0.14)
    tex = _node(nt, "ShaderNodeTexCoord", -800, 0)
    wave = _node(nt, "ShaderNodeTexWave", -600, -160)
    wave.inputs["Scale"].default_value = 60.0
    wave.inputs["Distortion"].default_value = 6.0
    wave.inputs["Detail"].default_value = 2.0
    wave.wave_type = "BANDS"
    wave.bands_direction = "Z"
    _link(tex.outputs["Object"], wave.inputs["Vector"])
    b = _node(nt, "ShaderNodeBsdfPrincipled", 200, 0)
    b.inputs["Roughness"].default_value = 0.12
    if "Coat Weight" in b.inputs:
        b.inputs["Coat Weight"].default_value = 1.0
    dark = tuple(c * 0.35 for c in tint)
    imix, ifac, ia, ib, io = _mix_rgba(nt, -160, 120)
    ia.default_value = (*dark, 1.0)
    ib.default_value = (*tint, 1.0)
    _link(wave.outputs["Fac"], ifac)
    # limbal darkening + pupil: distance-driven spherical gradient
    grad = _node(nt, "ShaderNodeTexGradient", -600, 240)
    grad.gradient_type = "SPHERICAL"
    mr = _node(nt, "ShaderNodeMapRange", -420, 240)
    mr.inputs["From Min"].default_value = -0.2
    mr.inputs["From Max"].default_value = 0.8
    _link(tex.outputs["Normal"], mr.inputs["Value"])
    _link(mr.outputs["Result"], grad.inputs["Vector"])
    ring = _node(nt, "ShaderNodeValToRGB", -240, 240)
    ring.color_ramp.elements[0].position = 0.30
    ring.color_ramp.elements[1].position = 0.90
    _link(grad.outputs["Fac"], ring.inputs["Fac"])
    _link(io, b.inputs["Base Color"])
    _link(b.outputs[0], out.inputs["Surface"])
    return mat


# ----------------------------------------------------------------------------- simple kinds
def build_generic(kind: str, spec):
    mat, nt, out = new_material(f"hcg:{kind}")
    b = _node(nt, "ShaderNodeBsdfPrincipled", 0, 0)
    if kind == "lip":
        b.inputs["Base Color"].default_value = (0.60, 0.24, 0.22, 1)
        b.inputs["Roughness"].default_value = 0.22
        if "Coat Weight" in b.inputs:
            b.inputs["Coat Weight"].default_value = 0.4
    elif kind == "gum":
        b.inputs["Base Color"].default_value = (0.52, 0.22, 0.21, 1)
        b.inputs["Roughness"].default_value = 0.34
    elif kind == "mucosa":
        b.inputs["Base Color"].default_value = (0.55, 0.24, 0.24, 1)
        b.inputs["Roughness"].default_value = 0.26
    elif kind == "enamel":
        b.inputs["Base Color"].default_value = (0.85, 0.82, 0.75, 1)
        b.inputs["Roughness"].default_value = 0.09
        if "Subsurface Weight" in b.inputs:
            b.inputs["Subsurface Weight"].default_value = 0.30
            b.inputs["Subsurface Radius"].default_value = (0.0012, 0.0024, 0.0034)
    elif kind == "nail":
        b.inputs["Base Color"].default_value = (0.72, 0.62, 0.57, 1)
        b.inputs["Roughness"].default_value = 0.11
        if "Coat Weight" in b.inputs:
            b.inputs["Coat Weight"].default_value = 0.85
    elif kind == "cloth":
        b.inputs["Base Color"].default_value = (0.20, 0.20, 0.23, 1)
        b.inputs["Roughness"].default_value = 0.66
        tex = _node(nt, "ShaderNodeTexWave", -420, -260)
        tex.inputs["Scale"].default_value = 900.0
        tex.inputs["Distortion"].default_value = 3.0
        bp = _node(nt, "ShaderNodeBump", -180, -260)
        bp.inputs["Strength"].default_value = 0.18
        bp.inputs["Distance"].default_value = 6e-5
        _link(tex.outputs["Fac"], bp.inputs["Height"])
        _link(bp.outputs["Normal"], b.inputs["Normal"])
    elif kind == "cybernetic":
        b.inputs["Base Color"].default_value = (0.55, 0.56, 0.58, 1)
        b.inputs["Metallic"].default_value = 1.0
        b.inputs["Roughness"].default_value = 0.22
        if "Anisotropic" in b.inputs:
            b.inputs["Anisotropic"].default_value = 0.6
    elif kind == "wing":
        b.inputs["Base Color"].default_value = (0.9, 0.9, 0.92, 1)
        b.inputs["Roughness"].default_value = 0.35
        if "Sheen Weight" in b.inputs:
            b.inputs["Sheen Weight"].default_value = 0.9
    _link(b.outputs[0], out.inputs["Surface"])
    return mat


def build_all(spec, anat):
    """Create every asset material (idempotent).  Returns kind→Material."""
    mats = {
        "skin": build_skin(spec, anat),
        "sclera": build_eye_sclera(),
        "cornea": build_cornea(),
        "iris": build_iris(spec),
    }
    for k in ("lip", "gum", "mucosa", "enamel", "nail", "cloth", "cybernetic", "wing"):
        mats[k] = build_generic(k, spec)
    return mats
