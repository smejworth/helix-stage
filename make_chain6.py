# make_chain6.py : writes chain6_korn_squash.hlx: chain 5 with the unused second cut block (block6) replaced by a
# compressor (Deluxe Comp, layout copied from a factory preset), to copy the stem's squashed, steady loudness.
# Knob slots:
#   knobs 1, 2    -> cut block A Low Cut (19.9 to 500 Hz) and High Cut (1000 to 20100 Hz), as in chain 5
#   knob 3        -> compressor Threshold, -50 to 0 dB (ratio 6:1, attack 10 ms, release 100 ms, fixed)
#   knob 4        -> amp Drive, 0 to 10 on the amp's own scale (stored 0 to 1)
#   knobs 5 to 11 -> Parametric EQ filter, same order and ranges as chain 5, so filter_fit.json knobs carry over
# Only the preset file is written.
# usage: python make_chain6.py
import json
p = json.load(open('chain5_korn_filter.hlx'))
tone = p['data']['tone']
p['data']['meta']['name'] = 'KORN CHAIN 6'
tone['dsp0']['block6'] = {'@enabled': True, '@model': 'HD2_CompressorDeluxeComp', '@no_snapshot_bypass': False,
                          '@path': 0, '@position': 6, '@stereo': False, '@type': 0, 'Attack': 0.01, 'Knee': 6,
                          'Level': 0, 'Mix': 1, 'Ratio': 3, 'Release': 0.1, 'Threshold': -20}
# Ratio is a position in the editor's list 2:1, 3:1, 4:1, 6:1, 10:1, 20:1 (0 to 5), not the ratio itself: 3 = 6:1
old = tone['automation']['@assignments']          # chain 5: 0,1 cut A; 2,3 cut B; 4 to 10 the filter
assign = old[0:2] + [{'@min': -50.0, '@max': 0.0, '@param': 'dsp0.block6.Threshold'},
                     {'@min': 0.0, '@max': 1.0, '@param': 'dsp0.block2.Drive'}] + old[4:11]
tone['automation'] = {'@assignments': assign}
with open('chain6_korn_squash.hlx', 'w') as f:
    json.dump(p, f, indent=1)
print('wrote chain6_korn_squash.hlx with', len(assign), 'knob assignments:')
for i, a in enumerate(assign):
    print(' knob', i + 1, a['@param'])
