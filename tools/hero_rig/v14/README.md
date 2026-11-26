# Wren v14: v143 head fitted to the references (Blender only)

Not exported to glb, not rigged, not in the game, not on a phone. Headless Blender 5.3 via `pip install bpy`; renders need `apt install libegl1` (see `blender/AGENTS.md`).

## The saved file
`feat_v14_head.blend` (1.1 MB) is the v12 head (`../v12/feat_v143.blend`) after these steps, in this order:
1. `fix_folds.py`: 74 folds at the eye corners smoothed locally (0 left; max move 2.7 mm).
2. `chart_profile.py` + `fit_back_to_chart.py`: back of the skull scaled per height to the Head Topology chart's side silhouette (data in `data/chart_rows.json`). Depth stays about 277 mm (chart depth/height at eye level 0.90).
3. `lower_mouth.py`: mouth groove lowered 9 mm (z 1476 to about 1467), nostrils and chin pinned. 14 mm was too long under the nose.
4. `build_eyes.py` + `recalc_normals.py` + `fill_small_holes.py` + `fix_folds.py`: both eye regions cut at the plan's outer ring (26 x 16 mm) and rebuilt as 10 rows of quads from the cut rim to the eye opening (10 x 6 mm).
5. `straighten_nose.py` + `smooth_bridge.py`: the bridge hump (up to 5.6 mm at z 1516-1520) pulled back to a straight root-to-tip line (within 0.65 mm).
6. `smooth_eyes.py`: eye rows smoothed (100 passes, no reprojection). Left and right eye match to 0.13 mm (was 1.07).

Checks (`check_mesh.py`, `check_deviation.py`, `check_fold_angles.py`): closed except the two eye openings (440 edges); 4 true fold-overs at the eyes remain (the base had them); 884 n-gons, 420 poles in the face band, about 1,970 faces with aspect above 3 are unchanged from v12.

## Not in the file (tried, rejected, scratch only)
- Nose and lip reshape toward the chart (`v143_nose*.blend`): profile numbers matched, the surface came out lumpy. The user: "The nose and mouth got worse". Reverted.
- Nostril rings, mouth rings and nostril/mouth caps (`build_regions*.py`, `add_caps.py`): worked as geometry, but the mouth was built 40-44 mm wide where the references say about 58 mm, and the nasolabial loop was never built. Reverted with the nose.
- Retopo (QuadriFlow 4,245 quads, 6 poles): clean, but it lost nose-tip and nostril detail; the user said to put the n-gons back.
- Cranium cap on the v13 mesh (rings, QuadriFlow, taper): none gave a fold-free cap on the approved seam; see the Log.

## Plan (approved in chat, not built): `HEAD_TOPOLOGY_PLAN_v14.md`, `images/midface_plan_round.png`
Built from all 16 references (not one chart): mouth about 0.8 x the eye distance (+-29 mm), four tight mouth rings; one nasolabial loop wrapping the nose wings and mouth down to a flat chin crease (z about 1430); cheek diagonals; nostril rings; nose side view as planes (straight dorsum, flat underside); a squarer jaw contour with a flat chin. Brow line z 1560 (27 mm above the eye centre, approved); eye line z 1533; forehead loop z 1617 (not approved).

## Lessons (also in `blender/AGENTS.md`)
- Use every reference the user sends, together. One chart gave a good profile and a bad mouth width.
- Profile numbers are not a render. The 70% nose matched the chart and looked lumpy; render before reporting a shape change.
- A y-only push cannot make a flat nose underside; move along the surface normal. Count folds by angle: 90-135 degrees are creases, over 150 are fold-overs.
- Smoothing that reprojects onto the old skin puts the terraces back. Smooth without projection, with the rim and opening fixed.
- If a shading offset appears, mirror the left and right halves of the render: here the bridge was centred and the light came from one side.

Scripts have the scratchpad paths of this session hard-coded (`/tmp/claude-0/...`); edit them. `data/` holds the chart silhouette rows, landmarks and the base nose profile the scripts read.
