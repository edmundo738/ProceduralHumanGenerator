"""Diagnóstico H3/H2: de onde vem a profundidade do tronco medida?

Não altera o gerador.  Constrói o corpo (pure-python) em variantes em que um
campo do DeformStack é desligado por monkeypatch (identificado pela direção do
bump), e mede na LINHA MÉDIA (corte por triângulos em x = 0, escala 1700 mm)
frente, costas e profundidade às cotas do instrumento.  Também imprime a tabela
de estações de ``trunk_sections`` (larguras/profundidades TOTAIS).

Uso: python tools/refstudy/trunk_diag.py [preset] [seed]
"""
import os, sys
sys.path.insert(0, os.getcwd())
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import geom  # noqa: E402
from human_generator.core import field as F
from human_generator.pipeline.assemble import build_character
from human_generator.core.anatomy import Anatomy
from human_generator.pipeline.assemble import resolve_spec

preset = sys.argv[1] if len(sys.argv) > 1 else "realistic_female"
seed = int(sys.argv[2]) if len(sys.argv) > 2 else 42

_orig = F.DeformStack.bump


def _variant(skip):
    def bump(self, centre, amp, radius=0.05, *, direction=None, **kw):
        if direction is not None and skip(tuple(round(c, 3) for c in direction)):
            amp = 0.0
        return _orig(self, centre, amp, radius, direction=direction, **kw)
    return bump


VARIANTS = {
    "full": lambda d: False,
    "sem_gluteo": lambda d: d == (0.0, -1.0, -0.12),
    "sem_busto": lambda d: d == (0.0, 1.0, -0.1),
}
FRACS = [("busto/chest 0.7194", 0.7194), ("0.70 (estação waist)", 0.700),
         ("10ª costela 0.649", 0.649), ("omphalion 0.6017", 0.6017),
         ("0.58 (buttock lo)", 0.58), ("nádega 0.512", 0.512)]


def midline(builder, S, z0):
    """Corte horizontal por triângulos (geom.slice_segments, o mesmo do
    instrumento); devolve (frente, costas) = max/min de y onde o contorno cruza
    x = 0.  Escala 1700 mm."""
    k = 1000.0 * 1700.0 / S
    V = np.array([(v.x * k, v.y * k, v.z * k) for v in builder.verts])
    T = []
    for f in builder.faces:
        for i in range(1, len(f) - 1):
            T.append((f[0], f[i], f[i + 1]))
    segs = geom.slice_segments(V, np.array(T), z0)
    ys = []
    for a, b in segs:
        if (a[0] > 0) != (b[0] > 0):
            t = a[0] / (a[0] - b[0]); ys.append(a[1] + t * (b[1] - a[1]))
    if not ys:
        return None
    return max(ys), min(ys)


spec = resolve_spec(preset, seed=seed)
anat = Anatomy.from_spec(spec)
S = anat.stature * 1000
print(f"# preset={preset} seed={seed} estatura={S:.1f} mm  (medidas @1700)")
print("# estações trunk_sections (TOTAIS, @estatura real):")
print(f"#   {'z':>6} {'z/S':>6} {'largura':>8} {'prof':>7} {'frente_y':>9} {'costas_y':>9} {'prof/larg':>9}")
for sc in sorted(anat.trunk_sections(), key=lambda q: -q.center.z):
    z = sc.center.z * 1000
    w = 2 * sc.width * 1000
    fy = (sc.center.y + sc.depth * sc.front_scale) * 1000
    by = (sc.center.y - sc.depth * sc.back_scale) * 1000
    print(f"#   {z:6.0f} {z/S:6.3f} {w:8.1f} {fy-by:7.1f} {fy:9.1f} {by:9.1f} {(fy-by)/w:9.3f}")

rows = {}
for name, skip in VARIANTS.items():
    F.DeformStack.bump = _variant(skip)
    r = build_character(preset, seed=seed)
    rows[name] = {lab: midline(r.builder, S, f * 1700) for lab, f in FRACS}
F.DeformStack.bump = _orig
print("# linha média (frente / costas / profundidade), mm @1700")
for lab, _ in FRACS:
    cells = []
    for name in VARIANTS:
        m = rows[name][lab]
        cells.append(f"{name}: {m[0]:6.1f}/{m[1]:7.1f}/{m[0]-m[1]:6.1f}" if m else f"{name}: --")
    print(f"{lab:22s} " + "  ".join(cells))
