"""Monta o mini site de preview em out/preview/ (estático; servir com qualquer servidor de ficheiros).

    # 1) modelos (Blender headless; ~10 s)
    python tools/headless_blender.py run tools/preview/export_glb.py -- out/preview/models
    # 2) site (copia páginas, three.js vendorizado, renders, dados)
    python tools/preview/build_site.py
    # 3) servir
    python -m http.server 8080 --bind 0.0.0.0 --directory out/preview

HCG_PREVIEW_OUT=<pasta> muda o destino (modelos: <pasta>/models).

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
OUT = os.path.abspath(os.environ.get("HCG_PREVIEW_OUT", os.path.join(ROOT, "out", "preview")))
ADDONS = ("loaders/GLTFLoader.js", "controls/OrbitControls.js", "utils/BufferGeometryUtils.js",
          "utils/SkeletonUtils.js")  # só o que o site importa (e as dependências diretas)
DOCS = os.path.join(ROOT, "docs", "head_phaseA")
THREE_VERSION = "0.186.1"

DESC = {
    "antes": "cabeça original: esfera com aberturas e ilhas coladas (olhos, boca, orelhas). HEAD STUDY 01: g–op 174 vs 196–210, relação globo–órbita invertida.",
    "faseA": "nova representação: casca fechada cubo-esfera 3456 quads cujo raio é o modelo de 6 massas R1 ajustado ao alvo médio das refs. Sem traços (por desenho da fase).",
    "a2b": "Fase A + canto mentoniano: união local com o envelope médio do queixo de 3 refs (frente do queixo + plano submental).",
    "n1": "A2b + pescoço superior (anéis trunk.2/3) calibrado para o perfil médio das refs. Só 32 vértices do corpo mudam.",
    "f1": "F1 = faceB + N1: sobre a mesma casca, campos anatómicos com limites de sinal (nariz, lábios, órbitas, orelhas) + camada corretiva estatística das refs (declarada; 43% explicado pelos campos). Globos oculares procedurais. Primeira versão 8/8 critérios (W1 153.2 ✓).",
    "f2": "F2 = CONT1 + N1: orelha INTEGRADA — janela C¹ (smoothstep, valor e declive nulos no bordo) × colina recentrada no envelope medido das refs + relevo reforçado; K mantido (suprimi-lo custou relevo: turn 449° vs 462°). Turn da secção 462→619° (refs 571–993). Fora da orelha: máx 0.035 mm. 8/8 critérios intactos.",
    "t1": "H-TT1 = TORSO B + loft SPLINE: o tronco deixa de ser C0 por troços — anéis densos por PCHIP (C¹, monotónica, sem overshoot) dos caminhos dos pontos das estações (a interpolação linear concentrava a curvatura nas estações = as 'lombas de estrada' medidas: R9 3 extremos vs 1 [1–1] das refs). Estação perineal nova (o PCHIP alargava anca→virilha e o tronco atravessava as pernas — corrigido). Amplitudes recalibradas para a malha densa (que agora realiza os campos por inteiro): mama 1.20→0.86, lombar, sacro, cifose, wf. P1–P12: 11/11 na banda pela PRIMEIRA vez (P10 232 ✓, era 242). Gate visual do dono: PENDENTE (docs/CHECKPOINT_TORSO_TT1.md).",
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
           ("F1", "oursF1", True), ("F2", "oursF2", True),
           ("makehuman", "makehuman", False), ("femalebase", "femalebase", False), ("bodytopo", "bodytopo", False),
           ("femalechar", "femalechar", False)]

RENDERS = [
    ("e1_views.png", "E1 — MULTI-VISTA clay (frente/¾/perfil/costas)", "BODY_SPEC_REMAKE §7: clay cinzento, câmara/luz/escala comuns. real005 · femalebase · V0 (antigo) · E1 (volumes SDF) × 4 vistas. Gate: 'lê como corpo?' — apontar zona (p.ex. 'E1 costas Z6')."),
    ("transition_kappa.png", "TRANSIÇÕES — κ(z) sagital: onde o corpo deixa de ser sistema", "BODY_SPEC_REMAKE §4 executado: curvatura dos perfis sagitais (frente/costas) por zona anatómica. MEASURED: pescoço→ombro (Z1/Z4) = 4-7× refs em TODAS as versões (o pior breakpoint — 'ombro=conector mecânico'); E1 já 2× melhor em torácica→lombar; frente sub-curvada no abdómen→pelve. Alvos do E2 definidos por número."),
    ("e1_gate.png", "E1 REMAKE — MICRO-GATE: mama como VOLUME (SDF)", "docs/REMAKE_01.md §8. Corpo modelado como função de distância: parede = loft polar suave das estações (resolução infinita, sem anéis) ∪ lóbulos mamários teardrop (união suave) − fossa clavicular; malha por marching cubes. Spec 7/7 em banda (ápice (69,94,1250), gap 21.8, prega 36.2, f1350 27.7, barriga −1.2) — 1.ª vez. Rig numpy IDÊNTICO em todos os tiles (Blender/EGL crasha neste sandbox): E1→real005 ΔL1 0.145 < baseline ref↔ref 0.169. Controlo E1N (sem lóbulos) incluído. GATE: 'E1 lê como volume?'"),
    ("e1_gate_side.png", "E1 REMAKE — perfil (projeção da mama)", "Perfil 660mm: real005 vs B2 (campo) vs E1 (volumes). Costas ainda sem curva S (é o estágio E2 — esperado)."),
    ("torso_system_panels.png", "T-TORSO — painel COMPOSTO (4 painéis, gate visual do dono)", "Os 4 painéis do estudo do torso como sistema (TORSO_STUDY_02) numa imagem: sagital (refs vs nós), larguras normalizadas, contorno glúteo, curvatura. É o material de leitura visual para o checkpoint de decisão (TORSO_DECISION_01) — os números orientam, o gate visual do dono decide."),
    ("torso_system_sagittal.png", "T-TORSO — perfis sagitais: refs vs nós", "Estudo do torso como SISTEMA (TORSO_STUDY_02): perfil posterior e anterior da linha média, refs (cinza) vs nós T1-off (tracejado) e T1-on (sólido). 17 padrões medidos com proveniência; painel 1 de 4."),
    ("torso_system_coronal.png", "T-TORSO — larguras normalizadas pela anca", "Largura do tronco / largura da anca (invariante à orientação): a cintura das refs (0.63–0.66 da anca) vs a nossa (0.70 — tubular). Padrão P7; painel 2."),
    ("torso_system_gluteal.png", "T-TORSO — contorno glúteo", "Contorno posterior no ápice da nádega: todas as refs válidas têm lóbulos laterais + sulco central (7–26 mm); nosso T1-on tem um esboço (4.4), T1-off é bloco. Padrão P16; painel 3."),
    ("torso_system_curvature.png", "T-TORSO — curvatura do perfil posterior", "κ(z) do perfil posterior (transições/quebras de plano). Instrumento limitado pela quantização dos cortes (5 mm) — comparação visual; a métrica de transições fica como gap G3. Painel 4."),
    ("sweep_breast_front.png", "SWEEP 01 MAMA (modo A) — frente", "Busca guiada pelo dono: 8 variantes da mama (só a mama muda; resto = H-TT1) + 2 refs, grelha A–H × 1–8 para apontar. O dono rankinga; o agente mede o que distingue as escolhas. docs/SWEEP_01_BREAST.md."),
    ("sweep_breast_q.png", "SWEEP 01 MAMA (modo A) — 3/4", "Vistas 3/4 das mesmas variantes V0–V7 + refs (real005, femalebase)."),
    ("sweep_breast_side.png", "SWEEP 01 MAMA (modo A) — perfil", "Vistas de perfil das mesmas variantes: polo superior/inferior, saliência, implantação."),
    ("sweep_breast_zoom.png", "SWEEP 01 MAMA — ZOOM peito (pós-gate)", "Resposta ao gate NEGATIVO: zoom 620mm com controlo N0 (mama OFF = parede nua), V0/V5/V6/V7 e refs. Verificação numérica: variantes diferem 6-12mm (real mas sub-limiar a corpo inteiro); a mama é um inchaço difuso, não volume — evidência para a decisão C2 (docs/MECHANISM_AUDIT_01.md)."),
    ("breast_c2_zoom.png", "BREAST C2 — ZOOM 660mm: protótipo estruturado (gate visual)", "MANDATO RND · docs/BREAST_C2_01.md. Causa-raiz do SWEEP 01 corrigida: o cage 16pts não tinha vértices na mama (uma aresta atravessava x 30-75 — 'linha-não-volume'); _densify_front insere pontos colineares (parede intacta) e o campo C2 forma volume. Especificação v3 (instrumento plane_scan v3.2): swB2 EM BANDA refs — gap 17 (refs 7-34), base 54 (58-90), prega 38 (21-79), f@1350 24 (22-27), ápice x 69 (69-71). Painel: 3 refs + N0 (parede) + V0 (H-TT1) + B2 (C2) × frente/¾/perfil. GATE do dono pendente."),
    ("breast_c2_torso.png", "BREAST C2 — corpo-torso (contexto)", "As mesmas fontes em vista corpo-torso (ortho 1.06): B2 vs V0 vs N0 vs refs — integração da mama estruturada no conjunto, peito superior recuado (f@1350 24 vs 50 do V0) e barriga plana (barriga-peito -6.7, banda refs -7..+9)."),
    ("renders_T1_vs_refs.png", "TORSO T1 — costas em S: nós vs refs (mesma câmara)", "Frente, ¾, lado e costas do tronco: ours T1 (curva S, braços caídos) e as refs (femalebase/femalechar/bodytopo/real005; T/A-pose). IoU lado 0.67–0.75 vs ref↔ref 0.69. A/B medido (amp0→amp1): lombar 26.9→45.3 ✓; nádega-vs-torácica +12→−6.0 ✓; costas altas −38→−26.0 ✓; larguras Δ0.0. Validação do dono: NEGATIVA por agora (docs/TORSO_STUDY_01.md §7)."),
    ("renders_F2_vs_refs.png", "F2 vs REFS — painel comparativo (mesma câmara)", "Cinco fontes × seis vistas (frente, ¾, lado, costas, orelha, orelha-¾), Cycles cinza neutro: oursF1, oursF2 e as 3 refs. IoU de silhueta: frente 0.91–0.94 vs baseline ref↔ref 0.90."),
    ("renders_F2_ear.png", "F2 — CONT1: close-up da orelha (PROXIMIDADE)", "F1 vs F2, lado e ¾ posterior; Cycles cinza neutro, sem cabelo, mesma câmara. A janela C¹ funde a orelha na casca (sem degrau no bordo) e o relevo entra na gama das refs (turn 462→619°)."),
    ("cont1_ear_h.png", "CONT1 — curvatura da orelha vs refs", "Secção horizontal z=92.5 (esq.) e |κ| ao longo do arco (dir.): F2 dentro da banda das refs."),
    ("cont1_nape_p.png", "CONT1 — nuca: pior excedente medido", "Silhueta occipital→nuca→pescoço: ours κ 1.8× as refs — pré-registo CONT2."),
    ("renders_F1.png", "F1 — ANTES/DEPOIS da face", "A2b+N1 vs F1 (faceB+N1); frente, ¾, lado; Cycles cinza neutro, sem cabelo, mesma câmara. A forma de massa desaparece: nariz, lábios, órbitas e orelhas."),
    ("views_F1.png", "Vistas neutras F1 (rasterizador do estudo)", "F1 vs refs, mesmo rasterizador; mm@H226."),
    ("profiles_F1.png", "Perfis sagital e de largura — F1", "Nossas versões vs refs (mm@H226)."),
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
    ("FACE F1 — massas faciais e traços", "2d6039f", "pass", "8/8 critérios ✓; C1 2.12; W1 153.2 ✓", "Campos anatómicos (limites de sinal) + camada corretiva estatística das refs, sobre a casca A2b/N1. Estatística declarada (43% campos, K das 3 refs). Digest oursF1 e21378e3624e5765.", "f1"),
    ("CONT1 — continuidade anatómica", "029063e", "pass", "PR1–PR5 ✓; orelha turn 619° (refs 571–993)", "Estudo medido por secções/silhueta (nuca 1.8× refs = pior; orelha 0.64× relevo). Orelha integrada: janela C¹ + envelope medido + relevo; K mantido (medido). Confinamento exato: 0.035 mm fora da zona.", "f2"),
    ("T1 COSTAS — curva sagital em S", "4258f24", "info", "bandas 3/3 ✓ (lombar 45.3; nádega −6.0; altas −26.0); validação do dono: NEGATIVA por agora", "CHECKPOINT (não fechada). RECONSTRUÇÃO 2× — o commit original (c8ee4ce) e a 1.ª reconstrução (837b69b) perderam-se em resets do sandbox antes do push. Três janelas C¹ (sacro/lombar/altas) só na face posterior + 10 anéis interpolados; larguras Δ0.0. O dono não gostou do resultado visual (2026-09-29): re-ajustar janelas/amplitudes antes de seguir para T2. Ref nova real005 admitida (lombar 56.2 ✓).", "t1"),
    ("TORSO B — tórax como sistema (decisão C)", "25cafb1", "info", "12/18 padrões ✓ na banda das refs (era ~2); P10 aproximação; P16 regressão declarada; gate visual do dono: PENDENTE", "Reconstrução estrutural (TORSO_STUDY_02 + TORSO_DECISION_01): estação de cifose T7–T8 nova, parede torácica boxy/costas-dominante, níveis da mama corrigidos (bug +h·0.5), mama = bump localizado, lóbulos glúteos laterais, cintura por razão wf 0.905, T1-ALTA off durante B. Calibração 7 its; P2/P10/P11 acoplados (P10 242 vs ≤236 = aproximação declarada). Pins 6483/6389; 136 tests ✓. RECONSTRUÇÃO: o commit B original perdeu-se num reset do sandbox antes do push; re-implementado dos parâmetros registados (10/11 métricas ao dígito, P11 198 vs 202 na banda). Regressões NÃO escondidas: sulco glúteo (amp lóbulos ↓; fila T2/T4), P14 1.10 (H-T2). docs/CHECKPOINT_TORSO_B.md.", "t1"),
    ("H-TT1 — loft spline C¹ (transições)", "8c6f568", "info", "P1–P12 11/11 na banda pela 1.ª vez (P10 232 ✓); +25 anéis PCHIP; gate visual: PENDENTE", "Resposta ao gate NEGATIVO do TORSO B ('a forma denuncia a construção procedural'): estudo TORSO_TRANSITIONS_01 mediu as ondas — 6/9 extremos a ≤18 mm das estações, R9 lombar 3 extremos vs 1 [1–1] das refs — e o mecanismo (loft LINEAR = C0 por troços). H-TT1: PCHIP dos caminhos dos pontos (interp de parâmetros incha os cantos +18 mm, T1 §7.2 — evitado), passagem exacta pelas estações, zero parâmetros novos de spec. Estação perineal (tronco atravessava as pernas com o PCHIP). Recalibração: a malha densa realiza os campos por inteiro (mama 1.20→0.86 etc.). Extremos NAS estações mantêm-se (R9) — H-TT2/TT4 na fila. 136 tests ✓; audit limpo.", "t1"),
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
    for a in ADDONS:
        os.makedirs(os.path.dirname(os.path.join(dst, "addons", a)), exist_ok=True)
        shutil.copy2(os.path.join(mod, "examples", "jsm", a), os.path.join(dst, "addons", a))


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
    ev = json.load(open(os.path.join(DOCS, "eval_F2.json")))
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
