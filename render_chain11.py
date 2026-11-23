# render_chain11.py : renders chain 11 versions for the owner's ear, everything else as the "ok" reference:
#   A: the Auto Filter with its resonant peak moved (frequency and Q; owner: "its the q placement of the envelope
#      thats the key"), B: the Mutant Filter alone, C: the Mystery Filter alone. Each is EQ-matched to the stem.
# Writes work\helix16\.
# usage: python -u render_chain11.py
import os, numpy as np, helixlab as H
from pedalboard.io import AudioFile
from scipy.signal import fftconvolve

S = open('chain11_state.bin', 'rb').read()
OUT = os.path.join('work', 'helix16'); os.makedirs(OUT, exist_ok=True)
with AudioFile(r'input\guitar_played.wav') as f:
    take, sr = f.read(f.frames).astype(np.float32), f.samplerate
with AudioFile(r'input\guitar_stem.wav') as f:
    stem = f.read(f.frames)[0]
RANGES = [(0, 1), (100, 2000), (0.5, 10), (0, 1), (0, 1), (0, 1), (0, 1), (0, 1), (0, 1), (0, 1), (0, 1), (0, 1), (0, 1), (-50, 0)]
def V(af=(100, 2, 1.0), mu=(0.8, 0.15, 0.0), my=(0.14, 0.8, 0.48, 0.13, 0.97, 0.0)):
    return [0.5, *af, *mu, *my, -10]
AF_OFF = (100, 2, 0.0)
VERSIONS = [('A1_auto_100Hz_Q2_reference', V()), ('A2_auto_100Hz_Q6', V(af=(100, 6, 1.0))),
            ('A3_auto_200Hz_Q6', V(af=(200, 6, 1.0))), ('A4_auto_400Hz_Q6', V(af=(400, 6, 1.0))),
            ('A5_auto_200Hz_Q10', V(af=(200, 10, 1.0))),
            ('B1_mutant_peak8_gain1_5', V(af=AF_OFF, mu=(0.8, 0.15, 1.0))), ('B2_mutant_peak5_gain3', V(af=AF_OFF, mu=(0.5, 0.3, 1.0))),
            ('B3_mutant_peak10_gain5', V(af=AF_OFF, mu=(1.0, 0.5, 1.0))),
            ('C1_mystery_factory', V(af=AF_OFF, my=(0.14, 0.8, 0.48, 0.13, 0.97, 1.0))),
            ('C2_mystery_freq_0_3', V(af=AF_OFF, my=(0.3, 0.8, 0.48, 0.13, 0.97, 1.0))),
            ('C3_mystery_low_sharp', V(af=AF_OFF, my=(0.1, 1.0, 0.7, 0.13, 0.97, 1.0)))]
def render(v):
    pl = H.load(); pl.raw_state = S
    for i, (x, (a, b)) in enumerate(zip(v, RANGES)):   # keep inside 0 to 1: exactly 0.0 never reaches the plugin
        pl.parameters['knob_%02d' % (i + 1)].raw_value = float(np.clip((x - a) / (b - a), 1e-4, 1 - 1e-4))
    pl.parameters['snapshot_index'].raw_value = 0.0
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
def write(name, y):
    y = y * np.sqrt(np.mean(stem ** 2)) / np.sqrt(np.mean(y ** 2)); pk = np.abs(y).max()
    if pk > 0.999: y = y * 0.999 / pk
    with AudioFile(os.path.join(OUT, name), 'w', sr, 2, bit_depth=24) as f:
        f.write(np.stack([y, y]).astype(np.float32))
write('0_target_stem.wav', stem)
for name, v in VERSIONS:
    write(name + '.wav', match(render(v))); print('wrote', name)
