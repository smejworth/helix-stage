# find_filter.py : looks for a filter in a recording, and whether it stays put or moves.
# It cuts the file into short frames (about 0.09 s) and, for each frame, measures:
#   - the spectral centroid (the "centre of mass" of the frequencies, a rough brightness number)
#   - the strongest peak in the 300 Hz to 5 kHz range of the smoothed spectrum (a filter's resonance shows up here)
# A fixed filter gives a peak that stays at one frequency. A wah, sweep or envelope filter gives a peak that moves.
# An envelope filter (auto wah) also moves with loudness, so it prints how brightness follows loudness.
# Run it on the stem and on a render through the Helix chain (which has no filter) as a control.
# usage: python find_filter.py FILE [FILE ...]
import sys, numpy as np
from pedalboard.io import AudioFile

N, HOP = 4096, 1024
for path in sys.argv[1:]:
    with AudioFile(path) as f:
        y, sr = f.read(f.frames)[0], f.samplerate
    fr = np.fft.rfftfreq(N, 1 / sr)
    w = np.hanning(N)
    frames = np.array([y[i:i + N] * w for i in range(0, len(y) - N, HOP)])
    P = np.abs(np.fft.rfft(frames, axis=1)) ** 2
    loud = 10 * np.log10(P.sum(axis=1) + 1e-20)
    keep = loud > loud.max() - 30                    # ignore near silent frames
    t = np.arange(len(P)) * HOP / sr
    # 1/12 octave bins from 300 Hz to 5 kHz, as a smoothed spectrum per frame
    edges = 300 * 2 ** (np.arange(0, np.log2(5000 / 300) + 1e-9, 1 / 12))
    cen = np.sqrt(edges[:-1] * edges[1:])
    B = np.array([[p[(fr >= a) & (fr < b)].mean() for a, b in zip(edges[:-1], edges[1:])] for p in P])
    BdB = 10 * np.log10(B + 1e-20)
    BdB -= BdB.mean(axis=1, keepdims=True)
    peak = cen[np.argmax(BdB, axis=1)]
    centroid = (P * fr).sum(axis=1) / (P.sum(axis=1) + 1e-20)
    k = keep
    print(f'\n== {path}  ({len(y) / sr:.1f} s, {k.sum()} frames used)')
    print(f'centroid: median {np.median(centroid[k]):.0f} Hz, 10th to 90th percentile {np.percentile(centroid[k], 10):.0f} to {np.percentile(centroid[k], 90):.0f} Hz')
    print(f'peak 300 Hz to 5 kHz: median {np.median(peak[k]):.0f} Hz, 10th to 90th percentile {np.percentile(peak[k], 10):.0f} to {np.percentile(peak[k], 90):.0f} Hz')
    print(f'how much each 1/12 octave band moves over time (std, dB): median {np.median(BdB[k].std(axis=0)):.1f}')
    print(f'brightness follows loudness (correlation of centroid with level): {np.corrcoef(loud[k], centroid[k])[1, 0]:+.2f}')
    # most common peak frequencies, to see a fixed resonance
    h, _ = np.histogram(peak[k], bins=edges)
    top = np.argsort(h)[::-1][:5]
    print('most frequent peak bins:', ', '.join(f'{cen[i]:.0f} Hz ({100 * h[i] / k.sum():.0f}%)' for i in top))
    # time course every 0.5 s: median centroid and peak
    print('time  centroid  peak')
    step = int(0.5 * sr / HOP)
    for s in range(0, len(P), step):
        m = k[s:s + step]
        if m.sum() == 0:
            continue
        print(f'{t[s]:5.1f}  {np.median(centroid[s:s + step][m]):6.0f}  {np.median(peak[s:s + step][m]):6.0f}')
