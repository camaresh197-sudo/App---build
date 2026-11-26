# Face topology plan (Wren v13, 2026-11-26): follow the facial muscles

Reference: the muscle chart with the wireframe overlay on the right half. Goal: edge loops that run along
the muscle lines, so the face deforms the way a real face does. Plan only; no geometry changed.

## Muscle lines to follow (from the reference)
| Region | Muscle | Loop it needs | Status on retopo head |
|---|---|---|---|
| Eyes | orbicularis oculi | concentric rings round each eye | done (eye patches, W053-W054) |
| Mouth | orbicularis oris | concentric rings round the lips | done (mouth patch, W073; corners open, W080-W084) |
| Nose | nasalis / alar | ring round each nostril, wing as crescent | partial (rings only, no crescent, W072) |
| Cheek | zygomaticus major and minor | diagonal loops from the cheekbone down to the mouth corner | not done: grid |
| Nasolabial | levator labii superioris | diagonal loop from the nostril wing to the mouth corner | not done |
| Forehead | frontalis | horizontal loops across the brow | not done: cranium is radial (W090-W101) |
| Temple / jaw | temporalis, masseter | loops following the jaw line down to the chin | not done |

## Order of work (each step checked before the next)
1. **Cheek and nasolabial (first).** Place the zygomatic and nasolabial lines as curves on the high-poly skin
   (ray-cast, as with the wing and cranium checks). Render the placed curves over the head. No build until approved.
2. **Build one cheek strip** on a copy: rings along the zygomatic line, stitched to the eye rings. Count folds.
3. **Forehead.** Horizontal loops across the brow, joined to the cranium seam.
4. **Temple and jaw.** Loops along the jaw line to the chin.

## Rules (from W036, W053-W101)
- Place curves on the skin first, then build. Measure folds and open edges after each build.
- Do not select regions by position alone; select by the identity of what was edited (W103).
- Keep one region per step. Commit only a checked, closed result.

## Open risks
- The cheek grid sits between the eye patch and the mouth patch. A new strip must meet both boundaries.
- The forehead loops must meet the cranium seam, which still has a fine serration (W101).
