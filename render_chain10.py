# render_chain10.py : renders a few chain 10 versions that make the envelope filter more aggressive, in different
# ways, for the owner to judge by ear (measurement could not isolate the wow; see docs/decisions.md). Each render
# gets the stem's average frequency balance (matching EQ, as match_eq.py) so only the filter behaviour differs.
#   1 reference : chain 9b settings, filter before the amp only (what the owner called closer but buried)
#   2 pre_strong: filter before the amp with a bigger sweep (1500 Hz), sharper peak (Q 5), more sensitive (0.3)
#   3 post_mid  : chain 9b plus the filter after everything, half mixed in (sweep 400 Hz up by 1500 Hz, Q 4)
#   4 post_full : chain 9b plus the filter after everything, fully on, bigger and sharper (sweep 2500 Hz, Q 6)
#   5 both      : 2 and 3 together
# Writes work\helix10\.
# usage: python -u render_chain10.py
import os, numpy as np, helixlab as H
from pedalboard.io import AudioFile
from scipy.signal import fftconvolve

S = open('chain10_state.bin', 'rb').read()
OUT = os.path.join('work', 'helix10'); os.makedirs(OUT, exist_ok=True)
with AudioFile(r'input\guitar_played.wav') as f:
    take, sr = f.read(f.frames).astype(np.float32), f.samplerate
with AudioFile(r'input\guitar_stem.wav') as f:
    stem = f.read(f.frames)[0]
RANGES = [(0, 1), (100, 2000), (0, 6000), (0, 1), (0.01, 1), (0.01, 2), (0.5, 10), (0, 1), (-50, 0),
          (100, 3000), (0, 6000), (0, 1), (0.005, 1), (0.01, 2), (0.5, 10), (0, 1)]
PRE = [0.5, 100, 500, 0.1, 0.02, 0.8, 2, 1.0, -10]           # chain 9b result
PRE_STRONG = [0.5, 100, 1500, 0.3, 0.02, 0.8, 5, 1.0, -10]
POST_OFF = [400, 1500, 0.3, 0.02, 0.4, 4, 0.0]
POST_MID = [400, 1500, 0.3, 0.02, 0.4, 4, 0.6]
POST_FULL = [400, 2500, 0.5, 0.02, 0.4, 6, 1.0]
VERSIONS = [('1_reference', PRE + POST_OFF), ('2_pre_strong', PRE_STRONG + POST_OFF), ('3_post_mid', PRE + POST_MID),
            ('4_post_full', PRE + POST_FULL), ('5_both', PRE_STRONG + POST_MID)]

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
