# wow_per_note.py : measures the "wow" on the first two notes of each riff repeat (notes start at 0.0 and 0.6 s in
# the owner's loop). A wow is the sound opening up then closing within a note. The balance "highs minus lows"
# (1.5 to 5 kHz against 150 to 500 Hz, dB) is tracked every 20 ms; per note it prints the swing (largest minus
# smallest), when the most open moment comes after the note starts, and how far it closes from that moment to the
# note's end. Files are lined up with the loop (stem and renders share the same timing grid).
# usage: python wow_per_note.py FILE [FILE ...]
import sys, numpy as np
from pedalboard.io import AudioFile

N = 2048
for path in sys.argv[1:]:
    with AudioFile(path) as f:
        y, sr = f.read(f.frames)[0], f.samplerate
    H = int(0.02 * sr); fr = np.fft.rfftfreq(N, 1 / sr); w = np.hanning(N)
    def hl(i):
        p = np.abs(np.fft.rfft(y[i:i + N] * w)) ** 2
        return 10 * np.log10(p[(fr >= 1500) & (fr < 5000)].sum() / p[(fr >= 150) & (fr < 500)].sum())
    rows = []
    for k in range(4):
        for start in (0.0, 0.6):
            st = int((k * 2.4 + start) * sr)
            tr = np.array([hl(st + j * H) for j in range(28) if st + j * H + N < len(y)])
            if len(tr) < 28:
                continue
            tr = np.convolve(tr, np.ones(3) / 3, mode='same')[1:-1]
            imax = int(np.argmax(tr))
            rows.append((tr.max() - tr.min(), (imax + 1) * 0.02, tr.max() - tr[-1]))
    a = np.array(rows)
    print(f'{path.split(chr(92))[-1]:30s} swing {a[:, 0].mean():4.1f} dB   most open at {a[:, 1].mean():.2f} s   closes {a[:, 2].mean():4.1f} dB by note end   '
          f'(per note swing: {" ".join(f"{x:.0f}" for x in a[:, 0])})')
