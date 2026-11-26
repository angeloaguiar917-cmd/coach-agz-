# Coach AGZ — "Executive Vault" Reel. 1080x1920, 30 fps.
# Usage: python3 render.py <S> stills t1 t2 ...   |   python3 render.py <S> chunk n0 n1 out.mp4
import json, subprocess, sys, math, random
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
S = sys.argv[1].rstrip('/') + '/'; F = S + 'fonts/'; AS = S + 'assets/'
W, H, FPS = 1080, 1920, 30
WORDS = json.load(open(S + 'words_final.json'))
TR = json.load(open(S + 'trim.json'))
CUTS = []; _acc = 0
for a, b in TR['keep'][:-1]: _acc += b - a; CUTS.append(round(_acc, 4))
DUR = _acc + TR['keep'][-1][1] - TR['keep'][-1][0]

GOLD = (201, 169, 110); CREAM = (244, 241, 234); NAVY = (14, 17, 23); MUTED = (184, 184, 188); DIM = (124, 124, 130)
RED = (255, 34, 28); VGOLD = (255, 194, 26); CYAN = (0, 229, 255); GREEN = (30, 255, 110); DEEP = (2, 3, 8); INK = (6, 8, 14); WHITE = (255, 255, 255)
BEB = 'BebasNeue-Regular.ttf'; BAR = 'BarlowCondensed-Bold.ttf'; BARS = 'BarlowCondensed-SemiBold.ttf'
_fc = {}
def f(n, s, wg=None):
    k = (n, int(s), wg)
    if k not in _fc:
        fo = ImageFont.truetype(F + n, int(s))
        if n == 'DMSans.ttf': fo.set_variation_by_axes([min(40, max(9, int(s) // 2)), wg or 700])
        if n == 'JBMono.ttf': fo.set_variation_by_axes([wg or 500])
        _fc[k] = fo
    return _fc[k]
MONO = lambda s, wg=500: f('JBMono.ttf', s, wg)
DM = lambda s, wg=700: f('DMSans.ttf', s, wg)
def clamp(x, a=0, b=1): return max(a, min(b, x))
def expo(x): x = clamp(x); return 1 if x >= 1 else 1 - 2 ** (-10 * x)
def ease_io(x): x = clamp(x); return 4 * x ** 3 if x < .5 else 1 - (-2 * x + 2) ** 3 / 2
def back_out(x, s=1.2): x = clamp(x); return 1 + (s + 1) * (x - 1) ** 3 + s * (x - 1) ** 2
def lerp(a, b, t): return a + (b - a) * t
def A(c, a): return tuple(c[:3]) + (int(clamp(a) * 255),)
def appear(t, t0, d=0.16): return expo((t - t0) / d)
def vis(t, t0, t1, din=0.18, dout=0.14):  # in/out envelope
    return min(appear(t, t0, din), 1 - clamp((t - t1) / dout))
GL = None

# ---------------- primitives ----------------
def brackets(d, x0, y0, x1, y1, col, L=34, w=4):
    for (cx, cy, sx, sy) in [(x0, y0, 1, 1), (x1, y0, -1, 1), (x0, y1, 1, -1), (x1, y1, -1, -1)]:
        d.line([(cx, cy), (cx + sx * L, cy)], fill=col, width=w); d.line([(cx, cy), (cx, cy + sy * L)], fill=col, width=w)
def lit_bar(d, x0, y0, x1, y1, col, a=1.0):
    h = max(1, int(y1 - y0))
    for i in range(h):
        k = i / h; c = tuple(int(min(255, v * (1.18 - 0.36 * k) + (40 if k < 0.12 else 0))) for v in col)
        d.line([(x0, y0 + i), (x1, y0 + i)], fill=c + (int(255 * clamp(a)),))
def tag(d, x, y, label, col=RED, size=30, a=1.0, glow=True, anchor='l'):
    fn = MONO(size, 700); tw = d.textlength(label, font=fn); h = size + 16
    if anchor == 'r': x = x - tw - 24
    if anchor == 'c': x = x - (tw + 24) / 2
    lit_bar(d, x, y, x + tw + 24, y + h, col, a)
    d.text((x + 12, y + 5), label, font=fn, fill=A(INK if col in (VGOLD, GREEN, CYAN, GOLD) else WHITE, a))
    if GL and glow: GL.rectangle([x - 4, y - 4, x + tw + 28, y + h + 4], outline=A(col, a), width=8)
    return x + tw + 24
def txt(d, x, y, s, font, col, a=1.0, anchor=None, stroke=0):
    d.text((x, y), s, font=font, fill=A(col, a), anchor=anchor, stroke_width=stroke, stroke_fill=A((0, 0, 0), a))
def check(d, x, y, col, s=1.0, a=1.0):
    pts = [(x, y + 16 * s), (x + 10 * s, y + 28 * s), (x + 30 * s, y + 2 * s)]
    d.line(pts, fill=A(col, a), width=int(6 * s))
    if GL: GL.line(pts, fill=A(col, a), width=int(12 * s))
def glowline(d, pts, col, w, a=1.0):
    d.line(pts, fill=A(col, a), width=w, joint='curve')
    if GL: GL.line(pts, fill=A(col, a), width=w * 2 + 4)
def shadow_paste(im, card, x, y, blur=18, off=14, op=0.75):
    sh = Image.new('RGBA', (card.width + 80, card.height + 80), (0, 0, 0, 0))
    m = card.split()[3].point(lambda v: int(v * op))
    sh.paste(Image.new('RGBA', card.size, (0, 0, 0, 255)), (40, 40), m)
    sh = sh.filter(ImageFilter.GaussianBlur(blur))
    im.alpha_composite(sh, (int(x - 40), int(y - 40 + off)))
    im.alpha_composite(card, (int(x), int(y)))
def rounded(img, r):
    m = Image.new('L', img.size, 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, img.width - 1, img.height - 1], radius=r, fill=255)
    out = img.convert('RGBA'); out.putalpha(m); return out
def fade(img, a):
    if a >= 0.999: return img
    img = img.copy(); img.putalpha(img.split()[3].point(lambda v: int(v * clamp(a)))); return img
def place_card(im, card, cx, cy, a=1.0, angle=0.0, scale=1.0, blur=0.0, shadow=True):
    c = card
    if abs(scale - 1) > 0.003: c = c.resize((max(1, int(c.width * scale)), max(1, int(c.height * scale))), Image.BICUBIC)
    if abs(angle) > 0.05: c = c.rotate(angle, resample=Image.BICUBIC, expand=True)
    if blur > 0.3: c = c.filter(ImageFilter.GaussianBlur(blur))
    c = fade(c, a)
    x, y = cx - c.width / 2, cy - c.height / 2
    if shadow: shadow_paste(im, c, x, y, op=0.7 * a)
    else: im.alpha_composite(c, (int(x), int(y)))

_img = {}
def asset(name, w=None, h=None, r=22, border=None):
    k = (name, w, h, r, border)
    if k in _img: return _img[k]
    im = Image.open(AS + name).convert('RGB')
    if w and not h: h = int(im.height * w / im.width)
    if h and not w: w = int(im.width * h / im.height)
    if w: im = im.resize((w, h), Image.LANCZOS)
    im = rounded(im, r)
    if border:
        d = ImageDraw.Draw(im); d.rounded_rectangle([1, 1, im.width - 2, im.height - 2], radius=r, outline=border, width=4)
    _img[k] = im; return im

# ---------------- footage + layout ----------------
def seg_idx(t): return sum(1 for c in CUTS if c <= t + 1e-6)
def zoom_of(t):
    k = seg_idx(t)
    if k == 0: return lerp(1.0, 1.07, expo((t - 0.68) / 0.14)) if t >= 0.68 else 1.0   # first punch lands on "anabolic"
    return 1.0 if k % 2 == 1 else 1.07
PIP_T = (41.97, 52.83)            # split layout window (both edges sit on jump cuts)
PIP_DST = (40, 250, 520, 790); PIP_SRC = (100, 470, 1000, 1482)
def pip_p(t):
    a, b = PIP_T
    if t < a or t >= b + 0.40: return 0.0
    if t < b: return ease_io((t - a) / 0.40)
    return 1 - ease_io((t - b) / 0.40)
_BG = None
def brand_bg():
    global _BG
    if _BG is None:
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        g = np.exp(-(((xx - 980) / 700) ** 2 + ((yy - 200) / 800) ** 2))
        g2 = np.exp(-(((xx - 200) / 600) ** 2 + ((yy - 1500) / 700) ** 2)) * 0.5
        base = np.array(NAVY, np.float32)[None, None, :] * 0.8
        img = base + (g[..., None] * np.array([38, 30, 18]) + g2[..., None] * np.array([10, 10, 22]))
        rng = np.random.default_rng(3); img += rng.normal(0, 2.2, img.shape)
        # faint grid lines (data-room texture)
        img[::90, :, :] += 5; img[:, ::90, :] += 5
        _BG = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).convert('RGBA')
    return _BG
def footage(src, t):
    z = zoom_of(t); p = pip_p(t)
    if z != 1.0:
        big = src.resize((int(W * z), int(H * z)), Image.BICUBIC); ox = (big.width - W) // 2; oy = int((big.height - H) * 0.42)
        src = big.crop((ox, oy, ox + W, oy + H))
    # gambling impact: 2-frame kick
    k = round((t - 15.98) * FPS)
    if k in (0, 1):
        zz = 1.035; big = src.resize((int(W * zz), int(H * zz)), Image.BICUBIC); ox = (big.width - W) // 2 + (8 if k == 0 else -4); oy = (big.height - H) // 2
        src = big.crop((ox, oy, ox + W, oy + H))
    if p <= 0: return src.convert('RGBA')
    sx0, sy0, sx1, sy1 = [lerp(a, b, p) for a, b in zip((0, 0, W, H), PIP_SRC)]
    dx0, dy0, dx1, dy1 = [lerp(a, b, p) for a, b in zip((0, 0, W, H), PIP_DST)]
    im = brand_bg().copy()
    # behind the card: a blurred dark echo of the footage fades away
    card = src.crop((int(sx0), int(sy0), int(sx1), int(sy1))).resize((max(1, int(dx1 - dx0)), max(1, int(dy1 - dy0))), Image.BICUBIC)
    card = rounded(card, int(lerp(0, 28, p)))
    shadow_paste(im, card, dx0, dy0, blur=24, off=18, op=0.8 * p)
    d = ImageDraw.Draw(im, 'RGBA')
    d.rounded_rectangle([dx0, dy0, dx1, dy1], radius=int(lerp(0, 28, p)), outline=A(GOLD, p), width=3)
    if p > 0.85:
        a = (p - 0.85) / 0.15
        d.ellipse([dx0 + 20, dy0 + 20, dx0 + 36, dy0 + 36], fill=A(RED, a if int(t * 3) % 2 == 0 else a * 0.35))
        txt(d, dx0 + 46, dy0 + 14, 'LIVE', MONO(26, 700), WHITE, a)
    return im

# ---------------- text hook (frame 0) ----------------
HOOK = [[('Reddit ', False), ('BLOODWORK', True), (' advice', False)], [('is gambling your health', False)]]
HOOK_END = 4.30
def text_hook(im, t):
    if t >= HOOK_END + 0.15: return
    a = 1 - clamp((t - HOOK_END) / 0.15)
    lay = Image.new('RGBA', (W, 420), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    size = 86
    while max(sum(d.textlength(s, font=DM(size, 800)) for s, _ in ln) for ln in HOOK) > 940: size -= 2
    fn = DM(size, 800)
    for li, ln in enumerate(HOOK):
        tw = sum(d.textlength(s, font=fn) for s, _ in ln); x = (W - tw) / 2; y = 60 + li * int(size * 1.18)
        for s, em in ln:
            d.text((x, y), s, font=fn, fill=VGOLD if em else WHITE, stroke_width=7, stroke_fill=(0, 0, 0))
            x += d.textlength(s, font=fn)
    sh = lay.filter(ImageFilter.GaussianBlur(10)); sh = Image.merge('RGBA', [Image.new('L', sh.size, 0)] * 3 + [sh.split()[3].point(lambda v: int(v * 0.8))])
    out = Image.new('RGBA', (W, 420), (0, 0, 0, 0)); out.alpha_composite(sh, (0, 8)); out.alpha_composite(lay)
    im.alpha_composite(fade(out, a), (0, 230))

# ---------------- topic band (hook exit -> midpoint cut) ----------------
BAND_T = (HOOK_END, 29.2)
def topic_band(im, t):
    if not (BAND_T[0] <= t < BAND_T[1]): return
    a = appear(t, BAND_T[0], 0.15)
    d = ImageDraw.Draw(im, 'RGBA')
    d.rectangle([8, 212, W, 290], fill=A(NAVY, 0.88 * a)); d.line([(8, 290), (W, 290)], fill=A(GOLD, 0.6 * a), width=2)
    fn = DM(40, 700); x = 40
    for s, em in [('Your ', False), ('BLOODWORK', True), (' expertise', False)]:
        txt(d, x, 226, s, fn, VGOLD if em else CREAM, a); x += d.textlength(s, font=fn)
    tw = d.textlength('@coach.agz', font=MONO(26)); txt(d, W - 40 - tw, 238, '@coach.agz', MONO(26), GOLD, a)

# ================= OVERLAYS (top zone y 310..640 unless noted) =================
def forum_card(w, h, kind, label=None, hl=False):
    c = Image.new('RGBA', (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(c)
    if kind == 'forum':
        d.rounded_rectangle([0, 0, w - 1, h - 1], radius=18, fill=(22, 24, 30, 250), outline=(70, 74, 86, 255), width=2)
        d.rectangle([0, 0, w, 46], fill=(36, 38, 46, 255)); d.rounded_rectangle([0, 0, w - 1, 46], radius=18, fill=(36, 38, 46, 255))
        d.text((16, 10), 'FORUM · THREAD', font=MONO(22, 700), fill=(200, 200, 205))
        d.ellipse([16, 62, 52, 98], fill=(90, 94, 110)); d.text((62, 66), 'anon_user_77', font=MONO(22), fill=(160, 164, 175))
        for i, ww in enumerate([0.86, 0.7, 0.8, 0.5]):
            d.rounded_rectangle([16, 116 + i * 30, 16 + (w - 32) * ww, 132 + i * 30], radius=6, fill=(70, 74, 86))
        d.polygon([(22, h - 22), (34, h - 40), (46, h - 22)], fill=(150, 150, 160)); d.text((56, h - 46), 'trust me bro', font=MONO(20), fill=(150, 150, 160))
    else:
        for yy in range(h):
            k = yy / h; d.line([(0, yy), (w, yy)], fill=(int(30 + 30 * k), int(32 + 20 * k), int(44 + 24 * k), 255))
        m = Image.new('L', (w, h), 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, w - 1, h - 1], radius=18, fill=255); c.putalpha(m); d = ImageDraw.Draw(c)
        cx, cy = w / 2, h * 0.42
        d.ellipse([cx - 34, cy - 34, cx + 34, cy + 34], fill=(255, 255, 255, 60)); d.polygon([(cx - 11, cy - 18), (cx - 11, cy + 18), (cx + 19, cy)], fill=(255, 255, 255, 230))
        for i, ww in enumerate([0.8, 0.55]): d.rounded_rectangle([14, h - 70 + i * 24, 14 + (w - 28) * ww, h - 56 + i * 24], radius=5, fill=(200, 200, 210, 140))
        d.text((14, 12), label or 'VIDEO', font=MONO(20, 700), fill=(255, 194, 26) if hl else (220, 220, 228))
        d.rounded_rectangle([0, 0, w - 1, h - 1], radius=18, outline=(255, 194, 26) if hl else (90, 94, 110), width=4 if hl else 2)
    return c
_FC = {}
def fc(key, *a):
    if key not in _FC: _FC[key] = forum_card(*a)
    return _FC[key]
FEED = [  # t_in, cx, cy, angle, key, args
    (5.98, 210, 470, -4, 'forum', (300, 270, 'forum')),
    (7.94, 470, 468, 3, 'v1', (190, 290, 'video')),
    (9.20, 680, 472, -2, 'v2', (190, 290, 'video')),
    (9.42, 890, 466, 4, 'v3', (190, 290, 'video')),
]
def ov_feed(im, t):
    t1 = 12.22
    if not (5.9 <= t < t1 + 0.3): return
    for i, (t0, cx, cy, ang, key, args) in enumerate(FEED):
        if t < t0: continue
        p = expo((t - t0) / 0.20)
        if key == 'v3' and t >= 10.58: card = fc('v3h', 190, 290, 'video', '@coach.agz', True)
        else: card = fc(key, *args)
        fall = clamp((t - t1 - i * 0.03) / 0.22)
        y = cy + lerp(60, 0, p) + 420 * fall ** 2; a = p * (1 - fall)
        place_card(im, card, cx, y, a, ang * (1 + 2 * fall), lerp(1.06, 1.0, p), blur=4 * (1 - p))
    d = ImageDraw.Draw(im, 'RGBA')
    if 11.58 <= t < t1:
        pa = appear(t, 11.58, 0.12)
        for (t0, cx, cy, ang, key, (w, h, _)) in FEED:
            brackets(d, cx - w / 2 - 10, cy - h / 2 - 10, cx + w / 2 + 10, cy + h / 2 + 10, A(RED, pa), 26, 6)
            if GL: brackets(GL, cx - w / 2 - 10, cy - h / 2 - 10, cx + w / 2 + 10, cy + h / 2 + 10, A(RED, pa), 26, 12)
        tag(d, 540, 590, 'GENERIC · NOT YOUR PANEL', RED, 30, pa, anchor='c')

def ov_t5(im, t):  # "customized to you" — client feedback
    t0, t1 = 12.26, 13.36
    if not (t0 <= t < t1 + 0.15): return
    p = expo((t - t0) / 0.22); out = clamp((t - t1) / 0.14)
    card = asset('t5_structure.png', w=900, r=24)
    place_card(im, card, 540, lerp(500, 470, p) - 40 * out, p * (1 - out), lerp(-2.5, -1.2, p), 1.0, blur=6 * (1 - p))
    d = ImageDraw.Draw(im, 'RGBA'); a = p * (1 - out)
    tag(d, 90, 318, 'CLIENT · WHATSAPP', VGOLD, 24, a)

def ov_gauge(im, t):  # optimization vs gambling
    t0, t1 = 13.40, 17.20
    if not (t0 <= t < t1 + 0.16): return
    a = vis(t, t0, t1, 0.2, 0.16); d = ImageDraw.Draw(im, 'RGBA')
    cx, cy, r = 540, 628, 250
    # dark lens behind the dial (keeps lines readable over the night sky)
    d.pieslice([cx - r - 40, cy - r - 40, cx + r + 40, cy + r + 40], 180, 360, fill=A(DEEP, 0.55 * a))
    zones = [(180, 236, GREEN), (238, 302, VGOLD), (304, 360, RED)]
    on_red = t >= 15.98
    for a0, a1, col in zones:
        lit = (col == GREEN and 14.46 <= t < 15.98) or (col == RED and on_red)
        cc = col if lit else tuple(int(v * 0.35) for v in col)
        d.arc([cx - r, cy - r, cx + r, cy + r], a0, a1, fill=A(cc, a), width=26)
        if GL and lit: GL.arc([cx - r, cy - r, cx + r, cy + r], a0, a1, fill=A(col, a), width=40)
    for k in range(0, 19):
        ang = math.radians(180 + k * 10); L = 26 if k % 3 == 0 else 14
        d.line([(cx + (r - 40) * math.cos(ang), cy + (r - 40) * math.sin(ang)), (cx + (r - 40 - L) * math.cos(ang), cy + (r - 40 - L) * math.sin(ang))], fill=A(CREAM, 0.7 * a), width=3)
    # needle
    if t < 14.46: ang = lerp(250, 205, expo((t - 13.6) / 0.6))
    elif t < 15.98: ang = 205 + 3 * math.sin(t * 5)
    else: ang = lerp(205, 338, expo((t - 15.98) / 0.16)) + (1.6 * math.sin(t * 47) * math.exp(-(t - 16.1) * 2) if t > 16.1 else 0)
    ra = math.radians(ang); nx, ny = cx + (r - 30) * math.cos(ra), cy + (r - 30) * math.sin(ra)
    glowline(d, [(cx, cy), (nx, ny)], WHITE if not on_red else RED, 7, a)
    d.ellipse([cx - 20, cy - 20, cx + 20, cy + 20], fill=A(CREAM, a)); d.ellipse([cx - 8, cy - 8, cx + 8, cy + 8], fill=A(INK, a))
    fn = f(BEB, 54)
    txt(d, cx - r - 20, cy - 40, 'OPTIMIZATION', fn, GREEN if 14.46 <= t < 15.98 else DIM, a, anchor='rs')
    txt(d, cx + r + 20, cy - 40, 'GAMBLING', fn, RED if on_red else DIM, a, anchor='ls')
    txt(d, cx, 334, 'RISK · YOUR OWN HEALTH', MONO(26, 700), CREAM, a * appear(t, 13.5), anchor='mt')
    if on_red: tag(d, cx + r + 20, cy - 26, 'NO DATA', RED, 26, a * appear(t, 16.58), anchor='l')

def ov_years(im, t):  # 15 years — big stat + timeline ruler
    t0, t1 = 17.20, 20.03
    if not (t0 <= t < t1 + 0.14): return
    a = vis(t, t0, t1, 0.16, 0.14); d = ImageDraw.Draw(im, 'RGBA')
    n = int(round(lerp(0, 15, ease_io((t - 18.30) / 0.45)))) if t >= 18.30 else 0
    land = appear(t, 18.75, 0.1)
    big = f(BEB, int(lerp(300, 280, land)))
    txt(d, 70, 300, f'{n:02d}', big, VGOLD, a)
    if GL and t >= 18.75: GL.text((70, 300), f'{n:02d}', font=big, fill=A(VGOLD, a * 0.6))
    txt(d, 380, 330, 'YEARS', f(BEB, 110), CREAM, a * appear(t, 18.68))
    txt(d, 386, 450, 'IN THE SPACE', MONO(30, 700), GOLD, a * appear(t, 19.36))
    # ruler 2011 -> 2026 (15 years back from today)
    x0, x1, y = 386, 1000, 560; pr = ease_io((t - 18.34) / 0.9)
    if pr > 0:
        xe = lerp(x0, x1, pr); d.line([(x0, y), (xe, y)], fill=A(CREAM, a), width=3)
        for k in range(16):
            xx = lerp(x0, x1, k / 15)
            if xx <= xe + 1: d.line([(xx, y - (16 if k % 5 == 0 else 8)), (xx, y)], fill=A(CREAM, a), width=3)
        txt(d, x0, y + 14, '2011', MONO(24), MUTED, a)
        if pr > 0.98:
            txt(d, x1, y + 14, '2026', MONO(24, 700), VGOLD, a, anchor='ra')
            pulse = 0.6 + 0.4 * math.sin(t * 9)
            d.ellipse([x1 - 10, y - 10, x1 + 10, y + 10], fill=A(VGOLD, a))
            if GL: GL.ellipse([x1 - 22, y - 22, x1 + 22, y + 22], fill=A(VGOLD, a * pulse))

_ORDER = None
def ov_matrix(im, t):  # 250+ protocols — dot matrix fill; collapses into a folder (handoff)
    global _ORDER
    t0, t1 = 20.03, 23.30
    if not (t0 <= t < t1 + 0.3): return
    if _ORDER is None:
        _ORDER = list(range(250)); random.Random(5).shuffle(_ORDER)
    a = appear(t, t0, 0.18); d = ImageDraw.Draw(im, 'RGBA')
    col_ = clamp((t - t1) / 0.3)  # collapse
    x0, y0, x1, y1 = 60, 318, 1020, 640
    if col_ < 1:
        pa = a * (1 - col_)
        d.rounded_rectangle([x0, y0, x1, y1], radius=16, fill=A(DEEP, 0.86 * pa)); brackets(d, x0, y0, x1, y1, A(VGOLD, pa), 30, 5)
        if GL: brackets(GL, x0, y0, x1, y1, A(VGOLD, pa), 30, 10)
        txt(d, x0 + 24, y0 + 20, 'PROTOCOL LIBRARY', MONO(28, 700), VGOLD, pa)
        fill = 0 if t < 21.84 else int(250 * ease_io((t - 21.84) / 0.62))
        lab = f'{fill}+' if fill >= 250 else f'{fill}'
        txt(d, x1 - 24, y0 + 6, lab, f(BEB, 84), WHITE if fill < 250 else VGOLD, pa, anchor='ra')
        txt(d, x0 + 24, y0 + 56, 'PROTOCOLS BUILT', MONO(22), MUTED, pa)
        for i in range(250):
            r_, c_ = divmod(i, 25); cx = x0 + 40 + c_ * 36.5; cy = y0 + 110 + r_ * 20
            k = _ORDER.index(i) if fill else 999
            on = k < fill
            tx, ty = 90 + (i % 25) * 6, 352 + (i // 25) * 3
            cxx, cyy = lerp(cx, tx, ease_io(col_)), lerp(cy, ty, ease_io(col_))
            d.rectangle([cxx, cyy, cxx + 26, cyy + 12], fill=A(VGOLD if on else (50, 54, 66), pa))
        if GL and fill: GL.rectangle([x0 + 40, y0 + 110, x0 + 40 + 25 * 36.5, y0 + 110 + 10 * 20], fill=A(VGOLD, pa * 0.22 * min(1, fill / 250)))

FOLDERS = [('PROTOCOLS', VGOLD, 23.30), ('COMPOUND BREAKDOWNS', CYAN, 23.38), ('BLOODWORK GUIDES', RED, 24.54)]
def folder_img(label, col):
    k = ('fold', label)
    if k in _img: return _img[k]
    w, h = 470, 74; c = Image.new('RGBA', (w, h + 14), (0, 0, 0, 0)); d = ImageDraw.Draw(c)
    d.rounded_rectangle([0, 0, 150, 30], radius=8, fill=col + (255,))
    d.rounded_rectangle([0, 14, w - 1, h + 13], radius=10, fill=(16, 19, 28, 250), outline=col + (255,), width=4)
    d.rectangle([0, 14, 12, h + 13], fill=col + (255,))
    d.text((30, 26), label, font=f(BAR, 46), fill=(244, 241, 234))
    _img[k] = c; return c
def vault_door(d, cx, cy, r, rot, a, locked):
    d.ellipse([cx - r - 14, cy - r - 14, cx + r + 14, cy + r + 14], fill=A((10, 12, 18), 0.95 * a), outline=A(GOLD, a), width=6)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=A((24, 27, 36), a), outline=A((90, 84, 70), a), width=4)
    for k in range(12):  # rim bolts
        an = math.radians(k * 30); bx, by = cx + (r + 1) * math.cos(an), cy + (r + 1) * math.sin(an)
        d.ellipse([bx - 6, by - 6, bx + 6, by + 6], fill=A(VGOLD if locked else (120, 110, 90), a))
    for k in range(3):  # wheel spokes
        an = math.radians(rot + k * 60)
        d.line([(cx - 0.62 * r * math.cos(an), cy - 0.62 * r * math.sin(an)), (cx + 0.62 * r * math.cos(an), cy + 0.62 * r * math.sin(an))], fill=A(CREAM, a), width=9)
    d.ellipse([cx - 0.62 * r, cy - 0.62 * r, cx + 0.62 * r, cy + 0.62 * r], outline=A(CREAM, a), width=5)
    d.ellipse([cx - 24, cy - 24, cx + 24, cy + 24], fill=A(VGOLD if locked else CREAM, a))
    if GL and locked: GL.ellipse([cx - r - 18, cy - r - 18, cx + r + 18, cy + r + 18], outline=A(VGOLD, a), width=14)
def ov_vault(im, t):
    t0, t1 = 23.30, 27.23
    if not (t0 <= t < t1 + 0.16): return
    a = vis(t, t0, t1, 0.12, 0.16); d = ImageDraw.Draw(im, 'RGBA')
    cx, cy, r = 838, 470, 132
    rot = 0 if t < 26.86 else 90 * expo((t - 26.86) / 0.25)
    locked = t >= 26.86 + 0.12
    for i, (lab, col, ti) in enumerate(FOLDERS):
        if t < ti: continue
        p = expo((t - ti) / 0.18)
        x, y = 70, 340 + i * 98 - lerp(40, 0, p)
        ins = ease_io((t - (25.36 + i * 0.16)) / 0.34)
        if ins > 0:
            x = lerp(x, cx - 60, ins); y = lerp(y, cy - 40, ins)
        sc = lerp(1, 0.25, ins); al = a * p * (1 - clamp((ins - 0.7) / 0.3))
        img = folder_img(lab, col)
        place_card(im, img, x + img.width * sc / 2, y + img.height * sc / 2, al, 0, sc, shadow=False)
    d = ImageDraw.Draw(im, 'RGBA')
    vault_door(d, cx, cy, r, rot, a * appear(t, 23.5, 0.2), locked)
    if t >= 26.86:
        b = a * appear(t, 26.9, 0.12)
        fn = f(BEB, 92); txt(d, 70, 420, 'EXECUTIVE', fn, CREAM, b); txt(d, 70 + d.textlength('EXECUTIVE ', font=fn), 420, 'VAULT', fn, VGOLD, b)
        tag(d, 74, 528, 'LOCKED IN · ONE PLACE', VGOLD, 26, b)
    if t >= 26.86 and t < 27.0:  # flash on lock
        fl = 1 - (t - 26.86) / 0.14
        if GL: GL.ellipse([cx - r - 60, cy - r - 60, cx + r + 60, cy + r + 60], fill=A(VGOLD, 0.6 * fl))

RESULTS = [(31.48, 'BLOODWORK GUIDE', CYAN, 'Reading your own panel'), (33.24, 'PROTOCOL', VGOLD, 'Health markers to track on cycle'), (34.84, 'COMPOUND', RED, 'Running it the right way')]
QUERY = 'how to optimize my bloods'
def ov_search(im, t):
    t0, t1 = 27.23, 35.95
    if not (t0 <= t < t1 + 0.16): return
    a = vis(t, t0, t1, 0.2, 0.16); d = ImageDraw.Draw(im, 'RGBA')
    y0 = lerp(300, 318, appear(t, t0, 0.25))
    d.rounded_rectangle([60, y0, 1020, y0 + 78], radius=39, fill=A((12, 14, 20), 0.95 * a), outline=A(VGOLD, a), width=3)
    if GL: GL.rounded_rectangle([60, y0, 1020, y0 + 78], radius=39, outline=A(VGOLD, a * 0.6), width=6)
    d.ellipse([96, y0 + 22, 126, y0 + 52], outline=A(VGOLD, a), width=4); d.line([(122, y0 + 49), (136, y0 + 63)], fill=A(VGOLD, a), width=5)
    n = 0 if t < 28.34 else int(len(QUERY) * clamp((t - 28.34) / 1.5))
    q = QUERY[:n]; fn = DM(38, 500)
    if n == 0: txt(d, 160, y0 + 18, 'Search the vault…', fn, (110, 112, 122), a)
    else: txt(d, 160, y0 + 18, q, fn, CREAM, a)
    if int(t * 2.5) % 2 == 0 and n < len(QUERY):
        cxp = 160 + d.textlength(q, font=fn) + 4; d.line([(cxp, y0 + 20), (cxp, y0 + 60)], fill=A(VGOLD, a), width=3)
    txt(d, 990, y0 + 26, '250+', MONO(24, 700), GOLD, a, anchor='ra')
    for i, (ti, kind, col, title) in enumerate(RESULTS):
        if t < ti: continue
        p = expo((t - ti) / 0.18); yy = y0 + 94 + i * 76; x = 60 + lerp(40, 0, p)
        d.rounded_rectangle([x, yy, x + 960, yy + 66], radius=12, fill=A((16, 19, 28), 0.94 * a * p), outline=A((60, 64, 80), a * p), width=2)
        d.rectangle([x, yy + 8, x + 6, yy + 58], fill=A(col, a * p))
        tag(d, x + 22, yy + 13, kind, col, 22, a * p, glow=False)
        tw = d.textlength(kind, font=MONO(22, 700)) + 24
        txt(d, x + 22 + tw + 22, yy + 13, title, DM(32, 600), CREAM, a * p)
        txt(d, x + 930, yy + 14, '→', DM(34, 700), col, a * p, anchor='ra')
        # scan sweep on arrival
        if 0 < t - ti < 0.3 and GL:
            sx = x + 960 * ((t - ti) / 0.3); GL.line([(sx, yy), (sx, yy + 66)], fill=A(col, 0.9), width=8)

DONUT = [(36.40, 'CYCLES', VGOLD), (37.34, 'ESTROGEN', CYAN), (38.06, 'SIDE EFFECTS', RED), (38.66, 'CARDIO HEALTH', CREAM)]
def ov_donut(im, t):
    t0, t1 = 36.10, 41.97
    if not (t0 <= t < t1 + 0.16): return
    a = vis(t, t0, t1, 0.16, 0.14); d = ImageDraw.Draw(im, 'RGBA')
    cx, cy, ro, ri = 230, 480, 152, 98
    d.ellipse([cx - ro, cy - ro, cx + ro, cy + ro], fill=A(DEEP, 0.6 * a))
    d.ellipse([cx - ro, cy - ro, cx + ro, cy + ro], outline=A((50, 54, 66), a), width=ro - ri)
    for i, (ti, lab, col) in enumerate(DONUT):
        if t < ti: continue
        p = expo((t - ti) / 0.28); s0 = -90 + i * 90 + 2; s1 = s0 + 86 * p
        d.arc([cx - ro, cy - ro, cx + ro, cy + ro], s0, s1, fill=A(col, a), width=ro - ri)
        if GL: GL.arc([cx - ro - 4, cy - ro - 4, cx + ro + 4, cy + ro + 4], s0, s1, fill=A(col, a * 0.5), width=10)
        # legend rows: arrive staggered, snap into a clean column on "organized"
        org = ease_io((t - 39.80) / 0.3)
        lx = lerp(470 + (i % 2) * 70, 450, org); ly = 352 + i * 66
        q = appear(t, ti, 0.14)
        d.rectangle([lx, ly + 10, lx + 30, ly + 40], fill=A(col, a * q))
        txt(d, lx + 48, ly, lab, f(BAR, 52), CREAM, a * q)
        if org > 0.9: check(d, 980, ly + 10, GREEN, 0.9, a * (org - 0.9) * 10)
    # centre: minutes stopwatch
    if t >= 41.06:
        b = a * appear(t, 41.06, 0.14); sw = (t - 41.06) * 360 / 0.8
        d.arc([cx - ri + 12, cy - ri + 12, cx + ri - 12, cy + ri - 12], -90, -90 + min(360, sw), fill=A(VGOLD, b), width=6)
        txt(d, cx, cy - 4, 'MIN', f(BEB, 70), VGOLD, b, anchor='mm'); txt(d, cx, cy + 40, 'SEARCH', MONO(20, 700), CREAM, b, anchor='mm')
    else:
        txt(d, cx, cy, 'VAULT', f(BEB, 58), CREAM, a * appear(t, 36.4), anchor='mm')

# ---------------- split layout content ----------------
def rail(im, t):  # right of the PiP: the path
    p = pip_p(t)
    if p < 0.6 or not (PIP_T[0] <= t < PIP_T[1] + 0.2): return
    a = clamp((p - 0.6) / 0.4) * (1 - clamp((t - (PIP_T[1] - 0.12)) / 0.12)); d = ImageDraw.Draw(im, 'RGBA')
    x0, y0 = 560, 262
    txt(d, x0, y0, 'THE PATH', MONO(26, 700), GOLD, a)
    d.line([(x0 + 150, y0 + 16), (1030, y0 + 16)], fill=A(GOLD, a * 0.5), width=2)
    steps = [(44.02, '01', 'EXECUTIVE VAULT', '$9 ACCESS'), (47.58, '02', 'LEARN MY PROCESS', 'HOW I RUN CLIENTS'), (50.72, '03', '1:1 COACHING', 'WHEN YOU\'RE READY')]
    for i, (ti, num, lab, sub) in enumerate(steps):
        y = y0 + 70 + i * 160; on = t >= ti; q = appear(t, ti, 0.14) if on else 0
        col = VGOLD if on else (70, 74, 86)
        if i < 2:
            d.line([(x0 + 34, y + 70), (x0 + 34, y + 160)], fill=A((70, 74, 86), a), width=4)
            nxt = steps[i + 1][0]
            if t >= nxt: d.line([(x0 + 34, y + 70), (x0 + 34, y + 70 + 90 * appear(t, nxt - 0.2, 0.2))], fill=A(VGOLD, a), width=4)
        d.ellipse([x0, y, x0 + 68, y + 68], fill=A(VGOLD if on else (20, 23, 32), a), outline=A(col, a), width=4)
        if GL and on: GL.ellipse([x0 - 6, y - 6, x0 + 74, y + 74], outline=A(VGOLD, a * q), width=10)
        txt(d, x0 + 34, y + 35, num, f(BEB, 40), INK if on else MUTED, a, anchor='mm')
        txt(d, x0 + 90, y + 2, lab, f(BEB, 56), CREAM if on else DIM, a)
        txt(d, x0 + 92, y + 62, sub, MONO(20, 600), GOLD if on else (90, 94, 106), a)

def price_graph(im, t):
    t0, t1 = 42.20, 44.60
    if not (t0 <= t < t1 + 0.2): return
    a = vis(t, t0, t1, 0.2, 0.2); d = ImageDraw.Draw(im, 'RGBA')
    x0, y0, x1, y1 = 40, 830, 1040, 1370
    d.rounded_rectangle([x0, y0, x1, y1], radius=24, fill=A(DEEP, 0.88 * a), outline=A((60, 64, 80), a), width=2)
    txt(d, x0 + 30, y0 + 24, 'EXECUTIVE VAULT · PRICE', MONO(26, 700), GOLD, a)
    base = y1 - 70; d.line([(x0 + 60, base), (x1 - 60, base)], fill=A(CREAM, a * 0.8), width=3)
    for k in range(1, 5):
        yy = base - k * 95; d.line([(x0 + 60, yy), (x1 - 60, yy)], fill=A((50, 54, 66), a * 0.7), width=1)
    MAXH = 290
    # $200 bar
    if t >= 42.50:
        p = expo((t - 42.50) / 0.35); h = MAXH * p
        bx0, bx1 = 200, 420
        d.rectangle([bx0, base - h, bx1, base], fill=A((120, 122, 132), a))
        txt(d, (bx0 + bx1) / 2, base - h - 12, '$200', f(BEB, 110), CREAM, a * p, anchor='ms')
        txt(d, (bx0 + bx1) / 2, base + 14, 'NORMALLY', MONO(24, 700), MUTED, a, anchor='mt')
        if t >= 42.98:
            q = expo((t - 42.98) / 0.12)
            sx0, sy0, sx1, sy1 = bx0 - 30, base - h - 110, bx1 + 30, base - 20
            glowline(d, [(sx0, sy0), (lerp(sx0, sx1, q), lerp(sy0, sy1, q))], RED, 12, a)
    if t >= 44.02:
        p = expo((t - 44.02) / 0.18); h = MAXH * 9 / 200 * p   # true scale: 9/200 of the $200 bar
        bx0, bx1 = 640, 860
        lit_bar(d, bx0, base - h, bx1, base, VGOLD, a)
        if GL: GL.rectangle([bx0, base - h, bx1, base], fill=A(VGOLD, a))
        s = lerp(1.25, 1.0, expo((t - 44.02) / 0.14))
        fn = f(BEB, int(200 * s)); txt(d, (bx0 + bx1) / 2, base - h - 16, '$9', fn, VGOLD, a, anchor='ms')
        if GL: GL.text(((bx0 + bx1) / 2, base - h - 16), '$9', font=fn, fill=A(VGOLD, a * 0.5), anchor='ms')
        txt(d, (bx0 + bx1) / 2, base + 14, 'NOW', MONO(24, 700), VGOLD, a, anchor='mt')
        tag(d, 1010, y0 + 20, '−95%', RED, 28, a * appear(t, 44.2), anchor='r')

DECK = [  # t_in, asset, label, entry style
    (44.84, 't6_level.png', 'CLIENT · WHATSAPP', 'right'),
    (46.60, 't7_feedback.png', 'CLIENT · CHECK-IN FEEDBACK', 'rise'),
    (48.40, 't1_ba_tattoo.png', 'CLIENT · BEFORE / AFTER', 'slam'),
    (49.86, 't3_ba_beach.png', 'CLIENT · BEFORE / AFTER', 'left'),
    (51.36, 'pair', 'CLIENT · DM + WHATSAPP', 'fan'),
]
REG = (40, 830, 1040, 1370)
def deck_card(name):
    rw, rh = REG[2] - REG[0] - 40, REG[3] - REG[1] - 70
    im = Image.open(AS + name); sc = min(rw / im.width, rh / im.height)
    return asset(name, w=int(im.width * sc), h=int(im.height * sc), r=22, border=(201, 169, 110))
def proof_deck(im, t):
    if not (DECK[0][0] <= t < PIP_T[1] + 0.1): return
    end_a = 1 - clamp((t - (PIP_T[1] - 0.14)) / 0.14)
    cur = max(i for i, c in enumerate(DECK) if c[0] <= t)
    cx, cy = (REG[0] + REG[2]) / 2, (REG[1] + REG[3]) / 2 + 22
    d0 = ImageDraw.Draw(im, 'RGBA')
    for i in range(max(0, cur - 1), cur + 1):
        t0, name, lab, style = DECK[i]
        p = expo((t - t0) / 0.24)
        under = i < cur
        if under:  # previous card sinks back
            q = expo((t - DECK[cur][0]) / 0.25); a = (1 - q) * end_a
            if a <= 0.01: continue
            if name == 'pair': continue
            place_card(im, deck_card(name), cx, cy + 10 * q, a, -2 * q, lerp(1, 0.9, q), blur=3 * q)
            continue
        a = p * end_a
        if name == 'pair':
            for j, (nm, ox, ang, dl) in enumerate([('t4_quote.png', -150, -2.5, 0), ('t2_dm_cut.png', 330, 4, 0.18)]):
                pp = expo((t - t0 - dl) / 0.24)
                if pp <= 0: continue
                c = deck_card(nm) if nm != 't4_quote.png' else asset(nm, w=640, r=22, border=(201, 169, 110))
                if nm == 't2_dm_cut.png': c = asset(nm, h=470, r=22, border=(201, 169, 110))
                place_card(im, c, cx + ox + lerp(120 if j else -120, 0, pp), cy, pp * end_a, lerp(ang * 2.5, ang, pp), 1.0, blur=5 * (1 - pp))
        else:
            c = deck_card(name)
            if style == 'right': place_card(im, c, cx + lerp(500, 0, p), cy, a, lerp(-8, -1.5, p), 1.0, blur=6 * (1 - p))
            elif style == 'left': place_card(im, c, cx - lerp(500, 0, p), cy, a, lerp(8, 1.5, p), 1.0, blur=6 * (1 - p))
            elif style == 'rise': place_card(im, c, cx, cy + lerp(260, 0, p), a, 0, lerp(0.92, 1.0, p), blur=5 * (1 - p))
            elif style == 'slam':
                s = lerp(1.18, 1.0, expo((t - t0) / 0.12)); place_card(im, c, cx, cy, min(1, appear(t, t0, 0.06)) * end_a, 0, s, blur=0)
        d = ImageDraw.Draw(im, 'RGBA')
        tag(d, REG[0] + 20, REG[1] - 10, lab, VGOLD, 24, a)
        if name == 't1_ba_tattoo.png' or name == 't3_ba_beach.png':
            tag(d, REG[2] - 20, REG[1] - 10, 'REAL CLIENT', GREEN, 24, a * appear(t, t0 + 0.3), anchor='r')
        if name == 'pair' and t >= 51.80:
            tag(d, REG[2] - 20, REG[1] - 10, '100% REAL', RED, 24, appear(t, 51.80) * end_a, anchor='r')

# ---------------- CTA ----------------
LOGO = None
def cta(im, t):
    t0 = 53.0
    if t < t0: return
    global LOGO
    a = appear(t, t0 + 0.05, 0.2); d = ImageDraw.Draw(im, 'RGBA')
    if LOGO is None:
        lg = Image.open(AS + 'logo.jpg').convert('RGB'); s = min(lg.size); lg = lg.crop(((lg.width - s) // 2, (lg.height - s) // 2, (lg.width + s) // 2, (lg.height + s) // 2)).resize((170, 170), Image.LANCZOS)
        m = Image.new('L', (170, 170), 0); ImageDraw.Draw(m).ellipse([0, 0, 169, 169], fill=255); lg.putalpha(m); LOGO = lg
    x0, y0, x1, y1 = 56, 300, 1024, 640
    reg = im.crop((x0, y0, x1, y1)).convert('RGB').filter(ImageFilter.GaussianBlur(14))
    im.paste(Image.blend(reg, Image.new('RGB', reg.size, DEEP), 0.8 * a).convert('RGBA'), (x0, y0))
    d = ImageDraw.Draw(im, 'RGBA')
    d.rectangle([x0, y0, x1, y1], outline=A(VGOLD, 0.45 * a), width=2); brackets(d, x0, y0, x1, y1, A(VGOLD, a), 30, 5)
    if GL: brackets(GL, x0, y0, x1, y1, A(VGOLD, a), 30, 10)
    im.alpha_composite(fade(LOGO, a), (x0 + 26, y0 + 26)); d = ImageDraw.Draw(im, 'RGBA')
    txt(d, 260, y0 + 30, 'EXECUTIVE VAULT · 250+ PROTOCOLS', MONO(26, 700), VGOLD, a)
    txt(d, 260, y0 + 70, '$9', f(BEB, 62), WHITE, a); tw = d.textlength('$9 ', font=f(BEB, 62))
    txt(d, 260 + tw, y0 + 70, '$200', f(BEB, 62), DIM, a); w200 = d.textlength('$200', font=f(BEB, 62))
    d.line([(260 + tw - 4, y0 + 104), (260 + tw + w200 + 4, y0 + 100)], fill=A(RED, a), width=5)
    if t >= 54.48:
        b = expo((t - 54.48) / 0.1); fn = f(BEB, 84)
        lab = 'COMMENT' if t < 55.04 else 'COMMENT  "VAULT"'
        s = lerp(1.12, 1.0, expo((t - 55.04) / 0.12)) if t >= 55.04 else 1.0
        fn = f(BEB, int(84 * s)); tw = d.textlength(lab, font=fn)
        y = y0 + 160
        lit_bar(d, 260, y, 260 + tw + 44, y + int(96 * s), VGOLD, b); d.text((282, y + 6), lab, font=fn, fill=A(INK, b))
        if GL: GL.rectangle([256, y - 4, 264 + tw + 44, y + int(96 * s) + 4], outline=A(VGOLD, b), width=12)
    if t >= 56.62:
        b = appear(t, 56.62, 0.16); px = lerp(260, 300, b); y = y0 + 282
        d.polygon([(px, y), (px + 34, y + 14), (px, y + 28), (px + 8, y + 14)], fill=A(VGOLD, b))
        txt(d, px + 50, y - 2, 'SENT TO YOUR DMs', MONO(28, 700), CREAM, b)
    txt(d, x1 - 20, y1 - 30, 'FOR RESEARCH & EDUCATIONAL PURPOSES ONLY', MONO(16, 500), MUTED, a * 0.8, anchor='ra')

# ---------------- captions ----------------
ACC_GOLD = {'vault', '250', '15', 'coaching', 'customized', 'nine', 'minutes', 'organized', 'searchable', 'expertise', 'protocols'}
ACC_RED = {'gambling', 'reddit', 'health', '200'}
def build_groups():
    G = []; cur = []
    for i, x in enumerate(WORDS):
        if cur:
            prev = WORDS[cur[-1]]
            if len(cur) >= 3 or x['s'] - prev['e'] > 0.28 or prev['w'][-1] in '.,?!' or any(prev['s'] < c <= x['s'] + 0.01 for c in CUTS): G.append(cur); cur = []
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
CAP_Y = 1378
def norm(w): return w.lower().strip('.,?!%$')
def captions(im, t):
    g = group_at(t)
    if not g: return
    d = ImageDraw.Draw(im, 'RGBA')
    ws = [WORDS[i]['w'].upper().rstrip(',.') for i in g]
    size = 124
    while True:
        fn = f(BEB, size); sp = d.textlength(' ', font=fn) + 14; wd = [d.textlength(w, font=fn) for w in ws]; tot = sum(wd) + sp * (len(ws) - 1)
        if tot <= 900: break
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
    for k, (w_, x_) in enumerate(zip(ws, xs)): sd.text((x_ + 4, 46), w_, font=fn, fill=(0, 0, 0, 220))
    cap.alpha_composite(shd.filter(ImageFilter.GaussianBlur(7)))
    aw = norm(WORDS[g[act]]['w'])
    bcol = VGOLD if aw in ACC_GOLD else RED
    lit_bar(cd, bx0, 40 + size * 0.16, bx1, 40 + size * 0.98, bcol)
    for k, (w_, x_) in enumerate(zip(ws, xs)):
        col = INK if (k == act and bcol == VGOLD) else CREAM
        cd.text((x_, 40), w_, font=fn, fill=col, stroke_width=0 if k == act else 3, stroke_fill=(0, 0, 0))
    if abs(s - 1) > 0.002:
        cap = cap.resize((int(W * s), int(300 * s)), Image.BICUBIC); ox = int((W - cap.width) / 2); oy = int(CAP_Y - 40 - (cap.height - 300) / 2)
    else: ox, oy = 0, CAP_Y - 40
    im.alpha_composite(cap, (ox, oy))

# ---------------- frame ----------------
_SCRIM = None
def scrim():
    global _SCRIM
    if _SCRIM is None:
        yy = np.arange(H); a = np.where(yy > 1250, np.clip((yy - 1250) / 260, 0, 1) * 120, 0)
        _SCRIM = Image.merge('RGBA', [Image.new('L', (W, H), c) for c in NAVY] + [Image.fromarray(np.repeat(a.astype(np.uint8)[:, None], W, 1))])
    return _SCRIM
def frame(src, t):
    global GL
    im = footage(src, t)
    if pip_p(t) < 1: im.alpha_composite(fade(scrim(), 1 - pip_p(t)))
    glow = Image.new('RGBA', (W, H), (0, 0, 0, 0)); GL = ImageDraw.Draw(glow, 'RGBA')
    for fn in (ov_feed, ov_t5, ov_gauge, ov_years, ov_matrix, ov_vault, ov_search, ov_donut, rail, price_graph, proof_deck, cta):
        fn(im, t)
    GL = None
    if glow.getbbox():
        sm = glow.resize((W // 4, H // 4), Image.BILINEAR)
        g1 = np.asarray(sm.filter(ImageFilter.GaussianBlur(3.5))).astype(np.float32) / 255; g2 = np.asarray(sm.filter(ImageFilter.GaussianBlur(10))).astype(np.float32) / 255
        prem = np.clip(g1[..., :3] * g1[..., 3:] * 2.3 + g2[..., :3] * g2[..., 3:] * 1.8, 0, 1)
        prem = np.asarray(Image.fromarray((prem * 255).astype(np.uint8)).resize((W, H), Image.BILINEAR)).astype(np.float32) / 255
        b = np.asarray(im.convert('RGB')).astype(np.float32) / 255
        im = Image.fromarray(((1 - (1 - b) * (1 - prem)) * 255).astype(np.uint8)).convert('RGBA')
    topic_band(im, t)
    text_hook(im, t)
    d = ImageDraw.Draw(im, 'RGBA'); d.rectangle([0, 0, 7, H], fill=GOLD)
    captions(im, t)
    return im.convert('RGB')

if __name__ == '__main__':
    mode = sys.argv[2]
    if mode == 'stills':
        import os; os.makedirs(S + 'qc', exist_ok=True)
        for tt in [float(x) for x in sys.argv[3:]]:
            subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', f'{tt:.4f}', '-i', S + 'assembled.mov', '-frames:v', '1', S + 'qc/_src.png'])
            frame(Image.open(S + 'qc/_src.png').convert('RGB'), tt).resize((540, 960)).save(S + f'qc/st_{tt:06.2f}.jpg', quality=85)
        sys.exit()
    n0, n1, out = int(sys.argv[3]), int(sys.argv[4]), sys.argv[5]
    dec = subprocess.Popen(['ffmpeg', '-v', 'error', '-i', S + 'assembled.mov', '-vf', f'select=between(n\\,{n0}\\,{n1 - 1})', '-vsync', '0', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], stdout=subprocess.PIPE)
    enc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-crf', '15', '-preset', 'medium', '-pix_fmt', 'yuv420p', out], stdin=subprocess.PIPE)
    for n in range(n0, n1):
        buf = dec.stdout.read(W * H * 3)
        if len(buf) < W * H * 3: print('short', n); break
        enc.stdin.write(frame(Image.frombuffer('RGB', (W, H), buf), n / FPS).tobytes())
    enc.stdin.close(); enc.wait(); dec.kill(); print('done', n0, n1)
