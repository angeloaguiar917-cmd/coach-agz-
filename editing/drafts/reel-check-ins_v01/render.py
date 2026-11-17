# @coach.agz Reel: "the guys who check in" — 1080x1920 30fps render
# Usage: python3 render.py <workdir> stills t1 t2 ... | python3 render.py <workdir> chunk n0 n1 out.mp4
import json, subprocess, sys, math
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
T = sys.argv[1].rstrip('/') + '/'
F = T + '../fonts/'
W, H = 1080, 1920; FPS = 30
CUT_DUR = 51.933; FREEZE = 0.6; DUR = CUT_DUR + FREEZE; N = int(round(DUR * FPS))
WORDS = json.load(open(T + 'words_caps.json'))
BOUNDS = json.load(open(T + 'bounds.json'))          # jump-cut times in the cut timeline
GOLD = (201, 169, 110); CREAM = (244, 241, 234); NAVY = (14, 17, 23)
RED = (255, 34, 28); VGOLD = (255, 194, 26); CYAN = (0, 229, 255); GREEN = (30, 255, 110)
DEEP = (2, 3, 8); INK = (6, 8, 14); WHITE = (255, 255, 255); MUTED = (124, 124, 130)
BLUE = (79, 163, 224); AMBER = (240, 160, 48); SGREEN = (60, 203, 106)
MONO = 'JBMono-500.ttf'; MONOB = 'JBMono-700.ttf'; BEB = 'BebasNeue.ttf'; BAR = 'Barlow-700.ttf'; BAR6 = 'Barlow-600.ttf'
_fc = {}
def f(n, s):
    k = (n, int(s))
    if k not in _fc: _fc[k] = ImageFont.truetype(F + n, int(s))
    return _fc[k]
def clamp(x, a=0, b=1): return max(a, min(b, x))
def expo(x): x = clamp(x); return 1 if x >= 1 else 1 - 2 ** (-10 * x)
def ease_io(x): x = clamp(x); return 4 * x ** 3 if x < .5 else 1 - (-2 * x + 2) ** 3 / 2
def back(x):  # heavy landing: slight settle, no bounce
    x = clamp(x); return 1 - (1 - x) ** 4
def lerp(a, b, t): return a + (b - a) * t
def A(c, a): return tuple(c[:3]) + (int(clamp(a) * 255),)
def appear(t, t0, dur=0.16): return expo((t - t0) / dur)
GL = None
def txt(d, x, y, s, font, col, a=1.0, anchor=None): d.text((x, y), s, font=font, fill=A(col, a), anchor=anchor)

# ---------------- primitives ----------------
def brackets(d, x0, y0, x1, y1, col, L=34, w=4):
    for (cx, cy, sx, sy) in [(x0, y0, 1, 1), (x1, y0, -1, 1), (x0, y1, 1, -1), (x1, y1, -1, -1)]:
        d.line([(cx, cy), (cx + sx * L, cy)], fill=col, width=w); d.line([(cx, cy), (cx, cy + sy * L)], fill=col, width=w)
def lit_bar(d, x0, y0, x1, y1, col, a=1.0):
    h = max(1, int(y1 - y0))
    for i in range(h):
        k = i / h; c = tuple(int(min(255, v * (1.18 - 0.36 * k) + (40 if k < 0.12 else 0))) for v in col)
        d.line([(x0, y0 + i), (x1, y0 + i)], fill=c + (int(255 * clamp(a)),))
def tag(d, x, y, label, col=RED, size=30, a=1.0, glow=True, right=False):
    if a <= 0: return x
    fn = f(MONOB, size); tw = d.textlength(label, font=fn); h = size + 16
    if right: x = x - tw - 24
    lit_bar(d, x, y, x + tw + 24, y + h, col, a)
    d.text((x + 12, y + 5), label, font=fn, fill=A(INK if col in (VGOLD, GREEN) else WHITE, a))
    if GL and glow: GL.rectangle([x - 4, y - 4, x + tw + 28, y + h + 4], outline=A(col, a), width=8)
    return x + tw + 24
def check(d, x, y, col, s=1.0, a=1.0):
    pts = [(x, y + 16 * s), (x + 10 * s, y + 28 * s), (x + 30 * s, y + 2 * s)]
    d.line(pts, fill=A(col, a), width=int(6 * s), joint='curve')
    if GL: GL.line(pts, fill=A(col, a), width=int(12 * s))
def cross(d, x, y, col, s=1.0, a=1.0):
    d.line([(x, y), (x + 28 * s, y + 28 * s)], fill=A(col, a), width=int(6 * s)); d.line([(x + 28 * s, y), (x, y + 28 * s)], fill=A(col, a), width=int(6 * s))
    if GL: GL.line([(x, y), (x + 28 * s, y + 28 * s)], fill=A(col, a), width=12); GL.line([(x + 28 * s, y), (x, y + 28 * s)], fill=A(col, a), width=12)
def frosted(im, box, dark=0.86, blur=10):
    x0, y0, x1, y1 = [int(v) for v in box]
    x0 = max(0, x0); y0 = max(0, y0); x1 = min(W, x1); y1 = min(H, y1)
    if x1 <= x0 or y1 <= y0: return
    reg = im.crop((x0, y0, x1, y1)).convert('RGB').filter(ImageFilter.GaussianBlur(blur))
    im.paste(Image.blend(reg, Image.new('RGB', reg.size, DEEP), dark).convert('RGBA'), (x0, y0))
def polyline(d, pts, col, w, a=1.0, glow=True):
    if len(pts) < 2: return
    d.line(pts, fill=A(col, a), width=w, joint='curve')
    if GL and glow: GL.line(pts, fill=A(col, a), width=w * 2 + 4, joint='curve')
def partial(pts, p):
    """first fraction p (0..1) of a polyline"""
    if p <= 0: return pts[:1]
    seg = [math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1)]; L = sum(seg) * clamp(p); out = [pts[0]]
    for i, s in enumerate(seg):
        if L >= s: out.append(pts[i + 1]); L -= s
        else:
            q = L / s if s else 0; out.append((lerp(pts[i][0], pts[i + 1][0], q), lerp(pts[i][1], pts[i + 1][1], q))); break
    return out

# ---------------- assets ----------------
IMG = {}
def img(name, size=None):
    k = (name, size)
    if k not in IMG:
        im = Image.open(T + 'img/' + name).convert('RGBA')
        if size: im = im.resize(size, Image.LANCZOS)
        IMG[k] = im
    return IMG[k]
def paste_img(im, src, x, y, a=1.0, blur=0, scale=1.0):
    s = src
    if abs(scale - 1) > 0.003: s = s.resize((max(1, int(s.width * scale)), max(1, int(s.height * scale))), Image.BICUBIC); x -= (s.width - src.width) / 2; y -= (s.height - src.height) / 2
    if blur > 0.3: s = s.filter(ImageFilter.GaussianBlur(blur))
    if a < 1: s = s.copy(); s.putalpha(s.split()[3].point(lambda v: int(v * a)))
    im.alpha_composite(s, (int(x), int(y)))
def shadow(im, box, a=1.0, r=22):
    x0, y0, x1, y1 = [int(v) for v in box]; pad = 40
    sh = Image.new('RGBA', (x1 - x0 + 2 * pad, y1 - y0 + 2 * pad), (0, 0, 0, 0))
    ImageDraw.Draw(sh).rectangle([pad, pad + 14, pad + x1 - x0, pad + y1 - y0 + 14], fill=(0, 0, 0, int(200 * a)))
    im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(r)), (x0 - pad, y0 - pad))
LOGO = None
def logo(sz):
    global LOGO
    if LOGO is None:
        lg = Image.open(T + 'img/logo.jpg').convert('RGB'); s = min(lg.size)
        lg = lg.crop(((lg.width - s) // 2, (lg.height - s) // 2, (lg.width + s) // 2, (lg.height + s) // 2)).resize((sz, sz), Image.LANCZOS)
        m = Image.new('L', (sz, sz), 0); ImageDraw.Draw(m).ellipse([0, 0, sz - 1, sz - 1], fill=255); lg.putalpha(m); LOGO = lg
    return LOGO
def make_deck_bg():
    bg = Image.new('RGB', (W, H), NAVY); px = np.asarray(bg).astype(np.float32)
    yy, xx = np.mgrid[0:H, 0:W]
    g = np.exp(-(((xx - 980) / 700) ** 2 + ((yy - 980) / 520) ** 2)) * 26
    px += g[..., None] * np.array([1.0, 0.85, 0.55])
    grid = ((xx % 60 == 0) | (yy % 60 == 0)) & (yy > 900)
    px[grid] += 7
    rng = np.random.default_rng(3); px += rng.normal(0, 2.2, px.shape[:2])[..., None]
    return Image.fromarray(np.clip(px, 0, 255).astype(np.uint8))
DECK = None

# ---------------- layout: A = full talking head, B = split (footage window top, deck below) ----------------
K = 0.85; SRC_Y = 420; WIN_B = (81, 0, 999, 900)
LAYOUT_B = [(17.96, 25.0 + 4.95 + 6.75 + 6.95), (49.92, 99)]  # B from 17.96 to 43.66, and the end card
LAYOUT_B = [(17.96, 43.66), (49.92, 99)]
def split_amt(t):
    s = 0
    for a, b in LAYOUT_B:
        if a - 0.0 <= t < b + 0.40:
            s = max(s, min(ease_io((t - a) / 0.38), 1 - ease_io((t - b) / 0.36)))
    return s
EMPH = [(16.66, 17.96, 1.12), (45.54, 48.54, 1.12)]  # emphasis punch-ins (snap)
def zoom_a(t):
    for a, b, z in EMPH:
        if a <= t < b: return z
    k = 0
    for b in BOUNDS:
        if b <= t + 1e-6: k += 1
    return 1.0 if k % 2 == 0 else 1.06

# ---------------- text hook (frame 0) + topic band ----------------
HOOK_END = 5.5
def text_hook(im, d, t):
    if t >= HOOK_END + 0.15: return
    a = 1.0 if t < HOOK_END else 1 - (t - HOOK_END) / 0.15
    s = lerp(1.0, 1.04, clamp(t / HOOK_END))           # slow 100 -> 104 % over the hold
    lines = [('My best ', 'CLIENTS'), ('never skip a week', '')]
    sz = int(96 * s); fn = f(BAR, sz)
    widths = [d.textlength(p + q, font=fn) for p, q in lines]
    bw = max(widths) + 80; cx = W / 2; y0 = 262 - (s - 1) * 120; lh = int(sz * 1.06)
    x0 = cx - bw / 2; x1 = cx + bw / 2; y1 = y0 + 2 * lh + 40
    box = Image.new('RGBA', (W, H), (0, 0, 0, 0)); bd = ImageDraw.Draw(box)
    bd.rounded_rectangle([x0, y0, x1, y1], radius=22, fill=A(DEEP, 0.88 * a))
    bd.rectangle([x0, y0 + 18, x0 + 8, y1 - 18], fill=A(GOLD, a))
    im.alpha_composite(box); d = ImageDraw.Draw(im, 'RGBA')
    for i, (p, q) in enumerate(lines):
        w_ = widths[i]; x = cx - w_ / 2 + 4; y = y0 + 14 + i * lh
        txt(d, x, y, p, fn, WHITE, a)
        if q: txt(d, x + d.textlength(p, font=fn), y, q, fn, VGOLD, a)
    if GL and a > 0: GL.rectangle([x0 - 2, y0 + 18, x0 + 10, y1 - 18], fill=A(GOLD, a * 0.6))
def topic_band(im, d, t, s):
    if not (HOOK_END <= t < 26.0): return
    a = clamp((t - HOOK_END) / 0.15) * (1 - s)
    if t > 25.85: a *= 1 - (t - 25.85) / 0.15
    if a <= 0: return
    fn = f(BAR6, 46); p, q = 'The guys who ', 'CHECK IN'
    tw = d.textlength(p + q, font=fn); x0 = 60; y0 = 232
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); ld = ImageDraw.Draw(lay)
    ld.rectangle([x0, y0, x0 + tw + 48, y0 + 64], fill=A(NAVY, 0.9 * a)); ld.rectangle([x0, y0, x0 + 6, y0 + 64], fill=A(GOLD, a))
    im.alpha_composite(lay); d = ImageDraw.Draw(im, 'RGBA')
    txt(d, x0 + 26, y0 + 6, p, fn, CREAM, a); txt(d, x0 + 26 + d.textlength(p, font=fn), y0 + 6, q, fn, VGOLD, a)

# ---------------- top-band widgets (layout A) ----------------
TB = (48, 300, 1032, 488)
def panel_top(im, t, t0, t1, kicker, right, rcol=VGOLD, kcol=VGOLD, y0=300, y1=488):
    pin = expo((t - t0) / 0.18); pout = clamp((t - t1) / 0.14)
    a = pin * (1 - pout)
    if a <= 0: return None, 0
    x0, x1 = TB[0], TB[2]; dy = lerp(-24, 0, pin)
    frosted(im, (x0, y0 + dy, x1, y1 + dy), 0.9, 12)
    d = ImageDraw.Draw(im, 'RGBA')
    d.rectangle([x0, y0 + dy, x0 + 6, y1 + dy], fill=A(GOLD, a))
    brackets(d, x0, y0 + dy, x1, y1 + dy, A(VGOLD, a), 22, 4)
    if GL: brackets(GL, x0, y0 + dy, x1, y1 + dy, A(VGOLD, a), 22, 9)
    txt(d, x0 + 24, y0 + 12 + dy, kicker, f(MONOB, 24), kcol, a)
    fr = f(MONOB, 24); tw = d.textlength(right, font=fr); txt(d, x1 - 22 - tw, y0 + 12 + dy, right, fr, rcol, a)
    return d, a, dy
def w_overnight(im, t):     # 5.5 - 11.1 : submitted AM -> midnight response -> ready tomorrow
    r = panel_top(im, t, 5.62, 11.05, 'CHECK-IN TURNAROUND', 'LIVE', GREEN)
    if r[0] is None: return
    d, a, dy = r; y = 300 + 122 + dy
    xs = [150, 540, 930]
    p1 = clamp((t - 6.2) / 2.0); p2 = clamp((t - 8.7) / 1.8)
    d.line([(xs[0], y), (xs[2], y)], fill=A((60, 64, 80), a), width=4)
    d.line([(xs[0], y), (lerp(xs[0], xs[1], ease_io(p1)), y)], fill=A(VGOLD, a), width=5)
    if p2 > 0: d.line([(xs[1], y), (lerp(xs[1], xs[2], ease_io(p2)), y)], fill=A(VGOLD, a), width=5)
    if GL: GL.line([(xs[0], y), (lerp(xs[0], xs[1], ease_io(p1)), y)], fill=A(VGOLD, a), width=10)
    nodes = [(6.10, 'SUBMITTED', 'THIS AM', VGOLD), (8.40, 'RESPONSE', None, VGOLD), (10.66, 'READY', 'TOMORROW', GREEN)]
    for i, (tt, lab, sub, col) in enumerate(nodes):
        on = t >= tt; aa = a * (appear(t, tt, 0.12) if on else 0.35)
        c = col if on else (90, 94, 110)
        d.ellipse([xs[i] - 13, y - 13, xs[i] + 13, y + 13], fill=A(DEEP, a), outline=A(c, a), width=4)
        if on:
            d.ellipse([xs[i] - 6, y - 6, xs[i] + 6, y + 6], fill=A(c, aa))
            if GL: GL.ellipse([xs[i] - 18, y - 18, xs[i] + 18, y + 18], fill=A(c, aa * 0.8))
        fn = f(BAR, 42); lw = d.textlength(lab, font=fn)
        lx = min(max(xs[i] - lw / 2, 84), 1000 - lw)
        txt(d, lx, y - 72, lab, fn, WHITE if on else (110, 110, 120), a)
        if sub:
            fs = f(MONOB, 26); sw = d.textlength(sub, font=fs); sx = min(max(xs[i] - sw / 2, 84), 1000 - sw)
            txt(d, sx, y + 20, sub, fs, c, aa if on else a * 0.35)
    # midnight clock on the middle node
    if t >= 7.6:
        ca = a * appear(t, 7.6, 0.12)
        mins = 58 + int(clamp((t - 7.7) / 0.7) * 2)
        s_ = '12:00 AM' if mins >= 60 else f'11:{mins:02d} PM'
        fs = f(MONOB, 28); sw = d.textlength(s_, font=fs)
        col = VGOLD if mins >= 60 else CREAM
        txt(d, xs[1] - sw / 2, y + 20, s_, fs, col, ca)
    if t >= 10.66: check(d, xs[2] + 44, y - 66, GREEN, 0.8, a * appear(t, 10.66, 0.12))
def w_scan(im, t):          # 11.2 - 16.9 : scan of client files, one pattern locks
    r = panel_top(im, t, 11.30, 16.86, 'CLIENT FILES · ALL CHECK-INS', 'SCANNING' if t < 15.22 else 'PATTERN FOUND', VGOLD if t >= 15.22 else CYAN)
    if r[0] is None: return
    d, a, dy = r
    cols = 15; x0 = 76; cw = 57; gap = 4.4; ys = [354 + dy, 418 + dy]
    sx = lerp(x0 - 40, x0 + cols * (cw + gap) + 40, clamp((t - 11.8) / 3.0)) if t < 14.9 else None
    pattern_on = t >= 14.68
    rng = np.random.default_rng(11)
    for r_ in range(2):
        for c in range(cols):
            x = x0 + c * (cw + gap); y = ys[r_]
            scanned = sx is None or x < sx
            gold = pattern_on and r_ == 0
            col = VGOLD if gold else ((70, 84, 110) if scanned else (40, 44, 58))
            fa = a * (appear(t, 14.68 + c * 0.012, 0.1) if gold else 1)
            d.rounded_rectangle([x, y, x + cw, y + 52], radius=6, fill=A((12, 16, 26), a), outline=A(col if not gold else VGOLD, a), width=2)
            if gold:
                d.rounded_rectangle([x + 6, y + 6, x + cw - 6, y + 46], radius=4, fill=A(VGOLD, fa * 0.85))
                if GL: GL.rounded_rectangle([x, y, x + cw, y + 52], radius=6, outline=A(VGOLD, fa), width=6)
            elif scanned:
                k = rng.integers(1, 4)
                for j in range(k): d.line([(x + 8, y + 12 + j * 12), (x + 8 + rng.integers(16, 40), y + 12 + j * 12)], fill=A((110, 120, 140), a), width=3)
    if sx is not None and sx < x0 + cols * (cw + gap) + 30:
        d.line([(sx, 346 + dy), (sx, 478 + dy)], fill=A(CYAN, a), width=4)
        if GL: GL.line([(sx, 346 + dy), (sx, 478 + dy)], fill=A(CYAN, a), width=14)
    if t >= 15.22:
        p = expo((t - 15.22) / 0.14); bx0, by0, bx1, by1 = x0 - 8, ys[0] - 7, x0 + cols * (cw + gap) + 4, ys[0] + 59
        brackets(d, bx0, by0, bx1, by1, A(RED, a * p), 18, 5)
        if GL: brackets(GL, bx0, by0, bx1, by1, A(RED, a * p), 18, 10)
def w_monitor(im, t):       # 43.9 - 49.9 : flatline progress, then the missed check-in log
    swap = 48.54; Y0 = 262
    r = panel_top(im, t, 43.90, 51.0, 'PROGRESS MONITOR' if t < swap else 'CHECK-IN LOG · SAME CLIENT', 'FLAT' if t < swap else 'GAPS', RED, RED, y0=Y0, y1=488)
    if r[0] is None: return
    d, a, dy = r
    if t < swap + 0.12:
        b = a * (1 - clamp((t - swap) / 0.12))
        x0, x1, y = 76, 640, Y0 + 132 + dy
        for k in (-1, 0, 1): d.line([(x0, y + k * 56), (x1, y + k * 56)], fill=A((40, 44, 60), b), width=1)
        txt(d, x0, Y0 + 52 + dy, 'WEEK 1', f(MONO, 20), MUTED, b); txt(d, x1 - 90, Y0 + 52 + dy, 'WEEK 12', f(MONO, 20), MUTED, b)
        p = clamp((t - 44.0) / 1.5); pts = []
        for i in range(61):
            xx = lerp(x0, x1, i / 60); n = math.sin(i * 1.7 + t * 9) * 2.5 if i % 7 else 0
            pts.append((xx, y + n))
        polyline(d, partial(pts, p), RED, 5, b)
        if 0 < p < 1:
            e = partial(pts, p)[-1]; d.ellipse([e[0] - 8, e[1] - 8, e[0] + 8, e[1] + 8], fill=A(WHITE, b))
        if t >= 45.54:
            c = b * appear(t, 45.54, 0.1)
            txt(d, 690, Y0 + 52 + dy, 'PROGRESS', f(MONOB, 22), MUTED, c)
            txt(d, 690, Y0 + 70 + dy, '0.0', f(BEB, 120), RED, c)
            if GL: GL.text((690, Y0 + 70 + dy), '0.0', font=f(BEB, 120), fill=A(RED, c * 0.7))
        if t >= 47.76:
            tag(d, 846, Y0 + 92 + dy, 'BLAMES', RED, 24, b * appear(t, 47.76, 0.1))
            tag(d, 846, Y0 + 140 + dy, 'COACH', RED, 24, b * appear(t, 47.86, 0.1))
    if t >= swap:
        b = a * appear(t, swap + 0.02, 0.12)
        marks = [1, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0]
        x0 = 76; cw = 66; gap = 13.5; y = Y0 + 84 + dy
        for i, m in enumerate(marks):
            tt = swap + 0.1 + i * 0.07; x = x0 + i * (cw + gap)
            d.rounded_rectangle([x, y, x + cw, y + 66], radius=8, fill=A((12, 16, 26), b), outline=A((70, 74, 90), b), width=2)
            if t >= tt:
                c = b * appear(t, tt, 0.08)
                if m: check(d, x + 17, y + 17, GREEN, 0.95, c)
                else:
                    d.rounded_rectangle([x, y, x + cw, y + 66], radius=8, outline=A(RED, c), width=3); cross(d, x + 19, y + 19, RED, 0.95, c)
            txt(d, x + 14, y - 28, f'W{i + 1}', f(MONO, 20), MUTED, b)
        if t >= 49.58: tag(d, x0, y + 84, 'CHECK-INS MISSED', RED, 28, a * appear(t, 49.58, 0.1))
# ---------------- deck scenes (layout B) ----------------
DX0, DX1, DY0, DY1 = 60, 1020, 990, 1478
def deck_header(d, a, left, right, rcol=VGOLD):
    y = 928
    d.line([(DX0, y + 16), (DX0 + 40, y + 16)], fill=A(VGOLD, a), width=4)
    txt(d, DX0 + 54, y, left, f(MONO, 26), VGOLD, a)
    fr = f(MONO, 26); tw = d.textlength(right, font=fr); txt(d, DX1 - tw, y, right, fr, rcol, a)
def photo_card(im, d, x, y, before, after, tb, ta, t, a=1.0, dim=0.0):
    w2, h = 235, 470
    p = back((t - tb) / 0.16)
    if p <= 0: return
    al = a * clamp(p * 1.4); yy = y + lerp(70, 0, p); sc = lerp(1.06, 1.0, p)
    shadow(im, (x, yy, x + 2 * w2, yy + h), al * 0.9)
    paste_img(im, img(before, (w2, h)), x, yy, al * (1 - dim * 0.6), blur=(1 - p) * 8, scale=sc)
    q = expo((t - ta) / 0.22)
    if q > 0:
        ai = img(after, (w2, h)); cut_h = int(h * q)
        if cut_h > 0:
            part = ai.crop((0, 0, w2, cut_h)); paste_img(im, part, x + w2, yy, al * (1 - dim * 0.6))
        d = ImageDraw.Draw(im, 'RGBA')
        if q < 1:
            d.line([(x + w2, yy + cut_h), (x + 2 * w2, yy + cut_h)], fill=A(VGOLD, al), width=4)
            if GL: GL.line([(x + w2, yy + cut_h), (x + 2 * w2, yy + cut_h)], fill=A(VGOLD, al), width=12)
    d = ImageDraw.Draw(im, 'RGBA')
    d.rectangle([x, yy, x + 2 * w2, yy + h], outline=A((70, 74, 90), al), width=2)
    d.line([(x + w2, yy), (x + w2, yy + h)], fill=A(WHITE, al * (1 - dim * 0.5)), width=3)
    brackets(d, x - 6, yy - 6, x + 2 * w2 + 6, yy + h + 6, A(VGOLD, al * (1 - dim * 0.5)), 30, 5)
    if GL and dim < 0.5: brackets(GL, x - 6, yy - 6, x + 2 * w2 + 6, yy + h + 6, A(VGOLD, al), 30, 10)
    tag(d, x + 10, yy + h - 50, 'BEFORE', RED, 22, al * (1 - dim * 0.5), glow=dim < 0.5)
    if q > 0.6: tag(d, x + w2 + 10, yy + h - 50, 'AFTER', VGOLD, 22, al * appear(t, ta + 0.1, 0.1) * (1 - dim * 0.5), glow=dim < 0.5)
def scene_results(im, t, a):    # 17.96 - 25.0
    d = ImageDraw.Draw(im, 'RGBA'); deck_header(d, a, 'CLIENT RESULTS', 'EVIDENCE 01')
    out = expo((t - 24.92) / 0.18); ox = -1100 * out ** 2
    dim = expo((t - 23.22) / 0.2) if t >= 23.22 else 0
    photo_card(im, d, DX0 + ox, DY0 + 2, 't1_before.png', 't1_after.png', 19.48, 20.02, t, a, dim)
    photo_card(im, d, DX0 + 490 + ox, DY0 + 2, 't2_before.png', 't2_after.png', 21.40, 22.16, t, a, dim)
    if t >= 23.22:
        p = back((t - 23.22) / 0.18); dm = img('dm.png', (394, 470))
        x = 343 + ox; y = DY0 + 2 + lerp(80, 0, p); al = a * clamp(p * 1.5)
        shadow(im, (x, y, x + 394, y + 470), al)
        paste_img(im, dm, x, y, al, blur=(1 - p) * 6, scale=lerp(1.08, 1, p))
        d = ImageDraw.Draw(im, 'RGBA')
        d.rectangle([x, y, x + 394, y + 470], outline=A(VGOLD, al), width=3)
        tag(d, x + 10, y + 10, 'CLIENT DM', VGOLD, 22, al)
        if t >= 24.38:
            b = expo((t - 24.38) / 0.14); bx0, by0, bx1, by1 = x + 2, y + 366, x + 392, y + 468
            brackets(d, bx0, by0, bx1, by1, A(RED, al * b), 24, 6)
            if GL: brackets(GL, bx0, by0, bx1, by1, A(RED, al * b), 24, 12)
MARKERS = [('HEMATOCRIT', 0.86, 0.47), ('ESTRADIOL', 0.12, 0.42), ('LDL-C', 0.92, 0.36), ('ALT · LIVER', 0.80, 0.40), ('eGFR · KIDNEY', 0.07, 0.52)]
def spectrum_strip(w, h):
    stops = [(0, BLUE), (0.2, BLUE), (0.27, SGREEN), (0.62, SGREEN), (0.72, AMBER), (0.84, AMBER), (0.92, RED), (1, RED)]
    arr = np.zeros((h, w, 3), np.float32)
    for x in range(w):
        u = x / (w - 1)
        for i in range(len(stops) - 1):
            if stops[i][0] <= u <= stops[i + 1][0]:
                q = (u - stops[i][0]) / max(1e-6, stops[i + 1][0] - stops[i][0]); c = [lerp(stops[i][1][k], stops[i + 1][1][k], q) for k in range(3)]; break
        arr[:, x] = c
    arr *= np.linspace(1.15, 0.7, h)[:, None, None]
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).convert('RGBA')
SPEC = None
def scene_blood(im, t, a):      # 25.08 - 29.95
    global SPEC
    if SPEC is None: SPEC = spectrum_strip(560, 20)
    d = ImageDraw.Draw(im, 'RGBA'); deck_header(d, a, 'BLOODWORK · CLIENT PANEL', 'EVIDENCE 02')
    xb0, xb1 = 410, 970
    txt(d, xb0, DY0 - 6, 'LOW', f(MONO, 18), BLUE, a * 0.9); txt(d, lerp(xb0, xb1, 0.36), DY0 - 6, 'DIALED IN', f(MONO, 18), SGREEN, a * 0.9); txt(d, lerp(xb0, xb1, 0.86), DY0 - 6, 'HIGH', f(MONO, 18), AMBER, a * 0.9)
    enter = [25.52, 25.88, 26.30, 26.72, 27.06]; land = [27.36, 27.62, 27.88, 28.16, 28.44]
    for i, (nm, start, end) in enumerate(MARKERS):
        y = DY0 + 34 + i * 76; ra = a * appear(t, enter[i], 0.16)
        if ra <= 0: continue
        dx = lerp(-30, 0, expo((t - enter[i]) / 0.16))
        txt(d, DX0 + dx, y - 6, nm, f(BAR6, 40), WHITE, ra)
        sp = SPEC.copy(); sp.putalpha(int(255 * ra * 0.9)); im.alpha_composite(sp, (xb0, y + 6)); d = ImageDraw.Draw(im, 'RGBA')
        d.rectangle([xb0, y + 6, xb1, y + 26], outline=A((20, 22, 30), ra), width=2)
        mv = ease_io((t - land[i] + 0.34) / 0.34)
        u = lerp(start, end, mv); mx = lerp(xb0, xb1, u)
        settled = t >= land[i]
        c = WHITE if not settled else GREEN
        d.polygon([(mx - 12, y - 10), (mx + 12, y - 10), (mx, y + 4)], fill=A(c, ra)); d.line([(mx, y), (mx, y + 32)], fill=A(c, ra), width=4)
        if GL: GL.line([(mx, y - 8), (mx, y + 32)], fill=A(c, ra), width=10)
        if t >= 28.6 + i * 0.09:
            check(d, xb1 + 14, y - 2, GREEN, 0.8, ra * appear(t, 28.6 + i * 0.09, 0.1))
    if t >= 29.06:
        p = expo((t - 29.06) / 0.2); y = DY0 + 34 + 5 * 76 - 4; x1 = lerp(DX0, DX1, p)
        lit_bar(d, DX0, y, x1, y + 62, GREEN, a)
        if GL: GL.rectangle([DX0 - 4, y - 4, x1 + 4, y + 66], outline=A(GREEN, a), width=10)
        if p > 0.6: txt(d, DX0 + 22, y + 4, 'ALL MARKERS IN RANGE', f(BEB, 58), INK, a)
WEEK = 12
def week_cells(d, t, y, x0, marks, t0, step, a, cw=58, gap=6):
    for i in range(WEEK):
        x = x0 + i * (cw + gap)
        d.rounded_rectangle([x, y, x + cw, y + 54], radius=8, fill=A((12, 16, 26), a), outline=A((60, 64, 80), a), width=2)
        tt = t0 + i * step
        if t >= tt:
            c = a * appear(t, tt, 0.08)
            if marks[i]: d.rounded_rectangle([x, y, x + cw, y + 54], radius=8, outline=A(GREEN, c), width=3); check(d, x + 14, y + 12, GREEN, 0.95, c)
            else: d.rounded_rectangle([x, y, x + cw, y + 54], radius=8, outline=A(RED, c), width=3); cross(d, x + 16, y + 13, RED, 0.95, c)
def scene_checkins(im, t, a):   # 30.04 - 36.7
    d = ImageDraw.Draw(im, 'RGBA'); deck_header(d, a, 'CHECK-IN LOG · 12 WEEKS', 'THE PATTERN')
    x0 = 252
    dimred = 1 - 0.65 * expo((t - 35.74) / 0.25) if t >= 35.74 else 1
    txt(d, DX0, DY0 + 8, 'EVERY WEEK', f(BAR, 34), VGOLD, a)
    week_cells(d, t, DY0, x0, [1] * 12, 30.88, 0.113, a)
    if t >= 33.98:
        b = a * appear(t, 33.98, 0.14) * dimred
        txt(d, DX0, DY0 + 76, 'ON / OFF', f(BAR, 34), RED, b)
        week_cells(d, t, DY0 + 68, x0, [1, 1, 0, 1, 0, 0, 1, 1, 0, 1, 0, 1], 34.12, 0.065, b)
    # chart
    cx0, cx1, cy0, cy1 = DX0 + 10, DX1 - 10, DY0 + 150, DY1 - 6
    ca = a * appear(t, 31.6, 0.25)
    d.line([(cx0, cy1), (cx1, cy1)], fill=A((90, 94, 110), ca), width=2); d.line([(cx0, cy0), (cx0, cy1)], fill=A((90, 94, 110), ca), width=2)
    for k in range(1, 4): d.line([(cx0, cy1 - k * 80), (cx1, cy1 - k * 80)], fill=A((36, 40, 56), ca), width=1)
    txt(d, cx0 + 14, cy0 - 4, 'PROGRESS', f(MONO, 22), MUTED, ca)
    gx = [lerp(cx0 + 20, cx1 - 30, i / 11) for i in range(12)]
    gold = [(gx[i], cy1 - 30 - (cy1 - cy0 - 90) * (i / 11) ** 0.9) for i in range(12)]
    redv = [0.06, 0.12, 0.06, 0.13, 0.07, 0.02, 0.09, 0.15, 0.08, 0.14, 0.07, 0.12]
    redp = [(gx[i], cy1 - 30 - (cy1 - cy0 - 90) * redv[i]) for i in range(12)]
    if t >= 32.6:
        polyline(d, partial(gold, ease_io((t - 32.6) / 0.85)), VGOLD, 6, a)
        e = partial(gold, ease_io((t - 32.6) / 0.85))[-1]; d.ellipse([e[0] - 9, e[1] - 9, e[0] + 9, e[1] + 9], fill=A(WHITE, a))
    if t >= 34.5:
        polyline(d, partial(redp, ease_io((t - 34.5) / 1.05)), RED, 5, a * dimred, glow=dimred > 0.6)
    if t >= 36.0:
        b = a * appear(t, 36.0, 0.12)
        tag(d, gold[-1][0] - 10, gold[-1][1] + 26, 'CONSISTENT', VGOLD, 26, b, right=True)
        pulse = 1 - clamp((t - 36.0) / 0.5)
        if GL and pulse > 0: GL.line(gold, fill=A(VGOLD, pulse), width=26)
def scene_comms(im, t, a):      # 36.78 - 43.66
    d = ImageDraw.Draw(im, 'RGBA'); deck_header(d, a, 'CLIENT · COACH', 'EVIDENCE 03')
    chat = img('chat.png'); full_h = 480; full_s = full_h / chat.height
    small_s = 0.46
    p = back((t - 36.92) / 0.18); m = ease_io((t - 38.62) / 0.36)
    s_ = lerp(full_s, small_s, m) * lerp(1.06, 1, p)
    cw, ch = chat.width * s_, chat.height * s_
    x = lerp((W - chat.width * full_s) / 2, DX0, m); y = DY0 + lerp(70, 0, p)
    al = a * clamp(p * 1.5)
    if al > 0:
        ci = chat.resize((int(cw), int(ch)), Image.BICUBIC)
        shadow(im, (x, y, x + cw, y + ch), al)
        paste_img(im, ci, x, y, al, blur=(1 - p) * 6)
        d = ImageDraw.Draw(im, 'RGBA')
        d.rectangle([x, y, x + cw, y + ch], outline=A(VGOLD, al), width=3)
        brackets(d, x - 6, y - 6, x + cw + 6, y + ch + 6, A(VGOLD, al), 26, 5)
        if GL: brackets(GL, x - 6, y - 6, x + cw + 6, y + ch + 6, A(VGOLD, al), 26, 10)
        tag(d, x + 10, y + ch - 46, 'CLIENT CHAT', VGOLD, 20, al)
    if t >= 38.7:
        b = a * appear(t, 38.7, 0.2)
        px0 = 530; colw = 68
        days = ['M', 'T', 'W', 'T', 'F', 'S', 'S']
        counts = [3, 4, 2, 4, 3, 3, 2]
        txt(d, px0, DY0 - 2, 'CONTACT · 1 WEEK', f(MONO, 22), MUTED, b)
        base = DY1 - 50
        d.line([(px0 - 10, base + 6), (px0 + 7 * colw, base + 6)], fill=A((90, 94, 110), b), width=2)
        for i, dn in enumerate(days):
            cx = px0 + i * colw + colw / 2 - 10
            txt(d, cx - 8, base + 14, dn, f(MONOB, 24), CREAM, b)
            n_on = 0
            if t >= 38.92 + i * 0.06: n_on = 1
            for k in range(1, counts[i]):
                if t >= 42.2 + (i * 3 + k) * 0.045: n_on = k + 1
            for k in range(n_on):
                tt = 38.92 + i * 0.06 if k == 0 else 42.2 + (i * 3 + k) * 0.045
                c = b * appear(t, tt, 0.08); yy = base - 34 - k * 62 + lerp(-14, 0, expo((t - tt) / 0.1))
                col = VGOLD
                d.rounded_rectangle([cx - 24, yy - 22, cx + 24, yy + 22], radius=10, fill=A(col, c))
                d.polygon([(cx - 10, yy + 20), (cx + 2, yy + 20), (cx - 12, yy + 32)], fill=A(col, c))
                if GL: GL.rounded_rectangle([cx - 28, yy - 26, cx + 28, yy + 26], radius=12, fill=A(col, c * 0.5))
        if t >= 39.30: tag(d, px0, DY0 + 38, 'EVERY DAY', VGOLD, 24, a * appear(t, 39.30, 0.1))
        if t >= 43.40: tag(d, px0 + 196, DY0 + 38, 'MULTIPLE / DAY', RED, 24, a * appear(t, 43.40, 0.1))
    if m > 0.5:
        c = a * appear(t, 39.2, 0.2); on = 0.55 + 0.45 * math.sin(t * 7)
        y = DY0 + 336
        d.ellipse([DX0 + 4, y + 8, DX0 + 22, y + 26], fill=A(GREEN, c * on))
        if GL: GL.ellipse([DX0 - 4, y, DX0 + 30, y + 34], fill=A(GREEN, c * on))
        txt(d, DX0 + 34, y, 'LINE OPEN', f(MONOB, 26), GREEN, c)
def scene_end(im, t, a):        # 49.92 -> end
    d = ImageDraw.Draw(im, 'RGBA'); deck_header(d, a, 'TWO KINDS OF CLIENT', 'THE DIFFERENCE')
    cx0, cx1, cy0, cy1 = DX0 + 10, 600, DY0 + 30, DY1 - 70
    d.line([(cx0, cy1), (cx1, cy1)], fill=A((90, 94, 110), a), width=2); d.line([(cx0, cy0), (cx0, cy1)], fill=A((90, 94, 110), a), width=2)
    g = [(lerp(cx0, cx1 - 20, i / 10), cy1 - 20 - (cy1 - cy0 - 50) * (i / 10) ** 1.1) for i in range(11)]
    r = [(lerp(cx0, cx1 - 20, i / 10), cy1 - 20 - 26 * (0.5 + 0.5 * math.sin(i * 1.9))) for i in range(11)]
    pg = ease_io((t - 50.15) / 0.9); pr = ease_io((t - 50.3) / 0.9)
    polyline(d, partial(g, pg), VGOLD, 6, a); polyline(d, partial(r, pr), RED, 5, a)
    if pg >= 1: tag(d, g[-1][0], g[-1][1] - 54, 'CHECKS IN', VGOLD, 22, a * appear(t, 51.05, 0.1), right=True)
    if pr >= 1: tag(d, r[-1][0], r[-1][1] - 60, 'SKIPS', RED, 22, a * appear(t, 51.2, 0.1), right=True)
    la = a * appear(t, 50.4, 0.25)
    lg = logo(170).copy(); lg.putalpha(lg.split()[3].point(lambda v: int(v * la))); im.alpha_composite(lg, (765, DY0 + 10))
    d = ImageDraw.Draw(im, 'RGBA')
    fn = f(BEB, 66); tw = d.textlength('COACH AGZ', font=fn); txt(d, 850 - tw / 2, DY0 + 196, 'COACH AGZ', fn, VGOLD, la)
    fm = f(MONO, 28); tw = d.textlength('@coach.agz', font=fm); txt(d, 850 - tw / 2, DY0 + 270, '@coach.agz', fm, CREAM, la)
    fd = f(MONO, 17); s_ = 'FOR RESEARCH & EDUCATIONAL PURPOSES ONLY'; tw = d.textlength(s_, font=fd)
    txt(d, (W - tw) / 2, DY1 - 18, s_, fd, MUTED, a)
DECK_SCENES = [(17.96, 25.10, scene_results), (25.08, 29.98, scene_blood), (29.96, 36.72, scene_checkins), (36.70, 43.70, scene_comms), (49.92, 99, scene_end)]

# ---------------- captions ----------------
def build_groups():
    G = []; cur = []
    for i, x in enumerate(WORDS):
        if cur:
            prev = WORDS[cur[-1]]
            if len(cur) >= 3 or x['s'] - prev['e'] > 0.28 or prev['w'][-1] in '.,?!' or any(prev['e'] <= b < x['s'] + 0.01 for b in BOUNDS) or len(''.join(WORDS[j]['w'] for j in cur)) + len(x['w']) > 17:
                G.append(cur); cur = []
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
    end = WORDS[lo[-1]]['e'] + 0.5
    nxt = [g for g in GROUPS if WORDS[g[0]]['s'] > WORDS[lo[0]]['s']]
    if t > end and (not nxt or WORDS[nxt[0][0]]['s'] > t): return None
    return lo
def captions(im, t, s):
    if t >= CUT_DUR - 2.0 and t > 49.95: return
    g = group_at(t)
    if not g: return
    d = ImageDraw.Draw(im, 'RGBA')
    ws = [WORDS[i]['w'].upper().strip('.,?!') for i in g]
    size = int(lerp(112, 92, s)); capy = lerp(1384, 788, s)
    while True:
        fn = f(BEB, size); sp = d.textlength(' ', font=fn) + 14; wd = [d.textlength(w, font=fn) for w in ws]; tot = sum(wd) + sp * (len(ws) - 1)
        if tot <= 900: break
        size -= 4
    xs = []; x = (W - tot) / 2
    for w_ in wd: xs.append(x); x += w_ + sp
    act = 0
    for k, i in enumerate(g):
        if WORDS[i]['s'] <= t: act = k
    g0 = WORDS[g[0]]['s']; sc = lerp(0.9, 1, expo((t - g0) / 0.10))
    ch = int(size * 1.4) + 60
    cap = Image.new('RGBA', (W, ch), (0, 0, 0, 0)); cd = ImageDraw.Draw(cap); shd = Image.new('RGBA', (W, ch), (0, 0, 0, 0)); sd = ImageDraw.Draw(shd)
    prev = max(0, act - 1); bt = expo((t - WORDS[g[act]]['s']) / 0.07) if act > 0 else 1
    bx0 = lerp(xs[prev], xs[act], bt) - 16; bx1 = lerp(xs[prev] + wd[prev], xs[act] + wd[act], bt) + 16
    for k, (w_, x_) in enumerate(zip(ws, xs)):
        if k != act: sd.text((x_ + 4, 34), w_, font=fn, fill=(0, 0, 0, 220))
    cap.alpha_composite(shd.filter(ImageFilter.GaussianBlur(6)))
    lit_bar(cd, bx0, 28 + size * 0.02, bx1, 28 + size * 0.98, RED)
    for k, (w_, x_) in enumerate(zip(ws, xs)): cd.text((x_, 28), w_, font=fn, fill=CREAM, stroke_width=0 if k == act else 3, stroke_fill=(0, 0, 0))
    if abs(sc - 1) > 0.002:
        cap = cap.resize((int(W * sc), int(ch * sc)), Image.BICUBIC); ox = int((W - cap.width) / 2); oy = int(capy - 28 - (cap.height - ch) / 2)
    else: ox, oy = 0, int(capy - 28)
    im.alpha_composite(cap, (ox, oy))

# ---------------- frame ----------------
def frame(src, t):
    global GL, DECK
    if DECK is None: DECK = make_deck_bg()
    s = split_amt(t); zA = zoom_a(t)
    # footage transform: A (anchor 540,700, zoom zA) -> B (scale K, src y 420 at top, x 81)
    za, oxa, oya = zA, 540 * (1 - zA), 700 * (1 - zA)
    sc = lerp(za, K, s); ox = lerp(oxa, 81, s); oy = lerp(oya, -SRC_Y * K, s)
    win = [lerp(0, WIN_B[0], s), lerp(0, WIN_B[1], s), lerp(W, WIN_B[2], s), lerp(H, WIN_B[3], s)]
    if s <= 0.001 and abs(sc - 1) < 1e-4: foot = src
    else:
        big = src.resize((int(round(W * sc)), int(round(H * sc))), Image.BICUBIC)
        foot = Image.new('RGB', (W, H), NAVY); foot.paste(big, (int(round(ox)), int(round(oy))))
    if s > 0.001:
        im = DECK.copy()
        m = Image.new('L', (W, H), 0); ImageDraw.Draw(m).rounded_rectangle([int(v) for v in win], radius=int(28 * s), fill=255)
        im.paste(foot, (0, 0), m); im = im.convert('RGBA')
    else: im = foot.convert('RGBA')
    glow = Image.new('RGBA', (W, H), (0, 0, 0, 0)); GL = ImageDraw.Draw(glow, 'RGBA')
    d = ImageDraw.Draw(im, 'RGBA')
    if s > 0.001:   # window frame
        x0, y0, x1, y1 = win
        d.rounded_rectangle([x0, y0 - 40, x1, y1], radius=int(28 * s), outline=A(VGOLD, s), width=3)
        GL.line([(x0 + 20, y1), (x1 - 20, y1)], fill=A(VGOLD, s), width=8)
        d.ellipse([x1 - 46, y1 - 46, x1 - 30, y1 - 30], fill=A(RED, s if int(t * 3) % 2 == 0 else s / 3))
        txt(d, 60, 1522, '@coach.agz', f(MONO, 26), GOLD, s * 0.9)
        for k in range(5):
            on = k == min(4, int(clamp((t - 17.96) / (43.7 - 17.96)) * 4)) if t < 49 else k == 4
            d.rectangle([800 + k * 44, 1536, 834 + k * 44, 1541], fill=A(VGOLD if on else (70, 74, 90), s))
    # top-band widgets (A only)
    text_hook(im, d, t); d = ImageDraw.Draw(im, 'RGBA')
    topic_band(im, d, t, s)
    if s < 0.6:
        if 5.5 <= t < 11.3: w_overnight(im, t)
        if 11.2 <= t < 17.1: w_scan(im, t)
        if 43.8 <= t < 50.2: w_monitor(im, t)
    # deck scenes
    if s > 0.01:
        for t0, t1, fn_ in DECK_SCENES:
            if t0 <= t < t1 + 0.2:
                a = min(1, s * 1.2) * (1 - clamp((t - t1) / 0.16)) * appear(t, t0, 0.14)
                if a <= 0: continue
                lay = Image.new('RGBA', (W, H), (0, 0, 0, 0))
                fn_(lay, t, 1.0)
                dy = lerp(160, 0, s)
                if dy > 0.5: lay = lay.transform((W, H), Image.AFFINE, (1, 0, 0, 0, 1, -dy))
                if a < 1: lay.putalpha(lay.split()[3].point(lambda v: int(v * a)))
                im.alpha_composite(lay)
    # bloom (screen blend), computed at 1/4 res
    if glow.getbbox():
        sm = glow.resize((W // 4, H // 4), Image.BILINEAR)
        g1 = np.asarray(sm.filter(ImageFilter.GaussianBlur(3.5))).astype(np.float32) / 255; g2 = np.asarray(sm.filter(ImageFilter.GaussianBlur(10))).astype(np.float32) / 255
        prem = np.clip(g1[..., :3] * g1[..., 3:] * 2.3 + g2[..., :3] * g2[..., 3:] * 1.8, 0, 1)
        prem = np.asarray(Image.fromarray((prem * 255).astype(np.uint8)).resize((W, H), Image.BILINEAR)).astype(np.float32) / 255
        b = np.asarray(im.convert('RGB')).astype(np.float32) / 255
        im = Image.fromarray(((1 - (1 - b) * (1 - prem)) * 255).astype(np.uint8)).convert('RGBA')
    GL = None
    captions(im, t, s)
    d = ImageDraw.Draw(im, 'RGBA'); d.rectangle([0, 0, 7, H], fill=GOLD)
    return im.convert('RGB')
GROUPS = build_groups()
if __name__ == '__main__':
    mode = sys.argv[2]
    if mode == 'stills':
        for tt in [float(x) for x in sys.argv[3:]]:
            ts = min(tt, CUT_DUR - 0.04)
            subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', f'{ts:.3f}', '-i', T + 'cut.mov', '-frames:v', '1', T + 'qc/_src.png'])
            frame(Image.open(T + 'qc/_src.png').convert('RGB'), tt).resize((540, 960)).save(T + f'qc/st_{tt:05.2f}.jpg', quality=88)
        sys.exit()
    n0, n1 = int(sys.argv[3]), int(sys.argv[4]); out = sys.argv[5]
    dec = subprocess.Popen(['ffmpeg', '-v', 'error', '-ss', f'{n0 / FPS:.4f}', '-i', T + 'cut.mov', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], stdout=subprocess.PIPE)
    enc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-crf', '12', '-preset', 'fast', '-pix_fmt', 'yuv420p', out], stdin=subprocess.PIPE)
    last = None
    for n in range(n0, n1):
        buf = dec.stdout.read(W * H * 3)
        if len(buf) < W * H * 3:
            if last is None: print('short', n); break
            srcf = last                                  # freeze the final frame for the end card hold
        else: srcf = Image.frombuffer('RGB', (W, H), buf).copy(); last = srcf
        enc.stdin.write(frame(srcf, n / FPS).tobytes())
    enc.stdin.close(); enc.wait(); dec.kill(); print('done', n0, n1)
