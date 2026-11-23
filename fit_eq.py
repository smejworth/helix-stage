# fit_eq.py : calculates the Helix EQ settings (10 band graphic plus stacked low and high cuts) that make the
# owner's take, run through chain 4, have the same frequency balance as the stem. No guessing by ear:
#   1. render with the EQ flat and measure the gap to the stem in 1/6 octave steps from 40 Hz to 16 kHz
#   2. measure what each EQ band really does (render with that band at +12 dB, compare with flat)
#   3. measure one cut block at several knob positions (stacking 2 or 3 identical blocks doubles or triples it in dB)
#   4. solve for the band gains and cut settings that best close the gap (least squares), render,
#      measure what is left over and correct once
# The EQ blocks sit after the amp, so they act on a fixed signal and their effect adds up exactly in dB.
# The plugin state is loaded unchanged; only knob values are set. Writes renders to work\helix04\
# and the chosen settings to eq_fit.json.
# usage: python fit_eq.py
import os, json, numpy as np, helixlab as H
from scipy.optimize import lsq_linear
from pedalboard.io import AudioFile

STATE = open('chain4_state.bin', 'rb').read()
OUT = os.path.join('work', 'helix04'); os.makedirs(OUT, exist_ok=True)
with AudioFile(r'input\guitar_played.wav') as f:
    take, sr = f.read(f.frames).astype(np.float32), f.samplerate
with AudioFile(r'input\guitar_stem.wav') as f:
    stem = f.read(f.frames)

# 1/6 octave bins from about 40 Hz to 16 kHz
edges = 40 * 2 ** (np.arange(0, np.log2(16000 / 40) + 1e-9, 1 / 6))
centers = np.sqrt(edges[:-1] * edges[1:])

def spec_db(y, n=8192):
    # average power spectrum (Welch's method), summed into the bins, in dB (absolute, not normalised)
    w = np.hanning(n)
    fr = np.fft.rfftfreq(n, 1 / sr)
    P = np.mean(np.abs(np.fft.rfft([y[i:i + n] * w for i in range(0, len(y) - n, n // 2)], axis=1)) ** 2, axis=0)
    return np.array([10 * np.log10(P[(fr >= a) & (fr < b)].sum() + 1e-20) for a, b in zip(edges[:-1], edges[1:])])

FLAT = [0.5] * 10 + [0.0, 1.0] * 3          # bands at 0 dB, low cuts at minimum, high cuts at maximum
def render(knobs, snap=1):
    pl = H.load(); pl.raw_state = STATE
    for i, v in enumerate(knobs):
        # every knob reads 0.0 after a state loads, so exactly 0.0 would never reach the plugin: stay inside 0 to 1
        pl.parameters['knob_%02d' % (i + 1)].raw_value = float(np.clip(v, 1e-4, 1 - 1e-4))
    pl.parameters['snapshot_index'].raw_value = (snap - 1) / 7.0
    return pl(take, sr, buffer_size=512)[0]

T = spec_db(stem[0])
base = spec_db(render(FLAT))
print('measuring each EQ band')
R = []
for k in range(10):
    kn = list(FLAT); kn[k] = 1.0
    R.append(spec_db(render(kn)) - base)    # response of band k at +12 dB
A = np.array(R).T / 12.0                     # response per dB of gain (assumed proportional; corrected in step 4)

print('measuring the cut blocks')
LV = [0.0, 0.1, 0.2, 0.3, 0.4, 0.6, 0.8, 1.0]       # low cut knob positions (19.9 to 500 Hz range)
HV = [0.0, 0.05, 0.1, 0.15, 0.2, 0.3, 0.45, 1.0]    # high cut knob positions (1000 to 20100 Hz range)
Lresp, Hresp = {}, {}
for v in LV:
    kn = list(FLAT); kn[10] = v; Lresp[v] = spec_db(render(kn)) - base
for v in HV:
    kn = list(FLAT); kn[11] = v; Hresp[v] = spec_db(render(kn)) - base

def solve(gap):
    # band gains g (-12 to +12 dB) and a free overall level c that best fit the gap
    M = np.hstack([A, np.ones((len(gap), 1))])
    r = lsq_linear(M, gap, bounds=([-12] * 10 + [-np.inf], [12] * 10 + [np.inf]))
    return r.x[:10], r.x[10], float(np.sqrt(np.mean((M @ r.x - gap) ** 2)))

best = None
for lv in LV:
    for nl in (1, 2, 3):
        for hv in HV:
            for nh in (1, 2, 3):
                gap = T - base - nl * Lresp[lv] - nh * Hresp[hv]
                g, c, err = solve(gap)
                if best is None or err < best[0]:
                    best = (err, lv, nl, hv, nh, g)
err, lv, nl, hv, nh, g = best
print(f'best predicted fit: rms error {err:.2f} dB, low cut knob {lv} x{nl} blocks, high cut knob {hv} x{nh} blocks')

def knobs_for(g):
    kn = [(gi + 12) / 24 for gi in g] + [0.0, 1.0] * 3
    for b in range(nl): kn[10 + 2 * b] = lv
    for b in range(nh): kn[11 + 2 * b] = hv
    return kn

def fit_error(y):
    d = T - spec_db(y); d -= d.mean()
    return float(np.sqrt(np.mean(d ** 2))), d

y1 = render(knobs_for(g)); e1, d1 = fit_error(y1)
print(f'measured after first solve: rms error {e1:.2f} dB')
g2, _, _ = solve(d1)                          # correct with the measured leftover
g_corr = np.clip(g + g2, -12, 12)
y2 = render(knobs_for(g_corr)); e2, d2 = fit_error(y2)
print(f'measured after correction:  rms error {e2:.2f} dB')
if e1 <= e2:                                  # keep whichever measured closer
    y2, e2, d2 = y1, e1, d1
    print('keeping the first solve (it measured closer)')
else:
    g = g_corr
e0, _ = fit_error(render(FLAT))
print(f'for comparison, EQ flat:     rms error {e0:.2f} dB')

def write(name, y):
    y2c = np.stack([y, y]); g_ = np.sqrt(np.mean(stem[0] ** 2)) / np.sqrt(np.mean(y ** 2))
    with AudioFile(os.path.join(OUT, name), 'w', sr, 2, bit_depth=24) as f:
        f.write(np.clip(y2c * g_, -1, 1).astype(np.float32))
write('1_target_stem.wav', stem[0]); write('2_dry_played.wav', take[0])
write('3_oct_on_fitted_eq.wav', y2)
write('4_oct_off_fitted_eq.wav', render(knobs_for(g), snap=2))
names = ['31Hz', '62Hz', '125Hz', '250Hz', '500Hz', '1k', '2k', '4k', '8k', '16k']
json.dump({'band_gains_db': dict(zip(names, [round(float(x), 2) for x in g])), 'low_cut_knob': lv, 'low_cut_blocks': nl,
           'high_cut_knob': hv, 'high_cut_blocks': nh, 'knobs': [round(float(x), 4) for x in knobs_for(g)],
           'rms_error_db': {'eq_flat': round(e0, 2), 'fitted': round(e2, 2)}}, open('eq_fit.json', 'w'), indent=1)
print('band gains dB:', ', '.join(f'{n} {x:+.1f}' for n, x in zip(names, g)))
print('leftover gap by 1/6 octave (stem minus render, dB):')
for c_, d_ in zip(centers[::2], d2[::2]):
    print(f'  {c_:7.0f} Hz  {d_:+5.1f}')
