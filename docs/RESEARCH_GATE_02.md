# RESEARCH GATE 02 — Segunda auditoria: afirmações × código real × medições

**Data:** 2026-09-24 (mesma sessão do Gate 01) · **Branch:** `arena/01a0d308-proceduralhumangenerator`
**Método:** cada afirmação foi confrontada com (a) `git log --all`, (b) leitura do código-fonte, (c) medição em execução headless (bpy 5.0.1). Zero implementação — apenas diagnóstico.
**Regra seguida:** nenhuma afirmação abaixo é apresentada como CONFIRMED sem evidência reproduzível; o que não foi medido está marcado UNKNOWN.

---

## 0. Veredito rápido das 5 alegações

| # | Alegação | Veredito | Evidência (1 linha) |
|---|---|---|---|
| 1 | HEAD real = `d7258a1`, não `2e67a82` | **CONFIRMED — imprecisão minha** | `git log` ; errata já inserida no Gate 01 |
| 2 | `pipeline/assemble.py` não existe ⇒ `hcg.generate_character()` está quebrado | **CONFIRMED — mais grave do que "documental"** | `ModuleNotFoundError: No module named 'human_generator.pipeline.assemble'`; `git log --all --diff-filter=AD -- 'human_generator/pipeline/*.py'` → **0 commits, nunca existiu** |
| 3 | `weld` global funde regiões semanticamente distintas | **PARCIALMENTE CORRETO / diagnósticos diferentes** | O weld é de facto a causa raiz dos 36+2, mas **não há uma única fusão cross-região** (0 pares `region_a+region_b`); a causa dominante é *clamp que projeta vértices distintos no mesmo ponto* — logo o meu `weld_exclude` do Gate 01 **era a cura errada** |
| 4 | `fbm3`/`ridged3` terminam em `... and 1.0` | **CONFIRMED oddity → IMPACT LATENT (não atual)** | divisor avalia sempre 1.0 em vez de 1.75/1.875; `fbm3` mede [-1.333, 1.262] (nominal [-1,1]); **0 chamadores de `stack.noise()`** em todo o repo → impacto geométrico hoje = nenhum |
| 5 | "topologia determinística ≠ semanticamente estável" | **CONFIRMED que é a pergunta certa — e já respondida por medição** | 5821 índices: 0,07% (4 índices) mudam de região nos extremos, 0,02% (1 índice) entre presets → estabilidade prática 99,93%, com regra estrutural a formalizar |

---

## 1. Errata ao Gate 01 (o que eu escrevi mal)

1. **HEAD**: o Gate 01 dizia `HEAD: 2e67a82`. Correto: `2e67a82` = último commit de **código**; `d7258a1` = HEAD no momento da leitura, só documentação. Já corrigido no próprio Gate 01 (§ cabeçalho).
2. **`weld_exclude` como "CHANGE #2"**: proposta errada/incompleta. Não existem fusões entre regiões diferentes (medido: `cross-region pairs: {}`), portanto excluir regiões do weld **não** remove nada dos 36 non-manifold. Substituída em §3.4 pela correção causal.
3. **A leitura dos 36 non-manifold no commit `2e67a82`** dizia "weld interaction" e ficava-se por aí. Agora está atribuído: 36 = dentes+clamp, 2 = globo ocular (o audit de produção conta só arestas com >2 faces; as 2 restantes são *loose edges*, §3.2).
4. **O Gate 01 não notou** que a API pública prometida no `__init__.py`/docstring nunca foi implementada (§4). O Edmundo encontrou-o; eu não o tinha destacado — falha minha de auditoria, não do processo.

---

## 2. O que o checkpoint realmente contém (medição fresca, `realistic_female` seed 42)

Construção completa = `build_body → build_head → build_eyes → build_mouth → merge(head)`. Índices: **corpo 0–3333**, **olhos/córnea/pálpebras 3334–4001**, **boca/dentes/gengivas/língua 4002–5820** (útil para atribuição causal por subconjunto).

| Métrica | `weld=0` | `weld=1e-5` (produção) |
|---|---|---|
| vértices | 5821 | **5695** ✓ (igual ao audit do checkpoint) |
| faces | 5642 | **5551** ✓ |
| faces degeneradas (área <1e-10) | **67** | **0** |
| arestas com 3 faces (non-manifold real) | 0 | **36** |
| arestas soltas (0 faces) | 0 | **2** |
| arestas de fronteira | 1000 | 970 |
| ngons | 0 | 0 |

**Leitura:** o weld é *necessário* (mata 67 faces degeneradas, criadas por vértices coincidentes-de-construção) e *nocivo* (fabrica 36 arestas triplas + 2 arestas soltas). As 5695 v / 5551 f reproduzem exactamente o número reportado no checkpoint → a minha reconstrução do pipeline é fiel.

---

## 3. Mecanismo do weld — prova, não hipótese

### 3.1 Atribuição causal por subconjunto (soldar apenas uns índices)
| Soldar só… | arestas non-manifold (>2 faces) |
|---|---|
| EYES (3334–4001) | **2** |
| MOUTH (4002–5820) | **36** |
| SKIN (0–3333) | **0** |
| tudo | **38** (36+2) |

Isto fecha o caso: **o clamp da boca produz 36; o globo ocular produz 2.** Não há um terceiro contribuinte.

### 3.2 Causa dos 36 (dentes) — A/B do clamp
Censo de grupos de vértices coincidentes (arredondado a 1e-5, que é a distância do weld):

| | grupos | decomposição por região |
|---|---|---|
| clamp ATIVO | 78 | scalp 2, skin 6, eye 28, cornea 10, **enamel 32** |
| clamp DESLIGADO (`skull_front_y → -1e9`) | 44 | eye 28, cornea 10, enamel 4, oral 2 |

→ O clamp **fabrica 32 grupos novos de esmalte** (e altera 2 orais, 6 de pele, 2 de couro cabeludo). Mecanismo: `_clamp_behind` (mouth.py:231) empurra cada vértice para `skull_front_y(x,z) − margem` — **uma projeção que depende só de (x,z)**; dois vértices distintos com o mesmo (x,z) (anel dentário × anel vizinho, dentes adjacentes) colapsam no mesmo ponto. O `remove_doubles` posterior funde-os e liga malhas de dentes diferentes ⇒ aresta com 3 faces.
Exemplo medido: grupo `(0.00393, 0.09088, 1.49139)`, vértices `1485` e `1502`, ambos `region=enamel`.

### 3.3 Causa dos 2 (olhos) — defeito no construtor do globo
- `eyes.py` gera o anel 0 do globo com `phi = mix(-π/2, 0.34π, k/NR)`, ou seja `phi_0 = -π/2`; em `sph()` a componente tangencial é `right * (theta * cos(phi))` e `cos(-π/2) = 6.1e-17` ⇒ **os 13 vértices do anel 0 (theta = -π/2 … +π/2) caem todos no mesmo ponto** (o polo posterior). Medido: ids 632–644 coincidentes, registados como `eye.L.0`.
- Segue-se `cap_start="pole"` → `cap_pole()` (topology.py:212) constrói um *anel intermédio encolhido* antes do vértice do polo; aplicado a um anel degenerado, gera **mais 13 vértices no mesmo ponto**. Medido: ids 710–722 (não registados em `builder.rings`), exactamente o mesmo `(0.03289, 0.08823, 1.55738)`.
- Total por olho: **26 vértices coincidentes** (13 anel degenerado + 13 anel intermédio do cap). O weld funde-os ⇒ o leque colapsa em *loose edges* (2 arestas com 0 faces).
- Nota: este defeito é **anterior e independente** da boca (aparece em `head+eyes`, sem boca) e independente do clamp.

### 3.4 Correção causal proposta (substitui o `weld_exclude`)
Nenhuma lista de exclusões é necessária se as causas forem removidas — a ordem de aplicação é que estava errada:

1. **Olhos**: não materializar o anel 0 do globo (começar em `k=1`), deixando o `cap_start="pole"` criar o polo. `cap_pole` já está correto para anéis não-degenerados. Custo: 0 geometria perdida (o anel 0 era 13 vértices no mesmo ponto), −52 vértices na malha final.
2. **Boca/clamp**: tornar `_clamp_behind` **não-colapsante** — em vez de projetar só em (x,z), preservar uma componente tangencial por vértice (ex.: deslocamento ao longo do arco dentário, ou clamp por normal local). Critério de prova: censo de grupos coincidentes dentro do conjunto `enamel+gum+oral+tongue` tem de voltar a **4** (o valor do build sem clamp) e o audit a **0 non-manifold**.
3. **Guarda permanente** (a parte que faltava no Gate 01): `audit()` passa a reportar `coincident_groups` por região e `loose_edges`; `to_bmesh` ganha um *assert* opcional (`strict=True`) que falha se o weld fundir vértices que não venham de `cap_pole`/`mirror_merge`/`close=True` — a classe de bug deixa de poder voltar em silêncio.
4. **Não mexer no weld global**: com 1–2 corrigidos, o weld continua a ser o que limpa as 67 faces degeneradas (efeito desejado) sem fabricar topologia inválida.

Elegância demonstrada: corrigir a *produção* da coincidência (2 pontos no código) substitui a lista de exclusões proposta no Gate 01 e é verificável por um número (36 → 0, 2 → 0).

### 3.5 Censo das restantes coincidências (fora do escopo das correções acima)
`eye`: 28 grupos (2 de 26 + 26 pares) · `cornea`: 10 pares · `skin`: 6 · `scalp`: 2 · `oral`: 2 · `enamel`: 4 base. **UNKNOWN** (não investigado nesta ronda): a proveniência individual dos 26 pares de `eye` e dos 10 de `cornea` — some não produzem non-manifold, mas nenhum deles foi atribuído a um construtor específico. Fica como item de investigação com prioridade baixa, custo ~20 linhas de diagnóstico.

---

## 4. A lacuna que o Edmundo encontrou: `hcg.generate_character`

- `human_generator/__init__.py` promete no docstring `result = hcg.generate_character(spec, out_dir="out")` e implementa o *wrapper* que importa `human_generator.pipeline.assemble`.
- `human_generator/pipeline/` contém **apenas** `__init__.py` (112 bytes, docstring de uma linha).
- `git log --all --diff-filter=AD -- 'human_generator/pipeline/*.py'` → nenhum commit **jamais** criou `assemble.py`.
- Chamada real: `ModuleNotFoundError: No module named 'human_generator.pipeline.assemble'`.
- O README (linha 2) descreve um sistema completo com "character pipelines" — **overpromise documental**, não uma regressão: foi sempre assim.

**Classificação honesta:** é um *contrato de API não implementado*, agravado por falhar com `ModuleNotFoundError` em vez de uma mensagem de estado. Como o Gate 01 listava "pipeline/CLI" para S5, este item **promove-se a S0** (bloqueante de credibilidade): ou se implementa o mínimo do contrato, ou se declara explicitamente o estado no `__init__`/README. A segunda opção é 10 linhas e zero risco; a primeira é a fatia S5. **Decisão do Edmundo** (o plano propõe S0 = declarar + teste que falha com mensagem útil, e S5 = implementar).

Nota adicional: a validação do checkpoint foi feita por `tools/dev_smoke.py` (monta os generators directamente). Ou seja, **o "pipeline" que o README anuncia existe hoje apenas como script de smoke** — exactamente a hipótese (1)/(3) do Edmundo, e as duas ao mesmo tempo.

---

## 5. `fbm3` / `ridged3`: oddity confirmada, impacto latente medido

Código:
```python
return tot / max(1e-6, 1.0 - 0.5 ** octaves and 1.0)
```
`X and 1.0` avalia a **1.0** sempre que `X` é verdadeiro, e `1.0 - 0.5**n ∈ [0.5, 1)` é sempre verdadeiro ⇒ o divisor é **sempre 1.0**; o `max(1e-6, …)` é código morto. A normalização pretendida (soma das amplitudes das oitavas: `(1-gain^n)/(1-gain)`) nunca acontece. Mesma linha em `ridged3`.

Medições: `fbm3(octaves=3)` → min −1.333, max **1.262** (nominal [−1, 1]; overshoot 1,75×) · `ridged3(octaves=4)` → min 0.373, max **1.824** (nominal [0, 1]; 1,88×).

**Impacto hoje: nenhum** — `grep -rn "\.noise(" human_generator tools` → **0 chamadores**; o `mode == "noise"` de `core/field.py:180` está implementado mas nenhum gerador o usa. Classificação: **CONFIRMED oddity → IMPACT LATENT** (dispara no dia em que o `stack.noise()` for usado: deslocamento 1,75× o pretendido). Correção: 1 linha + teste de contrato (`|fbm3| ≤ 1`).

---

## 6. Estabilidade semântica dos índices (a pergunta central levantada)

**Resultado medido** (5821 índices comparados um-a-um):

| Comparação | Índices que mudam de região | Localização |
|---|---|---|
| `realistic_female` 42 vs extremos (0.5→1.9 nariz, etc., cabeça 1.5×, estatura 1.50) | 4 / 5821 = **0,07%** | 2× `skin→sole` (fronteira da planta, y≈0.15) · 2× `brow→skin` (borda da região da sobrancelha, z≈1.5858) |
| `realistic_female` 42 vs `cyber_angel` 999 | 1 / 5821 = **0,02%** | 1× `palm→skin` (borda da palma, x≈−0.2988) |
| Contagem total de vértices/faces | **idêntica em todos os casos** | — |

**Conclusão disciplinada:** a carteira estrutural (quem é vizinho de quem, em que ordem, com que material) é estável; a **etiqueta de região** é *quase* estável, e as raras excepções não são estruturais — são **predicados de posição** (`sole`/`palm`/`brow` são decididos por testes geométricos sobre a posição final). Logo:
- UVs, pesos por anel e shape keys são transferíveis **com segurança** (dependem de índices e posições, não de etiquetas).
- Para se poder afirmar estabilidade semântica *plena*, falta uma regra: **as etiquetas de fronteira devem ser decididas por pertença estrutural (índice/anel de origem), nunca por comparação de coordenadas**. Teste de aceitação proposto: 0 flips em 20 specs × 3 presets, com a lista de índices-por-região a ser idêntica — e não "≈ idêntica".

Isto responde exactamente ao pedido do Edmundo: **topologia determinística (provada) + estabilidade semântica (medida em 99,93%, com causa identificada e regra de correção definida)**.

---

## 7. Estado do Gate

- **Implementado nesta ronda:** nada. Apenas `docs/RESEARCH_GATE_01.md` (errata) e este `RESEARCH_GATE_02.md`.
- **Código inalterado desde o checkpoint:** `2e67a82` (o único commit depois disso é documentação).
- **Bloqueante para `PROCEED`:** decisão do Edmundo sobre §4 (declarar vs implementar o contrato de `generate_character`).
- **O que eu proponho como primeira fatia depois do PROCEED:** S1 (infra de testes + contratos de `_math`/`rng`), precisamente porque agora há **três** bugs provados que teriam sido apanhados por um teste de 5 linhas: `smoothstep` invertido, `fbm3` mal normalizado, anel degenerado dos olhos.

## 8. Tabela de actualização do plano (Gate 01 §F)

| # | Estado novo |
|---|---|
| S0 **(novo)** | Decidir e fixar o contrato da API pública (`generate_character`); teste que verifica a mensagem de falha/comportamento. 10 linhas, risco nulo. |
| S1 | Sem alteração. Ganha 2 novos alvos: contrato `|fbm3| ≤ 1`, contrato "anel de loft não pode ser degenerado". |
| S2 | **Reformulado** por §3.4: (a) `eyes.py` não emite anel 0; (b) `_clamp_behind` não-colapsante; (c) `audit()` reporta `coincident_groups` + `loose_edges` e `to_bmesh(strict=True)` falha em fusão espúria. Critérios: non-manifold **36 → 0**, loose edges **2 → 0**, coincidências dentárias **32 → 4**, faces degeneradas continuam **0**. |
| S3–S6 | Sem alteração. |
