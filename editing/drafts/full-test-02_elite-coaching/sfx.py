# clinical SFX bed (synth): sub hits, scan sweeps, digital ticks, one heavy impact per beat
import sys, numpy as np, wave
S = sys.argv[1]
src = open(S + '/render.py').read().split("if __name__ == '__main__':")[0]
sys.argv = ['x', S]; exec(src)
SR = 48000; n = int(SR * (DUR + 0.5)); L = np.zeros(n); R = np.zeros(n)
rng = np.random.default_rng(11)
def place(sig, t, pan=0.0, gain=1.0):
    i = int(t * SR)
    if i >= n or i < 0: return
    s = sig[:n - i] * gain
    L[i:i + len(s)] += s * (1 - max(0, pan)); R[i:i + len(s)] += s * (1 + min(0, pan))
def lp(x, a):
    y = np.zeros_like(x); acc = 0
    for k in range(len(x)): acc += a * (x[k] - acc); y[k] = acc
    return y
def thud(weight=1.0):
    m = int(SR * 0.35); t = np.arange(m) / SR
    fr = 55 + 60 * np.exp(-t * 28); body = np.sin(2 * np.pi * np.cumsum(fr) / SR) * np.exp(-t * (14 / weight))
    click = lp(rng.standard_normal(m), 0.25) * np.exp(-t * 160) * 0.5
    y = body + click; return y / np.max(np.abs(y))
def tick(f1=2400):
    m = int(SR * 0.05); t = np.arange(m) / SR
    y = np.sin(2 * np.pi * f1 * t) * np.exp(-t * 140) + 0.4 * np.sin(2 * np.pi * f1 * 1.7 * t) * np.exp(-t * 220)
    return y / np.max(np.abs(y))
def impact():
    m = int(SR * 0.6); t = np.arange(m) / SR
    fr = 48 + 90 * np.exp(-t * 30); body = np.sin(2 * np.pi * np.cumsum(fr) / SR) * np.exp(-t * 7)
    crack = lp(rng.standard_normal(m), 0.6) * np.exp(-t * 45)
    y = body + 0.55 * crack; return y / np.max(np.abs(y))
def scan(d):
    m = int(SR * d); t = np.arange(m) / SR; nz = rng.standard_normal(m)
    cut = 0.05 + 0.35 * (t / d); y = np.zeros(m); acc = 0
    for k in range(m): acc += cut[k] * (nz[k] - acc); y[k] = acc
    y = y - lp(y, 0.08) + 0.15 * np.sin(2 * np.pi * (900 + 1400 * t / d) * t)
    env = np.minimum(1, t / 0.03) * np.minimum(1, (d - t) / 0.05)
    return y * env / np.max(np.abs(y * env))
def whoosh(d):
    m = int(SR * d); t = np.arange(m) / SR; nz = rng.standard_normal(m)
    cut = 0.02 + 0.25 * np.sin(np.pi * np.clip(t / d, 0, 1)) ** 2
    y = np.zeros(m); acc = 0
    for k in range(m): acc += cut[k] * (nz[k] - acc); y[k] = acc
    env = np.sin(np.pi * np.clip(t / d, 0, 1) ** 0.7) ** 2
    return y * env / np.max(np.abs(y * env))
dB = lambda x: 10 ** (x / 20)
hit = lambda t, g=-19: place(thud(1.3), t, gain=dB(g))
sw = lambda t, d=0.32, g=-30: place(scan(d), t, gain=dB(g))
tk = lambda t, g=-30, fr=2400: place(tick(fr), t, gain=dB(g))
imp = lambda t, g=-16: place(impact(), t, gain=dB(g))
wh = lambda t, d=0.4, g=-28: place(whoosh(d), t - d * 0.7, gain=dB(g))
T = TM
# tracker
sw(SC[0][0], 0.28); hit(T['wk'] + 0.02, -20)
for i in range(7): tk(T['dly'] + i * 0.07, -34, 2600)
sw(T['bp'], 1.1, -33)
# form
sw(SC[1][0], 0.28); [tk(x, -30) for x in (T['feel'], T['sleep'], T['eat'])]
# suspect
sw(SC[2][0], 0.3); imp(T['comp'], -18)
# radar
hit(SC[3][0] + 0.05, -21); [tk(K(w, 0, T['blood']), -31, 3000) for w in ('mood', 'sleep', 'cognition', 'focus', 'relationships')]
# range
sw(T['ref'], 0.5, -31); hit(T['sick'] + 0.02, -17); tk(T['optimal'], -29)
# gauges
for x in (T['side'], T['growth'], T['cresp']): sw(x, 0.55, -33)
# mixer
tk(T['rx'], -30); tk(T['anc'], -30); tk(T['you'], -28, 3200)
# pip / chart
wh(PIP[0] + 0.3, 0.45); tk(T['add'], -28); tk(T['und'], -29, 3200)
# simplify
wh(T['simp'] + 0.6, 0.6, -30)
# split docs
wh(SPLIT[0] + 0.3, 0.45); hit(T['sum'] + 0.25, -21); hit(T['deep'] + 0.25, -22)
# life
sw(T['rest2'], 1.0, -33); [tk(x, -31) for x in (T['lead'], T['kids'], T['wife'])]
# CTA
hit(T['com'], -20); imp(T['elite'], -15); tk(T['prof'], -28, 3200); hit(T['proto'] + 0.15, -18)
out = np.stack([L, R], 1); pk = np.max(np.abs(out)); print('sfx peak dBFS', 20 * np.log10(pk + 1e-9))
w = wave.open(S + '/sfx.wav', 'wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
w.writeframes((np.clip(out, -1, 1) * 32767).astype(np.int16).tobytes()); w.close()
