# render_take.py : runs the owner's clean take through a saved Helix chain at a chosen snapshot and Knob 1 settings.
# The plugin state file is loaded unchanged. Nothing about the plugin or its presets is edited.
# Every render is scaled to the same loudness (RMS) as the stem, so a listener compares tone, not volume.
# Writes WAV files into work\<out folder>\ next to copies of the stem and the dry take.
# usage: python render_take.py STATE_FILE OUT_FOLDER SNAPSHOT NAME=KNOB [NAME=KNOB ...]
#   example: python render_take.py chain3_state.bin helix03 1 3_oct_on_drive8=0.82
#   (helix01 used template_state.bin; helix02 used chain2_state.bin)
import os, sys, numpy as np, helixlab as H
from pedalboard.io import AudioFile

STATE, OUT, SNAP = sys.argv[1], sys.argv[2], int(sys.argv[3])
JOBS = [(a.split('=')[0], float(a.split('=')[1])) for a in sys.argv[4:]]
IN_DIR = os.path.join('input')
OUT_DIR = os.path.join('work', OUT)
os.makedirs(OUT_DIR, exist_ok=True)

def read(name):
    with AudioFile(os.path.join(IN_DIR, name)) as f:
        return f.read(f.frames), f.samplerate      # array shape (channels, samples)

def write(name, audio, sr):
    with AudioFile(os.path.join(OUT_DIR, name), 'w', sr, audio.shape[0], bit_depth=24) as f:
        f.write(audio)

def rms(a):
    return float(np.sqrt(np.mean(a[0] ** 2)))

stem, sr = read('guitar_stem.wav')
take, sr2 = read('guitar_played.wav')
assert sr == sr2
write('1_target_stem.wav', stem, sr)
write('2_dry_played.wav', take, sr)
target_rms = rms(stem)

print('file                       raw_rms  raw_peak  gain_dB  peak_after')
for name, knob in JOBS:
    pl = H.load()
    pl.raw_state = open(STATE, 'rb').read()
    pl.parameters['knob_01'].raw_value = min(max(knob, 1e-4), 1 - 1e-4)   # exactly 0.0 would not reach the plugin
    pl.parameters['snapshot_index'].raw_value = (SNAP - 1) / 7.0   # 8 snapshots spread over 0 to 1
    y = pl(take.astype(np.float32), sr, buffer_size=512)
    y = np.stack([y[0], y[0]])                     # keep it dual mono like the inputs
    g = target_rms / max(rms(y), 1e-9)
    out = y * g
    print(f'{name + ".wav":26s} {rms(y):.4f}   {np.abs(y).max():.4f}   {20 * np.log10(g):6.1f}   {np.abs(out).max():.3f}')
    write(name + '.wav', np.clip(out, -1, 1).astype(np.float32), sr)
print('written to', OUT_DIR)
