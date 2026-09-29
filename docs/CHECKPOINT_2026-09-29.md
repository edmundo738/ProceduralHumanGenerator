# CHECKPOINT 2026-09-29 — mudança de modo de operação + auditoria do método

**Gatilho:** mensagem do dono (2026-09-29) — registo de que o processo
regrediu para "falsas melhorias" e mudança do modo de trabalhar. A mensagem
integral está resumida em `OPERATING_MODE.md` (novo, em vigor).
**Estado do repo no checkpoint:** branch `arena/01a0d51d-proceduralhumangenerator`,
HEAD `fd25a98` (push verificado), testes 136 ✓, site 8080 (7 variantes, T1
visível), T1 COSTAS em checkpoint com validação visual do dono NEGATIVA.
**Nota de processo:** 3.ª recriação do sandbox no mesmo dia; nada se perdeu
porque o trabalho estava sincronizado no remote (regra §12 do OPERATING_MODE).

---

## A. Diagnóstico do método anterior

### O que estava a funcionar (preservar)
- Pré-registo antes de medir (bandas congeladas no pré-registo de cada fase).
- Instrumento comum (mesma medição para nós e refs, @1700 mm).
- Uma mudança estrutural por fase (T1–T5), contabilidade técnica (nenhum
  achado apagado), classes FACT/MEASURED/….
- Pins como barreira de regressão; flag → default só com validação.
- Biblioteca de referências com proveniência e suitability declarada.

### Onde começámos a regredir (MEASURED/INFERRED)
A cabeça foi construída no regime certo: **estrutura aprendida das refs**
(modelo de 6 massas R1 ajustado ao alvo médio das refs → casca → campos com
limites de sinal → corretiva estatística declarada). Daí saíram F1/F2 com
8/8 critérios e IoU acima do baseline ref↔ref.

Na lapidação, o processo deslizou para **ajuste local de números sobre a
geometria existente**:
- **Orelha (CONT1):** janela C¹ + envelope medido + relevo reforçado até o
  turn entrar na banda (619° vs refs 571–993). Melhoria LOCAL mensurável —
  mas sem compreensão interna de como uma orelha constrói volume, borda,
  espessura, cavidade e ligação ao crânio. Resultado: dono classificou
  ACEITÁVEL **com dívida visual notável**. [melhorou localmente]
- **Costas (T1):** três janelas C¹ calibradas por métrica sobre o TUBO de
  superelipses existente. As bandas §4 ficaram 3/3, larguras Δ0.0 — e o dono
  reconhece que "agora parecem mais costas" — mas a geometria continua
  estranha, as transições estranhas, a forma geral não convence.
  **[FALSE IMPROVEMENT — classificação registada]**: houve alteração
  mensurável (3/3 bandas) sem progresso proporcional na solução (o tronco
  como sistema anatómico continua errado).

### Porquê aconteceu — HYPOTHESES (correcção do dono, 2026-09-29)

> **Correcção registada:** a versão anterior classificava "a matemática
> substituiu o estudo e a calibração passou a ser feita no próprio corpo"
> como causa-raiz. **Forte demais e não demonstrado** — as refs externas
> FORAM usadas para estudar e corrigir o modelo (pré-registos, bandas das
> refs, alvos médios). Não há evidência suficiente para afirmar que a
> calibração passou a ser feita no próprio corpo. Reclassificado:

**HYPOTHESIS (H-M1):** o processo de refinamento pode ter dado peso excessivo
às métricas e transformações locais em relação à compreensão estrutural
obtida das referências.

**UNKNOWN:** ainda não está demonstrado que "a matemática substituiu o estudo"
foi a CAUSA da falsa melhoria.

**O que a T-TORSO investiga (perguntas precisas, do dono):**
1. O estudo das referências realmente foi convertido em **compreensão
   estrutural suficiente** para orientar a lapidação?
2. As métricas atuais **representam adequadamente** os padrões encontrados nas
   referências?
3. Ou algumas transformações foram **corretas do ponto de vista matemático,
   mas aplicadas sobre uma representação estrutural ainda inadequada**?

Notas factuais mantidas (estas são MEASURED/OBSERVED, não hipóteses):
- O mecanismo T1 (janelas suaves aditivas sobre o tubo) não deriva de uma
  decomposição estrutural das costas (coluna + escápulas + caixa torácica +
  pelve) — é um facto da implementação, independentemente de ser ou não a
  causa do resultado ruim.
- As métricas de silhueta/corte não medem transições, quebras de plano, sulcos
  nem qualidade de volume (auditoria E) — é por isso que 3/3 bandas coexiste
  com "não gostei" (a discrepância é FACT; a atribuição de causa é a hipótese
  H-M1).
- A comparação A/B amp0 vs amp1 mede o EFEITO da intervenção (uso legítimo do
  instrumento); não é, por si, "calibração no próprio corpo" — os ALVOS das
  bandas vieram das refs.

---

## B. Contexto acumulado (não é um projeto novo)

- **Processo:** `METHOD.md` (ciclo 16+1, 3 camadas de evidência — VISUAL do
  dono, MÉTRICA do instrumento, ESTRUTURA), `DEVELOPMENT_AGREEMENT.md`
  (participantes, regras vinculativas, independência intelectual),
  `OPERATING_MODE.md` (novo, este checkpoint).
- **Estado e memória:** `STATE.md` (variantes, distância/proximidade,
  contabilidade técnica, próximos passos).
- **Estudos do corpo:** `TORSO_STUDY_01.md` (§1–6 diagnóstico medido do
  tronco; §7 execução T1 + FALSE IMPROVEMENT), `H1_TRAPEZIUS_DEPTH.md`,
  `H3H2_TRUNK.md`, `REF_STUDY_01/02.md`, `S3_BODY_INTEGRATION.md`,
  `RESEARCH_COMPARATIVE_01.md` (7 projetos estudados ao nível da fonte),
  `RESEARCH_GATE_01/02.md`.
- **Estudos da cabeça:** `HEAD_STUDY_01`, `HEAD_PHASE_A*`, `S4_FACE`,
  `NECK_N1_*`, `HEAD_CONT1.md` (§5 = pré-registo CONT2), `HEAD_FACE_B.md`.
- **Biblioteca:** `REFERENCE_LIBRARY.md` + `references/` (14 entradas,
  INDEX com guarda de política; metas com suitability).
- **Instrumentos:** `tools/refstudy/` (medição comum), `tools/reflib/`
  (inspetor), `tools/preview/` (site), pins/tests.
- **Fontes externas recolhidas (em memória de sessão):** ANSUR II feminino
  (CSV público, cit. Gordon et al. 2014); normas da coluna (PMC4771498,
  Legaye 2002); dimorfismo torácico (s41598-020-67664-5); mama/nádega
  (plasticsurgerykey, Wong 2016); antropometria facial (globo-rebordo,
  exoftalmometria, espessuras de tecido); guias de topologia (vsquad,
  polycount); SMPL/QuadriFlow (estatística de forma).
- **Builds versionadas:** `builds/build02` (baseline congelado).

## C. Biblioteca de referências — mapa de utilidade (1.ª passagem)

14 entradas em `references/` (INDEX). Organização por utilidade:

| utilidade | entradas | notas |
|---|---|---|
| torso feminino realista (alvo principal) | REF-F-REAL-001 Female base · 003 FemaleCharacter · 005 T-pose GLB (ADMITIDA: pele nua 14474 v, lombar 56.2) | 005 é a melhor "pele nua" realista |
| topologia do corpo | REF-F-REAL-002 Body Topo (base mesh, sem pés/mamas — pesos menores) | quad topology de referência |
| corpo completo alternativo | REF-F-REAL-004 Lucia (makehuman) | realista médio, útil para variância |
| **torso PARCIAL** | REF-F-REAL-007 MPPled.fbx (scope=torso) | **pouco estudado até agora** — prioritário para o estudo do sistema torso |
| **POSES** | REF-F-REAL-008 Booty Hip Hop Dance (rig) | leitura do corpo em pose não-neutra (validação) |
| estilização feminina | REF-F-REAL-006 MOLLY (EXCLUÍDA dos alvos anatómicos: lombar 1.4, hip 640) · REF-F-ANIR-001 fffemale 11 | 006 serve para estilização, não anatomia |
| anime feminino (padrões independentes de estilo) | REF-F-ANIME-001/002/003 (pack SimpleRig: Anime/Base/Superhero) | o que sobrevive ao estilo = estrutura |
| masculino | REF-M-REAL-001 whitewalker · REF-M-ANIME-001 Anime_Male_A | contraste de sexo (dimorfismo) |

**Gaps (regiões SEM cobertura — procurar externo quando o estudo pedir):**
costas/escápula em detalhe, coluna/sulco paravertebral, glúteos (lóbulos +
sulco), mamas (nenhuma ref atual serve de alvo — TORSO_STUDY §2.3),
axila/ombro, orelha isolada de qualidade, esqueleto (caixa torácica/pelve
3D), mãos/pés de referência, anatomia de superfície (padrões musculares).

## D. Estudo real — 1.ª extração de padrões (torso; das medições já em docs + literatura recolhida)

> Âmbito honesto: padrões extraídos dos dados JÁ medidos (REF_STUDY_01,
> TORSO_STUDY_01 §2, real005) + literatura em memória. O estudo completo
> (todas as refs, todas as regiões, quebras de plano, transições por vista) é
> o próximo ciclo (§H) — esta é a semente, não a colheita.

**Padrões recorrentes (≥3 refs independentes, @1700 mm):**
- P1 (MEASURED, 4/4 refs): **lordose lombar 54–70 mm** — padrão estrutural,
  não individual (nossa pré-T1: 19.5).
- P2 (MEASURED, 4/4): **nádegas nunca mais posteriores que as costas
  torácicas** (−8…−20) — o balanço sagital cifose↔lordose↔nádega é um sistema.
- P3 (MEASURED, 3/3 com valor): **cintura 0.72–0.81 do quadril** (circ) —
  hourglass nas refs (tensão com a média ANSUR 0.842, declarada).
- P4 (MEASURED, 3/3): **peito 268–280 de largura, 218–236 de profundidade**
  — o nosso barril 352/314 está fora do p95 ANSUR nas DUAS dimensões.
- P5 (OBSERVED, perfis): **glúteos = lóbulos laterais + sulco central** (o
  contorno posterior tem máximo NOS LADOS e sulco no CENTRO); o nosso é um
  bloco central (mínimo no centro em |x|≤60).
- P6 (OBSERVED): o **nível do máximo torácico** das refs está ABAIXO do nosso
  (0.735–0.747·S vs 0.768·S) — o nosso tórax é alto além de largo.

**Da literatura (em memória, re-citar no estudo):** curvaturas da coluna
(Legaye: lordose lombar ~40–60°, sacro inclinado); dimorfismo torácico
feminino (tórax mais estreito/raso); mamas (nível ~0.72–0.75·S, projeção,
sulco inframamário); nádegas (Wong 2016: projeção/rotação).

**Pergunta que o estudo completo tem de responder:** quais destes padrões são
*consequência de estruturas* (costelas, pelve, escápulas, massa glandular) e
quais são *superfície* — e qual representação do nosso gerador produz os
primeiros sem colar os segundos.

## E. Auditoria das métricas atuais

| métrica | estado | nota |
|---|---|---|
| larguras/profundidades/circ por corte; cotas de nível; IoU de silhueta (confounds declarados); turn da orelha; perfis sagitais linha média | **CONFIÁVEL** | instrumento comum, refs + ANSUR como restrição |
| concavidade lombar | **REVISAR** | depende dos ápices torácico/nádega (argmin em bandas) — sensível à forma global; manteve-se após T1 mas a leitura da CAUSA não é confiável |
| costas-altas-vs-occipital | **CONFOUNDIDA** | mede contra um occipital nosso raso (−99 vs refs −139/−145): a referência da métrica é defeituosa |
| nádega-vs-torácica | **REVISAR** | o instrumento re-centra Y pela caixa → frame desloca ~Δ/2 (artefacto declarado §7.2 TORSO_STUDY) |
| cintas de peito/busto (argmax em banda) | **REVISAR** | dependem do nível escolhido; TORSO_STUDY usa cotas fixas — manter essa disciplina |
| **transições / quebras de plano / sulcos** | **CEGA (inexistente)** | o olho do dono vê o que nenhuma métrica atual mede — é a lacuna que permitiu a FALSE IMPROVEMENT |
| qualidade de volume 3D percebido | **CEGA** | só silhueta + cortes horizontais |
| percepção em poses | **INEXISTENTE** | rigs existem na biblioteca (REAL-008) |
| "lê como humano" | **UNKNOWN** | gates visuais do dono passam a critério explícito por região (§I) |

**Decisão:** o próximo ciclo adiciona métricas de curvatura (perfis κ por
região), comparação multi-vista por região (frente/perfil/costas/¾, alto/baixo)
e leitura em pose — antes de voltar a mexer na geometria.

## F. Auditoria da geometria atual (por região)

| classe | regiões | evidência |
|---|---|---|
| **BOM (preservar)** | cabeça F2 (8/8 critérios, IoU frente ≥ baseline refs), mãos (S3.8: 77.5 mm), pés (S3.6), simetria L/R (Hausdorff ~0), determinismo/pins, instrumentos, biblioteca | MEASURED nos docs respetivos |
| **APROVEITÁVEL** | pescoço superior N1 (N-C1 15/18); contorno da orelha (turn na banda; relevo = dívida); **representação por estações + loft quad** (a topologia é sã — o problema é a FORMA que ela carrega, não a malha); braços/pernas como cascas inseridas (silhueta lê bem) | MEASURED/OBSERVED |
| **LAPIDÁVEL** | trapézio/clavícula (campos existentes, nuca 1.8× refs → CONT2), sulco glúteo (bloqueado pelos lóbulos), barriga (pequeno excesso frontal) | TORSO_STUDY §2 |
| **ESTRUTURALMENTE INADEQUADO (reconstruir como sistema)** | **tronco**: barril torácico (P4/P6), cintura tubular (P3), glúteos bloco central (P5), curva S aplicada como janelas suaves sobre um tubo (T1 = FALSE IMPROVEMENT declarada), mamas como bumps sobre o barril (UNKNOWN nas refs), transições torso↔membros (axila/ombro só por silhueta) | TORSO_STUDY §2 + veredicto do dono |
| **UNKNOWN** | leitura em poses não-neutras; braços/pernas em movimento; como o tronco lê de ¾ alto/baixo | sem medição |

## G. Hipóteses — porque o corpo ainda não lê humano (HYPOTHESIS, testáveis)

- **H-T1:** o tronco é um TUBO de superelipses + campos aditivos; costas
  humanas são o resultado da intersecção de ESTRUTURAS (coluna, escápulas,
  caixa torácica, pelve) cujas bordas criam quebras de plano e sulcos que um
  campo suave não produz. *Teste:* mapas de curvatura refs vs nosso nas
  regiões das estruturas.
- **H-T2:** o S correto é consequência do BALANÇO sagital entre tórax
  (recuado) e pelve (avançada), não de janelas aditivas — por isso as janelas
  deram "costas mais costas" com transições estranhas. *Teste:* medir o
  balanço estrutural das refs (linhas de peso tórax/pelve) antes de mais
  campos.
- **H-T3:** o barril torácico mascara correções locais: cintura, glúteos e
  mamas lêem como anomalias sobre um bloco (por isso T2–T5 em fila, um métrica
  de cada vez, não converge). *Teste:* proporção relativa
  ombro:tórax:cintura:quadril refs vs nosso como VETOR, não métrica a métrica.
- **H-T4:** mamas/glúteos como bumps independentes não produzem a interação
  com a parede (sulco inframamário, dobra glútea, transição lateral). *Teste:*
  estudar as refs 005/003/007 nessas transições específicas.
- **H-T5 (quase MEASURED):** as métricas de silhueta/corte são cegas às
  transições — a discrepância "3/3 bandas" vs "não gostei" é a prova.
  *Mitigação:* métricas de curvatura + gates visuais por região (§I).
- **H-T6:** a percepção global depende de proporções RELATIVAS do sistema
  (incluindo pescoço/cabeça/pernas) — estudar o torso isolado artificialmente
  esconde parte do problema. *Teste:* painéis com contexto corporal completo.

## H. Plano de reconstrução (preservar / lapidar / reconstruir / testar)

1. **PRESERVAR:** cabeça F2, mãos, pés, topologia/representação por estações,
   instrumentos, biblioteca, pins, site. Nada disto se mexe no próximo ciclo.
2. **LAPIDAR (depois do torso):** orelha (dívida visual), nuca/pescoço-base
   (CONT2), trapézio/clavícula.
3. **RECONSTRUIR — ciclo "T-TORSO SISTEMA" (próximo, segue OPERATING_MODE §15):**
   a. ESTUDO: as 14 refs da biblioteca (com prioridade a 005/003/001/002 e ao
      torso parcial 007) + anatomia externa (esqueleto torácico/pélvico,
      escápula, coluna) + padrões D — por região E por transição, frente/
      perfil/costas/¾, com variação de estilo (anime vs realista: o que
      sobrevive ao estilo = estrutura).
   b. MÉTRICAS REVISADAS (auditoria E): curvatura por região, proporções
      relativas como vetor, multi-vista, pose.
   c. DECISÃO por componente: preservar / modificar / reconstruir — escrita
      antes de implementar (pré-registo).
   d. IMPLEMENTAÇÃO: provável modelo estrutural do tronco (estações dirigidas
      por cotas anatómicas do padrão extraído; volumes emergentes da parede
      em vez de bumps aditivos) — A DECIDIR pelo estudo, não agora.
   e. A T1 existente fica em checkpoint (código + medições + variante site);
      o destino (revert/rebuild/absorver) decide-se no fim do estudo — pergunta
      em aberto ao dono (ver fim do documento).
4. **TESTAR:** cada hipótese G com a observação específica indicada.

## I. Método de validação (como saber que MELHOROU de verdade)

1. **Multi-vista por região:** front / back / profile / ¾ (+ alto/baixo),
   mesma câmara/luz/material, nós vs refs — painéis por REGIÃO, não só corpo
   inteiro (render_torso.py generaliza para isto).
2. **Poses:** ≥2 poses não-neutras (rig REAL-008 da biblioteca como leitura;
   declarar limitações) — o corpo não pode deixar de ler em pose.
3. **Métricas:** bandas existentes (onde confiáveis) + novas (curvatura,
   proporção relativa como vetor, IoU por região) — todas vs banda das refs,
   nunca só nós-vs-nós.
4. **GATE HUMANO explícito:** validação visual do dono POR REGIÃO com
   checklist (forma, transição, volume, proporção) — "parece melhor" não
   chega; o resultado é classificado (incl. FALSE IMPROVEMENT) e a
   classificação fica registada.
5. **Anti-regressão:** pins/guardas; comparação lado-a-lado com o estado
   ANTERIOR (não apenas com refs); testes completos.

---

## Respostas do dono (2026-09-29, mesmo dia)

1. **T1 no build default: PERMANECE ACTIVO** — como estado
   **experimental/visível do checkpoint**, explicitamente **NÃO tratado como
   anatomia validada**. A decisão definitiva (preservar vs modificar vs
   reconstruir) fica suspensa até o estudo T-TORSO apresentar evidência
   suficiente para a comparação.
2. **Fontes do estudo T-TORSO: MISTURA**, na ordem:
   `biblioteca atual + anatomia (base: 005/003/001/002/007) → identificar
   gaps → Arena procura refs externas ESPECÍFICAS para os gaps → comparar →
   extrair padrões → só então propor alterações`. O ciclo NÃO bloqueia à
   espera de ZIP novo do dono (entram quando disponíveis). Refs externas
   servem para preencher lacunas E para TESTAR se os padrões se repetem.
   **Nenhuma referência isolada é verdade — padrões recorrentes entre fontes.**

**Regra nova para o T-TORSO (e em geral, OPERATING_MODE §7):** cada conclusão
importante regista **QUEM a sustenta** — `n refs / quais` — separando
"apareceu numa referência" (OBSERVED, n=1) de "padrão encontrado em várias
referências" (n≥3). (Já praticávamos isto de forma implícita com as
previews/painéis — a regra formaliza; a lapidação seguinte optimiza.)

**Registo final:** este checkpoint + `OPERATING_MODE.md` passam a ser leitura
obrigatória no passo 01 CONTEXTO de todos os ciclos (METHOD.md atualizado com
o apontador).
