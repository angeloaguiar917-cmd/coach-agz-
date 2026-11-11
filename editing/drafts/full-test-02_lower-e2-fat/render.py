# @coach.agz Reel: "Two things to lower E2 (fat)". 1080x1920, 30 fps.
# Usage: python3 render.py <workdir> stills t1 t2 ...   |   python3 render.py <workdir> chunk n0 n1 out.mp4
# <workdir> holds assembled.mov, words_cut.json, logo.jpg and fonts/.
import json, subprocess, sys, math
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

WD = sys.argv[1].rstrip('/') + '/'
F = WD + 'fonts/'
W, H = 1080, 1920; FPS = 30
DUR = 2413 / FPS
WORDS = json.load(open(WD + 'words_cut.json'))

# ---------- palette (BRAND.md + test-06 overlay accents) ----------
GOLD = (201, 169, 110); CREAM = (244, 241, 234); NAVY = (14, 17, 23); MUTED = (184, 184, 188); MUTED2 = (124, 124, 130)
RED = (255, 34, 28); VGOLD = (255, 194, 26); CYAN = (0, 229, 255); GREEN = (30, 255, 110); AMBER = (240, 160, 48)
BLUE = (79, 163, 224); DEEP = (2, 3, 8); INK = (6, 8, 14); WHITE = (255, 255, 255); COARED = (210, 10, 20)
PANEL = (24, 26, 34)
MONO = 'JBMono-500.ttf'; MONOB = 'JBMono-700.ttf'; BEB = 'BebasNeue.ttf'; DMB = 'DMSans-700.ttf'; DMR = 'DMSans-400.ttf'
BAR = 'BarlowC-800.ttf'; BAR6 = 'BarlowC-600.ttf'

# ---------- timeline ----------
CUTS = [3.6, 11.5667, 16.1333, 21.2, 27.8333, 30.1667, 31.45, 35.6333, 38.4167, 44.5333, 52.1, 68.1667]
CAR_T = 31.45          # car footage from here: captions move to the top (mouth sits low in frame)
HOOK_END = 3.6
BAND = (3.6, 38.4167)

_fc = {}
def f(n, s):
    k = (n, int(s))
    if k not in _fc: _fc[k] = ImageFont.truetype(F + n, int(s))
    return _fc[k]
def clamp(x, a=0, b=1): return max(a, min(b, x))
def expo(x): x = clamp(x); return 1 if x >= 1 else 1 - 2 ** (-10 * x)
def ease_in(x): x = clamp(x); return x ** 3
def ease_io(x): x = clamp(x); return 4 * x ** 3 if x < .5 else 1 - (-2 * x + 2) ** 3 / 2
def lerp(a, b, t): return a + (b - a) * t
def A(c, a=1.0): return tuple(c[:3]) + (int(clamp(a) * 255),)
def appear(t, t0, dur=0.16): return expo((t - t0) / dur)
def dim(c, k=0.35): return tuple(int(v * k) for v in c)

# ---------- primitives (draw d = content layer, g = glow layer) ----------
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
def tag(d, g, x, y, label, col=RED, size=30, a=1.0):
    if a <= 0: return x
    fn = f(MONOB, size); tw = d.textlength(label, font=fn); h = size + 16
    lit_bar(d, x, y, x + tw + 24, y + h, col, a)
    d.text((x + 12, y + 5), label, font=fn, fill=A(INK if col in (VGOLD, GREEN, CYAN, GOLD) else WHITE, a))
    if g: g.rectangle([x - 4, y - 4, x + tw + 28, y + h + 4], outline=A(col, a), width=8)
    return x + tw + 24
def tagw(d, label, size=30): return d.textlength(label, font=f(MONOB, size)) + 24
def arrow(d, x0, y0, x1, y1, col, w=5, a=1.0, L=20):
    d.line([(x0, y0), (x1, y1)], fill=A(col, a), width=w)
    ang = math.atan2(y1 - y0, x1 - x0)
    d.polygon([(x1, y1), (x1 - L * math.cos(ang - 0.45), y1 - L * math.sin(ang - 0.45)), (x1 - L * math.cos(ang + 0.45), y1 - L * math.sin(ang + 0.45))], fill=A(col, a))
def tri(d, cx, cy, s, col, a=1.0, up=True):
    k = -1 if up else 1
    d.polygon([(cx - s, cy - k * s * 0.6), (cx + s, cy - k * s * 0.6), (cx, cy + k * s * 0.8)], fill=A(col, a))
def check(d, g, x, y, col, s=1.0, a=1.0):
    pts = [(x, y + 16 * s), (x + 10 * s, y + 28 * s), (x + 30 * s, y + 2 * s)]
    d.line(pts, fill=A(col, a), width=int(6 * s), joint='curve')
    if g: g.line(pts, fill=A(col, a), width=int(12 * s))
def cross(d, g, x, y, col, s=1.0, a=1.0):
    for p in ([(x, y), (x + 28 * s, y + 28 * s)], [(x + 28 * s, y), (x, y + 28 * s)]):
        d.line(p, fill=A(col, a), width=int(6 * s))
        if g: g.line(p, fill=A(col, a), width=int(12 * s))
def hexagon(d, g, cx, cy, r, col, a=1.0, fill=True):
    pts = [(cx + r * math.cos(math.pi / 3 * i + math.pi / 6), cy + r * math.sin(math.pi / 3 * i + math.pi / 6)) for i in range(6)]
    if fill: d.polygon(pts, fill=A(dim(col, 0.25), a))
    d.line(pts + [pts[0]], fill=A(col, a), width=max(2, int(r / 6)))
    if g: g.line(pts + [pts[0]], fill=A(col, a * 0.9), width=max(4, int(r / 3)))
def dot(d, g, x, y, r, col, a=1.0):
    d.ellipse([x - r, y - r, x + r, y + r], fill=A(col, a))
    if g: g.ellipse([x - r * 2, y - r * 2, x + r * 2, y + r * 2], fill=A(col, a * 0.8))
def hbar(d, g, x0, y0, x1, y1, frac, col, a=1.0):
    d.rectangle([x0, y0, x1, y1], fill=A((10, 12, 18), 0.9 * a), outline=A((70, 74, 90), a), width=2)
    xf = lerp(x0 + 3, x1 - 3, clamp(frac)); lit_bar(d, x0 + 3, y0 + 3, xf, y1 - 3, col, a)
    if g: g.rectangle([x0 + 3, y0 + 3, xf, y1 - 3], fill=A(col, a * 0.6))
def dashed(d, p0, p1, col, w=3, dash=14, gap=10, a=1.0):
    L = math.hypot(p1[0] - p0[0], p1[1] - p0[1]); n = int(L // (dash + gap)) + 1
    for i in range(n):
        s0 = i * (dash + gap) / L; s1 = min(1, (i * (dash + gap) + dash) / L)
        if s0 >= 1: break
        d.line([(lerp(p0[0], p1[0], s0), lerp(p0[1], p1[1], s0)), (lerp(p0[0], p1[0], s1), lerp(p0[1], p1[1], s1))], fill=A(col, a), width=w)
def mix(c1, c2, k): return tuple(int(lerp(a, b, clamp(k))) for a, b in zip(c1, c2))

FROST = []   # frosted rects requested by a scene this frame: (box, dark, blur, alpha)

# =====================================================================
# SCENES. Each fn(d, g, t, lay) draws onto the scene layer.
# =====================================================================
P_OUT = (56, 404, 1024, 1378)    # outdoor shots: captions low
P_CAR = (56, 556, 1024, 1476)    # car shots: captions on the roof at the top

# S1 · live line graph: E2 climbs out of range and breaks the frame
def s1(d, g, t, lay):
    x0, y0, x1, y1 = 130, 600, 950, 1250
    for k in range(1, 6): d.line([(x0, y1 - k * 110), (x1, y1 - k * 110)], fill=A((40, 46, 62)), width=1)
    d.line([(x0, y1), (x1, y1)], fill=A((110, 116, 134)), width=3); d.line([(x0, y0), (x0, y1)], fill=A((110, 116, 134)), width=3)
    txt(d, x1, y1 + 14, 'WEEKS ON CYCLE', f(MONO, 24), MUTED2, 1, 'ra')
    # reference range band
    a = appear(t, 4.2, 0.3)
    d.rectangle([x0 + 2, 1030, x1, 1140], fill=A(GREEN, 0.13 * a)); d.line([(x0, 1030), (x1, 1030)], fill=A(GREEN, 0.7 * a), width=2); d.line([(x0, 1140), (x1, 1140)], fill=A(GREEN, 0.7 * a), width=2)
    txt(d, x1 - 12, 1096, 'REFERENCE RANGE', f(MONO, 22), GREEN, a, 'ra')
    # cycle start marker
    xs = 300
    if t >= 4.62:
        a = appear(t, 4.62); dashed(d, (xs, y0 + 30), (xs, y1), VGOLD, 3, a=a); tag(d, g, xs + 8, y1 - 56, 'CYCLE START', VGOLD, 22, a)
    # the line
    def yof(x):
        if x <= xs: return 1090 + 10 * math.sin(x / 37)
        u = (x - xs) / (x1 - 40 - xs); return 1090 - (u ** 2.1) * 640 + 6 * math.sin(x / 29)
    pr = clamp((t - 4.20) / (7.50 - 4.20)); pr = pr ** 1.15
    xe = lerp(x0, x1 - 40, pr)
    pts = [(x, yof(x)) for x in np.arange(x0, xe, 6)] + [(xe, yof(xe))]
    for i in range(len(pts) - 1):
        yy = pts[i + 1][1]; col = CYAN if yy > 1030 else (AMBER if yy > 760 else RED)
        d.line([pts[i], pts[i + 1]], fill=A(col), width=7); g.line([pts[i], pts[i + 1]], fill=A(col), width=14)
    hx, hy = pts[-1]; hc = CYAN if hy > 1030 else (AMBER if hy > 760 else RED)
    dot(d, g, hx, hy, 11, WHITE); dot(d, g, hx, hy, 7, hc)
    # status readout
    st, sc = ('IN RANGE', GREEN) if hy > 1030 else (('RISING', AMBER) if hy > 760 else ('HIGH', RED))
    txt(d, x0 + 20, y0 + 14, 'E2 STATUS', f(MONO, 24), MUTED, appear(t, 4.3))
    txt(d, x0 + 20, y0 + 44, st, f(BEB, 84), sc, appear(t, 4.3))
    if t >= 7.50:
        a = appear(t, 7.50, 0.08)
        # breach burst on the frame edge
        r = lerp(10, 60, expo((t - 7.50) / 0.3)); d.ellipse([hx - r, hy - r, hx + r, hy + r], outline=A(RED, a * (1 - clamp((t - 7.5) / 0.5))), width=5)
        tag(d, g, 520, 470, 'OUT OF RANGE', RED, 30, a)

# S2 · chest scan inset + live detection brackets on the face
def s2(d, g, t, lay):
    cx0, cy0, cx1, cy1 = 768, 430, 1030, 880
    a = appear(t, 8.40, 0.18)
    FROST.append(((cx0, cy0, cx1, cy1), 0.86, 10, a))
    d.rectangle([cx0, cy0, cx1, cy1], outline=A(CYAN, 0.6 * a), width=2); brackets(d, cx0, cy0, cx1, cy1, A(CYAN, a), 24, 5); brackets(g, cx0, cy0, cx1, cy1, A(CYAN, a), 24, 10)
    txt(d, cx0 + 14, cy0 + 12, 'CHEST · SCAN', f(MONOB, 22), CYAN, a)
    ox = cx0; oy = cy0
    C = CYAN; lw = 4
    torso = [[(ox + 112, oy + 70), (ox + 112, oy + 110)], [(ox + 150, oy + 70), (ox + 150, oy + 110)],
             [(ox + 22, oy + 160), (ox + 72, oy + 118), (ox + 190, oy + 118), (ox + 240, oy + 160)],
             [(ox + 32, oy + 160), (ox + 46, oy + 440)], [(ox + 230, oy + 160), (ox + 216, oy + 440)]]
    for ln in torso: d.line(ln, fill=A(C, a * 0.9), width=lw); g.line(ln, fill=A(C, a * 0.6), width=8)
    for bx in (ox + 44, ox + 132):
        d.arc([bx, oy + 170, bx + 90, oy + 290], 15, 165, fill=A(C, a * 0.9), width=lw); g.arc([bx, oy + 170, bx + 90, oy + 290], 15, 165, fill=A(C, a * 0.6), width=8)
    nips = [(ox + 92, oy + 268), (ox + 172, oy + 268)]
    for (nx, ny) in nips: d.ellipse([nx - 6, ny - 6, nx + 6, ny + 6], outline=A(C, a), width=3)
    sy = oy + 60 + ((t - 8.4) % 1.1) / 1.1 * 380
    d.line([(cx0 + 6, sy), (cx1 - 6, sy)], fill=A(CYAN, 0.8 * a), width=2); g.line([(cx0 + 6, sy), (cx1 - 6, sy)], fill=A(CYAN, 0.8 * a), width=8)
    if t >= 8.82:
        b = appear(t, 8.82, 0.1); pul = 0.5 + 0.5 * math.sin((t - 8.82) * 12)
        for (nx, ny) in nips:
            r = 14 + 8 * pul; d.ellipse([nx - r, ny - r, nx + r, ny + r], outline=A(RED, b), width=4); g.ellipse([nx - r, ny - r, nx + r, ny + r], outline=A(RED, b), width=10)
            dot(d, g, nx, ny, 6, RED, b)
        tag(d, g, cx0, cy1 + 12, 'TENDER · SWOLLEN', RED, 23, b)
    # face detection
    if t >= 9.60:
        b = appear(t, 9.60, 0.12); fx0, fy0, fx1, fy1 = 205, 640, 745, 1365
        q = expo((t - 9.60) / 0.14); inset = lerp(60, 0, q)
        bx = (fx0 - inset, fy0 - inset, fx1 + inset, fy1 + inset)
        brackets(d, *bx, A(RED, b), 46, 7); brackets(g, *bx, A(RED, b), 46, 14)
        if t < 10.6:
            yy = lerp(fy0, fy1, clamp((t - 9.6) / 1.0)); d.line([(fx0, yy), (fx1, yy)], fill=A(CYAN, 0.9), width=3); g.line([(fx0, yy), (fx1, yy)], fill=A(CYAN, 1), width=12)
        txt(d, fx0 + 10, fy0 + 10, 'FACE · FLUID', f(MONOB, 22), RED, b)
    if t >= 9.86: tag(d, g, 768, 1020, 'BLOAT · PUFFY', RED, 26, appear(t, 9.86))
    if t >= 10.82: tag(d, g, 768, 1080, 'PERSISTENT', VGOLD, 26, appear(t, 10.82))

# S3 · prescription labels, then the verdict stamp
RX = {}
def make_rx(hdr, big, sub, row):
    im = Image.new('RGBA', (600, 300), (236, 234, 228, 255)); d = ImageDraw.Draw(im)
    d.rectangle([0, 0, 600, 62], fill=COARED); d.text((22, 14), hdr, font=f(MONOB, 28), fill=WHITE)
    d.text((24, 82), big, font=f(DMB, 66), fill=INK); d.text((26, 166), sub, font=f(MONO, 24), fill=(110, 110, 120))
    d.line([(22, 212), (578, 212)], fill=(200, 198, 192), width=2); d.text((24, 228), row, font=f(DMR, 30), fill=(60, 62, 72))
    nz = (np.random.default_rng(len(big)).standard_normal((300, 600)) * 7).astype(np.int16)
    arr = np.asarray(im).astype(np.int16); arr[..., :3] = np.clip(arr[..., :3] + nz[..., None], 0, 255)
    return Image.fromarray(arr.astype(np.uint8), 'RGBA')
def paste_rot(lay, im, x, y, ang, a=1.0, shadow=True):
    r = im.rotate(ang, resample=Image.BICUBIC, expand=True)
    if a < 1: r.putalpha(r.split()[3].point(lambda v: int(v * a)))
    if shadow:
        sh = Image.new('RGBA', r.size, (0, 0, 0, 0)); sh.putalpha(r.split()[3].point(lambda v: int(v * 0.6)))
        sh = sh.filter(ImageFilter.GaussianBlur(14)); lay.alpha_composite(sh, (int(x + 10), int(y + 18)))
    lay.alpha_composite(r, (int(x), int(y)))
def s3(d, g, t, lay):
    if not RX:
        RX['a'] = make_rx('Rx · SERM', 'TAMOXIFEN', 'brand: NOLVADEX', 'Blocks estrogen at the receptor')
        RX['b'] = make_rx('Rx · AROMATASE INHIBITOR', 'ANASTROZOLE', 'class: AI', 'Cuts estrogen production')
    if t >= 12.62:
        p = expo((t - 12.62) / 0.22); paste_rot(lay, RX['a'], lerp(-700, 60, p), 450, 3, p)
    if t >= 14.36:
        p = expo((t - 14.36) / 0.22); paste_rot(lay, RX['b'], lerp(1100, 400, p), 830, -3, p)
    d = ImageDraw.Draw(lay, 'RGBA')
    if t >= 15.58:
        p = expo((t - 15.58) / 0.10); s = lerp(1.45, 1.0, p)
        st = Image.new('RGBA', (860, 170), (0, 0, 0, 0)); sd = ImageDraw.Draw(st)
        sd.rounded_rectangle([6, 6, 854, 164], radius=18, outline=A(RED), width=10)
        sd.text((430, 88), 'TREATS THE SYMPTOM', font=f(BEB, 112), fill=A(RED), anchor='mm')
        st = st.resize((int(860 * s), int(170 * s)), Image.BICUBIC).rotate(4, resample=Image.BICUBIC, expand=True)
        st.putalpha(st.split()[3].point(lambda v: int(v * p)))
        lay.alpha_composite(st, (int(540 - st.width / 2), int(1210 - st.height / 2)))
        g.rounded_rectangle([540 - 430 * s, 1210 - 85 * s, 540 + 430 * s, 1210 + 85 * s], radius=18, outline=A(RED, p * 0.7), width=10)
        d = ImageDraw.Draw(lay, 'RGBA')
        if t >= 15.80: tag(d, g, 540 - tagw(d, 'NOT THE SOURCE', 30) / 2, 1318, 'NOT THE SOURCE', RED, 30, appear(t, 15.80))

# S4 · drive-thru receipt printing, then the surplus stamp
REC = {}
REC_LINES = [(16.30, 'hdr'), (17.18, ('DBL BURGER', '590')), (17.82, ('LG FRIES', '480')), (18.54, ('LG SHAKE', '530')),
             (19.20, ('2 COOKIES', '340')), (19.64, 'total')]
def make_receipt():
    w, h = 300, 560; im = Image.new('RGBA', (w, h), (243, 241, 235, 255)); d = ImageDraw.Draw(im)
    ys = {}
    d.text((w / 2, 34), 'DRIVE-THRU', font=f(DMB, 34), fill=INK, anchor='mm'); d.text((w / 2, 70), 'ORDER #41 · 9:47 PM', font=f(MONO, 18), fill=(110, 110, 118), anchor='mm')
    dashed(d, (16, 96), (w - 16, 96), (150, 150, 156), 2, 8, 6); ys['hdr'] = 104
    y = 118
    for _, it in REC_LINES[1:5]:
        d.text((18, y), it[0], font=f(MONO, 22), fill=(40, 42, 50)); d.text((w - 18, y), it[1], font=f(MONO, 22), fill=(40, 42, 50), anchor='ra'); y += 46; ys[it[0]] = y
    dashed(d, (16, y + 4), (w - 16, y + 4), (150, 150, 156), 2, 8, 6)
    d.text((18, y + 18), 'TOTAL kcal', font=f(MONOB, 24), fill=INK); d.text((w - 18, y + 18), '1,940', font=f(MONOB, 24), fill=INK, anchor='ra')
    ys['total'] = y + 60
    d.text((w / 2, y + 96), 'ONE MEAL', font=f(MONO, 18), fill=(120, 120, 128), anchor='mm')
    ys['end'] = y + 120
    nz = (np.random.default_rng(3).standard_normal((h, w)) * 5).astype(np.int16)
    arr = np.asarray(im).astype(np.int16); arr[..., :3] = np.clip(arr[..., :3] + nz[..., None], 0, 255)
    return Image.fromarray(arr.astype(np.uint8), 'RGBA'), ys
def s4(d, g, t, lay):
    if not REC: REC['im'], REC['ys'] = make_receipt()
    im, ys = REC['im'], REC['ys']
    vis = 0
    for (tt, key) in REC_LINES:
        if t >= tt:
            k = key if isinstance(key, str) else key[0]; tgt = ys[k] if k != 'total' else ys['end']
            prev = vis; vis = lerp(prev, tgt, expo((t - tt) / 0.18))
    vis = int(vis)
    if vis < 10: return
    x, y = 752, 430
    crop = im.crop((0, 0, im.width, vis)).copy()
    # torn bottom edge
    m = crop.split()[3]; md = ImageDraw.Draw(m)
    for i in range(0, im.width, 12): md.polygon([(i, vis), (i + 6, vis - 7), (i + 12, vis)], fill=0)
    crop.putalpha(m)
    paste_rot(lay, crop, x, y, -2)
    d = ImageDraw.Draw(lay, 'RGBA')
    if t >= 20.34:
        p = expo((t - 20.34) / 0.09); s = lerp(1.5, 1, p)
        st = Image.new('RGBA', (300, 110), (0, 0, 0, 0)); sd = ImageDraw.Draw(st)
        sd.rectangle([5, 5, 295, 105], outline=A(RED), width=8); sd.text((150, 56), 'SURPLUS', font=f(BEB, 86), fill=A(RED), anchor='mm')
        st = st.resize((int(300 * s), int(110 * s)), Image.BICUBIC).rotate(12, resample=Image.BICUBIC, expand=True)
        st.putalpha(st.split()[3].point(lambda v: int(v * p * 0.95)))
        lay.alpha_composite(st, (int(900 - st.width / 2), int(y + ys['total'] - 20 - st.height / 2)))
        d = ImageDraw.Draw(lay, 'RGBA')
    if t >= 20.92:
        b = appear(t, 20.92); yy = y + ys['end'] + 30
        lit_bar(d, 752, yy, 1040, yy + 70, RED, b); g.rectangle([748, yy - 4, 1044, yy + 74], outline=A(RED, b), width=8)
        txt(d, 776, yy + 6, 'BODY FAT', f(BEB, 64), WHITE, b); tri(d, 1004, yy + 34, 16, WHITE, b, up=True)

# S5 · picture-in-picture + fat cell mechanism (full brand scene)
CELLS = [(300, 960, 105), (520, 900, 115), (740, 960, 100), (410, 1130, 100), (630, 1120, 108), (860, 1150, 85), (200, 1160, 80)]
def s5(d, g, t, lay):
    txt(d, 92, 450, '——', f(BAR, 40), GOLD, appear(t, 21.42)); txt(d, 160, 452, 'FAT TISSUE', f(BAR, 38), GOLD, appear(t, 21.5))
    a = appear(t, 22.0, 0.2)
    txt(d, 90, 510, 'STORAGE', f(BEB, 130), CREAM if t < 23.76 else MUTED2, a)
    if t >= 23.76:
        p = expo((t - 23.76) / 0.18); w = d.textlength('STORAGE', font=f(BEB, 130))
        d.line([(84, 570), (84 + (w + 12) * p, 570)], fill=A(RED), width=12); g.line([(84, 570), (84 + (w + 12) * p, 570)], fill=A(RED), width=20)
    if t >= 24.86:
        b = appear(t, 24.86, 0.14); y = lerp(700, 650, b)
        lit_bar(d, 90, y, 610, y + 96, VGOLD, b); g.rectangle([86, y - 4, 614, y + 100], outline=A(VGOLD, b), width=10)
        txt(d, 108, y + 6, 'ENDOCRINE ORGAN', f(BEB, 88), INK, b)
    # cells
    ca = appear(t, 22.2, 0.3)
    for i, (cx, cy, r) in enumerate(CELLS):
        ra = ca * appear(t, 22.2 + i * 0.06, 0.2); rr = r * lerp(0.85, 1, ra)
        d.ellipse([cx - rr, cy - rr * 0.92, cx + rr, cy + rr * 0.92], fill=A((60, 46, 20), 0.55 * ra), outline=A((250, 210, 130), ra), width=4)
        g.ellipse([cx - rr, cy - rr * 0.92, cx + rr, cy + rr * 0.92], outline=A((250, 200, 100), 0.4 * ra), width=8)
        d.ellipse([cx + rr * 0.35, cy - rr * 0.55, cx + rr * 0.6, cy - rr * 0.3], fill=A((140, 110, 60), ra))   # nucleus
        n = 0
        for j, tt in enumerate([26.02, 26.30, 26.62]):
            if t >= tt + i * 0.03: n = j + 1
        if t >= 24.86 and n == 0: n = 1 if t >= 25.2 else 0
        for k in range(n):
            ang = k * 2.1 + i; hx = cx + math.cos(ang) * rr * 0.42 - 8; hy = cy + math.sin(ang) * rr * 0.4
            hexagon(d, g, hx, hy, 18, VGOLD, appear(t, (25.2 if k == 0 else [26.02, 26.30, 26.62][k]) + i * 0.03, 0.1))
    if t >= 26.92: tag(d, g, 640, 790, 'AROMATASE ↑', VGOLD, 28, appear(t, 26.92))
    # testosterone in, estradiol out
    if t >= 27.40:
        a2 = appear(t, 27.40, 0.2)
        for k in range(9):
            p = ((t - 27.4) * 0.55 + k / 9) % 1; cy = CELLS[k % 5][1]; cx = CELLS[k % 5][0]
            x = lerp(-20, cx, p); y = lerp(cy + 40 * math.sin(k), cy, p); dot(d, g, x, y, 8, CYAN, a2 * min(1, (1 - p) * 4))
        txt(d, 90, 1265, '● T IN', f(MONOB, 26), CYAN, a2)
    if t >= 28.46:
        a3 = appear(t, 28.46, 0.2)
        for k in range(14):
            p = ((t - 28.46) * 0.7 + k / 14) % 1; c = CELLS[k % 7]
            x = lerp(c[0], 1100, p); y = lerp(c[1], c[1] - 160 + 40 * math.sin(k * 2), p); dot(d, g, x, y, 9, RED, a3 * min(1, p * 5))
        txt(d, 300, 1265, '● E2 OUT', f(MONOB, 26), RED, a3)
    if t >= 29.10: tag(d, g, 640, 1252, 'MORE ESTRADIOL', RED, 28, appear(t, 29.10))

# S6 · dose stat + body-fat meter, then the aromatase gauge (one panel, content swaps on the trim cut)
def s6(d, g, t, lay):
    if t < 35.6333:
        val = int(round(400 * ease_io((t - 31.60) / 0.60))) if t >= 31.60 else 0
        a = appear(t, 31.58, 0.1); fn = f(BEB, 330)
        if t >= 31.60:
            s = '%d' % val; tw = d.textlength(s, font=fn)
            txt(d, 96, 610, s, fn, VGOLD, a)
            if t >= 32.20:
                b = appear(t, 32.20, 0.1); txt(d, 100 + max(tw, d.textlength('400', font=fn)) + 16, 780, 'MG', f(BEB, 130), CREAM, b)
        if t >= 32.96: txt(d, 104, 930, 'TESTOSTERONE', f(MONOB, 34), CYAN, appear(t, 32.96))
        # body silhouette with fat filling
        if t >= 33.90:
            b = appear(t, 33.90, 0.2); bx0, by0, bx1, by1 = 700, 1060, 950, 1430
            fill = 0.15 + 0.62 * expo((t - 34.14) / 1.0)
            msk = Image.new('L', (W, H), 0); md = ImageDraw.Draw(msk)
            md.ellipse([775, 960, 875, 1060], fill=255); md.rounded_rectangle([bx0, by0, bx1, by1], radius=70, fill=255)
            fy = by1 - (by1 - 960) * fill
            fl = Image.new('RGBA', (W, H), (0, 0, 0, 0)); fd = ImageDraw.Draw(fl)
            col = mix(AMBER, RED, (fill - 0.4) / 0.4)
            lit_bar(fd, bx0, fy, bx1, by1, col, b * 0.85)
            fl.putalpha(Image.fromarray(np.minimum(np.asarray(fl.split()[3]), np.asarray(msk))))
            lay.alpha_composite(fl)
            d.ellipse([775, 960, 875, 1060], outline=A(CREAM, b), width=4); d.rounded_rectangle([bx0, by0, bx1, by1], radius=70, outline=A(CREAM, b), width=4)
            g.rounded_rectangle([bx0, by0, bx1, by1], radius=70, outline=A(col, b * 0.7), width=10)
            txt(d, 104, 1070, 'BODY FAT', f(MONOB, 30), CREAM, b)
            hbar(d, g, 104, 1120, 640, 1170, fill, col, b)
            if t >= 34.90: tag(d, g, 104, 1200, 'HIGH', RED, 34, appear(t, 34.90))
        if t >= 35.20:
            b = appear(t, 35.20); txt(d, 104, 1300, '400 MG  ×  HIGH BODY FAT', f(MONOB, 30), VGOLD, b)
            txt(d, 104, 1350, '= ?', f(BEB, 80), WHITE, b)
    else:
        cx, cy, R = 540, 1250, 380
        a = appear(t, 35.6333, 0.12)
        txt(d, 100, 640, 'AROMATASE OUTPUT', f(MONOB, 32), CREAM, a)
        segs = [(180, 225, BLUE), (225, 270, GREEN), (270, 315, AMBER), (315, 360, RED)]
        bb = [cx - R, cy - R, cx + R, cy + R]
        for s0, s1_, col in segs:
            d.arc(bb, s0 + 1, s1_ - 1, fill=A(col, a), width=50); g.arc(bb, s0 + 1, s1_ - 1, fill=A(col, a * 0.5), width=60)
        for k in range(19):
            an = math.radians(180 + k * 10); r0 = R - 64; r1 = R - (84 if k % 3 == 0 else 74)
            d.line([(cx + r0 * math.cos(an), cy + r0 * math.sin(an)), (cx + r1 * math.cos(an), cy + r1 * math.sin(an))], fill=A(MUTED, a), width=3)
        ang = 248 if t < 35.86 else lerp(248, 352, ease_io((t - 35.86) / (37.80 - 35.86)))
        if t >= 37.80: ang = 352 + 2.2 * math.sin((t - 37.8) * 40) * math.exp(-(t - 37.8) * 3)
        an = math.radians(ang); L = R - 90
        d.line([(cx, cy), (cx + L * math.cos(an), cy + L * math.sin(an))], fill=A(WHITE, a), width=9)
        g.line([(cx, cy), (cx + L * math.cos(an), cy + L * math.sin(an))], fill=A(RED if ang > 315 else WHITE, a), width=16)
        dot(d, g, cx, cy, 24, WHITE, a); d.ellipse([cx - 12, cy - 12, cx + 12, cy + 12], fill=A(INK, a))
        lbl, col = ('NORMAL', GREEN) if ang < 270 else (('HIGH', AMBER) if ang < 315 else ('MAX', RED))
        txt(d, cx, cy + 40, lbl, f(BEB, 120), col, a, 'ma')
        # factory icon venting estradiol
        if t >= 37.44:
            b = appear(t, 37.44, 0.14); fx, fy = 760, 700
            pts = [(fx, fy + 150), (fx, fy + 70), (fx + 50, fy + 100), (fx + 50, fy + 70), (fx + 100, fy + 100), (fx + 100, fy + 20), (fx + 140, fy + 20), (fx + 140, fy + 150)]
            d.polygon(pts, fill=A((20, 22, 30), b)); d.line(pts + [pts[0]], fill=A(RED, b), width=5); g.line(pts + [pts[0]], fill=A(RED, b), width=10)
            for k in range(8):
                p = ((t - 37.44) * 0.9 + k / 8) % 1
                dot(d, g, fx + 120 + 30 * math.sin(k * 1.7 + p * 3), fy + 10 - p * 150, 6 + 6 * p, RED, b * (1 - p))
            txt(d, fx - 20, fy + 160, 'E2 FACTORY', f(MONOB, 24), RED, b)

# S7 · dose vs result: gains plateau, estrogen keeps climbing
def s7(d, g, t, lay):
    x0, y0, x1, y1 = 140, 720, 960, 1380
    a = appear(t, 38.42, 0.15)
    txt(d, 96, 586, '——', f(BAR, 40), GOLD, a); txt(d, 164, 588, 'DOSE VS RESULT', f(BAR, 38), GOLD, a)
    for k in range(1, 6): d.line([(x0, y1 - k * 120), (x1, y1 - k * 120)], fill=A((40, 46, 62), a), width=1)
    d.line([(x0, y1), (x1 + 10, y1)], fill=A(CREAM, a), width=4); d.line([(x0, y0 - 20), (x0, y1)], fill=A(CREAM, a), width=4)
    tri(d, x1 + 18, y1, 14, CREAM, a)  # x-axis arrowhead (pointing right drawn as small marker)
    txt(d, x1, y1 + 16, 'DOSE', f(MONOB, 26), CREAM, a, 'ra'); txt(d, x0 + 12, y0 - 28, 'EFFECT', f(MONOB, 26), CREAM, a)
    gy = lambda u: y1 - (1 - math.exp(-3.4 * u)) * 560
    ry = lambda u: y1 - (u ** 2.5) * 640
    px = lambda u: lerp(x0, x1, u)
    ug = clamp((t - 38.64) / 1.0); ug = ease_io(ug)
    if ug > 0:
        pts = [(px(u), gy(u)) for u in np.linspace(0, ug, 80)]
        d.line(pts, fill=A(VGOLD), width=8, joint='curve'); g.line(pts, fill=A(VGOLD), width=16)
        dot(d, g, *pts[-1], 9, VGOLD)
        if ug < 1: dashed(d, (pts[-1][0], y1), (pts[-1][0], pts[-1][1]), VGOLD, 2, 8, 8, 0.6)
        if ug >= 1: txt(d, px(0.22), gy(0.22) - 96, 'GAINS', f(MONOB, 30), VGOLD, appear(t, 39.64))
    ur = ease_io(clamp((t - 39.68) / 1.1))
    if ur > 0:
        pts = [(px(u), ry(u)) for u in np.linspace(0, ur, 80)]
        d.line(pts, fill=A(RED), width=8, joint='curve'); g.line(pts, fill=A(RED), width=16)
        dot(d, g, *pts[-1], 9, RED)
        if ur >= 1: txt(d, x1 - 70, ry(1) - 4, 'ESTROGEN', f(MONOB, 30), RED, appear(t, 40.78), 'ra')
    if t >= 41.38:
        b = appear(t, 41.38, 0.3); us = np.linspace(0.62, 1, 40)
        poly = [(px(u), gy(u)) for u in us] + [(px(u), ry(u)) for u in us[::-1]]
        d.polygon(poly, fill=A(RED, 0.22 * b))
        for k in range(10):
            u = 0.64 + k * 0.036; ya, yb = gy(u), ry(u)
            if yb < ya: d.line([(px(u), ya), (px(u), yb)], fill=A(RED, 0.35 * b), width=2)
        tag(d, g, 470, 1180, 'MORE DOSE · LITTLE GAIN', RED, 26, b)
    if t >= 41.76:
        b = appear(t, 41.76); yp = gy(1)
        dashed(d, (x0, yp), (x1, yp), VGOLD, 3, 16, 10, b); tag(d, g, x0 + 20, yp - 60, 'PLATEAU', VGOLD, 26, b)

# S8 · full-screen title wipe (hand-off into the steps)
def s8(d, g, t, lay):
    a = appear(t, 43.18, 0.16)
    txt(d, 96, 770, '——', f(BAR, 44), GOLD, a); txt(d, 170, 772, 'THE FIX', f(BAR, 42), GOLD, a)
    b = appear(t, 43.30, 0.14); yo = lerp(30, 0, b)
    txt(d, 90, 830 + yo, 'FIX THE', f(BEB, 200), CREAM, b)
    c = appear(t, 43.50, 0.14)
    txt(d, 90, 1010 + yo, 'SOURCE', f(BEB, 200), VGOLD, c)
    if t >= 43.62: txt(d, 96, 1230, 'Not the symptom.', f(DMR, 46), MUTED, appear(t, 43.62))

# S9 · numbered steps with live mini-graphics
def pill(d, g, x, y, label, t0, t):
    p = expo((t - t0) / 0.18); xx = lerp(-160, x, p)
    lit_bar(d, xx, y, xx + 112, y + 104, VGOLD, 1); g.rectangle([xx - 4, y - 4, xx + 116, y + 108], outline=A(VGOLD), width=10)
    txt(d, xx + 56, y + 52, label, f(BEB, 92), INK, 1, 'mm')
def lock(d, x, y, col, a, opened=False):
    d.rounded_rectangle([x, y + 18, x + 34, y + 46], radius=5, fill=A(col, a))
    d.arc([x + 5, y + (0 if not opened else -8), x + 29, y + 30], 180, 360, fill=A(col, a), width=5)
def s9(d, g, t, lay):
    rows = [(640, 44.62), (920, 47.40), (1200, 49.60)]
    for i, (y, t0) in enumerate(rows):
        if t < t0: continue
        pill(d, g, 96, y, '0%d' % (i + 1), t0, t)
        a = appear(t, t0 + 0.08, 0.14)
        if i == 0:
            txt(d, 236, y - 4, 'CUT BODY FAT', f(BEB, 84), CREAM, a)
            if t >= 45.60:
                b = appear(t, 45.60); x = 236
                cross(d, g, x, y + 92, RED, 0.8, b); txt(d, x + 34, y + 88, 'DRIVE-THRU', f(MONOB, 26), RED, b)
            k = 0.82 if t < 46.36 else lerp(0.82, 0.36, expo((t - 46.36) / 0.7))
            hbar(d, g, 520, y + 94, 960, y + 130, k, mix(RED, GREEN, (0.82 - k) / 0.46), a)
            txt(d, 520, y + 136, 'BODY FAT', f(MONO, 22), MUTED, a)
            if t >= 46.36: tri(d, 940, y + 156, 14, GREEN, appear(t, 46.5), up=False)
        if i == 1:
            txt(d, 236, y - 4, 'GET LEAN FIRST', f(BEB, 84), CREAM, a)
            ok = t >= 48.30; b = appear(t, 47.62)
            d.rounded_rectangle([236, y + 92, 440, y + 150], radius=10, fill=A(PANEL, b), outline=A(GREEN if ok else (90, 94, 110), b), width=3)
            txt(d, 258, y + 102, 'LEAN', f(BAR, 40), WHITE, b)
            if ok: check(d, g, 380, y + 106, GREEN, 0.9, appear(t, 48.30))
            arrow(d, 456, y + 121, 560, y + 121, CREAM, 4, b)
            un = t >= 49.10; col = VGOLD if un else (80, 84, 100)
            d.rounded_rectangle([576, y + 92, 860, y + 150], radius=10, fill=A(PANEL, b), outline=A(col, b), width=3)
            txt(d, 600, y + 102, 'THEN DOSE', f(BAR, 40), col if un else (120, 124, 140), b)
            lock(d, 808, y + 100, col, b, un)
            if un: g.rounded_rectangle([576, y + 92, 860, y + 150], radius=10, outline=A(VGOLD, appear(t, 49.10)), width=8)
        if i == 2:
            txt(d, 236, y - 4, 'LOWER THE DOSE', f(BEB, 84), CREAM, a)
            k = 0.80 if t < 52.10 else lerp(0.80, 0.40, expo((t - 52.10) / 0.6))
            hbar(d, g, 236, y + 94, 700, y + 130, k, mix(RED, AMBER, (0.8 - k) / 0.4), a)
            txt(d, 236, y + 136, 'DOSE', f(MONO, 22), MUTED, a)
            if t >= 52.10: tri(d, 680, y + 156, 14, AMBER, appear(t, 52.2), up=False)
            if t >= 52.88: tag(d, g, 724, y + 90, 'UNTIL LEAN', VGOLD, 26, appear(t, 52.88))

# S10 · dose-range slider into the dial-in window, then the habit chips
def s10(d, g, t, lay):
    x0, x1, y0, y1 = 110, 970, 780, 830
    px = lambda m: lerp(x0, x1, m / 400)
    a = appear(t, 54.10, 0.14)
    txt(d, 104, 650, 'WEEKLY DOSE · MG', f(MONOB, 28), MUTED, a)
    stops = [(0, BLUE), (100, GREEN), (150, GREEN), (210, AMBER), (300, RED), (400, RED)]
    for xx in range(int(x0), int(x1)):
        m = (xx - x0) / (x1 - x0) * 400
        for j in range(len(stops) - 1):
            if stops[j][0] <= m <= stops[j + 1][0]:
                k = (m - stops[j][0]) / max(1, stops[j + 1][0] - stops[j][0]); col = mix(stops[j][1], stops[j + 1][1], k); break
        d.line([(xx, y0), (xx, y1)], fill=A(dim(col, 0.8), a))
    g.rectangle([x0, y0, x1, y1], outline=A(WHITE, 0.15 * a), width=6)
    for m in (0, 100, 150, 400): txt(d, px(m), y1 + 14, str(m), f(MONOB, 26), CREAM, a, 'ma')
    if t >= 54.74:
        b = appear(t, 54.74, 0.12)
        d.rectangle([px(100) - 4, y0 - 14, px(150) + 4, y1 + 14], outline=A(GREEN, b), width=5); g.rectangle([px(100) - 4, y0 - 14, px(150) + 4, y1 + 14], outline=A(GREEN, b), width=12)
    m = 400 if t < 54.30 else lerp(400, 125, ease_io((t - 54.30) / 0.95))
    if t >= 54.16:
        b = appear(t, 54.16, 0.1); x = px(m); col = GREEN if 100 <= m <= 150 else (AMBER if m < 260 else RED)
        d.polygon([(x - 18, y0 - 44), (x + 18, y0 - 44), (x, y0 - 12)], fill=A(col, b)); g.polygon([(x - 18, y0 - 44), (x + 18, y0 - 44), (x, y0 - 12)], fill=A(col, b))
        d.line([(x, y0 - 12), (x, y1 + 4)], fill=A(WHITE, b), width=4)
        txt(d, x, y0 - 104, '%d' % round(m), f(BEB, 64), col, b, 'ma')
    if t >= 55.38:
        b = appear(t, 55.38, 0.12)
        txt(d, 104, 900, '100-150', f(BEB, 170), GREEN, b); w = d.textlength('100-150', font=f(BEB, 170))
        txt(d, 120 + w, 990, 'MG', f(BEB, 80), CREAM, b); txt(d, 124 + w, 966, 'DIAL-IN WINDOW', f(MONOB, 22), GREEN, b)
    chips = [('NUTRITION', 57.02), ('STEPS', 58.26), ('CARDIO', 59.20), ('EAT RIGHT', 59.82)]
    for i, (nm, tt) in enumerate(chips):
        if t < tt - 0.02: continue
        b = appear(t, tt, 0.12); x = 104 + (i % 2) * 440; y = 1130 + (i // 2) * 118; yo = lerp(16, 0, b)
        d.rounded_rectangle([x, y + yo, x + 410, y + 96 + yo], radius=14, fill=A(PANEL, 0.95 * b), outline=A(GREEN, b), width=3)
        g.rounded_rectangle([x, y + yo, x + 410, y + 96 + yo], radius=14, outline=A(GREEN, 0.6 * b), width=8)
        check(d, g, x + 24, y + 30 + yo, GREEN, 1.1, b); txt(d, x + 80, y + 18 + yo, nm, f(BAR, 54), WHITE, b)

# S11 · same dose, two bodies: grouped bar comparison
def s11(d, g, t, lay):
    cols = [(90, 520, 'HIGH BODY FAT', RED, 60.90), (560, 990, 'LEAN', GREEN, 61.70)]
    base, top = 1370, 905
    for ci, (cx0, cx1, hdr, col, t0) in enumerate(cols):
        if t < t0: continue
        a = appear(t, t0, 0.16)
        d.rectangle([cx0, 690, cx1, 1460], fill=A(PANEL, 0.93 * a), outline=A((58, 54, 48), a), width=2)
        p = expo((t - t0) / 0.35); d.line([(cx0, 690), (lerp(cx0, cx1, p), 690)], fill=A(col, a), width=6); g.line([(cx0, 690), (lerp(cx0, cx1, p), 690)], fill=A(col, a), width=12)
        txt(d, cx0 + 24, 708, hdr, f(BAR, 50), col, a)
        d.line([(cx0 + 24, base), (cx1 - 24, base)], fill=A((110, 116, 134), a), width=3)
        bars = []
        ar = 0
        if t >= 62.30: ar = 0.92 * expo((t - 62.30) / 0.45)
        if ci == 1 and t >= 63.32: ar = lerp(0.92, 0.34, expo((t - 63.32) / 0.5))
        e2 = 0
        if t >= 66.70: e2 = (0.98 if ci == 0 else 0.42) * expo((t - 66.70) / 0.45)
        for bi, (val, lab) in enumerate([(ar, 'AROMATASE'), (e2, 'E2')]):
            bx0 = cx0 + 50 + bi * 190; bx1 = bx0 + 140
            bc = col if (ci == 0 or (bi == 0 and t >= 63.32) or bi == 1) else AMBER
            if val > 0:
                yy = base - (base - top) * val; lit_bar(d, bx0, yy, bx1, base, bc, a); g.rectangle([bx0, yy, bx1, base], outline=A(bc, a * 0.7), width=6)
            txt(d, (bx0 + bx1) / 2, base + 14, lab, f(MONOB, 22), CREAM, a, 'ma')
        if ci == 1 and t >= 63.32: tri(d, cx0 + 120, top - 40, 16, GREEN, appear(t, 63.4), up=False)
        if t >= 67.58:
            b = appear(t, 67.58)
            if ci == 0: tag(d, g, cx0 + 230, top - 74, 'SPIKE', RED, 28, b)
            else: tag(d, g, cx0 + 216, 1040, 'IN RANGE', GREEN, 26, b)
    if t >= 64.14:
        p = expo((t - 64.14) / 0.14); y = lerp(500, 590, p); lab = 'SAME DOSE'; fn = f(BEB, 78); w = d.textlength(lab, font=fn)
        lit_bar(d, 540 - w / 2 - 30, y, 540 + w / 2 + 30, y + 84, VGOLD, p); g.rectangle([540 - w / 2 - 34, y - 4, 540 + w / 2 + 34, y + 88], outline=A(VGOLD, p), width=10)
        txt(d, 540, y + 44, lab, fn, INK, p, 'mm')

# S12 · bloodwork route on top of a body-composition foundation slab
ROUTE = [(160, 1080), (300, 960), (450, 1010), (620, 830), (790, 880), (930, 700)]
def s12(d, g, t, lay):
    a = appear(t, 68.30, 0.2)
    txt(d, 96, 586, '——', f(BAR, 40), GOLD, a); txt(d, 164, 588, 'BLOODWORK · THE ROUTE', f(BAR, 38), GOLD, a)
    for k in range(9): d.line([(100 + k * 110, 660), (100 + k * 110, 1130)], fill=A(CYAN, 0.10 * a), width=1)
    for k in range(5): d.line([(100, 660 + k * 117), (980, 660 + k * 117)], fill=A(CYAN, 0.10 * a), width=1)
    p = clamp((t - 69.00) / 1.0) * (len(ROUTE) - 1)
    for i in range(len(ROUTE) - 1):
        if p > i:
            q = min(1, p - i); s = ROUTE[i]; e = ROUTE[i + 1]; m = (lerp(s[0], e[0], q), lerp(s[1], e[1], q))
            d.line([s, m], fill=A(CYAN), width=7); g.line([s, m], fill=A(CYAN), width=14)
    for k, i in enumerate((1, 3, 5)):
        if p >= i:
            b = appear(t, 69.0 + i / 5 * 1.0, 0.14); x, y = ROUTE[i]; s = lerp(0.5, 1, b)
            d.ellipse([x - 18 * s, y - 52 * s, x + 18 * s, y - 16 * s], fill=A(RED, b)); d.polygon([(x - 17 * s, y - 30 * s), (x + 17 * s, y - 30 * s), (x, y)], fill=A(RED, b))
            g.ellipse([x - 22, y - 56, x + 22, y - 12], fill=A(RED, b))
            txt(d, x + 24, y - 54, 'LABS %d' % (k + 1), f(MONOB, 22), CREAM, b)
    dot(d, g, *ROUTE[0], 10, CYAN, a)
    # slab falls, lands heavy
    if t >= 70.28:
        q = ease_in(clamp((t - 70.28) / 0.22)); dy = lerp(-900, 0, q)
        X0, X1, T0, F0, F1 = 90, 990, 1190, 1240, 1400
        top = [(X0 + 40, T0 + dy), (X1 + 40, T0 + dy), (X1, F0 + dy), (X0, F0 + dy)]
        d.polygon(top, fill=A(mix(VGOLD, WHITE, 0.25))); lit_bar(d, X0, F0 + dy, X1, F1 + dy, VGOLD, 1)
        d.polygon([(X1, F0 + dy), (X1 + 40, T0 + dy), (X1 + 40, F1 - 50 + dy), (X1, F1 + dy)], fill=A(dim(VGOLD, 0.55)))
        g.rectangle([X0 - 4, T0 + dy - 4, X1 + 44, F1 + dy + 4], outline=A(VGOLD), width=10)
        txt(d, (X0 + X1) / 2, (F0 + F1) / 2 + dy, 'BODY COMPOSITION', f(BEB, 100), INK, 1, 'mm')
        if t >= 70.50:
            r = expo((t - 70.5) / 0.4); al = 1 - clamp((t - 70.5) / 0.5)
            for side in (-1, 1):
                d.line([(540 + side * 470 * (0.6 + 0.4 * r), F1 + 10), (540 + side * 470 * (0.6 + 0.4 * r) + side * 60 * r, F1 + 10)], fill=A(CREAM, al), width=4)
    if t >= 72.06:
        b = appear(t, 72.06); w = tagw(d, 'BUILD THIS FIRST', 32); tag(d, g, 540 - w / 2, 1420, 'BUILD THIS FIRST', VGOLD, 32, b)

# S13 · CTA: comment box typing the keyword
LOGO = None
def s13(d, g, t, lay):
    global LOGO
    if LOGO is None:
        lg = Image.open(WD + 'logo.jpg').convert('RGB'); s = min(lg.size)
        lg = lg.crop(((lg.width - s) // 2, (lg.height - s) // 2, (lg.width + s) // 2, (lg.height + s) // 2)).resize((170, 170), Image.LANCZOS)
        m = Image.new('L', (170, 170), 0); ImageDraw.Draw(m).ellipse([0, 0, 169, 169], fill=255); lg.putalpha(m); LOGO = lg
    a = appear(t, 73.05, 0.2)
    lg = LOGO.copy(); lg.putalpha(lg.split()[3].point(lambda v: int(v * a))); lay.alpha_composite(lg, (96, 640))
    d.ellipse([94, 638, 268, 812], outline=A(GOLD, a), width=3)
    txt(d, 296, 652, 'COACH AGZ', f(BEB, 64), GOLD, a); txt(d, 298, 722, '@coach.agz', f(MONO, 28), GOLD, a)
    if t >= 74.08: txt(d, 96, 850, 'FREE · FULL ESTROGEN FRAMEWORK', f(MONOB, 30), VGOLD, appear(t, 74.08))
    if t >= 75.30: txt(d, 96, 894, '+ PROTOCOL', f(MONOB, 30), VGOLD, appear(t, 75.30))
    # comment box
    by0, by1 = 970, 1070; b = appear(t, 73.4, 0.2)
    posted = t >= 77.30
    d.rounded_rectangle([96, by0, 984, by1], radius=50, fill=A((18, 20, 28), 0.96 * b), outline=A(GREEN if posted else (96, 100, 118), b), width=3)
    if posted: g.rounded_rectangle([96, by0, 984, by1], radius=50, outline=A(GREEN, 1 - clamp((t - 77.3) / 0.8)), width=10)
    word = 'ESTROGEN'; n = 0 if t < 76.42 else min(len(word), int((t - 76.42) / (77.20 - 76.42) * len(word)) + 1)
    if n == 0: txt(d, 140, by0 + 28, 'Add a comment...', f(DMR, 40), MUTED2, b)
    else:
        txt(d, 140, by0 + 24, word[:n], f(DMB, 44), WHITE, b)
        if int(t * 3) % 2 == 0 and not posted:
            cw = d.textlength(word[:n], font=f(DMB, 44)); d.line([(144 + cw, by0 + 26), (144 + cw, by0 + 76)], fill=A(VGOLD), width=3)
    sc = VGOLD if n == len(word) else (70, 74, 90)
    d.ellipse([904, by0 + 14, 976, by1 - 14], fill=A(sc, b)); arrow(d, 920, by0 + 50, 958, by0 + 50, INK if n == len(word) else (30, 32, 40), 5, b, 14)
    if posted: check(d, g, 830, by0 + 32, GREEN, 1.0, appear(t, 77.30))
    # big keyword pill on "comment"
    if t >= 75.88:
        p = expo((t - 75.88) / 0.12); s = lerp(1.12, 1.0, p); fn = f(BEB, int(104 * s)); lab = 'COMMENT  "ESTROGEN"'; tw = d.textlength(lab, font=fn)
        x = 540 - (tw + 60) / 2; y = 1110
        lit_bar(d, x, y, x + tw + 60, y + int(118 * s), VGOLD, p); g.rectangle([x - 4, y - 4, x + tw + 64, y + int(118 * s) + 4], outline=A(VGOLD, p), width=12)
        txt(d, x + 30, y + 10, lab, fn, INK, p)
    if t >= 78.00: txt(d, 96, 1270, '→ SENT TO YOUR DMs', f(MONOB, 30), CREAM, appear(t, 78.00))
    if t >= 79.22: tag(d, g, 760, 1258, 'FREE', GREEN, 40, appear(t, 79.22))
    txt(d, 540, 1390, 'FOR RESEARCH & EDUCATIONAL PURPOSES ONLY', f(MONO, 20), MUTED2, a, 'ma')

# mode: panel (frosted box + chrome) | push (blur+darken footage) | ar (light dim) | navy (PIP scene) | full (wipe)
SC = [
    dict(t0=4.10, t1=8.30, fn=s1, mode='panel', box=P_OUT, hdr=('E2 · ESTRADIOL', 'LIVE'), acc=CYAN, enter='scale', dark=0.62),
    dict(t0=8.40, t1=11.5667, fn=s2, mode='ar', dark=0.22, enter='none', hard=True),
    dict(t0=12.40, t1=16.1333, fn=s3, mode='push', dark=0.55, blur=6, enter='none', hard=True),
    dict(t0=16.20, t1=21.2, fn=s4, mode='ar', dark=0.12, enter='none', hard=True),
    dict(t0=21.2, t1=30.1667, fn=s5, mode='navy', enter='none', hard=True),
    dict(t0=31.50, t1=38.4167, fn=s6, mode='panel', box=P_CAR, hdr=None, acc=VGOLD, enter='drop', hard=True, dark=0.62),
    dict(t0=38.4167, t1=43.05, fn=s7, mode='push', dark=0.80, blur=16, enter='none', hard=True),
    dict(t0=43.05, t1=44.5333, fn=s8, mode='full', enter='none', hard=True),
    dict(t0=44.5333, t1=53.95, fn=s9, mode='panel', box=P_CAR, hdr=('THE FIX', '3 STEPS'), acc=VGOLD, enter='wipe', dark=0.62),
    dict(t0=54.05, t1=60.50, fn=s10, mode='panel', box=P_CAR, hdr=('DIAL-IN', 'DOSE RANGE'), acc=CYAN, enter='rise', dark=0.62),
    dict(t0=60.80, t1=68.10, fn=s11, mode='push', dark=0.74, blur=14, enter='none'),
    dict(t0=68.25, t1=72.95, fn=s12, mode='push', dark=0.72, blur=14, enter='none'),
    dict(t0=73.00, t1=99.0, fn=s13, mode='panel', box=(56, 610, 1024, 1440), hdr=None, acc=VGOLD, enter='rise', dark=0.55),
]
def s6_hdr(t): return ('INPUT · DOSE', '01') if t < 35.6333 else ('AROMATASE', '02')
SHAKES = [(7.50, 9), (15.58, 10), (32.20, 6), (37.80, 10), (70.50, 12), (75.88, 5)]

# =====================================================================
# text hook, topic band, captions
# =====================================================================
def text_hook(im, t):
    if t >= HOOK_END: return
    s = lerp(1.0, 1.04, t / HOOK_END)
    L1 = [('High ', WHITE), ('ESTROGEN', VGOLD)]; L2 = [('fix this before an AI', WHITE)]
    fn = f(DMB, 80)
    tmp = ImageDraw.Draw(im)
    ws = [sum(tmp.textlength(s_, font=fn) for s_, _ in L) for L in (L1, L2)]
    bw = max(ws) + 80; bh = 2 * 96 + 50
    lay = Image.new('RGBA', (int(bw), int(bh)), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    d.rounded_rectangle([0, 0, bw - 1, bh - 1], radius=26, fill=(0, 0, 0, 214))
    for li, L in enumerate((L1, L2)):
        x = (bw - ws[li]) / 2; y = 22 + li * 96
        for s_, c in L: d.text((x, y), s_, font=fn, fill=A(c)); x += d.textlength(s_, font=fn)
    lay = lay.resize((int(bw * s), int(bh * s)), Image.BICUBIC)
    im.alpha_composite(lay, (int(540 - lay.width / 2), int(300 - (lay.height - bh) / 2)))
def band(im, t):
    if not (BAND[0] <= t < BAND[1]): return
    a = clamp((t - BAND[0]) / 0.15)
    d = ImageDraw.Draw(im, 'RGBA')
    d.rectangle([8, 212, W, 372], fill=NAVY + (int(228 * a),))
    d.line([(64, 244), (108, 244)], fill=A(GOLD, a), width=4); d.text((122, 228), '@coach.agz', font=f(MONO, 28), fill=A(GOLD, a))
    fn = f(BAR, 86); x = 64; y = 262
    for s_, c in [('High ', CREAM), ('ESTROGEN', VGOLD), ('  the real fix', CREAM)]:
        d.text((x, y), s_, font=fn, fill=A(c, a)); x += d.textlength(s_, font=fn)

FIX = {'nolvodex': 'NOLVADEX', 'fucking': 'F*CKING', 'shit': 'SH*T'}
def cap_y(t): return 1398 if t < CAR_T else 392
def build_groups():
    G = []; cur = []
    bounds = sorted(CUTS + [CAR_T])
    def nb(t):
        for b in bounds:
            if b > t + 0.01: return b
        return 1e9
    for i, x in enumerate(WORDS):
        if cur:
            prev = WORDS[cur[-1]]
            if len(cur) >= 3 or x['s'] - prev['e'] > 0.28 or prev['w'][-1] in '.,?!' or x['s'] >= nb(WORDS[cur[0]]['s']): G.append(cur); cur = []
        cur.append(i)
    if cur: G.append(cur)
    return G
GROUPS = build_groups()
def group_at(t):
    lo = None
    for gi, gr in enumerate(GROUPS):
        if WORDS[gr[0]]['s'] <= t + 1e-6: lo = gi
        else: break
    if lo is None: return None
    gr = GROUPS[lo]; end = WORDS[gr[-1]]['e'] + 0.6
    if lo + 1 < len(GROUPS): end = min(end, WORDS[GROUPS[lo + 1][0]]['s'])
    if t > end: return None
    return gr
def captions(im, t):
    gr = group_at(t)
    if not gr: return
    d = ImageDraw.Draw(im, 'RGBA')
    ws = [FIX.get(WORDS[i]['w'].lower().strip('.,?!'), WORDS[i]['w']).upper().rstrip('.,?!') for i in gr]
    size = 118
    while True:
        fn = f(BEB, size); sp = d.textlength(' ', font=fn) + 14; wd = [d.textlength(w, font=fn) for w in ws]; tot = sum(wd) + sp * (len(ws) - 1)
        if tot <= 900: break
        size -= 4
    xs = []; x = (W - tot) / 2
    for w_ in wd: xs.append(x); x += w_ + sp
    act = 0
    for k, i in enumerate(gr):
        if WORDS[i]['s'] <= t: act = k
    g0 = WORDS[gr[0]]['s']; s = lerp(0.9, 1, expo((t - g0) / 0.10))
    cap = Image.new('RGBA', (W, 260), (0, 0, 0, 0)); cd = ImageDraw.Draw(cap); shd = Image.new('RGBA', (W, 260), (0, 0, 0, 0)); sd = ImageDraw.Draw(shd)
    prev = max(0, act - 1); bt = expo((t - WORDS[gr[act]]['s']) / 0.07) if act > 0 else 1
    bx0 = lerp(xs[prev], xs[act], bt) - 16; bx1 = lerp(xs[prev] + wd[prev], xs[act] + wd[act], bt) + 16
    for k, (w_, x_) in enumerate(zip(ws, xs)): sd.text((x_ + 4, 46), w_, font=fn, fill=(0, 0, 0, 220))
    cap.alpha_composite(shd.filter(ImageFilter.GaussianBlur(6)))
    lit_bar(cd, bx0, 40 + size * 0.02, bx1, 40 + size * 0.98, RED)
    for k, (w_, x_) in enumerate(zip(ws, xs)): cd.text((x_, 40), w_, font=fn, fill=CREAM, stroke_width=0 if k == act else 3, stroke_fill=(0, 0, 0))
    cy = cap_y(t)
    if abs(s - 1) > 0.002:
        cap = cap.resize((int(W * s), int(260 * s)), Image.BICUBIC); ox = int((W - cap.width) / 2); oy = int(cy - 40 - (cap.height - 260) / 2)
    else: ox, oy = 0, cy - 40
    im.alpha_composite(cap, (ox, oy))

# =====================================================================
# compositing
# =====================================================================
def frosted(im, box, dark=0.86, blur=10, alpha=1.0):
    x0, y0, x1, y1 = [int(round(v)) for v in box]; x0 = max(0, x0); y0 = max(0, y0); x1 = min(W, x1); y1 = min(H, y1)
    if x1 <= x0 or y1 <= y0 or alpha <= 0: return
    reg = im.crop((x0, y0, x1, y1)).convert('RGB')
    out = Image.blend(reg.filter(ImageFilter.GaussianBlur(blur)), Image.new('RGB', reg.size, DEEP), dark)
    if alpha < 1: out = Image.blend(reg, out, alpha)
    im.paste(out.convert('RGBA'), (x0, y0))
def seg_of(t): return sum(1 for c in CUTS if c <= t + 1e-6)
def active(t):
    for sc in SC:
        if sc['t0'] <= t < sc['t1'] + (0 if sc.get('hard') else 0.18): return sc
    return None
NAVYBG = None
def navy_bg():
    global NAVYBG
    if NAVYBG is None:
        yy, xx = np.mgrid[0:H, 0:W]; r = np.sqrt((xx - 1000) ** 2 + (yy - 200) ** 2) / 1400
        k = np.clip(1 - r, 0, 1) ** 2
        arr = np.stack([NAVY[i] + (np.array([46, 40, 30])[i] - NAVY[i]) * k for i in range(3)], -1)
        NAVYBG = Image.fromarray(arr.astype(np.uint8)).convert('RGBA')
    return NAVYBG.copy()
def bloom(im, glow):
    if not glow.getbbox(): return im
    sm = glow.resize((W // 4, H // 4), Image.BILINEAR)
    g1 = np.asarray(sm.filter(ImageFilter.GaussianBlur(3.5))).astype(np.float32) / 255; g2 = np.asarray(sm.filter(ImageFilter.GaussianBlur(10))).astype(np.float32) / 255
    prem = np.clip(g1[..., :3] * g1[..., 3:] * 2.0 + g2[..., :3] * g2[..., 3:] * 1.6, 0, 1)
    prem = np.asarray(Image.fromarray((prem * 255).astype(np.uint8)).resize((W, H), Image.BILINEAR)).astype(np.float32) / 255
    b = np.asarray(im.convert('RGB')).astype(np.float32) / 255
    return Image.fromarray(((1 - (1 - b) * (1 - prem)) * 255).astype(np.uint8)).convert('RGBA')

def frame(src, t):
    z = 1.0 if seg_of(t) % 2 == 0 else 1.08
    if z != 1.0:
        big = src.resize((int(W * z), int(H * z)), Image.BICUBIC); ox = (big.width - W) // 2; oy = int((big.height - H) * 0.6); src = big.crop((ox, oy, ox + W, oy + H))
    sc = active(t)
    FROST.clear()
    glow = Image.new('RGBA', (W, H), (0, 0, 0, 0)); G = ImageDraw.Draw(glow, 'RGBA')
    # ---------- background ----------
    gpush = 0
    if sc and sc['mode'] in ('panel', 'push', 'ar'):
        gin = ease_io((t - sc['t0'] + 0.04) / 0.26); gout = 1 if sc.get('hard') else 1 - ease_io((t - sc['t1']) / 0.18)
        gpush = min(gin, gout)
    bg = src
    if sc and gpush > 0 and sc['mode'] in ('panel', 'push'):
        bl = sc.get('blur', 18)
        bg = Image.blend(src, src.filter(ImageFilter.GaussianBlur(bl)), gpush)
    im = bg.convert('RGBA')
    if sc and gpush > 0:
        im.alpha_composite(Image.new('RGBA', (W, H), (5, 8, 16, int(255 * sc.get('dark', 0.6) * gpush))))
    if sc and sc['mode'] == 'navy':
        q = expo((t - 21.2) / 0.38) if t < 29.80 else 1 - ease_io((t - 29.80) / 0.34)
        fx, fy = 480, 980; tx, ty, r = 836, 600, 182
        s = lerp(1, 0.42, q); ax, ay = lerp(fx, tx, q), lerp(fy, ty, q)
        fr = src.resize((max(1, int(W * s)), max(1, int(H * s))), Image.BICUBIC).convert('RGBA'); ox, oy = int(ax - fx * s), int(ay - fy * s)
        box = (lerp(0, tx - r, q), lerp(0, ty - r, q), lerp(W, tx + r, q), lerp(H, ty + r, q)); rad = lerp(0, r, q)
        canvas = navy_bg(); layer = Image.new('RGBA', (W, H), (0, 0, 0, 0)); layer.alpha_composite(fr, (max(0, ox), max(0, oy)), (max(0, -ox), max(0, -oy)))
        m = Image.new('L', (W, H), 0); ImageDraw.Draw(m).rounded_rectangle(box, radius=rad, fill=255)
        canvas.paste(layer, (0, 0), m); im = canvas
        if q > 0.02:
            d0 = ImageDraw.Draw(im, 'RGBA'); d0.rounded_rectangle(box, radius=rad, outline=A(VGOLD, q), width=6); G.rounded_rectangle(box, radius=rad, outline=A(VGOLD, q), width=12)
    if sc and sc['mode'] == 'full':
        p = expo((t - sc['t0']) / 0.32); xw = p * W
        nb = navy_bg(); m = Image.new('L', (W, H), 0); ImageDraw.Draw(m).rectangle([0, 0, xw, H], fill=255); im.paste(nb, (0, 0), m)
        d0 = ImageDraw.Draw(im, 'RGBA')
        if p < 0.999: d0.rectangle([xw - 8, 0, xw, H], fill=A(GOLD)); G.rectangle([xw - 10, 0, xw + 2, H], fill=A(VGOLD))
    # ---------- scene content ----------
    if sc:
        lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay, 'RGBA')
        sg = Image.new('RGBA', (W, H), (0, 0, 0, 0)); g = ImageDraw.Draw(sg, 'RGBA')
        pin = 1.0; pout = 0.0
        if sc['mode'] == 'panel':
            pin = expo((t - sc['t0']) / 0.22)
            if not sc.get('hard'): pout = clamp((t - sc['t1']) / 0.16)
        al = pin * (1 - pout)
        sc['fn'](d, g, t, lay)
        # entrance transforms
        dx = dy = 0; sca = 1.0; blur = 0; wipe = None
        en = sc.get('enter', 'none')
        if en == 'scale': sca = lerp(1.05, 1.0, pin) * lerp(1, 1.03, pout); blur = 8 * (1 - pin)
        elif en == 'drop': dy = lerp(-90, 0, pin); blur = 6 * (1 - pin)
        elif en == 'rise': dy = lerp(70, 0, pin) + 30 * pout; blur = 8 * (1 - pin)
        elif en == 'wipe': wipe = pin
        box = sc.get('box')
        if sc['mode'] == 'panel' and al > 0:
            x0, y0, x1, y1 = box; cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
            bx = (cx + (x0 - cx) * sca + dx, cy + (y0 - cy) * sca + dy, cx + (x1 - cx) * sca + dx, cy + (y1 - cy) * sca + dy)
            if wipe is not None: bx = (bx[0], bx[1], lerp(bx[0], bx[2], wipe), bx[3])
            frosted(im, bx, 0.90, 8, al)
        for (fb, dk, bl, fa) in FROST: frosted(im, fb, dk, bl, fa * al)
        def tf(L):
            if sca != 1.0:
                L2 = L.resize((int(W * sca), int(H * sca)), Image.BICUBIC); c = Image.new('RGBA', (W, H), (0, 0, 0, 0))
                ox = int((W - L2.width) / 2); oy = int((box[1] + box[3]) / 2 * (1 - sca)) if box else int((H - L2.height) / 2)
                c.alpha_composite(L2, (max(0, ox), max(0, oy)), (max(0, -ox), max(0, -oy))); L = c
            if dy or dx:
                c = Image.new('RGBA', (W, H), (0, 0, 0, 0)); c.alpha_composite(L, (0, max(0, int(dy))), (0, max(0, -int(dy)))); L = c
            if blur > 0.3: L = L.filter(ImageFilter.GaussianBlur(blur))
            if wipe is not None:
                m = Image.new('L', (W, H), 0); ImageDraw.Draw(m).rectangle([0, 0, box[0] + (box[2] - box[0]) * wipe, H], fill=255)
                L.putalpha(Image.fromarray(np.minimum(np.asarray(L.split()[3]), np.asarray(m))))
            if al < 1: L.putalpha(L.split()[3].point(lambda v: int(v * al)))
            return L
        if sc['mode'] == 'panel' and al > 0:
            x0, y0, x1, y1 = box; acc = sc['acc']; hdr = sc['hdr'] if sc['fn'] is not s6 else s6_hdr(t)
            d.rectangle([x0, y0, x1, y1], outline=A(acc, 0.75), width=3); brackets(d, x0, y0, x1, y1, A(acc), 48, 7)
            g.rectangle([x0, y0, x1, y1], outline=A(acc, 0.45), width=6); brackets(g, x0, y0, x1, y1, A(acc), 48, 14)
            if hdr:
                d.ellipse([x0 + 26, y0 + 26, x0 + 42, y0 + 42], fill=A(RED, 1 if int(t * 4) % 2 == 0 else 0.35))
                txt(d, x0 + 56, y0 + 18, hdr[0], f(MONOB, 28), WHITE); fr = f(MONOB, 28); tw = d.textlength(hdr[1], font=fr); txt(d, x1 - 30 - tw, y0 + 18, hdr[1], fr, acc)
        im.alpha_composite(tf(lay)); glow.alpha_composite(tf(sg))
    # ---------- hook, band, bloom, rule, captions ----------
    text_hook(im, t)
    im = bloom(im, glow)
    d = ImageDraw.Draw(im, 'RGBA'); d.rectangle([0, 0, 7, H], fill=GOLD)
    band(im, t)
    captions(im, t)
    out = im.convert('RGB')
    for (ts, amp) in SHAKES:
        k = round((t - ts) * FPS)
        if k in (0, 1, 2):
            dxs = [amp, -amp * 0.55, amp * 0.25][k]; zz = 1.02
            big = out.resize((int(W * zz), int(H * zz)), Image.BICUBIC); ox = int((big.width - W) / 2 - dxs); oy = (big.height - H) // 2
            out = big.crop((ox, oy, ox + W, oy + H)); ImageDraw.Draw(out).rectangle([0, 0, 7, H], fill=GOLD)
    return out

if __name__ == '__main__':
    mode = sys.argv[2]
    if mode == 'stills':
        import os; os.makedirs(WD + 'qc', exist_ok=True)
        for tt in [float(x) for x in sys.argv[3:]]:
            n = int(round(tt * FPS))
            subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', WD + 'assembled.mov', '-vf', f'select=eq(n\\,{n})', '-vsync', '0', '-frames:v', '1', WD + 'qc/_src.png'])
            frame(Image.open(WD + 'qc/_src.png').convert('RGB'), n / FPS).resize((540, 960), Image.LANCZOS).save(WD + f'qc/st_{tt:06.2f}.jpg', quality=88)
        sys.exit()
    n0, n1, out = int(sys.argv[3]), int(sys.argv[4]), sys.argv[5]
    dec = subprocess.Popen(['ffmpeg', '-v', 'error', '-ss', f'{n0 / FPS:.4f}', '-i', WD + 'assembled.mov', '-frames:v', str(n1 - n0), '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], stdout=subprocess.PIPE)
    enc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                            '-c:v', 'libx264', '-crf', '17', '-preset', 'slow', '-profile:v', 'high', '-level', '4.2', '-pix_fmt', 'yuv420p', '-g', '60', out], stdin=subprocess.PIPE)
    for n in range(n0, n1):
        buf = dec.stdout.read(W * H * 3)
        if len(buf) < W * H * 3: print('short', n); break
        enc.stdin.write(frame(Image.frombuffer('RGB', (W, H), buf), n / FPS).tobytes())
    enc.stdin.close(); enc.wait(); dec.kill(); print('done', n0, n1)
