# first_notes.py : looks closely at the start of each 2.4 s riff, where the owner hears the envelope filter close
# on the first two notes. Every 20 ms over the first 1.2 s it measures, for the stem and a render (lined up, the four
# repeats averaged): brightness (centroid), the frequency of the strongest region between 300 Hz and 3 kHz
# (smoothed over 1/3 octave, so it follows a filter's peak rather than single harmonics), and loudness.
# Pick attacks in the clean take over the same stretch are marked with '<- pick'.
# A closing filter shows as the peak frequency and brightness sliding DOWN after a pick.
# usage: python first_notes.py STEM RENDER CLEAN_TAKE
import sys, numpy as np
from pedalboard.io import AudioFile

def load(p):
    with AudioFile(p) as f:
        return f.read(f.frames)[0], f.samplerate
s, sr = load(sys.argv[1]); r, _ = load(sys.argv[2]); c, _ = load(sys.argv[3])
N, HOP, REP = 2048, int(0.02 * sr), 2.4
fr = np.fft.rfftfreq(N, 1 / sr); w = np.hanning(N)
g = 300 * 2 ** (np.arange(0, np.log2(3000 / 300), 1 / 24))
def track(y):
    out = []
    for k in range(4):
        st = int(k * REP * sr); rows = []
        for j in range(60):
            i = st + j * HOP
            seg = y[i:i + N]
            if len(seg) < N:
                break
            p = np.abs(np.fft.rfft(seg * w)) ** 2
            x = np.interp(g, fr, 10 * np.log10(p + 1e-20)); x = np.convolve(x, np.ones(9) / 9, mode='same')[4:-4]
            rows.append(((p * fr).sum() / p.sum(), g[4:-4][np.argmax(x)], 10 * np.log10(p.sum() + 1e-20)))
        if len(rows) == 60:
            out.append(rows)
    a = np.array(out)                     # repeats x frames x 3
    cen = a[:, :, 0].mean(0); pk = np.exp(np.log(a[:, :, 1]).mean(0)); lv = a[:, :, 2].mean(0)
    return cen, pk, lv - lv.max()
cs, ps, ls = track(s); cr, pr, lr = track(r); _, _, lc = track(c)
flux = np.r_[0, np.diff(lc)]
print(' time   stem: centroid  peak   level | render: centroid  peak   level')
for j in range(60):
    mark = '  <- pick' if flux[j] > 4 else ''
    print(f'{j * 0.02:5.2f}       {cs[j]:6.0f} {ps[j]:6.0f} {ls[j]:+6.1f} |         {cr[j]:6.0f} {pr[j]:6.0f} {lr[j]:+6.1f}{mark}')
