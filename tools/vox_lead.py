"""Per-clip lead calibration for the victory vox clips.

Engine (sound.gd:663) starts a line clip at (bar time - lead + 0.01), so the clip's
first audible sample must sit at time `lead` inside the clip. data_vox.json said 0.15
for every line, but the renders hold 0.08-0.56 s of silence, so each line entered late
by (measured - 0.15).

Writes: godot/hula/data/data_vox.json (leads), build/vox_before.ogg / vox_after.ogg
(v-A with the instrument stem, old vs new placement).
"""
import glob
import json
import os

import numpy as np
import soundfile as sf

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VOX = os.path.join(ROOT, 'godot', 'hula', 'audio', 'vox')
DATA = os.path.join(ROOT, 'godot', 'hula', 'data', 'data_vox.json')
STEMS = os.path.join(ROOT, 'stems')
OUT = os.path.join(ROOT, 'build')

WIN = 0.005


def first_sound(x, sr, rel_db=-40.0):
    """time of the first 5 ms window whose RMS is within rel_db of the clip peak"""
    hop = max(1, int(WIN * sr))
    n = len(x) // hop
    e = np.sqrt(np.mean(x[:n * hop].reshape(n, hop) ** 2, axis=1))
    db = 20 * np.log10(np.maximum(e, 1e-9) / e.max())
    idx = int(np.argmax(db > rel_db))
    return idx * WIN


def load(path):
    d, sr = sf.read(path)
    if d.ndim > 1:
        d = d.mean(1)
    return d, sr


def main():
    leads = {}
    for path in sorted(glob.glob(os.path.join(VOX, '*.ogg'))):
        name = os.path.basename(path)[:-4]
        if name.startswith('orig_'):
            continue
        d, sr = load(path)
        leads[name] = round(first_sound(d, sr), 2)

    data = json.load(open(DATA, encoding='utf-8'))
    moved = {k: (data[k][1], leads[k]) for k in leads if k in data and abs(data[k][1] - leads[k]) > 0.01}
    for k, v in moved.items():
        data[k][1] = v[1]
    with open(DATA, 'w', encoding='utf-8', newline='') as f:
        f.write(json.dumps(data, ensure_ascii=False) + '\n')
    print('leads moved (old -> new):')
    for k in sorted(moved):
        print('  %-5s %.2f -> %.2f  (%+.0f ms)' % (k, moved[k][0], moved[k][1], (moved[k][1] - moved[k][0]) * 1000))

    # --- v-A section with the instrument stem: before vs after placement ---
    ins, sr = load(os.path.join(STEMS, 'instruments.flac'))
    BAR = 1.68
    LINES = [('A0', 0), ('A2', 1), ('A4', 2), ('A6', 3)]
    # bar 0 of v-A sits this late in the stem (A0's clip start found by cross-correlation + old lead)
    bar0 = 1.619
    span = int(4 * 2 * BAR * sr)

    def mix(leads_used):
        pre = 0.6
        buf = np.zeros(int(pre * sr) + span + sr)
        start = int(bar0 * sr)
        buf[int(pre * sr):int(pre * sr) + span] = ins[start:start + span]
        for name, bar in LINES:
            clip, csr = load(os.path.join(VOX, name + '.ogg'))
            assert csr == sr
            t = bar * 2 * BAR - leads_used[name] + 0.01
            i = int(round((t + pre) * sr))
            buf[i:i + len(clip)] += clip * 1.0
        return buf[int(pre * sr):]

    before = mix({k: 0.15 for k, _ in LINES})
    after = mix(leads)
    for tag, x in (('before', before), ('after', after)):
        sf.write(os.path.join(OUT, 'vox_%s.wav' % tag), x / max(1.0, np.max(np.abs(x)) * 1.05), sr)
    print('wrote build/vox_before.wav, build/vox_after.wav')

    for name, bar in LINES:
        print('%-3s clip first sound %.2f  old lead 0.15 -> %+0.0f ms  new lead %.2f -> %+0.0f ms'
              % (name, leads[name], (leads[name] - 0.15) * 1000, leads[name], 0.0))


if __name__ == '__main__':
    main()
