// HCG — GERADOR DE CORPOS (caminho A · base mesh CC0 + morphs ao vivo)
// Espelha tools/refstudy/basemesh_proto.py (mesma ordem de morphs, mesmas
// bandas do corpus).  Frame: GLB é glTF (y↑, +z frente, metros); os morphs
// correm no frame NOSSO (z↑, +y frente, mm) — conversão (x,y,z)our↔glTF.
import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import { GLTFLoader } from "three/addons/loaders/GLTFLoader.js";

// ---------------------------------------------------------------- bandas (corpus v1 · A.1 largas)
const BANDS = {
  stature: { min: 1500, max: 1810, step: 5,  def: 1700, label: "Estatura (mm)" },
  waist:   { min: 0.80, max: 1.20, step: 0.01, def: 1.0, label: "Cintura ×base" },
  hip:     { min: 0.94, max: 1.12, step: 0.01, def: 1.0, label: "Anca ×base" },
  shoulder:{ min: 0.96, max: 1.08, step: 0.01, def: 1.0, label: "Ombro ×base" },
  thigh:   { min: 0.95, max: 1.12, step: 0.01, def: 1.0, label: "Coxa ×base" },
  breast:  { min: -0.30, max: 0.55, step: 0.01, def: 0.0, label: "Mama (±projecção)" },
  glute:   { min: -0.20, max: 0.35, step: 0.01, def: 0.0, label: "Glúteo (±projecção)" },
  asym:    { min: 0.0,  max: 0.06, step: 0.005, def: 0.0, label: "Assimetria ε" },
};
const ZONES = { shoulder: [1385, 1470], waist: [1010, 1105], hip: [880, 985], thigh: [690, 880] };

// arquétipos do dono (2026-10-07) — pontos de partida, sliders refinam
const PRESETS = {
  "Base (reset)": {},
  "Boazuda":      { stature: 1660, breast: .45, glute: .30, hip: 1.09, waist: .90, thigh: 1.08 },
  "Magra":        { stature: 1680, waist: .84, hip: .96, breast: -.18, thigh: .96 },
  "Robusta":      { stature: 1690, waist: 1.12, shoulder: 1.06, thigh: 1.10, hip: 1.06 },
  "Leviana":      { stature: 1550, waist: .88, hip: .99, breast: -.05 },
  "Chique":       { stature: 1730, waist: .86, hip: .99, breast: .05 },
  "Anca rabuda":  { hip: 1.11, glute: .32, waist: .88 },
  "Atlética":     { stature: 1700, shoulder: 1.07, waist: .84, thigh: 1.10, breast: -.15 },
  "Modelo":       { stature: 1780, waist: .83, hip: .96, shoulder: 1.02, breast: -.05 },
  "Chamativa":    { breast: .55, hip: 1.08, waist: .82, glute: .25 },
  "Intelectual":  { stature: 1650, waist: .95, hip: 1.02, breast: .12 },
};
const TONES = ["#b9b9bf", "#f6d7c4", "#eab99a", "#d39a6c", "#a8703f", "#7a4a26", "#55301a"];

// ---------------------------------------------------------------- utils
const sm01 = (t) => { t = Math.min(1, Math.max(0, t)); return t * t * (3 - 2 * t); };
const bandW = (z, lo, hi, ramp = 45) => sm01((z - lo) / ramp) * (1 - sm01((z - hi) / ramp));
function mulberry32(a) {
  return function () {
    a |= 0; a = (a + 0x6D2B79F5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

// ---------------------------------------------------------------- estado
const params = {};
for (const k in BANDS) params[k] = BANDS[k].def;

// ---------------------------------------------------------------- cena
const box = document.getElementById("canvas");
const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setPixelRatio(window.devicePixelRatio);
renderer.setSize(box.clientWidth, box.clientHeight);
box.appendChild(renderer.domElement);

const scene = new THREE.Scene();
scene.background = new THREE.Color(0x101016);
const camera = new THREE.PerspectiveCamera(35, box.clientWidth / box.clientHeight, 0.05, 30);
camera.position.set(0.4, 1.15, 3.4);
const controls = new OrbitControls(camera, renderer.domElement);
controls.target.set(0, 0.88, 0);
controls.update();

scene.add(new THREE.AmbientLight(0xffffff, 0.38));
const key = new THREE.DirectionalLight(0xffffff, 2.2); key.position.set(2, 3, 2.5); scene.add(key);
const fill = new THREE.DirectionalLight(0xffffff, 0.7); fill.position.set(-2.5, 1.4, 1.2); scene.add(fill);
const grid = new THREE.GridHelper(4, 24, 0x2c2c38, 0x1c1c26);
grid.position.y = 0.001; scene.add(grid);

const material = new THREE.MeshStandardMaterial({ color: 0xb9b9bf, roughness: 0.6, metalness: 0.0 });

// ---------------------------------------------------------------- base + morph
let baseOurs = null;      // Float32Array (x,y,z) nosso frame, mm
let geometry = null;

function morph() {
  if (!geometry) return;
  const P = baseOurs;
  const pos = geometry.attributes.position.array;
  const n = P.length / 3;
  const s = params.stature / 1700;
  const out = new Float32Array(P);            // trabalha numa cópia
  for (let i = 0; i < n; i++) {
    let x = out[3 * i], y = out[3 * i + 1], z = out[3 * i + 2];
    x *= s; y *= s; z *= s;                                   // estatura
    for (const k of ["shoulder", "waist", "hip", "thigh"]) {  // larguras
      const f = params[k] - 1;
      if (Math.abs(f) < 1e-4) continue;
      const [lo, hi] = ZONES[k];
      const w = bandW(z, lo, hi);
      x += f * x * w; y += 0.6 * f * y * w;
    }
    if (Math.abs(params.breast) > 1e-4) {                     // mama
      const ax = Math.abs(x);
      const w = bandW(z, 1140, 1330, 55) * (1 - sm01((ax - 125) / 40)) * sm01((ax - 12) / 22);
      const asym = 1 + (x < 0 ? params.asym : -params.asym);
      y += params.breast * 28 * w * asym;
    }
    if (Math.abs(params.glute) > 1e-4 && y < -20) {           // glúteo
      const ax = Math.abs(x);
      const w = bandW(z, 830, 965, 50) * (1 - sm01((ax - 115) / 40)) * sm01((ax - 15) / 25);
      y -= params.glute * 30 * w;
    }
    out[3 * i] = x; out[3 * i + 1] = y; out[3 * i + 2] = z;
  }
  // nosso (mm, z↑) → glTF (m, y↑, +z frente): (−x, z, y)/1000
  for (let i = 0; i < n; i++) {
    pos[3 * i] = -out[3 * i] / 1000;
    pos[3 * i + 1] = out[3 * i + 2] / 1000;
    pos[3 * i + 2] = out[3 * i + 1] / 1000;
  }
  geometry.attributes.position.needsUpdate = true;
  geometry.computeVertexNormals();
}

new GLTFLoader().load("models/m00_smooth.glb", (gltf) => {
  const mesh = gltf.scene.children[0];
  mesh.material = material;
  geometry = mesh.geometry;
  const pos = geometry.attributes.position.array;
  const n = pos.length / 3;
  baseOurs = new Float32Array(n * 3);
  for (let i = 0; i < n; i++) {   // glTF → nosso frame (mm)
    baseOurs[3 * i] = -pos[3 * i] * 1000;
    baseOurs[3 * i + 1] = pos[3 * i + 2] * 1000;
    baseOurs[3 * i + 2] = pos[3 * i + 1] * 1000;
  }
  scene.add(mesh);
  morph();
  document.getElementById("seedVal").textContent = "base m00";
}, undefined, (e) => console.error(e));

// ---------------------------------------------------------------- UI
const slidersEl = document.getElementById("sliders");
const sliderInputs = {};
for (const k in BANDS) {
  const b = BANDS[k];
  const div = document.createElement("div");
  div.className = "ctl";
  div.innerHTML = `<label><span>${b.label}</span><span id="v_${k}"></span></label>
    <input type="range" min="${b.min}" max="${b.max}" step="${b.step}" value="${b.def}">`;
  const inp = div.querySelector("input");
  sliderInputs[k] = inp;
  inp.addEventListener("input", () => {
    params[k] = parseFloat(inp.value);
    document.getElementById("v_" + k).textContent =
      k === "stature" ? params[k].toFixed(0) : params[k].toFixed(2);
    morph();
  });
  document.getElementById("v_" + k).textContent =
    k === "stature" ? b.def.toFixed(0) : b.def.toFixed(2);
  slidersEl.appendChild(div);
}

function applyParams(p, label) {
  for (const k in BANDS) {
    params[k] = (p && k in p) ? p[k] : BANDS[k].def;
    sliderInputs[k].value = params[k];
    document.getElementById("v_" + k).textContent =
      k === "stature" ? params[k].toFixed(0) : params[k].toFixed(2);
  }
  if (label !== undefined) document.getElementById("seedVal").textContent = label;
  morph();
}

const presetsEl = document.getElementById("presets");
for (const name in PRESETS) {
  const b = document.createElement("button");
  b.textContent = name;
  b.addEventListener("click", () => applyParams(PRESETS[name], name.toLowerCase()));
  presetsEl.appendChild(b);
}

document.getElementById("btnRandom").addEventListener("click", () => {
  const seed = Math.floor(Math.random() * 999999);
  const rng = mulberry32(seed);
  const p = {};
  for (const k in BANDS) {
    const b = BANDS[k];
    p[k] = b.min + rng() * (b.max - b.min);
    if (k === "stature") p[k] = Math.round(p[k] / 5) * 5;
  }
  applyParams(p, String(seed));
});

const tonesEl = document.getElementById("tones");
TONES.forEach((c, i) => {
  const b = document.createElement("button");
  b.style.background = c;
  if (i === 0) b.className = "sel";
  b.addEventListener("click", () => {
    material.color.set(c);
    for (const o of tonesEl.children) o.className = "";
    b.className = "sel";
  });
  tonesEl.appendChild(b);
});

// ---------------------------------------------------------------- loop
window.addEventListener("resize", () => {
  camera.aspect = box.clientWidth / box.clientHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(box.clientWidth, box.clientHeight);
});
renderer.setAnimationLoop(() => renderer.render(scene, camera));
