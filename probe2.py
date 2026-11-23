import pedalboard, sys, numpy as np
p=r'C:\Program Files\Common Files\VST3\Line 6\Helix Native (x64).vst3'
pl=pedalboard.load_plugin(p)
ps=pl.parameters
ks=list(ps.keys())
print([k for k in ks if not k.startswith('cc_') and not k.startswith('knob') and not k.startswith('switch')])
print(pl.is_instrument, pl.is_effect)
rs=pl.raw_state
print('raw_state',len(rs), rs[:64])
sr=48000
x=(0.3*np.sin(2*np.pi*220*np.arange(sr)/sr)).astype(np.float32)
y=pl(x[None,:].repeat(2,0),sr)
print(y.shape, np.abs(y).max(), np.abs(x).max(), np.abs(y-x).max())
