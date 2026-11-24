"""Synthesize the voiceover with Kokoro (free, open-source TTS) and write timings + subtitle cues.
Run with a Python that has kokoro-onnx + soundfile:  KOKORO_DIR=<dir with kokoro-v1.0.onnx, voices-v1.0.bin> python vo.py
"""
import json, os, re
import numpy as np, soundfile as sf
from kokoro_onnx import Kokoro

D = os.environ['KOKORO_DIR']
VOICE = os.environ.get('VOICE', 'am_michael')
SPEED = float(os.environ.get('SPEED', '1.0'))
k = Kokoro(f'{D}/kokoro-v1.0.onnx', f'{D}/voices-v1.0.bin')

# (start_seconds, spoken text for TTS, subtitle text) — starts sit on the scene beats from index.html
from vo_lines import LINES

SR = 44100
out = np.zeros(int(60 * SR))
timings = []
for i, (t0, say, sub) in enumerate(LINES):
    s, sr = k.create(say, voice=VOICE, speed=SPEED, lang='en-us')
    s = np.asarray(s, dtype=np.float64)
    # trim leading/trailing silence
    thr = 0.01 * np.max(np.abs(s)); idx = np.nonzero(np.abs(s) > thr)[0]
    s = s[max(0, idx[0] - int(.02 * sr)): idx[-1] + int(.05 * sr)]
    # resample 24k -> 44.1k (linear is fine for speech at this ratio after FFT lowpass)
    n_out = int(len(s) * SR / sr)
    s = np.interp(np.linspace(0, len(s) - 1, n_out), np.arange(len(s)), s)
    s *= 0.20 / (np.sqrt(np.mean(s ** 2)) + 1e-9)          # per-line RMS match
    fade = int(.015 * SR); s[:fade] *= np.linspace(0, 1, fade); s[-fade:] *= np.linspace(1, 0, fade)
    a = int(t0 * SR); b = min(len(out), a + len(s))
    out[a:b] += s[:b - a]
    timings.append(dict(i=i, start=t0, end=round(t0 + len(s) / SR, 3), dur=round(len(s) / SR, 3), text=sub))
    print(f'{i:2d} {t0:5.1f} -> {t0 + len(s) / SR:5.2f}  ({len(s) / SR:4.2f}s)  {sub}')

# overlap check
for a, b in zip(timings, timings[1:]):
    if a['end'] > b['start'] - .05: print('!! overlap/tight:', a['i'], a['end'], '>', b['start'])

sf.write('voice_raw.wav', out, SR)
json.dump(timings, open('vo_timings.kokoro.json', 'w'), indent=1)
