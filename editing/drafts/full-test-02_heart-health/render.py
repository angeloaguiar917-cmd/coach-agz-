# Coach AGZ - Heart health Reel, full test 02 renderer (1080x1920, 30 fps)
# Layout modes: FULL (untouched footage + roof graphics) and STAGE (footage window + graph panel).
import json, subprocess, sys, math
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

S = sys.argv[1]; F = S + '/fonts/'; T = S + '/work/'
W, H = 1080, 1920; FPS = 30
CUT = json.load(open(T + 'cutlist.json')); DUR = CUT['dur']
WORDS = json.load(open(T + 'words_final.json'))
# piece boundaries in cut time (jump cuts)
BOUNDS = []; acc = 0
for a, b in CUT['keeps']:
    BOUNDS.append((acc, acc + (b - a))); acc += b - a

GOLD = (201, 169, 110); CREAM = (244, 241, 234); NAVY = (14, 17, 23); MUTED = (124, 124, 130)
RED = (255, 34, 28); VGOLD = (255, 194, 26); CYAN = (0, 229, 255); GREEN = (30, 255, 110)
DEEP = (2, 3, 8); INK = (6, 8, 14); WHITE = (255, 255, 255); BLUE = (79, 163, 224); AMBER = (240, 160, 48)
PANELC = (18, 21, 30); COARED = (210, 10, 20)
MONO = 'JBMono-500.ttf'; MONOB = 'JBMono-800.ttf'; BEB = 'BebasNeue.ttf'; DMB = 'DMSans-700.ttf'; DMR = 'DMSans-400.ttf'
BAR = 'Barlow-600.ttf'; BARB = 'Barlow-800.ttf'
_fc = {}
def f(n, s):
    k = (n, int(s))
    if k not in _fc: _fc[k] = ImageFont.truetype(F + n, int(s))
    return _fc[k]
def clamp(x, a=0, b=1): return max(a, min(b, x))
def expo(x): x = clamp(x); return 1 if x >= 1 else 1 - 2 ** (-10 * x)
def ease_io(x): x = clamp(x); return 4 * x ** 3 if x < .5 else 1 - (-2 * x + 2) ** 3 / 2
def back(x, s=1.2): x = clamp(x); return 1 + (s + 1) * (x - 1) ** 3 + s * (x - 1) ** 2   # weighted settle (small)
def lerp(a, b, t): return a + (b - a) * t
def A(c, a): return tuple(c[:3]) + (int(clamp(a) * 255),)
def appear(t, t0, dur=0.16): return expo((t - t0) / dur)
def W_(i): return WORDS[i]
GL = None
SFX = []   # filled by build_sfx() below (time, kind)

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
def tag(d, x, y, label, col=RED, size=30, a=1.0, glow=True, font=None):
    if a <= 0: return x
    fn = font or f(MONOB, size); tw = d.textlength(label, font=fn); h = size + 16
    lit_bar(d, x, y, x + tw + 24, y + h, col, a)
    d.text((x + 12, y + 6), label, font=fn, fill=A(INK if col in (VGOLD, GREEN, CYAN) else WHITE, a))
    if GL and glow: GL.rectangle([x - 3, y - 3, x + tw + 27, y + h + 3], outline=A(col, a), width=7)
    return x + tw + 24
def arrow(d, x0, y0, x1, y1, col, w=5, a=1.0, L=18):
    if a <= 0: return
    d.line([(x0, y0), (x1, y1)], fill=A(col, a), width=int(w))
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
def meter(d, x0, y0, x1, y1, frac, col, label, value=None, a=1.0):
    if a <= 0: return
    txt(d, x0, y0 - 36, label, f(MONO, 24), CREAM, a)
    d.rectangle([x0, y0, x1, y1], outline=A((70, 74, 90), a), width=2)
    xf = lerp(x0 + 3, x1 - 3, clamp(frac)); lit_bar(d, x0 + 3, y0 + 3, xf, y1 - 3, col, a)
    if GL: GL.rectangle([x0 + 3, y0 + 3, xf, y1 - 3], fill=A(col, a * 0.6))
    if value:
        fn = f(BEB, 40); tw = d.textlength(value, font=fn); txt(d, x1 - tw, y0 - 46, value, fn, col, a)
def glowline(d, pts, col, w=5, a=1.0, gw=12):
    if a <= 0 or len(pts) < 2: return
    d.line(pts, fill=A(col, a), width=int(w), joint='curve')
    if GL: GL.line(pts, fill=A(col, a), width=gw)
def heart_pts(cx, cy, s, n=90):
    P = []
    for i in range(n):
        u = 2 * math.pi * i / n
        x = 16 * math.sin(u) ** 3; y = 13 * math.cos(u) - 5 * math.cos(2 * u) - 2 * math.cos(3 * u) - math.cos(4 * u)
        P.append((cx + x * s, cy - y * s))
    return P
def redacted(d, x, y, w, h, a=1.0):
    d.rectangle([x, y, x + w, y + h], fill=A((40, 42, 50), a))
    for k in range(0, int(w), 14): d.line([(x + k, y + h), (x + k + h, y)], fill=A((60, 62, 72), a), width=2)

# ---------------- layout constants ----------------
WIN = (70, 150, 1010, 1004)                       # footage window in STAGE
SRC_Y0 = 392; SRC_H = (WIN[3] - WIN[1]) * 1080 / (WIN[2] - WIN[0])
P = (64, 1028, 1016, 1392)                       # graph panel
CAP_Y = 1462                                      # caption lane centre

# ---------------- PANEL SCENES ----------------
def sc_problem(d, t):
    x0, y0, x1, y1 = P
    if t < 9.30:     # timeline
        a = 1 - clamp((t - 9.18) / 0.12)
        txt(d, x0 + 36, y0 + 70, 'YOUR TIMELINE', f(MONO, 26), GOLD, a)
        p = expo((t - 5.50) / 0.55); xl, xr, yy = x0 + 50, x1 - 50, y0 + 230
        d.line([(xl, yy), (lerp(xl, xr, p), yy)], fill=A(CREAM, a), width=4)
        for k in range(13):
            xx = lerp(xl, xr, k / 12)
            if xx <= lerp(xl, xr, p): d.line([(xx, yy - (14 if k % 4 == 0 else 7)), (xx, yy)], fill=A(CREAM, a), width=3)
        txt(d, xl, yy + 16, 'NOW', f(MONO, 24), MUTED, a); txt(d, xr - 90, yy + 16, 'YEARS', f(MONO, 24), MUTED, a * p)
        # heart load line creeping up along the timeline
        n = int(40 * p); pts = [(lerp(xl, xr, i / 40), yy - 20 - 90 * (i / 40) ** 1.6) for i in range(n + 1)]
        glowline(d, pts, RED, 4, a);
        if n > 3: txt(d, pts[-1][0] - 170, pts[-1][1] - 44, 'HEART LOAD', f(MONOB, 24), RED, a)
        aa = appear(t, 6.94); x = tag(d, xl, y0 + 112, 'TRT', VGOLD, 30, aa * a)
        txt(d, x + 16, y0 + 118, 'OR', f(MONO, 28), MUTED, appear(t, 7.5) * a)
        tag(d, x + 70, y0 + 112, 'CYCLE', VGOLD, 30, appear(t, 7.86) * a)
    elif t < 11.0:   # two unmanaged hits
        a = appear(t, 9.30, 0.14) * (1 - clamp((t - 10.9) / 0.10))
        for k, tt in enumerate((9.78, 10.14)):
            aa = appear(t, tt) * a; yy = y0 + 92 + k * 120
            if aa <= 0: continue
            d.rounded_rectangle([x0 + 36, yy, x1 - 36, yy + 96], 12, fill=A((24, 10, 14), aa), outline=A(RED, aa), width=3)
            txt(d, x0 + 60, yy + 18, f'HIT 0{k+1}', f(BEB, 62), WHITE, aa)
            redacted(d, x0 + 220, yy + 34, 300, 30, aa)
            cross(d, x1 - 300, yy + 32, RED, 1.0, aa); txt(d, x1 - 256, yy + 28, 'UNMANAGED', f(MONOB, 30), RED, aa)
    else:            # two compounds, redacted
        a = appear(t, 11.0, 0.14)
        for k, tt in enumerate((11.20, 11.40)):
            p = expo((t - tt) / 0.22)
            if p <= 0: continue
            cx = lerp(x0 + (240 if k == 0 else 712) + (-120 if k == 0 else 120), x0 + (240 if k == 0 else 712), p); cy = y0 + 170
            d.rounded_rectangle([cx - 150, cy - 46, cx + 150, cy + 46], 46, fill=A((10, 12, 20), p), outline=A(VGOLD, p), width=4)
            d.rounded_rectangle([cx - 150, cy - 46, cx, cy + 46], 46, fill=A(VGOLD, p)); d.rectangle([cx - 50, cy - 46, cx, cy + 46], fill=A(VGOLD, p))
            if GL: GL.rounded_rectangle([cx - 154, cy - 50, cx + 154, cy + 50], 50, outline=A(VGOLD, p), width=9)
            txt(d, cx - 132, cy - 30, f'0{k+1}', f(BEB, 66), INK, p); txt(d, cx + 26, cy - 22, '?', f(BEB, 56), VGOLD, p)
            txt(d, cx - 150, cy + 66, f'COMPOUND 0{k+1}', f(MONO, 26), CREAM, p); redacted(d, cx - 150, cy + 106, 300, 24, p)
        tag(d, x0 + 380, y0 + 30 + 300 - 4, 'START TODAY', GREEN, 26, appear(t, 12.62)) if False else None
        aa = appear(t, 12.62)
        if aa > 0:
            fn = f(MONOB, 28); lab = 'HOP ON TODAY'; tw = d.textlength(lab, font=fn)
            tag(d, (x0 + x1) / 2 - (tw + 24) / 2, y0 + 64, lab, VGOLD, 28, aa)

def sc_bars(d, t):
    x0, y0, x1, y1 = P
    txt(d, x0 + 36, y0 + 64, 'LIPID MARKERS', f(MONO, 26), GOLD, appear(t, 20.0))
    d.rectangle([x1 - 300, y0 + 70, x1 - 284, y0 + 86], outline=A(MUTED, 1), width=2); txt(d, x1 - 276, y0 + 64, 'BASELINE', f(MONO, 22), MUTED)
    d.rectangle([x1 - 150, y0 + 70, x1 - 134, y0 + 86], fill=A(RED, 1)); txt(d, x1 - 126, y0 + 64, 'CYCLE', f(MONO, 22), CREAM)
    base = y1 - 58; bw = 120
    groups = [('HDL', 21.18, 0.28, 'DOWN'), ('LDL', 23.76, 1.55, 'UP'), ('APOB', 24.44, 1.5, 'UP')]
    d.line([(x0 + 40, base), (x1 - 40, base)], fill=A((90, 94, 110), 1), width=2)
    for i, (lab, tt, tgt, dirn) in enumerate(groups):
        cx = x0 + 180 + i * 300; bh = 120
        ga = appear(t, 20.05 + i * 0.08, 0.2)
        d.rectangle([cx - bw / 2 - 66, base - bh, cx - 6 - bw / 2 + 60 - 66, base], outline=A(MUTED, ga), width=2)   # ghost baseline
        p = ease_io((t - tt) / 0.5); h = lerp(bh, bh * tgt, p) * ga
        col = RED if p > 0.05 else CYAN
        lit_bar(d, cx - 10, base - h, cx + 70, base, col, ga)
        if GL and p > 0: GL.rectangle([cx - 10, base - h, cx + 70, base], outline=A(col, ga), width=6)
        txt(d, cx - 70, base + 10, lab, f(BEB, 40), WHITE, ga)
        if p > 0.4:
            aa = clamp((p - 0.4) / 0.3); ay = base - h - 18
            if dirn == 'UP': arrow(d, cx + 30, ay, cx + 30, ay - 40, RED, 6, aa)
            else: arrow(d, cx + 110, base - bh, cx + 110, base - h + 4, RED, 6, aa); txt(d, cx + 128, base - bh + 20, 'CRASH', f(MONOB, 22), RED, aa)

def sc_lines(d, t):
    x0, y0, x1, y1 = P
    a = appear(t, 24.9, 0.14)
    txt(d, x0 + 36, y0 + 64, 'TRAJECTORY ON CYCLE', f(MONO, 26), GOLD, a)
    gx0, gy0, gx1, gy1 = x0 + 70, y0 + 110, x1 - 230, y1 - 40
    d.line([(gx0, gy0), (gx0, gy1), (gx1, gy1)], fill=A((90, 94, 110), a), width=3)
    for k in range(1, 4): d.line([(gx0, lerp(gy1, gy0, k / 4)), (gx1, lerp(gy1, gy0, k / 4))], fill=A((40, 44, 56), a), width=1)
    txt(d, gx1 - 70, gy1 + 4, 'TIME', f(MONO, 20), MUTED, a)
    def curve(t0, dur, shape, col, lab):
        p = clamp((t - t0) / dur)
        if p <= 0: return None
        n = int(60 * p) + 1; pts = [(lerp(gx0, gx1, i / 60), gy1 - (gy1 - gy0) * shape(i / 60)) for i in range(n)]
        glowline(d, pts, col, 6, a)
        x, y = pts[-1]; d.ellipse([x - 9, y - 9, x + 9, y + 9], fill=A(col, a))
        if p >= 1: txt(d, gx1 + 18, y - 18, lab, f(BEB, 40), col, a)
        return pts[-1]
    curve(25.10, 1.3, lambda u: 0.08 + 0.85 * u ** 2.1, RED, 'CV RISK')
    curve(27.10, 1.0, lambda u: 0.10 + 0.48 * (1 - (1 - u) ** 2), VGOLD, 'PHYSIQUE')
    if t >= 28.34:
        aa = appear(t, 28.34); bx = gx1 - 150
        brackets(d, bx, gy0 - 14, gx1 + 14, gy0 + 90, A(RED, aa), 22, 5)
        if GL: brackets(GL, bx, gy0 - 14, gx1 + 14, gy0 + 90, A(RED, aa), 22, 10)
        tag(d, gx0 + 20, gy0 - 6, 'LOOKS GREAT  ≠  HEALTHY', RED, 26, aa)

def sc_ezet(d, t):
    x0, y0, x1, y1 = P
    txt(d, x0 + 36, y0 + 64, 'INTESTINAL WALL · X-RAY', f(MONO, 26), CYAN, appear(t, 29.15))
    blocked = t >= 31.24
    wy = y0 + 236; chans = [x0 + 180 + k * 200 for k in range(4)]
    # villi wall (wavy) drawn as segments between channels
    pts = []
    for xx in range(x0 + 30, x1 - 30, 6):
        if any(abs(xx - c) < 30 for c in chans):
            if pts: glowline(d, pts, CYAN, 4, 0.95, 10); pts = []
            continue
        pts.append((xx, wy + 14 * math.sin(xx / 22.0)))
    if pts: glowline(d, pts, CYAN, 4, 0.95, 10)
    for c in chans:
        d.rectangle([c - 30, wy - 26, c - 22, wy + 26], fill=A(CYAN, 0.9)); d.rectangle([c + 22, wy - 26, c + 30, wy + 26], fill=A(CYAN, 0.9))
        if blocked:
            p = expo((t - 31.24 - (c - chans[0]) / 4000) / 0.12); yy = lerp(wy - 90, wy - 22, p)
            d.rectangle([c - 22, yy, c + 22, yy + 44], fill=A(RED, p));
            if GL: GL.rectangle([c - 24, yy - 2, c + 24, yy + 46], outline=A(RED, p), width=8)
    txt(d, x0 + 36, wy + 70, 'BLOODSTREAM', f(MONO, 22), MUTED); txt(d, x0 + 36, y0 + 110, 'GUT · DIETARY CHOLESTEROL', f(MONO, 22), MUTED)
    # cholesterol particles
    rng = np.random.default_rng(3)
    for i in range(26):
        c = chans[i % 4]; ph = rng.random(); sp = 0.45 + 0.3 * rng.random(); off = (rng.random() - 0.5) * 120
        u = (t * sp + ph) % 1
        ytop = y0 + 140; yy = lerp(ytop, wy + 110, u)
        xx = lerp(c + off, c, clamp((yy - ytop) / (wy - 40 - ytop)))
        if blocked and yy > wy - 30:
            if t - 31.24 < 0.4 and yy > wy + 30: pass                 # last ones already through
            else: continue
        al = min(1, u * 8) * (1 if yy < wy + 80 else clamp((wy + 110 - yy) / 30))
        d.ellipse([xx - 9, yy - 9, xx + 9, yy + 9], fill=A(VGOLD, al))
        if GL: GL.ellipse([xx - 12, yy - 12, xx + 12, yy + 12], fill=A(VGOLD, al * 0.7))
    aa = appear(t, 30.26)
    if aa > 0: tag(d, x1 - 260, y0 + 52, 'EZETIMIBE', VGOLD, 30, aa)
    if blocked:
        aa = appear(t, 31.40); tag(d, chans[1] - 40, wy - 96, 'NPC1L1 BLOCKED', RED, 26, aa)
    if t >= 33.84:
        aa = appear(t, 33.84); c = chans[2]
        brackets(d, c - 50, wy - 40, c + 50, wy + 40, A(CYAN, aa), 16, 4)
        txt(d, c + 60, wy + 40, 'CHOLESTEROL', f(MONOB, 22), CYAN, aa); txt(d, c + 60, wy + 66, 'TRANSPORTER', f(MONOB, 22), CYAN, aa)

def sc_flow(d, t):
    x0, y0, x1, y1 = P
    if t < 40.50:
        a = appear(t, 36.30, 0.14) * (1 - clamp((t - 40.38) / 0.12))
        txt(d, x0 + 36, y0 + 64, 'WHERE CHOLESTEROL GOES', f(MONO, 26), GOLD, a)
        nodes = [('GUT', x0 + 60), ('BLOOD', x0 + 360), ('LIVER', x0 + 660)]
        for k, (lab, nx) in enumerate(nodes):
            aa = appear(t, 36.36 + k * 0.1) * a
            d.rounded_rectangle([nx, y0 + 110, nx + 230, y0 + 190], 14, fill=A((10, 14, 24), aa), outline=A(CYAN if lab != 'LIVER' else VGOLD, aa), width=4)
            txt(d, nx + 115, y0 + 150, lab, f(BEB, 50), WHITE, aa, 'mm')
        absorb = lerp(1, 0.32, ease_io((t - 37.4) / 0.6)); clear = lerp(0.35, 0.95, ease_io((t - 38.9) / 0.6))
        arrow(d, x0 + 296, y0 + 150, x0 + 352, y0 + 150, CYAN, 4 + 6 * absorb, a)
        arrow(d, x0 + 596, y0 + 150, x0 + 652, y0 + 150, VGOLD, 4 + 6 * clear, a)
        meter(d, x0 + 60, y0 + 262, x0 + 430, y0 + 292, absorb, RED if absorb < 0.6 else CYAN, 'ABSORBED', 'LESS' if absorb < 0.6 else '', appear(t, 36.9) * a)
        meter(d, x0 + 520, y0 + 262, x1 - 60, y0 + 292, clear, GREEN if clear > 0.6 else CYAN, 'LDL CLEARED', 'MORE' if clear > 0.6 else '', appear(t, 38.6) * a)
    else:            # stat tiles
        txt(d, x0 + 36, y0 + 64, 'RESULT', f(MONO, 26), GOLD, appear(t, 40.5))
        for k, (lab, tt) in enumerate((('LDL', 40.62), ('APOB', 41.76))):
            p = expo((t - tt) / 0.2)
            if p <= 0: continue
            tx = x0 + 40 + k * 450; ty = y0 + 100 + (1 - p) * 30
            d.rounded_rectangle([tx, ty, tx + 420, ty + 200], 16, fill=A((10, 22, 16), p), outline=A(GREEN, p), width=4)
            if GL: GL.rounded_rectangle([tx, ty, tx + 420, ty + 200], 16, outline=A(GREEN, p * 0.7), width=8)
            q = ease_io((t - tt - 0.1) / 0.5); ay = ty + 40 + 100 * q
            arrow(d, tx + 330, ty + 40, tx + 330, ay + 10, GREEN, 12, p, 34)
            txt(d, tx + 30, ty + 26, lab, f(BEB, 120), WHITE, p); txt(d, tx + 34, ty + 150, 'LOWER', f(MONOB, 28), GREEN, p)
        if t >= 43.22:
            aa = appear(t, 43.22); check(d, x0 + 44, y1 - 54, GREEN, 1.1, aa); txt(d, x0 + 92, y1 - 54, 'LOWER = LESS CARDIOVASCULAR RISK', f(MONOB, 26), GREEN, aa)

def gauge(d, cx, cy, r, val, a=1.0, label='PRESSURE'):
    segs = [(BLUE, 0, 0.25), (GREEN, 0.25, 0.5), (AMBER, 0.5, 0.75), (RED, 0.75, 1.0)]
    for col, s0, s1 in segs:
        d.arc([cx - r, cy - r, cx + r, cy + r], 180 + 180 * s0 + 1, 180 + 180 * s1 - 1, fill=A(col, a), width=22)
        if GL: GL.arc([cx - r, cy - r, cx + r, cy + r], 180 + 180 * s0, 180 + 180 * s1, fill=A(col, a * 0.6), width=30)
    ang = math.pi * (1 + val)
    d.line([(cx, cy), (cx + (r - 30) * math.cos(ang), cy + (r - 30) * math.sin(ang))], fill=A(WHITE, a), width=6)
    d.ellipse([cx - 14, cy - 14, cx + 14, cy + 14], fill=A(WHITE, a))
    txt(d, cx, cy + 24, label, f(MONOB, 24), CREAM, a, 'mt')

def heart(d, cx, cy, s, wall, a=1.0, col=RED):
    out = heart_pts(cx, cy, s)
    d.polygon(out, fill=A((40, 8, 12), a)); glowline(d, out + [out[0]], col, 5, a, 12)
    # left-ventricle chamber shrinks as wall thickens
    cw = 4.6 * s * (1 - wall * 0.75); ch = 6.4 * s * (1 - wall * 0.5)
    lx, ly = cx + 2.6 * s, cy + 1.0 * s
    d.ellipse([lx - cw, ly - ch, lx + cw, ly + ch], fill=A((10, 12, 20), a), outline=A(CREAM, a * 0.8), width=3)
    return lx, ly, cw

def sc_pressure(d, t):
    x0, y0, x1, y1 = P
    txt(d, x0 + 36, y0 + 64, 'BLOOD PRESSURE · CARDIAC LOAD', f(MONO, 26), GOLD, appear(t, 47.2))
    v = lerp(0.38, 0.9, ease_io((t - 47.3) / 0.8))
    gauge(d, x0 + 220, y0 + 300, 140, v, appear(t, 47.25))
    if t >= 47.8: tag(d, x0 + 150, y0 + 102, 'ELEVATED', RED, 26, appear(t, 47.8))
    wl = lerp(0.2, 0.92, ease_io((t - 48.8) / 0.6))
    meter(d, x0 + 420, y1 - 60, x0 + 610, y1 - 36, wl, RED, 'WORKLOAD', None, appear(t, 48.8))
    wall = lerp(0.15, 0.62, ease_io((t - 50.74) / 1.0))
    ha = appear(t, 49.5, 0.25)
    lx, ly, cw = heart(d, x1 - 170, y0 + 200, 7.6, wall, ha)
    if t >= 50.74:
        aa = appear(t, 50.74)
        txt(d, x1 - 520, y0 + 96, 'LEFT VENTRICLE', f(MONOB, 24), CREAM, aa)
        arrow(d, x1 - 360, y0 + 128, lx - cw - 6, ly - 6, CREAM, 3, aa, 14)
    if t >= 51.44: tag(d, x1 - 520, y0 + 150, 'WALL THICKENS', RED, 24, appear(t, 51.44))

def sc_receptor(d, t):
    x0, y0, x1, y1 = P
    txt(d, x0 + 36, y0 + 64, 'AT1 RECEPTOR', f(MONO, 26), GOLD, appear(t, 57.95))
    # membrane + receptor socket (left half)
    my = y0 + 280; rx = x0 + 250
    d.line([(x0 + 40, my), (x0 + 450, my)], fill=A(CREAM, 0.9), width=4)
    d.line([(rx - 60, my), (rx - 60, my - 70), (rx - 30, my - 70), (rx - 30, my - 30), (rx + 30, my - 30), (rx + 30, my - 70), (rx + 60, my - 70), (rx + 60, my)], fill=A(CYAN, 1), width=6)
    if GL: GL.line([(rx - 60, my), (rx - 60, my - 70), (rx - 30, my - 70), (rx - 30, my - 30), (rx + 30, my - 30), (rx + 30, my - 70), (rx + 60, my - 70), (rx + 60, my)], fill=A(CYAN, 1), width=12)
    txt(d, rx, my + 14, 'AT1', f(BEB, 40), CYAN, 1, 'mt')
    pb = expo((t - 58.02) / 0.18); by = lerp(y0 + 100, my - 70, pb)
    if t >= 58.02:
        d.rectangle([rx - 28, by, rx + 28, by + 40], fill=A(VGOLD, 1));
        if GL: GL.rectangle([rx - 30, by - 2, rx + 30, by + 42], outline=A(VGOLD, 1), width=8)
        if pb > 0.9: txt(d, rx + 70, my - 96, 'TELMISARTAN', f(MONOB, 22), VGOLD, appear(t, 58.2))
    # angiotensin II key approaches then deflects
    if t >= 58.32:
        q = clamp((t - 58.32) / 1.2); kx = lerp(x0 + 60, rx - 10, min(1, q * 1.4)); ky = lerp(y0 + 112, my - 150, min(1, q * 1.4))
        if q > 0.72: kx -= (q - 0.72) * 300; ky -= (q - 0.72) * 120
        tri = [(kx, ky + 40), (kx - 26, ky), (kx + 26, ky)]
        d.polygon(tri, fill=A(RED, 1)); txt(d, kx + 34, ky + 4, 'ANGIOTENSIN II', f(MONOB, 20), RED, 1 - clamp((q - 0.66) * 8))
        if q > 0.72: cross(d, rx - 14, my - 160, RED, 0.9, clamp((q - 0.72) * 5)); txt(d, rx + 30, my - 160, 'NO SIGNAL', f(MONOB, 22), RED, clamp((q - 0.72) * 5))
    # vessel (right half)
    vx0, vx1, vc = x0 + 520, x1 - 40, y0 + 210
    rel = ease_io((t - 61.5) / 0.6); r = lerp(38, 82, rel)
    for sgn in (-1, 1):
        pts = [(x, vc + sgn * (r + 10 * math.sin(x / 40 + t * 3) * (1 - rel) * 0.4)) for x in range(int(vx0), int(vx1), 8)]
        glowline(d, pts, RED if rel < 0.5 else GREEN, 7, 1, 14)
    for k in range(7):
        xx = vx0 + ((t * 160 * (0.6 + rel) + k * 60) % (vx1 - vx0)); d.ellipse([xx - 12, vc - 8, xx + 12, vc + 8], fill=A((200, 30, 40), 0.9))
    txt(d, vx0, y0 + 70, 'BLOOD VESSEL', f(MONO, 22), MUTED)
    if t >= 62.04: tag(d, vx0, y1 - 72, 'RELAXED', GREEN, 24, appear(t, 62.04))
    if t >= 63.06:
        aa = appear(t, 63.06); bx = vx1 - 120
        txt(d, bx, y1 - 74, 'BP', f(BEB, 52), WHITE, aa); arrow(d, bx + 70, y1 - 82, bx + 70, y1 - 26, GREEN, 8, aa, 22)

def sc_study(d, t):
    x0, y0, x1, y1 = P
    txt(d, x0 + 36, y0 + 64, 'CLINICAL EVIDENCE', f(MONO, 26), GOLD, appear(t, 64.0))
    p = expo((t - 64.05) / 0.22); dx0, dy0 = x0 + 36, y0 + 104 + (1 - p) * 40; dx1, dy1 = x0 + 560, y1 - 24
    d.rectangle([dx0, dy0, dx1, dy1], fill=A((208, 204, 196), p))
    d.rectangle([dx0, dy0, dx1, dy0 + 40], fill=A(COARED, p)); txt(d, dx0 + 14, dy0 + 8, 'STUDY SUMMARY', f(MONOB, 22), WHITE, p)
    rows = [('POPULATION', 'Hypertensive patients', 66.10), ('AGENT', 'Telmisartan', 64.5), ('OUTCOME', 'Regression of LV mass', 67.74)]
    for k, (lab, val, tt) in enumerate(rows):
        yy = dy0 + 56 + k * 62
        txt(d, dx0 + 14, yy, lab, f(MONO, 18), (90, 90, 96), p)
        if t >= tt:
            aa = appear(t, tt)
            if lab == 'OUTCOME':
                hw = d.textlength(val, font=f(DMB, 26)) * expo((t - tt) / 0.35)
                d.rectangle([dx0 + 10, yy + 22, dx0 + 18 + hw, yy + 56], fill=A(VGOLD, 0.85))
            txt(d, dx0 + 14, yy + 22, val, f(DMB, 26), (20, 20, 24), aa)
        else: redacted(d, dx0 + 14, yy + 28, 260, 22, p)
    # before / after hearts
    ha = appear(t, 68.74, 0.25)
    if ha > 0:
        heart(d, x0 + 690, y0 + 205, 5.2, 0.62, ha); heart(d, x0 + 860, y0 + 205, 5.2, lerp(0.62, 0.22, ease_io((t - 69.0) / 0.8)), ha, GREEN)
        txt(d, x0 + 690, y0 + 290, 'BEFORE', f(MONO, 20), MUTED, ha, 'mt'); txt(d, x0 + 860, y0 + 290, 'AFTER', f(MONO, 20), GREEN, ha, 'mt')
        arrow(d, x0 + 760, y0 + 205, x0 + 790, y0 + 205, CREAM, 3, ha, 12)
    if t >= 70.18:
        q = expo((t - 70.18) / 0.14); bx0 = x0 + 600; bx1 = lerp(bx0, x1 - 30, q)
        lit_bar(d, bx0, y1 - 80, bx1, y1 - 24, RED)
        if GL: GL.rectangle([bx0 - 3, y1 - 83, bx1 + 3, y1 - 21], outline=A(RED, 1), width=8)
        if q > 0.6: txt(d, bx0 + 16, y1 - 76, 'LV MASS', f(BEB, 48), WHITE); arrow(d, bx0 + 168, y1 - 70, bx0 + 168, y1 - 32, WHITE, 6, 1, 16); txt(d, bx0 + 188, y1 - 62, 'REVERSED', f(MONOB, 22), WHITE)

def sc_compare(d, t):
    x0, y0, x1, y1 = P
    txt(d, x0 + 36, y0 + 64, 'SIMPLIFIED', f(MONO, 26), GOLD, appear(t, 79.95))
    mx = (x0 + x1) / 2
    cols = [('EZETIMIBE', x0 + 36, 81.88, 'HIT 01 · LIPIDS'), ('TELMISARTAN', mx + 12, 84.16, 'HIT 02 · PRESSURE')]
    for k, (nm, cx0, tt, hit) in enumerate(cols):
        cx1 = cx0 + (mx - x0 - 48)
        p = expo((t - (80.1 + k * 0.12)) / 0.35)
        d.line([(cx0, y0 + 104), (lerp(cx0, cx1, p), y0 + 104)], fill=A(VGOLD, 1), width=5)
        if GL: GL.line([(cx0, y0 + 104), (lerp(cx0, cx1, p), y0 + 104)], fill=A(VGOLD, 1), width=10)
        aa = appear(t, tt); txt(d, cx0, y0 + 112, nm, f(BEB, 62), VGOLD if aa > 0 else (70, 70, 76), 1)
        txt(d, cx0, y0 + 178, hit, f(MONO, 22), MUTED, p)
        if aa > 0:
            d.rounded_rectangle([cx0, y0 + 214, cx1, y1 - 20], 12, fill=A((24, 27, 38), aa), outline=A((70, 66, 58), aa), width=2)
            txt(d, cx0 + 16, y0 + 226, 'TARGETS', f(MONO, 20), MUTED, aa)
    if t >= 82.2:
        aa = appear(t, 82.2); x = x0 + 52
        txt(d, x, y0 + 258, 'CHOLESTEROL', f(BARB, 40), WHITE, aa); txt(d, x, y0 + 302, 'ABSORPTION', f(BARB, 40), WHITE, aa)
    if t >= 84.88:
        aa = appear(t, 84.88); x = mx + 28
        txt(d, x, y0 + 258, 'BLOOD PRESSURE', f(BARB, 40), WHITE, aa)
        txt(d, x, y0 + 302, '+ ANGIOTENSIN', f(BARB, 40), WHITE, appear(t, 86.16))

def sc_rank(d, t):
    x0, y0, x1, y1 = P
    txt(d, x0 + 36, y0 + 64, 'PRIORITY STACK', f(MONO, 26), GOLD, appear(t, 87.65))
    flip = ease_io((t - 92.84) / 0.45)
    rows = [('SIZE', 89.42), ('STRENGTH', 90.60), ('LOOKS', 91.40)]
    rh = 70; top = y0 + 100
    for k, (lab, tt) in enumerate(rows):
        aa = appear(t, tt)
        if aa <= 0: continue
        yy = top + k * (rh + 8) + flip * (rh + 8) * 0.55 + (1 - aa) * 20
        dim = 1 - 0.55 * flip
        d.rounded_rectangle([x0 + 36, yy, x0 + 600, yy + rh * (1 - 0.3 * flip)], 10, fill=A((26, 29, 40), aa * dim), outline=A((70, 74, 90), aa * dim), width=2)
        txt(d, x0 + 56, yy + 10 - 6 * flip, f'0{k+1 + (1 if flip > 0.5 else 0)}', f(BEB, 50 - 14 * flip), MUTED, aa * dim)
        txt(d, x0 + 130, yy + 10 - 6 * flip, lab, f(BEB, 50 - 14 * flip), CREAM, aa * dim)
        if flip > 0.2:
            lx = x0 + 128; d.line([(lx, yy + rh * 0.36), (lx + lerp(0, 230, clamp((flip - 0.2) / 0.5)), yy + rh * 0.36)], fill=A(RED, aa), width=4)
    if t >= 92.84:
        p = expo((t - 92.84) / 0.3); yy = lerp(y1 + 20, y0 + 92, p)
        d.rounded_rectangle([x0 + 630, y0 + 96, x1 - 36, y1 - 24], 14, fill=A((40, 8, 12), p), outline=A(VGOLD, p), width=4)
        if GL: GL.rounded_rectangle([x0 + 630, y0 + 96, x1 - 36, y1 - 24], 14, outline=A(VGOLD, p), width=9)
        txt(d, x0 + 660, y0 + 110, '#1', f(BEB, 70), VGOLD, p)
        out = heart_pts(x0 + 830, y0 + 200, 3.3); d.polygon(out, fill=A(RED, p))
        if GL: GL.polygon(out, fill=A(RED, p))
        # ECG trace
        ex0 = x0 + 650; pts = []
        for i in range(60):
            u = i / 59; xx = lerp(ex0, x1 - 56, u); ph = (u * 2 - t * 1.2) % 1
            yv = -60 if 0.48 < ph < 0.5 else (30 if 0.5 < ph < 0.52 else (-14 if 0.2 < ph < 0.26 else 0))
            pts.append((xx, y1 - 70 + yv))
        glowline(d, pts, GREEN, 4, p, 10); txt(d, x0 + 660, y1 - 60, 'HEART', f(BEB, 50), WHITE, p) if False else None

def sc_pdf(d, t):
    x0, y0, x1, y1 = P
    txt(d, x0 + 36, y0 + 64, 'WHAT YOU GET', f(MONO, 26), GOLD, appear(t, 102.45))
    p = expo((t - 103.5) / 0.25); dx0, dy0 = x0 + 36, y0 + 100 + (1 - p) * 50
    dx1, dy1 = dx0 + 330, y1 - 20
    if p > 0:
        d.rectangle([dx0 + 10, dy0 + 10, dx1 + 10, dy1 + 6], fill=A((0, 0, 0), 0.5 * p))
        d.rectangle([dx0, dy0, dx1, dy1], fill=A((22, 25, 34), p), outline=A(GOLD, p), width=3)
        d.rectangle([dx0, dy0, dx0 + 6, dy1], fill=A(GOLD, p))
        txt(d, dx0 + 24, dy0 + 16, 'COACH AGZ', f(BEB, 30), GOLD, p)
        txt(d, dx0 + 24, dy0 + 52, 'CARDIOVASCULAR', f(BEB, 44), CREAM, p); txt(d, dx0 + 24, dy0 + 94, 'BLOODWORK', f(BEB, 44), CREAM, p); txt(d, dx0 + 24, dy0 + 136, 'BREAKDOWN', f(BEB, 44), VGOLD, p)
        for k in range(3): d.line([(dx0 + 24, dy0 + 196 + k * 16), (dx1 - 30 - k * 40, dy0 + 196 + k * 16)], fill=A((70, 74, 90), p), width=6)
    if t >= 105.46:
        q = expo((t - 105.46) / 0.14); s = lerp(1.6, 1.0, q)
        fn = f(BEB, int(54 * s)); lab = 'FREE'; tw = d.textlength(lab, font=fn)
        cx, cy = dx1 - 20, dy0 + 10
        d.rounded_rectangle([cx - tw / 2 - 16, cy - 30 * s, cx + tw / 2 + 16, cy + 34 * s], 8, fill=A(VGOLD, q))
        if GL: GL.rounded_rectangle([cx - tw / 2 - 18, cy - 32 * s, cx + tw / 2 + 18, cy + 36 * s], 8, outline=A(VGOLD, q), width=8)
        txt(d, cx, cy + 2, lab, fn, INK, q, 'mm')
    items = [('DOSAGES', 107.56), ('TIMING', 108.30), ('BEST COMPOUNDS', 109.30)]
    for k, (lab, tt) in enumerate(items):
        yy = y0 + 112 + k * 80; xx = x0 + 420
        aa = appear(t, tt - 0.3, 0.2)
        d.rounded_rectangle([xx, yy, xx + 46, yy + 46], 8, outline=A((90, 94, 110), max(aa, 0.35)), width=3)
        if t >= tt: check(d, xx + 8, yy + 6, GREEN, 1.0, appear(t, tt))
        txt(d, xx + 70, yy - 4, lab, f(BEB, 56), CREAM if t >= tt else (90, 92, 100), max(aa, 0.35))

PANEL_SCENES = [  # (t0, t1, fn, window kicker, window right label)
    (5.45, 13.62, sc_problem, 'THE PROBLEM', '2 HITS'),
    (20.00, 24.90, sc_bars, '01 · LIPIDS', 'ON CYCLE'),
    (24.90, 28.95, sc_lines, '01 · LIPIDS', 'ON CYCLE'),
    (29.10, 36.30, sc_ezet, '01 · THE FIX', 'EZETIMIBE'),
    (36.30, 43.75, sc_flow, '01 · THE FIX', 'EZETIMIBE'),
    (47.20, 53.20, sc_pressure, '02 · PRESSURE', 'REMODELING'),
    (57.90, 63.95, sc_receptor, '02 · THE FIX', 'TELMISARTAN'),
    (63.95, 70.95, sc_study, '02 · THE FIX', 'TELMISARTAN'),
    (79.90, 87.60, sc_compare, 'SIMPLIFIED', '2 COMPOUNDS'),
    (87.60, 95.00, sc_rank, 'THE GOAL', 'RE-RANKED'),
    (102.40, 111.40, sc_pdf, 'FREE BREAKDOWN', '@COACH.AGZ'),
]
# STAGE blocks = merged contiguous panel scenes
STAGES = []
for t0, t1, *_ in PANEL_SCENES:
    if STAGES and t0 - STAGES[-1][1] < 0.3: STAGES[-1][1] = t1
    else: STAGES.append([t0, t1])
def stage_amt(t):
    for t0, t1 in STAGES:
        if t0 - 0.3 <= t <= t1 + 0.3:
            return min(ease_io((t - t0 + 0.12) / 0.32), 1 - ease_io((t - t1 + 0.05) / 0.30))
    return 0.0

# ---------------- ROOF (FULL-mode) ELEMENTS ----------------
RY = 236   # roof top (safe zone below 250 for text)
def roof_hook(d, t):          # TEXT HOOK - frame 0, hold to 5.5, 0.15 fade
    if t >= 5.65: return
    a = 1 - clamp((t - 5.5) / 0.15)
    s = lerp(1.0, 1.04, clamp(t / 5.5))     # slow scale over the hold (one move)
    l1 = [('Your ', CREAM), ('HEART', VGOLD), (' on anabolics', CREAM)]; l2 = [('2 hits nobody manages', CREAM)]
    fn = f(BEB, int(96 * s)); cx = 510
    ys = [262, 262 + 96 * s]
    widths = [sum(d.textlength(w, font=fn) for w, _ in L) for L in (l1, l2)]
    bw = max(widths) + 60
    d.rounded_rectangle([cx - bw / 2, ys[0] - 18, cx + bw / 2, ys[1] + 104 * s], 22, fill=A((6, 8, 14), 0.82 * a))
    d.rectangle([cx - bw / 2, ys[0] - 18, cx - bw / 2 + 8, ys[1] + 104 * s], fill=A(GOLD, a))
    for L, y, wdt in zip((l1, l2), ys, widths):
        x = cx - wdt / 2
        for w, col in L:
            d.text((x, y), w, font=fn, fill=A(col, a));
            if col == VGOLD and GL: GL.text((x, y), w, font=fn, fill=A(VGOLD, a * 0.8))
            x += d.textlength(w, font=fn)

def roof_steps(d, t):
    if not (13.60 <= t < 18.0): return
    a = appear(t, 13.7, 0.2) * (1 - clamp((t - 17.85) / 0.15))
    labs = [('SCIENCE', 15.12), ('SIMPLIFY', 16.26), ('OPTIMIZE', 17.26)]
    xs = [170, 500, 830]; y = RY + 56
    d.rounded_rectangle([60, RY, 1000, RY + 170], 18, fill=A((6, 8, 14), 0.78 * a))
    for k in range(2):
        p = clamp((t - labs[k][1]) / (labs[k + 1][1] - labs[k][1]))
        d.line([(xs[k] + 40, y), (xs[k + 1] - 40, y)], fill=A((70, 74, 90), a), width=4)
        d.line([(xs[k] + 40, y), (lerp(xs[k] + 40, xs[k + 1] - 40, p), y)], fill=A(VGOLD, a), width=4)
    for k, (lab, tt) in enumerate(labs):
        on = t >= tt; p = appear(t, tt, 0.14)
        r = 36 + 6 * p * (1 - clamp((t - tt - 0.1) / 0.2))
        d.ellipse([xs[k] - r, y - r, xs[k] + r, y + r], fill=A(VGOLD if on else (24, 27, 38), a), outline=A(VGOLD, a), width=4)
        if GL and on: GL.ellipse([xs[k] - r - 4, y - r - 4, xs[k] + r + 4, y + r + 4], outline=A(VGOLD, a), width=8)
        txt(d, xs[k], y, f'0{k+1}', f(BEB, 44), INK if on else MUTED, a, 'mm')
        txt(d, xs[k], y + 50, lab, f(BEB, 46), CREAM if on else (90, 92, 100), a, 'mt')

def roof_chapter(d, t, t0, t1, num, label, tl, sub=None, ts=None):
    if not (t0 <= t < t1 + 0.2): return
    a = 1 - clamp((t - t1) / 0.18)
    p = expo((t - t0) / 0.22)
    d.rounded_rectangle([60, RY, 1000, RY + 170], 18, fill=A((6, 8, 14), 0.8 * a * p))
    nx = lerp(-200, 90, p); txt(d, nx, RY + 4, num, f(BEB, 170), VGOLD, a)
    if GL: GL.text((nx, RY + 4), num, font=f(BEB, 170), fill=A(VGOLD, a * 0.7))
    d.rectangle([300, RY + 30, 306, RY + 140], fill=A(GOLD, a * p))
    if t >= tl:
        q = expo((t - tl) / 0.16); fn = f(BEB, 92 if len(label) < 10 else 78)
        txt(d, 330 + (1 - q) * 40, RY + 22, label, fn, CREAM, a * q)
    if sub and t >= ts: txt(d, 334, RY + 122, sub, f(MONOB, 26), RED, a * appear(t, ts))

def roof_name(d, t):
    if not (53.20 <= t < 58.05): return
    a = 1 - clamp((t - 57.88) / 0.15)
    if t >= 54.42:
        p = expo((t - 54.42) / 0.3)
        d.rounded_rectangle([60, RY, 1000, RY + 176], 18, fill=A((6, 8, 14), 0.8 * a * p))
        d.line([(100, RY + 40), (lerp(100, 160, p), RY + 40)], fill=A(GOLD, a), width=4)
        txt(d, 176, RY + 24, 'MY #1 HEART COMPOUND', f(BARB, 36), GOLD, a * p)
    if t >= 56.90:
        q = expo((t - 56.90) / 0.12); s = lerp(1.35, 1.0, q)
        fn = f(BEB, int(110 * s)); tw = d.textlength('TELMISARTAN', font=fn)
        x = 530 - tw / 2; y = RY + 66 - (s - 1) * 50
        d.text((x, y), 'TELMISARTAN', font=fn, fill=A(VGOLD, a * q))
    else:
        redacted(d, 290, RY + 90, 480, 56, a * appear(t, 54.6))

def roof_bonus(d, t):
    if not (73.40 <= t < 80.0): return
    a = 1 - clamp((t - 79.85) / 0.15)
    items = [('+ INSULIN SENSITIVITY', 73.58, VGOLD, None), ('+ ANDROGEN RECEPTORS', 76.26, VGOLD, 'SOME STUDIES')]
    for k, (lab, tt, col, note) in enumerate(items):
        p = expo((t - tt) / 0.2)
        if p <= 0: continue
        y = RY + 6 + k * 84; x = lerp(-500, 80, p)
        fn = f(BARB, 46); tw = d.textlength(lab, font=fn)
        d.rounded_rectangle([x, y, x + tw + 40, y + 66], 10, fill=A((6, 8, 14), 0.85 * a), outline=A(col, a), width=3)
        if GL: GL.rounded_rectangle([x, y, x + tw + 40, y + 66], 10, outline=A(col, a), width=8)
        txt(d, x + 20, y + 6, lab, fn, col, a)
        if k == 1: arrow(d, x + tw + 70, y + 54, x + tw + 70, y + 14, GREEN, 7, a, 18)
        if note:
            na = a * appear(t, tt + 0.5); nw = d.textlength(note, font=f(MONOB, 22))
            d.rounded_rectangle([x + tw + 96, y + 14, x + tw + 124 + nw, y + 52], 8, fill=A((6, 8, 14), 0.85 * na)); txt(d, x + tw + 110, y + 20, note, f(MONOB, 22), CREAM, na)
    if t >= 78.58: tag(d, 80, RY + 186, 'SEPARATE VIDEO', RED, 24, appear(t, 78.58) * a)

def roof_clock(d, t):
    if not (97.90 <= t < 102.45): return
    a = appear(t, 97.9, 0.25) * (1 - clamp((t - 102.3) / 0.15))
    d.rounded_rectangle([60, RY, 1000, RY + 196], 18, fill=A((6, 8, 14), 0.8 * a))
    cx, cy, r = 160, RY + 98, 74
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=A(CREAM, a), width=4)
    for k in range(12):
        an = k * math.pi / 6; d.line([(cx + (r - 12) * math.sin(an), cy - (r - 12) * math.cos(an)), (cx + (r - 2) * math.sin(an), cy - (r - 2) * math.cos(an))], fill=A(CREAM, a), width=3)
    p = ease_io((t - 98.1) / 1.15)
    hr = lerp(3.5, 6.0, p); mn = lerp(30, 0, p) + (60 if p < 1 else 0) * 0
    ha = hr / 12 * 2 * math.pi; ma = (lerp(0.5, 1.0, p) * 2 * math.pi)
    d.line([(cx, cy), (cx + 40 * math.sin(ha), cy - 40 * math.cos(ha))], fill=A(VGOLD, a), width=7)
    d.line([(cx, cy), (cx + 60 * math.sin(ma), cy - 60 * math.cos(ma))], fill=A(CREAM, a), width=4)
    d.ellipse([cx - 7, cy - 7, cx + 7, cy + 7], fill=A(VGOLD, a))
    if GL: GL.ellipse([cx - r, cy - r, cx + r, cy + r], outline=A(VGOLD, a * 0.6), width=8)
    txt(d, 262, RY + 20, '6:00 PM', f(BEB, 70), VGOLD, a * appear(t, 99.26))
    days = 'MTWTFSS'
    for row, (lab, tt) in enumerate((('KIDS', 99.96), ('WIFE', 101.60))):
        y = RY + 104 + row * 46
        txt(d, 262, y, lab, f(MONOB, 24), CREAM, a * appear(t, tt - 0.6))
        for k, ch in enumerate(days):
            x = 360 + k * 84; on = t >= tt + k * 0.05
            d.rounded_rectangle([x, y - 2, x + 70, y + 36], 6, fill=A((14, 40, 24) if on else (24, 27, 38), a * appear(t, tt - 0.6)), outline=A(GREEN if on else (60, 62, 72), a * appear(t, tt - 0.6)), width=2)
            if on: check(d, x + 24, y + 4, GREEN, 0.75, a * appear(t, tt + k * 0.05))
            else: txt(d, x + 26, y + 2, ch, f(MONOB, 24), MUTED, a * appear(t, tt - 0.6))

LOGO = None
def roof_cta(d, im, t):
    if t < 111.40: return
    a = appear(t, 111.40, 0.25)
    d.rounded_rectangle([60, RY, 1000, RY + 230], 18, fill=A((6, 8, 14), 0.86 * a))
    d.rectangle([60, RY, 66, RY + 230], fill=A(GOLD, a))
    lg = LOGO.copy(); m = Image.new('L', lg.size, 0); ImageDraw.Draw(m).ellipse([0, 0, lg.size[0] - 1, lg.size[1] - 1], fill=int(255 * a))
    im.paste(lg, (96, RY + 40), m)
    d.ellipse([93, RY + 37, 249, RY + 193], outline=A(GOLD, a), width=4)
    txt(d, 270, RY + 22, 'COMMENT', f(BARB, 40), CREAM, a)
    p = expo((t - 111.86) / 0.18); s = lerp(1.25, 1.0, p)
    fn = f(BEB, int(110 * s)); lab = '"HEALTH"'; tw = d.textlength(lab, font=fn)
    if p > 0:
        x0 = 266; y0 = RY + 70 - (s - 1) * 40
        lit_bar(d, x0, y0, x0 + tw + 40, y0 + 120 * s, VGOLD, p)
        if GL: GL.rectangle([x0 - 4, y0 - 4, x0 + tw + 44, y0 + 124 * s], outline=A(VGOLD, p), width=10)
        txt(d, x0 + 20, y0 + 6, lab, fn, INK, p)
    if t >= 113.22: txt(d, 270, RY + 196, "I'LL SEND IT · FREE", f(MONOB, 24), GOLD, appear(t, 113.22) * a)

# ---------------- captions ----------------
EMPH = {'HDL', 'LDL', 'APOB', 'EZETIMIBE', 'TELMISARTAN', 'HEART', 'NPC1L1', 'AT1', 'TRT', 'ANABOLICS', 'HEALTH', 'LIPIDS', 'PRESSURE', 'HYPERTROPHY', 'FAMILY', '6PM', 'FREE'}
def build_groups():
    G = []; cur = []
    def nb(tt):
        for b0, b1 in BOUNDS:
            if b0 > tt + 0.01: return b0
        return 1e9
    for i, x in enumerate(WORDS):
        if cur:
            prev = WORDS[cur[-1]]
            n_chars = sum(len(WORDS[j]['w']) for j in cur) + len(x['w'])
            if len(cur) >= 3 or n_chars > 20 or x['s'] - prev['e'] > 0.28 or prev['w'][-1] in '.,?!' or x['s'] >= nb(prev['e']): G.append(cur); cur = []
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
    end = WORDS[lo[-1]]['e'] + 0.5
    nxt = [g for g in GROUPS if WORDS[g[0]]['s'] > WORDS[lo[0]]['s']]
    if t > end and (not nxt or WORDS[nxt[0][0]]['s'] > t): return None
    return lo
def clean(w): return w.upper().strip('.,?!')
def captions(im, t):
    g = group_at(t)
    if not g: return
    d = ImageDraw.Draw(im, 'RGBA')
    ws = [clean(WORDS[i]['w']) for i in g]
    size = 104
    while True:
        fn = f(BEB, size); sp = d.textlength(' ', font=fn) + 12; wd = [d.textlength(w, font=fn) for w in ws]; tot = sum(wd) + sp * (len(ws) - 1)
        if tot <= 860: break
        size -= 4
    xs = []; x = (W - 80 - tot) / 2 + 20
    for w_ in wd: xs.append(x); x += w_ + sp
    act = 0
    for k, i in enumerate(g):
        if WORDS[i]['s'] <= t: act = k
    g0 = WORDS[g[0]]['s']; s = lerp(0.92, 1, expo((t - g0) / 0.10))
    ch = 200; top = CAP_Y - size / 2 - 40
    cap = Image.new('RGBA', (W, ch), (0, 0, 0, 0)); cd = ImageDraw.Draw(cap); shd = Image.new('RGBA', (W, ch), (0, 0, 0, 0)); sd = ImageDraw.Draw(shd)
    prev = max(0, act - 1); bt = expo((t - WORDS[g[act]]['s']) / 0.07) if act > 0 else 1
    bx0 = lerp(xs[prev], xs[act], bt) - 16; bx1 = lerp(xs[prev] + wd[prev], xs[act] + wd[act], bt) + 16
    for k, (w_, x_) in enumerate(zip(ws, xs)): sd.text((x_ + 4, 46), w_, font=fn, fill=(0, 0, 0, 230))
    cap.alpha_composite(shd.filter(ImageFilter.GaussianBlur(7)))
    lit_bar(cd, bx0, 40 + size * 0.02, bx1, 40 + size * 0.98, RED)
    for k, (w_, x_) in enumerate(zip(ws, xs)):
        col = CREAM if (k == act or w_ not in EMPH) else VGOLD
        cd.text((x_, 40), w_, font=fn, fill=col, stroke_width=0 if k == act else 3, stroke_fill=(0, 0, 0))
    if abs(s - 1) > 0.002:
        cap = cap.resize((int(W * s), int(ch * s)), Image.BICUBIC); ox = int((W - cap.width) / 2); oy = int(top - (cap.height - ch) / 2)
    else: ox, oy = 0, int(top)
    im.alpha_composite(cap, (ox, oy))

# ---------------- background + footage ----------------
def make_bg():
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    base = np.zeros((H, W, 3), np.float32) + np.array(NAVY, np.float32)
    g = np.exp(-(((xx - 980) / 700) ** 2 + ((yy - 200) / 800) ** 2)) * 22; base += g[..., None] * np.array([1.0, 0.85, 0.55])
    grid = ((xx % 60) < 1.5) | ((yy % 60) < 1.5); base[grid] += 7
    return Image.fromarray(np.clip(base, 0, 255).astype(np.uint8))
BG = None
def seg_of(t):
    for i, (b0, b1) in enumerate(BOUNDS):
        if b0 <= t < b1: return i
    return len(BOUNDS) - 1
def zoom_full(t):
    if t < 3.0: return lerp(1.0, 1.06, ease_io((t - 1.62) / 0.3))   # visual hook: lands on "cardiovascular"
    return 1.0 if seg_of(t) % 2 == 0 else 1.07
def compose_footage(src, t, st):
    z = zoom_full(t)
    fs = (W / z, H / z); fx = (W - fs[0]) / 2; fy = (H - fs[1]) * 0.35
    full_src = (fx, fy, fx + fs[0], fy + fs[1]); full_dst = (0, 0, W, H)
    stage_src = (0, SRC_Y0, W, SRC_Y0 + SRC_H); stage_dst = WIN
    e = st if st > 0.004 else 0.0
    if e == 0.0: return src.resize((W, H), Image.BICUBIC, box=full_src).convert('RGBA')
    sr = tuple(lerp(a, b, e) for a, b in zip(full_src, stage_src)); dr = tuple(lerp(a, b, e) for a, b in zip(full_dst, stage_dst))
    dw, dh = int(round(dr[2] - dr[0])), int(round(dr[3] - dr[1]))
    crop = src.resize((dw, dh), Image.BICUBIC, box=sr)
    if e <= 0.001: return crop.convert('RGBA')
    im = BG.copy().convert('RGBA')
    d = ImageDraw.Draw(im, 'RGBA')
    # moving scan line in background
    m = Image.new('L', (dw, dh), 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, dw - 1, dh - 1], int(28 * e), fill=255)
    sh = Image.new('RGBA', (W, H), (0, 0, 0, 0)); ImageDraw.Draw(sh).rounded_rectangle([dr[0] + 10, dr[1] + 18, dr[2] + 10, dr[3] + 18], 30, fill=(0, 0, 0, int(160 * e)))
    im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(14)))
    im.paste(crop, (int(round(dr[0])), int(round(dr[1]))), m)
    return im

def window_chrome(d, t, st, sc):
    if st < 0.6: return
    a = clamp((st - 0.6) / 0.4)
    x0, y0, x1, y1 = WIN
    d.rounded_rectangle([x0, y0, x1, y1], 28, outline=A(VGOLD, 0.75 * a), width=3); brackets(d, x0 - 8, y0 - 8, x1 + 8, y1 + 8, A(VGOLD, a), 44, 6)
    if GL: brackets(GL, x0 - 8, y0 - 8, x1 + 8, y1 + 8, A(VGOLD, a), 44, 12)
    if sc:
        k, r = sc[3], sc[4]
        fn = f(MONOB, 26); kw = d.textlength(k, font=fn); rw = d.textlength(r, font=fn)
        d.rounded_rectangle([x0 + 18, y1 - 64, x0 + 66 + kw, y1 - 18], 10, fill=A((6, 8, 14), 0.85 * a))
        d.ellipse([x0 + 32, y1 - 49, x0 + 46, y1 - 35], fill=A(RED, a if int(t * 4) % 2 == 0 else a / 3))
        txt(d, x0 + 56, y1 - 58, k, fn, WHITE, a)
        d.rounded_rectangle([x1 - 48 - rw, y1 - 64, x1 - 18, y1 - 18], 10, fill=A((6, 8, 14), 0.85 * a))
        txt(d, x1 - 33 - rw, y1 - 58, r, fn, VGOLD, a)
    txt(d, x0 + 4, y1 + 12, 'FOR RESEARCH & EDUCATIONAL PURPOSES ONLY', f(MONO, 16), MUTED, a)

def panel(im, t, st):
    if st < 0.02: return None
    x0, y0, x1, y1 = P
    a = clamp((st - 0.45) / 0.55); yo = (1 - a) * 90
    if a <= 0: return None
    d = ImageDraw.Draw(im, 'RGBA')
    d.rounded_rectangle([x0, y0 + yo, x1, y1 + yo], 22, fill=A(PANELC, 0.96 * a), outline=A((58, 54, 48), a), width=2)
    d.rectangle([x0, y0 + 20 + yo, x0 + 7, y1 - 20 + yo], fill=A((200, 16, 46), a))       # crimson bar
    txt(d, x1 - 150, y1 - 30 + yo, '@COACH.AGZ', f(MONO, 18), MUTED, a * 0.8)
    sc = None
    for s_ in PANEL_SCENES:
        if s_[0] <= t < s_[1] + 0.12: sc = s_
    if sc and st > 0.5:
        lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); dl = ImageDraw.Draw(lay, 'RGBA')
        sc[2](dl, t)
        al = appear(t, sc[0], 0.2) * (1 - clamp((t - sc[1]) / 0.12)) * clamp((st - 0.5) / 0.5)
        if al < 1: lay.putalpha(lay.split()[3].point(lambda v: int(v * al)))
        im.alpha_composite(lay)
    return sc

IMPACTS = [56.90, 70.18, 31.24]
def frame(src, t):
    global GL
    st = stage_amt(t)
    im = compose_footage(src, t, st)
    # readability gradient under captions (FULL mode only, footage untouched elsewhere)
    if st < 1:
        yy = np.arange(H); a = np.clip((yy - 1360) / 140, 0, 1) * 95 * (1 - st)
        a2 = np.where(yy < 470, np.clip((470 - yy) / 260, 0, 1) * 70, 0) * (1 - st)
        al = np.maximum(a, a2).astype(np.uint8)
        im.alpha_composite(Image.merge('RGBA', [Image.new('L', (W, H), c) for c in INK] + [Image.fromarray(np.repeat(al[:, None], W, 1))]))
    glow = Image.new('RGBA', (W, H), (0, 0, 0, 0)); GL = ImageDraw.Draw(glow, 'RGBA')
    sc = panel(im, t, st)
    d = ImageDraw.Draw(im, 'RGBA')
    window_chrome(d, t, st, sc)
    if st < 0.5:
        roof_hook(d, t); roof_steps(d, t)
        roof_chapter(d, t, 17.96, 20.0, '01', 'LIPIDS', 19.26)
        roof_chapter(d, t, 43.90, 47.2, '02', 'BLOOD PRESSURE', 44.58, '+ CARDIOVASCULAR REMODELING', 45.56)
        roof_name(d, t); roof_bonus(d, t); roof_clock(d, t); roof_cta(d, im, t)
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
    for ti in IMPACTS:          # 2-frame recoil on heavy impacts
        k = round((t - ti) * FPS)
        if k in (0, 1):
            dx = [9, -5][k]; z = 1.02; big = out.resize((int(W * z), int(H * z)), Image.BICUBIC); ox = (big.width - W) // 2 - dx; oy = (big.height - H) // 2
            out = big.crop((ox, oy, ox + W, oy + H)); ImageDraw.Draw(out).rectangle([0, 0, 7, H], fill=GOLD)
    return out

def init():
    global BG, LOGO
    BG = make_bg()
    LOGO = Image.open(S + '/logo.jpg').convert('RGB').resize((150, 150), Image.LANCZOS)

if __name__ == "__main__" and sys.argv[2] != "x":
    init()
    mode = sys.argv[2]
    if mode == 'stills':
        outdir = sys.argv[3]
        for tt in [float(x) for x in sys.argv[4:]]:
            n = int(round(tt * FPS))
            subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', f'{n/FPS:.4f}', '-i', T + 'assembled.mp4', '-frames:v', '1', outdir + '/_src.png'])
            frame(Image.open(outdir + '/_src.png').convert('RGB'), n / FPS).save(outdir + f'/st_{tt:07.2f}.jpg', quality=88)
        sys.exit()
    n0, n1 = int(sys.argv[3]), int(sys.argv[4]); out = sys.argv[5]
    dec = subprocess.Popen(['ffmpeg', '-v', 'error', '-ss', f'{n0/FPS:.4f}', '-i', T + 'assembled.mp4', '-frames:v', str(n1 - n0), '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], stdout=subprocess.PIPE)
    enc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-crf', '12', '-preset', 'veryfast', '-pix_fmt', 'yuv420p', out], stdin=subprocess.PIPE)
    for n in range(n0, n1):
        buf = dec.stdout.read(W * H * 3)
        if len(buf) < W * H * 3: print('short', n); break
        enc.stdin.write(frame(Image.frombuffer('RGB', (W, H), buf), n / FPS).tobytes())
    enc.stdin.close(); enc.wait(); dec.kill(); print('done', n0, n1)
