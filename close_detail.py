# close_detail.py : zooms in on the end of each riff repeat, where the stem drops by about 30 dB, to see HOW it goes
# quiet. If a low-pass filter is closing, the highs die first, then the mids, then the lows, one after the other.
# If the guitar is simply muted, all bands drop together.
# It folds the clip at the riff length (1.2 s, measured by phrase_sweep.py) and prints, every 20 ms from 0.7 s to the
# end of the repeat, the absolute level (dB) of four bands for the stem and for a render.
# usage: python close_detail.py STEM RENDER [REPEAT_SECONDS]
import sys, numpy as np
from pedalboard.io import AudioFile

def load(p):
    with AudioFile(p) as f:
        return f.read(f.frames)[0], f.samplerate
s, sr = load(sys.argv[1]); r, _ = load(sys.argv[2])
rep = float(sys.argv[3]) if len(sys.argv) > 3 else 1.2
N, HOP = 1024, int(0.02 * sr)
fr = np.fft.rfftfreq(N, 1 / sr); w = np.hanning(N)
BANDS = [(40, 150), (150, 600), (600, 2000), (2000, 6000)]
def lv(y):
    P = np.abs(np.fft.rfft(np.array([y[i:i + N] * w for i in range(0, len(y) - N, HOP)]), axis=1)) ** 2
    return np.array([10 * np.log10(P[:, (fr >= a) & (fr < b)].sum(1) + 1e-20) for a, b in BANDS]).T
S, R = lv(s), lv(r)
n = min(len(S), len(R)); L = int(round(rep / 0.02)); reps = n // L
fold = lambda X: np.mean([X[k * L:(k + 1) * L] for k in range(reps)], axis=0)
FS, FR = fold(S[:n]), fold(R[:n]); top = max(FS.max(), FR.max())
FS -= FS.max(); FR -= FR.max()
print(f'{reps} repeats of {rep} s folded. Levels in dB below each file\'s loudest band.')
print('  time | stem: 40-150  150-600  600-2k  2k-6k | render: 40-150  150-600  600-2k  2k-6k')
for i in range(int(0.7 / 0.02), L):
    print(f'{i * 0.02:6.2f} |      ' + '  '.join(f'{v:+6.1f}' for v in FS[i]) + '  |        ' + '  '.join(f'{v:+6.1f}' for v in FR[i]))
