// index.html (the game) + updater.js -> www/index.html.
// With the "bundle" argument it also writes dist/: a patch zip of www/, latest.json (version, url, sha256),
// index.html, and the large audio packs (kept beside the patch rather than inside it).
import fs from 'fs';
import crypto from 'crypto';
import archiver from 'archiver';

const mode = process.argv[2];
const version = process.env.APP_VERSION || String(Date.now());
const updateUrl = process.env.UPDATE_URL || '__UPDATE_URL__';

let html = fs.readFileSync('index.html', 'utf8');
if (!html.includes('</body>')) throw new Error('index.html has no </body>');
const updater = fs.readFileSync('updater.js', 'utf8').replace('__UPDATE_URL__', () => updateUrl);
// function replacers: the inlined script may contain "$" sequences that string replacements would expand
html = html.replace('</body>', () => `<script>\n${updater}\n</script>\n</body>`);

fs.mkdirSync('www', { recursive: true });
fs.writeFileSync('www/index.html', html);

if (mode === 'bundle') {
  fs.mkdirSync('dist', { recursive: true });
  const name = `bundle-${version}.zip`;
  const zipPath = `dist/${name}`;
  const out = fs.createWriteStream(zipPath);
  const zip = archiver('zip', { zlib: { level: 9 } });

  out.on('close', () => {
    const checksum = crypto.createHash('sha256').update(fs.readFileSync(zipPath)).digest('hex');
    fs.writeFileSync('dist/latest.json', JSON.stringify({ version, url: name, checksum }));
    fs.writeFileSync('dist/index.html', html);
    for (const f of fs.readdirSync('.')) {
      if (/^audio_.*\.v\d+\.ogg$/.test(f)) fs.copyFileSync(f, `dist/${f}`);
    }
    console.log('bundle', name, fs.statSync(zipPath).size);
  });
  // fail the CI step loudly instead of publishing a half-written patch
  const fail = (err) => { console.error(err); process.exit(1); };
  out.on('error', fail);
  zip.on('error', fail);

  zip.pipe(out);
  zip.directory('www/', false);
  zip.finalize();
}
