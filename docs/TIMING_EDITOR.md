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

- **Words** show the word, onset and IPA; tap a word to open its editor.
- **Word editor:** the IPA is a row of phone chips. Tap a chip, then a symbol from the
  40-phone palette to replace it; `-20 ms` / `+20 ms` change that phone's length; `ADD`,
  `DEL`, `RESET` and `DONE` finish. `LEN` is the sum of the phones.
- **Preview:** unchanged lines play the shipped clip. As soon as IPA, phone lengths or
  onsets differ, PLAY switches to the **phoneme sketch** so the edit is audible on the
  phone with no PC.
- **Graph:** notes (from `data_victory.json`), the vocal strip and the instrument strip;
  `VOX` / `INST` / `NOTES` toggle them. Word blocks use the edited onset and phone lengths.
- **Playhead:** tap the graph to set PLAY's start; the moving line tracks the sequencer.

## Data and tools

- `tools/phoneme_bank.py` renders the bank once from Piper:
  `godot/hula/audio/phon/p<hex>.wav` and `godot/hula/data/data_phon_bank.json`
  (IPA, natural length, voiced flag, base pitch). It is a sketch voice, not the singer.
- A line in `data_word_timing.json` may now carry `ipa` (one string per word) and
  `phones` (one list of `{"p", "d"}` per word). Missing fields are derived from
  `data_phonics.json` and the bank at load; the phone saves its edits in
  `user://word_timing.json`; COPY / SAVE behave as before.
- `tools/retime.py` accepts `ipa` / `phones` in the copied JSON and stores them.

## Limits — read before trusting it

- The phone cannot run Piper. The sketch concatenates one sample per phone, so joins are
  buzzy and pitch is not the song's melody; it is for judging timing, length and rough
  pronunciation.
- `piper_sing.py` still sings the text in `data_phonics.json`; it does not consume the
  per-phone lengths yet. **Next code change:** make `sing_clip` synthesize from the
  edited phone list and warp each phone to its edited length, then the re-sung line
  matches the sketch.
- IPA is per word, and a palette edit replaces one phone. There is no free-text field
  on the phone yet; the palette is the whole supported set.
