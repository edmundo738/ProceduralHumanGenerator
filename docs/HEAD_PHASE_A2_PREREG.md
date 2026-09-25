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
