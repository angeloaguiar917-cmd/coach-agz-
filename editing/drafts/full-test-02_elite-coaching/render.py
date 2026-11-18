# @coach.agz "Elite coaching" Reel — 1080x1920 renderer
# usage: python3 render.py <workdir> <n0> <n1> <out.mp4>
import json, subprocess, sys, math
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
S = sys.argv[1]; F = S + '/fonts/'
W, H = 1080, 1920; FPS = 30
WORDS = json.load(open(S + '/words_cut.json'))
CUTS = json.load(open(S + '/cut_points.json'))          # jump-cut times in the cut timeline
DUR = json.load(open(S + '/cut_meta.json'))['dur']
FACE_BOXES = json.load(open(S + '/face_y.json')) if False else None

# ---------- palette (BRAND.md overlay accent palette, test-06) ----------
GOLD = (201, 169, 110); CREAM = (244, 241, 234); NAVY = (14, 17, 23)
RED = (255, 34, 28); VGOLD = (255, 194, 26); CYAN = (0, 229, 255); GREEN = (30, 255, 110)
AMBER = (240, 160, 48); BLUE = (79, 163, 224)
DEEP = (2, 3, 8); INK = (6, 8, 14); WHITE = (255, 255, 255); MUTED = (124, 124, 130); GRID = (52, 56, 72)
MONO = 'JBMono-500.ttf'; MONOB = 'JBMono-700.ttf'; BEB = 'BebasNeue.ttf'; DMB = 'DMSans-700.ttf'; DMR = 'DMSans-400.ttf'
BAR6 = 'Barlow-600.ttf'; BAR8 = 'Barlow-800.ttf'
_fc = {}
def f(n, s):
    k = (n, int(s))
    if k not in _fc: _fc[k] = ImageFont.truetype(F + n, int(s))
    return _fc[k]
def clamp(x, a=0, b=1): return max(a, min(b, x))
def expo(x): x = clamp(x); return 1 if x >= 1 else 1 - 2 ** (-10 * x)
def ease_io(x): x = clamp(x); return 4 * x ** 3 if x < .5 else 1 - (-2 * x + 2) ** 3 / 2
def back(x, s=1.4): x = clamp(x); return 1 + (s + 1) * (x - 1) ** 3 + s * (x - 1) ** 2   # used only for heavy blocks, small overshoot
def lerp(a, b, t): return a + (b - a) * t
def A(c, a): return tuple(c[:3]) + (int(clamp(a) * 255),)
def appear(t, t0, dur=0.16): return expo((t - t0) / dur)

# ---------- word lookup ----------
def K(word, n=0, after=0.0, end=False):
    """start (or end) time of the n-th occurrence of `word` (lowercase, stripped) at/after `after`"""
    c = 0
    for x in WORDS:
        if x['s'] + 1e-6 < after: continue
        if x['w'].lower().strip('.,?!"\'') == word:
            if c == n: return x['e'] if end else x['s']
            c += 1
    raise KeyError(word)

GL = None   # glow layer draw
def glow_line(pts, col, a, w):
    if GL: GL.line(pts, fill=A(col, a), width=w)

# ---------- primitives ----------
def brackets(d, x0, y0, x1, y1, col, L=30, w=5):
    for (cx, cy, sx, sy) in [(x0, y0, 1, 1), (x1, y0, -1, 1), (x0, y1, 1, -1), (x1, y1, -1, -1)]:
        d.line([(cx, cy), (cx + sx * L, cy)], fill=col, width=w); d.line([(cx, cy), (cx, cy + sy * L)], fill=col, width=w)
def lit_bar(d, x0, y0, x1, y1, col, a=1.0):
    h = max(1, int(y1 - y0))
    if x1 <= x0: return
    for i in range(h):
        k = i / h; c = tuple(int(min(255, v * (1.18 - 0.36 * k) + (40 if k < 0.12 else 0))) for v in col)
        d.line([(x0, y0 + i), (x1, y0 + i)], fill=c + (int(255 * clamp(a)),))
def tag(d, x, y, label, col=RED, size=30, a=1.0, glow=True, fg=None):
    fn = f(MONOB, size); tw = d.textlength(label, font=fn); h = size + 16
    lit_bar(d, x, y, x + tw + 24, y + h, col, a)
    d.text((x + 12, y + 6), label, font=fn, fill=A(fg or (INK if col in (VGOLD, GREEN, CYAN) else WHITE), a))
    if GL and glow: GL.rectangle([x - 4, y - 4, x + tw + 28, y + h + 4], outline=A(col, a), width=8)
    return x + tw + 24
def txt(d, x, y, s, font, col, a=1.0, anchor=None):
    d.text((x, y), s, font=font, fill=A(col, a), anchor=anchor)
def check(d, x, y, col, s=1.0, a=1.0):
    pts = [(x, y + 16 * s), (x + 10 * s, y + 28 * s), (x + 30 * s, y + 2 * s)]
    d.line(pts, fill=A(col, a), width=int(6 * s)); glow_line(pts, col, a, int(12 * s))
def cross(d, x, y, col, s=1.0, a=1.0):
    for p in ([(x, y), (x + 28 * s, y + 28 * s)], [(x + 28 * s, y), (x, y + 28 * s)]):
        d.line(p, fill=A(col, a), width=int(6 * s)); glow_line(p, col, a, int(12 * s))
def frosted(im, box, dark=0.84, blur=14, radius=22):
    x0, y0, x1, y1 = [int(v) for v in box]
    x0 = max(0, x0); y0 = max(0, y0); x1 = min(W, x1); y1 = min(H, y1)
    if x1 <= x0 or y1 <= y0: return
    reg = im.crop((x0, y0, x1, y1)).convert('RGB').filter(ImageFilter.GaussianBlur(blur))
    reg = Image.blend(reg, Image.new('RGB', reg.size, DEEP), dark).convert('RGBA')
    m = Image.new('L', reg.size, 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, reg.width - 1, reg.height - 1], radius=radius, fill=255)
    im.paste(reg, (x0, y0), m)
def panel(im, box, t0, t1, t, col=VGOLD, kicker=None, kick_r=None, rise=40, accent='bar'):
    sh = LOWSHIFT if box[1] > 1000 else 0
    box = (box[0], box[1] + sh, box[2], box[3] + sh)
    """glass panel: rises with blur and settles; accent bar leads by a few frames. returns (alpha, draw, offset y) or None"""
    pin = expo((t - t0) / 0.24); pout = clamp((t - t1) / 0.16)
    if pin <= 0 or pout >= 1: return None
    a = pin * (1 - pout)
    dy = lerp(rise, 0, pin) - 20 * pout
    x0, y0, x1, y1 = box; y0 += dy; y1 += dy
    frosted(im, (x0, y0, x1, y1), 0.84 * a + 0.0, 14)
    d = ImageDraw.Draw(im, 'RGBA')
    d.rounded_rectangle([x0, y0, x1, y1], radius=22, outline=A(col, 0.55 * a), width=2)
    bar = expo((t - t0 + 0.06) / 0.18) * (1 - pout)
    d.rounded_rectangle([x0, y0 + 18, x0 + 7, lerp(y0 + 18, y1 - 18, bar)], radius=3, fill=A(col, bar))
    if GL: GL.rectangle([x0 - 2, y0 + 18, x0 + 9, lerp(y0 + 18, y1 - 18, bar)], fill=A(col, bar))
    if kicker:
        kp = appear(t, t0 + 0.08, 0.2)
        d.line([(x0 + 30, y0 + 36), (x0 + 30 + 40 * kp, y0 + 36)], fill=A(col, a), width=3)
        txt(d, x0 + 82, y0 + 20, kicker[:max(0, int(len(kicker) * clamp((t - t0 - 0.1) / 0.25)))], f(MONOB, 28), col, a)
    if kick_r:
        fn = f(MONO, 26); tw = d.textlength(kick_r, font=fn); txt(d, x1 - 28 - tw, y0 + 22, kick_r, fn, MUTED, a)
    return a, d, dy + sh

# ======================= SCENES =======================
LOWSHIFT = -112
SC = []   # (t_in, t_out, fn, zone)  zone: 'top' | 'low' | 'split' | 'pip' | 'none'

# ---- B. CHECK-IN TRACKER (calendar strip + ECG) ----
def sc_tracker(im, t, T0, T1, tw_, td, tbp, tcc):
    r = panel(im, (40, 250, 1040, 640), T0, T1, t, VGOLD, 'CLIENT TRACKER', 'WEEK 06')
    if not r: return
    a, d, dy = r
    days = ['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT', 'SUN']
    cw = 128; x0 = 82; y0 = 318 + dy
    for i, dn in enumerate(days):
        cx = x0 + i * (cw + 4)
        d.rounded_rectangle([cx, y0, cx + cw, y0 + 170], radius=10, fill=A((16, 19, 28), a), outline=A(GRID, a), width=2)
        txt(d, cx + 12, y0 + 10, dn, f(MONO, 24), MUTED, a)
        # daily check-in dot ticks across
        if t >= td + i * 0.07:
            q = appear(t, td + i * 0.07, 0.1) * a
            d.ellipse([cx + cw - 34, y0 + 14, cx + cw - 14, y0 + 34], fill=A(CYAN, q))
            if GL: GL.ellipse([cx + cw - 40, y0 + 8, cx + cw - 8, y0 + 40], fill=A(CYAN, q * 0.8))
    # weekly check-in stamp lands on Monday (heavy)
    if t >= tw_:
        p = expo((t - tw_) / 0.14); s = lerp(1.35, 1.0, p); q = p * a
        cx = x0; fn = f(BEB, int(40 * s)); lab = 'CHECK-IN'
        bw = d.textlength(lab, font=fn) + 16
        lit_bar(d, cx + cw / 2 - bw / 2, y0 + 52, cx + cw / 2 + bw / 2, y0 + 52 + 44 * s, VGOLD, q)
        txt(d, cx + cw / 2 - bw / 2 + 8, y0 + 54, lab, fn, INK, q)
    # BP ECG line across the week
    if t >= tbp:
        pr = clamp((t - tbp) / 1.2)
        xs = np.linspace(x0 + 6, x0 + 7 * (cw + 4) - 10, 260)
        pts = []
        for k, xv in enumerate(xs[:max(2, int(len(xs) * pr))]):
            ph = (k % 37) / 37
            yv = y0 + 128
            if 0.42 < ph < 0.47: yv -= 46
            elif 0.47 <= ph < 0.52: yv += 22
            elif 0.30 < ph < 0.36: yv -= 8
            pts.append((xv, yv))
        d.line(pts, fill=A(RED, a), width=4); glow_line(pts, RED, a, 9)
        if pr > 0.05: txt(d, x0 + 4, y0 + 176, 'BP DAILY', f(MONOB, 26), RED, a * appear(t, tbp + 0.2))
        if pr > 0.3: txt(d, x0 + 190, y0 + 176, '124/78', f(MONO, 26), CREAM, a * appear(t, tbp + 0.5))
    if t >= tcc:
        q = appear(t, tcc, 0.14) * a
        n = int(lerp(0, 41, clamp((t - tcc) / 1.0)))
        x = tag(d, 640, y0 + 172, f'MSGS THIS WEEK  {n:02d}', CYAN, 26, q)

# ---- C. DAILY CHECK-IN FORM (lower third, sliders) ----
def sc_form(im, t, T0, T1, tf, ts, te):
    r = panel(im, (60, 1360, 1020, 1660), T0, T1, t, CYAN, 'DAILY CHECK-IN', 'FORM 7/7')
    if not r: return
    a, d, dy = r
    rows = [('HOW YOU FEEL', tf, 0.78, GREEN), ('SLEEP', ts, 0.52, AMBER), ('NUTRITION', te, 0.86, GREEN)]
    for i, (lab, tt, v, col) in enumerate(rows):
        y = 1428 + dy + i * 72
        q = appear(t, tt - 0.05, 0.14) * a
        txt(d, 100, y, lab, f(MONOB, 28), CREAM, max(0.3 * a, q))
        x0, x1 = 400, 980
        d.line([(x0, y + 20), (x1, y + 20)], fill=A(GRID, a), width=6)
        p = lerp(0.12, v, expo((t - tt) / 0.45)) if t >= tt else 0.12
        xm = lerp(x0, x1, p)
        if t >= tt:
            lit_bar(d, x0, y + 16, xm, y + 25, col, q)
            d.ellipse([xm - 14, y + 6, xm + 14, y + 34], fill=A(WHITE, q), outline=A(col, q), width=4)
            if GL: GL.ellipse([xm - 18, y + 2, xm + 18, y + 38], outline=A(col, q), width=8)

# ---- D. HER vs THE COMPOUND (forensic lock) ----
def sc_suspect(im, t, T0, T1, ther, tcomp):
    r = panel(im, (40, 250, 1040, 600), T0, T1, t, RED, 'MOOD SHIFT · CAUSE?', 'INCIDENT 01')
    if not r: return
    a, d, dy = r
    y0 = 320 + dy
    for i, (lab, sub) in enumerate([('HER', 'PARTNER'), ('THE COMPOUND', 'E2 · ANDROGEN LOAD')]):
        x0 = 80 + i * 470; x1 = x0 + 440
        q = appear(t, T0 + 0.2 + i * 0.12) * a
        dim = (i == 0 and t >= tcomp + 0.3)
        d.rounded_rectangle([x0, y0, x1, y0 + 200], radius=14, fill=A((16, 19, 28), q), outline=A(GRID, q), width=2)
        txt(d, x0 + 24, y0 + 30, lab, f(BEB, 84), (110, 110, 118) if dim else WHITE, q)
        txt(d, x0 + 26, y0 + 128, sub, f(MONO, 26), MUTED if i == 0 else CYAN, q)
        if not dim and t < tcomp:
            txt(d, x1 - 70, y0 + 30, '?', f(BEB, 84), VGOLD, q * (0.6 + 0.4 * math.sin(t * 9)))
    if t >= ther and t < tcomp:   # scanning bracket hovers on HER
        q = appear(t, ther) * a; brackets(d, 70, y0 - 10, 530, y0 + 210, A(VGOLD, q), 30, 5)
    if t >= tcomp:   # lock on the compound
        p = expo((t - tcomp) / 0.14); q = p * a
        bx0 = lerp(70, 540, p); bx1 = lerp(530, 1000, p)
        brackets(d, bx0, y0 - 10, bx1, y0 + 210, A(RED, q), 34, 7)
        if GL: brackets(GL, bx0, y0 - 10, bx1, y0 + 210, A(RED, q), 34, 12)
        if p > 0.6: tag(d, 560, y0 + 220, 'LIKELY CAUSE', RED, 28, a * appear(t, tcomp + 0.12))
        if t > tcomp + 0.35: tag(d, 80, y0 + 220, 'CHECK THE DATA', VGOLD, 28, a * appear(t, tcomp + 0.35))

# ---- E. RADAR — everything is a data point ----
def sc_radar(im, t, T0, T1, axes_t, tdata):
    r = panel(im, (40, 1330, 1040, 1700), T0, T1, t, VGOLD, 'DATA POINTS · TRACKED', None)
    if not r: return
    a, d, dy = r
    cx, cy, R = 300, 1530 + dy, 128
    labs = ['MOOD', 'SLEEP', 'COGNITION', 'FOCUS', 'RELATIONSHIPS']
    vals = [0.82, 0.64, 0.76, 0.88, 0.70]
    n = 5
    ang = [-math.pi / 2 + 2 * math.pi * i / n for i in range(n)]
    for ring in (0.33, 0.66, 1.0):
        pts = [(cx + R * ring * math.cos(g), cy + R * ring * math.sin(g)) for g in ang]
        d.line(pts + [pts[0]], fill=A(GRID, a), width=2)
    shown = [i for i in range(n) if t >= axes_t[i]]
    for i in range(n):
        q = appear(t, axes_t[i], 0.12) * a if i in shown else 0.25 * a
        d.line([(cx, cy), (cx + R * math.cos(ang[i]), cy + R * math.sin(ang[i]))], fill=A(GRID if i not in shown else VGOLD, q), width=2)
    # polygon grows vertex by vertex
    pv = []
    for i in range(n):
        g = expo((t - axes_t[i]) / 0.3) if t >= axes_t[i] else 0
        pv.append((cx + R * vals[i] * g * math.cos(ang[i]), cy + R * vals[i] * g * math.sin(ang[i])))
    if shown:
        poly = Image.new('RGBA', (W, H), (0, 0, 0, 0)); pd = ImageDraw.Draw(poly)
        pd.polygon(pv, fill=A(VGOLD, 0.28 * a)); im.alpha_composite(poly); d = ImageDraw.Draw(im, 'RGBA')
        d.line(pv + [pv[0]], fill=A(VGOLD, a), width=4); glow_line(pv + [pv[0]], VGOLD, a, 8)
        for i in shown:
            d.ellipse([pv[i][0] - 7, pv[i][1] - 7, pv[i][0] + 7, pv[i][1] + 7], fill=A(WHITE, a))
    # legend list on right with live values
    for i, lab in enumerate(labs):
        y = 1402 + dy + i * 52
        if t >= axes_t[i]:
            q = appear(t, axes_t[i], 0.12) * a
            d.ellipse([500, y + 10, 516, y + 26], fill=A(VGOLD, q))
            txt(d, 530, y, lab, f(BAR8, 40), WHITE, q)
            v = int(vals[i] * 100 * expo((t - axes_t[i]) / 0.4))
            txt(d, 960, y, f'{v}', f(MONOB, 34), VGOLD, q, anchor='ra')
    if t >= tdata: tag(d, 80, 1648 + dy - 4, 'TRACKED WEEKLY', GREEN, 24, a * appear(t, tdata))

# ---- F. OPTIMAL vs REFERENCE RANGE ----
def sc_range(im, t, T0, T1, topt, tref, tsick):
    r = panel(im, (40, 250, 1040, 620), T0, T1, t, VGOLD, 'YOUR MARKER', 'TOTAL T · ng/dL')
    if not r: return
    a, d, dy = r
    x0, x1 = 90, 990; y = 400 + dy
    lo, hi = 0, 1300
    X = lambda v: lerp(x0, x1, (v - lo) / (hi - lo))
    # axis
    d.line([(x0, y + 60), (x1, y + 60)], fill=A(GRID, a), width=3)
    for v in (0, 250, 500, 750, 1000, 1250):
        d.line([(X(v), y + 54), (X(v), y + 66)], fill=A(MUTED, a), width=2)
        txt(d, X(v), y + 72, str(v), f(MONO, 22), MUTED, a, anchor='ma')
    # reference range (wide, grey) — draws on
    if t >= tref:
        p = expo((t - tref) / 0.5); q = a * appear(t, tref)
        ra, rb = X(264), lerp(X(264), X(916), p)
        d.rounded_rectangle([ra, y + 4, rb, y + 50], radius=8, fill=A((70, 74, 88), q))
        txt(d, ra + 10, y + 10, 'LAB REFERENCE 264–916', f(MONOB, 24), WHITE, q)
    if t >= tsick:
        tag(d, X(264), y - 52, 'BUILT FOR SICK + SEDENTARY', RED, 26, a * appear(t, tsick))
    if t >= topt:
        p = expo((t - topt) / 0.35); q = a * appear(t, topt)
        oa, ob = X(800), X(1100)
        yo = y + 112
        lit_bar(d, oa, yo, lerp(oa, ob, p), yo + 46, VGOLD, q)
        if GL: GL.rectangle([oa, yo, lerp(oa, ob, p), yo + 46], outline=A(VGOLD, q), width=8)
        txt(d, oa - 12, yo + 8, 'OPTIMAL', f(MONOB, 26), VGOLD, q, anchor='ra')
        # marker slides into optimal
        mv = lerp(420, 960, expo((t - topt - 0.3) / 0.7))
        mx = X(mv)
        d.polygon([(mx - 14, y - 4), (mx + 14, y - 4), (mx, y + 20)], fill=A(WHITE, q))
        d.line([(mx, y + 20), (mx, yo + 46)], fill=A(WHITE, q * 0.7), width=2)
        if t > topt + 1.0: txt(d, mx, y - 40, f'{int(mv)}', f(BEB, 40), WHITE, q, anchor='ma') if t < tsick else None

# ---- G. THREE RESPONSE GAUGES (lower third) ----
def gauge(d, cx, cy, R, v, col, lab, a, t0, t):
    d.arc([cx - R, cy - R, cx + R, cy + R], 180, 360, fill=A(GRID, a), width=16)
    p = expo((t - t0) / 0.6) if t >= t0 else 0
    if p > 0:
        d.arc([cx - R, cy - R, cx + R, cy + R], 180, 180 + 180 * v * p, fill=A(col, a), width=16)
        if GL: GL.arc([cx - R, cy - R, cx + R, cy + R], 180, 180 + 180 * v * p, fill=A(col, a), width=24)
    g = math.pi + math.pi * v * p
    d.line([(cx, cy), (cx + (R - 26) * math.cos(g), cy + (R - 26) * math.sin(g))], fill=A(WHITE, a), width=5)
    d.ellipse([cx - 9, cy - 9, cx + 9, cy + 9], fill=A(WHITE, a))
    txt(d, cx, cy + 16, lab, f(MONOB, 24), WHITE if p > 0 else MUTED, a, anchor='ma')
def sc_gauges(im, t, T0, T1, ts, tg, tc):
    r = panel(im, (40, 1360, 1040, 1660), T0, T1, t, CYAN, 'RESPONSE ANALYSIS', 'PER CLIENT')
    if not r: return
    a, d, dy = r
    for i, (lab, v, col, tt) in enumerate([('SIDE EFFECTS', 0.28, GREEN, ts), ('GROWTH', 0.81, VGOLD, tg), ('COMPOUND', 0.64, CYAN, tc)]):
        gauge(d, 210 + i * 330, 1560 + dy, 120, v, col, lab, a, tt, t)

# ---- H. DIAL-IN MIXER (faders) ----
def sc_mixer(im, t, T0, T1, tdial, trx, tanc, tyou):
    r = panel(im, (40, 250, 1040, 640), T0, T1, t, VGOLD, 'PROTOCOL · DIAL-IN', 'BUILT AROUND YOU')
    if not r: return
    a, d, dy = r
    chans = [('RX', 0.62, trx), ('ANCILLARY', 0.35, tanc), ('ANCILLARY', 0.22, tanc + 0.2), ('SUPPORT', 0.48, tanc + 0.4)]
    for i, (lab, v, tt) in enumerate(chans):
        cx = 150 + i * 230; yt, yb = 320 + dy, 540 + dy
        d.line([(cx, yt), (cx, yb)], fill=A(GRID, a), width=8)
        for k in range(6): d.line([(cx - 24, lerp(yt, yb, k / 5)), (cx - 12, lerp(yt, yb, k / 5))], fill=A(MUTED, a * 0.6), width=2)
        # fader wobbles while dialling then settles on value
        if t < tdial: pos = 0.5
        else:
            e = clamp((t - max(tdial, tt)) / 0.7) if t >= tt else 0
            wob = 0.25 * math.sin((t - tdial) * 7 + i * 1.7) * (1 - e)
            pos = lerp(0.5 + wob, v, expo(e)) if t >= tt else 0.5 + 0.25 * math.sin((t - tdial) * 7 + i * 1.7)
        yk = lerp(yb, yt, pos)
        lit_bar(d, cx - 4, yk, cx + 4, yb, VGOLD if t >= tt else MUTED, a)
        d.rounded_rectangle([cx - 34, yk - 16, cx + 34, yk + 16], radius=6, fill=A((30, 33, 44), a), outline=A(WHITE, a), width=3)
        d.line([(cx - 22, yk), (cx + 22, yk)], fill=A(VGOLD, a), width=3)
        txt(d, cx, yb + 14, lab, f(MONOB, 22), WHITE if t >= tt else MUTED, a, anchor='ma')
        if t >= tt + 0.7: check(d, cx + 44, yk - 14, GREEN, 0.7, a * appear(t, tt + 0.7))
    if t >= tyou: tag(d, 700, 268 + dy + 330, 'LOCKED TO YOU', GREEN, 24, a * appear(t, tyou)) if False else tag(d, 760, 590 + dy, 'FITTED TO YOU', GREEN, 24, a * appear(t, tyou))

# ---- I. PIP: WHAT TO EXPECT ON BLOODS (annotated line chart, full graphic with face window) ----
def sc_pip_chart(d, t, T0, T1, tsci, texp, tadd, tsimp, tlife, a):
    # chart area below the face window
    x0, y0, x1, y1 = 110, 1150, 990, 1520
    txt(d, 70, 1080, 'HEMATOCRIT · WHAT TO EXPECT', f(MONOB, 30), VGOLD, a)
    txt(d, 1010, 1084, 'EDUCATION', f(MONO, 24), MUTED, a, anchor='ra')
    for k in range(5):
        yy = lerp(y0, y1, k / 4); d.line([(x0, yy), (x1, yy)], fill=A(GRID, a), width=1)
        txt(d, x0 - 14, yy - 12, f'{54 - k * 3}%', f(MONO, 20), MUTED, a, anchor='ra')
    for k, wk in enumerate(['WK0', 'WK4', 'WK8', 'WK12', 'WK16']):
        txt(d, lerp(x0, x1, k / 4), y1 + 10, wk, f(MONO, 20), MUTED, a, anchor='ma')
    Y = lambda v: lerp(y1, y0, (v - 42) / 12)
    xadd = lerp(x0, x1, 0.25)
    # expected band (after compound added)
    if t >= texp:
        q = appear(t, texp, 0.3) * a
        band = Image.new('RGBA', (W, H), (0, 0, 0, 0)); bd = ImageDraw.Draw(band)
        top = [(lerp(xadd, x1, k / 20), Y(lerp(46, 51.5, 1 - (1 - k / 20) ** 2))) for k in range(21)]
        bot = [(lerp(xadd, x1, k / 20), Y(lerp(44.5, 48.5, 1 - (1 - k / 20) ** 2))) for k in range(21)]
        bd.polygon(top + bot[::-1], fill=A(CYAN, 0.22 * q)); band_im = band
        return_band = band_im
    else: return_band = None
    # compound added marker
    if t >= tadd:
        q = appear(t, tadd) * a
        for yy in range(int(y0), int(y1), 18): d.line([(xadd, yy), (xadd, yy + 9)], fill=A(VGOLD, q), width=3)
        tag(d, xadd + 10, y0 + 6, '+ COMPOUND', VGOLD, 22, q)
    # actual line
    vals = [45.0, 45.2, 44.8, 46.1, 47.4, 48.3, 48.9, 49.6, 49.9]
    pr = clamp((t - tsci) / 3.0) * (len(vals) - 1)
    pts = [(lerp(x0, x1, i / (len(vals) - 1)), Y(v)) for i, v in enumerate(vals)]
    for i in range(len(vals) - 1):
        if pr > i:
            q = min(1, pr - i); e = (lerp(pts[i][0], pts[i + 1][0], q), lerp(pts[i][1], pts[i + 1][1], q))
            d.line([pts[i], e], fill=A(WHITE, a), width=5); glow_line([pts[i], e], CYAN, a, 10)
    for i, p_ in enumerate(pts):
        if pr >= i: d.ellipse([p_[0] - 8, p_[1] - 8, p_[0] + 8, p_[1] + 8], fill=A(CYAN, a))
    if t >= tsimp: tag(d, 640, y1 - 70, 'INSIDE EXPECTED', GREEN, 24, a * appear(t, tsimp))
    return return_band

# ---- J. SIMPLIFY: tangle → clean line (lower third) ----
def sc_simplify(im, t, T0, T1, tsimp, tund):
    r = panel(im, (60, 1380, 1020, 1640), T0, T1, t, CYAN, 'THE SCIENCE · SIMPLIFIED', None)
    if not r: return
    a, d, dy = r
    m = expo((t - tsimp) / 0.8) if t >= tsimp else 0
    pts = []
    for k in range(240):
        u = k / 239; x = lerp(110, 960, u)
        noise = 70 * math.sin(u * 31 + 1.3) * math.cos(u * 13) + 40 * math.sin(u * 57)
        loop = 55 * math.sin(u * 23)
        x += (1 - m) * 60 * math.cos(u * 37)
        y = 1530 + dy + (1 - m) * (noise + loop * 0.4)
        pts.append((x, y))
    col = (lerp(MUTED[0], CYAN[0], m), lerp(MUTED[1], CYAN[1], m), lerp(MUTED[2], CYAN[2], m))
    col = tuple(int(c) for c in col)
    d.line(pts, fill=A(col, a), width=4); glow_line(pts, col, a * m, 9)
    if m > 0.9:
        d.polygon([(960, 1516 + dy), (990, 1530 + dy), (960, 1544 + dy)], fill=A(CYAN, a))
    txt(d, 110, 1446 + dy, 'TEXTBOOK', f(MONO, 24), MUTED, a * (1 - m * 0.6))
    if t >= tund: tag(d, 700, 1580 + dy, 'YOU UNDERSTAND IT', GREEN, 24, a * appear(t, tund))

# ---- K. PUSH-UP SPLIT: TWO-SECTION REPORT ----
def sc_docs(d, t, tsum, tdeep, tedu, texp, a, dy):
    # left: summary dashboard page
    y0 = 1150 + dy
    for i, (x0, ti, title) in enumerate([(50, tsum, 'SUMMARY DASHBOARD'), (560, tdeep, 'IN-DEPTH ANALYSIS')]):
        if t < ti: continue
        p = expo((t - ti) / 0.3); q = p * a; yy = y0 + lerp(80, 0, p)
        d.rounded_rectangle([x0, yy, x0 + 470, yy + 380], radius=16, fill=A((238, 236, 230), q))
        d.rectangle([x0, yy, x0 + 470, yy + 56], fill=A((16, 24, 48), q))
        d.rounded_rectangle([x0, yy, x0 + 470, yy + 30], radius=16, fill=A((16, 24, 48), q))
        txt(d, x0 + 18, yy + 12, f'0{i + 1} · {title}', f(MONOB, 24), WHITE, q)
        if i == 0:
            tiles = [('LIPIDS', GREEN, 'OK'), ('HCT', AMBER, 'WATCH'), ('E2', GREEN, 'OK'), ('LIVER', GREEN, 'OK'), ('BP', AMBER, 'WATCH'), ('KIDNEY', GREEN, 'OK')]
            for k, (nm, c, st) in enumerate(tiles):
                tt = ti + 0.1 + k * 0.08
                if t < tt: continue
                qq = q * appear(t, tt, 0.1); tx = x0 + 18 + (k % 2) * 222; ty = yy + 74 + (k // 2) * 98
                d.rounded_rectangle([tx, ty, tx + 210, ty + 86], radius=10, fill=A(WHITE, qq), outline=A((210, 210, 214), qq), width=2)
                d.ellipse([tx + 14, ty + 16, tx + 34, ty + 36], fill=A(c, qq))
                txt(d, tx + 44, ty + 10, nm, f(BAR8, 34), INK, qq)
                txt(d, tx + 16, ty + 50, st, f(MONOB, 22), (40, 120, 60) if c == GREEN else (180, 100, 0), qq)
        else:
            # dense analysis: text lines + mini chart + mechanism arrows
            for k in range(9):
                tt = ti + 0.15 + k * 0.07
                if t < tt: continue
                qq = q * appear(t, tt, 0.08); ly = yy + 76 + k * 22
                wl = [400, 360, 420, 300, 410, 380, 220, 390, 340][k]
                d.rounded_rectangle([x0 + 20, ly, x0 + 20 + wl, ly + 9], radius=4, fill=A((150, 150, 158), qq))
            if t >= tedu:
                qq = q * appear(t, tedu)
                cx0, cy0 = x0 + 20, yy + 290
                d.rectangle([cx0, cy0 - 70, cx0 + 200, cy0 + 60], outline=A((180, 180, 186), qq), width=2)
                pts = [(cx0 + 10 + k * 22, cy0 + 40 - 90 * (0.5 + 0.4 * math.sin(k * 0.8)) * (k / 8)) for k in range(9)]
                d.line(pts, fill=A((0, 140, 170), qq), width=4)
                txt(d, cx0 + 220, cy0 - 64, 'SCIENCE', f(MONOB, 22), INK, qq)
                txt(d, cx0 + 220, cy0 - 34, 'MECHANISM', f(MONOB, 22), INK, qq)
                txt(d, cx0 + 220, cy0 - 4, 'WHAT TO', f(MONOB, 22), (180, 20, 30), qq)
                txt(d, cx0 + 220, cy0 + 22, 'EXPECT', f(MONOB, 22), (180, 20, 30), qq)
    if t >= texp: tag(d, 560, y0 + 392, 'ANY COMPOUND', VGOLD, 24, a * appear(t, texp))

# ---- L. LEADER: lifespan timeline (lower third) ----
def sc_life(im, t, T0, T1, tlead, topt, tkids, twife, trest):
    r = panel(im, (40, 1350, 1040, 1660), T0, T1, t, VGOLD, 'THE LONG GAME', None)
    if not r: return
    a, d, dy = r
    x0, x1, y = 100, 980, 1520 + dy
    pr = expo((t - trest) / 1.2) if t >= trest else lerp(0, 0.32, expo((t - T0) / 0.6))
    d.line([(x0, y), (x1, y)], fill=A(GRID, a), width=6)
    lit_bar(d, x0, y - 3, lerp(x0, x1, pr), y + 4, VGOLD, a)
    if GL: GL.line([(x0, y), (lerp(x0, x1, pr), y)], fill=A(VGOLD, a), width=10)
    for k, lab in enumerate(['NOW', '+10 YRS', '+20 YRS', '+30 YRS', 'FOR LIFE']):
        xx = lerp(x0, x1, k / 4); on = pr >= k / 4 - 0.01
        d.ellipse([xx - 10, y - 10, xx + 10, y + 10], fill=A(VGOLD if on else GRID, a))
        txt(d, xx, y + 22, lab, f(MONOB, 22), WHITE if on else MUTED, a, anchor='ma')
    chips = [('LEADER OF THE HOUSE', tlead, 80), ('OPTIMAL', topt, 0), ('KIDS', tkids, 0), ('WIFE', twife, 0)]
    x = 80
    for lab, tt, _ in chips:
        if t >= tt:
            q = appear(t, tt) * a
            fn = f(BAR8, 34); tw = d.textlength(lab, font=fn)
            d.rounded_rectangle([x, 1410 + dy, x + tw + 32, 1462 + dy], radius=8, fill=A((40, 12, 18) if False else (36, 30, 12), q), outline=A(VGOLD, q), width=2)
            txt(d, x + 16, 1414 + dy, lab, fn, VGOLD, q)
            x += tw + 46

# ---- M. VERDICT + CTA ----
LOGO = None
def sc_cta(im, t, tcom, telite, tprof, tproto):
    global LOGO
    if t < tcom - 0.2: return
    r = panel(im, (40, 1250, 1040, 1660), tcom - 0.2, 1e9, t, VGOLD, 'ELITE COACHING', '@coach.agz')
    if not r: return
    a, d, dy = r
    if LOGO is None:
        lg = Image.open(S + '/logo.jpg').convert('RGB'); s = min(lg.size)
        lg = lg.crop(((lg.width - s) // 2, (lg.height - s) // 2, (lg.width + s) // 2, (lg.height + s) // 2)).resize((150, 150), Image.LANCZOS)
        m = Image.new('L', (150, 150), 0); ImageDraw.Draw(m).ellipse([0, 0, 149, 149], fill=255); lg.putalpha(m); LOGO = lg
    lg = LOGO.copy(); lg.putalpha(lg.split()[3].point(lambda v: int(v * a))); im.alpha_composite(lg, (80, int(1320 + dy)))
    d = ImageDraw.Draw(im, 'RGBA')
    if t >= telite:
        b = expo((t - telite) / 0.12); s = lerp(1.15, 1.0, b)
        fn = f(BEB, int(96 * s)); label = 'COMMENT "ELITE"'; tw = d.textlength(label, font=fn)
        lit_bar(d, 260, 1330 + dy, 260 + tw + 44, 1330 + dy + int(104 * s), VGOLD, b * a)
        if GL: GL.rectangle([256, 1326 + dy, 264 + tw + 44, 1334 + dy + int(104 * s)], outline=A(VGOLD, b * a), width=12)
        txt(d, 282, 1334 + dy, label, fn, INK, b * a)
    # coached vs protocol
    y = 1500 + dy
    if t >= tprof:
        q = appear(t, tprof) * a
        check(d, 84, y + 6, GREEN, 1.1, q); txt(d, 134, y - 4, 'COACHED LIKE A PRO', f(BAR8, 46), WHITE, q)
    if t >= tproto:
        q = appear(t, tproto) * a
        cross(d, 600, y + 8, RED, 1.0, q); fn = f(BAR8, 46); txt(d, 646, y - 4, 'JUST A PROTOCOL', fn, MUTED, q)
        tw = d.textlength('JUST A PROTOCOL', font=fn); p = expo((t - tproto - 0.15) / 0.2)
        d.line([(640, y + 26), (640 + (tw + 12) * p, y + 26)], fill=A(RED, q), width=6); glow_line([(640, y + 26), (640 + (tw + 12) * p, y + 26)], RED, q, 10)

# ======================= TEXT HOOK + TOPIC BAND =======================
BUSY_LOW = [False]
HOOK = json.load(open(S + '/hook.json'))
def hook(im, t):
    th = HOOK['text_hook']
    if t >= th['end'] + 0.15: return
    a = 1 - clamp((t - th['end']) / 0.15)
    d = ImageDraw.Draw(im, 'RGBA')
    l1, l2 = th['lines']; emph = th['emphasis']
    s = lerp(1.0, 1.04, clamp(t / th['end']))            # slow 100→104% move
    big = f(BEB, int(118 * s)); small = f(DMB, int(54 * s))
    # line 1 (dominant, Bebas) / line 2 (DM Sans) — premium mode
    def draw_line(y, text, fn, upper):
        parts = text.split(' ')
        ws = [d.textlength(p, font=fn) for p in parts]; sp = d.textlength(' ', font=fn)
        tot = sum(ws) + sp * (len(parts) - 1); x = W / 2 - tot / 2
        for p, w_ in zip(parts, ws):
            col = VGOLD if p.strip('"') in emph or p in emph else WHITE
            d.text((x + 4, y + 5), p, font=fn, fill=A((0, 0, 0), 0.75 * a))
            d.text((x, y), p, font=fn, fill=A(col, a), stroke_width=3, stroke_fill=A((0, 0, 0), a))
            if GL and col == VGOLD: GL.text((x, y), p, font=fn, fill=A(VGOLD, a * 0.7))
            x += w_ + sp
    # backing box for contrast over bright window patches
    box = Image.new('RGBA', (W, 400), (0, 0, 0, 0)); bd = ImageDraw.Draw(box)
    bd.rounded_rectangle([90, 30, 990, 300], radius=28, fill=(2, 3, 8, int(150 * a)))
    im.alpha_composite(box.filter(ImageFilter.GaussianBlur(10)), (0, th['position']['y_px'] - 50))
    d = ImageDraw.Draw(im, 'RGBA')
    y0 = th['position']['y_px']
    draw_line(y0, l1, big, True)
    draw_line(y0 + int(130 * s), l2, small, False)
    # gold kicker rule under
    d.line([(W / 2 - 60, y0 + int(210 * s)), (W / 2 + 60, y0 + int(210 * s))], fill=A(VGOLD, a), width=4)

def topic_band(im, t, busy):
    busy = busy or BUSY_LOW[0]
    th = HOOK['text_hook']; t0 = th['end']; t1 = DUR / 2
    if t < t0 or t >= t1 + 0.15 or busy: return
    a = appear(t, t0, 0.15) * (1 - clamp((t - t1) / 0.15))
    d = ImageDraw.Draw(im, 'RGBA')
    fn1 = f(BEB, 64); fn2 = f(DMB, 40)
    p1, p2 = 'ELITE COACHING', 'not just a protocol'
    w1 = d.textlength(p1, font=fn1); w2 = d.textlength(p2, font=fn2); tot = w1 + 24 + w2
    x = W / 2 - tot / 2; y = 262
    box = Image.new('RGBA', (W, 160), (0, 0, 0, 0)); bd = ImageDraw.Draw(box)
    bd.rounded_rectangle([x - 30, 20, x + tot + 30, 120], radius=20, fill=(2, 3, 8, int(170 * a)))
    im.alpha_composite(box.filter(ImageFilter.GaussianBlur(6)), (0, y - 30))
    d = ImageDraw.Draw(im, 'RGBA')
    d.text((x, y + 2), p1, font=fn1, fill=A(VGOLD, a)); d.text((x + w1 + 24, y + 16), p2, font=fn2, fill=A(WHITE, a))

# ======================= CAPTIONS =======================
FIX = {'blood': 'BLOOD', 'fucking': 'F*CKING', 'shit': 'SH*T'}
ACCENT_RED = {'sick', 'sedentary', 'argue', "don't", 'shit'}
ACCENT_GOLD = {'elite', 'optimal', 'optimize', 'track', 'educate', 'simplify', 'dashboard', 'leader', 'professional', 'coached', 'communicative', 'collaborative', 'dial'}
def build_groups():
    G = []; cur = []
    for i, x in enumerate(WORDS):
        if cur:
            prev = WORDS[cur[-1]]
            nb = next((c for c in CUTS if c > prev['s'] + 0.01), 1e9)
            if (x['w'][:1].isupper() and x['w'] not in ('I', "I'm")) or len(cur) >= 3 or x['s'] - prev['e'] > 0.28 or prev['w'][-1] in '.,?!' or x['s'] >= nb - 0.02 or len(''.join(WORDS[j]['w'] for j in cur)) > 15:
                G.append(cur); cur = []
        cur.append(i)
    if cur: G.append(cur)
    M = []
    for g in G:   # fold orphan connector words into the next group
        if M and len(M[-1]) == 1 and WORDS[M[-1][0]]['w'].lower() in ('and', 'to', 'a', 'the', 'but') and len(g) <= 3 and WORDS[g[0]]['s'] - WORDS[M[-1][0]]['e'] < 0.3:
            M[-1] = M[-1] + g
        else: M.append(g)
    return M
GROUPS = build_groups()
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
def captions(im, t, cap_y):
    g = group_at(t)
    if not g: return
    d = ImageDraw.Draw(im, 'RGBA')
    ws = [FIX.get(WORDS[i]['w'].lower().strip('.,?!'), WORDS[i]['w']).upper().strip('.,?!') for i in g]
    raw = [WORDS[i]['w'].lower().strip('.,?!') for i in g]
    size = 112
    while True:
        fn = f(BEB, size); sp = d.textlength(' ', font=fn) + 12; wd = [d.textlength(w, font=fn) for w in ws]; tot = sum(wd) + sp * (len(ws) - 1)
        if tot <= 900: break
        size -= 4
    xs = []; x = (W - tot) / 2
    for w_ in wd: xs.append(x); x += w_ + sp
    act = 0
    for k, i in enumerate(g):
        if WORDS[i]['s'] <= t: act = k
    g0 = WORDS[g[0]]['s']; s = lerp(0.92, 1, expo((t - g0) / 0.10))
    cap = Image.new('RGBA', (W, 260), (0, 0, 0, 0)); cd = ImageDraw.Draw(cap)
    shd = Image.new('RGBA', (W, 260), (0, 0, 0, 0)); sd = ImageDraw.Draw(shd)
    for k, (w_, x_) in enumerate(zip(ws, xs)): sd.text((x_ + 4, 46), w_, font=fn, fill=(0, 0, 0, 220))
    cap.alpha_composite(shd.filter(ImageFilter.GaussianBlur(7)))
    prev = max(0, act - 1); bt = expo((t - WORDS[g[act]]['s']) / 0.07) if act > 0 else 1
    bx0 = lerp(xs[prev], xs[act], bt) - 16; bx1 = lerp(xs[prev] + wd[prev], xs[act] + wd[act], bt) + 16
    hl = RED if raw[act] in ACCENT_RED else (VGOLD if raw[act] in ACCENT_GOLD else RED)
    lit_bar(cd, bx0, 40 + size * 0.02, bx1, 40 + size * 0.98, hl)
    for k, (w_, x_) in enumerate(zip(ws, xs)):
        col = CREAM
        if k != act and k < act and raw[k] in ACCENT_GOLD: col = VGOLD
        if k != act and k < act and raw[k] in ACCENT_RED: col = (255, 90, 80)
        if k == act and hl == VGOLD: col = INK
        cd.text((x_, 40), w_, font=fn, fill=col, stroke_width=0 if k == act else 3, stroke_fill=(0, 0, 0))
    if abs(s - 1) > 0.002:
        cap = cap.resize((int(W * s), int(260 * s)), Image.BICUBIC); ox = int((W - cap.width) / 2); oy = int(cap_y - 40 - (cap.height - 260) / 2)
    else: ox, oy = 0, cap_y - 40
    im.alpha_composite(cap, (ox, oy))

# ======================= STATIC BRAND LAYER =======================
def static_brand(d):
    # gold left rule (signature) + handle watermark + disclaimer
    d.rectangle([0, 250, 5, 1500], fill=A(GOLD, 0.85))
    d.text((W - 150, 1440), '@coach.agz', font=f(MONO, 24), fill=A(WHITE, 0.55), anchor='ra') if False else None

# ======================= TIMELINE BINDING =======================
def build_timeline():
    global SC, PIP, SPLIT, PUNCH
    T = {}
    T['wk'] = K('weekly'); T['dly'] = K('daily'); T['bp'] = K('daily', 1); T['cc'] = K('constant')
    T['feel'] = K('feel'); T['sleep'] = K('sleeping'); T['eat'] = K('eating')
    T['argue'] = K('argue'); T['her'] = K('her'); T['comp'] = K('compound')
    T['blood'] = K("how's"); axes = [K('mood'), K('sleep', 0, K('mood')), K('cognition'), K('focus'), K('relationships')]
    T['data'] = K('data'); T['track'] = K('track')
    T['optim'] = K('optimize'); T['optimal'] = K('optimal'); T['ref'] = K('reference'); T['sick'] = K('sick')
    T['side'] = K('side'); T['growth'] = K('growth'); T['cresp'] = K('compound', 0, K('growth'))
    T['dial'] = K('dial'); T['rx'] = K('prescriptions'); T['anc'] = K('ancillaries'); T['you'] = K('around')
    T['edu'] = K('educate'); T['sci'] = K('science'); T['exp'] = K('expect'); T['add'] = K('add')
    T['simp'] = K('simplify'); T['und'] = K('understand'); T['life'] = K('rest')
    T['guys'] = K('lot'); T['two'] = K('two'); T['sum'] = K('summary'); T['deep'] = K('insanely'); T['edu2'] = K('educational'); T['any'] = K('any')
    T['point'] = K('point', 0, K('any')); T['lead'] = K('leader'); T['opt2'] = K('optimal', 0, K('leader')); T['kids'] = K('kids'); T['wife'] = K('wife'); T['rest2'] = K('rest', 0, K('wife'))
    T['com'] = K('comment'); T['elite'] = K('elite', 0, K('comment')); T['prof'] = K('professional'); T['proto'] = K('protocol', 0, K('professional'))
    def END(word, n=0, after=0.0): return K(word, n, after, end=True)
    SC = [
        (HOOK['text_hook']['end'] - 0.05, T['feel'] - 0.35, lambda im, t, a, b: sc_tracker(im, t, a, b, max(T['wk'], HOOK['text_hook']['end'] + 0.2), T['dly'], T['bp'], T['cc']), 'top'),
        (T['feel'] - 0.25, END('eating') + 0.35, lambda im, t, a, b: sc_form(im, t, a, b, T['feel'], T['sleep'], T['eat']), 'low'),
        (T['argue'] - 0.2, T['blood'] - 0.2, lambda im, t, a, b: sc_suspect(im, t, a, b, T['her'], T['comp']), 'top'),
        (K('matters') - 0.3, END('basis', 1) + 0.25, lambda im, t, a, b: sc_radar(im, t, a, b, axes, T['data']), 'low'),
        (K('according') - 0.2, END('sedentary') + 0.4, lambda im, t, a, b: sc_range(im, t, a, b, T['optimal'], T['ref'], T['sick']), 'top'),
        (T['side'] - 0.25, T['dial'] - 0.3, lambda im, t, a, b: sc_gauges(im, t, a, b, T['side'], T['growth'], T['cresp']), 'low'),
        (T['dial'] - 0.2, T['edu'] - 0.3, lambda im, t, a, b: sc_mixer(im, t, a, b, T['dial'], T['rx'], T['anc'], T['you']), 'top'),
        (T['simp'] - 0.2, END('life') + 0.3, lambda im, t, a, b: sc_simplify(im, t, a, b, T['simp'], T['und']), 'low'),
        (T['lead'] - 0.25, T['com'] - 0.3, lambda im, t, a, b: sc_life(im, t, a, b, T['lead'], T['opt2'], T['kids'], T['wife'], T['rest2']), 'low'),
        (T['com'] - 0.2, 1e9, lambda im, t, a, b: sc_cta(im, t, T['com'], T['elite'], T['prof'], T['proto']), 'low'),
    ]
    PIP = (T['edu'] - 0.2, T['simp'] - 0.35, T)      # face window + chart
    SPLIT = (T['two'] - 0.2, T['point'] - 0.2, T)    # push-up split, two docs
    # punch-ins (110%) on key lines
    PUNCH = [(K('fucking') - 0.05, END('sedentary') + 0.1), (T['guys'] - 0.05, K('want', 0, T['guys']) + 0.4), (T['prof'] - 0.4, DUR + 1)]
    return T
TM = build_timeline()

# ======================= FRAME =======================
def frame(src, t):
    global GL
    seg = sum(1 for c in CUTS if c <= t + 1e-6)
    z = 1.0 if seg % 2 == 0 else 1.06
    for a_, b_ in PUNCH:
        if a_ <= t < b_: z = max(z, lerp(z, 1.12, expo((t - a_) / 0.18)))
    pip_p = 0; split_p = 0
    p0, p1, _ = PIP
    if p0 <= t < p1 + 0.35: pip_p = min(ease_io((t - p0) / 0.35), 1 - ease_io((t - p1) / 0.35))
    s0, s1, _ = SPLIT
    if s0 <= t < s1 + 0.35: split_p = min(ease_io((t - s0) / 0.35), 1 - ease_io((t - s1) / 0.35))
    if z != 1.0:
        big = src.resize((int(W * z), int(H * z)), Image.BICUBIC); ox = (big.width - W) // 2; oy = int((big.height - H) * 0.42); src = big.crop((ox, oy, ox + W, oy + H))
    # ---- layout modes that keep the face fully visible ----
    low_p = 0
    for (a_, b_, fn_, zone_) in SC:
        if zone_ == 'low' and a_ - 0.05 <= t < b_ + 0.45: low_p = max(low_p, min(ease_io((t - a_ + 0.05) / 0.3), 1 - ease_io((t - b_ - 0.1) / 0.3)))
    if pip_p > 0 or split_p > 0:
        base = Image.new('RGB', (W, H), NAVY)
        # subtle warm glow top-right (brand bg)
        if pip_p > 0:
            # face window: footage scaled to 0.62, framed, top-centre; the face stays large and clear
            sc_ = lerp(1.0, 0.56, pip_p)
            fw, fh = int(W * sc_), int(H * sc_)
            cx = W / 2; cy = lerp(H / 2, 560, pip_p)
            sm = src.resize((fw, fh), Image.BICUBIC)
            # crop the window to the head/shoulders region when small
            crop_h = int(lerp(fh, fh * 0.80, pip_p)); top_off = int(lerp(0, fh * 0.12, pip_p))
            sm = sm.crop((0, top_off, fw, top_off + crop_h))
            bg = src.filter(ImageFilter.GaussianBlur(30)); bg = Image.blend(bg, Image.new('RGB', (W, H), NAVY), 0.82 * pip_p + 0.0)
            im = bg.convert('RGBA')
            m = Image.new('L', sm.size, 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, sm.width - 1, sm.height - 1], radius=int(28 * pip_p), fill=255)
            px, py = int(cx - fw / 2), int(cy - crop_h / 2)
            im.paste(sm.convert('RGBA'), (px, py), m)
            d = ImageDraw.Draw(im, 'RGBA')
            d.rounded_rectangle([px, py, px + sm.width, py + sm.height], radius=int(28 * pip_p), outline=A(VGOLD, pip_p), width=4)
            brackets(d, px - 10, py - 10, px + sm.width + 10, py + sm.height + 10, A(VGOLD, pip_p), 36, 6)
            win_bottom = py + sm.height
        else:
            dy = -int(380 * split_p)
            im = Image.new('RGBA', (W, H), NAVY + (255,))
            im.paste(src.convert('RGBA'), (0, dy))
            # dark floor under the lifted footage
            fl = Image.new('RGBA', (W, H), (0, 0, 0, 0)); fd = ImageDraw.Draw(fl)
            yb = H + dy
            fd.rectangle([0, yb - 260, W, H], fill=(0, 0, 0, 0))
            grad = np.clip((np.arange(H)[:, None] - (yb - 420)) / 420, 0, 1) * split_p
            fl = Image.merge('RGBA', [Image.new('L', (W, H), c) for c in DEEP] + [Image.fromarray((np.repeat(grad, W, 1) * 245).astype(np.uint8))])
            im.alpha_composite(fl)
    elif low_p > 0:
        dy = int(round(LOWSHIFT * 1.35 * low_p))
        im = Image.new('RGBA', (W, H), DEEP + (255,)); im.paste(src.convert('RGBA'), (0, dy))
        if dy < 0:
            strip = src.crop((0, H + dy * 2, W, H + dy)).transpose(Image.FLIP_TOP_BOTTOM).filter(ImageFilter.GaussianBlur(12))
            strip = Image.blend(strip, Image.new('RGB', strip.size, DEEP), 0.45)
            im.paste(strip.convert('RGBA'), (0, H + dy))
    else:
        im = src.convert('RGBA')
    # top/bottom scrims for legibility (very light — footage untouched in the middle)
    yy = np.arange(H); sa = np.where(yy > 1300, np.clip((yy - 1300) / 300, 0, 1) * 120, 0); sa = np.maximum(sa, np.where(yy < 560, (1 - yy / 560) * 110, 0))
    im.alpha_composite(Image.merge('RGBA', [Image.new('L', (W, H), c) for c in NAVY] + [Image.fromarray(np.repeat(sa.astype(np.uint8)[:, None], W, 1))]))
    glow = Image.new('RGBA', (W, H), (0, 0, 0, 0)); GL = ImageDraw.Draw(glow, 'RGBA')
    d = ImageDraw.Draw(im, 'RGBA')
    # ---- scenes ----
    busy_top = False; busy_low = False
    for (a_, b_, fn, zone) in SC:
        if a_ <= t < b_ + 0.2:
            fn(im, t, a_, b_)
            if zone == 'top': busy_top = True
            if zone == 'low': busy_low = True
    if pip_p > 0:
        T = TM; d = ImageDraw.Draw(im, 'RGBA')
        lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); ld = ImageDraw.Draw(lay)
        band = sc_pip_chart(ld, t, p0, p1, T['sci'], T['exp'], T['add'], T['und'], T['life'], 1.0)
        if band is not None: im.alpha_composite(Image.eval(band, lambda v: v).point(lambda v: v) if False else band)
        lay.putalpha(lay.split()[3].point(lambda v: int(v * clamp((pip_p - 0.4) / 0.6))))
        im.alpha_composite(lay)
        busy_top = busy_low = True
    if split_p > 0:
        T = TM; lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); ld = ImageDraw.Draw(lay)
        sc_docs(ld, t, T['sum'], T['deep'], T['edu2'], T['any'], 1.0, int(lerp(300, 0, split_p)) - 80)
        lay.putalpha(lay.split()[3].point(lambda v: int(v * split_p)))
        im.alpha_composite(lay)
        busy_top = True
    BUSY_LOW[0] = busy_low
    hook(im, t)
    topic_band(im, t, busy_top)
    # captions: low by default; jump to the top zone when a lower panel is up; under the window in PIP
    if pip_p > 0.5: cap_y = 1600
    elif split_p > 0.5: cap_y = 1540
    elif busy_low: cap_y = 300 if t > HOOK['text_hook']['end'] + 0.15 else 1210
    else: cap_y = 1400
    if busy_low and busy_top and pip_p <= 0.5 and split_p <= 0.5: cap_y = 1210
    captions(im, t, cap_y)
    d = ImageDraw.Draw(im, 'RGBA')
    # static brand: gold edge rule + handle + disclaimer (never animate)
    d.rectangle([0, 250, 5, 1490], fill=A(GOLD, 0.9))
    txt(d, 1010, 206, '@coach.agz', f(MONO, 24), WHITE, 0.6, anchor='ra')
    txt(d, 66, 1478, 'FOR RESEARCH & EDUCATIONAL PURPOSES ONLY', f(MONO, 16), MUTED, 0.6) if False else None
    GL = None
    if glow.getbbox():
        sm = glow.resize((W // 4, H // 4), Image.BILINEAR)
        g1 = np.asarray(sm.filter(ImageFilter.GaussianBlur(3.5))).astype(np.float32) / 255; g2 = np.asarray(sm.filter(ImageFilter.GaussianBlur(10))).astype(np.float32) / 255
        prem = np.clip(g1[..., :3] * g1[..., 3:] * 2.0 + g2[..., :3] * g2[..., 3:] * 1.6, 0, 1)
        prem = np.asarray(Image.fromarray((prem * 255).astype(np.uint8)).resize((W, H), Image.BILINEAR)).astype(np.float32) / 255
        b = np.asarray(im.convert('RGB')).astype(np.float32) / 255
        return Image.fromarray(((1 - (1 - b) * (1 - prem)) * 255).astype(np.uint8))
    return im.convert('RGB')

if __name__ == '__main__':
    n0, n1, out = int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
    if out.endswith('.jpg') or out.endswith('.png'):
        # still mode: n0 = frame index
        dec = subprocess.run(['ffmpeg', '-v', 'error', '-ss', f'{n0 / FPS:.4f}', '-i', S + '/cut.mp4', '-frames:v', '1', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], capture_output=True).stdout
        frame(Image.frombuffer('RGB', (W, H), dec), n0 / FPS).save(out, quality=90); sys.exit()
    dec = subprocess.Popen(['ffmpeg', '-v', 'error', '-ss', f'{n0 / FPS:.4f}', '-i', S + '/cut.mp4', '-frames:v', str(n1 - n0), '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], stdout=subprocess.PIPE)
    enc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-crf', '14', '-preset', 'fast', '-pix_fmt', 'yuv420p', out], stdin=subprocess.PIPE)
    for n in range(n0, n1):
        buf = dec.stdout.read(W * H * 3)
        if len(buf) < W * H * 3: break
        enc.stdin.write(frame(Image.frombuffer('RGB', (W, H), buf), n / FPS).tobytes())
    enc.stdin.close(); enc.wait(); dec.kill(); print('done', n0, n1)
