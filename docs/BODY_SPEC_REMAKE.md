# BODY_SPEC_REMAKE — directriz do dono (2026-10-06, permanente)

> Registo da directriz recebida após o E1 (texto integral do dono em
> mensagens da sessão; paráfrase estruturada — discrepâncias devem ser
> apontadas e corrigidas aqui). Governa o REMAKE (docs/REMAKE_01.md) a
> partir de agora, em conjunto com MANDATE.md e OPERATING_MODE.md.

## 1. Diagnóstico adoptado (valida o REMAKE)

- O modelo actual (caminho estações+campos, t1) é um **"humanoide procedural
  com silhueta vagamente feminina"** — a feminilidade deriva de relações
  globais de largura (cintura/quadril), não de estrutura anatómica.
- **"Estrutura mamária NÃO DEMONSTRADA"**: não classificar uma região como
  anatomia presente só porque existe um volume semântico destinado a ela —
  classificar pelo que a GEOMETRIA demonstra (duas massas, dois centros,
  sulco, polos, base, continuidade mama→tórax).
- O corpo tem "linhas de mudança de componente" (o olho vê a TRANSFORMAÇÃO
  entre peças) em vez de **continuidade de forma** progressiva.
- Mais polígonos ≠ mais anatomia (563k verts = manequim de 563k verts).
  **O problema está na função que determina a forma.**

## 2. A pergunta-critério (regra permanente)

> **"Que estrutura anatómica causa este volume e como a sua influência se
> propaga para as estruturas vizinhas?"**

Se a resposta for "um parâmetro que aumenta X" — insuficiente. Queremos
anatomia FUNCIONAL para geração de forma: estrutura → massa → consequência
de superfície (NÃO gravação muscular / atlas anatómico).

## 3. Hierarquia de construção (níveis respeitam os anteriores)

```
N0 esqueleto (crânio, coluna, costelas, pelve, ossos longos)
N1 massas primárias (tórax, abdómen, pelve, membros)
N2 massas anatómicas (trapézio, deltoide, peitoral, glúteos, coxa...)
N3 tecido mole (gordura, mamas, subcutâneo)
N4 superfície (pele, dobras, compressão, microforma)
```

**Regra dos níveis (Primary/Secondary/Tertiary): o nível seguinte NUNCA
corrige o anterior** — silhueta errada → volta ao N1; massa errada → N2;
superfície errada → N4.

## 4. Transições como cidadãs de primeira classe

Anatomia convincente = `A → transição → B → transição → C`, não `A+B+C`.
As transições têm de ter explicação anatómica. Medir continuidade:

```
C = f(d, θ, κ)    d=distância entre superfícies, θ=mudança de orientação,
                  κ=mudança de curvatura
```

Cadeias prioritárias: pescoço→trapézio→ombro→braço; tórax→abdómen→pelve;
pelve→glúteo→coxa.

## 5. Parametria (não universais, INTERVALOS)

- Tudo normalizado pela estatura H; parâmetros como fracções com bandas
  [Pmin, Pmax] (ANSUR + refs).
- A mulher NÃO é `masculino × 0.9`: as diferenças vivem na DISTRIBUIÇÃO de
  volumes e nas TRANSIÇÕES.
- Parâmetros independentes por região (W/D do tórax, cintura, pelve,
  projeção glútea, coxa) — não um flag "female".

## 6. Loop de escultura com erro hierárquico

```
parâmetros → gerador → malha → render → MEDIÇÃO → comparação → erro → ajuste
E = ws·Es(silhueta) + wp·Ep(proporção) + wa·Ea(anatomia) + wc·Ec(continuidade) + wv·Ev(visual)
ordem: Es → Ep → Ea → Ec → Ev  (nunca começar pelo microdetalhe)
```

## 7. Avaliação

- Multi-vista obrigatória: frente, costas, perfil, ¾ frente, ¾ costas,
  close-up — câmara/luz/escala controladas.
- **Clay cinzento primeiro** (sem textura/cabelo/roupa/luz dramática — luz
  bonita esconde forma má).
- Assimetria controlada `R = L + ε` (ε pequeno e estruturado, NÃO ruído).

## 8. Especificação de trabalho (a frase do dono para o agente)

> "Construa e valide um modelo paramétrico de anatomia feminina plausível,
> separando evidência anatómica, medidas, hipóteses e julgamento visual.
> Não altere o gerador validado antes de demonstrar que o mecanismo actual
> consegue representar as variáveis. Primeiro determine quais parâmetros
> realmente controlam cada região, depois demonstre efeito causal por
> experimento A/B."

## 9. Mapeamento para os estágios do REMAKE

| directriz | estado |
|---|---|
| autópsia do gerador (famílias isoladas, A/B causal) | FEITO (MECHANISM_AUDIT_01, SWEEP_01 verificação, B2/E1 A/B) |
| N1 massas primárias como VOLUMES | E1 feito (SDF: parede + lóbulos + fossa) — gate pendente |
| transições com métrica C=f(d,θ,κ) | FEITO 2026-10-06 — transition_report.py + transition_kappa.png |

### Execução da directriz de transições (2026-10-06, MEASURED)

κ_max por zona (1/km; refs = banda real005/femalebase/femalechar):

| zona | refs | V0 antigo | E1 | leitura |
|---|---|---|---|---|
| Z1 clavícula→tórax | 29–47k | 242k | 185k | **4–7× refs em TODAS as versões — pior breakpoint** |
| Z4 cervical→torácica | 25–32k | 180k | 229k | idem (costas) |
| Z5 torácica→lombar | 12–18k | 49k | **22k** | E1 2× melhor (loft suave funcionou) |
| Z6 lombar→sacro | 12–27k | 87k | 38k | melhor, ainda fora |
| Z3 abdómen→pelve (frente) | 20–73k | 2.9k | 10k | E1 SUB-curvado (frente demasiado recta) |
| Z2/Z7/Z8 | — | — | em banda | arco costal / sacro-glúteo / glúteo-coxa |

**Alvos do E2 (por ordem de severidade):** (1) cintura escapular + trapézio
como VOLUMES (Z1/Z4 — o "ombro=conector mecânico" do diagnóstico);
(2) curva lombar/sacral no loft (Z5/Z6); (3) arco costal→abdómen frontal
(Z2/Z3 — a frente recta). Painel: docs/head_phaseA/transition_kappa.png.
| multi-vista clay | painéis e1_gate*.png (numpy rig) — a estender a ¾/costas |
| parametria em bandas | specs medidas (breast_spec_v3; faltam as outras massas) |
| N2 masses anatómicas (ombro/glúteo) | E3 planeado |
| loop de erro hierárquico | a construir sobre os instrumentos existentes |

A ordem de execução fica: **transições primeiro (E2)** — a directriz
coloca continuidade acima de detalhe.
