# @coach.agz Reel: "How I know you're gay" (anabolic coach bit). 1080x1920, 30 fps.
# Usage: python3 render.py <workdir> stills t1 t2 ...  |  python3 render.py <workdir> frames n0 n1 out.mp4
import json, subprocess, sys, math
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps
S = sys.argv[1].rstrip('/') + '/'
F = S + 'fonts/'
W, H, FPS = 1080, 1920, 30
WORDS = json.load(open(S + 'words_cut.json'))
# onset fixes (whisper stretched words across deliberate comedic pauses; checked against silencedetect)
for w in WORDS:
    if w['w'].lower().startswith('all') and abs(w['s'] - 21.08) < 0.05: w['s'] = 21.85
    if w['w'].lower().startswith('pictures') and abs(w['s'] - 18.66) < 0.05: w['e'] = 19.0
    if w['w'].lower().startswith('at') and abs(w['s'] - 20.72) < 0.05: w['e'] = 21.0
    if w['w'].lower().startswith('or') and abs(w['s'] - 9.94) < 0.05: w['s'] = 9.84
DUR = 24.4333; N = int(round(DUR * FPS))
CUT1 = 9.8  # jump cut (output time)
CUT2 = 9.8 + (23.233333 - 10.133333)

# ---------------- palette (BRAND.md overlay accents) ----------------
GOLD = (201, 169, 110); CREAM = (244, 241, 234); NAVY = (14, 17, 23); BG = (14, 17, 23)
RED = (255, 34, 28); VGOLD = (255, 194, 26); CYAN = (0, 229, 255); GREEN = (30, 255, 110)
DEEP = (2, 3, 8); INK = (6, 8, 14); WHITE = (255, 255, 255); MUTED = (124, 124, 130)
SBLUE = (79, 163, 224); SGREEN = (60, 203, 106); SAMBER = (240, 160, 48)
MONO = 'JBMono-500.ttf'; MONOB = 'JBMono-700.ttf'; BEB = 'BebasNeue.ttf'; BAR = 'Barlow-700.ttf'; DMB = 'DMSans-700.ttf'
_fc = {}
def f(n, s):
    k = (n, int(s))
    if k not in _fc: _fc[k] = ImageFont.truetype(F + n, int(s))
    return _fc[k]
def clamp(x, a=0, b=1): return max(a, min(b, x))
def expo(x): x = clamp(x); return 1 if x >= 1 else 1 - 2 ** (-10 * x)
def ease_io(x): x = clamp(x); return 4 * x ** 3 if x < .5 else 1 - (-2 * x + 2) ** 3 / 2
def back_heavy(x):  # heavy landing: fast, tiny settle (no cartoon bounce)
    x = clamp(x); return 1 - (1 - x) ** 4 * (1 + 0.0 * x)
def lerp(a, b, t): return a + (b - a) * t
def A(c, a): return tuple(c[:3]) + (int(clamp(a) * 255),)
def appear(t, t0, dur=0.16): return expo((t - t0) / dur)
def window(t, t0, t1, i=0.18, o=0.14): return min(expo((t - t0) / i), 1 - clamp((t - t1) / o))
GL = None
def comp(im, layer, xy=(0, 0)):
    im.paste(layer, (int(xy[0]), int(xy[1])), layer)

# ---------------- primitives (from the saved full-test pipeline) ----------------
def brackets(d, x0, y0, x1, y1, col, L=34, w=4):
    for (cx, cy, sx, sy) in [(x0, y0, 1, 1), (x1, y0, -1, 1), (x0, y1, 1, -1), (x1, y1, -1, -1)]:
        d.line([(cx, cy), (cx + sx * L, cy)], fill=col, width=w); d.line([(cx, cy), (cx, cy + sy * L)], fill=col, width=w)
def lit_bar(d, x0, y0, x1, y1, col, a=1.0):
    h = max(1, int(y1 - y0))
    for i in range(h):
        k = i / h; c = tuple(int(min(255, v * (1.18 - 0.36 * k) + (40 if k < 0.12 else 0))) for v in col)
        d.line([(x0, y0 + i), (x1, y0 + i)], fill=c + (int(255 * a),))
def tag(d, x, y, label, col=RED, size=32, a=1.0, glow=True):
    fn = f(MONOB, size); tw = d.textlength(label, font=fn); h = size + 16
    lit_bar(d, x, y, x + tw + 24, y + h, col, a); txt(d, x + 12, y + 5, label, fn, WHITE if col not in (VGOLD, GREEN, CYAN) else INK, a)
    if GL is not None and glow: GL.rectangle([x - 4, y - 4, x + tw + 28, y + h + 4], outline=A(col, a), width=8)
    return x + tw + 24
def txt(d, x, y, s, font, col, a=1.0, anchor=None):
    # Pillow 12 ignores fill alpha on text, so fade text through an L mask
    a = clamp(a)
    if a <= 0.004 or not s: return
    if a >= 0.996: d.text((x, y), s, font=font, fill=tuple(col[:3]) + (255,), anchor=anchor); return
    im = d._image
    b0, b1, b2, b3 = [int(v) for v in d.textbbox((x, y), s, font=font, anchor=anchor)]
    b0 -= 2; b1 -= 2; b2 += 2; b3 += 2
    if b2 <= b0 or b3 <= b1: return
    m = Image.new('L', (b2 - b0, b3 - b1), 0)
    ImageDraw.Draw(m).text((x - b0, y - b1), s, font=font, fill=int(255 * a), anchor=anchor)
    im.paste(Image.new(im.mode, m.size, tuple(col[:3]) + ((255,) if im.mode == 'RGBA' else ())), (b0, b1), m)
def check(d, x, y, col, s=1.0, a=1.0):
    pts = [(x, y + 16 * s), (x + 10 * s, y + 28 * s), (x + 30 * s, y + 2 * s)]
    d.line(pts, fill=A(col, a), width=int(6 * s))
    if GL is not None: GL.line(pts, fill=A(col, a), width=int(12 * s))
def frosted(im, box, dark=0.86, blur=10):
    x0, y0, x1, y1 = [int(v) for v in box]
    x0 = max(0, x0); y0 = max(0, y0); x1 = min(W, x1); y1 = min(H, y1)
    if x1 <= x0 or y1 <= y0: return
    reg = im.crop((x0, y0, x1, y1)).convert('RGB').filter(ImageFilter.GaussianBlur(blur))
    im.paste(Image.blend(reg, Image.new('RGB', reg.size, DEEP), dark), (x0, y0))
def card(im, box, a, accent=VGOLD, kicker=None, right=None, dark=0.9):
    """Frosted evidence card with brackets + mono header. Returns a draw handle."""
    if a <= 0: return ImageDraw.Draw(im, 'RGBA')
    x0, y0, x1, y1 = box
    frosted(im, box, dark * a, 10)
    d = ImageDraw.Draw(im, 'RGBA')
    d.rectangle([x0, y0, x1, y1], outline=A(accent, 0.55 * a), width=2)
    brackets(d, x0, y0, x1, y1, A(accent, a), 30, 6)
    if GL is not None: brackets(GL, x0, y0, x1, y1, A(accent, a), 30, 12)
    if kicker:
        d.line([(x0 + 24, y0 + 34), (x0 + 60, y0 + 34)], fill=A(accent, a), width=4)
        txt(d, x0 + 72, y0 + 18, kicker, f(MONO, 26), accent, a)
    if right:
        fr = f(MONO, 26); tw = d.textlength(right, font=fr); txt(d, x1 - 24 - tw, y0 + 18, right, fr, MUTED, a)
    return d
def paste_img(im, img, box, a=1.0, radius=10):
    x0, y0, x1, y1 = [int(v) for v in box]
    w, h = x1 - x0, y1 - y0
    if w < 2 or h < 2 or a <= 0: return
    r = ImageOps.fit(img, (w, h), Image.LANCZOS).convert('RGBA')
    m = Image.new('L', (w, h), 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, w - 1, h - 1], radius=radius, fill=int(255 * a))
    r.putalpha(m); comp(im, r, (x0, y0))

# ---------------- assets ----------------
IMG = {}
def assets():
    if IMG: return
    a = Image.open(S + 'imgs/client_A_beach.png').convert('RGB'); b = Image.open(S + 'imgs/client_B_tattoo.png').convert('RGB')
    c = Image.open(S + 'imgs/client_C_dm.png').convert('RGB')
    IMG['A0'] = a.crop((0, 0, 478, a.height)); IMG['A1'] = a.crop((484, 0, a.width, a.height))
    IMG['B0'] = b.crop((0, 0, 527, b.height)); IMG['B1'] = b.crop((533, 0, b.width, b.height))
    IMG['C'] = c; IMG['Ctop'] = c.crop((0, 0, 500, 640))
    lg = Image.open(S + 'logo.jpg').convert('RGB'); s = min(lg.size)
    lg = lg.crop(((lg.width - s) // 2, (lg.height - s) // 2, (lg.width + s) // 2, (lg.height + s) // 2)).resize((150, 150), Image.LANCZOS)
    m = Image.new('L', (150, 150), 0); ImageDraw.Draw(m).ellipse([0, 0, 149, 149], fill=255); lg.putalpha(m); IMG['logo'] = lg

# ---------------- layout: FULL vs SPLIT (face always sharp, never darkened) ----------------
SPLITS = [(10.70, 13.30), (15.92, 22.52)]
SPLIT_S, SPLIT_OUT = 0.64, (540, 1180)
WIN_TOP = 930
def split_k(t):
    k = 0
    for a, b in SPLITS:
        if a - 0.01 <= t < b + 0.36: k = max(k, min(ease_io((t - a) / 0.34), 1 - ease_io((t - b) / 0.34)))
    return k
def zoom(t):
    if t < 1.14: return 1.0
    if t < 1.70: return lerp(1.0, 1.12, expo((t - 1.14) / 0.10))  # punch on "gay?"
    if t < CUT1: return 1.0
    if t < CUT2: return 1.06  # alternate per jump cut
    # reaction beat: slow push through the pause, hard punch on "Damn"
    if t < 23.48: return lerp(1.0, 1.07, ease_io((t - CUT2) / (23.48 - CUT2)))
    return lerp(1.07, 1.17, expo((t - 23.48) / 0.09))
def place_footage(src, t):
    k = split_k(t); z = zoom(t)
    s = lerp(z, SPLIT_S, k)
    sa = (lerp(540, 560, k), 1000)                   # source anchor (face)
    oa = (lerp(540, SPLIT_OUT[0], k), lerp(1000, SPLIT_OUT[1], k))
    if k <= 0.001:
        if abs(s - 1) < 1e-3: return src.convert('RGBA'), k
        big = src.resize((int(W * s), int(H * s)), Image.BICUBIC)
        ox = int(sa[0] * s - oa[0]); oy = int(sa[1] * s - oa[1])
        ox = max(0, min(big.width - W, ox)); oy = max(0, min(big.height - H, oy))
        return big.crop((ox, oy, ox + W, oy + H)).convert('RGBA'), k
    out = bg_plate(t)
    sm = src.resize((int(W * s), int(H * s)), Image.BICUBIC)
    px = int(oa[0] - sa[0] * s); py = int(oa[1] - sa[1] * s)
    top = int(lerp(0, WIN_TOP, k))
    cy0 = max(0, top - py)
    sm = sm.crop((0, cy0, sm.width, sm.height))
    out.paste(sm, (px, py + cy0))
    d = ImageDraw.Draw(out, 'RGBA')
    x0, y0, x1 = px, py + cy0, px + sm.width
    if k > 0.5:
        a = (k - 0.5) * 2
        d.line([(x0, y0), (x1, y0)], fill=A(VGOLD, a), width=4)
        if GL is not None: GL.line([(x0, y0), (x1, y0)], fill=A(VGOLD, a), width=10)
    return out, k
_BG = None
def bg_plate(t):
    global _BG
    if _BG is None:
        yy, xx = np.mgrid[0:H, 0:W]
        g = np.exp(-(((xx - 900) / 700) ** 2 + ((yy - 300) / 600) ** 2))
        base = np.array(BG, np.float32)[None, None, :] + g[..., None] * np.array([15, 12, 7], np.float32)
        # faint scan grid texture
        base += (((yy % 48) == 0) | ((xx % 48) == 0))[..., None] * 5
        _BG = Image.fromarray(np.clip(base, 0, 255).astype(np.uint8)).convert('RGBA')
    return _BG.convert('RGB')

# ---------------- scenes ----------------
TOP = (60, 262, 1020, 628)  # top-zone card box for FULL layout (above the cap; face stays clear)

def s_credential(im, t):  # 2.20-3.30 "anabolic coach": ID plate
    if not (2.18 <= t < 3.46): return
    p = expo((t - 2.20) / 0.20); po = clamp((t - 3.18) / 0.12)
    a = p * (1 - po)
    x0, y0, x1, y1 = 60, 300, 1020, 520
    dx = lerp(-80, 0, p)
    d = card(im, (x0 + dx, y0, x1 + dx, y1), a, VGOLD, 'CREDENTIAL', 'ID · 001')
    lg = IMG['logo'].resize((120, 120)); al = lg.split()[3].point(lambda v: int(v * a)); lg.putalpha(al)
    comp(im, lg, (int(x0 + dx + 28), y0 + 72)); d = ImageDraw.Draw(im, 'RGBA')
    q = appear(t, 2.24, 0.14)
    fn = f(BEB, 96); x = x0 + dx + 172
    txt(d, x, y0 + 64, 'ANABOLIC', fn, VGOLD if t >= 2.24 else CREAM, a * q)
    tw = d.textlength('ANABOLIC ', font=fn)
    txt(d, x + tw, y0 + 64, 'COACH', fn, CREAM, a * appear(t, 2.70, 0.12))
    if t >= 2.72:
        b = a * appear(t, 2.72); txt(d, x, y0 + 162, '@coach.agz', f(MONO, 26), GOLD, b)
        tag(d, x + 250, y0 + 156, 'VERIFIED', GREEN, 24, b)

def clock_ring(d, cx, cy, r, frac, a, label=True):
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=A((60, 64, 80), a), width=10)
    if frac > 0:
        d.arc([cx - r, cy - r, cx + r, cy + r], -90, -90 + 360 * frac, fill=A(RED if frac > 0.85 else VGOLD, a), width=10)
        if GL is not None: GL.arc([cx - r, cy - r, cx + r, cy + r], -90, -90 + 360 * frac, fill=A(RED if frac > 0.85 else VGOLD, a), width=16)
    hrs = 9 + 15 * frac; hh = int(hrs); mm = int((hrs - hh) * 60)
    if label:
        txt(d, cx, cy - 8, f'{hh:02d}:{mm:02d}', f(BEB, int(r * 0.62)), WHITE, a, 'mm')
        txt(d, cx, cy + r * 0.42, 'SCREEN TIME', f(MONO, int(r * 0.17)), MUTED, a, 'mm')

def s_inbox(im, t):  # 3.30-5.62 "stare at half naked dudes all day": check-in inbox + clock ring
    if not (3.28 <= t < 5.80): return
    a = window(t, 3.30, 5.62, 0.16, 0.14)
    x0, y0, x1, y1 = 60, 268, 1020, 640
    d = card(im, (x0, y0, x1, y1), a, CYAN, 'CHECK-IN INBOX', None)
    # unread counter (counts the tiles visibly delivered, not a stat)
    thumbs = [IMG['A1'], IMG['B1'], IMG['Ctop'], IMG['B0'], IMG['A0'], IMG['B1'], IMG['A1']]
    times = [3.36, 3.58, 3.88, 4.02, 4.28, 4.56, 4.80]
    n = sum(1 for tt in times if t >= tt)
    tag(d, x1 - 220, y0 + 12, f'{n} UNREAD', RED, 24, a)
    scroll = lerp(0, 1, clamp((t - 3.3) / 2.3)) * 330
    tw_, th_ = 196, 262
    cl = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    for i, (img, tt) in enumerate(zip(thumbs, times)):
        if t < tt: continue
        q = expo((t - tt) / 0.16)
        tx = x0 + 28 + i * (tw_ + 14) - scroll; ty = y0 + 74 + lerp(30, 0, q)
        if tx > 760 or tx + tw_ < x0 + 10: continue
        paste_img(cl, img, (tx, ty, tx + tw_, ty + th_), a * q, 12)
        dd = ImageDraw.Draw(cl, 'RGBA')
        dd.ellipse([tx + tw_ - 30, ty + 10, tx + tw_ - 12, ty + 28], fill=A(RED, a * q))
    # clip thumbs to the left part of the card
    mask = Image.new('L', (W, H), 0); ImageDraw.Draw(mask).rectangle([x0 + 12, y0 + 60, 768, y1 - 10], fill=255)
    cl.putalpha(Image.fromarray(np.minimum(np.asarray(cl.split()[3]), np.asarray(mask))))
    comp(im, cl)
    d = ImageDraw.Draw(im, 'RGBA')
    # cyan scan line on "stare"
    if 3.58 <= t < 4.4:
        sx = lerp(x0 + 20, 770, clamp((t - 3.58) / 0.7))
        d.line([(sx, y0 + 66), (sx, y1 - 14)], fill=A(CYAN, a), width=4)
        if GL is not None: GL.line([(sx, y0 + 66), (sx, y1 - 14)], fill=A(CYAN, a), width=14)
    d.line([(784, y0 + 70), (784, y1 - 20)], fill=A((60, 64, 80), a), width=2)
    # 'all day': 24h ring winds 09:00 -> 23:59
    fr = 0.12 if t < 4.92 else lerp(0.12, 1.0, ease_io((t - 4.92) / 0.6))
    clock_ring(d, 902, y0 + 210, 98, fr * appear(t, 3.4, 0.3), a)

def dial(d, cx, cy, r, val, a, label, ok):
    # spectrum arc 200deg: blue(low) -> green -> amber/red(high)
    st, en = 170, 370
    segs = 40
    for i in range(segs):
        u = i / segs
        if u < 0.5: c = tuple(int(lerp(SBLUE[j], SGREEN[j], u * 2)) for j in range(3))
        else: c = tuple(int(lerp(SGREEN[j], RED[j], (u - 0.5) * 2)) for j in range(3))
        d.arc([cx - r, cy - r, cx + r, cy + r], st + (en - st) * u, st + (en - st) * (u + 1 / segs) + 0.6, fill=A(c, a * 0.9), width=12)
    ang = math.radians(st + (en - st) * val)
    nx, ny = cx + (r - 22) * math.cos(ang), cy + (r - 22) * math.sin(ang)
    col = GREEN if ok else RED
    d.line([(cx, cy), (nx, ny)], fill=A(WHITE, a), width=6); d.ellipse([cx - 11, cy - 11, cx + 11, cy + 11], fill=A(col, a))
    if GL is not None: GL.line([(cx, cy), (nx, ny)], fill=A(col, a), width=10)
    txt(d, cx, cy + 44, label, f(BEB, 46), WHITE, a, 'mm')

def s_bloodwork(im, t):  # 5.68-7.98 "dial in their bloodwork and keep them healthy": radial dials
    if not (5.66 <= t < 8.14): return
    a = window(t, 5.68, 7.98, 0.16, 0.14)
    x0, y0, x1, y1 = 60, 268, 1020, 640
    d = card(im, (x0, y0, x1, y1), a, VGOLD, 'BLOODWORK PANEL', 'ILLUSTRATIVE')
    specs = [('HEMATOCRIT', 0.92, 6.06), ('ESTRADIOL', 0.86, 6.48), ('LIPIDS', 0.95, 6.76)]
    for i, (nm, v0, tt) in enumerate(specs):
        cx = 220 + i * 320; cy = y0 + 200
        q = expo((t - tt) / 0.55) if t >= tt else 0
        v = lerp(v0, 0.5, q)
        dial(d, cx, cy, 118, v, a, nm, q > 0.9)
        if t >= 7.50:
            b = a * appear(t, 7.50 + i * 0.07, 0.12)
            check(d, cx - 70, cy + 92, GREEN, 0.8, b); txt(d, cx - 30, cy + 88, 'IN RANGE', f(MONOB, 26), GREEN, b)

def vial(d, x, y, w, h, col, label, a, fill):
    d.rounded_rectangle([x + w * 0.28, y, x + w * 0.72, y + h * 0.13], radius=4, fill=A((150, 150, 160), a))
    d.rounded_rectangle([x, y + h * 0.13, x + w, y + h], radius=16, outline=A(col, a), width=5)
    if GL is not None: GL.rounded_rectangle([x, y + h * 0.13, x + w, y + h], radius=16, outline=A(col, a), width=10)
    fy = y + h - (h * 0.75) * fill
    d.rounded_rectangle([x + 10, fy, x + w - 10, y + h - 10], radius=10, fill=A(col, a * 0.55))
    d.rectangle([x + 8, y + h * 0.36, x + w - 8, y + h * 0.58], fill=A((240, 238, 230), a))
    fn = f(BEB, 50); tw = d.textlength(label, font=fn); txt(d, x + w / 2 - tw / 2, y + h * 0.37, label, fn, INK, a)

def s_stack(im, t):  # 8.06-10.60 "test, NPP, or Tren": vial stack + stacked bar
    if not (8.04 <= t < 10.76): return
    a = window(t, 8.06, 10.60, 0.16, 0.14)
    x0, y0, x1, y1 = 60, 268, 1020, 640
    d = card(im, (x0, y0, x1, y1), a, CYAN, 'THE STACK', 'RESEARCH & EDUCATION ONLY')
    items = [('TEST', VGOLD, 8.76), ('NPP', CYAN, 9.22), ('TREN', RED, 9.98)]
    for i, (nm, col, tt) in enumerate(items):
        if t < tt - 0.12: continue
        q = clamp((t - (tt - 0.12)) / 0.14); y = lerp(y0 - 120, y0 + 72, q ** 2)  # gravity drop, lands on the word
        land = max(0, 1 - (t - tt) / 0.12) if t >= tt else 0
        vial(d, 110 + i * 170, y + land * 6, 130, 232, col, nm, a * min(1, q * 3), 0.9)
    # stacked bar: one segment per compound
    bx0, bx1, by = 640, 980, y0 + 110
    txt(d, bx0, by - 46, 'ON BOARD', f(MONO, 26), MUTED, a)
    d.rectangle([bx0, by, bx1, by + 56], outline=A((70, 74, 90), a), width=2)
    x = bx0 + 3
    for nm, col, tt in items:
        if t < tt: continue
        wseg = (bx1 - bx0 - 6) / 3 * expo((t - tt) / 0.22)
        lit_bar(d, x, by + 3, x + wseg, by + 53, col, a); x += wseg
    if t >= 9.98:
        b = a * appear(t, 10.05, 0.12)
        tag(d, bx0, by + 84, 'BLOODWORK EVERY STEP', VGOLD, 22, b)
        check(d, bx0, by + 150, GREEN, 0.8, b); txt(d, bx0 + 40, by + 146, 'STILL HEALTHY', f(MONOB, 26), GREEN, b)

def hud(d, box, t, t0, col, a):
    x0, y0, x1, y1 = box; p = expo((t - t0) / 0.35)
    m = lerp(90, 0, p)
    brackets(d, x0 - m, y0 - m, x1 + m, y1 + m, A(col, a), 46, 6)
    if GL is not None: brackets(GL, x0 - m, y0 - m, x1 + m, y1 + m, A(col, a), 46, 12)
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    if p > 0.6:
        d.line([(cx - 24, cy), (cx + 24, cy)], fill=A(col, a * 0.8), width=3); d.line([(cx, cy - 24), (cx, cy + 24)], fill=A(col, a * 0.8), width=3)

def s_lethal(im, t):  # 10.78-13.30 "make them into these lethal units" (SPLIT): before -> HUD lock on after
    if not (10.70 <= t < 13.50): return
    a = window(t, 11.02, 13.10, 0.18, 0.14)
    d = card(im, (40, 250, 1040, 912), a, RED, 'TRANSFORMATION', 'CLIENT RESULT')
    # small desaturated BEFORE, arrow, big AFTER
    bq = appear(t, 11.04, 0.16)
    b0 = ImageOps.grayscale(IMG['B0']).convert('RGB')
    paste_img(im, b0, (72, 330, 72 + 300, 330 + 470), a * bq, 10)
    d = ImageDraw.Draw(im, 'RGBA')
    if bq > 0: tag(d, 84, 810, 'BEFORE', (90, 94, 110), 24, a * bq, glow=False)
    if t >= 11.18:
        q = appear(t, 11.18, 0.18)
        ax = lerp(390, 430, q)
        d.polygon([(ax, 545), (ax + 36, 565), (ax, 585)], fill=A(RED, a * q))
    if t >= 11.42:
        q = expo((t - 11.42) / 0.22); s = lerp(1.06, 1.0, q)
        bx0, by0, bx1, by1 = 480, 300, 1008, 900
        cx, cy = (bx0 + bx1) / 2, (by0 + by1) / 2; w_, h_ = (bx1 - bx0) * s, (by1 - by0) * s
        paste_img(im, IMG['B1'], (cx - w_ / 2, cy - h_ / 2, cx + w_ / 2, cy + h_ / 2), a * q, 10)
        d = ImageDraw.Draw(im, 'RGBA')
        if t >= 11.62: hud(d, (560, 420, 940, 820), t, 11.62, RED, a)
        if 11.62 <= t < 12.5:
            sy = lerp(330, 880, clamp((t - 11.62) / 0.8)); d.line([(500, sy), (990, sy)], fill=A(RED, a * 0.8), width=3)
        if t >= 11.70: tag(d, 520, 320, 'TARGET LOCK', RED, 24, a * appear(t, 11.70, 0.1))
        if t >= 12.04:
            # threat meter fills to MAX on "lethal"
            fr = expo((t - 12.04) / 0.45)
            txt(d, 520, 700 - 0, '', f(MONO, 24), WHITE, a)
            d.rectangle([520, 846, 990, 878], outline=A(WHITE, a * 0.6), width=2)
            lit_bar(d, 523, 849, lerp(523, 987, fr), 875, RED, a)
            if GL is not None: GL.rectangle([523, 849, lerp(523, 987, fr), 875], fill=A(RED, a * 0.6))
            txt(d, 520, 806, 'THREAT LEVEL', f(MONOB, 26), WHITE, a)
            if fr > 0.9: tag(d, 870, 798, 'MAX', RED, 24, a)
    # verdict slam on "units"
    if t >= 12.54:
        p = expo((t - 12.54) / 0.10); y = 560; x0 = 40; x1 = lerp(40, 1040, p)
        if GL is not None: GL.rectangle([x0, y - 6, x1, y + 108], outline=A(RED, a), width=10)
        lit_bar(d, x0, y, x1, y + 102, RED, a); d.rectangle([x0, y + 98, x1, y + 102], fill=A((140, 0, 0), a))
        if p > 0.6:
            fn = f(BEB, 92); txt(d, 70, y + 6, 'LETHAL UNIT', fn, WHITE, a)
            tw = d.textlength('LETHAL UNIT', font=fn); txt(d, 70 + tw + 30, y + 38, 'CLASS CONFIRMED', f(MONOB, 28), WHITE, a)

def s_camera(im, t):  # 13.38-15.90 "make them take half naked pictures": viewfinder UI + polaroid
    if not (13.36 <= t < 16.10): return
    a = window(t, 13.40, 15.92, 0.14, 0.16)
    d = ImageDraw.Draw(im, 'RGBA')
    m = lerp(120, 50, expo((t - 13.40) / 0.25))
    x0, y0, x1, y1 = m, 250 + m * 0.4, W - m, 1880 - m
    brackets(d, x0, y0, x1, y1, A(WHITE, a * 0.95), 70, 5)
    on = int(t * 3) % 2 == 0
    d.ellipse([x0 + 20, y0 + 22, x0 + 42, y0 + 44], fill=A(RED, a if on else a * 0.3))
    txt(d, x0 + 54, y0 + 16, 'REC', f(MONOB, 28), WHITE, a)
    txt(d, x1 - 180, y0 + 16, '1080 · 30', f(MONO, 26), WHITE, a)
    # focus box locks on the subject (thin outline around the cap/face, no fill)
    fp = expo((t - 13.90) / 0.2)
    if t >= 13.90:
        fx0, fy0, fx1, fy1 = lerp(200, 300, fp), lerp(560, 640, fp), lerp(900, 820, fp), lerp(1500, 1420, fp)
        brackets(d, fx0, fy0, fx1, fy1, A(VGOLD, a), 30, 4)
        if t >= 14.1: txt(d, fx0, fy0 - 40, 'AF LOCK', f(MONOB, 24), VGOLD, a)
    # shutter: iris bars snap closed/open across 4 frames on "pictures" (no white flash)
    ts = 15.22
    if ts <= t < ts + 0.14:
        k = 1 - abs((t - ts) / 0.07 - 1)
        hh = int(H / 2 * k)
        d.rectangle([0, 0, W, hh], fill=(0, 0, 0, 255)); d.rectangle([0, H - hh, W, H], fill=(0, 0, 0, 255))
    # captured print drops into the top-right corner (polaroid), angled
    if t >= 15.30:
        q = expo((t - 15.30) / 0.22)
        pw, ph = 330, 400
        pol = Image.new('RGBA', (pw, ph), (244, 241, 234, 255))
        pol.paste(ImageOps.fit(IMG['Ctop'], (pw - 30, ph - 90)), (15, 15))
        pd = ImageDraw.Draw(pol); pd.text((18, ph - 64), 'CHECK-IN', font=f(BEB, 46), fill=INK); pd.text((206, ph - 52), 'WK 12', font=f(MONOB, 26), fill=(200, 20, 20))
        pol = pol.rotate(lerp(-14, -6, q), expand=True, resample=Image.BICUBIC)
        al = pol.split()[3].point(lambda v: int(v * a * min(1, q * 2))); pol.putalpha(al)
        x = int(lerp(1100, 690, q)); y = int(lerp(150, 240, q))
        sh = Image.new('RGBA', pol.size, (0, 0, 0, 0)); sh.putalpha(al.point(lambda v: int(v * 0.5)))
        comp(im, sh.filter(ImageFilter.GaussianBlur(10)), (x + 10, y + 16)); comp(im, pol, (x, y))

def wipe_compare(im, t, left, right, t_wipe, a, box, lab_l, lab_r, t_ll, t_lr):
    x0, y0, x1, y1 = box
    w_, h_ = x1 - x0, y1 - y0
    L = ImageOps.fit(left, (w_ // 2, h_), Image.LANCZOS); R = ImageOps.fit(right, (w_ // 2, h_), Image.LANCZOS)
    full = Image.new('RGB', (w_, h_)); full.paste(L, (0, 0)); full.paste(R, (w_ // 2, 0))
    # before wipes in from the left, after starts full width -> divider settles at centre
    p = ease_io((t - t_wipe) / 0.5) if t >= t_wipe else 0
    div = int(lerp(0, w_ // 2, p))
    base = ImageOps.fit(right, (w_, h_), Image.LANCZOS) if p < 1 else full
    comp = base.copy()
    if div > 0: comp.paste(full.crop((0, 0, div, h_)) if p >= 1 else L.crop((w_ // 2 - div, 0, w_ // 2, h_)), (0, 0))
    paste_img(im, comp, box, a, 10)
    d = ImageDraw.Draw(im, 'RGBA')
    if div > 0:
        dx = x0 + div
        d.line([(dx, y0), (dx, y1)], fill=A(VGOLD, a), width=6)
        if GL is not None: GL.line([(dx, y0), (dx, y1)], fill=A(VGOLD, a), width=14)
        d.ellipse([dx - 26, (y0 + y1) / 2 - 26, dx + 26, (y0 + y1) / 2 + 26], fill=A(VGOLD, a))
        d.polygon([(dx - 6, (y0 + y1) / 2 - 10), (dx - 16, (y0 + y1) / 2), (dx - 6, (y0 + y1) / 2 + 10)], fill=A(INK, a))
        d.polygon([(dx + 6, (y0 + y1) / 2 - 10), (dx + 16, (y0 + y1) / 2), (dx + 6, (y0 + y1) / 2 + 10)], fill=A(INK, a))
    if t >= t_ll: tag(d, x0 + 16, y1 - 62, lab_l, RED, 28, a * appear(t, t_ll, 0.12))
    if t >= t_lr: tag(d, x1 - 130, y1 - 62, lab_r, VGOLD, 28, a * appear(t, t_lr, 0.12))

def s_compare(im, t):  # 15.98-22.52 SPLIT: A wipe compare -> B side by side -> DM receipt + body-fat range
    if not (15.90 <= t < 22.90): return
    a = window(t, 16.24, 22.36, 0.16, 0.14)
    kick = 'BEFORE / AFTER' if t < 19.9 else 'CLIENT CHECK-IN'
    rt = 'CLIENT 01' if t < 18.66 else ('CLIENT 02' if t < 19.9 else 'CLIENT 03')
    card(im, (40, 250, 1040, 912), a, VGOLD, kick, rt)
    box = (64, 316, 1016, 890)
    if t < 18.66:
        wipe_compare(im, t, IMG['A0'], IMG['A1'], 16.30, a, box, 'OLD', 'NOW', 17.14, 16.40)
    elif t < 19.9:
        # client 02 pushes in from the right; the gold divider carries over (handoff)
        q = expo((t - 18.66) / 0.26)
        off = int(lerp(980, 0, q))
        x0, y0, x1, y1 = box; w_ = (x1 - x0) // 2
        b0 = ImageOps.grayscale(IMG['B0']).convert('RGB') if t >= 19.30 else IMG['B0']
        oa = off - (x1 - x0) - 24
        paste_img(im, IMG['A0'], (x0 + oa, y0, x0 + w_ + oa, y1), a, 10); paste_img(im, IMG['A1'], (x0 + w_ + oa, y0, x1 + oa, y1), a, 10)
        paste_img(im, b0, (x0 + off, y0, x0 + w_ + off, y1), a, 10)
        paste_img(im, IMG['B1'], (x0 + w_ + off, y0, x1 + off, y1), a, 10)
        d = ImageDraw.Draw(im, 'RGBA')
        dx = x0 + w_ + off; d.line([(dx, y0), (dx, y1)], fill=A(VGOLD, a), width=6)
        if GL is not None: GL.line([(dx, y0), (dx, y1)], fill=A(VGOLD, a), width=14)
        if t >= 18.80: tag(d, x0 + 16 + off, y1 - 62, 'OLD', RED, 28, a)
        if t >= 18.80: tag(d, x1 - 130 + off, y1 - 62, 'NOW', VGOLD, 28, a)
    else:
        s_dm(im, t, a)

def s_dm(im, t, a):  # 19.98-22.52 DM receipt + vertical body-fat range bar + clock ring callback
    q = expo((t - 19.90) / 0.24)
    c = IMG['C'].crop((0, 0, 683, 830))  # after-photo + message bubble
    hh = 560; ww = int(683 * hh / 830)
    x0 = int(lerp(-ww * 0.25, 70, q)); y0 = 320
    a = a * min(1, q * 2.5)
    paste_img(im, c, (x0, y0, x0 + ww, y0 + hh), a, 12)
    d = ImageDraw.Draw(im, 'RGBA')
    sc = hh / 830
    # bracket the client's own number on "stare"
    if t >= 20.46:
        bx0, by0, bx1, by1 = x0 + 150 * sc, y0 + 708 * sc, x0 + 318 * sc, y0 + 758 * sc
        p = expo((t - 20.46) / 0.14)
        brackets(d, bx0 - 8, by0 - 8, bx1 + 8, by1 + 8, A(VGOLD, a * p), 16, 5)
        if GL is not None: brackets(GL, bx0 - 8, by0 - 8, bx1 + 8, by1 + 8, A(VGOLD, a * p), 16, 10)
    # body-fat range: vertical scale 30% (top) -> 8% (bottom); marker lands in the client's 13-15% band
    if t >= 20.30:
        b = a * appear(t, 20.30, 0.2)
        gx0, gx1, gy0, gy1 = 640, 700, 340, 860
        txt(d, 560, 300 - 0, '', f(MONO, 22), MUTED, b)
        for i in range(int(gy1 - gy0)):
            u = i / (gy1 - gy0)
            col = tuple(int(lerp(SAMBER[j], SGREEN[j], u)) for j in range(3))
            d.line([(gx0, gy0 + i), (gx1, gy0 + i)], fill=A(col, b * 0.9))
        def ypos(pct): return lerp(gy0, gy1, (30 - pct) / 22)
        for pct in (30, 25, 20, 15, 10):
            y = ypos(pct); d.line([(gx1, y), (gx1 + 14, y)], fill=A(WHITE, b), width=2); txt(d, gx1 + 20, y - 14, f'{pct}%', f(MONO, 24), MUTED, b)
        band0, band1 = ypos(15), ypos(13)
        mk = expo((t - 20.62) / 0.6) if t >= 20.62 else 0
        my = lerp(gy0, (band0 + band1) / 2, mk)
        if mk > 0.85:
            d.rectangle([gx0 - 10, band0, gx1 + 10, band1], outline=A(WHITE, b), width=3)
        d.polygon([(gx0 - 34, my - 16), (gx0 - 6, my), (gx0 - 34, my + 16)], fill=A(WHITE, b))
        if GL is not None: GL.polygon([(gx0 - 34, my - 16), (gx0 - 6, my), (gx0 - 34, my + 16)], fill=A(WHITE, b))
        txt(d, 600, 312 - 0, 'BODY FAT', f(MONOB, 24), WHITE, b)
        if mk > 0.9:
            c2 = a * appear(t, 20.62 + 0.55, 0.14)
            txt(d, 800, 560, '13–15%', f(BEB, 112), GREEN, c2)
            txt(d, 804, 676, "CLIENT'S", f(MONO, 24), MUTED, c2); txt(d, 804, 704, 'ESTIMATE', f(MONO, 24), MUTED, c2)
    # callback to the opening: the 24h screen-time ring winds again on "all day"
    if t >= 21.85:
        fr = lerp(0.15, 1.0, ease_io((t - 21.85) / 0.55))
        clock_ring(d, 900, 420, 82, fr, a * appear(t, 21.85, 0.12))

def s_end(im, t):  # "Damn" -> end plate
    if t < 23.94: return
    a = appear(t, 23.96, 0.14)
    d = card(im, (60, 300, 1020, 520), a, VGOLD, None, None)
    lg = IMG['logo'].resize((140, 140)); lg.putalpha(lg.split()[3].point(lambda v: int(v * a))); comp(im, lg, (90, 340))
    d = ImageDraw.Draw(im, 'RGBA')
    txt(d, 260, 330, 'COACH AGZ', f(BEB, 104), CREAM, a)
    txt(d, 262, 442, '@coach.agz', f(MONO, 32), GOLD, a)
    tag(d, 560, 436, 'ENHANCED COACHING', VGOLD, 24, a)

# ---------------- captions (saved style: Bebas, every word, lit red block on active word) ----------------
FIX = {'npp': 'NPP', 'tren': 'TREN'}
def build_groups():
    G = []; cur = []
    for i, x in enumerate(WORDS):
        if cur:
            prev = WORDS[cur[-1]]
            if len(cur) >= 3 or x['s'] - prev['e'] > 0.28 or prev['w'][-1] in '.,?!' or (prev['s'] < CUT1 <= x['s']) or (prev['s'] < CUT2 <= x['s']):
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
CAP_Y = 1480
def captions(im, t):
    g = group_at(t)
    if not g: return
    d = ImageDraw.Draw(im, 'RGBA')
    ws = []
    for i in g:
        raw = WORDS[i]['w']; key = raw.lower().strip('.,?!')
        ws.append(FIX.get(key, raw.upper()).rstrip(',.') if key in FIX else raw.upper().rstrip(',.'))
    damn = len(g) == 1 and ws[0].startswith('DAMN')
    size = 170 if damn else 128
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
    CH = 320
    cap = Image.new('RGBA', (W, CH), (0, 0, 0, 0)); cd = ImageDraw.Draw(cap); shd = Image.new('RGBA', (W, CH), (0, 0, 0, 0)); sd = ImageDraw.Draw(shd)
    prev = max(0, act - 1); bt = expo((t - WORDS[g[act]]['s']) / 0.07) if act > 0 else 1
    bx0 = lerp(xs[prev], xs[act], bt) - 18; bx1 = lerp(xs[prev] + wd[prev], xs[act] + wd[act], bt) + 18
    for k, (w_, x_) in enumerate(zip(ws, xs)):
        if k != act: sd.text((x_ + 4, 46), w_, font=fn, fill=(0, 0, 0, 210))
    cap.alpha_composite(shd.filter(ImageFilter.GaussianBlur(6)))
    blk = VGOLD if damn else RED
    lit_bar(cd, bx0, 40 + size * 0.02, bx1, 40 + size * 0.98, blk)
    for k, (w_, x_) in enumerate(zip(ws, xs)):
        cd.text((x_, 40), w_, font=fn, fill=INK if (damn and k == act) else CREAM, stroke_width=0 if k == act else 3, stroke_fill=(0, 0, 0))
    if abs(s - 1) > 0.002:
        cap = cap.resize((int(W * s), int(CH * s)), Image.BICUBIC); ox = int((W - cap.width) / 2); oy = int(CAP_Y - 40 - (cap.height - CH) / 2)
    else: ox, oy = 0, CAP_Y - 40
    comp(im, cap, (ox, oy))

# ---------------- frame ----------------
def frame(src, t):
    global GL
    assets()
    glow = Image.new('RGBA', (W, H), (0, 0, 0, 0)); GL = ImageDraw.Draw(glow, 'RGBA')
    im, k = place_footage(src, t)
    im = im.convert('RGB')
    # light bottom scrim for caption legibility only (footage otherwise untouched)
    yy = np.arange(H); sa = np.clip((yy - 1420) / 300, 0, 1) * 120
    scr = Image.fromarray(np.repeat(sa.astype(np.uint8)[:, None], W, 1))
    comp(im, Image.merge('RGBA', [Image.new('L', (W, H), c) for c in NAVY] + [scr]))
    for sc in (s_credential, s_inbox, s_bloodwork, s_stack, s_camera):
        sc(im, t)
    if k > 0.02:
        for sc in (s_lethal, s_compare):
            sc(im, t)
    s_end(im, t)
    GL = None
    if glow.getbbox():
        sm = glow.resize((W // 4, H // 4), Image.BILINEAR)
        g1 = np.asarray(sm.filter(ImageFilter.GaussianBlur(3.5))).astype(np.float32) / 255; g2 = np.asarray(sm.filter(ImageFilter.GaussianBlur(10))).astype(np.float32) / 255
        prem = np.clip(g1[..., :3] * g1[..., 3:] * 2.3 + g2[..., :3] * g2[..., 3:] * 1.8, 0, 1)
        prem = np.asarray(Image.fromarray((prem * 255).astype(np.uint8)).resize((W, H), Image.BILINEAR)).astype(np.float32) / 255
        b = np.asarray(im.convert('RGB')).astype(np.float32) / 255
        im = Image.fromarray(((1 - (1 - b) * (1 - prem)) * 255).astype(np.uint8))
    d = ImageDraw.Draw(im, 'RGBA'); d.rectangle([0, 0, 7, H], fill=GOLD)
    txt(d, 1050, 1800, '@coach.agz', f(MONO, 24), GOLD, 0.75, 'rs')
    captions(im, t)
    out = im.convert('RGB')
    # 2-frame shake on the LETHAL UNIT slam
    kf = round((t - 12.64) * FPS)
    if kf in (0, 1):
        dx = [9, -5][kf]; z = 1.02; big = out.resize((int(W * z), int(H * z)), Image.BICUBIC); ox = (big.width - W) // 2 - dx; oy = (big.height - H) // 2
        out = big.crop((ox, oy, ox + W, oy + H)); ImageDraw.Draw(out).rectangle([0, 0, 7, H], fill=GOLD)
    return out

if __name__ == '__main__':
    mode = sys.argv[2]
    if mode == 'stills':
        for tt in [float(x) for x in sys.argv[3:]]:
            n = int(round(tt * FPS))
            subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', S + 'assembled.mov', '-vf', f'select=eq(n\\,{n})', '-vsync', '0', '-frames:v', '1', S + 'qc/_src.png'])
            frame(Image.open(S + 'qc/_src.png').convert('RGB'), n / FPS).resize((540, 960)).save(S + f'qc/st_{tt:05.2f}.jpg', quality=88)
        sys.exit()
    n0, n1, out = int(sys.argv[3]), int(sys.argv[4]), sys.argv[5]
    dec = subprocess.Popen(['ffmpeg', '-v', 'error', '-i', S + 'assembled.mov', '-vf', f'select=between(n\\,{n0}\\,{n1 - 1})', '-vsync', '0', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], stdout=subprocess.PIPE)
    enc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-crf', '17', '-preset', 'slow', '-profile:v', 'high', '-level', '4.2', '-pix_fmt', 'yuv420p', out], stdin=subprocess.PIPE)
    for n in range(n0, n1):
        buf = dec.stdout.read(W * H * 3)
        if len(buf) < W * H * 3: print('short', n); break
        enc.stdin.write(frame(Image.frombuffer('RGB', (W, H), buf), n / FPS).tobytes())
    enc.stdin.close(); enc.wait(); dec.kill(); print('done', n0, n1)
