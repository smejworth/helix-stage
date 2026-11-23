import pedalboard
pl=pedalboard.load_plugin(r'C:\Program Files\Common Files\VST3\Line 6\Helix Native (x64).vst3')
rs=pl.raw_state
open('state0.bin','wb').write(rs)
i=rs.find(b'</VST3PluginState>')
print(i)
print(rs[8:1800].decode('latin1'))
