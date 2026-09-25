# PRÉ-REGISTO — H7a × H4a: separar tamanho, forma e orientação da massa torácica

## Identificação

| campo | valor |
|---|---|
| BUILD | nenhum. **O gerador não foi alterado.** |
| COMMIT do controlo | `e6e809c` (igual a `e7df112` no gerador; o REF STUDY 02 só acrescentou docs e tools) |
| SEED / PRESET | 42 / `realistic_female`, gerado da árvore com `tools/refstudy/gen_blend.py` |
| ENV | Python 3.11 + `bpy 5.0.1` headless · numpy / scipy |
| Controlo do instrumento | `run_all.sh` → `metrics.txt` **idêntico** a `docs/h3h2_trunk/metrics_h3h2.txt`; `shape.json` e a tabela sagital idênticos aos versionados no REF STUDY 02 |
| Ferramentas | `tools/refstudy2/prereg_metrics.py` (métricas congeladas + calibração) · `tools/refstudy2/audit_bust.py` (auditoria só de leitura) |
| Dados congelados | `docs/prereg_h7a_h4a/criteria.json` (tolerâncias, valores do controlo, refs, sensibilidade rígida) · `baseline.json` · `baseline.txt` · `audit_bust.txt` |

**Pergunta única.** Como se distingue experimentalmente um problema de tamanho/forma da caixa torácica de um problema de orientação da massa torácica, sem que uma intervenção mascare o efeito da outra?

**Não incluído.**
- Nenhuma intervenção foi executada.
- H7a, H4a, H4b e H4c continuam **PAUSADOS**.
- Nada de BUILD, aumento de densidade ou refactor.
- Tudo o que está abaixo foi medido **só no controlo e nas referências**, para definir as métricas e o seu ruído antes de qualquer intervenção.

---

## 0. Factos novos encontrados ao preparar o pré-registo

Estes factos mudam o desenho da experiência.

| # | facto | rótulo | consequência para o desenho |
|---|---|---|---|
| F1 | Cada estação do tronco é parametrizada pelo **centro**; a parede posterior fica em `centro − depth·bs` (`core/topology.py: Section.point`) | FACT | encolher "à volta do centro" desloca as **costas** para a frente, o que altera as métricas de orientação sem que a orientação tenha sido mexida: **tamanho e orientação estão emaranhados pela parametrização** |
| F2 | `chest_half` alimenta ao mesmo tempo a largura e a profundidade das estações jugulum/busto/inframamária, **a profundidade da estação do deltoide** (`chest·0.62`) e a placa do esterno | FACT | "tamanho do tórax" não é hoje uma variável isolada: acopla o ombro (zona do H1) |
| F3 | `fs` da estação do busto = `1 + bust/(0.8·chest)`: a protrusão **absoluta** do busto mantém-se se o `chest` mudar | FACT | bom para isolar o tamanho: a massa anterior absoluta não muda com `k` |
| F4 | `front_scale` só atua na metade anterior da secção (`s ≥ 0`) | FACT | métricas feitas **só com a linha posterior** são imunes ao busto **por construção** |
| F5 | Aritmética da superelipse (p = 2): o `fs` = 1.404 da estação do busto desloca o centroide **24.4 mm para a frente**; a estação inframamária (71 mm abaixo) tem `fs` = 1, o que dá **≈ 19° locais** de inclinação "para a frente" do eixo do centroide | FACT (aritmético) | explica a divergência medida abaixo entre o centroide e a parede |
| F6 | Os dois lóbulos deformadores do busto estão **ambos em x = +0.1785** (os landmarks `nipple.*` e `bust.*` não multiplicam x por `sx`); z = 1.397 = **0.82·S** (soma `h·0.5`); y vem do fallback do elipsoide da **cabeça** | FACT (código + `audit_bust.txt`) | ver F7 |
| F7 | Efeito real dos lóbulos no controlo: **5 vértices em 24 986**, máximo 9.6 mm, a z = 0.80–0.82·S e \|x\| = 0.14–0.17 m (junto à **axila**, lado esquerdo; assimetria local de cerca de 10 mm) | MEASURED | a massa anterior do busto vem **quase toda do `fs`**. Os lóbulos são inertes para as métricas do tronco. Relação com o contrato de simetria S2: **UNKNOWN** (por verificar; registado como dívida, não corrigido) |
| F8 | O centroide diverge da parede posterior **só no nosso modelo** (tabela abaixo) | MEASURED | `C1` (eixo do centroide) **não é métrica válida de orientação** no nosso modelo |

**F8 em números (controlo, antes de qualquer intervenção):**

| | P2: corda torácica posterior (+ = inclinada para trás) | C1: eixo do centroide do tórax (+ = para trás) |
|---|---|---|
| Female base | +13.4° | +12.2° |
| FemaleChar | +13.5° | +29.4° |
| Body Topo | +17.0° | +11.9° |
| **nossa** | **+3.8°** | **−9.5°** |

Nas refs, o centroide e a parede têm o mesmo sinal. Na nossa, a parede inclina ligeiramente para trás e o centroide para a frente. Isto é consistente com F5 (INFERRED, forte).

Nota de convenção: no REF STUDY 02 o eixo do centroide usava o sinal inverso (+ = para a frente). Aqui, + = para trás em todas as métricas angulares.

---

## A. Variáveis independentes e confundidores

| variável | parâmetro no código (FACT) | é confundidora? de quê? | tratamento nesta experiência |
|---|---|---|---|
| **V1 tamanho transversal** | `chest_half` → larguras das estações jugulum / busto / inframamária | acoplada a V2, ao ombro (F2) e ao `fs` (F3) | manipulada em **E2** como fator único `k` |
| **V2 profundidade** | `chest_half × {0.72, 0.80, 0.70}` e `chest × 0.62` (deltoide) | confunde a **orientação** pela ancoragem ao centro (F1) | **junta com V1**. A razão profundidade/largura do controlo (0.892) já está dentro do ANSUR (0.798–1.045), por isso não há evidência para as separar |
| **V3 forma da secção** | `superellipse`, `bs` | **não confunde** extensões nem centroide: `width`/`depth` são extensões e `sup` é simétrico (bs = 1 no tórax). Só afeta fill e área. | **não manipulada.** Hipótese posterior, separada |
| **V4a massa anterior do busto** | `fs` da estação do busto | **confunde as métricas C** (F5, F8) e `D2` / `D1_z` (a cota do peito é a do busto) | **knock-out diagnóstico em E1** (não é candidata a correção) |
| **V4b colocação do busto** | estação a 0.762·S (o `chestheight` do ANSUR é 0.719·S); lóbulos mal colocados (F6) | confundidor potencial da orientação (massa alta) | **não manipulada**; limitada por cima pelo E1; dívida registada |
| **V5 orientação** | `y` por estação (quase constante) + `front_off`; `tangent` horizontal | é a variável do H4a | manipulada em **E3** como **cisalhamento sagital** das estações (a inclinação dos planos, V5b, fica para depois) |

**Princípio de separação (ENGINEERING JUDGMENT, com base anatómica FACT: as costelas articulam atrás com as vértebras torácicas).** Cada estação torácica é expressa em coordenadas ancoradas na coluna:

**parede posterior (linha da coluna) + profundidade para a frente + massa anterior**

- O **tamanho** (E2) muda a profundidade e a largura **com a parede posterior fixa**. Faz-se só com compensação de `y` por estação, dentro da representação atual.
- A **orientação** (E3) move a linha posterior (centros) **sem mudar larguras nem profundidades**.
- Assim, cada intervenção deixa invariante, por construção, a classe de métricas da outra, e essa invariância é verificada.

---

## B. Métricas congeladas

Definições em `prereg_metrics.py`. Cortes de 5 mm entre 0.44 e 0.84·S, grelha de 2 mm, suavização gaussiana com σ = 2 amostras. Tolerâncias em `criteria.json`: `max(3·SD do jitter sub-pixel, piso do instrumento)`, com pisos de 1° para ângulos, 5 mm para cotas, 2 mm para extensões e 0.01 para rácios.

### Classe D: geometria direta (extensões, independentes do referencial)

| id | definição | controlo | refs (fb / fc / bt) | tol |
|---|---|---|---|---|
| D1 | chest breadth **ao nível do ponto do busto** (cota da profundidade máxima do tórax, 0.72–0.80·S; definição ANSUR) | 352 @ z 1308 | 272 / 264 / 284 (as larguras das refs acima de 0.735·S são **inválidas**) | 2.9 |
| D2 | chest depth à mesma cota | 314 | 220 / 236 / 224 | 2.0 |
| D3 | profundidade mínima da cintura / máxima da nádega | 224 / 262 | 154, 176, 168 / 204, 232, 208 | 2.0 |
| D4 | largura máxima da anca (0.46–0.58·S) | 392 | 336 / 336 / (bt inválida) | 2.0 |
| D5 | chest / hip | 0.90 | 0.81 / 0.79 | 0.01 |
| D6 | profundidade peito / cintura; nádega / cintura | 1.40 / 1.17 | 1.43, 1.34, 1.33 / 1.32, 1.32, 1.24 | 0.01 |
| D7 | bideltoide (todas as peças, 0.79–0.83·S) e chest / bideltoide | 456 / 0.77 | refs: **inválido** (braços em T/A) | 3.0 / 0.01 |

Referências ANSUR (@1700): chestbreadth 281 (p5–p95 252–314); chestdepth 258 (216–307); chest/hip 0.763 (0.682–0.846); chest/bideltoid 0.598 (0.555–0.643); chest/biacromial 0.738 (0.664–0.824). **São restrições, não alvos.**

### Classe P: perfil posterior da linha média (imune à massa anterior por construção, F4)

Marcos: **G** = ápice glúteo (ponto mais posterior entre 0.44 e 0.58·S); **Tt** = ápice torácico (mais posterior entre 0.68 e 0.82·S); **L** = ponto lombar (mais anterior em relação à corda G–Tt).

| id | definição | invariância | controlo | refs | tol |
|---|---|---|---|---|---|
| **P3** | **flexão lombar = P1 + P2** (ângulo entre as cordas G→L e L→Tt) | translação ✓, rotação ✓ (0.45° por 3°) | **12.2°** | 29.7 / 26.1 / 33.9 | 1.0 |
| P1 | ângulo da corda pélvica G→L (+ = inclinada para a frente) | translação ✓, rotação ✗ (1:1) | 8.4° | 16.2 / 12.5 / 17.0 | 1.0 |
| P2 | ângulo da corda torácica L→Tt (+ = inclinada para trás) | translação ✓, rotação ✗ | 3.8° | 13.4 / 13.5 / 17.0 | 1.0 |
| P5 | concavidade lombar em relação à corda G–Tt (mm) | translação ✓, rotação ≈✓ | 19.4 | 54.5 / 52.0 / 67.8 | 2.0 |
| **P7** | **viragem total do contorno posterior entre G e Tt** (métrica de silhueta, invariante rígida) | ✓ / ✓ | 44° | 102 / 96 / 121 | 8.5 |
| P4 | cota de Tt / cota de G | ✓ / ≈ | 1313 / 943 | 1348, 1313, 1343 / 923, 853, 893 | 12 / 9.5 |
| P6 | y(G) − y(Tt) (+ = nádega à frente do tórax) | translação ✓, **rotação ✗ (19.6 mm por 3°)** | −9.6 | +8.6 / +20.4 / +15.2 | 2.0 |

### Classe C: dependem do centroide (incluem a massa anterior)

| id | definição | controlo | refs | tol |
|---|---|---|---|---|
| C1 | eixo do centroide, tórax 0.70–0.78·S (+ = para trás) | −9.5 | 12.2 / 29.4 / 11.9 | 1.0 |
| C2 | eixo do centroide, pelve 0.50–0.58·S | +3.2 | −6.1 / −11.6 / −10.7 | 1.0 |
| C4 | C1 − C2 | −12.7 | 18.3 / 41.0 / 22.6 | 1.4 |

### Classe F: posições absolutas (dependem do referencial)

F1 (y das costas no ápice torácico) e F2 (y do centroide na cota do peito) mudam **25 mm** com uma translação de 25 mm (medido). **Só relatório; nunca decidem.** O `buttock_behind_thoracic` do REF01 pertence a esta classe (é o artefacto do H3/H2).

**Distinção pedida.** Os critérios de decisão usam **só D e P**. C é diagnóstico (serve para medir o confundimento do busto). F é só relatório.

---

## C. Experiências mínimas

Todas são corridas de medição no mesmo harness, com o **gerador intacto** (override em tempo de execução num processo separado; `git diff` do gerador vazio antes e depois; digest do controlo verificado). Só a hipótese vencedora será depois implementada no gerador, **uma de cada vez**, com pins e testes.

| run | o que muda (e só isso) | papel | previsão pré-registada |
|---|---|---|---|
| **E0** | nada | controlo | valores de `criteria.json` (reprodução exata obrigatória) |
| **E1** | `fs` da estação do busto := 1.0 (lóbulos inalterados; inertes por F7) | **knock-out diagnóstico** de V4a: mede quanto de C e de D2 é busto. **Também é controlo positivo da imunidade da classe P.** | P: \|Δ\| ≤ tol. C1 **aumenta** (para trás) vários graus. D2 desce ≈ 57 mm antes da suavização (cerca de −17 %). |
| **E2** | escala `k = 0.85` na largura e profundidade de jugulum / busto / inframamária, **com a parede posterior fixa** (compensação de `y`); protrusão absoluta do busto mantida (F3); profundidade da estação do deltoide **congelada** no valor do controlo; placa do esterno acompanha a parede anterior | **H7a** (tamanho) | D1 −15 % ± 3 % (≈ 299); D2 −12.5 % ± 3 % (≈ 275); D5 ≈ 0.76; D7 ≈ 0.66; **P: \|Δ\| ≤ tol**; C muda (**não conta como orientação**) |
| **E3** | cisalhamento sagital das estações do tronco (definido abaixo); larguras e profundidades intactas | **H4a** (orientação) | P1 +6.9° ± 2°; P2 +10.9° ± 2° (verificações de manipulação); **D: \|Δ\| ≤ tol**; P4 \|Δ\| ≤ tol |
| **E4** | E2 + E3 | interação | **só é executada se** E2 violar a invariância P **ou** E3 violar a invariância D |

**Porquê `k = 0.85`** (relacional, não um alvo ANSUR absoluto): chest/hip do ANSUR (0.763) × a nossa anca (392) = 299 mm, e 299 / 352 = 0.85. Com `k` = 0.85, chest/biacromial fica ≈ 0.80, dentro de p5–p95 (0.664–0.824). Não há iteração sobre `k`.

**Porquê ancorar na parede posterior** (previsão aritmética a partir do código). Um H7a "ingénuo", ancorado ao centro, com `k` = 0.85, move as costas das estações torácicas ≈ 19–21 mm para a frente e não mexe na cintura. Isso faria descer P2 cerca de 5.6° e reduzir P5: **o H7a pareceria piorar a curva sem mexer na orientação**. É exatamente o mascaramento que este desenho evita.

**Definição do cisalhamento do E3** (Δy aplicado aos centros das estações; + = para a frente). As magnitudes vêm da diferença entre o controlo e a média das refs em P1 e P2.
- **Pelve:** pivô na estação `hip_flare` (≈ cota do ápice glúteo), com Δθp = 6.89°.
  - `hip_flare`, `hip` e `crotch`: Δy = 0 (**glúteo intocado**, sem invadir H4b/H4c).
  - `navel`: +7.4 mm; `waist`: +14.2 mm.
- **Tórax:** Δθt = 10.85° acima da cintura; a componente pélvica mantém-se constante acima da cintura.
  - `inframammary`: total −13.5 mm; `bust`: total −27.2 mm.
  - Descida linear até Δy = 0 na **linha do deltoide**: `jugulum` −9.2 mm; deltoide, rampas do trapézio e pescoço: 0.
- Resultado: pescoço, ombros, braços, cabeça e pernas **não mudam**. A linha de prumo de C7 sobre as ancas mantém-se (equilíbrio sagital: a coluna equilibra-se sobre as ancas, [Legaye et al. 2002](https://ncbi.nlm.nih.gov/entrez/query.fcgi?amp=&amp=&amp=&cmd=Retrieve&db=PubMed&dopt=Abstract&list_uids=11931071)).
- A escolha do pivô é um grau de liberdade que **P3 não determina**. Fica declarada e monitorizada: prevê-se que `upper_back_vs_occiput` (H1) **piore ≈ 15–20 mm** (interpolação entre busto −27.2 e jugulum −9.2 à cota 1330 ≈ −16 mm).

**Nota: P1 e P2 no E3 são verificações de manipulação, não critérios de sucesso.** A magnitude foi escolhida a partir delas. Os critérios de sucesso do H4a são as métricas **emergentes** (P5, P7, P6), que não foram usadas para calibrar.

---

## D. Critérios de decisão (congelados antes de executar)

**Validade do instrumento (obrigatória, antes de interpretar o que quer que seja):**
- E0 reproduz `criteria.json` exatamente.
- No **E1**, todas as métricas P têm \|Δ\| ≤ tol.

Se o E1 mexer em P para lá da tolerância, **a classe P não é imune ao busto**. Nesse caso paro, corrijo o instrumento e pré-registo de novo.

**H7a ganha suporte se, no E2, se cumprir tudo o que segue:**
1. Manipulação: D1 −15 % ± 3 % e D2 −12.5 % ± 3 %. Se falhar, a implementação é inválida; isso **não** é falha do H7a.
2. D5 (chest/hip) dentro de 0.682–0.846 **e** chest/biacromial dentro de 0.664–0.824 **e** D2 ≤ 307 (p95).
3. D7 (chest/bideltoid) ≤ 0.70 conta como suporte parcial; ≤ 0.643 como suporte total. O deltoide não é mexido, por isso **não se espera** chegar a 0.598.
4. **Separabilidade:** \|ΔP1\|, \|ΔP2\|, \|ΔP3\| ≤ 1°; \|ΔP5\| ≤ 2 mm; \|ΔP4\| ≤ tol.
5. Sem regressões (secção E).

**H4a ganha suporte se, no E3, se cumprir tudo o que segue:**
1. Manipulação: P1 +6.9° ± 2° e P2 +10.9° ± 2°. Se falhar, a implementação é inválida.
2. **Emergentes:**
   - P5 ≥ 36 mm (≥ 50 % do intervalo até à ref mínima de 52);
   - P7 ≥ 70° (≥ 50 % do intervalo até à ref mínima de 96);
   - P6 > 0 (nádega à frente do ápice torácico). P6 é sensível a rotação, mas o E3 não roda o referencial (pernas idênticas), por isso é aceitável.
3. **Separabilidade:** \|ΔD1\|…\|ΔD4\| ≤ tol e \|ΔP4\| ≤ tol (a orientação não deve mudar tamanhos nem as cotas dos ápices).
4. Sem regressões (secção E).
5. Monitorizado: se `upper_back_vs_occiput` piorar mais de 10 mm, é **conflito com o H1**. Tem de ser reportado e bloqueia a implementação até ser resolvido, mas não falsifica sozinho o H4a.

**Interação:**
- Declara-se se o E2 violar o critério H7a-4 **ou** o E3 violar o H4a-3.
- Nesse caso executa-se o E4. Para cada métrica primária (D1, D2, D5, P3, P5, P7) calcula-se `I = Δ(E4) − (Δ(E2) + Δ(E3))`. **Interação confirmada** se \|I\| > tol em alguma delas.
- A ordem de implementação passa a ser: primeiro a intervenção cujo efeito **não muda** na presença da outra, ou seja, cujo Δ no E4 difere menos do Δ isolado.
- Sem interação: a ordem é indiferente para as métricas. Recomenda-se o H7a primeiro por ser a menor alteração de código.

**Confundimento do busto (E1):**
- Se \|ΔC1(E1)\| ≥ 6.7° (≥ 50 % da divergência C1 − P2 de 13.3°) com P dentro da tolerância, **confirma-se que as métricas C do nosso modelo são dominadas pela massa anterior**. As decisões de orientação usam só P.
- A colocação e o emparelhamento do busto (V4b / H7b) passam a hipótese própria, **não misturada** com o H7a nem com o H4a.

**O que fica UNKNOWN, seja qual for o resultado:**
- se uma orientação ao nível das refs **se lê** como humana (os renders são evidência secundária, mostrados mas não decisivos);
- a forma posterior da pelve (H4b: não convexa, impossível de testar aqui);
- o bideltoide das refs, a inclinação da base do pescoço e o máximo de 244 mm na base do pescoço;
- se `k` = 0.85 serve à Lucia (isso será CharacterSpec, mais tarde);
- a variação civil fora da população do ANSUR;
- o efeito da altura do busto (V4b), que não é manipulada;
- a inclinação dos planos das estações (V5b), que também não.

---

## E. Invariância: verificações obrigatórias em cada run

1. **Identidade de vértices por peça.** As peças que não são alvo (cabeça, braços, mãos, pernas, pés) têm de ser **idênticas bit a bit** ao controlo (max \|Δ\| = 0). Na casca do tronco:
   - identidade **exata na cage** para as estações não modificadas;
   - na malha subdividida, identidade fora do suporte da Catmull-Clark (±2 anéis das estações modificadas).
2. **Referencial.** As comparações intra-modelo fazem-se **no referencial bruto do gerador** (sem centralização por caixa envolvente). As métricas D e P são também calculadas no referencial do REF01; se diferirem entre referenciais mais do que a tolerância, a métrica é declarada dependente do referencial e **não decide**.
3. **Postura e normalização.** O y da canela a 0.12·S e o fator de escala (zmax, com a cabeça intocada) têm de ser idênticos ao controlo (Δ = 0). Se não forem, a comparação é inválida.
4. **Instrumento.** O E1 funciona como controlo positivo da classe P. O jitter sub-pixel já está medido (`criteria.json`). Qualquer mudança numa região não alterada é investigada primeiro como centralização, caixa envolvente, instrumento, postura ou normalização, pela regra do H3/H2.
5. **Garantias S2/S3.** Integridade, chão, simetria (`mirror_stats`), mãos/pés, junções J1–J5, determinismo, contratos e pins. Nas corridas de medição são reportadas; na implementação posterior, `s0` 33/33, bpy 72/72 e pytest 133 / 1 skipped / 1 xfailed são obrigatórios. Uma quebra é **regressão**, não efeito colateral.

---

## Dívida registada (não resolver agora)

- **Arquitetura:** 85 ilhas sobrepostas contra cascas integradas nas refs (REF STUDY 02).
- **Representação:** estações convexas, sem sulcos nem lobos (H4b, H7b, escápulas); `ring_n = 16`; densidade na cabeça.
- **Busto** (F6/F7):
  - os landmarks `nipple.*` / `bust.*` não usam `sx`, somam `h·0.5` em z e tiram y da função do crânio;
  - os lóbulos atuam na axila esquerda;
  - relação com o contrato de simetria **UNKNOWN**.

  Fica fora do âmbito, por ser uma variável própria (V4b). Tem de ser tratado antes de qualquer hipótese sobre o busto e **não** pode entrar no H7a nem no H4a.
- **Planos de estação inclinados (V5b):** o código já os suporta (`Section.tangent/front`), mas não são usados no tronco.

## Reprodução

```bash
PY=/home/user/.venv-hcg/bin/python
HCG_BUILD_FROM_TREE=1 HCG_REFSTUDY_WORK=out/rs2 PY=$PY bash tools/refstudy/run_all.sh   # controlo
HCG_REFSTUDY_WORK=out/rs2 $PY tools/refstudy2/prereg_metrics.py                          # baseline + calibração
$PY tools/refstudy2/audit_bust.py                                                         # auditoria (da raiz do repo)
```
