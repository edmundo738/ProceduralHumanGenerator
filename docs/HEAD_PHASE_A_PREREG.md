# HEAD FASE A — pré-registo (1 página, congelado antes de implementar)

**Base:** `caf5d00` (gerador igual a `df03e98`). **Congelado em:** commit deste ficheiro. Nada abaixo muda depois de medir.

## 1. Objetivo

Crânio + silhueta + volume geral da cabeça, **sem traços**: sem olhos, boca, nariz nem orelhas.

Pergunta a responder: *Isto já parece uma cabeça humana antes de pormos os detalhes?*

## 2. Evidência que motiva a fase (já medida, `docs/head_phaseA/`)

- **Teste de capacidade.** A representação atual (elipsoide + máscara frontal), com **todos** os parâmetros livres e ajuste ótimo, fica em RMS 3.75 mm (máx. 14.3) contra o alvo. Só o consegue distorcendo a anatomia: largura 162 mm (refs 145–159) e mandíbula 77 mm (refs 86–114). Ajustada a uma cabeça real individual, fica em RMS 3.5–6.7 mm.
  **Conclusão: a representação é inadequada.** Não se continua a afinar.
- **R1 (massas).** Com o mesmo alvo e o mesmo domínio: RMS 1.35 mm (máx. 3.9), dimensões dentro das refs, e RMS 0.6–1.2 mm ajustada a refs individuais.

## 3. Alteração: UMA mudança estrutural

A casca da cabeça passa a ser construída por **R1**:

- união suave, em distância radial, de 6 massas: abóbada, frontal, occipital, face média, mandíbula, mento;
- os parâmetros vêm do ajuste ao **alvo estatístico** (média SH grau 16 de makehuman, femalebase, bodytopo e femalechar, normalizadas a H);
- malha nova: grelha cube-sphere equiangular de quads, 24×24 por face;
- em Python puro (o gerador não usa numpy);
- ativa só com `HCG_HEAD=massA`. A build por omissão, o spec, a fingerprint e os pins **ficam inalterados**.

No modo massA não há olhos, boca, narinas, orelhas nem campos de traços, e os geradores de olhos e boca não correm.

## 4. Métricas e critérios de passagem (instrumento HEAD STUDY 01 + `tools/headfit`)

Todos os critérios são sobre a malha suave (Subdivision 2) exportada pelo mesmo `export_heads.py`.

| # | métrica | atual | critério |
|---|---|---|---|
| C1 | RMS radial vs alvo (L16, domínio comum) | 7.63 mm | **≤ 2.5 mm** (e abaixo do melhor ref, 3.1) |
| C2a | largura/comprimento | 0.84 | **0.70 – 0.79** (ANSUR 0.78) |
| C2b | comprimento g–op (S7) | 173.9 | **196 – 210** |
| C2c | largura máxima (W1) | 145.9 | **141 – 156** |
| C2d | frontal mín./face anterior (W3/W2) | 0.92 | **≥ 0.95** |
| C2e | W(0.10·H)/W2 | 0.78 | **0.62 – 0.77** |
| C2f | glabela à frente do centro (S5) | 86.4 | **95 – 107** |
| C2g | comprimento submental (TR3) | 42.5 | **≥ 55** |
| C3 | vistas neutras frente, lado, ¾, costas | — | leitura de cabeça humana sem traços: julgamento **do utilizador**; eu registo o que OBSERVO, sem me dar por aprovado |
| C4a | build por omissão | — | digest e pins **inalterados** (testes pytest + S0 72/72) |
| C4b | corpo fora da cabeça (massA vs omissão) | — | vértices **bit-idênticos** |
| C4c | integridade da casca | — | fechada, manifold, 0 faces degeneradas, 100 % quads, polos só nos 8 cantos do cubo |
| C4d | determinismo | — | 2 builds massA dão o mesmo digest |

**Não se medem nesta fase** (não existem traços): pronasale, nasion, estómio, órbita, lábios. Essas métricas passam às fases seguintes.

## 5. Regras

- Se C1 ou C2 falharem, documenta-se a falha e a sua origem. **Não se afinam constantes às cegas.** Qualquer correção passa a ser nova hipótese.
- O resto do corpo fica congelado. O pescoço grosso (244 mm, UNKNOWN) não se toca.
- A transição cabeça → pescoço é observada e reportada; o pescoço não se altera.
