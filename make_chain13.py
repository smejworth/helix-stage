# make_chain13.py : writes chain13_korn_down.hlx: chain 12 with the envelope filter (Auto Filter, before the amp)
# switched to sweep DOWN: each pick opens it and it then closes. The owner hears "the envelope close" on the notes,
# and the owner's research names an EHX Micro Synth at the start of the song, whose filter sweeps from a start to a stop
# frequency on each note. Every earlier chain used the factory direction (up). Knob slots as chain 12 (13 slots:
# Whammy Mix, filter Frequency, depth, Sens, Attack, Decay, Q, Mix, compressor Threshold, Drive, compressor Attack,
# Ratio, Release). Only the preset file is written.
# usage: python make_chain13.py
import json
p = json.load(open('chain12_korn_control.hlx'))
t = p['data']['tone']
p['data']['meta']['name'] = 'KORN CHAIN 13'
t['dsp0']['block2']['Direction'] = False
with open('chain13_korn_down.hlx', 'w') as f:
    json.dump(p, f, indent=1)
print('wrote chain13_korn_down.hlx, filter Direction', t['dsp0']['block2']['Direction'])
