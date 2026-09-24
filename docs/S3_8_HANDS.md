# S3.8 — Mãos (contrato da fatia)

Aberta depois de S3.7 (`6b63242`). A BUILD 01 e o render de S3.7 mostram a mão
como uma **pá**: larga, espessa e com os dedos encostados uns aos outros. Esta
fatia mede, corrige na origem e volta a medir. Método: BASELINE → ALTERAÇÃO →
TESTE → MEDIÇÃO → COMPARAÇÃO. Instrumento: `core/integration.hand_metrics` +
`tools/measure.py`.

## 1. O que foi observado e medido

Observação (OBSERVED, render 3/4 e frente): a mão lê-se como uma pá com dedos
justapostos, sem a forma de cunha da mão humana.

| # | Medida no baseline (`6b63242`) | Valor | Referência |
|---|---|---|---|
| largura da mão (extensão da malha ao longo do eixo 2.º↔5.º metacarpo) | **123.6 mm** | 76 mm (mulher, p50) |
| distância entre os MCPs do índice e do mindinho | 61.2 mm | 0.38·L ≈ 66 mm |
| espessura da palma (perpendicular) | **57.2 mm** (0.314·L) | ≈ 28–30 mm |
| comprimento da mão (punho → ponta do médio) | 182.2 mm | 178 mm (mulher, p50) |
| folga entre dedos adjacentes (mín. do médio↔anelar) | **0.7 mm** | > 1 mm |

> Os valores desta tabela foram **re-medidos com o instrumento final**
> (`hand_metrics` v2, §7.3/§7.4) sobre o baseline `6b63242`, num worktree
> separado (`git archive 6b63242`) com o `integration.py` actual: largura
> 123.6 mm (o instrumento intermédio dizia 123.9) e espessura 57.2 (dizia
> 57.4). O comprimento (182.2), o MCP (61.2) e as folgas (0.7) não mudaram.

Mecanismo (medido no código, `generators/hands.py`):

* `half_b = hand_len * 0.285` e a largura dos anéis cresce com
  `(0.84 + 0.30·t)` → meia-largura **57.4 mm** nos nós dos dedos (115 mm de
  largura geométrica, 124 mm medidos na malha);
* `t_half = hand_len * 0.118` → espessura geométrica ≈ 41 mm, medida 57 mm;
* espaçamento dos nós `hand_len * 0.118` = 20.5 mm → 61 mm de índice a mindinho;
* raio dos dedos `hand_len * 0.052` = 9.0 mm (18 mm de largura) com os dedos a
  20.5 mm uns dos outros ⇒ ficam encostados (folga medida 0.7 mm).

## 2. Valores canónicos — fonte e classificação

| Quantidade | Valor | Classificação |
|---|---|---|
| comprimento da mão, mulher p50 | **178 mm** | **FACT (fonte)**: FAA/DOT *Anthropometric Data* Ap. B (mulheres, 50.º percentil) |
| largura da mão (nos metacarpos), mulher p50 | **76 mm** | **FACT (fonte)**: FAA/DOT Ap. B; também 75.2 mm (30 mulheres, Matec 2017), 73.1–77.5 mm (Índia/Etiópia) |
| largura / comprimento | **0.427–0.466** | **FACT (fonte)**: FAA 76/178 = 0.427; 3D scan feminino chinês 82.3/176.7 = 0.466 |
| espaçamento MCP índice↔mindinho | 0.38·comprimento | **INFERRED**: derivado da largura (76 mm) descontando ~5 mm de tecido mole por lado |
| espessura da palma | ≤ 0.165·comprimento | **INFERRED**: mão feminina ≈ 28–30 mm; sem fonte recolhida para a espessura, fica como **limite superior** |

## 3. Critérios (definidos antes do código)

- **H1 comprimento**: `|comprimento − 0.178 m| ≤ 5 %`. (Já passa: 182.2 mm.)
- **H2 largura**: extensão da malha ao longo do eixo 2.º↔5.º metacarpo dentro de
  **±10 % de 0.076 m**.
- **H3 espessura**: extensão perpendicular ≤ **0.165 · comprimento** (≈ 30 mm).
- **H4 nós dos dedos**: `0.36·L ≤ |MCP_índice − MCP_mindinho| ≤ 0.42·L`.
- **H5 dedos separados**: folga mínima entre superfícies de dedos adjacentes
  **≥ 1 mm** (0 = encostados; medido: 0.7 mm no médio↔anelar).
- **H6 polegar livre**: folga polegar↔índice **≥ 5 mm**.
- **H7 regressões**: J1–J5 (S3.7) mantidos; grelha `weld×dissolve` × 2 regimes
  com 0 non-manifold / 0 loose / 0 degeneradas / 0 ngons; 0 pares abaixo do weld;
  S0 nos 3 regimes; pins re-medidos.

## 4. Baseline (medido, `6b63242`)

| Critério | Baseline | Limite | Estado |
|---|---|---|---|
| H1 comprimento | 182.2 mm (1.024×) | ±5 % de 178 | ✓ |
| H2 largura | **123.6 mm** (1.63×) | 68.4–83.6 mm | ✗ |
| H3 espessura | **57.2 mm** (0.314·L) | ≤ 0.165·L (29.7 mm) | ✗ |
| H4 MCP span | 61.2 mm (0.336·L) | 0.36–0.42·L (65.5–76.4) | ✗ |
| H5 folga dedos | **0.7 mm** (médio↔anelar) | ≥ 1 mm | ✗ |
| H6 folga polegar↔índice | > 20 mm (∞ no medidor: > 20 mm) | ≥ 5 mm | ✓ |

Referência de regressão: 5955 v / 5936 f, `quad_ratio` 0.8514, fronteira 802,
espelho 38/5955 (0.638 %), altura 1684.2 mm, 0 flutuantes, chão exato,
silhueta frente 0.5438 m².

## 5. Fora do âmbito

- **Pose dos dedos** (flexão/curvatura de repouso): mantida a actual; S3.8 corrige
  dimensões, não a postura.
- **Musculatura da mão** (tenar, hipotenar): ficam como campos globais do
  `body.py` (o thenar é acrescentado ao nível do corpo); não é alvo desta fatia.
  *Nota acrescentada no fim da fatia*: o campo tenar **teve** de ser tocado —
  era a causa medida do falhanço de H3. Desvio declarado, com o mecanismo e o
  orçamento, em §7.1.
- **Costura topológica** punho↔palma: decisão separada (S3.7 §5.1).

## 6. Resultado (medido depois das alterações)

Alterações (BASELINE → ALTERAÇÃO):

| Sítio | Antes | Depois | Porquê |
|---|---|---|---|
| `hands.py` meia-largura de corpo `half_b` | 0.285·L | **0.190·L** | largura geométrica 2·0.190·1.163·L = 76 mm |
| `hands.py` meia-espessura `t_half` | 0.118·L | **0.066·L** | espessura geométrica ≈ 26 mm (palma humana ≈ 25–30 mm) |
| `hands.py` espaçamento dos nós `sp` | 0.118·L | **0.127·L** | 65.8 mm de índice a mindinho (0.365·L) |
| `hands.py` raio do dedo | 0.052·L | **0.046·L** | dedos deixam de estar encostados |
| `hands.py` raio do polegar | 0.058·L | **0.052·L** | idem, mantendo o polegar mais grosso que os dedos |
| `body.py` campo tenar (amplitude) | 0.0060·estatura (10.2 mm) | **0.0024·estatura (4.1 mm)** | ver §7 (desvio declarado) |
| `body.py` campo tenar (sigma) | (0.030, 0.022, 0.045)·s (51×37×76 mm) | **(0.024, 0.018, 0.030)·s** (41×31×51 mm) | idem |

Medições com `hand_metrics` no build final (`realistic_female`, seed 42,
mathutils e puro iguais ao 0.1 mm):

| Critério | Baseline | **Medido** | Limite | Estado |
|---|---|---|---|---|
| H1 comprimento | 182.2 mm (1.024×) | **180.2 mm (1.012×)** | ±5 % de 178 | ✓ |
| H2 largura | 123.6 mm (1.63×) | **77.5 mm (1.019×)** | 68.4–83.6 mm | ✓ |
| H3 espessura | 57.2 mm (0.314·L) | **28.7 mm (0.159·L)** | ≤ 0.165·L (29.7) | ✓ |
| H4 MCP índice↔mindinho | 61.2 mm (0.336·L) | **65.8 mm (0.365·L)** | 0.36–0.42·L | ✓ |
| H5 folga entre dedos | 0.7 mm (médio↔anelar) | **4.3 / 3.1 / 5.4 mm** | ≥ 1 mm | ✓ |
| H6 folga polegar↔índice | > 20 mm | **> 20 mm** (∞ no medidor) | ≥ 5 mm | ✓ |
| H7 regressões | — | ver abaixo | — | ✓ |

L/R: as duas mãos dão exactamente os mesmos valores (diferença < 1e-9 m) — há
teste dedicado (`test_hands_are_mirror_identical`).

H7 (regressões), medido:

* J1–J5 (S3.7): verdes nos testes sobre o build real
  (`TestS37CriteriaOnRealBuild`, 11 testes + instrumento sintético).
* Grelha `weld × dissolve` × 2 regimes (8 células): non-manifold **0**,
  loose **0**, degeneradas **0**, ngons **0**, fronteira 802, `ops 0/0` em todas.
* `quad_ratio` **0.8514**, 5054 quads / 882 tris / 0 ngons; 5955 v / 5936 f
  (inalterado: esta fatia não acrescenta geometria).
* S0 nos 3 regimes: **33/33, 72/72, 72/72**.
* pytest: **122 passados, 1 saltado** (regime por omissão). No regime forçado
  `HCG_MATHUTILS=0`: **121 passados, 1 saltado** — a falha
  (`test_math.py::test_auto_is_default`) é **pré-existente e não regressão**:
  verifiquei-a no commit `6b63242` num worktree separado (`git archive`), onde
  falha exactamente da mesma forma. O teste exige `preference == "auto"` quando
  o ambiente força `"0"`; contradiz-se com o próprio `test_env_can_force_pure_backend`.
* pins re-medidos nos 2 regimes: digests **`35f7076463f570d9` (puro)** /
  **`2c91d32a7dcc277d` (mathutils)**, fingerprint `ad620a90b8eba085` (inalterado).
* Regiões semânticas: `palm` **86 mathutils / 62 puro** (eram 86 / 76). A
  descida no regime puro é efeito da amplitude tenar reduzida — a fronteira da
  região `palm` é um raio de classificação, não um critério de aceitação.
* Espelho 38/5955 (0.638 %), altura 1684.2 mm, 0 flutuantes, chão exacto,
  silhueta frente 0.5371 m² / lado 0.3473 m² (a frente desce de 0.5438 porque a
  mão já não é uma pá).

### Comparação visual

`out/s3_8/hands_zoom/{out,back,right,left}.png` (final) e o mesmo enquadramento
`out_base/hands_zoom/` no baseline `6b63242` — a mesma câmara, o mesmo
`--hands` (novo modo do `tools/render_views.py`: enquadra punho→ponta do médio
medidos no próprio build). A mão deixa de ser uma pá: perfil de cunha, dedos
separados, polegar com volume próprio.

## 7. Erros meus e desvios desta fatia

1. **Desvio de âmbito declarado**: o §5 dava a musculatura da mão (tenar) como
   *fora do âmbito*. Medi o mecanismo e o campo tenar era **a causa directa** do
   falhanço de H3: com a amplitude antiga (10.2 mm num sigma de 51 mm) a palma
   ganhava ~10 mm em todas as direcções *depois* do loft. Reduzi amplitude e
   sigma e **não toquei em mais nenhum campo do corpo**. Justificação, não
   desculpa: sem isto, H3 só passaria pondo `t_half` tão baixo que a mão
   ficaria com menos de 20 mm de espessura geométrica — mascarar o defeito, o
   que está proibido. O valor 0.0024·estatura (4.1 mm) é **INFERRED**, derivado
   do orçamento de espessura; **não** tenho fonte para a altura da eminência
   tenar e digo-o aqui.
2. **H3 é uma coerência interna, não um facto com fonte**: o limite
   0.165·L (29.7 mm) foi **INFERRED** — não recolhi fonte para a espessura da
   palma. Os critérios com fonte são H1 (178 mm) e H2 (76 mm). H3 fecha com
   28.7 mm, ou seja, dentro de uma banda de 25–30 mm que eu próprio escolhi.
   Classificação: H1/H2 **FACT (fonte)**, H3 **INFERRED**.
3. **Três definições de instrumento erradas, medidas e descartadas** (cada uma
   inflacionava a espessura): projecção dos anéis da palma no eixo punho→ponta
   (dava 66.3 mm); PCA 2D em (x,y) globais (56.7 mm); usar o eixo da palma como
   direcção da espessura (121 mm). A que ficou — largura ao longo de
   `index.mcp↔pinky.mcp` ortogonalizada ao eixo dos anéis, espessura = eixo × largura
   — é a única que respeita os dois eixos anatómicos da palma.
4. **Bug meu na ponta do dedo médio**: a ponta era o vértice com maior
   projecção no eixo dos anéis; como o eixo (média das normais dos anéis) pode
   apontar para o lado oposto, no lado direito o "máximo" era o vértice mais
   próximo do punho ⇒ comprimento medido **90.9 mm em vez de 181.9**. Corrigido
   para "vértice do dedo médio mais distante do punho" (independente do sentido
   do eixo). Alcance real do bug: atingia a medição do lado **direito** quando
   reutilizava o eixo do lado esquerdo; o lado esquerdo dava o valor certo. O
   baseline foi **re-medido com o instrumento final** (§1) precisamente para não
   ficar a comparar números de instrumentos diferentes.
