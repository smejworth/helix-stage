# wah_measure.py : measures the "wow wow" of a wah or envelope filter: a sharp resonant peak that moves.
# For each short frame (46 ms) it looks between 250 Hz and 3 kHz for the highest narrow peak above the local shape
# of the spectrum (a half-octave running average), smoothed a little so single harmonics count less.
#   peak height : how sharp the resonance is (dB above the local shape), median over frames
#   peak travel : how far the peak's frequency moves from frame to frame (octaves, median), and its overall spread
# A strong "wow" has a tall peak that travels a lot. Prints these for each file.
# usage: python wah_measure.py FILE [FILE ...]
import sys, numpy as np
from pedalboard.io import AudioFile

N, HOP = 2048, 1024
g = 250 * 2 ** (np.arange(0, np.log2(3000 / 250), 1 / 24))
for path in sys.argv[1:]:
    with AudioFile(path) as f:
        y, sr = f.read(f.frames)[0], f.samplerate
    fr = np.fft.rfftfreq(N, 1 / sr); w = np.hanning(N)
    P = np.abs(np.fft.rfft(np.array([y[i:i + N] * w for i in range(0, len(y) - N, HOP)]), axis=1)) ** 2
    lv = 10 * np.log10(P.sum(1) + 1e-20); P = P[lv > lv.max() - 20]
    hts, fqs = [], []
    for p in P:
        x = np.interp(g, fr, 10 * np.log10(p + 1e-20))
        x = np.convolve(x, np.ones(3) / 3, mode='same')
        r = x - np.convolve(x, np.ones(13) / 13, mode='same')
        r = r[6:-6]; gg = g[6:-6]; i = int(np.argmax(r))
        hts.append(r[i]); fqs.append(gg[i])
    fqs = np.array(fqs); hts = np.array(hts)
    travel = np.abs(np.diff(np.log2(fqs)))
    print(f'{path.split(chr(92))[-1]:30s} peak height {np.median(hts):4.1f} dB   frame-to-frame travel {np.median(travel):.2f} oct   '
          f'spread {np.log2(np.percentile(fqs, 90) / np.percentile(fqs, 10)):.2f} oct ({np.percentile(fqs, 10):.0f} to {np.percentile(fqs, 90):.0f} Hz)')
