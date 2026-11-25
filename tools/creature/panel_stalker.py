#!/usr/bin/env python3
"""Painel THE STALKER v3 — vistas + TABELA MEDIDA (17/17).

Rederiza as vistas do GLB e cola ao lado os valores de
out/refstudy/stalker_measure.json. SEM número medido, SEM painel:
é a regra v3 (consistência medida, docs/CREATURE_SPEC_STALKER.md).

Uso: python3 tools/creature/panel_stalker.py
Saída: docs/head_phaseA/stalker2_views.png (o mesmo ficheiro que o site
usa em RENDERS — o painel É a prova).
"""
import json
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tools", "creature"))
sys.path.insert(0, os.path.join(ROOT, "tools", "refstudy"))
from measure_stalker import read_meshes                     # noqa: E402
from basemesh_proto import vertex_normals, render_view      # noqa: E402

DOC = os.path.join(ROOT, "docs", "head_phaseA")
MEAS = os.path.join(ROOT, "out", "refstudy", "stalker_measure.json")
GLB = os.path.join(ROOT, "site", "models", "stalker2_smooth.glb")

F = "/usr/share/fonts/truetype/dejavu/"


def main():
    # ---- geometria (do GLB, não dos parâmetros)
    M, IDX = read_meshes(GLB, with_index=True)
    Vs, Ts, off = [], [], 0
    for nm in M:
        Vs.append(M[nm]); Ts.append(IDX[nm] + off); off += len(M[nm])
    V = np.vstack(Vs); T = np.vstack(Ts)
    N = vertex_normals(V, T)

    tiles = []
    for phi, name in ((0.0, "FRENTE"), (np.pi / 2, "PERFIL"), (np.pi, "COSTAS")):
        a = render_view(V, T, N, span=2100.0, zc=880.0, phi=phi, res=460)
        tiles.append((Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8), "L"), name))
    head = V[V[:, 2] > 1450]
    zc = (head[:, 2].max() + 1450) / 2
    a = render_view(V, T, N, span=700.0, zc=zc, phi=0.15, res=460)
    tiles.append((Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8), "L"), "CABEÇA"))

    # ---- tabela medida (schema: measures / spec / verdicts / n_pass)
    mj = json.load(open(MEAS))
    ms, sp, vd = mj["measures"], mj["spec"], mj["verdicts"]
    ok = mj["n_pass"]

    fb = ImageFont.truetype(F + "DejaVuSansMono-Bold.ttf", 14)
    fm = ImageFont.truetype(F + "DejaVuSansMono.ttf", 14)
    fs = ImageFont.truetype(F + "DejaVuSansMono.ttf", 12)
    fT = ImageFont.truetype(F + "DejaVuSans-Bold.ttf", 22)

    colw = [210, 92, 150, 58]
    xT = sum(colw) + 30
    x0 = 20
    W = x0 + sum(t[0].width for t in tiles) + 20 * len(tiles) + xT + 20
    # altura: tiles OU tabela geometria (17 linhas) + tabela animação (6)
    H = max(max(t[0].height for t in tiles) + 34,
            34 + 22 + 17 * 19 + 44 + 40 + 24 + 13 * 19 + 44 + 40 + 24 + 10 * 19 + 30)
    panel = Image.new("L", (W, H), 24)
    dr = ImageDraw.Draw(panel)

    dr.text((x0, 6), "THE STALKER v3.3 — ANATOMIA MEDIDA: GEO 17/17 · FORMA 13/13 · ANIM 10/10", font=fT, fill=235)
    x = x0
    for img, name in tiles:
        panel.paste(img, (x, 40))
        dr.text((x + img.width // 2 - 34, 20), name, font=fs, fill=190)
        x += img.width + 20

    # ---- coluna da tabela
    xt = x + 10
    y = 20
    dr.text((xt, y), f"measure_stalker.py · {ok['pass']}/{ok['total']} PASS · seed 13",
            font=fb, fill=235)
    y += 34
    hdr = ("métrica", "valor", "banda", "")
    xc = xt
    for h, w in zip(hdr, colw):
        dr.text((xc, y), h, font=fb, fill=160)
        xc += w
    y += 22
    dr.line([(xt, y - 4), (xt + sum(colw), y - 4)], fill=70)
    for k in sorted(ms):
        v, p = ms[k], vd[k]
        lo, hi = sp[k]
        unit = "mm" if k.endswith("_mm") else ("°" if "graus" in k else "")
        vv = f"{v:.1f}{unit}" if isinstance(v, float) else str(v)
        b = f"[{lo:g}..{hi:g}]"
        fill = 235 if p == "PASS" else 120
        xc = xt
        for txt, w, fnt in ((k, colw[0], fm), (vv, colw[1], fm),
                            (b, colw[2], fs), (p, colw[3], fb)):
            dr.text((xc, y), txt, font=fnt, fill=fill)
            xc += w
        y += 19
    dr.line([(xt, y), (xt + sum(colw), y)], fill=70)
    dr.text((xt, y + 8), "PASS = dentro da banda (docs/CREATURE_SPEC_STALKER.md)",
            font=fs, fill=120)

    # ---- tabela da FORMA/RELEVO (measure_form.py)
    FORM = os.path.join(ROOT, "out", "refstudy", "stalker_form.json")
    if os.path.exists(FORM):
        fj = json.load(open(FORM))
        y += 44
        dr.text((xt, y), f"FORMA/RELEVO (measure_form.py) · {len(fj['spec']) - fj['n_fail']}/{len(fj['spec'])} PASS", font=fb, fill=235)
        y += 24
        fm2, spf = fj["measures"], fj["spec"]
        vdf = {k: ("PASS" if (fm2[k] >= v[0] and fm2[k] <= v[1]) else "FAIL")
               for k, v in spf.items()}
        for k in ("F1_costelas_n", "F1b_costelas_amp", "F2_espinha_mm", "F3_vertebras_n",
                  "F4_escapula_mm", "F5_braco_contraste", "F6_gemeo_tendao",
                  "F6b_ante_punho", "F6c_joelho_coxa", "F8_olho_assente_mm",
                  "T1_torso_px_m", "T2_membros_px_m", "T3_uniformidade"):
            v, p2 = fm2[k], vdf[k]
            lo, hi = spf[k]
            if k.endswith("_n"):
                vv = f"{int(v)}"
            elif k.startswith("T"):
                vv = f"{v:.0f}" if k != "T3_uniformidade" else f"{v:.1f}x"
            elif "contraste" in k or "tendao" in k or "punho" in k or "coxa" in k:
                vv = f"{v:.2f}x"
            else:
                vv = f"{v:.1f}mm"
            band = f"[{lo:g}..{hi:g}]" if hi < 1e8 else f"≥{lo:g}"
            fill = 235 if p2 == "PASS" else 120
            xc = xt
            for txt, w, fnt in ((k, colw[0], fm), (vv, colw[1], fm),
                                (band, colw[2], fs), (p2, colw[3], fb)):
                dr.text((xc, y), txt, font=fnt, fill=fill)
                xc += w
            y += 19
        dr.line([(xt, y), (xt + sum(colw), y)], fill=70)

    # ---- tabela da ANIMAÇÃO (anim_check.mjs: mesmíssimo módulo do site)
    ANIM = os.path.join(ROOT, "out", "refstudy", "stalker_anim_check.json")
    if os.path.exists(ANIM):
        aj = json.load(open(ANIM))
        y += 40
        dr.text((xt, y), f"ANIMAÇÃO (anim_check.mjs) · {aj['n_pass']}/6 PASS", font=fb, fill=235)
        y += 24
        am, sp, vd = aj["measures"], aj["spec"], aj["verdicts"]
        for k in ("A1_ossos_mm", "A2_sola_min_mm", "A3_patin_ms", "A4_bob_mm",
                  "A5_topo_de_pe_m", "A6_topo_dormant_m", "A7_anti_fase",
                  "A7b_duty", "A7c_duplo_apoio", "A8_bombeio"):
            v, p = am[k], vd[k]
            lo, hi = sp[k]
            unit = "mm" if k.endswith("_mm") else ("m/s" if k.endswith("_ms") else "m")
            if k == "A3_patin_ms":
                band = f"[0..{aj['a3_band_ms']:.2f}]"
                vv = f"{v:.2f}"
            elif k in ("A5_topo_de_pe_m", "A7_anti_fase", "A7b_duty",
                       "A7c_duplo_apoio", "A8_bombeio"):
                band = f"[{lo:g}..{hi:g}]"
                vv = f"{v:.3f}" if k == "A8_bombeio" else f"{v:.2f}"
            else:
                band = f"[{lo:g}..{hi:g}]"
                vv = f"{v:.1f}{unit}"
            fill = 235 if p == "PASS" else 120
            xc = xt
            for txt, w, fnt in ((k, colw[0], fm), (vv, colw[1], fm),
                                (band, colw[2], fs), (p, colw[3], fb)):
                dr.text((xc, y), txt, font=fnt, fill=fill)
                xc += w
            y += 19
        dr.line([(xt, y), (xt + sum(colw), y)], fill=70)

    out = os.path.join(DOC, "stalker2_views.png")
    panel.save(out)
    print("painel medido →", out, f"({W}x{H})")
    return 0


if __name__ == "__main__":
    sys.exit(0 if main() == 0 else 1)
