# steady_peaks.py : separates fixed resonances (a frequency that rings out whatever note is played, like a honk
# from a speaker, a filter or a wah left in one place) from note harmonics (which come and go with the notes).
# For each short frame (about 0.19 s) it finds how far each frequency rises above the local shape of that frame's
# spectrum, then reports the frequencies that stick out in most frames. A fixed resonance sticks out nearly always.
# usage: python steady_peaks.py FILE [FILE ...]
import sys, numpy as np
from pedalboard.io import AudioFile

N, HOP = 8192, 4096
g = 100 * 2 ** (np.arange(0, np.log2(8000 / 100), 1 / 48))   # 1/48 octave grid, 100 Hz to 8 kHz
for path in sys.argv[1:]:
    with AudioFile(path) as f:
        y, sr = f.read(f.frames)[0], f.samplerate
    fr = np.fft.rfftfreq(N, 1 / sr); w = np.hanning(N)
    P = np.abs(np.fft.rfft(np.array([y[i:i + N] * w for i in range(0, len(y) - N, HOP)]), axis=1)) ** 2
    lv = 10 * np.log10(P.sum(1) + 1e-20); P = P[lv > lv.max() - 20]
    res = []
    for p in P:
        x = np.interp(g, fr, 10 * np.log10(p + 1e-20))
        x = np.convolve(x, np.ones(5) / 5, mode='same')          # light smoothing so one FFT bin does not count
        res.append(x - np.convolve(x, np.ones(25) / 25, mode='same'))   # minus the half-octave shape
    res = np.array(res)[:, 12:-12]; gg = g[12:-12]
    often = (res > 3).mean(0); mean = res.mean(0)
    order = np.argsort(mean)[::-1]
    picked = []
    for i in order:
        if all(abs(np.log2(gg[i] / gg[j])) > 1 / 12 for j in picked):
            picked.append(i)
        if len(picked) == 8:
            break
    print(f'{path.split(chr(92))[-1]} ({len(P)} frames): frequencies that stick out on average')
    for i in sorted(picked, key=lambda i: -mean[i]):
        print(f'   {gg[i]:6.0f} Hz  average {mean[i]:+4.1f} dB above local shape, more than 3 dB above in {100 * often[i]:3.0f}% of frames')
