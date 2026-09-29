# TORSO TRANSITIONS 01 — estudo dirigido das transições (pós-gate TORSO B)

**Data:** 2026-09-30 · **Ciclo:** T-TORSO-2 · **Branch:** `arena/01a0d51d-proceduralhumangenerator`
**Gatilho:** gate visual do dono sobre TORSO B = **NÃO APROVADO**, com directriz
completa (preservada em §0). Este estudo É a fase "estudar o erro" da directriz:
**nenhuma geometria mudada.**

## 0. Veredicto visual do dono (registo, OBSERVED)

> "O corpo está reconhecível como humanoide, mas a forma ainda denuncia a
> construção procedural."

Diagnósticos por região (palavras do dono): cabeça separada do pescoço; ombros
"quase parabólicos" (complexo clavícula/deltoide/axila sub-representado); tórax
"superfície larga e suavizada" e não caixa 3D; **mamas = deformações colocadas
sobre a superfície** (prioritário: implantação, base, volume, orientação, polos,
sulco inframamário); abdómen com "ondas sucessivas associadas às estações";
cintura não pode ser redução radial; **costas com "lombas de estrada"**
(prioritário: quer continuidade ombros/trapézio→caixa→escápulas→lombar→sacro→
glúteos); glúteos: volume bom (NÃO destruir) mas divisão/lobos "geométricos".
Directriz de método: estudo dirigido → hipótese estrutural → checkpoint →
implementação (SEM pesquisa indefinida); métricas = guardrails, não prova de
humanidade; não polir detalhes antes das massas; corpo = camadas contínuas onde
"muito da anatomia de algo só se tem com o outro" (ex.: quadris com coxas).
**Critério de sucesso: "a silhueta e os volumes parecem pertencer ao mesmo corpo
humano" — visível ANTES de olhar para as métricas.**

## 1. Instrumento novo (mesmo referencial; refs e nós idênticos)

`tools/refstudy/torso_transitions.py` → `docs/head_phaseA/torso_transitions.png`
+ `out/refstudy/transitions.json`. Mede, nas 4 curvas de perfil da linha média
(frente, costas, largura, profundidade; grelha 5 mm, suavização 15 mm):
**nº de extremos locais** (prominence 2 mm, distância 20 mm) e **energia de
curvatura** (média |Δ²|) por junção/região (R1–R10, bandos z do dono); correlação
dos extremos nossos com as cotas das estações; assimetria sup/inf da mama; rampa
pescoço→ombro. Refs: femalebase, femalechar, bodytopo, real005, animeF (ff11
excluída low-poly; lucia só coronal). Larguras de refs em T-pose nos bandos do
ombro incluem braços → ler ESTRUTURA, não absolutos (marcados *).

## 2. Achados (MEASURED; n=5 refs)

### 2.1 As "lombas de estrada" existem e estão NAS estações — confirmado

| região | curva | extremos refs | extremos nós | wiggle refs | wiggle nós |
|---|---|---|---|---|---|
| **R9 lombar (0.55–0.68·S)** | costas | **1 [1–1]** | **3** | 0.21 | **0.57 (2.7×)** |
| R8 costas tórax/escápula | costas | 1 [0–2] | 1 | 0.26 | 0.51 (2×) |
| R5 mama→abdómen | frente | **1 [1–5]** | **0** | 0.19 | 0.19 |
| R4 mama (banda) | frente | 2 [1–2] | 1 | 0.48 | 0.27 |
| R3 tórax (caixa)* | largura | 0 [0–2] | 0 | 4.24 | **0.73 (5.8× menos)** |
| R2 clavícula→ombro/axila* | largura | 1 [0–4] | **0** | 12.23 | **0.75 (16× menos)** |
| R6 cintura | largura | 1 [0–1] | 1 | 0.56 | 0.56 |
| R10 sacro→glúteo→coxa | costas | 1 [0–3] | 1 | 1.88 | 2.42 |

**6 dos 9 extremos nossos estão a ≤18 mm de uma estação** (R9: navel −2 mm,
hip_flare +2 mm; R8: cifose −11 mm; R4: bust +8 mm; R6: waist −16 mm; R1:
deltoid_line −15 mm). As ondas que o dono vê são o padrão de interpolação entre
estações, não anatomia.

### 2.2 Tradução dos diagnósticos visuais para medidas

| diagnóstico do dono | medida correspondente |
|---|---|
| costas "lombas de estrada" | R9: 3 extremos vs 1 [1–1]; 2 nas estações; wiggle 2.7× |
| tórax "superfície suavizada" | R3: wiggle 0.73 vs 4.24 — a largura do tórax é quase constante (tubo) vs afunilamento real da caixa |
| ombros "parabólicos" | R2: 0 extremos, wiggle 0.75 vs 12.2 — a nossa rampa é lisa; real005 tem 6 extremos (clavícula/deltoide/axila) |
| mama "aplicada" | R5: a recessão submamária existe em TODAS as refs (1–5 extremos) e em nós NÃO existe (0); R4: só o ápice |
| abdómen "ondas" | R9/R5: extremos extra nas estações (navel, hip_flare) |
| cintura "cortada" | R6 igual em extremos — o corte é visual (descontinuidade de curvatura), não de extremos |

### 2.3 O que NÃO discrimina (registado, sem inventar)

- **Assimetria sup/inf da mama** (frente, linha média): refs 0.33–4.75 (n=4;
  fb 4.75, r005 3.20, fc 0.56, animeF 0.33), nós 0.75 — DENTRO do spread.
  A linha média não resolve implantação/base/lateral da mama; precisa de cortes
  sagitais LATERAIS (x=±55) — ferramenta da fase de implementação.
- **Dobra glútea inferior**: o plano médio passa pelo sulco central/entre-coxas,
  não pelos lóbulos → não mensurável no perfil actual (o contorno y(x) do painel
  gluteal + P16 ficam como evidência).
- R7 anca: wiggle nosso 5.43 vs refs 4.74 (sem sinal).

## 3. Avaliação do mecanismo (pergunta §3 do dono) — MEASURED no código

O loft entre anéis é **linear**: `topology.py:232` — `v = mix(v0, v1, k/(K-1))`;
os anéis extra da T1 (`subdivide_rings`) também são lineares; por cima corre um
Catmull-Clark nível 1. Consequência: a superfície é C0 por troços entre estações
e o subsurf concentra a curvatura À VOLTA das estações → exactamente o padrão
"extremos nas estações" medido em §2.1.

**Resposta à pergunta:** as estações + superelipses + DeformStack CONSEGUEM
representar os volumes (âncoras anatómicas por região — nada melhor proposto);
**o que não consegue representar a continuidade é a INTERPOLAÇÃO linear entre
elas.** Não é preciso reconstruir o sistema: é preciso substituir o interpolador
(e integrar a arquitectura sagital nas estações em vez de a somar depois).

## 4. Hipóteses estruturais (a testar na implementação, por ordem)

- **H-TT1 (fundação — continuidade C²):** substituir a interpolação linear do
  loft por uma spline cúbica (Hermite/Catmull-Rom) dos PARÂMETROS das estações
  (w, d, y, fs, bs, sup) amostrada em anéis densos. **Zero parâmetros novos.**
  Predição: R9 3→1 extremos; R8/R9 wiggle → ~0.2–0.3; ondas de estação sumirem.
- **H-TT2 (tórax vivo):** com C², o afunilamento da caixa torácica passa a ser
  controlável pelas larguras das estações (R3 wiggle 0.73 → direção 4.2 das
  refs) sem criar ondas.
- **H-TT3 (mama integrada):** mama = volume orientado com base larga (σx ↑),
  transição superior longa, polo inferior curto + **sulco inframamário**
  (recessão submamária: restaura o extremo R5 das refs). Não é amp: é forma.
- **H-TT4 (costas contínuas):** migrar a arquitectura sagital das janelas
  `_SACRAL/_LOMBAR/_ALTA` (campo somado pós-loft) para o y das PRÓPRIAS
  estações; o campo só sobrevive se a medição mostrar que ainda acrescenta.
- **H-TT5 (complexo do ombro):** clavícula/deltoide/axila como estrutura própria
  (estações com assimetria + re-ancoragem do deltoide) — alvo R2: estrutura
  onde hoje há rampa parabólica.
- **H-TT6 (junções inter-região):** anca→coxa e glúteo→coxa medidas e geridas
  como JUNÇÕES (directriz: "a anatomia de algo só se tem com o outro") —
  instrumento de corte lateral x=±55 a construir na implementação.

## 5. Plano de implementação (uma hipótese por passo, renders antes de métricas)

1. **H-TT1** (spline C² no loft) → render 4 vistas → gate visual dono → métricas
   (guardrails P1–P18; pins: contagens mudam só se o nº de anéis mudar).
2. Re-calibrar estações sobre o loft novo (H-TT2; bandas como restrição).
3. H-TT3 mama; 4. H-TT4 costas; 5. H-TT5 ombro; 6. H-TT6 junções.
Sem polimento de detalhes (pele, mamilos, micro-músculos) até as massas passarem
no critério do dono. Sem novas variáveis por descoberta: estrutura primeiro
(directriz §4); parâmetros só os que controlam a estrutura comprovada.

## 6. Validação e classificação

- Renders frente/3-4/perfil/costas + poses ANTES de qualquer métrica; a pergunta
  do dono ("reconheço primeiro uma pessoa ou primeiro a geometria procedural?")
  é o gate. Métricas P1–P18 = guardrails (aproximação ≠ conclusão).
- Classificação obrigatória por região: MELHORIA / REGRESSÃO / SEM MUDANÇA /
  APENAS-NUMÉRICA (métrica melhorou, visual não) = FALSE IMPROVEMENT.
- Preservar: volumes das guardas P8/P12/P18, glúteo com volume (dono), tudo o
  que as bandas já confirmam; substituir: o interpolador linear (demonstradamente
  produtor da aparência artificial, §2.1/§3).

## 7. Proveniência

Refs n=5 (femalebase, femalechar, bodytopo, real005, animeF; ff11 low-poly
excluída; lucia coronal-only; whitewalker/mppled fora do referencial). Perfis do
instrumento comum (measure.py @1700, grelha 5 mm). Instrumento novo idêntico para
refs e nós; parâmetros de detecção registados no código. Mecanismo: leitura
directa do código (topology.py loft; back_curve.py subdivide_rings). Nenhuma
geometria alterada neste estudo.
