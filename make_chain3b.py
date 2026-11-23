# make_chain3b.py : chain3_korn.hlx plus a Parametric EQ block after the cab with the same low cut (80 Hz) and
# high cut (8000 Hz) as the cab. Tests whether an EQ block filters in headless renders when the cab block seems not to.
# EQ layout copies the factory preset "Revv Gen Purple". All EQ gains are 0, so it only cuts lows and highs.
# usage: python make_chain3b.py
import json
p = json.load(open('chain3_korn.hlx'))
tone = p['data']['tone']
p['data']['meta']['name'] = 'KORN CHAIN 3B'
tone['dsp0']['block4'] = {
    '@enabled': True, '@model': 'HD2_EQParametric', '@no_snapshot_bypass': False, '@path': 0, '@position': 4,
    '@stereo': False, '@type': 0, 'Level': 0,
    'LowCut': 80, 'HighCut': 8000,
    'LowFreq': 110, 'LowGain': 0, 'LowQ': 0.707, 'MidFreq': 1000, 'MidGain': 0, 'MidQ': 0.707,
    'HighFreq': 6300, 'HighGain': 0, 'HighQ': 0.707,
}
for i in range(8):
    tone['snapshot%d' % i]['blocks']['dsp0']['block4'] = True
with open('chain3b_korn_eq.hlx', 'w') as f:
    json.dump(p, f, indent=1)
print('wrote chain3b_korn_eq.hlx')
