# First session report: Helix Native test

Session date: 2026-11-22. All work done inside C:\Users\userx\helix_stage.

## Short answers
- Task 1: template built, saved and exported to template_fuzz_oct.hlx. Done.
- Task 2: YES, Python can turn a control bound to Knob 1. Outputs change with the knob and repeat exactly. Brightness rises in order from knob 0.2 to 1.0. Knob 0.0 does not fit that order (details below). Snapshot switching from Python also works.
- Task 3: YES, a preset file edited by code loads in the plugin window, and the changed value shows (Sustain 2.0 instead of 8.3).

## Model choice (decided by Claude)
- Fuzz: Triangle Fuzz, id HD2_DistTriangleFuzz (Big Muff style, heavy fuzz). Its gain control is Sustain, so Sustain is on Knob 1.
- Sub octave: Boctaver, id VIC_PitchBoctaver (OC-2 style analog octaver).
- Order: Boctaver first, then Triangle Fuzz. An analog style octaver tracks a clean note better than a fuzzed one.

## Task 1: template preset
How it was built: save_state.py opened the editor. Claude replaced the old Feedbacker block in the FB TEST buffer with Boctaver, added Triangle Fuzz after it, set Controller Assign to Triangle Fuzz / Sustain / Knob 1, and renamed the preset FUZZ OCT TMPL. Then "..." menu > Save To Disk wrote template_fuzz_oct.hlx, and "..." menu > Save To Library saved it into FACTORY 1 slot 01A.

Slot 01A used to hold the earlier test preset "FB TEST". Copies of it are in this folder as FB_TEST.hlx and FB_TEST_on.hlx.

Because the preset started from the FB TEST buffer, it kept that preset's snapshot settings: in snapshots 2 to 8 the Boctaver (block0) is bypassed. In snapshot 1 both blocks are on.

### Block model ids and every parameter (from template_fuzz_oct.hlx)
Values are stored 0 to 1. The editor shows them times 10.

block0, VIC_PitchBoctaver (path 0, position 0)
- @enabled true, @no_snapshot_bypass false, @path 0, @position 0, @stereo false, @type 0
- DryLevel 0.60 (shown 6.0)
- Oct1Level 0.60 (shown as -1 Oct 6.0)
- Oct2Level 0.30 (shown as -2 Oct 3.0)

block1, HD2_DistTriangleFuzz (path 0, position 2)
- @enabled true, @no_snapshot_bypass false, @path 0, @position 2, @stereo false, @type 0
- Level 0.810 (shown 8.1)
- Sustain 0.830 (shown 8.3)
- Tone 0.560 (shown 5.6)

Other parts of the file (input, split, join and output blocks, dt0, dt1, powercab, variax, irUuidTable) are plugin defaults. They are kept unchanged in the file.

### How the Knob 1 assignment appears in the JSON
It is one entry in a list under data.tone.automation:

```
"automation" : {
 "@assignments" : [
  {
   "@max" : 1.0,
   "@min" : 0.0,
   "@param" : "dsp0.block1.Sustain"
  }
 ]
}
```

There is no knob number in the entry. Knob 1 is presumably the first position in the @assignments list (not tested with a second assignment). @min and @max match the Min Sustain 0.0 and Max Sustain 10.0 shown in the editor.

## Task 2: can Python turn a bound knob?
Steps: the state was saved by the plugin when the editor closed (template_state.bin, 124690 bytes, not edited). knob_test.py and knob_sweep.py load it unchanged and render a 110 Hz sawtooth, amplitude 0.3, 2 seconds, 48 kHz. Measurements use the steady part from 0.5 to 1.9 seconds.

Exposed parameters found: knob_01 (raw range 0 to 1, step 0.001) and snapshot_index (values 1 to 8), along with the master and generic slots listed in the brief. After loading the state, knob_01 reads 0.0 and snapshot_index reads 1.

### knob_test.py (three positions, a repeat, two snapshots)

| render | rms | centroid Hz | share above 1 kHz | 55 Hz vs 110 Hz |
|---|---|---|---|---|
| as loaded | 0.0219 | 219.8 | 0.0269 | 0.3615 |
| knob low (0.0) | 0.0219 | 219.8 | 0.0269 | 0.3615 |
| knob mid (0.5) | 0.0220 | 206.5 | 0.0233 | 0.4712 |
| knob high (1.0) | 0.0215 | 289.8 | 0.0415 | 0.3378 |
| knob mid again | 0.0220 | 206.5 | 0.0233 | 0.4712 |
| snapshot 1 | 0.0219 | 219.8 | 0.0269 | 0.3615 |
| snapshot 2 | 0.0225 | 183.1 | 0.0166 | 0.0000 |

RMS of the difference between two outputs:
- mid vs mid again (repeat noise): 0.0, so renders are exactly repeatable
- low vs high: 0.013227
- snapshot 1 vs 2: 0.016851

### knob_sweep.py (six positions)

| knob | rms | centroid Hz | share above 1 kHz | crest (peak / rms) |
|---|---|---|---|---|
| 0.0 | 0.0219 | 219.8 | 0.0269 | 2.00 |
| 0.2 | 0.0216 | 193.0 | 0.0200 | 1.86 |
| 0.4 | 0.0219 | 203.2 | 0.0225 | 1.78 |
| 0.6 | 0.0220 | 209.1 | 0.0239 | 1.98 |
| 0.8 | 0.0219 | 217.5 | 0.0262 | 1.96 |
| 1.0 | 0.0215 | 289.8 | 0.0415 | 1.62 |

### Answer: YES
- Setting knob_01 from Python changes the rendered sound, and the same setting gives exactly the same output. So the bound Sustain control is reachable from Python.
- From 0.2 to 1.0, both brightness measures rise in order (centroid 193.0, 203.2, 209.1, 217.5, 289.8 Hz).
- Knob 0.0 breaks the order: it is brighter than 0.2. The cause is not tested.
- RMS hardly moves (0.0215 to 0.0220). This fuzz evens out the output level, so loudness is not a useful measure of the knob here.
- The crest factor does not move in a clear order either.
- The "as loaded" render is identical to knob 0.0, even though the preset stores Sustain 0.83. So once the state loads, Knob 1 seems to set Sustain itself (starting at 0), rather than the stored preset value being used. Not tested further.
- Snapshot switching: setting snapshot_index to 2 removes the 55 Hz sub octave (ratio 0.3615 drops to 0.0000), which matches snapshot 2 bypassing the Boctaver. Snapshot switching from Python works.

## Task 3: can a preset written by code be imported?
- written_test.hlx is a copy of template_fuzz_oct.hlx with two lines changed: the name (FUZZ OCT TMPL to WRITTEN TEST) and Triangle Fuzz Sustain (0.830 to 0.200). The file is checked as valid JSON, and a line compare shows only those two lines differ.
- It was loaded through the plugin window with "..." menu > Open From Disk. That loads it into the editor without writing to any library slot.
- Result: it loaded with no error. The editor showed the name WRITTEN TEST and Sustain 2.0. The Knob 1 marker was still on Sustain. Screenshot: written_test_import.jpg.
- The PRESETS > IMPORT button (which writes into a library slot) was not tested.
- The editor state after this was saved as written_state.bin but has not been rendered (not tested).

## Notes for the main project
- The editor's pop-up menus and lists ignore a normal simulated click. Two things work: a slow press, short wait, then release on a menu item; and the mouse wheel over a closed dropdown to step its value. Ctrl+S does not save. Double-clicking a preset in the list reloads it and drops unsaved edits (Undo brings them back).
- knob_test_out.npz was overwritten by this session's run of knob_test.py.

## Files from this session
- first_session_brief.md: the brief
- template_fuzz_oct.hlx: exported template (Task 1)
- template_state.bin: plugin state with the template loaded (Task 2)
- knob_sweep.py: six-point knob check (new)
- knob_test_out.npz: audio from knob_test.py
- written_test.hlx: code-edited preset (Task 3)
- written_state.bin: plugin state after loading written_test.hlx (not used)
- written_test_import.jpg: screenshot of the imported preset in the editor
