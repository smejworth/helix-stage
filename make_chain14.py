# make_chain14.py : writes chain14_korn_microsynth.hlx, a Helix stand-in for the EHX Micro Synth the owner's research
# names at the start of "Here to Stay". Helix has no Micro Synth model; its three parts are approximated with blocks
# Helix does have, all before the amp:
#   sub-octave voice (analog divider)            -> Boctaver (also an analog-style octave divider)
#   square-wave voice                            -> Triangle Fuzz (a hard, square-ish fuzz)
#   filter sweeping from a start to a stop note  -> Auto Filter, kept sweeping UP as in the reference (down was worse)
# Chain: block0 gate -> block1 Whammy (dry plus octave down) -> block2 Boctaver -> block3 Triangle Fuzz
#   -> block4 Auto Filter (down) -> block5 Rectifier -> block6 cab -> block7 Deluxe Comp
# Knob slots: 1 Whammy Mix | Boctaver 2 Dry, 3 one octave down, 4 two octaves down (0-1 each) | fuzz 5 Sustain,
#   6 Tone (0-1) | filter 7 Frequency 100-2000 Hz, 8 depth 0-6000 Hz, 9 Sens 0-1, 10 Decay 0.01-2 s, 11 Q 0.5-10,
#   12 Mix 0-1 | 13 compressor Threshold -50-0 dB, 14 compressor Attack 0.001-0.1 s | 15 amp Drive 0-10 (stored 0-1)
#   16 fuzz Level 0-1
# Snapshots switch parts off to hear what each adds: 1 all on, 2 fuzz off, 3 Boctaver off, 4 fuzz and Boctaver off.
# Layouts copied from the earlier template preset. Only the preset file is written.
# usage: python make_chain14.py
import json
p = json.load(open('chain13_korn_down.hlx'))
t = p['data']['tone']
p['data']['meta']['name'] = 'KORN CHAIN 14'
o = t['dsp0']
base = {'@no_snapshot_bypass': False, '@path': 0, '@stereo': False, '@type': 0, '@enabled': True}
new = {k: v for k, v in o.items() if not k.startswith('block')}
new['block0'] = o['block0']
new['block1'] = o['block1']
new['block2'] = dict(base, **{'@model': 'VIC_PitchBoctaver', '@position': 2, 'DryLevel': 0.6, 'Oct1Level': 0.6, 'Oct2Level': 0.0})
new['block3'] = dict(base, **{'@model': 'HD2_DistTriangleFuzz', '@position': 3, 'Level': 0.5, 'Sustain': 0.8, 'Tone': 0.5})
new['block4'] = dict(o['block2'], **{'@position': 4, 'Direction': True})   # up: the owner judged every down-sweep worse
new['block5'] = dict(o['block3'], **{'@position': 5, 'Drive': 0.82})
new['block6'] = dict(o['block4'], **{'@position': 6})
new['block7'] = dict(o['block5'], **{'@position': 7})
t['dsp0'] = new
A = lambda lo, hi, prm: {'@min': float(lo), '@max': float(hi), '@param': 'dsp0.' + prm}
t['automation'] = {'@assignments': [A(0, 1, 'block1.Mix'), A(0, 1, 'block2.DryLevel'), A(0, 1, 'block2.Oct1Level'),
    A(0, 1, 'block2.Oct2Level'), A(0, 1, 'block3.Sustain'), A(0, 1, 'block3.Tone'), A(100, 2000, 'block4.Frequency'),
    A(0, 6000, 'block4.FreqDepth'), A(0, 1, 'block4.Sens'), A(0.01, 2, 'block4.Decay'), A(0.5, 10, 'block4.FilterQ'),
    A(0, 1, 'block4.Mix'), A(-50, 0, 'block7.Threshold'), A(0.001, 0.1, 'block7.Attack'), A(0, 1, 'block5.Drive'),
    A(0, 1, 'block3.Level')]}
SNAPS = [('MS ALL', {}), ('NO FUZZ', {'block3': False}), ('NO BOCT', {'block2': False}), ('NO FUZZ BOCT', {'block2': False, 'block3': False})]
for i in range(8):
    name, off = SNAPS[i] if i < 4 else SNAPS[0]
    blocks = {'block%d' % b: True for b in range(8)}; blocks.update(off)
    t['snapshot%d' % i]['blocks']['dsp0'] = blocks
    t['snapshot%d' % i]['@name'] = name
with open('chain14_korn_microsynth.hlx', 'w') as f:
    json.dump(p, f, indent=1)
print('wrote chain14_korn_microsynth.hlx:', ', '.join(f"{k} {v['@model']}" for k, v in new.items() if k.startswith('block')))
