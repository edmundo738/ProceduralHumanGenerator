"""Monta o mini site de preview em out/preview/ (estático; servir com qualquer servidor de ficheiros).

    # 1) modelos (Blender headless; ~10 s)
    python tools/headless_blender.py run tools/preview/export_glb.py -- out/preview/models
    # 2) site (copia páginas, three.js vendorizado, renders, dados)
    python tools/preview/build_site.py
    # 3) servir
    python -m http.server 8080 --bind 0.0.0.0 --directory out/preview

Os números vêm dos ficheiros de avaliação já no repositório (docs/head_phaseA/eval_N1.json,
neck_eval_N1.json) — o site não mede nada; mostra o que foi medido.
"""
import json
import os
import shutil
import subprocess
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SITE = os.path.join(ROOT, "tools", "preview", "site")
OUT = os.path.join(ROOT, "out", "preview")
DOCS = os.path.join(ROOT, "docs", "head_phaseA")
THREE_VERSION = "0.186.1"

DESC = {
    "antes": "cabeça original: esfera com aberturas e ilhas coladas (olhos, boca, orelhas). HEAD STUDY 01: g–op 174 vs 196–210, relação globo–órbita invertida.",
    "faseA": "nova representação: casca fechada cubo-esfera 3456 quads cujo raio é o modelo de 6 massas R1 ajustado ao alvo médio das refs. Sem traços (por desenho da fase).",
    "a2b": "Fase A + canto mentoniano: união local com o envelope médio do queixo de 3 refs (frente do queixo + plano submental).",
    "n1": "A2b + pescoço superior (anéis trunk.2/3) calibrado para o perfil médio das refs. Só 32 vértices do corpo mudam.",
}

METRIC_ROWS = [
    ("C1_rms", "C1 erro radial RMS vs alvo", None, 2.5, "≤ 2.5", 2),
    ("R_cephalic", "C2a largura / comprimento", 0.70, 0.79, "0.70–0.79", 2),
    ("S7_g_op", "C2b comprimento glabela–occipital", 196, 210, "196–210", 1),
    ("W1_breadth", "C2c largura máxima", 141, 156, "141–156", 1),
    ("W3/W2", "C2d têmporas W3/W2", 0.95, 99, "≥ 0.95", 2),
    ("W0.10H/W2", "C2e afunilamento da mandíbula", 0.62, 0.77, "0.62–0.77", 2),
    ("S5_glabella", "C2f glabela à frente do centro", 95, 107, "95–107", 1),
    ("TR3_submental", "C2g plano submental (TR3)", 55, 999, "≥ 55", 1),
    ("C1_max", "C1 erro radial máximo", None, None, "—", 1),
]
COLUMNS = [("antes", "ours", True), ("Fase A", "oursA", True), ("A2b", "oursA2", True), ("A2b + N1", "oursN1", True),
           ("makehuman", "makehuman", False), ("femalebase", "femalebase", False), ("bodytopo", "bodytopo", False),
           ("femalechar", "femalechar", False)]

RENDERS = [
    ("renders_N1.png", "NECK N1 — antes/depois (tronco)", "A2b vs A2b + N1; frente, ¾, lado, costas; Cycles cinza neutro, sem cabelo."),
    ("renders_N1_face.png", "A2b + N1 — enquadramento da cabeça", "Bordo inferior da mandíbula e submento visíveis no lado e ¾."),
    ("renders_A2b.png", "ANTES → FASE A → A2b", "Mesmas vistas e câmara; Cycles cinza neutro."),
    ("views_N1.png", "Vistas no rasterizador do estudo", "Mesmo rasterizador para as nossas versões e as refs."),
    ("profiles_N1.png", "Perfis sagital e de largura", "Nossas versões vs refs (mm@H226)."),
    ("jaw_coronal.png", "Cortes coronais do terço inferior", "Cabeça (preto) vs corpo/pescoço (vermelho) vs refs."),
    ("err_A2b.png", "Mapa de erro radial A2b vs alvo", "Contornos = desvio-padrão entre refs (3/5 mm)."),
    ("renders_phaseA.png", "FASE A — renders e wireframe da cage", "3456 quads, 8 polos de valência 3."),
    ("jaw_study.png", "Estudo da mandíbula", "Mapas laterais |x| e cortes horizontais."),
]

HISTORY = [
    ("HEAD STUDY 01 — diagnóstico", "de08023", "info", "medição", "Instrumento comum para a nossa cabeça e as refs. Cabeça curta (g–op 174 vs 196–210), glabela recuada, relação globo–órbita invertida, 280 polos e 45 ilhas na face.", "antes"),
    ("Capacidade R0 vs R1", "caf5d00", "info", "R0 inadequada · R1 capaz", "A representação antiga, com todos os parâmetros livres, não chega ao alvo (RMS 3.75, largura 162). O modelo de 6 massas R1 chega a RMS 1.35.", None),
    ("FASE A — casca de massas", "642cb7f", "fail", "5/8 critérios; C1, C2c, C2g ✗", "Nova casca fechada 100% quads. Falhas com origem única: o canto mento–submental arredondado desloca o mentón medido 9 mm.", "faseA"),
    ("A2 — plano submental (corte)", "3bf498f", "fail", "REFUTADA tal como implementada", "Erro de referencial: o canto estava subpreenchido, não em excesso. Registado e emendado antes de medir a A2b.", None),
    ("A2b — canto mentoniano", "5eb8c32", "pass", "hipótese suportada; C1 2.16 ✓; C2c 156.21 ✗; C2g ✗", "Envelope médio do queixo de 3 refs. Altura medida 213.1 → 219.8 mm; recuo do canto 9.9 → 40.0.", "a2b"),
    ("A3 — estudo da mandíbula", "500a694", "info", "A3 não suportada", "A mandíbula visível já coincide com as refs; a parte que não coincide está escondida dentro do pescoço (mais grosso que as refs).", None),
    ("NECK N1 — pescoço superior", "3ad83da", "pass", "N-C1 15/18 ✓; TR3 61.5 ✓", "Só os anéis trunk.2/3 mudam, calibrados para o perfil médio das refs. O submento e o bordo da mandíbula passam a ver-se.", "n1"),
]


def vendor_three(dst):
    cache = os.path.join(ROOT, "out", ".npm-three")
    mod = os.path.join(cache, "node_modules", "three")
    if not os.path.exists(os.path.join(mod, "build", "three.module.js")):
        os.makedirs(cache, exist_ok=True)
        subprocess.run(["npm", "install", "--silent", "--no-audit", "--no-fund", "--prefix", cache,
                        f"three@{THREE_VERSION}"], check=True)
    os.makedirs(os.path.join(dst, "addons"), exist_ok=True)
    for f in ("three.module.js", "three.core.js"):
        src = os.path.join(mod, "build", f)
        if os.path.exists(src):
            shutil.copy2(src, os.path.join(dst, f))
    shutil.copytree(os.path.join(mod, "examples", "jsm"), os.path.join(dst, "addons"), dirs_exist_ok=True)


def main():
    models = os.path.join(OUT, "models", "models.json")
    if not os.path.exists(models):
        sys.exit("falta out/preview/models — correr primeiro tools/preview/export_glb.py (ver docstring)")
    for f in os.listdir(SITE):
        shutil.copy2(os.path.join(SITE, f), os.path.join(OUT, f))
    vendor_three(os.path.join(OUT, "vendor", "three"))
    os.makedirs(os.path.join(OUT, "renders"), exist_ok=True)
    for src, *_ in RENDERS:
        shutil.copy2(os.path.join(DOCS, src), os.path.join(OUT, "renders", src))

    variants = json.load(open(models))
    for v in variants:
        v["desc"] = DESC[v["id"]]
    ev = json.load(open(os.path.join(DOCS, "eval_N1.json")))
    ne = json.load(open(os.path.join(DOCS, "neck_eval_N1.json")))
    rows = [{"key": k, "label": lab, "lo": (-1e9 if lo is None and hi is not None else lo), "hi": hi,
             "target": tgt, "dp": dp} for k, lab, lo, hi, tgt, dp in METRIC_ROWS]
    for r in rows:
        if r["hi"] is None:
            r["lo"] = None
    data = {
        "buildline": "realistic_female · seed 42 · cinza neutro, sem cabelo · branch arena/01a0d51d · "
                     + " · ".join(f"{v['id']} {v['digest']}" for v in variants),
        "variants": variants,
        "metrics": {"rows": rows, "columns": [{"label": a, "key": b, "ours": c} for a, b, c in COLUMNS],
                    "values": ev},
        "neck": [
            {"label": "N-C1 perfil do pescoço dentro das refs (18 medições)", "a": f"{ne['oursA2']['N_C1_in_range']}/18",
             "b": f"{ne['oursN1']['N_C1_in_range']}/18", "okA": ne["oursA2"]["N_C1_in_range"] >= 15,
             "okB": ne["oursN1"]["N_C1_in_range"] >= 15, "target": "≥ 15/18"},
            {"label": "C2g plano submental (TR3)", "a": f"{ev['oursA2']['TR3_submental']:.1f}",
             "b": f"{ev['oursN1']['TR3_submental']:.1f}", "okA": ev["oursA2"]["TR3_submental"] >= 55,
             "okB": ev["oursN1"]["TR3_submental"] >= 55, "target": "≥ 55"},
            {"label": "declive máx. da frente z −30…−65 (risco: tórax congelado)", "a": f"{ne['oursA2']['front_slope_max']:.2f}",
             "b": f"{ne['oursN1']['front_slope_max']:.2f}", "okA": True, "okB": False, "target": "registo (mais baixo = mais suave)"},
        ],
        "renders": [{"src": s, "title": t, "caption": c} for s, t, c in RENDERS],
        "history": [{"title": t, "commit": c, "status": s, "verdict": v, "text": x, "variant": var}
                    for t, c, s, v, x, var in HISTORY],
    }
    os.makedirs(os.path.join(OUT, "data"), exist_ok=True)
    json.dump(data, open(os.path.join(OUT, "data", "data.json"), "w"), ensure_ascii=False, indent=1)
    print("site em", OUT)


if __name__ == "__main__":
    main()
