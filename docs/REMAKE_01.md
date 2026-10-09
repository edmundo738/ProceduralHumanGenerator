# REMAKE_01 — decisão: opção 3 (reformulação do CORPO do zero)

> Decisão do dono (2026-10-02): 3 opções (encerrar / reutilizar para outra
> coisa / REMAKE do zero), escolha delegada ao agente com a condição
> "escolhe se sentires que terá diferença e alguma razão".
> **Escolha: 3 — REMAKE** — com a razão medida em §2.

## 1. Veredicto que motiva o remake [OBSERVED, dono]

- "A MAMA CONTINUA UMA LINHA" (após protótipo C2 com cage densificado e
  secções em banda — o campo por vértice não produz volume LEGÍVEL).
- "NADA ESTÁ BOM OU PERTO. NADA NO CORPO ALÉM DA CABEÇA E POR CONSEQUÊNCIA
  O PESCOÇO MAS NADA REALISTA."
- Gates visuais do corpo: 0 aprovados em 4 tentativas (TORSO B, T1, SWEEP 01,
  BREAST C2). As métricas caem "em banda" enquanto o olho diz "mecânico" —
  a representação é o gargalo, não os parâmetros.

## 2. A razão (spike medido, 2026-10-02) [MEASURED]

Pergunta: uma mama construída como VOLUME (união booleana de lóbulo
elipsoidal teardrop com a parede torácica das MESMAS estações) produz
estrutura de sombreado frontal que o campo por vértice não produz?

**Contraste local de sombreado (std L) na caixa da mama (x ±110 mm,
z 1140–1330, frontal 660 mm, grelha 1 mm):**

| modelo | contraste local |
|---|---|
| real005 (ref) | 0.040 |
| femalebase (ref) | 0.043 |
| N0 (parede nua) | 0.019 |
| B2 (campo estruturado actual) | 0.029 |
| **SDF volume (spike)** | **0.208** |

- B2 = 0.029: abaixo da banda das refs (0.040–0.043) — **o olho do dono
  estava certo**: o campo não gera estrutura de leitura suficiente.
- ΔL1 na caixa: B2 vs real005 = 0.017 > baseline ref↔ref 0.011 (B2 está
  mais longe de uma ref do que uma ref da outra).
- SDF = 0.208 (5× refs): DEMASIADO contraste (crease booleano duro + luz
  pontual, sem suavização de luz de área) — mas demonstra a ORDEM DE
  GRANDEZA: **volume ⇒ estrutura de sombreado que o olho lê**. A
  calibração (smooth-union, luz, teardrop) é trabalho futuro; a diferença
  de REPRESENTAÇÃO é a razão do remake.
- Geometria do spike em banda refs: esterno 76, ápice (63–85, 99, ~1255),
  gap 23 (refs 7–34), prega −4 mm @z1180.

Imagem: docs/head_phaseA/sdf_spike_front.png (real005 / femalebase / B2 /
SDF, mesma caixa). Instrumento: tools/refstudy/sdf_spike.py (numpy puro).

## 3. Âmbito

**MORRE (novo do zero):** o corpo construído por estações-analíticas +
anéis superelipse 16-pt + campos por vértice + subsurf, como caminho para
realismo. Fica no repo como baseline de comparação e fonte de proporções.

**MANTÉM (não se deita nada aprendido):**
- cabeça + pescoço validados (F2/N1) e o pipeline de integração/export/site;
- instrumentos: plane_scan v3.2, measure.py, métricas de imagem (ΔL1,
  contraste local, IoU) — agora métricas de PRIMEIRA CLASSE;
- biblioteca de refs + especificações medidas (breast_spec_v3; a extrair
  para as outras massas);
- MANDATE.md, OPERATING_MODE.md, modos A/B/D, histórico git/docs completo.

## 4. Arquitectura nova [HYPOTHESIS — a validar por micro-gates]

Corpo = **união suave de volumes anatómicos implícitos (SDF)**: caixa
torácica, abdómen/coluna, lóbulos mamários teardrop (com prega por
intersecção), massa glútea com sulco, cintura escapular/deltoides, coxas —
combinados por smooth-min (k calibrado) e amostrados numa malha contínua.
Parâmetros de RELAÇÕES entre volumes (a hipótese original do dono, agora
como representação e não como remendo). Cabeça/pescoço fundem-se como hoje.

## 5. FORMAS DE NÃO VOLTAR A ERRAR (protocolo anti-erro)

1. **Micro-gate por massa**: cada volume novo passa por um painel mínimo
   (ref vs novo, zoom à região) ANTES de integrar — nunca mais "reveal"
   grande. Gate barato, cedo, frequente.
2. **Sombreado como métrica de gate**: ΔL1 local + contraste local vs refs
   (o que o olho lê) — secções continuam, mas NUNCA mais sozinhas
   (lição B2: secções em banda + frontal invisível).
3. **Cada massa nasce de spec medida** das refs (plane_scan v3.2), bandas
   n≥3 quando possível; n=1 é OBSERVED.
4. **Controlo negativo sempre** (sem a massa) — a diferença tem de aparecer
   no RENDER, não só nas secções.
5. **Massa → proporção → transição → integração** (directriz TORSO B
   mantém-se; sem polir detalhes antes das massas).
6. **Default congelado**: o remake vive em módulo novo (body2) atrás de
   flag HCG_BODY2; o corpo actual (H-TT1+fs/bs) permanece o baseline
   comparativo até o remake GANHAR o gate.
7. **Proveniência sempre**: digests, instrumento+versão, resultados
   positivos E negativos, commit+push no mesmo passo.

## 6. Estágios (cada um termina em gate do dono)

- **E0 spike** ✓ FEITO (§2 — a razão).
- **E1 tórax+mama frontal**: volumes torácicos + mamas; gate: painel frontal
  zoom vs refs (contraste local na banda, ΔL1 < baseline ref↔ref).
- **E2 perfil/costas**: curvas S, zigzag costas, omoplata.
- **E3 glúteo + ombro**: lóbulos com sulco; cintura escapular (mata o
  "ombro=aba" e o "glúteo=boca").
- **E4 integração**: corpo inteiro, transições, membros; comparação com o
  baseline actual em TODAS as métricas + visual.
- **E5 variação**: parâmetros de relações → corpos diferentes ao clicar
  (objectivo final do mandato).

## 7. Risco (modo D, honesto)

O spike demonstra a razão de ordem de grandeza, não o sucesso final. A
calibração de smooth-union/luz/prega pode ainda falhar o gate — os
micro-gates baratos dizem-no em horas, não em semanas. Sem promessa de
prazo; promessa de medição honesta a cada passo.

## 8. E1 EXECUTADO (2026-10-02) — tórax + mama volumétricos [MEASURED]

Implementação (tools/refstudy/e1_body.py): corpo = FUNÇÃO DE DISTÂNCIA —
parede torácica = loft polar SUAVE (PCHIP) das mesmas 16 estações (resolução
infinita, sem anéis, sem subsurf) ∪ 2 lóbulos mamários teardrop (elipsoide
rz superior 78 / inferior 62 mm, tilt −20°, yaw 5°, smin k=28 mm) − fossa
clavicular (elipsoide subtractivo, smax k=30). Malha: marching cubes 1.5 mm
(412k verts). Controlo E1N: sem lóbulos (raw_e1n.npz).

**Especificação (instrumento plane_scan v3.2, frame mm@1700) — 7/7 em banda
(1.ª vez; o B2 tinha base 54 fora):**

| métrica | E1 | banda refs |
|---|---|---|
| ápice (x,y,z) | (69, 94, 1250) | x 69–71 · y 79–97 · z 1214–1266 |
| esterno | 72.6 | 58–89 |
| gap | 21.8 | 7–34 |
| prega (prominência) | 36.2 | 21–79 |
| f@1350 | 27.7 | 22–27 |
| barriga−peito | −1.2 | −7..+9 |

**Imagem (rig numpy — MESMO rig em todos; ver caveat):**
contraste local caixa da mama: refs 0.099–0.104 · parede E1N 0.075 ·
**E1 0.087** · B2 0.100. ΔL1: **E1→real005 0.145 < baseline ref↔ref 0.169**
(1.ª vez dentro do spread; B2→real005 0.164). Controlo limpo E1 vs E1N
(só lóbulos) = 0.046 — a diferença APARECE no render. (B2 vs N0 0.119 não é
controlo limpo: inclui prato esterno + cage.)

**Caveat honesto:** o Blender 5.0.1 deste sandbox crasha em epoxy/EGL mesmo
em Cycles CPU → o rig passou a numpy (Lambert 2 luzes, mesmas constantes do
build_scene) aplicado a TODOS os tiles. Rig numpy = normais por gradiente =
MAIS duro/sensível que o Cycles dos painéis anteriores (amplifica diferenças
de declive). Os números acima são INTERNOS ao rig (comparação válida entre
si); NÃO comparar com os ΔL1 do painel Cycles. O gate é o olho do dono:
docs/head_phaseA/e1_gate.png (frontal) + e1_gate_side.png (perfil).

**Estado: micro-gate E1 pendente (dono).** Se aprovado: E2 (perfil/costas —
curva S no loft SDF + zigzag), E3 (glúteo/ombro), E4 integração, E5 variação.

## 9. GATE E1: NEGATIVO — "uma porcaria, pior que o V0" (2026-10-06, OBSERVED)

Veredicto do dono: E1 pior que V0; pescoço lê exagerado; "embrulhaste
tudo"; "pegou tudo que tava horrível nos outros e piorou"; "antes no V0
parecia que conseguias ver algo próximo; agora já não"; "está a complicar
demais". Pergunta do dono: focar noutra coisa OU refazer tudo do zero?

**Post-mortem honesto (minha autópsia, sem defesa):**
1. **Framing enganador**: o E1 é um FRAGMENTO do tronco (z 833–1632, sem
   cabeça/membros, tampas cegas nas pontas) apresentado ao lado de corpos
   completos — a "tampa" no topo lê como pescoço balão. Erro meu de painel,
   não do dono.
2. **Rig numpy** (Lambert plano + normais por gradiente) faz a superfície
   marching-cubes ler "embrulhada" — e eu sabia que era mais duro.
3. **Erro estratégico**: investi em arquitectura (SDF) sem confirmar
   visualmente com o dono um único volume à vez. Medir bem ≠ ler bem —
   pela 5.ª vez.
4. Resultado: 5 gates visuais do corpo (TORSO B, T1, SWEEP 01, B2, E1),
   0 aprovados. **Evidência forte contra "gerar geometria de corpo do
   zero" como caminho** — quer em estações+campos, quer em SDF.

**Estado: REMAKE SUSPENSO. Decisão do dono pendente** (base-mesh+morphs /
congelar em V0 + foco no produto / pausa). E2-E5 cancelados até decisão.

## 10. DECISÃO: caminho A — base mesh + morphs (dono, 2026-10-07)

Após o gate E1 negativo (§9), o dono escolheu: **deixar de gerar geometria
do zero**; a fundação anatómica = base mesh feminina da biblioteca
(REF-F-REAL-001 "Female base.obj", CC0, 18577 verts) e o programa gera
corpos DIFERENTES por morphs paramétricos medidos (bandas).  É a abordagem
MakeHuman/MetaHuman — nunca testada aqui; o risco muda de "desenhar
anatomia" para "não estragar anatomia" (morphs pequenos).

### Protótipo A.0 executado no mesmo dia [MEASURED]

- `tools/refstudy/basemesh_proto.py` (numpy puro, sem Blender): loader .obj
  → frame exacto **(x,y,z) = (x, −z_obj, y_obj)·S** (validado por diff
  directo contra a frame do pipeline das refs, erro 0.1 µm — LIÇÃO: mapa
  determinístico, heurísticas de orientação BANIDAS: uma delas escolheu as
  costas como frente) → morphs por seed (estatura uniforme 1600–1740,
  cintura ×0.93–1.05, anca ×0.98–1.07, mama ±fracção da projecção,
  glúteo, ombro, coxa, ε de assimetria) → medidas (plane_scan v3.2) →
  render rig v2 (normais de VÉRTICE interpoladas nos cortes — não
  gradientes; mata o aspecto "embrulhado" do rig v1).
- **m00 (base, sem morphs): ápice (69, 75, 1265), gap 20.5 — a base JÁ TEM
  a anatomia mamária dentro da banda refs** (7–34).  5 seeds: WHR
  0.726–0.862 (refs 0.72–0.81; m05 0.86 ligeiro excesso — afinar banda),
  cintura 226–286, anca 304–352, ápice x 67–73 ✓ z 1215–1290 ✓,
  gap 19–29 ✓.
- Painéis: docs/head_phaseA/basemesh_gen.png (6 corpos × frente) e
  basemesh_zoom.png (zoom mama frente/perfil ×3).  Rig = clay numpy v2
  (declaração honesta: ainda não é Cycles; serve para gates de forma).
- **GATE do dono pendente**: "a direcção lê como corpos reais? qual
  seed/parametro preferes?"  Se aprovado: integração no human_generator
  (preset female_basemesh + sistema de seeds = o 'gerar ao clicar').

Nota: a biblioteca references/ ESTÁ no git (falso alarme do turno — o check
correu antes da recuperação do sandbox); refs intactas, sem re-upload.

## 11. GATE A.0: **POSITIVO** — "lê como corpos reais" (2026-10-07, OBSERVED)

Primeiro gate visual POSITIVO do projecto (6 tentativas). Direcção aprovada
pelo dono, com duas directrizes: (1) as diferenças entre seeds eram
"microscópicas" → **A.1 com bandas ~3× mais largas** (estatura 1500–1810,
cintura ×0.80–1.20, mama −0.30..+0.55...; medidas: estatura 1566–1792,
cintura 194–317, WHR 0.67–0.97); (2) **guardar o aprendizado** →
`human_generator/data/corpus.json` (v1): base meshes + frame maps, canais de
morph com bandas, bandas medidas das refs, lições dos gates (positivas E
negativas), instrumentos, registry de seeds. O corpus é a fonte de verdade
do gerador (o "conhecimento" do algoritmo, versionado no git).

**Botão v0:** 4 corpos exportados como GLB para o visualizador do site
(m00 base + w02/w03/w05 largos; tools/refstudy/basemesh_glb.py — writer
glTF minimal, transform ours→glTF (x,y,z)→(−x,z,y), winding revertido;
variants registadas em data.json e models.json — sobrevivem a rebuilds).

**Pendente (perguntas ao dono):** amplitude final; cabeça (base vs
transplante F2); UX do botão (galeria vs gerador interactivo).


## 12. Render A: 2 bugs MEUS + directriz CARNE LIGADA (2026-10-09, OBSERVED)

O dono viu os corpos A no visualizador: "dá para ver dentro da boneca",
"distorção e olho de peixe ao subir a câmara", "divisões na bunda ao
esticar". Diagnóstico e correcção:

1. **Winding invertido (x-ray).** O writer GLB revertia os índices por
   engano — o mapa nosso→glTF (−x,z,y) é UMA ROTAÇÃO PRÓPRIA (det=+1), não
   espelha, logo o winding do OBJ preserva-se. Prova por volume assinado:
   m00 −0.049 m³ (errado) vs t1 (Blender) +0.068 m³. Corrigido no writer +
   GLBs regenerados: 6/6 positivos. **Validação permanente nova: volume
   assinado > 0 em todo GLB exportado.**
2. **Moldura de cabeça em corpo (olho de peixe).** O site calibrava a
   câmara para cabeças (size 0.34 m); num corpo de 1.7 m a câmara ficava a
   ~0.6 m — DENTRO do mesh. AUTO-FRAME: bbox > 1.2 m ⇒ moldura "body".
   Gerador: fov 35→30, câmara mais afastada.
3. **Directriz CARNE LIGADA** (directriz anatómica permanente, ver
   OPERATING_MODE): morphs deixam de ser ilhas — cada canal propaga às
   regiões vizinhas (amp 0.20–0.35, rampas 45→120 mm). A.2 medido:
   estatura 1566–1792, cintura 200–337, WHR 0.71–0.90, gap 6.1–31.6.
   Painéis basemesh_gen3/zoom3.
