# Full test 04 — "Tren vs sleep". 1080x1920 30 fps.
# usage: python3 render.py <scratch> stills t1 t2 ...   |   python3 render.py <scratch> chunk n0 n1 out.mp4
import json, subprocess, sys, math, re
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
S = sys.argv[1].rstrip('/') + '/'
F = S + 'fonts/'; X = S + 'ex/'
W, H = 1080, 1920; FPS = 30
TR = json.load(open(X + 'trim.json')); KEEP = TR['keep']; DUR = TR['dur']; END = DUR + 1.0   # 1 s end-card hold
CUTS = []; acc = 0
for a, b in KEEP[:-1]:
    acc += b - a; CUTS.append(round(acc, 4))
WORDS = json.load(open(X + 'words_final.json'))

GOLD = (201, 169, 110); CREAM = (244, 241, 234); NAVY = (14, 17, 23)
RED = (255, 34, 28); VGOLD = (255, 194, 26); CYAN = (0, 229, 255); GREEN = (30, 255, 110)
DEEP = (2, 3, 8); INK = (6, 8, 14); WHITE = (255, 255, 255); GREY = (70, 74, 90); MUTED = (150, 154, 168)
MONO = 'JBMono-500.ttf'; MONOB = 'JBMono-700.ttf'; BEB = 'BebasNeue.ttf'; DMB = 'DMSans-700.ttf'; DMR = 'DMSans-400.ttf'; BAR = 'Barlow-800.ttf'
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
def appear(t, t0, dur=0.16): return expo((t - t0) / dur)

# ---------------- word cues (cut timeline) ----------------
def norm(w): return re.sub(r"[^a-z0-9%']", '', w.lower())
NW = [norm(w['w']) for w in WORDS]
def _find(seq, after):
    sq = [norm(s) for s in seq.split()]
    for i in range(len(NW) - len(sq) + 1):
        if WORDS[i]['s'] >= after - 1e-6 and NW[i:i + len(sq)] == sq: return i, i + len(sq) - 1
    raise KeyError(f'cue not found: {seq!r} after {after}')
def cue(seq, after=0.0): return WORDS[_find(seq, after)[0]]['s']
def cend(seq, after=0.0): return WORDS[_find(seq, after)[1]]['e']

GL = None   # glow layer draw (bloom)
# ---------------- primitives ----------------
def txt(d, x, y, s, font, col, a=1.0, anchor=None): d.text((x, y), s, font=font, fill=A(col, a), anchor=anchor)
def brackets(d, x0, y0, x1, y1, col, L=34, w=4):
    for (cx, cy, sx, sy) in [(x0, y0, 1, 1), (x1, y0, -1, 1), (x0, y1, 1, -1), (x1, y1, -1, -1)]:
        d.line([(cx, cy), (cx + sx * L, cy)], fill=col, width=w); d.line([(cx, cy), (cx, cy + sy * L)], fill=col, width=w)
def lit_bar(d, x0, y0, x1, y1, col, a=1.0):
    h = max(1, int(y1 - y0))
    for i in range(h):
        k = i / h; c = tuple(int(min(255, v * (1.18 - 0.36 * k) + (40 if k < 0.12 else 0))) for v in col)
        d.line([(x0, y0 + i), (x1, y0 + i)], fill=c + (int(255 * clamp(a)),))
def lit_col(d, x0, y0, x1, y1, col, a=1.0):   # vertical bar, lit left edge
    if y1 - y0 < 1: return
    wd = max(1, int(x1 - x0))
    for i in range(wd):
        k = i / wd; c = tuple(int(min(255, v * (1.15 - 0.4 * k) + (45 if k < 0.1 else 0))) for v in col)
        d.line([(x0 + i, y0), (x0 + i, y1)], fill=c + (int(255 * clamp(a)),))
def tag(d, x, y, label, col=RED, size=30, a=1.0, glow=True):
    if a <= 0: return x
    fn = f(MONO, size); tw = d.textlength(label, font=fn); h = size + 16
    lit_bar(d, x, y, x + tw + 24, y + h, col, a); d.text((x + 12, y + 5), label, font=fn, fill=A(INK if col in (VGOLD, GREEN, CYAN, WHITE) else WHITE, a))
    if GL and glow: GL.rectangle([x - 4, y - 4, x + tw + 28, y + h + 4], outline=A(col, a), width=8)
    return x + tw + 24
def tag_w(d, label, size=30): return d.textlength(label, font=f(MONO, size)) + 24
def check(d, x, y, col, s=1.0, a=1.0):
    pts = [(x, y + 16 * s), (x + 10 * s, y + 28 * s), (x + 30 * s, y + 2 * s)]
    d.line(pts, fill=A(col, a), width=int(6 * s))
    if GL: GL.line(pts, fill=A(col, a), width=int(12 * s))
def cross(d, x, y, col, s=1.0, a=1.0):
    for p in ([(x, y), (x + 28 * s, y + 28 * s)], [(x + 28 * s, y), (x, y + 28 * s)]):
        d.line(p, fill=A(col, a), width=int(6 * s))
        if GL: GL.line(p, fill=A(col, a), width=int(12 * s))
def dashed(d, x0, y0, x1, y1, col, w=3, dash=14, gap=10, a=1.0, glow=False):
    L = math.hypot(x1 - x0, y1 - y0)
    if L < 1: return
    n = int(L // (dash + gap)) + 1
    for k in range(n):
        s0 = k * (dash + gap) / L; s1 = min(1, (k * (dash + gap) + dash) / L)
        if s0 >= 1: break
        p = [(lerp(x0, x1, s0), lerp(y0, y1, s0)), (lerp(x0, x1, s1), lerp(y0, y1, s1))]
        d.line(p, fill=A(col, a), width=w)
        if glow and GL: GL.line(p, fill=A(col, a), width=w * 3)
def arrow(d, x0, y0, x1, y1, col, w=5, a=1.0):
    d.line([(x0, y0), (x1, y1)], fill=A(col, a), width=w)
    ang = math.atan2(y1 - y0, x1 - x0); L = 18
    d.polygon([(x1, y1), (x1 - L * math.cos(ang - 0.45), y1 - L * math.sin(ang - 0.45)), (x1 - L * math.cos(ang + 0.45), y1 - L * math.sin(ang + 0.45))], fill=A(col, a))
def polyline(d, pts, col, w, a=1.0, glow=True):
    if len(pts) < 2: return
    d.line(pts, fill=A(col, a), width=w, joint='curve')
    if GL and glow: GL.line(pts, fill=A(col, a), width=w * 2 + 4)
def partial(pts, p):   # first fraction p of a polyline (by index)
    if p <= 0: return pts[:1]
    n = (len(pts) - 1) * clamp(p); i = int(n)
    out = pts[:i + 1]
    if i < len(pts) - 1:
        q = n - i; a, b = pts[i], pts[i + 1]; out = out + [(lerp(a[0], b[0], q), lerp(a[1], b[1], q))]
    return out
def frosted(im, box, dark=0.86, blur=10):
    x0, y0, x1, y1 = [int(v) for v in box]
    x0 = max(0, x0); y0 = max(0, y0); x1 = min(W, x1); y1 = min(H, y1)
    if x1 <= x0 or y1 <= y0: return
    reg = im.crop((x0, y0, x1, y1)).convert('RGB').filter(ImageFilter.GaussianBlur(blur))
    im.paste(Image.blend(reg, Image.new('RGB', reg.size, DEEP), dark).convert('RGBA'), (x0, y0))
def rot_text(s, font, col, a=1.0, angle=90):
    tw = int(font.getlength(s)) + 8; th = int(font.size * 1.3)
    im = Image.new('RGBA', (tw, th), (0, 0, 0, 0)); ImageDraw.Draw(im).text((4, 0), s, font=font, fill=A(col, a))
    return im.rotate(angle, expand=True)
def bigstat(d, x, y, s, size, col, a=1.0):
    fn = f(BEB, size); d.text((x, y), s, font=fn, fill=A(col, a))
    if GL: GL.text((x, y), s, font=fn, fill=A(col, a * 0.7))
    return d.textlength(s, font=fn)
LOGO = None
def logo(sz):
    global LOGO
    if LOGO is None or LOGO.width != sz:
        lg = Image.open(X + 'logo.jpg').convert('RGB'); s = min(lg.size)
        lg = lg.crop(((lg.width - s) // 2, (lg.height - s) // 2, (lg.width + s) // 2, (lg.height + s) // 2)).resize((sz, sz), Image.LANCZOS)
        m = Image.new('L', (sz, sz), 0); ImageDraw.Draw(m).ellipse([0, 0, sz - 1, sz - 1], fill=255); lg.putalpha(m); LOGO = lg
    return LOGO

# ======================= SCENES =======================
P = (64, 502, 1016, 1262)   # full panel box (top below the frame-0 hook)
def hhmm(h): h = h % 24; return f'{int(h):02d}:{int(round((h % 1) * 60)) % 60:02d}'

# ---- S1: 24-hour sleep clock + CNS drive meter ----
def scene_clock(d, t, im):
    tS = cue('sleeping'); t2 = cue('two to three'); tH = cue('hours a night'); tC = cue('central'); tW = cue('wasting')
    cx, cy, r = 390, 900, 222
    def P_(h, rr): a = (h / 24) * 2 * math.pi - math.pi / 2; return (cx + rr * math.cos(a), cy + rr * math.sin(a))
    def arc(h0, h1, rr, col, w, a=1.0, glow=True):
        d.arc([cx - rr, cy - rr, cx + rr, cy + rr], h0 / 24 * 360 - 90, h1 / 24 * 360 - 90, fill=A(col, a), width=w)
        if glow and GL: GL.arc([cx - rr, cy - rr, cx + rr, cy + rr], h0 / 24 * 360 - 90, h1 / 24 * 360 - 90, fill=A(col, a * 0.8), width=w + 10)
    txt(d, 100, 558, '24H CLOCK', f(MONO, 24), MUTED, 1)
    d.ellipse([cx - r - 30, cy - r - 30, cx + r + 30, cy + r + 30], outline=A((40, 44, 58), 1), width=2)
    arc(0, 24, r, (30, 34, 46), 38, 1, False)
    for h in range(24):
        p0 = P_(h, r + 26); p1 = P_(h, r + (40 if h % 6 == 0 else 33)); d.line([p0, p1], fill=A(MUTED if h % 6 else WHITE, 1), width=3 if h % 6 == 0 else 2)
    for h, lab in ((0, '00'), (6, '06'), (12, '12'), (18, '18')):
        x, y = P_(h, r + 66); txt(d, x, y, lab, f(MONO, 24), MUTED, 1, 'mm')
    # target 8h: 22:00 -> 06:00 (ghost, dashed feel via low alpha)
    pa = expo((t - tS) / 0.6)
    if pa > 0:
        arc(22, 22 + 8 * pa, r, VGOLD, 38, 0.5, False)
        la = appear(t, tS + 0.3)
        d.rectangle([370, 562, 392, 584], fill=A(VGOLD, 0.6 * la)); txt(d, 402, 558, 'TARGET 8H', f(MONO, 24), CREAM, la)
    # actual: 2.5h, 03:00 -> 05:30
    pr = expo((t - t2) / 0.5) if t >= t2 else 0
    if pr > 0:
        arc(27, 27 + 2.5 * pr, r, RED, 38)
        d.rectangle([560, 562, 582, 584], fill=A(RED, pr)); txt(d, 592, 558, 'ON TREN', f(MONO, 24), RED, pr)
    # center readout
    if t >= t2:
        a = appear(t, t2, 0.15); bigstat(d, cx - d.textlength('2–3', font=f(BEB, 150)) / 2, cy - 100, '2–3', 150, RED, a)
        txt(d, cx, cy + 66, 'HRS ASLEEP', f(MONO, 26), CREAM, a, 'mm')
    else:
        txt(d, cx, cy, 'SLEEP', f(BEB, 80), (90, 94, 108), 1, 'mm')
    # CNS meter
    mx0, my0, mx1, my1 = 800, 640, 900, 1110
    txt(d, (mx0 + mx1) / 2, 590, 'CNS', f(BEB, 52), CREAM, 1, 'mt')
    d.rectangle([mx0, my0, mx1, my1], outline=A(GREY, 1), width=3)
    for k in range(1, 10): d.line([(mx0, my1 - k * (my1 - my0) / 10), (mx0 + 14, my1 - k * (my1 - my0) / 10)], fill=A(GREY, 1), width=2)
    lvl = 0.35 if t < tC else lerp(0.35, 0.96, expo((t - tC) / 0.7))
    lvl += 0.015 * math.sin(t * 31) if t >= tC else 0
    yl = my1 - 4 - lvl * (my1 - my0 - 8)
    col = CYAN if lvl < 0.6 else RED
    lit_col(d, mx0 + 4, yl, mx1 - 4, my1 - 4, col)
    if GL: GL.rectangle([mx0 + 4, yl, mx1 - 4, my1 - 4], outline=A(col, 0.9), width=8)
    if t >= tC: tag(d, 760, 1130, 'OVERDRIVE', RED, 26, appear(t, tC + 0.4))
    if t >= tW:
        p = expo((t - tW) / 0.12); s = lerp(1.5, 1.0, p)
        st = Image.new('RGBA', (560, 140), (0, 0, 0, 0)); sd = ImageDraw.Draw(st)
        sd.rounded_rectangle([6, 6, 554, 134], radius=10, outline=(255, 34, 28, 240), width=8)
        sd.text((280, 72), 'CYCLE WASTED', font=f(BEB, 104), fill=(255, 34, 28, 240), anchor='mm')
        st = st.rotate(-6, expand=True, resample=Image.BICUBIC); st = st.resize((int(st.width * s), int(st.height * s)), Image.BICUBIC)
        st.putalpha(st.split()[3].point(lambda v: int(v * p)))
        im.alpha_composite(st, (int(cx - st.width / 2 + 40), int(cy + 150 - st.height / 2)))

# ---- S2: KPI tiles (top strip) ----
def strip_kpi(d, t, im, box, al):
    x0, y0, x1, y1 = box
    txt(d, x0 + 56, y0 + 18, 'WHAT TREN DOES', f(MONO, 28), WHITE, al)
    tiles = [('PROTEIN SYNTHESIS', cue('protein')), ('NUTRIENT PARTITIONING', cue('partitioning'))]
    for i, (lab, tt) in enumerate(tiles):
        tx0 = x0 + 30 + i * 460; tx1 = tx0 + 430; ty0 = y0 + 70; ty1 = y1 - 26
        a = al * appear(t, tt - 0.1, 0.2)
        d.rounded_rectangle([tx0, ty0, tx1, ty1], radius=14, fill=A((12, 16, 26), 0.95 * a), outline=A(VGOLD if t >= tt else GREY, a), width=3)
        txt(d, tx0 + 22, ty0 + 16, lab, f(MONO, 24), CREAM, a)
        p = expo((t - tt) / 0.7) if t >= tt else 0
        pts = [(lerp(tx0 + 24, tx1 - 120, k / 20), ty1 - 30 - (k / 20) ** 1.8 * (ty1 - ty0 - 110) * p) for k in range(21)]
        polyline(d, pts, VGOLD, 5, a)
        if p > 0:
            ax = tx1 - 66; ay = ty0 + 70
            d.polygon([(ax, ay), (ax - 40, ay + 56), (ax + 40, ay + 56)], fill=A(GREEN, a * p))
            if GL: GL.polygon([(ax, ay - 6), (ax - 46, ay + 60), (ax + 46, ay + 60)], fill=A(GREEN, a * p))
            txt(d, ax, ay + 66, 'UP', f(BEB, 52), GREEN, a * p, 'mt')

# ---- S3: overnight hormone chart, then the 3-hour cut ----
def scene_night(d, t, im):
    tGH = cue('growth hormone'); tT = cue('testosterone'); tR = cue('recovery'); tI = cue('insulin'); tWS = cue('while you sleep')
    t3 = cue('only getting three') + 0.2; tN = cue('negative'); tNo = cue('none')
    x0, y0, x1, y1 = 120, 690, 960, 1090
    X_ = lambda h: x0 + h / 8 * (x1 - x0)
    # chips
    chips = [('GH', tGH, CYAN), ('TESTOSTERONE', tT, VGOLD), ('RECOVERY', tR, GREEN), ('INSULIN SENS.', tI, (190, 120, 255))]
    cx = 100
    for lab, tt, col in chips:
        a = 1 if t >= tt else 0.25
        cx = tag(d, cx, 560, lab, col if t >= tt else GREY, 24, a, glow=t >= tt) + 12
    # asleep band + moon
    if t >= tWS:
        a = appear(t, tWS, 0.25); d.rectangle([X_(0), 636, X_(8), 658], fill=A((60, 70, 120), 0.8 * a))
        txt(d, X_(4), 647, 'ASLEEP · 8 HRS', f(MONO, 20), WHITE, a, 'mm')
        mx, my = X_(0) - 2, 641
    # axes
    d.line([(x0, y1), (x1, y1)], fill=A(GREY, 1), width=3)
    for h in range(9):
        x = X_(h); d.line([(x, y1), (x, y1 + 10)], fill=A(GREY, 1), width=2); txt(d, x, y1 + 18, hhmm(22 + h), f(MONO, 20), MUTED, 1, 'mt')
    def gh(h): return 0.95 * math.exp(-((h - 1.2) ** 2) / 0.18) + 0.35 * math.exp(-((h - 3.6) ** 2) / 0.2) + 0.22 * math.exp(-((h - 5.8) ** 2) / 0.2) + 0.05
    def te(h): return 0.12 + 0.7 * (h / 8) ** 1.6
    def rec(h): return 0.1 + 0.45 * (1 - math.exp(-h / 3))
    def ins(h): return 0.08 + 0.3 * (h / 8)
    curves = [(gh, CYAN, tGH), (te, VGOLD, tT), (rec, GREEN, tR), (ins, (190, 120, 255), tI)]
    cut = expo((t - t3) / 0.5) if t >= t3 else 0
    for fn_, col, tt in curves:
        if t < tt: continue
        p = expo((t - tt) / 0.7)
        pts = [(X_(h / 10), y1 - fn_(h / 10) * (y1 - y0)) for h in range(0, 81)]
        shown = partial(pts, p)
        if cut > 0:
            keep = [q for q in shown if q[0] <= X_(3)]; lost = [q for q in shown if q[0] >= X_(3) - 1]
            polyline(d, keep, col, 5); polyline(d, lost, (70, 74, 90), 4, 1, glow=False)
        else:
            polyline(d, shown, col, 5)
    if cut > 0:
        xc = X_(3); d.rectangle([xc, y0 - 20, X_(8), y1], fill=A((40, 0, 0), 0.45 * cut))
        for k in range(0, 30):   # hatch
            hx = xc + k * 30; d.line([(hx, y1), (min(X_(8), hx + 120), y1 - 120)], fill=A(RED, 0.12 * cut), width=2)
        d.line([(xc, y0 - 40), (xc, y1)], fill=A(RED, cut), width=5)
        if GL: GL.line([(xc, y0 - 40), (xc, y1)], fill=A(RED, cut), width=12)
        tag(d, xc - tag_w(d, '3 HRS', 28) - 8, y0 + 4, '3 HRS', RED, 28, cut)
        tag(d, xc + 16, y0 + 4, 'AWAKE · 5 HRS LOST', WHITE, 24, appear(t, t3 + 0.5))
    if t >= tN:
        a = appear(t, tN); tag(d, X_(3) + 30, y0 + 120, 'SIDE EFFECTS: ALL', RED, 26, a)

# ---- S4: two-column comparison ----
def scene_compare(d, t, im):
    tV = cue('versus')
    L = [('HIGH HEMATOCRIT', cue('hematocrit')), ('HIGH BLOOD PRESSURE', cue('blood pressure')), ('ANXIETY', cue('anxiety')),
         ('NO RECOVERY', cue('no recovery')), ('IRRITABILITY', cue('irritability'))]
    R_ = [('TRT', cue('trt')), ('FOOD', cue('food')), ('TRAINING', cue('training')), ('RECOVERY', cue('recovery', cue('training')))]
    cols = [(90, 'TREN', 'NO SLEEP', RED, L, cue('trend') - 0.05, cross), (560, 'TRT', '8 HRS SLEEP', GREEN, R_, tV, check)]
    for x, h1, h2, col, rows, th, mark in cols:
        a = 1 if t >= th else 0.3
        p = expo((t - th) / 0.35) if t >= th else 0
        d.rounded_rectangle([x, 570, x + 430, 1180], radius=14, fill=A((12, 14, 22), 0.9), outline=A(col if t >= th else GREY, 0.9 * a), width=3)
        lit_bar(d, x, 570, x + 430 * p, 580, col) if p > 0 else None
        if GL and p > 0: GL.line([(x, 572), (x + 430 * p, 572)], fill=A(col, 1), width=10)
        txt(d, x + 28, 600, h1, f(BEB, 96), WHITE if t >= th else MUTED, 1)
        tw = d.textlength(h1, font=f(BEB, 96)); txt(d, x + 40 + tw, 636, h2, f(MONO, 24), col if t >= th else MUTED, 1)
        if t >= th and x > 100:
            # moon for the sleep column
            mx, my = x + 370, 630; d.ellipse([mx - 26, my - 26, mx + 26, my + 26], fill=A(VGOLD, 1)); d.ellipse([mx - 12, my - 34, mx + 34, my + 14], fill=A((12, 14, 22), 1))
            if GL: GL.ellipse([mx - 30, my - 30, mx + 30, my + 30], fill=A(VGOLD, 0.5))
        for i, (lab, tt) in enumerate(rows):
            y = 730 + i * 88
            d.line([(x + 24, y + 70), (x + 406, y + 70)], fill=A((40, 44, 58), 1), width=1)
            if t >= tt:
                ra = appear(t, tt, 0.12); mark(d, x + 28, y + 10, col, 1.15, ra)
                txt(d, x + 82, y + 4, lab, f(BAR, 46 if len(lab) < 16 else 38), WHITE, ra)
    if t >= tV:
        a = appear(t, tV, 0.1); d.ellipse([515, 840, 575, 900], fill=A(VGOLD, a)); txt(d, 545, 870, 'VS', f(BEB, 40), INK, a, 'mm')

# ---- S5: lab range bars (top strip) ----
def strip_labs(d, t, im, box, al):
    x0, y0, x1, y1 = box
    tG = cue('growing'); tC = cue('cortisol'); tL = cue('lipids')
    txt(d, x0 + 56, y0 + 18, 'BLOODWORK · 8 HRS SLEEP', f(MONO, 28), WHITE, al)
    if t >= tG: tag(d, x1 - 30 - tag_w(d, 'GROWTH ▲', 26), y0 + 12, 'GROWTH ▲', GREEN, 26, al * appear(t, tG))
    for i, (lab, tt) in enumerate([('CORTISOL', tC), ('LIPIDS', tL)]):
        by = y0 + 104 + i * 92; bx0, bx1 = x0 + 230, x1 - 50
        txt(d, x0 + 50, by - 8, lab, f(BAR, 44), WHITE, al)
        segs = [(0, 0.33, (79, 163, 224)), (0.33, 0.66, (60, 203, 106)), (0.66, 1, (240, 160, 48))]
        for s0, s1, c in segs: d.rectangle([lerp(bx0, bx1, s0), by + 8, lerp(bx0, bx1, s1) - 3, by + 30], fill=A(c, 0.85 * al))
        txt(d, lerp(bx0, bx1, 0.165), by + 38, 'LOW', f(MONO, 18), MUTED, al, 'mt'); txt(d, lerp(bx0, bx1, 0.5), by + 38, 'OPTIMAL', f(MONO, 18), MUTED, al, 'mt'); txt(d, lerp(bx0, bx1, 0.83), by + 38, 'HIGH', f(MONO, 18), MUTED, al, 'mt')
        v = 0.86 if t < tt else lerp(0.86, 0.48, expo((t - tt) / 0.6))
        mx = lerp(bx0, bx1, v)
        d.polygon([(mx - 16, by - 18), (mx + 16, by - 18), (mx, by + 6)], fill=A(WHITE, al))
        if GL: GL.polygon([(mx - 20, by - 22), (mx + 20, by - 22), (mx, by + 10)], fill=A(WHITE, al))
        d.line([(mx, by + 4), (mx, by + 34)], fill=A(WHITE, al), width=4)

# ---- S6: priority ladder ----
def scene_priority(d, t, im):
    tM = cue('most anabolic'); tF = cue('fix'); tB = cue('before'); tCo = cue('compounds')
    # #1 sleep
    a = appear(t, P_in[0] + 0.1, 0.2)
    d.rounded_rectangle([100, 580, 980, 820], radius=16, fill=A((40, 32, 8), 0.9 * a), outline=A(VGOLD, a), width=4)
    if GL: GL.rounded_rectangle([100, 580, 980, 820], radius=16, outline=A(VGOLD, a), width=10)
    bigstat(d, 130, 600, '01', 190, VGOLD, a)
    txt(d, 340, 610, 'SLEEP', f(BEB, 130), WHITE, a)
    if t >= tM: tag(d, 344, 750, 'MOST ANABOLIC', VGOLD, 28, appear(t, tM))
    if t >= tF:
        p = expo((t - tF) / 0.9); bx0, bx1 = 640, 950
        txt(d, bx0, 752, 'FIX', f(MONO, 24), CREAM, 1)
        d.rectangle([bx0 + 60, 756, bx1, 780], outline=A(GREY, 1), width=2); lit_bar(d, bx0 + 63, 759, lerp(bx0 + 63, bx1 - 3, p), 777, GREEN)
        if p > 0.95: check(d, bx1 - 40, 600, GREEN, 1.4, appear(t, tF + 0.9))
    # arrow
    if t >= tB:
        a2 = appear(t, tB, 0.2); arrow(d, 540, 840, 540, 900, WHITE, 6, a2); txt(d, 570, 856, 'THEN', f(MONO, 26), WHITE, a2)
    # #2 compounds
    on = t >= tCo
    b = 0.35 if not on else lerp(0.35, 1, appear(t, tCo, 0.2))
    d.rounded_rectangle([100, 920, 980, 1120], radius=16, fill=A((14, 16, 24), 0.9), outline=A(GREY if not on else CYAN, b), width=3)
    bigstat(d, 130, 932, '02', 150, (90, 94, 108) if not on else CYAN, 1)
    txt(d, 320, 950, 'COMPOUNDS', f(BEB, 104), (90, 94, 108) if not on else WHITE, 1)
    # padlock
    lx, ly = 900, 990; lc = (110, 114, 130) if not on else CYAN
    d.arc([lx - 22, ly - 40, lx + 22, ly + 6], 180, 360, fill=A(lc, 1), width=6); d.rounded_rectangle([lx - 32, ly - 14, lx + 32, ly + 40], radius=6, fill=A(lc, 1))
    txt(d, 320, 1066, 'LOCKED UNTIL 01 IS FIXED' if not on else 'ONLY AFTER 01 IS FIXED', f(MONO, 24), MUTED if not on else CYAN, 1)

# ---- CTA card ----
def cta_card(im, t, t0, t1, tc, y=1090, end=False):
    if not (t0 <= t < t1 + 0.2): return
    pin = expo((t - t0) / 0.22); pout = clamp((t - t1) / 0.2); a = pin * (1 - pout)
    if a <= 0: return
    yy = y + lerp(40, 0, pin); frosted(im, (56, yy, 1024, yy + 220), 0.84, 18)
    d = ImageDraw.Draw(im, 'RGBA')
    brackets(d, 56, yy, 1024, yy + 220, A(VGOLD, a), 30, 5)
    if GL: brackets(GL, 56, yy, 1024, yy + 220, A(VGOLD, a), 30, 10)
    lg = logo(170).copy(); lg.putalpha(lg.split()[3].point(lambda v: int(v * a))); im.alpha_composite(lg, (80, int(yy + 25)))
    d = ImageDraw.Draw(im, 'RGBA')
    txt(d, 280, yy + 22, 'FREE · SLEEP PROTOCOL FOR ENHANCED GUYS', f(MONO, 24), VGOLD, a)
    mx, my = 975, yy + 40; d.ellipse([mx - 18, my - 18, mx + 18, my + 18], fill=A(VGOLD, a)); d.ellipse([mx - 8, my - 24, mx + 24, my + 10], fill=A((8, 10, 16), a))
    if t >= tc:
        b = expo((t - tc) / 0.12) * (1 - pout); s = lerp(1.12, 1.0, b)
        fn = f(BEB, int(88 * s)); label = 'COMMENT  "SLEEP"'; tw = d.textlength(label, font=fn)
        lit_bar(d, 280, yy + 70, 280 + tw + 40, yy + 70 + int(104 * s), VGOLD, b); d.text((300, yy + 76), label, font=fn, fill=A(INK, b))
        if GL: GL.rectangle([276, yy + 66, 284 + tw + 40, yy + 74 + int(104 * s)], outline=A(VGOLD, b), width=12)
    else:
        txt(d, 282, yy + 80, 'Comment the word below', f(DMB, 46), CREAM, a * 0.9)
    if end: txt(d, 280, yy + 186, 'FOR RESEARCH & EDUCATIONAL PURPOSES ONLY  ·  @coach.agz', f(MONO, 18), MUTED, a)

# ---------------- timeline ----------------
def build_timeline():
    global SCENES, STRIPS, CTAS, VERDICTS, P_in, HOOK_END, BAND_END
    SCENES = [
        (cue('sleeping') - 0.1, cend('boys') + 0.3, scene_clock, 'TREN · SLEEP LOG', 'NIGHT 01'),
        (cue('but growth hormone') + 0.12, cend('gains') + 0.08, scene_night, 'OVERNIGHT', 'WHERE GAINS HAPPEN'),
        (cue('trend') + 0.05, cend('recovery', cue('training')) + 0.4, scene_compare, 'SAME GUY', 'TWO NIGHTS'),
        (cue('your sleep is the most') + 0.12, cend('compounds') + 0.4, scene_priority, 'PRIORITY', 'ORDER OF OPERATIONS'),
    ]
    STRIPS = [
        (cue('trenbolone definitely') - 0.1, cend('partitioning') - 0.1, strip_kpi),
        (cue('growing') - 0.3, cend('lipids') - 0.15, strip_labs),
    ]
    CTAS = [(cend('compounds') + 0.5, END, cue('comment the word'), True)]
    VERDICTS = [(cue('none'), 'SIDES ONLY', '= NO GAINS')]
    P_in = [0]
    HOOK_END = 6.0
    BAND_END = DUR / 2
SCENES = STRIPS = CTAS = VERDICTS = None; P_in = [0]

# ---------------- text hook + band ----------------
HOOK = ('2 to 3 hours of sleep', 'wasting your ', 'TREN', ' cycle')
def text_hook(im, t):
    if t >= HOOK_END + 0.15: return
    fade = 1 - clamp((t - HOOK_END) / 0.15); a = 1.0
    base = im.copy() if fade < 1 else None
    s = lerp(1.0, 1.04, clamp(t / HOOK_END))
    fn = f(DMB, int(78 * s)); d = ImageDraw.Draw(im, 'RGBA')
    l1, l2a, l2b, l2c = HOOK
    w1 = d.textlength(l1, font=fn); w2 = d.textlength(l2a, font=fn) + d.textlength(l2b, font=fn) + d.textlength(l2c, font=fn)
    bw = max(w1, w2) + 70; lh = int(96 * s); y = 276 - (s - 1) * 60
    bx0 = (W - bw) / 2
    frosted(im, (bx0, y - 26, bx0 + bw, y + 2 * lh + 26), 0.80, 16); d = ImageDraw.Draw(im, 'RGBA')
    d.rectangle([bx0, y - 26, bx0 + bw, y + 2 * lh + 26], fill=A(NAVY, 0.35 * a))
    d.rectangle([bx0, y - 26, bx0 + 8, y + 2 * lh + 26], fill=A(GOLD, a))
    d.text(((W - w1) / 2, y), l1, font=fn, fill=A(WHITE, a))
    x = (W - w2) / 2; d.text((x, y + lh), l2a, font=fn, fill=A(WHITE, a)); x += d.textlength(l2a, font=fn)
    d.text((x, y + lh), l2b, font=fn, fill=A(VGOLD, a)); d.text((x + d.textlength(l2b, font=fn), y + lh), l2c, font=fn, fill=A(WHITE, a))
    if GL and fade >= 1: GL.text((x, y + lh), l2b, font=fn, fill=A(VGOLD, 0.6 * a))
    if base is not None: im.paste(Image.blend(base, im, fade))
def topic_band(im, t):
    if not (HOOK_END + 0.15 <= t < BAND_END + 0.15): return
    a = clamp((t - HOOK_END - 0.15) / 0.15) * (1 - clamp((t - BAND_END) / 0.15))
    d = ImageDraw.Draw(im, 'RGBA')
    d.rectangle([8, 212, W, 352], fill=A(NAVY, 0.88 * a))
    d.line([(64, 240), (108, 240)], fill=A(GOLD, a), width=4); txt(d, 122, 224, '@coach.agz', f(MONO, 28), GOLD, a)
    fn = f(DMB, 54); s1 = 'Your sleep on '; txt(d, 64, 268, s1, fn, WHITE, a); txt(d, 64 + d.textlength(s1, font=fn), 268, 'TREN', fn, VGOLD, a)

# ---------------- captions ----------------
FIX = {'trend': 'TREN', 'two': '2', 'three': '3', 'eight': '8', 'trt': 'TRT'}
def build_groups():
    G = []; cur = []
    for i, x in enumerate(WORDS):
        if cur:
            prev = WORDS[cur[-1]]
            if len(cur) >= 3 or x['s'] - prev['e'] > 0.28 or prev['w'][-1] in '.,?!' or any(prev['e'] - 0.02 < c <= x['s'] + 0.02 for c in CUTS if x['s'] - prev['e'] > 0.15):
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
    if t > WORDS[lo[-1]]['e'] + 0.6: return None
    return lo
CAP_Y = 1335
def cap_word(w):
    k = norm(w)
    return FIX.get(k, w.upper().rstrip(',.?!'))
def captions(im, t):
    g = group_at(t)
    if not g: return
    d = ImageDraw.Draw(im, 'RGBA')
    ws = [cap_word(WORDS[i]['w']) for i in g]
    size = 124
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
def active_scene(t):
    for sc in SCENES:
        if sc[0] <= t < sc[1] + 0.16: return sc
    return None
STRIP_BOX = (64, 380, 1016, 672)
def frame(src, t):
    global GL
    z = 1.0 if seg_of(t) % 2 == 0 else 1.08
    if z != 1.0:
        big = src.resize((int(W * z), int(H * z)), Image.BICUBIC); ox = (big.width - W) // 2; oy = int((big.height - H) * 0.35); src = big.crop((ox, oy, ox + W, oy + H))
    sc = active_scene(t)
    g = 0
    if sc: g = min(ease_io((t - sc[0] + 0.05) / 0.30), 1 - ease_io((t - sc[1]) / 0.22))
    bg = src
    if g > 0: bg = Image.blend(src.filter(ImageFilter.GaussianBlur(18 * g)), Image.new('RGB', (W, H), (5, 8, 16)), 0.68 * g)
    im = bg.convert('RGBA')
    yy = np.arange(H); a = np.where(yy > 1180, np.clip((yy - 1180) / 260, 0, 1) * 110, 0); a = np.maximum(a, np.where(yy < 420, (1 - yy / 420) * 120, 0)); scr = (a * (1 - g)).astype(np.uint8)
    im.alpha_composite(Image.merge('RGBA', [Image.new('L', (W, H), c) for c in NAVY] + [Image.fromarray(np.repeat(scr[:, None], W, 1))]))
    glow = Image.new('RGBA', (W, H), (0, 0, 0, 0)); GL = ImageDraw.Draw(glow, 'RGBA')
    # strips (top cards, footage stays visible)
    for (s0, s1, fn) in STRIPS:
        if s0 <= t < s1 + 0.2:
            pin = expo((t - s0) / 0.2); pout = clamp((t - s1) / 0.18); al = pin * (1 - pout)
            if al <= 0: continue
            x0, y0, x1, y1 = STRIP_BOX; dy = lerp(-30, 0, pin)
            box = (x0, y0 + dy, x1, y1 + dy)
            frosted(im, box, 0.86, 14)
            lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay, 'RGBA')
            fn(d, t, lay, box, 1.0)
            lay.putalpha(lay.split()[3].point(lambda v: int(v * al))); im.alpha_composite(lay)
            d = ImageDraw.Draw(im, 'RGBA')
            d.rectangle(box, outline=A(VGOLD, 0.7 * al), width=3); brackets(d, *box, A(VGOLD, al), 36, 6); brackets(GL, *box, A(VGOLD, al), 36, 12)
            d.ellipse([box[0] + 26, box[1] + 26, box[0] + 42, box[1] + 42], fill=A(RED, al if int(t * 4) % 2 == 0 else al / 3))
    if sc:
        P_in[0] = sc[0]
        pin = expo((t - sc[0]) / 0.20); pout = clamp((t - sc[1]) / 0.16)
        if pout < 1:
            s = lerp(1.05, 1.0, pin) * lerp(1.0, 1.03, pout); w = (P[2] - P[0]) * s; h = (P[3] - P[1]) * s; cx = (P[0] + P[2]) / 2; cy = (P[1] + P[3]) / 2
            x0, y0, x1, y1 = cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2
            frosted(im, (x0, y0, x1, y1), 0.92, 8)
            lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay, 'RGBA')
            sc[2](d, t, lay)
            if pin < 1: lay = lay.filter(ImageFilter.GaussianBlur(8 * (1 - pin)))
            al = pin * (1 - pout); lay.putalpha(lay.split()[3].point(lambda v: int(v * al)))
            im.alpha_composite(lay); d = ImageDraw.Draw(im, 'RGBA')
            d.rectangle([x0, y0, x1, y1], outline=A(VGOLD, 0.8 * al), width=3); brackets(d, x0, y0, x1, y1, A(VGOLD, al), 48, 7)
            GL.rectangle([x0, y0, x1, y1], outline=A(VGOLD, 0.5 * al), width=6); brackets(GL, x0, y0, x1, y1, A(VGOLD, al), 48, 14)
            d.ellipse([x0 + 26, y0 + 26, x0 + 42, y0 + 42], fill=A(RED, al if int(t * 4) % 2 == 0 else al / 3))
            txt(d, x0 + 56, y0 + 18, sc[3], f(MONO, 28), WHITE, al); fr = f(MONO, 28); tw = d.textlength(sc[4], font=fr); txt(d, x1 - 30 - tw, y0 + 18, sc[4], fr, VGOLD, al)
            for (vt, a1, a2) in VERDICTS:
                if sc[0] <= vt <= sc[1] + 0.2 and t >= vt:
                    p = expo((t - vt) / 0.12); yv = 1150; vx0 = P[0] + 20; vx1 = lerp(vx0, P[2] - 20, p)
                    GL.rectangle([vx0 - 4, yv - 8, vx1 + 4, yv + 100], outline=A(RED, al), width=10)
                    lit_bar(d, vx0, yv, vx1, yv + 92, RED, al); d.rectangle([vx0, yv + 88, vx1, yv + 92], fill=A((140, 0, 0), al))
                    if p > 0.6:
                        fn = f(BEB, 80); d.text((vx0 + 30, yv + 6), a1, font=fn, fill=A(WHITE, al)); tw = d.textlength(a1, font=fn)
                        d.text((vx0 + 30 + tw + 24, yv + 26), a2, font=f(BEB, 60), fill=A(WHITE, al))
    for (c0, c1, cc, end) in CTAS: cta_card(im, t, c0, c1, cc, 1090, end)
    text_hook(im, t)
    GL = None
    if glow.getbbox():
        sm = glow.resize((W // 4, H // 4), Image.BILINEAR)
        g1 = np.asarray(sm.filter(ImageFilter.GaussianBlur(3.5))).astype(np.float32) / 255; g2 = np.asarray(sm.filter(ImageFilter.GaussianBlur(10))).astype(np.float32) / 255
        prem = np.clip(g1[..., :3] * g1[..., 3:] * 2.3 + g2[..., :3] * g2[..., 3:] * 1.8, 0, 1)
        prem = np.asarray(Image.fromarray((prem * 255).astype(np.uint8)).resize((W, H), Image.BILINEAR)).astype(np.float32) / 255
        b = np.asarray(im.convert('RGB')).astype(np.float32) / 255
        im = Image.fromarray(((1 - (1 - b) * (1 - prem)) * 255).astype(np.uint8)).convert('RGBA')
    d = ImageDraw.Draw(im, 'RGBA'); d.rectangle([0, 0, 7, H], fill=GOLD)
    topic_band(im, t)
    captions(im, t)
    out = im.convert('RGB')
    for (vt, _, _) in VERDICTS:
        k = round((t - vt - 0.12) * FPS)
        if k in (0, 1):
            dx = [9, -5][k]; zz = 1.025; big = out.resize((int(W * zz), int(H * zz)), Image.BICUBIC); ox = (big.width - W) // 2 - dx; oy = (big.height - H) // 2
            out = big.crop((ox, oy, ox + W, oy + H)); ImageDraw.Draw(out).rectangle([0, 0, 7, H], fill=GOLD)
    return out

build_timeline(); GROUPS = build_groups()
if __name__ == '__main__':
    mode = sys.argv[2]
    if mode == 'timeline':
        for sc in SCENES: print(f'{sc[0]:7.2f}-{sc[1]:7.2f} {sc[3]}')
        for sc in STRIPS: print(f'{sc[0]:7.2f}-{sc[1]:7.2f} strip {sc[2].__name__}')
        for sc in CTAS: print(f'{sc[0]:7.2f}-{sc[1]:7.2f} CTA pill@{sc[2]:.2f}')
        print('cuts', CUTS); sys.exit()
    if mode == 'stills':
        for tt in [float(x) for x in sys.argv[3:]]:
            subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', f'{tt:.3f}', '-i', X + 'cut.mov', '-frames:v', '1', S + 'qc/_src.png'])
            frame(Image.open(S + 'qc/_src.png').convert('RGB'), tt).resize((540, 960), Image.LANCZOS).save(S + f'qc/st_{tt:06.2f}.jpg', quality=85)
        sys.exit()
    n0, n1 = int(sys.argv[3]), int(sys.argv[4]); out = sys.argv[5]
    dec = subprocess.Popen(['ffmpeg', '-v', 'error', '-ss', f'{n0 / FPS:.4f}', '-i', X + 'cut.mov', '-frames:v', str(n1 - n0), '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], stdout=subprocess.PIPE)
    enc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-crf', '16', '-preset', 'medium', '-pix_fmt', 'yuv420p', out], stdin=subprocess.PIPE)
    for n in range(n0, n1):
        nb = dec.stdout.read(W * H * 3)
        if len(nb) == W * H * 3: buf = nb
        elif n < round(DUR * FPS) - 1: print('short', n); break   # past the end: hold last frame
        enc.stdin.write(frame(Image.frombuffer('RGB', (W, H), buf), n / FPS).tobytes())
    enc.stdin.close(); enc.wait(); dec.kill(); print('done', n0, n1)
