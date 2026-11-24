"""Voiceover via the ElevenLabs text-to-speech API.
The API key is NOT read here: the sandbox network proxy injects the `xi-api-key` header for api.elevenlabs.io.
Outside the sandbox, set up the header yourself (e.g. curl -H "xi-api-key: $ELEVENLABS_API_KEY") or adapt `call()`.
Lines are cached in el_cache/ so re-timing never spends credits again.
"""
import json, os, subprocess, sys
import numpy as np, soundfile as sf
from vo_lines import LINES

VOICE_ID = os.environ.get('EL_VOICE', 'onwK4e9ZLuTAKqWW03F9')   # Daniel - Steady Broadcaster (premade)
MODEL = os.environ.get('EL_MODEL', 'eleven_multilingual_v2')
SR = 44100
os.makedirs('el_cache', exist_ok=True)


def call(i, text, prev_text, next_text):
    path = f'el_cache/line_{i:02d}.mp3'
    if os.path.exists(path) and os.path.getsize(path) > 1000: return path
    body = dict(text=text, model_id=MODEL, seed=7,
                voice_settings=dict(stability=.55, similarity_boost=.75, style=.0, use_speaker_boost=True, speed=1.0))
    if prev_text: body['previous_text'] = prev_text
    if next_text: body['next_text'] = next_text
    json.dump(body, open('el_req.json', 'w'))
    r = subprocess.run(['curl', '-s', '-m', '90', '-o', path, '-w', '%{http_code}', '-X', 'POST',
                        f'https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}?output_format=mp3_44100_128',
                        '-H', 'Content-Type: application/json', '-d', '@el_req.json'], capture_output=True, text=True)
    if r.stdout.strip() != '200':
        err = open(path, 'rb').read(400); os.remove(path)
        sys.exit(f'line {i}: HTTP {r.stdout} {err!r}')
    return path


def load(path):
    p = subprocess.run(['ffmpeg', '-v', 'error', '-i', path, '-f', 'f32le', '-ac', '1', '-ar', str(SR), '-'], capture_output=True)
    return np.frombuffer(p.stdout, dtype='<f4').astype(np.float64)


OVERRIDE = {1: ('One point two kilobytes.', '1.2 KB.')}   # ElevenLabs reads slower than Kokoro; tighter wording keeps scene 1 inside its 5 s
LINES = [(l[0], OVERRIDE[i][0], OVERRIDE[i][1]) if i in OVERRIDE else l for i, l in enumerate(LINES)]
say = [l[1].replace('ORION', 'Orion') for l in LINES]
clips = []
for i, (t0, _, sub) in enumerate(LINES):
    path = call(i, say[i], say[i - 1] if i else None, say[i + 1] if i + 1 < len(say) else None)
    s = load(path)
    thr = .01 * np.max(np.abs(s)); idx = np.nonzero(np.abs(s) > thr)[0]
    s = s[max(0, idx[0] - int(.02 * SR)): idx[-1] + int(.05 * SR)]
    clips.append(s)
    print(f'{i:2d} want {t0:5.1f}  len {len(s) / SR:4.2f}s  {sub}')
json.dump([len(c) / SR for c in clips], open('el_durations.json', 'w'))
