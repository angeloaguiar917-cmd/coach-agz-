# Speech trimmed through trim.json (8 ms crossfades) + clinical SFX placed on visual landings (source times).
# usage: python3 audio_e2.py <in_48k_stereo.wav> <out.wav>
import json, sys, wave, os
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
TR = json.load(open(HERE + '/trim.json'))['remove']
SR = 48000
w = wave.open(sys.argv[1]); a = np.frombuffer(w.readframes(w.getnframes()), np.int16).reshape(-1, 2).astype(np.float64) / 32768
# --- speech cut ---
keep = []; t = 0.0
for s, e in TR: keep.append((t, s)); t = e
keep.append((t, len(a) / SR))
xf = int(SR * 0.008); out = None
for s, e in keep:
    seg = a[int(s * SR):int(e * SR)].copy()
    if out is None: out = seg; continue
    ramp = np.linspace(0, 1, xf)[:, None]
    out[-xf:] = out[-xf:] * (1 - ramp) + seg[:xf] * ramp
    out = np.concatenate([out, seg[xf:]])
n = len(out); L = np.zeros(n); R = np.zeros(n)
rng = np.random.default_rng(11)
def m(t): return t - sum(min(b, t) - a_ for a_, b in TR if a_ < t)
def place(sig, t, gain=1.0, pan=0.0):
    i = int(m(t) * SR); s = sig[:max(0, n - i)] * gain
    L[i:i + len(s)] += s * (1 - max(0, pan)); R[i:i + len(s)] += s * (1 + min(0, pan))
def lp(x, c):
    y = np.zeros_like(x); acc = 0.0
    for k in range(len(x)): acc += c * (x[k] - acc); y[k] = acc
    return y
def nrm(y): return y / (np.max(np.abs(y)) + 1e-9)
def thud(weight=1.0):
    k = int(SR * 0.35); tt = np.arange(k) / SR; fr = 55 + 60 * np.exp(-tt * 28)
    body = np.sin(2 * np.pi * np.cumsum(fr) / SR) * np.exp(-tt * (14 / weight)); click = lp(rng.standard_normal(k), 0.25) * np.exp(-tt * 160) * 0.5
    return nrm(body + click)
def impact():
    k = int(SR * 0.6); tt = np.arange(k) / SR; fr = 48 + 90 * np.exp(-tt * 30)
    return nrm(np.sin(2 * np.pi * np.cumsum(fr) / SR) * np.exp(-tt * 7) + 0.55 * lp(rng.standard_normal(k), 0.6) * np.exp(-tt * 45))
def tick():
    k = int(SR * 0.05); tt = np.arange(k) / SR
    return nrm(np.sin(2 * np.pi * 2400 * tt) * np.exp(-tt * 140) + 0.4 * np.sin(2 * np.pi * 4100 * tt) * np.exp(-tt * 220))
def scan(d, rise=True):
    k = int(SR * d); tt = np.arange(k) / SR; nz = rng.standard_normal(k)
    cut = 0.05 + 0.35 * (tt / d if rise else 1 - tt / d); y = np.zeros(k); acc = 0.0
    for i in range(k): acc += cut[i] * (nz[i] - acc); y[i] = acc
    y = y - lp(y, 0.08) + 0.15 * np.sin(2 * np.pi * (900 + 1400 * tt / d) * tt)
    return nrm(y * np.minimum(1, tt / 0.03) * np.minimum(1, (d - tt) / 0.05))
def whoosh(d):
    k = int(SR * d); tt = np.arange(k) / SR; nz = rng.standard_normal(k)
    cut = 0.02 + 0.25 * np.sin(np.pi * np.clip(tt / d, 0, 1)) ** 2; y = np.zeros(k); acc = 0.0
    for i in range(k): acc += cut[i] * (nz[i] - acc); y[i] = acc
    return nrm(y * np.sin(np.pi * np.clip(tt / d, 0, 1) ** 0.7) ** 2)
def snap():   # link break: short bright crack + sub
    k = int(SR * 0.25); tt = np.arange(k) / SR
    return nrm(lp(rng.standard_normal(k), 0.9) * np.exp(-tt * 60) + 0.8 * np.sin(2 * np.pi * 70 * tt) * np.exp(-tt * 18))
dB = lambda x: 10 ** (x / 20)
# whooshes END on the landing; hits/ticks ON the landing frame
def sw_in(t_land, d=0.34, g=-27): place(whoosh(d), t_land - d * 0.75, dB(g))
place(thud(0.9), 1.14, dB(-22))                     # hook punch-in on "body"
place(thud(1.4), 4.44, dB(-16))                     # counter "1" lands
place(scan(0.35), 5.62, dB(-29))                    # AROMATASE resolves
sw_in(6.74)                                         # split-screen opens
place(tick(), 7.54, dB(-27))                        # ADIPOSE TISSUE tag
place(scan(0.6), 8.64, dB(-31))                     # conversion flow starts
for k in range(5): place(tick(), 10.80 + 0.14 * k, dB(-33))   # fat cells grow on axis
place(scan(0.85), 11.68, dB(-30))                   # curve draws
place(tick(), 12.08, dB(-25))                       # CONVERSION tag
place(snap(), 13.62, dB(-17))                       # link breaks (heavy beat)
place(thud(1.0), 14.64, dB(-20))                    # lock clicks shut
for t0 in (17.80, 18.78, 19.64): place(tick(), t0, dB(-25))   # detection brackets lock
place(scan(0.4, False), 19.64, dB(-32))             # mood waveform destabilises
sw_in(21.30, 0.30)                                  # lab report slides up
place(impact(), 21.76, dB(-15))                     # CONFIRMED
place(tick(), 22.38, dB(-26)); place(tick(), 22.96, dB(-28))
sw_in(24.98, 0.30)                                  # checklist card arrives
for k in range(4): place(tick(), 25.80 + 0.16 * k, dB(-31))
place(thud(1.2), 26.90, dB(-17))                    # FREE stamp
place(impact(), 27.82, dB(-15))                     # COMMENT "E2" pill
place(tick(), 29.72, dB(-24))                       # DM toast
sfx = np.stack([L, R], 1)
mix = out + sfx
mix = np.clip(mix, -1, 1)
wo = wave.open(sys.argv[2], 'wb'); wo.setnchannels(2); wo.setsampwidth(2); wo.setframerate(SR)
wo.writeframes((mix * 32767).astype(np.int16).tobytes()); wo.close()
print('speech dur', n / SR)
