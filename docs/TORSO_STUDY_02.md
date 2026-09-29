# TORSO STUDY 02 — o torso como SISTEMA (estudo real das referências)

**Data:** 2026-09-29 · **Ciclo:** T-TORSO SISTEMA (CHECKPOINT_2026-09-29 §H) ·
**Estado:** estudo MEDIDO — NENHUMA alteração de geometria foi feita neste ciclo.
**Perguntas do dono (§A do checkpoint, versão corrigida):** (1) o estudo das refs
foi convertido em compreensão estrutural suficiente para orientar a lapidação?
(2) as métricas actuais representam adequadamente os padrões das refs?
(3) ou transformações matematicamente correctas foram aplicadas sobre uma
representação estrutural inadequada?

**Instrumento:** `tools/refstudy/torso_refs.py` (extracção de TODOS os modelos
da biblioteca) + `torso_orient.py` (orientação por MEDIÇÃO) +
`torso_system.py` (descritores de sistema + painéis). Tudo sobre o instrumento
comum (medição por cortes, @1700 mm, chão z=0, frente +Y).

## 1. Corpus e validade (com exclusões declaradas)

| modelo | estilo | sagital | coronal | notas de validade |
|---|---|---|---|---|
| femalebase | realista | ✓ | ✓ larguras | braços fora da banda do peito |
| femalechar | realista | ✓ | ✗ larguras peito (braços A-pose saturam a grelha) | |
| bodytopo | base mesh | ✓ | ✗ larguras (braços; sem pés: estatura INFERRED) | sem mamas (busto n/a) |
| real005 | realista | ✓ | ✓ | T-pose; pele nua; a melhor ref de pele |
| ff11 | anime-realista | ⚠ low-poly (2945 v: cortes grosseiros) | ✗ (artefactos) | sagital com cautela |
| animeF | anime | ✓ | ✗ larguras (braços) | contraste de estilo |
| lucia | makehuman | ✗ (sagital inconclusivo) | ✓ (braços afastados) | |
| whitewalker | masculino | ✗ | ✗ EXCLUÍDO | z-extent ≠ estatura (busto/plinto) — normalização quebrada |
| mppled | torso sculpt | — frame próprio (z-extent ≠ estatura) | — | SÓ forma; glúteos medidos (bloco, n=1) |
| real006 | estilizada | EXCLUÍDA (TORSO_STUDY_01 §7.2) | | |
| **ours / ours0** | — | T1 on / off (mesma topologia) | ✓ (braços excluídos pela regra do estudo) | |

**Orientação — lição medida (registo de método):** a decisão de flip vem da
MEDIÇÃO sagital (perfil posterior com lombar plausível + nádegas atrás), NUNCA
do eixo do ficheiro. Heurísticas de nuvem de pontos (nariz; mamas vs glúteos
por medianas) foram REFUTADAS neste estudo: (a) penteado/cabelo engana o
teste do nariz (mppled); (b) protrusão relativa ao centro min/max é simétrica
por construção (erro cometido e corrigido aqui, documentado); (c) o perfil do
próprio instrumento resolve (real005: lado +Y tem lombar 56.2 e nádegas +131
@920 ⇒ +Y = costas ⇒ flip). Onde o instrumento não corre (pernas fundas,
bustos), o modelo é excluído do sagital — não se adivinha.

## 2. PADRÕES (proveniência obrigatória: n refs / quais)

### P1 — Lordose lombar: refs 53.7–69.7 [n=5: femalebase 55.7, femalechar 53.7, bodytopo 69.7, real005 56.2, animeF 57.0] · MEASURED
A concavidade lombar das refs está em **53.7–69.7 mm** (incluindo a anime!).
**Nós T1: 45.3 — ainda 8.4 mm ABAIXO do mínimo das refs.**
⚠ **Achado de método:** a banda pré-registada T1 ([40,75], TORSO_STUDY_01 §4)
era MAIS LARGA do que a banda real das refs — passar a banda T1 ≠ alcançar as
refs. Isto responde à pergunta (2) do dono: **parcialmente NÃO — os alvos das
métricas estavam achatados/alargados em relação aos padrões reais.**

### P2 — Balanço nádega-vs-torácica: refs −8…−20 [n=4 realistas] · MEASURED
Nádegas nunca mais posteriores que −8 nem menos que −20 (realistas);
animeF −6. **Nós T1: −6.0 (limite/fora por 2 mm); T1-off: +12 (invertido).**

### P3 — Ápice torácico: refs z 1280–1335 [n=5] · MEASURED
**Nós T1: 1265 — 15 mm abaixo do mínimo** (T1-off: 1305 ✓ dentro). O campo
"costas altas" da T1 deslocou o ápice para baixo — efeito colateral medido.

### P4 — Nível da mama: refs z 1190–1260 (0.70–0.741·S) [n=5: fb 1260, fc 1210, bt 1190*, r005 1240, animeF 1235] · MEASURED
(*bodytopo sem mamas — mede a parede.) **Nós: 1305 (0.768·S) — 45–115 mm
ALTO DEMAIS.** A nossa "mama" é o máximo do barril, não uma mama ao nível das
refs. **real005 TEM mama utilizável (ver P5) — T4 deixou de ser UNKNOWN.**

### P5 — Saliência da mama (vs submamário 0.795·S): refs 54–70 mm [n=4 com mama: fb 54, fc 70, r005 68, animeF 64] · MEASURED
**Nós: 26 mm — menos de METADE do mínimo das refs.**

### P6 — Curvatura κ(z) do perfil posterior · INSTRUMENTO LIMITADO
A quantização dos cortes de 5 mm limita o κ (degraus ±0.003/mm) — **sem
padrão numérico defensável**; os painéis (`torso_system_curvature.png`)
ficam como comparação VISUAL para o dono. A lacuna "métricas cegas a
transições" (CHECKPOINT §E) **continua em aberto** — candidata a métrica nova
no próximo ciclo (cortes a 2 mm ou κ sobre interpolação suave).

### P7 — Cintura relativa: refs 0.63–0.66 [n=4 limpas: fb 0.63, fc 0.65, r005 0.66, lucia 0.65] · MEASURED
(largura mínima / largura da anca; bodytopo/animeF inválidas por braços;
ff11 por low-poly). **Nós: 0.70 — FORA por +0.04…+0.07** (cintura tubular,
agora em razão relativa, não só absoluta).

### P8 — Peito relativo: refs 0.78–0.96 [n=3: lucia 0.78, fb 0.94, r005 0.96] · MEASURED
**Nós: 0.91 ✓ DENTRO.** O problema do peito não é a razão peito/anca.

### P9 — Largura do peito (absoluta): refs 252–316 [n=3 limpas: lucia 252, fb 316, r005 316] · MEASURED
**Nós: 356 — 40 mm acima do máximo das refs** (e ANSUR p95 = 314).

### P10 — Profundidade do peito: refs realistas 218–236 [n=4] · MEASURED
**Nós: 310 — ~75 mm além do máximo.** O barril torácico é largo E fundo
(confirma TORSO_STUDY_01 §2.3 com corpus limpo).

### P11 — Profundidade da nádega: refs 198–232 [n=5] · MEASURED
**Nós T1: 250 (+18); T1-off: 266 (+34)** — a T1 melhorou a direção.

### P12 — Níveis (cotas): refs cintura 0.61–0.70·S, anca 0.46–0.58·S [n≥4] · MEASURED
**Nós: 0.64 / 0.50 ✓ DENTRO.** As COTAS estão certas — o problema é a FORMA
e a PROPORÇÃO, não o nível.

### P13 — Secção torácica BOXY: refs n≈3.8 [n=2 confiáveis: real005 3.8, femalebase 3.8; femalechar 4.5 ±braços] · MEASURED (n=2, +prior anatómico)
Expoente de superelipse da secção do peito: refs ≈**3.8** (caixa torácica
achatada/boxy) vs **nós 2.2** (elíptico). **O nosso tórax é redondo onde as
refs (e a anatomia — caixa torácica) são achatadas.** n=2 → confirmar com
refs externas (gap G2).

### P14 — Secção do peito dominada pelas COSTAS: refs front_share 0.60–0.72 [n=3 realistas: r005 0.60, fb 0.72, fc 0.68] · MEASURED
(partilha frente/trás do contorno pela média.) Nas refs, a traseira do peito
domina (0.60–0.72 = frente menor); **nós: 1.06 (frente domina)** — o nosso
tronco está "inclinado à frente" em relação ao balanço sagital das refs.
Liga a H-T2 (balanço tórax-recuado/pelve-avançada).

### P15 — Secção da cintura: refs front_share 1.06–1.52 (barriga > lombar) [n=5] · MEASURED
**Nós T1-off: 1.00 (simétrica — tubo); T1: 1.15** (a curva S começou a
criar a assimetria certa, ainda curta — coerente com P1).

### P16 — Sulco glúteo (lóbulos vs linha média): refs 7–26 mm [n=5: fc 26.0, fb 22.8, animeF 24.6, r005 18.5, bt 7.0] · MEASURED
Todas as refs válidas têm lóbulos laterais + sulco central medidos.
**Nós T1: 4.4 mm (esboço); T1-off: +5.3 (bloco — centro mais posterior que
os lóbulos).** A T1 criou um esboço de sulco mas longe do mínimo das refs.

### P17 — mppled (n=1, frame próprio): glúteos TAMBÉM bloco (+1.8) · OBSERVED
O torso sculpt parcial da biblioteca não tem lóbulos — qualidade duvidosa
para glúteos; suitability mantém UNKNOWN. Registo de que "estar na
biblioteca" ≠ "ser padrão".

## 3. Comparação com o nosso modelo — síntese

| padrão | refs | nós T1 | nós T1-off | veredicto |
|---|---|---|---|---|
| P1 lombar | 53.7–69.7 | 45.3 | 26.9 | fora (−8.4 do mín) / fora |
| P2 nádega-vs-torácica | −8…−20 | −6.0 | +12 | limite / invertido |
| P3 ápice torácico z | 1280–1335 | 1265 | 1305 | fora / ✓ |
| P4 nível mama | 1190–1260 | 1305 | 1305 | **fora (+45…115)** |
| P5 saliência mama | 54–70 | 26 | 26 | **fora (−28 do mín)** |
| P7 cintura/ância | 0.63–0.66 | 0.70 | 0.70 | fora |
| P9 largura peito | 252–316 | 356 | 356 | **fora (+40)** |
| P10 prof. peito | 218–236 | 310 | 314 | **fora (+74)** |
| P11 prof. nádega | 198–232 | 250 | 266 | fora (+18) |
| P12 níveis | 0.61–0.70 / 0.46–0.58 | 0.64 / 0.50 | ✓ | ✓ |
| P13 secção peito n | ≈3.8 | 2.2 | 2.2 | **fora (redondo vs boxy)** |
| P14 front_share peito | 0.60–0.72 | 1.06 | 1.06 | **fora (frente domina)** |
| P16 sulco glúteo | 7–26 | 4.4 | +5.3 | fora / bloco |

**Leitura honesta:** das 13 dimensões medidas, estamos DENTRO em 2 (P8, P12)
— as cotas e a razão peito/anca. O problema é estrutural: forma das secções
(P13/P14), barril (P9/P10), cintura relativa (P7), balanço sagital (P1/P2/P3)
e volumes emergentes (P4/P5/P16).

## 4. Respostas às perguntas do dono (com classificação)

1. **O estudo das refs foi convertido em compreensão estrutural suficiente?**
   **NÃO (MEASURED, neste ciclo).** Antes deste estudo, P4, P5, P13, P14 e
   P16 simplesmente NÃO ERAM MEDI DOS — não havia métricas para eles. A
   compreensão estrutural era parcial (cotas ✓, silhueta parcial) e a
   lapidação correu sem alvo estrutural para secções, balanço e volumes.
2. **As métricas representam os padrões das refs?** **PARCIALMENTE (MEASURED).**
   As bandas pré-registadas estavam mais largas que as refs (P1: [40,75] vs
   [53.7,69.7]) e métricas-chave não existiam (P13/P14/P16, κ-transições).
3. **Transformações correctas sobre representação inadequada?** **SIM para a
   T1 (INFERRED, consistente com as medições):** o campo da T1 é
   matematicamente são (larguras Δ0.0, C¹) e moveu P1/P2/P11/P15/P16 na
   DIREÇÃO das refs — mas sobre o tubo elíptico (P13/P14 errados) e com
   alvos achatados (P1). Por isso "3/3 bandas" coexistiu com "não gostei".
   H-M1 fica PORTANTO suportada nas duas metades (peso excessivo das métricas
   E representação inadequada) — mas como hipótese confirmada por ESTE
   estudo, não como causa-raiz declarada antes dele.

## 5. Gaps (para a mistura: refs externas específicas)

- **G1 mamas:** real005 já serve de alvo (P4/P5) ✓ FECHADO por este estudo;
  confirmar com +1–2 refs externas realistas.
- **G2 secções/quebras de plano:** n=2 em P13 — precisamos de mais refs
  realistas com braços FORA da banda (ou vestidas) para medir secções limpas.
- **G3 escápula/coluna:** κ cego (P6) — melhorar o instrumento (cortes 2 mm)
  antes de estudar quebras de plano.
- **G4 lóbulos glúteos/topologia:** nenhuma ref com topologia de referência
  para o sulco (mppled = bloco, P17) — procurar externo.
- **G5 poses:** rig REF-F-REAL-008 não medido (validação em pose — fica para
  a fase de validação, depois da reconstrução).

## 6. Hipóteses para o checkpoint de decisão (HYPOTHESIS — não conclusões)

- **H-D1 (representação):** o tubo de superelipses com fs/bs fixos + bumps
  aditivos não produz simultaneamente P13 (secção bozy), P14 (costas
  dominantes), P16 (lóbulos) e P4/P5 (mama ao nível certo) — porque não tem
  graus de liberdade para quebras de plano estruturais. *Teste:* protótipo
  de estação torácica com n≈3.8 + recuo sagital e medir P13/P14/P9/P10.
- **H-D2 (balanço):** o S correto é o BALANÇO tórax-recuado/pelve-avançada
  (P14+P3+P2), não janelas aditivas — o recuo torácico estrutural pode
  substituir o campo "costas altas" da T1. *Teste:* variante com estações
  torácicas recuadas em vez de campo.
- **H-D3 (T2):** a cintura deve ser perseguida como RAZÃO 0.63–0.66 (P7),
  não como largura absoluta (a largura absoluta das refs 212–220 já estava
  no alvo ANSUR do plano antigo).
- **H-D4 (T4):** mama = massa ao nível 0.70–0.741·S com saliência 54–70 sobre
  uma PAREDE recuada (P4+P5+P14) — real005 é o alvo primário, confirmar com
  refs externas (G1).

## 7. Próximo passo (checkpoint de DECISÃO com o dono)

Este estudo NÃO mexe na geometria. Ao dono, para decidir preservar/lapidar/
reconstruir (por região, CHECKPOINT §F actualizado por estes dados):

1. **T1 (campo S):** os dados dizem: direção certa, amplitude insuficiente
   (P1), ápice deslocado (P3) e mecanismo possivelmente substituível por
   balanço estrutural (H-D2). Opções: (a) recalibrar amplitudes; (b) migrar
   para balanço estrutural (H-D2) e retirar o campo; (c) manter como está
   durante a reconstrução do barril.
2. **Barril (P9/P10/P13/P14):** reconstrução das estações torácicas — é a
   mudança com maior número de padrões dependentes (P4/P5/P14 arrastam).
3. **Cintura (P7):** razão relativa na reconstrução das estações (junto com
   o barril? uma mudança de cada vez — decidir ordem).
4. **Glúteos (P16) e mama (P4/P5):** volumes emergentes DEPOIS da parede
   estar certa (T4 absorve o sulco, como já previsto).

Painéis para a leitura visual do dono: `torso_system_sagittal.png`,
`torso_system_coronal.png`, `torso_system_gluteal.png`,
`torso_system_curvature.png` (docs/head_phaseA/; também no site).
