# spectral_motion.py : measures how much a filter moves the sound, so the owner's "the filter is much more apparent
# in the original" can be seen in numbers. A moving filter makes the overall SHAPE of the spectrum move over time.
# For each 23 ms step: the spectrum in 1/6 octave bands (100 Hz to 8 kHz, which smooths away single harmonics), in dB,
# minus that moment's average level (so loudness changes do not count), minus each band's long-term average (so the
# fixed EQ does not count), lightly smoothed over 3 steps. What is left is how the shape moves.
#   movement per band : how far each band swings up and down over time (standard deviation, dB)
#   where it moves    : the band range that moves most, which shows the filter's sweep range
# The renders play the same notes, so movement the stem has beyond the renders is the filter (or other effects).
# usage: python spectral_motion.py FILE [FILE ...]
import sys, numpy as np
from pedalboard.io import AudioFile

N, HOP = 2048, 1024
edges = 100 * 2 ** (np.arange(0, np.log2(8000 / 100) + 1e-9, 1 / 6)); cen = np.sqrt(edges[:-1] * edges[1:])
show = [i for i in range(len(cen)) if i % 3 == 0]
print('movement per band (dB) at ' + ' '.join(f'{cen[i]:5.0f}' for i in show) + ' Hz')
for path in sys.argv[1:]:
    with AudioFile(path) as f:
        y, sr = f.read(f.frames)[0], f.samplerate
    fr = np.fft.rfftfreq(N, 1 / sr); w = np.hanning(N)
    P = np.abs(np.fft.rfft(np.array([y[i:i + N] * w for i in range(0, len(y) - N, HOP)]), axis=1)) ** 2
    lv = 10 * np.log10(P.sum(1) + 1e-20); P = P[lv > lv.max() - 20]
    B = 10 * np.log10(np.array([[p[(fr >= a) & (fr < b)].sum() for a, b in zip(edges[:-1], edges[1:])] for p in P]) + 1e-20)
    B -= B.mean(1, keepdims=True); B -= B.mean(0)
    B = np.array([np.convolve(B[:, j], np.ones(3) / 3, mode='same') for j in range(B.shape[1])]).T
    sd = B.std(0)
    top = np.argsort(sd)[::-1][:4]
    print(f'{path.split(chr(92))[-1]:26s} overall {np.sqrt(np.mean(sd ** 2)):4.2f} | ' + ' '.join(f'{sd[i]:5.1f}' for i in show)
          + f' | moves most at {", ".join(f"{cen[i]:.0f}" for i in sorted(top))} Hz')
