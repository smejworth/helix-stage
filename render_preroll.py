# render_preroll.py : fixes the smeared first note (owner: "why is the first note of my playing smooshed? it doesnt
# happen again when it loops"). Every render starts a fresh plugin and then sets the knobs, and Helix glides settings
# to new values instead of jumping, so the first fraction of a second played with settings still moving (measured:
# loop 1 matched loop 2 only 0.04 to 0.27 in the first 0.4 s, against 0.46 to 0.75 for loop 2 against loop 3).
# Two fixes are compared: 2.4 s of silence fed in first, or one pass of the loop fed in first (so the first note is
# set up exactly like the later ones: compressor, envelope filter and octave pitch tracker already running). The lead-in
# part of the output is cut off.
# Renders the owner's "ok" reference (chain 9 state, chain 9b settings), EQ-matched to the stem, and checks the start.
# Writes work\helix17\.
# usage: python -u render_preroll.py
import os, numpy as np, helixlab as H
from pedalboard.io import AudioFile
from scipy.signal import fftconvolve

S9 = open('chain9_state.bin', 'rb').read()
OUT = os.path.join('work', 'helix17'); os.makedirs(OUT, exist_ok=True)
with AudioFile(r'input\guitar_played.wav') as f:
    take, sr = f.read(f.frames).astype(np.float32), f.samplerate
with AudioFile(r'input\guitar_stem.wav') as f:
    stem = f.read(f.frames)[0]
RANGES = [(0, 1), (100, 2000), (0, 6000), (0, 1), (0.01, 1), (0.01, 2), (0.5, 10), (0, 1), (-50, 0), (0, 10)]
REF = [0.5, 100, 500, 0.1, 0.02, 0.8, 2, 1.0, -10, 8.2]
PRE = int(2.4 * sr)          # one pass of the 2.4 s loop
def render(v, preroll):
    pl = H.load(); pl.raw_state = S9
    for i, (x, (a, b)) in enumerate(zip(v, RANGES)):   # keep inside 0 to 1: exactly 0.0 never reaches the plugin
        pl.parameters['knob_%02d' % (i + 1)].raw_value = float(np.clip((x - a) / (b - a), 1e-4, 1 - 1e-4))
    pl.parameters['snapshot_index'].raw_value = 0.0
    if not preroll:
        return pl(take, sr, buffer_size=512)[0]
    lead = take[:, -int(2.4 * sr) - PRE:-int(2.4 * sr)] if preroll == 'loop' else np.zeros((take.shape[0], PRE), np.float32)
    x = np.concatenate([lead, take], axis=1)
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
def write(name, y):
    y = y * np.sqrt(np.mean(stem ** 2)) / np.sqrt(np.mean(y ** 2)); pk = np.abs(y).max()
    if pk > 0.999: y = y * 0.999 / pk
    with AudioFile(os.path.join(OUT, name), 'w', sr, 2, bit_depth=24) as f:
        f.write(np.stack([y, y]).astype(np.float32))
def start_check(y, label):
    L = int(2.4 * sr); seg = int(0.1 * sr)
    a = [np.corrcoef(y[k * seg:(k + 1) * seg], y[L + k * seg:L + (k + 1) * seg])[0, 1] for k in range(6)]
    b = [np.corrcoef(y[L + k * seg:L + (k + 1) * seg], y[2 * L + k * seg:2 * L + (k + 1) * seg])[0, 1] for k in range(6)]
    print(f'{label}: first 0.6 s, loop 1 vs 2: {" ".join(f"{x:.2f}" for x in a)}   loop 2 vs 3: {" ".join(f"{x:.2f}" for x in b)}')
y0 = render(REF, False); start_check(y0, 'no lead-in  ')
y1 = render(REF, 'silence'); start_check(y1, 'silent lead-in')
y2 = render(REF, 'loop'); start_check(y2, 'loop lead-in  ')
write('0_target_stem.wav', stem); write('1_reference_silent_lead_in.wav', match(y1)); write('2_reference_loop_lead_in.wav', match(y2)); write('3_reference_as_before.wav', match(y0))
print('wrote', OUT)

