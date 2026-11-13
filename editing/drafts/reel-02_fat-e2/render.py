# Reel 02 "Fat → E2" — 1080x1920 30 fps render. Usage:
#   python3 render.py <workdir> stills t1 t2 ...        (QC stills)
#   python3 render.py <workdir> chunk n0 n1 out.mp4     (render edited frames n0..n1-1)
# <workdir> holds fonts/, src/fat_e2.mov, work/{trim.json,words_final.json,logo.jpg}
import json, subprocess, sys, math
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
S = sys.argv[1]; F = S + '/fonts/'; WK = S + '/work/'; SRC = S + '/src/fat_e2.mov'
W, H = 1080, 1920; FPS = 30; SFPS = 60
TR = json.load(open(WK + 'trim.json')); KEEP = TR['keep']; REM = TR['remove']
DUR = sum(b - a for a, b in KEEP); N = int(round(DUR * FPS))
WORDS = json.load(open(WK + 'words_final.json'))
CUTS = [round(a - sum(b2 - a2 for a2, b2 in REM if a2 < a), 4) for a, b in REM]  # edited-time jump cuts
MID = DUR / 2

GOLD = (201, 169, 110); CREAM = (244, 241, 234); NAVY = (14, 17, 23); MUTED = (184, 184, 188); MUTED2 = (124, 124, 130)
RED = (255, 34, 28); VGOLD = (255, 194, 26); CYAN = (0, 229, 255); GREEN = (30, 255, 110); DEEP = (2, 3, 8)
INK = (6, 8, 14); WHITE = (255, 255, 255); BLUE = (79, 163, 224); AMBER = (240, 160, 48); COARED = (210, 10, 20)

# ---------------- fonts ----------------
_fc = {}
FONTFILES = {'BEB': ('BebasNeue-Regular.ttf', None), 'BAR': ('BarlowCondensed-Bold.ttf', None),
             'BARS': ('BarlowCondensed-SemiBold.ttf', None),
             'MONO': ('JetBrainsMono%5Bwght%5D.ttf', [500]), 'MONOB': ('JetBrainsMono%5Bwght%5D.ttf', [800]),
             'DMR': ('DMSans%5Bopsz,wght%5D.ttf', [14, 400]), 'DMB': ('DMSans%5Bopsz,wght%5D.ttf', [14, 700])}
def f(n, s):
    k = (n, int(s))
    if k not in _fc:
        fn, ax = FONTFILES[n]; ft = ImageFont.truetype(F + fn, int(s))
        if ax: ft.set_variation_by_axes(ax)
        _fc[k] = ft
    return _fc[k]

def clamp(x, a=0, b=1): return max(a, min(b, x))
def expo(x): x = clamp(x); return 1 if x >= 1 else 1 - 2 ** (-10 * x)
def ease_io(x): x = clamp(x); return 4 * x ** 3 if x < .5 else 1 - (-2 * x + 2) ** 3 / 2
def back_in(x): x = clamp(x); return x * x * x
def lerp(a, b, t): return a + (b - a) * t
def A(c, a): return tuple(c[:3]) + (int(clamp(a) * 255),)
def appear(t, t0, dur=0.16): return expo((t - t0) / dur)
def W_(i): return WORDS[i]['s']   # word start, edited time
GL = None
def comp(im, lay, pos=(0, 0)):
    if im.mode == 'RGBA': im.alpha_composite(lay, tuple(int(v) for v in pos))
    else: im.paste(lay, tuple(int(v) for v in pos), lay)

# ---------------- primitives (from the saved full-test setup) ----------------
def brackets(d, x0, y0, x1, y1, col, L=34, w=4):
    for (cx, cy, sx, sy) in [(x0, y0, 1, 1), (x1, y0, -1, 1), (x0, y1, 1, -1), (x1, y1, -1, -1)]:
        d.line([(cx, cy), (cx + sx * L, cy)], fill=col, width=w); d.line([(cx, cy), (cx, cy + sy * L)], fill=col, width=w)
def lit_bar(d, x0, y0, x1, y1, col, a=1.0):
    h = max(1, int(y1 - y0))
    for i in range(h):
        k = i / h; c = tuple(int(min(255, v * (1.18 - 0.36 * k) + (40 if k < 0.12 else 0))) for v in col)
        d.line([(x0, y0 + i), (x1, y0 + i)], fill=c + (int(255 * a),))
def tag(d, x, y, label, col=RED, size=30, a=1.0, glow=True, anchor='l'):
    fn = f('MONOB', size); tw = d.textlength(label, font=fn); h = size + 16
    if anchor == 'r': x = x - tw - 24
    if anchor == 'c': x = x - (tw + 24) / 2
    lit_bar(d, x, y, x + tw + 24, y + h, col, a)
    atext(d, (x + 12, y + 6), label, fn, A(INK if col in (VGOLD, GREEN, CYAN) else WHITE, a))
    if GL and glow: GL.rectangle([x - 4, y - 4, x + tw + 28, y + h + 4], outline=A(col, a), width=8)
    return x + tw + 24
def atext(d, xy, s, font, fill, anchor=None):
    # PIL ignores text alpha on RGB targets, so semi-transparent text goes through a layer
    al = fill[3] if len(fill) == 4 else 255
    if al >= 254: d.text(xy, s, font=font, fill=fill[:3] + (255,), anchor=anchor); return
    if al <= 1: return
    x0, y0, x1, y1 = [int(v) for v in d.textbbox(xy, s, font=font, anchor=anchor)]
    x0 -= 2; y0 -= 2; x1 += 2; y1 += 2
    lay = Image.new('RGBA', (x1 - x0, y1 - y0), (0, 0, 0, 0)); ld = ImageDraw.Draw(lay)
    ld.text((xy[0] - x0, xy[1] - y0), s, font=font, fill=fill[:3] + (255,), anchor=anchor)
    lay.putalpha(lay.split()[3].point(lambda v: v * al // 255))
    d._image.paste(lay, (x0, y0), lay)
def txt(d, x, y, s, font, col, a=1.0, anchor=None):
    atext(d, (x, y), s, font, A(col, a), anchor)
def hexagon(d, cx, cy, r, col, a=1.0, label=None, fill=(10, 14, 24), w=4):
    pts = [(cx + r * math.cos(math.pi / 3 * i + math.pi / 6), cy + r * math.sin(math.pi / 3 * i + math.pi / 6)) for i in range(6)]
    d.polygon(pts, fill=A(fill, 0.95 * a)); d.line(pts + [pts[0]], fill=A(col, a), width=w)
    if GL: GL.line(pts + [pts[0]], fill=A(col, a * 0.9), width=w * 2 + 2)
    if label:
        fn = f('BEB', int(r * 0.7)); txt(d, cx, cy, label, fn, col, a, 'mm')
def arrow(d, x0, y0, x1, y1, col, w=5, a=1.0, L=18):
    d.line([(x0, y0), (x1, y1)], fill=A(col, a), width=w)
    ang = math.atan2(y1 - y0, x1 - x0)
    d.polygon([(x1, y1), (x1 - L * math.cos(ang - 0.45), y1 - L * math.sin(ang - 0.45)), (x1 - L * math.cos(ang + 0.45), y1 - L * math.sin(ang + 0.45))], fill=A(col, a))
def check(d, x, y, col, s=1.0, a=1.0):
    d.line([(x, y + 16 * s), (x + 10 * s, y + 28 * s), (x + 30 * s, y + 2 * s)], fill=A(col, a), width=max(2, int(6 * s)))
    if GL: GL.line([(x, y + 16 * s), (x + 10 * s, y + 28 * s), (x + 30 * s, y + 2 * s)], fill=A(col, a), width=int(12 * s))
def cross(d, x, y, col, s=1.0, a=1.0, w=6):
    d.line([(x, y), (x + 28 * s, y + 28 * s)], fill=A(col, a), width=int(w * s)); d.line([(x + 28 * s, y), (x, y + 28 * s)], fill=A(col, a), width=int(w * s))
    if GL: GL.line([(x, y), (x + 28 * s, y + 28 * s)], fill=A(col, a), width=int(w * 2 * s)); GL.line([(x + 28 * s, y), (x, y + 28 * s)], fill=A(col, a), width=int(w * 2 * s))
def frosted(im, box, dark=0.86, blur=10, radius=0):
    x0, y0, x1, y1 = [int(v) for v in box]
    x0 = max(0, x0); y0 = max(0, y0); x1 = min(W, x1); y1 = min(H, y1)
    if x1 <= x0 + 2 or y1 <= y0 + 2: return
    reg = im.crop((x0, y0, x1, y1)).convert('RGB').filter(ImageFilter.GaussianBlur(blur))
    reg = Image.blend(reg, Image.new('RGB', reg.size, DEEP), dark).convert('RGBA')
    if radius:
        m = Image.new('L', reg.size, 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, reg.width - 1, reg.height - 1], radius=radius, fill=255)
        im.paste(reg, (x0, y0), m)
    else: im.paste(reg, (x0, y0))
def flow(d, x0, y0, x1, y1, t, col, n=5, speed=0.9, a=1.0, r=7, label=None):
    for k in range(n):
        p = (t * speed + k / n) % 1
        x = lerp(x0, x1, p); y = lerp(y0, y1, p); fa = a * min(1, p * 6, (1 - p) * 6)
        d.ellipse([x - r, y - r, x + r, y + r], fill=A(col, fa))
        if GL: GL.ellipse([x - r * 1.6, y - r * 1.6, x + r * 1.6, y + r * 1.6], fill=A(col, fa * 0.8))
        if label: txt(d, x, y, label, f('MONOB', int(r * 1.05)), INK, fa, 'mm')

# ---------------- brand background (look A) ----------------
def make_bg():
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    g = np.exp(-(((xx - 980) / 700) ** 2 + ((yy - 200) / 800) ** 2)) * 0.9
    base = np.array(NAVY, np.float32); glow = np.array((38, 34, 30), np.float32)
    img = base[None, None, :] + (glow - base)[None, None, :] * g[..., None]
    rng = np.random.default_rng(3); img += rng.normal(0, 1.6, img.shape)   # fine grain texture
    return Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))
BG = make_bg()
LOGO = None
def logo(sz):
    global LOGO
    if LOGO is None:
        lg = Image.open(WK + 'logo.jpg').convert('RGB'); s = min(lg.size)
        LOGO = lg.crop(((lg.width - s) // 2, (lg.height - s) // 2, (lg.width + s) // 2, (lg.height + s) // 2))
    lg = LOGO.resize((sz, sz), Image.LANCZOS); m = Image.new('L', (sz * 2, sz * 2), 0)
    ImageDraw.Draw(m).ellipse([0, 0, sz * 2 - 1, sz * 2 - 1], fill=255); lg.putalpha(m.resize((sz, sz), Image.LANCZOS)); return lg

# ---------------- camera / footage poses ----------------
def seg_of(t): return sum(1 for c in CUTS if c <= t + 1e-6)
def zoom(t):
    sg = seg_of(t)
    if sg == 0: return lerp(1.0, 1.05, ease_io((t - W_(4)) / 0.25))   # one push-in landing on "body fat"
    return 1.0 if sg % 2 == 1 else 1.07
T_SPLIT0, T_SPLIT1 = 5.90, 6.22          # full -> split screen
T_BUB0 = CUTS[0]; T_BUB1 = T_BUB0 + 0.30  # split -> face bubble (on the jump cut)
T_BACK0 = CUTS[2]; T_BACK1 = T_BACK0 + 0.28  # bubble -> full (on the jump cut)
BUB_C = (826, 612); BUB_R = 196; BUB_S = 0.42; FACE = (600, 990)
SPLIT_Y = 940; SPLIT_DY = -500
def pose_full(t):
    z = zoom(t); return dict(s=z, tx=-(W * z - W) / 2, ty=-(H * z - H) * 0.35, box=(0, 0, W, H), rad=0)
POSE_SPLIT = dict(s=1.0, tx=0, ty=SPLIT_DY, box=(0, 0, W, SPLIT_Y), rad=0)
POSE_BUB = dict(s=BUB_S, tx=BUB_C[0] - FACE[0] * BUB_S, ty=BUB_C[1] - FACE[1] * BUB_S,
                box=(BUB_C[0] - BUB_R, BUB_C[1] - BUB_R, BUB_C[0] + BUB_R, BUB_C[1] + BUB_R), rad=BUB_R)
def mix(p, q, e):
    return dict(s=lerp(p['s'], q['s'], e), tx=lerp(p['tx'], q['tx'], e), ty=lerp(p['ty'], q['ty'], e),
                box=tuple(lerp(a, b, e) for a, b in zip(p['box'], q['box'])), rad=lerp(p['rad'], q['rad'], e))
def pose(t):
    """returns pose, split amount, bubble amount"""
    if t < T_SPLIT0: return pose_full(t), 0, 0
    if t < T_SPLIT1: e = ease_io((t - T_SPLIT0) / (T_SPLIT1 - T_SPLIT0)); return mix(pose_full(t), POSE_SPLIT, e), e, 0
    if t < T_BUB0: return POSE_SPLIT, 1, 0
    if t < T_BUB1: e = ease_io((t - T_BUB0) / (T_BUB1 - T_BUB0)); return mix(POSE_SPLIT, POSE_BUB, e), 1 - e, e
    if t < T_BACK0: return POSE_BUB, 0, 1
    if t < T_BACK1: e = ease_io((t - T_BACK0) / (T_BACK1 - T_BACK0)); return mix(POSE_BUB, pose_full(t), e), 0, 1 - e
    return pose_full(t), 0, 0
def place_footage(src, P):
    s = P['s']; full = (P['box'] == (0, 0, W, H))
    if abs(s - 1) > 1e-4: fr = src.resize((max(1, round(W * s)), max(1, round(H * s))), Image.BICUBIC)
    else: fr = src
    if full and P['rad'] == 0:
        return fr.crop((int(round(-P['tx'])), int(round(-P['ty'])), int(round(-P['tx'])) + W, int(round(-P['ty'])) + H))
    canvas = BG.copy(); lay = Image.new('RGB', (W, H), NAVY); lay.paste(fr, (int(round(P['tx'])), int(round(P['ty']))))
    m = Image.new('L', (W * 2, H * 2), 0); x0, y0, x1, y1 = P['box']
    ImageDraw.Draw(m).rounded_rectangle([x0 * 2, y0 * 2, x1 * 2, y1 * 2], radius=int(P['rad'] * 2), fill=255)
    canvas.paste(lay, (0, 0), m.resize((W, H), Image.BILINEAR)); return canvas

# ---------------- 0. frame-0 text hook + topic band ----------------
HOOK_END = 3.0
def rich_line(d, y, parts, size, a=1.0, shadow=None):
    fn = f('BAR', size); tw = sum(d.textlength(s, font=fn) for s, _ in parts); x = (W - tw) / 2
    for s, c in parts:
        if shadow is not None: shadow.text((x + 3, y + 5), s, font=fn, fill=(0, 0, 0, int(220 * a)))
        d.text((x, y), s, font=fn, fill=A(c, a), stroke_width=3, stroke_fill=(0, 0, 0, int(200 * a)))
        if GL and c == VGOLD: GL.text((x, y), s, font=fn, fill=A(c, a * 0.55))
        x += d.textlength(s, font=fn)
def text_hook(im, t):
    if t >= HOOK_END + 0.15: return
    a = 1 if t < HOOK_END else 1 - (t - HOOK_END) / 0.15
    sh = Image.new('RGBA', (W, H), (0, 0, 0, 0)); sd = ImageDraw.Draw(sh)
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    rich_line(d, 268, [('BODY FAT', VGOLD), (' on TRT', WHITE)], 112, a, sd)
    rich_line(d, 378, [('your hidden E2 factory', WHITE)], 96, a, sd)
    comp(im, sh.filter(ImageFilter.GaussianBlur(9))); comp(im, lay)
def topic_band(im, t):
    if not (HOOK_END <= t < MID + 0.15): return
    a = clamp((t - HOOK_END - 0.15) / 0.15) * (1 - clamp((t - MID) / 0.15))
    d = ImageDraw.Draw(im, 'RGBA')
    d.rectangle([8, 212, W, 372], fill=NAVY + (int(228 * a),))
    d.line([(64, 244), (108, 244)], fill=A(GOLD, a), width=4); atext(d, (122, 228), '@coach.agz', f('MONO', 28), A(GOLD, a))
    fn = f('BAR', 84); atext(d, (64, 270), 'BODY FAT', fn, A(VGOLD, a))
    atext(d, (64 + d.textlength('BODY FAT ', font=fn), 270), 'your hidden E2 factory', fn, A(CREAM, a))

# ---------------- 1. HUD meter (side gauge) ----------------
def hud_meter(im, t):
    t0, t1 = W_(13) - 0.1, 5.78
    if not (t0 <= t < t1 + 0.22): return
    pin = expo((t - t0) / 0.2); pout = back_in((t - t1) / 0.22)
    x0 = 34 + lerp(-240, 0, pin) - 300 * pout; y0, x1, y1 = 930, x0 + 200, 1390
    frosted(im, (x0, y0, x1, y1), 0.84, 14, 16)
    d = ImageDraw.Draw(im, 'RGBA'); a = 1
    d.rounded_rectangle([x0, y0, x1, y1], radius=16, outline=A(VGOLD, 0.55), width=2)
    brackets(d, x0, y0, x1, y1, A(VGOLD, 1), 22, 5); GL and brackets(GL, x0, y0, x1, y1, A(VGOLD, 1), 22, 10)
    txt(d, x0 + 22, y0 + 14, 'E2', f('BEB', 70), CREAM); txt(d, x0 + 92, y0 + 34, 'SERUM', f('MONO', 20), MUTED)
    txt(d, x0 + 92, y0 + 56, 'LEVEL', f('MONO', 20), MUTED)
    tx0, tx1, ty0, ty1 = x0 + 34, x0 + 92, y0 + 112, y1 - 34
    lvl = 0.30 if t < W_(15) else lerp(0.30, 0.93, ease_io((t - W_(15)) / (W_(17) - W_(15) + 0.15)))
    # spectrum tube (data spectrum is the only gradient allowed)
    d.rounded_rectangle([tx0, ty0, tx1, ty1], radius=26, outline=A((90, 94, 110), 1), width=3)
    stops = [(0, BLUE), (0.35, GREEN), (0.65, AMBER), (1, RED)]
    def spec(k):
        for (k0, c0), (k1, c1) in zip(stops, stops[1:]):
            if k <= k1: u = (k - k0) / (k1 - k0); return tuple(int(lerp(a_, b_, u)) for a_, b_ in zip(c0, c1))
        return RED
    hh = ty1 - ty0 - 12; top = ty1 - 6 - hh * lvl
    for yy in range(int(top), int(ty1 - 6)):
        k = (ty1 - 6 - yy) / hh; d.line([(tx0 + 7, yy), (tx1 - 7, yy)], fill=A(spec(k), 1))
    if GL: GL.rectangle([tx0 + 7, top, tx1 - 7, ty1 - 6], fill=A(spec(lvl), 0.6))
    for k, lab in [(0.2, 'LOW'), (0.5, 'OK'), (0.82, 'HIGH')]:
        yy = ty1 - 6 - hh * k; d.line([(tx1 + 6, yy), (tx1 + 20, yy)], fill=A(MUTED2, 1), width=2); txt(d, tx1 + 26, yy - 12, lab, f('MONO', 18), MUTED2)
    # level marker
    d.polygon([(tx1 + 4, top), (tx1 + 22, top - 10), (tx1 + 22, top + 10)], fill=A(WHITE, 1))
    if lvl > 0.8:
        b = appear(t, W_(16) + 0.25, 0.12); tag(d, x0 + 18, y1 - 2 - 46 + 64 * 0, '', RED, 1, 0) if False else None
        txt(d, tx1 + 26, top - 44, '▲', f('DMB', 30), RED, b)

# ---------------- 2. split screen: fat-cell mechanism ----------------
CELLS = [(250, 1325, 76), (398, 1312, 70), (318, 1435, 80), (176, 1442, 62), (470, 1436, 64), (110, 1328, 50)]
def split_panel(im, t, amt):
    if amt <= 0: return
    a = amt if t < T_BUB0 else amt ** 3; d = ImageDraw.Draw(im, 'RGBA')
    # divider: the gold line that the footage window sits on
    d.line([(0, SPLIT_Y), (W, SPLIT_Y)], fill=A(VGOLD, a), width=4)
    if GL: GL.line([(0, SPLIT_Y), (W, SPLIT_Y)], fill=A(VGOLD, a), width=10)
    if t < 5.96: return
    kp = clamp((t - 5.96) / 0.25)
    d.line([(64, 1193), (64 + 44 * kp, 1193)], fill=A(VGOLD, a), width=4)
    txt(d, 120, 1178, 'ADIPOSE TISSUE', f('MONOB', 26), VGOLD, a * appear(t, 6.05))
    txt(d, 1016, 1178, 'CROSS-SECTION', f('MONO', 22), MUTED2, a * appear(t, 6.15), 'ra')
    # fat cells draw on, staggered
    for i, (cx, cy, r) in enumerate(CELLS):
        p = expo((t - (5.96 + i * 0.07)) / 0.22)
        if p <= 0: continue
        rr = r * lerp(0.82, 1, p)
        d.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], fill=A((40, 32, 18), a * 0.85 * p), outline=A(CREAM, a * p), width=3)
        lr = rr * 0.78; d.ellipse([cx - lr + 4, cy - lr - 2, cx + lr + 4, cy + lr - 2], fill=A((250, 196, 92), a * 0.30 * p))
        d.ellipse([cx - rr * 0.82 - 6, cy + rr * 0.35, cx - rr * 0.82 + 10, cy + rr * 0.35 + 16], fill=A(CREAM, a * p))  # nucleus
    # scan sweep on "enzyme"
    if W_(25) <= t < W_(27) + 0.35:
        u = clamp((t - W_(25)) / (W_(27) + 0.3 - W_(25))); sx = lerp(50, 560, u)
        d.line([(sx, 1240), (sx, 1530)], fill=A(CYAN, a), width=3)
        if GL: GL.line([(sx, 1240), (sx, 1530)], fill=A(CYAN, a), width=14)
        for k in range(1, 7): d.line([(sx - k * 9, 1240), (sx - k * 9, 1530)], fill=A(CYAN, a * 0.12 * (7 - k) / 6), width=2)
    # aromatase lights up inside each cell
    if t >= W_(27):
        for i, (cx, cy, r) in enumerate(CELLS):
            p = appear(t, W_(27) + i * 0.045, 0.12)
            if p > 0: hexagon(d, cx + r * 0.32, cy - r * 0.18, 17 * lerp(0.6, 1, p), VGOLD, a * p, fill=(40, 28, 4), w=3)
        b = appear(t, W_(27) + 0.12)
        d.line([(398 + 22, 1312 - 13), (520, 1240)], fill=A(VGOLD, a * b), width=2)
        tag(d, 520, 1218, 'AROMATASE', VGOLD, 24, a * b)
    # testosterone flowing in
    if t >= W_(30):
        b = appear(t, W_(30), 0.2)
        flow(d, 20, 1390, 240, 1380, t, CYAN, 4, 0.75, a * b, 15, 'T')
    # right side: T -> E2 conversion readout
    if t >= W_(32):
        b = appear(t, W_(32)); txt(d, 640, 1270, 'T', f('BEB', 150), CYAN, a * b)
        if GL: GL.text((640, 1270), 'T', font=f('BEB', 150), fill=A(CYAN, a * b * 0.6))
        txt(d, 642, 1430, 'TESTOSTERONE', f('MONO', 20), MUTED, a * b)
    if t >= W_(33):
        b = appear(t, W_(33), 0.2); arrow(d, 720, 1348, lerp(720, 840, b), 1348, VGOLD, 6, a)
        hexagon(d, 780, 1348, 20, VGOLD, a * b, fill=(40, 28, 4), w=3)
        flow(d, 545, 1390, 640, 1420, t, RED, 3, 0.9, a * b, 14, 'E2')
    if t >= W_(34):
        b = appear(t, W_(34), 0.12); s = lerp(1.25, 1, b)
        fn = f('BEB', int(150 * s)); txt(d, 862, 1270 - (s - 1) * 60, 'E2', fn, RED, a * b)
        if GL: GL.text((862, 1270 - (s - 1) * 60), 'E2', font=fn, fill=A(RED, a * b))
        txt(d, 864, 1430, 'ESTRADIOL', f('MONO', 20), MUTED, a * b)
        on = 0.5 + 0.5 * math.sin(t * 10)
        d.ellipse([644, 1494, 662, 1512], fill=A(RED, a * b * (0.4 + 0.6 * on)))
        txt(d, 672, 1488, 'CONVERSION ACTIVE', f('MONOB', 22), RED, a * b)

# ---------------- 3. full-screen graph + face bubble ----------------
CH = (130, 850, 990, 1330)   # chart box
def curve_a(x): return 0.12 + 0.55 * x ** 1.5
def curve_e(x): return 0.08 + 0.84 * x ** 2.0
def cpt(x, y): return (lerp(CH[0], CH[2], x), lerp(CH[3], CH[1], y))
def graph_scene(im, t, amt):
    if amt <= 0.02: return
    a = amt if t < T_BACK0 else amt ** 2.5; d = ImageDraw.Draw(im, 'RGBA')
    # bubble ring
    cx, cy = BUB_C
    d.ellipse([cx - BUB_R - 3, cy - BUB_R - 3, cx + BUB_R + 3, cy + BUB_R + 3], outline=A(VGOLD, a), width=6)
    if GL: GL.ellipse([cx - BUB_R - 6, cy - BUB_R - 6, cx + BUB_R + 6, cy + BUB_R + 6], outline=A(VGOLD, a), width=12)
    t0 = T_BUB0 + 0.12
    kp = clamp((t - t0) / 0.22); d.line([(70, 452), (70 + 44 * kp, 452)], fill=A(VGOLD, a), width=4)
    txt(d, 126, 437, 'THE CONVERSION CURVE', f('MONOB', 24), VGOLD, a * appear(t, t0 + 0.08))
    b = appear(t, t0 + 0.14, 0.2)
    txt(d, 68, 484 - 10 * (1 - b), 'FAT MASS', f('BEB', 104), CREAM, a * b)
    fn = f('BEB', 104); txt(d, 68, 584 - 10 * (1 - b), 'VS ', fn, CREAM, a * b)
    txt(d, 68 + d.textlength('VS ', font=fn), 584 - 10 * (1 - b), 'E2', fn, RED, a * b)
    txt(d, 70, 700, 'Illustrative trend, not lab data', f('DMR', 26), MUTED2, a * b)
    # axes + grid
    x0, y0, x1, y1 = CH
    for k in range(1, 4): d.line([(x0, lerp(y1, y0, k / 4)), (x1, lerp(y1, y0, k / 4))], fill=A((34, 38, 52), a), width=1)
    d.line([(x0, y1), (x1, y1)], fill=A((110, 114, 130), a), width=3); d.line([(x0, y0), (x0, y1)], fill=A((110, 114, 130), a), width=3)
    txt(d, x0 - 16, y0 - 2, 'HIGH', f('MONO', 18), MUTED2, a, 'ra'); txt(d, x0 - 16, y1 - 20, 'LOW', f('MONO', 18), MUTED2, a, 'ra')
    # x axis: a fat wedge that thickens left -> right, revealed by the scan marker on "more fat"
    mp = ease_io((t - W_(37)) / 0.85)
    if mp > 0:
        xm = lerp(x0, x1, mp)
        poly = [(x0, y1 + 14), (xm, y1 + 14), (xm, y1 + 14 + lerp(6, 34, mp))]
        lay = [(x0 + (xm - x0) * k / 40, y1 + 14 + lerp(6, 34, mp * k / 40)) for k in range(41)]
        d.polygon([(x0, y1 + 14)] + lay + [(xm, y1 + 14)], fill=A((250, 196, 92), a * 0.85))
        d.line([(xm, y0 - 10), (xm, y1 + 50)], fill=A(VGOLD, a * (1 - clamp((t - W_(42)) / 0.3)) ), width=2)
        txt(d, x0, y1 + 56, 'BODY FAT', f('MONOB', 22), VGOLD, a); arrow(d, x0 + 130, y1 + 68, x0 + 200, y1 + 68, VGOLD, 3, a, 12)
    # gold curve: aromatase activity
    def draw_curve(fn, col, p, wdt=6, fill=False):
        n = int(60 * p)
        if n < 2: return None
        pts = [cpt(k / 60, fn(k / 60)) for k in range(n + 1)]
        if fill: d.polygon(pts + [(pts[-1][0], y1), (pts[0][0], y1)], fill=A(col, a * 0.10))
        d.line(pts, fill=A(col, a), width=wdt, joint='curve')
        if GL: GL.line(pts, fill=A(col, a), width=wdt * 2 + 4)
        return pts[-1]
    pa = ease_io((t - W_(42)) / 0.75)
    ea = ease_io((t - W_(45)) / 0.7)
    end_e = draw_curve(curve_e, RED, ea, 7, True)
    end_a = draw_curve(curve_a, VGOLD, pa, 5)
    if end_a: d.ellipse([end_a[0] - 9, end_a[1] - 9, end_a[0] + 9, end_a[1] + 9], fill=A(WHITE, a))
    if end_e:
        r = 11 + (4 * (0.5 + 0.5 * math.sin(t * 12)) if ea >= 1 else 0)
        d.ellipse([end_e[0] - r, end_e[1] - r, end_e[0] + r, end_e[1] + r], fill=A(WHITE, a))
    # legend
    if pa > 0: d.line([(x0 + 30, y0 + 22), (x0 + 74, y0 + 22)], fill=A(VGOLD, a), width=5); txt(d, x0 + 86, y0 + 10, 'AROMATASE ACTIVITY', f('MONO', 22), CREAM, a * clamp(pa * 3))
    if ea > 0: d.line([(x0 + 30, y0 + 60), (x0 + 74, y0 + 60)], fill=A(RED, a), width=7); txt(d, x0 + 86, y0 + 48, 'ESTRADIOL (E2)', f('MONO', 22), CREAM, a * clamp(ea * 3))
    if t >= W_(46) + 0.25:
        tag(d, x1 - 40, cpt(1, curve_e(1))[1] - 22, 'E2 ▲ HIGH', RED, 26, a * appear(t, W_(46) + 0.25), anchor='r')

# ---------------- 4. side stack: symptom scan cards ----------------
def icon_water(d, x, y, t, a):
    pts = [(x + 45 + 34 * math.sin(k / 30 * math.pi) * (k / 30) ** 0.5 * (1 if k <= 30 else 1), 0) for k in range(0)]
    # droplet outline
    cx, cy = x + 45, y + 52; r = 28
    poly = [(cx, cy - 46)] + [(cx + r * math.cos(u), cy + r * math.sin(u)) for u in np.linspace(-0.35, math.pi + 0.35, 24)]
    lvl = cy + r - lerp(0, 2 * r + 8, 0.35 + 0.35 * clamp((t - W_(56)) / 0.8))
    m = Image.new('L', (W, H), 0)
    wave = [(cx - 40 + k * 4, lvl + 4 * math.sin(k * 0.5 + t * 7)) for k in range(21)]
    d.polygon(wave + [(cx + 40, cy + 40), (cx - 40, cy + 40)], fill=None)
    # fill below the wave, clipped roughly by drawing horizontal spans inside the droplet circle part
    for yy in range(int(lvl), int(cy + r)):
        dx = math.sqrt(max(0, r * r - (yy - cy) ** 2)) - 3 if yy > cy - 8 else max(0, (yy - (cy - 46)) / 38 * r * 0.75)
        d.line([(cx - dx, yy), (cx + dx, yy)], fill=A(CYAN, a * 0.55))
    d.line(poly + [poly[0]], fill=A(CYAN, a), width=4)
    if GL: GL.line(poly + [poly[0]], fill=A(CYAN, a), width=8)
def icon_mood(d, x, y, t, a):
    pts = []
    for k in range(40):
        u = k / 39; xx = x + 6 + u * 80
        amp = 26 * (0.3 + 0.7 * abs(math.sin(u * 9 + t * 5))) * math.sin(u * 23 + t * 9)
        pts.append((xx, y + 52 + amp))
    d.line(pts, fill=A(CYAN, a), width=4, joint='curve')
    if GL: GL.line(pts, fill=A(CYAN, a), width=8)
def icon_chest(d, x, y, t, a):
    # pec outline schematic with highlighted gland
    d.arc([x - 6, y + 10, x + 96, y + 104], 200, 340, fill=A(CREAM, a), width=4)
    d.line([(x + 4, y + 36), (x + 4, y + 84)], fill=A(CREAM, a), width=3)
    cx, cy = x + 52, y + 66; pr = 9 + 3 * (0.5 + 0.5 * math.sin(t * 9))
    d.ellipse([cx - 20, cy - 16, cx + 20, cy + 16], outline=A(RED, a), width=3)
    d.ellipse([cx - pr * 0.5, cy - pr * 0.5, cx + pr * 0.5, cy + pr * 0.5], fill=A(RED, a))
    if GL: GL.ellipse([cx - 24, cy - 20, cx + 24, cy + 20], outline=A(RED, a), width=6)
    brackets(d, cx - 30, cy - 26, cx + 30, cy + 26, A(RED, a), 10, 3)
SYMS = [('WATER', 'RETENTION', icon_water, 56), ('MOOD', 'SWINGS', icon_mood, 57), ('GYNO', 'SIGNS', icon_chest, 62)]
SYM_IN = W_(48); SYM_OUT = W_(64) - 0.12
def symptom_stack(im, t):
    if not (SYM_IN <= t < SYM_OUT + 0.4): return
    # header strip
    def slide(t0, k):
        pin = expo((t - t0) / 0.2); pout = back_in((t - SYM_OUT - k * 0.045) / 0.2)
        return lerp(-340, 0, pin) - 360 * pout, pin * (1 - clamp(pout))
    dx, a = slide(SYM_IN, 0)
    if a > 0:
        x0, y0 = 22 + dx, 862
        frosted(im, (x0, y0, x0 + 296, y0 + 52), 0.85, 10, 10); d = ImageDraw.Draw(im, 'RGBA')
        on = 0.5 + 0.5 * math.sin(t * 9); d.ellipse([x0 + 14, y0 + 18, x0 + 30, y0 + 34], fill=A(RED, a * (0.35 + 0.65 * on)))
        txt(d, x0 + 42, y0 + 13, 'E2 SIDE-EFFECT SCAN', f('MONOB', 21), CREAM, a)
    for k, (l1, l2, icon, wi) in enumerate(SYMS):
        t0 = W_(wi) - 0.04
        if t < t0: continue
        dx, a = slide(t0, k + 1)
        if a <= 0: continue
        x0, y0 = 22 + dx, 928 + k * 160; x1, y1 = x0 + 296, y0 + 146
        frosted(im, (x0, y0, x1, y1), 0.86, 12, 12); d = ImageDraw.Draw(im, 'RGBA')
        lit_bar(d, x0, y0, x0 + 7, y1, RED, a)
        d.rounded_rectangle([x0, y0, x1, y1], radius=12, outline=A((90, 30, 34), a), width=2)
        d.rounded_rectangle([x0 + 20, y0 + 22, x0 + 116, y0 + 124], radius=10, fill=A((8, 12, 22), a), outline=A((60, 64, 82), a), width=2)
        icon(d, x0 + 23, y0 + 20, t, a)
        txt(d, x0 + 132, y0 + 16, l1, f('BAR', 46), WHITE, a); txt(d, x0 + 132, y0 + 60, l2, f('BAR', 38), CREAM, a)
        if t >= t0 + 0.14: tag(d, x0 + 132, y0 + 104, 'E2-DRIVEN', RED, 17, a * appear(t, t0 + 0.14, 0.1))

# ---------------- 5. top dashboard: same dose, different E2 (dials) ----------------
DASH_IN = W_(64); DASH_OUT = CUTS[4]
def syringe(d, x, y, fill, a):
    d.rounded_rectangle([x + 30, y, x + 200, y + 40], radius=6, outline=A(CREAM, a), width=3)
    if fill > 0: lit_bar(d, x + 33, y + 4, x + 33 + 164 * fill, y + 37, VGOLD, a)
    for k in range(1, 8): d.line([(x + 30 + k * 21, y), (x + 30 + k * 21, y + 12)], fill=A(CREAM, a * 0.7), width=2)
    d.rectangle([x + 4, y + 8, x + 30, y + 32], fill=A(CREAM, a)); d.rectangle([x, y - 4, x + 8, y + 44], fill=A(CREAM, a))  # plunger
    d.line([(x + 200, y + 20), (x + 240, y + 20)], fill=A(CREAM, a), width=3)  # needle
def dial(d, cx, cy, r, v, a, verdict=None):
    segs = [(0, 0.3, BLUE), (0.3, 0.6, GREEN), (0.6, 0.78, AMBER), (0.78, 1, RED)]
    for s0, s1, c in segs:
        d.arc([cx - r, cy - r, cx + r, cy + r], 180 + 180 * s0, 180 + 180 * s1 - 1.5, fill=A(c, a), width=16)
    if GL:
        for s0, s1, c in segs: GL.arc([cx - r, cy - r, cx + r, cy + r], 180 + 180 * s0, 180 + 180 * s1, fill=A(c, a * 0.7), width=22)
    ang = math.pi * (1 + v); nx, ny = cx + (r - 26) * math.cos(ang), cy + (r - 26) * math.sin(ang)
    d.line([(cx, cy), (nx, ny)], fill=A(WHITE, a), width=6); d.ellipse([cx - 12, cy - 12, cx + 12, cy + 12], fill=A(WHITE, a))
    txt(d, cx, cy + 24, 'E2', f('BEB', 44), CREAM, a, 'mt')
def dashboard(im, t):
    if not (DASH_IN <= t < DASH_OUT): return
    swing = ease_io((t - W_(77)) / 0.55)
    for k in range(2):
        t0 = DASH_IN + k * 0.07; p = expo((t - t0) / 0.22)
        if p <= 0: continue
        x0 = 40 if k == 0 else 555; y0 = 252 + lerp(-50, 0, p); x1, y1 = x0 + 485, y0 + 318
        frosted(im, (x0, y0, x1, y1), 0.86, 12, 14); d = ImageDraw.Draw(im, 'RGBA'); a = p
        col = GREEN if k == 0 else RED
        d.rounded_rectangle([x0, y0, x1, y1], radius=14, outline=A(VGOLD, a * 0.6), width=2)
        brackets(d, x0, y0, x1, y1, A(VGOLD, a), 26, 5); GL and brackets(GL, x0, y0, x1, y1, A(VGOLD, a), 26, 10)
        txt(d, x0 + 24, y0 + 18, 'BODY A' if k == 0 else 'BODY B', f('MONOB', 24), VGOLD, a)
        txt(d, x0 + 24 + (122 if True else 0), y0 + 18, '· LEAN' if k == 0 else '· HIGHER BODY FAT', f('MONO', 24), CREAM, a)
        # dose half is on the inner side so the two syringes sit next to the "=" badge
        dx_ = x0 + 250 if k == 0 else x0 + 22; gx = x0 + 128 if k == 0 else x0 + 360
        fill = 0 if t < W_(67) else 0.68 * ease_io((t - W_(67)) / 0.35)
        dim = 1 - 0.45 * clamp((t - W_(73)) / 0.3)
        txt(d, dx_, y0 + 70, 'DOSE', f('MONO', 20), MUTED, a); syringe(d, dx_ - 2, y0 + 104, fill, a * dim)
        txt(d, dx_, y0 + 172, 'AROMATASE', f('MONO', 20), MUTED, a)
        nh = 1 if k == 0 else 5
        for j in range(nh):
            q = appear(t, W_(75) + j * 0.06, 0.12)
            if q > 0: hexagon(d, dx_ + 18 + j * 42, y0 + 232, 17 * lerp(0.5, 1, q), VGOLD, a * q, fill=(40, 28, 4), w=3)
        v = lerp(0.06, 0.44 if k == 0 else 0.9, swing)
        dial(d, gx, y0 + 220, 98, v, a)
        if swing >= 0.85:
            b = appear(t, W_(77) + 0.5, 0.12)
            tag(d, gx, y0 + 112 - 0, 'IN RANGE' if k == 0 else 'HIGH', col, 20, a * b, anchor='c') if False else None
            tag(d, gx, y1 + 10, 'IN RANGE' if k == 0 else 'HIGH', col, 24, a * b, anchor='c')
    # "=" badge between the two syringes on "exact"
    if t >= W_(68):
        b = appear(t, W_(68), 0.12); d = ImageDraw.Draw(im, 'RGBA'); s = lerp(1.3, 1, b)
        cx, cy = 540, 252 + 124; r = 32 * s
        lit_bar(d, cx - r, cy - r, cx + r, cy + r, VGOLD, b)
        if GL: GL.rectangle([cx - r - 4, cy - r - 4, cx + r + 4, cy + r + 4], outline=A(VGOLD, b), width=10)
        txt(d, cx, cy + 3, '=', f('BEB', int(64 * s)), INK, b, 'mm')
    if t >= W_(73):
        d = ImageDraw.Draw(im, 'RGBA'); tag(d, 540, 252 + 172, 'CONSTANT', VGOLD, 18, appear(t, W_(73)), anchor='c')

# ---------------- 6. corner evidence objects: Rx bottle vs lab order ----------------
EV_OUT = CUTS[5]
def rx_bottle(d, x, y, a):
    d.rounded_rectangle([x + 14, y, x + 206, y + 52], radius=10, fill=A((240, 240, 236), a))          # cap
    for k in range(10): d.line([(x + 26 + k * 18, y + 8), (x + 26 + k * 18, y + 44)], fill=A((200, 200, 196), a), width=3)
    d.rounded_rectangle([x, y + 52, x + 220, y + 300], radius=18, fill=A((176, 92, 18), a * 0.92))    # amber body
    d.rectangle([x + 10, y + 64, x + 30, y + 290], fill=A((230, 150, 60), a * 0.45))                  # highlight
    d.rectangle([x + 16, y + 100, x + 204, y + 262], fill=A((248, 247, 242), a))                       # label
    d.rectangle([x + 16, y + 100, x + 204, y + 128], fill=A(COARED, a)); txt(d, x + 26, y + 104, 'Rx  AROMATASE INH.', f('MONOB', 15), WHITE, a)
    txt(d, x + 26, y + 136, 'ANASTROZOLE', f('BAR', 40), INK, a); txt(d, x + 26, y + 182, '1 mg tablets', f('DMR', 22), (70, 70, 80), a)
    for k in range(3): d.line([(x + 26, y + 220 + k * 12), (x + 26 + [150, 120, 160][k], y + 220 + k * 12)], fill=A((160, 160, 168), a), width=4)
def lab_order(d, x, y, t, a):
    d.rounded_rectangle([x, y, x + 236, y + 300], radius=8, fill=A((250, 250, 248), a))
    d.rectangle([x, y, x + 236, y + 40], fill=A((16, 24, 48), a)); txt(d, x + 12, y + 9, 'LAB ORDER', f('MONOB', 20), WHITE, a)
    rows = ['Estradiol (sens.)', 'Total T', 'Free T', 'SHBG', 'CBC']
    for k, r_ in enumerate(rows):
        yy = y + 56 + k * 46; d.rectangle([x + 12, yy, x + 36, yy + 24], outline=A((60, 60, 70), a), width=2)
        txt(d, x + 46, yy - 1, r_, f('DMB' if k == 0 else 'DMR', 21), INK, a)
        q = appear(t, W_(97) + k * 0.07, 0.1)
        if q > 0: check(d, x + 13, yy - 6, (0, 150, 60), 0.85, a * q)
    # blood tube
    tx, ty = x - 30, y + 150
    d.rounded_rectangle([tx, ty, tx + 36, ty + 170], radius=16, fill=A((235, 235, 240), a * 0.9), outline=A((200, 200, 210), a), width=2)
    d.rounded_rectangle([tx + 4, ty + 60, tx + 32, ty + 166], radius=14, fill=A((150, 8, 16), a))
    d.rectangle([tx - 2, ty - 8, tx + 38, ty + 22], fill=A((150, 30, 160), a))  # cap
def evidence(im, t):
    if not (W_(89) - 0.05 <= t < EV_OUT): return
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay, 'RGBA')
    t0 = W_(89) - 0.05; p = expo((t - t0) / 0.26)
    rx, ry = 34, 1100 + lerp(260, 0, p); shadow = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(shadow).rounded_rectangle([rx + 10, ry + 20, rx + 240, ry + 316], radius=18, fill=(0, 0, 0, int(150 * p)))
    comp(im, shadow.filter(ImageFilter.GaussianBlur(14)))
    rx_bottle(d, rx, ry, p)
    if t >= W_(92):   # X stamp on "AI"
        b = expo((t - W_(92)) / 0.08); s = lerp(1.5, 1, b); cx, cy = rx + 110, ry + 175
        for (ax, ay, bx, by) in [(-1, -1, 1, 1), (1, -1, -1, 1)]:
            pts = [(cx + ax * 120 * s, cy + ay * 140 * s), (cx + bx * 120 * s, cy + by * 140 * s)]
            d.line(pts, fill=A(RED, b), width=int(22 * s))
            if GL: GL.line(pts, fill=A(RED, b), width=int(36 * s))
        tag(d, rx - 4, ry - 58, 'NOT STEP 1', RED, 26, b)
    t1 = W_(93) - 0.05
    if t >= t1:
        q = expo((t - t1) / 0.24); lx, ly = 820 + lerp(300, 0, q), 1100
        sh = Image.new('RGBA', (W, H), (0, 0, 0, 0)); ImageDraw.Draw(sh).rounded_rectangle([lx + 10, ly + 18, lx + 246, ly + 312], radius=8, fill=(0, 0, 0, int(150 * q)))
        comp(im, sh.filter(ImageFilter.GaussianBlur(14)))
        lab_order(d, lx, ly, t, q)
        if t >= W_(97):
            b = appear(t, W_(97), 0.12); tag(d, lx + 236, ly - 58, 'STEP 1', GREEN, 26, b, anchor='r')
            brackets(d, lx - 40, ly - 8, lx + 246, ly + 328, A(GREEN, b), 26, 5); GL and brackets(GL, lx - 40, ly - 8, lx + 246, ly + 328, A(GREEN, b), 26, 10)
    comp(im, lay)

# ---------------- 7. CTA: comment field + framework doc ----------------
CTA_IN = CUTS[5]
def doc_card(w, h, t):
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im, 'RGBA')
    d.rounded_rectangle([0, 0, w - 1, h - 1], radius=10, fill=(250, 248, 242, 255))
    d.rectangle([0, 0, w, 54], fill=VGOLD + (255,)); d.text((16, 13), 'COACH AGZ', font=f('MONOB', 22), fill=INK)
    d.text((18, 70), 'E2 MANAGEMENT', font=f('BEB', 46), fill=INK); d.text((18, 114), 'FRAMEWORK', font=f('BEB', 46), fill=COARED)
    for k in range(5):
        yy = 180 + k * 52; d.rectangle([18, yy, 42, yy + 24], outline=(60, 60, 70), width=2)
        d.rounded_rectangle([56, yy + 6, 56 + [190, 150, 200, 170, 120][k], yy + 18], radius=5, fill=(196, 196, 204))
        q = appear(t, W_(108) + k * 0.28, 0.1)
        if q > 0: d.line([(19, yy + 12), (28, yy + 22), (44, yy - 2)], fill=(0, 150, 60, int(255 * q)), width=5)
    return im
def cta(im, t):
    if t < CTA_IN: return
    d = ImageDraw.Draw(im, 'RGBA')
    p = expo((t - CTA_IN) / 0.2); s = lerp(1.15, 1, p)
    # COMMENT pill (heavy block)
    fn = f('BEB', int(58 * s)); lab = 'COMMENT'; tw = d.textlength(lab, font=fn)
    lit_bar(d, 60, 258, 60 + tw + 36, 258 + 66 * s, VGOLD, p); atext(d, (78, 262), lab, fn, A(INK, p))
    if GL: GL.rectangle([56, 254, 64 + tw + 36, 262 + 66 * s], outline=A(VGOLD, p), width=10)
    txt(d, 60 + tw + 56, 280, 'FREE · E2 FRAMEWORK', f('MONOB', 24), VGOLD, appear(t, CTA_IN + 0.12))
    # comment field
    q = expo((t - CTA_IN - 0.08) / 0.22); y0 = 344 + lerp(30, 0, q)
    frosted(im, (56, y0, 1024, y0 + 112), 0.86 * q, 12 * q + 1, 56) if q > 0.02 else None; d = ImageDraw.Draw(im, 'RGBA')
    d.rounded_rectangle([56, y0, 1024, y0 + 112], radius=56, outline=A(VGOLD, q), width=3)
    if GL: GL.rounded_rectangle([56, y0, 1024, y0 + 112], radius=56, outline=A(VGOLD, q * 0.6), width=8)
    lg = logo(84); lg.putalpha(lg.split()[3].point(lambda v: int(v * q))); comp(im, lg, (72, int(y0 + 14))); d = ImageDraw.Draw(im, 'RGBA')
    if t < W_(102): txt(d, 180, y0 + 34, 'Add a comment…', f('DMR', 36), MUTED2, q)
    else:
        b = appear(t, W_(102), 0.08); fnk = f('BEB', 78); txt(d, 180, y0 + 18, 'E2', fnk, VGOLD, b)
        if GL: GL.text((180, y0 + 18), 'E2', font=fnk, fill=A(VGOLD, b * 0.6))
        if int(t * 2.2) % 2 == 0: d.rectangle([180 + d.textlength('E2', font=fnk) + 8, y0 + 26, 186 + d.textlength('E2', font=fnk) + 8, y0 + 88], fill=A(CREAM, 1))
    # send button
    sp = 0 if t < W_(103) else expo((t - W_(103)) / 0.1); bs = 1 - 0.12 * math.sin(math.pi * clamp((t - W_(103)) / 0.16))
    cx, cy, r = 960, y0 + 56, 38 * bs
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=A(VGOLD, lerp(0.35, 1, sp) * q))
    if GL and sp > 0: GL.ellipse([cx - r - 4, cy - r - 4, cx + r + 4, cy + r + 4], outline=A(VGOLD, sp), width=10)
    d.polygon([(cx - 14, cy - 16), (cx + 18, cy), (cx - 14, cy + 16), (cx - 6, cy)], fill=A(INK, q))
    # framework doc flies from the send button to the left column on "send"
    t2 = W_(105) - 0.05
    if t >= t2:
        e = ease_io((t - t2) / 0.42); dw, dh = 300, 450
        card = doc_card(dw, dh, t)
        if t >= W_(119):   # FREE stamp
            b = expo((t - W_(119)) / 0.1); st = Image.new('RGBA', (240, 110), (0, 0, 0, 0)); sd = ImageDraw.Draw(st)
            sd.rounded_rectangle([4, 4, 236, 106], radius=10, outline=RED + (255,), width=8); sd.text((120, 56), 'FREE', font=f('BEB', 96), fill=RED + (255,), anchor='mm')
            st = st.rotate(9, expand=True, resample=Image.BICUBIC); sc = lerp(1.6, 1, b)
            st = st.resize((int(st.width * sc), int(st.height * sc)), Image.BICUBIC); st.putalpha(st.split()[3].point(lambda v: int(v * b)))
            card.alpha_composite(st, (int(dw / 2 - st.width / 2 + 20), int(dh - 150 - st.height / 2)))
        sc = lerp(0.18, 1, e); rot = lerp(-14, -2.0, e) + 2.0 * clamp((t - t2 - 0.42) / 0.3)
        c2 = card.resize((max(1, int(dw * sc)), max(1, int(dh * sc))), Image.BICUBIC).rotate(rot, expand=True, resample=Image.BICUBIC)
        cxp, cyp = lerp(960, 34 + dw / 2, e), lerp(400, 905 + dh / 2, e)
        sh = Image.new('RGBA', (W, H), (0, 0, 0, 0)); ImageDraw.Draw(sh).rectangle([cxp - c2.width / 2 + 12, cyp - c2.height / 2 + 22, cxp + c2.width / 2 + 12, cyp + c2.height / 2 + 22], fill=(0, 0, 0, int(140 * e)))
        comp(im, sh.filter(ImageFilter.GaussianBlur(16)))
        if e < 1: c2 = c2.filter(ImageFilter.GaussianBlur(4 * (1 - e)))
        comp(im, c2, (int(cxp - c2.width / 2), int(cyp - c2.height / 2)))

# ---------------- captions (saved setup, moved off the face) ----------------
FIX = {}
def build_groups():
    G = []; cur = []
    for i, x in enumerate(WORDS):
        if cur:
            prev = WORDS[cur[-1]]
            if len(cur) >= 3 or x['s'] - prev['e'] > 0.28 or prev['w'][-1] in '.,?!' or any(prev['e'] - 0.01 < c <= x['s'] + 0.01 for c in CUTS): G.append(cur); cur = []
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
def captions(im, t, cap_y):
    g = group_at(t)
    if not g: return
    d = ImageDraw.Draw(im, 'RGBA')
    ws = [WORDS[i]['w'].upper().strip('.,?!') for i in g]
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
    bx0 = lerp(xs[prev], xs[act], bt) - 16; bx1 = lerp(xs[prev] + wd[prev], xs[act] + wd[act], bt) + 16
    for k, (w_, x_) in enumerate(zip(ws, xs)): sd.text((x_ + 4, 46), w_, font=fn, fill=(0, 0, 0, 220))
    cap.alpha_composite(shd.filter(ImageFilter.GaussianBlur(6)))
    lit_bar(cd, bx0, 40 + size * 0.02, bx1, 40 + size * 0.98, RED)
    for k, (w_, x_) in enumerate(zip(ws, xs)): cd.text((x_, 40), w_, font=fn, fill=CREAM, stroke_width=0 if k == act else 3, stroke_fill=(0, 0, 0))
    if abs(s - 1) > 0.002:
        cap = cap.resize((int(W * s), int(260 * s)), Image.BICUBIC); ox = int((W - cap.width) / 2); oy = int(cap_y - 40 - (cap.height - 260) / 2)
    else: ox, oy = 0, cap_y - 40
    comp(im, cap, (ox, oy))

# ---------------- frame ----------------
def frame(src, t):
    global GL
    P, split_amt, bub_amt = pose(t)
    im = place_footage(src, P).convert('RGB')
    # light top/bottom scrims for text legibility (no footage grade)
    yy = np.arange(H); a = np.where(yy > 1300, np.clip((yy - 1300) / 260, 0, 1) * 100, 0); a = np.maximum(a, np.where(yy < 520, (1 - yy / 520) * 120, 0))
    scr = Image.fromarray(np.repeat(a.astype(np.uint8)[:, None], W, 1))
    comp(im, Image.merge('RGBA', [Image.new('L', (W, H), c) for c in NAVY] + [scr]))
    glow = Image.new('RGBA', (W, H), (0, 0, 0, 0)); GL = ImageDraw.Draw(glow, 'RGBA')
    hud_meter(im, t)
    split_panel(im, t, split_amt if t >= T_SPLIT0 and t < T_BUB1 else 0)
    graph_scene(im, t, bub_amt)
    symptom_stack(im, t)
    dashboard(im, t)
    evidence(im, t)
    cta(im, t)
    text_hook(im, t)
    GL = None
    if glow.getbbox():
        sm = glow.resize((W // 4, H // 4), Image.BILINEAR)
        g1 = np.asarray(sm.filter(ImageFilter.GaussianBlur(3.5))).astype(np.float32) / 255; g2 = np.asarray(sm.filter(ImageFilter.GaussianBlur(10))).astype(np.float32) / 255
        prem = np.clip(g1[..., :3] * g1[..., 3:] * 2.3 + g2[..., :3] * g2[..., 3:] * 1.8, 0, 1)
        prem = np.asarray(Image.fromarray((prem * 255).astype(np.uint8)).resize((W, H), Image.BILINEAR)).astype(np.float32) / 255
        b = np.asarray(im.convert('RGB')).astype(np.float32) / 255
        im = Image.fromarray(((1 - (1 - b) * (1 - prem)) * 255).astype(np.uint8))
    topic_band(im, t)
    d = ImageDraw.Draw(im, 'RGBA'); d.rectangle([0, 0, 7, H], fill=GOLD)   # gold edge rule
    cap_y = 1000 if split_amt > 0.5 else 1418
    captions(im, t, cap_y)
    out = im.convert('RGB')
    # recoil shake on the AI X-stamp impact
    k = round((t - W_(92) - 0.08) * FPS)
    if k in (0, 1):
        dx = [9, -5][k]; z = 1.02; big = out.resize((int(W * z), int(H * z)), Image.BICUBIC); ox = (big.width - W) // 2 - dx; oy = (big.height - H) // 2
        out = big.crop((ox, oy, ox + W, oy + H)); ImageDraw.Draw(out).rectangle([0, 0, 7, H], fill=GOLD)
    return out

def new_to_old(tn):
    acc = 0
    for a, b in KEEP:
        if tn < acc + (b - a) - 1e-9: return a + (tn - acc)
        acc += b - a
    return KEEP[-1][1] - 1 / SFPS
def src_frame_index(n): return min(int(round(new_to_old(n / FPS) * SFPS)), 2075)

if __name__ == '__main__':
    mode = sys.argv[2]
    if mode == 'stills':
        for tt in [float(x) for x in sys.argv[3:]]:
            k = src_frame_index(round(tt * FPS))
            subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', SRC, '-vf', f'select=eq(n\\,{k})', '-vsync', '0', '-frames:v', '1', WK + '_src.png'])
            frame(Image.open(WK + '_src.png').convert('RGB'), tt).save(S + f'/qc/st_{tt:05.2f}.jpg', quality=88)
        sys.exit()
    n0, n1, out = int(sys.argv[3]), int(sys.argv[4]), sys.argv[5]
    idx = [src_frame_index(n) for n in range(n0, n1)]
    first, last = idx[0], idx[-1]
    dec = subprocess.Popen(['ffmpeg', '-v', 'error', '-i', SRC, '-vf', f'select=between(n\\,{first}\\,{last})', '-vsync', '0', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], stdout=subprocess.PIPE)
    enc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                            '-c:v', 'libx264', '-crf', '12', '-preset', 'medium', '-pix_fmt', 'yuv420p', out], stdin=subprocess.PIPE)
    cur = first - 1; buf = None
    for n, o in zip(range(n0, n1), idx):
        while cur < o:
            buf = dec.stdout.read(W * H * 3); cur += 1
            if len(buf) < W * H * 3: raise SystemExit(f'short read at src frame {cur}')
        enc.stdin.write(frame(Image.frombuffer('RGB', (W, H), buf), n / FPS).tobytes())
    enc.stdin.close(); enc.wait(); dec.kill(); print('done', n0, n1)
