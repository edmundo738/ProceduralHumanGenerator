# -*- coding: utf-8 -*-
"""Anthropometric landmarks.

One place turns ``CharacterSpec`` numbers into a 3-D landmark rig + the
breadth table every generator reads.  Facial features are derived from the
skull *surface function* (not from raw stature fractions) so features can
never float off the head when proportions vary.

Key facts (validated against ISO-7250-ish female distributions):
  head height H = stature / head_units;  chin at H below the vertex;
  eyes at mid-head (chin + 0.50H);  mouth chin + 0.165H;  nose base chin + 0.30H;
  ear spans chin + 0.30H … 0.60H;  biacromial = shoulder_head_ratio·H.
"""
from __future__ import annotations

import math

from ._math import Vector, clamp, mix, smoothstep
from .field import smooth_max
from .topology import Section, make_section
from ..spec import CharacterSpec

# fractions of stature for body stations
_Z: dict[str, float] = {
    # S3.6 — "ankle" é a altura do JOINT do tornozelo acima do chão:
    # antropométrico ≈ 0.042·estatura (≈71 mm a 1.70 m).  Estava em 0.075
    # (127.5 mm, ~1.8× demasiado alto), o que tornava a perna mais curta e o pé
    # mais alto: medido, o pé tinha 177.8 mm de altura e a casca do pé subia
    # 106 mm acima do tornozelo.  Efeito colateral desejado: foot_len =
    # |toe_end − ankle| cai de 277 mm para 262 mm (canonical 258 mm).
    "floor": 0.0, "toe_end": 0.018, "heel": 0.020, "ankle": 0.042,
    "ball": 0.030, "calf": 0.222, "knee": 0.287, "midthigh": 0.400,
    "crotch": 0.490, "hip": 0.530, "iliac": 0.630, "navel": 0.645,
    "waist": 0.700, "inframammary": 0.720, "nipple": 0.768, "bust": 0.758,
    "jugulum": 0.795, "acromion": 0.818, "deltoid_line": 0.812,
    "elbow": 0.645, "wrist": 0.508, "fingertip": 0.380,
    "chest_top": 0.800, "neck_top": 0.834, "spine_head": 0.845,
    "chin": 0.858, "shoulder": 0.818, "pelvis": 0.530,
    # S3.4 — reconciliação do canon com a geometria medida (o valor nominal
    # anterior era uma referência antropométrica sem consumidores no código).
    # Medido em realistic_female seed 42: topo do crânio 1.6842 m (coroa do
    # crânio, achatada de propósito por squash_top), ponta dos dedos 0.6808 m
    # (mão de 0.82 cabeças, construída por hand_length()).  Nada consome estas
    # duas entradas além do instrumento de integração (grep: 0 chamadas), logo
    # alinhar a tabela com o construído não move geometria nenhuma.
    "vertex": 0.991, "fingertip": 0.400,
}
# facial levels: multiples of head height ABOVE the chin
_FACE_Z: dict[str, float] = {
    "mouth": 0.165, "nose_base": 0.300, "nose_tip": 0.315, "philtrum": 0.24,
    "eye": 0.500, "glabella": 0.575, "brow": 0.585, "hairline": 0.725,
    "ear_bottom": 0.300, "ear_top": 0.600, "ear": 0.440, "jaw_angle": 0.100,
    "cheek": 0.360, "temple": 0.640, "forehead": 0.660, "nape": 0.560,
}


class Anatomy:
    """Landmark + breadth provider for one spec. Stateless after build."""

    def __init__(self, spec: CharacterSpec):
        self.spec = spec
        b = spec.body
        self.stature = s = b.stature
        self.h = head = b.head_height
        self._face_z = dict(_FACE_Z)
        self.landmarks: dict[str, Vector] = {}
        self._build_centres()

    # -- z lookup -----------------------------------------------------------
    def z(self, key: str) -> float:
        if key in self._face_z:
            return self.z("chin") + self._face_z[key] * self.h
        return _Z.get(key, 0.5) * self.stature

    # -- head geometry (single source of truth) ------------------------------
    def head_center(self) -> Vector:
        return Vector((0.0, -0.004 * self.stature, self.z("chin") + 0.52 * self.h))

    def head_radii(self) -> tuple[float, float, float]:
        h = self.h
        return (0.365 * h * 0.98 + 0.02 * h, 0.50 * h, 0.52 * h)  # (breadth, depth, height)

    def _shell_y(self, x: float, z: float) -> float:
        c = self.head_center()
        rx, ry, rz = self.head_radii()
        t = 1.0 - ((x - c.x) / rx) ** 2 - ((z - c.z) / rz) ** 2
        if t <= 0.0:
            return c.y + ry * 0.35
        return c.y + ry * math.sqrt(t)

    def skull_front_y(self, x: float, z: float) -> float:
        """Front surface height: cranial ellipsoid blended with a midface/
        mandible block so the lower face keeps a vertical profile."""
        y_cran = self._shell_y(x, z)
        c = self.head_center()
        rx, ry, rz = self.head_radii()
        h = self.h
        c2 = Vector((c.x, c.y + 0.055 * h, c.z - 0.26 * h))
        r2 = (0.88 * rx, 0.80 * ry, 0.66 * h)
        t2 = 1.0 - ((x - c2.x) / r2[0]) ** 2 - ((z - c2.z) / r2[2]) ** 2
        if t2 <= 0.0:
            return y_cran
        y_face = c2.y + r2[1] * math.sqrt(t2)
        return smooth_max(y_cran, y_face, 0.010 * h)

    def face_front(self, x: float, z: float, protrude: float = 0.0) -> Vector:
        """Surface point on the anterior side (used for every facial landmark)."""
        return Vector((x, self.skull_front_y(x, z) + protrude, z))

    # -- breadths --------------------------------------------------------------
    def shoulder_half(self) -> float:
        return 0.5 * self.h * self.spec.body.shoulder_head_ratio

    def deltoid_half(self) -> float:
        return self.shoulder_half() + 0.030 * self.stature * (1.0 + 0.45 * self.spec.body.muscle_tone)

    def chest_half(self) -> float:
        b = self.spec.body
        return self.shoulder_half() * (0.80 + 0.10 * b.chest_breath) * (1.0 + 0.10 * b.fat_level)

    def waist_half(self) -> float:
        b = self.spec.body
        hip = self.hip_half()
        return hip * b.waist_hip_ratio * 0.94

    def hip_half(self) -> float:
        b = self.spec.body
        return 0.105 * self.stature * b.hip_width_scale * (1.0 + 0.28 * b.fat_level)

    def bust_protrusion(self) -> float:
        b = self.spec.body
        return 0.19 * self.h * b.bust_relative + 0.030 * self.stature * b.fat_level

    def breast_volume_scale(self) -> float:
        return max(0.25, self.spec.body.bust_relative)

    def neck_half(self) -> float:
        return 0.052 * self.stature * (1.0 + 0.12 * self.spec.body.fat_level)

    def limb_radius(self, upper: bool = True) -> float:
        b = self.spec.body
        base = (0.028 if upper else 0.020) * self.stature
        return base * (0.92 + 0.16 * b.muscle_tone + 0.20 * b.fat_level) * self._breath()

    def thigh_half(self) -> float:
        b = self.spec.body
        return 0.050 * self.stature * (0.94 + 0.16 * b.muscle_tone + 0.30 * b.fat_level)

    def thigh_radius(self) -> float:  # back-compat alias
        return self.thigh_half()

    def calf_radius(self) -> float:
        b = self.spec.body
        return 0.030 * self.stature * (0.95 + 0.20 * b.muscle_tone + 0.20 * b.fat_level)

    def _breath(self) -> float:
        return self.spec.body.breath_scale

    def hand_length(self) -> float:
        return 0.78 * self.h * self.spec.body.hand_size

    def foot_length(self) -> float:
        return 0.155 * self.stature * self.spec.body.foot_size

    # -- landmark assembly ------------------------------------------------------
    def _build_centres(self) -> None:
        s, h = self.stature, self.h
        lm = self.landmarks
        zf = self.z

        # body midline
        lm["pelvis"] = Vector((0, -0.006 * s, zf("hip")))
        lm["spine_pelvis"] = Vector((0, 0.002 * s, zf("hip") - 0.04 * s))
        lm["spine_waist"] = Vector((0, 0.0, zf("waist")))
        lm["spine_chest"] = Vector((0, -0.004 * s, zf("chest_top")))
        lm["spine_neck"] = Vector((0, -0.010 * s, zf("neck_top")))
        lm["spine_head"] = Vector((0, -0.004 * s, zf("spine_head")))
        lm["neck_top"] = Vector((0, -0.006 * s, zf("neck_top")))
        lm["jugulum"] = Vector((0.0, -0.012 * s, zf("jugulum")))
        lm["vertex"] = Vector((0, 0.0, zf("vertex")))
        lm["chin"] = Vector((0, 0.0, zf("chin")))
        lm["nape"] = Vector((0, -self.head_radii()[1] * 0.92, zf("nape") + h * 0.560))

        # head/face (surface-derived)
        c = self.head_center()
        rx, ry, rz = self.head_radii()
        eye_x = 0.148 * h * self.spec.face.eye_spacing
        lm["eye.L"] = self.face_front(eye_x, zf("eye"), -0.032 * h)
        lm["eye.R"] = self.face_front(-eye_x, zf("eye"), -0.032 * h)
        lm["eye"] = (lm["eye.L"] + lm["eye.R"]) / 2
        lm["glabella"] = self.face_front(0.0, zf("glabella"), 0.006 * h)
        lm["brow.L"] = self.face_front(eye_x * 0.9, zf("brow"), 0.004 * h)
        lm["brow.R"] = self.face_front(-eye_x * 0.9, zf("brow"), 0.004 * h)
        nose_base_z = zf("nose_base")
        nose_tip_z = zf("nose_tip")
        lm["nose_base"] = self.face_front(0.0, nose_base_z, 0.012 * h)
        lm["nose_tip"] = self.face_front(0.0, nose_tip_z, 0.078 * h + 0.030 * h * (self.spec.face.nose_tip_projection - 1.0))
        lm["nose_root"] = self.face_front(0.0, zf("eye") + 0.035 * h, -0.004 * h)
        mouth_z = zf("mouth")
        lm["mouth"] = self.face_front(0.0, mouth_z, 0.010 * h)
        lm["mouth_center"] = lm["mouth"]
        mhw = 0.0770 * s * self.spec.face.mouth_width * 0.5
        lm["mouth_corner.L"] = self.face_front(mhw, mouth_z, -0.004 * h)
        lm["mouth_corner.R"] = self.face_front(-mhw, mouth_z, -0.004 * h)
        lm["chin_front"] = self.face_front(0.0, zf("chin") + 0.008 * h, 0.008 * h * self.spec.face.chin_projection)
        lm["philtrum"] = self.face_front(0.0, zf("philtrum"), 0.008 * h)
        lm["hairline"] = self.face_front(0.0, zf("hairline"), -0.004 * h)
        lm["ear.L"] = self.face_front(rx * 0.95, zf("ear"), 0.0)
        lm["ear.R"] = self.face_front(-rx * 0.95, zf("ear"), 0.0)
        lm["jaw_angle.L"] = Vector((0.055 * s * self.spec.face.jaw_width, -0.008 * s, zf("jaw_angle")))
        lm["jaw_angle.R"] = Vector((-0.055 * s * self.spec.face.jaw_width, -0.008 * s, zf("jaw_angle")))
        lm["cheek.L"] = self.face_front(rx * 0.62, zf("cheek"), 0.004 * h * self.spec.face.cheek_fullness)
        lm["cheek.R"] = self.face_front(-rx * 0.62, zf("cheek"), 0.004 * h * self.spec.face.cheek_fullness)
        lm["temple.L"] = self.face_front(rx * 0.80, zf("temple"), 0.0)
        lm["temple.R"] = self.face_front(-rx * 0.80, zf("temple"), 0.0)
        lm["ear_canal.L"] = lm["ear.L"] + Vector((0.0012 * s, 0.0, 0.0))
        lm["ear_canal.R"] = lm["ear.R"] + Vector((-0.0012 * s, 0.0, 0.0))

        # torso / limbs
        sh = self.shoulder_half()
        for tag, sx in ((".L", 1.0), (".R", -1.0)):
            lm["clavicle" + tag] = Vector((sx * sh * 0.55, -0.004 * s, zf("jugulum") + 0.028 * s))
            lm["acromion" + tag] = Vector((sx * sh, -0.004 * s, zf("acromion")))
            lm["deltoid" + tag] = Vector((sx * (sh + 0.020 * s), -0.006 * s, zf("deltoid_line")))
            lm["elbow" + tag] = Vector((sx * (sh * 0.92 + 0.055 * s), -0.010 * s, zf("elbow")))
            lm["wrist" + tag] = Vector((sx * (sh * 0.80 + 0.075 * s), -0.004 * s, zf("wrist")))
            lm["hand" + tag] = Vector((sx * (sh * 0.78 + 0.082 * s), -0.012 * s, zf("wrist") - self.hand_length() * 0.72))
            lm["hip" + tag] = Vector((sx * self.hip_half() * 0.52, -0.004 * s, zf("hip")))
            lm["iliac" + tag] = Vector((sx * self.hip_half() * 0.88, -0.002 * s, zf("iliac")))
            lm["knee" + tag] = Vector((sx * (self.hip_half() * 0.72 + 0.010 * s), 0.006 * s, zf("knee")))
            lm["ankle" + tag] = Vector((sx * (self.hip_half() * 0.30 + 0.012 * s), -0.006 * s, zf("ankle")))
            lm["heel" + tag] = Vector((sx * 0.020 * s, -0.055 * s * self.spec.body.foot_size, zf("heel") + 0.02 * s))
            lm["toe_end" + tag] = Vector((sx * 0.026 * s, 0.145 * s * self.spec.body.foot_size, zf("toe_end")))
            lm["ball" + tag] = Vector((sx * 0.030 * s, 0.105 * s, zf("ball")))
            lm["nipple" + tag] = self.face_front(0.100 * s, zf("nipple") + h * 0.5,
                                                 self.bust_protrusion() * 0.55)
            lm["bust" + tag] = self.face_front(0.105 * s, zf("bust") + h * 0.5,
                                               self.bust_protrusion())
        lm["crotch"] = Vector((0, -0.010 * s, zf("crotch")))

        # asymmetry: nudge one eyebrow down slightly (driven by spec)
        a = self.spec.face.asymmetry
        if a > 0:
            lm["brow.L"] += Vector((0, 0, -0.0012 * h * a))

    # -- section stacks -------------------------------------------------------
    def trunk_sections(self, segments: int = 16) -> list[Section]:
        """Stations from inside the skull down to the perineum (canonical space)."""
        s, h = self.stature, self.h
        zf = self.z
        c = self.head_center()
        neck_w = self.neck_half()
        sh = self.shoulder_half()
        dh = self.deltoid_half()
        chest = self.chest_half()
        waist = self.waist_half()
        hip = self.hip_half()
        bust = self.bust_protrusion()
        lean = self.spec.body.posture_lean * 0.004 * s
        front_off = -0.006 * s + lean

        secs: list[Section] = []

        def add(z, w, d, *, y=0.0, fs=1.0, bs=1.0, sup=2.0, reg="skin"):
            secs.append(make_section((0, front_off + y, z), tangent=(1, 0, 0), front=(0, 1, 0),
                                     width=max(0.005, w), depth=max(0.005, d),
                                     front_scale=fs, back_scale=bs, superellipse=sup, region=reg))

        # inside the skull (welds the neck into the head)
        add(zf("chin") + 0.78 * h, neck_w * 0.92, neck_w * 1.06)
        add(zf("chin") + 0.62 * h, neck_w * 0.96, neck_w * 1.08, y=-0.004 * s)
        # neck
        add(zf("spine_head") + 0.008 * s, neck_w * 1.02, neck_w * 1.10, y=-0.006 * s)
        # C7 / trapezius plate (wide, flat, sloped down to shoulders)
        add(zf("neck_top") - 0.004 * s, dh * 0.72, 0.055 * s, sup=2.6, bs=1.18, y=-0.010 * s)
        # deltoid line / shoulders
        add(zf("deltoid_line"), dh, chest * 0.62, sup=2.5, fs=1.0, bs=1.02)
        # upper chest
        add(zf("jugulum") + 0.020 * s, chest * 1.01, chest * 0.72, sup=2.2, fs=1.02, y=-0.002 * s)
        # bust line — silhouette + soft-tissue field do the rest
        add(zf("bust") + 0.004 * s, chest * 1.02, chest * 0.80, sup=2.0,
            fs=1.0 + bust / max(1e-4, chest * 0.8), y=0.004 * s)
        # inframammary / ribs
        add(zf("inframammary"), chest * 0.92, chest * 0.70, sup=2.05, fs=1.0, bs=1.0)
        # natural waist (narrowest)
        add(zf("waist"), waist, waist * 0.82, sup=2.0, fs=0.98, bs=1.0)
        # navel
        add(zf("navel"), mix(waist, hip, 0.45), mix(waist, hip, 0.45) * 0.84,
            sup=2.05, fs=1.02)
        # iliac flare
        add(zf("iliac"), hip * 0.97, hip * 0.84, sup=2.1, bs=1.04)
        # hip widest (trochanteric level)
        add(zf("hip"), hip, hip * 0.86, sup=2.05, y=-0.004 * s, bs=1.06)
        # perineum cap
        add(zf("crotch"), hip * 0.52, hip * 0.40, sup=2.2, y=-0.010 * s)
        return secs

    def arm_sections(self, side: int) -> list[Section]:
        """Shoulder → elbow → wrist. Rings are horizontal ellipses; the chain
        slant supplies the silhouette (deltoid, biceps, supinator taper)."""
        s = self.stature
        lm = self.landmarks
        tag = ".L" if side > 0 else ".R"
        sh, el, wr = lm["acromion" + tag], lm["elbow" + tag], lm["wrist" + tag]
        r_up, r_lo = self.limb_radius(True), self.limb_radius(False)
        b = self.spec.body
        sup = 2.15
        out: list[Section] = []

        def at(p, w, d, *, fs=1.0, bs=1.0, e=sup):
            out.append(make_section(p, tangent=(1, 0, 0), front=(0, 1, 0),
                                    width=max(0.004, w), depth=max(0.004, d),
                                    front_scale=fs, back_scale=bs, superellipse=e))

        # S3.2 — raiz INSERIDA no tronco.  Medido antes: a primeira estação ficava
        # 4.5% da estatura (76 mm) ACIMA do acromion, em z=1.467, onde o tronco só
        # chega a |x|=0.095 — a raiz do braço estava literalmente no ar (folga
        # mínima braço↔tronco 7.5 mm; o braço lia-se como uma manga solta), apesar
        # de generators/body.py documentar "limb roots are *inserted* into the
        # trunk".  A raiz passa a ficar dentro do tórax na altura do ombro, com
        # raio menor que a meia-largura do tronco nessa estação (0.268 medido).
        at(sh + Vector((-side * 0.055 * s, -0.004 * s, -0.004 * s)),
           r_up * 0.92, r_up * 0.92)                                            # root (in chest)
        at(sh, r_up * 1.16, r_up * 1.12)                                        # deltoid top
        at(sh.lerp(el, 0.18), r_up * 1.02, r_up * 1.04)                        # deltoid belly
        at(sh.lerp(el, 0.50), r_up * 0.84, r_up * 0.86, fs=1.04, bs=1.06)      # biceps/triceps
        at(sh.lerp(el, 0.82), r_up * 0.70, r_up * 0.72)
        at(el, r_up * 0.62, r_up * 0.66, e=2.3)                                # elbow
        at(el.lerp(wr, 0.14), r_lo * 1.04, r_lo * 1.10)                        # supinator mass
        at(el.lerp(wr, 0.55), r_lo * 0.86, r_lo * 0.88)
        at(el.lerp(wr, 0.85), r_lo * 0.72, r_lo * 0.70)
        at(wr, r_lo * 0.60, r_lo * 0.62, e=2.2)                                 # wrist
        return out

    def leg_sections(self, side: int) -> list[Section]:
        s = self.stature
        lm = self.landmarks
        tag = ".L" if side > 0 else ".R"
        hip, knee, ankle = lm["hip" + tag], lm["knee" + tag], lm["ankle" + tag]
        r_th, r_ca = self.thigh_half(), self.calf_radius()
        out: list[Section] = []

        def at(p, w, d, *, fs=1.0, bs=1.0, e=2.05, reg="skin"):
            out.append(make_section(p, tangent=(1, 0, 0), front=(0, 1, 0),
                                    width=max(0.004, w), depth=max(0.004, d),
                                    front_scale=fs, back_scale=bs, superellipse=e, region=reg))

        at(hip + Vector((0, -0.012 * s, 0.055 * s)), r_th * 0.72, r_th * 0.70)      # root (in pelvis)
        at(hip, r_th * 1.00, r_th * 0.98)
        at(hip.lerp(knee, 0.22), r_th * 1.04, r_th * 1.02)                            # upper thigh max
        at(hip.lerp(knee, 0.55), r_th * 0.90, r_th * 0.88)
        at(hip.lerp(knee, 0.85), r_th * 0.72, r_th * 0.70)
        at(knee, r_th * 0.63, r_th * 0.66, e=2.25)                                     # knee
        at(knee.lerp(ankle, 0.16), r_ca * 1.06, r_ca * 1.10, bs=1.18)                   # gastrocnemius
        at(knee.lerp(ankle, 0.40), r_ca * 1.10, r_ca * 1.14, bs=1.16)
        at(knee.lerp(ankle, 0.72), r_ca * 0.86, r_ca * 0.84)
        at(ankle + Vector((0, 0, 0.02 * s)), r_ca * 0.66, r_ca * 0.62)
        at(ankle, r_ca * 0.60, r_ca * 0.58, e=2.2)
        return out

    # -- misc accessors -------------------------------------------------------
    def side(self, name: str, side: int) -> Vector:
        return self.landmarks[f"{name}.{'.LR'[0 if side > 0 else 1]}"]

    def both_sides(self, prefix: str) -> list[tuple[int, str, Vector]]:
        return [(1, "L", self.landmarks[f"{prefix}.L"]),
                (-1, "R", self.landmarks[f"{prefix}.R"])]

    def pelvis_width(self) -> float:
        return self.hip_half()

    def bone(self, a_key: str, b_key: str, side: int = 0) -> tuple[Vector, Vector]:
        sfx = "" if side == 0 else (".L" if side > 0 else ".R")
        return self.landmarks[a_key + sfx], self.landmarks[b_key + sfx]

    @classmethod
    def from_spec(cls, spec: CharacterSpec) -> "Anatomy":
        return cls(spec)

    def summary(self) -> str:
        lm, b = self.landmarks, self.spec.body
        return (f"stature={b.stature:.3f}m head={self.h*1000:.0f}mm "
                f"shoulder={2*self.shoulder_half()*1000:.0f}mm "
                f"chest={2*self.chest_half()*1000:.0f}mm waist={2*self.waist_half()*1000:.0f}mm "
                f"hip={2*self.hip_half()*1000:.0f}mm "
                f"eye_z={(lm['eye'].z-lm['chin'].z)*1000:.0f}mm-above-chin "
                f"mouth_z={(lm['mouth'].z-lm['chin'].z)*1000:.0f}mm-above-chin")
