# CHECKPOINT TORSO B — reconstrução estrutural do tórax (decisão C, TORSO_DECISION_01)

**Data:** 2026-09-29 · **Ciclo:** T-TORSO, fase B (após gate do dono: "implementar C
AGORA") · **Branch:** `arena/01a0d51d-proceduralhumangenerator`
**Estado do gate visual: PENDENTE (dono).** Este documento mede; não julga o visual.

## 0. NOTA DE RECONSTRUÇÃO (sandbox perdido)

A implementação B original (7 its de calibração, commit feito mas NUNCA pushed — o
token GitHub tinha expirado) perdeu-se na 8.ª recriação do sandbox. Foi
**re-implementada a partir dos parâmetros registados** na sessão e verificada:

- baseline T1: GEN digests `dd0a715deed6dfc3`/`917f86c385dcdbc2` = os históricos
  registados (byte-a-byte) → método e ambiente validados;
- reconstrução B: **contagens (6483/6389/2400), semântica (skin 3601/3577,
  palm 62/86) e fingerprint IDÊNTICOS** ao original; **10/11 métricas P ao dígito**
  (P1–P10 todas exactas; P11 198 vs 202, ambos na banda 198–232);
- diferenças residuais (≤4 mm, zona anca/nádega): P11 −4, hip n 2.5 vs 2.8,
  bs@920 −125 vs −127, waist front_share 1.19 vs 1.17 — sub-quantização do
  instrumento (2 mm), dentro da banda em todos os casos;
- digests portanto NOVOS: instrumento ours `25cafb179b04ed34` / ours0
  `cdc1996498342cdd`; build default pure `8b74b578adb1755b` / mathutils
  `ad377832122c78c3` (pins actualizados deliberadamente).

O dono nunca viu o original (gate pendente) — esta reconstrução É o TORSO B.

## 1. O que foi implementado (MEASURED; params no código)

**Causa-raiz encontrada antes de mexer** (confirma P4/P5 do estudo): os landmarks
`bust`/`nipple` em `anatomy.py` herdavam `+ h*0.5` dos landmarks faciais → os bumps
da mama centravam-se a ~1400 mm (base do pescoço). A "mama" visível no T1 era a
inflação `fs` da estação (o barril), não um volume mamário. P4/P5 eram consequência.

**Mudanças (método estrutura→volumes→transições):**

| ficheiro | mudança |
|---|---|
| `core/anatomy.py` | níveis nipple 0.742 / bust 0.730 (era 0.768/0.758); landmarks bust/nipple reescritos (âncora ±0.058·S, y=wall+0.012·S com wall=chest_half()·0.38, z=nível real); estações: deltoid_line (chest·0.62, sup 2.5, fs .85, bs .88), jugulum (w chest·0.880, d chest·0.315, sup 3.2, fs .70, bs .98), **NOVA estação de cifose T7–T8** em zf("bust")+0.034·s (w chest·0.870, d chest·0.740, sup 3.4, fs .62, bs 1.00), bust (w chest·0.860, d chest·0.670, sup 3.6, fs .68, bs 0.78, y +0.004·s), inframammary (0.845/0.550, sup 3.2, fs .82), waist wf=0.905 + depth_for(0.709, waist·wf, 1.12, 0.92), navel mix(waist·wf, hip, 0.35), hip_flare hip·0.93 depth 0.52 bs .98, hip depth_for(0.52) bs .98 |
| `generators/body.py` | mama = **bump localizado** (amp bust_protrusion·1.20, σ=(0.048, 0.040, 0.055)·s, dir (0,1,−0.18), centro lm[bust]+(0, 0.008s, −0.010s)) sobre a parede torácica; glúteos = lóbulos laterais (±0.60·hip_half, −0.100·s, 0.512·s; amp 0.013·s·(0.7+fat), σ=(0.055, 0.050, 0.075)·s); esterno y=chest_half·0.45+0.008s; grelha abdómen waist_half·0.72; σ assimetria |
| `generators/back_curve.py` | `_alta()` — janela ALTA **OFF por omissão durante B** (HCG_T1_ALTA=1 reactiva; decisão C: T1-andaime); `_LOMBAR` amp 0.0240→0.0215; `_amp()`/`_ZONES` intactos |
| `tests/pins.py` | pins actualizados **de propósito**: 6483/6389 (+1 estação = +16/+16), digests da reconstrução, skin 3601(pure)/3577(math); ver §0 e §5 |
| `tools/refstudy/torso_cmp_b.py` | NOVO comparador P1–P12 (bandas de TORSO_STUDY_02; baseline T1 medido a sério) |
| `tools/refstudy/torso_system.py` | **fix de instrumento**: painel glúteo estava VAZIO desde b0eda34 (`"contour" in g` vs chave real `contour_x`); números da tabela D sempre estiveram certos, o PNG é que não plottava nada |

Verts/faces: **6483/6389** (era 6467/6373). Digests: instrumento (faceB2+N1+T1amp):
ours `25cafb179b04ed34` / ours0 `cdc1996498342cdd`. Build default (sem env):
pure `8b74b578adb1755b` / mathutils `ad377832122c78c3`.

## 2. Calibração do original (7 its — trajectória registada para não repetir)

| it | mudança | P10 | resultado |
|---|---|---|---|
| 1–2 | estações boxy + níveis + mama bump | 276 | P3 alto (1355) |
| 3 | jugulum 0.440/bust 0.670 | 236 | P2 +18 invertido (o ápice torácico é MAIS posterior que a nádega), P3 baixo |
| 4 | jugulum 0.315 + estação cifose + glúteo 0.020→0.013 | 250 | 10✓/11 (só P10) |
| 5 | cifose bs .88 + glúteo .017 + mama 1.14 | 246 | REGRESSÃO P2/P1 (8✓) — glúteo ↑ quebrou P2 |
| 6 | **revert it4 + bust bs 0.90→0.78** | **242** | **10✓/11 — CONFIG FINAL** |
| 7 | bust fs .62 + mama 1.32 | 244 | pior (P4 no limite 1190); revertido |

**Lições estruturais:** a linha do P10 (z≈1255) é dominada pelas costas da estação
**bust**, não pela cifose; interpolação linear entre estações NÃO cria máximos
interiores — o ápice posterior (P3) precisa da sua própria estação (cifose T7–T8);
a mama tem de ser volume localizado sobre parede boxy/costas-dominante; cintura por
razão (wf≈0.905) mantém P7 sem magrear absolutos ANSUR; bs@1241 abaixo de ~0.78
criaria concavidade nas costas (verificado monótono em 1200→1260).

## 3. Resultado vs bandas das refs (instrumento comum; refs re-medidas)

Bandas = TORSO_STUDY_02. Baseline "antes" = T1 **medido** (não copiado): GEN T1
reproduz os digests históricos; perfis guardados em `prof_ours_prev.json`.
Refs re-medidas reproduzem as bandas do estudo (femalebase/femalechar/real005
exactas; ff11 outlier low-poly conhecido; bodytopo P1 acima da banda, outlier
declarado).

| padrão | T1 (antes, medido) | TORSO B | banda refs | classificação |
|---|---|---|---|---|
| P1 lombar | 45.3 | **54.4** | 53.7–69.7 | ✓ MELHORIA |
| P2 nádega−torácica | −6.0 | **−8.0** | −20…−8 | ✓ MELHORIA (limite) |
| P3 ápice torácico z | 1265 | **1310** | 1280–1335 | ✓ MELHORIA (estação própria) |
| P4 mama z | 1305 | **1230** | 1190–1260 | ✓ MELHORIA (bug h·0.5) |
| P5 saliência mama | 26 | **64** | 54–70 | ✓ MELHORIA |
| P7 cintura/anca | 0.70 | **0.63** | 0.63–0.66 | ✓ MELHORIA |
| P8 peito/anca (guarda) | 0.94 | **0.80** | 0.78–0.96 | ✓ MELHORIA |
| P9 largura peito | 356 | **312** | 252–316 | ✓ MELHORIA |
| P10 prof peito | 310 | **242** | 218–236 | ✗ **APROXIMAÇÃO** (+2.5%; P2/P10/P11 acoplados — parar) |
| P11 prof nádega | 250 | **198** | 198–232 | ✓ MELHORIA (limite) |
| P12 níveis (guarda) | 0.64/0.50 | **0.64/0.50** | 0.61–0.70/0.46–0.58 | ✓ inalterada |
| P13 secção peito n | 2.2 | **3.8** | 3.2–4.5 | ✓ MELHORIA (boxy) |
| P14 front_share peito | 1.06 | **1.10** | 0.60–0.72 (realistas) | ✗ SEM MUDANÇA (balanço sagital→H-T2) |
| P15 share cintura | 1.15 | **1.19** | 1.06–1.52 | ✓ (mantida) |
| P16 sulco glúteo | 4.4 | **0.2** | 7–26 | ✗ **REGRESSÃO** (amp lóbulos ↓ por P11/P2; declarada, fila T2/T4) |
| P17 mppled (n=1) | — | não medido | — | UNKNOWN (frame próprio) |
| P18 anca (guarda) | 392 | **392** | refs 324–336 / ANSUR 328–413 | ✓ por decisão (razões refs, absolutos ANSUR) |

**Síntese: 12 padrões na banda (era ~2 no início do ciclo T-TORSO).**

Outras medições: bs@920 −125 (banda [−139,−83] ✓); bs@1060 −115 ✓; bs@1220
−125 ✓; bs@1380 −111 ✓; buttock_z 875 ✓ [845,960]; κ_extrema 31 ✓ [27,50];
waist n 2.5 ✓; hip n 2.5 ✓ [2.2–3.2]; hip front_share 0.97 ✓ [0.86–1.35].

**IoU de silhueta do tronco (render como instrumento, 4 vistas):**
- perfil: ours vs refs **0.667–0.787** (3/4 acima do baseline ref↔ref 0.689)
- frente: ours vs refs 0.639–0.679 vs baseline ref↔ref 0.938 (gap = anca 392 vs
  refs 324–336, decisão ANSUR P18, + ombros/braços)

## 4. Classificação obrigatória (OPERATING_MODE)

| região/sistema | veredicto |
|---|---|
| Tórax estrutural global (P1,P2,P3,P4,P5,P7,P8,P9,P11,P13) | **MELHORIA** (na banda das refs; sem destruir guardas P8/P12/P18) |
| Peito profundidade (P10) | **APROXIMAÇÃO** — 242 vs ≤236; não conclusão |
| Balanço sagital do peito (P14) | **SEM MUDANÇA** — 1.10 vs refs 0.60–0.72; hipótese H-T2 intacta |
| Sulco glúteo (P16) | **REGRESSÃO** — 0.2 vs T1 4.4 (refs 7–26); causa: amp lóbulos ↓ para P11/P2; não escondida, fila T2/T4 |
| Sacro (bs@1060) | −115 ✓ banda [−93,−25] (melhorou vs T1 −121) |
| Falsa melhoria? | NÃO encontrada: nenhuma banda alargada; guardas P8/P12/P18 verificados; P16 reportada como regressão |

**Gate visual (dono): PENDENTE.** Entregues: `renders_T1_vs_refs.png`
(4 vistas: frente/3-4/perfil/costas, mesma câmara/luz, ours vs 4 refs),
painéis `torso_system_{sagittal,coronal,gluteal,curvature}.png` (glúteo agora
renderiza de facto — fix §1), site preview. O agente não avalia o visual.

## 5. Guardas técnicas

- pytest: **136 passed** (1 skip blender-only, 1 xfail) com pins actualizados
  deliberadamente (fim de B): 6483/6389; skin 3601 pure / 3577 math;
  **knife-edge `palm` reaberto em float32** (62 pure / 86 math) — mesmo fenómeno
  da S3.6, registado, não promovido.
- Determinismo: GEN T1 reproduz digests históricos byte-a-byte; reconstrução B
  reproduzida 2× idêntica.
- Contabilidade de perda: o commit B original perdeu-se (nunca pushed); a lição
  operacional — push IMEDIATO após commit — foi reforçada (commit+push no mesmo
  passo, OPERATING_MODE).

## 6. Fila (após gate visual do dono)

1. **Feedback do dono** sobre renders/painéis/site → se visual ✓, checkpoint B
   fecha e T1-ALTA decide-se por medição (HCG_T1_ALTA default);
2. **T2 cintura/balanço sagital**: P14 (frente/trás do peito), P16 (sulco +
   lóbulos: amp 0.020 vs 0.013 com P11/P2 re-calibrados), sacro;
3. **T4 volumes** (mama alvo real005, glúteos), **T5 pescoço-base/CONT2**;
4. Depois do torso: lapidação fina das regiões individuais (cabeça, mãos, pés…)
   — directriz TORSO-PRIMEIRO do dono.

## 7. Proveniência

Bandas: TORSO_STUDY_02 (n/quais por padrão no doc). Refs re-medidas hoje
(femalebase {}, femalechar/bodytopo/real005/ff11/animeF flip_y, lucia coronal;
bodytopo cfg stature re-derivada = valores históricos ao dígito). Instrumento:
measure.py/torso_cmp_b.py/torso_system.py/render_torso.py — **o mesmo referencial**
(nenhuma métrica re-definida para parecer melhor; único fix = painel glúteo que
não plottava). ANSUR II female (Gordon et al. 2014) para absolutos.
