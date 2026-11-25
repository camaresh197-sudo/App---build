# Modeling (Blender, rig, hero): read before touching the hero
Nested guide for `blender/`; the root `AGENTS.md` points here. Lessons from Wren v4-v5 (hero rework). When you make a new mistake, add one line here: symptom, cause, rule.

**Setup**
- Godot is not installed by default (see Face and eyes below for running it). Blender runs as pip `bpy` (`python3 -I script.py`); render with Workbench. Scripts that worked are in `tools/hero_rig/` (edit the hard-coded `/home/claude/out` paths). Index: `views_neutral`/`closeup`/`bonevis` renders; `hipsbone`, `rootmove`, `centerlegs`, `straighten2`, `headback` body; `apose_rest`, `rolls2`, `limits4`, `twistbone`, `armposes`, `limrender4` arms; `pen2` penetration test; `bones`, `shoulders`, `bridge` surface detail.
- Work in copies, one saved file per step (`_hips`, `_torso`, ...); keep the last good one. Claim `blender/character_rigged.blend` before editing the real file.
- Zero every expression shape key before judging the face or body (the original has them at 1.0).

**Prove it**
- Render after every change (front, back, left, right, plus a close-up) and send the images; the user wants pictures, not text. Render before you say it is fixed.
- Measure, don't eyeball. "Attached", "centred", "straight", "symmetric" means printed numbers: bone heads and world-space mesh bounds, left vs right. Wren once said the hips were attached when they sat ~1 m too high.
- Test poses, not just rest: elbow flexed, arms raised, arms forward, hand to chest. Rest-only checks missed the elbow melt and the "shoulders are a butt" bend.
- Check penetration with a BVHTree ray-cast parity test, not normals or signed distance. Forearm/upper-arm overlap at the elbow is by design.
- After any move, diff every bone head and mesh bound. A head move once dragged the forearms along.

**Gotchas (each cost a redo)**
- Meshes have non-identity `matrix_world`. Shift vertices with `o.matrix_world.inverted().to_3x3() @ delta`, per object, and check every piece (the `thigh_?_2` stubs were missed once).
- Shape keys: write Basis and keys, or only edit meshes without them. Never subdivide a mesh that has shape keys.
- Moving bones and meshes in separate steps breaks skinning. Move them together, re-skin from the original bone positions.
- Don't change rolls on a posed rig. Bake the pose into rest (`armature_apply`), then set rolls. Detect posed bones by pose matrix vs rest matrix, not by basis alone. `tools/rig_to_armature.py` sets every roll to 0; that was the root cause of mismatched left/right axes.
- Use one roll rule for both sides; the right side negates Y/Z in limits.
- `LIMIT_ROTATION` is LOCAL space; Euler flips beyond about +-120 degrees. Elbow flexion capped at 110 degrees (more melts the forearm into the bicep). Keep shoulder ranges tight. Twist bones use `COPY_ROTATION`, order YZX, Y only.
- Subdivide before sculpting small landmarks; features smaller than the ring spacing move almost no vertices.
- A sphere shoulder reads as a ball: deltoid is about 1.2x arm radius, tapers into the arm, and its lower part is weighted to the upper-arm bone.

**Face and eyes (Wren v6, 2026-11-23)**
- Judge faces in Cycles, not Workbench: Workbench shows grey and hides skin and iris texture. pip `bpy` aborts on any render here; use the standalone Blender 5.2 from download.blender.org (`apt install libegl1 libgl1`). Godot 4.6.3 also runs here (GitHub release, `--import`, then `xvfb-run -a godot --path godot/hula --rendering-driver opengl3 -- <out> 0 sheet neutral 0`) and renders the real game face. The user must allow the download and the run once.
- Ask which build the user is looking at (phone game, `godot` master, or the WIP) before editing. The shipped game already had working eyes while I edited the unshipped WIP for hours.
- Imported meshes carry custom normals. Scale, flip or rebuild a part and it shades pitch black in Cycles (irises, lids, eyeballs, skin shells). Run `bpy.ops.mesh.customdata_custom_splitnormals_clear()` and check winding (lower lids had ~860 of 895 faces inward).
- An eye part at the same depth as the white is invisible: compare front-y of iris and pupil with the white. Left and right must match: the right eye assembly (with `head_27`) sat 17 mm forward of the left. Measure protrusion past the skin per eye.
- Nose-side skin covers the eyeball beyond ~16 mm of its centre, so the lid opening ends where the skin starts (inner corner ~24 deg, outer 62).
- Don't patch old lid meshes (rim shards, spikes). Rebuild lids as dense sphere sections with the edge snapped to a curve (`tools/hero_rig/eyes/rebuild14.py`).
- Proportions: eyeball is 62 mm (29% of head width, human ~16%); iris 36% of its radius (human 47%).
- The face front was a V keel, 19-24 mm proud up the forehead. Measure a cross-section (rays at several x) before and after. Moving skin leaves brows and hair floating: move them with it.
- Hidden leftovers inflate counts: `head_12_OLD` (38.5k faces), hidden `chest_3-6`. Face meshes with shape keys (55k faces) cannot be decimated.
- Ambiguous words ("straight black line") cost three rebuilds: ask one question first.

**Hero WIP head, hair, brows, eyes (Wren v9, 2026-11-24): read before editing any of these**
- Latest file: `blender/wip/hero_v66_brows_flat.blend` on branch `wren-hero-wip` (WIP only, not exported to the game, `rigref` not run, not on a phone). Scripts, the generated iris texture and the full findings list: `tools/hero_rig/v9/README.md` on that branch. Open it first; do not re-derive.
- Do not put a .blend under `godot/hula/`. Fork a new file per change, claim it, and leave the eye session's `hero_v21..v39` alone.
- Traps that cost hours: the iris texture was never committed (pink iris); the WIP files carry 14 old area lights that overexpose Cycles renders (hide them); Workbench hides textures; the dark "helmet" is `head_118` and `hat_*`, not the hair; a scratch file named `inspect.py` breaks Python; sandbox `rigref` does not reproduce the committed `character_rig.json`.

**Anatomy checklist (the user's rules)**
- Hips are the centre of movement: root > hips > pelvis > spine and legs. Head and neck sit over the hips (no lean). Legs straight, centred under the hips, same size.
- The torso must touch the hips and run up into the shoulders. Check against a white background for gaps.
- Every joint has limits. "No abnormal bone bends unless a massive amount of force is applied. Then they explode into a million pieces of blood and bone shards."
- **Known defect (2026-11-23):** shoulder chain chest > clav > shoulder > uarm is wrong. The chest bone slants sideways, the left clav hangs off its tip, the right clav floats, neither starts at the sternum, no mesh is weighted to a clav, and there is no scapula. The torso/shoulder join is only visual. Fix this before more shoulder work. Fixed in Wren v8 (`42d9c73`).

**Game side**
- A bone, rest-pose or limit change needs `hero3d.gd` updated and `data/character_rig.json` regenerated (`godot --headless --path godot/hula -- /tmp/out 0 rigref`), then `tools/blend_to_glb.py`, import and smoke before any push. Done in Wren v8 (`42d9c73` on `wren-hero-wip`) for the WIP hero: hips, foretw twist bones, limits, eyes, lids and catchlights. Still open: about 90 face joints (mustache, lips, nose, cheeks), and the belt, buttons and collar meshes.
- Neutral must match: a rotating joint swings its bone by (R-I)*t, t = code joint origin minus file bone origin, so `rigref` must capture the file's own rest pose (A-pose arms, file positions) and `tools/hero_rig/v8/tools_t.py` must show 0.0 cm. Bone roll does not matter (rotation axes are world-frame). Wren v8 lost hours on roll first.
- Joints the code drives every frame (eyes, lids, catchlights, lips, mustache) ignore `character_offsets.json`: set the constants (`EYE_X/Y/Z/R`) and put the Blender bones on the same points. Catchlight meshes sit at the code's neutral spot, not the ball centre.
- A mesh with every normal inward is culled in the game (hollow face, neck showing through). Count normals against the part's centre before exporting (`head_12`: 16329 of 16386 were inward).

**Working with the user on models**
- Short instructions, many rounds. They point at a picture ("4th picture is broken"); answer with the fix and new images.
- If numbers can answer a question, answer it. Ask only when a choice changes the look (for example narrow the legs or widen the hips).
- Own a mistake plainly, fix it, move on.

- Agents get click-only access to Command Prompt (no typing). For scripted Blender runs use the Linux sandbox with `pip install --break-system-packages bpy` (Blender 5.3 as a module), or have the user paste the command output (2026-11-23, `0e1502a`).
- Head shape wrong ("egg", "dome", "regressing"): five passes of nudging ring values by eye made it worse. Cause: no measurement. Rule: threshold the reference silhouette, normalise by head height, generate the ring table from it, then compare front and side renders (Wren v12, `tools/hero_rig/v12/`).
- A fine-mesh strip that reaches the eye area breaks the lid outlines and balloons the vertex count (v138: 71k). Keep nose strips clear of the lids; model small forms as Gaussians, not ring terms, which turn into terraces on fine mesh (Wren v12).
