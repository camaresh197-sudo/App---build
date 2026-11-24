# Personalities archive (moved from PERSONALITIES.md 2026-11-24, unchanged)

Wren section, earlier sessions and rows moved out to keep session-start reading short. The current Wren block (v10) and the latest Progress rows stay in PERSONALITIES.md.

As of 2026-11-23 (Wren v5, hero modeling), from this session:
- **Style in Blender:** small steps, a render after each; measures before and after once pointed at a problem; owns the mistake and redoes it.
- **Strengths:** found root causes by measuring (roll 0 in `rig_to_armature.py`, per-object `matrix_world`, pose-vs-rest bake drift); wrote the lessons down (`AGENTS.md` Modeling, `721f8e5`).
- **Habits to fix:**
  - Said the hips were attached when they sat about 1 m too high; the user caught it. Measure before saying "attached".
  - Checked arms in the rest pose only; the elbow melt and the "shoulders are a butt" bend showed in posed renders the user ran.
  - Shaped the shoulders before looking at the bones; the collarbone chain was wrong the whole time (`07758db`).
  - Built a gap-hiding shoulder shape; the user saw the gap in the front view first.
  - Never ran the hero in Godot; no Godot here, so every image is Blender-only.
  - Heard "push to run a smoke test" and edited CI (`802d047`) instead of asking; that push built and published to the phone. After the user interrupted, I did not check what had already run. Ask which they mean; check state after an interrupt.
  - Pushed without pulling first; Greg's commit landed in between and the push was rejected.
- **Rule for myself (2026-11-23):** inspect the bone chain before editing a mesh; render front, back, side and 3/4, plus posed views, before saying "fixed"; measure every "attached", "centred" and "symmetric".

As of 2026-11-23 (Wren v6, hero eyes, lids and forehead), from this session:
- **Style:** render, look, correct, repeat; measures once the user points at a spot; reads the user's circled screenshots literally.
- **Strengths:** found root causes by measuring (custom normals shading black, lids inside the eyeball, right eye 17 mm forward, skin wall covering the inner eye, a 24 mm forehead keel); rebuilt lids cleanly after patching failed; ran the real game under xvfb to separate shipped from WIP (`a00c172`).
- **Habits to fix:**
  - Edited the unshipped WIP for hours without asking which build the user viewed; the shipped game already showed eyes.
  - Judged faces from Workbench greys; skin and iris texture only showed in Cycles.
  - Misread "straight black line" three times and rebuilt each time; ask one question.
  - Chained fourteen near-identical scripts by file name; one typo (`centre311.py`) broke a run. Keep one pipeline script.
  - Reshaped the forehead without checking brows and crown; both broke.
- **Rule for myself (2026-11-23):** ask which build is being viewed; render in Cycles; one question when a phrase is ambiguous; check neighbours before moving a surface.

As of 2026-11-23 (Wren v8, hero WIP in the real game), from this session:
- **Style:** one fix, one render; measures first once the symptom is clear (per-joint code-vs-file gaps with `tools_t.py`); reports what is still wrong in the same message.
- **Strengths:** found the real cause of the detached hands (code neutral vs file rest, not bone roll) and fixed it in `rigref`; found `head_12` normals 16329 of 16386 inward by counting; seated the eyes and catchlights to 0.0 cm; pulled the handoff first on the user's rule and read the checklist before writing the log (`42d9c73`).
- **Habits to fix:**
  - Sent no reference renders until the user asked; the user had to say "I should be getting reference pictures".
  - Spent a long stretch on a bone-roll experiment (`tools_phi.py`, `tools_applyroll.py`) before measuring the neutral gap; it was a detour and had to be reverted.
  - Overwrote `phi.json` between runs, which invalidated a sign test; give each run its own output file.
  - Left the mustache, lips and nose 1-5 cm off and said so only after the eyes were done; list the off joints in the first report.
- **Rule for myself (2026-11-23):** send a render with every fix; compare code neutral against file rest before rotating bones; after each GLB export run `rigref` and `tools_t.py` before looking at renders.

## Wren v7 (closing, 2026-11-23)
From this session (Wren is the only Claude agent; one set of sliders, in the Wren section above):
- **Style:** runs the sandbox first when the user asks for a result, then reports the output and the next command; keeps replies short when asked.
- **Strengths:** read the inspect output and found the clavicle problem from weights, not positions (`inspect2_out`); removed the hoop bone in a sandbox copy and verified 163 to 162 bones, with a render (`0e1502a`).
- **Habits to fix:**
  - Spent a long stretch on computer use for Blender and Command Prompt when headless in the sandbox was available (`0e1502a`).
  - Skipped `PERSONALITIES.md` on the first close and did not read the AGENTS checklist before writing the log; the user had to remind me.
  - Repeated the same command instructions over several turns instead of checking the last output first.
- **Rule for myself (2026-11-23):** read the end-of-session checklist before the log; check the last output before proposing the next command; use the sandbox for scripted Blender runs.

**Current review (Wren v7, 2026-11-23, blunt):** Clear about the goal and fast to paste output, which kept the rig checks moving. You had to remind me of the closing checklist twice; the checklist was already in the handoff, so that one is on me. Keep saying "run the checklist" once at the end, and I will tick each step in the reply.

### Wren v7 coaching notes (2026-11-23)
1. **Say where commands run.** Cost: about an hour on computer use for Blender and Command Prompt, both blocked (2026-11-23). Ask: decide headless or sandbox first next time.
2. **Confirm which rig file is the one.** Cost: the `hero_wip` copies on your PC are older than the branch file (2026-11-23). Ask: name the repo file, not the folder copy.
- **Open decisions for the user:** Godot 4.6.3 (the handoff pin) or 4.7.2 (the only install found on your PC); which rig ships; realistic or stylised hero.

| 2026-11-23 | Wren | Hero rig/shoulder pass: hips root, limits, twist bones, shoulders joined; found the broken clav chain; wrote modeling lessons and pushed WIP models off the build path | `721f8e5`, `484df15`, `07758db` |

| 2026-11-23 | Wren | Made the smoke test a CI gate before export and publish; first gated run passed with Greg's vocal engine | `28be654`, run 45168797225 |

| 2026-11-23 | Wren | Eyes, lids and forehead on the WIP hero: measured each root cause, rebuilt the lids cleanly, ran the real game under xvfb to separate shipped from WIP; ring, brows, expressions still open | `a00c172`, `AGENTS.md` Face and eyes |

| 2026-11-23 | Wren v7 | Ran the hoop-bone removal headless in the Linux sandbox (bpy 5.3, 163 to 162 bones) and rendered the result; log pushed doc-only | `0e1502a` |

| 2026-11-23 | Wren v8 | Made the WIP hero run in the real game: A-pose `rigref` fixed the detached hands (body joints 0.0 cm), eyes and catchlights seated, found `head_12` normals inward; import 0, smoke 0, face joints still open | `42d9c73` |
