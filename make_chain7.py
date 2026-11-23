# make_chain7.py : writes chain7_korn_650.hlx: chain 6 with the Parametric EQ's unused Low band put on knobs,
# to add the narrow resonance the stem has at about 650 Hz. Knob slots 1 to 11 are as in chain 6; new:
#   knob 12 -> Low band frequency, 300 to 1200 Hz
#   knob 13 -> Low band gain, -12 to +12 dB
#   knob 14 -> Low band Q, 0.5 to 8
# The compressor and Drive settings found by fit_squash.py are kept on their knobs (3 and 4). Only the preset file
# is written. Whether the Low band accepts frequencies this high is checked in the editor when loading.
# usage: python make_chain7.py
import json
p = json.load(open('chain6_korn_squash.hlx'))
tone = p['data']['tone']
p['data']['meta']['name'] = 'KORN CHAIN 7'
tone['dsp0']['block7'].update({'LowFreq': 650, 'LowGain': 0, 'LowQ': 4})
a = tone['automation']['@assignments']
a += [{'@min': 300.0, '@max': 1200.0, '@param': 'dsp0.block7.LowFreq'},
      {'@min': -12.0, '@max': 12.0, '@param': 'dsp0.block7.LowGain'},
      {'@min': 0.5, '@max': 8.0, '@param': 'dsp0.block7.LowQ'}]
with open('chain7_korn_650.hlx', 'w') as f:
    json.dump(p, f, indent=1)
print('wrote chain7_korn_650.hlx with', len(a), 'knob assignments')
