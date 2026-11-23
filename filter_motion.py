# filter_motion.py : isolates what a filter adds to the sound's movement, removing the notes.
# A render with the same chain but NO filter carries everything the notes and amp do. Subtracting its spectral shape
# frame by frame from another file leaves what that file's extra processing does (for the stem: its filter, plus
# differences in playing). The 4 riff repeats are then averaged (the take is an exact 2.4 s loop and the stem follows
# the same riff), which cancels one-off playing differences and keeps what repeats with the riff, such as a filter
# following the notes. Printed per 1/6 octave band: how much that repeating extra shape moves (dB, std over the riff),
# and the frequency range where the movement sits.
# usage: python filter_motion.py NO_FILTER_RENDER FILE [FILE ...]
import sys, numpy as np
from pedalboard.io import AudioFile

N, HOP = 2048, 1024
edges = 100 * 2 ** (np.arange(0, np.log2(8000 / 100) + 1e-9, 1 / 6)); cen = np.sqrt(edges[:-1] * edges[1:])
def shape(path):
    with AudioFile(path) as f:
        y, sr = f.read(f.frames)[0], f.samplerate
    fr = np.fft.rfftfreq(N, 1 / sr); w = np.hanning(N)
    P = np.abs(np.fft.rfft(np.array([y[i:i + N] * w for i in range(0, len(y) - N, HOP)]), axis=1)) ** 2
    B = 10 * np.log10(np.array([[p[(fr >= a) & (fr < b)].sum() for a, b in zip(edges[:-1], edges[1:])] for p in P]) + 1e-20)
    return B - B.mean(1, keepdims=True), sr
base, sr = shape(sys.argv[1])
L = int(round(2.4 * sr / HOP)); reps = 3                 # 3 full repeats (the 4th is cut by the clip end)
show = [i for i in range(len(cen)) if i % 3 == 0]
print('repeating extra movement per band (dB) at ' + ' '.join(f'{cen[i]:5.0f}' for i in show) + ' Hz')
for path in sys.argv[2:]:
    B, _ = shape(path); n = min(len(B), len(base))
    D = B[:n] - base[:n]; D -= D.mean(0)
    F = np.mean([D[k * L:(k + 1) * L] for k in range(reps)], axis=0)
    F = np.array([np.convolve(F[:, j], np.ones(3) / 3, mode='same') for j in range(F.shape[1])]).T
    sd = F.std(0); top = np.argsort(sd)[::-1][:5]
    print(f'{path.split(chr(92))[-1]:26s} overall {np.sqrt(np.mean(sd ** 2)):4.2f} | ' + ' '.join(f'{sd[i]:5.1f}' for i in show)
          + f' | most at {", ".join(f"{cen[i]:.0f}" for i in sorted(top))} Hz')
