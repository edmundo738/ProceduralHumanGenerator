// ProceduralHumanGenerator — preview da cabeça (three.js, sem servidor além de ficheiros estáticos).
import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import { GLTFLoader } from "three/addons/loaders/GLTFLoader.js";
import * as SkeletonUtils from "three/addons/utils/SkeletonUtils.js";

const $ = (s) => document.querySelector(s);
const DATA = await (await fetch(`data/data.json?v=${Date.now()}`)).json();

// ------------------------------------------------------------------ tabs
document.querySelectorAll(".tabs button").forEach((b) => b.addEventListener("click", () => {
  document.querySelectorAll(".tabs button").forEach((x) => x.classList.toggle("active", x === b));
  document.querySelectorAll(".tab").forEach((t) => t.classList.toggle("active", t.id === "tab-" + b.dataset.tab));
  if (b.dataset.tab === "viewer") resize();
}));
$("#buildline").textContent = DATA.buildline;

// ------------------------------------------------------------------ 3D
// Referencial glTF (Y para cima): a personagem olha para −Z (frente do Blender = +Y).
const FRAMES = { head: { y: 1.575, size: 0.34 }, bust: { y: 1.40, size: 0.78 }, body: { y: 0.90, size: 1.95 } };
const VIEWS = {
  front: [0, 0, -1], q: [Math.sin(0.7), 0, -Math.cos(0.7)], side: [1, 0, 0], back: [0, 0, 1],
  below: [0, -0.62, -0.78],
};
const state = { view: "front", frame: "head", mesh: "smooth", wire: false, flat: false, spin: false, mode: "compare" };

const camera = new THREE.PerspectiveCamera(30, 1, 0.01, 50);
const loader = new GLTFLoader();
const cache = new Map();

const material = new THREE.MeshStandardMaterial({
  color: 0xb9bcc2, roughness: 0.62, metalness: 0.0,
  polygonOffset: true, polygonOffsetFactor: 1, polygonOffsetUnits: 1,
});
const wireMat = new THREE.LineBasicMaterial({ color: 0x1b2330, transparent: true, opacity: 0.55 });

function makeScene() {
  const scene = new THREE.Scene();
  scene.background = new THREE.Color(0x2b2e36);
  scene.add(new THREE.HemisphereLight(0xf2f4f8, 0x3a3f4a, 1.25));
  const key = new THREE.DirectionalLight(0xffffff, 2.2); key.position.set(-1.2, 2.6, -2.2); scene.add(key);
  const fill = new THREE.DirectionalLight(0xdfe8ff, 0.7); fill.position.set(2.0, 1.2, -0.6); scene.add(fill);
  const rim = new THREE.DirectionalLight(0xffffff, 1.0); rim.position.set(0.5, 2.0, 2.5); scene.add(rim);
  return scene;
}

function makeViewport(side) {
  const el = $("#vp" + side);
  const renderer = new THREE.WebGLRenderer({ antialias: true });
  renderer.setPixelRatio(Math.min(2, window.devicePixelRatio));
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  el.prepend(renderer.domElement);
  const controls = new OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true; controls.dampingFactor = 0.12;
  return { side, el, renderer, controls, scene: makeScene(), group: null, variant: null,
           sel: $("#sel" + side), stats: $("#stats" + side), loading: $("#load" + side) };
}
const vps = [makeViewport("L"), makeViewport("R")];

// sincronizar alvo entre os dois controlos (partilham a câmara)
vps.forEach((v) => v.controls.addEventListener("change", () => {
  vps.forEach((o) => { if (o !== v) o.controls.target.copy(v.controls.target); });
}));

const TOON_RAMP = new THREE.DataTexture(new Uint8Array([70, 150, 255]), 3, 1, THREE.RedFormat);
TOON_RAMP.minFilter = THREE.NearestFilter; TOON_RAMP.magFilter = THREE.NearestFilter;
TOON_RAMP.needsUpdate = true;

async function loadGLB(url, toon) {
  // devolve um GROUP (variantes multi-mesh p/ ex. waifu: corpo+olhos+boca+mãos)
  if (!cache.has(url)) cache.set(url, loader.loadAsync(url).then((g) => {
    const group = new THREE.Group();
    g.scene.updateMatrixWorld(true);
    g.scene.traverse((o) => {
      if (!o.isMesh) return;
      const geo = o.geometry.clone();
      geo.applyMatrix4(o.matrixWorld);
      geo.computeVertexNormals();
      let m = material;
      if (toon) {   // look anime/kawaii: toon + cor do próprio GLB
        const col = (o.material && o.material.color) ? o.material.color.clone()
                                                     : new THREE.Color(0xcccccc);
        m = new THREE.MeshToonMaterial({ color: col, gradientMap: TOON_RAMP });
        m.name = (o.material && o.material.name) || "toon";
      }
      group.add(new THREE.Mesh(geo, m));
    });
    return group;
  }));
  return cache.get(url);
}
async function loadEdges(url) {
  if (!cache.has(url)) cache.set(url, fetch(url).then((r) => r.arrayBuffer()).then((buf) => {
    const g = new THREE.BufferGeometry();
    g.setAttribute("position", new THREE.BufferAttribute(new Float32Array(buf), 3));
    return g;
  }));
  return cache.get(url);
}

const clock = new THREE.Clock();

function loadAnimated(url) {   // preserva cena skinned + clips (p/ ex. waifu3)
  if (!cache.has(url)) cache.set(url, loader.loadAsync(url).then((g) => g));
  return cache.get(url);
}

function findSkinned(root) {
  let out = null;
  root.traverse((o) => { if (o.isSkinnedMesh && !out) out = o; });
  return out;
}

async function playClip(vp, name) {
  const c = vp.clips[name];
  if (!c || !vp.mixer) return;
  const next = vp.mixer.clipAction(c);
  if (vp.action && vp.action !== next) {
    next.reset().play();
    vp.action.crossFadeTo(next, 0.35, true);
  } else if (!vp.action) {
    next.play();
  }
  vp.action = next;
  state.clip = name;
  document.querySelectorAll("#animbar button").forEach((b) =>
    b.classList.toggle("on", b.dataset.clip === name));
}

function showAnimBar(clips) {
  const bar = $("#animbar");
  bar.innerHTML = "";
  bar.style.display = "flex";
  for (const c of clips) {
    const b = document.createElement("button");
    b.dataset.clip = c;
    b.textContent = ({ SambaDance: "💃 Samba", idle: "Idle", walk: "Andar",
                       run: "Correr", agree: "👍 Concordar",
                       headShake: "🙅 Negar", TPose: "T-pose" })[c] || c;
    b.addEventListener("click", () => vps.forEach((v) => v.mixer && playClip(v, c)));
    bar.appendChild(b);
  }
}

async function show(vp, id) {
  vp.variant = DATA.variants.find((v) => v.id === id);
  vp.loading.style.display = "flex";
  let loaded;
  if (vp.variant.animated) {
    // variantes ANIMADAS: cena skinned original + mixer + retarget (Xbot)
    const g = await loadAnimated(`models/${id}_${state.mesh}.glb`);
    loaded = g.scene;
    vp.mixer = new THREE.AnimationMixer(loaded);
    vp.clips = {};
    for (const c of g.animations) vp.clips[c.name] = c;
    try {
      const xb = await loadAnimated("models/anim_xbot.glb");
      const src = findSkinned(xb.scene), dst = findSkinned(loaded);
      if (src && dst) for (const n of ["idle", "walk", "run", "agree", "headShake"]) {
        const c = xb.animations.find((a) => a.name === n);
        if (c) vp.clips[n] = SkeletonUtils.retargetClip(dst, src, c);
      }
    } catch (e) { console.warn("retarget Xbot falhou (uso só clips nativos):", e); }
    const names = Object.keys(vp.clips);
    showAnimBar(names);
    vps.forEach((v) => { if (v !== vp && v.variant && v.variant.id === id) v.clips = vp.clips; });
    playClip(vp, vp.clips.SambaDance ? "SambaDance" : names[0]);
    vp.anim = null;
  } else {
    $("#animbar").style.display = "none";
    vp.mixer = null; vp.action = null;
    loaded = await loadGLB(`models/${id}_${state.mesh}.glb`, !!vp.variant.toon);
  }
  // AUTO-FRAME: corpos completos (~1.7 m) não podem usar a moldura de
  // cabeça (câmara a 0.6 m = DENTRO do corpo → x-ray + "olho de peixe").
  const bb = new THREE.Box3().setFromObject(loaded);
  if (bb.max.y - bb.min.y > 1.2 && state.frame !== "body") {
    setFrame("body");
  }
  const group = new THREE.Group();
  group.add(loaded);
  if (!vp.variant.animated) {
    vp.anim = vp.variant.toon ? loaded : null;
    if (vp.anim) prepAnim(vp.anim);
  }
  if (state.wire && !vp.variant.toon)
    group.add(new THREE.LineSegments(await loadEdges(`models/${id}_edges.bin`), wireMat));
  if (vp.group) vp.scene.remove(vp.group);
  vp.group = group; vp.scene.add(group);
  const m = vp.variant[state.mesh];
  vp.stats.textContent = `${state.mesh === "smooth" ? "suave" : "cage"} · ${m.verts.toLocaleString("pt-PT")} vértices · `
    + `${m.faces.toLocaleString("pt-PT")} faces (${Math.round(100 * m.quads / m.faces)}% quads) · digest ${vp.variant.digest}`;
  vp.loading.style.display = "none";
  updateNote();
}
function refreshAll() { vps.forEach((v) => v.variant && show(v, v.variant.id)); }

function setFrame(name) {   // define moldura E sincroniza os botões da UI
  state.frame = name;
  document.querySelectorAll("#frame button").forEach((b) => b.classList.toggle("on", b.dataset.v === name));
  setCamera();
}

function setCamera() {
  const f = FRAMES[state.frame], d = VIEWS[state.view];
  const dist = (f.size / 2) / Math.tan(THREE.MathUtils.degToRad(camera.fov / 2)) * 1.08;
  const t = new THREE.Vector3(0, f.y, -0.01);
  const dir = new THREE.Vector3(...d).normalize();
  camera.position.copy(t).addScaledVector(dir, dist);
  camera.up.set(0, 1, 0);
  vps.forEach((v) => { v.controls.target.copy(t); v.controls.update(); });
}

function resize() {
  vps.forEach((v) => {
    const r = v.el.getBoundingClientRect();
    if (r.width < 2) return;
    v.renderer.setSize(r.width, r.height, false);
  });
  const r = vps[0].el.getBoundingClientRect();
  camera.aspect = r.width / Math.max(1, r.height); camera.updateProjectionMatrix();
}
window.addEventListener("resize", resize);

function prepAnim(g) {   // olhos = meshes com material "eye" → pestanejar
  g.userData.eyes = [];
  g.traverse((o) => {
    if (o.isMesh && o.material && /eye/i.test(o.material.name)) {
      const bb = new THREE.Box3().setFromObject(o);
      o.userData.cy = (bb.max.y + bb.min.y) / 2;
      g.userData.eyes.push(o);
    }
  });
}

function idleAnim(g, t) {   // respiração + balanço + pestanejar (kawaii idle)
  g.rotation.z = Math.sin(t * 0.9) * 0.02;
  g.position.y = Math.sin(t * 1.7) * 0.006;
  const br = 1 + Math.sin(t * 1.7) * 0.004;
  g.scale.x = br; g.scale.z = br;
  const ph = t % 3.4;
  const k = ph < 0.14 ? Math.sin((ph / 0.14) * Math.PI) : 0;
  for (const e of g.userData.eyes || []) {
    e.scale.y = 1 - 0.85 * k;
    e.position.y = e.userData.cy * 0.85 * k;
  }
}

function loop() {
  requestAnimationFrame(loop);
  const dt = clock.getDelta();
  const tAnim = performance.now() / 1000;
  vps.forEach((v) => { if (v.mixer) v.mixer.update(dt); });
  if (state.spin) {
    const t = vps[0].controls.target, p = camera.position.clone().sub(t);
    p.applyAxisAngle(new THREE.Vector3(0, 1, 0), 0.006); camera.position.copy(t).add(p);
  }
  vps.forEach((v) => { if (v.anim) idleAnim(v.anim, tAnim); });
  vps.forEach((v) => v.controls.update());
  vps.forEach((v) => { if (state.mode === "compare" || v.side === "L") v.renderer.render(v.scene, camera); });
}

// ------------------------------------------------------------------ UI
function seg(id, key, after) {
  document.querySelectorAll(`#${id} button`).forEach((b) => b.addEventListener("click", () => {
    document.querySelectorAll(`#${id} button`).forEach((x) => x.classList.toggle("on", x === b));
    state[key] = b.dataset.v; after();
  }));
}
seg("views", "view", setCamera);
seg("frame", "frame", setCamera);
seg("meshmode", "mesh", refreshAll);
seg("mode", "mode", () => { $("#viewports").classList.toggle("single", state.mode === "single"); resize(); });
$("#wire").addEventListener("change", (e) => { state.wire = e.target.checked; refreshAll(); });
$("#flat").addEventListener("change", (e) => { state.flat = e.target.checked; material.flatShading = state.flat; material.needsUpdate = true; });
$("#spin").addEventListener("change", (e) => { state.spin = e.target.checked; });

for (const vp of vps) {
  for (const v of DATA.variants) vp.sel.add(new Option(v.label, v.id));
  vp.sel.addEventListener("change", () => show(vp, vp.sel.value));
}
function updateNote() {
  const a = vps[0].variant, b = vps[1].variant;
  const one = (v) => `<b>${v.label}</b> — ${v.desc}`;
  $("#note").innerHTML = state.mode === "compare" && b ? `${one(a)}<br>${one(b)}` : one(a);
}

// ------------------------------------------------------------------ métricas
function metricsTable() {
  const M = DATA.metrics, cols = M.columns;
  const head = `<thead><tr><th>critério</th>${cols.map((c) => `<th class="${c.ours ? "ours" : ""}">${c.label}</th>`).join("")}<th>alvo</th></tr></thead>`;
  const rows = M.rows.map((r) => {
    const cells = cols.map((c) => {
      const v = M.values[c.key]?.[r.key];
      if (v === undefined || v === null) return "<td>—</td>";
      const pass = r.lo <= v && v <= r.hi;
      const cls = c.ours ? (r.lo === null ? "" : pass ? "ok" : "bad") : "ref";
      return `<td class="${cls}">${v.toFixed(r.dp)}${c.ours && r.lo !== null ? (pass ? " ✓" : " ✗") : ""}</td>`;
    }).join("");
    return `<tr><td>${r.label}</td>${cells}<td class="tgt">${r.target}</td></tr>`;
  }).join("");
  $("#mtable").innerHTML = head + `<tbody>${rows}</tbody>`;
  const N = DATA.neck;
  $("#ntable").innerHTML = `<thead><tr><th>critério</th><th class="ours">A2b</th><th class="ours">A2b + N1</th><th>alvo</th></tr></thead><tbody>`
    + N.map((r) => `<tr><td>${r.label}</td><td class="${r.okA ? "ok" : "bad"}">${r.a}</td><td class="${r.okB ? "ok" : "bad"}">${r.b}</td><td class="tgt">${r.target}</td></tr>`).join("")
    + "</tbody>";
}

// ------------------------------------------------------------------ renders
function gallery() {
  $("#gallery").innerHTML = DATA.renders.map((r, i) =>
    `<div class="card" data-i="${i}"><img loading="lazy" src="renders/${r.src}" alt="${r.title}"><p><b>${r.title}</b>${r.caption}</p></div>`).join("");
  document.querySelectorAll(".card").forEach((c) => c.addEventListener("click", () => {
    const r = DATA.renders[+c.dataset.i];
    $("#lightbox img").src = "renders/" + r.src; $("#lightbox p").textContent = r.title + " — " + r.caption;
    $("#lightbox").classList.add("show");
  }));
  $("#lightbox").addEventListener("click", () => $("#lightbox").classList.remove("show"));
}

// ------------------------------------------------------------------ histórico
function timeline() {
  $("#timeline").innerHTML = DATA.history.map((h) => `<li class="${h.status}"><h3>${h.title}</h3>
    <div class="meta">${h.commit} · ${h.verdict}</div><p>${h.text}</p>
    ${h.variant ? `<button data-v="${h.variant}">ver no modelo 3D</button>` : ""}</li>`).join("");
  document.querySelectorAll(".timeline button").forEach((b) => b.addEventListener("click", () => {
    document.querySelector('.tabs button[data-tab="viewer"]').click();
    vps[1].sel.value = b.dataset.v; show(vps[1], b.dataset.v);
  }));
}

// ------------------------------------------------------------------ arranque
metricsTable(); gallery(); timeline();
vps[0].sel.value = "antes"; vps[1].sel.value = "n1";
resize(); setCamera(); loop();
await Promise.all([show(vps[0], "antes"), show(vps[1], "n1")]);
