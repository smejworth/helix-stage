# tone_traits.py : measures parts of a guitar tone that an EQ cannot change, to find what still differs once the
# frequency balance is close. For each file it prints:
#   loudness range   : spread of loudness over time (10th to 90th percentile of 50 ms RMS, dB). Small = squashed / compressed
#   crest factor     : peak level over average level (dB). Small = heavy clipping or compression
#   decay 0.2 s      : how far the level falls 200 ms after each hit (dB). Big = tight and choppy, small = sustained
#   fuzz 1 to 5 kHz  : spectral flatness (0 = clean separate harmonics, 1 = noise). Higher = fizzier, more broken up
#   sub 25 to 35 Hz  : energy around 27.5 Hz (one octave below drop A's low A) relative to the whole file (dB)
#   low A 50 to 60 Hz: energy around 55 Hz (drop A's low A) relative to the whole file (dB)
# usage: python tone_traits.py FILE [FILE ...]
import sys, numpy as np
from pedalboard.io import AudioFile

for path in sys.argv[1:]:
    with AudioFile(path) as f:
        y, sr = f.read(f.frames)[0], f.samplerate
    h = int(0.05 * sr)
    rms = np.array([np.sqrt(np.mean(y[i:i + h] ** 2)) + 1e-9 for i in range(0, len(y) - h, h // 2)])
    db = 20 * np.log10(rms)
    act = db > db.max() - 40
    lr = np.percentile(db[act], 90) - np.percentile(db[act], 10)
    crest = 20 * np.log10(np.max(np.abs(y)) / np.sqrt(np.mean(y ** 2)))
    # onsets: frames where level jumps by more than 6 dB over 50 ms
    hop = h // 2; on = [i for i in range(2, len(db) - 10) if db[i] - db[i - 2] > 6 and db[i] > db.max() - 25]
    on = [o for k, o in enumerate(on) if k == 0 or o - on[k - 1] > 4]
    step = int(0.2 * sr / hop)
    dec = np.mean([db[o:o + 3].max() - db[min(o + step, len(db) - 1)] for o in on]) if on else float('nan')
    n = 4096; w = np.hanning(n); fr = np.fft.rfftfreq(n, 1 / sr)
    P = np.abs(np.fft.rfft(np.array([y[i:i + n] * w for i in range(0, len(y) - n, n // 2)]), axis=1)) ** 2
    band = P[:, (fr >= 1000) & (fr < 5000)] + 1e-20
    flat = np.exp(np.mean(np.log(band), axis=1)) / np.mean(band, axis=1)
    loud = P.sum(1) > P.sum(1).max() * 1e-3
    N = 65536; Pl = np.abs(np.fft.rfft(y[:N] * np.hanning(len(y[:N])))) ** 2 if len(y) < N else None
    Pall = np.mean(np.abs(np.fft.rfft(np.array([y[i:i + N] * np.hanning(N) for i in range(0, len(y) - N, N // 2)]), axis=1)) ** 2, axis=0)
    fl = np.fft.rfftfreq(N, 1 / sr); tot = Pall.sum()
    sub = 10 * np.log10(Pall[(fl >= 25) & (fl < 35)].sum() / tot)
    la = 10 * np.log10(Pall[(fl >= 50) & (fl < 60)].sum() / tot)
    print(f'{path.split(chr(92))[-1]:28s} range {lr:5.1f}  crest {crest:5.1f}  decay {dec:5.1f} ({len(on)} hits)  fuzz {np.median(flat[loud]):.3f}  sub {sub:6.1f}  lowA {la:6.1f}')
