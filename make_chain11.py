# make_chain11.py : writes chain11_korn_filters.hlx to try other envelope filter models before the amp, with the
# owner's "ok" reference otherwise (chain 9b settings). Owner: the Q placement of the envelope is the key.
#   block0 gate -> block1 Whammy -> block2 Auto Filter -> block3 Mutant Filter -> block4 Mystery Filter
#   -> block5 Rectifier (Drive 8.2) -> block6 cab -> block7 Deluxe Comp 6:1
# Each filter's Mix is on a knob, so any one can be heard alone (Mix 0 lets the signal pass untouched).
# Auto Filter fixed at the chain 9b values except Frequency and Q; Mutant Filter in band pass, Range Low, sweeping
# up (as the editor showed when the model was picked); Mystery Filter starts from a factory preset's values.
# Knob slots:
#   1 Whammy Mix 0-1
#   2 Auto Filter Frequency 100-2000 Hz, 3 Auto Filter Q 0.5-10, 4 Auto Filter Mix 0-1
#   5 Mutant Peak 0-1 (shown 0-10), 6 Mutant Gain 0-1 (sensitivity, shown 0-10), 7 Mutant Mix 0-1
#   8 Mystery Frequency 0-1, 9 Mystery Resonance 0-1, 10 Mystery Sensitivity 0-1, 11 Mystery Attack 0-1,
#   12 Mystery Release 0-1, 13 Mystery Mix 0-1
#   14 compressor Threshold -50-0 dB
# Model ids and settings were read from the editor (probe_mutant.hlx) and a factory preset. Only the preset is written.
# usage: python make_chain11.py
import json
p = json.load(open('chain9_korn_envfilter.hlx'))
t = p['data']['tone']
p['data']['meta']['name'] = 'KORN CHAIN 11'
o = t['dsp0']
base = {'@no_snapshot_bypass': False, '@path': 0, '@stereo': False, '@type': 0, '@enabled': True}
new = {k: v for k, v in o.items() if not k.startswith('block')}
new['block0'] = o['block0']
new['block1'] = o['block1']
new['block2'] = dict(o['block2'], **{'Frequency': 100, 'FreqDepth': 500, 'Sens': 0.1, 'Attack': 0.02, 'Decay': 0.8, 'FilterQ': 2, 'Mix': 1})
new['block3'] = dict(base, **{'@model': 'HD2_FilterMutantFilter', '@position': 3, 'Drive': True, 'Gain': 0.15, 'Level': 1.0,
                              'Mix': 0, 'Mode': 1, 'Peak': 0.8, 'Range': False})
new['block4'] = dict(base, **{'@model': 'HD2_FilterMysterFilter', '@position': 4, 'Frequency': 0.14, 'Resonance': 0.8,
                              'Release': 0.97, 'Sensitivity': 0.48, 'Attack': 0.13, 'Mix': 0, 'Level': -1})
new['block5'] = dict(o['block3'], **{'@position': 5, 'Drive': 0.82})
new['block6'] = dict(o['block4'], **{'@position': 6})
new['block7'] = dict(o['block5'], **{'@position': 7, 'Threshold': -10, 'Ratio': 3})
t['dsp0'] = new
A = lambda lo, hi, prm: {'@min': float(lo), '@max': float(hi), '@param': 'dsp0.' + prm}
t['automation'] = {'@assignments': [A(0, 1, 'block1.Mix'), A(100, 2000, 'block2.Frequency'), A(0.5, 10, 'block2.FilterQ'),
                   A(0, 1, 'block2.Mix'), A(0, 1, 'block3.Peak'), A(0, 1, 'block3.Gain'), A(0, 1, 'block3.Mix'),
                   A(0, 1, 'block4.Frequency'), A(0, 1, 'block4.Resonance'), A(0, 1, 'block4.Sensitivity'),
                   A(0, 1, 'block4.Attack'), A(0, 1, 'block4.Release'), A(0, 1, 'block4.Mix'), A(-50, 0, 'block7.Threshold')]}
for i in range(8):
    t['snapshot%d' % i]['blocks']['dsp0'] = {'block%d' % b: True for b in range(8)}
with open('chain11_korn_filters.hlx', 'w') as f:
    json.dump(p, f, indent=1)
print('wrote chain11_korn_filters.hlx:', ', '.join(f"{k} {v['@model']}" for k, v in new.items() if k.startswith('block')))
