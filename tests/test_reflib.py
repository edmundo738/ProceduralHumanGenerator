# -*- coding: utf-8 -*-
"""Reference Library — validação do schema e do índice (S1-light).

Corre com ou sem Blender: só valida metadados/consistência.  A biblioteca está
commitada no repo (política híbrida ≤300 MB), por isso o teste exige a presença
das pastas — se references/ não existir, falha (não skipa silenciosamente).
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, os.path.join(ROOT, "tools", "reflib"))
import schema  # noqa: E402


def test_library_present():
    lib = os.path.join(ROOT, "references")
    assert os.path.isdir(lib), "references/ em falta no checkout"
    assert os.path.exists(os.path.join(lib, "INDEX.json")), "INDEX.json em falta — correr tools/reflib/index.py"


def test_metas_validate():
    lib = os.path.join(ROOT, "references")
    errs = []
    n = 0
    for sex in ("female", "male"):
        sdir = os.path.join(lib, sex)
        if not os.path.isdir(sdir):
            continue
        for st in os.listdir(sdir):
            for part in os.listdir(os.path.join(sdir, st)):
                base = os.path.join(sdir, st, part)
                if not os.path.isdir(base):
                    continue
                for mid in os.listdir(base):
                    d = os.path.join(base, mid)
                    if not os.path.exists(os.path.join(d, "meta.json")):
                        continue
                    n += 1
                    errs += schema.validate(schema.load(d), d)
    assert n >= 6, f"esperadas ≥6 entradas, encontradas {n}"
    assert not errs, "\n".join(errs)


def test_index_consistent():
    lib = os.path.join(ROOT, "references")
    idx = json.load(open(os.path.join(lib, "INDEX.json")))
    assert idx["total_bytes"] < 300 * 1024 * 1024, "política híbrida excedida (300 MB)"
    for m in idx["models"]:
        d = os.path.join(ROOT, m["path"])
        assert os.path.isdir(d), f"INDEX aponta para pasta inexistente: {m['path']}"
        assert m["has_extraction"], f"{m['id']} sem extraction.json — correr inspect_model.py"
