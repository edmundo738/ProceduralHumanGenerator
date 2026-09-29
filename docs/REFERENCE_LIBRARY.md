# REFERENCE LIBRARY — base de conhecimento geométrico (infraestrutura de estudo)

**Regra fundamental (dono):** a biblioteca é **observação externa**. NÃO modifica
automaticamente faceB2, N1, T1–T5 nem nada validado. O caminho é:
REFERENCES → CONTEXT → EXTRACTION → ANALYSIS → COMPARISON → HYPOTHESIS →
EXPERIMENT; só uma hipótese validada vira intervenção (METHOD.md).

**As entradas NÃO são ground truth.** Cada modelo é um dado de estudo com
proveniência, pose, topologia, escala e limitações documentadas; a adequação por
análise (`suitability`) começa UNKNOWN e é preenchida pelos estudos — ex.:
"REF-F-REAL-001: boa para forma geral, má para busto, pose inadequada para
comparação frontal" é INFORMAÇÃO, não veredicto prévio.

## 1. Estrutura

```
references/
├── INDEX.json                (gerado: tools/reflib/index.py)
├── female/
│   ├── realistic/ ├── semi_realistic/ ├── anime_realistic/
│   ├── anime/ ├── cartoon/ ├── low_poly/
│   └── (cada estilo:) full_body/ torso/ head/ face/ hands/ feet/ ears/ arms/ legs/ other/
│       └── REF-F-<STYLE>-NNN/   (pasta por modelo)
│           ├── <ficheiro do modelo>   (.blend/.obj/.fbx + assets)
│           ├── meta.json              (metadados — §3)
│           └── extraction.json        (gerado: tools/reflib/inspect_model.py)
└── male/                     (whitewalker entrou aqui por exclusão — sexo UNKNOWN)
```

Nova categoria só depois de justificada em STATE/METHOD (regra do dono).
Referências 2D (concept art da pasta original) FICARAM DE FORA por enquanto —
categoria a justificar pelo dono quando quiser usá-las.

## 2. Classificação

Classificação humana e simples (dono). A classificação provisória do agente é
marcada `style_confidence: "provisional_agent"` — o dono corrige no meta.json.
UNKNOWN em vez de inventar. Separar sempre: ANATOMIA / MORFOLOGIA / PROPORÇÃO /
ESTILO / TOPOLOGIA — nunca misturar numa única leitura.

## 3. Schema (meta.json; validação: tools/reflib/schema.py)

| campo | valores | nota |
|---|---|---|
| id | REF-(F\|M)-CODE-NNN | REAL/SEMI/ANIR/ANIME/CART/LOWP |
| sex / style / scope / ref_type / pose | enums (schema.py) | pose desconhecida → inspetor dá `pose_hint` HEURÍSTICO |
| style_confidence | high / provisional_agent | quem classificou |
| origin, provided_by_owner, license | texto/bool | proveniência (commit 408517a nas 6 iniciais) |
| file + files (INDEX) | caminho + sha256 + bytes | rastreável |
| limitations[] | lista | inclui o que MEDEMOS (ex.: bodytopo sem pés) |
| regions_available[] | lista | |
| observations{} / unknowns[] | dict/lista | UNKNOWN explícito obrigatório |
| suitability{} | dict vazio no início | preenchido só por estudo |

## 4. Política de git (híbrida, dono 2026-09-28)

Commitar até **~300 MB** no total (guarda: `tools/reflib/index.py` sai com erro
se exceder); ficheiro individual **> 50 MB** gera aviso (considerar fora do git,
com registo no INDEX). Atual: **13.5 MB / 6 modelos** — tudo commitado.

## 5. O que extraímos do Blender (matriz de capacidades, bpy 5.0.1)

| extraível com fiabilidade | ainda NÃO extraído (evolui) |
|---|---|
| verts/arestas/faces, quads/tris/ngons | node trees de materiais |
| ilhas (componentes conexos) | armaduras/skinning (só presença) |
| arestas de contorno/não-manifold (via edge_keys — `MeshEdge.is_boundary` não existe no bpy 5.0) | shape keys (só contagem) |
| faces degeneradas, densidade (percentis de aresta) | texturas (só ficheiros+hash no INDEX) |
| bbox MUNDO, fator de escala do objeto | drivers/constraints |
| UV (presença), grupos, modificadores (tipos), materiais (nomes) | avaliação de modificadores (extraímos a CAGE) |
| pose_hint (heurística largura/altura — declarada) | semântica anatômica automática (NÃO existe) |

## 6. Correspondência entre modelos (regra)

NUNCA assumir "vertex N do modelo A = vertex N do modelo B" — topologias, poses
e escalas diferem (medido: ff11 é 100% triângulos com 175 ilhas; Lucia tem 144
ilhas; whitewalker 1192 verts). Antes de qualquer comparação vertex-to-vertex é
preciso método de canonicalização validado. Entretanto: marcos, regiões,
perfis, secções, curvatura, descritores normalizados (como já fazem
tools/headstudy e tools/refstudy).

## 7. Separação A (reprodução) vs B (aprendizagem)

A — snapshot reproduzível: ver `tools/snapshot/` (protótipo mínimo:
geometria+transform+nomes+versões+digests; round-trip VERIFICADO 7/7 numa ref e
no nosso gerador). Evolui conforme descobrirmos o que é necessário preservar.
B — aprendizagem/estatística: modelo → canonicalização → marcos/regiões →
características → variação → padrões → parâmetros procedurais. **Ainda não
desenhada** — primeiro representação confiável dos dados (este documento), depois
o dono estuda as refs (métricas, padrões, suavização, profundidade, transições,
proporções, estilos) e só então projetamos a análise.

## 8. Estado atual (2026-09-28, após 1.º povoamento do dono)

**14 entradas** inspecionadas e indexadas (INDEX.json, 61.4 MB, sem avisos;
política híbrida ≤300 MB confortável):
- 6 iniciais migradas de `408517a` (REAL-001..004, ANIR-001, M-REAL-001);
- pack anime SimpleRig do dono: REF-F-ANIME-001..003 + REF-M-ANIME-001
  (masculino movido para `male/` — não misturar datasets; `SimpleRigUI.py`
  fica ao nível do pack, é utilitário de rig, não modelo);
- realisticas do dono: REF-F-REAL-005 (base mesh T-pose, GLB), REF-F-REAL-006
  ("realistic female.blend" do zip extraído; zip removido por duplicação),
  REF-F-REAL-007 (MPPled.fbx, tronco), REF-F-REAL-008 (rig+animação de dança —
  `other/`, não é alvo anatômico).

Notas técnicas: os FBX com luzes rebentam o importador do bpy 5.0
(`CyclesLightSettings.cast_shadow` removido — patch defensivo no inspetor;
afeta só settings de sombra, não a geometria). Adequação por análise: tudo
UNKNOWN por design. O dono continuará a povoar (foco realistic + T-pose).
