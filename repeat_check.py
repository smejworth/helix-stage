# repeat_check.py : checks whether rendering chain 4 with the fitted knobs gives the same result each time, and
# the same as the file already in work\helix04. Prints the spectral error to the stem (1/6 octave, 40 Hz to 16 kHz)
# for the saved file and for three fresh renders, plus the largest difference between the fresh renders.
# usage: python -u repeat_check.py
import json, numpy as np, helixlab as H
from pedalboard.io import AudioFile

with AudioFile(r'input\guitar_played.wav') as f:
    take, sr = f.read(f.frames).astype(np.float32), f.samplerate
with AudioFile(r'input\guitar_stem.wav') as f:
    stem = f.read(f.frames)[0]
with AudioFile(r'work\helix04\3_oct_on_fitted_eq.wav') as f:
    saved = f.read(f.frames)[0]
S4 = open('chain4_state.bin', 'rb').read()
K4 = json.load(open('eq_fit.json'))['knobs']

def spec_db(y, n=8192):
    edges = 40 * 2 ** (np.arange(0, np.log2(16000 / 40) + 1e-9, 1 / 6))
    w = np.hanning(n); fr = np.fft.rfftfreq(n, 1 / sr)
    P = np.mean(np.abs(np.fft.rfft([y[i:i + n] * w for i in range(0, len(y) - n, n // 2)], axis=1)) ** 2, axis=0)
    return np.array([10 * np.log10(P[(fr >= a) & (fr < b)].sum() + 1e-20) for a, b in zip(edges[:-1], edges[1:])])
def err(y):
    d = spec_db(stem) - spec_db(y); d -= d.mean(); return float(np.sqrt(np.mean(d ** 2)))

print(f'saved helix04 file 3: {err(saved):.2f} dB')
outs = []
for i in range(3):
    pl = H.load(); pl.raw_state = S4
    for j, v in enumerate(K4):
        pl.parameters['knob_%02d' % (j + 1)].raw_value = float(v)
    pl.parameters['snapshot_index'].raw_value = 0.0
    y = pl(take, sr, buffer_size=512)[0]
    outs.append(spec_db(y))
    print(f'fresh render {i + 1}: {err(y):.2f} dB')
print(f'largest band difference between fresh renders: {max(np.abs(o - outs[0]).max() for o in outs):.2f} dB')
print(f'largest band difference, fresh render 1 against saved file (level removed): {np.abs((outs[0] - spec_db(saved)) - (outs[0] - spec_db(saved)).mean()).max():.2f} dB')
