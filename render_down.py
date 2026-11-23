# render_down.py : renders chain 13 (envelope filter before the amp, sweeping DOWN: opens on each pick, then closes)
# with a few start points and sweep sizes; everything else is the owner's "ok" reference (Whammy 50%, compressor 6:1
# 10 ms -10 dB). Every render uses the loop lead-in (first note right), is EQ-matched to the stem, and goes through the
# stand-in mastering limiter from master_limit.py, so loudness and peak control equal the stem's.
# Writes work\helix19\.
# usage: python -u render_down.py
import os, subprocess, sys, numpy as np, helixlab as H
from pedalboard.io import AudioFile
from scipy.signal import fftconvolve

S = open('chain13_state.bin', 'rb').read()
OUT = os.path.join('work', 'helix19'); os.makedirs(OUT, exist_ok=True)
with AudioFile(r'input\guitar_played.wav') as f:
    take, sr = f.read(f.frames).astype(np.float32), f.samplerate
with AudioFile(r'input\guitar_stem.wav') as f:
    stem = f.read(f.frames)[0]
RANGES = [(0, 1), (100, 2000), (0, 6000), (0, 1), (0.01, 1), (0.01, 2), (0.5, 10), (0, 1), (-50, 0), (0, 10),
          (0.001, 0.1), (0, 5), (0.01, 1)]
def V(freq, depth, sens=0.1, decay=0.8, q=2):
    return [0.5, freq, depth, sens, 0.02, decay, q, 1.0, -10, 8.2, 0.01, 3, 0.1]
VERSIONS = [('1_down_100Hz_depth500', V(100, 500)), ('2_down_100Hz_depth1000', V(100, 1000)),
            ('3_down_200Hz_depth1500', V(200, 1500)), ('4_down_100Hz_depth2000_sens0_2', V(100, 2000, sens=0.2)),
            ('5_down_300Hz_depth2500_slow', V(300, 2500, decay=1.5))]
PRE = int(2.4 * sr)
def render(v):
    pl = H.load(); pl.raw_state = S
    for i, (x, (a, b)) in enumerate(zip(v, RANGES)):   # keep inside 0 to 1: exactly 0.0 never reaches the plugin
        pl.parameters['knob_%02d' % (i + 1)].raw_value = float(np.clip((x - a) / (b - a), 1e-4, 1 - 1e-4))
    pl.parameters['snapshot_index'].raw_value = 0.0
    x = np.concatenate([take[:, -2 * PRE:-PRE], take], axis=1)   # one pass of the loop first, cut off below
    return pl(x, sr, buffer_size=512)[0][PRE:]
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
def write(path, y):
    y = y * 0.5 / np.abs(y).max()
    with AudioFile(path, 'w', sr, 2, bit_depth=24) as f:
        f.write(np.stack([y, y]).astype(np.float32))
stem_path = os.path.join(OUT, '0_target_stem.wav'); write(stem_path, stem)
for name, v in VERSIONS:
    tmp = os.path.join(OUT, '_tmp.wav'); write(tmp, match(render(v)))
    r = subprocess.run([sys.executable, 'master_limit.py', stem_path, tmp, os.path.join(OUT, name + '.wav')], capture_output=True, text=True)
    print(name, '|', r.stdout.strip())
os.remove(os.path.join(OUT, '_tmp.wav'))
