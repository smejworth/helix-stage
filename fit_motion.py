# fit_motion.py : fits chain 9's envelope filter (before the amp) to the movement the stem's filter adds, measured as
# in filter_motion.py: spectral shape (1/6 octave, 100 Hz to 3 kHz) minus that of the same chain with the filter
# mixed out, averaged over 3 riff repeats. The score is how far the render's repeating movement is from the stem's,
# frame by frame and band by band (rms, dB), so timing and direction count, not just amount. One setting at a time,
# a few values each, from the owner's "ok" reference (chain 9b settings). About 25 renders.
# Writes work\helix14\ (EQ-matched for listening) and motion_fit.json.
# usage: python -u fit_motion.py
import os, json, numpy as np, helixlab as H
from pedalboard.io import AudioFile
from scipy.signal import fftconvolve

S9 = open('chain9_state.bin', 'rb').read()
OUT = os.path.join('work', 'helix14'); os.makedirs(OUT, exist_ok=True)
with AudioFile(r'input\guitar_played.wav') as f:
    take, sr = f.read(f.frames).astype(np.float32), f.samplerate
with AudioFile(r'input\guitar_stem.wav') as f:
    stem = f.read(f.frames)[0]
RANGES = [(0, 1), (100, 2000), (0, 6000), (0, 1), (0.01, 1), (0.01, 2), (0.5, 10), (0, 1), (-50, 0), (0, 10)]
NAMES = ['octave mix', 'filter freq Hz', 'sweep depth Hz', 'sensitivity', 'attack s', 'decay s', 'filter Q', 'filter mix', 'comp threshold dB', 'drive']
cur = [0.5, 100, 500, 0.1, 0.02, 0.8, 2, 1.0, -10, 8.2]
def render(v):
    pl = H.load(); pl.raw_state = S9
    for i, (x, (a, b)) in enumerate(zip(v, RANGES)):   # keep inside 0 to 1: exactly 0.0 never reaches the plugin
        pl.parameters['knob_%02d' % (i + 1)].raw_value = float(np.clip((x - a) / (b - a), 1e-4, 1 - 1e-4))
    pl.parameters['snapshot_index'].raw_value = 0.0
    return pl(take, sr, buffer_size=512)[0]

N, HOP = 2048, 1024
edges = 100 * 2 ** (np.arange(0, np.log2(3000 / 100) + 1e-9, 1 / 6)); cen = np.sqrt(edges[:-1] * edges[1:])
fr = np.fft.rfftfreq(N, 1 / sr); w = np.hanning(N)
def shape(y):
    P = np.abs(np.fft.rfft(np.array([y[i:i + N] * w for i in range(0, len(y) - N, HOP)]), axis=1)) ** 2
    B = 10 * np.log10(np.array([[p[(fr >= a) & (fr < b)].sum() for a, b in zip(edges[:-1], edges[1:])] for p in P]) + 1e-20)
    return B - B.mean(1, keepdims=True)
L = int(round(2.4 * sr / HOP))
def motion(y, base):
    B = shape(y); n = min(len(B), len(base)); D = B[:n] - base[:n]; D -= D.mean(0)
    F = np.mean([D[k * L:(k + 1) * L] for k in range(3)], axis=0)
    return np.array([np.convolve(F[:, j], np.ones(3) / 3, mode='same') for j in range(F.shape[1])]).T

base_v = list(cur); base_v[7] = 0.0
BASE = shape(render(base_v))                      # same chain, filter mixed out: the notes and amp alone
FS = motion(stem, BASE)
show = [i for i in range(len(cen)) if i % 3 == 0]
print('stem movement per band (dB) at ' + ' '.join(f'{cen[i]:.0f}' for i in show) + ' Hz: ' + ' '.join(f'{FS.std(0)[i]:.1f}' for i in show))
count = [0]
def evaluate(v):
    count[0] += 1
    F = motion(render(v), BASE)
    s = float(np.sqrt(np.mean((F - FS) ** 2)))
    print(f'  [{count[0]:2d}] score {s:.3f}  movement ' + ' '.join(f'{F.std(0)[i]:.1f}' for i in show))
    return s
best = evaluate(cur)
SWEEPS = [(6, [4, 7, 10]), (2, [150, 300, 1000]), (3, [0.05, 0.2, 0.3]), (4, [0.01, 0.05, 0.1]), (5, [0.3, 1.5]),
          (1, [150, 250]), (6, None), (2, None)]
for idx, vals in SWEEPS:
    if vals is None:
        c = cur[idx]; vals = [c * 0.7, c * 1.4]
    print(f'{NAMES[idx]} (now {cur[idx]:.3g}):')
    for x in vals:
        trial = list(cur); trial[idx] = float(np.clip(x, *RANGES[idx]))
        s = evaluate(trial)
        if s < best:
            best, cur = s, trial
    print(f'  keep {NAMES[idx]} = {cur[idx]:.3g}  (score {best:.3f})')
print('final settings:', ', '.join(f'{n} {v:.3g}' for n, v in zip(NAMES, cur)))

Nm = 16384; frm = np.fft.rfftfreq(Nm, 1 / sr); wm = np.hanning(Nm)
avg = lambda y: np.mean(np.abs(np.fft.rfft([y[i:i + Nm] * wm for i in range(0, len(y) - Nm, Nm // 8)], axis=1)) ** 2, axis=0)
AS = avg(stem)
def match(y):
    rd = 10 * np.log10(AS + 1e-20) - 10 * np.log10(avg(y) + 1e-20)
    sm = np.array([rd[(frm >= f * 2 ** (-1 / 48)) & (frm <= f * 2 ** (1 / 48))].mean() if f > 0 else rd[0] for f in frm])
    sm[frm < 35] = sm[np.argmin(np.abs(frm - 35))]; sm[frm > 16000] = sm[np.argmin(np.abs(frm - 16000))]; sm -= sm.max()
    mag = 10 ** (sm / 20); full = np.concatenate([mag, mag[-2:0:-1]])
    cep = np.fft.ifft(np.log(full + 1e-12)).real; n = len(full)
    fold = np.zeros(n); fold[0] = cep[0]; fold[1:n // 2] = 2 * cep[1:n // 2]; fold[n // 2] = cep[n // 2]
    h = np.fft.ifft(np.exp(np.fft.fft(fold))).real[:8192] * np.hanning(16384)[8192:]
    return fftconvolve(y, h)[:len(y)]
def write(name, y):
    y = y * np.sqrt(np.mean(stem ** 2)) / np.sqrt(np.mean(y ** 2)); pk = np.abs(y).max()
    if pk > 0.999: y = y * 0.999 / pk
    with AudioFile(os.path.join(OUT, name), 'w', sr, 2, bit_depth=24) as f:
        f.write(np.stack([y, y]).astype(np.float32))
ref = [0.5, 100, 500, 0.1, 0.02, 0.8, 2, 1.0, -10, 8.2]
write('0_target_stem.wav', stem); write('1_reference.wav', match(render(ref))); write('2_fitted_motion.wav', match(render(cur)))
json.dump({'settings': dict(zip(NAMES, [round(float(v), 4) for v in cur])), 'score': round(best, 3), 'renders': count[0] + 3},
          open('motion_fit.json', 'w'), indent=1)
print('wrote', OUT)
