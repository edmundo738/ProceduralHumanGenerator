# -*- coding: utf-8 -*-
"""WAIFU v3 — assets BAIXADOS da net (three.js repo, MIT) + PELE NEGRA na textura.

Fontes (github.com/mrdoob/three.js, exemplos MIT):
  Michelle.glb — rapariga com cabelo+roupa reais, texturas, esqueleto e clip
                 'SambaDance' EMBUTIDO (dança!);
  Xbot.glb     — 7 clips (idle/walk/run/agree/headShake/sad/sneak) p/ retarget.

Este script recolore a PELE do Michelle para NEGRA dentro do atlas albedo
(máscara de pele clássica + multiplicação que preserva o sombreado — a roupa
e o cabelo ficam intactos) e reconstrói o GLB byte a byte (só a imagem muda;
esqueleto/animações/materials preservados).

Uso: python3 tools/waifu/skin_negra.py
"""
import json
import struct

import numpy as np
from PIL import Image, ImageFilter

SRC = "/tmp/threejs/examples/models/gltf/Michelle.glb"
OUT = "site/models/waifu3_smooth.glb"
ALBEDO_IMG = 2            # pbrMetallicRoughness.baseColorTexture.index
DARK = np.array([0.40, 0.29, 0.24])   # multiplicador → castanho profundo


def recolor(im):
    a = np.asarray(im.convert("RGBA")).astype(np.float32)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    mx, mn = a[..., :3].max(2), a[..., :3].min(2)
    skin = ((r > 95) & (g > 40) & (b > 20) & ((mx - mn) > 15) &
            (r > g) & (g > b) & ((np.abs(r - g)) > 15))
    frac = skin.mean()
    mask = Image.fromarray((skin * 255).astype(np.uint8), "L").filter(
        ImageFilter.GaussianBlur(1.5))
    m = np.asarray(mask).astype(np.float32)[..., None] / 255.0
    dark = a[..., :3] * DARK
    a[..., :3] = a[..., :3] * (1 - m) + dark * m
    print(f"pele recolorida: {frac:.1%} dos pixels → NEGRA (multiplicador {DARK})")
    return Image.fromarray(a.astype(np.uint8), "RGBA")


def rebuild(path_in, path_out):
    b = open(path_in, "rb").read()
    clen, _ = struct.unpack("<II", b[12:20])
    js = json.loads(b[20:20 + clen])
    off = 20 + clen
    blen, _ = struct.unpack("<II", b[off:off + 8])
    bin_ = bytearray(b[off + 8:off + 8 + blen])

    iv = js["bufferViews"][js["images"][ALBEDO_IMG]["bufferView"]]
    old = bytes(bin_[iv["byteOffset"]:iv["byteOffset"] + iv["byteLength"]])
    im = recolor(Image.frombytes("RGBA", (0, 0)) if False else Image.open(
        __import__("io").BytesIO(old)))
    buf = __import__("io").BytesIO()
    im.save(buf, format="PNG")
    new = buf.getvalue()
    new_pad = new + b"\x00" * ((4 - len(new) % 4) % 4)
    old_pad_len = (iv["byteLength"] + 3) // 4 * 4
    delta = len(new_pad) - old_pad_len
    # reconstrói o BIN: mantém tudo, substitui a imagem, desloca as views seguintes
    nb = bytearray(bin_[:iv["byteOffset"]]) + bytearray(new_pad) + \
        bytearray(bin_[iv["byteOffset"] + old_pad_len:])
    for v in js["bufferViews"]:
        if v["byteOffset"] > iv["byteOffset"]:
            v["byteOffset"] += delta
    iv["byteLength"] = len(new)
    js["buffers"][0]["byteLength"] = len(nb)

    jsb = json.dumps(js).encode()
    jsb += b" " * ((4 - len(jsb) % 4) % 4)
    total = 12 + 8 + len(jsb) + 8 + len(nb)
    hdr = struct.pack("<III", 0x46546C67, 2, total)
    open(path_out, "wb").write(hdr + struct.pack("<II", len(jsb), 0x4E4F534A)
                               + jsb + struct.pack("<II", len(nb), 0x004E4942) + bytes(nb))
    return total


if __name__ == "__main__":
    import os
    os.chdir(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    #Michelle original → site/models (anim_xbot p/ retarget também)
    import shutil
    shutil.copy("/tmp/threejs/examples/models/gltf/Xbot.glb", "site/models/anim_xbot.glb")
    shutil.copy("/tmp/threejs/examples/models/gltf/Soldier.glb", "site/models/anim_soldier.glb")
    n = rebuild(SRC, OUT)
    print(f"waifu3_smooth.glb: {n/1e6:.2f} MB")
    shutil.copy(OUT, "site/models/waifu3_cage.glb")
    # guarda os originais na biblioteca de assets (permanente no git)
    os.makedirs("references/female/stylized/downloaded_assets", exist_ok=True)
    shutil.copy("/tmp/threejs/examples/models/gltf/Michelle.glb",
                "references/female/stylized/downloaded_assets/Michelle_original.glb")
    with open("references/female/stylized/downloaded_assets/LICENSES.txt", "w") as f:
        f.write(
            "Assets baixados do repositorio mrdoob/three.js (MIT) em 2026-09-24:\n"
            "- Michelle.glb: modelo de personagem feminina (exemplos three.js)\n"
            "- Xbot.glb: 7 clips de animacao (idle/walk/run/agree/headShake/sad/sneak)\n"
            "- Soldier.glb: clips Idle/Walk/Run/TPose\n"
            "Fonte: https://github.com/mrdoob/three.js (examples/models/gltf)\n"
            "Licenca do repositorio: MIT. Creditos dos modelos: Mixamo/three.js.\n"
            "Michelle com pele recolorida para negra (skin_negra.py) = waifu3.\n")
    print("assets originais arquivados em references/female/stylized/downloaded_assets/")
