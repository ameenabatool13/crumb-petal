// 3D bouquet designer (raw Three.js r160 loaded from a CDN via the import map in flowers.html).
// Performance choices (FE-10 lens):
//  - Three.js is NOT downloaded until the stage scrolls into view (or the user presses the button).
//  - No model file: flowers are procedural and each flower head is ONE merged geometry, so a bouquet is ~20 draw calls.
//  - Render loop pauses when the stage is off-screen or the tab is hidden; pixel ratio is capped.
//  - Reduced-motion / save-data / weak devices get the static illustration + a button instead of auto-loading.
const stage = document.getElementById("stage");
const canvas = document.getElementById("c3d");
const fallback = document.getElementById("fallback");
const msg = document.getElementById("fallbackMsg");
const loadBtn = document.getElementById("load3d");
const hud = document.getElementById("hud");
const fpsEl = document.getElementById("fps");
const form = document.getElementById("controls");

const reduceMotion = matchMedia("(prefers-reduced-motion: reduce)").matches;
const conn = navigator.connection || {};
const lowPower = reduceMotion || conn.saveData || (navigator.hardwareConcurrency || 8) <= 2 || (navigator.deviceMemory || 8) <= 2;
const state = { type: "tulip", color: "#E9A9BA", wrap: "#8FA58A", finish: "satin", stems: 9, rotate: !reduceMotion };
const FINISH = { matte: { roughness: 0.95, metalness: 0 }, satin: { roughness: 0.5, metalness: 0 }, glossy: { roughness: 0.15, metalness: 0.1 } };

let T = null; // THREE namespace once loaded
let booted = false, ready = false, visible = false, dirty = true;
let renderer, scene, camera, controls, petalMat, wrapMat, bouquet, headGeo, stemGeo, wrapMesh;
let disposables = [];

// ---- controls (work before and after the 3D scene is loaded) -------------------------------------
if (reduceMotion) form.elements.rotate.checked = false;
form.addEventListener("input", (e) => {
  const el = e.target;
  if (el.name === "type") state.type = el.value;
  if (el.name === "finish") state.finish = el.value;
  if (el.name === "stems") { state.stems = +el.value; document.getElementById("stemsOut").textContent = el.value; }
  if (el.name === "rotate") state.rotate = el.checked;
  apply();
});
form.querySelectorAll(".swatches").forEach((group) => {
  group.addEventListener("click", (e) => {
    const b = e.target.closest("button");
    if (!b) return;
    group.querySelectorAll("button").forEach((x) => x.setAttribute("aria-pressed", String(x === b)));
    state[group.dataset.name] = b.dataset.v;
    apply();
  });
});

// ---- lazy loading ----------------------------------------------------------------------------------
if (lowPower) {
  msg.textContent = "To keep things light on your device, the 3D preview is optional.";
} else if ("IntersectionObserver" in window) {
  const once = new IntersectionObserver((en) => { if (en.some((x) => x.isIntersecting)) { once.disconnect(); boot(); } }, { rootMargin: "250px" });
  once.observe(stage);
} else {
  msg.textContent = "Press the button to load the 3D preview.";
}
loadBtn.addEventListener("click", boot);
new IntersectionObserver((en) => { visible = en[0].isIntersecting; if (visible) loop(); }, { threshold: 0.05 }).observe(stage);
document.addEventListener("visibilitychange", () => { if (!document.hidden) loop(); });

async function boot() {
  if (booted) return;
  booted = true;
  loadBtn.disabled = true;
  msg.textContent = "Loading 3D preview...";
  const t0 = performance.now();
  try {
    T = await import("three");
    const { OrbitControls } = await import("three/addons/controls/OrbitControls.js");
    const { mergeGeometries } = await import("three/addons/utils/BufferGeometryUtils.js");
    T.mergeGeometries = mergeGeometries;
    renderer = new T.WebGLRenderer({ canvas, antialias: true, alpha: true, powerPreference: "low-power" });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, matchMedia("(pointer: coarse)").matches ? 1.5 : 2));
    scene = new T.Scene();
    camera = new T.PerspectiveCamera(35, 1, 0.1, 20);
    camera.position.set(0, 0.55, 2.7);
    scene.add(new T.HemisphereLight(0xffffff, 0xf3dfe5, 1.15));
    const sun = new T.DirectionalLight(0xffffff, 1.5);
    sun.position.set(2, 3, 2.5);
    scene.add(sun);
    controls = new OrbitControls(camera, canvas);
    controls.target.set(0, 0.2, 0);
    controls.enablePan = false;
    controls.enableDamping = true;
    controls.minDistance = 1.6;
    controls.maxDistance = 4;
    controls.maxPolarAngle = Math.PI * 0.62;
    controls.addEventListener("change", () => (dirty = true));
    petalMat = new T.MeshStandardMaterial({ side: T.DoubleSide });
    wrapMat = new T.MeshStandardMaterial({ side: T.DoubleSide, roughness: 0.9 });
    stemGeo = new T.CylinderGeometry(0.012, 0.012, 1, 6);
    new ResizeObserver(resize).observe(stage);
    canvas.hidden = false;
    stage.classList.add("live");
    hud.hidden = false;
    ready = true;
    resize();
    apply();
    console.info(`[3D] ready in ${Math.round(performance.now() - t0)} ms (includes Three.js download)`);
    loop();
  } catch (err) {
    console.warn("3D preview unavailable:", err);
    booted = false;
    loadBtn.disabled = false;
    msg.textContent = "Sorry, the 3D preview couldn't start on this device or connection. The shop works fine without it!";
  }
}

// ---- geometry --------------------------------------------------------------------------------------
function buildHead(type) {
  const parts = [];
  const m = new T.Matrix4(), q = new T.Quaternion(), e = new T.Euler(), s = new T.Vector3(), p = new T.Vector3();
  const add = (g, x, y, z, rx, ry, rz, sx, sy, sz) => {
    const c = g.clone();
    m.compose(p.set(x, y, z), q.setFromEuler(e.set(rx, ry, rz)), s.set(sx, sy, sz));
    c.applyMatrix4(m);
    parts.push(c);
  };
  if (type === "tulip") {
    const prof = [[0.001, 0], [0.07, 0.02], [0.15, 0.1], [0.19, 0.24], [0.16, 0.38], [0.07, 0.47], [0.001, 0.5]].map(([x, y]) => new T.Vector2(x, y));
    add(new T.LatheGeometry(prof, 16), 0, 0, 0, 0, 0, 0, 1, 1, 1);
  } else {
    // layered petals: each ring is a set of flattened spheres whose thin axis faces outward
    const rings = type === "rose" ? [[3, 0.045, 0.16, 0.1, 0.05], [5, 0.085, 0.13, 0.095, 0.09], [7, 0.125, 0.09, 0.09, 0.12]]
      : [[5, 0.04, 0.17, 0.07, 0.04], [7, 0.075, 0.14, 0.065, 0.07], [9, 0.11, 0.11, 0.06, 0.1], [11, 0.145, 0.08, 0.055, 0.12]];
    const sph = new T.SphereGeometry(1, 10, 8);
    rings.forEach(([n, r, y, w, h], k) => {
      for (let i = 0; i < n; i++) {
        const a = (i / n) * Math.PI * 2 + k * 0.5;
        add(sph, Math.cos(a) * r, y - k * 0.03, Math.sin(a) * r, 0.35, Math.PI / 2 - a, 0, w * 1.1, h * 1.4, 0.03);
      }
    });
    add(sph, 0, 0.16, 0, 0, 0, 0, 0.05, 0.05, 0.05);
  }
  const g = T.mergeGeometries(parts);
  parts.forEach((x) => x.dispose());
  return g;
}

function buildBouquet() {
  if (bouquet) scene.remove(bouquet);
  disposables.forEach((d) => d.dispose());
  disposables = [];
  headGeo = buildHead(state.type);
  disposables.push(headGeo);
  bouquet = new T.Group();
  const up = new T.Vector3(0, 1, 0), stemMat = new T.MeshStandardMaterial({ color: 0x5f7a52, roughness: 0.8 }), base = new T.Vector3(0, -0.5, 0);
  for (let i = 0; i < state.stems; i++) {
    const phi = i * 2.399963, rad = 0.125 * Math.sqrt(i + 0.4);
    const top = new T.Vector3(Math.cos(phi) * rad, 0.55 - rad * rad * 0.9, Math.sin(phi) * rad);
    const dir = top.clone().sub(base), len = dir.length();
    const quat = new T.Quaternion().setFromUnitVectors(up, dir.normalize());
    const stem = new T.Mesh(stemGeo, stemMat);
    stem.position.copy(base).addScaledVector(dir, len / 2);
    stem.quaternion.copy(quat);
    stem.scale.set(1, len, 1);
    const head = new T.Mesh(headGeo, petalMat);
    head.position.copy(top);
    head.quaternion.copy(quat);
    head.scale.setScalar(state.type === "tulip" ? 0.95 : 1.05);
    bouquet.add(stem, head);
  }
  disposables.push(stemMat);
  const coneGeo = new T.ConeGeometry(0.5, 0.9, 28, 1, true), ringGeo = new T.TorusGeometry(0.2, 0.014, 8, 32);
  const ribbonMat = new T.MeshStandardMaterial({ color: 0xc9a24b, roughness: 0.35, metalness: 0.6 });
  disposables.push(coneGeo, ringGeo, ribbonMat);
  wrapMesh = new T.Mesh(coneGeo, wrapMat);
  wrapMesh.rotation.x = Math.PI;
  wrapMesh.position.y = -0.1;
  const ribbon = new T.Mesh(ringGeo, ribbonMat);
  ribbon.rotation.x = Math.PI / 2;
  ribbon.position.y = -0.2;
  bouquet.add(wrapMesh, ribbon);
  scene.add(bouquet);
}

let builtKey = "";
function apply() {
  if (!ready) return; // before the scene exists, the controls just store their values
  const key = state.type + state.stems;
  if (key !== builtKey) { builtKey = key; buildBouquet(); }
  petalMat.color.set(state.color);
  Object.assign(petalMat, FINISH[state.finish]);
  wrapMat.color.set(state.wrap);
  controls.autoRotate = state.rotate;
  controls.autoRotateSpeed = 1.2;
  petalMat.needsUpdate = true;
  dirty = true;
  loop();
}

function resize() {
  if (!ready) return;
  const w = stage.clientWidth, h = stage.clientHeight;
  renderer.setSize(w, h, false);
  camera.aspect = w / h;
  camera.updateProjectionMatrix();
  dirty = true;
}

// ---- render loop (only runs while visible) ---------------------------------------------------------
let running = false, frames = 0, last = performance.now();
function loop() {
  if (running || !ready || !visible || document.hidden) return;
  running = true;
  const tick = () => {
    if (!visible || document.hidden) { running = false; return; }
    controls.update();
    if (dirty || state.rotate) { renderer.render(scene, camera); dirty = false; frames++; }
    const now = performance.now();
    if (now - last >= 1000) { fpsEl.textContent = frames ? Math.round((frames * 1000) / (now - last)) + " fps" : "idle"; frames = 0; last = now; }
    requestAnimationFrame(tick);
  };
  requestAnimationFrame(tick);
}
