# HGH carpal tunnel Reel — 1080x1920 30fps. Varied overlay types, footage untouched.
import json, subprocess, sys, math
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
D_ = sys.argv[1]; F = D_ + '/../fonts/'
W, H = 1080, 1920; FPS = 30
WORDS = json.load(open(D_ + '/words.json'))
TRK = json.load(open(D_ + '/track.json'))
KEEP = json.load(open(D_ + '/keep.json'))['keep']
CUTS = []; _acc = 0
for a_, b_ in KEEP[:-1]: _acc += b_ - a_; CUTS.append(round(_acc, 4))
DUR = _acc + KEEP[-1][1] - KEEP[-1][0]
GOLD = (201, 169, 110); CREAM = (244, 241, 234); NAVY = (14, 17, 23)
RED = (255, 34, 28); VGOLD = (255, 194, 26); CYAN = (0, 229, 255); GREEN = (30, 255, 110)
DEEP = (2, 3, 8); INK = (6, 8, 14); WHITE = (255, 255, 255); MUTED = (124, 124, 130); AMBER = (255, 140, 30)
MONO = 'JBMono-700.ttf'; BEB = 'BebasNeue.ttf'; DMB = 'DMSans-700.ttf'; DMR = 'DMSans-400.ttf'; BAR = 'Barlow-700.ttf'
_fc = {}
def f(n, s):
    k = (n, int(s))
    if k not in _fc: _fc[k] = ImageFont.truetype(F + n, int(s))
    return _fc[k]
def clamp(x, a=0, b=1): return max(a, min(b, x))
def expo(x): x = clamp(x); return 1 if x >= 1 else 1 - 2 ** (-10 * x)
def ease_io(x): x = clamp(x); return 4 * x ** 3 if x < .5 else 1 - (-2 * x + 2) ** 3 / 2
def lerp(a, b, t): return a + (b - a) * t
def A(c, a): return tuple(c[:3]) + (int(clamp(a) * 255),)
def ap(t, t0, dur=0.16): return expo((t - t0) / dur)
def win(t, t0, t1, i=0.18, o=0.14):  # in/out envelope
    return min(expo((t - t0) / i), 1 - clamp((t - t1) / o))
GL = None
# ---------------- primitives ----------------
def txt(d, x, y, s, font, col, a=1.0, anchor=None):
    if a > 0: d.text((x, y), s, font=font, fill=A(col, a), anchor=anchor)
def brackets(d, x0, y0, x1, y1, col, L=34, w=4):
    for (cx, cy, sx, sy) in [(x0, y0, 1, 1), (x1, y0, -1, 1), (x0, y1, 1, -1), (x1, y1, -1, -1)]:
        d.line([(cx, cy), (cx + sx * L, cy)], fill=col, width=w); d.line([(cx, cy), (cx, cy + sy * L)], fill=col, width=w)
def lit_bar(d, x0, y0, x1, y1, col, a=1.0):
    h = max(1, int(y1 - y0))
    for i in range(h):
        k = i / h; c = tuple(int(min(255, v * (1.18 - 0.36 * k) + (40 if k < 0.12 else 0))) for v in col)
        d.line([(x0, y0 + i), (x1, y0 + i)], fill=c + (int(255 * clamp(a)),))
def tag(d, x, y, label, col=RED, size=30, a=1.0, glow=True):
    if a <= 0: return x
    fn = f(MONO, size); tw = d.textlength(label, font=fn); h = size + 16
    lit_bar(d, x, y, x + tw + 24, y + h, col, a); d.text((x + 12, y + 6), label, font=fn, fill=A(WHITE if col not in (VGOLD, GREEN, CYAN) else INK, a))
    if GL and glow: GL.rectangle([x - 4, y - 4, x + tw + 28, y + h + 4], outline=A(col, a), width=8)
    return x + tw + 24
def arrow(d, x0, y0, x1, y1, col, w=5, a=1.0, L=18):
    if a <= 0: return
    d.line([(x0, y0), (x1, y1)], fill=A(col, a), width=w)
    ang = math.atan2(y1 - y0, x1 - x0)
    d.polygon([(x1, y1), (x1 - L * math.cos(ang - 0.45), y1 - L * math.sin(ang - 0.45)), (x1 - L * math.cos(ang + 0.45), y1 - L * math.sin(ang + 0.45))], fill=A(col, a))
def check(d, x, y, col, s=1.0, a=1.0):
    if a <= 0: return
    d.line([(x, y + 16 * s), (x + 10 * s, y + 28 * s), (x + 30 * s, y + 2 * s)], fill=A(col, a), width=int(6 * s))
    if GL: GL.line([(x, y + 16 * s), (x + 10 * s, y + 28 * s), (x + 30 * s, y + 2 * s)], fill=A(col, a), width=int(12 * s))
def cross(d, x, y, col, s=1.0, a=1.0):
    if a <= 0: return
    d.line([(x, y), (x + 28 * s, y + 28 * s)], fill=A(col, a), width=int(6 * s)); d.line([(x + 28 * s, y), (x, y + 28 * s)], fill=A(col, a), width=int(6 * s))
    if GL: GL.line([(x, y), (x + 28 * s, y + 28 * s)], fill=A(col, a), width=int(12 * s)); GL.line([(x + 28 * s, y), (x, y + 28 * s)], fill=A(col, a), width=int(12 * s))
def frosted(im, box, dark=0.86, blur=10):
    x0, y0, x1, y1 = [int(v) for v in box]
    x0 = max(0, x0); y0 = max(0, y0); x1 = min(W, x1); y1 = min(H, y1)
    if x1 <= x0 or y1 <= y0: return
    reg = im.crop((x0, y0, x1, y1)).convert('RGB').filter(ImageFilter.GaussianBlur(blur))
    im.paste(Image.blend(reg, Image.new('RGB', reg.size, DEEP), dark).convert('RGBA'), (x0, y0))
def card(im, box, a, col=VGOLD, head=None, head_r=None, dark=0.86):
    """Frosted evidence card: dark glass, gold brackets, mono header."""
    if a <= 0: return ImageDraw.Draw(im, 'RGBA')
    x0, y0, x1, y1 = box
    frosted(im, box, dark * a, 10)
    d = ImageDraw.Draw(im, 'RGBA')
    d.rectangle([x0, y0, x1, y1], outline=A(col, 0.45 * a), width=2); brackets(d, x0, y0, x1, y1, A(col, a), 30, 6)
    if GL: brackets(GL, x0, y0, x1, y1, A(col, a), 30, 12)
    if head: txt(d, x0 + 24, y0 + 16, head, f(MONO, 24), col, a)
    if head_r: fn = f(MONO, 24); txt(d, x1 - 24 - d.textlength(head_r, font=fn), y0 + 16, head_r, fn, MUTED, a)
    return d
def flow(d, x0, y0, x1, y1, t, col, n=5, speed=0.9, a=1.0, r=7):
    for k in range(n):
        p = (t * speed + k / n) % 1
        x = lerp(x0, x1, p); y = lerp(y0, y1, p); fa = a * min(1, p * 6, (1 - p) * 6)
        d.ellipse([x - r, y - r, x + r, y + r], fill=A(col, fa))
        if GL: GL.ellipse([x - r * 2, y - r * 2, x + r * 2, y + r * 2], fill=A(col, fa))
def drop(d, x, y, s, col, a):  # water droplet
    pts = [(x, y - 1.6 * s)] + [(x + s * math.cos(th), y + s * math.sin(th)) for th in np.linspace(-0.35, math.pi + 0.35, 14)]
    d.polygon(pts, fill=A(col, a))
def stamp(d, cx, cy, label, col, a, size=56, rot_box=True):
    if a <= 0: return
    fn = f(BEB, size); tw = d.textlength(label, font=fn)
    d.rectangle([cx - tw / 2 - 18, cy - size * 0.55, cx + tw / 2 + 18, cy + size * 0.6], outline=A(col, a), width=5)
    txt(d, cx - tw / 2, cy - size * 0.5, label, fn, col, a)
    if GL: GL.rectangle([cx - tw / 2 - 18, cy - size * 0.55, cx + tw / 2 + 18, cy + size * 0.6], outline=A(col, a), width=10)

# ---------------- designed background (for bubble / side / window layouts) ----------------
def make_bg():
    im = Image.new('RGB', (W, H), NAVY); d = ImageDraw.Draw(im)
    for x in range(0, W, 60): d.line([(x, 0), (x, H)], fill=(20, 24, 33), width=1)
    for y in range(0, H, 60): d.line([(0, y), (W, y)], fill=(20, 24, 33), width=1)
    yy, xx = np.mgrid[0:H, 0:W]
    g = np.exp(-(((xx - 980) / 700) ** 2 + ((yy - 200) / 800) ** 2))[..., None] * np.array([40, 30, 14])
    v = 1 - 0.45 * np.clip(((xx - 540) / 900) ** 2 + ((yy - 960) / 1300) ** 2, 0, 1)[..., None]
    arr = np.clip((np.asarray(im).astype(np.float32) + g) * v, 0, 255).astype(np.uint8)
    return Image.fromarray(arr)
BG = None
def head_xy(n):
    n = min(max(0, n), len(TRK['x']) - 1); return TRK['x'][n] - 20, TRK['y'][n] + 300

# ---------------- layouts ----------------
# (t_in, t_out, mode, params)
LAYOUTS = [
    (9.10, 16.50, 'bubble', dict(cx=808, cy=455, r=205)),
    (22.95, 36.50, 'side', {}),
    (46.50, 52.50, 'bubble', dict(cx=268, cy=455, r=205)),
    (67.40, 72.20, 'window', {}),
]
def layout_at(t):
    for (t0, t1, m, p) in LAYOUTS:
        if t0 <= t < t1 + 0.32:
            q = min(ease_io((t - t0) / 0.34), 1 - ease_io((t - t1) / 0.32))
            return m, p, clamp(q)
    return None, None, 0
def seg_of(t): return sum(1 for c in CUTS if c <= t + 1e-6)
def zoom_full(src, t):
    # visual hook punch on "growth" (0.82), then alternate 1.0/1.06 per jump cut
    z = 1.0
    if t < 4.5: z = lerp(1.0, 1.07, expo((t - 0.82) / 0.12)) if t >= 0.82 else 1.0
    else: z = 1.06 if seg_of(t) % 2 == 1 else 1.0
    if abs(z - 1) < 1e-3: return src
    big = src.resize((int(W * z), int(H * z)), Image.BICUBIC)
    ay = 900; ox = (big.width - W) // 2; oy = int(ay * z - ay)
    return big.crop((ox, oy, ox + W, oy + H))
def base(src, t, n):
    global BG
    if BG is None: BG = make_bg()
    m, p, q = layout_at(t)
    full = zoom_full(src, t)
    if m is None or q <= 0: return full.convert('RGBA')
    im = BG.copy().convert('RGBA')
    if m == 'bubble':
        hx, hy = head_xy(n)
        s = lerp(1.0, 0.56, q); r = lerp(1400, p['r'], q)
        cx = lerp(hx, p['cx'], q); cy = lerp(hy, p['cy'], q)
        sm = src.resize((int(W * s), int(H * s)), Image.BICUBIC)
        ox = int(cx - hx * s); oy = int(cy - hy * s)
        lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); lay.paste(sm, (ox, oy))
        mk = Image.new('L', (W * 2, H * 2), 0); ImageDraw.Draw(mk).ellipse([2 * (cx - r), 2 * (cy - r), 2 * (cx + r), 2 * (cy + r)], fill=255)
        mk = mk.resize((W, H), Image.LANCZOS)
        im.paste(lay, (0, 0), mk)
        d = ImageDraw.Draw(im, 'RGBA'); d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=A(VGOLD, q), width=5)
        if GL: GL.ellipse([cx - r, cy - r, cx + r, cy + r], outline=A(VGOLD, q), width=10)
        # rec dot + handle
        if q > 0.9: txt(d, cx - 70, cy + r + 14, '@coach.agz', f(MONO, 24), GOLD, q)
    elif m == 'side':
        s = lerp(1.0, 0.80, q); ox = int(lerp(0, 390, q)); oy = int(lerp(0, 190, q))
        sm = full.resize((int(W * s), int(H * s)), Image.BICUBIC)
        im.paste(sm, (ox, oy))
        # column scrim over the footage's left edge (wall only)
        cw_ = int(lerp(0, 500, q)); sc_ = np.clip((cw_ - np.arange(W)) / 80, 0, 1) * 235 * q
        im.alpha_composite(Image.merge('RGBA', [Image.new('L', (W, H), c) for c in NAVY] + [Image.fromarray(np.repeat(sc_[None, :].astype(np.uint8), H, 0))]))
        d = ImageDraw.Draw(im, 'RGBA'); d.line([(cw_, oy), (cw_, oy + sm.height)], fill=A(VGOLD, q), width=4)
        if GL: GL.line([(cw_, oy), (cw_, oy + sm.height)], fill=A(VGOLD, q), width=8)
    elif m == 'window':
        s = lerp(1.0, 0.62, q); hx, hy = 560, 1000
        ox = int(lerp(0, 540 - hx * 0.62, q)); oy = int(lerp(0, 640 - hy * 0.62, q))
        sm = src.resize((int(W * s), int(H * s)), Image.BICUBIC)
        lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); lay.paste(sm, (ox, oy))
        bx = (lerp(0, 210, q), lerp(0, 250, q), lerp(W, 870, q), lerp(H, 990, q))
        mk = Image.new('L', (W, H), 0); ImageDraw.Draw(mk).rounded_rectangle(bx, radius=int(lerp(0, 28, q)), fill=255)
        im.paste(lay, (0, 0), mk)
        d = ImageDraw.Draw(im, 'RGBA'); d.rounded_rectangle(bx, radius=int(lerp(0, 28, q)), outline=A(VGOLD, q), width=4)
        if GL: GL.rounded_rectangle(bx, radius=int(lerp(0, 28, q)), outline=A(VGOLD, q), width=9)
    if q < 1:  # blend from plain footage at the very start of the move (avoids a pop)
        pass
    return im

# ================= SCENES =================
# ---- A: frame-0 text hook (premium) ----
def hook(im, t):
    if t >= 4.62: return
    a = 1 - clamp((t - 4.47) / 0.15)
    s = lerp(1.0, 1.04, clamp(t / 4.47))
    lay = Image.new('RGBA', (W, 520), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    sh = Image.new('RGBA', (W, 520), (0, 0, 0, 0)); sd = ImageDraw.Draw(sh)
    l1 = 'GH CARPAL TUNNEL'; fn1 = f(BEB, 168); w1 = d.textlength(l1, font=fn1)
    l2 = 'starts in your kidneys'; fn2 = f(DMB, 70); w2 = d.textlength(l2, font=fn2)
    for (x, y, s_, fn) in [((W - w1) / 2, 60, l1, fn1), ((W - w2) / 2, 252, l2, fn2)]:
        sd.text((x + 4, y + 8), s_, font=fn, fill=(0, 0, 0, 230))
    sh = sh.filter(ImageFilter.GaussianBlur(10)); lay.alpha_composite(sh); lay.alpha_composite(sh)
    d = ImageDraw.Draw(lay)
    # kicker line
    d.line([((W - w1) / 2, 44), ((W - w1) / 2 + 70, 44)], fill=GOLD + (255,), width=5)
    d.text(((W - w1) / 2 + 84, 26), '@coach.agz', font=f(MONO, 28), fill=GOLD + (255,))
    d.text(((W - w1) / 2, 60), l1, font=fn1, fill=VGOLD + (255,), stroke_width=3, stroke_fill=(20, 12, 0))
    d.text(((W - w2) / 2, 252), l2, font=fn2, fill=WHITE + (255,), stroke_width=4, stroke_fill=(0, 0, 0))
    if s != 1: lay = lay.resize((int(W * s), int(520 * s)), Image.BICUBIC)
    lay.putalpha(lay.split()[3].point(lambda v: int(v * a)))
    im.alpha_composite(lay, (int((W - lay.width) / 2), int(250 - (lay.height - 520) / 2)))
    if GL: GL.line([((W - w1) / 2, 294), ((W - w1) / 2 + 70, 294)], fill=A(GOLD, a), width=8)

# ---- B: X-ray evidence cards (myths ruled out) ----
def xray_wrist(d, x0, y0, a, dim):
    c = tuple(int(v * (0.45 if dim else 1)) for v in CYAN)
    cx = x0 + 200
    # radius + ulna
    d.rounded_rectangle([cx - 70, y0 + 210, cx - 18, y0 + 300], radius=18, outline=A(c, a), width=4)
    d.rounded_rectangle([cx + 2, y0 + 216, cx + 46, y0 + 300], radius=16, outline=A(c, a), width=4)
    # carpals (8)
    for i, (dx, dy) in enumerate([(-60, 170), (-30, 165), (0, 165), (30, 170), (-55, 135), (-25, 128), (5, 128), (35, 135)]):
        d.ellipse([cx + dx - 14, y0 + dy - 14, cx + dx + 14, y0 + dy + 14], outline=A(c, a), width=3)
    # metacarpals
    for i, dx in enumerate([-72, -36, 0, 34, 66]):
        d.line([(cx + dx * 0.8, y0 + 112), (cx + dx * 1.15, y0 + 40)], fill=A(c, a), width=6)
    if GL and not dim: GL.rounded_rectangle([cx - 90, y0 + 30, cx + 90, y0 + 300], radius=20, outline=A(CYAN, a * 0.35), width=6)
def xray_cart(d, x0, y0, a, dim):
    c = tuple(int(v * (0.45 if dim else 1)) for v in CYAN)
    cx = x0 + 200
    d.pieslice([cx - 110, y0 + 30, cx + 110, y0 + 190], 0, 180, outline=A(c, a), width=4)   # upper bone end
    d.pieslice([cx - 110, y0 + 190, cx + 110, y0 + 350], 180, 360, outline=A(c, a), width=4)  # lower bone end
    d.arc([cx - 104, y0 + 50, cx + 104, y0 + 176], 0, 180, fill=A(VGOLD if not dim else MUTED, a), width=9)  # cartilage
    d.arc([cx - 104, y0 + 204, cx + 104, y0 + 330], 180, 360, fill=A(VGOLD if not dim else MUTED, a), width=9)
def scene_myth(im, t):
    if not (4.95 <= t < 9.25): return
    out = clamp((t - 9.0) / 0.14)
    for i, (x0, t_in, t_x, head, draw) in enumerate([(56, 5.10, 6.24, 'EXHIBIT 01 · WRIST JOINT', xray_wrist), (552, 6.86, 8.42, 'EXHIBIT 02 · CARTILAGE', xray_cart)]):
        a = ap(t, t_in, 0.2) * (1 - out)
        if a <= 0: continue
        dy = lerp(40, 0, ap(t, t_in, 0.22)) - 120 * out ** 2
        box = (x0, 252 + dy, x0 + 472, 612 + dy)
        d = card(im, box, a, CYAN, head)
        dim = t >= t_x + 0.1
        global GL
        gsave = GL; GL = None
        art = Image.new('RGBA', (400, 330), (0, 0, 0, 0)); draw(ImageDraw.Draw(art, 'RGBA'), 0, -10, 1.0, dim)
        GL = gsave
        art = art.resize((520, 429), Image.LANCZOS).crop((40, 40, 480, 360))
        if a < 1: art.putalpha(art.split()[3].point(lambda v: int(v * a)))
        im.alpha_composite(art, (int(x0 + 16), int(252 + dy + 44)))
        if GL and not dim: GL.rectangle([x0 + 120, 252 + dy + 70, x0 + 352, 252 + dy + 340], outline=A(CYAN, a * 0.35), width=6)
        d = ImageDraw.Draw(im, 'RGBA')
        # scan sweep while being examined
        if t_in + 0.2 < t < t_x:
            sy = 252 + dy + 60 + ((t - t_in) * 260) % 280
            d.line([(x0 + 10, sy), (x0 + 462, sy)], fill=A(CYAN, 0.8 * a), width=3)
            if GL: GL.line([(x0 + 10, sy), (x0 + 462, sy)], fill=A(CYAN, a), width=8)
        if t >= t_x:
            b = ap(t, t_x, 0.1) * (1 - out); s = lerp(1.5, 1.0, expo((t - t_x) / 0.1))
            cx, cy = x0 + 236, 252 + dy + 210
            L = 105 * s
            d.line([(cx - L, cy - L), (cx + L, cy + L)], fill=A(RED, b * 0.9), width=9); d.line([(cx + L, cy - L), (cx - L, cy + L)], fill=A(RED, b * 0.9), width=9)
            if GL: GL.line([(cx - L, cy - L), (cx + L, cy + L)], fill=A(RED, b), width=16); GL.line([(cx + L, cy - L), (cx - L, cy + L)], fill=A(RED, b), width=16)
            tag(d, x0 + 20, 252 + dy + 300, 'RULED OUT', RED, 28, b)

# ---- C: kidney chain (bubble layout) ----
def bean(cx, cy, s):
    pts = []
    for th in np.linspace(0, 2 * math.pi, 60):
        r = 1 - 0.32 * max(0, math.cos(th)) ** 3
        pts.append((cx + s * 0.62 * r * math.cos(th), cy + s * math.sin(th)))
    return pts
def node(d, x0, y0, x1, y1, title, col, lit, a=1.0, size=44):
    c = col if lit else (60, 66, 80)
    d.rounded_rectangle([x0, y0, x1, y1], radius=14, fill=A((10, 14, 24), 0.96 * a), outline=A(c, a), width=4)
    if GL and lit: GL.rounded_rectangle([x0, y0, x1, y1], radius=14, outline=A(col, a), width=9)
    fn = f(BEB, size); tw = d.textlength(title, font=fn)
    txt(d, (x0 + x1) / 2 - tw / 2, (y0 + y1) / 2 - size * 0.52, title, fn, WHITE if lit else (95, 100, 115), a)
def scene_kidney(im, t, q):
    if q <= 0: return
    d = ImageDraw.Draw(im, 'RGBA'); a = q
    txt(d, 64, 276, 'MECHANISM 01', f(MONO, 26), VGOLD, a)
    d.line([(64, 330), (130, 330)], fill=A(GOLD, a), width=4)
    txt(d, 64, 350, 'FLUID', f(BEB, 96), CREAM, a); txt(d, 64, 440, 'CHAIN', f(BEB, 96), VGOLD, a)
    txt(d, 64, 556, '01 / 03', f(MONO, 24), MUTED, a)
    # chain row
    xs = [56, 302, 548, 794]; names = [('GH', VGOLD, 9.16), ('KIDNEYS', CYAN, 10.20), ('SODIUM', VGOLD, 11.34), ('WATER', CYAN, 12.04)]
    for i, (nm, col, tt) in enumerate(names):
        lit = t >= tt; s = 1 + 0.08 * (1 - expo((t - tt) / 0.18)) if lit else 1
        x0 = xs[i]; w = 230
        node(d, x0, 720, x0 + w, 830, nm, col, lit, a, 50)
        if i < 3: arrow(d, x0 + w + 2, 775, xs[i + 1] - 4, 775, col if t >= names[i + 1][2] else (60, 66, 80), 4, a, 12)
    if t >= 13.50:
        b = ap(t, 13.50)
        tag(d, 56, 846, 'LINK 01 OF THE CHAIN', VGOLD, 24, b * a)
        # dashed continuation off to the right
        for k in range(6):
            x = 1030 + k * 16 - 60
            d.line([(x, 775), (x + 8, 775)], fill=A(VGOLD, b * a * (1 - k / 6)), width=4)
    # kidney + body fluid tank
    kx, ky = 300, 1150
    d.line(bean(kx, ky, 190) + [bean(kx, ky, 190)[0]], fill=A(CYAN, a * ap(t, 10.2, 0.3)), width=6)
    if GL: GL.line(bean(kx, ky, 190), fill=A(CYAN, a * ap(t, 10.2, 0.3)), width=12)
    txt(d, kx - 70, ky - 24, 'KIDNEY', f(BEB, 52), CREAM, a * ap(t, 10.2, 0.3))
    # exit pipe (urine) at bottom
    ea = a * ap(t, 10.2, 0.3)
    d.line([(kx, ky + 190), (kx, ky + 280)], fill=A((90, 96, 110), ea), width=10)
    txt(d, kx + 22, ky + 236, 'OUT', f(MONO, 24), MUTED, ea)
    closed = t >= 10.72
    if closed:
        b = ap(t, 10.72, 0.08); y = lerp(ky + 150, ky + 214, b)
        d.rectangle([kx - 48, y, kx + 48, y + 16], fill=A(RED, a));
        if GL: GL.rectangle([kx - 48, y, kx + 48, y + 16], fill=A(RED, a))
        tag(d, kx - 230, ky + 250, 'EXIT HELD', RED, 24, a * b)
    # tank
    tx0, ty0, tx1, ty1 = 640, 940, 960, 1400
    d.rounded_rectangle([tx0, ty0, tx1, ty1], radius=20, outline=A((150, 156, 170), a * ap(t, 11.3, 0.3)), width=4)
    txt(d, tx0, ty0 - 44, 'BODY FLUID', f(MONO, 26), CREAM, a * ap(t, 11.3, 0.3))
    lvl = 0.22
    if t >= 11.34: lvl = lerp(0.22, 0.42, expo((t - 11.34) / 1.2))
    if t >= 15.70: lvl = lerp(0.42, 0.80, expo((t - 15.70) / 1.0))
    yl = ty1 - 6 - (ty1 - ty0 - 12) * lvl
    wav = [(x, yl + 6 * math.sin(x / 40 + t * 5)) for x in range(tx0 + 6, tx1 - 5, 8)]
    d.polygon(wav + [(tx1 - 6, ty1 - 6), (tx0 + 6, ty1 - 6)], fill=A((0, 120, 160), 0.75 * a))
    d.line(wav, fill=A(CYAN, a), width=4)
    if GL: GL.line(wav, fill=A(CYAN, a), width=8)
    if t >= 15.76: tag(d, tx0 + 20, ty0 + 20, 'VOLUME UP', CYAN, 26, a * ap(t, 15.76))
    # Na+ particles: kidney -> tank (retained), water drops follow from 14.9
    if t >= 11.34:
        for k in range(7):
            p = ((t - 11.34) * 0.55 + k / 7) % 1
            x = lerp(kx + 90, tx0 + 40 + (k * 37) % 240, p); y = lerp(ky - 40 + k * 12, yl + 30 + (k * 23) % 120, p) - 90 * math.sin(math.pi * p)
            fa = a * min(1, p * 5, (1 - p) * 5 + 0.4)
            d.ellipse([x - 13, y - 13, x + 13, y + 13], fill=A(VGOLD, fa))
            txt(d, x - 13, y - 11, 'Na', f(MONO, 15), INK, fa)
            if GL: GL.ellipse([x - 20, y - 20, x + 20, y + 20], fill=A(VGOLD, fa * 0.7))
            if t >= 14.92:
                lag = 0.07; p2 = p - lag
                if p2 > 0:
                    x2 = lerp(kx + 90, tx0 + 40 + (k * 37) % 240, p2); y2 = lerp(ky - 40 + k * 12, yl + 30 + (k * 23) % 120, p2) - 90 * math.sin(math.pi * p2)
                    drop(d, x2, y2 + 4, 10, CYAN, fa * ap(t, 14.92, 0.3))
        if t >= 15.00: tag(d, tx0 - 10, ty1 + 14, 'WATER FOLLOWS Na', CYAN, 24, a * ap(t, 15.76))

# ---- D: ROOM TO EXPAND bar chart (top shelf over footage) ----
def scene_room(im, t):
    if not (16.72 <= t < 23.05): return
    a = win(t, 16.72, 22.85, 0.2, 0.2)
    box = (56, 252, 1024, 640)
    d = card(im, box, a, VGOLD, 'FLUID LOAD · ROOM TO EXPAND', 'ILLUSTRATIVE')
    rows = [('LOWER LEGS', 0), ('ABDOMEN', 1), ('FACE · HANDS', 2), ('CARPAL TUNNEL', 3)]
    for label, i in rows:
        y = 312 + i * 76
        ct = i == 3
        la = a * ap(t, 16.9 + i * 0.12, 0.2)
        col = (RED if t >= 22.18 else VGOLD) if ct else CREAM
        txt(d, 84, y + 6, label, f(BAR, 40), col if ct and t >= 21.42 else CREAM, la)
        tx0 = 400
        cap = 0.55 if not ct else 0.16
        if not ct and t >= 19.48: cap = lerp(0.55, 0.96 - i * 0.05, expo((t - 19.48) / 0.6))
        tx1 = lerp(tx0, 990, cap)
        d.rounded_rectangle([tx0, y + 6, tx1, y + 50], radius=10, outline=A((120, 126, 140) if not ct else (RED if t >= 22.18 else (200, 200, 210)), la), width=3)
        if ct:  # hard wall
            d.line([(tx1 + 8, y - 2), (tx1 + 8, y + 58)], fill=A(WHITE, la), width=8)
            for k in range(4): d.line([(tx1 + 12, y + k * 16), (tx1 + 26, y + k * 16 - 10)], fill=A(WHITE, la), width=3)
        fill = 0
        if t >= 17.30: fill = lerp(0, 0.5, expo((t - 17.30) / 0.7))
        if t >= 19.48 and not ct: fill = lerp(0.5, 0.92, expo((t - 19.48) / 0.8))
        if ct and t >= 21.6: fill = lerp(0.5, 1.0, expo((t - 21.6) / 0.4))
        fx = lerp(tx0 + 4, tx1 - 4, min(1, fill / (1 if ct else 1)))
        if ct: fx = lerp(tx0 + 4, tx1 - 4, min(1, fill))
        lit_bar(d, tx0 + 4, y + 10, max(tx0 + 5, fx), y + 46, (RED if (ct and t >= 22.18) else CYAN), la)
        if GL: GL.rectangle([tx0 + 4, y + 10, fx, y + 46], fill=A(RED if (ct and t >= 22.18) else CYAN, la * 0.6))
    if t >= 22.18: tag(d, 640, 540, 'NO STRETCH', RED, 32, a * ap(t, 22.18, 0.08))

# ---- E/F: side split — carpal cross-section scope, pressure curve, hand map ----
def scene_side(im, t, q):
    if q <= 0: return
    d = ImageDraw.Draw(im, 'RGBA'); a = q
    # header (handoff from the D row)
    hy = 268
    d.line([(40, hy + 16), (100, hy + 16)], fill=A(GOLD, a), width=4)
    txt(d, 112, hy, 'CROSS-SECTION', f(MONO, 24), VGOLD, a)
    txt(d, 40, hy + 36, 'CARPAL TUNNEL', f(BEB, 74), CREAM, a)
    hand_a = ap(t, 34.84, 0.25)
    sc_a = a * (1 - hand_a)
    cx, cy, R = 252, 600, 196
    if sc_a > 0:
        d.ellipse([cx - R, cy - R, cx + R, cy + R], fill=A((6, 10, 18), sc_a), outline=A(CYAN, sc_a * 0.7), width=4)
        if GL: GL.ellipse([cx - R, cy - R, cx + R, cy + R], outline=A(CYAN, sc_a * 0.5), width=8)
        # carpal bones U
        ba = sc_a * ap(t, 24.95, 0.3) if t < 25.0 else sc_a
        ba = max(ba, sc_a * ap(t, 23.6, 0.3) * 0.35)
        for k in range(8):
            th = math.pi * (0.08 + 0.84 * k / 7); bx = cx - 150 * math.cos(th); by = cy - 10 + 120 * math.sin(th)
            d.ellipse([bx - 30, by - 24, bx + 30, by + 24], fill=A((40, 50, 66), ba), outline=A(CREAM, ba), width=3)
        # transverse ligament
        la_ = sc_a * ap(t, 25.55, 0.25)
        d.rounded_rectangle([cx - 170, cy - 104, cx + 170, cy - 80], radius=12, fill=A(AMBER, la_))
        if GL: GL.rounded_rectangle([cx - 170, cy - 104, cx + 170, cy - 80], radius=12, fill=A(AMBER, la_ * 0.6))
        if t >= 25.62: txt(d, cx - 108, cy - 150, 'LIGAMENT', f(MONO, 22), AMBER, sc_a * ap(t, 25.62))
        if t >= 25.02 and t < 34.84: txt(d, cx - 46, cy + 128, 'BONE', f(MONO, 22), CREAM, sc_a * ap(t, 25.02))
        # fluid
        fl = 0
        if t >= 26.54: fl = lerp(0, 0.45, expo((t - 26.54) / 0.6))
        if t >= 29.62: fl = lerp(0.45, 0.8, expo((t - 29.62) / 0.6))
        if t >= 31.58: fl = lerp(0.8, 1.0, expo((t - 31.58) / 0.5))
        if fl > 0:
            d.ellipse([cx - 128, cy - 78, cx + 128, cy + 96], fill=A((0, 150, 200), sc_a * 0.55 * fl))
        # tendons
        for k, (dx, dy) in enumerate([(-80, 30), (-40, 52), (0, 60), (40, 52), (80, 30), (-56, -6), (-14, 10), (28, 10), (68, -6)]):
            d.ellipse([cx + dx - 17, cy + dy - 17, cx + dx + 17, cy + dy + 17], fill=A((150, 160, 178), sc_a * ap(t, 23.6, 0.3)))
        # median nerve: squashes on "compresses"
        sq = expo((t - 33.02) / 0.35) if t >= 33.02 else 0
        nh = lerp(26, 9, sq); nw = lerp(46, 70, sq); ny = cy - 52 - sq * 18
        ncol = RED if sq > 0.4 else VGOLD
        d.ellipse([cx - nw, ny - nh, cx + nw, ny + nh], fill=A(ncol, sc_a * ap(t, 23.6, 0.3)))
        if GL: GL.ellipse([cx - nw, ny - nh, cx + nw, ny + nh], fill=A(ncol, sc_a * 0.8))
        if t >= 23.6 and t < 26.54: tag(d, 34, 820, 'RIGID WALLS', VGOLD, 24, sc_a * ap(t, 23.6))
        if t >= 27.54: tag(d, 34, 820, 'ZERO ROOM', RED, 26, sc_a * ap(t, 27.54, 0.08))
        if t >= 33.86:
            b = sc_a * ap(t, 33.86)
            d.line([(cx + nw, ny), (cx + 150, 820)], fill=A(RED, b), width=3)
            tag(d, 250, 820, 'MEDIAN NERVE', RED, 24, b)
    # pressure-volume curve
    ga = a * ap(t, 28.80, 0.3)
    if ga > 0:
        gx0, gy0, gx1, gy1 = 70, 930, 470, 1290
        d.line([(gx0, gy1), (gx1, gy1)], fill=A((120, 126, 140), ga), width=3); d.line([(gx0, gy0), (gx0, gy1)], fill=A((120, 126, 140), ga), width=3)
        txt(d, gx0, gy1 + 10, 'FLUID IN TUNNEL →', f(MONO, 20), MUTED, ga)
        txt(d, gx0 + 8, gy0 - 34, 'PRESSURE ON NERVE', f(MONO, 20), MUTED, ga)
        def curve(u): return gy1 - 6 - (gy1 - gy0 - 20) * (0.06 * u + 0.94 * u ** 6)
        dp = clamp((t - 28.80) / 0.7)
        pts = [(lerp(gx0 + 6, gx1 - 10, u), curve(u)) for u in np.linspace(0, dp, 40)]
        if len(pts) > 1:
            d.line(pts, fill=A(CYAN, ga), width=6)
            if GL: GL.line(pts, fill=A(CYAN, ga), width=12)
        u = 0.25
        if t >= 29.62: u = lerp(0.25, 0.55, expo((t - 29.62) / 0.6))
        if t >= 31.58: u = lerp(0.55, 0.78, expo((t - 31.58) / 0.5))
        if t >= 33.02: u = lerp(0.78, 0.97, expo((t - 33.02) / 0.4))
        px, py = lerp(gx0 + 6, gx1 - 10, u), curve(u)
        mc = RED if u > 0.8 else VGOLD
        d.ellipse([px - 13, py - 13, px + 13, py + 13], fill=A(mc, ga));
        if GL: GL.ellipse([px - 22, py - 22, px + 22, py + 22], fill=A(mc, ga))
        if t >= 31.08:  # small extra volume -> big pressure jump
            b = ga * ap(t, 31.08, 0.25)
            ua, ub = 0.80, 0.97; xa, xb = lerp(gx0 + 6, gx1 - 10, ua), lerp(gx0 + 6, gx1 - 10, ub)
            d.line([(xa, gy1 + 44), (xb, gy1 + 44)], fill=A(CYAN, b), width=4)
            txt(d, xa - 60, gy1 + 52, 'SMALL +', f(MONO, 20), CYAN, b)
            ya, yb = curve(ua), curve(ub)
            d.line([(gx1 + 14, ya), (gx1 + 14, yb)], fill=A(RED, b), width=6)
            if GL: GL.line([(gx1 + 14, ya), (gx1 + 14, yb)], fill=A(RED, b), width=10)
            txt(d, gx1 - 90, yb - 34, 'BIG', f(BEB, 40), RED, b); arrow(d, gx1 - 30, yb - 2, gx1 - 30, yb - 34, RED, 5, b, 14)
    # F: hand map (median nerve territory) on "tingling"
    if hand_a > 0:
        ha = a * hand_a; hx, hy0 = 250, 600
        hot = ap(t, 35.34, 0.12); pul = 0.5 + 0.5 * math.sin(t * 18)
        # palm
        d.rounded_rectangle([hx - 110, hy0, hx + 110, hy0 + 210], radius=50, outline=A(CREAM, ha), width=4)
        d.rounded_rectangle([hx - 50, hy0 + 205, hx + 50, hy0 + 270], radius=10, outline=A(CREAM, ha), width=4)
        fings = [(-100, -150, 1), (-46, -190, 2), (10, -175, 3), (66, -130, 4)]
        for dx, top, k in fings:
            box = [hx + dx - 2, hy0 + top, hx + dx + 42, hy0 + 20]
            on = k <= 2
            if on: d.rounded_rectangle(box, radius=22, fill=A(RED, ha * hot * (0.35 + 0.4 * pul)))
            elif k == 3: d.rounded_rectangle([box[0], box[1], (box[0] + box[2]) / 2, box[3]], radius=10, fill=A(RED, ha * hot * 0.35))
            d.rounded_rectangle(box, radius=22, outline=A(CREAM, ha), width=4)
        thumb = [(hx - 108, hy0 + 140), (hx - 196, hy0 + 40), (hx - 168, hy0 + 14), (hx - 96, hy0 + 76)]
        d.polygon(thumb, fill=A(RED, ha * hot * (0.35 + 0.4 * pul)), outline=A(CREAM, ha))
        d.line(thumb + [thumb[0]], fill=A(CREAM, ha), width=4)
        d.polygon([(hx - 104, hy0 + 30), (hx + 30, hy0 + 30), (hx + 30, hy0 + 200), (hx - 104, hy0 + 200)], fill=A(RED, ha * hot * 0.22))
        # nerve line from wrist up the middle, with zap ticks
        d.line([(hx - 20, hy0 + 270), (hx - 20, hy0 + 40)], fill=A(VGOLD, ha), width=5)
        if GL: GL.line([(hx - 20, hy0 + 270), (hx - 20, hy0 + 40)], fill=A(VGOLD, ha), width=10)
        if hot > 0:
            rng_ = np.random.default_rng(int(t * 15))
            for _ in range(6):
                zx = hx - 150 + rng_.random() * 190; zy = hy0 - 160 + rng_.random() * 300
                d.line([(zx, zy), (zx + 10, zy - 12), (zx + 4, zy - 16), (zx + 16, zy - 30)], fill=A(VGOLD, ha * hot), width=3)
                if GL: GL.line([(zx, zy), (zx + 16, zy - 30)], fill=A(VGOLD, ha * hot), width=6)
            tag(d, 34, 880, 'TINGLING ZONE', RED, 26, ha * ap(t, 35.34, 0.08))

# ---- G: RAAS control system + fluid-balance gauge (top shelf) ----
def scene_raas(im, t):
    if not (37.20 <= t < 46.62): return
    a = win(t, 37.20, 46.45, 0.2, 0.16)
    box = (56, 252, 1024, 652)
    d = card(im, box, a, CYAN, 'GH → RAAS · FLUID CONTROL', 'SYSTEM')
    # row 1: GH chip -> three hormone nodes
    ga = a * ap(t, 37.32)
    d.rounded_rectangle([84, 304, 184, 372], radius=12, fill=A(VGOLD, ga)); txt(d, 102, 306, 'GH', f(BEB, 66), INK, ga)
    if GL: GL.rounded_rectangle([80, 300, 188, 376], radius=14, outline=A(VGOLD, ga), width=10)
    if t >= 37.78:
        p = expo((t - 37.78) / 0.25); arrow(d, 190, 338, lerp(190, 222, p), 338, VGOLD, 5, a)
    for i, (nm, tt) in enumerate([('RENIN', 38.94), ('ANGIOTENSIN', 39.40), ('ALDOSTERONE', 40.14)]):
        xs = [232, 462, 734][i]; xe = [432, 704, 1000][i]
        lit = t >= tt
        node(d, xs, 304, xe, 372, nm, CYAN, lit, a * (0.4 + 0.6 * ap(t, 38.6, 0.3)), 40)
        if i < 2: arrow(d, xe + 2, 338, [462, 734][i] - 4, 338, CYAN if t >= [39.40, 40.14][i] else (60, 66, 80), 4, a, 10)
    if t >= 40.84:
        b = a * ap(t, 40.84, 0.12); brackets(d, 224, 296, 1008, 380, A(CYAN, b), 22, 5)
        tag(d, 830, 388, 'RAAS', CYAN, 24, b)
    # row 2: gauge (DUMP <-> HOLD) and kidney excretion line
    ga2 = a * ap(t, 41.58, 0.3)
    if ga2 > 0:
        gx, gy, gr = 270, 620, 160
        segs = [(180, 228, (60, 140, 220)), (228, 312, GREEN), (312, 360, RED)]
        for (s0, s1, c) in segs:
            d.arc([gx - gr, gy - gr, gx + gr, gy + gr], s0, s1, fill=A(c, ga2), width=22)
        if GL: GL.arc([gx - gr, gy - gr, gx + gr, gy + gr], 312, 360, fill=A(RED, ga2), width=26)
        txt(d, gx - gr - 6, gy - 34, 'DUMP', f(MONO, 22), (110, 170, 230), ga2)
        txt(d, gx + gr - 56, gy - 34, 'HOLD', f(MONO, 22), RED, ga2)
        txt(d, gx - 96, gy - 236 + 30, 'FLUID BALANCE', f(MONO, 22), CREAM, ga2)
        ang = 270
        if t >= 45.00: ang = lerp(270, 338, expo((t - 45.00) / 0.35))
        rad = math.radians(ang)
        d.line([(gx, gy), (gx + (gr - 30) * math.cos(rad), gy + (gr - 30) * math.sin(rad))], fill=A(WHITE, ga2), width=7)
        d.ellipse([gx - 14, gy - 14, gx + 14, gy + 14], fill=A(WHITE, ga2))
        # right: Na+ excretion route
        kx = 520
        txt(d, kx, 452, 'KIDNEY · SODIUM', f(MONO, 24), CREAM, ga2)
        d.rounded_rectangle([kx, 494, kx + 200, 560], radius=12, outline=A(CYAN, ga2), width=3); txt(d, kx + 36, 500, 'RETAIN', f(BEB, 48), WHITE if t >= 45.18 else MUTED, ga2)
        d.rounded_rectangle([kx + 240, 494, kx + 460, 560], radius=12, outline=A((90, 96, 110), ga2), width=3); txt(d, kx + 270, 500, 'EXCRETE', f(BEB, 48), MUTED, ga2)
        if t >= 45.18:
            b = ga2 * ap(t, 45.18, 0.1); check(d, kx + 160, 510, GREEN, 1.0, b)
            if GL: GL.rounded_rectangle([kx, 494, kx + 200, 560], radius=12, outline=A(CYAN, b), width=8)
        if t >= 46.02: cross(d, kx + 410, 512, RED, 1.1, ga2 * ap(t, 46.02, 0.1))

# ---- H: cascade column chart (bubble top-left) ----
def scene_cascade(im, t, q):
    if q <= 0: return
    d = ImageDraw.Draw(im, 'RGBA'); a = q
    txt(d, 520, 276, 'MECHANISM 02', f(MONO, 26), VGOLD, a)
    d.line([(520, 330), (586, 330)], fill=A(GOLD, a), width=4)
    txt(d, 520, 350, 'THE', f(BEB, 96), CREAM, a); txt(d, 520, 440, 'CASCADE', f(BEB, 96), VGOLD, a)
    txt(d, 520, 556, '02 / 03', f(MONO, 24), MUTED, a)
    x0, y0, x1, y1 = 70, 760, 1010, 1400
    d.line([(x0, y1), (x1, y1)], fill=A((120, 126, 140), a), width=3)
    lim = y1 - 470
    for k in range(0, 940, 26): d.line([(x0 + k, lim), (x0 + k + 13, lim)], fill=A(WHITE, a * 0.8), width=3)
    txt(d, x0, lim - 36, "TUNNEL'S LIMIT", f(MONO, 22), CREAM, a)
    cols = [('SODIUM', 46.78, 0.30, VGOLD), ('WATER', 47.80, 0.48, CYAN), ('PRESSURE', 49.34, 0.70, AMBER), ('CARPAL', 50.90, 1.12, RED)]
    cw = 190; gap = (x1 - x0 - 4 * cw) / 5
    prev = None
    for i, (nm, tt, hgt, col) in enumerate(cols):
        bx0 = x0 + gap + i * (cw + gap); bx1 = bx0 + cw
        hh = 0
        if t >= tt: hh = hgt * expo((t - tt) / (0.45 if i < 3 else 0.3))
        top = y1 - 3 - 420 * hh
        if hh > 0:
            lit_bar(d, bx0, top, bx1, y1 - 3, col, a)
            if GL: GL.rectangle([bx0, top, bx1, y1 - 3], outline=A(col, a), width=8)
            txt(d, bx0 + 10, y1 + 10, nm, f(BEB, 50), col, a)
            arrow(d, bx0 + cw / 2, top - 12, bx0 + cw / 2, top - 52, WHITE, 6, a, 16)
            if prev: arrow(d, prev[0] + 6, prev[1] - 20, bx0 - 8, top + 20, (200, 204, 214), 4, a * 0.8, 12)
            prev = (bx1, top)
    if t >= 50.90:
        b = a * ap(t, 50.90, 0.08); fl = 1 if int((t - 50.9) * 12) % 2 == 0 and t < 51.3 else 0.75
        bx0 = x0 + gap + 3 * (cw + gap)
        tag(d, bx0 - 120, lim - 104, 'OVER LIMIT', RED, 30, b * fl)
    if t >= 52.02: tag(d, x0 + gap + 3 * (cw + gap) - 30, y1 + 70, 'TUNNEL', RED, 26, a * ap(t, 52.02))

# ---- I: chapter card "THE FIX" ----
def scene_fix(im, t):
    if not (52.82 <= t < 54.45): return
    a = 1 - clamp((t - 54.22) / 0.2)
    d = ImageDraw.Draw(im, 'RGBA')
    p = expo((t - 52.82) / 0.3)
    frosted(im, (8, 250, lerp(8, W, p), 610), 0.88 * a, 10); d = ImageDraw.Draw(im, 'RGBA')
    d.line([(8, 250), (lerp(8, W, p), 250)], fill=A(VGOLD, a), width=6)
    if GL: GL.line([(8, 250), (lerp(8, W, p), 250)], fill=A(VGOLD, a), width=12)
    if t >= 53.0:
        b = a * ap(t, 53.0); txt(d, 64, 282, '—— PART 02', f(MONO, 30), VGOLD, b)
    if t >= 53.32:
        s = lerp(1.25, 1.0, expo((t - 53.32) / 0.14)); b = a * ap(t, 53.32, 0.1)
        fn = f(BEB, int(220 * s)); txt(d, 60, 330 - (s - 1) * 100, 'THE', fn, CREAM, b)
        tw = d.textlength('THE ', font=fn)
        fixc = VGOLD if t >= 53.84 else CREAM
        txt(d, 60 + tw, 330 - (s - 1) * 100, 'FIX', fn, fixc, b)
        if GL and t >= 53.84: GL.text((60 + tw, 330), 'FIX', font=fn, fill=A(VGOLD, b * 0.8))

# ---- J + K: symptom clock -> verdict + levers (top shelf) ----
def scene_clock(im, t):
    if not (54.30 <= t < 67.55): return
    a = win(t, 54.30, 67.35, 0.18, 0.18)
    box = (56, 252, 1024, 652)
    sw = ap(t, 61.70, 0.3)  # swap to verdict
    d = card(im, box, a, VGOLD if sw < 0.5 else GREEN, 'SYMPTOM LOG' if sw < 0.5 else 'VERDICT', 'NIGHT · DAY' if sw < 0.5 else 'RESPONDS TO')
    ja = a * (1 - sw)
    if ja > 0:
        cx, cy, r = 250, 470, 150
        # 24h dial: night half (top=midnight) dark, day half lighter
        d.pieslice([cx - r, cy - r, cx + r, cy + r], 180, 360, fill=A((14, 18, 40), ja))
        d.pieslice([cx - r, cy - r, cx + r, cy + r], 0, 180, fill=A((60, 52, 30), ja))
        d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=A(CREAM, ja), width=3)
        for k in range(24):
            th = math.radians(k * 15 - 90); L = 16 if k % 6 == 0 else 8
            d.line([(cx + (r - L) * math.cos(th), cy + (r - L) * math.sin(th)), (cx + r * math.cos(th), cy + r * math.sin(th))], fill=A(CREAM, ja), width=3)
        txt(d, cx - 18, cy - r + 22, '00', f(MONO, 22), CREAM, ja); txt(d, cx - 18, cy + r - 46, '12', f(MONO, 22), CREAM, ja)
        # moon & sun glyphs
        d.ellipse([cx - 30, cy - 80, cx + 10, cy - 40], fill=A(CREAM, ja)); d.ellipse([cx - 18, cy - 86, cx + 22, cy - 46], fill=A((14, 18, 40), ja))
        d.ellipse([cx - 16, cy + 34, cx + 16, cy + 66], fill=A(VGOLD, ja))
        if t >= 57.54:  # numb events: night arc
            pul = 0.55 + 0.45 * math.sin(t * 12)
            b = ja * ap(t, 57.54, 0.15)
            d.arc([cx - r + 14, cy - r + 14, cx + r - 14, cy + r - 14], 165, 275, fill=A(RED, b * pul), width=18)
            if GL: GL.arc([cx - r + 14, cy - r + 14, cx + r - 14, cy + r - 14], 165, 275, fill=A(RED, b), width=24)
        if t >= 59.96:
            b = ja * ap(t, 59.96, 0.15)
            d.arc([cx - r + 14, cy - r + 14, cx + r - 14, cy + r - 14], 20, 120, fill=A(AMBER, b * 0.8), width=12)
        rows = [('ON GH', 'YES', VGOLD, 56.06), ('HANDS', 'NUMB', RED, 57.54), ('WHEN', 'NIGHT · ASLEEP', RED, 58.30), ('ALSO', 'DAYTIME', AMBER, 59.96)]
        for i, (k_, v_, c_, tt) in enumerate(rows):
            if t >= tt:
                b = ja * ap(t, tt, 0.12); y = 312 + i * 66
                txt(d, 450, y, k_, f(MONO, 26), MUTED, b)
                tag(d, 590, y - 6, v_, c_, 26, b)
                d.line([(450, y + 50), (1000, y + 50)], fill=A((50, 54, 66), b), width=1)
        if t >= 61.28:
            b = ja * ap(t, 61.28, 0.12); txt(d, 450, 584, 'CAUSE → FLUID PRESSURE', f(MONO, 24), CYAN, b)
    ka = a * sw
    if ka > 0:
        # verdict bars
        y = 320
        d.rounded_rectangle([84, y, 600, y + 96], radius=10, fill=A((26, 10, 14), ka), outline=A(RED, ka), width=3)
        txt(d, 108, y + 18, 'PERMANENT DAMAGE', f(BEB, 62), (150, 150, 158), ka)
        sp = expo((t - 62.28) / 0.25) if t >= 62.28 else 0
        if sp > 0:
            d.line([(100, y + 50), (lerp(100, 584, sp), y + 50)], fill=A(RED, ka), width=8)
            if GL: GL.line([(100, y + 50), (lerp(100, 584, sp), y + 50)], fill=A(RED, ka), width=14)
        y2 = 440
        pa = ka * ap(t, 63.58, 0.12)
        d.rounded_rectangle([84, y2, 600, y2 + 96], radius=10, fill=A((8, 30, 18), pa), outline=A(GREEN, pa), width=3)
        txt(d, 108, y2 + 18, 'PRESSURE', f(BEB, 62), WHITE, pa); check(d, 520, y2 + 30, GREEN, 1.3, pa)
        txt(d, 108, y2 + 108, 'REVERSIBLE', f(MONO, 22), GREEN, pa)
        # levers
        for i, (nm, tt) in enumerate([('DOSE', 65.22), ('SODIUM', 66.50)]):
            lx = 650; ly = 330 + i * 140
            txt(d, lx, ly, nm, f(BEB, 56), CREAM, ka)
            on = expo((t - tt) / 0.14) if t >= tt else 0
            tx0 = lx + 190; d.rounded_rectangle([tx0, ly + 4, tx0 + 140, ly + 66], radius=31, fill=A(lerp_c((50, 54, 66), VGOLD, on), ka))
            kx = lerp(tx0 + 32, tx0 + 108, on); d.ellipse([kx - 26, ly + 9, kx + 26, ly + 61], fill=A(WHITE, ka))
            if GL and on > 0: GL.rounded_rectangle([tx0, ly + 4, tx0 + 140, ly + 66], radius=31, outline=A(VGOLD, ka * on), width=10)
            txt(d, lx, ly + 76, 'ADJUST' if i == 0 else 'MANAGE', f(MONO, 22), VGOLD if on > 0.5 else MUTED, ka)
def lerp_c(c1, c2, p): return tuple(int(lerp(a_, b_, p)) for a_, b_ in zip(c1, c2))

# ---- L: dose-over-time line graph (window layout) ----
def scene_dose(im, t, q):
    if q <= 0: return
    d = ImageDraw.Draw(im, 'RGBA'); a = q
    box = (56, 1020, 1024, 1452)
    d.rounded_rectangle(box, radius=18, fill=A((8, 11, 18), 0.96 * a), outline=A((60, 64, 80), a), width=2)
    brackets(d, *box, A(VGOLD, a), 30, 6)
    txt(d, 84, 1040, 'GH DOSE vs FLUID · PROTOCOL', f(MONO, 24), VGOLD, a)
    txt(d, 800, 1040, 'ILLUSTRATIVE', f(MONO, 20), MUTED, a)
    gx0, gy0, gx1, gy1 = 100, 1100, 990, 1390
    d.line([(gx0, gy1), (gx1, gy1)], fill=A((110, 116, 130), a), width=2); d.line([(gx0, gy0), (gx0, gy1)], fill=A((110, 116, 130), a), width=2)
    txt(d, gx1 - 110, gy1 + 8, 'TIME →', f(MONO, 20), MUTED, a)
    thr = gy0 + 70
    for k in range(gx0, gx1, 24): d.line([(k, thr), (k + 12, thr)], fill=A(RED, a * 0.8), width=3)
    txt(d, gx0 + 420, thr - 30, 'SYMPTOM LINE', f(MONO, 20), RED, a)
    # dose path (gold): high -> drop -> flat -> slow steps up
    X = lambda u: lerp(gx0, gx1, u)
    dose = [(0, 0.80), (0.14, 0.80), (0.18, 0.35), (0.50, 0.35), (0.56, 0.35), (0.56, 0.45), (0.68, 0.45), (0.68, 0.55), (0.80, 0.55), (0.80, 0.64), (1.0, 0.64)]
    fluid = [(0, 0.86), (0.14, 0.88), (0.30, 0.42), (0.50, 0.36), (0.60, 0.42), (0.72, 0.50), (0.84, 0.56), (1.0, 0.60)]
    Y = lambda v: gy1 - (gy1 - gy0) * v
    prog = 0.14
    if t >= 67.62: prog = lerp(0.14, 0.30, expo((t - 67.62) / 0.5))
    if t >= 68.80: prog = lerp(0.30, 0.54, expo((t - 68.80) / 0.7))
    if t >= 70.40: prog = lerp(0.54, 1.0, clamp((t - 70.40) / 1.3))
    def path(pts, u):
        out = [];
        for (u0, v0), (u1, v1) in zip(pts, pts[1:]):
            if u0 > u: break
            e = min(u, u1); k = 0 if u1 == u0 else (e - u0) / (u1 - u0)
            if not out: out.append((X(u0), Y(v0)))
            out.append((X(lerp(u0, u1, k)), Y(lerp(v0, v1, k))))
        return out
    fp = path(fluid, prog)
    if len(fp) > 1:
        for i in range(0, len(fp) - 1):
            d.line([fp[i], fp[i + 1]], fill=A(CYAN, a * 0.9), width=5)
        if GL: GL.line(fp, fill=A(CYAN, a * 0.7), width=10)
    dp = path(dose, prog)
    if len(dp) > 1:
        d.line(dp, fill=A(VGOLD, a), width=7, joint='curve')
        if GL: GL.line(dp, fill=A(VGOLD, a), width=13)
        d.ellipse([dp[-1][0] - 11, dp[-1][1] - 11, dp[-1][0] + 11, dp[-1][1] + 11], fill=A(WHITE, a))
    txt(d, 120, 1104 + 0, '— DOSE', f(MONO, 22), VGOLD, a); txt(d, 270, 1104, '— FLUID', f(MONO, 22), CYAN, a)
    if t >= 67.62: tag(d, X(0.16), Y(0.35) + 20, 'DROP', VGOLD, 24, a * ap(t, 67.62))
    if t >= 69.08: tag(d, X(0.33), Y(0.35) + 20, 'STABILIZE', CYAN, 24, a * ap(t, 69.08))
    if t >= 70.52: tag(d, X(0.60), Y(0.45) + 34, 'SLOW STEPS', VGOLD, 24, a * ap(t, 70.52))
    if t >= 71.46: b = a * ap(t, 71.46); check(d, X(0.88), Y(0.6) + 24, GREEN, 1.0, b)

# ---- M: CTA — framework document, then COMMENT "PANEL" ----
DOC = None; LOGO = None
def make_doc():
    im = Image.new('RGBA', (600, 330), (246, 244, 238, 255)); d = ImageDraw.Draw(im)
    d.rectangle([0, 0, 600, 74], fill=(14, 17, 23)); d.rectangle([0, 0, 8, 330], fill=GOLD)
    d.text((26, 10), 'HGH WATER RETENTION', font=f(BEB, 40), fill=CREAM); d.text((26, 46), 'FRAMEWORK · @coach.agz', font=f(MONO, 18), fill=GOLD)
    for i, s in enumerate(['01  PROTOCOL', '02  DOSE ADJUSTMENT', '03  SODIUM MANAGEMENT']):
        y = 100 + i * 70
        d.text((30, y), s, font=f(BAR, 38), fill=(30, 32, 40)); d.line([(30, y + 54), (570, y + 54)], fill=(215, 212, 205), width=2)
    return im.resize((540, 297), Image.LANCZOS)
def scene_cta(im, t):
    global DOC, LOGO
    if t < 73.40: return
    if DOC is None: DOC = make_doc()
    up = ap(t, 80.40, 0.3)  # doc leaves when COMMENT lands
    a = ap(t, 73.40, 0.25) * (1 - up)
    if a > 0:
        frosted(im, (56, 252, 1024, 640), 0.80 * a, 10); d = ImageDraw.Draw(im, 'RGBA')
        brackets(d, 56, 252, 1024, 640, A(VGOLD, a), 30, 6)
        txt(d, 80, 268, 'FREE · FULL FRAMEWORK', f(MONO, 24), VGOLD, a)
        # back pages
        for k in (2, 1):
            pg = Image.new('RGBA', (540, 297), (200, 198, 192, int(255 * a))); im.alpha_composite(pg, (420 + k * 14, 320 - k * 12 + int(lerp(40, 0, ap(t, 73.6, 0.3)))))
        dp = DOC.copy(); dp.putalpha(int(255 * a)) if False else None
        dd = DOC.copy(); al = dd.split()[3].point(lambda v: int(v * a)); dd.putalpha(al)
        oy = int(lerp(60, 0, ap(t, 74.64, 0.3)))
        im.alpha_composite(dd, (420, 320 + oy)); d = ImageDraw.Draw(im, 'RGBA')
        hi = [(75.38, 0), (65 + 999, 1)]
        if t >= 75.38:
            b = a * ap(t, 75.38, 0.12); d.rectangle([424, 404 + oy, 956, 454 + oy], outline=A(RED, b), width=4)
            if GL: GL.rectangle([424, 404 + oy, 956, 454 + oy], outline=A(RED, b), width=8)
        if t >= 77.12: check(d, 900, 470 + oy + 8, (20, 160, 70), 1.0, a * ap(t, 77.12))
        # icon column left
        txt(d, 84, 330, 'GH', f(BEB, 90), VGOLD, a); txt(d, 84, 420, 'WATER', f(BEB, 56), CYAN, a); txt(d, 84, 476, 'PLAN', f(BEB, 56), CREAM, a)
    if t >= 80.40:
        b = ap(t, 80.40, 0.14); s = lerp(1.18, 1.0, expo((t - 80.40) / 0.14))
        frosted(im, (56, 252, 1024, 640), 0.84 * b, 12); d = ImageDraw.Draw(im, 'RGBA')
        brackets(d, 56, 252, 1024, 640, A(VGOLD, b), 30, 6)
        if LOGO is None:
            lg = Image.open(D_ + '/../logo.jpg').convert('RGB'); sq = min(lg.size)
            lg = lg.crop(((lg.width - sq) // 2, (lg.height - sq) // 2, (lg.width + sq) // 2, (lg.height + sq) // 2)).resize((150, 150), Image.LANCZOS)
            m = Image.new('L', (150, 150), 0); ImageDraw.Draw(m).ellipse([0, 0, 149, 149], fill=255); lg.putalpha(m); LOGO = lg
        lg = LOGO.copy(); lg.putalpha(lg.split()[3].point(lambda v: int(v * b))); im.alpha_composite(lg, (84, 286)); d = ImageDraw.Draw(im, 'RGBA')
        txt(d, 258, 300, 'COACH AGZ', f(BEB, 58), GOLD, b); txt(d, 258, 360, '@coach.agz', f(MONO, 26), GOLD, b)
        fn = f(BEB, int(118 * s)); label = 'COMMENT "PANEL"'; tw = d.textlength(label, font=fn)
        x0 = (W - tw) / 2 - 30; y0 = 456
        lit_bar(d, x0, y0, x0 + tw + 60, y0 + int(124 * s), VGOLD, b); d.text((x0 + 30, y0 + 6), label, font=fn, fill=A(INK, b))
        if GL: GL.rectangle([x0 - 4, y0 - 4, x0 + tw + 64, y0 + int(124 * s) + 4], outline=A(VGOLD, b), width=14)
        if t >= 81.54:
            bb = ap(t, 81.54); yy = 600 + 10 * math.sin(t * 7)
            arrow(d, W / 2, 596, W / 2, yy + 34, VGOLD, 6, bb, 18)
        txt(d, 600, 312, 'FREE FRAMEWORK', f(MONO, 22), CREAM, b)
        txt(d, 600, 344, 'SENT TO YOUR DMs', f(MONO, 22), CREAM, b)
        txt(d, 300, 610, 'FOR RESEARCH & EDUCATIONAL PURPOSES ONLY', f(MONO, 16), MUTED, b) if False else None
    if t >= 80.40:
        d = ImageDraw.Draw(im, 'RGBA'); fn = f(MONO, 17); s_ = 'FOR RESEARCH & EDUCATIONAL PURPOSES ONLY'
        txt(d, (W - d.textlength(s_, font=fn)) / 2, 1660, s_, fn, (200, 200, 205), 0.85 * ap(t, 80.4))

# ---------------- captions ----------------
FIX = {'renin': 'RENIN', '-ingiotensin': 'ANGIOTENSIN', '-aldosterone': 'ALDOSTERONE', 'ag,': 'AGZ', 'ag': 'AGZ', 'gh': 'GH', 'hgh': 'HGH'}
ACCENT_G = {'KIDNEYS', 'SODIUM', 'WATER', 'GH', 'HGH', 'GROWTH', 'HORMONE', 'DOSE', 'PANEL', 'FRAMEWORK', 'PROTOCOL', 'STABILIZE', 'SLOWLY'}
ACCENT_R = {'CARPAL', 'TUNNEL', 'NERVE', 'MEDIAN', 'ZERO', 'PRESSURE', 'NUMB', 'TINGLING', 'COMPRESSES', 'CANNOT'}
def wtxt(i):
    w = WORDS[i]['w']; k = w.lower()
    if k in FIX: return FIX[k]
    return w.upper().strip('.,?!')
def build_groups():
    G = []; cur = []
    for i, x in enumerate(WORDS):
        if cur:
            prev = WORDS[cur[-1]]
            long_ = sum(len(wtxt(j)) for j in cur) + len(wtxt(i)) > 16
            if len(cur) >= 3 or long_ or x['s'] - prev['e'] > 0.28 or prev['w'][-1] in '.,?!' or any(prev['e'] <= c < x['s'] + 0.01 for c in CUTS): G.append(cur); cur = []
        cur.append(i)
    if cur: G.append(cur)
    return G
GROUPS = None
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
    m, p, q = layout_at(t)
    return 1470
def captions(im, t):
    g = group_at(t)
    if not g: return
    d = ImageDraw.Draw(im, 'RGBA')
    ws = [wtxt(i) for i in g]
    size = 112
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
    CY = cap_y(t)
    cap = Image.new('RGBA', (W, 260), (0, 0, 0, 0)); cd = ImageDraw.Draw(cap); shd = Image.new('RGBA', (W, 260), (0, 0, 0, 0)); sd = ImageDraw.Draw(shd)
    prev = max(0, act - 1); bt = expo((t - WORDS[g[act]]['s']) / 0.07) if act > 0 else 1
    bx0 = lerp(xs[prev], xs[act], bt) - 18; bx1 = lerp(xs[prev] + wd[prev], xs[act] + wd[act], bt) + 18
    for k, (w_, x_) in enumerate(zip(ws, xs)): sd.text((x_ + 4, 46), w_, font=fn, fill=(0, 0, 0, 220))
    cap.alpha_composite(shd.filter(ImageFilter.GaussianBlur(7)))
    lit_bar(cd, bx0, 40 + size * 0.02, bx1, 40 + size * 0.98, RED)
    for k, (w_, x_) in enumerate(zip(ws, xs)):
        col = CREAM
        if k != act and WORDS[g[k]]['s'] <= t:
            if w_ in ACCENT_G: col = VGOLD
            elif w_ in ACCENT_R: col = (255, 90, 80)
        cd.text((x_, 40), w_, font=fn, fill=col, stroke_width=0 if k == act else 3, stroke_fill=(0, 0, 0))
    if abs(s - 1) > 0.002:
        cap = cap.resize((int(W * s), int(260 * s)), Image.BICUBIC); ox = int((W - cap.width) / 2); oy = int(CY - 40 - (cap.height - 260) / 2)
    else: ox, oy = 0, CY - 40
    im.alpha_composite(cap, (ox, oy))

# ---------------- frame ----------------
def frame(src, t, n):
    global GL
    glow = Image.new('RGBA', (W, H), (0, 0, 0, 0)); GL = ImageDraw.Draw(glow, 'RGBA')
    im = base(src, t, n)
    m, p, q = layout_at(t)
    # subtle top/bottom scrim on plain-footage moments only (for caption/card legibility)
    if m is None or q < 1:
        yy = np.arange(H); al = np.where(yy > 1380, np.clip((yy - 1380) / 300, 0, 1) * 120, 0)
        sc = (al * (1 - q)).astype(np.uint8)
        im.alpha_composite(Image.merge('RGBA', [Image.new('L', (W, H), c) for c in NAVY] + [Image.fromarray(np.repeat(sc[:, None], W, 1))]))
    gq = clamp((q - 0.5) / 0.5) ** 1.5
    if m == 'bubble' and p['cx'] > 540: scene_kidney(im, t, gq)
    if m == 'bubble' and p['cx'] < 540: scene_cascade(im, t, gq)
    if m == 'side': scene_side(im, t, gq)
    if m == 'window': scene_dose(im, t, gq)
    hook(im, t); scene_myth(im, t); scene_room(im, t); scene_raas(im, t); scene_fix(im, t); scene_clock(im, t); scene_cta(im, t)
    GL = None
    if glow.getbbox():
        sm = glow.resize((W // 4, H // 4), Image.BILINEAR)
        g1 = np.asarray(sm.filter(ImageFilter.GaussianBlur(3.5))).astype(np.float32) / 255; g2 = np.asarray(sm.filter(ImageFilter.GaussianBlur(10))).astype(np.float32) / 255
        prem = np.clip(g1[..., :3] * g1[..., 3:] * 2.0 + g2[..., :3] * g2[..., 3:] * 1.6, 0, 1)
        prem = np.asarray(Image.fromarray((prem * 255).astype(np.uint8)).resize((W, H), Image.BILINEAR)).astype(np.float32) / 255
        b = np.asarray(im.convert('RGB')).astype(np.float32) / 255
        im = Image.fromarray(((1 - (1 - b) * (1 - prem)) * 255).astype(np.uint8)).convert('RGBA')
    d = ImageDraw.Draw(im, 'RGBA'); d.rectangle([0, 0, 7, H], fill=GOLD)
    captions(im, t)
    out = im.convert('RGB')
    # impact shake on key landings (2 frames)
    for t1 in (6.24, 8.42, 22.18, 50.90, 53.32, 80.40):
        k = round((t - t1) * FPS)
        if k in (0, 1):
            dx = [8, -4][k]; z = 1.02; big = out.resize((int(W * z), int(H * z)), Image.BICUBIC); ox = (big.width - W) // 2 - dx; oy = (big.height - H) // 2
            out = big.crop((ox, oy, ox + W, oy + H)); ImageDraw.Draw(out).rectangle([0, 0, 7, H], fill=GOLD)
    return out
GROUPS = build_groups()
if __name__ == '__main__':
    mode = sys.argv[2]
    if mode == 'stills':
        import os; os.makedirs(D_ + '/qc', exist_ok=True)
        for tt in [float(x) for x in sys.argv[3:]]:
            n = round(tt * FPS)
            subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', D_ + '/video.mov', '-vf', f'select=eq(n\\,{n})', '-frames:v', '1', D_ + '/qc/_src.png'])
            frame(Image.open(D_ + '/qc/_src.png').convert('RGB'), n / FPS, n).resize((540, 960)).save(D_ + f'/qc/st_{tt:05.2f}.jpg', quality=85)
        sys.exit()
    n0, n1 = int(sys.argv[3]), int(sys.argv[4]); out = sys.argv[5]
    dec = subprocess.Popen(['ffmpeg', '-v', 'error', '-i', D_ + '/video.mov', '-vf', f'select=between(n\\,{n0}\\,{n1 - 1})', '-vsync', '0', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], stdout=subprocess.PIPE)
    enc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-crf', '14', '-preset', 'fast', '-pix_fmt', 'yuv420p', out], stdin=subprocess.PIPE)
    for n in range(n0, n1):
        buf = dec.stdout.read(W * H * 3)
        if len(buf) < W * H * 3: print('short', n); break
        enc.stdin.write(frame(Image.frombuffer('RGB', (W, H), buf), n / FPS, n).tobytes())
    enc.stdin.close(); enc.wait(); dec.kill(); print('done', n0, n1)
