"""PRÉ-REGISTO H7a × H4a — auditoria (só leitura) da massa anterior do busto no CONTROLO.

Avalia os dois deformadores "bust lobes" de generators/body.py (cópia literal dos
parâmetros) sobre os vértices do controlo exportado, e a contribuição analítica do
`front_scale` da estação do busto para o centroide.  Não gera nenhum modelo novo.

Uso: python tools/refstudy2/audit_bust.py   (requer out/rs2/raw_ours.npz)
"""
import sys, os, numpy as np, math
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
from human_generator.core.anatomy import Anatomy
from human_generator.pipeline.assemble import resolve_spec
from human_generator.core.field import DeformStack
from human_generator.core.field import Vector
a = Anatomy.from_spec(resolve_spec('realistic_female', seed=42)); h = a.h; lm = a.landmarks; s = a.stature
d = np.load(os.path.join(os.environ.get('HCG_REFSTUDY_WORK', 'out/rs2'), 'raw_ours.npz')); V = d['V']
print('raw units: z range', V[:, 2].min(), V[:, 2].max())
sc = 1.0 if V[:, 2].max() < 10 else 0.001
st = DeformStack()
for tag in ('L', 'R'):            # cópia literal de generators/body.py (bust lobes)
    c = Vector(lm[f'bust.{tag}'])
    st.bump(c + Vector((0, -0.010 * h, -0.012 * h)), a.bust_protrusion() * 0.42,
            sigma=(0.075 * h * 1.05, 0.065 * h, 0.085 * h), direction=Vector((0, 1, -0.10)))
    print('lobe', tag, 'centre', tuple(round(x, 4) for x in (c + Vector((0, -0.010 * h, -0.012 * h)))),
          'amp', round(a.bust_protrusion() * 0.42, 4), 'sigma', tuple(round(x, 4) for x in (0.075 * h * 1.05, 0.065 * h, 0.085 * h)))
disp = np.array([st.apply([Vector(p * sc)])[0] - Vector(p * sc) for p in V[::1]])
mag = np.linalg.norm(disp, axis=1) * 1000
idx = np.nonzero(mag > 0.5)[0]
print(f'vértices com deslocamento > 0.5 mm: {len(idx)} de {len(V)}; máx {mag.max():.1f} mm')
if len(idx):
    P = V[idx] * sc
    print(f'  z (m): {P[:,2].min():.3f}–{P[:,2].max():.3f}  (= {P[:,2].min()/s:.3f}–{P[:,2].max()/s:.3f}·S)')
    print(f'  |x| (m): {np.abs(P[:,0]).min():.3f}–{np.abs(P[:,0]).max():.3f}; y: {P[:,1].min():.3f}–{P[:,1].max():.3f}')
    k = np.argmax(mag); print('  ponto de máx:', np.round(V[k] * sc, 3), f'{mag[k]:.1f} mm')
# decomposição analítica do fs da estação do busto (aritmética da superelipse p=2)
ch = a.chest_half(); bust = a.bust_protrusion(); fs = 1 + bust / (ch * 0.8); dd = ch * 0.8
print(f'estação busto z={a.z("bust")+0.004*s:.4f} d={dd:.4f} fs={fs:.3f} → Δcy analítico = {4*dd/(3*math.pi)*(fs-1)*1000:.1f} mm para a frente')
print(f'estação inframamária z={a.z("inframammary"):.4f} fs=1 → Δcy 0; estação jugulum fs=1.02 → Δcy {4*ch*0.72/(3*math.pi)*0.02*1000:.1f} mm')
dz = (a.z("bust") + 0.004 * s - a.z("inframammary")) * 1000
print(f'salto de centroide entre inframamária e busto: {4*dd/(3*math.pi)*(fs-1)*1000:.1f} mm em {dz:.0f} mm de altura → {math.degrees(math.atan(4*dd/(3*math.pi)*(fs-1)*1000/dz)):.1f}° p/ a frente (local)')
