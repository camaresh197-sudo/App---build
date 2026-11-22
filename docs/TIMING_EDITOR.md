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
- **Preview:** PLAY uses the real sung clip. Edited onsets are applied word by word, so
  timing is heard immediately. IPA and phone-length edits are saved and copied, but they
  are heard only after `tools/retime.py` re-sings the line — the phone cannot run Piper.
  (A per-phoneme preview was tried and removed: splicing isolated phone samples was
  unintelligible.)
- **Graph:** notes (from `data_victory.json`), the vocal strip and the instrument strip;
  `VOX` / `INST` / `NOTES` toggle them. Word blocks use the edited onset and phone lengths.
- **Playhead:** tap the graph to set PLAY's start; the moving line tracks the sequencer.

## Data and tools

- `tools/phoneme_bank.py` writes `godot/hula/data/data_phon_bank.json` (IPA, natural
  length, voiced flag). The editor uses it for the palette and default phone lengths;
  `piper_sing` uses the lengths to divide a word render between its phones. The WAV
  version (`--wavs`) is no longer used by the game.
- A line in `data_word_timing.json` may now carry `ipa` (one string per word) and
  `phones` (one list of `{"p", "d"}` per word). Missing fields are derived from
  `data_phonics.json` and the bank at load; the phone saves its edits in
  `user://word_timing.json`; COPY / SAVE behave as before.
- `tools/retime.py` accepts `ipa` / `phones` in the copied JSON and stores them.
- `tools/build_timing.py` fills `data_word_timing.json` for every line from the same grid the
  renderer uses (kept edits survive). `tools/line_env.py --lines <ids>` rebuilds the graphs.
- `tools/build_stems.py <mix_base>` rebuilds `stems/` from a `shotter mix` capture; the stems
  now cover the full 70 s track, so the late lines (C4, C6, tag, F0, B6) locate.

## Limits — read before trusting it

- The phone cannot run Piper. PLAY is the real clip plus edited onsets; IPA and phone
  lengths are silent until `retime.py` re-sings. Splicing isolated phones was tried and
  removed — it was the gibberish.
- `piper_sing.py` sings an edited line as **whole words**: the word's phone sequence is
  synthesized in one pass (context kept), then its frames are divided between the edited
  phone lengths. `retime.py` writes `ipa` / `phones` for a changed line and triggers this.
  Unedited lines keep the original text-based render.
- Word renders are synthesized in isolation, so a re-sung edited word can sound slightly
  detached from its neighbours; that is the cost of arbitrary IPA without an alignment model.
- IPA is per word, and a palette edit replaces one phone. There is no free-text field
  on the phone yet; the palette is the whole supported set.
