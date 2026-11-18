# Full test 02 (toned-down overlay plan), 1080x1920 30 fps
# usage: python3 render.py <scratch_dir> <chunk> <n_chunks>
# scratch_dir holds src/src.mov, f/ (stand-in fonts), words.json (source-time words), logo.jpg
import json, subprocess, sys, math
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

S = sys.argv[1]; CH = int(sys.argv[2]); NCH = int(sys.argv[3]); F = S + '/f/'
W, H, FPS = 1080, 1920, 30
KEEP = [(0, 406), (412, 1994), (2006, 2418)]          # source frame ranges kept
SRC = [i for a, b in KEEP for i in range(a, b)]
CUTS = [412, 2006]
WORDS = json.load(open(S + '/words.json'))

GOLD=(201,169,110); CREAM=(244,241,234); MUTED=(184,184,188); LBL=(124,124,130)
RED=(255,34,28); VGOLD=(255,194,26); CYAN=(0,229,255); GREEN=(30,255,110)
DEEP=(2,3,8); BG=(5,8,16); INK=(6,8,14); WHITE=(255,255,255)
BEB='BebasNeue.ttf'; MONO='JBMono-500.ttf'; MONOB='JBMono-800.ttf'; DMX='DMSans-900.ttf'; DMB='DMSans-700.ttf'
_fc = {}
def f(n, s):
    k = (n, int(s))
    if k not in _fc: _fc[k] = ImageFont.truetype(F + n, int(s))
    return _fc[k]
def clamp(x, a=0, b=1): return max(a, min(b, x))
def expo(x): x = clamp(x); return 1 if x >= 1 else 1 - 2**(-10*x)
def ease_io(x): x = clamp(x); return 4*x**3 if x < .5 else 1-(-2*x+2)**3/2
def lerp(a, b, t): return a + (b-a)*t
def A(c, a): return tuple(c[:3]) + (int(clamp(a)*255),)
def appear(t, t0, d=0.16): return expo((t-t0)/d)
def window(t, t0, t1, i=0.18, o=0.16): return min(expo((t-t0)/i), 1-clamp((t-t1)/o))
GL = None

def txt(d, x, y, s, font, col, a=1.0, anchor=None):
    if a > 0: d.text((x, y), s, font=font, fill=A(col, a), anchor=anchor)
def lit_bar(d, x0, y0, x1, y1, col, a=1.0):
    if x1 <= x0 or a <= 0: return
    h = max(1, int(y1-y0))
    for i in range(h):
        k = i/h; c = tuple(int(min(255, v*(1.18-0.36*k)+(40 if k < 0.12 else 0))) for v in col)
        d.line([(x0, y0+i), (x1, y0+i)], fill=c+(int(255*a),))
def tag(d, x, y, label, col=RED, size=30, a=1.0, anchor='l'):
    if a <= 0: return x
    fn = f(MONOB, size); tw = d.textlength(label, font=fn); h = size+18
    if anchor == 'c': x -= (tw+28)/2
    if anchor == 'r': x -= tw+28
    lit_bar(d, x, y, x+tw+28, y+h, col, a)
    d.text((x+14, y+6), label, font=fn, fill=A(INK if col in (VGOLD, GREEN, CYAN) else WHITE, a))
    if GL: GL.rectangle([x-4, y-4, x+tw+32, y+h+4], outline=A(col, a), width=8)
    return x+tw+28
def glass(im, box, dark=0.82, blur=16):
    x0, y0, x1, y1 = [int(round(v)) for v in box]; x0=max(0,x0); y0=max(0,y0); x1=min(W,x1); y1=min(H,y1)
    if x1 <= x0 or y1 <= y0: return
    reg = im.crop((x0, y0, x1, y1)).convert('RGB').filter(ImageFilter.GaussianBlur(blur))
    im.paste(Image.blend(reg, Image.new('RGB', reg.size, DEEP), dark).convert('RGBA'), (x0, y0))
def kicker(d, x, y, label, col, a, t, t0):
    p = expo((t-t0)/0.22)
    d.line([(x, y+15), (x+46*p, y+15)], fill=A(col, a), width=4)
    if p > 0.4: txt(d, x+60, y, label, f(MONOB, 26), col, a*clamp((p-0.4)/0.6))
def cross(d, x, y, col, s=1.0, a=1.0):
    if a <= 0: return
    for p in ([(x, y), (x+28*s, y+28*s)], [(x+28*s, y), (x, y+28*s)]):
        d.line(p, fill=A(col, a), width=int(7*s))
        if GL: GL.line(p, fill=A(col, a), width=int(13*s))
def check(d, x, y, col, s=1.0, a=1.0):
    if a <= 0: return
    p = [(x, y+16*s), (x+10*s, y+28*s), (x+30*s, y+2*s)]
    d.line(p, fill=A(col, a), width=int(7*s))
    if GL: GL.line(p, fill=A(col, a), width=int(13*s))

def make_bg():
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    g = np.exp(-(((xx-900)/700)**2 + ((yy-150)/600)**2))
    b = np.zeros((H, W, 3), np.float32) + np.array(BG, np.float32) + g[..., None]*np.array([26, 19, 8], np.float32)
    b += (((yy.astype(int) % 6) < 1).astype(np.float32)*3)[..., None]
    return Image.fromarray(np.clip(b, 0, 255).astype(np.uint8)).convert('RGBA')
BGIM = make_bg()

# ---------------- layouts ----------------
L_FULL = dict(oy=0, m0=0, m1=H, cy=1400)
L_SPLIT = dict(oy=360, m0=880, m1=H, cy=806)        # graphic on top, footage pushed down (face intact)
L_INV = dict(oy=-430, m0=0, m1=1060, cy=1000)       # footage pushed up, dashboard below
KEYS = [(0.0, L_FULL), (56.20, L_SPLIT), (64.40, L_INV), (72.40, L_FULL)]
def layout_at(ts):
    cur = KEYS[0][1]
    for i, (k, l) in enumerate(KEYS):
        if ts >= k:
            prev = KEYS[i-1][1] if i else l; p = ease_io((ts-k)/0.36)
            cur = {key: lerp(prev[key], l[key], p) for key in l}
    return cur
PUNCH = [(0.54, 1.06), (6.70, 1.0), (13.80, 1.10), (24.48, 1.0), (34.94, 1.07), (40.98, 1.0), (45.18, 1.06), (50.46, 1.0), (55.40, 1.13), (56.20, 1.0), (72.52, 1.06), (76.72, 1.0)]
def punch_at(ts):
    z = 1.0; zp = 1.0
    for k, v in PUNCH:
        if ts >= k: z = lerp(zp, v, expo((ts-k)/0.12)); zp = v
    return z

# ---------------- captions ----------------
ACC = {'ANAVAR': VGOLD, 'ANADROL': VGOLD, 'DIET': VGOLD, 'FOOD': VGOLD, 'WRONG': RED, 'WATER': CYAN, 'SODIUM': CYAN, 'ESTROGEN': RED, 'ORALS': VGOLD, 'BLOATED': RED, 'SURPLUS': VGOLD, 'DEFICIT': VGOLD}
def cw(w): return w.upper().strip(',.?!')
def groups():
    G = []; cur = []
    for i, x in enumerate(WORDS):
        if cur:
            pv = WORDS[cur[-1]]
            brk = len(cur) >= 3 or x['s']-pv['e'] > 0.28 or pv['w'][-1] in '.,?!'
            if any(pv['s']*30 < c <= x['s']*30+3 for c in CUTS): brk = True
            if brk: G.append(cur); cur = []
        cur.append(i)
    if cur: G.append(cur)
    return G
GROUPS = groups()
def group_at(ts):
    lo = None
    for g in GROUPS:
        if WORDS[g[0]]['s'] <= ts+1e-6: lo = g
        else: break
    if lo is None: return None
    nxt = [g for g in GROUPS if WORDS[g[0]]['s'] > WORDS[lo[0]]['s']]
    if ts > WORDS[lo[-1]]['e']+0.5 and (not nxt or WORDS[nxt[0][0]]['s'] > ts): return None
    return lo
def captions(im, ts, cy):
    g = group_at(ts)
    if not g: return
    d = ImageDraw.Draw(im, 'RGBA'); ws = [cw(WORDS[i]['w']) for i in g]; size = 112
    while True:
        fn = f(BEB, size); sp = d.textlength(' ', font=fn)+14; wd = [d.textlength(w, font=fn) for w in ws]; tot = sum(wd)+sp*(len(ws)-1)
        if tot <= 880: break
        size -= 4
    xs = []; x = (W-tot)/2-30
    for w_ in wd: xs.append(x); x += w_+sp
    act = max([k for k, i in enumerate(g) if WORDS[i]['s'] <= ts] or [0])
    sc = lerp(0.9, 1, expo((ts-WORDS[g[0]]['s'])/0.10)); CHh = 260
    cap = Image.new('RGBA', (W, CHh), (0,0,0,0)); cd = ImageDraw.Draw(cap); shd = Image.new('RGBA', (W, CHh), (0,0,0,0)); sd = ImageDraw.Draw(shd)
    pv = max(0, act-1); bt = expo((ts-WORDS[g[act]]['s'])/0.07) if act else 1
    bx0 = lerp(xs[pv], xs[act], bt)-16; bx1 = lerp(xs[pv]+wd[pv], xs[act]+wd[act], bt)+16
    for w_, x_ in zip(ws, xs): sd.text((x_+4, 46), w_, font=fn, fill=(0,0,0,230))
    cap.alpha_composite(shd.filter(ImageFilter.GaussianBlur(7)))
    lit_bar(cd, bx0, 40+size*0.02, bx1, 40+size*0.98, RED)
    for k, (w_, x_) in enumerate(zip(ws, xs)):
        col = ACC.get(w_, CREAM) if (k != act and WORDS[g[k]]['s'] <= ts) else CREAM
        cd.text((x_, 40), w_, font=fn, fill=col, stroke_width=0 if k == act else 3, stroke_fill=(0,0,0))
    if abs(sc-1) > 0.002:
        cap = cap.resize((int(W*sc), int(CHh*sc)), Image.BICUBIC); ox = int((W-cap.width)/2); oy = int(cy-40-(cap.height-CHh)/2)
    else: ox, oy = 0, int(cy-40)
    im.alpha_composite(cap, (ox, oy))

# ================= overlays (source seconds) =================
HOOK_END = 6.0
def text_hook(im, ts):                     # TEXT_HOOK_ENGINE winner, native mode, frame 0
    if ts >= HOOK_END+0.15: return
    a = 1-clamp((ts-HOOK_END)/0.15); s = lerp(1.0, 1.04, clamp(ts/HOOK_END))
    lay = Image.new('RGBA', (W, 420), (0,0,0,0)); d = ImageDraw.Draw(lay)
    def line(parts, y, size):
        while True:
            fn = f(DMX, size); tw = sum(d.textlength(p, font=fn) for p, _ in parts)
            if tw <= 840: break
            size -= 2
        x = 60 + (880-tw)/2
        for p, c in parts: d.text((x, y), p, font=fn, fill=c+(255,), stroke_width=4, stroke_fill=(0,0,0,255)); x += d.textlength(p, font=fn)
    line([('ANAVAR', VGOLD), (' vs ', WHITE), ('ANADROL', VGOLD)], 60, 90); line([('What most guys get wrong', WHITE)], 170, 66)
    sh = Image.new('RGBA', lay.size, (0,0,0,0)); sh.putalpha(lay.split()[3].filter(ImageFilter.GaussianBlur(14)).point(lambda v: int(v*0.8)))
    out = Image.new('RGBA', lay.size, (0,0,0,0)); out.alpha_composite(sh, (0, 6)); out.alpha_composite(lay)
    if abs(s-1) > 1e-3: out = out.resize((int(W*s), int(420*s)), Image.BICUBIC)
    if a < 1: out.putalpha(out.split()[3].point(lambda v: int(v*a)))
    im.alpha_composite(out, (int((W-out.width)/2), int(250-(out.height-420)/2)))

def topic_band(d, ts):                     # after the hook, until the midpoint (40.3 s)
    a = window(ts, HOOK_END+0.15, 40.10, 0.15, 0.15)
    if a <= 0: return
    fn = f(DMX, 46); parts = [('ANAVAR', VGOLD), (' vs ', WHITE), ('ANADROL', VGOLD)]
    tw = sum(d.textlength(p, font=fn) for p, _ in parts); x = (W-tw)/2-40
    d.rounded_rectangle([x-24, 262, x+tw+24, 330], radius=14, fill=A(DEEP, 0.78*a), outline=A(VGOLD, 0.55*a), width=2)
    for p, c in parts: txt(d, x, 266, p, fn, c, a); x += d.textlength(p, font=fn)

# chapter tags: heavy gold block slides from the left edge, mono label follows
CHAPTERS = [(13.80, 18.4, '01', 'THE MISTAKE'), (24.48, 29.0, '02', 'THE LOOK'), (34.94, 39.6, '03', 'THE CLAIM'), (45.18, 49.6, '04', 'THE PROOF')]
def chapter(d, ts):
    for t0, t1, n, lab in CHAPTERS:
        a = window(ts, t0, t1, 0.2, 0.18)
        if a <= 0: continue
        x = lerp(-260, 0, expo((ts-t0)/0.22)); y = 372
        lit_bar(d, x, y, x+132, y+92, VGOLD, a); txt(d, x+66, y+46, n, f(BEB, 84), INK, a, 'mm')
        if GL: GL.rectangle([x, y-4, x+136, y+96], outline=A(VGOLD, a), width=8)
        q = a*appear(ts, t0+0.12, 0.2)
        d.rectangle([x+132, y, x+132+lerp(0, 330, q), y+92], fill=A(DEEP, 0.82*q))
        txt(d, x+156, y+18, 'CHAPTER', f(MONO, 22), LBL, q); txt(d, x+156, y+42, lab, f(BEB, 50), CREAM, q)

# VS slam -> "wrong question" strike (kinetic type over full footage)
def vs_slam(im, ts):
    a = window(ts, 52.60, 56.30, 0.12, 0.16)
    if a <= 0: return
    d = ImageDraw.Draw(im, 'RGBA'); y = 410
    p = expo((ts-52.66)/0.20)
    fn = f(BEB, 132)
    xl = lerp(-520, 70, p); xr = lerp(W+520, 1010, p)
    for (x, s, anc) in [(xl, 'ANAVAR', 'la'), (xr, 'ANADROL', 'ra')]:
        d.text((x+6, y+8), s, font=fn, fill=(0,0,0,int(200*a)), anchor=anc)
        d.text((x, y), s, font=fn, fill=A(VGOLD, a), anchor=anc, stroke_width=3, stroke_fill=(0,0,0))
    if p > 0.6:
        q = expo((ts-52.86)/0.12); r = lerp(110, 62, q); cx, cy = 540, y+70
        dm = [(cx, cy-r), (cx+r, cy), (cx, cy+r), (cx-r, cy)]
        d.polygon(dm, fill=A(RED, a)); txt(d, cx, cy+2, 'VS', f(BEB, 62), WHITE, a, 'mm')
        if GL: GL.polygon(dm, outline=A(RED, a), width=12)
    if ts >= 53.26 and ts < 55.40: txt(d, 540, y+170, '?', f(BEB, 150), WHITE, a*appear(ts, 53.26), 'ma')
    if ts >= 55.40:
        q = expo((ts-55.40)/0.14)
        x0, y0, x1, y1 = 50, y+150, 1030, y-10
        d.line([(x0, y0), (lerp(x0, x1, q), lerp(y0, y1, q))], fill=A(RED, a), width=14)
        if GL: GL.line([(x0, y0), (lerp(x0, x1, q), lerp(y0, y1, q))], fill=A(RED, a), width=24)
    if ts >= 55.84:
        s_ = lerp(1.3, 1.0, expo((ts-55.84)/0.12))
        tag(d, 540, y+190, 'WRONG QUESTION', RED, int(44*s_), a, anchor='c')

# DIET SWITCHBOARD (split layout, graphic on top): calories decide, the compound doesn't flip the result
def switchboard(im, ts):
    a = window(ts, 56.30, 64.50, 0.25, 0.16)
    if a <= 0: return
    lay = Image.new('RGBA', (W, 880), (0,0,0,0)); d = ImageDraw.Draw(lay)
    d.rectangle([0, 262, 6, 860], fill=A(GOLD, 1))
    kicker(d, 40, 272, 'WHAT ACTUALLY DECIDES IT', VGOLD, 1, ts, 56.40)
    txt(d, 1000, 272, 'DIET  >  COMPOUND', f(MONO, 24), LBL, 1, 'ra')
    food_on = ts >= 63.18
    rows = [('SURPLUS', 'MASS', 57.62, 58.50), ('DEFICIT', 'FAT LOSS', 59.32, 60.10)]
    for i, (sw, res, t_sw, t_res) in enumerate(rows):
        y = 330+i*150; ra = appear(ts, t_sw, 0.2)
        if ra <= 0: continue
        d.rounded_rectangle([40, y, 1040, y+140], radius=18, fill=(10,13,22,235), outline=A((70,64,52), ra), width=2)
        txt(d, 70, y+16, 'CALORIES', f(MONO, 22), LBL, ra); txt(d, 70, y+46, sw, f(BEB, 66), CREAM, ra)
        # toggle
        on = expo((ts-63.18-i*0.12)/0.18) if food_on else 0
        tx = 330; d.rounded_rectangle([tx, y+42, tx+120, y+100], radius=29, fill=A(lerp_col((60,60,70), VGOLD, on), ra))
        kx = lerp(tx+29, tx+91, on); d.ellipse([kx-23, y+48, kx+23, y+94], fill=A(WHITE, ra))
        if GL and on > 0: GL.rounded_rectangle([tx, y+42, tx+120, y+100], radius=29, outline=A(VGOLD, on), width=10)
        txt(d, tx+60, y+108, 'ON' if on > 0.5 else 'OFF', f(MONOB, 20), VGOLD if on > 0.5 else RED, ra, 'ma')
        # arrow + result meter
        d.line([(480, y+71), (560, y+71)], fill=A(MUTED, ra), width=4); d.polygon([(560, y+61), (576, y+71), (560, y+81)], fill=A(MUTED, ra))
        txt(d, 600, y+16, res, f(BEB, 48), CREAM, appear(ts, t_res))
        mx0, mx1 = 600, 1010; d.rectangle([mx0, y+76, mx1, y+112], outline=A((80,84,100), ra), width=2)
        fill = 0.04 + (0.03 if ts >= 61.44 else 0) + 0.88*on
        lit_bar(d, mx0+3, y+79, mx0+3+(mx1-mx0-6)*fill, y+109, VGOLD if on > 0.5 else RED, ra)
        if ts >= t_res and on < 0.5: cross(d, 960, y+22, RED, 1.2, appear(ts, t_res))
        if on > 0.5: check(d, 958, y+20, GREEN, 1.2, on)
    # compound chip plugs in and barely moves anything
    if ts >= 61.44:
        q = expo((ts-61.44)/0.22); y = 632
        d.rounded_rectangle([40, y, 1040, y+130], radius=18, fill=(10,13,22,int(235*q)), outline=A(CYAN, q*0.7), width=2)
        y -= 4
        x = lerp(-300, 70, q)
        lit_bar(d, x, y+30, x+300, y+100, CYAN, q); txt(d, x+150, y+65, 'COMPOUND', f(BEB, 56), INK, q, 'mm')
        if ts >= 61.84: txt(d, 420, y+28, 'SHAPES THE LOOK', f(BEB, 52), CYAN, appear(ts, 61.84))
        if ts >= 63.18: txt(d, 420, y+80, 'FOOD DECIDES THE RESULT', f(MONOB, 28), VGOLD, appear(ts, 63.44))
    lay.putalpha(lay.split()[3].point(lambda v: int(v*a)))
    im.alpha_composite(lay)
def lerp_col(a, b, t): return tuple(int(lerp(x, y, t)) for x, y in zip(a, b))

# BLOAT DASHBOARD (inverse split, footage pushed up): three dials swing into the red on the spoken word
def dashboard(im, ts):
    a = window(ts, 64.50, 72.50, 0.25, 0.16)
    if a <= 0: return
    d = ImageDraw.Draw(im, 'RGBA'); top = 1060
    d.rectangle([0, top, 6, 1500], fill=A(GOLD, a))
    d.line([(0, top), (W, top)], fill=A(VGOLD, a), width=3)
    if GL: GL.line([(0, top), (W, top)], fill=A(VGOLD, a), width=8)
    kicker(d, 40, top+110, 'THE BLOAT DASHBOARD', VGOLD, a, ts, 64.6)
    dials = [('ESTROGEN', 67.88, 70.16, RED), ('WATER', 64.94, 70.92, CYAN), ('SODIUM', 65.74, 72.08, CYAN)]
    for i, (nm, t_in, t_hi, col) in enumerate(dials):
        da = a*appear(ts, t_in, 0.22)
        if da <= 0: continue
        cx = 190+i*350; cy = top+390; r = 140
        for k in range(30):        # arc ticks green -> amber -> red
            ang = math.pi + math.pi*k/29; zc = GREEN if k < 12 else ((240,160,48) if k < 20 else RED)
            x0 = cx+(r-24)*math.cos(ang); y0 = cy+(r-24)*math.sin(ang); x1 = cx+r*math.cos(ang); y1 = cy+r*math.sin(ang)
            d.line([(x0, y0), (x1, y1)], fill=A(zc, da*0.9), width=6)
        v = 0.30 + 0.05*math.sin(ts*3+i)
        if ts >= 68.74: v = lerp(v, 0.55, expo((ts-68.74)/0.6))
        if ts >= t_hi: v = lerp(0.55, 0.93, expo((ts-t_hi)/0.25))
        ang = math.pi + math.pi*v
        nx = cx+(r-34)*math.cos(ang); ny = cy+(r-34)*math.sin(ang)
        d.line([(cx, cy), (nx, ny)], fill=A(WHITE, da), width=7); d.ellipse([cx-14, cy-14, cx+14, cy+14], fill=A(WHITE, da))
        if GL: GL.line([(cx, cy), (nx, ny)], fill=A(col, da), width=12)
        txt(d, cx, cy+28, nm, f(BEB, 52), CREAM, da, 'ma')
        if ts >= t_hi: tag(d, cx, cy-r-58, 'HIGH', RED, 26, appear(ts, t_hi), anchor='c')
    if ts >= 69.10: txt(d, 1040, top+112, 'BLOATED = THESE THREE', f(MONOB, 24), RED, a*appear(ts, 69.10), 'ra')

# CTA end card (top zone over full footage) + delivery notification
LOGO = None
def cta(im, ts):
    global LOGO
    a = window(ts, 73.66, 99, 0.22)
    if a <= 0: return
    x0, y0, x1, y1 = 40, 262, 1000, 640
    glass(im, (x0, y0, x1, y1), 0.84, 16); d = ImageDraw.Draw(im, 'RGBA')
    d.rectangle([x0, y0, x0+6, y1], fill=A(GOLD, a)); d.rectangle([x0, y0, x1, y1], outline=A((70,64,52), a), width=2)
    if LOGO is None:
        lg = Image.open(S+'/logo.jpg').convert('RGB'); s = min(lg.size)
        lg = lg.crop(((lg.width-s)//2, (lg.height-s)//2, (lg.width+s)//2, (lg.height+s)//2)).resize((150, 150), Image.LANCZOS)
        m = Image.new('L', (150, 150), 0); ImageDraw.Draw(m).ellipse([0, 0, 149, 149], fill=255); lg.putalpha(m); LOGO = lg
    lg = LOGO.copy(); lg.putalpha(lg.split()[3].point(lambda v: int(v*a))); im.alpha_composite(lg, (x0+30, y0+30)); d = ImageDraw.Draw(im, 'RGBA')
    txt(d, x0+210, y0+36, 'FREE', f(MONOB, 26), VGOLD, a)
    items = [('ORALS FULL BREAKDOWN', 73.90), ('LIVER HEALTH STACK', 74.94)]
    for i, (lab, tt) in enumerate(items):
        q = a*appear(ts, tt); y = y0+76+i*52
        check(d, x0+210, y, GREEN, 1.0, q); txt(d, x0+256, y-4, lab, f(BEB, 46), CREAM, q)
    if ts >= 76.72:
        b = expo((ts-76.72)/0.14); s_ = lerp(1.12, 1.0, b); fn = f(BEB, int(96*s_)); lab = 'COMMENT  "ORALS"'
        tw = d.textlength(lab, font=fn); xx = (x0+x1)/2-tw/2-24; yy = y0+210
        lit_bar(d, xx, yy, xx+tw+48, yy+int(118*s_), VGOLD, b*a); d.text((xx+24, yy+10), lab, font=fn, fill=A(INK, b*a))
        if GL: GL.rectangle([xx-4, yy-4, xx+tw+52, yy+int(118*s_)+4], outline=A(VGOLD, b*a), width=12)
    # delivery notification drops in on "I'll send it"
    if ts >= 78.66:
        q = expo((ts-78.66)/0.25)
        y = lerp(560, 662, q); bx0, bx1 = 140, 940
        glass(im, (bx0, y, bx1, y+104), 0.75*q, 18); d = ImageDraw.Draw(im, 'RGBA')
        d.rounded_rectangle([bx0, y, bx1, y+104], radius=26, outline=A(VGOLD, 0.7*q), width=2)
        d.ellipse([bx0+20, y+22, bx0+80, y+82], fill=A(VGOLD, q)); txt(d, bx0+50, y+52, 'A', f(BEB, 44), INK, q, 'mm')
        txt(d, bx0+100, y+16, '@coach.agz', f(MONOB, 24), VGOLD, q); txt(d, bx0+100, y+50, 'sent you: ORALS breakdown', f(DMB, 32), WHITE, q)

def disclaimer(d, ts, lay):
    if ts < HOOK_END or lay['m0'] > 1 or lay['m1'] < 1900: return
    txt(d, 540, 1548, 'FOR RESEARCH & EDUCATIONAL PURPOSES ONLY', f(MONO, 20), MUTED, 0.6, 'ma')

# ---------------- frame ----------------
def frame(src, ts):
    global GL
    lay = layout_at(ts); z = punch_at(ts)
    if lay['oy'] != 0: z = 1.0 + (z-1.0)*(1-min(1, abs(lay['oy'])/120))
    if abs(z-1) > 1e-3:
        big = src.resize((int(W*z), int(H*z)), Image.BICUBIC); ox = (big.width-W)//2; oy = int((big.height-H)*(930/H)); src = big.crop((ox, oy, ox+W, oy+H))
    im = BGIM.copy()
    oy = int(round(lay['oy'])); m0 = int(round(lay['m0'])); m1 = int(round(lay['m1']))
    # paste the footage region that falls inside the mask (no resize: face stays 1:1)
    sy0 = max(0, m0-oy); sy1 = min(H, m1-oy)
    if sy1 > sy0: im.paste(src.crop((0, sy0, W, sy1)).convert('RGBA'), (0, sy0+oy))
    # soft dark seam on the footage edge in split modes
    d = ImageDraw.Draw(im, 'RGBA')
    glow = Image.new('RGBA', (W, H), (0,0,0,0)); GL = ImageDraw.Draw(glow, 'RGBA')
    if m0 > 0: d.line([(0, m0), (W, m0)], fill=A(VGOLD, 0.9), width=3); GL.line([(0, m0), (W, m0)], fill=A(VGOLD, 0.9), width=8)
    # top/bottom legibility gradients (graphics zones only, footage colour untouched elsewhere)
    text_hook(im, ts)
    d = ImageDraw.Draw(im, 'RGBA')
    topic_band(d, ts); chapter(d, ts); vs_slam(im, ts)
    switchboard(im, ts); dashboard(im, ts); cta(im, ts)
    d = ImageDraw.Draw(im, 'RGBA'); disclaimer(d, ts, lay)
    moving = any(k > 0 and k <= ts < k+0.36 for k, _ in KEYS)   # captions hide while the layout moves
    if not moving: captions(im, ts, lay['cy'])
    GL = None
    if glow.getbbox():
        sm = glow.resize((W//4, H//4), Image.BILINEAR)
        g1 = np.asarray(sm.filter(ImageFilter.GaussianBlur(3.5))).astype(np.float32)/255; g2 = np.asarray(sm.filter(ImageFilter.GaussianBlur(10))).astype(np.float32)/255
        pr = np.clip(g1[..., :3]*g1[..., 3:]*2.3+g2[..., :3]*g2[..., 3:]*1.8, 0, 1)
        pr = np.asarray(Image.fromarray((pr*255).astype(np.uint8)).resize((W, H), Image.BILINEAR)).astype(np.float32)/255
        b = np.asarray(im.convert('RGB')).astype(np.float32)/255
        return Image.fromarray(((1-(1-b)*(1-pr))*255).astype(np.uint8))
    return im.convert('RGB')

if __name__ == '__main__':
    n = len(SRC); per = (n+NCH-1)//NCH; o0 = CH*per; o1 = min(n, o0+per)
    s_first = SRC[o0]
    dec = subprocess.Popen(['ffmpeg', '-v', 'error', '-ss', f'{s_first/30:.4f}', '-i', S+'/src/src.mov', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], stdout=subprocess.PIPE)
    enc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', '30', '-i', '-',
                            '-c:v', 'libx264', '-preset', 'medium', '-crf', '14', '-pix_fmt', 'yuv420p', f'{S}/chunk_{CH:02d}.mp4'], stdin=subprocess.PIPE)
    cur = s_first-1; fr = None
    for k in range(o0, o1):
        want = SRC[k]
        while cur < want:
            buf = dec.stdout.read(W*H*3)
            if len(buf) < W*H*3: break
            fr = buf; cur += 1
        img = Image.frombuffer('RGB', (W, H), fr)
        enc.stdin.write(frame(img, want/30).tobytes())
    enc.stdin.close(); enc.wait(); dec.kill()
    print('chunk', CH, 'done', o1-o0)
