# Coach AGZ — "Collaborative coaching" Reel. 1080x1920, 30 fps.
# Footage is never graded. Overlays live in the top zone, a drop-frame or a split window so the face stays clear.
import json, subprocess, sys, math
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
HERE = sys.argv[1]; F = HERE + '/../fonts/'
W, H, FPS = 1080, 1920, 30
WORDS = json.load(open(HERE + '/words_cut.json'))
CUTS = [3.1667, 13.9001, 17.2334, 18.6667, 34.4667, 40.5667, 49.8667, 69.5334, 84.7001, 86.5001, 89.4001, 92.1667, 92.8667, 94.0001]
DUR = 95.6667; MID = DUR / 2
GOLD = (201, 169, 110); CREAM = (244, 241, 234); NAVY = (14, 17, 23); MUTED = (150, 150, 158)
RED = (255, 34, 28); VGOLD = (255, 194, 26); CYAN = (0, 229, 255); GREEN = (30, 255, 110); DEEP = (2, 3, 8)
INK = (6, 8, 14); WHITE = (255, 255, 255); BLUE = (79, 163, 224); AMBER = (240, 160, 48); SGREEN = (60, 203, 106)
MONO = 'JBMono-500.ttf'; MONOB = 'JBMono-700.ttf'; BEB = 'BebasNeue.ttf'; DMB = 'DMSans-700.ttf'; DMR = 'DMSans-400.ttf'
B8 = 'BarlowC-800.ttf'; B7 = 'BarlowC-700.ttf'; B6 = 'BarlowC-600.ttf'
_fc = {}
def f(n, s):
    k = (n, int(s))
    if k not in _fc: _fc[k] = ImageFont.truetype(F + n, int(s))
    return _fc[k]
def clamp(x, a=0, b=1): return max(a, min(b, x))
def expo(x): x = clamp(x); return 1 if x >= 1 else 1 - 2 ** (-10 * x)
def ease_io(x): x = clamp(x); return 4 * x ** 3 if x < .5 else 1 - (-2 * x + 2) ** 3 / 2
def back(x, s=1.2): x = clamp(x); return 1 + (s + 1) * (x - 1) ** 3 + s * (x - 1) ** 2   # used only for heavy recoil, small s
def lerp(a, b, t): return a + (b - a) * t
def A(c, a): return tuple(c[:3]) + (int(clamp(a) * 255),)
def appear(t, t0, d=0.16): return expo((t - t0) / d)
def win(t, t0, t1, fi=0.2, fo=0.18): return min(expo((t - t0) / fi), 1 - ease_io((t - t1) / fo)) if t0 - 0.001 <= t <= t1 + fo else 0
GL = None   # bloom layer (ImageDraw) for the current frame

# ---------------- primitives ----------------
def txt(d, x, y, s, font, col, a=1.0, anchor=None):
    if a > 0.003: d.text((x, y), s, font=font, fill=A(col, a), anchor=anchor)
def brackets(d, x0, y0, x1, y1, col, L=34, w=4):
    for (cx, cy, sx, sy) in [(x0, y0, 1, 1), (x1, y0, -1, 1), (x0, y1, 1, -1), (x1, y1, -1, -1)]:
        d.line([(cx, cy), (cx + sx * L, cy)], fill=col, width=w); d.line([(cx, cy), (cx, cy + sy * L)], fill=col, width=w)
def lit_bar(d, x0, y0, x1, y1, col, a=1.0):
    h = max(1, int(y1 - y0))
    for i in range(h):
        k = i / h; c = tuple(int(min(255, v * (1.18 - 0.36 * k) + (40 if k < 0.12 else 0))) for v in col)
        d.line([(x0, y0 + i), (x1, y0 + i)], fill=c + (int(255 * clamp(a)),))
def tag(d, x, y, label, col=RED, size=30, a=1.0, glow=True, fg=None):
    if a <= 0.003: return x
    fn = f(MONOB, size); tw = d.textlength(label, font=fn); h = size + 16
    lit_bar(d, x, y, x + tw + 24, y + h, col, a)
    d.text((x + 12, y + 6), label, font=fn, fill=A(fg or (INK if col in (VGOLD, GREEN, CYAN) else WHITE), a))
    if GL and glow: GL.rectangle([x - 4, y - 4, x + tw + 28, y + h + 4], outline=A(col, a), width=8)
    return x + tw + 24
def check(d, x, y, col, s=1.0, a=1.0):
    pts = [(x, y + 16 * s), (x + 10 * s, y + 28 * s), (x + 30 * s, y + 2 * s)]
    d.line(pts, fill=A(col, a), width=int(6 * s))
    if GL: GL.line(pts, fill=A(col, a), width=int(12 * s))
def cross(d, x, y, col, s=1.0, a=1.0):
    for p in [[(x, y), (x + 28 * s, y + 28 * s)], [(x + 28 * s, y), (x, y + 28 * s)]]:
        d.line(p, fill=A(col, a), width=int(6 * s))
        if GL: GL.line(p, fill=A(col, a), width=int(12 * s))
def arrow(d, x0, y0, x1, y1, col, w=5, a=1.0, L=18):
    d.line([(x0, y0), (x1, y1)], fill=A(col, a), width=w)
    ang = math.atan2(y1 - y0, x1 - x0)
    d.polygon([(x1, y1), (x1 - L * math.cos(ang - 0.45), y1 - L * math.sin(ang - 0.45)), (x1 - L * math.cos(ang + 0.45), y1 - L * math.sin(ang + 0.45))], fill=A(col, a))
def tri(d, x, y, up, col, s=22, a=1.0):
    pts = [(x, y + s), (x + s, y + s), (x + s / 2, y)] if up else [(x, y), (x + s, y), (x + s / 2, y + s)]
    d.polygon(pts, fill=A(col, a))
    if GL: GL.polygon(pts, fill=A(col, a))
def frosted(im, box, dark=0.88, blur=12):
    x0, y0, x1, y1 = [int(v) for v in box]
    x0 = max(0, x0); y0 = max(0, y0); x1 = min(W, x1); y1 = min(H, y1)
    if x1 <= x0 or y1 <= y0: return
    reg = im.crop((x0, y0, x1, y1)).convert('RGB').filter(ImageFilter.GaussianBlur(blur))
    m = Image.new('L', reg.size, 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, reg.width - 1, reg.height - 1], radius=22, fill=255)
    im.paste(Image.blend(reg, Image.new('RGB', reg.size, DEEP), dark).convert('RGBA'), (x0, y0), m)
def panel_frame(im, d, box, a, left, right, col=VGOLD, handle=True):
    x0, y0, x1, y1 = box
    d.rounded_rectangle([x0, y0, x1, y1], radius=22, outline=A(col, 0.55 * a), width=2)
    brackets(d, x0 + 2, y0 + 2, x1 - 2, y1 - 2, A(col, a), 40, 6)
    if GL: brackets(GL, x0, y0, x1, y1, A(col, a), 40, 12)
    if left:
        d.ellipse([x0 + 28, y0 + 28, x0 + 44, y0 + 44], fill=A(RED, a if int(T_NOW * 4) % 2 == 0 else a / 3))
        txt(d, x0 + 58, y0 + 20, left, f(MONOB, 27), WHITE, a)
    if right:
        fr = f(MONOB, 27); tw = d.textlength(right, font=fr); txt(d, x1 - 32 - tw, y0 + 20, right, fr, col, a)
    if handle:
        fh = f(MONO, 20); tw = d.textlength('@COACH.AGZ', font=fh); txt(d, x1 - 28 - tw, y1 - 36, '@COACH.AGZ', fh, MUTED, a * 0.9)

# ---------------- layout modes ----------------
# M2 = drop-frame (footage slides down so a taller panel fits above the face)
# M3 = split window (footage shrinks into a framed window, graphic above, face still large)
M2_SPANS = [(21.75, 36.25), (65.25, 79.10)]
M3_SPANS = [(45.80, 59.60)]
def span_amt(t, spans, fi=0.32, fo=0.32):
    v = 0
    for a, b in spans:
        if a <= t <= b + fo: v = max(v, min(ease_io((t - a) / fi), 1 - ease_io((t - b) / fo)))
    return v
DROP = 170
WIN_SRC = (0, 360, 1080, 1540)      # region of the source shown in the split window
WIN_DST = (215, 690, 865, 1406)     # same aspect (1080x1180 -> 650x710.4)

# ---------------- text hook (frame 0) + topic band ----------------
HOOK_END = 3.5
def text_hook(d, t):
    if t >= HOOK_END + 0.15: return
    a = 1 - clamp((t - HOOK_END) / 0.15)
    s = lerp(1.0, 1.04, clamp(t / HOOK_END))
    l1a, l1b = 'The ', 'DAILY CHECK-INS'; l2 = 'your coach skips'
    fn = f(B8, int(104 * s)); y0 = 300 - (s - 1) * 60
    w1 = d.textlength(l1a + l1b, font=fn); w2 = d.textlength(l2, font=fn)
    bw = max(w1, w2) + 70; bx = (W - bw) / 2
    d.rounded_rectangle([bx, y0 - 18, bx + bw, y0 + 2 * 112 * s + 14], radius=22, fill=A((6, 7, 12), 0.80 * a))
    d.rectangle([bx, y0 - 18, bx + 8, y0 + 2 * 112 * s + 14], fill=A(GOLD, a))
    x = (W - w1) / 2
    d.text((x, y0), l1a, font=fn, fill=A(WHITE, a)); xx = x + d.textlength(l1a, font=fn)
    d.text((xx, y0), l1b, font=fn, fill=A(VGOLD, a))
    if GL: GL.text((xx, y0), l1b, font=fn, fill=A(VGOLD, a * 0.55))
    d.text(((W - w2) / 2, y0 + 112 * s), l2, font=fn, fill=A(WHITE, a))
def topic_band(d, t):
    if t < HOOK_END or t > MID + 0.15: return
    a = min(appear(t, HOOK_END, 0.15), 1 - clamp((t - MID) / 0.15))
    y0, y1 = 212, 290
    d.rectangle([8, y0, W, y1], fill=A(NAVY, 0.90 * a))
    d.line([(48, y0 + 39), (84, y0 + 39)], fill=A(GOLD, a), width=4)
    fn = f(B8, 54); x = 100
    for s, c in [('What ', CREAM), ('ELITE COACHING', VGOLD), (' tracks', CREAM)]:
        txt(d, x, y0 + 8, s, fn, c, a); x += d.textlength(s, font=fn)
    fh = f(MONO, 22); tw = d.textlength('@coach.agz', font=fh); txt(d, W - 40 - tw, y0 + 28, '@coach.agz', fh, GOLD, a)

# ---------------- S1 · check-in cadence grid (top deck, grows out of the band) ----------------
S1 = (3.20, 9.95)
def s1(im, t):
    a0 = win(t, *S1, fi=0.22)
    if a0 <= 0: return
    g = expo((t - S1[0]) / 0.28)               # grows down from the band
    x0, x1, y0 = 48, 1032, 300; y1 = lerp(y0 + 20, 620, g)
    frosted(im, (x0, y0, x1, y1), 0.90)
    d = ImageDraw.Draw(im, 'RGBA'); panel_frame(im, d, (x0, y0, x1, y1), a0, 'CHECK-IN CADENCE', 'WEEK 01')
    if g < 0.85: return
    a = a0 * clamp((g - 0.85) / 0.15)
    days = ['M', 'T', 'W', 'T', 'F', 'S', 'S']; cx0 = 250; cw = 104
    for i, dd in enumerate(days): txt(d, cx0 + i * cw + cw / 2, 372, dd, f(MONOB, 26), MUTED, a, 'mm')
    rows = [('WEEKLY', 432), ('DAILY', 496), ('BP', 560)]
    for nm, y in rows:
        txt(d, 80, y - 18, nm, f(B7, 38), CREAM, a)
        d.line([(cx0, y + 26), (cx0 + 7 * cw, y + 26)], fill=A((45, 48, 62), a), width=1)
    # weekly: one heavy gold block on Sunday
    if t >= 3.32:
        p = expo((t - 3.32) / 0.18); bx = cx0 + 6 * cw + 10; by = 432 - 20
        lit_bar(d, bx, lerp(by - 30, by, p), bx + cw - 20, lerp(by + 10, by + 40, p), VGOLD, a * p)
        if GL: GL.rectangle([bx, by, bx + cw - 20, by + 40], outline=A(VGOLD, a * p), width=8)
    # daily: ticks sweep Monday -> Sunday
    for i in range(7):
        tt = 4.30 + i * 0.07
        if t >= tt: check(d, cx0 + i * cw + 36, 478, GREEN, 1.0, a * appear(t, tt, 0.1))
    # BP: small pulse marks every day
    for i in range(7):
        tt = 5.40 + i * 0.06
        if t >= tt:
            q = a * appear(t, tt, 0.12); bx = cx0 + i * cw + 22; by = 560
            pts = [(bx, by), (bx + 14, by), (bx + 22, by - 18), (bx + 32, by + 16), (bx + 42, by - 6), (bx + 60, by)]
            d.line(pts, fill=A(RED, q), width=4)
            if GL: GL.line(pts, fill=A(RED, q), width=8)
    # constant communication: a live signal line under the grid
    if t >= 6.28:
        q = a * appear(t, 6.28, 0.25); xs = np.linspace(80, 1000, 140)
        span = clamp((t - 6.28) / 0.6)
        pts = [(x, 596 + 7 * math.sin(x / 22 - t * 9)) for x in xs[:max(2, int(140 * span))]]
        d.line(pts, fill=A(CYAN, q * 0.9), width=3)
        if GL: GL.line(pts, fill=A(CYAN, q), width=6)
def s1_chips(im, t):
    # FEEL / SLEEP / FOOD status chips ride on the panel's bottom edge
    a0 = win(t, *S1)
    if a0 <= 0 or t < 7.70: return
    d = ImageDraw.Draw(im, 'RGBA'); x = 250
    for nm, tt in [('FEEL', 7.70), ('SLEEP', 8.64), ('FOOD', 9.52)]:
        if t >= tt:
            p = expo((t - tt) / 0.14); x = tag(d, x, lerp(650, 636, p), nm + ' ✓' if False else nm, CYAN, 28, a0 * p) + 14

# ---------------- S2 · check-in form (light paper, slides in) ----------------
S2 = (10.10, 16.95)
FORM = None
def make_form():
    im = Image.new('RGBA', (900, 330), (238, 236, 230, 255)); d = ImageDraw.Draw(im)
    d.rectangle([0, 0, 900, 62], fill=(210, 10, 20)); d.text((24, 12), 'DAILY CHECK-IN · CLIENT LOG', font=f(MONOB, 30), fill=WHITE)
    d.text((700, 16), 'DAY 23', font=f(MONOB, 26), fill=(255, 220, 210))
    for i, k in enumerate(['MOOD', 'CONFLICT', 'PATTERN', 'CAUSE']):
        y = 82 + i * 62; d.text((24, y + 10), k, font=f(MONOB, 26), fill=(90, 92, 100)); d.line([(20, y + 56), (880, y + 56)], fill=(205, 203, 198), width=2)
    return im
def s2(im, t):
    global FORM
    a0 = win(t, *S2, fi=0.18, fo=0.16)
    if a0 <= 0: return
    if FORM is None: FORM = make_form()
    p = expo((t - S2[0]) / 0.30); ox = lerp(700, 0, p); rot = lerp(-4, 0, expo((t - S2[0] - 0.05) / 0.4))
    x0, y0 = 90 + ox, 296
    lay = Image.new('RGBA', (900, 330), (0, 0, 0, 0)); lay.alpha_composite(FORM); d = ImageDraw.Draw(lay, 'RGBA')
    INKD = (20, 22, 30)
    if t >= 10.74:   # mood + conflict filled in
        q = appear(t, 10.74, 0.12); d.text((260, 88), 'irritable', font=f(DMB, 34), fill=A(INKD, q))
        tri(d, 420, 100, False, (210, 10, 20), 20, q)
    if t >= 11.02:
        q = appear(t, 11.02, 0.12); d.text((260, 150), 'yes · argued w/ partner', font=f(DMB, 34), fill=A((210, 10, 20), q))
    if t >= 12.58:   # pattern: 14-day strip, one red day
        q = appear(t, 12.58, 0.14)
        for i in range(14):
            cx = 268 + i * 40; red = (i == 13)
            col = (210, 10, 20) if red else (150, 200, 160)
            if t >= 12.62 + i * 0.03: d.ellipse([cx, 218, cx + 24, 242], fill=A(col, q))
        if t >= 13.32: d.text((840, 214), '1/14', font=f(MONOB, 22), fill=A((90, 92, 100), appear(t, 13.32)))
    if t >= 14.26:   # cause: her | compound toggle
        q = appear(t, 14.26, 0.12)
        for j, (nm, tt) in enumerate([('HER', 14.26), ('COMPOUND', 15.30)]):
            bx = 260 + j * 200; on = (j == 1 and t >= 15.30) or (j == 0 and 14.26 <= t < 15.30)
            fill = (210, 10, 20) if (on and j == 1) else ((40, 44, 56) if on else (215, 213, 208))
            d.rounded_rectangle([bx, 276, bx + (110 if j == 0 else 230), 316], radius=8, fill=A(fill, q))
            d.text((bx + 14, 280), nm, font=f(MONOB, 26), fill=A(WHITE if on else (90, 92, 100), q))
    if rot != 0: lay = lay.rotate(rot, resample=Image.BICUBIC, expand=False)
    sh = Image.new('RGBA', (980, 410), (0, 0, 0, 0)); ImageDraw.Draw(sh).rectangle([40, 50, 940, 380], fill=(0, 0, 0, 150))
    sh = sh.filter(ImageFilter.GaussianBlur(16)); sh.putalpha(sh.split()[3].point(lambda v: int(v * a0)))
    im.alpha_composite(sh, (int(x0 - 40), int(y0 - 30)))
    lay.putalpha(lay.split()[3].point(lambda v: int(v * a0))); im.alpha_composite(lay, (int(x0), int(y0)))
    d = ImageDraw.Draw(im, 'RGBA')
    if t >= 15.30:   # forensic bracket + verdict tag on COMPOUND
        q = a0 * expo((t - 15.30) / 0.14); bx0, by0 = x0 + 452, y0 + 268
        brackets(d, bx0, by0, bx0 + 246, by0 + 56, A(RED, q), 18, 6)
        if GL: brackets(GL, bx0, by0, bx0 + 246, by0 + 56, A(RED, q), 18, 12)
        if t >= 15.66: tag(d, x0 + 600, y0 + 340, 'SIDE EFFECT?', RED, 28, a0 * appear(t, 15.66))

# ---------------- S4 · radar (drop-frame) -> S5 · bell curve (same panel, handoff) ----------------
S45 = (21.85, 36.25)
RAD_C = (540, 548); RAD_R = 168
AXES = [('MOOD', 22.06), ('SLEEP', 22.56), ('COGNITION', 23.06), ('FOCUS', 23.72), ('RELATIONSHIPS', 24.26)]
VAL = [0.82, 0.64, 0.9, 0.72, 0.58]; PREV = [0.6, 0.78, 0.66, 0.52, 0.74]
def s45(im, t):
    a0 = win(t, *S45, fi=0.26, fo=0.2)
    if a0 <= 0: return
    pin = expo((t - S45[0]) / 0.26); sc = lerp(0.95, 1, pin)
    x0, y0, x1, y1 = 48, 300, 1032, 780
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2; w2, h2 = (x1 - x0) / 2 * sc, (y1 - y0) / 2 * sc
    box = (cx - w2, cy - h2, cx + w2, cy + h2)
    frosted(im, box, 0.90)
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay, 'RGBA')
    radar_a = 1 - ease_io((t - 28.55) / 0.35)
    if radar_a > 0: radar(d, t, radar_a)
    if t >= 28.6: bell(d, t, ease_io((t - 28.6) / 0.35))
    if pin < 1: lay = lay.filter(ImageFilter.GaussianBlur(6 * (1 - pin)))
    lay.putalpha(lay.split()[3].point(lambda v: int(v * a0))); im.alpha_composite(lay)
    d = ImageDraw.Draw(im, 'RGBA')
    panel_frame(im, d, box, a0, 'DATA POINTS' if t < 28.6 else 'OPTIMAL vs REFERENCE', 'TRACKED' if t < 28.6 else 'YOUR LABS')
def radar(d, t, a):
    cx, cy = RAD_C; n = len(AXES)
    ang = [-math.pi / 2 + i * 2 * math.pi / n for i in range(n)]
    for k in (0.33, 0.66, 1.0):
        pts = [(cx + RAD_R * k * math.cos(g), cy + RAD_R * k * math.sin(g)) for g in ang]
        d.line(pts + [pts[0]], fill=A((60, 66, 86), a), width=2)
    for i, (nm, tt) in enumerate(AXES):
        if t < tt: continue
        q = a * appear(t, tt, 0.14); g = ang[i]
        ex, ey = cx + RAD_R * math.cos(g), cy + RAD_R * math.sin(g)
        d.line([(cx, cy), (lerp(cx, ex, q), lerp(cy, ey, q))], fill=A((110, 116, 140), q), width=2)
        lx, ly = cx + (RAD_R + 30) * math.cos(g), cy + (RAD_R + 26) * math.sin(g)
        anc = 'mm' if abs(math.cos(g)) < 0.3 else ('lm' if math.cos(g) > 0 else 'rm')
        txt(d, lx, ly, nm, f(B7, 34), WHITE, q, anc)
    # previous-week ghost (gold), appears on "track"
    if t >= 27.16:
        q = a * appear(t, 27.16, 0.3)
        pts = [(cx + RAD_R * PREV[i] * math.cos(ang[i]), cy + RAD_R * PREV[i] * math.sin(ang[i])) for i in range(n)]
        d.line(pts + [pts[0]], fill=A(VGOLD, q * 0.9), width=3)
        if GL: GL.line(pts + [pts[0]], fill=A(VGOLD, q * 0.6), width=6)
        txt(d, 92, 714, '— LAST WEEK', f(MONOB, 22), VGOLD, q); txt(d, 92, 742, '— THIS WEEK', f(MONOB, 22), CYAN, q)
    # current polygon: each vertex shoots out on its word
    pts = []
    for i, (nm, tt) in enumerate(AXES):
        v = VAL[i] * expo((t - tt - 0.04) / 0.22) if t >= tt else 0
        pts.append((cx + RAD_R * v * math.cos(ang[i]), cy + RAD_R * v * math.sin(ang[i])))
    if t >= AXES[0][1]:
        d.polygon(pts, fill=A(CYAN, a * 0.18)); d.line(pts + [pts[0]], fill=A(CYAN, a), width=4)
        if GL: GL.line(pts + [pts[0]], fill=A(CYAN, a), width=9)
        for p in pts: d.ellipse([p[0] - 7, p[1] - 7, p[0] + 7, p[1] + 7], fill=A(WHITE, a))
    # "data points": a scan sweep circles once, dots pulse
    if 25.46 <= t <= 26.9:
        g = -math.pi / 2 + (t - 25.46) / 1.2 * 2 * math.pi
        d.line([(cx, cy), (cx + RAD_R * math.cos(g), cy + RAD_R * math.sin(g))], fill=A(CYAN, a * 0.8), width=3)
        if GL: GL.line([(cx, cy), (cx + RAD_R * math.cos(g), cy + RAD_R * math.sin(g))], fill=A(CYAN, a), width=8)
    if t >= 25.46: tag(d, 760, 712, '5 DATA POINTS', CYAN, 24, a * appear(t, 25.46))
def bell(d, t, a):
    x0, x1, base = 110, 970, 690; top = 430
    def yv(x): z = (x - 540) / 175; return base - (base - top) * math.exp(-z * z / 2)
    # curve draws left -> right
    pr = clamp((t - 28.6) / 0.7); xs = np.linspace(x0, x1, 180)
    pts = [(x, yv(x)) for x in xs[:max(2, int(180 * pr))]]
    d.line([(x0, base), (x1, base)], fill=A((90, 94, 110), a), width=2)
    d.line(pts, fill=A(CREAM, a), width=4)
    # optimal band (gold, narrow, upper part) on "optimal"
    if t >= 31.02:
        q = a * appear(t, 31.02, 0.22); ox0, ox1 = 640, 742
        poly = [(ox0, base)] + [(x, yv(x)) for x in np.linspace(ox0, ox1, 30)] + [(ox1, base)]
        d.polygon(poly, fill=A(VGOLD, q * 0.45)); d.line([(ox0, base), (ox0, yv(ox0))], fill=A(VGOLD, q), width=4); d.line([(ox1, base), (ox1, yv(ox1))], fill=A(VGOLD, q), width=4)
        if GL: GL.polygon(poly, fill=A(VGOLD, q * 0.5))
        tag(d, 600, 372, 'YOUR OPTIMAL', VGOLD, 26, q)
    # reference range: wide dashed bounds, 95% labelled "normal"
    if t >= 32.44:
        q = a * appear(t, 32.44, 0.2); rx0, rx1 = 540 - 1.96 * 175, 540 + 1.96 * 175
        for x in (rx0, rx1):
            for yy in range(int(top - 30), base, 18): d.line([(x, yy), (x, yy + 9)], fill=A(MUTED, q), width=3)
        d.line([(rx0, base + 22), (rx1, base + 22)], fill=A(MUTED, q), width=3)
        txt(d, 540, base + 44, 'REFERENCE RANGE · MIDDLE 95% = "NORMAL"', f(MONOB, 22), MUTED, q, 'mm')
        for x, s in ((x0 + 6, '2.5%'), (x1 - 70, '2.5%')): txt(d, x, base - 34, s, f(MONOB, 20), RED, q)
    if t >= 33.60:   # lab printout label
        q = a * appear(t, 33.60, 0.15); tag(d, 92, 372, 'LAB PRINTOUT', (90, 94, 110), 24, q, glow=False, fg=WHITE)
    if t >= 35.06:   # who the range is built from
        q = a * appear(t, 35.06, 0.14); x = tag(d, 92, 426, 'SICK', RED, 26, q); tag(d, x + 10, 426, 'SEDENTARY', RED, 26, a * appear(t, 35.74, 0.14))


# ---------------- S6 · response monitor (CRT power-on) ----------------
S6 = (36.40, 40.50)
def s6(im, t):
    a0 = win(t, *S6, fi=0.12, fo=0.14)
    if a0 <= 0: return
    p = expo((t - S6[0]) / 0.22); cy = 455; hh = lerp(4, 165, p)
    x0, x1 = lerp(500, 48, min(1, p * 3)), lerp(580, 1032, min(1, p * 3)); box = (x0, cy - hh, x1, cy + hh)
    frosted(im, box, 0.94, 6)
    d = ImageDraw.Draw(im, 'RGBA')
    panel_frame(im, d, box, a0 if p > 0.6 else a0 * 0.4, 'RESPONSE MONITOR' if p > 0.8 else '', 'LIVE' if p > 0.8 else '', col=CYAN)
    if p < 0.8: return
    rows = [('SIDE EFFECTS', 37.16, RED), ('GROWTH', 38.36, GREEN), ('COMPOUND', 39.50, VGOLD)]
    for i, (nm, tt, col) in enumerate(rows):
        y = 380 + i * 72
        txt(d, 80, y - 20, nm, f(B7, 34), WHITE if t >= tt else (90, 94, 110), a0)
        d.line([(330, y), (1000, y)], fill=A((40, 44, 58), a0), width=1)
        if t >= tt:
            span = clamp((t - tt) / 0.9); n = int(170 * span) + 2
            xs = np.linspace(330, lerp(330, 1000, span), n); pts = []
            for x in xs:
                ph = (x - 330) / 670 * 6 * math.pi
                if i == 0: v = math.sin(ph) * 0.4 + (1.6 if int((x - 330) / 70) % 3 == 1 and (x % 70) < 14 else 0) * math.sin((x % 70) / 14 * math.pi)
                elif i == 1: v = (x - 330) / 670 * 1.4 - 0.6 + 0.15 * math.sin(ph * 2)
                else: v = 0.6 * math.sin(ph * 0.7) * math.exp(-(x - 330) / 900)
                pts.append((x, y - v * 22))
            d.line(pts, fill=A(col, a0), width=4)
            if GL: GL.line(pts, fill=A(col, a0), width=9)
            ex, ey = pts[-1]; d.ellipse([ex - 7, ey - 7, ex + 7, ey + 7], fill=A(WHITE, a0))

# ---------------- S7 · dial gauge (heavy slide from left) ----------------
S7 = (40.62, 45.70)
def s7(im, t):
    a0 = win(t, *S7, fi=0.2, fo=0.16)
    if a0 <= 0: return
    p = clamp((t - S7[0]) / 0.36); ox = lerp(-1000, 0, back(p, 0.6))
    x0, y0, x1, y1 = 48 + ox, 300, 1032 + ox, 620
    frosted(im, (x0, y0, x1, y1), 0.90)
    d = ImageDraw.Draw(im, 'RGBA'); panel_frame(im, d, (x0, y0, x1, y1), a0, 'PROTOCOL FIT', 'DIAL-IN')
    gx, gy, R = x0 + 735, y0 + 268, 190
    # spectrum arc: blue (low) -> green (dialed) -> amber (high)
    for k in range(60):
        g0 = math.pi + k * math.pi / 60; g1 = g0 + math.pi / 60 + 0.01; u = k / 59
        col = tuple(int(lerp(c1, c2, (u * 2) % 1 if u < 0.5 else (u - 0.5) * 2)) for c1, c2 in zip(BLUE if u < 0.5 else SGREEN, SGREEN if u < 0.5 else AMBER))
        d.arc([gx - R, gy - R, gx + R, gy + R], math.degrees(g0), math.degrees(g1), fill=A(col, a0), width=22)
    if GL: GL.arc([gx - R, gy - R, gx + R, gy + R], 180, 360, fill=A(SGREEN, a0 * 0.5), width=26)
    for nm, u in [('LOW', 0.08), ('DIALED IN', 0.5), ('HIGH', 0.92)]:
        g = math.pi + u * math.pi; txt(d, gx + (R + 38) * math.cos(g), gy + (R + 30) * math.sin(g) + 4, nm, f(MONOB, 20), MUTED, a0, 'mm')
    # needle: wanders on "dial", hunts on "make damn sure", locks green on "around you"
    if t < 40.96: u = 0.12
    elif t < 43.68: u = 0.12 + 0.62 * expo((t - 40.96) / 0.5) + 0.07 * math.sin((t - 40.96) * 7)
    elif t < 44.88: u = lerp(0.74, 0.36, ease_io((t - 43.68) / 0.6)) + 0.03 * math.sin(t * 15)
    else: u = lerp(0.40, 0.5, expo((t - 44.88) / 0.25))
    g = math.pi + u * math.pi; nx, ny = gx + (R - 30) * math.cos(g), gy + (R - 30) * math.sin(g)
    locked = t >= 44.88
    d.line([(gx, gy), (nx, ny)], fill=A(WHITE if not locked else GREEN, a0), width=7)
    if GL: GL.line([(gx, gy), (nx, ny)], fill=A(GREEN if locked else WHITE, a0 * 0.7), width=12)
    d.ellipse([gx - 16, gy - 16, gx + 16, gy + 16], fill=A(WHITE, a0))
    # left column: the inputs being dialled
    for i, (nm, tt) in enumerate([('PRESCRIPTIONS', 41.76), ('ANCILLARIES', 42.50)]):
        if t >= tt:
            q = a0 * appear(t, tt, 0.14); y = y0 + 92 + i * 80
            lit_bar(d, x0 + 40, y, x0 + 50, y + 50, VGOLD, q); txt(d, x0 + 66, y + 2, nm, f(B8, 46), WHITE, q)
    if locked:
        q = a0 * appear(t, 44.88, 0.12); tag(d, x0 + 40, y0 + 252, 'BUILT AROUND YOU', GREEN, 28, q)

# ---------------- S8 · split window: bloodwork expectations -> simplified ----------------
S8 = (45.90, 59.55)
LAB = None
LAB_ROWS = [('Hematocrit', True), ('Estradiol', True), ('HDL', False), ('LH', False)]
def make_lab():
    im = Image.new('RGBA', (900, 330), (250, 250, 248, 255)); d = ImageDraw.Draw(im)
    d.rectangle([0, 0, 900, 58], fill=(16, 24, 48)); d.text((22, 12), 'LAB REPORT · ENHANCED PANEL', font=f(MONOB, 28), fill=WHITE)
    d.text((560, 70), 'RESULT', font=f(MONOB, 20), fill=(120, 120, 130)); d.text((740, 70), 'EXPECT', font=f(MONOB, 20), fill=(210, 10, 20))
    for i, (k, _) in enumerate(LAB_ROWS):
        y = 100 + i * 56; d.text((22, y + 6), k, font=f(DMB, 32), fill=(40, 42, 52))
        for j in range(5): d.rectangle([560 + j * 30, y + 18, 580 + j * 30, y + 26], fill=(200, 200, 206))
        d.line([(18, y + 52), (880, y + 52)], fill=(222, 222, 226), width=2)
    return im
def s8(im, t):
    global LAB
    a0 = win(t, *S8, fi=0.28, fo=0.2)
    if a0 <= 0: return
    if LAB is None: LAB = make_lab()
    d = ImageDraw.Draw(im, 'RGBA')
    txt(d, 70, 316, '—— YOUR BLOODWORK, EXPLAINED', f(MONOB, 26), VGOLD, a0 * appear(t, 46.22, 0.2))
    simp = ease_io((t - 55.70) / 0.45)          # dense doc collapses into one clear card
    if simp < 1:
        p = expo((t - 46.22) / 0.32); oy = 0; ox_in = lerp(1000, 0, p)
        stack = 0
        if t >= 53.34: stack = expo((t - 53.34) / 0.35)
        for k in (2, 1):                          # copies fan out behind on "each compound"
            if stack > 0:
                gx, gy = 90 + ox_in + 28 * k * stack, 360 - 22 * k * stack + oy
                cp = Image.new('RGBA', (900, 330), (236, 236, 232, 255)); cd = ImageDraw.Draw(cp)
                cd.rectangle([0, 0, 900, 58], fill=(30, 38, 62)); cd.text((22, 12), f'COMPOUND 0{k + 1}', font=f(MONOB, 28), fill=WHITE)
                cp.putalpha(int(255 * a0 * stack * (1 - simp))); im.alpha_composite(cp, (int(gx), int(gy)))
        lay = LAB.copy(); ld = ImageDraw.Draw(lay, 'RGBA')
        if t >= 49.98:   # expected-direction arrows tick in
            for i, (_, up) in enumerate(LAB_ROWS):
                tt = 50.32 + i * 0.22
                if t >= tt: q = appear(t, tt, 0.12); tri(ld, 760, 100 + i * 56 + 14, up, (210, 10, 20) if up else (20, 110, 210), 26, q)
        if t >= 53.34:
            q = appear(t, 53.34); ld.rectangle([600, 12, 880, 46], fill=A((210, 10, 20), q)); ld.text((614, 14), 'COMPOUND 01', font=f(MONOB, 24), fill=A(WHITE, q))
        sc = lerp(1, 0.4, simp); lw, lh = int(900 * sc), int(330 * sc)
        lay = lay.resize((lw, lh), Image.BICUBIC) if sc != 1 else lay
        lay.putalpha(lay.split()[3].point(lambda v: int(v * a0 * (1 - simp))))
        cx = lerp(90 + ox_in, 540 - lw / 2, simp); cy = lerp(360 + oy, 500 - lh / 2, simp)
        sh = Image.new('RGBA', (lw + 60, lh + 60), (0, 0, 0, 0)); ImageDraw.Draw(sh).rectangle([30, 36, lw + 30, lh + 36], fill=(0, 0, 0, int(140 * a0 * (1 - simp))))
        im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(14)), (int(cx - 30), int(cy - 30)))
        im.alpha_composite(lay, (int(cx), int(cy)))
        d = ImageDraw.Draw(im, 'RGBA')
        if t >= 52.64 and simp <= 0: tag(d, 90 + 600, int(360 + oy + 340), '+ COMPOUNDS', RED, 26, a0 * appear(t, 52.64))
    if simp > 0:     # the simple version: three rows, one check
        q = a0 * simp; x0, y0, x1, y1 = 90, 352, 990, 650
        frosted(im, (x0, y0, x1, y1), 0.9); d = ImageDraw.Draw(im, 'RGBA')
        panel_frame(im, d, (x0, y0, x1, y1), q, 'SIMPLIFIED', 'YOUR VERSION', handle=False)
        for i, (k, s) in enumerate([('WHAT MOVES', 'HCT ↑  E2 ↑  HDL ↓  LH ↓'), ('WHY', 'the mechanism, in plain terms'), ('WHAT WE DO', 'the next step, decided')]):
            tt = 55.9 + i * 0.25
            if t >= tt:
                r = q * appear(t, tt, 0.14); y = y0 + 84 + i * 66
                txt(d, x0 + 36, y, k, f(B8, 42), VGOLD, r); txt(d, x0 + 300, y + 8, s, f(MONOB if i == 0 else DMB, 30), WHITE, r)
        if t >= 57.24:
            r = q * expo((t - 57.24) / 0.14); s = lerp(1.25, 1, r)
            tag(d, x1 - 300, y1 + 14, 'UNDERSTOOD', GREEN, int(30 * s), r)

# ---------------- S10 · two-section dashboard (drop-frame, app screen) ----------------
S10 = (65.35, 79.05)
def s10(im, t):
    a0 = win(t, *S10, fi=0.3, fo=0.2)
    if a0 <= 0: return
    p = expo((t - S10[0]) / 0.34); oy = lerp(-120, 0, p)
    x0, y0, x1, y1 = 48, 252 + oy, 1032, 780 + oy
    frosted(im, (x0, y0, x1, y1), 0.92)
    d = ImageDraw.Draw(im, 'RGBA'); panel_frame(im, d, (x0, y0, x1, y1), a0 * p, 'CLIENT REPORT', '', handle=True)
    tab2 = t >= 69.52
    # tab bar
    if t >= 66.70:
        q = a0 * appear(t, 66.70, 0.18)
        for j, nm in enumerate(['01  SUMMARY', '02  DEEP DIVE']):
            bx = x0 + 40 + j * 300; on = (j == 1) == tab2
            if on: lit_bar(d, bx, y0 + 70, bx + 280, y0 + 120, VGOLD, q)
            else: d.rectangle([bx, y0 + 70, bx + 280, y0 + 120], outline=A((80, 84, 100), q), width=2)
            txt(d, bx + 140, y0 + 95, nm, f(MONOB, 26), INK if on else MUTED, q, 'mm')
    cy0 = y0 + 146
    if not tab2:
        # summary: four KPI tiles with status lights + a bar sparkline each
        if t >= 67.70:
            tiles = [('HCT', 'WATCH', AMBER), ('E2', 'IN RANGE', GREEN), ('BP', 'IN RANGE', GREEN), ('LIPIDS', 'WATCH', AMBER)]
            for i, (nm, st, col) in enumerate(tiles):
                tt = 67.70 + i * 0.12
                if t < tt: continue
                q = a0 * appear(t, tt, 0.14); bx = x0 + 40 + i * 232; by = cy0 + lerp(20, 0, q)
                d.rounded_rectangle([bx, by, bx + 212, by + 330], radius=14, fill=A((14, 18, 28), q), outline=A(col, q), width=3)
                txt(d, bx + 18, by + 14, nm, f(BEB, 58), WHITE, q)
                d.ellipse([bx + 168, by + 26, bx + 192, by + 50], fill=A(col, q))
                if GL: GL.ellipse([bx + 160, by + 18, bx + 200, by + 58], fill=A(col, q))
                vals = [0.4, 0.55, 0.5, 0.7, 0.62] if col == AMBER else [0.5, 0.45, 0.55, 0.5, 0.52]
                for k, v in enumerate(vals):
                    hh = 150 * v * expo((t - tt - 0.1 - k * 0.04) / 0.2)
                    lit_bar(d, bx + 18 + k * 38, by + 250 - hh, bx + 46 + k * 38, by + 250, col if k == 4 else (70, 76, 96), q)
                txt(d, bx + 18, by + 278, st, f(MONOB, 22), col, q)
    else:
        sw = expo((t - 69.52) / 0.25)
        # deep dive: dense pages scroll past, then mechanism + forecast chart build
        if t < 73.64:
            off = (t - 69.52) * 260
            for k in range(8):
                yy = cy0 + 20 + k * 90 - off % 90
                if yy < cy0 or yy > y1 - 70: continue
                q = a0 * sw * 0.8
                d.rectangle([x0 + 40, yy, x0 + 40 + 220, yy + 14], fill=A(CREAM, q * 0.7))
                for j in range(3): d.rectangle([x0 + 40, yy + 26 + j * 16, x0 + 40 + [880, 760, 820][(k + j) % 3], yy + 34 + j * 16], fill=A((90, 94, 110), q))
            if t >= 69.82: tag(d, x0 + 600, cy0 - 10 + 330, 'IN-DEPTH · 24 PAGES' if False else 'IN-DEPTH ANALYSIS', CYAN, 26, a0 * appear(t, 69.82))
        else:
            q = a0 * appear(t, 73.64, 0.2)
            # mechanism: T -> aromatase -> E2 ; T -> 5AR -> DHT
            nodes = [('T', x0 + 70, cy0 + 70, CYAN), ('E2', x0 + 330, cy0 + 10, VGOLD), ('DHT', x0 + 330, cy0 + 130, RED)]
            for nm, nx, ny, col in nodes:
                d.rounded_rectangle([nx, ny, nx + 120, ny + 70], radius=12, fill=A((14, 18, 28), q), outline=A(col, q), width=3)
                txt(d, nx + 60, ny + 37, nm, f(BEB, 50), WHITE, q, 'mm')
            pr = clamp((t - 74.18) / 0.4)
            if pr > 0:
                arrow(d, x0 + 192, cy0 + 95, lerp(x0 + 192, x0 + 324, pr), lerp(cy0 + 95, cy0 + 50, pr), VGOLD, 4, q)
                arrow(d, x0 + 192, cy0 + 115, lerp(x0 + 192, x0 + 324, pr), lerp(cy0 + 115, cy0 + 160, pr), RED, 4, q)
            txt(d, x0 + 70, cy0 + 236, 'MECHANICS', f(MONOB, 22), MUTED, q)
            # forecast: measured line then dashed projection band ("what to expect")
            fx0, fx1, fyb = x0 + 520, x1 - 40, cy0 + 260
            d.line([(fx0, fyb), (fx1, fyb)], fill=A((90, 94, 110), q), width=2)
            meas = [0.30, 0.34, 0.33, 0.40]; xs = [lerp(fx0, fx0 + 210, i / 3) for i in range(4)]
            pts = [(x, fyb - v * 300) for x, v in zip(xs, meas)]
            d.line(pts, fill=A(CYAN, q), width=5)
            if GL: GL.line(pts, fill=A(CYAN, q), width=10)
            for pnt in pts: d.ellipse([pnt[0] - 7, pnt[1] - 7, pnt[0] + 7, pnt[1] + 7], fill=A(WHITE, q))
            txt(d, fx0, fyb + 14, 'MEASURED', f(MONOB, 20), CYAN, q)
            if t >= 75.64:
                r = q * appear(t, 75.64, 0.2); pr = clamp((t - 75.64) / 0.8)
                ex = lerp(pts[-1][0], fx1, pr); hi = lerp(pts[-1][1], fyb - 0.62 * 300, pr); lo = lerp(pts[-1][1], fyb - 0.42 * 300, pr)
                d.polygon([pts[-1], (ex, hi), (ex, lo)], fill=A(VGOLD, r * 0.28))
                for k in range(12):
                    u0, u1 = k / 12 * pr, (k + 0.5) / 12 * pr
                    d.line([(lerp(pts[-1][0], fx1, u0), lerp(pts[-1][1], fyb - 0.52 * 300, u0)), (lerp(pts[-1][0], fx1, u1), lerp(pts[-1][1], fyb - 0.52 * 300, u1))], fill=A(VGOLD, r), width=4)
                txt(d, fx1, fyb + 14, 'EXPECTED', f(MONOB, 20), VGOLD, r, 'ra')
            if t >= 78.0:
                r = q * appear(t, 78.0, 0.14); tag(d, fx0, cy0 - 6, 'ANY COMPOUND', RED, 24, r)

# ---------------- S11 · for life: timeline + chips (no panel, floats on a top scrim) ----------------
S11 = (81.40, 89.30)
def s11(im, t):
    a0 = win(t, *S11, fi=0.25, fo=0.2)
    if a0 <= 0: return
    d = ImageDraw.Draw(im, 'RGBA')
    sc = Image.new('RGBA', (W, 380), (0, 0, 0, 0)); sd = ImageDraw.Draw(sc)
    for y in range(380): sd.line([(0, y), (W, y)], fill=(2, 3, 8, int(200 * a0 * (1 - (y / 380) ** 2))))
    im.alpha_composite(sc, (0, 230)); d = ImageDraw.Draw(im, 'RGBA')
    y = 470; pr = expo((t - S11[0]) / 0.6)
    xe = lerp(80, 960, pr) if t < 88.38 else lerp(960, 1060, expo((t - 88.38) / 0.3))
    d.line([(80, y), (xe, y)], fill=A(VGOLD, a0), width=6)
    if GL: GL.line([(80, y), (xe, y)], fill=A(VGOLD, a0), width=12)
    if t >= 88.38: arrow(d, xe - 60, y, xe, y, VGOLD, 6, a0, 30)
    txt(d, 80, y + 22, 'NOW', f(MONOB, 24), MUTED, a0)
    for k, lab in enumerate(['30s', '40s', '50s', '60s+']):
        xx = 260 + k * 190
        if xx < xe: d.line([(xx, y - 12), (xx, y + 12)], fill=A(VGOLD, a0), width=4); txt(d, xx, y + 36, lab, f(MONOB, 22), MUTED, a0, 'mm')
    if t >= 83.26:   # the optimal line: flat and high across the decades
        q = a0 * appear(t, 83.26, 0.2); pr2 = clamp((t - 83.26) / 0.8)
        d.line([(80, y - 90), (lerp(80, 960, pr2), y - 90)], fill=A(GREEN, q), width=4)
        if GL: GL.line([(80, y - 90), (lerp(80, 960, pr2), y - 90)], fill=A(GREEN, q), width=8)
        txt(d, 84, y - 130, 'OPTIMAL, HELD', f(MONOB, 22), GREEN, q)
    x = 330
    for nm, tt in [('LEADER', 81.60), ('FATHER', 86.04), ('HUSBAND', 86.70)]:
        if t >= tt:
            p = expo((t - tt) / 0.16); yy = lerp(300, 318, p)
            fn = f(B8, 40); tw = d.textlength(nm, font=fn)
            d.rounded_rectangle([x, yy, x + tw + 36, yy + 56], radius=8, fill=A((40, 6, 10), a0 * p), outline=A(RED, a0 * p), width=3)
            if GL: GL.rounded_rectangle([x, yy, x + tw + 36, yy + 56], radius=8, outline=A(RED, a0 * p), width=7)
            txt(d, x + 18, yy + 4, nm, fn, (255, 190, 186), a0 * p); x += tw + 52
    if t >= 88.38: tag(d, 800, 520, 'FOR LIFE', VGOLD, 30, a0 * appear(t, 88.38))

# ---------------- S12 · CTA ----------------
LOGO = None
def s12(im, t):
    global LOGO
    if t < 89.50: return
    a = appear(t, 89.50, 0.2)
    x0, y0, x1, y1 = 48, 290, 1032, 640
    frosted(im, (x0, y0, x1, y1), 0.88)
    d = ImageDraw.Draw(im, 'RGBA')
    panel_frame(im, d, (x0, y0, x1, y1), a, '', '', handle=False)
    if LOGO is None:
        lg = Image.open(HERE + '/logo.jpg').convert('RGB'); s = min(lg.size)
        lg = lg.crop(((lg.width - s) // 2, (lg.height - s) // 2, (lg.width + s) // 2, (lg.height + s) // 2)).resize((150, 150), Image.LANCZOS)
        m = Image.new('L', (150, 150), 0); ImageDraw.Draw(m).ellipse([0, 0, 149, 149], fill=255); lg.putalpha(m); LOGO = lg
    lg = LOGO.copy(); lg.putalpha(lg.split()[3].point(lambda v: int(v * a))); im.alpha_composite(lg, (x0 + 36, y0 + 34))
    d = ImageDraw.Draw(im, 'RGBA')
    txt(d, x0 + 210, y0 + 40, 'COACH AGZ', f(B8, 46), GOLD, a); txt(d, x0 + 210, y0 + 92, '1:1 ELITE COACHING', f(MONOB, 24), CREAM, a)
    if t >= 89.56:   # heavy gold pill slams in on "Comment"
        b = expo((t - 89.56) / 0.12); s = lerp(1.15, 1.0, b)
        fn = f(BEB, int(96 * s)); label = 'COMMENT  "ELITE"'; tw = d.textlength(label, font=fn)
        bx = x0 + 36; by = y0 + 200
        lit_bar(d, bx, by, bx + tw + 44, by + int(104 * s), VGOLD, b); d.text((bx + 22, by + 6), label, font=fn, fill=A(INK, b))
        if GL: GL.rectangle([bx - 4, by - 4, bx + tw + 48, by + int(104 * s) + 4], outline=A(VGOLD, b), width=12)
    # "not just a protocol": a generic protocol sheet gets struck
    if t >= 93.32:
        q = appear(t, 93.32, 0.2); px, py = x0 + 760, y0 + 150
        d.rectangle([px, py, px + 170, py + 160], fill=A((236, 236, 232), q))
        d.rectangle([px, py, px + 170, py + 30], fill=A((90, 94, 110), q)); txt(d, px + 10, py + 4, 'PROTOCOL', f(MONOB, 20), WHITE, q)
        for k in range(5): d.rectangle([px + 12, py + 46 + k * 20, px + 12 + [140, 110, 130, 90, 120][k], py + 54 + k * 20], fill=A((170, 170, 176), q))
        if t >= 94.40:
            r = expo((t - 94.40) / 0.1); cross(d, px + 20, py + 15, RED, 4.6 * r + 0.01, r)
    fd = f(MONO, 18); txt(d, x0 + 36, y1 - 34, 'FOR RESEARCH & EDUCATIONAL PURPOSES ONLY', fd, MUTED, a)

# ---------------- captions ----------------
FIX = {'did': None}
def build_groups():
    G = []; cur = []
    for i, x in enumerate(WORDS):
        if cur:
            prev = WORDS[cur[-1]]
            if not x['w'].startswith('-') and (len(cur) >= 3 or x['s'] - prev['e'] > 0.28 or prev['w'][-1] in '.,?!' or any(prev['e'] - 0.01 < c <= x['s'] + 0.01 for c in CUTS)): G.append(cur); cur = []
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
def clean(w):
    w = w.upper().replace('-INS', 'INS').rstrip(',').rstrip('.')
    if w.startswith('-'): w = w[1:]
    return w
def words_display(g):
    out = []
    for i in g:
        w = WORDS[i]['w']
        if w.startswith('-') and out: out[-1] = out[-1] + '-' + clean(w); continue
        out.append(clean(w))
    return out
def captions(im, t, cap_y, size0):
    g = group_at(t)
    if not g: return
    d = ImageDraw.Draw(im, 'RGBA')
    # merge hyphen pieces (check -ins) for display, keep timing on the first piece
    disp = []; idx = []
    for i in g:
        w = WORDS[i]['w']
        if w.startswith('-') and disp: disp[-1] = disp[-1] + w.upper().rstrip(',.'); continue
        disp.append(w.upper().rstrip(',').rstrip('.') if not w.endswith('?') else w.upper()); idx.append(i)
    size = size0
    while True:
        fn = f(BEB, size); sp = d.textlength(' ', font=fn) + 14; wd = [d.textlength(w, font=fn) for w in disp]; tot = sum(wd) + sp * (len(disp) - 1)
        if tot <= 920: break
        size -= 4
    xs = []; x = (W - tot) / 2
    for w_ in wd: xs.append(x); x += w_ + sp
    act = 0
    for k, i in enumerate(idx):
        if WORDS[i]['s'] <= t: act = k
    g0 = WORDS[idx[0]]['s']; s = lerp(0.9, 1, expo((t - g0) / 0.10))
    cap = Image.new('RGBA', (W, 300), (0, 0, 0, 0)); cd = ImageDraw.Draw(cap); shd = Image.new('RGBA', (W, 300), (0, 0, 0, 0)); sd = ImageDraw.Draw(shd)
    prev = max(0, act - 1); bt = expo((t - WORDS[idx[act]]['s']) / 0.07) if act > 0 else 1
    bx0 = lerp(xs[prev], xs[act], bt) - 18; bx1 = lerp(xs[prev] + wd[prev], xs[act] + wd[act], bt) + 18
    for k, (w_, x_) in enumerate(zip(disp, xs)):
        if k != act: sd.text((x_ + 4, 46), w_, font=fn, fill=(0, 0, 0, 210))
    cap.alpha_composite(shd.filter(ImageFilter.GaussianBlur(6)))
    lit_bar(cd, bx0, 40 + size * 0.02, bx1, 40 + size * 0.98, RED)
    for k, (w_, x_) in enumerate(zip(disp, xs)): cd.text((x_, 40), w_, font=fn, fill=CREAM, stroke_width=0 if k == act else 3, stroke_fill=(0, 0, 0))
    if abs(s - 1) > 0.002:
        cap = cap.resize((int(W * s), int(300 * s)), Image.BICUBIC); ox = int((W - cap.width) / 2); oy = int(cap_y - 40 - (cap.height - 300) / 2)
    else: ox, oy = 0, int(cap_y - 40)
    im.alpha_composite(cap, (ox, oy))

# ---------------- camera ----------------
PUNCH = [(0.26, 3.1667, 1.08), (21.28, 21.75, 1.12), (61.84, 62.16, 1.12), (63.60, 65.25, 1.07), (89.56, 95.67, 1.0)]
def seg_idx(t): return sum(1 for c in CUTS if c <= t + 1e-6)
def zoom_at(t, m):
    for a, b, z in PUNCH:
        if a <= t < b:
            if a == 0.26: return lerp(1.0, z, expo((t - a) / 0.12))
            return z
    if m > 0.01: return 1.0                      # camera holds steady while a big graphic is up
    return 1.0 if seg_idx(t) % 2 == 0 else 1.06
def zoomed(src, z):
    if abs(z - 1) < 1e-3: return src
    big = src.resize((int(W * z), int(H * z)), Image.BICUBIC); ox = (big.width - W) // 2; oy = int((big.height - H) * 0.42)
    return big.crop((ox, oy, ox + W, oy + H))

# ---------------- frame ----------------
T_NOW = 0
def frame(src, t):
    global GL, T_NOW
    T_NOW = t
    m2 = span_amt(t, M2_SPANS); m3 = span_amt(t, M3_SPANS)
    src = zoomed(src, zoom_at(t, max(m2, m3)))
    if m3 > 0:
        blur = src.filter(ImageFilter.GaussianBlur(26 * m3))
        bg = Image.blend(src, Image.blend(blur, Image.new('RGB', (W, H), (5, 8, 16)), 0.62), m3)
        sx0, sy0, sx1, sy1 = WIN_SRC; dx0, dy0, dx1, dy1 = WIN_DST
        rx0, ry0, rx1, ry1 = [lerp(a, b, m3) for a, b in zip((sx0, sy0, sx1, sy1), (dx0, dy0, dx1, dy1))]
        win_im = src.crop(WIN_SRC).resize((int(rx1 - rx0), int(ry1 - ry0)), Image.BICUBIC)
        mk = Image.new('L', win_im.size, 0); ImageDraw.Draw(mk).rounded_rectangle([0, 0, win_im.width - 1, win_im.height - 1], radius=int(28 * m3), fill=255)
        bg.paste(win_im, (int(rx0), int(ry0)), mk)
        im = bg.convert('RGBA'); d = ImageDraw.Draw(im, 'RGBA')
        d.rounded_rectangle([rx0, ry0, rx1, ry1], radius=int(28 * m3), outline=A(VGOLD, m3), width=4)
    elif m2 > 0:
        off = int(DROP * ease_io(m2))
        bg = src.filter(ImageFilter.GaussianBlur(20)).point(lambda v: int(v * 0.35)) if off > 0 else src
        bg = bg.copy(); bg.paste(src.crop((0, 0, W, H - off)), (0, off))
        im = bg.convert('RGBA')
        if off > 0:   # soft seam between the revealed top and the shifted footage
            sm = Image.new('RGBA', (W, 80), (0, 0, 0, 0)); sdd = ImageDraw.Draw(sm)
            for y in range(80): sdd.line([(0, y), (W, y)], fill=(2, 3, 8, int(160 * (1 - y / 80))))
            im.alpha_composite(sm, (0, off))
    else:
        im = src.convert('RGBA')
    # top + bottom scrims for legibility (graphics/captions only; no grade on the face)
    yy = np.arange(H); a = np.where(yy > 1240, np.clip((yy - 1240) / 300, 0, 1) * 100, 0); a = np.maximum(a, np.where(yy < 460, (1 - yy / 460) * 110, 0))
    im.alpha_composite(Image.merge('RGBA', [Image.new('L', (W, H), c) for c in NAVY] + [Image.fromarray(np.repeat(a.astype(np.uint8)[:, None], W, 1))]))
    glow = Image.new('RGBA', (W, H), (0, 0, 0, 0)); GL = ImageDraw.Draw(glow, 'RGBA')
    s1(im, t); s1_chips(im, t); s2(im, t); s45(im, t); s6(im, t); s7(im, t); s8(im, t); s10(im, t); s11(im, t); s12(im, t)
    d = ImageDraw.Draw(im, 'RGBA'); topic_band(d, t); text_hook(d, t)
    GL = None
    if glow.getbbox():
        sm = glow.resize((W // 4, H // 4), Image.BILINEAR)
        g1 = np.asarray(sm.filter(ImageFilter.GaussianBlur(3.5))).astype(np.float32) / 255; g2 = np.asarray(sm.filter(ImageFilter.GaussianBlur(10))).astype(np.float32) / 255
        prem = np.clip(g1[..., :3] * g1[..., 3:] * 2.3 + g2[..., :3] * g2[..., 3:] * 1.8, 0, 1)
        prem = np.asarray(Image.fromarray((prem * 255).astype(np.uint8)).resize((W, H), Image.BILINEAR)).astype(np.float32) / 255
        b = np.asarray(im.convert('RGB')).astype(np.float32) / 255
        im = Image.fromarray(((1 - (1 - b) * (1 - prem)) * 255).astype(np.uint8)).convert('RGBA')
    d = ImageDraw.Draw(im, 'RGBA'); d.rectangle([0, 0, 7, H], fill=GOLD)
    mm = max(m2, m3); captions(im, t, lerp(1335, 1405, mm), int(lerp(128, 104, mm)))
    return im.convert('RGB')

if __name__ == '__main__':
    mode = sys.argv[2]
    if mode == 'stills':
        for tt in [float(x) for x in sys.argv[3:]]:
            subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', f'{tt:.4f}', '-i', HERE + '/assembled.mov', '-frames:v', '1', HERE + '/qc/_src.png'])
            frame(Image.open(HERE + '/qc/_src.png').convert('RGB'), tt).resize((540, 960)).save(HERE + f'/qc/st_{tt:06.2f}.jpg', quality=85)
        sys.exit()
    n0, n1, out = int(sys.argv[3]), int(sys.argv[4]), sys.argv[5]
    dec = subprocess.Popen(['ffmpeg', '-v', 'error', '-i', HERE + '/assembled.mov', '-vf', f'select=between(n\\,{n0}\\,{n1 - 1})', '-vsync', '0', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], stdout=subprocess.PIPE)
    enc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-crf', '12', '-preset', 'fast', '-pix_fmt', 'yuv420p', out], stdin=subprocess.PIPE)
    for n in range(n0, n1):
        buf = dec.stdout.read(W * H * 3)
        if len(buf) < W * H * 3: print('short', n); break
        enc.stdin.write(frame(Image.frombuffer('RGB', (W, H), buf), n / FPS).tobytes())
    enc.stdin.close(); enc.wait(); dec.kill(); print('done', n0, n1)
