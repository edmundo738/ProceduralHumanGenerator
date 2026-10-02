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
