# Clinical SFX bed for full test 02. All cue times are SOURCE seconds; mapped through the trims.
# usage: python3 sfx.py <out.wav>
import sys, wave, numpy as np
SR = 48000
KEEP = [(0, 406), (412, 1994), (2006, 2418)]
DUR = sum(b-a for a, b in KEEP)/30; n = int(SR*DUR)
L = np.zeros(n); R = np.zeros(n); rng = np.random.default_rng(7)
def mp(t):
    acc = 0
    for a, b in KEEP:
        if a/30 <= t < b/30: return acc + t - a/30
        acc += (b-a)/30
    return None
def place(sig, t, gain=1.0, pan=0.0):
    t = mp(t)
    if t is None: print('cue dropped (inside cut)'); return
    i = int(t*SR); s = sig[:max(0, n-i)]*gain
    L[i:i+len(s)] += s*(1-max(0, pan)); R[i:i+len(s)] += s*(1+min(0, pan))
def lp(x, a):
    y = np.zeros_like(x); acc = 0
    for k in range(len(x)): acc += a*(x[k]-acc); y[k] = acc
    return y
def norm(y): return y/np.max(np.abs(y))
def thud(weight=1.0):
    m = int(SR*0.35); t = np.arange(m)/SR; fr = 55+60*np.exp(-t*28)
    return norm(np.sin(2*np.pi*np.cumsum(fr)/SR)*np.exp(-t*(14/weight)) + lp(rng.standard_normal(m), 0.25)*np.exp(-t*160)*0.5)
def tick():
    m = int(SR*0.05); t = np.arange(m)/SR
    return norm(np.sin(2*np.pi*2400*t)*np.exp(-t*140)+0.4*np.sin(2*np.pi*4100*t)*np.exp(-t*220))
def impact():
    m = int(SR*0.6); t = np.arange(m)/SR; fr = 48+90*np.exp(-t*30)
    return norm(np.sin(2*np.pi*np.cumsum(fr)/SR)*np.exp(-t*7) + 0.55*lp(rng.standard_normal(m), 0.6)*np.exp(-t*45))
def sweep(d, up=True):
    m = int(SR*d); t = np.arange(m)/SR; nz = rng.standard_normal(m)
    cut = 0.05+0.35*(t/d if up else 1-t/d); y = np.zeros(m); acc = 0
    for k in range(m): acc += cut[k]*(nz[k]-acc); y[k] = acc
    y = y-lp(y, 0.08); env = np.minimum(1, t/0.03)*np.minimum(1, (d-t)/0.05)
    return norm(y*env)
def switch():
    m = int(SR*0.08); t = np.arange(m)/SR
    return norm(lp(rng.standard_normal(m), 0.5)*np.exp(-t*90) + 0.6*np.sin(2*np.pi*1400*t)*np.exp(-t*120))
dB = lambda x: 10**(x/20)
hit = lambda t, g=-17: place(thud(1.4), t, dB(g))
tk = lambda t, g=-29: place(tick(), t, dB(g))
imp = lambda t, g=-15: place(impact(), t, dB(g))
sw = lambda t, d=0.32, g=-29: place(sweep(d), t-d*0.8, dB(g))

tk(6.0, -31)                                   # band handoff
for t in (13.80, 24.48, 34.94, 45.18): sw(t, 0.28, -30); hit(t+0.18, -20)   # chapter blocks land
sw(52.66, 0.22, -27); imp(52.86, -17)          # VS slam
tk(53.26, -27)                                 # "?"
place(sweep(0.16, False), 55.40, dB(-26)); imp(55.84, -15)   # strike + WRONG QUESTION
sw(56.20, 0.36, -28)                           # layout split
for t in (57.62, 59.32): tk(t, -28)            # rows in
for t in (58.50, 60.10): place(thud(0.8), t, dB(-24))   # X on result
hit(61.44, -21)                                # compound chip
place(switch(), 63.18, dB(-22)); place(switch(), 63.30, dB(-23))   # toggles flip on
imp(63.44, -18)                                # result bars rise
sw(64.40, 0.36, -28)                           # layout inverse
for t in (64.94, 65.74, 67.88): tk(t, -28)     # dials appear
for t in (70.16, 70.92, 72.08): place(thud(1.0), t, dB(-20))   # needles hit red
sw(72.40, 0.36, -29)
hit(73.66, -20); tk(73.90, -28); tk(74.94, -28)
imp(76.72, -16)                                # COMMENT pill
tk(78.66, -24); tk(78.74, -27)                 # notification
out = np.stack([L, R], 1); print('sfx peak dBFS', 20*np.log10(np.max(np.abs(out))))
w = wave.open(sys.argv[1], 'wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
w.writeframes((np.clip(out, -1, 1)*32767).astype(np.int16).tobytes()); w.close()
