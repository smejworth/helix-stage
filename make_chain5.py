# make_chain5.py : writes chain5_korn_filter.hlx: chain 4 plus a Parametric EQ block at the end, to copy the
# narrow filter measured in the stem (a bump at about 5 kHz, a notch at about 6.4 kHz, a fall from about 10 kHz).
# To free knob slots, the 10 band graphic EQ is no longer on knobs: its gains are written into the file as the
# values fit_eq.py found (eq_fit.json). Knob slots now:
#   knobs 1 to 4   -> the first two Low Cut / High Cut blocks, same order and ranges as chain 4
#   knobs 5, 6, 7  -> Parametric EQ Mid band: frequency 2000 to 9000 Hz, gain -12 to +12 dB, Q 0.5 to 8
#   knobs 8, 9, 10 -> Parametric EQ High band: frequency 4000 to 12000 Hz, gain -12 to +12 dB, Q 0.5 to 8
#   knob 11        -> Parametric EQ High Cut, 5000 to 20100 Hz
# Layout of the Parametric EQ block copies a factory preset. Only the preset file is written.
# usage: python make_chain5.py
import json
p = json.load(open('chain4_korn_eq.hlx'))
fit = json.load(open('eq_fit.json'))
tone = p['data']['tone']
p['data']['meta']['name'] = 'KORN CHAIN 5'
dsp = tone['dsp0']
BANDS = ['31p25Hz', '62p5Hz', '125Hz', '250Hz', '500Hz', '1kHz', '2kHz', '4kHz', '8kHz', '16kHz']
for b, g in zip(BANDS, fit['band_gains_db'].values()):
    dsp['block4'][b] = g
# A path holds at most 8 blocks (positions 0 to 7), so the parametric EQ replaces the third cut block (block7),
# which the chain 4 fit left unused.
dsp['block7'] = {'@enabled': True, '@model': 'HD2_EQParametric', '@no_snapshot_bypass': False, '@path': 0,
                 '@position': 7, '@stereo': False, '@type': 0, 'Level': 0, 'LowCut': 19.9, 'HighCut': 20100,
                 'LowFreq': 110, 'LowGain': 0, 'LowQ': 0.707, 'MidFreq': 5300, 'MidGain': 0, 'MidQ': 2.7,
                 'HighFreq': 6400, 'HighGain': 0, 'HighQ': 2.6}
assign = []
for blk in ['block5', 'block6']:
    assign.append({'@min': 19.9, '@max': 500.0, '@param': 'dsp0.%s.LowCut' % blk})
    assign.append({'@min': 1000.0, '@max': 20100.0, '@param': 'dsp0.%s.HighCut' % blk})
for band, lo, hi in (('Mid', 2000.0, 9000.0), ('High', 4000.0, 12000.0)):
    assign.append({'@min': lo, '@max': hi, '@param': 'dsp0.block7.%sFreq' % band})
    assign.append({'@min': -12.0, '@max': 12.0, '@param': 'dsp0.block7.%sGain' % band})
    assign.append({'@min': 0.5, '@max': 8.0, '@param': 'dsp0.block7.%sQ' % band})
assign.append({'@min': 5000.0, '@max': 20100.0, '@param': 'dsp0.block7.HighCut'})
tone['automation'] = {'@assignments': assign}
with open('chain5_korn_filter.hlx', 'w') as f:
    json.dump(p, f, indent=1)
print('wrote chain5_korn_filter.hlx with', len(assign), 'knob assignments')
