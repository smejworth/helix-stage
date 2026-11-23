# knob_sweep.py : finer check of Knob 1 (bound to Triangle Fuzz Sustain).
# Loads the saved plugin state unchanged, renders the same 110 Hz test note at six knob positions,
# and prints loudness (RMS), brightness (spectral centroid), share of energy above 1 kHz,
# and crest factor (peak divided by RMS; heavier fuzz squares the wave off, which lowers it).
# usage: python knob_sweep.py template_state.bin
import sys, numpy as np, helixlab as H
from scipy.signal import sawtooth
SR = 48000
state_file = sys.argv[1] if len(sys.argv) > 1 else 'template_state.bin'
t = np.arange(2 * SR) / SR
x = (0.3 * sawtooth(2 * np.pi * 110 * t)).astype(np.float32)

def measure(y):
    seg = y[int(0.5 * SR):int(1.9 * SR)]
    rms = float(np.sqrt(np.mean(seg ** 2)))
    crest = float(np.max(np.abs(seg)) / rms)
    S = np.abs(np.fft.rfft(seg * np.hanning(len(seg)))) ** 2
    f = np.fft.rfftfreq(len(seg), 1 / SR)
    return rms, float(np.sum(f * S) / np.sum(S)), float(np.sum(S[f > 1000]) / np.sum(S)), crest

print('knob   rms      centroid_Hz  share_above_1k  crest')
for raw in (0.0, 0.2, 0.4, 0.6, 0.8, 1.0):
    pl = H.load()
    pl.raw_state = open(state_file, 'rb').read()
    pl.parameters['knob_01'].raw_value = raw
    y = pl(np.stack([x, x]), SR, buffer_size=512)[0]
    r, c, h, cr = measure(y)
    print(f'{raw:.1f}    {r:.4f}   {c:9.1f}    {h:.4f}          {cr:.2f}')
