# Builds the cut dialogue (8 ms crossfades at each trim) + clinical SFX, all SFX times in SOURCE seconds.
import sys, json, subprocess, wave, numpy as np
S = sys.argv[1]; WD = S + '/w/'
SR = 48000
KEEP = json.load(open(WD + 'trim.json'))['keep']
raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', S + '/src/src.mov', '-vn', '-ac', '2', '-ar', str(SR), '-f', 'f32le', '-'], capture_output=True).stdout
src = np.frombuffer(raw, np.float32).reshape(-1, 2)
XF = int(0.008 * SR)
parts = []
for a, b in KEEP:
    parts.append(src[int(round(a * SR)):int(round(b * SR))].copy())
out = parts[0]
for p in parts[1:]:
    r = np.linspace(0, 1, XF)[:, None]
    out = np.concatenate([out[:-XF], out[-XF:] * (1 - r) + p[:XF] * r, p[XF:]])
n = len(out)
def old_to_new(to):
    acc = 0
    for a, b in KEEP:
        if to < b: return acc + max(0, to - a)
        acc += b - a
    return acc
rng = np.random.default_rng(7)
L = np.zeros(n); R = np.zeros(n)
def place(sig, t_src, gain=1.0, pan=0.0):
    i = int(old_to_new(t_src) * SR); s = sig[:max(0, n - i)] * gain
    L[i:i + len(s)] += s * (1 - max(0, pan)); R[i:i + len(s)] += s * (1 + min(0, pan))
def lp(x, a):
    y = np.zeros_like(x); acc = 0
    for k in range(len(x)): acc += a * (x[k] - acc); y[k] = acc
    return y
def thud(weight=1.0):
    m = int(SR * 0.35); t = np.arange(m) / SR; f = 55 + 60 * np.exp(-t * 28)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * (14 / weight)); click = lp(rng.standard_normal(m), 0.25) * np.exp(-t * 160) * 0.5
    y = body + click; return y / np.max(np.abs(y))
def tick():
    m = int(SR * 0.05); t = np.arange(m) / SR
    y = np.sin(2 * np.pi * 2400 * t) * np.exp(-t * 140) + 0.4 * np.sin(2 * np.pi * 4100 * t) * np.exp(-t * 220); return y / np.max(np.abs(y))
def impact():
    m = int(SR * 0.6); t = np.arange(m) / SR; f = 48 + 90 * np.exp(-t * 30)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 7); crack = lp(rng.standard_normal(m), 0.6) * np.exp(-t * 45)
    y = body + 0.55 * crack; return y / np.max(np.abs(y))
def scan(d):
    m = int(SR * d); t = np.arange(m) / SR; nz = rng.standard_normal(m); cut = 0.05 + 0.35 * (t / d); y = np.zeros(m); acc = 0
    for k in range(m): acc += cut[k] * (nz[k] - acc); y[k] = acc
    y = y - lp(y, 0.08) + 0.15 * np.sin(2 * np.pi * (900 + 1400 * t / d) * t)
    env = np.minimum(1, t / 0.03) * np.minimum(1, (d - t) / 0.05); return y * env / np.max(np.abs(y * env))
def whoosh(d):
    m = int(SR * d); t = np.arange(m) / SR; nz = rng.standard_normal(m); cut = 0.02 + 0.25 * np.sin(np.pi * np.clip(t / d, 0, 1)) ** 2
    y = np.zeros(m); acc = 0
    for k in range(m): acc += cut[k] * (nz[k] - acc); y[k] = acc
    env = np.sin(np.pi * np.clip(t / d, 0, 1) ** 0.7) ** 2; return y * env / np.max(np.abs(y * env))
def beep():  # monitor beep, soft
    m = int(SR * 0.09); t = np.arange(m) / SR; y = np.sin(2 * np.pi * 1000 * t) * np.minimum(1, t / 0.005) * np.minimum(1, (0.09 - t) / 0.02); return y
dB = lambda x: 10 ** (x / 20)
hit = lambda t, g=-17: place(thud(1.4), t, dB(g))
tk = lambda t, g=-28: place(tick(), t, dB(g))
sw = lambda t, d=0.32, g=-29: place(scan(d), t, dB(g))
imp = lambda t, g=-14: place(impact(), t, dB(g))
sw(6.0, 0.3, -31)                       # band in
tk(7.18, -27); tk(10.04, -25); hit(10.66, -21)   # 03 flags red, 01 locks in
hit(11.3); sw(13.32, 0.8, -31); tk(17.14); tk(18.32); sw(19.14, 0.9, -31); place(thud(1.0), 20.2, dB(-20))
for t in (21.68, 22.28, 23.12): tk(t, -29)
place(thud(0.8), 23.9, dB(-21))
tk(25.7, -27)
for k in range(5): place(beep(), 25.95 + k * 0.62, dB(-36))
hit(27.9, -16)
place(whoosh(0.32), 28.7, dB(-27)); hit(29.0, -19)
for t in (29.86, 30.66, 31.34, 32.22, 33.38): tk(t, -30)
hit(34.5); tk(37.88, -27); imp(39.16, -15)
hit(40.64, -16); tk(43.78, -24)
place(whoosh(0.42), 44.4, dB(-27)); tk(46.38); tk(48.7)
for t in (49.3, 49.5, 49.82, 50.14): place(thud(0.6), t, dB(-24))
tk(50.7, -25); hit(51.74, -18); imp(54.38, -14)
sw(58.2, 0.35, -29); sw(59.46, 1.0, -32); tk(62.26)
for k in range(7): tk(63.82 + k * 0.05, -34)
sw(64.45, 0.4, -29)
for t, _ in [(65.42, 0), (66.66, 0), (67.62, 0), (68.26, 0), (69.02, 0), (70.2, 0)]: tk(t, -30)
for k in range(6): tk(72.0 + k * 0.22, -33)
hit(74.5, -19); place(thud(1.2), 75.98, dB(-17))
fx = np.stack([L, R], 1); print('sfx peak dBFS', 20 * np.log10(np.max(np.abs(fx)) + 1e-9))
mix = out + fx
w = wave.open(S + '/w/mix_pre.wav', 'wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
w.writeframes((np.clip(mix / max(1, np.max(np.abs(mix))), -1, 1) * 32767).astype(np.int16).tobytes()); w.close()
print('dur', n / SR)
