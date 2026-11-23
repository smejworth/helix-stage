# stick_out.py : finds single frequencies that stick out of a recording (a ringing resonance, a whistle, a honk).
# Uses a long FFT (about 1.5 s, 0.7 Hz per step) averaged over the clip, smooths it over one octave to get the
# broad shape, and lists the narrow peaks that rise above that shape. Done for the stem and for a render, then
# for the stem minus the render, so peaks the stem has and the render lacks stand out.
# Peaks are also checked against the notes of drop A tuning (A1 = 55 Hz), since a note's harmonics also make peaks.
# usage: python stick_out.py STEM RENDER
import sys, numpy as np
from pedalboard.io import AudioFile
from scipy.signal import find_peaks

def load(p):
    with AudioFile(p) as f:
        return f.read(f.frames)[0], f.samplerate
s, sr = load(sys.argv[1]); r, _ = load(sys.argv[2])
N = 65536
fr = np.fft.rfftfreq(N, 1 / sr); w = np.hanning(N)
def spec(y):
    return 10 * np.log10(np.mean(np.abs(np.fft.rfft([y[i:i + N] * w for i in range(0, len(y) - N, N // 8)], axis=1)) ** 2, axis=0) + 1e-20)
S, R = spec(s), spec(r)
# put the spectrum on a log frequency grid (1/96 octave) from 60 Hz to 12 kHz
g = 60 * 2 ** (np.arange(0, np.log2(12000 / 60), 1 / 96))
Sg, Rg = np.interp(g, fr, S), np.interp(g, fr, R)
def resid(x):
    trend = np.convolve(x, np.ones(97) / 97, mode='same')     # one octave running average
    return (x - trend)[48:-48], g[48:-48]
NOTES = ['A', 'A#', 'B', 'C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#']
def note(f):
    k = 12 * np.log2(f / 55.0); i = int(round(k))
    return f'{NOTES[i % 12]}{1 + (i + 9) // 12} {100 * (k - i):+.0f}c'
for name, x in (('stem', Sg), ('render', Rg), ('stem minus render', Sg - Rg)):
    rr, gg = resid(x)
    pk, pr = find_peaks(rr, prominence=3, distance=8)
    top = pk[np.argsort(pr['prominences'])[::-1][:10]]
    print(f'{name}: biggest narrow peaks above the broad shape')
    for i in sorted(top, key=lambda i: -rr[i]):
        print(f'   {gg[i]:7.0f} Hz  {rr[i]:+5.1f} dB above trend   nearest note {note(gg[i])}')
