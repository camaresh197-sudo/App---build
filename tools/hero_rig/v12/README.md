# Wren v12: semi-real male head built from measured reference (Blender only)

Not in the game; not exported to glb. Headless Blender 5.3 via `pip install bpy`. Run `python3 -I build_v143.py` (writes `feat_v143.blend`, about 37k verts), then `python3 -I rend_hi.py -- feat_v143.blend out.png` (also `rend_side.py`, `rend_front.py`, `rend_nocav.py`, `rend_flat.py`). `prop.py` prints centreline proportions from a .blend (edit its path).

## How it is built
- Skull: a `bmesh` loft over a ring table (z, half-width, back depth, front depth) generated from the Head Topology reference silhouette (skin-colour threshold, normalised by crown-to-chin H = 0.274 m, t = (crown - z) / H). Rings are PCHIP-densified to 0.004 m. Crown is a near-sphere of radius about 0.092 m. No neck, ears or hair.
- Eye line at t = 0.50 (z 1.533). Eyes: dish socket 0.024 deep, lids by local subdivision (rim, crease, eyebag).
- Nose: Gaussian ridge, tip, wings, alar creases, bridge ridge with sidewall shadow lines; nostrils are separate dark ellipsoid objects (`nostril_l`, `nostril_r`). Fine mesh strips over the nose only (see `for _rx,_rz in` block).

## Gotchas
- A fine-mesh region that reaches the eye area breaks the lid outlines (v138: 71k verts, segmented lids). Keep nose strips clear of the lids.
- Ring terms resolve as contour terraces on a fine mesh; use `gbump` Gaussians instead.
- Do not nudge rings by eye. Measure the reference silhouette first (five failed egg/dome passes, v114-v118).
- Open: blocky shading at the inner eye corners (coarse mesh at socket dish and lids; needs a finer lid mesh); nostril pieces read as glossy seeds up close; 8 mm gap at the nose base; no ears, neck or hair.

## Saved outputs
- `feat_v143.blend` (1.3 MB): the head as built, 37k verts, local only.
- `feat_v143_hi.png`, `feat_v143_side.png`, `nose_v143.png`: front, side and nose close-up renders of that build.
