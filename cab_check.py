# cab_check.py : is the cab block working in headless renders?
# A 4x12 cab with an 8 kHz high cut should leave very little energy above 10 kHz.
# Renders the take through a saved chain three ways and prints the share of energy above 10 kHz:
#   A: right after loading the state (as render_take.py does)
#   B: after waiting 5 seconds, on a fresh plugin
#   C: a second render on the same plugin as B (after a warm-up render)
# usage: python cab_check.py chain3_state.bin
import sys, time, numpy as np, helixlab as H
from pedalboard.io import AudioFile
with AudioFile(r'input\guitar_played.wav') as f:
    take, sr = f.read(f.frames).astype(np.float32), f.samplerate

def hf_share(y):
    S = np.abs(np.fft.rfft(y[0])) ** 2
    fr = np.fft.rfftfreq(len(y[0]), 1 / sr)
    return 10 * np.log10(np.sum(S[fr > 10000]) / np.sum(S))

def fresh():
    pl = H.load(); pl.raw_state = open(sys.argv[1], 'rb').read(); pl.parameters['knob_01'].raw_value = 0.82
    return pl

pl = fresh()
print('A  straight away          above 10 kHz: %.1f dB' % hf_share(pl(take, sr, buffer_size=512)))
pl = fresh(); time.sleep(5)
print('B  after 5 s wait         above 10 kHz: %.1f dB' % hf_share(pl(take, sr, buffer_size=512)))
print('C  second render, same    above 10 kHz: %.1f dB' % hf_share(pl(take, sr, buffer_size=512, reset=False)))
