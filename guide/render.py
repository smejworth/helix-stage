# render.py : plays a dry DI take through a saved Helix Native state and writes the result as a WAV.
# The first pass is a lead-in that is cut off again: without it the first note comes out smeared.
# usage: python render.py STATE.bin DI.wav OUT.wav
import sys, numpy as np, pedalboard
from pedalboard.io import AudioFile
PLUGIN = r'C:\Program Files\Common Files\VST3\Line 6\Helix Native (x64).vst3'
state, di_path, out_path = sys.argv[1:4]
with AudioFile(di_path) as f:
    di, sr = f.read(f.frames)[:1].astype(np.float32), f.samplerate   # first channel only
di = np.concatenate([di, di])                 # Helix Native wants two input channels: the same signal on both
pl = pedalboard.load_plugin(PLUGIN)
pl.raw_state = open(state, 'rb').read()      # loaded exactly as saved, never edited
pre = min(int(2.4 * sr), di.shape[1])         # lead-in length: 2.4 s, or the whole take if shorter
x = np.concatenate([di[:, -pre:], di], axis=1)
y = pl(x, sr, buffer_size=512)[0][pre:]
y = y * 0.5 / np.abs(y).max()                 # normalise to half scale so nothing clips
with AudioFile(out_path, 'w', sr, 2, bit_depth=24) as f:
    f.write(np.stack([y, y]).astype(np.float32))
print('wrote', out_path)
