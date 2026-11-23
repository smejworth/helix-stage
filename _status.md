# Helix, status

**Phase:** matching the original isolated guitar track of Korn's "Here to Stay" intro (`input/guitar_stem.wav`, kept out of git) with the owner's clean DI of the same riff (`input/guitar_played.wav`) through Helix Native, driven from Python on the Windows laptop (`C:\Users\userx\helix_stage`). Findings and verdicts are in `docs/decisions.md`. The repo is the PUBLIC `smejworth/helix-stage`.

## Where it stands

- [x] Best by ear overall: `work/helix18/5_reference_plus_master_limiter.wav` (owner: "was best"), also as `work/mp3/best_reference_plus_limiter.mp3`. It is the chain 9b reference (`chain9_state.bin`, knobs Whammy mix 0.5, Auto Filter up, low pass, 100 Hz, depth 500 Hz, Sens 0.1, Attack 20 ms, Decay 0.8 s, Q 2, Mix 1, compressor 6:1 at -10 dB, 10 ms, Drive 8.2), rendered with the loop lead-in, EQ-matched, then the stand-in limiter.
- [x] Ruled out by ear: envelope filter after the amp, sweeping down, wider sweep ranges, moving the Auto Filter's peak, Mutant and Mystery filters, high-passing the take, a Boctaver plus fuzz stand-in for the Micro Synth (series or parallel). Older listening items for `work/helix04`, `helix05`, `helix06` and `helix09` were superseded by these later verdicts.
- [ ] Still missing by ear: the original's more apparent, more aggressive envelope and its tighter, more distinct sound. Measures tried for the envelope do not track the owner's ear (`docs/decisions.md`).
- [ ] The matching EQ and the limiter run in Python only. Loading the matching EQ into Helix as an IR (2048 samples, `work/match01/match_ir_2048_48k.wav` or a new one for chain 9) and finding a Helix block for the limiter's job are not done.
- [ ] Open problem: Helix cab blocks do not remove the top end in headless renders (`docs/decisions.md`). An EQ block is the stand-in. Cause not found.
- [x] Guide for a guitarist friend, as a shareable doc: https://claude.ai/artifact/PrvqtjsG96M8nNYNVcgjVq. Its four scripts are in `guide/`. `render.py` ran without errors on `chain9_state.bin`; the full loop on another PC is not tested.

## Rules for every script

- [ ] Every render starts with one 2.4 s pass of the take as a lead-in, cut off afterwards (`render_preroll.py`); without it the first note is smeared. Renders made before that fix all have the fault.
- [ ] Knob values stay between 0.0001 and 0.9999 (exactly 0.0 is ignored), and each process stays under about 50 renders.

## Repo

- [x] Public GitHub repo `smejworth/helix-stage`. `.gitignore` is an allow-list of the project's scripts, the guide scripts, the notes and two example audio files (the owner's DI and the best render). Every push needs the owner's go.
- [ ] Untracked leftovers from the earlier, separate project sit in `_archive/` (ignored). The owner may delete them.
