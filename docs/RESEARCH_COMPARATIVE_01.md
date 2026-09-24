# RESEARCH COMPARATIVE 01 — Investigação externa ao nível do código-fonte

**Data:** 2026-09-24 · **Branch:** `arena/01a0d308-proceduralhumangenerator`
**Estado:** S0 IMPLEMENTADO E VALIDADO (`cd7828b`) · S1–S6 NÃO IMPLEMENTADOS · nada neste relatório foi implementado.
**Método:** todo o material externo foi lido por API GitHub (`contents`/`git/trees`) no código-fonte real dos projetos, não em READMEs. Cada afirmação tem classificação: `FACT` (facto verificado em ficheiro/commit), `MEASURED` (medido por execução nossa), `OBSERVED` (visto em listagem/doc de origem), `HYPOTHESIS`, `PROPOSAL`, `VALIDATED`, `UNKNOWN`.
**Regra aplicada:** nenhuma recomendação é "X faz, logo devemos fazer"; todas seguem *X faz por causa de Y → nós temos Z → hipótese H → teste T*.

---

## 1. Estado real do nosso sistema (depois de S0)

**FACT — o que passou a existir.** `human_generator/pipeline/assemble.py` (S0) com contrato `hcg-charapi/1.0.0`: `build_character()` (puro Python, sem `bpy`) e `generate_character()` (Blender: objetos, materiais, audit, `.blend`, relatório JSON). `human_generator/__init__.py` e `pipeline/__init__.py` exportam-no; a "promessa quebrada" (`ModuleNotFoundError`) desapareceu.

**MEASURED — números do estado atual** (`realistic_female`, seed 42, `bpy` 5.0.1):

| grandeza | valor |
|---|---|
| pré-weld (puro) | 5 821 v / 5 642 f, quad 0.869, degeneradas 0 |
| pós-weld (Blender) | 5 695 v / 5 551 f, quad 0.866, degeneradas 0, **non-manifold 36**, loose 2 |
| determinismo | idêntico por regime: `float64` → `39ce28298fce36de`; `mathutils float32` → `34e746aa4e649945` |
| API pública | `tests/test_s0_public_api.py`: **67/67 checks** (modo bpy) e 32/32 (modo puro) |
| render do smoke via API | `out/face.png` + `out/full.png`, 156 s, audit inalterado |

**MEASURED — três defeitos descobertos *durante* o S0** (nenhum estava no Gate 02):
1. **Regime numérico dependente da ordem de import.** `core/_math.py` prefere `mathutils` (float32) quando `bpy` já foi importado e usa o stand-in puro (float64) caso contrário → **dois digests legítimos para o mesmo spec+seed**. Medido: 39ce… (puro) vs 34e7… (bpy primeiro). Documentado no contrato (`result.numerics`) e no README; unificação = decisão S1/S2.
2. **As minhas chaves de audit estavam erradas** (`non_manifold`/`degenerate` em vez de `non_manifold_edges`/`degenerate_faces`): os avisos de defeito conhecido eram **código morto que nunca disparava**. Corrigido e coberto por teste.
3. **`body.head_size` não existe** (`BodyParams` tem `head_units`): os casos "cabeça grande/pequena" do varrimento de extremos do Gate 01 foram **no-op silenciosos**. O validador estrito de `overrides` apanhou isto ao recusar a chave — a mesma classe de bug silencioso que já tinha aparecido no `smoothstep`. Consequência: a afirmação "cabeça 0.75–1.5 testada" do Gate 01 fica **retractada**; o varrimento correto (com `head_units` 6.4 vs 7.65) está agora no teste S0 e passa com topologia constante.

**FACT — dívida que o S0 tornou visível:** `to_bmesh(weld=...)` engole exceções (`except Exception: pass`) — se a soldadura falhar, ninguém saberá.

---

## 2. Auditoria S0 (o que foi pedido vs. o que foi entregue)

| Critério do Edmundo | Resultado |
|---|---|
| "Transformar `generate_character(...)` numa API real, pequena e verificável" | FEITO — um módulo, duas funções, contrato escrito no docstring: entrada, saída, determinismo, erros, versão |
| "Definir o contrato antes de escrever código" | FEITO — secção CONTRACT no topo de `assemble.py` (frozen `1.0.0`), incluindo a qualificação de determinismo por regime numérico |
| "A implementação deve apenas orquestrar os componentes que já existem" | CUMPRIDO — nenhum gerador, anatomia, material, rig, roupa ou otimização novos; `git diff` toca apenas ligação/orquestração + testes + docs |
| "`generate_character(spec, seed=...)` devolve personagem válida pela API pública" | VALIDADO — objetos na cena, 13 materiais, UVs, atributo de região, modificador do spec, tag de spec |
| "Segunda execução, mesmos parâmetros e seed, resultado determinístico" | VALIDADO — digest, fingerprint, audit e stats idênticos entre execuções independentes; pins por regime |
| "`tools/dev_smoke.py` deixa de ser a única prova" | FEITO — o smoke **passou a usar** `build_character` (uma só via de orquestração) e existe `tests/test_s0_public_api.py` |
| "Não avançar para S1" | CUMPRIDO — S1–S6 intocados |

**Erros que a auditoria S0 encontrou no próprio S0 (registados, não escondidos):** os três do §1 mais um `class GenerationResult(BuildResult.__mro__[1] if False else object)` (artefacto de splice) que foi corrigido antes do commit — a classe de bug que já está nas lições do projeto.

---

## 3. Investigação externa (ao nível do código)

### 3.1 Projetos efetivamente estudados

| # | Projeto | Estado verificado | Ficheiros lidos |
|---|---|---|---|
| P1 | `makehumancommunity/mpfb2` | ativo (push 2026-09-23), 2 853 ficheiros | `docs/fileformats/{target,weights,rig,expression,human_preset}.md`, `src/mpfb/services/{rigservice,exportservice}.py`, `test/{README.md,test_headless.py}`, árvore `test/testdata/` |
| P2 | `jonathandasilvasantos/2026-human-body-generator` | push 2026-04-27, 4 202 ficheiros | `human/mesh.py` (2 129 linhas; `SkinnedMesh`, `_capsule`, `_profiled_capsule`, `_torso_profile`, `_limb_profile`, `_skull_shell`), `human/skeleton.py`, `human/face_anim.py`, `human/anim_debug.py`, árvore completa |
| P3 | `OliverJPost/HumGen3D` | ativo (push 2026-05-05), 329 ficheiros | `tests/{expectations,test_fixtures}.py`, `tests/human/test_body.py`, `human/skin/skin.py`, `human/process/{apply_modifiers,export}.py`, `common/compatibility.py`, árvores `backend/content/`, `human/process/` |
| P4 | `Upliner/CharMorph` (sucessor do MB-Lab) | muito ativo (push 2026-09-22), 570★ | árvores `lib/`, `cmedit/`; `cmedit/vg_calc.py`; `CharMorph-db` (647 ficheiros: `.blend` por personagem + `aliases.yaml`) |
| P5 | `vchoutas/smplx` (SMPL-X) | 70 ficheiros, último push 2024-08-12 | `smplx/vertex_ids.py`, `smplx/body_models.py` (grep estrutural de `lbs`, `shapedirs`, `posedirs`, `J_regressor`, `vertices2landmarks`) |
| P6 | `abirmehmed/human_character_generator` | ★0, push 2026-07-06 | `mesh_generator.py` (630 linhas, lido), `test_generator.py`, `cli.py`, `blender_addon.py` (listados) |
| P7 | `Z-Anatomy/Models-of-human-anatomy` | 203★, push 2026-09-23, **9 ficheiros** | árvore: `Z-Anatomy.zip` (86 MB), `TA2.csv`, `Anatomy-shortcuts.py` (290 KB) — **dados, não gerador** |
| P8 | `weihaox/awesome-digital-human`, `duixcom/Duix-Avatar` (contexto) | ativos | metadados + descrição — "digital human" no ecossistema = avatar neural 2D/4D (vídeo), **não** geração paramétrica de malha |

`OBSERVED`: MB-Lab está descontinuado e CharMorph é a reescrita ativa — logo a linha MakeHuman/MB-Lab/Mutatis é hoje P1 + P4. Nenhum destes projetos (nem os 8) gera topologia a partir de anatomia: **todos** usam malha-base + morph targets ou cápsulas por osso (`FACT` por leitura de código em P1–P6). A nossa diferença estrutural confirmou-se na fonte, não na documentação.

### 3.2 Mecanismos encontrados (formato pedido)

---

**F1 — Identidade de vértices como contrato publicado**
- **PROBLEMA:** como garantir que "índice 15 432" significa a mesma coisa anatómica em qualquer personagem/versão?
- **EVIDÊNCIA:** P5 `smplx/vertex_ids.py` — dicionário literal `'nose': 332, 'reye': 6260, 'leye': 2800, 'rear': 4071, 'lear': 583, 'rthumb': 6191 …` separado por variante (`'smplh'`, `'smplx'`, `'smpl'`). P1 `docs/fileformats/weights.md` — pesos são `[vertex_index, weight]` e **tudo** (targets, rigs, roupa, pesos) indexa a mesma malha-base imutável `hm08`.
- **MECANISMO:** a identidade não é inferida — é **declarada** numa tabela e congelada com a malha; qualquer operação downstream refere-se ao índice.
- **PORQUE FUNCIONA:** elimina todo o problema de re-identificação: pesos, rigs, blendshapes e assets são simplesmente arrays paralelos.
- **LIMITAÇÕES:** qualquer alteração topológica invalida *todos* os ficheiros (é por isso que P1/P4 não podem corrigir a mão da malha-base); e a tabela é **por variante** — o próprio standard quebra entre SMPL/SMPL-H/SMPL-X (`FACT`, chaves separadas no mesmo ficheiro).
- **NOSSO EQUIVALENTE:** temos o *inverso* — os landmarks geram a geometria, mas não existe tabela landmark↔índice. A topologia constante (5 821 v em todos os specs; 99,93 % de estabilidade de região, Gate 02 §6) dá-nos o direito de publicar a tabela, e a validação estrita de `overrides` impede derivas silenciosas.
- **DECISÃO: ADAPTAR.** `build_character` passa a emitir `landmarks.json` (nome → índice de vértice, e depois → âncora baricêntrica, ver F2) com o `fingerprint`/`digest`. Não adoptamos a malha congelada: adoptamos a *tabela* e o princípio de a versionar.
- **TESTE (S3):** os mesmos 40+ landmarks resolvem para os mesmos índices em 20 specs × 3 presets × extremos; falha se um índice mudar sem que a versão da tabela suba.

---

**F2 — Landmarks como âncoras locais (baricêntricas), não como pontos no espaço**
- **PROBLEMA:** um landmark guardado como coordenada deixa de ser exato quando a malha deforma ou subdivide.
- **EVIDÊNCIA:** P5 `smplx/body_models.py` importa de `lbs.py`: `vertices2landmarks`, `find_dynamic_lmk_idx_and_bcoords`; landmarks são `lmk_faces_idx` + `lmk_bary_coords`.
- **MECANISMO:** o landmark é definido **dentro de uma face** (índice de face + coordenadas baricêntricas); para obter a posição faz-se interpolação — sobrevive a qualquer deformação, subdivisão ou pose, por construção.
- **PORQUE FUNCIONA:** a informação é relativa à superfície, não ao mundo; é o análogo de UV para pontos.
- **LIMITAÇÕES:** exige faces estáveis; um landmark no meio de uma região que muda de triangulação perde validade; soma custo de lookup.
- **NOSSO EQUIVALENTE:** `Anatomy.landmarks` são pontos analíticos e usam-se *antes* da malha existir (o que é mais forte para gerar e mais fraco para consultar). Não temos consulta landmark→superfície depois do build.
- **DECISÃO: ADAPTAR (investigar em S3).** Guardar, por landmark, a âncora local (face+baricêntricas) calculada no fim do build; serve para rig, para shape keys e para o pipeline de subdivisão.
- **TESTE (S3):** com 3 specs extremos + subsurf 2, a posição reconstruída pela âncora difere < 1e-6 m do valor analítico recalculado; e o rig definido por âncoras não deriva > 0,1 mm sob deformação extrema.

---

**F3 — Pesos gerados na construção (nunca pintados)**
- **PROBLEMA:** skin weights são caros, não determinísticos se pintados, e frágeis se derivados de distância pós-hoc.
- **EVIDÊNCIA:** P2 `human/mesh.py`: `SkinnedMesh(positions, normals, bones (N,2), weights (N,2) rows sum to 1, indices)`; em `_profiled_capsule` cada anel escreve `w` explicitamente (`wa = 0.0` na calote proximal, interpolação suave em `blend_zone = 0.35 * max(length, 1e-3)`), com o comentário "keeps the cheap capsule topology".
- **MECANISMO:** a função que cria a geometria sabe, em cada anel, a que osso pertence e a que distância está da junta → escreve o par (osso, peso) no mesmo passo. Zero pintura, zero procura espacial, determinístico.
- **PORQUE FUNCIONA:** o peso é uma consequência da topologia, não um dado extra a manter sincronizado; sobrevive a mudanças de proporção.
- **LIMITAÇÕES:** 2 ossos por vértice fixos (inadequado a ombros/quadril reais), e a topologia é uma cápsula por osso — pagam a simplicidade na forma.
- **NOSSO EQUIVALENTE:** os nossos `loft` já são **estações numeradas**: cada anel sabe o `t` da estação e a que junta pertence; `MeshBuilder` tem `set_group` mas ninguém escreve pesos. O `Anatomy` tem landmarks que são exatamente as juntas.
- **DECISÃO: ADOPTAR (S3).** Gerar `hcg_defgroup` no construtor: por anel, mapear `t`→(osso proximal, osso distal) com *smoothstep* na zona de junta, mais de 2 influências onde a anatomia exigir.
- **TESTE (S3):** Σpesos = 1 ± 1e-6 em todos os vértices com peso; rotação de −40° na coxa e 60° no cotovelo sem auto-interseção de anéis (medida de comprimento de aresta vs. baseline) e sem "candy-wrapper" (raio do anel dentro de 10 % do esperado).

---

**F4 — Âncora de junta = centróide ponderado de um grupo de vértices**
- **PROBLEMA:** onde está exatamente a junta, sem a colocar à mão e sem ela se deslocar quando as proporções mudam?
- **EVIDÊNCIA:** P1 `docs/fileformats/rig.md` — estratégia `CUBE`: posição do osso = **centróide dos vértices do grupo de junção**; alternativa `VERTEX` (índice) com `default_position` e `offset`. P4 `cmedit/vg_calc.py` — `vg_full_to_avg(group)` devolve `Σ(co·weight)/Σweight` **exatamente a mesma ideia**, num projeto independente.
- **MECANISMO:** a junta é derivada da malha: como os targets deformam a malha *e os grupos*, a junta segue automaticamente qualquer morph.
- **PORQUE FUNCIONA:** desacopla rig de números fixos; uma só fonte de verdade (a geometria).
- **LIMITAÇÕES:** requer grupos de junção fiáveis; junta "média" pode cair fora da pele em anatomia extrema (daí precisarem de `default_position`).
- **NOSSO EQUIVALENTE:** `Anatomy.landmarks` já dá as juntas analyticamente (mais preciso), mas o rig futuro precisa dos grupos de qualquer forma para *pesos*.
- **DECISÃO: ADAPTAR (S3):** junta = landmark analítico; peso/junção de fallback = centróide ponderado (reuso para corrigir landmarks em specs extremos).
- **TESTE (S3):** para cada osso, a cabeça calculada pelo centróide difere < 2 mm do landmark analítico nos 3 presets; divergência > 2 mm falha (sinal de grupo mal formado).

---

**F5 — Limpeza de degenerados pela operação certa (`dissolve_degenerate`), não por soldadura**
- **PROBLEMA:** a malha construída tem faces de área nula (vértices coincidentes de construção) e nós resolvíamos isso com `remove_doubles` global → 36 arestas non-manifold + 2 loose edges (Gate 02).
- **EVIDÊNCIA (externa):** P1 `exportservice.py` não contém qualquer `weld`/`remove_doubles` (`FACT` por grep); P3 tem `human/process/apply_modifiers.py` com tratamento explícito de modificadores que mudam topologia; nenhum dos projetos estuda solda global como passo normal. **EVIDÊNCIA (nossa, `MEASURED` hoje):** A/B/C/D numa execução headless:

| variante | v | f | non-manifold | loose | degeneradas | ngons | quad |
|---|---|---|---|---|---|---|---|
| A `weld=0` (cru) | 5 821 | 5 642 | **0** | 0 | **67** | 0 | 0.869 |
| B `weld=0` + `dissolve_degenerate(1e-5)` | 5 749 | 5 567 | **0** | 2 | **0** | 10 | 0.865 |
| C `weld=1e-5` (produção atual) | 5 695 | 5 551 | **36** | 2 | 0 | 0 | 0.866 |
| D C + `dissolve_degenerate` | 5 695 | 5 543 | 36 | 2 | 0 | 10 | 0.865 |

- **MECANISMO:** `bmesh.ops.dissolve_degenerate(dist=…)` colapsa arestas/faces de comprimento/área abaixo do limiar por **dissolução local** e reconstrói as faces vizinhas; não tenta decidir que vértices *distintos* são o mesmo ponto, que é precisamente onde o `remove_doubles` corrompe topologia.
- **PORQUE FUNCIONA:** respeita a conectividade existente; o custo são ngons (10) e não há fusão de regiões distintas.
- **LIMITAÇÕES:** produz ngons (10 no nosso caso) e não corrige a *fonte* da degeneração (o anel 0 do globo ocular continua a ser 26 vértices num ponto, agora visível como 2 loose edges e 103 vértices de valência irregular).
- **NOSSO EQUIVALENTE:** `to_bmesh(weld=…)` + `except Exception: pass` (dívida adicional: falha silenciosa).
- **DECISÃO: ADOPTAR como mecanismo de limpeza, ADAPTAR com correção na fonte.** S2 = (a) corrigir a fonte (anel 0 do globo; clamp não-colapsante), (b) trocar a soldadura global por `dissolve_degenerate` como **rede de segurança** com contagem declarada no audit, (c) `weld` passa a default 0 e o parâmetro deixa de existir sem opt-in explícito.
- **TESTE (S2):** non-manifold 36→0, loose 2→0, degeneradas 67→0, ngons ≤ 12 (e explicados), quads ≥ 0.86; `weld=1e-5` a produzir aviso (não a ser o caminho por omissão).

---

**F6 — Validação automática dentro do Blender, com asserções numéricas**
- **PROBLEMA:** provar que um gerador dentro do Blender funciona sem inspeção visual.
- **EVIDÊNCIA:** P1 `test/` com `execute_tests_headless.bash`, `test_headless.py` (pytest via `pytest.main`), `testdata/*.target`, `human.unit_test_sample.json`, `crossref_target.obj` e cobertura. P3 `tests/` com pytest + fixtures em Blender (`humans/body/face/hair/pose/skin/export/baking`), `test_fixtures.py` com fixtures `scope="class"` reaproveitadas (`male_human`, `female_human`, `male_rigify_human`, `male_2nd_scene_human`) e `expectations.py` para exceções esperadas.
- **MECANISMO:** a mesma linguagem (pytest) corre *dentro* do processo do Blender; fixtures criam humanos uma vez por classe e os testes mutam/afirmam estado.
- **PORQUE FUNCIONA:** o custo de arranque do Blender é amortizado; as asserções são código, não imagens.
- **LIMITAÇÕES:** P3 assere sobretudo *estado da API* (`hash(human.body)` mudou, `len(keys com valor>0.001) > 10`), não geometria — defeitos geométricos passam-lhe ao lado; P1 precisa do Blender instalado e permissões de escrita.
- **NOSSO EQUIVALENTE:** S0 criou exatamente isto, mas em versão mínima: um ficheiro, asserts sem framework, e um *pin* de geometria (digest/counts) que P1/P3 não têm. Faltam pytest, fixtures e contratos de `_math`/`rng` (S1).
- **DECISÃO: ADOPTAR (S1) pytest + fixtures de classe**; **ADAPTAR** mantendo os nossos *pins* — a originalidade útil aqui é nossa: pins de digest e de audit, que transformam "mudou a geometria" em falha de teste.
- **TESTE (S1):** `pytest tests/` corre headless; um teste-sonda que altera um coeficiente de geometria tem de falhar o pin (meta-teste de que o pin realmente mede).

---

**F7 — Diagnóstico quantitativo como produto (não só render)**
- **PROBLEMA:** "parece bem" não é evidência; e render é lento (156 s nosso).
- **EVIDÊNCIA:** P2 `human/anim_debug.py` — strip de frames + relatório com duração, ossos mapeados, trajetória do root, *range* de rotação por osso (deteta ossos presos ou selvagens) e desvio de direção mundo entre fonte e modelo. P2 `human/face_anim.py` — canais de região muscular derivados dos pesos ARKit, permitindo auditar acoplamento.
- **MECANISMO:** em vez de julgar imagens, imprime-se um conjunto de números por execução e comparam-se entre execuções/variações.
- **PORQUE FUNCIONA:** deteta regressões que o olho perde, e é reprodutível em CI.
- **LIMITAÇÕES:** os números têm de ser escolhidos com cuidado — o próprio P2 imprime, não assere (nenhum limiar de falha).
- **NOSSO EQUIVALENTE:** `core.topology.audit` (bons números: non-manifold, degeneradas, valência, quad) + `BuildResult.to_dict()` (S0) — mas sem comparação automática nem *baselines*.
- **DECISÃO: ADOPTAR (S6) `tools/validate.py`**: matriz seeds × presets × extremos, relatório JSON por execução, comparação contra baseline versionado, **com limiares que falham** (o que P2 não faz).
- **TESTE (S6):** o relatório tem de detetar uma regressão injetada (ex.: forçar `margin` do clamp) como falha, não como diferença informativa.

---

**F8 — Versionamento de formato e compatibilidade tolerante**
- **PROBLEMA:** presets/ficheiros evoluem; dados antigos têm de continuar a carregar.
- **EVIDÊNCIA:** P1 `human_preset.md` e `weights.md` (`"version": 110`), com upgrades v100→v110 no load; `expression.md` — chaves desconhecidas são ignoradas com aviso, nunca erro; P3 `human/skin/skin.py` `set_from_dict()` **devolve a lista de erros** em vez de rebentar (`as_dict()`/`set_from_dict()` simétricos); P5 `body_models.py` degrada explicitamente: `num_betas = min(num_betas, shapedirs.shape[-1])` com mensagem de incompatibilidade.
- **MECANISMO:** campo de versão + política declarada (ignorar desconhecido, avisar, degradar com mínimo) + round-trip simétrico dict↔objeto.
- **PORQUE FUNCIONA:** os dados sobrevivem ao código; os utilizadores não perdem trabalho por causa de uma chave nova.
- **LIMITAÇÕES:** tolerância sem validação esconde erros de escrita; P1/P3 confiam na disciplina do autor.
- **NOSSO EQUIVALENTE:** presets JSON **sem** `format_version` (`FACT`); `CharacterSpec.from_dict` ignora campos desconhecidos **em silêncio** (`OBSERVED` no código) — e o S0 só o corrigiu no caminho `overrides`; `to_json`/`from_json` existem mas sem round-trip testado.
- **DECISÃO: ADOPTAR (S1) `format_version` + `load` tolerante com avisos + round-trip simétrico**; **REJEITAR** a tolerância silenciosa.
- **TESTE (S1):** JSON com chave desconhecida → aviso explícito, carrega; JSON com campo obrigatório ausente → erro claro; `from_dict(spec.to_dict()) == spec` (fingerprint igual) em 3 presets × 3 seeds.

---

**F9 — Operações destrutivas com restauro de estado (shape keys/drivers)**
- **PROBLEMA (o nosso futuro imediato):** aplicar subdivisão/boolean/topologia destrói shape keys; qualquer pipeline que faça isso perde trabalho do utilizador.
- **EVIDÊNCIA:** P3 `human/process/apply_modifiers.py` — `_add_shapekeys_again(objs, sk_dict, driver_dict)` depois de `apply_topology_changing_modifiers`; `apply_selected_modifiers(modifier_types, obj, context)`; e `refresh_modapply` + `build_summary_list` para avisar o utilizador do que vai ser aplicado.
- **MECANISMO:** serializar valores de keys + drivers antes, aplicar o modificador, reconstruir as keys depois; e ser explícito com o utilizador sobre a ordem.
- **PORQUE FUNCIONA:** reconhece que aplicar modificadores é irreversível e trata o estado como dado a preservar.
- **LIMITAÇÕES:** se falhar a meio, o estado intermediário é pior que o inicial; keys reconstruídas podem perder *drivers* complexos; requer o contexto certo do Blender.
- **NOSSO EQUIVALENTE:** ainda não temos shape keys nem ordem de modificadores gerida (o S0 põe só o SUBSURF). P1 tem abordagem paralela: `bake_modifiers_remove_helpers(bake_masks, bake_subdiv)` antes de exportar, com o modificador MASK ligado ao grupo de vértices `"body"` para esconder geometria auxiliar.
- **DECISÃO: ADOPTAR como requisito de S4** (e adoptar já o princípio em S2: qualquer operação que mude índices tem de declarar o efeito no contrato).
- **TESTE (S4):** criar keys, aplicar subsurf, verificar valores intactos e ausência de *drivers* órfãos; e um teste que falha se uma operação mudar contagens de vértices sem atualizar a versão do contrato.

---

**F10 — Exportar "dados de identidade" junto com a malha**
- **PROBLEMA:** quem recebe a nossa malha não sabe a que vértice corresponde cada landmark nem a que spec pertence.
- **EVIDÊNCIA:** P1 exporta por *bake de modificadores* com máscaras por grupo de vértices (geometria auxiliar removida por MASK, não por delete); P5 publica `vertex_ids`; P6 `MeshExporter.export_obj` escreve cabeçalho com contagens e **gera um script Python do Blender** em vez de um `.blend` (`export_blend_script`).
- **MECANISMO:** a interoperabilidade passa por metadados explícitos (tabela de índices, contagens, versão).
- **PORQUE FUNCIONA:** o consumidor consegue reancorar rigs/vestuário/animações sem adivinhar.
- **LIMITAÇÕES:** P6 exporta grupos iterando **todas** as faces por grupo (faces duplicadas no OBJ — `HYPOTHESIS`, não executado); P1 precisa de Blender para exportar.
- **NOSSO EQUIVALENTE:** S0 já escreve `<nome>.report.json` com `fingerprint`, `digest`, `contract_version`, `audit`, `numerics` — falta a tabela de landmarks e o GLB.
- **DECISÃO: ADOPTAR (S5):** GLB/blend + `report.json` + `landmarks.json` com a mesma versão de contrato; **REJEITAR** o padrão "exportar script" do P6.
- **TESTE (S5):** reimportar o GLB exportado e verificar contagens, materiais e presença dos metadados (round-trip), com o digest do spec no ficheiro.

---

**F11 — Alavancas de forma: perfis por estação em vez de cápsulas**
- **PROBLEMA:** gerar membros com forma anatómica sem arte manual.
- **EVIDÊNCIA:** P2 `human/mesh.py`: `_profiled_capsule(..., profile, radial=16, rings=6, top_cap_scale, bottom_cap_scale)` com `profile(t)` a devolver multiplicador de raio, `t=0` proximal → `t=1` distal; `_torso_profile`, `_limb_profile`, e `_skull_shell(cy, half_h, profile, …)`. P6 `RealisticHumanBuilder._calculate_proportions()` deriva alturas (ombro, peito, cintura, quadril, joelho, tornozelo) de um canône "1/8 da altura" e constrói anéis por secção.
- **MECANISMO:** raio por estação = função explícita; a topologia é fixa (anéis × segmentos) e a forma vem de perfis.
- **PORQUE FUNCIONA:** é a nossa própria ideia, em versão simplificada — e o `top_cap_scale` do P2 resolve o mesmo problema que o nosso `pole_shrink` (evitar o "balão" do peito sobre o pescoço).
- **LIMITAÇÕES:** perfis são 1D por osso — sem campo de superfície, sem dedos, sem orelhas, sem dentes (P2 e P6 não têm nada disso); e a normal é derivada da posição, não da anatomia.
- **NOSSO EQUIVALENTE:** `MeshBuilder.loft` (estações), `DeformStack` (campos gaussianos/socket/ridge/capsule) e `Anatomy.skull_front_y(x,z)` — estritamente mais rico; a nossa dívida aqui é só a documentação do *porquê* de cada estação.
- **DECISÃO: MANTER** o modelo de campos (não migrar para perfis), **ADAPTAR** a ideia de *estação nomeada* para os pesos (F3) e **documentar** a tabela de estações como API pública (útil a testes e a rig).
- **TESTE (S3):** cada anel do corpo tem de estar associado a uma estação nomeada; um teste verifica que a contagem de estações é a mesma em todos os presets (já é: 5 821 v).

---

**F12 — Blendshapes de pose (corretivos) e a razão pela qual o LBS sozinho não basta**
- **PROBLEMA:** skinning linear deforma mal ombros/cotovelos; os projetos comerciais usam corretivos.
- **EVIDÊNCIA:** P5 `body_models.py` — `posedirs` (pose blend shapes) além de `shapedirs` (identidade) e da expressão; `lbs(lbs_weights, J, pose, shapedirs, posedirs, …)`; P2 resolve o mesmo com *blend zone* explícita na construção ("avoids candy-wrapper").
- **MECANISMO:** duas soluções reais para o mesmo problema — (i) dados corretivos por pose (SMPL-X) ou (ii) pesos escritos para nunca colapsar (P2). P1/P4 usam uma terceira: `sliding_joints.py` (P4) e *bendy bones*/constraints (P1).
- **PORQUE FUNCIONA:** cada uma ataca o artefacto na sua causa; nenhuma é gratuita.
- **LIMITAÇÕES:** corretivos exigem dados/autoria; pesos-por-construção exigem topologia simples; sliding joints exigem malha de referência bem comportada.
- **NOSSO EQUIVALENTE:** não temos rig; quando tivermos, `joint rings` explícitos (nossos) permitem as três opções.
- **DECISÃO: ADIAR a decisão para S3, com critério:** gerar pesos por construção (F3) + medir "candy-wrapper" (raio do anel vs. esperado) sob 60°; só se falhar se adiciona corretivo.
- **TESTE (S3):** medição de colapso a 60°/-40° (já definida em F3) — é isto que decide se precisamos de corretivos, em vez de os assumirmos.

---

### 3.3 Falhas e anti-padrões encontrados (procurados de propósito)

| Falha | Evidência | Classificação | Lição para nós |
|---|---|---|---|
| Malha-base imutável = lock-in total | P1: `weights.md` (índices), `rig.md` (estratégias de junta atadas à malha), mpfb targets | FACT | não congelar topologia; publicar tabela de identidade (F1) |
| Dados curados por índice de aresta | P3 `human/process/lod2.json`, `collar_edges.json`, `edges.json` | FACT | qualquer LOD que fizermos deve derivar de regiões/estações, não de listas de arestas |
| Asserções fracas (estado da API, não geometria) | P3 `tests/human/test_body.py`: `hash(...) != hash_before`, `len(keys>0.001) > 10` | FACT | os nossos pins de digest/audit são mais fortes — mantê-los |
| "Testes" que só imprimem | P6 `test_generator.py` (exporta e faz `print("[OK]")`) | FACT | nenhum teste nosso pode ter sucesso sem assert |
| Estado destruído e restaurado | P3 `_add_shapekeys_again` (implica que foram apagadas antes) | HYPOTHESIS (sobre fragilidade) | guardar sempre estado antes de operações irreversíveis (F9) |
| Tolerância silenciosa a campos desconhecidos | P1/P3 políticas declaradas; nosso `from_dict` ignora em silêncio | OBSERVED/ FACT nosso | avisar sempre (F8) |
| Exportação com duplicação de faces por grupo | P6 `export_obj`: para cada grupo itera *todas* as faces | HYPOTHESIS (não executado) | não copiar; se exportarmos grupos, testar contagens |
| Cápsulas como corpo | P2 `_capsule`/`_profiled_capsule` | FACT | usar só para *pesos*, nunca para forma |
| Sem normalização de ruído (nosso) | `fbm3` `... and 1.0` (Gate 02 §5) | CONFIRMED | contrato `|fbm3| ≤ 1` (S1) |

---

## 4. Comparação arquitetural

| Dimensão | Nós (HCG) | P1 MPFB2 | P2 2026-hbg | P3 HumGen3D | P4 CharMorph | P5 SMPL-X | P6 abir |
|---|---|---|---|---|---|---|---|
| Fonte da forma | anatomia → estações + campos | malha fixa + targets | perfis por osso | malha fixa + morphtargets | malha fixa + morphs | template + blendshapes estatísticos | proporções calculadas + anéis |
| Topologia | **gerada** (5 821 v constante) | congelada | gerada (cápsulas) | congelada | congelada | congelada | gerada (simples) |
| Identidade de vértices | *em falta* (§8 G1) | tabela de pesos + rig | implícita no gerador | tabela de edges (LOD) | pesos/grupos | **publicada** (`vertex_ids`) | implícita |
| Rosto/dentes/olhos/língua | **construídos** | assets | parcial (olhos/boca por ARKit) | assets | assets | blendshapes | não tem |
| Pesos | por fazer | ficheiro JSON | na construção | pintados/gerados? (`skin.py` só material) | álgebra de grupos (`vg_calc`) | ficheiro (LBS) | não tem |
| Rig | por fazer | JSON + estratégias CUBE/VERTEX | esqueleto + LBS | Rigify + helpers | rigging.py + sliding joints | esqueleto fixo | não tem |
| Expressões | planeadas (ARKit subset) | ARKit-52 + `!ex-` | ARKit-52 por canal | expressions | morphs | expressão/pose dirs | não tem |
| Testes | S0: 67 checks, pins | pytest headless + testdata | scripts de diagnóstico | pytest + fixtures | (não verificado) | (não verificado) | prints |
| Determinismo | digests por regime (2!) | não declarado | float32 fixo | não declarado | não declarado | dtype explícito | float nativo |
| Export | blend + report.json (S0) | bake+export | não encontrado (OpenGL) | export.py + LOD | assets `.blend` | n/a | OBJ + script |
| Versão de formato | **em falta** | 110, com upgrade | n/a | dicts compat | aliases YAML | n/a | n/a |

---

## 5. Problemas equivalentes: quem resolve o quê (matriz de decisão)

| Nosso problema | Melhor precedente | Classificação da solução | Decisão |
|---|---|---|---|
| Identidade de vértices/landmarks | P5 `vertex_ids`, P1 pesos | FACT | ADAPTAR (F1, F2) |
| Pesos de pele | P2 construção, P4 álgebra | FACT | ADOPTAR (F3, F4) |
| Soldadura/degenerados | Blender `dissolve_degenerate` (medido por nós) | MEASURED | ADOPTAR (F5) |
| Validação automática | P1 pytest headless, P3 fixtures | FACT | ADOPTAR+ADAPTAR (F6) |
| Diagnóstico numérico | P2 `anim_debug` | FACT | ADOPTAR com limiares (F7) |
| Versionamento de preset | P1 `version`, P3 `set_from_dict` | FACT | ADOPTAR (F8) |
| Shape keys × modificadores | P3 `_add_shapekeys_again` | FACT | ADOPTAR em S4 (F9) |
| Export com metadados | P1 bake+mask, P5 tabela | FACT | ADOPTAR (F10) |
| Forma de membros/tronco | P2 perfis, P6 proporções | FACT | MANTER o nosso (mais rico) (F11) |
| Correção de pose (candy-wrapper) | P5 posedirs, P2 blend zone, P4 sliding joints | FACT | MEDIR primeiro, decidir depois (F12) |
| Expressões | P1/P2 ARKit-52 | FACT | ADOPTAR em S4 |
| Nomenclatura anatómica | P7 `TA2.csv` | OBSERVED | ADIAR (custosa, sem necessidade atual) |

---

## 6. Soluções encontradas (síntese acionável)

1. **Tabela de identidade + âncoras locais** (F1/F2): `landmarks.json` por build, versionado, com âncoras baricêntricas opcionais. Custo pequeno, valor alto (rig, keys, vestuário futuro).
2. **Pesos por construção** (F3): usar a estação de cada anel; sem pintura; mede-se a qualidade por colapso a 60°.
3. **`dissolve_degenerate` em vez de soldadura global** (F5): medido, resolve a classe de defeito sem a criar.
4. **Pins de geometria como teste** (F6): já implementado em S0; é a nossa vantagem face a P1/P3.
5. **Relatório de validação com limiares** (F7): P2 imprime, nós falhamos — diferença deliberada.
6. **Formato versionado + leitura tolerante com avisos** (F8).
7. **Estado preservado em operações destrutivas** (F9): requisito de S4, princípio a partir de S2.
8. **Export com metadados de identidade** (F10).

## 7. Soluções que devemos evitar

1. **Congelar a topologia** para ganhar estabilidade de índices (P1/P3/P4): destrói a razão de existir do projeto; resolvemos o mesmo com F1 + F8.
2. **Ficheiros curados de índices de arestas** (P3 `lod2.json`): quebram a cada mudança de topologia; derivar de regiões.
3. **Cápsulas como corpo** (P2): usar só para pesos.
4. **"Testes" que imprimem** (P6) e **estado destruído/restaurado sem rede** (P3): a nossa regra é assert + estado guardado.
5. **`except Exception: pass`** (nosso `to_bmesh`): substituir por erro explícito ou contagem reportada.
6. **Soldadura global como limpeza por omissão** (medido: cria o defeito).
7. **Tolerância silenciosa** a campos desconhecidos.

## 8. Lacunas do nosso projeto (confirmadas por esta investigação)

| # | Lacuna | Impacto | Onde entra |
|---|---|---|---|
| G1 | Sem tabela landmark↔vértice | rig, keys, vestuário, interoperabilidade | S3 |
| G2 | Sem pesos de pele | validação de deformação (G5) impossível | S3 |
| G3 | Sem `format_version` nos presets; `from_dict` silencioso | presets antigos quebram em silêncio | S1 |
| G4 | Sem export (GLB) e sem metadados além do `report.json` | entrega ao utilizador | S5 |
| G5 | Sem shape keys/expressões | rosto inanimado | S4 |
| G6 | Sem LOD/qualidade | performance, produção | DEFER |
| G7 | Sem rig | validação G5 bloqueada | S3 |
| G8 | Sem suite de testes com pytest (só 1 ficheiro de aceitação) | regressões | S1 |
| G9 | Sem política numérica (float32 vs float64) | dois digests legítimos | S1/S2 |
| G10 | Sem política de estabilidade de API documentada | consumidores | S1 (documento de contrato) |

## 9. Testes que cada descoberta sugere

| Descoberta | Teste proposto | Fatia |
|---|---|---|
| F1 identidade | 20 specs × 3 presets: tabela landmark→índice idêntica; versão sobe se mudar | S3 |
| F2 âncoras locais | posição reconstruída por âncora vs. analítica < 1e-6 m (3 specs extremos + subsurf) | S3 |
| F3 pesos na construção | Σw=1±1e-6; colapso de anel < 10 % a 60°; sem auto-interseção a −40° | S3 |
| F4 junta = centróide | centróide do grupo vs. landmark < 2 mm nos 3 presets | S3 |
| F5 limpeza | non-manifold 36→0, loose 2→0, degeneradas 67→0, ngons ≤ 12, quads ≥ 0.86 | S2 |
| F6 pytest/pins | meta-teste: alterar um coeficiente de geometria tem de falhar o pin | S1 |
| F7 relatório | regressão injetada (ex.: clamp margin) detetada como falha | S6 |
| F8 versionamento | presets com chave desconhecida/ausente → aviso/erro claro; round-trip fingerprint igual | S1 |
| F9 keys × modificadores | keys intactas após subsurf; nenhuma mudança de contagem sem subir versão de contrato | S4 |
| F10 export | reimportar GLB: contagens, materiais e metadados iguais | S5 |
| F12 candy-wrapper | colapso medido antes de decidir corretivos | S3 |
| Gate 02 §5 | `|fbm3| ≤ 1`, `|ridged3| ≤ 1`; aresta de loft nunca degenerada | S1 |
| Gate 02 §6 | 0 flips de região estrutural (etiquetas por pertença, não por predicado de posição) | S2 |
| Regime numérico (S0) | digest idêntico dentro do regime; diferença entre regimes declarada e pinada (feito) | S1 (unificação) |

## 10. Plano S1→S6 atualizado

| # | Objetivo | Ficheiros | Teste/critério | Rollback |
|---|---|---|---|---|
| **S1** | Infra de testes: pytest, fixtures, contratos de `_math`/`rng`, versionamento de preset | `tests/conftest.py`, `tests/test_math.py`, `tests/test_spec.py`, `tests/test_topology.py`, `human_generator/spec.py` (`format_version` + loader com avisos) | pytest verde; pins S0 preservados; `|fbm3|≤1`; round-trip de preset; meta-teste de que o pin falha quando a geometria muda | apagar `tests/` + reverter loader |
| **S2** | Corrigir a fonte dos defeitos: anel 0 do globo; clamp não-colapsante; trocar soldadura por `dissolve_degenerate` (opt-in `weld`); audit reporta coincidências/loose; etiquetas de fronteira por estrutura | `generators/eyes.py`, `generators/mouth.py`, `core/topology.py`, `core/object.py` | non-manifold **36→0**; loose **2→0**; degeneradas **67→0**; ngons ≤ 12; 0 flips semânticos; render antes/depois; pins S0 atualizados *deliberadamente* | reverter slice (weld continua disponível) |
| **S3** | Rig derivado da construção: estações→pesos, juntas=landmarks, tabela de identidade + âncoras locais | `pipeline/rig.py`, `core/topology.py` (tag de estação), `human_generator/pipeline/assemble.py` (emitir `landmarks.json`) | Σw=1±1e-6; colapso <10 % a 60°; junta vs. centróide <2 mm; tabela estável em 60 builds | sem rig (export malha) |
| **S4** | Expressões ARKit-subset (Blink/Smile/Jaw/Brow) + política de preservação de estado | `pipeline/expressions.py` | keys intactas após subsurf; 3 expressões renderizadas; canais sem gancho = no-op declarados | remover keys |
| **S5** | Pipeline final: CLI (`spec → blend/glb/png`), export com metadados, guarda para Curves→mesh no glTF | `pipeline/__init__.py`, `tools/hcg_cli.py` | `--seed 42 --preset cyber_angel --out …` reprodutível (digests iguais em 2 execuções); round-trip do GLB | CLI fino |
| **S6** | Validação multi-seed com limiares + documentação de estado | `tools/validate.py`, `README.md` | matriz 8 seeds × 3 presets × extremos; zero asserts falhados; regressão injetada detetada | reverter relatório |

**Riscos maiores:** S2 muda os pins (é suposto) — tem de ser um ato explícito e documentado; S3 é a maior fatia (pesos + tabela de identidade); S4 depende de S3 e da política F9.

---

## Conclusão

A investigação confirma a tese do projeto com evidência externa: **ninguém gera topologia a partir de anatomia** — todos os pares estudados (MPFB2, CharMorph, HumGen3D, SMPL-X, 2026-hbg, abirmehmed) usam malha-base + morphs ou cápsulas, e pagam por isso com imutabilidade (P1/P3/P4) ou com forma pobre (P2/P6). Em troca, esses projetos resolvem melhor do que nós **identidade de vértices** (P5), **pesos sem pintura** (P2), **validação headless dentro do Blender** (P1/P3) e **versionamento de formato** (P1/P3). O S2 ficou resolvido por medição (`dissolve_degenerate`), o S3 tem agora um mecanismo com dois precedentes independentes (pesos na construção + junta por centróide), e o S0 deu-nos a infraestrutura onde estas ideias podem ser testadas em vez de acreditadas.

**S0 IMPLEMENTADO E VALIDADO.**
**INVESTIGAÇÃO COMPARATIVA CONCLUÍDA.**
**S1–S6 NÃO IMPLEMENTADOS.**
**AGUARDANDO NOVO PROCEED DO EDMUNDO.**
