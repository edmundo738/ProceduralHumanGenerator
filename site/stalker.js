// THE STALKER — O Encharcado · cena de teste (PSX moderno sujo)
// Modelo: stalker.glb (Michelle rig + texturas PBR geradas) + clips Xbot
// retonados. FSM: DORMANT/ROAMING/INVESTIGATING/STALKING/HUNTING/LOST/
// DISAPPEARING. Look-at com atraso, respiração irregular, boca com dentes,
// olhos emissivos, som de respiração sintetizado. Clique no chão = ruído.
import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import { GLTFLoader } from "three/addons/loaders/GLTFLoader.js";
import * as SkeletonUtils from "three/addons/utils/SkeletonUtils.js";

const B = (n) => "mixamorig:" + n;
const $ = (s) => document.querySelector(s);

// ---------------------------------------------------------------- cena
const scene = new THREE.Scene();
scene.background = new THREE.Color(0x020202);
scene.fog = new THREE.Fog(0x020202, 1.5, 17);
const camera = new THREE.PerspectiveCamera(50, innerWidth / innerHeight, 0.05, 40);
camera.position.set(0, 1.55, 5.5);
const renderer = new THREE.WebGLRenderer({ antialias: false });
renderer.setSize(innerWidth / 2, innerHeight / 2, false);   // PSX: meia resolução
$("#scene").appendChild(renderer.domElement);
const controls = new OrbitControls(camera, renderer.domElement);
controls.target.set(0, 1.1, 0);
controls.enableDamping = true;
controls.maxDistance = 12; controls.minDistance = 1.2;
controls.maxPolarAngle = 1.65;

scene.add(new THREE.AmbientLight(0x1a1418, 0.6));
const spot = new THREE.SpotLight(0xcfc4bd, 60, 30, 0.55, 1.0, 1.2);
spot.position.set(0, 4.5, 0); scene.add(spot); scene.add(spot.target);
const eyeLight = new THREE.PointLight(0x660000, 0.0, 3.5); scene.add(eyeLight);

const ground = new THREE.Mesh(new THREE.PlaneGeometry(80, 80),
  new THREE.MeshStandardMaterial({ color: 0x0a0708, roughness: 1 }));
ground.rotation.x = -Math.PI / 2; scene.add(ground);

// ---------------------------------------------------------------- criatura
const loader = new GLTFLoader();
let creature = null, mixer = null, clips = {}, actions = {};
let head = null, eyes = [], jaw = null, eyeMats = [];
const state = { s: "DORMANT", auto: true, t: 0, next: 5, mouth: 0, lastSeen: new THREE.Vector3() };

function findSkinned(root) { let o = null; root.traverse((x) => { if (x.isSkinnedMesh && !o) o = x; }); return o; }

function buildFace() {
  // olhos + boca anexados ao osso da cabeça (posições em espaço do osso)
  const wp = new THREE.Vector3(), wq = new THREE.Quaternion();
  head.getWorldPosition(wp); head.getWorldQuaternion(wq);
  const up = new THREE.Vector3(0, 1, 0).applyQuaternion(wq);
  const ctr = wp.clone().addScaledVector(up, 0.075);
  const fwd = new THREE.Vector3(0, 0, 1).applyQuaternion(creature.quaternion);
  const side = new THREE.Vector3(1, 0, 0).applyQuaternion(creature.quaternion);
  const mkEye = (sx) => {
    const m = new THREE.MeshStandardMaterial({ color: 0x020101, roughness: 0.15,
      emissive: 0x2a0000, emissiveIntensity: 0.7 });
    const e = new THREE.Mesh(new THREE.SphereGeometry(0.026, 10, 8), m);
    e.position.copy(ctr).addScaledVector(fwd, 0.088).addScaledVector(side, sx * 0.052)
      .addScaledVector(up, 0.012);
    e.position.copy(head.worldToLocal(e.position.clone()));
    eyeMats.push(m); eyes.push(e); head.add(e);
    return e;
  };
  mkEye(1); mkEye(-1);
  // boca: cavidade escura + dentes (2 fileiras; a inferior abre)
  const mouth = new THREE.Group();
  const cav = new THREE.Mesh(new THREE.SphereGeometry(0.062, 10, 8),
    new THREE.MeshStandardMaterial({ color: 0x050000, roughness: 0.9 }));
  cav.scale.set(1, 0.55, 0.8); mouth.add(cav);
  const toothG = new THREE.ConeGeometry(0.0072, 0.03, 5);
  const toothM = new THREE.MeshStandardMaterial({ color: 0x8a7a6a, roughness: 0.5 });
  for (let r = 0; r < 2; r++) for (let i = 0; i < 9; i++) {
    const t = new THREE.Mesh(toothG, toothM);
    const a = (i / 8 - 0.5) * 1.5;
    t.position.set(Math.sin(a) * 0.05, (r ? -1 : 1) * 0.028, Math.cos(a) * 0.045);
    t.rotation.x = (r ? 1 : -1) * 0.15;
    if (r) { t.userData.jaw = true; }
    mouth.add(t);
  }
  jaw = new THREE.Group(); jaw.position.y = -0.005;
  mouth.children.filter((c) => c.userData.jaw).forEach((c) => { mouth.remove(c); jaw.add(c); });
  mouth.add(jaw);
  mouth.position.copy(ctr).addScaledVector(fwd, 0.085).addScaledVector(up, -0.045);
  mouth.quaternion.copy(creature.quaternion);
  mouth.rotation.x += 0.15;
  const mp = head.worldToLocal(mouth.position.clone());
  mouth.position.copy(mp);
  mouth.quaternion.copy(head.quaternion);
  head.add(mouth);
  state.mouthGroup = mouth;
}

async function load() {
  const g = await loader.loadAsync("models/stalker_smooth.glb");
  creature = g.scene;
  scene.add(creature);
  mixer = new THREE.AnimationMixer(creature);
  for (const c of g.animations) { clips[c.name] = c; actions[c.name] = mixer.clipAction(c); }
  const xb = await loader.loadAsync("models/anim_xbot.glb");
  const src = findSkinned(xb.scene), dst = findSkinned(creature);
  if (src && dst) for (const n of ["idle", "walk", "run"]) {
    const c = xb.animations.find((a) => a.name === n);
    if (c) { clips[n] = SkeletonUtils.retargetClip(dst, src, c); actions[n] = mixer.clipAction(clips[n]); }
  }
  head = creature.getObjectByName(B("Head"));
  buildFace();
  play("idle");
  $("#st").textContent = "DORMANT";
}
load().catch((e) => { $("#st").textContent = "ERRO: " + e.message; console.error(e); });

function play(name) {
  const a = actions[name]; if (!a) return;
  for (const k in actions) if (actions[k] !== a) actions[k].fadeOut(0.3);
  a.reset().fadeIn(0.3).play();
}

// ---------------------------------------------------------------- FSM
const pos = new THREE.Vector3(0, 0, -4);
let target = pos.clone(), speed = 0;
const STATES = {
  DORMANT:     { speed: 0,    clip: "idle", mouth: 0, eye: 0.35, next: [5, 10] },
  ROAMING:     { speed: 0.75, clip: "walk", mouth: 0, eye: 0.7,  next: [6, 11] },
  INVESTIGATING:{ speed: 1.4, clip: "walk", mouth: 0.1, eye: 1.0, next: [4, 8] },
  STALKING:    { speed: 1.1,  clip: "walk", mouth: 0,   eye: 1.4, next: [7, 12] },
  HUNTING:     { speed: 3.2,  clip: "run",  mouth: 1,  eye: 3.2, next: [6, 9] },
  LOST:        { speed: 0.9,  clip: "walk", mouth: 0,   eye: 0.8, next: [5, 9] },
  DISAPPEARING:{ speed: 2.0,  clip: "walk", mouth: 0,   eye: 0.2, next: [3, 5] },
};
function setState(s) {
  if (!STATES[s]) return;
  state.s = s;
  const d = STATES[s];
  play(d.clip);
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
  if (s === "LOST") target.copy(state.lastSeen);
  if (s === "HUNTING") target.copy(camera.position).setY(0);
  state.next = d.next[0] + Math.random() * (d.next[1] - d.next[0]);
}
document.querySelectorAll("#ui button[data-s]").forEach((b) =>
  b.addEventListener("click", () => { state.auto = false; $("#auto").classList.remove("on"); setState(b.dataset.s); }));
$("#auto").addEventListener("click", () => {
  state.auto = !state.auto; $("#auto").classList.toggle("on", state.auto); state.next = 1;
});

// ruído: clique no chão
renderer.domElement.addEventListener("pointerdown", (e) => {
  const r = new THREE.Raycaster();
  r.setFromCamera(new THREE.Vector2((e.clientX / innerWidth) * 2 - 1, -(e.clientY / innerHeight) * 2 + 1), camera);
  const hit = r.intersectObject(ground)[0];
  if (hit && state.auto && ["ROAMING", "LOST", "DORMANT"].includes(state.s)) {
    target.copy(hit.point).setY(0);
    setState("INVESTIGATING"); target.copy(hit.point);
  }
});

// ---------------------------------------------------------------- som (respiração)
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

// ---------------------------------------------------------------- loop
const clock = new THREE.Clock();
const fwdV = new THREE.Vector3();
const lookQ = new THREE.Quaternion();
let headLag = new THREE.Quaternion();

function animate() {
  requestAnimationFrame(animate);
  const dt = Math.min(clock.getDelta(), 0.05);
  const t = clock.elapsedTime;
  if (creature && mixer) {
    mixer.update(dt);
    // corcunda + braços longos (por cima do clip, cada frame)
    const sp = creature.getObjectByName(B("Spine")), sp1 = creature.getObjectByName(B("Spine1")),
          sp2 = creature.getObjectByName(B("Spine2")), nk = creature.getObjectByName(B("Neck"));
    if (sp) { sp.rotation.x += 0.14; sp1.rotation.x += 0.14; sp2.rotation.x += 0.13; nk.rotation.x -= 0.22; }
    for (const s of ["Left", "Right"]) {
      const fa = creature.getObjectByName(B(s + "ForeArm")), hd = creature.getObjectByName(B(s + "Hand"));
      if (fa) fa.scale.setScalar(1.16); if (hd) hd.scale.setScalar(1.16);
    }
    // respiração irregular + tiques
    if (sp1) sp1.rotation.x += Math.sin(t * 1.9) * 0.02 + Math.sin(t * 7.3) * 0.006;
    // look-at com ATRASO (a cabeça segue o jogador devagar, com tremor)
    if (head) {
      const m = new THREE.Matrix4().lookAt(camera.position, head.getWorldPosition(new THREE.Vector3()), creature.up);
      lookQ.setFromRotationMatrix(m);
      headLag.slerp(lookQ, 1 - Math.pow(0.0018, dt));   // atraso forte
      const tw = Math.sin(t * 13.0) * 0.02 * (state.s === "HUNTING" ? 2 : 1);
      head.quaternion.slerp(headLag, 0.35);
      head.rotation.z += tw;
    }
    // olhos + boca
    const d = STATES[state.s];
    for (const m of eyeMats) m.emissiveIntensity = d.eye * (0.75 + 0.25 * Math.sin(t * 2.3));
    eyeLight.intensity = d.eye * 0.35;
    if (state.mouthGroup) {
      state.mouth += ((d.mouth * 0.9) - state.mouth) * Math.min(1, dt * 2.2);
      state.mouthGroup.scale.set(1, 0.25 + state.mouth * 1.2, 0.6 + state.mouth * 0.6);
      if (jaw) jaw.rotation.x = state.mouth * 0.55;
    }
    // movimento FSM
    const toT = target.clone().sub(pos).setY(0);
    const dist = toT.length();
    if (speed > 0 && dist > (state.s === "HUNTING" ? 1.35 : 0.3)) {
      pos.addScaledVector(toT.normalize(), Math.min(speed * dt, dist));
    }
    if (state.s === "STALKING") {   // orbita o jogador a ~7 m, sempre de frente
      const dir = pos.clone().sub(camera.position).setY(0);
      const ang = Math.atan2(dir.x, dir.z) + dt * 0.25;
      const r = 7;
      target.set(camera.position.x + Math.sin(ang) * r, 0, camera.position.z + Math.cos(ang) * r);
      speed = 1.1;
    }
    creature.position.copy(pos);
    // encara o jogador em STALKING/HUNTING; senão encara o movimento
    const face = (state.s === "STALKING" || state.s === "HUNTING" || dist < 0.4 || state.s === "DORMANT")
      ? camera.position : target;
    fwdV.copy(face).sub(creature.position).setY(0);
    if (fwdV.lengthSq() > 1e-4) {
      const yaw = Math.atan2(fwdV.x, fwdV.z);
      creature.rotation.y += ((yaw - creature.rotation.y + Math.PI * 3) % (Math.PI * 2) - Math.PI) * Math.min(1, dt * 3);
    }
    // luz segue a criatura; flicker PSX
    spot.position.set(pos.x, 4.2, pos.z + 0.6);
    spot.target.position.copy(pos);
    spot.intensity = 55 + Math.sin(t * 31) * 6 + Math.random() * 8;
    eyeLight.position.copy(pos).add(new THREE.Vector3(0, 1.55, 0));
    // AUTO: transições
    if (state.auto) {
      state.next -= dt;
      const camMoved = camera.position.distanceTo(state.lastCam || camera.position) > 0.4;
      state.lastCam = (state.lastCam || camera.position.clone());
      state.lastCam.lerp(camera.position, 0.1);
      if (state.s !== "DORMANT") state.lastSeen.lerp(camera.position, 0.02);
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
