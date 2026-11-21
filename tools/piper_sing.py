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
CHORUS_GRID = {"B0": ("v-B", 0, 2), "B1": ("v-B", 2, 2),
               "B2": ("v-B", 4, 2), "B3": ("v-B", 6, 2)}


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


def grid_melody(section: str, start_bar: int, n_bars: int, syllables: int = 0):
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
    if k <= n_bars * 4:
        onsets = [min(lead + b * 4 * step_frames, n - 1) for b in range(k)]
        steps_at = [b * 4 for b in range(k)]
    else:
        onsets = [int(round(i * (n - 1) / (k - 1))) for i in range(k)]
        steps_at = [min(int(round(o / step_frames)), n_bars * 16 - 1) for o in onsets]
    onsets = [int(round(o)) for o in onsets]

    spans = []
    for i, o in enumerate(onsets):
        e = onsets[i + 1] if i + 1 < len(onsets) else n
        hz = pitch[steps_at[i]]
        if hz <= 0:
            hz = pitch[max(0, steps_at[i] - 1)]
        spans.append((o, e, float(hz)))
    f0 = np.zeros(n)
    for (a, b, hz) in spans:
        f0[a:b] = hz
    return f0, spans


VOWELS = set("aeiouyæɑɒɔəɚɛɜɪʊʌɐɤɯɵɞɘøœʏɨʉ")
_ALIGNED = {}


def aligned_voice(name):
    """Piper voice loaded so each call can return phoneme/audio alignments."""
    from piper import PiperVoice
    if name not in _ALIGNED:
        _ALIGNED[name] = PiperVoice.load(str(MODELS / f"{name}.onnx"),
                                         config_path=str(MODELS / f"{name}.onnx.json"),
                                         use_cuda=False, include_alignments=True)
        from pronounce.engine import attach_lexicon
        attach_lexicon(_ALIGNED[name])
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


def synth_aligned(text: str, voice: str, use_cache: bool = True):
    """Synthesize and return (audio, [(phoneme, start_sample, end_sample)]).

    The audio and its alignment are cached together; a second call reads them
    from disk instead of running Piper again.
    """
    CACHE.mkdir(parents=True, exist_ok=True)
    k = _key(text, voice)
    wav = CACHE / f"al_{voice}_{k}.wav"
    js = CACHE / f"al_{voice}_{k}.json"
    if use_cache and wav.exists() and js.exists():
        x, sr = sf.read(str(wav), dtype="float64", always_2d=True)
        phonemes = [tuple(p) for p in json.loads(js.read_text(encoding="utf-8"))]
        return _fit(x[:, 0], sr), phonemes
    chunks = list(aligned_voice(voice).synthesize(text, include_alignments=True))
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


def sing_clip(clip_id: str, text: str, voices: list, args_mix_weights, vib: float = 0.65,
              flow: str = "notes", grid=None, use_cache: bool = True) -> dict:
    spans = []
    if grid:
        melody, spans = grid_melody(*grid, syllables=len(words_of(text)))
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
    with tempfile.TemporaryDirectory() as td:
        for i, voice in enumerate(voices):
            if grid:
                # Grid mode: Piper's phoneme alignments say exactly when each
                # vowel starts. Put every vowel on its beat, keep the consonants
                # in the gaps, and sing one note per syllable.
                audio, phonemes = synth_aligned(spoken(text), voice, use_cache)
                f0_r, sp_r, ap_r = analyze(audio)
                nr = len(f0_r)
                nuc = word_spans(phonemes)
                if len(nuc) == len(spans):
                    vsf0 = nuc[0][0] / FS * 1000.0 / FRAME_MS
                    lead = float(spans[0][0])
                    anchors_src, anchors_out = [0.0, vsf0], [max(0.0, lead - vsf0), lead]
                    for k, (vs, ve) in enumerate(nuc):
                        a, b, _hz = spans[k]
                        if k > 0:
                            anchors_src.append(vs / FS * 1000.0 / FRAME_MS)
                            anchors_out.append(float(a))
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
                    new_f0 = np.zeros(nc)
                    for (a, b, hz) in spans:
                        L = b - a
                        t = np.arange(L)
                        note = hz * np.power(2.0, float(rng.normal(0.0, 6.0)) / 1200.0)
                        f = np.full(L, note)
                        if prev > 0.0 and 1200.0 * np.log2(note / prev) > 90.0:
                            depth = float(rng.uniform(12.0, 28.0))
                            k = min(int(0.045 * (1000.0 / FRAME_MS)), max(3, L // 3))
                            f[:k] = note * np.power(2.0, -depth * (1.0 - np.arange(k) / k) / 1200.0)
                        if L >= 24:
                            rate = float(rng.uniform(4.8, 6.2))
                            depth = float(rng.uniform(16.0, 26.0)) if L < 60 else float(rng.uniform(28.0, 44.0))
                            ramp = np.clip((t - 0.10 * (1000.0 / FRAME_MS)) / (0.15 * (1000.0 / FRAME_MS)), 0.0, 1.0)
                            f = f * np.power(2.0, depth * np.sin(phase + 2.0 * np.pi * rate * t / (1000.0 / FRAME_MS)) * ramp / 1200.0)
                            phase += 2.0 * np.pi * rate * L / (1000.0 / FRAME_MS)
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
                    drift = np.cumsum(rng.normal(0.0, 0.035, nc))
                    drift -= np.linspace(drift[0], drift[-1], nc)
                    jit = np.convolve(rng.normal(0.0, 1.8, nc), np.ones(3) / 3.0, mode="same")
                    new_f0 = new_f0 * np.power(2.0, (np.clip(drift, -7.0, 7.0) + jit) / 1200.0)
                    takes.append(pyworld.synthesize(new_f0, sp, ap, FS))
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
                        depth = float(rng.uniform(12.0, 28.0))
                        k = min(int(0.045 * fps), max(3, L // 3))
                        f[:k] = note * np.power(2.0, -depth * (1.0 - np.arange(k) / k) / 1200.0)
                    # vibrato on anything long enough to hold, with a continuous
                    # phase and a rate/depth that varies per note
                    if L >= 24:
                        rate = float(rng.uniform(4.8, 6.2))
                        depth = float(rng.uniform(16.0, 26.0)) if L < 60 else float(rng.uniform(28.0, 44.0))
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
                    if 3 <= b - a <= 16 and a > 0 and b < nc and new_f0[a - 1] > 0 and new_f0[b] > 0:
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
    # normalize + tiny edge fades to avoid clicks
    peak = np.max(np.abs(y)) or 1.0
    y = y / peak * 0.89
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
    ap.add_argument("--voice", default="en_US-ryan-high",
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

    # one-time backup of the bank's sung clips
    BACKUP.mkdir(parents=True, exist_ok=True)
    for clip_id in ids:
        dst = BACKUP / f"{clip_id}.ogg"
        if not dst.exists():
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
