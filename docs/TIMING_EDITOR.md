# TIMING editor (in-game)

User request, 2026-11-22 (their wording, from the chat mock — the grid was a sketch, not a layout):

1. IPA should be editable and heard immediately on hitting play.
2. Clicking on a word should give a detailed way to edit the length of each letter and syllable, the more detailed the better.
3. Ability to edit the sung voice in game.
4. The vocal map should change to map timing and word length changes.
5. Clicking on graph should give a toggleable note-by-note breakdown of the vocals and instruments.
6. Ability to start and stop at any point in the line; click a spot to place the playhead there, play to play it.

Layout is a compact 612 px panel inside the existing secret menu (TIMING tab), not the
spreadsheet in the chat.

## What is in the game now

All 16 sung lines (A0–A6, B0–B3, C0–C6, tag0, tag2, F0, B6) are editable, and every one has a
graph. The line picker is three columns.

- **Words** show the word, onset and IPA; tap a word to open its editor.
- **Word editor:** the IPA is a row of phone chips. Tap a chip, then a symbol from the
  40-phone palette to replace it; `-20 ms` / `+20 ms` change that phone's length; `ADD`,
  `DEL`, `RESET` and `DONE` finish. `LEN` is the sum of the phones.
- **Preview:** unedited lines play the real clip. Edited lines play the **embedded Piper**
  when present (`PiperVoice.available()`), the **diphone bank** otherwise, and real-clip
  word slices as the last fallback. The embedded render is the exact singer, offline.
- **Graph:** notes (from `data_victory.json`), the vocal strip and the instrument strip;
  `VOX` / `INST` / `NOTES` toggle them. Word blocks use the edited onset and phone lengths.
- **Playhead:** tap the graph to set PLAY's start; the moving line tracks the sequencer.
- **A/B:** `BEFORE` plays the shipped line, `CURRENT` plays the edited one; `RESET LINE`
  restores the line. Shipped onsets stay as faint ticks behind the edited ones.

## Data and tools

- `tools/diphone_bank.py` renders every phone pair with Piper into one
  `godot/hula/audio/di_bank.ogg` plus `data_diphone_bank.json` (start/duration per pair).
  That is the offline preview: a pair keeps the transition, which is what isolated phones
  lost.
- A line in `data_word_timing.json` may now carry `ipa` (one string per word) and
  `phones` (one list of `{"p", "d"}` per word). Missing fields are derived from
  `data_phonics.json` and the bank at load; the phone saves its edits in
  `user://word_timing.json`; COPY / SAVE behave as before.
- `tools/retime.py` accepts `ipa` / `phones` in the copied JSON and stores them.
- `tools/build_timing.py` fills `data_word_timing.json` for every line from the same grid the
  renderer uses (kept edits survive). `tools/line_env.py --lines <ids>` rebuilds the graphs.
- `tools/build_stems.py <mix_base>` rebuilds `stems/` from a `shotter mix` capture; the stems
  now cover the full 70 s track, so the late lines (C4, C6, tag, F0, B6) locate.

## Why it was gibberish (fixed 2026-11-22)

Piper's voices are trained on `^ _ p1 _ p2 _ ... pn _ $`: a pad id (`_`, id 0) after **every**
phoneme. Our custom-IPA paths (`word_audio`, `diphone_bank.py`, `PiperPlugin.kt`) sent
`^ p1 p2 ... $` with no pads. The model then babbles at about half the length. Measured with
a speech recogniser on the same phonemes: "Welcome to the victory dance" came back as
"Wanda, the paper you'd ask." without pads and correctly with them. Two smaller causes:

- The editor dropped stress marks (`ˈ`) when splitting IPA and rebuilt the string without them.
  Dropped stress alone turned "I am Jeff and I'm so gay" into "I am Jiff and on, so gay".
  Phones now carry `m` (stress mark before) and `x` (length mark after); both reach Piper.
- `data_phon_bank.json` durations came from the no-pad renders (a vowel could be 0.43 s), so default
  phone lengths and the slicing of a word were wrong. `tools/phone_durations.py` rebuilds them
  as medians of real in-context alignments (vowels ~0.07-0.12 s, stops ~0.04-0.06 s).

`piper_sing.py` now renders the **whole edited line in one pass** (`line_audio`: pads, stress,
space tokens between words, model alignments patched in via the `onnx` package) and cuts each
phone out at its real boundary before warping it to the edited length and onset. Test it
with a recogniser, not by eye: `render_phones` on A0 with default phones transcribes as
"I am Jeff and I'm so gay" (was empty), C0 as "Shake the street, Jeff wants to bait" (was "I... I... I...").
Do not judge Piper by a single 0.1-0.4 s word through a recogniser: even the official render fails there.

## Limits — read before trusting it

- **The diphone preview is OFF** (`DIPHONE_PREVIEW := false` in `menu.gd`): a speech recogniser hears nothing in it even with correct pads. Without the Piper build, an edited line plays the real clip at the edited onsets; hear IPA and length edits via COPY + `retime.py`. The old description follows.
- The diphone preview was a sketch: pairs are cut to the phone length and overlap, so joins
  can be audible and the pitch is flat. It is for judging IPA and timing, not the final
  voice. `di_bank.ogg` was rebuilt with pads (1.98 MB); not yet heard on a phone.
- `retime.py` writes `ipa` / `phones` for a changed line; `piper_sing.py` re-sings it as one
  line pass. Unedited lines keep the original text-based render.
- The on-phone Piper plugin still synthesizes **one word at a time** (`PiperVoice.sing_stream(ipa)`),
  so an edited word has no line context. It is intelligible now (pads), but a whole-line
  call with the edited words substituted is the next improvement.
- Phones espeak en-us never emits (`r`, `ɾ`, `ʔ`) have no measured length; typical values are used.
- IPA is per word, and a palette edit replaces one phone. There is no free-text field
  on the phone yet; the palette is the whole supported set.
