# many_instances.py : checks whether a render of chain 4 changes after many plugin instances have been made in the
# same process (fit_eq.py made about 50 before its final render, and today's single renders do not match it).
# Renders chain 4 with the fitted knobs every 10 instances and prints its error to the stem.
# usage: python -u many_instances.py
import json, numpy as np, helixlab as H
from pedalboard.io import AudioFile
with AudioFile(r'input\guitar_played.wav') as f:
    take, sr = f.read(f.frames).astype(np.float32), f.samplerate
with AudioFile(r'input\guitar_stem.wav') as f:
    stem = f.read(f.frames)[0]
K4 = json.load(open('eq_fit.json'))['knobs']; S4 = open('chain4_state.bin', 'rb').read()
n = 8192; w = np.hanning(n); fr = np.fft.rfftfreq(n, 1 / sr)
e = 40 * 2 ** (np.arange(0, np.log2(16000 / 40) + 1e-9, 1 / 6))
def sp(x):
    P = np.mean(np.abs(np.fft.rfft([x[i:i + n] * w for i in range(0, len(x) - n, n // 2)], axis=1)) ** 2, axis=0)
    return np.array([10 * np.log10(P[(fr >= a) & (fr < b)].sum() + 1e-20) for a, b in zip(e[:-1], e[1:])])
def render(k):
    pl = H.load(); pl.raw_state = S4
    for j, v in enumerate(k):
        pl.parameters['knob_%02d' % (j + 1)].raw_value = float(v)
    pl.parameters['snapshot_index'].raw_value = 0.0
    return pl(take, sr, buffer_size=512)[0]
def err(y):
    d = sp(stem) - sp(y); d -= d.mean(); return float(np.sqrt(np.mean(d ** 2)))
FLAT = [0.5] * 10 + [0.0, 1.0] * 3
count = 0
for rnd in range(6):
    print(f'after {count} instances: chain 4 error {err(render(K4)):.2f} dB'); count += 1
    for k in range(9):
        kn = list(FLAT); kn[k] = 1.0; render(kn); count += 1
