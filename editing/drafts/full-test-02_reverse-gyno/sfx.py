# SFX bed for Reverse GYNO edit: synthesized clinical sounds placed on visual landings (cut timeline)
import sys, json, wave, numpy as np
S = sys.argv[1]
sys.argv = ['render.py', S, 'none']
src = open(__file__.replace('sfx.py', 'render.py')).read().split("if __name__ == '__main__':")[0]
g = {}; exec(src, g); T = g['T']; DUR = g['DUR']; SPL = g['SPLITS']; PIP = g['PIPS']
SR = 48000; n = int(SR * DUR); L = np.zeros(n); R = np.zeros(n); rng = np.random.default_rng(7)
def place(sig, t, gain=1.0, pan=0.0):
    i = int(t * SR); s = sig[:max(0, n - i)] * gain
    L[i:i + len(s)] += s * (1 - max(0, pan)); R[i:i + len(s)] += s * (1 + min(0, pan))
def lp(x, a):
    y = np.zeros_like(x); acc = 0
    for k in range(len(x)): acc += a * (x[k] - acc); y[k] = acc
    return y
def nrm(y): return y / np.max(np.abs(y))
def thud(weight=1.0):
    m = int(SR * 0.35); t = np.arange(m) / SR; fr = 55 + 60 * np.exp(-t * 28)
    body = np.sin(2 * np.pi * np.cumsum(fr) / SR) * np.exp(-t * (14 / weight)); click = lp(rng.standard_normal(m), 0.25) * np.exp(-t * 160) * 0.5
    return nrm(body + click)
def tick():
    m = int(SR * 0.05); t = np.arange(m) / SR
    return nrm(np.sin(2 * np.pi * 2400 * t) * np.exp(-t * 140) + 0.4 * np.sin(2 * np.pi * 4100 * t) * np.exp(-t * 220))
def impact():
    m = int(SR * 0.6); t = np.arange(m) / SR; fr = 48 + 90 * np.exp(-t * 30)
    return nrm(np.sin(2 * np.pi * np.cumsum(fr) / SR) * np.exp(-t * 7) + 0.55 * lp(rng.standard_normal(m), 0.6) * np.exp(-t * 45))
def whoosh(d):
    m = int(SR * d); t = np.arange(m) / SR; nz = rng.standard_normal(m); cut = 0.02 + 0.25 * np.sin(np.pi * np.clip(t / d, 0, 1)) ** 2
    y = np.zeros(m); acc = 0
    for k in range(m): acc += cut[k] * (nz[k] - acc); y[k] = acc
    return nrm(y * np.sin(np.pi * np.clip(t / d, 0, 1) ** 0.7) ** 2)
def scan(d):
    m = int(SR * d); t = np.arange(m) / SR; nz = rng.standard_normal(m); cut = 0.05 + 0.35 * (t / d); y = np.zeros(m); acc = 0
    for k in range(m): acc += cut[k] * (nz[k] - acc); y[k] = acc
    y = y - lp(y, 0.08) + 0.15 * np.sin(2 * np.pi * (900 + 1400 * t / d) * t)
    return nrm(y * np.minimum(1, t / 0.03) * np.minimum(1, (d - t) / 0.05))
def marker(d):
    m = int(SR * d); t = np.arange(m) / SR; nz = lp(rng.standard_normal(m), 0.35)
    return nrm(nz * np.minimum(1, t / 0.02) * np.exp(-np.maximum(0, t - d * 0.6) * 30))
dB = lambda x: 10 ** (x / 20)
hit = lambda t, g=-18: place(thud(1.3), t, dB(g))
tk = lambda t, g=-29: place(tick(), t, dB(g))
imp = lambda t, g=-15: place(impact(), t, dB(g))
sw = lambda t, d=0.32, g=-30: place(scan(d), t, dB(g))
wh = lambda tend, d=0.38, g=-28: place(whoosh(d), tend - d * 0.7, dB(g))
# hook punch-in
hit(T['trt'], -24)
# split 1: reversal window
wh(SPL[0][0] + 0.38); hit(SPL[0][0] + 0.38, -21); sw(SPL[0][0] + 0.25, 1.3, -33)
tk(T['rightnow']); tk(T['reverse1'], -31); place(whoosh(1.1), T['months1'], dB(-31)); imp(T['surgical'])
wh(SPL[0][1] + 0.3, 0.3, -32)
# lenses
sw(T['soft'] - 0.12, 0.32); tk(T['glandular'], -31); tk(T['back']); sw(T['after'] - 0.1, 0.32); tk(T['hard'], -31); hit(T['noprot'], -20)
for i in range(3): tk(T['three'] - 0.1 + 0.18 * i, -32)
# PIP step 1
wh(PIP[0][0] + 0.38); hit(PIP[0][0] + 0.38, -20); hit(T['driver1'], -21)
for k in ('trt2', 'estradiol1', 'anab2', 'prl1', 'npp', 'deca'): tk(T[k] - 0.05, -31)
place(marker(0.3), T['sensitive'] - 0.25, dB(-27)); tk(T['sensitive'] + 0.1, -28); tk(T['prl2'] + 0.05, -28); tk(T['anything'] - 0.05, -30); imp(T['asap'], -16)
# step 2 range gauge
wh(PIP[0][1] + 0.3, 0.3, -32); hit(T['step2'] + 0.1, -22); place(whoosh(0.6), T['range1'], dB(-32)); tk(T['range1'] + 0.6, -29)
place(whoosh(0.55), T['range2'], dB(-33)); imp(T['nuke'] + 0.25, -16)
for k in ('joints', 'libido', 'mood'): tk(T[k] - 0.2, -28)
tk(T['tool'], -31)
# split 2: step 3
wh(SPL[1][0] + 0.38); hit(SPL[1][0] + 0.38, -21); tk(T['biomarker'] - 0.1); tk(T['worse'] - 0.3, -31); hit(T['shrink'], -21)
place(whoosh(0.4), T['tissue3'] - 0.2, dB(-31)); hit(T['modulator'] + 0.2, -19); tk(T['ralox'] - 0.05); tk(T['nolva'] - 0.05); hit(T['block'], -22); tk(T['breast'] - 0.1, -31)
wh(SPL[1][1] + 0.3, 0.3, -32)
# privacy file
hit(T['clients'] - 0.6 + 0.2, -24)
for tt in (T['clients'] - 0.2, T['blast'] - 0.1, T['blast'] + 0.5): place(marker(0.35), tt, dB(-28))
tk(T['forever'] - 0.2, -28); hit(T['privacy'] + 0.08, -19)
# case PIP
wh(PIP[1][0] + 0.38); hit(PIP[1][0] + 0.38, -20); sw(T['n120'] - 0.2, 0.5, -31); hit(T['n120'] + 0.32, -19)
tk(T['fine'] - 0.2); tk(T['lump'] - 0.1, -28)
for k in ('found', 'corrected', 'treated'): tk(T[k] - 0.05, -28)
sw(T['found'], T['weeks2'] - T['found'], -36); hit(T['gone'], -19)
wh(PIP[1][1] + 0.3, 0.3, -32)
# MENT
hit(T['ment1'] - 0.1, -20); sw(T['aromatizes'], 0.9, -29); tk(T['crazy'] - 0.1, -28); imp(T['dontrun'] + 0.15, -15)
# CTA
tk(T['protocol9'] - 0.15, -29); tk(T['blood9'], -29); hit(T['free'] + 0.05, -20); imp(T['comment'] + 0.1, -15)
out = np.stack([L, R], 1); print('sfx peak dBFS', round(20 * np.log10(np.max(np.abs(out))), 1))
w = wave.open(S + '/build/sfx.wav', 'wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
w.writeframes((np.clip(out, -1, 1) * 32767).astype(np.int16).tobytes()); w.close()
