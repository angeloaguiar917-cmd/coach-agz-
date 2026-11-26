# EQ-overrated renderer — core: constants, primitives, captions, furniture.
import json, math, os
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

WD = os.path.dirname(os.path.abspath(__file__))
F = WD + '/fonts/'
W, H = 1080, 1920; FPS = 30
CUTS = [407/30, 869/30, 2031/30]
N_FRAMES = 2606

GOLD=(201,169,110); CREAM=(244,241,234); NAVY=(14,17,23); MUTED=(184,184,188)
RED=(255,34,28); VGOLD=(255,194,26); CYAN=(0,229,255); GREEN=(30,255,110); AMBER=(240,160,48)
DEEP=(2,3,8); INK=(6,8,14); WHITE=(255,255,255)
BEB='BEB.woff'; BAR='BAR7.woff'; DMR='DMR.woff'; DMB='DMB.woff'; MONO='MONO.ttf'
_fc={}
def f(n,s):
    k=(n,int(s))
    if k not in _fc: _fc[k]=ImageFont.truetype(F+n,int(s))
    return _fc[k]
def clamp(x,a=0,b=1): return max(a,min(b,x))
def expo(x): x=clamp(x); return 1 if x>=1 else 1-2**(-10*x)
def ease(x): x=clamp(x); return 4*x**3 if x<.5 else 1-(-2*x+2)**3/2
def land(x):            # heavy settle, no cartoon bounce
    x=clamp(x); return 1-(1-x)**3*(1+2.0*x)
def lerp(a,b,t): return a+(b-a)*t
def A(c,a): return tuple(c[:3])+(int(clamp(a)*255),)
def ap(t,t0,d=0.16): return expo((t-t0)/d)
def win(t,t0,t1,fi=0.18,fo=0.16):
    if t<t0 or t>t1+fo: return 0.0
    out=1.0 if fo<=0 else 1-clamp((t-t1)/fo)
    return min(expo((t-t0)/fi), out)
GL=None

def line(d,pts,col,w=4,a=1.0):
    d.line(pts,fill=A(col,a),width=w)
def brackets(d,x0,y0,x1,y1,col,L=32,w=4,a=1.0):
    for cx,cy,sx,sy in [(x0,y0,1,1),(x1,y0,-1,1),(x0,y1,1,-1),(x1,y1,-1,-1)]:
        d.line([(cx,cy),(cx+sx*L,cy)],fill=A(col,a),width=w); d.line([(cx,cy),(cx,cy+sy*L)],fill=A(col,a),width=w)
def litbar(d,x0,y0,x1,y1,col,a=1.0):
    h=max(1,int(y1-y0))
    for i in range(h):
        k=i/h; c=tuple(int(min(255,v*(1.18-0.36*k)+(42 if k<0.12 else 0))) for v in col)
        d.line([(x0,y0+i),(x1,y0+i)],fill=c+(int(255*a),))
def txt(d,x,y,s,fo,col,a=1.0,anc=None):
    d.text((x,y),s,font=fo,fill=A(col,a),anchor=anc)
def stxt(d,x,y,s,fo,col,a=1.0,anc=None,sw=3):
    d.text((x,y),s,font=fo,fill=A(col,a),anchor=anc,stroke_width=sw,stroke_fill=A((0,0,0),a*0.85))
def tag(d,x,y,label,col=RED,size=30,a=1.0,glow=True,fo=MONO):
    fn=f(fo,size); tw=d.textlength(label,font=fn); h=size+16
    litbar(d,x,y,x+tw+24,y+h,col,a)
    d.text((x+12,y+(5 if fo==MONO else 9)),label,font=fn,fill=A(WHITE if col not in (VGOLD,GREEN,CYAN) else INK,a))
    if GL and glow: GL.rectangle([x-4,y-4,x+tw+28,y+h+4],outline=A(col,a),width=8)
    return x+tw+24
def check(d,x,y,col,s=1.0,a=1.0):
    p=[(x,y+16*s),(x+10*s,y+28*s),(x+30*s,y+2*s)]; d.line(p,fill=A(col,a),width=int(6*s))
    if GL: GL.line(p,fill=A(col,a),width=int(12*s))
def cross(d,x,y,col,s=1.0,a=1.0):
    d.line([(x,y),(x+28*s,y+28*s)],fill=A(col,a),width=int(6*s)); d.line([(x+28*s,y),(x,y+28*s)],fill=A(col,a),width=int(6*s))
    if GL: GL.line([(x,y),(x+28*s,y+28*s)],fill=A(col,a),width=12); GL.line([(x+28*s,y),(x,y+28*s)],fill=A(col,a),width=12)
def arrow(d,x0,y0,x1,y1,col,w=5,a=1.0,L=18):
    d.line([(x0,y0),(x1,y1)],fill=A(col,a),width=w); ang=math.atan2(y1-y0,x1-x0)
    d.polygon([(x1,y1),(x1-L*math.cos(ang-0.45),y1-L*math.sin(ang-0.45)),(x1-L*math.cos(ang+0.45),y1-L*math.sin(ang+0.45))],fill=A(col,a))
def frosted(im,box,dark=0.86,blur=12):
    x0,y0,x1,y1=[int(v) for v in box]; x0=max(0,x0);y0=max(0,y0);x1=min(W,x1);y1=min(H,y1)
    if x1<=x0 or y1<=y0: return
    reg=im.crop((x0,y0,x1,y1)).convert('RGB').filter(ImageFilter.GaussianBlur(blur))
    im.paste(Image.blend(reg,Image.new('RGB',reg.size,DEEP),dark).convert('RGBA'),(x0,y0))
def shade(im,box,a=0.55,r=60):
    x0,y0,x1,y1=[int(v) for v in box]
    m=Image.new('L',(W,H),0); ImageDraw.Draw(m).rounded_rectangle([x0,y0,x1,y1],radius=r,fill=int(255*a))
    m=m.filter(ImageFilter.GaussianBlur(r*0.6))
    im.alpha_composite(Image.merge('RGBA',[Image.new('L',(W,H),c) for c in DEEP]+[m]))

# ---- captions (word-synced, phone-safe, accent recolour) ----
WORDS=json.load(open(WD+'/cut_words.json'))
FIX={'eq':'EQ','e2':'E2',"i'll":"I'LL",'biomarkers':'BIOMARKERS'}
ACC_GOLD={'EQ','E2','ESTROGEN','HEMATOCRIT','PROTOCOL','BIOMARKERS','VASCULARITY'}
ACC_RED={'OVERRATED','THICK','CRASHED','STUCK','PROBLEM','TERRIBLE','OVERTIME'}
def _groups():
    G=[];cur=[]
    for i,x in enumerate(WORDS):
        if cur:
            pv=WORDS[cur[-1]]
            if len(cur)>=3 or x['s']-pv['e']>0.28 or pv['w'][-1] in '.,?!' or any(pv['e']<=c+0.01<=x['s']+0.05 for c in CUTS):
                G.append(cur);cur=[]
        cur.append(i)
    if cur: G.append(cur)
    return G
GROUPS=_groups()
def group_at(t):
    lo=None
    for g in GROUPS:
        if WORDS[g[0]]['s']<=t+1e-6: lo=g
        else: break
    if lo is None: return None
    end=WORDS[lo[-1]]['e']+0.55
    nxt=[g for g in GROUPS if WORDS[g[0]]['s']>WORDS[lo[0]]['s']]
    if t>end and (not nxt or WORDS[nxt[0][0]]['s']>t): return None
    return lo
def wtxt(i):
    w=WORDS[i]['w'].strip(); core=w.lower().strip('.,?!')
    return FIX.get(core,w.upper().rstrip(',.?!'))
CAP_Y=1560
def captions(im,t):
    g=group_at(t)
    if not g: return
    d=ImageDraw.Draw(im,'RGBA'); ws=[wtxt(i) for i in g]; size=118
    while True:
        fn=f(BEB,size); sp=d.textlength(' ',font=fn)+14; wd=[d.textlength(w,font=fn) for w in ws]; tot=sum(wd)+sp*(len(ws)-1)
        if tot<=900 or size<=70: break
        size-=4
    xs=[];x=(W-tot)/2
    for w_ in wd: xs.append(x); x+=w_+sp
    act=0
    for k,i in enumerate(g):
        if WORDS[i]['s']<=t: act=k
    g0=WORDS[g[0]]['s']; s=lerp(0.9,1,expo((t-g0)/0.10))
    cap=Image.new('RGBA',(W,300),(0,0,0,0)); cd=ImageDraw.Draw(cap)
    shd=Image.new('RGBA',(W,300),(0,0,0,0)); sd=ImageDraw.Draw(shd)
    prev=max(0,act-1); bt=expo((t-WORDS[g[act]]['s'])/0.07) if act>0 else 1
    bx0=lerp(xs[prev],xs[act],bt)-18; bx1=lerp(xs[prev]+wd[prev],xs[act]+wd[act],bt)+18
    for k,(w_,x_) in enumerate(zip(ws,xs)):
        if k!=act: sd.text((x_+4,46),w_,font=fn,fill=(0,0,0,220))
    cap.alpha_composite(shd.filter(ImageFilter.GaussianBlur(6)))
    litbar(cd,bx0,40+size*0.02,bx1,40+size*0.98,RED)
    for k,(w_,x_) in enumerate(zip(ws,xs)):
        col=CREAM
        if k!=act and WORDS[g[k]]['s']<=t+0.02:
            if w_ in ACC_GOLD: col=VGOLD
            elif w_ in ACC_RED: col=(255,90,80)
        cd.text((x_,40),w_,font=fn,fill=col,stroke_width=0 if k==act else 3,stroke_fill=(0,0,0))
    if abs(s-1)>0.002:
        cap=cap.resize((int(W*s),int(300*s)),Image.BICUBIC); ox=int((W-cap.width)/2); oy=int(CAP_Y-40-(cap.height-300)/2)
    else: ox,oy=0,CAP_Y-40
    im.alpha_composite(cap,(ox,oy))
