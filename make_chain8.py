# make_chain8.py : writes chain8_korn_octpos.hlx, a test chain for WHERE the octave-down sits:
#   block0 noise gate -> block1 Whammy (octave down, BEFORE the amp) -> block2 Rectifier amp -> block3 cab
#   -> block4 Whammy (octave down, AFTER the cab) -> block5 compressor (6:1 at -20 dB, from fit_squash.py)
# Both Whammy blocks are copies of chain 6's (Toe -12, Pedal 1). Their Mix sets the blend: 0 = only the original
# notes pass, 1 = only the octave-down voice (chain 6 used 1 before the amp, so the amp never saw the real notes).
#   knob 1 -> Mix of the Whammy before the amp, 0 to 1
#   knob 2 -> Mix of the Whammy after the cab, 0 to 1
# No EQ blocks: the listening files get the stem's frequency balance afterwards with match_eq.py, so only the
# octave placement differs between versions. All blocks on in every snapshot. Only the preset file is written.
# usage: python make_chain8.py
import json, copy
p = json.load(open('chain6_korn_squash.hlx'))
t = p['data']['tone']
p['data']['meta']['name'] = 'KORN CHAIN 8'
old = t['dsp0']
wham = copy.deepcopy(old['block1']); wham['Mix'] = 0
new = {k: v for k, v in old.items() if not k.startswith('block')}
new['block0'] = old['block0']
new['block1'] = dict(copy.deepcopy(wham), **{'@position': 1})
new['block2'] = old['block2']
new['block3'] = old['block3']
new['block4'] = dict(copy.deepcopy(wham), **{'@position': 4})
new['block5'] = dict(old['block6'], **{'@position': 5, 'Ratio': 3, 'Threshold': -20})
t['dsp0'] = new
t['automation'] = {'@assignments': [{'@min': 0.0, '@max': 1.0, '@param': 'dsp0.block1.Mix'},
                                    {'@min': 0.0, '@max': 1.0, '@param': 'dsp0.block4.Mix'}]}
for i in range(8):
    t['snapshot%d' % i]['blocks']['dsp0'] = {'block%d' % b: True for b in range(6)}
with open('chain8_korn_octpos.hlx', 'w') as f:
    json.dump(p, f, indent=1)
print('wrote chain8_korn_octpos.hlx:', ', '.join(f"{k} {v['@model']}" for k, v in new.items() if k.startswith('block')))
