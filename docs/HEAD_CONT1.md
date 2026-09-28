# CHECKPOINT CONT1 — ANATOMICAL CONTINUITY: estudo + orelha integrada (`HCG_HEAD=faceB2`)

**Identificação:** branch `arena/01a0d51d` · realistic_female · seed 42 · env `HCG_HEAD=faceB2 HCG_NECK=N1` · digests: oursF1 `e21378e3624e5765`, **oursF2 `b713d9489ecd8bb9`**.

**Objetivo (uma pergunta):** onde é que a nossa cabeça quebra a continuidade anatómica
(as "massas coladas") em relação às refs, e qual técnica de construção a elimina?

**Critério visual adotado (utilizador):** DISTÂNCIA (reconheço um humano?) +
PROXIMIDADE (as partes parecem do mesmo organismo?).  A F1 passou à distância;
este checkpoint ataca a proximidade.

## 1. Estudo medido (instrumento novo: `tools/headface/continuity.py`)

Secções planares (orelha h/v, órbita) + perfis de SILHUETA visível (nuca, mento),
κ = dθ/ds ao longo do arco (0.5 mm, suavização 2 mm), mm@H226, mesmas fontes:
oursN1/oursF1 vs bodytopo/femalebase/femalechar.  MEASURED (κ_p99 / turn):

| interface | oursF1 | refs (min–máx) | ours/refs | leitura |
|---|---|---|---|---|
| nuca (silhueta) | 0.102 / 146° | 0.033–0.099 / 71–103° | **1.8× / 1.6×** | pior excedente: "cabeça colocada no pescoço" |
| órbita canto lat. | 0.609 / 320° / conc 0.34 | 0.63–1.01 / 181–222° / conc 0.55–0.73 | κ ok / **turn 1.6×** | depressão difusa; refs têm rebordo DEFINIDO (conc alta) |
| orelha horizontal | 0.552 / 462° | 0.48–0.58 / 571–993° | κ ok / **turn 0.64×** | "placa": relevo em falta, não quinas |
| orelha vertical | 0.402 / 536° | 0.11–0.70 / 193–1355° | dentro | — |
| mento/garganta | 0.396 / 643° | 0.29–0.55 / 563–750° | ✓ | sem ação |

Envelope medido da orelha (secção z=92.5, `ear_envelope.npz`): pico médio das refs
~9–10 mm em y≈−25; nosso pico 13 mm em y=−33 (alto e recuado); ±10 mm de
variabilidade entre refs (a orelha é a estrutura mais variável — UNKNOWN parcial).

**Conclusão do estudo:** o defeito não é "peças más" — é o MECANISMO aditivo:
planaltos de bordo nítido (blob p=5) e depressões largas onde as refs concentram
a curvatura.  A nuca exige intervenção conjunta casco+pescoço (CONT2); a orelha
é autocontida e demonstra a técnica.

## 2. Pré-registo da intervenção (congelado antes de medir)

Substituir a orelha v1 (planalto p=5 + 5 campos + K) por **construção integrada**:
janela elíptica C¹ (smoothstep — valor e declive nulos no bordo) em (Y,V) ×
(colina-base recentrada no envelope medido + relevo interno reforçado), K mantido.
Fora da janela a contribuição é 0 EXATO.

- **PR1** turn orelha_h ∈ [500, 1000]° (alvo: gama das refs 571–993).
- **PR2** κ_p99 orelha_h ≤ 0.75 (≤ 1.2× média das refs).
- **PR3** fora da zona da orelha: máx |Δ| < 0.1 mm; nuca/mento/órbita inalterados.
- **PR4** critérios da fase A idênticos aos da F1 (a orelha está fora do domínio C1).
- **PR5** digests: default e todas as variantes anteriores inalterados.

## 3. Resultados (MEASURED)

| | oursF1 | **oursF2** | refs |
|---|---|---|---|
| PR1 turn orelha_h | 462° | **619°✓** | 571–993° |
| PR2 κ_p99 orelha_h | 0.552 | **0.614✓** | 0.478–0.583 (média 0.52) |
| PR3 máx Δ fora da orelha | — | **0.035 mm✓** (0 verts > 0.1 mm) | — |
| PR4 C1 / W1 / TR3 … | 2.12 / 153.18 / 63.58 | **idênticos✓ (8/8)** | — |
| PR5 digests | — | **F1 `e21378e3…` e todos os anteriores inalterados✓** | — |

Resultado intermédio registado (não escondido): suprimir o K na zona da orelha
BAIXOU o turn para 449° — o K (alinhado pelos marcos) carrega relevo real; foi
mantido.  Topologia: 34728 verts, 34716 faces (98,8% quads), 0 degeneradas.

## 4. Não incluído

Nuca/pescoço (CONT2, pré-registo abaixo), órbita (rebordo definido — CONT3),
corpo/pés, materiais/textura, cabelo.  Nada fora da zona da orelha mudou.

## 5. Pré-registo CONT2 (nuca — próxima)

A nuca mede κ 1.8× e turn 1.6× as refs: o casco fecha em "chávena" e o pescoço
(N1, calibrado) solda por cima.  Hipótese: dar ao quadrante póstero-inferior do
casco uma continuação do plano nucal com tangente casada com os anéis do pescoço
(janela C¹ como na orelha), revalidando N1 em seguida.  Critérios: κ_p99 nuca
≤ 1.2× média refs (≤ 0.075); turn ≤ 1.25× (≤ 115°); N-C1 ≥ 15/18 mantido; tudo
fora da zona nucal inalterado.

## 6. Avaliação

- **Minha avaliação:** a orelha passou de planalto com bordo a uma estrutura
  janelada C¹ com relevo na gama das refs (medido); a integração visual julga-se
  na evidência de proximidade (render close-up, sem cabelo) — OBSERVED a confirmar
  pelo utilizador.
- **Concordo porque:** os critérios PR1–PR5 foram congelados antes e passaram;
  o confinamento é exato (0.035 mm fora da zona).
- **Discordo de / riscos:** κ_p99 0.614 fica 1.18× a média das refs (dentro do
  pré-registo, mas no limite); o envelope da orelha tem ±10 mm de variabilidade
  entre refs (UNKNOWN — a "orelha média" não é uma orelha); o K mantém o caráter
  estatístico na orelha (declarado); não vejo os renders (sem visão) — a leitura
  de proximidade é do utilizador.
- **Próximo passo que recomendo:** CONT2 (nuca) com o pré-registo acima.
- **Por quê:** é o pior excedente medido e fecha a transição crânio→pescoço que
  o utilizador identificou como "cabeça encaixada".
