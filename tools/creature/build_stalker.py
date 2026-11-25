# -*- coding: utf-8 -*-
"""THE STALKER — O Encharcado: texturas PBR geradas + transplante para o rig.

Directriz do dono (2026-09-24): monstro de terror PSX moderno sujo —
"gera as texturas com gerador de imagem... profundidade PBR e realismo
mas com o nosso estilo PSX moderno mas sujo".

Pipeline (nada fingido — os mapas são COMPUTADOS, não RGB fingido):
  1. texturas geradas por IA: albedo + height (site/textures/stalker_*.png);
  2. NORMAL: Sobel do height (tangent-space, k=2.2);
  3. ROUGHNESS: 0.88 base, zonas húmidas (escuras+coradas = secreção) → 0.25
     (a secreção brilha); empacotado em metallicRoughness (G=rough, B=0);
  4. AO: height invertido (cavidades escuras) — canal R;
  5. PSX: 512px + posterização 32 níveis + dither Bayer 4x4;
  6. GLB: Michelle (rig Mixamo + SambaDance) com as 3 imagens substituídas
     + occlusionTexture adicionada — reconstrução byte a byte (offsets
     recomputados por ordem; JSON acochado com ESPAÇOS — lição registada).

Uso: python3 tools/creature/build_stalker.py
"""
import io
import json
import os
import shutil
import struct

import numpy as np
from PIL import Image, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
SRC = "/tmp/threejs/examples/models/gltf/Michelle.glb"
TEX = os.path.join(ROOT, "site", "textures")
OUT = os.path.join(ROOT, "site", "models")
PSX = 512
BAYER = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) / 16.0


def psx(im):
    """512px + posterização 32 níveis + dither Bayer (o 'sujo' PSX)."""
    a = np.asarray(im.convert("RGB").resize((PSX, PSX), Image.LANCZOS)).astype(np.float32)
    b = np.tile(BAYER, (PSX // 4 + 1, PSX // 4 + 1))[:PSX, :PSX]
    q = 255.0 / 31.0
    a = np.clip(np.floor(a / q + b[..., None] * 0.6) * q, 0, 255)
    return a.astype(np.uint8)


def load_gray(path):
    return np.asarray(Image.open(path).convert("L").resize((PSX, PSX), Image.LANCZOS)).astype(np.float32) / 255.0


def normal_from_height(h, k=2.2):
    gx = np.zeros_like(h); gy = np.zeros_like(h)
    gx[1:-1, 1:-1] = (h[1:-1, 2:] - h[1:-1, :-2]) * 0.5
    gy[1:-1, 1:-1] = (h[2:, 1:-1] - h[:-2, 1:-1]) * 0.5
    nx, ny, nz = -k * gx, -k * gy, np.ones_like(h)
    n = np.sqrt(nx * nx + ny * ny + nz * nz)
    return np.stack([0.5 + 0.5 * nx / n, 0.5 + 0.5 * ny / n, 0.5 + 0.5 * nz / n], -1)


def maps():
    alb = psx(Image.open(os.path.join(TEX, "stalker_albedo.png")))
    h = load_gray(os.path.join(TEX, "stalker_height.png"))
    nrm = (normal_from_height(h) * 255).astype(np.uint8)
    a = alb.astype(np.float32) / 255.0
    lum = a @ np.array([0.299, 0.587, 0.114])
    sat = a.max(2) - a.min(2)
    wet = ((lum < 0.30) & (sat > 0.25)).astype(np.uint8) * 255
    wet = np.asarray(Image.fromarray(wet).filter(ImageFilter.GaussianBlur(3))).astype(np.float32) / 255.0
    rough = np.clip(0.88 - 0.63 * wet, 0, 1)
    mr = np.zeros((PSX, PSX, 3), np.uint8)
    mr[..., 1] = (rough * 255).astype(np.uint8)
    hn = (h - h.min()) / max(h.max() - h.min(), 1e-6)
    ao = np.clip(1.0 - 0.55 * hn ** 0.7, 0, 1)
    aoimg = np.stack([((ao ** 0.5) * 255).astype(np.uint8)] * 3, -1)
    for name, arr in (("stalker_normal.png", nrm), ("stalker_rough_metal.png", mr),
                      ("stalker_ao.png", aoimg)):
        Image.fromarray(arr).save(os.path.join(TEX, name))
    print(f"mapas: wet {wet.mean():.1%} · rough médio {rough.mean():.2f} · normal+AO ok")
    return alb, nrm, mr, aoimg


def png_bytes(arr):
    b = io.BytesIO()
    Image.fromarray(arr).save(b, format="PNG")
    return b.getvalue()


def pad4(x):
    return x + b"\x00" * ((4 - len(x) % 4) % 4)


def rebuild(src, out, replacements, extra_images):
    """replacements: {image_index: bytes}; extras: [(bytes, mime)] → novos índices."""
    b = open(src, "rb").read()
    clen, _ = struct.unpack("<II", b[12:20])
    js = json.loads(b[20:20 + clen])
    off = 20 + clen
    blen, _ = struct.unpack("<II", b[off:off + 8])
    bin_ = b[off + 8:off + 8 + blen]

    new_data = {}
    for idx, data in replacements.items():
        bv = js["bufferViews"][js["images"][idx]["bufferView"]]
        new_data[bv["byteOffset"]] = pad4(data)
        bv["byteLength"] = len(data)
    lengths = {v["byteOffset"]: v["byteLength"] for v in js["bufferViews"]}
    old_offsets = sorted(set(list(lengths.keys()) + list(new_data.keys())))

    off_map, cur, parts = {}, 0, []
    for o in old_offsets:
        off_map[o] = cur
        d = new_data[o] if o in new_data else pad4(bin_[o:o + lengths.get(o, 0)])
        parts.append(d)
        cur += len(d)
    newbin = b"".join(parts)

    tex_indices = []
    for data, mime in extra_images:
        vi = len(js["bufferViews"])
        js["bufferViews"].append({"buffer": 0, "byteOffset": len(newbin), "byteLength": len(data)})
        newbin += pad4(data)
        js["images"].append({"mimeType": mime, "bufferView": vi})
        # glTF: materiais referem TEXTURES (que referem images) — nunca
        # imagens directamente (bug 2026-09-24: occlusionTexture.index=4
        # apontava para image → GLTFLoader falhava → stalker invisível).
        js["textures"].append({"source": len(js["images"]) - 1})
        tex_indices.append(len(js["textures"]) - 1)

    for v in js["bufferViews"]:
        if v["byteOffset"] in off_map:      # extras (AO) já têm offset final
            v["byteOffset"] = off_map[v["byteOffset"]]
    js["buffers"][0]["byteLength"] = len(newbin)
    js["materials"][0]["metallicFactor"] = 0.05
    if tex_indices:
        js["materials"][0]["occlusionTexture"] = {"index": tex_indices[0], "strength": 0.9}

    jsb = json.dumps(js).encode()
    jsb += b" " * ((4 - len(jsb) % 4) % 4)          # ESPAÇOS (nunca NUL)
    total = 12 + 8 + len(jsb) + 8 + len(newbin)
    hdr = struct.pack("<III", 0x46546C67, 2, total)
    open(out, "wb").write(hdr + struct.pack("<II", len(jsb), 0x4E4F534A) + jsb
                          + struct.pack("<II", len(newbin), 0x004E4942) + newbin)
    return total


def main():
    os.chdir(ROOT)
    alb, nrm, mr, ao = maps()
    n = rebuild(SRC, os.path.join(OUT, "stalker_smooth.glb"),
                {2: png_bytes(alb), 1: png_bytes(nrm), 3: png_bytes(mr)},
                [(png_bytes(ao), "image/png")])
    print(f"stalker_smooth.glb: {n/1e6:.2f} MB")
    shutil.copy(os.path.join(OUT, "stalker_smooth.glb"), os.path.join(OUT, "stalker_cage.glb"))
    shutil.copy("/tmp/threejs/examples/models/gltf/Xbot.glb", os.path.join(OUT, "anim_xbot.glb"))

    b = open(os.path.join(OUT, "stalker_smooth.glb"), "rb").read()
    clen, _ = struct.unpack("<II", b[12:20])
    js = json.loads(b[20:20 + clen])
    off = 20 + clen
    blen, _ = struct.unpack("<II", b[off:off + 8])
    for v in js["bufferViews"]:
        assert v["byteOffset"] + v["byteLength"] <= blen, "view fora do buffer"
    nT = len(js.get("textures", []))
    for mi, mat in enumerate(js["materials"]):
        pbr = mat.get("pbrMetallicRoughness", {})
        for key, t in list(pbr.items()) + list(mat.items()):
            if isinstance(t, dict) and "index" in t and "Texture" in key:
                assert t["index"] < nT, f"material {mi}.{key}: texture index inválido"
        for t in js.get("textures", []):
            assert t["source"] < len(js["images"]), "texture.source inválido"
    names = [nd.get("name", "?") for nd in js["nodes"]]
    joints = [names[j] for j in js["skins"][0]["joints"]]
    print("VALIDAÇÃO OK · anims:", [a["name"] for a in js["animations"]])
    print("ossos chave:", [j for j in joints if any(k in j.lower() for k in
          ("spine", "head", "neck", "arm", "hand", "leg", "hips"))][:16])
    os.makedirs(os.path.join(ROOT, "out", "refstudy"), exist_ok=True)
    json.dump({"bones": joints, "anims": [a["name"] for a in js["animations"]]},
              open(os.path.join(ROOT, "out", "refstudy", "stalker_rig.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
