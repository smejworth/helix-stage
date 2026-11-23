# make_chain10.py : writes chain10_korn_envpost.hlx. Owner on chain 9b: closer, but the envelope is more aggressive
# in the original and gets buried in ours. Before the amp, the high gain distortion smooths the filter's movement
# away, so this chain adds a second envelope filter at the very end, after the compressor, where nothing buries it:
#   block0 gate -> block1 Whammy -> block2 Auto Filter (before amp) -> block3 Rectifier (Drive 8.2, fixed)
#   -> block4 cab -> block5 Deluxe Comp 6:1 -> block6 Auto Filter (after everything)
# Knob slots:
#   1 Whammy Mix 0-1 | before-amp filter: 2 Frequency 100-2000 Hz, 3 depth 0-6000 Hz, 4 Sens 0-1, 5 Attack 0.01-1 s,
#   6 Decay 0.01-2 s, 7 Q 0.5-10, 8 Mix 0-1 | 9 compressor Threshold -50-0 dB | after filter: 10 Frequency 100-3000 Hz,
#   11 depth 0-6000 Hz, 12 Sens 0-1, 13 Attack 0.005-1 s, 14 Decay 0.01-2 s, 15 Q 0.5-10, 16 Mix 0-1
# Both filters in low pass mode with Filter Gain +12 dB (as the factory example). Only the preset file is written.
# usage: python make_chain10.py
import json, copy
p = json.load(open('chain9_korn_envfilter.hlx'))
t = p['data']['tone']
p['data']['meta']['name'] = 'KORN CHAIN 10'
d = t['dsp0']
d['block3']['Drive'] = 0.82
post = copy.deepcopy(d['block2']); post.update({'@position': 6, 'Frequency': 400, 'FreqDepth': 1500, 'Mix': 0})
d['block6'] = post
A = lambda lo, hi, prm: {'@min': float(lo), '@max': float(hi), '@param': 'dsp0.' + prm}
old = t['automation']['@assignments'][:9]          # chain 9 slots 1 to 9 (Whammy, filter before amp, compressor)
t['automation'] = {'@assignments': old + [A(100, 3000, 'block6.Frequency'), A(0, 6000, 'block6.FreqDepth'),
                   A(0, 1, 'block6.Sens'), A(0.005, 1, 'block6.Attack'), A(0.01, 2, 'block6.Decay'),
                   A(0.5, 10, 'block6.FilterQ'), A(0, 1, 'block6.Mix')]}
for i in range(8):
    t['snapshot%d' % i]['blocks']['dsp0'] = {'block%d' % b: True for b in range(7)}
with open('chain10_korn_envpost.hlx', 'w') as f:
    json.dump(p, f, indent=1)
print('wrote chain10_korn_envpost.hlx:', ', '.join(f"{k} {v['@model']}" for k, v in d.items() if k.startswith('block')))
for i, a in enumerate(t['automation']['@assignments']):
    print(' knob', i + 1, a['@param'], a['@min'], 'to', a['@max'])
