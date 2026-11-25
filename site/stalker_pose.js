// THE STALKER — POSTURA PROCEDURAL (módulo PURO, sem THREE/DOM).
// Partilhado entre o site (stalker.js) e o INSTRUMENTO de medição
// (tools/creature/anim_check.mjs): o que é medido é EXACTAMENTE o que
// corre no browser.
//
// Correcções v3 (gate do dono: "a animação estica o boneco"):
//   1. escala NUNCA em grupos (só na MALHA do tronco — grupos são pais
//      de cabeça/braços/pernas: escalá-los estica o boneco);
//   2. pernas por IK de 2 ossos (coxa 0.500 + canela 0.475, pivôs do
//      rig): tornozelo segue um ALVO → pés tocam o chão (fim do patinar
//      e dos pés debaixo do piso); joelho INVERTIDO (dobra p/ trás);
//   3. DORMANT agacha por articulação (root −0.25 + IK), nunca por
//      translação cega;
//   4. frequência de passada ligada à velocidade (f = v/0.95 clamp
//      0.55..2.2 Hz) e meio-passo = v/(2πf) → pé plantado ~parado no
//      mundo à meio da fase de apoio (medido em A3).

export const LEG = { L1: 0.500, L2: 0.475, hipY: 1.06, ankleY: 0.085 };
const clamp = (x, a, b) => Math.max(a, Math.min(b, x));

// frequência de passada (Hz) para uma velocidade (m/s)
export function stepHz(v) {
  return clamp(v / 0.95, 0.55, 2.7);
}
// meio-passo (m): apoio recua 2·hs = v·T/2 → pé PARADO no mundo
export function halfStride(v) {
  return Math.min(0.30, v / (4 * stepHz(v)));
}

// IK de 2 ossos no plano sagital (y=altura, z=frente). s=+1 → joelho
// invertido (dobra p/ trás, tipo ave). Devolve rotações .x RELATIVAS.
function legIK(hy, hz, ay, az, L1, L2, s, toe) {
  const dy = ay - hy, dz = az - hz;
  let r = Math.hypot(dy, dz);
  const rMax = (L1 + L2) * 0.999;
  let tz = az;
  if (r > rMax) {                       // alvo fora do alcance: puxa p/ dentro
    const k = rMax / r;
    tz = hz + dz * k;
    r = rMax;
  }
  const base = Math.atan2(-tz + hz, -(ay - hy));   // 0 = perna pende
  const phi = Math.acos(clamp((L1 * L1 + r * r - L2 * L2) / (2 * L1 * r), -1, 1));
  const psi = Math.acos(clamp((L2 * L2 + r * r - L1 * L1) / (2 * L2 * r), -1, 1));
  return {
    thigh: base + s * phi,
    shin: -s * (phi + psi),
    foot: -(base - s * psi) + toe,      // palm plana + dedos p/ baixo
  };
}

// -------------------------------------------------------------- postura
// s: estado FSM; t: segundos; phase: fase da passada (rad, avança no
// caller); speed: m/s do estado. Devolve rotações a APLICAR (SET, não
// acumular) + escala da MALHA do tronco + y do root (m).
export function computePose(s, t, phase, speed) {
  const dormant = s === "DORMANT";
  const hunting = s === "HUNTING";
  const moving = speed > 0.01;
  const parts = {};
  const hs = halfStride(speed);
  const lift = 0.07 + (speed > 2 ? 0.06 : 0) + (hunting ? 0.02 : 0);
  const f = stepHz(speed);
  const W = 2 * Math.PI * f;

  const rootY = dormant ? -0.33
    : moving ? -0.02 - 0.02 * Math.abs(Math.cos(phase)) * (speed > 2 ? 1.3 : 1)
    : 0;

  // ANTI-FASE OBRIGATÓRIA (R=0, L=π): bug v3.1 — as duas pernas
  // partilhavam a MESMA fase (saltava com as duas juntas; o dono viu
  // "as pernas mexem-se de forma unificada"). +0.18 = claudicação.
  for (const [sd, ph] of [["R", 0], ["L", Math.PI]]) {
    const p = phase + ph + (sd === "L" ? 0.10 : 0);   // leve atraso L (claudicação no PASSO: 0.94)
    const hz0 = 0.008, hxz = 0.0;
    if (dormant) {
      // agachado: tornozelo no chão, ligeiro avanço; hip efectivo = rootY
      const k = legIK(LEG.hipY + rootY, hz0, LEG.ankleY, 0.10, LEG.L1, LEG.L2, 1, -0.12);
      parts["thigh_" + sd] = [k.thigh, 0, 0];
      parts["shin_" + sd] = [k.shin, 0, 0];
      parts["foot_" + sd] = [k.foot, 0, 0];
    } else {
      // ciclo do pé: apoio (frac<0.5) recua à velocidade do CORPO
      // (z mundo do pé ≈ constante = plantado); balanço avança em
      // smoothstep e eleva cedo (garra sai do chão depressa)
      const frac = ((p / (2 * Math.PI)) % 1 + 1) % 1;
      // folga da garra: alvo do tornozelo acima do chão pelo drop dos
      // dedos (medido: HUNTING escavava −25.5mm sem folga)
      const ay0 = LEG.ankleY + (speed > 2 ? 0.030 : 0.0);   // passo: garras ao chão
      let ay, az;
      if (frac < 0.5) {
        az = hs * (1 - 4 * frac);        // +hs → −hs linear (dz/dt = −v)
        // heel-strike / toe-off (anatomia do passo): alvo sobe 18-20mm
        // nas PONTAS da fase de apoio — sem isto o IK clampa a perna
        // 100% esticada no início do contacto e o pé SALTA 28mm/frame
        ay = ay0
          + 0.018 * (frac < 0.12 ? (0.12 - frac) / 0.12 : 0)
          + 0.020 * (frac > 0.40 ? (frac - 0.40) / 0.10 : 0);
      } else {
        const sg = (frac - 0.5) * 2;     // 0..1 balanço
        const ss = sg * sg * (3 - 2 * sg);
        az = -hs + 2 * hs * ss;
        ay = ay0 + lift * Math.sin(Math.PI * sg) ** 0.7;
      }
      const k = legIK(LEG.hipY + (moving ? -0.02 - 0.02 * Math.abs(Math.cos(p)) : 0), hz0,
        ay, az, LEG.L1, LEG.L2, 1, -0.12);
      parts["thigh_" + sd] = [k.thigh, 0, 0];
      parts["shin_" + sd] = [k.shin, 0, 0];
      parts["foot_" + sd] = [k.foot, 0, 0];
    }
  }

  // ---- braços: pendem, contrafase com a perna do mesmo lado
  for (const [sd, ph] of [["R", 0], ["L", Math.PI]]) {
    const p = phase + ph + (sd === "L" ? 0.18 : 0);
    if (dormant) {
      parts["upperarm_" + sd] = [0.25, 0, (sd === "R" ? -1 : 1) * 0.30];
      parts["forearm_" + sd] = [0.60, 0, 0];
      parts["hand_" + sd] = [0.15, 0, 0];
    } else {
      const amp = hunting ? 0.55 : 0.30;
      parts["upperarm_" + sd] = [-0.08 + Math.sin(p) * amp, 0,
        (sd === "R" ? -1 : 1) * (0.14 + 0.05 * Math.sin(t * 0.9 + ph))];
      parts["forearm_" + sd] = [0.3 + Math.sin(p + 0.5) * 0.18, 0, 0];
      parts["hand_" + sd] = [Math.sin(p + 0.8) * 0.22 + 0.1, 0, 0];
    }
  }

  // ---- tronco: ROTAÇÕES apenas (nunca escala no grupo!)
  parts["torso"] = [
    dormant ? 0.30 : 0.10 + Math.sin(t * 1.1) * 0.015,
    0,
    moving ? Math.sin(phase * 0.5) * 0.05 : 0.012 * Math.sin(t * 0.6),
  ];
  // respiração: escala só da MALHA (x lateral, z profundidade; y=1 SEMPRE)
  const br = 1 + Math.sin(t * 1.9) * 0.012 + Math.sin(t * 7.3) * 0.004;
  const torsoMesh = { x: br, z: 1 + (br - 1) * 0.8 };

  // ---- BOMBEIO MUSCULAR (docs/ANATOMY_RESEARCH_STALKER.md §2): a
  // barriga engrossa quando a articulação FILHA dobra (bíceps com o
  // cotovelo, quadríceps com o joelho). Escala da MALHA (nunca do
  // grupo — regra v3.1), amplitude pequena e limitada.
  const bulge = {};
  const B = (x, k, cap) => Math.min(cap, k * Math.abs(x || 0));
  for (const sd of ["R", "L"]) {
    const elbow = (parts["forearm_" + sd] || [0])[0];
    const knee = (parts["shin_" + sd] || [0])[0];
    const ankle = (parts["foot_" + sd] || [0])[0];
    bulge["upperarm_" + sd] = B(elbow, 0.10, 0.14);
    bulge["forearm_" + sd] = B(elbow, 0.07, 0.11);
    bulge["thigh_" + sd] = B(knee, 0.08, 0.12);
    bulge["shin_" + sd] = B(knee, 0.06, 0.10) + B(ankle, 0.02, 0.03);
  }

  const headTremorZ = Math.sin(t * 13.0) * 0.02 * (hunting ? 2 : 1);
  return { parts, torsoMesh, rootY, headTremorZ, bulge, W };
}
