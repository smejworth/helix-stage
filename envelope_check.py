# envelope_check.py : tests whether the stem has an envelope filter (a filter whose frequency follows how hard
# you play: it opens on each pick attack and closes as the note dies, like an auto-wah).
# Stem and render play the same riff, lined up in time, so dividing one by the other frame by frame removes the
# notes and leaves what the stem's extra processing does. For each frame (about 46 ms) it finds where that
# extra boost sits (the weighted centre of the stem-over-render difference, 200 Hz to 6 kHz), then checks whether
# that frequency moves with the stem's loudness and with time since the last pick attack.
# It also prints the stem's own brightness against loudness for the same frames, and the same for the render.
# usage: python envelope_check.py STEM RENDER CLEAN_TAKE
import sys, numpy as np
from pedalboard.io import AudioFile

def load(p):
    with AudioFile(p) as f:
        return f.read(f.frames)[0], f.samplerate
a, sr = load(sys.argv[1]); b, _ = load(sys.argv[2])
N, HOP = 2048, 1024
fr = np.fft.rfftfreq(N, 1 / sr)
edges = 200 * 2 ** (np.arange(0, np.log2(6000 / 200) + 1e-9, 1 / 6)); cen = np.sqrt(edges[:-1] * edges[1:])
def bands(y):
    w = np.hanning(N)
    P = np.abs(np.fft.rfft(np.array([y[i:i + N] * w for i in range(0, len(y) - N, HOP)]), axis=1)) ** 2
    return P, np.array([[p[(fr >= lo) & (fr < hi)].sum() for lo, hi in zip(edges[:-1], edges[1:])] for p in P])
PA, A = bands(a); PB, B = bands(b)
n = min(len(A), len(B)); A, B, PA, PB = A[:n], B[:n], PA[:n], PB[:n]
la = 10 * np.log10(PA.sum(1) + 1e-20); lb = 10 * np.log10(PB.sum(1) + 1e-20)
k = la > la.max() - 25
D = 10 * np.log10(A + 1e-20) - 10 * np.log10(B + 1e-20)
D -= D[k].mean(axis=0)                     # remove the fixed difference (the EQ already handles that)
D -= D.mean(axis=1, keepdims=True)
wpos = np.clip(D, 0, None) + 1e-9
fc = np.exp((np.log(cen) * wpos).sum(1) / wpos.sum(1))     # where the stem's extra boost sits, per frame
# time since the last pick attack, found in the clean take (third file), which is lined up with the other two.
# "Spectral flux": how much new energy appears from one frame to the next; a pick attack makes a sharp jump.
c_, _ = load(sys.argv[3])
PC = np.abs(np.fft.rfft(np.array([c_[i:i + N] * np.hanning(N) for i in range(0, len(c_) - N, HOP)]), axis=1))[:n]
flux = np.r_[0, np.clip(np.diff(np.log(PC + 1e-9), axis=0), 0, None).sum(1)]
thr = np.median(flux) + 2 * np.std(flux)
att = np.r_[False, (flux[1:-1] > thr) & (flux[1:-1] >= flux[:-2]) & (flux[1:-1] >= flux[2:]), False]
since = np.zeros(n); t = 99.0
for i in range(n):
    t = 0.0 if att[i] else t + HOP / sr; since[i] = t
cs = lambda P: (P * fr).sum(1) / (P.sum(1) + 1e-20)
r = lambda x, y: np.corrcoef(x[k], y[k])[1, 0]
print(f'frames used {k.sum()}, attacks found {att.sum()}')
print(f'extra-boost frequency: median {np.median(fc[k]):.0f} Hz, 10th to 90th percentile {np.percentile(fc[k], 10):.0f} to {np.percentile(fc[k], 90):.0f} Hz')
print(f'  correlation with stem loudness:       {r(fc, la):+.2f}')
print(f'  correlation with time since attack:   {r(fc, np.minimum(since, 0.5)):+.2f}')
print(f'stem brightness (centroid) vs its loudness:     {r(cs(PA), la):+.2f}')
print(f'render brightness (centroid) vs its loudness:   {r(cs(PB), lb):+.2f}')
print(f'stem brightness vs time since attack:           {r(cs(PA), np.minimum(since, 0.5)):+.2f}')
print(f'render brightness vs time since attack:         {r(cs(PB), np.minimum(since, 0.5)):+.2f}')
print('average over frames grouped by time since attack (s): stem centroid, render centroid, extra-boost freq')
for lo, hi in ((0, 0.05), (0.05, 0.1), (0.1, 0.2), (0.2, 0.35), (0.35, 99)):
    m = k & (since >= lo) & (since < hi)
    if m.sum():
        print(f'  {lo:4.2f} to {min(hi, 9):4.2f}: {np.median(cs(PA)[m]):6.0f}  {np.median(cs(PB)[m]):6.0f}  {np.median(fc[m]):6.0f}   ({m.sum()} frames)')
