#!/usr/bin/env node
// INSTRUMENTO v3 — mede a ANIMAÇÃO do THE STALKER (não a geometria).
// Monta a MESMA hierarquia que tools/preview/site/stalker.js (pivô −
// pivô do pai; malha a −pivô) e aplica a MESMA postura (módulo puro
// tools/preview/site/stalker_pose.js). Spec A1–A6 (bandas declaradas
// ANTES de correr, docs/CREATURE_SPEC_STALKER.md §animação):
//   A1 ossos: comprimentos constantes ≤ 2mm (apanha escala em grupos)
//   A2 solas: nunca abaixo de −25mm (pés debaixo do chão)
//   A3 patinação: contacto |vz pé| ≤ 0.35·v + 0.15 m/s
//   A4 bob do root: amplitude ≤ 60mm
//   A5 de pé (não-DORMANT): topo da cabeça ∈ [1.50, 1.86] m
//   A6 DORMANT: topo ∈ [0.90, 1.45] (agacha a sério) + |rx canela| ≥ 0.8
// Saída: tabela + out/refstudy/stalker_anim_check.json
import * as THREE from "../../out/preview/vendor/three/three.module.js";
import { computePose, stepHz } from "../../tools/preview/site/stalker_pose.js";
import fs from "node:fs";
import path from "node:path";

const ROOT = path.resolve(import.meta.dirname, "../..");
const GLB = fs.readFileSync(path.join(ROOT, "site/models/stalker2_smooth.glb"));
const RIG = JSON.parse(fs.readFileSync(path.join(ROOT, "site/models/stalker2_rig.json"), "utf8"));

// ---- GLB → geometrias (parse directo do binário)
const jlen = GLB.readUInt32LE(12);
const js = JSON.parse(GLB.slice(20, 20 + jlen).toString("utf8"));
let binOff = 20 + jlen;
binOff += (4 - (binOff % 4)) % 4;
const blen = GLB.readUInt32LE(binOff);
const BIN = GLB.slice(binOff + 8, binOff + 8 + blen);

// NOTA: `new Float32Array(nodeBuffer)` converteria BYTES elemento-a-
// elemento (bug clássico) — reinterpreter por LE explícito.
function f32le(b) {
  const out = new Float32Array(b.length / 4);
  for (let i = 0; i < out.length; i++) out[i] = b.readFloatLE(i * 4);
  return out;
}
function u16le(b) {
  const out = new Uint16Array(b.length / 2);
  for (let i = 0; i < out.length; i++) out[i] = b.readUInt16LE(i * 2);
  return out;
}
function u32le(b) {
  const out = new Uint32Array(b.length / 4);
  for (let i = 0; i < out.length; i++) out[i] = b.readUInt32LE(i * 4);
  return out;
}
function accData(ai) {
  const a = js.accessors[ai], v = js.bufferViews[a.bufferView];
  return BIN.slice(v.byteOffset + (a.byteOffset || 0), v.byteOffset + (a.byteOffset || 0) + a.count * 12);
}
const geos = {};
for (const m of js.meshes) {
  const pr = m.primitives[0];
  const g = new THREE.BufferGeometry();
  g.setAttribute("position", new THREE.BufferAttribute(f32le(accData(pr.attributes.POSITION)), 3));
  const ia = js.accessors[pr.indices], iv = js.bufferViews[ia.bufferView];
  const ib = BIN.slice(iv.byteOffset + (ia.byteOffset || 0), iv.byteOffset + (ia.byteOffset || 0) + ia.count * (ia.componentType === 5123 ? 2 : 4));
  const idx = ia.componentType === 5123 ? u16le(ib) : u32le(ib);
  g.setIndex(new THREE.BufferAttribute(idx, 1));
  geos[m.name] = g;
}

// ---- hierarquia IGUAL ao stalker.js (sincronizar se o site mudar)
const root = new THREE.Group();
const G = {}, M = {};
const PV = {};
for (const r of RIG.rig) PV[r.name] = r.pivot;
for (const r of RIG.rig) {
  const g = new THREE.Group();
  const pp = r.parent ? PV[r.parent] : [0, 0, 0];
  g.position.set(r.pivot[0] - pp[0], r.pivot[1] - pp[1], r.pivot[2] - pp[2]);
  G[r.name] = g;
  if (geos[r.name]) {
    const mesh = new THREE.Mesh(geos[r.name], new THREE.MeshBasicMaterial());
    mesh.position.set(-r.pivot[0], -r.pivot[1], -r.pivot[2]);
    g.add(mesh);
    M[r.name] = mesh;
  }
  (r.parent ? G[r.parent] : root).add(g);
}

// ---- ossos a medir (pivôs = articulações)
const BONES = [];
for (const s of ["R", "L"]) {
  BONES.push(["ombro" + s, "upperarm_" + s, "forearm_" + s]);
  BONES.push(["cotovelo" + s, "forearm_" + s, "hand_" + s]);
  BONES.push(["anca" + s, "thigh_" + s, "shin_" + s]);
  BONES.push(["joelho" + s, "shin_" + s, "foot_" + s]);
}
BONES.push(["pescoco", "torso", "head"]);
const rest = {};
root.updateMatrixWorld(true);
const wp = (n) => G[n].getWorldPosition(new THREE.Vector3());
for (const [nm, a, b] of BONES) rest[nm] = wp(a).distanceTo(wp(b));

// ---- simulação por estado (8s @ 30fps; root avança à velocidade do estado)
const STATES = { DORMANT: 0, ROAMING: 0.75, INVESTIGATING: 1.4, STALKING: 1.1, HUNTING: 3.2, LOST: 0.9, DISAPPEARING: 2.0 };
const R = { per_state: {}, worst: {} };
const tmpV = new THREE.Vector3();
let a1 = 0, a2 = 1e9, a3 = 0, a4 = 0, a5min = 1e9, a5max = -1e9, a6top = 0, a6shin = 0;
let maxBulge = 0;
const GLOB = { thR: [], thL: [], contR: [], contL: [] };   // A7 global (estados móveis)

for (const [st, v] of Object.entries(STATES)) {
  // reset
  for (const g of Object.values(G)) g.rotation.set(0, 0, 0);
  for (const m of Object.values(M)) m.scale.set(1, 1, 1);
  root.position.set(0, 0, 0); root.rotation.set(0, 0, 0);
  let phase = 0, t = 0, rootZ = 0, prevFootZ = null, maxDrift = 0;
  let rootMin = 1e9, rootMax = -1e9;
  const thR = [], thL = [], contR = [], contL = [];   // A7
  const dt = 1 / 30, N = 240;
  const stW = { bone: 0, sole: 1e9, drift: 0, top: 0 };
  for (let i = 0; i < N; i++) {
    t += dt;
    if (v > 0.01) phase += dt * 2 * Math.PI * stepHz(v);
    rootZ += v * dt;
    const P = computePose(st, t, phase, v);
    for (const [nm, r] of Object.entries(P.parts)) {
      const g = G[nm];
      if (g) g.rotation.set(r[0], r[1] || 0, r[2] || 0);
    }
    if (v > 0.01) { thR.push(P.parts["thigh_R"][0]); thL.push(P.parts["thigh_L"][0]); }
    if (M.torso) M.torso.scale.set(P.torsoMesh.x, 1, P.torsoMesh.z);
    if (P.bulge) for (const [nm, b] of Object.entries(P.bulge)) {
      const m = M[nm];
      if (m) m.scale.set(1 + b, 1 - b * 0.5, 1 + b);
      maxBulge = Math.max(maxBulge, v > 0.01 ? b : 0);
    }
    root.position.set(0, P.rootY, rootZ);
    root.updateMatrixWorld(true);
    // A1 ossos
    for (const [nm, a, b] of BONES) {
      const d = Math.abs(wp(a).distanceTo(wp(b)) - rest[nm]);
      stW.bone = Math.max(stW.bone, d);
    }
    // A2/A3 solas + patinação
    let contF = {};
    for (const s of ["R", "L"]) {
      const posA = geos["foot_" + s].attributes.position;
      const mtx = M["foot_" + s].matrixWorld;
      let ymin = 1e9;
      for (let k = 0; k < posA.count; k++) {
        tmpV.fromBufferAttribute(posA, k).applyMatrix4(mtx);
        if (tmpV.y < ymin) ymin = tmpV.y;
      }
      stW.sole = Math.min(stW.sole, ymin);
      // contacto = garra CRavada (≤5mm); limiar de 30mm apanhava frames
      // de balanço inicial (pé a descolar ainda baixo) → "drift" do
      // balanço, não do apoio (refinamento declarado §v3.3)
      if (v > 0.01) contF[s] = ymin < 0.005;
      if (v > 0.01 && s === "R") contR.push(contF[s]);
      if (v > 0.01 && s === "L") contL.push(contF[s]);
      if (ymin < 0.005) {                                 // garra cravada
        const fz = wp("foot_" + s).z;
        if (prevFootZ !== null && prevFootZ[s] !== undefined) {
          maxDrift = Math.max(maxDrift, Math.abs((fz - prevFootZ[s]) / dt));
        }
        prevFootZ = prevFootZ || {};
        prevFootZ[s] = fz;
      } else if (prevFootZ) prevFootZ[s] = undefined;
    }
    stW.drift = Math.max(stW.drift, maxDrift);
    // A4 bob / A5/A6 topo
    const hp = geos.head ? wp("head") : new THREE.Vector3();
    const hgeo = geos.head.attributes.position;
    let top = -1e9;
    const hmtx = M.head.matrixWorld;
    for (let k = 0; k < hgeo.count; k += 7) {
      tmpV.fromBufferAttribute(hgeo, k).applyMatrix4(hmtx);
      if (tmpV.y > top) top = tmpV.y;
    }
    stW.top = Math.max(stW.top, top);
    // A4 bob: AMPLITUDE dentro do estado (offset estático do agachado
    // DORMANT não é bob — definição afinada, ver SPEC §animação)
    rootMin = Math.min(rootMin, P.rootY);
    rootMax = Math.max(rootMax, P.rootY);
    if (st === "DORMANT") {
      a6top = Math.max(a6top, top);
      a6shin = Math.max(a6shin, Math.abs(P.parts["shin_R"][0]));
    } else {
      a5min = Math.min(a5min, top); a5max = Math.max(a5max, top);
    }
  }
  a1 = Math.max(a1, stW.bone);
  a2 = Math.min(a2, stW.sole);
  a3 = Math.max(a3, stW.drift);
  a4 = Math.max(a4, Math.max(0, rootMax - rootMin));
  if (v > 0.01) { GLOB.thR.push(...thR); GLOB.thL.push(...thL);
                  GLOB.contR.push(...contR); GLOB.contL.push(...contL); }
  R.per_state[st] = { bone_mm: +stW.bone.toFixed(1), sole_mm: +(stW.sole * 1000).toFixed(1),
    drift_ms: +stW.drift.toFixed(2), top_m: +stW.top.toFixed(3) };
}

// ---- A7 anti-fase (Pearson coxa_R vs coxa_L, estados móveis)
function pearson(a, b) {
  const n = a.length;
  const ma = a.reduce((x, y) => x + y, 0) / n, mb = b.reduce((x, y) => x + y, 0) / n;
  let sab = 0, sa = 0, sb = 0;
  for (let i = 0; i < n; i++) {
    const da = a[i] - ma, db = b[i] - mb;
    sab += da * db; sa += da * da; sb += db * db;
  }
  return sab / Math.sqrt(sa * sb);
}
const a7corr = pearson(GLOB.thR, GLOB.thL);
const a7duty = Math.max(GLOB.contR.filter(Boolean).length / GLOB.contR.length,
                        GLOB.contL.filter(Boolean).length / GLOB.contL.length);
let dbl = 0;
for (let i = 0; i < GLOB.contR.length; i++) if (GLOB.contR[i] && GLOB.contL[i]) dbl++;
const a7double = dbl / GLOB.contR.length;

// ---- veredictos
const SPEC = {
  A1_ossos_mm: [0, 2],
  A2_sola_min_mm: [-25, 1e9],
  A3_patin_ms: [0, 1e9],          // relativo: 0.35·v + 0.15 (calculado)
  A4_bob_mm: [0, 60],
  A5_topo_de_pe_m: [1.50, 1.86],
  A6_topo_dormant_m: [0.90, 1.45],
  A7_anti_fase: [-1e9, -0.75],
  A7b_duty: [0, 0.70],
  A7c_duplo_apoio: [0, 0.30],
  A8_bombeio: [0.02, 0.15],
};
const vSpeed = STATES.HUNTING;
const a3band = 0.35 * vSpeed + 0.15;
const vals = {
  A1_ossos_mm: a1 * 1000, A2_sola_min_mm: a2 * 1000, A3_patin_ms: a3,
  A4_bob_mm: a4 * 1000, A5_topo_de_pe_m: a5max, A6_topo_dormant_m: a6top,
  A7_anti_fase: a7corr, A7b_duty: a7duty, A7c_duplo_apoio: a7double,
  A8_bombeio: maxBulge,
};
const verdicts = {
  A1_ossos_mm: a1 * 1000 <= 2 ? "PASS" : "FAIL",
  A2_sola_min_mm: a2 * 1000 >= -25 ? "PASS" : "FAIL",
  A3_patin_ms: a3 <= a3band ? "PASS" : "FAIL",
  A4_bob_mm: a4 * 1000 <= 60 ? "PASS" : "FAIL",
  A5_topo_de_pe_m: (a5min >= 1.50 && a5max <= 1.86) ? "PASS" : "FAIL",
  A6_topo_dormant_m: (a6top >= 0.90 && a6top <= 1.45 && a6shin >= 0.8) ? "PASS" : "FAIL",
  A7_anti_fase: a7corr <= -0.75 ? "PASS" : "FAIL",
  A7b_duty: a7duty <= 0.70 ? "PASS" : "FAIL",
  A7c_duplo_apoio: a7double <= 0.30 ? "PASS" : "FAIL",
  A8_bombeio: (maxBulge >= 0.02 && maxBulge <= 0.15) ? "PASS" : "FAIL",
};
R.measures = { ...vals, A6_shin_rx_abs: a6shin };
R.spec = SPEC;
R.verdicts = verdicts;
R.a3_band_ms = a3band;
R.n_pass = Object.values(verdicts).filter((v) => v === "PASS").length;

console.log("métrica                          valor      banda            veredicto");
const fmt = (k, v, band) => console.log(
  `${k.padEnd(28)} ${String(v).padEnd(10)} ${band.padEnd(16)} ${verdicts[k]}`);
fmt("A1_ossos_mm", (a1 * 1000).toFixed(1), "[0..2]");
fmt("A2_sola_min_mm", (a2 * 1000).toFixed(1), "[-25..∞]");
fmt("A3_patin_ms", a3.toFixed(2), `[0..${a3band.toFixed(2)}]`);
fmt("A4_bob_mm", (a4 * 1000).toFixed(1), "[0..60]");
fmt("A5_topo_de_pe_m", `${a5min.toFixed(2)}..${a5max.toFixed(2)}`, "[1.50..1.86]");
fmt("A6_topo_dormant_m", a6top.toFixed(2), "[0.90..1.45]");
fmt("A7_anti_fase", a7corr.toFixed(2), "[-∞..-0.75]");
fmt("A7b_duty", a7duty.toFixed(2), "[0..0.70]");
fmt("A7c_duplo_apoio", a7double.toFixed(2), "[0..0.30]");
fmt("A8_bombeio", maxBulge.toFixed(3), "[0.02..0.15]");
console.log(`\n${R.n_pass}/${Object.keys(SPEC).length} PASS · A6_shin_rx=${a6shin.toFixed(2)} rad`);
console.log("por estado:", JSON.stringify(R.per_state));

fs.mkdirSync(path.join(ROOT, "out/refstudy"), { recursive: true });
fs.writeFileSync(path.join(ROOT, "out/refstudy/stalker_anim_check.json"), JSON.stringify(R, null, 1));
