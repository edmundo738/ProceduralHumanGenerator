# S3.7 — Alinhamento e junções (contrato da fatia)

Aberta depois de BUILD 01 (`1686941`). A BUILD 01 respondeu *sim* à pergunta
estrutural, mas a observação humana + medição identificaram quatro defeitos de
**alinhamento** e **junção** que fazem a figura ler como manequim e não como
pessoa. Esta fatia corrige-os, com critérios escritos **antes** do código e
baseline medido no commit `1686941`.

Método obrigatório: BASELINE → ALTERAÇÃO → TESTE → MEDIÇÃO → COMPARAÇÃO.
Instrumento: `core/integration.junction_metrics` (novo, com testes próprios) +
`tools/measure.py`.

## 1. O que foi observado e o que foi medido

| # | Observação (BUILD 01) | Medição no baseline | Mecanismo encontrado |
|---|---|---|---|
| A | "sem pescoço; a cabeça parece um capuz" | a largura mínima na banda do pescoço é **202.0 mm** = **1.195×** a largura da cabeça (169.0 mm) | as estações de pescoço do tronco têm `neck_half = 0.052·estatura` = **91.6 mm** (183 mm de largura) e sobem até z = 1633 mm (96 % da cabeça): a *coluna do pescoço* engole o crânio |
| B | "ombros com aresta de manga" | largura máxima do ombro **542.2 mm** = **1.413×** o biacromial canónico (383.7 mm) | `deltoid_half = shoulder_half + 0.030·estatura·(1+0.45·tom)` = 266.9 mm (534 mm); a placa do ombro é 26 % mais larga que a linha do ombro real |
| C | degrau visível no tornozelo | salto da silhueta na passagem perna→pé = **54.1 mm** (perna 67.6 mm sobre um bico de 13.4 mm do pé) | a perna termina em z = 70.6 mm com tampa de 68 mm; o pé é um tubo horizontal cujo dorso é uma aresta estreita a 70.9 mm: o cap da perna fica *fora* do volume do pé |
| D | "braços abertos; pernas arqueadas" | cotovelo **+77.1 mm**, punho **+86.4 mm** fora do acrómio (limite 34 mm = 0.02·estatura); joelho **+55.7 mm** fora da anca | `elbow.x = sh·0.92 + 0.055·estatura`, `wrist.x = sh·0.80 + 0.075·estatura`, `knee.x = hip_half·0.72 + 0.010·estatura` |

## 2. Critérios (definidos antes do código)

Instrumento: `junction_metrics(build)`; todas as larguras são secções por
**intersecção de planos** com a superfície (não bandas de vértices) e as cascas
são identificadas pelo **registo de anéis** (`trunk.*`, `arm.L.*`, `head.skull.*`, …),
nunca por heurísticas.

- **J1 — pescoço visível.**
  (a) `largura_min(na banda [linha do ombro, queixo]) ≤ 0.80 × largura_max(cabeça)`;
  (b) `largura_min ≤ 0.35 × largura_max(ombro)` — **acrescentado durante a fatia**:
  a razão pescoço/cabeça sozinha era satisfeita com o pescoço a 116 mm (0.68), mas
  a primeira versão exigia também um troço contínuo de ≥ 25 mm com
  `|dw/dz| ≤ 1.0` e essa exigência foi **refutada por medição**: a banda entre a
  linha do ombro (0.812·estatura) e o queixo (0.858·estatura) tem 78 mm e é
  dominada pela rampa do trapézio, pelo que nenhum corpo plausível a satisfaz. O
  troço vertical fica reportado, não gated.
  (c) **acrescentado**: a rampa do tronco não pode ter parede —
  `max |Δlargura / Δz| entre estações consecutivas ≤ 10 mm/mm` (medido: era
  **82.6 mm/mm**, a "gola" da BUILD 01).
  Justificação do 0.80: numa mulher adulta o pescoço (≈106 mm) é ~0.63 da largura
  da cabeça (≈169 mm); 0.80 deixa margem para pescoços largos sem admitir uma
  coluna que engole o crânio. Limiar é **escolha de engenharia declarada**.
- **J2 — linha do ombro.** `largura_max(ombro) ≤ 1.20 × biacromial canónico`
  (0.2257·estatura). O biacromial é **FACT com fonte** (§3); os 20 % de margem
  cobrem o deltoide e são **INFERRED**.
- **J3 — degrau de junção.** `|salto de silhueta| ≤ 0.10 × largura do pai` na
  cota de passagem (`z*` = extremo do pai), com
  `salto = w_união(z*+1 mm) − w_união(z*−1 mm)`.
  Justificação: um salto maior que um décimo da largura do membro lê-se como
  aresta; a métrica é adimensional (razão), não um número absoluto inventado.
- **J4 — pose de repouso (braços).** `|x_cotovelo − x_acrómio| ≤ 0.02·estatura`
  **e** `|x_punho − x_acrómio| ≤ 0.02·estatura`. É uma **decisão de pose**
  declarada (braços pendentes em vez de A-pose); sujeita a veto.
- **J5 — alinhamento dos membros inferiores.** `|x_joelho − x_anca| ≤ 0.02·estatura`.
  Mesma natureza: decisão de alinhamento declarada.
- **J6 — regressões.** S2/S3 mantidos: 0 non-manifold / 0 loose / 0 degeneradas /
  0 ngons na grelha `weld×dissolve` × 2 regimes; 0 pares de vértices abaixo do
  `weld` por omissão; S0 nos 3 regimes; pins re-medidos.

## 3. Valores canónicos novos — fonte e classificação

| Quantidade | Valor usado | Classificação |
|---|---|---|
| circunferência do pescoço, mulher adulta | 32.5–36.1 cm (média 33.3 cm) | **FACT (fonte externa)**: NHANES/Joshipura (20–29: 32.5; 50–59: 34.8) e Kim et al. 2016 (36.1 ± 2.9) |
| `neck_half` | 0.031·estatura (52.7 mm ⇒ 105.4 mm) | **INFERRED**: 33.3 cm ÷ π = 106 mm de diâmetro; largura frontal ≈ diâmetro |
| biacromial / estatura, mulher | 22.57 % (0.2257) | **FACT (fonte externa)**: Korean Anthropometric Survey 2015 (n=3221); 1988: 22.25 %; 354 mm a 1572 mm de estatura |
| margem do deltoide (por lado) | 0.015·estatura (25.5 mm) | **INFERRED** (tecido mole sobre o acrómio; não há fonte recolhida) |
| largura da placa do trapézio | `(neck_half + shoulder_half)/2` | **DERIVED** de duas grandezas acima (nenhuma constante nova) |
| `shoulder_head_ratio` (spec) | 1.85 → **1.7266** | derivado: 0.2257 × `head_units` (7.65). **Muda o fingerprint do spec** — revisão declarada |

O valor antigo `neck_half = 0.052·estatura` **não tem fonte no repositório**
(nenhum documento do canon o cita): fica registado como constante sem origem
verificável, substituída pela derivada acima.

## 4. Baseline medido (commit `1686941`)

| Critério | Baseline | Limite | Estado |
|---|---|---|---|
| J1a razão pescoço/cabeça | **1.195** | ≤ 0.80 | ✗ |
| J1b troço vertical na banda | **0 mm** | ≥ 25 mm | ✗ |
| J2 ombro / biacromial | **1.413** | ≤ 1.20 | ✗ |
| J3 tornozelo (salto) | **54.1 mm** (perna 67.6 / pé 13.4) | ≤ 6.8 mm (10 % de 67.6) | ✗ |
| J3 punho (salto) | **−4.2 mm** (braço 68.1 / mão 72.3) | ≤ 6.8 mm | ✓ (margem pequena) |
| J4 cotovelo dx | **77.1 mm** | ≤ 34.0 mm | ✗ |
| J4 punho dx | **86.4 mm** | ≤ 34.0 mm | ✗ |
| J5 joelho dx | **55.7 mm** | ≤ 34.0 mm | ✗ |

Referência da BUILD 01 (para comparação): 5891 v / 5872 f, `quad_ratio` 0.849796,
fronteira 802, espelho 38/5891 (0.645 %), altura 1684.2 mm, espelho dos dedos
0.000 mm, pés 257.8 mm (0.997×), 0 flutuantes, chão exato.

## 5. Resultados (medidos, 2 regimes)

| Critério | Baseline | Depois de S3.7 | Limite | Estado |
|---|---|---|---|---|
| J1a pescoço/cabeça | 1.195 | **0.664** (pescoço 105.4 mm, cabeça 169.0) | ≤ 0.80 | ✓ |
| J1b pescoço/ombro | 0.372 | **0.255** | ≤ 0.35 | ✓ |
| J1c rampa do tronco | 82.6 mm/mm | **7.44 mm/mm** | ≤ 10 | ✓ |
| J2 ombro/biacromial | 1.413 (542.2 mm) | **1.180** (452.9 mm) | ≤ 1.20 | ✓ |
| J3 salto tornozelo | **54.1 mm** | **−0.95 mm** | ≤ 8.6 mm | ✓ |
| J3 salto punho | −4.2 mm | **−4.25 mm** | ≤ 6.7 mm | ✓ |
| J4 cotovelo / punho | +77.1 / +86.4 mm | **+17.0 / +13.6 mm** | ≤ 34 mm | ✓ |
| J5 joelho vs anca | +55.7 mm | **+8.0 mm** | ≤ 34 mm | ✓ |
| folga mão↔coxa | (não medido) | **6.0 mm** (sem interpenetração) | > 0 | ✓ |
| folga braço↔tronco | 7.5 mm | **6.6 mm** | > 0 | ✓ |

Regressões S2/S3 (I9) re-medidas nos **4 pares `weld×dissolve` × 2 regimes**:
non-manifold 0, degeneradas 0, loose 0, ngons 0, fronteira 802, `weld`/`dissolve`
no-ops (`ops 0/0`) em todos. Componentes 85, flutuantes 0, chão exato (0 abaixo),
altura 1684.2 mm, espelho **38/5955 (0.638 %)**, Hausdorff dos dedos L/R 0.000 mm,
`quad_ratio` 0.8514 (subiu de 0.8498 porque a rampa do trapézio acrescenta
estações de quads).

Contagens: **5955 v / 5936 f** (eram 5891/5872: +2 estações de tronco, cap do
ombro, rampa). Pins re-medidos: fingerprint `ad620a90b8eba085`, digests
`c58b94868bb0f879` (puro) / `9843b7280144dfe3` (mathutils). S0 nos 3 regimes:
**33/33, 72/72, 72/72**. pytest: **115 passados, 1 saltado**. Silhueta rasterizada:
frente 1 região / 0.5438 m² (era 0.6018 com braços abertos), lado 1 / 0.3473.

### Erros meus registados nesta fatia

1. `cross_section_width` media o **corpo inteiro** quando não recebia a lista de
   faces (devolvia 660 mm no punho) — corrigido para filtrar sempre pela parte.
2. `part_distance` indexava a grelha com o índice do *ponto* em vez do índice na
   lista de pontos — corrigido.
3. Dois testes meus com expectativas erradas (4 vértices onde a caixa regista 8;
   secção em plano tangente, que não existe) — corrigidos para o comportamento
   medido.
4. As estações da rampa do trapézio foram inseridas **fora de ordem por z**; o
   loft segue a ordem de criação, logo o tubo dobrava-se. A ordenação passou a
   ser explícita no `build_body` (ordenar **também revelou** um defeito
   pré-existente: `deltoid_line` a 1380.4 mm vinha antes do peito superior a
   1385.5 mm — o tronco já se dobrava sobre si nesse intervalo antes de S3.7).
5. Bloco de pins reescrito com aspas erradas (a mesma classe do erro de S2):
   apanhado imediatamente pelo `import`, corrigido e re-verificado.

## 5.1 Fora do âmbito (registado, não corrigido aqui)

- **Face** (S4): a cabeça é um ovo com traços sugeridos.
- **Barriga proeminente**: `fat_level = 0.30` do preset + campos de tecido mole;
  medir e decidir em S4/S5.
- **Costura topológica entre cascas** (union/boolean/remesh): decisão separada.
- **Costura do ombro** (a linha de interseção braço/tronco): fica declarada; a
  S3.7 reduziu a largura e criou a rampa, mas não transforma a junção numa
  transição topológica contínua.
- **Mão "em pá"**: a largura da mão medida é 104.4 mm a z = 770 mm (o pulso tem
  68.1 mm de diâmetro); a palma é `0.285·comprimento_da_mão` (= 60.8 mm de
  meia-largura). É a maior falha de silhueta que resta depois desta fatia e é
  geometria de mão — pertence a uma fatia de mão, não a S3.7.
- **Cunha `palm`/`sole`**: `sole` fechou em S3.6 (40 vértices nos 2 regimes);
  `palm` continua em cunha (76 puro / 86 mathutils) — registado.
