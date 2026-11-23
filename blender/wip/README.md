# Hero WIP (Wren v5), not the master

Copies made from the user's local `hero_wip/character_rigged_newhands2.blend` (Wren v4). The master `blender/character_rigged.blend` is untouched. Never run in Godot or on a phone.

- `hero_v5_bridge_latest.blend`: newest. Hips root, rebuilt torso (chest, ribs, abs), straight centred legs, A-pose arms with limits and forearm twist bones, bone detail (collarbones, scapulae, elbows), deltoid shoulders, upper chest joined to the shoulders.
- `hero_v5_twist_rig_only.blend`: the same rig before the bone-detail and shoulder surface edits.

Known defect: the chest > clav > shoulder bone chain is wrong (see `AGENTS.md`, Modeling). Scripts: `tools/hero_rig/`.
Before shipping: fix the chain, update `hero3d.gd`, regenerate `data/character_rig.json`, export the GLB, run import and smoke.
