# Victory lyrics ΓÇö bars, syllables, notes

Generated from `data_lyrics.json`, `data_vox.json` and `data_victory.json`.
Step = sixteenth-note slot in the victory sequencer (0.105 s, 16 per bar);
four steps = one beat. Chorus lines are two bars and are sung one syllable
per beat, so their notes are written at steps 0, 4, 8, ...

## Lines

| Line | Section / bars | Lyric | Words (syllables) | Syll. | Notes (step:note) |
|---|---|---|---|---|---|
| A0 | v-A 0 | I am Jeff and I'm so gay | I(1) am(1) Jeff(1) and(1) I'm(1) so(1) gay(1) | 7 | 0:G5 3:B5 6:D6 12:G5 |
| A2 | v-A 2 | I like Jake's mom, cuz of Jake | I(1) like(1) Jake's(1) mom(1) cuz(1) of(1) Jake(1) | 7 | 0:B5 2:G5 5:B5 |
| A4 | v-A 4 | Jake's mom plays with Jeff all day | Jake's(1) mom(1) plays(1) with(1) Jeff(1) all(1) day(1) | 7 | 0:B5 3:D6 6:B5 10:G5 |
| A6 | v-A 6 | To make Jeff feel proud and gay | To(1) make(1) Jeff(1) feel(1) proud(1) and(1) gay(1) | 7 | 0:E5 3:G5 7:C6 10:G5 |
| B0 | v-B 0ΓÇô1 | Jeff is gay, so gay | Jeff(1) is(1) gay(1) so(1) gay(1) | 5 | 0:G5 4:C6 8:G5 12:E5 16:B5 (5 beats, last held) |
| B1 | v-B 2ΓÇô3 | Jeff is gay, so gay | Jeff(1) is(1) gay(1) so(1) gay(1) | 5 | 0:A5 4:C6 8:B5 12:A5 16:A5 (5 beats, last held) |
| B2 | v-B 4ΓÇô5 | Jeff is gay, so gay | Jeff(1) is(1) gay(1) so(1) gay(1) | 5 | 0:G5 4:C6 8:G5 12:E5 16:B5 (5 beats, last held) |
| B3 | v-B 6ΓÇô7 | Gay gay gay gay Jeff's so gay | Gay(1) gay(1) gay(1) gay(1) Jeff's(1) so(1) gay(1) | 7 | 0:A5 4:D6 8:D6 12:F#5 16:G5 20:B5 24:D6 (7 beats, last held) |
| C0 | v-C 0 | Jake is baked, Jeff wants to bate | Jake(1) is(1) baked(1) Jeff(1) wants(1) to(1) bate(1) | 7 | 0:G5 3:B5 6:D6 12:B5 |
| C2 | v-C 2 | He has done the most the day | He(1) has(1) done(1) the(1) most(1) the(1) day(1) | 7 | 0:G5 3:C6 6:G5 10:C6 |
| C4 | v-C 4 | He'll hug Jake on their next date | He'll(1) hug(1) Jake(1) on(1) their(1) next(1) date(1) | 7 | 0:G5 3:B5 6:D6 10:B5 |
| C6 | v-C 6 | What a shame that Jake is tall | What(1) a(1) shame(1) that(1) Jake(1) is(1) tall(1) | 7 | 0:E5 2:E5 4:A5 7:C6 10:A5 |
| tag0 | v-tag 0 | Jeff is gay so gay | Jeff(1) is(1) gay(1) so(1) gay(1) | 5 | 0:G5 2:G5 4:C6 |
| tag1 | v-tag 1 | Jeff is gay so gay | Jeff(1) is(1) gay(1) so(1) gay(1) | 5 | 0:D6 4:F#5 |
| tag2 | v-tag 2 | Jeff is gay so gay | Jeff(1) is(1) gay(1) so(1) gay(1) | 5 | 0:B5 3:B5 6:D6 9:D6 12:B5 |
| tag3 | v-tag 3 | Gay gay gay gay | Gay(1) gay(1) gay(1) gay(1) | 4 | 0:D6 |
| F0 | v-F 0 | Jeff is gay. So gay | Jeff(1) is(1) gay(1) So(1) gay(1) | 5 | 0:G5 2:G5 4:C6 8:G5 10:E5 |
| F1 | v-F 1 | Fun for all hey | Fun(1) for(1) all(1) hey(1) | 4 | 0:B5 2:B5 4:D6 8:D6 10:G5 |
| B6 | v-F 2 | Jeff is gay so gay | Jeff(1) is(1) gay(1) so(1) gay(1) | 5 | 0:A5 2:A5 4:D6 8:D6 10:F#5 |
| B7 | v-F 3 | Gay gay gay gay | Gay(1) gay(1) gay(1) gay(1) | 4 | 0:G5 3:B5 6:D6 9:D6 |

## Chorus on the beat grid

`v-B` is eight bars of four two-bar lines. `sound.gd` plays one clip every
other bar; each syllable's vowel is anchored to a beat.

| Beat | Step | B0 | B1 | B2 | B3 |
|---|---|---|---|---|---|
| 1 | 0 | G5 | A5 | G5 | A5 |
| 2 | 4 | C6 | C6 | C6 | D6 |
| 3 | 8 | G5 | B5 | G5 | D6 |
| 4 | 12 | E5 | A5 | E5 | F#5 |
| 5 | 16 | B5 | A5 | B5 | G5 |
| 6 | 20 | ┬╖ | ┬╖ | ┬╖ | B5 |
| 7 | 24 | ┬╖ | ┬╖ | ┬╖ | D6 |
| 8 | 28 | ┬╖ | ┬╖ | ┬╖ | ┬╖ |

Words per line:
- **B0**: Jeff ┬╖ is ┬╖ gay ┬╖ so ┬╖ gay
- **B1**: Jeff ┬╖ is ┬╖ gay ┬╖ so ┬╖ gay
- **B2**: Jeff ┬╖ is ┬╖ gay ┬╖ so ┬╖ gay
- **B3**: Gay ┬╖ gay ┬╖ gay ┬╖ gay ┬╖ Jeff's ┬╖ so ┬╖ gay

`B4`ΓÇô`B7` are no longer triggered (the old one-bar chorus clips).
