# Full test 02: "E2 / body fat" Reel, 1080x1920 30 fps.
# usage: python3 render_e2.py <scratch_dir> <chunk_index> <n_chunks>   (writes <scratch>/chunk_<i>.mp4)
#        python3 render_e2.py <scratch_dir> still <out_t> <out.jpg>
# All overlay event times are SOURCE times (word timestamps); each output frame maps back to its source time.
import json, subprocess, sys, math, os
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops

S = sys.argv[1]; F = S + '/fonts/'; HERE = os.path.dirname(os.path.abspath(__file__))
SRC = S + '/src/e2.mov'
W, H = 1080, 1920; FPS = 30; SFPS = 60
WORDS = json.load(open(HERE + '/words.json'))
TRIM = json.load(open(HERE + '/trim.json'))['remove']
FACE = json.load(open(HERE + '/face_track.json'))
LOGO_P = HERE + '/../../brand/logo/coach-agz-logo-round.jpg'

# ---------- palette (BRAND.md + test-06 overlay accents) ----------
GOLD = (201, 169, 110); CREAM = (244, 241, 234); NAVY = (14, 17, 23)
RED = (255, 34, 28); VGOLD = (255, 194, 26); CYAN = (0, 229, 255); GREEN = (30, 255, 110)
DEEP = (2, 3, 8); INK = (6, 8, 14); WHITE = (255, 255, 255); MUTED = (124, 124, 130); COARED = (210, 10, 20)
MONO = 'JBMono-500.ttf'; MONOB = 'JBMono-700.ttf'; BEB = 'BebasNeue.ttf'; DMB = 'DMSans-700.ttf'; DMR = 'DMSans-400.ttf'
BAR = 'BarlowC-800.ttf'; BAR6 = 'BarlowC-600.ttf'
_fc = {}
def f(n, s):
    k = (n, int(s))
    if k not in _fc: _fc[k] = ImageFont.truetype(F + n, int(s))
    return _fc[k]
def clamp(x, a=0, b=1): return max(a, min(b, x))
def expo(x): x = clamp(x); return 1 if x >= 1 else 1 - 2 ** (-10 * x)
def ease_io(x): x = clamp(x); return 4 * x ** 3 if x < .5 else 1 - (-2 * x + 2) ** 3 / 2
def back(x, k=1.2): x = clamp(x); return 1 + (k + 1) * (x - 1) ** 3 + k * (x - 1) ** 2   # used only for heavy landings (small overshoot)
def lerp(a, b, t): return a + (b - a) * t
def A(c, a): return tuple(c[:3]) + (int(clamp(a) * 255),)
def appear(t, t0, dur=0.16): return expo((t - t0) / dur)
def window(t, t0, t1, fin=0.18, fout=0.16): return min(expo((t - t0) / fin), 1 - clamp((t - t1) / fout))

# ---------- timeline mapping ----------
def out_to_src(tau):
    t = tau
    for a, b in TRIM:
        if t >= a - 1e-9: t += (b - a)
        else: break
    return t
def src_to_out(t):
    return t - sum(min(b, t) - a for a, b in TRIM if a < t)
N = int(round(src_to_out(31.45) * FPS))
CUTS = [a for a, b in TRIM]   # source times where a jump cut lands (start of removed span)
def seg_of(t):
    return sum(1 for a, b in TRIM if t >= b - 1e-9)

# ---------- face track (smoothed) ----------
_ft = np.array(FACE, float)
def face(t):
    x = np.interp(t, _ft[:, 0], _ft[:, 1]); y = np.interp(t, _ft[:, 0], _ft[:, 2]); w = np.interp(t, _ft[:, 0], _ft[:, 3])
    return x, y, w   # haar box: brow..chin, square

GL = None   # glow layer (bloom), set per frame
# ---------- primitives ----------
def comp(im, layer, pos=(0, 0)):
    im.paste(layer, (int(pos[0]), int(pos[1])), layer)
def txt(d, x, y, s, font, col, a=1.0, anchor=None):
    d.text((x, y), s, font=font, fill=A(col, a), anchor=anchor)
def brackets(d, x0, y0, x1, y1, col, L=34, w=4):
    for (cx, cy, sx, sy) in [(x0, y0, 1, 1), (x1, y0, -1, 1), (x0, y1, 1, -1), (x1, y1, -1, -1)]:
        d.line([(cx, cy), (cx + sx * L, cy)], fill=col, width=w); d.line([(cx, cy), (cx, cy + sy * L)], fill=col, width=w)
def lit_bar(d, x0, y0, x1, y1, col, a=1.0):
    h = max(1, int(y1 - y0))
    if x1 <= x0: return
    for i in range(h):
        k = i / h; c = tuple(int(min(255, v * (1.18 - 0.36 * k) + (40 if k < 0.12 else 0))) for v in col)
        d.line([(x0, y0 + i), (x1, y0 + i)], fill=c + (int(255 * a),))
def tag(d, x, y, label, col=RED, size=30, a=1.0, glow=True, fg=None):
    fn = f(MONOB, size); tw = d.textlength(label, font=fn); h = size + 16
    lit_bar(d, x, y, x + tw + 24, y + h, col, a)
    d.text((x + 12, y + 6), label, font=fn, fill=A(fg or (INK if col in (VGOLD, GREEN, CYAN) else WHITE), a))
    if GL and glow: GL.rectangle([x - 4, y - 4, x + tw + 28, y + h + 4], outline=A(col, a), width=8)
    return x + tw + 24
def frosted(im, box, dark=0.86, blur=10, r=0):
    x0, y0, x1, y1 = [int(v) for v in box]
    x0 = max(0, x0); y0 = max(0, y0); x1 = min(W, x1); y1 = min(H, y1)
    if x1 <= x0 or y1 <= y0: return
    reg = im.crop((x0, y0, x1, y1)).convert('RGB')
    sm = reg.resize((max(1, reg.width // 4), max(1, reg.height // 4))).filter(ImageFilter.GaussianBlur(blur / 4)).resize(reg.size)
    out = Image.blend(sm, Image.new('RGB', reg.size, DEEP), dark).convert('RGBA')
    if r:
        m = Image.new('L', reg.size, 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, reg.width - 1, reg.height - 1], radius=r, fill=255)
        im.paste(out, (x0, y0), m)
    else: im.paste(out, (x0, y0))
def hexagon(d, cx, cy, r, col, a=1.0, rot=0.0, w=5, fill=True):
    pts = [(cx + r * math.cos(math.pi / 3 * i + math.pi / 6 + rot), cy + r * math.sin(math.pi / 3 * i + math.pi / 6 + rot)) for i in range(6)]
    if fill: d.polygon(pts, fill=A((10, 14, 24), 0.95 * a))
    d.line(pts + [pts[0]], fill=A(col, a), width=w, joint='curve')
    if GL: GL.line(pts + [pts[0]], fill=A(col, a * 0.9), width=w * 2)
    return pts
def arrow(d, x0, y0, x1, y1, col, w=5, a=1.0, L=18):
    d.line([(x0, y0), (x1, y1)], fill=A(col, a), width=w)
    ang = math.atan2(y1 - y0, x1 - x0)
    d.polygon([(x1, y1), (x1 - L * math.cos(ang - 0.45), y1 - L * math.sin(ang - 0.45)), (x1 - L * math.cos(ang + 0.45), y1 - L * math.sin(ang + 0.45))], fill=A(col, a))
def check(d, x, y, col, s=1.0, a=1.0):
    pts = [(x, y + 16 * s), (x + 10 * s, y + 28 * s), (x + 30 * s, y + 2 * s)]
    d.line(pts, fill=A(col, a), width=int(6 * s), joint='curve')
    if GL: GL.line(pts, fill=A(col, a), width=int(12 * s))
def padlock(d, x, y, col, a=1.0, s=1.0, open_=0.0):
    d.rounded_rectangle([x, y + 22 * s, x + 44 * s, y + 58 * s], radius=6, fill=A(col, a))
    sh = -14 * s * open_
    d.arc([x + 7 * s, y + sh, x + 37 * s, y + 40 * s + sh], 180, 360, fill=A(col, a), width=int(6 * s))
    d.line([(x + 7 * s, y + 20 * s + sh), (x + 7 * s, y + 26 * s)], fill=A(col, a), width=int(6 * s))
    d.line([(x + 37 * s, y + 20 * s + sh), (x + 37 * s, y + 26 * s)], fill=A(col, a), width=int(6 * s))
def kicker(d, x, y, label, t, t0, col=VGOLD, a=1.0):
    p = expo((t - t0) / 0.22)
    if p <= 0: return
    d.line([(x, y + 17), (x + 46 * p, y + 17)], fill=A(col, a), width=4)
    q = clamp((t - t0 - 0.08) / 0.25); n = int(len(label) * q)
    txt(d, x + 62, y, label[:n], f(BAR6, 34), col, a)
def text_tracked(d, x, y, s, font, col, a, track):
    for ch in s:
        d.text((x, y), ch, font=font, fill=A(col, a)); x += d.textlength(ch, font=font) + track
    return x

# =====================================================================
# LAYOUT: where the footage sits (full / split-top-graphic / split-bottom-graphic)
# =====================================================================
FULL = (1.0, 0, 0, 0, 1920)                     # scale, x, y of footage top-left
SPLIT_TOP = (0.70, 162, 470, 430, 1920)  # graphic above; window starts at the cap (source y 430) -> screen y ~771
SPLIT_LOW = (0.76, 130, -150, 520, 1560)  # graphic below; window shows cap..chest, screen y ~245-1036
LAYOUT_KEYS = [  # (src_t, layout, transition s); 0 = hard cut on a jump cut
    (0.0, FULL, 0), (6.40, SPLIT_TOP, 0.34), (13.0333, FULL, 0), (20.86, SPLIT_LOW, 0.34), (24.50, FULL, 0)]
def layout(t):
    cur = LAYOUT_KEYS[0][1]
    for i, (t0, L, dur) in enumerate(LAYOUT_KEYS):
        if t >= t0:
            prev = LAYOUT_KEYS[i - 1][1] if i else L
            p = ease_io((t - t0) / dur) if dur else 1.0
            cur = tuple(lerp(a, b, p) for a, b in zip(prev, L))
    return cur
def split_amount(t):
    s = layout(t)[0]; return clamp((1 - s) / 0.24)

# punch-ins: alternate per take on full-frame shots (hides each jump cut); explicit punch on "body" (1.14)
def punch(t):
    if t < 3.6: return 1.0 if t < 1.14 else lerp(1.0, 1.06, expo((t - 1.14) / 0.12))
    if 13.02 <= t < 15.74: return 1.0     # flank meters need the full width
    return 1.0 if seg_of(t) % 2 == 1 else 1.07

# =====================================================================
# SCENES
# =====================================================================
# --- 1. text hook (frame 0) + topic band ---------------------------------
HOOK_END = 3.98
def hook(im, t, tau):
    if t >= HOOK_END + 0.15: return
    a = 1 - clamp((t - HOOK_END) / 0.15)
    s = lerp(1.0, 1.04, clamp(tau / 3.87))
    lay = Image.new('RGBA', (W, 420), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    fn = f(BAR, 104)
    L1 = [('High ', WHITE), ('ESTROGEN', VGOLD), (' on TRT', WHITE)]; L2 = [("it's not your dose", WHITE)]
    for li, line in enumerate([L1, L2]):
        tw = sum(d.textlength(s_, font=fn) for s_, _ in line); x = (W - tw) / 2; y = 40 + li * 118
        for s_, c in line:
            d.text((x + 4, y + 5), s_, font=fn, fill=(0, 0, 0, 200)); x += d.textlength(s_, font=fn)
    lay = lay.filter(ImageFilter.GaussianBlur(7)); d = ImageDraw.Draw(lay)
    for li, line in enumerate([L1, L2]):
        tw = sum(d.textlength(s_, font=fn) for s_, _ in line); x = (W - tw) / 2; y = 40 + li * 118
        for s_, c in line:
            d.text((x, y), s_, font=fn, fill=c + (255,), stroke_width=2, stroke_fill=(0, 0, 0)); x += d.textlength(s_, font=fn)
    if s != 1: lay = lay.resize((int(W * s), int(420 * s)), Image.BICUBIC)
    if a < 1: lay.putalpha(lay.split()[3].point(lambda v: int(v * a)))
    comp(im, lay, (int((W - lay.width) / 2), int(250 - (lay.height - 420) / 2)))
BAND_IN, BAND_OUT = 3.98, 15.74
def band(im, t):
    if not (BAND_IN <= t < BAND_OUT + 0.15): return
    a = min(clamp((t - BAND_IN) / 0.15), 1 - clamp((t - BAND_OUT) / 0.15))
    d = ImageDraw.Draw(im, 'RGBA'); fn = f(BAR, 50)
    parts = [('Body fat raises ', WHITE), ('ESTROGEN', VGOLD)]
    tw = sum(d.textlength(s_, font=fn) for s_, _ in parts); x0 = (W - tw) / 2 - 26; y0 = 196
    frosted(im, (x0, y0, x0 + tw + 52, y0 + 70), 0.80, 12, r=10); d = ImageDraw.Draw(im, 'RGBA')
    d.rectangle([x0, y0, x0 + 5, y0 + 70], fill=A(GOLD, a))
    x = x0 + 26
    for s_, c in parts: d.text((x, y0 + 6), s_, font=fn, fill=A(c, a)); x += d.textlength(s_, font=fn)

# --- 2. ENZYME ID card (top zone, counter + molecule) ----------------------
def enzyme_card(im, t):
    t0, t1 = 3.86, 6.40
    if not (t0 <= t < t1 + 0.4): return
    pin = expo((t - t0) / 0.22); pout = clamp((t - t1) / 0.18)
    a = pin * (1 - pout)
    x0, y0, x1, y1 = 60, 290 + 30 * (1 - pin), 1020, 545 + 30 * (1 - pin)
    if a > 0:
        frosted(im, (x0, y0, x1, y1), 0.90, 10, r=18); d = ImageDraw.Draw(im, 'RGBA')
        d.rectangle([x0, y0, x0 + 6, y1], fill=A(RED, a))        # crimson bar leads
        brackets(d, x0, y0, x1, y1, A(VGOLD, a), 30, 5)
        if GL: brackets(GL, x0, y0, x1, y1, A(VGOLD, a), 30, 10)
        txt(d, x0 + 34, y0 + 22, 'ENZYMES DOING THIS', f(MONO, 26), MUTED, a)
        # counter: 0 -> 1, lands on "one" (4.44)
        if t < 4.44: n = '0'; sc = 1.0
        else: n = '1'; sc = lerp(1.35, 1.0, expo((t - 4.44) / 0.14))
        fn = f(BEB, int(190 * sc)); tw = d.textlength(n, font=fn)
        d.text((x0 + 130 - tw / 2, y0 + 150 - 95 * sc), n, font=fn, fill=A(VGOLD if n == '1' else (90, 90, 96), a))
        if GL and n == '1': GL.text((x0 + 130 - tw / 2, y0 + 150 - 95 * sc), n, font=fn, fill=A(VGOLD, a * 0.7))
        d.line([(x0 + 262, y0 + 30), (x0 + 262, y1 - 30)], fill=A((70, 70, 80), a), width=2)
    # molecule: hexagon ring (stays to hand off into the fat cell)
    hx, hy, hr = 420, 418 + 30 * (1 - pin), 62
    if t >= t1:   # handoff: fly to the cell membrane (split layout)
        p = ease_io((t - t1) / 0.40); hx = lerp(420, 540 + math.cos(-0.5) * 175, p); hy = lerp(hy, 530 + math.sin(-0.5) * 175, p); hr = lerp(62, 34, p)
        if p >= 1: return
    ha = pin
    hexagon(ImageDraw.Draw(im, 'RGBA'), hx, hy, hr, VGOLD, ha, rot=t * 0.6, w=6)
    d = ImageDraw.Draw(im, 'RGBA')
    hexagon(d, hx, hy, hr * 0.55, CYAN, ha * 0.9, rot=-t * 0.9, w=3, fill=False)
    if a > 0 and t >= 5.62:
        b = appear(t, 5.62, 0.12) * a
        text_tracked(d, 520, y0 + 64, 'AROMATASE', f(BEB, int(lerp(96, 92, b))), CREAM, b, lerp(14, 3, expo((t - 5.62) / 0.3)))
        txt(d, 524, y0 + 168, 'GENE CYP19A1', f(MONO, 26), CYAN, appear(t, 5.80) * a)
        tag(d, 780, y0 + 162, 'CONVERTER', VGOLD, 24, appear(t, 5.95) * a)

# --- 3. FAT CELL mechanism (split screen, graphic on top) ------------------
GA = (60, 285, 1020, 790)    # graphic area in split-top layout
def cell(d, cx, cy, r, a, t, lip=1.0):
    # adipocyte: membrane ring, big lipid droplet, nucleus pushed to the edge
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=A((24, 20, 12), 0.92 * a), outline=A(CREAM, a), width=4)
    lr = r * 0.74 * lip
    d.ellipse([cx - lr - 8, cy - lr + 4, cx + lr - 8, cy + lr + 4], fill=A((255, 194, 26), 0.22 * a), outline=A(VGOLD, 0.75 * a), width=3)
    for k in range(6):   # droplet texture
        ang = k * 1.1 + 0.4; rr = lr * (0.25 + 0.12 * (k % 3))
        bx = cx - 8 + math.cos(ang) * lr * 0.45; by = cy + 4 + math.sin(ang) * lr * 0.45
        d.ellipse([bx - rr * 0.35, by - rr * 0.35, bx + rr * 0.35, by + rr * 0.35], outline=A(VGOLD, 0.25 * a), width=2)
    d.ellipse([cx + r * 0.62 - 16, cy - r * 0.55 - 12, cx + r * 0.62 + 16, cy - r * 0.55 + 12], fill=A((120, 110, 150), a))
    if GL: GL.ellipse([cx - r, cy - r, cx + r, cy + r], outline=A(VGOLD, 0.5 * a), width=6)
def particle(d, x, y, label, col, a, r=19):
    d.ellipse([x - r, y - r, x + r, y + r], fill=A(col, a))
    if GL: GL.ellipse([x - r * 1.6, y - r * 1.6, x + r * 1.6, y + r * 1.6], fill=A(col, a * 0.6))
    fn = f(MONOB, 20 if len(label) > 1 else 22); tw = d.textlength(label, font=fn)
    d.text((x - tw / 2, y - 13), label, font=fn, fill=A(INK, a))
def fat_cell_scene(im, t):
    if not (6.40 <= t < 10.92): return
    sp = split_amount(t)
    out = clamp((t - 10.62) / 0.30)          # handoff into graph
    a = clamp((t - 6.70) / 0.2) * (1 - out)
    d = ImageDraw.Draw(im, 'RGBA')
    kicker(d, 80, 300, 'WHERE IT LIVES', t, 6.55, VGOLD, sp)
    cx, cy, r = 540, 530, 175
    if out > 0:   # shrink to the first x-axis icon of the graph
        p = ease_io(out); cx = lerp(540, 250, p); cy = lerp(530, 680, p); r = lerp(175, 16, p)
    if a <= 0 and out == 0: return
    cell(d, cx, cy, r, a if out == 0 else 1.0, t)
    if out > 0: return
    if t >= 7.54:
        b = appear(t, 7.54)
        tag(d, 640, 338, 'ADIPOSE TISSUE', VGOLD, 26, b)
        d.line([(cx + r * 0.5, cy - r * 0.86), (700, 386)], fill=A(VGOLD, b * 0.8), width=2)
    # aromatase enzymes on the membrane (one arrives from the ID card)
    for k, ang in enumerate([-0.5, 0.5, 2.6]):
        ex = cx + math.cos(ang) * r; ey = cy + math.sin(ang) * r
        ea = 1.0 if k == 0 else appear(t, 7.0 + 0.12 * k)
        if k == 0 and t < 6.80: continue
        hexagon(d, ex, ey, 30, VGOLD, ea * a, rot=t * 0.8, w=4)
    # T -> aromatase -> E2 flow, starts on "converts" (8.64)
    if t >= 8.64:
        ent = (cx + math.cos(2.6) * r, cy + math.sin(2.6) * r); ex_ = (cx + math.cos(0.5) * r, cy + math.sin(0.5) * r)
        for k in range(5):
            p = ((t - 8.64) * 0.55 + k / 5) % 1
            if (t - 8.64) * 0.55 + k / 5 < 0: continue
            if p < 0.4:   # outside -> entry enzyme
                q = p / 0.4; x = lerp(80, ent[0], q); y = lerp(ent[1] + 40, ent[1], q); particle(d, x, y, 'T', CYAN, a * min(1, q * 5))
            elif p < 0.62:
                q = (p - 0.4) / 0.22; x = lerp(ent[0], ex_[0], q); y = lerp(ent[1], ex_[1], q) + math.sin(q * math.pi) * 30
                particle(d, x, y, 'T' if q < 0.5 else 'E2', CYAN if q < 0.5 else RED, a)
            else:
                q = (p - 0.62) / 0.38; x = lerp(ex_[0], 1010, q); y = lerp(ex_[1], ex_[1] + 30, q); particle(d, x, y, 'E2', RED, a * min(1, (1 - q) * 5))
        if t >= 8.96: txt(d, 80, 712, 'TESTOSTERONE', f(MONOB, 28), CYAN, appear(t, 8.96) * a)
        if t >= 9.84:
            fn = f(MONOB, 28); tw = d.textlength('ESTRADIOL', font=fn); txt(d, 1000 - tw, 712, 'ESTRADIOL', fn, RED, appear(t, 9.84) * a)

# --- 4. LINE GRAPH: body fat vs conversion (split, graph) --------------------
def curve_y(u):   # concept curve: accelerating rise
    return 0.08 + 0.80 * (u ** 1.6)
def graph_scene(im, t):
    if not (10.62 <= t < 13.0333): return
    a = clamp((t - 10.70) / 0.2)
    d = ImageDraw.Draw(im, 'RGBA')
    gx0, gy0, gx1, gy1 = 200, 370, 990, 630
    kicker(d, 80, 300, 'CONVERSION RATE', t, 10.66, VGOLD, a)
    d.line([(gx0, gy1), (gx1, gy1)], fill=A((150, 150, 160), a), width=3); d.line([(gx0, gy0), (gx0, gy1)], fill=A((150, 150, 160), a), width=3)
    for k in range(1, 4): d.line([(gx0, gy1 - k * 80), (gx1, gy1 - k * 80)], fill=A((50, 52, 64), a), width=1)
    txt(d, 80, gy0 - 6, 'E2', f(BEB, 44), RED, a); txt(d, 80, gy1 - 40, 'LOW', f(MONO, 20), MUTED, a); txt(d, 80, gy0 + 40, 'HIGH', f(MONO, 20), MUTED, a)
    # x-axis: fat cells growing (body fat), land on "higher body fat" (10.8-11.42)
    for k in range(5):
        u = k / 4; x = lerp(gx0 + 50, gx1 - 40, u); rr = lerp(16, 34, u)
        ca = 1.0 if k == 0 else appear(t, 10.80 + 0.14 * k)
        if ca <= 0: continue
        d.ellipse([x - rr, gy1 + 42 - rr, x + rr, gy1 + 42 + rr], fill=A((40, 32, 10), a * ca), outline=A(VGOLD, a * ca), width=3)
        d.ellipse([x - rr * 0.6, gy1 + 42 - rr * 0.6, x + rr * 0.6, gy1 + 42 + rr * 0.6], fill=A(VGOLD, 0.35 * a * ca))
    if t >= 11.0:
        fn = f(MONOB, 24); txt(d, gx1 - d.textlength('BODY FAT  →', font=fn), gy1 + 76, 'BODY FAT  →', fn, VGOLD, appear(t, 11.0) * a)
    # curve draws on "increases" (11.68)
    p = clamp((t - 11.68) / 0.85)
    if p > 0:
        pts = []
        for i in range(int(60 * p) + 1):
            u = i / 60; pts.append((lerp(gx0, gx1, u), gy1 - curve_y(u) * (gy1 - gy0)))
        poly = pts + [(pts[-1][0], gy1), (gx0, gy1)]
        fill = Image.new('RGBA', (W, H), (0, 0, 0, 0)); fd = ImageDraw.Draw(fill)
        fd.polygon(poly, fill=A(RED, 0.20 * a)); comp(im, fill); d = ImageDraw.Draw(im, 'RGBA')
        if len(pts) > 1:
            d.line(pts, fill=A(RED, a), width=7, joint='curve')
            if GL: GL.line(pts, fill=A(RED, a), width=14)
        hx, hy = pts[-1]
        d.ellipse([hx - 13, hy - 13, hx + 13, hy + 13], fill=A(WHITE, a))
        if GL: GL.ellipse([hx - 24, hy - 24, hx + 24, hy + 24], fill=A(RED, a))
        if t >= 12.08:
            tag(d, min(hx - 250, 700), hy - 78, 'CONVERSION ▲', RED, 26, appear(t, 12.08) * a)
    txt(d, gx0 + 10, gy1 + 76, 'CONCEPT · NOT TO SCALE', f(MONO, 20), MUTED, a * 0.9)

# --- 5. FLANKING METERS beside the face: dose locked, E2 rising --------------
def gauge(d, x0, y0, x1, y1, frac, col, a):
    d.rounded_rectangle([x0, y0, x1, y1], radius=10, outline=A((90, 92, 104), a), width=3)
    yt = lerp(y1 - 6, y0 + 6, clamp(frac))
    lit_bar(d, x0 + 6, yt, x1 - 6, y1 - 6, col, a)
    if GL: GL.rectangle([x0 + 6, yt, x1 - 6, y1 - 6], outline=A(col, a), width=6)
    for k in range(1, 5): d.line([(x0, lerp(y1, y0, k / 5)), (x0 + 14, lerp(y1, y0, k / 5))], fill=A((120, 120, 130), a), width=2)
def flank_scene(im, t):
    if not (13.10 <= t < 15.90): return
    out = clamp((t - 15.70) / 0.18)
    aL = appear(t, 13.14, 0.2) * (1 - out); aR = appear(t, 13.40, 0.2) * (1 - out)
    # left: TRT DOSE (x 34-230), right: E2 OUTPUT (x 850-1046)
    for (x0, a, slide) in [(34, aL, -1), (850, aR, 1)]:
        if a <= 0: continue
        dx = slide * 40 * (1 - a)
        frosted(im, (x0 + dx, 600, x0 + 196 + dx, 1180), 0.86, 12, r=16)
    d = ImageDraw.Draw(im, 'RGBA')
    if aL > 0:
        dx = -40 * (1 - aL); x0 = 34 + dx
        d.rectangle([x0, 600, x0 + 5, 1180], fill=A(GOLD, aL))
        txt(d, x0 + 24, 620, 'TRT', f(BEB, 52), CREAM, aL); txt(d, x0 + 24, 672, 'DOSE', f(MONOB, 26), VGOLD, aL)
        gauge(d, x0 + 46, 730, x0 + 150, 1040, 0.55, VGOLD, aL)
        lk = appear(t, 14.64, 0.12)
        padlock(d, x0 + 76, 1060, VGOLD if lk > 0 else (90, 90, 96), aL, 1.0, open_=1 - lk)
        if lk > 0: tag(d, x0 + 30, 1130, 'SAME', VGOLD, 22, lk * aL)
    if aR > 0:
        dx = 40 * (1 - aR); x0 = 850 + dx
        d.rectangle([x0 + 191, 600, x0 + 196, 1180], fill=A(RED, aR))
        txt(d, x0 + 24, 620, 'E2', f(BEB, 52), CREAM, aR); txt(d, x0 + 24, 672, 'OUTPUT', f(MONOB, 26), RED, aR)
        fr = lerp(0.35, 0.92, ease_io((t - 13.55) / 1.6))
        gauge(d, x0 + 46, 730, x0 + 150, 1040, fr, RED, aR)
        for k in range(3):   # rising chevrons
            q = ((t * 1.4) + k / 3) % 1; yy = lerp(1000, 760, q)
            d.line([(x0 + 82, yy + 14), (x0 + 98, yy), (x0 + 114, yy + 14)], fill=A(WHITE, aR * 0.7 * math.sin(q * math.pi)), width=4)
        txt(d, x0 + 22, 1066, 'BODY FAT', f(MONOB, 22), VGOLD, aR); txt(d, x0 + 22, 1096, 'DRIVEN ▲', f(MONOB, 22), RED, aR)
    # link between the two gauges snaps on "independent" (13.62)
    if aL > 0 and aR > 0:
        y = 548; brk = clamp((t - 13.62) / 0.25)
        if brk <= 0:
            d.line([(130, y), (950, y)], fill=A(VGOLD, aR * 0.8), width=4)
            for k in range(16): d.ellipse([140 + k * 52, y - 6, 152 + k * 52, y + 6], outline=A(VGOLD, aR), width=3)
        else:
            gap = 70 * expo(brk); col = RED
            d.line([(130, y + 18 * brk), (540 - gap, y + 40 * brk)], fill=A(VGOLD, aR * (1 - brk * 0.5)), width=4)
            d.line([(540 + gap, y + 40 * brk), (950, y + 18 * brk)], fill=A(VGOLD, aR * (1 - brk * 0.5)), width=4)
            if brk < 1:
                for k in range(8):
                    ang = k * 0.8; rr = 60 * brk
                    d.line([(540, y + 20), (540 + math.cos(ang) * rr, y + 20 + math.sin(ang) * rr)], fill=A(RED, 1 - brk), width=3)
            if GL: GL.ellipse([520, y, 560, y + 40], fill=A(RED, (1 - brk)))
            tag(d, 420, y - 70, 'NOT LINKED', RED, 26, appear(t, 13.70) * min(aL, aR))

# --- 6. AR body callouts: detection brackets on the subject + mood waveform ---
def callouts(im, t):
    if not (15.86 <= t < 21.05): return
    out = clamp((t - 20.86) / 0.16)
    d = ImageDraw.Draw(im, 'RGBA')
    z = punch(t); fx, fy, fw = face(t)
    def tf(x, y):   # source coords -> screen coords (full layout with punch-in about the anchor)
        return (x - 540) * z + 540, (y - 980) * z + 980
    kicker(d, 64, 290, 'HIGH E2 · SIGNS', t, 16.10, RED, 1 - out)
    rows = [(17.80, 'FLUID'), (18.78, 'TISSUE'), (19.64, 'MOOD')]
    for i, (t0, lab) in enumerate(rows):
        a = appear(t, t0, 0.12) * (1 - out)
        if a <= 0: continue
        ty = 352 + i * 66
        tag(d, 64, ty, lab, RED, 30, a)
        if i == 0:   # jaw / lower face (water retention shows as facial puffiness)
            x0, y0 = tf(fx + fw * 0.06, fy + fw * 0.70); x1, y1 = tf(fx + fw * 0.94, fy + fw * 1.08)
            brackets(d, x0, y0, x1, y1, A(RED, a), 26, 5)
            if GL: brackets(GL, x0, y0, x1, y1, A(RED, a), 26, 10)
            d.line([(x0, (y0 + y1) / 2), (40, (y0 + y1) / 2), (40, ty + 23), (64, ty + 23)], fill=A(RED, a * 0.8), width=2)
            # droplet + level gauge
            gx = 200; d.polygon([(gx + 14, ty + 4), (gx + 2, ty + 26), (gx + 26, ty + 26)], fill=A(CYAN, a)); d.ellipse([gx + 2, ty + 16, gx + 26, ty + 40], fill=A(CYAN, a))
            fr = lerp(0.3, 0.8, expo((t - t0) / 0.6)); d.rectangle([gx + 40, ty + 12, gx + 200, ty + 34], outline=A((90, 92, 104), a), width=2)
            lit_bar(d, gx + 43, ty + 15, gx + 43 + 154 * fr, ty + 31, CYAN, a)
        if i == 1:   # chest, below the caption band
            x0, y0, x1, y1 = 250, 1650, 520, 1800
            brackets(d, x0, y0, x1, y1, A(RED, a), 26, 5)
            if GL: brackets(GL, x0, y0, x1, y1, A(RED, a), 26, 10)
            d.line([(x0, (y0 + y1) / 2), (26, (y0 + y1) / 2), (26, ty + 23), (64, ty + 23)], fill=A(RED, a * 0.8), width=2)
            cx_, cy_ = 230, ty + 23   # crosshair
            d.ellipse([cx_ - 16, cy_ - 16, cx_ + 16, cy_ + 16], outline=A(RED, a), width=3); d.line([(cx_ - 24, cy_), (cx_ + 24, cy_)], fill=A(RED, a), width=2); d.line([(cx_, cy_ - 24), (cx_, cy_ + 24)], fill=A(RED, a), width=2)
            tag(d, 270, ty, 'TENDER', (60, 10, 14), 24, a, glow=False, fg=RED)
        if i == 2:   # head bracket + live mood waveform
            x0, y0 = tf(fx - fw * 0.10, fy - fw * 0.38); x1, y1 = tf(fx + fw * 1.10, fy + fw * 0.30)
            brackets(d, x0, y0, x1, y1, A(RED, a), 30, 5)
            if GL: brackets(GL, x0, y0, x1, y1, A(RED, a), 30, 10)
    # mood waveform (live line chart), top right; calm baseline from 16.1, swings on "emotional volatility"
    wa = appear(t, 16.30, 0.2) * (1 - out)
    if wa > 0:
        x0, y0, x1, y1 = 560, 350, 1016, 540
        frosted(im, (x0, y0, x1, y1), 0.85, 10, r=12); d = ImageDraw.Draw(im, 'RGBA')
        brackets(d, x0, y0, x1, y1, A(RED, wa), 22, 4)
        txt(d, x0 + 16, y0 + 10, 'MOOD · LIVE', f(MONO, 20), MUTED, wa)
        amp_on = expo((t - 19.64) / 0.5) if t >= 19.64 else 0
        pts = []
        for i in range(90):
            u = i / 89; tt = t * 2.2 - (1 - u) * 3.0
            base = math.sin(tt * 2.1) * 0.12 + math.sin(tt * 5.3) * 0.05
            spike = (math.sin(tt * 7.7) * 0.55 + math.sin(tt * 13.1) * 0.3) * amp_on * clamp(u * 1.6)
            pts.append((lerp(x0 + 16, x1 - 16, u), (y0 + y1) / 2 + 14 - (base + spike) * 70))
        d.line([(x0 + 16, (y0 + y1) / 2 + 14), (x1 - 16, (y0 + y1) / 2 + 14)], fill=A((60, 62, 74), wa), width=1)
        col = RED if amp_on > 0.3 else GREEN
        d.line(pts, fill=A(col, wa), width=4, joint='curve')
        if GL: GL.line(pts, fill=A(col, wa), width=8)
        if amp_on > 0: tag(d, x1 - 150, y1 - 50, 'UNSTABLE', RED, 20, amp_on * wa)

# --- 7. LAB REPORT (split, graphic below): desaturated scan + range bars + steps
DOC = None
def make_doc():
    w, h = 900, 470
    im = Image.new('RGB', (w, h), (238, 238, 236)); d = ImageDraw.Draw(im)
    d.rectangle([0, 0, w, 64], fill=(16, 24, 48)); d.text((24, 16), 'LAB REPORT · HORMONE PANEL', font=f(MONOB, 28), fill=WHITE)
    d.text((w - 210, 22), 'SPECIMEN: SERUM', font=f(MONO, 18), fill=(170, 176, 196))
    for i, (k, m) in enumerate([('Estradiol, Sensitive', 'LC/MS-MS'), ('Testosterone, Total', 'LC/MS-MS')]):
        y = 84 + i * 112
        d.text((24, y), k, font=f(DMB, 32), fill=(40, 44, 56)); d.text((24, y + 42), m, font=f(MONO, 18), fill=(120, 120, 130))
        d.text((24, y + 66), 'reference range', font=f(MONO, 16), fill=(140, 140, 150))
        # range track
        d.rounded_rectangle([430, y + 30, 820, y + 52], radius=11, fill=(214, 214, 212))
        d.rounded_rectangle([540, y + 30, 710, y + 52], radius=6, fill=(170, 214, 184))
        d.line([(20, y + 102), (w - 20, y + 102)], fill=(210, 210, 212), width=2)
    d.text((24, 318), 'NEXT STEP', font=f(MONO, 18), fill=(120, 120, 130))
    noise = np.random.default_rng(3).normal(0, 6, (h, w, 1))
    arr = np.clip(np.asarray(im).astype(float) + noise, 0, 255).astype(np.uint8)
    return Image.fromarray(arr).convert('RGBA')
def lab_scene(im, t):
    global DOC
    if not (20.90 <= t < 24.50): return
    if DOC is None: DOC = make_doc()
    pin = expo((t - 21.00) / 0.30); pout = 0.0
    if pin <= 0: return
    dx, dy = 90, 1010 + 380 * (1 - pin) + 0 * pout
    a = 1 - pout
    doc = DOC.copy()
    if a < 1: doc.putalpha(doc.split()[3].point(lambda v: int(v * a)))
    sh = Image.new('RGBA', (W, H), (0, 0, 0, 0)); ImageDraw.Draw(sh).rectangle([dx + 10, dy + 14, dx + 910, dy + 484], fill=(0, 0, 0, int(150 * a)))
    comp(im, sh.filter(ImageFilter.GaussianBlur(14)))
    comp(im, doc, (dx, int(dy)))
    d = ImageDraw.Draw(im, 'RGBA')
    # markers slide along the range tracks
    for i, (target, t0, col) in enumerate([(0.97, 21.30, COARED), (0.55, 21.50, (40, 44, 56))]):
        y = dy + 84 + i * 112 + 41
        p = expo((t - t0) / 0.6); u = lerp(0.05, target, p)
        x = dx + 430 + u * 390
        d.polygon([(x - 13, y - 34), (x + 13, y - 34), (x, y - 12)], fill=A(col, a))
        if i == 0 and p > 0.85:
            txt(d, dx + 836, y - 30, 'H', f(DMB, 40), COARED, a)
        if i == 1 and p > 0.85:
            txt(d, dx + 836, y - 24, '—', f(DMB, 30), (110, 110, 120), a)
    # detection bracket + CONFIRMED on "confirm" (21.76)
    if t >= 21.76:
        b = appear(t, 21.76, 0.12) * a; y0 = dy + 76; y1 = dy + 190
        brackets(d, dx + 8, y0, dx + 892, y1, A(RED, b), 30, 6)
        if GL: brackets(GL, dx + 8, y0, dx + 892, y1, A(RED, b), 30, 12)
        tag(d, dx + 620, dy - 52, 'CONFIRMED', RED, 30, b)
    # steps: 01 LABS (green check) -> 02 PROTOCOL (locked) on "before any protocol change" (22.38 / 22.96)
    sy = dy + 350
    if t >= 22.38:
        b = appear(t, 22.38) * a
        d.rounded_rectangle([dx + 24, sy, dx + 380, sy + 92], radius=12, fill=A((16, 24, 48), b))
        txt(d, dx + 44, sy + 16, '01', f(MONOB, 24), GREEN, b); txt(d, dx + 96, sy + 14, 'LABS', f(BEB, 62), WHITE, b); check(d, dx + 316, sy + 28, GREEN, 1.1, b)
        arrow(d, dx + 396, sy + 46, dx + 474, sy + 46, (60, 64, 80), 5, b)
    if t >= 22.96:
        b = appear(t, 22.96) * a
        d.rounded_rectangle([dx + 490, sy, dx + 876, sy + 92], radius=12, outline=A((60, 64, 80), b), width=4)
        txt(d, dx + 510, sy + 16, '02', f(MONOB, 24), (110, 110, 120), b); txt(d, dx + 562, sy + 14, 'PROTOCOL', f(BEB, 62), (90, 94, 110), b)
        padlock(d, dx + 812, sy + 18, (110, 110, 120), b, 0.9)

# --- 8. CTA: checklist card + FREE stamp -> COMMENT "E2" pill -> DM toast ---
LOGO = None
def logo(sz):
    global LOGO
    if LOGO is None:
        lg = Image.open(LOGO_P).convert('RGB'); s = min(lg.size)
        LOGO = lg.crop(((lg.width - s) // 2, (lg.height - s) // 2, (lg.width + s) // 2, (lg.height + s) // 2))
    lg = LOGO.resize((sz, sz), Image.LANCZOS).convert('RGBA'); m = Image.new('L', (sz, sz), 0); ImageDraw.Draw(m).ellipse([0, 0, sz - 1, sz - 1], fill=255); lg.putalpha(m)
    return lg
def cta(im, t):
    if t < 24.60: return
    # A. checklist card (24.7 -> 27.7), tilted clipboard
    if t < 27.95:
        pin = expo((t - 24.70) / 0.28); pout = clamp((t - 27.62) / 0.26)
        if pin > 0:
            cw, ch = 560, 300
            card = Image.new('RGBA', (cw, ch), (0, 0, 0, 0)); d = ImageDraw.Draw(card)
            d.rounded_rectangle([0, 0, cw - 1, ch - 1], radius=16, fill=(12, 14, 20, 245), outline=A(VGOLD, 1), width=3)
            d.rectangle([0, 0, 8, ch], fill=A(GOLD, 1))
            txt(d, 30, 18, 'E2 MANAGEMENT', f(BEB, 58), CREAM); txt(d, 30, 74, 'CHECKLIST · COACH AGZ', f(MONO, 20), VGOLD)
            for k in range(4):
                y = 118 + k * 42; tk = appear(t, 25.80 + k * 0.16, 0.1)
                d.rounded_rectangle([30, y, 58, y + 28], radius=5, outline=A((140, 140, 150), 1), width=3)
                if tk > 0:
                    d.line([(34, y + 14), (42, y + 23), (56, y + 3)], fill=A(GREEN, tk), width=5)
                d.rounded_rectangle([76, y + 8, 76 + [360, 300, 400, 250][k], y + 20], radius=6, fill=(70, 72, 84, 255))   # redacted line
            if t >= 26.90:   # FREE stamp
                sp = expo((t - 26.90) / 0.12); sc = lerp(1.6, 1.0, sp)
                st = Image.new('RGBA', (300, 130), (0, 0, 0, 0)); sd = ImageDraw.Draw(st)
                sd.rounded_rectangle([6, 6, 294, 124], radius=10, outline=A(RED, 1), width=8)
                fn = f(BEB, 104); tw = sd.textlength('FREE', font=fn); sd.text((150 - tw / 2, 14), 'FREE', font=fn, fill=A(RED, 1))
                st = st.rotate(-12, expand=True, resample=Image.BICUBIC).resize((int(320 * sc), int(190 * sc)), Image.BICUBIC)
                st.putalpha(st.split()[3].point(lambda v: int(v * sp)))
                card.alpha_composite(st, (int(cw - 300 - (st.width - 320) / 2), int(ch - 200 - (st.height - 190) / 2)))
            card = card.rotate(lerp(-9, 3, pin), expand=True, resample=Image.BICUBIC)
            a = pin * (1 - pout)
            card.putalpha(card.split()[3].point(lambda v: int(v * a)))
            x = int(lerp(1100, 470, pin) + 0 * pout); y = int(270 - 260 * ease_io(pout))
            sh = Image.new('RGBA', card.size, (0, 0, 0, 0)); sh.putalpha(card.split()[3].point(lambda v: int(v * 0.6)))
            comp(im, sh.filter(ImageFilter.GaussianBlur(12)), (x + 8, y + 16)); comp(im, card, (x, y))
            # logo lockup left
            la = appear(t, 24.80, 0.2) * (1 - pout)
            if la > 0:
                lg = logo(150); lg.putalpha(lg.split()[3].point(lambda v: int(v * la))); comp(im, lg, (70, 300))
                d = ImageDraw.Draw(im, 'RGBA'); txt(d, 70, 466, 'COACH AGZ', f(BEB, 52), GOLD, la); txt(d, 72, 520, '@coach.agz', f(MONO, 22), MUTED, la)
    # B. COMMENT "E2" pill lands on "comment" (27.82)
    if t >= 27.82:
        d = ImageDraw.Draw(im, 'RGBA'); b = expo((t - 27.82) / 0.14); s = lerp(1.25, 1.0, b)
        fn = f(BEB, int(118 * s)); label = 'COMMENT  "E2"'; tw = d.textlength(label, font=fn); hh = int(132 * s)
        x0 = (W - tw - 70) / 2; y0 = 312 - (hh - 132) / 2
        if GL: GL.rectangle([x0 - 6, y0 - 6, x0 + tw + 76, y0 + hh + 6], outline=A(VGOLD, b), width=14)
        lit_bar(d, x0, y0, x0 + tw + 70, y0 + hh, VGOLD, b); d.text((x0 + 35, y0 + 8 * s), label, font=fn, fill=A(INK, b))
        if t >= 28.30:   # "the word E2" -> E2 flashes red
            pass
        # bobbing arrow toward the comment button (right column)
        if t >= 28.84:
            c = appear(t, 28.84); bob = math.sin((t - 28.84) * 7) * 8
            arrow(d, 900, 480 + bob, 980, 560 + bob, VGOLD, 7, c, 26)
        txt(d, (W - d.textlength('FOR RESEARCH & EDUCATIONAL PURPOSES ONLY', font=f(MONO, 18))) / 2, 280, 'FOR RESEARCH & EDUCATIONAL PURPOSES ONLY', f(MONO, 18), MUTED, b * 0.9)
    # C. DM toast on "send it out" (29.72)
    if t >= 29.72:
        p = expo((t - 29.72) / 0.25); y = int(lerp(520, 468, p)); x0, x1 = 120, 960
        frosted(im, (x0, y, x1, y + 96), 0.80, 12, r=20); d = ImageDraw.Draw(im, 'RGBA')
        d.rounded_rectangle([x0, y, x1, y + 96], radius=20, outline=A((80, 82, 96), p), width=2)
        lg = logo(64); lg.putalpha(lg.split()[3].point(lambda v: int(v * p))); comp(im, lg, (x0 + 18, y + 16))
        d = ImageDraw.Draw(im, 'RGBA')
        txt(d, x0 + 100, y + 14, 'coach.agz', f(DMB, 28), WHITE, p); txt(d, x0 + 100, y + 52, 'sent you  E2_checklist.pdf', f(DMR, 26), (200, 200, 206), p)
        d.ellipse([x1 - 40, y + 40, x1 - 24, y + 56], fill=A((60, 140, 255), p))

# =====================================================================
# CAPTIONS (every word, Bebas, red active-word block: saved style), low under the chin
# =====================================================================
FIX = {'trt?': 'TRT'}
def build_groups():
    G = []; cur = []
    for i, x in enumerate(WORDS):
        if cur:
            prev = WORDS[cur[-1]]
            if len(cur) >= 3 or x['s'] - prev['e'] > 0.28 or prev['w'][-1] in '.,?!': G.append(cur); cur = []
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
    if t > WORDS[lo[-1]]['e'] + 0.5:
        nxt = [g for g in GROUPS if WORDS[g[0]]['s'] > WORDS[lo[0]]['s']]
        if not nxt or WORDS[nxt[0][0]]['s'] > t: return None
    return lo
CAP_Y = 1500
def captions(im, t):
    g = group_at(t)
    if not g: return
    d = ImageDraw.Draw(im, 'RGBA')
    ws = [FIX.get(WORDS[i]['w'].lower(), WORDS[i]['w']).upper().rstrip('.,?!') for i in g]
    size = 112
    while True:
        fn = f(BEB, size); sp = d.textlength(' ', font=fn) + 12; wd = [d.textlength(w, font=fn) for w in ws]; tot = sum(wd) + sp * (len(ws) - 1)
        if tot <= 800: break
        size -= 4
    xs = []; x = (W - tot) / 2
    for w_ in wd: xs.append(x); x += w_ + sp
    act = 0
    for k, i in enumerate(g):
        if WORDS[i]['s'] <= t: act = k
    g0 = WORDS[g[0]]['s']; s = lerp(0.9, 1, expo((t - g0) / 0.10))
    cap = Image.new('RGBA', (W, 240), (0, 0, 0, 0)); cd = ImageDraw.Draw(cap); shd = Image.new('RGBA', (W, 240), (0, 0, 0, 0)); sd = ImageDraw.Draw(shd)
    prev = max(0, act - 1); bt = expo((t - WORDS[g[act]]['s']) / 0.07) if act > 0 else 1
    bx0 = lerp(xs[prev], xs[act], bt) - 16; bx1 = lerp(xs[prev] + wd[prev], xs[act] + wd[act], bt) + 16
    for k, (w_, x_) in enumerate(zip(ws, xs)): sd.text((x_ + 4, 46), w_, font=fn, fill=(0, 0, 0, 220))
    cap.alpha_composite(shd.filter(ImageFilter.GaussianBlur(7)))
    lit_bar(cd, bx0, 40 + size * 0.02, bx1, 40 + size * 0.98, RED)
    for k, (w_, x_) in enumerate(zip(ws, xs)): cd.text((x_, 40), w_, font=fn, fill=CREAM, stroke_width=0 if k == act else 3, stroke_fill=(0, 0, 0))
    if abs(s - 1) > 0.002:
        cap = cap.resize((int(W * s), int(240 * s)), Image.BICUBIC); ox = int((W - cap.width) / 2); oy = int(CAP_Y - 40 - (cap.height - 240) / 2)
    else: ox, oy = 0, CAP_Y - 40
    comp(im, cap, (ox, oy))

# =====================================================================
# FRAME
# =====================================================================
BGCACHE = {}
def compose_footage(src, t):
    s, lx, ly, ct, cb = layout(t)
    z = punch(t)
    if s > 0.995:   # full frame, punch-in about the face anchor (540, 980)
        if abs(z - 1) < 1e-3: return src.copy()
        big = src.resize((int(W * z), int(H * z)), Image.BICUBIC)
        ox = int(540 * z - 540); oy = int(980 * z - 980)
        return big.crop((ox, oy, ox + W, oy + H))
    # split: blurred, pushed background + rounded footage window with gold frame
    sm = src.resize((W // 8, H // 8), Image.BILINEAR).filter(ImageFilter.GaussianBlur(3)).resize((W, H), Image.BILINEAR)
    k = clamp((1 - s) / 0.24)
    bg = Image.blend(sm, Image.new('RGB', (W, H), (5, 8, 16)), 0.78 * k)
    # subtle warm glow top-right (brand bg-glow)
    gl = Image.new('RGBA', (W, H), (0, 0, 0, 0)); ImageDraw.Draw(gl).ellipse([600, -300, 1400, 500], fill=(201, 169, 110, int(26 * k)))
    comp(bg, gl.filter(ImageFilter.GaussianBlur(120)))
    fw = int(W * s); ct = int(ct); cb = int(cb)
    fr = src.crop((0, ct, W, cb)).resize((fw, int((cb - ct) * s)), Image.BICUBIC); fh = fr.height; ly = ly + ct * s
    r = int(lerp(0, 34, k)); m = Image.new('L', (fw, fh), 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, fw - 1, fh - 1], radius=r, fill=255)
    sh = Image.new('RGBA', (W, H), (0, 0, 0, 0)); ImageDraw.Draw(sh).rounded_rectangle([lx + 6, ly + 18, lx + fw + 6, ly + fh + 18], radius=r, fill=(0, 0, 0, int(170 * k)))
    comp(bg, sh.filter(ImageFilter.GaussianBlur(20)))
    bg.paste(fr, (int(lx), int(ly)), m)
    d = ImageDraw.Draw(bg, 'RGBA')
    d.rounded_rectangle([lx, ly, lx + fw, ly + fh], radius=r, outline=A(VGOLD, 0.85 * k), width=3)
    if GL: GL.rounded_rectangle([lx, ly, lx + fw, ly + fh], radius=r, outline=A(VGOLD, 0.6 * k), width=6)
    d.rectangle([0, 0, 5, H], fill=A(GOLD, k))   # signature gold left rule
    return bg
def render_frame(src, tau):
    global GL
    t = out_to_src(tau)
    glow = Image.new('RGBA', (W, H), (0, 0, 0, 0)); GL = ImageDraw.Draw(glow, 'RGBA')
    im = compose_footage(src, t)
    # gentle top/bottom navy scrims for text legibility (footage itself untouched)
    yy = np.arange(H); a = np.maximum(np.where(yy > 1380, np.clip((yy - 1380) / 300, 0, 1) * 120, 0), np.where(yy < 560, (1 - yy / 560) * 110, 0)).astype(np.uint8)
    comp(im, Image.merge('RGBA', [Image.new('L', (W, H), c) for c in NAVY] + [Image.fromarray(np.repeat(a[:, None], W, 1))]))
    hook(im, t, tau); band(im, t)
    enzyme_card(im, t); fat_cell_scene(im, t); graph_scene(im, t); flank_scene(im, t); callouts(im, t); lab_scene(im, t); cta(im, t)
    captions(im, t)
    GL = None
    if glow.getbbox():
        sm = glow.resize((W // 4, H // 4), Image.BILINEAR)
        g1 = np.asarray(sm.filter(ImageFilter.GaussianBlur(3.5))).astype(np.float32) / 255; g2 = np.asarray(sm.filter(ImageFilter.GaussianBlur(10))).astype(np.float32) / 255
        prem = np.clip(g1[..., :3] * g1[..., 3:] * 2.0 + g2[..., :3] * g2[..., 3:] * 1.6, 0, 1)
        prem = np.asarray(Image.fromarray((prem * 255).astype(np.uint8)).resize((W, H), Image.BILINEAR)).astype(np.float32) / 255
        b = np.asarray(im.convert('RGB')).astype(np.float32) / 255
        return Image.fromarray(((1 - (1 - b) * (1 - prem)) * 255).astype(np.uint8))
    return im

def reader(t_start):
    p = subprocess.Popen(['ffmpeg', '-v', 'error', '-ss', f'{max(0, t_start):.4f}', '-i', SRC, '-vf', f'fps={SFPS}', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], stdout=subprocess.PIPE)
    return p
if __name__ == '__main__':
    if sys.argv[2] == 'still':
        tau = float(sys.argv[3]); t = out_to_src(tau)
        p = reader(t); raw = p.stdout.read(W * H * 3); p.kill()
        render_frame(Image.frombytes('RGB', (W, H), raw), tau).save(sys.argv[4], quality=90); sys.exit()
    ci, nc = int(sys.argv[2]), int(sys.argv[3])
    k0 = N * ci // nc; k1 = N * (ci + 1) // nc
    ts = out_to_src(k0 / FPS) - 0.05
    p = reader(ts); j = -1; cur = None
    enc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-preset', 'fast', '-crf', '10', '-pix_fmt', 'yuv420p', f'{S}/chunk_{ci}.mp4'], stdin=subprocess.PIPE)
    for k in range(k0, k1):
        t = out_to_src(k / FPS)
        target = int(round((t - ts) * SFPS))
        while j < target:
            raw = p.stdout.read(W * H * 3)
            if len(raw) < W * H * 3: break
            cur = raw; j += 1
        enc.stdin.write(render_frame(Image.frombytes('RGB', (W, H), cur), k / FPS).tobytes())
        if (k - k0) % 30 == 0: print(f'chunk {ci}: {k - k0}/{k1 - k0}', flush=True)
    enc.stdin.close(); enc.wait(); p.kill()
    print('done', ci)
