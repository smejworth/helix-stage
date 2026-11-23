# match_eq.py : makes a "matching EQ": a filter whose curve is exactly the difference between the stem's average
# spectrum and a render's, so that the render filtered through it has the stem's frequency balance.
#   1. average spectrum of each file (many overlapping FFTs), ratio stem / render, smoothed to 1/24 octave
#      (finer smoothing would copy differences between the notes played, not the tone)
#   2. turns that curve into a filter (an impulse response, IR: the filter's "fingerprint", what a cab IR also is),
#      minimum phase so it adds no delay or pre-echo, as a speaker cab IR behaves
#   3. applies it to the render in Python and measures the remaining difference at 1/6, 1/12 and 1/24 octave
#   4. writes the IR at 48 kHz in two lengths: 8192 samples (very fine) and 2048 (the longest a Helix IR block
#      takes; coarser below about 300 Hz). Writes the filtered renders for listening.
# This does not change the amp, compression or any timing; it only matches the average frequency balance.
# usage: python match_eq.py STEM RENDER OUT_FOLDER
import os, sys, numpy as np
from pedalboard.io import AudioFile
from scipy.signal import fftconvolve, resample_poly

def load(p):
    with AudioFile(p) as f:
        return f.read(f.frames)[0], f.samplerate
s, sr = load(sys.argv[1]); r, _ = load(sys.argv[2]); out = sys.argv[3]; os.makedirs(out, exist_ok=True)
N = 16384
fr = np.fft.rfftfreq(N, 1 / sr); w = np.hanning(N)
avg = lambda y: np.mean(np.abs(np.fft.rfft([y[i:i + N] * w for i in range(0, len(y) - N, N // 8)], axis=1)) ** 2, axis=0)
ratio_db = 10 * np.log10(avg(s) + 1e-20) - 10 * np.log10(avg(r) + 1e-20)
# 1/24 octave smoothing: average the dB curve over a window 1/24 octave wide around each frequency
sm = np.empty_like(ratio_db)
for i, f in enumerate(fr):
    lo, hi = f * 2 ** (-1 / 48), f * 2 ** (1 / 48)
    m = (fr >= lo) & (fr <= hi)
    sm[i] = ratio_db[m].mean() if m.any() else ratio_db[i]
# outside 35 Hz to 16 kHz both files are nearly empty; hold the curve flat there so noise is not boosted
sm[fr < 35] = sm[np.argmin(np.abs(fr - 35))]; sm[fr > 16000] = sm[np.argmin(np.abs(fr - 16000))]
sm -= np.max(sm)                                  # the filter only cuts, so it can never clip

def min_phase_ir(mag_db, n_out):
    # minimum phase from a magnitude curve via the cepstrum (standard method): same EQ curve, no added delay
    mag = 10 ** (mag_db / 20)
    full = np.concatenate([mag, mag[-2:0:-1]])
    cep = np.fft.ifft(np.log(full + 1e-12)).real
    n = len(full); fold = np.zeros(n); fold[0] = cep[0]; fold[1:n // 2] = 2 * cep[1:n // 2]; fold[n // 2] = cep[n // 2]
    h = np.fft.ifft(np.exp(np.fft.fft(fold))).real[:n_out]
    h *= np.hanning(2 * n_out)[n_out:]           # fade the tail so the cut-off is smooth
    return h

def spec_err(y, step):
    e = 40 * 2 ** (np.arange(0, np.log2(16000 / 40) + 1e-9, step))
    a, b = avg(s), avg(y)
    d = np.array([10 * np.log10(a[(fr >= x) & (fr < z)].sum() / b[(fr >= x) & (fr < z)].sum()) for x, z in zip(e[:-1], e[1:])])
    d -= d.mean(); return float(np.sqrt(np.mean(d ** 2)))

def write(name, y, rate=sr):
    with AudioFile(os.path.join(out, name), 'w', rate, 2 if rate == sr else 1, bit_depth=24) as f:
        f.write((np.stack([y, y]) if rate == sr else y[None]).astype(np.float32))
def level(y):
    y = y * np.sqrt(np.mean(s ** 2)) / np.sqrt(np.mean(y ** 2)); pk = np.abs(y).max()
    return y * 0.999 / pk if pk > 0.999 else y

print(f'before:          error {spec_err(r, 1 / 6):.2f} dB at 1/6 octave, {spec_err(r, 1 / 12):.2f} at 1/12, {spec_err(r, 1 / 24):.2f} at 1/24')
for taps in (8192, 2048):
    h = min_phase_ir(sm, taps)
    y = fftconvolve(r, h)[:len(r)]
    print(f'IR {taps:4d} samples: error {spec_err(y, 1 / 6):.2f} dB at 1/6 octave, {spec_err(y, 1 / 12):.2f} at 1/12, {spec_err(y, 1 / 24):.2f} at 1/24')
    write(f'3_matched_{taps}.wav', level(y))
    h48 = resample_poly(h, 160, 147) if sr == 44100 else h     # Helix works at 48 kHz
    h48 *= 0.5 / np.abs(h48).max()
    write(f'match_ir_{taps}_48k.wav', h48[:taps], 48000)
write('1_target_stem.wav', level(s)); write('2_render_before.wav', level(r))
c = 40 * 2 ** (np.arange(0, np.log2(16000 / 40), 1 / 3))
print('matching curve, every 1/3 octave (dB):', '  '.join(f'{x:.0f}:{np.interp(x, fr, sm):+.1f}' for x in c))
