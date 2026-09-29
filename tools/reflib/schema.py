# -*- coding: utf-8 -*-
"""REFERENCE LIBRARY — schema de metadados e validação (docs/REFERENCE_LIBRARY.md).

Regras do dono: classificação humana e simples; UNKNOWN em vez de inventar;
nenhum modelo é ground truth — a adequação por análise (suitability) começa
desconhecida e é preenchida pelos estudos.
"""
from __future__ import annotations

import json
import os
import re

STYLES = ["realistic", "semi_realistic", "anime_realistic", "anime", "cartoon", "low_poly", "unknown"]
STYLE_CODE = {"realistic": "REAL", "semi_realistic": "SEMI", "anime_realistic": "ANIR",
              "anime": "ANIME", "cartoon": "CART", "low_poly": "LOWP", "unknown": "UNKN"}
SCOPES = ["full_body", "torso", "head", "face", "hands", "feet", "ears", "arms", "legs", "other"]
REF_TYPES = ["scan", "artistic_mesh", "base_mesh", "procedural", "unknown"]
SEXES = ["female", "male", "unknown"]
POSES = ["t_pose", "a_pose", "custom", "unknown"]

REQUIRED = ["id", "sex", "style", "style_confidence", "scope", "ref_type", "origin",
            "pose", "file", "limitations", "regions_available", "unknowns", "suitability"]
ID_RE = re.compile(r"^REF-(F|M)-[A-Z]{3,5}-\d{3}$")
ENUMS = {"style": STYLES, "scope": SCOPES, "ref_type": REF_TYPES, "sex": SEXES, "pose": POSES}


def validate(meta: dict, model_dir: str) -> list[str]:
    """Erros de conformidade do meta.json (lista vazia = conforme)."""
    errs = []
    for k in REQUIRED:
        if k not in meta:
            errs.append(f"{model_dir}: campo obrigatório em falta: {k}")
    if errs:
        return errs
    for k, vals in ENUMS.items():
        if meta[k] not in vals:
            errs.append(f"{model_dir}: {k}={meta[k]!r} fora de {vals}")
    if not ID_RE.match(meta["id"]):
        errs.append(f"{model_dir}: id {meta['id']!r} não bate com REF-(F|M)-<CODE>-NNN")
    if not isinstance(meta["limitations"], list) or not isinstance(meta["unknowns"], list):
        errs.append(f"{model_dir}: limitations/unknowns têm de ser listas")
    if not isinstance(meta["suitability"], dict):
        errs.append(f"{model_dir}: suitability tem de ser dict (vazio = tudo UNKNOWN)")
    if not os.path.exists(os.path.join(model_dir, meta["file"])):
        errs.append(f"{model_dir}: ficheiro declarado não existe: {meta['file']}")
    return errs


def load(model_dir: str) -> dict:
    return json.load(open(os.path.join(model_dir, "meta.json"), encoding="utf-8"))
