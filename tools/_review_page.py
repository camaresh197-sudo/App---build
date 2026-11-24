import soundfile as sf, json, pathlib

ids = ['A0', 'A2', 'A4', 'A6', 'B0', 'B1', 'B2', 'B3', 'B4', 'B5', 'B6', 'B7',
       'C0', 'C2', 'C4', 'C6', 'D0', 'D2', 'D4', 'D6', 'tag0', 'tag2', 'F0']
out = []
for i in ids:
    p = f'godot/hula/audio/vox/{i}.ogg'
    if pathlib.Path(p).exists():
        x, r = sf.read(p)
        sf.write(f'build/rev_{i}.wav', x, r)
        out.append(i)
lyr = json.load(open('godot/hula/data/data_lyrics.json', encoding='utf-8'))['victory_vocals']
rows = ''.join(
    f'<section><h2>{i} — {lyr.get(i, "")}</h2><audio controls src="rev_{i}.wav"></audio></section>'
    for i in out)
html = ('<!doctype html><html><head><meta charset="utf-8"><title>Victory song - bryce full render</title>'
        '<style>body{font-family:sans-serif;background:#1c1c24;color:#eee;max-width:640px;margin:2rem auto}'
        'h2{margin:.4rem 0}audio{width:100%}section{background:#2a2a35;border-radius:10px;padding:12px 16px;margin:10px 0}'
        '</style></head><body><h1>Victory song - bryce, fixed engine - ' + str(len(out)) + ' lines</h1>'
        + rows + '</body></html>')
open('build/victory_review.html', 'w', encoding='utf-8').write(html)
print('lines:', ' '.join(out))
