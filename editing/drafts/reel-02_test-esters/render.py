# Reel 02 "Test esters" — 1080x1920 30fps render. usage: python3 render.py <workdir> [chunk_i n_chunks | qc t1 t2 ...]
import json, sys, math, subprocess, os
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

S = sys.argv[1]; B = S + '/build/'; F = S + '/fonts/'
LOGO = os.path.dirname(os.path.abspath(__file__)) + '/../../brand/logo/coach-agz-logo-round.jpg'
W, H, FPS = 1080, 1920, 30
TL = json.load(open(B + 'timeline.json')); KEEP = TL['keep']; BOUNDS = TL['bounds']; DUR = TL['dur']
N = int(round(DUR * FPS))
WORDS = json.load(open(B + 'words.json'))

def m(t):  # source time -> output time
    o = 0
    for a, b in KEEP:
        if t < a: return o
        if t <= b: return o + t - a
        o += b - a
    return o
c = m

# ---------------- palette / type ----------------
GOLD = (201, 169, 110); CREAM = (244, 241, 234); NAVY = (14, 17, 23); PANEL = (24, 26, 34)
RED = (255, 34, 28); VGOLD = (255, 194, 26); CYAN = (0, 229, 255); GREEN = (30, 255, 110)
AMBER = (240, 160, 48); DEEP = (2, 3, 8); INK = (6, 8, 14); WHITE = (255, 255, 255); MUTED = (184, 184, 188); DIM = (124, 124, 130)
BEB = 'BebasNeue.ttf'; DMB = 'DMSans-700.ttf'; DMR = 'DMSans-400.ttf'; MONO = 'JBMono-500.ttf'; MONOB = 'JBMono-800.ttf'; BAR = 'Barlow-600.ttf'; BARB = 'Barlow-800.ttf'
_fc = {}
def f(n, s):
    if n in (MONO, MONOB): s = s * 1.22  # phone legibility for small labels
    k = (n, int(s))
    if k not in _fc: _fc[k] = ImageFont.truetype(F + n, int(s))
    return _fc[k]
def clamp(x, a=0, b=1): return max(a, min(b, x))
def expo(x): x = clamp(x); return 1 if x >= 1 else 1 - 2 ** (-10 * x)
def ease_io(x): x = clamp(x); return 4 * x ** 3 if x < .5 else 1 - (-2 * x + 2) ** 3 / 2
def back(x):  # heavy landing: small settle, no bounce
    x = clamp(x); return 1 - (1 - x) ** 3
def lerp(a, b, t): return a + (b - a) * t
def A(col, a): return tuple(col[:3]) + (int(clamp(a) * 255),)
def ap(t, t0, d=0.16): return expo((t - t0) / d)

class Ctx:  # per-frame drawing context
    def __init__(s, im):
        s.im = im; s.ov = Image.new('RGBA', (W, H), (0, 0, 0, 0)); s.d = ImageDraw.Draw(s.ov, 'RGBA')
        s.gl = Image.new('RGBA', (W, H), (0, 0, 0, 0)); s.g = ImageDraw.Draw(s.gl, 'RGBA')
    def frost(s, box, r=26, dark=0.82, a=1.0, blur=14):
        x0, y0, x1, y1 = [int(v) for v in box]
        x0 = max(0, x0); y0 = max(0, y0); x1 = min(W, x1); y1 = min(H, y1)
        if x1 - x0 < 4 or y1 - y0 < 4 or a <= 0: return
        reg = s.im.crop((x0, y0, x1, y1)).filter(ImageFilter.GaussianBlur(blur))
        reg = Image.blend(reg, Image.new('RGBA', reg.size, DEEP + (255,)), dark)
        mk = Image.new('L', reg.size, 0); ImageDraw.Draw(mk).rounded_rectangle([0, 0, x1 - x0 - 1, y1 - y0 - 1], radius=r, fill=int(255 * a))
        s.im.paste(reg, (x0, y0), mk)

# ---------------- primitives ----------------
def txt(d, x, y, s, fn, col, a=1.0, anchor='la', **kw):
    d.text((x, y), s, font=fn, fill=A(col, a), anchor=anchor, **kw)
def tw(d, s, fn): return d.textlength(s, font=fn)
def lit_bar(d, x0, y0, x1, y1, col, a=1.0):
    h = max(1, int(y1 - y0))
    for i in range(h):
        k = i / h; cc = tuple(int(min(255, v * (1.18 - 0.36 * k) + (40 if k < 0.12 else 0))) for v in col)
        d.line([(x0, y0 + i), (x1, y0 + i)], fill=cc + (int(255 * a),))
def tag(C, x, y, label, col=RED, size=30, a=1.0, anchor='l'):
    d = C.d; fn = f(MONOB, size); w = tw(d, label, fn); h = size + 18
    if anchor == 'c': x -= (w + 28) / 2
    if anchor == 'r': x -= (w + 28)
    lit_bar(d, x, y, x + w + 28, y + h, col, a)
    txt(d, x + 14, y + 7, label, fn, INK if col in (VGOLD, GREEN, AMBER) else WHITE, a)
    C.g.rectangle([x - 3, y - 3, x + w + 31, y + h + 3], outline=A(col, a * 0.9), width=7)
    return x + w + 28
def brackets(d, x0, y0, x1, y1, col, L=30, w=5):
    for (cx, cy, sx, sy) in [(x0, y0, 1, 1), (x1, y0, -1, 1), (x0, y1, 1, -1), (x1, y1, -1, -1)]:
        d.line([(cx, cy), (cx + sx * L, cy)], fill=col, width=w); d.line([(cx, cy), (cx, cy + sy * L)], fill=col, width=w)
def kicker(C, x, y, label, t0, t, col=VGOLD, a=1.0, size=30, anchor='l'):
    p = ap(t, t0, 0.22)
    if p <= 0: return
    fn = f(BARB, size); wl = tw(C.d, label, fn) + len(label) * 5
    ox = x if anchor == 'l' else x - (wl + 74) / 2
    C.d.line([(ox, y + size * 0.55), (ox + 56 * p, y + size * 0.55)], fill=A(col, a), width=4)
    q = clamp((t - t0 - 0.08) / 0.25); n = int(len(label) * q)
    xx = ox + 74
    for ch in label[:n]:
        txt(C.d, xx, y, ch, fn, col, a); xx += tw(C.d, ch, fn) + 5
def panel(C, box, a=1.0, r=26, bar=True, barcol=RED, frost=True, border=None):
    x0, y0, x1, y1 = box
    if frost: C.frost(box, r=r, a=a)
    else: C.d.rounded_rectangle(box, radius=r, fill=A(DEEP, 0.92 * a))
    C.d.rounded_rectangle(box, radius=r, outline=A(border or (58, 54, 48), a), width=2)
    if bar:
        C.d.rounded_rectangle([x0, y0 + 18, x0 + 8, y1 - 18], radius=4, fill=A(barcol, a)); C.g.rectangle([x0 - 2, y0 + 18, x0 + 10, y1 - 18], fill=A(barcol, a * .8))
def check(d, x, y, col, s=1.0, a=1.0, w=7):
    d.line([(x - 16 * s, y), (x - 5 * s, y + 12 * s), (x + 18 * s, y - 14 * s)], fill=A(col, a), width=w, joint='curve')
def cross(d, x, y, col, s=1.0, a=1.0, w=7):
    d.line([(x - 13 * s, y - 13 * s), (x + 13 * s, y + 13 * s)], fill=A(col, a), width=w); d.line([(x - 13 * s, y + 13 * s), (x + 13 * s, y - 13 * s)], fill=A(col, a), width=w)
def arrow(d, x0, y0, x1, y1, col, w=5, a=1.0, hd=16):
    d.line([(x0, y0), (x1, y1)], fill=A(col, a), width=w); ang = math.atan2(y1 - y0, x1 - x0)
    d.polygon([(x1, y1), (x1 - hd * math.cos(ang - .45), y1 - hd * math.sin(ang - .45)), (x1 - hd * math.cos(ang + .45), y1 - hd * math.sin(ang + .45))], fill=A(col, a))
def poly_reveal(d, pts, q, col, w, a=1.0):
    if q <= 0 or len(pts) < 2: return None
    n = max(2, int(len(pts) * clamp(q))); P = pts[:n]
    d.line(P, fill=A(col, a), width=w, joint='curve'); return P[-1]
def watermark(C, x, y, a=1.0, anchor='rs'):
    txt(C.d, x, y, '@COACH.AGZ', f(MONO, 22), MUTED, a * 0.8, anchor=anchor)
def disclaimer(C, y=1488, a=1.0):
    txt(C.d, W / 2, y, 'FOR RESEARCH & EDUCATIONAL PURPOSES ONLY', f(MONO, 19), DIM, a, anchor='ms')

# ---------------- pharmacokinetics (illustrative, first-order) ----------------
def pk(hl, interval, t_axis, missed=(), ka_mult=5.0, warm=60):
    ke = math.log(2) / hl; ka = ke * ka_mult; C = np.zeros_like(t_axis)
    k = -int(warm / interval)
    while k * interval <= t_axis[-1]:
        ti = k * interval
        if not any(abs(ti - mm) < 1e-6 for mm in missed):
            dt = t_axis - ti; v = np.where(dt > 0, np.exp(-ke * np.clip(dt, 0, None)) - np.exp(-ka * np.clip(dt, 0, None)), 0)
            C += v * interval
        k += 1
    return C

# ---------------- footage layouts ----------------
# layout = (k, ox, oy, mask_box, mask_radius, border_alpha)
def L_full(t):
    seg = 0
    for i, (b0, b1) in enumerate(BOUNDS):
        if b0 <= t < b1 + 1e-6: seg = i
    s = 1.0 if seg % 2 == 0 else 1.08
    cx, cy = 520, 880
    return (s, cx - cx * s, cy - cy * s, (0, 0, W, H), 0, 0.0)
L_SPLIT = (0.62, 205 - 0 * 0.62, 400 - 330 * 0.62, (205, 400, 875, 1100), 30, 1.0)
L_CIRC = (0.56, 850 - 520 * 0.56, 610 - 860 * 0.56, (680, 440, 1020, 780), 170, 1.0)
L_SQ = (0.62, 250 - 520 * 0.62, 545 - 850 * 0.62, (60, 355, 440, 735), 36, 1.0)
L_RAIL = (1.0, 290, 0, (470, 0, W + 40, H), 40, 1.0)

def lay_lerp(a, b, p):
    return (lerp(a[0], b[0], p), lerp(a[1], b[1], p), lerp(a[2], b[2], p), tuple(lerp(x, y, p) for x, y in zip(a[3], b[3])), lerp(a[4], b[4], p), lerp(a[5], b[5], p))

BG = None
def make_bg():
    bg = Image.new('RGB', (W, H), NAVY); arr = np.asarray(bg).astype(np.float32)
    yy, xx = np.mgrid[0:H, 0:W]
    glow = np.exp(-(((xx - 980) / 700.0) ** 2 + ((yy - 200) / 800.0) ** 2))
    arr += glow[..., None] * np.array([18, 14, 8]); arr += np.exp(-(((xx - 100) / 600.0) ** 2 + ((yy - 1700) / 600.0) ** 2))[..., None] * np.array([10, 2, 4])
    rng = np.random.default_rng(3); arr += rng.normal(0, 2.2, (H, W, 1))
    im = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)); d = ImageDraw.Draw(im)
    for x in range(0, W, 60): d.line([(x, 0), (x, H)], fill=(20, 24, 32))
    for y in range(0, H, 60): d.line([(0, y), (W, y)], fill=(20, 24, 32))
    d.rectangle([0, 0, 5, H], fill=GOLD)  # signature gold rule
    return im.convert('RGBA')

def place_footage(src, lay, bgp):
    k, ox, oy, box, r, ba = lay
    if bgp <= 0.001 and abs(k - 1) < 1e-4 and abs(ox) < .5 and abs(oy) < .5: return src.convert('RGBA'), None
    canvas = BG.copy()  # window morphs over the brand background
    sw, sh = int(round(W * k)), int(round(H * k))
    fs = src.resize((sw, sh), Image.BILINEAR).convert('RGBA')
    lay_im = Image.new('RGBA', (W, H), (0, 0, 0, 0)); lay_im.paste(fs, (int(round(ox)), int(round(oy))))
    mk = Image.new('L', (W, H), 0); ImageDraw.Draw(mk).rounded_rectangle([int(v) for v in box], radius=int(r), fill=255)
    canvas.paste(lay_im, (0, 0), Image.fromarray(np.minimum(np.asarray(mk), np.asarray(lay_im.split()[3]))))
    return canvas, (box, r, ba)

# ---------------- scenes ----------------
def sc_hook(C, t):  # frame-0 text hook (premium mode, two lines)
    a = 1.0 if t < 3.4 else 1 - clamp((t - 3.4) / 0.15)
    if a <= 0: return
    d = C.d; f1 = f(BEB, 132); f2 = f(DMB, 58)
    l1 = ['CYP', ' vs ', 'ENAN', ' vs ', 'PROP']
    fn_vs = f(DMB, 60)
    widths = [tw(d, s, f1 if i % 2 == 0 else fn_vs) for i, s in enumerate(l1)]; w1 = sum(widths)
    w2 = tw(d, 'stop guessing your ester', f2)
    bw = max(w1, w2) + 90; x0 = (W - bw) / 2; y0 = 272; y1 = y0 + 262
    d.rounded_rectangle([x0, y0, x0 + bw, y1], radius=28, fill=A((4, 5, 10), 0.86 * a), outline=A(VGOLD, 0.85 * a), width=3)
    C.g.rounded_rectangle([x0, y0, x0 + bw, y1], radius=28, outline=A(VGOLD, 0.7 * a), width=8)
    d.rounded_rectangle([x0 + 14, y0 + 30, x0 + 22, y1 - 30], radius=4, fill=A(RED, a))
    x = (W - w1) / 2
    for i, s in enumerate(l1):
        if i % 2 == 0: txt(d, x, y0 + 24, s, f1, VGOLD, a)
        else: txt(d, x, y0 + 74, s, fn_vs, WHITE, a)
        x += widths[i]
    txt(d, W / 2, y0 + 186, 'stop guessing your ester', f2, WHITE, a, anchor='mt')
    sc = 1 + 0.03 * clamp(t / 3.4)  # one slow move over the hold
    return sc

def sc_band(C, t, t_in, t_out):
    a = min(clamp((t - t_in) / 0.15), clamp((t_out - t) / 0.15))
    if a <= 0: return
    d = C.d; fa = f(BEB, 66); fb = f(DMB, 40)
    wa = tw(d, 'TEST ESTERS', fa); wb = tw(d, 'how to pick', fb); bw = wa + wb + 90; x0 = (W - bw) / 2; y0 = 250
    d.rounded_rectangle([x0, y0, x0 + bw, y0 + 86], radius=18, fill=A((4, 5, 10), .82 * a))
    d.rectangle([x0, y0 + 14, x0 + 6, y0 + 72], fill=A(GOLD, a))
    txt(d, x0 + 30, y0 + 12, 'TEST ESTERS', fa, VGOLD, a); txt(d, x0 + 54 + wa, y0 + 25, 'how to pick', fb, WHITE, a)

def mini_curve(C, box, kind, q, col, a):
    x0, y0, x1, y1 = box; ta = np.linspace(0, 14, 120)
    hl, iv = {'CYP': (7, 3.5), 'ENAN': (4.5, 3.5), 'PROP': (1.2, 1.0)}[kind]
    v = pk(hl, iv, ta); v = (v - v.min() * 0.6) / (v.max() - v.min() * 0.6 + 1e-9)
    pts = [(lerp(x0, x1, i / 119), y1 - (y1 - y0) * vv) for i, vv in enumerate(v)]
    poly_reveal(C.d, pts, q, col, 4, a); poly_reveal(C.g, pts, q, col, 8, a * .8)

def sc_lineup(C, t, t_in, t_out):  # three vial chips with their curve shapes
    a = clamp((t_out - t) / 0.18)
    cues = [c(3.4), c(4.0), c(4.7)]; names = ['CYP', 'ENAN', 'PROP']; full = ['CYPIONATE', 'ENANTHATE', 'PROPIONATE']
    for i in range(3):
        p = back((t - cues[i]) / 0.22)
        if p <= 0: continue
        cx = 190 + i * 350; y = 400 + 60 * (1 - p); aa = a * clamp(p * 1.4)
        box = (cx - 160, y, cx + 160, y + 250); panel(C, box, aa, r=22, bar=False)
        brackets(C.d, box[0] + 10, box[1] + 10, box[2] - 10, box[3] - 10, A(VGOLD, aa), 22, 4)
        # vial schematic
        vx = box[0] + 44; vy = box[1] + 40
        C.d.rounded_rectangle([vx, vy + 22, vx + 46, vy + 150], radius=10, outline=A(CYAN, aa), width=3)
        C.d.rectangle([vx + 6, vy, vx + 40, vy + 22], fill=A(CYAN, aa * .9))
        C.d.rectangle([vx + 4, vy + 70, vx + 42, vy + 146], fill=A(CYAN, aa * .25))
        C.g.rounded_rectangle([vx, vy + 22, vx + 46, vy + 150], radius=10, outline=A(CYAN, aa), width=6)
        txt(C.d, vx + 70, vy - 4, names[i], f(BEB, 70), VGOLD, aa); txt(C.d, vx + 72, vy + 66, full[i], f(MONO, 21), MUTED, aa)
        q = clamp((t - c(6.7) - i * 0.12) / 0.9)
        mini_curve(C, (vx + 70, vy + 105, box[2] - 22, vy + 175), names[i], q, [VGOLD, AMBER, RED][i], aa)
    if t > c(6.7):
        tag(C, W / 2, 668, 'SAME HORMONE · 3 CURVES', VGOLD, 26, a * ap(t, c(7.6), 0.2), anchor='c')

def sc_cyp(C, t, t_in, t_out, a):  # SPLIT: footage window top, dossier below
    d = C.d
    kicker(C, 70, 1120, 'ESTER 01 · LONG', t_in + 0.15, t, VGOLD, a)
    p = back((t - t_in - 0.25) / 0.3)
    if p > 0: txt(d, 70 - 40 * (1 - p), 1160, 'TEST CYPIONATE', f(BEB, 104), CREAM, a * p)
    # stamp: most scripted
    ps = ap(t, c(11.9), 0.12)
    if ps > 0:
        s = lerp(1.5, 1, ps)
        fn = f(BEB, int(44 * s)); lab = '#1 SCRIPTED · US'; w = tw(d, lab, fn)
        cx, cy = 770, 1210
        d.rounded_rectangle([cx - w / 2 - 18, cy - 34 * s, cx + w / 2 + 18, cy + 34 * s], radius=10, outline=A(RED, a * ps), width=5)
        txt(d, cx, cy + 2, lab, fn, RED, a * ps, anchor='mm'); C.g.rounded_rectangle([cx - w / 2 - 18, cy - 34 * s, cx + w / 2 + 18, cy + 34 * s], radius=10, outline=A(RED, a * ps), width=10)
    # half-life range bar
    ph = ap(t, c(14.2), 0.2)
    if ph > 0:
        x0, x1, y = 70, 1010, 1300
        txt(d, x0, y + 52, 'HALF-LIFE', f(MONOB, 22), MUTED, a * ph); txt(d, 1010, y + 74, 'DAYS', f(MONO, 16), DIM, a * ph, anchor='ra')
        bx0, bx1 = 260, 1010; d.line([(bx0, y + 34), (bx1, y + 34)], fill=A((70, 74, 86), a * ph), width=3)
        for k in range(0, 11, 2):
            xx = lerp(bx0, bx1, k / 10); d.line([(xx, y + 26), (xx, y + 42)], fill=A(DIM, a * ph), width=2); txt(d, xx, y + 50, f'{k}', f(MONO, 18), DIM, a * ph, anchor='mt')
        q = expo((t - c(14.2) - 0.1) / 0.5); xa = lerp(bx0, bx1, .5); xb = lerp(xa, lerp(bx0, bx1, .8), q)
        lit_bar(d, xa, y + 18, xb, y + 50, VGOLD, a * ph); C.g.rectangle([xa, y + 18, xb, y + 50], fill=A(VGOLD, a * ph * .6))
        if q > .6: txt(d, xa - 14, y + 4, '5-8 DAYS', f(BEB, 56), VGOLD, a * clamp((q - .6) / .4), anchor='ra')
    # milligram composition bar
    pm = ap(t, c(16.4), 0.2)
    if pm > 0:
        y = 1400; x0, x1 = 70, 1010
        txt(d, x0, y, '100 MG CYPIONATE  =', f(MONOB, 24), MUTED, a * pm)
        q = expo((t - c(19.1)) / 0.5)
        bx = lerp(x0, x1, 0.70)
        lit_bar(d, x0, y + 38, lerp(x0, bx, expo((t - c(16.6)) / .45)), y + 92, VGOLD, a * pm)
        if q > 0:
            lit_bar(d, bx + 4, y + 38, lerp(bx + 4, x1, q), y + 92, RED, a * pm); C.g.rectangle([bx + 4, y + 38, lerp(bx + 4, x1, q), y + 92], outline=A(RED, a * pm), width=6)
        txt(d, x0 + 18, y + 46, '~70 MG TESTOSTERONE', f(BARB, 38), INK, a * pm)
        if q > .5: txt(d, (bx + x1) / 2, y + 65, '~30 MG ESTER', f(BARB, 32), WHITE, a * clamp((q - .5) * 2), anchor='mm')
        if t > c(21.0): tag(C, x1, y - 6, 'DEAD WEIGHT', RED, 24, a * ap(t, c(21.0)), anchor='r')

def chart_axes(C, box, a, xlabel_days, ylab='SERUM T'):
    x0, y0, x1, y1 = box; d = C.d
    d.line([(x0, y1), (x1, y1)], fill=A((90, 94, 106), a), width=3); d.line([(x0, y0), (x0, y1)], fill=A((90, 94, 106), a), width=3)
    for k, lab in xlabel_days:
        xx = lerp(x0, x1, k); d.line([(xx, y1), (xx, y1 + 10)], fill=A(DIM, a), width=2); txt(d, xx, y1 + 16, lab, f(MONO, 19), DIM, a, anchor='mt')
    txt(d, x0 + 10, y0 - 34, ylab, f(MONOB, 22), MUTED, a)

def sc_flex(C, t, t_in, t_out, a):  # TAKEOVER line chart + circular face cam
    d = C.d
    kicker(C, 70, 470, 'SERUM LEVEL · CYPIONATE', t_in + .1, t, VGOLD, a, 28)
    p = back((t - t_in - .2) / .3)
    if p > 0:
        txt(d, 70, 520, 'PIN FREQUENCY', f(BEB, 92), CREAM, a * p); txt(d, 70, 612, 'vs how flat it stays', f(DMR, 38), MUTED, a * p)
    box = (110, 830, 1010, 1240); pa = ap(t, c(24.2), .3)
    if pa <= 0: return
    ta = np.linspace(0, 14, 260)
    curves = [('2X / WEEK', 3.5, AMBER, c(27.7)), ('3X / WEEK', 7 / 3, VGOLD, c(28.7)), ('DAILY', 1.0, GREEN, c(31.2))]
    allv = [pk(7, iv, ta, ka_mult=14) for _, iv, _, _ in curves]; lo = min(v.min() for v in allv) * .85; hi = max(v.max() for v in allv) * 1.05
    x0, y0, x1, y1 = box
    # stable zone band
    pz = ap(t, c(31.6), .3)
    if pz > 0:
        mean = allv[2].mean(); yz0 = y1 - (y1 - y0) * ((mean * 1.04 - lo) / (hi - lo)); yz1 = y1 - (y1 - y0) * ((mean * 0.96 - lo) / (hi - lo))
        d.rectangle([x0 + 2, yz0 - 14, x1, yz1 + 14], fill=A(GREEN, .10 * a * pz)); d.line([(x0, yz0 - 14), (x1, yz0 - 14)], fill=A(GREEN, .5 * a * pz), width=2); d.line([(x0, yz1 + 14), (x1, yz1 + 14)], fill=A(GREEN, .5 * a * pz), width=2)
        txt(d, x1 - 8, yz0 - 22, 'STABLE ZONE', f(MONOB, 22), GREEN, a * pz, anchor='rs')
    chart_axes(C, box, a * pa, [(i / 14, f'{i}') for i in range(0, 15, 2)]); txt(C.d, box[2], box[3] + 44, 'DAYS', f(MONO, 18), DIM, a * pa, anchor='ra')
    for i, ((lab, iv, col, tc), v) in enumerate(zip(curves, allv)):
        q = clamp((t - tc) / 0.9)
        if q <= 0: continue
        dim = 0.45 if (t > c(31.2) and i < 2) else 1.0
        pts = [(lerp(x0, x1, j / 259), y1 - (y1 - y0) * ((vv - lo) / (hi - lo))) for j, vv in enumerate(v)]
        poly_reveal(d, pts, q, col, 5, a * dim); poly_reveal(C.g, pts, q, col, 10, a * dim * .8)
        lx = 110 + i * 300; ly = 1300
        d.rectangle([lx, ly + 12, lx + 40, ly + 20], fill=A(col, a * dim)); txt(d, lx + 52, ly, lab, f(MONOB, 26), col, a * dim)
    # forgiveness: missed pin on the 2x curve barely leaves range (long half-life)
    pf = ap(t, c(34.8), .2)
    if pf > 0:
        tag(C, W / 2, 1360, 'LONG TAIL = FORGIVES A LATE PIN', GREEN, 26, a * pf, anchor='c')

def sc_enan(C, t, t_in, t_out, a):  # SIDE RAIL: footage pushed right, vertical evidence column left
    d = C.d; X0, X1 = 40, 450
    kicker(C, X0 + 10, 410, 'ESTER 02 · MID', t_in + .1, t, VGOLD, a, 26)
    p = back((t - t_in - .2) / .3)
    if p > 0: txt(d, X0 + 10, 450, 'ENANTHATE', f(BEB, 100), CREAM, a * p)
    # phase 1: vertical half-life ruler
    r_out = c(41.3)
    a1 = a * (1 - ap(t, r_out, .2))
    if a1 > 0 and t > t_in + .3:
        y0, y1 = 600, 1260; d.line([(X0 + 70, y0), (X0 + 70, y1)], fill=A((90, 94, 106), a1), width=3)
        for k in range(0, 11, 2):
            yy = lerp(y1, y0, k / 10); d.line([(X0 + 60, yy), (X0 + 80, yy)], fill=A(DIM, a1), width=2); txt(d, X0 + 52, yy, f'{k}', f(MONO, 22), DIM, a1, anchor='rm')
        txt(d, X0 + 10, y0 - 62, 'HALF-LIFE · DAYS', f(MONOB, 20), MUTED, a1)
        # CYP ghost
        ya, yb = lerp(y1, y0, .5), lerp(y1, y0, .8)
        d.rectangle([X0 + 100, yb, X0 + 220, ya], fill=A(GOLD, a1 * .28), outline=A(GOLD, a1 * .6), width=2); txt(d, X0 + 160, yb - 10, 'CYP', f(BEB, 52), GOLD, a1 * .8, anchor='ms')
        q = expo((t - c(40.0)) / .45)
        if q > 0:
            ya, yb = lerp(y1, y0, .4), lerp(y1, y0, .5); yy = lerp(ya, yb, q)
            lit_bar(d, X0 + 250, yy, X0 + 360, ya, VGOLD, a1); C.g.rectangle([X0 + 250, yy, X0 + 360, ya], outline=A(VGOLD, a1), width=6)
            txt(d, X0 + 305, yy - 10, 'ENAN', f(BEB, 52), VGOLD, a1, anchor='ms')
            if q > .7:
                tag(C, X0 + 250, ya + 20, '4-5 DAYS', VGOLD, 28, a1 * ap(t, c(40.3)))
                d.line([(X0 + 230, lerp(y1, y0, .5)), (X0 + 380, lerp(y1, y0, .5))], fill=A(WHITE, a1 * .5), width=2)
    # phase 2: research document scan
    a2 = a * ap(t, r_out, .25) * (1 - ap(t, c(49.1), .2))
    if a2 > 0:
        sl = 1 - ap(t, r_out, .3); bx = (X0 - 30 * sl, 610, X1, 1250)
        d.rounded_rectangle(bx, radius=10, fill=A((206, 204, 198), a2 * .96))
        d.rectangle([bx[0], bx[1], bx[2], bx[1] + 62], fill=A((210, 10, 20), a2)); txt(d, bx[0] + 20, bx[1] + 14, 'CLINICAL RESEARCH', f(MONOB, 26), WHITE, a2)
        txt(d, bx[0] + 20, bx[1] + 80, 'RELEASED 2026', f(MONO, 20), (60, 60, 64), a2)
        rng = np.random.default_rng(11)
        for i in range(11):
            yy = bx[1] + 128 + i * 40; wl = rng.uniform(.55, .95) * (bx[2] - bx[0] - 40)
            if i == 4:
                ph = expo((t - c(43.8)) / .4)
                d.rectangle([bx[0] + 14, yy - 8, bx[0] + 14 + (bx[2] - bx[0] - 28) * ph, yy + 30], fill=A(VGOLD, a2 * .85))
                txt(d, bx[0] + 22, yy - 4, 'ENANTHATE > GYM GAINS ?', f(BARB, 30), (10, 10, 12), a2)
            else: d.rounded_rectangle([bx[0] + 20, yy, bx[0] + 20 + wl, yy + 16], radius=4, fill=A((150, 148, 144), a2))
        if t > c(43.8):
            pt = ap(t, c(44.6), .14)
            tag(C, bx[0] + 14, bx[3] + 18, 'SUGGESTS · EARLY DATA', AMBER, 24, a2 * pt)
    # phase 3: weekly pin dots
    a3 = a * ap(t, c(49.1), .2)
    if a3 > 0:
        days = 'MTWTFSS'; y = 700
        txt(d, X0 + 10, y - 60, 'PINS / WEEK', f(MONOB, 26), MUTED, a3)
        two = {0, 3}; three = {0, 2, 4}
        for i, ch in enumerate(days):
            yy = y + i * 82; cx = X0 + 60
            txt(d, cx - 30, yy, ch, f(BEB, 44), DIM, a3, anchor='mm')
            on = (t > c(52.7) and ap(t, c(52.7) + i * .07, .1) > .5) or (t > c(49.8) and i in three) or (t > c(49.4) and i in two and t < c(49.8))
            col = GREEN if t > c(52.7) else VGOLD
            d.ellipse([cx + 20, yy - 26, cx + 72, yy + 26], outline=A(col if on else (70, 74, 86), a3), width=4, fill=A(col, a3 * .9) if on else None)
            if on: C.g.ellipse([cx + 20, yy - 26, cx + 72, yy + 26], fill=A(col, a3 * .7))
            if on: d.line([(cx + 90, yy), (cx + 90 + 160 * ap(t, c(49.4), .3), yy)], fill=A(col, a3 * .4), width=3)
        lab = 'DAILY · SMOOTHEST' if t > c(52.7) else ('3X / WEEK' if t > c(49.8) else '2X / WEEK')
        tag(C, X0 + 10, y + 7 * 82 - 10, lab, GREEN if t > c(52.7) else VGOLD, 28, a3)

def sc_prop(C, t, t_in, t_out, a):  # TAKEOVER stats + square face cam
    d = C.d
    kicker(C, 480, 390, 'ESTER 03 · SHORT', t_in + .1, t, RED, a, 28)
    p = back((t - t_in - .2) / .3)
    if p > 0: txt(d, 480, 430, 'PROPIONATE', f(BEB, 112), CREAM, a * p); txt(d, 482, 552, 'the short ester', f(DMR, 38), MUTED, a * p)
    # 90% ring
    pr = ap(t, c(57.6), .2) * (1 - ap(t, c(61.1), .2))
    if pr > 0:
        cx, cy, R = 300, 1060, 200; q = expo((t - c(57.8)) / .7)
        d.ellipse([cx - R, cy - R, cx + R, cy + R], outline=A((60, 22, 26), a * pr), width=34)
        d.arc([cx - R, cy - R, cx + R, cy + R], -90, -90 + 360 * .9 * q, fill=A(RED, a * pr), width=34); C.g.arc([cx - R, cy - R, cx + R, cy + R], -90, -90 + 324 * q, fill=A(RED, a * pr), width=44)
        txt(d, cx, cy + 8, f'{int(round(90 * q))}%', f(BEB, 150), WHITE, a * pr, anchor='mm')
        txt(d, 560, 880, 'OF CASES', f(BEB, 90), RED, a * pr); txt(d, 560, 975, 'it makes no sense', f(DMB, 44), CREAM, a * pr)
        cross(d, 1000, 910, RED, 1.6, a * pr * ap(t, c(58.3), .12), 10)
        # big stat: user-supplied half-life
        ph = ap(t, c(59.1), .14)
        if ph > 0:
            txt(d, 560, 1110, 'HALF-LIFE', f(MONOB, 26), MUTED, a * pr * ph)
            txt(d, 560 - 30 * (1 - ph), 1150, '20-36 HRS', f(BEB, 150), VGOLD, a * pr * ph)
    # all three half-lives bar chart
    pb = ap(t, c(61.1), .2)
    if pb > 0:
        x0, x1 = 80, 1000; y = 870
        txt(d, x0, y - 80, 'HALF-LIFE · HOURS', f(MONOB, 26), MUTED, a * pb)
        rows = [('CYP', 120, 192, '5-8 DAYS', VGOLD), ('ENAN', 96, 120, '4-5 DAYS', AMBER), ('PROP', 20, 36, '20-36 HRS', RED)]
        sx = lambda h: lerp(x0 + 150, x1, h / 200)
        for k in range(0, 201, 50):
            xx = sx(k); d.line([(xx, y - 10), (xx, y + 3 * 190 - 40)], fill=A((40, 44, 54), a * pb), width=2); txt(d, xx, y - 16, f'{k}', f(MONO, 19), DIM, a * pb, anchor='ms')
        for i, (n, lo, hi, lab, col) in enumerate(rows):
            yy = y + i * 190; q = expo((t - c(61.2) - i * .18) / .45)
            if q <= 0: continue
            txt(d, x0, yy + 6, n, f(BEB, 72), col, a * pb)
            xa = sx(0); xl = sx(lo) * q + xa * (1 - q); xh = sx(hi) * q + xa * (1 - q)
            lit_bar(d, xa, yy + 10, xl, yy + 70, col, a * pb)
            d.rectangle([xl, yy + 10, xh, yy + 70], fill=A(col, a * pb * .35), outline=A(col, a * pb), width=3)
            C.g.rectangle([xa, yy + 10, xh, yy + 70], outline=A(col, a * pb * .8), width=6)
            txt(d, xh + 16 if i == 2 else xh - 12, yy + 82 if i < 2 else yy + 20, lab, f(BARB, 40), col if i == 2 else CREAM, a * pb * clamp(q * 2 - 1), anchor='la' if i == 2 else 'ra')
        if t > c(62.0):
            yy = y + 2 * 190; brackets(d, x0 - 24, yy - 14, sx(36) + 250, yy + 92, A(RED, a * pb), 24, 5)
            tag(C, x0 - 24, yy + 112, 'SHORTEST · BY A WIDE MARGIN', RED, 26, a * pb * ap(t, c(62.3)))
    disclaimer(C, 1488, a * .9)

def sc_trough(C, t, t_in, t_out, a):  # TOP HUD monitor over full footage
    d = C.d; box = (40, 262, 1040, 560)
    panel(C, box, a, r=22, bar=True, barcol=CYAN)
    txt(d, 76, 284, 'PROP · DAILY PINS', f(MONOB, 24), CYAN, a); txt(d, 1012, 284, 'SERUM T', f(MONOB, 24), MUTED, a, anchor='ra')
    x0, y0, x1, y1 = 76, 330, 1012, 530
    miss = 4.0; ta = np.linspace(0, 7, 300)
    missed_on = t > c(68.5)
    v = pk(28 / 24, 1.0, ta, missed=(miss,) if missed_on else ())
    ref = pk(28 / 24, 1.0, ta); lo, hi = ref.min() * .45, ref.max() * 1.08
    zone = lo + (ref.min() - lo) * 0.75
    yz = y1 - (y1 - y0) * ((zone - lo) / (hi - lo))
    pz = ap(t, c(69.6), .2)
    d.rectangle([x0, yz, x1, y1], fill=A(RED, .10 + .22 * pz * a)); d.line([(x0, yz), (x1, yz)], fill=A(RED, .6 * a), width=2, )
    txt(d, x1 - 8, y1 - 8, 'TROUGH', f(MONOB, 22), RED, a, anchor='rs')
    for k in range(8):
        xx = lerp(x0, x1, k / 7); d.line([(xx, y0), (xx, y1)], fill=A((30, 36, 48), a), width=1)
    q = clamp((t - t_in - .2) / 4.4)
    pts = [(lerp(x0, x1, j / 299), y1 - (y1 - y0) * ((vv - lo) / (hi - lo))) for j, vv in enumerate(v)]
    end = poly_reveal(d, pts, q, CYAN, 5, a); poly_reveal(C.g, pts, q, CYAN, 12, a)
    if end:  # scan head
        d.ellipse([end[0] - 9, end[1] - 9, end[0] + 9, end[1] + 9], fill=A(WHITE, a)); C.g.line([(end[0], y0), (end[0], y1)], fill=A(CYAN, a * .6), width=6)
    for k in range(7):
        xx = lerp(x0, x1, k / 7)
        if xx > (end[0] if end else 0): break
        if missed_on and abs(k - miss) < .01:
            cross(d, xx + 6, y0 - 4, RED, 1.0, a, 6)
        else: d.polygon([(xx, y0 - 16), (xx + 12, y0 - 16), (xx + 6, y0 - 2)], fill=A(VGOLD, a))
    if missed_on:
        xm = lerp(x0, x1, (miss + 1.0) / 7)
        if t > c(70.1): tag(C, min(xm + 20, 760), 576, 'MISSED 1 DAY', RED, 26, a * ap(t, c(70.1), .12))

def steroid(C, cx, cy, r, col, a, glow=1.0):
    d = C.d; s3 = math.sqrt(3)
    def hexpts(x, y): return [(x + r * math.cos(math.radians(60 * i + 30)), y + r * math.sin(math.radians(60 * i + 30))) for i in range(6)]
    A_ = (cx - s3 * r * 1.5, cy + r * .75); B_ = (A_[0] + s3 * r, A_[1]); C_ = (B_[0] + s3 * r / 2, A_[1] - 1.5 * r)
    rings = [hexpts(*A_), hexpts(*B_), hexpts(*C_)]
    # D ring: pentagon fused to C's right edge
    e0 = rings[2][5]; e1 = rings[2][0]
    mx, my = (e0[0] + e1[0]) / 2, (e0[1] + e1[1]) / 2; ang = math.atan2(e1[1] - e0[1], e1[0] - e0[0]) - math.pi / 2
    dc = (mx - math.cos(ang) * r * .69, my - math.sin(ang) * r * .69)
    base = math.atan2(e0[1] - dc[1], e0[0] - dc[0])
    rp = math.hypot(e0[0] - dc[0], e0[1] - dc[1])
    pent = [(dc[0] + rp * math.cos(base + i * 2 * math.pi / 5), dc[1] + rp * math.sin(base + i * 2 * math.pi / 5)) for i in range(5)]
    for P in rings + [pent]:
        d.line(P + [P[0]], fill=A(col, a), width=5, joint='curve'); C.g.line(P + [P[0]], fill=A(col, a * glow), width=10)
    # ketone on A ring, 17-O on D ring
    k0 = rings[0][2]; d.line([k0, (k0[0] - 34, k0[1] + 20)], fill=A(col, a), width=5); txt(d, k0[0] - 40, k0[1] + 24, 'O', f(BARB, 34), col, a, anchor='rm')
    o17 = max(pent, key=lambda p: p[0])
    return o17

def sc_mol(C, t, t_in, t_out, a):  # GLASS CARD lower: X-ray molecule, ester tail detaches
    d = C.d; box = (40, 1150, 1040, 1510)
    pin = back((t - t_in) / .3); dy = 50 * (1 - pin)
    box = (box[0], box[1] + dy, box[2], box[3] + dy)
    panel(C, box, a, r=26, bar=True, barcol=CYAN)
    kicker(C, 76, box[1] + 22, 'X-RAY · TESTOSTERONE ESTER', t_in + .1, t, CYAN, a, 24)
    p2 = ap(t, c(77.0), .25)  # handoff to table
    am = a * (1 - p2)
    if am > 0:
        o17 = steroid(C, 380, box[1] + 230, 52, CYAN if t < c(75.6) else GREEN, am, 1.0)
        names = [('CYPIONATE', 7), ('ENANTHATE', 6), ('PROPIONATE', 2)]
        cyc = int(max(0, t - c(72.8)) / 0.42) % 3 if t < c(74.1) else 0
        nm, L = names[cyc]
        pc = ap(t, c(74.1), .12); drift = 300 * expo((t - c(74.3)) / .8)
        ta = am * (1 - expo((t - c(74.3)) / .9)) if t > c(74.1) else am
        x, y = o17[0] + 12, o17[1]
        d.line([(o17[0] + 2, y), (x + 22, y)], fill=A(CYAN, am), width=5); txt(d, x + 24, y, 'O', f(BARB, 34), CYAN, am, anchor='lm')
        xs = x + 52 + drift; pts = [(xs, y)]
        for i in range(L + 1): pts.append((xs + 30 * (i + 1), y + (-24 if i % 2 == 0 else 0)))
        if ta > 0:
            col = VGOLD
            d.line(pts, fill=A(col, ta), width=5, joint='curve'); C.g.line(pts, fill=A(col, ta), width=10)
            pc0 = pts[1]; d.line([pc0, (pc0[0], pc0[1] - 38)], fill=A(col, ta), width=5); txt(d, pc0[0], pc0[1] - 42, 'O', f(BARB, 30), col, ta, anchor='ms')
            txt(d, pts[-1][0] + 14, y - 4, nm, f(MONOB, 24), col, ta, anchor='lm')
        if pc > 0 and t < c(75.3):
            cxx = x + 44; d.line([(cxx - 10, y - 46), (cxx + 10, y + 46)], fill=A(RED, am * pc), width=6); C.g.line([(cxx - 10, y - 46), (cxx + 10, y + 46)], fill=A(RED, am * pc), width=12)
        if t > c(74.6): tag(C, 760, box[1] + 120, 'ESTER = CARRIER', VGOLD, 24, am * ap(t, c(74.6)))
        if t > c(75.6): tag(C, 760, box[1] + 190, 'SAME MOLECULE', GREEN, 24, am * ap(t, c(75.6)))
    if p2 > 0:  # table: what the ester actually changes
        a2 = a * p2; y = box[1] + 80
        cols = [(76, 'ESTER'), (330, 'PINS / WEEK'), (700, 'MISSED PIN')]
        for x, h in cols: txt(d, x, y, h, f(MONOB, 22), MUTED, a2)
        rows = [('CYP', '2-3X · DAILY BEST', 'FORGIVING', GREEN), ('ENAN', '2-3X · DAILY BEST', 'FORGIVING', GREEN), ('PROP', 'DAILY · NO SKIPS', 'TROUGH', RED)]
        for i, (n, pw, ms, mc) in enumerate(rows):
            yy = y + 50 + i * 82; q = ap(t, c(77.1) + .25 * i, .15)
            if q <= 0: continue
            d.line([(76, yy - 10), (1004, yy - 10)], fill=A((58, 54, 48), a2 * q), width=2)
            txt(d, 76, yy, n, f(BEB, 60), VGOLD, a2 * q); txt(d, 330, yy + 12, pw, f(BARB, 38), CREAM, a2 * q)
            tag(C, 700, yy + 6, ms, mc, 24, a2 * ap(t, c(78.1) + .3 * i, .12))

def sc_pick(C, t, t_in, t_out, a):  # SELECTOR: three schedule cards, cursor, verdict bar
    d = C.d; names = [('CYP', '2-3X / WK'), ('ENAN', '2-3X / WK'), ('PROP', 'DAILY')]
    pos = clamp((t - c(80.9)) / 1.8) * 2; sel = int(round(pos))
    locked = t > c(83.0)
    for i, (n, s) in enumerate(names):
        p = back((t - t_in - i * .08) / .26)
        if p <= 0: continue
        x0 = 60 + i * 330; y0 = 1210 + 40 * (1 - p); bx = (x0, y0, x0 + 300, y0 + 200)
        hot = (abs(pos - i) < .5) or locked
        panel(C, bx, a * p, r=22, bar=False, border=VGOLD if hot else None)
        txt(d, x0 + 150, y0 + 40, n, f(BEB, 84), VGOLD if hot else DIM, a * p, anchor='mt')
        txt(d, x0 + 150, y0 + 130, s, f(MONOB, 26), CREAM if hot else DIM, a * p, anchor='mt')
    cx = 60 + pos * 330
    if not locked:
        brackets(d, cx - 10, 1200, cx + 310, 1420, A(VGOLD, a), 34, 6); brackets(C.g, cx - 10, 1200, cx + 310, 1420, A(VGOLD, a), 34, 10)
    else:
        pl = back((t - c(83.0)) / .2); y = 1425 + 30 * (1 - pl)
        lit_bar(d, 60, y, 1020, y + 84, VGOLD, a * pl); C.g.rectangle([60, y, 1020, y + 84], outline=A(VGOLD, a * pl), width=10)
        txt(d, 540, y + 42, 'THE ONE YOU WILL ACTUALLY KEEP', f(BEB, 62), INK, a * pl, anchor='mm')

def sc_streak(C, t, t_in, t_out, a):  # TOP HUD: 30-day pin log filling
    d = C.d; box = (40, 262, 1040, 540); panel(C, box, a, r=22, bar=True, barcol=GREEN)
    q = clamp((t - c(84.6)) / (c(87.9) - c(84.6))); n = int(30 * q)
    txt(d, 76, 284, 'PIN LOG', f(MONOB, 24), GREEN, a)
    txt(d, 1012, 280, f'DAY {max(1, n):02d} / 30', f(MONOB, 26), CREAM, a, anchor='ra')
    for i in range(30):
        r_, k = divmod(i, 15); x = 76 + k * 62; y = 340 + r_ * 86
        on = i < n
        d.rounded_rectangle([x, y, x + 50, y + 66], radius=8, fill=A(GREEN, a * .9) if on else A((24, 28, 36), a), outline=A((60, 64, 76), a), width=2)
        if on: C.g.rounded_rectangle([x, y, x + 50, y + 66], radius=8, fill=A(GREEN, a * .5)); check(d, x + 25, y + 33, INK, .8, a, 5)
    if t > c(87.1): tag(C, 540, 556, 'EVERY SINGLE TIME', GREEN, 26, a * ap(t, c(87.1)), anchor='c')

_logo = None
def sc_cta(C, t, t_in, t_out, a):  # END CARD lower: poll chips + comment keyword
    global _logo
    d = C.d; p = back((t - t_in) / .3); box = (40, 1100 + 40 * (1 - p), 1040, 1500)
    panel(C, box, a * p, r=28, bar=True, barcol=RED)
    if _logo is None:
        lg = Image.open(LOGO).convert('RGBA').resize((120, 120), Image.LANCZOS); mk = Image.new('L', (120, 120), 0); ImageDraw.Draw(mk).ellipse([0, 0, 119, 119], fill=255); lg.putalpha(mk); _logo = lg
    y0 = box[1]
    lg = _logo.copy(); lg.putalpha(Image.fromarray((np.asarray(lg.split()[3]) * (a * p)).astype(np.uint8))); C.ov.alpha_composite(lg, (76, int(y0 + 28)))
    txt(d, 216, y0 + 40, 'COACH AGZ', f(BEB, 54), GOLD, a * p); txt(d, 218, y0 + 98, '@coach.agz', f(MONO, 24), MUTED, a * p)
    txt(d, 1004, y0 + 52, 'WHICH ONE DO YOU RUN', f(MONOB, 22), MUTED, a * p, anchor='ra')
    for i, n in enumerate(['CYP', 'ENAN', 'PROP']):
        q = back((t - c(89.5) - i * .12) / .2)
        if q <= 0: continue
        x = 76 + i * 190; y = y0 + 168
        d.rounded_rectangle([x, y + 10 * (1 - q), x + 170, y + 70 + 10 * (1 - q)], radius=12, fill=A((40, 12, 18), a * q), outline=A(RED, a * q), width=3)
        txt(d, x + 85, y + 36 + 10 * (1 - q), n, f(BEB, 52), (255, 170, 170), a * q, anchor='mm')
    txt(d, 680, y0 + 190, 'comment yours', f(DMB, 36), CREAM, a * ap(t, c(89.9)))
    pl = back((t - c(91.1)) / .22)
    if pl > 0:
        y = y0 + 268; xs = lerp(1040, 76, pl)
        lit_bar(d, xs, y, xs + 928, y + 92, VGOLD, a); C.g.rectangle([xs, y, xs + 928, y + 92], outline=A(VGOLD, a), width=10)
        txt(d, xs + 464, y + 46, 'COMMENT "LABS"', f(BEB, 76), INK, a * ap(t, c(91.25), .12), anchor='mm')
    disclaimer(C, box[3] + 30 if box[3] + 30 < 1530 else 1528, a * p)

# scene table: (fn, src_in, src_out, layout, caption_y)
SC = [
    (sc_cyp, 9.45, 21.9, L_SPLIT, 965),
    (sc_flex, 22.0, 37.35, L_CIRC, 1420),
    (sc_enan, 37.78, 53.85, L_RAIL, 1335),
    (sc_prop, 54.2, 63.45, L_SQ, 1500),
    (sc_trough, 63.5, 71.0, None, 1335),
    (sc_mol, 71.15, 80.5, None, 262),
    (sc_pick, 80.6, 84.2, None, 262),
    (sc_streak, 84.25, 88.5, None, 1335),
    (sc_cta, 88.7, 999, None, 262),
]
SCN = [(fn, c(a), c(b) if b < 900 else DUR + 1, lay, cy) for fn, a, b, lay, cy in SC]
for _i in range(len(SCN) - 1):  # close short gaps so layouts hand off directly (no snap to full frame)
    if SCN[_i + 1][1] - SCN[_i][2] < 0.5: SCN[_i] = SCN[_i][:2] + (SCN[_i + 1][1],) + SCN[_i][3:]
MID = DUR / 2
BAND_OUT = min([b0 for b0, b1 in BOUNDS if abs(b0 - MID) < 1.2] or [MID], key=lambda x: abs(x - MID))

def scene_at(t):
    for i, s in enumerate(SCN):
        if s[1] <= t < s[2]: return i
    return None

def layout_at(t):
    i = scene_at(t); full = L_full(t)
    if i is None: return full, 0.0
    fn, t0, t1, lay, cy = SCN[i]
    target = lay if lay else full
    prev = SCN[i - 1] if i > 0 else None
    src = (prev[3] if (prev and prev[3] and t0 - prev[2] < 0.5) else full)
    D = 0.38
    p = ease_io((t - t0) / D)
    cur = lay_lerp(src, target, p)
    nxt = SCN[i + 1] if i + 1 < len(SCN) else None
    if lay and not (nxt and nxt[1] - t1 < 0.5):  # return to full frame
        q = ease_io((t1 - t) / D); cur = lay_lerp(full, cur, q); bgp = q
    else: bgp = 1.0
    from_lay = bool(prev and prev[3] and t0 - prev[2] < 0.5)
    if not lay: bgp = (1 - p) if from_lay else 0.0
    else:
        src_bg = 1.0 if from_lay else 0.0
        bgp = min(bgp, lerp(src_bg, 1.0, p))
    return cur, bgp

# ---------------- captions (saved style: Bebas, red lit box on the spoken word) ----------------
FIX = {'cipionate': 'cypionate', '-cypionate': 'cypionate', 'inante': 'enanthate', 'cell': 'test', 'serum\'s': 'serum'}
ACC = {'cypionate': VGOLD, 'enanthate': VGOLD, 'propionate': VGOLD, '90%': RED, 'trough': RED, 'miss': RED, 'consistency': GREEN, 'labs': VGOLD}
def build_groups():
    G = []; cur = []
    for i, x in enumerate(WORDS):
        if cur:
            prev = WORDS[cur[-1]]
            if len(cur) >= 3 or x['s'] - prev['e'] > 0.28 or prev['w'][-1] in '.,?!' or any(prev['e'] <= b0 + 1e-3 <= x['s'] for b0, _ in BOUNDS) or any(prev['s'] < s[1] <= x['s'] for s in SCN):
                G.append(cur); cur = []
        cur.append(i)
    if cur: G.append(cur)
    return G
GROUPS = build_groups()
def wtext(i):
    w = WORDS[i]['w']; k = w.lower().strip('.,?!')
    out = FIX.get(k, k.lstrip('-')).upper()
    if k == '90': out = '90%'
    if k == '%': return None
    return out
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
def cap_y(t):
    i = scene_at(t)
    return SCN[i][4] if i is not None else 1335
def captions(im, t):
    g = group_at(t)
    if not g: return
    idx = [i for i in g if wtext(i)]
    if not idx: return
    d = ImageDraw.Draw(im, 'RGBA'); ws = [wtext(i) for i in idx]
    size = 120
    while True:
        fn = f(BEB, size); sp = d.textlength(' ', font=fn) + 14; wd = [d.textlength(w, font=fn) for w in ws]; tot = sum(wd) + sp * (len(ws) - 1)
        if tot <= 900: break
        size -= 4
    xs = []; x = (W - tot) / 2
    for w_ in wd: xs.append(x); x += w_ + sp
    act = 0
    for k, i in enumerate(idx):
        if WORDS[i]['s'] <= t: act = k
    g0 = WORDS[idx[0]]['s']; s = lerp(0.9, 1, expo((t - g0) / 0.10))
    CY = cap_y(t)
    cap = Image.new('RGBA', (W, 300), (0, 0, 0, 0)); cd = ImageDraw.Draw(cap); shd = Image.new('RGBA', (W, 300), (0, 0, 0, 0)); sd = ImageDraw.Draw(shd)
    prev = max(0, act - 1); bt = expo((t - WORDS[idx[act]]['s']) / 0.07) if act > 0 else 1
    bx0 = lerp(xs[prev], xs[act], bt) - 18; bx1 = lerp(xs[prev] + wd[prev], xs[act] + wd[act], bt) + 18
    for k, (w_, x_) in enumerate(zip(ws, xs)): sd.text((x_ + 4, 46), w_, font=fn, fill=(0, 0, 0, 220))
    cap.alpha_composite(shd.filter(ImageFilter.GaussianBlur(6)))
    lit_bar(cd, bx0, 40 + size * 0.02, bx1, 40 + size * 0.98, RED)
    for k, (w_, x_) in enumerate(zip(ws, xs)):
        col = CREAM
        if k != act and ws[k].lower() in ACC and WORDS[idx[k]]['s'] <= t: col = ACC[ws[k].lower()]
        cd.text((x_, 40), w_, font=fn, fill=col, stroke_width=0 if k == act else 3, stroke_fill=(0, 0, 0))
    if abs(s - 1) > 0.002:
        cap = cap.resize((int(W * s), int(300 * s)), Image.BICUBIC); ox = int((W - cap.width) / 2); oy = int(CY - 40 - (cap.height - 300) / 2)
    else: ox, oy = 0, CY - 40
    im.alpha_composite(cap, (ox, oy))

# ---------------- frame ----------------
def bloom(img, gl):
    sm = gl.resize((W // 4, H // 4), Image.BILINEAR)
    g1 = np.asarray(sm.filter(ImageFilter.GaussianBlur(4))).astype(np.float32) / 255; g2 = np.asarray(sm.filter(ImageFilter.GaussianBlur(12))).astype(np.float32) / 255
    g = (g1 * 1.6 + g2 * 1.4); rgb = g[..., :3] * g[..., 3:4]
    rgb = np.asarray(Image.fromarray(np.clip(rgb * 255, 0, 255).astype(np.uint8)).resize((W, H), Image.BILINEAR)).astype(np.float32) / 255
    base = np.asarray(img.convert('RGB')).astype(np.float32) / 255
    out = 1 - (1 - base) * (1 - np.clip(rgb * 0.75, 0, 1))
    return Image.fromarray((out * 255).astype(np.uint8))

def frame(src, t):
    lay, bgp = layout_at(t)
    im, win = place_footage(src, lay, bgp)
    C = Ctx(im)
    if win and win[2] > 0.01:
        box, r, ba = win
        C.d.rounded_rectangle([int(v) for v in box], radius=int(r), outline=A(VGOLD, ba * bgp), width=4)
        C.g.rounded_rectangle([int(v) for v in box], radius=int(r), outline=A(VGOLD, ba * bgp * .7), width=8)
    if t < 3.6: sc_hook(C, t)
    if 3.4 <= t < BAND_OUT: sc_band(C, t, 3.4, BAND_OUT)
    if t < c(9.4): sc_lineup(C, t, 3.4, c(9.4))
    i = scene_at(t)
    if i is not None:
        fn, t0, t1, l_, cy = SCN[i]
        a = min(clamp((t - t0) / 0.2), clamp((t1 - t) / 0.15))
        fn(C, t, t0, t1, a)
    C.im.alpha_composite(C.ov)
    out = bloom(C.im, C.gl).convert('RGBA')
    captions(out, t)
    return out.convert('RGB')

def decode(n0, n1):
    return subprocess.Popen(['ffmpeg', '-v', 'error', '-ss', f'{n0 / FPS:.4f}', '-i', B + 'assembled.mov', '-frames:v', str(n1 - n0), '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], stdout=subprocess.PIPE)

if __name__ == '__main__':
    BG = make_bg()
    if sys.argv[2] in ('qc', 'qcs'):
        os.makedirs(B + 'qc', exist_ok=True)
        for tt in sys.argv[3:]:
            tt = float(tt)
            if sys.argv[2] == 'qcs': tt = c(tt)
            n0 = int(tt * FPS); p = decode(n0, n0 + 1); raw = p.stdout.read(W * H * 3); p.wait()
            frame(Image.frombytes('RGB', (W, H), raw), n0 / FPS).save(B + f'qc/{tt:06.2f}.jpg', quality=88)
        sys.exit()
    ci, nc = int(sys.argv[2]), int(sys.argv[3]); per = math.ceil(N / nc); n0 = ci * per; n1 = min(N, n0 + per)
    dec = decode(n0, n1)
    enc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-crf', '12', '-preset', 'veryfast', '-pix_fmt', 'yuv420p', B + f'chunk{ci:02d}.mp4'], stdin=subprocess.PIPE)
    for n in range(n0, n1):
        raw = dec.stdout.read(W * H * 3)
        if len(raw) < W * H * 3: break
        enc.stdin.write(frame(Image.frombytes('RGB', (W, H), raw), n / FPS).tobytes())
        if (n - n0) % 150 == 0: print(ci, n, flush=True)
    enc.stdin.close(); enc.wait(); dec.wait()
