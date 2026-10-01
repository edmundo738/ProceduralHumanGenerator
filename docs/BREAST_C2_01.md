# BREAST_C2_01 — protótipo C2 da mama (HCG_BREAST2)

> Ciclo T-TORSO-2 · MANDATO RND (docs/MANDATE.md) · modo A dominante.
> Antecedentes: SWEEP 01 GATE NEGATIVO (docs/SWEEP_01_BREAST.md) +
> MECHANISM_AUDIT_01 (docs/MECHANISM_AUDIT_01.md).
> Estado: **PROTÓTIPO atrás de flag HCG_BREAST2=1** (default com fs/bs
> H-TT2-parcial = ee588326c69b1f8d, verificável). Sem promoção — gate visual
> do dono pendente (painel docs/head_phaseA/breast_c2_{zoom,torso}.png).

---

## 1. Descoberta maior: o CAGE não tinha vértices na mama [MEASURED]

**O tronco é construído com anéis de 16 pontos.** Os pontos frontais de cada
anel caem em x ≈ 0 / ±84 / ±137 (superelipse amostrada a 22.5°): **entre o
esterno e o flanco passa UMA aresta por anel** — a região da mama
(x 30–75 mm) não tem NENHUM vértice de controlo.

Consequência medida (in-process, cage 16 pts, janela x 40–90, z 1210–1280):

- **4 vértices** no total; mais próximos da mama: (±83, 65) e (±90, 74).
- Qualquer campo por vértice (gaussiano H-TT1 OU estruturado C2) degrada na
  **crista suave dessa aresta** — é o mecanismo exacto do diagnóstico do
  dono **"mama = linha-não-volume"** (SWEEP 01: saliência 42–58 mm que
  "aparece" mas não forma volume; base medida 10–12 mm vs refs 58–90).
- O mesmo vale para o peito superior recuado: a recessão realizava −4 mm dos
  −32 mm pedidos (f@1350 = 36 vs refs 22–27).

**Isto explica o SWEEP 01**: variar parâmetros de um campo que não tem onde
se expressar produz variantes indistinguíveis — o vocabulário não era o
problema (só), a RESOLUÇÃO DO CAGE era.

### Correcção: `_densify_front` (pontos COLINEARES)

- `ring_n=32` puro foi medido e **REJEITADO**: a frente do 16-gon (plana,
  herdada do subsurf dos pontos em x≈0/±84) está MAIS PERTO das refs do que
  a superelipse real (o 32-gon segue a superelipse → parede +16 mm →
  afastamento das refs; a "frente plana" estava acidentalmente certa).
- Solução: inserir pontos 1/4, 1/2, 3/4 **nas 2 arestas adjacentes ao ponto
  frontal (x≈0)** de cada anel. Pontos colineares não alteram a parede
  (Catmull-Clark de pontos colineares mantém a recta) mas dão ao campo
  controlo em **x ≈ 21/42/63** — exactamente a rampa medial/planalto da mama.
- Contagem uniforme em todos os anéis (n+6; sem roll — ver spline_rings);
  só activo com HCG_BREAST2=1.

## 2. Instrumento: plane_scan v3.2 [MEASURED — 3 bugs corrigidos]

Durante a verificação do protótipo, o instrumento de medição revelou-se
bugado de três formas (todas reproduzidas e corrigidas — lição permanente:
**cada número novo exige validação do instrumento contra segmentos crus**):

1. **v2 fill encadeava segmentos em polígonos** e, quando o encadeamento
   falhava (a pele da prega inframamária DESCE antes de subir à mama),
   fechava o polígono errado → **topo fantasma +24 mm** em z 1150–1220 do
   sagital (segmentos crus: 63.7@1170, 92.6@1245). O "polo inferior
   demasiado cheio" era artefacto, não geometria.
2. **Plano de corte em coordenada EXACTA de vértice** → intersecções
   degeneradas → segmentos perdidos ao longo de toda a coluna (swB2 tem
   vértices inseridos em x=±63.0 exactos; o sagital x=63 perdia a frente).
   Correcção: corte com offset sub-bin (z0 + 0.37·RES).
3. **Malhas de refs fragmentadas** (real005: 69 comps; buracos de scan) →
   colunas só-costas davam "frente" = −18 mm entre valores 72 e 90.
   Correcção: reparo por contexto (mediana rolante ±8 col; queda > 40 mm →
   NaN; buracos ≤ 25 mm tapados; curva cortada onde a frente termina).

v3.2 = **binning directo** (máx y por coluna, amostrando cada segmento ao
passo RES=2 mm) + offset + reparo. As curvas vêm agora consistentes com os
segmentos crus em todas as malhas testadas.

## 3. Especificação da mama v3 (breast_spec_v3.json) [MEASURED]

Instrumento v3.2; frame normalizado 1700 mm, y centrado min/max do corpo.

| modelo | ápice (x,y,z) | barriga−peito | esterno | gap | planalto | base | prega | f@1350 |
|---|---|---|---|---|---|---|---|---|
| real005 | (71, 91, 1252) | +2.8 | 62 | 28 | 59–85 | 80 | 41 | 22 |
| femalebase | (71, 79, 1266) | +8.9 | 58 | 21 | 55–83 | 72 | 30 | 25 |
| femalechar | (69, 97, 1214) | +6.6 | 89 | 7 | 43–87 | 58 | 21 | 27 |
| animeF | (71, 199, 1250) | −7.1 | 165 | 34 | 53–91 | 90 | 79 | 133 |
| **banda refs** | x 69–71 · y 79–97 · z 1214–1266 | −7..+9 | 58–89 | 7–34 | 43–91 | 58–90 | 21–79 | 22–27 |
| swN0 (parede) | (21, 77, 1260) | −6.7 | 77 | −0.2 | 1–69 | 12 | 9 | 37 |
| swV0 (H-TT1) | (21, 121, 1249) | −37.2 | 121 | −0.0 | 1–73 | 10 | 36 | 50 |
| **swB2 (C2)** | **(69, 95, 1261)** | **−6.7** | **79** | **17** | **53–75** | **54** | **38** | **24** |

Leituras:

- **B2 em banda em todas as métricas** excepto base (54 vs 58–90; bordo
  lateral da meia-altura ligeiramente estreito — próximo passo).
- A mudança estrutural V0→B2 é demonstrável geometricamente, não por
  parâmetros: **gap 0→17** (sulco medial existe), **base 10→54** (volume),
  **esterno 121→79** (a laje medial desapareceu), **f@1350 50→24**
  (peito superior recuado à banda), **ápice x 21→69** (lateral, como TODAS
  as refs: 69–71).
- swV0 confirma o diagnóstico do SWEEP 01 com o instrumento corrigido:
  saliência 44 mm mas gap 0 e base 10 — uma crista, não uma mama.

### Sagital do lobo (x=63) — B2 rastreia real005 [MEASURED]

z 1160→1380 (mm): **real005** 63, 63, 60, 72, 84, 89, 89, 82, 66, 45, 25, 8,
−8 · **swB2** 63, 64, 65, 69, 76, 86, 95, 90, 77, 59, 33, 20, 31 ·
**swN0** 62, 64, 65, 65, 66, 70, 75, 74, 70, 63, 46, 28, 41.
Teardrop completo (subida longa 1215→1260, prega com mergulho, descida
−62 mm em 100 mm); barriga plana como as refs (63–65 vs 55–63).

## 4. Campo estruturado `_structured_breast` (body.py)

Propriedades por termo (composição, deslocamento +y só na frente):

1. **Perfil vertical teardrop** no z: subida suave L_up=0.038·s, ápice
   z=0.732·s, polo inferior curto L_dn=0.034·s com prega (mergulho dip=0.16)
   e saída curta.
2. **Termo lateral em |x| absoluto**: sulco medial até x_m0=0.018·s (31 mm),
   rampa 31→51, planalto até 71, blend lateral até 119.
3. **Recessão do peito superior** (rec_max=0.019·s, planalto z≈1330–1370,
   atenuada acima pelo peso frontal w — o peito raso (y 30–45) recebe w
   0.4–0.6, que É a atenuação pretendida).
4. Peso frontal w = smoothstep(y/0.046·s): 0 atrás/laterais.

Amplitude amp=0.0125·s (saliência ~21 mm; ápice y 95 = topo da banda, onde
estão real005 91 / femalechar 97).

## 5. Verificação de integridade [MEASURED]

- **Atenção — o default JÁ NÃO é o H-TT1 histórico**: a correcção
  H-TT2-parcial (waist/navel fs/bs, core/anatomy.py) NÃO é gated e altera
  todos os builds. Digests: default actual (fs/bs, sem flags) =
  **ee588326c69b1f8d**; H-TT1 pré-fs/bs histórico = 70437b0bcc3a90f5.
  O protótipo C2 em SI (HCG_BREAST2) não toca o caminho default: sem a
  flag, `_densify_front`/`_structured_breast` não executam.
- **Reprodutibilidade após 15.ª recriação do sandbox**: trabalho perdido
  re-aplicado do zero; digests reproduzem EXACTAMENTE — N0 0437cc4ce71c49b2,
  B2 2ea834f946c214ad (cage 22 pts/anel + campo; 142400 verts no eval),
  V0-rebuild 9ed92eee38c0ee3d, e a tabela §3 linha-a-linha.
- swV0 foi RECONSTRUÍDO sobre a anatomia actual (o do sweep era pré-fs/bs,
  digest 8c6f568c — não comparável coluna-a-coluna): novo digest
  **9ed92eee38c0ee3d**. H-TT2-parcial incluído em N0/V0/B2: barriga−peito
  −6.7 (parede) — banda −7..+9 ✓ (V0 sem correção: −37).
- O campo é simétrico por construção (termo em |x|); inserts colineares
  simétricos (2 arestas adjacentes ao ponto frontal).

## 6. Pendente / próximos passos

1. **Gate visual do dono** (modo A): painel breast_c2_zoom.png +
   breast_c2_torso.png (refs × N0 × V0 × B2; grelha A–H × 1–8).
2. Base 54→58+: alargar o planalto/blend lateral (x_p1 0.042→~0.046·s) —
   1 iteração, re-medir tudo.
3. Esterno 79 vs real005/femalebase 62/58: a COLUNA do peito (parede) é
   anterior às refs no frame centrado — propriedade das estações/profundidade
   do tronco (F/B), NÃO da mama; tratar no ciclo de estações com as mesmas
   curvas (a diferença de profundidade de fatia entre nós e refs é ≈ const
   ao longo de z 1200–1350, com a nossa ~16 mm mais rasa em 1350).
4. Se o dono aprovar a direcção: re-medir pins/guardrails P1–P12 (o
   H-TT2-parcial muda a silhueta frontal) antes de qualquer promoção.
5. Trapézio/ombro a z≥1380 permanece o problema auditado ("ombro=aba") —
   fora do âmbito deste protótipo.

## 7. Proveniência

- Malhas: out/refstudy/raw_{real005,femalebase,femalechar,animeF,swN0,swV0,swB2}.npz
  (gitignored; regeneráveis: torso_refs.py + build_b2.py).
- Especificação: out/refstudy/breast_spec_v3.json (v3.2;
  **NÃO reutilizar breast_geometry.json v1 nem breast_spec_clean.json v2** —
  instrumentos bugados, ver §2; breast_geometry.py mantido por proveniência).
- Instrumentos: tools/refstudy/plane_scan.py (v3.2), breast_spec.py,
  render_c2.py, build_b2.py; gerador: human_generator/generators/body.py
  (`_densify_front`, `_structured_breast`, gates HCG_BREAST/HCG_BREAST2);
  core/anatomy.py (fs/bs waist/navel H-TT2-parcial).
- Refs n=4 (n=1 por estilo ⇒ OBSERVED por modelo; bandas = min–max).
- Sandbox (15.ª recriação): apt bloqueado → libs X/GL satisfeitas com stubs
  em /usr/lib/x86_64-linux-gnu/stubs (LD_LIBRARY_PATH no headless_blender;
  Cycles CPU não usa GL real; 519 símbolos stubados).
