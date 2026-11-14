# Full test 02 — "Online protocols / zero data on you" (bloodwork baseline)
# usage: python3 render.py <workdir> <fontdir> <frame0> <frame1> <out.mp4>
# workdir holds assembled.mp4 (trimmed 1080x1920 30fps cut); this folder holds the json files.
import json, subprocess, sys, math, os
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops

HERE = os.path.dirname(os.path.abspath(__file__))
# Pillow draws text at full strength when the fill alpha is 0; skip invisible text explicitly
_pil_text = ImageDraw.ImageDraw.text
def _text(self, xy, text, fill=None, *a, **k):
    if isinstance(fill, tuple) and len(fill) == 4 and fill[3] <= 2: return
    return _pil_text(self, xy, text, fill, *a, **k)
ImageDraw.ImageDraw.text = _text
WK, FD = sys.argv[1], sys.argv[2]
W, H, FPS = 1080, 1920, 30
WORDS = json.load(open(HERE + '/words_final.json'))
TR = json.load(open(HERE + '/trim.json'))
DUR = TR['newdur']

# ---------- palette ----------
GOLD = (201, 169, 110); CREAM = (244, 241, 234); NAVY = (14, 17, 23); PANEL = (24, 26, 34)
RED = (255, 34, 28); VGOLD = (255, 194, 26); CYAN = (0, 229, 255); GREEN = (30, 255, 110)
DEEP = (2, 3, 8); INK = (6, 8, 14); WHITE = (255, 255, 255); MUTED = (184, 184, 188); DIM = (124, 124, 130)
COARED = (210, 10, 20); CRIMSON = (224, 36, 63)
MONO = 'JBMono-500.ttf'; MONOB = 'JBMono-700.ttf'; BEB = 'BebasNeue.ttf'; DMB = 'DMSans-700.ttf'; DMR = 'DMSans-400.ttf'
BAR = 'Barlow-600.ttf'; BARX = 'Barlow-800.ttf'
_fc = {}
def f(n, s):
    k = (n, int(s))
    if k not in _fc: _fc[k] = ImageFont.truetype(os.path.join(FD, n), int(s))
    return _fc[k]

# ---------- easing ----------
def clamp(x, a=0, b=1): return max(a, min(b, x))
def expo(x): x = clamp(x); return 1 if x >= 1 else 1 - 2 ** (-10 * x)
def ease_io(x): x = clamp(x); return 4 * x ** 3 if x < .5 else 1 - (-2 * x + 2) ** 3 / 2
def back(x, s=1.2): x = clamp(x); return 1 + (s + 1) * (x - 1) ** 3 + s * (x - 1) ** 2  # small settle, used sparingly
def lerp(a, b, t): return a + (b - a) * t
def A(c, a): return tuple(c[:3]) + (int(clamp(a) * 255),)
def win(t, t0, t1, fi=0.2, fo=0.18):
    """visibility 0..1 for an element living t0..t1"""
    if t < t0 or t > t1 + fo: return 0.0
    return min(expo((t - t0) / fi), 1 - clamp((t - t1) / fo))
def appear(t, t0, d=0.12): return expo((t - t0) / d) if t >= t0 else 0.0

# word lookup: first word matching text after approx time
def wt(word, near, end=False):
    best = None
    for w in WORDS:
        if w['w'].lower().strip('.,?!') == word.lower() and abs(w['s'] - near) < 1.5:
            if best is None or abs(w['s'] - near) < abs(best['s'] - near): best = w
    if best is None: raise SystemExit(f'cue not found: {word} ~{near}')
    return best['e'] if end else best['s']

# ---------- cut points (output timeline) ----------
CUTS = []; acc = 0
for a, b in TR['keep'][:-1]:
    acc += b - a; CUTS.append(acc)
def seg_of(t): return sum(1 for c in CUTS if c <= t + 1e-6)

# ---------- face track (smoothed) ----------
_fr = json.load(open(HERE + '/face_raw.json'))
_k = np.array([r[0] for r in _fr], float)
_ok = np.array([r[1] is not None for r in _fr])
def _interp(col):
    v = np.array([r[col] if r[col] is not None else np.nan for r in _fr], float)
    good = ~np.isnan(v); v = np.interp(_k, _k[good], v[good])
    # median 5 then EMA both directions
    m = np.array([np.median(v[max(0, i - 2):i + 3]) for i in range(len(v))])
    for _ in range(2):
        for i in range(1, len(m)): m[i] = m[i - 1] + 0.35 * (m[i] - m[i - 1])
        for i in range(len(m) - 2, -1, -1): m[i] = m[i + 1] + 0.35 * (m[i] - m[i + 1])
    return m
FX, FY, FWD = _interp(1), _interp(2), _interp(3)
def face(t):
    fr = t * FPS
    return (float(np.interp(fr, _k, FX)), float(np.interp(fr, _k, FY)), float(np.interp(fr, _k, FWD)))

# ---------- primitives ----------
GL = None
def brackets(d, x0, y0, x1, y1, col, L=34, w=4):
    for (cx, cy, sx, sy) in [(x0, y0, 1, 1), (x1, y0, -1, 1), (x0, y1, 1, -1), (x1, y1, -1, -1)]:
        d.line([(cx, cy), (cx + sx * L, cy)], fill=col, width=w); d.line([(cx, cy), (cx, cy + sy * L)], fill=col, width=w)
def lit_bar(d, x0, y0, x1, y1, col, a=1.0):
    if x1 <= x0: return
    h = max(1, int(y1 - y0))
    for i in range(h):
        k = i / h; c = tuple(int(min(255, v * (1.18 - 0.36 * k) + (40 if k < 0.12 else 0))) for v in col)
        d.line([(x0, y0 + i), (x1, y0 + i)], fill=c + (int(255 * a),))
def tag(d, x, y, label, col=RED, size=30, a=1.0, glow=True, fg=None):
    fn = f(MONO, size); tw = d.textlength(label, font=fn); h = size + 16
    lit_bar(d, x, y, x + tw + 24, y + h, col, a)
    d.text((x + 12, y + 5), label, font=fn, fill=A(fg or (INK if col in (VGOLD, GREEN, GOLD) else WHITE), a))
    if GL and glow: GL.rectangle([x - 4, y - 4, x + tw + 28, y + h + 4], outline=A(col, a), width=8)
    return x + tw + 24
def txt(d, x, y, s, font, col, a=1.0, anchor=None): d.text((x, y), s, font=font, fill=A(col, a), anchor=anchor)
def frosted(im, box, dark=0.86, blur=10, radius=0, tint=DEEP, a=1.0):
    x0, y0, x1, y1 = [int(round(v)) for v in box]
    x0, y0 = max(0, x0), max(0, y0); x1, y1 = min(W, x1), min(H, y1)
    if x1 <= x0 or y1 <= y0: return
    reg = im.crop((x0, y0, x1, y1)).convert('RGB').filter(ImageFilter.GaussianBlur(blur))
    reg = Image.blend(reg, Image.new('RGB', reg.size, tint), dark)
    if a < 1: reg = Image.blend(im.crop((x0, y0, x1, y1)).convert('RGB'), reg, clamp(a))
    reg = reg.convert('RGBA')
    if radius:
        m = Image.new('L', reg.size, 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, reg.width - 1, reg.height - 1], radius=radius, fill=255)
        im.paste(reg, (x0, y0), m)
    else: im.paste(reg, (x0, y0))
def check(d, x, y, col, s=1.0, a=1.0, w=6):
    d.line([(x, y), (x + 12 * s, y + 12 * s), (x + 32 * s, y - 12 * s)], fill=A(col, a), width=w, joint='curve')
def cross(d, x, y, col, s=1.0, a=1.0, w=6):
    d.line([(x - 13 * s, y - 13 * s), (x + 13 * s, y + 13 * s)], fill=A(col, a), width=w)
    d.line([(x - 13 * s, y + 13 * s), (x + 13 * s, y - 13 * s)], fill=A(col, a), width=w)
def kicker(d, x, y, label, col=VGOLD, a=1.0, p=1.0, size=28):
    L = 46 * expo(p * 2); d.line([(x, y + size * 0.55), (x + L, y + size * 0.55)], fill=A(col, a), width=3)
    q = clamp(p * 2 - 0.6)
    if q > 0:
        n = int(len(label) * q + 0.999); txt(d, x + 60, y, spaced(label[:n]), f(BAR, size), col, a)
def spaced(s): return ' '.join(s) if False else s
def padlock(d, cx, cy, col, a=1.0, s=1.0, open_=0.0):
    w_, h_ = 34 * s, 28 * s
    d.rounded_rectangle([cx - w_ / 2, cy - h_ / 2 + 8 * s, cx + w_ / 2, cy + h_ / 2 + 8 * s], radius=4 * s, fill=A(col, a))
    sh = -10 * s * open_
    d.arc([cx - 11 * s, cy - 22 * s + sh, cx + 11 * s, cy + 2 * s + sh], 180, 360, fill=A(col, a), width=int(5 * s))
    d.line([(cx - 11 * s, cy - 10 * s + sh), (cx - 11 * s, cy - 2 * s)], fill=A(col, a), width=int(5 * s))
    d.line([(cx + 11 * s, cy - 10 * s + sh), (cx + 11 * s, cy - 2 * s + sh)], fill=A(col, a), width=int(5 * s))

LOGO = None
def logo_badge(size):
    global LOGO
    if LOGO is None:
        p = os.path.join(HERE, '../../brand/logo/coach-agz-logo-round.jpg')
        LOGO = Image.open(p).convert('RGB')
    lg = LOGO.resize((size, size), Image.LANCZOS).convert('RGBA')
    m = Image.new('L', (size, size), 0); ImageDraw.Draw(m).ellipse([0, 0, size - 1, size - 1], fill=255); lg.putalpha(m)
    return lg

# =====================================================================
# CUES (output timeline)
# =====================================================================
T_HOOK_END = wt('guess', 5.8)                 # 5.80
T_MID = DUR / 2                               # topic band exits here
C = dict(
    protocol=wt('protocol', 1.94),
    conf_in=wt('guess', 5.8), confidence=wt('confidence', 7.1), because=wt('because', 7.7),
    bloods=wt('bloods', 10.9), aromatize=wt('aromatize', 12.1), testo=wt('testosterone', 13.9), lipids=wt('lipids', 15.3),
    hct=wt('hematocrit', 16.0), liver=wt('liver', 16.8), kidney=wt('kidney', 17.9), something=wt('something', 20.0),
    surface=wt('surface', 21.3), worse=wt('worse', 23.06), essentially=wt('essentially', 23.6), recommendation=wt('recommendation', 24.7),
    zero=wt('zero', 26.7), physio_end=wt('physiology', 27.96, True), even=wt('even', 29.6), foundational=wt('foundational', 30.7),
    anecdotal=wt('anecdotal', 31.9), most=wt('most', 34.06), you1=wt('you', 37.46), ten=wt('10', 38.6), worse2=wt('worse', 39.28),
    two=wt('two', 40.1), age=wt('age', 41.04), weight=wt('weight', 41.74), training=wt('training', 42.34), input=wt('input', 43.66),
    output=wt('output', 44.42), walks=wt('walks', 45.24), fine=wt('fine', 45.88), crashes=wt('crashes', 47.02), why=wt('why', 48.42),
    enzyme=wt('enzyme', 50.06), receptor=wt('receptor', 51.86), lipid=wt('lipid', 53.72), liver2=wt('liver', 55.10),
    cardio=wt('cardiovascular', 56.42), androgen=wt('androgen', 58.92), variable=wt('variable', 60.68), compound=wt('compound', 62.44),
    person=wt('person', 63.58), and_=wt('and', 65.02), five=wt('500', 66.02), panels=wt('panels', 67.36), pattern=wt('pattern', 69.44),
    compound2=wt('compound', 71.10), bad=wt('bad', 71.78), good=wt('good', 72.98), patterns=wt('patterns', 73.22), hurt=wt('hurt', 74.76),
    flying=wt('flying', 75.24), time=wt('time', 76.94), something2=wt('something', 77.40), bloodwork2=wt('blood', 79.26),
    im=wt("i'm", 79.82), run=wt('run', 81.40), direction=wt('direction', 83.22), drawn=wt('drawn', 85.56), first=wt('first', 85.90),
    anything=wt('anything', 87.16), blood3=wt('blood', 88.18), road=wt('road', 89.60), opinion=wt('opinion', 91.44),
    never=wt('never', 93.04), lived=wt('lived', 93.36), that_=wt('that', 93.90), guide=wt('guide', 95.44), markers=wt('markers', 96.56),
    each=wt('each', 98.74), comment=wt('comment', 100.28), baseline=wt('baseline', 100.92),
)

# =====================================================================
# LAYOUT: footage transform + caption placement, blended over time
# modes: face | sidebar | full (pip) | split
# =====================================================================
SPLIT_DY = -470                     # footage shift up in split
SIDE_DX = -262                      # footage shift left with right sidebar
LAYOUTS = [  # (start, end, mode, pip_center)
    (C['even'] - 0.25, C['two'] - 0.05, 'full', (540, 470)),
    (C['two'] - 0.05, C['why'] - 0.10, 'split', None),
    (C['why'] - 0.10, C['and_'] - 0.05, 'side', None),
    (C['blood3'] - 0.30, C['that_'] - 0.05, 'full', (812, 452)),
    (C['that_'] - 0.05, DUR + 1, 'split', None),
]
TIN, TOUT = 0.42, 0.36
def layout_at(t):
    """returns weights dict for each mode active and the pip center"""
    for (t0, t1, m, pc) in LAYOUTS:
        if t0 <= t < t1 + TOUT:
            p = ease_io((t - t0) / TIN) * (1 - ease_io((t - t1) / TOUT))
            return m, p, pc, t0, t1
    return 'face', 0.0, None, 0, 0

def cap_place(t):
    m, p, pc, *_ = layout_at(t)
    y, cx, mw = 1335, 540, 920
    if m == 'split': y = lerp(1335, 880, p)
    if m == 'side': cx, mw = lerp(540, 310, p), lerp(920, 560, p)
    if m == 'full': y = lerp(1335, 1352, p)
    if C['run'] - 1.6 <= t < C['blood3']:  # stepper strip occupies the chest; captions sit just under it
        y = lerp(1335, 1352, win(t, C['run'] - 1.6, C['blood3'] - 0.3, 0.3, 0.3))
    return y, cx, mw

def footage(src, t):
    """returns RGBA frame of the footage after punch-in/layout moves (face never blurred)"""
    m, p, pc, *_ = layout_at(t)
    z = 1.0 if seg_of(t) % 2 == 0 else 1.075
    if t < C['protocol']: z = 1.0
    elif t < T_HOOK_END: z = 1.075
    dx = dy = 0.0
    if m == 'split': dy = SPLIT_DY * p
    if m == 'side': dx = SIDE_DX * p
    fx, fy, _ = face(t)
    # zoom about the face so punch-ins keep the eyes in place
    ax, ay = 540 + (fx - 540) * 0.5, 960 + (fy - 960) * 0.5
    # inverse affine: out(x,y) -> src
    a = 1 / z
    c0 = ax - (ax + dx) * a; c1 = ay - (ay + dy) * a
    out = src.transform((W, H), Image.AFFINE, (a, 0, c0, 0, a, c1), Image.BICUBIC, fillcolor=NAVY)
    return out.convert('RGBA')

# =====================================================================
# BACKGROUND SCENES (full mode)
# =====================================================================
def navy_bg():
    bg = Image.new('RGB', (W, H), NAVY)
    yy, xx = np.mgrid[0:H, 0:W]
    g = np.exp(-(((xx - 980) / 620.0) ** 2 + ((yy - 260) / 700.0) ** 2)) * 0.9
    arr = np.asarray(bg).astype(np.float32)
    arr += g[..., None] * (np.array([29, 29, 30]) - np.array(NAVY))
    # faint grid
    arr[::60, :, :] += 5; arr[:, ::60, :] += 5
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).convert('RGBA')
NAVYBG = None

def full_scene(im, src_fx, t, pc, p, t0, t1, draw_fn):
    """face shrinks into a PiP circle (handoff), graphic scene builds behind"""
    global NAVYBG
    if NAVYBG is None: NAVYBG = navy_bg()
    fx, fy, fw = face(t)
    R = lerp(1250, 196, p)
    s = lerp(1.0, 0.62, p)
    tx, ty = lerp(fx, pc[0], p), lerp(fy, pc[1] + 18, p)
    a = 1 / s; c0 = fx - tx * a; c1 = fy - ty * a
    fr = src_fx.transform((W, H), Image.AFFINE, (a, 0, c0, 0, a, c1), Image.BICUBIC, fillcolor=NAVY).convert('RGBA')
    base = NAVYBG.copy()
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay, 'RGBA')
    draw_fn(d, t, lay)
    al = clamp((p - 0.35) / 0.65)
    if al < 1: lay.putalpha(lay.split()[3].point(lambda v: int(v * al)))
    base.alpha_composite(lay)
    # circle mask (supersampled edge)
    m = Image.new('L', (W, H), 0); md = ImageDraw.Draw(m)
    md.ellipse([tx - R, pc[1] - R if p > 0.999 else ty - 18 - R, tx + R, (pc[1] if p > 0.999 else ty - 18) + R], fill=255)
    base.paste(fr, (0, 0), m.filter(ImageFilter.GaussianBlur(1.2)))
    d = ImageDraw.Draw(base, 'RGBA'); cy = (pc[1] if p > 0.999 else ty - 18)
    if p > 0.6:
        ra = clamp((p - 0.6) / 0.4)
        d.ellipse([tx - R - 4, cy - R - 4, tx + R + 4, cy + R + 4], outline=A(VGOLD, ra), width=5)
        if GL: GL.ellipse([tx - R - 6, cy - R - 6, tx + R + 6, cy + R + 6], outline=A(VGOLD, ra * 0.8), width=10)
        # live dot + handle
        d.ellipse([tx + R * 0.62, cy + R * 0.62, tx + R * 0.62 + 30, cy + R * 0.62 + 30], fill=A(RED, ra), outline=A(NAVY, ra), width=4)
    # brand chrome
    if p > 0.5:
        ra = clamp((p - 0.5) / 0.5)
        d.rectangle([0, 0, 5, H], fill=A(GOLD, ra))
        txt(d, 60, 1478, 'FOR RESEARCH & EDUCATIONAL PURPOSES ONLY', f(MONO, 20), DIM, ra)
    return base

# =====================================================================
# SCENES
# =====================================================================
def hook(im, t):
    if t >= T_HOOK_END + 0.15: return
    a = 1 - clamp((t - T_HOOK_END) / 0.15)
    s = lerp(1.0, 1.04, clamp(t / T_HOOK_END))
    lay = Image.new('RGBA', (W, 420), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    l1a, l1b = 'Online ', 'PROTOCOLS'; l2 = 'zero data on you'
    f1 = f(BEB, 118)
    w1 = d.textlength(l1a, font=f1) + d.textlength(l1b, font=f1); w2 = d.textlength(l2, font=f1)
    # black rounded plates for contrast over the bright car window
    pad = 26
    d.rounded_rectangle([540 - w1 / 2 - pad, 34, 540 + w1 / 2 + pad, 170], radius=22, fill=(4, 6, 12, 228))
    d.rounded_rectangle([540 - w2 / 2 - pad, 182, 540 + w2 / 2 + pad, 318], radius=22, fill=(4, 6, 12, 228))
    x = 540 - w1 / 2
    d.text((x, 44), l1a, font=f1, fill=WHITE); d.text((x + d.textlength(l1a, font=f1), 44), l1b, font=f1, fill=VGOLD)
    d.text((540 - w2 / 2, 192), l2, font=f1, fill=WHITE)
    d.rectangle([540 - w1 / 2 - pad, 34, 540 - w1 / 2 - pad + 7, 170], fill=VGOLD)
    if s != 1: lay = lay.resize((int(W * s), int(420 * s)), Image.BICUBIC)
    if a < 1: lay.putalpha(lay.split()[3].point(lambda v: int(v * a)))
    im.alpha_composite(lay, (int((W - lay.width) / 2), int(268 - (lay.height - 420) / 2)))

def topic_band(im, t):
    a = win(t, T_HOOK_END, T_MID, 0.15, 0.15)
    lo, pp, *_ = layout_at(t)
    if lo == 'full': a *= 1 - pp
    if a <= 0: return
    d = ImageDraw.Draw(im, 'RGBA')
    a *= (1 - pp) ** 3 if lo == 'full' else 1
    if a <= 0.01: return
    frosted(im, (40, 222, 1040, 362), 0.80, 14, 18, a=a)
    d.rounded_rectangle([40, 222, 1040, 362], radius=18, outline=A((60, 60, 70), a), width=2)
    d.rectangle([40, 240, 46, 344], fill=A(VGOLD, a))
    fn = f(BEB, 70); x = 72
    for s, col in [('Your ', WHITE), ('PROTOCOL', VGOLD), (' starts with bloodwork', WHITE)]:
        d.text((x, 236), s, font=fn, fill=A(col, a)); x += d.textlength(s, font=fn)
    tg = appear(t, T_HOOK_END + 0.35, 0.18) * a
    if tg > 0:
        d.text((74, 314), '◆', font=f(DMB, 22), fill=A(VGOLD, tg))
        txt(d, 104, 312, '500+ ENHANCED PANELS REVIEWED', f(MONO, 26), CREAM, tg)
        txt(d, 1016, 312, '@coach.agz', f(MONO, 24), DIM, tg, anchor='ra')
    if a < 1:  # fade the frosted plate too
        pass

# ---- S2: confidence vs data meter (floating glass card, left) ----
def s_confidence(im, t):
    a = win(t, C['conf_in'] + 0.05, C['because'] - 0.05, 0.22, 0.2)
    if a <= 0: return
    x0, y0, x1, y1 = 36, 600, 392, 980
    dx = lerp(-60, 0, expo((t - C['conf_in']) / 0.3)) - 80 * clamp((t - C['because'] + 0.05) / 0.2) ** 2
    x0 += dx; x1 += dx
    frosted(im, (x0, y0, x1, y1), 0.88, 12, 22, a=a)
    d = ImageDraw.Draw(im, 'RGBA')
    d.rounded_rectangle([x0, y0, x1, y1], radius=22, outline=A((70, 70, 80), a), width=2)
    d.rectangle([x0, y0 + 24, x0 + 6, y1 - 24], fill=A(VGOLD, a))
    txt(d, x0 + 28, y0 + 22, 'ADVICE AUDIT', f(MONO, 26), VGOLD, a)
    # bars
    pc = expo((t - C['conf_in'] - 0.15) / 1.1)
    for i, (lab, frac, col, val) in enumerate([('CONFIDENCE', pc, VGOLD, f'{int(round(100 * pc))}%'), ('DATA ON YOU', 0.0, RED, '0%')]):
        y = y0 + 96 + i * 132
        txt(d, x0 + 28, y, lab, f(BAR, 36), CREAM, a)
        fn = f(BEB, 56); vw = d.textlength(val, font=fn)
        blink = 1 if (i == 0 or int(t * 4) % 2 == 0) else 0.35
        txt(d, x1 - 26 - vw, y - 14, val, fn, col, a * blink)
        bx0, by0, bx1, by1 = x0 + 28, y + 50, x1 - 26, y + 84
        d.rectangle([bx0, by0, bx1, by1], outline=A((80, 84, 100), a), width=2)
        if frac > 0:
            lit_bar(d, bx0 + 3, by0 + 3, lerp(bx0 + 3, bx1 - 3, frac), by1 - 3, col, a)
            if GL: GL.rectangle([bx0 + 3, by0 + 3, lerp(bx0 + 3, bx1 - 3, frac), by1 - 3], fill=A(col, a * 0.6))
        else:
            # flatline marker
            d.line([(bx0 + 6, (by0 + by1) / 2), (bx1 - 6, (by0 + by1) / 2)], fill=A(RED, a * 0.6), width=2)
    q = appear(t, C['confidence'] + 0.1, 0.12) * a
    if q > 0: tag(d, x0 + 28, y1 - 74, 'MISMATCH', RED, 28, q)

# ---- S3: HUD scan of the subject + readout list (left column) ----
HUD_ROWS = [('BLOOD PANEL', 'NOT RUN', 'bloods'), ('E2 / AROMATASE', '???', 'aromatize'), ('BASELINE TEST', '???', 'testo'),
            ('LIPIDS', '???', 'lipids'), ('HEMATOCRIT', '???', 'hct'), ('LIVER  ALT/AST', '???', 'liver'), ('KIDNEY  eGFR', '???', 'kidney')]
HUD_T0 = C['because'] + 0.05
HUD_T1 = C['essentially'] - 0.05
def s_hud(im, t):
    a = win(t, HUD_T0, HUD_T1 + 5.0, 0.25, 0.25)  # readout panel persists into the Rx slip morph
    if t < HUD_T0: return
    d = ImageDraw.Draw(im, 'RGBA')
    fx, fy, fw = face(t)
    z = 1.075 if seg_of(t) % 2 else 1.0
    ha = win(t, HUD_T0, HUD_T1, 0.2, 0.2)
    if ha > 0:
        # scan brackets around the head (tracked)
        bw = fw * z * 0.68; bh = fw * z * 0.92
        bx0, by0, bx1, by1 = fx - bw, fy - bh * 1.05, fx + bw, fy + bh * 0.95
        grow = lerp(1.25, 1.0, expo((t - HUD_T0) / 0.25))
        cx, cy = (bx0 + bx1) / 2, (by0 + by1) / 2
        bx0, bx1 = cx + (bx0 - cx) * grow, cx + (bx1 - cx) * grow; by0, by1 = cy + (by0 - cy) * grow, cy + (by1 - cy) * grow
        brackets(d, bx0, by0, bx1, by1, A(CYAN, ha), 46, 5)
        if GL: brackets(GL, bx0, by0, bx1, by1, A(CYAN, ha), 46, 12)
        txt(d, bx0, by0 - 40, 'SUBJECT: YOU', f(MONO, 26), CYAN, ha)
        txt(d, bx1, by0 - 40, 'DATA 0/7', f(MONO, 26), RED, ha * (1 if int(t * 3) % 2 else 0.5), anchor='ra')
        # scan sweep for "something under the surface"
        if C['something'] <= t <= C['worse'] + 0.4:
            sp = clamp((t - C['something']) / (C['surface'] + 0.5 - C['something']))
            sy = lerp(by0 - 40, 1700, ease_io(sp))
            sa = ha * (1 - clamp((t - C['worse']) / 0.4))
            for k in range(26):
                d.line([(0, sy - k * 3), (W, sy - k * 3)], fill=A(CYAN, sa * 0.10 * (1 - k / 26)))
            d.line([(0, sy), (W, sy)], fill=A(CYAN, sa * 0.9), width=3)
            if GL: GL.line([(0, sy), (W, sy)], fill=A(CYAN, sa), width=10)
            # anomaly detected below the surface (chest)
            if sy > 1260:
                pa = appear(t, C['surface'] + 0.2, 0.14) * sa / max(sa, 1e-6) * ha
                ax, ay = fx + 40, 1300
                r = 18 + 8 * math.sin(t * 9)
                d.ellipse([ax - r, ay - r, ax + r, ay + r], outline=A(RED, pa), width=4)
                d.ellipse([ax - 8, ay - 8, ax + 8, ay + 8], fill=A(RED, pa))
                if GL: GL.ellipse([ax - r - 4, ay - r - 4, ax + r + 4, ay + r + 4], outline=A(RED, pa), width=10)
    # readout list (left column)
    if t < HUD_T1 + 0.05:
        x0, y0, x1 = 34, 560, 394
        y1 = y0 + 92 + 66 * len(HUD_ROWS) + (150 if t >= C['something'] else 0) * expo((t - C['something']) / 0.3)
        ra = win(t, HUD_T0, HUD_T1, 0.25, 0.1)
        if ra <= 0: return
        frosted(im, (x0, y0, x1, y1), 0.88, 12, 20, a=ra)
        d = ImageDraw.Draw(im, 'RGBA')
        d.rounded_rectangle([x0, y0, x1, y1], radius=20, outline=A(CYAN, ra * 0.6), width=2)
        txt(d, x0 + 22, y0 + 20, 'YOUR FILE', f(MONO, 26), CYAN, ra)
        txt(d, x1 - 22, y0 + 20, 'COACH VIEW', f(MONO, 20), DIM, ra, anchor='ra')
        d.line([(x0 + 20, y0 + 64), (x1 - 20, y0 + 64)], fill=A((60, 70, 80), ra), width=2)
        for i, (lab, val, cue) in enumerate(HUD_ROWS):
            q = appear(t, C[cue] - 0.04, 0.12) * ra
            if q <= 0: continue
            y = y0 + 84 + i * 66; sl = lerp(-24, 0, q)
            txt(d, x0 + 24 + sl, y, lab, f(BAR, 33), CREAM, q)
            fn = f(MONOB, 28); vw = d.textlength(val, font=fn)
            d.rectangle([x1 - 30 - vw - 12, y + 2, x1 - 22, y + 40], fill=A((60, 6, 10), q), outline=A(RED, q), width=2)
            txt(d, x1 - 28 - vw, y + 6, val, fn, (255, 120, 110), q)
            d.line([(x0 + 22, y + 54), (x1 - 22, y + 54)], fill=A((40, 46, 56), q), width=1)
        if t >= C['something']:
            q = expo((t - C['something'] - 0.15) / 0.25) * ra
            y = y0 + 84 + 66 * len(HUD_ROWS) + 4
            txt(d, x0 + 24, y, 'UNDER THE SURFACE', f(MONO, 22), RED, q)
            # rising risk sparkline
            px0, px1, py0, py1 = x0 + 24, x1 - 24, y + 40, y + 120
            d.line([(px0, py1), (px1, py1)], fill=A((60, 66, 80), q), width=2)
            sp = clamp((t - C['surface']) / (C['worse'] - C['surface'] + 0.2))
            pts = []
            for k in range(41):
                u = k / 40
                if u > sp: break
                v = 0.08 + 0.05 * math.sin(u * 13) + (0.85 * ((u - 0.45) / 0.55) ** 2 if u > 0.45 else 0)
                pts.append((lerp(px0, px1, u), lerp(py1 - 4, py0, v)))
            if len(pts) > 1:
                d.line(pts, fill=A(RED, q), width=4)
                if GL: GL.line(pts, fill=A(RED, q), width=10)
                ex, ey = pts[-1]; d.ellipse([ex - 6, ey - 6, ex + 6, ey + 6], fill=A(RED, q))

# ---- S4: the Rx slip (paper document, left) ----
def s_rx(im, t):
    t0, t1 = C['essentially'] - 0.05, C['even'] - 0.25
    a = win(t, t0, t1, 0.3, 0.2)
    if a <= 0: return
    p = expo((t - t0) / 0.35)
    pw, ph = 372, 640
    paper = Image.new('RGBA', (pw, ph), (236, 233, 226, 255)); d = ImageDraw.Draw(paper)
    # paper texture
    rng = np.random.default_rng(3); nz = (rng.standard_normal((ph, pw)) * 5).astype(np.int16)
    arr = np.asarray(paper).astype(np.int16); arr[..., :3] += nz[..., None]; paper = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)); d = ImageDraw.Draw(paper)
    d.rectangle([0, 0, pw, 64], fill=COARED)
    d.text((18, 14), 'PROTOCOL RECOMMENDATION', font=f(MONOB, 22), fill=WHITE)
    rows = [('CLIENT', 'anon'), ('SOURCE', 'internet'), ('BLOODS SEEN', 'none'), ('BASELINE T', '—'), ('E2 / HCT', '—'), ('LIPIDS / LIVER', '—')]
    for i, (k, v) in enumerate(rows):
        y = 86 + i * 50
        d.text((18, y), k, font=f(MONO, 22), fill=(90, 92, 100)); d.text((pw - 18, y), v, font=f(DMB, 27), fill=(30, 32, 40), anchor='ra')
        d.line([(16, y + 38), (pw - 16, y + 38)], fill=(200, 198, 192), width=1)
    y = 86 + 6 * 50 + 6
    d.text((18, y), 'Rx', font=f(DMB, 34), fill=(30, 32, 40))
    for k in range(3):  # dose lines (scribbled, unreadable on purpose)
        yy = y + 50 + k * 34; d.rounded_rectangle([60, yy, 60 + [250, 200, 230][k], yy + 14], radius=7, fill=(70, 72, 84))
    d.text((18, ph - 64), 'DATA INPUTS', font=f(MONO, 22), fill=(90, 92, 100))
    zq = appear(t, C['zero'], 0.12)
    d.text((pw - 18, ph - 76), '0 / 7', font=f(BEB, 52), fill=(210, 10, 20) if zq > 0 else (40, 40, 48), anchor='ra')
    # desaturate slightly
    paper = Image.blend(paper.convert('RGB'), paper.convert('L').convert('RGB'), 0.25).convert('RGBA')
    ang = lerp(-9, -2.5, p)
    rot = paper.rotate(ang, Image.BICUBIC, expand=True)
    cx, cy = lerp(-200, 214, p), lerp(820, 862, p)
    # shadow
    sh = Image.new('RGBA', rot.size, (0, 0, 0, 0)); sh.putalpha(rot.split()[3].point(lambda v: int(v * 0.55)))
    sh = sh.filter(ImageFilter.GaussianBlur(14))
    blur = (1 - p) * 6
    if blur > 0.3: rot = rot.filter(ImageFilter.GaussianBlur(blur))
    if a < 1:
        rot.putalpha(rot.split()[3].point(lambda v: int(v * a))); sh.putalpha(sh.split()[3].point(lambda v: int(v * a)))
    im.alpha_composite(sh, (int(cx - rot.width / 2 + 12), int(cy - rot.height / 2 + 18)))
    im.alpha_composite(rot, (int(cx - rot.width / 2), int(cy - rot.height / 2)))
    d = ImageDraw.Draw(im, 'RGBA')
    if zq > 0:
        # red detection bracket on DATA INPUTS
        bx0, by0, bx1, by1 = cx - pw / 2 - 2, cy + ph / 2 - 100, cx + pw / 2 + 8, cy + ph / 2 - 6
        brackets(d, bx0, by0, bx1, by1, A(RED, zq * a), 26, 6)
        if GL: brackets(GL, bx0, by0, bx1, by1, A(RED, zq * a), 26, 12)
        tag(d, bx0 + 4, by1 + 12, 'ZERO DATA ON YOU', RED, 26, zq * a)
    sq = appear(t, C['recommendation'] + 0.25, 0.1)
    if sq > 0:  # stamp lands
        s = lerp(1.6, 1.0, sq); st = Image.new('RGBA', (300, 90), (0, 0, 0, 0)); sd = ImageDraw.Draw(st)
        sd.rounded_rectangle([4, 4, 296, 86], radius=10, outline=(255, 34, 28, 235), width=6)
        sd.text((150, 46), 'UNVERIFIED', font=f(BEB, 62), fill=(255, 34, 28, 235), anchor='mm')
        st = st.resize((int(300 * s), int(90 * s)), Image.BICUBIC).rotate(12, Image.BICUBIC, expand=True)
        st.putalpha(st.split()[3].point(lambda v: int(v * a * sq)))
        im.alpha_composite(st, (int(cx - st.width / 2 + 20), int(cy - 110 - st.height / 2)))

# ---- S5: bell curve (full scene) ----
def g_bell(d, t, lay):
    x0, x1, yb, ht = 90, 990, 1180, 330
    kicker(d, 90, 700, 'SAME PROTOCOL · 100 GUYS', VGOLD, 1, clamp((t - C['even'] + 0.1) / 0.6))
    hp = expo((t - C['foundational']) / 0.5)
    txt(d, 90, 748, 'HOW THEY RESPOND', f(BEB, 92), CREAM, hp)
    def g(u): return math.exp(-((u - 0.42) / 0.16) ** 2 / 2)
    dp = ease_io((t - C['foundational'] - 0.1) / 1.0)
    N = 160; pts = [(lerp(x0, x1, k / N), yb - ht * g(k / N)) for k in range(N + 1)]
    # axis
    d.line([(x0, yb), (lerp(x0, x1, dp), yb)], fill=A((90, 94, 110), 1), width=3)
    txt(d, x0, yb + 18, 'BETTER', f(MONO, 22), DIM, dp); txt(d, x1, yb + 18, 'WORSE', f(MONO, 22), DIM, dp, anchor='ra')
    # "works for most" fill
    mp = expo((t - C['most']) / 0.5)
    if mp > 0:
        lo, hi = 0.24, 0.60
        poly = [(lerp(x0, x1, lo), yb)] + [p for p in pts if lerp(x0, x1, lo) <= p[0] <= lerp(x0, x1, hi)] + [(lerp(x0, x1, hi), yb)]
        d.polygon(poly, fill=A(GOLD, 0.30 * mp))
        for xx in (lerp(x0, x1, lo), lerp(x0, x1, hi)):
            for yy in range(int(yb - ht - 10), int(yb), 14): d.line([(xx, yy), (xx, yy + 7)], fill=A(GOLD, 0.7 * mp), width=2)
        txt(d, lerp(x0, x1, 0.42), yb - ht * 0.45, 'WORKS FOR', f(MONO, 24), GOLD, mp, anchor='mm')
        txt(d, lerp(x0, x1, 0.42), yb - ht * 0.45 + 46, 'MOST', f(BEB, 66), CREAM, mp, anchor='mm')
    # tail (worse)
    tp = expo((t - C['ten']) / 0.35)
    if tp > 0:
        lo = 0.72; poly = [(lerp(x0, x1, lo), yb)] + [p for p in pts if p[0] >= lerp(x0, x1, lo)] + [(x1, yb)]
        d.polygon(poly, fill=A(RED, 0.55 * tp))
        if GL: GL.polygon(poly, fill=A(RED, 0.35 * tp))
    n = int(N * dp)
    if n > 1:
        d.line(pts[:n + 1], fill=A(CREAM, 1), width=5)
        if GL: GL.line(pts[:n + 1], fill=A(GOLD, 0.5), width=8)
    # YOU marker drops into the tail
    yp = clamp((t - C['you1'] + 0.05) / 0.28)
    if yp > 0:
        ux = lerp(x0, x1, 0.83); uy_t = yb - ht * g(0.83)
        uy = lerp(uy_t - 300, uy_t, expo(yp))
        d.line([(ux, uy - 70), (ux, uy)], fill=A(RED, 1), width=4)
        d.ellipse([ux - 13, uy - 13, ux + 13, uy + 13], fill=A(RED, 1), outline=A(WHITE, 1), width=4)
        if GL: GL.ellipse([ux - 20, uy - 20, ux + 20, uy + 20], fill=A(RED, 0.8))
        tag(d, ux - 60, uy - 130, 'YOU?', RED, 34, 1)
    if tp > 0:  # 10x lands with weight
        s = lerp(1.35, 1.0, expo((t - C['ten'] - 0.1) / 0.25)); fn = f(BEB, int(150 * s))
        txt(d, 980, 820, '10×', fn, RED, clamp((t - C['ten'] - 0.05) / 0.12), anchor='ra')
        q = appear(t, C['worse2'], 0.15)
        txt(d, 980, 970, 'WORSE OUTCOME', f(MONO, 26), CREAM, q, anchor='ra')
    # anecdote vs data tokens under the axis
    for i, (lab, cue) in enumerate([('FOUNDATIONAL DATA', 'foundational'), ('ANECDOTES', 'anecdotal')]):
        q = appear(t, C[cue] + 0.1, 0.15)
        if q > 0:
            x = 90 + i * 390; y = 1250
            d.rounded_rectangle([x, y, x + (360 if i == 0 else 230), y + 48], radius=8, fill=A((40, 12, 18) if i else (20, 26, 36), q), outline=A(DIM, q), width=2)
            txt(d, x + 16, y + 10, lab, f(MONO, 22), CREAM, q)
    q = appear(t, C['you1'], 0.15)
    if q > 0:
        x = 90 + 2 * 310 + 30; d.rounded_rectangle([x, 1250, x + 270, 1298], radius=8, fill=A((60, 6, 10), q), outline=A(RED, q), width=2)
        txt(d, x + 16, 1260, 'YOUR BLOODS: —', f(MONO, 22), (255, 140, 130), q)

# ---- S6: same input, different output (split panel) ----
def g_twins(d, t, top):
    a = 1
    # header
    kicker(d, 60, top + 34, 'SAME INPUT', VGOLD, 1, clamp((t - C['two']) / 0.5))
    colx = [600, 860]
    for j, nm in enumerate(['GUY A', 'GUY B']):
        q = appear(t, C['two'] + 0.15 + j * 0.12, 0.2)
        cx = colx[j]
        # line-schematic head + shoulders
        d.ellipse([cx - 22, top + 18, cx + 22, top + 62], outline=A(WHITE, q), width=3)
        d.arc([cx - 46, top + 62, cx + 46, top + 128], 180, 360, fill=A(WHITE, q), width=3)
        txt(d, cx, top + 102, nm, f(BAR, 30), CREAM, q, anchor='mm')
    rows = [('AGE', 'age'), ('WEIGHT', 'weight'), ('TRAINING', 'training'), ('INPUT', 'input')]
    for i, (lab, cue) in enumerate(rows):
        q = appear(t, C[cue] - 0.02, 0.12)
        if q <= 0: continue
        y = top + 128 + i * 46
        d.line([(60, y + 44), (1020, y + 44)], fill=A((44, 48, 60), q), width=1)
        txt(d, 60 + lerp(-20, 0, q), y + 4, lab, f(BAR, 34), CREAM, q)
        for j in range(2):
            check(d, colx[j] - 18, y + 22, GREEN, 0.9, q, 5)
        txt(d, 730, y + 22, '=', f(BEB, 44), DIM, q, anchor='mm')
    # outcome chart
    cy0, cy1, cx0, cx1 = top + 380, top + 510, 60, 1020
    cp = clamp((t - C['output'] + 0.1) / 0.4)
    if cp <= 0: return
    d.line([(cx0, cy1), (lerp(cx0, cx1, cp), cy1)], fill=A((90, 94, 110), 1), width=2)
    txt(d, cx0, cy0 - 34, 'OUTCOME OVER THE CYCLE', f(MONO, 22), DIM, cp)
    mid = lerp(cx0, cx1, 0.32); base_y = cy0 + 50
    pa = clamp((t - C['walks']) / 0.9); pb = clamp((t - C['crashes'] + 0.15) / 0.5)
    shared = [(lerp(cx0, mid, u / 20), base_y + 3 * math.sin(u)) for u in range(int(20 * clamp(cp * 1.4)) + 1)]
    if len(shared) > 1: d.line(shared, fill=A(CREAM, 1), width=5)
    if pa > 0:
        A_ = [(lerp(mid, cx1 - 120, u / 30 * pa), base_y - 6 * (u / 30 * pa) + 3 * math.sin(u)) for u in range(31)]
        d.line(A_, fill=A(GREEN, 1), width=5)
        if GL: GL.line(A_, fill=A(GREEN, 0.7), width=10)
        if pa > 0.5: tag(d, cx1 - 110, A_[-1][1] - 26, 'FINE', GREEN, 26, clamp((pa - 0.5) * 3))
    if pb > 0:
        B_ = []
        for u in range(31):
            v = u / 30 * pb
            yy = base_y + (0 if v < 0.25 else (cy1 - 14 - base_y) * ease_io((v - 0.25) / 0.75))
            B_.append((lerp(mid, cx1 - 120, v), yy))
        d.line(B_, fill=A(RED, 1), width=6)
        if GL: GL.line(B_, fill=A(RED, 0.9), width=12)
        if pb > 0.7:
            q = clamp((pb - 0.7) * 4); tag(d, cx1 - 110, B_[-1][1] - 62, 'CRASHED', RED, 26, q)

# ---- S7: why — radar + the variable selector (right sidebar) ----
AXES = [('ENZYME', 'enzyme'), ('RECEPTOR', 'receptor'), ('LIPIDS', 'lipid'), ('LIVER', 'liver2'), ('CARDIO', 'cardio'), ('ANDROGEN', 'androgen')]
VA = [0.78, 0.62, 0.70, 0.82, 0.74, 0.58]
VB = [0.36, 0.92, 0.30, 0.38, 0.42, 0.95]
def g_sidebar(im, t, p, t0, t1):
    sx = lerp(W + 10, 612, ease_io(p))
    frosted(im, (sx, 0, W, H), 0.90, 16)
    d = ImageDraw.Draw(im, 'RGBA')
    d.rectangle([sx, 0, sx + 5, H], fill=A(VGOLD, 1))
    if GL: GL.rectangle([sx - 2, 0, sx + 7, H], fill=A(VGOLD, 0.7))
    x0 = sx + 32
    q0 = clamp((t - t0 - 0.2) / 0.5)
    kicker(d, x0, 420, 'WHY', VGOLD, 1, q0)
    txt(d, x0, 466, 'SAME INPUT', f(BEB, 62), CREAM, appear(t, t0 + 0.3, 0.2))
    txt(d, x0, 526, 'DIFFERENT BODIES', f(BEB, 62), VGOLD, appear(t, t0 + 0.4, 0.2))
    cx, cy, R = sx + 236, 790, 108
    # web
    for ring in (0.33, 0.66, 1.0):
        poly = [(cx + R * ring * math.cos(-math.pi / 2 + k * math.pi / 3), cy + R * ring * math.sin(-math.pi / 2 + k * math.pi / 3)) for k in range(6)]
        d.polygon(poly, outline=A((60, 64, 78), q0))
    pa, pb = [], []
    for k, (lab, cue) in enumerate(AXES):
        ang = -math.pi / 2 + k * math.pi / 3
        on = appear(t, C[cue] - 0.03, 0.18)
        col = VGOLD if on > 0 else (60, 64, 78)
        ex, ey = cx + R * math.cos(ang), cy + R * math.sin(ang)
        d.line([(cx, cy), (ex, ey)], fill=A(col if on else (60, 64, 78), max(q0, on)), width=2 if not on else 3)
        lx, ly = cx + (R + 26) * math.cos(ang), cy + (R + 26) * math.sin(ang)
        anc = 'mm' if abs(math.cos(ang)) < 0.2 else ('lm' if math.cos(ang) > 0 else 'rm')
        txt(d, lx, ly, lab, f(BAR, 23), CREAM if on else DIM, max(q0 * 0.6, on), anchor=anc)
        pa.append((cx + R * VA[k] * on * math.cos(ang), cy + R * VA[k] * on * math.sin(ang)))
        pb.append((cx + R * VB[k] * on * math.cos(ang), cy + R * VB[k] * on * math.sin(ang)))
    if any(appear(t, C[c] - 0.03, 0.18) > 0 for _, c in AXES):
        d.polygon(pa, fill=A(VGOLD, 0.18), outline=A(VGOLD, 1)); d.line(pa + [pa[0]], fill=A(VGOLD, 1), width=3)
        d.polygon(pb, fill=A(RED, 0.18)); d.line(pb + [pb[0]], fill=A(RED, 1), width=3)
        if GL: GL.line(pa + [pa[0]], fill=A(VGOLD, 0.7), width=8); GL.line(pb + [pb[0]], fill=A(RED, 0.8), width=8)
        lq = appear(t, C['enzyme'], 0.2)
        d.line([(x0, 958), (x0 + 30, 958)], fill=A(VGOLD, lq), width=5); txt(d, x0 + 40, 946, 'GUY A', f(MONO, 22), CREAM, lq)
        d.line([(x0 + 170, 958), (x0 + 200, 958)], fill=A(RED, lq), width=5); txt(d, x0 + 210, 946, 'GUY B', f(MONO, 22), CREAM, lq)
    # selector: the variable that matters
    sq = appear(t, C['variable'] - 0.1, 0.2)
    if sq > 0:
        txt(d, x0, 1010, 'THE VARIABLE', f(MONO, 24), VGOLD, sq)
        for i, (lab, cue) in enumerate([('THE COMPOUND', 'compound'), ('THE PERSON', 'person')]):
            y = 1052 + i * 92; bx0, bx1 = x0, W - 34
            if bx1 - bx0 < 120: continue
            sel = appear(t, C[cue] + 0.05, 0.14)
            if i == 0:
                d.rounded_rectangle([bx0, y, bx1, y + 74], radius=12, fill=A((30, 10, 14), sq * (0.4 + 0.6 * sel)), outline=A(RED if sel else (80, 84, 100), sq), width=3)
                txt(d, bx0 + 22, y + 14, lab, f(BEB, 52), DIM if sel else CREAM, sq)
                if sel: d.line([(bx0 + 18, y + 40), (lerp(bx0 + 18, bx0 + 270, sel), y + 40)], fill=A(RED, sq), width=5); cross(d, bx1 - 40, y + 37, RED, 1, sel)
            else:
                if sel > 0:
                    sp = expo((t - C[cue] - 0.05) / 0.16)
                    lit_bar(d, bx0, y, lerp(bx0, bx1, sp), y + 74, VGOLD, sq)
                    if GL: GL.rectangle([bx0 - 4, y - 4, bx1 + 4, y + 78], outline=A(VGOLD, sp), width=10)
                d.rounded_rectangle([bx0, y, bx1, y + 74], radius=12, outline=A(VGOLD if sel else (80, 84, 100), sq), width=3)
                txt(d, bx0 + 22, y + 14, lab, f(BEB, 52), INK if sel > 0.5 else CREAM, sq)
                if sel > 0.5: check(d, bx1 - 58, y + 37, INK, 1, sel, 7)

# ---- S8 + S9: 500+ panels dot grid -> donut (top card) ----
def s_panels(im, t):
    t0, t1 = C['and_'] - 0.05, C['im'] - 0.05
    a = win(t, t0, t1, 0.25, 0.22)
    if a <= 0: return
    x0, y0, x1, y1 = 34, 380, 1046, 640
    yo = lerp(-40, 0, expo((t - t0) / 0.3))
    y0 += yo; y1 += yo
    frosted(im, (x0, y0, x1, y1), 0.86, 14, 22, a=a)
    d = ImageDraw.Draw(im, 'RGBA')
    d.rounded_rectangle([x0, y0, x1, y1], radius=22, outline=A(VGOLD, a * 0.55), width=2)
    brackets(d, x0, y0, x1, y1, A(VGOLD, a), 30, 5)
    if GL: brackets(GL, x0, y0, x1, y1, A(VGOLD, a), 30, 10)
    # phase 1: count + grid
    gm = clamp((t - C['pattern']) / 0.9)          # morph grid -> ring
    cnt = int(500 * ease_io((t - C['five'] + 0.1) / 0.8))
    if gm < 1:
        ba = a * (1 - gm)
        txt(d, x0 + 30, y0 + 22, 'ENHANCED PANELS REVIEWED', f(MONO, 24), VGOLD, ba)
        s = lerp(1.25, 1, expo((t - C['five'] - 0.6) / 0.25)) if t > C['five'] + 0.6 else 1
        txt(d, x0 + 26, y0 + 54, f'{cnt}' + ('+' if cnt >= 500 else ''), f(BEB, int(150 * s)), VGOLD, ba)
        txt(d, x0 + 30, y1 - 44, 'LAST COUPLE OF YEARS', f(MONO, 22), DIM, ba * appear(t, C['panels'] + 0.4, 0.2))
    # dots: 50 x 10
    gx0, gy0, sp = x0 + 390, y0 + 40, 12.2
    rcx, rcy, rr = x0 + 170, (y0 + y1) / 2, 92
    shown = cnt
    for k in range(500):
        if k >= shown: break
        c, r = k % 50, k // 50
        px, py = gx0 + c * sp, gy0 + r * sp * 1.6
        ang = -math.pi / 2 + k / 500 * 2 * math.pi
        qx, qy = rcx + rr * math.cos(ang), rcy + rr * math.sin(ang)
        e = ease_io(clamp(gm * 1.3 - (k % 37) / 37 * 0.3))
        x, y = lerp(px, qx, e), lerp(py, qy, e)
        col = VGOLD
        d.ellipse([x - 3.6, y - 3.6, x + 3.6, y + 3.6], fill=A(col, a * (1 - clamp((gm - 0.85) / 0.15))))
    # phase 2: compound bad / good chips (not the pattern)
    if t >= C['compound2'] - 0.1:
        for i, (lab, verdict, cue, col) in enumerate([('COMPOUND A', 'BAD?', 'bad', RED), ('COMPOUND B', 'GOOD?', 'good', GREEN)]):
            q = appear(t, C[cue] - 0.3, 0.14) * a * (1 - clamp((t - C['patterns']) / 0.25))
            if q <= 0: continue
            y = y0 + 40 + i * 90
            d.rounded_rectangle([x0 + 400, y, x0 + 760, y + 70], radius=10, fill=A((20, 24, 32), q), outline=A((80, 84, 100), q), width=2)
            txt(d, x0 + 420, y + 16, lab, f(BAR, 36), CREAM, q); txt(d, x0 + 740, y + 14, verdict, f(BEB, 46), col, q, anchor='ra')
        if t > C['patterns'] - 0.1:
            q = appear(t, C['patterns'] - 0.1, 0.12) * a * (1 - clamp((t - C['patterns'] - 0.3) / 0.2))
            if q > 0: tag(d, x0 + 400, y0 + 210, 'NOT THE PATTERN', RED, 24, q)
    # phase 3: donut — of the guys who got hurt, how many pulled bloods first
    if gm >= 0.85:
        ra = clamp((gm - 0.85) / 0.15) * a
        box = [rcx - rr, rcy - rr, rcx + rr, rcy + rr]
        d.ellipse(box, outline=A((60, 64, 78), ra), width=26)
        fp = ease_io((t - C['flying']) / (C['time'] - C['flying'] + 0.2))
        if fp > 0:
            d.arc(box, -90, -90 + 360 * fp, fill=A(RED, ra), width=26)
            if GL: GL.arc(box, -90, -90 + 360 * fp, fill=A(RED, ra), width=34)
        pct = int(round(100 * fp))
        txt(d, rcx, rcy - 6, f'{pct}%', f(BEB, 70), RED if fp > 0 else DIM, ra, anchor='mm')
        txt(d, rcx, rcy + 40, 'BLIND', f(MONO, 20), CREAM, ra * appear(t, C['flying'], 0.2), anchor='mm')
        lx = x0 + 330
        q = appear(t, C['hurt'] - 0.15, 0.15) * a
        txt(d, lx, y0 + 26, 'THE GUYS WHO GOT HURT', f(MONO, 24), VGOLD, q)
        q2 = appear(t, C['flying'], 0.14) * a
        if q2 > 0: tag(d, lx, y0 + 64, 'FLYING BLIND', RED, 34, q2)
        q3 = appear(t, C['time'], 0.15) * a
        txt(d, lx, y0 + 132, 'BASELINE PULLED FIRST:', f(MONO, 22), CREAM, q3); txt(d, lx + 330, y0 + 128, '0', f(BEB, 40), RED, q3)
        # labs that went bad afterwards
        for i, (lab, cue_off) in enumerate([('HCT', 0.0), ('LIPIDS', 0.25), ('LIVER', 0.5)]):
            q4 = appear(t, C['something2'] + 0.5 + cue_off, 0.12) * a
            if q4 <= 0: continue
            x = lx + i * 225; y = y0 + 186
            d.rounded_rectangle([x, y, x + 205, y + 50], radius=8, fill=A((60, 6, 10), q4), outline=A(RED, q4), width=2)
            txt(d, x + 14, y + 10, lab, f(BAR, 32), CREAM, q4)
            # up arrow
            ax = x + 178; d.polygon([(ax, y + 10), (ax - 12, y + 30), (ax + 12, y + 30)], fill=A(RED, q4)); d.line([(ax, y + 26), (ax, y + 42)], fill=A(RED, q4), width=6)

# ---- S10: order of operations (stepper strip on the chest) ----
def s_stepper(im, t):
    t0, t1 = C['run'] - 1.5, C['blood3'] - 0.32
    a = win(t, t0, t1, 0.25, 0.2)
    if a <= 0: return
    x0, y0, x1, y1 = 34, 1150, 1046, 1316
    sh = lerp(80, 0, expo((t - t0) / 0.35))
    y0 += sh; y1 += sh
    frosted(im, (x0, y0, x1, y1), 0.88, 14, 20, a=a)
    d = ImageDraw.Draw(im, 'RGBA')
    d.rounded_rectangle([x0, y0, x1, y1], radius=20, outline=A((70, 70, 80), a), width=2)
    txt(d, x0 + 24, y0 + 14, 'ORDER OF OPERATIONS', f(MONO, 22), VGOLD, a)
    nodes = [('BLOOD DRAW', 'drawn'), ('READ BASELINE', 'first'), ('PROTOCOL', 'run')]
    xs = [x0 + 150, 540, x1 - 150]; ny = y0 + 92
    # track
    d.line([(xs[0], ny), (xs[2], ny)], fill=A((70, 74, 90), a), width=4)
    prog = ease_io((t - C['direction']) / (C['drawn'] - C['direction'] + 0.3))
    if prog > 0:
        d.line([(xs[0], ny), (lerp(xs[0], xs[1], prog), ny)], fill=A(VGOLD, a), width=5)
        if GL: GL.line([(xs[0], ny), (lerp(xs[0], xs[1], prog), ny)], fill=A(VGOLD, a), width=10)
    for i, (lab, cue) in enumerate(nodes):
        q = appear(t, t0 + 0.15 + i * 0.12, 0.2) * a
        cx = xs[i]
        if i == 0:
            on = appear(t, C['drawn'] + 0.1, 0.12)
            d.ellipse([cx - 30, ny - 30, cx + 30, ny + 30], fill=A(VGOLD if on else (24, 26, 34), q), outline=A(VGOLD, q), width=4)
            if on: check(d, cx - 15, ny + 1, INK, 0.95, q * on, 6)
            else: txt(d, cx, ny, '01', f(BEB, 36), VGOLD, q, anchor='mm')
            if on and GL: GL.ellipse([cx - 34, ny - 34, cx + 34, ny + 34], outline=A(VGOLD, q), width=10)
            if on: tag(d, cx + 42, ny - 58, 'FIRST', VGOLD, 22, q * on)
        elif i == 1:
            on = appear(t, C['first'] + 0.4, 0.15)
            d.ellipse([cx - 30, ny - 30, cx + 30, ny + 30], fill=A((24, 26, 34), q), outline=A(VGOLD if on else (90, 94, 110), q), width=4)
            txt(d, cx, ny, '02', f(BEB, 36), VGOLD if on else DIM, q, anchor='mm')
        else:
            pulse = 1 if not (C['anything'] <= t <= C['anything'] + 0.8) else (0.5 + 0.5 * math.sin((t - C['anything']) * 20))
            d.ellipse([cx - 30, ny - 30, cx + 30, ny + 30], fill=A((40, 10, 14), q), outline=A(RED, q * pulse), width=4)
            padlock(d, cx, ny - 4, RED, q, 0.85)
            if GL and C['anything'] <= t: GL.ellipse([cx - 34, ny - 34, cx + 34, ny + 34], outline=A(RED, q * pulse), width=10)
        txt(d, cx, ny + 50, lab, f(BAR, 30), CREAM if i != 2 else (255, 150, 140), q, anchor='mm')

# ---- S11: roadmap (full scene) ----
RPTS = [(150, 1240), (260, 1120), (190, 990), (330, 880), (470, 960), (560, 1090), (700, 1150), (850, 1060), (900, 900), (830, 760)]
WAY = [('TEST', 1), ('E2', 2), ('HCT', 4), ('LIPIDS', 5), ('LIVER', 7), ('KIDNEY', 8)]
def _bez(pts, n=24):
    out = []
    for i in range(len(pts) - 1):
        p0 = pts[max(0, i - 1)]; p1 = pts[i]; p2 = pts[i + 1]; p3 = pts[min(len(pts) - 1, i + 2)]
        for k in range(n):
            u = k / n; u2, u3 = u * u, u * u * u
            out.append((0.5 * ((2 * p1[0]) + (-p0[0] + p2[0]) * u + (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * u2 + (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * u3),
                        0.5 * ((2 * p1[1]) + (-p0[1] + p2[1]) * u + (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * u2 + (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * u3)))
    out.append(pts[-1]); return out
RCURVE = _bez(RPTS)
def g_road(d, t, lay):
    t0 = C['blood3'] - 0.3
    kicker(d, 70, 300, 'THE ROADMAP', VGOLD, 1, clamp((t - t0) / 0.6))
    txt(d, 70, 346, 'YOUR BLOODS', f(BEB, 96), CREAM, appear(t, t0 + 0.3, 0.2))
    txt(d, 70, 436, 'SET THE ROUTE', f(BEB, 96), VGOLD, appear(t, t0 + 0.45, 0.2))
    # topo lines
    for k in range(7):
        pts = [(x, 720 + k * 90 + 30 * math.sin(x / 140 + k)) for x in range(40, 1060, 20)]
        d.line(pts, fill=A((30, 36, 48), 1), width=2)
    # opinion detours (grey dashed dead ends)
    oq = appear(t, C['opinion'] - 0.5, 0.3)
    if oq > 0:
        for (sx, sy, ex, ey, lab) in [(330, 880, 120, 760, 'OPINION'), (560, 1090, 420, 1250, 'BRO SCIENCE'), (850, 1060, 1010, 1210, 'GUESS')]:
            L = math.hypot(ex - sx, ey - sy); n = int(L / 18)
            for k in range(n):
                if k % 2: continue
                u0, u1 = k / n * oq, (k + 1) / n * oq
                d.line([(lerp(sx, ex, u0), lerp(sy, ey, u0)), (lerp(sx, ex, u1), lerp(sy, ey, u1))], fill=A((120, 124, 136), 1), width=4)
            if oq > 0.8:
                q = clamp((oq - 0.8) * 5); txt(d, ex, ey + 30 if ey > sy else ey - 30, lab, f(MONO, 22), (150, 154, 166), q, anchor='mm')
                xq = appear(t, C['lived'] - 0.1, 0.12)
                if xq: cross(d, ex, ey, RED, 1.1, xq, 7)
    # route draws on
    rp = ease_io((t - C['road'] + 0.4) / 1.6)
    n = int(len(RCURVE) * rp)
    if n > 1:
        d.line(RCURVE[:n], fill=A(VGOLD, 1), width=9, joint='curve')
        if GL: GL.line(RCURVE[:n], fill=A(VGOLD, 0.9), width=18)
    sx, sy = RPTS[0]; d.ellipse([sx - 16, sy - 16, sx + 16, sy + 16], fill=A(CREAM, 1)); txt(d, sx, sy + 40, 'BASELINE', f(MONO, 22), CREAM, 1, anchor='mm')
    for lab, idx in WAY:
        # when the drawn route reaches the waypoint
        frac = (idx * 24) / len(RCURVE)
        q = clamp((rp - frac) / 0.06)
        if q <= 0: continue
        x, y = RPTS[idx]
        d.ellipse([x - 13, y - 13, x + 13, y + 13], fill=A(INK, 1), outline=A(VGOLD, q), width=5)
        fn = f(BAR, 30); tw = d.textlength(lab, font=fn)
        lx = x + 24 if x < 800 else x - 24 - tw - 16
        d.rounded_rectangle([lx, y - 22, lx + tw + 16, y + 20], radius=6, fill=A((20, 24, 32), q), outline=A(VGOLD, q * 0.7), width=2)
        txt(d, lx + 8, y - 18, lab, fn, CREAM, q)
    if rp >= 1:
        ex, ey = RPTS[-1]; q = appear(t, C['road'] + 1.25, 0.2)
        d.polygon([(ex, ey - 46), (ex - 18, ey - 14), (ex + 18, ey - 14)], fill=A(VGOLD, q))
        txt(d, ex, ey - 70, 'YOUR GOAL', f(MONO, 22), VGOLD, q, anchor='mm')

# ---- S12: CTA panel (split) ----
GUIDE = ['TESTOSTERONE', 'ESTRADIOL (E2)', 'HEMATOCRIT', 'LIPIDS', 'LIVER', 'KIDNEY']
def g_cta(d, t, top, im):
    t0 = C['that_']
    # guide document (paper) on the left
    gp = expo((t - C['guide'] + 0.3) / 0.35)
    if gp > 0:
        pw, ph = 470, 440
        doc = Image.new('RGBA', (pw, ph), (238, 235, 228, 255)); dd = ImageDraw.Draw(doc)
        dd.rectangle([0, 0, pw, 70], fill=(14, 17, 23)); dd.rectangle([0, 0, 8, 70], fill=GOLD)
        dd.text((24, 10), 'BASELINE', font=f(BEB, 40), fill=GOLD); dd.text((24, 44), 'PANEL GUIDE · PULL BEFORE YOU START', font=f(MONO, 16), fill=(200, 200, 205))
        for i, m in enumerate(GUIDE):
            y = 92 + i * 54
            dd.rectangle([22, y + 4, 52, y + 34], outline=(60, 62, 70), width=3)
            dd.text((70, y + 2), m, font=f(BAR, 32), fill=(24, 26, 34))
            dd.line([(20, y + 46), (pw - 20, y + 46)], fill=(205, 202, 196), width=1)
        doc = doc.rotate(lerp(-8, -2, gp), Image.BICUBIC, expand=True)
        sh = Image.new('RGBA', doc.size, (0, 0, 0, 0)); sh.putalpha(doc.split()[3].point(lambda v: int(v * 0.5))); sh = sh.filter(ImageFilter.GaussianBlur(12))
        ox, oy = int(lerp(-300, 50, gp)), int(top + 40)
        im.alpha_composite(sh, (ox + 10, oy + 16)); im.alpha_composite(doc, (ox, oy))
        dg = ImageDraw.Draw(im, 'RGBA')
        for i, m in enumerate(GUIDE):  # ticks land as he says "which markers"
            q = appear(t, C['markers'] + 0.12 * i, 0.1)
            if q <= 0: continue
            # approximate the rotated row position
            ang = math.radians(2)
            rx, ry = 37, 92 + i * 54 + 19
            cx_, cy_ = pw / 2, ph / 2
            px = ox + doc.width / 2 + (rx - cx_) * math.cos(ang) + (ry - cy_) * math.sin(ang)
            py = oy + doc.height / 2 - (rx - cx_) * math.sin(ang) + (ry - cy_) * math.cos(ang)
            check(dg, px - 10, py, (20, 150, 70), 0.9, q, 6)
    # right side: what you get
    rx0 = 580
    q = appear(t, C['guide'], 0.2)
    kicker(d, rx0, top + 52, 'FREE GUIDE', VGOLD, 1, clamp((t - C['guide']) / 0.5))
    items = [('WHICH MARKERS', 'markers'), ('BEFORE YOU START', 'markers'), ('WHAT EACH ONE TELLS YOU', 'each')]
    for i, (lab, cue) in enumerate(items):
        qq = appear(t, C[cue] + 0.5 * i - (0.3 if i == 0 else 0), 0.15)
        y = top + 108 + i * 56
        d.text((rx0, y + 4), '◆', font=f(DMB, 24), fill=A(VGOLD, qq)); txt(d, rx0 + 34, y, lab, f(BAR, 33), CREAM, qq)
    # COMMENT "BASELINE" pill slams
    cp = appear(t, C['comment'], 0.16)
    if cp > 0:
        s = lerp(1.3, 1.0, cp); bx0, by0 = rx0, top + 290
        txt(d, bx0, by0, 'COMMENT THE WORD', f(MONO, 26), CREAM, cp)
        fn = f(BEB, int(104 * s)); lab = '"BASELINE"'; tw = d.textlength(lab, font=fn)
        lit_bar(d, bx0, by0 + 42, bx0 + tw + 44, by0 + 42 + int(112 * s), VGOLD, 1)
        if GL: GL.rectangle([bx0 - 6, by0 + 36, bx0 + tw + 50, by0 + 48 + 112 * s], outline=A(VGOLD, 1), width=14)
        txt(d, bx0 + 22, by0 + 50, lab, fn, INK, 1)
        q2 = appear(t, C['comment'] + 0.6, 0.2)
        txt(d, bx0, by0 + 176, "I'LL SEND IT TO YOU", f(MONO, 24), DIM, q2)

def split_scene(im, t, p, t0, t1, which):
    top = min(H - 1, lerp(H + 20, 1004, ease_io(p)))
    frosted(im, (0, top, W, H), 0.90, 18)
    d = ImageDraw.Draw(im, 'RGBA')
    lit_bar(d, 0, top - 3, W, top + 3, VGOLD, 1)
    if GL: GL.rectangle([0, top - 4, W, top + 4], fill=A(VGOLD, 0.8))
    d.rectangle([0, top, 5, H], fill=A(GOLD, 1))
    txt(d, 1046, top + 22, '@COACH.AGZ', f(MONO, 22), DIM, p, anchor='ra')
    if p < 0.3: return
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); ld = ImageDraw.Draw(lay, 'RGBA')
    if which == 'twins': g_twins(ld, t, top)
    else: g_cta(ld, t, top, lay)
    al = clamp((p - 0.3) / 0.7)
    if al < 1: lay.putalpha(lay.split()[3].point(lambda v: int(v * al)))
    im.alpha_composite(lay)

# =====================================================================
# CAPTIONS (house style from full test 01: Bebas, red lit block on the spoken word)
# =====================================================================
FIX = {'patterns': "PATTERN'S", 'road': 'ROAD', "isn't": "ISN'T"}
def build_groups():
    G = []; cur = []
    for i, x in enumerate(WORDS):
        if cur:
            prev = WORDS[cur[-1]]
            if len(cur) >= 3 or x['s'] - prev['e'] > 0.28 or prev['w'][-1] in '.,?!' or any(prev['e'] <= c <= x['s'] + 0.01 for c in CUTS):
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
def captions(im, t):
    g = group_at(t)
    if not g: return
    cy, ccx, maxw = cap_place(t)
    d = ImageDraw.Draw(im, 'RGBA')
    ws = [FIX.get(WORDS[i]['w'].lower().strip('.,?!'), WORDS[i]['w']).upper().strip('.,?!') for i in g]
    size = 120
    while True:
        fn = f(BEB, size); sp = d.textlength(' ', font=fn) + 14; wd = [d.textlength(w, font=fn) for w in ws]; tot = sum(wd) + sp * (len(ws) - 1)
        if tot <= maxw: break
        size -= 4
    xs = []; x = (W - tot) / 2 + (ccx - 540)
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
    for k, (w_, x_) in enumerate(zip(ws, xs)): cd.text((x_, 40), w_, font=fn, fill=CREAM, stroke_width=0 if k == act else 3, stroke_fill=(0, 0, 0))
    if abs(s - 1) > 0.002:
        cw, ch = int(W * s), int(300 * s); cap = cap.resize((cw, ch), Image.BICUBIC)
        ox = int(ccx - ccx * s); oy = int(cy - 40 - (ch - 300) / 2)
    else: ox, oy = 0, int(cy - 40)
    im.alpha_composite(cap, (ox, oy))

# =====================================================================
# FRAME
# =====================================================================
def frame(src, t):
    global GL
    glow = Image.new('RGBA', (W, H), (0, 0, 0, 0)); GL = ImageDraw.Draw(glow, 'RGBA')
    m, p, pc, t0, t1 = layout_at(t)
    if m == 'full' and p > 0:
        im = full_scene(None, src, t, pc, p, t0, t1, g_bell if t < 60 else g_road)
    else:
        im = footage(src, t)
    # light top/bottom scrim for text legibility (no grade on the footage itself)
    scr = Image.new('L', (1, H), 0); sp_ = scr.load()
    for y in range(H):
        v = 0
        if y < 420: v = (1 - y / 420) * 105
        if y > 1180: v = max(v, min(1, (y - 1180) / 300) * 95)
        sp_[0, y] = int(v)
    im.alpha_composite(Image.merge('RGBA', [Image.new('L', (W, H), c) for c in NAVY] + [scr.resize((W, H))]))
    if m != 'full' or p == 0:
        s_confidence(im, t); s_hud(im, t); s_rx(im, t); s_panels(im, t); s_stepper(im, t)
        if m == 'side' and p > 0: g_sidebar(im, t, p, t0, t1)
        if m == 'split' and p > 0: split_scene(im, t, p, t0, t1, 'twins' if t < 60 else 'cta')
    else:
        if p < 1:  # leaving/entering: keep footage-side graphics consistent
            pass
    hook(im, t); topic_band(im, t)
    # gold edge rule + handle (static brand anchor)
    d = ImageDraw.Draw(im, 'RGBA'); d.rectangle([0, 0, 5, H], fill=A(GOLD, 0.9))
    captions(im, t)
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
    n0, n1, out = int(sys.argv[3]), int(sys.argv[4]), sys.argv[5]
    dec = subprocess.Popen(['ffmpeg', '-v', 'error', '-i', WK + '/assembled.mp4', '-vf', f'select=between(n\\,{n0}\\,{n1 - 1})', '-vsync', '0', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], stdout=subprocess.PIPE)
    if out.endswith('.mp4'):
        enc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-crf', '12', '-preset', 'fast', '-pix_fmt', 'yuv420p', out], stdin=subprocess.PIPE)
    for n in range(n0, n1):
        b = dec.stdout.read(W * H * 3)
        if len(b) < W * H * 3: break
        fr = frame(Image.frombuffer('RGB', (W, H), b), n / FPS)
        if out.endswith('.mp4'): enc.stdin.write(fr.tobytes())
        else: fr.save(f'{out}/f{n:05d}.jpg', quality=88)
    if out.endswith('.mp4'): enc.stdin.close(); enc.wait()
    dec.kill(); print('done', n0, n1)
