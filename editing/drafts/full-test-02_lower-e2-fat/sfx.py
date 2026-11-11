# SFX bed for "Two things to lower E2 (fat)". Times are on the edited-cut timeline (render.py).
# Clinical palette only: sub hits, scan sweeps, digital ticks, one heavy impact per beat.
import numpy as np, wave, sys
SR = 48000; DUR = 2413 / 30; n = int(SR * DUR); L = np.zeros(n); R = np.zeros(n)
rng = np.random.default_rng(11)
def place(sig, t, pan=0.0, gain=1.0):
    i = int(t * SR); s = sig[:max(0, n - i)] * gain
    L[i:i + len(s)] += s * (1 - max(0, pan)); R[i:i + len(s)] += s * (1 + min(0, pan))
def lp(x, a):
    y = np.zeros_like(x); acc = 0
    for k in range(len(x)): acc += a * (x[k] - acc); y[k] = acc
    return y
def norm(y): return y / np.max(np.abs(y))
def whoosh(d):
    m = int(SR * d); t = np.arange(m) / SR; nz = rng.standard_normal(m)
    cut = 0.02 + 0.25 * np.sin(np.pi * np.clip(t / d, 0, 1)) ** 2; y = np.zeros(m); acc = 0
    for k in range(m): acc += cut[k] * (nz[k] - acc); y[k] = acc
    return norm(y * np.sin(np.pi * np.clip(t / d, 0, 1) ** 0.7) ** 2)
def thud(weight=1.0):
    m = int(SR * 0.35); t = np.arange(m) / SR; f = 55 + 60 * np.exp(-t * 28)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * (14 / weight))
    return norm(body + lp(rng.standard_normal(m), 0.25) * np.exp(-t * 160) * 0.5)
def tick():
    m = int(SR * 0.05); t = np.arange(m) / SR
    return norm(np.sin(2 * np.pi * 2400 * t) * np.exp(-t * 140) + 0.4 * np.sin(2 * np.pi * 4100 * t) * np.exp(-t * 220))
def impact():
    m = int(SR * 0.6); t = np.arange(m) / SR; f = 48 + 90 * np.exp(-t * 30)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 7)
    return norm(body + 0.55 * lp(rng.standard_normal(m), 0.6) * np.exp(-t * 45))
def scan(d):
    m = int(SR * d); t = np.arange(m) / SR; nz = rng.standard_normal(m)
    cut = 0.05 + 0.35 * (t / d); y = np.zeros(m); acc = 0
    for k in range(m): acc += cut[k] * (nz[k] - acc); y[k] = acc
    y = y - lp(y, 0.08) + 0.15 * np.sin(2 * np.pi * (900 + 1400 * t / d) * t)
    return norm(y * np.minimum(1, t / 0.03) * np.minimum(1, (d - t) / 0.05))
def riser(d):   # needle sweep: rising sine + filtered noise
    m = int(SR * d); t = np.arange(m) / SR; f = 120 + 520 * (t / d) ** 2
    y = np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.6 + 0.4 * (rng.standard_normal(m) - lp(rng.standard_normal(m), 0.1)) * (t / d)
    return norm(y * (t / d) ** 1.5 * np.minimum(1, (d - t) / 0.02))
dB = lambda x: 10 ** (x / 20)
hit = lambda t, g=-17: place(thud(1.4), t, gain=dB(g))
th = lambda t, g=-19: place(thud(1.0), t, gain=dB(g))
tk = lambda t, g=-29: place(tick(), t, gain=dB(g))
sw = lambda t, d=0.4, g=-29: place(scan(d), t, gain=dB(g))
imp = lambda t, g=-14: place(impact(), t, gain=dB(g))
wh = lambda t_land, d=0.3, g=-27: place(whoosh(d), t_land - d * 0.7, gain=dB(g))

tk(3.60, -31)                                                        # topic band
hit(4.10); tk(4.62); sw(4.25, 3.1, -34); imp(7.50)                   # S1 line graph, breach
sw(8.40, 0.5); tk(8.82); sw(9.60, 0.9); tk(9.86); tk(10.82, -31)     # S2 scans
wh(12.72, 0.25); wh(14.46, 0.25); imp(15.58)                         # S3 Rx labels, stamp
th(16.30, -24)
for t in (17.18, 17.82, 18.54, 19.20, 19.64): tk(t, -33)             # S4 receipt printing
th(20.34, -18); tk(20.92)
wh(21.50, 0.38); th(22.00, -21); tk(23.76); hit(24.86)               # S5 PIP + cells
for t in (26.02, 26.30, 26.62): tk(t, -31)
sw(27.40, 1.0, -33); tk(29.10); wh(30.10, 0.34)
hit(31.55)
for k in range(10): tk(31.60 + k * 0.06, -38)                        # S6 count-up
th(32.20, -17); tk(32.96); sw(34.14, 0.9, -32); tk(34.90)
tk(35.6333, -30); place(riser(1.94), 35.86, gain=dB(-30)); imp(37.80) # gauge needle, slam
hit(38.4167); sw(38.64, 1.0, -33); sw(39.68, 1.1, -33); tk(41.38); tk(41.76)
wh(43.30, 0.30); th(43.30, -19)                                      # S8 wipe
th(44.62, -18); tk(45.60); tk(46.36)                                 # S9 steps
th(47.40, -18); tk(48.30); tk(49.10)
th(49.60, -18); tk(52.10); tk(52.88)
hit(54.05); sw(54.30, 0.95, -32); tk(54.74); th(55.38, -20)          # S10 slider
for t in (57.02, 58.26, 59.20, 59.82): tk(t, -30)
hit(60.80); tk(61.70, -31); sw(62.30, 0.5, -33); tk(63.32); th(64.14, -18); sw(66.70, 0.5, -33); tk(67.58)  # S11
hit(68.25); sw(69.00, 1.0, -33)
for t in (69.2, 69.6, 70.0): tk(t, -33)
wh(70.50, 0.22, -26); imp(70.50, -13); tk(72.06)                     # S12 slab lands
hit(73.00); tk(74.08, -31); tk(75.30, -31); th(75.88, -18)           # S13 CTA
for k in range(8): tk(76.42 + k * 0.0975, -37)
tk(77.30, -28); tk(78.00, -31); th(79.22, -20)
out = np.stack([L, R], 1); print('sfx peak dBFS %.1f' % (20 * np.log10(np.max(np.abs(out)))))
w = wave.open(sys.argv[1] if len(sys.argv) > 1 else 'sfx.wav', 'wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
w.writeframes((np.clip(out, -1, 1) * 32767).astype(np.int16).tobytes()); w.close()
