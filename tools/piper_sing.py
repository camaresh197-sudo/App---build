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
import json
import shutil
import subprocess
import sys
import tempfile
import wave
from pathlib import Path

import numpy as np
import pyworld

TOOLS = Path(__file__).resolve().parent
ROOT = TOOLS.parent
HULA = ROOT / "godot" / "hula"
VOX = HULA / "audio" / "vox"
LYRICS = HULA / "data" / "data_lyrics.json"
DATA_VOX = HULA / "data" / "data_vox.json"
MODELS = TOOLS / "models"
BACKUP = TOOLS / "vox_backup" / "originals"

sys.path.insert(0, str(TOOLS))
import piper_gen  # noqa: E402

FS = 22050          # analysis rate (the medium/high models are 22050; low is 16 kHz and ffmpeg-resampled)
FRAME_MS = 5.0      # WORLD frame period
OGG_RATE = 44100    # the bank ships 44.1 kHz mono vorbis


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


def sing_clip(clip_id: str, text: str, voices: list, args_mix_weights, vib: float = 0.65,
              flow: str = "notes") -> dict:
    # the melody comes from the ORIGINAL bank clip, not the current one: after a
    # first Ryan pass the file on disk is already sung, so re-running would
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
            rwav = Path(td) / f"take_{i}.wav"
            piper_gen.synthesize(text, voice, str(rwav), str(MODELS))
            xr = load_wav_mono(rwav, FS)
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
                # stretches get one steady note (+vibrato on long holds), glide
                # stretches keep the shaped melody's own contour, so every pitch
                # is the performance's, never an average of a slide
                ref = max(float(np.median(melody[melody > 0])), 1e-6)
                cents_curve = 1200.0 * np.log2(np.maximum(melody, 1e-6) / ref)
                vmask = melody > 0
                fps = 1000.0 / FRAME_MS
                new_f0 = np.zeros(nc)
                for (ss, se, kind, note_c) in melody_segments(cents_curve, vmask):
                    L = se - ss
                    t = np.arange(L)
                    if kind == "glide":
                        new_f0[ss:se] = melody[ss:se]      # the real slide, in tune
                        continue
                    note = ref * np.power(2.0, note_c / 1200.0)
                    f = np.full(L, note)
                    g = min(5, max(2, L // 4))             # settle onto the note
                    f[:g] = melody[ss:ss + g] + (f[:g] - melody[ss:ss + g]) * (t[:g] / g)
                    if L >= 50:                            # 250 ms: a held note earns its vibrato
                        depth = 40.0 if L >= 100 else 28.0
                        ramp = np.clip((t - 24) / 40.0, 0.0, 1.0)
                        f = f * np.power(2.0, depth * np.sin(2 * np.pi * 5.5 * t / fps) * ramp / 1200.0)
                    new_f0[ss:se] = f
                new_f0[f0_rw <= 0] = 0.0               # consonants stay consonants
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
        info = sing_clip(clip_id, text, voices, weights, ps_vib, ps_flow)
        report.append(info)
        print(f"  {clip_id}: '{text}'  melody {info['melody_hz']} Hz, "
              f"Ryan base {info['ryan_hz']} Hz, {info['dur']} s, {info['takes']} takes")
    print(f"done: {len(report)} clips re-sung with {'+'.join(voices)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
