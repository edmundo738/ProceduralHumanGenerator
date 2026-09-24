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

*(preenchida depois da medição; ver abaixo)*
