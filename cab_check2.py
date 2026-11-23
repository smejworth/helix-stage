# cab_check2.py : does the cab start working if the plugin's editor window is opened once in this process?
# Loads the saved state, renders (before), opens the editor for 4 seconds (it closes by itself, no clicks needed),
# then renders again (after). Prints the share of energy above 10 kHz for each; a working 4x12 cab should push it far down.
# usage: python cab_check2.py chain3_state.bin
import sys, threading, numpy as np, helixlab as H
from pedalboard.io import AudioFile
with AudioFile(r'input\guitar_played.wav') as f:
    take, sr = f.read(f.frames).astype(np.float32), f.samplerate

def hf_share(y):
    S = np.abs(np.fft.rfft(y[0])) ** 2
    fr = np.fft.rfftfreq(len(y[0]), 1 / sr)
    return 10 * np.log10(np.sum(S[fr > 10000]) / np.sum(S))

pl = H.load(); pl.raw_state = open(sys.argv[1], 'rb').read(); pl.parameters['knob_01'].raw_value = 0.82
print('before editor   above 10 kHz: %.1f dB' % hf_share(pl(take, sr, buffer_size=512)))
ev = threading.Event(); t = threading.Timer(4, ev.set); t.daemon = True; t.start()
pl.show_editor(ev)
print('after editor    above 10 kHz: %.1f dB' % hf_share(pl(take, sr, buffer_size=512)))
