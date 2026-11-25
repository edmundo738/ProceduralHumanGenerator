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
