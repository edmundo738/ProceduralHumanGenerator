# RESULTADOS — pré-registo H7a × H4a (E0 → E1 → E2 → E3)

## Identificação
- **BUILD:** nenhuma. São corridas de medição; o gerador não foi alterado.
- **COMMIT:** base 8b6bb79, que contém o pré-registo congelado (`docs/PREREG_H7A_H4A.md`, `docs/prereg_h7a_h4a/criteria.json`).
- **SEED / PRESET:** 42 / `realistic_female`.
- **ENV:** bpy 5.0.1 headless (`tools/headless_blender.py`), numpy/scipy.
- **Harness:** `tools/refstudy2/prereg_run.py` gera as variantes. Faz o override em tempo de execução, num processo separado, de `Anatomy.trunk_sections` e, só no E2, da placa esternal em `DeformStack.bump`. Guarda o SHA-256 das fontes do gerador antes e depois.
- **Avaliação:** `tools/refstudy2/prereg_eval.py all`. Usa o mesmo instrumento congelado: `prereg_metrics.metrics` e o `measure.py` + `metrics.py` do REF01, sem alterações.
- **Dados:** `docs/prereg_h7a_h4a/results/`. Contém `results.json`, `run_log_E*.json`, `ref01_metrics_E*.txt`, o diagnóstico `run_log_diag_E2_noplate.json` e `profiles_E0_E3.png`.
- **E4:** não executado. Ver §5.

**Objetivo (uma pergunta):** distinguir experimentalmente um problema de tamanho/forma da caixa torácica (H7a) de um problema de orientação da massa torácica (H4a), sem que uma intervenção mascare a outra.

> `k = 0.85` é uma **condição experimental**, não uma proporção anatómica validada, e não passa a constante. O pivô do E3 e os limiares são escolhas experimentais, não verdade anatómica.

---

## 1. Validade das corridas (verificado em todas)

| verificação | E0 | E1 | E2 | E3 |
|---|---|---|---|---|
| fontes do gerador idênticas (SHA-256 antes = depois) | ✔ | ✔ | ✔ | ✔ |
| só a intervenção planeada (estações alteradas, conforme `run_log`) | nenhuma; digest do pin `c7ab2932f5d66ede` | bust `fs` 1.404 → 1.0 | jugulum, bust, inframammary: w,d ×0.85; y compensado; bust `fs` → 1.476; placa −41.15 mm | y de navel +7.40, waist +14.17, inframammary −13.52, bust −27.21, jugulum −9.25 |
| E0 = baseline congelado | Δ = 0.0 em todas as métricas (pré-registo e REF01); raw bit-idêntico ao controlo | | | |
| peças não-alvo (84 de 85 componentes) | — | 0.0 exato | 0.0 exceto 24/30: 0.071 mm (a) | 0.0 exato |
| cage: estações não modificadas | — | só `bust` muda | jugulum/bust/infra mudam; resto ≤ 0.07 mm (a); deltoide frontal 2.69 mm (a) | só as 5 planeadas mudam; deltoide, hip_flare, hip e crotch = 0 |
| postura e escala: zmax, zmin, y da canela a 0.12·S | idênticos | idênticos | idênticos | idênticos |
| contratos S2/S3 (J1–J5 13/13, 85 componentes, 0 flutuantes, 962 arestas de fronteira, 464 sobreposições, chão na sola) | ✔ | ✔ | ✔ (espelho: falhas 158 → 154) | ✔ |
| instrumento idêntico | ✔ | ✔ | ✔ | ✔ |

(a) **Atribuído por diagnóstico.** Repetiu-se o E2 sem re-ancorar a placa (`HCG_PREREG_DIAG=noplate`). Nessa corrida a fuga fora do tronco é exatamente 0: componentes 0, cage fora do tronco 0, deltoide 0. Toda a fuga vem da cauda gaussiana da placa esternal (σ = 48/34/85 mm). Como a placa acompanhar a parede anterior faz parte do E2 pré-registado, isto é um efeito da intervenção planeada, não contaminação.

**Artefacto de instrumento identificado.** O REF01 mostra "mudanças" em E1–E3 em regiões intocadas: circunferência do joelho e da barriga da perna, `occiput_z`, `headlength`. Os vértices dessas peças são **bit-idênticos**. A origem é a centragem pela caixa envolvente do REF01 somada à grelha de 2 mm. Pela regra E.2, as decisões fazem-se no referencial bruto.

---

## 2. Tabela principal

Valores no referencial **bruto** (decisão), à escala de 1700 mm. Entre parênteses, o valor no REF01 quando difere. Tolerâncias em `criteria.json`.

| métrica | E0 | E1 | E2 | E3 | critério congelado | resultado | interpretação |
|---|---|---|---|---|---|---|---|
| **E1: instrumento** P1…P7 \|Δ\| | — | 0.00 (P7 REF01 +0.19) | | | ≤ tol | **PASS** | a classe P é imune à massa anterior do busto |
| E1: ΔC1 (°) | −9.50 | **+6.41** | | | \|Δ\| ≥ 6.7 | **FAIL (por 0.29°)** | o busto explica cerca de 48% da divergência C1−P2 (13.3°); "C dominado pelo busto" não fica confirmado pelo limiar |
| E1: D2 | 312 (314) | 276 | | | previsão −57 mm "antes da suavização" | não comparável | medido −36 mm (−11.5%) depois da subdivisão |
| **E2: manipulação** D1 | 352 | | **296 (−15.9%)** | | −15% ± 3% | **PASS** | |
| E2: manipulação D2 | 312 (314) | | **274 (272): −12.2% (−13.4%)** | | −12.5% ± 3% | **PASS nos dois referenciais** | D2 fica sinalizado como dependente do referencial no E2 (Δ difere 4 mm > 2), mas o veredito é o mesmo nos dois |
| E2: D5 chest/hip | 0.898 | | **0.755** | | 0.682–0.846 | **PASS** | |
| E2: chest/biacromial (INFERRED; biacromial = parâmetro da spec, 387.7 mm) | 0.908 | | **0.763** | | 0.664–0.824 | **PASS** | |
| E2: D2 ≤ 307 | 312 | | 274 | | ≤ 307 | **PASS** | |
| E2: D7 chest/bideltoid | 0.772 | | **0.649** | | ≤ 0.70 parcial; ≤ 0.643 total | **PARCIAL** | o deltoide não foi mexido (previsto) |
| E2: separabilidade ΔP1 / ΔP2 / ΔP3 | | | 0.00 / +0.31 / +0.31 | | ≤ 1° | **PASS** | |
| E2: ΔP5 / ΔP4 (tórax, glúteo) | | | +0.48 / 0 / 0 | | ≤ 2 mm / ≤ tol | **PASS** | o tamanho não mexeu na curva posterior |
| **E3: manipulação** ΔP1 | 8.54 | | | **+3.38** | +6.9° ± 2° | **FAIL** | calibração errada no desenho (§4) |
| E3: manipulação ΔP2 | 3.85 | | | **+8.29** | +10.9° ± 2° | **FAIL** | calibração errada no desenho (§4) |
| E3: P5 concavidade (mm) | 19.5 | | | **37.6** | ≥ 36 | PASS* | *a manipulação é inválida, por isso não decide |
| E3: P7 viragem (°) | 46.5 | | | **67.7** | ≥ 70 | FAIL* | *idem |
| E3: P6 glúteo − ápice torácico (mm) | −10.3 | | | **+11.4** | > 0 | PASS* | *idem |
| E3: P3 flexão lombar (°) | 12.4 | 12.4 | 12.7 | **24.1** | (monitorizado) | — | refs 26.1–33.9 |
| E3: separabilidade D1 | 352 | | | **348 (−4)** | \|Δ\| ≤ 2.94 | **FAIL formal** | investigado pela regra E.4: no corte vetorial exato Δlargura = **−0.45 mm** em z 1293–1313; os −4 são 2 píxeis de quantização da grelha |
| E3: D2 / D3 cintura / D3 nádega / D4 | | | | +2 / −2 / 0 / 0 | ≤ tol | PASS (D2 e D3 no limite) | |
| E3: ΔP4 ápices z | | | | −5 / 0 | ≤ 12 / 9.5 | **PASS** | |
| **E3: upper_back_vs_occiput** (mm) | −52 | −52 | −52 | **−70** (vértices brutos: −51.98 → −69.02) | piorar > 10 mm = conflito com H1 | **CONFLITO** (≈ −17…−18) | previsto ≈ −16; bloqueia a implementação; não foi compensado |

---

## 3. Registo do E3 (exigido)

- **Pivô:** estação `hip_flare`. Δy = 0 em hip_flare, hip e crotch, e na linha do deltoide para cima.
- **Estações afetadas (Δy planeado → Δ observado na linha média posterior, subdividida):**

| estação | Δy planeado | Δ observado |
|---|---|---|
| navel | +7.4 | +8 |
| waist | +14.2 | **+10** |
| inframammary | −13.5 | −12 |
| bust | −27.2 | **−22** |
| jugulum | −9.2 | −8 |

- **Estações intocadas:** deltoid_line, hip_flare, hip, crotch, pescoço/cabeça (3 estações) e rampas do trapézio (2). Confirmado na cage (Δ = 0) e nos vértices de todas as outras peças (Δ = 0).
- **Linha posterior:**
  - o ápice torácico recua cerca de 21 mm e desce de z 1308 para 1303;
  - a lordose avança cerca de 10 mm;
  - o ápice glúteo fica intocado (z 943, Δ 0).
- **Flexão lombar P3:** 12.4° → 24.1° (+11.7°).
- **upper_back_vs_occiput:** −52 → −70 mm (Δ −18 no REF01; −17.0 nos vértices brutos, com o occipital idêntico).

## 4. Porque falhou a manipulação do E3 (MEASURED + INFERRED)

1. **O desenho estava mal calibrado.** Assumi que ΔP1 = Δθp. Mas o ápice glúteo G (z 943) fica **abaixo do pivô** (z 972), e as cordas vão de marco a marco (G→L→Tt), não de estação a estação. Refazendo a conta com os marcos, dá ΔP1 ≈ 3.6° e ΔP2 ≈ 8.6°, próximo do observado (3.4° / 8.3°).
2. **A superfície atenua o cisalhamento.** A Catmull-Clark e a interpolação entre anéis atenuam os picos do perfil de Δy em cerca de 25–30% (waist e bust).

É um erro meu no pré-registo, não uma falha do H4a. Pelo critério congelado, *"se falhar, a implementação é inválida"*.

## 5. E4: gatilho formal disparou, mas não foi executado

- A regra congelada diz: interação declarada se o E3 violar H4a-3, e então executa-se o E4. O D1 viola por 1.06 mm acima da tolerância.
- **Não executei o E4, por três razões:**
  - a violação é quantização de instrumento (Δ geométrico −0.45 mm), identificada pela regra E.4;
  - o E3 é inválido por manipulação, e um E4 = E2 + E3 herdaria essa invalidez;
  - a instrução é que o E4 não é automático e que a interpretação causal é feita contigo antes de avançar.
- Fica **para tua decisão**.

## 6. Conclusões

| afirmação | estado |
|---|---|
| A classe P é imune à massa anterior do busto (E1) | **supported** |
| As métricas C são dominadas pelo busto (limiar 6.7°) | **inconclusive** (6.41°: cerca de 48% da divergência; abaixo do limiar) |
| H7a: tamanho do tórax reduzível sem mexer na orientação posterior | **supported** (critérios 1, 2, 4 e 5; critério 3 parcial) |
| H4a: a orientação corrige a curva posterior | **inconclusive** (manipulação inválida; resultados emergentes a cerca de 50–75% da dose: P5 e P6 passam, P7 falha) |
| Separabilidade tamanho ↔ orientação | **supported** no sentido E2 → P. No sentido E3 → D: geometricamente sim (−0.45 mm), formalmente FAIL por quantização |
| Interação H4a ↔ H1 (costas altas vs occipital) | **supported como conflito**: −17 mm > 10 mm; bloqueia a implementação do H4a tal como desenhado |

**UNKNOWN:**
- se a orientação ao nível das refs se lê como humana;
- a forma posterior da pelve (H4b);
- o bideltoide das refs;
- o máximo de 244 mm na base do pescoço;
- se k = 0.85 serve à Lucia;
- a variação civil fora do ANSUR;
- o efeito da altura do busto (V4b);
- a inclinação dos planos das estações (V5b);
- o efeito do E3 à dose planeada.

**Observação (E2, não é critério).** D3, a profundidade mínima da cintura, desce 8 mm, porque o anel interpolado entre waist e inframammary encolhe. A cintura propriamente dita não mudou (0.07 mm na cage).

## Reprodução
```
PY=/home/user/.venv-hcg/bin/python
HCG_BUILD_FROM_TREE=1 HCG_REFSTUDY_WORK=out/rs2 PY=$PY bash tools/refstudy/run_all.sh     # controlo + refs
for v in E0 E1 E2 E3; do $PY tools/headless_blender.py run tools/refstudy2/prereg_run.py -- $v out/prereg/$v; done
HCG_PREREG_DIAG=noplate $PY tools/headless_blender.py run tools/refstudy2/prereg_run.py -- E2 out/prereg/diag_E2_noplate
$PY tools/refstudy2/prereg_eval.py all
```
