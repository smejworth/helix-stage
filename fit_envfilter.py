# fit_envfilter.py : sets chain 9's envelope filter (Auto Filter) and compressor by measuring against the stem.
# Every render first gets the stem's average frequency balance (matching EQ, as match_eq.py), so only the way the
# sound MOVES is compared. Three measurements, each compared with the stem's:
#   after-pick profile : brightness (centroid) in 5 time slots after each pick attack (attacks found in the clean take)
#   riff profile       : brightness every 0.1 s through the 2.4 s riff, the 4 repeats averaged
#   loudness range     : 10th to 90th percentile of 50 ms loudness (the squash)
# score = rms difference of after-pick profile / 100 Hz + rms difference of riff profile / 100 Hz + 2 x range difference (dB)
# One setting at a time, a few values each, keeping the best before moving on (about 35 renders; one process manages
# about 55). Writes work\helix09\ and envfilter_fit.json.
# usage: python -u fit_envfilter.py
import os, json, numpy as np, helixlab as H
from pedalboard.io import AudioFile
from scipy.signal import fftconvolve

S9 = open('chain9_state.bin', 'rb').read()
OUT = os.path.join('work', 'helix09'); os.makedirs(OUT, exist_ok=True)
with AudioFile(r'input\guitar_played.wav') as f:
    take, sr = f.read(f.frames).astype(np.float32), f.samplerate
with AudioFile(r'input\guitar_stem.wav') as f:
    stem = f.read(f.frames)[0]
dry = take[0]
# knob order: whammy mix, freq Hz, depth Hz, sens, attack s, decay s, Q, filter mix, threshold dB, drive (0-10)
RANGES = [(0, 1), (100, 2000), (0, 6000), (0, 1), (0.01, 1), (0.01, 2), (0.5, 10), (0, 1), (-50, 0), (0, 10)]
NAMES = ['octave mix', 'filter freq Hz', 'sweep depth Hz', 'sensitivity', 'attack s', 'decay s', 'filter Q', 'filter mix', 'comp threshold dB', 'drive']
cur = [0.5, 300, 2000, 0.5, 0.2, 0.5, 4, 1.0, -25, 8.2]
knob = lambda v: [(x - a) / (b - a) for x, (a, b) in zip(v, RANGES)]

def render(v, snap=1):
    pl = H.load(); pl.raw_state = S9
    for i, k in enumerate(knob(v)):           # keep inside 0 to 1: exactly 0.0 never reaches the plugin
        pl.parameters['knob_%02d' % (i + 1)].raw_value = float(np.clip(k, 1e-4, 1 - 1e-4))
    pl.parameters['snapshot_index'].raw_value = (snap - 1) / 7.0
    return pl(take, sr, buffer_size=512)[0]

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

# pick attacks in the clean take (spectral flux), shared by all measurements
n2, hop = 2048, 1024; fr2 = np.fft.rfftfreq(n2, 1 / sr); w2 = np.hanning(n2)
frames = lambda y: np.abs(np.fft.rfft(np.array([y[i:i + n2] * w2 for i in range(0, len(y) - n2, hop)]), axis=1)) ** 2
PC = np.sqrt(frames(dry)); flux = np.r_[0, np.clip(np.diff(np.log(PC + 1e-9), axis=0), 0, None).sum(1)]
thr_ = np.median(flux) + 2 * np.std(flux)
att = np.r_[False, (flux[1:-1] > thr_) & (flux[1:-1] >= flux[:-2]) & (flux[1:-1] >= flux[2:]), False]
since = np.zeros(len(att)); t = 99.0
for i in range(len(att)):
    t = 0.0 if att[i] else t + hop / sr; since[i] = t
SLOTS = [(0, 0.05), (0.05, 0.1), (0.1, 0.2), (0.2, 0.35), (0.35, 99)]

def measure(y):
    P = frames(y); m = min(len(P), len(since)); P = P[:m]
    cen = (P * fr2).sum(1) / (P.sum(1) + 1e-20)
    loud = 10 * np.log10(P.sum(1) + 1e-20); k = loud > loud.max() - 25
    ap = np.array([np.median(cen[k & (since[:m] >= a) & (since[:m] < b)]) for a, b in SLOTS])
    hop10 = int(0.1 * sr); n4 = 4096; w4 = np.hanning(n4); fr4 = np.fft.rfftfreq(n4, 1 / sr)
    Q = np.abs(np.fft.rfft(np.array([y[i:i + n4] * w4 for i in range(0, len(y) - n4, hop10)]), axis=1)) ** 2
    c4 = (Q * fr4).sum(1) / (Q.sum(1) + 1e-20)
    rp = np.mean([c4[r * 24:r * 24 + 21] for r in range(4) if r * 24 + 21 <= len(c4)], axis=0)
    h50 = int(0.05 * sr)
    db = 20 * np.log10(np.array([np.sqrt(np.mean(y[i:i + h50] ** 2)) + 1e-9 for i in range(0, len(y) - h50, h50 // 2)]))
    act = db > db.max() - 40
    return ap, rp, float(np.percentile(db[act], 90) - np.percentile(db[act], 10))

SAP, SRP, SRG = measure(stem)
def score(y):
    ap, rp, rg = measure(y)
    s = np.sqrt(np.mean((ap - SAP) ** 2)) / 100 + np.sqrt(np.mean((rp - SRP) ** 2)) / 100 + 2 * abs(rg - SRG)
    return float(s), ap, rp, rg
print('stem after-pick profile (Hz):', ' '.join(f'{x:.0f}' for x in SAP), f'  loudness range {SRG:.1f} dB')
print('stem riff profile (Hz):', ' '.join(f'{x:.0f}' for x in SRP))

count = [0]
def evaluate(v):
    count[0] += 1
    s, ap, rp, rg = score(match(render(v)))
    print(f'  [{count[0]:2d}] score {s:5.2f}  after-pick {" ".join(f"{x:.0f}" for x in ap)}  range {rg:.1f}')
    return s
best = evaluate(cur)
SWEEPS = [(3, [0.1, 0.3, 0.7, 0.9]), (1, [150, 600, 1000]), (2, [500, 1000, 4000]), (4, [0.02, 0.08, 0.4]),
          (5, [0.15, 1.0, 1.6]), (6, [1, 7]), (7, [0.4, 0.7]), (8, [-15, -20, -30, -35]), (3, None), (1, None)]
for idx, vals in SWEEPS:
    if vals is None:                          # second, finer look at sensitivity and frequency around the best
        c = cur[idx]; vals = [c * 0.7, c * 1.3]
    print(f'{NAMES[idx]} (now {cur[idx]}):')
    for v in vals:
        trial = list(cur); trial[idx] = float(np.clip(v, *RANGES[idx]))
        s = evaluate(trial)
        if s < best:
            best, cur = s, trial
    print(f'  keep {NAMES[idx]} = {cur[idx]:.3g}  (score {best:.2f})')

y = match(render(cur)); s, ap, rp, rg = score(y)
print('final settings:', ', '.join(f'{n} {v:.3g}' for n, v in zip(NAMES, cur)))
print(f'final score {s:.2f}; after-pick {" ".join(f"{x:.0f}" for x in ap)} (stem {" ".join(f"{x:.0f}" for x in SAP)}); range {rg:.1f} (stem {SRG:.1f})')
print('riff profile, render:', ' '.join(f'{x:.0f}' for x in rp))
nf = list(cur); nf[7] = 0.0; y0 = match(render(nf)); s0 = score(y0)[0]
print(f'same settings with the filter mix at 0 (no filter): score {s0:.2f}')
def write(name, yy):
    yy = yy * np.sqrt(np.mean(stem ** 2)) / np.sqrt(np.mean(yy ** 2)); pk = np.abs(yy).max()
    if pk > 0.999: yy = yy * 0.999 / pk
    with AudioFile(os.path.join(OUT, name), 'w', sr, 2, bit_depth=24) as f:
        f.write(np.stack([yy, yy]).astype(np.float32))
write('1_target_stem.wav', stem); write('3_envelope_filter.wav', y); write('4_same_without_filter.wav', y0)
json.dump({'settings': dict(zip(NAMES, [round(float(v), 4) for v in cur])), 'knobs': [round(float(k), 4) for k in knob(cur)],
           'score': round(s, 2), 'score_without_filter': round(s0, 2), 'renders': count[0] + 2}, open('envfilter_fit.json', 'w'), indent=1)
print('wrote', OUT)
