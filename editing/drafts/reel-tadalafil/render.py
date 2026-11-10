# Tadalafil Reel renderer: 1080x1920 30fps. Usage: render.py <workdir> frames <n0> <n1> <out.mp4> | stills t1 t2 ...
import json, subprocess, sys, math
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
T = sys.argv[1].rstrip('/') + '/'
F = T + '../fonts/'
W, H = 1080, 1920; FPS = 30
WORDS = json.load(open(T + 'words_final.json'))
KEEP = json.load(open(T + 'cut.json'))['keep']
CUTS = []; _acc = 0
for a, b in KEEP: _acc += b - a; CUTS.append(round(_acc * FPS) / FPS)
DUR = CUTS[-1]; CUTS = CUTS[:-1]
MID = DUR / 2

GOLD=(201,169,110); CREAM=(244,241,234); NAVY=(14,17,23); PANEL=(24,26,34)
RED=(255,34,28); VGOLD=(255,194,26); CYAN=(0,229,255); GREEN=(30,255,110); DEEP=(2,3,8); INK=(6,8,14); WHITE=(255,255,255)
CRIM=(200,16,46); CRIM2=(224,36,63); AMBER=(240,160,48); BLUE=(79,163,224); SGREEN=(60,203,106); MUTED=(124,124,130); GREY=(184,184,188)
MONO='JBMono-500.ttf'; MONOB='JBMono-700.ttf'; BEB='BebasNeue.ttf'; DMB='DMSans-700.ttf'; DMR='DMSans-400.ttf'; DMM='DMSans-500.ttf'; BAR='Barlow-700.ttf'; BAR8='Barlow-800.ttf'
_fc = {}
def f(n, s):
    k = (n, int(s))
    if k not in _fc: _fc[k] = ImageFont.truetype(F + n, int(s))
    return _fc[k]
def clamp(x, a=0, b=1): return max(a, min(b, x))
def expo(x): x = clamp(x); return 1 if x >= 1 else 1 - 2 ** (-10 * x)
def back(x, s=1.2): x = clamp(x); return 1 + (s + 1) * (x - 1) ** 3 + s * (x - 1) ** 2   # heavy settle (small overshoot)
def ease_io(x): x = clamp(x); return 4 * x ** 3 if x < .5 else 1 - (-2 * x + 2) ** 3 / 2
def lerp(a, b, t): return a + (b - a) * t
def A(c, a): return tuple(c[:3]) + (int(clamp(a) * 255),)
def ap(t, t0, d=0.16): return expo((t - t0) / d)
def win(t, t0, t1, din=0.18, dout=0.16): return min(expo((t - t0) / din), 1 - clamp((t - t1) / dout))
GL = None

# ---------------- primitives ----------------
def txt(d, x, y, s, font, col, a=1.0, anchor=None): d.text((x, y), s, font=font, fill=A(col, a), anchor=anchor)
def brackets(d, x0, y0, x1, y1, col, L=34, w=4):
    for (cx, cy, sx, sy) in [(x0,y0,1,1),(x1,y0,-1,1),(x0,y1,1,-1),(x1,y1,-1,-1)]:
        d.line([(cx,cy),(cx+sx*L,cy)], fill=col, width=w); d.line([(cx,cy),(cx,cy+sy*L)], fill=col, width=w)
def lit_bar(d, x0, y0, x1, y1, col, a=1.0):
    h = max(1, int(y1 - y0))
    for i in range(h):
        k = i / h; c = tuple(int(min(255, v * (1.18 - 0.36 * k) + (40 if k < 0.12 else 0))) for v in col)
        d.line([(x0, y0 + i), (x1, y0 + i)], fill=c + (int(255 * a),))
def tag(d, x, y, label, col=RED, size=32, a=1.0, glow=True):
    fn = f(MONO, size); tw = d.textlength(label, font=fn); h = size + 16
    lit_bar(d, x, y, x + tw + 24, y + h, col, a); d.text((x + 12, y + 5), label, font=fn, fill=A(INK if col in (VGOLD, GREEN, CYAN) else WHITE, a))
    if GL and glow: GL.rectangle([x-4, y-4, x+tw+28, y+h+4], outline=A(col, a), width=8)
    return x + tw + 24
def check(d, x, y, col, s=1.0, a=1.0):
    pts = [(x, y+16*s), (x+10*s, y+28*s), (x+30*s, y+2*s)]
    d.line(pts, fill=A(col, a), width=int(6*s), joint='curve')
    if GL: GL.line(pts, fill=A(col, a), width=int(12*s))
def cross(d, x, y, col, s=1.0, a=1.0):
    for p in ([(x,y),(x+28*s,y+28*s)], [(x+28*s,y),(x,y+28*s)]):
        d.line(p, fill=A(col, a), width=int(6*s))
        if GL: GL.line(p, fill=A(col, a), width=int(12*s))
def arrow(d, x0, y0, x1, y1, col, w=5, a=1.0, L=18):
    d.line([(x0,y0),(x1,y1)], fill=A(col,a), width=w)
    ang = math.atan2(y1-y0, x1-x0)
    d.polygon([(x1,y1),(x1-L*math.cos(ang-0.45),y1-L*math.sin(ang-0.45)),(x1-L*math.cos(ang+0.45),y1-L*math.sin(ang+0.45))], fill=A(col,a))
def up_arrow(d, x, y, col, s=1.0, a=1.0):
    d.polygon([(x, y), (x+14*s, y+18*s), (x+5*s, y+18*s), (x+5*s, y+34*s), (x-5*s, y+34*s), (x-5*s, y+18*s), (x-14*s, y+18*s)], fill=A(col, a))
    if GL: GL.polygon([(x, y-4), (x+18*s, y+20*s), (x-18*s, y+20*s)], fill=A(col, a))
def frosted(im, box, dark=0.86, blur=10, radius=0):
    x0, y0, x1, y1 = [int(v) for v in box]
    x0 = max(0, x0); y0 = max(0, y0); x1 = min(W, x1); y1 = min(H, y1)
    if x1 <= x0 or y1 <= y0: return
    reg = im.crop((x0, y0, x1, y1)).convert('RGB').filter(ImageFilter.GaussianBlur(blur))
    reg = Image.blend(reg, Image.new('RGB', reg.size, DEEP), dark).convert('RGBA')
    if radius:
        m = Image.new('L', reg.size, 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, reg.width-1, reg.height-1], radius=radius, fill=255)
        im.paste(reg, (x0, y0), m)
    else: im.paste(reg, (x0, y0))
def layer():
    L = Image.new('RGBA', (W, H), (0, 0, 0, 0)); return L, ImageDraw.Draw(L, 'RGBA')
def comp(im, L, a=1.0, blur=0):
    if a <= 0: return
    if blur > 0.3: L = L.filter(ImageFilter.GaussianBlur(blur))
    if a < 1: L.putalpha(L.split()[3].point(lambda v: int(v * a)))
    im.alpha_composite(L)
def flow(d, x0, y0, x1, y1, t, col, n=5, speed=0.9, a=1.0, r=7, jitter=0):
    for k in range(n):
        p = (t * speed + k / n) % 1
        x = lerp(x0, x1, p); y = lerp(y0, y1, p) + jitter * math.sin(k * 2.1 + t * 3)
        fa = a * min(1, p * 6, (1 - p) * 6)
        d.ellipse([x-r, y-r, x+r, y+r], fill=A(col, fa))
        if GL: GL.ellipse([x-r*2, y-r*2, x+r*2, y+r*2], fill=A(col, fa))
def kicker(d, x, y, label, col=VGOLD, a=1.0, t=None, t0=0):
    p = 1 if t is None else ap(t, t0, 0.2)
    d.line([(x, y + 16), (x + 44 * p, y + 16)], fill=A(col, a), width=4)
    if p > 0.5: txt(d, x + 58, y, label, f(MONO, 26), col, a * clamp((p - 0.5) * 2))

# ---------------- 0. TEXT HOOK (frame 0, native mode) + Rx label ----------------
HOOK_END = 5.30
def text_hook(im, t):
    if t >= HOOK_END + 0.15: return
    a = 1 - clamp((t - HOOK_END) / 0.15)
    s = lerp(1.0, 1.04, clamp(t / HOOK_END))       # one slow move over the hold
    L, d = layer()
    fn = f(DMB, int(72 * s)); fg = f(BEB, int(96 * s))
    l1 = 'Your blast is missing'; l2a = '5mg '; l2b = 'TADALAFIL'
    w1 = d.textlength(l1, font=fn); w2 = d.textlength(l2a, font=fn) + d.textlength(l2b, font=fg)
    bw = max(w1, w2) + 70; cx = W / 2; y0 = 300 - 10 * (s - 1) * 10
    d.rounded_rectangle([cx - bw/2, y0, cx + bw/2, y0 + 220 * s], radius=26, fill=(4, 6, 12, 222))
    d.rectangle([cx - bw/2, y0 + 30, cx - bw/2 + 7, y0 + 220 * s - 30], fill=GOLD + (255,))
    txt(d, cx - w1/2, y0 + 22 * s, l1, fn, WHITE)
    x = cx - w2/2; txt(d, x, y0 + 116 * s, l2a, fn, WHITE)
    x += d.textlength(l2a, font=fn); txt(d, x, y0 + 106 * s, l2b, fg, VGOLD)
    GL.text((x, y0 + 106 * s), l2b, font=fg, fill=A(VGOLD, 0.8 * a))
    comp(im, L, a)

def rx_label(im, t):   # Rx bottle label card, slides in on "Tadalafil", leaves before scene 1
    t0, t1 = 0.84, 5.15
    a = win(t, t0, t1, 0.22, 0.14)
    if a <= 0: return
    p = back((t - t0) / 0.32, 0.9); dx = lerp(380, 0, p) + 420 * clamp((t - t1) / 0.14) ** 2
    dx = -dx; x0, y0 = 50 + dx, 640; x1, y1 = x0 + 420, y0 + 330
    L, d = layer()
    # bottle silhouette behind label
    d.rounded_rectangle([x0 + 30, y0 - 40, x1 - 30, y1 + 20], radius=40, fill=(150, 88, 20, 235))
    d.rounded_rectangle([x0 + 60, y0 - 90, x1 - 60, y0 - 34], radius=10, fill=(236, 236, 240, 255))
    d.rectangle([x0 + 60, y0 - 70, x1 - 60, y0 - 64], fill=(200, 200, 206, 255))
    d.rounded_rectangle([x0, y0, x1, y1 - 30], radius=10, fill=(250, 250, 246, 255))
    d.rectangle([x0, y0, x1, y0 + 54], fill=(210, 10, 20, 255))
    txt(d, x0 + 18, y0 + 10, 'Rx  ·  RESEARCH SUPPLY', f(MONOB, 26), WHITE)
    txt(d, x0 + 18, y0 + 66, 'TADALAFIL', f(BEB, 76), INK)
    txt(d, x0 + 18, y0 + 142, '5 MG  TABLETS', f(MONO, 28), (40, 40, 48))
    txt(d, x0 + 18, y0 + 186, 'PDE5 INHIBITOR', f(MONO, 24), (110, 110, 120))
    for i in range(14): d.line([(x0 + 260 + i * 9, y0 + 190), (x0 + 260 + i * 9, y0 + 228)], fill=(30, 30, 36, 255), width=2 + (i % 3 == 0) * 2)
    if t >= 1.96:   # "underrated" -> red detection brackets on the label
        b = ap(t, 1.96, 0.12); brackets(d, x0 - 14, y0 - 14, x1 + 14, y1 - 16, A(RED, b), 30, 7)
        if GL: brackets(GL, x0 - 14 + dx * 0, y0 - 14, x1 + 14, y1 - 16, A(RED, b * a), 30, 12)
        tag(d, x0 - 14, y1 - 6, 'UNDERRATED', RED, 28, b)
    L = L.resize((int(W * 0.8), int(H * 0.8)), Image.BICUBIC); L2 = Image.new('RGBA', (W, H), (0, 0, 0, 0)); L2.alpha_composite(L, (8, 140))
    comp(im, L2, a, blur=6 * (1 - clamp((t - t0) / 0.2)))

# ---------------- 1. STACK BUILDER (lower strip, face stays clear) ----------------
SLOTS = ['BLAST', 'AI DIALED', 'BLOODWORK']
def stack_strip(d, t, t_rows, t_missing, fill_t=None, x0=56, y0=1040, a=1.0, empty_red=None):
    w = (W - 2 * x0 - 3 * 16) / 4; h = 190
    for i in range(4):
        tt = t_rows[i] if i < 3 else t_missing
        if t < tt:
            d.rounded_rectangle([x0 + i*(w+16), y0, x0 + i*(w+16) + w, y0 + h], radius=16, outline=A((70, 74, 90), 0.6 * a), width=2)
            continue
        b = ap(t, tt, 0.14) * a; yy = y0 + lerp(-26, 0, back((t - tt) / 0.22, 1.0))
        X0 = x0 + i * (w + 16); X1 = X0 + w
        if i < 3:
            d.rounded_rectangle([X0, yy, X1, yy + h], radius=16, fill=A((10, 14, 24), 0.94 * b), outline=A(CYAN, b), width=4)
            if GL: GL.rounded_rectangle([X0, yy, X1, yy + h], radius=16, outline=A(CYAN, 0.7 * b), width=8)
            txt(d, X0 + 18, yy + 16, f'0{i+1}', f(MONO, 24), CYAN, b)
            fn = f(BEB, 52 if len(SLOTS[i]) < 8 else 44); txt(d, X0 + 18, yy + 58, SLOTS[i], fn, WHITE, b)
            check(d, X0 + 18, yy + 136, GREEN, 1.0, ap(t, tt + 0.12, 0.12) * a)
            txt(d, X0 + 60, yy + 136, 'ON', f(MONO, 26), GREEN, ap(t, tt + 0.12, 0.12) * a)
        else:
            filled = fill_t is not None and t >= fill_t
            if not filled:
                pul = 0.55 + 0.45 * math.sin(t * 10)
                dash_rect(d, X0, yy, X1, yy + h, A(RED, b * (0.6 + 0.4 * pul)), 5)
                if GL: GL.rounded_rectangle([X0, yy, X1, yy + h], radius=16, outline=A(RED, 0.6 * b * pul), width=10)
                txt(d, (X0 + X1) / 2, yy + 92, '?', f(BEB, 110), RED, b * (0.5 + 0.5 * pul), 'mm')
                lab = empty_red or 'MISSING'; fn = f(MONO, 24); tw = d.textlength(lab, font=fn)
                lit_bar(d, X0, yy + h + 10, X0 + tw + 20, yy + h + 46, RED, b); txt(d, X0 + 10, yy + h + 14, lab, fn, WHITE, b)
            else:
                c = ap(t, fill_t, 0.12) * a; yy2 = y0 + lerp(-80, 0, back((t - fill_t) / 0.25, 1.4))
                lit_bar(d, X0, yy2, X1, yy2 + h, VGOLD, c)
                if GL: GL.rectangle([X0 - 4, yy2 - 4, X1 + 4, yy2 + h + 4], outline=A(VGOLD, c), width=12)
                txt(d, X0 + 16, yy2 + 16, '04', f(MONO, 24), INK, c)
                txt(d, X0 + 14, yy2 + 50, 'TADALAFIL', f(BEB, 50), INK, c)
                txt(d, X0 + 16, yy2 + 120, '5MG DAILY', f(MONOB, 26), INK, c)
    return x0, y0, w, h
def dash_rect(d, x0, y0, x1, y1, col, w=4, dash=18):
    for (a_, b_) in [((x0, y0), (x1, y0)), ((x1, y0), (x1, y1)), ((x1, y1), (x0, y1)), ((x0, y1), (x0, y0))]:
        L_ = math.hypot(b_[0] - a_[0], b_[1] - a_[1]); n = int(L_ // (dash * 2)) + 1
        for k in range(n):
            s0 = k * dash * 2 / L_; s1 = min(1, (k * dash * 2 + dash) / L_)
            d.line([(lerp(a_[0], b_[0], s0), lerp(a_[1], b_[1], s0)), (lerp(a_[0], b_[0], s1), lerp(a_[1], b_[1], s1))], fill=col, width=w)
def scene_stack(im, t):
    t0, t1 = 5.45, 13.40
    a = win(t, t0, t1, 0.2, 0.16)
    if a <= 0: return
    frosted(im, (40, 392, W - 40, 790), 0.55 * a, 14, 22)
    L, d = layer()
    kicker(d, 64, 405, 'YOUR PROTOCOL  ·  ' + ('3 / 4' if t < 10.70 else '3 / 4  INCOMPLETE'), VGOLD, 1, t, t0)
    x0, y0, w, h = stack_strip(d, t, [7.00, 8.14, 9.46], 10.70, None, y0=460)
    if t >= 11.98:   # "amplifies everything" -> boost beams from the empty slot into each chip
        b = ap(t, 11.98, 0.2); sx = x0 + 3 * (w + 16) + w / 2
        for i in range(3):
            cx = x0 + i * (w + 16) + w / 2; q = clamp((t - 11.98 - i * 0.12) / 0.3)
            d.line([(sx, y0 + h + 8), (lerp(sx, cx, q), y0 + h + 8 + 40 * math.sin(math.pi * q))], fill=A(VGOLD, b), width=4)
            if q >= 1: up_arrow(d, x0 + i * (w + 16) + w - 34, y0 + 18, VGOLD, 1.0, b)
        tag(d, x0, y0 + h + 58, 'AMPLIFIES EVERYTHING', VGOLD, 24, b)
    comp(im, L, a)

# ---------------- 2. FULL-SCREEN TIMELINE (navy carousel look, face in PIP) ----------------
_g = Image.new('RGBA', (W, H), (0, 0, 0, 0)); ImageDraw.Draw(_g).ellipse([520, -260, 1340, 560], fill=(60, 48, 30, 90)); GLOW_TL = _g.filter(ImageFilter.GaussianBlur(120))
def scene_timeline(im, t, src):
    t0, t1 = 13.55, 27.22
    a = win(t, t0, t1, 0.24, 0.18)
    if a <= 0: return
    bg = Image.new('RGBA', (W, H), NAVY + (255,)); bd = ImageDraw.Draw(bg, 'RGBA')
    bg.alpha_composite(GLOW_TL)
    for y in range(0, H, 6): bd.line([(0, y), (W, y)], fill=(255, 255, 255, 4))
    # PIP of the speaker (rounded window, top right), grows in from full frame
    p = ease_io((t - t0) / 0.45) * (1 - ease_io((t - t1) / 0.3))
    pw, ph = int(lerp(W, 330, p)), int(lerp(H, 440, p)); px, py = int(lerp(0, 700, p)), int(lerp(0, 400, p))
    crop = src.crop((int(lerp(0, 150, p)), int(lerp(0, 300, p)), int(lerp(W, 930, p)), int(lerp(H, 1340, p)))).resize((pw, ph), Image.BICUBIC)
    m = Image.new('L', (pw, ph), 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, pw - 1, ph - 1], radius=int(28 * p), fill=255)
    bg.paste(crop.convert('RGBA'), (px, py), m)
    bd.rounded_rectangle([px, py, px + pw, py + ph], radius=int(28 * p), outline=A(GOLD, p), width=3)
    if p > 0.9: txt(bd, px + 16, py + ph - 44, '● LIVE', f(MONO, 22), RED, (p - 0.9) * 10)
    L, d = layer()
    # title block
    if t >= 14.74:
        b = ap(t, 14.74, 0.18); kicker(d, 64, 410, 'COMPOUND FILE', VGOLD, 1, t, 14.6)
        txt(d, 64, 456 + lerp(30, 0, b), 'TADALAFIL', f(BEB, 132), CREAM, b)
    if t >= 15.32: tag(d, 64, 606, 'A.K.A. CIALIS', VGOLD, 30, ap(t, 15.32))
    if t >= 16.06:
        b = ap(t, 16.06); x_ = tag(d, 64, 670, 'BEDROOM ONLY', CRIM, 30, b, glow=False)
        if t >= 16.62:
            q = clamp((t - 16.62) / 0.16); d.line([(56, 694), (lerp(56, x_ + 10, q), 694)], fill=A(WHITE, 1), width=6)
            if q >= 1: txt(d, x_ + 20, 674, 'FALSE', f(MONOB, 30), RED, ap(t, 16.78))
    # vertical timeline
    X = 92; Y0 = 790; nodes = [
        (17.88, 'CLINICAL RESEARCH', 'CARDIOVASCULAR HEALTH', 19.56, CYAN),
        (21.42, 'SIDE FINDING', 'HELPS IN THE BEDROOM', 23.06, VGOLD),
        (24.52, 'MARKET SIZE', None, 24.70, GREEN),
        (26.48, 'ROUTE CHOSEN', 'SOLD AS A BEDROOM DRUG', 26.84, RED)]
    if t >= 17.6:
        q = clamp((t - 17.6) / 9.0); yb = Y0 + 470 * q
        d.line([(X, Y0), (X, Y0 + 470)], fill=A((60, 64, 80), 1), width=3)
        d.line([(X, Y0), (X, yb)], fill=A(VGOLD, 1), width=5)
        if GL: GL.line([(X, Y0), (X, yb)], fill=A(VGOLD, 0.7), width=10)
    for i, (tn, title, sub, ts, col) in enumerate(nodes):
        if t < tn: continue
        b = ap(t, tn, 0.16); y = Y0 + i * 150
        r = lerp(4, 14, back((t - tn) / 0.25)); d.ellipse([X - r, y - r, X + r, y + r], fill=A(col, b))
        if GL: GL.ellipse([X - 26, y - 26, X + 26, y + 26], fill=A(col, b * 0.8))
        txt(d, X + 40 + lerp(-20, 0, b), y - 22, f'0{i+1}  ' + title, f(MONO, 26), col, b)
        if t >= ts:
            c = ap(t, ts, 0.16)
            if sub: txt(d, X + 40, y + 12, sub, f(BAR, 52), CREAM, c)
            else:   # $ ticker rolls then lands on BILLIONS
                if t < ts + 0.9:
                    v = int(lerp(1e6, 9.9e9, ((t - ts) / 0.9) ** 2)); s_ = f'$ {v:,}'
                    txt(d, X + 40, y + 6, s_, f(BEB, 64), GREEN, c)
                else:
                    sc = lerp(1.25, 1, ap(t, ts + 0.9, 0.12)); txt(d, X + 40, y + 6, '$ BILLIONS', f(BEB, int(64 * sc)), GREEN, 1)
                    if GL: GL.text((X + 40, y + 6), '$ BILLIONS', font=f(BEB, int(64 * sc)), fill=A(GREEN, 0.7))
    if t >= 26.84:   # stamp
        b = ap(t, 26.84, 0.1); s = lerp(1.6, 1.0, b)
        st = Image.new('RGBA', (420, 120), (0, 0, 0, 0)); sd = ImageDraw.Draw(st)
        sd.rounded_rectangle([4, 4, 416, 116], radius=10, outline=RED + (255,), width=7); txt(sd, 210, 62, 'REBRANDED', f(BEB, 84), RED, 1, 'mm')
        st = st.rotate(-8, expand=True, resample=Image.BICUBIC); st = st.resize((int(st.width * s), int(st.height * s)), Image.BICUBIC)
        L.alpha_composite(st, (int(820 - st.width / 2), int(1180 - st.height / 2)))
        if GL: GL.rectangle([640, 1110, 1000, 1250], outline=A(RED, b), width=10)
    bg.alpha_composite(L)
    comp(im, bg, a)

# ---------------- 3. X-RAY VESSEL CROSS-SECTION (frosted evidence panel) ----------------
P3 = (64, 440, 1016, 1270)
def scene_vessel(im, t):
    t0, t1 = 27.30, 33.30
    a = win(t, t0, t1, 0.2, 0.16)
    if a <= 0: return
    s = lerp(1.05, 1.0, ap(t, t0, 0.2)); x0, y0, x1, y1 = P3
    frosted(im, (x0, y0, x1, y1), 0.92, 10)
    L, d = layer()
    d.rectangle([x0, y0, x1, y1], outline=A(CYAN, 0.6), width=2); brackets(d, x0, y0, x1, y1, A(CYAN, 1), 46, 7)
    if GL: brackets(GL, x0, y0, x1, y1, A(CYAN, 1), 46, 14)
    d.ellipse([x0 + 26, y0 + 26, x0 + 42, y0 + 42], fill=A(RED, 1 if int(t * 4) % 2 == 0 else 0.3))
    txt(d, x0 + 56, y0 + 18, 'VESSEL SCAN · CROSS-SECTION', f(MONO, 28), WHITE)
    # grid
    for gx in range(x0 + 40, x1, 60): d.line([(gx, y0 + 70), (gx, y1 - 20)], fill=A(CYAN, 0.06), width=1)
    for gy in range(y0 + 70, y1, 60): d.line([(x0 + 20, gy), (x1 - 20, gy)], fill=A(CYAN, 0.06), width=1)
    # vessel ring: wall + lumen, lumen widens on "opens up" (30.10)
    cx, cy = 330, 820
    op = 0 if t < 30.10 else ease_io((t - 30.10) / 0.7)
    R_out = lerp(150, 205, op); R_in = lerp(62, 160, op)
    for k in range(10):
        rr = R_out - k * (R_out - R_in) / 10
        d.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], fill=A((255, 70, 90) if k < 7 else (255, 120, 130), 0.10 + 0.05 * k))
    d.ellipse([cx - R_out, cy - R_out, cx + R_out, cy + R_out], outline=A(CYAN, 1), width=5)
    d.ellipse([cx - R_in, cy - R_in, cx + R_in, cy + R_in], fill=A((10, 12, 22), 1), outline=A(CYAN, 1), width=4)
    if GL: GL.ellipse([cx - R_out, cy - R_out, cx + R_out, cy + R_out], outline=A(CYAN, 1), width=10); GL.ellipse([cx - R_in, cy - R_in, cx + R_in, cy + R_in], outline=A(CYAN, 0.8), width=8)
    for k in range(int(lerp(4, 14, op))):   # red cells in lumen
        ang = k * 2.4 + t * (0.8 + 0.1 * k); rr = (R_in - 20) * ((k * 37 % 10) / 10)
        ex, ey = cx + rr * math.cos(ang), cy + rr * math.sin(ang); d.ellipse([ex - 11, ey - 7, ex + 11, ey + 7], fill=A(RED, 0.9))
    # scan line
    sy = y0 + 80 + ((t - t0) * 260) % (y1 - y0 - 100); d.line([(x0 + 10, sy), (x1 - 10, sy)], fill=A(CYAN, 0.35), width=2)
    if GL: GL.line([(x0 + 10, sy), (x1 - 10, sy)], fill=A(CYAN, 0.5), width=6)
    # diameter readout
    d.line([(cx - R_in, cy + R_out + 40), (cx + R_in, cy + R_out + 40)], fill=A(WHITE, 1), width=3)
    for xx in (cx - R_in, cx + R_in): d.line([(xx, cy + R_out + 28), (xx, cy + R_out + 52)], fill=A(WHITE, 1), width=3)
    txt(d, cx, cy + R_out + 76, 'LUMEN  ' + ('NARROW' if op < 0.5 else 'WIDE OPEN'), f(MONO, 28), GREEN if op > 0.5 else GREY, 1, 'mm')
    # right column: enzyme + block + hold bar
    RX = 600
    if t >= 28.16:
        b = ap(t, 28.16); y = lerp(560, 540, b)
        d.rounded_rectangle([RX, y, RX + 360, y + 110], radius=14, fill=A((40, 10, 16), 0.95 * b), outline=A(RED, b), width=4)
        txt(d, RX + 20, y + 10, 'PDE5', f(BEB, 70), WHITE, b); txt(d, RX + 160, y + 22, 'ENZYME', f(MONO, 24), RED, b); txt(d, RX + 160, y + 54, 'CLOSES VESSEL', f(MONO, 20), GREY, b)
    if t >= 29.18:
        b = ap(t, 29.18, 0.1); brackets(d, RX - 12, 528, RX + 372, 662, A(VGOLD, b), 26, 7)
        if GL: brackets(GL, RX - 12, 528, RX + 372, 662, A(VGOLD, b), 26, 12)
        cross(d, RX + 300, 570, VGOLD, 1.3, b); tag(d, RX, 672, 'INHIBITED', VGOLD, 28, b)
    if t >= 31.64:   # "keeps them open long term" -> hold meter that stays full
        b = ap(t, 31.64); txt(d, RX, 800, 'VESSEL STATE', f(MONO, 26), CREAM, b)
        n = 8; filled = int(clamp((t - 31.64) / 0.9) * n + 0.999)
        for i in range(n):
            xx = RX + i * 45; c = GREEN if i < filled else (40, 44, 56)
            d.rectangle([xx, 840, xx + 36, 900], fill=A(c, b))
            if GL and i < filled: GL.rectangle([xx, 840, xx + 36, 900], fill=A(GREEN, 0.6 * b))
        txt(d, RX, 916, 'OPEN · HELD · LONG-ACTING', f(MONO, 22), GREEN, b)
    elif t >= 30.10:
        b = ap(t, 30.10); txt(d, RX, 800, 'VESSEL STATE', f(MONO, 26), CREAM, b); tag(d, RX, 840, 'DILATING', GREEN, 30, b)
    comp(im, L, a, blur=8 * (1 - ap(t, t0, 0.2)))

# ---------------- 4. SPLIT SCREEN: delivery flow + gauge ----------------
def split_amt(t): return min(ease_io((t - 33.40) / 0.35), 1 - ease_io((t - 45.30) / 0.30))
def split_bg(src, t):
    p = split_amt(t)
    if p <= 0: return src
    out = Image.new('RGB', (W, H), NAVY); od = ImageDraw.Draw(out)
    for y in range(0, H, 6): od.line([(0, y), (W, y)], fill=(18, 21, 28))
    wx0, wy0, wx1, wy1 = lerp(0, 40, p), lerp(0, 400, p), lerp(W, W - 40, p), lerp(H, 990, p)
    ww, wh = int(wx1 - wx0), int(wy1 - wy0)
    # crop from source keeping the face (aspect of window)
    cw = W; ch = cw * wh / ww
    if ch > H: ch = H; cw = ch * ww / wh
    cy0 = clamp(lerp(0, 640, p), 0, H - ch); cx0 = (W - cw) / 2
    crop = src.crop((int(cx0), int(cy0), int(cx0 + cw), int(cy0 + ch))).resize((ww, wh), Image.BICUBIC)
    m = Image.new('L', (ww, wh), 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, ww - 1, wh - 1], radius=int(30 * p), fill=255)
    out.paste(crop, (int(wx0), int(wy0)), m)
    od.rounded_rectangle([wx0, wy0, wx1, wy1], radius=int(30 * p), outline=GOLD, width=3)
    return out
def scene_delivery(im, t):
    p = split_amt(t)
    if p <= 0.05: return
    a = clamp((p - 0.3) / 0.7)
    L, d = layer()
    y = 1012; kicker(d, 64, y, 'NUTRIENT DELIVERY  ·  ILLUSTRATIVE', VGOLD, 1, t, 33.6)
    # vessel tube that widens with vasodilation
    op = ease_io((t - 33.46) / 0.8); hh = lerp(26, 58, op); cy = 1120
    d.rounded_rectangle([64, cy - hh, 760, cy + hh], radius=int(hh), fill=A((60, 10, 20), 1), outline=A(CRIM2, 1), width=4)
    if GL: GL.rounded_rectangle([64, cy - hh, 760, cy + hh], radius=int(hh), outline=A(CRIM2, 0.7), width=8)
    chips = [(38.06, 'CREATINE', CYAN), (39.34, 'AMINOS', GREEN), (40.42, 'CARBS', VGOLD)]
    flow(d, 80, cy, 750, cy, t, RED, int(lerp(3, 9, op)), 0.6 + 0.7 * op, 1, 7, jitter=hh * 0.4)
    for i, (tc, nm, col) in enumerate(chips):
        if t < tc: continue
        q = ((t - tc) * 0.55 + i * 0.33) % 1 if t > tc + 0.5 else lerp(0, 0.15, (t - tc) / 0.5)
        x = lerp(90, 640, q); fn = f(MONOB, 22); tw = d.textlength(nm, font=fn)
        d.rounded_rectangle([x, cy - 17, x + tw + 20, cy + 17], radius=17, fill=A(col, 1)); txt(d, x + 10, cy - 13, nm, fn, INK)
        if GL: GL.rounded_rectangle([x - 4, cy - 21, x + tw + 24, cy + 21], radius=20, fill=A(col, 0.6))
    # muscle cell (right)
    mx, my = 900, 1120; lit = ap(t, 36.40, 0.2); fill = clamp((t - 38.06) / 6.0)
    for k in range(5):
        d.ellipse([mx - 120 + k * 4, my - 70 + k * 12, mx + 120 - k * 4, my + 70 - k * 12], outline=A(lerp_c((80, 40, 50), CRIM2, lit), 1), width=3)
    d.ellipse([mx - 116, my - 66, mx - 116 + 232 * max(0.02, fill), my + 66], fill=A(VGOLD, 0.35 * lit))
    if t < 43.96: txt(d, mx, my - 100, 'MUSCLE CELL', f(MONO, 22), CREAM, 1, 'mm')
    if t >= 43.96:
        b = ap(t, 43.96); check(d, mx - 40, my - 18, GREEN, 1.3, b); txt(d, mx - 4, my - 14, 'IN', f(MONOB, 30), GREEN, b)
        tag(d, mx - 90, my - 122, 'DELIVERED', GREEN, 24, b)
    # delivery gauge (bottom) sweeps on "better delivery"
    gy = 1240; g = 0.25 if t < 35.14 else lerp(0.25, 0.9, ease_io((t - 35.14) / 0.9))
    txt(d, 64, gy - 6, 'DELIVERY', f(MONO, 22), CREAM)
    for i in range(24):
        xx = 210 + i * 22; on = i / 24 < g; c = lerp_c(BLUE, GREEN, i / 24) if on else (40, 44, 56)
        d.rectangle([xx, gy - 4, xx + 15, gy + 22], fill=A(c, 1))
        if GL and on: GL.rectangle([xx, gy - 4, xx + 15, gy + 22], fill=A(c, 0.5))
    txt(d, 750, gy - 8, 'AMPLIFIED' if g > 0.6 else 'BASELINE', f(MONOB, 26), GREEN if g > 0.6 else GREY)
    comp(im, L, a)
def lerp_c(c1, c2, k): return tuple(int(lerp(a, b, clamp(k))) for a, b in zip(c1, c2))

# ---------------- 5. LINE GRAPH: systemic stress (charcoal + crimson card) ----------------
def scene_graph(im, t):
    t0, t1 = 45.45, 58.20
    a = win(t, t0, t1, 0.22, 0.16)
    if a <= 0: return
    rise = back((t - t0) / 0.3, 0.6); oy = lerp(60, 0, rise)
    x0, y0, x1, y1 = 56, 450 + oy, W - 56, 1290 + oy
    frosted(im, (x0, y0, x1, y1), 0.9, 12, 26)
    L, d = layer()
    d.rounded_rectangle([x0, y0, x1, y1], radius=26, outline=A((60, 60, 70), 1), width=2)
    d.rounded_rectangle([x0, y0 + 30, x0 + 10, y1 - 30], radius=4, fill=A(CRIM, 1))
    txt(d, x0 + 40, y0 + 26, 'SYSTEMIC STRESS', f(BAR8, 34), CRIM2); txt(d, x1 - 30, y0 + 32, 'ILLUSTRATIVE', f(MONO, 22), MUTED, 1, 'ra')
    txt(d, x0 + 40, y0 + 66, 'Heart + prostate load as the protocol grows', f(DMR, 30), GREY)
    # axes
    gx0, gy0, gx1, gy1 = x0 + 70, y0 + 140, x1 - 40, y0 + 560
    d.line([(gx0, gy1), (gx1, gy1)], fill=A((110, 110, 120), 1), width=3); d.line([(gx0, gy0), (gx0, gy1)], fill=A((110, 110, 120), 1), width=3)
    for k in range(1, 4): d.line([(gx0, gy1 - k * 105), (gx1, gy1 - k * 105)], fill=A((50, 50, 60), 1), width=1)
    txt(d, gx0 - 20, gy0 - 8, 'LOAD', f(MONO, 20), MUTED, 1, 'ra') if False else txt(d, gx0 + 10, gy0 - 34, 'LOAD ↑', f(MONO, 22), MUTED)
    labels = [('BASE', 46.0), ('HIGHER DOSE', 47.46), ('+ COMPOUND', 48.42), ('+ COMPOUND', 48.70), ('CONSTANT', 51.34)]
    vals = [0.18, 0.45, 0.66, 0.82, 0.86]
    pts = [(lerp(gx0 + 40, gx1 - 40, i / 4), gy1 - v * (gy1 - gy0)) for i, v in enumerate(vals)]
    shown = [i for i, (_, tt) in enumerate(labels) if t >= tt]
    if shown:
        last = shown[-1]
        # area fill + line up to last shown point (with draw-on of the newest segment)
        seg = clamp((t - labels[last][1]) / 0.3)
        pl = pts[:last] + ([(lerp(pts[last - 1][0], pts[last][0], seg), lerp(pts[last - 1][1], pts[last][1], seg))] if last > 0 else [pts[0]])
        if len(pl) > 1:
            d.polygon(pl + [(pl[-1][0], gy1), (pl[0][0], gy1)], fill=A(RED, 0.16))
            d.line(pl, fill=A(RED, 1), width=7, joint='curve')
            if GL: GL.line(pl, fill=A(RED, 1), width=14)
        for i in shown:
            if i <= last and (i < last or seg >= 1):
                px, py = pts[i]; d.ellipse([px - 10, py - 10, px + 10, py + 10], fill=A(WHITE, 1))
                lab = labels[i][0]; fn = f(MONO, 19); tw = d.textlength(lab, font=fn)
                txt(d, clamp(px - tw / 2, gx0 + 4, gx1 - tw), gy1 + 14 + (i % 2) * 26, lab, fn, CREAM)
    if t >= 51.34:
        b = ap(t, 51.34); tag(d, pts[3][0] - 160, pts[3][1] - 72, 'CONSTANT STRESS', RED, 24, b)
    # Tadalafil line (green) draws lower from the compound point
    if t >= 53.30:
        q = clamp((t - 53.30) / 1.4); tv = [0.66, 0.6, 0.5]; tp = [pts[2], (pts[3][0], gy1 - tv[1] * (gy1 - gy0)), (pts[4][0], gy1 - tv[2] * (gy1 - gy0))]
        n = q * 2; pl = [tp[0]]
        for i in range(2):
            if n > i: k = min(1, n - i); pl.append((lerp(tp[i][0], tp[i + 1][0], k), lerp(tp[i][1], tp[i + 1][1], k)))
        for k in range(len(pl) - 1):
            # dashed green
            ax_, ay_ = pl[k]; bx_, by_ = pl[k + 1]; Ls = math.hypot(bx_ - ax_, by_ - ay_); m_ = int(Ls // 24) + 1
            for j in range(m_):
                s0 = j * 24 / max(Ls, 1); s1 = min(1, (j * 24 + 14) / max(Ls, 1))
                d.line([(lerp(ax_, bx_, s0), lerp(ay_, by_, s0)), (lerp(ax_, bx_, s1), lerp(ay_, by_, s1))], fill=A(GREEN, 1), width=7)
        if GL and len(pl) > 1: GL.line(pl, fill=A(GREEN, 0.9), width=12)
        if q >= 1: tag(d, tp[2][0] - 250, tp[2][1] + 24, '+ TADALAFIL', GREEN, 24, ap(t, 54.7))
    # organ strain meters
    oy0 = y0 + 640
    for i, (nm, tt) in enumerate([('HEART', 49.94), ('PROSTATE', 50.42)]):
        if t < tt: continue
        b = ap(t, tt); xx = x0 + 40 + i * 470
        strain = lerp(0.2, 0.88, ease_io((t - tt) / 0.6))
        if t >= 56.62: strain = lerp(0.88, 0.48, ease_io((t - 56.62 - i * 0.15) / 0.7))
        organ_icon(d, xx + 30, oy0 + 50, nm, b)
        txt(d, xx + 90, oy0 + 6, nm, f(BEB, 52), WHITE, b); txt(d, xx + 90, oy0 + 60, 'STRAIN', f(MONO, 20), MUTED, b)
        bx0, by0 = xx + 90, oy0 + 92
        d.rectangle([bx0, by0, bx0 + 300, by0 + 34], outline=A((80, 80, 92), b), width=2)
        col = lerp_c(SGREEN, RED, (strain - 0.4) / 0.4); lit_bar(d, bx0 + 3, by0 + 3, bx0 + 3 + 294 * strain, by0 + 31, col, b)
        if GL: GL.rectangle([bx0 + 3, by0 + 3, bx0 + 3 + 294 * strain, by0 + 31], fill=A(col, 0.5 * b))
    if t >= 55.98: tag(d, x0 + 40, y1 - 64, 'BLOOD FLOW ↑', CYAN, 26, ap(t, 55.98))
    if t >= 56.62: tag(d, x0 + 330, y1 - 64, 'STRAIN ↓', GREEN, 26, ap(t, 56.62))
    comp(im, L, a)
def organ_icon(d, cx, cy, kind, a):
    if kind == 'HEART':
        r = 22; d.ellipse([cx - 2 * r, cy - r - 10, cx, cy + r - 10], fill=A(CRIM2, a)); d.ellipse([cx, cy - r - 10, cx + 2 * r, cy + r - 10], fill=A(CRIM2, a))
        d.polygon([(cx - 2 * r + 2, cy - 2), (cx + 2 * r - 2, cy - 2), (cx, cy + 2 * r + 4)], fill=A(CRIM2, a))
        if GL: GL.ellipse([cx - 50, cy - 50, cx + 50, cy + 50], fill=A(CRIM2, 0.5 * a))
    else:
        d.ellipse([cx - 40, cy - 30, cx + 40, cy + 34], outline=A(AMBER, a), width=6); d.line([(cx, cy - 50), (cx, cy + 54)], fill=A(AMBER, a), width=6)
        if GL: GL.ellipse([cx - 50, cy - 40, cx + 50, cy + 44], fill=A(AMBER, 0.4 * a))

# ---------------- 6. COMPARISON COLUMNS (slide in from both sides) ----------------
def scene_compare(im, t):
    t0, t1 = 58.30, 64.95
    if t < t0 or t > t1 + 0.2: return
    out = clamp((t - t1) / 0.18)
    for side, tin in ((0, 58.36), (1, 60.76)):
        if t < tin: continue
        p = back((t - tin) / 0.32, 0.7); dx = (-1 if side == 0 else 1) * (lerp(560, 0, p) + 600 * out ** 2)
        x0 = 48 + side * 500 + dx; y0 = 470; x1 = x0 + 484; y1 = 1250
        frosted(im, (x0, y0, x1, y1), 0.9, 12, 22)
        L, d = layer(); col = RED if side == 0 else VGOLD
        d.rounded_rectangle([x0, y0, x1, y1], radius=22, outline=A(col, 1), width=3)
        d.rectangle([x0 + 22, y0, x1 - 22, y0 + 8], fill=A(col, 1))
        if GL: GL.rounded_rectangle([x0, y0, x1, y1], radius=22, outline=A(col, 0.8), width=8)
        txt(d, x0 + 28, y0 + 30, 'PROTOCOL A' if side == 0 else 'PROTOCOL B', f(MONO, 24), col)
        txt(d, x0 + 28, y0 + 66, 'RECKLESS' if side == 0 else 'OPTIMIZED', f(BEB, 92), CREAM)
        if side == 0:
            # chaos: overlapping unmanaged compound vials, no labs
            for k in range(5):
                vx = x0 + 50 + k * 80; vy = y0 + 240 + (k % 2) * 30
                d.rounded_rectangle([vx, vy, vx + 56, vy + 120], radius=10, fill=A((60, 20, 26), 1), outline=A(RED, 0.8), width=3)
                d.rectangle([vx + 8, vy - 20, vx + 48, vy], fill=A((150, 150, 160), 1))
            txt(d, x0 + 28, y0 + 420, 'LABS', f(MONO, 26), GREY); cross(d, x0 + 130, y0 + 420, RED, 0.9)
            txt(d, x0 + 28, y0 + 470, 'PLAN', f(MONO, 26), GREY); cross(d, x0 + 130, y0 + 470, RED, 0.9)
            if t >= 59.18:
                b = ap(t, 59.18, 0.1); add = 'TADALAFIL ADDED'
                txt(d, x0 + 28, y0 + 540, add, f(MONO, 24), CREAM, b)
                lit_bar(d, x0 + 28, y0 + 600, x1 - 28, y0 + 700, RED, b); txt(d, (x0 + x1) / 2, y0 + 652, 'NOT A FIX', f(BEB, 80), WHITE, b, 'mm')
                if GL: GL.rectangle([x0 + 24, y0 + 596, x1 - 24, y0 + 704], outline=A(RED, b), width=12)
        else:
            # protection layers stack (shield rings)
            layers = [('BLOODWORK', 60.9, CYAN), ('DIALED DOSES', 61.0, CYAN), ('TADALAFIL LAYER', 61.32, VGOLD)]
            for k, (nm, tt, c) in enumerate(layers):
                if t < tt: continue
                b = ap(t, tt, 0.14); yy = y0 + 420 - k * 74 + lerp(-30, 0, back((t - tt) / 0.25))
                if c == VGOLD: lit_bar(d, x0 + 28, yy, x1 - 28, yy + 62, VGOLD, b)
                else: d.rounded_rectangle([x0 + 28, yy, x1 - 28, yy + 62], radius=8, fill=A((10, 30, 40), b), outline=A(c, b), width=3)
                txt(d, x0 + 46, yy + 12, nm, f(MONOB, 28), INK if c == VGOLD else c, b)
                if GL and c == VGOLD: GL.rectangle([x0 + 24, yy - 4, x1 - 24, yy + 66], outline=A(VGOLD, b), width=10)
            for k, (nm, tt) in enumerate([('OPTIMIZED', 62.58), ('INTENTIONAL', 63.62)]):
                if t < tt: continue
                b = ap(t, tt); yy = y0 + 540 + k * 60; check(d, x0 + 32, yy, GREEN, 1.0, b); txt(d, x0 + 76, yy - 2, nm, f(MONO, 28), WHITE, b)
            if t >= 61.72: tag(d, x0 + 28, y0 + 680, 'LAYER OF PROTECTION', GREEN, 26, ap(t, 61.72))
        comp(im, L, 1)

# ---------------- 7. BIG STAT 5MG + 12-month calendar + benefit chips (lower third) ----------------
def scene_stat(im, t):
    t0, t1 = 65.20, 73.75
    a = win(t, t0, t1, 0.2, 0.16)
    if a <= 0: return
    L, d = layer()
    kicker(d, 64, 440, 'COACH AGZ + CLIENTS  ·  PROTOCOL', VGOLD, 1, t, 65.3)
    fb = f(BEB, 360); fm = f(BEB, 170); w5 = d.textlength('5', font=fb); wm = d.textlength('MG', font=fm); X = (W - w5 - wm - 16) / 2
    if t >= 69.02:
        b = ap(t, 69.02, 0.1); sc = lerp(1.35, 1.0, back((t - 69.02) / 0.28, 1.6)); fn = f(BEB, int(360 * sc))
        yy = 480 - (sc - 1) * 160; txt(d, X - (sc - 1) * 90, yy, '5', fn, VGOLD, b)
        if GL: GL.text((X - (sc - 1) * 90, yy), '5', font=fn, fill=A(VGOLD, 0.9 * b))
        txt(d, X + w5 + 16, 640, 'MG', fm, CREAM, b)
        if t >= 69.64:
            c = ap(t, 69.64); fd = f(MONOB, 34); lab = 'DAILY  ·  LOW DOSE'; tw = d.textlength(lab, font=fd)
            lit_bar(d, (W - tw) / 2 - 20, 850, (W + tw) / 2 + 20, 900, VGOLD, c); txt(d, W / 2, 875, lab, fd, INK, c, 'mm')
            if GL: GL.rectangle([(W - tw) / 2 - 24, 846, (W + tw) / 2 + 24, 904], outline=A(VGOLD, c), width=10)
    else:
        txt(d, W / 2, 660, 'LOW DOSE', f(BEB, 200), (70, 74, 92), ap(t, 68.28), 'mm')
    months = 'JFMAMJJASOND'; cx0 = (W - 12 * 62 + 8) / 2
    txt(d, W / 2, 940, 'YEAR-ROUND', f(MONO, 26), CREAM, 1, 'mm')
    for i, m in enumerate(months):
        xx = cx0 + i * 62; on = t >= 67.40 + i * 0.07; c = ap(t, 67.40 + i * 0.07, 0.1) if on else 0
        d.rounded_rectangle([xx, 966, xx + 54, 1026], radius=8, fill=A(VGOLD, c) if on else A((34, 38, 50), 1))
        txt(d, xx + 27, 996, m, f(MONOB, 26), INK if on else (90, 94, 110), 1, 'mm')
        if GL and on: GL.rounded_rectangle([xx, 966, xx + 54, 1026], radius=8, fill=A(VGOLD, 0.5 * c))
    for i, (nm, tt) in enumerate([('VASCULARITY', 70.42), ('PUMPS', 71.68), ('RECOVERY', 72.64)]):
        if t < tt: continue
        b = ap(t, tt, 0.14); yy = 1056 + i * 64; xx = cx0 + lerp(40, 0, b)
        d.rounded_rectangle([xx, yy, xx + 736, yy + 54], radius=10, fill=A((10, 14, 24), 0.9 * b), outline=A(GREEN, b), width=2)
        txt(d, xx + 20, yy + 10, nm, f(MONOB, 30), WHITE, b)
        bar = ease_io((t - tt) / 0.6); lit_bar(d, xx + 300, yy + 16, xx + 300 + 360 * bar, yy + 38, GREEN, b)
        if GL: GL.rectangle([xx + 300, yy + 16, xx + 300 + 360 * bar, yy + 38], fill=A(GREEN, 0.5 * b))
        up_arrow(d, xx + 706, yy + 9, GREEN, 0.9, b)
    comp(im, L, a)

# ---------------- 8. LAB REPORT with reference-range spectrum bars (paper document) ----------------
DOCS = {}
def make_lab_doc():
    im = Image.new('RGBA', (900, 640), (248, 248, 244, 255)); d = ImageDraw.Draw(im)
    d.rectangle([0, 0, 900, 84], fill=(210, 10, 20)); txt(d, 30, 20, 'LAB REPORT  ·  CLIENT PANEL', f(MONOB, 34), WHITE)
    txt(d, 30, 104, 'Marker', f(DMB, 28), (60, 60, 70)); txt(d, 380, 104, 'Reference range position', f(DMB, 28), (60, 60, 70))
    d.line([(24, 148), (876, 148)], fill=(200, 200, 205), width=2)
    for k in range(140): d.point((np.random.default_rng(k).integers(0, 900), np.random.default_rng(k + 999).integers(90, 640)), fill=(215, 215, 210))
    return im
LAB_ROWS = [('PSA, Total', 'PROSTATE', 0.35, 74.86, True), ('Hematocrit', '', 0.86, 76.96, False), ('Estradiol', '', 0.82, 77.20, False), ('Blood Pressure', '', 0.80, 77.44, False)]
def scene_lab(im, t):
    t0, t1 = 73.90, 78.22
    a = win(t, t0, t1, 0.22, 0.16)
    if a <= 0: return
    if 'lab' not in DOCS: DOCS['lab'] = make_lab_doc()
    doc = DOCS['lab'].copy(); d = ImageDraw.Draw(doc, 'RGBA')
    for i, (nm, sub, pos, tt, good) in enumerate(LAB_ROWS):
        y = 176 + i * 110
        txt(d, 30, y, nm, f(DMB, 34), (30, 30, 36));
        if sub: txt(d, 30, y + 44, sub, f(MONO, 22), (210, 10, 20))
        bx0, bx1, by = 380, 860, y + 22
        # spectrum: low blue / in-range green / high amber
        for k in range(int(bx1 - bx0)):
            kk = k / (bx1 - bx0); c = BLUE if kk < 0.25 else (SGREEN if kk < 0.7 else AMBER)
            d.line([(bx0 + k, by), (bx0 + k, by + 22)], fill=c + (255,))
        if t >= tt:
            q = ease_io((t - tt) / 0.45); mxp = bx0 + (bx1 - bx0) * lerp(0.05, pos, q)
            d.polygon([(mxp, by - 4), (mxp - 14, by - 26), (mxp + 14, by - 26)], fill=(20, 20, 26, 255)); d.line([(mxp, by - 4), (mxp, by + 26)], fill=(20, 20, 26, 255), width=4)
            if q >= 1:
                lab = 'IN RANGE' if good else 'HIGH'; c = (20, 150, 70) if good else (200, 110, 0)
                d.rounded_rectangle([bx1 - 150, by + 34, bx1, by + 72], radius=6, fill=c + (255,)); txt(d, bx1 - 75, by + 53, lab, f(MONOB, 22), WHITE, 1, 'mm')
        d.line([(24, y + 96), (876, y + 96)], fill=(225, 225, 228), width=2)
    p = back((t - t0) / 0.35, 0.8); ang = lerp(-9, -2.5, p); sc = lerp(1.0, 1.1, p)
    dd = doc.resize((int(900 * sc), int(640 * sc)), Image.BICUBIC).rotate(ang, expand=True, resample=Image.BICUBIC)
    # shadow
    sh = Image.new('RGBA', dd.size, (0, 0, 0, 0)); sh.putalpha(dd.split()[3].point(lambda v: int(v * 0.55))); sh = sh.filter(ImageFilter.GaussianBlur(18))
    L, d = layer()
    ox = int(W / 2 - dd.width / 2); oy = int(lerp(980, 470, p))
    L.alpha_composite(sh, (ox + 18, oy + 26)); L.alpha_composite(dd, (ox, oy))
    if t >= 75.66:   # forensic bracket on the PSA row
        b = ap(t, 75.66, 0.12); brackets(d, 40, oy + 175, 1040, oy + 330, A(GREEN, b), 30, 7)
        if GL: brackets(GL, 40, oy + 175, 1040, oy + 330, A(GREEN, b), 30, 12)
        tag(d, 60, oy + 760, 'PROSTATE MARKERS · STABLE', GREEN, 28, b) if t < 77.60 else None
    if t >= 77.60:
        b = ap(t, 77.60, 0.12); tag(d, 60, oy + 760, 'EVEN WHEN OTHERS RUN HIGH', AMBER, 28, b)
    comp(im, L, a)

# ---------------- 9. CALLBACK: stack strip returns, chips fall off the table, slot fills ----------------
def scene_callback(im, t):
    t0, t1 = 78.30, 86.10
    a = win(t, t0, t1, 0.2, 0.16)
    if a <= 0: return
    frosted(im, (40, 392, W - 40, 720), 0.55 * a, 14, 22)
    L, d = layer()
    kicker(d, 64, 405, 'YOUR PROTOCOL  ·  ' + ('4 / 4  COMPLETE' if t >= 85.22 else 'LONG-TERM'), GREEN if t >= 85.22 else VGOLD, 1, t, t0)
    x0, y0, w, h = stack_strip(d, t, [t0 - 1, t0 - 1, t0 - 1], t0 - 1, 85.22, y0=460, empty_red=('NOT USING' if t >= 81.12 else 'MISSING'))
    # GAINS / HEALTH chips slide off the right edge ("leaving on the table")
    for i, (nm, tt) in enumerate([('GAINS', 83.52), ('HEALTH', 84.26)]):
        if t < tt - 0.3 or t > 85.6: continue
        b = ap(t, tt - 0.3, 0.14); q = clamp((t - tt) / 0.6)
        xx = lerp(560 + i * 230, 1180, q ** 2); yy = 730 + 300 * q ** 2
        fn = f(BEB, 56); tw = d.textlength(nm, font=fn)
        d.rounded_rectangle([xx, yy, xx + tw + 34, yy + 66], radius=10, fill=A(RED, b)); txt(d, xx + 17, yy + 4, nm, fn, WHITE, b)
        if GL: GL.rounded_rectangle([xx - 4, yy - 4, xx + tw + 38, yy + 70], radius=12, outline=A(RED, b), width=10)
    if 83.0 <= t < 85.22: tag(d, 64, 742, 'LEFT ON THE TABLE', RED, 26, ap(t, 83.0))
    if t >= 85.22: check(d, x0 + 3 * (w + 16) + w - 50, y0 - 46, GREEN, 1.1, ap(t, 85.3))
    comp(im, L, a)

# ---------------- 10. CTA end card ----------------
LOGO = None
def cta(im, t):
    t0 = 86.20
    if t < t0: return
    a = ap(t, t0, 0.25); y0 = lerp(560, 500, a)
    frosted(im, (48, y0, W - 48, 1290), 0.9 * a, 14, 28)
    L, d = layer()
    d.rounded_rectangle([48, y0, W - 48, 1290], radius=28, outline=A(VGOLD, 0.7), width=3); brackets(d, 48, y0, W - 48, 1290, A(VGOLD, 1), 44, 7)
    if GL: brackets(GL, 48, y0, W - 48, 1290, A(VGOLD, a), 44, 14)
    global LOGO
    if LOGO is None:
        lg = Image.open(T + 'logo.jpg').convert('RGB'); s = min(lg.size); lg = lg.crop(((lg.width - s) // 2, (lg.height - s) // 2, (lg.width + s) // 2, (lg.height + s) // 2)).resize((150, 150), Image.LANCZOS)
        m = Image.new('L', (150, 150), 0); ImageDraw.Draw(m).ellipse([0, 0, 149, 149], fill=255); lg.putalpha(m); LOGO = lg
    L.alpha_composite(LOGO, (84, int(y0 + 36)))
    txt(d, 260, y0 + 52, 'COACH AGZ', f(BEB, 72), GOLD); txt(d, 262, y0 + 128, '@coach.agz', f(MONO, 28), GOLD)
    # lab panel review icon row
    if t >= 87.30:
        b = ap(t, 87.30); txt(d, 84, y0 + 220, 'FULL LABS · BLOODWORK REVIEW', f(MONO, 26), CREAM, b)
        for k in range(6):
            hh = [60, 90, 44, 110, 72, 96][k]; xx = 640 + k * 50
            lit_bar(d, xx, y0 + 250 - hh * ease_io((t - 87.3 - k * 0.05) / 0.4), xx + 34, y0 + 250, [CYAN, GREEN, VGOLD, CYAN, GREEN, CYAN][k], b)
    if t >= 89.48:
        b = expo((t - 89.48) / 0.12); s = lerp(1.15, 1.0, expo((t - 89.90) / 0.14)) if t >= 89.90 else 1.0
        lab = 'COMMENT  "LABS"' if t >= 89.90 else 'COMMENT'; fn = f(BEB, int(110 * s)); tw = d.textlength(lab, font=fn)
        yy = y0 + 290; lit_bar(d, 84, yy, 84 + tw + 50, yy + int(124 * s), VGOLD, b); txt(d, 109, yy + 8, lab, fn, INK, b)
        if GL: GL.rectangle([80, yy - 4, 88 + tw + 50, yy + int(124 * s) + 4], outline=A(VGOLD, b), width=14)
    items = [('FULL BREAKDOWN', 91.78), ('FULL FRAMEWORK', 92.74), ('HOW TADALAFIL WORKS', 93.58), ('DOSING', 95.12), ('FIT FOR YOUR GENETICS', 97.84)]
    for i, (nm, tt) in enumerate(items):
        if t < tt: continue
        b = ap(t, tt); yy = y0 + 450 + i * 60 if False else y0 + 450 + (i // 2) * 62; xx = 84 + (i % 2) * 470
        if i == 4: xx = 84; yy = y0 + 450 + 2 * 62
        check(d, xx, yy + 4, GREEN, 0.9, b); txt(d, xx + 44, yy, nm, f(MONO, 28), WHITE, b)
    txt(d, W - 76, 1250, 'FOR RESEARCH & EDUCATIONAL PURPOSES ONLY', f(MONO, 18), MUTED, a, 'rm')
    comp(im, L, a)

# ---------------- topic band (after hook until midpoint) ----------------
def topic_band(im, t):
    if t < HOOK_END or t > MID + 0.15: return
    if 13.55 <= t <= 27.4 or 33.4 <= t <= 45.5: return   # full-screen / split scenes carry their own header
    a = min(clamp((t - HOOK_END) / 0.15), 1 - clamp((t - MID) / 0.15))
    for (s0, s1) in ((13.55, 27.4), (33.4, 45.5)):
        if s0 - 0.15 < t < s0: a = min(a, (s0 - t) / 0.15)
        if s1 < t < s1 + 0.15: a = min(a, (t - s1) / 0.15)
    L, d = layer()
    d.rectangle([8, 232, W, 352], fill=NAVY + (215,)); d.line([(64, 262), (108, 262)], fill=GOLD, width=4)
    txt(d, 122, 248, '@coach.agz', f(MONO, 26), GOLD)
    fn = f(BEB, 62); txt(d, 64, 282, 'TADALAFIL', fn, VGOLD); x = 64 + d.textlength('TADALAFIL', font=fn) + 18
    txt(d, x, 290, 'the underrated compound', f(DMB, 42), CREAM)
    comp(im, L, a)

# ---------------- captions ----------------
ACCENT = {'tadalafil': VGOLD, 'cialis': VGOLD, 'pde5': CYAN, 'five': VGOLD, 'milligrams': VGOLD, 'daily': VGOLD, 'heart': RED, 'prostate': RED,
          'stress': RED, 'cardiovascular': CYAN, 'billions': GREEN, 'labs': VGOLD, 'vasodilation': CYAN, 'reckless': RED, 'protection': GREEN, 'missing': RED}
def nearest_cut(t):
    for c in CUTS:
        if c > t + 0.01: return c
    return 1e9
def build_groups():
    G = []; cur = []
    for i, x in enumerate(WORDS):
        if cur:
            prev = WORDS[cur[-1]]
            if len(cur) >= 3 or x['s'] - prev['e'] > 0.28 or prev['w'][-1] in '.,?!' or x['s'] >= nearest_cut(prev['e']) or len(''.join(WORDS[j]['w'] for j in cur) + x['w']) > 17: G.append(cur); cur = []
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
    nxt = [g for g in GROUPS if WORDS[g[0]]['s'] > WORDS[lo[0]]['s']]
    if t > WORDS[lo[-1]]['e'] + 0.6 and (not nxt or WORDS[nxt[0][0]]['s'] > t): return None
    return lo
CAP_Y = 1335
def captions(im, t):
    g = group_at(t)
    if not g: return
    d = ImageDraw.Draw(im, 'RGBA')
    ws = [WORDS[i]['w'].upper().rstrip(',.') for i in g]
    keys = [WORDS[i]['w'].lower().strip(',.') for i in g]
    size = 120
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
    for k, (w_, x_) in enumerate(zip(ws, xs)):
        if k != act: sd.text((x_ + 4, 46), w_, font=fn, fill=(0, 0, 0, 210))
    cap.alpha_composite(shd.filter(ImageFilter.GaussianBlur(6)))
    lit_bar(cd, bx0, 40 + size * 0.02, bx1, 40 + size * 0.98, RED)
    for k, (w_, x_) in enumerate(zip(ws, xs)):
        col = CREAM if k == act else ACCENT.get(keys[k], CREAM)
        cd.text((x_, 40), w_, font=fn, fill=col, stroke_width=0 if k == act else 3, stroke_fill=(0, 0, 0))
    if abs(s - 1) > 0.002:
        cap = cap.resize((int(W * s), int(300 * s)), Image.BICUBIC); ox = int((W - cap.width) / 2); oy = int(CAP_Y - 40 - (cap.height - 300) / 2)
    else: ox, oy = 0, CAP_Y - 40
    im.alpha_composite(cap, (ox, oy))

# ---------------- frame assembly ----------------
def zoom_at(t):
    seg = sum(1 for c in CUTS if c <= t + 1e-6)
    if seg == 0: return 1.0 if t < 0.84 else lerp(1.0, 1.08, expo((t - 0.84) / 0.12))   # punch-in lands on "Tadalafil"
    return 1.08 if seg % 2 == 0 else 1.0
PUSH = [(27.30, 33.30), (45.45, 58.20), (58.30, 64.95), (65.20, 73.75), (73.90, 78.22), (86.20, 999)]
def push_amt(t):
    g = 0
    for s0, s1 in PUSH: g = max(g, min(ease_io((t - s0 + 0.05) / 0.3), 1 - ease_io((t - s1) / 0.22)))
    return g
def frame(src, t):
    z = zoom_at(t)
    if z != 1.0:
        big = src.resize((int(W * z), int(H * z)), Image.BICUBIC); ox = (big.width - W) // 2; oy = int((big.height - H) * 0.35); src = big.crop((ox, oy, ox + W, oy + H))
    raw = src
    src = split_bg(src, t)
    g = push_amt(t)
    bg = src if g <= 0 else Image.blend(src.filter(ImageFilter.GaussianBlur(16 * g)), Image.new('RGB', (W, H), (5, 8, 16)), 0.66 * g)
    im = bg.convert('RGBA')
    # top/bottom scrim for text legibility (graphics only, footage untouched otherwise)
    yy = np.arange(H); sa = np.where(yy > 1200, np.clip((yy - 1200) / 260, 0, 1) * 110, 0); sa = np.maximum(sa, np.where(yy < 440, (1 - yy / 440) * 110, 0)); sa = (sa * (1 - g)).astype(np.uint8)
    im.alpha_composite(Image.merge('RGBA', [Image.new('L', (W, H), c) for c in NAVY] + [Image.fromarray(np.repeat(sa[:, None], W, 1))]))
    global GL
    glow = Image.new('RGBA', (W, H), (0, 0, 0, 0)); GL = ImageDraw.Draw(glow, 'RGBA')
    scene_timeline(im, t, raw)
    rx_label(im, t); scene_stack(im, t); scene_vessel(im, t); scene_delivery(im, t); scene_graph(im, t)
    scene_compare(im, t); scene_stat(im, t); scene_lab(im, t); scene_callback(im, t); cta(im, t)
    topic_band(im, t); text_hook(im, t)
    GL = None
    if glow.getbbox():
        sm = glow.resize((W // 4, H // 4), Image.BILINEAR)
        g1 = np.asarray(sm.filter(ImageFilter.GaussianBlur(3.5))).astype(np.float32) / 255; g2 = np.asarray(sm.filter(ImageFilter.GaussianBlur(10))).astype(np.float32) / 255
        prem = np.clip(g1[..., :3] * g1[..., 3:] * 2.3 + g2[..., :3] * g2[..., 3:] * 1.8, 0, 1)
        prem = np.asarray(Image.fromarray((prem * 255).astype(np.uint8)).resize((W, H), Image.BILINEAR)).astype(np.float32) / 255
        b = np.asarray(im.convert('RGB')).astype(np.float32) / 255
        im = Image.fromarray(((1 - (1 - b) * (1 - prem)) * 255).astype(np.uint8)).convert('RGBA')
    d = ImageDraw.Draw(im, 'RGBA'); d.rectangle([0, 0, 7, H], fill=GOLD)
    captions(im, t)
    out = im.convert('RGB')
    # camera shake on the two heavy slams (stamp, 5MG)
    for ts in (26.84, 69.02):
        k = round((t - ts) * FPS)
        if k in (0, 1, 2):
            dx = [10, -6, 3][k]; zz = 1.02; big = out.resize((int(W * zz), int(H * zz)), Image.BICUBIC); ox = (big.width - W) // 2 - dx; oy = (big.height - H) // 2
            out = big.crop((ox, oy, ox + W, oy + H)); ImageDraw.Draw(out).rectangle([0, 0, 7, H], fill=GOLD)
    return out

if __name__ == '__main__':
    mode = sys.argv[2]
    if mode == 'stills':
        import os; os.makedirs(T + 'qc', exist_ok=True)
        for tt in [float(x) for x in sys.argv[3:]]:
            n = round(tt * FPS)
            subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', T + 'assembled.mov', '-vf', f'select=eq(n\\,{n})', '-vsync', '0', '-frames:v', '1', T + 'qc/_src.png'])
            frame(Image.open(T + 'qc/_src.png').convert('RGB'), n / FPS).resize((540, 960)).save(T + f'qc/st_{tt:06.2f}.jpg', quality=85)
        sys.exit()
    n0, n1, out = int(sys.argv[3]), int(sys.argv[4]), sys.argv[5]
    dec = subprocess.Popen(['ffmpeg', '-v', 'error', '-i', T + 'assembled.mov', '-vf', f'select=between(n\\,{n0}\\,{n1 - 1})', '-vsync', '0', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], stdout=subprocess.PIPE)
    enc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-crf', '14', '-preset', 'medium', '-pix_fmt', 'yuv420p', out], stdin=subprocess.PIPE)
    for n in range(n0, n1):
        buf = dec.stdout.read(W * H * 3)
        if len(buf) < W * H * 3: print('short', n); break
        enc.stdin.write(frame(Image.frombuffer('RGB', (W, H), buf), n / FPS).tobytes())
    enc.stdin.close(); enc.wait(); dec.kill(); print('done', n0, n1)
