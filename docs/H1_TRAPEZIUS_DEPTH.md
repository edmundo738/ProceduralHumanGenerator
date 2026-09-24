# H1 — Profundidade das estações da rampa do trapézio

**Tipo:** experimento isolado (uma hipótese, alteração mínima). **Não é um build.**
**Base:** `7431e36` (REF STUDY 01) · **Preset/seed:** `realistic_female` / 42 · **Ambiente:** bpy 5.0.1 headless, Cycles CPU
**Origem da hipótese:** `docs/REF_STUDY_01.md` §9, H1
**Pergunta única:** *a elevação posterior na base do pescoço ("capuz") vem de as duas
estações da rampa do trapézio terem o dobro da profundidade pretendida?*

Classificação usada: FACT · MEASURED · OBSERVED · INFERRED · HYPOTHESIS · ENGINEERING JUDGMENT · UNKNOWN.

---

## 1. Hipótese e previsão (registadas antes da medição)

- **HYPOTHESIS (REF STUDY 01 §9):** `Section.depth` é **meia**-profundidade
  (`core/topology.py`, FACT). As estações da rampa do trapézio usavam
  `0.075·S` e `0.100·S`, o que dá **275 / 364 mm de profundidade total**.
  São as estações mais profundas de todo o corpo, mais do que o peito (MEASURED
  no código). A suspeita é que estes números tenham sido escritos como
  profundidade **total**.
- **Critérios §9:** (a) nenhum pico de profundidade em z 1380–1450;
  (b) `upper_back_vs_occiput` em ≈ −30…0 mm (refs −2 / −10 / −22).
- **Previsão pré-registada:** o pico desaparece, mas as costas altas podem
  continuar ≈ 50 mm atrás do occipital, porque as estações do peito ficam
  intactas (território de H2/H5). H1 falhar, total ou parcialmente, é um
  resultado válido.

## 2. Alteração (FACT)

Ficheiro único do gerador: `human_generator/core/anatomy.py`, `trunk_sections()`.
As duas profundidades da rampa foram multiplicadas por 0,5. **Larguras, `bs`,
`sup`, deslocamento `y` e cotas z ficaram iguais**, e nenhuma outra estação,
deformador ou módulo mudou.

| estação (z) | prof. total antes | prof. total depois | costas y antes | costas y depois |
|---|---|---|---|---|
| 1414 | 275 | **137,7** | — | **−101,2** |
| 1401 | 364 | **181,9** | — | **−124,1** |
| 1352 (peito) | inalterada | inalterada | −141,6 | −141,6 |
| 1295 (peito) | inalterada | inalterada | −145,7 | −145,7 |

MEASURED (código): a profundidade total das estações passa a crescer de forma
monótona de cima para baixo (109 → 138 → 182 → 223 → 259 → 342 mm). Antes
havia um salto de 109 → 275 → 364 → 223.

Ferramentas (não mudam a geometria): métricas H1 em `tools/refstudy/metrics.py`;
`tools/refstudy/gen_blend.py` e `HCG_BUILD_FROM_TREE=1` em `run_all.sh` para
medir a árvore de trabalho; correção do caminho BUILD por omissão em
`refload.py`; flag `--neutral` em `tools/render_views.py` (material cinzento
uniforme para avaliação anatómica).

## 3. Controlo do instrumento (MEASURED)

Antes de alterar o gerador, o instrumento foi corrido duas vezes: sobre o .blend
do BUILD 02 (`out/rs_build`) e sobre a árvore inalterada gerada por
`gen_blend.py` (`out/rs_base`, digest `63a579d98df0c8d8`). O resultado foi um
`metrics.txt` **idêntico nas 51 linhas**. Logo, as diferenças abaixo vêm da
alteração, não do caminho de medição.

## 4. Resultado (MEASURED, mesmo instrumento antes/depois)

| métrica | antes | **H1** | femalebase | femalechar | bodytopo | critério |
|---|---|---|---|---|---|---|
| neckbase_depth_excess | +20 | **−58** | (+102)* | −44 | −62 | (a) **PASSA** |
| neckbase_depth_max | 322 | **244** | (294)* | 158 | 146 | — |
| upper_back_z | 1415 | **1330** | 1330 | 1330 | 1335 | (a) **PASSA** |
| upper_back_vs_occiput | −104 | **−52** | −2 | −22 | −10 | (b) **FALHA** (alvo −30…0) |
| occiput_z | 1580 | 1580 | 1600 | 1585 | 1605 | — |
| nape_z | 1530 | 1515 | 1485 | 1470 | 1495 | (H5) |
| nape_recess | 16 | 18 | 32 | 36 | 24 | (H5) |
| neck_depth | 168 | 154 | 98 | 108 | 152 | (H5) |
| neckcircumference | 453 | 429 | — | — | — | ANSUR p5–p95 315–382 (H5) |

\* **femalebase é inválida nas métricas da base do pescoço**: está em pose T, com
os braços dentro da janela 1380–1450 (OBSERVED no REF STUDY 01).

**Isolamento (MEASURED):** só mudaram 8 das 51 linhas de `metrics.txt`, todas
de pescoço ou base do pescoço. Tronco, cintura, anca, glúteo, pernas, joelho e
cabeça ficaram idênticos. Ficheiros: `docs/h1_trapezius/metrics_before.txt` e
`metrics_after.txt`.

**Atribuição do resíduo de −52 mm (INFERRED, concordância numérica forte):** do
código, as costas nas estações do peito ficam em −141,6 / −145,7 mm e o
occipital (elipsoide) em −93,8 mm, o que dá −47,8 / −51,8 mm. O valor medido na
malha é −52. O resíduo vem das estações do tórax, que H1 não toca. Coincide com
a previsão pré-registada e com o excesso de profundidade do tronco (H2).

**Máximo absoluto na base do pescoço ainda 244 mm vs 146–158 (UNKNOWN):** o
excesso normalizado está dentro das refs, mas o máximo absoluto não. Candidatos,
nenhum testado: a estação `deltoid_line` (`chest·0.62`), a profundidade geral do
tronco (H2) e a contribuição da raiz do braço em pose A. Não é atribuído a H1.

## 5. Evidência visual (OBSERVED)

`docs/h1_trapezius/h1_before_after.png`: sem cabelo, material neutro, Cycles
ortográfico, a mesma câmara nos dois casos. A baseline foi gerada numa worktree
temporária de `7431e36`.

- De perfil, a "gola/capuz" cónica saliente na base do pescoço (atrás **e** à
  frente) **desapareceu**. O pescoço passa para as costas e o peito em rampa.
- De costas, a "capa" plana e larga foi substituída por uma inclinação do
  trapézio do pescoço para os ombros.
- **Não mudou, e não devia mudar com H1:** o tronco em cabaça com a barriga
  saliente (H2/H3), a ausência de lordose e o glúteo alto (H4), e o pescoço
  ainda grosso e curto com a nuca pouco recuada (H5).

## 6. Garantias S2/S3 (MEASURED)

| verificação | resultado |
|---|---|
| pytest | 133 passed · 1 skipped · 1 xfailed (igual à baseline) |
| S0 aceitação pure-python | 33/33 PASS |
| S0 aceitação bpy | 72/72 PASS |
| auditoria | 6307 v / 6213 f · non-manifold 0 · degenerate 0 · loose 0 · ngons 0 · boundary 962 (inalterado) |
| fingerprint | `ad620a90b8eba085` (inalterado) |
| pins semânticos, J1–J5, mãos, pés, simetria, weld, chão | passam, inalterados |
| digest | **mudou (esperado)**: pure-python `af71a975bdfc8998 → c0a50b8a261633ad`, mathutils `63a579d98df0c8d8 → 1dfe85655ada5de0` |

Antes do re-pin, o **único** teste a falhar era o do digest (MEASURED). O
re-pin em `tests/pins.py` foi feito de propósito, com comentário e com os
valores anteriores registados.

## 7. Veredicto

- **O mecanismo de H1 confirma-se (MEASURED):** as duas estações sobredimensionadas
  eram a origem geométrica do pico de profundidade e do "capuz". Corrigidas, o
  pico desaparece (−58 vs −44/−62) e a cota das costas altas coincide com as
  refs (1330 vs 1330–1335).
- **O critério (b), como estava escrito no §9, FALHA:** −52 vs −30…0. A previsão
  pré-registada antecipou isto. O critério (b) media duas coisas ao mesmo tempo
  (o pico de H1 e o alinhamento global costas/cabeça), e só a primeira pertence
  a H1. Esta separação é feita **depois** de medir e fica declarada como tal.
- **A causa "total vs meia profundidade" continua UNKNOWN:** ×0,5 dá valores
  plausíveis, o que é consistente com a hipótese, mas não prova a intenção de
  quem escreveu as constantes. ENGINEERING JUDGMENT: o fator exato (0,5) não
  foi ajustado aos dados. É o valor que a hipótese previa e não foi afinado
  depois de ver o resultado.

## 8. Dívida registada (sem refactor agora)

1. As constantes `0.075·S·0.5` e `0.100·S·0.5` deviam ser derivadas das estações
   vizinhas (profundidade do pescoço e do ombro) em vez de números soltos. A
   forma `×0.5` foi mantida de propósito para o diff mostrar exatamente o que o
   experimento mudou.
2. A convenção meia/total de `Section` não é verificada por nenhum teste. Um pin
   de "profundidade monótona nas estações do pescoço → peito" teria apanhado
   isto. Proposta para depois de H2, quando a sequência do tronco estiver
   estável.
3. `femalebase` (pose T) não serve para métricas entre ombro e pescoço. O
   instrumento devia marcar estas células como inválidas automaticamente.
4. O occipital usado na atribuição vem do elipsoide analítico, não da malha. É
   suficiente para atribuir, mas não para medir.

## Minha avaliação

**Concordo porque** a alteração tem duas linhas e ataca a origem geométrica, não
o sintoma. O efeito ficou confinado às métricas previstas (8/51 linhas), a
imagem confirma o que os números dizem, e nenhuma garantia S2/S3 regrediu.

**Discordo de** chamar a isto "o pescoço resolvido". O critério de alinhamento
falhou e o pescoço continua grosso (circunferência 429 vs ANSUR p95 382), com a
nuca pouco recuada. H1 retirou um defeito e não pôs o pescoço certo.

**Riscos:** (1) a separação do critério (b) foi feita depois de medir, e pode
parecer que empurrei a hipótese para passar; (2) H2 vai mudar as estações do
peito, e o alinhamento costas/occipital tem de ser medido de novo lá, não
assumido; (3) o máximo absoluto de 244 mm na base do pescoço continua sem
explicação.

**Próximo passo que recomendo:** H3/H2 juntas, com os critérios medidos em
separado. H3 desce as estações abdominais e H2 corrige as razões de
profundidade do tronco. Levam `upper_back_vs_occiput` como critério herdado de
H1, com a mesma previsão explícita antes de medir.

**Por quê:** o resíduo de −52 mm e o tronco em cabaça vêm das estações do tórax
e do abdómen (INFERRED com concordância numérica). Mexer já no pescoço (H5)
misturava duas causas na mesma medição.
