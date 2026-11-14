# Clinical SFX bed (sub hits, scan sweeps, digital ticks, one heavy impact per beat), synthesised.
# usage: python3 sfx.py out.wav
import sys, wave
import numpy as np
SR = 48000; DUR = 31.45; n = int(SR * DUR)
L = np.zeros(n); R = np.zeros(n); rng = np.random.default_rng(7)
def place(sig, t, pan=0.0, gain=1.0):
    i = int(t * SR); s = sig[:max(0, n - i)] * gain
    L[i:i + len(s)] += s * (1 - max(0, pan)); R[i:i + len(s)] += s * (1 + min(0, pan))
def onepole(x, a):
    y = np.empty_like(x); acc = 0.
    for k in range(len(x)): acc += a[k] * (x[k] - acc) if hasattr(a, '__len__') else a * (x[k] - acc); y[k] = acc
    return y
def norm(y): return y / (np.max(np.abs(y)) + 1e-9)
def whoosh(d, peak=0.7):
    m = int(SR * d); t = np.arange(m) / SR; cut = 0.02 + 0.22 * np.sin(np.pi * np.clip(t / d, 0, 1)) ** 2
    y = onepole(rng.standard_normal(m), cut); env = np.sin(np.pi * np.clip(t / d, 0, 1) ** peak) ** 2
    return norm(y * env)
def sub(weight=1.0):
    m = int(SR * 0.45); t = np.arange(m) / SR; f = 48 + 55 * np.exp(-t * 26)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * (11 / weight))
    click = onepole(rng.standard_normal(m), 0.3) * np.exp(-t * 170) * 0.45
    return norm(body + click)
def impact():
    m = int(SR * 0.7); t = np.arange(m) / SR; f = 44 + 95 * np.exp(-t * 30)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 6.5)
    crack = onepole(rng.standard_normal(m), 0.55) * np.exp(-t * 40) * 0.6
    return norm(body + crack)
def tick(f0=2400):
    m = int(SR * 0.05); t = np.arange(m) / SR
    return norm(np.sin(2 * np.pi * f0 * t) * np.exp(-t * 140) + 0.4 * np.sin(2 * np.pi * f0 * 1.7 * t) * np.exp(-t * 220))
def scan(d=0.6):
    m = int(SR * d); t = np.arange(m) / SR; f = 600 + 2600 * (t / d)
    y = np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.25 + onepole(rng.standard_normal(m), 0.5) * 0.3
    return norm(y * np.sin(np.pi * t / d) ** 2)
def paper():
    m = int(SR * 0.3); t = np.arange(m) / SR
    return norm(onepole(rng.standard_normal(m), 0.7) * np.exp(-t * 14) * (1 - np.exp(-t * 200)))
W_, S_, I_, T_, SC = whoosh, sub, impact, tick, scan
# --- cue sheet (each lands on a visible contact / change) ---
place(SC(0.7), 3.80, -0.4, 0.16)            # enzyme scan widget opens
place(T_(2000), 4.44, -0.4, 0.22)           # ENZYME x1
place(S_(0.7), 5.62, -0.3, 0.32)            # AROMATASE label lands
place(W_(0.30), 6.34, 0.3, 0.16)            # enzyme flies into lens
for k in range(4): place(T_(2600 + 200 * k), 6.96 + k * 0.18, 0.4, 0.12)  # markers light
place(T_(1800), 7.54, 0.3, 0.2)             # ADIPOSE TISSUE tag
place(W_(0.30), 8.36, 0, 0.16)              # lens -> flow handoff
place(T_(2200), 8.92, -0.3, 0.2); place(T_(2200), 9.80, 0.3, 0.2)
place(S_(1.0), 10.58, 0, 0.36)              # layout restack
place(SC(1.6), 11.0, 0, 0.12)               # curve draws
place(T_(3000), 12.06, 0.3, 0.2)            # RATE tag
place(W_(0.28), 12.92, 0, 0.14)
place(T_(2400), 13.48, -0.3, 0.18); place(T_(2400), 13.60, 0.3, 0.18)  # SAME DOSE checks
place(S_(0.8), 14.70, 0.3, 0.3)             # high bar tops out
place(W_(0.3), 15.25, 0, 0.14)              # restore full frame
place(S_(1.0), 15.90, 0, 0.36)              # punch-in + gauge
place(SC(0.6), 16.45, 0.3, 0.12)            # needle swing
for tt in (17.80, 18.80, 19.64): place(S_(0.6), tt, -0.3, 0.26); place(T_(1600), tt, -0.3, 0.14)
place(paper(), 21.00, 0, 0.22); place(S_(0.8), 21.22, 0, 0.26)  # lab report drops
place(I_(), 21.76, 0, 0.5)                  # CONFIRMED (heavy)
place(T_(2600), 22.38, -0.3, 0.2); place(T_(1900), 23.42, 0.3, 0.2)
place(W_(0.3), 24.45, 0, 0.14); place(S_(0.8), 24.70, 0, 0.3)  # CTA card
for k in range(4): place(T_(2400 + 150 * k), 25.3 + k * 0.28, 0.2, 0.12)
place(S_(0.9), 26.88, 0.3, 0.34)            # FREE stamp
place(I_(), 27.80, 0, 0.48)                 # COMMENT pill (heavy)
for k in range(3): place(T_(1500 - 200 * k), 28.84 + k * 0.07, 0.5, 0.14)
place(S_(0.7), 30.62, 0, 0.22)              # end lockup
st = np.stack([L, R], 1); st = st / max(1.0, np.max(np.abs(st)) / 0.9)
with wave.open(sys.argv[1], 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((st * 32767).astype(np.int16).tobytes())
print('sfx ok')
