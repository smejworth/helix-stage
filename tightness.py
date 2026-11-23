# tightness.py : measures how "tight and distinct" a guitar sound is against how "mushy" it is.
# Uses the pick attacks of the clean take (the loop's timing, shared by all files) as markers, then for each file:
#   attack jump   : how much new sound appears at each pick (spectral flux at the attack frame divided by the
#                   median flux; bigger = each note starts more clearly)
#   low ring      : level of 80 to 300 Hz in the 60 ms just before each pick, relative to the 60 ms after it
#                   (dB; more negative = the old note's low end has died before the next note = tighter)
#   mid ring      : the same for 300 Hz to 1.5 kHz
#   smear         : how alike consecutive 20 ms spectra are on average (correlation; higher = sound blurs together)
# usage: python tightness.py CLEAN_TAKE FILE [FILE ...]
import sys, numpy as np
from pedalboard.io import AudioFile

def load(p):
    with AudioFile(p) as f:
        return f.read(f.frames)[0], f.samplerate
c, sr = load(sys.argv[1])
N, HOP = 1024, int(0.01 * sr)
fr = np.fft.rfftfreq(N, 1 / sr); w = np.hanning(N)
spec = lambda y: np.abs(np.fft.rfft(np.array([y[i:i + N] * w for i in range(0, len(y) - N, HOP)]), axis=1)) ** 2
flux = lambda P: np.r_[0, np.clip(np.diff(np.log(P + 1e-9), axis=0), 0, None).sum(1)]
fc = flux(spec(c))
pk = [i for i in range(3, len(fc) - 3) if fc[i] == fc[i - 3:i + 4].max() and fc[i] > np.median(fc) + 2.5 * np.std(fc)]
print(f'{len(pk)} pick attacks found in the clean take')
for path in sys.argv[2:]:
    y, _ = load(path); P = spec(y)[:len(fc)]; f_ = flux(P)
    jump = np.median([f_[max(0, i - 2):i + 3].max() for i in pk]) / np.median(f_)
    def ring(a, b):
        band = 10 * np.log10(P[:, (fr >= a) & (fr < b)].sum(1) + 1e-20)
        return np.median([band[max(0, i - 7):i - 1].mean() - band[i + 1:i + 7].mean() for i in pk if i > 8 and i + 7 < len(band)])
    L = np.log(P[:, (fr >= 80) & (fr < 6000)] + 1e-9)
    sm = np.mean([np.corrcoef(L[i], L[i + 2])[0, 1] for i in range(0, len(L) - 2, 3)])
    print(f'{path.split(chr(92))[-1]:28s} attack jump {jump:4.2f}   low ring {ring(80, 300):+5.1f} dB   mid ring {ring(300, 1500):+5.1f} dB   smear {sm:.3f}')
