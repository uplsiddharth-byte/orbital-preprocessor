"""Mix voiceover over the music with ducking. Needs numpy + soundfile."""
import numpy as np, soundfile as sf
SR = 44100
import sys
VF = sys.argv[1] if len(sys.argv) > 1 else 'voice_raw.wav'; OUT = sys.argv[2] if len(sys.argv) > 2 else 'mix.wav'
m, _ = sf.read('music.wav'); v, _ = sf.read(VF)
n = min(len(m), len(v)); m = m[:n]; v = v[:n]
def hp(x, fc, order=2):
    X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / SR); r = (f / fc) ** (2 * order)
    return np.fft.irfft(X * np.sqrt(r / (1 + r)), len(x))
v = hp(v, 85)
# presence lift: +3 dB around 2-4 kHz via gentle band boost
X = np.fft.rfft(v); f = np.fft.rfftfreq(len(v), 1 / SR)
X *= 1 + .41 * np.exp(-((np.log2(np.maximum(f, 1) / 3000)) ** 2) / .5); v = np.fft.irfft(X, len(v))
# envelope follower (10 ms blocks): fast attack, slow release
blk = int(.01 * SR); nb = n // blk
rms = np.sqrt((v[:nb * blk].reshape(nb, blk) ** 2).mean(1))
act = (rms > .012).astype(float); g = np.zeros(nb); cur = 0
for i in range(nb):
    a = .35 if act[i] > cur else .015     # attack ~30 ms, release ~650 ms
    cur += (act[i] - cur) * a; g[i] = cur
gain_blk = 1 - g * (1 - 10 ** (-7.5 / 20))      # music -7.5 dB under voice
gain = np.interp(np.arange(n), (np.arange(nb) + .5) * blk, gain_blk)
v *= 0.90                                       # voice level relative to music
mix = m * gain[:, None] + v[:, None]
mix = np.tanh(mix * 1.05); mix /= max(1e-9, np.abs(mix).max()) / .89
sf.write(OUT, mix, SR, subtype='PCM_16')
print('mix ok', np.abs(mix).max())
