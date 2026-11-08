# Full test 03 — "Expectations" (genetics / realistic gains). 1080x1920 30 fps.
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
    L = math.hypot(x1 - x0, y1 - y0); n = int(L // (dash + gap)) + 1
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
P = (64, 470, 1016, 1262)   # full panel box

# ---- S1: client ask -> timeline zoom (line chart -> scale) ----
def scene_timeline(d, t, im):
    tA = cue('20'); tP = cue('pounds'); tM = cue('six months'); tS = cue('stop'); t90 = cue('90'); t5 = cue('fifth'); tSM = cue('social')
    x0, y0, x1, y1 = 170, 640, 960, 1040
    zoom = ease_io((t - tS) / 0.9)
    dom = lerp(6, 60, zoom)
    X_ = lambda m: x0 + m / dom * (x1 - x0)
    Y_ = lambda lb: y1 - lb / 30 * (y1 - y0 - 30)
    # grid + axes
    for lb in (10, 20, 30):
        y = Y_(lb); d.line([(x0, y), (x1, y)], fill=A((38, 42, 56), 1), width=1); txt(d, x0 - 16, y, str(lb), f(MONO, 24), MUTED, 1, 'rm')
    d.line([(x0, y1), (x1, y1)], fill=A(GREY, 1), width=3); d.line([(x0, y0), (x0, y1)], fill=A(GREY, 1), width=3)
    txt(d, x0 - 70, y0 - 64, 'LEAN MASS GAINED · LB', f(MONO, 26), CREAM, appear(t, P_in[0]))
    # x ticks: months fade out, years fade in
    am = 1 - clamp(zoom * 2); ay = clamp(zoom * 2 - 1)
    for m in range(0, 7):
        if am > 0: x = X_(m); d.line([(x, y1), (x, y1 + 10)], fill=A(GREY, am), width=2); txt(d, x, y1 + 18, f'{m}', f(MONO, 24), MUTED, am, 'mt')
    if am > 0: txt(d, x1, y1 + 52, 'MONTHS', f(MONO, 22), MUTED, am, 'rt')
    for yr in range(0, 6):
        if ay > 0: x = X_(yr * 12); d.line([(x, y1), (x, y1 + 10)], fill=A(GREY, ay), width=2); txt(d, x, y1 + 18, f'{yr}', f(MONO, 24), MUTED, ay, 'mt')
    if ay > 0: txt(d, x1, y1 + 52, 'YEARS', f(MONO, 22), MUTED, ay, 'rt')
    # highlights (beat B)
    if t >= t90:
        a = appear(t, t90, 0.2); xa, xb = X_(0), X_(3)
        d.rectangle([xa, y0, max(xa + 6, xb), y1], fill=A(CYAN, 0.28 * a)); d.line([(xb, y0), (xb, y1)], fill=A(CYAN, a), width=3)
        if GL: GL.line([(xb, y0), (xb, y1)], fill=A(CYAN, a), width=8)
        tag(d, max(xa, xb) + 18, Y_(5), 'YOUR FIRST 90 DAYS', CYAN, 26, a)
    if t >= t5:
        a = appear(t, t5, 0.2); xa, xb = X_(48), X_(60)
        d.rectangle([xa, y0, xb, y1], fill=A(VGOLD, 0.22 * a)); d.line([(xa, y0), (xa, y1)], fill=A(VGOLD, a), width=3)
        if GL: GL.line([(xa, y0), (xa, y1)], fill=A(VGOLD, a), width=8)
        tw = tag_w(d, 'THEIR YEAR 5', 26); tag(d, xb - tw - 8, y0 + 64, 'THEIR YEAR 5', VGOLD, 26, a)
    # expectation line: (0,0)->(6,25), band 20-30 at 6 months
    if t >= tA - 0.05:
        p = expo((t - tA) / 0.55)
        pts = [(X_(m / 4), Y_(25 * (m / 24) ** 0.9)) for m in range(0, 25)]
        polyline(d, partial(pts, p), RED, 6)
        if p >= 1:
            ex, ey = pts[-1]; d.ellipse([ex - 10, ey - 10, ex + 10, ey + 10], fill=A(WHITE, 1))
    if t >= tP:
        a = appear(t, tP, 0.18); ex = X_(6); yt, yb = Y_(30), Y_(20)
        d.line([(ex + 16, yt), (ex + 16, yb)], fill=A(RED, a), width=4); d.line([(ex + 8, yt), (ex + 24, yt)], fill=A(RED, a), width=4); d.line([(ex + 8, yb), (ex + 24, yb)], fill=A(RED, a), width=4)
        if zoom < 0.5: tag(d, ex - tag_w(d, '20–30 LB', 30) - 14, yt - 56, '20–30 LB', RED, 30, a * (1 - zoom * 2))
        else: tag(d, ex + 36, yt - 4, 'THE ASK', RED, 26, clamp(zoom * 2 - 1))
    if t >= tM and zoom < 0.5:
        a = appear(t, tM) * (1 - zoom * 2); ex = X_(6)
        dashed(d, ex, Y_(25), ex, y1, WHITE, 2, a=a); tag(d, ex - tag_w(d, 'IN 6 MONTHS', 26) / 2, y1 - 58, 'IN 6 MONTHS', WHITE, 26, a) if False else tag(d, ex - tag_w(d, 'IN 6 MONTHS', 26) + 10, y1 - 58, 'IN 6 MONTHS', VGOLD, 26, a)
    if tS <= t:
        a = appear(t, tS + 0.95, 0.2)
        if a > 0: tag(d, X_(6) + 36, Y_(20) + 10, 'TOO STEEP', RED, 24, a)
    # bottom stat
    if t >= tSM:
        a = appear(t, tSM, 0.18); yb = 1120
        d.line([(100, yb - 14), (980, yb - 14)], fill=A(GREY, a), width=2)
        w1 = bigstat(d, 100, yb, '90 DAYS', 92, CYAN, a)
        txt(d, 100 + w1 + 30, yb + 34, 'vs', f(MONO, 34), CREAM, a)
        n = int(lerp(90, 1825, expo((t - tSM - 0.1) / 0.6)))
        bigstat(d, 100 + w1 + 100, yb, f'{n:,} DAYS', 92, VGOLD, a)

# ---- S2: rate-of-gain gauge ----
def scene_gauge(d, t, im):
    tN = cue('never'); tF = cue('fast'); tB = cue('building'); tK = cue('keeping')
    cx, cy, r = 540, 1060, 330
    def ang(v): return math.pi * (1 - v)   # v 0..1 -> left..right
    def pt(v, rr): a = ang(v); return (cx + rr * math.cos(a), cy - rr * math.sin(a))
    txt(d, 540, 590, 'RATE OF GAIN', f(MONO, 30), CREAM, 1, 'mt')
    # zone arcs
    for (v0, v1, col) in [(0.0, 0.62, VGOLD), (0.62, 0.78, (255, 120, 30)), (0.78, 1.0, RED)]:
        lit = 1.0 if col != VGOLD else (0.55 + 0.45 * appear(t, tB + 0.2, 0.3))
        d.arc([cx - r, cy - r, cx + r, cy + r], 180 + v0 * 180, 180 + v1 * 180, fill=A(col, lit), width=34)
        if GL: GL.arc([cx - r, cy - r, cx + r, cy + r], 180 + v0 * 180, 180 + v1 * 180, fill=A(col, 0.6 * lit), width=44)
    for k in range(0, 11):
        v = k / 10; p0 = pt(v, r - 30); p1 = pt(v, r - (58 if k % 5 == 0 else 46)); d.line([p0, p1], fill=A(WHITE, 0.8), width=3)
    txt(d, cx - r + 10, cy + 20, 'SLOW', f(MONO, 24), MUTED, 1); txt(d, cx + r - 10, cy + 20, 'MAX', f(MONO, 24), MUTED, 1, 'ra')
    # needle
    if t < tB: v = 0.93 + 0.025 * math.sin(t * 40) * appear(t, P_in[0] + 0.15, 0.3)
    else: v = lerp(0.95, 0.42, expo((t - tB) / 0.5))
    v0 = 0.05
    vv = lerp(v0, v, expo((t - P_in[0] - 0.1) / 0.35))
    tip = pt(vv, r - 70); bl = pt(vv + 0.25, 16); br_ = pt(vv - 0.25, 16)
    d.polygon([tip, (cx + 14 * math.cos(ang(vv) + 1.57), cy - 14 * math.sin(ang(vv) + 1.57)), (cx + 14 * math.cos(ang(vv) - 1.57), cy - 14 * math.sin(ang(vv) - 1.57))], fill=A(WHITE, 1))
    if GL: GL.line([(cx, cy), tip], fill=A(WHITE, 0.6), width=10)
    d.ellipse([cx - 26, cy - 26, cx + 26, cy + 26], fill=A((20, 24, 34), 1), outline=A(WHITE, 1), width=4)
    # labels
    if t >= tN - 0.3:
        a = appear(t, tN - 0.3); pr = pt(0.89, r + 70); tw = tag_w(d, 'AS FAST AS POSSIBLE', 26)
        tag(d, min(1000 - tw, pr[0] - tw / 2), pr[1] - 40, 'AS FAST AS POSSIBLE', RED, 26, a)
    if t >= tF + 0.15:
        a = appear(t, tF + 0.15, 0.12); px, py = pt(0.80, r - 115)
        cross(d, px - 30, py - 30, RED, 2.0, a)
        tag(d, 680, 1110, 'NOT THE GOAL', RED, 30, a)
    if t >= tK - 0.1:
        a = appear(t, tK - 0.1); px, py = pt(0.42, r + 62)
        tw = tag_w(d, 'MUSCLE WORTH KEEPING', 28); tag(d, px - tw / 2, py - 40, 'MUSCLE WORTH KEEPING', VGOLD, 28, a)
        check(d, 110, 1118, GREEN, 1.2, a); txt(d, 160, 1112, 'SUSTAINABLE', f(MONO, 30), GREEN, a)

# ---- S3: ECG monitor (top strip, no push) ----
def ecg_wave(u):   # u in beats
    p = u % 1.0
    if 0.10 < p < 0.16: return 0.15 * math.sin((p - 0.10) / 0.06 * math.pi)
    if 0.20 < p < 0.22: return -0.15 * (p - 0.20) / 0.02
    if 0.22 <= p < 0.25: return lerp(-0.15, 1.0, (p - 0.22) / 0.03)
    if 0.25 <= p < 0.28: return lerp(1.0, -0.35, (p - 0.25) / 0.03)
    if 0.28 <= p < 0.31: return lerp(-0.35, 0, (p - 0.28) / 0.03)
    if 0.42 < p < 0.56: return 0.25 * math.sin((p - 0.42) / 0.14 * math.pi)
    return 0.0
def strip_ecg(d, t, im, box, al):
    x0, y0, x1, y1 = box
    tD = cue('disposable'); tDie = cue('die'); t10 = cue('10 years') if True else 0; tK = cue('kids'); tX = cue('destroy')
    txt(d, x0 + 56, y0 + 18, 'LONG-TERM HEALTH', f(MONO, 28), WHITE, al)
    # grid
    gx0, gy0, gx1, gy1 = x0 + 30, y0 + 70, x1 - 30, y1 - 24
    for gx in range(int(gx0), int(gx1), 40): d.line([(gx, gy0), (gx, gy1)], fill=A((30, 40, 36), al), width=1)
    for gy in range(int(gy0), int(gy1), 40): d.line([(gx0, gy), (gx1, gy)], fill=A((30, 40, 36), al), width=1)
    mid = (gy0 + gy1) / 2 + 30; amp = (gy1 - gy0) * 0.42
    flat_at = tDie + 0.1
    col = GREEN if t < tD else RED
    pts = []
    N = 220
    for i in range(N + 1):
        x = lerp(gx0, gx1, i / N)
        ts = t - (1 - i / N) * 2.2           # sample time (scrolling)
        bpm = 1.25 if ts < tD else 2.1
        y = ecg_wave(ts * bpm) if ts < flat_at else 0
        if tD <= ts < flat_at: y *= 1.15 + 0.25 * math.sin(ts * 23)
        pts.append((x, mid - y * amp))
    d.line(pts, fill=A(col, al), width=5, joint='curve')
    if GL: GL.line(pts, fill=A(col, al), width=12)
    hx, hy = pts[-1]; d.ellipse([hx - 8, hy - 8, hx + 8, hy + 8], fill=A(WHITE, al))
    # readout
    if t < flat_at: bpm_txt = '72' if t < tD else str(118 + int(6 * math.sin(t * 5)))
    else: bpm_txt = '0'
    bigstat(d, x1 - 200, y0 + 6, bpm_txt, 64, col, al); txt(d, x1 - 70, y0 + 30, 'BPM', f(MONO, 22), col, al)
    if t >= tD: tag(d, x0 + 360, y0 + 16, 'DISPOSABLE?', RED, 26, al * appear(t, tD))
    if t >= flat_at:
        a = al * appear(t, flat_at, 0.1)
        tag(d, gx0 + 10, gy1 - 52, 'FLATLINE', RED, 28, a)
        tag(d, gx0 + 10 + tag_w(d, 'FLATLINE', 28) + 14, gy1 - 52, 'IN 10 YEARS', WHITE, 28, a) if False else None
        tw = bigstat(d, gx1 - 270, mid - 130, '10 YRS', 96, RED, a)
    if t >= tK:
        a = al * appear(t, tK); tag(d, gx0 + 10 + tag_w(d, 'FLATLINE', 28) + 14, gy1 - 52, 'NO FATHER', WHITE, 28, a)

# ---- S5: genetics: ceiling + response quadrant -> bell curve ----
def scene_genetics(d, t, im):
    tC = cue('ceiling'); tR = cue('respond'); tT = cue('tolerate'); tB = cue('combination'); tBell = cue("there's a very specific", tB)
    tPh = cue('phil'); tRo = cue('ronnie')
    qa = 1 - clamp((t - tBell) / 0.25)      # quadrant fades out
    ba = clamp((t - tBell - 0.15) / 0.3)    # bell fades in
    # --- quadrant
    if qa > 0:
        x0, y0, x1, y1 = 200, 690, 960, 1200; mx, my = (x0 + x1) / 2, (y0 + y1) / 2
        # ceiling
        if t >= tC - 0.05:
            p = expo((t - tC) / 0.4)
            dashed(d, 100, 600, lerp(100, 980, p), 600, VGOLD, 4, a=qa, glow=True)
            if p > 0.6: tag(d, 100, 548, 'GENETIC CEILING', VGOLD, 26, qa)
        for (bx0, by0, bx1, by1, lab, tt, col) in [(mx, my, x1, y1, 'HYPER-\nRESPONDER', tR, CYAN), (x0, y0, mx, my, 'HYPER-\nTOLERATOR', tT, CYAN), (mx, y0, x1, my, 'BOTH', tB, VGOLD)]:
            if t >= tt:
                a = appear(t, tt, 0.18) * qa
                d.rectangle([bx0 + 4, by0 + 4, bx1 - 4, by1 - 4], fill=A(col, 0.16 * a), outline=A(col, a), width=3)
                if GL: GL.rectangle([bx0 + 4, by0 + 4, bx1 - 4, by1 - 4], outline=A(col, a), width=8)
                fn = f(BEB, 58 if lab != 'BOTH' else 96)
                d.multiline_text(((bx0 + bx1) / 2, (by0 + by1) / 2), lab, font=fn, fill=A(WHITE, a), anchor='mm', align='center', spacing=0)
        d.line([(x0, my), (x1, my)], fill=A(GREY, qa), width=2); d.line([(mx, y0), (mx, y1)], fill=A(GREY, qa), width=2)
        d.rectangle([x0, y0, x1, y1], outline=A((90, 94, 110), qa), width=3)
        arrow(d, x0, y1 + 30, x1, y1 + 30, MUTED, 3, qa); txt(d, x1, y1 + 42, 'RESPONSE', f(MONO, 24), CREAM, qa, 'rt')
        arrow(d, x0 - 34, y1, x0 - 34, y0, MUTED, 3, qa)
        rt = rot_text('TOLERANCE', f(MONO, 24), CREAM, qa); im.alpha_composite(rt, (int(x0 - 82), int(y0)))
        if t >= tB:
            pulse = 0.5 + 0.5 * math.sin(t * 7); cx, cy = (mx + x1) / 2 + 120, (y0 + my) / 2 - 70
            d.ellipse([cx - 16, cy - 16, cx + 16, cy + 16], fill=A(VGOLD, qa)); d.ellipse([cx - 16 - 14 * pulse, cy - 16 - 14 * pulse, cx + 16 + 14 * pulse, cy + 16 + 14 * pulse], outline=A(VGOLD, qa * (1 - pulse)), width=3)
            if GL: GL.ellipse([cx - 26, cy - 26, cx + 26, cy + 26], fill=A(VGOLD, qa))
    # --- bell curve
    if ba > 0:
        x0, y0, x1, y1 = 110, 640, 970, 1110
        mu, sg = 0.42, 0.14
        g = lambda u: math.exp(-((u - mu) ** 2) / (2 * sg * sg))
        p = expo((t - tBell - 0.15) / 0.8)
        pts = [(lerp(x0, x1, i / 200), y1 - g(i / 200) * (y1 - y0 - 40)) for i in range(201)]
        shown = partial(pts, p)
        if len(shown) > 2:
            fill = shown + [(shown[-1][0], y1), (x0, y1)]
            d.polygon(fill, fill=A(CYAN, 0.13 * ba))
        # majority shading (mu +/- 1 sigma)
        polyline(d, shown, CYAN, 5, ba)
        d.line([(x0, y1), (x1, y1)], fill=A(GREY, ba), width=3)
        txt(d, x0, y1 + 16, 'BELOW AVERAGE', f(MONO, 22), MUTED, ba); txt(d, x1, y1 + 16, 'ELITE', f(MONO, 22), MUTED, ba, 'ra')
        txt(d, lerp(x0, x1, mu), y1 - 150, 'MOST', f(BEB, 64), WHITE, ba * appear(t, tBell + 0.7, 0.3), 'mm')
        txt(d, lerp(x0, x1, mu), y1 - 100, 'LIFTERS', f(BEB, 64), WHITE, ba * appear(t, tBell + 0.7, 0.3), 'mm')
        # gold dot handoff: flies from quadrant into the tail
        src = ((200 + 960) / 2 + (960 - 580) / 2 + 120 - 190 + 190, 0)
        tail_x = lerp(x0, x1, 0.965); tail_y = y1 - g(0.965) * (y1 - y0 - 40) - 4
        fp = expo((t - tBell) / 0.6); sx, sy = (770 + 190 - 190 + 120 - 120 + 0, 755)
        sx, sy = 865, 755
        dx, dy = lerp(sx, tail_x, fp), lerp(sy, tail_y, fp)
        d.ellipse([dx - 14, dy - 14, dx + 14, dy + 14], fill=A(VGOLD, 1))
        if GL: GL.ellipse([dx - 26, dy - 26, dx + 26, dy + 26], fill=A(VGOLD, 1))
        if t >= tPh:
            a = appear(t, tPh); d.line([(tail_x, tail_y - 20), (tail_x, 760)], fill=A(VGOLD, a), width=3)
            tw = tag_w(d, '1  PHIL HEATH', 28); tag(d, tail_x - tw + 12, 712, '1  PHIL HEATH', VGOLD, 28, a)
        if t >= tRo:
            a = appear(t, tRo); tw = tag_w(d, '1  RONNIE COLEMAN', 28); tag(d, tail_x - tw + 12, 652, '1  RONNIE COLEMAN', VGOLD, 28, a)
        if t >= tRo + 0.6:
            a = appear(t, tRo + 0.6); txt(d, tail_x - 8, 820, 'THE TAIL', f(MONO, 24), VGOLD, a, 'ra')

# ---- S7: client file (document) ----
DOC = None
def make_doc():
    w, h = 760, 640
    im = Image.new('RGB', (w, h), (238, 236, 230)); d = ImageDraw.Draw(im)
    d.rectangle([0, 0, w, 84], fill=(16, 24, 48)); d.text((28, 22), 'CLIENT PROGRESS FILE', font=f(MONOB, 32), fill=WHITE)
    d.text((w - 28, 30), '#0417', font=f(MONO, 26), fill=(180, 186, 200), anchor='ra')
    rows = [('Weekly dose', 'LOW'), ('Training age', '—'), ('Lean mass trend', '')]
    for i, (k, v) in enumerate(rows):
        y = 112 + i * 92
        d.text((28, y + 14), k, font=f(DMR, 32), fill=(70, 74, 86))
        d.text((360, y + 4), v, font=f(DMB, 48), fill=INK)
        d.line([(24, y + 84), (w - 24, y + 84)], fill=(212, 210, 204), width=2)
    # chart box
    d.rectangle([28, 400, w - 28, h - 28], outline=(200, 198, 192), width=2)
    for k in range(1, 4): d.line([(28, 400 + k * 53), (w - 28, 400 + k * 53)], fill=(225, 223, 218), width=1)
    d.text((40, 408), 'LBM', font=f(MONO, 20), fill=(140, 140, 150))
    return im.convert('RGBA')
def scene_client(d, t, im):
    global DOC
    tL = cue('low'); tG = cue('grow'); tI = cue('insane'); tJ = cue('jealous')
    if DOC is None: DOC = make_doc()
    ox, oy = 160, 540
    im.alpha_composite(DOC, (ox, oy))
    # trend line in the document chart (drawn as ink)
    cx0, cy0, cx1, cy1 = ox + 60, oy + 430, ox + 720, oy + 600
    p = expo((t - tG) / 0.9) if t >= tG else 0
    pts = [(lerp(cx0, cx1, i / 30), cy1 - ((i / 30) ** 1.6) * (cy1 - cy0)) for i in range(31)]
    if p > 0: d.line(partial(pts, p), fill=A((20, 40, 160), 1), width=5, joint='curve')
    # red pen marks
    if t >= tL:
        a = appear(t, tL, 0.2); bx = ox + 340
        d.ellipse([bx, oy + 104, bx + 150, oy + 186], outline=A((210, 10, 20), a), width=5)
    if t >= tG:
        a = appear(t, tG + 0.6, 0.2); tag(d, ox + 470, oy + 300 - 6, 'GROWING FAST', RED, 26, a)
    if t >= tJ:
        a = appear(t, tJ); tag(d, ox + 760 - tag_w(d, 'HYPER-RESPONDER', 28), oy + 652, 'HYPER-RESPONDER', CYAN, 28, a)
    if t >= tI:
        # stamp: scales down hard
        p = expo((t - tI) / 0.12); s = lerp(1.6, 1.0, p)
        st = Image.new('RGBA', (420, 150), (0, 0, 0, 0)); sd = ImageDraw.Draw(st)
        sd.rounded_rectangle([6, 6, 414, 144], radius=12, outline=(220, 20, 30, 230), width=8)
        sd.text((210, 78), 'OUTLIER', font=f(BEB, 112), fill=(220, 20, 30, 230), anchor='mm')
        st = st.rotate(-9, expand=True, resample=Image.BICUBIC).resize((int(st.width * s * 1.0) + 40, int(st.height * s) + 70), Image.BICUBIC)
        st.putalpha(st.split()[3].point(lambda v: int(v * p)))
        im.alpha_composite(st, (int(ox + 470 - st.width / 2), int(oy + 500 - st.height / 2)))

# ---- S8: my inputs checklist (top strip) ----
def strip_inputs(d, t, im, box, al):
    x0, y0, x1, y1 = box
    items = [('TRAINING', cue('training')), ('NUTRITION', cue('nutrition')), ('RECOVERY', cue('recovery')),
             ('SLEEP', cue('sleep')), ('BLOODWORK', cue('blood')), ('EVERY DAY', cue('every single day', cue('optimized')))]
    txt(d, x0 + 56, y0 + 18, 'MY INPUTS', f(MONO, 28), WHITE, al)
    n = sum(1 for _, tt in items if t >= tt)
    for i, (nm, tt) in enumerate(items):
        cx = x0 + 50 + (i % 2) * 440; cy = y0 + 68 + (i // 2) * 54
        d.rectangle([cx, cy, cx + 38, cy + 38], outline=A(GREY, al), width=3)
        if t >= tt:
            a = al * appear(t, tt, 0.12); check(d, cx + 4, cy + 3, GREEN, 1.0, a); txt(d, cx + 58, cy - 2, nm, f(BAR, 40), WHITE, a)
        else: txt(d, cx + 58, cy - 2, nm, f(BAR, 40), (90, 94, 108), al)
    # effort meter
    my = y1 - 44; fr = n / 6
    txt(d, x0 + 50, my - 2, 'EFFORT', f(MONO, 24), CREAM, al)
    mx0, mx1 = x0 + 190, x1 - 140
    d.rectangle([mx0, my, mx1, my + 26], outline=A(GREY, al), width=2)
    prev = (n - 1) / 6 if n > 0 else 0
    tt = items[n - 1][1] if n > 0 else 0
    cur = lerp(prev, fr, expo((t - tt) / 0.3)) if n > 0 else 0
    if cur > 0: lit_bar(d, mx0 + 3, my + 3, lerp(mx0 + 3, mx1 - 3, cur), my + 23, VGOLD, al)
    txt(d, x1 - 40, my - 8, f'{int(round(cur * 100))}%', f(BEB, 44), VGOLD, al, 'ra')

# ---- S9: grouped bar chart them vs me ----
def scene_bars(d, t, im):
    tF = cue('fourth'); groups = [('6 MO', cue('six months', tF)), ('1 YR', cue('year', tF)), ('3 YR', cue('three', tF)), ('5 YR', cue('five', tF))]
    x0, y0, x1, y1 = 120, 700, 960, 1150
    them = [0.38, 0.58, 0.82, 1.0]
    d.line([(x0, y1), (x1, y1)], fill=A(GREY, 1), width=3)
    for k in range(1, 5): d.line([(x0, y1 - k * (y1 - y0) / 4), (x1, y1 - k * (y1 - y0) / 4)], fill=A((34, 38, 52), 1), width=1)
    # legend
    lit_bar(d, 100, 584, 130, 614, VGOLD); txt(d, 142, 582, 'CLIENTS · LOW DOSE', f(MONO, 26), CREAM)
    lit_bar(d, 100, 630, 130, 660, CYAN); txt(d, 142, 628, 'ME · MAX EFFORT', f(MONO, 26), CREAM)
    gw = (x1 - x0) / 4
    for i, ((lab, tt), hv) in enumerate(zip(groups, them)):
        gx = x0 + i * gw + 24; bw = (gw - 60) / 2
        t0 = min(tt, tF + 0.2) if i == 0 else tt
        p = expo((t - t0) / 0.45) if t >= t0 else 0
        a = 1 if t >= t0 else 0.25
        txt(d, gx + bw, y1 + 14, lab, f(MONO, 26), CREAM if t >= t0 else MUTED, 1, 'mt')
        if p > 0:
            hT = hv * (y1 - y0) * p; hM = hv * 0.25 * (y1 - y0) * expo((t - t0 - 0.12) / 0.45)
            lit_col(d, gx, y1 - hT, gx + bw, y1, VGOLD); lit_col(d, gx + bw + 8, y1 - hM, gx + 2 * bw + 8, y1, CYAN)
            if GL: GL.rectangle([gx, y1 - hT, gx + bw, y1], outline=A(VGOLD, 0.8), width=6); GL.rectangle([gx + bw + 8, y1 - hM, gx + 2 * bw + 8, y1], outline=A(CYAN, 0.8), width=6)
    if t >= tF:
        a = appear(t, tF, 0.14); s = lerp(1.25, 1, expo((t - tF) / 0.14))
        bigstat(d, 700, 540, '¼', int(170 * s), CYAN, a)
        txt(d, 812, 600, 'OF THEIR', f(MONO, 26), CREAM, a); txt(d, 812, 632, 'GAINS', f(MONO, 26), CREAM, a)

# ---- S10: amplifier (genetics x gear, capped by ceiling) ----
def scene_amp(d, t, im):
    tS = cue('steroids'); tBl = cue('blow'); tGuy = cue('guy'); tO = cue('optimize'); tAm = cue('amplify'); tC = cue('ceiling', tAm)
    base_y = 1150; top = 640; Hh = base_y - top
    cols = [(150, 'AVERAGE', 0.30, 0.52), (590, 'ELITE', 0.62, 1.0)]  # x, label, genetics, ceiling
    for i, (cx, lab, gen, ceil) in enumerate(cols):
        w = 340
        d.rectangle([cx, top, cx + w, base_y], outline=A((44, 48, 62), 1), width=2)
        txt(d, cx + w / 2, base_y + 16, lab + ' GENETICS', f(MONO, 24), CREAM, 1, 'mt')
        # ceiling line
        cyl = base_y - ceil * Hh
        ca = appear(t, tO - 0.2 if i == 0 else tGuy, 0.25)
        flash = 1.0 if t < tC else (0.6 + 0.4 * math.sin((t - tC) * 18))
        ccol = VGOLD if t < tC else RED
        if ca > 0:
            dashed(d, cx - 10, cyl, cx + w + 10, cyl, ccol, 5, a=ca * flash, glow=True)
            txt(d, cx + w, cyl - 34, 'CEILING', f(MONO, 22), ccol, ca, 'ra')
        # genetics base
        if i == 1: pg = expo((t - tBl) / 0.35)
        else: pg = expo((t - tO) / 0.4)
        if pg > 0:
            hb = gen * Hh * pg; lit_col(d, cx + 20, base_y - hb, cx + w - 20, base_y, (120, 128, 150))
            if pg > 0.5: txt(d, cx + w / 2, base_y - hb / 2, 'GENETICS', f(BEB, 46), INK, 1, 'mm')
            # gear layer: grows up to ceiling only
            ga_t = tBl + 0.25 if i == 1 else tAm
            pa = expo((t - ga_t) / 0.6) if t >= ga_t else 0
            if pa > 0:
                ha = (ceil - gen) * Hh * pa; yA = base_y - hb - ha
                lit_col(d, cx + 20, yA, cx + w - 20, base_y - hb, VGOLD)
                if GL: GL.rectangle([cx + 20, yA, cx + w - 20, base_y - hb], outline=A(VGOLD, 0.9), width=8)
                if ha > 50: txt(d, cx + w / 2, yA + ha / 2, '+ GEAR', f(BEB, 46), INK, 1, 'mm')
    if t >= tGuy:
        a = appear(t, tGuy); tag(d, 590, 560, 'THAT ONE GUY', VGOLD, 28, a)
    if t >= tO - 0.1:
        a = appear(t, tO - 0.1); tag(d, 150, 560, 'YOU', CYAN, 28, a)
    if t >= tAm:
        a = appear(t, tAm); txt(d, 540, 900, '×', f(BEB, 120), WHITE, a, 'mm')

# ---- S11: waffle 80-85% ----
def scene_waffle(d, t, im):
    t8 = cue('80'); tG = cue('genetics', t8); tU = cue('unfortunate')
    gx0, gy0, s = 120, 700, 46
    p = clamp((t - t8 - 0.1) / 1.4)
    nfill = int(round(ease_io(p) * 85))
    for k in range(100):
        r_, c_ = divmod(k, 10); x = gx0 + c_ * s; y = gy0 + r_ * s
        if k < nfill:
            col = RED if k < 80 else (255, 110, 90)
            d.ellipse([x, y, x + 34, y + 34], fill=A(col, 1))
            if GL and k >= nfill - 6: GL.ellipse([x - 4, y - 4, x + 38, y + 38], fill=A(col, 0.9))
        else:
            gold = t >= tG + 0.2
            d.ellipse([x, y, x + 34, y + 34], outline=A(VGOLD if gold else (60, 64, 80), 1), width=3, fill=A(VGOLD, 0.85) if (gold and k >= 85) else None)
            if gold and k >= 85 and GL: GL.ellipse([x - 4, y - 4, x + 38, y + 38], fill=A(VGOLD, 0.6))
    txt(d, gx0, 600, '100 GUYS ON GEAR', f(MONO, 28), CREAM, 1)
    lo = int(round(lerp(0, 80, ease_io(clamp((t - t8 - 0.1) / 1.2)))))
    a = appear(t, t8)
    if t < t8 + 1.3: bigstat(d, 620, 700, f'{lo}%', 170, RED, a)
    else:
        b = expo((t - t8 - 1.3) / 0.12); bigstat(d, 620, 730, '80–85%', int(lerp(150, 124, b)), RED, 1)
    if t >= tG:
        b = appear(t, tG); txt(d, 624, 990, 'LIMITED', f(MONO, 28), WHITE, b); txt(d, 624, 1026, 'GENETICS', f(MONO, 28), WHITE, b)
    if t >= tG + 0.2:
        b = appear(t, tG + 0.2); tag(d, gx0, 1180, 'THE OTHER 15–20%', VGOLD, 28, b)

# ---- S12: progress (top strip) ----
def strip_progress(d, t, im, box, al):
    x0, y0, x1, y1 = box
    tP = cue('progress'); tB = cue('best'); tE = cue('every', tB)
    txt(d, x0 + 56, y0 + 18, 'YOU vs YOU', f(MONO, 28), WHITE, al)
    gx0, gy0, gx1, gy1 = x0 + 40, y0 + 80, x1 - 60, y1 - 30
    d.line([(gx0, gy1), (gx1, gy1)], fill=A(GREY, al), width=2)
    pts = []
    for i in range(41):
        u = i / 40; pts.append((lerp(gx0, gx1, u), gy1 - (u * 0.85 + 0.04 * math.sin(u * 19)) * (gy1 - gy0)))
    p = clamp((t - tP + 0.1) / 2.2)
    polyline(d, partial(pts, ease_io(p)), GREEN, 6, al)
    for k in (10, 20, 30):
        if p * 40 >= k:
            x, y = pts[k]; d.ellipse([x - 8, y - 8, x + 8, y + 8], fill=A(WHITE, al))
    if t >= tB:
        a = al * appear(t, tB); x, y = pts[-1]
        d.ellipse([x - 14, y - 14, x + 14, y + 14], fill=A(VGOLD, a))
        if GL: GL.ellipse([x - 26, y - 26, x + 26, y + 26], fill=A(VGOLD, a))
        tw = tag_w(d, 'BEST VERSION', 26); tag(d, x - tw - 20, y - 8, 'BEST VERSION', VGOLD, 26, a)
    if t >= tE:
        a = al * appear(t, tE); tag(d, gx0 + 10, gy0 - 6, '+1% EVERY DAY', GREEN, 26, a) if False else tag(d, gx0 + 10, gy0 - 6, 'EVERY SINGLE DAY', GREEN, 26, a)

# ---- CTA card (mid + end) ----
def cta_card(im, t, t0, t1, tc, y=1040, end=False):
    if not (t0 <= t < t1 + 0.2): return
    pin = expo((t - t0) / 0.22); pout = clamp((t - t1) / 0.2); a = pin * (1 - pout)
    if a <= 0: return
    dy = lerp(40, 0, pin)
    yy = y + dy; frosted(im, (56, yy, 1024, yy + 220), 0.84, 18)
    d = ImageDraw.Draw(im, 'RGBA')
    brackets(d, 56, yy, 1024, yy + 220, A(VGOLD, a), 30, 5)
    if GL: brackets(GL, 56, yy, 1024, yy + 220, A(VGOLD, a), 30, 10)
    lg = logo(170).copy(); lg.putalpha(lg.split()[3].point(lambda v: int(v * a))); im.alpha_composite(lg, (80, int(yy + 25)))
    d = ImageDraw.Draw(im, 'RGBA')
    txt(d, 280, yy + 22, 'FREE · MUSCLE GROWTH TRACKING FRAMEWORK' if not end else '@coach.agz · GROWTH FRAMEWORK', f(MONO, 24), VGOLD, a)
    # mini rising sparkline icon
    sp = [(940 + i * 8, yy + 52 - (i ** 1.4) * 2.2) for i in range(8)]
    d.line(sp, fill=A(GREEN, a), width=4)
    if t >= tc:
        b = expo((t - tc) / 0.12) * (1 - pout); s = lerp(1.12, 1.0, b)
        fn = f(BEB, int(88 * s)); label = 'COMMENT  "GROWTH"'; tw = d.textlength(label, font=fn)
        lit_bar(d, 280, yy + 70, 280 + tw + 40, yy + 70 + int(104 * s), VGOLD, b); d.text((300, yy + 76), label, font=fn, fill=A(INK, b))
        if GL: GL.rectangle([276, yy + 66, 284 + tw + 40, yy + 74 + int(104 * s)], outline=A(VGOLD, b), width=12)
    else:
        txt(d, 282, yy + 80, 'Comment the word below', f(DMB, 46), CREAM, a * 0.9)
    if end: txt(d, 280, yy + 186, 'FOR RESEARCH & EDUCATIONAL PURPOSES ONLY', f(MONO, 18), MUTED, a)

# ---------------- timeline ----------------
def build_timeline():
    global SCENES, STRIPS, CTAS, VERDICTS, P_in, HOOK_END, BAND_END
    SCENES = [  # t_in, t_out, fn, header_left, header_right
        (cue("they're") - 0.05, cend('social media') + 0.45, scene_timeline, 'CLIENT INTAKE', 'EXPECTATION CHECK'),
        (cue('because the goal') - 0.05, cend('keeping') + 0.55, scene_gauge, 'THE GOAL', 'SPEED vs QUALITY'),
        (cue('genetic ceiling') - 0.25, cend('ronnie coleman') + 0.45, scene_genetics, 'GENETIC PROFILE', 'RESPONSE MAP'),
        (cue('handful') - 0.1, cend('insane') + 0.45, scene_client, 'CLIENT FILE', 'EVIDENCE'),
        (cue('probably') - 0.1, cend('five years') + 0.45, scene_bars, 'MUSCLE GAINED', 'THEM vs ME'),
        (cue('steroids') - 0.1, cend('ceiling', cue('amplify')) + 0.6, scene_amp, 'WHAT GEAR DOES', 'AMPLIFIER'),
        (cue('80') - 0.25, cend('unfortunate') + 0.3, scene_waffle, 'THE ODDS', 'POPULATION'),
    ]
    STRIPS = [
        (cue('without') - 0.05, cend('around you') + 0.35, strip_ecg),
        (cue('training') - 0.1, cend('every single day', cue('optimized')) + 0.5, strip_inputs),
        (cue('progress') - 0.15, END, strip_progress),
    ]
    CTAS = [
        (cue('if you want') - 0.05, cend('absolutely free') + 0.3, cue('comment the word'), False),
        (cue('every single day', cue('best')) - 0.1, END, cue('appreciate'), True),
    ]
    VERDICTS = [(cue('ceiling', cue('amplify')), 'GENETICS', '= YOUR CEILING')]
    P_in = [0]
    HOOK_END = 6.0
    BAND_END = DUR / 2
SCENES = STRIPS = CTAS = VERDICTS = None; P_in = [0]

# ---------------- text hook + band ----------------
HOOK = (['Expecting 20 to 30 lbs', 'in 6 months on '], 'STEROIDS')
def text_hook(im, t):
    if t >= HOOK_END + 0.15: return
    a = 1 - clamp((t - HOOK_END) / 0.15)
    s = lerp(1.0, 1.04, clamp(t / HOOK_END))
    fn = f(DMB, int(78 * s)); d = ImageDraw.Draw(im, 'RGBA')
    l1 = HOOK[0][0]; l2a = HOOK[0][1]; l2b = HOOK[1]
    w1 = d.textlength(l1, font=fn); w2 = d.textlength(l2a, font=fn) + d.textlength(l2b, font=fn)
    bw = max(w1, w2) + 70; lh = int(96 * s); y = 300 - (s - 1) * 60
    bx0 = (W - bw) / 2
    frosted(im, (bx0, y - 26, bx0 + bw, y + 2 * lh + 26), 0.80, 16); d = ImageDraw.Draw(im, 'RGBA')
    d.rectangle([bx0, y - 26, bx0 + bw, y + 2 * lh + 26], fill=A(NAVY, 0.35 * a))
    d.rectangle([bx0, y - 26, bx0 + 8, y + 2 * lh + 26], fill=A(GOLD, a))
    d.text(((W - w1) / 2, y), l1, font=fn, fill=A(WHITE, a))
    x = (W - w2) / 2; d.text((x, y + lh), l2a, font=fn, fill=A(WHITE, a)); x += d.textlength(l2a, font=fn)
    d.text((x, y + lh), l2b, font=fn, fill=A(VGOLD, a))
    if GL: GL.text((x, y + lh), l2b, font=fn, fill=A(VGOLD, 0.6 * a))
def topic_band(im, t):
    if not (HOOK_END <= t < BAND_END + 0.15): return
    a = clamp((t - HOOK_END) / 0.15) * (1 - clamp((t - BAND_END) / 0.15))
    d = ImageDraw.Draw(im, 'RGBA')
    d.rectangle([8, 212, W, 352], fill=A(NAVY, 0.88 * a))
    d.line([(64, 240), (108, 240)], fill=A(GOLD, a), width=4); txt(d, 122, 224, '@coach.agz', f(MONO, 28), GOLD, a)
    fn = f(DMB, 54); s1 = 'Real expectations on '; txt(d, 64, 268, s1, fn, WHITE, a); txt(d, 64 + d.textlength(s1, font=fn), 268, 'STEROIDS', fn, VGOLD, a)

# ---------------- captions ----------------
FIX = {'antibiotic': 'ANABOLIC', 'gotta': 'GOTTA'}
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
