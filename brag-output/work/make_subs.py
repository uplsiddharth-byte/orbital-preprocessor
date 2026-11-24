"""Chunk VO timings into subtitle cues; writes subs.js (overlay) + SRT/VTT.  usage: make_subs.py timings.json out_prefix"""
import json, re, sys
T = json.load(open(sys.argv[1])); prefix = sys.argv[2]; cues = []
for i, t in enumerate(T):
    words = t['text'].split(); chunks = []; cur = ''
    for w in words:
        if cur and len(cur) + 1 + len(w) > 52: chunks.append(cur); cur = w
        else: cur = (cur + ' ' + w).strip()
        if cur and re.search(r'[,.?!]$', cur) and len(cur) > 30 and w is not words[-1]: chunks.append(cur); cur = ''
    if cur: chunks.append(cur)
    if len(chunks) > 1 and len(chunks[-1]) < 12: chunks[-2] += ' ' + chunks[-1]; chunks.pop()
    start = t['start']; nxt = T[i + 1]['start'] if i + 1 < len(T) else 60
    end = min(t['end'] + .2, nxt - .05, 60); total = sum(len(c) for c in chunks); a = start
    for c in chunks:
        d = (end - start) * len(c) / total; cues.append(dict(start=round(a, 2), end=round(a + d, 2), text=c)); a += d
json.dump(cues, open('subs.json', 'w'), indent=1); open('subs.js', 'w').write('window.SUBS=' + json.dumps(cues) + ';')
def ts(x, sep):
    h = int(x // 3600); m = int(x % 3600 // 60); s = x % 60; return f"{h:02d}:{m:02d}:{int(s):02d}{sep}{int(round((s - int(s)) * 1000)):03d}"
open(f'../{prefix}.srt', 'w').write(''.join(f"{i+1}\n{ts(c['start'],',')} --> {ts(c['end'],',')}\n{c['text']}\n\n" for i, c in enumerate(cues)))
open(f'../{prefix}.vtt', 'w').write('WEBVTT\n\n' + ''.join(f"{ts(c['start'],'.')} --> {ts(c['end'],'.')}\n{c['text']}\n\n" for c in cues))
print(len(cues), 'cues')
