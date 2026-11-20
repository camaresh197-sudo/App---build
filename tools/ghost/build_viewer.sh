#!/bin/bash
# usage: build_viewer.sh <glb> <out.html>
GLB="$(realpath "$1")"; OUT="$(realpath -m "$2")"
cd "$(dirname "$0")"
./node_modules/.bin/esbuild viewer.src.js --bundle --minify --format=iife --outfile=viewer.bundle.js >/dev/null 2>&1
python3 - "$GLB" "$OUT" <<'PY'
import base64, sys
glb = base64.b64encode(open(sys.argv[1],'rb').read()).decode()
js = open('viewer.bundle.js').read().replace('</script>', '<\\/script>')
html = '''<!DOCTYPE html><html><head><meta charset="utf-8"><title>Ghost boy - 3D viewer</title>
<style>html,body{margin:0;height:100%;overflow:hidden;background:#12142a;font:13px system-ui}#ui{position:fixed;left:10px;top:10px;display:flex;flex-wrap:wrap;gap:6px;max-width:92vw}
button{background:#23284d;color:#cfe0ff;border:1px solid #3a4280;border-radius:6px;padding:5px 9px;cursor:pointer}button.on{background:#3f6bd6;color:#fff}
#morph{position:fixed;right:8px;top:8px;bottom:8px;overflow:auto;width:190px;background:#0e1022cc;padding:6px;border-radius:8px;color:#9fb0e8;font-size:11px}#morph label{display:block;margin-bottom:3px}#morph input{width:100%;margin:0 0 4px}#hint{position:fixed;bottom:8px;left:10px;color:#7f8cc0}</style></head><body><div id="ui"></div><div id="morph"><b>Blendshapes</b></div><div id="hint">drag to orbit, scroll to zoom. Buttons play the rig animations in the GLB.</div>
<script id="glb" type="text/plain">''' + glb + '</script><script>' + js + '</script></body></html>'
open(sys.argv[2],'w').write(html)
PY
