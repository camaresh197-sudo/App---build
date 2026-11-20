// Renders the ghost boy: sprite sheet PNG (190x260 x 8x3) + rigged GLB (bones, float/expression clips, 22 face blendshapes).
// usage: NODE_PATH=$(npm root -g) node run.mjs <name> [outdir]   (needs `npm i` here for three, and playwright installed globally)
import http from 'http';
import fs from 'fs';
import path from 'path';
import { createRequire } from 'module';
const require = createRequire(import.meta.url);
const { chromium } = require('playwright');
const root = path.dirname(new URL(import.meta.url).pathname);
const types = { '.js': 'text/javascript', '.mjs': 'text/javascript', '.html': 'text/html', '.json': 'application/json' };
const server = http.createServer((q, r) => {
  const f = path.join(root, decodeURIComponent(q.url.split('?')[0]));
  if (!f.startsWith(root) || !fs.existsSync(f) || fs.statSync(f).isDirectory()) { r.writeHead(404); r.end(); return; }
  r.writeHead(200, { 'content-type': types[path.extname(f)] || 'application/octet-stream' }); fs.createReadStream(f).pipe(r);
}).listen(0);
const port = server.address().port;
const b = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
const p = await b.newPage();
p.on('console', (m) => console.log('[page]', m.text()));
p.on('pageerror', (e) => console.log('[pageerror]', e.message));
await p.goto(`http://localhost:${port}/ghost.html`);
const out = await p.evaluate(() => window.run());
const name = process.argv[2] || 'ghost_boy';
const dir = path.resolve(process.argv[3] || path.join(root, 'out'));
fs.mkdirSync(dir, { recursive: true });
fs.writeFileSync(path.join(dir, name + '.png'), Buffer.from(out.sheet.split(',')[1], 'base64'));
fs.writeFileSync(path.join(dir, name + '.glb'), Buffer.from(out.glb, 'base64'));
console.log('done tris', out.tris, 'bones', out.bones);
await b.close(); server.close();
