import pedalboard, sys, numpy as np
p=r'C:\Program Files\Common Files\VST3\Line 6\Helix Native (x64).vst3'
try:
    pl=pedalboard.load_plugin(p)
    print('loaded',pl.name)
    ps=pl.parameters
    print(len(ps))
    for k in list(ps.keys())[:80]: print(k, ps[k])
except Exception as e:
    print('ERR',type(e).__name__,e)
