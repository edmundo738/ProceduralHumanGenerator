# S4 — Rosto e superfície (contrato da fatia)

Aberta depois de S3.8 (`b77d512`). Método obrigatório:
BASELINE → ALTERAÇÃO → TESTE → MEDIÇÃO → COMPARAÇÃO. Instrumento:
`core/integration.face_metrics` (novo em S4) + `tools/measure.py`.
Nenhum critério sem definição escrita e nenhum número sem classificação
(FACT / MEASURED / INFERRED).

## 1. O que foi observado e medido (baseline `b77d512`)

Observação (OBSERVED, render `out/s4_base/face/`): a cabeça é um **ovo**; as
orelhas são **placas soltas** (malha aberta em treliça, destacada do crânio); os
olhos são **duas saliências** sem abertura; os lábios formam uma **barra** que
atravessa o rosto de lado a lado. Não há sobrancelha, maçã do rosto, mandíbula
nem queixo legíveis.

Medição (`face_metrics`, `realistic_female`, seed 42):

| # | Medida | Baseline | Referência | Razão |
|---|---|---|---|---|
| 1 | largura do crânio (`head_breadth`, anéis `head.skull.*`) | **169.2 mm** | 144 mm | 1.18× |
| 2 | comprimento craniano (`head_depth`) | **223.1 mm** | 183 mm | 1.22× |
| 3 | largura da boca (região `lip` e marcos `mouth_corner.*`) | **130.9 mm** | 49.2 mm | **2.66×** |
| 4 | vermelhão superior / inferior | 3.2 / 5.1 mm (troca de rótulo: ver §7.1) | 6.5 / 10.0 mm | 0.5× |
| 5 | abertura ocular (região `eye`, X×Z por lado) | 20.8 × 22.5 mm | fissura 27–30 × 8–11 mm | sem fissura |
| 6 | distância interpupilar | 65.8 mm | 62 mm | 1.06× |
| 7 | comprimento do nariz (`nose_root`→`nose_tip`) | 48.9 mm | 45.3 mm | 1.08× |
| 8 | largura alar | **não medida** (região `nostril` vazia) | 31–35 mm | — |
| 9 | arco maxilar / mandibular (região `gum`) | 134.6 / 132.6 mm | 47.9 / 39.9 mm | 2.8× / 3.3× |
| 10 | orelha (comprimento, posição) | **não medida** (sem anel registado) | 58.0 mm | — |

Mecanismos (medidos no código):

* `anatomy.head_radii` devolvia `(0.3777·H, 0.50·H, 0.52·H)` — a largura e a
  profundidade do crânio não tinham fonte; davam 169.2 × 223.1 mm;
* `anatomy` punha as comissuras da boca a `0.0385·estatura` = 64.8 mm do centro
  (boca de 130 mm), e `mouth_aperture` escalava a **altura** do lábio com essa
  meia-largura (`0.030·half_w`);
* `add_ear` constrói uma **folha 6×8 de uma só camada** encostada ao elipsoide
  (sem hélice, sem concha, sem lóbulo, sem espessura) — no render lê-se como
  treliça; a orelha não tem anel registado, logo o instrumento não a identifica;
* `add_feature_loops` + campos dão os "olhos" como saliências: não existe
  abertura palpebral, o globo ocular (`generators/eyes.py`) fica atrás da pele;
* não há campo de sobrancelha, órbita, maçã do rosto, ângulo mandibular ou
  queixo com amplitude suficiente para ler como rosto (o `temple_pull` e o
  `squash_top` são as únicas correcções do elipsoide).

## 2. Valores canónicos — fonte e classificação

| Quantidade | Valor | Classificação |
|---|---|---|
| largura da cabeça, mulher p50 | **144 mm** | **FACT (fonte)**: FAA/DOT Ap. B (mulheres p50); 145 mm (British 19–65), 150 mm (Hong Kong) |
| comprimento craniano (glabela→opistocrânio), mulher | **183 mm** | **FACT (fonte)**: Norte da Índia 177.7 mm; Nigéria 183.9 mm |
| largura da boca (ch–ch), mulher | **49.2 mm** | **FACT (fonte)**: Indonesia 2023 (49.24 ± 6.06 mm); caucasiana 2024 (48.06 ± 3.34 mm) |
| vermelhão superior, mulher | **6.5 mm** | **FACT (fonte)**: Indonesia 6.59 ± 1.39; caucasiana 6.47 ± 1.36 |
| vermelhão inferior, mulher | **10.0–11.6 mm** | **FACT (fonte)**: Indonesia 10.02 ± 1.38; caucasiana 11.64 ± 1.46 |
| fissura palpebral | **27–30 mm × 8–11 mm** | **FACT (fonte)**: ScienceDirect/BCSC (25–30 × 8–10); chinês 27.1 mm (mulher) |
| distância interpupilar, mulher p50 | **62 mm** | **FACT (fonte)**: FAA/DOT Ap. B |
| comprimento do nariz (sellion→base), mulher | **45.3 mm** | **FACT (fonte)**: Turquia 2023 (45.28 ± 4.18 mm) |
| largura do nariz (alar), mulher | **31–35 mm** | **FACT (fonte)**: Irão 31.4 mm; Turquia 34.94 mm |
| comprimento da orelha, mulher | **58.0–58.7 mm** | **FACT (fonte)**: 58.70 ± 4.20 mm; 58.0 ± 3.7 mm; 58.1 ± 2.7 mm |
| largura da orelha | ≈ 0.55 × comprimento (32–34 mm) | **FACT (fonte)**: "width is 55 % of the length" (33.4 mm mulher) |
| topo da orelha ≈ nível da sobrancelha/olho; base ≈ base do nariz | — | **INFERRED** (relação anatómica clássica, sem fonte recolhida) |
| arco maxilar intermolar, mulher | **47.9 mm** | **FACT (fonte)**: Maharashtrian 2023 (47.90 ± 2.06); Egípcio 45.2 |
| arco maxilar intercanino, mulher | **34.3 mm** | **FACT (fonte)**: Maharashtrian 2023 (34.31 ± 1.75) |
| arco mandibular intermolar, mulher | **39.9 mm** | **FACT (fonte)**: 39.89 ± 2.48 mm |

Fontes recolhidas em 2026-09-24 por pesquisa; nenhuma foi extrapolada para além
do que a fonte diz. Onde não há fonte, o valor está marcado **INFERRED** com o
raciocínio declarado.

## 3. Critérios (definidos antes do código)

- **F1 largura do crânio**: `head_breadth` ∈ [0.93, 1.07] × 144 mm.
- **F2 comprimento craniano**: `head_depth` ∈ [0.93, 1.07] × 183 mm.
- **F3 boca**: `mouth_width` ∈ [0.88, 1.12] × 49.2 mm (malha e marcos coerentes
  entre si a < 2 mm).
- **F4 vermelhão**: superior ∈ [0.75, 1.35] × 6.5 mm; inferior ∈ [0.75, 1.30] ×
  10.0 mm.
- **F5 fissura palpebral**: por lado, largura ∈ [24, 32] mm e altura ∈ [7, 13] mm
  (banda que contém 27–30 × 8–11 e tolera o recorte da malha).
- **F6 interpupilar**: ∈ [0.94, 1.06] × 62 mm.
- **F7 nariz**: comprimento ∈ [0.88, 1.12] × 45.3 mm; largura alar ∈ [28, 38] mm.
- **F8 orelha**: comprimento ∈ [0.85, 1.15] × 58.0 mm; largura ∈ [0.85, 1.15] ×
  0.55·comprimento; topo ≥ nível do olho (≥ −5 mm); base ∈ base do nariz ± 8 mm;
  orelha **fechada** (sem fronteira aberta) e identificada por anel registado
  `head.ear.<lado>`.
- **F9 arcos dentários**: maxilar intermolar ∈ [0.90, 1.10] × 47.9 mm; maxilar
  intercanino ∈ [0.88, 1.12] × 34.3 mm; mandibular intermolar ∈ [0.90, 1.12] ×
  39.9 mm.
- **F10 regressões**: J1–J5 (S3.7) e H1–H7 (S3.8) verdes; grelha `weld×dissolve`
  × 2 regimes com 0 non-manifold / 0 loose / 0 degeneradas / 0 ngons; 0
  componentes flutuantes; chão exacto; S0 nos 3 regimes; pins re-medidos.

## 4. Sequência de sub-fatias (cada uma medida e commitada)

| Sub-fatia | Âmbito | Critérios |
|---|---|---|
| **S4.1** | proporções do crânio, boca, vermelhão | F1–F4, F10 |
| **S4.2** | **aberturas da cabeça** (pré-requisito medido em S4.1, ver §7.3): cortar a órbita, a boca e as narinas na casca do crânio | nova: ver §8 |
| **S4.2b** | olhos: globo, fissura palpebral, pálpebras (só fazem sentido depois das aberturas) | F5, F6 |
| **S4.3** | orelhas: aurícula fechada, hélice/concha/lóbulo, posição | F8 |
| **S4.4** | arcos dentários e dentes | F9 |
| **S4.5** | superfície: sobrancelha, órbita, maçã do rosto, mandíbula, queixo, nariz alar | F7 + observação |

## 5. Fora do âmbito

- **Cabelo**: a franja que tapa os olhos é defeito conhecido; S4.5 no máximo
  ajusta a linha de implantação; o sistema de fios não muda.
- **Pele/PBR**: materiais e shader não mudam nesta fatia.
- **Expressão**: `smile_rest` mantém-se; não há rig.
- **Costura topológica** crânio↔pescoço: decisão separada (S3.7 §5.1).

## 6. Resultado de S4.1 (medido)

Alterações (BASELINE → ALTERAÇÃO → MEDIÇÃO):

| Sítio | Antes | Depois | Efeito medido |
|---|---|---|---|
| `anatomy.head_radii` raio X | 0.3777·H (169.2 mm) | **0.3215·H** | 144.1 mm = **1.001×** os 144 mm canónicos |
| `anatomy.head_radii` raio Y | 0.50·H (223.1 mm) | **0.3917·H** | 185.1 mm = **1.011×** os 183 mm |
| `anatomy` comissuras da boca | 0.0385·estatura (boca 130.9 mm) | **0.0146·estatura** | 49.6 mm = **1.009×** os 49.2 mm |
| `anatomy` `eye_x` | 0.148·H (67.0 mm) | **0.1371·H** | 60.9 mm = 0.983× os 62 mm |
| `mouth.mouth_aperture` altura do lábio | proporcional à meia-largura | **absoluta** (0.0287·H, derivada do pico do arco de cupido) | vermelhão 6.4 / 10.0 mm = 0.98× / 1.00× |
| `head.build_head` correcção sagital | só para a frente (`need <= 0` saía) | **com sinal** | 108 das 160 colunas frontais deslocadas até −17.7 mm; a pele passa a estar exactamente na máscara facial (medido: 63.3 mm no marco do olho) |
| `anatomy` centro do globo | −0.032·H (7.2 mm dentro da pele) | **raio + 0.010·H** (12.3+2.3 mm) | globo deixa de sair 12.3 mm pela cara |
| `head` órbita | socket 0.0125·H, r 0.048·H | **0.0245·H, r 0.055·H + rebordo** | pálpebra passou de 4.9 mm dentro para 3.9 mm dentro; globo exposto 7 → 16 vértices |

Regressões (todas declaradas):

* `brow` (região e grupo) era 2 → 0 → **2** conforme as passagens; continua
  **frágil** porque a testa não tem anéis de vértices (o crânio `n=9` deixa
  ~50 mm entre anéis centrais) — §7.4.
* `scalp` 148 → **134**; `skin` 3086 → **3096** (+10) e `head.scalp` 148 → **134**:
  efeito directo das proporções novas do crânio (a máscara de couro cabeludo é
  geométrica).
* Contagens: **5951 v / 5932 f** (eram 5955/5936 — quatro faces degradadas a
  menos no `box_sphere` com os raios novos); `quad_ratio` 0.85131; grupos 57→58
  (`head.brow` voltou a 2 vértices); creases 426.
* **`palm` deixou de ser sensível ao regime** numérico: 62 vértices nos DOIS
  regimes (era 108 puro / 86 mathutils em S3.8). Não é uma correcção da questão
  de fundo (um predicado de região em cima de uma fronteira float32/float64);
  é um efeito colateral medido da nova geometria da mão. Registado.
* J1–J5 verdes: J1a **0.78** (era 0.664; sobe porque o crânio encolheu — o
  limite é 0.80), J1b 0.248, J1c 7.43, J2 1.180, H1–H6 verdes.
* Grelha `weld×dissolve` × 2 regimes: 0 non-manifold / 0 loose / 0 degeneradas /
  0 ngons, fronteira 802, `ops 0/0`. Pins re-medidos: digests
  `3f23485d4117c50a` (puro) / `cdd24607c7567e54` (mathutils). S0: 33/33, 72/72,
  72/72. pytest **128/1**.

## 7. Erros meus e achados desta fatia

1. **Instrumento com superior/inferior trocados**: `lip_vermilion.upper` media
   o lábio de baixo. Só descobri porque o valor (3.2 mm) contradizia a
   observação do render (lábio de cima fino mas não de 3 mm); corrigido e
   re-medido antes de qualquer decisão.
2. **Segunda medição inventada, travada pela primeira**: escrevi que o baseline
   tinha "3.2 / 5.1 mm" com base no instrumento trocado; a re-medição correcta
   deu 8.70 / 9.82 mm. A tabela do §1 fica com o valor re-medido e a nota da
   troca — o número errado fica registado, não apagado.
3. **A casca do crânio não tem aberturas.** Medido: o crânio é um elipsoide
   FECHADO (cube-sphere); não existe um único polígono removido na órbita, na
   boca ou nas narinas. Consequência medida: o globo ocular, as pálpebras
   (`eyelid`, 240 vértices) e os lábios estão todos **dentro** da pele — a
   pálpebra a 3.9 mm da superfície, o globo a expor 16 vértices (3.9 mm) contra
   a pele. Isto explica, sem hipótese, por que os olhos aparecem fechados no
   render e por que a boca se lê como uma barra: não há orifício para onde
   olhar. `add_feature_loops` já insere os anéis de retenção "para manter as
   aberturas nítidas sob Catmull-Clark", mas **a abertura nunca foi cortada**.
   Consequência de planeamento: S4.2 muda de conteúdo — primeiro as aberturas.
4. **A máscara `brow` é frágil por construção**: depende de um raio fixo
   (0.026·H) contra uma malha cuja densidade na testa é de ~50 mm entre anéis.
   2 vértices, 0 ou 4 conforme a passagem. Fica registado como débito técnico:
   a máscara certa é por coordenadas faciais, e isso exige anéis de testa.
5. **O nariz não é nariz**: `nose_length` 48.9 mm (1.079×) e `nose_protrusion`
   12.9 mm medidos, mas o que se vê é uma cunha que desce até à boca — o campo
   do nariz (`head.py` §5) empilha gaussianas ao longo de `nose_root→nose_tip`
   com sigma de 0.9·H em Z (203 mm!), o que arrasta a crista por metade da cara.
   Não corrigido nesta sub-fatia (é S4.5), mas medido e nomeado.
6. **Orelhas**: `add_ear` produz uma folha de uma camada, sem anéis registados
   (o instrumento devolve `None`), com face interior visível — a "treliça" do
   render. Continua exactamente como estava: S4.3.

## 8. Critérios revistos para S4.2 (aberturas) — definidos antes do código

- **A1 órbita aberta**: a casca do crânio tem de ter uma abertura por olho;
  medida como: nenhum vértice da casca dentro do cilindro do globo
  (raio do globo, eixo = eixo do olho) — hoje falha por construção.
- **A2 boca aberta**: a casca tem de ter uma abertura na região oral, e a
  abertura tem de ser **menor** que a boca de lábios (os lábios cobrem-na e
  fecham-na: 49.6 × ~6 mm de fenda).
- **A3 narinas abertas**: duas aberturas na base do nariz, separadas, com
  largura alar total ∈ [28, 38] mm (F7).
- **A4 nenhuma abertura pode deixar a malha aberta para o exterior**: as
  aberturas são *bordas* da casca e a fronteira da malha passa a incluir as
  novas 3 aberturas; o audit tem de a medir exactamente (o pin de fronteira
  802 mm deixa de valer e é re-derivado).
- **A5 regressões**: 0 non-manifold / 0 loose / 0 degeneradas / 0 ngons na grelha
  completa; J1–J5 e F1–F4 verdes.
