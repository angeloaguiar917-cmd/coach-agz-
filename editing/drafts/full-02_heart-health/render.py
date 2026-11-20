# Full 02: "2 compounds every STEROID cycle needs" (Ezetimibe + Telmisartan), 1080x1920 30 fps
# usage: python3 render.py <workdir> stills t1 t2 ...   |   python3 render.py <workdir> <n0> <n1> <out.mp4>
# workdir holds: assembled.mov, words.json, face.json, logo.jpg, fonts/
import json, subprocess, sys, math, re
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops
S = sys.argv[1].rstrip('/') + '/'
F = S + 'fonts/'
W, H = 1080, 1920; FPS = 30
WORDS = json.load(open(S + 'words.json'))
FACE = json.load(open(S + 'face.json'))
CUTS = json.load(open(S + 'cuts.json'))          # jump points in the cut timeline (s)
DUR = 143.633

GOLD = (201, 169, 110); CREAM = (244, 241, 234); NAVY = (14, 17, 23)
RED = (255, 34, 28); VGOLD = (255, 194, 26); CYAN = (0, 229, 255); GREEN = (30, 255, 110)
DEEP = (2, 3, 8); INK = (6, 8, 14); WHITE = (255, 255, 255); MUTED = (124, 124, 130)
AMBER = (240, 160, 48); CRIMSON = (200, 16, 46)
MONO = 'JBMono-500.ttf'; BEB = 'BebasNeue.ttf'; DMB = 'DMSans-700.ttf'; DMR = 'DMSans-400.ttf'
BC6 = 'BarlowCond-600.ttf'; BC8 = 'BarlowCond-800.ttf'
_fc = {}
def f(n, s):
    k = (n, int(s))
    if k not in _fc: _fc[k] = ImageFont.truetype(F + n, int(s))
    return _fc[k]
def clamp(x, a=0, b=1): return max(a, min(b, x))
def expo(x): x = clamp(x); return 1 if x >= 1 else 1 - 2 ** (-10 * x)
def ease_io(x): x = clamp(x); return 4 * x ** 3 if x < .5 else 1 - (-2 * x + 2) ** 3 / 2
def back(x, s=1.2): x = clamp(x); return 1 + (s + 1) * (x - 1) ** 3 + s * (x - 1) ** 2
def lerp(a, b, t): return a + (b - a) * t
def A(c, a): return tuple(c[:3]) + (int(clamp(a) * 255),)
def appear(t, t0, dur=0.16): return expo((t - t0) / dur)
def life(t, t0, t1, i=0.16, o=0.14): return appear(t, t0, i) * (1 - clamp((t - t1) / o))
def txt(d, x, y, s, font, col, a=1.0, anchor=None): d.text((x, y), s, font=font, fill=A(col, a), anchor=anchor)

# ---------------- word cues ----------------
def _n(w): return re.sub(r"[^a-z0-9]", "", w.lower())
NW = [_n(w['w']) for w in WORDS]
def T(phrase, after=0.0, end=False):
    ps = [_n(p) for p in phrase.split()]
    for i in range(len(NW) - len(ps) + 1):
        if WORDS[i]['s'] >= after - 1e-6 and all(NW[i + k].startswith(ps[k]) for k in range(len(ps))):
            return WORDS[i + len(ps) - 1]['e'] if end else WORDS[i]['s']
    raise KeyError(phrase)

# ---------------- face track ----------------
_fd = {int(k): v for k, v in FACE['det'].items()}
_fk = sorted(_fd)
_fx = np.interp(np.arange(FACE['n']), _fk, [_fd[k][0] for k in _fk])
_fy = np.interp(np.arange(FACE['n']), _fk, [_fd[k][1] for k in _fk])
_fw = np.interp(np.arange(FACE['n']), _fk, [_fd[k][2] for k in _fk])
def _smooth(a, r=12):
    k = np.ones(2 * r + 1) / (2 * r + 1); p = np.pad(a, r, mode='edge'); return np.convolve(p, k, 'valid')
_fx, _fy, _fw = _smooth(_fx), _smooth(_fy), _smooth(_fw, 20)
def face_at(t):
    n = int(clamp(round(t * FPS), 0, len(_fx) - 1)); return _fx[n], _fy[n], _fw[n]

def comp(im, layer, pos=(0, 0)): im.paste(layer, (int(pos[0]), int(pos[1])), layer)
GL = None   # glow layer draw (screen-blend bloom)
# ---------------- primitives ----------------
def brackets(d, x0, y0, x1, y1, col, L=34, w=4):
    for (cx, cy, sx, sy) in [(x0, y0, 1, 1), (x1, y0, -1, 1), (x0, y1, 1, -1), (x1, y1, -1, -1)]:
        d.line([(cx, cy), (cx + sx * L, cy)], fill=col, width=w); d.line([(cx, cy), (cx, cy + sy * L)], fill=col, width=w)
def lit_bar(d, x0, y0, x1, y1, col, a=1.0):
    h = max(1, int(y1 - y0))
    for i in range(h):
        k = i / h; c = tuple(int(min(255, v * (1.18 - 0.36 * k) + (40 if k < 0.12 else 0))) for v in col)
        d.line([(x0, y0 + i), (x1, y0 + i)], fill=c + (int(255 * a),))
def tag(d, x, y, label, col=RED, size=32, a=1.0, glow=True):
    fn = f(MONO, size); tw = d.textlength(label, font=fn); h = size + 16
    lit_bar(d, x, y, x + tw + 24, y + h, col, a); d.text((x + 12, y + 5), label, font=fn, fill=A(WHITE if col not in (VGOLD, GREEN, CYAN) else INK, a))
    if GL and glow: GL.rectangle([x - 4, y - 4, x + tw + 28, y + h + 4], outline=A(col, a), width=8)
    return x + tw + 24
def tagw(d, label, size=32): return d.textlength(label, font=f(MONO, size)) + 24
def arrow(d, x0, y0, x1, y1, col, w=5, a=1.0, L=18):
    d.line([(x0, y0), (x1, y1)], fill=A(col, a), width=w)
    ang = math.atan2(y1 - y0, x1 - x0)
    d.polygon([(x1, y1), (x1 - L * math.cos(ang - 0.45), y1 - L * math.sin(ang - 0.45)), (x1 - L * math.cos(ang + 0.45), y1 - L * math.sin(ang + 0.45))], fill=A(col, a))
    if GL: GL.line([(x0, y0), (x1, y1)], fill=A(col, a * 0.7), width=w + 6)
def flow(d, x0, y0, x1, y1, t, col, n=5, speed=0.9, a=1.0, r=7):
    for k in range(n):
        p = (t * speed + k / n) % 1
        x = lerp(x0, x1, p); y = lerp(y0, y1, p); fa = a * min(1, p * 6, (1 - p) * 6)
        d.ellipse([x - r, y - r, x + r, y + r], fill=A(col, fa))
        if GL: GL.ellipse([x - r * 2, y - r * 2, x + r * 2, y + r * 2], fill=A(col, fa))
def check(d, x, y, col, s=1.0, a=1.0):
    pts = [(x, y + 16 * s), (x + 10 * s, y + 28 * s), (x + 30 * s, y + 2 * s)]
    d.line(pts, fill=A(col, a), width=int(6 * s))
    if GL: GL.line(pts, fill=A(col, a), width=int(12 * s))
def cross(d, x, y, col, s=1.0, a=1.0):
    d.line([(x, y), (x + 28 * s, y + 28 * s)], fill=A(col, a), width=int(6 * s)); d.line([(x + 28 * s, y), (x, y + 28 * s)], fill=A(col, a), width=int(6 * s))
    if GL: GL.line([(x, y), (x + 28 * s, y + 28 * s)], fill=A(col, a), width=12); GL.line([(x + 28 * s, y), (x, y + 28 * s)], fill=A(col, a), width=12)
def node(d, x0, y0, x1, y1, title, sub, col, a=1.0, dim=False, size=46):
    c = col if not dim else tuple(int(v * 0.35) for v in col)
    d.rounded_rectangle([x0, y0, x1, y1], radius=14, fill=A((10, 14, 24), 0.95 * a), outline=A(c, a), width=4)
    if GL and not dim: GL.rounded_rectangle([x0, y0, x1, y1], radius=14, outline=A(col, a * 0.8), width=8)
    fn = f(BEB, size); tw = d.textlength(title, font=fn)
    d.text(((x0 + x1) / 2 - tw / 2, y0 + 12 if sub else (y0 + y1) / 2 - size * 0.5), title, font=fn, fill=A(WHITE if not dim else (110, 110, 120), a))
    if sub:
        fs = f(MONO, 22); sw = d.textlength(sub, font=fs); d.text(((x0 + x1) / 2 - sw / 2, y1 - 36), sub, font=fs, fill=A(c, a))
def panel_box(d, x0, y0, x1, y1, a, title_l='', title_r='', col=VGOLD, t=0):
    d.rounded_rectangle([x0, y0, x1, y1], radius=18, fill=A(DEEP, 0.9 * a), outline=A(col, 0.55 * a), width=2)
    brackets(d, x0, y0, x1, y1, A(col, a), 40, 6)
    if GL: brackets(GL, x0, y0, x1, y1, A(col, a), 40, 12)
    if title_l:
        d.ellipse([x0 + 24, y0 + 26, x0 + 40, y0 + 42], fill=A(RED, a if int(t * 4) % 2 == 0 else a / 3))
        txt(d, x0 + 54, y0 + 18, title_l, f(MONO, 28), WHITE, a)
    if title_r:
        fr = f(MONO, 28); tw = d.textlength(title_r, font=fr); txt(d, x1 - 28 - tw, y0 + 18, title_r, fr, col, a)
def heart_pts(cx, cy, s, n=80):
    pts = []
    for i in range(n):
        u = 2 * math.pi * i / n
        x = 16 * math.sin(u) ** 3; y = 13 * math.cos(u) - 5 * math.cos(2 * u) - 2 * math.cos(3 * u) - math.cos(4 * u)
        pts.append((cx + x * s, cy - y * s))
    return pts
def frosted(im, box, dark=0.86, blur=10):
    x0, y0, x1, y1 = [int(v) for v in box]
    x0, y0 = max(0, x0), max(0, y0); x1, y1 = min(W, x1), min(H, y1)
    if x1 <= x0 or y1 <= y0: return
    reg = im.crop((x0, y0, x1, y1)).convert('RGB').filter(ImageFilter.GaussianBlur(blur))
    im.paste(Image.blend(reg, Image.new('RGB', reg.size, DEEP), dark), (x0, y0))

# ---------------- brand background (behind windowed footage) ----------------
def make_bg():
    y, x = np.mgrid[0:H, 0:W].astype(np.float32)
    g = np.exp(-(((x - 900) / 700) ** 2 + ((y - 260) / 700) ** 2))
    g2 = np.exp(-(((x - 150) / 600) ** 2 + ((y - 1600) / 600) ** 2))
    base = np.array(NAVY, np.float32)[None, None, :] + g[..., None] * np.array([46, 34, 14], np.float32) + g2[..., None] * np.array([30, 6, 10], np.float32)
    rng = np.random.default_rng(3); base += rng.normal(0, 3.2, (H, W, 1))
    # fine horizontal scan lines (clinical monitor texture)
    base[::4] *= 0.93
    return Image.fromarray(np.clip(base, 0, 255).astype(np.uint8)).convert('RGBA')
BG = make_bg()
LOGO = None
def logo(size):
    global LOGO
    if LOGO is None:
        lg = Image.open(S + 'logo.jpg').convert('RGB'); s = min(lg.size)
        LOGO = lg.crop(((lg.width - s) // 2, (lg.height - s) // 2, (lg.width + s) // 2, (lg.height + s) // 2))
    lg = LOGO.resize((size, size), Image.LANCZOS); m = Image.new('L', (size, size), 0)
    ImageDraw.Draw(m).ellipse([0, 0, size - 1, size - 1], fill=255); lg.putalpha(m); return lg

# =====================================================================================
# CUE TIMES (cut timeline)
# =====================================================================================
C = {}
def cues():
    c = C
    c['steroids'] = T('steroids'); c['two'] = T('two compounds'); c['cv1'] = T('cardiovascular'); c['unprot'] = T('unprotected')
    c['why_e'] = T('exactly why', end=True)
    c['mech'] = T('two separate'); c['neither'] = T('neither'); c['neither_e'] = T('neither', end=True)
    c['lipids'] = T('lipids'); c['downreg'] = T('down'); c['ldl1'] = T('ldl'); c['hdl1'] = T('hdl', after=c['ldl1'])
    c['apob1'] = T('apob'); c['plaque'] = T('plaque'); c['panel'] = T('panel'); c['already'] = T('already')
    c['already_e'] = T('problem', after=c['already'], end=True)
    c['fix1'] = T('number one fix'); c['eze1'] = T('ezetimibe'); c['statin'] = T('statins'); c['liver1'] = T('liver')
    c['burden'] = T('burden'); c['eze2'] = T('ezetimibe', after=c['burden']); c['blocks'] = T('blocks'); c['gut'] = T('gut')
    c['absorbed'] = T('absorbed'); c['delivered'] = T('delivered'); c['pulling'] = T('pulling'); c['circ_e'] = T('circulation', end=True)
    c['bw'] = T('bloodwork') if 'bloodwork' in NW else T('blood work'); c['lowldl'] = T('lower ldl'); c['lowapob'] = T('lower apob')
    c['ratio'] = T('better'); c['zero1'] = T('zero hormonal'); c['zero2'] = T('zero impact'); c['cleanest'] = T('cleanest')
    c['avail_e'] = T('available', end=True)
    c['p2'] = T('problem number two'); c['bp1'] = T('blood pressure', after=c['p2']); c['struct'] = T('structural')
    c['supra'] = T('supraphysiological') if any(w.startswith('supraphys') for w in NW) else T('super')
    c['resist'] = T('resistance'); c['bpclimb'] = T('climbs', after=c['resist']); c['overload'] = T('overload')
    c['lvh'] = T('left', after=c['overload']); c['wall'] = T('wall'); c['ef'] = T('ejection') if 'ejection' in NW else T('injection')
    c['silent'] = T('silently'); c['years_e'] = T('years', end=True)
    c['fix2'] = T('fix here'); c['fav'] = T('favorite'); c['telmi1'] = T('telmisartan')
    c['ang2'] = T('angiotensin'); c['constrict'] = T('constricts'); c['remodel'] = T('remodeling')
    c['telmi2'] = T('telmisartan', after=c['remodel']); c['at1'] = T('blocks', after=c['telmi2']); c['relax'] = T('relax'); c['pdrop'] = T('drops')
    c['wallred'] = T('reduces'); c['hey'] = T('alright'); c['gold'] = T('gold standard'); c['bb_body'] = T('bodybuilders', end=True)
    c['lowers'] = T('lowers'); c['hr'] = T('heart rate'); c['diur'] = T('diuretics'); c['electro'] = T('electrolyte')
    c['blunted'] = T('blunted'); c['beta'] = T('beta'); c['beta_e'] = T('blockers', end=True)
    c['getthis'] = T('get this'); c['clinical'] = T('clinical'); c['regression'] = T('regression'); c['prevention'] = T('prevention')
    c['reversal'] = T('reversal'); c['hyper_e'] = T('hypertrophy', after=c['reversal'], end=True)
    c['endday'] = T('end of the day'); c['twosol'] = T('two solutions'); c['eze3'] = T('ezetimibe', after=c['endday'])
    c['telmi3'] = T('telmisartan', after=c['endday']); c['both'] = T('both'); c['everytime'] = T('every time')
    c['every_e'] = T('time', after=c['everytime'], end=True)
    c['cta'] = T('if you want', after=c['both']); c['stack'] = T('stack', after=c['cta']); c['comment'] = T('comment')
    c['health'] = T('health', after=c['comment'])
cues()

# =====================================================================================
# LAYOUT: where the footage sits.  modes: full | split | pip | sbs | drawer | wipe
# =====================================================================================
MODES = [   # (t_in, t_out, mode)
    (C['lipids'] - 0.25, C['already_e'] + 0.35, 'split'),
    (C['eze2'] - 0.30, C['circ_e'] + 0.30, 'pip'),
    (C['bw'] - 0.25, C['avail_e'] + 0.25, 'sbs'),
    (C['p2'] - 0.10, C['p2'] + 1.55, 'wipe'),
    (C['overload'] - 0.25, C['years_e'] + 0.30, 'split'),
    (C['ang2'] - 0.35, C['wallred'] + 0.75, 'drawer'),
    (C['lowers'] - 0.30, C['beta_e'] + 0.40, 'pipr'),
]
def mode_at(t):
    for a, b, m in MODES:
        if a <= t < b + 0.32:
            pin = ease_io((t - a) / 0.34); pout = ease_io((t - b) / 0.30)
            return m, min(pin, 1 - pout), a, b
    return 'full', 0.0, 0, 0

def seg_of(t): return sum(1 for c in CUTS if c <= t + 1e-6)
def zoom_full(t):
    # alternating punch-in at every jump cut + purposeful punch on the spoken subject in the hook
    z = 1.0 if seg_of(t) % 2 == 0 else 1.08
    if t < CUTS[0]:
        z = lerp(1.0, 1.10, expo((t - C['steroids']) / 0.12)) if t >= C['steroids'] else 1.0
    if C['gold'] - 0.05 <= t < C['bb_body'] + 0.4: z = max(z, lerp(1.0, 1.14, expo((t - C['gold'] + 0.05) / 0.12)))
    if C['reversal'] - 0.05 <= t < C['hyper_e'] + 0.2: z = max(z, lerp(1.0, 1.15, expo((t - C['reversal'] + 0.05) / 0.12)))
    if C['comment'] <= t: z = 1.0
    return z
def src_full(t):
    z = zoom_full(t); w = W / z; h = H / z; cx, cy, _ = face_at(t)
    x0 = clamp(cx - w / 2, 0, W - w) if z > 1 else 0; y0 = clamp(cy - h * 0.42, 0, H - h) if z > 1 else 0
    return (x0, y0, x0 + w, y0 + h)
def src_face(t, wmul, aspect, yoff=0.42, minw=420):
    cx, cy, fw = face_at(t); w = clamp(fw * wmul, minw, W); h = w * aspect
    if h > H: h = H; w = h / aspect
    x0 = clamp(cx - w / 2, 0, W - w); y0 = clamp(cy - h * yoff, 0, H - h)
    return (x0, y0, x0 + w, y0 + h)
DEST = {'split': (190, 150, 890, 850), 'pip': (712, 150, 1032, 470), 'sbs': (34, 330, 534, 1290),
        'pipr': (60, 150, 420, 510), 'drawer': (0, -400, W, H - 400)}
def mode_geom(m, t):
    if m == 'split': return src_face(t, 2.15, 1.0), DEST['split'], 30
    if m == 'pip': return src_face(t, 1.65, 1.0, 0.48, 360), DEST['pip'], 160
    if m == 'pipr': return src_face(t, 1.75, 1.0, 0.48, 360), DEST['pipr'], 26
    if m == 'sbs': return src_face(t, 1.45, 1.92, 0.36), DEST['sbs'], 26
    if m == 'drawer': return (0, 0, W, H), DEST['drawer'], 0
    return src_full(t), (0, 0, W, H), 0

def compose_base(src, t):
    m, p, a, b = mode_at(t)
    sfull = src_full(t)
    if m == 'full' or m == 'wipe' or p <= 0:
        x0, y0, x1, y1 = sfull
        im = src.resize((W, H), Image.BICUBIC, box=sfull) if (x1 - x0) < W - 0.5 else src.copy()
        return im.convert('RGB'), None, m, p
    sr, dr, rad = mode_geom(m, t)
    q = p
    s = tuple(lerp(sfull[i], sr[i], q) for i in range(4)); dd = tuple(lerp([0, 0, W, H][i], dr[i], q) for i in range(4))
    r = lerp(0, rad, q)
    im = BG.copy()
    dw, dh = int(round(dd[2] - dd[0])), int(round(dd[3] - dd[1]))
    if dw > 4 and dh > 4:
        piece = src.resize((dw, dh), Image.BICUBIC, box=s).convert('RGBA')
        mk = Image.new('L', (dw, dh), 0); ImageDraw.Draw(mk).rounded_rectangle([0, 0, dw - 1, dh - 1], radius=int(min(r, dw / 2, dh / 2)), fill=255)
        # soft drop shadow
        sh = Image.new('RGBA', (W, H), (0, 0, 0, 0)); ImageDraw.Draw(sh).rounded_rectangle([dd[0] + 6, dd[1] + 16, dd[2] + 6, dd[3] + 16], radius=int(r), fill=(0, 0, 0, int(150 * q)))
        im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(18)))
        im.paste(piece, (int(round(dd[0])), int(round(dd[1]))), mk)
    return im.convert('RGB'), (dd, r, q), m, p

def window_frame(d, geo, t, m):
    if not geo: return
    dd, r, q = geo
    if q < 0.6 or m == 'drawer': return
    a = clamp((q - 0.6) / 0.4)
    if m == 'pip':
        d.ellipse(dd, outline=A(VGOLD, a), width=5)
        if GL: GL.ellipse(dd, outline=A(VGOLD, a), width=12)
        # live dot + label under the bubble
        txt(d, dd[0] + 70, dd[3] + 12, '@coach.agz', f(MONO, 24), GOLD, a)
        return
    d.rounded_rectangle(dd, radius=int(r), outline=A(VGOLD, 0.7 * a), width=3)
    brackets(d, dd[0] - 10, dd[1] - 10, dd[2] + 10, dd[3] + 10, A(VGOLD, a), 40, 6)
    if GL: brackets(GL, dd[0] - 10, dd[1] - 10, dd[2] + 10, dd[3] + 10, A(VGOLD, a), 40, 12)
    d.ellipse([dd[0] + 22, dd[1] + 22, dd[0] + 38, dd[1] + 38], fill=A(RED, a if int(t * 3) % 2 == 0 else a * 0.3))
    txt(d, dd[0] + 48, dd[1] + 16, 'REC', f(MONO, 22), WHITE, a * 0.9)

# =====================================================================================
# SCENES
# =====================================================================================
# --- S0 text hook (frame 0, premium, Barlow Condensed so sentence case is possible) ---
HOOK_END = max(3.0, min(6.0, T('protocol', end=True) + 0.5))   # spoken hook ends at the pause after 'protocol'
def text_hook(im, t):
    if t >= HOOK_END + 0.15: return
    a = 1 - clamp((t - HOOK_END) / 0.15)
    d = ImageDraw.Draw(im, 'RGBA')
    s = lerp(1.0, 1.04, clamp(t / HOOK_END))          # slow 100->104% push over the hold
    l1 = [('2 compounds', WHITE)]
    l2 = [('every ', WHITE), ('STEROID', VGOLD), (' cycle needs', WHITE)]
    fn = f(BC8, int(92 * s))
    def wline(parts): return sum(d.textlength(p, font=fn) for p, _ in parts)
    w1, w2 = wline(l1), wline(l2); lh = int(100 * s)
    bw = max(w1, w2) + 70; x0 = (W - bw) / 2; y0 = 300 - lh * 0.1
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); ld = ImageDraw.Draw(lay)
    ld.rounded_rectangle([x0, y0, x0 + bw, y0 + lh * 2 + 46], radius=26, fill=(4, 5, 10, 215))
    ld.rectangle([x0, y0 + 22, x0 + 7, y0 + lh * 2 + 24], fill=GOLD + (255,))
    for li, (parts, ww) in enumerate([(l1, w1), (l2, w2)]):
        x = (W - ww) / 2; y = y0 + 14 + li * lh
        for p, col in parts:
            ld.text((x, y), p, font=fn, fill=col + (255,)); x += ld.textlength(p, font=fn)
    if a < 1: lay.putalpha(lay.split()[3].point(lambda v: int(v * a)))
    comp(im, lay)
    if GL: GL.text(((W - w2) / 2 + d.textlength('every ', font=fn), y0 + 14 + lh), 'STEROID', font=fn, fill=A(VGOLD, 0.55 * a))

# --- topic band (after hook until midpoint; only over plain talking head) ---
MID = DUR / 2
def topic_band(im, t, m, p, hud_busy):
    return   # suppressed this video: the top zone carries graphics through the whole first half (see README)
    if t < HOOK_END or t >= MID + 0.15: return
    a = appear(t, HOOK_END, 0.15) * (1 - clamp((t - MID) / 0.15))
    if m != 'full': a *= (1 - p)
    if hud_busy: a *= 0
    if a <= 0.01: return
    d = ImageDraw.Draw(im, 'RGBA')
    d.rectangle([8, 212, W, 300], fill=NAVY + (int(220 * a),))
    fn = f(BC8, 56); parts = [('2 compounds every ', CREAM), ('STEROID', VGOLD), (' cycle needs', CREAM)]
    x = 40
    for s_, c_ in parts: d.text((x, 222), s_, font=fn, fill=A(c_, a)); x += d.textlength(s_, font=fn)
    txt(d, W - 40, 238, '@coach.agz', f(MONO, 24), GOLD, a, anchor='ra')

# --- S1 side card: heart, shield cracks on "unprotected" (side chosen away from face) ---
def side_x(t, w):
    cx, _, fw = face_at(t)
    return (W - w - 30) if cx < 560 else 30
def s1_side(im, t):
    t0 = C['cv1'] - 0.15; t1 = C['why_e'] + 0.25
    if not (t0 - 0.01 <= t < t1 + 0.2): return False
    a = life(t, t0, t1, 0.22, 0.18); w, h = 300, 430; x0 = side_x(t0 + 0.5, w); y0 = 560
    dx = lerp(40 if x0 > 500 else -40, 0, expo((t - t0) / 0.25))
    x0 += dx
    frosted(im, (x0, y0, x0 + w, y0 + h), 0.84, 14)
    d = ImageDraw.Draw(im, 'RGBA')
    panel_box(d, x0, y0, x0 + w, y0 + h, a, col=CYAN)
    txt(d, x0 + 22, y0 + 18, 'CARDIO · SCAN', f(MONO, 24), CYAN, a)
    beat = 1 + 0.05 * max(0, math.sin(t * 7.5)) ** 8
    hp = heart_pts(x0 + w / 2, y0 + 200, 7.2 * beat)
    d.line(hp + [hp[0]], fill=A(CYAN, a), width=4)
    if GL: GL.line(hp + [hp[0]], fill=A(CYAN, a), width=10)
    # ECG trace sweeping
    pts = []
    for i in range(60):
        xx = x0 + 20 + i * (w - 40) / 59; ph = (i / 59 * 3 - t * 1.5) % 1
        yy = y0 + 330 - (60 if 0.47 < ph < 0.5 else -22 if 0.5 < ph < 0.53 else 0)
        pts.append((xx, yy))
    d.line(pts, fill=A(GREEN if t < C['unprot'] else RED, a), width=3)
    if GL: GL.line(pts, fill=A(GREEN if t < C['unprot'] else RED, a * 0.8), width=8)
    # shield outline that cracks
    sx, sy = x0 + w / 2, y0 + 205
    sh = [(sx - 70, sy - 85), (sx + 70, sy - 85), (sx + 70, sy - 10), (sx, sy + 70), (sx - 70, sy - 10)]
    if t < C['unprot']:
        d.line(sh + [sh[0]], fill=A(VGOLD, a * appear(t, t0 + 0.3)), width=4)
    else:
        q = appear(t, C['unprot'], 0.12)
        off = 14 * q
        d.line([(sx - 70 - off, sy - 85), (sx - 6 - off, sy - 85), (sx - 18 - off, sy - 10), (sx - 2 - off, sy + 64), (sx - 70 - off, sy - 10), (sx - 70 - off, sy - 85)], fill=A(VGOLD, a * (1 - 0.5 * q)), width=4)
        d.line([(sx + 6 + off, sy - 85), (sx + 70 + off, sy - 85), (sx + 70 + off, sy - 10), (sx + 2 + off, sy + 64), (sx + 14 + off, sy - 20), (sx + 6 + off, sy - 85)], fill=A(VGOLD, a * (1 - 0.5 * q)), width=4)
        tag(d, x0 + 22, y0 + h - 66, 'UNPROTECTED', RED, 30, a * q)
    return True

# --- S2 top HUD: two mechanism lanes, both stamped UNMANAGED on "neither" ---
def s2_hud(im, t):
    t0 = C['mech'] - 0.1; t1 = C['lipids'] - 0.3
    if not (t0 <= t < t1 + 0.2): return False
    a = life(t, t0, t1, 0.2, 0.16)
    x0, y0, x1, y1 = 60, 330, 1020, 540
    frosted(im, (x0, y0, x1, y1), 0.82, 14); d = ImageDraw.Draw(im, 'RGBA')
    panel_box(d, x0, y0, x1, y1, a)
    txt(d, x0 + 26, y0 + 18, 'ANDROGENS · CV LOAD', f(MONO, 26), VGOLD, a)
    for i, (num, nm, col) in enumerate([('01', 'LIPIDS', AMBER), ('02', 'PRESSURE', RED)]):
        la = a * appear(t, t0 + 0.25 + i * 0.35, 0.2); lx = x0 + 26 + i * 470; ly = y0 + 70
        d.rounded_rectangle([lx, ly, lx + 440, ly + 110], radius=12, fill=A((12, 16, 26), la), outline=A(col, la), width=3)
        txt(d, lx + 18, ly + 8, num, f(BEB, 90), col, la); txt(d, lx + 110, ly + 14, nm, f(BEB, 58), WHITE, la)
        if GL: GL.rounded_rectangle([lx, ly, lx + 440, ly + 110], radius=12, outline=A(col, la * 0.7), width=8)
        if t >= C['neither']:
            q = appear(t, C['neither'] + i * 0.12, 0.1)
            s = lerp(1.4, 1.0, q)
            fn = f(MONO, int(26 * s)); lab = 'UNMANAGED'; tw = d.textlength(lab, font=fn)
            bx = lx + 110; by = ly + 70
            d.rectangle([bx, by, bx + tw + 20, by + 32 * s], outline=A(RED, la * q), width=3)
            txt(d, bx + 10, by + 2, lab, fn, RED, la * q)
    return True

# --- S3 split: lipid mechanism (liver receptor dimming, artery narrowing) -> lab flags bar chart ---
P3 = (60, 890, 1020, 1350)
def s3_split(im, t, geo):
    m, p, a0, b0 = mode_at(t)
    if m != 'split' or a0 != MODES[0][0] or p <= 0: return
    a = clamp((p - 0.5) / 0.5)
    d = ImageDraw.Draw(im, 'RGBA'); x0, y0, x1, y1 = P3
    phase2 = t >= C['panel'] - 0.1
    panel_box(d, x0, y0, x1, y1, a, 'MECHANISM 01' if not phase2 else 'YOUR LIPID PANEL', 'LIPIDS', AMBER, t)
    if not phase2:
        # liver with LDL receptors (left)
        la = a * appear(t, C['lipids'] + 0.2)
        lx, ly = x0 + 40, y0 + 80
        d.rounded_rectangle([lx, ly, lx + 400, ly + 230], radius=16, outline=A(GOLD, la), width=3, fill=A((14, 12, 10), la * 0.8))
        txt(d, lx + 20, ly + 12, 'LIVER', f(BEB, 50), WHITE, la)
        act = 1.0 if t < C['downreg'] else lerp(1.0, 0.33, expo((t - C['downreg']) / 0.9))
        for k in range(6):
            rx = lx + 30 + k * 60; ry = ly + 120; on = k < round(act * 6)
            col = CYAN if on else (60, 66, 80)
            d.arc([rx, ry, rx + 40, ry + 40], 180, 360, fill=A(col, la), width=5)
            d.line([(rx + 20, ry + 20), (rx + 20, ry + 60)], fill=A(col, la), width=4)
            if on and GL: GL.arc([rx, ry, rx + 40, ry + 40], 180, 360, fill=A(col, la), width=10)
        txt(d, lx + 20, ly + 186, 'LDL-RECEPTOR ACTIVITY', f(MONO, 22), CYAN, la)
        if t >= C['downreg']: tag(d, lx + 250, ly + 10, '↓ DOWN', RED, 26, la * appear(t, C['downreg']))
        if t >= C['hdl1']:
            ha = a * appear(t, C['hdl1']); tag(d, lx, ly + 250, 'HDL ↓', RED, 30, ha)
        # artery cross-section (right): plaque grows as ApoB climbs
        aa = a * appear(t, C['apob1'] - 0.4)
        if aa > 0:
            cx, cy = x0 + 700, y0 + 230
            pl = 0 if t < C['apob1'] else expo((t - C['apob1']) / 2.2)
            d.ellipse([cx - 150, cy - 150, cx + 150, cy + 150], fill=A((60, 14, 20), aa), outline=A(CRIMSON, aa), width=8)
            if GL: GL.ellipse([cx - 150, cy - 150, cx + 150, cy + 150], outline=A(RED, aa * 0.8), width=12)
            d.ellipse([cx - 118, cy - 118, cx + 118, cy + 118], fill=A((150, 30, 40), aa))
            # plaque crescent grows from the top-left wall, lumen shrinks
            r_l = lerp(110, 52, pl); ox = lerp(0, 40, pl); oy = lerp(0, 34, pl)
            d.ellipse([cx - 118, cy - 118, cx + 118, cy + 118], fill=A(AMBER, aa * min(1, pl * 3)))
            d.ellipse([cx + ox - r_l, cy + oy - r_l, cx + ox + r_l, cy + oy + r_l], fill=A((150, 30, 40), aa))
            for k in range(int(pl * 12)):
                ang = 3.6 + k * 0.22; rr = 92
                d.ellipse([cx + rr * math.cos(ang) - 6, cy + rr * math.sin(ang) - 6, cx + rr * math.cos(ang) + 6, cy + rr * math.sin(ang) + 6], fill=A((255, 230, 140), aa))
            txt(d, cx - 150, y0 + 70, 'ARTERY · CROSS-SECTION', f(MONO, 22), CREAM, aa)
            if t >= C['apob1']: tag(d, cx + 40, cy + 120, 'ApoB ↑', RED, 28, aa * appear(t, C['apob1']))
            if t >= C['plaque']: tag(d, cx - 160, cy + 120, 'PLAQUE ↑', AMBER, 28, aa * appear(t, C['plaque']))
    else:
        # horizontal bar chart with reference band + H/L flags (no invented numbers)
        rows = [('LDL', 0.86, 'H', RED, C['panel'] + 0.2), ('HDL', 0.22, 'L', RED, C['panel'] + 0.55), ('ApoB', 0.80, 'H', RED, C['panel'] + 0.9)]
        bx0, bx1 = x0 + 180, x1 - 120
        rz0, rz1 = lerp(bx0, bx1, 0.30), lerp(bx0, bx1, 0.62)
        ra = a * appear(t, C['panel'] - 0.1)
        d.rectangle([rz0, y0 + 80, rz1, y0 + 360], fill=A(GREEN, 0.10 * ra)); d.line([(rz0, y0 + 80), (rz0, y0 + 360)], fill=A(GREEN, 0.6 * ra), width=2); d.line([(rz1, y0 + 80), (rz1, y0 + 360)], fill=A(GREEN, 0.6 * ra), width=2)
        txt(d, rz0 + 8, y0 + 66, 'REFERENCE', f(MONO, 20), GREEN, ra)
        for i, (nm, v, fl, col, tt) in enumerate(rows):
            ya = a * appear(t, tt, 0.2); yy = y0 + 110 + i * 86
            txt(d, x0 + 40, yy - 4, nm, f(BEB, 56), WHITE, ya)
            grow = expo((t - tt) / 0.6); xe = lerp(bx0, lerp(bx0, bx1, v), grow)
            lit_bar(d, bx0, yy + 6, xe, yy + 50, col if (v > 0.62 or v < 0.30) else CYAN, ya)
            if GL: GL.rectangle([bx0, yy + 6, xe, yy + 50], fill=A(col, ya * 0.5))
            if grow > 0.8: txt(d, bx1 + 30, yy - 6, fl, f(BEB, 64), RED, ya * clamp((grow - 0.8) / 0.2))
        txt(d, x0 + 40, y1 - 50, 'ILLUSTRATIVE · ENHANCED ATHLETE, FIRST PANEL', f(MONO, 20), MUTED, ra)
        if t >= C['already']:
            q = expo((t - C['already']) / 0.18); vx1 = lerp(x0, x1, q); vy = y1 - 120
            if GL: GL.rectangle([x0 - 4, vy - 6, vx1 + 4, vy + 70], outline=A(RED, a), width=10)
            lit_bar(d, x0, vy, vx1, vy + 64, RED, a)
            if q > 0.6: txt(d, x0 + 26, vy + 6, 'FLAGGED ON ARRIVAL', f(BEB, 58), WHITE, a)

# --- S4 top HUD table: statin vs ezetimibe ---
def s4_table(im, t):
    t0 = C['fix1'] - 0.1; t1 = C['eze2'] - 0.35
    if not (t0 <= t < t1 + 0.2): return False
    a = life(t, t0, t1, 0.2, 0.16)
    x0, y0, x1, y1 = 40, 310, 1040, 620
    frosted(im, (x0, y0, x1, y1), 0.84, 14); d = ImageDraw.Draw(im, 'RGBA')
    panel_box(d, x0, y0, x1, y1, a)
    txt(d, x0 + 26, y0 + 16, 'FIX 01 · LIPIDS', f(MONO, 30), VGOLD, a)
    # pill: EZETIMIBE slides in heavy on the word
    if t >= C['eze1'] - 0.05:
        q = expo((t - C['eze1'] + 0.05) / 0.22); px = lerp(x1 + 40, x1 - 380, q)
        d.rectangle([px, y0 + 10, x1 - 14, y0 + 62], fill=A(VGOLD, a)); txt(d, px + 16, y0 + 12, 'EZETIMIBE', f(BEB, 52), INK, a)
        if GL: GL.rectangle([px - 4, y0 + 6, x1 - 10, y0 + 60], outline=A(VGOLD, a), width=10)
    cols = [('STATIN', x0 + 280, RED, C['statin']), ('EZETIMIBE', x0 + 640, VGOLD, C['statin'] + 0.25)]
    for nm, cx, col, tt in cols:
        ca = a * appear(t, tt)
        if ca <= 0: continue
        d.line([(cx - 10, y0 + 84), (cx + 320, y0 + 84)], fill=A(col, ca), width=4)
        txt(d, cx, y0 + 92, nm, f(BEB, 60), col, ca)
    rows = [('WORKS AT', C['liver1'], ['LIVER', 'GUT']), ('SIDE-EFFECT LOAD', C['burden'], ['FULL', 'LOW'])]
    for i, (lab, tt, vals) in enumerate(rows):
        ra = a * appear(t, tt); yy = y0 + 172 + i * 66
        if ra <= 0: continue
        txt(d, x0 + 30, yy + 4, lab.replace('SIDE-EFFECT ', 'SIDE FX '), f(MONO, 30), CREAM, ra)
        cross(d, x0 + 280, yy + 8, RED, 1.0, ra) if i == 1 else None
        txt(d, x0 + 280 + (44 if i == 1 else 0), yy - 6, vals[0], f(BC8, 52), RED if i == 1 else WHITE, ra)
        txt(d, x0 + 640, yy - 6, vals[1], f(BC8, 52), WHITE, ra)
    return True

# --- S5 PiP: gut -> liver -> blood flow; NPC1L1 gate blocked ---
def s5_pip(im, t):
    m, p, a0, b0 = mode_at(t)
    if m != 'pip' or p <= 0: return
    a = clamp((p - 0.4) / 0.6); d = ImageDraw.Draw(im, 'RGBA')
    txt(d, 70, 170, 'MECHANISM', f(MONO, 28), VGOLD, a); txt(d, 66, 204, 'EZETIMIBE', f(BEB, 120), WHITE, a)
    txt(d, 70, 330, 'CHOLESTEROL ABSORPTION', f(MONO, 26), CREAM, a)
    d.line([(70, 372), (640, 372)], fill=A(GOLD, a), width=3)
    blocked = t >= C['blocks'] + 0.2
    # GUT lane
    gy = 560
    node(d, 70, gy - 70, 330, gy + 70, 'GUT', 'INTESTINE', AMBER, a)
    gx = 470
    d.rounded_rectangle([gx - 50, gy - 90, gx + 50, gy + 90], radius=16, outline=A(CYAN if not blocked else (60, 70, 80), a), width=4)
    txt(d, gx - 48, gy + 98, 'NPC1L1', f(MONO, 22), CYAN, a); txt(d, gx - 70, gy - 128, 'TRANSPORTER', f(MONO, 20), MUTED, a)
    flow(d, 335, gy, 420, gy, t, (255, 230, 140), 4, a=a)
    if not blocked: flow(d, 520, gy, 760, gy, t, (255, 230, 140), 5, a=a)
    else: flow(d, 520, gy, 760, gy, t, (255, 230, 140), 1, a=a * 0.5)
    if t >= C['blocks']:
        q = expo((t - C['blocks']) / 0.16); yb = lerp(gy - 260, gy - 30, q)
        d.rounded_rectangle([gx - 120, yb, gx + 120, yb + 60], radius=10, fill=A(VGOLD, a)); txt(d, gx - 104, yb + 6, 'EZETIMIBE', f(BEB, 50), INK, a)
        if GL: GL.rounded_rectangle([gx - 124, yb - 4, gx + 124, yb + 64], radius=12, outline=A(VGOLD, a), width=10)
        if q >= 1: cross(d, gx + 130, gy - 20, RED, 1.1, a)
    if t >= C['absorbed']: tag(d, 560, gy + 60, 'LESS ABSORBED', RED, 26, a * appear(t, C['absorbed']))
    # LIVER
    ly = 860
    la = a * appear(t, C['delivered'] - 0.3)
    node(d, 380, ly - 80, 700, ly + 80, 'LIVER', 'STARVED OF CHOLESTEROL' if t >= C['delivered'] else '', GOLD, la)
    arrow(d, 760, gy + 20, 640, ly - 86, (255, 230, 140), 4, la * (0.4 if blocked else 1))
    # BLOOD vessel along bottom; LDL pulled up into liver
    by = 1150; ba = a * appear(t, C['pulling'] - 0.5)
    d.rounded_rectangle([70, by - 50, 1010, by + 50], radius=50, fill=A((90, 16, 26), ba), outline=A(CRIMSON, ba), width=5)
    if GL: GL.rounded_rectangle([70, by - 50, 1010, by + 50], radius=50, outline=A(RED, ba * 0.7), width=10)
    txt(d, 90, by + 60, 'BLOOD · CIRCULATING LDL', f(MONO, 22), CREAM, ba)
    pull = 0 if t < C['pulling'] else expo((t - C['pulling']) / 1.4)
    rng = np.random.default_rng(11)
    for k in range(14):
        x = 120 + k * 64 + 8 * math.sin(t * 2 + k); y = by + 10 * math.sin(t * 3 + k * 1.7)
        if k % 2 == 0 and pull > 0:
            tx, ty = 540 + (k - 7) * 18, ly + 70; q = clamp(pull * 1.3 - k * 0.03)
            x, y = lerp(x, tx, q), lerp(y, ty, q)
            if q >= 1: continue
        d.ellipse([x - 14, y - 14, x + 14, y + 14], fill=A(AMBER, ba)); txt(d, x - 11, y - 9, 'LDL', f(MONO, 12), INK, ba)
    if pull > 0:
        for xx in (470, 540, 610): arrow(d, xx, by - 56, xx, ly + 92, CYAN, 4, ba * min(1, pull * 2))
        tag(d, 720, ly + 130, 'LDL CLEARED ↑', GREEN, 26, ba * appear(t, C['pulling'] + 0.4))

# --- S6 side-by-side: face left, before/after bar graph right, then zero chips ---
def s6_sbs(im, t):
    m, p, a0, b0 = mode_at(t)
    if m != 'sbs' or p <= 0: return
    a = clamp((p - 0.4) / 0.6); d = ImageDraw.Draw(im, 'RGBA')
    x0, y0, x1, y1 = 560, 330, 1046, 1290
    panel_box(d, x0, y0, x1, y1, a, 'BLOODWORK', '', VGOLD, t)
    txt(d, x0 + 26, y0 + 64, 'BEFORE vs ON EZETIMIBE', f(MONO, 20), MUTED, a)
    # vertical paired bars: LDL, ApoB (drop), HDL ratio (improve)
    gx0, gy1 = x0 + 40, y0 + 520
    d.line([(gx0 - 10, gy1), (x1 - 30, gy1)], fill=A((90, 94, 110), a), width=2)
    sets = [('LDL', 0.82, 0.42, C['lowldl']), ('ApoB', 0.78, 0.44, C['lowapob']), ('HDL\nRATIO', 0.35, 0.62, C['ratio'])]
    for i, (nm, b, af, tt) in enumerate(sets):
        bx = gx0 + i * 140; ba = a * appear(t, tt - 0.6)
        hb = 360 * b * ba; lit_bar(d, bx, gy1 - hb, bx + 50, gy1, (90, 94, 110), ba)
        g = expo((t - tt) / 0.5); ha = 360 * lerp(b, af, g) * ba
        col = GREEN if t >= tt else CYAN
        lit_bar(d, bx + 58, gy1 - ha, bx + 108, gy1, col, ba)
        if GL and t >= tt: GL.rectangle([bx + 58, gy1 - ha, bx + 108, gy1], fill=A(col, ba * 0.6))
        for li, ln in enumerate(nm.split('\n')): txt(d, bx, gy1 + 10 + li * 34, ln, f(BEB, 38), WHITE, ba)
        if t >= tt + 0.3: txt(d, bx + 58, gy1 - ha - 52, '↓' if af < b else '↑', f(BEB, 52), GREEN, ba * appear(t, tt + 0.3))
    # zero chips
    zs = [('HORMONAL', 'INTERFERENCE', C['zero1']), ('PERFORMANCE', 'IMPACT', C['zero2'])]
    for i, (l1, l2, tt) in enumerate(zs):
        za = a * appear(t, tt, 0.14); zy = y0 + 640 + i * 130
        if za <= 0: continue
        s = lerp(1.25, 1.0, expo((t - tt) / 0.16))
        txt(d, x0 + 30, zy - 8, '0', f(BEB, int(120 * s)), VGOLD, za)
        if GL: GL.text((x0 + 30, zy - 8), '0', font=f(BEB, int(120 * s)), fill=A(VGOLD, za * 0.6))
        txt(d, x0 + 120, zy + 8, l1, f(BC8, 40), WHITE, za); txt(d, x0 + 120, zy + 52, l2, f(MONO, 24), CREAM, za)
    if t >= C['cleanest']:
        tag(d, x0 + 30, y1 - 80, 'CLEANEST LIPID TOOL', VGOLD, 28, a * appear(t, C['cleanest']))

# --- S7 chapter wipe "PROBLEM 02" -> hands off into a persistent top tag ---
def s7_wipe(im, t):
    t0 = C['p2'] - 0.1; t1 = C['p2'] + 1.55
    if t < t0: return
    # handoff tag persists until telmisartan fix
    if t >= t1 - 0.1 and t < C['fix2'] - 0.2:
        a = 1 - clamp((t - C['fix2'] + 0.35) / 0.15)
        m, p, _, _ = mode_at(t)
        d = ImageDraw.Draw(im, 'RGBA'); q = expo((t - t1 + 0.1) / 0.3)
        y = lerp(800, 226, q) if m != 'split' else 60
        lit_bar(d, 40, y, 40 + 300, y + 58, RED, a); txt(d, 56, y + 4, 'PROBLEM 02', f(BEB, 54), WHITE, a)
        if GL: GL.rectangle([36, y - 4, 344, y + 62], outline=A(RED, a), width=10)
        return
    if t >= t1: return
    pin = expo((t - t0) / 0.22); pout = ease_io((t - (t1 - 0.3)) / 0.3)
    xr = lerp(0, W, pin); xl = lerp(0, W, pout)
    d = ImageDraw.Draw(im, 'RGBA')
    d.rectangle([xl, 0, xr, H], fill=NAVY + (250,))
    d.rectangle([max(xl, xr - 10), 0, xr, H], fill=GOLD + (255,))
    if pin > 0.7:
        a = clamp((pin - 0.7) / 0.3) * (1 - pout)
        txt(d, 90, 700, 'PROBLEM', f(BEB, 120), CREAM, a)
        s = lerp(1.3, 1.0, expo((t - t0 - 0.15) / 0.2))
        txt(d, 80, 790, '02', f(BEB, int(380 * s)), RED, a)
        if GL: GL.text((80, 790), '02', font=f(BEB, int(380 * s)), fill=A(RED, a * 0.6))
        if t >= C['bp1']: txt(d, 90, 1200, 'BLOOD PRESSURE', f(BC8, 72), WHITE, a * appear(t, C['bp1']))
        if t >= C['bp1'] + 0.5: txt(d, 90, 1280, '+ STRUCTURAL STRESS', f(BC8, 56), VGOLD, a * appear(t, C['bp1'] + 0.5))

# --- S8a top HUD: BP gauge needle climbs into red ---
def gauge(d, cx, cy, r, v, a, lab):
    for k in range(40):
        u = k / 39; ang = math.pi * (1 + u)
        col = GREEN if u < 0.45 else AMBER if u < 0.7 else RED
        d.line([(cx + (r - 22) * math.cos(ang), cy + (r - 22) * math.sin(ang)), (cx + r * math.cos(ang), cy + r * math.sin(ang))], fill=A(col, a), width=7)
    ang = math.pi * (1 + v); d.line([(cx, cy), (cx + (r - 30) * math.cos(ang), cy + (r - 30) * math.sin(ang))], fill=A(WHITE, a), width=6)
    if GL: GL.line([(cx, cy), (cx + (r - 30) * math.cos(ang), cy + (r - 30) * math.sin(ang))], fill=A(WHITE, a * 0.6), width=10)
    d.ellipse([cx - 12, cy - 12, cx + 12, cy + 12], fill=A(WHITE, a)); txt(d, cx, cy + 14, lab, f(MONO, 22), CREAM, a, anchor='ma')
def s8a_hud(im, t):
    t0 = C['supra'] - 0.1; t1 = C['overload'] - 0.3
    if not (t0 <= t < t1 + 0.2): return False
    a = life(t, t0, t1, 0.2, 0.15)
    x0, y0, x1, y1 = 60, 320, 1020, 560
    frosted(im, (x0, y0, x1, y1), 0.84, 14); d = ImageDraw.Draw(im, 'RGBA')
    panel_box(d, x0, y0, x1, y1, a, col=RED)
    txt(d, x0 + 26, y0 + 16, 'SUPRAPHYSIOLOGICAL ANDROGENS', f(MONO, 24), VGOLD, a)
    # vessel narrowing (resistance)
    nr = 0 if t < C['resist'] else expo((t - C['resist']) / 0.6)
    vx0, vx1, vy = x0 + 40, x0 + 480, y0 + 150; hh = lerp(46, 24, nr)
    d.rounded_rectangle([vx0, vy - hh - 10, vx1, vy + hh + 10], radius=20, outline=A(CRIMSON, a), width=6)
    d.rectangle([vx0 + 8, vy - hh, vx1 - 8, vy + hh], fill=A((150, 30, 40), a))
    flow(d, vx0 + 20, vy, vx1 - 20, vy, t, (255, 140, 140), 6, speed=lerp(0.9, 2.2, nr), a=a, r=6)
    txt(d, vx0, y1 - 44, 'VASCULAR RESISTANCE', f(MONO, 22), CREAM, a)
    if nr > 0: tag(d, vx0 + 300, y1 - 52, '↑', RED, 26, a * nr)
    v = 0.3 if t < C['bpclimb'] else lerp(0.3, 0.88, expo((t - C['bpclimb']) / 0.9))
    gauge(d, x0 + 740, y0 + 190, 150, v, a, 'BLOOD PRESSURE')
    return True

# --- S8b split: LV wall thickening + EF meter + silent line chart over years ---
def s8b_split(im, t, geo):
    m, p, a0, b0 = mode_at(t)
    if m != 'split' or a0 != MODES[4][0] or p <= 0: return
    a = clamp((p - 0.5) / 0.5); d = ImageDraw.Draw(im, 'RGBA'); x0, y0, x1, y1 = P3
    panel_box(d, x0, y0, x1, y1, a, 'LEFT VENTRICLE', 'STRUCTURE', RED, t)
    cx, cy = x0 + 210, y0 + 250
    th = 0 if t < C['lvh'] else expo((t - C['lvh']) / 1.5)
    beat = 1 + 0.04 * max(0, math.sin(t * 7)) ** 8
    ro = 150 * beat; ri = lerp(108, 62, th) * beat
    d.ellipse([cx - ro, cy - ro, cx + ro, cy + ro], fill=A((120, 20, 32), a), outline=A(RED, a), width=4)
    d.ellipse([cx - ri, cy - ri, cx + ri, cy + ri], fill=A((25, 8, 12), a), outline=A(CYAN, a), width=3)
    if GL: GL.ellipse([cx - ro, cy - ro, cx + ro, cy + ro], outline=A(RED, a), width=10)
    txt(d, cx - 150, y0 + 72, 'LV · SHORT AXIS', f(MONO, 20), CREAM, a)
    if t >= C['wall']:
        wa = a * appear(t, C['wall']); arrow(d, cx + ro + 30, cy, cx + ri + 6, cy, VGOLD, 4, wa, 14)
        tag(d, cx - 150, cy + ro + 14, 'WALL THICKENS', RED, 24, wa)
    # EF meter
    ex0 = x0 + 430
    if t >= C['ef'] - 0.2:
        ea = a * appear(t, C['ef'] - 0.2); ef = lerp(0.82, 0.48, expo((t - C['ef']) / 1.0))
        txt(d, ex0, y0 + 72, 'EJECTION FRACTION', f(MONO, 22), CREAM, ea)
        d.rectangle([ex0, y0 + 104, x1 - 40, y0 + 140], outline=A((70, 74, 90), ea), width=2)
        lit_bar(d, ex0 + 3, y0 + 107, lerp(ex0 + 3, x1 - 43, ef), y0 + 137, AMBER if ef > 0.6 else RED, ea)
        txt(d, x1 - 40, y0 + 146, '↓ DECLINING', f(MONO, 22), RED, ea, anchor='ra')
    # silent line chart over years
    if t >= C['silent'] - 0.3:
        la = a * appear(t, C['silent'] - 0.3); gx0, gx1, gy0, gy1 = ex0, x1 - 40, y0 + 210, y0 + 400
        d.line([(gx0, gy1), (gx1, gy1)], fill=A((90, 94, 110), la), width=2); d.line([(gx0, gy0), (gx0, gy1)], fill=A((90, 94, 110), la), width=2)
        txt(d, gx1, gy1 + 6, 'YEARS →', f(MONO, 20), MUTED, la, anchor='ra'); txt(d, gx0 + 10, gy0 - 4, 'LV MASS', f(MONO, 20), MUTED, la)
        pr = clamp((t - C['silent']) / 1.8)
        pts = [(lerp(gx0, gx1, u / 30), gy1 - 20 - 150 * (u / 30) ** 1.8) for u in range(31)]
        n = max(2, int(pr * 31)); seg = pts[:n]
        d.line(seg, fill=A(RED, la), width=5)
        if GL: GL.line(seg, fill=A(RED, la), width=10)
        if pr > 0.5: tag(d, gx0 + 20, gy0 + 30, 'NO SYMPTOMS', (90, 94, 110), 22, la * clamp((pr - 0.5) * 3), glow=False)

# --- S9a gold pill slam: FIX 02 TELMISARTAN over chest-free roof zone ---
def s9a_pill(im, t):
    t0 = C['fix2'] - 0.1; t1 = C['ang2'] - 0.4
    if not (t0 <= t < t1 + 0.2): return False
    a = life(t, t0, t1, 0.12, 0.15); d = ImageDraw.Draw(im, 'RGBA')
    lit_bar(d, 40, 226, 40 + 300, 284, VGOLD, a); txt(d, 56, 230, 'FIX 02', f(BEB, 54), INK, a)
    if GL: GL.rectangle([36, 222, 344, 288], outline=A(VGOLD, a), width=10)
    txt(d, 360, 236, 'MY #1 HEALTH COMPOUND', f(MONO, 26), CREAM, a * appear(t, C['fav']))
    if t >= C['telmi1'] - 0.05:
        q = expo((t - C['telmi1'] + 0.05) / 0.14); s = lerp(1.25, 1.0, q)
        fn = f(BEB, int(140 * s)); lab = 'TELMISARTAN'; tw = d.textlength(lab, font=fn)
        x = (W - tw) / 2; y = 330
        frosted(im, (x - 30, y - 10, x + tw + 30, y + 150 * s), 0.7, 10); d = ImageDraw.Draw(im, 'RGBA')
        d.text((x, y), lab, font=fn, fill=A(VGOLD, a * q))
        if GL: GL.text((x, y), lab, font=fn, fill=A(VGOLD, a * q * 0.7))
        txt(d, W / 2, y + 150 * s + 4, 'ARB · ANGIOTENSIN II RECEPTOR BLOCKER', f(MONO, 24), CREAM, a * appear(t, C['telmi1'] + 0.4), anchor='ma')
    return True

# --- S9b drawer: footage slides up, mechanism panel underneath (Ang II key -> AT1 lock) ---
def s9b_drawer(im, t):
    m, p, a0, b0 = mode_at(t)
    if m != 'drawer' or p <= 0: return
    a = clamp((p - 0.3) / 0.7); d = ImageDraw.Draw(im, 'RGBA')
    y0 = lerp(H, 1530 - 520, p); x0, x1 = 30, 1050; y1 = y0 + 480
    d.rectangle([0, y0 - 6, W, y0], fill=A(VGOLD, 1));
    if GL: GL.rectangle([0, y0 - 8, W, y0 + 2], fill=A(VGOLD, 1))
    d.rectangle([0, y0, W, H], fill=A(DEEP, 0.96))
    txt(d, 50, y0 + 18, 'MECHANISM 02 · TELMISARTAN', f(MONO, 26), VGOLD, a)
    # angiotensin II "key" travelling toward AT1 receptor
    rx, ry = 380, y0 + 225
    blocked = t >= C['at1']
    d.rounded_rectangle([rx - 70, ry - 70, rx + 70, ry + 70], radius=18, outline=A(CYAN, a), width=5)
    d.rectangle([rx - 20, ry - 70, rx + 20, ry - 10], fill=A(DEEP, a))
    txt(d, rx, ry + 80, 'AT1 RECEPTOR', f(MONO, 22), CYAN, a, anchor='ma')
    kx = lerp(80, rx - 0, ((t * 0.7) % 1)) if not blocked else lerp(rx - 10, 120, expo((t - C['at1']) / 0.5))
    ky = ry - 110
    kcol = RED
    d.ellipse([kx - 38, ky - 38, kx + 38, ky + 38], fill=A(kcol, a)); txt(d, kx, ky - 18, 'ANG II', f(MONO, 20), WHITE, a, anchor='ma')
    if GL: GL.ellipse([kx - 44, ky - 44, kx + 44, ky + 44], outline=A(RED, a), width=8)
    if t >= C['constrict'] and not blocked: tag(d, 60, y0 + 330, 'CONSTRICTS · REMODELS', RED, 24, a * appear(t, C['constrict']))
    if blocked: tag(d, 60, y0 + 330, 'ANG II LOCKED OUT', GREEN, 24, a * appear(t, C['at1'] + 0.3))
    if blocked:
        q = expo((t - C['at1'] + 0.05) / 0.14)
        d.rounded_rectangle([rx - 22, lerp(ry - 200, ry - 70, q), rx + 22, lerp(ry - 140, ry - 10, q)], radius=6, fill=A(VGOLD, a))
        if GL: GL.rounded_rectangle([rx - 26, ry - 74, rx + 26, ry - 6], radius=8, outline=A(VGOLD, a * q), width=10)
        txt(d, rx + 90, ry - 40, 'TELMISARTAN', f(BEB, 46), VGOLD, a * q); txt(d, rx + 90, ry + 6, 'BLOCKS IT', f(MONO, 22), CREAM, a * q)
    # vessel relaxing + pressure gauge dropping
    vx0, vx1, vy = 640, 1020, y0 + 120
    rel = 0 if t < C['relax'] else expo((t - C['relax']) / 0.6)
    hh = lerp(26, 52, rel)
    d.rounded_rectangle([vx0, vy - hh - 10, vx1, vy + hh + 10], radius=24, outline=A(CRIMSON, a), width=6)
    d.rectangle([vx0 + 8, vy - hh, vx1 - 8, vy + hh], fill=A((150, 30, 40), a))
    flow(d, vx0 + 20, vy, vx1 - 20, vy, t, (255, 160, 160), 7, speed=lerp(2.0, 0.8, rel), a=a, r=6)
    txt(d, vx0, vy + 70, 'VESSEL', f(MONO, 22), CREAM, a)
    if rel > 0: tag(d, vx0 + 140, vy + 64, 'RELAXED', GREEN, 22, a * rel)
    if t >= C['pdrop']:
        pv = lerp(0.88, 0.38, expo((t - C['pdrop']) / 0.7)); gauge(d, 900, y0 + 330, 95, pv, a * appear(t, C['pdrop']), 'PRESSURE')
    if t >= C['wallred']:
        tag(d, 560, y0 + 250, 'WALL STRESS ↓', GREEN, 26, a * appear(t, C['wallred']))

# --- S10 stamp: gold-standard seal ---
def s10_stamp(im, t):
    t0 = C['gold'] - 0.05; t1 = C['lowers'] - 0.35
    if not (t0 <= t < t1 + 0.15): return False
    a = life(t, t0, t1, 0.1, 0.15); d = ImageDraw.Draw(im, 'RGBA')
    q = expo((t - t0) / 0.13); s = lerp(1.6, 1.0, q); rot = lerp(-24, -9, q)
    R = int(170 * s); lay = Image.new('RGBA', (2 * R + 20, 2 * R + 20), (0, 0, 0, 0)); ld = ImageDraw.Draw(lay)
    c = R + 10
    ld.ellipse([10, 10, 2 * R + 10, 2 * R + 10], fill=(18, 14, 4, 235), outline=VGOLD + (255,), width=8)
    ld.ellipse([30, 30, 2 * R - 10, 2 * R - 10], outline=VGOLD + (255,), width=3)
    for k in range(24):
        ang = k / 24 * 2 * math.pi; ld.ellipse([c + (R - 3) * math.cos(ang) - 5, c + (R - 3) * math.sin(ang) - 5, c + (R - 3) * math.cos(ang) + 5, c + (R - 3) * math.sin(ang) + 5], fill=VGOLD + (255,))
    ld.text((c, c - 0.62 * R), 'BODYBUILDER BP', font=f(MONO, int(20 * s)), fill=VGOLD + (255,), anchor='ma')
    ld.text((c, c - 0.36 * R), 'GOLD', font=f(BEB, int(96 * s)), fill=VGOLD + (255,), anchor='ma')
    ld.text((c, c + 0.12 * R), 'STANDARD', font=f(BEB, int(62 * s)), fill=CREAM + (255,), anchor='ma')
    ld.text((c, c + 0.52 * R), 'TELMISARTAN', font=f(MONO, int(20 * s)), fill=VGOLD + (255,), anchor='ma')
    lay = lay.rotate(rot, resample=Image.BICUBIC, expand=False)
    if a < 1: lay.putalpha(lay.split()[3].point(lambda v: int(v * a)))
    cx, cy, _ = face_at(t); px = 790 if cx < 560 else 290
    comp(im, lay, (px - c, 450 - c))
    if GL: GL.ellipse([px - R, 450 - R, px + R, 450 + R], outline=A(VGOLD, a), width=14)
    return True

# --- S11 PiP-rect + comparison table: telmisartan vs diuretics vs beta blockers ---
def s11_table(im, t):
    m, p, a0, b0 = mode_at(t)
    if m != 'pipr' or p <= 0: return
    a = clamp((p - 0.4) / 0.6); d = ImageDraw.Draw(im, 'RGBA')
    txt(d, 460, 170, 'BP OPTIONS', f(MONO, 28), VGOLD, a); txt(d, 456, 206, 'ON CYCLE', f(BEB, 110), WHITE, a)
    txt(d, 460, 330, 'WHAT EACH COSTS YOU', f(MONO, 24), CREAM, a)
    x0, y0, x1 = 40, 600, 1040
    cols = [('TELMISARTAN', VGOLD, 560), ('DIURETICS', CREAM, 740), ('BETA BLOCKER', CREAM, 900)]
    d.rounded_rectangle([x0, y0 - 80, x1, y0 + 560], radius=18, fill=A(DEEP, 0.85 * a), outline=A(VGOLD, 0.5 * a), width=2)
    d.rectangle([520, y0 - 80, 690, y0 + 560], fill=A(VGOLD, 0.10 * a))
    if GL: GL.rectangle([520, y0 - 80, 690, y0 + 560], outline=A(VGOLD, 0.6 * a), width=6)
    for nm, col, cx in cols:
        for li, ln in enumerate(nm.split(' ')): txt(d, cx + 45, y0 - 70 + li * 34 - (0 if ' ' in nm else -16), ln, f(BEB, 36), col, a, anchor='ma')
    rows = [('ARTERIAL RESISTANCE ↓', C['lowers'], ['ok', 'ok', 'ok']), ('HEART RATE INTACT', C['hr'], ['ok', 'ok', 'no']),
            ('ELECTROLYTES INTACT', C['electro'], ['ok', 'no', 'ok']), ('CARDIAC OUTPUT INTACT', C['blunted'], ['ok', 'ok', 'no'])]
    for i, (lab, tt, vals) in enumerate(rows):
        ra = a * appear(t, tt - 0.1); yy = y0 + 20 + i * 130
        if ra <= 0: continue
        d.line([(x0 + 20, yy + 100), (x1 - 20, yy + 100)], fill=A((50, 54, 66), ra), width=2)
        for li, ln in enumerate(lab.split(' ', 1)): txt(d, x0 + 24, yy + li * 40, ln, f(BC8 if li == 0 else BC6, 40 if li == 0 else 32), WHITE if li == 0 else CREAM, ra)
        for k, (v, (_, _, cx)) in enumerate(zip(vals, cols)):
            va = a * appear(t, tt + 0.08 * k, 0.12)
            (check if v == 'ok' else cross)(d, cx + 26, yy + 20, GREEN if v == 'ok' else RED, 1.3, va)

# --- S12 top line chart: LV mass regression, prevention vs reversal ---
def s12_chart(im, t):
    t0 = C['clinical'] - 0.2; t1 = C['hyper_e'] + 0.3
    if not (t0 <= t < t1 + 0.2): return False
    a = life(t, t0, t1, 0.2, 0.16)
    x0, y0, x1, y1 = 50, 300, 1030, 600
    frosted(im, (x0, y0, x1, y1), 0.80, 14); d = ImageDraw.Draw(im, 'RGBA')
    panel_box(d, x0, y0, x1, y1, a, col=GREEN)
    txt(d, x0 + 26, y0 + 16, 'CLINICAL DATA · LV MASS', f(MONO, 24), GREEN, a)
    gx0, gx1, gy0, gy1 = x0 + 60, x1 - 60, y0 + 70, y1 - 40
    d.line([(gx0, gy1), (gx1, gy1)], fill=A((90, 94, 110), a), width=2)
    txt(d, gx1, gy1 + 4, 'TIME ON TELMISARTAN →', f(MONO, 18), MUTED, a, anchor='ra')
    base_y = gy0 + 50
    d.line([(gx0, base_y), (gx1, base_y)], fill=A(RED, 0.5 * a), width=2); txt(d, gx0 + 6, base_y - 30, 'EXISTING LVH', f(MONO, 20), RED, a)
    pr = clamp((t - C['regression']) / 1.6)
    if pr > 0:
        pts = [(lerp(gx0, gx1, u / 30), base_y + (gy1 - base_y - 40) * (1 - math.exp(-3 * u / 30)) * 0.95) for u in range(31)]
        n = max(2, int(pr * 31)); d.line(pts[:n], fill=A(GREEN, a), width=6)
        if GL: GL.line(pts[:n], fill=A(GREEN, a), width=12)
        d.ellipse([pts[n - 1][0] - 9, pts[n - 1][1] - 9, pts[n - 1][0] + 9, pts[n - 1][1] + 9], fill=A(WHITE, a))
    if t >= C['prevention']:
        pa = a * appear(t, C['prevention']); tag(d, gx0 + 380, y0 + 70, 'PREVENTION', (90, 94, 110), 26, pa, glow=False)
        if t >= C['reversal']: d.line([(gx0 + 380, y0 + 92), (gx0 + 380 + tagw(d, 'PREVENTION', 26), y0 + 92)], fill=A(RED, a), width=4)
    if t >= C['reversal']:
        q = expo((t - C['reversal']) / 0.14); s = lerp(1.3, 1.0, q)
        tag(d, gx0 + 600, y0 + 66, 'REVERSAL', GREEN, int(34 * s), a * q)
    return True

# --- S13 flanking cards: problem -> solution, then merge into STACK bar ---
def s13_flank(im, t):
    t0 = C['endday'] - 0.1; t1 = C['cta'] - 0.3
    if not (t0 <= t < t1 + 0.2): return False
    a = life(t, t0, t1, 0.18, 0.15)
    merge = 0 if t < C['both'] else expo((t - C['both']) / 0.4)
    cards = [(30, 'PROBLEM 01', 'LIPIDS', 'EZETIMIBE', AMBER, C['eze3']), (W - 30 - 300, 'PROBLEM 02', 'PRESSURE', 'TELMISARTAN', RED, C['telmi3'])]
    for i, (cx0, k, prob, sol, col, ts) in enumerate(cards):
        ca = a * appear(t, t0 + 0.15 + i * 0.2, 0.2) * (1 - merge)
        if ca <= 0: continue
        y0 = lerp(620, 380, merge); w, h = 300, 400
        frosted(im, (cx0, y0, cx0 + w, y0 + h), 0.82, 14); d = ImageDraw.Draw(im, 'RGBA')
        d.rounded_rectangle([cx0, y0, cx0 + w, y0 + h], radius=18, outline=A(col, ca), width=3)
        if GL: GL.rounded_rectangle([cx0, y0, cx0 + w, y0 + h], radius=18, outline=A(col, ca), width=8)
        txt(d, cx0 + 20, y0 + 18, k, f(MONO, 24), col, ca); txt(d, cx0 + 20, y0 + 54, prob, f(BEB, 70), WHITE, ca)
        if t >= ts:
            sa = ca * appear(t, ts); arrow(d, cx0 + 40, y0 + 150, cx0 + 40, y0 + 230, col, 5, sa)
            lit_bar(d, cx0 + 16, y0 + 250, cx0 + w - 16, y0 + 320, VGOLD, sa); txt(d, cx0 + w / 2, y0 + 258, sol, f(BEB, 54 if len(sol) < 10 else 46), INK, sa, anchor='ma')
            txt(d, cx0 + 20, y0 + 340, 'ENVIRONMENT' if i == 0 else 'STRUCTURE', f(MONO, 22), CREAM, sa)
    if merge > 0:
        d = ImageDraw.Draw(im, 'RGBA'); ma = a * merge; x0, x1 = lerp(W / 2, 40, merge), lerp(W / 2, W - 40, merge); y = 330
        frosted(im, (x0, y, x1, y + 210), 0.82, 14); d = ImageDraw.Draw(im, 'RGBA')
        d.rectangle([x0, y, x1, y + 210], outline=A(VGOLD, ma), width=3)
        if GL: GL.rectangle([x0, y, x1, y + 210], outline=A(VGOLD, ma), width=10)
        if merge > 0.7:
            txt(d, 70, y + 16, 'THE CV PROTECTION STACK', f(MONO, 26), VGOLD, ma)
            lit_bar(d, 70, y + 60, 520, y + 130, VGOLD, ma); txt(d, 295, y + 66, 'EZETIMIBE', f(BEB, 60), INK, ma, anchor='ma')
            txt(d, 540, y + 66, '+', f(BEB, 60), WHITE, ma)
            lit_bar(d, 580, y + 60, 1010, y + 130, VGOLD, ma); txt(d, 795, y + 66, 'TELMISARTAN', f(BEB, 60), INK, ma, anchor='ma')
            if t >= C['everytime']: tag(d, 70, y + 148, 'EVERY CYCLE · EVERY COMPOUND', RED, 28, ma * appear(t, C['everytime']))
    return True

# --- S14 end card + comment pill ---
def s14_cta(im, t):
    if t < C['cta'] - 0.1: return False
    a = appear(t, C['cta'] - 0.1, 0.25); y = 320
    frosted(im, (40, y, 1040, y + 300), 0.84, 16); d = ImageDraw.Draw(im, 'RGBA')
    brackets(d, 40, y, 1040, y + 300, A(VGOLD, a), 40, 6)
    if GL: brackets(GL, 40, y, 1040, y + 300, A(VGOLD, a), 40, 12)
    lg = logo(170)
    if a < 1: lg.putalpha(lg.split()[3].point(lambda v: int(v * a)))
    comp(im, lg, (64, y + 24)); d = ImageDraw.Draw(im, 'RGBA')
    txt(d, 260, y + 30, 'FREE', f(MONO, 26), VGOLD, a)
    txt(d, 260, y + 62, 'CV PROTECTION STACK', f(BEB, 62), WHITE, a * appear(t, C['stack'] - 0.2))
    txt(d, 260, y + 122, '+ DOSING FRAMEWORK', f(BC8, 40), CREAM, a * appear(t, C['stack'] + 0.4))
    if t >= C['comment']:
        b = expo((t - C['comment']) / 0.12); s = lerp(1.15, 1.0, b)
        fn = f(BEB, int(86 * s)); lab = 'COMMENT  "HEALTH"'; tw = d.textlength(lab, font=fn)
        lit_bar(d, 64, y + 196, 64 + tw + 44, y + 196 + int(92 * s), VGOLD, b); d.text((86, y + 200), lab, font=fn, fill=A(INK, b))
        if GL: GL.rectangle([60, y + 192, 68 + tw + 44, y + 200 + int(92 * s)], outline=A(VGOLD, b), width=12)
    return True

# =====================================================================================
# CAPTIONS (saved style: Bebas, 3-word groups, lit red box tracks the active word)
# =====================================================================================
FIX = {'ezetimibe': 'EZETIMIBE', 'telmisartan': 'TELMISARTAN', 'apob': 'APOB'}
def build_groups():
    G = []; cur = []
    for i, x in enumerate(WORDS):
        if cur:
            prev = WORDS[cur[-1]]
            if len(cur) >= 3 or x['s'] - prev['e'] > 0.28 or prev['w'][-1] in '.,?!' or len(''.join(WORDS[j]['w'] for j in cur + [i])) > 22:
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
    nxt = [g for g in GROUPS if WORDS[g[0]]['s'] > WORDS[lo[0]]['s']]
    if t > WORDS[lo[-1]]['e'] + 0.6 and (not nxt or WORDS[nxt[0][0]]['s'] > t): return None
    return lo
CAP_Y = 1395
def captions(im, t, y=CAP_Y, base=118):
    g = group_at(t)
    if not g: return
    ws = [FIX.get(_n(WORDS[i]['w']), WORDS[i]['w'].upper().strip(',.?!')) for i in g]
    d = ImageDraw.Draw(im, 'RGBA'); size = base
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
        if k != act: sd.text((x_ + 4, 46), w_, font=fn, fill=(0, 0, 0, 220))
    cap.alpha_composite(shd.filter(ImageFilter.GaussianBlur(6)))
    lit_bar(cd, bx0, 40 + size * 0.02, bx1, 40 + size * 0.98, RED)
    for k, (w_, x_) in enumerate(zip(ws, xs)): cd.text((x_, 40), w_, font=fn, fill=CREAM, stroke_width=0 if k == act else 3, stroke_fill=(0, 0, 0))
    if abs(s - 1) > 0.002:
        cap = cap.resize((int(W * s), int(300 * s)), Image.BICUBIC); ox = int((W - cap.width) / 2); oy = int(y - 40 - (cap.height - 300) / 2)
    else: ox, oy = 0, y - 40
    comp(im, cap, (ox, oy))

# =====================================================================================
# FRAME
# =====================================================================================
def frame(src, t):
    global GL
    im, geo, m, p = compose_base(src, t)
    # light legibility scrims top/bottom over full-frame footage only (footage itself is not graded)
    if m in ('full', 'wipe') or p < 1:
        yy = np.arange(H); a_ = np.where(yy > 1300, np.clip((yy - 1300) / 220, 0, 1) * 90, 0); a_ = np.maximum(a_, np.where(yy < 560, (1 - yy / 560) * 90, 0))
        a_ = (a_ * (1 - (p if m not in ('full', 'wipe') else 0))).astype(np.uint8)
        comp(im, Image.merge('RGBA', [Image.new('L', (W, H), c) for c in NAVY] + [Image.fromarray(np.repeat(a_[:, None], W, 1))]))
    glow = Image.new('RGBA', (W, H), (0, 0, 0, 0)); GL = ImageDraw.Draw(glow, 'RGBA')
    d = ImageDraw.Draw(im, 'RGBA'); window_frame(d, geo, t, m)
    busy = False
    for fn in (s1_side, s2_hud, s4_table, s8a_hud, s9a_pill, s10_stamp, s12_chart, s13_flank):
        busy = fn(im, t) or busy
    s3_split(im, t, geo); s5_pip(im, t); s6_sbs(im, t); s8b_split(im, t, geo); s9b_drawer(im, t); s11_table(im, t)
    cta_on = s14_cta(im, t)
    topic_band(im, t, m, p, busy or cta_on)
    s7_wipe(im, t)
    text_hook(im, t)
    GL_ = GL; GL = None
    if glow.getbbox():
        sm = glow.resize((W // 4, H // 4), Image.BILINEAR)
        g1 = np.asarray(sm.filter(ImageFilter.GaussianBlur(3.5))).astype(np.float32) / 255; g2 = np.asarray(sm.filter(ImageFilter.GaussianBlur(10))).astype(np.float32) / 255
        prem = np.clip(g1[..., :3] * g1[..., 3:] * 2.3 + g2[..., :3] * g2[..., 3:] * 1.8, 0, 1)
        prem = np.asarray(Image.fromarray((prem * 255).astype(np.uint8)).resize((W, H), Image.BILINEAR)).astype(np.float32) / 255
        b = np.asarray(im.convert('RGB')).astype(np.float32) / 255
        im = Image.fromarray(((1 - (1 - b) * (1 - prem)) * 255).astype(np.uint8))
    d = ImageDraw.Draw(im, 'RGBA'); d.rectangle([0, 0, 7, H], fill=GOLD)      # signature gold rule
    m2, p2, _, _ = mode_at(t)
    in_drawer = (m2 == 'drawer' and p2 > 0.3)
    captions(im, t, y=CAP_Y if not in_drawer else 1440, base=118 if not in_drawer else 96)
    # disclaimer, static
    txt(ImageDraw.Draw(im, 'RGBA'), W / 2, 1520 if not in_drawer else 1580, 'FOR RESEARCH & EDUCATIONAL PURPOSES ONLY', f(MONO, 20), (190, 190, 196), 0.75, anchor='ma')
    return im

if __name__ == '__main__':
    mode = sys.argv[2]
    if mode == 'stills':
        import os; os.makedirs(S + 'qc', exist_ok=True)
        for tt in [float(x) for x in sys.argv[3:]]:
            subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', f'{tt:.3f}', '-i', S + 'assembled.mov', '-frames:v', '1', S + 'qc/_src.png'])
            frame(Image.open(S + 'qc/_src.png').convert('RGB'), tt).resize((540, 960), Image.LANCZOS).save(S + f'qc/st_{tt:07.2f}.jpg', quality=85)
        sys.exit()
    n0, n1 = int(sys.argv[2]), int(sys.argv[3]); out = sys.argv[4]
    dec = subprocess.Popen(['ffmpeg', '-v', 'error', '-ss', f'{n0 / FPS:.4f}', '-i', S + 'assembled.mov', '-frames:v', str(n1 - n0), '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], stdout=subprocess.PIPE)
    enc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-crf', '14', '-preset', 'medium', '-pix_fmt', 'yuv420p', out], stdin=subprocess.PIPE)
    for n in range(n0, n1):
        buf = dec.stdout.read(W * H * 3)
        if len(buf) < W * H * 3: print('short', n); break
        enc.stdin.write(frame(Image.frombuffer('RGB', (W, H), buf), n / FPS).tobytes())
    enc.stdin.close(); enc.wait(); dec.kill(); print('done', n0, n1)
