# Wren v8 scripts (2026-11-23): hero rig in the real game

Run with the bpy pip module: `python3 -I script.py -- <args>`. Paths inside are the sandbox's (`/home/claude/...`); edit before reuse.
Chain: `hero_v6_eyes_keel.blend` -> clav (`tools_clavfix`) -> legs/feet (`legs`, `legfix`, `legfix2`, `toefix`) -> weights (`weights`) -> UVs (`tools/mesh_uvs.py`) -> root/bake/drop hidden (`root`, `bake`, `drop`, `hidden`) -> `hero_v19_catch.blend`.
Eyes: `eyes` (measure), `eyefix` (bones onto the eyeball centres, head bone centred), `eyefix2` (flip `head_12` normals, catchlights), `eyefix3` (catchlights at the code's neutral from `character_rig.json`).
Check: `tools_t.py <glb> <character_rig.json> N` prints how far each code joint is from its file bone (0.0 cm = consistent). Needs `glbcmp`.
Game side: `rigref` (`shotter.gd`) captures the file's A-pose rest and writes `data/character_rig.json` and `data/character_offsets.json`; run it after every GLB export.
