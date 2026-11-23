# make_chain3c.py : chain3_korn.hlx with the cab swapped for the older style 4x12 Cali V30 cab model
# (HD2_Cab4X12CaliV30), laid out as in the factory preset "G.O.A.T. Rodeo". No EQ block.
# Tests whether this cab type filters in headless renders, where the mic'd IR cab model did not.
# usage: python make_chain3c.py
import json
p = json.load(open('chain3_korn.hlx'))
tone = p['data']['tone']
p['data']['meta']['name'] = 'KORN CHAIN 3C'
cab = {'@enabled': True, '@mic': 0, '@model': 'HD2_Cab4X12CaliV30', 'Distance': 1, 'EarlyReflections': 0,
       'HighCut': 8000, 'Level': 0, 'LowCut': 80}
tone['dsp0']['block3'] = dict(cab, **{'@cab': 'cab0', '@no_snapshot_bypass': False, '@path': 0, '@position': 3, '@type': 4})
tone['cab0'] = dict(cab)
with open('chain3c_korn_cab2.hlx', 'w') as f:
    json.dump(p, f, indent=1)
print('wrote chain3c_korn_cab2.hlx')
