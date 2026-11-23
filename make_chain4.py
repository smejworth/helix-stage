# make_chain4.py : writes chain4_korn_eq.hlx: chain 3 (gate, Whammy octave down, Rectifier, cab) followed by
# a 10 band graphic EQ and three stacked Low and High Cut blocks (stacking makes the cuts steeper).
# Every EQ band and every cut frequency is bound to its own knob slot, so Python can measure and set them:
#   knobs 1 to 10  -> graphic EQ bands 31 Hz to 16 kHz, range -12 to +12 dB
#   knobs 11,13,15 -> Low Cut of cut blocks A, B, C, range 19.9 to 500 Hz
#   knobs 12,14,16 -> High Cut of cut blocks A, B, C, range 1000 to 20100 Hz
# The file stores no knob numbers; the order of the assignment list is assumed to be the knob order, and
# measure_eq.py checks that. Layouts copy factory presets. Only the preset file is written.
# usage: python make_chain4.py
import json
p = json.load(open('chain3_korn.hlx'))
tone = p['data']['tone']
p['data']['meta']['name'] = 'KORN CHAIN 4'
dsp = tone['dsp0']
common = {'@enabled': True, '@no_snapshot_bypass': False, '@path': 0, '@stereo': False, '@type': 0, 'Level': 0}
BANDS = ['31p25Hz', '62p5Hz', '125Hz', '250Hz', '500Hz', '1kHz', '2kHz', '4kHz', '8kHz', '16kHz']
dsp['block4'] = dict(common, **{'@model': 'HD2_EQGraphic10Band', '@position': 4}, **{b: 0 for b in BANDS})
for i, blk in enumerate(['block5', 'block6', 'block7']):
    dsp[blk] = dict(common, **{'@model': 'HD2_EQLowCutHighCut', '@position': 5 + i, 'LowCut': 19.9, 'HighCut': 20100})

assign = [{'@min': -12.0, '@max': 12.0, '@param': 'dsp0.block4.' + b} for b in BANDS]
for blk in ['block5', 'block6', 'block7']:
    assign.append({'@min': 19.9, '@max': 500.0, '@param': 'dsp0.%s.LowCut' % blk})
    assign.append({'@min': 1000.0, '@max': 20100.0, '@param': 'dsp0.%s.HighCut' % blk})
tone['automation'] = {'@assignments': assign}
for i in range(8):
    tone['snapshot%d' % i]['blocks']['dsp0'].update({'block4': True, 'block5': True, 'block6': True, 'block7': True})
with open('chain4_korn_eq.hlx', 'w') as f:
    json.dump(p, f, indent=1)
print('wrote chain4_korn_eq.hlx with', len(assign), 'knob assignments')
