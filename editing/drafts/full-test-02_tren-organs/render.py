# Coach AGZ - "Tren without shitting out your organs" - full test 02 renderer (1080x1920, 30 fps)
# usage: python3 render.py <workdir> stills t1 t2 ...    |   python3 render.py <workdir> chunk n0 n1 out.mp4
# <workdir> holds assembled.mp4, words_final.json, cut.json and fonts/ (stand-ins, see README)
import json, subprocess, sys, math
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

T = sys.argv[1].rstrip('/') + '/'
F = T + 'fonts/'
W, H = 1080, 1920; FPS = 30
CUT = json.load(open(T + 'cut.json')); DUR = CUT['dur']; HOLD = 0.5; TOTAL = DUR + HOLD
WORDS = json.load(open(T + 'words_final.json'))
LOGO_PATH = T + 'logo.jpg'

# ---------------- palette (BRAND.md + test-06 overlay accents) ----------------
GOLD = (201, 169, 110); CREAM = (244, 241, 234); NAVY = (14, 17, 23); PANEL = (24, 26, 34)
RED = (255, 34, 28); VGOLD = (255, 194, 26); CYAN = (0, 229, 255); GREEN = (30, 255, 110)
DEEP = (2, 3, 8); INK = (6, 8, 14); WHITE = (255, 255, 255); MUTED = (184, 184, 188); COARED = (210, 10, 20)
AMBER = (240, 160, 48); DIM = (70, 74, 90)
BEB = 'BebasNeue.woff'; BAR = 'Barlow-700.woff'; BAR8 = 'Barlow-800.woff'; DMB = 'DMSans-700.woff'; DMR = 'DMSans-400.woff'
MONO = 'JBMono-700.ttf'; MONOM = 'JBMono-500.ttf'
_fc = {}
def f(n, s):
    k = (n, int(s))
    if k not in _fc: _fc[k] = ImageFont.truetype(F + n, int(s))
    return _fc[k]

def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def expo(x): x = clamp(x); return 1 if x >= 1 else 1 - 2 ** (-10 * x)
def ease_io(x): x = clamp(x); return 4 * x ** 3 if x < .5 else 1 - (-2 * x + 2) ** 3 / 2
def back(x):  # heavy settle: tiny overshoot only (no bounce)
    x = clamp(x); c = 1.2; return 1 + (c + 1) * (x - 1) ** 3 + c * (x - 1) ** 2
def lerp(a, b, t): return a + (b - a) * t
def A(c, a): return tuple(int(v) for v in c[:3]) + (int(clamp(a) * 255),)
def mix(c1, c2, t): return tuple(int(lerp(a, b, clamp(t))) for a, b in zip(c1, c2))
def appear(t, t0, d=0.16): return expo((t - t0) / d)
def life(t, t0, t1, din=0.18, dout=0.16):
    """alpha for an element living t0..t1 (fade in from t0, fade out ending at t1)"""
    if t < t0 or t > t1: return 0.0
    return min(expo((t - t0) / din), clamp((t1 - t) / dout))

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
        d.line([(x0, y0 + i), (x1, y0 + i)], fill=c + (int(255 * clamp(a)),))
def tag(d, x, y, label, col=RED, size=30, a=1.0, glow=True, anchor='l'):
    fn = f(MONO, size); tw = d.textlength(label, font=fn); h = size + 16
    if anchor == 'c': x = x - (tw + 24) / 2
    if anchor == 'r': x = x - (tw + 24)
    lit_bar(d, x, y, x + tw + 24, y + h, col, a)
    d.text((x + 12, y + 6), label, font=fn, fill=A(INK if col in (VGOLD, GREEN, CYAN, GOLD) else WHITE, a))
    if GL and glow: GL.rectangle([x - 4, y - 4, x + tw + 28, y + h + 4], outline=A(col, a), width=8)
    return x + tw + 24
def check(d, x, y, col, s=1.0, a=1.0, p=1.0):
    pts = [(x, y + 16 * s), (x + 10 * s, y + 28 * s), (x + 30 * s, y + 2 * s)]
    if p < 0.5: pts = [pts[0], (lerp(pts[0][0], pts[1][0], p * 2), lerp(pts[0][1], pts[1][1], p * 2))]
    elif p < 1: q = (p - 0.5) * 2; pts = [pts[0], pts[1], (lerp(pts[1][0], pts[2][0], q), lerp(pts[1][1], pts[2][1], q))]
    d.line(pts, fill=A(col, a), width=max(2, int(6 * s)), joint='curve')
    if GL: GL.line(pts, fill=A(col, a), width=max(3, int(12 * s)))
def cross(d, x, y, col, s=1.0, a=1.0):
    d.line([(x, y), (x + 28 * s, y + 28 * s)], fill=A(col, a), width=int(6 * s)); d.line([(x + 28 * s, y), (x, y + 28 * s)], fill=A(col, a), width=int(6 * s))
    if GL: GL.line([(x, y), (x + 28 * s, y + 28 * s)], fill=A(col, a), width=12); GL.line([(x + 28 * s, y), (x, y + 28 * s)], fill=A(col, a), width=12)
def arrow(d, x0, y0, x1, y1, col, w=5, a=1.0, L=18):
    d.line([(x0, y0), (x1, y1)], fill=A(col, a), width=w)
    ang = math.atan2(y1 - y0, x1 - x0)
    d.polygon([(x1, y1), (x1 - L * math.cos(ang - 0.45), y1 - L * math.sin(ang - 0.45)), (x1 - L * math.cos(ang + 0.45), y1 - L * math.sin(ang + 0.45))], fill=A(col, a))
def warn_icon(d, x, y, s, col, a=1.0):
    d.polygon([(x + s / 2, y), (x + s, y + s * 0.9), (x, y + s * 0.9)], outline=A(col, a), fill=None, width=4)
    d.line([(x + s / 2, y + s * 0.3), (x + s / 2, y + s * 0.6)], fill=A(col, a), width=5); d.ellipse([x + s / 2 - 3, y + s * 0.7, x + s / 2 + 3, y + s * 0.76], fill=A(col, a))
def txt(d, x, y, s, font, col, a=1.0, anchor=None):
    d.text((x, y), s, font=font, fill=A(col, a), anchor=anchor)
def ctext(d, cx, y, s, font, col, a=1.0):
    tw = d.textlength(s, font=font); d.text((cx - tw / 2, y), s, font=font, fill=A(col, a))
def frosted(im, box, dark=0.86, blur=10, radius=0):
    x0, y0, x1, y1 = [int(v) for v in box]
    x0 = max(0, x0); y0 = max(0, y0); x1 = min(W, x1); y1 = min(H, y1)
    if x1 <= x0 or y1 <= y0: return
    reg = im.crop((x0, y0, x1, y1)).convert('RGB').filter(ImageFilter.GaussianBlur(blur))
    reg = Image.blend(reg, Image.new('RGB', reg.size, DEEP), dark).convert('RGBA')
    if radius:
        m = Image.new('L', reg.size, 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, reg.width - 1, reg.height - 1], radius=radius, fill=255)
        im.paste(reg, (x0, y0), m)
    else: im.paste(reg, (x0, y0))
def counter(v0, v1, p): return int(round(lerp(v0, v1, ease_io(p))))

# ---------------- word timing helpers ----------------
def wt(word, after=0.0, nth=0):
    """start time of the nth occurrence of word (case-insens, punctuation stripped) at/after `after`"""
    k = 0
    for x in WORDS:
        if x['s'] >= after - 1e-6 and x['w'].lower().strip('.,?!') == word.lower():
            if k == nth: return x['s']
            k += 1
    raise KeyError(word)

# ======================================================================================
# SCENES  (output-time).  Each returns nothing; draws into d (overlay layer), may use im.
# 'lower' scenes occupy the lower band (y 1130-1580) -> captions lift above them.
# ======================================================================================
PANEL = (50, 1150, 950, 1565)

def hud_frame(im, d, box, al, hl, hr, col=VGOLD):
    x0, y0, x1, y1 = box
    d.rectangle([x0, y0, x1, y1], outline=A(col, 0.75 * al), width=3); brackets(d, x0, y0, x1, y1, A(col, al), 44, 7)
    if GL: GL.rectangle([x0, y0, x1, y1], outline=A(col, 0.45 * al), width=6); brackets(GL, x0, y0, x1, y1, A(col, al), 44, 14)
    d.ellipse([x0 + 24, y0 + 25, x0 + 40, y0 + 41], fill=A(RED, al))
    txt(d, x0 + 54, y0 + 16, hl, f(MONO, 28), WHITE, al)
    fr = f(MONO, 26); tw = d.textlength(hr, font=fr); txt(d, x1 - 28 - tw, y0 + 18, hr, fr, col, al)

# ---- S0 text hook (frame 0) + topic band ----
HOOK_END = 5.10
def text_hook(im, t):
    if t > HOOK_END + 0.15: return
    a = 1.0 if t <= HOOK_END else 1 - (t - HOOK_END) / 0.15
    s = lerp(1.0, 1.04, clamp(t / HOOK_END))  # one slow move over the hold
    lay = Image.new('RGBA', (W, 300), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    l1 = [('3 ', CREAM), ('TREN', VGOLD), (' rules', CREAM)]; l2 = [('before your organs pay', CREAM)]
    size = 112
    while max(sum(d.textlength(p, font=f(BEB, size)) for p, _ in l) for l in (l1, l2)) > 780: size -= 2
    fn = f(BEB, size)
    bw = max(sum(d.textlength(p, font=fn) for p, _ in l) for l in (l1, l2)) + 80
    cx = 500; bh = int(size * 2 * 0.98 + 50)
    d.rounded_rectangle([cx - bw / 2, 10, cx + bw / 2, 10 + bh], radius=26, fill=A(DEEP, 0.86))
    d.rectangle([cx - bw / 2, 10 + 26, cx - bw / 2 + 7, 10 + bh - 26], fill=A(VGOLD, 1))
    for li, l in enumerate((l1, l2)):
        tw = sum(d.textlength(p, font=fn) for p, _ in l); x = cx - tw / 2; y = 30 + li * size * 0.98
        for p, c in l:
            d.text((x, y), p, font=fn, fill=c + (255,)); x += d.textlength(p, font=fn)
    if s != 1: lay = lay.resize((int(W * s), int(300 * s)), Image.BICUBIC)
    if a < 1: lay.putalpha(lay.split()[3].point(lambda v: int(v * a)))
    im.alpha_composite(lay, (int((W - lay.width) / 2 + (1 - s) * 0), int(262 - (lay.height - 300) / 2)))

BAND_END = 52.367  # midpoint snapped to the jump cut at 52.37
def topic_band(d, t):
    if t < HOOK_END + 0.12 or t > BAND_END: return
    a = min(clamp((t - HOOK_END - 0.12) / 0.15), clamp((BAND_END - t) / 0.15))
    y0, y1 = 236, 334
    d.rectangle([8, y0, W, y1], fill=A(NAVY, 0.9 * a))
    d.line([(36, y0 + 26), (70, y0 + 26)], fill=A(GOLD, a), width=4); txt(d, 80, y0 + 12, '@coach.agz', f(MONO, 24), GOLD, a)
    fn = f(BEB, 66); x = 36; y = y0 + 38
    for p, c in [('TREN', VGOLD), (' without the organ damage', CREAM)]:
        d.text((x, y), p, font=fn, fill=A(c, a)); x += d.textlength(p, font=fn)

# ---- S1 the 01/02/03 rail grown out of the gold edge rule ----
RAIL = [(5.08, 'DOSE', 10.05), (5.20, 'CARDIO', 25.36), (5.32, 'SIDES', 41.30)]
def rail(d, t):
    if t < 5.0 or t > BAND_END: return
    a = clamp((BAND_END - t) / 0.15)
    for i, (ta, lab, tact) in enumerate(RAIL):
        p = expo((t - ta) / 0.22)
        if p <= 0: continue
        cy = 610 + i * 118; cx = lerp(-30, 66, p)
        d.line([(8, cy), (cx - 30, cy)], fill=A(GOLD, a * p), width=3)
        if i < 2 and t > ta + 0.1:
            d.line([(cx, cy + 32), (cx, cy + 86)], fill=A(GOLD, 0.5 * a), width=2)
        nxt = RAIL[i + 1][2] if i < 2 else 1e9
        active = tact <= t < nxt; done = t >= nxt
        mistake = (i == 2 and 6.66 <= t < 10.05)
        col = RED if mistake else VGOLD
        if active or mistake:
            pulse = 0.75 + 0.25 * math.sin(t * 9) if mistake else 1
            d.ellipse([cx - 32, cy - 32, cx + 32, cy + 32], fill=A(col, a * pulse))
            if GL: GL.ellipse([cx - 38, cy - 38, cx + 38, cy + 38], outline=A(col, a), width=10)
            ctext(d, cx, cy - 26, f'0{i + 1}', f(BEB, 52), INK, a)
        else:
            d.ellipse([cx - 30, cy - 30, cx + 30, cy + 30], fill=A(DEEP, 0.88 * a * p), outline=A(GOLD, (0.55 if not done else 0.9) * a * p), width=3)
            ctext(d, cx, cy - 25, f'0{i + 1}', f(BEB, 50), GOLD if done else CREAM, a * p * (0.7 if not done else 1))
        if active:
            q = appear(t, tact, 0.2)
            tag(d, lerp(cx + 10, cx + 46, q), cy - 22, lab, VGOLD, 28, a * q)
        if mistake and t >= 9.27:
            tag(d, cx + 46, cy - 22, 'MISTAKE', RED, 28, a * appear(t, 9.27, 0.12))

# ---- S2 receptor docking scan -> diminishing-returns line graph ----
def steroid(d, cx, cy, s, col, a, w=4):
    """four fused rings (A-B-C hexagons + D pentagon), line-art"""
    r = 26 * s; pts_all = []
    def hexp(x, y): return [(x + r * math.cos(math.pi / 3 * k + math.pi / 6), y + r * math.sin(math.pi / 3 * k + math.pi / 6)) for k in range(6)]
    dx = r * math.sqrt(3)
    rings = [hexp(cx - dx, cy + r * 0.5), hexp(cx, cy), hexp(cx + dx, cy - r * 0.5 + r * 0.0 - r * 0.5 + r * 0.5)]
    for p in rings: d.line(p + [p[0]], fill=A(col, a), width=w); pts_all += p
    px, py = cx + dx * 1.85, cy - r * 0.55
    pent = [(px + r * 0.9 * math.cos(2 * math.pi / 5 * k + math.pi), py + r * 0.9 * math.sin(2 * math.pi / 5 * k + math.pi)) for k in range(5)]
    d.line(pent + [pent[0]], fill=A(col, a), width=w)
    if GL:
        for p in rings: GL.line(p + [p[0]], fill=A(col, a), width=w * 2)
        GL.line(pent + [pent[0]], fill=A(col, a), width=w * 2)
def scene_receptor(im, d, t):
    t0, t1 = 13.40, 20.55
    al = life(t, t0, t1, 0.2, 0.16)
    if al <= 0: return
    graph = t >= 17.55
    hud_frame(im, d, PANEL, al, 'DOSE vs MUSCLE' if graph else 'RECEPTOR SCAN', 'ILLUSTRATIVE' if graph else 'TREN · AR')
    x0, y0, x1, y1 = PANEL
    if not graph or t < 17.75:
        a = al * (1 - clamp((t - 17.55) / 0.2))
        # scan grid
        for gx in range(x0 + 40, x1 - 20, 40): d.line([(gx, y0 + 70), (gx, y1 - 20)], fill=A(CYAN, 0.06 * a))
        sy = y0 + 70 + ((t * 260) % (y1 - y0 - 90)); d.line([(x0 + 10, sy), (x1 - 10, sy)], fill=A(CYAN, 0.35 * a), width=2)
        # receptor pocket (right)
        rx, ry = 700, 1330
        d.rounded_rectangle([rx - 150, ry - 120, rx + 150, ry + 120], radius=70, outline=A(CYAN, a), width=5)
        d.rounded_rectangle([rx - 150, ry - 46, rx - 40, ry + 46], radius=20, fill=A(DEEP, a), outline=None)
        d.line([(rx - 150, ry - 46), (rx - 40, ry - 46), (rx - 40, ry + 46), (rx - 150, ry + 46)], fill=A(CYAN, a), width=5)
        if GL: GL.rounded_rectangle([rx - 150, ry - 120, rx + 150, ry + 120], radius=70, outline=A(CYAN, a), width=10)
        ctext(d, rx + 40, ry - 20, 'ANDROGEN', f(BEB, 40), CYAN, a); ctext(d, rx + 40, ry + 18, 'RECEPTOR', f(BEB, 40), CYAN, a)
        # TREN molecule docks on "agonist"
        tdock = wt('agonist', 15); p = expo((t - 14.0) / 0.25) * 0.55 + 0.45 * expo((t - tdock) / 0.18)
        mx = lerp(150, 470, p) if t >= 14.0 else 150; my = 1330
        steroid(d, mx, my, 1.0, VGOLD, a * appear(t, 13.53, 0.2))
        txt(d, mx - 70, my + 50, 'TREN', f(MONO, 26), VGOLD, a * appear(t, 13.53, 0.2))
        if t >= tdock:
            k = clamp((t - tdock) / 0.45); r = lerp(40, 170, k)
            d.ellipse([rx - 95 - r, ry - r, rx - 95 + r, ry + r], outline=A(CYAN, a * (1 - k)), width=4)
            tag(d, 560, 1478, 'AGONIST · BOUND', CYAN, 26, a * appear(t, tdock + 0.05, 0.12))
        # binding strength meter
        tpot = wt('potent', 13); q = expo((t - tpot) / 0.5)
        txt(d, 100, 1222, 'BINDING STRENGTH', f(MONO, 24), CREAM, a * appear(t, tpot - 0.1))
        d.rectangle([100, 1256, 420, 1276], outline=A(DIM, a), width=2)
        if q > 0: lit_bar(d, 103, 1259, lerp(103, 417, 0.94 * q), 1273, VGOLD, a)
        if q > 0.8: txt(d, 430, 1248, 'HIGH', f(BEB, 36), VGOLD, a)
        # more androgenic exposure -> extra molecules bounce off a full receptor
        tm = wt('androgenic', 15)
        for k in range(3):
            tk_ = tm + 0.12 * k; pp = clamp((t - tk_) / 0.5)
            if pp <= 0: continue
            bx = lerp(160, 400, expo(pp)) - (0 if pp < 0.6 else (pp - 0.6) * 90); by = 1250 + k * 90 - 60
            steroid(d, bx, by + (k - 1) * 25, 0.55, RED if pp > 0.6 else VGOLD, a * 0.9, 3)
        if t >= wt('exposure', 15): tag(d, 100, 1478, 'SATURATED', VGOLD, 26, a * appear(t, wt('exposure', 15), 0.12))
    if graph:
        a = al * clamp((t - 17.6) / 0.2)
        gx0, gy0, gx1, gy1 = 130, 1240, 900, 1500
        pa = expo((t - 17.6) / 0.25)
        d.line([(gx0, gy1), (lerp(gx0, gx1, pa), gy1)], fill=A(CREAM, a), width=3); d.line([(gx0, gy1), (gx0, lerp(gy1, gy0, pa))], fill=A(CREAM, a), width=3)
        txt(d, gx1 - 110, gy1 + 10, 'DOSE →', f(MONO, 24), CREAM, a); txt(d, gx0 + 12, gy0 - 8, 'MUSCLE', f(MONO, 24), CREAM, a)
        # expected (linear, dashed cyan)
        te = wt('guarantee', 17); pe = clamp((t - te) / 0.45)
        n = 26
        for k in range(int(n * pe)):
            if k % 2: continue
            u0, u1 = k / n, (k + 1) / n
            d.line([(lerp(gx0, gx1, u0), lerp(gy1, gy0 + 10, u0)), (lerp(gx0, gx1, u1), lerp(gy1, gy0 + 10, u1))], fill=A(CYAN, a), width=4)
        if pe >= 1: txt(d, gx0 + 330, gy0 + 4, 'EXPECTED', f(MONO, 24), CYAN, a)
        # actual (plateau, gold)
        ta = wt('proportionally', 17); pa2 = clamp((t - ta) / 0.8)
        def yc(u): return gy1 - (gy1 - gy0) * 0.56 * (1 - math.exp(-4.2 * u)) / (1 - math.exp(-4.2))
        pts = [(lerp(gx0, gx1, u / 60), yc(u / 60)) for u in range(int(60 * pa2) + 1)]
        if len(pts) > 1:
            d.line(pts, fill=A(VGOLD, a), width=6, joint='curve')
            if GL: GL.line(pts, fill=A(VGOLD, a), width=12)
            ex, ey = pts[-1]; d.ellipse([ex - 9, ey - 9, ex + 9, ey + 9], fill=A(VGOLD, a))
        if pa2 >= 1: txt(d, gx1 - 130, yc(1) + 14, 'ACTUAL', f(MONO, 24), VGOLD, a)
        tg = wt('muscle', 19)
        if t >= tg - 0.3:
            q = appear(t, tg - 0.3, 0.2); ya, yb = gy0 + 10 + 4, yc(1) - 4; xg = gx1 - 30
            d.line([(xg, ya), (xg, lerp(ya, yb, q))], fill=A(RED, a), width=5)
            d.line([(xg - 14, ya), (xg + 14, ya)], fill=A(RED, a), width=5); d.line([(xg - 14, yb), (xg + 14, yb)], fill=A(RED, a * q), width=5)
            if GL: GL.line([(xg, ya), (xg, lerp(ya, yb, q))], fill=A(RED, a), width=10)
            if q > 0.5: tag(d, xg - 22, yb + 52, 'DIMINISHING RETURNS', RED, 26, a, anchor='r')

# ---- S3 vitals: four free-floating meters that drain on the word ----
def scene_vitals(im, d, t):
    t0, t1 = 20.70, 25.22
    al = life(t, t0, t1, 0.18, 0.18)
    if al <= 0: return
    txt(d, 70, 1150, '● VITALS · HIGH-DOSE TREN', f(MONO, 26), VGOLD, al)
    rows = [('RECOVERY', wt('recovery', 20)), ('APPETITE', wt('appetite', 20)), ('SLEEP', wt('sleep', 20)), ('MOOD', wt('moods', 20))]
    tsh = wt('shit', 23)
    for i, (lab, tw_) in enumerate(rows):
        y = 1205 + i * 86; p = expo((t - (t0 + 0.05 * i)) / 0.25); x_off = lerp(-60, 0, p); a = al * p
        txt(d, 70 + x_off, y + 4, lab, f(BAR, 40), CREAM, a)
        drain = expo((t - tw_) / 0.4); lvl = lerp(0.88, 0.14, drain)
        col = mix(GREEN, RED, drain)
        if t >= tsh and int((t - tsh) * 14) % 2 == 0 and t < tsh + 0.45: col = WHITE
        n = 14
        for k in range(n):
            sx = 330 + k * 43 + x_off; on = (k + 0.5) / n <= lvl
            d.rectangle([sx, y + 8, sx + 35, y + 48], fill=A(col if on else (30, 32, 40), a * (1 if on else 0.8)))
            if on and GL: GL.rectangle([sx, y + 8, sx + 35, y + 48], fill=A(col, a * 0.5))
        if drain > 0.6: txt(d, 940 + x_off - d.textlength('LOW', font=f(BEB, 40)), y + 4 - 46, '', f(BEB, 40), RED, a)
        if drain > 0.7: tag(d, 330 + n * 43 + x_off - 6, y + 6, 'LOW', RED, 24, a * clamp((drain - 0.7) / 0.3), anchor='r') if False else None
    if t >= tsh:
        tag(d, 70, 1555, 'SYSTEM CRASHING', RED, 30, al * appear(t, tsh, 0.1))

# ---- S4 NON-NEGOTIABLE slam pill ----
def scene_nonneg(im, d, t):
    t0 = wt('non-negotiable', 27); t1 = 29.62
    if t < t0 or t > t1: return
    p = clamp((t - t0) / 0.12); s = lerp(1.35, 1.0, expo(p)); al = min(p * 3, 1, clamp((t1 - t) / 0.16))
    fn = f(BEB, int(104 * s)); label = 'NON-NEGOTIABLE 02'; tw = d.textlength(label, font=fn); h = 118 * s * 1.02
    cx, cy = 500, 1250
    lit_bar(d, cx - tw / 2 - 34, cy - h / 2, cx + tw / 2 + 34, cy + h / 2, VGOLD, al)
    d.text((cx - tw / 2, cy - h / 2 + 8 * s), label, font=fn, fill=A(INK, al))
    if GL: GL.rectangle([cx - tw / 2 - 40, cy - h / 2 - 6, cx + tw / 2 + 40, cy + h / 2 + 6], outline=A(VGOLD, al), width=12)
    q = appear(t, t0 + 0.2, 0.2)
    ctext(d, cx, cy + h / 2 + 18, 'CARDIOVASCULAR · ANY DOSE · ANY CYCLE', f(MONO, 28), CREAM, al * q)

# ---- S5 lab requisition (paper document) ----
def scene_labform(im, d, t):
    t0, t1 = 29.66, 34.95
    if t < t0 or t > t1 + 0.25: return
    pin = expo((t - t0) / 0.28); pout = ease_io((t - t1) / 0.25)
    pw, ph = 860, 430
    pap = Image.new('RGBA', (pw, ph), (0, 0, 0, 0)); pd = ImageDraw.Draw(pap)
    pd.rectangle([0, 0, pw, ph], fill=(236, 234, 228, 255))
    pd.rectangle([0, 0, pw, 64], fill=COARED + (255,)); pd.text((22, 14), 'LAB REQUISITION · CARDIO PANEL', font=f(MONO, 30), fill=WHITE)
    pd.text((22, 76), 'PATIENT: ENHANCED ATHLETE      PRIORITY: ROUTINE', font=f(MONOM, 20), fill=(120, 120, 128))
    rows = [('Blood pressure', wt('blood', 29.8)), ('ApoB', wt('apob', 30)), ('Lipid panel (cholesterol)', wt('cholesterol', 31)), ('Hematocrit', wt('hematocrit', 32)), ('Cardiac function', wt('cardiac', 33))]
    for i, (lab, tw_) in enumerate(rows):
        y = 116 + i * 60
        pd.rectangle([24, y + 8, 60, y + 44], outline=(60, 62, 70, 255), width=3)
        on = t >= tw_
        pd.text((80, y + 4), lab, font=f(DMB if on else DMR, 34), fill=(14, 16, 22, 255) if on else (90, 92, 100, 255))
        pd.line([(24, y + 54), (pw - 24, y + 54)], fill=(212, 210, 204, 255), width=2)
        if on:
            p = clamp((t - tw_) / 0.14)
            pts = [(28, y + 26), (40, y + 40), (66, y + 2)]
            if p < 0.5: pts = [pts[0], (lerp(28, 40, p * 2), lerp(y + 26, y + 40, p * 2))]
            elif p < 1: q = (p - 0.5) * 2; pts = [pts[0], pts[1], (lerp(40, 66, q), lerp(y + 40, y + 2, q))]
            pd.line(pts, fill=(205, 12, 22, 255), width=7, joint='curve')
    ts = wt('overall', 34)
    if t >= ts:
        q = clamp((t - ts) / 0.1); s = lerp(1.6, 1.0, expo(q))
        st = Image.new('RGBA', (360, 120), (0, 0, 0, 0)); sd = ImageDraw.Draw(st)
        sd.rounded_rectangle([4, 4, 356, 116], radius=10, outline=(205, 12, 22, 230), width=7)
        sd.text((180, 60), 'REQUIRED', font=f(BEB, 84), fill=(205, 12, 22, 230), anchor='mm')
        st = st.rotate(9, expand=True, resample=Image.BICUBIC).resize((int(380 * s), int(160 * s)), Image.BICUBIC)
        st.putalpha(st.split()[3].point(lambda v: int(v * min(1, q * 3))))
        pap.alpha_composite(st, (int(600 - st.width / 2), int(300 - st.height / 2)))
    pap = pap.rotate(-2.0, expand=True, resample=Image.BICUBIC)
    sh = Image.new('RGBA', (pap.width + 60, pap.height + 60), (0, 0, 0, 0)); sh.paste((0, 0, 0, 150), (30, 40), pap.split()[3].point(lambda v: 150 if v > 0 else 0))
    sh = sh.filter(ImageFilter.GaussianBlur(14))
    x = int(500 - pap.width / 2); y = int(lerp(1960, 1138, pin) + pout * 820)
    im.alpha_composite(sh, (x - 30, y - 30)); im.alpha_composite(pap, (x, y))

# ---- S6 artery scope + ECG monitor ----
def ecg_wave(u):
    """PQRST, u in beats"""
    ph = u % 1.0
    v = 0.12 * math.exp(-((ph - 0.12) / 0.03) ** 2) - 0.12 * math.exp(-((ph - 0.25) / 0.012) ** 2) + 1.0 * math.exp(-((ph - 0.28) / 0.012) ** 2) \
        - 0.25 * math.exp(-((ph - 0.31) / 0.014) ** 2) + 0.25 * math.exp(-((ph - 0.55) / 0.05) ** 2)
    return v
def scene_cardio(im, d, t):
    t0 = wt('arteries', 37) - 0.08; t1 = 41.22
    al = life(t, t0, t1, 0.2, 0.15)
    if al <= 0: return
    th = wt('healthy', 38); tx = wt('explode', 40); thr = wt("heart's", 39)
    # scope (left)
    cx, cy, R = 225, 1345, 160
    frosted(im, (cx - R, cy - R, cx + R, cy + R), 0.9, 8, radius=R)
    d.ellipse([cx - R, cy - R, cx + R, cy + R], outline=A(CYAN, al), width=4)
    if GL: GL.ellipse([cx - R, cy - R, cx + R, cy + R], outline=A(CYAN, al), width=10)
    for k in range(12):
        an = k * math.pi / 6; d.line([(cx + (R - 14) * math.cos(an), cy + (R - 14) * math.sin(an)), (cx + R * math.cos(an), cy + R * math.sin(an))], fill=A(CYAN, al), width=3)
    pl = expo((t - (t0 + 0.2)) / 0.9)  # plaque growth
    d.ellipse([cx - 112, cy - 112, cx + 112, cy + 112], fill=A((60, 14, 24), al), outline=A((255, 120, 140), al), width=6)
    lr = lerp(88, 50, pl)
    d.ellipse([cx - 88, cy - 88, cx + 88, cy + 88], fill=A((150, 30, 46), al))
    # plaque crescent (red) narrowing the lumen from one side
    d.ellipse([cx - lr + (88 - lr) * 0.9, cy - lr, cx + lr + (88 - lr) * 0.9, cy + lr], fill=A((8, 10, 16), al))
    d.ellipse([cx - lr + (88 - lr) * 0.9, cy - lr, cx + lr + (88 - lr) * 0.9, cy + lr], outline=A(CYAN, al), width=3)
    if pl > 0.05 and GL: GL.arc([cx - 92, cy - 92, cx + 92, cy + 92], 120, 240, fill=A(RED, al * pl), width=14)
    txt(d, cx - R, cy - R - 40, 'ARTERY · CROSS-SECTION', f(MONO, 22), CYAN, al)
    if t >= th: tag(d, cx - R + 4, cy + R + 10, 'NOT GUARANTEED', RED, 24, al * appear(t, th, 0.12))
    # ECG monitor (right)
    if t >= thr - 0.15:
        a = al * appear(t, thr - 0.15, 0.18)
        mx0, my0, mx1, my1 = 420, 1215, 945, 1470
        frosted(im, (mx0, my0, mx1, my1), 0.92, 8)
        bad = t >= tx
        bc = RED if bad else CYAN
        if bad and int((t - tx) * 10) % 2 == 0: bc = WHITE
        d.rectangle([mx0, my0, mx1, my1], outline=A(bc, a), width=4)
        if GL: GL.rectangle([mx0, my0, mx1, my1], outline=A(bc, a), width=8)
        for gx in range(mx0 + 25, mx1, 25): d.line([(gx, my0 + 50), (gx, my1 - 6)], fill=A(CYAN, 0.08 * a))
        for gy in range(my0 + 50, my1, 25): d.line([(mx0 + 4, gy), (mx1 - 4, gy)], fill=A(CYAN, 0.08 * a))
        txt(d, mx0 + 16, my0 + 10, 'ECG · LEAD II', f(MONO, 24), CYAN, a)
        hr = 'HR 74' if not bad else 'HR ---'
        fr = f(BEB, 44); tw_ = d.textlength(hr, font=fr); txt(d, mx1 - 18 - tw_, my0 + 2, hr, fr, RED if bad else GREEN, a)
        base = (my0 + my1) / 2 + 40; pts = []
        sweep = (t - thr) * 1.6  # beats travelled
        for k in range(0, 500, 3):
            u = k / 500 * 3.2 + sweep
            if bad and (t - tx) > 0 and k / 500 > 1 - (t - tx) * 1.2:
                v = 0.55 * math.sin(u * 23) + 0.35 * math.sin(u * 37 + 1.3) + 0.2 * math.sin(u * 61)
            else: v = ecg_wave(u)
            pts.append((mx0 + 12 + k * (mx1 - mx0 - 24) / 500, base - v * 120))
        col = RED if bad else GREEN
        d.line(pts, fill=A(col, a), width=4, joint='curve')
        if GL: GL.line(pts, fill=A(col, a), width=10)
        if bad: tag(d, mx0 + 14, my1 + 12, 'CARDIAC EVENT RISK', RED, 26, a * appear(t, tx + 0.05, 0.1))

# ---- S7 supplement stack (objects) ----
SUPPS = ['BP', 'SLEEP', 'LIVER', 'CARDIO', 'MOOD']
def bottle(d, x, y, lab, a, dim=1.0):
    d.rounded_rectangle([x + 34, y, x + 96, y + 34], radius=6, fill=A(mix(VGOLD, (60, 50, 20), 1 - dim), a), outline=None)
    d.rounded_rectangle([x, y + 30, x + 130, y + 230], radius=22, fill=A((22, 26, 36), a * 0.96), outline=A(mix(WHITE, DIM, 1 - dim), a), width=4)
    d.rectangle([x + 12, y + 92, x + 118, y + 186], fill=A(mix((236, 234, 228), (90, 90, 96), 1 - dim), a))
    fn = f(BAR8, 34 if len(lab) < 6 else 28); tw = d.textlength(lab, font=fn); d.text((x + 65 - tw / 2, y + 104), lab, font=fn, fill=A(INK, a))
    fs = f(MONOM, 15); s2 = 'SUPPORT'; tw = d.textlength(s2, font=fs); d.text((x + 65 - tw / 2, y + 152), s2, font=fs, fill=A((70, 70, 80), a))
def scene_supps(im, d, t):
    t0 = wt('stop', 41.8); t1 = 44.42
    al = life(t, t0, t1, 0.12, 0.14)
    if al <= 0: return
    tse = wt('side', 43); tbro = wt('bro', 44)
    floor = 1505
    d.line([(60, floor), (940, floor)], fill=A(GOLD, al), width=3)
    for i, lab in enumerate(SUPPS):
        ti = t0 + 0.04 + i * 0.2
        p = clamp((t - ti) / 0.16)
        if p <= 0: continue
        y = lerp(floor - 230 - 220, floor - 230, expo(p) if p < 1 else 1) + (6 * math.exp(-(t - ti - 0.16) * 30) if t > ti + 0.16 else 0)
        bottle(d, 80 + i * 168, y, lab, al * min(1, p * 4))
    if t >= tse:
        q = clamp((t - tse) / 0.4); sx = lerp(60, 940, q)
        if q < 1:
            d.line([(sx, floor - 260), (sx, floor)], fill=A(CYAN, al), width=4)
            if GL: GL.line([(sx, floor - 260), (sx, floor)], fill=A(CYAN, al), width=14)
    te = wt('effects', 43)
    if t >= te + 0.1:
        a = al * appear(t, te + 0.1, 0.12)
        brackets(d, 66, floor - 262, 934, floor + 8, A(RED, a), 40, 7)
        if GL: brackets(GL, 66, floor - 262, 934, floor + 8, A(RED, a), 40, 14)
        tag(d, 66, floor + 16, 'MASKS SYMPTOMS · ROOT CAUSE: DOSE', RED, 26, a)
    if t >= tbro:
        q = expo((t - tbro) / 0.12); x = lerp(70, 930, q)
        d.line([(70, floor - 40), (x, lerp(floor - 40, floor - 230, q))], fill=A(RED, al), width=10)
        if GL: GL.line([(70, floor - 40), (x, lerp(floor - 40, floor - 230, q))], fill=A(RED, al), width=20)

# ---- S8 symptom monitor: sleep ring big stat + BP live chart ----
def scene_symptoms(im, d, t):
    t0 = wt('sleeping', 44) - 0.2; t1 = 49.0
    al = life(t, t0, t1, 0.2, 0.16)
    if al <= 0: return
    frosted(im, PANEL, 0.9, 9)
    hud_frame(im, d, PANEL, al, 'SYMPTOM MONITOR', 'ON CYCLE', CYAN)
    # sleep ring
    cx, cy, R = 250, 1380, 128
    th2 = wt('two', 44.8); p = ease_io((t - th2) / 0.7)
    hrs = counter(8, 2, p) if t >= th2 else 8
    frac = hrs / 8 if p >= 1 else lerp(1, 0.25, ease_io(p))
    col = mix(CYAN, RED, p)
    d.ellipse([cx - R, cy - R, cx + R, cy + R], outline=A((40, 44, 56), al), width=18)
    d.arc([cx - R, cy - R, cx + R, cy + R], -90, -90 + 360 * frac, fill=A(col, al), width=18)
    if GL: GL.arc([cx - R, cy - R, cx + R, cy + R], -90, -90 + 360 * frac, fill=A(col, al), width=26)
    ctext(d, cx, cy - 78, str(hrs), f(BEB, 130), WHITE, al)
    ctext(d, cx, cy + 46, 'HRS SLEEP', f(MONO, 22), col, al)
    ts = wt('sweating', 46)
    if t >= ts: tag(d, 500, 1222, 'NIGHT SWEATS', RED, 26, al * appear(t, ts, 0.12))
    # BP chart
    tb = wt('blood', 47.4); tsk = wt('skyrocketing', 48)
    gx0, gy0, gx1, gy1 = 510, 1290, 920, 1525
    zone = gy0 + (gy1 - gy0) * 0.38
    d.rectangle([gx0, gy0, gx1, zone], fill=A((90, 8, 12), al * 0.55)); txt(d, gx1 - 70, gy0 + 6, 'HIGH', f(MONO, 22), RED, al)
    d.line([(gx0, zone), (gx1, zone)], fill=A(RED, al * 0.8), width=2)
    d.line([(gx0, gy1), (gx1, gy1)], fill=A(CREAM, al * 0.7), width=2)
    txt(d, gx0, gy1 + 6, 'BLOOD PRESSURE', f(MONO, 20), CREAM, al)
    if t >= tb - 0.1:
        pr = clamp((t - (tb - 0.1)) / (tsk + 0.45 - tb))
        N = 40; pts = []
        for k in range(int(N * pr) + 1):
            u = k / N
            v = 0.32 + 0.03 * math.sin(u * 30) + (0 if u < 0.55 else ((u - 0.55) / 0.45) ** 1.6 * 0.6)
            pts.append((lerp(gx0, gx1 - 14, u), gy1 - v * (gy1 - gy0)))
        if len(pts) > 1:
            c = RED if pts[-1][1] < zone else WHITE
            d.line(pts, fill=A(c, al), width=5, joint='curve')
            if GL: GL.line(pts, fill=A(c, al), width=12)
            ex, ey = pts[-1]; d.ellipse([ex - 9, ey - 9, ex + 9, ey + 9], fill=A(c, al))
        if t >= tsk + 0.3:
            q = appear(t, tsk + 0.3, 0.12); arrow(d, gx1 - 40, gy0 + 120, gx1 - 40, gy0 + 40, RED, 6, al * q, 22)

# ---- S9 dose fader ----
def scene_fader(im, d, t):
    t0 = 49.10; t1 = wt('why', 55) - 0.05
    al = life(t, t0, t1, 0.2, 0.16)
    if al <= 0: return
    bx0, by0, bx1, by1 = 50, 1230, 950, 1500
    frosted(im, (bx0, by0, bx1, by1), 0.9, 9, radius=26)
    d.rounded_rectangle([bx0, by0, bx1, by1], radius=26, outline=A((60, 64, 78), al), width=3)
    txt(d, bx0 + 30, by0 + 20, '● DOSE', f(MONO, 28), VGOLD, al)
    tx0, tx1, ty = 110, 890, 1380
    zones = [(110, 330, VGOLD, 'MICRO'), (330, 610, AMBER, 'MODERATE'), (610, 890, RED, 'HIGH')]
    tm = wt('microdosing', 52)
    for (a0, a1, c, lab) in zones:
        hot = (lab == 'MICRO' and t >= tm + 0.3) or (lab == 'HIGH' and t < wt('dropping', 50))
        d.rectangle([a0 + 3, ty - 7, a1 - 3, ty + 7], fill=A(c, al * (1 if hot else 0.45)))
        if hot and GL: GL.rectangle([a0 + 3, ty - 7, a1 - 3, ty + 7], fill=A(c, al))
        ctext(d, (a0 + a1) / 2, ty + 40, lab, f(MONO, 24), c if hot else MUTED, al)
    for k in range(17): x = lerp(tx0, tx1, k / 16); d.line([(x, ty - 30), (x, ty - 18)], fill=A(MUTED, al * 0.6), width=2)
    td = wt('dropping', 50)
    def kx(tt):
        x = 840
        x = lerp(x, 470, ease_io((tt - td) / 0.6))
        x = lerp(x, 220, ease_io((tt - tm) / 0.6))
        return x
    x = kx(t)
    for g in (0.12, 0.08, 0.04):
        gxp = kx(t - g)
        if abs(gxp - x) > 4: d.rounded_rectangle([gxp - 24, ty - 50, gxp + 24, ty + 50], radius=8, fill=A(WHITE, al * 0.10))
    d.rounded_rectangle([x - 26, ty - 52, x + 26, ty + 52], radius=9, fill=A((40, 44, 54), al), outline=A(WHITE, al), width=3)
    for k in range(5): d.line([(x - 16, ty - 32 + k * 16), (x + 16, ty - 32 + k * 16)], fill=A(MUTED, al), width=2)
    d.line([(x, ty - 52), (x, ty + 52)], fill=A(VGOLD, al), width=3)
    if GL: GL.rounded_rectangle([x - 28, ty - 54, x + 28, ty + 54], radius=9, outline=A(VGOLD if t > tm else WHITE, al * 0.6), width=8)
    lvl = 'HIGH' if x > 620 else ('MODERATE' if x > 335 else 'MICRO')
    fr = f(BEB, 52); tw = d.textlength(lvl, font=fr)
    txt(d, bx1 - 30 - tw, by0 + 10, lvl, fr, {'HIGH': RED, 'MODERATE': AMBER, 'MICRO': VGOLD}[lvl], al)
    if t >= tm + 0.45: tag(d, 110, by1 + 14, 'MICRODOSE · RECOMMENDED', VGOLD, 26, al * appear(t, tm + 0.45, 0.12))

# ---- S10 alert toasts from your body ----
def scene_alerts(im, d, t):
    t0 = wt('side', 55.6) - 0.1; t1 = 61.05
    al = life(t, t0, t1, 0.1, 0.16)
    if al <= 0: return
    toasts = [(wt('side', 55.6), 'BLOOD PRESSURE ELEVATED'), (wt('high', 56), 'SLEEP · 2 HRS'), (wt('tren', 57), 'NIGHT SWEATS'), (wt('body', 58), 'MOOD CRASHING')]
    tt = wt('telling', 58)
    if t >= tt: txt(d, 70, 1140, 'INCOMING · FROM YOUR BODY', f(MONO, 26), VGOLD, al * appear(t, tt, 0.15))
    live = [(ts, lab) for ts, lab in toasts if t >= ts]
    tdone = wt('done', 60)
    dimk = 1 - 0.55 * expo((t - tdone) / 0.15) if t >= tdone else 1
    for rank, (ts, lab) in enumerate(reversed(live)):
        p = expo((t - ts) / 0.2)
        # earlier toasts glide down when a newer one arrives
        y_target = 1182 + rank * 98
        y_prev = 1182 + max(0, rank - 1) * 98
        newer = [x for x in live if x[0] > ts]
        if newer:
            q = expo((t - newer[0][0]) / 0.2); y = lerp(y_prev if rank > 0 else 1182, y_target, q)
            if len(newer) > 1:
                q2 = expo((t - newer[-1][0]) / 0.2); y = lerp(1182 + (rank - 1) * 98, y_target, q2)
        else: y = 1182
        x = lerp(560, 70, p); a = al * min(1, p * 2) * dimk
        frosted(im, (x, y, x + 860, y + 88), 0.9, 8, radius=18)
        d.rounded_rectangle([x, y, x + 860, y + 88], radius=18, outline=A((70, 74, 90), a), width=2)
        d.rectangle([x + 2, y + 16, x + 8, y + 72], fill=A(RED, a))
        warn_icon(d, x + 26, y + 22, 44, RED, a)
        txt(d, x + 90, y + 18, lab, f(BAR, 42), CREAM, a)
        fr = f(MONOM, 22); txt(d, x + 860 - 22 - d.textlength('NOW', font=fr), y + 32, 'NOW', fr, MUTED, a)
    if t >= tdone - 0.08:
        q = expo((t - (tdone - 0.08)) / 0.14); x1 = lerp(60, 940, q); y = 1290
        lit_bar(d, 60, y, x1, y + 118, RED, al)
        if GL: GL.rectangle([56, y - 6, x1 + 4, y + 124], outline=A(RED, al), width=12)
        if q > 0.6: ctext(d, 500, y + 12, 'ACTION REQUIRED', f(BEB, 104), WHITE, al)

# ---- S11 decision fork ----
def scene_fork(im, d, t):
    t0 = wt('smartest', 61) - 0.1; t1 = wt("i've", 65) - 0.03
    al = life(t, t0, t1, 0.15, 0.12)
    if al <= 0: return
    nx, ny = 500, 1192
    fn = f(MONO, 28); lab = 'SMARTEST MOVE'; tw = d.textlength(lab, font=fn)
    d.rounded_rectangle([nx - tw / 2 - 22, ny - 26, nx + tw / 2 + 22, ny + 26], radius=26, fill=A(DEEP, 0.9 * al), outline=A(VGOLD, al), width=3)
    ctext(d, nx, ny - 16, lab, fn, VGOLD, al)
    tdd = wt('dropping', 62.9); tdc = wt('dropping', 64.3); tor = wt('or', 63.9)
    cards = [((60, 1312, 480, 1562), 'DROP THE', 'DOSE', tdd, 'fader'), ((520, 1312, 940, 1562), 'DROP THE', 'COMPOUND', tdc, 'vial')]
    for i, (box, l1, l2, ts, icon) in enumerate(cards):
        x0, y0, x1, y1 = box; cx = (x0 + x1) / 2
        pb = expo((t - (t0 + 0.25)) / 0.3)
        d.line([(nx, ny + 26), (nx, ny + 60), (lerp(nx, cx, pb), ny + 60), (lerp(nx, cx, pb), lerp(ny + 60, y0, pb))], fill=A(GOLD, al * 0.8), width=3)
        if pb < 0.9: continue
        sel = t >= ts; ps = appear(t, ts, 0.14)
        frosted(im, box, 0.9, 8, radius=20)
        oc = mix(DIM, VGOLD, ps)
        d.rounded_rectangle(box, radius=20, outline=A(oc, al), width=4 if sel else 3)
        if sel and GL: GL.rounded_rectangle(box, radius=20, outline=A(VGOLD, al * ps), width=12)
        txt(d, x0 + 30, y0 + 26, l1, f(MONO, 26), MUTED, al)
        txt(d, x0 + 28, y0 + 60, l2, f(BEB, 92 if len(l2) < 6 else 78), WHITE if sel else (150, 150, 160), al)
        if icon == 'fader':
            for k in range(3): d.line([(x1 - 70 + k * 20, y0 + 40), (x1 - 70 + k * 20, y0 + 120)], fill=A(MUTED, al), width=3)
            yy = lerp(y0 + 50, y0 + 110, ps); d.rectangle([x1 - 80, yy - 8, x1 - 20, yy + 8], fill=A(VGOLD if sel else MUTED, al))
        else:
            d.rounded_rectangle([x1 - 72, y0 + 50, x1 - 32, y0 + 130], radius=8, outline=A(MUTED, al), width=3); d.rectangle([x1 - 66, y0 + 36, x1 - 38, y0 + 50], fill=A(MUTED, al))
            if sel: cross(d, x1 - 76, y0 + 76, RED, 1.2, al * ps)
        if sel: check(d, x0 + 30, y1 - 64, VGOLD, 1.3, al, clamp((t - ts) / 0.16)); txt(d, x0 + 82, y1 - 60, 'VALID CALL', f(MONO, 24), VGOLD, al * ps)
    if t >= tor:
        qa = appear(t, tor, 0.1); d.rounded_rectangle([462, 1226, 538, 1278], radius=14, fill=A(DEEP, al * qa), outline=A(CREAM, al * qa), width=2)
        ctext(d, 500, 1226, 'OR', f(BEB, 50), CREAM, al * qa)

# ---- S12 case files A vs B ----
def scene_cases(im, d, t):
    t0 = wt('witnessed', 65.9) - 0.1; t1 = wt('but', 75) - 0.15
    al = life(t, t0, t1, 0.18, 0.16)
    if al <= 0: return
    specs = [((60, 1150, 480, 1565), 'CASE A', wt('could', 66), wt('rip', 67), 0.9, GREEN, [(wt('fantastic', 68), 'MOOD STABLE'), (wt('fantastic', 68) + 0.25, 'SLEEP OK'), (wt('fantastic', 68) + 0.5, 'GAINS UP')]),
             ((520, 1150, 940, 1565), 'CASE B', wt('other', 69), wt('bottle', 71), 0.08, RED, [(wt('schizophrenia', 72), 'PSYCHOSIS SX'), (wt('paranoia', 74), 'PARANOIA')])]
    for (box, name, ts, tm, lvl, col, chips) in specs:
        if t < ts - 0.05: continue
        p = expo((t - ts + 0.05) / 0.25); a = al * p
        x0, y0, x1, y1 = box; y0s = lerp(y0 + 60, y0, p)
        frosted(im, (x0, y0s, x1, y1), 0.9, 8, radius=18)
        d.rounded_rectangle([x0, y0s, x1, y1], radius=18, outline=A((70, 74, 90), a), width=3)
        d.rounded_rectangle([x0, y0s, x0 + 170, y0s + 50], radius=18, fill=A(col if t >= tm else DIM, a))
        txt(d, x0 + 22, y0s + 9, name, f(MONO, 28), INK if t >= tm else WHITE, a)
        txt(d, x0 + 190, y0s + 14, 'RESPONSE TO TREN', f(MONOM, 20), MUTED, a)
        q = ease_io((t - tm) / 0.6) if t >= tm else 0; v = lerp(0.5, lvl, q)
        txt(d, x0 + 24, y0s + 80, 'TOLERANCE', f(MONO, 24), CREAM, a)
        d.rectangle([x0 + 24, y0s + 118, x1 - 24, y0s + 150], outline=A(DIM, a), width=2)
        c2 = mix(AMBER, col, q); lit_bar(d, x0 + 27, y0s + 121, lerp(x0 + 27, x1 - 27, v), y0s + 147, c2, a)
        if GL and q > 0: GL.rectangle([x0 + 27, y0s + 121, lerp(x0 + 27, x1 - 27, v), y0s + 147], fill=A(c2, a * 0.6))
        fr = f(BEB, 52); s = f'{int(round(v * 100))}%'; tw = d.textlength(s, font=fr); txt(d, x1 - 24 - tw, y0s + 64, s, fr, c2, a)
        for k, (tc, lab) in enumerate(chips):
            if t < tc: continue
            qa = appear(t, tc, 0.14); yy = y0s + 186 + k * 66
            fn = f(BAR, 36); tw = d.textlength(lab, font=fn)
            fill = (8, 40, 20) if col == GREEN else (40, 10, 14)
            d.rectangle([x0 + 24, yy, x0 + 24 + tw + 70, yy + 52], fill=A(fill, a * qa), outline=A(col, a * qa), width=2)
            if col == GREEN: check(d, x0 + 36, yy + 10, GREEN, 0.95, a * qa)
            else: cross(d, x0 + 38, yy + 12, RED, 0.95, a * qa)
            txt(d, x0 + 84, yy + 6, lab, fn, mix(col, WHITE, 0.4), a * qa)

# ---- S13 amplifier ----
def scene_amp(im, d, t):
    t0 = wt('day', 75.5) - 0.05; t1 = wt("there's", 79.5) - 0.28
    al = life(t, t0, t1, 0.2, 0.16)
    if al <= 0: return
    y0, y1 = 1190, 1530; cy = 1365
    frosted(im, (50, y0, 950, y1), 0.88, 10, radius=24)
    ttr = wt('tren', 76); tam = wt('amplify', 76.5); tme = wt('massive', 79)
    # input
    txt(d, 80, y0 + 18, 'INPUT · YOU', f(MONO, 24), CYAN, al)
    def wave(x0, x1, amp, ph, col, clip=None, w=4):
        pts = []
        for k in range(0, 121):
            u = k / 120; x = lerp(x0, x1, u)
            v = math.sin(u * 14 + ph) * 0.7 + math.sin(u * 31 + ph * 1.7) * 0.3
            y = v * amp
            if clip: y = max(-clip, min(clip, y))
            pts.append((x, cy - y))
        d.line(pts, fill=A(col, al), width=w, joint='curve')
        if GL: GL.line(pts, fill=A(col, al), width=w * 2 + 4)
    ph = t * 6
    wave(80, 360, 28, ph, CYAN)
    # amplifier triangle
    q = appear(t, ttr, 0.18)
    tri = [(400, cy - 110), (400, cy + 110), (580, cy)]
    d.polygon(tri, fill=A((24, 20, 8), al * q), outline=None); d.line(tri + [tri[0]], fill=A(VGOLD, al * q), width=6)
    if GL: GL.line(tri + [tri[0]], fill=A(VGOLD, al * q), width=14)
    txt(d, 418, cy - 26, 'TREN', f(BEB, 56), VGOLD, al * q)
    d.line([(360, cy), (400, cy)], fill=A(CYAN, al), width=4)
    # output
    g = lerp(1.0, 4.0, ease_io((t - tam) / 0.6)) if t >= tam else 1.0
    clipping = t >= tme
    if clipping: g = lerp(4.0, 6.5, ease_io((t - tme) / 0.4))
    amp = 28 * g; cl = 120
    txt(d, 620, y0 + 18, 'OUTPUT', f(MONO, 24), RED if clipping else VGOLD, al)
    d.line([(580, cy), (610, cy)], fill=A(VGOLD, al), width=4)
    if clipping:
        for yy in (cy - cl, cy + cl): d.line([(610, yy), (930, yy)], fill=A(RED, al), width=3)
    wave(610, 930, amp, ph, RED if clipping else VGOLD, cl if clipping else None, 5)
    if clipping: tag(d, 930, y1 + 10, 'CLIPPING', RED, 26, al * appear(t, tme + 0.15, 0.12), anchor='r')
    gtxt = f'GAIN ×{g:.1f}'; fr = f(MONO, 26); txt(d, 930 - d.textlength(gtxt, font=fr), y0 + 18, gtxt, fr, MUTED, al) if False else None

# ---- S14 bell curve (carousel look: navy + gold rule) ----
def scene_bell(im, d, t):
    t0 = wt("there's", 80) - 0.1; t1 = wt('regardless', 85.5) - 0.05
    al = life(t, t0, t1, 0.2, 0.16)
    if al <= 0: return
    x0, y0, x1, y1 = 50, 1140, 950, 1570
    d.rounded_rectangle([x0, y0, x1, y1], radius=16, fill=A(NAVY, 0.95 * al))
    d.rectangle([x0, y0 + 16, x0 + 5, y1 - 16], fill=A(GOLD, al))
    d.line([(x0 + 36, y0 + 40), (x0 + 76, y0 + 40)], fill=A(GOLD, al), width=3)
    txt(d, x0 + 88, y0 + 26, 'HOW GUYS RESPOND TO TREN', f(BAR, 30), GOLD, al)
    fr = f(MONOM, 20); txt(d, x1 - 26 - d.textlength('ILLUSTRATIVE', font=fr), y0 + 32, 'ILLUSTRATIVE', fr, MUTED, al)
    bx0, bx1, base, pk = 110, 890, 1500, 250
    def yv(u): return base - pk * math.exp(-((u - 0.5) / 0.17) ** 2 / 2) - 0
    pd_ = clamp((t - t0 - 0.05) / 0.5)
    tR = wt('handle', 80.5); tL = wt("can't", 81.8); tM = wt('most', 82.5); tMi = wt('microdose', 83.8); tW = wt('without', 84.4)
    def fill(u0, u1, col, a):
        pts = [(lerp(bx0, bx1, u0), base)] + [(lerp(bx0, bx1, u), yv(u)) for u in np.linspace(u0, u1, 40)] + [(lerp(bx0, bx1, u1), base)]
        d.polygon(pts, fill=A(col, a))
    if t >= tM: fill(0.2, 0.8, VGOLD, 0.35 * al * appear(t, tM, 0.2))
    if t >= tR: fill(0.8, 1.0, GREEN, 0.45 * al * appear(t, tR, 0.2))
    if t >= tL: fill(0.0, 0.2, RED, 0.5 * al * appear(t, tL, 0.2))
    pts = [(lerp(bx0, bx1, u), yv(u)) for u in np.linspace(0, pd_, max(2, int(80 * pd_)))]
    d.line(pts, fill=A(CREAM, al), width=5, joint='curve')
    if GL: GL.line(pts, fill=A(VGOLD, al * 0.7), width=10)
    d.line([(bx0, base), (bx1, base)], fill=A(MUTED, al), width=2)
    for u in (0.2, 0.8): d.line([(lerp(bx0, bx1, u), base), (lerp(bx0, bx1, u), base - pk - 10)], fill=A(MUTED, al * 0.5), width=2)
    txt(d, bx0, base + 10, 'LOW TOLERANCE', f(MONOM, 20), MUTED, al)
    fr = f(MONOM, 20); txt(d, bx1 - d.textlength('HIGH TOLERANCE', font=fr), base + 10, 'HIGH TOLERANCE', fr, MUTED, al)
    if t >= tR: ctext(d, lerp(bx0, bx1, 0.9), base - 120, 'HANDLE IT', f(BEB, 40), GREEN, al * appear(t, tR, 0.15))
    if t >= tL: ctext(d, lerp(bx0, bx1, 0.1), base - 120, "CAN'T", f(BEB, 40), RED, al * appear(t, tL, 0.15))
    if t >= tM: ctext(d, 500, base - 175, 'MOST GUYS', f(BEB, 56), CREAM, al * appear(t, tM, 0.15))
    if t >= tMi: tag(d, 500, base - 100, 'MICRODOSE → OK', VGOLD, 28, al * appear(t, tMi, 0.15), anchor='c')
    if t >= tW: ctext(d, 500, base - 40, 'MINIMAL SIDES', f(MONO, 22), GREEN, al * appear(t, tW, 0.15))

# ---- S15 equation: RESULTS x HEALTH = OUTCOME ----
def scene_equation(im, d, t):
    t0 = wt('extraordinary', 86) - 0.1; t1 = wt('so', 91) - 0.46
    al = life(t, t0, t1, 0.18, 0.16)
    if al <= 0: return
    tn = wt('nothing', 88.5); tdes = wt('destroying', 89.4); th = wt('health', 90)
    blocks = [(60, 'RESULTS'), (380, 'HEALTH'), (700, 'OUTCOME')]
    y0, y1 = 1200, 1440
    for i, (x0, lab) in enumerate(blocks):
        p = expo((t - (t0 + 0.08 * i)) / 0.22); a = al * p; x1 = x0 + 240
        if p <= 0: continue
        yo = lerp(30, 0, p)
        frosted(im, (x0, y0 + yo, x1, y1 + yo), 0.9, 8, radius=18)
        oc = DIM
        if lab == 'OUTCOME' and t >= tn: oc = RED
        if lab == 'HEALTH' and t >= tdes: oc = mix(GREEN, RED, ease_io((t - tdes) / 0.8))
        if lab == 'RESULTS': oc = VGOLD
        d.rounded_rectangle([x0, y0 + yo, x1, y1 + yo], radius=18, outline=A(oc, a), width=4)
        if GL and oc != DIM: GL.rounded_rectangle([x0, y0 + yo, x1, y1 + yo], radius=18, outline=A(oc, a), width=10)
        ctext(d, (x0 + x1) / 2, y0 + yo + 18, lab, f(MONO, 26), MUTED, a)
        if lab == 'RESULTS':
            for k in range(5):
                hh = 18 + k * 20 * appear(t, t0 + 0.2 + k * 0.06, 0.2)
                bx = x0 + 40 + k * 34; d.rectangle([bx, y1 + yo - 30 - hh, bx + 24, y1 + yo - 30], fill=A(VGOLD, a))
            ctext(d, (x0 + x1) / 2, y0 + yo + 50, 'MAX', f(BEB, 64), VGOLD, a)
        if lab == 'HEALTH':
            v = 100 if t < tdes else counter(100, 0, (t - tdes) / 0.8)
            c = GREEN if t < tdes else mix(GREEN, RED, ease_io((t - tdes) / 0.8))
            ctext(d, (x0 + x1) / 2, y0 + yo + 56, f'{v}%', f(BEB, 100), c, a)
            d.rectangle([x0 + 30, y1 + yo - 50, x1 - 30, y1 + yo - 30], outline=A(DIM, a), width=2)
            lit_bar(d, x0 + 33, y1 + yo - 47, lerp(x0 + 33, x1 - 33, v / 100), y1 + yo - 33, c, a)
        if lab == 'OUTCOME':
            if t < tn: ctext(d, (x0 + x1) / 2, y0 + yo + 56, '?', f(BEB, 110), DIM, a)
            else:
                q = clamp((t - tn) / 0.1); s = lerp(1.6, 1, expo(q))
                ctext(d, (x0 + x1) / 2, y0 + yo + 56 - (s - 1) * 50, '0', f(BEB, int(120 * s)), RED, a)
        if i < 2:
            sym = '×' if i == 0 else '='
            ctext(d, x1 + 40, y0 + 80, sym, f(BEB, 80), CREAM, a)
    if t >= th: tag(d, 500, y1 + 26, 'HEALTH × 0 = NOTHING TO SHOW', RED, 28, al * appear(t, th, 0.14), anchor='c')

# ---- S16 protocol document (brand carousel look) ----
LOGO = None
def scene_doc(im, d, t):
    global LOGO
    t0 = wt('trenbolone', 92.5) - 0.12; t1 = wt('comment', 100.8)
    if t < t0 or t > t1 + 0.28: return
    pin = expo((t - t0) / 0.3); pout = expo((t - t1) / 0.16)
    lay = Image.new('RGBA', (840, 440), (0, 0, 0, 0)); ld = ImageDraw.Draw(lay)
    ld.rounded_rectangle([0, 0, 839, 439], radius=18, fill=NAVY + (245,), outline=(58, 54, 48, 255), width=2)
    ld.rectangle([0, 18, 5, 422], fill=GOLD + (255,))
    if LOGO is None:
        try: LOGO = Image.open(LOGO_PATH).convert('RGB').resize((58, 58), Image.LANCZOS)
        except Exception: LOGO = False
    if LOGO:
        m = Image.new('L', (58, 58), 0); ImageDraw.Draw(m).ellipse([0, 0, 57, 57], fill=255); lay.paste(LOGO, (28, 22), m)
    ld.text((100, 22), 'COACH AGZ', font=f(BEB, 36), fill=GOLD + (255,)); ld.text((100, 58), '@coach.agz', font=f(MONOM, 18), fill=MUTED + (255,))
    fr = f(MONOM, 20); ld.text((840 - 28 - ld.textlength('PROTOCOL · 01', font=fr), 30), 'PROTOCOL · 01', font=fr, fill=GOLD + (255,))
    tf = wt('framework', 93.5); tp = wt('protocol', 94); tcl = wt('clients', 95.5)
    a1 = appear(t, tf - 0.25, 0.18)
    fn = f(BEB, 84); x = 30
    for p_, c in [('TREN', VGOLD), (' FRAMEWORK', CREAM)]:
        ld.text((x, 104), p_, font=fn, fill=c + (int(255 * a1),)); x += ld.textlength(p_, font=fn)
    if t >= tp:
        a2 = appear(t, tp, 0.18); ld.line([(30, 210), (70, 210)], fill=GOLD + (int(255 * a2),), width=3)
        ld.text((82, 196), 'MICRODOSE PROTOCOL', font=f(BAR, 30), fill=GOLD + (int(255 * a2),))
    rows = [(wt('microdose', 96.8), 'How to microdose', 'what I run with clients'), (wt('most', 98.6), 'Get the most out of it', ''), (wt('least', 99.7), 'Least amount of side effects', '')]
    for k, (tr, lead, sub) in enumerate(rows):
        if t < tr: continue
        a3 = appear(t, tr, 0.16); y = 250 + k * 58; xo = lerp(-20, 0, a3)
        ld.polygon([(40 + xo, y + 18), (50 + xo, y + 8), (60 + xo, y + 18), (50 + xo, y + 28)], fill=VGOLD + (int(255 * a3),))
        ld.text((76 + xo, y), lead, font=f(DMB, 32), fill=CREAM + (int(255 * a3),))
        w_ = ld.textlength(lead, font=f(DMB, 32))
        if sub: ld.text((86 + xo + w_, y + 6), '— ' + sub, font=f(DMR, 24), fill=MUTED + (int(255 * a3),))
    if t >= tcl:
        a4 = appear(t, tcl, 0.14)
        st = Image.new('RGBA', (300, 60), (0, 0, 0, 0)); sd = ImageDraw.Draw(st)
        lit_bar(sd, 0, 0, 300, 60, VGOLD, a4); sd.text((150, 30), 'USED WITH CLIENTS', font=f(MONO, 24), fill=INK + (int(255 * a4),), anchor='mm')
        s_ = lerp(1.4, 1, expo(clamp((t - tcl) / 0.12)))
        st = st.resize((int(300 * s_), int(60 * s_)), Image.BICUBIC)
        lay.alpha_composite(st, (int(810 - st.width), int(122 - (st.height - 60) / 2)))
    fd = ld.textlength('FOR RESEARCH & EDUCATIONAL PURPOSES ONLY', font=f(MONOM, 16))
    ld.text((30, 416), 'FOR RESEARCH & EDUCATIONAL PURPOSES ONLY', font=f(MONOM, 16), fill=(124, 124, 130, 255))
    # rise in (glass, slight blur); exit = collapse toward the CTA pill (handoff)
    s = lerp(0.94, 1, pin) * lerp(1, 0.35, pout)
    if s != 1: lay = lay.resize((max(1, int(840 * s)), max(1, int(440 * s))), Image.BICUBIC)
    if pin < 1: lay = lay.filter(ImageFilter.GaussianBlur(6 * (1 - pin)))
    a = min(pin, 1 - pout)
    lay.putalpha(lay.split()[3].point(lambda v: int(v * a)))
    cx = 500; cy = lerp(lerp(1420, 1360, pin), 1240, pout)
    im.alpha_composite(lay, (int(cx - lay.width / 2), int(cy - lay.height / 2)))

# ---- S17 CTA end card ----
def scene_cta(im, d, t):
    t0 = wt('comment', 100.8) + 0.14
    if t < t0: return
    p = clamp((t - t0) / 0.14); s = lerp(1.3, 1, expo(p)); al = min(1, p * 3)
    ttr = wt('tren', 101.3)
    fn = f(BEB, int(110 * s))
    parts = [('COMMENT ', INK), ('"TREN"', INK if t < ttr else (150, 8, 8))]
    tw = sum(d.textlength(x, font=fn) for x, _ in parts); h = 110 * s * 1.04; cx, cy = 500, 1215
    lit_bar(d, cx - tw / 2 - 36, cy - h / 2, cx + tw / 2 + 36, cy + h / 2, VGOLD, al)
    if GL: GL.rectangle([cx - tw / 2 - 42, cy - h / 2 - 6, cx + tw / 2 + 42, cy + h / 2 + 6], outline=A(VGOLD, al), width=14)
    x = cx - tw / 2
    for x_, c in parts: d.text((x, cy - h / 2 + 8 * s), x_, font=fn, fill=A(c, al)); x += d.textlength(x_, font=fn)
    # comment field typing TREN
    tb = wt('below', 101.8)
    if t >= t0 + 0.25:
        a = appear(t, t0 + 0.25, 0.2); y0 = 1310; y1 = 1410
        d.rounded_rectangle([90, y0, 910, y1], radius=50, fill=A((24, 26, 34), 0.95 * a), outline=A((80, 84, 100), a), width=2)
        if LOGO:
            m = Image.new('L', (58, 58), 0); ImageDraw.Draw(m).ellipse([0, 0, 57, 57], fill=255)
            av = LOGO.copy(); im.paste(av, (110, y0 + 21), m) if False else None
        d.ellipse([110, y0 + 21, 168, y0 + 79], fill=A((60, 64, 76), a))
        n = 0 if t < ttr else min(4, int((t - ttr) / 0.09) + 1)
        typed = 'TREN'[:n]
        if n == 0: txt(d, 190, y0 + 28, 'Add a comment…', f(DMR, 36), (130, 130, 140), a)
        else:
            txt(d, 190, y0 + 22, typed, f(DMB, 44), WHITE, a)
            if int(t * 3) % 2 == 0 and t < tb: cw = d.textlength(typed, font=f(DMB, 44)); d.line([(194 + cw, y0 + 28), (194 + cw, y0 + 74)], fill=A(VGOLD, a), width=3)
        sent = t >= tb
        sc = VGOLD if n >= 4 else (90, 94, 110)
        px, py = 850, y0 + 50
        d.polygon([(px - 26, py - 22), (px + 24, py), (px - 26, py + 22), (px - 16, py)], fill=A(sc, a))
        if sent and GL: GL.polygon([(px - 26, py - 22), (px + 24, py), (px - 26, py + 22), (px - 16, py)], fill=A(VGOLD, a))
        if sent:
            q = appear(t, tb, 0.18)
            txt(d, 110, y1 + 22, 'POSTED · FRAMEWORK SENT TO YOUR DMs', f(MONO, 24), GREEN, a * q)
    if t >= t0 + 0.6:
        a = appear(t, t0 + 0.6, 0.3)
        txt(d, 110, 1520, '@coach.agz', f(MONO, 30), GOLD, a)
        txt(d, 110, 1562, 'FOR RESEARCH & EDUCATIONAL PURPOSES ONLY', f(MONOM, 18), (150, 150, 156), a)

SCENES = [  # (fn, t_lower_start, t_lower_end) - lower = captions lift above the band
    (scene_receptor, 13.40, 20.55), (scene_vitals, 20.70, 25.22), (scene_nonneg, 28.0, 29.62), (scene_labform, 29.66, 35.15),
    (scene_cardio, 37.73, 41.22), (scene_supps, 42.08, 44.42), (scene_symptoms, 44.60, 49.0), (scene_fader, 49.10, 55.42),
    (scene_alerts, 55.91, 61.05), (scene_fork, wt('smartest', 61) - 0.1, wt("i've", 65) - 0.03),
    (scene_cases, wt('witnessed', 65.9) - 0.1, wt('but', 75) - 0.15), (scene_amp, wt('day', 75.5) - 0.05, wt("there's", 79.5) - 0.28),
    (scene_bell, wt("there's", 80) - 0.1, wt('regardless', 85.5) - 0.05), (scene_equation, wt('extraordinary', 86) - 0.1, wt('so', 91) - 0.46),
    (scene_doc, wt('trenbolone', 92.5) - 0.12, wt('comment', 100.8) + 0.28), (scene_cta, wt('comment', 100.8), 999)]
def lower_amount(t):
    v = 0
    for fn, a, b in SCENES:
        if a - 0.2 <= t <= b + 0.2: v = max(v, min(clamp((t - (a - 0.2)) / 0.2), clamp((b + 0.2 - t) / 0.2)))
    return ease_io(v)

# ---------------- captions (saved style: Bebas, every word, lit red box on the live word) ----------------
CUTS = []
_acc = 0
for a_, b_ in CUT['keep'][:-1]: _acc += b_ - a_; CUTS.append(round(_acc, 3))
def build_groups():
    G = []; cur = []
    for i, x in enumerate(WORDS):
        if cur:
            prev = WORDS[cur[-1]]
            jc = any(prev['e'] - 0.02 <= c <= x['s'] + 0.02 for c in CUTS)
            long_ = sum(len(WORDS[j]['w']) for j in cur) + len(x['w']) > 22
            if len(cur) >= 3 or x['s'] - prev['e'] > 0.28 or prev['w'][-1] in '.,?!' or jc or long_: G.append(cur); cur = []
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
FIX = {'apob': 'APOB', 'apob,': 'APOB'}
def captions(im, t):
    g = group_at(t)
    if not g or t > DUR: return
    d = ImageDraw.Draw(im, 'RGBA')
    ws = [FIX.get(WORDS[i]['w'].lower(), WORDS[i]['w']).upper().rstrip(',.?!') for i in g]
    lv = lower_amount(t)
    maxs = lerp(124, 94, lv)
    size = int(maxs)
    while True:
        fn = f(BEB, size); sp = d.textlength(' ', font=fn) + 14; wd = [d.textlength(w, font=fn) for w in ws]; tot = sum(wd) + sp * (len(ws) - 1)
        if tot <= 860: break
        size -= 4
    cxc = 500
    xs = []; x = cxc - tot / 2
    for w_ in wd: xs.append(x); x += w_ + sp
    act = 0
    for k, i in enumerate(g):
        if WORDS[i]['s'] <= t: act = k
    g0 = WORDS[g[0]]['s']; s = lerp(0.9, 1, expo((t - g0) / 0.10))
    cap = Image.new('RGBA', (W, 260), (0, 0, 0, 0)); cd = ImageDraw.Draw(cap); shd = Image.new('RGBA', (W, 260), (0, 0, 0, 0)); sd = ImageDraw.Draw(shd)
    prev = max(0, act - 1); bt = expo((t - WORDS[g[act]]['s']) / 0.07) if act > 0 else 1
    bx0 = lerp(xs[prev], xs[act], bt) - 16; bx1 = lerp(xs[prev] + wd[prev], xs[act] + wd[act], bt) + 16
    for k, (w_, x_) in enumerate(zip(ws, xs)):
        sd.text((x_ + 4, 46), w_, font=fn, fill=(0, 0, 0, 220))
    cap.alpha_composite(shd.filter(ImageFilter.GaussianBlur(7)))
    lit_bar(cd, bx0, 40 + size * 0.02, bx1, 40 + size * 0.98, RED)
    for k, (w_, x_) in enumerate(zip(ws, xs)): cd.text((x_, 40), w_, font=fn, fill=CREAM + (255,), stroke_width=0 if k == act else 3, stroke_fill=(0, 0, 0))
    cy = lerp(1335, 1042, lv)
    if abs(s - 1) > 0.002:
        cap = cap.resize((int(W * s), int(260 * s)), Image.BICUBIC); ox = int((W - cap.width) / 2 + (1 - s) * (cxc - W / 2)); oy = int(cy - 40 - (cap.height - 260) / 2)
    else: ox, oy = 0, int(cy - 40)
    im.alpha_composite(cap, (ox, oy))

# ---------------- camera: punch-ins (jump cuts + emphasis), anchored on the face ----------------
ZOOM = [(0, 1.0), (wt('trenbolone', 1.5), 1.08), (CUTS[0], 1.0), (wt('number', 25), 1.1), (wt('we\'re', 29.5), 1.0), (wt('greek', 35.9), 1.14),
        (wt('arteries', 37.5) - 0.08, 1.04), (CUTS[1], 1.1), (wt('bro', 44), 1.0), (CUTS[2], 1.06), (CUTS[3], 1.0), (wt('why', 55), 1.1), (wt('sometimes', 61), 1.0),
        (CUTS[4], 1.08), (CUTS[5], 1.0), (CUTS[6], 1.08), (wt('but', 75.4), 1.12), (wt("there's", 80), 1.0), (CUTS[7], 1.07), (wt('regardless', 85.5), 1.14), (wt('so', 91.7), 1.0),
        (CUTS[8], 1.07), (CUTS[9], 1.0), (CUTS[10], 1.06), (CUTS[11], 1.0)]
def zoom_at(t):
    z = 1.0
    for tz, v in ZOOM:
        if t >= tz - 1e-6: z = v
    return z
AX, AY = 590, 740

# ---------------- SFX cue list (exported for sfx.py) ----------------
def frame(src, t):
    global GL
    z = zoom_at(t)
    if z != 1.0:
        big = src.resize((int(W * z), int(H * z)), Image.BICUBIC); ox = int(AX * z - AX); oy = int(AY * z - AY); src = big.crop((ox, oy, ox + W, oy + H))
    im = src.convert('RGBA')
    # scrims (overlay only, footage untouched): top for band, bottom under graphics/captions
    lv = lower_amount(t)
    yy = np.arange(H)
    a = np.where(yy > 1000, np.clip((yy - 1000) / 330, 0, 1) * lerp(90, 175, lv), 0)
    a = np.maximum(a, np.where(yy < 400, (1 - yy / 400) * 100, 0)).astype(np.uint8)
    im.alpha_composite(Image.merge('RGBA', [Image.new('L', (W, H), c) for c in DEEP] + [Image.fromarray(np.repeat(a[:, None], W, 1))]))
    glow = Image.new('RGBA', (W, H), (0, 0, 0, 0)); GL = ImageDraw.Draw(glow, 'RGBA')
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay, 'RGBA')
    # scenes that need the live frame (frosted backplates / pasted docs) draw straight into im first
    for fn, _, _ in SCENES:
        fn(im, d, t)
    im.alpha_composite(lay)
    d2 = ImageDraw.Draw(im, 'RGBA')
    topic_band(d2, t); rail(d2, t)
    GL_ = GL; GL = None
    if glow.getbbox():
        sm = glow.resize((W // 4, H // 4), Image.BILINEAR)
        g1 = np.asarray(sm.filter(ImageFilter.GaussianBlur(3.5))).astype(np.float32) / 255; g2 = np.asarray(sm.filter(ImageFilter.GaussianBlur(10))).astype(np.float32) / 255
        prem = np.clip(g1[..., :3] * g1[..., 3:] * 2.3 + g2[..., :3] * g2[..., 3:] * 1.8, 0, 1)
        prem = np.asarray(Image.fromarray((prem * 255).astype(np.uint8)).resize((W, H), Image.BILINEAR)).astype(np.float32) / 255
        b = np.asarray(im.convert('RGB')).astype(np.float32) / 255
        im = Image.fromarray(((1 - (1 - b) * (1 - prem)) * 255).astype(np.uint8)).convert('RGBA')
    # red edge flash on "explode"
    tx = wt('explode', 40)
    if tx <= t < tx + 0.35:
        k = 1 - (t - tx) / 0.35
        v = np.zeros((H, W), np.float32); m = 120
        xx = np.arange(W); yy2 = np.arange(H)
        ex = np.clip(1 - np.minimum(xx, W - 1 - xx) / m, 0, 1); ey = np.clip(1 - np.minimum(yy2, H - 1 - yy2) / m, 0, 1)
        v = np.maximum(ex[None, :], ey[:, None]) * 200 * k
        im.alpha_composite(Image.merge('RGBA', [Image.new('L', (W, H), c) for c in RED] + [Image.fromarray(v.astype(np.uint8))]))
    d = ImageDraw.Draw(im, 'RGBA'); d.rectangle([0, 0, 7, H], fill=GOLD)
    text_hook(im, t)
    captions(im, t)
    out = im.convert('RGB')
    # 2-frame impact shake on the heaviest landings
    for ts in SHAKES:
        k = round((t - ts) * FPS)
        if k in (0, 1):
            dx = [10, -5][k]; zz = 1.025; big = out.resize((int(W * zz), int(H * zz)), Image.BICUBIC); ox = (big.width - W) // 2 - dx; oy = (big.height - H) // 2
            out = big.crop((ox, oy, ox + W, oy + H)); ImageDraw.Draw(out).rectangle([0, 0, 7, H], fill=GOLD)
    return out
SHAKES = [wt('non-negotiable', 27), wt('explode', 40), wt('done', 60), wt('nothing', 88.5), wt('comment', 100.8) + 0.14]

if __name__ == '__main__':
    mode = sys.argv[2]
    if mode == 'stills':
        for tt in [float(x) for x in sys.argv[3:]]:
            n = min(int(round(tt * FPS)), int(DUR * FPS) - 1)
            subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', f'{n / FPS:.4f}', '-i', T + 'assembled.mp4', '-frames:v', '1', '-vf', 'scale=in_color_matrix=bt709:in_range=tv:out_range=full', T + 'qc/_src.png'])
            frame(Image.open(T + 'qc/_src.png').convert('RGB'), tt).resize((540, 960), Image.LANCZOS).save(T + f'qc/st_{tt:06.2f}.jpg', quality=88)
        sys.exit()
    n0, n1, out = int(sys.argv[3]), int(sys.argv[4]), sys.argv[5]
    NSRC = int(round(DUR * FPS))
    dec = subprocess.Popen(['ffmpeg', '-v', 'error', '-ss', f'{min(n0, NSRC - 1) / FPS:.4f}', '-i', T + 'assembled.mp4', '-vf', 'scale=in_color_matrix=bt709:in_range=tv:out_range=full', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], stdout=subprocess.PIPE)
    enc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                            '-vf', 'scale=out_color_matrix=bt709:out_range=tv', '-c:v', 'libx264', '-crf', '12', '-preset', 'medium', '-pix_fmt', 'yuv420p',
                            '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709', out], stdin=subprocess.PIPE)
    buf = None
    for n in range(n0, n1):
        if n < NSRC or buf is None:
            b = dec.stdout.read(W * H * 3)
            if len(b) == W * H * 3: buf = b
            elif buf is None: raise SystemExit(f'short read at {n}')
        enc.stdin.write(frame(Image.frombuffer('RGB', (W, H), buf), n / FPS).tobytes())
    enc.stdin.close(); enc.wait(); dec.kill(); print('done', n0, n1)
