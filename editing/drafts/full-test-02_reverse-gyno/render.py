# Reverse GYNO in 3 steps — 1080x1920 30fps render (PIL compositor, footage untouched)
# usage: python3 render.py <scratch> stills t1 t2 ...   |   python3 render.py <scratch> chunk n0 n1 out.mp4
import json, subprocess, sys, math, random
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops

S = sys.argv[1]; F = S + '/fonts/'; B = S + '/build/'
W, H, FPS = 1080, 1920, 30
WORDS = json.load(open(B + 'words_final.json'))
TR = json.load(open(B + 'trim.json'))
SPEECH_END = round(sum(b - a for a, b in TR['keep']), 4)
DUR = SPEECH_END + 1.0
NFR = int(round(DUR * FPS)); NSRC = int(round(SPEECH_END * FPS))
MID = DUR / 2
CUTS = []; acc = 0
for a, b in TR['keep'][:-1]:
    acc += b - a; CUTS.append(round(acc, 4))

GOLD = (201, 169, 110); CREAM = (244, 241, 234); NAVY = (14, 17, 23); MUTED = (184, 184, 188); DIM = (124, 124, 130)
RED = (255, 34, 28); VGOLD = (255, 194, 26); CYAN = (0, 229, 255); GREEN = (30, 255, 110); DEEP = (2, 3, 8)
INK = (6, 8, 14); WHITE = (255, 255, 255); AMBER = (240, 160, 48); COARED = (210, 10, 20); PAPER = (233, 230, 223)
BEB = 'BebasNeue.woff'; DMB = 'DMSans-700.woff'; DMR = 'DMSans-400.woff'; BAR = 'Barlow-700.woff'; MONO = 'JBMono-500.ttf'; MONOB = 'JBMono-700.ttf'
_fc = {}
def f(n, s):
    k = (n, int(s))
    if k not in _fc: _fc[k] = ImageFont.truetype(F + n, int(s))
    return _fc[k]
def clamp(x, a=0, b=1): return max(a, min(b, x))
def expo(x): x = clamp(x); return 1 if x >= 1 else 1 - 2 ** (-10 * x)
def ease_io(x): x = clamp(x); return 4 * x ** 3 if x < .5 else 1 - (-2 * x + 2) ** 3 / 2
def back(x):  # heavy landing with small settle (no cartoon bounce)
    x = clamp(x); c = 1.2; return 1 + (c + 1) * (x - 1) ** 3 + c * (x - 1) ** 2
def lerp(a, b, t): return a + (b - a) * t
def lerpc(c1, c2, t): return tuple(int(lerp(a, b, clamp(t))) for a, b in zip(c1, c2))
def A(c, a): return tuple(c[:3]) + (int(clamp(a) * 255),)
def appear(t, t0, d=0.16): return expo((t - t0) / d)
def window(t, a, b, i=0.18, o=0.16): return min(appear(t, a, i), 1 - clamp((t - b) / o))

def wt(word, near):
    best = None
    for x in WORDS:
        if word.lower() in x['w'].lower().strip('.,?!'):
            if best is None or abs(x['s'] - near) < abs(best - near): best = x['s']
    if best is None or abs(best - near) > 3: raise SystemExit(f'anchor {word}@{near} not found')
    return best

GL = None
# ---------------- primitives ----------------
def txt(d, x, y, s, font, col, a=1.0, anchor=None):
    d.text((x, y), s, font=font, fill=A(col, a), anchor=anchor)
def tw(d, s, font): return d.textlength(s, font=font)
def lit_bar(d, x0, y0, x1, y1, col, a=1.0):
    h = max(1, int(y1 - y0))
    for i in range(h):
        k = i / h; c = tuple(int(min(255, v * (1.18 - 0.36 * k) + (40 if k < 0.12 else 0))) for v in col)
        d.line([(x0, y0 + i), (x1, y0 + i)], fill=c + (int(255 * a),))
def tag(d, x, y, label, col=RED, size=30, a=1.0, glow=True, align='left', font=MONO):
    fn = f(font, size); w_ = tw(d, label, fn); h = size + 16
    if align == 'right': x = x - w_ - 24
    lit_bar(d, x, y, x + w_ + 24, y + h, col, a)
    txt(d, x + 12, y + 5, label, fn, INK if col in (VGOLD, GREEN, CYAN, GOLD) else WHITE, a)
    if GL and glow: GL.rectangle([x - 4, y - 4, x + w_ + 28, y + h + 4], outline=A(col, a), width=8)
    return x + w_ + 24
def brackets(d, x0, y0, x1, y1, col, L=34, w=4):
    for (cx, cy, sx, sy) in [(x0, y0, 1, 1), (x1, y0, -1, 1), (x0, y1, 1, -1), (x1, y1, -1, -1)]:
        d.line([(cx, cy), (cx + sx * L, cy)], fill=col, width=w); d.line([(cx, cy), (cx, cy + sy * L)], fill=col, width=w)
def check(d, x, y, col, s=1.0, a=1.0):
    pts = [(x, y + 16 * s), (x + 10 * s, y + 28 * s), (x + 30 * s, y + 2 * s)]
    d.line(pts, fill=A(col, a), width=int(6 * s), joint='curve')
    if GL: GL.line(pts, fill=A(col, a), width=int(12 * s))
def cross(d, x, y, col, s=1.0, a=1.0):
    for p in ([(x, y), (x + 28 * s, y + 28 * s)], [(x + 28 * s, y), (x, y + 28 * s)]):
        d.line(p, fill=A(col, a), width=int(6 * s))
        if GL: GL.line(p, fill=A(col, a), width=int(12 * s))
def arrow(d, x0, y0, x1, y1, col, w=5, a=1.0):
    d.line([(x0, y0), (x1, y1)], fill=A(col, a), width=w)
    ang = math.atan2(y1 - y0, x1 - x0); L = 18
    d.polygon([(x1, y1), (x1 - L * math.cos(ang - 0.45), y1 - L * math.sin(ang - 0.45)), (x1 - L * math.cos(ang + 0.45), y1 - L * math.sin(ang + 0.45))], fill=A(col, a))
def flow(d, x0, y0, x1, y1, t, col, n=4, speed=0.9, a=1.0, r=7):
    for k in range(n):
        p = (t * speed + k / n) % 1; x = lerp(x0, x1, p); y = lerp(y0, y1, p); fa = a * min(1, p * 6, (1 - p) * 6)
        d.ellipse([x - r, y - r, x + r, y + r], fill=A(col, fa))
        if GL: GL.ellipse([x - r * 2, y - r * 2, x + r * 2, y + r * 2], fill=A(col, fa))
def node(d, box, title, sub, col, a=1.0, dim=False, size=44):
    x0, y0, x1, y1 = box; c = col if not dim else tuple(int(v * 0.35) for v in col)
    d.rounded_rectangle(box, radius=14, fill=A((10, 14, 24), 0.95 * a), outline=A(c, a), width=4)
    if GL and not dim: GL.rounded_rectangle(box, radius=14, outline=A(col, a * 0.7), width=8)
    fn = f(BEB, size); txt(d, (x0 + x1) / 2, y0 + 14, title, fn, WHITE if not dim else (110, 110, 120), a, 'mt')
    if sub: txt(d, (x0 + x1) / 2, y1 - 14, sub, f(MONO, 22), c, a, 'mb')
def frosted(im, box, dark=0.86, blur=10, radius=0):
    x0, y0, x1, y1 = [int(v) for v in box]
    x0 = max(0, x0); y0 = max(0, y0); x1 = min(W, x1); y1 = min(H, y1)
    if x1 <= x0 or y1 <= y0: return
    reg = im.crop((x0, y0, x1, y1)).convert('RGB').filter(ImageFilter.GaussianBlur(blur))
    reg = Image.blend(reg, Image.new('RGB', reg.size, DEEP), dark)
    if radius:
        m = Image.new('L', reg.size, 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, reg.width - 1, reg.height - 1], radius=radius, fill=255)
        im.paste(reg.convert('RGBA'), (x0, y0), m)
    else: im.paste(reg.convert('RGBA'), (x0, y0))
def frosted_a(im, box, a, dark=0.86, blur=10, radius=18):
    """frosted panel with fade alpha a"""
    if a <= 0.01: return
    x0, y0, x1, y1 = [int(v) for v in box]
    x0 = max(0, x0); y0 = max(0, y0); x1 = min(W, x1); y1 = min(H, y1)
    if x1 <= x0 or y1 <= y0: return
    reg = im.crop((x0, y0, x1, y1)).convert('RGB')
    fr = Image.blend(reg.filter(ImageFilter.GaussianBlur(blur)), Image.new('RGB', reg.size, DEEP), dark)
    m = Image.new('L', reg.size, 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, reg.width - 1, reg.height - 1], radius=radius, fill=int(255 * a))
    im.paste(fr.convert('RGBA'), (x0, y0), m)

# static textures
rng = np.random.default_rng(3)
def make_bg():
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    g = np.exp(-(((xx - 1000) / 700) ** 2 + ((yy - 150) / 600) ** 2))
    base = np.array(NAVY, np.float32)[None, None, :] + g[..., None] * np.array([18, 16, 12], np.float32)
    base += rng.normal(0, 2.2, (H, W, 1))
    im = Image.fromarray(np.clip(base, 0, 255).astype(np.uint8)).convert('RGBA')
    d = ImageDraw.Draw(im, 'RGBA')
    for x in range(0, W, 60): d.line([(x, 0), (x, H)], fill=(255, 255, 255, 7))
    for y in range(0, H, 60): d.line([(0, y), (W, y)], fill=(255, 255, 255, 7))
    return im
BG = make_bg()
def make_panel_tex():
    p = Image.new('RGBA', (W, 900), (8, 11, 19, 255)); d = ImageDraw.Draw(p, 'RGBA')
    for x in range(0, W, 48): d.line([(x, 0), (x, 900)], fill=(120, 140, 170, 10))
    for y in range(0, 900, 48): d.line([(0, y), (W, y)], fill=(120, 140, 170, 10))
    n = (rng.normal(0, 3, (900, W)) + 0).clip(-8, 8)
    arr = np.asarray(p).astype(np.int16); arr[..., :3] += n[..., None].astype(np.int16)
    return Image.fromarray(arr.clip(0, 255).astype(np.uint8))
PANEL_TEX = make_panel_tex()
LOGO = Image.open('/home/user/coach-agz-/editing/brand/logo/coach-agz-logo-round.jpg').convert('RGB').resize((132, 132), Image.LANCZOS)
LOGO_M = Image.new('L', (132, 132), 0); ImageDraw.Draw(LOGO_M).ellipse([0, 0, 131, 131], fill=255)

# ---------------- timing anchors (cut timeline) ----------------
T = {}
def a(key, word, near): T[key] = wt(word, near)
a('trt', 'TRT', 0.5); a('nipple', "nipple", 2.3)
a('rightnow', 'right', 11.0); a('reverse1', 'reverse', 13.2); a('months1', 'months', 15.0); a('surgical', 'surgical', 16.8)
a('soft', 'soft', 22.5); a('glandular', 'glandular', 23.3); a('back', 'back', 25.0); a('after', 'after', 27.6); a('hard', 'hard', 29.5)
a('fibrotic', 'fibrotic', 30.0); a('noprot', 'protocol', 31.8); a('touch', 'touch', 32.6)
a('three', 'three', 33.4); a('step1', 'step', 37.6); a('driver1', 'driver', 39.2); a('trt2', 'TRT', 40.9); a('estradiol1', 'estradiol', 41.6)
a('anab2', 'anabolics', 43.0); a('prl1', 'prolactin', 44.0); a('aromat', 'aromatization', 46.3); a('npp', 'NPP', 47.5); a('deca', 'DECA', 48.3)
a('table', 'table', 49.6); a('sensitive', 'sensitive', 51.6); a('prl2', 'prolactin', 53.0); a('anything', 'anything', 54.6); a('asap', 'possible', 55.8)
a('step2', 'step', 56.5); a('rootcause', 'cause', 59.0); a('crash', 'crash', 60.0); a('range1', 'range', 61.8); a('prl3', 'prolactin', 62.6); a('range2', 'range', 63.8)
a('nuke', 'nuke', 64.8); a('zero', 'zero', 65.4); a('joints', 'joints', 67.4); a('libido', 'libido', 68.4); a('mood', 'mood', 69.4); a('tool', 'tool', 71.1)
a('step3', 'step', 73.6); a('biomarker', 'biomarker', 75.0); a('worse', 'worse', 77.6); a('shrink', 'shrink', 79.0); a('tissue3', 'tissue', 80.8)
a('selective', 'selective', 81.3); a('modulator', 'modulator', 82.8); a('ralox', 'Raloxifene', 83.8); a('nolva', 'Nolvadex', 85.0); a('serms', 'SERMs', 86.1)
a('block', 'block', 87.6); a('breast', 'breast', 88.6)
a('clients', 'clients', 91.8); a('blast', 'blast', 93.0); a('testimonial', 'testimonial', 99.4); a('forever', 'forever', 100.6); a('privacy', 'privacy', 103.6)
a('client2', 'client', 106.2); a('e2c', 'E2', 107.2); a('n120', '120', 107.9); a('fine', 'fine', 110.0); a('lump', 'lump', 111.2); a('weeks1', 'weeks', 113.0)
a('found', 'found', 114.2); a('corrected', 'corrected', 115.0); a('treated', 'treated', 115.9); a('gone', 'gone', 117.3); a('four', 'four', 118.0); a('weeks2', 'weeks', 118.4)
a('ment1', 'MENT', 124.6); a('aromatizes', 'aromatizes', 125.4); a('crazy', 'crazy', 126.5); a('dontrun', 'run', 128.6)
a('protocol9', 'protocol', 130.8); a('blood9', 'blood', 132.5); a('free', 'free', 133.9); a('comment', 'Comment', 134.8); a('gyno9', 'GYNO', 135.2)

HOOK_END = 4.8
SPLITS = [(T['rightnow'] - 0.55, T['surgical'] + 1.6), (T['step3'] - 0.3, T['breast'] + 1.9)]
PIPS = [(T['step1'] - 0.35, T['step2'] - 0.3), (T['client2'] - 1.0, T['weeks2'] + 2.2)]
def env(t, ab, i=0.38, o=0.32):
    a_, b_ = ab
    return min(ease_io((t - a_) / i), 1 - ease_io((t - b_) / o))
def layout(t):
    s = max([clamp(env(t, x)) for x in SPLITS] + [0]); p = max([clamp(env(t, x)) for x in PIPS] + [0])
    return s, p
SHIFT = 400; PANEL_Y = 1070
PIP_CROP = (140, 380, 940, 1380); PIP_DST = (580, 262, 1040, 837)

def seg_of(t): return sum(1 for c in CUTS if c <= t + 1e-6)
def zoom_at(t):
    if t < T['trt']: return 1.0
    z = 1.06 if seg_of(t) % 2 == 0 else 1.0
    if seg_of(t) == 0: z = lerp(1.0, 1.06, expo((t - T['trt']) / 0.12))
    return z

# ---------------- scenes ----------------
def sc_window(im, d, t, dy):
    """SPLIT: reversal-window line graph"""
    t0 = SPLITS[0][0]
    x0 = 80; txt(d, 80 + 0, 1092 + dy, '', f(BAR, 34), GOLD)
    d.line([(80, 1112 + dy), (120, 1112 + dy)], fill=A(GOLD, 1), width=4)
    txt(d, 134, 1092 + dy, 'REVERSAL WINDOW', f(BAR, 38), GOLD)
    txt(d, 1000, 1098 + dy, 'TIME SINCE FIRST SYMPTOM', f(MONO, 22), MUTED, 1, 'ra')
    cx0, cx1, cy0, cy1 = 120, 1000, 1200 + dy, 1470 + dy
    d.line([(cx0, cy1), (cx1, cy1)], fill=A((90, 96, 112), 1), width=2); d.line([(cx0, cy0 - 10), (cx0, cy1)], fill=A((90, 96, 112), 1), width=2)
    txt(d, cx1, cy0 - 30, 'REVERSIBILITY', f(MONO, 20), DIM, 1, 'ra')
    r = lambda u: 1 / (1 + math.exp((u - 0.45) * 12))
    px = lambda u: lerp(cx0, cx1, u); py = lambda u: cy1 - (cy1 - cy0 - 10) * r(u)
    colu = lambda u: GREEN if u < 0.3 else (lerpc(GREEN, AMBER, (u - .3) / .15) if u < .45 else lerpc(AMBER, RED, (u - .45) / .15))
    ud = ease_io((t - (t0 + 0.25)) / 1.3)
    N = 90; pts = [(px(i / N), py(i / N)) for i in range(N + 1) if i / N <= ud]
    for i in range(len(pts) - 1):
        u = i / N; c = colu(u)
        d.polygon([pts[i], pts[i + 1], (pts[i + 1][0], cy1), (pts[i][0], cy1)], fill=A(c, 0.22))
    for i in range(len(pts) - 1):
        c = colu(i / N); d.line([pts[i], pts[i + 1]], fill=A(c, 1), width=6)
        if GL: GL.line([pts[i], pts[i + 1]], fill=A(c, 0.9), width=10)
    for u, lab in [(0.05, 'WEEK 1'), (0.32, 'WEEKS'), (0.8, 'MONTHS')]:
        if ud > u: txt(d, px(u), cy1 + 10, lab, f(MONO, 26), MUTED, appear(t, t0 + 0.25 + 1.3 * u, 0.2), 'ma')
    # surgical zone hatch
    if t >= T['surgical']:
        p = expo((t - T['surgical']) / 0.25); xs = px(0.62)
        for k in range(0, 900, 22):
            xa = xs + k;
            if xa > cx1: break
            d.line([(xa, cy1), (min(cx1, xa + (cy1 - cy0) * 0.5), cy0)], fill=A(RED, 0.35 * p), width=3)
        d.rectangle([xs, cy0, cx1, cy1], outline=A(RED, p), width=3)
    # marker
    if t >= T['rightnow']:
        um = 0.06 if t < T['months1'] else lerp(0.06, 0.8, ease_io((t - T['months1']) / 1.1))
        mx, my = px(um), py(um); c = colu(um); pa = appear(t, T['rightnow'], 0.12)
        pul = (t * 1.6) % 1
        d.ellipse([mx - 30 * pul, my - 30 * pul, mx + 30 * pul, my + 30 * pul], outline=A(c, (1 - pul) * pa), width=3)
        d.ellipse([mx - 12, my - 12, mx + 12, my + 12], fill=A(c, pa), outline=A(WHITE, pa), width=3)
        if GL: GL.ellipse([mx - 20, my - 20, mx + 20, my + 20], fill=A(c, pa))
        for yy in range(int(my + 16), int(cy1), 14): d.line([(mx, yy), (mx, min(cy1, yy + 7))], fill=A(c, pa * 0.8), width=2)
        if t < T['months1']:
            lab = 'NOW' if t < T['reverse1'] else 'NOW · BEST TIME TO REVERSE'
            tag(d, mx + 28, my - 6, lab, GREEN, 30, pa)
        elif t < T['surgical']:
            tag(d, mx - 28, my - 80, 'WAITING', AMBER, 30, 1, align='right')
        else:
            p = back((t - T['surgical']) / 0.22); tag(d, mx - 28, my - 84, 'SURGICAL ONLY', RED, 34, clamp(p * 1.4), align='right')

def lens(im, lay, d, cx, cy, r, t, t0, kind, t_out):
    p = expo((t - t0) / 0.32); q = 1 - clamp((t - t_out) / 0.18)
    if p <= 0 or q <= 0: return
    al = q; s = lerp(0.9, 1.0, p) * lerp(1, 0.96, 1 - q); rr = r * s
    # frosted disc
    box = (int(cx - rr), int(cy - rr), int(cx + rr), int(cy + rr))
    reg = im.crop(box).convert('RGB').filter(ImageFilter.GaussianBlur(9)); reg = Image.blend(reg, Image.new('RGB', reg.size, DEEP), 0.82)
    # interior content
    sz = reg.size; inner = Image.new('RGBA', sz, (0, 0, 0, 0)); di = ImageDraw.Draw(inner, 'RGBA'); c0 = sz[0] / 2
    if kind == 'soft':
        random.seed(5)
        for k in range(9):
            ang = k * 0.7 + 0.3; dist = (0 if k == 0 else 34 + (k % 3) * 22)
            ox = c0 + dist * math.cos(ang); oy = c0 + dist * math.sin(ang); rad = 30 + 6 * math.sin(t * 2.2 + k) - (k % 3) * 4
            di.ellipse([ox - rad, oy - rad, ox + rad, oy + rad], outline=A(CYAN, 0.9), width=3, fill=A(CYAN, 0.10))
            di.ellipse([ox - 5, oy - 5, ox + 5, oy + 5], fill=A(CYAN, 0.7))
        sy = (t * 0.7 % 1) * sz[1]; di.line([(0, sy), (sz[0], sy)], fill=A(CYAN, 0.8), width=3)
        col = CYAN
    else:
        random.seed(9)
        di.ellipse([c0 - 62, c0 - 50, c0 + 62, c0 + 54], fill=A((120, 10, 12), 0.8))
        for k in range(46):
            ang = random.uniform(0, math.pi); L = random.uniform(40, 110); ox = c0 + random.uniform(-50, 50); oy = c0 + random.uniform(-50, 50)
            jit = math.sin(t * 3 + k) * 1.5
            di.line([(ox - L * math.cos(ang), oy - L * math.sin(ang) + jit), (ox + L * math.cos(ang), oy + L * math.sin(ang) - jit)], fill=A(lerpc(RED, AMBER, random.random() * 0.4), 0.75), width=2)
        sy = (t * 0.7 % 1) * sz[1]; di.line([(0, sy), (sz[0], sy)], fill=A(RED, 0.7), width=3)
        col = RED
    blur = 6 * (1 - p)
    if blur > 0.3: inner = inner.filter(ImageFilter.GaussianBlur(blur))
    disc = reg.convert('RGBA'); disc.alpha_composite(inner)
    m = Image.new('L', sz, 0); ImageDraw.Draw(m).ellipse([0, 0, sz[0] - 1, sz[1] - 1], fill=int(255 * al * p))
    im.paste(disc, box[:2], m)
    # ring draws on
    sweep = 360 * expo((t - t0) / 0.28)
    d.arc([cx - rr, cy - rr, cx + rr, cy + rr], -90, -90 + sweep, fill=A(col, al), width=5)
    if GL: GL.arc([cx - rr, cy - rr, cx + rr, cy + rr], -90, -90 + sweep, fill=A(col, al), width=10)
    for ang in (0, 90, 180, 270):
        ca, sa = math.cos(math.radians(ang)), math.sin(math.radians(ang))
        d.line([(cx + ca * (rr + 4), cy + sa * (rr + 4)), (cx + ca * (rr + 18), cy + sa * (rr + 18))], fill=A(col, al * p), width=4)
    lab = 'EARLY' if kind == 'soft' else 'LATE'
    txt(d, cx, cy + rr - 34, lab, f(MONOB, 22), WHITE, al * p, 'mt')

def sc_lenses(im, lay, d, t):
    tout = T['three'] - 0.15
    Lc, Rc, r = (162, 532), (918, 532), 118
    lens(im, lay, d, Lc[0], Lc[1], r, t, T['soft'] - 0.12, 'soft', tout)
    lens(im, lay, d, Rc[0], Rc[1], r, t, T['after'] - 0.1, 'hard', tout)
    q = 1 - clamp((t - tout) / 0.18)
    if t >= T['glandular']: tag(d, 34, 668, 'SOFT · GLANDULAR', CYAN, 22, appear(t, T['glandular']) * q)
    if t >= T['back']:
        aa = appear(t, T['back']) * q; tag(d, 34, 718, 'REVERSIBLE', GREEN, 26, aa); check(d, 228, 724, GREEN, 0.9, aa)
    if t >= T['hard']: tag(d, 1046, 668, 'HARD · FIBROTIC', RED, 22, appear(t, T['hard']) * q, align='right')
    if t >= T['noprot']:
        aa = appear(t, T['noprot']) * q; tag(d, 1046, 718, 'SURGICAL ONLY', RED, 26, aa, align='right')

STEPS = [('01', 'FIND'), ('02', 'CORRECT'), ('03', 'TREAT')]
def step_state(t):
    if t < T['step1']: return 0
    if t < T['step2']: return 1
    if t < T['step3']: return 2
    return 3
def pills(d, x, y, t, a, size=22, show_t=None):
    st = step_state(t)
    for i, (n, lab) in enumerate(STEPS):
        pa = a * (appear(t, show_t + 0.18 * i, 0.14) if show_t is not None else 1)
        if pa <= 0: x += 10; continue
        s = f'{n} {lab}'; fn = f(MONOB, size); w_ = tw(d, s, fn) + 22; h = size + 16
        if st == i + 1:
            lit_bar(d, x, y, x + w_, y + h, VGOLD, pa); txt(d, x + 11, y + 6, s, fn, INK, pa)
            if GL: GL.rectangle([x - 3, y - 3, x + w_ + 3, y + h + 3], outline=A(VGOLD, pa), width=8)
        elif st > i + 1:
            d.rectangle([x, y, x + w_, y + h], outline=A(GREEN, pa), width=2); txt(d, x + 11, y + 6, s, fn, GREEN, pa)
        else:
            d.rectangle([x, y, x + w_, y + h], outline=A(DIM, pa), width=2); txt(d, x + 11, y + 6, s, fn, MUTED, pa)
        x += w_ + 10
    return x

def sc_step1(im, d, t):
    """PIP: decision tree -> lab requisition"""
    t0 = PIPS[0][0]; a0 = appear(t, t0 + 0.15, 0.25)
    d.line([(64, 300), (64 + 44 * a0, 300)], fill=A(GOLD, a0), width=4)
    txt(d, 122, 280, 'STEP 01', f(BAR, 38), GOLD, a0)
    h1 = appear(t, t0 + 0.3, 0.2); h2 = appear(t, T['driver1'], 0.16)
    txt(d, 60, 340 + 30 * (1 - h1), 'FIND THE', f(BEB, 132), CREAM, h1)
    fn = f(BEB, 176); txt(d, 58, 460 + 30 * (1 - h2), 'DRIVER', fn, VGOLD, h2)
    if GL and h2 > 0: GL.text((58, 460), 'DRIVER', font=fn, fill=A(VGOLD, 0.35 * h2))
    pills(d, 60, 690, t, a0, 20)
    # tree
    tree_out = T['sensitive'] - 0.25; tq = 1 - ease_io((t - tree_out) / 0.3); dyq = -40 * (1 - tq)
    if tq > 0:
        aA = appear(t, T['trt2'] - 0.1); aE = appear(t, T['estradiol1'] - 0.05)
        aB = appear(t, T['anab2'] - 0.1); aP = appear(t, T['prl1'] - 0.05)
        if aA > 0: node(d, (60, 905 + dyq, 430, 1015 + dyq), 'ON TRT', None, CYAN, aA * tq)
        if aE > 0:
            arrow(d, 440, 960 + dyq, 588, 960 + dyq, VGOLD, 5, aE * tq); flow(d, 440, 960 + dyq, 580, 960 + dyq, t, VGOLD, 3, a=aE * tq)
            sub = 'LIKELY' if t < T['aromat'] else 'VIA AROMATIZATION'
            node(d, (600, 905 + dyq, 1020, 1015 + dyq), 'ESTRADIOL  E2', sub, VGOLD, aE * tq)
        if aB > 0: node(d, (60, 1065 + dyq, 430, 1175 + dyq), 'OTHER ANABOLICS', None, CYAN, aB * tq)
        if aP > 0:
            on = t >= T['table']
            arrow(d, 440, 1120 + dyq, 588, 1120 + dyq, VGOLD if on else MUTED, 5, aP * tq)
            if on: flow(d, 440, 1120 + dyq, 580, 1120 + dyq, t, VGOLD, 3, a=aP * tq)
            node(d, (600, 1065 + dyq, 1020, 1175 + dyq), 'PROLACTIN', 'POSSIBLE' if not on else 'ON THE TABLE', VGOLD, aP * tq)
        x = 60
        for k, tt in (('NPP', T['npp']), ('DECA', T['deca'])):
            if t >= tt:
                p = back((t - tt) / 0.2); yy = 1192 + dyq + 20 * (1 - p)
                fn = f(BAR, 34); w_ = tw(d, k, fn) + 30
                d.rectangle([x, yy, x + w_, yy + 50], fill=A((40, 12, 18), tq), outline=A(RED, tq), width=2)
                txt(d, x + 15, yy + 6, k, fn, (255, 140, 130), tq); x += w_ + 12
    # lab requisition paper
    if t >= T['sensitive'] - 0.25:
        p = expo((t - (T['sensitive'] - 0.25)) / 0.32); ox = 900 * (1 - p); rot = 3 * (1 - p)
        pw, ph = 950, 390
        pap = Image.new('RGBA', (pw, ph), (0, 0, 0, 0)); pd = ImageDraw.Draw(pap, 'RGBA')
        pd.rectangle([0, 0, pw - 1, ph - 1], fill=PAPER + (255,))
        pd.rectangle([0, 0, pw, 64], fill=COARED + (255,))
        pd.text((24, 14), 'LAB REQUISITION', font=f(MONOB, 30), fill=WHITE)
        pd.text((pw - 24, 20), 'PRE-TREATMENT', font=f(MONO, 22), fill=(255, 220, 220), anchor='ra')
        rows = [('ESTRADIOL (E2), SENSITIVE', T['sensitive'] + 0.1), ('PROLACTIN', T['prl2'] + 0.05)]
        for i, (lab, tt) in enumerate(rows):
            y = 96 + i * 76
            pd.rectangle([24, y, 64, y + 40], outline=(40, 40, 46, 255), width=3)
            pd.text((86, y + 2), lab, font=f(DMB, 32), fill=(24, 24, 30))
            pd.line([(24, y + 58), (pw - 24, y + 58)], fill=(190, 186, 178), width=2)
            if t >= tt:
                q = expo((t - tt) / 0.12); pd.line([(30, y + 20), (42, y + 34), (42 + 24 * q, y + 34 - 34 * q)], fill=(20, 150, 70), width=7)
        pd.text((24, 262), 'ORDERED BY  ____________', font=f(MONO, 22), fill=(110, 108, 104))
        nz = Image.effect_noise((pw, ph), 18).convert('L').point(lambda v: 0 if v > 110 else 22)
        pap.alpha_composite(Image.merge('RGBA', [nz.point(lambda v: 0)] * 3 + [nz]))
        if rot: pap = pap.rotate(rot, resample=Image.BICUBIC, expand=True)
        sh = Image.new('RGBA', (pap.width + 60, pap.height + 60), (0, 0, 0, 0)); ImageDraw.Draw(sh).rectangle([30, 40, pap.width + 30, pap.height + 40], fill=(0, 0, 0, 150))
        sh = sh.filter(ImageFilter.GaussianBlur(14))
        px0 = int(65 + ox); py0 = 900
        im.alpha_composite(sh, (px0 - 30, py0 - 30)); im.alpha_composite(pap, (px0, py0))
        if t >= T['anything'] - 0.05:
            tag(d, px0 + 24, py0 + 300, 'DRAW BEFORE ANY CHANGE', RED, 28, appear(t, T['anything'] - 0.05))
        if t >= T['asap']:
            q = back((t - T['asap']) / 0.18); st = Image.new('RGBA', (300, 130), (0, 0, 0, 0)); sd = ImageDraw.Draw(st)
            sd.rectangle([4, 4, 295, 125], outline=RED + (235,), width=8); sd.text((150, 66), 'ASAP', font=f(BEB, 104), fill=RED + (235,), anchor='mm')
            sc = lerp(1.5, 1.0, q); st = st.resize((int(300 * sc), int(130 * sc)), Image.BICUBIC).rotate(-9, expand=True, resample=Image.BICUBIC)
            st.putalpha(st.split()[3].point(lambda v: int(v * clamp(q * 2))))
            im.alpha_composite(st, (int(px0 + 760 - st.width / 2), int(py0 + 200 - st.height / 2)))

def spectrum_row(d, y, label, u, t, a, col_marker, dim=False):
    x0, x1 = 190, 990
    txt(d, 80, y - 14, label, f(BEB, 56), WHITE if not dim else DIM, a)
    zones = [(0, .22, RED), (.22, .58, GREEN), (.58, 1, AMBER)]
    for z0, z1, c in zones:
        cc = c if not dim else tuple(int(v * .35) for v in c)
        lit_bar(d, lerp(x0, x1, z0) + 2, y, lerp(x0, x1, z1) - 2, y + 34, cc, a * 0.9)
    mx = lerp(x0, x1, u); c = col_marker if not dim else DIM
    d.polygon([(mx - 16, y - 24), (mx + 16, y - 24), (mx, y - 2)], fill=A(WHITE, a)); d.line([(mx, y - 4), (mx, y + 40)], fill=A(WHITE, a), width=4)
    if GL and not dim: GL.ellipse([mx - 22, y - 10, mx + 22, y + 44], fill=A(c, a * 0.8))

def sc_step2(im, d, t):
    t0 = T['step2']; tout = T['tool'] + 1.7
    a_ = window(t, t0 - 0.05, tout, 0.22, 0.2)
    if a_ <= 0: return
    PB = (52, 332, 1028, 652)
    frosted_a(im, PB, a_, 0.86, 10, 20); d = ImageDraw.Draw(im, 'RGBA')
    d.rounded_rectangle(PB, radius=20, outline=A(VGOLD, 0.6 * a_), width=2)
    txt(d, 80, 344, 'STEP 02 · BRING IT INTO RANGE', f(MONO, 22), VGOLD, a_)
    Y1, Y2 = 412, 512
    if t < T['range1']: u = 0.86
    elif t < T['nuke']: u = lerp(0.86, 0.40, ease_io((t - T['range1']) / 0.6))
    else: u = lerp(0.40, 0.04, expo((t - T['nuke'] - 0.25) / 0.3))
    col = AMBER if u > .58 else (GREEN if u > .22 else RED)
    sw = ease_io((t - t0) / 0.5)
    spectrum_row(d, Y1, 'E2', u, t, a_ * sw, col)
    for uu, lab in [(0.11, 'CRASHED'), (0.40, 'IN RANGE'), (0.79, 'HIGH')]:
        txt(d, lerp(190, 990, uu), Y1 + 40, lab, f(MONO, 20), MUTED, a_ * sw, 'ma')
    if T['range1'] + 0.6 <= t < T['nuke']: check(d, lerp(190, 990, 0.40) + 30, Y1 - 46, GREEN, 0.8, a_)
    zx = lerp(190, 990, 0.22)
    if T['crash'] <= t < T['range1'] + 0.4:
        p = appear(t, T['crash'], 0.12); brackets(d, 186, Y1 - 18, zx, Y1 + 40, A(RED, p * a_), 18, 5)
    if t >= T['nuke'] + 0.25:
        p = appear(t, T['nuke'] + 0.5, 0.12); brackets(d, 186, Y1 - 18, zx, Y1 + 40, A(RED, p * a_), 18, 5)
        if GL: brackets(GL, 186, Y1 - 18, zx, Y1 + 40, A(RED, p * a_), 18, 10)
    if t >= T['prl3'] - 0.1:
        pa = a_ * appear(t, T['prl3'] - 0.1, 0.25); dim = t >= T['tool']
        up = 0.82 if t < T['range2'] else lerp(0.82, 0.42, ease_io((t - T['range2']) / 0.55))
        spectrum_row(d, Y2, 'PRL', up, t, pa, GREEN if up < .58 else AMBER, dim=dim)
        if dim: tag(d, 1010, Y2 - 8, 'SEPARATE PROTOCOL', VGOLD, 22, appear(t, T['tool'], 0.15) * a_, align='right')
    if t >= T['joints'] - 0.35:
        ca = window(t, T['joints'] - 0.35, tout, 0.2, 0.2)
        txt(d, 80, 580, 'TRADE-OFF', f(MONO, 20), RED, ca)
        x = 210
        for lab, tt in (('DEAD JOINTS', T['joints'] - 0.2), ('NO LIBIDO', T['libido'] - 0.15), ('FLAT MOOD', T['mood'] - 0.15)):
            if t < tt: break
            p = expo((t - tt) / 0.16); fn = f(BAR, 38); w_ = tw(d, lab, fn) + 30; yy = 566 - 24 * (1 - p)
            d.rectangle([x, yy, x + w_, yy + 56], fill=A((40, 12, 18), 0.95 * ca), outline=A(RED, ca * p), width=3)
            txt(d, x + 15, yy + 7, lab, fn, (255, 150, 140), ca * p)
            if GL: GL.rectangle([x, yy, x + w_, yy + 56], outline=A(RED, ca * p), width=8)
            x += w_ + 12

def receptor(d, cx, cy, col, a, k=1.6):
    pts = [(cx - 90 * k, cy), (cx - 40 * k, cy), (cx - 40 * k, cy - 60 * k), (cx + 40 * k, cy - 60 * k), (cx + 40 * k, cy), (cx + 90 * k, cy)]
    d.line(pts[:3], fill=A(col, a), width=7); d.line(pts[3:], fill=A(col, a), width=7)
    if GL: GL.line(pts[:3], fill=A(col, a * 0.6), width=12); GL.line(pts[3:], fill=A(col, a * 0.6), width=12)
def hexa(d, cx, cy, r, col, a, label='E'):
    pts = [(cx + r * math.cos(math.pi / 3 * i), cy + r * math.sin(math.pi / 3 * i)) for i in range(6)]
    d.polygon(pts, fill=A((30, 22, 6), a), outline=A(col, a)); d.line(pts + [pts[0]], fill=A(col, a), width=4)
    if GL: GL.polygon(pts, fill=A(col, a * 0.5))
    txt(d, cx, cy + 1, label, f(BEB, int(r * 1.15)), col, a, 'mm')

def sc_step3(im, d, t, dy):
    a0 = 1
    d.line([(80, 1112 + dy), (120, 1112 + dy)], fill=A(GOLD, 1), width=4)
    txt(d, 134, 1092 + dy, 'STEP 03', f(BAR, 38), GOLD); txt(d, 270, 1090 + dy, 'TREAT THE TISSUE', f(BEB, 52), CREAM)
    pills(d, 640, 1092 + dy, t, 1, 18)
    phB = T['tissue3'] - 0.2
    qa = 1 - ease_io((t - phB) / 0.3); ox = -600 * (1 - qa)
    if qa > 0:
        # card 1 biomarker
        a1 = appear(t, T['biomarker'] - 0.1, 0.2) * qa
        if a1 > 0:
            b = (60 + ox, 1170 + dy, 520 + ox, 1460 + dy); d.rounded_rectangle(b, radius=16, fill=A((10, 14, 24), 0.95 * a1), outline=A(GREEN, a1), width=3)
            txt(d, b[0] + 24, b[1] + 20, 'BIOMARKER CORRECTED', f(MONO, 24), GREEN, a1)
            check(d, b[0] + 30, b[1] + 80, GREEN, 2.2, a1)
            if t >= T['worse'] - 0.3: txt(d, b[0] + 120, b[1] + 86, 'STOPS GROWTH', f(BEB, 64), WHITE, appear(t, T['worse'] - 0.3) * qa)
            if t >= T['worse'] - 0.3: txt(d, b[0] + 24, b[1] + 200, 'NEW TISSUE STOPS FORMING', f(MONO, 20), MUTED, appear(t, T['worse']) * qa)
        a2 = appear(t, T['shrink'] - 0.6, 0.2) * qa
        if a2 > 0:
            b = (560 + ox, 1170 + dy, 1020 + ox, 1460 + dy); d.rounded_rectangle(b, radius=16, fill=A((10, 14, 24), 0.95 * a2), outline=A(RED, a2), width=3)
            txt(d, b[0] + 24, b[1] + 20, 'EXISTING TISSUE', f(MONO, 24), RED, a2)
            cx, cy = b[0] + 110, b[1] + 150
            random.seed(2)
            for k in range(7):
                rr = 26 + k % 3 * 6; ang = k * 0.9; dd = 0 if k == 0 else 34
                d.ellipse([cx + dd * math.cos(ang) - rr, cy + dd * math.sin(ang) - rr, cx + dd * math.cos(ang) + rr, cy + dd * math.sin(ang) + rr], outline=A(RED, a2), width=3, fill=A(RED, 0.15 * a2))
            if t >= T['shrink']:
                q = appear(t, T['shrink'], 0.14); txt(d, b[0] + 220, b[1] + 100, "WON'T", f(BEB, 64), WHITE, q * qa); txt(d, b[0] + 220, b[1] + 160, 'SHRINK', f(BEB, 64), RED, q * qa)
                cross(d, b[0] + 380, b[1] + 26, RED, 1.0, q * qa)
    if t >= phB:
        pb = appear(t, phB, 0.3)
        # left column: SERM tags
        cx, cy = 770, 1420 + dy; K = 1.6
        d.line([(470, cy), (1030, cy)], fill=A((120, 130, 150), pb), width=3)
        for k in range(470, 1030, 26): d.line([(k, cy + 8), (k + 12, cy + 8)], fill=A((80, 88, 104), pb), width=2)
        blocked = t >= T['modulator']
        rc = CYAN if blocked else (RED if t >= phB + 0.7 else WHITE)
        receptor(d, cx, cy, rc, pb, K)
        lab_on = t >= T['breast'] - 0.1
        txt(d, cx, cy + 22, 'BREAST TISSUE RECEPTOR', f(MONO, 26), VGOLD if lab_on else MUTED, pb, 'ma')
        if lab_on and GL: GL.rectangle([cx - 200, cy + 20, cx + 200, cy + 54], outline=A(VGOLD, 0.6), width=4)
        dock = (cx, cy - 46)
        for k in range(3):
            ph = ((t - phB) * 0.55 + k / 3) % 1
            sx, sy = 520, 1200 + dy
            if not blocked:
                q = min(1, ph * 1.25); x = lerp(sx, dock[0], q); y = lerp(sy, dock[1], q)
                hexa(d, x, y, 36, VGOLD, pb * min(1, (1 - ph) * 5))
            else:
                hit = (cx - 120, cy - 150)
                if ph < 0.6: x = lerp(sx, hit[0], ph / 0.6); y = lerp(sy, hit[1], ph / 0.6)
                else: x = lerp(hit[0], 560, (ph - .6) / .4); y = lerp(hit[1], 1170 + dy, (ph - .6) / .4)
                hexa(d, x, y, 36, VGOLD, pb * min(1, (1 - ph) * 5, ph * 6))
                if 0.55 < ph < 0.72 and t >= T['block']: cross(d, hit[0] + 10, hit[1] - 50, RED, 1.1, 1)
        if phB + 0.7 <= t < T['modulator']: tag(d, cx + 150, cy - 150, 'GROWTH SIGNAL', RED, 26, appear(t, phB + 0.7), align='right')
        if t >= T['selective'] - 0.1:
            p = back((t - T['modulator']) / 0.25) if blocked else 0
            ky = lerp(1160 + dy, cy - 60 * K, p) if blocked else 1160 + dy
            ka = appear(t, T['selective'] - 0.1, 0.2)
            d.rounded_rectangle([cx - 60, ky, cx + 60, ky + 92], radius=10, fill=A(CYAN, ka), outline=A(WHITE, ka), width=3)
            txt(d, cx, ky + 46, 'SERM', f(BEB, 52), INK, ka, 'mm')
            if GL: GL.rounded_rectangle([cx - 64, ky - 4, cx + 64, ky + 96], radius=12, outline=A(CYAN, ka), width=12)
        if t >= T['ralox'] - 0.05: tag(d, 80, 1190 + dy, 'RALOXIFENE', CYAN, 34, appear(t, T['ralox'] - 0.05))
        if t >= T['nolva'] - 0.05: tag(d, 80, 1270 + dy, 'NOLVADEX', CYAN, 34, appear(t, T['nolva'] - 0.05))
        if t >= T['block']: tag(d, 80, 1350 + dy, 'ESTROGEN BLOCKED', RED, 30, appear(t, T['block']))
        txt(d, 80, 1150 + dy, 'SELECTIVE ESTROGEN RECEPTOR MODULATOR', f(MONO, 22), MUTED, appear(t, T['selective']))

def sc_privacy(im, d, t):
    t0 = T['clients'] - 0.6; tout = T['privacy'] + 1.3
    a_ = window(t, t0, tout, 0.25, 0.2)
    if a_ <= 0: return
    box = (60, 262, 1020, 470); yo = -18 * (1 - expo((t - t0) / 0.3))
    d.rectangle([box[0] + 8, box[1] + 14 + yo, box[2] + 8, box[3] + 14 + yo], fill=A((0, 0, 0), 0.45 * a_))
    d.rectangle([box[0], box[1] + yo, box[2], box[3] + yo], fill=A(PAPER, a_))
    d.rectangle([box[0], box[1] + yo, box[2], box[1] + 52 + yo], fill=A(COARED, a_))
    txt(d, 86, 274 + yo, 'CLIENT FILE', f(MONOB, 26), WHITE, a_); txt(d, 996, 278 + yo, 'CONFIDENTIAL', f(MONO, 22), (255, 220, 220), a_, 'ra')
    rows = [('NAME', T['clients'] - 0.2, 1.0), ('PHOTOS', T['blast'] - 0.1, 0.8), ('RESULTS', T['blast'] + 0.5, 0.9)]
    for i, (lab, tt, wfrac) in enumerate(rows):
        y = 334 + i * 44 + yo
        txt(d, 86, y, lab, f(MONOB, 24), (60, 58, 56), a_)
        d.line([(230, y + 34), (640, y + 34)], fill=A((180, 176, 168), a_), width=2)
        if t >= tt:
            p = ease_io((t - tt) / 0.35); x0 = 230; x1 = lerp(x0, x0 + 400 * wfrac, p)
            d.rectangle([x0, y, x1, y + 30], fill=A((8, 8, 10), a_))
    if t >= T['forever'] - 0.2: tag(d, 1000, 330, 'POSTED = PERMANENT', RED, 24, appear(t, T['forever'] - 0.2) * a_, align='right')
    if t >= T['privacy'] - 0.1:
        q = back((t - (T['privacy'] - 0.1)) / 0.2)
        st = Image.new('RGBA', (300, 84), (0, 0, 0, 0)); sd = ImageDraw.Draw(st)
        sd.rectangle([3, 3, 296, 80], outline=VGOLD + (240,), width=6); sd.text((150, 44), 'PROTECTED', font=f(BEB, 62), fill=VGOLD + (240,), anchor='mm')
        sc = lerp(1.4, 1.0, q); st = st.resize((int(300 * sc), int(84 * sc)), Image.BICUBIC).rotate(-6, expand=True, resample=Image.BICUBIC)
        st.putalpha(st.split()[3].point(lambda v: int(v * clamp(q * 2) * a_)))
        im.alpha_composite(st, (int(830 - st.width / 2), int(420 - st.height / 2)))

def sc_case(im, d, t):
    t0 = PIPS[1][0]; a0 = appear(t, t0 + 0.15, 0.25)
    d.line([(64, 300), (108, 300)], fill=A(GOLD, a0), width=4); txt(d, 122, 280, 'CLIENT CASE', f(BAR, 38), GOLD, a0)
    if t >= T['e2c'] - 0.1:
        aa = appear(t, T['e2c'] - 0.1); txt(d, 64, 350, 'ESTRADIOL (E2)', f(MONO, 26), MUTED, aa)
        v = 0 if t < T['n120'] - 0.2 else int(round(120 * expo((t - (T['n120'] - 0.2)) / 0.5)))
        fn = f(BEB, 250); txt(d, 56, 380, str(v), fn, RED, aa)
        if GL: GL.text((56, 380), str(v), font=fn, fill=A(RED, 0.45 * aa))
        if v == 120: tag(d, 64 + tw(d, '120', fn) + 18, 560, 'HIGH', RED, 26, appear(t, T['n120'] + 0.35))
    if t >= T['fine'] - 0.2:
        aa = appear(t, T['fine'] - 0.2); check(d, 64, 646, GREEN, 0.9, aa); txt(d, 110, 644, 'FEELING FINE', f(MONOB, 30), GREEN, aa)
    if t >= T['lump'] - 0.1:
        aa = appear(t, T['lump'] - 0.1); tag(d, 60, 702, 'LUMP · 2–3 WEEKS', RED, 26, aa)
    # chart
    ca = appear(t, T['found'] - 0.5, 0.3)
    if ca <= 0: return
    x0, x1, y0, y1 = 120, 1000, 960, 1236
    d.rounded_rectangle([52, 872, 1028, 1300], radius=18, fill=A((8, 11, 19), 0.9 * ca), outline=A((60, 66, 84), ca), width=2)
    xx = 76
    for lab, tt in (('01 FOUND', T['found']), ('02 CORRECTED', T['corrected']), ('03 TREATED', T['treated'])):
        if t >= tt - 0.05: xx = tag(d, xx, 888, lab, VGOLD, 22, appear(t, tt - 0.05)) + 10
    d.line([(x0, y1), (x1, y1)], fill=A((90, 96, 112), ca), width=2)
    # range band
    rb0, rb1 = y1 - 0.34 * (y1 - y0), y1 - 0.14 * (y1 - y0)
    d.rectangle([x0, rb0, x1, rb1], fill=A(GREEN, 0.10 * ca)); txt(d, x1 - 6, rb0 + 4, 'E2 RANGE', f(MONO, 18), GREEN, ca, 'ra')
    prog = clamp((t - T['found']) / (T['weeks2'] - T['found']))
    lump = [1, .78, .48, .2, 0]; e2 = [1.0, .62, .38, .27, .25]
    xs = [lerp(x0 + 70, x1 - 70, i / 4) for i in range(5)]
    for i in range(5):
        txt(d, xs[i], y1 + 8, f'WK {i}', f(MONO, 20), MUTED, ca, 'ma')
        ri = clamp(prog * 4 - i + 1) if i > 0 else ca
        if ri <= 0: continue
        hgt = lump[i] * (y1 - y0 - 40) * expo(ri)
        c = lerpc(RED, AMBER, i / 4)
        if hgt > 1: lit_bar(d, xs[i] - 38, y1 - hgt, xs[i] + 38, y1, c, ca)
    pts = []
    for i in range(5):
        ri = clamp(prog * 4 - i + 1) if i > 0 else 1
        if ri <= 0: break
        y = y1 - e2[i] * (y1 - y0 - 10)
        if i > 0 and ri < 1: px_, py_ = pts[-1]; pts.append((lerp(px_, xs[i], ri), lerp(py_, y, ri)))
        else: pts.append((xs[i], y))
    if len(pts) > 1:
        d.line(pts, fill=A(CYAN, ca), width=5, joint='curve')
        if GL: GL.line(pts, fill=A(CYAN, ca), width=10)
    for p_ in pts: d.ellipse([p_[0] - 8, p_[1] - 8, p_[0] + 8, p_[1] + 8], fill=A(CYAN, ca), outline=A(WHITE, ca), width=2)
    if pts: txt(d, pts[0][0] + 16, pts[0][1] - 34, '120', f(BEB, 40), CYAN, ca)
    if prog >= 0.98: tag(d, xs[3] - 40, y0 - 4, 'E2 IN RANGE', CYAN, 22, appear(t, T['weeks2']))
    if t >= T['gone']:
        q = appear(t, T['gone'], 0.14); tag(d, xs[4] - 60, y1 - 64, 'GONE', GREEN, 30, q)
    txt(d, 76, 1268, '■ LUMP SIZE   ● E2', f(MONO, 18), MUTED, ca); txt(d, 1004, 1268, 'ILLUSTRATIVE TREND · CASE: E2 120, CLEAR BY WK 4', f(MONO, 16), DIM, ca, 'ra')

def sc_ment(im, d, t):
    t0 = T['ment1'] - 0.25; tout = T['dontrun'] + 1.0
    a_ = window(t, t0, tout, 0.22, 0.2)
    if a_ <= 0: return
    box = (60, 262, 1020, 462); frosted_a(im, box, a_, 0.88, 10, 16); d = ImageDraw.Draw(im, 'RGBA')
    # hazard stripes left
    for k in range(0, 200, 28):
        d.polygon([(60, 262 + k), (88, 262 + k), (60, 262 + k + 28)], fill=A(RED, a_))
    d.rectangle([60, 262, 88, 462], outline=A(RED, a_), width=2)
    txt(d, 112, 268, 'MENT', f(BEB, 112), RED, a_); txt(d, 116, 386, 'TRESTOLONE', f(MONO, 24), MUTED, a_)
    txt(d, 116, 420, 'MY ONLY GYNO EPISODE', f(MONOB, 20), VGOLD, a_ * appear(t, T['ment1'] + 0.1))
    mx0, mx1, my = 440, 990, 360
    txt(d, mx0, 300, 'AROMATIZATION', f(MONO, 24), CREAM, a_)
    d.rectangle([mx0, my, mx1, my + 44], outline=A((90, 94, 110), a_), width=2)
    fr = 0.0 if t < T['aromatizes'] else expo((t - T['aromatizes']) / 0.9)
    xf = lerp(mx0 + 3, mx1 - 3, fr);
    if fr > 0:
        for i in range(int(mx0 + 3), int(xf), 4):
            c = lerpc(AMBER, RED, (i - mx0) / (mx1 - mx0)); d.line([(i, my + 3), (i, my + 41)], fill=A(c, a_), width=4)
        if GL: GL.rectangle([mx0 + 3, my + 3, xf, my + 41], fill=A(RED, 0.6 * a_))
    if t >= T['crazy'] - 0.1:
        fl = 1 if int(t * 6) % 2 == 0 else 0.55
        tag(d, mx1, 412, 'OFF THE SCALE', RED, 24, a_ * fl, align='right')
    if t >= T['dontrun']:
        p = expo((t - T['dontrun']) / 0.18); y = 478; x0 = 60; x1 = lerp(x0, 1020, p); al = window(t, T['dontrun'], tout, 0.01, 0.2)
        if GL: GL.rectangle([x0 - 4, y - 8, x1 + 4, y + 100], outline=A(RED, al), width=10)
        lit_bar(d, x0, y, x1, y + 84, RED, al); d.rectangle([x0, y + 80, x1, y + 84], fill=A((140, 0, 0), al))
        if p > 0.6: txt(d, x0 + 30, y + 4, 'NO PLAN = NO MENT', f(BEB, 76), WHITE, al)

def sc_cta(im, d, t):
    t0 = T['protocol9'] - 0.3
    if t < t0: return
    a_ = appear(t, t0, 0.2) * (1 - clamp((t - (T['comment'] - 0.15)) / 0.15))
    frosted_a(im, (60, 262, 1020, 462), a_, 0.88, 10, 16); d = ImageDraw.Draw(im, 'RGBA')
    d.rectangle([60, 262, 67, 462], fill=A(GOLD, a_))
    txt(d, 92, 276, 'COACH AGZ · FREE DOWNLOAD', f(MONO, 22), GOLD, a_)
    for i, (lab, tt) in enumerate((('GYNO REVERSAL PROTOCOL', T['protocol9'] - 0.25), ('BLOODWORK PANEL TO PULL', T['blood9'] - 0.1))):
        if t < tt: continue
        p = expo((t - tt) / 0.22) * a_; y = 318 + i * 66; x = 92 + 60 * (1 - p)
        d.rectangle([x, y, x + 40, y + 50], fill=A(PAPER, p), outline=A(WHITE, p)); d.polygon([(x + 28, y), (x + 40, y + 12), (x + 28, y + 12)], fill=A((160, 156, 150), p))
        for k in range(3): d.line([(x + 7, y + 20 + k * 9), (x + 32, y + 20 + k * 9)], fill=A((120, 116, 110), p), width=2)
        txt(d, x + 58, y + 2, lab, f(BEB, 52), CREAM, p)
    if T['free'] - 0.1 <= t < T['comment'] - 0.05:
        q = back((t - (T['free'] - 0.1)) / 0.22); x = 860; y = 340
        lit_bar(d, x, y + 20 * (1 - q), x + 140, y + 74 + 20 * (1 - q), VGOLD, clamp(q * 1.5))
        txt(d, x + 70, y + 37 + 20 * (1 - q), 'FREE', f(BEB, 62), INK, clamp(q * 1.5), 'mm')
        if GL: GL.rectangle([x - 4, y - 4, x + 144, y + 78], outline=A(VGOLD, clamp(q)), width=10)
    if t >= T['comment'] - 0.15:
        q = back((t - (T['comment'] - 0.15)) / 0.28); y = 286 - 50 * (1 - q); x0, x1 = 70, 1010
        al = clamp(q * 1.6)
        if GL: GL.rounded_rectangle([x0 - 6, y - 6, x1 + 6, y + 156], radius=26, outline=A(VGOLD, al), width=14)
        d.rounded_rectangle([x0, y, x1, y + 150], radius=24, fill=A(VGOLD, al))
        lit_bar(d, x0 + 20, y + 4, x1 - 20, y + 12, (255, 236, 160), al * 0.6)
        txt(d, x0 + 46, y + 48, 'COMMENT', f(MONOB, 46), INK, al)
        txt(d, x1 - 46, y + 10, '"GYNO"', f(BEB, 138), INK, al, 'ra')
    if t >= SPEECH_END:
        q = appear(t, SPEECH_END, 0.25)
        lg = LOGO.copy(); m = LOGO_M.point(lambda v: int(v * q))
        im.paste(lg, (90, 1290), m); d = ImageDraw.Draw(im, 'RGBA')
        txt(d, 240, 1300, 'COACH AGZ', f(BEB, 64), GOLD, q); txt(d, 242, 1368, '@coach.agz', f(MONO, 30), CREAM, q)
        txt(d, 90, 1446, 'FOR RESEARCH & EDUCATIONAL PURPOSES ONLY', f(MONO, 20), DIM, q)

# ---------------- hook + band ----------------
def hook(im, t):
    if t >= HOOK_END + 0.15: return
    a_ = 1 - clamp((t - HOOK_END) / 0.15)
    s = lerp(1.0, 1.04, clamp(t / HOOK_END))
    L1 = [('Reverse ', WHITE), ('GYNO', VGOLD), (' in 3 steps', WHITE)]; L2 = [('before it turns surgical', WHITE)]
    size = 74; fn = f(DMB, size)
    lay = Image.new('RGBA', (W, 300), (0, 0, 0, 0)); ld = ImageDraw.Draw(lay)
    sh = Image.new('RGBA', (W, 300), (0, 0, 0, 0)); sd = ImageDraw.Draw(sh)
    for li, line in enumerate((L1, L2)):
        total = sum(tw(ld, s_, fn) for s_, _ in line); x = (W - 80 - total) / 2 + 30; y = 40 + li * 100
        for s_, c in line:
            sd.text((x + 3, y + 5), s_, font=fn, fill=(0, 0, 0, 230)); ld.text((x, y), s_, font=fn, fill=c + (255,), stroke_width=3, stroke_fill=(0, 0, 0, 255))
            x += tw(ld, s_, fn)
    sh = sh.filter(ImageFilter.GaussianBlur(9)); sh.alpha_composite(lay); lay = sh
    if s != 1: lay = lay.resize((int(W * s), int(300 * s)), Image.BICUBIC)
    if a_ < 1: lay.putalpha(lay.split()[3].point(lambda v: int(v * a_)))
    im.alpha_composite(lay, (int((W - lay.width) / 2), int(250 - (lay.height - 300) / 2)))

def band(im, t, s, p):
    if t < HOOK_END or t >= MID + 0.15: return
    a_ = appear(t, HOOK_END, 0.15) * (1 - clamp((t - MID) / 0.15)) * (1 - max(s, p))
    if a_ <= 0.01: return
    d = ImageDraw.Draw(im, 'RGBA'); y0 = 214
    d.rectangle([8, y0, W, y0 + 104], fill=NAVY + (int(228 * a_),))
    d.line([(52, y0 + 22), (88, y0 + 22)], fill=A(GOLD, a_), width=4); txt(d, 98, y0 + 8, '@coach.agz', f(MONO, 22), GOLD, a_)
    fn = f(DMB, 44); x = 52; y = y0 + 40
    for s_, c in (('Reverse ', CREAM), ('GYNO', VGOLD), (' in 3 steps', CREAM)):
        txt(d, x, y, s_, fn, c, a_); x += tw(d, s_, fn)
    if t >= T['three'] - 0.1:
        global GL
        pills(d, 1040 - 3 * 152, y0 + 52, t, a_, 18, show_t=T['three'] - 0.1)

# ---------------- captions ----------------
GOLDW = {'GYNO', 'RANGE', 'DRIVER', 'SERMS', 'RALOXIFENE', 'NOLVADEX', 'PROTOCOL', 'FREE', 'ONE', 'TWO', 'THREE', 'REVERSE', 'ESTRADIOL', 'PROLACTIN', 'E2'}
REDW = {'SURGICAL', 'FIBROTIC', 'HARD', 'CRASH', 'NUKE', 'ZERO', 'MENT', 'MENT.', 'FOREVER', 'LUMP', '120', 'CRAZY'}
def build_groups():
    G = []; cur = []
    for i, x in enumerate(WORDS):
        if cur:
            prev = WORDS[cur[-1]]
            if len(cur) >= 3 or x['s'] - prev['e'] > 0.28 or prev['w'][-1] in '.,?!' or any(prev['e'] - 0.02 <= c <= x['s'] + 0.02 for c in CUTS):
                G.append(cur); cur = []
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
def captions(im, t, cy):
    if t >= SPEECH_END - 0.02: return
    g = group_at(t)
    if not g: return
    d = ImageDraw.Draw(im, 'RGBA')
    raw = [WORDS[i]['w'] for i in g]
    ws = [w_.upper().rstrip(',.?!') for w_ in raw]
    size = 124
    while True:
        fn = f(BEB, size); sp = tw(d, ' ', fn) + 14; wd = [tw(d, w_, fn) for w_ in ws]; tot = sum(wd) + sp * (len(ws) - 1)
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
    cap.alpha_composite(shd.filter(ImageFilter.GaussianBlur(7)))
    lit_bar(cd, bx0, 40 + size * 0.02, bx1, 40 + size * 0.98, RED)
    for k, (w_, x_) in enumerate(zip(ws, xs)):
        spoken = WORDS[g[k]]['s'] <= t
        col = CREAM
        if spoken and k != act:
            if w_ in GOLDW: col = VGOLD
            elif w_ in REDW: col = (255, 92, 80)
        cd.text((x_, 40), w_, font=fn, fill=col, stroke_width=0 if k == act else 3, stroke_fill=(0, 0, 0))
    if abs(s - 1) > 0.002:
        cap = cap.resize((int(W * s), int(260 * s)), Image.BICUBIC); ox = int((W - cap.width) / 2); oy = int(cy - 40 - (cap.height - 260) / 2)
    else: ox, oy = 0, int(cy - 40)
    im.alpha_composite(cap, (ox, oy))

# ---------------- frame ----------------
def frame(src, t):
    global GL
    s, p = layout(t)
    z = zoom_at(t) if (s < 0.001 and p < 0.001) else lerp(zoom_at(t), 1.0, max(s, p))
    if abs(z - 1) > 0.001:
        big = src.resize((int(W * z), int(H * z)), Image.BICUBIC); ox = (big.width - W) // 2; oy = int((big.height - H) * 0.38); src = big.crop((ox, oy, ox + W, oy + H))
    glow = Image.new('RGBA', (W, H), (0, 0, 0, 0)); GL = ImageDraw.Draw(glow, 'RGBA')
    if p > 0.001:
        im = BG.copy()
        cr = [lerp(a_, b_, p) for a_, b_ in zip((0, 0, W, H), PIP_CROP)]; ds = [lerp(a_, b_, p) for a_, b_ in zip((0, 0, W, H), PIP_DST)]
        dw, dh = int(ds[2] - ds[0]), int(ds[3] - ds[1])
        card = src.crop(tuple(int(v) for v in cr)).resize((dw, dh), Image.BICUBIC).convert('RGBA')
        rad = int(28 * p); m = Image.new('L', (dw, dh), 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, dw - 1, dh - 1], radius=rad, fill=255)
        if p > 0.05:
            sh = Image.new('RGBA', (dw + 80, dh + 80), (0, 0, 0, 0)); ImageDraw.Draw(sh).rounded_rectangle([40, 50, dw + 40, dh + 50], radius=rad, fill=(0, 0, 0, int(170 * p)))
            im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(18)), (int(ds[0]) - 40, int(ds[1]) - 40))
        im.paste(card, (int(ds[0]), int(ds[1])), m)
        d = ImageDraw.Draw(im, 'RGBA')
        d.rounded_rectangle([ds[0], ds[1], ds[2], ds[3]], radius=rad, outline=A(VGOLD, p), width=4)
        GL.rounded_rectangle([ds[0], ds[1], ds[2], ds[3]], radius=rad, outline=A(VGOLD, 0.6 * p), width=8)
        if p > 0.5:
            d.ellipse([ds[0] + 22, ds[3] - 44, ds[0] + 38, ds[3] - 28], fill=A(RED, 1 if int(t * 2) % 2 == 0 else 0.3))
            txt(d, ds[0] + 48, ds[3] - 50, 'LIVE', f(MONOB, 22), WHITE, p)
        lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); ld = ImageDraw.Draw(lay, 'RGBA')
        if PIPS[0][0] - 0.1 <= t < PIPS[0][1] + 0.4: sc_step1(lay, ld, t)
        else: sc_case(lay, ld, t)
        if p < 1: lay.putalpha(lay.split()[3].point(lambda v: int(v * ease_io((p - 0.3) / 0.7))))
        im.alpha_composite(lay)
    else:
        im = src.convert('RGBA')
        if s > 0.001:
            sh_ = int(SHIFT * s); py = int(lerp(H, PANEL_Y, s))
            moved = Image.new('RGBA', (W, H), (0, 0, 0, 255)); moved.paste(im.crop((0, sh_, W, H)), (0, 0)); im = moved
            im.paste(PANEL_TEX.crop((0, 0, W, H - py)), (0, py))
            d = ImageDraw.Draw(im, 'RGBA')
            for k in range(40): d.line([(0, py - 40 + k), (W, py - 40 + k)], fill=(8, 11, 19, int(200 * (k / 40) ** 2)))
            d.line([(0, py), (W, py)], fill=A(GOLD, 1), width=3); GL.line([(0, py), (W, py)], fill=A(VGOLD, 0.7), width=6)
            lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); ld = ImageDraw.Draw(lay, 'RGBA'); dy = py - PANEL_Y
            if t < 40: sc_window(lay, ld, t, dy)
            else: sc_step3(lay, ld, t, dy)
            if s < 1: lay.putalpha(lay.split()[3].point(lambda v: int(v * ease_io((s - 0.4) / 0.6))))
            im.alpha_composite(lay)
        # top/bottom legibility scrims (very light, no grade on face)
        yy = np.arange(H); a2 = np.where(yy > 1240, np.clip((yy - 1240) / 260, 0, 1) * 100, 0); a2 = np.maximum(a2, np.where(yy < 470, (1 - yy / 470) * 110, 0))
        a2 = (a2 * (1 - s)).astype(np.uint8)
        im.alpha_composite(Image.merge('RGBA', [Image.new('L', (W, H), c) for c in NAVY] + [Image.fromarray(np.repeat(a2[:, None], W, 1))]))
        d = ImageDraw.Draw(im, 'RGBA')
        if T['soft'] - 0.3 <= t < T['three'] + 0.2: sc_lenses(im, None, d, t)
        if T['step2'] - 0.2 <= t < T['tool'] + 2.0: sc_step2(im, d, t)
        if T['clients'] - 0.8 <= t < T['privacy'] + 1.6: sc_privacy(im, d, t)
        if T['ment1'] - 0.4 <= t < T['dontrun'] + 1.3: sc_ment(im, d, t)
        sc_cta(im, ImageDraw.Draw(im, 'RGBA'), t)
    band(im, t, s, p)
    hook(im, t)
    GL = None
    if glow.getbbox():
        sm = glow.resize((W // 4, H // 4), Image.BILINEAR)
        g1 = np.asarray(sm.filter(ImageFilter.GaussianBlur(3.5))).astype(np.float32) / 255; g2 = np.asarray(sm.filter(ImageFilter.GaussianBlur(10))).astype(np.float32) / 255
        prem = np.clip(g1[..., :3] * g1[..., 3:] * 2.0 + g2[..., :3] * g2[..., 3:] * 1.6, 0, 1)
        prem = np.asarray(Image.fromarray((prem * 255).astype(np.uint8)).resize((W, H), Image.BILINEAR)).astype(np.float32) / 255
        b = np.asarray(im.convert('RGB')).astype(np.float32) / 255
        im = Image.fromarray(((1 - (1 - b) * (1 - prem)) * 255).astype(np.uint8)).convert('RGBA')
    cy = lerp(1335, 940, s)
    captions(im, t, cy)
    d = ImageDraw.Draw(im, 'RGBA'); d.rectangle([0, 0, 7, H], fill=GOLD)
    if HOOK_END <= t < SPEECH_END and s < 0.01 and p < 0.01: txt(d, 64, 1492, '@coach.agz', f(MONO, 22), GOLD, 0.7)
    out = im.convert('RGB')
    for th in (T['surgical'], T['nuke'] + 0.25, T['dontrun'], T['comment'] - 0.15 + 0.2):
        k = round((t - th) * FPS)
        if k in (0, 1):
            dx = [8, -4][k]; zz = 1.02; big = out.resize((int(W * zz), int(H * zz)), Image.BICUBIC); ox = (big.width - W) // 2 - dx; oy = (big.height - H) // 2
            out = big.crop((ox, oy, ox + W, oy + H)); ImageDraw.Draw(out).rectangle([0, 0, 7, H], fill=GOLD)
    return out

def src_frames(n0, n1):
    """yield source frames for output frames n0..n1-1 (freeze on last after speech end)"""
    m1 = min(n1, NSRC)
    if n0 < NSRC:
        dec = subprocess.Popen(['ffmpeg', '-v', 'error', '-ss', f'{n0 / FPS:.4f}', '-i', B + 'assembled.mp4', '-frames:v', str(m1 - n0), '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], stdout=subprocess.PIPE)
        last = None
        for n in range(n0, m1):
            buf = dec.stdout.read(W * H * 3)
            if len(buf) < W * H * 3: buf = last
            last = buf; yield n, Image.frombuffer('RGB', (W, H), buf)
        dec.kill()
    if n1 > NSRC:
        dec = subprocess.run(['ffmpeg', '-v', 'error', '-sseof', '-0.1', '-i', B + 'assembled.mp4', '-frames:v', '1', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], capture_output=True)
        fr = Image.frombuffer('RGB', (W, H), dec.stdout[:W * H * 3])
        for n in range(max(n0, NSRC), n1): yield n, fr

if __name__ == '__main__':
    mode = sys.argv[2]
    if mode == 'anchors': print(json.dumps({k: round(v, 2) for k, v in T.items()})); print('dur', DUR, 'mid', MID, SPLITS, PIPS); sys.exit()
    if mode == 'stills':
        import os; os.makedirs(B + 'qc', exist_ok=True)
        for tt in [float(x) for x in sys.argv[3:]]:
            n = min(int(round(tt * FPS)), NSRC - 1)
            r = subprocess.run(['ffmpeg', '-v', 'error', '-ss', f'{n / FPS:.4f}', '-i', B + 'assembled.mp4', '-frames:v', '1', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], capture_output=True)
            frame(Image.frombuffer('RGB', (W, H), r.stdout[:W * H * 3]), tt).resize((540, 960), Image.LANCZOS).save(B + f'qc/st_{tt:06.2f}.jpg', quality=88)
        sys.exit()
    n0, n1, out = int(sys.argv[3]), int(sys.argv[4]), sys.argv[5]
    enc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-crf', '12', '-preset', 'veryfast', '-pix_fmt', 'yuv420p', out], stdin=subprocess.PIPE)
    for n, fr in src_frames(n0, n1):
        enc.stdin.write(frame(fr, n / FPS).tobytes())
    enc.stdin.close(); enc.wait(); print('done', n0, n1)
