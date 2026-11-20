import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
const b64 = document.getElementById('glb').textContent.trim();
const bin = Uint8Array.from(atob(b64), c => c.charCodeAt(0)).buffer;
const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false, preserveDrawingBuffer: true });
renderer.setPixelRatio(Math.min(2, devicePixelRatio)); renderer.setSize(innerWidth, innerHeight);
renderer.shadowMap.enabled = true; renderer.shadowMap.type = THREE.PCFShadowMap;
renderer.toneMapping = THREE.ACESFilmicToneMapping; renderer.toneMappingExposure = 1.1;
document.body.appendChild(renderer.domElement);
const scene = new THREE.Scene(); scene.background = new THREE.Color('#12142a');
scene.add(new THREE.HemisphereLight(0xe6eeff, 0x8a7a88, 1.2));
const key = new THREE.DirectionalLight(0xfff0dd, 3); key.position.set(-1.6, 2.6, 2.6); key.castShadow = true; key.shadow.mapSize.set(4096, 4096);
Object.assign(key.shadow.camera, { left: -1.4, right: 1.4, top: 1.6, bottom: -1.4, near: 0.5, far: 8 }); key.shadow.normalBias = 0.018; scene.add(key);
const rim = new THREE.DirectionalLight(0x8fb8ff, 2.2); rim.position.set(0.2, 1.6, -2.6); scene.add(rim);
const fill = new THREE.DirectionalLight(0x9ec5ff, 1); fill.position.set(2.2, 0.6, 1.6); scene.add(fill);
const camera = new THREE.PerspectiveCamera(30, innerWidth / innerHeight, 0.05, 30); camera.position.set(0, 0.35, 3.4);
const controls = new OrbitControls(camera, renderer.domElement); controls.target.set(0, 0.0, 0); controls.enableDamping = true; controls.autoRotate = true; controls.autoRotateSpeed = 1.2;
let mixer, actions = {}, cur;
new GLTFLoader().parse(bin, '', (g) => {
  g.scene.traverse(o => { if (o.isMesh) { o.castShadow = true; o.receiveShadow = true; } });
  scene.add(g.scene); mixer = new THREE.AnimationMixer(g.scene);
  const ui = document.getElementById('ui');
  for (const c of g.animations) {
    const a = mixer.clipAction(c); actions[c.name] = a;
    const btn = document.createElement('button'); btn.textContent = c.name.replace('expr_', ''); btn.onclick = () => play(c.name); ui.appendChild(btn);
  }
  window.play = play; play('float'); window.__ready = g.animations.map(c => c.name);
  const morphMeshes = []; g.scene.traverse(o => { if (o.isMesh && o.morphTargetDictionary) morphMeshes.push(o); });
  const names = [...new Set(morphMeshes.flatMap(m => Object.keys(m.morphTargetDictionary)))];
  const panel = document.getElementById('morph');
  const sliders = {};
  const setM = (n, v) => { for (const m of morphMeshes) { const i = m.morphTargetDictionary[n]; if (i !== undefined) m.morphTargetInfluences[i] = v; } if (sliders[n]) sliders[n].value = v; };
  for (const n of names) {
    const row = document.createElement('label'); row.textContent = n; const r = document.createElement('input'); r.type = 'range'; r.min = 0; r.max = 1; r.step = 0.01; r.value = 0;
    r.oninput = () => setM(n, +r.value); row.appendChild(r); panel.appendChild(row); sliders[n] = r;
  }
  window.setMorph = setM; window.morphNames = names;
  window.resetMorphs = () => names.forEach(n => setM(n, 0));
  window.faceCam = () => { controls.autoRotate = false; camera.position.set(0, 0.34, 1.75); controls.target.set(0, 0.32, 0); controls.update(); };
  window.__morphs = names; window.__morphMeshes = morphMeshes.map(m => m.name + ':' + Object.keys(m.morphTargetDictionary).length);
}, (e) => { window.__err = String(e); console.error(e); });
function play(n) {
  const next = actions[n]; if (!next) return;
  next.reset().play();
  if (cur && cur !== next) cur.crossFadeTo(next, 0.35, false);
  cur = next; window.__cur = n;
  document.querySelectorAll('#ui button').forEach(b => b.classList.toggle('on', n === 'float' ? b.textContent === 'float' : n === 'expr_' + b.textContent));
}
const clock = new THREE.Clock();
renderer.setAnimationLoop(() => { const d = clock.getDelta(); mixer && mixer.update(d); controls.update(); renderer.render(scene, camera); });
addEventListener('resize', () => { camera.aspect = innerWidth / innerHeight; camera.updateProjectionMatrix(); renderer.setSize(innerWidth, innerHeight); });
