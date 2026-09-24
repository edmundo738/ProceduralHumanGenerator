#!/usr/bin/env bash
# Estudo de referências 01 — reprodução completa.
#  Requer: bpy 5.0.1 (+ tools/headless_blender.py build), numpy, scipy, matplotlib.
#  Entradas: referências do commit 408517a e o BUILD versionado em builds/.
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
PY=${PY:-python}
export HCG_REFSTUDY_WORK=${HCG_REFSTUDY_WORK:-out/refstudy}
mkdir -p out/refs "$HCG_REFSTUDY_WORK/build"
[ -d "out/refs/treino para o arena" ] || git archive 408517a "treino para o arena" | tar -x -C out/refs
if [ "${HCG_BUILD_FROM_TREE:-0}" = "1" ]; then     # experimento: mede a árvore de trabalho atual
  $PY tools/headless_blender.py run tools/refstudy/gen_blend.py "$HCG_REFSTUDY_WORK/tree" | grep '^GEN'
  export HCG_BUILD_BLEND="$HCG_REFSTUDY_WORK/tree/tree_realistic_female_s42.blend"
else                                               # por omissão: a BUILD versionada
  unzip -qo builds/build02_realistic_female_s42.zip -d "$HCG_REFSTUDY_WORK/build"
fi
if [ ! -f "$HCG_REFSTUDY_WORK/ansur_f.csv" ]; then   # espelho público do CSV DCPH-A (sha256 ed7e800a…)
  rm -rf /tmp/ansur_src && git clone -q --depth 1 --filter=blob:none --sparse https://github.com/sharad18/Adidas-Data-Challenge.git /tmp/ansur_src
  git -C /tmp/ansur_src sparse-checkout set --no-cone "/ANSUR II FEMALE Public.csv"
  cp "/tmp/ansur_src/ANSUR II FEMALE Public.csv" "$HCG_REFSTUDY_WORK/ansur_f.csv"
fi
$PY tools/refstudy/ansur.py
$PY tools/headless_blender.py run tools/refstudy/extract.py
$PY tools/refstudy/comps.py
$PY tools/refstudy/measure.py ours "{\"drop_labels\": $(cat $HCG_REFSTUDY_WORK/drop_ours.json)}"
$PY tools/refstudy/measure.py femalebase '{}'
$PY tools/refstudy/measure.py femalechar '{"flip_y": true}'
$PY tools/refstudy/measure.py bodytopo '{"flip_y": true}'
$PY tools/refstudy/bodytopo_stature.py
$PY tools/refstudy/measure.py bodytopo "$(cat $HCG_REFSTUDY_WORK/cfg_bodytopo.json)"
$PY tools/refstudy/metrics.py | tee "$HCG_REFSTUDY_WORK/metrics.txt"
$PY tools/refstudy/plots.py
$PY tools/refstudy/sil.py
