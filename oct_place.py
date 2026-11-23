# oct_place.py : renders chain 8 with the octave-down in different places and blends, gives each render the stem's
# average frequency balance (the same matching EQ as match_eq.py, 8192 sample IR), then measures for each:
#   flutter at the half-note rate (26-34 Hz) and the note rate (54-64 Hz) in three bands (the "tearing", see tearing.py)
#   sub (25-35 Hz) and low A (50-60 Hz) energy relative to the whole file
# and prints the stem's values alongside. Writes the matched renders to work\helix08\ for listening.
# usage: python -u oct_place.py
import os, numpy as np, helixlab as H
from pedalboard.io import AudioFile
from scipy.signal import butter, sosfiltfilt, hilbert, resample_poly, fftconvolve

S8 = open('chain8_state.bin', 'rb').read()
OUT = os.path.join('work', 'helix08'); os.makedirs(OUT, exist_ok=True)
with AudioFile(r'input\guitar_played.wav') as f:
    take, sr = f.read(f.frames).astype(np.float32), f.samplerate
with AudioFile(r'input\guitar_stem.wav') as f:
    stem = f.read(f.frames)[0]
VARIANTS = [('A_before_amp_full', 1.0, 0.0), ('B_no_octave', 0.0, 0.0), ('C_before_amp_half', 0.5, 0.0),
            ('D_after_cab_half', 0.0, 0.5), ('E_after_cab_30pct', 0.0, 0.3), ('F_after_cab_full', 0.0, 1.0)]

def render(pre, post):
    pl = H.load(); pl.raw_state = S8
    for i, v in enumerate((pre, post)):      # keep inside 0 to 1: exactly 0.0 never reaches the plugin
        pl.parameters['knob_%02d' % (i + 1)].raw_value = float(np.clip(v, 1e-4, 1 - 1e-4))
    pl.parameters['snapshot_index'].raw_value = 0.0
    return pl(take, sr, buffer_size=512)[0]

N = 16384; fr = np.fft.rfftfreq(N, 1 / sr); w = np.hanning(N)
avg = lambda y: np.mean(np.abs(np.fft.rfft([y[i:i + N] * w for i in range(0, len(y) - N, N // 8)], axis=1)) ** 2, axis=0)
def match(y):
    # matching EQ, as in match_eq.py: stem over render, 1/24 octave smoothing, minimum phase, 8192 samples
    rd = 10 * np.log10(avg(stem) + 1e-20) - 10 * np.log10(avg(y) + 1e-20)
    sm = np.array([rd[(fr >= f * 2 ** (-1 / 48)) & (fr <= f * 2 ** (1 / 48))].mean() if f > 0 else rd[0] for f in fr])
    sm[fr < 35] = sm[np.argmin(np.abs(fr - 35))]; sm[fr > 16000] = sm[np.argmin(np.abs(fr - 16000))]; sm -= sm.max()
    mag = 10 ** (sm / 20); full = np.concatenate([mag, mag[-2:0:-1]])
    cep = np.fft.ifft(np.log(full + 1e-12)).real; n = len(full)
    fold = np.zeros(n); fold[0] = cep[0]; fold[1:n // 2] = 2 * cep[1:n // 2]; fold[n // 2] = cep[n // 2]
    h = np.fft.ifft(np.exp(np.fft.fft(fold))).real[:8192] * np.hanning(16384)[8192:]
    return fftconvolve(y, h)[:len(y)]
def flutter(y):
    out = []
    for lo, hi in ((150, 600), (600, 2000), (2000, 6000)):
        env = resample_poly(np.abs(hilbert(sosfiltfilt(butter(4, [lo, hi], 'band', fs=sr, output='sos'), y))), 1, 44)
        fs = sr / 44; n = 1024; mf = np.fft.rfftfreq(n, 1 / fs); wn = np.hanning(n)
        M = np.mean([np.abs(np.fft.rfft((s_ - s_.mean()) * wn)) ** 2 / s_.mean() ** 2 for s_ in [env[i:i + n] for i in range(0, len(env) - n, n // 2)]], axis=0)
        t = lambda a, b: 10 * np.log10(M[(mf >= a) & (mf < b)].sum())
        out.append((t(26, 34), t(54, 64)))
    return out
def lows(y):
    Nl = 65536; P = np.mean(np.abs(np.fft.rfft([y[i:i + Nl] * np.hanning(Nl) for i in range(0, len(y) - Nl, Nl // 2)], axis=1)) ** 2, axis=0)
    fl = np.fft.rfftfreq(Nl, 1 / sr); tot = P.sum()
    return 10 * np.log10(P[(fl >= 25) & (fl < 35)].sum() / tot), 10 * np.log10(P[(fl >= 50) & (fl < 60)].sum() / tot)
def line(name, y):
    fl = flutter(y); sb, la = lows(y)
    print(f'{name:20s} ' + '   '.join(f'{a:5.1f}/{b:5.1f}' for a, b in fl) + f'   sub {sb:6.1f}  lowA {la:6.1f}')
def write(name, y):
    y = y * np.sqrt(np.mean(stem ** 2)) / np.sqrt(np.mean(y ** 2)); pk = np.abs(y).max()
    if pk > 0.999: y = y * 0.999 / pk
    with AudioFile(os.path.join(OUT, name), 'w', sr, 2, bit_depth=24) as f:
        f.write(np.stack([y, y]).astype(np.float32))

print('flutter half-note rate / note rate (dB) in 150-600 Hz, 600 Hz-2 kHz, 2-6 kHz; sub 25-35 Hz and low A 50-60 Hz (dB of total)')
line('stem', stem); write('0_target_stem.wav', stem)
for name, pre, post in VARIANTS:
    y = match(render(pre, post))
    line(name, y); write(name + '.wav', y)
print('wrote', OUT)
