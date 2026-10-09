# STATE — estado do HCG (entrada para qualquer agente/desenvolvedor)

Última atualização: 2026-10-02 (veredicto do dono: mama continua LINHA, nada no corpo realista além de cabeça/pescoço → DECISÃO: REMAKE do corpo do zero — docs/REMAKE_01.md; spike SDF mede a razão) · branch `arena/01a0d51d-proceduralhumangenerator`

## REMAKE_01 — decisão do dono (3 opções) → agente escolhe 3 (2026-10-02)

Veredicto OBSERVED: "a mama continua uma linha; nada está bom ou perto; nada
no corpo além da cabeça e por consequência o pescoço é realista". Gates do
corpo: 0/4 aprovados. **Decisão: REMAKE do CORPO do zero** (docs/REMAKE_01.md)
— mantém cabeça/pescoço validados, pipeline, instrumentos, refs, specs,
MANDATO/OPERATING_MODE/modos A-D. Morre: estações+superelipse+campos como
caminho de realismo (fica como baseline). Arquitectura nova [HYPOTHESIS]:
união suave de volumes anatómicos SDF (tórax, mamas, glúteo, ombros) com
parâmetros de relações. **Razão medida (spike, MEASURED)**: contraste local
de sombreado na caixa da mama: refs 0.040–0.043 | B2 0.029 (abaixo da banda —
olho do dono confirmado) | **SDF volume 0.208** (volume ⇒ estrutura legível;
calibração futura). Geometria do spike em banda (gap 23, prega, ápice 99).
Protocolo anti-erro (7 regras) + estágios E1–E5 com micro-gates em
REMAKE_01.md. Próximo: E1 (tórax+mama frontal SDF) com gate barato cedo.
**E1 EXECUTADO no mesmo dia** (REMAKE_01 §8): SDF loft polar suave das
estações + lóbulos teardrop smin + fossa clavicular; marching cubes 1.5mm.
Spec 7/7 em banda (ápice (69,94,1250), gap 21.8, prega 36.2, f1350 27.7,
barriga −1.2 — 1.ª vez; B2 tinha base fora). Imagem (rig numpy comum —
Blender/EGL crasha neste sandbox, caveat no doc): E1→real005 ΔL1 0.145 <
baseline ref↔ref 0.169 (1.ª vez dentro do spread); controlo limpo E1/E1N
0.046. Painéis e1_gate.png / e1_gate_side.png — **MICRO-GATE do dono pendente.**
**GATE E1 (2026-10-06): NEGATIVO — "pior que V0, embrulhado, pescoço
exagerado"** (REMAKE_01 §9): fragmento de tronco apresentado contra corpos
completos (framing meu), rig numpy duro, aposta em arquitectura sem confirmação
visual incremental. 5.º gate visual do corpo sem aprovação. REMAKE SUSPENSO;
E2–E5 cancelados até decisão do dono: (A) base-mesh CC0 + morphs paramétricos
(deixar de gerar geometria do zero — abordagem MakeHuman, nunca testada aqui),
(B) congelar corpo em V0 + foco no produto (variação/pele/cabelo/poses/export),
(C) pausa/encerrar.
**DECISÃO DO DONO: A — base mesh + morphs (2026-10-07).** Protótipo A.0
executado (basemesh_proto.py, numpy puro): frame exacto da base validado por
diff (y=−z_obj; heurísticas banidas); morphs por seed em bandas; **a base
JÁ tem anatomia mamária em banda (gap 20.5)**; 5 seeds: WHR 0.726–0.862,
cintura 226–286, tudo dentro/limítrofe das bandas refs. Rig v2 (normais de
vértice). Painéis basemesh_gen.png / basemesh_zoom.png. GATE do dono
pendente → se aprovado: preset female_basemesh + seeds no gerador (o
'gerar corpos ao clicar').
**Directriz BODY_SPEC_REMAKE (2026-10-06, do dono):** adoptada — anatomia
funcional ("que estrutura produz este volume"), hierarquia N0–N4 com regra
"nível seguinte nunca corrige anterior", transições como cidadãs de 1.ª
classe (C=f(d,θ,κ)), parametria em bandas, clay multi-vista, ε de assimetria
controlado, loop de erro hierárquico Es→Ep→Ea→Ec→Ev. **Autópsia de
transições EXECUTADA** (transition_report.py): Z1/Z4 pescoço→ombro = 4–7×
refs em TODAS as versões (pior breakpoint; alvo E2 nº1); Z5/Z6 E1 2× melhor
que V0 (loft suave funcionou); Z3 frente sub-curvada (10k vs refs 20–73k).
Painéis novos: transition_kappa.png + e1_views.png (multi-vista clay 4
vistas × 4 fontes). Alvos E2: cintura escapular/trapézio (volumes), curva
lombar/sacral, arco costal→abdómen.
Processo: ver `METHOD.md` (ciclo 16+1) e **`OPERATING_MODE.md` (novo, em vigor
— leitura obrigatória)** e `DEVELOPMENT_AGREEMENT.md` (formato).

## MODO DE OPERAÇÃO NOVO (2026-09-29, decisão do dono)

**`docs/OPERATING_MODE.md`** em vigor SEMPRE: mudança ≠ melhoria;
FALSE IMPROVEMENT como classificação obrigatória de resultados; pedido literal
vs problema real; referências como modelo externo de compreensão (não cópia,
não números); o corpo atual NÃO é autoridade anatómica; sistemas antes de
regiões; commit+push no mesmo passo. **`docs/CHECKPOINT_2026-09-29.md`**:
diagnóstico do método (T1 costas = FALSE IMPROVEMENT classificada; orelha =
melhoria local com dívida), auditoria de métricas (cegas a transições) e de
geometria (tronco estruturalmente inadequado), hipóteses H-T1..H-T6, plano
**T-TORSO SISTEMA** e método de validação (multi-vista por região + poses +
gates do dono). Próximo ciclo: estudo do torso como sistema — NÃO mexer na
geometria antes do estudo. **Decisões do dono (2026-09-29):** T1 fica ACTIVO
como estado experimental do checkpoint (não anatomia validada; decisão
definitiva suspensa até ao estudo); estudo T-TORSO por MISTURA (biblioteca
005/003/001/002/007 + anatomia → gaps → refs externas específicas → padrões;
refs novas do dono entram sem bloquear; proveniência obrigatória em cada
conclusão — n refs / quais, n=1 vs n≥3).


## Variantes ativas (realistic_female, seed 42, mm@H226)

| variante | flag | digest | estado |
|---|---|---|---|
| antes | (default) | `c7ab2932f5d66ede` | cabeça antiga (esfera+ilhas) |
| faseA | HCG_HEAD=massA | `76c5875d00a6db12` | casca de massas R1 |
| a2b | HCG_HEAD=massA2 | `db7871c83c9cf800` | + canto mentoniano |
| n1 | + HCG_NECK=N1 | `179c676c86b5f012` | + pescoço superior |
| f1 | HCG_HEAD=faceB+N1 | `e21378e3624e5765` | + face (campos+K+olhos) 8/8 |
| **f2** | HCG_HEAD=faceB2+N1 | `b713d9489ecd8bb9` | + CONT1 orelha integrada — validação do dono: ACEITÁVEL com dívida visual na orelha (resolver depois) |
| **t1** | **HCG_HEAD=faceB2+N1 (T1 on)** | **`dd0a715deed6dfc3`** | **+ T1 COSTAS curva S — CHECKPOINT: dono NÃO GOSTOU do visual (2026-09-29, provisório); NÃO fechada, re-ajustar antes de T2** |

**T1 COSTAS (2026-09-29) muda o BUILD DEFAULT**: pins agora 6467 verts/6373
faces (curva S é o default; `49fcc725984aec75` pure / `e9692d34c0dde938`
mathutils; testes 136 passed). `HCG_T1_AMP=0` reverte o campo (variantes
históricas do site exportam assim; digests preservados). **O dono não validou
o resultado visual das costas** — o checkpoint fica de pé (medições 3/3 em
§7 TORSO_STUDY_01), mas a T1 não está fechada: re-ajustar janelas/amplitudes
a partir do feedback específico do dono antes de avançar para T2.
Site: `site/` commitado — `tools/preview/serve.sh 8080`.

## Onde estamos (leitura honesta)

- DISTÂNCIA: similaridade de silhueta global medida por IoU (caixa da cabeça,
  câmara ortográfica comum): frente 0.913–0.940 vs baseline ref↔ref 0.897;
  lado ~baseline. MEASURED (medida, não veredicto visual).
- PROXIMIDADE: parcial. Interfaces medidas (continuity.py, κ_p99/turn):

| interface | oursF2 | refs | veredicto |
|---|---|---|---|
| orelha (turn) | 619° | 571–993° | ✓ dentro da banda (CONT1) |
| orelha (envelope) | pico 13.3 @ y−28.7 | média 13.1 @ −28.9 | ✓ (era −33) |
| nuca | κ 0.102 / 146° | 0.033–0.099 / 71–103° | ✗ pior excedente (1.8×) |
| órbita canto | conc 0.34 | 0.55–0.73 | ✗ difusa; falta rebordo definido |
| mento/garganta | ✓ | — | sem ação |

## Reference Library (docs/REFERENCE_LIBRARY.md) — FEITA a infraestrutura

`references/` (commitada; **14 entradas** — 6 migradas de 408517a + 8 do 1.º povoamento do dono: pack anime ×4 (1 masculina movida para male/), base mesh T-pose GLB, realistic female.blend, torso MPPled.fbx, rig de dança em other/; NÃO ground truth, suitability UNKNOWN por design): estrutura female/male × 6 estilos × 11 componentes; `meta.json` por modelo (schema.py validado em tests/test_reflib.py); `extraction.json` (inspect_model.py: contagens/ilhas/contorno/densidade/pose_hint); `INDEX.json` (index.py; guarda da política híbrida ≤300 MB — atual 13.5 MB). Snapshot mínimo reproduzível em `tools/snapshot/` (round-trip verificado 7/7 numa ref + gerador). Regra: a biblioteca é observação externa — nunca altera o gerador sem hipótese validada. Dono povoa; agente estuda.

## Próximos passos — programa PESCOÇO+TRONCO (TORSO STUDY 01, docs/TORSO_STUDY_01.md)

Prioridade do dono (2026-09-28): pescoço + torso (peito, abdômen, costas, cinturas).
Estudo MEDIDO feito; plano T1–T5 (uma mudança estrutural por fase, pré-registo antes):
1. **T1 COSTAS — CHECKPOINT (2026-09-29, reconstruída 2×; §7 TORSO_STUDY_01)** — curva sagital em S: lombar 26.9→45.3 ✓[40,75]; nádega-vs-torácica +12→−6.0 ✓[−25,−2]; costas altas −38→−26.0 ✓[−30,−8]; larguras Δ0.0. **Dono NÃO validou o visual** — re-ajustar (queixa específica pendente) antes de T2; não fechar.
2. **T2 CINTURA** — largura natural 288→[230,270]; cintura/nádegas 0.904→[0.75,0.85].
3. **T3 PEITO** — derreter o barril: largura 352→[268,314], profundidade 314→[216,307] (fora do p95 ANSUR).
4. **T4 BUSTO** — UNKNOWN nas refs atuais (uma sem mamas, uma com barriga dominante, uma mama pequena): decidir com o dono (refs novas ou literatura).
5. **T5 PESCOÇO-BASE + CONT2** — circ 417→≤382; nuca (CONT2 pré-registado em HEAD_CONT1.md §5).
Aguarda: validação do painel `renders_T1_vs_refs.png` + decisão do busto.

## T-TORSO SISTEMA — estudo REAL das refs FEITO (2026-09-29, docs/TORSO_STUDY_02.md)

Sem NENHUMA alteração de geometria. 17 padrões medidos com proveniência
(n refs/quais) sobre 11 modelos (2 excluídos com causa medida: whitewalker
normalização quebrada; real006 estilizada; mppled frame próprio). Síntese:
**de 13 dimensões, dentro só em 2** (cotas P12, razão peito/anca P8). Fora:
lombar 45.3 vs refs 53.7–69.7 (P1 — a banda T1 [40,75] era mais LARGA que as
refs: achado de método que explica "3/3 bandas" vs "não gostei"); mama alta
demais +45–115 e saliência 26 vs 54–70 (P4/P5 — real005 FECHA o gap do busto);
barril +40 largura/+74 profundidade (P9/P10); secção do peito redonda (n 2.2)
vs boxy das refs (≈3.8, P13) e dominada pela frente (1.06) vs costas
(0.60–0.72, P14); cintura 0.70 vs 0.63–0.66 (P7); sulco glúteo 4.4 vs 7–26
(P16). Respostas às 3 perguntas do dono em §4 do doc (1: NÃO — P4/P5/P13/
P14/P16 nunca tinham sido medidos; 2: PARCIALMENTE — bandas achatadas; 3: SIM
para a T1). Hipóteses H-D1..H-D4 + gaps G1–G5 + perguntas de decisão §7.
**Próximo: checkpoint de DECISÃO com o dono** (T1: recalibrar vs balanço
estrutural vs manter; ordem barril→cintura→volumes). Painéis:
docs/head_phaseA/torso_system_{sagittal,coronal,gluteal,curvature}.png (+site).

## TORSO DECISION 01 — checkpoint de DECISÃO formulado (2026-09-29, docs/TORSO_DECISION_01.md)

**NENHUMA geometria mudada; gate = dono.** Alternativas comparadas por PODER
EXPLICATIVO (pergunta-guia do dono): A recalibrar-T1 = 4 padrões directos/6
intocados (polidura numa parede errada); **B tórax-estrutural = 5 directos
(P3/P9/P10/P13/P14) + 5 habilitados (P1/P2/P4/P5/P7)**; C = B com T1 como
andaime (ALTA off durante B; T1 re-decidida DEPOIS por medição); D cintura
primeiro = 2 directos + re-trabalho. **RECOMENDAÇÃO (proposta): C**, ordem
B → T2-razão (P7/P18) → T4-volumes (mama alvo real005 + lóbulos/sulco P16) →
T5. Validação anti-falsa-melhoria: regra das bandas (emendada no
OPERATING_MODE — bandas = banda das refs, nunca mais largas), matriz
antes/depois dos 18 padrões, guardas P8/P12, gates visuais do dono por
região. P18 novo: anca 392 vs refs 324–336 (ANSUR ✓) — razões das refs,
absolutos limitados por ANSUR. Painel composto para o gate visual:
docs/head_phaseA/torso_system_panels.png (+site). **Aguarda gate do dono
(perguntas §6 do doc).**

## TORSO B — reconstrução estrutural do tórax IMPLEMENTADA (2026-09-29, docs/CHECKPOINT_TORSO_B.md)

Gate do dono APROVADO (decisão C) → B implementada em 7 its de calibração.
**12 padrões na banda das refs (era ~2):** P1 54.4 ✓, P2 −8 ✓, P3 1310 ✓ (estação
própria de cifose T7–T8), P4 1230 ✓ (bug +h·0.5 dos landmarks encontrado — a
"mama" do T1 era a inflação fs da estação), P5 64 ✓, P7 0.63 ✓, P8 0.80 ✓,
P9 312 ✓, P11 198 ✓, P13 3.8 ✓ (boxy), P15 1.19 ✓, P18 392 ✓ (ANSUR). Fora:
**P10 242 = APROXIMAÇÃO** (+2.5% sobre 236; P2/P10/P11 acoplados — parar),
**P14 1.10 = SEM MUDANÇA** (H-T2), **P16 sulco 0.2 = REGRESSÃO** vs T1 4.4
(amp lóbulos 0.020→0.013 por P11/P2; declarada, fila T2/T4). IoU perfil ours
0.667–0.787 (3/4 ≥ baseline ref↔ref 0.689); frente 0.639–0.679 vs 0.938 (gap =
anca ANSUR). T1-ALTA OFF durante B (HCG_T1_ALTA=1 reactiva); lombar amp 0.0215.
Pins: 6483/6389, skin 3601/3577, palm knife-edge float32 (62/86, registado).
136 tests passed. Fix de instrumento: painel glúteo do torso_system estava VAZIO
desde b0eda34 (chave "contour" vs contour_x) — números sempre certos, PNG agora
renderiza. **PERDA+RECONSTRUÇÃO:** o commit B original perdeu-se na 8.ª recriação
do sandbox (nunca chegou a ser pushed — token GitHub expirado a meio); foi
re-implementado dos parâmetros registados e verificado: GEN T1 reproduz os
digests históricos byte-a-byte; counts/semântica/fingerprint idênticos; 10/11
métricas P ao dígito (P11 198 vs 202, ambos na banda); digests novos: default
pure `8b74b578adb1755b` / math `ad377832122c78c3`, instrumento ours
`25cafb179b04ed34` / ours0 `cdc1996498342cdd`. **Gate visual do dono: PENDENTE**
(renders_T1_vs_refs.png 4 vistas + 4 painéis torso_system_* + site). Fila:
feedback → T2 (P14/P16/sulco) → T4 → T5 → só depois lapidação de regiões.

## GATE VISUAL TORSO B: NÃO APROVADO (2026-09-30) + TORSO TRANSITIONS 01 ESTUDADO

**Veredicto do dono:** "reconhecível como humanoide, mas a forma ainda denuncia a
construção procedural". Directriz completa em docs/TORSO_TRANSITIONS_01.md §0
(preservada verbatim): prioridades = mamas (volumes aplicados, não amp) e costas
("lombas de estrada"); tórax superfície suavizada, ombros parabólicos, abdómen em
ondas, cintura cortada, glúteos geométricos (mas NÃO destruir o volume);
métricas = guardrails não prova de humanidade; não polir detalhes antes das
massas; não criar variáveis por descoberta; corpo = camadas contínuas ("a anatomia
de algo só se tem com o outro"). Critério de sucesso: silhueta/volumes parecem
pertencer ao mesmo corpo humano, visível ANTES das métricas.

**Estudo dirigido FEITO (docs/TORSO_TRANSITIONS_01.md; SEM alteração de
geometria).** Instrumento novo torso_transitions.py (extremos locais + energia de
curvatura por junção R1–R10): **"lombas" confirmadas — R9 lombar: 3 extremos
nossos vs 1 [1–1] das refs, 2 deles a ≤2 mm das estações navel/hip_flare; 6/9
extremos nossos a ≤18 mm de uma estação**; R5: recessão submamária existe em
todas as refs e em nós NÃO (mama "aplicada"); R3: tórax é tubo (wiggle 0.73 vs
4.24 das refs); R2: ombro parabólico (0 extremos, wiggle 0.75 vs 12.2).
**Mecanismo (código):** o loft é LINEAR (topology.py mix(v0,v1,k/(K-1)) +
subdivide_rings linear + CC 1×) → C0 por troços, curvatura concentrada nas
estações. Resposta à pergunta §3: estações/superelipses/bumps PODEM ficar; o
INTERPOLADOR é o que tem de mudar. Hipóteses H-TT1..H-TT6 + plano ordenado
(H-TT1 spline C² primeiro, zero parâmetros novos). Mama-assimetria e dobra
glútea: linha média não discrimina (registado; cortes laterais na implementação).
Painel: docs/head_phaseA/torso_transitions.png.

## H-TT1 IMPLEMENTADO — loft spline C¹ (2026-09-30, docs/CHECKPOINT_TORSO_TT1.md)

Passo 1 do plano TORSO_TRANSITIONS_01: `spline_rings` (PCHIP monótona, C¹, sem
overshoot) dos CAMINHOS DOS PONTOS das estações substitui o loft linear +
subdivide_rings (+25 anéis = +400 verts/faces → 6883/6789; digests pure
`70437b0bcc3a90f5`/math `625a96991cc38bd0`). Interp de PARÂMETROS evitada (incha
cantos +18 mm, T1 §7.2). Estação perineal NOVA (sem ela o PCHIP alargava
anca→virilha e o tronco ATRAVESSAVA as pernas — componentes fundiam, banda `lo`
do instrumento saltava 0.475→0.540). Recalibração: a malha densa REALIZA os
campos por inteiro (gaiola dispersa amortecia ~30%) — mama 1.20→0.86, lombar
0.0215→0.0202, sacro 0.0240→0.0222, cifose 0.740→0.700, infra 0.550→0.540,
wf 0.905→0.912. **P1–P12: 11/11 na banda pela 1.ª VEZ (P10 232 ✓ — nunca
tinha entrado; alavanca = estação de cifose, o máximo de profundidade é o ápice
posterior z≈1305).** Transições: R1/R4/R5/R6 aproximam-se das refs (recessão
submamária COMEÇA a existir, R5 0→2); extremos NAS estações mantêm-se (R9 3,
R8 3 com dip @1260) — como previsto, fila H-TT2/TT4. 136 tests ✓, audit limpo.
Bugs próprios apanhados: dedup em metros (apagava a grelha), anéis 0.2 mm.
**Gate visual: PENDENTE** (renders + painéis + site). Fila: H-TT2 (sequências
de estações → matar extremos R8/R9) → H-TT3 mama → H-TT4 sagital → H-TT5 ombro
→ H-TT6 junções.

## MODO A ACTIVADO (decisão do dono 2026-10-01): busca guiada pelos olhos do dono

Após declaração honesta de limites do agente (cegueira visual raiz; memória com
perdas; viés optimista; vocabulário de representação limitado), o dono decidiu:
**A dominante** (loop invertido: agente gera variantes de UMA região → dono
escolhe/rankinga em folhas padronizadas com grelha → agente mede as diferenças
e aprende a função perceptual do dono), B (grelhas A–H × 1–8) suporte, C
(paradigma de representação) decidido com dados de ≥2 sweeps, D (expectativas
honestas: alvo = "convence à primeira vista na maioria das vistas") registada.

**SWEEP 01 MAMA pronto para o gate** (docs/SWEEP_01_BREAST.md): 8 variantes
V0–V7 (só a mama muda; V0 = H-TT1 digest exacto 8c6f568ccfbbe530) + 2 refs,
3 vistas (frente/3-4/perfil), folhas sweep_breast_*.png com grelha; gancho
HCG_BREAST (instrumento por chamada, default = H-TT1; vencedor vira default
calibrado — sem flags de spec). Protocolo de resposta no doc §3 (ranking +
células p.ex. "V3 perfil C4"). 30/30 tiles verificados numericamente.

## GATE SWEEP 01: NÃO APROVADO (2026-10-01) + MECHANISM AUDIT 01 FEITO

Veredicto do dono: V0–V7 indistinguíveis; mama não lê como volume; linguagem de
forma mecânica (aba no ombro, lombas, ondas, glúteo "boca"). Verificação:
parâmetros actuam (saliência 42–58mm, Δ 6–12mm) mas sub-limiar visual; cabelo e
grelha abdominal ELIMINADOS como confundidores (medidas); controlo negativo N0
adicionado. **MECHANISM_AUDIT_01.md**: cada defeito OBSERVED→mecanismo→medida —
ombro: largura 109→219mm em 32mm de z (gaiola); mama: gaussiana = vocabulário
insuficiente (9 características visíveis vs 4+3 DOF; amplitude JÁ comparável às
refs — falta FORMA); costas: zigzag de profundidades + planaltos PCHIP (R9 3
extremos, 2 nas estações); glúteo: lóbulos σx 55mm não cobrem o centro → canal
(peso e^−(116/55)²≈0.01) = "boca". Protocolo modo A corrigido (variantes de
REPRESENTAÇÃO quando a base está em causa; zoom à região; controlo negativo;
números Δ com cada folha). **Decisão C formulada com evidência: C1 refinamento /
C2 híbrido (estações + volumes próprios p/ mama-glúteo-ombro) / C3 camadas —
RECOMENDAÇÃO C2** (preserva o que funciona, substitui os mecanismos que
produzem a aparência artificial). AGUARDA GATE do dono (C1/C2/C3).
Painel novo: docs/head_phaseA/sweep_breast_zoom.png (N0/V0/V5/V6/V7 + refs).

## MANDATO RND (2026-10-01, permanente) + BREAST_C2_01 — protótipo C2 da mama

**MANDATO RND** (docs/MANDATE.md, íntegra): refs = material de estudo ACTIVO
(medir/isolar/separar/extrair); objectivo = PROGRAMA que gera corpos ao clicar;
visão computacional quando a inspecção falha; FACT/MEASURED/OBSERVED/INFERRED/
HYPOTHESIS/UNKNOWN obrigatório; demonstrar geometricamente (não por parâmetros);
propor outro mecanismo quando o actual não chega; preservar o que funciona;
BUILD DON'T FREEZE.

**BREAST_C2_01** (docs/BREAST_C2_01.md — protótipo C2 em HCG_BREAST2=1):
causa-raiz do SWEEP 01 medida = **cage 16 pts sem vértices na mama** (uma
aresta atravessa x 30–75; "linha-não-volume"). Correcção `_densify_front`
(pontos COLINEARES nas arestas frontais — parede não muda, campo ganha
controlo x≈21/42/63; ring_n=32 puro medido e REJEITADO: incha a parede +16).
Instrumento plane_scan v3.2 (3 bugs corrigidos: fill encadeava mal → topo
fantasma +24; plano exacto em vértice → segmentos perdidos; refs fragmentadas
→ reparo por contexto). **Especificação v3 (breast_spec_v3.json): swB2 EM
BANDA refs** — ápice (69,95,1261) vs refs x 69–71/y 79–97/z 1214–1266; gap
17 vs 7–34; base 54 vs 58–90; prega 38 vs 21–79; f@1350 24 vs 22–27;
barriga−peito −6.7 vs −7..+9. V0 (H-TT1, re-build sobre a anatomia actual)
com instrumento corrigido: gap −0, base 10, esterno 121 — crista confirmada.
Sagital do lobo rastreia real005 quase paralelo. Digests: N0
0437cc4ce71c49b2, B2 2ea834f946c214ad, V0-rebuild 9ed92eee38c0ee3d;
**default actual (com fs/bs H-TT2-parcial, não-gated) = ee588326c69b1f8d**
(H-TT1 histórico pré-fs/bs = 70437b0bcc3a90f5); P1–P12 por re-medir antes de
qualquer promoção. **GATE VISUAL do dono: NEGATIVO** (2026-10-02, "não vi diferença, está
sempre mal") — confirmado numericamente: B2 vs V0 frente = 0.1% silhueta /
2.5 níveis; B2 vs parede nua = 0.9 níveis (a mama é volume em profundidade,
invisível na frontal com luz plana; só o perfil mexe 13.2). A mama era 1 de
4 mecanismos auditados; dominadores frontais por reconstruir: ombro, costas,
glúteo, proporções (BREAST_C2_01 §8). Fila: gate → base 54→58+ → estações F/B
do esterno (coluna peito anterior, propriedade da parede).

**15.ª recriação do sandbox (2026-10-01):** trabalho do dia perdeu-se ANTES
do push (token GitHub expirado) — re-aplicado do zero e VERIFICADO: os 3
digests e a tabela de especificação reproduzem exactamente. Refspec do clone
agora inclui refs/heads/arena/* (era single-branch main — causa do push
"fetch first"). Ambiente: apt bloqueado → libs X/GL por stubs
(/usr/lib/x86_64-linux-gnu/stubs; LD_LIBRARY_PATH no headless_blender).

## Contabilidade técnica (METHOD: nenhum achado é apagado)

| achado | classificação |
|---|---|
| orelha: turn/envelope dentro das refs (CONT1) | melhoria confirmada (quantitativa) |
| orelha: integração visual de perto | dono: ACEITÁVEL — dívida visual notável (resolver depois) |
| tronco: costas sem curva S (lombar 19.5 vs refs 54–70) | T1 checkpoint: bandas 3/3 ✓ mas dono NÃO validou o visual — re-ajuste pendente |
| tronco: cintura tubular (WHpR 0.904 vs refs 0.72–0.81) | não corrigido (T2) |
| tronco: peito-barril (largura/profundidade > p95 ANSUR) | não corrigido (T3) |
| busto: alvo UNKNOWN nas refs | decisão do dono pendente (T4) |
| pescoço: circ 417 > p95 382 | não corrigido (T5; caveat 244 UNKNOWN) |
| pés: 758 verts assimétricos (max 17 mm) | pré-existente · não corrigido · fora de escopo |
| nuca: κ 1.8× refs | não corrigido (CONT2 pré-registado) |
| órbita: conc 0.34 vs 0.55–0.73 refs | não corrigido (CONT3) |
| K estatístico de 3 refs | declarado · UNKNOWN parcial (sobreajuste local) |
| fissura palpebral das refs ~14 mm vs norma ~10.4 | dívida das refs (estilizada) |
| default/pins/digests anteriores | intactos (verificado por auditoria) |

## Problemas conhecidos / dívida (regressões registadas, não escondidas)

- Pés: 758 verts assimétricos >0.1 mm (max 17 mm, z≈0.01–0.03 m) —
  PRÉ-EXISTENTE (idêntico em oursN1/F1/F2; nada a ver com a cabeça).
  Investigar em checkpoint do corpo. MEASURED.
- K (face_detail_v1.bin) é estatístico de 3 refs — declarado; ear alignment
  só por 3 marcos; orelha média varia ±10 mm entre refs (UNKNOWN parcial).
- Fissura palpebral das refs estilizada (~14 mm vs norma ~10.4); altura da
  femalebase tratada como outlier só nessa medida (HEAD_FACE_B.md).
- Cabeça↔pescoço: ainda sem continuidade C¹ (é o CONT2).
- F2 (orelha) aguarda validação visual do dono (painel
  `docs/head_phaseA/renders_F2_vs_refs.png` + close-up `renders_F2_ear.png`).

## Instrumentos (reutilizar, não duplicar)

- `tools/headface/continuity.py` — secções/silhueta, κ/turn/conc, nós vs refs.
- `tools/headface/render_cmp.py` — painéis render nós×refs (mesma câmara) +
  IoU de silhueta (proxy DISTÂNCIA).
- `tools/headface/render_ear.py` — close-up neutro da orelha.
- `tools/headfit/eval_phaseA.py` — critérios C1/C2 congelados (eval_F2.*).
- `tools/headface/{face_target,residual,fit_face,bake_detail}.py` — cadeia de
  calibração dos campos (refs → alvo → ajuste → K).
- `tools/headstudy/` — normalização/marcos comuns (common.py), exportação.

## Reprodução (sandbox novo)

```bash
git fetch origin arena/01a0d51d-proceduralhumangenerator && git reset --hard FETCH_HEAD
python3.11 -m venv /home/user/.venv-hcg
/home/user/.venv-hcg/bin/pip install bpy==5.0.1 numpy pytest scipy matplotlib pillow
/home/user/.venv-hcg/bin/python tools/headless_blender.py build   # stubs X/GL + smoke
mkdir -p out/refs && git archive 408517a "treino para o arena" | tar -x -C out/refs
/home/user/.venv-hcg/bin/python tools/headless_blender.py run tools/headstudy/export_heads.py
# site: tools/preview/serve.sh 8080  (a cópia commitada em site/ já serve)
```
