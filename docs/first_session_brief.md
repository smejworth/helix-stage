# Brief: Helix Native test for the tone matching project

Work only inside C:\Users\userx\helix_stage. Do not search or read anywhere else on the drive. I am new to Python and audio code: keep scripts small and say what each one does.

## Background
- Wider goal: make my clean guitar take sound like a reference recording with heavy fuzz and what sounds like a sub octave.
- Idea under test: write Helix Native presets from code and let a script adjust their controls.
- Already in this folder: a Python environment pbvenv with pedalboard 0.9.26 that loads the Helix Native VST3 headless. load_fbtest.py opens the plugin editor so a preset can be clicked, then saves the plugin state. fb_measure.py loads a saved state and renders a test signal. A previous session may have left save_state.py here too. Read these first.
- Known: the plugin exposes only master input level, master output level, master bypass, snapshot index (1 to 8) and generic knob, switch and cc slots. No preset select. An exported preset is plain JSON (schema L6Preset).

## Rules
- Never decrypt, edit or hand-build a plugin state blob. States are only saved from the running plugin and loaded back unchanged.
- Never write into any Line 6 folder or the preset library by file copy. Presets go in through the plugin window only.
- Do not touch licensing or authorisation.
- Do not install any package without asking me first.
- Do not save memories. Keep all notes in this folder.
- Report only what you measured. Say "not tested" for anything you did not run.
- In anything you write: no em-dashes, no tilde character, no dollar sign.
- You may use computer use for clicks inside the Helix Native window only.

## Task 1: template preset
In Helix Native, build a preset with one fuzz block and one octave (sub octave) block, assign the fuzz block's main gain or drive control to automation slot Knob 1, save it, and export it to helix_stage\template_fuzz_oct.hlx. Ask me before choosing which fuzz and octave models if it is not obvious. Read the exported file and record in helix_stage\first_session_report.md: the block model ids, every parameter key and value, and exactly how the Knob 1 assignment appears in the JSON.

## Task 2: can Python turn a bound knob? (the question that matters)
1. Load that preset through the plugin editor window and save the plugin state.
2. Load the saved state headless, list the exposed parameters, find the Knob 1 slot.
3. Render the same test signal (110 Hz sawtooth, amplitude 0.3, 2 seconds, 48 kHz) three times with Knob 1 low, middle and high.
4. Compare RMS level and a rough measure of harmonic content. Clear ordered differences mean yes; identical outputs mean no.
5. Render once each at snapshot index 1 and 2 to confirm snapshot switching from Python works.
Write the numbers and the yes or no answer into first_session_report.md.

## Task 3: can a preset written by code be imported?
Copy the template to helix_stage\written_test.hlx, change one obvious value in the JSON (for example the fuzz gain) and the preset name, import it through the plugin window, and record whether it imports and whether the changed value shows.

## Then stop
Do not start any search or tone matching. Tell me the report is ready so I can copy first_session_report.md and template_fuzz_oct.hlx back to the main project.
