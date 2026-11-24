# Wren v9 scripts (2026-11-24): hero WIP head, hair, brows, iris

**Read this before editing the hero's head, hair, brows or eyes.** Models are WIP only (branch `wren-hero-wip`, `blender/wip/`); the shipped master `blender/character_rigged.blend` is untouched. Nothing here is exported to the game, `rigref` has not been run on it, and it has not been on a phone.

## Latest file
`blender/wip/hero_v66_brows_flat.blend`. Lineage: `hero_v19_catch` -> eye session `hero_v21..v39` (claimed by another session) -> `hero_v40_face_joints` (87 face bones moved onto `character_rig.json` points) -> `hero_v58_blend` (hair) -> `hero_v59_iris_fix` -> `hero_v60_brows` -> `hero_v66_brows_flat` (smooth brows). Versions in between are failed or superseded passes; the HANDOFF Claimed table has one row each.
The .blend is NOT under `godot/hula/` on purpose: a .blend inside `res://` can make Godot's import abort. Export a GLB with `tools/blend_to_glb.py` instead.

## What each script does
Run as `blender --background --factory-startup --python <script> -- <args>` (Blender 5.2 standalone) or `python3 -I <script> -- <args>` (pip `bpy`). Edit the hard-coded scratch paths first.
- `face_align.py <in> report|apply <character_rig.json> <out>`: moves non-eye face bones onto the reference points. The reference stores Game Y-up; Blender (x,y,z) = (jx, -jz, jy).
- `hair_cards.py`: rebuilds `hair_l_0`/`hair_r_0` as strand cards (84 body + 40 crown per side, 30 fringe cards, side part, per-strand width). Weighted 100% to `head`. Final tuned version; `hair_cards.py` was patched through several passes, spikes at the top left are NOT fully fixed.
- `del_head118.py`: deletes the dark cap `head_118` (1,488 faces). No code refers to it by name; the master glb does list it.
- `iris_png.py` + `iris_pack.py`: generate and pack the iris texture. `iris_tex_v59.png` is the generated file.
- `brow_smooth.py` + `brow_dark.py`: smooth tapered brows ray-cast onto the skin, dark brown material `BrowHairMat`.
- `render_eyes_cycles.py`, `render_hair_views.py`, `face_joint_distances.py`: checks (see below).

## Findings (read these, they cost hours)
- **Missing iris texture:** `iris_tex_v38.png` was never committed (0x0 image, path into another session's scratch). The iris rendered untextured = pink. Pack textures into the .blend, and write the PNG from numpy: a generated Blender image that is not saved to a file loses its pixels on save.
- **14 old area lights** (7 key 900 W, 7 fill 250 W) sit in the WIP files. They overexpose every Cycles render. Hide them (`hide_render`) and light the scene yourself.
- **Workbench hides textures.** Judge eyes and skin in Cycles. pip `bpy` aborts on render; use standalone Blender 5.2 (`download.blender.org/release/Blender5.2/blender-5.2.0-linux-x64.tar.xz`, plus `apt install libegl1 libgl1`).
- **The "helmet" over the hair was `head_118` and the `hat_*` meshes**, not the hair. Hide `hat*` and `head_118` when judging hair.
- **A scratch file named `inspect.py` shadows Python's stdlib** and breaks numpy/bpy imports. Never name a script after a stdlib module.
- **Master head bone is 63 deg off vertical** (the mesh is upright, skull ~4 deg, neck ~7 deg). The WIP head bone is already vertical. Do not fix the master unless you also fix the rig data.
- **`rigref` here does not reproduce the committed `character_rig.json`:** 32 arm/hand joints differ even on the shipped glb (Godot 4.6.3). Find which Godot version made the committed file before regenerating.
- **Hair is a shell of cards, not a sculpt.** A single wavy shell reads as a cloak; thin cards with taper read as hair. Keep strands off the face with a path check, not only a root check.
- **Brows:** capsules read as caterpillars; triangle strokes read spiky. Smooth tapered crescents on the skin work.

## Open
Hair colour (black), top-left fringe spikes, forehead skin seams, GLB export + `rigref` + smoke + a phone look, phone budget (hair about 3,900 faces, check it), and whether the eyes session wants the generated iris or its own.
