# Eye, lid and forehead scripts (Wren v6, 2026-11-23)
Blender 5.x Python, run as `blender -b --factory-startup --python <script>`. Each script opens one `.blend` and saves the next; the paths are hard-coded to the scratch folder of that session: edit them (like the other `hero_rig` scripts). Needs the standalone Blender 5.2 (pip `bpy` aborts on render) plus `libegl1 libgl1`.
Run in this order, one output file feeding the next (suffix 14 = the run that produced `blender/wip/hero_v6_eyes_keel.blend`):
1. `keel2.py` - flattens the forehead keel (dome 6 mm, fades in 1.545-1.60, out 1.64-1.70) and moves the inner brow pieces back with the skin. Base: the WIP file with the eye work not yet applied.
2. `rebuild14.py` - rebuilds the four lids as dense sphere shells with an almond opening (outer corner 62 deg, inner 24 deg, inner side 25% narrower), exact edge curve, outer shell sunk toward the skin.
3. `definition_a14.py` - iris material, catchlight. 4. `irisscale14.py` - irises 1.1x on the eyeball surface. 5. `irisgrad_c14.py` + `irisfix2_c14.py` - radial iris gradient. 6. `centre3_14.py` - centres each iris in its opening.
7. `ductwedge14.py` - pink tear-duct wedge in each inner corner. 8. `finish2_14.py` - lids use the head's skin material; lash line and waterline strips.
`prehead.py` is UNTESTED (an interrupted run): raises the skin around the eye to meet the lid shell, to remove the faint ring. `render_face_cycles.py` renders the face with Cycles (hat hidden).
Known: lids are ~3,900 faces each; expressions, blinking and the game's lid code were never tested; nothing here ran in Godot.
