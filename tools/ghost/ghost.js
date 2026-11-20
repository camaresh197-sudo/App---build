import * as THREE from 'three';
import { GLTFExporter } from 'three/addons/exporters/GLTFExporter.js';

const FW = 190, FH = 260, SS = 4, COLS = 8;
const HEAD_C = 0.44, HEAD_R = 0.34, K = HEAD_R / 0.40;
const W = 2048, H = 1024;

// ---------------------------------------------------------------- face sculpt math
const sstep = (a, b, x) => { const t = Math.min(1, Math.max(0, (x - a) / (b - a))); return t * t * (3 - 2 * t); };
const gau = (x, y, cx, cy, sx, sy) => Math.exp(-((x - cx) ** 2 / (2 * sx * sx) + (y - cy) ** 2 / (2 * sy * sy)));
const EYE_X = 0.1232, EYE_Y = HEAD_C - 0.0136, BROW_Y = HEAD_C + 0.100, MY = HEAD_C - 0.188, MW = 0.082;
function disp(x, y) {
  let d = 0;
  d += 0.025 * gau(x, y, 0, HEAD_C - 0.035, 0.02, 0.05);                 // nose bridge
  d += 0.045 * gau(x, y, 0, HEAD_C - 0.080, 0.027, 0.023);               // nose tip
  d += 0.028 * (gau(x, y, -0.027, HEAD_C - 0.090, 0.013, 0.013) + gau(x, y, 0.027, HEAD_C - 0.090, 0.013, 0.013)); // nostril wings
  d -= 0.012 * gau(x, y, 0, HEAD_C - 0.110, 0.030, 0.015);              // shadow under nose
  d += 0.006 * gau(x, y, 0, HEAD_C + 0.085, 0.12, 0.014);                 // brow ridge
  d -= 0.022 * (gau(x, y, -EYE_X, EYE_Y, 0.04, 0.04) + gau(x, y, EYE_X, EYE_Y, 0.04, 0.04)); // eye sockets
  d += 0.021 * (gau(x, y, -0.112, HEAD_C - 0.095, 0.058, 0.052) + gau(x, y, 0.112, HEAD_C - 0.095, 0.058, 0.052)); // soft round cheeks
  d += 0.011 * (gau(x, y, -0.085, HEAD_C - 0.145, 0.040, 0.025) + gau(x, y, 0.085, HEAD_C - 0.145, 0.040, 0.025)); // cheekbone definition
  d -= 0.008 * gau(x, y, 0, HEAD_C - 0.165, 0.11, 0.025);               // jaw shadow
  d += 0.012 * gau(x, y, 0, MY, 0.05, 0.03);                             // mouth area
  d += 0.011 * gau(x, y, 0, HEAD_C - 0.19, 0.040, 0.035);                 // chin
  return d;
}
const z0 = (x, y) => 0.98 * Math.sqrt(Math.max(1e-4, HEAD_R * HEAD_R - (x / 0.96) ** 2 - ((y - HEAD_C) / 1.07) ** 2));
const surfZ = (x, y) => z0(x, y) + disp(x, y);

// ---------------------------------------------------------------- skeleton
const BONES = [
  ['hips', null, 0, -0.20], ['spine', 'hips', 0, -0.02], ['chest', 'spine', 0, 0.10],
  ['neck', 'chest', 0, 0.20], ['head', 'neck', 0, 0.28],
  ['shL', 'chest', -0.19, 0.08], ['elL', 'shL', -0.27, -0.04], ['haL', 'elL', -0.34, -0.15],
  ['shR', 'chest', 0.19, 0.08], ['elR', 'shR', 0.27, -0.04], ['haR', 'elR', 0.34, -0.15],
  ['tail1', 'hips', 0, -0.30], ['tail2', 'tail1', 0, -0.45], ['tail3', 'tail2', 0, -0.60], ['tail4', 'tail3', 0, -0.74],
  ['jaw', 'head', 0, HEAD_C - 0.10, -0.02],
  ['cornerL', 'head', -MW, MY, surfZ(-MW, MY) - 0.004], ['cornerR', 'head', MW, MY, surfZ(MW, MY) - 0.004],
  // fingers: thumb, index, middle, ring (2 joints each)
  ['thL1', 'haL', -0.015, -0.025, 0], ['thL2', 'thL1', -0.012, -0.018, 0],
  ['f1L1', 'haL', -0.005, -0.032, 0], ['f1L2', 'f1L1', -0.004, -0.018, 0],
  ['f2L1', 'haL', 0.005, -0.034, 0], ['f2L2', 'f2L1', 0.004, -0.020, 0],
  ['f3L1', 'haL', 0.015, -0.032, 0], ['f3L2', 'f3L1', 0.012, -0.018, 0],
  ['thR1', 'haR', 0.015, -0.025, 0], ['thR2', 'thR1', 0.012, -0.018, 0],
  ['f1R1', 'haR', 0.005, -0.032, 0], ['f1R2', 'f1R1', 0.004, -0.018, 0],
  ['f2R1', 'haR', -0.005, -0.034, 0], ['f2R2', 'f2R1', -0.004, -0.020, 0],
  ['f3R1', 'haR', -0.015, -0.032, 0], ['f3R2', 'f3R1', -0.012, -0.018, 0],
];
const EYEZ = (sx) => z0(sx * EYE_X, EYE_Y) - 0.060;
for (const sx of [-1, 1]) {
  const S = sx < 0 ? 'L' : 'R';
  for (const n of ['eye', 'lidU', 'lidL']) BONES.push([n + S, 'head', sx * EYE_X, EYE_Y, EYEZ(sx)]);
  BONES.push(['brow' + S, 'head', sx * EYE_X, BROW_Y, surfZ(sx * EYE_X, BROW_Y)]);
}
const B = {}, IDX = {}, boneList = [];
const wpos = {};
for (const [n, par, x, y, z = 0] of BONES) {
  const b = new THREE.Bone(); b.name = n;
  wpos[n] = [x, y, z];
  if (par) { b.position.set(x - wpos[par][0], y - wpos[par][1], z - wpos[par][2]); B[par].add(b); }
  else b.position.set(x, y, z);
  B[n] = b; IDX[n] = boneList.length; boneList.push(b);
}
const REST = {}; for (const b of boneList) REST[b.name] = b.position.clone();

function setSkin(geo, fn) {
  const n = geo.attributes.position.count;
  const si = new Uint16Array(n * 4), sw = new Float32Array(n * 4);
  const p = new THREE.Vector3();
  for (let i = 0; i < n; i++) {
    p.fromBufferAttribute(geo.attributes.position, i);
    const ws = fn(p).filter(w => w[1] > 1e-4).slice(0, 4);
    const tot = ws.reduce((a, w) => a + w[1], 0) || 1;
    for (let k = 0; k < 4; k++) {
      si[i * 4 + k] = ws[k] ? IDX[ws[k][0]] : 0;
      sw[i * 4 + k] = ws[k] ? ws[k][1] / tot : 0;
    }
  }
  geo.setAttribute('skinIndex', new THREE.Uint16BufferAttribute(si, 4));
  geo.setAttribute('skinWeight', new THREE.Float32BufferAttribute(sw, 4));
}
const rigid = (name) => () => [[name, 1]];

const CHAIN = [['chest', 0.10], ['spine', -0.02], ['hips', -0.20], ['tail1', -0.30], ['tail2', -0.45], ['tail3', -0.60], ['tail4', -0.74]];
function torsoWeights(p) {
  const y = p.y;
  if (y >= CHAIN[0][1]) return [['chest', 1]];
  for (let i = 0; i < CHAIN.length - 1; i++) {
    const [a, ya] = CHAIN[i], [b, yb] = CHAIN[i + 1];
    if (y <= ya && y >= yb) { const t = (ya - y) / (ya - yb); return [[a, 1 - t], [b, t]]; }
  }
  return [['tail4', 1]];
}

function addColors(geo, fn) {
  const n = geo.attributes.position.count, c = new Float32Array(n * 4), p = new THREE.Vector3();
  for (let i = 0; i < n; i++) {
    p.fromBufferAttribute(geo.attributes.position, i);
    const [r, g, b, a] = fn(p);
    c.set([r, g, b, a], i * 4);
  }
  geo.setAttribute('color', new THREE.Float32BufferAttribute(c, 4));
}

// baked ambient occlusion: darker near the neck/chin and where sleeves meet the torso
const headC = new THREE.Vector3(0, HEAD_C, 0.05);
function aoBody(p) { const d = p.distanceTo(headC); return 1 - 0.5 * (1 - sstep(0.24, 0.46, d)); }

// ---------------------------------------------------------------- textures
function skinTex(ctx) {}
const faceCanvas = document.createElement('canvas'); faceCanvas.width = W; faceCanvas.height = H;
const faceTex = new THREE.CanvasTexture(faceCanvas); faceTex.colorSpace = THREE.SRGBColorSpace; faceTex.anisotropy = 8;

function P(fx, fy) {
  const r = HEAD_R, th = Math.acos(Math.max(-1, Math.min(1, fy / r))), s = Math.sin(th);
  const ph = Math.asin(Math.max(-1, Math.min(1, fx / (r * s))));
  return { x: W * (0.25 + ph / (2 * Math.PI)), y: H * th / Math.PI, sx: W / (2 * Math.PI) / (r * s), sy: H / (Math.PI * r) };
}
function at(ctx, fx, fy, fn) {
  const p = P(fx * K, fy * K); ctx.save(); ctx.translate(p.x, p.y); ctx.scale(p.sx * K, -p.sy * K); fn(ctx); ctx.restore();
}
const ellPath = (c, x, y, rx, ry) => { c.beginPath(); c.ellipse(x, y, rx, ry, 0, 0, Math.PI * 2); };

function drawFace(ex) {
  const ctx = faceCanvas.getContext('2d');
  const g = ctx.createLinearGradient(0, 0, 0, H);
  g.addColorStop(0, '#d2a283'); g.addColorStop(0.45, '#d9ae92'); g.addColorStop(1, '#cf9f86');
  ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
  for (const sx of [-1, 1]) {
    if (ex.red) at(ctx, sx * 0.145, -0.015, (c) => { const rg = c.createRadialGradient(0, 0, 0.05, 0, 0, 0.10); rg.addColorStop(0, 'rgba(205,70,80,0.55)'); rg.addColorStop(1, 'rgba(205,70,80,0)'); c.fillStyle = rg; ellPath(c, 0, 0, 0.10, 0.10); c.fill(); });
    at(ctx, sx * 0.225, -0.115, (c) => {
      const rg = c.createRadialGradient(0, 0, 0, 0, 0, 0.085);
      rg.addColorStop(0, 'rgba(205,228,255,0.30)'); rg.addColorStop(1, 'rgba(205,228,255,0)');
      c.fillStyle = rg; ellPath(c, 0, 0, 0.085, 0.060); c.fill();
    });
    if (ex.tear) at(ctx, sx * 0.152, -0.115, (c) => { c.fillStyle = 'rgba(200,225,255,0.7)'; c.beginPath(); c.moveTo(0, 0.02); c.bezierCurveTo(0.018, -0.012, 0.014, -0.04, 0, -0.04); c.bezierCurveTo(-0.014, -0.04, -0.018, -0.012, 0, 0.02); c.fill(); c.strokeStyle = 'rgba(200,225,255,0.35)'; c.lineWidth = 0.008; c.beginPath(); c.moveTo(0, 0.03); c.lineTo(0, 0.07); c.stroke(); });
  }
  faceTex.needsUpdate = true;
}

const eyeCanvas = document.createElement('canvas'); eyeCanvas.width = 1024; eyeCanvas.height = 512;
{
  const c = eyeCanvas.getContext('2d');
  const sg = c.createLinearGradient(0, 0, 0, 512); sg.addColorStop(0, '#d9cdca'); sg.addColorStop(0.5, '#f1e9e6'); sg.addColorStop(1, '#e6dad6');
  c.fillStyle = sg; c.fillRect(0, 0, 1024, 512);
  const ig = c.createRadialGradient(256, 256, 8, 256, 256, 90);
  ig.addColorStop(0, '#a26a34'); ig.addColorStop(0.5, '#6b3c18'); ig.addColorStop(0.88, '#341a0a'); ig.addColorStop(1, '#150a04');
  c.fillStyle = ig; c.beginPath(); c.arc(256, 256, 90, 0, 7); c.fill();
  c.strokeStyle = 'rgba(210,150,80,0.40)'; c.lineWidth = 2.5;
  for (let k = 0; k < 32; k++) { const a = k / 32 * 6.283; c.beginPath(); c.moveTo(256 + Math.cos(a) * 24, 256 + Math.sin(a) * 24); c.lineTo(256 + Math.cos(a) * 88, 256 + Math.sin(a) * 88); c.stroke(); }
  c.strokeStyle = 'rgba(220,170,100,0.25)'; c.lineWidth = 1;
  for (let k = 0; k < 16; k++) { const a = k / 16 * 6.283 + 0.098; c.beginPath(); c.moveTo(256 + Math.cos(a) * 30, 256 + Math.sin(a) * 30); c.lineTo(256 + Math.cos(a) * 75, 256 + Math.sin(a) * 75); c.stroke(); }
  const pg = c.createRadialGradient(256, 256, 20, 256, 256, 42);
  pg.addColorStop(0, 'rgba(90,50,20,0.4)'); pg.addColorStop(1, 'rgba(80,40,10,0)');
  c.fillStyle = pg; c.beginPath(); c.arc(256, 256, 42, 0, 7); c.fill();
  c.fillStyle = '#030303'; c.beginPath(); c.arc(256, 256, 32, 0, 7); c.fill();
  c.fillStyle = 'rgba(180,160,140,0.15)'; c.beginPath(); c.arc(256-8, 256-8, 12, 0, 7); c.fill();
}
const eyeTex = new THREE.CanvasTexture(eyeCanvas); eyeTex.colorSpace = THREE.SRGBColorSpace; eyeTex.anisotropy = 8;

// shirt texture (u around, v along the profile, flipY=false so v=0 is the neckline)
function makeShirtTex(vOfY) {
  const c = document.createElement('canvas'); c.width = 1024; c.height = 512; const g = c.getContext('2d');
  const base = g.createLinearGradient(0, 0, 0, 512); base.addColorStop(0, '#e6e0d0'); base.addColorStop(1, '#d6cfbc');
  g.fillStyle = base; g.fillRect(0, 0, 1024, 512);
  g.globalAlpha = 0.05; g.fillStyle = '#7a6f5a';
  for (let y = 0; y < 512; y += 4) g.fillRect(0, y, 1024, 1);
  for (let x = 0; x < 1024; x += 4) g.fillRect(x, 0, 1, 512);
  g.globalAlpha = 1;
  const Y = (y) => vOfY(y) * 512;
  // collar band
  g.fillStyle = '#138a83'; g.fillRect(0, Y(0.20), 1024, Y(0.155) - Y(0.20));
  g.fillStyle = '#f2b632'; for (let x = 0; x < 1024; x += 32) { g.beginPath(); g.arc(x + 16, (Y(0.20) + Y(0.155)) / 2, 5, 0, 7); g.fill(); }
  // hem embroidery
  const hy = Y(-0.17), hh = Y(-0.275) - hy;
  g.fillStyle = '#f26b1d'; g.fillRect(0, hy, 1024, hh * 0.5);
  g.fillStyle = '#17a39b'; g.fillRect(0, hy - 7, 1024, 5); g.fillRect(0, hy + hh * 0.5 + 3, 1024, 5);
  for (let x = 0; x < 1024; x += 64) {
    g.save(); g.translate(x + 32, hy + hh * 0.78);
    g.fillStyle = '#e8386c';
    for (let k = 0; k < 6; k++) { g.rotate(Math.PI / 3); g.beginPath(); g.ellipse(0, -9, 4, 8, 0, 0, 7); g.fill(); }
    g.fillStyle = '#f6c445'; g.beginPath(); g.arc(0, 0, 4.5, 0, 7); g.fill(); g.restore();
  }
  // wear: faded embroidery, dirt, grass stain, patch, tear
  g.fillStyle = 'rgba(214,207,188,0.35)'; g.fillRect(0, hy - 8, 1024, hh + 16);
  let seed = 7; const rnd = () => (seed = (seed * 16807) % 2147483647) / 2147483647;
  for (let i = 0; i < 70; i++) { const x = rnd() * 1024, y = Y(-0.02) + rnd() * (512 - Y(-0.02)); g.fillStyle = `rgba(85,62,40,${0.05 + rnd() * 0.12})`; g.beginPath(); g.ellipse(x, y, 14 + rnd() * 46, 8 + rnd() * 22, rnd() * 3, 0, 7); g.fill(); }
  g.fillStyle = 'rgba(70,110,50,0.28)'; g.beginPath(); g.ellipse(430, Y(-0.12), 38, 22, 0.5, 0, 7); g.fill();
  g.fillStyle = '#7f93b5'; g.fillRect(560, Y(0.0), 70, 64); g.strokeStyle = '#d8d2c2'; g.setLineDash([6, 5]); g.lineWidth = 2; g.strokeRect(564, Y(0.0) + 4, 62, 56); g.setLineDash([]);
  g.fillStyle = '#5b4a3a'; g.beginPath(); g.moveTo(380, Y(0.075)); g.lineTo(412, Y(0.06)); g.lineTo(405, Y(0.035)); g.lineTo(430, Y(0.025)); g.lineTo(398, Y(0.0)); g.lineTo(386, Y(0.03)); g.closePath(); g.fill();
  g.strokeStyle = 'rgba(230,224,208,0.9)'; g.lineWidth = 2; for (let k = 0; k < 4; k++) { g.beginPath(); g.moveTo(376 + k * 12, Y(0.085)); g.lineTo(384 + k * 12, Y(-0.005)); g.stroke(); }
  // zig-zag stitches
  g.strokeStyle = '#17a39b'; g.lineWidth = 3; g.beginPath(); const zy = Y(-0.145);
  for (let x = 0; x <= 1024; x += 16) g.lineTo(x, zy + ((x / 16) % 2 ? 6 : -6)); g.stroke();
  // button placket (front is u=0.5 after the lathe is rotated)
  g.fillStyle = 'rgba(0,0,0,0.12)'; g.fillRect(512 - 14, Y(0.155), 28, Y(-0.17) - Y(0.155));
  g.strokeStyle = '#bdb6a6'; g.lineWidth = 2; g.beginPath(); g.moveTo(512, Y(0.155)); g.lineTo(512, Y(-0.17)); g.stroke();
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; t.flipY = false; t.anisotropy = 8; t.wrapS = THREE.RepeatWrapping;
  return t;
}

// ---------------------------------------------------------------- materials
function ghostly(m, color, str) {
  m.onBeforeCompile = (sh) => {
    sh.fragmentShader = sh.fragmentShader.replace('#include <emissivemap_fragment>',
      `#include <emissivemap_fragment>
       float rimF = pow(1.0 - saturate(dot(normalize(vNormal), normalize(vViewPosition))), 2.4);
       totalEmissiveRadiance += vec3(${color}) * rimF * ${str.toFixed(2)};`);
  };
  return m;
}
const SKIN_EMI = { emissive: '#3a2a1e', emissiveIntensity: 0.25 };
const skinMat = ghostly(new THREE.MeshStandardMaterial({ color: '#d3a68a', roughness: 0.75, metalness: 0, ...SKIN_EMI }), '0.5,0.75,1.0', 0.10);
const headMat = ghostly(new THREE.MeshStandardMaterial({ map: faceTex, roughness: 0.75, metalness: 0, ...SKIN_EMI }), '0.5,0.75,1.0', 0.10);
const earInMat = ghostly(new THREE.MeshStandardMaterial({ color: '#9b6450', roughness: 0.7 }), '0.45,0.70,1.0', 0.28);
const eyeMat = new THREE.MeshStandardMaterial({ map: eyeTex, roughness: 0.08, metalness: 0 });
const lidMat = ghostly(new THREE.MeshStandardMaterial({ color: '#d3a68a', roughness: 0.75, vertexColors: true, ...SKIN_EMI }), '0.5,0.75,1.0', 0.10);
const lipUpMat = new THREE.MeshStandardMaterial({ color: '#8b7a8c', roughness: 0.55 });
const lipLoMat = new THREE.MeshStandardMaterial({ color: '#9b8a9c', roughness: 0.45 });
const mouthInMat = new THREE.MeshStandardMaterial({ color: '#2a0509', roughness: 0.9 });
const tongueMat = new THREE.MeshStandardMaterial({ color: '#c4505c', roughness: 0.5 });
const browMat = new THREE.MeshStandardMaterial({ color: '#1a1210', roughness: 0.8 });
const hairMat = ghostly(new THREE.MeshStandardMaterial({ color: '#2a1f21', roughness: 0.55, metalness: 0, vertexColors: true }), '0.45,0.70,1.0', 0.28);
const hairShellMat = ghostly(new THREE.MeshStandardMaterial({ color: '#1b1416', roughness: 0.65, metalness: 0, vertexColors: true }), '0.45,0.70,1.0', 0.25);
const clothBase = { roughness: 0.82, metalness: 0, vertexColors: true };
const cuffMat = ghostly(new THREE.MeshStandardMaterial({ color: '#f26b1d', roughness: 0.7 }), '0.55,0.80,1.0', 0.40);
const buttonMat = new THREE.MeshStandardMaterial({ color: '#c9a45a', roughness: 0.3, metalness: 0.6 });
const tailMat = ghostly(new THREE.MeshStandardMaterial({
  color: '#b6c8e8', roughness: 0.6, vertexColors: true, transparent: true, depthWrite: true,
  emissive: new THREE.Color('#5d86d6'), emissiveIntensity: 0.4 }), '0.55,0.8,1.0', 1.1);

// ---------------------------------------------------------------- geometry
const meshes = [];
function addSkinned(geo, mat, name, weightFn) {
  setSkin(geo, weightFn);
  const m = new THREE.SkinnedMesh(geo, mat); m.name = name; m.castShadow = true; m.receiveShadow = true; m.frustumCulled = false;
  meshes.push(m); return m;
}

function build() {
  const group = new THREE.Group(); group.name = 'GhostBoy';
  group.add(B.hips);

  // sculpted head: displaced sphere with a mouth opening, jaw/corner skin weights
  const hs = new THREE.SphereGeometry(HEAD_R, 128, 96); hs.scale(0.96, 1.07, 0.98); hs.translate(0, HEAD_C, 0);
  { const hp = hs.attributes.position, v = new THREE.Vector3();
    for (let i = 0; i < hp.count; i++) {
      v.fromBufferAttribute(hp, i);
      const m = sstep(-0.02, 0.12, v.z), n = new THREE.Vector3(v.x / 0.9216, (v.y - HEAD_C) / 1.1449, v.z / 0.9604).normalize();
      const d = disp(v.x, v.y) * m; v.addScaledVector(n, d);
      v.x *= 1 - 0.05 * sstep(HEAD_C - 0.08, HEAD_C - 0.30, v.y);
      hp.setXYZ(i, v.x, v.y, v.z);
    } }
  { const hp = hs.attributes.position, ix = hs.index.array, keep = [];
    for (let i = 0; i < ix.length; i += 3) {
      let cx = 0, cy = 0, cz = 0; for (let k = 0; k < 3; k++) { cx += hp.getX(ix[i + k]); cy += hp.getY(ix[i + k]); cz += hp.getZ(ix[i + k]); }
      cx /= 3; cy /= 3; cz /= 3;
      if (cz > 0.1 && (cx / (MW + 0.012)) ** 2 + ((cy - MY) / 0.020) ** 2 < 1) continue;
      keep.push(ix[i], ix[i + 1], ix[i + 2]);
    }
    hs.setIndex(keep); }
  hs.computeVertexNormals();
  const cL = new THREE.Vector3(-MW, MY, surfZ(-MW, MY)), cR = new THREE.Vector3(MW, MY, surfZ(MW, MY));
  addSkinned(hs, headMat, 'head', (p) => {
    const jw = sstep(MY + 0.03, MY - 0.025, p.y) * sstep(-0.06, 0.08, p.z) * (1 - sstep(0.2, 0.3, Math.abs(p.x)));
    const wl = 0.9 * Math.exp(-p.distanceToSquared(cL) / (2 * 0.032 * 0.032)), wr = 0.9 * Math.exp(-p.distanceToSquared(cR) / (2 * 0.032 * 0.032));
    const j = jw * Math.max(0, 1 - wl - wr);
    return [['cornerL', wl], ['cornerR', wr], ['jaw', j], ['head', Math.max(0, 1 - wl - wr - j)]];
  });
  for (const sx of [-1, 1]) {
    const S = sx < 0 ? 'L' : 'R';
    const place = (g) => {
      g.scale(1.45, 1.85, 1.55); g.rotateY(-0.46);
      if (sx < 0) { g.scale(-1, 1, 1); const ix = g.index.array; for (let i = 0; i < ix.length; i += 3) { const t = ix[i]; ix[i] = ix[i + 1]; ix[i + 1] = t; } }
      g.translate(sx * 0.322, HEAD_C + 0.004, -0.012); g.computeVertexNormals(); return g;
    };
    const arc = (ry, rz, a0, a1, x, n, tubeR) => {
      const p = []; for (let k = 0; k <= n; k++) { const a = a0 + (a1 - a0) * k / n; p.push(new THREE.Vector3(x, ry * Math.sin(a), -rz * Math.cos(a))); }
      return new THREE.TubeGeometry(new THREE.CatmullRomCurve3(p), n * 2, tubeR, 8, false);
    };
    const plate = new THREE.SphereGeometry(1, 28, 20); plate.scale(0.011, 0.050, 0.038); plate.translate(0.012, 0, 0);
    addSkinned(place(plate), skinMat, 'earPlate' + S, rigid('head'));
    addSkinned(place(arc(0.050, 0.038, Math.PI * 1.45, Math.PI * 3.05, 0.021, 18, 0.0085)), skinMat, 'earRim' + S, rigid('head'));
    addSkinned(place(arc(0.024, 0.018, Math.PI * 0.2, Math.PI * 1.5, 0.0245, 12, 0.0060)), skinMat, 'earAnti' + S, rigid('head'));
    const conch = new THREE.SphereGeometry(1, 20, 14); conch.scale(0.005, 0.025, 0.019); conch.translate(0.0225, -0.004, 0.006);
    addSkinned(place(conch), earInMat, 'earConcha' + S, rigid('head'));
    const lobe = new THREE.SphereGeometry(0.0105, 18, 14); lobe.scale(0.75, 1.0, 0.9); lobe.translate(0.017, -0.040, 0.004);
    addSkinned(place(lobe), skinMat, 'earLobe' + S, rigid('head'));
    const tragus = new THREE.SphereGeometry(0.0105, 14, 10); tragus.scale(0.9, 1.2, 1); tragus.translate(0.017, -0.009, 0.037);
    addSkinned(place(tragus), skinMat, 'earTragus' + S, rigid('head'));
  }
  const neck = new THREE.CylinderGeometry(0.068, 0.08, 0.18, 24, 1, true); neck.translate(0, 0.19, 0);
  addSkinned(neck, skinMat, 'neck', (p) => [['neck', 0.6], ['chest', 0.4]]);

  // eyes: eyeball + upper/lower lid shells + 3D brow, each on its own bone
  for (const sx of [-1, 1]) {
    const S = sx < 0 ? 'L' : 'R', ex_ = sx * EYE_X, ez = EYEZ(sx);
    const ball = new THREE.SphereGeometry(0.059, 40, 30); ball.scale(1.15, 1, 1); ball.translate(ex_, EYE_Y, ez);
    addSkinned(ball, eyeMat, 'eyeball' + S, rigid('eye' + S));
    const lidR = 0.0635;
    const up = new THREE.SphereGeometry(lidR, 40, 20, 0, Math.PI * 2, 0, Math.PI / 2);
    addColors(up, (p) => { const c = 0.30 + 0.70 * sstep(0.0, 0.014, Math.abs(p.y)); return [c, c * 0.9, c * 0.88, 1]; });
    up.scale(1.12, 1, 1); up.rotateX(-0.43); up.translate(ex_, EYE_Y, ez);
    addSkinned(up, lidMat, 'lidU' + S, rigid('lidU' + S));
    const lo = new THREE.SphereGeometry(lidR, 40, 20, 0, Math.PI * 2, Math.PI / 2 + 0.40, Math.PI / 2 - 0.40);
    addColors(lo, (p) => { const e = -lidR * Math.sin(0.40); const c = 0.55 + 0.45 * sstep(0.0, 0.012, Math.abs(p.y - e)); return [c, c * 0.92, c * 0.9, 1]; });
    lo.scale(1.12, 1, 1); lo.translate(ex_, EYE_Y, ez);
    addSkinned(lo, lidMat, 'lidL' + S, rigid('lidL' + S));
    // eyebrow: tapered arched tube following the brow ridge
    const pts = [];
    for (let k = -4; k <= 4; k++) { const t = k / 4, x = ex_ + t * 0.066, y = BROW_Y - 0.006 * t * t - 0.003; pts.push(new THREE.Vector3(x, y, surfZ(x, y) + 0.007)); }
    const curve = new THREE.CatmullRomCurve3(pts), tube = new THREE.TubeGeometry(curve, 20, 0.0100, 8, false);
    const tp = tube.attributes.position, ring = 9, c3 = new THREE.Vector3(), v3 = new THREE.Vector3();
    for (let i = 0; i <= 20; i++) { curve.getPointAt(i / 20, c3); const tpr = Math.sin(Math.PI * (0.12 + 0.76 * i / 20)); for (let j = 0; j < ring; j++) { const idx = i * ring + j; v3.fromBufferAttribute(tp, idx).sub(c3); v3.multiplyScalar(0.35 + 0.65 * tpr); v3.z *= 0.65; tp.setXYZ(idx, c3.x + v3.x, c3.y + v3.y, c3.z + v3.z); } }
    tube.computeVertexNormals();
    addSkinned(tube, browMat, 'brow' + S, rigid('brow' + S));
  }

  // mouth: lips follow the corner bones, lower lip + interior follow the jaw
  const lipCurve = (yOff, bow) => { const q = []; for (let k = -6; k <= 6; k++) { const t = k / 6, x = t * MW, y = MY + yOff + bow * (1 - t * t) - 0.0; q.push(new THREE.Vector3(x, y, surfZ(x, y) + 0.004)); } return new THREE.CatmullRomCurve3(q); };
  const lipTube = (curve, r, taper) => {
    const g = new THREE.TubeGeometry(curve, 24, r, 8, false), tp = g.attributes.position, c3 = new THREE.Vector3(), v3 = new THREE.Vector3();
    for (let i = 0; i <= 24; i++) { curve.getPointAt(i / 24, c3); const f = taper + (1 - taper) * Math.sin(Math.PI * i / 24); for (let j = 0; j < 9; j++) { const idx = i * 9 + j; v3.fromBufferAttribute(tp, idx).sub(c3); v3.multiplyScalar(f); v3.z *= 0.75; tp.setXYZ(idx, c3.x + v3.x, c3.y + v3.y, c3.z + v3.z); } }
    g.computeVertexNormals(); return g;
  };
  const cornerW = (p) => sstep(0.022, MW, Math.abs(p.x));
  const upper = lipTube(lipCurve(0.0060, 0.0035), 0.0105, 0.32);
  addSkinned(upper, lipUpMat, 'lipUpper', (p) => { const w = cornerW(p); return [[p.x < 0 ? 'cornerL' : 'cornerR', w], ['head', 1 - w]]; });
  const lower = lipTube(lipCurve(-0.0085, -0.004), 0.0165, 0.30);
  addSkinned(lower, lipLoMat, 'lipLower', (p) => { const w = cornerW(p); return [[p.x < 0 ? 'cornerL' : 'cornerR', w], ['jaw', 1 - w]]; });
  const inner = new THREE.SphereGeometry(0.058, 24, 16); inner.scale(2.0, 0.75, 0.95); inner.translate(0, MY, surfZ(0, MY) - 0.05);
  addSkinned(inner, mouthInMat, 'mouthInside', rigid('head'));
  const tongue = new THREE.SphereGeometry(0.034, 20, 14); tongue.scale(1.75, 0.5, 1.4); tongue.translate(0, MY - 0.015, surfZ(0, MY) - 0.04);
  addSkinned(tongue, tongueMat, 'tongue', rigid('jaw'));

  // hair: shell around the head with the face area cut away (short crop + fringe)
  const hg = new THREE.SphereGeometry(HEAD_R + 0.030, 160, 120); hg.scale(0.96, 1.07, 0.98); hg.translate(0, HEAD_C + 0.02, -0.02);
  { const hp = hg.attributes.position; for (let i = 0; i < hp.count; i++) { const x = hp.getX(i), y = hp.getY(i) - HEAD_C, z = hp.getZ(i); const nz = 0.5 + 0.5 * (0.55 * Math.sin(11 * x + 2) * Math.sin(9 * y + 7 * z) + 0.3 * Math.sin(21 * x + 31 * z) + 0.15 * Math.sin(37 * x + 29 * y + 11 * z)); const f = 0.975 + 0.11 * nz; hp.setXYZ(i, x * f, HEAD_C + y * f, z * f); } }
  const pos = hg.attributes.position, idx = hg.index.array, keep = [];
  for (let i = 0; i < idx.length; i += 3) {
    let cx = 0, cy = 0, cz = 0;
    for (let k = 0; k < 3; k++) { cx += pos.getX(idx[i + k]); cy += pos.getY(idx[i + k]); cz += pos.getZ(idx[i + k]); }
    cx /= 3; cy /= 3; cz /= 3;
    const fringe = HEAD_C + 0.17 - 0.040 * Math.cos(cx * 19) - 0.030 * Math.sin(cx * 47 + 1) - 0.022 * Math.sin(cx * 83 + 3) - 0.12 * sstep(0.20, 0.32, Math.abs(cx));
    const nape = HEAD_C - 0.215 - 0.085 * sstep(0.03, -0.10, cz) + 0.05 * Math.abs(cx) * 2 + 0.05 * Math.sin(cx * 33 + cz * 17) + 0.035 * Math.sin(cx * 71 - cz * 23 + 1);
    const faceZone = (cz > 0.04 + 0.035 * Math.sin(cy * 70 + cx * 30) + 0.075 * sstep(0.27, 0.31, Math.abs(cx)) && cy < fringe) || (cz > -0.045 + 0.03 * Math.sin(cy * 85 + cz * 40) && cy < HEAD_C - 0.065 + 0.018 * Math.sin(cz * 120));
    const sideZone = false;
    const ez = ((cy - (HEAD_C + 0.005)) / 0.118) ** 2 + ((cz + 0.014) / 0.078) ** 2, earZone = Math.abs(cx) > 0.27 && ez < 0.75 + 0.06 * Math.sin(cy * 90 + cz * 60);
    if (!faceZone && !sideZone && !earZone && cy > nape) for (let k = 0; k < 3; k++) keep.push(idx[i + k]);
  }
  hg.setIndex(keep);
  addColors(hg, (p) => { const c = 0.5 + 0.5 * Math.abs(Math.sin(70 * p.x + 22 * p.z) * Math.sin(55 * p.y + 18 * p.x)) + 0.12 * Math.sin(150 * p.x * p.y); return [c, c * 0.96, c * 0.95, 1]; });
  addSkinned(hg, hairShellMat, 'hair', rigid('head'));
  { // natural hair growth: strands start all over the scalp and flow away from a crown whorl, bending down toward the hairline
    let sd = 41; const rnd = () => (sd = (sd * 16807) % 2147483647) / 2147483647;
    const hc = new THREE.Vector3(0, HEAD_C + 0.02, -0.02), R0 = HEAD_R + 0.03;
    const V = (x, y, z) => new THREE.Vector3(x, y, z);
    const world = (u, lift) => V(hc.x + (R0 + lift) * 0.96 * u.x, hc.y + (R0 + lift) * 1.07 * u.y, hc.z + (R0 + lift) * 0.98 * u.z);
    const whorl = V(0, 0.95, -0.31).normalize();
    const fringeAt = (cx) => HEAD_C + 0.17 - 0.040 * Math.cos(cx * 19) - 0.030 * Math.sin(cx * 47 + 1) - 0.022 * Math.sin(cx * 83 + 3) - 0.12 * sstep(0.20, 0.32, Math.abs(cx));
    const allowed = (P) => {
      const cx = P.x, cy = P.y, cz = P.z;
      const nape = HEAD_C - 0.215 - 0.085 * sstep(0.03, -0.10, cz) + 0.05 * Math.abs(cx) * 2 + 0.05 * Math.sin(cx * 33 + cz * 17) + 0.035 * Math.sin(cx * 71 - cz * 23 + 1);
      if (cy < nape) return false;
      if (cz > 0.04 + 0.035 * Math.sin(cy * 70 + cx * 30) + 0.075 * sstep(0.27, 0.31, Math.abs(cx)) && cy < fringeAt(cx)) return false;
      if (cz > -0.045 + 0.03 * Math.sin(cy * 85 + cz * 40) && cy < HEAD_C - 0.065 + 0.018 * Math.sin(cz * 120)) return false;
      const ez = ((cy - (HEAD_C + 0.005)) / 0.115) ** 2 + ((cz + 0.014) / 0.075) ** 2;
      if (Math.abs(cx) > 0.25 && ez < 0.25) return false;
      return true;
    };
    let n = 0;
    const tube = (pts, rad, tint) => {
      const curve = new THREE.CatmullRomCurve3(pts), TS = 9, g = new THREE.TubeGeometry(curve, TS, rad, 5, false);
      const tp = g.attributes.position, c3 = new THREE.Vector3(), v3 = new THREE.Vector3();
      for (let a = 0; a <= TS; a++) { curve.getPointAt(a / TS, c3); const f = 1 - 0.88 * Math.pow(a / TS, 1.5); for (let b = 0; b < 6; b++) { const idx = a * 6 + b; v3.fromBufferAttribute(tp, idx).sub(c3).multiplyScalar(f); tp.setXYZ(idx, c3.x + v3.x, c3.y + v3.y, c3.z + v3.z); } }
      g.computeVertexNormals();
      const cc = new Float32Array(tp.count * 4); for (let q = 0; q < tp.count; q++) { const t = Math.floor(q / 6) / TS, b = tint * (0.85 + 0.35 * t); cc.set([b, b * 0.97, b * 0.95, 1], q * 4); }
      g.setAttribute('color', new THREE.Float32BufferAttribute(cc, 4));
      addSkinned(g, hairMat, 'lock' + (n++), rigid('head'));
    };
    const flow = (u0, len, jit, flick, rad) => {
      const u = u0.clone(), pts = [], STEP = 0.06, ns = Math.ceil(len / STEP), tint = 0.80 + rnd() * 0.35;
      for (let k = 0; k <= ns; k++) {
        const P = world(u, 0.004 + flick * Math.pow(k / ns, 2)); if (!allowed(P)) break; pts.push(P);
        const th = Math.acos(Math.max(-1, Math.min(1, u.y)));
        const away = u.clone().sub(whorl.clone().multiplyScalar(u.dot(whorl))); if (away.lengthSq() < 1e-4) break; away.normalize();
        const up = V(0, 1, 0).sub(u.clone().multiplyScalar(u.y)); const down = up.lengthSq() > 1e-5 ? up.normalize().negate() : away.clone();
        const gr = 0.12 + 0.72 * sstep(0.35, 1.5, th);
        let t = away.clone().multiplyScalar(1 - gr).add(down.multiplyScalar(gr)).normalize();
        const ang = 0.30 + jit * 0.6, c = Math.cos(ang), s2 = Math.sin(ang); t = t.clone().multiplyScalar(c).add(u.clone().cross(t).multiplyScalar(s2));
        u.add(t.multiplyScalar(STEP)).normalize();
      }
      if (pts.length >= 3) {
        for (let i = 1; i < pts.length - 1; i++) { pts[i].lerp(pts[i - 1].clone().add(pts[i + 1]).multiplyScalar(0.5), 0.15); }
        tube(pts, rad * 0.95, tint);
      }
    };
    // guide curves: key hair strands that define the overall direction
    const NG = 48;
    const guides = [];
    for (let i = 0; i < NG; i++) {
      const y = 0.9988 + (-0.5474 - 0.9988) * (i + 0.5) / NG, th = Math.acos(y), ph = i * 2.399963;
      const u = V(Math.sin(th) * Math.cos(ph), y, Math.sin(th) * Math.sin(ph));
      if (u.angleTo(whorl) < 0.07 || !allowed(world(u, 0.004))) continue;
      const stray = i % 8 === 0;
      guides.push({ u, len: 0.30 + (stray ? 0.1 : 0), jit: (stray ? 0.8 : 0.3), flick: stray ? 0.04 : 0.02, rad: 0.030 });
      flow(u, guides[guides.length - 1].len, guides[guides.length - 1].jit, guides[guides.length - 1].flick, guides[guides.length - 1].rad);
    }
    // procedurally generate strands between guides
    for (let i = 0; i < guides.length; i++) {
      const g0 = guides[i], g1 = guides[(i + 1) % guides.length];
      for (let j = 1; j < 16; j++) {
        const t = j / 16, u = g0.u.clone().lerp(g1.u.clone(), t).normalize();
        const len = g0.len + (g1.len - g0.len) * (0.5 + 0.5 * Math.sin(j * Math.PI / 16)), jit = g0.jit + (g1.jit - g0.jit) * t + (rnd() - 0.5) * 0.2;
        const flick = g0.flick + (g1.flick - g0.flick) * t + rnd() * 0.01, rad = g0.rad + (g1.rad - g0.rad) * t + (rnd() - 0.5) * 0.002;
        if (allowed(world(u, 0.004))) flow(u, len, jit, flick, rad);
      }
    }
    // a few bangs that overhang the forehead (still above the brows)
    for (let k = 0; k < 18; k++) {
      const ph = Math.PI / 2 + (k / 17 - 0.5) * 1.9 + (rnd() - 0.5) * 0.06, th0 = 0.5 + rnd() * 0.25, th1 = 1.04 + rnd() * 0.16, pts = [];
      for (let q = 0; q <= 6; q++) { const t = q / 6, th = th0 + (th1 - th0) * t, p = ph + (rnd() - 0.5) * 0.02; pts.push(world(V(Math.sin(th) * Math.cos(p), Math.cos(th), Math.sin(th) * Math.sin(p)), 0.006 + rnd() * 0.01 * t)); }
      tube(pts, 0.024 + rnd() * 0.008, 0.8 + rnd() * 0.5);
    }
  }
  // shirt: lathe profile resampled by arc length, rotated so the front is u=0.5
  const shirtKeys = [[0.095, 0.205], [0.15, 0.185], [0.20, 0.13], [0.215, 0.05], [0.205, -0.05], [0.215, -0.15], [0.26, -0.235], [0.30, -0.28]]
    .map(([r, y]) => new THREE.Vector2(r * 0.98, y));
  const shirtCurve = new THREE.SplineCurve(shirtKeys);
  const shirtPts = shirtCurve.getSpacedPoints(48);
  const vOfY = (y) => { for (let i = 0; i < shirtPts.length - 1; i++) if (shirtPts[i].y >= y && shirtPts[i + 1].y <= y) return (i + (shirtPts[i].y - y) / (shirtPts[i].y - shirtPts[i + 1].y)) / (shirtPts.length - 1); return 1; };
  const shirt = new THREE.LatheGeometry(shirtPts, 72); shirt.rotateY(Math.PI);
  addColors(shirt, (p) => { const a = aoBody(p); return [a, a, a, 1]; });
  const shirtMat = ghostly(new THREE.MeshStandardMaterial({ ...clothBase, map: makeShirtTex(vOfY) }), '0.5,0.75,1.0', 0.12);
  addSkinned(shirt, shirtMat, 'shirt', torsoWeights);

  // buttons
  const rAt = (y) => { let best = shirtPts[0]; for (const q of shirtPts) if (Math.abs(q.y - y) < Math.abs(best.y - y)) best = q; return best.x; };
  for (const y of [0.09, 0.01, -0.13]) {
    const b = new THREE.SphereGeometry(0.02, 14, 10); b.scale(1, 1, 0.55); b.translate(0, y, rAt(y) + 0.004);
    addSkinned(b, buttonMat, 'button' + y, torsoWeights);
  }

  // ghost tail: one swept, tapering crescent body (hem width -> flick), streaked texture + thin trailing wisps
  { const tc = document.createElement('canvas'); tc.width = 512; tc.height = 1024; const g2 = tc.getContext('2d');
    g2.fillStyle = '#9db8e4'; g2.fillRect(0, 0, 512, 1024);
    let sd = 77; const rnd = () => (sd = (sd * 16807) % 2147483647) / 2147483647;
    for (let i = 0; i < 90; i++) {
      const u0 = rnd() * 512, ph = rnd() * 6.28, amp = 6 + rnd() * 22, fr = 3 + rnd() * 5, w = 1 + rnd() * 5, bright = rnd() < 0.7;
      g2.strokeStyle = bright ? `rgba(245,250,255,${0.25 + rnd() * 0.35})` : `rgba(90,130,200,${0.18 + rnd() * 0.25})`; g2.lineWidth = w; g2.beginPath();
      for (let y = 0; y <= 1024; y += 16) { const x = u0 + amp * Math.sin(y / 1024 * fr * 6.28 + ph) + 0.12 * y * Math.sin(ph); y ? g2.lineTo(x, y) : g2.moveTo(x, y); }
      g2.stroke();
      g2.save(); g2.translate(512, 0); g2.beginPath(); g2.restore();
    }
    const tailTex = new THREE.CanvasTexture(tc); tailTex.colorSpace = THREE.SRGBColorSpace; tailTex.wrapS = THREE.RepeatWrapping; tailTex.anisotropy = 8;
    tailMat.map = tailTex; tailMat.needsUpdate = true;

    const Y0 = -0.27, Y1 = -0.99, SWEEP = -0.46, R0 = 0.28;
    const spine = (t) => new THREE.Vector3(SWEEP * Math.pow(t, 2.1) + 0.02 * Math.sin(t * 7) * t, Y0 + (Y1 - Y0) * t + 0.07 * Math.pow(Math.max(0, t - 0.86) / 0.14, 2), 0);
    const radius = (t) => R0 * Math.pow(1 - t, 0.85) * (1 + 0.05 * Math.sin(t * 9));
    const NR = 120, NA = 128, pos = [], uv = [], col = [], ind = [];
    for (let i = 0; i <= NR; i++) {
      const t = i / NR, C = spine(t), T = spine(Math.min(1, t + 0.002)).sub(spine(Math.max(0, t - 0.002))).normalize();
      const Nn = new THREE.Vector3(-T.y, T.x, 0).normalize();
      const fade = t < 0.12 ? 1 : Math.pow(1 - (t - 0.12) / 0.88, 0.7);
      for (let j = 0; j <= NA; j++) {
        const th = j / NA * Math.PI * 2;
        const ripple = 1 + (0.10 * Math.sin(5 * th + t * 8) + 0.06 * Math.sin(9 * th - t * 13 + 1)) * t;
        const r = radius(t) * ripple, rz = r * 0.82;
        const x = C.x + Nn.x * Math.cos(th) * r, y = C.y + Nn.y * Math.cos(th) * r, z = Math.sin(th) * rz;
        pos.push(x, y, z); uv.push(j / NA, t);
        const streak = 0.80 + 0.20 * Math.sin(th * 7 + Math.sin(t * 6) * 2 + t * 10);
        const rim = 0.55 + 0.45 * Math.abs(Math.sin(th / 2));
        col.push(streak, streak, 1, Math.min(1, fade * (0.55 + 0.45 * rim) * (t < 0.12 ? 1 : 0.9)));
      }
    }
    for (let i = 0; i < NR; i++) for (let j = 0; j < NA; j++) { const a0 = i * (NA + 1) + j, b0 = a0 + NA + 1; ind.push(a0, b0, a0 + 1, b0, b0 + 1, a0 + 1); }
    const tail = new THREE.BufferGeometry();
    tail.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3)); tail.setAttribute('uv', new THREE.Float32BufferAttribute(uv, 2));
    tail.setAttribute('color', new THREE.Float32BufferAttribute(col, 4)); tail.setIndex(ind); tail.computeVertexNormals();
    addSkinned(tail, tailMat, 'tail', torsoWeights);

    // thin trailing wisps that peel off the body and drift along the same sweep
    for (let k = 0; k < 12; k++) {
      const t0 = 0.20 + 0.62 * Math.pow(k / 11, 0.75) + rnd() * 0.04, side = (k % 2 ? 1 : -1) * (0.35 + rnd() * 0.5), len = 0.10 + rnd() * 0.30, pts = [];
      for (let q = 0; q <= 10; q++) {
        const f = q / 10, tt = Math.min(1, t0 + f * len), C = spine(tt), Nn = new THREE.Vector3(1, 0, 0);
        const off = radius(t0) * side * (1 + 0.5 * f) + 0.05 * Math.sin(f * 7 + k) * f;
        pts.push(new THREE.Vector3(C.x + off, C.y - 0.03 * f, 0.07 * Math.sin(f * 5 + k * 2) * f + 0.04 * side));
      }
      const curve = new THREE.CatmullRomCurve3(pts), TS = 20, rad = 0.009 + rnd() * 0.017, wg = new THREE.TubeGeometry(curve, TS, rad, 6, false);
      const wp = wg.attributes.position, cc = new THREE.Vector3(), vv = new THREE.Vector3(), wc = new Float32Array(wp.count * 4);
      for (let a = 0; a <= TS; a++) { curve.getPointAt(a / TS, cc); const f = Math.pow(1 - a / TS, 0.9);
        for (let b = 0; b < 7; b++) { const idx = a * 7 + b; vv.fromBufferAttribute(wp, idx).sub(cc).multiplyScalar(f); wp.setXYZ(idx, cc.x + vv.x, cc.y + vv.y, cc.z + vv.z); wc.set([1, 1, 1, 0.8 * f + 0.04], idx * 4); } }
      wg.setAttribute('color', new THREE.Float32BufferAttribute(wc, 4)); wg.computeVertexNormals();
      addSkinned(wg, tailMat, 'tailWisp' + k, torsoWeights);
    }
  }

  // arms
  for (const sx of [-1, 1]) {
    const S = sx < 0 ? 'L' : 'R', sh = new THREE.Vector3(sx * 0.19, 0.08, 0), wr = new THREE.Vector3(sx * 0.34, -0.15, 0.0);
    const dir = wr.clone().sub(sh), len = dir.length();
    const arm = new THREE.CylinderGeometry(0.072, 0.060, len, 24, 12, false);
    arm.applyQuaternion(new THREE.Quaternion().setFromUnitVectors(new THREE.Vector3(0, 1, 0), dir.clone().normalize().negate()));
    arm.translate(...sh.clone().add(wr).multiplyScalar(0.5).toArray());
    const sArm = (p) => Math.min(1, Math.max(0, p.clone().sub(sh).dot(dir) / (len * len)));
    const armW = (p) => { const s = sArm(p); return s < 0.5 ? [['sh' + S, 1 - s * 2], ['el' + S, s * 2]] : [['el' + S, 1 - (s - 0.5) * 2], ['ha' + S, (s - 0.5) * 2]]; };
    addColors(arm, (p) => { const a = Math.min(1, 0.7 + 0.3 * sstep(0.1, 0.4, Math.abs(p.x))); return [a, a, a, 1]; });
    addSkinned(arm, ghostly(new THREE.MeshStandardMaterial({ ...clothBase, color: '#e6e0d0' }), '0.5,0.75,1.0', 0.12), 'sleeve' + S, armW);
    const shoulder = new THREE.SphereGeometry(0.078, 24, 18); shoulder.translate(...sh.toArray());
    addSkinned(shoulder, ghostly(new THREE.MeshStandardMaterial({ color: '#e6e0d0', roughness: 0.82 }), '0.5,0.75,1.0', 0.12), 'shoulder' + S, rigid('sh' + S));
    const cuff = new THREE.TorusGeometry(0.062, 0.014, 12, 28);
    cuff.applyQuaternion(new THREE.Quaternion().setFromUnitVectors(new THREE.Vector3(0, 0, 1), dir.clone().normalize()));
    cuff.translate(...sh.clone().add(dir.clone().multiplyScalar(0.9)).toArray());
    addSkinned(cuff, cuffMat, 'cuff' + S, rigid('ha' + S));
    const hand = new THREE.SphereGeometry(0.064, 28, 20); hand.scale(1, 1.1, 0.9); hand.translate(sx * 0.352, -0.175, 0.0);
    addSkinned(hand, skinMat, 'hand' + S, rigid('ha' + S));

    // fingers: 4 per hand, 2 segments each
    const fingerNames = ['th', 'f1', 'f2', 'f3'];
    const fingerRads = [0.018, 0.016, 0.018, 0.015];
    for (let f = 0; f < 4; f++) {
      const fn = fingerNames[f] + S, r1 = fingerRads[f], r2 = r1 * 0.65;
      const seg1 = new THREE.CylinderGeometry(r1, r2, 0.025, 12, 2, false);
      seg1.rotateX(Math.PI / 2.5); seg1.translate(sx * (0.34 + (f - 1.5) * 0.008), -0.185, 0);
      addSkinned(seg1, skinMat, fn + '1seg', rigid(fn + '1'));
      const seg2 = new THREE.CylinderGeometry(r2, r2 * 0.5, 0.018, 12, 2, false);
      seg2.rotateX(Math.PI / 2.5); seg2.translate(0, -0.015, 0);
      addSkinned(seg2, skinMat, fn + '2seg', rigid(fn + '2'));
    }
  }

  addMorphs();
  group.updateMatrixWorld(true);
  const skeleton = new THREE.Skeleton(boneList);
  for (const m of meshes) { group.add(m); m.bind(skeleton, new THREE.Matrix4()); }
  return group;
}


// ---------------------------------------------------------------- face blendshapes (morph targets)
// Every face mesh (skin, lips, brows, lids, tongue) gets matching deltas from the same fields, so one named shape moves them together.
function addMorphs() {
  const gx = (p, cx, cy, sx, sy) => gau(p.x, p.y, cx, cy, sx, sy);
  const SK = {};   // skin-following shapes: p -> [dx, dy, dzExtra]
  for (const sg of [-1, 1]) {
    const S = sg < 0 ? 'L' : 'R';
    SK['mouthSmile' + S] = (p) => { const w = gx(p, sg * MW, MY, 0.038, 0.032), c = gx(p, sg * 0.11, HEAD_C - 0.10, 0.05, 0.05); return [sg * (0.010 * w + 0.004 * c), 0.024 * w + 0.012 * c, 0.003 * w]; };
    SK['mouthFrown' + S] = (p) => { const w = gx(p, sg * MW, MY, 0.038, 0.032); return [-sg * 0.004 * w, -0.020 * w, 0]; };
    SK['browDown' + S] = (p) => { const w = gx(p, sg * EYE_X, BROW_Y, 0.058, 0.030); return [-sg * 0.006 * w, -0.016 * w, 0.002 * w]; };
    SK['browOuterUp' + S] = (p) => { const w = gx(p, sg * (EYE_X + 0.045), BROW_Y, 0.04, 0.03); return [0, 0.020 * w, 0]; };
    SK['cheekSquint' + S] = (p) => { const w = gx(p, sg * 0.112, HEAD_C - 0.095, 0.055, 0.05); return [0, 0.012 * w, 0.006 * w]; };
    SK['noseSneer' + S] = (p) => { const w = gx(p, sg * 0.027, HEAD_C - 0.09, 0.022, 0.022); return [sg * 0.004 * w, 0.014 * w, 0]; };
  }
  SK.browInnerUp = (p) => { const w = gx(p, -0.05, BROW_Y, 0.04, 0.03) + gx(p, 0.05, BROW_Y, 0.04, 0.03); return [0, 0.022 * w, 0]; };
  SK.cheekPuff = (p) => { const w = gx(p, 0, HEAD_C - 0.10, 0.10, 0.06); return [Math.sign(p.x) * 0.010 * w, 0, 0.008 * w]; };
  SK.mouthPucker = (p) => { const w = gx(p, 0, MY, 0.07, 0.035); return [-p.x * 0.35 * w, 0, 0.012 * w]; };
  SK.mouthOpen = (p) => { const w = sstep(MY + 0.004, MY - 0.012, p.y) * (1 - sstep(MY - 0.07, MY - 0.13, p.y)) * Math.exp(-((p.x / 0.13) ** 2)); return [0, -0.034 * w, 0]; };
  const rotX = (c, a) => (p) => { const vy = p.y - c.y, vz = p.z - c.z, cs = Math.cos(a), sn = Math.sin(a); return [0, vy * cs - vz * sn - vy, vy * sn + vz * cs - vz]; };
  const eyeFns = (name) => {
    const m = /^lid([UL])([LR])$/.exec(name); if (!m) return {};
    const U = m[1] === 'U', S = m[2], sg = S === 'L' ? -1 : 1, c = new THREE.Vector3(sg * EYE_X, EYE_Y, EYEZ(sg));
    return U ? { ['eyeBlink' + S]: rotX(c, 1.6), ['eyeWide' + S]: rotX(c, -0.4), ['eyeSquint' + S]: rotX(c, 0.8) }
             : { ['eyeBlink' + S]: rotX(c, -0.25), ['eyeWide' + S]: rotX(c, 0.03), ['eyeSquint' + S]: rotX(c, -0.12) };
  };
  const FACE = ['head', 'lipUpper', 'lipLower', 'tongue', 'browL', 'browR', 'lidUL', 'lidUR', 'lidLL', 'lidLR'];
  for (const m of meshes) {
    if (!FACE.includes(m.name)) continue;
    const pos = m.geometry.attributes.position, n = pos.count, p = new THREE.Vector3(), list = [];
    const skin = m.name === 'tongue' ? { mouthOpen: SK.mouthOpen } : SK;
    const targets = [...Object.entries(skin).map(([k, f]) => [k, f, true]), ...Object.entries(eyeFns(m.name)).map(([k, f]) => [k, f, false])];
    for (const [name, f, follow] of targets) {
      const arr = new Float32Array(n * 3); let mx = 0;
      for (let i = 0; i < n; i++) {
        p.fromBufferAttribute(pos, i);
        let [dx, dy, dz] = f(p);
        if (follow) { const msk = sstep(-0.02, 0.10, p.z); dx *= msk; dy *= msk; dz *= msk; if (dx || dy) dz += (surfZ(p.x + dx, p.y + dy) - surfZ(p.x, p.y)) * sstep(0.05, 0.12, p.z); }
        arr[i * 3] = dx; arr[i * 3 + 1] = dy; arr[i * 3 + 2] = dz; mx = Math.max(mx, Math.abs(dx), Math.abs(dy), Math.abs(dz));
      }
      if (mx < 1e-6) continue;
      const a = new THREE.Float32BufferAttribute(arr, 3); a.name = name; list.push(a);
    }
    if (list.length) { m.geometry.morphAttributes.position = list; m.geometry.morphTargetsRelative = true; m.updateMorphTargets(); }
  }
}

// ---------------------------------------------------------------- posing
function resetPose() { for (const b of boneList) { b.rotation.set(0, 0, 0); b.position.copy(REST[b.name]); } }
function pose(group, p) {
  resetPose();
  const ph = p.ph ?? 0, sway = p.sway ?? 0.7;
  group.position.y = p.bob ?? 0;
  for (let i = 1; i <= 4; i++) {
    B['tail' + i].rotation.z = sway * Math.sin(ph - i * 0.8) * (0.09 + 0.04 * i);
    B['tail' + i].rotation.x = sway * 0.7 * Math.cos(ph - i * 0.8) * (0.06 + 0.03 * i);
  }
  const a = p.raise ?? 0, f = p.fwd ?? 0, ins = p.inward ?? 0;
  const sl = p.slump ?? 1;
  B.shL.rotation.set(-f, 0, -a + ins + 0.12 * sl + 0.04 * Math.sin(ph + 1));
  B.shR.rotation.set(-f, 0, a - ins - 0.12 * sl - 0.04 * Math.sin(ph + 1));
  B.elL.rotation.z = (p.bendL ?? 0.10);
  B.elR.rotation.z = -(p.bendR ?? 0.10);
  if (p.wave) { B.shR.rotation.z = typeof p.wave === 'number' ? p.wave : 1.25; B.elR.rotation.z = 0.35 * Math.sin(ph * 3) - 0.1; }
  B.head.rotation.set(0.05 * sl + (p.nod ?? 0), p.turn ?? 0, p.tilt ?? 0);
  B.chest.rotation.z = 0.025 * Math.sin(ph);
  B.spine.rotation.y = p.twist ?? 0;
  B.spine.rotation.x = 0.10 * sl + (p.lean ?? 0); B.chest.rotation.x = 0.05 * sl;
}

const DEF = { smile: -0.15, brow: 0.014, tilt: -0.5, eye: 1.05, look: -0.6, bags: 0.55 };
function applyFace(ex) {
  const eo = ex.eye ?? 1.05, look = ex.look ?? 0, ly = ex.lookY ?? 0.04, sm = ex.smile ?? 0, op = ex.open ?? 0, br = ex.brow ?? 0, tl = ex.tilt ?? 0;
  for (const S of ['L', 'R']) {
    const sg = S === 'L' ? -1 : 1;
    B['eye' + S].rotation.set(ly, look * 0.18, 0);
    B['lidU' + S].rotation.x = -(eo - 1.05) * 1.8;
    B['lidL' + S].rotation.x = -Math.max(0, 1.05 - eo) * 0.28 + Math.max(0, eo - 1.05) * 0.14;
    B['brow' + S].position.copy(REST['brow' + S]); B['brow' + S].position.y += br * K * 1.07;
    B['brow' + S].rotation.z = sg * tl * 0.40;
    B['corner' + S].position.copy(REST['corner' + S]); B['corner' + S].position.y += sm * 0.025; B['corner' + S].position.x += sg * sm * 0.004;
  }
  B.jaw.rotation.x = op * 2.8;
}

const EXPR = [
  { ex: { ...DEF }, p: { turn: 0.1 } },                                                                                   // worried (default)
  { ex: { smile: -1.1, tilt: -1.0, eye: 0.55, look: -1.0, bags: 1.6, red: 1, tear: 1 }, p: { nod: 0.14, slump: 1.8, lean: 0.14, tilt: 0.10 } }, // defeated
  { ex: { open: 0.06, smile: -0.4, eye: 1.35, brow: 0.05, tilt: -1.0, bags: 1.2 }, p: { fwd: 1.2, inward: 1.0, nod: -0.06, bendL: 1.0, bendR: 1.0, slump: 0.3 } }, // scared
  { ex: { smile: -0.5, eye: 0.60, look: -1.2, tilt: -0.6, bags: 1.1 }, p: { fwd: 0.8, inward: 1.0, tilt: 0.20, turn: -0.5, nod: 0.14, bendL: 1.1, bendR: 1.1 } }, // ashamed
  { ex: { open: 0.025, smile: -0.8, eye: 0.20, tilt: 0.6, brow: -0.012, bags: 1.3 }, p: { lean: 0.25, nod: 0.08, tilt: -0.10, fwd: 0.5, inward: 0.8, bendL: 1.2, bendR: 1.2 } }, // wince
  { ex: { smile: 0.65, tilt: -0.9, eye: 1.2, look: 0.4, bags: 0.8 }, p: { nod: -0.05, slump: 0.4, raise: 0.30 } },        // weak hopeful smile
  { ex: { smile: 0.35, eye: 0.70, tilt: -0.4, bags: 1.0, brow: -0.008 }, p: { wave: 1.0, slump: 1.0, tilt: 0.08, raise: 0.1 } },  // weary wave
  { ex: { smile: -0.2, eye: 0.15, bags: 1.5, brow: -0.01 }, p: { nod: 0.12, tilt: 0.18, slump: 1.6, raise: -0.14, lean: -0.05 } }, // exhausted
];

// ---------------------------------------------------------------- render
export async function run() {
  drawFace(DEF);
  const group = build();
  const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, preserveDrawingBuffer: true, premultipliedAlpha: true });
  renderer.setPixelRatio(1); renderer.setSize(FW * SS, FH * SS);
  renderer.shadowMap.enabled = true; renderer.shadowMap.type = THREE.PCFShadowMap;
  renderer.toneMapping = THREE.ACESFilmicToneMapping; renderer.toneMappingExposure = 1.25;
  renderer.setClearColor(0xffffff, 0);
  const scene = new THREE.Scene(); scene.add(group);
  scene.add(new THREE.HemisphereLight(0xe6eeff, 0x8a7a88, 1.3));
  const key = new THREE.DirectionalLight(0xfff0dd, 3.0); key.position.set(-1.6, 2.6, 2.6); key.castShadow = true;
  key.shadow.mapSize.set(4096, 4096); Object.assign(key.shadow.camera, { left: -1.2, right: 1.2, top: 1.4, bottom: -1.2, near: 0.5, far: 8 });
  key.shadow.bias = -0.0004; key.shadow.normalBias = 0.018; key.shadow.radius = 4;
  scene.add(key);
  const fill = new THREE.DirectionalLight(0x9ec5ff, 1.0); fill.position.set(2.2, 0.6, 1.6); scene.add(fill);
  const rim = new THREE.DirectionalLight(0x8fb8ff, 1.3); rim.position.set(0.2, 1.6, -2.6); scene.add(rim);
  const camera = new THREE.PerspectiveCamera(28, FW / FH, 0.1, 20);
  camera.position.set(0, 0.5, 4.0); camera.lookAt(0, 0.0, 0);

  const sheet = document.createElement('canvas'); sheet.width = FW * COLS; sheet.height = FH * 3;
  const sctx = sheet.getContext('2d');
  const tmp = document.createElement('canvas'); tmp.width = FW; tmp.height = FH; const tctx = tmp.getContext('2d');
  const glow = document.createElement('canvas'); glow.width = FW; glow.height = FH; const gctx = glow.getContext('2d');
  const NW = FW * SS, NH = FH * SS;
  const ca = document.createElement('canvas'); ca.width = NW; ca.height = NH; const cac = ca.getContext('2d', { willReadFrequently: true });
  const cb = document.createElement('canvas'); cb.width = NW; cb.height = NH; const cbc = cb.getContext('2d', { willReadFrequently: true });
  const normalMat = new THREE.MeshNormalMaterial(); normalMat.toneMapped = false;
  const lin = (v) => Math.pow((v / 255 + 0.055) / 1.055, 2.4);
  function shot(col, row) {
    renderer.render(scene, camera);
    cac.clearRect(0, 0, NW, NH); cac.drawImage(renderer.domElement, 0, 0);
    const A = cac.getImageData(0, 0, NW, NH);
    scene.overrideMaterial = normalMat; renderer.render(scene, camera); scene.overrideMaterial = null;
    cbc.clearRect(0, 0, NW, NH); cbc.drawImage(renderer.domElement, 0, 0);
    const Bm = cbc.getImageData(0, 0, NW, NH);
    for (let i = 0; i < NW * NH; i++) {
      const a = A.data[i * 4 + 3]; if (!a) continue;
      const nz = Bm.data[i * 4 + 3] ? Math.min(1, Math.max(0, lin(Bm.data[i * 4 + 2]) * 2 - 1)) : 1;
      A.data[i * 4 + 3] = a;
    }
    cac.putImageData(A, 0, 0);
    tctx.clearRect(0, 0, FW, FH); tctx.imageSmoothingQuality = 'high'; tctx.drawImage(ca, 0, 0, FW, FH);
    // outer ghost glow
    gctx.clearRect(0, 0, FW, FH); gctx.shadowColor = 'rgba(140,190,255,1.0)'; gctx.shadowBlur = 20; gctx.drawImage(tmp, 0, 0);
    sctx.drawImage(glow, col * FW, row * FH); sctx.drawImage(tmp, col * FW, row * FH);
  }
  for (let i = 0; i < COLS; i++) {
    const ph = i * 2 * Math.PI / COLS;
    group.rotation.y = ph; pose(group, { ph, sway: 0.5 }); drawFace(DEF); applyFace(DEF); shot(i, 0);
    group.rotation.y = 0; pose(group, { ph: ph * 1, bob: 0.035 * Math.sin(ph), sway: 1.0 }); applyFace(DEF); shot(i, 1);
    const e = EXPR[i]; drawFace(e.ex); pose(group, { ph, bob: 0.02 * Math.sin(ph), sway: 0.8, ...e.p }); applyFace(e.ex); shot(i, 2);
  }
  // apply 20% transparency to entire sheet
  { const idata = sctx.getImageData(0, 0, FW * COLS, FH * 3); for (let i = 3; i < idata.data.length; i += 4) idata.data[i] *= 0.80; sctx.putImageData(idata, 0, 0); }
  // export GLB (neutral face, rest pose + float clip)
  drawFace(DEF); resetPose(); group.position.y = 0; group.rotation.y = 0;
  const tracks = [];
  const K = 16, times = [...Array(K + 1).keys()].map(i => i / K * 2);
  const state = {};
  for (const b of boneList) state[b.name] = [];
  for (let k = 0; k <= K; k++) { pose(group, { ph: k / K * 2 * Math.PI, bob: 0, sway: 1.0 }); for (const b of boneList) state[b.name].push(...b.quaternion.toArray()); }
  for (const b of boneList) tracks.push(new THREE.QuaternionKeyframeTrack(b.name + '.quaternion', times, state[b.name]));
  const clip = new THREE.AnimationClip('float', 2, tracks);
  const EN = ['worried', 'defeated', 'scared', 'ashamed', 'wince', 'hopeful_smile', 'weary_wave', 'exhausted'];
  const exprClips = EXPR.map((e, i) => {
    pose(group, { bob: 0, sway: 0.8, ...e.p }); applyFace(e.ex);
    const tr = [];
    for (const b of boneList) {
      tr.push(new THREE.QuaternionKeyframeTrack(b.name + '.quaternion', [0, 0.5], [...b.quaternion.toArray(), ...b.quaternion.toArray()]));
      tr.push(new THREE.VectorKeyframeTrack(b.name + '.position', [0, 0.5], [...b.position.toArray(), ...b.position.toArray()]));
    }
    return new THREE.AnimationClip('expr_' + EN[i], 0.5, tr);
  });
  resetPose();
  const seen = new Set(); for (const m of meshes) { const mt = m.material; if (!seen.has(mt) && mt !== tailMat) { seen.add(mt); const solid = [skinMat, headMat, lidMat, hairMat, hairShellMat, browMat, eyeMat, lipUpMat, lipLoMat, mouthInMat, tongueMat, buttonMat, earInMat].includes(mt); mt.transparent = !solid; mt.opacity = solid ? 1 : 0.8; } }
  const glb = await new GLTFExporter().parseAsync(group, { binary: true, animations: [clip, ...exprClips] });
  const bytes = new Uint8Array(glb); let s = ''; for (let i = 0; i < bytes.length; i += 0x8000) s += String.fromCharCode.apply(null, bytes.subarray(i, i + 0x8000));
  return { sheet: sheet.toDataURL('image/png'), glb: btoa(s), tris: meshes.reduce((a, m) => a + (m.geometry.index ? m.geometry.index.count / 3 : m.geometry.attributes.position.count / 3), 0), bones: boneList.length };
}
window.run = run;
