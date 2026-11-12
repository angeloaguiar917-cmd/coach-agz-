# Full test 02: "Tren / organs" Reel. 1080x1920, 30 fps.
# Usage: python3 render.py <scratch> stills t1 t2 ...       (t = OUTPUT seconds)
#        python3 render.py <scratch> range n0 n1 out.mp4    (output frame range)
# All overlay timings below are SOURCE seconds (from words_src.json); output frames map to source via KEEP.
import json, subprocess, sys, math
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops

S = sys.argv[1]; F = S + '/fonts/'; WD = S + '/w/'; SRC = S + '/src/src.mov'
W, H, FPS = 1080, 1920, 30
WORDS = json.load(open(WD + 'words_src.json'))
KEEP = json.load(open(WD + 'trim.json'))['keep']
OUT_DUR = sum(b - a for a, b in KEEP)
N_OUT = int(round(OUT_DUR * FPS))

def new_to_old(tn):
    acc = 0
    for a, b in KEEP:
        if tn < acc + (b - a) - 1e-9: return a + (tn - acc)
        acc += b - a
    return KEEP[-1][1] - 1 / FPS
def old_to_new(to):
    acc = 0
    for a, b in KEEP:
        if to < b: return acc + max(0, to - a)
        acc += b - a
    return acc
MID_SRC = new_to_old(OUT_DUR / 2)

# ---------------- palette / type ----------------
GOLD = (201, 169, 110); CREAM = (244, 241, 234); NAVY = (14, 17, 23); BG2 = (24, 26, 34)
RED = (255, 34, 28); VGOLD = (255, 194, 26); CYAN = (0, 229, 255); GREEN = (30, 255, 110)
DEEP = (2, 3, 8); INK = (6, 8, 14); WHITE = (255, 255, 255); MUTED = (124, 124, 130); AMBER = (240, 160, 48); BLUE = (79, 163, 224)
MONO = 'JBMono-500.ttf'; MONOB = 'JBMono-700.ttf'; BEB = 'BebasNeue.ttf'; DMB = 'DMSans-700.ttf'; DMR = 'DMSans-400.ttf'
BC7 = 'BarlowCond-700.ttf'; BC6 = 'BarlowCond-600.ttf'
_fc = {}
def f(n, s):
    k = (n, int(s))
    if k not in _fc: _fc[k] = ImageFont.truetype(F + n, int(s))
    return _fc[k]
def clamp(x, a=0, b=1): return max(a, min(b, x))
def expo(x): x = clamp(x); return 1 if x >= 1 else 1 - 2 ** (-10 * x)
def ease_io(x): x = clamp(x); return 4 * x ** 3 if x < .5 else 1 - (-2 * x + 2) ** 3 / 2
def back(x):  # heavy landing: slight undershoot settle, no bounce
    x = clamp(x); return 1 - (1 - x) ** 3
def lerp(a, b, t): return a + (b - a) * t
def A(c, a): return tuple(c[:3]) + (int(clamp(a) * 255),)
def appear(t, t0, dur=0.16): return expo((t - t0) / dur)
def window(t, t0, t1, fi=0.18, fo=0.16): return min(expo((t - t0) / fi), 1 - clamp((t - t1) / fo))
GL = None  # glow layer draw (bloom)

# ---------------- primitives ----------------
def brackets(d, x0, y0, x1, y1, col, L=34, w=4):
    for (cx, cy, sx, sy) in [(x0, y0, 1, 1), (x1, y0, -1, 1), (x0, y1, 1, -1), (x1, y1, -1, -1)]:
        d.line([(cx, cy), (cx + sx * L, cy)], fill=col, width=w); d.line([(cx, cy), (cx, cy + sy * L)], fill=col, width=w)
def lit_bar(d, x0, y0, x1, y1, col, a=1.0):
    h = max(1, int(y1 - y0))
    if x1 <= x0: return
    for i in range(h):
        k = i / h; c = tuple(int(min(255, v * (1.18 - 0.36 * k) + (40 if k < 0.12 else 0))) for v in col)
        d.line([(x0, y0 + i), (x1, y0 + i)], fill=c + (int(255 * a),))
def tag(d, x, y, label, col=RED, size=30, a=1.0, glow=True):
    if a <= 0: return x
    fn = f(MONOB, size); tw = d.textlength(label, font=fn); h = size + 16
    lit_bar(d, x, y, x + tw + 24, y + h, col, a)
    d.text((x + 12, y + 5), label, font=fn, fill=A(WHITE if col not in (VGOLD, GREEN, CYAN, WHITE) else INK, a))
    if GL and glow: GL.rectangle([x - 4, y - 4, x + tw + 28, y + h + 4], outline=A(col, a), width=8)
    return x + tw + 24
def txt(d, x, y, s, font, col, a=1.0, anchor=None):
    if a > 0: d.text((x, y), s, font=font, fill=A(col, a), anchor=anchor)
def arrow(d, x0, y0, x1, y1, col, w=5, a=1.0, L=20):
    d.line([(x0, y0), (x1, y1)], fill=A(col, a), width=w)
    ang = math.atan2(y1 - y0, x1 - x0)
    d.polygon([(x1, y1), (x1 - L * math.cos(ang - 0.45), y1 - L * math.sin(ang - 0.45)), (x1 - L * math.cos(ang + 0.45), y1 - L * math.sin(ang + 0.45))], fill=A(col, a))
def check(d, x, y, col, s=1.0, a=1.0):
    if a <= 0: return
    pts = [(x, y + 16 * s), (x + 10 * s, y + 28 * s), (x + 30 * s, y + 2 * s)]
    d.line(pts, fill=A(col, a), width=int(6 * s), joint='curve')
    if GL: GL.line(pts, fill=A(col, a), width=int(12 * s))
def cross(d, x, y, col, s=1.0, a=1.0):
    if a <= 0: return
    d.line([(x, y), (x + 28 * s, y + 28 * s)], fill=A(col, a), width=int(6 * s)); d.line([(x + 28 * s, y), (x, y + 28 * s)], fill=A(col, a), width=int(6 * s))
    if GL: GL.line([(x, y), (x + 28 * s, y + 28 * s)], fill=A(col, a), width=12); GL.line([(x + 28 * s, y), (x, y + 28 * s)], fill=A(col, a), width=12)
def frosted(im, box, dark=0.86, blur=10, col=DEEP):
    x0, y0, x1, y1 = [int(v) for v in box]
    x0 = max(0, x0); y0 = max(0, y0); x1 = min(W, x1); y1 = min(H, y1)
    if x1 <= x0 or y1 <= y0: return
    reg = im.crop((x0, y0, x1, y1)).convert('RGB').filter(ImageFilter.GaussianBlur(blur))
    im.paste(Image.blend(reg, Image.new('RGB', reg.size, col), dark).convert('RGBA'), (x0, y0))
def polyline(d, pts, col, w, a=1.0, glow=True):
    if len(pts) < 2 or a <= 0: return
    d.line(pts, fill=A(col, a), width=w, joint='curve')
    if GL and glow: GL.line(pts, fill=A(col, a), width=w * 2)
def partial(pts, p):
    """first fraction p of a polyline"""
    if p <= 0: return pts[:1]
    if p >= 1: return pts
    n = (len(pts) - 1) * p; i = int(n); q = n - i
    out = pts[:i + 1]
    if i + 1 < len(pts): out = out + [(lerp(pts[i][0], pts[i + 1][0], q), lerp(pts[i][1], pts[i + 1][1], q))]
    return out
def kicker(d, x, y, label, col, t, t0, size=28):
    p = expo((t - t0) / 0.18)
    if p <= 0: return
    d.line([(x, y + size * 0.55), (x + 44 * p, y + size * 0.55)], fill=A(col, 1), width=4)
    q = clamp((t - t0 - 0.08) / 0.2)
    if q > 0:
        s = label[:max(1, int(len(label) * q))]
        txt(d, x + 58, y, s, f(BC7, size + 4), col, 1)
def header(d, x0, y0, x1, left, right, t, col=VGOLD):
    d.ellipse([x0 + 26, y0 + 26, x0 + 42, y0 + 42], fill=A(RED, 1 if int(t * 4) % 2 == 0 else 0.35))
    txt(d, x0 + 56, y0 + 16, left, f(MONO, 28), WHITE)
    fr = f(MONO, 28); tw = d.textlength(right, font=fr); txt(d, x1 - 30 - tw, y0 + 16, right, fr, col)

# ---------------- layout (footage placement) ----------------
SHIFT = 420           # in 'shift' mode the footage slides up so the face stays whole above the graphic zone
PIPR = (650, 196, 1040, 890)  # picture-in-picture window
MODES = [(0, 'full'), (11.22, 'shift'), (20.92, 'full'), (29.0, 'pip'), (34.42, 'shift'), (39.85, 'full'),
         (44.62, 'shift'), (55.12, 'full'), (58.12, 'shift'), (71.12, 'full'), (74.40, 'shift')]
ZOOM = [(0, 1.0), (6.9, 1.08), (9.18, 1.15), (10.66, 1.08), (20.92, 1.0), (25.7, 1.06), (27.88, 1.12), (29.0, 1.0),
        (39.85, 1.0), (40.48, 1.10), (44.62, 1.0), (55.12, 1.07), (56.38, 1.12), (58.12, 1.0), (71.12, 1.06), (74.4, 1.0)]
TR = 0.32
def zoom_at(t):
    z = 1.0
    for t0, v in ZOOM:
        if t >= t0: z = v
    return z
def mode_params(m, t):
    if m == 'full':
        z = zoom_at(t); return (z, (W - W * z) / 2, (H - H * z) * 0.42)
    if m == 'shift': return (1.0, 0.0, -SHIFT)
    if m == 'pip':
        k = (PIPR[2] - PIPR[0]) / W; return (k, PIPR[0], PIPR[1])
def layout(t):
    i = max(j for j, (t0, _) in enumerate(MODES) if t >= t0)
    t0, m = MODES[i]; cur = mode_params(m, t)
    if i > 0 and t - t0 < TR:
        prev = mode_params(MODES[i - 1][1], t0 - 1e-3); p = ease_io((t - t0) / TR)
        return tuple(lerp(a, b, p) for a, b in zip(prev, cur)), m, MODES[i - 1][1], p
    return cur, m, m, 1.0
def amount(t, name):
    (k, ox, oy), m, pm, p = layout(t)
    a = 1.0 if m == name else 0.0; b = 1.0 if pm == name else 0.0
    return lerp(b, a, p)

def background():
    bg = Image.new('RGB', (W, H), NAVY)
    yy, xx = np.mgrid[0:H, 0:W]
    g = np.exp(-(((xx - 980) / 700) ** 2 + ((yy - 300) / 700) ** 2)) * 18
    arr = np.asarray(bg).astype(np.float32) + g[..., None] * np.array([1.0, 0.85, 0.6])
    # fine scan-line texture
    arr[::4] *= 0.93
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
BG = None

# ---------------- text hook (frame 0) ----------------
HOOK_END = 6.0
def hook(im, t):
    if t >= HOOK_END + 0.15: return
    a = 1 - clamp((t - HOOK_END) / 0.15)
    s = lerp(1.0, 1.04, clamp(t / HOOK_END))
    lay = Image.new('RGBA', (W, 460), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    f1 = f(BC7, 150); f2 = f(BC7, 92)
    p1 = [('3 ', CREAM), ('TREN', VGOLD), (' rules', CREAM)]; l2 = 'before your organs pay'
    w1 = sum(d.textlength(s_, font=f1) for s_, _ in p1); w2 = d.textlength(l2, font=f2)
    bw = max(w1, w2) + 80; cx = 500
    x0 = cx - bw / 2; d.rounded_rectangle([x0, 30, x0 + bw, 330], radius=22, fill=(8, 10, 16, 222))
    d.rectangle([x0, 30, x0 + 8, 330], fill=GOLD)
    x = cx - w1 / 2
    for s_, c in p1:
        d.text((x, 46), s_, font=f1, fill=c); x += d.textlength(s_, font=f1)
    d.text((cx - w2 / 2, 210), l2, font=f2, fill=CREAM)
    lay = lay.resize((int(W * s), int(460 * s)), Image.BICUBIC)
    if a < 1: lay.putalpha(lay.split()[3].point(lambda v: int(v * a)))
    im.alpha_composite(lay, (int(500 - 500 * s), int(220 - 30 * s)))

# ---------------- topic band (hook exit -> midpoint) + rule chips ----------------
def band(im, d, t):
    if t < HOOK_END or t > MID_SRC + 0.15: return
    a = min(clamp((t - HOOK_END) / 0.15), 1 - clamp((t - MID_SRC) / 0.15)) * clamp(1 - 2 * amount(t, 'pip'))
    if a <= 0.01: return
    y0, y1 = 212, 372
    d.rectangle([8, y0, W, y1], fill=NAVY + (int(228 * a),))
    d.line([(64, 244), (108, 244)], fill=A(GOLD, a), width=4); txt(d, 122, 228, '@coach.agz', f(MONO, 28), GOLD, a)
    fn = f(BC7, 84); x = 64
    for s_, c in [('3 ', CREAM), ('TREN', VGOLD), (' rules', CREAM)]:
        txt(d, x, 268, s_, fn, c, a); x += d.textlength(s_, font=fn)
    # chips
    for i, (lab, ton) in enumerate([('01', 10.66), ('02', 25.7), ('03', 40.5)]):
        cx0 = 640 + i * 128; cy0 = 252; cx1 = cx0 + 104; cy1 = cy0 + 92
        warn = 7.18 <= t < 10.66 and i == 2
        active = (t >= ton) and (i == 2 or t < [25.7, 40.5, 99][i])
        done = t >= [25.7, 40.5, 99][i]
        if warn:
            pul = 0.65 + 0.35 * math.sin(t * 10)
            lit_bar(d, cx0, cy0, cx1, cy1, RED, a * pul); GL.rectangle([cx0 - 4, cy0 - 4, cx1 + 4, cy1 + 4], outline=A(RED, a), width=10)
            txt(d, cx0 + 52, cy0 + 46, lab, f(BEB, 70), WHITE, a, 'mm')
        elif active:
            p = appear(t, ton, 0.12); lit_bar(d, cx0, cy0, cx1, cy1, VGOLD, a * p); GL.rectangle([cx0 - 4, cy0 - 4, cx1 + 4, cy1 + 4], outline=A(VGOLD, a * p), width=10)
            txt(d, cx0 + 52, cy0 + 46, lab, f(BEB, 70), INK, a * p, 'mm')
        else:
            d.rectangle([cx0, cy0, cx1, cy1], outline=A((90, 94, 110), a), width=3)
            txt(d, cx0 + 52, cy0 + 46, lab, f(BEB, 70), (110, 112, 125) if not done else GREEN, a, 'mm')
    if 7.18 <= t < 10.66:
        b = a * appear(t, 10.04, 0.12) * (1 - clamp((t - 10.5) / 0.16))
        if b > 0: tag(d, 640, 384, 'WHERE MOST GO WRONG', RED, 26, b)

# ---------------- SCENE A: dose-response chart (split) ----------------
P = (40, 990, 1040, 1490)
def panel_frame(im, d, t, t0, t1, left, right, col=VGOLD, style='brackets'):
    al = window(t, t0, t1, 0.2, 0.16)
    if al <= 0: return 0
    x0, y0, x1, y1 = P
    # gold edge rule grows into the panel top border (handoff from the left brand rule)
    gp = expo((t - t0) / 0.28)
    frosted(im, (x0, y0, x1, y1), 0.9, 8)
    d.rectangle([x0, y0, x1, y1], fill=None)
    if style == 'brackets':
        d.line([(0, y0), (lerp(0, x1, gp), y0)], fill=A(col, al), width=4)
        GL.line([(0, y0), (lerp(0, x1, gp), y0)], fill=A(col, al), width=8)
        brackets(d, x0, y0, x1, y1, A(col, al), 44, 6); brackets(GL, x0, y0, x1, y1, A(col, al), 44, 12)
    else:  # scope style
        d.rounded_rectangle([x0, y0, x1, y1], radius=26, outline=A(col, al), width=4)
        GL.rounded_rectangle([x0, y0, x1, y1], radius=26, outline=A(col, al * 0.8), width=8)
    header(d, x0, y0, x1, left, right, t, col)
    return al
def curve_pts(fn, x0, x1, y0, y1, n=60, xmax=1.0):
    return [(lerp(x0, x1, i / n * xmax), lerp(y1, y0, fn(i / n * xmax))) for i in range(n + 1)]
def scene_dose(im, d, t):
    t0, t1 = 11.3, 20.92
    al = panel_frame(im, d, t, t0, t1, 'DOSE vs RESPONSE', 'RULE 01')
    if al <= 0: return
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); dd = ImageDraw.Draw(lay)
    gx0, gx1, gy0, gy1 = 130, 990, 1090, 1400
    ax = expo((t - 11.5) / 0.35)
    dd.line([(gx0, gy1), (lerp(gx0, gx1, ax), gy1)], fill=A((150, 154, 170), 1), width=3)
    dd.line([(gx0, gy1), (gx0, lerp(gy1, gy0, ax))], fill=A((150, 154, 170), 1), width=3)
    for k in range(1, 4): dd.line([(gx0, gy1 - k * 75), (lerp(gx0, gx1, ax), gy1 - k * 75)], fill=A((44, 48, 64), 1), width=1)
    txt(dd, gx1, gy1 + 12, 'ANDROGENIC EXPOSURE', f(MONO, 24), MUTED, ax, 'ra')
    txt(dd, gx0 - 16, gy0 - 4, 'RESPONSE', f(MONO, 22), MUTED, ax, 'ra') if False else None
    musc = lambda x: 0.78 * (1 - math.exp(-4.2 * x))
    side = lambda x: 0.92 * x ** 2.7
    # dose marker
    if t >= 12.28:
        xm = 0.18 if t < 12.68 else lerp(0.18, 0.45, expo((t - 12.68) / 0.35))
        if t >= 17.14: xm = lerp(0.45, 0.9, expo((t - 17.14) / 0.6))
        X = lerp(gx0, gx1, xm)
        for yy in range(gy0, gy1, 18): dd.line([(X, yy), (X, yy + 9)], fill=A(WHITE, 0.7), width=2)
        tag(dd, X - 44, gy1 - 30, 'DOSE', WHITE, 22, appear(t, 12.28), glow=False)
        if t >= 13.32:
            Y = lerp(gy1, gy0, musc(xm)); dd.ellipse([X - 11, Y - 11, X + 11, Y + 11], fill=A(VGOLD, 1)); GL.ellipse([X - 20, Y - 20, X + 20, Y + 20], fill=A(VGOLD, 1))
    if t >= 13.32:
        p = expo((t - 13.32) / 0.9); pts = curve_pts(musc, gx0, gx1, gy0, gy1)
        polyline(dd, partial(pts, p), VGOLD, 7)
        txt(dd, gx0 + 20, lerp(gy1, gy0, musc(0.2)) - 64, 'MUSCLE', f(BC7, 42), VGOLD, appear(t, 13.6))
    if 14.14 <= t < 17.0:
        b = appear(t, 14.14) * (1 - clamp((t - 16.85) / 0.15))
        x = tag(dd, gx0 + 20, gy0 + 4, 'TREN', VGOLD, 28, b); tag(dd, x + 10, gy0 + 4, 'POTENT AR AGONIST', CYAN, 28, b)
    if t >= 18.32:   # plateau bracket
        b = appear(t, 18.32, 0.14); xa = lerp(gx0, gx1, 0.55); ya = lerp(gy1, gy0, musc(1)) - 26
        brackets(dd, xa, ya - 6, gx1, ya + 50, A(VGOLD, b), 22, 5); brackets(GL, xa, ya - 6, gx1, ya + 50, A(VGOLD, b), 22, 10)
        tag(dd, xa, ya - 60, 'PLATEAU', VGOLD, 26, b)
    if t >= 19.14:
        p = expo((t - 19.14) / 1.0); pts = curve_pts(side, gx0, gx1, gy0, gy1)
        polyline(dd, partial(pts, p), RED, 7)
        if p > 0.9: txt(dd, gx1 - 250, gy0 + 60, 'SIDE EFFECTS', f(BC7, 42), RED, appear(t, 19.9))
    if t >= 20.2:   # cost exceeds return: shade the gap past the crossover
        b = appear(t, 20.2, 0.2); xc = 0.79
        poly = curve_pts(side, gx0, gx1, gy0, gy1, 30, 1)[int(30 * xc):] + list(reversed(curve_pts(musc, gx0, gx1, gy0, gy1, 30, 1)[int(30 * xc):]))
        dd.polygon(poly, fill=A(RED, 0.28 * b))
        tag(dd, gx0 + 380, gy1 - 120, 'COST > RETURN', RED, 30, b)
    txt(dd, P[2] - 24, P[3] - 34, 'ILLUSTRATIVE', f(MONO, 20), MUTED, 1, 'ra')
    pin = expo((t - t0) / 0.22)
    if pin < 1: lay = lay.filter(ImageFilter.GaussianBlur(6 * (1 - pin)))
    lay.putalpha(lay.split()[3].point(lambda v: int(v * al)))
    im.alpha_composite(lay)

# ---------------- SCENE B: recovery / appetite / sleep gauges (top HUD) ----------------
def gauge(d, cx, cy, r, val, label, a, col):
    frosted_circle = None
    d.ellipse([cx - r - 10, cy - r - 10, cx + r + 10, cy + r + 10], fill=A(DEEP, 0.86 * a))
    d.arc([cx - r, cy - r, cx + r, cy + r], 150, 390, fill=A((60, 64, 80), a), width=10)
    e = 150 + 240 * clamp(val)
    d.arc([cx - r, cy - r, cx + r, cy + r], 150, e, fill=A(col, a), width=10)
    GL.arc([cx - r, cy - r, cx + r, cy + r], 150, e, fill=A(col, a), width=16)
    ang = math.radians(e); d.line([(cx, cy), (cx + (r - 18) * math.cos(ang), cy + (r - 18) * math.sin(ang))], fill=A(WHITE, a), width=4)
    d.ellipse([cx - 6, cy - 6, cx + 6, cy + 6], fill=A(WHITE, a))
    fn = f(MONOB, 26); tw = d.textlength(label, font=fn)
    d.rounded_rectangle([cx - tw / 2 - 12, cy + r + 2, cx + tw / 2 + 12, cy + r + 40], radius=6, fill=A(DEEP, 0.88 * a))
    txt(d, cx, cy + r + 6, label, fn, WHITE, a, 'mt')
def scene_gauges(im, d, t):
    if not (21.6 <= t < 25.75): return
    for i, (lab, t_on) in enumerate([('RECOVERY', 21.68), ('APPETITE', 22.28), ('SLEEP', 23.12)]):
        a = appear(t, t_on, 0.12) * (1 - clamp((t - 25.55) / 0.16))
        if a <= 0: continue
        v = 0.86 if t < 23.9 else lerp(0.86, 0.14, expo((t - 23.9 - i * 0.08) / 0.55))
        col = GREEN if v > 0.6 else (AMBER if v > 0.32 else RED)
        cx = 220 + i * 320
        gauge(d, cx, 478, 76, v, lab, a, col)
        if t >= 24.72: tag(d, cx + 40, 392, 'LOW', RED, 26, appear(t, 24.72 + i * 0.06) * a)

# ---------------- SCENE C: ECG + NON-NEGOTIABLE pill ----------------
def ecg_wave(x):  # one beat shape over [0,1]
    if 0.30 < x < 0.36: return -0.25 * math.sin((x - 0.30) / 0.06 * math.pi)
    if 0.40 < x < 0.44: return 0.25 * (x - 0.40) / 0.04
    if 0.44 <= x < 0.48: return 0.25 - 1.6 * (x - 0.44) / 0.04
    if 0.48 <= x < 0.52: return -1.35 + 1.6 * (x - 0.48) / 0.04
    if 0.62 < x < 0.74: return -0.3 * math.sin((x - 0.62) / 0.12 * math.pi)
    return 0
def ecg_line(d, x0, x1, ymid, amp, t, col, a, speed=1.0, chaos=0.0, beat=260):
    pts = []
    head = (t * 420 * speed) % (x1 - x0 + 200)
    for x in range(int(x0), int(x1), 3):
        ph = ((x - x0) % beat) / beat
        y = ecg_wave(ph)
        if chaos > 0: y = y * (1 - chaos) + chaos * (math.sin(x * 0.11 + t * 30) * 0.9 + math.sin(x * 0.037) * 0.5)
        pts.append((x, ymid + y * amp))
    # sweep reveal: bright near the head, fading behind
    for i in range(len(pts) - 1):
        dx = (pts[i][0] - x0) - head
        k = 1 if dx < 0 and dx > -(x1 - x0) * 0.8 else 0.18
        if dx < 0: k = max(0.18, 1 + dx / ((x1 - x0) * 0.8))
        d.line([pts[i], pts[i + 1]], fill=A(col, a * k), width=4)
    hx = x0 + head
    if hx < x1:
        GL.ellipse([hx - 14, ymid - 14, hx + 14, ymid + 14], fill=A(col, a))
def scene_cardio_top(im, d, t):
    if not (25.7 <= t < 29.0): return
    a = appear(t, 25.75, 0.2) * (1 - clamp((t - 28.84) / 0.16))
    ecg_line(d, 40, 1040, 470, 70, t, CYAN, a)
    if t >= 27.9:
        p = back((t - 27.9) / 0.18); x = lerp(-520, 64, p)
        fn = f(BEB, 66); lab = 'NON-NEGOTIABLE'; tw = d.textlength(lab, font=fn)
        lit_bar(d, x, 392, x + tw + 150, 470, VGOLD, a); txt(d, x + 22, 398, lab, fn, INK, a)
        txt(d, x + tw + 44, 410, '02', f(MONOB, 40), INK, a)
        GL.rectangle([x - 4, 388, x + tw + 154, 474], outline=A(VGOLD, a), width=10)

# ---------------- SCENE D: cardio dashboard (PiP) ----------------
MARKERS = [('BLOOD PRESSURE', 29.86), ('APOB', 30.66), ('CHOLESTEROL', 31.34), ('HEMATOCRIT', 32.22), ('CARDIAC FUNCTION', 33.38)]
def scene_dash(im, d, t):
    pa = amount(t, 'pip')
    a = clamp((pa - 0.5) / 0.5)   # content only once the footage has mostly moved into the window
    if a <= 0.01 or not (28.9 <= t < 34.9): return
    kicker(d, 64, 214, 'CARDIOVASCULAR', VGOLD, t, 29.05)
    txt(d, 64, 262, 'RULE 02', f(BEB, 120), CREAM, a * appear(t, 29.15))
    txt(d, 64, 384, 'MONITOR PANEL', f(MONO, 28), MUTED, a * appear(t, 29.3))
    # ECG continues from the previous beat (handoff), confined to the left column
    d.rounded_rectangle([56, 450, 620, 700], radius=16, fill=A((10, 14, 24), 0.95 * a), outline=A((50, 54, 70), a), width=2)
    for k in range(1, 5): d.line([(60, 450 + k * 50), (616, 450 + k * 50)], fill=A((30, 34, 48), a), width=1)
    ecg_line(d, 70, 610, 590, 70, t, CYAN, a, 0.8, beat=180)
    txt(d, 76, 462, 'ECG', f(MONOB, 22), CYAN, a)
    hb = 0.5 + 0.5 * math.sin(t * 7.5)
    d.ellipse([566, 466, 590, 490], fill=A(RED, a * (0.5 + 0.5 * hb))); GL.ellipse([556, 456, 600, 500], fill=A(RED, a * hb))
    # PiP frame
    x0, y0, x1, y1 = PIPR
    d.rounded_rectangle([x0 - 3, y0 - 3, x1 + 3, y1 + 3], radius=24, outline=A(VGOLD, a), width=4)
    GL.rounded_rectangle([x0 - 3, y0 - 3, x1 + 3, y1 + 3], radius=24, outline=A(VGOLD, a * 0.7), width=8)
    d.ellipse([x0 + 20, y0 + 20, x0 + 36, y0 + 36], fill=A(RED, a if int(t * 4) % 2 == 0 else a * 0.3)); txt(d, x0 + 46, y0 + 14, 'LIVE', f(MONOB, 24), WHITE, a)
    # marker rows
    ry = 960
    txt(d, 64, ry - 46, 'MARKER', f(MONO, 24), MUTED, a); txt(d, 470, ry - 46, 'LOW', f(MONO, 22), BLUE, a)
    txt(d, 665, ry - 46, 'IN RANGE', f(MONO, 22), GREEN, a, 'ma'); txt(d, 860, ry - 46, 'HIGH', f(MONO, 22), AMBER, a, 'ra')
    for i, (nm, tt) in enumerate(MARKERS):
        y = ry + i * 72; b = a * appear(t, tt, 0.14)
        d.line([(56, y + 64), (1024, y + 64)], fill=A((40, 44, 58), a), width=1)
        txt(d, 64, y + 6, nm, f(BC7, 46), WHITE if b > 0 else (90, 92, 104), max(b, a * 0.5))
        # spectrum bar
        bx0, bx1 = 470, 860
        for k in range(bx1 - bx0):
            u = k / (bx1 - bx0); c = BLUE if u < 0.3 else (GREEN if u < 0.68 else AMBER)
            d.line([(bx0 + k, y + 24), (bx0 + k, y + 40)], fill=A(c, a * (0.25 + 0.6 * b)))
        if b > 0:
            u = 0.5 if t > tt + 0.5 else lerp(0.95, 0.5, expo((t - tt) / 0.45))
            mx = lerp(bx0, bx1, u); d.polygon([(mx - 10, y + 12), (mx + 10, y + 12), (mx, y + 26)], fill=A(WHITE, b))
            d.line([(mx, y + 20), (mx, y + 46)], fill=A(WHITE, b), width=3)
            check(d, 930, y + 10, GREEN, 1.0, a * appear(t, tt + 0.4, 0.12))
    txt(d, 1024, ry + 5 * 72 + 6, 'TARGET ZONE · ILLUSTRATIVE', f(MONO, 20), MUTED, a, 'ra')

# ---------------- SCENE E: outside vs inside comparison (split) ----------------
def scene_compare(im, d, t):
    t0, t1 = 34.5, 39.85
    al = window(t, t0, t1, 0.2, 0.16)
    if al <= 0: return
    x0, y0, x1, y1 = P
    frosted(im, P, 0.9, 8)
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); dd = ImageDraw.Draw(lay)
    cols = [(60, 520, 'OUTSIDE', VGOLD, 34.6), (560, 1020, 'INSIDE', CYAN, 37.14)]
    for (cx0, cx1, lab, col, ton) in cols:
        p = expo((t - ton) / 0.3)
        dd.line([(cx0, y0 + 18), (lerp(cx0, cx1, p), y0 + 18)], fill=A(col, 1), width=5); GL.line([(cx0, y0 + 18), (lerp(cx0, cx1, p), y0 + 18)], fill=A(col, al), width=10)
        txt(dd, cx0, y0 + 32, lab, f(BEB, 58), col, appear(t, ton + 0.05))
    # OUTSIDE: mirror check -> physique score bar
    a = appear(t, 35.24)
    if a > 0:
        dd.rounded_rectangle([60, 1110, 520, 1330], radius=14, fill=A((10, 14, 24), 0.95), outline=A((70, 74, 90), 1), width=2)
        txt(dd, 84, 1126, 'MIRROR', f(MONO, 26), MUTED, a)
        fr = lerp(0, 0.94, expo((t - 35.3) / 0.6))
        dd.rectangle([84, 1180, 496, 1216], outline=A((70, 74, 90), a), width=2); lit_bar(dd, 87, 1183, lerp(87, 493, fr), 1213, VGOLD, a)
        txt(dd, 84, 1236, 'SIZE · DRY · FULL', f(MONO, 24), CREAM, a)
        check(dd, 460, 1240, GREEN, 1.0, appear(t, 35.6))
    # INSIDE: artery cross-section narrowing
    b = appear(t, 37.24)
    if b > 0:
        cx, cy, R = 700, 1260, 118
        dd.ellipse([cx - R, cy - R, cx + R, cy + R], fill=A((10, 14, 24), b), outline=A(CYAN, b), width=6)
        GL.ellipse([cx - R, cy - R, cx + R, cy + R], outline=A(CYAN, b), width=12)
        narrow = 0 if t < 37.88 else expo((t - 37.88) / 0.7)
        r_in = lerp(86, 40, narrow); ox = lerp(0, 34, narrow)
        # plaque fills between wall and lumen
        dd.ellipse([cx - R + 8, cy - R + 8, cx + R - 8, cy + R - 8], fill=A(AMBER if narrow > 0 else (30, 40, 60), b * (0.25 + 0.6 * narrow)))
        dd.ellipse([cx - r_in + ox, cy - r_in - ox * 0.4, cx + r_in + ox, cy + r_in - ox * 0.4], fill=A((120, 10, 18), b), outline=A(RED, b * narrow), width=3)
        txt(dd, cx, cy + R + 8, 'ARTERY · CROSS-SECTION', f(MONO, 20), MUTED, b, 'ma')
        if narrow > 0.3: tag(dd, 840, 1140, 'NARROWED', RED, 26, appear(t, 38.1))
        # ECG strip, goes irregular on "heart attack"
        chaos = 0 if t < 39.16 else expo((t - 39.16) / 0.25)
        ecg_line(dd, 840, 1020, 1300, 50, t, RED if chaos > 0 else GREEN, b, 1.2, chaos, beat=90)
        if t >= 39.16: tag(dd, 840, 1360, 'EVENT', RED, 28, appear(t, 39.16, 0.1))
    lay.putalpha(lay.split()[3].point(lambda v: int(v * al)))
    im.alpha_composite(lay)
    d.rectangle([x0, y0, x1, y1], outline=A((80, 84, 100), 0.6 * al), width=2)
    d.line([(540, y0 + 30), (540, y1 - 30)], fill=A((70, 74, 90), al), width=2)

# ---------------- SCENE F: side rail "03" + dose dial ----------------
def scene_rail(im, d, t):
    if not (40.48 <= t < 44.75): return
    a = appear(t, 40.5, 0.12) * (1 - clamp((t - 44.55) / 0.16))
    x0 = 30; frosted(im, (x0, 560, 250, 1060), 0.8, 12)
    d.rectangle([x0, 560, 250, 1060], outline=A((70, 74, 90), a), width=2)
    d.line([(x0, 560), (x0, lerp(560, 1060, expo((t - 40.5) / 0.25)))], fill=A(VGOLD, a), width=6)
    GL.line([(x0, 560), (x0, 1060)], fill=A(VGOLD, a), width=10)
    txt(d, 56, 578, 'RULE', f(MONOB, 26), VGOLD, a)
    p = back((t - 40.64) / 0.16); s = lerp(1.25, 1.0, p)
    txt(d, 140, 720, '03', f(BEB, int(190 * s)), VGOLD, a * p, 'mm')
    # dose dial
    cx, cy, r = 140, 930, 70
    d.arc([cx - r, cy - r, cx + r, cy + r], 180, 360, fill=A((60, 64, 80), a), width=12)
    d.arc([cx - r, cy - r, cx + r, cy + r], 180, 250, fill=A(GREEN, a), width=12)
    d.arc([cx - r, cy - r, cx + r, cy + r], 250, 300, fill=A(AMBER, a), width=12)
    d.arc([cx - r, cy - r, cx + r, cy + r], 300, 360, fill=A(RED, a), width=12)
    GL.arc([cx - r, cy - r, cx + r, cy + r], 300, 360, fill=A(RED, a), width=18)
    v = 0.3 if t < 43.78 else lerp(0.3, 0.93, expo((t - 43.78) / 0.25))
    ang = math.radians(180 + 180 * v)
    d.line([(cx, cy), (cx + (r - 6) * math.cos(ang), cy + (r - 6) * math.sin(ang))], fill=A(WHITE, a), width=5)
    d.ellipse([cx - 8, cy - 8, cx + 8, cy + 8], fill=A(WHITE, a))
    txt(d, cx, cy + 16, 'DOSE', f(MONOB, 24), RED if v > 0.8 else WHITE, a, 'ma')

# ---------------- SCENE G: sleep-tracker phone (object, rises into frame) ----------------
def scene_phone(im, d, t):
    if not (44.7 <= t < 49.32): return
    pin = back((t - 44.74) / 0.42); pout = clamp((t - 49.1) / 0.2) ** 2
    oy = lerp(560, 0, pin) + 700 * pout
    px0, px1, py0 = 300, 780, 1000 + oy
    a = 1.0
    sh = Image.new('RGBA', (W, H), (0, 0, 0, 0)); ImageDraw.Draw(sh).rounded_rectangle([px0 - 10, py0 + 20, px1 + 30, py0 + 900], radius=70, fill=(0, 0, 0, 150))
    im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(24)))
    d = ImageDraw.Draw(im, 'RGBA')
    d.rounded_rectangle([px0, py0, px1, py0 + 960], radius=64, fill=(20, 22, 28, 255), outline=(90, 94, 108, 255), width=4)
    sx0, sy0, sx1 = px0 + 18, py0 + 18, px1 - 18
    d.rounded_rectangle([sx0, sy0, sx1, py0 + 942], radius=50, fill=(4, 6, 12, 255))
    d.rounded_rectangle([(px0 + px1) / 2 - 60, sy0 + 14, (px0 + px1) / 2 + 60, sy0 + 44], radius=15, fill=(0, 0, 0, 255))
    txt(d, sx0 + 30, sy0 + 64, 'SLEEP · LAST NIGHT', f(MONOB, 22), MUTED)
    txt(d, sx0 + 30, sy0 + 96, '2–3 HRS', f(BEB, 96), RED, appear(t, 45.12, 0.12))
    # hypnogram: mostly awake
    hx0, hx1, hy = sx0 + 30, sx1 - 30, sy0 + 230
    stages = [0, 1, 0, 0, 2, 0, 1, 0, 0, 0, 1, 0, 0, 0, 2, 0, 0, 1, 0, 0, 0, 0]
    pr = clamp((t - 45.12) / 0.9)
    for i, st in enumerate(stages[:int(len(stages) * pr)]):
        w = (hx1 - hx0) / len(stages); x = hx0 + i * w
        c = RED if st == 0 else (BLUE if st == 1 else (90, 70, 200))
        d.rectangle([x + 1, hy + st * 26, x + w - 1, hy + st * 26 + 22], fill=c + (255,))
    txt(d, hx0, hy + 86, 'AWAKE', f(MONO, 18), RED); txt(d, hx1, hy + 86, 'DEEP', f(MONO, 18), (130, 110, 230), anchor='ra')
    # rows
    if t >= 46.38:
        b = appear(t, 46.38); y = sy0 + 350
        d.line([(sx0 + 24, y - 12), (sx1 - 24, y - 12)], fill=A((40, 44, 58), b), width=1)
        txt(d, sx0 + 30, y, 'NIGHT SWEATS', f(BC7, 38), WHITE, b); tag(d, sx1 - 140, y - 2, 'FLAG', RED, 22, b)
    if t >= 47.88:
        b = appear(t, 47.88); y = sy0 + 420
        d.line([(sx0 + 24, y - 12), (sx1 - 24, y - 12)], fill=A((40, 44, 58), b), width=1)
        txt(d, sx0 + 30, y, 'BLOOD PRESSURE', f(BC7, 38), WHITE, b)
        pts = [(sx0 + 40 + i * 50, y + 120 - v) for i, v in enumerate([10, 18, 14, 30, 42, 50, 66])]
        p = expo((t - 48.0) / 0.8)
        polyline(d, partial(pts, p), RED, 5, b)
        if t >= 48.7:
            arrow(d, pts[-1][0] + 14, pts[-1][1] + 10, pts[-1][0] + 40, pts[-1][1] - 26, RED, 5, appear(t, 48.7), 16)

# ---------------- SCENE H: supplement stack vs root cause (objects + verdict) ----------------
def bottle(d, x, y, w, h, label, a=1.0):
    d.rounded_rectangle([x + w * 0.22, y - 34, x + w * 0.78, y + 4], radius=6, fill=A((210, 212, 220), a))
    d.rounded_rectangle([x, y, x + w, y + h], radius=22, fill=A((26, 30, 40), a), outline=A((150, 156, 175), a), width=3)
    d.rectangle([x + 6, y + h * 0.32, x + w - 6, y + h * 0.66], fill=A((235, 232, 224), a))
    txt(d, x + w / 2, y + h * 0.49, label, f(MONOB, 22), INK, a, 'mm')
def scene_stack(im, d, t):
    if not (49.25 <= t < 55.3): return
    a = 1 - clamp((t - 55.1) / 0.16)
    floor = 1400
    d.line([(60, floor), (1020, floor)], fill=A((70, 74, 90), a), width=2)
    labels = [('SLEEP', 49.3), ('BP', 49.5), ('LIVER', 49.82), ('+1 MORE', 50.14)]
    for i, (lab, tt) in enumerate(labels):
        if t < tt - 0.12: continue
        p = expo((t - tt + 0.12) / 0.14)   # fast drop, hard land
        y = lerp(floor - 420, floor - 230, p)
        bottle(d, 80 + i * 150, y, 128, 230, lab, a)
    if t >= 50.7:   # bracket the stack as a patch
        b = appear(t, 50.7) * a
        brackets(d, 64, 1110, 690, 1416, A(RED, b), 30, 6); brackets(GL, 64, 1110, 690, 1416, A(RED, b), 30, 12)
        tag(d, 64, 1046, 'SYMPTOM PATCH', RED, 28, b)
        cross(d, 700, 1240, RED, 1.2, appear(t, 51.06) * a)
    if t >= 51.74:  # the root block
        b = appear(t, 51.74, 0.14) * a
        x0 = 790; yb = lerp(floor - 330, floor - 230, expo((t - 51.74) / 0.14))
        lit_bar(d, x0, yb, 1010, floor, RED, b); GL.rectangle([x0 - 4, yb - 4, 1014, floor + 4], outline=A(RED, b), width=10)
        txt(d, (x0 + 1010) / 2, yb + 60, 'HIGH', f(BEB, 64), WHITE, b, 'mm'); txt(d, (x0 + 1010) / 2, yb + 120, 'DOSE', f(BEB, 64), WHITE, b, 'mm')
        tag(d, x0 - 10, 1046, 'ROOT CAUSE', VGOLD, 28, appear(t, 52.22) * a)
    if t >= 53.08:  # body signal -> verdict bar on "needs to change"
        for k in range(3):
            ph = ((t - 53.08) * 1.6 - k * 0.33) % 1
            r = lerp(20, 160, ph); cx, cy = 900, 1220
            d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=A(RED, a * (1 - ph) * 0.8), width=3) if t < 54.38 else None
    if t >= 54.38:
        p = expo((t - 54.38) / 0.12); y = 1010; x0 = 40; x1 = lerp(x0, 1040, p)
        GL.rectangle([x0 - 4, y - 8, x1 + 4, y + 100], outline=A(RED, a), width=10)
        lit_bar(d, x0, y, x1, y + 92, RED, a); d.rectangle([x0, y + 88, x1, y + 92], fill=A((140, 0, 0), a))
        if p > 0.6:
            fn = f(BEB, 74); txt(d, x0 + 30, y + 8, 'BODY SIGNAL', fn, WHITE, a); tw = d.textlength('BODY SIGNAL', font=fn)
            txt(d, x0 + 30 + tw + 24, y + 30, '= CHANGE THE PROTOCOL', f(MONOB, 30), WHITE, a)

# ---------------- SCENE I: blood-level scope (PK) ----------------
def scene_scope(im, d, t):
    t0, t1 = 58.2, 64.4
    al = panel_frame(im, d, t, t0, t1, 'BLOOD LEVEL · 7 DAYS', 'TREN', CYAN, 'scope')
    if al <= 0: return
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); dd = ImageDraw.Draw(lay)
    gx0, gx1, gy0, gy1 = 90, 990, 1090, 1360
    for k in range(0, 8):
        x = lerp(gx0, gx1, k / 7); dd.line([(x, gy0), (x, gy1)], fill=A((0, 70, 90), 1), width=1)
        if k < 7: txt(dd, x + (gx1 - gx0) / 14, gy1 + 8, f'D{k + 1}', f(MONO, 20), (0, 160, 190), 1, 'ma')
    for k in range(0, 5): dd.line([(gx0, lerp(gy0, gy1, k / 4)), (gx1, lerp(gy0, gy1, k / 4))], fill=A((0, 70, 90), 1), width=1)
    # steady zone
    zb = appear(t, 62.26, 0.3)
    dd.rectangle([gx0, gy0 + 120, gx1, gy0 + 175], fill=A(GREEN, 0.12 * zb), outline=A(GREEN, 0.5 * zb))
    if zb > 0: txt(dd, gx0 + 10, gy0 + 124, 'STEADY', f(MONOB, 20), GREEN, zb)
    # big infrequent doses: spikes and crashes
    def spiky(u):
        ph = (u * 7) % 3.5 / 3.5
        return 0.05 + 0.92 * math.exp(-ph * 4.5) * min(1, ph * 30)
    def daily(u):
        ph = (u * 7) % 1
        return 0.47 + 0.07 * math.exp(-ph * 3) * min(1, ph * 30) - 0.02
    if t >= 59.46:
        p = clamp((t - 59.46) / 1.4); pts = [(lerp(gx0, gx1, i / 200), lerp(gy1, gy0, spiky(i / 200))) for i in range(201)]
        dim = 1 - 0.65 * appear(t, 63.16, 0.3)
        polyline(dd, partial(pts, p), RED, 5, dim)
        if p > 0.4: tag(dd, gx0 + 150, gy0 - 6, 'SPIKE', RED, 22, appear(t, 60.0) * dim); tag(dd, gx0 + 310, gy1 - 46, 'CRASH', RED, 22, appear(t, 60.3) * dim)
    if t >= 62.26:
        p = clamp((t - 62.26) / 1.2); pts = [(lerp(gx0, gx1, i / 200), lerp(gy1, gy0, daily(i / 200))) for i in range(201)]
        polyline(dd, partial(pts, p), VGOLD, 7)
        tag(dd, 620, gy0 + 186, 'ACETATE · DAILY MICRODOSE', VGOLD, 22, appear(t, 62.7))
    if t >= 63.82:  # daily injection ticks
        for k in range(7):
            b = appear(t, 63.82 + k * 0.05, 0.08); x = lerp(gx0, gx1, k / 7) + 6
            dd.polygon([(x, gy1 + 40), (x + 14, gy1 + 40), (x + 7, gy1 + 56)], fill=A(VGOLD, b))
    txt(dd, P[2] - 24, P[3] - 30, 'ILLUSTRATIVE', f(MONO, 20), MUTED, 1, 'ra')
    lay.putalpha(lay.split()[3].point(lambda v: int(v * al)))
    im.alpha_composite(lay)

# ---------------- SCENE J: lab order document ----------------
LABROWS = [('SHBG', 65.42), ('Testosterone, Total', 66.66), ('Testosterone, Free', 67.62), ('Progesterone', 68.26), ('Prolactin', 69.02), ('Estradiol, Sensitive', 70.2)]
DOC = None
def make_doc():
    w, h = 900, 520
    im = Image.new('RGB', (w, h), (238, 236, 230)); d = ImageDraw.Draw(im)
    d.rectangle([0, 0, w, 64], fill=(16, 24, 48)); d.text((24, 14), 'LAB ORDER · HORMONE PANEL', font=f(MONOB, 30), fill=WHITE)
    d.text((24, 76), 'TEST', font=f(MONO, 20), fill=(110, 110, 120)); d.text((w - 170, 76), 'ORDERED', font=f(MONO, 20), fill=(110, 110, 120))
    for i, (k, _) in enumerate(LABROWS):
        y = 108 + i * 66
        d.text((24, y + 10), k, font=f(DMR, 34), fill=(50, 54, 66))
        d.rectangle([w - 120, y + 12, w - 84, y + 48], outline=(90, 90, 100), width=3)
        d.line([(16, y + 62), (w - 16, y + 62)], fill=(205, 203, 198), width=2)
    # paper texture
    arr = np.asarray(im).astype(np.int16) + np.random.default_rng(3).integers(-6, 6, (h, w, 1))
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).convert('RGBA')
def scene_doc(im, d, t):
    global DOC
    if not (64.4 <= t < 71.35): return
    if DOC is None: DOC = make_doc()
    pin = expo((t - 64.45) / 0.34); pout = clamp((t - 71.12) / 0.2)
    ang = lerp(-6, -1.2, pin); y = lerp(1500, 985, pin) + 600 * pout ** 2
    doc = DOC.copy(); dd = ImageDraw.Draw(doc)
    for i, (k, tt) in enumerate(LABROWS):
        if t >= tt:
            yy = 108 + i * 66; b = appear(t, tt, 0.12)
            check(dd, 900 - 118, yy + 6, (10, 150, 60), 1.15, b) if False else None
            dd.line([(900 - 116, yy + 28), (900 - 104, yy + 42), (900 - 80, yy + 10)], fill=(10, 150, 60, int(255 * b)), width=7)
    sh = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    rot = doc.rotate(ang, resample=Image.BICUBIC, expand=True)
    ox = int(540 - rot.width / 2); oy = int(y)
    m = rot.split()[3]; shadow = Image.new('RGBA', rot.size, (0, 0, 0, 170)); shadow.putalpha(m.point(lambda v: int(v * 0.65)))
    sh.alpha_composite(shadow, (ox + 14, oy + 22)); im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(14)))
    im.alpha_composite(rot, (ox, oy))
    d = ImageDraw.Draw(im, 'RGBA')
    # highlight the row being spoken (gold bracket, follows the doc's tilt approximately)
    cur = None
    for i, (k, tt) in enumerate(LABROWS):
        if t >= tt: cur = i
    if cur is not None and pout == 0:
        yy = oy + 108 + cur * 66 + (rot.height - 520) / 2 + math.sin(math.radians(-ang)) * 0
        bx0, bx1 = ox + 30, ox + rot.width - 30
        b = appear(t, LABROWS[cur][1], 0.12)
        brackets(d, bx0, yy - 4, bx1, yy + 64, A(VGOLD, b), 22, 5); brackets(GL, bx0, yy - 4, bx1, yy + 64, A(VGOLD, b), 22, 10)

# ---------------- SCENE K: recheck cadence rail (full frame) ----------------
def scene_cadence(im, d, t):
    if not (71.2 <= t < 74.45): return
    a = appear(t, 71.2, 0.14) * (1 - clamp((t - 74.25) / 0.16))
    x0, x1 = 30, 230; y0, y1 = 520, 1180
    frosted(im, (x0, y0, x1, y1), 0.8, 12)
    d.rectangle([x0, y0, x1, y1], outline=A((70, 74, 90), a), width=2)
    d.line([(x0, y0), (x0, y1)], fill=A(CYAN, a), width=6); GL.line([(x0, y0), (x0, y1)], fill=A(CYAN, a), width=10)
    txt(d, 52, y0 + 18, 'RECHECK', f(MONOB, 26), CYAN, a)
    ln_x = 80
    d.line([(ln_x, y0 + 80), (ln_x, y1 - 40)], fill=A((90, 94, 110), a), width=3)
    labels = ['LABS', 'BP', 'SLEEP', 'MOOD', 'LABS', 'BP']
    for k, lab in enumerate(labels):
        tt = 72.0 + k * 0.22; b = appear(t, tt, 0.1) * a
        y = y0 + 110 + k * 88
        d.ellipse([ln_x - 12, y - 12, ln_x + 12, y + 12], fill=A(CYAN if b > 0 else (40, 44, 58), max(b, a * 0.5)))
        if b > 0: GL.ellipse([ln_x - 18, y - 18, ln_x + 18, y + 18], fill=A(CYAN, b))
        txt(d, ln_x + 30, y - 16, lab, f(MONOB, 26), WHITE, b)

# ---------------- SCENE L: CTA end card ----------------
LOGO = None
def scene_cta(im, d, t):
    global LOGO
    if t < 74.45: return
    a = appear(t, 74.5, 0.22)
    x0, y0, x1, y1 = P
    frosted(im, P, 0.9, 10); d = ImageDraw.Draw(im, 'RGBA')
    gp = expo((t - 74.45) / 0.3)
    d.line([(0, y0), (lerp(0, x1, gp), y0)], fill=A(VGOLD, a), width=4); GL.line([(0, y0), (lerp(0, x1, gp), y0)], fill=A(VGOLD, a), width=8)
    brackets(d, x0, y0, x1, y1, A(VGOLD, a), 44, 6); brackets(GL, x0, y0, x1, y1, A(VGOLD, a), 44, 12)
    if LOGO is None:
        lg = Image.open(S + '/logo.jpg').convert('RGB'); s = min(lg.size)
        lg = lg.crop(((lg.width - s) // 2, (lg.height - s) // 2, (lg.width + s) // 2, (lg.height + s) // 2)).resize((170, 170), Image.LANCZOS)
        m = Image.new('L', (170, 170), 0); ImageDraw.Draw(m).ellipse([0, 0, 169, 169], fill=255); lg.putalpha(m); LOGO = lg
    lg = LOGO.copy(); lg.putalpha(lg.split()[3].point(lambda v: int(v * a))); im.alpha_composite(lg, (80, y0 + 40))
    d = ImageDraw.Draw(im, 'RGBA')
    kicker(d, 280, y0 + 44, 'FULL PROTOCOL', VGOLD, t, 74.84)
    if t >= 75.08:
        b = appear(t, 75.08); fn = f(BEB, 96); txt(d, 280, y0 + 92, 'TREN', fn, VGOLD, b)
        tw = d.textlength('TREN ', font=fn); txt(d, 280 + tw, y0 + 92, 'PROTOCOL', fn, CREAM, appear(t, 75.4))
    if t >= 75.98:
        p = expo((t - 75.98) / 0.12); s = lerp(1.12, 1.0, p)
        fn = f(BEB, int(96 * s)); label = 'COMMENT  "TREN"'; tw = d.textlength(label, font=fn)
        yb = y0 + 236; lit_bar(d, 80, yb, 80 + tw + 48, yb + int(110 * s), VGOLD, p); txt(d, 104, yb + 8, label, fn, INK, p)
        GL.rectangle([76, yb - 4, 84 + tw + 48, yb + int(110 * s) + 4], outline=A(VGOLD, p), width=12)
        txt(d, 80 + tw + 72, yb + 40, '@coach.agz', f(MONO, 30), GOLD, appear(t, 76.5))
    txt(d, 80, y1 - 52, 'FOR RESEARCH & EDUCATIONAL PURPOSES ONLY', f(MONO, 20), MUTED, a)

# ---------------- captions ----------------
FIXCAP = {'SHITTING': 'SH*TTING', 'SHIT.': 'SH*T.', 'SHIT': 'SH*T', 'FUCKING': 'F*CKING'}
ACCENT = {'TRENBOLONE': VGOLD, 'TREN': VGOLD, 'ORGANS': RED, 'MISTAKES': RED, 'GAINS': VGOLD, 'MUSCLE': VGOLD, 'CARDIOVASCULAR': VGOLD,
          'NON-NEGOTIABLE': VGOLD, 'ARTERIES': RED, 'ATTACK': RED, 'DOSAGE': RED, 'CLIMBING': RED, 'PROBLEM': RED,
          'MICRODOSE': VGOLD, 'DAILY': VGOLD, 'CONSISTENT': VGOLD, 'COMMENT': VGOLD, 'FREE': VGOLD, 'SHBG': VGOLD, 'ESTRADIOL': VGOLD}
def build_groups():
    G = []; cur = []
    for i, x in enumerate(WORDS):
        if cur:
            prev = WORDS[cur[-1]]
            ln = sum(len(WORDS[j]['w']) for j in cur) + len(x['w'])
            if len(cur) >= 3 or ln > 20 or x['s'] - prev['e'] > 0.28 or prev['w'][-1] in '.,?!': G.append(cur); cur = []
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
def captions(im, t, cap_y, scale):
    g = group_at(t)
    if not g: return
    d = ImageDraw.Draw(im, 'RGBA')
    raw = [WORDS[i]['w'].upper() for i in g]
    ws = [FIXCAP.get(w, w).rstrip(',') for w in raw]
    size = int(124 * scale)
    while True:
        fn = f(BEB, size); sp = d.textlength(' ', font=fn) + 14; wd = [d.textlength(w, font=fn) for w in ws]; tot = sum(wd) + sp * (len(ws) - 1)
        if tot <= 900: break
        size -= 4
    xs = []; x = (W - tot) / 2 - 20
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
    key = ws[act].strip('.,?!"')
    boxcol = RED if key not in ACCENT or ACCENT[key] == RED else VGOLD
    lit_bar(cd, bx0, 40 + size * 0.02, bx1, 40 + size * 0.98, boxcol)
    for k, (w_, x_) in enumerate(zip(ws, xs)):
        kk = w_.strip('.,?!"'); col = CREAM
        if k != act and kk in ACCENT and WORDS[g[k]]['s'] <= t: col = ACCENT[kk]   # recolour on the spoken word
        if k == act and boxcol == VGOLD: col = INK
        cd.text((x_, 40), w_, font=fn, fill=col, stroke_width=0 if k == act else 3, stroke_fill=(0, 0, 0))
    if abs(s - 1) > 0.002:
        cap = cap.resize((int(W * s), int(300 * s)), Image.BICUBIC); ox = int((W - cap.width) / 2); oy = int(cap_y - 40 - (cap.height - 300) / 2)
    else: ox, oy = 0, int(cap_y - 40)
    im.alpha_composite(cap, (ox, oy))

# ---------------- frame ----------------
def frame(src, t):
    global GL, BG
    if BG is None: BG = background()
    (k, ox, oy), m, pm, p = layout(t)
    sa = amount(t, 'shift'); pa = amount(t, 'pip')
    canvas = BG.copy()
    fw, fh = int(round(W * k)), int(round(H * k))
    foot = src.resize((fw, fh), Image.BICUBIC) if (fw, fh) != (W, H) else src
    if pa > 0.01:
        mask = Image.new('L', (fw, fh), 0); ImageDraw.Draw(mask).rounded_rectangle([0, 0, fw - 1, fh - 1], radius=int(lerp(0, 24, pa)), fill=255)
        canvas.paste(foot, (int(ox), int(oy)), mask)
    else:
        canvas.paste(foot, (int(ox), int(oy)))
    im = canvas.convert('RGBA')
    # caption-contrast scrim (footage only, never a grade)
    yy = np.arange(H)
    cap_y = lerp(1335, 868, sa)
    scr = np.where((yy > cap_y - 140) & (yy < cap_y + 200), np.sin(np.clip((yy - (cap_y - 140)) / 340, 0, 1) * np.pi) * 95, 0) * (1 - pa)
    if sa > 0:  # shift mode: footage fades into the navy floor at its bottom edge
        fe = oy + H * k  # footage bottom edge
        scr = np.maximum(scr, np.clip((yy - (fe - 160)) / 160, 0, 1) * 255 * sa)
    alpha = Image.fromarray(np.repeat(scr.astype(np.uint8)[:, None], W, 1))
    im.alpha_composite(Image.merge('RGBA', [Image.new('L', (W, H), c) for c in NAVY] + [alpha]))
    glow = Image.new('RGBA', (W, H), (0, 0, 0, 0)); GL = ImageDraw.Draw(glow, 'RGBA')
    d = ImageDraw.Draw(im, 'RGBA')
    hook(im, t)
    d = ImageDraw.Draw(im, 'RGBA')
    band(im, d, t)
    for sc in (scene_dose, scene_gauges, scene_cardio_top, scene_dash, scene_compare, scene_rail, scene_phone, scene_stack, scene_scope, scene_doc, scene_cadence, scene_cta):
        sc(im, ImageDraw.Draw(im, 'RGBA'), t)
    GL = None
    if glow.getbbox():
        sm = glow.resize((W // 4, H // 4), Image.BILINEAR)
        g1 = np.asarray(sm.filter(ImageFilter.GaussianBlur(3.5))).astype(np.float32) / 255; g2 = np.asarray(sm.filter(ImageFilter.GaussianBlur(10))).astype(np.float32) / 255
        prem = np.clip(g1[..., :3] * g1[..., 3:] * 2.3 + g2[..., :3] * g2[..., 3:] * 1.8, 0, 1)
        prem = np.asarray(Image.fromarray((prem * 255).astype(np.uint8)).resize((W, H), Image.BILINEAR)).astype(np.float32) / 255
        b = np.asarray(im.convert('RGB')).astype(np.float32) / 255
        im = Image.fromarray(((1 - (1 - b) * (1 - prem)) * 255).astype(np.uint8)).convert('RGBA')
    d = ImageDraw.Draw(im, 'RGBA'); d.rectangle([0, 0, 7, H], fill=GOLD)
    capscale = lerp(1.0, 0.82, sa)
    if not (t < HOOK_END and False): captions(im, t, cap_y if pa < 0.5 else 1395, capscale)
    out = im.convert('RGB')
    # verdict / impact shakes (2 frames)
    for tv in (39.16, 54.5):
        kf = round((t - tv) * FPS)
        if kf in (0, 1):
            dx = [9, -5][kf]; z = 1.02; big = out.resize((int(W * z), int(H * z)), Image.BICUBIC); ox_ = (big.width - W) // 2 - dx; oy_ = (big.height - H) // 2
            out = big.crop((ox_, oy_, ox_ + W, oy_ + H)); ImageDraw.Draw(out).rectangle([0, 0, 7, H], fill=GOLD)
    return out

def src_frames(n0, n1):
    """yield (out_frame_index, source_time, PIL frame) for output frames n0..n1-1"""
    olds = [round(new_to_old(n / FPS) * FPS) for n in range(n0, n1)]
    first, last = olds[0], olds[-1]
    dec = subprocess.Popen(['ffmpeg', '-v', 'error', '-ss', f'{max(0, first / FPS - 1):.3f}', '-i', SRC, '-vf', f'fps={FPS},scale={W}:{H}', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], stdout=subprocess.PIPE)
    cur = int(round(max(0, first / FPS - 1) * FPS)) - 1; buf = None
    for n, o in zip(range(n0, n1), olds):
        while cur < o:
            buf = dec.stdout.read(W * H * 3); cur += 1
            if len(buf) < W * H * 3: raise SystemExit(f'short read at {cur}')
        yield n, o / FPS, Image.frombuffer('RGB', (W, H), buf)
    dec.kill()

if __name__ == '__main__':
    mode = sys.argv[2]
    if mode == 'stills':
        for tn in [float(x) for x in sys.argv[3:]]:
            n = int(round(tn * FPS))
            for _, to, fr in src_frames(n, n + 1):
                frame(fr, to).resize((540, 960)).save(S + f'/qc/st_{tn:06.2f}.jpg', quality=88)
        sys.exit()
    n0, n1, out = int(sys.argv[3]), int(sys.argv[4]), sys.argv[5]
    n1 = min(n1, N_OUT)
    enc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                            '-c:v', 'libx264', '-crf', '16', '-preset', 'medium', '-pix_fmt', 'yuv420p', out], stdin=subprocess.PIPE)
    for n, to, fr in src_frames(n0, n1):
        enc.stdin.write(frame(fr, to).tobytes())
    enc.stdin.close(); enc.wait(); print('done', n0, n1)
