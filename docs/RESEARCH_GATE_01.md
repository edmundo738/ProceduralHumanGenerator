# RESEARCH GATE 01 — Checkpoint, Estudo, Comparação e Plano

**Data:** 2026-09-24 · **Branch:** `arena/01a0d308-proceduralhumangenerator`
**HEAD código:** `2e67a82` ("B4 checkpoint: hair strand system…") · prévio `d9861fb` ("face v2…")  
**Errata (Gate 02):** este documento foi comitado *depois* como `d7258a1`; HEAD do branch no momento da leitura = `d7258a1` (documentação apenas). Ver `docs/RESEARCH_GATE_02.md` para as correções de conteúdo.
**Estado:** GATE FECHADO — este documento é a entrega; nenhuma implementação nova foi feita depois do checkpoint `2e67a82`.

---

## A. Estado atual (o que existe e o que foi observado)

### A.1 Arquitetura implementada (4 713 LOC, 24 ficheiros)

```
CharacterSpec (spec.py, dataclasses + presets JSON + fingerprint blake2s)
   ↓
Anatomy (core/anatomy.py → z-tables antropométricos, skull_front_y(x,z),
   landmarks, secções de trunk/arm/leg)
   ↓
MeshBuilder (core/topology.py → loft quad-ring, cap_pole, patch_grid,
   merge/mirror_merge, creases, region codes, audit/stats)
   ↓
Fields (core/field.py → Deformer/DeformStack: gauss, socket, ridge,
   capsule, flatten, twist, noise)
   ↓
Generators: body(=trunk+armas+pés+mãos) · head(box-sphere+puxada sagital
   +loops+orelhas+campos) · eyes(globo/córnea/pálpebras) · mouth(lábios,
   arco dentário 28, gengivas, cavidade, língua) · hair(fios puros→Curves,
   pestanas, sobrancelhas, bun lofted)
   ↓
Materials (materials/skin.py: MATERIAL_MAP + PBR procedural; hcg:<kind>)
   ↓
bpy binding (core/object.py mesh/UVs/vgroups/refine-attr; conventions.py
   hcg:root rot_z=π; tools/headless_blender.py bpy 5.0.1 headless)
```

### A.2 Factos medidos (não intenção — observação)

| Teste | Resultado |
|---|---|
| Corpo (seed 42, seed 7) | 2 702 v, 2 516 f, quad 0.924, **degenerate 0**, determinismo digest ✓, 0.7 s |
| Landmarks faciais (mm acima do queixo) | olho 111 · boca 37 · glabella 128 ✓ (Farkas ok) |
| Audit face v2 (merge corpo+cabeça+olhos+boca, `d9861fb`) | 5 191 v, non-manifold **0**, degen **0** |
| Audit atual c/ cabelo (`2e67a82`) | 5 695 v, **non-manifold 36** ← regressão (ver D) |
| Varredura extremos (14 casos face.min/max, cabeça 0.75–1.5, estatura 1.50–1.90, todos-min, todos-max) | **0 crashes, 0 degenerates, 0 poke-through, 3 119 v em TODOS os casos** |
| Cabelo (3 presets) | 2 400–3 200 fios, determinismo ✓, differs cross-seed ✓, 0.8–2.9 s |
| Contrato `smoothstep` arestas invertidas | PASS manual — **não existe ficheiro de teste** |
| Render headless Cycles CPU | face+full 640×800@16spp ≈ 70–160 s — viável mas lento (2 cores) |

### A.3 Estado visual observado (renders guardados em `out/`)

BOM: pele com tom/SSS plausível; nariz com ponte→ponta→asas; perfil sagital estável em todos os extremos; lábios fechados selados (sem túnel); dentes escondidos atrás da pele central; orelhas coladas ao crânio.

MAU (confirmado por render, imagens `out/face.png` de cada commit):
1. Franja cai sobre os olhos (comprimento `front` do perfil 0.62 ainda cobre).
2. Pontas dos dentes visíveis nos cantos da boca (arco dentário ±0.98·half_w + meia-largura ultrapassa o fim da banda labial).
3. Pálpebras lêem como "chapéus" brancos sobre os olhos (folha a 1.03r sem sulco de pestanas forte).
4. Orelhas com faixas/ruído de sombreado (crestas de crease num patch 6×8 a 1.3 MP, piorado pela franja).
5. Cabelo: cor muito lavada p/ melanin 0.55 (fórmula `base` do material dilui demais).

### A.4 Ainda não validado (UNKNOWN declarado)

Grafos de material em EEVEE Next; exportação glTF de Curves (cabelo); exportação .blend/glb end-to-end; alinhamento pescoço⇄base do crânio em close-up (body top 1.633 vs skull start ~1.46 — sem render de costura); qualidade de pesos de skin; shape keys; tons de pele extremos renderizados (só numérico); física do cabelo com cache; `fuse` watertight; compatibilidade bpy 5.2 vs 5.0.1 (só 5.0.1 executou código de material com guards).

---

## B. O que foi estudado (fora do repo, a 2026-09-24 via GitHub API `HEAD`)

### B.1 `makehumancommunity/mpfb2` (607★, push 2026-09-23 — ativo)

**Arquivos lidos:** `docs/fileformats/target.md`, `human_preset.md`, `expression.md`, `rig.md`; `src/mpfb/services/humanservice.py` (índice de defs).

Como realmente fazem:

- **Malha-base fixa (hm08) + targets esparsos.** Um `.target` = linhas `vertex_index Δx Δz Δy` (ordem XZY, Y invertido, 3 decimais; <0.0001 omitido). O morph NÃO é função paramétrica: é deslocamento pré-assado sobre topologia imutável. Topologia/UVs/pintura são estáveis porque nunca mudam.
- **Preset = JSON com secções**: `phenotype` (sliders macro: Gender/Age/Height/proportions + mistura racial como 3 pesos), `targets` (lista com peso), `rig` (tipo), `slots de body parts` (eyes/eyebrows/eyelashes/tongue/teeth/hair/proxy = ASSETS trocáveis, não gerados), `clothes` (assets), `expressions`, `skin_mhmat` + `skin_material_type` (enum por shader: MAKESKIN/ENHANCED/ENHANCED_SSS/LAYERED/GAMEENGINE) + `skin_material_settings` zone-keyed, `color_adjustments` por UUID com nós Color1/Color2/Fac.
- **Rig serializado com estratégias de posição** (`rig.md`, v110): cada osso tem `head/tail` como `{strategy: CUBE|VERTEX, cube_name: "joint-spine-1"|vertex_index, default_position, offset}` — CUBE = centróide de vertex-group da junção. Como os grupos de junta vivem na base-mesh e os targets também deformam os grupos, **o rig segue automaticamente qualquer morph**. Versão de formato explícita + upgrade v100→v110 on-load.
- **Expressões = ARKit-52 como API pública** (`expression.md`): JSON com `format_version`, `face_units {nome: peso 0–1}`, `!ex-` prefix só dentro do Blender (helpers `expression_name_to_shapekey_name`), regras de compatibilidade para trás/para a frente explicitadas (chaves desconhecidas → ignorar com warning, nunca erro).

**Problemas que MPFB resolveu e nós ainda não:** versionamento de formato de preset; standardização ARKit; rig como dado derivado da malha; catálogo de partes como slots nomeados; material por "zone-keyed settings" com tipos enumerados.

**Problemas que MPFB tem e nós não:** teto topológico fixo (dedos/palma de uma malha só); dependência de 100 MB+ de assets; morphs são offsets não-anatométicos (combinações extremas afundam); nós não podemos ter "dedo a mais" nem boca aberta geométrica paramétrica — nós podemos.

### B.2 `jonathandasilvasantos/2026-human-body-generator` (push 2026-04-27; OpenGL puro, sem Blender)

**Arquivos lidos:** `human/mesh.py`, `human/skeleton.py`, `human/face_anim.py`, `human/anim_debug.py`.

- **Skeletão-primeiro**: osso = `(nome, parent, head_offset_local, tip_offset, raio)` calibrado em "head units" (0.22 m; canône Farkas: 7.5 cabeças, ombros 1.7 cabeças…). A malha é **uma cápsula por osso com pesos embutidos na construção**: `_capsule` gera `bones[]`/`weights[]` por blend-zone `smoothstep` (0.35·length) → **pesos vêm do construtor, não de pintura**. É exatamente o que o nosso MeshBuilder pode copiar: os nossos lofts já são estações numeradas — o índice de anel é a coordenada de peso.
- **`face_anim.py`**: ARKit-52/FACS como "superfície padrão que o resto do código fala"; canais sem gancho geométrico são no-op aceites; `muscle_activations()` deriva sinais de região anatómica a partir dos pesos (acoplamento muscular sem API dupla).
- **`anim_debug.py`**: validação como produto — frame-strip render + relatório quantitativo (ranges de rotação por osso, mismatches de direção source-vs-ours, spin não-intencional do root). O padrão "diagnóstico imprime números, não só imagens" é o que nos falta.

**Não copiar:** numpy/VBO/OpenGL, cápsulas como corpo (a nossa malha loftada é superior em forma), BVH retarget agora (deferido).

### B.3 Ecossistema (busca rápida, 2026-09-24)

`awesome-blender`: MB-Lab está **unmaintained**; `CharMorph` é a rewrite ativa de MB-Lab — **identificado, não estudado → UNKNOWN**. Mutatis (projeto CC-BY sobre targets MakeHuman) — histórico. Conclusão: todo o mundo open-source de "human generator" em Blender é base-mesh+targets (MPFB2/CharMorph); **ninguém faz topologia generativa por anatomia** — é a nossa diferença estrutural, para bem (liberdade morfológica real) e para mal (UVs/shape-keys/rig têm de ser regenerados deterministicamente a cada spec — que é exatamente o que a nossa constante de contagem demonstrou ser viável: 3 119 v em todos os extremos).

---

## C. Comparação

| Dimensão | Nós | MPFB2 | 2026-hbg |
|---|---|---|---|
| Fonte da forma | anatomia paramétrica → cage+fields | base mesh + offsets pré-assados | esqueleto paramétrico → cápsulas |
| Topologia | gerada, contagem fixa por spec ✓ (medido) | fixa hm08 | fixa procedural |
| Mãos/dentes/língua | construídos parametricamente | assets trocáveis | não tem |
| Rig | joints = landmarks (por construir) | JSON + estratégias CUBE/VERTEX na malha | osso primitivo, pesos na construção |
| Expressões | planeadas (keys) | ARKit-52 via `!ex-` shape keys | ARKit-52 como API central |
| Cabelo | fios de curva determinísticos (2.4k–3.2k, medido) | assets `.mhclo` + hair-editor | Curvas simples |
| Materiais | PBR procedural por params (implemented ≠ validated) | mhmat + zones, bake-friendly | flat shading OpenGL |
| Formato | presets JSON sem `format_version` ← risco | `format_version` + regras de compat. | n/a |
| Validação | smoke+audit+scan extremos (agora manual) | testes UI/pipeline do plugin | `anim_debug` numérico + strip render |

---

## D. Problemas do nosso sistema (classificados honestamente)

### CONFIRMED (com evidência acima)
1. **36 arestas non-manifold** após introduzir o clamp de boca (`d9861fb→2e67a82`). Causa provável documentada por código: `_clamp_behind` move vértices para `skull_front_y(x,z)−m` e `to_bmesh(weld)` cola dentes/gengivas vizinhos partilhando o mesmo alvo → fusões cruzadas. (Mecanismo exato = LIKELY; contagem = CONFIRMED.)
2. **Dentes visíveis nos cantos da boca** — render `out/face.png@2e67a82`; o teste numérico só compara com a superfície do crânio, não com a cobertura labial (gap no próprio teste → CONFIRMED que o teste é cego a isto).
3. **Franja cobre os olhos** (perfil de comprimento) — render.
4. **Pálpebras com aspeto de calote** (sem vinco/sulco suficiente; sheet aberto com 0 colunas ancoradas à pele) — render.
5. **Família de bug "função matemática sem contrato"** (smoothstep invertido zerava máscaras silenciosamente) — corrigido, mas **sem testes unitários** → CONFIRMED como dívida.
6. **Zero testes automatizados versionados** (`tests/` vazio; grep: nenhum assert roda em CI) — CONFIRMED.
7. **`ParameterImplemented ≠ RealismValidated`** nos materiais: todos os coeficientes (SSS radius, Fresnel mix 0.45, pore distance 6e-5) são escolhas minhas sem validação cross-view — CONFIRMED como NÃO validado.
8. **Preset JSON sem `format_version`** — CONFIRMED (li o ficheiro).
9. Coeficiente de cor de cabelo dilui a melanin (render mostra loiro-platinado para melanin 0.55) — CONFIRMED visual.

### LIKELY (suspeitas fortes, sem teste dedicado ainda)
- Fusão weld×clamp (mecanismo do #1).
- Orelhas: crestas de sombreado por normal-mismatch entre patch e elipsoide + hair overlap.
- Costura pescoço⇄crânio: os troncos param as secções nos landmarks; a puxada da face não afeta o pescoço — plausível tensão contínua, nunca medido em close.
- Cabelo longo vs ombros: sem qualquer teste de colisão/attenuation — `loose` a 0.55 m pousa nos ombros por acaso.
- glTF export de Curves com bevel → provavelmente precisa conversão para mesh antes do exporter.

### UNKNOWN (nada afirmado)
Comportamento em EEVEE Next; pesos LBS gerados; deformação de shape keys em subdiv; fidelidade sob Blender 5.2 (só testado 5.0.1); tons de pele extremos em close; custo de render com 3.2k curvas em cena animada; import/re-export round-trip.

---

## E. Decisões arquiteturais

**KEEP**
- Pipeline `SPEC→ANATOMY→LANDMARKS→GEOMETRY` (demonstrado estável nos 14 extremos).
- MeshBuilder com contagem determinística (a constância 3 119 v é o nosso "base mesh implícito" — manter invariantes de contagem como contrato!).
- DeformStack de campos analíticos + clamp por vértice.
- `Rng(seed, salt)` por módulo; fingerprint do spec.
- Fios de cabelo puros-python + `curves_to_object` (testável sem bpy).
- tooling headless bpy 5.0.1 com guards de feature-detection.

**CHANGE** (propostas, cada uma = fatia testável)
1. `tests/test_math.py` — contratos de `clamp/mix/smoothstep(±invert)/Vector.lerp` + regressão do caso zero-máscara.
2. Soldadura controlada: `to_bmesh` ganha `weld_exclude` para que clamp não funda dentes⇄gengiva; gate no smoke: `non_manifold == 0` (assert, não print).
3. Boca: banda labial cobre o arco (half_w_lips = arch_half_w + max_crown_w) e teste de cobertura estende-se a "behind lips surface", não só skull.
4. Hair: perfil de franja (curto até à linha das sobrancelhas) + direção `front` tangente; cor do fio = interp. sem diluição extra.
5. Rig: adotar "pesos da construção" (padrão 2026-hbg) — cada anel de loft guarda o parâmetro `t` da estação e a junta mais próxima → `hcg_defgroup` gerada no builder, zero pintura; joints = landmarks (já existem).
6. Expressões: camada ARKit-subset (Blink L/R, Smile L/R, JawOpen, BrowDown/Up) gerada como shape keys sobre as nossas regiões/`palpebral_fissure()` (já exposta para isto); nome `ARKIT names` verbatim para interop.
7. Presets: adicionar `format_version` + loader tolerante (lição MPFB: unknown keys→ignore, missing→default+warning).
8. Validação como produto: `tools/validate.py` — varrimento de extremos parametrizável + strip-render + relatório numérica (padrão anim_debug); roda em cada checkpoint.

**INVESTIGATE** (provar antes de decidir)
- CharMorph (MB-Lab rewrite) — estado/ideias importáveis.
- Import de `.target` MakeHuman via nearest-vertex → poderíamos aplicar offsets curados (ex.: biblioteca facial) à nossa cage; risco: deltas em topologia alheia. Provar com 1 target num spike de 30 linhas antes de prometer.
- Custo real de render/export de cabelo (curves vs mesh).
- Costura pescoço e EEVEE (close-up renders multi-view).

**DEFER**
- Roupa como sistema (manter presets actuais), BVH/retarget, lip-sync áudio, `fuse` print, Geometry Nodes, UI do addon.

**REJECT**
- Particles para cabelo; cache de base-mesh fixa (destruiria a vantagem do projeto); copiar o modelo de assets do MPFB.

---

## F. Plano de execução (aguarda aprovação — nada foi implementado)

| # | Slice | Ficheiros | Teste/sucesso | Rollback |
|---|---|---|---|---|
| S1 | Test infra + contratos math | `tests/test_math.py`, `test_spec.py`, `test_topology.py`, `pytest` no venv | pytest verde; teste do smoothstep reprovável a propósito | apagar `tests/` |
| S2 | weld_exclude + gate non-manifold + cobertura labial + franja/cor | `core/topology.py`, `mouth.py`, `hair.py` | smoke asserts: `non_manifold==0`, poke/coverage 0, render strip face antes/depois | reverter slice |
| S3 | Rig de construção + pesos por anel | `pipeline/rig.py`, `core/topology.py` (t-tag), `tools/validate.py` | joint count=bones=espec; teste sintético: roçar coxa -40° não rasga audit; weights somam 1 ±1e-6 | sem rig, export malha |
| S4 | Camada ARKit-subset shape keys + loader versionado | `pipeline/expressions.py`, `spec.py` | keys existem, weights 0–1 lidos em CLI, render de 3 expressions | remover keys |
| S5 | Pipeline final: CLI `tools/hcg_cli.py` (spec→blend/glb/png), export guard gltf-curves | `pipeline/__init__.py` | `--seed 42 --preset cyber_angel --out x/` reprodutível: digests iguais em 2 runs | CLI fino |
| S6 | Validação multi-seed (8 seeds × 3 presets × extremos) + README de validação | `tools/validate.py`, `README.md` | relatório JSON committed; zero asserts falham | — |

Cada S = commit+push (checkpoint), com o estado anterior recuperável. Estimativa: S1+S2 numa sessão; S3 a peça de maior risco.

## G. Perguntas do critério de sucesso — respostas curtas

1. **Como transformamos parâmetros em humano?** `spec→Anatomy(z/landmarks/superfícies)→cage loftada por estações→campos DeformStack→clamp de cobertura→builder (region/material/crease/UV)→bpy`. (módulos: `core/anatomy.py`, `core/topology.py`, `core/field.py`, `generators/*`)
2. **Como fazem os outros?** Base-mesh + offsets de target (MPFB2) ou esqueleto + cápsulas com pesos de construção (2026-hbg). (evidência: §B)
3. **Onde diferimos?** Topologia generativa com contagem determinística vs morfologia pré-assada; campos analíticos vs offsets; órgãos construídos (dentes/língua/orelhas) vs assets.
4. **Porquê?** Para suportar variação anatómica contínua (incl. o que hm08 não tem: boca paramétrica aberta, crânio que muda de forma) sem library de assets.
5. **O que têm eles com evidência de ser melhor?** Rig-como-dado que segue a malha (CUBE strategy), ARKit-standard, `format_version`, validação numérica — todos adoptáveis sem perder a nossa essência (itens CHANGE 5–8).
6. **O que mudar / manter / não sabemos** — ver D/E.
7. **Como provamos a próxima alteração** — F, coluna teste: asserts quantitativos + render strip + digest determinista, nunca "parece ok".

---
*Entregue por Arena.ai Agent Mode. GATE: não implementar sem aprovação explícita de Edmundo.*
