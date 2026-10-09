# -*- coding: utf-8 -*-
"""EXPORTA os corpos do caminho A como GLB (visualizador do site = o 'botão').

Escreve GLB minimal (glTF 2.0: positions+normals+indices) para site/models e
regista as variants em out/preview/models/models.json (fonte do build_site) —
sobrevive a rebuilds.  Transform ours(z-up, +y frente) → glTF(y-up, +z frente):
(x,y,z)→(−x, z, y)  [right-handed; winding invertido ⇒ índices revertidos].

Uso: python3 tools/refstudy/basemesh_glb.py
"""
import hashlib
import json
import os
import struct
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
WORK = os.path.join(ROOT, "out", "refstudy")
SITE_M = os.path.join(ROOT, "site", "models")
OUT_M = os.path.join(ROOT, "out", "preview", "models")

BODIES = [  # (id, label, desc)
    ("m00", "A·BASE (Female base CC0)",
     "Fundação anatómica do caminho A (REF-F-REAL-001, 18577 verts) — sem "
     "morphs. Mama já em banda refs (gap 20.5)."),
    ("w02", "A·seed 202 (largo)",
     "Morphs A.1 amplitudes largas: estatura 1607, cintura 209, WHR 0.67, "
     "mama+. VARIANTE VISÍVEL."),
    ("w03", "A·seed 303 (largo)",
     "Morphs A.1: estatura 1566 (baixa), cintura 194, anca 291 — compacta."),
    ("w05", "A·seed 505 (largo)",
     "Morphs A.1: estatura 1764, cintura 317, anca 328, mama++ — robusta."),
]


def write_glb(V_m, T, N, path):
    """GLB glTF 2.0 minimal.  V/T/N no frame OURS (mm, z-up)."""
    P = np.stack([-V_m[:, 0], V_m[:, 2], V_m[:, 1]], 1).astype(np.float32) / 1000.0
    NN = np.stack([-N[:, 0], N[:, 2], N[:, 1]], 1).astype(np.float32)
    NN /= np.maximum(np.linalg.norm(NN, axis=1, keepdims=True), 1e-12)
    I = T[:, ::-1].astype(np.uint32).ravel()          # winding invertido

    def pad(b):
        return b + b"\x00" * ((4 - len(b) % 4) % 4)

    # glTF spec: chunk JSON acochoado com ESPAÇOS (0x20); BIN com NUL.
    # (bug 2026-10-09: NUL no JSON → JSON.parse do three.js lança SyntaxError
    #  → corpos novos nunca carregaram no browser; spinner eterno. FIX.)
    def pad_js(b):
        return b + b" " * ((4 - len(b) % 4) % 4)

    bin_ = pad(P.tobytes()) + pad(NN.tobytes()) + pad(I.tobytes())
    nv, ni = len(P), len(I)
    views = [
        {"buffer": 0, "byteOffset": 0, "byteLength": len(P.tobytes())},
        {"buffer": 0, "byteOffset": len(pad(P.tobytes())), "byteLength": len(NN.tobytes())},
        {"buffer": 0, "byteOffset": len(pad(P.tobytes())) + len(pad(NN.tobytes())),
         "byteLength": len(I.tobytes())},
    ]
    gltf = {
        "asset": {"version": "2.0", "generator": "hcg basemesh A"},
        "scene": 0,
        "scenes": [{"nodes": [0]}],
        "nodes": [{"mesh": 0, "name": "body"}],
        "meshes": [{"primitives": [{"attributes": {"POSITION": 0, "NORMAL": 1},
                                     "indices": 2}]}],
        "accessors": [
            {"bufferView": 0, "componentType": 5126, "count": nv, "type": "VEC3",
             "min": P.min(0).tolist(), "max": P.max(0).tolist()},
            {"bufferView": 1, "componentType": 5126, "count": nv, "type": "VEC3"},
            {"bufferView": 2, "componentType": 5125, "count": ni, "type": "SCALAR"},
        ],
        "bufferViews": views,
        "buffers": [{"byteLength": len(bin_)}],
    }
    js = pad_js(json.dumps(gltf).encode())
    hdr = struct.pack("<III", 0x46546C67, 2, 12 + 8 + len(js) + 8 + len(bin_))
    out = hdr + struct.pack("<II", len(js), 0x4E4F534A) + js + \
        struct.pack("<II", len(bin_), 0x004E4942) + bin_
    open(path, "wb").write(out)
    return nv, len(I) // 3, len(out)


def digest(V, T):
    h = hashlib.sha256()
    h.update(np.ascontiguousarray(V, np.float32).tobytes())
    h.update(np.ascontiguousarray(T, np.int64).tobytes())
    return h.hexdigest()[:16]


def main():
    os.makedirs(SITE_M, exist_ok=True)
    os.makedirs(OUT_M, exist_ok=True)
    sys.path.insert(0, HERE)
    from basemesh_proto import vertex_normals

    manifest = []
    for bid, label, desc in BODIES:
        d = np.load(os.path.join(WORK, f"raw_{bid}.npz"))
        V, T = d["V"].astype(float), d["T"]
        N = vertex_normals(V, T)
        dg = digest(V, T)
        row = {"id": bid, "label": label, "env": {"HCG_BODY": "basemesh"},
               "commit": "basemesh-A.1", "digest": dg, "desc": desc}
        for mesh in ("smooth", "cage"):     # mesmo ficheiro nos dois slots
            p = os.path.join(SITE_M, f"{bid}_{mesh}.glb")
            nv, nf, nb = write_glb(V, T, N, p)
            row[mesh] = {"verts": nv, "faces": nf, "quads": 0, "bytes": nb}
        manifest.append(row)
        print(f"GLB {bid}: v={nv} f={nf} {nb/1e6:.1f}MB digest={dg}")

    # regista nas DUAS fontes (site vivo + out/preview p/ futuros builds)
    for mp in (os.path.join(OUT_M, "models.json"),):
        cur = json.load(open(mp)) if os.path.exists(mp) else []
        cur = [v for v in cur if v["id"] not in {r["id"] for r in manifest}] + manifest
        json.dump(cur, open(mp, "w"), indent=1)
    dj = os.path.join(ROOT, "site", "data", "data.json")
    d = json.load(open(dj))
    d["variants"] = [v for v in d["variants"] if v["id"] not in {r["id"] for r in manifest}] \
        + manifest
    json.dump(d, open(dj, "w"), indent=1, ensure_ascii=False)
    print("variants registadas:", [r["id"] for r in manifest])


if __name__ == "__main__":
    main()
