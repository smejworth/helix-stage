# render_sidesynth.py : chain 15 (Micro Synth stand-in on a parallel path, blended in at the join). First checks the
# parallel path is really wired in (the output must change when the synth path level moves from -40 to 0 dB), then
# renders blends for the owner's ear, everything else as the reference. Loop lead-in, EQ-matched, stand-in limiter.
# Writes work\helix20\.
# usage: python -u render_sidesynth.py
import os, subprocess, sys, numpy as np, helixlab as H
from pedalboard.io import AudioFile
from scipy.signal import fftconvolve

S = open('chain15_state.bin', 'rb').read()
OUT = os.path.join('work', 'helix20'); os.makedirs(OUT, exist_ok=True)
with AudioFile(r'input\guitar_played.wav') as f:
    take, sr = f.read(f.frames).astype(np.float32), f.samplerate
with AudioFile(r'input\guitar_stem.wav') as f:
    stem = f.read(f.frames)[0]
RANGES = [(0, 1), (0, 1), (0, 1), (0, 1), (0, 1), (0, 1), (100, 2000), (0, 6000), (0, 1), (0.01, 2), (0.5, 10), (0, 1),
          (-50, 0), (0.001, 0.1), (0, 1), (0, 1)]
def V(blevel, oct1=0.8, oct2=0.0, sustain=0.8, tone=0.5):
    # Whammy 50%, Boctaver dry 0, filter = reference (100 Hz, depth 500, Sens 0.1, Decay 0.8, Q 2, Mix 1),
    # compressor -10 dB 10 ms, Drive 8.2
    return [0.5, 0.0, oct1, oct2, sustain, tone, 100, 500, 0.1, 0.8, 2, 1.0, -10, 0.01, 0.82, blevel]
PRE = int(2.4 * sr)
def render(v, snap=1):
    pl = H.load(); pl.raw_state = S
    for i, (x, (a, b)) in enumerate(zip(v, RANGES)):   # keep inside 0 to 1: exactly 0.0 never reaches the plugin
        pl.parameters['knob_%02d' % (i + 1)].raw_value = float(np.clip((x - a) / (b - a), 1e-4, 1 - 1e-4))
    pl.parameters['snapshot_index'].raw_value = (snap - 1) / 7.0
    x = np.concatenate([take[:, -2 * PRE:-PRE], take], axis=1)   # one pass of the loop first, cut off below
    return pl(x, sr, buffer_size=512)[0][PRE:]
lo = render(V(0.0)); hi = render(V(1.0))
print(f'wiring check: synth path (fuzz Level) at 0 vs 1, output level {20*np.log10(np.sqrt(np.mean(lo**2))):.2f} vs {20*np.log10(np.sqrt(np.mean(hi**2))):.2f} dB, waveform correlation {np.corrcoef(lo, hi)[0, 1]:.3f}')
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
# fuzz Level 0.2 to 0.7 measured 99.8 to 100% the same as no synth, so only the top of its range and the sub voice are used
VERSIONS = [('1_synth_off_reference', V(0.0), 1), ('2_sub_and_fuzz_level_0_9', V(0.9), 1), ('3_sub_and_fuzz_level_1_0', V(1.0), 1),
            ('4_sub_only_quiet', V(0.0, oct1=0.4), 2), ('5_sub_only_loud', V(0.0, oct1=0.8), 2), ('6_fuzz_only_level_1_0', V(1.0), 3)]
for name, v, snap in VERSIONS:
    tmp = os.path.join(OUT, '_tmp.wav'); write(tmp, match(render(v, snap)))
    r = subprocess.run([sys.executable, 'master_limit.py', stem_path, tmp, os.path.join(OUT, name + '.wav')], capture_output=True, text=True)
    print(name, '|', r.stdout.strip())
os.remove(os.path.join(OUT, '_tmp.wav'))


