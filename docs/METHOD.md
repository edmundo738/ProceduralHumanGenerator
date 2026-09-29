# MÉTODO HCG — o ciclo de engenharia (v2, pós-CONT1)

Este documento é o **contrato de processo** do HCG. Complementa (não substitui)
`DEVELOPMENT_AGREEMENT.md` (formato de build, classificação FACT/MEASURED/…).
Foi consolidado a partir da direção do dono do projeto em 2026-09 (CONT1).

> **2026-09-29 — leitura obrigatória ANTES deste ciclo:** `OPERATING_MODE.md`
> (modo de operação Arena↔dono↔projeto: pedido literal vs problema real,
> FALSE IMPROVEMENT, estudo de referências como modelo externo de
> compreensão, sistemas antes de regiões) e `CHECKPOINT_2026-09-29.md`
> (auditoria do método, métricas e geometria; hipóteses do torso; plano
> T-TORSO SISTEMA). O ciclo abaixo continua a ser o detalhamento técnico; o
> OPERATING_MODE acrescenta o que vem antes (contexto, problema real,
> evidência, estudo) e a classificação de resultados no passo de REVIEW.

## O ciclo (16 + 1 passos)

    01 CONTEXT      ler STATE.md + docs do checkpoint anterior
    02 BASELINE     congelar a versão anterior (digest + métricas + renders)
    03 OBSERVATION  ver o que está errado (render + DISTÂNCIA/PROXIMIDADE)
    04 MEASUREMENT  medir o problema (instrumento comum, nós vs refs)
    05 REFERENCES   comparar sempre com as refs estudadas
    06 HYPOTHESIS   explicação testável (falsificável, com critérios ANTES de medir)
    07 INTERVENTION a menor alteração estrutural adequada
    08 RENDER       evidência visual (vista padrão, ver abaixo)
    09 COMPARISON   antes × depois × refs (painéis, mesma câmara/luz)
    10 METRICS      re-executar as métricas
    11 REGRESSION   o que NÃO devia mudar mudou? (digests, confinamento, testes)
    12 REVIEW       procurar falhas que os testes não acham (auditoria)
    13 REFINEMENT   se falhou, voltar ao estudo (registar a falha, não esconder)
    14 INTEGRATION  só depois integrar (flag → default só com validação visual)
    15 CHECKPOINT   documentar (formato do acordo; docs/HEAD_*.md)
    16 GENERALIZATION abstrair SÓ com evidência de ≥2-3 casos (ex.: janela C¹
                       → mecanismo geral de transição anatómica, CONT2/3 decidem)

    17 POST-INTEGRATION AUDIT — depois de integrar, re-verificar: renders,
       métricas, invariantes/testes, digests, confinamento, simetria, site,
       reprodutibilidade.  "Passou, acabou" NÃO existe.

## Três camadas de evidência (todas obrigatórias)

- **VISUAL** — o que o render mostra. Painéis antes×depois×refs, mesma câmara,
  luz e material (tools/headface/render_cmp.py, render_ear.py). O agente atual
  NÃO tem visão (FACT) → a leitura visual é do dono; o agente produz os painéis
  e os proxies medidos.
- **GEOMÉTRICA** — o que a geometria faz: curvatura κ, perfis, silhuetas,
  envelopes, secções (tools/headface/continuity.py).
- **MÉTRICA** — números reproduzíveis com critérios congelados antes de medir
  (tools/headfit/eval_phaseA.py; IoU de silhueta como proxy rastreável).

Critério visual duplo (do dono):
- **DISTÂNCIA** — "reconheço um humano?" (leitura global; IoU de silhueta =
  proxy medido)
- **PROXIMIDADE** — "aproximando, as estruturas parecem do mesmo organismo?"
  (integração; κ/turn/conc das interfaces = proxy medido)

Vista padrão de comparação: frente, perfil, ¾, posterior quando relevante,
close-up da região, silhueta, secções quando necessário.

## Regras

1. **Métrica ≠ realidade visual; visual ≠ prova geométrica.** Exigir as duas;
   se conflitarem, registar o conflito (nunca escolher a que convém).
2. Referências = evidência anatômica/estatística, NÃO função objetivo cega.
   Procuramos os padrões consistentes entre refs, não copiar uma ref.
3. Intervenção pequena, rastreável, explicável: o que muda, porquê, hipótese,
   região que DEVE mudar, região que NÃO deve, métrica que responde, resultado
   esperado, o que refutaria a hipótese.
4. Regressão é registada como regressão — nunca escondida.
5. Nada é declarado "concluído/bom/pronto" sem medição + render + validação.
   HYPOTHESIS continua HYPOTHESIS; UNKNOWN continua UNKNOWN.
6. Sem acumulação de patches: problema recorrente → procurar princípio
   arquitetural; mas abstrair SÓ depois de prova (regra 16 do ciclo).
7. Ideias do dono não são requisitos automáticos: o engenheiro interpreta,
   testa e pode contrariar com evidência (o dono espera isso).
8. Toda a descoberta volta para o sistema: campos, regras, métricas,
   instrumentos, invariantes, documentos — não fica no chat.
9. O repositório é a memória científica: outro agente/desenvolvedor deve
   reconstruir estado→decisões→experimentos a partir de `STATE.md` + `docs/`.

## Contabilidade técnica (registo obrigatório de toda a falha)

Nenhuma falha é apagada por estar fora do escopo do checkpoint. Cada achado
entra num destes estados (ver tabela em `STATE.md`):

    introduzido pelo estudo · pré-existente · corrigido · não corrigido ·
    UNKNOWN · fora de escopo · regressão · melhoria confirmada

Exemplo (CONT1): 758 verts assimétricos nos pés — **pré-existente + não
corrigido + fora de escopo** (idêntico em N1/F1/F2; não é regressão da orelha).

## Linguagem científica (medida ≠ interpretação)

Cada medida é chamada pelo que É; a interpretação vem à parte e em conjunto:

- IoU de silhueta = **similaridade de silhueta global medida por IoU** sob uma
  normalização/câmara/caixa definidas — não é "parece com as refs".
- κ = **curvatura** (1/mm) ao longo do arco — não é "qualidade anatômica".
- turn = **distribuição de mudança angular** (graus) na janela — não é "humanidade".
- conc = **concentração da viragem** perto do pico — não é "integração".

"Nós interpretamos essas medidas em conjunto" + a camada visual do dono.
IoU alto + envelope correto ≠ estrutura resolvida (CONT1: orelha segue UNKNOWN
até validação visual).

## Papéis

- **DONO** — direção, percepção visual, objetivos, visão do produto.
- **ENGENHEIRO/AGENTE** — arquitetura, experimentos, interpretação, validação.
- **SISTEMA/REPO** — evidência, reprodução, métricas, histórico, memória.
