# Reel 03 — "Realistic muscle on gear: 3 months vs 5 years" (1080x1920, 30 fps)
# usage: python3 render.py <scratch> stills t1 t2 ...   |   python3 render.py <scratch> <n0> <n1> <out.mp4>
import json, subprocess, sys, math, re
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
S = sys.argv[1]; F = S + '/fonts/'; B = S + '/build/'
REPO = __file__.rsplit('/editing/', 1)[0]
W, H = 1080, 1920; FPS = 30
TL = json.load(open(B + 'timeline.json')); DUR = TL['dur']; PIECES = TL['pieces']
RAW = json.load(open(B + '../raw_small.json'))['words']
WORDS = json.load(open(B + 'captions.json'))
# ---------------- palette ----------------
GOLD = (201, 169, 110); CREAM = (244, 241, 234); NAVY = (14, 17, 23); MUTED = (184, 184, 188); DIM = (124, 124, 130)
RED = (255, 34, 28); VGOLD = (255, 194, 26); CYAN = (0, 229, 255); GREEN = (30, 255, 110); DEEP = (2, 3, 8)
INK = (6, 8, 14); WHITE = (255, 255, 255); CRIMSON = (224, 36, 63); CBAR = (200, 16, 46); COARED = (210, 10, 20)
GRID = (52, 56, 70); STEEL = (120, 132, 160)
# ---------------- fonts ----------------
FONTS = {'BEB': 'BebasNeue-Regular.ttf', 'BAR': 'BarlowCondensed-ExtraBold.ttf', 'BARB': 'BarlowCondensed-Bold.ttf',
         'BARS': 'BarlowCondensed-SemiBold.ttf', 'MONO': '/usr/share/fonts/truetype/jetbrains-mono/JetBrainsMono-Bold.ttf',
         'MONOM': '/usr/share/fonts/truetype/jetbrains-mono/JetBrainsMono-Medium.ttf', 'DMB': 'DMSans%5Bopsz%2Cwght%5D.ttf',
         'DMR': 'DMSans%5Bopsz%2Cwght%5D.ttf'}
_fc = {}
def f(n, s):
    k = (n, int(s))
    if k not in _fc:
        p = FONTS[n]; p = p if p.startswith('/') else F + p
        fo = ImageFont.truetype(p, int(s))
        if n in ('DMB', 'DMR'):
            try: fo.set_variation_by_axes([14, 700 if n == 'DMB' else 420])
            except Exception: pass
        _fc[k] = fo
    return _fc[k]
# ---------------- easing / util ----------------
def clamp(x, a=0, b=1): return max(a, min(b, x))
def expo(x): x = clamp(x); return 1 if x >= 1 else 1 - 2 ** (-10 * x)
def ease_io(x): x = clamp(x); return 4 * x ** 3 if x < .5 else 1 - (-2 * x + 2) ** 3 / 2
def back(x):  # firm settle, tiny undershoot only (no bounce)
    x = clamp(x); c = 1.2; return 1 + (c + 1) * (x - 1) ** 3 + c * (x - 1) ** 2
def lerp(a, b, t): return a + (b - a) * t
def A(c, a): return tuple(c[:3]) + (int(clamp(a) * 255),)
def appear(t, t0, dur=0.16): return expo((t - t0) / dur)
def mix(c1, c2, k): return tuple(int(lerp(a, b, clamp(k))) for a, b in zip(c1, c2))
# ---------------- time mapping (source -> output) ----------------
def O(ts):
    for p in PIECES:
        s, e = p['src']
        if s - 1e-6 <= ts < e: return p['out'][0] + ts - s
    nxt = [p for p in PIECES if p['src'][0] >= ts]
    if nxt: return min(nxt, key=lambda p: p['src'][0])['out'][0]
    return DUR
def _clean(w): return re.sub(r"[^a-z0-9%]", '', w.lower())
def cue(word, approx, win=2.6):
    word = _clean(word)
    c = [w for w in RAW if _clean(w['w']).startswith(word) and abs(w['s'] - approx) <= win]
    if not c: raise SystemExit(f'cue not found: {word} @ {approx}')
    return O(min(c, key=lambda w: abs(w['s'] - approx))['s'])
# ---------------- drawing primitives ----------------
GL = None  # glow layer draw
def txt(d, x, y, s, font, col, a=1.0, anchor=None):
    if a <= 0: return
    d.text((x, y), s, font=font, fill=A(col, a), anchor=anchor)
def tracked(d, x, y, s, font, col, a=1.0, sp=4):
    for ch in s:
        txt(d, x, y, ch, font, col, a); x += d.textlength(ch, font=font) + sp
    return x
def tw(d, s, font): return d.textlength(s, font=font)
def brackets(d, x0, y0, x1, y1, col, L=34, w=4):
    for (cx, cy, sx, sy) in [(x0, y0, 1, 1), (x1, y0, -1, 1), (x0, y1, 1, -1), (x1, y1, -1, -1)]:
        d.line([(cx, cy), (cx + sx * L, cy)], fill=col, width=w); d.line([(cx, cy), (cx, cy + sy * L)], fill=col, width=w)
def lit_bar(d, x0, y0, x1, y1, col, a=1.0):
    if x1 <= x0 or y1 <= y0: return
    h = max(1, int(y1 - y0))
    for i in range(h):
        k = i / h; c = tuple(int(min(255, v * (1.18 - 0.36 * k) + (40 if k < 0.12 else 0))) for v in col)
        d.line([(x0, y0 + i), (x1, y0 + i)], fill=c + (int(255 * a),))
def lit_vbar(d, x0, y0, x1, y1, col, a=1.0):  # vertical bar, lit top edge
    if x1 <= x0 or y1 <= y0: return
    d.rectangle([x0, y0, x1, y1], fill=A(col, a * 0.92))
    d.rectangle([x0, y0, x1, min(y1, y0 + 6)], fill=A(mix(col, WHITE, 0.45), a))
    d.rectangle([x0, max(y0, y1 - 10), x1, y1], fill=A(mix(col, (0, 0, 0), 0.35), a))
def tag(d, x, y, label, col=RED, size=30, a=1.0, glow=True):
    if a <= 0: return x
    fn = f('MONO', size); w_ = d.textlength(label, font=fn); h = size + 16
    lit_bar(d, x, y, x + w_ + 24, y + h, col, a)
    d.text((x + 12, y + 5), label, font=fn, fill=A(INK if col in (VGOLD, GREEN, CYAN) else WHITE, a))
    if GL and glow: GL.rectangle([x - 4, y - 4, x + w_ + 28, y + h + 4], outline=A(col, a), width=8)
    return x + w_ + 24
def flag(d, box, t0, t, col=RED, L=28):
    p = expo((t - t0) / 0.14)
    if p <= 0: return
    x0, y0, x1, y1 = box; s = lerp(1.25, 1, p); cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    x0, x1 = cx + (x0 - cx) * s, cx + (x1 - cx) * s; y0, y1 = cy + (y0 - cy) * s, cy + (y1 - cy) * s
    brackets(d, x0, y0, x1, y1, A(col, p), L, 6)
    if GL: brackets(GL, x0, y0, x1, y1, A(col, p), L, 12)
def arrow(d, x0, y0, x1, y1, col, w=5, a=1.0, head=18):
    d.line([(x0, y0), (x1, y1)], fill=A(col, a), width=w)
    ang = math.atan2(y1 - y0, x1 - x0); L = head
    d.polygon([(x1, y1), (x1 - L * math.cos(ang - 0.45), y1 - L * math.sin(ang - 0.45)),
               (x1 - L * math.cos(ang + 0.45), y1 - L * math.sin(ang + 0.45))], fill=A(col, a))
def check(d, x, y, col, s=1.0, a=1.0):
    pts = [(x, y + 16 * s), (x + 10 * s, y + 28 * s), (x + 30 * s, y + 2 * s)]
    d.line(pts, fill=A(col, a), width=int(6 * s))
    if GL: GL.line(pts, fill=A(col, a), width=int(12 * s))
def cross(d, x, y, col, s=1.0, a=1.0):
    d.line([(x, y), (x + 28 * s, y + 28 * s)], fill=A(col, a), width=int(6 * s)); d.line([(x + 28 * s, y), (x, y + 28 * s)], fill=A(col, a), width=int(6 * s))
    if GL: GL.line([(x, y), (x + 28 * s, y + 28 * s)], fill=A(col, a), width=12); GL.line([(x + 28 * s, y), (x, y + 28 * s)], fill=A(col, a), width=12)
def polyline(d, pts, col, w=6, a=1.0, glow=True):
    if len(pts) < 2: return
    d.line(pts, fill=A(col, a), width=w, joint='curve')
    if GL and glow: GL.line(pts, fill=A(col, a), width=w * 2, joint='curve')
def partial(pts, p):  # first fraction p of a polyline (by index)
    if p <= 0: return pts[:1]
    n = len(pts) - 1; k = p * n; i = int(k)
    if i >= n: return pts
    q = k - i; a_, b_ = pts[i], pts[i + 1]
    return pts[:i + 1] + [(lerp(a_[0], b_[0], q), lerp(a_[1], b_[1], q))]
def dashed(d, pts, col, w=4, a=1.0, on=16, off=12):
    acc = 0
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        L = math.hypot(x1 - x0, y1 - y0)
        if L == 0: continue
        pos = 0
        while pos < L:
            ph = (acc + pos) % (on + off); seg = min(L - pos, (on - ph) if ph < on else (on + off - ph))
            if ph < on:
                a0 = pos / L; a1 = (pos + seg) / L
                d.line([(lerp(x0, x1, a0), lerp(y0, y1, a0)), (lerp(x0, x1, a1), lerp(y0, y1, a1))], fill=A(col, a), width=w)
            pos += max(seg, 0.5)
        acc += L
def hatch(d, x0, y0, x1, y1, col, a=1.0, step=14):
    d.rectangle([x0, y0, x1, y1], outline=A(col, a), width=3)
    for k in range(int(-(y1 - y0)), int(x1 - x0), step):
        xa, ya = x0 + k, y1; xb, yb = x0 + k + (y1 - y0), y0
        if xa < x0: ya = y1 - (x0 - xa); xa = x0
        if xb > x1: yb = y0 + (xb - x1); xb = x1
        if xb > xa: d.line([(xa, ya), (xb, yb)], fill=A(col, a * 0.7), width=2)
def kicker(d, x, y, s, col=VGOLD, a=1.0, size=26, line=True):
    if line: d.line([(x, y + size * 0.55), (x + 40, y + size * 0.55)], fill=A(col, a), width=4); x += 54
    return tracked(d, x, y, s, f('MONO', size), col, a, 3)
def frosted(im, box, dark=0.86, blur=10):
    x0, y0, x1, y1 = [int(v) for v in box]
    x0, y0 = max(0, x0), max(0, y0); x1, y1 = min(W, x1), min(H, y1)
    if x1 - x0 < 4 or y1 - y0 < 4: return
    reg = im.crop((x0, y0, x1, y1)).convert('RGB')
    sm = reg.resize((max(1, reg.width // 4), max(1, reg.height // 4)), Image.BILINEAR).filter(ImageFilter.GaussianBlur(blur / 4))
    reg = sm.resize(reg.size, Image.BILINEAR)
    im.paste(Image.blend(reg, Image.new('RGB', reg.size, DEEP), dark).convert('RGBA'), (x0, y0))
def big_blur(img, r):
    sm = img.resize((W // 4, H // 4), Image.BILINEAR).filter(ImageFilter.GaussianBlur(max(0.1, r / 4)))
    return sm.resize((W, H), Image.BILINEAR)
def headline(d, x, y, parts, size=92, a=1.0, maxw=None):
    # parts: list of lines; each line list of (text, colour)
    for line in parts:
        sz = size
        if maxw:
            while sum(tw(d, s, f('BEB', sz)) for s, _ in line) > maxw: sz -= 2
        xx = x
        for s, c in line:
            txt(d, xx, y, s, f('BEB', sz), c, a); xx += tw(d, s, f('BEB', sz))
        y += sz * 0.95
    return y
# ======================= CUES (all from the source transcript) =======================
C = {}
def setc(k, w, ap): C[k] = cue(w, ap)
for k, w, ap in [
    ('70', '70', 3.0), ('trt', 'trt', 7.2), ('another', 'another', 8.9),
    ('three', 'three', 13.3), ('stacking', 'stacking', 17.2), ('bloodwork', 'bloodwork', 18.9), ('five', 'five', 19.7), ('crazy', 'crazy', 21.6), ('gear1', 'gear', 22.8),
    ('promise', 'promise', 23.4), ('real', 'real', 26.4), ('fast', 'fast', 29.2), ('scale', 'scale', 31.7), ('water', 'water', 33.4), ('glycogen', 'glycogen', 34.3), ('sponge', 'sponge', 36.3), ('That', 'that', 37.28),
    ('stall', 'stall', 38.6), ('reckless', 'reckless', 39.2), ('dose', 'dose', 40.2), ('heart', 'heart', 42.0), ('kidneys', 'kidneys', 42.9), ('hardware', 'hardware', 44.8), ('exacerbated', 'exacerbated', 46.0), ('steroids', 'steroids', 48.6),
    ('Some', 'some', 63.44), ('15', '15', 64.44), ('mirror', 'mirror', 65.6), ('Ronnie', 'ronnie', 68.2), ('Coleman', 'coleman', 68.78),
    ('explode', 'explode', 77.6), ('Unless', 'unless', 78.44), ('of1', 'of', 79.5), ('im', "i'm", 81.64),
    ('break', 'break', 84.78), ('3mo', '3', 85.8), ('6mo', '6', 87.42), ('1yr', '1', 88.4), ('5yr', '5', 89.2),
    ('assuming', 'assuming', 90.04), ('training', 'training', 90.9), ('nutrition', 'nutrition', 91.4), ('recovery', 'recovery', 92.2), ('health', 'health', 92.9), ('locked', 'locked', 94.6), ('24', '24', 95.8),
    ('Now1', 'now', 96.98), ('first3', 'first', 98.2), ('strength', 'strength', 102.0), ('fuller', 'fuller', 103.6), ('weight', 'weight', 104.8),
    ('controlled', 'controlled', 107.9), ('super', 'superphysiological', 109.3), ('13', '13', 111.0), ('fatfree', 'fat', 112.5), ('weeks10', 'weeks', 114.6),
    ('not13', 'not', 118.0), ('permanent', 'permanent', 119.4), ('mostly', 'most', 120.52), ('water2', 'water', 121.8), ('glycogen2', 'glycogen', 122.4), ('other', 'other', 123.4),
    ('receptor', 'receptor', 126.1), ('synthesis', 'synthesis', 128.3), ('hypertrophy', 'hypertrophy', 129.12), ('scale2', 'scale', 131.5), ('keep', 'keep', 132.6), ('Alright2', 'alright', 132.88),
    ('6months', '6', 134.0), ('study2', 'study', 140.4), ('17', '17', 141.6), ('weeks20', 'weeks', 145.4), ('guaranteed', 'guaranteed', 147.4), ('Delt', 'delt', 149.6),
    ('chest', 'chest', 150.7), ('back', 'back', 151.2), ('legs', 'legs', 151.9), ('thicker', 'thicker', 153.0), ('growth1', 'growth', 155.0), ('accelerating', 'accelerating', 156.4),
    ('600', '600', 161.4), ('forklift', 'forklift', 163.6), ('Then', 'then', 165.3),
    ('oneyear', 'one', 166.0), ('adaptation', 'adaptation', 170.9), ('nutrition2', 'nutrition', 172.6), ('progressive', 'progressive', 176.8), ('protein', 'protein', 177.9), ('recovery2', 'recovery', 178.4), ('consistency', 'consistency', 178.9),
    ('science', 'science', 183.0), ('fibers', 'fibers', 187.0), ('tension', 'tension', 189.0), ('mTOR', 'mtor', 190.6), ('synthesis2', 'synthesis', 191.9),
    ('Theres', "there's", 192.6), ('research', 'research', 195.5), ('20to30', '20', 197.9), ('12weeks', '12', 200.6), ('behemoths', 'behemoths', 203.2),
    ('genetics', 'genetics', 207.3), ('history', 'history', 208.84), ('size', 'size', 210.4), ('And5', 'and', 212.9),
    ('fiveyrs', 'five', 214.4), ('15b', '15', 227.0), ('zip', 'zip', 231.4), ('outliers', 'outliers', 238.0), ('harder', 'harder', 242.9),
    ('ignore', 'ignore', 244.9), ('optimized', 'optimized', 249.4), ('bloodwork2', 'blood', 251.8), ('EKGs', 'ekgs', 253.6), ('cardio', 'cardiovascular', 254.5), ('accumulate', 'accumulate', 256.4),
    ('hct', 'hematocrate', 258.3), ('lipids', 'lipids', 258.9), ('bp', 'pressure', 259.5), ('kidney2', 'kidney', 259.9), ('heart2', 'heart', 260.8), ('Now2', 'now', 262.5),
    ('Assuming2', 'assuming', 268.46), ('untrained', 'untrained', 270.0), ('average', 'average', 272.0), ('locked2', 'locked', 273.4),
    ('r3', 'about', 276.4), ('r6', 'about', 281.6), ('r12', '10', 285.7), ('r5y', '20', 298.4), ('fiveyrs2', '5', 289.4),
    ('clarify', 'clarify', 303.9), ('240', '240', 305.4), ('40', '40', 311.0), ('realistic', 'realistic', 315.1), ('averagemale', 'average', 316.1), ('freak', 'freak', 318.6), ('how', 'how', 320.6),
    ('gear10', 'gear', 322.9), ('10y', '10', 324.4), ('suboptimal', 'suboptimal', 326.8), ('linear', 'linear', 332.9),
    ('I_need', 'need', 340.0), ('client', 'client', 345.6), ('2030', '20', 348.6), ('sixmo', 'six', 349.98), ('90', '90', 351.9), ('fifth', 'fifth', 353.8), ('goal', 'goal', 355.8), ('Its', "it's", 358.3),
    ('ceiling', 'ceiling', 381.6), ('respond', 'respond', 383.6), ('tolerate', 'tolerate', 384.8), ('combination', 'combination', 386.6), ('Phil', 'phil', 389.6), ('Ronnie2', 'ronnie', 393.4), ('Honestly', 'honestly', 394.46),
    ('clients', 'clients', 397.4), ('low', 'low', 402.6), ('weeds', 'weeds', 404.8), ('training3', 'training', 410.9), ('nutrition3', 'nutrition', 413.2), ('recovery3', 'recovery', 413.9),
    ('sleep', 'sleep', 415.34), ('bloodwork3', 'blood', 417.6), ('hard', 'hard', 419.4), ('fourth', 'fourth', 425.0), ('six3', 'six', 426.9), ('year3', 'year', 428.5), ('three3', 'three', 429.8), ('five3', 'five', 430.9), ('Anyways', 'anyways', 431.86),
    ('optimize', 'optimize', 443.0), ('amplify', 'amplify', 444.8), ('Your', 'your', 447.1), ('80', '80', 451.8), ('85', '85', 452.2), ('genetics2', 'genetics', 455.8), ('progress', 'progress', 458.4), ('day', 'day', 463.4),
    ('want', 'want', 373.7), ('framework', 'framework', 375.1), ('Comment', 'comment', 375.9), ('free', 'free', 378.9), ('Appreciate', 'appreciate', 463.8)]:
    setc(k, w, ap)
CTA_IN = O(373.56); PUSH_END = O(379.5); HOOK_END = 3.3
# ======================= SCENES =======================
# --- T strip: top glass strip over the wall/cap (footage untouched) ---
TS = (40, 360, 1040, 662)
def strip_chrome(im, d, t, sc, label, right=''):
    x0, y0, x1, y1 = TS
    p = ease_io((t - sc['t0']) / 0.22); xr = lerp(x0, x1, p)
    frosted(im, (x0, y0, xr, y1), 0.84, 14)
    d.rectangle([x0, y0, xr, y1], outline=A(VGOLD, 0.35), width=2)
    d.line([(x0, y0), (xr, y0)], fill=A(VGOLD, 1), width=4)
    if GL: GL.line([(x0, y0), (xr, y0)], fill=A(VGOLD, 1), width=8)
    if p > 0.6:
        a = appear(t, sc['t0'] + 0.14)
        kicker(d, x0 + 24, y0 + 18, label, VGOLD, a, 24)
        if right: fr = f('MONO', 22); txt(d, x1 - 24 - tw(d, right, fr), y0 + 20, right, fr, DIM, a)
    return p
def sc_waffle(im, d, t, sc):
    strip_chrome(im, d, t, sc, 'GYM FLOOR · 100 LIFTERS', 'SAMPLE')
    t0 = sc['t0']; n = int(clamp((t - t0 - 0.1) / 0.7) * 70)
    cnt = int(lerp(0, 70, expo((t - t0 - 0.1) / 0.7)))
    txt(d, 70, 418, f'{cnt}%', f('BEB', 190), RED, appear(t, t0 + 0.05))
    if GL: GL.text((70, 418), f'{cnt}%', font=f('BEB', 190), fill=A(RED, 0.6 * appear(t, t0 + 0.05)))
    cs, gp = 26, 6; gx, gy = 370, 420
    for i in range(100):
        r, c = i // 20, i % 20; x = gx + c * (cs + gp); y = gy + r * (cs + gp)
        on = i < n
        d.rectangle([x, y, x + cs, y + cs], fill=A(RED if on else (58, 62, 76), 1 if on else 0.9))
    if t >= C['trt']:
        a = appear(t, C['trt']); x = tag(d, gx, 600, 'TRT / GEAR', RED, 26, a)
        txt(d, x + 18, 604, '70', f('MONO', 26), WHITE, a); txt(d, x + 60, 604, '· NATURAL 30', f('MONO', 26), DIM, a)
def sc_months(im, d, t, sc):
    strip_chrome(im, d, t, sc, 'TIME ON GEAR', 'MONTHS')
    ax0, ax1, ay = 190, 1000, 620
    a0 = appear(t, sc['t0'] + 0.15)
    d.line([(ax0, ay), (ax1, ay)], fill=A(STEEL, a0), width=2)
    for k in range(0, 61, 12):
        x = lerp(ax0, ax1, k / 60); d.line([(x, ay - 8), (x, ay + 4)], fill=A(STEEL, a0), width=2)
        lb = '0' if k == 0 else f'{k // 12}Y'; fn = f('MONO', 20); txt(d, x - tw(d, lb, fn) / 2, ay + 8, lb, fn, DIM, a0)
    rows = [('YOU', 3, C['three'], RED, '3 MO'), ('HIM', 60, C['five'], VGOLD, '5 YRS')]
    for i, (lb, m, tt, col, val) in enumerate(rows):
        y = 440 + i * 84; a = appear(t, tt - 0.4 if i == 0 else C['stacking'])
        txt(d, 70, y + 4, lb, f('BEB', 56), WHITE, a)
        if t >= tt:
            p = expo((t - tt) / (0.25 if i == 0 else 0.9)); xe = lerp(ax0, lerp(ax0, ax1, m / 60), p)
            lit_bar(d, ax0, y + 6, max(ax0 + 6, xe), y + 58, col)
            if GL: GL.rectangle([ax0, y + 6, xe, y + 58], fill=A(col, 0.55))
            if p > 0.5: txt(d, xe + 14 if i == 0 else xe - 130, y + 6, val, f('BEB', 54), col if i == 0 else INK)
    if t >= C['bloodwork']:  # bloodwork panel ticks along the 5-year bar
        for k in range(20):
            tk = C['bloodwork'] + k * 0.05
            if t >= tk and t >= C['five']:
                x = lerp(ax0, ax1, (k * 3 + 1.5) / 60); xe = lerp(ax0, ax1, expo((t - C['five']) / 0.9))
                if x < xe - 140: d.rectangle([x - 2, 530, x + 2, 540], fill=A(INK, 0.8))
    if t >= C['crazy']:
        a = appear(t, C['crazy']); tag(d, 620, 380, '20× THE TIME', VGOLD, 26, a)
def sc_months_guard(): pass
# --- A: frosted centre panel over blurred footage ---
PA = (56, 372, 1024, 1340)
def sc_sponge(im, d, t, sc):
    cx, cy, R = 300, 760, 210
    a = appear(t, sc['t0'] + 0.15, 0.3)
    sw = expo((t - C['water']) / 0.9) if t >= C['water'] else 0
    gly = appear(t, C['glycogen'], 0.4)
    # cross-section (X-ray): epimysium + fascicles
    d.ellipse([cx - R, cy - R, cx + R, cy + R], outline=A(CYAN, a), width=5)
    if GL: GL.ellipse([cx - R, cy - R, cx + R, cy + R], outline=A(CYAN, a), width=10)
    rng = np.random.default_rng(3)
    fas = [(cx + r * math.cos(th), cy + r * math.sin(th)) for r, th in [(0, 0)] + [(95, k * math.pi / 3) for k in range(6)] + [(165, k * math.pi / 5 + 0.3) for k in range(10)]]
    for i, (fx, fy) in enumerate(fas):
        rr = (34 if i else 40) * lerp(1.0, 1.22, sw)
        d.ellipse([fx - rr, fy - rr, fx + rr, fy + rr], fill=A(mix((8, 30, 40), CYAN, 0.35 * sw), a * (0.6 + 0.3 * sw)), outline=A(CYAN, a * 0.85), width=3)
        if gly > 0:
            for k in range(4):
                gx_ = fx + rng.uniform(-rr * 0.55, rr * 0.55); gy_ = fy + rng.uniform(-rr * 0.55, rr * 0.55)
                d.ellipse([gx_ - 4, gy_ - 4, gx_ + 4, gy_ + 4], fill=A(VGOLD, gly))
        else: [rng.uniform(0, 1) for _ in range(8)]
        if sw > 0:
            for k in range(3):
                ang = t * 1.5 + i + k * 2.1; wx = fx + rr * 0.45 * math.cos(ang); wy = fy + rr * 0.45 * math.sin(ang)
                d.ellipse([wx - 3, wy - 3, wx + 3, wy + 3], fill=A(WHITE, 0.7 * sw))
    txt(d, 100, 470, 'MUSCLE CROSS-SECTION', f('MONO', 24), CREAM, a)
    if sw > 0: tag(d, 96, 1000, 'H2O', CYAN, 26, appear(t, C['water']))
    if gly > 0: tag(d, 210, 1000, 'GLYCOGEN', VGOLD, 26, gly)
    # right: two mini time-series
    def series(y0, label, tt, pts_fn, col, val):
        if t < tt - 0.1: return
        aa = appear(t, tt - 0.1)
        txt(d, 580, y0, label, f('MONO', 24), CREAM, aa)
        x0, x1, yb, yt = 580, 980, y0 + 230, y0 + 50
        d.line([(x0, yb), (x1, yb)], fill=A(GRID, aa), width=2); d.line([(x0, yt), (x0, yb)], fill=A(GRID, aa), width=2)
        pts = [(lerp(x0, x1, k / 20), lerp(yb, yt, pts_fn(k / 20))) for k in range(21)]
        pp = partial(pts, clamp((t - tt) / 1.4)); polyline(d, pp, col, 6, aa)
        if len(pp) > 1: d.ellipse([pp[-1][0] - 8, pp[-1][1] - 8, pp[-1][0] + 8, pp[-1][1] + 8], fill=A(WHITE, aa))
        if t >= tt + 1.0: txt(d, 980 - tw(d, val, f('BEB', 48)), y0 - 6, val, f('BEB', 48), col, appear(t, tt + 1.0))
    series(520, 'CONTRACTILE TISSUE', C['real'], lambda k: 0.12 * k, CYAN, 'SLOW')
    series(820, 'SCALE WEIGHT', C['scale'], lambda k: 0.95 * (1 - (1 - k) ** 2.2), VGOLD, 'FAST')
    if t >= C['sponge']:
        p = expo((t - C['sponge']) / 0.22); y = 1180; x1 = lerp(100, 980, p)
        GL.rectangle([96, y - 6, x1 + 4, y + 96], outline=A(RED, 1), width=10)
        lit_bar(d, 100, y, x1, y + 90, RED)
        if p > 0.6: txt(d, 128, y + 10, 'SWELLING', f('BEB', 74), WHITE); txt(d, 128 + tw(d, 'SWELLING ', f('BEB', 74)), y + 32, '≠ NEW TISSUE', f('MONO', 32), WHITE)
# --- B: PIP takeover on brand navy ---
def sc_dose(im, d, t, sc):
    a = appear(t, sc['t0'] + 0.3, 0.25)
    kicker(d, 80, 384, 'WHY GUYS STALL', VGOLD, a)
    headline(d, 80, 440, [[('DOSE ', CREAM), ('UP.', RED)], [('GAINS ', CREAM), ('FLAT.', VGOLD)]], 104, a)
    txt(d, 80, 650, 'Same heart. Same kidneys.', f('DMR', 34), MUTED, appear(t, C['hardware']))
    # chart
    x0, x1, yb, yt = 110, 980, 1160, 990
    d.line([(x0, yb), (x1, yb)], fill=A(GRID, a), width=2); d.line([(x0, yt), (x0, yb)], fill=A(GRID, a), width=2)
    txt(d, x0, yb + 8, 'WEEKS →', f('MONO', 20), DIM, a)
    g = [(lerp(x0, x1, k / 30), lerp(yb - 10, yt + 30, min(1, (k / 30) ** 0.5 * 1.25) if k < 12 else 1.0 * (0.55 + 0.45 * min(1, (12 / 30) ** 0.5 * 1.25)) / 1)) for k in range(31)]
    g = [(x, max(y, yt + 30)) for x, y in g]
    for k in range(12, 31): g[k] = (g[k][0], g[11][1] - (k - 11) * 0.6)
    polyline(d, partial(g, clamp((t - sc['t0'] - 0.4) / 1.0)), VGOLD, 6, a)
    txt(d, x1 - 100, g[-1][1] + 14, 'GAINS', f('MONO', 22), VGOLD, a)
    steps = [C['reckless'], C['reckless'] + 0.5, C['dose'], C['dose'] + 0.6]
    lvl = sum(1 for s in steps if t >= s)
    if t >= C['reckless'] - 0.2:
        ys = [yb - 30 - 30 * i for i in range(5)]; pts = [(x0, ys[0])]
        for i in range(1, 5):
            xs = lerp(x0, x1, 0.4 + 0.15 * (i - 1))
            if i <= lvl: pts += [(xs, ys[i - 1]), (xs, ys[i])]
        pts += [(lerp(x0, x1, min(1, 0.4 + 0.15 * lvl)), ys[lvl])]
        polyline(d, pts, RED, 6, 1); txt(d, lerp(x0, x1, min(1, 0.4 + 0.15 * lvl)) + 10, ys[lvl] - 14, 'DOSE', f('MONO', 22), RED)
    if t >= C['stall']: tag(d, 560, 1000, 'PLATEAU', VGOLD, 24, appear(t, C['stall']))
    for i, (lb, tt) in enumerate([('HEART', C['heart']), ('KIDNEYS', C['kidneys'])]):
        if t < tt: continue
        aa = appear(t, tt); y = 1218 + i * 70
        txt(d, 110, y, lb, f('MONO', 28), CREAM, aa)
        load = 0.25 + 0.17 * lvl + (0.12 if t >= C['exacerbated'] else 0)
        col = mix(CYAN, RED, (load - 0.3) / 0.5)
        d.rectangle([330, y + 2, 980, y + 40], outline=A(GRID, aa), width=2)
        lit_bar(d, 334, y + 6, lerp(334, 976, clamp(load) * expo((t - tt) / 0.5)), y + 36, col, aa)
    if t >= C['exacerbated']: tag(d, 760, 1170, 'LOAD ↑', RED, 24, appear(t, C['exacerbated']))
def sc_scale(im, d, t, sc):  # C corner card (left)
    x0, y0 = sc['box'][:2]
    v = 15.0 * expo((t - C['15']) / 0.7) if t >= C['15'] else 0.0
    s = f'+{v:4.1f}'
    txt(d, x0 + 34, y0 + 62, s, f('BEB', 150), CYAN)
    if GL: GL.text((x0 + 34, y0 + 62), s, font=f('BEB', 150), fill=A(CYAN, 0.7))
    txt(d, x0 + 34 + tw(d, s, f('BEB', 150)) + 10, y0 + 156, 'LB', f('BEB', 56), CYAN)
    txt(d, x0 + 36, y0 + 236, 'BODYWEIGHT · SCALE', f('MONO', 22), DIM)
    if t >= C['Ronnie']:
        flag(d, (x0 + 22, y0 + 60, x0 + 380, y0 + 226), C['Ronnie'], t, RED)
        tag(d, x0 + 34, y0 + 272, '≠ PRO STAGE', RED, 24, appear(t, C['Coleman']))
def sc_dots(im, d, t, sc):  # D full takeover
    kicker(d, 90, 392, '10,000 LIFTERS', VGOLD, 1)
    n = 100; sp = 9; gx, gy = 90, 470; p = clamp((t - sc['t0']) / 0.35)
    rows = int(p * n)
    for r in range(rows):
        y = gy + r * sp
        d.line([(gx, y), (gx + (n - 1) * sp, y)], fill=A((86, 92, 112), 1), width=4)
    # dot texture: punch gaps with background columns
    for c in range(n - 1): d.line([(gx + c * sp + 5, gy - 2), (gx + c * sp + 5, gy + rows * sp)], fill=A(DEEP, 1), width=4)
    tt = sc['t1'] - 0.75
    if t >= tt:
        a = appear(t, tt, 0.1); x, y = gx + 67 * sp, gy + 41 * sp
        d.rectangle([x - 4, y - 4, x + 6, y + 6], fill=A(RED, a)); GL.ellipse([x - 22, y - 22, x + 24, y + 24], fill=A(RED, a))
        flag(d, (x - 30, y - 30, x + 32, y + 32), tt, t, RED, 14)
        tag(d, x + 44, y - 22, '1 IN 10,000', RED, 30, a)
# --- top band / chapter tracker ---
BAND = (8, 250, W, 340)
CH = [('3 MO', 'first3', '6months'), ('6 MO', '6months', 'Then'), ('1 YR', 'Then', 'And5'), ('5 YR', 'And5', 'Now2')]
NODE_X = [430, 600, 770, 940]
def topic_band(im, d, t):
    if t < HOOK_END or t >= C['break'] + 0.2: return
    a = clamp((t - HOOK_END) / 0.15) * (1 - clamp((t - C['break']) / 0.2))
    x0, y0, x1, y1 = BAND
    d.rectangle([x0, y0, x1, y1], fill=NAVY + (int(228 * a),))
    d.line([(56, 270), (96, 270)], fill=A(GOLD, a), width=4); txt(d, 108, 257, '@coach.agz', f('MONO', 24), GOLD, a)
    fn = f('BAR', 60); s1 = 'Realistic muscle on '; txt(d, 56, 274, s1, fn, CREAM, a); txt(d, 56 + tw(d, s1, fn), 274, 'GEAR', fn, VGOLD, a)
def tracker(im, d, t):
    t0 = C['break']; t1 = C['Now2']
    if t < t0 or t > t1 + 0.5: return
    a = clamp((t - t0) / 0.2); hand = clamp((t - t1) / 0.45)  # handoff into the reveal rows
    x0, y0, x1, y1 = BAND
    d.rectangle([x0, y0, x1, y1], fill=NAVY + (int(228 * a * (1 - hand)),))
    txt(d, 56, 258, '@coach.agz', f('MONO', 22), GOLD, a * (1 - hand)); txt(d, 56, 288, 'THE TIMELINE', f('BEB', 46), CREAM, a * (1 - hand))
    lp_ = clamp((t - t0) / 0.8); d.line([(NODE_X[0], 295), (lerp(NODE_X[0], NODE_X[-1], lp_), 295)], fill=A(GRID, a * (1 - hand)), width=4)
    for i, (lb, ks, ke) in enumerate(CH):
        ta = [C['3mo'], C['6mo'], C['1yr'], C['5yr']][i]
        if t < ta: continue
        aa = appear(t, ta) * (1 - hand) if hand < 1 else 0
        active = C[ks] <= t < C[ke]; done = t >= C[ke]
        x = NODE_X[i]; col = VGOLD if (active or done) else STEEL
        fn = f('BEB', 44); w_ = tw(d, lb, fn)
        if active:
            lit_bar(d, x - w_ / 2 - 14, 270, x + w_ / 2 + 14, 322, VGOLD, aa); txt(d, x - w_ / 2, 274, lb, fn, INK, aa)
            if GL: GL.rectangle([x - w_ / 2 - 18, 266, x + w_ / 2 + 18, 326], outline=A(VGOLD, aa), width=10)
        else:
            d.rectangle([x - w_ / 2 - 14, 270, x + w_ / 2 + 14, 322], fill=A(NAVY, aa), outline=A(col, aa), width=3)
            txt(d, x - w_ / 2, 274, lb, fn, col if done else MUTED, aa)
# --- more T strips ---
def sc_assume(im, d, t, sc):
    strip_chrome(im, d, t, sc, 'ASSUMPTIONS', 'PROTOCOL')
    items = [('TRAINING', 'training'), ('NUTRITION', 'nutrition'), ('RECOVERY', 'recovery'), ('HEALTH MONITORING', 'health')]
    for i, (lb, k) in enumerate(items):
        x = 80 + (i % 2) * 470; y = 430 + (i // 2) * 76
        d.rectangle([x, y, x + 44, y + 44], outline=A(STEEL, 1), width=3)
        if t >= C[k]: check(d, x + 7, y + 6, GREEN, 1.0, appear(t, C[k], 0.1)); txt(d, x + 62, y + 2, lb, f('BARB', 44), WHITE, appear(t, C[k], 0.12))
        else: txt(d, x + 62, y + 2, lb, f('BARB', 44), (90, 94, 110))
    if t >= C['locked']:
        p = expo((t - C['locked']) / 0.18); y = 590
        x = lerp(1060, 620, p); xe = tag(d, x, y, 'LOCKED IN', VGOLD, 30, p)
        if t >= C['24']: tag(d, xe + 12, y, '24/7', RED, 30, appear(t, C['24']))
def ccard_chrome(im, d, t, sc, label):
    x0, y0, x1, y1 = sc['box']
    p = expo((t - sc['t0'] - 0.07) / 0.22); dy = lerp(24, 0, p)
    pb = clamp((t - sc['t0']) / 0.1)
    frosted(im, (x0, y0 + dy, x1, y1 + dy), 0.9, 16)
    d.rounded_rectangle([x0, y0 + dy, x1, y1 + dy], radius=22, fill=A((12, 12, 14), 0.35 * p), outline=A((60, 60, 66), 0.8 * p), width=2)
    d.rounded_rectangle([x0, y0 + dy * 0.3, x0 + 10, lerp(y0, y1, pb) + dy * 0.3], radius=4, fill=A(CBAR, 1))
    if GL: GL.rectangle([x0, y0, x0 + 10, lerp(y0, y1, pb)], fill=A(CBAR, 0.9))
    if p > 0.3: tracked(d, x0 + 34, y0 + 22 + dy, label, f('BARB', 28), CRIMSON, p, 4)
    txt(d, x1 - 128, y1 - 34 + dy, '@COACH.AGZ', f('MONO', 16), DIM, p * 0.8)
    return p, dy
def sc_spark(im, d, t, sc):
    x0, y0, x1, y1 = sc['box']
    for i, (lb, k, col) in enumerate([('STRENGTH', 'strength', CYAN), ('FULLNESS', 'fuller', VGOLD), ('BODYWEIGHT', 'weight', CYAN)]):
        y = y0 + 80 + i * 74; a = 1 if t >= C[k] else 0.35
        txt(d, x0 + 34, y + 6, lb, f('BARB', 38), WHITE if t >= C[k] else (110, 112, 125))
        pts = [(x0 + 236 + j * 15, y + 44 - (j / 9) ** 1.4 * 40 - (3 if j % 3 == 1 else 0)) for j in range(10)]
        if t >= C[k]: polyline(d, partial(pts, clamp((t - C[k]) / 0.5)), col, 5)
        else: dashed(d, pts, (70, 74, 90), 2)
        if t >= C[k] + 0.4: arrow(d, x1 - 46, y + 44, x1 - 46, y + 4, GREEN, 5, appear(t, C[k] + 0.4), 14)
# --- A scenes ---
DOC = None
def make_doc():
    w_, h_ = 860, 372; im = Image.new('RGB', (w_, h_), (233, 231, 226)); d = ImageDraw.Draw(im)
    d.rectangle([0, 0, w_, 62], fill=COARED); d.text((22, 14), 'CLINICAL TRIAL · RESULT SUMMARY', font=f('MONO', 28), fill=WHITE)
    rows = [('PROTOCOL', 'Supraphysiological testosterone + training'), ('DURATION', '10 weeks'), ('OUTCOME', '+13.4 lb fat-free mass')]
    for i, (k, v) in enumerate(rows):
        y = 84 + i * 84; d.text((22, y + 8), k, font=f('MONO', 22), fill=(110, 110, 118))
        d.text((210, y), v, font=f('DMB' if i == 2 else 'DMR', 34 if i else 30), fill=INK if i != 2 else (20, 20, 26))
        d.line([(20, y + 70), (w_ - 20, y + 70)], fill=(205, 203, 198), width=2)
    d.text((22, h_ - 40), 'Bhasin et al. · NEJM 1996 · 600 mg/wk', font=f('MONO', 20), fill=(120, 120, 128))
    # scan texture
    arr = np.asarray(im).astype(np.int16); arr += np.random.default_rng(1).integers(-7, 7, arr.shape[:2])[..., None]
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).convert('RGBA')
DOCMASK = {}
def sc_study1(im, d, t, sc, lay):
    global DOC
    if DOC is None: DOC = make_doc()
    a_doc = appear(t, sc['t0'] + 0.15, 0.25) * (1 - 0.45 * appear(t, C['not13'], 0.4))
    if a_doc > 0:
        dd = DOC.copy(); m = Image.new('L', DOC.size, 0); md = ImageDraw.Draw(m)
        md.rectangle([0, 0, DOC.width, 62], fill=255)  # header first, rows reveal on cue
        for i, k in enumerate(['super', 'weeks10', '13']):
            if t >= C[k] - 0.1: md.rectangle([0, 76 + i * 84, DOC.width, 160 + i * 84], fill=int(255 * appear(t, C[k] - 0.1, 0.12)))
        if t >= C['13']: md.rectangle([0, DOC.height - 54, DOC.width, DOC.height], fill=255)
        dd.putalpha(Image.eval(m, lambda v: int(v * a_doc)))
        lay.alpha_composite(dd, (110, 470))
        if t >= C['13'] and t < C['not13'] + 0.3: flag(d, (300, 630, 900, 716), C['13'], t, RED)
    if t >= C['not13']:
        a = appear(t, C['not13'], 0.3); y = 892
        txt(d, 110, y, 'WHAT +13.4 LB FAT-FREE MASS IS MADE OF', f('MONO', 26), VGOLD, a)
        txt(d, 110, y + 36, 'ILLUSTRATIVE SPLIT · NOT MEASURED', f('MONO', 18), DIM, a)
        segs = [('WATER', 0.36, CYAN, 'water2'), ('GLYCOGEN', 0.18, VGOLD, 'glycogen2'), ('OTHER LEAN', 0.2, STEEL, 'other'), ('MUSCLE ?', 0.26, WHITE, 'permanent')]
        x = 110; xb = 970; yb0, yb1 = y + 82, y + 172
        d.rectangle([x, yb0, xb, yb1], outline=A(GRID, a), width=2)
        order = sorted(segs, key=lambda s: C[s[3]])
        xs = 110
        for lb, fr, col, k in segs:
            w_ = fr * (xb - 110)
            if t >= C[k]:
                p = expo((t - C[k]) / 0.3)
                if lb.startswith('MUSCLE'): hatch(d, xs + 2, yb0 + 2, xs + w_ * p - 2, yb1 - 2, WHITE, p)
                else:
                    lit_bar(d, xs + 2, yb0 + 2, xs + w_ * p - 2, yb1 - 2, col)
                    if GL: GL.rectangle([xs, yb0, xs + w_ * p, yb1], fill=A(col, 0.4))
                fn = f('MONO', 20); txt(d, xs + 6, yb1 + 10, lb, fn, col if col != STEEL else MUTED, p)
            xs += w_
        if t >= C['scale2']:
            mx0 = 110 + (1 - 0.26) * (xb - 110)
            flag(d, (mx0 - 6, yb0 - 10, xb + 6, yb1 + 10), C['scale2'], t, RED, 22)
            tag(d, mx0 - 70, yb0 - 62, 'UNMEASURED', RED, 24, appear(t, C['scale2'] + 0.1))
        for i, (lb, k) in enumerate([('AR SIGNALING', 'receptor'), ('PROTEIN SYNTHESIS', 'synthesis'), ('HYPERTROPHY', 'hypertrophy')]):
            if t >= C[k]:
                aa = appear(t, C[k]); x = 110 + [0, 270, 590][i]; yy = 1150
                d.rectangle([x, yy, x + [250, 300, 240][i], yy + 52], fill=A((10, 30, 22), aa), outline=A(GREEN, aa), width=2)
                txt(d, x + 14, yy + 12, lb, f('MONO', 22), GREEN, aa); arrow(d, x + [228, 278, 218][i], yy + 42, x + [228, 278, 218][i], yy + 10, GREEN, 4, aa, 10)
def sc_study2(im, d, t, sc):  # B, window left
    a = appear(t, sc['t0'] + 0.3, 0.25)
    kicker(d, 480, 384, 'EVIDENCE 02', VGOLD, a)
    headline(d, 480, 440, [[('SECOND', CREAM)], [('TRIAL', CREAM)], [('20 WEEKS', VGOLD)]], 100, a, 520)
    txt(d, 480, 740, 'Bhasin et al. · 2001 · 600 mg/wk', f('MONO', 20), DIM, appear(t, C['study2']))
    txt(d, 480, 790, 'Fat-free mass, lb', f('DMR', 30), MUTED, a)
    x0, x1, yb, yt = 140, 980, 1330, 990
    for k in (0, 5, 10, 15, 20):
        y = lerp(yb, yt, k / 20); d.line([(x0, y), (x1, y)], fill=A(GRID, a), width=1)
        txt(d, x0 - 50, y - 14, str(k), f('MONO', 20), DIM, a)
    bars = [('10 WK', 13.4, CYAN, sc['t0'] + 0.5, '13.4'), ('20 WK', 17.4, VGOLD, C['17'], '~17')]
    for i, (lb, v, col, tt, vs) in enumerate(bars):
        if t < tt: continue
        p = expo((t - tt) / 0.6); bx0 = 260 + i * 360; bx1 = bx0 + 220; top = lerp(yb, lerp(yb, yt, v / 20), p)
        lit_vbar(d, bx0, top, bx1, yb, col)
        if GL: GL.rectangle([bx0, top, bx1, yb], outline=A(col, 0.9), width=8)
        txt(d, bx0 + 110, top - 70, vs, f('BEB', 66), col, p, 'mt'); txt(d, bx0 + 110, yb + 10, lb, f('MONO', 24), CREAM, p, 'mt')
    if t >= C['weeks20']: tag(d, 860, 1000, '2× TIME', CYAN, 22, appear(t, C['weeks20']))
    if t >= C['guaranteed']:
        p = appear(t, C['guaranteed'], 0.3); bx0 = 620; top = lerp(yb, yt, 17.4 / 20); mid = lerp(yb, yt, 11 / 20)
        hatch(d, bx0, top, bx0 + 220, top + (mid - top) * p, RED, p)
        tag(d, 846, int(top) + 40, 'NOT ALL', RED, 22, p); tag(d, 846, int(top) + 84, 'TISSUE', RED, 22, p)
def sc_curve(im, d, t, sc):
    for i, (lb, k) in enumerate([('DELTS', 'Delt'), ('CHEST', 'chest'), ('BACK', 'back'), ('LEGS', 'legs')]):
        if t >= C[k] - 0.05: tag(d, 100 + i * 170, 470, lb, VGOLD, 30, appear(t, C[k] - 0.05))
    if t >= C['thicker']: check(d, 790, 478, GREEN, 1.0, appear(t, C['thicker'])); txt(d, 836, 474, 'THICKER', f('MONO', 28), GREEN, appear(t, C['thicker']))
    x0, x1, yb, yt = 150, 970, 1180, 600
    a = appear(t, C['thicker'], 0.3)
    d.line([(x0, yb), (x1, yb)], fill=A(STEEL, a), width=3); d.line([(x0, yt), (x0, yb)], fill=A(STEEL, a), width=3)
    txt(d, x1 - 70, yb + 10, 'TIME', f('MONO', 22), DIM, a)
    txt(d, x0 - 10, yt - 40, 'MUSCLE', f('MONO', 22), DIM, a)
    for k in range(1, 4): d.line([(x0, lerp(yb, yt, k / 4)), (x1, lerp(yb, yt, k / 4))], fill=A((34, 38, 50), a), width=1)
    real = [(lerp(x0, x1, k / 40), lerp(yb, yt, 0.55 * math.log1p(9 * k / 40) / math.log(10))) for k in range(41)]
    if t >= C['growth1']:
        polyline(d, partial(real, clamp((t - C['growth1']) / 1.2)), VGOLD, 7)
        if t >= C['growth1'] + 1.2: txt(d, x1 - 150, real[-1][1] - 50, 'REAL', f('BEB', 44), VGOLD, appear(t, C['growth1'] + 1.2))
    if t >= C['accelerating']:
        acc = [(lerp(x0, x1, k / 40), lerp(yb, yt, 0.04 * (math.exp(4.2 * k / 40) - 1))) for k in range(41)]
        p = clamp((t - C['accelerating']) / 1.2)
        pts = [q for q in partial(acc, p) if q[1] >= yt - 2]
        dashed(d, pts, RED, 5)
        if GL: dashed(GL, pts, RED, 10)
        if p >= 1 or (pts and pts[-1][1] <= yt + 2):
            tag(d, 180, 640, 'IF IT KEPT ACCELERATING', RED, 24, appear(t, C['accelerating'] + 0.5))
    if t >= C['600']:
        v = int(600 * expo((t - C['600']) / 0.8)); ex = lerp(x0, x1, 0.86)
        arrow(d, ex, yt + 40, ex, yt - 10, RED, 6, 1, 20)
        txt(d, ex - 140, yt + 60, f'{v} LB', f('BEB', 70), RED)
    if t >= C['forklift']:
        p = expo((t - C['forklift']) / 0.2); y = 1226; xe = lerp(100, 980, p)
        GL.rectangle([96, y - 6, xe + 4, y + 96], outline=A(RED, 1), width=10); lit_bar(d, 100, y, xe, y + 90, RED)
        if p > 0.6: txt(d, 128, y + 10, 'PROJECTION', f('BEB', 74), WHITE); txt(d, 128 + tw(d, 'PROJECTION ', f('BEB', 74)), y + 32, '≠ PHYSIOLOGY', f('MONO', 32), WHITE)
def sc_stack(im, d, t, sc):
    strip_chrome(im, d, t, sc, 'YEAR 1 · WHAT COMPOUNDS', 'BUILD')
    blocks = [('ADAPTATION', 'adaptation'), ('NUTRITION', 'nutrition2'), ('OVERLOAD', 'progressive'), ('PROTEIN', 'protein'), ('RECOVERY', 'recovery2'), ('CONSISTENCY', 'consistency')]
    bw, gap = 152, 8; x0 = 64
    for i, (lb, k) in enumerate(blocks):
        x = x0 + i * (bw + gap); yb = 560
        d.rectangle([x, 470, x + bw, yb], outline=A((60, 64, 80), 1), width=2)
        if t >= C[k]:
            p = clamp((t - C[k]) / 0.16); y = lerp(380, 470, p ** 2)  # drops in, hard land
            col = VGOLD if i % 2 == 0 else CYAN
            lit_bar(d, x + 3, y + 3, x + bw - 3, y + 87, col)
            if GL: GL.rectangle([x, y, x + bw, y + 90], outline=A(col, 0.8), width=6)
            fn = f('BARB', 30 if len(lb) < 10 else 26); txt(d, x + bw / 2, y + 45, lb, fn, INK, 1, 'mm')
    n = sum(1 for _, k in blocks if t >= C[k])
    xe = x0 + n * (bw + gap) - gap
    if n: lit_bar(d, x0, 590, xe, 600, GREEN); txt(d, x0, 610, 'TRAINING AGE ↑', f('MONO', 22), GREEN, 1)
def sc_mtor(im, d, t, sc):  # crimson card look
    x0, y0, x1, y1 = 90, 400, 990, 1320
    a = appear(t, sc['t0'] + 0.1, 0.25)
    d.rounded_rectangle([x0, y0, x1, y1], radius=26, fill=A((12, 12, 14), 0.9 * a))
    d.rounded_rectangle([x0, y0, x0 + 12, y1], radius=4, fill=A(CBAR, a))
    tracked(d, x0 + 330, y0 + 34, 'THE MECHANISM', f('BEB', 44), CRIMSON, a, 6)
    steps = [('TENSION', 'Mechanical load on the fibre', 'tension'), ('mTOR', 'Growth signalling hub', 'mTOR'), ('MPS', 'Muscle protein synthesis', 'synthesis2'), ('HYPERTROPHY', 'Fibre gets bigger', 'synthesis2')]
    for i, (h1, sub, k) in enumerate(steps):
        tt = C[k] + (0.7 if i == 3 else 0) if i else C['fibers']
        if t < tt: continue
        aa = appear(t, tt, 0.2); y = y0 + 120 + i * 196; dy = lerp(14, 0, aa)
        d.rounded_rectangle([250, y + dy, 830, y + 130 + dy], radius=18, outline=A(WHITE, aa), width=3, fill=A((29, 29, 33), aa))
        d.ellipse([196, y + 40 + dy, 246, y + 90 + dy], fill=A(CBAR, aa)); txt(d, 221, y + 65 + dy, str(i + 1), f('BEB', 40), WHITE, aa, 'mm')
        txt(d, 540, y + 20 + dy, h1, f('BEB', 66), CREAM if i < 3 else VGOLD, aa, 'mt'); txt(d, 540, y + 88 + dy, sub, f('DMR', 26), (207, 202, 196), aa, 'mt')
        if i: arrow(d, 540, y - 64, 540, y - 4, CRIMSON, 5, aa, 16)
    txt(d, x1 - 150, y1 - 40, '@COACH.AGZ', f('MONO', 18), DIM, a)
def bell_pts(x0, x1, yb, yt, mu=6, sd=3.2, top=30):
    return [(lerp(x0, x1, v / top), yb - (yb - yt) * math.exp(-((v - mu) ** 2) / (2 * sd ** 2))) for v in np.linspace(0, top, 90)]
def sc_bell(im, d, t, sc):  # B, window right
    a = appear(t, sc['t0'] + 0.3, 0.25)
    kicker(d, 80, 384, '12-WEEK GAINS', VGOLD, a)
    if t >= C['20to30']:
        aa = appear(t, C['20to30'], 0.2)
        headline(d, 80, 440, [[('20–30 LB', RED)], [('IN 12 WEEKS?', CREAM)]], 104, aa, 520)
    else: headline(d, 80, 440, [[('WHAT\'S', CREAM)], [('NORMAL?', VGOLD)]], 104, a, 520)
    txt(d, 80, 670, 'Illustrative distribution', f('DMR', 28), MUTED, a)
    x0, x1, yb, yt = 110, 980, 1240, 1000
    d.line([(x0, yb), (x1, yb)], fill=A(STEEL, a), width=3)
    for v in (0, 10, 20, 30): x = lerp(x0, x1, v / 30); txt(d, x - 14, yb + 8, f'{v}', f('MONO', 22), DIM, a)
    txt(d, x0, yb + 40, 'LB', f('MONO', 20), DIM, a)
    pts = bell_pts(x0, x1, yb, yt); pp = partial(pts, clamp((t - sc['t0'] - 0.4) / 1.0))
    if len(pp) > 2: d.polygon(pp + [(pp[-1][0], yb), (x0, yb)], fill=A(VGOLD, 0.22 * a)); polyline(d, pp, VGOLD, 5, a)
    if t >= C['20to30']:
        p = appear(t, C['20to30'], 0.25); rx0, rx1 = lerp(x0, x1, 20 / 30), x1
        d.rectangle([rx0, yt - 20, rx1, yb], fill=A(RED, 0.18 * p)); flag(d, (rx0, yt - 20, rx1, yb), C['20to30'], t, RED, 24)
        tag(d, rx0 + 14, yt + 4, 'NO STUDY', RED, 24, p)
    if t >= C['behemoths']:
        p = appear(t, C['behemoths']); x = lerp(x0, x1, 27 / 30); y = yb - 16
        d.ellipse([x - 10, y - 10, x + 10, y + 10], fill=A(VGOLD, p)); GL.ellipse([x - 22, y - 22, x + 22, y + 22], fill=A(VGOLD, p))
        txt(d, x - 210, y - 52, 'SOCIAL MEDIA', f('MONO', 22), VGOLD, p)
    for i, (lb, k) in enumerate([('GENETICS', 'genetics'), ('TRAINING HISTORY', 'history'), ('STARTING SIZE', 'size')]):
        if t >= C[k]: tag(d, 260 + [0, 190, 470][i], 1300, lb, CYAN, 22, appear(t, C[k]))
def sc_5yr(im, d, t, sc):
    strip_chrome(im, d, t, sc, 'GAIN PER YEAR · YEARS 1–5', 'ILLUSTRATIVE')
    vals = [1.0, 0.58, 0.38, 0.27, 0.2]; bx, bw, yb, ht = 90, 82, 640, 190
    for i, v in enumerate(vals):
        tt = sc['t0'] + 0.3 + i * 0.18
        if t < tt: continue
        p = expo((t - tt) / 0.4); x = bx + i * (bw + 26); top = yb - ht * v * p
        lit_vbar(d, x, top, x + bw, yb, VGOLD if i == 0 else mix(VGOLD, CYAN, i / 4))
        txt(d, x + bw / 2, yb + 2 - 0, '', f('MONO', 20), DIM)
        txt(d, x + bw / 2, top - 30, f'Y{i + 1}', f('MONO', 22), CREAM, p, 'mt')
    if t >= C['harder']:  # cost-per-lb line rising across the bars
        pts = [(bx + i * (bw + 26) + bw / 2, yb - 40 - 34 * i) for i in range(5)]
        polyline(d, partial(pts, clamp((t - C['harder']) / 0.8)), RED, 5)
        tag(d, 90, 420, 'COST PER LB ↑', RED, 24, appear(t, C['harder'] + 0.5))
    # right: the 15 lb / 3 months fantasy, compounded
    if t >= C['15b']:
        a = appear(t, C['15b']); x = 640
        txt(d, x, 430, '15 LB EVERY 3 MO', f('MONO', 26), CREAM, a)
        txt(d, x, 468, '× 20 QUARTERS', f('MONO', 26), DIM, a)
        if t >= C['zip']:
            v = int(300 * expo((t - C['zip']) / 0.7)); aa = appear(t, C['zip'])
            txt(d, x, 506, f'+{v} LB', f('BEB', 110), RED, aa)
            if GL: GL.text((x, 506), f'+{v} LB', font=f('BEB', 110), fill=A(RED, 0.6 * aa))
            if t >= C['zip'] + 0.9: cross(d, x + 330, 540, RED, 1.4, appear(t, C['zip'] + 0.9))
def sc_risk(im, d, t, sc):
    x0, x1, yb, yt = 150, 970, 820, 500
    a = appear(t, sc['t0'] + 0.15, 0.3)
    txt(d, 100, 452, 'CUMULATIVE CARDIOVASCULAR LOAD', f('MONO', 24), CREAM, a)
    d.line([(x0, yb), (x1, yb)], fill=A(STEEL, a), width=3)
    for i in range(5):
        x = lerp(x0, x1, (i + 0.5) / 5); txt(d, x, yb + 8, f'Y{i + 1}', f('MONO', 22), DIM, a, 'mt')
    if t >= C['optimized']:
        p = clamp((t - C['optimized']) / 1.6 if t < C['accumulate'] else 1)
        pts = [(lerp(x0, x1, k / 30), yb - (yb - yt - 20) * (k / 30) ** 1.5) for k in range(31)]
        pp = partial(pts, p if t < C['accumulate'] else 1)
        if len(pp) > 1:
            d.polygon(pp + [(pp[-1][0], yb), (x0, yb)], fill=A(RED, 0.28)); polyline(d, pp, RED, 6)
        if t >= C['accumulate']: tag(d, 640, 520, 'STILL ACCUMULATES', RED, 24, appear(t, C['accumulate']))
    for i in range(5):
        tt = C['bloodwork2'] + i * 0.18
        if t >= tt:
            x = lerp(x0, x1, (i + 0.5) / 5) - 52; aa = appear(t, tt)
            d.rectangle([x, yb + 44, x + 104, yb + 84], fill=A((10, 30, 22), aa), outline=A(GREEN, aa), width=2)
            check(d, x + 8, yb + 50, GREEN, 0.8, aa); txt(d, x + 40, yb + 52, 'LABS' if t < C['EKGs'] else 'EKG', f('MONO', 20), GREEN, aa)
    rows = [('HEMATOCRIT', 'hct'), ('LIPIDS', 'lipids'), ('BLOOD PRESSURE', 'bp'), ('KIDNEY FUNCTION', 'kidney2'), ('HEART HEALTH', 'heart2')]
    for i, (lb, k) in enumerate(rows):
        y = 960 + i * 70
        if t < C[k] - 0.05: continue
        aa = appear(t, C[k] - 0.05)
        d.line([(100, y + 58), (980, y + 58)], fill=A(GRID, aa), width=1)
        txt(d, 100, y + 8, lb, f('BARB', 42), WHITE, aa)
        rng = np.random.default_rng(i + 4); sp = [(560 + j * 26, y + 30 + rng.uniform(-12, 12) - j * 1.2) for j in range(10)]
        polyline(d, sp, CYAN, 3, aa)
        tag(d, 850, y + 6, 'TRACK', VGOLD, 22, aa)
REV_ROWS = [('3 MO', 3, 8, 'r3'), ('6 MO', 5, 12, 'r6'), ('1 YR', 10, 20, 'r12'), ('5 YR', 20, 40, 'r5y')]
def sc_reveal(im, d, t, sc):  # B, small window left
    a = appear(t, sc['t0'] + 0.3, 0.25)
    kicker(d, 410, 384, 'REALISTIC LEAN GAINS', VGOLD, a, 24)
    headline(d, 410, 430, [[('POUNDS OF', CREAM)], [('MUSCLE', VGOLD)]], 110, a, 600)
    for i, (lb, k) in enumerate([('UNTRAINED START', 'untrained'), ('AVERAGE GENETICS', 'average'), ('LOCKED IN', 'locked2')]):
        if t >= C[k]:
            aa = appear(t, C[k]); y = 650 + i * 58; check(d, 410, y, GREEN, 0.9, aa); txt(d, 456, y - 2, lb, f('MONO', 28), WHITE, aa)
    ax0, ax1 = 260, 990; ytop = 880
    for v in (0, 10, 20, 30, 40):
        x = lerp(ax0, ax1, v / 40); d.line([(x, ytop + 30), (x, ytop + 440)], fill=A((40, 44, 58), a), width=2)
        txt(d, x, ytop - 6, f'{v}', f('MONO', 22), DIM, a, 'mt')
    txt(d, ax1 - 4, ytop - 40, 'LB', f('MONO', 22), DIM, a, 'rt')
    hand = clamp((t - sc['t0']) / 0.5)
    for i, (lb, lo, hi, k) in enumerate(REV_ROWS):
        y = ytop + 50 + i * 104
        # labels arrive from the timeline tracker (handoff)
        lx = lerp(NODE_X[i] - 40, 70, ease_io(hand)); ly = lerp(274, y + 12, ease_io(hand))
        txt(d, lx, ly, lb, f('BEB', lerp(44, 60, hand)), VGOLD if t >= C[k] else CREAM)
        if t >= C[k]:
            p = expo((t - C[k]) / 0.7); xa = lerp(ax0, ax1, lo / 40); xb = lerp(xa, lerp(ax0, ax1, hi / 40), p)
            lit_bar(d, xa, y + 14, xb, y + 72, VGOLD)
            if GL: GL.rectangle([xa - 2, y + 12, xb + 2, y + 74], fill=A(VGOLD, 0.55))
            val = f'{lo}–{int(lerp(lo, hi, p))}'
            fn = f('BEB', 60)
            if xb + 14 + tw(d, val, fn) < 1050: txt(d, xb + 14, y + 12, val, fn, WHITE, p)
            else: txt(d, xa + 14, y + 12, val, fn, INK, p)
def sc_outlier(im, d, t, sc):  # C card right
    x0, y0, x1, y1 = sc['box']
    gx0, gx1, gyb, gyt = x0 + 90, x1 - 30, y1 - 50, y0 + 80
    for v in (0, 20, 40):
        y = lerp(gyb, gyt, v / 40); d.line([(gx0, y), (gx1, y)], fill=A((48, 52, 66), 1), width=1); txt(d, gx0 - 56, y - 12, f'{v}', f('MONO', 20), DIM)
    rng = np.random.default_rng(11); n = int(42 * clamp((t - sc['t0'] - 0.2) / 0.6))
    for i in range(42):
        v = float(np.clip(rng.normal(6.5, 2.2), 1, 13)); x = lerp(gx0 + 10, gx1 - 70, rng.uniform())
        if i < n: y = lerp(gyb, gyt, v / 40); d.ellipse([x - 6, y - 6, x + 6, y + 6], fill=A(CYAN, 0.85))
    if t >= C['40']:
        x, y = gx1 - 30, lerp(gyb, gyt, 40 / 40) + 6; p = appear(t, C['40'])
        d.ellipse([x - 9, y - 9, x + 9, y + 9], fill=A(RED, p)); GL.ellipse([x - 20, y - 20, x + 20, y + 20], fill=A(RED, p))
        flag(d, (x - 24, y - 24, x + 24, y + 24), C['40'], t, RED, 12)
        tag(d, gx0 - 10, y - 18, '+40 LB · OUTLIER', RED, 20, p)
    if t >= C['averagemale']:
        p = appear(t, C['averagemale']); ya, yb_ = lerp(gyb, gyt, 13 / 40), gyb + 4
        d.rectangle([gx0, ya, gx1 - 60, yb_], outline=A(VGOLD, p), width=3)
        txt(d, gx0 + 8, ya - 34, 'AVERAGE MALE', f('MONO', 20), VGOLD, p)
def sc_gantt(im, d, t, sc):
    strip_chrome(im, d, t, sc, 'COACH AGZ · 10 YEARS', 'ON / OFF · ILLUSTRATIVE')
    x0, x1 = 80, 1000; y = 470
    on = [(0, 1.2), (1.8, 3.0), (3.6, 4.4), (5.0, 6.6), (7.2, 8.4), (9.0, 10)]
    sweep = clamp((t - C['10y'] + 0.4) / 1.4) * 10
    d.rectangle([x0, y, x1, y + 70], outline=A(GRID, 1), width=2)
    for s, e in on:
        if sweep <= s: continue
        e2 = min(e, sweep); xa, xb = lerp(x0, x1, s / 10), lerp(x0, x1, e2 / 10)
        lit_bar(d, xa + 2, y + 4, xb - 2, y + 66, VGOLD)
        if GL: GL.rectangle([xa, y, xb, y + 70], fill=A(VGOLD, 0.4))
    for k in range(11):
        x = lerp(x0, x1, k / 10); d.line([(x, y + 70), (x, y + 82)], fill=A(STEEL, 1), width=2)
        if k % 2 == 0: txt(d, x, y + 88, f'Y{k}', f('MONO', 20), DIM, 1, 'mt')
    txt(d, x0, 600, 'ON', f('MONO', 22), VGOLD); d.rectangle([x0 + 44, 606, x0 + 70, 624], fill=A(VGOLD, 1))
    txt(d, x0 + 100, 600, 'OFF', f('MONO', 22), DIM); d.rectangle([x0 + 160, 606, x0 + 186, 624], outline=A(GRID, 1), width=2)
    if t >= C['suboptimal']: tag(d, 640, 594, 'STILL BUILDING', CYAN, 24, appear(t, C['suboptimal']))
def sc_compare(im, d, t, sc):
    cols = [(100, 'CLIENT WANTS', RED, '+20–30', '2030'), (560, 'REALISTIC', VGOLD, '+5–12', 'sixmo')]
    for x, hd, col, big, k in cols:
        tt = C[k] + (0.5 if k == 'sixmo' else 0)
        a0 = appear(t, sc['t0'] + 0.15, 0.25)
        d.rectangle([x, 474, x + 420, 800], fill=A((24, 26, 34), 0.9 * a0))
        d.line([(x, 470), (x + 420, 470)], fill=A((70, 74, 90), a0), width=6)
        txt(d, x + 24, 706, 'LB · FIRST 6 MONTHS', f('MONO', 24), MUTED, a0)
        if t < tt - 0.05:
            txt(d, x + 24, 494, hd, f('BEB', 54), (110, 112, 125), a0); txt(d, x + 24, 566, '+ ?', f('BEB', 130), (70, 74, 90), a0)
            continue
        a = appear(t, tt - 0.05, 0.2)
        d.line([(x, 470), (x + lerp(0, 420, expo((t - tt + 0.05) / 0.3)), 470)], fill=A(col, 1), width=6)
        if GL: GL.line([(x, 470), (x + 420, 470)], fill=A(col, a), width=10)
        txt(d, x + 24, 494, hd, f('BEB', 54), col, a); txt(d, x + 24, 566, big, f('BEB', 130), WHITE, a)
        if k == '2030': cross(d, x + 360, 500, RED, 1.2, appear(t, C['sixmo'] + 0.6))
        else: check(d, x + 360, 498, GREEN, 1.2, appear(t, tt + 0.3))
    # day 90 vs year 5 (callback to the reveal numbers)
    for i, (lb, lo, hi, k, col) in enumerate([('DAY 90', 3, 8, '90', CYAN), ('YEAR 5', 20, 40, 'fifth', VGOLD)]):
        if t < C[k]: continue
        p = expo((t - C[k]) / 0.6); y = 860 + i * 110
        txt(d, 100, y + 8, lb, f('BEB', 60), WHITE, appear(t, C[k]))
        xa = lerp(300, 980, lo / 40); xb = lerp(xa, lerp(300, 980, hi / 40), p)
        lit_bar(d, xa, y + 10, xb, y + 70, col)
        txt(d, xb + 12 if i == 0 else xb - 170, y + 10, f'{lo}–{hi} LB', f('BEB', 56), WHITE if i == 0 else INK, p)
    if t >= C['goal']:
        p = expo((t - C['goal']) / 0.2); y = 1130; xe = lerp(100, 980, p)
        GL.rectangle([96, y - 6, xe + 4, y + 96], outline=A(RED, 1), width=10); lit_bar(d, 100, y, xe, y + 90, RED)
        if p > 0.6: txt(d, 128, y + 10, 'KEEPABLE', f('BEB', 74), WHITE); txt(d, 128 + tw(d, 'KEEPABLE ', f('BEB', 74)), y + 32, '> FAST', f('MONO', 32), WHITE)
def sc_quad(im, d, t, sc):  # B, window right
    a = appear(t, sc['t0'] + 0.3, 0.25)
    kicker(d, 80, 384, 'GENETIC CEILING', VGOLD, a)
    headline(d, 80, 440, [[('RESPONSE', CREAM)], [('× TOLERANCE', VGOLD)]], 100, a, 520)
    x0, x1, y0, y1 = 170, 950, 985, 1350; mx, my = (x0 + x1) / 2, (y0 + y1) / 2
    d.rectangle([x0, y0, x1, y1], outline=A(STEEL, a), width=3); d.line([(mx, y0), (mx, y1)], fill=A(STEEL, a), width=2); d.line([(x0, my), (x1, my)], fill=A(STEEL, a), width=2)
    txt(d, x0 - 50, my, 'RESPONSE', f('MONO', 20), DIM, a, 'mm') if False else None
    txt(d, x0, y1 + 8, 'TOLERANCE →', f('MONO', 20), DIM, a)
    d.text((x0 - 34, y0), '↑', font=f('MONO', 30), fill=A(DIM, a)); txt(d, x0 - 140, y0 + 40, 'RESP.', f('MONO', 20), DIM, a)
    quads = [('AVERAGE', x0, my, mx, y1, STEEL, None), ('HYPER-\nRESPONDER', x0, y0, mx, my, CYAN, 'respond'), ('HYPER-\nTOLERATOR', mx, my, x1, y1, CYAN, 'tolerate'), ('BOTH', mx, y0, x1, my, VGOLD, 'combination')]
    lit = None
    for nm, qa, qb, qc, qd, col, k in quads:
        on = k and t >= C[k]
        if on: lit = (qa, qb, qc, qd, col, k)
    if lit:
        qa, qb, qc, qd, col, k = lit; p = appear(t, C[k], 0.18)
        d.rectangle([qa + 4, qb + 4, qc - 4, qd - 4], fill=A(col, 0.14 * p), outline=A(col, p), width=4)
        if GL: GL.rectangle([qa + 4, qb + 4, qc - 4, qd - 4], outline=A(col, p), width=8)
    for nm, qa, qb, qc, qd, col, k in quads:
        on = k and t >= C[k]
        d.multiline_text((qa + 24, qb + 20), nm, font=f('BEB', 50), fill=A(col if on else (90, 94, 110), a), spacing=0)
    if t >= C['Phil']: tag(d, mx + 24, y0 + 100, '1 OF 1', VGOLD, 28, appear(t, C['Phil']))
    if t >= C['Ronnie2']: tag(d, mx + 160, y0 + 100, 'ELITE', RED, 28, appear(t, C['Ronnie2']))
def sc_race(im, d, t, sc):
    a = appear(t, sc['t0'] + 0.15, 0.3)
    marks = [('6 MO', 'six3'), ('1 YR', 'year3'), ('3 YR', 'three3'), ('5 YR', 'five3')]
    lanes = [('HYPER-RESPONDER · LOW DOSE', VGOLD, 'low'), ('COACH AGZ · EVERYTHING LOCKED', CYAN, 'training3')]
    ax0, ax1 = 100, 980
    for i, (lb, col, k) in enumerate(lanes):
        y = 470 + i * 140
        aa = appear(t, sc['t0'] + 0.15 + 0.12 * i, 0.25); txt(d, ax0, y, lb, f('MONO', 26), col if t >= C[k] - 0.1 else (110, 112, 125), aa)
        d.rectangle([ax0, y + 44, ax1, y + 104], outline=A(GRID, aa), width=2)
        if t < C[k] - 0.1: continue
        if i == 0: g = 0.25 * appear(t, C['low'], 0.5) + 0.75 * expo((t - C['weeds']) / 1.4) if t >= C['low'] else 0
        else: g = 0.25 * expo((t - C['training3']) / 3.0)
        lit_bar(d, ax0 + 3, y + 48, lerp(ax0 + 3, ax1 - 3, clamp(g)), y + 100, col)
        if GL: GL.rectangle([ax0, y + 46, lerp(ax0, ax1, clamp(g)), y + 102], fill=A(col, 0.45))
    if t >= C['fourth']:
        p = appear(t, C['fourth']); x = lerp(ax0, ax1, 0.25)
        d.line([(x, 600), (x, 770)], fill=A(RED, p), width=3); tag(d, x + 12, 714, '¼ THE GROWTH', RED, 26, p)
    for i, (lb, k) in enumerate(marks):
        if t >= C[k]: tag(d, 100 + i * 150, 790, lb, STEEL if t >= C[marks[min(i + 1, 3)][1]] and i < 3 else VGOLD, 24, appear(t, C[k]))
    items = [('TRAINING', 'training3'), ('NUTRITION', 'nutrition3'), ('RECOVERY', 'recovery3'), ('SLEEP', 'sleep'), ('BLOODWORK', 'bloodwork3'), ('INTENSITY', 'hard')]
    if t >= C['training3']: txt(d, 100, 870, 'MY INPUTS', f('MONO', 24), CYAN, appear(t, C['training3']))
    for i, (lb, k) in enumerate(items):
        if t < C[k]: continue
        aa = appear(t, C[k]); x = 100 + (i % 3) * 300; y = 916 + (i // 3) * 66
        check(d, x, y + 4, GREEN, 0.9, aa); txt(d, x + 44, y, lb, f('BARB', 42), WHITE, aa)
    if t >= C['fourth'] + 0.3:
        aa = appear(t, C['fourth'] + 0.3); y = 1090
        txt(d, 100, y, '4×', f('BEB', 200), VGOLD, aa)
        if GL: GL.text((100, y), '4×', font=f('BEB', 200), fill=A(VGOLD, 0.5 * aa))
        txt(d, 330, y + 50, 'GROWTH RATE GAP', f('MONO', 30), CREAM, aa); txt(d, 330, y + 96, 'SAME TIMELINE · DIFFERENT GENETICS', f('MONO', 22), DIM, aa)
def sc_amp(im, d, t, sc):
    strip_chrome(im, d, t, sc, 'GEAR = AMPLIFIER', 'SIGNAL')
    for i, (amp_in, col, k, lb) in enumerate([(0.25, CYAN, 'optimize', 'AVERAGE'), (0.8, VGOLD, 'amplify', 'ELITE')]):
        if t < C[k]: continue
        a = appear(t, C[k]); y = 470 + i * 104
        txt(d, 70, y - 8, lb, f('MONO', 20), col, a)
        pts = [(70 + j * 3, y + 30 - math.sin(j * 0.32 + t * 6) * 26 * amp_in) for j in range(80)]
        polyline(d, pts, col, 4, a)
        tx = 380; d.polygon([(tx, y - 14), (tx, y + 74), (tx + 110, y + 30)], outline=A(WHITE, a), fill=A((20, 22, 30), a)); d.line([(tx, y - 14), (tx, y + 74), (tx + 110, y + 30), (tx, y - 14)], fill=A(WHITE, a), width=4)
        txt(d, tx + 12, y + 16, 'GEAR', f('MONO', 20), WHITE, a)
        arrow(d, 320, y + 30, 372, y + 30, STEEL, 3, a, 10)
        p = clamp((t - C[k] - 0.2) / 0.5)
        out = [(520 + j * 6, y + 30 - math.sin(j * 0.32 * 0.5 + t * 6) * 40 * amp_in * 1.6) for j in range(int(80 * p))]
        polyline(d, out, col, 5, a)
def sc_donut(im, d, t, sc):
    x0, y0, x1, y1 = sc['box']; cx, cy, r = x0 + 150, y0 + 190, 104
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=A((54, 58, 72), 1), width=26)
    p80 = expo((t - C['80']) / 0.7) if t >= C['80'] else 0; p85 = expo((t - C['85']) / 0.4) if t >= C['85'] else 0
    if p80 > 0:
        d.arc([cx - r, cy - r, cx + r, cy + r], -90, -90 + 360 * 0.80 * p80, fill=A(RED, 1), width=26)
        if GL: GL.arc([cx - r, cy - r, cx + r, cy + r], -90, -90 + 360 * 0.80 * p80, fill=A(RED, 1), width=34)
    if p85 > 0: d.arc([cx - r, cy - r, cx + r, cy + r], -90 + 288, -90 + 288 + 18 * p85, fill=A(mix(RED, WHITE, 0.45), 1), width=26)
    s = '80–85%' if t >= C['85'] else f'{int(80 * p80)}%'
    txt(d, cx, cy, s, f('BEB', 60 if t >= C['85'] else 70), WHITE, 1, 'mm')
    txt(d, x0 + 290, y0 + 120, 'OF LIFTERS', f('MONO', 20), DIM); txt(d, x0 + 290, y0 + 150, 'WITHOUT', f('MONO', 20), DIM)
    txt(d, x0 + 290, y0 + 180, 'ELITE', f('BEB', 48), RED); txt(d, x0 + 290, y0 + 226, 'GENETICS', f('BEB', 48), RED)
    if t >= C['progress']:
        aa = appear(t, C['progress']); arrow(d, x0 + 300, y1 - 30, x0 + 300, y1 - 76, GREEN, 5, aa, 14); txt(d, x0 + 322, y1 - 70, 'STILL', f('MONO', 20), GREEN, aa); txt(d, x0 + 322, y1 - 44, 'PROGRESS', f('MONO', 20), GREEN, aa)
LOGO = None
def sc_cta(im, d, t, sc):
    global LOGO
    if LOGO is None:
        lg = Image.open(REPO + '/editing/brand/logo/coach-agz-logo-round.jpg').convert('RGB'); s_ = min(lg.size)
        lg = lg.crop(((lg.width - s_) // 2, (lg.height - s_) // 2, (lg.width + s_) // 2, (lg.height + s_) // 2)).resize((170, 170), Image.LANCZOS)
        m = Image.new('L', (170, 170), 0); ImageDraw.Draw(m).ellipse([0, 0, 169, 169], fill=255); lg.putalpha(m); LOGO = lg
    a = appear(t, sc['t0'] + 0.3, 0.25)
    lg = LOGO.copy(); lg.putalpha(lg.split()[3].point(lambda v: int(v * a))); im.alpha_composite(lg, (80, 1000))
    txt(d, 280, 1006, 'COACH AGZ', f('BEB', 60), GOLD, a); txt(d, 280, 1066, '@coach.agz', f('MONO', 24), GOLD, a)
    txt(d, 280, 1108, 'FREE · MUSCLE GROWTH TRACKING FRAMEWORK', f('MONO', 22), VGOLD, appear(t, C['framework']))
    if t >= C['Comment']:
        b = expo((t - C['Comment']) / 0.14); s_ = lerp(1.1, 1.0, b)
        fn = f('BEB', int(96 * s_)); label = 'COMMENT  "GROWTH"'; w_ = tw(d, label, fn)
        x = 80; y = 1190
        lit_bar(d, x, y, x + w_ + 48, y + int(112 * s_), VGOLD, b); d.text((x + 24, y + 6), label, font=fn, fill=A(INK, b))
        if GL: GL.rectangle([x - 4, y - 4, x + w_ + 52, y + int(112 * s_) + 4], outline=A(VGOLD, b), width=12)
# ---------------- scene table (output times) ----------------
def SC(kind, t0, t1, fn, **kw): return dict(kind=kind, t0=t0, t1=t1, fn=fn, **kw)
WIN_R = (636, 372, 1016, 940); WIN_L = (64, 372, 444, 940); WIN_S = (64, 372, 364, 822)
SCENES = [
    SC('T', HOOK_END, C['another'] + 0.35, sc_waffle),
    SC('T', C['three'] - 1.0, C['gear1'] + 0.3, sc_months),
    SC('A', C['promise'], C['That'] - 0.05, sc_sponge, hl='SCALE vs TISSUE', hr='SCAN 01'),
    SC('B', C['That'], C['steroids'] + 0.55, sc_dose, win=WIN_R),
    SC('C', C['Some'], C['Coleman'] + 0.45, sc_scale, box=(56, 360, 476, 700), label='SCALE READING'),
    SC('D', C['of1'], C['im'] - 0.02, sc_dots),
    SC('T', C['assuming'], C['Now1'] - 0.05, sc_assume),
    SC('C', C['first3'], C['controlled'] - 1.6, sc_spark, box=(604, 360, 1024, 640), label='FIRST 90 DAYS'),
    SC('A', C['controlled'] - 1.0, C['Alright2'] - 0.05, sc_study1, hl='CONTROLLED TRIAL', hr='EVIDENCE 01'),
    SC('B', C['Alright2'], C['Delt'] - 0.1, sc_study2, win=WIN_L),
    SC('A', C['Delt'] - 0.1, C['Then'] - 0.05, sc_curve, hl='GROWTH CURVE', hr='PROJECTION'),
    SC('T', C['adaptation'] - 0.6, C['consistency'] + 2.0, sc_stack),
    SC('M', C['fibers'] - 0.5, C['Theres'] - 0.05, sc_mtor),
    SC('B', C['Theres'], C['And5'] - 0.05, sc_bell, win=WIN_R),
    SC('T', C['fiveyrs'], C['harder'] + 0.45, sc_5yr),
    SC('A', C['ignore'] - 0.9, C['Now2'] - 0.05, sc_risk, hl='5-YEAR EXPOSURE', hr='RISK MONITOR'),
    SC('B', C['Now2'], C['clarify'] - 0.4, sc_reveal, win=WIN_S),
    SC('C', C['clarify'] - 0.2, C['how'] - 0.1, sc_outlier, box=(604, 360, 1024, 760), label='FIRST-CYCLE GAINS'),
    SC('T', C['gear10'] - 0.2, C['linear'], sc_gantt),
    SC('A', C['client'] - 0.6, C['Its'] - 0.05, sc_compare, hl='CLIENT INTAKE', hr='EXPECTATION CHECK'),
    SC('B', C['ceiling'] - 0.5, C['Honestly'] - 0.05, sc_quad, win=WIN_R),
    SC('A', C['clients'] - 0.4, C['Anyways'] - 0.05, sc_race, hl='SAME TIMELINE', hr='RESPONDER GAP'),
    SC('T', C['optimize'] - 0.3, C['Your'], sc_amp),
    SC('C', C['80'] - 0.6, C['day'] + 0.3, sc_donut, box=(56, 360, 516, 700), label='GENETIC CEILING'),
    SC('B', CTA_IN, DUR + 1, sc_cta, win=(240, 372, 840, 952), cta=True),
]
def active(t, kinds=None):
    return [s for s in SCENES if s['t0'] <= t < s['t1'] + 0.3 and (kinds is None or s['kind'] in kinds)]
# ---------------- text hook (engine) ----------------
HOOK = ['Real muscle on ', 'GEAR', '3 months vs 5 years']
def text_hook(im, d, t):
    if t >= HOOK_END + 0.15: return
    a = 1 - clamp((t - HOOK_END) / 0.15)
    s_ = lerp(1.0, 1.04, clamp(t / HOOK_END))
    fn = f('BAR', int(104 * s_))
    l1 = tw(d, HOOK[0] + HOOK[1], fn); l2 = tw(d, HOOK[2], fn); lh = 104 * s_ * 1.02
    y = 300 - (s_ - 1) * 60
    for i, (wd, parts) in enumerate([(l1, [(HOOK[0], WHITE), (HOOK[1], VGOLD)]), (l2, [(HOOK[2], WHITE)])]):
        x = (W - wd) / 2; yy = y + i * (lh + 14)
        d.rounded_rectangle([x - 26, yy - 6, x + wd + 26, yy + lh + 4], radius=18, fill=A((0, 0, 0), 0.82 * a))
        for s, c in parts:
            txt(d, x, yy - 8, s, fn, c, a); x += tw(d, s, fn)
# ---------------- captions ----------------
GROUPS = []
def build_groups():
    G = []; cur = []
    for i, x in enumerate(WORDS):
        if cur:
            prev = WORDS[cur[-1]]
            if len(cur) >= 3 or x['s'] - prev['e'] > 0.28 or prev['w'][-1:] in '.,?!': G.append(cur); cur = []
        cur.append(i)
    if cur: G.append(cur)
    return G
def group_at(t):
    lo = None
    for g in GROUPS:
        if WORDS[g[0]]['s'] <= t + 1e-6: lo = g
        else: break
    if lo is None: return None
    end = WORDS[lo[-1]]['e'] + 0.5
    nxt = [g for g in GROUPS if WORDS[g[0]]['s'] > WORDS[lo[0]]['s']]
    if t > end and (not nxt or WORDS[nxt[0][0]]['s'] > t): return None
    return lo
CAP_Y = 1398
def captions(im, t):
    g = group_at(t)
    if not g: return
    d = ImageDraw.Draw(im, 'RGBA')
    ws = [WORDS[i]['w'].upper().rstrip(',.?!') for i in g]
    size = 116
    while True:
        fn = f('BEB', size); sp = d.textlength(' ', font=fn) + 14; wd = [d.textlength(w, font=fn) for w in ws]; tot = sum(wd) + sp * (len(ws) - 1)
        if tot <= 900: break
        size -= 4
    xs = []; x = (W - tot) / 2
    for w_ in wd: xs.append(x); x += w_ + sp
    act = 0
    for k, i in enumerate(g):
        if WORDS[i]['s'] <= t: act = k
    g0 = WORDS[g[0]]['s']; s = lerp(0.9, 1, expo((t - g0) / 0.10))
    cap = Image.new('RGBA', (W, 260), (0, 0, 0, 0)); cd = ImageDraw.Draw(cap); shd = Image.new('RGBA', (W, 260), (0, 0, 0, 0)); sd = ImageDraw.Draw(shd)
    prev = max(0, act - 1); bt = expo((t - WORDS[g[act]]['s']) / 0.07) if act > 0 else 1
    bx0 = lerp(xs[prev], xs[act], bt) - 18; bx1 = lerp(xs[prev] + wd[prev], xs[act] + wd[act], bt) + 18
    for k, (w_, x_) in enumerate(zip(ws, xs)): sd.text((x_ + 4, 46), w_, font=fn, fill=(0, 0, 0, 220))
    cap.alpha_composite(shd.filter(ImageFilter.GaussianBlur(6)))
    lit_bar(cd, bx0, 40 + size * 0.02, bx1, 40 + size * 0.98, RED)
    for k, (w_, x_) in enumerate(zip(ws, xs)): cd.text((x_, 40), w_, font=fn, fill=CREAM, stroke_width=0 if k == act else 3, stroke_fill=(0, 0, 0))
    if abs(s - 1) > 0.002:
        cap = cap.resize((int(W * s), int(260 * s)), Image.BICUBIC); ox = int((W - cap.width) / 2); oy = int(CAP_Y - 40 - (cap.height - 260) / 2)
    else: ox, oy = 0, CAP_Y - 40
    im.alpha_composite(cap, (ox, oy))
# ---------------- camera ----------------
JUMPS = [p['out'][0] for p in PIECES[1:]]
def zoom_at(t):
    z = 1.0 if sum(1 for c in JUMPS if c <= t + 1e-6) % 2 == 0 else 1.08
    if C['explode'] <= t < C['Unless']: z = 1.16 if t >= C['explode'] else z            # punch on "explode"
    if C['im'] <= t < C['break']: z = 1.12                                                # "I'm sorry bro, but you're not"
    if C['Its'] <= t < PUSH_END: z = lerp(1.0, 1.12, ease_io((t - C['Its']) / (PUSH_END - C['Its'])))  # slow push on the heavy beat
    return z
def apply_zoom(src, z):
    if z == 1.0: return src
    big = src.resize((int(W * z), int(H * z)), Image.BICUBIC); ox = (big.width - W) // 2; oy = int((big.height - H) * 0.42)
    return big.crop((ox, oy, ox + W, oy + H))
# ---------------- B layout background ----------------
NAVYBG = None
def navy_bg():
    global NAVYBG
    if NAVYBG is None:
        yy, xx = np.mgrid[0:H, 0:W]; r = np.sqrt((xx - W * 0.85) ** 2 + (yy - H * 0.12) ** 2) / (W * 0.9)
        g = np.clip(1 - r, 0, 1) ** 2
        base = np.array(NAVY, np.float32)[None, None] * (1 - g[..., None] * 0.0) + np.array([29, 29, 30], np.float32)[None, None] * g[..., None] * 0.9
        rng = np.random.default_rng(5); base += rng.normal(0, 2.0, (H, W, 1))
        NAVYBG = Image.fromarray(np.clip(base, 0, 255).astype(np.uint8)).convert('RGBA')
    return NAVYBG
def pip(src, sc, t):
    # window rect animates from full frame -> target (in) and back (out)
    pin = ease_io((t - sc['t0']) / 0.4); pout = ease_io((t - sc['t1']) / 0.3) if not sc.get('cta') else 0
    k = pin * (1 - pout)
    wx0, wy0, wx1, wy1 = sc['win']; ww, wh = wx1 - wx0, wy1 - wy0
    ch = 1250; cw = ch * ww / wh; cx, cy = 540, 960   # crop around the face
    crop = (lerp(0, cx - cw / 2, k), lerp(0, cy - ch / 2, k), lerp(W, cx + cw / 2, k), lerp(H, cy + ch / 2, k))
    dst = (lerp(0, wx0, k), lerp(0, wy0, k), lerp(W, wx1, k), lerp(H, wy1, k))
    bg = navy_bg().copy()
    if k < 1: bg = Image.blend(src.convert('RGBA'), bg, clamp(k * 1.6))
    win = src.crop(tuple(int(v) for v in crop)).resize((max(2, int(dst[2] - dst[0])), max(2, int(dst[3] - dst[1]))), Image.BILINEAR)
    bg.paste(win, (int(dst[0]), int(dst[1])))
    return bg, dst, k
# ---------------- frame ----------------
def _sub_glow():
    global GL
    g = Image.new('RGBA', (W, H), (0, 0, 0, 0)); GL = ImageDraw.Draw(g, 'RGBA'); return g
def _merge_glow(glow, g, al):
    global GL
    al = clamp(al)
    if al > 0:
        if al < 1: g.putalpha(g.split()[3].point(lambda v: int(v * al)))
        glow.alpha_composite(g)
    GL = ImageDraw.Draw(glow, 'RGBA')
def frame(src, t):
    global GL
    src = apply_zoom(src, zoom_at(t))
    glow = Image.new('RGBA', (W, H), (0, 0, 0, 0)); GL = ImageDraw.Draw(glow, 'RGBA')
    scs = active(t)
    main = None
    for s in scs:
        if s['kind'] in 'ABDM' and s['t0'] <= t < s['t1'] + 0.3: main = s
    im = None; layer_alpha = 1.0
    if main and main['kind'] in 'AM':
        g = min(ease_io((t - main['t0'] + 0.05) / 0.30), 1 - ease_io((t - main['t1']) / 0.22))
        bg = Image.blend(src, big_blur(src, 18 * g), g) if g > 0 else src
        bg = Image.blend(bg, Image.new('RGB', (W, H), (5, 8, 16)), 0.68 * g)
        im = bg.convert('RGBA')
    elif main and main['kind'] == 'B':
        im, dst, k = pip(src, main, t)
    elif main and main['kind'] == 'D' and main['t0'] <= t < main['t1']:
        im = Image.new('RGBA', (W, H), DEEP + (255,))
    else:
        im = src.convert('RGBA'); main = None if (main and main['kind'] == 'D') else main
    # top/bottom readability scrim on footage-only moments
    if not main or main['kind'] in 'AM':
        yy = np.arange(H); a = np.where(yy > 1300, np.clip((yy - 1300) / 220, 0, 1) * 120, 0); a = np.maximum(a, np.where(yy < 460, (1 - yy / 460) * 110, 0))
        im.alpha_composite(Image.merge('RGBA', [Image.new('L', (W, H), c) for c in NAVY] + [Image.fromarray(np.repeat(a.astype(np.uint8)[:, None], W, 1))]))
    d = ImageDraw.Draw(im, 'RGBA')
    # --- main scene ---
    if main and main['kind'] == 'A':
        pin = expo((t - main['t0']) / 0.20); pout = clamp((t - main['t1']) / 0.16)
        if pout < 1:
            s = lerp(1.05, 1.0, pin) * lerp(1.0, 1.03, pout); P = PA
            w = (P[2] - P[0]) * s; h = (P[3] - P[1]) * s; cx = (P[0] + P[2]) / 2; cy = (P[1] + P[3]) / 2
            x0, y0, x1, y1 = cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2
            frosted(im, (x0, y0, x1, y1), 0.92, 8)
            lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); ld = ImageDraw.Draw(lay, 'RGBA'); sg = _sub_glow()
            if main['fn'] is sc_study1: main['fn'](im, ld, t, main, lay)
            else: main['fn'](im, ld, t, main)
            if pin < 1: lay = lay.filter(ImageFilter.GaussianBlur(8 * (1 - pin)))
            al = pin * (1 - pout); lay.putalpha(lay.split()[3].point(lambda v: int(v * al))); _merge_glow(glow, sg, al ** 2)
            im.alpha_composite(lay); d = ImageDraw.Draw(im, 'RGBA')
            d.rectangle([x0, y0, x1, y1], outline=A(VGOLD, 0.8 * al), width=3); brackets(d, x0, y0, x1, y1, A(VGOLD, al), 48, 7)
            GL.rectangle([x0, y0, x1, y1], outline=A(VGOLD, 0.5 * al), width=6); brackets(GL, x0, y0, x1, y1, A(VGOLD, al), 48, 14)
            d.ellipse([x0 + 26, y0 + 26, x0 + 42, y0 + 42], fill=A(RED, al if int(t * 4) % 2 == 0 else al / 3))
            txt(d, x0 + 56, y0 + 18, main['hl'], f('MONO', 28), WHITE, al); fr = f('MONO', 28); txt(d, x1 - 30 - tw(d, main['hr'], fr), y0 + 18, main['hr'], fr, VGOLD, al)
    elif main and main['kind'] == 'M':
        pin = expo((t - main['t0']) / 0.22); pout = clamp((t - main['t1']) / 0.16)
        if pout < 1:
            lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); ld = ImageDraw.Draw(lay, 'RGBA'); sg = _sub_glow(); main['fn'](im, ld, t, main)
            dy = lerp(30, 0, pin); lay = lay.transform(lay.size, Image.AFFINE, (1, 0, 0, 0, 1, -dy)) if dy > 0.5 else lay
            if pin < 1: lay = lay.filter(ImageFilter.GaussianBlur(6 * (1 - pin)))
            al = pin * (1 - pout); _merge_glow(glow, sg, al ** 2); lay.putalpha(lay.split()[3].point(lambda v: int(v * al))); im.alpha_composite(lay); d = ImageDraw.Draw(im, 'RGBA')
    elif main and main['kind'] == 'B':
        pin = ease_io((t - main['t0']) / 0.4); pout = ease_io((t - main['t1']) / 0.3) if not main.get('cta') else 0
        k = pin * (1 - pout)
        if k > 0.02:
            wx0, wy0, wx1, wy1 = dst
            d.rectangle([0, 0, 8, H], fill=A(GOLD, k))
            brackets(d, wx0 - 8, wy0 - 8, wx1 + 8, wy1 + 8, A(VGOLD, k), 40, 6); brackets(GL, wx0 - 8, wy0 - 8, wx1 + 8, wy1 + 8, A(VGOLD, k), 40, 12)
            d.rectangle([wx0, wy0, wx1, wy1], outline=A(VGOLD, 0.6 * k), width=2)
            if k > 0.9:
                d.ellipse([wx0 + 16, wy0 + 18, wx0 + 30, wy0 + 32], fill=A(RED, 1 if int(t * 4) % 2 == 0 else 0.35)); txt(d, wx0 + 38, wy0 + 12, 'LIVE', f('MONO', 20), WHITE, 0.9)
            lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); ld = ImageDraw.Draw(lay, 'RGBA'); sg = _sub_glow(); main['fn'](lay, ld, t, main)
            al = clamp((k - 0.72) / 0.28); _merge_glow(glow, sg, al ** 2); lay.putalpha(lay.split()[3].point(lambda v: int(v * al))); im.alpha_composite(lay); d = ImageDraw.Draw(im, 'RGBA')
            txt(d, 64, 1556, 'FOR RESEARCH & EDUCATIONAL PURPOSES ONLY', f('MONO', 18), DIM, 0.85 * al)
    elif main and main['kind'] == 'D':
        main['fn'](im, d, t, main)
    # --- overlays on footage: T strips & C cards ---
    for s in scs:
        if s['kind'] == 'T':
            pout = clamp((t - s['t1']) / 0.18)
            if pout >= 1 or t < s['t0']: continue
            lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); ld = ImageDraw.Draw(lay, 'RGBA'); sg = _sub_glow()
            frosted_target = im
            s['fn'](frosted_target, ld, t, s); _merge_glow(glow, sg, (1 - pout) ** 2)
            if pout > 0:
                lay = lay.transform(lay.size, Image.AFFINE, (1, 0, 0, 0, 1, 20 * pout)); lay.putalpha(lay.split()[3].point(lambda v: int(v * (1 - pout))))
                # fade the frosted strip back to footage
                if pout > 0: im.paste(Image.blend(im.crop(TS).convert('RGB'), apply_zoom(src, 1.0).crop(TS) if False else src.crop(TS), pout).convert('RGBA'), TS[:2])
            im.alpha_composite(lay); d = ImageDraw.Draw(im, 'RGBA')
        elif s['kind'] == 'C':
            pout = clamp((t - s['t1']) / 0.18)
            if pout >= 1 or t < s['t0']: continue
            lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); ld = ImageDraw.Draw(lay, 'RGBA')
            sg = _sub_glow(); p, dy = ccard_chrome(im, ld, t, s, s['label'])
            cl = Image.new('RGBA', (W, H), (0, 0, 0, 0)); cd = ImageDraw.Draw(cl, 'RGBA'); s['fn'](im, cd, t, s); _merge_glow(glow, sg, (p * (1 - pout)) ** 2)
            if dy > 0.5: cl = cl.transform(cl.size, Image.AFFINE, (1, 0, 0, 0, 1, -dy))
            if p < 1: cl = cl.filter(ImageFilter.GaussianBlur(5 * (1 - p)))
            lay.alpha_composite(cl)
            if pout > 0:
                lay.putalpha(lay.split()[3].point(lambda v: int(v * (1 - pout))))
                x0, y0, x1, y1 = s['box']; im.paste(Image.blend(im.crop((x0, y0, x1, y1)).convert('RGB'), src.crop((x0, y0, x1, y1)), pout).convert('RGBA'), (x0, y0))
            im.alpha_composite(lay); d = ImageDraw.Draw(im, 'RGBA')
    # --- top layer: hook / band / tracker ---
    text_hook(im, d, t)
    if not (main and main['kind'] == 'D' and t < main['t1']):
        topic_band(im, d, t); tracker(im, d, t)
    GL = None
    if glow.getbbox():
        sm = glow.resize((W // 4, H // 4), Image.BILINEAR)
        g1 = np.asarray(sm.filter(ImageFilter.GaussianBlur(3.5))).astype(np.float32) / 255; g2 = np.asarray(sm.filter(ImageFilter.GaussianBlur(10))).astype(np.float32) / 255
        prem = np.clip(g1[..., :3] * g1[..., 3:] * 2.3 + g2[..., :3] * g2[..., 3:] * 1.8, 0, 1)
        prem = np.asarray(Image.fromarray((prem * 255).astype(np.uint8)).resize((W, H), Image.BILINEAR)).astype(np.float32) / 255
        b = np.asarray(im.convert('RGB')).astype(np.float32) / 255
        im = Image.fromarray(((1 - (1 - b) * (1 - prem)) * 255).astype(np.uint8)).convert('RGBA')
    d = ImageDraw.Draw(im, 'RGBA'); d.rectangle([0, 0, 7, H], fill=GOLD)
    captions(im, t)
    out = im.convert('RGB')
    # impact shake on the verdict bars
    for tv in [C['sponge'] + 0.22, C['forklift'] + 0.2, C['goal'] + 0.2, C['of1']]:
        k = round((t - tv) * FPS)
        if k in (0, 1):
            dx = [9, -5][k]; z = 1.02; big = out.resize((int(W * z), int(H * z)), Image.BICUBIC); ox = (big.width - W) // 2 - dx; oy = (big.height - H) // 2
            out = big.crop((ox, oy, ox + W, oy + H)); ImageDraw.Draw(out).rectangle([0, 0, 7, H], fill=GOLD)
    return out
GROUPS[:] = build_groups()
if __name__ == '__main__':
    mode = sys.argv[2]
    if mode == 'stills':
        for tt in [float(x) for x in sys.argv[3:]]:
            subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', f'{tt:.3f}', '-i', B + 'assembled.mov', '-frames:v', '1', B + '_src.png'])
            frame(Image.open(B + '_src.png').convert('RGB'), tt).resize((540, 960), Image.LANCZOS).save(S + f'/qc/st_{tt:07.2f}.jpg', quality=88)
        sys.exit()
    if mode == 'cues':
        for k, v in C.items(): print(k, round(v, 2))
        for s in SCENES: print(s['kind'], round(s['t0'], 2), round(s['t1'], 2), s['fn'].__name__)
        sys.exit()
    n0, n1, out = int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
    dec = subprocess.Popen(['ffmpeg', '-v', 'error', '-ss', f'{n0 / FPS:.4f}', '-i', B + 'assembled.mov', '-frames:v', str(n1 - n0), '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], stdout=subprocess.PIPE)
    enc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-crf', '12', '-preset', 'veryfast', '-pix_fmt', 'yuv420p', out], stdin=subprocess.PIPE)
    for n in range(n0, n1):
        buf = dec.stdout.read(W * H * 3)
        if len(buf) < W * H * 3: print('short', n); break
        enc.stdin.write(frame(Image.frombuffer('RGB', (W, H), buf), n / FPS).tobytes())
    enc.stdin.close(); enc.wait(); dec.kill(); print('done', n0, n1)
