# Preview local (modelo 3D + métricas + renders + histórico)

## Ver o site (rápido — não precisa de venv nem Blender)

O site construído está **commitado em `site/`** (é o próprio deliverable, com os GLBs e
digests verificados). Servir:

```bash
python3 -m http.server 8080 --bind 0.0.0.0 --directory site   # abrir http://localhost:8080
```

Num sandbox reciclado, restaurar é só:

```bash
git fetch origin arena/01a0d51d-proceduralhumangenerator && git reset --hard FETCH_HEAD
python3 -m http.server 8080 --bind 0.0.0.0 --directory site
```

## Regenerar (só quando as variantes mudarem)

```bash
PY=/home/user/.venv-hcg/bin/python          # venv com bpy
HCG_PREVIEW_OUT=site $PY tools/headless_blender.py run tools/preview/export_glb.py -- site/models
HCG_PREVIEW_OUT=site python3 tools/preview/build_site.py
git add site && git commit -m "preview: site regenerado"   # voltar a commitar (é pesado, ~56 MB)
```

`HCG_PREVIEW_OUT=<pasta>` muda o destino (por omissão `out/preview`, ignorado pelo git;
`site/` é a cópia persistente que vai para o git).

- Versões: `antes` (cabeça original), `faseA`, `a2b`, `n1`, `f1` (faceB+N1) — geradas com
  as mesmas flags de ambiente dos estudos (digests iguais aos registados em docs/head_phaseA/).
- Cinza neutro, sem cabelo, sem materiais. "Suave" = malha com subdivisão (a que vai a render);
  "Cage" = malha do gerador. O wireframe usa as arestas reais em quads (o GLB triangula).
- As refs NÃO estão no visualizador 3D (escala/alinhamento diferentes); aparecem nas tabelas e nas figuras.
