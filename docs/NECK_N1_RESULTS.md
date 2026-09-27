# NECK N1 — resultados (contra `NECK_N1_PREREG.md`, congelado em e606e42)

Build: realistic_female · seed 42 · `HCG_HEAD=massA2 HCG_NECK=N1` · digest 214446515369c36b (builder, pure-python).
Mudança: só os parâmetros das estações trunk.2/trunk.3 (`core/anatomy.py`, `NECK_N1`), calibrados para os anéis finais
atingirem o perfil médio das 3 refs (`tools/headfit/neck_calib.py`, 1 iteração, erro 0.16 mm).
Declarado: o anel trunk.3 ficou em z −34.0 (antes −35.8; o campo do corpo depende da posição) — alvos do pré-registo mantidos.

| critério | A2b | A2b + N1 | alvo | |
|---|---|---|---|---|
| N-C1 perfil do pescoço dentro das refs (18 medições, tol 2 mm) | 2/18 | **15/18** | ≥ 15 | ✓ (no limite) |
| N-C2 = C2g TR3 submental | 41.4 | **61.5** | ≥ 55 | ✓ |
| N-C3 C1 RMS | 2.16 | 2.14 | ≤ 2.5 | ✓ |
| N-C3 C2a / b / d / f | ✓ | ✓ (0.77 / 203.4 / 1.00 / 101.7) | | ✓ |
| N-C3 C2e W(0.10H)/W2 | 0.76 | 0.71 | 0.62–0.77 | ✓ (passa a medir a mandíbula, não o pescoço) |
| C2c W1 (não é critério N1) | 156.21 | 156.21 | 141–156 | ✗ inalterado |
| N-C4 | | mesma contagem (6356) e faces; UV idênticos; alterados exactamente os 32 vértices de trunk.2/3; omissão = pin cb4e855996c2f1fd, 133/1/1; J1–J5 passam com as flags; determinista | | ✓ |
| N-C5 vistas | | `docs/head_phaseA/renders_N1.png`, `renders_N1_face.png` | juízo do utilizador | pendente |

Falhas N-C1 restantes: largura em z −10/−15/−20 = 60.4 / 63.1 / 67.4 vs máx. das refs 56 / 59 / 64 (+4 mm):
entre o anel +1.4 (48) e o anel −34 (75.7) o loft é linear; as refs mantêm a coluna estreita até −25 e só depois abrem
— com dois anéis a forma de "coluna + abertura" não é representável (INFERRED; exigiria mais estações ⇒ UV do tronco mudam).
Frente e trás: 12/12 dentro.

Risco registado confirmado: declive máx. da frente z −30…−65 1.66 → **2.03 mm/mm** (transição para o tórax congelado,
cuja frente está 70–85 mm à frente das refs).
Testes com as flags: as mesmas 6 falhas esperadas da cabeça (pins ×3, F3/F4 sem boca, F2 constante histórica).

OBSERVED (vistas): pescoço mais estreito e recuado; o bordo inferior da mandíbula e o submento passam a ver-se no lado e ¾;
a cabeça deixa de "assentar" num tubo tão largo como ela.  Continua: aresta visível na junção cabeça↔pescoço (cascas
não soldadas); a frente do tórax sobe cedo (degrau pescoço→peito mais marcado no lado); massa facial ainda macia.
