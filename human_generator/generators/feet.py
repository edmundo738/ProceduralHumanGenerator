# -*- coding: utf-8 -*-
"""Foot + toes.

Foot space: ``+z`` toward the toes (forward), ``+y`` up (dorsum), ``+x``
lateral — so the big toe sits medially (−x for L after side flip).  A
flatten-clamp field guarantees a flat sole (needed for standing), while the
transverse arch and the metatarsal fan do the organic shaping.
"""
from __future__ import annotations

import math

from ..core._math import Matrix, Vector
from ..core.topology import POLE_SCALE, MeshBuilder, make_section
from .digits import DigitPlan, build_digit, digit_rings

TOE_LEN = {"big": 1.0, "long": 0.88, "second": 0.80, "third": 0.70, "little": 0.58}
TOE_RAD = {"big": 1.0, "long": 0.86, "second": 0.78, "third": 0.70, "little": 0.58}


def _foot_basis(ankle: Vector, toe: Vector, side: int) -> Matrix:
    """Referencial local do pé; o lado direito é o **espelho exato** do esquerdo.

    S3.1 — mesma correcção do referencial da mão (``hands.py:_hand_basis``):
    ``x = z.cross(y) * side`` não produz um espelho (o produto externo não é
    equivariante sob reflexão).  Medido antes: 7.5–8.3 mm de Hausdorff entre os
    dedos dos dois pés.  O lado esquerdo mantém-se exactamente como estava.
    """
    mirror = side < 0
    a = Vector(ankle)
    t = Vector(toe)
    if mirror:                                  # trabalhar no lado canónico
        a = Vector((-a.x, a.y, a.z))
        t = Vector((-t.x, t.y, t.z))
    z = (t - a)
    z.y = max(z.y, 0.35 * z.length)             # sempre algum avanço
    z = z.normalized()
    y = Vector((0, 0, 1.0))
    y -= z * y.dot(z)
    y = y.normalized()
    x = z.cross(y)
    if x.length_squared < 1e-9:
        x = Vector((1.0, 0.0, 0.0))
    x = x.normalized()
    y = z.cross(x).normalized()
    rows = ((x.x, y.x, z.x, a.x),
            (x.y, y.y, z.y, a.y),
            (x.z, y.z, z.z, a.z),
            (0.0, 0.0, 0.0, 1.0))
    M = Matrix(rows)
    if mirror:
        M = Matrix(((-1.0, 0.0, 0.0, 0.0), (0.0, 1.0, 0.0, 0.0),
                    (0.0, 0.0, 1.0, 0.0), (0.0, 0.0, 0.0, 1.0))) @ M
    return M


def build_foot(spec, anat, *, side: int, rng) -> tuple[MeshBuilder, dict]:
    tag = "L" if side > 0 else "R"
    lm = anat.landmarks
    ankle = Vector(lm[f"ankle.{tag}"])
    toe = Vector(lm[f"toe_end.{tag}"])
    heel = Vector(lm[f"heel.{tag}"])
    ball = Vector(lm[f"ball.{tag}"])
    M = _foot_basis(ankle, toe, side)
    foot_len = (toe - ankle).length
    sole_drop = ankle.z - 0.004 * anat.stature  # sole plane in world z

    b = MeshBuilder(f"foot.{tag}")
    # S3.6 — parametrização anatómica.  Medido antes desta correcção (métrica
    # perpendicular ao eixo do pé, ver core/integration.foot_metrics):
    #   comprimento 287.3 mm (1.112× o canónico 0.152·estatura)
    #   largura     184.4 mm (1.972×)
    #   altura      177.8 mm  |  separação entre pés 0.25 mm
    # e, sobretudo, o tornozelo caía a **54 % do comprimento** do pé quando
    # anatomicamente fica a ~29 %: a perna entrava no pé a meio e sobrava
    # "remo" de calcanhar atrás.  As estações passam a ser fracções do
    # comprimento anatómico L, com o tornozelo em ``ankle_frac``:
    L = 0.152 * anat.stature * spec.body.foot_size
    ankle_frac = 0.29
    # S3.6 — o ``cap_pole`` é superfície: põe o pólo ``POLE_SCALE·r_médio``
    # ALÉM do anel, logo o extremo de trás do pé é o pólo do calcanhar, não a
    # estação 0.  Medido com o cap corrigido: o calcanhar ia 23 mm para trás da
    # estação e o pé media 274.3 mm (1.061× o canónico).  A estação do calcanhar
    # recua ``heel_frac`` para que o PÓLO caia na fracção 0 do comprimento
    # (calculado a partir do próprio anel — sem constante mágica).
    # A estação do calcanhar fica ``heel_frac`` à frente do extremo de trás; a
    # fracção é a distância do pólo ao anel, medida no 1º passo.
    heel_frac = 0.0
    width_ball = 0.181 * L * (1.0 + 0.25 * spec.body.fat_level)   # MEIA-largura

    def zl(frac: float) -> float:
        """Coordenada longitudinal local (tornozelo = 0).

        ``frac`` é medido a partir do **calcanhar anatómico**, isto é, do extremo
        de trás da superfície — que é o pólo do cap do calcanhar (``POLE_SCALE·r``
        ALÉM do anel), não o anel.  Medido: medindo as fracções a partir do anel
        do calcanhar o pé media 274.3 mm (1.061× o canónico 258.4 mm), porque o
        pólo empurrava o extremo de trás para fora do referencial.
        """
        return frac * L - ankle_frac * L

    # (fracção do comprimento, meia_largura, meia_profundidade, front, back,
    #  superelipse) — as fracções (e não as coordenadas) ficam guardadas porque
    # ``zl`` depende do ``heel_shift``, que só é conhecido depois de medir o
    # anel do calcanhar.
    def make_stations() -> list:
        return [
            (heel_frac, 0.085 * L, 0.135 * L, 1.00, 1.00, 2.4),   # calcanhar
            (0.11, 0.105 * L, 0.135 * L, 1.02, 0.98, 2.5),   # calcanhar
            (0.29, 0.135 * L, 0.140 * L, 1.02, 0.90, 2.4),   # arco/tornozelo
            (0.45, 0.155 * L, 0.105 * L, 1.00, 0.92, 2.3),   # meio
            (0.60, 0.181 * L, 0.086 * L, 0.98, 0.95, 2.2),   # bola (mais larga)
            (0.72, 0.170 * L, 0.070 * L, 0.96, 0.92, 2.1),   # linha dos dedos
        ]
    # A sola é colocada NO PLANO DO CHÃO por construção (e não por um clamp a
    # posteriori): para cada estação calcula-se o ``y`` local que mapeia em
    # ``z = 0`` e o centro da secção fica ``depth`` acima dele.  Medido: sem isto
    # o pé flutuava 13 mm (a versão anterior dependia de um clamp suavizado que
    # nunca chegava ao plano).
    def basis_col(idx: int) -> Vector:
        return M @ Vector(tuple(1.0 if k == idx else 0.0 for k in range(3))) - M @ Vector((0, 0, 0))

    y_ax = basis_col(1)
    z_ax = basis_col(2)

    def floor_local_y(zf: float) -> float:
        return -(zf * z_ax.z + ankle.z) / y_ax.z

    # Medido: neste referencial o eixo local +y aponta para BAIXO (y_ax.z =
    # −0.988).  Sem este sinal, ``centro = chão + meia_profundidade`` coloca a
    # secção *acima* do chão e ela estende-se para baixo dele — o clamp de chão
    # achatava então o pé inteiro em z=0 (medido: componente com altura 0).
    up = -1.0 if y_ax.z < 0.0 else 1.0

    def make_rings() -> list:
        out = []
        for (frac, w, hh, fs, bs, e) in make_stations():
            zf = zl(frac)
            # arco longitudinal: a sola levanta-se na zona do arco médio (o apoio
            # fica no calcanhar e na bola, como num pé real)
            arch = max(0.0, 1.0 - abs(zf - zl(0.44)) / (L * 0.22))
            sole_lift = 0.055 * L * arch * math.sin(math.pi * min(1.0, arch))
            centre_y = floor_local_y(zf) + up * (hh + sole_lift)
            secs = make_section((0.0, centre_y, zf), tangent=(1, 0, 0), front=(0, 1, 0),
                                width=w, depth=hh, front_scale=fs, back_scale=bs, superellipse=e)
            out.append([M @ p for p in secs.points(12)])
        return out

    rings = make_rings()
    # 2ª passagem: deslocamento medido (raio médio do anel do calcanhar) — a
    # rotação/translação M não altera o raio médio em torno do centro.
    heel_c = sum(rings[0], Vector((0, 0, 0))) / len(rings[0])
    heel_r = sum((p - heel_c).length for p in rings[0]) / len(rings[0])
    if heel_frac == 0.0:
        heel_frac = POLE_SCALE * heel_r / L
        rings = make_rings()
    # S3.5 — o pé era uma casca ABERTA (24 arestas de fronteira medidas em
    # z 0.012..0.178): via-se o interior através da boca do tornozelo e da ponta.
    created = b.loft(rings, close=True, region="skin", material="skin",
                     uv_rect=(0.05, 0.95, 0.0, 0.4), register=f"foot.{tag}",
                     cap_start="pole", cap_end="pole")
    # S3.6 — "sole" pelo chão (z mundial), não pelo limiar local que oscilava
    # entre regimes numéricos (a região só aparecia em float64 — limiar em cunha
    # documentado em docs/S3_BODY_INTEGRATION.md §3).  O pé está apoiado no plano
    # z=0, logo a sola é objectivamente "z ≤ 12 mm".
    for ring in created["rings"]:
        for vi in ring:
            if b.verts[vi].z <= 0.012:
                b.regions[vi] = "sole"

    joints: dict[str, Vector] = {}
    # toes from the ball row
    toe_x = [-0.62 * width_ball, -0.30 * width_ball, 0.02 * width_ball,
             0.30 * width_ball, 0.55 * width_ball]
    volar_foot = Vector((0, -1, 0.05))  # toward sole → toes flex down
    volar_w = (M.to_4x4() @ volar_foot) - (M.to_4x4() @ Vector((0, 0, 0)))
    volar_w = volar_w.normalized()
    for ti, name in enumerate(TOE_LEN.keys()):
        # S3.6 — os dedos nascem na linha dos dedos (0.72·L) e a ponta do dedo
        # grande fecha o comprimento anatómico (0.72 + 0.26 ≈ 0.98·L).  Antes
        # nasciam a 0.40·foot_len do tornozelo (≈94 % do pé) e mediam 10 % do pé:
        # eram tocos numa extremidade de remo.
        toe_r = L * 0.040 * TOE_RAD[name]
        base = M @ Vector((toe_x[ti], floor_local_y(zl(0.72)) + up * toe_r * 0.92, zl(0.72)))
        # A ponta do dedo é o PÓLO do cap (``POLE_SCALE·r`` além do último anel):
        # é ele que tem de fechar a estação anatómica, não a âncora.  Medido
        # antes: com a âncora em 0.97·L a unha/ponta levavam o pé a 272.3 mm
        # (1.054× o canónico).  O dedo grande fecha 0.98·L; os outros escalam.
        pole_frac = 0.72 + 0.26 * TOE_LEN[name]
        tl = (pole_frac - 0.72) * L * (0.9 + 0.2 * rng.f(0.9, 1.1))
        dirv = M.to_4x4() @ Vector((toe_x[ti] / max(1e-6, L) * 0.05, 0.02, 1.0)) \
            - M.to_4x4() @ Vector((0, 0, 0))
        dirv = dirv.normalized()

        def make_plan(length: float) -> DigitPlan:
            return DigitPlan(kind="toe", name=name,
                             anchors=[base, base + dirv * length * 0.55,
                                      base + dirv * length],
                             base_radius=toe_r,
                             flex=(0.05, 0.10), volar=volar_w,
                             flatness=0.85, segments=2, ring_n=8, nail=(ti == 0))

        probe = digit_rings(make_plan(tl))
        tip_c = sum(probe[-1], Vector((0, 0, 0))) / len(probe[-1])
        tip_r = sum((p - tip_c).length for p in probe[-1]) / len(probe[-1])
        tl -= POLE_SCALE * tip_r                      # ápice na estação
        plan = make_plan(tl)
        build_digit(b, plan, material="skin", group_prefix=f"{tag}.")
        a0, a2 = plan.anchors[0], plan.anchors[-1]
        joints[f"{name}.mcp"] = a0
        joints[f"{name}.tip"] = a2
    joints["ankle"] = ankle
    joints["heel"] = heel
    joints["toe_end"] = toe
    for key in list(joints):
        joints[f"foot.{tag}.{key}"] = joints.pop(key)

    # ---- rede de segurança: nada abaixo do plano z=0 ----------------------
    # (a sola já é construída no plano; ``sole_z`` era +5.95 mm e empurrava a
    # sola inteira para cima — medido)
    from ..core.field import Deformer
    flat = Deformer("flatten", plane_n=(0.0, 0.0, -1.0), plane_d=0.0,
                    amp=0.0, sigma=(0.008, 0.008, 0.008))
    for i, p in enumerate(b.verts):
        d = flat.evaluate(p, None)
        if d.length_squared > 1e-12:
            b.verts[i] = p + d
    return b, joints
