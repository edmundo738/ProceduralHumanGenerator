# -*- coding: utf-8 -*-
"""THE STALKER v2 — GEOMETRIA CRIADA DE RAIO (dono: 'cria a forma, não uses
modelos — só para comparação e escala').

Nenhum corpo emprestado: cada anel é gerado aqui. O Michelle (1.66 m) serviu
SÓ de régua de escala — a criatura acorda em ~1.82 m.

Construção (numpy, determinístico, seed fixa):
  - LOFT geral: splines de centro + perfis de raio → anéis → quads→tris;
  - tronco: UMA superfície contínua da bacia ao pescoço, com a coluna
    CORCUNDA (curva, não cilindro) e secções elípticas com ε orgânico;
  - cabeça alongada inclinada; mandíbula separada (pivô próprio = boca
    que ABRE); olhos negros embutidos; cavidade + 2 fileiras de dentes;
  - membros: tubos enraizados DENTRO do tronco (as junções ficam
    escondidas na carne — CARNE LIGADA) + esferas de articulação nos
    pivôs (cobrem a rotação, à moda PSX);
  - braços até ao joelho (0.34+0.36+~0.30); pernas com canela quase
    recta e pé alongado com 3 garras; mãos com 4 dedos + polegar.

Saída:
  site/models/stalker2_smooth.glb (+cage) — meshes NOMEADOS por parte +
  TEXCOORD_0 (UV cilíndrico, texturas tileable do stalker);
  site/models/stalker2_rig.json — hierarquia/pivôs p/ animação procedural
  em three.js (stalker.js v2);
  painel docs/head_phaseA/stalker2_views.png (frente/perfil/costas + zoom
  cabeça) — auto-cheque de silhueta ANTES do site.

Uso: python3 tools/creature/build_stalker2.py
"""
import json
import os
import struct

import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
OUT = os.path.join(ROOT, "site", "models")
DOC = os.path.join(ROOT, "docs", "head_phaseA")
SEED = 13
rng = np.random.default_rng(SEED)

# ---------------------------------------------------------------- primitivas
def sphere(c, r, n=10):
    us = np.linspace(0, np.pi, n)
    vs = np.linspace(0, 2 * np.pi, 2 * n, endpoint=False)
    V, T = [], []
    for i, u in enumerate(us):
        for j, v in enumerate(vs):
            p = c + r * np.array([np.sin(u) * np.cos(v), np.sin(u) * np.sin(v), np.cos(u)])
            V.append(p)
    V = np.array(V)
    nu, nv = len(us), len(vs)
    for i in range(nu - 1):
        for j in range(nv):
            a, b = i * nv + j, i * nv + (j + 1) % nv
            c_, d = (i + 1) * nv + (j + 1) % nv, (i + 1) * nv + j
            T.append((a, b, c_)); T.append((a, c_, d))
    return V, np.array(T)


def cone(c, r, h, dirv, n=8):
    """Cone com base em c (círculo perpendicular a dirv) e ápice c+h*dirv."""
    t = np.asarray(dirv, float); t /= np.linalg.norm(t)
    ref = np.array([0, 0, 1.0]) if abs(t[2]) < 0.9 else np.array([1.0, 0, 0])
    b1 = np.cross(t, ref); b1 /= np.linalg.norm(b1)
    b2 = np.cross(t, b1)
    th = np.linspace(0, 2 * np.pi, n, endpoint=False)
    ring = c + r * (np.cos(th)[:, None] * b1 + np.sin(th)[:, None] * b2)
    apex = np.repeat((c + h * t)[None], n, 0)
    V = np.vstack([ring, apex])
    T = []
    for j in range(n):
        k = (j + 1) % n
        T.append((j, k, n)); T.append((j, n, k))   # base fecha p/ fora
    return V, np.array(T), np.zeros((len(V), 2))


def loft(pts, rads, e1=None, e2=None, n=24, caps=True, noise=0.0):
    """Tubo ao longo da polilinha pts (N,3); rads (N,) raio base.
    e1/e2: factores elípticos (N,) nos eixos b1/b2. Devolve V,T,UV."""
    N = len(pts)
    e1 = np.ones(N) if e1 is None else e1
    e2 = np.ones(N) if e2 is None else e2
    V, UV = [], []
    eps = 1.0 + noise * rng.standard_normal((N, 2))
    for i in range(N):
        t = pts[min(i + 1, N - 1)] - pts[max(i - 1, 0)]
        t = t / max(np.linalg.norm(t), 1e-9)
        ref = np.array([0, 0, 1.0]) if abs(t[2]) < 0.9 else np.array([1.0, 0, 0])
        b1 = np.cross(t, ref); b1 /= np.linalg.norm(b1)
        b2 = np.cross(t, b1)
        th = np.linspace(0, 2 * np.pi, n, endpoint=False) + i * 0.13
        r1, r2 = rads[i] * e1[i] * eps[i, 0], rads[i] * e2[i] * eps[i, 1]
        ring = pts[i] + np.cos(th)[:, None] * (r1 * b1) + np.sin(th)[:, None] * (r2 * b2)
        V.append(ring)
        UV.append(np.stack([th / (2 * np.pi), np.full(n, i / max(N - 1, 1))], 1))
    V = np.vstack(V); UV = np.vstack(UV)
    T = []
    for i in range(N - 1):
        for j in range(n):
            k = (j + 1) % n
            a, b = i * n + j, i * n + k
            c_, d = (i + 1) * n + k, (i + 1) * n + j
            T.append((a, b, c_)); T.append((a, c_, d))
    if caps:                                     # tampas em leque
        for (idx, tri) in ((0, (0, 1, 2)), (N - 1, (0, 2, 1))):
            base = idx * n
            for j in range(1, n - 1):
                T.append((base, base + j, base + j + 1) if tri[0] == 0 else
                         (base, base + j + 1, base + j))
    return V, np.array(T), UV


def merge(*parts):
    Vs, Ts, UVs, off = [], [], [], 0
    for V, T, UV in parts:
        Vs.append(V); Ts.append(T + off); UVs.append(UV); off += len(V)
    return np.vstack(Vs), np.vstack(Ts), np.vstack(UVs)


# ---------------------------------------------------------------- anatomia (m, nosso frame: z↑, +y frente)
def build():
    parts = {}    # name -> (V, T, UV)
    rig = []      # {name, parent, pivot}

    # ---- tronco: coluna corcunda contínua (bacia → pescoço)
    P = np.array([
        [0.000, 0.010, 0.980],    # bacia
        [0.000, 0.015, 1.060],    # anca
        [0.000, 0.010, 1.150],    # cintura (gaunt)
        [0.000, -0.005, 1.260],   # costelas
        [0.000, -0.045, 1.360],   # costelas altas (curva p/ trás)
        [0.000, -0.075, 1.430],   # ombros (corcunda)
        [0.000, -0.040, 1.480],   # base pescoço (juta p/ frente)
        [0.000, 0.030, 1.515],    # pescoço
    ])
    R = np.array([0.115, 0.105, 0.088, 0.108, 0.125, 0.140, 0.085, 0.055])
    E1 = np.array([1.25, 1.25, 1.25, 1.30, 1.32, 1.35, 1.10, 1.0])   # largura x
    E2 = np.array([0.85, 0.82, 0.80, 0.82, 0.85, 0.88, 0.95, 1.0])   # profundidade y
    V, T, UV = loft(P, R, E1, E2, n=28, noise=0.03)
    parts["torso"] = (V, T, UV)
    rig.append({"name": "torso", "parent": None, "pivot": [0, 0, 0.98]})

    # ---- cabeça alongada, inclinada p/ frente
    Hp = np.array([0.000, 0.055, 1.540])          # pivô na base do crânio
    d = np.array([0.0, np.sin(0.62), np.cos(0.62)])  # ~35° para a frente
    P = np.stack([Hp + s * d for s in (0.00, 0.05, 0.12, 0.20, 0.27)])
    R = np.array([0.070, 0.098, 0.108, 0.092, 0.055])
    E1 = np.array([0.95, 1.05, 1.10, 1.02, 0.85])
    V, T, UV = loft(P, R, E1, None, n=24, noise=0.025)
    parts["head"] = (V, T, UV)
    rig.append({"name": "head", "parent": "torso", "pivot": list(Hp)})

    # ---- mandíbula (pivô na dobradiça; abre p/ baixo)
    Jp = Hp + 0.10 * d
    P = np.stack([Jp + s * d + np.array([0, 0, -0.055]) for s in (0.00, 0.05, 0.11, 0.16)])
    R = np.array([0.052, 0.060, 0.052, 0.018])
    E1 = np.array([1.15, 1.2, 1.1, 0.9])
    V, T, UV = loft(P, R, E1, None, n=18, noise=0.02)
    parts["mandible"] = (V, T, UV)
    rig.append({"name": "mandible", "parent": "head", "pivot": list(Jp)})

    # cavidade da boca + dentes (2 fileiras) — filhos da cabeça
    cavity_c = Jp + 0.045 * d + np.array([0, 0.02, -0.01])
    Vc, Tc = sphere(cavity_c, 0.052, 10)
    parts["cavity"] = (Vc, Tc, np.zeros((len(Vc), 2)))
    rig.append({"name": "cavity", "parent": "head", "pivot": list(Hp)})
    teeth = []
    up = Jp + 0.055 * d + np.array([0, 0.025, 0.005])
    for row, dz in ((0, 0.030), (1, -0.038)):
        for i in range(9):
            a = (i / 8 - 0.5) * 1.35
            c = up + np.array([np.sin(a) * 0.038, np.cos(a) * 0.012, dz * (0.7 if row else 1.0)])
            vt = np.array([0.0, 0.0, -1.0]) if row == 0 else np.array([0.0, 0.0, 1.0])
            teeth.append(cone(c, 0.0062, 0.026 if row else 0.020, vt, 6))
    Vt = np.vstack([t[0] for t in teeth])
    offs = np.cumsum([0] + [len(tv[0]) for tv in teeth[:-1]])
    Tt = np.vstack([tv[1] + int(o) for tv, o in zip(teeth, offs)])
    parts["teeth"] = (Vt, Tt, np.zeros((len(Vt), 2)))
    rig.append({"name": "teeth", "parent": "head", "pivot": list(Hp)})

    # ---- olhos negros (embutidos, cor escura emissiva no site)
    for s, nm in ((1, "R"), (-1, "L")):
        e = Hp + 0.115 * d + np.array([s * 0.052, 0.010, 0.018])
        Ve, Te = sphere(e, 0.021, 10)
        parts["eye_" + nm] = (Ve, Te, np.zeros((len(Ve), 2)))
        rig.append({"name": "eye_" + nm, "parent": "head", "pivot": list(Hp)})

    # ---- membros: tubos enraizados DENTRO do tronco + esfera no pivô
    def limb(name, parent, pivot, A, B, r0, r1, ry=0.0, n=16, joint=True):
        """Segmento A→B (A dentro do pai); esfera no pivô A esconde a junção."""
        dirv = np.asarray(B, float) - np.asarray(A, float)
        L = np.linalg.norm(dirv)
        P = np.stack([A + (dirv) * f for f in (-0.12, 0.0, 0.35, 0.7, 1.0)])  # raiz para dentro
        R = np.array([r0, r0 * 0.97, (r0 + r1) / 2, r1 * 1.05, r1])
        V, T, UV = loft(P, R, None, None, n=n, noise=0.02)
        if joint:
            Vs, Ts = sphere(np.asarray(A, float), max(r0, r1) * 1.12, 9)
            V, T, UV = merge((V, T, UV), (Vs, Ts, np.zeros((len(Vs), 2))))
        parts[name] = (V, T, UV)
        rig.append({"name": name, "parent": parent, "pivot": list(map(float, pivot))})

    for s, nm in ((1, "R"), (-1, "L")):
        sh = np.array([s * 0.165, -0.06, 1.415])       # ombro
        el = sh + np.array([s * 0.06, -0.10, -0.335])  # cotovelo (levemente aberto)
        wr = el + np.array([s * 0.02, 0.06, -0.360])   # pulso (braços pendem p/ frente)
        limb("upperarm_" + nm, "torso", sh, sh + np.array([s * 0.05, -0.02, 0.06]), el, 0.048, 0.038)
        limb("forearm_" + nm, "upperarm_" + nm, el, el - (el - sh) * 0.05, wr, 0.038, 0.027)
        # mão: palma achatada + 4 dedos longos + polegar
        palm_d = (wr - el) / np.linalg.norm(wr - el)
        palm_c = wr + palm_d * 0.055
        hand = []
        Pp = np.stack([palm_c - palm_d * 0.04, palm_c + palm_d * 0.06])
        hand.append(loft(Pp, np.array([0.030, 0.024]), np.array([1.15, 1.1]), np.array([0.55, 0.5]), 12, noise=0.0))
        for k in range(4):
            base = palm_c + palm_d * 0.075 + np.array([s * (k - 1.5) * 0.016, 0, 0.004 * (k % 2)])
            fdir = palm_d + np.array([s * (k - 1.5) * 0.22, 0.18, -0.10])
            fdir /= np.linalg.norm(fdir)
            Pf = np.stack([base - fdir * 0.01, base + fdir * (0.13 - 0.012 * abs(k - 1.5))])
            hand.append(loft(Pf, np.array([0.0085, 0.0038]), None, None, 8, caps=True))
        base = palm_c - palm_d * 0.02 + np.array([s * 0.026, 0.01, 0.012])
        fdir = np.array([s * 0.8, 0.35, -0.3]); fdir /= np.linalg.norm(fdir)
        hand.append(loft(np.stack([base, base + fdir * 0.09]), np.array([0.0075, 0.0035]), None, None, 8))
        parts["hand_" + nm] = merge(*hand)
        rig.append({"name": "hand_" + nm, "parent": "forearm_" + nm, "pivot": list(map(float, wr))})

    for s, nm in ((1, "R"), (-1, "L")):
        hip = np.array([s * 0.062, 0.005, 0.965])
        knee = hip + np.array([s * 0.008, -0.045, -0.475])
        ankle = knee + np.array([0, 0.030, -0.445])
        limb("thigh_" + nm, "torso", hip, hip + np.array([0, 0, 0.06]), knee, 0.070, 0.050)
        limb("shin_" + nm, "thigh_" + nm, knee, knee - (knee - hip) * 0.04, ankle, 0.048, 0.033)
        # pé alongado + 3 garras
        foot = []
        Pd = np.stack([ankle, ankle + np.array([0, 0.13, -0.075]), ankle + np.array([0, 0.225, -0.085])])
        foot.append(loft(Pd, np.array([0.036, 0.030, 0.012]), np.array([1.0, 0.9, 0.8]), np.array([0.75, 0.55, 0.45]), 12))
        for k in range(3):
            b = Pd[2] + np.array([(k - 1) * 0.018, 0.02, 0.002])
            foot.append(cone(b, 0.009, 0.05, np.array([(k - 1) * 0.25, 1, -0.15]), 6))
        parts["foot_" + nm] = merge(*foot)
        rig.append({"name": "foot_" + nm, "parent": "shin_" + nm, "pivot": list(map(float, ankle))})
    return parts, rig


# ---------------------------------------------------------------- GLB multi-part com UV
def write_glb(parts, rig, path):
    def pad(x):
        return x + b"\x00" * ((4 - len(x) % 4) % 4)
    posA, nrmA, uvA, idxA, views, meshes, nodes = [], [], [], [], [], [], []
    binparts, offset = [], 0
    MAT = {"skin": 0, "eye": 1, "cavity": 2, "teeth": 3}
    for name, (V, T, UV) in parts.items():
        P = np.stack([-V[:, 0], V[:, 2], V[:, 1]], 1).astype(np.float32)   # nosso→glTF
        a, b, c = V[T[:, 0]], V[T[:, 1]], V[T[:, 2]]
        fn = np.cross(b - a, c - a)
        N = np.zeros_like(V)
        for k in range(3):
            np.add.at(N, T[:, k], fn)
        N /= np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-12)
        NN = np.stack([-N[:, 0], N[:, 2], N[:, 1]], 1).astype(np.float32)
        UU = np.asarray(UV, np.float32).reshape(-1, 2)
        I = T.astype(np.uint32).ravel()
        for arr in (P, NN, UU, I):
            raw = pad(arr.tobytes())
            views.append({"buffer": 0, "byteOffset": offset, "byteLength": len(arr.tobytes())})
            acc = {"bufferView": len(views) - 1, "count": len(arr)}
            if arr is P:
                acc.update({"componentType": 5126, "type": "VEC3", "min": P.min(0).tolist(), "max": P.max(0).tolist()})
                posA.append(acc)
            elif arr is NN:
                acc.update({"componentType": 5126, "type": "VEC3"}); nrmA.append(acc)
            elif arr is UU:
                acc.update({"componentType": 5126, "type": "VEC2"}); uvA.append(acc)
            else:
                acc.update({"componentType": 5125, "type": "SCALAR"}); idxA.append(acc)
            binparts.append(raw); offset += len(raw)
        mi = MAT["eye"] if name.startswith("eye") else MAT["cavity"] if name == "cavity" \
            else MAT["teeth"] if name == "teeth" else MAT["skin"]
        i = len(meshes)
        meshes.append({"name": name, "primitives": [{"attributes": {
            "POSITION": i, "NORMAL": len(posA) + len(nrmA) - len(nrmA) + i, "TEXCOORD_0": 2 * len(meshes) + i},
            "indices": 3 * len(meshes) + i, "material": mi}]})
        nodes.append({"mesh": i, "name": name})
    bin_ = b"".join(binparts)
    # fix accessors ABSOLUTOS: pos i, norm N+i, uv 2N+i, idx 3N+i
    nM = len(meshes)
    for i, m in enumerate(meshes):
        pr = m["primitives"][0]
        pr["attributes"]["POSITION"] = i
        pr["attributes"]["NORMAL"] = nM + i
        pr["attributes"]["TEXCOORD_0"] = 2 * nM + i
        pr["indices"] = 3 * nM + i
    textures = []
    for si in range(5):
        textures.append({"source": si})
    gltf = {
        "asset": {"version": "2.0", "generator": "hcg stalker2 (geometria própria)"},
        "scene": 0, "scenes": [{"nodes": list(range(len(nodes)))}],
        "nodes": nodes, "meshes": meshes,
        "materials": [
            {"name": "skin", "pbrMetallicRoughness": {"baseColorTexture": {"index": 2},
             "metallicRoughnessTexture": {"index": 3}, "metallicFactor": 0.05},
             "normalTexture": {"index": 1}, "occlusionTexture": {"index": 4, "strength": 0.9}},
            {"name": "eye", "pbrMetallicRoughness": {"baseColorFactor": [0.01, 0.0, 0.0, 1.0],
             "roughnessFactor": 0.12, "metallicFactor": 0.0},
             "emissiveFactor": [0.35, 0.02, 0.02]},
            {"name": "cavity", "pbrMetallicRoughness": {"baseColorFactor": [0.02, 0.0, 0.0, 1.0],
             "roughnessFactor": 0.95, "metallicFactor": 0.0}},
            {"name": "teeth", "pbrMetallicRoughness": {"baseColorFactor": [0.42, 0.36, 0.30, 1.0],
             "roughnessFactor": 0.45, "metallicFactor": 0.0}}],
        "textures": textures, "images": "IMAGES", "accessors": posA + nrmA + uvA + idxA,
        "bufferViews": views, "buffers": [{"byteLength": len(bin_)}],
    }
    return gltf, bin_, pad


def embed_images(gltf, bin_, texdir):
    from PIL import Image
    import io
    imgs = []
    newbin = bytearray(bin_)
    for fn in ("stalker_normal.png", "stalker_rough_metal.png", "stalker_albedo.png",
               "stalker_rough_metal.png", "stalker_ao.png"):
        data = open(os.path.join(texdir, fn), "rb").read()
        # normal e MR referenciados 2x → texturas distintas partilham a MESMA imagem
        imgs.append(("image/png", data))
    # imagens por bufferView novo
    views = []
    for (mime, data) in imgs:
        vi = len(gltf["bufferViews"])
        gltf["bufferViews"].append({"buffer": 0, "byteOffset": len(newbin), "byteLength": len(data)})
        newbin += data + b"\x00" * ((4 - len(data) % 4) % 4)
        views.append(vi)
    # texturas já existem (0..4) → sources correctos
    for i, t in enumerate(gltf["textures"]):
        t["source"] = i
    gltf["images"] = [{"mimeType": m, "bufferView": v} for (m, _), v in zip(imgs, views)]
    gltf["buffers"][0]["byteLength"] = len(newbin)
    return gltf, bytes(newbin)


def write_out(gltf, bin_, path):
    js = json.dumps(gltf).encode()
    js += b" " * ((4 - len(js) % 4) % 4)
    total = 12 + 8 + len(js) + 8 + len(bin_)
    hdr = struct.pack("<III", 0x46546C67, 2, total)
    open(path, "wb").write(hdr + struct.pack("<II", len(js), 0x4E4F534A) + js
                           + struct.pack("<II", len(bin_), 0x004E4942) + bin_)
    return total


def main():
    os.chdir(ROOT)
    parts, rig = build()
    for name, (V, T, UV) in parts.items():
        print(f"  {name:14} v={len(V):5} t={len(T):5}")
    tot_v = sum(len(p[0]) for p in parts.values())
    tot_t = sum(len(p[1]) for p in parts.values())
    print(f"TOTAL: {tot_v} verts, {tot_t} tris — CRIADO DE RAIO (zero modelos)")

    gltf, bin_, _ = write_glb(parts, rig, "")
    gltf, bin_ = embed_images(gltf, bin_, os.path.join(ROOT, "site", "textures"))
    n = write_out(gltf, bin_, os.path.join(OUT, "stalker2_smooth.glb"))
    import shutil
    shutil.copy(os.path.join(OUT, "stalker2_smooth.glb"), os.path.join(OUT, "stalker2_cage.glb"))
    print(f"stalker2_smooth.glb: {n/1e6:.2f} MB")

    # rig json (pivôs em frame GLB)
    rigg = [{"name": r["name"], "parent": r["parent"],
             "pivot": [-r["pivot"][0], r["pivot"][2], r["pivot"][1]]} for r in rig]
    json.dump({"rig": rigg}, open(os.path.join(OUT, "stalker2_rig.json"), "w"), indent=1)

    # ---- validação estrita + volume
    b = open(os.path.join(OUT, "stalker2_smooth.glb"), "rb").read()
    clen, _ = struct.unpack("<II", b[12:20])
    js = json.loads(b[20:20 + clen])
    off = 20 + clen
    blen, _ = struct.unpack("<II", b[off:off + 8])
    buf = b[off + 8:off + 8 + blen]
    for v in js["bufferViews"]:
        assert v["byteOffset"] + v["byteLength"] <= blen
    nT = len(js["textures"])
    for mat in js["materials"]:
        for key, t in list(mat.get("pbrMetallicRoughness", {}).items()) + list(mat.items()):
            if isinstance(t, dict) and "index" in t and "Texture" in key:
                assert t["index"] < nT, key
    print(f"VALIDAÇÃO: {len(js['meshes'])} meshes · {nT} texturas · views OK")

    # ---- painel de silhueta (auto-cheque)
    import sys
    sys.path.insert(0, os.path.join(ROOT, "tools", "refstudy"))
    from basemesh_proto import vertex_normals, render_view
    Vs, Ts, off_v = [], [], 0
    for V, T, UV in parts.values():
        Vs.append(V * 1000); Ts.append(T + off_v); off_v += len(V)
    V = np.vstack(Vs) * (1.0)      # mm
    T = np.vstack(Ts)
    V[:, 2] -= V[:, 2].min()
    N = vertex_normals(V, T)
    tiles = []
    for phi, name in ((0.0, "frente"), (np.pi / 2, "perfil"), (np.pi, "costas")):
        a = render_view(V, T, N, span=2100.0, zc=950.0, phi=phi, res=460)
        tiles.append((Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8), "L"), name))
    head = V[V[:, 2] > 1450]
    if len(head):
        zc = (head[:, 2].max() + 1450) / 2
        a = render_view(V, T, N, span=700.0, zc=zc, phi=0.15, res=460)
        tiles.append((Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8), "L"), "cabeça"))
    H = max(t[0].height for t in tiles) + 34
    W = sum(t[0].width for t in tiles) + 20 * (len(tiles) + 1)
    panel = Image.new("L", (W, H), 24)
    dr = ImageDraw.Draw(panel)
    x = 20
    for img, name in tiles:
        panel.paste(img, (x, 26)); dr.text((x + img.width // 2 - 24, 6), name, fill=230)
        x += img.width + 20
    panel.save(os.path.join(DOC, "stalker2_views.png"))
    print("painel →", os.path.join(DOC, "stalker2_views.png"))
    print(f"estatura construída: {V[:,2].max():.0f} mm (alvo ~1820)")


if __name__ == "__main__":
    main()
