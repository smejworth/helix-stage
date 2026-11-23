# filter_over_time.py : compares two recordings of the same riff frame by frame, to show a filter that
# the stem has and the render does not. The average difference is already removed by the EQ fit, so
# what is left over time is a filter that moves (wah, sweep, envelope filter) or a resonance that the
# fixed EQ could not follow.
#   1. lines the two files up in time (cross-correlation of their loudness envelopes)
#   2. for each frame (about 0.09 s), the difference stem minus render in 1/6 octave bands, minus its average
#   3. prints, every 0.25 s, the band where the stem is most above the render, and a small band table
# usage: python filter_over_time.py STEM RENDER
import sys, numpy as np
from pedalboard.io import AudioFile

def load(p):
    with AudioFile(p) as f:
        return f.read(f.frames)[0], f.samplerate
a, sr = load(sys.argv[1]); b, _ = load(sys.argv[2])
N, HOP = 4096, 1024
fr = np.fft.rfftfreq(N, 1 / sr)
edges = 80 * 2 ** (np.arange(0, np.log2(12000 / 80) + 1e-9, 1 / 6))
cen = np.sqrt(edges[:-1] * edges[1:])

def bands(y):
    w = np.hanning(N)
    P = np.abs(np.fft.rfft(np.array([y[i:i + N] * w for i in range(0, len(y) - N, HOP)]), axis=1)) ** 2
    return np.array([[p[(fr >= lo) & (fr < hi)].sum() for lo, hi in zip(edges[:-1], edges[1:])] for p in P])

A, B = bands(a), bands(b)
ea, eb = np.log10(A.sum(1) + 1e-20), np.log10(B.sum(1) + 1e-20)
n = min(len(ea), len(eb))
ea_, eb_ = ea[:n] - ea[:n].mean(), eb[:n] - eb[:n].mean()
lags = range(-40, 41)
cc = [np.sum(ea_[max(0, L):n + min(0, L)] * eb_[max(0, -L):n - max(0, L)]) for L in lags]
lag = list(lags)[int(np.argmax(cc))]
print(f'best alignment: render shifted by {lag} frames ({lag * HOP / sr * 1000:.0f} ms); envelope correlation {np.max(cc) / np.sqrt(np.sum(ea_ ** 2) * np.sum(eb_ ** 2)):.2f}')
if lag >= 0:
    A, B = A[lag:], B
else:
    A, B = A, B[-lag:]
n = min(len(A), len(B)); A, B = A[:n], B[:n]
D = 10 * np.log10(A + 1e-20) - 10 * np.log10(B + 1e-20)
D -= D.mean(axis=0)                       # remove the fixed (already EQ'd) difference per band
D -= D.mean(axis=1, keepdims=True)        # remove level changes per frame
loud = 10 * np.log10(A.sum(1) + 1e-20)
k = loud > loud.max() - 30
print(f'frames used {k.sum()} of {n}')
print('how much the stem/render difference moves over time, per band (std, dB):')
sd = D[k].std(axis=0)
for c, s in zip(cen, sd):
    print(f'  {c:6.0f} Hz  {s:4.1f}  ' + '#' * int(round(s * 2)))
print('every 0.25 s: band where the stem is most above the render (dB), and most below')
step = max(1, int(0.25 * sr / HOP))
for s in range(0, n, step):
    m = k[s:s + step]
    if m.sum() == 0:
        continue
    d = D[s:s + step][m].mean(axis=0)
    print(f'{s * HOP / sr:5.2f} s  up {cen[np.argmax(d)]:6.0f} Hz {d.max():+5.1f}   down {cen[np.argmin(d)]:6.0f} Hz {d.min():+5.1f}')
