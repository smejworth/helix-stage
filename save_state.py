# save_state.py : opens the Helix Native editor window, waits for you to close it, then saves the plugin state to a file.
# Same idea as load_fbtest.py, but the file name is given on the command line.
# usage: python save_state.py template_state.bin
# The state is saved exactly as the plugin hands it over. Nothing is decoded or changed.
import sys, threading, helixlab as H
out = sys.argv[1] if len(sys.argv) > 1 else 'template_state.bin'
pl = H.load()
print('Editor opening. Load the preset you want, check it looks right, then close the editor window.')
ev = threading.Event()
timer = threading.Timer(1800, ev.set)      # auto close after 30 minutes
timer.daemon = True                        # do not keep the program running after the window closes
timer.start()
pl.show_editor(ev)
rs = pl.raw_state
open(out, 'wb').write(rs)
print('saved', out, len(rs), 'bytes')
