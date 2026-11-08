# Clinical SFX bed for full test 03, placed on graphic landings (cues from render.py).  usage: python3 sfx.py <scratch>
import sys, os, wave, importlib.util
import numpy as np
S = sys.argv[1].rstrip('/') + '/'
spec = importlib.util.spec_from_file_location('r', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'render.py'))
sys.argv = ['render.py', S]; r = importlib.util.module_from_spec(spec); spec.loader.exec_module(r)
cue, cend = r.cue, r.cend
SR = 48000; n = int(SR * r.END) + SR; L = np.zeros(n); R = np.zeros(n); rng = np.random.default_rng(7)
def place(sig, t, gain=1.0, pan=0.0):
    i = int(t * SR); s = sig[:max(0, n - i)] * gain
    L[i:i + len(s)] += s * (1 - max(0, pan)); R[i:i + len(s)] += s * (1 + min(0, pan))
def lp(x, a):
    y = np.zeros_like(x); acc = 0
    for k in range(len(x)): acc += a * (x[k] - acc); y[k] = acc
    return y
def thud(weight=1.0):
    m = int(SR * 0.35); t = np.arange(m) / SR; f = 55 + 60 * np.exp(-t * 28)
    y = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * (14 / weight)) + lp(rng.standard_normal(m), 0.25) * np.exp(-t * 160) * 0.5
    return y / np.max(np.abs(y))
def tick():
    m = int(SR * 0.05); t = np.arange(m) / SR
    y = np.sin(2 * np.pi * 2400 * t) * np.exp(-t * 140) + 0.4 * np.sin(2 * np.pi * 4100 * t) * np.exp(-t * 220); return y / np.max(np.abs(y))
def impact():
    m = int(SR * 0.6); t = np.arange(m) / SR; f = 48 + 90 * np.exp(-t * 30)
    y = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 7) + 0.55 * lp(rng.standard_normal(m), 0.6) * np.exp(-t * 45); return y / np.max(np.abs(y))
def scan(d):
    m = int(SR * d); t = np.arange(m) / SR; nz = rng.standard_normal(m); cut = 0.05 + 0.35 * (t / d); y = np.zeros(m); acc = 0
    for k in range(m): acc += cut[k] * (nz[k] - acc); y[k] = acc
    y = y - lp(y, 0.08) + 0.15 * np.sin(2 * np.pi * (900 + 1400 * t / d) * t); env = np.minimum(1, t / 0.03) * np.minimum(1, (d - t) / 0.05)
    return y * env / np.max(np.abs(y * env))
def beep(fr=1000, d=0.09):
    m = int(SR * d); t = np.arange(m) / SR; return np.sin(2 * np.pi * fr * t) * np.minimum(1, t / 0.005) * np.minimum(1, (d - t) / 0.01)
dB = lambda x: 10 ** (x / 20)
hit = lambda t: place(thud(1.4), t, dB(-17))
tk = lambda t, g=-28: place(tick(), t, dB(g))
sw = lambda t, d=0.32: place(scan(d), t, dB(-29))
# panels land
for sc in r.SCENES: hit(sc[0])
for st in r.STRIPS: sw(st[0], 0.3)
# S1
sw(cue('20'), 0.5); tk(cue('pounds')); sw(cue('stop'), 0.8); tk(cue('90')); tk(cue('fifth')); place(thud(1.0), cue('social'), dB(-21))
# S2 gauge
tk(cue('never') - 0.3); place(impact(), cue('fast') + 0.15, dB(-18)); tk(cue('keeping') - 0.1, -26)
# ECG beeps until flatline, then long tone
t0 = cue('without'); tD = cue('disposable'); tF = cue('die') + 0.1; t = t0 + 0.3
while t < tF:
    place(beep(1000), t, dB(-34)); t += 0.8 if t < tD else 0.48
place(beep(1000, 1.4), tF, dB(-36))
# CTA
place(thud(1.2), cue('comment the word'), dB(-18))
# genetics
sw(cue('ceiling')); tk(cue('respond')); tk(cue('tolerate')); hit(cue('combination') + 0.0)
sw(cue("there's a very specific", cue('combination')), 0.6); tk(cue('phil')); tk(cue('ronnie'))
# client file
tk(cue('low')); place(impact(), cue('insane'), dB(-17))
# checklist
for w in ('nutrition', 'recovery', 'sleep', 'blood'): tk(cue(w), -30)
tk(cue('every single day', cue('optimized')), -30)
# bars
place(thud(1.0), cue('fourth'), dB(-20))
for w, a in (('six months', cue('fourth')), ('year', cue('fourth')), ('three', cue('fourth')), ('five', cue('fourth'))): tk(cue(w, a), -30)
# amplifier
sw(cue('blow'), 0.35); tk(cue('guy')); sw(cue('amplify'), 0.6); place(impact(), r.VERDICTS[0][0], dB(-14))
# waffle
sw(cue('80'), 1.4); tk(cue('80') + 1.3, -26)
# end
tk(cue('best')); place(thud(1.2), cue('appreciate'), dB(-18))
out = np.stack([L, R], 1)[:int(SR * r.END)]
print('sfx peak dBFS', 20 * np.log10(np.max(np.abs(out))))
w = wave.open(S + 'ex/sfx.wav', 'wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
w.writeframes((np.clip(out, -1, 1) * 32767).astype(np.int16).tobytes()); w.close()
