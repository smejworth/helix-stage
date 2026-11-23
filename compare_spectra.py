# compare_spectra.py : where do the stem and the Helix renders differ in frequency balance?
# For each file it prints the level in octave-wide bands (relative to the file's own total, so loudness
# does not matter), the spectral centroid (higher = brighter), and the strongest peaks below 600 Hz
# from the average spectrum (a rough look at which low notes are present).
# usage: python compare_spectra.py [FOLDER FILE FILE ...]   (folder inside work; default is the helix01 set)
import os, sys, numpy as np
from pedalboard.io import AudioFile
if len(sys.argv) > 2:
    D, files = os.path.join('work', sys.argv[1]), sys.argv[2:]
else:
    D = os.path.join('work', 'helix01')
    files = ['1_target_stem.wav', '2_dry_played.wav', '3_oct_on_sustain2.wav', '5_oct_on_sustain8.wav', '7_oct_off_sustain8.wav']
edges = [20, 40, 80, 160, 320, 640, 1280, 2560, 5120, 10240, 20000]

def avg_spectrum(x, sr, n=8192):
    # average power spectrum over many short windows (Welch's method, done by hand)
    w = np.hanning(n); hop = n // 2
    frames = [x[i:i + n] * w for i in range(0, len(x) - n, hop)]
    P = np.mean(np.abs(np.fft.rfft(frames, axis=1)) ** 2, axis=0)
    return np.fft.rfftfreq(n, 1 / sr), P

print('band Hz        ' + '  '.join(f'{f[:12]:>12s}' for f in files))
spec = {}
for f in files:
    with AudioFile(os.path.join(D, f)) as a:
        spec[f] = avg_spectrum(a.read(a.frames)[0], a.samplerate)
for lo, hi in zip(edges[:-1], edges[1:]):
    row = []
    for f in files:
        fr, P = spec[f]
        row.append(10 * np.log10(np.sum(P[(fr >= lo) & (fr < hi)]) / np.sum(P) + 1e-12))
    print(f'{lo:>5d}-{hi:<6d}  ' + '  '.join(f'{v:12.1f}' for v in row))
print('centroid Hz    ' + '  '.join(f'{np.sum(spec[f][0] * spec[f][1]) / np.sum(spec[f][1]):12.0f}' for f in files))
print()
for f in files:
    fr, P = spec[f]
    m = (fr > 40) & (fr < 600)
    idx = np.where(m)[0]
    # local maxima, keep the 8 strongest
    pk = [i for i in idx if P[i] > P[i - 1] and P[i] > P[i + 1]]
    pk = sorted(pk, key=lambda i: -P[i])[:8]
    print(f'{f:24s} strongest peaks below 600 Hz: ' + ', '.join(f'{fr[i]:.0f}' for i in sorted(pk)))
