# STATE — estado do HCG (entrada para qualquer agente/desenvolvedor)

Última atualização: 2026-09-29 · branch `arena/01a0d51d-proceduralhumangenerator`
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
