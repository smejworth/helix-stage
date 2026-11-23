# make_chain2.py : writes chain2_rectifier.hlx, a Helix preset made by code from the exported template.
# Chain: Cali Rectifire amp (Mesa Rectifier style) then 4x12 Cali V30 cab, no octave block.
# Knob 1 is bound to the amp's Drive. Block and cab layouts copy the factory presets in factory1.hls.
# Only the preset file (plain JSON) is written. The plugin state is never touched.
# usage: python make_chain2.py
import json, copy
p = json.load(open('template_fuzz_oct.hlx'))
tone = p['data']['tone']
p['data']['meta']['name'] = 'KORN CHAIN 2'

dsp = tone['dsp0']
for k in [k for k in dsp if k.startswith('block')]:
    del dsp[k]                                   # remove the old Boctaver and Triangle Fuzz

# amp block: controls are stored 0 to 1 (the editor shows them times 10)
dsp['block0'] = {
    '@bypassvolume': 1, '@enabled': True, '@model': 'HD2_AmpCaliRectifire', '@no_snapshot_bypass': False,
    '@path': 0, '@position': 0, '@type': 1,
    'Drive': 0.70, 'Bass': 0.50, 'Mid': 0.30, 'Treble': 0.60, 'Presence': 0.60,
    'ChVol': 0.80, 'Master': 0.50, 'Sag': 0.5, 'Hum': 0.5, 'Ripple': 0.5, 'Bias': 0.5, 'BiasX': 0.5,
}
# cab block: LowCut and HighCut in Hz, chosen from the stem's measured low and high roll-off
cab = {
    '@enabled': True, '@model': 'HD2_CabMicIr_4x12CaliV30WithPan',
    'Angle': 0, 'Delay': 0, 'Distance': 1, 'HighCut': 8000, 'Level': 0, 'LowCut': 100,
    'Mic': 0, 'Pan': 0.5, 'Position': 0.23,
}
dsp['block1'] = dict(cab, **{'@cab': 'cab0', '@no_snapshot_bypass': False, '@path': 0, '@position': 1, '@type': 4})
tone['cab0'] = copy.deepcopy(cab)                # factory presets carry a matching top-level cab0 entry

tone['automation'] = {'@assignments': [{'@max': 1.0, '@min': 0.0, '@param': 'dsp0.block0.Drive'}]}
tone['global']['@cursor_group'] = 'block0'
for i in range(8):                               # both blocks on in every snapshot
    tone['snapshot%d' % i]['blocks'] = {'dsp0': {'block0': True, 'block1': True}}

with open('chain2_rectifier.hlx', 'w') as f:
    json.dump(p, f, indent=1)
print('wrote chain2_rectifier.hlx')
