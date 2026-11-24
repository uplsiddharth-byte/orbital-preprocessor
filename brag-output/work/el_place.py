"""Place cached ElevenLabs clips on the scene beats (tempo-fit + push-back), write voice_raw_el.wav + vo_timings.el.json."""
import json, subprocess, sys, os
import numpy as np, soundfile as sf
from vo_lines import LINES
SR = 44100
OVERRIDE = {1: ('One point two kilobytes.', '1.2 KB.')}
L = [(l[0], OVERRIDE[i][1]) if i in OVERRIDE else (l[0], l[2]) for i, l in enumerate(LINES)]
def load(i, tempo):
    f = ['-filter:a', f'atempo={tempo}'] if abs(tempo - 1) > 1e-3 else []
    p = subprocess.run(['ffmpeg', '-v', 'error', '-i', f'el_cache/line_{i:02d}.mp3'] + f + ['-f', 'f32le', '-ac', '1', '-ar', str(SR), '-'], capture_output=True)
    s = np.frombuffer(p.stdout, dtype='<f4').astype(np.float64)
    idx = np.nonzero(np.abs(s) > .01 * np.max(np.abs(s)))[0]
    return s[max(0, idx[0] - int(.02 * SR)): idx[-1] + int(.05 * SR)]
def plan(tempo, gap=.10):
    t = 0; out = []
    for i, (want, sub) in enumerate(L):
        s = load(i, tempo); start = max(want if i else .25, t + gap); end = start + len(s) / SR
        out.append((start, end, s)); t = end
    return out
best = None
for tempo in [1.0, 1.04, 1.06, 1.08, 1.10, 1.12, 1.15]:
    p = plan(tempo); drift = max(abs(a[0] - L[i][0]) for i, a in enumerate(p)); last = p[-1][1]
    print(f'tempo {tempo}: last ends {last:.2f}s, max start drift {drift:.2f}s')
    if best is None and last <= 59.6 and drift <= .75: best = tempo
tempo = float(os.environ.get('TEMPO', best or 1.15)); print('using tempo', tempo)
p = plan(tempo); out = np.zeros(int(60 * SR)); T = []
for i, (start, end, s) in enumerate(p):
    s = s * (0.20 / (np.sqrt(np.mean(s ** 2)) + 1e-9)); f = int(.015 * SR); s[:f] *= np.linspace(0, 1, f); s[-f:] *= np.linspace(1, 0, f)
    a = int(start * SR); b = min(len(out), a + len(s)); out[a:b] += s[:b - a]
    T.append(dict(i=i, start=round(start, 3), end=round(end, 3), dur=round(end - start, 3), text=L[i][1])); print(f'{i:2d} {start:5.2f}-{end:5.2f} (want {L[i][0]:5.1f})  {L[i][1]}')
sf.write('voice_raw_el.wav', out, SR); json.dump(T, open('vo_timings.el.json', 'w'), indent=1)
