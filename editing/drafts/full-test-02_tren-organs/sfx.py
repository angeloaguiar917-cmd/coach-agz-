# SFX bed for full test 02 (clinical: sub hits, scan sweeps, digital ticks, one heavy impact per beat)
# usage: python3 sfx.py <workdir>  -> writes <workdir>/sfx.wav (48 kHz stereo, length = cut + hold)
import sys, json, wave, numpy as np
T = sys.argv[1].rstrip('/') + '/'
WORDS = json.load(open(T + 'words_final.json')); C = json.load(open(T + 'cut.json'))
SR = 48000; DUR = C['dur'] + 0.5; n = int(SR * DUR); L = np.zeros(n); R = np.zeros(n)
rng = np.random.default_rng(11)
def wt(word, after=0.0, nth=0):
    k = 0
    for x in WORDS:
        if x['s'] >= after - 1e-6 and x['w'].lower().strip('.,?!') == word.lower():
            if k == nth: return x['s']
            k += 1
    raise KeyError(word)
def place(sig, t, pan=0.0, gain=1.0):
    i = int(t * SR); s = sig[:max(0, n - i)] * gain
    L[i:i + len(s)] += s * (1 - max(0, pan)); R[i:i + len(s)] += s * (1 + min(0, pan))
def lp(x, a):
    y = np.zeros_like(x); acc = 0.0
    for k in range(len(x)): acc += a * (x[k] - acc); y[k] = acc
    return y
def thud(weight=1.0):
    m = int(SR * 0.35); t = np.arange(m) / SR; fr = 55 + 60 * np.exp(-t * 28)
    y = np.sin(2 * np.pi * np.cumsum(fr) / SR) * np.exp(-t * (14 / weight)) + lp(rng.standard_normal(m), 0.25) * np.exp(-t * 160) * 0.5
    return y / np.max(np.abs(y))
def tick(f1=2400):
    m = int(SR * 0.05); t = np.arange(m) / SR
    y = np.sin(2 * np.pi * f1 * t) * np.exp(-t * 140) + 0.4 * np.sin(2 * np.pi * f1 * 1.7 * t) * np.exp(-t * 220)
    return y / np.max(np.abs(y))
def impact():
    m = int(SR * 0.6); t = np.arange(m) / SR; fr = 48 + 90 * np.exp(-t * 30)
    y = np.sin(2 * np.pi * np.cumsum(fr) / SR) * np.exp(-t * 7) + 0.55 * lp(rng.standard_normal(m), 0.6) * np.exp(-t * 45)
    return y / np.max(np.abs(y))
def scan(d):
    m = int(SR * d); t = np.arange(m) / SR; nz = rng.standard_normal(m); cut = 0.05 + 0.35 * (t / d); y = np.zeros(m); acc = 0.0
    for k in range(m): acc += cut[k] * (nz[k] - acc); y[k] = acc
    y = y - lp(y, 0.08) + 0.15 * np.sin(2 * np.pi * (900 + 1400 * t / d) * t)
    env = np.minimum(1, t / 0.03) * np.minimum(1, (d - t) / 0.05); return y * env / np.max(np.abs(y * env))
def whoosh(d):
    m = int(SR * d); t = np.arange(m) / SR; nz = rng.standard_normal(m); cut = 0.02 + 0.25 * np.sin(np.pi * np.clip(t / d, 0, 1)) ** 2
    y = np.zeros(m); acc = 0.0
    for k in range(m): acc += cut[k] * (nz[k] - acc); y[k] = acc
    env = np.sin(np.pi * np.clip(t / d, 0, 1) ** 0.7) ** 2; return y * env / np.max(np.abs(y * env))
def paper(d):
    m = int(SR * d); t = np.arange(m) / SR; nz = rng.standard_normal(m); hp = nz - lp(nz, 0.15)
    env = np.sin(np.pi * np.clip(t / d, 0, 1)) ** 1.5; return hp * env / np.max(np.abs(hp * env))
def beep(f=1000, d=0.09):
    m = int(SR * d); t = np.arange(m) / SR; y = np.sin(2 * np.pi * f * t) * np.minimum(1, t / 0.004) * np.minimum(1, (d - t) / 0.01); return y
def riser(d):
    m = int(SR * d); t = np.arange(m) / SR; fr = 120 * (1 + 5 * (t / d) ** 2)
    y = np.sign(np.sin(2 * np.pi * np.cumsum(fr) / SR)) * 0.3 + lp(rng.standard_normal(m), 0.2) * 0.5
    y = lp(y, 0.3) * (t / d) ** 1.5; return y / np.max(np.abs(y))
def crackle(d):
    m = int(SR * d); y = rng.standard_normal(m) * (rng.random(m) < 0.02) * 1.0; y = y - lp(y, 0.3)
    return y / max(1e-9, np.max(np.abs(y)))
dB = lambda x: 10 ** (x / 20)
hit = lambda t, g=-17: place(thud(1.4), t, gain=dB(g))
tk = lambda t, g=-29, f1=2400: place(tick(f1), t, gain=dB(g))
sw = lambda t, d=0.32, g=-29: place(scan(d), t, gain=dB(g))
wh = lambda t_land, d=0.32, g=-28: place(whoosh(d), max(0, t_land - d * 0.7), gain=dB(g))
imp = lambda t, g=-14: place(impact(), t, gain=dB(g))
# --- S0/S1 hook + rail
place(thud(1.8), 0.0, gain=dB(-22))
for k, t in enumerate((5.08, 5.20, 5.32)): tk(t, -30, 2000 + 300 * k)
place(beep(520, 0.12), wt('third', 6) , gain=dB(-30)); hit(wt('mistake', 9), -19)
tk(wt('number', 9.9), -26)
# --- S2 receptor -> graph
wh(13.55, 0.3); sw(13.6, 0.5, -31); tk(wt('potent', 13), -30)
hit(wt('agonist', 15), -18); sw(wt('exposure', 16.9), 0.25, -30)
sw(17.58, 0.3, -31); tk(wt('guarantee', 17.5), -31); tk(wt('muscle', 19.8) - 0.3, -26, 1800)
# --- S3 vitals drain
for wd in ('recovery', 'appetite', 'sleep', 'moods'): place(scan(0.3)[::-1].copy(), wt(wd, 20.5), gain=dB(-32))
hit(wt('shit', 24), -20)
# --- S4/S5
imp(wt('non-negotiable', 27), -15)
place(paper(0.35), 29.66, gain=dB(-30))
for wd, a in (('blood', 29.8), ('apob', 30), ('cholesterol', 31), ('hematocrit', 32), ('cardiac', 33)): tk(wt(wd, a), -29, 3000)
hit(wt('overall', 34), -17)
# --- S6 cardio
sw(wt('arteries', 37) - 0.08, 0.6, -30)
tb = wt("heart's", 39); tx = wt('explode', 40)
bt = tb
while bt < tx: place(beep(1000, 0.07), bt, gain=dB(-33)); bt += 1 / 1.6
imp(tx, -13); place(beep(1000, 0.6) * np.linspace(1, 0.2, int(SR * 0.6)), tx + 0.05, gain=dB(-31))
# --- S7 supplements
for i in range(5): place(thud(0.6), wt('stop', 41.8) + 0.04 + i * 0.2 + 0.16, gain=dB(-25))
sw(wt('side', 43), 0.4, -30); hit(wt('bro', 44), -19)
# --- S8 symptoms
wh(wt('sleeping', 44) - 0.2, 0.3)
for k in range(6): tk(wt('two', 44.8) + k * 0.11, -32, 2600)
tk(wt('sweating', 46), -28); place(riser(0.9), wt('blood', 47.4) - 0.1, gain=dB(-30)); hit(wt('skyrocketing', 48) + 0.3, -20)
# --- S9 fader
wh(49.15, 0.3, -30)
place(whoosh(0.6), wt('dropping', 50), gain=dB(-29)); tk(wt('dropping', 50) + 0.6, -27, 1500)
place(whoosh(0.6), wt('microdosing', 52), gain=dB(-29)); hit(wt('microdosing', 52) + 0.6, -21); tk(wt('microdosing', 52) + 0.45, -28)
# --- S10 alerts
for wd, a in (('side', 55.6), ('high', 56), ('tren', 57), ('body', 58)): place(beep(1600, 0.06), wt(wd, a), gain=dB(-31)); place(beep(2100, 0.06), wt(wd, a) + 0.07, gain=dB(-33))
imp(wt('done', 60) - 0.08 + 0.14, -15)
# --- S11 fork
tk(wt('smartest', 61), -29); hit(wt('dropping', 62.9), -21); hit(wt('dropping', 64.3), -21); tk(wt('or', 63.9), -31)
# --- S12 cases
wh(wt('witnessed', 65.9), 0.3, -30); place(riser(0.6), wt('rip', 67), gain=dB(-33)); tk(wt('fantastic', 68), -29, 3000)
wh(wt('other', 69), 0.3, -30); place(scan(0.5)[::-1].copy(), wt('bottle', 71), gain=dB(-30))
hit(wt('schizophrenia', 72), -20); hit(wt('paranoia', 74), -20)
# --- S13 amplifier
sw(wt('day', 75.5), 0.35, -31); hit(wt('tren', 76), -21); place(riser(0.6), wt('amplify', 76.5), gain=dB(-30))
place(crackle(0.8), wt('massive', 79), gain=dB(-24)); hit(wt('massive', 79), -18)
# --- S14 bell
sw(wt("there's", 80), 0.5, -30); tk(wt('handle', 80.5), -29, 3000); tk(wt("can't", 81.8), -27, 1500); hit(wt('most', 82.5), -22); tk(wt('microdose', 83.8), -28)
# --- S15 equation
for k in range(3): tk(wt('extraordinary', 86) - 0.1 + 0.08 * k, -31)
imp(wt('nothing', 88.5), -13); place(scan(0.8)[::-1].copy(), wt('destroying', 89.4), gain=dB(-30)); hit(wt('health', 90), -20)
# --- S16 doc + S17 CTA
wh(wt('trenbolone', 92.5), 0.35, -27); tk(wt('protocol', 94), -29); hit(wt('clients', 95.5), -21)
for wd, a in (('microdose', 96.8), ('most', 98.6), ('least', 99.7)): tk(wt(wd, a), -29, 2800)
imp(wt('comment', 100.8) + 0.14, -15)
for k in range(4): tk(wt('tren', 101.3) + k * 0.09, -33, 3400)
tk(wt('below', 101.8), -27, 1800)
out = np.stack([L, R], 1); pk = np.max(np.abs(out)); print('sfx peak dBFS', round(20 * np.log10(pk), 1))
w = wave.open(T + 'sfx.wav', 'wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
w.writeframes((np.clip(out, -1, 1) * 32767).astype(np.int16).tobytes()); w.close()
