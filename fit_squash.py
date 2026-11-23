# fit_squash.py : sets chain 6's amp Drive and compressor Threshold by measuring two traits against the stem,
# one knob at a time, a handful of renders each (no blind search):
#   fuzz  : spectral flatness 1 to 5 kHz (0 = clean separate harmonics, 1 = noise); the stem measures 0.46
#   range : loudness spread over time (10th to 90th percentile of 50 ms RMS, dB); the stem measures 1.4
#   1. Drive sweep with the compressor barely working (threshold 0 dB): pick the Drive whose fuzz is closest
#   2. Threshold sweep at that Drive: pick the threshold whose loudness range is closest
#   3. render, and report the spectral error to the stem too (the EQ is fixed, so changing Drive can move it)
# Writes work\helix06\ and squash_fit.json. About 15 renders (one process manages about 55).
# usage: python -u fit_squash.py
import os, json, numpy as np, helixlab as H
from pedalboard.io import AudioFile

S6 = open('chain6_state.bin', 'rb').read()
K4 = json.load(open('eq_fit.json'))['knobs']; KF = json.load(open('filter_fit.json'))['knobs']
OUT = os.path.join('work', 'helix06'); os.makedirs(OUT, exist_ok=True)
with AudioFile(r'input\guitar_played.wav') as f:
    take, sr = f.read(f.frames).astype(np.float32), f.samplerate
with AudioFile(r'input\guitar_stem.wav') as f:
    stem = f.read(f.frames)[0]

def knobs(thr_db, drive):                 # drive on the amp's 0 to 10 scale
    return K4[10:12] + [(thr_db + 50) / 50, drive / 10] + KF[4:11]
def render(k, snap=1):
    pl = H.load(); pl.raw_state = S6
    for i, v in enumerate(k):             # keep inside 0 to 1: exactly 0.0 never reaches the plugin
        pl.parameters['knob_%02d' % (i + 1)].raw_value = float(np.clip(v, 1e-4, 1 - 1e-4))
    pl.parameters['snapshot_index'].raw_value = (snap - 1) / 7.0
    return pl(take, sr, buffer_size=512)[0]

def traits(y):
    h = int(0.05 * sr)
    db = 20 * np.log10(np.array([np.sqrt(np.mean(y[i:i + h] ** 2)) + 1e-9 for i in range(0, len(y) - h, h // 2)]))
    act = db > db.max() - 40
    rng = np.percentile(db[act], 90) - np.percentile(db[act], 10)
    n = 4096; w = np.hanning(n); fr = np.fft.rfftfreq(n, 1 / sr)
    P = np.abs(np.fft.rfft(np.array([y[i:i + n] * w for i in range(0, len(y) - n, n // 2)]), axis=1)) ** 2
    band = P[:, (fr >= 1000) & (fr < 5000)] + 1e-20
    flat = np.exp(np.mean(np.log(band), axis=1)) / np.mean(band, axis=1)
    loud = P.sum(1) > P.sum(1).max() * 1e-3
    return float(np.median(flat[loud])), float(rng)
def spec_err(y, step):
    n = 8192; w = np.hanning(n); fr = np.fft.rfftfreq(n, 1 / sr)
    e = 40 * 2 ** (np.arange(0, np.log2(16000 / 40) + 1e-9, step))
    sp = lambda x: np.array([10 * np.log10(p[(fr >= a) & (fr < b)].sum() + 1e-20) for p in [np.mean(np.abs(np.fft.rfft([x[i:i + n] * w for i in range(0, len(x) - n, n // 2)], axis=1)) ** 2, axis=0)] for a, b in zip(e[:-1], e[1:])])
    d = sp(stem) - sp(y); d -= d.mean(); return float(np.sqrt(np.mean(d ** 2)))

sf, sr_ = traits(stem)
print(f'stem: fuzz {sf:.3f}, loudness range {sr_:.1f} dB')
import sys
print('1. Drive sweep, compressor threshold 0 dB')
best = None
# optional: python fit_squash.py DRIVE  keeps that Drive and skips the sweep (the first run showed Drive barely
# changes the fuzz measure: 0.52 to 0.53 from Drive 2 to 8.2)
for dv in ([float(sys.argv[1])] if len(sys.argv) > 1 else (8.2, 7, 6, 5, 4, 3, 2)):
    f_, r_ = traits(render(knobs(0, dv)))
    print(f'   Drive {dv:4.1f}: fuzz {f_:.3f}  range {r_:.1f} dB')
    if best is None or abs(f_ - sf) < abs(best[1] - sf):
        best = (dv, f_)
drive = best[0]; print(f'   chosen Drive {drive}')
print('2. Threshold sweep at that Drive')
bt = None
for th in (-5, -10, -15, -20, -25, -30, -40):
    f_, r_ = traits(render(knobs(th, drive)))
    print(f'   Threshold {th:4d} dB: fuzz {f_:.3f}  range {r_:.1f} dB')
    if bt is None or abs(r_ - sr_) < abs(bt[1] - sr_):
        bt = (th, r_)
thr = bt[0]; print(f'   chosen Threshold {thr} dB')
y = render(knobs(thr, drive)); y5 = render(knobs(0, 8.2))
f_, r_ = traits(y)
print(f'3. result: fuzz {f_:.3f} (stem {sf:.3f}), range {r_:.1f} dB (stem {sr_:.1f})')
print(f'   spectral error to stem: {spec_err(y, 1 / 6):.2f} dB at 1/6 octave, {spec_err(y, 1 / 12):.2f} at 1/12 '
      f'(chain 5 settings: {spec_err(y5, 1 / 6):.2f}, {spec_err(y5, 1 / 12):.2f})')

def write(name, yy):
    g = np.sqrt(np.mean(stem ** 2)) / np.sqrt(np.mean(yy ** 2))
    yy = yy * g
    pk = np.abs(yy).max()
    if pk > 0.999:                        # pull the level down rather than clip
        yy = yy * 0.999 / pk
    with AudioFile(os.path.join(OUT, name), 'w', sr, 2, bit_depth=24) as f:
        f.write(np.stack([yy, yy]).astype(np.float32))
write('1_target_stem.wav', stem); write('2_dry_played.wav', take[0])
write('3_oct_on_squash.wav', y); write('4_oct_off_squash.wav', render(knobs(thr, drive), snap=2))
write('5_oct_on_chain5_settings.wav', y5)
json.dump({'drive': drive, 'threshold_db': thr, 'ratio': '6:1', 'knobs': [round(float(v), 4) for v in knobs(thr, drive)],
           'fuzz': {'stem': round(sf, 3), 'result': round(f_, 3)}, 'range_db': {'stem': round(sr_, 1), 'result': round(r_, 1)},
           'spectral_error_db': {'1_6': round(spec_err(y, 1 / 6), 2), '1_12': round(spec_err(y, 1 / 12), 2)}},
          open('squash_fit.json', 'w'), indent=1)
print('wrote', OUT)
