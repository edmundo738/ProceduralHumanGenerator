# HEAD FACE F1 — massas faciais e traços (`HCG_HEAD=faceB`)

**Pré-registo (congelado antes de medir):** substituir a casca lisa de massas por uma
cabeça com forma facial humana — nariz, lábios, órbitas/pálpebras, orelhas — construída
proceduralmente, com as refs como supervisão (medição/alvo), nunca deformando uma malha
de ref. Uma pergunta: a forma de "massa" desaparece em avaliação neutra (sem cabelo,
sem materiais de beleza) e as métricas aproximam-se das refs?

## Conteúdo (o que mudou)

- `human_generator/generators/head_face.py` (novo): cabeça em três camadas sobre a
  mesma casca contínua A2b/N1 (`radial_cont_a2`):
  1. **campos anatómicos** (`face_fields.py`, novo): bolhas/cristas paramétricas em
     coordenadas (H, Y, V) com **limites de sinal** (narina [−4, 0], subnasal [−6, 0],
     ponta nasal [0, 20], asa nasal [0, 12], lábios [0, 8], estômio [−6, 0], órbita
     [−20, 0]) — o sinal impede "invenções" fora da direção anatómica;
  2. **modelo de olho**: globo (R 12,5), fenda com largura/altura medidas nas refs,
     pálpebras por `eye_blend` com janela cantal (evita estrias além do canto externo);
  3. **camada corretiva K** (`data/face_detail_v1.bin`): resíduo médio das 3 refs
     alinhadas (TPS + marcos, orelha incluída por protrusão > 2,5 mm), dessalmalcado
     (mediana 5×5, 1018 salpicos) e suavizado (σ 0,6), com taper na zona do olho.
- Orelhas: marcos de protrusão (topo/baixo/trás por lado) no TPS; campo gaussiano
  acrescenta a orelha à casca (o earfront é excluído — inconsistente entre refs).
- Globos oculares procedurais (esferas com polos triangulados) — ilhas próprias,
  descartadas na exportação de estudo (`common.load_raw`).
- `assemble.py`: envolvente `HCG_HEAD=faceB` (com `HCG_NECK=N1`).

## Não incluído

Cabelo, expressão, crânio novo (mantém A2b), F2, pescoço abaixo do N1, dentes/língua.

## Declaração de estatística (acordo)

Os campos são ajustados ao **alvo facial médio de 3 refs** (bodytopo, femalebase,
femalechar; **makehuman excluído**). A camada corretiva K é um **modelo estatístico**
das refs (43% do detalhe é explicado pelos campos com nome; K cobre o resto, RMS 0,98).
A altura da fenda palpebral trata a femalebase como outlier só nesta medida
(19,1 mm ≈ 2× a norma de Farkas; o laço dela inclui o rebordo do sulco — INFERRED).

## Evidência técnica (MEASURED, mm@H226)

| medida | A2b+N1 | **F1 (faceB+N1)** | alvo |
|---|---|---|---|
| C1 RMS radial vs alvo fase A | 2.14 | **2.12** | ≤ 2.5 |
| C1 máx |e| | 6.6 | **5.7** | — |
| W1 largura máxima (C2c) | 156.21 ✗ | **153.18 ✓** | 141–156 |
| R_cephalic / S7 / W3W2 / W0.10H / S5 / TR3 | ✓ | **todos ✓** | — |
| ajuste dos campos (RMS detalhe) | — | 1.28 (p90 1.54) | — |

Primeira versão com **8/8 critérios** (a C2c falhava por 0,21 desde a A2b).
Topologia: 34728 verts, 98,8% quads, 432 triângulos (polos dos globos), 0 degeneradas.
Digest oursF1 `e21378e3624e5765`; default e todas as variantes anteriores inalterados.

## Evidência visual

`renders_F1.png` (antes/depois, Cycles cinza neutro, sem cabelo — mesma câmara),
`views_F1.png` (rasterizador do estudo vs refs), `profiles_F1.png` (sagital/larguras).

## Avaliação

- **Minha avaliação:** a forma de massa desapareceu na frente e ¾; nariz, lábios,
  filtro, órbitas e orelha são legíveis como traços humanos (OBSERVED, renders neutros).
- **Concordo porque:** C1/max melhoraram, C2c entrou no intervalo e o ajuste aos
  marcos das refs é medido (não é impressão de render).
- **Discordo de / riscos:** a camada corretiva K é estatística de só 3 refs (risco de
  sobreajuste local); orelhas alinhadas só por 3 marcos; fenda da femalebase tratada
  como outlier numa medida (declarado); focinho/orelha ainda simplificados vs refs.
- **Próximo passo que recomendo:** congelar a F1 e avaliar a fase C (cavidades —
  narinas/escleral visível) sobre a mesma casca; só depois textura/material.
- **Por quê:** o acordo manda fase a fase com uma mudança estrutural de cada vez;
  cavidades têm de emergir da massa e não ser cortes.
