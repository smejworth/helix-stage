# knob_test.py : can Python turn a control that the preset has bound to Knob 1?
# Loads a saved plugin state (unchanged), then renders the same test note several times:
#   Knob 1 low, middle, high, a repeat of middle (to see how much two identical renders differ),
#   and snapshot 1 and snapshot 2.
# For each render it prints the loudness (RMS) and two rough measures of harmonic content.
# usage: python knob_test.py template_state.bin
import sys, numpy as np, helixlab as H
from scipy.signal import sawtooth
SR = 48000
state_file = sys.argv[1] if len(sys.argv) > 1 else 'template_state.bin'

# test signal: 110 Hz sawtooth, amplitude 0.3, 2 seconds, 48 kHz
t = np.arange(2 * SR) / SR
x = (0.3 * sawtooth(2 * np.pi * 110 * t)).astype(np.float32)

def measure(y):
    seg = y[int(0.5 * SR):int(1.9 * SR)]              # steady part of the note
    rms = float(np.sqrt(np.mean(seg ** 2)))
    S = np.abs(np.fft.rfft(seg * np.hanning(len(seg)))) ** 2
    f = np.fft.rfftfreq(len(seg), 1 / SR)
    centroid = float(np.sum(f * S) / np.sum(S))         # higher = brighter, more upper harmonics
    hi = float(np.sum(S[f > 1000]) / np.sum(S))         # share of energy above 1 kHz
    def near(fr): return float(np.sum(S[(f > fr - 5) & (f < fr + 5)]))
    sub = near(55) / max(near(110), 1e-30)               # 55 Hz (octave down) relative to 110 Hz
    return rms, centroid, hi, sub

def fresh():
    pl = H.load()
    pl.raw_state = open(state_file, 'rb').read()
    return pl

def render(pl):
    return pl(np.stack([x, x]), SR, buffer_size=512)[0]

pl = fresh()
k = pl.parameters['knob_01']; s = pl.parameters['snapshot_index']
print('knob_01 after loading state: raw', round(k.raw_value, 4), 'shown as', k.string_value, '| range', k.range)
print('snapshot_index after loading state: raw', round(s.raw_value, 4), 'shown as', s.string_value, '| valid', s.valid_values)
print()
print('render            rms      centroid_Hz  share_above_1k  sub55_vs_110')
y0 = render(pl)
print(f'as loaded       {measure(y0)[0]:.4f}   {measure(y0)[1]:9.1f}    {measure(y0)[2]:.4f}          {measure(y0)[3]:.4f}')

outs = {}
for name, raw in [('knob low', 0.0), ('knob mid', 0.5), ('knob high', 1.0), ('knob mid again', 0.5)]:
    pl = fresh()
    pl.parameters['knob_01'].raw_value = raw
    shown = pl.parameters['knob_01'].string_value
    y = render(pl); outs[name] = y
    r, c, h, sb = measure(y)
    print(f'{name:15s} {r:.4f}   {c:9.1f}    {h:.4f}          {sb:.4f}   (knob raw {raw}, shown {shown})')

for snap in (1, 2):
    pl = fresh()
    pl.parameters['snapshot_index'].raw_value = (snap - 1) / 7.0     # 8 snapshots spread over 0..1
    shown = pl.parameters['snapshot_index'].string_value
    y = render(pl); outs['snap%d' % snap] = y
    r, c, h, sb = measure(y)
    print(f'snapshot {snap}      {r:.4f}   {c:9.1f}    {h:.4f}          {sb:.4f}   (shown {shown})')

def diff(a, b): return float(np.sqrt(np.mean((outs[a] - outs[b]) ** 2)))
print()
print('rms of difference, mid vs mid again (repeat noise):', round(diff('knob mid', 'knob mid again'), 6))
print('rms of difference, low vs high:', round(diff('knob low', 'knob high'), 6))
print('rms of difference, snapshot 1 vs 2:', round(diff('snap1', 'snap2'), 6))
np.savez('knob_test_out.npz', **{n.replace(' ', '_'): v for n, v in outs.items()})
print('saved knob_test_out.npz')
