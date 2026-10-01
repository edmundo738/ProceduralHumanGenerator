# CHECKPOINT TORSO TT1 — loft spline C¹ (H-TT1 de TORSO_TRANSITIONS_01)

**Data:** 2026-09-30 · **Ciclo:** T-TORSO-2, passo 1 (H-TT1) · **Branch:** `arena/01a0d51d-proceduralhumangenerator`
**Gate visual: PENDENTE (dono).** Este documento mede; não julga o visual.

## 1. O que foi implementado

**H-TT1 (fundação — continuidade C¹), conforme pré-registado no estudo:**

| mudança | ficheiro | detalhe |
|---|---|---|
| `make_pchip` + `spline_rings` | `core/topology.py` | PCHIP (Fritsch–Carlson, C¹, monótona, sem overshoot) dos CAMINHOS DOS PONTOS das estações (interpolar PARÂMETROS incha os cantos +18 mm, medido na T1 §7.2 — evitado); grelha uniforme 0.012·s + z das estações (passagem exacta); dedup <max_step/6 |
| loft do tronco | `generators/body.py` | `subdivide_rings` (linear) substituído por `spline_rings`; +25 anéis = +400 verts/faces |
| estação perineal NOVA | `core/anatomy.py` | zf(hip)−0.030·s, hip·0.76/hip·0.365 — sem ela o PCHIP (tangente nula no máximo local da anca) alargava anca→virilha +12 mm e o tronco ATRAVESSAVA as pernas (componentes fundiam até z 991; a banda `lo` do instrumento saltava 0.475→0.540) |
| recalibração de amplitudes | `body.py`, `back_curve.py`, `anatomy.py` | a malha densa REALIZA os campos por inteiro (a gaiola dispersa amortecia ~30%): mama 1.20→0.86, _LOMBAR 0.0215→0.0202, _SACRAL 0.0240→0.0222, cifose d 0.740→0.700, inframammary 0.550→0.540, wf 0.905→0.912 |

**Bugs apanhados no caminho (registados):** dedup em unidades erradas (3.0 m = 3000 mm
apagava a grelha TODA — apanhado pelo dump da gaiola: 15 anéis em vez de ~60);
anéis quase duplicados (estação 1224.0 + grelha 1224.2 = pares a 0.2 mm).

Verts/faces: **6883/6789** (TORSO B: 6483/6389). Digests: pure `70437b0bcc3a90f5`
/ math `625a96991cc38bd0`; instrumento ours `8c6f568ccfbbe530` / ours0 `fed1fac2790f7bbd`.

## 2. Guardrails P1–P12: 11/11 na banda — PRIMEIRA VEZ

| padrão | TORSO B | H-TT1 | banda |
|---|---|---|---|
| P1 lombar | 54.4 | **60.3 ✓** | 53.7–69.7 |
| P2 nádega−torácica | −8 | **−16 ✓** | −20…−8 |
| P3 ápice torácico z | 1310 | **1310 ✓** | 1280–1335 |
| P4 mama z | 1230 | **1250 ✓** | 1190–1260 |
| P5 saliência mama | 64 | **70 ✓** (limite) | 54–70 |
| P7 cintura/anca | 0.63 | **0.63 ✓** | 0.63–0.66 |
| P8 peito/anca | 0.80 | **0.79 ✓** | 0.78–0.96 |
| P9 largura peito | 312 | **308 ✓** | 252–316 |
| **P10 prof peito** | 242 ✗ | **232 ✓** | 218–236 |
| P11 prof nádega | 198 | **202 ✓** | 198–232 |
| P12 níveis | 0.64/0.50 | **0.64/0.51 ✓** | — |

O P10 nunca tinha entrado (T1: 310; TORSO B: 242 "aproximação") — a alavanca
final foi a estação de cifose (0.740→0.700: o máximo de profundidade é o ápice
posterior, z≈1305, não a linha do busto).

## 3. Transições (instrumento do estudo) — antes → depois vs refs

| região | ext refs | ext antes → depois | wiggle refs | antes → depois |
|---|---|---|---|---|
| R1 pescoço→clavícula | 0 [0-5] | 1 → 1 | 9.89 | 3.44 → **5.12** |
| R2 clavícula→ombro | 1 [0-4] | 0 → 0 | 12.23 | 0.75 → 0.93 |
| R3 tórax (caixa) | 0 [0-2] | 0 → 0 | 4.24 | 0.73 → 0.55 |
| R4 mama | 2 [1-2] | 1 → 1 | 0.48 | 0.27 → **0.38** |
| R5 mama→abdómen | 1 [1-5] | 0 → **2** | 0.19 | 0.19 → 0.27 |
| R6 cintura | 1 [0-1] | 1 → 1 | 0.56 | 0.56 → **0.49** |
| R8 costas/escápula | 1 [0-2] | 1 → 3 | 0.26 | 0.51 → 0.69 |
| R9 lombar | **1 [1-1]** | 3 → **3** | 0.21 | 0.57 → 0.63 |
| R10 sacro→glúteo→coxa | 1 [0-3] | 1 → 1 | 1.88 | 2.42 → 2.61 |

**Leitura honesta:** a fundação C¹ está posta (R1/R4/R5/R6 aproximam-se das
refs; a recessão submamária COMEÇOU a existir — R5 0→2 extremos). **Os extremos
NAS estações mantêm-se** (R9 3: navel/hip_flare + lombar; R8 3: bust-costas +
"dip" @1260 + escápula/cifose) — EXACTAMENTE como previsto no estudo: PCHIP é
monótono ENTRE nós, os extremos dos DADOS das estações permanecem até H-TT2
(re-calibrar sequências) e H-TT4 (arquitectura sagital nas estações). A mama
continua formalmente um bump sobre a parede (H-TT3) e o ombro uma rampa (H-TT5).

IoU perfil: 0.676–0.761 (baseline ref↔ref 0.689); frente 0.639–0.679 (gap =
anca ANSUR, decisão P18).

## 4. Classificação obrigatória

| item | veredicto |
|---|---|
| Continuidade C¹ do tronco (fundação) | **MELHORIA** (medida: wiggle R1/R4/R6 → refs; sem ondas ENTRE estações por construção) |
| P1–P12 guardrails | **MELHORIA** — 11/11 (P10 ✓ pela 1.ª vez) |
| Extremos nas estações (R8/R9) | **SEM MUDANÇA** — esperado; fila H-TT2/H-TT4 |
| Mama (forma/implantação) | **SEM MUDANÇA estrutural** (amplitude recalibrada; H-TT3 pendente) |
| Ombro parabólico (R2) | **SEM MUDANÇA** (H-TT5) |
| Falsa melhoria? | verificação: bandas inalteradas; refs re-medidas idênticas; `lo` do instrumento RESTAURADO para o valor do estudo (o bug era GEOMETRIA — tronco a atravessar as pernas — corrigido, não métrica ajustada) |

## 5. Guardas técnicas

136 tests ✓ (pins actualizados de propósito: 6883/6789, skin 4001/3977, palm
62/86 knife-edge mantém-se; neon_idol 6869/6775 — 2 estações suas a <3 mm fundem
no dedup). Audit: 0 non-manifold/degenerate/loose/ngon, boundary 962,
weld/dissolve 0/0. Determinismo: GEN reproduzido por recharge.

## 6. Fila (ordem do estudo, inalterada)

1. **Gate visual do dono** (renders_T1_vs_refs.png 4 vistas + painéis + site);
2. **H-TT2**: re-calibrar as SEQUÊNCIAS das estações para matar os extremos
   R8/R9 (navel/hip_flare zigzag; dip @1260) — alvo R9 3→1;
3. **H-TT3** mama (base larga, sulco inframamário, orientação; cortes laterais);
4. **H-TT4** arquitectura sagital nas estações (fim das janelas somadas);
5. **H-TT5** complexo do ombro; **H-TT6** junções anca→coxa/glúteo→coxa.

## 7. Proveniência

Mesmo instrumento/referencial (measure.py/torso_cmp_b.py/torso_transitions.py/
render_torso.py; bandas TORSO_STUDY_02; refs re-medidas no sandbox actual
reproduzem as bandas). Nenhuma métrica re-definida; único fix de instrumento
permanece o do painel glúteo (commit anterior). ANSUR II para absolutos.
