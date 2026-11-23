# bandwidth.py : measures how band-limited a recording is, the "AM radio" quality: radio and telephone sound
# comes from cutting both ends of the spectrum steeply, leaving a narrow middle band.
# For each file it smooths the long-term spectrum (1/3 octave), finds the loudest region, and prints where the
# spectrum has fallen 3, 10 and 20 dB below that peak on the low side and the high side, plus how steep the
# fall is on each side (dB per octave between the -3 and -20 dB points). Also prints the spectrum itself.
# usage: python bandwidth.py FILE [FILE ...]
import sys, numpy as np
from pedalboard.io import AudioFile

N = 16384
rows = []
for path in sys.argv[1:]:
    with AudioFile(path) as f:
        y, sr = f.read(f.frames)[0], f.samplerate
    fr = np.fft.rfftfreq(N, 1 / sr); w = np.hanning(N)
    P = np.mean(np.abs(np.fft.rfft([y[i:i + N] * w for i in range(0, len(y) - N, N // 4)], axis=1)) ** 2, axis=0)
    c = 30 * 2 ** (np.arange(0, np.log2(18000 / 30), 1 / 12))
    # power density (mean per Hz) in a 1/3 octave window around each point, so wide and narrow bands compare fairly
    d = np.array([10 * np.log10(P[(fr >= x * 2 ** (-1 / 6)) & (fr < x * 2 ** (1 / 6))].mean() + 1e-20) for x in c])
    d -= d.max(); pk = int(np.argmax(d))
    def cross(level, side):
        idx = range(pk, -1, -1) if side == 'low' else range(pk, len(d))
        for i in idx:
            if d[i] < level:
                return c[i]
        return float('nan')
    lo3, lo10, lo20 = cross(-3, 'low'), cross(-10, 'low'), cross(-20, 'low')
    hi3, hi10, hi20 = cross(-3, 'high'), cross(-10, 'high'), cross(-20, 'high')
    print(f'{path.split(chr(92))[-1]}: peak {c[pk]:.0f} Hz')
    print(f'   low side  -3 dB {lo3:6.0f} Hz  -10 dB {lo10:6.0f}  -20 dB {lo20:6.0f}   slope {17 / np.log2(lo3 / lo20):5.1f} dB/oct')
    print(f'   high side -3 dB {hi3:6.0f} Hz  -10 dB {hi10:6.0f}  -20 dB {hi20:6.0f}   slope {17 / np.log2(hi20 / hi3):5.1f} dB/oct')
    rows.append(d)
print('spectrum, dB below each file\'s peak (power per Hz, 1/3 octave smoothing):')
print('   Hz  ' + '  '.join(f'file{i + 1}' for i in range(len(rows))))
for i in range(0, len(c), 6):
    print(f'{c[i]:6.0f} ' + '  '.join(f'{r[i]:+6.1f}' for r in rows))
