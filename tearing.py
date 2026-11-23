# tearing.py : measures "tearing" or "ripping": the sound breaking up in fast pulses. Our ears hear loudness that
# flutters 20 to 200 times a second as rough or ripping (slower flutter, under 20 Hz, sounds like tremolo).
# For each frequency band it follows the band's loudness over time (the "envelope", via the Hilbert transform),
# then measures how strongly that envelope flutters at different speeds (its own spectrum, the "modulation
# spectrum"). Prints flutter depth for slow (4-20 Hz), rough (20-80 Hz) and buzzy (80-200 Hz) speeds, and the
# fastest strong flutter rates, which can show what causes the tearing (for example 27.5 or 55 Hz from drop A notes,
# or beating between the octave-down voice and the original).
# usage: python tearing.py FILE [FILE ...]
import sys, numpy as np
from pedalboard.io import AudioFile
from scipy.signal import butter, sosfiltfilt, hilbert, resample_poly

BANDS = [(150, 600), (600, 2000), (2000, 6000)]
SPEEDS = [(4, 20), (20, 80), (80, 200)]
for path in sys.argv[1:]:
    with AudioFile(path) as f:
        y, sr = f.read(f.frames)[0], f.samplerate
    print(path.split(chr(92))[-1])
    for lo, hi in BANDS:
        x = sosfiltfilt(butter(4, [lo, hi], 'band', fs=sr, output='sos'), y)
        env = np.abs(hilbert(x))
        env = resample_poly(env, 1, int(sr // 1000))        # about 1000 envelope values per second is enough
        fs = sr / int(sr // 1000)
        n = 1024; w = np.hanning(n); mf = np.fft.rfftfreq(n, 1 / fs)
        segs = [env[i:i + n] for i in range(0, len(env) - n, n // 2)]
        M = np.mean([np.abs(np.fft.rfft((s_ - s_.mean()) * w)) ** 2 / (s_.mean() ** 2 + 1e-20) for s_ in segs], axis=0)
        tot = lambda a, b: 10 * np.log10(M[(mf >= a) & (mf < b)].sum() + 1e-20)
        sp = '  '.join(f'{a}-{b} Hz {tot(a, b):6.1f}' for a, b in SPEEDS)
        m = (mf >= 15) & (mf < 250)
        pk = mf[m][np.argsort(M[m])[::-1][:4]]
        print(f'   band {lo}-{hi} Hz: flutter {sp}   strongest rates {", ".join(f"{p:.0f}" for p in sorted(pk))} Hz')
