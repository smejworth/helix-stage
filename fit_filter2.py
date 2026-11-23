# fit_filter2.py : calculates the Parametric EQ settings (two peak/notch bands and a high cut) for the end of
# chain 5 from the measured gap to the stem, using the standard formulas for these filters, then checks with renders.
# No search over renders:
#   1. render chain 5 with the filter flat (same as chain 4), measure stem minus render at 1/24 octave, 2 to 14 kHz
#   2. fit the curve of a peak band, a second peak band and a 12 dB per octave high cut to that gap (maths only)
#   3. render once with those settings and measure; also measure what the block really did (render minus flat)
#      against what the formulas predicted, so a mismatch in how Helix maps its knobs shows up
# Uses at most 4 renders (one process can make only about 55 plugin instances before it crashes).
# Writes renders to work\helix05\ and the settings to filter_fit.json.
# usage: python -u fit_filter2.py
import os, json, numpy as np, helixlab as H
from scipy.optimize import least_squares
from scipy.signal import freqz, butter
from pedalboard.io import AudioFile

S5 = open('chain5_state.bin', 'rb').read()
K4 = json.load(open('eq_fit.json'))['knobs']
OUT = os.path.join('work', 'helix05'); os.makedirs(OUT, exist_ok=True)
with AudioFile(r'input\guitar_played.wav') as f:
    take, sr = f.read(f.frames).astype(np.float32), f.samplerate
with AudioFile(r'input\guitar_stem.wav') as f:
    stem = f.read(f.frames)

def spec_db(y, step, lo=40, hi=16000, n=8192):
    edges = lo * 2 ** (np.arange(0, np.log2(hi / lo) + 1e-9, step))
    w = np.hanning(n); fr = np.fft.rfftfreq(n, 1 / sr)
    P = np.mean(np.abs(np.fft.rfft([y[i:i + n] * w for i in range(0, len(y) - n, n // 2)], axis=1)) ** 2, axis=0)
    return np.sqrt(edges[:-1] * edges[1:]), np.array([10 * np.log10(P[(fr >= a) & (fr < b)].sum() + 1e-20) for a, b in zip(edges[:-1], edges[1:])])

def render(knobs, snap=1):
    pl = H.load(); pl.raw_state = S5
    for i, v in enumerate(knobs):      # keep inside 0 to 1: exactly 0.0 never reaches the plugin
        pl.parameters['knob_%02d' % (i + 1)].raw_value = float(np.clip(v, 1e-4, 1 - 1e-4))
    pl.parameters['snapshot_index'].raw_value = (snap - 1) / 7.0
    return pl(take, sr, buffer_size=512)[0]

def err(y, step):
    d = spec_db(stem[0], step)[1] - spec_db(y, step)[1]; d -= d.mean()
    return float(np.sqrt(np.mean(d ** 2)))

# the filter's response from its settings (standard "peaking EQ" biquad formula, and a 2 pole Butterworth low pass)
def peak_db(f, f0, g, q):
    A = 10 ** (g / 40); w0 = 2 * np.pi * f0 / sr; al = np.sin(w0) / (2 * q)
    b = [1 + al * A, -2 * np.cos(w0), 1 - al * A]; a = [1 + al / A, -2 * np.cos(w0), 1 - al / A]
    return 20 * np.log10(np.abs(freqz(b, a, worN=f, fs=sr)[1]))
def cut_db(f, fc):
    b, a = butter(2, min(fc, 0.49 * sr), 'low', fs=sr)
    return 20 * np.log10(np.abs(freqz(b, a, worN=f, fs=sr)[1]) + 1e-12)
def model(p, f):
    return peak_db(f, p[0], p[1], p[2]) + peak_db(f, p[3], p[4], p[5]) + cut_db(f, p[6])

CUTS = K4[10:14]
FLATK = CUTS + [0.47, 0.5, 0.29, 0.3, 0.5, 0.47, 1.0]
yflat = render(FLATK)
c, s = spec_db(stem[0], 1 / 24, 2000, 14000)
_, r = spec_db(yflat, 1 / 24, 2000, 14000)
_, sall = spec_db(stem[0], 1 / 24); _, rall = spec_db(yflat, 1 / 24)
gap = (s - r) - np.mean(sall - rall)          # the gap in 2 to 14 kHz, on the same level footing as the whole range
print(f'filter flat (chain 4): error {err(yflat, 1 / 12):.2f} dB at 1/12 octave, {err(yflat, 1 / 6):.2f} at 1/6')

lo = [2000, -12, 0.5, 4000, -12, 0.5, 5000]; hi = [9000, 12, 8, 12000, 12, 8, 20000]
p0 = [5300, 4, 2.7, 6400, -6, 4, 12000]
fit = least_squares(lambda p: model(p, c) - gap, p0, bounds=(lo, hi))
p = fit.x
print('calculated filter: mid %.0f Hz %+.1f dB Q %.2f, high %.0f Hz %+.1f dB Q %.2f, high cut %.0f Hz' % tuple(p))
print(f'predicted leftover in 2 to 14 kHz: {np.sqrt(np.mean((model(p, c) - gap) ** 2)):.2f} dB (before: {np.sqrt(np.mean((gap - gap.mean()) ** 2)):.2f})')

kn = CUTS + [(p[0] - 2000) / 7000, (p[1] + 12) / 24, (p[2] - 0.5) / 7.5, (p[3] - 4000) / 8000, (p[4] + 12) / 24,
             (p[5] - 0.5) / 7.5, (p[6] - 5000) / 15100]
y = render(kn)
_, rf = spec_db(y, 1 / 24, 2000, 14000)
did = rf - r; did -= did.mean(); want = model(p, c); want -= want.mean()
print(f'check, what the block did against what the formulas said: largest difference {np.abs(did - want).max():.1f} dB')
print(f'with filter: error {err(y, 1 / 12):.2f} dB at 1/12 octave, {err(y, 1 / 6):.2f} at 1/6')
print('freq   gap  formula  block did')
for ci, g_, m_, d_ in zip(c[::2], gap[::2], want[::2], did[::2]):
    print(f'{ci:6.0f} {g_:+5.1f}  {m_:+5.1f}  {d_:+5.1f}')

def write(name, yy):
    g = np.sqrt(np.mean(stem[0] ** 2)) / np.sqrt(np.mean(yy ** 2))
    with AudioFile(os.path.join(OUT, name), 'w', sr, 2, bit_depth=24) as f:
        f.write(np.clip(np.stack([yy, yy]) * g, -1, 1).astype(np.float32))
write('1_target_stem.wav', stem[0]); write('2_dry_played.wav', take[0])
write('3_oct_on_with_filter.wav', y); write('4_oct_off_with_filter.wav', render(kn, snap=2))
write('5_oct_on_no_filter.wav', yflat)
json.dump({'knobs': [round(float(v), 4) for v in kn],
           'filter': dict(zip(['mid_hz', 'mid_db', 'mid_q', 'high_hz', 'high_db', 'high_q', 'high_cut_hz'], [round(float(v), 2) for v in p])),
           'error_db': {'no_filter_1_12': round(err(yflat, 1 / 12), 2), 'filter_1_12': round(err(y, 1 / 12), 2),
                        'no_filter_1_6': round(err(yflat, 1 / 6), 2), 'filter_1_6': round(err(y, 1 / 6), 2)}},
          open('filter_fit.json', 'w'), indent=1)
print('wrote', OUT)
