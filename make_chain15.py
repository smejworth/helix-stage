# make_chain15.py : writes chain15_korn_sidesynth.hlx. The Micro Synth stand-in (Boctaver sub voice into a Triangle
# Fuzz square voice) runs on its own parallel path, blended back in at the join, because the fuzz block has no mix
# control (owner: "the synth probably needs to be side chained", "if that block doesnt have a mix function").
#   path A: gate (pos 0) -> Whammy dry plus octave down (pos 1) -> [split at pos 2] -> straight through -> [join at pos 4]
#   path B: from the split -> Boctaver, sub voice only (pos 2) -> Triangle Fuzz (pos 3) -> join
#   after the join: envelope filter, sweeping up as in the reference (pos 4) -> Rectifier (pos 5) -> cab (pos 6)
#   -> Deluxe Comp (pos 7)
# Split/join layout copied from factory presets (a block on path 1 shares a position with path 0 inside the split).
# Knob slots: 1 Whammy Mix | Boctaver 2 dry (kept 0: the dry note goes through path A), 3 one octave down, 4 two
# octaves down | fuzz 5 Sustain, 6 Tone | filter 7 Frequency 100-2000 Hz, 8 depth 0-6000 Hz, 9 Sens, 10 Decay 0.01-2 s,
# 11 Q 0.5-10, 12 Mix | 13 compressor Threshold -50-0 dB, 14 compressor Attack 0.001-0.1 s | 15 amp Drive (0-10 as 0-1)
# | 16 fuzz output Level 0-1 (sets how loud the synth path is at the join)
# Snapshots: 1 all on, 2 fuzz off, 3 Boctaver off, 4 both off. Only the preset file is written.
# usage: python make_chain15.py
import json, copy
p = json.load(open('chain14_korn_microsynth.hlx'))
t = p['data']['tone']
p['data']['meta']['name'] = 'KORN CHAIN 15'
o = t['dsp0']
d = {k: v for k, v in o.items() if not k.startswith('block')}
d['block0'] = dict(o['block0'], **{'@path': 0, '@position': 0})
d['block1'] = dict(o['block1'], **{'@path': 0, '@position': 1})
d['block2'] = dict(o['block2'], **{'@path': 1, '@position': 2, 'DryLevel': 0.0, 'Oct1Level': 0.8, 'Oct2Level': 0.0})
d['block3'] = dict(o['block3'], **{'@path': 1, '@position': 3})
d['block4'] = dict(o['block4'], **{'@path': 0, '@position': 4, 'Direction': True})
d['block5'] = dict(o['block5'], **{'@path': 0, '@position': 5})
d['block6'] = dict(o['block6'], **{'@path': 0, '@position': 6})
d['block7'] = dict(o['block7'], **{'@path': 0, '@position': 7})
d['split'] = dict(o['split'], **{'@position': 2, '@enabled': True})
d['join'] = dict(o['join'], **{'@position': 4, '@enabled': True, 'B Level': 0.0})   # -12 dB made the synth path nearly inaudible (99% same waveform)
t['dsp0'] = d
a = t['automation']['@assignments']
# A knob on the join's B Level was tried first and did nothing (output identical at -40 and 0 dB), so the synth path's
# level is set by the fuzz block's own output Level, the last block on that path.
a[15] = {'@min': 0.0, '@max': 1.0, '@param': 'dsp0.block3.Level'}
with open('chain15_korn_sidesynth.hlx', 'w') as f:
    json.dump(p, f, indent=1)
print('wrote chain15_korn_sidesynth.hlx')
for k in sorted(x for x in d if x.startswith('block')):
    print(' ', k, d[k]['@model'], 'path', d[k]['@path'], 'pos', d[k]['@position'])
print('  split pos', d['split']['@position'], ' join pos', d['join']['@position'])
