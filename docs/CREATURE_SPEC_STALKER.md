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
