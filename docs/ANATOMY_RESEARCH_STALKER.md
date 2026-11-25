# ANATOMIA — pesquisa aplicada ao THE STALKER (v3.3)

Pedido do dono: "pesquisa sobre anatomia humana, como cada peça se
comunica com outra, deforma, estica, puxa etc, tudo conectado; depois
como modelar e como criar um monstro em condições; depois prossiga
automaticamente ao rigor para construir".

## 1. Como as peças se comunicam (fascia / cadeias miofasciais)

- A fascia é uma **rede 3D contínua** (colagénio+elastina) que envolve
  e INTERLIGA músculos, ossos e órgãos — não é "embrulho passivo":
  transmite força (até 30–40% da força muscular contorna os tendões e
  passa pela matriz fascial — myofascial force transmission, Huijing).
- Cadeias miofasciais (ex.: linha posterior: plantares → gémeos →
  isquios → eretores da espinha → occipital) coordenam movimento e
  distribuem carga: "tudo puxa tudo" através de ligações contínuas.
- Modelos de biotensegridade: forma mantida por equilíbrio tensão
  (fascia) + compressão (ossos); sem carregador localizado único.
- Músculo individual: epimísio → perimísio → endomísio, tudo contínuo
  com o TENDÃO nas duas pontas (origem/inserção). As "bainhas" são
  PARTILHADAS entre fibras vizinhas → transmissão por cisalhamento.

**Aplicação ao STALKER:** a junção entre partes NÃO pode ser "esfera
geométrica + tubo" (leitura de peças enfiadas) → **blend Laplaciano da
costura** (suavização local da malha fundida na zona da articulação,
gradiente contínuo = CARNE LIGADA em força, não só em nome).

## 2. Como cada músculo se DEFORMA (estica/puxa/bombeia)

- Musculatura real: **origem (tendão) → BARRIGA (ponto mais grosso,
  a meio) → inserção (tendão)** — e as barrigas CRUZAM as articulações
  (bíceps: omoplata → passa ombro E cotovelo → insere no rádio).
- Ao contrair: a barriga ENCURTA e ENGLESA (squash), os tendões puxam;
  volume ~preservado (barriga alarga ao encurtar).
- Na animação clássica: squash & stretch com volume constante = leitura
  de material vivo; rígido = leitura de objecto/Minecraft.

**Aplicação:** perfis de raio dos membros com **barriga a meio do osso
e tendão FINO nas juntas** (não bojos nas juntas como eu tinha — era o
inverso da anatomia!) + **bombeio procedural** da malha do membro
sincronizado com a dobragem da articulação filha (bulge 3–9%).

## 3. Como MODELAR (fluxo dos artistas)

- Ordem: esqueleto/landmarks → massas → grupos musculares (origem+
  inserção) → tendões/gordura/pele. A SILHUETA é determinada pelos
  volumes musculares e por ONDE viram tendão.
- Erros comuns a evitar: caixa torácica grande demais, mãos/pés
  sub-escalados, inserções no sítio errado, articulações rígidas.

## 4. Como criar um MONSTRO em condições

- **Base na realidade + exagero estratégico** (Giger's Alien: estrutura
  humanoide + anatomia própria + design). Distorsão CREDÍVEL: "está
  errado… mas vejo como funcionava" — pergunta: como se move? como
  percebe?
- Elongação PROPÓSITAL: alongar antebraços/canelas MANTENDO mãos/pés
  (contraste = grotesco); membros traseiros "scrawny, gnarled" com
  tendões e nós ósseos à mostra; postura corcunda/contorcida.
- Front forte / trás franzino; articulações estranhas mas FUNCIONAIS.

## Fontes (consultadas 2026-09-24)

- Grokipedia "Fascia" — rede contínua, transmissão de força, cadeias.
- scienceinsights.org "What Is Myofascial Tissue" — 30-40% força
  epimuscular; biotensegrity.
- musculoskeletalkey.com "General anatomy of the muscle fasciae" —
  endomísio partilhado, cisalhamento trans-laminar.
- tensegrityinbiology.co.uk "Myofascial Helices" — bainhas contínuas.
- cursoseorientacoes.com "Human anatomy drawing for artists" (Lesson) —
  músculos cruzam articulações; origem/inserção definem a forma.
- docs.superhuman.com/@hankyu/character-design — belly = ponto mais
  grosso; origem→tendon→muscle→tendon→inserção.
- proko.com Anatomy course — esqueleto→origem/inserção→formas.
- cgmasteracademy.com "10 Steps to Improve Your Sculpting" — silhueta
  dominada por onde vira tendão vs volume.
- tripo3d.ai "Human Anatomy for 3D Modeling" — fluxo blockout→músculo;
  erros comuns.
- dessindigo.com "How to Draw a Monster" — distorcer sem perder a
  lógica; pernas traseiras scrawny/gnarled.
- creativize.net "How to Draw Horror Characters" — distorção credível,
  alongar membros manter extremidades.
- creativebloq.com "Top tips for designing a terrifying creature" —
  base naturalista + exagero (Alien).
- nccastaff.bournemouth.ac.uk (Zhang) "Automatic muscle generation for
  character skin deformation" — músculos preservam volume, deslizam e
  dobram em volta de ossos/juntas.
- users.cs.utah.edu "Dynamic implicit muscles for character skinning" —
  bulge por activação, colisão músculo-osso.
- education.siggraph.org "Squash and Stretch" — volume constante.

## Plano v3.3 (do rigor → construção)

| # | mudança | métrica nova |
|---|---|---|
| 1 | pernas em ANTI-FASE (π em falta = bug "unificadas") | A7 |
| 2 | perfis barriga/tendão (barriga a meio, tendão fino na junta) | F6, F6b, F6c |
| 3 | blend Laplaciano das juntas (fim de esferas+cones) | F4 já cobre relevo; validação visual por painel |
| 4 | bombeio muscular por dobragem (squash) | A8 |
| 5 | UV físico (tiles de 250mm — densidade constante) | T1–T3 |
