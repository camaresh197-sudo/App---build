# Scratch results from Wren v6 (2026-11-23) - torso, joints and phone-budget exports
Derived from `blender/wip/hero_v5_bridge_latest.blend`, all built with Blender 5.2 Python. WIP only: never run in Godot or on a phone; the eye and forehead work is NOT in these files (that is `blender/wip/hero_v6_eyes_keel.blend`). Chain, oldest first:
1. `hero_chest_bones.blend` - chest bone made vertical (top x 0.088), both clavicles start at its top. Meshes unchanged (the visible torso is `torso_cartoon`; `chest_3-6` are hidden strays near the world origin, not part of it).
2. (not saved: the same file with the hidden `chest_3-6` removed.) `hero_torso_weights.blend` - upper `torso_cartoon` re-weighted so the chest bone drives it (chest weight above z 1.20 = 1.0, blended with spine 1.05-1.20).
3. `hero_joinfix.blend` - shoulder heads snapped to the clavicle ends (was 27 mm off), neck base moved to the chest top (was 79 mm), each subtree and its weighted vertices shifted with it. Rest-pose joints measure 0 mm.
4. `hero_neckup.blend` - torso vertices around the neck base moved 15 mm forward. This did not close the neck gap: the torso top is an open ring, so a neck collar needs new geometry.
5. `hero_torso_smooth.blend` - torso at about 81,000 faces (4x subdivision, then one Catmull-Clark level). Whole character about 218,000 faces.
6. `hero_phone.blend` - from 5: meshes without shape keys decimated to a 15,000-face budget; whole character 76,091 faces. The four face meshes with shape keys (55,346 faces) are untouched.
7. `hero_face_lean.blend` - from 6 minus the hidden `head_12_OLD` (38,546 faces): 37,545 faces in total.
`character_phone.glb` (9.2 MB, from 6) and `character_lean.glb` (4.5 MB, from 7) were exported with the stock glTF exporter (`export_texcoords=True`), not `tools/blend_to_glb.py`, and never loaded in Godot. Re-export through the project tool before any phone test.
Open here: neck collar, torso anatomy (ribs, pecs, abs), expressions and blinking, GLB through the real pipeline, `hero3d.gd` + `character_rig.json` update.
