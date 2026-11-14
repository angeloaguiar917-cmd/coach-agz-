# Coach AGZ — "Body fat & E2 on TRT" Reel, 1080x1920 30fps.
# usage: python3 render.py <scratch> stills t1 t2 ...   |   python3 render.py <scratch> chunk n0 n1 out.mp4
import json, subprocess, sys, math
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops
S = sys.argv[1]; FD = S + '/fnt/'; SRC = S + '/src/raw.mov'
HERE = __file__.rsplit('/', 1)[0]
W, H, FPS = 1080, 1920, 30
DUR = 31.45; N = int(DUR * FPS)
WORDS = json.load(open(HERE + '/words.json'))
# ---- palette (BRAND.md + overlay accent palette) ----
GOLD = (201, 169, 110); CREAM = (244, 241, 234); NAVY = (14, 17, 23); PANEL = (24, 26, 34)
RED = (255, 34, 28); VGOLD = (255, 194, 26); CYAN = (0, 229, 255); GREEN = (30, 255, 110)
DEEP = (2, 3, 8); INK = (6, 8, 14); WHITE = (255, 255, 255); MUTED = (184, 184, 188); COARED = (210, 10, 20)
AMBER = (240, 160, 48); BLUE = (79, 163, 224)
BEB = 'bebas-neue-latin-400-normal.woff'; BC8 = 'barlow-condensed-latin-800-normal.woff'
BC7 = 'barlow-condensed-latin-700-normal.woff'; BC6 = 'barlow-condensed-latin-600-normal.woff'
DMB = 'dm-sans-latin-700-normal.woff'; DMR = 'dm-sans-latin-400-normal.woff'
MONO = 'JetBrainsMono-Bold.ttf'; MONOM = 'JetBrainsMono-Medium.ttf'
_fc = {}
def f(n, s):
    k = (n, int(s))
    if k not in _fc: _fc[k] = ImageFont.truetype(FD + n, int(s))
    return _fc[k]
def clamp(x, a=0., b=1.): return max(a, min(b, x))
def expo(x): x = clamp(x); return 1 if x >= 1 else 1 - 2 ** (-10 * x)
def ease_io(x): x = clamp(x); return 4 * x ** 3 if x < .5 else 1 - (-2 * x + 2) ** 3 / 2
def back(x):  # snap with tiny settle (not bouncy): fast in, 4% overshoot
    x = clamp(x); c = 1.2; return 1 + (c + 1) * (x - 1) ** 3 + c * (x - 1) ** 2
def lerp(a, b, t): return a + (b - a) * t
def A(c, a): return tuple(c[:3]) + (int(clamp(a) * 255),)
def win(t, t0, t1, fin=0.18, fout=0.16):  # 0..1 presence of an element
    if t < t0 or t > t1 + fout: return 0.
    return min(expo((t - t0) / fin), 1 - clamp((t - t1) / max(fout, 1e-6)))
GL = None  # glow layer draw (screen-blend bloom)

# ---------------- primitives ----------------
def lit_bar(d, x0, y0, x1, y1, col, a=1.0):
    h = max(1, int(y1 - y0))
    for i in range(h):
        k = i / h; c = tuple(int(min(255, v * (1.18 - 0.36 * k) + (40 if k < 0.12 else 0))) for v in col)
        d.line([(x0, y0 + i), (x1, y0 + i)], fill=c + (int(255 * a),))
def brackets(d, x0, y0, x1, y1, col, L=34, w=4):
    for (cx, cy, sx, sy) in [(x0, y0, 1, 1), (x1, y0, -1, 1), (x0, y1, 1, -1), (x1, y1, -1, -1)]:
        d.line([(cx, cy), (cx + sx * L, cy)], fill=col, width=w); d.line([(cx, cy), (cx, cy + sy * L)], fill=col, width=w)
def tag(d, x, y, label, col=RED, size=30, a=1.0, glow=True, txtcol=None):
    fn = f(MONO, size); tw = d.textlength(label, font=fn); h = size + 18
    lit_bar(d, x, y, x + tw + 26, y + h, col, a)
    tc = txtcol or (INK if col in (VGOLD, GREEN, CYAN) else WHITE)
    d.text((x + 13, y + 6), label, font=fn, fill=A(tc, a))
    if GL and glow: GL.rectangle([x - 3, y - 3, x + tw + 29, y + h + 3], outline=A(col, a), width=8)
    return x + tw + 26
def txt(d, x, y, s, font, col, a=1.0, anchor='la'):
    d.text((x, y), s, font=font, fill=A(col, a), anchor=anchor)
def frosted(im, box, dark=0.88, blur=14, radius=26, tint=DEEP):
    x0, y0, x1, y1 = [int(round(v)) for v in box]
    x0 = max(0, x0); y0 = max(0, y0); x1 = min(W, x1); y1 = min(H, y1)
    if x1 - x0 < 4 or y1 - y0 < 4: return
    reg = im.crop((x0, y0, x1, y1)).convert('RGB').filter(ImageFilter.GaussianBlur(blur))
    reg = Image.blend(reg, Image.new('RGB', reg.size, tint), dark)
    m = Image.new('L', reg.size, 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, reg.width - 1, reg.height - 1], radius=radius, fill=255)
    im.paste(reg, (x0, y0), m)
def panel(im, box, a, col=VGOLD, label=None, right=None, dark=0.88):
    """frosted inspection panel with gold frame + brackets; a = presence 0..1 (scale/blur in)"""
    if a <= 0: return None
    x0, y0, x1, y1 = box; cx, cy = (x0 + x1) / 2, (y0 + y1) / 2; s = lerp(1.04, 1, a)
    bx = (cx - (cx - x0) * s, cy - (cy - y0) * s, cx + (x1 - cx) * s, cy + (y1 - cy) * s)
    if a < 1:
        tmp = im.copy(); frosted(tmp, bx, dark); im.paste(Image.blend(im, tmp, a))
    else: frosted(im, bx, dark)
    d = ImageDraw.Draw(im, 'RGBA')
    d.rounded_rectangle(bx, radius=26, outline=A(col, 0.55 * a), width=2)
    brackets(d, bx[0], bx[1], bx[2], bx[3], A(col, a), 40, 6)
    if GL: brackets(GL, bx[0], bx[1], bx[2], bx[3], A(col, a), 40, 12)
    if label:
        d.ellipse([bx[0] + 26, bx[1] + 25, bx[0] + 40, bx[1] + 39], fill=A(RED, a))
        txt(d, bx[0] + 52, bx[1] + 18, label, f(MONO, 24), WHITE, a)
    if right:
        fr = f(MONO, 24); tw = d.textlength(right, font=fr); txt(d, bx[2] - 28 - tw, bx[1] + 18, right, fr, VGOLD, a)
    return bx
def arrow(d, x0, y0, x1, y1, col, w=5, a=1.0, L=20):
    d.line([(x0, y0), (x1, y1)], fill=A(col, a), width=w)
    ang = math.atan2(y1 - y0, x1 - x0)
    d.polygon([(x1, y1), (x1 - L * math.cos(ang - 0.45), y1 - L * math.sin(ang - 0.45)), (x1 - L * math.cos(ang + 0.45), y1 - L * math.sin(ang + 0.45))], fill=A(col, a))
def check(d, x, y, col, s=1.0, a=1.0, p=1.0):
    pts = [(x, y + 16 * s), (x + 10 * s, y + 28 * s), (x + 30 * s, y + 2 * s)]
    if p < 0.5: pts = [pts[0], (lerp(pts[0][0], pts[1][0], p * 2), lerp(pts[0][1], pts[1][1], p * 2))]
    else: pts = [pts[0], pts[1], (lerp(pts[1][0], pts[2][0], (p - .5) * 2), lerp(pts[1][1], pts[2][1], (p - .5) * 2))]
    d.line(pts, fill=A(col, a), width=int(6 * s), joint='curve')
    if GL: GL.line(pts, fill=A(col, a), width=int(12 * s))
def hexagon(d, cx, cy, r, col, a=1.0, width=5, fill=None, rot=0.):
    pts = [(cx + r * math.cos(math.pi / 3 * i + math.pi / 6 + rot), cy + r * math.sin(math.pi / 3 * i + math.pi / 6 + rot)) for i in range(6)]
    if fill: d.polygon(pts, fill=A(fill, a))
    d.line(pts + [pts[0]], fill=A(col, a), width=width, joint='curve')
    if GL: GL.line(pts + [pts[0]], fill=A(col, a * 0.9), width=width * 2)
    return pts

# ---------------- static assets ----------------
def make_bg():
    """brand background for the stacked layout: navy, warm glow top-right, fine noise"""
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    g = np.exp(-(((xx - 980) / 620) ** 2 + ((yy - 120) / 700) ** 2))
    base = np.array(NAVY, np.float32)[None, None, :] + g[..., None] * np.array([18, 14, 8], np.float32)
    rng = np.random.default_rng(3); base += rng.normal(0, 2.2, (H, W, 1))
    # faint gold scan rules every 6px in the panel band only
    return Image.fromarray(np.clip(base, 0, 255).astype(np.uint8))
def make_tissue(R=170):
    """adipose histology slide (Voronoi fat cells) for the microscope lens, 2R x 2R"""
    rng = np.random.default_rng(11); n = 26; D = 2 * R
    seeds = rng.uniform(-30, D + 30, (n, 2))
    yy, xx = np.mgrid[0:D, 0:D].astype(np.float32)
    d = np.stack([(xx - sx) ** 2 + (yy - sy) ** 2 for sx, sy in seeds], 0)
    srt = np.sort(d, 0); edge = (np.sqrt(srt[1]) - np.sqrt(srt[0])) < 5.0
    lab = np.argmin(d, 0)
    shade = rng.uniform(0.85, 1.0, n)[lab]
    img = np.zeros((D, D, 3), np.float32)
    inner = np.array([58, 40, 22], np.float32)  # lipid droplet: dark amber
    img[:] = inner[None, None, :] * shade[..., None]
    img[edge] = np.array([255, 196, 120], np.float32)  # membranes, warm gold
    im = Image.fromarray(img.astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.8))
    # membrane points for enzyme markers: pick edge pixels spread out
    ys, xs = np.nonzero(edge); pick = []
    order = rng.permutation(len(xs))
    for i in order:
        p = (xs[i], ys[i])
        if (p[0] - R) ** 2 + (p[1] - R) ** 2 > (R - 34) ** 2: continue
        if all((p[0] - q[0]) ** 2 + (p[1] - q[1]) ** 2 > 64 ** 2 for q in pick): pick.append(p)
        if len(pick) >= 7: break
    return im, pick
BG = None; TISSUE = None; TPTS = None; LOGO = None

# ---------------- timeline ----------------
HOOK_END = 4.95           # burned-in source title disappears at 4.93 s; hook covers it
BAND = (5.10, 15.70)      # topic band until the midpoint
STACK = (10.55, 15.45)    # stacked layout (graph scenes)
def layout_amt(t):
    if t < STACK[0] or t > STACK[1] + 0.32: return 0.
    return min(ease_io((t - STACK[0]) / 0.32), 1 - ease_io((t - STACK[1]) / 0.32))
def zoom_at(t):  # purposeful punch-ins (camera steady while graphics build)
    if 15.88 <= t < 21.0: return 1.08
    if 24.68 <= t: return 1.05
    return 1.0

# ---------------- footage ----------------
WIN = (86, 716, 994, 1356)
def footage(src, t):
    L = layout_amt(t); z = zoom_at(t)
    if L <= 0.0001:
        if z == 1.0: return src.copy()
        s = z; cs = (540, 880); cd = (540, 880)
    else:
        s = lerp(z, 0.84, L); cs = (540, lerp(880, 955, L)); cd = (540, lerp(880, 1036, L))
    big = src.resize((int(W * s), int(H * s)), Image.BICUBIC)
    ox = int(round(cd[0] - cs[0] * s)); oy = int(round(cd[1] - cs[1] * s))
    if L <= 0.0001:
        out = Image.new('RGB', (W, H)); out.paste(big, (ox, oy)); return out
    out = BG.copy()
    x0, y0, x1, y1 = [lerp(a, b, L) for a, b in zip((0, 0, W, H), WIN)]
    m = Image.new('L', (W, H), 0); ImageDraw.Draw(m).rounded_rectangle([x0, y0, x1, y1], radius=int(30 * L), fill=255)
    lay = Image.new('RGB', (W, H)); lay.paste(big, (ox, oy))
    out.paste(lay, (0, 0), m)
    d = ImageDraw.Draw(out, 'RGBA')
    d.rounded_rectangle([x0, y0, x1, y1], radius=int(30 * L), outline=A(GOLD, L * 0.9), width=3)
    if L > 0.5:
        a = (L - .5) * 2
        txt(d, x0 + 22, y1 - 46, 'REC', f(MONO, 22), RED, a); d.ellipse([x0 + 74, y1 - 40, x0 + 86, y1 - 28], fill=A(RED, a if int(t * 3) % 2 else a * .3))
    return out

# ---------------- scene 0: text hook (frame-0, premium) ----------------
HOOK_L1 = [('BODY FAT', VGOLD), (' raises your E2', WHITE)]
HOOK_L2 = [('at any TRT dose', WHITE)]
def hook(im0, t):
    if t > HOOK_END + 0.15: return
    a = 1 - clamp((t - HOOK_END) / 0.15)
    im = im0.copy() if a < 1 else im0
    s = lerp(1.0, 1.04, clamp(t / HOOK_END))  # one small move over the hold
    lay = Image.new('RGBA', (W, 340), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    fn = f(BC8, 112)
    while max(d.textlength(''.join(x for x, _ in L_), font=fn) for L_ in (HOOK_L1, HOOK_L2)) > 900: fn = f(BC8, fn.size - 2)
    for row, (y, segs) in enumerate([(30, HOOK_L1), (156, HOOK_L2)]):
        tw = sum(d.textlength(s_, font=fn) for s_, _ in segs); x = (W - tw) / 2
        for s_, c in segs:
            d.text((x + 4, y + 5), s_, font=fn, fill=(0, 0, 0, 160)); d.text((x, y), s_, font=fn, fill=c + (255,)); x += d.textlength(s_, font=fn)
    if s != 1: lay = lay.resize((int(W * s), int(340 * s)), Image.BICUBIC)
    ox = int((W - lay.width) / 2); oy = int(250 - (lay.height - 340) / 2)
    # plate (covers the burned-in source title at y 405-475)
    pb = (44, 246, 1036, 590)
    frosted(im, pb, 0.9, 16, 30, NAVY)
    d = ImageDraw.Draw(im, 'RGBA')
    d.rounded_rectangle(pb, radius=30, outline=A(GOLD, 0.6), width=2)
    d.rectangle([pb[0], pb[1] + 30, pb[0] + 7, pb[3] - 30], fill=A(VGOLD, 1))
    im.alpha_composite(lay, (ox, oy))
    if a < 1: im0.paste(Image.blend(im0, im, a))

def band(im, t):
    a = win(t, BAND[0], BAND[1], 0.15, 0.15)
    if a <= 0: return
    d = ImageDraw.Draw(im, 'RGBA')
    d.rectangle([8, 212, W, 292], fill=A(NAVY, 0.9 * a))
    d.line([(52, 252), (88, 252)], fill=A(GOLD, a), width=4)
    x = 104; fn = f(BC8, 56)
    for s_, c in [('BODY FAT', VGOLD), (' raises E2 on TRT', CREAM)]:
        txt(d, x, 222, s_, fn, c, a); x += d.textlength(s_, font=fn)
    txt(d, W - 40, 238, '@coach.agz', f(MONO, 24), GOLD, a, 'ra')

# ---------------- scene 1: enzyme scan (side widget) ----------------
def enzyme3d(d, cx, cy, r, t, col, a):
    # wireframe hexagonal ring rotating about the vertical axis (two offset rings + struts)
    ang = t * 1.6
    def proj(i, z0):
        th = math.pi / 3 * i
        x = r * math.cos(th); z = r * math.sin(th)
        xr = x * math.cos(ang) - z * math.sin(ang); zr = x * math.sin(ang) + z * math.cos(ang)
        return (cx + xr, cy + z0 + zr * 0.32)
    top = [proj(i, -r * 0.34) for i in range(6)]; bot = [proj(i, r * 0.34) for i in range(6)]
    for ring in (top, bot):
        d.line(ring + [ring[0]], fill=A(col, a), width=4)
        if GL: GL.line(ring + [ring[0]], fill=A(col, a), width=9)
    for p, q in zip(top, bot): d.line([p, q], fill=A(col, a * 0.7), width=3)
    for p in top + bot: d.ellipse([p[0] - 6, p[1] - 6, p[0] + 6, p[1] + 6], fill=A(WHITE, a))
def scene_enzyme(im, t):
    T0, T1 = 3.82, 6.40
    a = win(t, T0, T1, 0.16, 0.0)
    if t > T1 or a <= 0: return
    box = (28, 612, 290, 1000)
    bx = panel(im, box, a, CYAN)
    d = ImageDraw.Draw(im, 'RGBA')
    cx, cy = (box[0] + box[2]) / 2, 790
    enzyme3d(d, cx, cy, 86, t, CYAN, a)
    # scan line sweeping down the widget
    sy = box[1] + 40 + ((t - T0) * 260) % (box[3] - box[1] - 80)
    d.line([(box[0] + 14, sy), (box[2] - 14, sy)], fill=A(CYAN, 0.8 * a), width=2)
    if GL: GL.line([(box[0] + 14, sy), (box[2] - 14, sy)], fill=A(CYAN, 0.6 * a), width=6)
    txt(d, box[0] + 24, box[1] + 20, 'SCAN', f(MONO, 22), CYAN, a)
    if t >= 4.44:
        p = expo((t - 4.44) / 0.12); txt(d, cx, box[1] + 64, 'ENZYME ×1', f(MONO, 26), WHITE, p * a, 'ma')
    if t >= 5.62:
        p = expo((t - 5.62) / 0.14); y = lerp(930, 900, p)
        fn = f(BEB, 56); tw = d.textlength('AROMATASE', font=fn)
        d.rectangle([cx - tw / 2 - 12, y - 4, cx + tw / 2 + 12, y + 58], fill=A(VGOLD, p))
        if GL: GL.rectangle([cx - tw / 2 - 14, y - 6, cx + tw / 2 + 14, y + 60], outline=A(VGOLD, p), width=8)
        txt(d, cx, y + 2, 'AROMATASE', fn, INK, p, 'ma')

# ---------------- scene 2: microscope lens (adipose tissue) ----------------
LENS_C = (800, 540); LENS_R = 170
def scene_lens(im, t):
    T0, T1 = 6.40, 8.52
    if t < T0 or t > T1 + 0.3: return
    # handoff in: enzyme flies from the side widget into the lens
    d = ImageDraw.Draw(im, 'RGBA')
    if t < 6.62:
        p = ease_io((t - T0) / 0.22)
        x = lerp(159, LENS_C[0], p); y = lerp(790, LENS_C[1], p); r = lerp(86, 22, p)
        hexagon(d, x, y, r, CYAN, 1, 5)
        return
    p = expo((t - 6.62) / 0.22)                 # lens irises open
    # handoff out: lens shrinks into the aromatase hex of the flow diagram
    q = ease_io((t - T1) / 0.28) if t > T1 else 0
    cx = lerp(LENS_C[0], 540, q); cy = lerp(LENS_C[1], 450, q); R = LENS_R * p * lerp(1, 0.42, q)
    if R < 4: return
    D = int(2 * R)
    tis = TISSUE.resize((D, D), Image.BILINEAR)
    # subtle focus pull
    fb = max(0., 1 - (t - 6.62) / 0.35) * 6
    if fb > 0.2: tis = tis.filter(ImageFilter.GaussianBlur(fb))
    m = Image.new('L', (D, D), 0); ImageDraw.Draw(m).ellipse([0, 0, D - 1, D - 1], fill=255)
    if q > 0: m = m.point(lambda v: int(v * (1 - q)))
    im.paste(tis, (int(cx - R), int(cy - R)), m)
    d = ImageDraw.Draw(im, 'RGBA'); al = 1 - q
    # vignette ring + reticle ticks
    d.ellipse([cx - R, cy - R, cx + R, cy + R], outline=A(VGOLD, al), width=6)
    if GL: GL.ellipse([cx - R, cy - R, cx + R, cy + R], outline=A(VGOLD, al), width=12)
    for k in range(36):
        th = k * math.pi / 18; r0 = R + 8; r1 = R + (22 if k % 9 == 0 else 14)
        d.line([(cx + r0 * math.cos(th), cy + r0 * math.sin(th)), (cx + r1 * math.cos(th), cy + r1 * math.sin(th))], fill=A(VGOLD, al * 0.8), width=3)
    d.line([(cx - R * 0.15, cy), (cx + R * 0.15, cy)], fill=A(WHITE, 0.35 * al), width=1); d.line([(cx, cy - R * 0.15), (cx, cy + R * 0.15)], fill=A(WHITE, 0.35 * al), width=1)
    # aromatase markers light up in the membranes on "lives"
    sc = R / LENS_R
    for i, (px, py) in enumerate(TPTS):
        tt = 6.96 + i * 0.09
        if t < tt: continue
        pa = expo((t - tt) / 0.12) * al
        x = cx - R + px * sc; y = cy - R + py * sc
        hexagon(d, x, y, 13 * sc, CYAN, pa, 3, fill=(0, 60, 80))
    if q == 0:
        if t >= 7.54:
            pa = expo((t - 7.54) / 0.14); tag(d, cx - R - 30, cy + R + 22, 'ADIPOSE TISSUE', VGOLD, 28, pa)
        txt(d, cx + R - 6, cy - R - 10, '40×', f(MONO, 24), VGOLD, p, 'rb')
        # leader line from lens to label "AROMATASE SITES"
        if t >= 7.1:
            pa = expo((t - 7.1) / 0.14)
            x0, y0 = cx - R * 0.7, cy - R * 0.55; x1 = x0 - 120 * pa
            d.line([(x0, y0), (x0 - 40, y0 - 40), (x1 - 40, y0 - 40)], fill=A(CYAN, pa), width=3)
            txt(d, x1 - 46, y0 - 74, 'AROMATASE', f(MONO, 24), CYAN, pa, 'ra')
            txt(d, x1 - 46, y0 - 46, 'LIVES HERE', f(MONO, 24), WHITE, pa, 'ra')

# ---------------- scene 3: conversion flow (T -> aromatase -> E2) ----------------
def node(d, x0, y0, x1, y1, title, sub, col, a=1.0, lit=1.0):
    c = tuple(int(lerp(60, v, lit)) for v in col)
    d.rounded_rectangle([x0, y0, x1, y1], radius=16, fill=A((10, 14, 24), 0.95 * a), outline=A(c, a), width=4)
    if GL and lit > 0.5: GL.rounded_rectangle([x0, y0, x1, y1], radius=16, outline=A(col, a * lit), width=9)
    txt(d, (x0 + x1) / 2, y0 + 14, title, f(BEB, 78), WHITE if lit > .5 else (120, 120, 128), a, 'ma')
    txt(d, (x0 + x1) / 2, y1 - 40, sub, f(MONO, 22), c, a, 'ma')
def scene_flow(im, t):
    T0, T1 = 8.52, 10.48
    if t < T0 or t > T1 + 0.12: return
    a = win(t, T0, T1, 0.2, 0.12)
    box = (40, 316, 1040, 600)
    panel(im, box, a, VGOLD, 'CONVERSION', 'T → E2')
    d = ImageDraw.Draw(im, 'RGBA')
    lt = expo((t - 8.92) / 0.14); le = expo((t - 9.80) / 0.14)
    node(d, 80, 384, 330, 560, 'T', 'TESTOSTERONE', CYAN, a, lt)
    node(d, 750, 384, 1000, 560, 'E2', 'ESTRADIOL', RED, a, le)
    cx, cy = 540, 470
    hexagon(d, cx, cy, 74, VGOLD, a, 6, fill=(30, 22, 6), rot=t * 0.8)
    txt(d, cx, cy - 16, 'AROM.', f(MONO, 26), VGOLD, a, 'ma')
    arrow(d, 340, cy, 452, cy, CYAN, 5, a * lt); arrow(d, 628, cy, 740, cy, RED, 5, a * le)
    # particles: cyan T in, red E2 out once conversion is spoken
    for k in range(5):
        if lt > 0:
            p = (t * 1.1 + k / 5) % 1; x = lerp(340, 452, p); fa = a * lt * min(1, p * 5, (1 - p) * 5)
            d.ellipse([x - 8, cy - 8, x + 8, cy + 8], fill=A(CYAN, fa))
            if GL: GL.ellipse([x - 14, cy - 14, x + 14, cy + 14], fill=A(CYAN, fa))
        if le > 0:
            p = (t * 1.1 + k / 5 + .1) % 1; x = lerp(628, 740, p); fa = a * le * min(1, p * 5, (1 - p) * 5)
            d.ellipse([x - 8, cy - 8, x + 8, cy + 8], fill=A(RED, fa))
            if GL: GL.ellipse([x - 14, cy - 14, x + 14, cy + 14], fill=A(RED, fa))

# ---------------- scene 4: line graph (stacked layout) ----------------
GP = (40, 312, 1040, 700)   # graph panel
def curve_y(u):  # illustrative: conversion climbs with body fat
    return 0.12 + 0.80 * (u ** 1.7)
def scene_graph(im, t):
    T0, T1 = 10.66, 13.12
    if t < T0 - 0.05 or t > T1 + 0.25: return
    a = win(t, T0, 13.06, 0.25, 0.10)
    if a <= 0: return
    panel(im, GP, a, VGOLD, 'BODY FAT vs CONVERSION', 'ILLUSTRATIVE')
    d = ImageDraw.Draw(im, 'RGBA')
    ax0, ay0, ax1, ay1 = 150, 384, 990, 620   # plot area
    pa = expo((t - 10.75) / 0.3) * a
    d.line([(ax0, ay1), (ax0 + (ax1 - ax0) * pa, ay1)], fill=A(CREAM, 0.9 * a), width=3)
    d.line([(ax0, ay1), (ax0, ay1 - (ay1 - ay0) * pa)], fill=A(CREAM, 0.9 * a), width=3)
    for k in range(1, 4):  # gridlines
        y = ay1 - (ay1 - ay0) * k / 4; d.line([(ax0 + 4, y), (ax1, y)], fill=A((90, 94, 110), 0.5 * pa), width=1)
    txt(d, ax0, ay1 + 14, 'LOWER', f(MONO, 22), MUTED, pa); txt(d, ax1, ay1 + 14, 'HIGHER', f(MONO, 22), MUTED, pa, 'ra')
    txt(d, (ax0 + ax1) / 2, ay1 + 14, 'BODY FAT  →', f(MONO, 24), VGOLD, pa, 'ma')
    # rotated y label
    yl = Image.new('RGBA', (300, 34), (0, 0, 0, 0)); ImageDraw.Draw(yl).text((150, 0), 'T→E2 CONVERSION', font=f(MONO, 22), fill=A(CYAN, pa), anchor='ma')
    im.alpha_composite(yl.rotate(90, expand=True), (ax0 - 52, int((ay0 + ay1) / 2 - 150)))
    d = ImageDraw.Draw(im, 'RGBA')
    # curve draws with "higher body fat increases conversion rate" (10.8 -> 12.9)
    prog = ease_io((t - 10.95) / 1.95)
    if prog > 0:
        pts = []
        for i in range(int(80 * prog) + 1):
            u = i / 80; pts.append((ax0 + (ax1 - ax0) * u, ay1 - (ay1 - ay0) * curve_y(u)))
        # area fill under curve
        if len(pts) > 1:
            poly = pts + [(pts[-1][0], ay1), (ax0, ay1)]
            d.polygon(poly, fill=A(RED, 0.16 * a))
            d.line(pts, fill=A(RED, a), width=7, joint='curve')
            if GL: GL.line(pts, fill=A(RED, a), width=14)
        mx, my = pts[-1]
        d.ellipse([mx - 13, my - 13, mx + 13, my + 13], fill=A(WHITE, a), outline=A(RED, a), width=5)
        if t > 12.0:
            q = expo((t - 12.06) / 0.14)
            tag(d, mx - 250, my - 6, 'RATE ▲', RED, 30, q * a)
    # flat reference: what you'd expect if only the dose mattered
    if t > 11.4:
        q = expo((t - 11.4) / 0.3) * a; yy = ay1 - (ay1 - ay0) * 0.12
        for xx in range(ax0, int(ax0 + (ax1 - ax0) * q), 26): d.line([(xx, yy), (xx + 13, yy)], fill=A(CYAN, 0.75 * a), width=3)
        txt(d, ax1 - 8, yy - 34, 'LEAN BASELINE', f(MONO, 20), CYAN, q, 'ra')

# ---------------- scene 5: bar comparison, same dose ----------------
def syringe(d, x, y, col, a, s=1.0):
    d.rounded_rectangle([x, y, x + 110 * s, y + 30 * s], radius=6, outline=A(col, a), width=3)
    d.rectangle([x + 4, y + 4, x + 70 * s, y + 26 * s], fill=A(col, 0.55 * a))
    d.line([(x + 110 * s, y + 15 * s), (x + 150 * s, y + 15 * s)], fill=A(col, a), width=3)
    d.line([(x - 22 * s, y + 15 * s), (x, y + 15 * s)], fill=A(col, a), width=5); d.line([(x - 22 * s, y + 2), (x - 22 * s, y + 28 * s)], fill=A(col, a), width=5)
def scene_bars(im, t):
    T0, T1 = 13.16, 15.40
    if t < T0 or t > T1 + 0.2: return
    a = win(t, T0, T1, 0.22, 0.18)
    panel(im, GP, a, VGOLD, 'SAME DOSE TEST', 'E2 OUTPUT')
    d = ImageDraw.Draw(im, 'RGBA')
    base = 640; cols = [(300, 'LEAN', CYAN, 0.36), (780, 'HIGHER BODY FAT', RED, 0.92)]
    d.line([(90, base), (990, base)], fill=A(CREAM, 0.8 * a), width=3)
    for i, (cx, lab, col, hgt) in enumerate(cols):
        txt(d, cx, base + 14, lab, f(MONO, 24), WHITE, a, 'ma')
        # identical dose chips land on "independent" / "dose"
        ds = expo((t - (13.48 + i * 0.12)) / 0.16)
        if ds > 0:
            syringe(d, cx - 200, 376, VGOLD, ds * a, 0.8)
            txt(d, cx - 60, 372, 'SAME DOSE', f(MONO, 24), VGOLD, ds * a)
            check(d, cx + 104, 368, GREEN, 0.9, ds * a, ds)
        # E2 bars grow after the dose is shown equal
        g = ease_io((t - (14.2 + i * 0.25)) / 0.5)
        if g > 0:
            top = base - (base - 430) * hgt * g; w2 = 120
            if top > base - 6: continue
            lit_bar(d, cx - w2, top, cx + w2, base - 2, col, a)
            if GL: GL.rectangle([cx - w2, top, cx + w2, base - 2], outline=A(col, a), width=8)
            if g > 0.9:
                txt(d, cx, top + 10, 'E2' + (' HIGH' if i else ''), f(BEB, 52), INK if i == 0 else WHITE, a, 'ma')
    if t > 14.9:
        q = expo((t - 14.9) / 0.14)
        brackets(d, 640, 410, 920, 650, A(RED, q * a), 30, 6)

# ---------------- scene 6: E2 gauge + symptom stack ----------------
def gauge(d, cx, cy, R, val, a):
    # semicircle dial: blue low -> green dialed-in -> amber -> red high (data spectrum)
    segs = [(180, 225, BLUE), (225, 290, GREEN), (290, 325, AMBER), (325, 360, RED)]
    for s0, s1, c in segs:
        d.arc([cx - R, cy - R, cx + R, cy + R], s0 + 1, s1 - 1, fill=A(c, a), width=22)
        if GL and c == RED: GL.arc([cx - R, cy - R, cx + R, cy + R], s0, s1, fill=A(c, a), width=34)
    ang = math.radians(180 + 180 * val)
    x1 = cx + (R - 30) * math.cos(ang); y1 = cy + (R - 30) * math.sin(ang)
    d.line([(cx, cy), (x1, y1)], fill=A(WHITE, a), width=7)
    if GL: GL.line([(cx, cy), (x1, y1)], fill=A(WHITE, a * .6), width=10)
    d.ellipse([cx - 16, cy - 16, cx + 16, cy + 16], fill=A(WHITE, a))
    txt(d, cx - R, cy + 18, 'LOW', f(MONO, 20), BLUE, a); txt(d, cx + R, cy + 18, 'HIGH', f(MONO, 20), RED, a, 'ra')
def icon(d, kind, x, y, a):
    c = WHITE
    if kind == 'drop':
        d.polygon([(x + 30, y + 4), (x + 12, y + 32), (x + 48, y + 32)], fill=A(c, a)); d.ellipse([x + 11, y + 20, x + 49, y + 56], fill=A(c, a))
    elif kind == 'target':
        for r, w_ in [(26, 4), (15, 4)]: d.ellipse([x + 30 - r, y + 30 - r, x + 30 + r, y + 30 + r], outline=A(c, a), width=w_)
        d.ellipse([x + 25, y + 25, x + 35, y + 35], fill=A(c, a))
    elif kind == 'wave':
        pts = [(x + 2, y + 30), (x + 12, y + 30), (x + 18, y + 8), (x + 26, y + 52), (x + 34, y + 14), (x + 42, y + 44), (x + 48, y + 30), (x + 58, y + 30)]
        d.line(pts, fill=A(c, a), width=5, joint='curve')
SYM = [(17.80, 'drop', 'WATER RETENTION'), (18.80, 'target', 'SENSITIVE NIPPLES'), (19.64, 'wave', 'EMOTIONAL VOLATILITY')]
def scene_symptoms(im, t):
    T0, T1 = 15.90, 20.95
    if t < T0 or t > T1 + 0.2: return
    a = win(t, T0, T1, 0.18, 0.18)
    gb = (650, 290, 1044, 600)
    panel(im, gb, a, VGOLD, 'E2', 'LEVEL')
    d = ImageDraw.Draw(im, 'RGBA')
    v = lerp(0.42, 0.93, ease_io((t - 16.45) / 0.6))
    v += 0.012 * math.sin(t * 23) * clamp((t - 17.05) * 5)  # needle tremor in the red
    gauge(d, (gb[0] + gb[2]) / 2, 530, 140, v, a)
    if t > 17.0: tag(d, gb[0] + 24, 548 - 0, 'ELEVATED', RED, 22, expo((t - 17.0) / .14) * a)
    for i, (tt, ic, lab) in enumerate(SYM):
        if t < tt - 0.02: continue
        p = expo((t - tt) / 0.16); y = 300 + i * 104; x = lerp(-420, 40, p)
        frosted(im, (x, y, x + 580, y + 88), 0.9, 10, 14)
        d = ImageDraw.Draw(im, 'RGBA')
        lit_bar(d, x, y, x + 88, y + 88, RED, a)
        if GL: GL.rectangle([x, y, x + 88, y + 88], outline=A(RED, a), width=8)
        icon(d, ic, x + 14, y + 14, a)
        txt(d, x + 108, y + 14, lab, f(BC8, 54), WHITE, a)
        brackets(d, x - 6, y - 6, x + 586, y + 94, A(RED, a * expo((t - tt - 0.1) / 0.12)), 22, 4)

# ---------------- scene 7: lab report ----------------
def scene_labs(im, t):
    T0, T1 = 21.00, 24.45
    if t < T0 or t > T1 + 0.3: return
    pin = expo((t - T0) / 0.28); pout = ease_io((t - T1) / 0.28)
    w, h = 880, 470
    doc = Image.new('RGBA', (w, h), (232, 230, 224, 255)); d = ImageDraw.Draw(doc)
    rng = np.random.default_rng(5)
    d.rectangle([0, 0, w, 64], fill=COARED); d.text((24, 14), 'LAB REPORT · HORMONE PANEL', font=f(MONO, 30), fill=WHITE)
    d.text((w - 24, 20), 'PG 1/1', font=f(MONO, 22), fill=(255, 220, 220), anchor='ra')
    d.text((24, 80), 'TEST', font=f(MONO, 20), fill=(110, 110, 120)); d.text((450, 80), 'RESULT vs REFERENCE RANGE', font=f(MONO, 20), fill=(110, 110, 120))
    rows = [('Testosterone, Total', 'IN RANGE', 0.58, (20, 130, 60)), ('Estradiol, Sensitive', 'HIGH', 0.93, (210, 10, 20))]
    for i, (nm, fl, mv, fc) in enumerate(rows):
        y = 120 + i * 112
        d.text((24, y + 6), nm, font=f(DMB, 38), fill=INK); d.text((24, y + 52), 'LC/MS-MS' if i else 'Immunoassay', font=f(MONO, 20), fill=(120, 120, 130))
        # range bar: grey track, green reference band, marker
        bx0, bx1, by = 450, 680, y + 34
        d.rounded_rectangle([bx0, by, bx1, by + 18], radius=9, fill=(205, 203, 198))
        d.rounded_rectangle([bx0 + 70, by, bx0 + 200, by + 18], radius=9, fill=(150, 205, 165))
        if t > 21.2 + i * 0.2:
            mp = ease_io((t - 21.2 - i * 0.2) / 0.4); mx = lerp(bx0, bx0 + (bx1 - bx0) * mv, mp)
            d.polygon([(mx - 11, by - 14), (mx + 11, by - 14), (mx, by + 2)], fill=fc)
            d.line([(mx, by), (mx, by + 18)], fill=fc, width=4)
        d.text((w - 24, y + 22), fl, font=f(DMB, 34), fill=fc, anchor='ra')
        d.line([(16, y + 98), (w - 16, y + 98)], fill=(210, 210, 214), width=2)
    # footer: order of operations
    fy = 360
    d.text((24, fy), 'ORDER', font=f(MONO, 20), fill=(110, 110, 120))
    s1 = expo((t - 22.38) / 0.14); s2 = expo((t - 23.42) / 0.14)
    d.rounded_rectangle([24, fy + 32, 300, fy + 92], radius=10, fill=(20, 130, 60) if s1 > .5 else (200, 200, 205))
    d.text((44, fy + 42), '1  LABS', font=f(BEB, 46), fill=WHITE)
    if s1 > .5: d.line([(236, fy + 62), (250, fy + 76), (276, fy + 46)], fill=WHITE, width=6)
    d.line([(318, fy + 62), (410, fy + 62)], fill=(80, 80, 90), width=4); d.polygon([(410, fy + 50), (428, fy + 62), (410, fy + 74)], fill=(80, 80, 90))
    d.rounded_rectangle([446, fy + 32, w - 24, fy + 92], radius=10, outline=INK, width=3, fill=(232, 230, 224) if s2 < .5 else (40, 44, 56))
    d.text((466, fy + 42), '2  PROTOCOL CHANGE', font=f(BEB, 46), fill=INK if s2 < .5 else (255, 194, 26))
    # paper texture + slight desaturation look
    noise = Image.fromarray(rng.integers(0, 18, (h, w), dtype=np.uint8), 'L')
    doc = Image.composite(Image.new('RGBA', (w, h), (0, 0, 0, 255)), doc, noise.point(lambda v: v))
    dd = ImageDraw.Draw(doc, 'RGBA')
    # red detection on E2 row + CONFIRMED stamp on "confirm"
    if t > 21.74:
        q = expo((t - 21.74) / 0.12)
        brackets(dd, 10, 224, w - 10, 334, (230, 20, 20, int(255 * q)), 30, 6)
    stamp = None
    if t > 21.76:
        q = clamp((t - 21.76) / 0.10); s = lerp(1.6, 1.0, expo(q))
        st = Image.new('RGBA', (360, 110), (0, 0, 0, 0)); sd = ImageDraw.Draw(st)
        sd.rounded_rectangle([4, 4, 356, 106], radius=10, outline=(230, 20, 20, 235), width=7)
        sd.text((180, 16), 'CONFIRMED', font=f(BEB, 84), fill=(230, 20, 20, 235), anchor='ma')
        st = st.rotate(8, expand=True, resample=Image.BICUBIC)
        st = st.resize((int(st.width * s), int(st.height * s)), Image.BICUBIC)
        st.putalpha(st.split()[3].point(lambda v: int(v * clamp(q * 3))))
        doc.alpha_composite(st, (int(300 - st.width / 2), int(300 - st.height / 2)))
    # place: drops in with focus pull, slight tilt, exits upward
    ang = lerp(-6, -2, pin)
    y = lerp(-520, 300, pin) - 900 * pout
    sh = Image.new('RGBA', (w + 80, h + 80), (0, 0, 0, 0)); ImageDraw.Draw(sh).rectangle([40, 52, w + 40, h + 52], fill=(0, 0, 0, 150))
    sh = sh.filter(ImageFilter.GaussianBlur(16))
    blur = (1 - pin) * 8
    if blur > 0.3: doc = doc.filter(ImageFilter.GaussianBlur(blur))
    sh.alpha_composite(doc, (40, 40))
    sh = sh.rotate(ang, expand=True, resample=Image.BICUBIC)
    im.alpha_composite(sh, (int(540 - sh.width / 2), int(y - 40)))

# ---------------- scene 8: freebie + comment CTA ----------------
def scene_cta(im, t):
    T0 = 24.68
    if t < T0: return
    if t < 27.84:
        q = clamp((t - 27.72) / 0.12)
        tmp = im.copy(); card_cta(tmp, t, T0)
        im.paste(Image.blend(im, tmp, 1 - q) if q > 0 else tmp)
    if t >= 27.75: pill_cta(im, t)
def card_cta(im, t, T0):
    if True:
        pin = back((t - T0) / 0.32); q = 0
        box = (lerp(150, 120, q), lerp(290, 360, q), lerp(930, 960, q), lerp(760, 520, q))
        x0, y0, x1, y1 = box; yoff = lerp(120, 0, clamp(pin))
        y0 += yoff; y1 += yoff
        frosted(im, (x0, y0, x1, y1), 0.9, 14, 24, NAVY)
        d = ImageDraw.Draw(im, 'RGBA'); al = clamp(pin) * (1 - q)
        d.rounded_rectangle([x0, y0, x1, y1], radius=24, outline=A(GOLD, 0.8 * clamp(pin)), width=3)
        d.rectangle([x0, y0 + 24, x0 + 7, y1 - 24], fill=A(VGOLD, clamp(pin)))
        txt(d, x0 + 40, y0 + 28, '——  FREE RESOURCE', f(MONO, 24), VGOLD, al)
        txt(d, x0 + 40, y0 + 64, 'E2 MANAGEMENT', f(BEB, 96), CREAM, al)
        txt(d, x0 + 40 + d.textlength('E2 MANAGEMENT ', font=f(BEB, 96)), y0 + 64, 'CHECKLIST', f(BEB, 96), VGOLD, al)
        for k in range(4):
            tt = 25.3 + k * 0.28; yy = y0 + 196 + k * 64
            if t < tt: continue
            p = expo((t - tt) / 0.14)
            d.rounded_rectangle([x0 + 40, yy, x0 + 80, yy + 40], radius=6, outline=A(CREAM, al * p), width=3)
            check(d, x0 + 46, yy + 2, GREEN, 0.9, al * p, p)
            for j, wl in enumerate([0.62, 0.45, 0.70, 0.52][k:k + 1]):
                d.rounded_rectangle([x0 + 104, yy + 12, x0 + 104 + (x1 - x0 - 160) * wl * p, yy + 28], radius=8, fill=A((90, 94, 110), al))
        if t > 26.88:
            p = clamp((t - 26.88) / 0.1); s = lerp(1.7, 1.0, expo(p))
            st = Image.new('RGBA', (300, 120), (0, 0, 0, 0)); sd = ImageDraw.Draw(st)
            lit_bar(sd, 0, 0, 300, 120, RED); sd.text((150, 10), 'FREE', font=f(BEB, 110), fill=WHITE, anchor='ma')
            st = st.rotate(-9, expand=True, resample=Image.BICUBIC); st = st.resize((int(st.width * s), int(st.height * s)), Image.BICUBIC)
            st.putalpha(st.split()[3].point(lambda v: int(v * clamp(p * 3) * (1 - q))))
            im.alpha_composite(st, (int(x1 - 170 - st.width / 2), int(y1 - 110 - st.height / 2)))
            if GL: GL.rectangle([x1 - 320, y1 - 180, x1 - 20, y1 - 40], outline=A(RED, (1 - q) * clamp(p * 3)), width=10)
def pill_cta(im, t):
    # comment pill lands on "comment" (27.82)
    p = expo((t - 27.80) / 0.16); s = lerp(1.12, 1.0, p)
    d = ImageDraw.Draw(im, 'RGBA')
    label = 'COMMENT  "E2"'; fn = f(BEB, int(118 * s)); tw = d.textlength(label, font=fn)
    bw = tw + 150; x0 = 540 - bw / 2; y0 = 370 - 8 * (1 - p); hh = 140 * s
    if GL: GL.rectangle([x0 - 6, y0 - 6, x0 + bw + 6, y0 + hh + 6], outline=A(VGOLD, p), width=14)
    lit_bar(d, x0, y0, x0 + bw, y0 + hh, VGOLD, p)
    # speech-bubble icon
    bx, by = x0 + 34, y0 + hh / 2 - 34
    d.rounded_rectangle([bx, by, bx + 76, by + 56], radius=14, fill=A(INK, p)); d.polygon([(bx + 14, by + 50), (bx + 34, by + 50), (bx + 10, by + 74)], fill=A(INK, p))
    for k in range(3): d.ellipse([bx + 16 + k * 18, by + 22, bx + 26 + k * 18, by + 32], fill=A(VGOLD, p))
    txt(d, x0 + 130, y0 + 12 * s, label, fn, INK, p)
    # "below" chevrons, snapping down in sequence
    if 28.8 < t:
        for k in range(3):
            q = expo((t - 28.84 - k * 0.07) / 0.12); yy = 1170 + k * 40
            if GL: GL.line([(950, yy), (985, yy + 28), (1020, yy)], fill=A(VGOLD, q * (0.5 + 0.25 * k)), width=14)
            d.line([(950, yy), (985, yy + 28), (1020, yy)], fill=A(VGOLD, q * (0.5 + 0.25 * k)), width=8)
    # end lockup
    if t > 30.6:
        q = expo((t - 30.62) / 0.2)
        frosted(im, (300, y0 + hh + 10, 780, y0 + hh + 130), 0.9 * q, 10, 18, NAVY)
        if LOGO is not None:
            lg = LOGO.resize((96, 96)); m = Image.new('L', (96, 96), 0); ImageDraw.Draw(m).ellipse([0, 0, 95, 95], fill=int(255 * q))
            im.paste(lg, (int(540 - 48 - 150), int(y0 + hh + 22)), m)
        d = ImageDraw.Draw(im, 'RGBA')
        txt(d, 540 - 80, y0 + hh + 30, 'COACH AGZ', f(BEB, 56), GOLD, q); txt(d, 540 - 80, y0 + hh + 84, '@coach.agz', f(MONO, 24), CREAM, q)

# ---------------- captions (plate covers the burned-in source captions) ----------------
GOLDW = {'aromatase', 'adipose', 'testosterone', 'estradiol', 'e2', 'labs', 'free', 'checklist', 'enzyme'}
REDW = {'estrogen', 'fat', 'retention', 'nipples', 'volatility', 'increases'}
def cw(i): return WORDS[i]['w'].strip('.,?!').lower()
def build_groups():
    G = []; cur = []
    for i, x in enumerate(WORDS):
        if cur:
            prev = WORDS[cur[-1]]; chars = sum(len(WORDS[j]['w']) for j in cur) + len(x['w'])
            if len(cur) >= 3 or chars > 19 or x['s'] - prev['e'] > 0.28 or prev['w'][-1] in '.,?!': G.append(cur); cur = []
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
    if t > WORDS[lo[-1]]['e'] + 0.5: return None
    return lo
PLATE = (64, 1368, 1016, 1540)
def captions(im, t):
    frosted(im, PLATE, 0.86, 12, 22, NAVY)
    d = ImageDraw.Draw(im, 'RGBA')
    d.rounded_rectangle(PLATE, radius=22, outline=A(GOLD, 0.35), width=2)
    g = group_at(t)
    if not g:
        txt(d, 540, 1438, '@coach.agz', f(MONO, 28), GOLD, 0.7, 'ma'); return
    ws = [WORDS[i]['w'].upper().strip(',.?!') for i in g]
    size = 112
    while True:
        fn = f(BEB, size); sp = d.textlength(' ', font=fn) + 12; wd = [d.textlength(w_, font=fn) for w_ in ws]; tot = sum(wd) + sp * (len(ws) - 1)
        if tot <= 860: break
        size -= 4
    xs = []; x = (W - tot) / 2
    for w_ in wd: xs.append(x); x += w_ + sp
    act = 0
    for k, i in enumerate(g):
        if WORDS[i]['s'] <= t: act = k
    g0 = WORDS[g[0]]['s']; s = lerp(0.92, 1, expo((t - g0) / 0.10))
    cap = Image.new('RGBA', (W, 160), (0, 0, 0, 0)); cd = ImageDraw.Draw(cap)
    prev = max(0, act - 1); bt = expo((t - WORDS[g[act]]['s']) / 0.07) if act > 0 else 1
    bx0 = lerp(xs[prev], xs[act], bt) - 14; bx1 = lerp(xs[prev] + wd[prev], xs[act] + wd[act], bt) + 14
    cy = 80 - size * 0.5
    lit_bar(cd, bx0, cy - 2, bx1, cy + size * 0.98, RED)
    for k, (w_, x_) in enumerate(zip(ws, xs)):
        spoken = WORDS[g[k]]['s'] <= t; key = cw(g[k])
        col = CREAM
        if spoken and k != act and key in GOLDW: col = VGOLD
        if spoken and k != act and key in REDW: col = (255, 120, 110)
        cd.text((x_, cy + size * 0.06), w_, font=fn, fill=col + (255,) if spoken or k == act else (150, 150, 158, 255))
    if abs(s - 1) > 0.002:
        cap = cap.resize((int(W * s), int(160 * s)), Image.BICUBIC)
    im.alpha_composite(cap, (int((W - cap.width) / 2), int(1454 - cap.height / 2)))

# ---------------- frame ----------------
def frame(src, t):
    global GL
    base = footage(src, t)
    im = base.convert('RGBA')
    # soft top/bottom navy screens for legibility (light; footage itself untouched)
    glow = Image.new('RGBA', (W, H), (0, 0, 0, 0)); GL = ImageDraw.Draw(glow, 'RGBA')
    hook(im, t); band(im, t)
    scene_enzyme(im, t); scene_lens(im, t); scene_flow(im, t)
    scene_graph(im, t); scene_bars(im, t); scene_symptoms(im, t); scene_labs(im, t); scene_cta(im, t)
    GL = None
    if glow.getbbox():
        sm = glow.resize((W // 4, H // 4), Image.BILINEAR)
        g1 = np.asarray(sm.filter(ImageFilter.GaussianBlur(3.5))).astype(np.float32) / 255; g2 = np.asarray(sm.filter(ImageFilter.GaussianBlur(10))).astype(np.float32) / 255
        prem = np.clip(g1[..., :3] * g1[..., 3:] * 2.0 + g2[..., :3] * g2[..., 3:] * 1.6, 0, 1)
        prem = np.asarray(Image.fromarray((prem * 255).astype(np.uint8)).resize((W, H), Image.BILINEAR)).astype(np.float32) / 255
        b = np.asarray(im.convert('RGB')).astype(np.float32) / 255
        im = Image.fromarray(((1 - (1 - b) * (1 - prem)) * 255).astype(np.uint8)).convert('RGBA')
    captions(im, t)
    d = ImageDraw.Draw(im, 'RGBA')
    d.rectangle([0, 0, 7, H], fill=GOLD)  # signature gold rule
    txt(d, 540, 1554, 'FOR RESEARCH & EDUCATIONAL PURPOSES ONLY', f(MONOM, 18), MUTED, 0.75, 'ma')
    out = im.convert('RGB')
    # impact shake (2 frames) on the two heavy hits
    for th in (21.86, 27.96):
        k = round((t - th) * FPS)
        if k in (0, 1):
            dx = [8, -4][k]; z = 1.02; big = out.resize((int(W * z), int(H * z)), Image.BICUBIC); ox = (big.width - W) // 2 - dx; oy = (big.height - H) // 2
            out = big.crop((ox, oy, ox + W, oy + H))
    return out

def init():
    global BG, TISSUE, TPTS, LOGO
    BG = make_bg(); TISSUE, TPTS = make_tissue(LENS_R)
    try: LOGO = Image.open(HERE + '/../../brand/logo/coach-agz-logo-round.jpg').convert('RGB')
    except Exception: LOGO = None

def decode(t0, nframes):
    return subprocess.Popen(['ffmpeg', '-v', 'error', '-ss', f'{t0:.4f}', '-i', SRC, '-vf', 'fps=30', '-frames:v', str(nframes), '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], stdout=subprocess.PIPE)

if __name__ == '__main__':
    init(); mode = sys.argv[2]
    if mode == 'stills':
        outdir = sys.argv[3]
        for tt in [float(x) for x in sys.argv[4:]]:
            p = decode(tt, 1); buf = p.stdout.read(W * H * 3); p.wait()
            frame(Image.frombuffer('RGB', (W, H), buf), tt).resize((540, 960), Image.LANCZOS).save(f'{outdir}/st_{tt:05.2f}.jpg', quality=88)
        sys.exit()
    n0, n1, out = int(sys.argv[3]), int(sys.argv[4]), sys.argv[5]
    dec = decode(n0 / FPS, n1 - n0)
    enc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-crf', '16', '-preset', 'medium', '-pix_fmt', 'yuv420p', out], stdin=subprocess.PIPE)
    for n in range(n0, n1):
        buf = dec.stdout.read(W * H * 3)
        if len(buf) < W * H * 3:
            print('short', n); buf = last
        last = buf
        enc.stdin.write(frame(Image.frombuffer('RGB', (W, H), buf), n / FPS).tobytes())
    enc.stdin.close(); enc.wait(); dec.kill(); print('done', n0, n1)
