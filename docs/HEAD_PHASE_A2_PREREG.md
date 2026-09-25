# HEAD FASE A — intervenção A2 (pré-registo, congelado antes de medir)

**Hipótese.** O arredondamento excessivo da região mentoniana (sem canto mento–submental,
face inferior a descer para trás) é uma causa comum das falhas C1, C2c e C2g da Fase A.

**Observado que a motiva (MEASURED, `tools/headfit/chin_study.py`, malhas brutas, mm@H226, mentón 45°):**
| | plano sob o mentón x=0/10/20 | inclinação (desce p/ trás) | recuo 6 mm abaixo do mentón |
|---|---|---|---|
| femalebase | −2.7 / −2.3 / +1.2 | +7.3° | 36.7 |
| bodytopo | −2.0 / −1.5 / +1.0 | −6.0° | 54.9 |
| femalechar | −5.7 / −4.6 / +2.1 | −5.9° | 48.3 |
| Fase A | −3.7 / −2.6 / +1.8 | **+13.7°** | **9.9** |

makehuman excluído deste estudo (medido: a regra dos 45° coloca-lhe o mentón já no submento —
y_me 61.6 vs pogónio 104.4; o perfil em z=0 já recuou para 49).  Decisão tomada antes de medir A2.

**Mudança única.** Um plano submental aprendido das 3 refs limita a casca por baixo, com canto de
concordância local:  r_A2(u) = smin(r_A(u), r_plano(u), k_c), smin polinomial (exactamente local:
|r_A − r_plano| ≥ k_c ⇒ nada muda).  Plano: z = a0 + c·min(|x|, 20)²,
a0 = −3.5 mm (média x=0), c = 0.01225 (sobe até +1.4 em x=20; mantém-se além — não se extrapola),
horizontal em y (inclinação média das 3 refs −1.5°, dentro do ruído ±7° → 0).
k_c = 4 mm (ENGINEERING JUDGMENT: ordem do recuo a 3 mm nas refs de canto nítido, 3.5–4.0).
Nada mais muda: massas R1, união k, largura, crânio, testa, têmporas, mapeamento para o mundo,
corpo, pescoço.  Flag `HCG_HEAD=massA2` (A continua reproduzível com `massA`).

**Critérios: os mesmos C1–C4 de `HEAD_PHASE_A_PREREG.md`, sem alteração.**
Vistas, seed 42, normalização, instrumento: os mesmos.

**Previsões registadas (para julgar a hipótese, não para passar):**
- P1 altura pela regra do mentón: 213.1 → 222 ± 3 mm (mundo).
- P2 recuo 6 mm abaixo do mentón: 9.9 → ≥ 30.   P3 inclinação submental: +13.7° → entre −7° e +7°.
- C1 e C2c: devem melhorar (diagnóstico da Fase A: RMS 1.73 com o mentón pretendido); C2a,b,d,e,f não podem sair do intervalo.
- **C2g (TR3) depende do pescoço congelado**: o ponto cervical da nossa build é a frente do pescoço
  (y ≈ 42 contra 5–25 nas refs), a argmin de um perfil quase constante — espera-se que A2 **não**
  resolva C2g; se falhar, a causa registada é a relação cabeça↔pescoço, não o queixo.

**Leitura.** Hipótese SUPORTADA se P1–P3 se cumprirem e C1/C2c melhorarem sem regressões; PARCIAL se
só parte; REFUTADA se P1 não se mover.  A Fase A só fecha com C3 aprovado pelo utilizador —
números a passar não bastam.

---
## Resultado A2 tal como registada + emenda A2b (escrita ANTES de medir A2b)

**A2 (plano por baixo, smin) — MEASURED:** altura pela regra do mentón 213.1 → **213.1 mm** (P1 falha).
**REFUTADA tal como implementada.**  Origem (MEASURED, perfil analítico do modelo no seu próprio
referencial, z = 0 = mentón do alvo): a face inferior do modelo já está a z −1.9…0, *acima* do plano
(−3.5) — o plano não corta nada.  O "submento a descer 14°" vinha de ter medido a Fase A no
referencial normalizado, que já está deslocado ~9 mm pelo próprio mentón mal colocado (erro meu de
referencial, declarado).  Mesmo referencial, x = 0:
| z | 17 | 7 | 1 |
|---|---|---|---|
| modelo A, y | 90 | 80 | 67 |
| 3 refs (média), y | ~85 | 83.5 | 80.6 |
⇒ o canto está **subpreenchido** (~13 mm para dentro em z ≈ 1), não em excesso.  A hipótese (o
arredondamento mentoniano é a causa comum) mantém-se; o mecanismo tinha o sinal errado.

**Emenda A2b — mudança única (substitui A2; A2 sai):** união local com o **envelope mentoniano médio
das 3 refs**: bloco = { sub_z(x) ≤ z ≤ 15 mm, 0 ≤ y ≤ Yf(x, z) }, Yf = tabela média medida da frente
do queixo (`out/headfit/chin_front.npz`, z −1…15 de 2 em 2, |x| 0…40 de 4 em 4, interpolação bilinear;
fora da tabela o bloco não existe), sub_z(x) = plano submental da A2 (face inferior do bloco).
r_A2b(u) = smax(r_A(u), r_bloco(u), k_c = 4 mm), smax polinomial (local: só acrescenta onde o envelope
das refs sai para fora da casca A).  Tabela (y, colunas x = 0, 8, 16, 24, 32):
z −1: 78.8 77.4 54.8 33.8 13.1 · z 1: 80.6 79.5 73.7 36.5 15.8 · z 5: 82.8 81.8 77.6 52.0 30.9 ·
z 9: 84.0 83.0 79.4 72.2 44.6 · z 15: 84.9 83.9 80.9 75.3 65.6 (sd entre refs em x=0 ≈ 11 mm).
Critérios C1–C4, previsões P1–P3 e regra de leitura: **inalterados**.  Flag `HCG_HEAD=massA2`.
