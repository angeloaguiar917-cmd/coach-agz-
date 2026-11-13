# SFX bed for reel 02 (edited timeline). Same synthesized clinical palette as the saved full-test setup.
# Usage: python3 sfx.py <workdir>  -> <workdir>/work/sfx.wav
import numpy as np, wave, json, sys
S = sys.argv[1]; WK = S + '/work/'
WORDS = json.load(open(WK + 'words_final.json')); TR = json.load(open(WK + 'trim.json'))
DUR = sum(b - a for a, b in TR['keep'])
CUTS = [a - sum(b2 - a2 for a2, b2 in TR['remove'] if a2 < a) for a, b in TR['remove']]
w = lambda i: WORDS[i]['s']
SR = 48000; n = int(SR * (DUR + 0.5)); L = np.zeros(n); R = np.zeros(n)
rng = np.random.default_rng(7)
def place(sig, t, pan=0.0, gain=1.0, end_on=False):
    if end_on: t = t - len(sig) / SR          # whooshes arrive on the landing
    i = max(0, int(t * SR)); s = sig[:max(0, n - i)] * gain
    L[i:i + len(s)] += s * (1 - max(0, pan)); R[i:i + len(s)] += s * (1 + min(0, pan))
def lp(x, a):
    y = np.zeros_like(x); acc = 0
    for k in range(len(x)): acc += a * (x[k] - acc); y[k] = acc
    return y
def whoosh(d):
    m = int(SR * d); t = np.arange(m) / SR; nz = rng.standard_normal(m)
    cut = 0.02 + 0.25 * np.sin(np.pi * np.clip(t / d, 0, 1)) ** 2; y = np.zeros(m); acc = 0
    for k in range(m): acc += cut[k] * (nz[k] - acc); y[k] = acc
    env = np.sin(np.pi * np.clip(t / d, 0, 1) ** 0.7) ** 2; return y * env / np.max(np.abs(y * env))
def thud(weight=1.0):
    m = int(SR * 0.35); t = np.arange(m) / SR; f = 55 + 60 * np.exp(-t * 28)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * (14 / weight))
    click = lp(rng.standard_normal(m), 0.25) * np.exp(-t * 160) * 0.5; y = body + click; return y / np.max(np.abs(y))
def tick():
    m = int(SR * 0.05); t = np.arange(m) / SR
    y = np.sin(2 * np.pi * 2400 * t) * np.exp(-t * 140) + 0.4 * np.sin(2 * np.pi * 4100 * t) * np.exp(-t * 220); return y / np.max(np.abs(y))
def impact():
    m = int(SR * 0.6); t = np.arange(m) / SR; f = 48 + 90 * np.exp(-t * 30); body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 7)
    crack = lp(rng.standard_normal(m), 0.6) * np.exp(-t * 45); y = body + 0.55 * crack; return y / np.max(np.abs(y))
def scan(d):
    m = int(SR * d); t = np.arange(m) / SR; nz = rng.standard_normal(m); cut = 0.05 + 0.35 * (t / d); y = np.zeros(m); acc = 0
    for k in range(m): acc += cut[k] * (nz[k] - acc); y[k] = acc
    y = y - lp(y, 0.08) + 0.15 * np.sin(2 * np.pi * (900 + 1400 * t / d) * t)
    env = np.minimum(1, t / 0.03) * np.minimum(1, (d - t) / 0.05); return y * env / np.max(np.abs(y * env))
def riser(d):   # meter fill: rising filtered tone
    m = int(SR * d); t = np.arange(m) / SR; f = 180 + 520 * (t / d) ** 1.5
    y = np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.6 + 0.4 * lp(rng.standard_normal(m), 0.05)
    env = np.minimum(1, t / 0.05) * np.minimum(1, (d - t) / 0.04); return y * env / np.max(np.abs(y * env))
dB = lambda x: 10 ** (x / 20)
hit = lambda t, g=-17: place(thud(1.4), t, gain=dB(g))
tk = lambda t, g=-28: place(tick(), t, gain=dB(g))
sw = lambda t, d=0.32, g=-29: place(scan(d), t, gain=dB(g))
wh = lambda t, d=0.3, g=-26: place(whoosh(d), t, gain=dB(g), end_on=True)

place(thud(1.0), w(4), gain=dB(-24))                          # push-in on "body fat"
tk(w(13) - 0.1, -30); place(riser(0.85), w(15), gain=dB(-30)); tk(w(16) + 0.25, -26)   # E2 meter
wh(6.22, 0.32); hit(6.22, -18)                                # split screen lands
sw(w(25), w(27) + 0.3 - w(25)); tk(w(27), -27)                 # scan + aromatase lights
tk(w(32), -29); tk(w(34), -25)                                # T, then E2
wh(CUTS[0] + 0.30, 0.3); hit(CUTS[0] + 0.30, -19)              # into the face bubble / graph
sw(w(37), 0.85, -31); tk(w(42), -29); tk(w(45), -28); tk(w(46) + 0.25, -25)
wh(CUTS[2] + 0.28, 0.26, -28)                                 # back to full face
tk(w(48), -30)
for i in (56, 57, 62): place(thud(0.8), w(i), gain=dB(-22)); tk(w(i) + 0.14, -31)
hit(w(64) + 0.2, -19); tk(w(67), -30); tk(w(68), -26); tk(w(73), -30)
for j in range(5): tk(w(75) + j * 0.06, -33)
place(whoosh(0.55), w(77), gain=dB(-30)); tk(w(77) + 0.5, -26)
wh(w(89) + 0.21, 0.26, -27)                                   # Rx bottle slides up
place(impact(), w(92), gain=dB(-14))                          # X stamp on "AI"
wh(w(93) + 0.19, 0.24, -27)
for k in range(5): tk(w(97) + k * 0.07, -31)
tk(w(97), -25)
hit(CUTS[5], -17)                                             # COMMENT pill
tk(w(102), -27); tk(w(102) + 0.07, -30); tk(w(103), -24)      # typing "E2", send
wh(w(105) - 0.05 + 0.42, 0.4, -27)                            # doc flies over
for k in range(5): tk(w(108) + k * 0.28, -33)
place(thud(1.2), w(119), gain=dB(-17))                        # FREE stamp
out = np.stack([L, R], 1)[:int(SR * DUR)]; pk = np.max(np.abs(out)); print('sfx peak dBFS', 20 * np.log10(pk))
wv = wave.open(WK + 'sfx.wav', 'wb'); wv.setnchannels(2); wv.setsampwidth(2); wv.setframerate(SR)
wv.writeframes((np.clip(out, -1, 1) * 32767).astype(np.int16).tobytes()); wv.close()
