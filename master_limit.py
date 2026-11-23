# master_limit.py : a simple peak limiter, as a stand-in for the mastering limiter the original record went through
# (the stem was separated from a finished mix; our render has never been through one). It looks 5 ms ahead, turns the
# level down just enough that no peak passes the ceiling, and lets go over 60 ms. The ceiling is set so the result's
# peak-to-average ratio (crest) equals the stem's, then the file is level-matched to the stem.
# This is not in Helix; it shows what the final mastering step would add.
# usage: python master_limit.py STEM IN.wav OUT.wav
import sys, numpy as np
from pedalboard.io import AudioFile
from scipy.ndimage import maximum_filter1d

def load(p):
    with AudioFile(p) as f:
        return f.read(f.frames)[0], f.samplerate
s, sr = load(sys.argv[1]); y, _ = load(sys.argv[2])
crest = lambda x: 20 * np.log10(np.abs(x).max() / np.sqrt(np.mean(x ** 2)))
target = crest(s)
def limit(x, ceiling):
    la = int(0.005 * sr)
    need = np.minimum(1.0, ceiling / (maximum_filter1d(np.abs(x), 2 * la + 1) + 1e-12))   # gain each sample may have
    g = np.empty_like(need); cur = 1.0; rel = np.exp(-1 / (0.06 * sr))
    for i in range(len(need)):                     # drop at once, recover slowly (release)
        cur = need[i] if need[i] < cur else need[i] + (cur - need[i]) * rel
        g[i] = cur
    g = np.convolve(g, np.ones(la) / la, mode='same')    # smooth the gain so the limiter does not crackle
    return x * g
lo, hi = 0.05, 1.0
pk = np.abs(y).max()
for _ in range(14):                                 # find the ceiling that gives the stem's crest
    mid = (lo + hi) / 2
    if crest(limit(y, mid * pk)) > target:
        hi = mid
    else:
        lo = mid
out = limit(y, (lo + hi) / 2 * pk)
out = out * np.sqrt(np.mean(s ** 2)) / np.sqrt(np.mean(out ** 2))
out = out * min(1.0, 0.999 / np.abs(out).max())
print(f'crest before {crest(y):.2f} dB, after {crest(out):.2f} dB (stem {target:.2f}); level {20 * np.log10(np.sqrt(np.mean(out ** 2))):.2f} dB (stem {20 * np.log10(np.sqrt(np.mean(s ** 2))):.2f})')
with AudioFile(sys.argv[3], 'w', sr, 2, bit_depth=24) as f:
    f.write(np.stack([out, out]).astype(np.float32))
