# fit_control.py : sets chain 12's compressor (ratio, attack, threshold) so the render's peaks and loudness are as
# controlled as the stem's. Owner: "the original sounds louder and more controlled still". Targets, measured on the stem:
#   crest     : peak level above average level, 13.42 dB (the reference had 15.31, so it ended up 1.9 dB quieter)
#   range 50  : spread of 50 ms loudness (10th to 90th percentile), 1.42 dB
#   range 400 : spread of 400 ms loudness (10th to 95th percentile), 0.49 dB
# score = |crest - target| + |range 50 - target| + 2 x |range 400 - target|. Everything else is the reference
# (chain 9b settings). Every render uses the loop lead-in (render_preroll.py), so the first note is right.
# Tries 3 ratios x 3 attacks x 3 thresholds = 27 renders, release 100 ms. Writes work\helix18\.
# usage: python -u fit_control.py
import os, itertools, numpy as np, helixlab as H
from pedalboard.io import AudioFile
from scipy.signal import fftconvolve

S = open('chain12_state.bin', 'rb').read()
OUT = os.path.join('work', 'helix18'); os.makedirs(OUT, exist_ok=True)
with AudioFile(r'input\guitar_played.wav') as f:
    take, sr = f.read(f.frames).astype(np.float32), f.samplerate
with AudioFile(r'input\guitar_stem.wav') as f:
    stem = f.read(f.frames)[0]
RANGES = [(0, 1), (100, 2000), (0, 6000), (0, 1), (0.01, 1), (0.01, 2), (0.5, 10), (0, 1), (-50, 0), (0, 10),
          (0.001, 0.1), (0, 5), (0.01, 1)]
RATIOS = {3: '6:1', 4: '10:1', 5: '20:1'}
def settings(thr, attack, ratio_idx, release=0.1):
    return [0.5, 100, 500, 0.1, 0.02, 0.8, 2, 1.0, thr, 8.2, attack, ratio_idx, release]
PRE = int(2.4 * sr)
def render(v):
    pl = H.load(); pl.raw_state = S
    for i, (x, (a, b)) in enumerate(zip(v, RANGES)):   # keep inside 0 to 1: exactly 0.0 never reaches the plugin
        pl.parameters['knob_%02d' % (i + 1)].raw_value = float(np.clip((x - a) / (b - a), 1e-4, 1 - 1e-4))
    pl.parameters['snapshot_index'].raw_value = 0.0
    x = np.concatenate([take[:, -2 * PRE:-PRE], take], axis=1)   # one pass of the loop first, cut off below
    return pl(x, sr, buffer_size=512)[0][PRE:]
N = 16384; fr = np.fft.rfftfreq(N, 1 / sr); w = np.hanning(N)
avg = lambda y: np.mean(np.abs(np.fft.rfft([y[i:i + N] * w for i in range(0, len(y) - N, N // 8)], axis=1)) ** 2, axis=0)
AS = avg(stem)
def match(y):
    rd = 10 * np.log10(AS + 1e-20) - 10 * np.log10(avg(y) + 1e-20)
    sm = np.array([rd[(fr >= f * 2 ** (-1 / 48)) & (fr <= f * 2 ** (1 / 48))].mean() if f > 0 else rd[0] for f in fr])
    sm[fr < 35] = sm[np.argmin(np.abs(fr - 35))]; sm[fr > 16000] = sm[np.argmin(np.abs(fr - 16000))]; sm -= sm.max()
    mag = 10 ** (sm / 20); full = np.concatenate([mag, mag[-2:0:-1]])
    cep = np.fft.ifft(np.log(full + 1e-12)).real; n = len(full)
    fold = np.zeros(n); fold[0] = cep[0]; fold[1:n // 2] = 2 * cep[1:n // 2]; fold[n // 2] = cep[n // 2]
    h = np.fft.ifft(np.exp(np.fft.fft(fold))).real[:8192] * np.hanning(16384)[8192:]
    return fftconvolve(y, h)[:len(y)]
def measures(y):
    crest = 20 * np.log10(np.abs(y).max() / np.sqrt(np.mean(y ** 2)))
    h = int(0.05 * sr); db = 20 * np.log10(np.array([np.sqrt(np.mean(y[i:i + h] ** 2)) + 1e-9 for i in range(0, len(y) - h, h // 2)]))
    h4 = int(0.4 * sr); st = 20 * np.log10(np.array([np.sqrt(np.mean(y[i:i + h4] ** 2)) + 1e-9 for i in range(0, len(y) - h4, h4 // 4)]))
    return crest, np.percentile(db, 90) - np.percentile(db, 10), np.percentile(st, 95) - np.percentile(st, 10)
TC, T50, T400 = measures(stem)
print(f'stem: crest {TC:.2f} dB, range 50 ms {T50:.2f}, range 400 ms {T400:.2f}')
def write(name, y):
    y = y * np.sqrt(np.mean(stem ** 2)) / np.sqrt(np.mean(y ** 2)); pk = np.abs(y).max()
    if pk > 0.999: y = y * 0.999 / pk
    with AudioFile(os.path.join(OUT, name), 'w', sr, 2, bit_depth=24) as f:
        f.write(np.stack([y, y]).astype(np.float32))
    return 20 * np.log10(np.sqrt(np.mean(y ** 2)))
results = []
for ri, att, thr in itertools.product((3, 4, 5), (0.001, 0.003, 0.01), (-10, -20, -30)):
    y = match(render(settings(thr, att, ri)))
    c, r50, r400 = measures(y)
    s = abs(c - TC) + abs(r50 - T50) + 2 * abs(r400 - T400)
    results.append((s, ri, att, thr, y))
    print(f'  ratio {RATIOS[ri]:5s} attack {att * 1000:4.0f} ms threshold {thr:4d} dB: crest {c:5.2f}  range50 {r50:.2f}  range400 {r400:.2f}  score {s:.2f}')
results.sort(key=lambda r: r[0])
write('0_target_stem.wav', stem)
for k, (s, ri, att, thr, y) in enumerate(results[:3]):
    lvl = write(f'{k + 1}_ratio_{RATIOS[ri].replace(":", "to")}_attack_{att * 1000:.0f}ms_thr_{-thr}dB.wav', y)
    print(f'wrote best {k + 1}: ratio {RATIOS[ri]}, attack {att * 1000:.0f} ms, threshold {thr} dB (score {s:.2f}), level {lvl:.2f} dB')
