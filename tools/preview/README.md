# Preview local (modelo 3D + métricas + renders + histórico)

```bash
PY=/home/user/.venv-hcg/bin/python          # venv com bpy
$PY tools/headless_blender.py run tools/preview/export_glb.py -- out/preview/models   # 4 versões → GLB
python3 tools/preview/build_site.py                                                   # páginas + three.js + dados
python3 -m http.server 8080 --bind 0.0.0.0 --directory out/preview                   # abrir http://localhost:8080
```

- Versões: `antes` (cabeça original), `faseA`, `a2b`, `n1` — geradas com as mesmas flags de ambiente dos estudos
  (digests iguais aos registados em docs/head_phaseA/).
- Cinza neutro, sem cabelo, sem materiais. "Suave" = malha com subdivisão (a que vai a render);
  "Cage" = malha do gerador. O wireframe usa as arestas reais em quads (o GLB triangula).
- As refs NÃO estão no visualizador 3D (escala/alinhamento diferentes); aparecem nas tabelas e nas figuras.
- Tudo o que é gerado fica em `out/` (ignorado pelo git).
