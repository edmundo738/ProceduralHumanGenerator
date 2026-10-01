# MECHANISM AUDIT 01 — porque a forma denuncia a construção (resposta ao gate SWEEP 01)

**Data:** 2026-10-01 · **Ciclo:** T-TORSO-2 · **Branch:** `arena/01a0d51d-proceduralhumangenerator`
**Input:** diagnóstico visual do dono/analista (OBSERVED, preservado em
SWEEP_01_BREAST.md §0): "linguagem de forma demasiado mecânica" — aba parabólica
nos ombros, tórax caixa suavizada, mama = linha/sombra (não volume), abdómen em
ondas, costas em lombas, glúteo triangular/"boca", cabeça inserida.
**Método:** nenhuma geometria mudada; cada OBSERVED foi levado ao mecanismo no
código e MEDIDO. Directriz cumprida: "não inventar a causa antes de verificar".

## 0. Resposta à pergunta crítica: porquê V0–V7 visualmente indistinguíveis

**MEASURED (perfis densos, instrumento comum, controlo negativo N0 = mama OFF):**

| variante | saliência mama (mm acima da parede nua) | Δmáx vs V0 (mm) |
|---|---|---|
| V0 baseline | 46.0 | — |
| V1 base larga | 56.0 | 12.0 |
| V2 gota | 48.0 | 6.0 |
| V3 sup. longa | 48.0 | 6.0 |
| V4 integrada | 48.0 | 6.0 |
| V5 lateral | 58.0 | 12.0 |
| V6 natural | 54.0 | 10.0 |
| V7 compacta | 42.0 | 6.0 |

- Os parâmetros **não foram anulados**: digests distintos (reproduzidos hoje),
  saliencias distintas. As diferenças são REAIS mas de **6–12 mm** numa superfície
  de ~440 mm — num tile de corpo inteiro (0.93 mm/px) = ≤13 px, e **na vista
  frontal a mama nem toca a silhueta** (o contorno está em x≈±155).
- Causa profunda: **nem sequer a V-max é uma mama legível** (ver §2) — diferenças
  entre "inchaços difusos" são ainda menos legíveis que o inchaço em si.
- **Confundidor cabelo ELIMINADO por medição**: o cabelo não desce abaixo de
  z≈1455 (comp. 41 = cabeça+cabelo, z 1455–1682); a "sombra horizontal" está no
  corpo (base do bump/inframamário), não é cabelo. Perfis do instrumento a z<1400
  não contaminados (verificado por componente: Δ=0.0 em todas as fatias).
- **Grelha abdominal ELIMINADA**: o código dos 6 bumps abdominais está INACTIVO
  (muscle_tone 0.45 < 0.55). As ondas do abdómen vêm das estações (§3).

**Falha do desenho do sweep (minha, declarada):** vary parâmetros de um mecanismo
que não produz a forma-alvo; zoom de corpo inteiro; sem controlo negativo.
Protocolo modo A corrigido: (1) sweeps incluem variantes de REPRESENTAÇÃO quando
a forma-base está em causa; (2) zoom à região (painel novo
`sweep_breast_zoom.png`); (3) controlo negativo + ref SEMPRE; (4) números Δ
publicados com cada folha. **Nenhuma variante promovida** (correcto).

## 1. Ombros: "aba/parábola/para-choques" — MEASURED na gaiola

Larguras das estações (dump da gaiola H-TT1, linha média):

```
z 1414  w 109   (pescoço, dentro do crânio — S3.7)
z 1406  w 142
z 1389  w 209
z 1383  w 219   (deltoid_line)
z 1368  w 188
z 1323  w 156   (peito)
```

**A largura passa 109→219 mm em ~32 mm de altura** = parede/aba. Nas refs, a
rampa do trapézio/clavícula distribui-se por 80–120 mm (R1 wiggle refs 9.89 vs
nosso 5.12; R2: real005 tem 6 extremos clavícula/deltoide/axila vs nosso 0).
Mecanismo: pescoço = tubo estreito com estações ESCONDIDAS no crânio (S3.7) +
rampa do trapézio em só 2 estações + salto na deltoid_line + braços como cascas
inseridas (as "extremidades pontiagudas" = raiz dos tubos dos braços a atravessar
a silhueta). **Correcção: H-TT5** — complexo clavícula/deltoide/axila como
região estruturada (estações intermédias z 1380–1440 com assimetria fs/bs e
re-ancoragem do deltoide).

## 2. Mama: "linha/sombra, não volume" — a representação é insuficiente (evidência para C)

- O bump é UMA gaussiana: amp·bust_protrusion (46–58 mm realizados) com
  σ=(48, 40, 55–65) mm — um inchaço difuso sobre uma parede já convexa.
- **Amplitude comparável às refs** (nossa saliência 46–58 mm; real005/femalebase
  15–23 mm no mesmo plano, c/ braços em T-pose a confundir a parede) — o que
  falta é FORMA, não tamanho: base mamária, ápice definido, teardrop, polo
  inferior, sulco inframamário (R5: refs 1–5 extremos vs nosso esboço).
- **Argumento de graus de liberdade:** a analista lista 9 características
  visíveis da mama (implantação, base, volume, orientação, transição superior,
  lateral, polo inferior, relação entre as duas, sulco). Uma gaussiana tem 4
  graus de liberdade + centro + direcção. **Não é calibração — é vocabulário.**
- Opções para o gate C (ver §6): mama por mini-loft de secções próprias
  (consistente com a arquitectura), ou volume primitivo (teardrop) fundido à
  parede com termo de sulco, ou campo de deslocamento com perfil assimétrico
  (transição superior longa / polo inferior curto + mínimo local = sulco).

## 3. Costas/abdómen: "lombas" e "ondas" — o zigzag das estações + planaltos PCHIP

- R9 lombar: **3 extremos vs 1 [1–1] das refs**; dois NAS estações (navel −2 mm,
  hip_flare +2 mm). R8: 3 extremos (z 1230, 1260, 1310): costas do busto (bs
  0.78) → dip → ápice da cifose (d 0.700·chest).
- Mecanismo: a sequência de profundidades das estações alterna (bust 0.670 / 
  cifose 0.740→0.700 / infra 0.540) e o PCHIP põe tangente NULA em cada extremo
  local → cada estação vira um planalto/lomba própria. As janelas sagitais
  (SACRAL/LOMBAR) acrescentam extremos próprios entre estações.
- Abdómen: mesma causa (navel/hip_flare) — grelha de "abs" verificada inactiva.
- **Correcção: H-TT2** (re-sequenciar profundidades/larguras por região para
  monotonia/uni-modalidade) + **H-TT4** (arquitectura sagital DENTRO do y das
  estações — uma só fonte de curvatura em vez de campo somado).

## 4. Glúteos: "triângulo/boca" — canal central por construção

- Lóbulos em ±0.60·hip_half = ±116 mm com σx 55 mm → no plano médio o peso é
  e^{−(116/55)²} ≈ 0.01: **nenhum lobo cobre o centro**; a janela sacral empurra
  a linha média para a frente; abaixo, as pernas separam-se. Resultado: canal
  central + dois lóbulos = "boca"/Pac-Man (sulco medido 0.2 mm vs refs 7–26).
- **Correcção:** massa glútea contínua — lóbulos com σx > 0.62·hip_half (cobrem
  o centro), sulco como prega RASA inferior (não canal), dobra inferior como
  transição para a coxa (H-TT6: junções).

## 5. Cabeça "inserida"

Cabeça = casca subsurf própria (comp 41) fundida ao pescoço na zona z≈1440–1460;
o N1 melhorou mas a junção ainda lê como inserção (o trapézio não continua para
dentro da casca da cabeça). Fila: T5/CONT2 (pré-registado).

## 6. Decisão C (representação) — evidência acumulada e opções

**Evidência:** §2 (mama: vocabulário insuficiente), §4 (glúteo: canal por
construção), §1 (ombro: rampa de 2 estações), §3 (zigzag + planaltos). O sistema
estações+PCHIP+gaussianas **representa bem**: proporções, níveis, balanço global,
cintura (o analista reconheceu a curva da cintura como aproveitável). **Não
representa:** formas com base/prega/ápice próprios (mama, glúteo, ombro).

| opção | descrição | custo | risco |
|---|---|---|---|
| C1 | refinamento contínuo do actual (H-TT2/4/5/6) | baixo | tecto: "humanoide suave" — a mama/glúteo continuam gaussianas |
| C2 | híbrido: estações para o corpo + **volumes próprios** (mini-lofts/primitivos fundidos) para mama, glúteo, ombro | médio | integração/arestas — exige junções cuidadas |
| C3 | re-construção por camadas anatómicas (gaiola torácica/pelve como objectos, superfície derivada) | alto | recomeço parcial — contra a directriz "não recomeçar" |

**Recomendação (para gate do dono): C2** — preserva o que funciona (directriz),
substitui só os mecanismos que "demonstradamente produzem a aparência artificial"
(§2/§4 — a linguagem de forma do dono). A mama em C2: mini-loft de 3–4 secções
teardrop com base na parede + sulco inframamário como mínimo local.

## 7. Proveniência

Medições: perfis measure.py por variante (prof_sw*.json, instrumento comum);
dump da gaiola (anéis registados); componentes geom.py; presets (muscle_tone
0.45). Render zoom: `docs/head_phaseA/sweep_breast_zoom.png` (janela 620 mm,
câmara idêntica, N0/V0/V5/V6/V7 + refs). Nenhuma alteração de geometria.
