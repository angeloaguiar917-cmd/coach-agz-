# Clinical SFX bed for full-02 (sub hits, scan sweeps, digital ticks, one impact per beat), synced to the word cues in render.py
import sys, wave, importlib.util
import numpy as np
S = sys.argv[1].rstrip('/') + '/'
sys.argv = ['render.py', S, 'lib']
spec = importlib.util.spec_from_file_location('rnd', __file__.replace('sfx.py', 'render.py')); R = importlib.util.module_from_spec(spec); spec.loader.exec_module(R)
C = R.C; MODES = R.MODES
SR = 48000; DUR = R.DUR + 0.2; n = int(SR * DUR); L = np.zeros(n); Rr = np.zeros(n)
rng = np.random.default_rng(7)
def place(sig, t, gain=1.0, pan=0.0):
    i = int(max(0, t) * SR); s = sig[:max(0, n - i)] * gain
    L[i:i + len(s)] += s * (1 - max(0, pan)); Rr[i:i + len(s)] += s * (1 + min(0, pan))
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
    m = int(SR * 0.35); t = np.arange(m) / SR; fr = 55 + 60 * np.exp(-t * 28)
    body = np.sin(2 * np.pi * np.cumsum(fr) / SR) * np.exp(-t * (14 / weight)); click = lp(rng.standard_normal(m), 0.25) * np.exp(-t * 160) * 0.5
    y = body + click; return y / np.max(np.abs(y))
def tick():
    m = int(SR * 0.05); t = np.arange(m) / SR
    y = np.sin(2 * np.pi * 2400 * t) * np.exp(-t * 140) + 0.4 * np.sin(2 * np.pi * 4100 * t) * np.exp(-t * 220); return y / np.max(np.abs(y))
def impact():
    m = int(SR * 0.6); t = np.arange(m) / SR; fr = 48 + 90 * np.exp(-t * 30)
    body = np.sin(2 * np.pi * np.cumsum(fr) / SR) * np.exp(-t * 7); crack = lp(rng.standard_normal(m), 0.6) * np.exp(-t * 45)
    y = body + 0.55 * crack; return y / np.max(np.abs(y))
def scan(d):
    m = int(SR * d); t = np.arange(m) / SR; nz = rng.standard_normal(m); cut = 0.05 + 0.35 * (t / d); y = np.zeros(m); acc = 0
    for k in range(m): acc += cut[k] * (nz[k] - acc); y[k] = acc
    y = y - lp(y, 0.08) + 0.15 * np.sin(2 * np.pi * (900 + 1400 * t / d) * t)
    env = np.minimum(1, t / 0.03) * np.minimum(1, (d - t) / 0.05); return y * env / np.max(np.abs(y * env))
dB = lambda x: 10 ** (x / 20)
TH, TK, IM, = thud(1.4), tick(), impact()
hit = lambda t: place(TH, t, dB(-17)); tk = lambda t, g=-29: place(TK, t, dB(g)); imp = lambda t: place(IM, t, dB(-15))
sw = lambda t, d=0.32: place(scan(d), t, dB(-29)); wh = lambda t_land, d=0.34: place(whoosh(d), t_land - d * 0.75, dB(-27))
# layout changes: whoosh lands as the window settles
for a, b, m in MODES:
    if m == 'wipe': continue
    wh(a + 0.30); wh(b + 0.28, 0.28)
tk(C['steroids'], -27)
sw(C['cv1'] - 0.15); imp(C['unprot'])
hit(C['mech'] + 0.1); tk(C['neither'], -26); tk(C['neither'] + 0.12, -28)
tk(C['downreg']); tk(C['hdl1']); sw(C['apob1'], 0.5); tk(C['plaque'])
hit(C['panel'] - 0.05)
for k in range(3): tk(C['panel'] + 0.2 + k * 0.35, -31)
imp(C['already'])
hit(C['fix1']); place(TH, C['eze1'] + 0.1, dB(-19)); tk(C['statin']); tk(C['liver1']); tk(C['burden'], -26)
imp(C['blocks'] + 0.12); tk(C['absorbed']); tk(C['delivered']); sw(C['pulling'], 0.6)
for k in ('lowldl', 'lowapob', 'ratio'): tk(C[k], -28)
hit(C['zero1']); hit(C['zero2']); tk(C['cleanest'], -26)
wh(C['p2'] + 0.12, 0.3); imp(C['p2'] + 0.15); tk(C['bp1'])
hit(C['supra']); sw(C['resist'], 0.45); tk(C['bpclimb'])
sw(C['lvh'], 0.6); tk(C['wall']); tk(C['ef'])
hit(C['fix2']); imp(C['telmi1'])
place(TH, C['at1'] + 0.1, dB(-17)); sw(C['relax'], 0.45); tk(C['pdrop']); tk(C['wallred'])
imp(C['gold'] + 0.08)
for k in ('lowers', 'hr', 'electro', 'blunted'): tk(C[k] + 0.05, -30)
sw(C['regression'], 0.7); imp(C['reversal'] + 0.1)
hit(C['endday']); tk(C['eze3']); tk(C['telmi3']); hit(C['both'] + 0.35)
hit(C['cta']); imp(C['comment'] + 0.05)
out = np.stack([L, Rr], 1); print('sfx peak dBFS', 20 * np.log10(np.max(np.abs(out))))
w = wave.open(S + 'sfx.wav', 'wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
w.writeframes((np.clip(out, -1, 1) * 32767).astype(np.int16).tobytes()); w.close()
