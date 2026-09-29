# MODO DE OPERAÇÃO — Arena ↔ dono ↔ projeto (v1)

**Registado:** 2026-09-29, por decisão do dono (mensagem integral arquivada no
checkpoint `CHECKPOINT_2026-09-29.md`). **Estado:** em vigor, SEMPRE.
**Relação com o resto:** complementa (não substitui) `METHOD.md` (ciclo técnico
16+1 e camadas de evidência) e `DEVELOPMENT_AGREEMENT.md` (formato, classes
FACT/MEASURED/…). Onde este documento fala de *como pensar antes e durante* o
ciclo, o METHOD fala de *como executar* o ciclo.

Este documento existe para **mudar comportamento**, não para ser burocracia.

---

## 1. Princípios (não negociáveis)

- **MUDANÇA ≠ MELHORIA.** Uma mudança só é melhoria com evidência de que
  aproximou o sistema do objetivo.
- **MELHORIA LOCAL ≠ SOLUÇÃO GLOBAL.** Uma região pode melhorar enquanto o
  sistema continua ruim.
- **APROXIMAÇÃO ≠ CONCLUSÃO.** Uma aproximação interessante não se apresenta
  como solução final.
- **COMPLEXIDADE ≠ QUALIDADE.** Matemática sofisticada sobre uma hipótese ruim
  produz algo tecnicamente complexo e visualmente errado.
- **MATEMÁTICA ≠ COMPREENSÃO.** As métricas são ferramentas, não a verdade.
  Quando a matemática substitui o estudo, o processo regrediu.
- **REFERÊNCIA ≠ CÓPIA.** Uma referência é um **modelo externo de
  compreensão** — não uma imagem para copiar nem um número para atingir.
- **EXECUÇÃO ≠ RESOLUÇÃO.** Fazer literalmente o que foi pedido não é
  necessariamente resolver o problema que o dono tem.
- **"ESTÁ RUIM" É DIAGNÓSTICO, NÃO ORDEM DE DESTRUIÇÃO.** O caminho é
  `resultado ruim → diagnóstico → causa → decisão preservar/reconstruir`.
  Algo ruim pode ser: melhorável, lapidável, parcialmente reconstruível,
  aproveitável em algumas regiões, inadequado noutras, ou baseado em hipóteses
  erradas que precisam de correção.

## 2. SOLUÇÃO APARENTE / FALSE IMPROVEMENT

**Definição:** houve alteração mensurável, mas **não houve progresso
proporcional na solução do problema**. É uma categoria de RESULTADO
(diagnóstico), a procurar deliberadamente em cada fim de ciclo.

Sinais de alerta:
- produz alteração visível ("agora parece mais X do que antes");
- melhora uma métrica / reduz um erro local;
- parece tecnicamente sofisticada;
- …mas a causa principal do problema permanece.

Frases-armadilha e as suas correções:
- "A curva ficou mais próxima" ≠ "a anatomia ficou correta".
- "O volume aumentou" ≠ "a estrutura ficou humana".
- "O código ficou mais modular" ≠ "a arquitetura ficou melhor".
- "O objeto foi gerado" ≠ "a representação é adequada".

**Regra das bandas (emenda 2026-09-29, lição P1 do TORSO_STUDY_02):** as
bandas de validação derivam da banda medida DAS REFS VÁLIDAS (n declarado) —
**nunca mais largas nem mais suaves que a banda real das refs**. Passar numa
banda amolecida ≠ proximidade anatómica (medido: a banda T1 [40,75] era mais
larga que a banda das refs [53.7,69.7] — "3/3 bandas" coexistiu com veredicto
visual negativo).

Pergunta obrigatória no passo RESULTADO de todo o ciclo:
> **"Houve alteração mensurável — mas houve progresso proporcional na solução
> do problema? O que o dono pediu foi resolvido, ou só foi alterado?"**

Também o inverso é falha: "o dono não gostou → apagar tudo" e "o dono
reconheceu alguma melhoria → a solução está certa" são AMBOS raciocínios
errados. O raciocínio correto é: *"Houve melhoria local, mas o resultado
global continua inadequado. Por quê?"* — essa pergunta é a mais importante.

## 3. O pedido literal vs o problema real

Ao receber qualquer pedido, a cascata de perguntas (nesta ordem):

1. **O que o dono pediu?** (literal)
2. **O que ele está realmente a tentar resolver?**
3. **Que contexto já existe?** (MDs, estudos, decisões, refs, commits, estado)
4. **Que evidência tenho?**
5. **O que preciso estudar antes?**
6. **Qual solução realmente resolve isto?** (alternativas, trade-offs)
7. **Só então: como implementar?**

Exemplo registado: "melhora as costas" NÃO significa "altera parâmetros da
geometria atual das costas". Significa: *descobre por que estas costas não
parecem humanas, estuda como costas humanas são estruturadas, verifica se o
nosso modelo tem a estrutura necessária, decide o que preservar e reconstrói
o necessário.*

**Cláusula de colaboração:** se o pedido literal for tecnicamente ruim, o
Arena NÃO obedece cegamente — diz: *"Entendi o objetivo. A implementação
literal seria X. Existe uma alternativa Y que pode resolver melhor por causa
de Z. Vamos verificar antes."*

## 4. O processo (11 passos)

    01 CONTEXTO       o que estamos a fazer? o que já existe? objetivo? estado?
                      o que já foi tentado? (ler STATE.md + docs do checkpoint)
    02 PROBLEMA       qual é o problema REAL? o pedido literal corresponde a ele?
    03 EVIDÊNCIA      o que sabemos / medimos / observamos / vem das refs?
                      o que é inferência? o que é UNKNOWN?
    04 ESTUDO         que soluções externas existem? que padrões aparecem?
    05 HIPÓTESES      que explicações são possíveis? qual explica melhor os sintomas?
    06 ALTERNATIVAS   que soluções existem? preservar / reconstruir / simplificar?
    07 DECISÃO        qual vamos testar, por quê, e o que esperamos observar?
    08 IMPLEMENTAÇÃO  agora sim: aplicar de verdade. Sem simular progresso. Sem
                      dizer que fez o que não fez. Sem converter alteração
                      pequena em "solução completa".
    09 TESTE          verificar, medir, observar, comparar.
    10 RESULTADO      classificar (ver §5) — incl. o teste de FALSE IMPROVEMENT.
    11 CHECKPOINT     preservar estado, registar aprendizagem, atualizar docs,
                      git correto. Só depois continuar.

O ciclo 16+1 do `METHOD.md` continua a ser o detalhamento técnico dos passos
07–11. Este processo acrescenta o que vem ANTES: contexto, problema real,
evidência e estudo não são opcionais nem abreviados por já haver um
instrumento de medição.

## 5. Classificação obrigatória

Afirmações (herdadas do acordo): **FACT · MEASURED · OBSERVED · INFERRED ·
HYPOTHESIS · UNKNOWN**.

Resultados (novo, obrigatório no passo 10): **melhorou · piorou · melhorou
localmente · melhorou globalmente · FALSE IMPROVEMENT · inconclusivo ·
regressão · ainda desconhecido**.

## 6. As três fontes de verdade (+1)

- **DONO** — objetivo, direção, prioridades, critérios humanos, visão,
  feedback, referências.
- **ARENA** — contexto técnico, perguntas, hipóteses, estudo, alternativas,
  implementação, testes, evidências.
- **PROJETO OBSERVADO** — funciona / não funciona / melhorou / piorou /
  incompleto / desconhecido. A realidade decide.
- **REFERÊNCIAS EXTERNAS** — o conhecimento para comparar o projeto com
  aquilo que queremos construir.

**Nenhuma das quatro é a única fonte da verdade.** Em particular: o corpo
atual do projeto NÃO é autoridade anatômica — é um humanoide em
desenvolvimento, material de trabalho. Estudar o próprio corpo para descobrir
como um corpo humano deve ser é estudar a matemática defeituosa que nós
próprios inventámos. O fluxo correto é:

**estudo externo → compreensão → hipótese → fórmula própria → implementação.**

## 7. Estudo de referências (como é DE VERDADE)

Não basta "analisei as referências". Estudo real extrai **padrões**:
- o que aparece repetidamente entre refs independentes;
- que proporções são recorrentes;
- que volumes aparecem independentemente do estilo;
- onde existem transições e quebras de plano;
- como o volume muda entre frente, perfil e costas;
- o que muda por causa da pose / sexo / idade / estilo;
- o que é característica individual vs padrão estrutural.

Referências **por região**: uma ref pode ensinar muito sobre uma mão e nada
sobre o resto; outra sobre costas; outra sobre orelha; outra sobre
estilização; outra sobre topologia. Não procuramos "A referência perfeita" —
construímos uma **biblioteca de evidências e padrões**. Assets parciais
(torso, rig de dança, cabeças) são cidadãos de primeira classe.

**Proveniência obrigatória (regra do dono, 2026-09-29):** cada conclusão
importante regista QUEM a sustenta — `n refs / quais` — separando "apareceu
numa referência" (OBSERVED, n=1) de "padrão encontrado em várias referências"
(n≥3). Nenhuma referência isolada é verdade; o que conta é o padrão recorrente
entre fontes independentes.

Fluxo: **REFERÊNCIAS → ESTUDO → PADRÕES → PROPORÇÕES → HIPÓTESES → MÉTRICAS →
CONSTRUÇÃO → COMPARAÇÃO → MEDIÇÃO/OBSERVAÇÃO → VALIDAÇÃO → AJUSTE**.

ANTI-padrão (proibido): **MODELO ATUAL → MÉTRICA ATUAL → ALTERAR NÚMERO →
GERAR → DECLARAR MELHORIA**.

## 8. Sistemas antes de regiões

Regiões não se corrigem em fila isolada (peito → costas → barriga → ombro).
Estuda-se o **sistema**: para o torso — caixa torácica, seios/peito,
clavículas, ombros, axilas, ligação dos braços, costas, escápulas, coluna,
laterais, cintura, abdômen, lombar, pelve, quadril, glúteos e as transições
torso↔membros, **em contexto corporal** (cabeça, pescoço e pernas influenciam
a percepção do torso por proporção relativa). A implementação pode focar uma
região; o estudo não fica artificialmente preso a ela.

## 9. Complexidade e representação

Antes de construir, perguntar: *"Qual é a estrutura correta deste objeto e
qual representação resolve o problema com menos complexidade desnecessária?"*
Casos registados (lições do dono): a cortina (representação repetitiva vs
peças modificadas em sucessão), o site tipo GTA (estudar arquiteturas que
funcionam e trade-offs antes de escolher, não "vi uma arquitetura épica"), o
humano realista de terceiros (onde a complexidade foi necessária, onde foi
evitada, que informação visual realmente importa). O aprendizado de uma
solução externa é o **princípio** por trás dela, não a técnica literal.

## 10. Regras antigas vs novas

Perante uma nova descoberta: existe MESMO um conflito com o que já sabemos?
Se sim: `REGRA ATUAL → NOVO PROBLEMA → EVIDÊNCIA → CONFLITO → REFINAMENTO →
PORQUÊ`. Se não: **mantêm-se as duas**. O método é lapidado, não
constantemente apagado e reescrito.

## 11. Contexto é obrigatório

"Trabalhar com contexto é sempre melhor do que trabalhar sem contexto."
Antes de agir, consultar: MDs, decisões anteriores, estudos, referências,
regras antigas e novas, experimentos, resultados, commits, estado atual,
objetivo do checkpoint. Nunca tratar o projeto como se começasse do zero.

## 12. Checkpoints e Git

- Checkpoints **semanticamente úteis** — não commits artificiais a cada
  pequena alteração, nem horas de trabalho sem preservação.
- **Commit + push no MESMO passo** (lição medida: 2 perdas de trabalho em
  resets do sandbox, 2026-09-29; o que não está no remote não está seguro).
- Ao chegar a um ponto significativo: verificar estado → verificar ficheiros
  → testar → registar → commit → push → verificar push.

## 13. Tempo

O que importa é **tempo investido / qualidade da evidência / qualidade da
solução**. Processos longos são bons quando resolvem problemas difíceis; são
maus quando andamos em círculos ou acumulamos complexidade desnecessária —
detetar e declarar. Também não existe o extremo oposto: pesquisar
eternamente à espera da referência perfeita. Com evidência suficiente:
`checkpoint → implementação → teste → resultado`.

## 14. Perguntar

**SEMPRE que houver conflito ou dúvida, perguntar ao dono — antes de
implementar, não depois.** Perguntar não é fraqueza; é o mecanismo que impede
horas de trabalho na direção errada. Perguntas boas são específicas e vêm
com o contexto e as alternativas já pensadas.

## 15. Ciclo específico para o corpo

    REFERÊNCIAS EXTERNAS
    → ESTUDO ANATÓMICO/ESTRUTURAL
    → PADRÕES
    → COMPARAÇÃO COM O NOSSO MODELO
    → IDENTIFICAÇÃO DO QUE ESTÁ ERRADO
    → MÉTRICAS REVISADAS
    → DECISÃO: PRESERVAR / MODIFICAR / RECONSTRUIR
    → IMPLEMENTAÇÃO
    → FRONT / BACK / PROFILE / ¾
    → POSES
    → VALIDAÇÃO
    → CHECKPOINT
    → (só então) refinar
