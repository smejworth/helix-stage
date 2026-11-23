# make_chain9.py : writes chain9_korn_envfilter.hlx:
#   block0 noise gate -> block1 Whammy octave down (Mix on a knob, 0.5 found best in oct_place.py)
#   -> block2 Auto Filter (Helix's envelope filter: it follows how hard you pick and sweeps a filter with it)
#   -> block3 Rectifier amp -> block4 cab -> block5 Deluxe Comp (6:1)
# The filter sits before the amp, so it reacts to the picking before the amp and compressor squash the level.
# Auto Filter layout copied from a factory preset. Knob slots:
#   1 Whammy Mix 0 to 1            2 filter Frequency 100 to 2000 Hz   3 filter FreqDepth (sweep range) 0 to 6000 Hz
#   4 filter Sens 0 to 1           5 filter Attack 0.01 to 1 s          6 filter Decay 0.01 to 2 s
#   7 filter Q 0.5 to 10           8 filter Mix 0 to 1                  9 compressor Threshold -50 to 0 dB
#   10 amp Drive 0 to 10 (stored 0 to 1)
# No EQ blocks: listening files get the stem's frequency balance with the matching EQ afterwards.
# Only the preset file is written.
# usage: python make_chain9.py
import json, copy
p = json.load(open('chain8_korn_octpos.hlx'))
t = p['data']['tone']
p['data']['meta']['name'] = 'KORN CHAIN 9'
o = t['dsp0']
new = {k: v for k, v in o.items() if not k.startswith('block')}
new['block0'] = o['block0']
new['block1'] = dict(o['block1'], **{'Mix': 0.5})
new['block2'] = {'@enabled': True, '@model': 'HD2_FilterAutoFilter', '@no_snapshot_bypass': False, '@path': 0,
                 '@position': 2, '@stereo': False, '@type': 0, 'Direction': True, 'Frequency': 300, 'Sens': 0.5,
                 'FilterGain': 12, 'Attack': 0.2, 'FilterQ': 4, 'Mix': 1, 'FreqDepth': 2000, 'Level': 0,
                 'Decay': 0.5, 'Mode': 0}
new['block3'] = dict(o['block2'], **{'@position': 3})
new['block4'] = dict(o['block3'], **{'@position': 4})
new['block5'] = dict(o['block5'], **{'@position': 5})
t['dsp0'] = new
A = lambda lo, hi, prm: {'@min': float(lo), '@max': float(hi), '@param': 'dsp0.' + prm}
t['automation'] = {'@assignments': [A(0, 1, 'block1.Mix'), A(100, 2000, 'block2.Frequency'), A(0, 6000, 'block2.FreqDepth'),
                                    A(0, 1, 'block2.Sens'), A(0.01, 1, 'block2.Attack'), A(0.01, 2, 'block2.Decay'),
                                    A(0.5, 10, 'block2.FilterQ'), A(0, 1, 'block2.Mix'), A(-50, 0, 'block5.Threshold'),
                                    A(0, 1, 'block3.Drive')]}
for i in range(8):
    t['snapshot%d' % i]['blocks']['dsp0'] = {'block%d' % b: True for b in range(6)}
with open('chain9_korn_envfilter.hlx', 'w') as f:
    json.dump(p, f, indent=1)
print('wrote chain9_korn_envfilter.hlx:', ', '.join(f"{k} {v['@model']}" for k, v in new.items() if k.startswith('block')))
