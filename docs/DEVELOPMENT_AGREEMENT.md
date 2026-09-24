# Registo do Acordo de Desenvolvimento, Builds e Visão Independente

**Data do registo:** 2026-09-24 · **Estado:** em vigor
**Nota:** este ficheiro é um **registo condensado** do acordo entregue por Edmundo
nessa data (o texto integral está no registo da sessão). Onde o texto original e
este resumo divergirem, o original manda — corrigir aqui.

## Participantes

- **Edmundo** — proprietário do projeto, validação humana.
- **Luna** — análise crítica, engenharia, proteção contra overengineering.
- **Arena** — investigação aplicada, implementação, testes, medição, documentação.

## Regras vinculativas

1. **Dois ciclos, nenhum substitui o outro**
   - Desenvolvimento: `CONTRACT → PLAN → ACTION → EVIDENCE → TEST → MEASURE → DOCUMENT`
   - Integração: `BUILD → HUMAN OBSERVATION → FEEDBACK → HYPOTHESIS → TARGETED CHANGE → TEST → MEASURE`
2. **Independência intelectual do Arena.** Em cada grande slice, o relatório termina com
   uma secção obrigatória: `Minha avaliação · Concordo porque · Discordo de · Riscos ·
   Próximo passo que recomendo · Por quê`. Se não houver objeção:
   *"Não identifico objeção técnica relevante."* Concordo para manter o fluxo é proibido;
   discordância fundamentada é bem-vinda.
3. **O Arena pode dizer "não"**, com a estrutura
   `PROPOSTA → PROBLEMA → EVIDÊNCIA → ALTERNATIVAS → RECOMENDAÇÃO`, e deve declarar
   quando a objeção é hipótese e não conclusão.
4. **Classificação obrigatória** nas afirmações: FACT · MEASURED · OBSERVED · INFERRED ·
   HYPOTHESIS · OPINION/ENGINEERING JUDGMENT · UNKNOWN.
5. **Quando NÃO pedir build:** componente isolado concluído, gerador novo, função
   alterada, API alterada, teste a passar, defeito de topologia corrigido (inclui S2).
6. **Quando pedir build:** integração suficiente · pergunta concreta · feedback que
   **possa mudar uma decisão** · sistema estável (não a mudar de estrutura a cada hora).
7. **Apresentação de build:** identificação (BUILD/COMMIT/VERSÃO/SEED/PRESET/AMBIENTE) ·
   objetivo (uma pergunta) · conteúdo · não incluído · evidência técnica · evidência
   visual. Build ≠ release ≠ produção.
8. **Feedback humano é evidência, não especificação.** Decompor
   `OBSERVATION → HYPOTHESIS → TEST → MEASURE` antes de mexer na arquitetura.
9. **Sem burocracia artificial:** problema claro → corrigir; testável → testar; passou →
   documentar; próximo passo óbvio → avançar. Discussão conjunta só quando a decisão é
   realmente relevante.
10. **Avançar** quando se sabe o que foi resolvido, medido, o que resta desconhecido,
    que regressões existem e se o sistema está estável para o próximo objetivo — não se
    espera perfeição. **Não avançar** quando uma falha estrutural impede compreender o
    sistema seguinte (ex.: geometria inválida → não empilhar deformação em cima).

## Roadmap orientador (não é promessa de implementação)

| Fase | Objetivo | Build humana |
|---|---|---|
| **S2** | Integridade geométrica (fechado 2026-09-24, `f8d1516`) | **não** (decidido) |
| **S3** | Corpo humano integrado: cabeça → pescoço → tronco → braços → mãos → pelvis → pernas → pés, base corporal coerente | **BUILD 01 — HUMAN SILHOUETTE** no final, se a anatomia básica estiver integrada |
| **S4** | Rosto e superfície: "temos uma representação visual humana convincente?" | **BUILD 02 — HUMAN CHARACTER** |
| **S5** | Variação, deformação e identidade; morphs/weights; preparação para rig | **BUILD 03 — VARIATION** |
| **S6** | Pipeline de produção: rig, animação, exportação, presets, CLI, performance, integração | **BUILD 04 — PRODUCTION CANDIDATE** |

Pergunta de BUILD 01 (a única): **a estrutura corporal básica forma uma figura humana
coerente?** — proporções da cabeça, comprimento dos braços, pernas, tronco, ombros,
pelvis, silhueta geral, ausência de deformações absurdas, escala. Não é "está bonito?".
Nesta build ainda **não** se avalia cabelo final, pele final, rosto definitivo, rig,
animação.

## Decisão imediata registada no acordo

- S2 continua/termina conforme os critérios aprovados (feito).
- **Nenhuma build humana neste momento.**
- Depois de S2: avaliar o estado real e avançar para a integração corporal (S3).
- O momento da build é determinado **pela pergunta que ela consegue responder**.
