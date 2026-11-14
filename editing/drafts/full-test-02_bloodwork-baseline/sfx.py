# SFX bed for full test 02. usage: python3 sfx.py <workdir> <fontdir> <out.wav>
import sys, importlib.util, os, wave
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); out = sys.argv[3]
sys.argv = ['r', sys.argv[1], sys.argv[2]]
spec = importlib.util.spec_from_file_location('r', HERE + '/render.py'); r = importlib.util.module_from_spec(spec); spec.loader.exec_module(r)
C, DUR = r.C, r.DUR
SR = 48000; n = int(SR * (DUR + 0.5)); L = np.zeros(n); R = np.zeros(n); rng = np.random.default_rng(11)
def lp(x, a):
    y = np.zeros_like(x); acc = 0.0
    for k in range(len(x)): acc += a * (x[k] - acc); y[k] = acc
    return y
def norm(y): return y / (np.max(np.abs(y)) + 1e-9)
def whoosh(d):
    m = int(SR * d); t = np.arange(m) / SR; nz = rng.standard_normal(m)
    cut = 0.02 + 0.22 * np.sin(np.pi * np.clip(t / d, 0, 1)) ** 2; y = np.zeros(m); acc = 0
    for k in range(m): acc += cut[k] * (nz[k] - acc); y[k] = acc
    return norm(y * np.sin(np.pi * np.clip(t / d, 0, 1) ** 0.7) ** 2)
def thud(weight=1.0):
    m = int(SR * 0.35); t = np.arange(m) / SR; fr = 55 + 60 * np.exp(-t * 28)
    return norm(np.sin(2 * np.pi * np.cumsum(fr) / SR) * np.exp(-t * (14 / weight)) + lp(rng.standard_normal(m), 0.25) * np.exp(-t * 160) * 0.5)
def tick():
    m = int(SR * 0.05); t = np.arange(m) / SR
    return norm(np.sin(2 * np.pi * 2400 * t) * np.exp(-t * 140) + 0.4 * np.sin(2 * np.pi * 4100 * t) * np.exp(-t * 220))
def impact():
    m = int(SR * 0.7); t = np.arange(m) / SR; fr = 46 + 90 * np.exp(-t * 30)
    return norm(np.sin(2 * np.pi * np.cumsum(fr) / SR) * np.exp(-t * 6) + 0.5 * lp(rng.standard_normal(m), 0.6) * np.exp(-t * 45))
def sweep(d, f0=300, f1=2600):
    m = int(SR * d); t = np.arange(m) / SR; fr = f0 * (f1 / f0) ** (t / d)
    return norm(np.sin(2 * np.pi * np.cumsum(fr) / SR) * np.sin(np.pi * t / d) ** 2 * 0.6 + lp(rng.standard_normal(m), 0.3) * np.sin(np.pi * t / d) * 0.3)
def riser(d):
    m = int(SR * d); t = np.arange(m) / SR; fr = 80 + 160 * (t / d) ** 2
    return norm(np.sin(2 * np.pi * np.cumsum(fr) / SR) * (t / d) ** 1.5)
def place(sig, t, g=1.0, pan=0.0):
    i = int(t * SR); s = sig[:max(0, n - i)] * g
    L[i:i + len(s)] += s * (1 - max(0, pan)); R[i:i + len(s)] += s * (1 + min(0, pan))
place(impact(), 0.0, 0.35)
place(thud(0.8), C['protocol'], 0.25)
place(whoosh(0.35), C['conf_in'] - 0.2, 0.18, -0.4)
place(tick(), C['confidence'] + 0.1, 0.2)
place(sweep(0.4), C['because'] - 0.1, 0.16)
for k in ['bloods', 'aromatize', 'testo', 'lipids', 'hct', 'liver', 'kidney']: place(tick(), C[k], 0.14, -0.5)
place(sweep(1.4, 1800, 200), C['something'], 0.16)
place(thud(1.2), C['surface'] + 0.3, 0.3)
place(whoosh(0.4), C['essentially'] - 0.3, 0.2, -0.4)
place(impact(), C['recommendation'] + 0.25, 0.32)
place(tick(), C['zero'], 0.22)
place(whoosh(0.5), C['even'] - 0.35, 0.22)
place(thud(), C['most'], 0.2)
place(thud(1.4), C['you1'] + 0.2, 0.3)
place(impact(), C['ten'] + 0.1, 0.38)
place(whoosh(0.45), C['two'] - 0.3, 0.2)
for k in ['age', 'weight', 'training', 'input']: place(tick(), C[k], 0.15)
place(impact(), C['crashes'] + 0.2, 0.4)
place(whoosh(0.5), C['why'] - 0.3, 0.22, 0.4)
for k in ['enzyme', 'receptor', 'lipid', 'liver2', 'cardio', 'androgen']: place(tick(), C[k], 0.13, 0.5)
place(thud(0.8), C['compound'] + 0.05, 0.22)
place(impact(), C['person'] + 0.05, 0.38)
place(whoosh(0.35), C['and_'] - 0.25, 0.18)
for k in range(10): place(tick(), C['five'] - 0.1 + k * 0.08, 0.06 + 0.01 * k)
place(thud(1.3), C['five'] + 0.65, 0.35)
place(sweep(0.9, 400, 1400), C['pattern'], 0.12)
place(riser(1.6), C['flying'] - 0.2, 0.16)
place(impact(), C['time'] + 0.15, 0.36)
for k in range(3): place(tick(), C['something2'] + 0.5 + 0.25 * k, 0.16)
place(whoosh(0.4), C['run'] - 1.7, 0.18)
place(thud(1.2), C['drawn'] + 0.1, 0.32)
place(tick(), C['anything'], 0.2); place(tick(), C['anything'] + 0.25, 0.15)
place(whoosh(0.5), C['blood3'] - 0.6, 0.22)
place(sweep(1.4, 250, 900), C['road'] - 0.3, 0.12)
place(thud(0.9), C['lived'] - 0.1, 0.22)
place(whoosh(0.45), C['that_'] - 0.3, 0.2)
for k in range(6): place(tick(), C['markers'] + 0.12 * k, 0.12)
place(impact(), C['comment'], 0.42)
y = np.stack([L, R], 1); y = np.clip(y, -1, 1)
o = wave.open(out, 'wb'); o.setnchannels(2); o.setsampwidth(2); o.setframerate(SR); o.writeframes((y * 32767).astype(np.int16).tobytes()); o.close(); print('sfx ok', DUR)
