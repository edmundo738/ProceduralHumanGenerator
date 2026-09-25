# HEAD FASE A — resultados (contra o pré-registo congelado `HEAD_PHASE_A_PREREG.md`)

Build: realistic_female · seed 42 · `HCG_HEAD=massA` (cabeça nova) vs omissão (cabeça antiga).
Ferramentas: `tools/headfit/eval_phaseA.py` (mesmo instrumento HEAD STUDY 01 para todas as fontes),
`tools/headstudy/export_heads.py -- oursA`, `tools/render_views.py --face --neutral`.

## Mudança estrutural única
Representação da cabeça substituída: esfera com buracos + ilhas coladas →
**casca fechada cubo-esfera 6×24×24 (3456 quads) cujo raio é o modelo de massas R1**
(`generators/head_mass.py`, parâmetros = ajuste R1 ao alvo estatístico médio das refs,
`docs/head_phaseA/capacity_R1.json`). Sem olhos, boca, nariz, orelhas (fora da fase).
Atrás da flag `HCG_HEAD=massA`; omissão inalterada.

## Critérios (MEASURED, mm@H226)
| critério | antes | Fase A | alvo | |
|---|---|---|---|---|
| C1 RMS radial vs alvo L16 | 7.71 | 4.59 | ≤ 2.5 | **✗** |
| C2a largura/comprimento | 0.84 | 0.77 | 0.70–0.79 | ✓ |
| C2b g–op | 173.9 | 209.8 | 196–210 | ✓ |
| C2c W1 largura máx. | 145.9 | 160.7 | 141–156 | **✗** |
| C2d W3/W2 | 0.92 | 1.00 | ≥ 0.95 | ✓ |
| C2e W(0.10H)/W2 | 0.78 | 0.76 | 0.62–0.77 | ✓ |
| C2f S5 glabela | 86.4 | 104.9 | 95–107 | ✓ |
| C2g TR3 submental | 42.5 | 46.2 | ≥ 55 | **✗** |
| C3 vistas | — | — | juízo do utilizador | pendente |
| C4a pins/testes omissão | — | digest cb4e855996c2f1fd = pin; 133 pass/1 skip/1 xfail | inalterado | ✓ |
| C4b corpo bit-idêntico | — | 2898/2898 vértices | idêntico | ✓ |
| C4c casca | — | fechada, cada aresta 2×, orientação consistente, 100 % quads, 8 polos-3 | | ✓ |
| C4d determinismo | — | 2 builds e198b40a2831becf | | ✓ |

Refs no mesmo instrumento, C1: makehuman 4.80 · femalebase 4.02 · bodytopo 3.91 · femalechar 3.13
(o limiar 2.5 é mais exigente do que qualquer ref individual contra a média — FACT do quadro).

**Veredicto pelo pré-registo: FASE A NÃO PASSA** (C1, C2c, C2g falham). Não há reinterpretação de critérios.

## Origem das falhas (MEASURED → INFERRED)
1. Altura medida pela regra do mentón (tangente 45°, igual para todas as fontes) = **213.1 mm** vs 222.2 pretendidos.
   O modelo analítico tem o fundo do queixo no sítio certo (z ≈ −1.9 mm), mas o **queixo é arredondado**
   (união suave k = 8.7 mm): dy/dz ≈ 0.9 entre z 17 e 7 mm, sem canto queixo–plano submental. A regra marca o mentón ~9 mm acima.
2. A normalização por essa altura amplia a cabeça ~4.3 % → W1 155 → 160.7 (**C2c**) e ~4–5 mm de erro radial (**C1**).
   Diagnóstico (não é critério): normalizando pelo mentón pretendido, RMS = **1.73** (cage 1.69; contração da subdivisão 0.3 mm).
3. O mesmo queixo arredondado encurta o plano submental (**C2g**, 46 vs ≥ 55).
   ⇒ as três falhas têm **uma origem geométrica única: o canto mento–submental**.

No mundo (FACT ANSUR II fem. no repo, `docs/h1_trapezius/metrics_after.txt`: headlength 198 [184–213], headbreadth 154 [143–168]):
Fase A g–op ≈ 197.7 mm, largura ≈ 151.5 mm (INFERRED por reescala 213.1/226.1).

## Testes afectados com a flag (esperado; não alterados)
Com `HCG_HEAD=massA`: 6 falham — pins (3, cabeça substituída), F3/F4 (boca inexistente nesta fase),
F2 `head_depth` 206.9 mm vs constante 183 mm (mede extensão Y total incl. massa facial; a constante
diverge do próprio ANSUR 198 — conflito de definição a resolver na aprovação, não agora).
Corrigido nesta fase: a casca nova não registava anéis `skull.<k>` (contrato S3.7) → instrumentos J1–J5/F1 rebentavam; registo adicionado, J1–J5 e F1 passam.

## Visual (OBSERVED; C3 é do utilizador)
`docs/head_phaseA/views.png`, `profiles.png`, `renders_phaseA.png`.
- Perfil sagital acompanha o envelope das refs na testa, vértex e occipital; cabeça antiga ficava 15–25 mm atrás na testa.
- Lê-se como massa de cabeça única (sem ilhas/buracos), mas: massa facial é uma protuberância mole sem
  plano mandibular nem ângulo da mandíbula; queixo arredondado; junção nuca–pescoço com aresta visível
  (a casca intersecta o pescoço, não soldada — como a antiga); pescoço largo (UNKNOWN congelado) domina abaixo de z≈30.
- Risco de nomes: a "massa mentum" do R1 (z≈72) funciona como protuberância nasal/mediofacial e a "occipital" é o crânio principal —
  na Fase B as massas têm de ser ancoradas a marcos, não aos nomes.
- makehuman é outlier (mapa SH ruidoso, RMS próprio 3.84).

## Próxima hipótese (A2, uma só mudança, a pré-registar)
OBSERVED queixo arredondado → HYPOTHESIS: o canto mento–submental não é representável com união suave global k=8.7
e sem termo de marco; → TEST: raio de união local no mento **ou** termo de mentón/plano submental no ajuste R1 →
MEASURE com os mesmos C1–C4 congelados.

---
# Intervenção A2 / A2b (pré-registo `HEAD_PHASE_A2_PREREG.md`)

**A2 (corte por plano submental) — REFUTADA tal como implementada**: altura medida 213.1 → 213.1 mm.
Erro de referencial meu (medi a Fase A no referencial já deslocado pelo mentón); o canto estava
*subpreenchido*.  Emenda A2b escrita e enviada (3bf498f) **antes** de medir.

**A2b — união local com o envelope mentoniano médio de 3 refs** (frente do queixo + plano submental).
Flag `HCG_HEAD=massA2`; digest df0eb519fecb4bc3; massA continua e198b40a2831becf.

| critério (mm@H226) | antes | A | **A2b** | alvo | |
|---|---|---|---|---|---|
| C1 RMS radial | 7.71 | 4.59 | **2.16** | ≤ 2.5 | ✓ |
| C1 máx | 17.8 | 11.2 | 6.8 | — | |
| C2a L/C | 0.84 | 0.77 | 0.77 | 0.70–0.79 | ✓ |
| C2b g–op | 173.9 | 209.8 | 203.4 | 196–210 | ✓ |
| C2c W1 | 145.9 | 160.7 | **156.21** | 141–156 | **✗ (por 0.21)** |
| C2d W3/W2 | 0.92 | 1.00 | 1.00 | ≥ 0.95 | ✓ |
| C2e W0.10H/W2 | 0.78 | 0.76 | 0.76 | 0.62–0.77 | ✓ |
| C2f S5 | 86.4 | 104.9 | 101.7 | 95–107 | ✓ |
| C2g TR3 | 42.5 | 46.2 | **41.4** | ≥ 55 | **✗** |
| C4a–d | | ✓ | ✓ (omissão = pin; corpo 2898/2898; casca fechada 100 % quads 8 polos-3, área mín. 23.6 mm²; determinista) | | |

Previsões: P1 altura 213.1 → **219.8** (222 ± 3) ✓ · P2 recuo a −6 mm 9.9 → **40.0** (≥ 30) ✓ ·
P3 inclinação submental x=0 +13.7° → **+3.2°** ✓ (x=20: +12.1°, ainda acima das refs).
Testes com a flag: as mesmas 6 falhas esperadas da Fase A (pins ×3, F3/F4 boca inexistente, F2 constante histórica); nenhuma nova.

**Leitura pela regra registada: hipótese SUPORTADA (P1–P3 cumpridas; C1 passa; C2c melhora sem passar;
sem regressões C2a,b,d,e,f).  C2g piorou, como previsto: o ponto cervical é a frente do pescoço congelado
(y 40.5, z −11.7 vs refs y 5–25, z −37…−67) — causa registada: relação cabeça↔pescoço, não o queixo.**
C2c falha por 0.21 mm — não se arredonda; resíduo de escala (altura 219.8 vs 222.2 ⇒ ~1 % de ampliação).
**Fase A NÃO fecha** (C2c, C2g ✗; C3 não aprovado).

Visual (OBSERVED, `renders_A2b.png`, `views_A2b.png`, `profiles_A2b.png`): o queixo passa a ter canto
inferior e face submental plana (lado, ¾); a frente mostra a base do queixo mais definida.  Continua:
massa facial mole sem plano nem ângulo da mandíbula (gónio), faces laterais da face sem planos, e o
pescoço entra logo atrás do queixo — o submento visível é curto porque o pescoço ocupa esse espaço.
