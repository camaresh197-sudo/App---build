# Hero WIP (Wren v5), not the master

Copies made from the user's local `hero_wip/character_rigged_newhands2.blend` (Wren v4). The master `blender/character_rigged.blend` is untouched. Never run in Godot or on a phone.

- `hero_v5_bridge_latest.blend`: newest. Hips root, rebuilt torso (chest, ribs, abs), straight centred legs, A-pose arms with limits and forearm twist bones, bone detail (collarbones, scapulae, elbows), deltoid shoulders, upper chest joined to the shoulders.
- `hero_v5_twist_rig_only.blend`: the same rig before the bone-detail and shoulder surface edits.

Known defect: the chest > clav > shoulder bone chain is wrong (see `AGENTS.md`, Modeling). Scripts: `tools/hero_rig/`.
Before shipping: fix the chain, update `hero3d.gd`, regenerate `data/character_rig.json`, export the GLB, run import and smoke.

## Eyes, eyelids and forehead (Wren v5-v6, 2026-11-23)
- `hero_v6_eyes_keel.blend`: `hero_v5_bridge_latest.blend` with the face's eyes, lids and forehead reworked. It does not include the torso, neck or shoulder-joint scratch edits. Previews: `preview/v6_face.png`, `v6_side.png`, `v6_right_eye.png` (Cycles, hat hidden). Scripts and run order: `tools/hero_rig/eyes/README.md`. Replaces `hero_v5_eyes_lids.blend` (still in history at `1242786`).
- Fixed: iris and pupil sat behind the white (moved forward); broken imported custom normals shaded eye, lid and skin-shell meshes black (cleared); iris texture rendered white (now a radial gradient); the right eye assembly sat 17 mm forward (seated like the left); 6 mm sockets in `head_12`; lids rebuilt with an almond opening, skin-tone material, lash line, waterline; pink tear-duct wedge; irises centred; forehead keel flattened (it stood 19-24 mm proud of the sides).
- Measured: eyeball is a 62 mm sphere (29% of head width; human about 16%), iris 36% of its radius (human 47%, so irises were scaled 1.1x). Nose-side skin covers the eyeball beyond about 16 mm from its centre, so the inner corner is at 24 deg.
- Not done: faint ring where the lid shell meets the skin (`prehead.py`, untested), brows/mustache/neck/hair, crown crest, lids are heavy (thin for the phone), expressions and blinking untested, no GLB export, never run in Godot.
- The shipped master `blender/character_rigged.blend` on `godot` already has working eyes in the game (Godot 4.6.3 renders them under xvfb); this WIP is a different, newer rig.
