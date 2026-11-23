# helix-stage

Matching a recorded guitar tone in Helix Native, driven from Python by an AI agent. The worked case is the intro of Korn's "Here to Stay": the original isolated guitar track (the stem) against the owner's own clean DI of the same riff.

The full write-up, including the steps, the chain that worked, what did not work, and the traps, is the guide doc: https://claude.ai/artifact/PrvqtjsG96M8nNYNVcgjVq

Findings and listening verdicts, as current truth: `docs/decisions.md`. Where things stand: `_status.md`.

## Layout

- `input/`: the two source files. Only the owner's DI (`guitar_played.wav`) is in the repo; the stem stays local.
- `work/`: renders, one folder per listening batch (`helix01` to `helix20`, `match01`, `mp3`). Only `work/mp3/best_reference_plus_limiter.mp3` is in the repo.
- `docs/`: `decisions.md` (findings), `first_session_brief.md` and `first_session_report.md` (the first Helix Native session).
- `guide/`: the four scripts the guide hands to a new user (save_state, render, match_eq, master_limit).
- Scripts at the root, run from the root:
    - `make_chain*.py`: each writes one .hlx preset for a chain version. The presets themselves are not in the repo.
    - `render_*.py`: render the take through a saved plugin state for listening. `render_preroll.py` holds the lead-in fix for the smeared first note.
    - `fit_*.py` and `*_fit*.json`: knob fits against the stem and their results.
    - `match_eq.py`, `master_limit.py`: the matching EQ (as an IR) and the stand-in mastering limiter.
    - `helixlab.py`, `save_state.py`, `probe*.py`, `knob_*.py`, `many_instances.py`, `cab_check*.py`: loading Helix Native from Python, saving states, checking knob control and limits.
    - The rest are measuring scripts (spectra, envelopes, filter motion, tightness and others), each described in its first lines.

## Requirements

- Windows with Helix Native (VST3) installed.
- Python 3 with pedalboard, numpy and scipy.
- Your own stem and DI in `input/`, and your own presets built in Helix Native.

## Example audio

- `input/guitar_played.wav`: the owner's clean DI, one 2.4 s riff played 4 times.
- `work/mp3/best_reference_plus_limiter.mp3`: that DI through the best chain, EQ-matched and limited; the owner's best by ear.
