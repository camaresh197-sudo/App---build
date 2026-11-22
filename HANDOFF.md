# Handoff: Wren (Claude) <-> Greg

Git is our only channel. Pull before you start, push when you stop.

## Start of every session
Read this file first, then `AGENTS.md` (rules, complaints, numbering, overrides) and `PERSONALITIES.md`, then `git log origin/godot -5`.
Only claim what the Log, commits or your own runs show. If an entry about you is unconfirmed, say so in the Log.

## Claimed
| Who | Files | Since |
|---|---|---|
| — | (none) | — |

## Gotchas
- `var x := SOME_CONST_ARRAY[i]` fails to compile (untyped array). Write `var x: String = ...`. A `menu.gd` compile error leaves Android showing only the background.
- Pre-push check: `godot --headless --path godot/hula --quit-after 120 -- --smoke`, and look for `SCRIPT ERROR` (Godot 4.6.3).
- The updater mounts `user://.../packs` over `res://`. On desktop that is now disabled unless the game is launched with `-- --packs`; otherwise a stale pack silently overrides the disk code. The TIMING tab shows `BUILD n` or `DEV BUILD`.
- `shotter` face/sheet/map modes need a real renderer. `--headless` hangs; run the windowed binary and kill a hang.
- Narration-only cutscenes have no `data_cutscenes.json` entry. Their text lives in `data_theater.json`.
- Shape keys: `mesh.vertices` and `key_blocks[0]` are separate. Write both (see `docs/CHARACTER.md`).

## Open items (as of 2026-11-22)
- **Edit-only diphthong samples (TODO):** add vowel+glide samples for word editing (e.g. `e|ɪ#edit`, `a|ʊ#edit`), rendered with Piper by `tools/diphone_bank.py`. Existing bank entries stay unchanged; only the word-edit preview reads the new keys. Blocked here: no Piper model or `piper` package in this session. Owner: whoever runs the bank script with the model.
- **"gay" by ear:** the diphthong now plays as one bank sample (commit 22f89ae). Confirm it says "gay", not "geh", on a phone.
- **Branch cleanup and default branch:** 19 merged branches still on origin (list in the scratchpad notes). Needs someone with repo admin rights; the session's push was denied.
- **TIMING tab (all unheard on a phone):** words move freely (onsets, bar-length handle on each word's right edge, LOCK toggles); the layout is new; the graph is 150 px with notes on both strips; IPA edits play through the Piper APK; per-syllable pitch (ST -1 / +1) is applied by the PSOLA shifter in `scripts/psola.gd`; the word fit is limited to 0.8x-1.3x; diphthongs are marked. Check each on a phone and send the TIMING status line.
- **Piper APK:** the plugin and model load (status "plugin + model ready" once build 8+ is installed). The model lives in `piper-assets/` in the Android build. Rebuild with `piper-apk.yml` when plugin files change.
- **Pitch in the PC re-sing:** `st` is kept per syllable in the data but `piper_sing.py` does not read it yet, so the clip and the phone preview will differ.
- **Diphthongs:** recognised and marked (`dip`), with minimum lengths. The phone preview ignores per-sound lengths; the glide there depends on the 0.8x-1.3x fit. No automatic glide when a diphthong is edited to a monophthong.
- **Audio:** B2 unsung in `mix victory 30`; the instrument stem over-subtracts where vocals sit; the vocal bus overdrives before the limiter (2026-11-21 mix, 1220 clipped samples).
- **Coverage:** word onsets for all 16 sung lines come from the render grid, not from audio. Map: playtest difficulty and star write; milestones 4–5 to do.
- **Chord conflict:** v-B bar 2, beat 3 sings B over an A-minor chord. Change the chord in `data_victory.json` or keep the passing tone.
- **"I'm" schwa:** Piper renders it as `aɪɐm`; add a sheet entry in `data_phonics.json`.
- **Act intros:** need a music handoff.
- **Branches:** `menu-no-portrait` holds old TIMING and title work. Branch cleanup needs someone with repo rights.

## Map contract (Greg, 2026-11-20)
- 4 acts × 5 nodes, targets 150 → ~1200 (`data/data_map.json`). `start_run(id, target)`; `score ≥ target` wins.
- Stars: 3 if HP ≥ 70 at clear, 2 if ≥ 40, else 1. A loss scores 0 and can be retried.
- Node N unlocks with ≥ 1 star on N−1; `a1_1` is always open. Save keeps `levels: {id: stars}`; endless writes nothing.
- `menu.gd` is the compile tripwire: `:=` on untyped arrays fails there. Full plan: `docs/HANDOFF_LOG.md`.

## Log (newest first)
- **Wren v3 (timing-fixes), 2026-11-22:** Branch `timing-fixes` (on `godot`, 8702dbe): PLAY drift fix, locks kept on reset, diphone preview on, syllable pitch kept through sound edits and applied in the preview, PLAY WORD button, clearer sound editor, diphthongs played as one sample (22f89ae). Not run in Godot here; not heard on a phone.
  **Complaints:** (1) Nothing above is confirmed by ear. (2) The edit-only diphthong samples need the Piper model; run `tools/diphone_bank.py`.
- **Wren v3 (handoff and AUDIO.md), 2026-11-22:** Updated Open items to the state after the TIMING, Piper-model, PSOLA and diphthong work, and updated `docs/AUDIO.md` for per-syllable pitch (PSOLA, `st`), the 0.8x-1.3x fit, diphthong marks and the new word-length and lock controls. Docs only.
  **Complaints:** (1) Open items were not updated after each push; update them with the commit. (2) Nothing in TIMING is confirmed by ear yet. (3) The PC re-sing still ignores `st`; add it before the phone and the clip disagree for long.
- **Wren v3 (diphthongs recognised), 2026-11-22:** User asked the game to recognise diphthongs and add a glide where needed. `_timing_mark_diphthongs` (menu.gd) marks a vowel (e a o ɔ ɑ æ ə ɛ) followed by ɪ or ʊ as one sound: both parts get `dip`, and minimum lengths (0.10 s vowel, 0.08 s glide). It runs when a word's phones are built and after palette edits and ADD.
  Checked: "gay" is marked on load; a palette edit that breaks the pair clears the marks. Smoke clean.
  Limit: Piper's phone preview ignores per-sound lengths (it sets the sound from the whole word), so the glide there is protected by the 0.8x-1.3x fit limit, not by these marks. The marks matter for the PC re-sing and the editor's defaults. The "add a glide" step is not automatic: a word whose vowel was replaced by a monophthong is left as the user set it.
  **Complaints:** (1) Wren's "geh" fix assumed short phones; the real cause was the fit, which the test showed. (2) The glide is not added automatically; decide whether it should be. (3) Phone-level lengths do nothing in the phone preview; say so in the editor.
- **Wren v3 (gay sounds like "geh"), 2026-11-22:** User: "It doesn't always speak out the words correctly. When I spell gay it sounds more like geh." Test with the Piper voice in a carrier phrase: at 1.0x "gay" came out "gain"; at 0.7x still "gain"; at 0.5x "I'll see you now". So the fit that squeezes an edited word to its length is the damage.
  Change: `PiperVoice.sing_stream` now limits the fit to 0.8x-1.3x. Words edited shorter than that run slightly past their length.
  Not done: diphthong phones (`e` then `ɪ`) default to short lengths, so a diphthong has little room; that needs its own default.
  **Complaints:** (1) Wren let the fit go to 0.4x without a test; check any range change in the carrier test. (2) Diphthongs are split into two short phones; keep them together or lengthen the glide. (3) The user has not yet heard the 0.8x limit.
- **Wren v3 (syllable pitch, phone preview), 2026-11-22:** User chose the phone option: pitch per syllable. WORLD is not in the game and GitHub blocks its repository here, so the phone uses PSOLA written in GDScript (`scripts/psola.gd`).
  Pitch: the clip's pitch is estimated by autocorrelation; pitch marks sit on each period's peak; grains are overlap-added at each period, so only the pitch moves. The first version was wrong (identity correlation -0.16); the fix was to step by the spacing to the next mark.
  Editor: ST -1 / ST +1 apply to the syllable of the selected phone, stored as `st` on that syllable's first phone (range -12..12). The header shows the syllable's pitch. Consonants before the first vowel are not pitched.
  Checks: GDScript and Python agree on a Piper clip: identity corr 0.983; +4 gives 1.254x (1.26 expected); unshifted part 1.000; length kept. Harness: +2 then -5 gives 1.12x then 0.84x. Smoke clean. Not checked: on a phone (the Piper plugin is needed for the preview), and the PC re-sing does not use `st` yet.
  **Complaints:** (1) Wren's first PSOLA was wrong on the identity test; test identity before shifts. (2) Syllable pitch is not in the PC re-sing, so the clip and the phone will differ. (3) Grain quality on a phone is unheard; judge it by ear before more DSP.
- **Wren v3 (TIMING layout, taller graph, word length handles), 2026-11-22:** User asked for: a rebuilt layout (left column of full-height buttons, words and graph on the right); a taller sound graph with a seconds ruler and visible note names on both the VOX and INST strips; and control over a word's length and hold.
  Layout: `TL_*` / `TR_*` constants in `menu.gd`. Graph: 496x150, notes drawn on both strips. Length: a handle on each word block's right edge; dragging it changes the word's last sound (the hold), so the bar length changes. Minimum sound 0.03 s, capped at the line's end. Start (onset) drags are unchanged.
  Checks: smoke clean; harness on B0 word 1: +0.3 s hold -> 0.24 to 0.54 s; -0.5 s -> 0.14 s; +9 s capped at 3.36 s. Renders reviewed in a virtual display. Not checked: by finger.
  **Complaints:** (1) Wren ties length to the last sound only; per-sound length still needs the editor. (2) The handle is 14 px wide; check it is big enough for a finger. (3) Layout and graph changes were not pushed; push them with the handle.
- **Wren v3 (AUDIO.md), 2026-11-22:** User: "Add to audio. Md". Updated `docs/AUDIO.md`: edited-line singer, free words and locks, the status line, new tools, and gotchas (Piper pad ids, test with a recogniser on the phone's own path, Piper APK vs packs, model asset folder). Docs only; no code or phone change.
  **Complaints:** (1) Wren left AUDIO.md describing neighbour limits for hours; update the doc with the behaviour change. (2) The doc claims nothing is confirmed by ear; someone must listen. (3) VOCAL.md still lacks the pad-id finding; add it next.
- **Wren v3 (palette taps swallowed; free word timing), 2026-11-22:** User: changing the IPA letters does nothing; wants free reign over word timing. Cause 1 (my regression from 8fd5fc6): `timing_grab` swallowed taps inside the graph's rect while the word editor was open, but the palette is drawn on exactly that rect (`ox+14, 220, 612`), so no palette tap reached the editor. Now the editor owns those taps and the graph rect and markers are cleared while it is open.
  Change 2: `_timing_set_onset` now just clamps one word to 0..line end - 0.1; no push, no order, no neighbour limit. Locked words still do not move. Drag message at the edge: "edge of the line".
  Note: the singer sings words in order, so `retime.py` still rejects out-of-order onsets (message explains); the phone preview does not care.
  Checks: smoke clean; harness on B0: w1 -> 3.0, w3 -> 0.0, w0 -> 99 (stopped at 3.26) with no other word moving; a tap in the old graph rect with the editor open is no longer taken. Not checked: by finger or ear.
  **Complaints:** (1) Wren guarded a rect that was not on screen; test hit areas against what is drawn. (2) Free order means COPY can fail in retime.py; decide whether the singer can sing out of order. (3) Overlapping words can play on top of each other; add a visible overlap cue if it confuses.
- **Wren v3 (Piper fits the word), 2026-11-22:** User: "Changing the ipa does nothing" (plugin working). Found: PLAY cut each Piper word at its edited LEN, but Piper's natural word is longer, so the last phones were chopped (an edit there was never heard) and length edits did nothing.
  Change: `PiperVoice.sing_stream(ipa, target, info)` renders once to measure, then again with `length_scale = target / natural` (0.4 to 3.0); playback no longer truncates; the TIMING line reports "Piper sang N edited word(s): natural X s, fitted to Y s".
  Checks: smoke clean (desktop has no plugin, so the Piper path itself is unrun). Not checked: on a phone.
  Next: edit a phoneme in the FIRST half of a word and in the LAST half, press PLAY, and send the TIMING line.
  **Complaints:** (1) Wren cannot run the plugin on a desktop; test the fit on a phone before trusting it. (2) Length is fitted per word, not per phone; per-phone lengths still do nothing. (3) The first PLAY renders twice per edited word; cache hits afterwards, but the first press may lag.
- **Wren v3 (word locks), 2026-11-22:** User: "Lock the words I don't want to move." Each word box has a LOCK / LOCKED toggle (red box and red graph line when locked). A locked word's onset never moves (drag and nudge say it is locked); moving other words stops short of the nearest locked word, leaving room for the words between.
  Files: `menu.gd` (`_timing_locked`, `_timing_toggle_lock`, `_timing_set_onset`, word grid, graph colour). Locks are saved with the timing as `locks` (a bool per word), so COPY / SAVE carry them; `retime.py` ignores the key.
  Checks: smoke clean; harness on B0 with word 2 locked: neighbours stopped at 0.41 and 0.45, the locked word stayed at 0.43, and after unlocking it moved. Not checked: by finger on a phone.
  **Complaints:** (1) Wren's lock toggle sits in the word box corner; check it is easy to hit with a finger. (2) A lock holds the start only; locking word length is a separate feature. (3) RESET LINE may clear locks; check it before trusting them.
- **Wren v3 (words push their neighbours), 2026-11-22:** User: the plugin works, but timing does not move word starts, or stops a word before the next word's old position. Cause 1: drag and nudge clamped a word to the next word's current onset. Cause 2: an unedited word's slice length came from the gap to the next new onset, so a moved word was cut or ran into its neighbour.
  Change: `_timing_set_onset` moves a word and pushes neighbours along (order and 0.02 s gap kept, last word still starts inside the line); drag, nudge and load use it. Unedited words play their shipped length (`_timing_shipped_len`). Removed the `piper.gd.uid` I committed by mistake.
  Checks: smoke clean; harness on B0: word 1 to 1.5 s pushed later words forward, word 3 to 0.1 s pulled earlier words back, last word capped at 3.26 s. Not checked: by ear.
  **Complaints:** (1) Wren bounded drags by the neighbour's current onset; free movement needs a push rule. (2) Pulling a word far left drags earlier words with it; maybe add a lock. (3) `git add -A` swept up a generated uid file; add only named files.
- **Wren v3 (Piper model missing from APK), 2026-11-22:** User screenshot, build 7: "model failed: assets/piper is empty". The model was copied into `src/main/assets/piper`, which Godot's export rewrites, so it was lost.
  Fix in `piper-apk.yml`: the model goes in `piper-assets/piper`, and build.gradle adds `main.assets.srcDirs += ['piper-assets']` beside the template's `main.res.srcDirs`.
  Checks: the sed edit was run on the real template and gives the expected lines. Not checked: the CI build or the model loading on the phone.
  Next: install the new `HulaVaqueroPiper`; the status line should then read "plugin + model ready".
  **Complaints:** (1) Wren put the model where the export overwrites it; check file survival after export. (2) The 77 MB APK size was misread as proof the model was in; check the assets list. (3) Nobody has confirmed the model loads on the phone yet; read the status line first.
- **Wren v3 (Piper model error shown), 2026-11-22:** User screenshot: TIMING says "plugin loaded but model failed" and "Update ready — closing to apply"; the Piper APK is `BUILD 5`. Logcat is not visible on the phone, so the reason was hidden.
  Change: `PiperPlugin.kt` keeps the first load failure (`loadError`, `lastError()`); `piper.gd` shows it on the TIMING line.
  Checks: smoke clean. Not checked: Kotlin compile (CI runs it), the model load itself.
  Next: install the new `HulaVaqueroPiper` artifact and read the TIMING line; it names the failure.
  **Complaints:** (1) Wren hid the cause in logcat; show failures where the user looks. (2) The model may not fit on this phone; check memory before blaming the file. (3) Nobody has read the new error line yet; read it before the next fix.
- **Wren v3 (onsets past the line), 2026-11-22:** User: "Changing word timing doesn't play if it's past the default vocal graph." Cause: the graph and PLAY use the line's 2 bars (3.36 s), but a drag or nudge could move the last word to 9.9 s. Such words were drawn off the graph and PLAY stopped before them.
  Change: `_timing_line_len`, `_timing_onset_bounds` and `_timing_clamp_onsets` in `menu.gd`. Drags, nudges and saved timing are kept inside the line; the last word may start up to 3.26 s. The shipped onsets already sat inside it, so no shipped timing moves.
  Checks: smoke clean; a harness check pushed the last word +9 s and it stopped at 3.26 s, the first word -5 s stopped at 0 s. Not checked: by ear, or on a phone.
  Decision: words cannot move past the line's end. A word that needs to sit later must move into the next line's bars, which would overlap that line's audio. If you want longer lines, change the bar count in `data_word_timing.json` and the victory sequence together.
  **Complaints:** (1) Wren let the drag range ignore the line the graph draws; check ranges against what is shown. (2) Words near the end get cut by the line end; show a cut warning or extend the line. (3) Nobody has played a moved word on a phone yet; test a word at 3.0 s first.
- **Wren v3 (Piper status), 2026-11-22:** User: "I applied the piper apk and ipa still don't work." Code trace: the TIMING tab printed "Piper preview (exact)" whenever the plugin singleton existed, even when `singIpa` returned no audio; the edited word then silently played the real clip. So a broken plugin looks like "nothing happens".
  Change: `PiperVoice.status()` (cached) reports plugin missing, model failed, or ready; `_timing_play_piper` shows that status and says when Piper gave no audio for an edited word. Smoke clean. Not checked on a phone.
  Also true: Piper renders IPA only; phone-length edits do not change the Piper audio (the Kotlin `singIpa` ignores `d`).
  Next: read the TIMING message after one PLAY on the Piper APK and report it; that line says which of the three cases it is.
  **Complaints:** (1) Wren shipped a silent fallback; a fallback must say it fell back. (2) Length edits do nothing under Piper; either stretch the output or label the lengths as not applied. (3) Nobody has read the phone's status line yet; ask for it first next time.
- **Wren v3 (piper-apk run 3), 2026-11-22:** User: "The piper apk failed." Run 3 got past the template step and Gradle setup, then failed in `compileStandardDebugKotlin`: `PiperPlugin.kt:35` used `getActivity().assets`, which Godot 4.6 declares nullable. Fixed with `getActivity() ?: return false`.
  Checks: the log shows the template install, the Gradle run and the Kotlin compile; that compile error was the only one reported. Not checked: the rest of the Kotlin build and the APK (no SDK here).
  Next: watch the `piper-apk` run that follows this push; if it fails, the log is `get_job_logs` with `failed_only`.
  **Complaints:** (1) Wren pushed the Kotlin plugin untested; compile it in CI before saying it works. (2) Greg's plugin calls Godot APIs from memory; check them against the 4.6 headers. (3) Wren should have read the failed log before reporting the hang as fixed.
- **Wren v3 (piper-apk hang), 2026-11-22:** User: "2" (look at why piper-apk hangs). Both runs (1 and 2) sat on "Install the Android build template" for over an hour. Cause: `godot --install-android-build-template` is only a modifier for `--export-*`; alone it starts the game headless and never exits (reproduced locally, killed at 40 s).
  Second bug behind it: later steps used `android/build` at the repo root, but the template installs to `godot/hula/android/build`. Fixed in `piper-apk.yml`: install via a throwaway `--export-debug`, assert the template exists, use the right paths, add step and job timeouts.
  Checks: with real 4.6.3 templates the install step puts `build.gradle` in `godot/hula/android/build` and exits in seconds; the manifest and gradle seds match the real template. Not checked: Gradle, the Kotlin plugin, or the APK itself (no Android SDK here).
  Next: push, watch the new `piper-apk` run; cancel runs 44995585000 and 45000047988 in the Actions tab (they hold runners until timeout).
  **Complaints:** (1) Greg never watched piper-apk run once; a green first run beats three more features. (2) Greg's workflow had no timeout; one bad flag hung a runner for hours. (3) Wren caught this only after the phone failed; check CI before reporting it shipped.
- **Wren v3 (diphone off), 2026-11-22:** User: "It didn't fix the gibberish problem." My earlier fix repaired the PC re-sing and the plugin ids, not what the phone plays: with no Piper APK the phone uses the diphone bank, and a recogniser still hears nothing in it (A0: empty; C0: "Thanks for watching. Bye!").
  The Piper APK has never finished building (`piper-apk` runs 1 and 2 still in progress), so the phone has only ever had the diphone fallback.
  Change: `DIPHONE_PREVIEW := false` in `menu.gd`. Edited lines now play the real clip at the edited onsets; IPA and phone lengths are heard after COPY + `retime.py`, or in the Piper build. Smoke clean. Not heard on a phone.
  Next: get one `piper-apk` run to finish and install it; then feed the plugin the whole line, not one word.
  **Complaints:** (1) Wren tested the PC path and called the phone fixed; test what the phone plays. (2) Greg's diphone preview was never recognised-tested before shipping; unintelligible stitching should not ship. (3) piper-apk runs hang unnoticed for an hour; someone must check them.
- **Wren v3 (gibberish root cause), 2026-11-22:** User: "It still produces gibberish. How do we fix this?" Cause: every custom-IPA path sent Piper `^ p1 p2 $` without the pad id after each phoneme; the voice is trained on `^ _ p1 _ p2 _ $`. Fixed in `piper_sing.py`, `PiperPlugin.kt`, `diphone_bank.py`.
  Also: stress marks were dropped by the editor (now `m`/`x` keys on each phone); default phone lengths came from the broken renders (rebuilt: new `tools/phone_durations.py`); re-sing now renders the whole line in one pass and cuts phones at the model's real alignments.
  Checks: recogniser on real `render_phones` output: A0 "I am Jeff and I'm so gay" (was empty), C0 "Shake the street, Jeff wants to bait" (was "I... I... I..."); B0 partial ("Jeff is here, so..."). Import 0, smoke clean. Not checked: by ear, the Kotlin plugin (no SDK), a phone.
  Files: `tools/piper_sing.py`, `tools/phone_durations.py`, `tools/diphone_bank.py`, `android/piper/.../PiperPlugin.kt`, `menu.gd`, `data_phon_bank.json`, `di_bank.ogg` (rebuilt), `docs/TIMING_EDITOR.md`.
  Next: plugin takes the whole line (edited words substituted) instead of one word; listen to B0 (held "gay"); rebuild the APK.
  **Complaints:** (1) Greg shipped three previews on the same unpadded ids; compare against Piper's own ids first. (2) Greg's per-word plugin discards line context; pass the whole line next. (3) Wren should have diffed Piper's source in session one; run a recogniser before claiming.
- **Greg v4 (embedded Piper), 2026-11-22:** User: "do number 2." Built the offline exact preview: `PiperPlugin.kt` runs the VITS model on-device via ONNX Runtime, `piper.gd` wraps it, and `_timing_play_piper` renders edited words while unchanged words keep the shipped clip.
  Build: new `piper-apk.yml` (AndroidPiper preset, Gradle build; the model is downloaded in CI, never committed). `godot-apk` now ignores `android/**`, `addons/**`, `tools/**` and `stems/**`, so plugin-only pushes do not rebuild packs and a broken plugin cannot block game updates.
  Install path: the Piper APK is a workflow artifact; install it on the phone once, then pack updates continue as before.
  Files: `android/piper/.../PiperPlugin.kt`, `scripts/piper.gd`, `menu.gd`, `sound.gd` (`play_stream`), `export_presets.cfg` (AndroidPiper), `docs/PIPER_ANDROID.md`.
  Checks: import and smoke clean locally; the APK itself is unverified (no local SDK). Per-phone lengths are not fed to the plugin yet.
  **Complaints:** (1) Greg built an APK he cannot run; verify it on the phone first. (2) The plugin JNI path is untested; check logcat on first load. (3) `godot-apk` ignores `tools/**` now; run `codemap` manually when tools change.
- **Greg v4 (stale pack cause), 2026-11-22:** User: "changing anything still produces gibberish." Cause: a normal desktop launch mounted stale packs from `user://packs` (`code-223/224`, `assets-1cc1…`) over `res://`, so every fix was invisible. Deleted that folder; desktop now ignores packs unless launched with `-- --packs`.
  Added a `BUILD n` / `DEV BUILD` tag on the TIMING tab so the running code is visible.
  Files: `updater.gd`, `menu.gd`, `HANDOFF.md`. This does not touch the phone's update path; it still mounts packs on mobile.
  Checks: import 0, smoke 0; screenshot shows `DEV BUILD` and the new BEFORE/CURRENT/RESET row. The local packs folder is gone, so the next normal launch runs disk code.
  **Complaints:** (1) Greg tested with stale packs mounted for sessions; clear user://packs before judging audio. (2) The desktop updater mounted old code silently; the new DEV BUILD tag should stay visible. (3) The phone build is still unconfirmed; check BUILD on the TIMING tab after restart.
- **Greg v4 (diphone preview), 2026-11-22:** User: "do 1 first." Built the offline diphone bank: `tools/diphone_bank.py` renders all 1600 phone pairs with Piper into one 1.2 MB `audio/di_bank.ogg` + `data_diphone_bank.json`.
  Edited lines now play that bank at the edited onsets and phone lengths; unedited lines keep the real clip. IPA edits are audible on the phone immediately, with the transition that isolated phones lost.
  Files: `menu.gd`, `sound.gd` (stop queued bank chunks), `docs/TIMING_EDITOR.md`, `tools/diphone_bank.py`, `audio/di_bank.ogg`, `data/data_diphone_bank.json`.
  UI: `BEFORE` plays the shipped line, `CURRENT` plays the edit, `RESET LINE` restores it; shipped onsets are faint ticks behind the edited ones.
  Checks: bank 1600 pairs / 142.6 s; import 0, smoke 0 (16-resource exit warning); PLAY-on-edit ran with no errors. Not checked: by ear, or on a phone.
  Exact re-sing still runs `retime.py`; the bank is a preview with flat pitch and possibly audible joins.
  **Complaints:** (1) Greg shipped the bank unheard; listen to B0 before trusting it. (2) The pairs are cut to one phone length; check whether the overlap smears words. (3) No phone test yet; try the TIMING tab on build 267.
- **Greg v4 (IPA preview fix), 2026-11-22:** User: "all changes cause gibberish." Removed the phoneme preview: splicing Piper's isolated phones was the gibberish. PLAY now plays the real clip with the edited onsets; IPA and phone lengths are silent until a re-sing.
  Fixed the editor so a palette change rewrites the word's IPA string (it only changed the hidden phone list before, hence "does nothing").
  Re-sing: `piper_sing` now synthesizes each word's whole phone sequence in one pass and divides its frames between the edited phone lengths, instead of splicing single phones.
  Files: `menu.gd`, `piper_sing.py`, `phoneme_bank.py`, `docs/TIMING_EDITOR.md`; deleted `audio/phon/*`. `sound.gd` untouched.
  Checks: import 0, smoke 0 (12-resource exit warning); the screenshot shows a palette change rewriting the header IPA; the retime B0 test re-sang cleanly, then was reverted. Not checked: by ear, or on the phone.
  **Complaints:** (1) Greg shipped the sketch without an ear test; hear a word before the next preview. (2) The IPA display was never synced; test the visible string on every edit. (3) Re-sing quality is still unheard; listen to a retimed line before pushing.
- **Greg v4 (TIMING editor), 2026-11-22:** Built the on-phone IPA and phone-length editor the user sketched: tap a word, edit its phones on a 40-symbol palette, `-20`/`+20 ms`, ADD/DEL/RESET; tap the graph to set PLAY's start; VOX/INST/NOTES toggles.
  Preview (removed later this session; see the top entry): `tools/phoneme_bank.py` rendered `audio/phon/p<hex>.wav` + `data_phon_bank.json`.
  Files: `menu.gd`, `sound.gd` (wav streams, victory step offset, stop phonemes), `shotter.gd` (`timing` mode), `retime.py`, `docs/TIMING_EDITOR.md`, `AGENTS.md`.
  Checks: import 0, smoke 0 (12-resource exit warning); screenshots of the graph and word editor; sketch PLAY ran with no errors. Not checked: audio by ear, or on the phone.
  Pending: none for the sketch; `piper_sing.py` now renders a line's edited `phones` list (each phone alone, warped to its edited length), so `retime.py` applies IPA and lengths instead of only onsets.
  All 16 lines are now editable with graphs: `build_timing.py` fills onsets from the render grid, a fresh 70 s mix plus `build_stems.py` rebuilt `stems/`, and `line_env.py` wrote all 16. Found and fixed `piper_sing` dropping explicit onsets (the 6-tuple was never read).
  Branch: built on `greg-timing-editor`, fast-forwarded to `godot` in `c98cc25`; `godot-apk` 44989699677 is green (build 262), so the phone gets it.
  **Complaints:** (1) Greg left per-phone re-sing unimplemented; wire piper_sing before calling the editor exact. (2) Wren's graph showed waveform only; the note lane now needs a phone check. (3) Sketch voice is untested by ear; listen to a dragged word before trusting preview.

Older entries: `docs/HANDOFF_LOG.md`, including the 2026-11-22 Wren v2 and Greg v3 entries and the Greg notes.
