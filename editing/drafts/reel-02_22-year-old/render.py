# @coach.agz Reel 02 "22-year-old me" — 1080x1920 30fps render
# usage: python3 render.py <scratch_root> stills t1 t2 ...   |   python3 render.py <scratch_root> chunk n0 n1 out.mp4
import json, subprocess, sys, math
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
S = sys.argv[1]; F = S + '/fonts/'; T = S + '/work/'
W, H = 1080, 1920; FPS = 30
TR = json.load(open(T + 'trim.json')); KEEP = TR['keep']
CUTS = []; _acc = 0
for a, b in KEEP[:-1]:
    _acc += b - a; CUTS.append(round(_acc * FPS) / FPS)
DUR = round(sum(b - a for a, b in KEEP) * FPS) / FPS
MID = min(CUTS, key=lambda c: abs(c - DUR / 2))
WORDS = json.load(open(T + 'words_final.json'))

GOLD = (201, 169, 110); CREAM = (244, 241, 234); NAVY = (14, 17, 23); MUTED = (150, 152, 160)
RED = (255, 34, 28); VGOLD = (255, 194, 26); CYAN = (0, 229, 255); GREEN = (30, 255, 110)
DEEP = (2, 3, 8); INK = (6, 8, 14); WHITE = (255, 255, 255); GRID = (44, 48, 62); DIM = (70, 74, 90)
MONO = 'JBMono-500.ttf'; MONOB = 'JBMono-700.ttf'; BEB = 'BebasNeue.ttf'; BAR = 'Barlow-800.ttf'; BAR6 = 'Barlow-600.ttf'
DMB = 'DMSans-700.ttf'; DMR = 'DMSans-400.ttf'
_fc = {}
def f(n, s):
    k = (n, int(s))
    if k not in _fc: _fc[k] = ImageFont.truetype(F + n, int(s))
    return _fc[k]
def clamp(x, a=0, b=1): return max(a, min(b, x))
def expo(x): x = clamp(x); return 1 if x >= 1 else 1 - 2 ** (-10 * x)
def ease_io(x): x = clamp(x); return 4 * x ** 3 if x < .5 else 1 - (-2 * x + 2) ** 3 / 2
def back(x):  # heavy settle, tiny overshoot (for paper / pills)
    x = clamp(x); c = 1.2; return 1 + (c + 1) * (x - 1) ** 3 + c * (x - 1) ** 2
def lerp(a, b, t): return a + (b - a) * t
def A(c, a): return tuple(c[:3]) + (int(clamp(a) * 255),)
def appear(t, t0, dur=0.16): return expo((t - t0) / dur)
GL = None; SRC = None; LAYER = None

# ---------------- primitives ----------------
def txt(d, x, y, s, font, col, a=1.0, anchor=None):
    d.text((x, y), s, font=font, fill=A(col, a), anchor=anchor)
def brackets(d, x0, y0, x1, y1, col, L=34, w=4):
    for (cx, cy, sx, sy) in [(x0, y0, 1, 1), (x1, y0, -1, 1), (x0, y1, 1, -1), (x1, y1, -1, -1)]:
        d.line([(cx, cy), (cx + sx * L, cy)], fill=col, width=w); d.line([(cx, cy), (cx, cy + sy * L)], fill=col, width=w)
def lit_bar(d, x0, y0, x1, y1, col, a=1.0):
    h = max(1, int(y1 - y0))
    for i in range(h):
        k = i / h; c = tuple(int(min(255, v * (1.18 - 0.36 * k) + (40 if k < 0.12 else 0))) for v in col)
        d.line([(x0, y0 + i), (x1, y0 + i)], fill=c + (int(255 * clamp(a)),))
def lit_vbar(d, x0, y0, x1, y1, col, a=1.0):  # vertical fill, hot top
    h = max(1, int(y1 - y0))
    for i in range(h):
        k = i / h; c = tuple(int(min(255, v * (1.2 - 0.45 * k) + (50 if i < 6 else 0))) for v in col)
        d.line([(x0, y0 + i), (x1, y0 + i)], fill=c + (int(255 * clamp(a)),))
def tag(d, x, y, label, col=RED, size=32, a=1.0, glow=True):
    if a <= 0: return x
    fn = f(MONOB, size); tw = d.textlength(label, font=fn); h = size + 16
    lit_bar(d, x, y, x + tw + 24, y + h, col, a); d.text((x + 12, y + 5), label, font=fn, fill=A(INK if col in (VGOLD, GREEN, CYAN) else WHITE, a))
    if GL and glow: GL.rectangle([x - 4, y - 4, x + tw + 28, y + h + 4], outline=A(col, a), width=8)
    return x + tw + 24
def tagw(d, label, size): return d.textlength(label, font=f(MONOB, size)) + 24
def arrow(d, x0, y0, x1, y1, col, w=5, a=1.0, L=20):
    d.line([(x0, y0), (x1, y1)], fill=A(col, a), width=w)
    ang = math.atan2(y1 - y0, x1 - x0)
    d.polygon([(x1, y1), (x1 - L * math.cos(ang - 0.45), y1 - L * math.sin(ang - 0.45)), (x1 - L * math.cos(ang + 0.45), y1 - L * math.sin(ang + 0.45))], fill=A(col, a))
def tri_up(d, x, y, s, col, a=1.0): d.polygon([(x, y + s), (x + s, y + s), (x + s / 2, y)], fill=A(col, a))
def tri_dn(d, x, y, s, col, a=1.0): d.polygon([(x, y), (x + s, y), (x + s / 2, y + s)], fill=A(col, a))
def check(d, x, y, col, s=1.0, a=1.0):
    pts = [(x, y + 16 * s), (x + 10 * s, y + 28 * s), (x + 30 * s, y + 2 * s)]
    d.line(pts, fill=A(col, a), width=int(6 * s))
    if GL: GL.line(pts, fill=A(col, a), width=int(12 * s))
def cross(d, x, y, col, s=1.0, a=1.0):
    d.line([(x, y), (x + 28 * s, y + 28 * s)], fill=A(col, a), width=int(6 * s)); d.line([(x + 28 * s, y), (x, y + 28 * s)], fill=A(col, a), width=int(6 * s))
    if GL: GL.line([(x, y), (x + 28 * s, y + 28 * s)], fill=A(col, a), width=12); GL.line([(x + 28 * s, y), (x, y + 28 * s)], fill=A(col, a), width=12)
def flag(d, box, label, t0, t, side='right', size=28):
    p = expo((t - t0) / 0.14)
    if p <= 0: return
    x0, y0, x1, y1 = box; brackets(d, x0, y0, x1, y1, A(RED, 1), 22, 6)
    if GL: brackets(GL, x0, y0, x1, y1, A(RED, 1), 22, 12)
    q = clamp((p - 0.3) / 0.7)
    for seg in [((x0, y0), (lerp(x0, x1, q), y0)), ((x1, y1), (lerp(x1, x0, q), y1)), ((x0, y1), (x0, lerp(y1, y0, q))), ((x1, y0), (x1, lerp(y0, y1, q)))]:
        if q > 0: d.line(seg, fill=A(RED, 1), width=3)
    if p > 0.5 and label:
        if side == 'right': tag(d, x1 + 12, (y0 + y1) / 2 - 22, label, size=size)
        elif side == 'above': tag(d, x0, y0 - 54, label, size=size)
        elif side == 'left': tag(d, x0 - 12 - tagw(d, label, size), (y0 + y1) / 2 - 22, label, size=size)
        else: tag(d, x0, y1 + 10, label, size=size)
def frosted(im, box, dark=0.86, blur=10):
    x0, y0, x1, y1 = [int(v) for v in box]
    x0 = max(0, x0); y0 = max(0, y0); x1 = min(W, x1); y1 = min(H, y1)
    if x1 <= x0 or y1 <= y0: return
    reg = im.crop((x0, y0, x1, y1)).convert('RGB').filter(ImageFilter.GaussianBlur(blur))
    im.paste(Image.blend(reg, Image.new('RGB', reg.size, DEEP), dark).convert('RGBA'), (x0, y0))
def kicker(d, x, y, label, col=VGOLD, a=1.0, prog=1.0, size=26):
    L = 40 * clamp(prog * 2); d.line([(x, y + size * 0.55), (x + L, y + size * 0.55)], fill=A(col, a), width=4)
    q = clamp(prog * 2 - 1)
    if q > 0:
        n = int(len(label) * q + 0.999); txt(d, x + 54, y, label[:n], f(MONOB, size), col, a)
def card(im, t, t0, t1, box, col=VGOLD, motion='rise', dark=0.88):
    """floating glass card; returns (draw, alpha, dx, dy) or None"""
    pin = expo((t - t0) / 0.22); pout = clamp((t - t1) / 0.16)
    if pin <= 0 or pout >= 1: return None
    a = pin * (1 - pout)
    dx = dy = 0
    if motion == 'rise': dy = lerp(70, 0, pin) + 40 * pout
    elif motion == 'right': dx = lerp(520, 0, pin) + 520 * pout ** 2
    elif motion == 'left': dx = lerp(-560, 0, pin) - 560 * pout ** 2
    elif motion == 'up': dy = lerp(560, 0, pin) + 40 * pout
    x0, y0, x1, y1 = box[0] + dx, box[1] + dy, box[2] + dx, box[3] + dy
    frosted(im, (x0, y0, x1, y1), dark * a, 12 * a)
    d = ImageDraw.Draw(LAYER, 'RGBA')
    d.rectangle([x0, y0, x1, y1], outline=A(col, 0.55 * a), width=2)
    brackets(d, x0, y0, x1, y1, A(col, a), 28, 5)
    if GL: brackets(GL, x0, y0, x1, y1, A(col, a), 28, 10)
    return d, a, dx, dy

# ---------------- S1: rewind / age counter (card) ----------------
def sc_rewind(im, t, t0, t1):
    r = card(im, t, t0, t1, (60, 392, 500, 602), VGOLD, 'left')
    if not r: return
    d, a, dx, dy = r; x0, y0 = 60 + dx, 392 + dy
    # rewind glyph + label
    blink = 1 if int(t * 5) % 2 == 0 else 0.35
    for k in range(2):
        d.polygon([(x0 + 52 + k * 22, y0 + 22), (x0 + 52 + k * 22, y0 + 50), (x0 + 30 + k * 22, y0 + 36)], fill=A(VGOLD, a * blink))
    txt(d, x0 + 104, y0 + 20, 'REWIND', f(MONOB, 28), VGOLD, a)
    # slot digits roll and land on 22 (spoken 4.78-5.22)
    land = 5.10
    fn = f(BEB, 128)
    for i in range(2):
        tl = land + i * 0.06
        if t < tl:
            k = int((t - t0) * 30 + i * 3)
            digit = str((k * 7 + 3 * i) % 10); yo = ((t * 30) % 1) * 40 - 20; aa = a * 0.55
        else:
            digit = '2'; yo = lerp(-26, 0, expo((t - tl) / 0.1)); aa = a
        txt(d, x0 + 32 + i * 62, y0 + 64 + yo, digit, fn, WHITE, aa)
    if t >= land:
        b = appear(t, land + 0.1)
        txt(d, x0 + 170, y0 + 84, 'YEARS OLD', f(MONOB, 30), CREAM, a * b)
        if t >= 5.64: tag(d, x0 + 170, y0 + 128, 'FILE: ANGELO', VGOLD, 26, a * appear(t, 5.64))

# ---------------- S2: REALITY 01 heart panel ----------------
def ecg_shape(p):
    g = lambda c, w, h: h * math.exp(-((p - c) / w) ** 2)
    return g(.15, .03, .12) + g(.28, .008, -.15) + g(.30, .011, 1.0) + g(.325, .01, -.28) + g(.56, .055, .3)
def ecg_phase(t):
    r0, r1, a, b = 1.15, 2.5, 9.62, 10.42
    if t < a: return r0 * t
    if t < b: return r0 * a + r0 * (t - a) + (r1 - r0) * (t - a) ** 2 / (2 * (b - a))
    return r0 * a + (r0 + r1) / 2 * (b - a) + r1 * (t - b)
def vgauge(d, x0, y0, x1, y1, frac, label, t, ton, troof, rooftag, a=1.0):
    txt(d, x0, y1 + 12, label, f(MONOB, 26), CREAM, a)
    d.rectangle([x0, y0, x1, y1], outline=A(DIM, a), width=2)
    base = 0.42; yb = lerp(y1, y0, base)
    d.rectangle([x0 + 2, yb, x1 - 2, y1 - 2], fill=A((30, 36, 52), a))
    for yy in range(int(y0) + 2, int(y1), 22): d.line([(x0 + 2, yy), (x0 + 14, yy)], fill=A(GRID, a), width=2)
    d.line([(x0 - 10, yb), (x1 + 10, yb)], fill=A(MUTED, a), width=2)
    txt(d, x1 + 16, yb - 14, 'BASELINE', f(MONO, 22), MUTED, a)
    if t < ton: return
    fh = lerp(base * 0.9, 1.0, expo((t - ton) / 0.7))
    if t >= troof: fh = lerp(1.0, 1.14, expo((t - troof) / 0.35))
    yt = lerp(y1, y0, fh)
    col = CYAN if fh < 0.62 else RED
    lit_vbar(d, x0 + 8, yt, x1 - 8, y1 - 4, col, a)
    if GL: GL.rectangle([x0 + 8, yt, x1 - 8, y1 - 4], fill=A(col, a * 0.55))
    if fh > 1.0:  # bar breaks through the top of the gauge
        for k in range(3):
            yy = y0 - 6 + k * 9; d.line([(x0 - 6, yy), (x1 + 6, yy - 6)], fill=A(INK, a), width=4)
        tri_up(d, (x0 + x1) / 2 - 18, yt - 46, 36, RED, a)
        if GL: tri_up(GL, (x0 + x1) / 2 - 22, yt - 52, 44, RED, a)
    if t >= troof: tag(d, x1 + 16, y0 + 40, rooftag, RED, 28, a * appear(t, troof + 0.1))
def sc_heart(d, t):
    # ECG monitor strip
    x0, x1, ym = 110, 970, 650
    txt(d, x0, 530, 'CARDIAC LOAD', f(MONOB, 28), CREAM)
    for gx in range(x0, x1 + 1, 43): d.line([(gx, 560), (gx, 760)], fill=A((24, 30, 44), 1), width=1)
    for gy in range(560, 761, 40): d.line([(x0, gy), (x1, gy)], fill=A((24, 30, 44), 1), width=1)
    pxps = 430.0; pts = []
    for x in range(x0, x1 + 1, 3):
        ts = t - (x1 - x) / pxps
        if ts < 8.70: continue
        p = ecg_phase(ts) % 1.0
        pts.append((x, ym - 95 * ecg_shape(p)))
    over = t >= 9.62
    col = RED if t > 10.2 else CYAN
    if len(pts) > 1:
        n = len(pts)
        for k, frac in enumerate([0.25, 0.5, 0.75, 1.0]):
            seg = pts[int(n * (frac - 0.25)):int(n * frac) + 1]
            if len(seg) > 1: d.line(seg, fill=A(col, 0.25 + 0.75 * frac), width=5)
        if GL: GL.line(pts[-int(n * 0.35):], fill=A(col, 1), width=10)
        hx, hy = pts[-1]; d.ellipse([hx - 9, hy - 9, hx + 9, hy + 9], fill=A(WHITE, 1))
    rate = ecg_phase(t + 0.5) - ecg_phase(t - 0.5)
    txt(d, x1 - 250, 528, 'RATE', f(MONO, 24), MUTED)
    for i in range(6):
        on = rate > 1.0 + i * 0.28
        d.rectangle([x1 - 180 + i * 30, 532, x1 - 160 + i * 30, 556], fill=A(RED if i >= 3 and on else (CYAN if on else (34, 38, 50)), 1))
    if over: tag(d, x0, 776, 'OVERTIME', RED, 28, appear(t, 9.98))
    # RBC + blood volume gauges
    vgauge(d, 150, 900, 270, 1150, 0, 'RED BLOOD CELLS', t, 10.96, 12.16, 'THROUGH THE ROOF', appear(t, 10.90))
    if t >= 13.10: vgauge(d, 600, 900, 720, 1150, 0, 'BLOOD VOLUME', t, 13.20, 14.54, 'SPIKED', appear(t, 13.10))

# ---------------- S3: 24/7 immune dial (card) ----------------
def sc_dial(im, t, t0, t1):
    box = (600, 384, 1022, 774)
    r = card(im, t, t0, t1, box, RED, 'right')
    if not r: return
    d, a, dx, dy = r; x0, y0 = box[0] + dx, box[1] + dy
    txt(d, x0 + 24, y0 + 18, 'IMMUNE RESPONSE', f(MONOB, 26), CREAM, a)
    cx, cy, R = x0 + 211, y0 + 214, 118
    prog = clamp((t - 17.62) / 1.0)  # fills across "24/7"
    n = 24 * expo(prog) if prog < 1 else 24
    for i in range(24):
        s0 = -90 + i * 15 + 1.5; s1 = s0 + 12
        on = i < n
        col = RED if on else (40, 44, 58)
        d.arc([cx - R, cy - R, cx + R, cy + R], s0, s1, fill=A(col, a), width=24)
        if on and GL: GL.arc([cx - R - 6, cy - R - 6, cx + R + 6, cy + R + 6], s0, s1, fill=A(RED, a), width=30)
    for hr, (ox, oy) in [('00', (0, -1)), ('06', (1, 0)), ('12', (0, 1)), ('18', (-1, 0))]:
        fn = f(MONO, 20); tw = d.textlength(hr, font=fn)
        txt(d, cx + ox * (R + 30) - tw / 2, cy + oy * (R + 30) - 12, hr, fn, MUTED, a)
    if t < 17.62:
        txt(d, cx, cy - 6, 'ACTIVE', f(BEB, 58), WHITE, a, 'mm')
    elif t < 23.80:
        txt(d, cx, cy - 18, '24/7', f(BEB, 84), WHITE, a, 'mm'); txt(d, cx, cy + 34, 'ALWAYS ON', f(MONOB, 20), RED, a, 'mm')
    else:
        pulse = 0.7 + 0.3 * math.sin(t * 10)
        txt(d, cx, cy - 4, 'CHRONIC', f(BEB, 58), RED, a * pulse, 'mm')
        if GL: GL.ellipse([cx - 70, cy - 40, cx + 70, cy + 34], fill=A(RED, 0.25 * a * pulse))
    # outside tags hang off the top edge of the card
    if 19.54 <= t < 23.80: tag(d, x0 - 12 - tagw(d, 'FORCED TISSUE GROWTH', 26), y0 + 330, 'FORCED TISSUE GROWTH', VGOLD, 26, a * appear(t, 19.54))
    if t >= 23.80: tag(d, x0 - 12 - tagw(d, 'INFLAMMATION', 26), y0 + 330, 'INFLAMMATION', RED, 26, a * appear(t, 23.80))

# ---------------- S4: scale + 10-week line chart (card) ----------------
def sc_weight(im, t, t0, t1):
    box = (58, 384, 1022, 766)
    r = card(im, t, t0, t1, box, VGOLD, 'rise')
    if not r: return
    d, a, dx, dy = r; x0, y0 = box[0] + dx, box[1] + dy
    txt(d, x0 + 26, y0 + 20, 'SCALE · THIS MORNING', f(MONOB, 24), VGOLD, a)
    v = 0 if t < 26.72 else int(round(224 * expo((t - 26.72) / 0.55)))
    if t >= 27.40: v = 224
    fn = f(BEB, 170); s = f'{v:03d}'
    txt(d, x0 + 26, y0 + 70, s, fn, WHITE, a); tw = d.textlength(s, font=fn)
    txt(d, x0 + 34 + tw, y0 + 168, 'LB', f(BEB, 60), VGOLD, a)
    if GL and t >= 27.40: GL.rectangle([x0 + 26, y0 + 92, x0 + 26 + tw, y0 + 232], outline=A(VGOLD, a * 0.5), width=6)
    # chart
    cx0, cx1, cy0, cy1 = x0 + 420, x0 + 930, y0 + 60, y0 + 300
    d.line([(cx0, cy1), (cx1, cy1)], fill=A(DIM, a), width=2); d.line([(cx0, cy0), (cx0, cy1)], fill=A(DIM, a), width=2)
    for k in range(1, 4): d.line([(cx0, cy1 - k * 60), (cx1, cy1 - k * 60)], fill=A(GRID, a), width=1)
    wk_a = appear(t, 30.36, 0.2)
    for i in range(11):
        xx = lerp(cx0 + 10, cx1 - 10, i / 10); d.line([(xx, cy1), (xx, cy1 + 8)], fill=A(DIM, a), width=2)
    txt(d, cx0, cy1 + 14, 'WK 0', f(MONO, 22), MUTED, a); fn2 = f(MONOB, 22); tw2 = d.textlength('WK 10', font=fn2)
    txt(d, cx1 - tw2, cy1 + 14, 'WK 10', fn2, lerp_col(MUTED, VGOLD, wk_a), a)
    ya, yb = cy1 - 40, cy0 + 20
    p = clamp((t - 29.10) / 1.3)
    if p > 0:
        pe = ease_io(p); xa, xb = cx0 + 10, cx1 - 10
        xe = lerp(xa, xb, pe); ye = lerp(ya, yb, pe)
        d.polygon([(xa, cy1), (xa, ya), (xe, ye), (xe, cy1)], fill=A(VGOLD, 0.16 * a))
        d.line([(xa, ya), (xe, ye)], fill=A(VGOLD, a), width=6)
        if GL: GL.line([(xa, ya), (xe, ye)], fill=A(VGOLD, a), width=12)
        for i in range(11):
            xx = lerp(xa, xb, i / 10)
            if xx <= xe + 1: yy = lerp(ya, yb, i / 10); d.ellipse([xx - 6, yy - 6, xx + 6, yy + 6], fill=A(WHITE, a))
        # delta bracket
        d.line([(xb + 4, ya), (xb + 20, ya)], fill=A(MUTED, a * pe), width=2)
        if p >= 1:
            d.line([(xb + 14, ya), (xb + 14, yb)], fill=A(VGOLD, a), width=3)
    if t >= 29.10: tag(d, cx0 + 20, cy0 - 8, '+18 LB', VGOLD, 30, a * appear(t, 29.10))
    if t >= 30.36: tag(d, cx0 + 210, cy0 - 8, 'IN 10 WEEKS', CYAN, 30, a * wk_a)
def lerp_col(c1, c2, k): return tuple(int(lerp(u, v, clamp(k))) for u, v in zip(c1, c2))

# ---------------- S5: MIRROR vs BLOODWORK split screen (full) ----------------
def range_bar(d, x0, y, x1, label, sub, ref, val_frac, t, t_move, val_txt, flagtxt, a=1.0, overshoot=False):
    txt(d, x0, y, label, f(MONOB, 28), WHITE, a); txt(d, x0, y + 34, sub, f(MONO, 20), MUTED, a)
    by = y + 80; d.rectangle([x0, by, x1, by + 22], fill=A((30, 34, 46), a))
    r0, r1 = lerp(x0, x1, ref[0]), lerp(x0, x1, ref[1])
    d.rectangle([r0, by, r1, by + 22], fill=A((60, 70, 90), a)); txt(d, r0, by + 28, 'REF RANGE', f(MONO, 18), MUTED, a)
    if t < t_move: m = lerp(x0, x1, (ref[0] + ref[1]) / 2)
    else:
        k = expo((t - t_move) / 0.45); m = lerp(lerp(x0, x1, (ref[0] + ref[1]) / 2), lerp(x0, x1, val_frac), k)
    hot = m > r1 + 4
    col = RED if hot else CYAN
    if overshoot and m > x1:  # marker leaves the scale
        d.rectangle([r1, by, x1, by + 22], fill=A(RED, a * 0.6))
        arrow(d, x1 - 30, by + 11, x1 + 34, by + 11, RED, 8, a, 26)
        if GL: GL.line([(x1 - 30, by + 11), (x1 + 30, by + 11)], fill=A(RED, a), width=16)
    else:
        d.polygon([(m - 14, by - 22), (m + 14, by - 22), (m, by - 2)], fill=A(col, a)); d.line([(m, by - 2), (m, by + 24)], fill=A(col, a), width=4)
        if GL: GL.line([(m, by - 20), (m, by + 24)], fill=A(col, a), width=10)
        if hot and val_txt: txt(d, m - 6 - d.textlength(val_txt, font=f(BEB, 56)), by - 74, val_txt, f(BEB, 56), RED, a)
    if hot and flagtxt: tag(d, x0 + d.textlength(label, font=f(MONOB, 28)) + 16, y - 6, flagtxt, RED, 24, a)
def sc_mirror(im, t, t0, t1):
    pin = expo((t - t0) / 0.22); pout = clamp((t - t1) / 0.14)
    if pin <= 0 or pout >= 1: return
    a = pin * (1 - pout)
    L = (58, 440, 520, 1262); R = (546, 440, 1022, 1262)
    # mirror: live crop of the footage (him), framed
    wipe = expo((t - t0) / 0.30)
    mw, mh = L[2] - L[0] - 24, L[3] - L[1] - 90
    ch = 820; cw = int(ch * mw / mh); cx = 540; cy = 760
    crop = SRC.crop((cx - cw // 2, cy - ch // 2, cx + cw // 2, cy + ch // 2)).resize((mw, mh), Image.BILINEAR).convert('RGBA')
    frosted(im, L, 0.9 * a, 10); frosted(im, R, 0.92 * a, 10)
    vis = int(mw * wipe)
    if vis > 0:
        im.alpha_composite(crop.crop((0, 0, vis, mh)), (L[0] + 12, L[1] + 66))
    d = ImageDraw.Draw(LAYER, 'RGBA')
    # mirror sheen
    xx = L[0] + 20 + int((t - t0) * 90) % 520
    if xx < L[2] - 150: d.line([(xx, L[3] - 100), (xx + 130, L[1] + 70)], fill=(255, 255, 255, int(16 * a)), width=26)
    d.rectangle(L, outline=A(VGOLD, 0.6 * a), width=2); brackets(d, *L, A(VGOLD, a), 30, 5)
    if GL: brackets(GL, *L, A(VGOLD, a), 30, 10)
    txt(d, L[0] + 22, L[1] + 18, 'THE MIRROR', f(MONOB, 28), VGOLD, a)
    if t >= 33.56:
        b = appear(t, 33.56); y = L[3] - 80
        lit_bar(d, L[0] + 12, y, L[2] - 12, y + 68, VGOLD, a * b); check(d, L[0] + 30, y + 18, INK, 1.0, a * b)
        txt(d, L[0] + 76, y + 6, 'LOOKS LIKE A TANK', f(BEB, 56), INK, a * b)
    if t >= 36.36:  # mirror can't see labs
        b = appear(t, 36.36, 0.12)
        d.rectangle([L[0] + 12, L[1] + 66, L[2] - 12, L[3] - 90], fill=A((5, 8, 16), 0.45 * a * b))
        tag(d, L[0] + 22, L[1] + 84, "CAN'T SEE BLOODWORK", RED, 24, a * b)
    # right column: bloodwork
    d.rectangle(R, outline=A(CYAN, 0.5 * a), width=2); brackets(d, *R, A(CYAN, a), 30, 5)
    if GL: brackets(GL, *R, A(CYAN, a), 30, 10)
    txt(d, R[0] + 22, R[1] + 18, 'YOUR BLOODWORK', f(MONOB, 28), CYAN, a)
    if t < 34.36:
        blink = 0.4 + 0.6 * (int(t * 3) % 2)
        txt(d, (R[0] + R[2]) / 2, 840, 'AWAITING LABS', f(MONOB, 28), MUTED, a * blink, 'mm')
        return
    b = appear(t, 34.36, 0.25)
    # organ function trend (falls)
    x0, x1, y0, y1 = R[0] + 30, R[2] - 30, R[1] + 120, R[1] + 300
    txt(d, x0, R[1] + 80, 'ORGAN FUNCTION', f(MONOB, 26), WHITE, a * b)
    d.line([(x0, y1), (x1, y1)], fill=A(DIM, a * b), width=2)
    for k in range(1, 3): d.line([(x0, y1 - k * 60), (x1, y1 - k * 60)], fill=A(GRID, a * b), width=1)
    vals = [0.9, 0.86, 0.8, 0.68, 0.5, 0.28, 0.1]
    pts = [(lerp(x0 + 10, x1 - 10, i / 6), lerp(y1 - 6, y0 + 10, v)) for i, v in enumerate(vals)]
    p = clamp((t - 35.08) / 1.1) * 6
    for i in range(6):
        if p > i:
            q = min(1, p - i); e = (lerp(pts[i][0], pts[i + 1][0], q), lerp(pts[i][1], pts[i + 1][1], q))
            col = CYAN if i < 3 else RED
            d.line([pts[i], e], fill=A(col, a), width=6)
            if GL: GL.line([pts[i], e], fill=A(col, a), width=12)
    if t >= 35.96: tri_dn(d, x1 - 40, y0 - 4, 30, RED, a); tag(d, x1 - 200 - 40, y0 - 12, 'DECLINING', RED, 24, a * appear(t, 35.96))
    # hematocrit + liver enzymes
    if t >= 37.20:
        range_bar(d, x0, R[1] + 360, x1, 'HEMATOCRIT', 'HCT · %', (0.30, 0.62), 0.92, t, 37.80, '58', 'HIGH', a * appear(t, 37.20))
    if t >= 38.70:
        range_bar(d, x0, R[1] + 560, x1, 'LIVER ENZYMES', 'ALT · AST', (0.18, 0.45), 1.25, t, 39.40, '', 'OFF THE SCALE', a * appear(t, 38.70), overshoot=True)

# ---------------- S6: the trade receipt (paper card) ----------------
_GRAIN = None
def sc_receipt(im, t, t0, t1):
    global _GRAIN
    pin = clamp((t - t0) / 0.42); pout = clamp((t - t1) / 0.2)
    if pin <= 0 or pout >= 1: return
    rows = [(41.80, 'BOUGHT', 'AESTHETICS', INK), (43.00, 'PAID WITH', 'YEARS', (200, 10, 20)),
            (45.66, 'REPEAT', 'x2', INK), (46.08, 'REPEAT', 'x3', INK)]
    pw = 400; base_h = 150; rh = 50
    nrows = sum(1 for r in rows if t >= r[0])
    # paper feeds out smoothly as rows print
    grow = 0
    for r in rows:
        if t >= r[0]: grow += rh * expo((t - r[0]) / 0.25)
    ph = int(base_h + grow + 46)
    if _GRAIN is None:
        rng = np.random.default_rng(3); _GRAIN = (rng.standard_normal((700, pw)) * 7).astype(np.int16)
    paper = np.full((ph, pw, 3), (236, 232, 221), np.int16) + _GRAIN[:ph, :, None]
    pim = Image.fromarray(np.clip(paper, 0, 255).astype(np.uint8)).convert('RGBA'); d = ImageDraw.Draw(pim)
    # zigzag torn bottom
    for x in range(0, pw, 16): d.polygon([(x, ph), (x + 8, ph - 10), (x + 16, ph)], fill=(0, 0, 0, 0))
    m = f(MONOB, 24); m2 = f(MONO, 20)
    d.text((22, 16), 'REALITY 03', font=m2, fill=(110, 110, 116)); d.text((22, 40), 'TRANSACTION', font=f(BEB, 56), fill=INK)
    d.line([(18, 104), (pw - 18, 104)], fill=(120, 120, 125), width=2)
    d.text((22, 114), 'CUSTOMER', font=m2, fill=(110, 110, 116)); d.text((pw - 22, 114), 'YOU, 22', font=m2, fill=INK, anchor='ra')
    for i, (tt, k, v, col) in enumerate(rows):
        if t < tt: continue
        y = base_h + i * rh + 6
        d.text((24, y), k, font=m, fill=(90, 90, 96))
        d.text((pw - 24, y - 2), v, font=f(MONOB, 28), fill=col, anchor='ra')
        for xx in range(int(24 + d.textlength(k, font=m) + 12), int(pw - 30 - d.textlength(v, font=f(MONOB, 28))), 12):
            d.ellipse([xx, y + 22, xx + 3, y + 25], fill=(160, 160, 166))
    if nrows >= 2:
        y = base_h + nrows * rh + 4; d.line([(20, y), (pw - 20, y)], fill=(120, 120, 125), width=2)
    # stamp on "22 years old"
    if t >= 47.12:
        k = expo((t - 47.12) / 0.12); sc = lerp(1.5, 1.0, k)
        st = Image.new('RGBA', (300, 130), (0, 0, 0, 0)); sd = ImageDraw.Draw(st)
        sd.rounded_rectangle([6, 6, 294, 124], radius=12, outline=(210, 12, 24, 230), width=7)
        sd.text((150, 66), 'NO REFUNDS', font=f(BEB, 64), fill=(210, 12, 24, 230), anchor='mm')
        st = st.rotate(-11, expand=True, resample=Image.BICUBIC).resize((int(320 * sc), int(170 * sc)), Image.BICUBIC)
        st.putalpha(st.split()[3].point(lambda v: int(v * k)))
        st = st.resize((int(st.width * 0.7), int(st.height * 0.7)), Image.BICUBIC); pim.alpha_composite(st, (pw - st.width - 4, 4))
    # drop shadow + tilt + entry from below
    rot = pim.rotate(3.2, expand=True, resample=Image.BICUBIC)
    sh = Image.new('RGBA', rot.size, (0, 0, 0, 0)); sh.putalpha(rot.split()[3].point(lambda v: int(v * 0.6)))
    sh = sh.filter(ImageFilter.GaussianBlur(14))
    e = back(pin); y = 372
    x = int(lerp(-rot.width - 40, 52, e) - 600 * pout ** 2)
    al = 1 - pout
    if al < 1:
        rot.putalpha(rot.split()[3].point(lambda v: int(v * al)))
    im.alpha_composite(sh, (x + 14, y + 22)); im.alpha_composite(rot, (x, y))

# ---------------- S7: lifespan dual-path chart (panel) ----------------
def age_x(age): return lerp(150, 960, (age - 18) / 64)
def sc_life(d, t):
    x0, x1, y0, y1 = 150, 960, 560, 1090
    txt(d, 110, 520, 'PHYSIQUE', f(MONO, 22), MUTED)
    d.line([(x0, y1), (x1, y1)], fill=A(DIM, 1), width=2); d.line([(x0, y0), (x0, y1)], fill=A(DIM, 1), width=2)
    for age in (22, 50, 80):
        xx = age_x(age); d.line([(xx, y1), (xx, y1 + 12)], fill=A(DIM, 1), width=3)
        hot = (age == 22 and t >= 49.94) or (age == 50 and t >= 51.50) or (age == 80 and t >= 53.72)
        txt(d, xx, y1 + 40, f'AGE {age}', f(MONOB, 28), WHITE if hot else MUTED, 1, 'mm')
    for k in range(1, 5): d.line([(x0, y1 - k * 100), (x1, y1 - k * 100)], fill=A(GRID, 1), width=1)
    # path A: peak at 22, ends at 50
    pa = clamp((t - 49.18) / 1.9)
    if pa > 0:
        ages = np.linspace(22, 50, 60); ya = [lerp(610, 700, ((g - 22) / 28) ** 2.2) for g in ages]
        n = max(2, int(len(ages) * ease_io(pa)))
        pts = [(age_x(g), y) for g, y in zip(ages[:n], ya[:n])]
        d.line(pts, fill=A(VGOLD, 1), width=7)
        if GL: GL.line(pts, fill=A(VGOLD, 1), width=14)
        d.ellipse([pts[0][0] - 10, pts[0][1] - 10, pts[0][0] + 10, pts[0][1] + 10], fill=A(WHITE, 1))
        tag(d, age_x(22) + 14, 548, 'PEAK AT 22', VGOLD, 26, appear(t, 49.40))
        if pa >= 1 and t >= 50.98:
            ex, ey = pts[-1]; b = appear(t, 50.98)
            d.line([(ex, ey), (ex, y1)], fill=A(RED, b), width=3)
            cross(d, ex - 18, ey - 18, RED, 1.3, b)
            tag(d, ex + 22, ey - 22, 'ENDS AT 50', RED, 26, b)
    pb = clamp((t - 52.22) / 1.5)
    if pb > 0:
        ages = np.linspace(22, 80, 80); yb = [lerp(840, 900, (g - 22) / 58) for g in ages]
        n = max(2, int(len(ages) * ease_io(pb)))
        pts = [(age_x(g), y) for g, y in zip(ages[:n], yb[:n])]
        d.line(pts, fill=A(CYAN, 1), width=6)
        if GL: GL.line(pts, fill=A(CYAN, 0.8), width=12)
        if pb >= 0.6: tag(d, age_x(52), 936, 'AVERAGE AT 80', CYAN, 26, appear(t, 52.22 + 0.9))
def stamp_false(im, t, t_hit, t1):
    if t < t_hit or t > t1 + 0.16: return
    k = expo((t - t_hit) / 0.10); sc = lerp(1.6, 1.0, k); a = k * (1 - clamp((t - t1) / 0.16))
    st = Image.new('RGBA', (760, 190), (0, 0, 0, 0)); sd = ImageDraw.Draw(st)
    lit_bar(sd, 0, 0, 760, 190, RED, 1); sd.rectangle([0, 182, 760, 190], fill=(120, 0, 0, 255))
    sd.text((380, 100), 'FALSE CHOICE', font=f(BEB, 150), fill=WHITE, anchor='mm')
    st = st.rotate(7, expand=True, resample=Image.BICUBIC)
    st = st.resize((int(st.width * sc), int(st.height * sc)), Image.BICUBIC)
    st.putalpha(st.split()[3].point(lambda v: int(v * a)))
    st = st.resize((int(st.width * 0.8), int(st.height * 0.8)), Image.BICUBIC)
    im.alpha_composite(st, (int(540 - st.width / 2), int(985 - st.height / 2)))
    if GL: GL.rectangle([540 - st.width / 2 + 20, 985 - st.height / 2 + 30, 540 + st.width / 2 - 20, 985 + st.height / 2 - 30], outline=A(RED, a), width=14)

# ---------------- S8: disclaimer lower third with right/wrong switch ----------------
def sc_switch(im, t, t0, t1):
    box = (58, 300, 1022, 512)
    r = card(im, t, t0, t1, box, VGOLD, 'rise')
    if not r: return
    d, a, dx, dy = r; x0, y0 = box[0] + dx, box[1] + dy
    kicker(d, x0 + 26, y0 + 18, 'NOT A GREEN LIGHT', VGOLD, a, clamp((t - t0) / 0.5), 24)
    if t < 61.20:
        txt(d, x0 + 26, y0 + 92, 'ANABOLIC STEROIDS', f(BEB, 84), WHITE, a)
        if t >= 58.66:
            b = expo((t - 58.66) / 0.16); xx = lerp(x0 + 990, x0 + 600, b)
            lit_bar(d, xx, y0 + 96, xx + 330, y0 + 176, RED, a * b); txt(d, xx + 165, y0 + 136, 'NOT SAFE', f(BEB, 70), WHITE, a * b, 'mm')
            if GL: GL.rectangle([xx - 4, y0 + 92, xx + 334, y0 + 180], outline=A(RED, a * b), width=10)
        return
    # toggle: RIGHT WAY | WRONG WAY
    b = appear(t, 61.20, 0.2)
    sx0, sx1, sy0, sy1 = x0 + 26, x0 + 938, y0 + 78, y0 + 182
    d.rounded_rectangle([sx0, sy0, sx1, sy1], radius=52, fill=A((16, 20, 30), a * b), outline=A(DIM, a * b), width=3)
    mid = (sx0 + sx1) / 2
    k = 0 if t < 62.46 else expo((t - 62.46) / 0.22)
    kx0 = lerp(sx0 + 8, mid + 4, k); kx1 = lerp(mid - 4, sx1 - 8, k)
    col = VGOLD if k < 0.5 else RED
    d.rounded_rectangle([kx0, sy0 + 8, kx1, sy1 - 8], radius=44, fill=A(col, a * b))
    if GL: GL.rounded_rectangle([kx0, sy0 + 8, kx1, sy1 - 8], radius=44, outline=A(col, a * b), width=10)
    txt(d, (sx0 + mid) / 2, (sy0 + sy1) / 2, 'RIGHT WAY', f(BEB, 66), INK if k < 0.5 else MUTED, a * b, 'mm')
    txt(d, (mid + sx1) / 2, (sy0 + sy1) / 2, 'WRONG WAY', f(BEB, 66), WHITE if k >= 0.5 else MUTED, a * b, 'mm')

# ---------------- S9: "when you know" checklist (card, left) ----------------
def sc_check(im, t, t0, t1):
    box = (58, 290, 1022, 640)
    r = card(im, t, t0, t1, box, VGOLD, 'left')
    if not r: return
    d, a, dx, dy = r; x0, y0 = box[0] + dx, box[1] + dy
    kicker(d, x0 + 26, y0 + 20, 'WHEN YOU KNOW', VGOLD, a, clamp((t - t0) / 0.5), 26)
    items = [(65.10, 'THE COST'), (65.92, 'YOUR BIOMARKERS'), (67.02, 'YOUR BLOODWORK'), (68.16, 'SIDE-EFFECT CONTROL')]
    for i, (tt, nm) in enumerate(items):
        cx_ = x0 + 26 + (i % 2) * 470; y = y0 + 80 + (i // 2) * 84
        d.rectangle([cx_, y, cx_ + 44, y + 44], outline=A(DIM, a), width=3)
        if t >= tt:
            b = appear(t, tt, 0.12)
            check(d, cx_ + 7, y + 6, GREEN, 1.0, a * b)
            txt(d, cx_ + 64, y + 2 + lerp(10, 0, b), nm, f(BEB, 50), WHITE, a * b)
        else:
            d.line([(cx_ + 64, y + 26), (cx_ + 330, y + 26)], fill=A(GRID, a), width=3)
    if t >= 69.46:
        b = expo((t - 69.46) / 0.2); y = y0 + 258
        lit_bar(d, x0 + 26, y, lerp(x0 + 26, x0 + 938, b), y + 66, VGOLD, a)
        if b > 0.6: txt(d, x0 + 46, y + 4, 'OUTCOME CHANGES', f(BEB, 60), INK, a)
        if GL: GL.rectangle([x0 + 22, y - 4, lerp(x0 + 26, x0 + 942, b), y + 70], outline=A(VGOLD, a), width=10)

# ---------------- S10: silent damage threshold chart (panel) ----------------
def sc_silent(d, t):
    x0, x1, y0, y1 = 120, 960, 560, 1150
    thr = 760
    d.line([(x0, y1), (x1, y1)], fill=A(DIM, 1), width=2); d.line([(x0, y0), (x0, y1)], fill=A(DIM, 1), width=2)
    txt(d, x0, y1 + 14, 'TIME ON CYCLE', f(MONO, 22), MUTED); txt(d, x0 + 10, y0 - 34, 'DAMAGE', f(MONO, 22), MUTED)
    # silent zone hatching under the threshold
    for k in range(-600, 900, 34):
        a0 = (x0 + k, y1); a1 = (x0 + k + (y1 - thr), thr)
        # clip to box
        if a0[0] < x0: a0 = (x0, y1 - (x0 - a0[0]))
        if a1[0] > x1: a1 = (x1, thr + (a1[0] - x1))
        if a0[0] < a1[0] and a0[1] > thr: d.line([a0, a1], fill=A((26, 32, 46), 1), width=3)
    txt(d, x0 + 30, thr + 24, 'SILENT ZONE', f(MONOB, 30), MUTED); txt(d, x0 + 30, thr + 62, 'NO SYMPTOMS · NO SIGNAL', f(MONO, 22), (130, 134, 146))
    for xx in range(x0, x1, 28): d.line([(xx, thr), (xx + 16, thr)], fill=A(CREAM, 1), width=3)
    txt(d, x0 + 20, thr - 36, 'SYMPTOM THRESHOLD', f(MONOB, 24), CREAM)
    # damage curve: rises silently, crosses at "damage is done"
    t_start, t_cross = 70.95, 74.32
    def cy(u): return y1 - 20 - (y1 - 20 - thr) * (math.exp(3.0 * u) - 1) / (math.exp(3.0) - 1) * 1.0
    p = clamp((t - t_start) / (t_cross - t_start))
    u_end = 0.82 * ease_io(p) if t < t_cross else lerp(0.82, 1.0, expo((t - t_cross) / 1.2))
    us = np.linspace(0, u_end, 80)
    pts = [(lerp(x0 + 10, x1 - 10, u), cy(u / 0.82) if u <= 0.82 else thr - (u - 0.82) / 0.18 * 190) for u in us]
    if len(pts) > 1:
        below = [p_ for p_ in pts if p_[1] >= thr]; above = [p_ for p_ in pts if p_[1] <= thr]
        if len(below) > 1:
            d.polygon(below + [(below[-1][0], y1), (below[0][0], y1)], fill=A((120, 30, 30), 0.35))
            d.line(below, fill=A((190, 70, 60), 1), width=5)
        if len(above) > 1:
            d.polygon(above + [(above[-1][0], thr), (above[0][0], thr)], fill=A(RED, 0.35))
            d.line(above, fill=A(RED, 1), width=7)
            if GL: GL.line(above, fill=A(RED, 1), width=14)
        hx, hy = pts[-1]; d.ellipse([hx - 9, hy - 9, hx + 9, hy + 9], fill=A(WHITE, 1))
    if t >= 71.64:
        pulse = 1 if int(t * 4) % 2 == 0 else 0.35
        d.ellipse([x0 + 24, y0 + 30, x0 + 44, y0 + 50], fill=A(RED, pulse)); txt(d, x0 + 56, y0 + 24, 'STRESS · CONSTANT', f(MONOB, 26), RED)
    if t >= t_cross:
        cxp = lerp(x0 + 10, x1 - 10, 0.82)
        flag(d, (cxp - 26, thr - 26, cxp + 26, thr + 26), 'FIRST SYMPTOM', t_cross, t, 'below', 26)
        if t < t_cross + 0.25 and GL: GL.ellipse([cxp - 80, thr - 80, cxp + 80, thr + 80], fill=A(RED, 1 - (t - t_cross) / 0.25))
    if t >= 75.38: tag(d, x0 + 30, 650, 'DAMAGE ALREADY DONE', RED, 28, appear(t, 75.38))

# ---------------- S11: bloodwork roadmap (full) ----------------
_TOPO = None
def topo(w, h):
    global _TOPO
    if _TOPO is None:
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
        z = np.sin(xx / 110 + np.sin(yy / 160) * 1.3) + np.cos(yy / 95 + np.cos(xx / 210) * 1.1) + 0.5 * np.sin((xx + yy) / 70)
        band = np.abs(((z * 3) % 1) - 0.5) < 0.035
        img = np.zeros((h, w, 4), np.uint8); img[..., 0] = 8; img[..., 1] = 12; img[..., 2] = 22; img[..., 3] = 255
        img[band] = (26, 36, 58, 255)
        for gx in range(0, w, 120): img[:, gx:gx + 1] = (18, 24, 40, 255)
        for gy in range(0, h, 120): img[gy:gy + 1, :] = (18, 24, 40, 255)
        _TOPO = Image.fromarray(img, 'RGBA')
    return _TOPO
def catmull(pts, n=40):
    out = []
    P = [pts[0]] + pts + [pts[-1]]
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        for k in range(n):
            s = k / n
            out.append(tuple(0.5 * ((2 * p1[j]) + (-p0[j] + p2[j]) * s + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * s * s + (-p0[j] + 3 * p1[j] - 3 * p2[j] + p3[j]) * s ** 3) for j in range(2)))
    out.append(pts[-1]); return out
WAY = [((200, 610), 'BLOODWORK', 77.92), ((820, 720), 'EKG / ECG', 79.14), ((250, 880), 'BIOMARKERS', 81.76),
       ((800, 1020), 'CROSS-REFERENCE', 83.00), ((330, 1170), 'SIDE-EFFECT PROFILE', 85.46)]
_ROUTE = None
def sc_road(im, t, t0, t1):
    global _ROUTE
    pin = expo((t - t0) / 0.25); pout = clamp((t - t1) / 0.16)
    if pin <= 0 or pout >= 1: return
    a = pin * (1 - pout)
    box = (58, 440, 1022, 1262)
    tp = topo(box[2] - box[0], box[3] - box[1]).copy()
    if a < 1: tp.putalpha(int(255 * a))
    oy = int(lerp(40, 0, pin))
    im.alpha_composite(tp, (box[0], box[1] + oy))
    d = ImageDraw.Draw(LAYER, 'RGBA')
    d.rectangle([box[0], box[1] + oy, box[2], box[3] + oy], outline=A(VGOLD, 0.6 * a), width=2); brackets(d, box[0], box[1] + oy, box[2], box[3] + oy, A(VGOLD, a), 40, 6)
    if GL: brackets(GL, box[0], box[1] + oy, box[2], box[3] + oy, A(VGOLD, a), 40, 12)
    txt(d, box[0] + 26, box[1] + 18 + oy, 'THE ROADMAP', f(MONOB, 28), VGOLD, a)
    tw = d.textlength('ROUTE · 5 STOPS', font=f(MONO, 24)); txt(d, box[2] - 26 - tw, box[1] + 20 + oy, 'ROUTE · 5 STOPS', f(MONO, 24), MUTED, a)
    if _ROUTE is None: _ROUTE = catmull([w[0] for w in WAY], 50)
    route = [(x, y + oy) for x, y in _ROUTE]
    # dashed preview
    for i in range(0, len(route) - 1, 6): d.line([route[i], route[min(i + 3, len(route) - 1)]], fill=A((70, 80, 100), a), width=4)
    # progress along route
    seg_n = 50; prog = 0.0
    for i, (_, _, tt) in enumerate(WAY):
        if i == 0: continue
        prog += expo((t - (tt - 0.45)) / 0.55)
    idx = int(prog * seg_n)
    if idx > 0:
        lit = route[:idx + 1]
        d.line(lit, fill=A(VGOLD, a), width=8)
        if GL: GL.line(lit, fill=A(VGOLD, a), width=16)
    hx, hy = route[min(idx, len(route) - 1)]
    d.ellipse([hx - 12, hy - 12, hx + 12, hy + 12], fill=A(WHITE, a))
    if GL: GL.ellipse([hx - 22, hy - 22, hx + 22, hy + 22], fill=A(VGOLD, a))
    # cross-reference links
    if t >= 83.00:
        b = clamp((t - 83.0) / 0.6)
        for (p, q) in [(WAY[2][0], WAY[0][0]), (WAY[2][0], WAY[1][0])]:
            px, py = p; qx, qy = q; ex, ey = lerp(px, qx, b), lerp(py, qy, b)
            n = 14
            for k in range(n):
                if k % 2 == 0:
                    s0, s1 = k / n, (k + 1) / n
                    d.line([(lerp(px, ex, s0), lerp(py, ey, s0) + oy), (lerp(px, ex, s1), lerp(py, ey, s1) + oy)], fill=A(CYAN, a), width=4)
    # waypoints
    for i, ((x, y), nm, tt) in enumerate(WAY):
        y += oy
        on = t >= tt
        b = appear(t, tt, 0.14) if on else 0
        col = VGOLD if on else DIM
        d.ellipse([x - 26, y - 26, x + 26, y + 26], fill=A((10, 14, 24), a), outline=A(col, a), width=5)
        txt(d, x, y, f'{i + 1}', f(BEB, 40), WHITE if on else MUTED, a, 'mm')
        if on:
            if GL: GL.ellipse([x - 30, y - 30, x + 30, y + 30], outline=A(VGOLD, a * b), width=10)
            fn = f(BEB, 58); tw = d.textlength(nm, font=fn)
            lx = x + 44 if x < 540 else x - 44 - tw
            txt(d, lx, y - 32 + lerp(12, 0, b), nm, fn, WHITE, a * b)

# ---------------- S12: lab history grid (card) ----------------
def sc_grid(im, t, t0, t1):
    box = (58, 280, 1022, 702)
    r = card(im, t, t0, t1, box, CYAN, 'rise')
    if not r: return
    d, a, dx, dy = r; x0, y0 = box[0] + dx, box[1] + dy
    kicker(d, x0 + 26, y0 + 20, 'AGE 35+ · LAB HISTORY', CYAN, a, clamp((t - t0) / 0.6), 26)
    cols, rows = 12, 3; gx0, gy0, cw, chh, gap = x0 + 110, y0 + 80, 64, 66, 6
    for rr in range(rows): txt(d, x0 + 26, gy0 + rr * (chh + gap) + 20, f'YR {rr + 1}', f(MONO, 22), MUTED, a)
    sweep = clamp((t - 89.40) / 1.4) * cols * rows
    last = cols * rows - 1
    for i in range(cols * rows):
        rr, cc = divmod(i, cols); x = gx0 + cc * (cw + gap); y = gy0 + rr * (chh + gap)
        if i == last and t >= 91.36:
            b = appear(t, 91.36, 0.1)
            d.rectangle([x, y, x + cw, y + chh], fill=A(RED, a * b))
            if GL: GL.rectangle([x - 4, y - 4, x + cw + 4, y + chh + 4], outline=A(RED, a * b), width=10)
            d.line([(x + 8, y + 10), (x + 30, y + 34), (x + 20, y + 44), (x + 54, y + 62)], fill=A(INK, a * b), width=4)
            continue
        d.rectangle([x, y, x + cw, y + chh], fill=A((18, 22, 32), a), outline=A((40, 46, 60), a), width=2)
        if i < sweep:
            k = clamp(sweep - i)
            d.line([(x + 22, y + 25), (x + 42, y + 45)], fill=A(MUTED, a * k * 0.8), width=3); d.line([(x + 42, y + 25), (x + 22, y + 45)], fill=A(MUTED, a * k * 0.8), width=3)
    ly = gy0 + rows * (chh + gap) + 12
    if t >= 89.70:
        b = appear(t, 89.70)
        d.line([(x0 + 26, ly + 12), (x0 + 46, ly + 32)], fill=A(MUTED, a * b), width=3); d.line([(x0 + 46, ly + 12), (x0 + 26, ly + 32)], fill=A(MUTED, a * b), width=3)
        txt(d, x0 + 60, ly + 8, 'LABS PULLED: 0', f(MONOB, 26), CREAM, a * b)
    if t >= 91.36: tag(d, x0 + 520, ly + 2, 'SOMETHING BREAKS', RED, 26, a * appear(t, 91.50))

# ---------------- S13: end card ----------------
LOGO = None
def sc_end(im, t, t0, t1):
    global LOGO
    if t < t0: return
    a = appear(t, t0, 0.22); y = 300
    frosted(im, (56, y, 1024, y + 232), 0.86 * a, 14); d = ImageDraw.Draw(LAYER, 'RGBA')
    brackets(d, 56, y, 1024, y + 232, A(VGOLD, a), 30, 5)
    if GL: brackets(GL, 56, y, 1024, y + 232, A(VGOLD, a), 30, 10)
    if LOGO is None:
        lg = Image.open(T + 'logo.jpg').convert('RGB'); s = min(lg.size)
        lg = lg.crop(((lg.width - s) // 2, (lg.height - s) // 2, (lg.width + s) // 2, (lg.height + s) // 2)).resize((176, 176), Image.LANCZOS)
        m = Image.new('L', (176, 176), 0); ImageDraw.Draw(m).ellipse([0, 0, 175, 175], fill=255); lg.putalpha(m); LOGO = lg
    lg = LOGO.copy(); lg.putalpha(lg.split()[3].point(lambda v: int(v * a))); im.alpha_composite(lg, (82, y + 28))
    kicker(d, 290, y + 30, 'BLOODWORK IS THE ROADMAP', VGOLD, a, clamp((t - t0) / 0.6), 24)
    if t >= t0 + 0.25:
        b = expo((t - t0 - 0.25) / 0.14); s = lerp(1.1, 1.0, b)
        fn = f(BEB, int(96 * s)); label = '@COACH.AGZ'; tw = d.textlength(label, font=fn)
        lit_bar(d, 290, y + 76, 290 + tw + 40, y + 76 + int(100 * s), VGOLD, a * b); d.text((310, y + 82), label, font=fn, fill=A(INK, a * b))
        if GL: GL.rectangle([286, y + 72, 294 + tw + 40, y + 80 + int(100 * s)], outline=A(VGOLD, a * b), width=12)
    txt(d, 290, y + 194, 'FOR RESEARCH & EDUCATIONAL PURPOSES ONLY', f(MONO, 18), MUTED, a)

# ---------------- scene table ----------------
# kind: panel = frosted evidence panel w/ header (footage pushed back); full = custom full scene (footage pushed back); card = floating, footage live
SCENES = [
    dict(t0=4.70, t1=8.52, kind='card', fn=sc_rewind),
    dict(t0=8.64, t1=15.00, kind='panel', fn=sc_heart, hdr=('REALITY 01 · YOUR HEART', 'LIVE MONITOR')),
    dict(t0=15.08, t1=25.38, kind='card', fn=sc_dial),
    dict(t0=25.52, t1=30.92, kind='card', fn=sc_weight),
    dict(t0=31.00, t1=40.62, kind='full', fn=sc_mirror),
    dict(t0=41.30, t1=47.96, kind='card', fn=sc_receipt),
    dict(t0=48.78, t1=55.96, kind='panel', fn=sc_life, hdr=('THE TRADE', 'LIFESPAN')),
    dict(t0=56.30, t1=63.46, kind='card', fn=sc_switch),
    dict(t0=64.44, t1=70.70, kind='card', fn=sc_check),
    dict(t0=70.80, t1=76.30, kind='panel', fn=sc_silent, hdr=('CONSTANT CRISIS', 'HIDDEN DAMAGE')),
    dict(t0=77.80, t1=86.58, kind='full', fn=sc_road),
    dict(t0=86.72, t1=92.80, kind='card', fn=sc_grid),
    dict(t0=93.00, t1=99.0, kind='card', fn=sc_end),
]
P = (64, 440, 1016, 1262)
STAMP = (54.16, 55.96)
SHAKES = [54.26]

# ---------------- text hook + topic band ----------------
HOOK_END = 4.40
def text_hook(im, t):
    if t >= HOOK_END + 0.15: return
    a = 1 - clamp((t - HOOK_END) / 0.15)
    s = lerp(1.0, 1.04, clamp(t / HOOK_END))
    lay = Image.new('RGBA', (W, 420), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    l1a, l1b = 'STEROIDS', ' at 22'; l2 = "the damage you can't see"
    size = 104
    while max(d.textlength(l1a + l1b, font=f(BAR, size)), d.textlength(l2, font=f(BAR, size))) > 900: size -= 2
    fn = f(BAR, size)
    w1 = d.textlength(l1a + l1b, font=fn); w2 = d.textlength(l2, font=fn)
    y1, y2 = 40, 40 + size * 1.02
    pad = 26
    d.rounded_rectangle([(W - max(w1, w2)) / 2 - pad, y1 - 10, (W + max(w1, w2)) / 2 + pad, y2 + size * 1.08 + 8], radius=22, fill=(4, 6, 12, 205))
    x = (W - w1) / 2; d.text((x, y1), l1a, font=fn, fill=VGOLD); d.text((x + d.textlength(l1a, font=fn), y1), l1b, font=fn, fill=WHITE)
    d.text(((W - w2) / 2, y2), l2, font=fn, fill=WHITE)
    lay = lay.resize((int(W * s), int(420 * s)), Image.BICUBIC)
    if a < 1: lay.putalpha(lay.split()[3].point(lambda v: int(v * a)))
    im.alpha_composite(lay, (int((W - lay.width) / 2), int(268 - (lay.height - 420) / 2)))
REAL = [(9.22, '01', 'HEART'), (34.36, '02', 'LABS'), (42.74, '03', 'YEARS')]
def topic_band(d, t):
    if t < HOOK_END or t >= MID + 0.15: return
    a = min(clamp((t - HOOK_END) / 0.15), 1 - clamp((t - MID) / 0.15))
    d.rectangle([8, 212, W, 352], fill=NAVY + (int(228 * a),))
    d.line([(64, 240), (104, 240)], fill=A(GOLD, a), width=4); txt(d, 116, 226, '@coach.agz', f(MONO, 26), GOLD, a)
    fn = f(BAR, 58); txt(d, 64, 262, 'STEROIDS', fn, VGOLD, a); x = 64 + d.textlength('STEROIDS', font=fn)
    txt(d, x, 262, ' at 22', fn, WHITE, a)
    # 3-realities tracker
    txt(d, 600, 228, '3 HARSH REALITIES', f(MONOB, 22), CREAM, a)
    for i, (tt, n, lab) in enumerate(REAL):
        x0 = 600 + i * 140; on = t >= tt; b = appear(t, tt, 0.15) if on else 0
        col = VGOLD if on else DIM
        d.rectangle([x0, 268, x0 + 128, 336], fill=A(col, a * (0.18 + 0.82 * b) if on else a * 0.25), outline=A(col, a), width=2)
        txt(d, x0 + 10, 270, n, f(BEB, 40), INK if on else MUTED, a); txt(d, x0 + 10, 308, lab, f(MONOB, 20), INK if on else MUTED, a)
        if on and GL: GL.rectangle([x0 - 2, 266, x0 + 130, 338], outline=A(VGOLD, a * b), width=8)

# ---------------- captions ----------------
FIX = {'fucking': 'F*CKING'}
def nearest_cut(t):
    for c in CUTS:
        if c > t + 0.01: return c
    return 1e9
def build_groups():
    G = []; cur = []
    for i, x in enumerate(WORDS):
        if cur:
            prev = WORDS[cur[-1]]
            if len(cur) >= 3 or x['s'] - prev['e'] > 0.28 or prev['w'][-1] in '.,?!' or x['s'] >= nearest_cut(prev['e']): G.append(cur); cur = []
        cur.append(i)
    if cur: G.append(cur)
    return G
GROUPS = build_groups()
def group_at(t):
    lo = None
    for g in GROUPS:
        if WORDS[g[0]]['s'] <= t + 1e-6: lo = g
        else: break
    if lo is None: return None
    end = WORDS[lo[-1]]['e'] + 0.6
    nxt = [g for g in GROUPS if WORDS[g[0]]['s'] > WORDS[lo[0]]['s']]
    if t > end and (not nxt or WORDS[nxt[0][0]]['s'] > t): return None
    return lo
CAP_Y = 1335
def captions(im, t):
    g = group_at(t)
    if not g: return
    d = ImageDraw.Draw(im, 'RGBA')
    ws = [FIX.get(WORDS[i]['w'].lower().strip('.,?!'), WORDS[i]['w']).upper().rstrip(',.?!') for i in g]
    size = 128
    while True:
        fn = f(BEB, size); sp = d.textlength(' ', font=fn) + 14; wd = [d.textlength(w, font=fn) for w in ws]; tot = sum(wd) + sp * (len(ws) - 1)
        if tot <= 920: break
        size -= 4
    xs = []; x = (W - tot) / 2
    for w_ in wd: xs.append(x); x += w_ + sp
    act = 0
    for k, i in enumerate(g):
        if WORDS[i]['s'] <= t: act = k
    g0 = WORDS[g[0]]['s']; s = lerp(0.9, 1, expo((t - g0) / 0.10))
    cap = Image.new('RGBA', (W, 300), (0, 0, 0, 0)); cd = ImageDraw.Draw(cap); shd = Image.new('RGBA', (W, 300), (0, 0, 0, 0)); sd = ImageDraw.Draw(shd)
    prev = max(0, act - 1); bt = expo((t - WORDS[g[act]]['s']) / 0.07) if act > 0 else 1
    bx0 = lerp(xs[prev], xs[act], bt) - 18; bx1 = lerp(xs[prev] + wd[prev], xs[act] + wd[act], bt) + 18
    for k, (w_, x_) in enumerate(zip(ws, xs)):
        if k != act: sd.text((x_ + 4, 46), w_, font=fn, fill=(0, 0, 0, 210))
    cap.alpha_composite(shd.filter(ImageFilter.GaussianBlur(6)))
    lit_bar(cd, bx0, 40 + size * 0.02, bx1, 40 + size * 0.98, RED)
    for k, (w_, x_) in enumerate(zip(ws, xs)): cd.text((x_, 40), w_, font=fn, fill=CREAM, stroke_width=0 if k == act else 3, stroke_fill=(0, 0, 0))
    if abs(s - 1) > 0.002:
        cap = cap.resize((int(W * s), int(300 * s)), Image.BICUBIC); ox = int((W - cap.width) / 2); oy = int(CAP_Y - 40 - (cap.height - 300) / 2)
    else: ox, oy = 0, CAP_Y - 40
    im.alpha_composite(cap, (ox, oy))

# ---------------- frame ----------------
def seg_of(t): return sum(1 for c in CUTS if c <= t + 1e-6)
def frame(src, t):
    global GL, SRC, LAYER
    z = 1.0 if seg_of(t) % 2 == 0 else 1.08
    if z != 1.0:
        big = src.resize((int(W * z), int(H * z)), Image.BICUBIC); ox = (big.width - W) // 2; oy = int((big.height - H) * 0.35); src = big.crop((ox, oy, ox + W, oy + H))
    SRC = src
    act = [sc for sc in SCENES if sc['t0'] <= t < sc['t1'] + 0.24]
    g = 0
    for sc in act:
        if sc['kind'] in ('panel', 'full'):
            g = max(g, min(ease_io((t - sc['t0'] + 0.05) / 0.30), 1 - ease_io((t - sc['t1']) / 0.22)))
    bg = src
    if g > 0: bg = Image.blend(src.filter(ImageFilter.GaussianBlur(18 * g)), Image.new('RGB', (W, H), (5, 8, 16)), 0.68 * g)
    im = bg.convert('RGBA')
    yy = np.arange(H); sa = np.where(yy > 1180, np.clip((yy - 1180) / 260, 0, 1) * 110, 0); sa = np.maximum(sa, np.where(yy < 420, (1 - yy / 420) * 120, 0)); sa = (sa * (1 - g)).astype(np.uint8)
    im.alpha_composite(Image.merge('RGBA', [Image.new('L', (W, H), c) for c in NAVY] + [Image.fromarray(np.repeat(sa[:, None], W, 1))]))
    glow = Image.new('RGBA', (W, H), (0, 0, 0, 0)); GL = ImageDraw.Draw(glow, 'RGBA')
    for sc in act:
        if sc['kind'] == 'panel':
            pin = expo((t - sc['t0']) / 0.20); pout = clamp((t - sc['t1']) / 0.16)
            if pout >= 1: continue
            s = lerp(1.05, 1.0, pin) * lerp(1.0, 1.03, pout); w = (P[2] - P[0]) * s; h = (P[3] - P[1]) * s; cx = (P[0] + P[2]) / 2; cy = (P[1] + P[3]) / 2
            x0, y0, x1, y1 = cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2
            frosted(im, (x0, y0, x1, y1), 0.92, 8)
            lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay, 'RGBA')
            sc['fn'](d, t)
            if pin < 1: lay = lay.filter(ImageFilter.GaussianBlur(8 * (1 - pin)))
            al = pin * (1 - pout); lay.putalpha(lay.split()[3].point(lambda v: int(v * al)))
            im.alpha_composite(lay); d = ImageDraw.Draw(im, 'RGBA')
            d.rectangle([x0, y0, x1, y1], outline=A(VGOLD, 0.8 * al), width=3); brackets(d, x0, y0, x1, y1, A(VGOLD, al), 48, 7)
            GL.rectangle([x0, y0, x1, y1], outline=A(VGOLD, 0.5 * al), width=6); brackets(GL, x0, y0, x1, y1, A(VGOLD, al), 48, 14)
            d.ellipse([x0 + 26, y0 + 26, x0 + 42, y0 + 42], fill=A(RED, al if int(t * 4) % 2 == 0 else al / 3))
            txt(d, x0 + 56, y0 + 18, sc['hdr'][0], f(MONOB, 28), WHITE, al); fr = f(MONO, 26); tw = d.textlength(sc['hdr'][1], font=fr); txt(d, x1 - 30 - tw, y0 + 20, sc['hdr'][1], fr, VGOLD, al)
        else:
            LAYER = Image.new('RGBA', (W, H), (0, 0, 0, 0))
            sc['fn'](im, t, sc['t0'], sc['t1'])
            im.alpha_composite(LAYER)
    stamp_false(im, t, *STAMP)
    bl = Image.new('RGBA', (W, H), (0, 0, 0, 0)); topic_band(ImageDraw.Draw(bl, 'RGBA'), t); im.alpha_composite(bl)
    text_hook(im, t)
    GL = None
    if glow.getbbox():
        sm = glow.resize((W // 4, H // 4), Image.BILINEAR)
        g1 = np.asarray(sm.filter(ImageFilter.GaussianBlur(3.5))).astype(np.float32) / 255; g2 = np.asarray(sm.filter(ImageFilter.GaussianBlur(10))).astype(np.float32) / 255
        prem = np.clip(g1[..., :3] * g1[..., 3:] * 2.3 + g2[..., :3] * g2[..., 3:] * 1.8, 0, 1)
        prem = np.asarray(Image.fromarray((prem * 255).astype(np.uint8)).resize((W, H), Image.BILINEAR)).astype(np.float32) / 255
        b = np.asarray(im.convert('RGB')).astype(np.float32) / 255
        im = Image.fromarray(((1 - (1 - b) * (1 - prem)) * 255).astype(np.uint8)).convert('RGBA')
    captions(im, t)
    d = ImageDraw.Draw(im, 'RGBA'); d.rectangle([0, 0, 7, H], fill=GOLD)
    out = im.convert('RGB')
    for t_s in SHAKES:
        k = round((t - t_s) * FPS)
        if k in (0, 1):
            dx = [9, -5][k]; z = 1.025; big = out.resize((int(W * z), int(H * z)), Image.BICUBIC); ox = (big.width - W) // 2 - dx; oy = (big.height - H) // 2
            out = big.crop((ox, oy, ox + W, oy + H)); ImageDraw.Draw(out).rectangle([0, 0, 7, H], fill=GOLD)
    return out

if __name__ == '__main__':
    mode = sys.argv[2]
    if mode == 'stills':
        import os; os.makedirs(S + '/qc', exist_ok=True)
        for tt in [float(x) for x in sys.argv[3:]]:
            n = round(tt * FPS)
            subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', T + 'assembled.mp4', '-vf', f'select=eq(n\\,{n})', '-vsync', '0', '-frames:v', '1', S + '/qc/_src.png'])
            frame(Image.open(S + '/qc/_src.png').convert('RGB'), n / FPS).resize((540, 960), Image.LANCZOS).save(S + f'/qc/st_{tt:06.2f}.jpg', quality=88)
        sys.exit()
    n0, n1, out = int(sys.argv[3]), int(sys.argv[4]), sys.argv[5]
    dec = subprocess.Popen(['ffmpeg', '-v', 'error', '-ss', f'{n0 / FPS:.4f}', '-i', T + 'assembled.mp4', '-frames:v', str(n1 - n0), '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], stdout=subprocess.PIPE)
    enc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-crf', '16', '-preset', 'medium', '-profile:v', 'high', '-pix_fmt', 'yuv420p', out], stdin=subprocess.PIPE)
    for n in range(n0, n1):
        buf = dec.stdout.read(W * H * 3)
        if len(buf) < W * H * 3: print('short', n); break
        enc.stdin.write(frame(Image.frombuffer('RGB', (W, H), buf), n / FPS).tobytes())
    enc.stdin.close(); enc.wait(); dec.kill(); print('done', n0, n1)
