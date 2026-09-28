# -*- coding: utf-8 -*-
"""REFERENCE LIBRARY — índice, validação e guarda da política git (híbrida).

Percorre references/, valida cada meta.json (schema.py), agrega tamanhos e
sha256 e escreve references/INDEX.json.  Política híbrida (dono, 2026-09-28):
commitar até ~300 MB no total; ficheiro individual > 50 MB gera AVISO e o
excedente total gera ERRO (exit 1) com a lista a manter fora do git.

Uso: python tools/reflib/index.py
"""
import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..", "..")
sys.path.insert(0, HERE)
import schema  # noqa: E402

LIB = os.path.join(ROOT, "references")
TOTAL_CAP = 300 * 1024 * 1024
FILE_WARN = 50 * 1024 * 1024
MODEL_EXTS = (".blend", ".obj", ".fbx", ".stl", ".ply", ".glb", ".gltf")


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    models, errs, warn = [], [], []
    total = 0
    for sex in sorted(os.listdir(LIB)):
        sdir = os.path.join(LIB, sex)
        if not os.path.isdir(sdir):
            continue
        for st in sorted(os.listdir(sdir)):
            for part in sorted(os.listdir(os.path.join(sdir, st))):
                base = os.path.join(sdir, st, part)
                if not os.path.isdir(base):
                    continue
                for mid in sorted(os.listdir(base)):
                    d = os.path.join(base, mid)
                    if not os.path.exists(os.path.join(d, "meta.json")):
                        continue
                    meta = schema.load(d)
                    errs += schema.validate(meta, d)
                    files = []
                    for f in sorted(os.listdir(d)):
                        p = os.path.join(d, f)
                        if os.path.isfile(p):
                            sz = os.path.getsize(p)
                            files.append({"file": f, "bytes": sz,
                                          "sha256": sha256(p) if f.lower().endswith(MODEL_EXTS) else None})
                            total += sz
                            if sz > FILE_WARN:
                                warn.append(f"{mid}/{f}: {sz/1e6:.1f} MB > 50 MB (política híbrida: considerar fora do git)")
                    models.append({
                        "id": mid, "sex": meta["sex"], "style": meta["style"],
                        "style_confidence": meta["style_confidence"], "scope": meta["scope"],
                        "ref_type": meta["ref_type"], "pose": meta["pose"],
                        "path": os.path.relpath(d, ROOT), "files": files,
                        "has_extraction": os.path.exists(os.path.join(d, "extraction.json")),
                    })
    over = total - TOTAL_CAP
    if over > 0:
        errs.append(f"POLÍTICA: biblioteca com {total/1e6:.1f} MB > 300 MB (excede {over/1e6:.1f} MB) — "
                    "manter excedente fora do git e registar aqui")
    index = {"models": models, "total_bytes": total, "policy": {"total_cap_bytes": TOTAL_CAP,
                                                                "file_warn_bytes": FILE_WARN},
             "warnings": warn, "note": "primeiras entradas migradas de 408517a — NÃO ground truth; "
                                       "suitability por análise desconhecida até estudo"}
    json.dump(index, open(os.path.join(LIB, "INDEX.json"), "w"), ensure_ascii=False, indent=1)
    print(json.dumps({"models": len(models), "total_MB": round(total / 1e6, 1),
                      "warnings": warn, "errors": errs}, ensure_ascii=False, indent=1))
    if errs:
        sys.exit(1)


if __name__ == "__main__":
    main()
