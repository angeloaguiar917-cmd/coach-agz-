# @coach.agz — "3 steps to reverse gyno" full edit renderer (1080x1920, 30 fps)
# usage: render.py <workdir> <fontdir> stills t1 t2 ... | render.py <workdir> <fontdir> <n0> <n1> <out.mp4>
import json, subprocess, sys, math
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

WD = sys.argv[1].rstrip('/') + '/'; FD = sys.argv[2].rstrip('/') + '/'
W, H = 1080, 1920; FPS = 30
TR = json.load(open(WD + 'trim.json')); KEEP = TR['keep']; DUR = TR['newdur']
WORDS = json.load(open(WD + 'words_final.json'))
WT = {int(k): v for k, v in json.load(open(WD + 'wt.json')).items()}
FACE = json.load(open(WD + 'face.json'))

def T(i):
    while i not in WT: i += 1
    return WT[i][0]
def TE(i):
    while i not in WT: i -= 1
    return WT[i][1]
def mp(t):
    acc = 0
    for s, e in KEEP:
        if t < s: return acc
        if t <= e: return acc + (t - s)
        acc += e - s
    return acc
BOUNDS = []; acc = 0
for s, e in KEEP: BOUNDS.append((acc, acc + e - s)); acc += e - s
FACE_N = [(mp(t), cx, cy, sz) for t, cx, cy, sz in FACE]

# ---------------- palette / fonts ----------------
GOLD = (201, 169, 110); CREAM = (244, 241, 234); NAVY = (14, 17, 23); MUTED = (184, 184, 188); DIM = (124, 124, 130)
RED = (255, 34, 28); VGOLD = (255, 194, 26); CYAN = (0, 229, 255); GREEN = (30, 255, 110); DEEP = (2, 3, 8)
INK = (6, 8, 14); WHITE = (255, 255, 255); BLUE = (79, 163, 224); AMBER = (240, 160, 48); CHIP = (40, 12, 18)
BEB = 'BebasNeue-Regular.ttf'; BAR = 'BarlowCondensed-Bold.ttf'; BARS = 'BarlowCondensed-SemiBold.ttf'
MONO = 'JetBrainsMono-Medium.ttf'; MONOB = 'JetBrainsMono-Bold.ttf'
_fc = {}
def f(n, s):
    k = (n, int(s))
    if k not in _fc: _fc[k] = ImageFont.truetype(FD + n, int(s))
    return _fc[k]
def clamp(x, a=0, b=1): return max(a, min(b, x))
def expo(x): x = clamp(x); return 1 if x >= 1 else 1 - 2 ** (-10 * x)
def ease_io(x): x = clamp(x); return 4 * x ** 3 if x < .5 else 1 - (-2 * x + 2) ** 3 / 2
def back(x):  # heavy landing, tiny settle (no cartoon bounce)
    x = clamp(x); c = 1.2; return 1 + (c + 1) * (x - 1) ** 3 + c * (x - 1) ** 2
def lerp(a, b, t): return a + (b - a) * t
def A(c, a): return tuple(c[:3]) + (int(clamp(a) * 255),)
def ap(t, t0, d=0.16): return expo((t - t0) / d)
GL = None

# ---------------- primitives ----------------
def txt(d, x, y, s, font, col, a=1.0, anchor=None):
    if a > 0: d.text((x, y), s, font=font, fill=A(col, a), anchor=anchor)
def brackets(d, x0, y0, x1, y1, col, L=34, w=4):
    for (cx, cy, sx, sy) in [(x0, y0, 1, 1), (x1, y0, -1, 1), (x0, y1, 1, -1), (x1, y1, -1, -1)]:
        d.line([(cx, cy), (cx + sx * L, cy)], fill=col, width=w); d.line([(cx, cy), (cx, cy + sy * L)], fill=col, width=w)
def lit_bar(d, x0, y0, x1, y1, col, a=1.0):
    h = max(1, int(y1 - y0))
    if x1 <= x0: return
    for i in range(h):
        k = i / h; c = tuple(int(min(255, v * (1.18 - 0.36 * k) + (40 if k < 0.12 else 0))) for v in col)
        d.line([(x0, y0 + i), (x1, y0 + i)], fill=c + (int(255 * clamp(a)),))
def tag(d, x, y, label, col=RED, size=30, a=1.0, glow=True, anchor_right=False):
    if a <= 0: return x
    fn = f(MONOB, size); tw = d.textlength(label, font=fn); h = size + 16
    if anchor_right: x = x - tw - 24
    lit_bar(d, x, y, x + tw + 24, y + h, col, a)
    d.text((x + 12, y + 6), label, font=fn, fill=A(INK if col in (VGOLD, GREEN, CYAN) else WHITE, a))
    if GL and glow: GL.rectangle([x - 4, y - 4, x + tw + 28, y + h + 4], outline=A(col, a), width=8)
    return x + tw + 24
def chip(d, x, y, label, a=1.0, size=34):
    if a <= 0: return x
    fn = f(BAR, size); tw = d.textlength(label, font=fn)
    d.rounded_rectangle([x, y, x + tw + 32, y + size + 18], radius=8, fill=A(CHIP, 0.95 * a), outline=A(RED, a), width=3)
    d.text((x + 16, y + 6), label, font=fn, fill=A((255, 150, 140), a))
    if GL: GL.rounded_rectangle([x, y, x + tw + 32, y + size + 18], radius=8, outline=A(RED, a * 0.7), width=6)
    return x + tw + 32
def check(d, x, y, col, s=1.0, a=1.0):
    if a <= 0: return
    pts = [(x, y + 16 * s), (x + 10 * s, y + 28 * s), (x + 30 * s, y + 2 * s)]
    d.line(pts, fill=A(col, a), width=int(6 * s), joint='curve')
    if GL: GL.line(pts, fill=A(col, a), width=int(12 * s))
def cross(d, x, y, col, s=1.0, a=1.0):
    if a <= 0: return
    d.line([(x, y), (x + 28 * s, y + 28 * s)], fill=A(col, a), width=int(6 * s)); d.line([(x + 28 * s, y), (x, y + 28 * s)], fill=A(col, a), width=int(6 * s))
    if GL: GL.line([(x, y), (x + 28 * s, y + 28 * s)], fill=A(col, a), width=12); GL.line([(x + 28 * s, y), (x, y + 28 * s)], fill=A(col, a), width=12)
def arrow(d, x0, y0, x1, y1, col, w=5, a=1.0, glow=False):
    if a <= 0: return
    d.line([(x0, y0), (x1, y1)], fill=A(col, a), width=w)
    ang = math.atan2(y1 - y0, x1 - x0); L = 18
    d.polygon([(x1, y1), (x1 - L * math.cos(ang - 0.45), y1 - L * math.sin(ang - 0.45)), (x1 - L * math.cos(ang + 0.45), y1 - L * math.sin(ang + 0.45))], fill=A(col, a))
    if GL and glow: GL.line([(x0, y0), (x1, y1)], fill=A(col, a), width=w + 6)
def flow(d, x0, y0, x1, y1, t, col, n=4, speed=0.9, a=1.0, r=6):
    for k in range(n):
        p = (t * speed + k / n) % 1
        x = lerp(x0, x1, p); y = lerp(y0, y1, p); fa = a * min(1, p * 6, (1 - p) * 6)
        d.ellipse([x - r, y - r, x + r, y + r], fill=A(col, fa))
        if GL: GL.ellipse([x - r * 2, y - r * 2, x + r * 2, y + r * 2], fill=A(col, fa))
def node(d, x0, y0, x1, y1, title, col, a=1.0, size=40, dim=False, sub=None):
    if a <= 0: return
    c = col if not dim else tuple(int(v * 0.35) for v in col)
    d.rounded_rectangle([x0, y0, x1, y1], radius=12, fill=A((10, 14, 24), 0.96 * a), outline=A(c, a), width=4)
    if GL and not dim: GL.rounded_rectangle([x0, y0, x1, y1], radius=12, outline=A(col, a * 0.8), width=8)
    cy = (y0 + y1) / 2 - (10 if sub else 0)
    txt(d, (x0 + x1) / 2, cy, title, f(BEB, size), WHITE if not dim else (110, 110, 120), a, 'mm')
    if sub: txt(d, (x0 + x1) / 2, y1 - 20, sub, f(MONO, 20), c, a, 'mm')
def kicker(d, x, y, label, a=1.0, col=VGOLD, size=26):
    if a <= 0: return
    p = clamp(a); d.line([(x, y + size * 0.55), (x + 44 * p, y + size * 0.55)], fill=A(col, a), width=4)
    txt(d, x + 58, y, label, f(MONOB, size), col, a)
def pill(d, x, y, label, col=VGOLD, a=1.0, size=28):
    if a <= 0: return x
    fn = f(MONOB, size); tw = d.textlength(label, font=fn)
    lit_bar(d, x, y, x + tw + 28, y + size + 18, col, a); d.text((x + 14, y + 7), label, font=fn, fill=A(INK, a))
    if GL: GL.rectangle([x - 3, y - 3, x + tw + 31, y + size + 21], outline=A(col, a * 0.8), width=6)
    return x + tw + 28
def mini_steps(d, x, y, cur, a=1.0):
    if a <= 0: return
    for i in range(3):
        cx = x + i * 44
        if i < 2: d.line([(cx + 10, y), (cx + 34, y)], fill=A((90, 94, 110), a), width=3)
    for i in range(3):
        cx = x + i * 44; col = GREEN if i < cur else (VGOLD if i == cur else (70, 74, 90))
        r = 11 if i == cur else 8
        d.ellipse([cx - r, y - r, cx + r, y + r], fill=A(col, a))
        if GL and i == cur: GL.ellipse([cx - 16, y - 16, cx + 16, y + 16], fill=A(col, a))
def frosted(im, box, dark=0.86, blur=10):
    x0, y0, x1, y1 = [int(v) for v in box]
    x0 = max(0, x0); y0 = max(0, y0); x1 = min(W, x1); y1 = min(H, y1)
    if x1 <= x0 or y1 <= y0: return
    reg = im.crop((x0, y0, x1, y1)).convert('RGB').filter(ImageFilter.GaussianBlur(blur))
    im.paste(Image.blend(reg, Image.new('RGB', reg.size, DEEP), dark).convert('RGBA'), (x0, y0))
def step_header(d, x, y, n, title, a, size=56):
    if a <= 0: return
    xe = pill(d, x, y + 6, f'STEP 0{n}', VGOLD, a, 26)
    txt(d, xe + 20, y, title, f(BEB, size), CREAM, a)
    mini_steps(d, 1010 - 88, y + 26, n - 1, a)

# ---------------- background for graphic layouts ----------------
def make_bg():
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    base = np.zeros((H, W, 3), np.float32) + np.array([11, 14, 21], np.float32)
    g = np.exp(-(((xx - 980) / 700) ** 2 + ((yy - 120) / 900) ** 2)) * 26
    base += g[..., None] * np.array([1.0, 0.8, 0.55])
    r2 = np.exp(-(((xx - 120) / 600) ** 2 + ((yy - 1700) / 700) ** 2)) * 14
    base += r2[..., None] * np.array([1.0, 0.15, 0.12])
    grid = ((xx % 60) < 1.2) | ((yy % 60) < 1.2)
    base[grid] += 7
    vig = 1 - 0.35 * (((xx - W / 2) / W) ** 2 + ((yy - H / 2) / H) ** 2) * 2
    base *= vig[..., None]
    rng = np.random.default_rng(3); base += rng.normal(0, 2.0, (H, W, 1))
    return Image.fromarray(np.clip(base, 0, 255).astype(np.uint8)).convert('RGBA')
BG = None

# ---------------- layouts ----------------
# mask (x0,y0,x1,y1,radius), footage scale, face target (fx,fy) ; fx None = keep face x
LAY = {
    'split': dict(mask=(0, 0, W, 1000, 0), s=1.0, fx=None, fy=470, cap=(858, 100)),
    'circ':  dict(mask=(335, 375, 745, 785, 205), s=0.58, fx=540, fy=575, cap=(820, 100)),
    'rect':  dict(mask=(590, 400, 1020, 850, 28), s=0.62, fx=805, fy=615, cap=(872, 96)),
    'circs': dict(mask=(80, 435, 410, 765, 165), s=0.45, fx=245, fy=595, cap=(872, 96)),
}
CAP_NORMAL = (1335, 128)

# ---------------- scenes ----------------
SC = []  # (t0, t1, layout or None, fn)
def scene(t0, t1, layout=None):
    def deco(fn): SC.append((t0, t1, layout, fn)); return fn
    return deco

# S1  chest scan tag (normal footage)
@scene(T(9) - 0.1, TE(29) + 0.35)
def s1(d, t, a, im):
    x0, y0, x1, y1 = 560, 1560, 910, 1760
    p = ap(t, T(9) - 0.1, 0.14)
    brackets(d, x0, y0, x1, y1, A(RED, a * p), 34, 6)
    if GL: brackets(GL, x0, y0, x1, y1, A(RED, a * p), 34, 12)
    # scan line
    sy = y0 + (y1 - y0) * ((t * 0.9) % 1)
    d.line([(x0 + 8, sy), (x1 - 8, sy)], fill=A(CYAN, 0.7 * a * p), width=2)
    if GL: GL.line([(x0 + 8, sy), (x1 - 8, sy)], fill=A(CYAN, a * p), width=6)
    tag(d, x0, y0 - 54, 'SORE · TENDER', RED, 26, a * p)
    # 7-day strip
    if t >= T(13):
        q = ap(t, T(13), 0.2) * a
        txt(d, 100, 1506, 'DAYS SORE', f(MONOB, 22), CREAM, q)
        for k in range(7):
            on = clamp((t - T(13) - k * 0.07) / 0.08)
            bx = 100 + k * 58
            d.rectangle([bx, 1542, bx + 48, 1582], outline=A((120, 124, 140), q), width=2)
            if on > 0: lit_bar(d, bx + 3, 1545, bx + 45, 1579, RED, q * on)
            txt(d, bx + 24, 1562, str(k + 1), f(MONOB, 20), WHITE, q * on, 'mm')
    for k, (lab, i) in enumerate([('POKING', 18), ('PRODDING', 22), ('SHOWER CHECKS', 25)]):
        if t >= T(i): tag(d, 100, 1602 + k * 50, lab, VGOLD, 24, a * ap(t, T(i)))

# S2  reversibility curve (split)
@scene(T(45) - 0.25, TE(71) + 0.55, 'split')
def s2(d, t, a, im):
    kicker(d, 70, 1028, 'THE WINDOW', a); txt(d, 1010, 1028, 'REVERSIBILITY', f(MONOB, 26), CREAM, a, 'ra')
    x0, x1, y0, y1 = 120, 990, 1100, 1500
    def u2x(u): return lerp(x0, x1, u)
    def fu(u): return 1 / (1 + math.exp((u - 0.5) * 11))
    def u2y(u): return y1 - 18 - fu(u) * (y1 - y0 - 40)
    # zones
    if t >= T(55):
        q = ap(t, T(55), 0.25) * a
        d.rectangle([u2x(0), y0, u2x(0.33), y1], fill=A(GREEN, 0.13 * q))
        tag(d, u2x(0) + 10, y1 - 60, 'PROTOCOL WINDOW', GREEN, 26, q)
    if t >= T(62):
        q = ap(t, T(62), 0.25) * a
        d.rectangle([u2x(0.62), y0, u2x(1), y1], fill=A(RED, 0.16 * q))
        txt(d, u2x(0.81), y0 + 20, 'HARD · FIBROTIC', f(MONOB, 26), (255, 140, 130), q, 'mt')
    d.line([(x0, y1), (x1, y1)], fill=A((110, 114, 130), a), width=2); d.line([(x0, y0), (x0, y1)], fill=A((110, 114, 130), a), width=2)
    for k in (1, 2, 3, 4): d.line([(x0, y1 - k * 80), (x1, y1 - k * 80)], fill=A((40, 44, 60), a), width=1)
    txt(d, x0 + 14, y0 + 4, 'REVERSIBLE ↑', f(MONOB, 24), MUTED, a)
    txt(d, u2x(0.12), y1 + 14, 'WEEKS', f(MONOB, 26), MUTED, a, 'mt'); txt(d, u2x(0.85), y1 + 14, 'MONTHS', f(MONOB, 26), MUTED, a, 'mt')
    # curve draw
    pr = clamp((t - (T(45) - 0.05)) / 1.0)
    pts = [(u2x(u / 80), u2y(u / 80)) for u in range(0, int(80 * pr) + 1)]
    if len(pts) > 1:
        d.line(pts, fill=A(CYAN, a), width=8, joint='curve')
        if GL: GL.line(pts, fill=A(CYAN, a), width=14)
    # now marker
    if t >= T(46):
        q = ap(t, T(46), 0.18) * a; ux = u2x(0.1); uy = u2y(0.1)
        for yy in range(int(y0), int(y1), 18): d.line([(ux, yy), (ux, yy + 9)], fill=A(VGOLD, q), width=3)
        d.ellipse([ux - 13, uy - 13, ux + 13, uy + 13], fill=A(VGOLD, q))
        if GL: GL.ellipse([ux - 22, uy - 22, ux + 22, uy + 22], fill=A(VGOLD, q))
        tag(d, ux + 30, uy + 30, 'YOU · NOW', VGOLD, 28, q)
    # waiting: dot slides down the curve
    if t >= T(59):
        u = lerp(0.1, 0.86, ease_io((t - T(59)) / 1.6)); ux, uy = u2x(u), u2y(u)
        d.ellipse([ux - 12, uy - 12, ux + 12, uy + 12], fill=A(RED, a));
        if GL: GL.ellipse([ux - 22, uy - 22, ux + 22, uy + 22], fill=A(RED, a))
    if t >= T(71):
        p = back((t - T(71)) / 0.22); q = a * clamp((t - T(71)) / 0.08)
        bx0 = u2x(0.62) + 8; by = y1 - 150; bw = (u2x(1) - 8 - bx0)
        sc = lerp(1.15, 1.0, clamp(p))
        cx = bx0 + bw / 2; w2 = bw * sc / 2; h2 = 40 * sc
        lit_bar(d, cx - w2, by - h2, cx + w2, by + h2, RED, q)
        if GL: GL.rectangle([cx - w2 - 4, by - h2 - 4, cx + w2 + 4, by + h2 + 4], outline=A(RED, q), width=10)
        txt(d, cx, by + 2, 'SURGERY ONLY', f(BEB, int(58 * sc)), WHITE, q, 'mm')

# S3  tissue scan, early vs late (circle PiP)
LOB = [(math.cos(k * 2.4) * (30 + 14 * (k % 3)) , math.sin(k * 2.4) * (26 + 12 * (k % 4)), 22 + 6 * (k % 3)) for k in range(11)]
rngF = np.random.default_rng(11)
FIB = [(rngF.uniform(-110, 110), rngF.uniform(-80, 80), rngF.uniform(0, math.pi), rngF.uniform(26, 60)) for _ in range(70)]
@scene(T(91) - 0.25, TE(128) + 0.45, 'circ')
def s3(d, t, a, im):
    kicker(d, 70, 420, 'TISSUE SCAN', a); txt(d, 1010, 420, 'EARLY vs LATE', f(MONOB, 26), CREAM, a, 'ra')
    # left card: early
    L = (70, 960, 525, 1590); R_ = (555, 960, 1010, 1590)
    qa = a
    d.rounded_rectangle(L, radius=16, fill=A((8, 12, 22), 0.9 * qa), outline=A(CYAN, qa), width=3)
    if GL: GL.rounded_rectangle(L, radius=16, outline=A(CYAN, qa * 0.6), width=6)
    txt(d, L[0] + 22, L[1] + 18, 'EARLY · WEEKS', f(MONOB, 26), CYAN, qa)
    cx, cy = (L[0] + L[2]) / 2, 1290
    shrink = 1.0 if t < T(100) else lerp(1.0, 0.55, ease_io((t - T(100)) / 2.2))
    br = 1 + 0.05 * math.sin(t * 3)
    for (lx, ly, lr) in LOB:
        rr = lr * shrink * br * 1.3; x = cx + lx * shrink * 2.1; y = cy + ly * shrink * 2.1
        d.ellipse([x - rr, y - rr, x + rr, y + rr], fill=A((0, 120, 150), 0.35 * qa), outline=A(CYAN, qa), width=3)
        if GL: GL.ellipse([x - rr, y - rr, x + rr, y + rr], outline=A(CYAN, qa * 0.7), width=6)
    for k, (lab, i) in enumerate([('SOFT', 95), ('TENDER', 96), ('GLANDULAR', 97)]):
        if t >= T(i): tag(d, L[0] + 22 + [0, 120, 0][k], L[1] + 66 + [0, 0, 54][k], lab, CYAN, 26, qa * ap(t, T(i)))
    if t >= T(105):
        q = qa * ap(t, T(105)); check(d, L[0] + 24, L[3] - 80, GREEN, 1.3, q); txt(d, L[0] + 76, L[3] - 84, 'REVERSIBLE', f(BEB, 60), GREEN, q)
    # right card: late
    if t >= T(108) - 0.1:
        qb = a * ap(t, T(108) - 0.1, 0.22); dy = lerp(30, 0, qb)
        d.rounded_rectangle((R_[0], R_[1] + dy, R_[2], R_[3] + dy), radius=16, fill=A((16, 8, 10), 0.92 * qb), outline=A(RED, qb), width=3)
        if GL: GL.rounded_rectangle((R_[0], R_[1] + dy, R_[2], R_[3] + dy), radius=16, outline=A(RED, qb * 0.6), width=6)
        txt(d, R_[0] + 22, R_[1] + 18 + dy, 'LATE · MONTHS', f(MONOB, 26), RED, qb)
        hard = clamp((t - T(115)) / 0.8)
        cx2, cy2 = (R_[0] + R_[2]) / 2, 1290 + dy
        d.ellipse([cx2 - 165, cy2 - 125, cx2 + 165, cy2 + 125], fill=A((60, 20, 24), (0.4 + 0.4 * hard) * qb), outline=A(RED, qb), width=3)
        for (fx, fy, fa, fl) in FIB[:int(20 + 50 * hard)]:
            x = cx2 + fx * 1.3; y = cy2 + fy * 1.3
            if (fx / 125) ** 2 + (fy / 92) ** 2 > 1: continue
            d.line([(x - math.cos(fa) * fl / 2, y - math.sin(fa) * fl / 2), (x + math.cos(fa) * fl / 2, y + math.sin(fa) * fl / 2)], fill=A((230, 140, 140), qb * 0.9), width=3)
        for k, (lab, i) in enumerate([('HARD', 116), ('FIBROTIC', 118)]):
            if t >= T(i): tag(d, R_[0] + 22 + k * 116, R_[1] + 66 + dy, lab, RED, 26, qb * ap(t, T(i)))
        if t >= T(122):
            q = qb * ap(t, T(122)); cross(d, R_[0] + 26, R_[3] - 76 + dy, RED, 1.2, q); txt(d, R_[0] + 76, R_[3] - 84 + dy, 'NO PROTOCOL', f(BEB, 60), (255, 120, 110), q)
        if t >= T(127):
            q = qb * clamp((t - T(127)) / 0.08); sc = lerp(1.2, 1, clamp(back((t - T(127)) / 0.2)))
            cx3, cy3 = cx2, cy2; w2 = 170 * sc; h2 = 44 * sc
            lit_bar(d, cx3 - w2, cy3 - h2, cx3 + w2, cy3 + h2, RED, q)
            if GL: GL.rectangle([cx3 - w2 - 4, cy3 - h2 - 4, cx3 + w2 + 4, cy3 + h2 + 4], outline=A(RED, q), width=10)
            txt(d, cx3, cy3 + 2, 'SURGERY', f(BEB, int(68 * sc)), WHITE, q, 'mm')
    # scan sweep
    sx = lerp(70, 1010, (t * 0.45) % 1)
    d.line([(sx, 960), (sx, 1590)], fill=A(CYAN, 0.55 * a), width=2)
    if GL: GL.line([(sx, 960), (sx, 1590)], fill=A(CYAN, 0.8 * a), width=8)

# S4  three-step roadmap (top card)
@scene(T(129) - 0.1, TE(148) + 0.35)
def s4(d, t, a, im):
    y0, y1 = 400, 640
    txt(d, 0, 0, '', f(MONO, 10), WHITE, 0)
    kicker(d, 90, y0 + 22, 'THE FIX · 3 STEPS', a)
    xs = [210, 540, 870]; ry = y0 + 120
    pr = clamp((t - T(131)) / 0.6)
    d.line([(xs[0], ry), (lerp(xs[0], xs[2], pr), ry)], fill=A(VGOLD, a), width=4)
    if GL: GL.line([(xs[0], ry), (lerp(xs[0], xs[2], pr), ry)], fill=A(VGOLD, a), width=10)
    for k, lab in enumerate(['FIND THE DRIVER', 'CORRECT IT', 'TREAT THE TISSUE']):
        q = a * ap(t, T(131) + k * 0.2, 0.14)
        if q <= 0: continue
        r = 34 * lerp(1.25, 1, clamp(back((t - T(131) - k * 0.2) / 0.22)))
        d.ellipse([xs[k] - r, ry - r, xs[k] + r, ry + r], fill=A((14, 16, 24), q), outline=A(VGOLD, q), width=4)
        if GL: GL.ellipse([xs[k] - r, ry - r, xs[k] + r, ry + r], outline=A(VGOLD, q), width=10)
        txt(d, xs[k], ry + 2, f'0{k + 1}', f(BEB, 44), VGOLD, q, 'mm')
        txt(d, xs[k], ry + 50, lab, f(MONOB, 22), CREAM, a * ap(t, T(131) + 0.3 + k * 0.2), 'mt')
S4_BOX = (60, 400, 1020, 640)

# S5  step 1: find the driver (split)
@scene(T(149) - 0.25, TE(221) + 0.45, 'split')
def s5(d, t, a, im):
    step_header(d, 70, 1022, 1, 'FIND THE DRIVER', a)
    tb = T(204)
    qa = a * (1 - clamp((t - tb) / 0.25))
    if qa > 0:
        rows = [(1120, 'TRT', 164), (1270, 'OTHER ANABOLICS', 173), (1420, 'NPP / DECA', 192)]
        for (y, lab, i) in rows:
            if t >= T(i): node(d, 70, y, 410, y + 104, lab, CREAM, qa * ap(t, T(i)), 46)
        E2 = (680, 1120, 1010, 1300); PRL = (680, 1380, 1010, 1540)
        if t >= T(168):
            q = qa * ap(t, T(168)); node(d, *E2, 'ESTRADIOL', CYAN, q, 54, sub='E2')
            arrow(d, 414, 1172, 674, 1190, CYAN, 6, q, True); flow(d, 414, 1172, 674, 1190, t, CYAN, 4, a=q)
        if t >= T(178):
            q = qa * ap(t, T(178)); hot = t >= T(196)
            node(d, *PRL, 'PROLACTIN', RED if hot else AMBER, q, 54, sub='PRL')
            if t < T(181) + 0.4:
                for k in range(12):
                    xx = lerp(414, 674, k / 12); yy = lerp(1322, 1430, k / 12); xx2 = lerp(414, 674, (k + 0.5) / 12); yy2 = lerp(1322, 1430, (k + 0.5) / 12)
                    d.line([(xx, yy), (xx2, yy2)], fill=A(AMBER, q * (1 - clamp((t - T(181)) / 0.4))), width=4)
        if t >= T(181):
            q = qa * ap(t, T(181)); arrow(d, 414, 1322, 674, 1240, CYAN, 8, q, True); flow(d, 414, 1322, 674, 1240, t, CYAN, 4, a=q)
            txt(d, 548, 1312, 'USUALLY', f(MONOB, 26), CYAN, q, 'mm')
        if t >= T(186):
            q = qa * ap(t, T(186)); tag(d, 420, 1100, 'AROMATIZATION', CYAN, 26, q)
        if t >= T(196):
            q = qa * ap(t, T(196)); arrow(d, 414, 1472, 674, 1460, RED, 8, q, True); flow(d, 414, 1472, 674, 1460, t, RED, 4, a=q)
            tag(d, 1010, 1552, 'ON THE TABLE', RED, 26, q, anchor_right=True)
    if t >= tb:
        q = a * ap(t, tb, 0.25); dy = lerp(120, 0, expo((t - tb) / 0.3))
        slip_draw(d, t, q, dy)
def slip_draw(d, t, q, dy):
    x0, y0, x1, y1 = 90, 1120 + dy, 990, 1560 + dy
    d.rectangle([x0 + 8, y0 + 10, x1 + 8, y1 + 10], fill=A((0, 0, 0), 0.5 * q))
    d.rectangle([x0, y0, x1, y1], fill=A((238, 236, 230), q))
    d.rectangle([x0, y0, x1, y0 + 72], fill=A((16, 24, 48), q))
    txt(d, x0 + 26, y0 + 18, 'LAB ORDER · HORMONE PANEL', f(MONOB, 32), WHITE, q)
    rows = [('Estradiol, Sensitive', 'LC/MS-MS', 206), ('Prolactin', 'Serum', 210)]
    for k, (nm, meth, i) in enumerate(rows):
        y = y0 + 110 + k * 140
        d.rectangle([x0 + 28, y, x0 + 88, y + 60], outline=A((40, 44, 60), q), width=4)
        if t >= T(i):
            p = ap(t, T(i), 0.12)
            d.line([(x0 + 36, y + 30), (x0 + 54, y + 50), (x0 + 84, y + 6)], fill=A((0, 150, 70), q * p), width=9)
        txt(d, x0 + 112, y - 6, nm, f(BAR, 58), (30, 32, 40), q)
        txt(d, x0 + 112, y + 56, meth, f(MONO, 26), (110, 110, 120), q)
        d.line([(x0 + 24, y + 112), (x1 - 24, y + 112)], fill=A((205, 205, 210), q), width=2)
    if t >= T(211):
        p = clamp((t - T(211)) / 0.14); sc = lerp(1.5, 1.0, expo(p)); qq = q * p
        stamp(d, x1 - 200, y0 + 360, 'PULL FIRST', sc * 1.15, qq, -8)
def stamp(d, cx, cy, label, sc, a, ang):
    if a <= 0: return
    fn = f(BEB, int(70 * sc)); tw = d.textlength(label, font=fn)
    lay = Image.new('RGBA', (int(tw + 60), int(110 * sc)), (0, 0, 0, 0)); ld = ImageDraw.Draw(lay)
    ld.rounded_rectangle([3, 3, lay.width - 4, lay.height - 4], radius=10, outline=(210, 10, 20, int(230 * a)), width=7)
    ld.text((lay.width / 2, lay.height / 2 + 3), label, font=fn, fill=(210, 10, 20, int(230 * a)), anchor='mm')
    lay = lay.rotate(ang, expand=True, resample=Image.BICUBIC)
    STAMPS.append((lay, int(cx - lay.width / 2), int(cy - lay.height / 2)))
STAMPS = []

# S6  step 2: correct, don't crash (top card, gauges)
S6_BOX = (60, 400, 1020, 700)
@scene(T(222) - 0.1, TE(278) + 0.35)
def s6(d, t, a, im):
    x0, y0 = 90, 418
    xe = pill(d, x0, y0 + 4, 'STEP 02', VGOLD, a, 24)
    txt(d, xe + 18, y0 - 4, 'CORRECT · DON\'T CRASH', f(BEB, 52), CREAM, a); mini_steps(d, 1000 - 88, y0 + 22, 1, a)
    bx0, bx1 = 230, 990
    def bar(y, label, mval, dim=1.0):
        q = a * dim
        txt(d, x0, y - 6, label, f(BEB, 46), WHITE, q)
        segs = [(0, 0.3, BLUE), (0.3, 0.64, GREEN), (0.64, 0.82, AMBER), (0.82, 1.0, RED)]
        for (u0, u1, c) in segs:
            d.rectangle([lerp(bx0, bx1, u0) + 2, y, lerp(bx0, bx1, u1) - 2, y + 26], fill=A(tuple(int(v * 0.75) for v in c), q))
        if GL: GL.rectangle([bx0 + 2, y, bx1 - 2, y + 26], outline=A(WHITE, 0.0), width=1)
        for (u, lab) in [(0.15, 'LOW'), (0.47, 'IN RANGE'), (0.82, 'HIGH')]:
            txt(d, lerp(bx0, bx1, u), y + 34, lab, f(MONO, 18), MUTED, q, 'mt')
        mx = lerp(bx0, bx1, mval)
        d.polygon([(mx, y - 4), (mx - 14, y - 26), (mx + 14, y - 26)], fill=A(WHITE, q)); d.line([(mx, y - 4), (mx, y + 30)], fill=A(WHITE, q), width=4)
        if GL: GL.line([(mx, y - 8), (mx, y + 32)], fill=A(WHITE, q), width=10)
        return mx
    # E2 marker: high -> range -> zero
    e2 = 0.9
    if t >= T(237): e2 = lerp(0.9, 0.47, back((t - T(237)) / 0.5))
    if t >= T(251): e2 = lerp(0.47, 0.02, expo((t - T(251)) / 0.25))
    mx = bar(500, 'E2', e2)
    if T(240) <= t < T(251): check(d, mx + 22, 466, GREEN, 0.9, a * ap(t, T(240)))
    if t >= T(251):
        q = a * ap(t, T(251) + 0.15); tag(d, mx + 28, 526, 'NUKED TO ZERO', RED, 22, q)
    prl = 0.86
    if t >= T(243): prl = lerp(0.86, 0.47, back((t - T(243)) / 0.5))
    pdim = 1.0 if t < T(269) else lerp(1.0, 0.35, clamp((t - T(269)) / 0.3))
    if t < T(258):
        mx2 = bar(600, 'PRL', prl, pdim)
        if T(245) <= t: check(d, mx2 + 22, 566, GREEN, 0.9, a * ap(t, T(245)))
    else:
        # side-effect row replaces PRL row
        q = a * (1 if t >= T(258) + 0.2 else ap(t, T(258), 0.2))
        txt(d, x0, 594, 'COST', f(BEB, 46), (255, 120, 110), q)
        xx = 200
        for (lab, i) in [('DEAD JOINTS', 262), ('NO LIBIDO', 264), ('FLAT MOOD', 266)]:
            if t >= T(i): xx = chip(d, xx, 590, lab, a * ap(t, T(i)), 34) + 14
    if t >= T(269):
        q = a * ap(t, T(269)); tag(d, 990, 646, 'PROLACTIN = DIFFERENT TOOL', VGOLD, 22, q, anchor_right=True)

# S7  step 3: treat the tissue (rect PiP)
@scene(T(281) - 0.25, TE(357) + 0.45, 'rect')
def s7(d, t, a, im):
    pill(d, 70, 412, 'STEP 03', VGOLD, a, 24); mini_steps(d, 410, 432, 2, a)
    txt(d, 70, 470, 'TREAT THE', f(BEB, 78), CREAM, a); txt(d, 70, 540, 'TISSUE', f(BEB, 78), VGOLD, a)
    if t >= T(283):
        q = a * ap(t, T(283)); txt(d, 70, 640, 'FIX THE BIOMARKER', f(MONOB, 24), CREAM, q)
    if t >= T(289):
        q = a * ap(t, T(289)); check(d, 72, 690, GREEN, 0.9, q); txt(d, 116, 684, 'STOPS IT WORSENING', f(BAR, 38), GREEN, q)
    if t >= T(297):
        q = a * ap(t, T(297)); cross(d, 74, 752, RED, 0.9, q); txt(d, 116, 744, 'SHRINKS WHAT\'S THERE', f(BAR, 38), (255, 120, 110), q)
    tB = T(332)
    qa = a * (1 - clamp((t - tB) / 0.25))
    if t >= T(302) - 0.2 and qa > 0:
        q0 = qa * ap(t, T(302) - 0.2, 0.25)
        kicker(d, 70, 1010, 'SERM · BREAST RECEPTOR', q0)
        # receptor dock
        rx, ry = 560, 1400
        d.arc([rx - 120, ry - 120, rx + 120, ry + 120], 0, 180, fill=A(WHITE, q0), width=10)
        d.line([(rx - 120, ry), (rx - 120, ry - 60)], fill=A(WHITE, q0), width=10); d.line([(rx + 120, ry), (rx + 120, ry - 60)], fill=A(WHITE, q0), width=10)
        if GL: GL.arc([rx - 120, ry - 120, rx + 120, ry + 120], 0, 180, fill=A(WHITE, q0 * 0.5), width=14)
        txt(d, rx, ry + 150, 'BREAST TISSUE RECEPTOR', f(MONOB, 26), MUTED, q0, 'mm')
        # SERM capsule
        ts = T(324)
        sx = 860 if t < ts else lerp(860, rx, back((t - ts) / 0.45)); sy = 1230 if t < ts else lerp(1230, ry - 30, back((t - ts) / 0.45))
        d.rounded_rectangle([sx - 96, sy - 46, sx + 96, sy + 46], radius=46, fill=A(VGOLD, q0))
        if GL: GL.rounded_rectangle([sx - 100, sy - 50, sx + 100, sy + 50], radius=48, outline=A(VGOLD, q0), width=8)
        txt(d, sx, sy + 2, 'SERM', f(BEB, 62), INK, q0, 'mm')
        if t >= T(312): tag(d, 1010, 1080, 'RALOXIFENE', VGOLD, 26, q0 * ap(t, T(312)), anchor_right=True)
        if t >= T(317): tag(d, 1010, 1136, 'NOLVADEX', VGOLD, 26, q0 * ap(t, T(317)), anchor_right=True)
        # estrogen: approaches, bounces off once SERM docked
        cyc = ((t - T(302)) % 1.6) / 1.6
        if t < ts + 0.4:
            ex = lerp(140, rx - 10, ease_io(min(1, cyc * 1.6))); ey = lerp(1230, ry - 30, ease_io(min(1, cyc * 1.6)))
            ea = q0 * (1 - clamp((cyc - 0.8) / 0.2))
        else:
            k = cyc
            if k < 0.5: ex = lerp(140, rx - 200, ease_io(k / 0.5)); ey = lerp(1230, ry - 40, ease_io(k / 0.5))
            else: ex = lerp(rx - 200, 160, expo((k - 0.5) / 0.5)); ey = lerp(ry - 40, 1200, expo((k - 0.5) / 0.5))
            ea = q0
        hexr = 54; pts = [(ex + hexr * math.cos(math.pi / 3 * i), ey + hexr * math.sin(math.pi / 3 * i)) for i in range(6)]
        d.polygon(pts, fill=A((0, 90, 110), ea), outline=A(CYAN, ea)); d.line(pts + [pts[0]], fill=A(CYAN, ea), width=4)
        if GL: GL.line(pts + [pts[0]], fill=A(CYAN, ea), width=8)
        txt(d, ex, ey + 2, 'E2', f(BEB, 50), WHITE, ea, 'mm')
        if t >= T(326):
            q = q0 * ap(t, T(326)); brackets(d, rx - 300, ry - 150, rx - 100, ry + 50, A(RED, q), 26, 6)
            if GL: brackets(GL, rx - 300, ry - 150, rx - 100, ry + 50, A(RED, q), 26, 12)
            tag(d, rx - 300, ry + 62, 'BLOCKED', RED, 28, q)
    if t >= tB:
        q0 = a * ap(t, tB, 0.25)
        kicker(d, 70, 1010, 'DOSE · FIRST WEEKS', q0)
        cx0, cx1, cy0, cy1 = 150, 990, 1090, 1520
        d.line([(cx0, cy1), (cx1, cy1)], fill=A((110, 114, 130), q0), width=2)
        y2x = cy1 - 300; y1x = cy1 - 150
        for (yy, lab) in [(y2x, '2×'), (y1x, '1×')]:
            for xx in range(cx0, cx1, 20): d.line([(xx, yy), (xx + 10, yy)], fill=A((70, 74, 90), q0), width=2)
            txt(d, cx0 - 16, yy, lab, f(BEB, 40), MUTED, q0, 'rm')
        bw = 100; gap = (cx1 - cx0 - 6 * bw) / 7
        for k in range(6):
            bx = cx0 + gap + k * (bw + gap)
            if k < 2: t0 = T(335) + k * 0.12; hgt = 300; col = VGOLD
            else: t0 = T(351) + (k - 2) * 0.1; hgt = 150; col = CYAN
            if t < t0:
                txt(d, bx + bw / 2, cy1 + 16, f'W{k + 1}', f(MONOB, 26), DIM, q0, 'mt'); continue
            p = back((t - t0) / 0.35); hh = hgt * clamp(p, 0, 1.08)
            lit_bar(d, bx, cy1 - hh, bx + bw, cy1, col, q0)
            if GL: GL.rectangle([bx, cy1 - hh, bx + bw, cy1], outline=A(col, q0 * 0.8), width=6)
            txt(d, bx + bw / 2, cy1 + 16, f'W{k + 1}', f(MONOB, 26), CREAM, q0, 'mt')
        if t >= T(340):
            q = q0 * ap(t, T(340)); bx_a = cx0 + gap; bx_b = cx0 + gap + bw + gap + bw
            d.line([(bx_a, y2x - 30), (bx_b, y2x - 30)], fill=A(VGOLD, q), width=3); d.line([(bx_a, y2x - 30), (bx_a, y2x - 14)], fill=A(VGOLD, q), width=3); d.line([(bx_b, y2x - 30), (bx_b, y2x - 14)], fill=A(VGOLD, q), width=3)
            txt(d, (bx_a + bx_b) / 2, y2x - 40, '2 WEEKS · DOUBLE', f(MONOB, 26), VGOLD, q, 'mb')
        if t >= T(347): tag(d, 990, y2x - 20, 'SATURATE', CYAN, 26, q0 * ap(t, T(347)), anchor_right=True)
        if t >= T(355): tag(d, 990, y1x - 76, 'SINGLE DOSE', CYAN, 26, q0 * ap(t, T(355)), anchor_right=True)

# S8  privacy: client file (split)
@scene(T(359) - 0.25, TE(410) + 0.45, 'split')
def s8(d, t, a, im):
    kicker(d, 70, 1028, 'CLIENT PRIVACY', a)
    x0, y0, x1, y1 = 90, 1100, 990, 1570
    d.rectangle([x0 + 10, y0 + 12, x1 + 10, y1 + 12], fill=A((0, 0, 0), 0.5 * a))
    d.rectangle([x0, y0, x1, y1], fill=A((226, 222, 212), a))
    d.rectangle([x0, y0, x1, y0 + 70], fill=A((30, 30, 36), a))
    txt(d, x0 + 26, y0 + 16, 'CLIENT FILE', f(MONOB, 34), WHITE, a)
    fields = [('NAME', 0.62), ('PROTOCOL', 0.78), ('BLOODWORK', 0.7), ('PHOTOS', 0.5)]
    for k, (lab, wfr) in enumerate(fields):
        y = y0 + 106 + k * 92
        txt(d, x0 + 26, y + 8, lab, f(MONOB, 30), (90, 90, 96), a)
        t0 = T(368) + k * 0.16
        bx0 = x0 + 290; bx1 = bx0 + (x1 - 40 - bx0) * wfr
        if t >= t0:
            p = expo((t - t0) / 0.18); d.rectangle([bx0, y, lerp(bx0, bx1, p), y + 52], fill=A((8, 8, 10), a))
        else:
            txt(d, bx0, y + 4, '—' * 3, f(MONO, 26), (150, 150, 155), a)
    if t >= T(394):
        tag(d, x1, y0 - 62, 'POSTED = FOREVER', RED, 28, a * ap(t, T(394)), anchor_right=True)
    if t >= T(406):
        p = clamp((t - T(406)) / 0.14); stamp(d, (x0 + x1) / 2 + 110, y0 + 290, 'CONFIDENTIAL', lerp(1.7, 1.2, expo(p)), a * p, 7)

# S9  client case (small circle PiP, data)
@scene(T(411) - 0.25, TE(481) + 0.45, 'circs')
def s9(d, t, a, im):
    kicker(d, 460, 430, 'CLIENT CASE', a)
    if t >= T(424) - 0.1:
        q = a * ap(t, T(424) - 0.1)
        txt(d, 460, 488, 'E2 AT START', f(MONOB, 26), CREAM, q)
        v = int(round(120 * expo((t - T(426)) / 0.6))) if t >= T(426) else 0
        col = RED if v >= 100 else VGOLD
        txt(d, 455, 520, str(v), f(BEB, 210), col, q)
        if GL and t >= T(426): GL.text((455, 520), str(v), font=f(BEB, 210), fill=A(col, q * 0.5))
        if t >= T(426) + 0.6: tag(d, 760, 640, 'HIGH', RED, 26, q)
    if t >= T(434): q = a * ap(t, T(434)); check(d, 462, 762, GREEN, 0.8, q); txt(d, 500, 754, 'FELT FINE', f(BAR, 38), GREEN, q)
    if t >= T(440): chip(d, 700, 750, 'LUMP · 2–3 WKS', a * ap(t, T(440)), 32)
    # checklist row
    for k, (lab, i) in enumerate([('FOUND', 453), ('CORRECTED', 457), ('TREATED', 460)]):
        if t >= T(i):
            q = a * ap(t, T(i)); x = 70 + k * 320
            check(d, x, 1022, GREEN, 0.9, q); txt(d, x + 42, 1012, lab, f(BEB, 52), CREAM, q)
    # chart
    if t >= T(451):
        q = a * ap(t, T(451), 0.25)
        cx0, cx1, cy0, cy1 = 130, 990, 1120, 1520
        d.line([(cx0, cy1), (cx1, cy1)], fill=A((110, 114, 130), q), width=2); d.line([(cx0, cy0), (cx0, cy1)], fill=A((110, 114, 130), q), width=2)
        by0, by1 = cy1 - 210, cy1 - 100
        d.rectangle([cx0 + 2, by0, cx1, by1], fill=A(GREEN, 0.12 * q)); txt(d, cx1 - 8, by0 + 8, 'IN RANGE', f(MONOB, 24), GREEN, q, 'ra')
        xs = [lerp(cx0 + 70, cx1 - 70, k / 4) for k in range(5)]
        for k, x in enumerate(xs): txt(d, x, cy1 + 14, f'WK {k}', f(MONOB, 26), MUTED, q, 'mt')
        e2v = [cy0 + 40, cy1 - 260, by0 + 40, by0 + 55, by0 + 52]
        lump = [1.0, 0.85, 0.55, 0.22, 0.0]
        pr = clamp((t - T(457)) / (T(466) - T(457)))
        for k, x in enumerate(xs):
            sh = lump[k] if pr * 4 >= k else None
            if sh is None: continue
            hh = 170 * sh
            if hh > 1: lit_bar(d, x - 32, cy1 - hh, x + 32, cy1, RED, q * 0.9)
        n = pr * 4; pts = []
        for k in range(5):
            if n >= k: pts.append((xs[k], e2v[k]))
            elif n > k - 1: pts.append((lerp(xs[k - 1], xs[k], n - (k - 1)), lerp(e2v[k - 1], e2v[k], n - (k - 1)))); break
        if len(pts) > 1:
            d.line(pts, fill=A(CYAN, q), width=6, joint='curve')
            if GL: GL.line(pts, fill=A(CYAN, q), width=12)
        for p_ in pts: d.ellipse([p_[0] - 8, p_[1] - 8, p_[0] + 8, p_[1] + 8], fill=A(WHITE, q))
        txt(d, cx0 + 14, cy0 - 6, 'E2 LINE · LUMP BARS · ILLUSTRATIVE', f(MONOB, 22), MUTED, q)
        if t >= T(466): tag(d, xs[4] + 40, cy1 - 70, 'GONE · 4 WKS', GREEN, 28, a * ap(t, T(466)), anchor_right=True)

# S10 MENT warning (top card)
S10_BOX = (60, 400, 1020, 660)
@scene(T(490) - 0.1, TE(520) + 0.35)
def s10(d, t, a, im):
    x0, y0, x1 = 60, 400, 1020
    lit_bar(d, x0, y0, x1, y0 + 54, RED, a)
    if GL: GL.rectangle([x0, y0, x1, y0 + 54], outline=A(RED, a), width=8)
    txt(d, x0 + 30, y0 + 10, '⚠ WARNING', f(MONOB, 28), WHITE, a); txt(d, x1 - 30, y0 + 10, 'COMPOUND · MENT', f(MONOB, 28), WHITE, a, 'ra')
    if t >= T(495): tag(d, x0 + 30, y0 + 74, 'COACH\'S ONLY GYNO CASE', VGOLD, 24, a * ap(t, T(495)))
    txt(d, x0 + 30, y0 + 140, 'AROMATIZATION', f(MONOB, 24), CREAM, a)
    mx0, mx1, my = x0 + 300, x1 - 40, y0 + 140
    d.rectangle([mx0, my, mx1, my + 34], outline=A((90, 94, 110), a), width=2)
    fr = 0.25
    if t >= T(503): fr = lerp(0.25, 1.0, expo((t - T(503)) / 0.7)) - (0.012 * (1 + math.sin(t * 40)) if t > T(503) + 0.7 else 0)
    lit_bar(d, mx0 + 3, my + 3, lerp(mx0 + 3, mx1 - 3, fr), my + 31, RED if fr > 0.6 else AMBER, a)
    if GL: GL.rectangle([mx0 + 3, my + 3, lerp(mx0 + 3, mx1 - 3, fr), my + 31], fill=A(RED, a * 0.6 * fr))
    if t >= T(508): txt(d, mx1, my + 46, 'OFF THE CHART', f(MONOB, 22), RED, a * ap(t, T(508)), 'ra')
    if t >= T(518):
        p = back((t - T(518)) / 0.22); q = a * clamp((t - T(518)) / 0.08); sc = lerp(1.15, 1.0, clamp(p))
        cx, cy = (x0 + x1) / 2, y0 + 228; w2 = 430 * sc; h2 = 34 * sc
        lit_bar(d, cx - w2, cy - h2, cx + w2, cy + h2, RED, q)
        if GL: GL.rectangle([cx - w2 - 4, cy - h2 - 4, cx + w2 + 4, cy + h2 + 4], outline=A(RED, q), width=10)
        txt(d, cx, cy + 2, 'DON\'T KNOW IT · DON\'T RUN IT', f(BEB, int(52 * sc)), WHITE, q, 'mm')

# S11 CTA + recap (split)
LOGO = None
@scene(T(521) - 0.25, DUR + 1, 'split')
def s11(d, t, a, im):
    global LOGO
    tR = T(548)
    qa = a * (1 - clamp((t - tR) / 0.12))
    if LOGO is None:
        lg = Image.open(WD + 'logo.jpg').convert('RGB'); s = min(lg.size)
        lg = lg.crop(((lg.width - s) // 2, (lg.height - s) // 2, (lg.width + s) // 2, (lg.height + s) // 2)).resize((170, 170), Image.LANCZOS)
        m = Image.new('L', (170, 170), 0); ImageDraw.Draw(m).ellipse([0, 0, 169, 169], fill=255); lg.putalpha(m); LOGO = lg
    if qa > 0:
        lg = LOGO.copy(); lg.putalpha(lg.split()[3].point(lambda v: int(v * qa))); im.alpha_composite(lg, (70, 1070))
        d.ellipse([68, 1068, 242, 1242], outline=A(VGOLD, qa), width=3)
        if t >= T(527): txt(d, 270, 1072, 'FREE · FULL PROTOCOL', f(MONOB, 28), VGOLD, qa * ap(t, T(527)))
        if t >= T(529): txt(d, 270, 1110, 'GYNO REVERSAL', f(BEB, 92), CREAM, qa * ap(t, T(529)))
        if t >= T(534): txt(d, 270, 1204, '+ EXACT BLOODWORK TO PULL', f(MONOB, 26), MUTED, qa * ap(t, T(534)))
        if t >= T(541):
            b = expo((t - T(541)) / 0.12); s = lerp(1.15, 1.0, b)
            fn = f(BEB, int(96 * s)); label = 'COMMENT  "GYNO"'; tw = d.textlength(label, font=fn)
            x = 540 - (tw + 60) / 2; y = 1300
            lit_bar(d, x, y, x + tw + 60, y + int(116 * s), VGOLD, qa * b); d.text((x + 30, y + 10), label, font=fn, fill=A(INK, qa * b))
            if GL: GL.rectangle([x - 4, y - 4, x + tw + 64, y + int(116 * s) + 4], outline=A(VGOLD, qa * b), width=12)
        txt(d, 540, 1470, 'FOR RESEARCH & EDUCATIONAL PURPOSES ONLY', f(MONO, 18), DIM, qa, 'mt')
    if t >= tR:
        q = a * ap(t, tR + 0.1, 0.2)
        kicker(d, 70, 1028, 'THE RECAP', q)
        pill(d, 1010 - 252, 1018, 'COMMENT "GYNO"', VGOLD, q, 26)
        for k, (lab, i) in enumerate([('FIND IT EARLY', 549), ('READ THE PANEL', 555), ('TREAT THE TISSUE', 561), ('CROSS-REFERENCE DOSAGES', 568)]):
            y = 1100 + k * 84
            d.rectangle([70, y + 8, 120, y + 58], outline=A((110, 114, 130), q), width=3)
            if t >= T(i):
                p = ap(t, T(i)); check(d, 78, y + 14, GREEN, 1.15, q * p); txt(d, 142, y - 2, lab, f(BEB, 66), CREAM, q * p)
            else: txt(d, 142, y - 2, lab, f(BEB, 66), (70, 74, 90), q)
        if t >= T(579):
            p = expo((t - T(579)) / 0.22); x0 = 70; x1 = lerp(x0, 1010, p); y = 1450
            lit_bar(d, x0, y, x1, y + 92, VGOLD, q)
            if GL: GL.rectangle([x0 - 4, y - 4, x1 + 4, y + 96], outline=A(VGOLD, q), width=10)
            if p > 0.6: txt(d, x0 + 30, y + 48, 'BLOODWORK = THE ROADMAP', f(BEB, 76), INK, q, 'lm')

# ---------------- text hook + topic band ----------------
HOOK = dict(lines=['Reverse GYNO', 'before it needs surgery'], emph='GYNO', end=None)
HOOK['end'] = round(max(3.0, min(6.0, TE(15) + 0.5)), 2)
MID = DUR / 2
def draw_hook(im, t):
    if t >= HOOK['end'] + 0.15: return
    a = 1 - clamp((t - HOOK['end']) / 0.15)
    s = lerp(1.0, 1.04, clamp(t / HOOK['end']))
    fn = f(BAR, int(96 * s)); lh = int(104 * s)
    d0 = ImageDraw.Draw(im, 'RGBA')
    widths = [d0.textlength(l, font=fn) for l in HOOK['lines']]
    bw = max(widths) + 70 * s; bh = lh * 2 + 46 * s; cx = 540; y0 = 300
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    d.rounded_rectangle([cx - bw / 2, y0, cx + bw / 2, y0 + bh], radius=int(26 * s), fill=(0, 0, 0, 225))
    for k, l in enumerate(HOOK['lines']):
        x = cx - widths[k] / 2; y = y0 + 18 * s + k * lh
        for word in l.split(' '):
            col = VGOLD if word == HOOK['emph'] else WHITE
            d.text((x, y), word, font=fn, fill=col + (255,)); x += d.textlength(word + ' ', font=fn)
    if a < 1: lay.putalpha(lay.split()[3].point(lambda v: int(v * a)))
    im.alpha_composite(lay)
def draw_band(im, t):
    t0 = HOOK['end']
    if t < t0 or t > MID + 0.15: return
    a = clamp((t - t0) / 0.15) * (1 - clamp((t - MID) / 0.15))
    d = ImageDraw.Draw(im, 'RGBA')
    d.rectangle([8, 212, W, 372], fill=NAVY + (int(228 * a),))
    d.line([(64, 244), (108, 244)], fill=A(GOLD, a), width=4); txt(d, 122, 228, '@coach.agz', f(MONO, 28), GOLD, a)
    fn = f(BAR, 74); x = 64
    for word, col in [('GYNO', VGOLD), ('reversal in 3 steps', CREAM)]:
        txt(d, x, 266, word, fn, col, a); x += d.textlength(word + ' ', font=fn)

# ---------------- captions ----------------
def nearest_bound(t):
    for b0, b1 in BOUNDS:
        if b0 > t + 0.01: return b0
    return 1e9
def build_groups():
    G = []; cur = []
    for i, x in enumerate(WORDS):
        if cur:
            prev = WORDS[cur[-1]]
            if len(cur) >= 3 or x['s'] - prev['e'] > 0.28 or prev['w'][-1] in '.,?!' or x['s'] >= nearest_bound(prev['e']) - 0.001: G.append(cur); cur = []
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
ACCENT = {'GYNO': VGOLD, 'E2': VGOLD, 'ESTRADIOL': VGOLD, 'PROLACTIN': VGOLD, 'SERM': VGOLD, 'SERMS': VGOLD, 'RALOXIFENE': VGOLD, 'NOLVADEX': VGOLD,
          'BLOODWORK': VGOLD, 'MENT': VGOLD, 'TRT': VGOLD, 'SURGICAL': RED, 'ZERO': RED, 'HARD': RED, 'FIBROTIC': RED, 'CRASH': RED, '120': RED}
def captions(im, t, cap_y, size0):
    g = group_at(t)
    if not g: return
    d = ImageDraw.Draw(im, 'RGBA')
    ws = [WORDS[i]['w'].upper().rstrip(',.?!') for i in g]
    size = int(size0)
    while True:
        fn = f(BEB, size); sp = d.textlength(' ', font=fn) + 14; wd = [d.textlength(w, font=fn) for w in ws]; tot = sum(wd) + sp * (len(ws) - 1)
        if tot <= 900: break
        size -= 4
    xs = []; x = (W - tot) / 2
    for w_ in wd: xs.append(x); x += w_ + sp
    act = 0
    for k, i in enumerate(g):
        if WORDS[i]['s'] <= t: act = k
    g0 = WORDS[g[0]]['s']; s = lerp(0.9, 1, expo((t - g0) / 0.10))
    CH = int(size * 2.3)
    cap = Image.new('RGBA', (W, CH), (0, 0, 0, 0)); cd = ImageDraw.Draw(cap); shd = Image.new('RGBA', (W, CH), (0, 0, 0, 0)); sd = ImageDraw.Draw(shd)
    top = int(size * 0.31)
    prev = max(0, act - 1); bt = expo((t - WORDS[g[act]]['s']) / 0.07) if act > 0 else 1
    bx0 = lerp(xs[prev], xs[act], bt) - 18; bx1 = lerp(xs[prev] + wd[prev], xs[act] + wd[act], bt) + 18
    for k, (w_, x_) in enumerate(zip(ws, xs)):
        if k != act: sd.text((x_ + 4, top + 6), w_, font=fn, fill=(0, 0, 0, 210))
    cap.alpha_composite(shd.filter(ImageFilter.GaussianBlur(6)))
    lit_bar(cd, bx0, top + size * 0.02, bx1, top + size * 0.98, RED)
    for k, (w_, x_) in enumerate(zip(ws, xs)):
        col = CREAM if k == act else ACCENT.get(w_, CREAM)
        cd.text((x_, top), w_, font=fn, fill=col, stroke_width=0 if k == act else 3, stroke_fill=(0, 0, 0))
    if abs(s - 1) > 0.002:
        cap = cap.resize((int(W * s), int(CH * s)), Image.BICUBIC); ox = int((W - cap.width) / 2); oy = int(cap_y - top - (cap.height - CH) / 2)
    else: ox, oy = 0, int(cap_y - top)
    im.alpha_composite(cap, (ox, oy))

# ---------------- frame composition ----------------
def seg_of(t):
    for i, (b0, b1) in enumerate(BOUNDS):
        if b0 <= t < b1: return i
    return len(BOUNDS) - 1
FACE_CACHE = {}
def scene_face(sc):
    k = (sc[0], sc[1])
    if k not in FACE_CACHE:
        v = [(cx, cy) for (tt, cx, cy, sz) in FACE_N if sc[0] <= tt <= sc[1]]
        if not v: v = [(540, 930)]
        FACE_CACHE[k] = (float(np.median([a for a, b in v])), float(np.median([b for a, b in v])))
    return FACE_CACHE[k]
def scene_at(t):
    for sc in SC:
        if sc[0] <= t < sc[1] + 0.4: return sc
    return None
def layout_p(sc, t):
    return min(ease_io((t - sc[0]) / 0.4), 1 - ease_io((t - sc[1]) / 0.35))
def frame(src, t):
    global GL, BG
    STAMPS.clear()
    z = 1.0 if seg_of(t) % 2 == 0 else 1.08
    # normal transform params
    n_s = z; n_ox = (W - W * z) / 2; n_oy = -(H * z - H) * 0.35
    sc = scene_at(t)
    p = 0; L = None
    if sc and sc[2]:
        L = LAY[sc[2]]; p = layout_p(sc, t)
    cap_y, cap_size = CAP_NORMAL
    if p <= 0.001:
        if z != 1.0:
            big = src.resize((int(W * z), int(H * z)), Image.BICUBIC); ox = (big.width - W) // 2; oy = int((big.height - H) * 0.35); src = big.crop((ox, oy, ox + W, oy + H))
        im = src.convert('RGBA')
    else:
        if BG is None: BG = make_bg()
        fcx, fcy = scene_face(sc)
        s = L['s']; fx = L['fx'] if L['fx'] is not None else fcx * s
        l_ox = fx - fcx * s; l_oy = L['fy'] - fcy * s
        if L['fx'] is None: l_ox = 0
        S_ = lerp(n_s, s, p); OX = lerp(n_ox, l_ox, p); OY = lerp(n_oy, l_oy, p)
        mx0, my0, mx1, my1, mr = [lerp(a_, b_, p) for a_, b_ in zip((0, 0, W, H, 0), L['mask'])]
        im = BG.copy()
        bx0, by0, bx1, by1 = int(max(0, mx0)), int(max(0, my0)), int(min(W, mx1)), int(min(H, my1))
        bw, bh = bx1 - bx0, by1 - by0
        foot = src.transform((bw, bh), Image.AFFINE, (1 / S_, 0, (bx0 - OX) / S_, 0, 1 / S_, (by0 - OY) / S_), Image.BILINEAR)
        m = Image.new('L', (bw, bh), 0); ImageDraw.Draw(m).rounded_rectangle([mx0 - bx0, my0 - by0, mx1 - bx0 - 1, my1 - by0 - 1], radius=int(mr), fill=255)
        im.paste(foot.convert('RGBA'), (bx0, by0), m)
        cap_y = lerp(CAP_NORMAL[0], L['cap'][0], p); cap_size = lerp(CAP_NORMAL[1], L['cap'][1], p)
    glow = Image.new('RGBA', (W, H), (0, 0, 0, 0)); GL = ImageDraw.Draw(glow, 'RGBA')
    d = ImageDraw.Draw(im, 'RGBA')
    # top + bottom readability scrims on raw footage only
    if p < 1:
        scr = np.zeros(H, np.float32); yy = np.arange(H)
        scr = np.maximum(np.where(yy > 1200, np.clip((yy - 1200) / 260, 0, 1) * 110, 0), np.where(yy < 420, (1 - yy / 420) * 110, 0)) * (1 - p)
        im.alpha_composite(Image.merge('RGBA', [Image.new('L', (W, H), c) for c in NAVY] + [Image.fromarray(np.repeat(scr.astype(np.uint8)[:, None], W, 1))]))
        d = ImageDraw.Draw(im, 'RGBA')
    # window frame
    if L is not None and p > 0:
        mx0, my0, mx1, my1, mr = L['mask']
        if sc[2] == 'split':
            yy = lerp(H, my1, p)
            d.line([(0, yy), (W, yy)], fill=A(VGOLD, p), width=4); GL.line([(0, yy), (W, yy)], fill=A(VGOLD, p), width=10)
        else:
            d.rounded_rectangle([mx0 - 3, my0 - 3, mx1 + 3, my1 + 3], radius=int(mr + 3), outline=A(VGOLD, p), width=5)
            GL.rounded_rectangle([mx0 - 3, my0 - 3, mx1 + 3, my1 + 3], radius=int(mr + 3), outline=A(VGOLD, p), width=10)
            lx = {'rect': mx0 + 20, 'circ': mx1 + 6, 'circs': mx0 + 120}[sc[2]]; ly = {'rect': my1 - 34, 'circ': my1 - 40, 'circs': my1 + 14}[sc[2]]
            d.ellipse([lx, ly + 6, lx + 14, ly + 20], fill=A(RED, p if int(t * 3) % 2 == 0 else p / 3)); txt(d, lx + 22, ly, 'LIVE', f(MONOB, 22), WHITE, p)
    # top-card frames (normal-footage scenes)
    if sc and sc[2] is None and sc[3] in (s4, s6, s10):
        box = {s4: S4_BOX, s6: S6_BOX, s10: S10_BOX}[sc[3]]
        pin = expo((t - sc[0]) / 0.22); pout = clamp((t - sc[1]) / 0.18)
        if pout < 1:
            dy = lerp(-26, 0, pin) - 20 * pout; aa = pin * (1 - pout)
            x0, y0, x1, y1 = box[0], box[1] + dy, box[2], box[3] + dy
            frosted(im, (x0, y0, x1, y1), 0.82, 14); d = ImageDraw.Draw(im, 'RGBA')
            d.rectangle([x0, y0, x1, y1], outline=A(VGOLD, 0.45 * aa), width=2); brackets(d, x0, y0, x1, y1, A(VGOLD, aa), 30, 5)
            brackets(GL, x0, y0, x1, y1, A(VGOLD, aa), 30, 10)
            if sc[3] is not s10: d.rectangle([x0, y0, x0 + 6, y1], fill=A(RED, aa))
    # scene content
    if sc:
        if sc[2]: a = clamp((layout_p(sc, t) - 0.35) / 0.65)
        else:
            a = expo((t - sc[0]) / 0.22) * (1 - clamp((t - sc[1]) / 0.18))
        if a > 0:
            lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); ld = ImageDraw.Draw(lay, 'RGBA')
            if sc[2] is None and sc[3] in (s4, s6, s10):
                dyy = lerp(-26, 0, expo((t - sc[0]) / 0.22)) - 20 * clamp((t - sc[1]) / 0.18)
                sub = Image.new('RGBA', (W, H), (0, 0, 0, 0)); sd = ImageDraw.Draw(sub, 'RGBA'); sc[3](sd, t, 1.0, sub)
                lay.alpha_composite(sub, (0, int(dyy)))
            else:
                sc[3](ld, t, 1.0, lay)
            for (st, sx, sy) in STAMPS: lay.alpha_composite(st, (max(0, sx), max(0, sy)))
            if a < 1: lay.putalpha(lay.split()[3].point(lambda v: int(v * a)))
            im.alpha_composite(lay)
    GL = None
    if glow.getbbox():
        sm = glow.resize((W // 4, H // 4), Image.BILINEAR)
        g1 = np.asarray(sm.filter(ImageFilter.GaussianBlur(3.5))).astype(np.float32) / 255; g2 = np.asarray(sm.filter(ImageFilter.GaussianBlur(10))).astype(np.float32) / 255
        prem = np.clip(g1[..., :3] * g1[..., 3:] * 2.0 + g2[..., :3] * g2[..., 3:] * 1.6, 0, 1)
        prem = np.asarray(Image.fromarray((prem * 255).astype(np.uint8)).resize((W, H), Image.BILINEAR)).astype(np.float32) / 255
        b = np.asarray(im.convert('RGB')).astype(np.float32) / 255
        im = Image.fromarray(((1 - (1 - b) * (1 - prem)) * 255).astype(np.uint8)).convert('RGBA')
    d = ImageDraw.Draw(im, 'RGBA'); d.rectangle([0, 0, 7, H], fill=GOLD)
    draw_band(im, t)
    draw_hook(im, t)
    captions(im, t, cap_y, cap_size)
    return im.convert('RGB')

if __name__ == '__main__':
    mode = sys.argv[3]
    if mode == 'stills':
        import os; os.makedirs(WD + 'qc', exist_ok=True)
        for tt in [float(x) for x in sys.argv[4:]]:
            subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', f'{tt:.4f}', '-i', WD + 'assembled.mov', '-frames:v', '1', WD + 'qc/_src.png'])
            frame(Image.open(WD + 'qc/_src.png').convert('RGB'), tt).resize((540, 960), Image.LANCZOS).save(WD + f'qc/st_{tt:07.2f}.jpg', quality=88)
        sys.exit()
    n0, n1, out = int(sys.argv[3]), int(sys.argv[4]), sys.argv[5]
    dec = subprocess.Popen(['ffmpeg', '-v', 'error', '-ss', f'{n0 / FPS:.4f}', '-i', WD + 'assembled.mov', '-frames:v', str(n1 - n0), '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], stdout=subprocess.PIPE)
    enc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-crf', '14', '-preset', 'medium', '-pix_fmt', 'yuv420p', out], stdin=subprocess.PIPE)
    for n in range(n0, n1):
        buf = dec.stdout.read(W * H * 3)
        if len(buf) < W * H * 3: print('short', n); break
        enc.stdin.write(frame(Image.frombuffer('RGB', (W, H), buf), n / FPS).tobytes())
    enc.stdin.close(); enc.wait(); dec.kill(); print('done', n0, n1)
