# fit_filter.py : fits the narrow filter (a bump near 5 kHz, a notch near 6.4 kHz, a fall near 10 kHz) with the
# Parametric EQ block at the end of chain 5, by measurement, then renders for listening.
#   1. check: chain 5 with the filter flat must sound like chain 4 with its fitted knobs (same graphic EQ, now
#      written into the preset instead of set by knobs). If the two differ, the knob to dB mapping was wrong.
#   2. search the 7 filter knobs (mid band freq, gain, Q; high band freq, gain, Q; high cut) for the setting whose
#      spectrum is closest to the stem at 1/12 octave resolution, 40 Hz to 16 kHz (Nelder-Mead: a search that
#      only needs to measure, no formula for the filter needed). Each step is one real render.
#   3. writes renders to work\helix05\ and the settings to filter_fit.json
# The plugin state is loaded unchanged; only knob values are set.
# usage: python fit_filter.py
import os, json, time, numpy as np, helixlab as H
from scipy.optimize import minimize
from pedalboard.io import AudioFile

S4 = open('chain4_state.bin', 'rb').read()
S5 = open('chain5_state.bin', 'rb').read()
K4 = json.load(open('eq_fit.json'))['knobs']
OUT = os.path.join('work', 'helix05'); os.makedirs(OUT, exist_ok=True)
with AudioFile(r'input\guitar_played.wav') as f:
    take, sr = f.read(f.frames).astype(np.float32), f.samplerate
with AudioFile(r'input\guitar_stem.wav') as f:
    stem = f.read(f.frames)

def spec_db(y, step, n=8192):
    edges = 40 * 2 ** (np.arange(0, np.log2(16000 / 40) + 1e-9, step))
    w = np.hanning(n); fr = np.fft.rfftfreq(n, 1 / sr)
    P = np.mean(np.abs(np.fft.rfft([y[i:i + n] * w for i in range(0, len(y) - n, n // 2)], axis=1)) ** 2, axis=0)
    return np.array([10 * np.log10(P[(fr >= a) & (fr < b)].sum() + 1e-20) for a, b in zip(edges[:-1], edges[1:])])

def render(state, knobs, snap=1):
    pl = H.load(); pl.raw_state = state
    for i, v in enumerate(knobs):
        # after a state loads every knob reads 0.0, so setting exactly 0.0 is not a change and never reaches
        # the plugin. Keeping values a hair inside 0 to 1 makes every setting take effect.
        pl.parameters['knob_%02d' % (i + 1)].raw_value = float(np.clip(v, 1e-4, 1 - 1e-4))
    pl.parameters['snapshot_index'].raw_value = (snap - 1) / 7.0
    return pl(take, sr, buffer_size=512)[0]

def err(y, step):
    d = spec_db(stem[0], step) - spec_db(y, step); d -= d.mean()
    return float(np.sqrt(np.mean(d ** 2)))

CUTS = K4[10:14]                          # chain 4 cut blocks A and B, as fitted
FLAT = [0.5, 0.5, 0.0, 1.0, 1.0]          # filter neutral: gains 0 dB, high cut at maximum (freqs and Q irrelevant)
def k5(f):                                # f = mid freq, mid gain, mid Q, high freq, high gain, high Q, high cut
    return CUTS + [f[0], f[1], f[2], f[3], f[4], f[5], f[6]]

t0 = time.time()
y4 = render(S4, K4)
print(f'one render takes {time.time() - t0:.1f} s')
y5flat = render(S5, CUTS + [0.47, 0.5, 0.29, 0.3, 0.5, 0.47, 1.0])
diff = spec_db(y4, 1 / 12) - spec_db(y5flat, 1 / 12)
print(f'check, chain 4 against chain 5 with filter flat: largest difference {np.abs(diff - diff.mean()).max():.2f} dB')
print(f'chain 4 error to stem: {err(y4, 1 / 6):.2f} dB at 1/6 octave, {err(y4, 1 / 12):.2f} dB at 1/12 octave')

# start from the measured shape: bump 5.3 kHz +6 dB, notch 6.4 kHz -9 dB, high cut 10.5 kHz
x0 = np.array([(5300 - 2000) / 7000, 0.75, (2.7 - 0.5) / 7.5, (6400 - 4000) / 8000, 0.125, (4 - 0.5) / 7.5, (10500 - 5000) / 15100])
n = [0]
def cost(x):
    n[0] += 1
    e = err(render(S5, k5(np.clip(x, 0, 1))), 1 / 12)
    print(f'  render {n[0]}: knobs {np.round(np.clip(x, 0, 1), 3).tolist()} error {e:.2f} dB')
    return e
print(f'start point error: {cost(x0):.2f} dB at 1/12 octave')
r = minimize(cost, x0, method='Nelder-Mead', options={'maxfev': 140, 'initial_simplex': None, 'xatol': 0.01, 'fatol': 0.02})
x = np.clip(r.x, 0, 1)
y5 = render(S5, k5(x))
print(f'after {n[0]} renders: error {err(y5, 1 / 12):.2f} dB at 1/12 octave, {err(y5, 1 / 6):.2f} dB at 1/6 octave')

vals = {'mid_freq_hz': 2000 + 7000 * x[0], 'mid_gain_db': -12 + 24 * x[1], 'mid_q': 0.5 + 7.5 * x[2],
        'high_freq_hz': 4000 + 8000 * x[3], 'high_gain_db': -12 + 24 * x[4], 'high_q': 0.5 + 7.5 * x[5],
        'high_cut_hz': 5000 + 15100 * x[6]}
print('filter (knob ranges mapped linearly, not checked against the editor):', ', '.join(f'{k} {v:.1f}' for k, v in vals.items()))

def write(name, y):
    g = np.sqrt(np.mean(stem[0] ** 2)) / np.sqrt(np.mean(y ** 2))
    with AudioFile(os.path.join(OUT, name), 'w', sr, 2, bit_depth=24) as f:
        f.write(np.clip(np.stack([y, y]) * g, -1, 1).astype(np.float32))
write('1_target_stem.wav', stem[0]); write('2_dry_played.wav', take[0])
write('3_oct_on_with_filter.wav', y5)
write('4_oct_off_with_filter.wav', render(S5, k5(x), snap=2))
write('5_oct_on_chain4_no_filter.wav', y4)
json.dump({'knobs': [round(float(v), 4) for v in k5(x)], 'filter_values': {k: round(float(v), 2) for k, v in vals.items()},
           'error_db_1_12_octave': {'chain4': round(err(y4, 1 / 12), 2), 'chain5': round(err(y5, 1 / 12), 2)},
           'error_db_1_6_octave': {'chain4': round(err(y4, 1 / 6), 2), 'chain5': round(err(y5, 1 / 6), 2)},
           'renders': n[0]}, open('filter_fit.json', 'w'), indent=1)
d = spec_db(stem[0], 1 / 12) - spec_db(y5, 1 / 12); d -= d.mean()
e4 = spec_db(stem[0], 1 / 12) - spec_db(y4, 1 / 12); e4 -= e4.mean()
c = 40 * 2 ** (np.arange(0, len(d)) / 12 + 1 / 24)
print('leftover stem minus render, 3 to 14 kHz (dB): freq  chain4  chain5')
for ci, a, b in zip(c, e4, d):
    if 3000 < ci < 14000:
        print(f'  {ci:6.0f}  {a:+5.1f}  {b:+5.1f}')
