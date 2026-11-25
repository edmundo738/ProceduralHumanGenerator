// THE STALKER v3 — geometria medida (build_stalker2.py) + pivôs
// (stalker2_rig.json) → hierarquia three.js → ANIMAÇÃO PROCEDURAL
// própria (módulo stalker_pose.js?v=db15d471: IK 2-ossos, pés plantados, joelho
// invertido). O módulo de postura é PURO e é partilhado com o
// instrumento tools/creature/anim_check.mjs — a animação é MEDIDA.
//
// BUGS v2 corrigidos aqui (o boneco "esticava"):
//   1. grupos filhos recebiam pivôs ABSOLUTOS como posição LOCAL →
//      cada parte deslocava-se pelo pivô do pai (criatura desmontada);
//   2. torso.scale no GRUPO (pai de tudo) → respiração esticava o
//      boneco; agora escala só na MALHA;
//   3. DORMANT afundava o root −0.42m (pés debaixo do chão) → agora
//      agacha por articulação (IK).
import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import { GLTFLoader } from "three/addons/loaders/GLTFLoader.js";
import { computePose, stepHz } from "./stalker_pose.js?v=db15d471";

const $ = (s) => document.querySelector(s);

// ---------------------------------------------------------------- cena
const scene = new THREE.Scene();
scene.background = new THREE.Color(0x020202);
scene.fog = new THREE.Fog(0x020202, 2.0, 20);
const camera = new THREE.PerspectiveCamera(50, innerWidth / innerHeight, 0.05, 40);
camera.position.set(0, 1.45, 4.6);
const renderer = new THREE.WebGLRenderer({ antialias: false });
renderer.setSize(innerWidth / 2, innerHeight / 2, false);
$("#scene").appendChild(renderer.domElement);
const controls = new OrbitControls(camera, renderer.domElement);
controls.target.set(0, 1.05, 0);
controls.enableDamping = true;
controls.maxDistance = 12; controls.minDistance = 1.2;
controls.maxPolarAngle = 1.65;
scene.add(new THREE.AmbientLight(0x241c20, 1.1));
const spot = new THREE.SpotLight(0xcfc4bd, 55, 30, 0.55, 1.0, 1.2);
spot.position.set(0, 3.6, 2.4); scene.add(spot); scene.add(spot.target);
const rim = new THREE.PointLight(0x3a0d0d, 6, 14);          // contraluz vermelho frio
rim.position.set(-3, 2.0, -4); scene.add(rim);
const eyeLight = new THREE.PointLight(0x660000, 0.0, 3.5); scene.add(eyeLight);
const ground = new THREE.Mesh(new THREE.PlaneGeometry(80, 80),
  new THREE.MeshStandardMaterial({ color: 0x0a0708, roughness: 1 }));
ground.rotation.x = -Math.PI / 2; scene.add(ground);

// ---------------------------------------------------------------- criatura v3
const loader = new GLTFLoader();
const G = {};           // grupos por parte (pivot = origem do grupo)
const M = {};           // meshes por parte
let creatureRoot = null, headG = null, mandibleG = null, eyeMats = [], torsoMesh = null;

async function load() {
  const gltf = await loader.loadAsync("models/stalker2_smooth.glb");
  const def = await (await fetch("models/stalker2_rig.json?v=" + Date.now())).json();
  creatureRoot = new THREE.Group();
  scene.add(creatureRoot);
  for (const o of gltf.scene.children) M[o.name] = o;
  const PV = {};                                    // pivôs absolutos
  for (const r of def.rig) PV[r.name] = r.pivot;
  for (const r of def.rig) {
    const g = new THREE.Group();
    g.name = r.name;
    // LOCAL = pivô − pivô do pai → mundo do grupo = pivô absoluto
    // (bug v2: pivô absoluto como local desmontava a criatura)
    const pp = r.parent ? PV[r.parent] : [0, 0, 0];
    g.position.set(r.pivot[0] - pp[0], r.pivot[1] - pp[1], r.pivot[2] - pp[2]);
    G[r.name] = g;
    const mesh = M[r.name];
    if (mesh) {
      mesh.position.set(-r.pivot[0], -r.pivot[1], -r.pivot[2]);  // verts absolutos
      g.add(mesh);
      if (r.name.startsWith("eye_")) eyeMats.push(mesh.material);
      if (r.name === "torso") torsoMesh = mesh;
    }
    (r.parent ? G[r.parent] : creatureRoot).add(g);
  }
  headG = G.head; mandibleG = G.mandible;
  for (const m of eyeMats) m.emissiveIntensity = 1.0;
  $("#st").textContent = "DORMANT";
}
load().catch((e) => { $("#st").textContent = "ERRO: " + e.message; console.error(e); });

// ---------------------------------------------------------------- FSM
const state = { s: "DORMANT", auto: true, next: 5, mouth: 0 };
const pos = new THREE.Vector3(0, 0, -4);
let target = pos.clone(), speed = 0, phase = 0;
const STATES = {
  DORMANT:      { speed: 0,    eye: 0.35, mouth: 0,   next: [5, 10] },
  ROAMING:      { speed: 0.75, eye: 0.7,  mouth: 0,   next: [6, 11] },
  INVESTIGATING:{ speed: 1.4,  eye: 1.0,  mouth: 0.1, next: [4, 8] },
  STALKING:     { speed: 1.1,  eye: 1.4,  mouth: 0,   next: [7, 12] },
  HUNTING:      { speed: 3.2,  eye: 3.2,  mouth: 1,   next: [6, 9] },
  LOST:         { speed: 0.9,  eye: 0.8,  mouth: 0,   next: [5, 9] },
  DISAPPEARING: { speed: 2.0,  eye: 0.2,  mouth: 0,   next: [3, 5] },
};
function setState(s) {
  if (!STATES[s]) return;
  state.s = s;
  const d = STATES[s];
  speed = d.speed;
  document.querySelectorAll("#ui button[data-s]").forEach((b) => b.classList.toggle("on", b.dataset.s === s));
  $("#st").textContent = s + (s === "HUNTING" ? " 🔥" : "");
  if (s === "ROAMING" || s === "DORMANT") {
    const a = Math.random() * Math.PI * 2, r = 4 + Math.random() * 4;
    target.set(Math.cos(a) * r, 0, Math.sin(a) * r - 2);
  }
  if (s === "DISAPPEARING") {
    const dir = pos.clone().sub(camera.position).setY(0).normalize();
    target.copy(pos).addScaledVector(dir, 12);
  }
  if (s === "HUNTING") target.copy(camera.position).setY(0);
  state.next = d.next[0] + Math.random() * (d.next[1] - d.next[0]);
}
document.querySelectorAll("#ui button[data-s]").forEach((b) =>
  b.addEventListener("click", () => { state.auto = false; $("#auto").classList.remove("on"); setState(b.dataset.s); }));
$("#auto").addEventListener("click", () => {
  state.auto = !state.auto; $("#auto").classList.toggle("on", state.auto); state.next = 1;
});
renderer.domElement.addEventListener("pointerdown", (e) => {
  const r = new THREE.Raycaster();
  r.setFromCamera(new THREE.Vector2((e.clientX / innerWidth) * 2 - 1, -(e.clientY / innerHeight) * 2 + 1), camera);
  const hit = r.intersectObject(ground)[0];
  if (hit && state.auto && ["ROAMING", "LOST", "DORMANT"].includes(state.s)) {
    setState("INVESTIGATING"); target.copy(hit.point).setY(0);
  }
});

// ---------------------------------------------------------------- som
let audio = null;
function initAudio() {
  audio = new (window.AudioContext || window.webkitAudioContext)();
  const len = audio.sampleRate * 2;
  const buf = audio.createBuffer(1, len, audio.sampleRate);
  const d = buf.getChannelData(0);
  for (let i = 0; i < len; i++) d[i] = Math.random() * 2 - 1;
  const src = audio.createBufferSource(); src.buffer = buf; src.loop = true;
  const bp = audio.createBiquadFilter(); bp.type = "bandpass"; bp.frequency.value = 420; bp.Q.value = 1.2;
  const g = audio.createGain(); g.gain.value = 0;
  src.connect(bp).connect(g).connect(audio.destination);
  src.start();
  audio.gain = g;
}
$("#snd").addEventListener("click", () => {
  if (!audio) initAudio();
  if (audio.state === "suspended") audio.resume();
});
let breathT = 0;
function breath(dt) {
  if (!audio) return;
  breathT -= dt;
  const hunting = state.s === "HUNTING";
  if (breathT <= 0) breathT = (hunting ? 0.55 : 1.6) + Math.random() * (hunting ? 0.4 : 2.2);
  const ph = (hunting ? 0.55 : 2.4);
  const env = Math.max(0, Math.sin(Math.min(1, breathT / ph) * Math.PI));
  audio.gain.gain.value = (hunting ? 0.16 : 0.06) * env;
}

// ---------------------------------------------------------------- ANIMAÇÃO (postura do módulo PURO)
const clock = new THREE.Clock();
const tmp = new THREE.Vector3();

function animate() {
  requestAnimationFrame(animate);
  const dt = Math.min(clock.getDelta(), 0.05);
  const t = clock.elapsedTime;
  if (creatureRoot) {
    const d = STATES[state.s];
    const hunting = state.s === "HUNTING";
    if (speed > 0.01) phase += dt * 2 * Math.PI * stepHz(speed) * (1 + 0.05 * Math.sin(t * 0.7));

    // ---- postura (stalker_pose.js?v=db15d471 — o MESMO código que o anim_check.mjs mede)
    const P = computePose(state.s, t, phase, speed);
    for (const [nm, r] of Object.entries(P.parts)) {
      const g = G[nm];
      if (g) g.rotation.set(r[0], r[1] || 0, r[2] || 0);
    }
    // respiração: escala SÓ na malha do tronco (grupo nunca — esticava)
    if (torsoMesh) torsoMesh.scale.set(P.torsoMesh.x, 1, P.torsoMesh.z);
    creatureRoot.position.y = P.rootY;

    // ---- cabeça: tremor do módulo + look-at com ATRASO (a cara segue devagar)
    if (headG) {
      const hp = headG.getWorldPosition(tmp.set(0, 0, 0));
      const dirv = camera.position.clone().sub(hp);
      const yaw = Math.atan2(dirv.x, dirv.z) - creatureRoot.rotation.y;
      const pitch = Math.atan2(dirv.y, Math.hypot(dirv.x, dirv.z));
      const k = 1 - Math.pow(0.004, dt);
      headG.rotation.y += (THREE.MathUtils.clamp(yaw, -1.1, 1.1) - headG.rotation.y) * k;
      headG.rotation.x += (THREE.MathUtils.clamp(-pitch + 0.25, -0.5, 0.6) - headG.rotation.x) * k;
      headG.rotation.z = P.headTremorZ;
    }
    // ---- olhos + mandíbula
    for (const m of eyeMats) m.emissiveIntensity = d.eye * (0.8 + 0.25 * Math.sin(t * 2.3));
    eyeLight.intensity = d.eye * 0.5;
    if (mandibleG) {
      state.mouth += (d.mouth * 0.95 - state.mouth) * Math.min(1, dt * 2.0);
      mandibleG.rotation.x = state.mouth * 0.95 + Math.sin(t * 2.6) * 0.02 * state.mouth;
    }
    // ---- movimento FSM
    const toT = target.clone().sub(pos).setY(0);
    const dist = toT.length();
    if (speed > 0 && dist > (state.s === "HUNTING" ? 1.35 : 0.3)) {
      pos.addScaledVector(toT.normalize(), Math.min(speed * dt, dist));
    }
    if (state.s === "STALKING") {
      const dir = pos.clone().sub(camera.position).setY(0);
      const ang = Math.atan2(dir.x, dir.z) + dt * 0.25;
      target.set(camera.position.x + Math.sin(ang) * 7, 0, camera.position.z + Math.cos(ang) * 7);
      speed = 1.1;
    }
    creatureRoot.position.x = pos.x; creatureRoot.position.z = pos.z;
    const face = (state.s === "STALKING" || state.s === "HUNTING" || dist < 0.4 || state.s === "DORMANT")
      ? camera.position : target;
    const fv = face.clone().sub(creatureRoot.position).setY(0);
    if (fv.lengthSq() > 1e-4) {
      const yaw = Math.atan2(fv.x, fv.z);
      creatureRoot.rotation.y += ((yaw - creatureRoot.rotation.y + Math.PI * 3) % (Math.PI * 2) - Math.PI) * Math.min(1, dt * 3);
    }
    // luz segue + flicker
    spot.position.set(pos.x, 3.6, pos.z + 2.4);
    spot.target.position.copy(pos);
    spot.intensity = 48 + Math.sin(t * 31) * 6 + Math.random() * 8;
    eyeLight.position.copy(creatureRoot.position).add(new THREE.Vector3(0, 1.62, 0));
    // AUTO
    if (state.auto) {
      state.next -= dt;
      if (state.next <= 0) {
        const r = Math.random();
        const nxt = {
          DORMANT: "ROAMING", ROAMING: r < 0.5 ? "STALKING" : "ROAMING",
          INVESTIGATING: r < 0.4 ? "STALKING" : "ROAMING",
          STALKING: r < 0.45 ? "HUNTING" : (r < 0.7 ? "LOST" : "DISAPPEARING"),
          HUNTING: r < 0.5 ? "STALKING" : "LOST",
          LOST: r < 0.5 ? "DORMANT" : "ROAMING", DISAPPEARING: "ROAMING",
        }[state.s] || "ROAMING";
        setState(nxt);
      }
    }
  }
  breath(dt);
  controls.update();
  renderer.render(scene, camera);
}
animate();

addEventListener("resize", () => {
  camera.aspect = innerWidth / innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(innerWidth / 2, innerHeight / 2, false);
});
