# render_hp.py : owner: "a whole lot of smooshy nastyness at the bottom end, can you try high passing the original
# signal before it hits anything else?". Filters the clean take with a high pass (12 dB per octave, like a typical
# low cut block) BEFORE it enters the Helix chain, at several cutoffs, then renders the reference settings (chain 9b,
# envelope filter before the amp). Drop A's lowest note is A1 = 55 Hz, so cutoffs above that thin its fundamental.
# Each render is EQ-matched to the stem, so only what the high pass does to the distortion and filter is heard, not
# a simple loss of bass. Also prints the filter-movement score (filter_motion.py's measure; lower = closer to the
# stem's movement) for each cutoff. Writes work\helix15\.
# usage: python -u render_hp.py
import os, numpy as np, helixlab as H
from pedalboard.io import AudioFile
from scipy.signal import fftconvolve, butter, sosfilt

S9 = open('chain9_state.bin', 'rb').read()
OUT = os.path.join('work', 'helix15'); os.makedirs(OUT, exist_ok=True)
with AudioFile(r'input\guitar_played.wav') as f:
    take, sr = f.read(f.frames).astype(np.float32), f.samplerate
with AudioFile(r'input\guitar_stem.wav') as f:
    stem = f.read(f.frames)[0]
RANGES = [(0, 1), (100, 2000), (0, 6000), (0, 1), (0.01, 1), (0.01, 2), (0.5, 10), (0, 1), (-50, 0), (0, 10)]
REF = [0.5, 100, 500, 0.1, 0.02, 0.8, 2, 1.0, -10, 8.2]
def render(v, x):
    pl = H.load(); pl.raw_state = S9
    for i, (k, (a, b)) in enumerate(zip(v, RANGES)):   # keep inside 0 to 1: exactly 0.0 never reaches the plugin
        pl.parameters['knob_%02d' % (i + 1)].raw_value = float(np.clip((k - a) / (b - a), 1e-4, 1 - 1e-4))
    pl.parameters['snapshot_index'].raw_value = 0.0
    return pl(x, sr, buffer_size=512)[0]
def highpass(x, fc):
    return sosfilt(butter(2, fc, 'high', fs=sr, output='sos'), x, axis=-1).astype(np.float32)

N, HOP = 2048, 1024
edges = 100 * 2 ** (np.arange(0, np.log2(3000 / 100) + 1e-9, 1 / 6))
fr = np.fft.rfftfreq(N, 1 / sr); w = np.hanning(N)
def shape(y):
    P = np.abs(np.fft.rfft(np.array([y[i:i + N] * w for i in range(0, len(y) - N, HOP)]), axis=1)) ** 2
    B = 10 * np.log10(np.array([[p[(fr >= a) & (fr < b)].sum() for a, b in zip(edges[:-1], edges[1:])] for p in P]) + 1e-20)
    return B - B.mean(1, keepdims=True)
L = int(round(2.4 * sr / HOP))
def motion(y, base):
    B = shape(y); n = min(len(B), len(base)); D = B[:n] - base[:n]; D -= D.mean(0)
    F = np.mean([D[k * L:(k + 1) * L] for k in range(3)], axis=0)
    return np.array([np.convolve(F[:, j], np.ones(3) / 3, mode='same') for j in range(F.shape[1])]).T

Nm = 16384; frm = np.fft.rfftfreq(Nm, 1 / sr); wm = np.hanning(Nm)
avg = lambda y: np.mean(np.abs(np.fft.rfft([y[i:i + Nm] * wm for i in range(0, len(y) - Nm, Nm // 8)], axis=1)) ** 2, axis=0)
AS = avg(stem)
def match(y):
    rd = 10 * np.log10(AS + 1e-20) - 10 * np.log10(avg(y) + 1e-20)
    sm = np.array([rd[(frm >= f * 2 ** (-1 / 48)) & (frm <= f * 2 ** (1 / 48))].mean() if f > 0 else rd[0] for f in frm])
    sm[frm < 35] = sm[np.argmin(np.abs(frm - 35))]; sm[frm > 16000] = sm[np.argmin(np.abs(frm - 16000))]; sm -= sm.max()
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
nf = list(REF); nf[7] = 0.0
for fc in (0, 80, 120, 180, 250):
    x = take if fc == 0 else highpass(take, fc)
    y = render(REF, x); base = shape(render(nf, x))
    s = float(np.sqrt(np.mean((motion(y, base) - motion(stem, base)) ** 2)))
    name = 'hp_none_reference' if fc == 0 else f'hp_{fc}Hz'
    write(name + '.wav', match(y)); print(f'wrote {name}   movement score {s:.3f}')
