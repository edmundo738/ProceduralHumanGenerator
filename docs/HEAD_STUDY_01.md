# HEAD STUDY 01 — a cabeça como estrutura craniana + face

| campo | valor |
|---|---|
| ETAPA | HEAD 01 → **HEAD STUDY 01** (só estudo; **nenhuma alteração ao gerador**) |
| COMMIT base | `df03e98` (gerador inalterado desde `e7df112`; hash das fontes `4bf619f101754494` antes = depois) |
| BUILD medida | `realistic_female`, seed 42, digest da malha `c7ab2932f5d66ede` |
| AMBIENTE | Blender 5.0.1 headless (bpy), numpy/scipy; rasterizador numpy próprio + Cycles CPU (controlo) |
| PERGUNTA | *O que falta, medido contra referências e anatomia, para que a cabeça leia inequivocamente como cabeça humana 3D — e por que ordem se deve atacar?* |
| NÃO INCLUÍDO | qualquer mudança ao gerador; cabelo, materiais, rig, expressão; tronco/pescoço (só medidos como transição) |
| INSTRUMENTO | `tools/headstudy/{export_heads,common,analyse,figures}.py` → `docs/head_study_01/` |

Classes de afirmação: **FACT** (código/literatura) · **MEASURED** · **OBSERVED** (visual) · **INFERRED** · **HYPOTHESIS** · **MODELING PRACTICE** · **ENGINEERING JUDGMENT** · **UNKNOWN**.

---

## 1. Método

### 1.1 Fontes

Seis fontes geométricas e um contra-exemplo, todas exportadas pelo mesmo script.

| fonte | origem | malha exportada (cage / suave) |
|---|---|---|
| **ours** | `generate_character` (build acima) | 6307 v / 97 858 v (Subdivision 2) |
| whitewalker | criatura "White Walker" (cabeça + pescoço, MIRROR + SUBSURF) | 1779 / 28 092 |
| makehuman | `Lucia_Prototype_v01.fbx` → `female_generic.objMesh` (base MakeHuman) | 32 035 |
| femalechar | `FemaleCharacter.blend` | 4203 / 66 927 |
| bodytopo | base de topologia corporal | 5163 / 82 170 |
| femalebase | `Female base` (obj) | 18 577 |
| ff11 | cabeça de jogo, 2347 v, traços **pintados** | **excluída das métricas** (mentón indetetável; só render) |

### 1.2 Normalização e marcos

Todas as fontes são normalizadas da mesma maneira:

- **Escala**: H = vértex→mentón = 226.1 mm (a H do nosso CharacterSpec). As comparações são de **forma e proporção**, não de tamanho absoluto.
- **Eixos**: z = 0 no mentón; y = 0 no ponto médio glabela–opistocrânio; +y = frente.
- **Marcos sagitais**: obtidos por corte exato de segmentos num plano com um desvio de 0.001·largura em relação a x = 0. No espelho exato perdiam-se segmentos (lição de instrumento registada em `common.py`).
- **Mentón**: é a primeira tangente a 45° abaixo do queixo. Só se usa a sua cota z, porque a linha submental é horizontal e o seu y é ambíguo.
- **Validação**: todos os marcos foram verificados visualmente, fonte a fonte.

### 1.3 Pele comparável (FACT, medido)

**A nossa cabeça não é uma superfície.** É uma casca craniana (888 v na cage) com **44 ilhas** coladas por cima:

- 2 orelhas;
- por olho: globo, córnea, pálpebra superior e pálpebra inferior;
- na boca: lábios, gengiva, 2 arcadas, 28 dentes e língua.

Nas referências, globos e dentes são objetos separados e não entram. Para comparar pele com pele, excluem-se da nossa malha o globo, a córnea e a boca interior, e mantêm-se casca, orelhas, pálpebras e lábios. A regra é explícita e exclui as mesmas 36 ilhas na cage e na malha suave.

Sem isto, o mapa "orbitário" media o globo na nossa malha e a nuca nas referências, porque o corte atravessava a abertura do olho. Os recessos saíam em ~180 mm; foi corrigido.

### 1.4 Correções de instrumento feitas durante o estudo (declaradas)

1. O corte sagital em x = 0 perdia segmentos → corte com desvio e cruzamento exato de segmentos.
2. Na abertura do olho sem pele, o contorno frontal apanhava a nuca → só conta pele com y > 0.
3. A largura alar e a da boca, pela regra do mínimo local, nunca disparavam → passou a concavidade máxima (y'').
4. A largura do pescoço a −0.25·H apanhava os ombros → passou a largura mínima do pescoço.
5. A topologia contava os polígonos dos dentes e globos → passou a só pele: 3474 → **1385 v**.
6. O "bizigomático" com y > 20 mm incluía os retalhos das nossas orelhas (chegam a y ≈ 39) → passou a y > 40 mm (face anterior). O valor antigo fica guardado como `W2_old`.

**Consequência para o relatório**: o achado preliminar "face mais larga que o crânio" (R_bizyg/breadth 1.02) **desapareceu** com a correção 6. Não é um défice e não é reportado como tal.

### 1.5 Evidência visual

Todas as figuras usam o mesmo rasterizador (cinza neutro, sem cabelo nem materiais):

- `docs/head_study_01/renders.png`: frente, lado e ¾;
- `wire.png`: cage com polos;
- `profiles.png`: perfil sagital, larguras e para-sagital a x = 34 mm;
- `orbit_maps.png`.

**Controlo independente**: `ours_cycles_neutral.png` (Cycles, material cinza neutro) mostra a mesma geometria. O aspeto "estilhaçado" da nossa face **não é artefacto do rasterizador** (OBSERVED em dois renderizadores). Nos renders numpy ficam salpicos claros residuais; são do instrumento, não da geometria.

---

## 2. Classificação das referências

Legenda: ● fonte primária · ◐ secundária / com ressalva · ○ não usar para isto.

| fonte | ANAT | PROP | FORMA | SILH | PLANOS | CAVID | TOPO | DEFORM | ESTILO | notas |
|---|---|---|---|---|---|---|---|---|---|---|
| makehuman (Lucia fbx) | ● | ● | ● | ● | ◐ | ● (órbita escavada) | ◐ (densa, 16.8 k v cabeça) | ◐ | ○ | modelo estatístico (FACT: MakeHuman); a melhor referência de proporção anatómica |
| femalebase | ● | ● | ● | ● | ● | ● | ● (7 anéis limpos à volta do olho e da boca) | ◐ | ○ | realista; cabeça comprida (g–op 210 @H) |
| bodytopo | ◐ | ◐ | ● | ● | ● | ● | ● (fluxo de retopologia clássico) | ● | ○ | A-pose; queixo/mandíbula estreitos (jaw taper 0.62) |
| femalechar | ◐ | ◐ | ● | ● | ● | ● | ● (1214 v e lê como humana) | ◐ | ◐ estilizada | prova de que a leitura não depende de densidade |
| whitewalker | ○ (criatura) | ◐ | ● | ● | ● | ◐ | ● | ○ | ● | proporções de criatura (TR1 136, S10 1.04); FORMA/PLANOS/TOPOLOGIA, nunca anatomia |
| ff11 | ○ | ○ | ○ | ◐ | ○ | ○ (pintadas) | ○ | ○ | ● MATERIAL | **contra-exemplo**: traços em textura sobre geometria mínima; é o que não queremos |
| imagens Lucia (ChatGPT/Gemini) | ○ | ○ | ◐ | ◐ | ○ | ○ | ○ | ○ | ● IDENTIDADE | malares largos, lábios cheios, nariz largo, sobrancelha forte. Vale para a variação Lucia **depois** da anatomia |
| Female-Body-Base-Mesh.jpg | ○ | ◐ | ◐ | ● | ○ | ○ | ● | ○ | ○ | só topologia/silhueta |

As normas de literatura (secção 4) são FACT populacional. Servem de **restrição e verificação**, não de alvo de malha (regra ANSUR).

---

## 3. Resultados medidos

Todos os valores são MEASURED, em mm@H226. "refs" = intervalo das 5 referências geométricas; o whitewalker entra no intervalo mas é criatura, e isso vai assinalado. Ficheiros: `docs/head_study_01/metrics.txt` e `metrics.json`.

### 3.1 Perfil sagital (S)

| métrica | nossa | refs | leitura |
|---|---|---|---|
| S5 glabela à frente do centro | **86.4** | 97.9 – 104.9 | **testa/glabela 12–18 mm recuada** |
| S7 comprimento g–op | **173.9** | 195.8 – 209.9 | cabeça curta (ver 3.2) |
| S3 convexidade g–sn–pg (°) | **148.8** | 157.8 – 167.8 | a face média "sai" entre testa e queixo, como um focinho |
| S1 projeção nasal prn–sn | **6.8** | 10.7 – 23.5 | nariz sem projeção |
| S6 pronasale à frente do centro | 104.4 | 109.4 – 124.4 | — |
| S2 profundidade do nasion | 7.0 | −0.9 – 6.4 | nasion fundo **porque** a glabela está recuada e o nariz não sobe |
| S4 queixo vs sn | −11.3 | −14.4 – −6.4 | dentro do intervalo |
| S8 inclinação da testa (°) | 15.3 | 14.1 – 23.3 | dentro do intervalo |
| S10 (sn–sto)/(sto–me) | 0.32 | 0.36 – 1.04 | lábio superior curto (fraco: refs muito dispersas) |
| S11 (n–sn)/(sn–me) | 1.39 | 0.86 – 1.32 (whitewalker 2.28) | fraco |

### 3.2 Larguras e razões (W)

| métrica | nossa | refs | leitura |
|---|---|---|---|
| R cefálico largura/comprimento | **0.84** | 0.70 – 0.79 | cabeça redonda e curta (ANSUR, FACT: 154/198 = **0.78**) |
| W1 largura máxima | 145.9 | 141.0 – 156.2 | ok |
| W2 face anterior (y > 40) | 138.9 | 128.3 – 144.2 | ok (o achado antigo era instrumento) |
| W3 frontal mínima (têmporas) | **127.9** | 134.3 – 144.2 | têmporas estreitas |
| R frontal mín./W2 | **0.92** | 1.00 – 1.06 | a testa estreita-se face ao malar; nas refs não |
| R W(0.10H)/W2 (afunilamento da mandíbula) | 0.78 | 0.62 – 0.77 | ligeiramente acima |
| W6 pescoço mínimo | **139.6** | 88.0 – 119.7 | pescoço grosso: **UNKNOWN, não atribuir** (regra) |

**Três medições independentes do comprimento da cabeça** (MEASURED):

- este estudo: g–op = 174;
- REF01 (`docs/h1_trapezius/metrics_after.txt`): 176, abaixo do p5 ANSUR;
- alvo declarado no código: **183** (FACT, `anatomy.head_radii`, FAA/DOT p50).

A razão do alvo, 144/183 = 0.787, bate com o ANSUR. **O alvo está certo; a malha realizada fica 9 mm abaixo dele.** O défice tem origem na glabela (−12…−18) e no opistocrânio (−88 contra −98…−105), não na constante.

### 3.3 Órbita (CV_orbit): a pele à volta do olho (`orbit_maps.png`)

| métrica | nossa | refs (sem makehuman) | makehuman |
|---|---|---|---|
| sobrancelha acima do olho | **6.6** | 13.7 – 21.0 | 42.4 |
| parede medial (ponte nasal − olho) | **5.6** | 17.8 – 21.1 | 46.3 |
| nasion − olho | **3.0** | 15.1 – 20.1 | 43.6 |
| rebordo lateral (x + 0.10·H) − olho | **−18.7** | −4.9 – +2.6 | 23.8 |
| recesso máximo sob a ponte | 6.6 | 6.5 – 13.7 | 41.2 |

OBSERVED no mapa:

- **Nas referências** as curvas de nível contornam o olho como uma **tigela**, e o ponto mais fundo fica no **canto medial**, entre o nariz e o olho. A ponte nasal (x = 0) é uma crista contínua até ao nasion.
- **Na nossa** as curvas são quase horizontais e o olho é uma fenda fina sem tigela. Entre os olhos não há crista nasal; a testa é o ponto mais alto. O rebordo lateral foge 19 mm para trás, com a esfera craniana a curvar.

**Globo ↔ rebordos** (MEASURED na nossa malha; o globo só existe na nossa):

| relação com a córnea (mm) | nossa | norma clínica (FACT) |
|---|---|---|
| pele supraorbitária | **−0.5** | **+10** |
| pele infraorbitária | **+3.3** | **−3** (entre −2 e −3) |
| proeminência malar | +7.6 | +2 |
| supra − infra | **−3.8** | **+13** |

Fontes da norma: [plasticsurgerykey, Globe–Rim Relations](https://plasticsurgerykey.com/infraorbital-rim/) e [Alloplastic augmentation of the midface](https://plasticsurgerykey.com/alloplastic-augmentation-of-the-midface-2/), segundo Jelks & Jelks e Yaremchuk.

INFERRED: **a relação está invertida.** O olho está pousado numa superfície em que a massa de cima (frontal/supraorbitária) falta e a de baixo (malar/maxilar) sobressai. É uma discrepância de ~17 mm no desnível supra − infra, a maior de todo o estudo em termos relativos.

(`docs/head_study_01/ours_globe_rim.json`.)

### 3.4 Nariz e boca (CV_nose_mouth, PL)

| métrica | nossa | refs | leitura |
|---|---|---|---|
| largura alar (concavidade) | 34 | 22 – 41 | ok (canon femininos 31–35, S4) |
| afastamento do nariz à asa | 13.2 | 6.4 – 12.3 | ligeiramente alto |
| PL boca (meio do lábio superior) | **0.15** | 0.36 – 0.89 | frente pontiaguda; falta um arco maxilar/dentário largo |
| PL queixo (0.08·H) | **0.60** | 0.94 – 1.30 | queixo em bico; falta o plano frontal da mandíbula |
| lábio inferior vs Sn–Pg | −3.6 | −2.3 – +5.6 | lábio inferior recuado |
| largura da boca (proxy) | 35 | 36 – 57 | estreita (fraco: proxy frágil) |
| PL testa / crânio / bochecha | 0.97 / 0.89 / 0.33 | 0.91–1.39 / 0.89–1.14 / 0.11–0.23 | dentro ou perto do intervalo |

### 3.5 Transições (TR)

| métrica | nossa | refs | leitura |
|---|---|---|---|
| TR3 comprimento submental | **42.5** | 59.0 – 97.4 | o pescoço começa logo atrás do queixo: não há mandíbula a projetar-se para trás |
| TR2 ângulo cervicomental (°) | 83.7 | 89.8 – 127.2 | agudo; a literatura usa outra definição (C-Me/G-Pg, mulheres 94 ± 6°), por isso **não se compara diretamente** |
| TR1 saliência occipital | 20.1 | 23.2 – 38.6 (whitewalker 136) | occipital pouco saliente sobre a nuca |

### 3.6 Topologia (TP, cage, só pele)

| métrica | nossa | refs |
|---|---|---|
| ilhas na cabeça | **45** | 1 – 5 |
| vértices da cabeça | 1385 | 1214 – 16 814 |
| polos interiores na face | **280** | 32 – 86 |
| aresta mediana face / crânio (mm) | 3.7 / 14.9 | 1.7–5.3 / 7.2–28.5 |
| anéis concêntricos limpos à volta do olho | 0 – 1 (alguns 4) | 2 – 7 |

OBSERVED (`wire.png`):

- **Na nossa**: a cage é uma grelha de box-sphere com leques de triângulos (o "nariz" é um triângulo) e com polos acumulados na boca.
- **Nas referências**: há uma máscara facial com anéis à volta dos olhos e da boca. Uma rede nariz→malar→queixo liga-os, e os polos ficam nas zonas estáticas.

**INFERRED**: a resolução **não** é o gargalo. A femalechar lê como humana com 1214 v e arestas maiores do que as nossas. O que falta é a **organização**: as massas e os anéis.

---

## 4. Pesquisa externa

### 4.1 FACT: anatomia e antropometria

- **Globo ↔ rebordos**: a pele supraorbitária fica ~10 mm à frente da córnea e a infraorbitária ~3 mm atrás. O rebordo supraorbitário projeta-se ~13 mm além do infraorbitário, e a proeminência malar ~2 mm além da córnea. É esta relação que decide se os olhos parecem fundos ou salientes. Fonte: [plasticsurgerykey](https://plasticsurgerykey.com/infraorbital-rim/) e [plasticsurgerykey 2](https://plasticsurgerykey.com/alloplastic-augmentation-of-the-midface-2/).
- **Hertel** (córnea → rebordo lateral): 15.5 ± 2.6 mm nas mulheres [openophthalmologyjournal](https://openophthalmologyjournal.com/VOLUME/9/PAGE/113/FULLTEXT/); normal entre 12 e 21 mm [Nature s41598-022-16131-4](https://www.nature.com/articles/s41598-022-16131-4). *O rebordo lateral está atrás da córnea, mas o supraorbitário está à frente.* O nosso lateral −18.7 mm é compatível com isto; **o que está errado é o supraorbitário.**
- **Convexidade facial** g–sn–pg: 166.6 ± 4.1° nas mulheres [sagepub, jp-journals-10021-1021](https://journals.sagepub.com/doi/pdf/10.5005/jp-journals-10021-1021). A literatura clínica dá 12 ± 4° de convexidade, ou seja, ~168° [plasticsurgerykey, Facial Type](https://plasticsurgerykey.com/facial-type-3/). **A nossa: 148.8°.**
- **Terços**: n–sn ≈ 45 % e sn–gn ≈ 55 % da altura facial anterior [slideshare, soft tissue analysis](https://www.slideshare.net/slideshow/soft-tissue-analysis/245622544). É uma norma clínica aproximada.
- **Espessura dos tecidos moles** (reconstrução facial forense): glabela ~5–6 mm, nasion ~5–6 mm, fim dos nasais ~2–3 mm, philtrum ~11–13 mm, sulco mentolabial ~8 mm. Fontes: [PMC13499785](https://pmc.ncbi.nlm.nih.gov/articles/PMC13499785/) e [PMC12991463](https://pmc.ncbi.nlm.nih.gov/articles/PMC12991463/). **Consequência (INFERRED)**: na metade superior da face a pele é fina (2–6 mm), por isso **a forma visível é essencialmente a do osso**: glabela, rebordos orbitários, nasais e zigoma. Na boca e no queixo a pele é espessa (8–13 mm) e suaviza o osso.
- **Cefálico** (ANSUR II mulheres, via REF01): 154/198 = 0.78.

### 4.2 MODELING PRACTICE (técnica; não é anatomia)

- **Loomis**: esfera craniana com os **lados cortados em plano**, a que se junta um **bloco de mandíbula** afunilado. A linha da sobrancelha e a linha média fixam a construção; a mandíbula varre do canto do plano lateral até ao queixo. O próprio Loomis constrói o crânio por esta ordem: esfera → mandíbula → malares → órbitas [canmom](https://canmom.art/animation/the-human-head-1), [gridmakerpro](https://gridmakerpro.com/grids/artist-guides/loomis-head/). *Nota*: o plano lateral corresponde à zona temporal, e é justamente onde a nossa W3 é estreita.
- **Asaro**: os planos da frente formam um triângulo invertido que se estreita para o queixo, enquanto a parte de trás da mandíbula é muito mais larga [canmom](https://canmom.art/animation/the-human-head-1).
- **Topologia da face** [vsquad](https://vsquad.art/blog/modeling-guide-to-achieving-good-face-topology), [polycount](https://polycount.com/discussion/comment/1367984):
  - começa-se pelos anéis orbitários e oral, que depois se ligam pela estrutura nasolabial;
  - são precisos ≥ 2 anéis à volta do olho e 2–3 à volta da boca;
  - usa-se um laço nariz→malar→sobrancelha para que os anéis do olho não irradiem indefinidamente;
  - os polos de 5 arestas vão para zonas estáticas; os de 6 evitam-se.
- **Subdivision Surface** (Catmull-Clark, FACT do Blender): as singularidades degradam a superfície limite (QuadriFlow, SGP 2018). A subdivisão atenua os relevos em ~25–30 % (lição PREREG).

---

## 5. Princípios encontrados (procedimentais, generalizáveis)

| # | princípio | classe | evidência |
|---|---|---|---|
| P1 | **A face superior é osso com pele fina.** A forma de testa, órbita, nariz alto e malar tem de vir de massas "esqueléticas" (glabela / arco supraorbitário, rebordos, nasais, zigoma), e não de bossas locais. | FACT (tecidos moles) + INFERRED | §4.1; os nossos rebordos não existem (§3.3) |
| P2 | **Uma cavidade é o espaço entre massas.** A órbita lê-se porque a sobrancelha está ~10 mm à frente da córnea, a ponte nasal ~18–21 mm à frente do canto medial e o malar ~2 mm à frente. | FACT + MEASURED | §3.3 (a nossa inverte isto) |
| P3 | **Hierarquia de massas primárias**: crânio (com planos laterais) + bloco mandibular; só depois vêm malares, órbitas, nariz e boca. | MODELING PRACTICE (Loomis) coerente com P1 | §4.2; a nossa tem crânio + máscara e **não tem mandíbula** |
| P4 | **Os marcos da face referem-se às massas.** Se a glabela, o arco maxilar ou o mento se deslocam, as cavidades mudam de profundidade. Esculpir cavidades antes de fixar as massas obriga a refazer. | ENGINEERING JUDGMENT + a lição S4 §10 | S4 §10: as aberturas cortadas numa superfície sem massa ficaram bloqueadas |
| P5 | **O rebordo de uma abertura é uma curva-anel nova, com arestas curtas, e não um corte na grelha.** | FACT (S4 §10, medido) + MODELING PRACTICE | S4 §10: as células passavam de 20.6 para 82.4 mm; refs com 2–7 anéis limpos, a nossa com 0–1 |
| P6 | **Organização > densidade.** | MEASURED | femalechar (1214 v) lê como humana; a nossa (1385 v, 280 polos, 45 ilhas) não |
| P7 | **Os marcos anatómicos restringem; não são alvo de malha.** | regra do projeto | ANSUR e normas clínicas: restrições CharacterSpec |

---

## 6. Défices medidos (síntese, por região)

| região | défice principal | magnitude | classe |
|---|---|---|---|
| A crânio / silhueta | glabela/testa recuada; cabeça curta; têmporas estreitas; occipital pouco saliente | S5 −12…−18; g–op −22…−36 (−9 vs o próprio alvo); cefálico 0.84 vs 0.78; W3/W2 0.92 vs ≥ 1.00 | MEASURED |
| B órbita | sem arco supraorbitário, sem ponte nasal e sem tigela; relação globo–rebordo invertida | supra − infra −3.8 vs +13; parede medial 5.6 vs 18–21 | MEASURED + FACT |
| C nariz | sem projeção; forma de placa triangular (OBSERVED) | prn–sn 6.8 vs 10.7–23.5 | MEASURED |
| D boca / maxila / mandíbula | sem arco maxilar (boca pontiaguda), sem plano mentoniano, sem corpo/ramo mandibular | PL boca 0.15 vs 0.36–0.89; PL queixo 0.60 vs 0.94–1.30; submental 42 vs 59–97 | MEASURED |
| E transições | face = máscara colada à esfera (S3 148.8°); submento→pescoço abrupto; ilhas nas junções (orelhas, lábios, pálpebras) | S3 −9…−19°; 45 ilhas | MEASURED |
| mecanismo | cut-and-project + ilhas; não existe nenhuma estrutura óssea | 280 polos faciais vs 32–86 | FACT (código) + MEASURED |

---

## 7. Proposta de decomposição e ordem (derivada da evidência)

**Ordem proposta: HEAD-A → HEAD-B → HEAD-D → HEAD-C → HEAD-E.**

| ordem | bloco | porquê aqui (evidência) | força da evidência |
|---|---|---|---|
| 1 | **HEAD-A crânio e silhueta** (massas primárias): frontal/glabela e arco supraorbitário como massa; comprimento; planos laterais/têmporas; volume do zigoma; bloco mandibular à escala da silhueta | É referência de todas as métricas de cavidade (P2, P4). O maior défice relativo da órbita, a sobrancelha −0.5 vs +10, é **massa frontal**, não cavidade. O défice de comprimento tem três medições concordantes e uma causa mecânica identificada (glabela e occipital, e não a constante). Hierarquia FORMA → CAVIDADES. | **forte** |
| 2 | **HEAD-B cavidade orbital** (rebordos, ponte nasal alta, tigela, anel de rebordo novo) | Depende de A (sobrancelha, zigoma). É o sinal mais importante para "ler como humano" (ENGINEERING JUDGMENT) e tem a maior discrepância de todo o estudo. Exige P5 (um anel novo), o que liga ao bloqueio S4 §10. | **forte** (a dependência de A é medida) |
| 3 | **HEAD-D maxila / mandíbula / boca** (arco maxilar, plano mentoniano, abertura oral) | A base do nariz assenta na maxila (a abertura piriforme é maxilar, FACT). PL boca e PL queixo são défices grandes, e a mandíbula também condiciona a transição submental (E). | **moderada** |
| 4 | **HEAD-C nariz / cavidade nasal** | Assenta no nasion (A/B) e na maxila (D). A largura alar já está no intervalo; o défice é de projeção, uma forma local sobre as massas. | **moderada**; a ordem entre C e D é a menos determinada |
| 5 | **HEAD-E transições** (face↔crânio, submento↔pescoço, junções das ilhas) | Pela hierarquia vêm por último. O submento toca no pescoço, que está sob restrições (244 mm UNKNOWN, não mexer). Parte de E resolve-se com A e D. | forte, pela hierarquia |

**Não recomendado** (evidência contra): começar por B ou C diretamente. É repetir S4 §10, que escavou e cortou numa superfície sem as massas de referência e ficou bloqueado.

### 7.1 Primeiro candidato dentro de HEAD-A (HYPOTHESIS, para pré-registar só se o utilizador escolher)

**HEAD-A1: massa frontal-glabelar e supraorbitária.**

- **OBSERVED/MEASURED**:
  - glabela a 86 mm, contra 98–105 nas refs;
  - sobrancelha −0.5 mm atrás da córnea, contra +10;
  - g–op 9 mm abaixo do próprio alvo.
- **HYPOTHESIS**: falta ao `skull_front_y` uma massa frontal com arco supraorbitário. Uma única massa procedimental, ancorada em marcos (glabela, rebordo supraorbitário e zigoma), deve deslocar em simultâneo e na direção das refs:
  - S5 e S7;
  - o desnível sobrancelha − córnea;
  - brow_over_eye;
  - nasion − olho;
  - S3.
  
  E não deve tocar no resto do corpo.
- **Critérios a congelar ANTES** (na pré-registação):
  - magnitudes previstas, descontando a atenuação da subdivisão;
  - regiões invariantes: bit-idênticas fora da cabeça;
  - S2/S3 e J1–J5 13/13 sem regressões;
  - ilhas e topologia inalteradas.
- **Alternativa A0: comprimento/occipital.** É mais simples, mas explica menos métricas.

### 7.2 Decisão estrutural que o utilizador tem de tomar (não resolvida aqui)

P5 e o bloqueio S4 §10 indicam que **B, C e D vão precisar do anel de rebordo como curva nova**. Isso é uma mudança estrutural à malha facial, e a regra atual é "nenhuma mudança estrutural por agora".

HEAD-A1 **não** precisa disso: é uma deformação de massas no campo existente. Recomenda-se, por isso, decidir a questão estrutural **quando se chegar a B**, com a evidência de A1 já medida. Fica registado como **dívida**, não como refactor.

---

## 8. Limitações (UNKNOWN / riscos do instrumento)

- As refs são 5 malhas de artista/estatísticas (n pequeno), com poses e estilos diferentes. Os intervalos são **de referência, não populacionais**.
- A normalização por H (vértex–mentón) propaga para tudo qualquer erro do mentón. O mentón foi validado visualmente em todas as fontes.
- O whitewalker é criatura, e alguns intervalos (TR1, S10, S11) são alargados por ele.
- As métricas de concavidade (largura alar, boca) são proxies. A largura da boca é frágil.
- O makehuman tem órbitas escavadas sem globo (recessos de ~41 mm), o que o torna outlier no CV_orbit.
- A relação globo–rebordo só pôde ser medida na nossa malha; nas refs o globo não foi exportado.
- As figuras numpy têm salpicos residuais do instrumento. O controlo Cycles confirma a geometria.
- **Não medido**: a espessura real dos "tecidos" na nossa malha (não há osso) e a deformação (não há rig facial).
