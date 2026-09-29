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

## 7. T1 COSTAS — execução (MEASURED 2026-09-29)

**Proveniência (registo honesto):** a T1 foi executada e fechada a 2026-09-29
(commit `c8ee4ce`), mas o push falhou (token GitHub inválido) e o sandbox foi
recriado antes do reenvio — o commit perdeu-se. A 1.ª reconstrução
(`837b69b`+site) perdeu-se da mesma forma (2.º reset do sandbox). Esta é a
**2.ª reconstrução**: `back_curve.py` re-escrito da especificação pré-registada
(§4) e das constantes calibradas registadas, depois verificado
**digest-a-digest** contra os pins medidos na 1.ª passagem (idênticos —
`49fcc725984aec75` pure / `e9692d34c0dde938` mathutils) e com as medições
A/B reproduzidas à casa decimal onde registadas.

**Mecanismo (uma mudança estrutural, como pré-registado):**
`generators/back_curve.py` — três janelas C¹ do perfil sagital posterior
(sacro `z∈[.4982,.6000]·S` pico `.55`, lombar `[.6035,.6928]` pico `.6434`,
costas altas `[.7663,.8263]` platô `.7972`; cotas em fração da estatura
NOMINAL × `_K=0.98965`), amplitudes `.024/.0235/.0282·S` para +y (anterior),
com cauda lateral por janela (sacro: planalto |x|≤`.0233·S` até zero em
`.0466·S` — gaussiana estreita morre no Catmull-Clark; lombar/altas:
gaussiana σx `.0524/.0233·S`) e peso angular y (só a face posterior do anel;
frente e larguras intocadas por construção). `subdivide_rings` insere **+10
anéis** interpolados LINEARMENTE EM PONTOS nas zonas da curva (+160 verts/
faces; interpolar parâmetros incha os cantos +18 mm — medido); `apply_sagittal_back`
aplica o campo aos anéis `trunk.k` DEPOIS do DeformStack. Instrumento A/B:
`HCG_T1_AMP=0` desliga só o campo (topologia idêntica).

**Resultado A/B (amp0→amp1, mesma topologia, subsurf nível 1, @1700 mm):**

| métrica (banda §4) | amp0 | amp1 | original `c8ee4ce` | veredicto |
|---|---|---|---|---|
| concavidade lombar ∈ [40,75] | 26.9 | **45.3** ✓ | 45.3 ✓ | idêntico ao original |
| nádega−vs−torácica ∈ [−25,−2] | +12.0 | **−6.0** ✓ | −6.0 ✓ | idêntico ao original |
| costas altas−vs−occipital ∈ [−30,−8] | −38.0 | **−26.0** ✓ | −32 ✗ (2 mm) | **reconstrução DENTRO** |
| larguras peito/cintura/quadril (Δ±2) | — | **Δ0.0** ✓ | Δ0.0 ✓ | exacto |
| circ cintura (±2) | 920.1 | −0.9 ✓ | −1.9 ✓ | |
| circ peito (±2) | 1051.7 | −1.4 ✓ | −6.0 ✗ declarado | reconstrução dentro |
| circ nádegas | 1025.4 | −6.4 | −5.1 declarado | efeito declarado (abaixo) |
| circ pescoço | 417.2 | +0.3 | +0.7 | |
| crotchheight | 840 | Δ0.0 | Δ0.0 | |

Perfil sagital posterior (linha média, controlo): lombar **−107**@1100
(amp0 −131), sacro **−149**@920 (−163), altas **−133**@1360 (−147); ápices:
nádega 920→915, lombar 1085→1110, torácico 1305→1265. IoU do painel
(`renders_T1_vs_refs.png`, com **real005**): lado 0.67–0.75 (ref↔ref 0.69);
frente 0.63–0.66 com o artefacto de centrado-y por caixa declarado no
original (a frente não é tocada pelo campo).

## 7.1 Validação do dono e decisão

**VALIDAÇÃO DO DONO (2026-09-29): NEGATIVA, provisória — "acho que não
gostei do resultado das costas no momento".** A T1 fica em **CHECKPOINT**
(código + medições + variante do site), **NÃO fechada**:

- As três bandas §4 estão cumpridas (medição objectiva), mas a leitura
  visual do dono manda — a métrica não captura tudo (ex.: leitura de
  "gibosidade" no sacro/ilíaca, transições, quão harmónica a curva parece).
- **Próximo passo:** o dono diz O QUE lê mal (sacro saliente? lombar
  exagerada? costas altas recuada a mais? transições duras?) e re-ajustam-se
  as janelas/amplitudes DENTRO do mesmo mecanismo; `HCG_T1_AMP=0` reverte o
  default se preferir voltar ao perfil recto enquanto isso.
- **T2 não parte daqui sem re-decisão** (método: uma mudança de cada vez,
  validação intercalada).

Efeitos estruturais conhecidos (mantêm-se declarados): o campo achata o
BLOCO central glúteo (contorno posterior 910–950 = −163..−165 em |x|≤60 com
mínimo NO CENTRO; refs têm lóbulos laterais + sulco) ⇒ circ nádegas −6.4 —
lóbulos continuam **pré-requisito T4**; confundidor occipital nosso −99 vs
refs −139/−145 (liga a T5/CONT2).

## 7.2 Notas de instrumento (reconstrução)

- A comparação correcta é **amp0 vs amp1** (mesma topologia). amp0 vs baseline
  mistura artefactos de amostragem dos novos anéis.
- A medição avalia o **subsurf nível 1**: o pad sacral realiza ~0.5 da
  amplitude (Catmull-Clark) — daí o planalto lateral; a lombar (σx largo)
  realiza ~0.85.
- O instrumento **re-centra Y pela caixa** (mín/máx da malha mantida): quando
  o mínimo posterior (nádega) avança, o frame inteiro desloca ~Δ/2 — as zonas
  não tocadas "recuam" na leitura. Artefacto declarado; as métricas relativas
  (t−b) compensam-no.
- Constantes lidas dinamicamente (`_amp()`) para variantes coexistirem no
  mesmo processo (export do site); janelas em fração ×_K (a malha realiza
  1.6824 m para 1.7 nominal — sem o ×_K as janelas deslocam 1%).
- **Refs novas (REF-F-REAL-005/006):** real005 (T-pose, pele nua
  `Std_Skin_*` = 14474 v) ADMITIDA como supervisão — lombar **56.2** ✓ banda
  refs, nádega-vs-torácica −8 ✓, hipbreadth 328 ✓. real006 (MOLLY, 26435 v)
  **EXCLUÍDA**: estilizada (lombar 1.4; hipbreadth 640 > p95+230).
- Orientação de refs: a heurística "pés" engana (a banda z<16% inclui a
  canela); a decisão de flip foi VALIDADA pela medição sagital (frente errada
  ⇒ lombar ~4 com a barriga atrás; certa ⇒ 56.2 na banda).
- **Lições de processo (2 perdas):** commitar E fazer push no mesmo passo;
  nunca terminar um turno com commits não sincronizados.
