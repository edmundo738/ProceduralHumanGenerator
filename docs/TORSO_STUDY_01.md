# TORSO STUDY 01 — pescoço e tronco: peito, abdômen, costas, cinturas

**Identificação:** árvore atual (`51df6e2`), realistic_female seed 42, `HCG_HEAD=faceB2 HCG_NECK=N1`
(medição via `tools/refstudy/run_all.sh` com `HCG_BUILD_FROM_TREE=1`). Normalização do
estudo: 1700 mm, chão z=0, frente +Y. Instrumento: `tools/refstudy/` (REF01) +
`bust_band.py` + `render_torso.py` (novos). ANSUR II feminino = restrição
(p5–p95), não forma-alvo; refs = supervisão.

**Objetivo (uma pergunta):** que diferenças medíveis separam o nosso tronco/pescoço
das referências, e em que ordem as resolver?

## 1. Silhueta global (MEASURED)

IoU de silhueta frontal (caixa do tronco 560–1250 mm):

| caixa | ours vs refs | baseline ref↔ref |
|---|---|---|
| full (±235 mm, **confound da pose**) | 0.763–0.815 | 0.929 |
| **tronco (±150 mm, dentro dos braços)** | **0.880–0.923** | **0.949** |

Confound declarado: os nossos braços estão CAÍDOS junto ao corpo (x máx 0.26 m,
3196 verts ao lado do tronco) e as refs em T/A-pose — o IoU full mistura pose com
forma; o do tronco isola a forma. **Conclusão: a silhueta do tronco está abaixo da
variabilidade entre refs (0.88–0.92 vs 0.95) — diferença real, concentrada na cintura/ombros.**

## 2. Achados por região (MEASURED @1700 mm; refs = femalebase/femalechar/bodytopo)

### 2.1 Cintura — pouco marcada (o mais claro com as costas)
| métrica | ours | refs | ANSUR (p5–p95) |
|---|---|---|---|
| largura natural mínima | **288** | 212–220 (442†) | — |
| largura no omphalion | 328 | 272 / 228 | 264–372 |
| circunferência cintura | 914 | 666–728 | 750–1082 |
| cintura/nádegas (circ) | **0.904** | 0.719–0.811 | 0.842 (0.749–0.946) |

† bodytopo é base mesh em A-pose (sem valor anatômico para cintura). Tensão
declarada: as refs são mais "hourglass" que a média ANSUR; alvo = banda das refs
DENTRO dos limites ANSUR. A cintura existe mas o tronco é quase tubular.

### 2.2 Costas — sem curva em S (o mais claro)
| métrica | ours | refs |
|---|---|---|
| concavidade lombar | **19.5** | 53.7–69.7 |
| nádega vs costas torácicas | **+10** (nádega mais posterior) | −8 a −20 (costas mais posteriores) |
| costas altas vs occipital | **−38** | −2 a −22 |

O perfil sagital posterior é RETO: falta lordose lombar e o balanço cifose/nádega
das refs; as costas altas ficam recuadas vs occipital (liga ao CONT2/trapézio).

### 2.3 Peito — barril alto e largo; busto UNKNOWN nas refs
| métrica | ours | refs | ANSUR p5–p95 |
|---|---|---|---|
| largura do peito | **352** | 268–280 | 252–314 (**fora**) |
| profundidade do peito | **314** | 218–236 | 216–307 (**fora**) |
| circunferência | 1052 | 843–905 | 862–1145 |
| nível do máximo | 0.768·S | 0.735–0.747·S | (linha mamilar) |
| parede a 0.795·S (banda \|x\|<120) | **147** | 26–124 | — |

Busto (`bust_band.py`, banda central sem braços): ours ápice 0.768S com
projeção 49 mas saliência vs parede ~15 (a "projeção" é a inclinação do barril);
femalebase mama pequena (Δ17 @ 0.744S); **bodytopo sem mamas**; **femalechar: o
ponto mais anterior é a BARRIGA**. ⇒ **As refs atuais não dão um alvo de busto
consistente — UNKNOWN.** O peito atual é um barril torácico largo/profundo acima
do nível mamilar das refs, não um tórax + mamas.

### 2.4 Abdômen — ligeiro excesso frontal na linha média
abdomen_front − waist_front: ours +10 vs refs −2…+2 (belly_fixed −6 vs −8…+4, misto). Diferença pequena.

### 2.5 Pescoço — espesso (conhecido; caveats H1)
circunferência **417** vs refs 296–324 (394†) e ANSUR p95 382; profundidade
158 vs refs 98–108 (152†); largura 108 vs 92–100. O excesso é ântero-posterior
(base/trapézio — território H1; o máximo de 244 mm na base segue UNKNOWN, não
"corrigir" artificialmente). nape_recess 32 ✓.

### 2.6 Verificados ✓ (sem ação)
crotchheight 840 ✓; quadril: hipbreadth 392 (ANSUR 328–413 ✓), buttockdepth 262
(206–291 ✓); níveis: cintura 1100 ✓, nádega 940 ✓, pescoço 1485 ✓; coxa/panturrilha ✓.

## 3. Ranking (pior → menor)
1. **Costas sem curva S** (2.2) e **cintura pouco marcada** (2.1) — a silhueta frontal/lateral.
2. **Peito-barril** (2.3) — fora de ANSUR p95 em largura E profundidade.
3. **Busto** — UNKNOWN (refs inconsistentes; decisão do dono necessária).
4. **Pescoço-base espesso** (2.5) — integrar com CONT2 (nuca), caveat H1/244.
5. **Barriga** (2.4) — pequena; acompanha T1/T2.

## 4. PLANO — séries T (uma mudança estrutural por fase; pré-registo antes de medir)

| fase | mudança única | mecanismo (origem geométrica) | critérios congelados (congelar no pré-registo de cada fase) |
|---|---|---|---|
| **T1 COSTAS** | curva sagital em S | perfil `bs(z)` da linha média posterior (níveis fixos, média das refs) — continuidade C¹ como CONT1 | lombar ∈ [40,75]; nádega-vs-torácica ∈ [−25,−2]; costas altas-vs-occipital ∈ [−30,−8]; larguras/circ ±2 mm; fora da zona lombar/glútea inalterado |
| **T2 CINTURA** | definição da cintura | larguras das estações lombares do loft (estilo H3, alvo banda refs dentro de ANSUR) | largura natural ∈ [230,270]; cintura/nádegas ∈ [0.75,0.85]; quadril/peito inalterados |
| **T3 PEITO** | derreter o barril alto | redução da parede/profundidade torácica alta (fs/bs + estações) | largura ∈ [268,314]; profundidade ∈ [216,307]; parede 0.795S ≤ 120; circ ∈ ANSUR |
| **T4 BUSTO** | mamas como massa emergente | SUB-ESTUDO primeiro (refs atuais não servem) → campos tipo face-B | a definir no sub-estudo (nível 0.72–0.75S, projeção, underbust) |
| **T5 PESCOÇO-BASE + CONT2** | nuca→clavícula (com o pré-registo CONT2 já escrito) | anéis/pescoço inferior + trapézio, aprendido das refs | circ ≤ 382; N-C1 ≥ 15/18; critérios CONT2; caveat 244 UNKNOWN |

Ordem justificada: massa/perfil antes de features (como na cabeça: A→B); T1+T2
são o esqueleto da silhueta; o busto precisa de decisão do dono (refs novas ou
literatura já estudada); o pescoço fecha integrando com a nuca (CONT2).

## 5. Decisões pedidas ao dono
1. **Busto:** mandar 1–2 refs com busto modelado realista (ou aprovar o uso da
   literatura anatômica já estudada + femalebase como limite inferior)?
2. Confirmar a ordem T1→T5 (ou priorizar outra região primeiro).
3. Painel de renders `docs/head_phaseA/renders_T1_vs_refs.png` para leitura visual
   (frente/¾/lado/costas, mesma câmara; braços caídos vs T-pose declarado).

## 6. Avaliação
- **Minha avaliação:** o tronco é hoje a região mais distante das refs (IoU 0.88–0.92
  vs 0.95 entre refs; cabeça estava acima do baseline). Costas retas + cintura
  tubular + peito-barril explicam a leitura de "massa".
- **Concordo porque:** todas as diferenças têm medição em instrumento comum, com
  confounds (pose, ilhas, nível de corte) declarados.
- **Discordo de / riscos:** refs slim vs ANSUR (tensão declarada — não perseguir a
  magreira das refs cegamente); busto UNKNOWN; medidas no omphalian/linha mamilar
  dependem do nível (cotas fixas sempre); bodytopo sem pés/mamas (pesos menores).
- **Próximo passo que recomendo:** dono valida o painel + decide a questão do busto;
  depois pré-registo T1 (costas) e execução.
- **Por quê:** T1 é a fundação da silhueta e tem os critérios mais claros; o
  método exige uma mudança de cada vez com validação visual intercalada.
