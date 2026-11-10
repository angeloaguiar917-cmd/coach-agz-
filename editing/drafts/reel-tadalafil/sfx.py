# Clinical SFX bed for the Tadalafil Reel (cut timeline). Usage: sfx.py <out.wav> <dur>
import numpy as np, wave, sys
SR = 48000; DUR = float(sys.argv[2]); n = int(SR * DUR); L = np.zeros(n); R = np.zeros(n)
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
    return norm(np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * (14 / weight)) + lp(rng.standard_normal(m), 0.25) * np.exp(-t * 160) * 0.5)
def tick():
    m = int(SR * 0.05); t = np.arange(m) / SR
    return norm(np.sin(2 * np.pi * 2400 * t) * np.exp(-t * 140) + 0.4 * np.sin(2 * np.pi * 4100 * t) * np.exp(-t * 220))
def impact():
    m = int(SR * 0.6); t = np.arange(m) / SR; f = 48 + 90 * np.exp(-t * 30)
    return norm(np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 7) + 0.55 * lp(rng.standard_normal(m), 0.6) * np.exp(-t * 45))
def scan(d):
    m = int(SR * d); t = np.arange(m) / SR; nz = rng.standard_normal(m); cut = 0.05 + 0.35 * (t / d); y = np.zeros(m); acc = 0
    for k in range(m): acc += cut[k] * (nz[k] - acc); y[k] = acc
    y = y - lp(y, 0.08) + 0.15 * np.sin(2 * np.pi * (900 + 1400 * t / d) * t)
    return norm(y * np.minimum(1, t / 0.03) * np.minimum(1, (d - t) / 0.05))
def ticker(d):   # rapid digital counter
    m = int(SR * d); y = np.zeros(m); tk = tick()
    for k in range(int(d / 0.045)):
        i = int(k * 0.045 * SR); y[i:i + len(tk)] += tk[:max(0, m - i)] * (0.5 + 0.5 * k / (d / 0.045))
    return norm(y)
def riser(d):    # sub swell into a slam
    m = int(SR * d); t = np.arange(m) / SR; f = 40 + 40 * (t / d)
    return norm(np.sin(2 * np.pi * np.cumsum(f) / SR) * (t / d) ** 2)
dB = lambda x: 10 ** (x / 20)
hit = lambda t, g=-17: place(thud(1.4), t, gain=dB(g))
tk = lambda t, g=-28: place(tick(), t, gain=dB(g))
sw = lambda t, d=0.32, g=-29: place(scan(d), t, gain=dB(g))
imp = lambda t, g=-14: place(impact(), t, gain=dB(g))
wh = lambda t_land, d=0.32, g=-27: place(whoosh(d), t_land - d * 0.7, gain=dB(g))
# hook: Rx label lands, underrated brackets
wh(1.06, 0.3); place(thud(0.8), 1.06, gain=dB(-21)); tk(1.96, -25)
# 1 stack builder
hit(5.45, -20)
for t in (7.00, 8.14, 9.46): tk(t, -26)
place(thud(1.0), 10.70, gain=dB(-19)); wh(12.10, 0.4, -28)
# 2 timeline full-screen
wh(13.75, 0.45, -24); hit(14.74, -19)
for t in (17.88, 21.42, 24.52): tk(t, -26)
place(ticker(0.9), 24.70, gain=dB(-31)); tk(25.60, -22)
imp(26.84, -13)
# 3 vessel scan
hit(27.30, -18); sw(27.40, 0.9, -30); place(thud(1.0), 29.18, gain=dB(-18)); wh(30.6, 0.6, -28)
for k in range(8): tk(31.64 + k * 0.11, -33)
# 4 split delivery
wh(33.70, 0.4, -24); sw(35.14, 0.9, -31)
for t in (38.06, 39.34, 40.42): tk(t, -27)
place(thud(0.9), 43.96, gain=dB(-20))
# 5 graph
hit(45.60, -18)
for t in (47.46, 48.42, 48.70): tk(t, -26)
tk(49.94, -24); tk(50.42, -24); place(thud(1.1), 51.34, gain=dB(-20)); sw(53.30, 1.3, -31); tk(55.98, -26); tk(56.62, -26)
# 6 compare
wh(58.62, 0.32, -25); place(thud(1.2), 59.18, gain=dB(-17)); wh(61.08, 0.32, -25); tk(61.32, -24)
tk(62.58, -27); tk(63.62, -27)
# 7 stat
hit(65.30, -20)
for i in range(12): tk(67.40 + i * 0.07, -34)
place(riser(0.6), 68.42, gain=dB(-24)); imp(69.02, -13)
for t in (70.42, 71.68, 72.64): tk(t, -26)
# 8 lab document
wh(74.15, 0.35, -24); place(thud(0.8), 74.20, gain=dB(-21)); sw(74.86, 0.5, -31); tk(75.66, -24)
for t in (76.96, 77.20, 77.44): tk(t, -28)
# 9 callback
hit(78.35, -20); place(thud(1.0), 81.12, gain=dB(-20)); wh(83.9, 0.5, -27); wh(84.6, 0.5, -27); imp(85.22, -15)
# CTA
hit(86.25, -19); place(thud(1.3), 89.90, gain=dB(-16))
for t in (91.78, 92.74, 93.58, 95.12, 97.84): tk(t, -28)
out = np.stack([L, R], 1); pk = np.max(np.abs(out)); print('sfx peak dBFS', round(20 * np.log10(pk), 2))
w = wave.open(sys.argv[1], 'wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
w.writeframes((np.clip(out, -1, 1) * 32767).astype(np.int16).tobytes()); w.close()
