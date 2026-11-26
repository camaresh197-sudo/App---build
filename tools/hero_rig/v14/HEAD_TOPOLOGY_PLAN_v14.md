# Head topology plan (Wren v14, 2026-11-26): sketch first, then loops

Status: PLAN ONLY. No geometry changed. Build waits for the user's approval of this plan.
Order (user, 2026-11-26): **face topology first** (green loops: cap, brow, eye, mouth, jaw, nose). The expression set and red loops (section 3d) wait until the green topology is approved. The expression set can be redone later.
Sketch: `topology_sketch.png` (front and side) in this folder. It draws the current `head_quad` skin as points, the current `head_low` edges, the eye line, and the planned 82 degree stitch ring.

## 1. Main shape (measured, from `feat_v13_retopo_cranium_v3.blend` and the v12 reference)
- Measured on `cranium_v4_try.blend` (v13 mesh, 2026-11-26): head_low crown z 1,674 mm, chin 1,416 mm, height 258 mm.
- **Eye line corrected:** eye centre z 1,546 mm (eye span 1,534-1,558 mm), at t = 0.504 of the head height. Nostrils 1,509 mm; ears 1,505-1,572 mm.
- The earlier values (crown 1,670, chin 1,396, eye line 1,533) came from the v12 head, not this mesh. Do not mix them.
- Head width about 169 mm; depth about 249 mm (head_low bounds).
- Crown pole centre (0, -0.02, 1.58) (W085).

## 2. Finding that changes the plan
The 82 degree polar ring that W086 proposed as the cranium stitch line sits at z about 1,590-1,600 mm. That is about 45-55 mm above the eye centre (z 1,546), so it runs across the brow, not at temple or ear height. The sketch shows this directly. This is why the seam shows serration and a brow step (W095-W101).

Correction: move the stitch line down so it runs from the temples at about eye-line height, over the top of the skull. The cranium cap is then everything above that line.

## 3. Regions and loop plan
| Region | Loops | Planned polygons (quads unless noted) | Status |
|---|---|---|---|
| Cranium cap | radial rings from the crown pole, stitched at the temple line (eye-line height) | about 1,700 (W090 remesh result) | not built; seam must be re-planned |
| Brow / forehead | horizontal loops across the brow, joined to the cap | to size on the sketch | not built |
| Eyes | concentric rings round each eye | existing eye patches (610 verts each) | done |
| Nose | ring round each nostril, wing as a crescent | existing nostril pieces (314 verts each) | partial (W072) |
| Mouth | concentric rings round the lips, corners as a designed ring | existing mouth patch | corners open (W080-W084) |
| Cheek | zygomatic diagonal loops, eye ring to mouth corner | to size | not built (see FACE_TOPOLOGY_PLAN.md) |
| Jaw / temple | loops along the jaw line to the chin | to size | not built |
| Back of skull | sparse loops, low density (hair will cover it) | in the cap budget | not built |

Budget: head_low is 9,527 faces now. Target: about 9,500 for the whole head, with the cap at about 1,700. Spend the rest on the face, not the back.

## 4. Order of work (one region per step, each checked before the next)
1. **Approve this plan** (user). No build before that.
2. **Place the stitch ring** at eye-line height on the skin (ray-cast, 0 mm to skin). Render front, side, back over the head. Approve the position.
3. **Build the cap** from the approved ring as its own object: radial rings to the crown, QuadriFlow remesh with the boundary held (W090). Count folds and open edges.
4. **Zip the cap to the head rim in loop order**, 1:1, with the ring spacing matched (W095, W101, W098). Measure the seam against the skin. Check the four-face-edge rule (W105).
5. **Forehead loops** across the brow, joined to the cap seam.
6. **Mouth corners** as a designed ring (W084).
7. **Wrinkle loops from exaggerated references, not from muscles.** Per the Thunder Cloud guide (sections 3, 3.1): model the visible skin, not each muscle. Exaggerate the nasolabial, brow and cheek creases on the reference first, then place loops along those creases. Do not plan a separate loop per muscle (zygomaticus, levator, depressor): the guide says that over-planning leads to a dead end. This replaces the cheek-first order in `docs/FACE_TOPOLOGY_PLAN.md`; that file needs revising to match.

## 3b. Section 3.2 rules, checked on the current mesh (`cranium_v4_try.blend`, head_low)
Rules: a suitable tri count; quads where possible, a few triangles only to end a loop; poles hidden in less-seen areas.
- Faces: 9,527. Quads 93.9%, triangles 5.2% (498), n-gons 84.
- Poles (vertices with more than 4 edges): 170. About 140 are at z about 1,590 mm, the brow-height seam. That is the most visible place on the head, so the rule is broken there.
- Plan change: the cap seam moves down to eye-line height (section 2) so its poles fall on the temple and hairline, where the rule wants them. The 84 n-gons are to be removed or triangulated during the rebuild.
- Triangles: keep only where they end a loop (the cap tip, the mouth corners if needed); count them each step.

## 3c. Shape rules (Thunder Cloud, polygon shape and edge direction), checked on the current mesh
Rules: faces should be chubby or square, not long, thin or diamond; edges should not run across the curvature, and 45 degrees is the worst case.
- Median face aspect ratio (longest edge / shortest): 1.18. Good.
- Faces with aspect above 2.5: 1,342 (14.1%). Above 4: 832. Worst: 64.
- The slivers sit at the seam and the zip, as the rule predicts. Plan: each step must reduce them, and the step's report counts them before and after.
- Edge-to-curvature angle: not measured yet. Needs the curvature field from the reference, so it is part of the reference check (4a).

## 3d. Green and red loops (Thunder Cloud, main topology lines)
- **Green** = form loops that follow the surface curvature (cap, brow, eye and mouth rings, jaw). These are the structure we are rebuilding now.
- **Red** = expression loops that work only in extreme poses. How many depends on how extreme the expressions get.
- Expression data (`godot/hula/data/data_expr.json` on `godot`): about 200 named expressions (smile, grin, rage, sob, smug, disgust, and so on), each set by 31 controls: `mo`, `mw` (mouth open, wide), `sm` (smile), `pu`/`pf` (pucker), `bo`/`bi` and `boL`/`boR`/`biL`/`biR` (brow outer and inner, per side), `lid`/`lidL`/`lidR` (lids), `sq` (squint), `ew` (eyes wide), `ns` (nose sneer), `nf` (nostril flare), `ch` (cheek), `nb`, `te`, `wet`, `pd`, `gx`/`gy` (gaze), `fix`, `hr`/`hp`/`hy`, `sk`, `tt`/`tg`.
- Red loops needed, by control group:
  - **Brows** (`bo`, `bi`, per side): red loops across the brow above and between the brows.
  - **Eyes** (`lid`, `sq`, `ew`): the existing eye rings need red loops at the lid crease and outer corner.
  - **Nose** (`ns`, `nf`): loops at the nostril wing and the sneer line.
  - **Mouth** (`mo`, `mw`, `sm`, `pu`): the existing mouth rings need red loops at the corners and the smile crease (the step 7 wrinkle loops).
  - **Cheek** (`ch`): loops at the cheek crease under the eye.
- Open decision for the user: must all ~200 expressions work, or a subset? That sets how many red loops to add now.

## 3e. Feature lines follow the grid (reference image "1000034914")
- Bad (left): loops are irregular and the feature line (red) cuts across them at a random angle. That matches the current cranium zip.
- Good (right): the grid flows in one direction, the feature line runs along that flow, and loops meet it evenly.
- Rule for this plan: the cap seam (step 2-4) and each wrinkle loop (step 7) are placed as flow lines first, then the loops are built to meet them evenly. No zipper through an irregular grid.

## 4a. Reference check (before step 1, needs the user's photos)
- Lens-correct the front and side photos, then draw horizontal guide lines across the eyes, nose base, mouth and brows (guide section 02).
- Compare each guide line with the mesh (eye line z 1,546 mm, brow line, nose base, mouth). Front and side must agree (guide section 01).
- Not done yet: the reference photos are on the user's PC, not in the repo.

## 5. Checks after every step
- Open edges = 0; edges with 3+ faces = 0 (except a deliberate, named one).
- Loose geometry = 0 (the current file has 10,107 loose edges; remove them before any step).
- Seam to skin: max deviation measured in mm, not by eye.
- Renders: front, side, back, close-up of the changed region, Cycles for the final check.

## 6. Open decisions for the user
- Approve the corrected stitch line at eye-line height (step 1), or set another height.
- Approve the budget: about 1,700 for the cap, the rest on the face.
- Mouth corners: approve the designed-ring approach (step 6), or leave the corners for later.
