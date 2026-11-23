# narrow_peaks.py : looks for a narrow fixed filter (a sharp resonant peak or notch) that the 1/6 octave EQ fit
# could not see. It takes the long term spectrum of stem minus render at fine resolution (1/24 octave), removes
# the broad trend (a running average over one octave), and lists what sticks out.
# usage: python narrow_peaks.py STEM RENDER
import sys, numpy as np
from pedalboard.io import AudioFile

def load(p):
    with AudioFile(p) as f:
        return f.read(f.frames)[0], f.samplerate
a, sr = load(sys.argv[1]); b, _ = load(sys.argv[2])
N = 16384
fr = np.fft.rfftfreq(N, 1 / sr)
w = np.hanning(N)
def spec(y):
    return np.mean(np.abs(np.fft.rfft([y[i:i + N] * w for i in range(0, len(y) - N, N // 4)], axis=1)) ** 2, axis=0)
edges = 60 * 2 ** (np.arange(0, np.log2(16000 / 60) + 1e-9, 1 / 24))
cen = np.sqrt(edges[:-1] * edges[1:])
def binned(P):
    return np.array([10 * np.log10(P[(fr >= lo) & (fr < hi)].mean() + 1e-20) for lo, hi in zip(edges[:-1], edges[1:])])
d = binned(spec(a)) - binned(spec(b))
trend = np.convolve(d, np.ones(25) / 25, mode='same')     # 25 bins of 1/24 octave = about one octave
r = (d - trend)[12:-12]; c = cen[12:-12]
print(f'fine detail of stem minus render after removing the broad trend: std {r.std():.1f} dB')
o = np.argsort(r)
print('largest narrow peaks in the stem (dB above trend):', ', '.join(f'{c[i]:.0f} Hz {r[i]:+.1f}' for i in o[::-1][:8]))
print('largest narrow dips in the stem (dB below trend): ', ', '.join(f'{c[i]:.0f} Hz {r[i]:+.1f}' for i in o[:8]))
print('above 1 kHz only, per 1/24 octave:')
for ci, ri in zip(c, r):
    if ci > 1000:
        print(f'  {ci:6.0f} Hz {ri:+5.1f} ' + ('+' * int(round(ri * 2)) if ri > 0 else '-' * int(round(-ri * 2))))
