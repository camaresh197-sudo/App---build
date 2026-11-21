# CHARACTER.md — mesh, rig, face, animation

Entry point: `godot/hula/scripts/hero3d.gd` (~26k tokens whole — always read a slice
using `docs/CODEMAP.md`). Master asset: `blender/character_rigged.blend`.

## Pipeline

- `blender/character_rigged.blend` is the **master** for the character's mesh and rig.
  Edit it in Blender; publish with:

  ```powershell
  blender --background --factory-startup --python tools\blend_to_glb.py -- blender\character_rigged.blend godot\hula\art\character_skinned.glb
  ```

- `character_skinned.glb` is what the game loads (`godot/hula/art/`). Never regenerate the
  mesh from code: `shotter.gd`'s GLB export is frozen and would clobber Blender edits.
- `hero3d.gd` builds the runtime skeleton/materials and renders the vaquero into a
  transparent SubViewport that `main.gd` draws as a sprite. The skeleton is a hierarchy of
  `Node3D` joints; `pose()` is procedural (hula/salsa/dance gestures).
- Face expressions are expression shape keys on the merged face mesh, driven by
  `data_expr.json` and `hero3d.gd`'s expression code.

## Tools (Blender's Python, not `py`)

```powershell
blender --background --factory-startup --python tools\face_merge.py   -- <in.blend> <out.blend>
blender --background --factory-startup --python tools\face_sculpt.py  -- <in.blend> <out.blend>
blender --background --factory-startup --python tools\face_shapes.py  -- <in.blend> <out.blend>
blender --background --factory-startup --python tools\face_jaw.py     -- <in.blend> <out.blend>
blender --background --factory-startup --python tools\face_rebuild.py -- <in.blend> <out.blend>
blender --background --factory-startup --python tools\face_lips.py    -- <in.blend> <out.blend>
blender --background --factory-startup --python tools\face_mouth2.py  -- <in.blend> <out.blend>
blender --background --factory-startup --python tools\face_chin.py    -- <in.blend> <out.blend>
blender --background --factory-startup --python tools\verify_rig.py   -- <in.blend> <out.png>
blender --background --factory-startup --python tools\pose_test.py
```

Pipeline order: `face_merge` → `face_sculpt` → `face_shapes` → `face_jaw` → `face_rebuild` → `face_lips` → `face_mouth2`.
`face_jaw.py` widens the jaw; `face_rebuild.py` joins the jaw into the head mesh
(all seven shape keys expand to the joined verts) and blends the lower face onto the jaw
group; `face_lips.py` squashes the old lip tubes in depth; `face_mouth2.py` replaces those
tubes with lip geometry that is part of the head (upper lip on the head bone, lower lip on
the jaw), restores some lip depth, colours it `lip_mouth`, adds lip-corner motion to the
smile/frown/pucker keys and a `lip_up` key for talk. `face_sculpt.py`'s chin step runs
before the rebuild on `jaw_0`, so it never reaches the master; `face_chin.py` is the
one-off post-pass for the merged mesh: it pushes the chin forward/up and carries the same
delta into every shape key. All are **one-off** passes: running one twice compounds the
change; there is no automatic inverse.

The master also has two tooth rows, `teeth_u` (bone-parented to `head`) and `teeth_l`
(bone-parented to `jaw`), each with a `hide` shape key. `hero3d.gd` finds them by name on
load and drives `hide` from the same show/hide logic it used for the procedural control
teeth, which stay hidden whenever the file supplies its own.

`rig_to_armature.py` converts the exported node hierarchy into a real Blender armature.
Check each tool's docstring before rerunning it: the `face_*.py` passes rewrite the
master mesh in place, so keep a backup and confirm which stage you are on.

## The rig reference (`data/character_rig.json`)

`hero3d.gd` drives the glb's armature bones every frame by copying each control joint's
pose onto the matching bone (`_rig_sync()`), using a per-bone conversion matrix (`rig_c`)
built from `data/character_rig.json` — a snapshot of every control joint's **world**
transform at the moment the glb was authored. `RIG_REF` must point at wherever that file
actually lives (`res://data/character_rig.json`); it silently stopped doing so for a
while after `data/` was split out, which left the whole glb rig undriven — the file drew
at its raw bind pose, under the still-visible procedural control mesh, which is what the
texture-grid-looking artifact in this era's renders actually was.

**If you change a control joint's own position/scale formula in `_apply_face()` or
`pose()`** — anything that feeds `fr`/`j` node transforms, not just the face's shape
keys — regenerate the reference, or that joint's glb geometry comes out scaled/skewed
relative to the new formula (this is how the mouth cavity plate ended up stretched across
the cheeks: its code-side scale formula changed, but the baked reference still reflected
the old one). Regenerate with the harness, which settles the control rig with no glb
overlay (`rig_skel = null`) and dumps the current joint transforms:

```
godot --headless --path godot/hula -- /tmp/out 0 rigref
```

Pass an expression name as a 4th harness arg (default `neutral`) to bake the reference at
a different pose. Re-import and re-render a few expressions afterward to confirm the
joint in question tracks correctly again.

## Gotchas

- Keep intermediate `.blend` files in `blender/`, never inside `godot/hula/`: Godot's
  import would try (and fail) to open them when Blender isn't configured.
- The `.glb` and albedo PNGs are binary; don't scan or diff them (`AGENTS.md` token hygiene).
- Visual checks are renders, not unit tests: use `pose_test.py` / `verify_rig.py` and the
  harness `face` mode (`-- face.png 1 face 3.2`) rather than guessing from code.
- `tools/blend_to_glb.py` must pass `export_texcoords=True` explicitly: at least one
  Blender version's glTF exporter drops the head's UVs (`TEXCOORD_0`) without it, which
  mis-maps the face albedo into a visible grid.
