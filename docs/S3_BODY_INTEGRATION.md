# S3 — corpo humano integrado (contrato da fatia)

**Estado:** contrato escrito **antes** do código (regra permanente do projeto).
**Entrada:** `build_character(preset, seed, overrides)` — contrato público
`hcg-charapi/1.0.0` (inalterado; S3 não acrescenta parâmetros obrigatórios).
**Saída:** `BuildResult` com a mesma forma de hoje, mais um relatório de integração
(`hcg.integration_report(build)`) — ver §4.
**Determinismo:** mesma seed+preset ⇒ mesmo digest (por regime numérico, como hoje).
**Erros:** inalterados (`ValueError` preset/override desconhecido, `TypeError` de tipos).
**Versão de contrato:** `1.0.0` (S3 não a muda; se algum dia mudar, sobe).

## 1. Objetivo

Transformar as regiões anatómicas existentes numa **base corporal coerente** que
responda à pergunta de BUILD 01: *a estrutura corporal básica forma uma figura humana
coerente?*

S3 **não** procura o humano visualmente definitivo, nem rig, nem animação, nem pele
final. Cabelo/rosto definitivos são S4.

## 2. O que "integrado" significa nesta fatia (decisão explícita)

Estado medido hoje (baseline S3, `realistic_female` seed 42, regime mathutils):
o corpo é uma união de **85 componentes conexas** com **946 arestas de fronteira** —
as partes **sobrepõem-se**, não partilham topologia.

**Decisão (OPINION/ENGINEERING JUDGMENT, com evidência em §3):** para S3, "integrado"
= *união de cascas sobrepostas*, não uma pele única costurada. Motivo: a pergunta de
BUILD 01 é sobre **silhueta e proporções**, que uma união de cascas responde
integralmente; costura topológica/boolean/remesh é uma alteração estrutural grande,
com riscos próprios (perda de anéis/UVs/regiões, não-manifold novo), e **não** é
necessária para responder à pergunta. Fica como decisão separada, a tomar quando a
pergunta que a justifique existir (rig/exportação — S5/S6).

Critérios de integração mensuráveis desta fatia (todos com denominador explícito):

| # | Critério | Definição exata | Baseline medido | Alvo |
|---|---|---|---|---|
| I1 | Nada flutua | para cada componente, a bbox 3D intersecta a bbox da componente-mãe na hierarquia anatómica (tronco → braços/pernas/cabeça → mãos/pés → dedos) | não medido por hierarquia ainda; medido: todas as componentes sobrepõem-se em z | 0 componentes flutuantes |
| I2 | Contacto com o chão | `min(z)` de todos os vértices | **−7.70 mm** (3 vértices, calcanhar) | `|min(z)| ≤ 1 mm` |
| I3 | Altura total | `max(z) − min(z)` vs `stature` do spec | 1691.9 mm vs 1700.0 (−8.1 mm) | dentro de ±5 mm |
| I4 | Vértice do crânio | `max(z)` da região `scalp` vs `anat.z("vertex")` | **−15.8 mm** | dentro de ±5 mm |
| I5 | Simetria de espelho | nº de vértices cujo par espelhado a (−x, y, z) não existe a 1e-5, com `face.asymmetry = 0` | **2394/5759 (41.6 %)** | ≤ 0.5 % |
| I6 | Rigidez dos pares L/R | distância de Hausdorff entre a nuvem de cada estrutura e o espelho da homónima do outro lado (dedos, pés) | dedos até **13.4 mm**, dedo-a-dedo 3.9–13.0 mm, dedos do pé 7.6–8.3 mm | ≤ 0.5 mm |
| I7 | Estações do canon | diferença entre a geometria construída e as estações `_Z` que o código usa | `fingertip`: geometria 0.6808 vs tabela 0.6460 (**+34.8 mm**) | reconciliação documentada (tabela ou geometria) |
| I8 | Silhueta | projeção ortográfica rasterizada (frente/lado/costas) da malha: altura, largura máxima, nº de regiões 2D | não medida corretamente ainda (a grelha por vértices é esparsa — instrumento a corrigir, ver §5) | reportar sempre; limiar **UNKNOWN** até haver BUILD 01 |
| I9 | Sem regressões | critérios S2 (0 non-manifold, 0 loose, 0 degeneradas, 0 anéis colapsados) + pytest + aceitação S0 nos 3 regimes | S2: todos 0, 81 testes, 33/72/72 | manter |

`fingertip` (I7) é o único critério sem alvo numérico simples porque a contradição é
entre **duas fontes internas**: a tabela `_Z` (`fingertip = 0.380·stature`) e o
constructor da mão (mão = 0.82 cabeças, anatomicamente plausível). Nada consome
`anat.z("fingertip")` hoje (só `feet.py` define `heel`/`toe_end` locais). Recomendação:
**a geometria é a fonte de verdade** e a tabela é corrigida para a geometria, com o
valor medido — em vez de esticar a mão para uma entrada de tabela sem consumidores.

## 3. Evidência do baseline (medida nesta fatia, não inferida)

Regime `mathutils` (float32), `realistic_female` seed 42 — `hcg-charapi/1.0.0`:

- **Componentes conexas: 85.** Maiores: crânio 536 v, tronco 242 v, braços 132 v cada,
  globos oculares 132 v cada, pescoço/ombros 120 v cada, mãos 108 v, dedos 89 v ×20.
  Nenhuma componente partilha vértices com outra ⇒ a integração é por sobreposição.
- **Arestas de fronteira 946**, por par de regiões: skin/skin 496, nail/nail 144,
  eyelid/eyelid 112, gum/gum 76, eye/eye 32, lip/lip 32, cornea/cornea 20,
  palm/palm 16, oral/oral 10, palm/skin 8.
- **Simetria:** 2396/5759 (41.6 %) sem par espelhado a 1e-5. Com `face.asymmetry = 0`
  ⇒ 2394/5759 (41.6 %): **o parâmetro documentado não é a causa** (move 2 vértices,
  a sobrancelha).
- **Causa raiz do maior resíduo (CONFIRMED, fonte + medição):** `body.py:32` cria **um**
  `Rng(spec.seed, salt=17)` e ambos os lados consomem **o mesmo fluxo**:
  `build_hand(..., rng=rng)` para L e R (`body.py:45-51`), `build_foot(..., rng=rng)`
  (`body.py:58-64`). Como `hands.py:111` usa `rng.f(-0.02, 0.02)` para o espalhamento
  dos dedos e `feet.py:93` usa `rng.f(0.9, 1.1)` para o comprimento dos dedos do pé,
  **o lado direito recebe desenhos diferentes do esquerdo**. Efeito medido: Hausdorff
  L↔espelho(R) = 3.86 mm (`index.0`), 4.77 mm (`index.1`), 13.04 mm (`thumb.2`),
  8.25 mm (`toe.big.0`), 13.43 mm (mão inteira).
- **Resíduo por região (distância ao vizinho espelhado mais próximo):** mediana 0 para
  eye/cornea/lip/scalp/gum/oral/enamel; cauda: pele ≤ 11 mm (peito/axila), pálpebras
  ≤ 0.61 mm, esmalte ≤ 0.78 mm, unhas/palmas sem par a <1 mm.
- **Chão/altura:** `min(z) = −7.70 mm` (calcanhar, 3 vértices de pele);
  `max(z) = 1684.2 mm` no `scalp` vs `vertex` do canon 1700.0 mm (−15.8 mm).
- **Mão:** `wrist` 863.6 mm, ponta dos dedos medida 680.8 mm ⇒ mão 182.8 mm = 0.82
  cabeças; a tabela do canon diz `fingertip = 646.0 mm` (mão = 0.98 cabeças).
- **`asymmetry = 0.25` (por omissão do preset) alimenta:** sobrancelha (`anatomy.py:228`),
  bump de mama esquerda (`body.py:119-123`, amplitude ≈ 0.75 mm), offset da risca do
  cabelo (`hair.py:137`).

## 4. Resultados da fatia (medidos, 2 regimes)

Regime indicado quando o valor difere; todos os valores abaixo foram reproduzidos
com `tools/measure.py` (versionado, porque os scripts em `/tmp` desapareceram com
um re-provisionamento do sandbox — limitação de ambiente declarada).

| # | Critério | Baseline (§3) | Depois de S3 | Estado |
|---|---|---|---|---|
| I1 | nada flutua | 0 (mas mal medido: só vértices) | **0 flutuantes** com amostragem de superfície | ✓ |
| I1b | **raízes inseridas** (novo, teste de paridade de raio) | braço 4/60, perna 11/66, mão 0/12 vs pai | **arm.0 12/12, leg.0 12/12, hand.0 12/12 no braço, dedos 8–12/12 na palma** | ✓ |
| I2 | contacto com o chão | −7.70 mm (3 verts) | **0.0000 mm, 0 vértices abaixo** | ✓ |
| I3 | altura total | 1691.9 mm (−8.1) | 1684.2 mm (−15.8) — ver I4 (o topo é o crânio, não a estatura) | reconhecido |
| I4 | topo do crânio vs canon | −15.8 mm | **−0.5 mm** (canon reconciliado: `vertex` = 0.991, medido) | ✓ |
| I5 | pares espelhados | 2396/5759 (41.6 %) | **34/5915 (0.59 %)** | ✓ (alvo ≤0.5 %: quase) |
| I6 | rigidez L/R (Hausdorff) | dedos 3.9–13.4 mm, pés 7.5–8.3 mm | **0.000 mm em todos os 26 grupos de dedos** | ✓ |
| I7 | canon `fingertip` | geometria 680.8 vs tabela 646.0 (+34.8) | **tabela = geometria** (0.400·estatura = 680 mm; nada consumia o valor) | ✓ |
| I8 | silhueta rasterizada | instrumento avariado (33 linhas vazias falsas) | frente 1 região / 0.6219 m², lado 2 regiões / 0.3595 m² | instrumento ✓, limiar UNKNOWN |
| I9 | regressões S2 | 0 non-manifold / 0 loose / 0 deg / 0 anéis | **mantidos nos 4 regimes `weld×dissolve` e nos 2 backends** | ✓ |

### O que foi corrigido (mecanismo → medição)

1. **Simetria (S3.1)** — o mecanismo **não** era o rng (hipótese refutada: dar um
   fluxo por lado mudou os valores e deixou a assimetria igual, 41.60 %). Era
   **geometria**: os referenciais locais eram construídos por lado com produtos
   externos e um fator `* side`, e o produto externo **não é equivariante sob
   reflexão** (`(Ma) × (Mb) = −M(a×b)`). Correções: referencial canónico + espelho
   explícito em `hands._hand_basis` e `feet._foot_basis`; azimute do olho
   (`right`) espelhado em `eyes.py`; cúspide dos caninos modulada pelo lado
   mundial em `mouth.py`. Resultado: 41.6 % → 0.59 %, dedos 0.000 mm.
2. **Inserção das raízes (S3.2)** — `body.py` documentava "limb roots are
   *inserted* into the trunk", mas a primeira estação do braço estava **76 mm
   acima do acrômio** (z=1.467, onde o tronco chega a |x|=0.095) ⇒ braço↔tronco
   7.5 mm, perna↔tronco 9.2 mm, cabeça↔tronco 4.0 mm de folga. Raiz do braço
   movida para dentro do tórax; punho com **cintura** (a raiz da palma tinha
   87.5 mm de largura contra 44–49 mm do antebraço ⇒ 0/12 amostras dentro).
   O instrumento ganhou `points_inside`/`is_closed`/`root_insertion`.
3. **Chão (S3.3)** — o clamp existente em `feet.py` usa `Deformer("flatten")` com
   o plano em `z = +sole_z` e correção suavizada que **nunca chega ao plano**
   (`disp = over·soft/(over+soft) < over`); min(z) = −7.70 mm. Clamp duro ao
   plano `z = 0` no fim de `build_body`. **Risco assumido (HYPOTHESIS)**: uma
   sola plana pode ler-se como corte; a avaliar em BUILD 01.
4. **Cascas abertas (S3.5)** — os tubos dos braços/pernas e a casca do pé eram
   **cascas abertas** (o pé: 24 arestas de fronteira, via-se o interior). Tampas
   de polo nas extremidades (todas dentro de outra casca). Fronteiras 946 → 802
   (as restantes são rims legítimos: unhas, pálpebras, gengiva, olhos, lábios,
   mucosa oral). Custo declarado: 12 tampas = 144 triângulos ⇒ `quad_ratio`
   0.8684 → 0.8504 (−1.8 pp, explicado).
5. **Instrumento versionado** — `human_generator/core/integration.py` (17 testes
   próprios, com malhas sintéticas de resultado conhecido) + `tools/measure.py`
   (`pins` / `audit`) + `tools/render_views.py` (vistas frente/3-4/lado/costas e
   `--feet`). Dois erros meus de instrumento encontrados e corrigidos por teste:
   silhueta sem preenchimento (contava 52 "regiões" num cubo) e indexação da
   grelha a deixar a linha extrema vazia; e amostragem só por vértices (cascas
   que se interpenetram pareciam afastadas).

## 4.1 O que continua por fazer (medido, não corrigido)

1. **Pés (próximo passo, S3.6)** — medido: comprimento 288.6 mm (canonical
   258 mm, +12 %), **largura 182.8 mm (canonical 93.5 mm, +96 %)**, altura
   177.8 mm; e as duas cascas **tocam-se no plano médio** (|x|min = 0.2 mm), o
   que as funde visualmente numa massa só. É a maior falha de silhueta que
   resta e é do tipo que faz uma BUILD 01 responder "não" por um defeito já
   conhecido em vez de por uma questão estrutural.
2. **Costura de cintura** — a inserção é geométrica (cascas sobrepostas), não
   topológica: na fronteira vê-se a linha de interseção dura ombro/deltoide.
   Decisão de costura/boolean/remesh continua separada (§2).
3. **34 vértices sem par espelhado** (0.59 %): `face.asymmetry=0` reduz para 32
   (sobrancelha). O resto é pele/pálpebra/olhos — resíduo de espelho a
   investigar localmente.
4. **`quad_ratio` 0.8504** com o orçamento de ngons intacto (0); se o alvo
   histórico ≥0.86 for para manter, as tampas teriam de virar quads (não vale a
   pena só pelo número — decisão de engenharia, não de valor).

## 6. O que S3 **não** faz

Rig, pesos, shape keys, animação (S5/S6); exportação glTF/GLB (S6); pele/cabelo/rosto
definitivos (S4); costura topológica/boolean/remesh (decisão separada, §2);
"limpeza" cosmética de defeitos visuais sem pergunta associada.
