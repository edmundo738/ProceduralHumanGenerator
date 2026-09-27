# HEAD FASE A — estudo A3 (mandíbula lateral/ângulo) — resultado: intervenção A3 NÃO suportada

Ferramentas: `tools/headfit/jaw_study.py`, `tools/headfit/jaw_coronal.py`; figuras `docs/head_phaseA/jaw_study.png`,
`jaw_coronal.png`, `err_A2b.png`.  Referencial mm@H226, z = 0 mentón 45°, y = 0 centro g–op.  Build A2b (`HCG_HEAD=massA2`).

## 1. A metade anterior do terço inferior já coincide com as refs (OBSERVED, cortes coronais)
Em y = 35, 50, 65 a casca A2b fica sobre femalebase/bodytopo/femalechar (paredes laterais e fundo).

## 2. Erro por região vs alvo (MEASURED) — todas abaixo da variação entre refs
| região | RMS A2b | desvio médio | sd entre refs |
|---|---|---|---|
| face | 2.26 | +1.27 | 5.04 |
| testa | 1.17 | +0.30 | 2.32 |
| topo | 0.98 | +0.17 | 1.59 |
| lateral | 2.81 | +1.79 | 4.38 |
| occipital | 2.55 | +2.14 | 3.04 |
| mandíbula (z<50, |x|>25) | 2.62 | +1.62 | 5.48 |
Resíduo dominante: desvio uniforme ≈ +1.5 mm = escala ~1 % (altura medida 219.8 vs 222.2) — a mesma causa de C2c (156.21).

## 3. O que falta no terço inferior vem do pescoço do corpo (MEASURED, secção 20 mm abaixo do mentón)
| | centro | frente | trás | profundidade | meia-largura |
|---|---|---|---|---|---|
| refs (média 3) | −29 | 20 (9–32) | −79 | 99 | 54 |
| nosso pescoço | −21 | 42 | −84 | 126 | 81 |
O tubo do pescoço sobe por dentro da cabeça (±52 mm) e, abaixo de z ≈ 25, é mais largo do que a mandíbula da cabeça:
o bordo inferior e o ângulo ficam dentro do pescoço.  O pescoço abre para os ombros logo abaixo do mentón (refs: 40–60 mm de pescoço vertical).
Mover a cabeça em y não resolve (INFERRED): corrigiria o centro (+8 mm) mas pioraria a nuca (−92 vs −79); o pescoço é mais **grosso**, não só deslocado.
⇒ Relação com a regra do utilizador: o pescoço grosso está UNKNOWN e não se corrige artificialmente nesta fase — não foi alterado.

## 4. Porque ainda "lê como manequim" (INFERRED / HYPOTHESIS)
O alvo é a **média** SH L16 de 4 refs: planos e arestas (ângulo da mandíbula, zigomático, planos laterais) ficam em posições
diferentes em cada ref e **a média alisa-os**; L16 também (≈ 20 mm de comprimento de onda).  Uma forma dentro da variação da
média é, por construção, macia.  HYPOTHESIS para a Fase B: os planos/arestas faciais têm de vir de marcos alinhados por ref
(gónio, zigomático, bordo mandibular) e de estatística de marcos, não do mapa radial médio.

## Conclusão
A3 (mandíbula só na cabeça) não é suportada pela medição: onde é visível já coincide; onde não coincide está escondida pelo pescoço.
Nada foi alterado no gerador nesta etapa.
