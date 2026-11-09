# -*- coding: utf-8 -*-
"""WAIFU v2 — CABELO (bob) + VESTIDO (topo + saia A) + BOTAS + olhos de pestanejar.

Tudo derivado da PRÓPRIA geometria da waifu v1 (site/models/waifu_smooth.glb):
invólucros (shells) das zonas do corpo → ajuste PERFEITO por construção
(directriz CARNE LIGADA: as roupas seguem o corpo, sem ilhas).

Frame OURS (mm @1.58 m estatura, z↑, +y=frente) — igual ao glTF do site:
  x_our = x_g ; y_our = z_g (frente) ; z_our = y_g (altura) ; ×1000.

Peças (limites em mm @1.58):
  CABELO  bob: cz > 1330, MENOS a janela da cara (Ny > 0.25 frontal,
          1260 < cz < 1490, |cx| < 96) → franja acima dos olhos, cobre
          orelhas/nuvca até ao queixo; offset 12 mm (+4 no topo).
  VESTIDO topo: 790 < cz < 1140, |cx| < 350 (exclui braços) offset 8 mm.
  SAIA    cone A: anel da anca a z=776 amostrado em 48 ângulos, anéis
          776/690/615/545 com abertura 1.02/1.12/1.26/1.40 (doubleSided).
  BOTAS   zona do corpo cz < 300 (pés + cano até meio da canela).
  OLHOS   meshes kawaii_eye preservados (o site pestaneja por material).

Uso: python3 tools/waifu/build_waifu2.py   (numpy puro; sem Blender)
"""
import json
import os
import struct
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
SRC_GLB = os.path.join(ROOT, "site", "models", "waifu_smooth.glb")
WORK = os.path.join(ROOT, "out", "refstudy")
REF = os.path.join(ROOT, "tools", "refstudy")

HAIR = (0.23, 0.14, 0.10, 1.0)      # castanho quente
DRESS = (0.93, 0.55, 0.65, 1.0)     # rosa sakura
BOOT = (0.22, 0.14, 0.11, 1.0)      # chocolate escuro
SKIN = (1.00, 0.84, 0.77, 1.0)
EYE = (0.07, 0.08, 0.16, 1.0)
MOUTH = (0.90, 0.50, 0.55, 1.0)


# ---------------------------------------------------------------- glTF I/O
def read_glb(path):
    b = open(path, "rb").read()
    clen, _ = struct.unpack("<II", b[12:20])
    js = json.loads(b[20:20 + clen])
    off = 20 + clen
    blen, _ = struct.unpack("<II", b[off:off + 8])
    buf = b[off + 8:off + 8 + blen]
    def acc(aidx):
        a = js["accessors"][aidx]
        v = js["bufferViews"][a["bufferView"]]
        d = buf[v["byteOffset"]:v["byteOffset"] + v["byteLength"]]
        if a["type"] == "VEC3":
            return np.frombuffer(d, np.float32).reshape(-1, 3).astype(np.float64)
        dt = np.uint16 if a["componentType"] == 5123 else np.uint32
        return np.frombuffer(d, dt).reshape(-1, 3).astype(np.int64)
    out = []
    for mesh in js.get("meshes", []):
        for pr in mesh["primitives"]:
            mi = pr.get("material")
            mname = js["materials"][mi]["name"] if mi is not None else "skin"
            # glTF → nosso frame (mm).  Mapa PRÓPRIO (−x, z_g→y, y_g→z):
            # det=+1 (a permuta nua (x,z,y) é IMPROPRIA e inverteria o
            # winding — apanhado pelo volume assinado negativo).
            V = acc(pr["attributes"]["POSITION"]) * 1000.0
            V = np.stack([-V[:, 0], V[:, 2], V[:, 1]], 1)
            T = acc(pr["indices"])
            out.append((mesh.get("name", "mesh"), mname, V, T))
    return out


def write_glb_multi(prims, path):
    """prims: [(name, matname, rgba, doubleSided, V_mm_ours, T)] → GLB."""
    def pad(x):
        return x + b"\x00" * ((4 - len(x) % 4) % 4)
    pos_acc, nrm_acc, idx_acc, views, meshes, mats, nodes = [], [], [], [], [], [], []
    binparts, offset = [], 0
    matidx = {}
    for name, mname, rgba, dbl, V, T in prims:
        P = np.stack([-V[:, 0], V[:, 2], V[:, 1]], 1).astype(np.float32) / 1000.0
        a, b_, c = V[T[:, 0]], V[T[:, 1]], V[T[:, 2]]
        fn = np.cross(b_ - a, c - a)
        N = np.zeros_like(V)
        for k in range(3):
            np.add.at(N, T[:, k], fn)
        N /= np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-12)
        NN = np.stack([-N[:, 0], N[:, 2], N[:, 1]], 1).astype(np.float32)
        I = T.astype(np.uint32).ravel()
        for arr, comp, tp in ((P, 5126, "VEC3"), (NN, 5126, "VEC3"), (I, 5125, "SCALAR")):
            raw = pad(arr.tobytes())
            views.append({"buffer": 0, "byteOffset": offset, "byteLength": len(arr.tobytes())})
            a = {"bufferView": len(views) - 1, "componentType": comp,
                 "count": len(arr), "type": tp}
            if tp == "VEC3":
                a["min"] = arr.min(0).tolist(); a["max"] = arr.max(0).tolist()
            (pos_acc if comp == 5126 and tp == "VEC3" and arr is P else
             nrm_acc if comp == 5126 else idx_acc).append(a)
            binparts.append(raw); offset += len(raw)
        if mname not in matidx:
            matidx[mname] = len(mats)
            mats.append({"name": mname, "doubleSided": bool(dbl),
                         "pbrMetallicRoughness": {"baseColorFactor": list(rgba),
                                                   "metallicFactor": 0.0,
                                                   "roughnessFactor": 0.65}})
        meshes.append({"name": name, "primitives": [{
            "attributes": {"POSITION": len(pos_acc) - 1,
                           "NORMAL": len(nrm_acc) - 1},
            "indices": len(idx_acc) - 1, "material": matidx[mname]}]})
        nodes.append({"mesh": len(meshes) - 1, "name": name})
    bin_ = b"".join(binparts)
    # accessors = pos_acc + nrm_acc + idx_acc (concatenação) → os índices
    # RELATIVOS de NORMAL/indices têm de ser corrigidos para ABSOLUTOS.
    nP, nN = len(pos_acc), len(nrm_acc)
    for i, m in enumerate(meshes):
        pr = m["primitives"][0]
        pr["attributes"]["POSITION"] = i                     # pos_acc[i]
        pr["attributes"]["NORMAL"] = nP + i                  # nrm_acc[i]
        pr["indices"] = nP + nN + i                          # idx_acc[i]
    gltf = {"asset": {"version": "2.0", "generator": "hcg waifu v2"},
            "scene": 0, "scenes": [{"nodes": list(range(len(nodes)))}],
            "nodes": nodes, "meshes": meshes, "materials": mats,
            "accessors": pos_acc + nrm_acc + idx_acc, "bufferViews": views,
            "buffers": [{"byteLength": len(bin_)}]}
    js = json.dumps(gltf).encode()
    js += b" " * ((4 - len(js) % 4) % 4)
    hdr = struct.pack("<III", 0x46546C67, 2, 12 + 8 + len(js) + 8 + len(bin_))
    open(path, "wb").write(hdr + struct.pack("<II", len(js), 0x4E4F534A) + js
                           + struct.pack("<II", len(bin_), 0x004E4942) + bin_)
    return len(bin_)


# ---------------------------------------------------------------- peças
def shell(V, T, mask, offset_fn):
    """Copia triângulos mask e desloca cada vértice ao longo da normal."""
    sys.path.insert(0, REF)
    from basemesh_proto import vertex_normals
    N = vertex_normals(V, T)
    idx = np.where(mask)[0]
    verts = np.unique(T[idx])
    off = np.broadcast_to(np.asarray(offset_fn(V[verts]), float), (len(verts),))
    Vn = V[verts] + N[verts] * off[:, None]
    remap = -np.ones(len(V), int)
    remap[verts] = np.arange(len(verts))
    Tn = remap[T[idx]]
    return Vn, Tn


def ring_at(V, T, z0, n=48):
    """Contorno (x,y) da secção do corpo em z0, re-amostrado em n ângulos."""
    pts = []
    for tri in T:
        for i in range(3):
            p, q = V[tri[i]], V[tri[(i + 1) % 3]]
            if (p[2] - z0) * (q[2] - z0) < 0:
                t = (z0 - p[2]) / (q[2] - p[2])
                pts.append(p[:2] + (q[:2] - p[:2]) * t)
    pts = np.unique(np.round(np.array(pts), 1), axis=0)
    ang = np.sort(np.arctan2(pts[:, 1], pts[:, 0]))
    # re-amostra n ângulos uniformes interpolando raio
    th = np.linspace(-np.pi, np.pi, n, endpoint=False)
    def radius(a):
        a = (a - ang.min()) % (2 * np.pi) + ang.min()
        i = np.searchsorted(ang, a)
        i0, i1 = ang[(i - 1) % len(ang)], ang[i % len(ang)]
        r0 = np.interp(i0, ang, np.hypot(*(pts.T)))
        r1 = np.interp(i1, ang, np.hypot(*(pts.T)))
        w = 0 if i1 == i0 else (a - i0) / (i1 - i0)
        return r0 + (r1 - r0) * w
    rr = np.array([np.interp((a - ang.min()) % (2 * np.pi) + ang.min(), ang,
                             np.hypot(pts[:, 0], pts[:, 1])) for a in th])
    return th, rr


def skirt(z0=776.0, zs=(776.0, 690.0, 615.0, 545.0), ss=(1.02, 1.12, 1.26, 1.40), n=48):
    """Saia A: anéis amostrados do contorno da anca, abertura crescente."""
    th, r = ring_at(BODY_V, BODY_T, z0, n)
    cy = np.mean(r * np.sin(th))            # centro y do anel (frente+)
    rings = [np.stack([r * np.cos(th) * s, (r * np.sin(th) - cy) * s + cy,
                       np.full(n, z)], 1) for z, s in zip(zs, ss)]
    V = np.vstack(rings)                    # (len(zs)*n, 3)
    T = []
    for k in range(len(zs) - 1):
        for i in range(n):
            j = (i + 1) % n
            a, b_ = k * n + i, k * n + j
            c, d = (k + 1) * n + j, (k + 1) * n + i
            T += [(a, b_, c), (a, c, d)]
    return V, np.array(T)


# ---------------------------------------------------------------- main
BODY_V = BODY_T = None

def main():
    global BODY_V, BODY_T
    prims_in = read_glb(SRC_GLB)
    print("primitivas do v1:", [(n, m, len(V)) for n, m, V, T in prims_in])

    # o corpo vem EM VÁRIAS primitivas (costura do Mirror) → fundir
    bodyprims = [p for p in prims_in if p[0] == "Anime_Female_A"]
    assert bodyprims, "corpo não encontrado no GLB"
    Vs, Ts, off = [], [], 0
    for _, _, V, T in bodyprims:
        Vs.append(V); Ts.append(T + off); off += len(V)
    BODY_V, BODY_T = np.vstack(Vs), np.vstack(Ts)
    others = [p for p in prims_in if p[0] != "Anime_Female_A"]
    print(f"corpo fundido: {len(BODY_V)} verts, {len(BODY_T)} tris")

    # ---------- botas: zona do corpo z < 300
    cz = BODY_V[BODY_T].mean(1)[:, 2]
    boot_mask = cz < 300.0
    skin_mask = ~boot_mask
    print(f"botas: {boot_mask.sum()} tris | pele: {skin_mask.sum()} tris")

    # ---------- cabelo bob
    fn = np.cross(BODY_V[BODY_T[:, 1]] - BODY_V[BODY_T[:, 0]],
                  BODY_V[BODY_T[:, 2]] - BODY_V[BODY_T[:, 0]])
    fn /= np.maximum(np.linalg.norm(fn, axis=1, keepdims=True), 1e-12)
    cc = BODY_V[BODY_T].mean(1)
    face_win = (fn[:, 1] > 0.25) & (cc[:, 2] > 1260) & (cc[:, 2] < 1490) & (np.abs(cc[:, 0]) < 96)
    hair_mask = (cc[:, 2] > 1330) & ~face_win
    print(f"cabelo: {hair_mask.sum()} tris (cara excluída: {face_win.sum()})")

    # ---------- vestido topo
    dress_mask = (cc[:, 2] > 790) & (cc[:, 2] < 1140) & (np.abs(cc[:, 0]) < 350)
    print(f"vestido topo: {dress_mask.sum()} tris")

    Vh, Th = shell(BODY_V, BODY_T, hair_mask,
                   lambda v: 12.0 + 4.0 * (v[:, 2] > 1530))
    Vd, Td = shell(BODY_V, BODY_T, dress_mask, lambda v: 8.0)
    Vs, Ts = skirt()
    # winding da saia: normal do 1.º tri deve apontar PARA FORA (+x radial)
    fn0 = np.cross(Vs[Ts[0, 1]] - Vs[Ts[0, 0]], Vs[Ts[0, 2]] - Vs[Ts[0, 0]])
    if fn0 @ np.array([1.0, 0.0, 0.0]) < 0:
        Ts = Ts[:, [0, 2, 1]]

    # botas/pele: dividir o corpo em 2 prims (mesmos vértices)
    sys.path.insert(0, REF)
    from basemesh_proto import vertex_normals
    Nb = vertex_normals(BODY_V, BODY_T)

    prims = [
        ("body_skin", "kawaii_skin", SKIN, False, BODY_V, BODY_T[skin_mask]),
        ("body_boot", "kawaii_boot", BOOT, False, BODY_V, BODY_T[boot_mask]),
        ("hair", "kawaii_hair", HAIR, False, Vh, Th),
        ("dress_top", "kawaii_dress", DRESS, False, Vd, Td),
        ("skirt", "kawaii_dress", DRESS, True, Vs, Ts),
    ]
    for name, m, V, T in others:
        rgba = EYE if "eye" in m else MOUTH if "mouth" in m else SKIN
        prims.append((name + "_v1", m, rgba, False, V, T))

    out = os.path.join(ROOT, "site", "models")
    for mesh in ("smooth", "cage"):
        nb = write_glb_multi(prims, os.path.join(out, f"waifu2_{mesh}.glb"))
        print(f"waifu2_{mesh}.glb: {nb/1e6:.2f} MB")

    # ---------- medidas (corpo + partes v1, SEM roupa) + painel
    from basemesh_proto import measure, render_view, vertex_normals as vn
    Vs_all = [BODY_V] + [p[2] for p in others]
    Ts_all, off = [], 0
    for V, T in [(BODY_V, BODY_T)] + [(p[2], p[3]) for p in others]:
        Ts_all.append(T + off); off += len(V)
    V = np.vstack(Vs_all); T = np.vstack(Ts_all)
    os.makedirs(WORK, exist_ok=True)
    np.savez(os.path.join(WORK, "raw_waifu02.npz"), V=V, T=T)
    med = measure(V, T)
    print("waifu02 medidas:", {k: (tuple(np.round(v, 1)) if isinstance(v, tuple)
                                    else round(float(v), 1)) for k, v in med.items()})

    # painel: TUDO (roupa incluída — é o que se VÊ)
    Vp = np.vstack([BODY_V, Vh, Vd, Vs] + [p[2] for p in others])
    Tp = np.vstack([BODY_T, Th, Td, Ts] + [p[3] + len(BODY_V) for p in others])
    # (índices de Th/Td/Ts já são locais; ajustar offsets)
    Tp = np.vstack([BODY_T,
                    Th + len(BODY_V),
                    Td + len(BODY_V) + len(Vh),
                    Ts + len(BODY_V) + len(Vh) + len(Vd)]
                   + [p[3] + len(BODY_V) + len(Vh) + len(Vd) + len(Vs) for p in others])
    N = vn(Vp, Tp)
    from PIL import Image, ImageDraw
    tiles = []
    for phi, name in ((0.0, "frente"), (np.pi / 2, "perfil"), (np.pi, "costas")):
        a = render_view(Vp, Tp, N, span=1000.0, zc=850.0, phi=phi, res=460)
        tiles.append((Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8), "L"), name))
    H = max(t[0].height for t in tiles) + 34
    W = sum(t[0].width for t in tiles) + 80
    panel = Image.new("L", (W, H), 24)
    dr = ImageDraw.Draw(panel)
    x = 20
    for img, name in tiles:
        panel.paste(img, (x, 26))
        dr.text((x + img.width // 2 - 20, 6), name, fill=230)
        x += img.width + 20
    os.makedirs(os.path.join(ROOT, "docs", "head_phaseA"), exist_ok=True)
    panel.save(os.path.join(ROOT, "docs", "head_phaseA", "waifu_v2.png"))
    print("painel → docs/head_phaseA/waifu_v2.png", panel.size)

    json.dump({"measures": {k: (list(v) if isinstance(v, tuple) else round(float(v), 2))
                            for k, v in med.items()},
               "verts": int(len(V)), "tris": int(len(T)),
               "clothes": {"hair": int(len(Th)), "dress_top": int(len(Td)),
                           "skirt": int(len(Ts)), "boot": int(boot_mask.sum())},
               "colors": {"hair": list(HAIR), "dress": list(DRESS), "boot": list(BOOT)}},
              open(os.path.join(WORK, "waifu_v2.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
