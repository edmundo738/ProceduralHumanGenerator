# H3/H2 — Cotas e profundidades das estações do tronco inferior

**Tipo:** experimento (duas hipóteses implementadas em conjunto, com critérios medidos em separado). **Não é um build.**
**Base:** `97ff706` (H1 aceite) · **Preset/seed:** `realistic_female` / 42 · **Ambiente:** bpy 5.0.1 headless
**Origem:** `docs/REF_STUDY_01.md` §5 (T1, T2) e §9 (H2, H3)

Classificação usada: FACT · MEASURED · OBSERVED · INFERRED · HYPOTHESIS · ENGINEERING JUDGMENT · UNKNOWN.

> **Parte I (§1–§8) é o PRÉ-REGISTO.** Foi escrita e enviada (commit próprio) **antes** de qualquer
> alteração ao gerador e antes de qualquer medição do resultado. Não é editada depois de medir; os
> desvios ficam registados na Parte II.

---

# PARTE I — PRÉ-REGISTO (congelado antes da medição)

## 1. Hipóteses

- **H3 (cotas).** A barriga e o "jarro" inferior vêm de o bloco de estações abdominais estar alto:
  a cintura está a 0.700·S e o umbigo a 0.645·S. Além disso, a estação ilíaca impõe 97 % da largura da
  anca a 0.630·S.
- **H2 (profundidades).** O jarro vem de as meias-profundidades das estações inferiores serem frações
  da meia-largura quase circulares (0.82–0.86). Ficam fora das razões profundidade/largura humanas
  (ANSUR 0.709 na cintura, 0.658 na anca).

## 2. Evidência de partida (MEASURED, sem alteração do gerador)

**Controlo:** a árvore em `97ff706` reproduz exatamente as 51 linhas de `docs/h1_trapezius/metrics_after.txt`.

**Decomposição na linha média** (`tools/refstudy/trunk_diag.py`, cortes por triângulos, @1700):

| cota | profundidade total | contributo do bump glúteo | contributo do busto |
|---|---|---|---|
| 0.70·S | 234 | 9 | 0 |
| 0.649·S | 289 | 17 | 0 |
| omphalion 0.6017·S | **353** | **17** | 0 |
| nádega 0.512·S | 272 | 12 | 0 |

**Leitura (INFERRED):** o bump glúteo contamina pouco (≈ 17 mm no omphalion). O excesso contra o
ANSUR (média 223 mm) vem das **estações**, não dos campos de deformação.

**Larguras nas referências válidas** (femalebase, femalechar; a bodytopo está contaminada pelas mãos):

| | nossa | femalebase | femalechar |
|---|---|---|---|
| cota da largura mínima | 0.697·S | 0.656 | 0.612 |
| largura ≥ 0.90×anca a partir de | 0.632·S | 0.571 | 0.532 |
| largura ≥ 0.97×anca a partir de | 0.524·S | 0.529 | 0.494 |
| `belly_front_fixed` (métrica nova, §5) | **+40** | +4 | −8 (bodytopo +4) |

**Factos de código relevantes (FACT):**
- O loft do tronco é **linear** entre anéis ordenados por z (`body.py`). O `.blend` tem subdivisão,
  pelo que a influência de um anel alastra cerca de 1–2 anéis.
- `_Z["iliac"]` alimenta **ao mesmo tempo** a estação do tronco e o landmark `iliac.L/R`. Esse landmark
  só é consumido pelo bump glúteo (`body.py:110`, centro = iliac − 0.030·S).
- `_Z["waist"]` alimenta a estação da cintura, o landmark `spine_waist` (junta do rig) e os bumps de
  tónus abdominal. Estes últimos só existem com `muscle_tone > 0.55` e `fat < 0.42`, o que não é o caso
  do realistic_female (0.45).
- `_Z["navel"]` só alimenta a estação.
- A largura da estação `navel` é `mix(waist, hip, 0.45)` = **0.840×anca**. A razão ANSUR na cota do
  omphalion é waistbreadth/hipbreadth = **0.847**. A largura está certa; a cota está errada (+74 mm).
- As frações ANSUR à letra (omphalion 0.602 **abaixo** da crista ilíaca 0.611) deixariam a estação
  `navel` (0.84×anca) abaixo da estação `iliac` (0.97×anca). O resultado seria um novo estrangulamento.
  Por isso a estação `iliac` não pode ser movida para a cota da crista.

## 3. O que muda (congelado)

### H3: cotas (larguras, fs/bs, sup e y intactos)

| estação | z/S antes | **z/S H3** | referência | classificação |
|---|---|---|---|---|
| `waist` (`_Z["waist"]`) | 0.700 | **0.635** | largura mínima das refs 3D: 0.612–0.656 (REF STUDY §4.2); ANSUR entre a 10ª costela 0.649 e o iliocristale 0.611 | MEASURED + INFERRED |
| `navel` (`_Z["navel"]`) | 0.645 | **0.602** | ANSUR omphalion 0.6017 (p5–p95 0.580–0.624); a largura da estação já é a razão ANSUR a essa cota | MEASURED |
| estação ilíaca (chave nova `_Z["hip_flare"]`) | 0.630 | **0.566** | ponto médio entre o umbigo (0.602) e a anca (0.530); as refs atingem 0.90×anca a 0.532–0.571 | ENGINEERING JUDGMENT |
| landmark `iliac` (`_Z["iliac"]`) | 0.630 | **0.630 (inalterado)** | ANSUR iliocristale p95 0.632, dentro do intervalo; mantém o bump glúteo **exatamente** onde está (o glúteo é de H4) | decisão de isolamento |

Fora de H3, declarado antes de medir:
- **Busto, inframamária, mamilo e jugulum ficam inalterados.** O §9 incluía o busto em H3. Retiro-o
  porque tem mecanismo próprio (landmarks e bumps das mamas) e não é uma estação abdominal. A cota do
  busto (+66 mm contra ANSUR) fica **aberta**.
- **Efeito colateral declarado:** `spine_waist` (junta do rig) desce com `_Z["waist"]`
  (−0.065·S = −110 mm). Não gera geometria.

### H2: profundidades (só estas quatro; cotas vêm de H3; fs/bs/sup/y intactos)

Regra: meia-profundidade `d = r · largura_total / (fs + bs)`, de modo que profundidade total /
largura total = `r`.

| estação | largura | prof. antes | r antes | **r H2** | **prof. H2** | costas y antes → H2 | fonte de `r` |
|---|---|---|---|---|---|---|---|
| waist | 274.6 | 223.0 | 0.812 | **0.709** | 194.7 | −122.8 → −108.5 | ANSUR waistdepth/waistbreadth (média) |
| navel | 325.2 | 275.9 | 0.848 | **0.709** | 230.6 | −146.8 → −124.3 | idem (o ANSUR mede-a no omphalion) |
| hip_flare | 375.4 | 331.6 | 0.883 | **0.658** | 247.0 | −179.2 → −136.1 | ANSUR buttockdepth/hipbreadth |
| hip | 387.0 | 342.8 | 0.886 | **0.658** | 254.6 | −193.4 → −148.0 | idem |

- **ENGINEERING JUDGMENT:** uso as médias ANSUR gerais (0.709 / 0.658), não o subconjunto de mulheres
  negras (0.746 / 0.686). A regra do projeto é anatomia primeiro e variação para a Lucia depois; essa
  variação deve vir do spec e não de constantes.
- **Fora de H2:** as estações do tórax (jugulum, busto, inframamária) e o períneo. A razão do peito
  medida (0.892) já está dentro de ANSUR p5–p95. O `front_scale` do busto não é tocado (o §9 dizia
  "limitado"; desvio declarado aqui, antes de medir).

## 4. Protocolo de medição (congelado)

Desenho 2×2 sobre `97ff706`, com o mesmo instrumento (`HCG_BUILD_FROM_TREE=1 tools/refstudy/run_all.sh`):

| execução | árvore |
|---|---|
| `rs_h1base2` | base (H1) — já medida, controlo |
| `rs_h3` | só H3 |
| `rs_h2` | só H2 (com as cotas antigas; a chave `hip_flare` = 0.630) |
| `rs_h3h2` | H3 + H2 (é o que fica no commit, se aceite) |

Os critérios de H3 avaliam-se **em `rs_h3`** e os de H2 **em `rs_h2`**. A execução `rs_h3h2` confirma a
combinação e a interação.

## 5. Métricas e critérios

`belly_front_fixed` = frente(0.6017·S) − frente(0.70·S), na linha média e em cotas fixas. Foi
acrescentada ao instrumento **antes** do pré-registo; as outras 51 linhas ficaram idênticas. Existe
porque `abdomen_front_minus_waist_front` usa a cota da largura mínima, que H3 desloca, e poderia
melhorar por construção.

### H3: deve mudar

| critério | antes | alvo | avaliado em |
|---|---|---|---|
| H3.a `waist_nat_z` | 1185 | **[1040, 1115]** (0.612–0.656·S) | rs_h3 |
| H3.b `belly_front_fixed` | +40 | **redução ≥ 20 mm** em rs_h3; **≤ +10** em rs_h3h2 (§9) | rs_h3, rs_h3h2 |
| H3.c `waistbreadth/hipbreadth` | 0.939 | **continua em [0.760, 0.949]** | rs_h3 |
| (informativo) `abdomen_front_minus_waist_front` | +40 | ≤ 10 (§9); reportado, **sem peso** (artefacto possível) | todas |

### H2: deve mudar

| critério | antes | alvo (ANSUR p5–p95) | avaliado em |
|---|---|---|---|
| H2.a `waistdepth/waistbreadth` | 0.929 | **[0.623, 0.809]** | rs_h2, rs_h3h2 |
| H2.b `buttockdepth/hipbreadth` | 0.872 | **[0.590, 0.740]** | rs_h2, rs_h3h2 |
| H2.c `waistdepth` / `buttockdepth` | 342 / 342 | **[177, 284] / [206, 291]** | rs_h3h2 |
| H2.d `chestdepth` | 314 | **[216, 307]** (§9) — **PREVISÃO: FALHA** | rs_h3h2 |

H2.d fica congelado tal como estava no §9. Prevejo que falhe porque as estações do tórax não mudam. O
peito está 22–25 % acima do ANSUR nas **duas** dimensões, com a razão correta (0.892); isso é
território de H7.

### Conjunto

- `waistcircumference/buttockcircumference`: antes 1.000, alvo **[0.749, 0.946]** (§9 punha-o em H3).
  Depende das duas hipóteses, por isso é reportado nas três execuções **sem ser atribuído** a uma só.

### Critério herdado (NÃO é critério de aceitação de H3/H2)

`upper_back_vs_occiput` = −52 (refs −2 / −10 / −22).
**PREVISÃO: inalterado (±4 mm) nas três execuções.** Nenhuma estação acima de 0.72·S muda. O ponto a
1330 mm fica no vão jugulum–busto, a mais de dois anéis da estação mais próxima alterada (a cintura).
Consequência declarada: **H3/H2 não é um teste causal do tórax.** Se o −52 mudar mais de 10 mm, o meu
modelo de localidade do loft está errado e isso tem de ser investigado antes de continuar.

Nota sobre H7 (não faz parte deste experimento): com `chest_half` a partir da chestbreadth ANSUR
(281 mm @1700), as costas no jugulum ficariam em ≈ −114 mm, contra o occipital em −94. O
`upper_back_vs_occiput` passaria a ≈ −20 (INFERRED, aritmética da tabela de estações). É esse o teste
que o tórax pede.

### Devem mudar, mas NÃO são critérios (monitorizados; território de H4)

`lumbar_concavity`, `lumbar_z`, `buttock_apex_z`, `buttock_behind_thoracic`, `thoracic_apex_z`,
`buttock_z`, `buttockcircumference`, `hip_z`. Direção prevista: `buttock_behind_thoracic` desce (a
nádega recua menos); para as restantes, **UNKNOWN**. Não serão usadas para aceitar nem rejeitar.

### Devem permanecer idênticas

- **Exatamente iguais:** `crotchheight`, `thighcircumference`, `calfcircumference`,
  `anklecircumference`, `calf_z`, `knee_min_circ`, `leg_cx_thigh/knee/ankle`, `leg_gap_knee`,
  `neckcircumference`, `neck_z/breadth/depth`, `headbreadth`, `headlength`, `occiput_z`, `nape_z`,
  `nape_recess`, `upper_back_z`, `neckbase_depth_max/excess`.
- **±5 mm** (dois anéis de subdivisão da inframamária): `chest_z`, `chestdepth`, `chestbreadth`,
  `chestcircumference`, `hipbreadth`.
- **Garantias S2/S3:** tudo verde exceto o digest. Contagens 6307/6213, auditoria 0/0/0/0 e
  boundary 962, fingerprint `ad620a90b8eba085`, pins semânticos, J1–J5, mãos, pés, simetria, chão,
  determinismo, S0 33/33 e 72/72.

## 6. O que conta como falha (congelado)

- **H3 FALHA** se, em rs_h3: H3.a estiver fora do intervalo, **ou** H3.b reduzir menos de 20 mm, **ou**
  H3.c sair do intervalo.
- **H2 FALHA** se H2.a ou H2.b estiverem fora do intervalo em rs_h2 **ou** em rs_h3h2.
  - H2.c fora do intervalo em rs_h3h2 conta como falha **parcial**.
  - H2.d fora do intervalo é **falha prevista** e fica registada como tal, não é escondida.
- **O experimento é INVÁLIDO** (paro e reformulo, sem re-pin nem commit do gerador) se qualquer métrica
  "exatamente igual" mudar, se alguma do grupo ±5 mm sair da tolerância, ou se qualquer garantia S2/S3
  falhar.
- **Não há ajuste de parâmetros depois de medir.** Se uma hipótese falhar, os valores da §3 **não** são
  afinados para passar; documenta-se e reformula-se.

## 7. Evidência visual prevista

Renders neutros sem cabelo (frente, lado, 3/4, costas), antes e depois, com a mesma câmara. Previsão
(HYPOTHESIS): o tronco perde a forma de "cabaça" na parte inferior e a barriga saliente reduz-se. A
falta de lordose e o glúteo alto **mantêm-se** (H4). O ombro e o peito largos **mantêm-se** (H7).

## 8. Riscos declarados antes de medir

1. A cota de `hip_flare` (0.566) é ENGINEERING JUDGMENT (ponto médio), não um valor de referência.
2. A razão por estação não garante a razão medida: o loft, a subdivisão e o glúteo (+17 mm) somam-se.
   Prevejo um H2.a medido ≈ 0.75–0.78 (INFERRED), acima da razão por estação.
3. A profundidade continua a ser derivada da largura, agora com a razão ANSUR. Se a largura estiver
   errada, a profundidade herda o erro. Fica como dívida, sem refactor.
4. Tirar profundidade à anca vai mudar o perfil posterior (métricas de H4). Isso não conta como
   melhoria nem como piora de H3/H2.

---

# PARTE II — RESULTADOS

A Parte I foi congelada no commit `1f854c2`, antes de qualquer alteração ao gerador. Os resultados
abaixo vêm das quatro execuções da §4. Métricas completas estão em `docs/h3h2_trunk/metrics_*.txt` e
em `compare_2x2.txt`.

## 9. Implementação (FACT)

Só `human_generator/core/anatomy.py`, exatamente como na §3:
- `_Z`: `waist` 0.700 → 0.635, `navel` 0.645 → 0.602, e uma chave nova `hip_flare` = 0.566 para a
  estação ilíaca. `_Z["iliac"]` (landmark e âncora do glúteo) fica em 0.630.
- As quatro profundidades passam a `depth_for(r, meia_largura, fs, bs)` com r = 0.709 / 0.709 / 0.658 /
  0.658. fs/bs/sup/y e todas as outras estações ficam intactos.
- Nenhum valor foi ajustado depois de medir.

## 10. Resultados por hipótese (MEASURED, @1700 mm)

| métrica | base | só H3 | só H2 | H3+H2 | alvo congelado | veredicto |
|---|---|---|---|---|---|---|
| **H3.a** `waist_nat_z` | 1185 | **1100** | 1185 | 1100 | [1040, 1115] | **PASSA** |
| **H3.b** `belly_front_fixed` | +40 | **+14** (−26) | +14 | **−6** | −20 em H3; ≤ +10 em H3+H2 | **PASSA** |
| **H3.c** `waistbreadth/hipbreadth` | 0.939 | **0.837** | 0.939 | 0.837 | [0.760, 0.949] | **PASSA** (ANSUR 0.847) |
| (inf.) `abdomen_front_minus_waist_front` | +40 | +22 | +14 | +12 | ≤ 10 | sem peso |
| **H2.a** `waistdepth/waistbreadth` | 0.929 | 0.915 | **0.717** | **0.756** | [0.623, 0.809] | **PASSA** (previsto 0.75–0.78) |
| **H2.b** `buttockdepth/hipbreadth` | 0.872 | 0.878 | **0.663** | **0.668** | [0.590, 0.740] | **PASSA** |
| **H2.c** `waistdepth` / `buttockdepth` | 342 / 342 | 300 / 344 | 264 / 260 | **248 / 262** | [177, 284] / [206, 291] | **PASSA** |
| **H2.d** `chestdepth` | 314 | 314 | 314 | **314** | [216, 307] | **FALHA (prevista)** |
| conjunto `waistcirc/buttockcirc` | 1.000 | **0.873** | 1.002 | **0.902** | [0.749, 0.946] | dentro (H3 e H3+H2) |
| herdado `upper_back_vs_occiput` | −52 | −52 | −52 | **−52** | previsão: inalterado ±4 | **previsão confirmada** (0 mm) |

Absolutos contra ANSUR (MEASURED, H3+H2):
- circunferência da cintura 911 (ANSUR 899, p5–p95 750–1082)
- circunferência das nádegas 1010 (1067, 953–1196)
- largura da cintura 328 (313, 264–372)

**Atribuição causal pelo 2×2 (INFERRED a partir de MEASURED):**
- H3 sozinha move a largura mínima e resolve a razão das larguras e das circunferências. Não mexe na
  razão de profundidade (0.915).
- H2 sozinha resolve as razões de profundidade. Não mexe na cota da cintura nem na razão das
  circunferências (1.002).
- A barriga em cotas fixas cai 26 mm com qualquer uma das duas, e só fica ≤ +10 com as duas juntas.
  As duas hipóteses são necessárias e cada uma resolve a sua parte, **sem sobreposição relevante**.

## 11. Invariância: um critério congelado foi acionado (desvio declarado)

**Facto:** várias métricas da lista "exatamente iguais" (§5) mudaram. Pela §6 à letra, o experimento
seria **INVÁLIDO**:

| métrica | base | H3 | H2 | H3+H2 |
|---|---|---|---|---|
| `calf_z` | 365 | 390 | 365 | 365 |
| `knee_min_circ` | 377.0 | 377.0 | 374.0 | 377.0 |
| `calfcircumference` | 389.8 | 390.0 | 389.8 | 393.0 |
| `occiput_z` | 1580 | 1580 | 1590 | 1590 |
| `neck_depth` | 154 | 154 | 156 | 156 |
| `nape_z` / `nape_recess` | 1515 / 18 | = | 1515 / 20 | 1520 / 20 |
| `neckcircumference`, `leg_cx_*`, `leg_gap_knee` | | ±0.1–0.6 | | |

**Investigação (MEASURED):**
1. **Vértices, pure-python, base contra variante:** pernas 0/1752, ombro/pescoço 0/140 e cabeça
   0/3456 vértices diferentes. São **bit a bit idênticos**. Só mudam 48–62 vértices do tronco.
2. **Mecanismo:** o instrumento centra Y pelo centro da caixa envolvente do corpo inteiro e rasteriza
   cada corte numa grelha de 2 mm. Com H2, a nádega deixa de ser o ponto mais posterior (ymin passa de
   −198.8 para −157.2). O centro desloca-se 20.8 mm, com H3 0.1 mm, e a rasterização e os argmax em
   patamares reagem.
3. **Controlo:** a malha **base**, medida com o centramento de cada variante (`measure.py`, parâmetro
   `y_shift`, omissão 0), reproduz **exatamente** todas as mudanças da tabela nas três variantes
   (`docs/h3h2_trunk/control_centering_*.txt`). Única exceção: a `chestcircumference` difere
   0.04–0.06 mm (≤ 0.6 mm no total, dentro do grupo ±5 mm). É influência real da subdivisão junto à
   inframamária.

**Decisão (ENGINEERING JUDGMENT, submetida ao utilizador):** não declarei o experimento inválido. A
regra da §6 existia para apanhar fugas de geometria para fora do tronco, e a identidade bit a bit dos
vértices mais o controlo são um teste mais forte dessa mesma coisa. **A regra, tal como escrita, foi
acionada**, e isto é um desvio ao pré-registo, não uma reinterpretação silenciosa.
Para os próximos pré-registos, o critério de invariância passa a ser **vértices idênticos por região,
mais métricas medidas com o centramento controlado**. Fica registado já aqui, antes do próximo
experimento.

## 12. Métricas monitorizadas (H4; não são critérios)

| métrica | base | H3 | H2 | H3+H2 | refs |
|---|---|---|---|---|---|
| `buttock_behind_thoracic` | +50 | +50 | +10 | **+10** | −8 / −20 / −16 |
| `lumbar_concavity` | 26.5 | 29.4 | 25.3 | **19.7** | 55.7 / 53.7 / 69.7 |
| `buttock_apex_z` | 980 | 935 | 975 | **930** | 910 / 845 / 880 |
| `lumbar_z` | 1185 | 1100 | 1190 | 1085 | 1105 / 1055 / 1100 |
| `thoracic_apex_z` | 1305 | 1300 | 1295 | 1290 | 1330 / 1280 / 1335 |

- **A previsão confirma-se:** `buttock_behind_thoracic` desce.
- **A concavidade lombar PIORA** (26.5 → 19.7). A anca perdeu 45 mm de profundidade atrás e as costas
  torácicas não mudaram, por isso a linha costas–nádega ficou mais reta (INFERRED).
- `buttock_apex_z` desceu 50 mm **sem o bump glúteo se ter movido** (landmark `iliac` intacto). A
  descida vem da estação `hip_flare`.

## 13. Evidência visual (OBSERVED)

`docs/h3h2_trunk/h3h2_2x2.png` (quatro variantes, lado/frente/3-4) e `h3h2_side_back.png`. Sem cabelo,
material neutro, mesma câmara.

- **Base:** barriga "de grávida" de perfil e tronco em cabaça de frente.
- **Só H3:** a barriga desce e encolhe, mas continua como volume baixo. A cintura desce.
- **Só H2:** o perfil afina, mas de frente continua um barril com a cintura alta.
- **H3+H2:** a cabaça e a barriga desaparecem em grande parte. Fica um volume pequeno acima do púbis.
- **Leitura nova e negativa:** de lado e de costas, o tronco de H3+H2 lê-se como uma **coluna quase
  reta**, sem lordose e sem forma glútea. A nádega continua as costas sem se destacar, e a cintura, de
  costas, é fraca. O jarro saiu e ficou à vista a ausência de curva sagital (H4), que antes estava
  mascarada pelo volume.

## 14. Garantias S2/S3 (MEASURED)

| verificação | resultado |
|---|---|
| pytest (antes do re-pin) | 1 falha: só o digest (`c0a50b8a…` → `cb4e8559…`) |
| pytest (depois do re-pin) | 133 passed · 1 skipped · 1 xfailed |
| S0 pure-python / bpy | 33/33 PASS · 72/72 PASS |
| auditoria (três variantes) | 6307 v / 6213 f · non-manifold 0 · boundary 962 |
| fingerprint | `ad620a90b8eba085` (inalterado) |
| digest re-pinado | pure-python `cb4e855996c2f1fd`, mathutils `c7ab2932f5d66ede` (anteriores no comentário) |

## 15. Veredicto

- **H3: PASSA** nos três critérios congelados.
- **H2: PASSA** em H2.a, H2.b e H2.c. **H2.d FALHA, como previsto:** a profundidade do peito não mudou
  (314 contra p95 307), porque o tórax não foi tocado.
- **Critério herdado:** o −52 ficou **exatamente igual**, como previsto. H3/H2 não testa o tórax. A
  hipótese "o resíduo está no tórax" **continua INFERRED**, nem confirmada nem refutada por este
  experimento.
- **Invariância:** a regra congelada foi acionada por um artefacto do instrumento, demonstrado com
  controlo (§11). A decisão de aceitar é do utilizador.
- **Leitura anatómica:** a forma em frente e em corte aproximou-se da humana (razões dentro do ANSUR).
  O perfil sagital ficou mais exposto como problema: a concavidade lombar piorou.
  **Não é "tronco resolvido".**

## 16. Dívida registada (sem refactor)

1. **Instrumento:** o centramento Y pela caixa envolvente faz as métricas depender de regiões
   distantes. Proposta: centrar por um referencial fixo (por exemplo, o ponto médio dos tornozelos) e
   declarar essa mudança com um controlo próprio. Não foi mudado agora para não mudar o instrumento a
   meio de uma comparação.
2. **A profundidade continua derivada da largura** (agora com a razão ANSUR). Uma largura errada
   propaga-se para a profundidade.
3. `hip_flare` 0.566 é ENGINEERING JUDGMENT (ponto médio). Deve passar a ser derivado quando houver uma
   referência para a cota a que a largura atinge 0.97×anca.
4. **A estação `navel` está no omphalion e a crista ilíaca (landmark) acima dela:** a ordem anatómica
   está certa, mas a estação ilíaca do tronco já não tem nome anatómico. Rever quando a pélvis for
   tratada (H4).
5. **Cota do busto (+66 mm) aberta**, fora de H3 por decisão pré-registada.

## Minha avaliação

**Concordo porque:**
- Cada hipótese resolveu exatamente a parte que previa, e o 2×2 mostra-o sem sobreposição.
- As razões ficaram dentro do ANSUR sem se ajustar nenhum valor depois de medir.
- A geometria fora do tronco ficou bit a bit idêntica.
- O jarro e a barriga, que eram os defeitos mais visíveis do tronco, reduziram-se claramente na imagem
  neutra.

**Discordo de:**
- Chamar a isto uma melhoria do tronco sem ressalva. A vista lateral tem agora uma coluna reta, e a
  concavidade lombar piorou (19.7 contra 54–70).
- Considerar o −52 explicado. Este experimento não o podia testar e não testou.

**Riscos:**
1. Aceitar o desvio da §11 cria precedente. Mitigação: o critério de invariância por vértices fica já
   escrito para o próximo pré-registo.
2. Levar H4 a compensar a nádega "achatada" empurrando o glúteo para trás. Isso seria corrigir o
   sintoma: H4 tem de introduzir a curva da coluna, não só volume.
3. A razão ANSUR militar aplicada à Lucia. Tem de vir a ser variação do spec, não uma constante.

**Próximo passo que recomendo:** antes de H4, fazer **H7** (largura do peito a partir da chestbreadth
ANSUR), isolada e pré-registada. A previsão congelável é `upper_back_vs_occiput` ≈ −20
(aritmética da tabela de estações), `chestdepth` para dentro de p5–p95, e nenhuma mudança abaixo de
0.72·S. Depois disso, H4 com o tronco completo estável.

**Por quê:**
- O tronco só está "estabilizado" na metade inferior. O tórax continua 22–25 % sobredimensionado nas
  duas dimensões e é a causa mais provável do −52.
- H4 (curva sagital) depende das costas torácicas como ponto de referência posterior. Fazê-la com o
  tórax ainda grande obrigaria a refazê-la depois de H7.
- É uma recomendação que altera a ordem que aprovaste (H4 antes de H7). **A decisão é tua.** Não
  iniciei nem H7 nem H4.
