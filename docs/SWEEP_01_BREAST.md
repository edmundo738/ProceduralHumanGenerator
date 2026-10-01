# SWEEP 01 — MAMA · Modo A (busca guiada pelo dono)

**Data:** 2026-10-01 · **Ciclo:** T-TORSO-2, H-TT3 via modo A · **Branch:** `arena/01a0d51d-proceduralhumangenerator`

## 0. Mudança de modo (decisão do dono, 2026-10-01)

Após declaração honesta de limites do agente (cegueira visual = limitação raiz),
o dono decidiu: **A dominante** — o loop inverte-se. O agente gera N variantes
de UMA região com o resto do corpo constante, renderiza vistas padronizadas
com grelha etiquetada (modo B), **o dono escolhe/rankinga**, e o agente MEDE o
que distingue as escolhidas das rejeitadas — aprendendo a função perceptual do
dono em vez de a adivinhar. B (grelhas A–H × 1–8) suporta A; C (decisão de
paradigma de representação) fica informada pelos dados dos sweeps: **se nenhuma
família de parâmetros desta representação satisfizer o dono, isso é evidência
de que a representação tem de mudar** (não de que faltam pânos); D
(expectativas) registada no STATE.

## 1. Instrumento

`tools/refstudy/sweep_breast.py` → `docs/head_phaseA/sweep_breast_{front,q,side}.png`
+ `out/refstudy/sweep_breast.json`. Mesma câmara/luz/material do
`render_torso.py` (render como instrumento); grelha 8×8 por tile (células
A–H × 1–8) para referência espacial precisa. Gancho de sweep: `HCG_BREAST`
(JSON, lido por chamada em `body._breast_params()` — instrumento A/B como
`HCG_T1_AMP`, **não** parâmetro de spec; o vencedor torna-se default calibrado).

## 2. Variantes (só a mama muda; resto = H-TT1, digest V0 = `8c6f568ccfbbe530`)

| id | descoberta testada | params (Δ do default H-TT1) |
|---|---|---|
| V0 | baseline H-TT1 | — |
| V1 | implantação/base larga | σx 0.048→0.058, σy 0.040→0.046 |
| V2 | gota — polo inferior longo | σz 0.065, cz −0.016, dir −0.28, σy 0.042 |
| V3 | transição superior longa | σz 0.050, cz −0.004, dir −0.08, amp 0.88 |
| V4 | integrada na parede (menos saliência, mais espalhada) | amp 0.76, σx 0.054, σy 0.046, σz 0.060 |
| V5 | lateral cheia | σx 0.060, cz −0.012 |
| V6 | natural (combinação: base larga + gota suave) | amp 0.84, σx 0.056, σy 0.044, σz 0.060, cz −0.014, dir −0.24 |
| V7 | redonda compacta | amp 0.88, σx 0.044, σy 0.036, σz 0.050, dir −0.12 |
| R·real005 / R·femalebase | refs externas (mesmas vistas) | — |

Default H-TT1 (referência dos Δ): amp 0.86·bust_protrusion, σ=(0.048, 0.040,
0.055)·s, centro lm[bust]+(0, +0.008s, −0.010s), dir (0, 1, −0.18).

## 3. Protocolo de resposta (dono)

1. **Ranking geral**: p.ex. `V2 > V6 > V0` (basta o top-2/3 e os rejeitados).
2. **Apontar células** (opcional, modo B): p.ex. "no V3, perfil C4 duro",
   "V5 frente B6 vazia" — a grelha está em cada tile.
3. **Veredicto por dimensão** (opcional): implantação / volume / orientação /
   polo inferior / relação entre as duas.

O agente então: mede escolhidas vs rejeitadas (P5/P10/R4/R5 + contornos),
promove o vencedor a default (commit + digests), e regista o APRENDIDO
(ex.: "o dono prefere base larga + polo inferior curto") para os próximos sweeps.

## 3.5 RESULTADO DO GATE (2026-10-01): NÃO APROVADO — veredicto e causa

**Diagnóstico do dono/analista (OBSERVED, resumo; íntegra na sessão):** V0–V7
visualmente indistinguíveis; mama não lê como volume (linha/sombra); ombro =
aba/parábola pontiaguda; tórax caixa suavizada; abdómen em ondas; costas em
lombas; glúteo triangular/"boca"; refs muito superiores em continuidade.
"Nao interpretar variantes/parâmetros/métricas como evidência de melhoria
visual."

**Verificação numérica (docs/MECHANISM_AUDIT_01.md):** parâmetros NÃO anulados
(saliências 42–58 mm, Δ 6–12 mm vs V0, digests reproduzidos) — mas sub-limiar
visual a zoom de corpo inteiro e a base nem é mama legível. Confundidores
eliminados por medição: cabelo (não desce de z≈1455), grelha abdominal
(inactiva, mus 0.45). Controlo negativo N0 construído a posteriori.
**Nenhuma variante promovida.** Painel zoom: sweep_breast_zoom.png.

## 4. Estado

- Folhas geradas (front/q/side, 10 tiles cada, grelha A–H × 1–8): prontas para
  o gate; site actualizado (secção renders).
- 30/30 tiles com corpo visível (máscaras verificadas numericamente; o agente
  NÃO avalia visualmente — limitação declarada).
- Digests das variantes em `out/refstudy/sweep_breast.json` (V0 = H-TT1 exacto;
  determinismo confirmado).
- Fila após escolha: vencedor → default + medição do aprendido → próximo sweep
  (costas R8/R9 = H-TT2; ombro = H-TT5) → C decide-se com dados de ≥2 sweeps.

## 5. Adenda (2026-10-01): resolução da causa-raiz

O MECHANISM_AUDIT (§8) encontrou a causa-raiz: cage sem vértices na frente
da mama (uma aresta atravessa x 30–75). O protótipo C2 (HCG_BREAST2,
`_densify_front` + `_structured_breast`) corrige-a e mede-se EM BANDA das
refs em gap (17 vs 7–34), base (54 vs 58–90), f@1350 (24 vs 22–27), ápice
x (69 vs 69–71) — ver docs/BREAST_C2_01.md e breast_spec_v3.json
(instrumento plane_scan v3.2; os números v2 deste doc §3.5 com bug de fill
foram supersedidos). Painel: breast_c2_{zoom,torso}.png.
