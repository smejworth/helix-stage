# phrase_sweep.py : looks for a filter that opens and closes over a musical phrase rather than a single note.
# It measures brightness (spectral centroid) every 0.1 s for the stem and a render, finds how long the riff
# repeats (autocorrelation of the clean take's loudness), then folds the clip at that length and averages, so
# each riff repeat is laid on top of the others. A filter closing shows as brightness falling through the repeat.
# Also prints where in the repeat the energy sits (low 150 to 600 Hz, mid 600 to 2000 Hz, high 2 to 6 kHz).
# usage: python phrase_sweep.py STEM RENDER CLEAN_TAKE
import sys, numpy as np
from pedalboard.io import AudioFile

def load(p):
    with AudioFile(p) as f:
        return f.read(f.frames)[0], f.samplerate
s, sr = load(sys.argv[1]); r, _ = load(sys.argv[2]); c, _ = load(sys.argv[3])
N, HOP = 4096, int(0.1 * sr)
fr = np.fft.rfftfreq(N, 1 / sr); w = np.hanning(N)
def frames(y):
    return np.abs(np.fft.rfft(np.array([y[i:i + N] * w for i in range(0, len(y) - N, HOP)]), axis=1)) ** 2
PS, PR, PC = frames(s), frames(r), frames(c)
n = min(len(PS), len(PR), len(PC))
cent = lambda P: (P * fr).sum(1) / (P.sum(1) + 1e-20)
def share(P, a, b):
    return 10 * np.log10(P[:, (fr >= a) & (fr < b)].sum(1) / (P[:, (fr >= 150) & (fr < 6000)].sum(1) + 1e-20) + 1e-20)
env = 10 * np.log10(PC[:n].sum(1) + 1e-20); env -= env.mean()
ac = [np.sum(env[:n - L] * env[L:]) / (n - L) for L in range(n // 2)]
L = int(np.argmax(ac[10:]) + 10)            # repeat length in frames, at least 1 s
if len(sys.argv) > 4:                        # optional 4th argument: force the repeat length in seconds
    L = int(round(float(sys.argv[4]) / 0.1))
print(f'riff repeats every {L * 0.1:.1f} s (clip {n * 0.1:.1f} s, {n // L} full repeats)')
reps = n // L
def fold(x):
    return np.mean([x[k * L:(k + 1) * L] for k in range(reps)], axis=0)
cs, cr = fold(cent(PS[:n])), fold(cent(PR[:n]))
hs, hr = fold(share(PS[:n], 2000, 6000)), fold(share(PR[:n], 2000, 6000))
ms, mr = fold(share(PS[:n], 600, 2000)), fold(share(PR[:n], 600, 2000))
ls_, lr = fold(share(PS[:n], 150, 600)), fold(share(PR[:n], 150, 600))
lv = fold(10 * np.log10(PS[:n].sum(1) + 1e-20)); lv -= lv.max()
print(' time  stem level | centroid stem render | 2-6k share stem render | 600-2k stem render | 150-600 stem render')
for i in range(L):
    print(f'{i * 0.1:5.1f}  {lv[i]:+5.1f}     |   {cs[i]:6.0f} {cr[i]:6.0f}      |   {hs[i]:+6.1f} {hr[i]:+6.1f}         |  {ms[i]:+5.1f} {mr[i]:+5.1f}      |  {ls_[i]:+5.1f} {lr[i]:+5.1f}')
print(f'how much brightness swings through the repeat: stem {cs.max() - cs.min():.0f} Hz, render {cr.max() - cr.min():.0f} Hz')
print(f'correlation of stem and render brightness through the repeat: {np.corrcoef(cs, cr)[1, 0]:+.2f}')
