"""Synthesize the soundtrack for the OSP brag video.
One grid: 120 BPM (beat = 0.5 s), A minor, every event is placed on that grid from sample 0.
"""
import json, wave
import numpy as np

SR = 44100
DUR = 60.0
N = int(SR * DUR)
BEAT = 0.5
BAR = 2.0
rng = np.random.default_rng(7)

cues = json.load(open('cues.json'))
CUES = sorted(set(round(c * 4) / 4 for c in cues['cues']))  # snap to 16ths of the grid (0.25 s)
SCENES = cues['scenes']

# buses (stereo): dry music, wet (reverb send), sfx
dry = np.zeros((2, N)); wet = np.zeros((2, N)); duck_src = np.zeros(N)


def midi(m): return 440.0 * 2 ** ((m - 69) / 12)


def tt(n): return np.arange(n) / SR


def lp(x, fc, order=2):
    X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / SR)
    return np.fft.irfft(X / np.sqrt(1 + (f / fc) ** (2 * order)), len(x))


def hp(x, fc, order=2):
    X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / SR); r = (f / fc) ** (2 * order)
    return np.fft.irfft(X * np.sqrt(r / (1 + r)), len(x))


def put(sig, start, pan=0.0, send=0.0, gain=1.0, bus=None):
    i = int(round(start * SR)); n = min(len(sig), N - i)
    if n <= 0 or i < 0: return
    s = sig[:n] * gain
    l = np.cos((pan + 1) * np.pi / 4); r = np.sin((pan + 1) * np.pi / 4)
    tgt = dry if bus is None else bus
    tgt[0, i:i + n] += s * l; tgt[1, i:i + n] += s * r
    if send > 0:
        wet[0, i:i + n] += s * l * send; wet[1, i:i + n] += s * r * send


def kick(start, g=1.0):
    t = tt(int(.5 * SR)); f = 45 + 110 * np.exp(-t * 28)
    ph = 2 * np.pi * np.cumsum(f) / SR
    s = np.sin(ph) * np.exp(-t * 7) + .35 * np.sin(ph * 2) * np.exp(-t * 30)
    s += .25 * hp(rng.standard_normal(len(t)) * np.exp(-t * 400), 2000)
    put(s, start, gain=.9 * g)
    i = int(start * SR); duck_src[i:i + 1] += 1


def clap(start, g=1.0):
    t = tt(int(.3 * SR)); n = rng.standard_normal(len(t))
    env = np.exp(-t * 18) * (1 + .9 * (np.sin(t * 2 * np.pi * 90) > 0) * np.exp(-t * 60))
    s = hp(lp(n, 6500), 900) * env
    put(s, start, pan=.1, send=.30, gain=.30 * g)


def hat(start, g=1.0, open_=False, pan=0.0):
    L = .28 if open_ else .06; t = tt(int(L * SR)); n = rng.standard_normal(len(t))
    s = hp(n, 7500) * np.exp(-t * (14 if open_ else 70))
    put(s, start, pan=pan, send=.12, gain=.13 * g)


def bass(start, f, L=.45, g=1.0):
    t = tt(int(L * SR)); ph = 2 * np.pi * f * t
    s = np.sin(ph) + .35 * np.sin(2 * ph) + .12 * (2 * ((f * t) % 1) - 1)
    s = lp(s, 380) * np.minimum(1, t / .006) * np.exp(-t * 3.2)
    put(s, start, gain=.42 * g)


def pad(start, notes, L, g=1.0, bright=1500):
    n = int((L + 1.2) * SR); t = tt(n); s = np.zeros(n)
    for k, m in enumerate(notes):
        f = midi(m)
        for d in (-.11, .0, .11):
            ph = 2 * np.pi * f * (1 + d / 100) * t + k
            s += (2 * ((f * (1 + d / 100) * t + k * .13) % 1) - 1) * .5 + np.sin(ph) * .5
    s = lp(s, bright)
    env = np.minimum(1, t / .35) * np.where(t < L, 1, np.exp(-(t - L) * 2.5))
    s *= env / (len(notes) * 3)
    put(s, start, pan=0.0, send=.35, gain=.62 * g)
    return s


def pluck(start, f, g=1.0, pan=0.0, L=.6):
    t = tt(int(L * SR)); ph = 2 * np.pi * f * t
    s = np.sin(ph) + .4 * np.sin(2 * ph) * np.exp(-t * 14) + .15 * np.sin(3 * ph) * np.exp(-t * 25)
    s *= np.minimum(1, t / .003) * np.exp(-t * 9)
    put(s, start, pan=pan, send=.4, gain=.2 * g)
    put(s, start + .375, pan=-pan, send=.4, gain=.09 * g)       # dotted-8th echo, on grid
    put(s, start + .75, pan=pan * .5, send=.4, gain=.04 * g)


def boom(start, g=1.0, L=2.4):
    t = tt(int(L * SR)); f = 38 + 90 * np.exp(-t * 3.0)
    ph = 2 * np.pi * np.cumsum(f) / SR
    s = np.sin(ph) * np.exp(-t * 1.6)
    n = lp(rng.standard_normal(len(t)), 900) * np.exp(-t * 4) * .5
    put(s + n, start, send=.45, gain=.85 * g)
    i = int(start * SR); duck_src[i:i + 1] += 1.5


def riser(start, L, g=1.0):
    n = int(L * SR); t = tt(n); x = rng.standard_normal(n)
    fc = 300 * (4000 / 300) ** (t / L)  # sweep (applied by blocks)
    out = np.zeros(n); blk = 2048
    for i in range(0, n, blk):
        seg = x[i:i + blk]; c = fc[min(i, n - 1)]
        out[i:i + len(seg)] = hp(seg, c * .6, 1)
    env = (t / L) ** 2.2
    put(out * env, start, pan=0, send=.5, gain=.16 * g)


def whoosh_rev(end, L=.6, g=1.0):
    n = int(L * SR); t = tt(n); x = hp(lp(rng.standard_normal(n), 5500), 500)
    put(x * (t / L) ** 2 * np.exp(-0), end - L, send=.35, gain=.13 * g)


def blip(start, f, g=1.0, pan=0.0):
    t = tt(int(.22 * SR)); s = np.sin(2 * np.pi * f * t) * np.exp(-t * 22) + .3 * np.sin(2 * np.pi * f * 2 * t) * np.exp(-t * 40)
    put(s, start, pan=pan, send=.45, gain=.10 * g)


def tick(start, g=1.0):
    t = tt(int(.02 * SR)); s = hp(rng.standard_normal(len(t)), 3500) * np.exp(-t * 220)
    put(s, start, gain=.09 * g, send=.15)


# --------------------------------------------------------------- arrangement
chords = [  # Am F C G, one bar each
    dict(root=45, pad=[57, 60, 64, 69], arp=[69, 72, 76, 81]),
    dict(root=41, pad=[53, 57, 60, 65], arp=[65, 69, 72, 77]),
    dict(root=48, pad=[55, 60, 64, 67], arp=[67, 72, 76, 79]),
    dict(root=43, pad=[55, 59, 62, 67], arp=[67, 71, 74, 79]),
]
bars = int(DUR / BAR)
KICK_ON = [(12, 51), ]   # kick from the drop to the stripped-back moment
def in_kick(t): return 12 <= t < 51 or 54 <= t < 56  # 51-54 stripped (OVV beat), 54-56 back in

for b in range(bars):
    t0 = b * BAR; c = chords[b % 4]
    # sub drone / pad
    if t0 < 2.5:
        pass
    elif t0 < 12:
        pad(t0, c['pad'][:3], BAR, g=.55 + .35 * min(1, (t0 - 2) / 8), bright=900 + 100 * b)
    elif t0 < 57:
        pad(t0, c['pad'], BAR, g=.85, bright=1800)
    # bass
    if 12 <= t0 < 56:
        for k in range(4):
            bass(t0 + k * BEAT, midi(c['root']) * (1 if k != 3 else 2 if b % 2 else 1), L=.46, g=1.0)
    elif 5 <= t0 < 12:
        bass(t0, midi(c['root']) * .5 + 0, L=1.8, g=.8)

# opening drone on A1 + the tick-up of the 100 MB counter
t = tt(int(2.6 * SR)); drone = np.sin(2 * np.pi * 55 * t) * np.minimum(1, t / 1.2) * .5
put(drone, 0, send=.2, gain=.9)
for k in range(13):                       # counter ticks 0.1 -> 0.9 s
    tick(.1 + k * .0625, g=.9)
boom(2.5, 1.0)                            # 100 MB -> 1.2 KB
put(np.sin(2 * np.pi * midi(93) * tt(int(.4 * SR))) * np.exp(-tt(int(.4 * SR)) * 9), 2.5, send=.6, gain=.06)

# sparse plucks 5-12 (one per bar, A pentatonic)
for b, f in zip(range(5, 12, 1), [81, 76, 72, 76, 79, 76, 81]):
    pass
for k, bt in enumerate([5.0, 6.0, 7.0, 8.0, 9.0, 10.0, 11.0]):
    pluck(bt + .0, midi([81, 76, 72, 76, 79, 74, 76][k]), g=.8, pan=(-.4 if k % 2 else .4))
riser(9.5, 2.5, g=1.0)
for k in range(8):                        # snare-ish roll into the drop
    hat(11.0 + k * .125, g=.5 + k * .1)
whoosh_rev(12.0, .8)

# the drop
boom(12.0, 1.0)

for b in range(bars):
    t0 = b * BAR; c = chords[b % 4]
    for k in range(4):                    # four-on-the-floor
        bt = t0 + k * BEAT
        if in_kick(bt): kick(bt, g=1.0 if k else 1.0)
        if 14 <= bt < 51 or 54 <= bt < 56:
            if k in (1, 3): clap(bt, g=1.0 if bt >= 17 else .7)
        if 16 <= bt < 56:
            hat(bt + .25, g=.9 if k % 2 else .7, open_=(k == 3 and bt >= 27), pan=.25)
        if 27 <= bt < 56:                 # 16ths
            hat(bt + .125, g=.5, pan=-.2); hat(bt + .375, g=.5, pan=.2)
    # arp 8ths from S4 on
    if 17 <= t0 < 56:
        order = [0, 1, 2, 3, 2, 1, 2, 3]
        for k in range(8):
            f = midi(c['arp'][order[k]])
            if t0 >= 27: f *= 1
            pluck(t0 + k * .25, f, g=(.85 if t0 < 27 else 1.0), pan=(-.45 if k % 2 else .45))
    # sparse melody on strong beats in the second half
    if 36 <= t0 < 51:
        pluck(t0, midi(c['arp'][3] + 12) / 1, g=.55, pan=0, L=.9)

# transitions: reverse-swell into every scene boundary (except the drop which has its own)
for s in SCENES[1:]:
    if s[0] in (12, 57): continue
    whoosh_rev(s[0], .5, g=.9)

# UI blips on the visual cues, same key (A minor pentatonic), alternating pan
pent = [81, 84, 88, 91, 93]
for k, ct in enumerate(CUES):
    if ct < 3 or ct in (12.0, 57.0): continue
    blip(ct, midi(pent[k % len(pent)]), g=.9, pan=(-.35 if k % 2 else .35))

# final hit + resolve on A minor
boom(57.0, 1.1, L=3.0)
pad(57.0, [45, 57, 60, 64, 69], 2.0, g=1.0, bright=2200)
for k, m in enumerate([81, 76, 72, 69]):
    pluck(57.5 + k * .25, midi(m), g=.8, pan=(.4 if k % 2 else -.4), L=.8)

# ---------------------------------------------------------------- mix
# reverb (stereo noise IR, 1.7 s)
irn = int(1.7 * SR); ti = tt(irn)
IR = np.stack([rng.standard_normal(irn) * np.exp(-ti * 3.2) for _ in range(2)])
IR = np.stack([lp(IR[0], 5500), lp(IR[1], 5500)]) * .06
sz = 1 << int(np.ceil(np.log2(N + irn)))
rev = np.stack([np.fft.irfft(np.fft.rfft(wet[c], sz) * np.fft.rfft(IR[c], sz), sz)[:N] for c in range(2)])

# sidechain duck from kicks (applied to everything but the kick: approximated on the pad/bass/arp via the shared bus)
env = np.zeros(N); kidx = np.nonzero(duck_src)[0]
for i in kidx:
    L = int(.22 * SR); e = np.arange(min(L, N - i)) / L
    env[i:i + len(e)] = np.maximum(env[i:i + len(e)], (1 - e) ** 2 * min(1, duck_src[i]))
duck = 1 - .35 * env
out = dry * duck + rev * 1.0
# intro fade-in and final tail fade
fade_in = np.minimum(1, tt(N) / .05); fade_out = np.minimum(1, (DUR - tt(N)) / 1.0)
out *= fade_in * fade_out
# soft clip then normalize
out = np.tanh(out * 1.15)
out /= np.max(np.abs(out)) / .89
pcm = (out.T * 32767).astype('<i2')
with wave.open('music.wav', 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
print('ok', N / SR, 'peak', float(np.max(np.abs(out))))
