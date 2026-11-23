# make_chain3.py : writes chain3_korn.hlx, a Helix preset made by code, using the owner's researched settings
# for the intro of Korn "Here to Stay": noise gate, Whammy style octave down, Rectifier amp, 4x12 V30 cab.
# Snapshot 1 has the octave on, snapshot 2 has it off. Knob 1 is bound to the amp's Drive.
# Block layouts and value scales copy factory presets in factory1.hls. Only the preset file is written.
# usage: python make_chain3.py
import json, copy
p = json.load(open('template_fuzz_oct.hlx'))
tone = p['data']['tone']
p['data']['meta']['name'] = 'KORN CHAIN 3'
dsp = tone['dsp0']
for k in [k for k in dsp if k.startswith('block')]:
    del dsp[k]

common = {'@enabled': True, '@no_snapshot_bypass': False, '@path': 0}
# noise gate (dB threshold, decay in seconds)
dsp['block0'] = dict(common, **{'@model': 'HD2_GateNoiseGate', '@position': 0, '@stereo': False, '@type': 0,
                                'Threshold': -60, 'Decay': 0.05, 'Level': 0})
# Whammy style pitch: pedal fully at the toe, toe set 12 semitones down, fully wet, so the note is replaced by its octave below
dsp['block1'] = dict(common, **{'@model': 'HD2_PitchPitchWham', '@position': 1, '@stereo': False, '@type': 0,
                                'Heel': 0, 'Toe': -12, 'Pedal': 1, 'Mix': 1, 'Level': 0})
# Rectifier amp, owner's starting settings on the 0 to 10 scale divided by 10: gain 8.2, bass 7, mid 3, treble 6.2, presence 6.2
dsp['block2'] = dict(common, **{'@model': 'HD2_AmpCaliRectifire', '@position': 2, '@type': 1, '@bypassvolume': 1,
                                'Drive': 0.82, 'Bass': 0.70, 'Mid': 0.30, 'Treble': 0.62, 'Presence': 0.62,
                                'ChVol': 0.80, 'Master': 0.50, 'Sag': 0.5, 'Hum': 0.5, 'Ripple': 0.5, 'Bias': 0.5, 'BiasX': 0.5})
# 4x12 V30 cab: modest low cut for a tight low end, high cut near the stem's measured top roll-off
cab = {'@enabled': True, '@model': 'HD2_CabMicIr_4x12CaliV30WithPan', 'Angle': 0, 'Delay': 0, 'Distance': 1,
       'HighCut': 8000, 'Level': 0, 'LowCut': 80, 'Mic': 0, 'Pan': 0.5, 'Position': 0.23}
dsp['block3'] = dict(cab, **{'@cab': 'cab0', '@no_snapshot_bypass': False, '@path': 0, '@position': 3, '@type': 4})
tone['cab0'] = copy.deepcopy(cab)

tone['automation'] = {'@assignments': [{'@max': 1.0, '@min': 0.0, '@param': 'dsp0.block2.Drive'}]}
tone['global']['@cursor_group'] = 'block2'
for i in range(8):
    on = {'block0': True, 'block1': True, 'block2': True, 'block3': True}
    if i == 1:
        on['block1'] = False                     # snapshot 2: octave off
    tone['snapshot%d' % i]['blocks'] = {'dsp0': on}
tone['snapshot0']['@name'] = 'OCT ON'
tone['snapshot1']['@name'] = 'OCT OFF'

with open('chain3_korn.hlx', 'w') as f:
    json.dump(p, f, indent=1)
print('wrote chain3_korn.hlx')
