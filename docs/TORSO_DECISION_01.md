# TORSO DECISION 01 — checkpoint de DECISÃO do T-TORSO (formulação, não implementação)

**Data:** 2026-09-29 · **Base:** TORSO_STUDY_02 (18 padrões medidos, proveniência
n refs/quais) · **Estado:** NENHUMA geometria foi alterada. Este documento
formula a decisão; **o gate é do dono** (mensagem do dono: *"não transforme o
estudo em implementação automática; quero ver por que a alternativa escolhida
explica o maior conjunto de evidências, quais hipóteses ela testa e como
saberemos se houve melhoria real ou apenas outra falsa melhoria"*).

**A pergunta-guia (do dono):** *qual das alternativas explica mais padrões
SIMULTANEAMENTE?*

---

## 1. As alternativas

- **A — RECALIBRAR A T1:** subir amplitudes/ajustar janelas do campo S
  (lombar para ≥53.7, ápice para 1280–1335, balanço para −8…−20).
- **B — RECONSTRUÇÃO ESTRUTURAL DO TÓRAX (H-D1+H-D2):** reescrever as
  estações torácicas — secção **boxy** (superelipse ≈3.8, P13), **dominada
  pelas costas** (front_share 0.60–0.72, P14), **largura 252–316 e
  profundidade 218–236** (P9/P10, com bornes ANSUR), **nível do ápice
  1280–1335** (P3) e **recuo sagital da caixa torácica** (balanço
  tórax-recuado/pelve-avançada, H-D2).
- **C — B COM A T1 COMO ANDAIME:** o mesmo B, com a questão T1 resolvida
  DENTRO dele: durante B, a janela "costas altas" (ALTA) é DESLIGADA (o
  recuo estrutural substitui-a — evitar dupla correcção); lombar/sacro
  mantêm-se; DEPOIS de B, re-medir P1/P2/P11/P15/P16 e decidir
  manter/recalibrar/absorver o campo **por medição** (não por apego).
- **D — T2 CINTURA PRIMEIRO** (ordem do plano antigo): estreitar a cintura
  (razão 0.63–0.66, P7/P18) antes do tórax.

## 2. Matriz de poder explicativo (padrões = TORSO_STUDY_02; ✓ directo, ◐ parcial/habilitado, · intocado, ⚠ risco)

| padrão | A recalibrar T1 | B tórax estrutural | C = B + andaime | D cintura |
|---|---|---|---|---|
| P1 lombar 53.7–69.7 | ✓ | ◐ (recuo muda o referente; amplitude pode faltar) | ◐ (janela lombar mantida cobre) | · |
| P2 balanço −8…−20 | ✓ | ◐ | ◐ | · |
| P3 ápice 1280–1335 | ✓ | ✓ | ✓ | · |
| P4 mama alta +45–115 | · (consequência do nível do barril) | ◐ (a parede desce o máximo) | ◐ | · |
| P5 saliência 26 vs 54–70 | · | ◐ habilita T4 (parede certa → mama como massa) | ◐ | · |
| P7 cintura 0.70 vs 0.63–0.66 | · | ◐ habilita (estações adjacentes) | ◐ | ✓ |
| P9 largura peito +40 | · | ✓ | ✓ | · |
| P10 prof. peito +74 | · | ✓ | ✓ | · |
| P11 prof. nádega +18 | ◐ | · (T4/ânde) | · | · |
| P13 secção boxy 2.2 vs 3.8 | · | ✓ | ✓ | · |
| P14 frente domina 1.06 vs 0.60–0.72 | · | ✓ | ✓ | · |
| P15 cintura share | ✓ | ◐ | ◐ | ✓ |
| P16 sulco 4.4 vs 7–26 | ◐ (só recua o centro; sem lóbulos) | · (T4) | · | · |
| P18 anca 392 vs refs 324–336 (ANSUR ✓) | · | · (tensão declarada; decisão própria) | · | ◐ (razão com bornes) |
| **TOTAL directo** | **4** (P1,P2,P3,P15) | **5** (P3,P9,P10,P13,P14) | **5** | **2** (P7,P15) |
| **parcial/habilitado** | 2 (P11,P16) | 5 (P1,P2,P4,P5,P7) | 6 (+P1 coberto pela janela) | 1 |
| **intocado** | 6 | 2 (P11,P16) | 2 | 10 |
| **riscos** | polir números numa parede errada (P13/P14) | junção ombro/braço (estações deltoide assentam no peito); pins movem; interacção com a T1 | idem B + gestão do andaime | re-trabalho: cintura reconstruída adjacente a um barril que depois muda |

**Causalidade (por que B/C domina):** P4 é CONSEQUÊNCIA do nível do barril (o
nosso "ápice de mama" É o máximo do barril a 1305); P1/P2 MEDEM-SE contra o
ápice torácico; P7 está acoplada às estações adjacentes. Os sintomas de A e D
estão a jusante do tórax. A é a única que não toca nas duas causas mais
profundas medidas (P13/P14 — estrutura do volume, não quantidade).

## 3. Recomendação (PROPOSTA — aguarda gate do dono)

**C — reconstrução estrutural do tórax com a T1 como andaime**, na ordem:

1. **B (tórax):** estações torácicas boxy/costas-dominantes/níveis/tamanhos
   (bornes ANSUR), recuo sagital (H-D2); ALTA desligada durante B.
   *Testa:* H-D1 (representação) e H-D2 (balanço). *Esperado:* P3/P9/P10/P13/
   P14 → bandas; P4 melhora; P8 (0.91→~0.81, banda refs 0.78–0.96 ✓) e P12
   não regredem.
2. **T2-cintura (razão):** 0.63–0.66 com bornes ANSUR (P7/P18).
3. **T4-volumes:** mama ao nível 0.70–0.741·S, saliência 54–70 (alvo primário
   real005, confirmar externo); lóbulos glúteos + sulco (P16) no mesmo pacote
   de "volumes emergentes".
4. **T5 pescoço-base + CONT2** (como já planeado).

## 4. Como saberemos que foi melhoria REAL (anti-falsa-melhoria)

1. **Regra das bandas (nova, emendada no OPERATING_MODE):** as bandas de
   validação derivam da banda DAS REFS VÁLIDAS (n declarado) — **nunca mais
   largas nem mais suaves**. Passar numa banda amolecida ≠ proximidade
   anatómica (lição P1: a banda T1 [40,75] era mais larga que as refs
   [53.7,69.7]).
2. **Matriz antes/depois multi-padrão:** os 18 padrões medidos pelo MESMO
   instrumento antes e depois; o resultado é classificado por padrão
   (melhorou/regrediu/sem mudança), não por uma métrica isolada.
3. **Guardas de regressão:** P8 e P12 (os 2 em que estamos dentro) têm de
   continuar dentro; larguras que não devem mudar não mudam; pins actualizados
   deliberadamente (barreira, não obstáculo).
4. **Gates visuais do dono por região:** painéis frente/costas/perfil/¾ antes
   × depois × refs (o render_torso generaliza para isto); classificação
   obrigatória do dono (melhorou / melhorou localmente / FALSE IMPROVEMENT /
   regressão) registada no checkpoint da fase.
5. **A T1 é re-decidida DEPOIS de B por medição** (manter/recalibrar/absorver)
   — o destino dela não é parte da decisão de agora.

## 5. O que NÃO vamos fazer

- Implementar qualquer coisa antes do gate do dono sobre §3.
- Re-definir bandas a posteriori para fazer passar.
- Declarar vitória por uma métrica isolada ou por "houve mudança visível".

## 6. Perguntas ao dono (gate)

1. Aprova **C** (B com T1-andaime) e a ordem B → T2-razão → T4-volumes → T5?
2. Desligar a janela ALTA da T1 durante B (evitar dupla correcção) — OK?
3. P18: concorda que **razões vêm das refs, absolutos limitados por ANSUR**
   (não perseguir a magreira slim das refs em largura absoluta)?
4. Painéis visuais (torso_system_panels.png, no site): o seu gate visual
   confirma a leitura dos números (barril frente-dominante, secção redonda,
   esboço de sulco)? Algo que os números não estão a capturar e que ele vê?
