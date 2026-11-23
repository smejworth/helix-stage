# save_state.py : opens the Helix Native window. Build or load your preset there, then close the window.
# The plugin's state is then saved to the file you named, exactly as the plugin hands it over.
# usage: python save_state.py STATE.bin
import sys, threading, pedalboard
PLUGIN = r'C:\Program Files\Common Files\VST3\Line 6\Helix Native (x64).vst3'
pl = pedalboard.load_plugin(PLUGIN)
print('Helix Native is opening. Set up the preset, then close its window.')
pl.show_editor(threading.Event())
open(sys.argv[1], 'wb').write(pl.raw_state)
print('saved', sys.argv[1])
