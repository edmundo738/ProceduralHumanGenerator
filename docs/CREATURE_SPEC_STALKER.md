# CREATURE_SPEC_STALKER — bandas MENSURÁVEIS (v1, 2026-09-24)

Directriz do dono: "não mediu, só mentiste na cara dura; precisa de ser
consistente, não qualquer coisa aleatória". **Regra: nenhuma afirmação de
proporção sem medição numérica do OUTPUT (a geometria gerada, nunca os
parâmetros de construção).**

Fonte das bandas: conceito do dono (§1 do pedido) + proporções humanas de
referência (humano: braço/estatura ≈ 0.44; punho humano fica ~0.25 m acima
do joelho). Frame mm.

| # | Métrica | Método (do GLB) | Banda |
|---|---------|-----------------|-------|
| M1 | estatura | max z (todas as malhas) | 1750–1900 |
| M2 | punho acima do joelho | z(punho)−z(joelho); punho = fronteira antebraço/mão; joelho = fronteira coxa/canela | **−20 … +60** |
| M3 | alcance do braço/estatura | (z(ombro)−ponta dos dedos)/estatura; ombro = esfera de junção | 0.50–0.62 |
| M4 | comprimento da mão | extensão da malha hand | 120–180 |
| M5 | cabeça: comprimento/estatura | eixo principal (PCA) da malha head | 0.115–0.150 |
| M6 | cabeça: inclinação | ângulo do eixo principal vs vertical | 20–40° |
| M7 | corcunda (ombros recuados) | jut do pescoço: y(centroide último anel) − y(anel do dip), pela ordem dos vértices do loft | ≥ 45 |
| M8 | pescoço retractado | z(base do crânio, malha head) − z(anel do dip) | 60–100 |
| M9 | coxa/canela | distâncias entre PIVÔS do rig (extensões de malha inflam c/ esferas de junção) | 0.90–1.10 |
| M10 | pé: comprimento | extensão y da malha foot | 200–280 |
| M11 | ombro (largura/estatura) | extensão x do torso em z∈[1360,1440] | 0.19–0.26 |
| M12 | cintura (largura/estatura) | extensão x do torso em z∈[1100,1180] | 0.085–0.115 |
| M13 | anca/cintura | razão das larguras | 1.05–1.30 |
| M14 | olhos: interocular | centróides das malhas eye | 95–115 |
| M15 | olho: raio | bbox/2 | 18–24 |
| M16 | mandíbula: comprimento | eixo principal (PCA) | 90–140 |
| M17 | assimetria de braços | \|alcance R − alcance L\| | 5–25 (presente, controlada) |

Instrumento: `tools/creature/measure_stalker.py` (mede o GLB em
site/models/stalker2_smooth.glb; escreve out/refstudy/stalker_measure.json;
PASS/FAIL por métrica). **O gate do painel só é declarado com a tabela
inteira PASS.**

## v3 — resultado medido (2026-09-24, seed 13)

`python3 tools/creature/measure_stalker.py` → **17/17 PASS** (out/refstudy/stalker_measure.json).
Painel com a tabela medida: `python3 tools/creature/panel_stalker.py` → docs/head_phaseA/stalker2_views.png.
Regra v3: proporção só se declara com a tabela PASS; bandas = fonte única (SPEC no instrumento).
Ciclo de conformidade desta versão: 10 FAIL → 8 → 5 → 5 → 1 → 0 (cada FAIL diagnosticado
por números: troca de eixos do loft, anéis do pescoço a poluir fatias, esferas de junção
a inflar extensões, braços 127mm curtos, corcunda inexistente).

## v3.1 — spec da ANIMAÇÃO (declarada ANTES da medição)

Instrumento: `tools/creature/anim_check.mjs` (aplica o módulo puro
`tools/preview/site/stalker_pose.js` — o MESMO código do site — à
hierarquia real do GLB; 7 estados × 8s × 30fps). Saída:
`out/refstudy/stalker_anim_check.json`.

| id | o que garante | banda |
|---|---|---|
| A1 | ossos constantes (ombro−cotovelo−punho, anca−joelho−tornozelo, pescoço): desvio ≤ 2mm — apanha escala em grupos (o "estica o boneco") | ≤ 2mm |
| A2 | solas nunca abaixo do chão | ≥ −25mm |
| A3 | patinação: velocidade horizontal do pé durante contacto | ≤ 0.35·v + 0.15 m/s |
| A4 | bob vertical do root | ≤ 60mm |
| A5 | de pé (não-DORMANT): topo da cabeça | 1.50–1.86m |
| A6 | DORMANT agacha de verdade: topo da cabeça + canela dobrada | 0.90–1.45m e |rx|≥0.8 |

## v3.1 — resultado medido da animação (2026-09-24)

`node tools/creature/anim_check.mjs` → **6/6 PASS**
(out/refstudy/stalker_anim_check.json): A1 ossos 0.0mm · A2 sola mín
+10.2mm (HUNTING 21.6 = só as garras tocam, corrida) · A3 patinação
0.40 m/s (banda 1.27) · A4 bob 26mm · A5 topo de pé 1.69–1.72m ·
A6 DORMANT topo 1.355m + canela 1.68 rad. Ciclo: 1/6 → 4/6 → 5/6 → 6/6.
Refinamentos DECLARADOS (instrumento): A4 passou a medir a AMPLITUDE da
oscilação dentro do estado (o offset estático do agachado não é bob);
bug do instrumento corrigido (Float32Array de um Buffer converte bytes —
agora readFloatLE). Movimento: apoio do pé recua à velocidade exacta do
corpo (dz/dt = −v ⇒ pé parado no mundo); alvo do tornozelo sobe pela
folga da garra (HUNTING escavava −25.5mm sem folga).

## v3.2 — spec da FORMA/RELEVO (declarada ANTES da medição)

Gate do dono: "a forma/silhueta do monstro" é o pior. Diagnóstico: o
tronco é um tubo liso de elipses (zero relevo) e os membros são
salsichas de raio linear — silhueta genérica, não de terror. Horror
PSX lê por RELEVO: costelas à mostra, crista espinal, escápulas,
braços de nó vs antebraços de corda, órbitas fundas. Tudo com CARNE
LIGADA (modulação Gaussiana contínua dos anéis — nunca degraus).

Instrumento: `tools/creature/measure_form.py` (mede o GLB; perfis
radiais por anel do torso/cabeça e por linha óssea dos membros).
Saída: `out/refstudy/stalker_form.json`.

| id | relevo | banda |
|---|---|---|
| F1 | costelas: nº de máximos do perfil lateral r(z), z 1260–1445 | ≥ 5 |
| F1b | amplitude do perfil lateral (máx−mín) | 6–30mm |
| F2 | crista espinal: r_costas(z) − r_lateral(z), máximo | ≥ 10mm |
| F3 | vértebras: nº de máximos do perfil costas, z 1150–1450 | ≥ 6 |
| F4 | escápulas: min/max do raio no sector costas a z 1370–1420 | ≥ 6mm |
| F5 | contraste braço: r raiz supra / r meio antebraço | 1.45–2.1 |
| F6 | bojo do joelho: r máx canela f<0.12 / r meio canela | ≥ 1.2 |
| F6b | bojo do cotovelo: r máx antebraço f<0.1 / r meio antebraço | ≥ 1.15 |
| F8 | testa vs órbita: r frente z 1620–1660 − r frente z 1580–1615 | ≥ 4mm |

## v3.2.1 — refinamentos de método (declarados antes de re-medir)

As primeiras medições mostraram que os métodos mediam ARTEFACTOS, não
relevo (elipse/tendência ≠ gomo). Instrumento corrigido:

- **F2/F3**: medidos na LINHA DE SILHUETA COSTAS y_back(z) (média dos 5
  verts mais recuados por anel), des-tendenciada (janela ±45mm). A
  elipse (E1>E2) faz o polo costas ser o ponto +próximo — comparar
  polo/flanco media −15mm de elipse, não relevo.
- **F4**: des-tendência ANGULAR por anel (r(θ) − média móvel angular
  ±0.7rad) — a elipse produzia 15-25mm de variação angular SEM nenhuma
  escápula (F4 "passava" por artefacto).
- **F8**: recesso do GLOBO OCULAR (distância do centro do olho aos 10
  verts mais próximos da cabeça, menos raio 21mm), banda 2–12mm — a
  média do sector frontal diluía órbita/arcada (sinais opostos).
- **F1**: gomos das costelas EXACTAMENTE nas estações do loft (closure
  sobre as estações reais; bumps entre estações aliasavam a zero).

## v3.2.2 — F8 apanhou um bug REAL (olhos invisíveis)

F8 mediu +42.9mm: os globos oculares estavam ENTERRADOS 43mm dentro da
cabeça — invisíveis desde a v2 (os "olhos negros que brilham" nunca
brilharam; o emissive estava debaixo da pele). Redefinição final do F8:
**assentamento do olho** = distância média dos 10 verts mais próximos
da cabeça ao centro do olho, banda [17, 25]mm (globo r21 quase à flor
da pele — fenda negra; +43 = enterrado, −21 = a flutuar). Olhos agora
COLOCADOS NA SUPERFÍCIE (vértice real da cabeça − 19mm ao longo da
normal). Janela de des-tendência ±45→±30mm (os bumps vizinhos a 36.7mm
entravam na média e comiam os máximos: F1 contava 3 de 5).

## v3.2.3 — terceiro refinamento F8 (densidade da malha)

mean10-verts media DENSIDADE (anéis de 24 verts), não superfície: F8
por distância mínima aos TRIÂNGULOS da cabeça. E causa-raiz do relevo
fraco achada: anéis INCLINADOS (corcunda) → verts de um anel espalham
±40mm em z → gomos por z-de-vértice diluídos + vértebras apanhavam
verts laterais (espinhos de 29mm nos flancos). Relevo agora INDEXADO
À ESTAÇÃO (centro do anel) com transição Gaussiana entre anéis.

## v3.2 — resultado medido da FORMA (2026-09-24)

`python3 tools/creature/measure_form.py` → **9/9 PASS**
(out/refstudy/stalker_form.json): F1 costelas 6 gomos · F1b amplitude
14.1mm · F2 crista espinal 38.7mm · F3 vértebras 7 · F4 escápulas
20.9mm · F5 contraste braço 2.00 · F6 joelho 1.4x · F6b cotovelo 1.6x
· F8 olho assente 18.1mm. Ciclo: 6 FAIL → 2 → 0 (refinamentos de método
v3.2.1/.2/.3 declarados a cada passo; bug REAL: olhos enterrados 43mm).
Painel: 3 tabelas (geometria 17/17 + forma 9/9 + animação 6/6).
Re-medições cruzadas intactas: 17/17 e 6/6.

## v3.3 — specs da ANATOMIA APLICADA (declaradas ANTES de medir)

Pesquisa (docs/ANATOMY_RESEARCH_STALKER.md): músculo = tendão→BARRIGA
(a meio)→tendão, cruzando as articulações; fascia liga tudo (força
transmite-se); squash/stretch com volume ~preservado. Bug achado por
leitura do código: as duas pernas partilham a MESMA fase (π em falta) —
"as pernas mexem-se de forma unificada" (gate do dono).

**Forma (redefinições anatómicas — measure_form.py):**

| id | o que | banda |
|---|---|---|
| F6 | gémeo: barriga (anel f=0.35) / tendão do tornozelo (anel 1.0) | ≥ 1.4 |
| F6b | antebraço: barriga (anel f=0) / tendão do punho (anel 1.0) | ≥ 1.5 |
| F6c | joelho (anel 0 canela) / barriga da coxa (anel f=0): joelho nunca mais largo que o quadríceps | 0.50–0.95 |

**Animação (acrescento ao anim_check.mjs):**

| id | o que | banda |
|---|---|---|
| A7 | anti-fase das pernas: correlação de Pearson entre coxa_R e coxa_L ao longo do ciclo (estados móveis) | ≤ −0.75 |
| A7b | duty factor por pé (fracção do ciclo em contacto) | ≤ 0.70 |
| A7c | duplo apoio (ambos os pés no chão) | ≤ 0.30 |
| A8 | bombeio muscular: amplitude máx da barriga nos estados móveis | 0.02–0.15 |

**Textura (densidade de texel — measure_form.py, UVs do GLB):**

| id | o que | banda |
|---|---|---|
| T1 | densidade vertical do torso (512px · Δv / comprimento) | ≥ 1000 px/m |
| T2 | densidade vertical de cada membro (8 membros) | ≥ 1000 px/m |
| T3 | uniformidade torso+membros (max/min) | ≤ 2.5× |

## v3.3.1 — refinamento de medição A3/A7b (declarado)

Contacto do pé = garra a ≤5mm do solo (cravada). O limiar anterior
(30mm) apanhava frames do INÍCIO do balanço — o pé descola ainda baixo
(lift parte de 0) — e o "drift" medido era a aceleração do balanço, não
escorregamento do apoio. Com o limiar certo, A3 volta a medir o apoio.

## v3.3 — resultado medido (2026-09-24)

Anatomia aplicada (docs/ANATOMY_RESEARCH_STALKER.md): **FORMA 13/13**
(out/refstudy/stalker_form.json): F6 gémeo/tornozelo 1.9 · F6b
flexores/punho 3.0 · F6c joelho 0.6·quadríceps · T1 1017px/m · T2
1020px/m · T3 1.2x. **ANIMAÇÃO 10/10** (stalker_anim_check.json): A7
anti-fase −0.78 (bug das pernas unificadas: π em falta no módulo de
postura!) · A7b duty 0.25 · A7c duplo apoio 0.00 · A8 bombeio 0.105.
A3 drift 0.00 (contacto = garra ≤5mm; heel-strike/toe-off no alvo do
tornozelo tira o clamp do IK). Geometria 17/17 intacta.

## v3.4 — spec da SOLDADURA (declarada ANTES; gate: "ombros = vulcões")

Prova numérica do estado actual (2026-09-24): anel raiz do braço a
z=1535 (altura do pescoço), 16/16 verts FORA do torso, r=52.9mm + tampa
plana + esfera — o "vulcão/canudo". Coxa: 9/16 fora (bolas nas ancas).
Directriz do dono (curso colado): soldar as peças (bridge), tampas
escondidas DENTRO, deltoideu ENVOLVE o ombro (não bola colada), pele
passa sem interrupção.

| id | o que | banda |
|---|---|---|
| S1a | anel raiz do braço (primeira estação): verts DENTRO do torso (distância assinada) | 20/20 |
| S1b | raio do anel raiz do braço (tendão) | ≤ 34mm |
| S2a | anel raiz da coxa: verts dentro do torso | 20/20 |
| S2b | raio do anel raiz da coxa | ≤ 46mm |
| S3 | colar da base do crânio sobrepõe o pescoço (z mín da cabeça) | 1.460–1.500 |
| S4 | variação de raio entre anéis ADJACENTES dos membros (contorno suave) | ≤ 12mm |

Método: distância assinada ao mesh do torso (triângulo mais próximo,
sinal pelo normal). Anéis por ordem de vértices (topologia).
**F5 redefinido** (refinamento declarado): raio MÁX do braço na janela
f∈[−0.12, 0.45] (deltoideu, medido à linha óssea) / raio médio do
antebraço f∈[0.3, 0.6] — a raiz agora é TENDÃO enterrado (não deve
contar para o contraste).

## v3.4.1 — refinamentos de método (durante a medição, calibrados)

O método declarado (distância assinada pelo normal do triângulo mais
próximo) **mentia**: a tampa inferior do torso tem winding invertido
(normal aponta para dentro) e o corte do ombro é PINÇADO (trapézio +
tampa = dois lóbos com aperto no meio — por isso "interior" aparecia
fragmentado). Substituído por **ray-cast por paridade** (Möller–
Trumbore, contagem ímpar de atravessamentos; independente do winding).
Calibração: pontos interiores (z 1075/1100/1200/1300/1450) = DENTRO,
exteriores = fora, e 3 direcções de raio distintas concordam em todos
os pontos de teste. Os anéis passaram a ser medidos **por linha óssea**
(f = projecção nos pivôs do rig, janelas por f) em vez de índice de
estação — a densificação (mult=3) mudou a contagem de estações e o
índice já não significava nada (v3.3 media 5 estações; agora 13-16).

## v3.4 — resultado medido (2026-09-24)

**FORMA 19/19** (out/refstudy/stalker_form.json): S1a 20/20 · S1b
24.0mm · S2a 20/20 · S2b 44.8mm · S3 1479.8mm · S4 9.9mm · F5
(redef, deltoideu/antebraço) 1.9 · F6 1.8 · F6b 2.8 · F6c 0.6 · F1-F4/
F8/T1-T3 inalterados PASS. **GEO 17/17** (M8 61.4 — o colar da cabeça
não pode descer mais que ~8mm sem quebrar M8; equilíbrio calibrado).
**ANIM 10/10** (re-medido: A7 −0.78, A8 0.105, drift 0.00).

Construção: braço com estações EXPLÍCITAS — tendão r24 desce de DENTRO
da tampa do ombro (0.150,−0.045,1.435; anel ~horizontal = disco
perpendicular à descida), deltoideu r52 EMERGE por baixo da tampa,
bíceps→cotovelo r41; coxa: tendão r45 na bacia (20/20); canela/ante-
braço root_frac 0.05 (raiz dentro do membro pai); cap_start=False em
todos os tubos de membro e na base do crânio (tampas de cilindro
ABOLIDAS — o tubo solda, não encaixa); densify mult=3 com suavização
de r só nos pontos interpolados (estações originais intactas). GLB
5312v/9806t digest 36e57e105d6c3fbc. Painel 2500×1176 (3 tabelas:
17+19+10). Deploy por hash + cache-buster no GLB.

## v3.5 — spec do CONTORNO DO BRAÇO (declarada ANTES; dono: "não corrigiste nada")

O dono tem razão em parte: a massa-vulcão a z=1535 SUMIU (perfil w:
z1450 281→193, z1500 272→166 — medido), mas o braço continua a ler-se
como CANUDO: a silhueta frontal ALARGA para BAIXO — deltoideu 235 →
bíceps 250 → COTOVELO 271 (o ponto mais largo do membro!) — um cone
invertido pendurado ao lado de um tronco de 100mm na cintura. Causa
medida: pivôs do braço derivam para fora (ombro x170 → cotovelo x225 →
punho x243) e o deltoideu máx está a z1330, ABAIXO da linha do ombro
(tronco 196 em z1380-1465, mas 157 em z1330 — o tubo atravessa a zona
onde o tronco já afunila).

| id | o que | banda |
|---|---|---|
| C1 | degrau do contorno frontal: máx \|Δw\| por passo de 25mm na banda z∈[1280,1440] (largura da silhueta = união de TODAS as malhas, vista frontal ortográfica) | ≤ 12mm |
| C2 | cone invertido: largura máx na banda do cotovelo z∈[1000,1060] − largura máx na banda do deltoideu z∈[1310,1400] (o braço AFFINA para baixo; nunca o cotovelo/antebraço proximal é o ponto mais largo) | ≤ +8mm |

v3.3 media C1 ~86mm/25mm (o vulcão); v3.4 actual: C1 ~11 (passa) mas
**C2 = +39 (FALHA — o canudo)**. Construção prevista: pivôs do braço
quase verticais (cotovelo x 0.185, punho x 0.185), deltoideu máx r46
EM z1380 (na linha do ombro, onde o tronco tem 196), afinamento
monótono até r33 no cotovelo, barriga do antebraço 0.043.

## v3.5 — resultado medido (2026-09-24)

**FORMA 21/21**: C1 10.6mm (era 22.6) · C2 +1.3mm (era **+35.5** — o
cone invertido: a ESFERA do cotovelo r44.7 + barriga do antebraço eram
o ponto mais largo de todo o braço) · F5 1.6 · F6b 2.0 · S1-S4 e
restantes inalterados PASS. **GEO 17/17** (pivôs do braço movidos:
cotovelo/punho x 0.225/0.243 → 0.185 — M2/M3/M11/M17 re-medidos PASS,
todos z-based). **ANIM 10/10**.

Construção: braço quase VERTICAL sob o ombro (o deriva-fora 170→225→
243 pendurava o tubo ao lado do tronco magro); deltoideu máx r44 NA
linha do ombro (z1380, tronco 196 — emerge do volume, sem degrau);
afinamento monótono 44→38→35→31 até ao cotovelo; esfera do cotovelo
REMOVIDA ("bola colada"); raiz do antebraço r31.4 entra dentro do fim
do braço (r31). GLB 4988v/9230t digest 1dbd59ca. Painel 2500×1214.
