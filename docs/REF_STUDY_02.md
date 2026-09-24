# REF STUDY 02 — Como os bons modelos constroem a forma humana (e porque a nossa ainda não)

## Identificação

| campo | valor |
|---|---|
| BUILD | nenhum. Estudo apenas: **não houve alteração de gerador nem de geometria**. |
| COMMIT base | `e7df112` (H3/H2 fechado) |
| VERSION / SEED / PRESET | o nosso modelo é `realistic_female`, seed 42, gerado da árvore via `tools/refstudy/gen_blend.py` (digest ✓) |
| ENV | Python 3.11 + `bpy 5.0.1` headless · numpy/scipy/matplotlib |
| Ferramentas novas | `tools/refstudy2/` (`inspect_assets.py`, `shape.py`, `plots_sections.py`, `tables.py`, `sagittal.py`, `export_cages.py`, `topology.py`) |
| Dados | `docs/ref_study_02/data/` (inventário, rácios ANSUR, descritores de secção, perfis sagitais, topologia) |
| Controlo do instrumento | o instrumento REF01, re-executado para `out/rs2`, reproduz **exatamente** `docs/h3h2_trunk/metrics_h3h2.txt`. |

**Objetivo (uma pergunta).** Que princípios de construção fazem os modelos de referência lerem-se como humanos, onde está conceptualmente limitado o nosso gerador, e o H7 continua a ser a próxima hipótese certa?

**Não incluído.**
- Nenhuma alteração ao gerador.
- H7, H4 e H5 não foram executados.
- Nenhuma malha de referência foi copiada ou importada para o gerador.
- Cabelo, materiais e rosto ficam fora da análise anatómica.

**Rótulos usados.** FACT · MEASURED · OBSERVED · INFERRED · HYPOTHESIS · MODELING PRACTICE · ENGINEERING JUDGMENT · UNKNOWN.

---

## 1. O que as referências são de facto (e o que podem ensinar)

Todas as refs foram abertas e medidas. Os números vêm de `data/inventory.json` e `data/topology.json`.

| ref | o que é realmente (FACT/MEASURED) | pode ensinar | não usar para |
|---|---|---|---|
| **Female base.obj** | 18 577 v, quase só quads, **1 ilha**, pose em T; malha-base de escultura, densa e uniforme | ANATOMIA/PROPORÇÃO (tronco abaixo de 0.74·S) · SILHUETA/FORMA · MODELAGEM/TOPOLOGIA (grelha densa) | larguras acima de 0.74·S (braços em T) |
| **Body Topo.blend** | 5 163 v, 100 % quads, SUBSURF 2, pose A sem pés, traz `topo7.png`: é um **estudo de topologia** | **MODELAGEM/TOPOLOGIA** (loops à volta das mamas, das escápulas e dos glúteos) · DEFORMAÇÃO · perfil sagital e profundidades | larguras entre 0.47 e 0.78·S (mãos na anca, braços contra o tronco); fill entre 0.37 e 0.57 |
| **FemaleCharacter.blend** | 2 160 v, MIRROR + SUBSURF, box-modeling sobre blueprint, **estilizado** | MODELAGEM/TOPOLOGIA (fluxo radial no busto e nos glúteos; do pescoço, pelo trapézio, ao deltoide) · SILHUETA · DESIGN/ESTILO | medidas absolutas (proporções estilizadas; o alinhamento pela canela desloca-a cerca de 80 mm) |
| **Lucia_Prototype_v01.fbx** | MakeHuman `female_generic`, 32 k v, rig com 163 ossos, roupa. **O corpo só tem mãos e cabeça/pescoço; o tronco foi apagado** debaixo da roupa. | DEFORMAÇÃO/RIG · MATERIAL/SHADER · IDENTIDADE DA LUCIA (roupa, escala) | **qualquer medição do tronco (não existe)** |
| **fffemale 11.obj** | extraído de um jogo, só triângulos; **sem tronco na linha média entre z 4.5 e 6.0**; a textura pinta o corpo inteiro | MATERIAL/SHADER · prática de apagar geometria escondida | REFERÊNCIA FRACA/NÃO USAR PARA MEDIÇÃO |
| **whitewalker.blend** | só cabeça e pescoço (926 v) | MODELAGEM/TOPOLOGIA da cabeça | corpo |
| `Female-Body-Base-Mesh.jpg` | grelha em pose A, frente e costas | ANATOMIA (costas: escápulas, sulco da coluna, losango sacral, prega glútea) · TOPOLOGIA | medidas (perspetiva) |
| `eglwbay1.jpg` | loops radiais à volta das mamas, estilizado | MODELAGEM/TOPOLOGIA · ESTILO | anatomia |
| esboço `31e173dd…jpg` | linhas de construção; curva em S com caixa torácica e pelve como duas massas inclinadas | desenho: massas e eixo | medidas |
| imagens ChatGPT/Gemini | Lucia: angolana, 26 anos, curvilínea, crop top, calças cargo, folha em pose A | **IDENTIDADE DA LUCIA** | anatomia (são imagens geradas) |
| `.webp`, `ff_female11_*.png`, `textures/` | vistas fracas / texturas | MATERIAL | medição |

**Prática observada (MODELING PRACTICE, OBSERVED em duas refs independentes).** A Lucia/MakeHuman e o ff11 apagam a geometria escondida pela roupa. Não é anatomia: é orçamento de polígonos. É também um aviso de que nenhuma das duas pode servir de referência do tronco.

**Contraste fundamental (FACT).** As refs corporais são **cascas integradas de quads**: Female base tem 1 ilha e Body Topo é um único corpo. O nosso modelo tem **85 ilhas sobrepostas** e 107 poles de valência 8 nas tampas. As transições (deltoide→braço, pescoço→tórax, glúteo→coxa) são, no nosso modelo, **interseções entre peças**, e não superfície contínua.

---

## 2. Estudo de desenho: o que faz uma figura ler-se como humana antes de qualquer detalhe

A literatura de desenho é MODELING PRACTICE: é regra artística, não facto anatómico. Onde a anatomia ou as medições a confirmam, isso fica dito.

1. **Duas massas rígidas, a caixa torácica e a pelve, ligadas por uma cintura flexível.** Vilppu constrói a figura a partir do oval da caixa torácica e das massas da pelve, com a linha de ação primeiro e o detalhe por último [Vilppu/AWN](https://www.awn.com/animationworld/vilppu-drawing-online-seeing-anatomical-masses), [Russell Collection](https://russell-collection.com/what-is-gesture-drawing-in-painting/). A cintura "não é um cilindro de largura igual; é a zona de transição entre duas massas sólidas" [Jerwood](https://jerwoodvisualarts.org/blog/how-to-draw-a-torso/).
2. **As massas inclinam em sentidos opostos na vista lateral.** A pelve inclina-se para a frente em cima e empurra para trás em baixo; a caixa torácica faz o contrário, para a frente em baixo e para trás em cima [GVAAT](https://gvaat.com/blog/how-to-draw-a-female-torso/). A inclinação da pelve é muitas vezes oposta à da caixa torácica, o que dá mais estiramento à frente e uma mudança de ângulo mais marcada atrás [Love Life Drawing](https://www.lovelifedrawing.com/pelvis-anatomy-for-drawing/).
   - **Confirmado por medição nas nossas refs** (secção 3.2), e com base anatómica (FACT): lordose lombar e cifose torácica normais em mulheres assintomáticas, com LL 50.5° ± 9.3 e TK 33.9° ± 11.3 [PMC4771498](https://pmc.ncbi.nlm.nih.gov/articles/PMC4771498/). A coluna e a pelve equilibram-se à volta do eixo das ancas [Legaye et al.](https://ncbi.nlm.nih.gov/entrez/query.fcgi?amp=&amp=&amp=&cmd=Retrieve&db=PubMed&dopt=Abstract&list_uids=11931071).
3. **A cintura aperta nas duas vistas**, frente e lado. A silhueta muda de direção em pontos definidos: axila, costelas inferiores, cintura, crista ilíaca, trocânter/anca, prega glútea.
4. **Marcos posteriores visíveis** (OBSERVED em Female-Body-Base-Mesh.jpg e MEASURED nas secções): sulco da coluna, escápulas, losango sacral, dois lobos glúteos, fenda interglútea e prega glútea.
5. **Os ombros ficam fora da caixa torácica.** O deltoide é a massa mais larga da parte superior do corpo: nas mulheres do ANSUR, o bideltoide mede 1.28 × a largura da anca e o peito só 0.60 × o bideltoide (MEASURED).
6. **O pescoço sai de uma abertura oblíqua**, mais baixa à frente do que atrás. A abertura torácica superior desce para a frente. Na mulher é mais oblíqua, e a incisura jugular fica ao nível de T3, contra T2 no homem [Gray's/Clinical Gate](https://clinicalgate.com/2015/03/17/thorax-overview-and-surface-anatomy/) (FACT). No ANSUR, cervicale − suprasternale ≈ 0.041·S, cerca de 70 mm a 1700 (MEASURED).
7. **As mamas são duas massas sobre a parede torácica, dos dois lados do esterno.** A base da mama assenta sobre o grande peitoral, entre a 2.ª e a 6.ª costelas; a prega inframamária é o limite inferior [Plastic Surgery Key](https://plasticsurgerykey.com/anatomy-for-plastic-surgery-of-the-breast/), [Medscape](https://emedicine.medscape.com/article/1273133-author) (FACT). Não são uma prateleira única na linha média.

**Resposta curta (INFERRED).** Uma figura lê-se como humana pelas **relações e orientações das massas grandes**, e não pelas medidas absolutas: duas massas rígidas com inclinação oposta, cintura a apertar nas duas vistas, ombros para fora da caixa torácica, pelve com massa posterior bilobada, e marcos posteriores na linha média.

**Prova disto nas nossas próprias refs (MEASURED).** As refs estão **fora** das médias ANSUR e leem-se como humanas na mesma. A profundidade da cintura é 154–176 mm (a 1700) contra uma média ANSUR de 223 mm, **abaixo do p5 (177)**. A profundidade do peito é 222–234 contra uma média de 258. São figuras magras e idealizadas. O que partilham entre si, e nós não, são as relações da secção 3.

---

## 3. TRONCO: continuidade caixa torácica → lombar → pelve → glúteo (a secção mais funda)

Normalização igual ao REF01: estatura 1700, pés em z = 0, x centrado. Validade das larguras:
- Female base e FemaleCharacter só abaixo de 0.735·S.
- Body Topo não tem larguras válidas no tronco; só profundidade e linha média.

### 3.1 Tamanho da massa torácica (MEASURED)

| medida @1700 | nossa | ANSUR ♀ média (p5–p95) | refs |
|---|---|---|---|
| chest breadth | ~352 | 281 (252–314) | a 0.72·S: 252 / 264 |
| chest depth | 314 | 258 (216–307) | 222 / 234 / 222 (máx.) |
| biacromial/S | 0.226 | 0.224 (0.208–0.240) ✓ | — |
| bideltoid/S | 0.256 | 0.277 (0.250–0.306) | UNKNOWN (braços em T/A impedem a medição) |
| chest/bideltoid | **0.835** | 0.598 (0.555–0.643) | — |
| chest/hip | **~0.94** (0.83 a 0.72·S) | 0.763 (0.682–0.846) | 0.80 / 0.81 (chest ao nível do peito vs hip máx.); 0.76 / 0.86 se o peito for tomado a 0.72·S |
| waist depth | 225 | 223 | 154 / 176 / 170 |

INFERRED: o esqueleto do ombro está certo, mas a **massa torácica está acima do p95 do ANSUR em largura e em profundidade**. Por isso o deltoide não sai para fora da caixa torácica e a pelve não fica mais larga do que o tórax. O H7 original ("peito largo demais") estava **certo mas incompleto**.

### 3.2 Orientação: o S é uma propriedade do eixo de massa, não só da linha das costas (MEASURED)

`data/tables_sagittal.txt`, `fig_sagittal.png`. y = 0 na canela a 0.12·S, uma linha de prumo aproximada que depende da postura.

| | nossa | Female base | FemaleChar | Body Topo |
|---|---|---|---|---|
| inclinação do eixo, **pelve** 0.50–0.58 | **−3.3°** | +6.9° | +11.5° | +10.4° |
| inclinação do eixo, lombar 0.60–0.68 | +1.4° | +3.5° | −3.3° | −6.7° |
| inclinação do eixo, **tórax** 0.70–0.78 | **+9.3°** | −12.3° | −29.0° | −12.5° |
| concavidade lombar vs corda (mm) | **19.5** | 54.5 | 51.8 | 68.0 |
| ápice torácico z (costas) | 1310 | 1350 | 1310 | 1340 |
| ápice glúteo z | **945** | 920 | 855 | 895 |
| prega glútea z | 870 | 870 | 800 | 830 |
| nádega − ápice torácico (y, + = à frente) | −9 | +8 | ≈+21 | +15 |

Nas **três refs independentes**:
- a massa pélvica inclina para a frente ao subir;
- a massa torácica inclina para trás;
- a lombar é a charneira quase vertical entre as duas.

É exatamente a regra de desenho da secção 2, ponto 2, agora **medida**.

No nosso modelo:
- o tórax inclina com o **sinal oposto**;
- a pelve não inclina;
- a concavidade lombar é cerca de 1/3 da das refs.

INFERRED: a inclinação +9° do nosso tórax vem sobretudo do busto (`front_scale` da estação do busto), que empurra o centroide para a frente no topo do tórax. A caixa torácica, por baixo, está vertical.

### 3.3 Forma da secção: a caixa torácica não é uma elipse, a pelve não é centrada (MEASURED)

`data/tables_sections.txt`, `fig_sections.png`.

| descritor | nossa | refs válidas |
|---|---|---|
| fill (área / caixa) no tórax 0.72 | 0.79–0.81 (**elipse pura em todas as cotas**) | 0.88–0.91 (retângulo arredondado, costas planas); 0.81–0.85 na cintura e pelve |
| sulco posterior na linha média (0.78 / 0.52) | **0 / 0** | 8, 14, 4 / 22, 18, 8 (coluna / fenda interglútea) |
| sulco anterior (0.78) | 0 | Body Topo 30 (intermamário) |
| \|x\| do ponto mais posterior, 0.72 | ≈0–33 | ≈57 (escápulas) |
| \|x\| do ponto mais posterior, 0.52–0.57 | ≈0–33 | 55–71 (**dois lobos glúteos**) |
| profundidade/largura, 0.72 | 0.82 | 0.73 / 0.88 |
| profundidade/largura, 0.52 | 0.58 | 0.60 / 0.74 |
| anca/cintura (largura) | 1.35 | 1.58 / 1.52 |
| nádega/cintura (profundidade) | 1.16 | 1.32 / 1.31 / 1.22 |

FACT (matemático): cada estação do tronco é uma superelipse convexa com expoente ≥ 2 (`core/topology.py: Section`). Uma curva convexa **não pode** ter sulco na linha média nem dois máximos posteriores laterais. Estas formas medidas nas refs são **impossíveis por construção**, seja qual for o parâmetro escolhido.

### 3.4 Resolução: o tronco não tem vértices para formar anatomia (MEASURED)

`data/tables_topology.txt`, `fig_topology_torso.png` (cage sem Subdivision).

| banda | nossa: faces (aresta mediana) | Female base | Body Topo (× 16 com Subdiv 2) | FemaleChar |
|---|---|---|---|---|
| tórax 0.70–0.80 | **80 (67 mm)** | 2346 (8.8) | 376 (25) | 1518 (12) |
| abdómen/cintura 0.60–0.70 | **104 (49 mm)** | 636 (12) | 908 (10) | 130 (31) |
| pelve 0.47–0.60 | 630 (13, inclui topo das pernas) | 1135 | 1602 | 266 |
| cabeça | **3430 (2.7 mm)** | 3400 | 1618 | 1068 |

FACT: o tronco tem 14 estações × `ring_n = 16`. Mais de metade das faces está na cabeça.

ENGINEERING JUDGMENT: uma forma precisa de cerca de 2 arestas de cage de largura para existir depois da Catmull-Clark. Com 49–67 mm por aresta, isso deixa de fora o sulco da coluna (~30–40 mm), o bordo da escápula, a fenda interglútea e a prega glútea. **Nenhum deformador as pode criar sem vértices.**

Onde as refs concentram geometria (OBSERVED + MEASURED):
- **Body Topo** e **FemaleChar** concentram poles e loops nas zonas de forma e de deformação: à volta das mamas (loops concêntricos), das escápulas (dois sistemas circulares nas costas, Body Topo), dos glúteos (radiais, FemaleChar), da axila/ombro (loops do peito sobre o ombro) e da pelve (Body Topo tem 176 poles-3 e 152 poles-5+).
- **Economizam** no abdómen e nas pernas.
- A orientação das arestas no tronco é, na nossa, 51 % horizontal e 28 % diagonal, contra 31–43 % e 32–50 % nas refs: a malha das refs **segue as massas** e não apenas anéis horizontais.

### 3.5 Continuidades específicas (OBSERVED + INFERRED)

- **Peito → costas.** Nas refs, a secção torácica é um retângulo arredondado de costas planas, com as escápulas como massas laterais posteriores. Na nossa é uma elipse com o ponto mais posterior na linha média, o que dá umas costas "em barril".
- **Pelve → coluna.** Nas refs, a lombar é côncava e a pelve inclina para a frente, de modo que o sacro continua a curva e os glúteos ficam **abaixo e à frente** do ápice torácico. Na nossa, a nádega está 9 mm **atrás** do ápice torácico e a curva quase não existe (o "pilar quase reto" do H3/H2).
- **Glúteo vs lombar.** O glúteo das refs é uma massa bilobada com sulco central e prega inferior (MEASURED: `back_max_absx` e `back_groove`). O nosso é um alargamento da elipse centrada. O ápice glúteo está alto: 945 contra 855–920 nas refs e contra `buttockheight` do ANSUR (0.512·S = 870).
- **Pescoço → caixa torácica.** A inclinação da base (costas − frente, Δz) é 40 mm na nossa e 20 / 60 / 85 nas refs; o ANSUR dá cerca de 70. Com o nosso detetor simples (desvio de 15 mm da coluna do pescoço), **este marcador não discrimina de forma robusta**: fica em UNKNOWN. O máximo de 244 mm na base do pescoço continua UNKNOWN e não é atribuído ao H1.
- **Deltoide → braço.** Nas refs, loops contínuos descem do peito e do trapézio para o deltoide. Na nossa, o braço é uma ilha separada que interseta o tronco. O bideltoide medido é estreito (0.256 contra 0.277·S), mas **nas refs não é medível de forma limpa** (UNKNOWN).
- **Onde o cilindro se torna massa anatómica.** Nas refs acontece nas quatro zonas onde a secção deixa de ser convexa e centrada: escápulas, mamas, glúteos e deltoides. **São precisamente as zonas onde as refs concentram loops e poles.**

### 3.6 O que é anatomia e o que é escolha de modelagem

| forma | tipo |
|---|---|
| inclinações opostas do tórax e da pelve, lordose/cifose | FACT (radiologia) + MEASURED (3 refs) |
| tórax feminino relativamente mais estreito; costelas mais inclinadas | FACT [Nature Sci Rep 2020](https://www.nature.com/articles/s41598-020-67664-5), [ATS 2002](https://www.atsjournals.org/doi/10.1164/rccm.200208-876OC), [ERS Breathe](https://publications.ersnet.org/content/breathe/14/2/131) |
| mamas como massas pares sobre o peitoral, 2.ª–6.ª costelas | FACT |
| abertura torácica oblíqua (base do pescoço inclinada) | FACT |
| sulcos (coluna, fenda interglútea) e lobos glúteos | anatomia (OBSERVED nas refs e na imagem) |
| loops concêntricos à volta das massas; X-loop no ombro | MODELING PRACTICE ([BSE](https://blender.stackexchange.com/questions/415/what-is-the-ideal-topology-for-a-shoulder-joint), [tese DiVA](https://www.diva-portal.org/smash/get/diva2:1218697/FULLTEXT01.pdf), [No Starch](https://nostarch.com/download/samples/Blender_ch5.pdf)) |
| cintura e anca muito marcadas; "ideais" de nádega e mama | DESIGN/ESTILO e preferência estética ([PRS 2016](https://journals.lww.com/plasreconsurg/abstract/2016/06000/redefining_the_ideal_buttocks__a_population.18.aspx)): **não é anatomia** |
| magreza das refs | ESTILO / idealização (MEASURED: abaixo do p5 do ANSUR) |

---

## 4. Investigação externa: síntese e hierarquia

| fonte | tipo | uso aqui |
|---|---|---|
| PMC4771498 (101 adultos, radiografias) | académico | LL/TK normais em mulheres: FACT de que existe S, não é um alvo de malha |
| Legaye et al. 2002 · Le Huec et al. 2019 ([Springer](https://link.springer.com/article/10.1007/s00586-019-06083-1)) | académico | a coluna equilibra-se sobre as ancas (linha de gravidade cerca de 9 mm à frente das cabeças femorais); TK ≈ 0.75 × LL |
| Gray's (via Clinical Gate) | anatomia de referência | abertura torácica oblíqua; incisura jugular em T3 na mulher |
| Bellemare et al. 2003 (ATS) · García-Martínez (via ERS) · Sci Rep 2020 | académico | tórax feminino desproporcionalmente menor; costelas mais inclinadas |
| literatura de cirurgia plástica da mama | clínica | base da mama sobre o peitoral, 2.ª–6.ª costelas |
| SMPL ([Loper et al. 2015](https://institute-tue.ellis.eu/en/publications/smpl-2015)); Allen et al. 2003 | académico | **uma topologia fixa, de resolução espacialmente variável e quads limpos, mais um espaço de forma PCA sobre scans CAESAR**: o estado da arte separa topologia de forma, e a forma vem de dados de população |
| QuadriFlow / Instant Meshes ([Huang et al. 2018](https://stanford.edu/~jingweih/papers/quadriflow/)) | académico | singularidades (poles) prejudicam a Catmull-Clark e devem ser poucas e bem colocadas; remeshing guiado por campo |
| Blender Manual (Subdivision Surface) · Blender Human Base Meshes ([3.6](https://wiki.blender.org/wiki/Reference/Release_Notes/3.6/Asset_Bundles), [4.0](https://developer.blender.org/docs/release_notes/4.0/asset_bundles/), [CG Channel](https://www.cgchannel.com/2023/06/download-blender-studios-free-human-base-meshes/)) | doc técnica / Blender Studio | as bases profissionais são volumes fechados em quads para Subdivision; a base realista masculina de 4.0 foi **refeita a partir de dados de scan**. Sugestão de refs futuras (CC0), por obter e medir. |
| Vilppu, GVAAT, Love Life Drawing, Jerwood | desenho (prática) | massas, linha de ação, inclinações opostas: MODELING PRACTICE, confirmada acima por medição |
| BSE, tese DiVA, No Starch, Sloyd | tutoriais / prática | loops seguem músculos; X-loop no ombro; poles 3/5 em zonas calmas: **técnica, não anatomia** |

**Não verificado nesta ronda (UNKNOWN):** textos primários de Bay Raitt, Loomis, Bammes e Hampton. As afirmações de desenho acima apoiam-se nas fontes citadas, não nesses autores.

---

## 5. Matriz de princípios

| princípio | evidência nos nossos modelos | evidência externa | relevância para o gerador | confiança |
|---|---|---|---|---|
| P1. Tórax e pelve são duas massas rígidas com inclinação sagital oposta | MEASURED: eixo das 3 refs pelve +7…+11°, tórax −12…−29°; nossa −3° / +9° | FACT: LL/TK normais; MODELING PRACTICE: Vilppu, GVAAT | alta: é o mecanismo por trás do "pilar reto" | alta |
| P2. A massa torácica feminina é estreita em relação à cintura escapular e à pelve | MEASURED: ANSUR chest/bideltoid 0.60 e chest/hip 0.76; refs ≈0.76–0.86; nossa 0.835 / 0.94 | FACT: tórax feminino menor | alta | alta |
| P3. A secção torácica é um retângulo arredondado de costas planas, não uma elipse | MEASURED: fill 0.88–0.91 vs 0.79 | anatomia (ângulos das costelas formam a parede posterior; escápulas) | média-alta | média-alta |
| P4. A pelve tem massa posterior bilobada, com fenda e prega | MEASURED: `back_max_absx` 55–71; groove 8–22 | anatomia de superfície; OBSERVED na imagem | alta para o H4 | alta |
| P5. As mamas são massas pares laterais ao esterno | MEASURED: `front_groove` 30 (Body Topo) vs 0; perfil da linha média | FACT (2.ª–6.ª costelas, peitoral) | média; afeta a profundidade e a inclinação do tórax | média |
| P6. O deltoide é a massa mais larga da parte superior do corpo e fica fora da caixa torácica | MEASURED: ANSUR bideltoid/hip 1.28; nossa bideltoide estreita; refs UNKNOWN | anatomia; topologia do ombro | média-alta | média |
| P7. A densidade de geometria segue a forma e a deformação | MEASURED: tronco 80–104 faces vs 636–2346; cabeça 3430 | MODELING PRACTICE; SMPL "resolução espacialmente variável"; QuadriFlow | alta: é o limite de representação | alta |
| P8. Casca integrada, sem peças sobrepostas | FACT: 85 ilhas vs 1 | prática de todas as bases profissionais | alta a longo prazo; arquitetura (dívida) | alta (como diagnóstico) |
| P9. A base do pescoço é oblíqua (frente mais baixa) | ANSUR ≈ 70 mm; refs 20–85; nossa 40 (detetor fraco) | FACT (abertura torácica) | média | baixa (medição fraca) |
| P10. Ler-se humano depende de relações, não de médias | MEASURED: as refs estão abaixo do p5 do ANSUR em profundidade da cintura | SMPL: forma como espaço de variação | alta para a CharacterSpec da Lucia | alta |

## 6. Matriz de problemas

| problema atual | evidência | mecanismos possíveis | refs que ajudam | intervenção candidata |
|---|---|---|---|---|
| Massa torácica grande demais | largura ~352 e profundidade 314, ambas > p95 do ANSUR; chest/bideltoid 0.835 | `chest_half = shoulder_half·0.9·1.03`, ligado ao ombro e não à caixa torácica; o busto soma profundidade | ANSUR, Female base, FemaleChar | **H7a**: dimensionar a caixa torácica pelas suas próprias medidas (chest/biacromial, chest/hip, chestdepth) e não como fração do ombro |
| Inclinação invertida do tórax / pelve sem inclinação | eixo +9° / −3° vs −12…−29° / +7…+11° | estações horizontais empilhadas com y_offset quase constante; busto como prateleira anterior | as 3 refs, perfil sagital | **H4a**: eixo sagital de duas massas (offsets y por estação a partir de ângulos de tórax e pelve; `tangent`/`front` já permitem planos inclinados) |
| Lombar pouco côncava; nádega atrás do tórax | 19.5 vs 52–68; −9 vs +8…+21 | consequência de H4a + profundidade da pelve posterior | Body Topo, Female base | medir depois do H4a antes de mexer mais |
| Glúteo alto e sem forma | ápice 945 vs 855–920; ANSUR 870; groove 0; sem lobos | convexidade da superelipse; densidade | FemaleChar (radial), Body Topo | **H4c** (altura), **H4b** (forma: exige extensão da representação) |
| Tórax "barril" | fill 0.79; ponto mais posterior central | superelipse única com expoente 2 | Female base, Body Topo | parte do H7a (expoente/costas planas é paramétrico); escápulas exigem representação (dívida) |
| Busto numa só massa | `front_groove` 0; frente da linha média +168 | busto modelado como `front_scale` da estação | Body Topo (loops concêntricos), imagens | **H7b** (mamas como massas pares): exige representação (dívida) |
| Sem sulcos nem marcos posteriores | groove 0 em todas as cotas | convexidade; 16 amostras por anel | Female-Body-Base-Mesh.jpg, Body Topo | extensão de estação r(θ) não convexa **ou** primitivas de massa (dívida, só com hipótese que o exija) |
| Tronco sub-resolvido | 80–104 faces, arestas de 49–67 mm | `ring_n = 16`; 14 estações; mais de metade das faces na cabeça | todas as refs | densidade regional por banda (ENGINEERING JUDGMENT; toca nos pins; só com pré-registo) |
| Transições entre peças | 85 ilhas; braço, pescoço e perna sobrepostos | arquitetura de peças | Female base, Body Topo | **dívida arquitetural**; nada agora |
| Deltoide estreito | 0.256 vs 0.277·S | `deltoid_half` | ANSUR | monitorizar no H7a; hipótese própria depois |

---

## 7. H7: reexame e reformulação

O problema é largura? Profundidade? Posição? Forma da caixa torácica? Transição do ombro? Relação tórax–coluna? Falta de massas intermédias? **Resposta: é uma combinação, e os componentes têm estatutos diferentes.**

| componente | estatuto |
|---|---|
| largura da caixa torácica | **confirmado** (MEASURED, ANSUR e refs) |
| profundidade da caixa torácica | **confirmado** (> p95) |
| forma da secção (costas planas) | confirmado (fill); parcialmente representável |
| orientação (inclinação para trás) | **confirmado**, mas é o H4a (eixo) |
| mamas como massas pares | confirmado como diferença; **não representável** hoje |
| transição do ombro / deltoide | ANSUR sim; refs UNKNOWN |
| relação tórax–coluna | medida pelo eixo; pertence ao H4a |

**Reformulação proposta (HYPOTHESIS, ainda não pré-registada):**

- **H7a (massa da caixa torácica).** A caixa torácica deve ser dimensionada pela sua própria relação com a cintura escapular e a pelve (chest/biacromial, chest/hip, chest depth), e não como fração do ombro. Reduzir largura e profundidade para dentro da gama ANSUR deve:
  - pôr chest/bideltoid e chest/hip dentro de p5–p95;
  - reduzir o fill "barril";
  - **sem** tocar no biacromial nem nas junções.

  Candidata: expoente de superelipse e `back_scale` do tórax (dentro da representação atual). Critérios a congelar **antes** de medir. **Monitorizar** (não otimizar): a inclinação do eixo torácico, porque parte da inclinação invertida pode vir do volume do busto.
- **H7b (mamas como massas pares).** Adiada: requer extensão da representação.
- A orientação passa para o **H4a**.

## 8. H4: uma hipótese ou várias?

**Dividir.** A evidência mostra três mecanismos distintos:

| | pergunta | representável hoje? | evidência |
|---|---|---|---|
| **H4a** eixo sagital das massas | tórax e pelve inclinam em sentidos opostos? | **sim** (y_offset por estação; `tangent`/`front` permitem planos inclinados) | eixo nas 3 refs; LL/TK |
| **H4c** altura do glúteo e da prega | o ápice e a prega estão à altura certa? | sim | 945 vs 855–920; ANSUR 870 |
| **H4b** forma posterior da pelve | lobos, fenda, prega | **não** (convexidade) | groove, `back_max_absx` |

O "pilar quase reto" do H3/H2 **não** é simplesmente "precisa do H4". É sobretudo o H4a (orientação das massas), agravado pelo volume torácico (H7a). As estações horizontais **chegam** para o H4a e o H4c. **Não chegam** para o H4b.

## 9. Precisamos de mudar a representação por estações?

**Para já não; a prazo sim, mas só com uma hipótese que o exija** (ENGINEERING JUDGMENT, sustentado pelo FACT da convexidade e pelo MEASURED da densidade).

Opções registadas como dívida, **por ordem de invasividade**:
1. Planos de estação inclinados: já suportado por `Section.tangent/front`, não usado no tronco.
2. Densidade regional (`ring_n` e estações por banda no tronco).
3. Perfil radial não convexo por estação, r(θ) com harmónicos ou deslocamentos locais, para sulcos e lobos.
4. Primitivas de massa anatómica (mamas, glúteos, escápulas, deltoides) combinadas numa casca única com remeshing guiado por campo (QuadriFlow).

A opção 4 é a mais próxima das refs e do estado da arte, e é refactor arquitetural: **proibido agora** sem evidência de necessidade para a hipótese corrente.

---

## 10. As 10 perguntas

1. **O que as nossas refs têm em comum?** (MEASURED/OBSERVED)
   - cascas integradas de quads;
   - tórax em retângulo arredondado de costas planas;
   - lombar côncava de 52–68 mm;
   - eixo com pelve para a frente e tórax para trás;
   - pelve com massa posterior bilobada e sulcos na linha média;
   - geometria concentrada onde a secção deixa de ser convexa (mamas, escápulas, glúteos, ombros).
2. **O que torna a silhueta convincentemente humana?** As relações e orientações das massas grandes (secção 2), e não as médias. Prova: as refs leem-se como humanas estando abaixo do p5 do ANSUR em profundidade da cintura.
3. **Que princípios de modelagem são independentes da ref?** P1, P2, P3, P4, P5, P7, P8.
4. **O que é só estilo?**
   - a magreza das refs;
   - o exagero de cintura e anca da FemaleChar;
   - os "ideais" estéticos de nádega e mama;
   - a disposição exata de loops e poles (cada modelador usa a sua, com os mesmos princípios).
5. **O que é suportado por anatomia/antropometria?**
   - curvas sagitais;
   - tórax feminino relativamente estreito;
   - mamas sobre o peitoral entre a 2.ª e a 6.ª costelas;
   - abertura torácica oblíqua;
   - rácios ANSUR (como restrições, numa população militar).
6. **Onde o gerador está conceptualmente limitado?**
   - estações convexas centradas (sem sulcos nem lobos);
   - 16 amostras e 14 estações no tronco;
   - densidade na cabeça e não no tronco;
   - peças sobrepostas em vez de casca integrada;
   - caixa torácica derivada do ombro;
   - eixo sagital sem inclinações por massa.
7. **O H7 continua a ser a melhor próxima hipótese?** **Reformulado, sim, como H7a** (massa da caixa torácica em largura, profundidade e forma, dentro da representação atual). A orientação passa para o H4a. As mamas pares ficam em dívida (H7b). Alternativa defensável: fazer o **H4a primeiro**, porque é o sinal mais consistente nas três refs. A minha recomendação está na avaliação final.
8. **O H4 fica único ou divide-se?** **Divide-se** em H4a (eixo), H4c (altura) e H4b (forma, que depende da representação).
9. **É preciso mudar a representação por estações?** Para o H7a, o H4a e o H4c não. Para o H4b, o H7b e os sulcos, sim. Fica como dívida, com as opções ordenadas acima.
10. **Que princípios se incorporam proceduralmente sem copiar uma base mesh?** Todos, como relações:
    - ângulos de massa (tórax e pelve) → offsets e planos de estação;
    - rácios de massa (chest/bideltoid, chest/hip, chest/buttock depth) → dimensões de estação;
    - forma de secção → expoente e `back_scale`;
    - mais tarde, massas pares e lobos → perfil radial ou primitivas;
    - densidade por região → `ring_n` regional.

    Nada disto exige vértices de uma ref.

## 11. O que NÃO devemos fazer

- **Não** empurrar o glúteo para baixo ou para trás para "parecer melhor" antes do H4a: o problema principal é a orientação das massas.
- **Não** tentar criar sulcos, lobos ou escápulas com deformadores sobre 16 amostras convexas: é impossível por construção e produz artefactos.
- **Não** subir densidade ou polígonos como "melhoria": só com hipótese e medição (P7 é um limite de representação, não um objetivo).
- **Não** copiar, importar ou deformar Female base, Body Topo ou MakeHuman, nem transferir as suas posições de loops.
- **Não** usar a Lucia FBX nem o ff11 para medir o tronco (não existe geometria).
- **Não** usar as larguras das refs acima de 0.735·S (T/A-pose), nem as da Body Topo no tronco.
- **Não** tratar a magreza das refs como alvo, nem as médias ANSUR como forma final: ANSUR = restrições; refs = relações.
- **Não** tratar ideais estéticos de cirurgia plástica como anatomia.
- **Não** fazer o H7a e o H4a na mesma experiência.
- **Não** fazer refactor arquitetural (casca integrada, primitivas) sem uma hipótese pré-registada que o exija.
- **Não** "corrigir" o pescoço grosso nem atribuir os 244 mm ao H1.

---

## Figuras

- `ref_study_02/fig_sections.png`: secções a 0.78…0.50·S sobrepostas; contaminações marcadas.
- `ref_study_02/fig_sagittal.png`: perfis da linha média (costas e frente) com pontos de viragem, e eixo de massa do tronco.
- `ref_study_02/fig_topology_torso.png`: cages sem Subdivision, frente, lado e costas; poles 3 (azul) e 5+ (vermelho).

Limitações declaradas:
- A frente da linha média passa entre as mamas, por isso não mede o ápice do busto.
- O alinhamento pela canela depende da postura: a FemaleChar desloca-se cerca de 80 mm, por isso só uso as suas inclinações e amplitudes.
- A nossa cage mostra peças sobrepostas.
- O pico da Female base a z ≈ 1360–1400 no perfil frontal é um artefacto.

## Reprodução

```bash
PY=/home/user/.venv-hcg/bin/python
HCG_BUILD_FROM_TREE=1 HCG_REFSTUDY_WORK=out/rs2 bash tools/refstudy/run_all.sh     # instrumento REF01 (controlo)
$PY tools/headless_blender.py run tools/refstudy2/inspect_assets.py                  # inventário (bpy)
$PY tools/headless_blender.py run tools/refstudy2/export_cages.py                    # cages (bpy)
for s in shape plots_sections tables sagittal topology; do
  HCG_REFSTUDY_WORK=out/rs2 $PY tools/refstudy2/$s.py; done
```
(`inspect_assets.py` e `export_cages.py` exigem as refs extraídas em `out/refs/`.)
