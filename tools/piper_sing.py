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
    python piper_sing.py [--voice en_US-ryan-medium] [--force] [--restore] [--dry-run]
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

FS = 22050          # analysis rate (piper medium models are 22050)
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


def sing_clip(clip_id: str, text: str, voice: str) -> dict:
    orig = VOX / f"{clip_id}.ogg"
    x0 = load_wav_mono(orig, FS)
    f0_c, _, _ = analyze(x0)                      # the melody to borrow
    nc = len(f0_c)
    dur = len(x0) / FS

    with tempfile.TemporaryDirectory() as td:
        rwav = Path(td) / "ryan.wav"
        piper_gen.synthesize(text, voice, str(rwav), str(MODELS))
        xr = load_wav_mono(rwav, FS)
    f0_r, sp_r, ap_r = analyze(xr)
    nr = len(f0_r)

    # 1) time-warp Ryan's spectral frames onto the clip's duration
    sp = warp_frames(sp_r, nc)
    ap = warp_frames(ap_r, nc)

    # 2) borrow the melody: clip F0 where Ryan is voiced, gaps filled,
    #    unvoiced where Ryan is unvoiced (consonants stay consonants)
    f0_rw = warp_frames(f0_r.reshape(-1, 1), nc).ravel()
    melody = fill_gaps(f0_c)
    voiced_r = f0_rw > 0
    new_f0 = np.where(voiced_r, melody, 0.0)

    y = pyworld.synthesize(new_f0, sp, ap, FS)
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
        "ryan_hz": round(float(np.median(f0_r[f0_r > 0])), 1) if (f0_r > 0).any() else 0,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--voice", default="en_US-ryan-medium")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--restore", action="store_true", help="put the original clips back")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

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
        info = sing_clip(clip_id, text, args.voice)
        report.append(info)
        print(f"  {clip_id}: '{text}'  melody {info['melody_hz']} Hz, "
              f"Ryan base {info['ryan_hz']} Hz, {info['dur']} s")
    print(f"done: {len(report)} clips re-sung with {args.voice}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
