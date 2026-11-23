# helixlab.py : loads the Helix Native VST3 plugin in Python through pedalboard, ready to render audio.
# Scripts load a saved plugin state into it unchanged (pl.raw_state = ...) and set knobs; nothing else.
import pedalboard
PATH = r'C:\Program Files\Common Files\VST3\Line 6\Helix Native (x64).vst3'
def load():
    return pedalboard.load_plugin(PATH)
