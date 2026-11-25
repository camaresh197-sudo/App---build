#!/usr/bin/env python3
"""Put a Piper voice ON the victory song: speech -> singing via WORLD.

For each sung lyric clip in the vox bank (audio/vox/<id>.ogg, ids from
data/data_vox.json, words from data/data_lyrics.json "victory_vocals"):

  1. Analyze the ORIGINAL clip with WORLD -> its F0 contour (the melody,
     vibrato included) and its duration.
  2. Synthesize the clip's lyric text with Piper (the chosen voice).
  3. Analyze the Piper speech with WORLD -> spectral envelope + aperiodicity.
  4. Time-warp the Piper speech frames to the clip's duration, then replace
     its F0 with the clip's melody contour. Same mouth, new tune.
  5. WORLD resynthesize -> normalize -> 44.1 kHz mono Ogg, same name.

The original clips are copied to tools/vox_backup/originals/ once; pass
--restore to put them back. --force regenerates; otherwise clips that
already carry a Ryan marker are skipped.

Usage:
    python piper_sing.py [--voice en_US-ryan-high] [--force] [--restore] [--dry-run]

--voice is one model by default. Comma-separated voices render one take per
model and mix them into the clip, but independently-spoken takes smear like a
chorus, so prefer a single model unless you want that effect.
"""

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
import wave
import zlib
from pathlib import Path

import numpy as np
import pyworld
import soundfile as sf
from piper.config import SynthesisConfig

TOOLS = Path(__file__).resolve().parent
ROOT = TOOLS.parent
HULA = ROOT / "godot" / "hula"
VOX = HULA / "audio" / "vox"
LYRICS = HULA / "data" / "data_lyrics.json"
DATA_VOX = HULA / "data" / "data_vox.json"
DATA_VICTORY = HULA / "data" / "data_victory.json"
MODELS = TOOLS / "models"
CACHE = TOOLS / ".cache" / "speech"
BACKUP = TOOLS / "vox_backup" / "originals"

sys.path.insert(0, str(TOOLS))
sys.path.insert(0, str(TOOLS / "pronounce"))
import piper_gen  # noqa: E402

FS = 22050          # analysis rate (the medium/high models are 22050; low is 16 kHz and ffmpeg-resampled)
FRAME_MS = 5.0      # WORLD frame period
OGG_RATE = 44100    # the bank ships 44.1 kHz mono vorbis
VE = 0.105          # victory step length (sound.gd), 16 steps/bar
# The grid melodies in data_victory.json are written two octaves above the band's key.
# The original bank clips (B4, B5) are already in the key, so only grid melodies shift.
OCTAVE_SHIFT = -24
# Grid clips synthesize Piper SLOW (length_scale) so vowels are natively long: the warp
# then mostly COMPRESSES onto the grid, which is artifact-free, instead of stretching a
# short word into a long hold (that is what garbled the held 'gay's).
GRID_LS = 2.6
# Per-line render-speed override (D0 test: the smeared "isss"/"luhimp" may come from
# the 2.6x-slow render elongating fricatives before the warp; natural speed keeps them).
LS_BY_LINE = {"D0": 1.0}

# Pronunciation table. data_phonics.json is the source of truth and is read on
# first render; these dicts are only fallbacks used while building that file.
SAY = {}                         # display spelling -> text handed to Piper
PRON = {}                        # display spelling -> what the sheet shows
PHONICS = HULA / "data" / "data_phonics.json"
_PHONICS = None


def phonics() -> dict:
    """Read data_phonics.json once per process (the engine's word table)."""
    global _PHONICS
    if _PHONICS is None:
        if PHONICS.exists():
            _PHONICS = json.loads(PHONICS.read_text(encoding="utf-8")).get("words", {})
        else:
            _PHONICS = {}
    return _PHONICS


def spoken(text: str) -> str:
    table = phonics()

    def swap(m):
        w = m.group(0)
        entry = table.get(w.lower())
        if entry and entry.get("say"):
            return entry["say"]
        return SAY.get(w.lower(), w)

    return re.sub(r"[A-Za-z']+", swap, text)


def words_of(text: str) -> list:
    return re.findall(r"[A-Za-z']+", text)

# Chorus phrases are two bars each: bars 0-1, 2-3, 4-5, 6-7 of v-B.
# "Jeff is gay so gay" as sung in the reference recording (Voice_Recorder_14): word starts about
# 0.27 s apart, and the last word is short (about 0.35 s), with no hold.
GAY_WORD = 0.27
GAY_LAST = 0.35
CHORUS_GRID = {"B0": ("v-B", 0, 2, 7.6, GAY_WORD, None, [], [], {'keep_last_pitch': True}),
               "B1": ("v-B", 2, 2, 7.6, GAY_WORD, None, [], [], {'keep_last_pitch': True}),
               "B2": ("v-B", 4, 2, 7.6, GAY_WORD, None, [], [], {'keep_last_pitch': True}),
               "B3": ("v-B", 6, 2, 7.6, 0.0, None, [], [], {'keep_last_pitch': True})}

# Verse 1 phrases are also two bars each: bars 0-1, 2-3, 4-5, 6-7 of v-A.
CHORUS_GRID.update({"A0": ("v-A", 0, 2, 7.6, 0.0, None, [], [], {'keep_last_pitch': True}), "A2": ("v-A", 2, 2, 7.6),
                    "A4": ("v-A", 4, 2, 7.6, 0.0, None, [[1, 2]], [], {'keep_first_pitch': True, 'keep_last_pitch': True, 'no_release': True}),
                    "A6": ("v-A", 6, 2, 7.6, 0.0, None, [[0, 1]])})

# Verse 2 phrases: two bars each (v-C). Verse 3 (new, 2026-11-23, user lyrics)
# sits between the second chorus and the finale, sung to the same verse tune.
CHORUS_GRID.update({"D0": ("v-D", 0, 2, 7.6),
                    "D2": ("v-D", 2, 2, 7.6), "D4": ("v-D", 4, 2, 7.6), "D6": ("v-D", 6, 2, 7.6),
                    "C0": ("v-C", 0, 2, 7.6), "C2": ("v-C", 2, 2, 7.6),
                    "C4": ("v-C", 4, 2, 7.6), "C6": ("v-C", 6, 2, 7.6),
                    "tag0": ("v-tag", 0, 2, 0.0, GAY_WORD), "tag2": ("v-tag", 2, 2, 0.0, GAY_WORD),
                    "F0": ("v-F", 0, 2, 7.6, GAY_WORD), "B6": ("v-F", 2, 2, 7.6, GAY_WORD)})


# Word timing edited in the game (secret menu, TIMING tab) and copied to tools/retime.py.
# A line with "onsets" in data_word_timing.json gets explicit word times; others keep the grid above.
WORD_TIMING = ROOT / "godot" / "hula" / "data" / "data_word_timing.json"
WORD_LINES = {}
if WORD_TIMING.exists():
    WORD_LINES = json.loads(WORD_TIMING.read_text(encoding="utf-8")).get("lines", {})
    for _id, _line in WORD_LINES.items():
        if _line.get("onsets"):
            _old = CHORUS_GRID.get(_id, (_line["section"], int(_line["bar"]), int(_line["bars"])))
            _hold = _old[3] if len(_old) > 3 else 0.0
            _word = _old[4] if len(_old) > 4 else 0.0
            CHORUS_GRID[_id] = (_line["section"], int(_line["bar"]), int(_line["bars"]), _hold, _word,
                                [float(x) for x in _line["onsets"]],
                                [(int(g[0]), int(g[1])) for g in _line.get("glides", [])],
                                [int(x) for x in _line.get("punches", [])])


def find_ffmpeg() -> str:
    import shutil as sh
    ff = sh.which("ffmpeg")
    if ff:
        return ff
    packages = Path.home() / "AppData" / "Local" / "Microsoft" / "WinGet" / "Packages"
    for p in packages.rglob("ffmpeg.exe"):
        return str(p)
    raise FileNotFoundError("ffmpeg not found; run: winget install ffmpeg")


def run_ffmpeg(ff, args):
    r = subprocess.run([ff, "-y", *args], capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"ffmpeg failed:\n{r.stderr[-600:]}")


def load_wav_mono(path: Path, rate: int) -> np.ndarray:
    """Decode any audio file to float mono at `rate` via ffmpeg."""
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td) / "a.wav"
        run_ffmpeg(find_ffmpeg(), ["-i", str(path), "-ar", str(rate), "-ac", "1",
                                   "-c:a", "pcm_s16le", str(tmp)])
        with wave.open(str(tmp)) as w:
            data = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16)
    return (data.astype(np.float64) + 0.5) / 32767.5


def save_ogg(path: Path, samples: np.ndarray, rate: int) -> None:
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td) / "a.wav"
        x = np.clip(samples, -1.0, 1.0)
        pcm = (x * 32767.0).astype(np.int16)
        with wave.open(str(tmp), "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(rate)
            w.writeframes(pcm.tobytes())
        run_ffmpeg(find_ffmpeg(), ["-i", str(tmp), "-ar", str(OGG_RATE), "-ac", "1",
                                   "-c:a", "libvorbis", "-q:a", "4", str(path)])


def analyze(x: np.ndarray):
    """WORLD analysis -> (f0, sp, ap)."""
    f0, t = pyworld.harvest(x, FS, frame_period=FRAME_MS)
    sp = pyworld.cheaptrick(x, f0, t, FS)
    ap = pyworld.d4c(x, f0, t, FS)
    return f0, sp, ap


def warp_frames(mat: np.ndarray, n_out: int) -> np.ndarray:
    """Resample along the frame axis (columns are kept)."""
    n_in = mat.shape[0]
    if n_in == n_out:
        return mat
    src = np.linspace(0.0, n_in - 1.0, n_out)
    idx = np.floor(src).astype(int)
    frac = (src - idx)[..., None]
    idx2 = np.minimum(idx + 1, n_in - 1)
    return mat[idx] * (1.0 - frac) + mat[idx2] * frac


def fill_gaps(f0: np.ndarray) -> np.ndarray:
    """Linearly interpolate short unvoiced holes in a melody contour."""
    y = f0.astype(float).copy()
    voiced = y > 0
    if voiced.all() or not voiced.any():
        return y
    x = np.arange(len(y))
    y[~voiced] = np.interp(x[~voiced], x[voiced], y[voiced])
    # only fill small holes (<= 12 frames = 60 ms); long gaps stay unvoiced
    runs = []
    start = None
    for i, v in enumerate(voiced):
        if not v and start is None:
            start = i
        elif v and start is not None:
            runs.append((start, i))
            start = None
    if start is not None:
        runs.append((start, len(voiced)))
    for a, b in runs:
        if b - a > 12:
            # rebuild the hole from the original (unfilled) values -> 0
            y[a:b] = 0.0
            y[a:b] = f0[a:b]
    return y


def shape_melody(f0: np.ndarray, win: int = 9, max_step: float = 50.0, max_dev: float = 250.0,
                 vib: float = 0.65) -> np.ndarray:
    """Shape a borrowed melody so it can be imposed on a different phoneme layout.

    The original contour is smooth on its own vowels; dropped onto another
    singer's voiced runs it arrives at arbitrary phase, so vibrato swings and
    note leaps turn into instant 300-600 cent steps that sound like cracks.
    Median-filter in cents (kills octave glitches, keeps slow vibrato), scale
    the vibrato detail down (it arrives at the wrong phase on the new vowels,
    where full depth reads as warble), then cap the per-frame slope while
    staying anchored to the real melody (real leaps still happen, spread over a
    few frames instead of one).
    """
    voiced = f0 > 0
    out = f0.astype(float).copy()
    if int(voiced.sum()) < win:
        return out
    x = np.arange(len(f0))
    curve = np.interp(x, x[voiced], f0[voiced])           # continuous Hz curve over the gaps
    ref = max(float(np.median(f0[voiced])), 1e-6)
    cents = 1200.0 * np.log2(np.maximum(curve, 1e-6) / ref)

    def medfilt(v: np.ndarray, w: int) -> np.ndarray:
        r = w // 2
        pad = np.pad(v, r, mode="edge")
        return np.array([np.median(pad[i:i + w]) for i in range(len(v))])

    cents = medfilt(cents, win)                           # octave glitches out
    slow = medfilt(cents, 41)                             # the note line (~205 ms)
    cents = slow + (cents - slow) * vib                   # vibrato at reduced depth
    target = cents.copy()
    for i in range(1, len(cents)):
        step = float(np.clip(cents[i] - cents[i - 1], -max_step, max_step))
        cents[i] = min(max(cents[i - 1] + step, target[i] - max_dev), target[i] + max_dev)
    out = ref * np.power(2.0, cents / 1200.0)
    out[~voiced] = 0.0                                    # unvoiced stays unvoiced
    return out


def runs_of(mask: np.ndarray, min_len: int = 5) -> list:
    """Contiguous True runs as (start, end) frame pairs, min_len or longer."""
    idx = np.where(mask)[0]
    if len(idx) == 0:
        return []
    br = np.where(np.diff(idx) > 1)[0]
    starts = np.concatenate(([idx[0]], idx[br + 1]))
    ends = np.concatenate((idx[br], [idx[-1]]))
    return [(int(s), int(e) + 1) for s, e in zip(starts, ends) if e + 1 - s >= min_len]


def equalize_runs(orig: list, ryan: list) -> list:
    """Merge the smallest-gap runs on the longer side until both lists match.

    The song holds few long vowels (legato); speech has one short run per
    syllable. Merging Ryan's adjacent runs maps two spoken syllables onto one
    held note, which is what the song does. Returns [orig, ryan] or [None, None]
    if they refuse to match.
    """
    a, b = list(orig), list(ryan)
    guard = 0
    while len(a) != len(b):
        longer = a if len(a) > len(b) else b
        if len(longer) < 2:
            return [None, None]
        gaps = [longer[i + 1][0] - longer[i][1] for i in range(len(longer) - 1)]
        i = int(np.argmin(gaps))
        longer[i] = (longer[i][0], longer[i + 1][1])
        del longer[i + 1]
        guard += 1
        if guard > 64:
            return [None, None]
    return [a, b]


def melody_segments(cents: np.ndarray, voiced: np.ndarray, slope_max: float = 12.0,
                    fit_max: float = 4.0, min_plateau: int = 5) -> list:
    """Classify a shaped melody into held notes and slides.

    A plateau is a voiced stretch whose smoothed slope is small AND whose linear
    fit is near-flat (the fit rejects slow slides that a slope window can hide).
    Everything else voiced is a glide and keeps the melody's own contour - which
    is what keeps every pitch in tune: notes come from the performance, never
    from an average of a slide.
    Returns (start, end, kind, note_cents); every voiced frame is covered.
    """
    n = len(cents)
    x = np.arange(n)
    xv = x[voiced]
    filled = np.interp(x, xv, cents[voiced])
    slope = np.convolve(np.gradient(filled), np.ones(7) / 7.0, mode="same")
    is_flat = voiced & (np.abs(slope) <= slope_max)
    segs = []
    i = 0
    while i < n:
        if not voiced[i]:
            i += 1
            continue
        flat = is_flat[i]
        j = i + 1
        while j < n and voiced[j] and is_flat[j] == flat:
            j += 1
        if flat and j - i >= min_plateau:
            fit = np.polyfit(x[i:j], cents[i:j], 1)[0]
            if abs(fit) <= fit_max:
                segs.append((i, j, "plateau", float(np.median(cents[i:j]))))
                i = j
                continue
        segs.append((i, j, "glide", 0.0))
        i = j
    return segs


def warp_along(mat: np.ndarray, src_idx: np.ndarray) -> np.ndarray:
    """Resample along the frame axis following an explicit fractional index map."""
    i = np.floor(src_idx).astype(int)
    frac = (src_idx - i)[..., None]
    j = np.minimum(i + 1, mat.shape[0] - 1)
    return mat[i] * (1.0 - frac) + mat[j] * frac


def syllable_count(text: str) -> int:
    """Rough English syllable count, enough for the lyric lines we sing."""
    n = 0
    for w in re.findall(r"[A-Za-z']+", text):
        w = w.lower()
        w = re.sub(r"'s$", "", w)                   # possessive: Jake's -> jake
        w = w.replace("'", "")                       # I'm -> im, he'll -> hell
        # magic e: vowel + consonant + e (+ consonants) -> the e is silent
        w = re.sub(r"([aeiouy])([^aeiouy])e([^aeiouy]*)$", r"\1\2\3", w)
        groups = re.findall(r"[aeiouy]+", w)
        n += max(1, len(groups))
    return n


def grid_melody(section: str, start_bar: int, n_bars: int, syllables: int = 0, hold_to: float = 0.0, word_secs: float = 0.0,
                onsets=None):
    """Target notes from the song data, one syllable per beat.

    Returns (f0, spans) where spans are (start_frame, end_frame, hz) per
    syllable. The melody is read from data_victory.json, so the words land on
    the grid the sequencer actually plays rather than on the old take's
    phrasing. `LEAD` frames of consonant room sits in front of the first beat;
    data_vox.json's 0.15 s lead-in puts that consonant before the downbeat.
    """
    vic = json.loads(DATA_VICTORY.read_text(encoding="utf-8"))
    rows = [b for b in vic if b[6] == section and start_bar <= int(b[7]) < start_bar + n_bars]
    rows.sort(key=lambda b: int(b[7]))
    steps = []
    for b in rows:
        steps.extend(int(x) for x in b[3])
    steps = steps[:n_bars * 16]
    step_frames = VE * 1000.0 / FRAME_MS
    n = int(round(n_bars * 16 * step_frames))

    pitch = np.zeros(n_bars * 16)
    cur = 0.0
    for s, m in enumerate(steps):
        if m > 0:
            cur = 440.0 * np.power(2.0, (m - 69) / 12.0)
        pitch[s] = cur

    k = max(1, syllables or n_bars * 4)
    lead = 30                                        # 150 ms, matches data_vox lead-in
    if onsets:
        # explicit word times from the TIMING tab (seconds from the first word)
        k = len(onsets)
        ons = [lead + float(o) * 1000.0 / FRAME_MS for o in onsets]
        steps_at = [min(int(o / step_frames), n_bars * 16 - 1) for o in ons]
    elif word_secs > 0.0:
        # free spacing (a reference phrasing): one word every word_secs, not tied to the step grid
        wf = word_secs * 1000.0 / FRAME_MS
        ons = [lead + i * wf for i in range(k)]
        steps_at = [min(int(o / step_frames), n_bars * 16 - 1) for o in ons]
    elif k <= n_bars * 4:
        ons = [min(lead + b * 4 * step_frames, n - 1) for b in range(k)]
        steps_at = [b * 4 for b in range(k)]
    else:
        # more words than beats (e.g. five words in a one-bar tag): keep every vowel on the
        # step grid, after the same 150 ms lead-in, and spread them across the bar. The old
        # even spread over the whole clip started word 1 at 0 s (150 ms early against the
        # data_vox lead-in) and put the last word on the next bar's downbeat.
        steps_at = [min(int(round(i * n_bars * 16 / k)), n_bars * 16 - 1) for i in range(k)]
        ons = [min(lead + s * step_frames, n - 1) for s in steps_at]
    onsets = [int(round(o)) for o in ons]

    spans = []
    for i, o in enumerate(onsets):
        e = onsets[i + 1] if i + 1 < len(onsets) else n
        if i + 1 == len(onsets) and word_secs > 0.0:
            e = min(n, o + int(round(GAY_LAST * 1000.0 / FRAME_MS)))   # short last word, then rest
        if i + 1 == len(onsets) and hold_to > 0.0:
            # the last word sustains until `hold_to` beats into the clip (its vowel is stretched over the hold)
            e = min(n, int(round(lead + hold_to * 4 * step_frames)))
        hz = pitch[steps_at[i]] * 2.0 ** (OCTAVE_SHIFT / 12.0)
        if hz <= 0:
            hz = pitch[max(0, steps_at[i] - 1)]
        spans.append((o, e, float(hz)))
    f0 = np.zeros(n)
    for (a, b, hz) in spans:
        f0[a:b] = hz
    return f0, spans


VOWELS = set("aeiouyæɑɒɔəɚɛɜɪʊʌɐɤɯɵɞɘøœʏɨʉ")
_ALIGNED = {}


# Observed on this machine: the espeak binding returns 'Ëˆ' for ˈ (U+02C8),
# 'É”' for ɔ (U+0254) and 'Éª' for ɪ (U+026A). The mojibake is not in the
# voice's id map, so Piper drops the phoneme (wrong pronunciation: "lost" -> "lst",
# "dick" -> "tick") and the alignment reconstruction fails, which silently pushes
# every clip through the abandoned runs-mapping that garbles words.
MOJIBAKE = {"Ëˆ": "ˈ", "É”": "ɔ", "Éª": "ɪ"}


def _fix_mojibake(p: str, id_map) -> str:
    """Repair phonemizer output that arrived mangled on this machine."""
    if p in id_map:
        return p
    fixed = MOJIBAKE.get(p)
    if fixed is None:
        try:
            cand = p.encode("latin-1").decode("utf-8")
        except (UnicodeEncodeError, UnicodeDecodeError):
            return p
        fixed = cand
    return fixed if fixed in id_map else p


def aligned_voice(name):
    """Piper voice loaded so each call can return phoneme/audio alignments."""
    from piper import PiperVoice
    if name not in _ALIGNED:
        _ALIGNED[name] = PiperVoice.load(str(MODELS / f"{name}.onnx"),
                                         config_path=str(MODELS / f"{name}.onnx.json"),
                                         use_cuda=False, include_alignments=True)
        from pronounce.engine import attach_lexicon
        attach_lexicon(_ALIGNED[name])
        v = _ALIGNED[name]
        _phm = v.phonemize

        def _fixed_phonemize(text, _phm=_phm, _v=v):
            out = []
            for sent in _phm(text):
                out.append([_fix_mojibake(p, _v.config.phoneme_id_map) for p in sent])
            return out

        v.phonemize = _fixed_phonemize
    return _ALIGNED[name]


def _fit(x: np.ndarray, sr: int) -> np.ndarray:
    """Resample to the WORLD analysis rate if the voice shipped another one."""
    if sr == FS:
        return x
    n = int(len(x) * FS / sr)
    return np.interp(np.linspace(0, len(x) - 1, n), np.arange(len(x)), x)


def _key(text: str, voice: str) -> str:
    return hashlib.sha1(f"{voice}|{text}".encode("utf-8")).hexdigest()[:20]


def synth_audio(text: str, voice: str, use_cache: bool = True):
    """Piper speech as (mono float at FS), read from the on-disk cache when present."""
    CACHE.mkdir(parents=True, exist_ok=True)
    wav = CACHE / f"{voice}_{_key(text, voice)}.wav"
    if use_cache and wav.exists():
        x, sr = sf.read(str(wav), dtype="float64", always_2d=True)
        return _fit(x[:, 0], sr), FS
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td) / "a.wav"
        piper_gen.synthesize(text, voice, str(tmp), str(MODELS))
        x, sr = sf.read(str(tmp), dtype="float64", always_2d=True)
        if use_cache:
            shutil.copy2(tmp, wav)
    return _fit(x[:, 0], sr), FS


def synth_aligned(text: str, voice: str, use_cache: bool = True, length_scale: float = 1.0):
    """Synthesize and return (audio, [(phoneme, start_sample, end_sample)]).

    The audio and its alignment are cached together; a second call reads them
    from disk instead of running Piper again. `length_scale` slows Piper down
    (more frames for the same words): sung clips are warped onto the grid
    anyway, so a slower source only means smoother warps, never longer clips.
    """
    CACHE.mkdir(parents=True, exist_ok=True)
    k = _key(text, f"{voice}#{length_scale:.2f}")
    wav = CACHE / f"al_{voice}_{k}.wav"
    js = CACHE / f"al_{voice}_{k}.json"
    if use_cache and wav.exists() and js.exists():
        x, sr = sf.read(str(wav), dtype="float64", always_2d=True)
        phonemes = [tuple(p) for p in json.loads(js.read_text(encoding="utf-8"))]
        return _fit(x[:, 0], sr), phonemes
    cfg = SynthesisConfig(length_scale=length_scale) if length_scale != 1.0 else None
    chunks = list(aligned_voice(voice).synthesize(text, syn_config=cfg, include_alignments=True))
    audio = np.concatenate([np.asarray(c.audio_float_array, dtype=np.float64) for c in chunks])
    phonemes, off = [], 0
    for c in chunks:
        for a in (c.phoneme_alignments or []):
            phonemes.append((str(a.phoneme), int(off), int(off + a.num_samples)))
            off += int(a.num_samples)
    if use_cache:
        sf.write(str(wav), audio, chunks[0].sample_rate)
        js.write_text(json.dumps(phonemes, ensure_ascii=False), encoding="utf-8")
    return audio, phonemes


def word_spans(phonemes: list) -> list:
    """One span per word (space-separated), from the first to the last phoneme."""
    out, cur = [], None
    for (p, a, b) in phonemes:
        if p == " ":
            if cur is not None:
                out.append((cur[0], cur[1])); cur = None
        elif cur is None:
            cur = [a, b]
        else:
            cur[1] = b
    if cur is not None:
        out.append((cur[0], cur[1]))
    return out


def nuclei_spans(phonemes: list) -> list:
    """Vowel nuclei as (start_sample, end_sample); consecutive vowels are one."""
    out, cur = [], None
    for (p, a, b) in phonemes:
        if p and p[0] in VOWELS:
            if cur is None:
                cur = [a, b]
            else:
                cur[1] = b
        elif cur is not None:
            out.append((cur[0], cur[1]))
            cur = None
    if cur is not None:
        out.append((cur[0], cur[1]))
    return out


PHON_CACHE = CACHE / "phon"
SONORANT = set("aeiouɪʊɛæʌəɜɔɐɑɒɘɚɞɨʉɯɵɶʏmnŋlrɹɾɻɽjw")
VOICED_OBSTRUENT = set("bdɡvðzʒ")
PHON_BANK = {}
_bank_file = HULA / "data" / "data_phon_bank.json"
if _bank_file.exists():
    PHON_BANK = json.loads(_bank_file.read_text(encoding="utf-8")).get("phones", {})


def _chars(ph) -> str:
    if isinstance(ph, dict):
        return str(ph.get("m", "")) + str(ph.get("p", "")) + str(ph.get("x", ""))
    return str(ph)


def phone_ids(pmap: dict, words: list):
    """Piper's id layout: ^ _ p1 _ p2 _ ... pn _ $  (a pad after every phoneme, as the voice was trained).

    `words` is a list of words, each a list of phones (strings or dicts {"p", "m" stress mark
    before, "x" length mark after}). Words are separated by the space token, like espeak's output.
    Leaving the pads out makes the model babble at about half the length: the old "gibberish".
    Returns (ids, spans); spans[w][j] is the (first, last+1) id index of phone j of word w.
    """
    pad = pmap["_"][0] if "_" in pmap else 0
    ids = list(pmap.get("^", []))
    ids.append(pad)
    spans = []
    for wi, word in enumerate(words):
        if wi > 0 and " " in pmap:
            ids.append(pmap[" "][0])
            ids.append(pad)
        ws = []
        for ph in word:
            a = len(ids)
            for ch in _chars(ph):
                if ch in pmap:
                    ids.append(pmap[ch][0])
                    ids.append(pad)
            ws.append((a, len(ids)))
        spans.append(ws)
    ids.extend(pmap.get("$", []))
    return ids, spans


def line_audio(voice: str, words: list, use_cache: bool = True):
    """A whole line's phones in ONE pass, so words keep their context (stress, linking, rhythm).

    Returns (audio at FS, bounds) with bounds[w][j] = (start, end) samples of phone j of word w,
    taken from the model's own per-id lengths (Piper alignments), not from guessed lengths.
    """
    PHON_CACHE.mkdir(parents=True, exist_ok=True)
    tag = " | ".join(" ".join(_chars(ph) for ph in w) for w in words)
    base = PHON_CACHE / f"{voice}_l3_{_key('line|' + tag, voice)}"
    wav, js = base.with_suffix(".wav"), base.with_suffix(".json")
    if use_cache and wav.exists() and js.exists():
        x, sr = sf.read(str(wav), dtype="float64")
        return _fit(x, sr), [[tuple(t) for t in w] for w in json.loads(js.read_text())]
    model = aligned_voice(voice)
    ids, spans = phone_ids(model.config.phoneme_id_map, words)
    if len(ids) < 4:
        return np.zeros(0), [[] for _ in words]
    res = model.phoneme_ids_to_audio(ids, include_alignments=True)
    audio, counts = res if isinstance(res, tuple) else (res, None)
    x = np.asarray(audio, dtype=np.float64)
    sr = model.config.sample_rate
    scale = FS / sr
    flat = [t for w in spans for t in w]
    if counts is not None and len(counts) == len(ids):
        cum = np.concatenate([[0], np.cumsum(np.asarray(counts, dtype=np.int64))])
        sec = lambda t: (float(cum[t[0]]) * scale, float(cum[t[1]]) * scale)
    else:  # a model without durations: even split of the speech
        n = len(x) * scale
        k = {t: i for i, t in enumerate(flat)}
        sec = lambda t: (n * k[t] / len(flat), n * (k[t] + 1) / len(flat))
    bounds = [[sec(t) for t in w] for w in spans]
    x = _fit(x, sr)
    off = 0
    if x.size:
        loud = np.abs(x) > 0.002
        if loud.any():
            a = int(np.argmax(loud))
            b = int(len(loud) - np.argmax(loud[::-1]))
            tail = int(0.005 * FS)
            off = max(0, a - tail)
            x = x[off:min(len(x), b + tail)]
    n = float(len(x))
    bounds = [[(max(0.0, lo - off), max(0.0, min(hi - off, n))) for lo, hi in w] for w in bounds]
    if use_cache:
        sf.write(str(wav), x, FS)
        js.write_text(json.dumps(bounds), encoding="utf-8")
    return x, bounds


def _add_at(out: np.ndarray, y: np.ndarray, s: int, fade: int) -> None:
    n = len(out)
    if s >= n or y.size == 0:
        return
    if s < 0:
        y = y[-s:]
        s = 0
    y = y[:min(len(y), n - s)]
    k = min(fade, len(y), s)
    if k > 0:
        w = np.linspace(0.0, 1.0, k)
        out[s:s + k] = out[s:s + k] * (1.0 - w) + y[:k] * w
        s += k
        y = y[k:]
    out[s:s + len(y)] += y


def render_phones(line: dict, grid, voice: str, use_cache: bool = True) -> np.ndarray:
    """Sing the edited IPA: the whole line is synthesized in one pass (Piper pad layout, stress kept),
    then each phone's real span in that render is warped to its edited length and put at its word's onset.

    One pass keeps the model's coarticulation and rhythm; the alignments give true phone boundaries,
    so a length edit moves a real phone instead of an arbitrary slice.
    """
    bars = int(grid[2])
    lead = 30
    _mel, spans = grid_melody(grid[0], grid[1], bars, syllables=len(line.get("words", [])),
                              hold_to=grid[3] if len(grid) > 3 else 0.0,
                              word_secs=grid[4] if len(grid) > 4 else 0.0,
                              onsets=line.get("onsets"))
    nc = int(round(bars * 16 * (VE * 1000.0 / FRAME_MS)))
    nsamp = int(round(nc * FS * FRAME_MS / 1000.0))
    out = np.zeros(nsamp, dtype=np.float64)
    onsets = line.get("onsets", [])
    words = line.get("phones", [])
    x, bounds = line_audio(voice, words, use_cache)
    if x.size < 32:
        return out
    f0, tt = pyworld.harvest(x, FS, frame_period=FRAME_MS)
    if len(f0) < 3:
        return out
    sp = pyworld.cheaptrick(x, f0, tt, FS)
    ap = pyworld.d4c(x, f0, tt, FS)
    nr = len(f0)
    per_frame = FS * FRAME_MS / 1000.0
    for wi, phs in enumerate(words):
        hz = float(spans[wi][2]) if wi < len(spans) else 220.0
        seq = [str(ph.get("p", "ə")) for ph in phs]
        targets = [max(2, int(round(float(ph.get("d", 0.12)) * 1000.0 / FRAME_MS))) for ph in phs]
        t_cum = 0
        pieces_sp, pieces_ap, pieces_f0 = [], [], []
        for j, p in enumerate(seq):
            lo, hi = bounds[wi][j] if wi < len(bounds) and j < len(bounds[wi]) else (0.0, 0.0)
            s0 = min(nr - 2, max(0, int(round(lo / per_frame))))
            s1 = max(s0 + 1, min(int(round(hi / per_frame)), nr - 1))
            d = targets[j]
            idx = np.linspace(float(s0), float(s1), d)
            pieces_sp.append(warp_along(sp[s0:s1 + 1], idx - s0))
            pieces_ap.append(warp_along(ap[s0:s1 + 1], idx - s0))
            fsrc = warp_along(f0[s0:s1 + 1].reshape(-1, 1), idx - s0).ravel()
            carry = p in SONORANT or p in VOICED_OBSTRUENT
            pieces_f0.append(np.where((fsrc > 0.0) & carry, hz, 0.0))
            t_cum += d
        if not pieces_sp:
            continue
        sp2 = np.concatenate(pieces_sp, axis=0)
        ap2 = np.concatenate(pieces_ap, axis=0)
        f0_new = np.concatenate(pieces_f0)
        m = min(len(sp2), len(ap2), len(f0_new), t_cum)
        y = pyworld.synthesize(f0_new[:m], sp2[:m], ap2[:m], FS, frame_period=FRAME_MS)
        t = lead + (float(onsets[wi]) * 1000.0 / FRAME_MS if wi < len(onsets) else 0.0)
        _add_at(out, y, int(round(t * FS * FRAME_MS / 1000.0)), int(0.008 * FS))
    peak = float(np.max(np.abs(out))) or 1.0
    return out / peak * 0.89


MASTER = "loudness"   # "loudness" (default, Wren v11) or "peak" (the old peak-to-0.89 normalise)
MASTER_TARGET_DB = -17.0   # gated RMS target: the median shipped clip sits near here
MASTER_CEILING = 0.89      # peak ceiling, as before
MASTER_GATE_DB = -45.0     # frames quieter than this do not count toward the RMS
MASTER_HP_HZ = 60.0        # removes sub-60 Hz rumble found in the gaps (W026); voice fundamentals sit well above


def master_level(y: np.ndarray, rate: int = FS) -> np.ndarray:
    """Match loudness between clips instead of peak-normalising each one.

    Peak normalising put every shipped clip at about -1 dB, so average loudness
    ranged 9 dB across clips (RMS -12.8 to -21.6 dB). This measures gated RMS on
    frames above MASTER_GATE_DB, applies a gain to hit MASTER_TARGET_DB, and caps
    the gain so the peak stays under MASTER_CEILING (no clipping). A high-pass
    at MASTER_HP_HZ removes low rumble that the gaps carried.
    """
    from scipy.signal import butter, sosfilt
    y = np.asarray(y, dtype=np.float64)
    if MASTER_HP_HZ > 0 and len(y) > 64:
        sos = butter(2, MASTER_HP_HZ, btype="highpass", fs=rate, output="sos")
        y = sosfilt(sos, y)
    fr = max(64, int(0.02 * rate))
    n = len(y) // fr
    if n:
        rms = np.sqrt(np.mean(y[: n * fr].reshape(n, fr) ** 2, axis=1))
        db = 20 * np.log10(rms + 1e-12)
        act = rms[db > MASTER_GATE_DB]
        level = float(np.sqrt(np.mean(act ** 2))) if act.size else float(np.sqrt(np.mean(y ** 2)))
    else:
        level = float(np.sqrt(np.mean(y ** 2)))
    if level <= 1e-9:
        return y
    gain = 10 ** (MASTER_TARGET_DB / 20) / level
    peak = float(np.max(np.abs(y))) or 1.0
    gain = min(gain, MASTER_CEILING / peak)
    return y * gain


def _declick(y: np.ndarray) -> np.ndarray:
    """Fade in over ~3 ms wherever audio starts after a silent gap.

    The warp can leave short holes inside a word (e.g. before a vowel); the
    voice then pops in at full amplitude ("tiny pop" in A0's 'a -> y').
    """
    thr = 0.02
    gap = int(0.03 * FS)
    fade = max(8, int(0.003 * FS))
    quiet = np.abs(y) < thr
    # runs of quiet of at least `gap`
    d = np.diff(quiet.astype(np.int8))
    ends = np.where(d == -1)[0] + 1          # quiet -> loud
    for i in ends:
        # count backwards over the quiet run
        j = i - gap
        if j >= 0 and quiet[j:i].all():
            f = np.linspace(0.0, 1.0, fade)
            y[i:i + fade] *= f
    return y


def sing_clip(clip_id: str, text: str, voices: list, args_mix_weights, vib: float = 0.65,
              flow: str = "notes", grid=None, use_cache: bool = True) -> dict:
    spans = []
    if grid:
        melody, spans = grid_melody(*grid[:3], syllables=len(words_of(text)), hold_to=grid[3] if len(grid) > 3 else 0.0,
                                    word_secs=grid[4] if len(grid) > 4 else 0.0,
                                    onsets=grid[5] if len(grid) > 5 else None)
        nc = len(melody)
        dur = nc * FRAME_MS / 1000.0
        f0_c = melody.copy()
    else:
        # the melody comes from the ORIGINAL bank clip, not the current one: after
        # a first Ryan pass the file on disk is already sung, so re-running would
        # otherwise borrow its melody from Ryan's render instead of the performance
        src = BACKUP / f"{clip_id}.ogg"
        src = src if src.exists() else VOX / f"{clip_id}.ogg"
        x0 = load_wav_mono(src, FS)
        f0_c, _, _ = analyze(x0)                      # the melody to borrow
        nc = len(f0_c)
        dur = len(x0) / FS
        melody = shape_melody(fill_gaps(f0_c), vib=vib)
    takes = []
    base_hz = 0.0
    line_ph = WORD_LINES.get(clip_id, {}).get("phones") if grid else None
    with tempfile.TemporaryDirectory() as td:
        for i, voice in enumerate(voices):
            if line_ph:
                takes.append(render_phones(WORD_LINES[clip_id], grid, voice, use_cache))
                if base_hz == 0.0:
                    base_hz = 220.0
                continue
            if grid:
                # Grid mode: Piper's phoneme alignments say exactly when each
                # vowel starts. Put every vowel on its beat, keep the consonants
                # in the gaps, and sing one note per syllable.
                audio, phonemes = synth_aligned(spoken(text), voice, use_cache, length_scale=LS_BY_LINE.get(clip_id, GRID_LS))
                f0_r, sp_r, ap_r = analyze(audio)
                nr = len(f0_r)
                nuc = word_spans(phonemes)
                fr = int(FS * FRAME_MS / 1000.0)
                e_src = np.array([np.sqrt((audio[i * fr:(i + 1) * fr] ** 2).mean())
                                  for i in range(len(audio) // fr)]) if len(audio) >= fr else np.zeros(1)
                if len(e_src) > 7:
                    e_src = np.convolve(e_src, np.ones(7) / 7.0, mode="same")
                if len(nuc) == len(spans):
                    # per-word anchors: each word's voiced span maps onto its note span.
                    # (A runs-based flow mapping was tried and garbled words whenever the
                    # singer's run count disagreed with the note count; with legato ramps,
                    # GRID_LS slow rendering and the glide/punch toys, the anchors no longer
                    # stutter, so they are the reliable choice.)
                    vsf0 = nuc[0][0] / FS * 1000.0 / FRAME_MS
                    lead = float(spans[0][0])
                    anchors_src, anchors_out = [0.0, vsf0], [max(0.0, lead - vsf0), lead]
                    for k, (vs, ve) in enumerate(nuc):
                        a, b, _hz = spans[k]
                        L = b - a
                        if k > 0:
                            anchors_src.append(vs / FS * 1000.0 / FRAME_MS)
                            anchors_out.append(float(a))
                        if L >= 60:
                            anchors_src.append(ve / FS * 1000.0 / FRAME_MS)
                            anchors_out.append(float(min(a + 0.93 * L, nc - 1)))
                        else:
                            anchors_src.append(ve / FS * 1000.0 / FRAME_MS)
                            anchors_out.append(float(min(a + 0.85 * (b - a), nc - 1)))
                    anchors_src.append(float(nr))
                    anchors_out.append(float(nc))
                    src_idx = np.interp(np.arange(nc), anchors_out, anchors_src)
                    src_idx = np.clip(src_idx, 0.0, float(nr - 1))
                    sp = warp_along(sp_r, src_idx)
                    ap = warp_along(ap_r, src_idx)
                    f0_rw = warp_along(f0_r.reshape(-1, 1), src_idx).ravel()

                    rng = np.random.default_rng(zlib.crc32(clip_id.encode("utf-8")))
                    phase = float(rng.uniform(0.0, 2.0 * np.pi))
                    prev = 0.0
                    notes = []
                    new_f0 = np.zeros(nc)
                    # "glides" (from data_word_timing): word i ends early, a breath, then the
                    # voice slides into word j's note - flamboyant portamento, e.g. am -> Jeff.
                    glides = grid[6] if len(grid) > 6 else []
                    punches = grid[7] if len(grid) > 7 else []
                    # "rel" (per-line switch): word gi-1 releases 25 ms early so word
                    # gi's consonant gets room, without the punch's pitch accent
                    # (the accent's rise read as a pop through A0's "gay" glide).
                    rels = grid[8].get('rel', []) if len(grid) > 8 and isinstance(grid[8], dict) else []
                    sp2 = list(spans)
                    for gi in rels:
                        if 0 < gi < len(sp2) and sp2[gi - 1][1] == sp2[gi][0]:
                            a_, b_, h_ = sp2[gi - 1]
                            sp2[gi - 1] = (a_, b_ - 5, h_)
                    for (gi, gj) in glides:
                        if gi < len(sp2) and gj < len(sp2):
                            a_i, b_i, h_i = sp2[gi]
                            a_j = sp2[gj][0]
                            cut = a_j - int(0.02 * (1000.0 / FRAME_MS)) - int(0.12 * (1000.0 / FRAME_MS))
                            if cut > a_i + 4:
                                sp2[gi] = (a_i, cut, h_i)
                    for pi in punches:
                        # a punch enters through the consonant: the previous word's vowel
                        # gives up its last 25 ms so the pitch hit lives before the vowel
                        if 0 < pi < len(sp2) and sp2[pi - 1][1] == sp2[pi][0]:
                            a_, b_, h_ = sp2[pi - 1]
                            sp2[pi - 1] = (a_, b_ - 5, h_)
                    flags = grid[8] if len(grid) > 8 else {}
                    for si, (a, b, hz) in enumerate(sp2):
                        L = b - a
                        t = np.arange(L)
                        note = hz * np.power(2.0, float(rng.normal(0.0, 6.0)) / 1200.0)
                        notes.append(note)
                        natural_last = si == len(sp2) - 1 and flags.get('keep_last_pitch')
                        natural_first = si == 0 and flags.get('keep_first_pitch')
                        if (natural_last or natural_first):
                            which = f0_rw[a:b]
                            voiced = np.where(which > 0)[0]
                            if len(voiced) > 8 and float(which[voiced].max()) > 0:
                                ref = float(np.median(which[voiced]))
                                ratio = np.empty(len(which))
                                ratio[voiced] = which[voiced] / ref
                                x_v = voiced.astype(float)
                                ratio = np.interp(np.arange(len(which)), x_v, ratio[voiced])
                                f = note * ratio
                            else:
                                f = np.full(L, note)
                        else:
                            f = np.full(L, note)
                        if prev > 0.0 and not natural_last:
                            # legato: every note change slides from the previous note over
                            # ~20 ms (40 ms into a punch) so syllables float instead of stepping
                            k = min(8 if si in punches else 4, L)
                            cents = 1200.0 * np.log2(note / prev)
                            f[:k] = prev * np.power(2.0, cents * (np.arange(k) + 1) / k / 1200.0)
                        if L >= 24 and not (natural_last or natural_first):
                            rate = float(rng.uniform(4.8, 6.2))
                            depth = (float(rng.uniform(16.0, 26.0)) if L < 60
                                     else float(rng.uniform(28.0, 44.0)) if L < 150
                                     else float(rng.uniform(20.0, 31.0)))
                            ramp = np.clip((t - 0.10 * (1000.0 / FRAME_MS)) / (0.15 * (1000.0 / FRAME_MS)), 0.0, 1.0)
                            if si + 1 in punches:
                                # a punch wants a steady note to hit: taper this span's vibrato
                                # out over its last 60 ms so the F0 is flat entering the hit
                                ramp = ramp * np.clip((L - 1 - t) / 12.0, 0.0, 1.0)
                            if si == len(sp2) - 1 and si in punches:
                                # the melisma is the gesture: steady note into the swoop, no
                                # wobble riding the rise (that is the 'cough')
                                ramp = ramp * np.clip((int(0.55 * L) - t) / 12.0, 0.0, 1.0)
                            f = f * np.power(2.0, depth * np.sin(phase + 2.0 * np.pi * rate * t / (1000.0 / FRAME_MS)) * ramp / 1200.0)
                            phase += 2.0 * np.pi * rate * L / (1000.0 / FRAME_MS)
                        if si == len(sp2) - 1 and si in punches and (grid[3] if len(grid) > 3 else 0.0) > 0.0 and not flags.get('no_melisma'):
                            # 7 syllables over 8 notes: the final word is a two-note melisma -
                            # firm D4, swoop up a minor third, then HOLD the F4 so the gesture
                            # lands before the release (a rise that never lands reads as a cut)
                            k0 = int(0.55 * L)
                            rk = max(4, int(0.25 * L))
                            f[k0:] = note * np.power(2.0, 300.0 / 1200.0)
                            f[k0:k0 + rk] = note * np.power(2.0, 300.0 * ((np.arange(rk) + 1.0) / rk) ** 2 / 1200.0)
                        elif si == 0 and L >= 8:
                            # goofy entrance: the first word scoops up from a third below
                            k = min(6, L // 3)
                            f[:k] = note * np.power(2.0, -250.0 * (1.0 - (np.arange(k) + 1.0) / k) / 1200.0)
                        new_f0[a:b] = f
                        prev = note
                    new_f0[f0_rw <= 0] = 0.0
                    holes, start = [], None
                    for j, hole in enumerate(new_f0 <= 0.0):
                        if hole and start is None:
                            start = j
                        elif not hole and start is not None:
                            holes.append((start, j)); start = None
                    if start is not None:
                        holes.append((start, nc))
                    for (a, b) in holes:
                        if 3 <= b - a <= 16 and a > 0 and b < nc and new_f0[a - 1] > 0 and new_f0[b] > 0:
                            new_f0[a:b] = np.exp(np.linspace(np.log(new_f0[a - 1]),
                                                             np.log(new_f0[b]), b - a))
                    for (gi, gj) in glides:      # the slide itself: last 120 ms before word j
                        if gi < len(sp2) and gj < len(sp2):
                            b_i, h_i = sp2[gi][1], sp2[gi][2]
                            a_j, h_j = sp2[gj][0], sp2[gj][2]
                            gs = a_j - int(0.12 * (1000.0 / FRAME_MS))
                            if b_i < gs and h_i > 0 and h_j > 0:
                                k = np.arange(gs, a_j)
                                new_f0[k] = h_i * np.power(h_j / h_i, (k - gs) / max(1, a_j - gs))
                    for pi in punches:           # the hit: rises through the consonant, lands on the vowel
                        if 0 < pi < len(sp2) and len(notes) > pi:
                            a_j = sp2[pi][0]
                            k0 = a_j - 5
                            if 0 <= k0 < a_j and notes[pi - 1] > 0:
                                kk = np.arange(k0, a_j)
                                new_f0[kk] = notes[pi - 1] * np.power(notes[pi] / notes[pi - 1],
                                                                      (kk - k0 + 1) / len(kk))
                    drift = np.cumsum(rng.normal(0.0, 0.02, nc))
                    drift -= np.linspace(drift[0], drift[-1], nc)
                    jit = np.convolve(rng.normal(0.0, 1.0, nc), np.ones(3) / 3.0, mode="same")
                    new_f0 = new_f0 * np.power(2.0, (np.clip(drift, -7.0, 7.0) + jit) / 1200.0)
                    y = pyworld.synthesize(new_f0, sp, ap, FS)
                    for (gi, gj) in glides:
                        # the pause between the two words: f0 is 0 there, which WORLD renders
                        # as hiss - pull it down to a faint breath instead
                        if gi < len(sp2) and gj < len(sp2):
                            cut = sp2[gi][1]
                            gs = sp2[gj][0] - int(0.12 * (1000.0 / FRAME_MS))
                            if gs > cut + 4:
                                s0 = int(cut * FS * FRAME_MS / 1000.0)
                                n = min(int((gs - cut) * FS * FRAME_MS / 1000.0), len(y) - s0)
                                if n > 0:
                                    g = np.full(n, 0.12)
                                    e = min(int(0.010 * FS), n // 2)
                                    g[:e] *= np.linspace(0.0, 1.0, e)
                                    g[-e:] *= np.linspace(1.0, 0.0, e)
                                    y[s0:s0 + n] *= g
                    for pi in punches:           # punched word: the accent swells through the consonant
                        if pi < len(sp2):
                            s0 = int(max(0.0, sp2[pi][0] * FS * FRAME_MS / 1000.0 - 0.05 * FS))
                            n = min(int(0.28 * FS), len(y) - s0)
                            if n > 0:
                                tt = np.arange(n) / FS - 0.05
                                rise = np.clip((tt + 0.05) / 0.05, 0.0, 1.0)
                                fall = np.exp(-np.clip(tt, 0.0, None) / 0.12)
                                y[s0:s0 + n] *= 1.0 + 0.12 * rise * fall
                    hold_to = grid[3] if len(grid) > 3 else 0.0
                    if hold_to > 0.0 and len(sp2) and sp2[-1][1] - sp2[-1][0] >= 60 and not flags.get('no_release'):
                        # musical release for a held last word: keep the vowel alive and fade it
                        # out by the span's end instead of letting the source die mid-note.
                        # The fade stays shallow so the tag stays audible.
                        la, lb, _hz = sp2[-1]
                        s0 = int(la * FS * FRAME_MS / 1000.0)
                        n = min(len(y) - s0, int((lb - la) * FS * FRAME_MS / 1000.0))
                        if n > 0:
                            tt = np.arange(n) / (FS * FRAME_MS / 1000.0)
                            start = 0.85 * (lb - la)
                            g = np.ones(n)
                            mask = tt >= start
                            xr = (tt[mask] - start) / max(1.0, (lb - la - start))
                            g[mask] = np.power(10.0, -2.0 * xr ** 2)
                            e = min(int(0.10 * n), n)
                            g[-e:] *= np.linspace(1.0, 0.0, e)
                            y[s0:s0 + n] *= g
                            if not flags.get('no_melisma'):
                                k2 = int(0.35 * (lb - la))          # lift the melisma tag so it cuts
                                s1 = int((lb - k2) * FS * FRAME_MS / 1000.0)
                                n1 = min(int(k2 * FS * FRAME_MS / 1000.0), len(y) - s1)
                                if n1 > 0:
                                    y[s1:s1 + n1] *= np.linspace(1.0, 1.25, n1)
                    takes.append(_declick(y))
                    if (f0_r > 0).any() and base_hz == 0.0:
                        base_hz = float(np.median(f0_r[f0_r > 0]))
                    continue
            xr, _ = synth_audio(spoken(text), voice, use_cache)
            f0_r, sp_r, ap_r = analyze(xr)
            nr = len(f0_r)

            if flow == "notes":
                # SING, don't talk on a tune: the song holds few long vowels
                # (legato), speech fires one short run per syllable. Map Ryan's
                # voiced runs onto the song's note spans in order, stretch each
                # pair to the note's duration, and put one steady note (with
                # vibrato that grows in) on every span.
                o_runs, r_runs = equalize_runs(runs_of(melody > 0, min_len=8),
                                               runs_of(f0_r > 0, min_len=5))
                ok = o_runs is not None and len(o_runs) > 0
            else:
                ok = False

            if ok:
                # piecewise time map: Ryan's run k lands exactly on note span k,
                # the consonant gaps in between map proportionally
                out_pts, src_pts = [0.0], [0.0]
                for (os_, oe_), (rs_, re_) in zip(o_runs, r_runs):
                    out_pts += [float(os_), float(oe_)]
                    src_pts += [float(rs_), float(re_)]
                out_pts.append(float(nc))
                src_pts.append(float(nr))
                for p in range(1, len(out_pts)):       # keep the map strictly increasing
                    if out_pts[p] <= out_pts[p - 1]:
                        out_pts[p] = out_pts[p - 1] + 1e-3
                    if src_pts[p] <= src_pts[p - 1]:
                        src_pts[p] = src_pts[p - 1] + 1e-3
                src_idx = np.interp(np.arange(nc), out_pts, src_pts)
                src_idx = np.clip(src_idx, 0.0, float(nr - 1))
                sp = warp_along(sp_r, src_idx)
                ap = warp_along(ap_r, src_idx)
                f0_rw = warp_along(f0_r.reshape(-1, 1), src_idx).ravel()

                # hold where the melody rests, slide where it moves: plateau
                # stretches get one steady note (with vibrato), glide stretches
                # keep the shaped melody's own contour, so every pitch is the
                # performance's, never an average of a slide.
                #
                # Then stop it sounding like a synthesiser: a singer is never
                # dead on the grid. Each note lands a few cents off, upward leaps
                # scoop, the vibrato keeps one phase across note boundaries, and
                # the whole line drifts and jitters by cents. All of it is small
                # enough to stay in tune.
                ref = max(float(np.median(melody[melody > 0])), 1e-6)
                cents_curve = 1200.0 * np.log2(np.maximum(melody, 1e-6) / ref)
                vmask = melody > 0
                fps = 1000.0 / FRAME_MS
                new_f0 = np.zeros(nc)
                rng = np.random.default_rng(zlib.crc32(clip_id.encode("utf-8")))
                phase = float(rng.uniform(0.0, 2.0 * np.pi))
                prev = 0.0
                for (ss, se, kind, note_c) in melody_segments(cents_curve, vmask):
                    L = se - ss
                    t = np.arange(L)
                    if kind == "glide":
                        new_f0[ss:se] = melody[ss:se]      # the real slide, in tune
                        prev = float(melody[ss:se][-1])
                        continue
                    detune = float(rng.normal(0.0, 6.0))   # nobody lands dead centre
                    note = ref * np.power(2.0, (note_c + detune) / 1200.0)
                    f = np.full(L, note)
                    g = min(5, max(2, L // 4))             # settle onto the note
                    f[:g] = melody[ss:ss + g] + (f[:g] - melody[ss:ss + g]) * (t[:g] / g)
                    # scoop up into a leap, like a singer reaching for the note
                    if prev > 0.0 and 1200.0 * np.log2(note / prev) > 90.0:
                        depth = float(rng.uniform(16.0, 40.0))
                        k = min(int(0.045 * fps), max(3, L // 3))
                        f[:k] = note * np.power(2.0, -depth * (1.0 - np.arange(k) / k) / 1200.0)
                    # vibrato on anything long enough to hold, with a continuous
                    # phase and a rate/depth that varies per note
                    if L >= 24:
                        rate = float(rng.uniform(4.8, 6.2))
                        depth = (float(rng.uniform(16.0, 26.0)) if L < 60
                                 else float(rng.uniform(28.0, 44.0)) if L < 150
                                 else float(rng.uniform(20.0, 31.0)))
                        ramp = np.clip((t - 0.10 * fps) / (0.15 * fps), 0.0, 1.0)
                        f = f * np.power(2.0, depth * np.sin(phase + 2.0 * np.pi * rate * t / fps) * ramp / 1200.0)
                        phase += 2.0 * np.pi * rate * L / fps
                    new_f0[ss:se] = f
                    prev = note
                new_f0[f0_rw <= 0] = 0.0               # consonants stay consonants
                # ...except the tiny ones. A 15-80 ms hole between syllables is
                # what reads as a stutter; sung words ride the vowel through it.
                holes, start = [], None
                for i, hole in enumerate(new_f0 <= 0.0):
                    if hole and start is None:
                        start = i
                    elif not hole and start is not None:
                        holes.append((start, i)); start = None
                if start is not None:
                    holes.append((start, nc))
                for (a, b) in holes:
                    # a gap inside one sustained note (same pitch both sides) is a stutter, not a
                    # word break: ride the note through gaps up to 150 ms. A gap where the pitch
                    # changes is a syllable boundary and keeps its short silence (the old 80 ms cap).
                    same_note = a > 0 and b < nc and new_f0[a - 1] > 0 and new_f0[b] > 0 and \
                        abs(1200.0 * np.log2(new_f0[b] / new_f0[a - 1])) < 200.0
                    cap = 30 if same_note else 16
                    if 3 <= b - a <= cap and a > 0 and b < nc and new_f0[a - 1] > 0 and new_f0[b] > 0:
                        new_f0[a:b] = np.exp(np.linspace(np.log(new_f0[a - 1]),
                                                         np.log(new_f0[b]), b - a))
                # slow drift + fine jitter over the whole line
                drift = np.cumsum(rng.normal(0.0, 0.035, nc))
                drift -= np.linspace(drift[0], drift[-1], nc)
                jit = np.convolve(rng.normal(0.0, 1.8, nc), np.ones(3) / 3.0, mode="same")
                new_f0 = new_f0 * np.power(2.0, (np.clip(drift, -7.0, 7.0) + jit) / 1200.0)
            else:
                # fallback: the old contour path (linear warp + shaped melody)
                sp = warp_frames(sp_r, nc)
                ap = warp_frames(ap_r, nc)
                f0_rw = warp_frames(f0_r.reshape(-1, 1), nc).ravel()
                voiced_r = f0_rw > 0
                new_f0 = np.where(voiced_r, melody, 0.0)

            takes.append(pyworld.synthesize(new_f0, sp, ap, FS))
            if (f0_r > 0).any() and base_hz == 0.0:
                base_hz = float(np.median(f0_r[f0_r > 0]))

    # merge the takes into one voice: every take is already warped to the same
    # length, so an equal mix is sample-aligned. Takes are independent renders,
    # so they sum in power, not phase; normalize afterwards.
    w = np.array(args_mix_weights, dtype=float)
    if len(takes) > 1:
        w = w[:len(takes)] / np.sum(w[:len(takes)])
        y = np.zeros_like(takes[0])
        for take, wi in zip(takes, w):
            y += take * wi
    else:
        y = takes[0]
    # level + tiny edge fades to avoid clicks
    if MASTER == "peak":
        peak = np.max(np.abs(y)) or 1.0
        y = y / peak * MASTER_CEILING
    else:
        y = master_level(y, FS)
    nfade = int(0.006 * FS)
    if len(y) > 2 * nfade:
        y[:nfade] *= np.linspace(0, 1, nfade)
        y[-nfade:] *= np.linspace(1, 0, nfade)

    save_ogg(VOX / f"{clip_id}.ogg", y, FS)
    f0m = f0_c[f0_c > 0]
    return {
        "clip": clip_id,
        "dur": round(dur, 2),
        "melody_hz": round(float(np.median(f0m)), 1) if len(f0m) else 0,
        "ryan_hz": round(base_hz, 1),
        "takes": len(takes),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--voice", default="en_US-bryce-medium",
                    help="one voice; comma-separated renders one take per voice and mixes them (chorus-style, can smear)")
    ap.add_argument("--mix", default="1,1,0.6",
                    help="take weights, comma-separated; ryan-low is a 16 kHz model, so it sits under the two 22 kHz takes")
    ap.add_argument("--vibrato", type=float, default=0.65,
                    help="how much of the original clip's vibrato survives (0 = straight notes, 1 = full depth)")
    ap.add_argument("--flow", choices=["notes", "contour"], default="notes",
                    help="notes: align syllables to the song's held notes and sing steady notes; "
                         "contour: the old path (speech rhythm, melody painted over it)")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--only", default="",
                    help="comma-separated clip ids to render (testing; default: every used clip)")
    ap.add_argument("--restore", action="store_true", help="put the original clips back")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    voices = [v.strip() for v in args.voice.split(",") if v.strip()]
    weights = [float(x) for x in args.mix.split(",")]
    ps_vib = args.vibrato
    ps_flow = args.flow

    vox_map = json.loads(DATA_VOX.read_text(encoding="utf-8"))
    lyrics = json.loads(LYRICS.read_text(encoding="utf-8"))["victory_vocals"]

    # unique source clips only (F2/F3 alias B6/B7 in the song data)
    used = {v[0] for v in vox_map.values()}
    ids = sorted(k for k in used if k in lyrics)
    if args.only:
        want = {x.strip() for x in args.only.split(",") if x.strip()}
        ids = [k for k in ids if k in want]

    if args.restore:
        restored = 0
        for p in BACKUP.glob("*.ogg"):
            shutil.copy2(p, VOX / p.name)
            restored += 1
        print(f"restored {restored} original clips")
        return 0

    # one-time backup of the bank's sung clips (new clips have no original yet)
    BACKUP.mkdir(parents=True, exist_ok=True)
    for clip_id in ids:
        dst = BACKUP / f"{clip_id}.ogg"
        if not dst.exists() and (VOX / f"{clip_id}.ogg").exists():
            shutil.copy2(VOX / f"{clip_id}.ogg", dst)

    report = []
    for clip_id in ids:
        text = lyrics[clip_id]
        if args.dry_run:
            print(f"would sing {clip_id}: {text!r}")
            continue
        info = sing_clip(clip_id, text, voices, weights, ps_vib, ps_flow,
                         grid=CHORUS_GRID.get(clip_id), use_cache=not args.force)
        report.append(info)
        print(f"  {clip_id}: '{text}'  melody {info['melody_hz']} Hz, "
              f"Ryan base {info['ryan_hz']} Hz, {info['dur']} s, {info['takes']} takes")
    print(f"done: {len(report)} clips re-sung with {'+'.join(voices)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
