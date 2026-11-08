# Clinical SFX bed synced to render.py's scene table and word cues.  usage: python3 sfx.py <scratch> <out.wav>
import sys, wave
import numpy as np
S, OUT = sys.argv[1], sys.argv[2]
src = open(__file__.replace('sfx.py', 'render.py')).read().split("if __name__ == '__main__':")[0]
_a = sys.argv; sys.argv = ['render.py', S]; G = {'__file__': __file__.replace('sfx.py', 'render.py')}; exec(src, G); sys.argv = _a
C, SCENES, DUR = G['C'], G['SCENES'], G['DUR']
SR = 48000; n = int(SR * (DUR + 1)); L = np.zeros(n); R = np.zeros(n); rng = np.random.default_rng(7)
def lp(x, a):
    y = np.zeros_like(x); acc = 0.0
    for k in range(len(x)): acc += a * (x[k] - acc); y[k] = acc
    return y
def norm(y): return y / (np.max(np.abs(y)) + 1e-9)
def thud(weight=1.0):
    m = int(SR * 0.35); t = np.arange(m) / SR; fr = 55 + 60 * np.exp(-t * 28)
    return norm(np.sin(2 * np.pi * np.cumsum(fr) / SR) * np.exp(-t * (14 / weight)) + lp(rng.standard_normal(m), 0.25) * np.exp(-t * 160) * 0.5)
def tick():
    m = int(SR * 0.05); t = np.arange(m) / SR
    return norm(np.sin(2 * np.pi * 2400 * t) * np.exp(-t * 140) + 0.4 * np.sin(2 * np.pi * 4100 * t) * np.exp(-t * 220))
def impact():
    m = int(SR * 0.6); t = np.arange(m) / SR; fr = 48 + 90 * np.exp(-t * 30)
    return norm(np.sin(2 * np.pi * np.cumsum(fr) / SR) * np.exp(-t * 7) + 0.55 * lp(rng.standard_normal(m), 0.6) * np.exp(-t * 45))
def scan(d):
    m = int(SR * d); t = np.arange(m) / SR; nz = rng.standard_normal(m); cut = 0.05 + 0.35 * (t / d); y = np.zeros(m); acc = 0.0
    for k in range(m): acc += cut[k] * (nz[k] - acc); y[k] = acc
    y = y - lp(y, 0.08) + 0.15 * np.sin(2 * np.pi * (900 + 1400 * t / d) * t)
    return norm(y * np.minimum(1, t / 0.03) * np.minimum(1, (d - t) / 0.05))
def whoosh(d):
    m = int(SR * d); t = np.arange(m) / SR; nz = rng.standard_normal(m); cut = 0.02 + 0.25 * np.sin(np.pi * np.clip(t / d, 0, 1)) ** 2
    y = np.zeros(m); acc = 0.0
    for k in range(m): acc += cut[k] * (nz[k] - acc); y[k] = acc
    return norm(y * np.sin(np.pi * np.clip(t / d, 0, 1) ** 0.7) ** 2)
TH, TK, IM, SC3, SC2, WH = thud(1.4), tick(), impact(), scan(0.32), scan(0.2), whoosh(0.42)
dB = lambda x: 10 ** (x / 20)
def place(sig, t, g, pan=0.0):
    i = int(t * SR)
    if i < 0 or i >= n: return
    s = sig[:n - i] * dB(g); L[i:i + len(s)] += s * (1 - max(0, pan)); R[i:i + len(s)] += s * (1 + min(0, pan))
ev = []
for s in SCENES:
    k, t0 = s['kind'], s['t0']
    if k == 'A': ev += [(SC3, t0, -29), (TH, t0 + 0.05, -18)]
    elif k == 'M': ev += [(SC3, t0, -29), (TH, t0 + 0.1, -19)]
    elif k == 'B': ev += [(WH, t0, -27), (TH, t0 + 0.4, -18)]
    elif k == 'T': ev += [(SC2, t0, -30), (TK, t0 + 0.2, -30)]
    elif k == 'C': ev += [(TK, t0, -28), (thud(0.8), t0 + 0.08, -23)]
    elif k == 'D': ev += [(IM, t0, -15), (TH, s['t1'], -20)]
for key, g in [('untrained', -30), ('average', -30), ('locked', -28), ('a3', -24), ('a6', -24), ('a12', -24), ('n20', -22), ('240', -28), ('pct', -28), ('40', -26),
               ('10y', -30), ('linear', -28), ('risk', -26), ('n2030', -26), ('90', -28), ('fifth', -24), ('social', -28)]:
    ev.append((TK if g < -27 else TH, C[key], g))
for key in ['training', 'nutrition', 'protocols', 'side', 'blood', 'client']: ev.append((TK, C[key], -32))
for key in ['fast', 'keeping', 'health']: ev.append((thud(0.7), C[key] + 0.18, -24))
ev += [(IM, C['Not'], -15), (TH, C['Comment'] + 0.14, -17)]
for sig, t, g in ev: place(sig, t, g)
out = np.stack([L, R], 1)[:int(SR * DUR)]
print('events', len(ev), 'peak dBFS', round(20 * np.log10(np.max(np.abs(out)) + 1e-9), 1))
with wave.open(OUT, 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((np.clip(out, -1, 1) * 32767).astype(np.int16).tobytes())
