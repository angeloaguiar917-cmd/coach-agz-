# Reel 04 — "Muscle on gear: 3 months to 5 years" (test 2) (1080x1920, 30 fps)
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
for k, w, ap in [
    ('pounds', 'pounds', 2.9), ('Assuming', 'assuming', 5.88), ('untrained', 'untrained', 7.56), ('average', 'average', 9.72), ('locked', 'locked', 11.24),
    ('within', 'within', 12.16), ('a3', 'about', 14.0), ('a6', 'about', 19.08), ('a12', 'ten', 23.8), ('And5', 'and', 26.38),
    ('training', 'training', 31.02), ('nutrition', 'nutrition', 31.62), ('protocols', 'protocols', 32.88), ('side', 'side', 33.66),
    ('n20', '20', 35.86), ('started', 'started', 39.04), ('clarify', 'clarify', 41.18), ('240', '240', 42.26), ('mutant', 'mutant', 44.28),
    ('pct', '1', 45.38), ('comes', 'comes', 47.02), ('40', '40', 48.52), ('realistic', 'realistic', 51.88), ('averagemale', 'average', 53.76),
    ('Not', 'not', 55.04), ('self', 'self', 57.48), ('how', 'how', 58.24), ('10y', '10', 61.58), ('suboptimal', 'suboptimal', 64.18), ('good', 'good', 65.48),
    ('Then', 'then', 67.08), ('growth', 'growth', 68.14), ('linear', 'linear', 70.1), ('monitoring', 'monitoring', 70.98), ('blood', 'blood', 71.86),
    ('eliminate', 'eliminate', 73.58), ('risk', 'risk', 74.56), ('Listen', 'listen', 77.12), ('client', 'client', 83.26), ('n2030', '20', 85.58),
    ('six', 'six', 87.44), ('You', 'you', 88.14), ('90', '90', 89.32), ('fifth', 'fifth', 91.04), ('social', 'social', 91.84),
    ('goal', 'goal', 92.98), ('fast', 'fast', 94.94), ('keeping', 'keeping', 98.08), ('health', 'health', 100.68), ('disposable', 'disposable', 101.34),
    ('so', 'so', 103.02), ('That', 'that', 110.48), ('framework', 'framework', 112.48), ('Comment', 'comment', 113.6), ('free', 'free', 116.32)]:
    C[k] = cue(w, ap)
HOOK_END = 6.0; MID = DUR / 2
CTA_IN = C['That']
# ======================= SHARED CHROME =======================
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
def ccard_chrome(im, d, t, sc, label):
    x0, y0, x1, y1 = sc['box']
    p = expo((t - sc['t0'] - 0.07) / 0.22); dy = lerp(24, 0, p)
    pb = clamp((t - sc['t0']) / 0.1)
    frosted(im, (x0, y0 + dy, x1, y1 + dy), 0.9, 16)
    d.rounded_rectangle([x0, y0 + dy, x1, y1 + dy], radius=22, fill=A((12, 12, 14), 0.35 * p), outline=A((60, 60, 66), 0.8 * p), width=2)
    d.rounded_rectangle([x0, y0 + dy * 0.3, x0 + 10, lerp(y0, y1, pb) + dy * 0.3], radius=4, fill=A(CBAR, 1))
    if GL: GL.rectangle([x0, y0, x0 + 10, lerp(y0, y1, pb)], fill=A(CBAR, 0.9))
    if p > 0.3: tracked(d, x0 + 34, y0 + 22 + dy, label, f('BARB', 28), CRIMSON, p, 4)
    if not sc.get('nowm'): txt(d, x1 - 128, y1 - 34 + dy, '@COACH.AGZ', f('MONO', 16), DIM, p * 0.8)
    return p, dy
PA = (56, 372, 1024, 1340)
def topic_band(im, d, t):
    if t < HOOK_END or t >= MID + 0.15: return
    a = clamp((t - HOOK_END) / 0.15) * (1 - clamp((t - MID) / 0.15))
    x0, y0, x1, y1 = (8, 250, W, 340)
    d.rectangle([x0, y0, x1, y1], fill=NAVY + (int(228 * a),))
    d.line([(56, 270), (96, 270)], fill=A(GOLD, a), width=4); txt(d, 108, 257, '@coach.agz', f('MONO', 24), GOLD, a)
    fn = f('BAR', 60); s1 = 'Realistic muscle on '; txt(d, 56, 274, s1, fn, CREAM, a); txt(d, 56 + tw(d, s1, fn), 274, 'GEAR', fn, VGOLD, a)
def tracker(im, d, t): pass
sc_study1 = None
# ======================= SCENES =======================
SPEC = [(79, 163, 224), (60, 203, 106), (240, 160, 48)]  # brand spectrum: blue / green / amber
def spectrum_bar(d, x0, y0, x1, y1, a=1.0):
    for x in range(int(x0), int(x1)):
        k = (x - x0) / (x1 - x0); c = mix(SPEC[0], SPEC[1], k * 2) if k < 0.5 else mix(SPEC[1], SPEC[2], (k - 0.5) * 2)
        d.line([(x, y0), (x, y1)], fill=A(c, a))
def sc_sliders(im, d, t, sc):
    strip_chrome(im, d, t, sc, 'SUBJECT PROFILE', 'ASSUMPTIONS')
    rows = [('TRAINING AGE', 'untrained', 0.06, 'UNTRAINED', 'NEW', 'VETERAN'), ('GENETICS', 'average', 0.5, 'AVERAGE', 'POOR', 'ELITE'),
            ('ADHERENCE', 'locked', 0.97, 'LOCKED IN', 'LOOSE', 'TOTAL')]
    bx0, bx1 = 330, 800
    for i, (lb, k, pos, val, lo, hi) in enumerate(rows):
        y = 446 + i * 74; a = appear(t, sc['t0'] + 0.2 + i * 0.1)
        txt(d, 70, y - 6, lb, f('BARB', 40), WHITE if t >= C[k] else (130, 132, 145), a)
        spectrum_bar(d, bx0, y + 10, bx1, y + 22, a * (1 if t >= C[k] else 0.45))
        txt(d, bx0, y + 26, lo, f('MONO', 16), DIM, a); txt(d, bx1, y + 26, hi, f('MONO', 16), DIM, a, 'rt')
        if t >= C[k] - 0.3:
            p = ease_io((t - C[k] + 0.3) / 0.45); x = lerp(bx0 + 0.5 * (bx1 - bx0), lerp(bx0, bx1, pos), p)
            d.polygon([(x - 13, y - 10), (x + 13, y - 10), (x, y + 8)], fill=A(WHITE, 1))
            if GL: GL.polygon([(x - 15, y - 12), (x + 15, y - 12), (x, y + 10)], fill=A(WHITE, 0.6))
            if t >= C[k]:
                tag(d, 830, y - 8, val, VGOLD if k != 'locked' else GREEN, 22, appear(t, C[k]))
COLS = [('3 MO', 3, 8, 'a3'), ('6 MO', 5, 12, 'a6'), ('1 YR', 10, 20, 'a12')]
def sc_columns(im, d, t, sc):  # B, window right
    a = appear(t, sc['t0'] + 0.3, 0.25)
    kicker(d, 80, 384, 'LEAN TISSUE GAINED', VGOLD, a, 24)
    headline(d, 80, 440, [[('YEAR ONE', CREAM)], [('IN POUNDS', VGOLD)]], 104, a, 520)
    txt(d, 80, 650, 'Untrained · average · locked in', f('DMR', 30), MUTED, a)
    x0, x1, yb, yt = 170, 990, 1330, 1070; top = 20
    for v in (0, 5, 10, 15, 20):
        y = lerp(yb, yt, v / top); d.line([(x0, y), (x1, y)], fill=A((40, 44, 58), a), width=1); txt(d, x0 - 20, y - 12, str(v), f('MONO', 20), DIM, a, 'rt')
    txt(d, x0 - 20, yt - 44, 'LB', f('MONO', 20), DIM, a, 'rt')
    mids = []
    for i, (lb, lo, hi, k) in enumerate(COLS + [('5 YR', 0, 0, None)]):
        cx = 280 + i * 205; w2 = 64
        txt(d, cx, yb + 10, lb, f('BEB', 44), VGOLD if (k and t >= C[k]) else MUTED, a, 'mt')
        if k is None:
            dashed(d, [(cx - w2, yb), (cx - w2, yt + 20), (cx + w2, yt + 20), (cx + w2, yb)], (90, 94, 110), 3, a)
            txt(d, cx, yt + 120, '?', f('BEB', 120), (90, 94, 110), a, 'mt'); continue
        if t < C[k]: continue
        p = expo((t - C[k]) / 0.7); ylo = lerp(yb, yt, lo / top); yhi = lerp(ylo, lerp(yb, yt, hi / top), p)
        d.rectangle([cx - w2, ylo, cx + w2, yb], fill=A((30, 34, 46), 0.9))   # baseline stem
        lit_vbar(d, cx - w2, yhi, cx + w2, ylo, mix(CYAN, VGOLD, i / 2))
        if GL: GL.rectangle([cx - w2, yhi, cx + w2, ylo], outline=A(mix(CYAN, VGOLD, i / 2), 0.9), width=8)
        val = f'{lo}–{int(lerp(lo, hi, p))}'; txt(d, cx, yhi - 66, val, f('BEB', 60), WHITE, 1, 'mt')
        mids.append((cx, (ylo + yhi) / 2))
    if len(mids) > 1: dashed(d, mids, WHITE, 3, 0.7)
def sc_band(im, d, t, sc):
    for i, (lb, k) in enumerate([('TRAINING', 'training'), ('NUTRITION', 'nutrition'), ('PROTOCOLS', 'protocols'), ('SIDE-EFFECT MGMT', 'side')]):
        if t >= C[k]: tag(d, 100 + [0, 190, 390, 600][i], 470, lb, CYAN, 24, appear(t, C[k]))
    x0, x1, yb, yt = 170, 960, 1230, 600; a = appear(t, sc['t0'] + 0.2, 0.3)
    for v in (0, 10, 20, 30, 40):
        y = lerp(yb, yt, v / 40); d.line([(x0, y), (x1, y)], fill=A((40, 44, 58), a), width=1); txt(d, x0 - 16, y - 12, str(v), f('MONO', 20), DIM, a, 'rt')
    for m, lb in [(0, '0'), (12, '1Y'), (24, '2Y'), (36, '3Y'), (48, '4Y'), (60, '5Y')]:
        x = lerp(x0, x1, m / 60); txt(d, x, yb + 10, lb, f('MONO', 20), DIM, a, 'mt')
    txt(d, x0 - 16, yt - 40, 'LB', f('MONO', 20), DIM, a, 'rt')
    pts = [(0, 0, 0), (3, 3, 8), (6, 5, 12), (12, 10, 20), (24, 14, 27), (36, 17, 32), (48, 19, 36), (60, 20, 40)]
    def P(m, v): return (lerp(x0, x1, m / 60), lerp(yb, yt, v / 40))
    sweep = 12 * ease_io((t - sc['t0'] - 0.3) / 0.8) + (48 * ease_io((t - C['n20']) / 1.4) if t >= C['n20'] else 0)
    if t < C['n20'] + 1.2:  # ghost of the unknown part of the trajectory
        ga = appear(t, sc['t0'] + 1.0, 0.4) * (1 - appear(t, C['n20'] + 0.6, 0.5))
        dashed(d, [P(m, hi) for m, lo, hi in pts[3:]], (110, 114, 130), 3, ga); dashed(d, [P(m, lo) for m, lo, hi in pts[3:]], (110, 114, 130), 3, ga)
        gx_, gy_ = P(48, 28); txt(d, gx_, gy_, '?', f('BEB', 110), (110, 114, 130), ga, 'mm')
    vis = [p for p in pts if p[0] <= sweep + 1e-6]
    if len(vis) >= 2:
        if vis[-1][0] < sweep and len(vis) < len(pts):  # interpolate the leading edge
            n_ = pts[len(vis)]; q = (sweep - vis[-1][0]) / (n_[0] - vis[-1][0])
            vis = vis + [(sweep, lerp(vis[-1][1], n_[1], q), lerp(vis[-1][2], n_[2], q))]
        top_ = [P(m, hi) for m, lo, hi in vis]; bot = [P(m, lo) for m, lo, hi in vis][::-1]
        d.polygon(top_ + bot, fill=A(VGOLD, 0.26)); polyline(d, top_, VGOLD, 4); polyline(d, bot[::-1], VGOLD, 4)
        polyline(d, [P(m, (lo + hi) / 2) for m, lo, hi in vis], WHITE, 3, 0.8, glow=False)
        for m, lo, hi in vis:
            if m in (3, 6, 12, 60) and m <= sweep: x, y = P(m, hi); d.ellipse([x - 7, y - 7, x + 7, y + 7], fill=A(WHITE, 1))
    if t >= C['n20'] + 1.3:
        p = appear(t, C['n20'] + 1.3); x, y = P(60, 40)
        txt(d, x - 10, y + 6, '20–40 LB', f('BEB', 84), WHITE, p, 'rt')
        if GL: GL.text((x - 10 - tw(d, '20–40 LB', f('BEB', 84)), y + 6), '20–40 LB', font=f('BEB', 84), fill=A(VGOLD, 0.5 * p))
    if t >= C['started']: tag(d, 800, 700, 'VS. DAY 1', CYAN, 24, appear(t, C['started']))
    if t >= C['n20'] + 2.0: tag(d, 560, 1170, 'RATE SLOWS EVERY YEAR', VGOLD, 22, appear(t, C['n20'] + 2.0))
def sc_table(im, d, t, sc):
    strip_chrome(im, d, t, sc, 'OUTLIER vs AVERAGE', 'SPEC SHEET')
    cx = [70, 380, 720]; a = appear(t, sc['t0'] + 0.25)
    txt(d, cx[1], 410, 'OUTLIER', f('BEB', 48), RED, a); txt(d, cx[2], 410, 'AVERAGE MALE', f('BEB', 48), VGOLD, appear(t, C['realistic']) if t >= C['realistic'] else 0.35 * a)
    rows = [('BODYWEIGHT', '240 LB', '240', '—'), ('PERCENTILE', 'TOP 0.01%', 'pct', '50TH'), ('FIRST CYCLE', '+40 LB', '40', '+3–8 LB')]
    for i, (lb, ov, k, av) in enumerate(rows):
        y = 470 + i * 60; d.line([(70, y + 54), (1010, y + 54)], fill=A(GRID, a), width=1)
        txt(d, cx[0], y + 10, lb, f('MONO', 24), MUTED, a)
        if t >= C[k]: txt(d, cx[1], y + 2, ov, f('BEB', 52), WHITE, appear(t, C[k], 0.12) * (1 - 0.6 * appear(t, C['Not'], 0.2)))
        if t >= C['averagemale'] + 0.15 * i: txt(d, cx[2], y + 2, av, f('BEB', 52), WHITE, appear(t, C['averagemale'] + 0.15 * i, 0.12))
    if t >= C['mutant']: flag(d, (cx[1] - 14, 400, 690, 650), C['mutant'], t, RED, 24)
    if t >= C['Not']:
        p = expo((t - C['Not']) / 0.14); s_ = lerp(1.5, 1.0, p)
        lay = Image.new('RGBA', (360, 110), (0, 0, 0, 0)); ld = ImageDraw.Draw(lay)
        ld.rectangle([4, 4, 356, 106], outline=A(RED, 1), width=7); ld.text((180, 56), 'NOT YOU', font=f('BEB', 86), fill=A(RED, 1), anchor='mm')
        lay = lay.rotate(-8, resample=Image.BICUBIC, expand=True); lay = lay.resize((int(lay.width * s_), int(lay.height * s_)))
        lay.putalpha(lay.split()[3].point(lambda v: int(v * p)))
        d._image.alpha_composite(lay, (int(535 - lay.width / 2), int(540 - lay.height / 2)))
        if GL: GL.rectangle([390, 470, 680, 610], outline=A(RED, p * 0.8), width=10)
def sc_heatmap(im, d, t, sc):
    x0, y0, x1, y1 = sc['box']; gx, gy, cw, ch = x0 + 84, y0 + 74, 22, 16
    rng = np.random.default_rng(21); grid = []
    for r in range(10):
        row = []; on = rng.uniform() < 0.5; run = 0
        for c in range(12):
            run -= 1
            if run <= 0: on = not on; run = int(rng.integers(3, 7)) if on else int(rng.integers(2, 5))
            row.append(on)
        grid.append(row)
    sweep = clamp((t - C['10y'] + 0.5) / 1.6) * 120
    for r in range(10):
        if r % 3 == 0 or r == 9: txt(d, gx - 16, gy + r * (ch + 3) + 1, f'Y{r + 1}', f('MONO', 16), DIM, 1, 'rt')
        for c in range(12):
            x = gx + c * (cw + 3); y = gy + r * (ch + 3); idx = r * 12 + c
            col = (40, 44, 58)
            if idx < sweep and grid[r][c]: col = VGOLD
            d.rectangle([x, y, x + cw, y + ch], fill=A(col, 1))
            if idx < sweep and grid[r][c] and GL: GL.rectangle([x, y, x + cw, y + ch], fill=A(VGOLD, 0.35))
    lx = gx + 12 * (cw + 3) + 16
    d.rectangle([lx, gy + 4, lx + 18, gy + 18], fill=A(VGOLD, 1)); txt(d, lx + 26, gy, 'ON', f('MONO', 18), VGOLD)
    d.rectangle([lx, gy + 36, lx + 18, gy + 50], fill=A((40, 44, 58), 1)); txt(d, lx + 26, gy + 32, 'OFF', f('MONO', 18), DIM)
    txt(d, lx, gy + 74, 'ILLUS-', f('MONO', 14), DIM); txt(d, lx, gy + 92, 'TRATIVE', f('MONO', 14), DIM)
    if t >= C['suboptimal']: tag(d, x0 + 34, y1 - 52, 'STILL BUILDING', CYAN, 20, appear(t, C['suboptimal']))
    if t >= C['good']: check(d, x0 + 260, y1 - 48, GREEN, 0.8, appear(t, C['good'])); txt(d, x0 + 292, y1 - 50, 'PROGRESS', f('MONO', 20), GREEN, appear(t, C['good']))
def sc_gauge(im, d, t, sc):  # B, window left
    a = appear(t, sc['t0'] + 0.3, 0.25)
    kicker(d, 480, 384, 'REALITY CHECK', VGOLD, a, 24)
    headline(d, 480, 440, [[('NEVER', CREAM)], [('LINEAR', VGOLD)]], 120, a, 520)
    txt(d, 480, 680, 'Growth stalls, dips, restarts.', f('DMR', 28), MUTED, appear(t, C['linear']))
    x0, x1, yb, yt = 110, 980, 1170, 990
    d.line([(x0, yb), (x1, yb)], fill=A(STEEL, a), width=2); txt(d, x1, yb + 6, 'TIME →', f('MONO', 18), DIM, a, 'rt')
    if t >= C['growth'] - 0.2:
        dashed(d, [(x0, yb - 6), (x1, yt)], (130, 134, 150), 3, appear(t, C['growth'] - 0.2)); txt(d, x1 - 150, yt - 4, 'EXPECTED', f('MONO', 18), MUTED, appear(t, C['growth']))
    if t >= C['linear'] - 0.5:
        ys = [0, .18, .2, .2, .34, .3, .31, .5, .52, .5, .62, .64, .64, .72, .7, .78]
        pts = []
        for i, v in enumerate(ys):
            x = lerp(x0, x1, i / (len(ys) - 1)); y = lerp(yb - 6, yt + 70, v)
            if pts: pts.append((x, pts[-1][1]))
            pts.append((x, y))
        polyline(d, partial(pts, clamp((t - C['linear'] + 0.5) / 1.2)), VGOLD, 6)
        txt(d, x0 + 10, yt + 4, 'ACTUAL', f('MONO', 18), VGOLD, appear(t, C['linear']))
    # risk gauge
    if t >= C['monitoring'] - 0.1:
        ga = appear(t, C['monitoring'] - 0.1, 0.25); cx, cy, r = 700, 1350, 128
        for k in range(60):
            a0 = 180 + k * 3; col = mix(SPEC[1], RED, k / 59)
            d.arc([cx - r, cy - r, cx + r, cy + r], a0, a0 + 3.2, fill=A(col, ga), width=22)
        ang = 180 + 180 * (0.62 - 0.27 * appear(t, C['blood'], 0.6) if t < C['eliminate'] else 0.35 + 0.015 * math.sin(t * 7))
        nx, ny = cx + (r - 30) * math.cos(math.radians(ang)), cy + (r - 30) * math.sin(math.radians(ang))
        d.line([(cx, cy), (nx, ny)], fill=A(WHITE, ga), width=6); d.ellipse([cx - 12, cy - 12, cx + 12, cy + 12], fill=A(WHITE, ga))
        if GL: GL.line([(cx, cy), (nx, ny)], fill=A(WHITE, ga * 0.6), width=10)
        txt(d, 110, 1214, 'CV RISK', f('MONO', 26), CREAM, ga)
        if t >= C['blood']: check(d, 110, 1262, GREEN, 0.9, appear(t, C['blood'])); txt(d, 152, 1258, 'BLOODWORK', f('MONO', 26), GREEN, appear(t, C['blood']))
        if t >= C['risk']: tag(d, 110, 1306, 'NOT ZERO', RED, 26, appear(t, C['risk']))
DOC4 = None
def make_form():
    w_, h_ = 860, 400; im = Image.new('RGB', (w_, h_), (233, 231, 226)); d = ImageDraw.Draw(im)
    d.rectangle([0, 0, w_, 62], fill=COARED); d.text((22, 14), 'NEW CLIENT · INTAKE FORM', font=f('MONO', 28), fill=WHITE)
    for i, k in enumerate(['PRIMARY GOAL', 'TARGET GAIN', 'TIMEFRAME']):
        y = 92 + i * 96; d.text((22, y + 10), k, font=f('MONO', 22), fill=(110, 110, 118)); d.line([(260, y + 62), (w_ - 30, y + 62)], fill=(170, 168, 162), width=2)
    arr = np.asarray(im).astype(np.int16); arr += np.random.default_rng(2).integers(-7, 7, arr.shape[:2])[..., None]
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).convert('RGBA')
def sc_form(im, d, t, sc, lay=None):
    global DOC4
    if DOC4 is None: DOC4 = make_form()
    a = appear(t, sc['t0'] + 0.15, 0.25)
    dd = DOC4.copy(); dd.putalpha(int(255 * a)); d._image.alpha_composite(dd, (110, 470))
    vals = [('Build muscle', 'client', INK), ('+20–30 lb', 'n2030', (30, 40, 160)), ('6 months', 'six', (30, 40, 160))]
    for i, (v, k, col) in enumerate(vals):
        if t >= C[k]:
            p = clamp((t - C[k]) / 0.35); s = v[:max(1, int(len(v) * p))]   # written in
            txt(d, 380, 470 + 92 + i * 96 + 4, s, f('DMB', 44), col, 1)
    if t >= C['n2030'] + 0.4: flag(d, (370, 652, 760, 726), C['n2030'] + 0.4, t, RED, 22)
    if t >= C['n2030'] + 0.5:
        y0 = 920; pa = appear(t, C['n2030'] + 0.5)
        txt(d, 110, y0, 'FIRST 6 MONTHS · LB OF MUSCLE', f('MONO', 24), VGOLD, pa)
        ax0, ax1 = 360, 970
        for v in (0, 10, 20, 30): x = lerp(ax0, ax1, v / 30); d.line([(x, y0 + 50), (x, y0 + 250)], fill=A((40, 44, 58), pa), width=1); txt(d, x, y0 + 256, str(v), f('MONO', 18), DIM, pa, 'mt')
        for i, (lb, lo, hi, col, tt) in enumerate([('REQUESTED', 20, 30, RED, C['n2030'] + 0.6), ('REALISTIC', 5, 12, VGOLD, C['six'] - 0.2)]):
            if t < tt: continue
            p = expo((t - tt) / 0.5); y = y0 + 70 + i * 92
            txt(d, 110, y + 12, lb, f('BEB', 50), col, appear(t, tt))
            xa = lerp(ax0, ax1, lo / 30); xb = lerp(xa, lerp(ax0, ax1, hi / 30), p); lit_bar(d, xa, y + 8, xb, y + 66, col)
            if GL: GL.rectangle([xa, y + 8, xb, y + 66], fill=A(col, 0.45))
            txt(d, xb + 12 if hi < 25 else xa - 12, y + 10, f'{lo}–{hi}', f('BEB', 54), WHITE, p, None if hi < 25 else 'ra')
def sc_bubbles(im, d, t, sc):
    x0, y0, x1, y1 = sc['box']; R = 118; cyb = y0 + 210
    if t >= C['90'] - 0.1:
        p = expo((t - C['90'] + 0.1) / 0.3); r = R * math.sqrt(90 / 1825) * p; cx = x0 + 90
        d.ellipse([cx - r, cyb - r, cx + r, cyb + r], fill=A(CYAN, 0.9)); GL.ellipse([cx - r - 6, cyb - r - 6, cx + r + 6, cyb + r + 6], fill=A(CYAN, 0.6 * p))
        txt(d, cx, cyb + 50, 'DAY 90', f('BEB', 40), CYAN, p, 'mt'); txt(d, cx, cyb + 92, 'YOU', f('MONO', 18), DIM, p, 'mt')
    if t >= C['fifth'] - 0.1:
        p = expo((t - C['fifth'] + 0.1) / 0.6); r = R * p; cx = x1 - 150
        d.ellipse([cx - r, cyb - r, cx + r, cyb + r], fill=A(VGOLD, 0.22), outline=A(VGOLD, 1), width=4)
        if GL: GL.ellipse([cx - r, cyb - r, cx + r, cyb + r], outline=A(VGOLD, p), width=8)
        txt(d, cx, cyb - 20, 'YEAR 5', f('BEB', 56), VGOLD, p, 'mm'); txt(d, cx, cyb + 24, '1,825 DAYS', f('MONO', 18), CREAM, p, 'mm')
    if t >= C['social']: tag(d, x0 + 34, y1 - 76, '20× THE TIME', RED, 22, appear(t, C['social']))
def sc_balance(im, d, t, sc):
    strip_chrome(im, d, t, sc, 'WHAT YOU OPTIMISE FOR', 'TRADE-OFF')
    left = [('GAIN FAST', 'fast', RED)]; right = [('KEEPABLE MUSCLE', 'keeping', VGOLD), ('LONG-TERM HEALTH', 'health', GREEN)]
    wl = sum(1 for _, k, _ in left if t >= C[k]); wr = sum(1 for _, k, _ in right if t >= C[k])
    target = clamp((wr - wl) * 7, -9, 9)   # degrees, + = right side down
    # settle with a short, damped lag (heavy beam, no bounce)
    ang = target
    for _, k, _ in left + right:
        if t >= C[k] and t < C[k] + 0.5:
            prev = clamp(((wr - (1 if k != 'fast' else 0)) - (wl - (1 if k == 'fast' else 0))) * 7, -9, 9)
            ang = lerp(prev, target, ease_io((t - C[k]) / 0.5))
    cx, cy, L = 540, 580, 300; th = math.radians(ang)
    d.polygon([(cx, cy), (cx - 34, cy + 90), (cx + 34, cy + 90)], fill=A((60, 64, 80), 1), outline=A(STEEL, 1))
    lx, ly = cx - L * math.cos(th), cy - L * math.sin(th); rx, ry = cx + L * math.cos(th), cy + L * math.sin(th)
    d.line([(lx, ly), (rx, ry)], fill=A(WHITE, 1), width=7)
    if GL: GL.line([(lx, ly), (rx, ry)], fill=A(WHITE, 0.4), width=10)
    for (px, py, items) in [(lx, ly, left), (rx, ry, right)]:
        d.line([(px - 110, py + 6), (px + 110, py + 6)], fill=A(STEEL, 1), width=4)
        stack = 0
        for lb, k, col in items:
            if t < C[k]: continue
            p = clamp((t - C[k]) / 0.18); yy = lerp(py - 160, py - 4 - stack * 46, p ** 2)
            fn = f('BARB', 26); w_ = tw(d, lb, fn) + 22
            lit_bar(d, px - w_ / 2, yy - 40, px + w_ / 2, yy, col); txt(d, px, yy - 20, lb, fn, INK, 1, 'mm')
            if GL: GL.rectangle([px - w_ / 2, yy - 40, px + w_ / 2, yy], outline=A(col, 0.8), width=6)
            stack += 1
    if t >= C['fast'] + 0.6: cross(d, lx - 14, ly + 26, RED, 0.9, appear(t, C['fast'] + 0.6))
    if t >= C['keeping'] + 0.5: check(d, rx - 14, ry + 26, GREEN, 0.9, appear(t, C['keeping'] + 0.5))
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
WIN_R = (636, 372, 1016, 940); WIN_L = (64, 372, 444, 940)
SCENES = [
    SC('T', HOOK_END, C['within'] - 0.05, sc_sliders),
    SC('B', C['within'], C['And5'] - 0.05, sc_columns, win=WIN_R),
    SC('A', C['And5'], C['clarify'] - 0.6, sc_band, hl='5-YEAR TRAJECTORY', hr='RANGE BAND'),
    SC('T', C['clarify'] - 0.3, C['self'] + 0.2, sc_table),
    SC('C', C['how'] - 0.1, C['Then'] - 0.1, sc_heatmap, box=(56, 360, 516, 700), label='CYCLE LOG · 10 YEARS', nowm=True),
    SC('B', C['Then'], C['Listen'] - 0.05, sc_gauge, win=WIN_L),
    SC('A', C['Listen'], C['You'] - 0.05, sc_form, hl='CLIENT INTAKE', hr='FORM 01'),
    SC('C', C['You'], C['goal'] - 0.25, sc_bubbles, box=(604, 360, 1024, 700), label='TIME ON THE CLOCK'),
    SC('T', C['goal'] - 0.2, C['so'] - 0.05, sc_balance),
    SC('B', CTA_IN, DUR + 1, sc_cta, win=(240, 372, 840, 952), cta=True),
]
def active(t, kinds=None):
    return [s for s in SCENES if s['t0'] <= t < s['t1'] + 0.3 and (kinds is None or s['kind'] in kinds)]

# ---------------- text hook (engine) ----------------
HOOK = ['Muscle on ', 'GEAR', '3 months to 5 years']
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
    if C['mutant'] <= t < C['comes']: z = 1.15                                          # punch on "genetic mutant"
    if C['so'] <= t < CTA_IN: z = lerp(1.0, 1.12, ease_io((t - C['so']) / (CTA_IN - C['so'])))  # slow push on the heavy beat
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
    for tv in [C['Not'] + 0.14]:
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
