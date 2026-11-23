# make_chain12.py : writes chain12_korn_control.hlx: chain 9 (the owner's "ok" reference chain) with the
# compressor's Attack, Ratio and Release added to the knobs, to tame the peaks. Owner: "the original sounds louder
# and more controlled still". Measured: the reference's peaks stand 15.3 dB above its average level against 13.4 dB
# for the stem, which also made the level-matched file 1.9 dB quieter. A faster attack and higher ratio catch peaks.
# Knob slots 1 to 10 as chain 9 (Whammy Mix, envelope filter x7, compressor Threshold, Drive), plus:
#   11 compressor Attack 0.001 to 0.1 s   12 compressor Ratio 0 to 5 (list position: 2:1 3:1 4:1 6:1 10:1 20:1)
#   13 compressor Release 0.01 to 1 s
# Envelope filter values in the file set to the chain 9b settings (the knobs set them at render time anyway).
# Only the preset file is written.
# usage: python make_chain12.py
import json
p = json.load(open('chain9_korn_envfilter.hlx'))
t = p['data']['tone']
p['data']['meta']['name'] = 'KORN CHAIN 12'
t['dsp0']['block2'].update({'Frequency': 100, 'FreqDepth': 500, 'Sens': 0.1, 'Attack': 0.02, 'Decay': 0.8, 'FilterQ': 2, 'Mix': 1})
t['dsp0']['block5'].update({'Ratio': 3, 'Threshold': -10})
A = lambda lo, hi, prm: {'@min': float(lo), '@max': float(hi), '@param': 'dsp0.' + prm}
t['automation']['@assignments'] += [A(0.001, 0.1, 'block5.Attack'), A(0, 5, 'block5.Ratio'), A(0.01, 1, 'block5.Release')]
with open('chain12_korn_control.hlx', 'w') as f:
    json.dump(p, f, indent=1)
print('wrote chain12_korn_control.hlx with', len(t['automation']['@assignments']), 'knob assignments')
