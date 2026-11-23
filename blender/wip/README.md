# Hero WIP (Wren v5), not the master

Copies made from the user's local `hero_wip/character_rigged_newhands2.blend` (Wren v4). The master `blender/character_rigged.blend` is untouched. Never run in Godot or on a phone.

- `hero_v5_bridge_latest.blend`: newest. Hips root, rebuilt torso (chest, ribs, abs), straight centred legs, A-pose arms with limits and forearm twist bones, bone detail (collarbones, scapulae, elbows), deltoid shoulders, upper chest joined to the shoulders.
- `hero_v5_twist_rig_only.blend`: the same rig before the bone-detail and shoulder surface edits.

Known defect: the chest > clav > shoulder bone chain is wrong (see `AGENTS.md`, Modeling). Scripts: `tools/hero_rig/`.
Before shipping: fix the chain, update `hero3d.gd`, regenerate `data/character_rig.json`, export the GLB, run import and smoke.

## Eyes and eyelids (Wren v5, session of 2026-11-23)
- `hero_v5_eyes_lids.blend`: `hero_v5_bridge_latest.blend` with the face's eyes repaired. It does not include the torso, neck or shoulder-joint scratch edits from the same session. Previews: `preview/eyes_lids_face.png`, `preview/eyes_lids_right_eye.png` (Cycles, hat hidden).
- Fixed: irises and pupils sat 2-2.6 mm behind the white eyeball (moved 4 mm forward); iris, pupil, eyelid, eyeball and skin-shell meshes (`head_21`, `head_27`) had broken imported custom normals that shaded black (cleared); iris material pointed at a texture that renders white (now solid amber); the right eye assembly sat 17 mm too far forward (moved back); 6 mm sockets carved in `head_12` around each eye (base shape and all expression keys), eyes sunk the same amount.
- Eyelids (`lidu_*_0`, `lidl_*_0`) were rebuilt as dense sphere shells (~3,900 faces each) with an almond-shaped opening (corners at +-62 degrees, upper edge 23, lower 19). Same objects, vertex groups, armature modifier and material, so the game's lid bones still drive them.
- Not done: expressions, blinking and the game's lid code are untested; lids are too heavy for the phone (thin them); corners are pointed; brows, mustache, neck and hair are unchanged. Not exported to `character_skinned.glb`; never run in Godot or on a phone.
- Note: `blender/character_rigged.blend` on `godot` (the shipped master) already has working eyes in the game; this WIP is a different, newer rig.
