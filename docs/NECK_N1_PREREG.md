# NECK N1 — pescoço superior aprendido das refs (pré-registo, congelado antes de medir)

Autorizado pelo utilizador: intervenção própria no pescoço superior (mentón → início dos ombros);
garantia sobre o corpo = **tudo fora do pescoço superior idêntico**.

**Hipótese.** O pescoço superior é demasiado largo e adiantado (cone entre dois anéis), o que enterra o
bordo inferior/ângulo da mandíbula e encurta o submento (C2g).  Seguir o perfil das refs no pescoço
superior liberta o terço inferior da cabeça sem mexer na cabeça.

**Observado (MEASURED, `tools/headfit/neck_study.py`, referencial da cabeça mm@H226, 3 refs
femalebase/bodytopo/femalechar; makehuman fora pela mesma razão do estudo do queixo):**
| z | nossa w / frente / trás | refs média w / frente / trás | refs intervalo w |
|---|---|---|---|
| −10 | 72.4 / 40.4 / −81.1 | 50.2 / 25.1 / −75.3 | 44–56 |
| −20 | 81.6 / 41.3 / −85.3 | 53.8 / 20.1 / −78.7 | 47–64 |
| −30 | 95.0 / 43.1 / −91.1 | 64.1 / 17.5 / −82.8 | 54–82 |
| −35 | 103.8 / 44.8 / −94.8 | 72.8 / 16.8 / −84.9 | 57–97 |
Anéis finais do builder (depois dos campos): trunk.2 em z = +1.0 (52.1 / 41.4 / −71.5),
trunk.3 em z = −35.8 (99.4 / 43.6 / −98.2), trunk.4 em z = −53.0 (144 / 67 / −121, início dos ombros).

**Mudança única (flag `HCG_NECK=N1`; omissão inalterada).** Só os parâmetros das DUAS estações do pescoço
superior (trunk.2, trunk.3) mudam; cotas, número de estações, anéis, faces e UV ficam iguais.  Alvo de
cada anel **final** = perfil médio das 3 refs à cota final do anel:
- trunk.3 (z −35.8): w 75.7, frente 16.8, trás −85.3 (interpolação da tabela).
- trunk.2 (z +1.0, acima do mentón, quase todo dentro da cabeça): extrapolação linear do perfil de
  pescoço das refs em z −10…−25 ⇒ w 48.0, frente 29.8, trás −71.2 (declarado: extrapolado).
Os valores das estações obtêm-se corrigindo o desvio medido estação → anel final (os campos do corpo
deslocam ~−3 mm em y e ~+2 % em largura); uma iteração de verificação automática, sem escolha manual.
Escala por h (altura da cabeça), referencial y da cabeça (−0.0398·h), como a cabeça.
trunk.4 e abaixo (ombros, tórax) **não mudam**.

**Critérios (na superfície exportada, mesmo instrumento):**
- N-C1 perfil: em z = −10, −15, −20, −25, −30, −35: w, frente e trás dentro de [mín, máx] das 3 refs
  (tolerância 2 mm) em ≥ 15 das 18 medições.  (Antes: 1/18.)
- N-C2 C2g/TR3 ≥ 55 (critério da Fase A, sem alteração).  Previsão: ≈ 70.
- N-C3 sem regressão da cabeça: C1 ≤ 2.5 e C2a,b,d,e,f dentro (A2b + N1 vs A2b).
- N-C4 garantias: mesma contagem de vértices/faces e mesmas faces; UV idênticos; todos os vértices fora
  dos anéis trunk.2/trunk.3 bit-idênticos; testes da omissão = 133/1/1; J1–J5 passam com a flag; determinismo.
- N-C5 vistas (juízo do utilizador): frente, lado, ¾, costas, cinza neutro, sem cabelo.

**Risco registado antes de medir:** a frente do tórax congelado está 70–85 mm à frente das refs
(z −80…−120).  Com o pescoço a seguir as refs, a passagem trunk.3 → trunk.4 fica mais íngreme
(frente 16.8 → 67 em 17 mm; antes 43.6 → 67).  Medir e mostrar; não corrigir aqui (tórax congelado).
