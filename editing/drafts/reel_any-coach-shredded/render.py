# @coach.agz — "Any coach can get you shredded" — 1080x1920 30fps
# All graphic times are in RAW source time; the trim is applied at render.
import json, sys, math, subprocess, os
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
HERE=os.path.dirname(os.path.abspath(__file__)); FD=os.path.join(HERE,'..','fonts')+'/'
SRC=os.path.join(HERE,'..','src','raw.mov')
W,H=1080,1920; FPS=30
WORDS=json.load(open(os.path.join(HERE,'words.json')))
TR=json.load(open(os.path.join(HERE,'trim.json'))); KEEP=TR['keep']; CUTS=[a for a,b in TR['remove']]
GOLD=(201,169,110); CREAM=(244,241,234); NAVY=(14,17,23); MUTED=(184,184,188)
RED=(255,34,28); VGOLD=(255,194,26); CYAN=(0,229,255); GREEN=(30,255,110); DEEP=(2,3,8); INK=(6,8,14); WHITE=(255,255,255)
BEB='BebasNeue-Regular.ttf'; MONO='JetBrainsMono-Medium.ttf'; MONOB='JetBrainsMono-Bold.ttf'; BAR='BarlowCondensed-SemiBold.ttf'; BARB='BarlowCondensed-Bold.ttf'; DM='DMSans.ttf'
_fc={}
def f(n,s,wght=None):
    k=(n,int(s),wght)
    if k not in _fc:
        ft=ImageFont.truetype(FD+n,int(s))
        if wght:
            try: ft.set_variation_by_axes([14,wght])
            except Exception: pass
        _fc[k]=ft
    return _fc[k]
def clamp(x,a=0,b=1): return max(a,min(b,x))
def expo(x): x=clamp(x); return 1 if x>=1 else 1-2**(-10*x)
def ease_io(x): x=clamp(x); return 4*x**3 if x<.5 else 1-(-2*x+2)**3/2
def lerp(a,b,t): return a+(b-a)*t
def A(c,a): return tuple(c[:3])+(int(clamp(a)*255),)
def ap(t,t0,d=0.16): return expo((t-t0)/d)
GL=None
def txt(d,x,y,s,font,col,a=1.0,anchor=None): d.text((x,y),s,font=font,fill=A(col,a),anchor=anchor)
def brackets(d,x0,y0,x1,y1,col,L=34,w=4):
    for (cx,cy,sx,sy) in [(x0,y0,1,1),(x1,y0,-1,1),(x0,y1,1,-1),(x1,y1,-1,-1)]:
        d.line([(cx,cy),(cx+sx*L,cy)],fill=col,width=w); d.line([(cx,cy),(cx,cy+sy*L)],fill=col,width=w)
def lit_bar(d,x0,y0,x1,y1,col,a=1.0):
    h=max(1,int(y1-y0))
    for i in range(h):
        k=i/h; c=tuple(int(min(255,v*(1.18-0.36*k)+(40 if k<0.12 else 0))) for v in col)
        d.line([(x0,y0+i),(x1,y0+i)],fill=c+(int(255*a),))
def tag(d,x,y,label,col=RED,size=30,a=1.0,glow=True,anchor_right=False):
    fn=f(MONOB,size); tw=d.textlength(label,font=fn); h=size+16
    if anchor_right: x=x-tw-24
    lit_bar(d,x,y,x+tw+24,y+h,col,a); d.text((x+12,y+6),label,font=fn,fill=A(INK if col in (VGOLD,GREEN,CYAN) else WHITE,a))
    if GL and glow and a>0: GL.rectangle([x-4,y-4,x+tw+28,y+h+4],outline=A(col,a),width=8)
    return x+tw+24
def check(d,x,y,col,s=1.0,a=1.0):
    pts=[(x,y+16*s),(x+10*s,y+28*s),(x+30*s,y+2*s)]
    d.line(pts,fill=A(col,a),width=int(6*s))
    if GL: GL.line(pts,fill=A(col,a),width=int(12*s))
def cross(d,x,y,col,s=1.0,a=1.0):
    d.line([(x,y),(x+28*s,y+28*s)],fill=A(col,a),width=int(6*s)); d.line([(x+28*s,y),(x,y+28*s)],fill=A(col,a),width=int(6*s))
    if GL: GL.line([(x,y),(x+28*s,y+28*s)],fill=A(col,a),width=12); GL.line([(x+28*s,y),(x,y+28*s)],fill=A(col,a),width=12)
def kicker(d,x,y,label,t,t0,col=VGOLD,size=26,a=1.0):
    p=ap(t,t0,0.18)
    if p<=0: return
    d.line([(x,y+size*0.55),(x+lerp(0,40,p),y+size*0.55)],fill=A(col,a),width=4)
    q=clamp((t-t0-0.06)/0.25); n=int(len(label)*q)
    txt(d,x+54,y,label[:n],f(MONOB,size),col,a)
def frosted(im,box,dark=0.86,blur=10):
    x0,y0,x1,y1=[int(v) for v in box]; x0=max(0,x0); y0=max(0,y0); x1=min(W,x1); y1=min(H,y1)
    if x1<=x0 or y1<=y0: return
    reg=im.crop((x0,y0,x1,y1)).convert('RGB').filter(ImageFilter.GaussianBlur(blur))
    im.paste(Image.blend(reg,Image.new('RGB',reg.size,DEEP),dark).convert('RGBA'),(x0,y0))
def panel_frame(d,box,col,a,L=36):
    x0,y0,x1,y1=box
    d.rectangle([x0,y0,x1,y1],outline=A(col,0.45*a),width=2); brackets(d,x0,y0,x1,y1,A(col,a),L,6)
    if GL: brackets(GL,x0,y0,x1,y1,A(col,a),L,12)

# ---------------- footage layouts ----------------
def env(t,t_in,t_out,d_in=0.35,d_out=0.35):
    if t<t_in or t>t_out+d_out: return 0.0
    return min(ease_io((t-t_in)/d_in),1-ease_io((t-t_out)/d_out))
SPLITS=[(21.70,31.20),(100.30,115.20)]
PIPS=[(37.20,60.05)]
def layout(t):
    for a,b in SPLITS:
        p=env(t,a,b)
        if p>0: return 'split',p
    for a,b in PIPS:
        p=env(t,a,b,0.40,0.40)
        if p>0: return 'pip',p
    return 'full',0.0
def seg_of(t): return sum(1 for c in CUTS if c<=t+1e-6)
def place_footage(src,t):
    z=1.0 if seg_of(t)%2==0 else 1.08
    if z!=1.0:
        big=src.resize((int(W*z),int(H*z)),Image.BICUBIC); ox=(big.width-W)//2; oy=int((big.height-H)*0.40); src=big.crop((ox,oy,ox+W,oy+H))
    mode,p=layout(t)
    if mode=='full' or p<=0: return src.convert('RGBA'),mode,p,None
    if mode=='split':
        # dest shrinks to the top 1080px, source window slides to the face band (same scale: no distortion)
        dh=lerp(H,1080,p); sy0=lerp(0,470,p)
        crop=src.crop((0,int(sy0),W,int(sy0+dh)))
        base=Image.new('RGBA',(W,H),NAVY+(255,)); bg_glow(base)
        base.paste(crop.convert('RGBA'),(0,0))
        return base,mode,p,(0,0,W,int(dh))
    # pip: footage becomes a window on a navy board; face stays in frame the whole move
    dx0,dy0,dx1,dy1=lerp(0,560,p),lerp(0,250,p),lerp(W,1020,p),lerp(H,710,p)
    s=lerp(1.0,460/820,p); cx=lerp(540,640,p); cy=lerp(960,920,p)
    sw=(dx1-dx0)/s; sh=(dy1-dy0)/s
    crop=src.crop((int(cx-sw/2),int(cy-sh/2),int(cx+sw/2),int(cy+sh/2))).resize((max(1,int(dx1-dx0)),max(1,int(dy1-dy0))),Image.BICUBIC)
    base=Image.new('RGBA',(W,H),NAVY+(255,)); bg_glow(base)
    m=Image.new('L',crop.size,0); ImageDraw.Draw(m).rounded_rectangle([0,0,crop.width-1,crop.height-1],radius=int(lerp(0,28,p)),fill=255)
    base.paste(crop.convert('RGBA'),(int(dx0),int(dy0)),m)
    return base,mode,p,(int(dx0),int(dy0),int(dx1),int(dy1))
_GLOW=None
def bg_glow(base):
    global _GLOW
    if _GLOW is None:
        yy,xx=np.mgrid[0:H,0:W]; r=np.sqrt((xx-W*0.95)**2+(yy-H*0.05)**2)/1300
        g=np.clip(1-r,0,1)**2*38
        arr=np.zeros((H,W,4),np.uint8); arr[...,0]=40; arr[...,1]=34; arr[...,2]=22; arr[...,3]=g.astype(np.uint8)
        # fine film grain texture so the board isn't flat digital
        rng=np.random.default_rng(3); n=rng.integers(0,10,(H,W)).astype(np.uint8)
        _GLOW=(Image.fromarray(arr,'RGBA'),Image.fromarray(np.dstack([np.full((H,W),255,np.uint8)]*3+[n]),'RGBA'))
    base.alpha_composite(_GLOW[0]); base.alpha_composite(_GLOW[1])

# ---------------- TOP BAND helpers ----------------
TB=(56,248,1024,592)
def band(im,t,t_in,t_out,col=VGOLD,box=TB):
    pin=ap(t,t_in,0.22); pout=clamp((t-t_out)/0.18)
    if pin<=0 or pout>=1: return None,0
    x0,y0,x1,y1=box; a=pin*(1-pout)
    yy=lerp(y0-24,y0,pin); bx=(x0,yy,x1,yy+(y1-y0))
    frosted(im,bx,0.84*a,14)
    d=ImageDraw.Draw(im,'RGBA'); panel_frame(d,bx,col,a)
    return d,a

# ---- SC1 the stack (vials) ----
STACK=[('TREN','300 MG',3.90,VGOLD,'vial'),('TEST','500 MG',5.36,VGOLD,'vial'),('MASTERON','',6.38,VGOLD,'vial'),
       ('RETA','',7.46,CYAN,'pen'),('GLP-1','',13.78,CYAN,'pen'),('PEPTIDES','',15.70,CYAN,'pep')]
def vial(d,cx,base,kind,col,a,fill=0.7):
    if kind=='pen':
        x0,x1=cx-20,cx+20; y0,y1=base-190,base
        d.rounded_rectangle([x0,y0,x1,y1],radius=14,outline=A(WHITE,a),width=3)
        d.rectangle([x0+6,y0+40,x1-6,y0+110],fill=A(col,0.85*a)); d.rectangle([x0-4,y0-24,x1+4,y0],fill=A((90,96,110),a))
        for k in range(4): d.line([(x0,y1-20-k*12),(x0+10,y1-20-k*12)],fill=A(WHITE,a),width=2)
        if GL: GL.rectangle([x0+6,y0+40,x1-6,y0+110],fill=A(col,0.6*a))
        return
    w=64 if kind=='vial' else 50; h=140 if kind=='vial' else 110
    x0,x1=cx-w/2,cx+w/2; y0=base-h
    d.rectangle([cx-w*0.32,y0-34,cx+w*0.32,y0-8],fill=A((170,30,40) if kind=='vial' else (200,200,210),a))
    d.rectangle([cx-w*0.22,y0-10,cx+w*0.22,y0+4],outline=A(WHITE,a),width=3)
    d.rounded_rectangle([x0,y0,x1,base],radius=12,outline=A(WHITE,a),width=3)
    if kind=='vial':
        ly=lerp(base-6,y0+h*(1-fill),1); d.rounded_rectangle([x0+5,ly,x1-5,base-5],radius=8,fill=A(col,0.85*a))
        if GL: GL.rounded_rectangle([x0+5,ly,x1-5,base-5],radius=8,fill=A(col,0.55*a))
    else:
        d.rounded_rectangle([x0+5,base-34,x1-5,base-5],radius=6,fill=A((235,235,240),0.9*a))
def sc_stack(im,t):
    d,a=band(im,t,2.0,16.15)
    if not d: return
    kicker(d,84,270,'THE STACK',t,2.05,a=a)
    n=6; xs=[150+i*156 for i in range(n)]; base=508
    for i,(nm,dose,t0,col,kind) in enumerate(STACK):
        p=ap(t,t0-0.08,0.20)
        if p<=0:
            d.rounded_rectangle([xs[i]-40,base-150,xs[i]+40,base],radius=10,outline=A((70,74,90),0.6*a),width=2); continue
        dy=lerp(-90,0,p); aa=a*p
        vial(d,xs[i],base+dy,kind,col,aa)
        fn=f(BEB,40); tw=d.textlength(nm,font=fn); txt(d,xs[i]-tw/2,base+8+dy,nm,fn,WHITE,aa)
        if dose:
            fd=f(MONOB,17); dw=d.textlength(dose,font=fd)
            d.rectangle([xs[i]-30,base-92+dy,xs[i]+30,base-66+dy],fill=A((245,245,248),aa)); txt(d,xs[i]-dw/2,base-91+dy,dose,fd,INK,aa)
    if t>=8.52:
        q=ap(t,8.52,0.2); tag(d,1000,268,'LOOKS: INCREDIBLE',VGOLD,24,a*q,anchor_right=True)
    if t>=10.36:
        q=ap(t,10.36,0.14); tag(d,1000,316,'SHORT-TERM',RED,24,a*q,anchor_right=True)
    txt(d,84,560,'FOR RESEARCH & EDUCATIONAL PURPOSES ONLY',f(MONO,18),MUTED,0.8*a)

# ---- SC2 side rail: body fat line ----
RAIL=(36,650,320,1400)
def rail(im,t,t_in,t_out,col=VGOLD,box=RAIL):
    pin=ap(t,t_in,0.24); pout=clamp((t-t_out)/0.18)
    if pin<=0 or pout>=1: return None,0,box
    a=pin*(1-pout); x0,y0,x1,y1=box; dx=lerp(-60,0,pin)-300*pout**2
    bx=(x0+dx,y0,x1+dx,y1); frosted(im,bx,0.84*a,14); d=ImageDraw.Draw(im,'RGBA'); panel_frame(d,bx,col,a,28)
    return d,a,bx
def sc_bodyfat(im,t):
    d,a,(x0,y0,x1,y1)=rail(im,t,16.30,21.45)
    if not d: return
    txt(d,x0+22,y0+22,'BODY FAT',f(MONOB,26),VGOLD,a); txt(d,x0+22,y0+58,'ON THE STACK',f(MONO,18),MUTED,a)
    gx0,gy0,gx1,gy1=x0+40,y0+130,x1-24,y1-170
    d.line([(gx0,gy1),(gx1,gy1)],fill=A((90,94,110),a),width=2); d.line([(gx0,gy0),(gx0,gy1)],fill=A((90,94,110),a),width=2)
    for k in range(1,5): d.line([(gx0,gy0+k*(gy1-gy0)/5),(gx1,gy0+k*(gy1-gy0)/5)],fill=A((40,44,60),a),width=1)
    vals=[0.9,0.86,0.7,0.48,0.3,0.16,0.1]
    pts=[(lerp(gx0+10,gx1-10,i/6),lerp(gy1-10,gy0+10,v)) for i,v in enumerate(vals)]
    pr=clamp((t-16.9)/1.6)*6
    for i in range(6):
        if pr>i:
            q=min(1,pr-i); e=(lerp(pts[i][0],pts[i+1][0],q),lerp(pts[i][1],pts[i+1][1],q))
            d.line([pts[i],e],fill=A(VGOLD,a),width=6)
            if GL: GL.line([pts[i],e],fill=A(VGOLD,a),width=12)
    for i,pt in enumerate(pts):
        if pr>=i: d.ellipse([pt[0]-7,pt[1]-7,pt[0]+7,pt[1]+7],fill=A(WHITE,a))
    txt(d,gx0,gy1+10,'WEEKS',f(MONO,18),MUTED,a)
    if t>=18.36: tag(d,x0+22,y1-130,'SHREDDED',VGOLD,26,a*ap(t,18.36))
    if t>=20.04: tag(d,x0+22,y1-74,'THE GOAL?',RED,26,a*ap(t,20.04))

# ---- SC3 split: the rest of your life (two-line timeline) ----
def sc_future(d,t,p):
    a=p
    kicker(d,70,1228,'THE REST OF YOUR LIFE',t,21.9,a=a)
    gx0,gy0,gx1,gy1=110,1300,1000,1540
    d.line([(gx0,gy1),(gx1,gy1)],fill=A((90,94,110),a),width=2)
    ticks=[('NOW',22.06),('1 YR',24.52),('2 YRS',26.76),('OFF',29.26)]
    xs=[lerp(gx0+30,gx1-60,i/3) for i in range(4)]
    for i,(lb,tt) in enumerate(ticks):
        q=ap(t,tt,0.14)
        col=WHITE if i==0 else (RED if i==3 else CREAM)
        d.line([(xs[i],gy1-8),(xs[i],gy1+8)],fill=A((120,124,140),a),width=2)
        fn=f(MONOB,24); tw=d.textlength(lb,font=fn); txt(d,xs[i]-tw/2,gy1+14,lb,fn,col,a*max(0.35,q))
    # LOOK line: holds high, falls off a cliff once you're OFF
    def ylook(x):
        if x<xs[3]-40: return gy0+30
        return lerp(gy0+30,gy1-30,ease_io((x-(xs[3]-40))/90))
    # HEALTH line: unknown — dashed, drifting down
    def yhealth(x): return lerp(gy0+70,gy0+170,clamp((x-xs[0])/(xs[3]-xs[0]))**1.4)
    reach=xs[0]
    if t>=22.06: reach=lerp(xs[0],xs[3]+90,clamp((t-22.1)/(29.6-22.1)))
    if t>=29.26: reach=xs[3]+120
    prev=None
    for x in np.arange(xs[0],reach,6):
        pt=(x,ylook(x))
        if prev: d.line([prev,pt],fill=A(VGOLD,a),width=6); GL and GL.line([prev,pt],fill=A(VGOLD,a*0.8),width=10)
        prev=pt
    prev=None
    for k,x in enumerate(np.arange(xs[0],min(reach,xs[3]+80),6)):
        pt=(x,yhealth(x))
        if prev and (k//3)%2==0: d.line([prev,pt],fill=A(RED,a),width=5)
        prev=pt
    if t>=22.2: txt(d,gx0-6,gy0+2,'PHYSIQUE',f(MONOB,22),VGOLD,a*ap(t,22.2)); txt(d,gx0-6,gy0+86,'HEALTH',f(MONOB,22),RED,a*ap(t,22.4))
    for i,tt in [(1,24.52),(2,26.76),(3,30.48)]:
        if t>=tt:
            q=ap(t,tt,0.12); x=xs[i]; y=yhealth(x)
            d.ellipse([x-24,y-24,x+24,y+24],fill=A(RED,a*q)); fn=f(BEB,40); txt(d,x-8,y-20,'?',fn,WHITE,a*q)
            if GL: GL.ellipse([x-28,y-28,x+28,y+28],outline=A(RED,a*q),width=8)
    if t>=25.94: tag(d,xs[1]+40,gy0-10,'OFF RETA',CYAN,22,a*ap(t,25.94))
    if t>=29.26: tag(d,xs[3]-250,gy1-74,'OFF COMPOUNDS',RED,22,a*ap(t,29.26))

# ---- SC4 DMs inbox (top band) ----
DMS=[('what dose should i run?',31.88),('bro can u send ur protocol',32.78),('what stack should i copy??',33.24)]
def sc_dms(im,t):
    d,a=band(im,t,31.50,37.05,CYAN)
    if not d: return
    txt(d,84,266,'MESSAGE REQUESTS',f(MONOB,26),CREAM,a)
    n=min(99,int(lerp(12,99,clamp((t-32.78)/1.2)))) if t>=32.78 else 12
    lb=('99+' if n>=99 else str(n)); fn=f(MONOB,24); tw=d.textlength(lb,font=fn)
    d.rounded_rectangle([370,264,370+tw+26,300],radius=18,fill=A(RED,a)); txt(d,383,268,lb,fn,WHITE,a)
    txt(d,1000-d.textlength('EVERY SINGLE DAY',font=f(MONO,22)),272,'EVERY SINGLE DAY',f(MONO,22),CYAN,a*ap(t,32.78))
    for i,(msg,tt) in enumerate(DMS):
        q=ap(t,tt,0.18)
        if q<=0: continue
        y=320+i*86; x=lerp(1040,84,q)
        d.rounded_rectangle([x,y,x+900,y+74],radius=16,fill=A((22,26,36),a*q))
        d.ellipse([x+14,y+12,x+64,y+62],fill=A((60,66,84),a*q))
        d.rounded_rectangle([x+82,y+14,x+232,y+30],radius=6,fill=A((70,76,96),a*q))
        txt(d,x+82,y+34,msg,f(DM,30,600),WHITE,a*q)
        d.ellipse([x+870,y+30,x+884,y+44],fill=A(CYAN,a*q))
    for i,tt in [(0,35.26),(1,36.08),(2,36.52)]:
        if t>=tt:
            y=320+i*86; q=ap(t,tt,0.1); brackets(d,80,y-4,988,y+78,A(VGOLD,a*q),22,5)
            if GL: brackets(GL,80,y-4,988,y+78,A(VGOLD,a*q),22,10)

# ---- SC5 PiP: your lab panel — unknown ----
LAB=[('Estradiol','AROMATIZATION',41.90),('Prolactin','',43.54),('Creatinine / eGFR','KIDNEY',45.40),('ALT / AST','LIVER',46.62),
     ('HDL','LIPIDS',47.64),('Side-effect response','YOU',49.10),('Compound response','YOU',50.70),('Positive response','YOU',52.30)]
def sc_lab(d,im,t,p):
    a=p
    kicker(d,64,262,'CLIENT FILE',t,37.4,a=a)
    txt(d,64,312,'YOUR',f(BEB,96),CREAM,a*ap(t,37.5)); txt(d,64,398,'BLOODWORK',f(BEB,96),VGOLD,a*ap(t,37.7))
    if t>=38.98:
        q=ap(t,38.98,0.12); blink=1 if int(t*3)%2==0 else 0.55
        tag(d,64,512,'NOT ON FILE',RED,30,a*q*blink)
    if t>=39.54: txt(d,64,580,'DOSE ▸ ?    PROTOCOL ▸ ?',f(MONOB,26),MUTED,a*ap(t,39.54))
    # report sheet
    x0,y0,x1,y1=56,760,1024,1390
    pa=ap(t,40.2,0.25)*a
    if pa<=0: return
    yy=lerp(y0+40,y0,ap(t,40.2,0.25))
    d.rectangle([x0,yy,x1,yy+(y1-y0)],fill=A((236,236,240),pa)); d.rectangle([x0,yy,x1,yy+64],fill=A((210,10,20),pa))
    txt(d,x0+24,yy+14,'LAB REPORT · HORMONE + HEALTH PANEL',f(MONOB,26),WHITE,pa)
    txt(d,x0+24,yy+76,'TEST',f(MONOB,20),(110,110,120),pa); txt(d,x0+560,yy+76,'RESULT',f(MONOB,20),(110,110,120),pa); txt(d,x0+800,yy+76,'FLAG',f(MONOB,20),(110,110,120),pa)
    for i,(nm,sub,tt) in enumerate(LAB):
        ry=yy+108+i*62
        if i==5: d.line([(x0+20,ry-6),(x1-20,ry-6)],fill=A((150,150,160),pa),width=3)
        txt(d,x0+24,ry+4,nm,f(DM,32,600),(40,44,56),pa)
        if sub: fn=f(MONO,18); txt(d,x0+24+d.textlength(nm,font=f(DM,32,600))+14,ry+14,sub,fn,(130,130,140),pa)
        if t>=tt:
            q=ap(t,tt,0.12)
            txt(d,x0+560,ry-2,'??',f(BEB,48),(210,10,20),pa*q)
            tag(d,x0+780,ry,'NO DATA',RED,22,pa*q,glow=False)
            if t<tt+0.5:
                k=1-clamp((t-tt)/0.5); d.rectangle([x0+6,ry-4,x1-6,ry+54],outline=A(RED,pa*k),width=4)
        else:
            txt(d,x0+560,ry+4,'—',f(DM,32,600),(150,150,160),pa)
        d.line([(x0+20,ry+56),(x1-20,ry+56)],fill=A((215,215,222),pa),width=1)
    if t>=59.82:
        q=expo((t-59.82)/0.12); xr=lerp(x0,x1,q); yv=1404
        lit_bar(d,x0,yv,xr,yv+86,RED,a)
        if GL: GL.rectangle([x0-4,yv-4,xr+4,yv+90],outline=A(RED,a),width=10)
        if q>0.6: txt(d,x0+26,yv+8,'NO BLOODWORK = NO PROTOCOL',f(BEB,74),WHITE,a)

# ---- SC6 weekly bloodwork bars (top band) ----
BARS=[0.88,0.22,0.74,0.36,0.62,0.48,0.56,0.52]
def sc_weekly(im,t):
    d,a=band(im,t,60.45,68.85,GREEN)
    if not d: return
    kicker(d,84,270,'WEEKLY BLOODWORK',t,60.5,a=a)
    if t>=61.90: tag(d,1000,264,'CUSTOM · YOU',VGOLD,24,a*ap(t,61.90),anchor_right=True)
    gx0,gy0,gx1,gy1=110,330,990,540
    lo,hi=0.40,0.64
    opt=ap(t,67.36,0.3)
    bcol=tuple(int(lerp(c1,c2,opt)) for c1,c2 in zip((70,74,90),GREEN))
    by0=lerp(gy1,gy0,hi); by1=lerp(gy1,gy0,lo)
    d.rectangle([gx0,by0,gx1,by1],fill=A(bcol,a*lerp(0.18,0.30,opt)))
    d.line([(gx0,by0),(gx1,by0)],fill=A(bcol,a),width=2); d.line([(gx0,by1),(gx1,by1)],fill=A(bcol,a),width=2)
    txt(d,gx1-150,by0-26,'TARGET RANGE',f(MONO,18),bcol,a)
    d.line([(gx0,gy1),(gx1,gy1)],fill=A((90,94,110),a),width=2)
    bw=(gx1-gx0)/8
    for i,v in enumerate(BARS):
        tt=61.30+i*0.52
        q=ap(t,tt,0.22)
        cx=gx0+bw*(i+0.5)
        fn=f(MONO,18); lb=f'W{i+1}'; tw=d.textlength(lb,font=fn); txt(d,cx-tw/2,gy1+4,lb,fn,MUTED,a)
        if q<=0: continue
        top=lerp(gy1,lerp(gy1,gy0,v),q); inr=lo<=v<=hi
        col=GREEN if inr and opt>0.5 else (RED if not inr else VGOLD)
        lit_bar(d,cx-bw*0.3,top,cx+bw*0.3,gy1,col,a)
        if GL: GL.rectangle([cx-bw*0.3,top,cx+bw*0.3,gy1],outline=A(col,a*0.7),width=6)
    if t>=65.04: txt(d,110,560,'CONSISTENT · BLOODWORK-BACKED',f(MONOB,20),CREAM,a*ap(t,65.04))
    if t>=67.36: tag(d,1000,546,'OPTIMIZED FIRST',GREEN,22,a*ap(t,67.36),anchor_right=True)

# ---- SC7 side rail: coaching pillars ----
PILLARS=[('01','SUSTAIN-','ABILITY',71.90),('02','CONSIS-','TENCY',72.82),('03','EDUCA-','TION',74.52)]
def sc_pillars(im,t):
    d,a,(x0,y0,x1,y1)=rail(im,t,69.25,78.40,VGOLD,(36,640,320,1440))
    if not d: return
    txt(d,x0+22,y0+22,'COACHING',f(MONOB,28),VGOLD,a); txt(d,x0+22,y0+60,'IS SUPPOSED TO BE',f(MONO,18),MUTED,a)
    for i,(no,l1,l2,tt) in enumerate(PILLARS):
        q=ap(t,tt,0.2)
        if q<=0: continue
        by=y0+110+i*150; bx=lerp(x0-120,x0+18,q)
        d.rectangle([bx,by,bx+248,by+130],fill=A((24,22,18),a*q),outline=A(VGOLD,a*q),width=3)
        d.rectangle([bx,by,bx+8,by+130],fill=A(VGOLD,a*q))
        txt(d,bx+22,by+8,no,f(MONOB,22),VGOLD,a*q); txt(d,bx+22,by+34,l1,f(BEB,48),CREAM,a*q); txt(d,bx+22,by+78,l2,f(BEB,48),CREAM,a*q)
        if GL: GL.rectangle([bx,by,bx+248,by+130],outline=A(VGOLD,a*q*0.6),width=6)
    if t>=75.90:
        q=ap(t,75.90); check(d,x0+24,y0+570,GREEN,0.8,a*q); txt(d,x0+60,y0+568,'YOU UNDERSTAND IT',f(MONOB,18),GREEN,a*q)
    if t>=78.04:
        q=expo((t-78.04)/0.3); ry=y0+620; rx1=lerp(x0+24,x1-20,q)
        d.line([(x0+24,ry+30),(rx1,ry+30)],fill=A(VGOLD,a),width=6)
        for k,lb in enumerate(['10','20','30+']):
            xx=lerp(x0+24,x1-40,(k+1)/3)
            if rx1>=xx-4: d.line([(xx,ry+18),(xx,ry+42)],fill=A(VGOLD,a),width=4); txt(d,xx-14,ry+48,lb,f(MONOB,20),CREAM,a)
        txt(d,x0+24,ry-10,'YEARS · DECADES',f(MONOB,20),VGOLD,a*q)

# ---- SC8 looks vs energy (top band) ----
def sc_energy(im,t):
    d,a=band(im,t,79.70,92.40,RED,(56,248,1024,620))
    if not d: return
    kicker(d,84,266,'WHAT IS THE POINT',t,79.78,RED,a=a)
    # LOOKS meter
    lx0,lx1=84,520
    txt(d,lx0,320,'LOOKS',f(MONOB,24),VGOLD,a)
    lf=ap(t,80.98,0.6)
    d.rectangle([lx0,356,lx1,392],outline=A((70,74,90),a),width=2); lit_bar(d,lx0+3,359,lerp(lx0+3,lx1-3,lf),389,VGOLD,a)
    if GL and lf>0: GL.rectangle([lx0+3,359,lerp(lx0+3,lx1-3,lf),389],fill=A(VGOLD,a*0.6))
    txt(d,lx1-70,312,f'{int(100*lf)}%',f(BEB,44),VGOLD,a*ap(t,80.98))
    # clock
    if t>=83.68:
        q=ap(t,83.68,0.14); d.rounded_rectangle([lx0,418,lx0+250,500],radius=10,fill=A((10,12,18),a*q),outline=A(CREAM,a*q),width=2)
        txt(d,lx0+18,414,'5:00',f(BEB,90),CREAM,a*q); txt(d,lx0+160,440,'PM',f(MONOB,30),CREAM,a*q)
        txt(d,lx0+268,430,'HOME',f(MONOB,22),MUTED,a*q); txt(d,lx0+268,458,'AFTER WORK',f(MONOB,22),MUTED,a*q)
    # battery
    bx0,by0,bx1,by1=640,330,960,470
    e=1.0 if t<85.66 else lerp(1.0,0.08,ease_io((t-85.66)/(88.02-85.66)))
    col=GREEN if e>0.5 else (VGOLD if e>0.2 else RED)
    txt(d,bx0,290,'ENERGY',f(MONOB,24),col,a)
    d.rounded_rectangle([bx0,by0,bx1,by1],radius=12,outline=A(WHITE,a),width=4); d.rectangle([bx1+4,by0+44,bx1+18,by1-44],fill=A(WHITE,a))
    lit_bar(d,bx0+10,by0+10,lerp(bx0+10,bx1-10,e),by1-10,col,a)
    if GL: GL.rectangle([bx0+10,by0+10,lerp(bx0+10,bx1-10,e),by1-10],outline=A(col,a),width=8)
    txt(d,bx1-110,290,f'{int(e*100)}%',f(BEB,44),col,a)
    if t>=88.02: tag(d,bx0,480,'FRIED',RED,26,a*ap(t,88.02))
    for i,(lb,tt) in enumerate([('KIDS · NO ENERGY',89.08),('WIFE · ON EDGE',90.36)]):
        if t>=tt:
            q=ap(t,tt); y=540+0*i; x=84+i*470
            cross(d,x,y+2,RED,0.9,a*q); txt(d,x+40,y,lb,f(MONOB,26),WHITE,a*q)

# ---- SC9 SHREDDED ≠ THE GOAL (stamp) ----
def sc_stamp(im,t):
    d,a=band(im,t,92.70,94.55,RED,(56,300,1024,560))
    if not d: return
    q=ap(t,92.88,0.12); s=lerp(1.25,1.0,q)
    fn=f(BEB,int(190*s)); lb='SHREDDED'; tw=d.textlength(lb,font=fn)
    txt(d,540-tw/2,330+(1-s)*40,lb,fn,CREAM,a*q)
    if t>=93.36:
        p=expo((t-93.36)/0.16); x0=540-tw/2-20; x1=lerp(x0,540+tw/2+20,p)
        d.line([(x0,440),(x1,420)],fill=A(RED,a),width=16)
        if GL: GL.line([(x0,440),(x1,420)],fill=A(RED,a),width=26)
    if t>=93.72: tag(d,540-150,500,'≠ THE GOAL',RED,34,a*ap(t,93.72))

# ---- SC10 gauge: 100% hormonally optimized ----
def sc_gauge(im,t):
    d,a=band(im,t,94.80,100.10,GREEN)
    if not d: return
    cx,cy,r=300,540,190
    v=0 if t<95.42 else ease_io((t-95.42)/0.9)
    for k in range(60):
        f0=k/60; ang0=math.pi+f0*math.pi; ang1=math.pi+(k+0.7)/60*math.pi
        col=(RED if f0<0.4 else (VGOLD if f0<0.75 else GREEN)); lit=f0<=v
        c=col if lit else (50,54,66)
        d.arc([cx-r,cy-r,cx+r,cy+r],math.degrees(ang0),math.degrees(ang1),fill=A(c,a),width=34)
        if GL and lit: GL.arc([cx-r,cy-r,cx+r,cy+r],math.degrees(ang0),math.degrees(ang1),fill=A(c,a*0.8),width=40)
    ang=math.pi+v*math.pi
    d.line([(cx,cy),(cx+(r-24)*math.cos(ang),cy+(r-24)*math.sin(ang))],fill=A(WHITE,a),width=8); d.ellipse([cx-16,cy-16,cx+16,cy+16],fill=A(WHITE,a))
    txt(d,560,270,'HORMONAL STATUS',f(MONOB,24),CREAM,a)
    num=int(round(100*v)); txt(d,560,300,f'{num}%',f(BEB,170),GREEN if v>0.75 else VGOLD,a*ap(t,95.30))
    if t>=97.28: txt(d,560,468,'HORMONALLY OPTIMIZED',f(MONOB,26),GREEN,a*ap(t,97.28))
    if t>=99.48: tag(d,560,510,'THE GOAL',VGOLD,30,a*ap(t,99.48))

# ---- SC11 split: the full breakdown staircase ----
STEPS=[('01','YOUR','BLOODWORK',105.00),('02','SIDE-EFFECT','RESPONSE',105.74),('03','LOW + SLOW','TITRATION',106.86),('04','COMPOUND','RESPONSE',109.22),('05','THE RIGHT','FRAMEWORKS',112.12)]
def sc_steps(d,t,p):
    a=p
    kicker(d,70,1228,'THE FULL BREAKDOWN',t,101.38,a=a)
    x0=64; sw=184; base=1560
    for i,(no,l1,l2,tt) in enumerate(STEPS):
        q=ap(t,tt,0.2); hgt=110+i*44; bx=x0+i*(sw+4); top=base-hgt
        if q<=0:
            d.rectangle([bx,top,bx+sw,base],outline=A((60,64,80),a*0.7),width=2); continue
        yy=lerp(top+60,top,q)
        d.rectangle([bx,yy,bx+sw,base],fill=A((20,22,30),a*q),outline=A(VGOLD,a*q),width=3)
        lit_bar(d,bx,yy,bx+sw,yy+8,VGOLD,a*q)
        if GL: GL.rectangle([bx,yy,bx+sw,base],outline=A(VGOLD,a*q*0.6),width=6)
        txt(d,bx+12,yy+14,no,f(MONOB,22),VGOLD,a*q)
        txt(d,bx+12,yy+40,l1,f(BAR,30),MUTED,a*q); txt(d,bx+12,yy+68,l2,f(BEB,40),CREAM,a*q)
        if i==2 and t>=107.24:   # low and slow: stepped dose ramp inside the block
            pr=clamp((t-107.24)/2.2); sx0,sy0=bx+14,base-16; prev=(sx0,sy0)
            for k in range(int(pr*6)+1):
                nx=sx0+k*26; ny=sy0-k*9
                d.line([prev,(nx,prev[1])],fill=A(CYAN,a),width=4); d.line([(nx,prev[1]),(nx,ny)],fill=A(CYAN,a),width=4); prev=(nx,ny)
            if GL: GL.line([(sx0,sy0),prev],fill=A(CYAN,a*0.5),width=6)
    if t>=114.30:
        q=ap(t,114.30,0.2); tag(d,1016,1236,'FOR LIFE',VGOLD,26,a*q,anchor_right=True)

# ---- SC12 CTA end card (top band) ----
LOGO=None
def sc_cta(im,t):
    d,a=band(im,t,115.60,999,VGOLD,(56,262,1024,560))
    if not d: return
    global LOGO
    if LOGO is None:
        lg=Image.open(os.path.join(HERE,'logo.jpg')).convert('RGB'); s=min(lg.size); lg=lg.crop(((lg.width-s)//2,(lg.height-s)//2,(lg.width+s)//2,(lg.height+s)//2)).resize((200,200),Image.LANCZOS)
        m=Image.new('L',(200,200),0); ImageDraw.Draw(m).ellipse([0,0,199,199],fill=255); lg.putalpha(m); LOGO=lg
    lg=LOGO.copy(); lg.putalpha(lg.split()[3].point(lambda v:int(v*a))); im.alpha_composite(lg,(84,300))
    d=ImageDraw.Draw(im,'RGBA')
    txt(d,310,296,'FREE · FULL PROTOCOL BREAKDOWN',f(MONOB,24),VGOLD,a)
    if t>=115.76:
        b=expo((t-115.76)/0.14); s=lerp(1.12,1.0,b); fn=f(BEB,int(96*s)); lb='COMMENT  "LABS"'; tw=d.textlength(lb,font=fn)
        lit_bar(d,310,340,310+tw+40,340+int(112*s),VGOLD,b); d.text((330,348),lb,font=fn,fill=A(INK,b))
        if GL: GL.rectangle([306,336,314+tw+40,344+int(112*s)],outline=A(VGOLD,b),width=12)
    if t>=116.26: txt(d,310,478,'BLOODWORK · TITRATION · FRAMEWORKS',f(MONO,22),CREAM,a*ap(t,116.26))
    txt(d,310,512,'@coach.agz',f(MONOB,22),GOLD,a)

# ---------------- captions ----------------
def build_groups():
    G=[];cur=[]
    for i,x in enumerate(WORDS):
        if cur:
            prev=WORDS[cur[-1]]
            if len(cur)>=3 or x['s']-prev['e']>0.28 or prev['w'][-1] in '.,?!' : G.append(cur); cur=[]
        cur.append(i)
    if cur: G.append(cur)
    return G
GROUPS=build_groups()
def group_at(t):
    lo=None
    for g in GROUPS:
        if WORDS[g[0]]['s']<=t+1e-6: lo=g
        else: break
    if lo is None: return None
    end=WORDS[lo[-1]]['e']+0.5
    nxt=[g for g in GROUPS if WORDS[g[0]]['s']>WORDS[lo[0]]['s']]
    if t>end and (not nxt or WORDS[nxt[0][0]]['s']>t): return None
    return lo
FIX={'tren,':'TREN,','glps,':'GLPS,','reta.':'RETA.','reta,':'RETA,'}
ACCENT={'SHREDDED':VGOLD,'SHREDDED,':VGOLD,'BLOOD':VGOLD,'WORK':VGOLD,'WORK,':VGOLD,'OPTIMIZED,':GREEN,'LABS':VGOLD,'DECADES':VGOLD,'SUSTAINABILITY':VGOLD,'CONSISTENCY':VGOLD,'EDUCATION':VGOLD,'FRIED':RED,'EDGE':RED,'KNOW.':RED}
def captions(im,t,cy):
    g=group_at(t)
    if not g: return
    d=ImageDraw.Draw(im,'RGBA')
    ws=[WORDS[i]['w'].upper().rstrip(',') for i in g]
    size=104
    while True:
        fn=f(BEB,size); sp=d.textlength(' ',font=fn)+14; wd=[d.textlength(w,font=fn) for w in ws]; tot=sum(wd)+sp*(len(ws)-1)
        if tot<=860: break
        size-=4
    xs=[];x=(W-tot)/2
    for w_ in wd: xs.append(x); x+=w_+sp
    act=0
    for k,i in enumerate(g):
        if WORDS[i]['s']<=t: act=k
    g0=WORDS[g[0]]['s']; s=lerp(0.9,1,expo((t-g0)/0.10))
    CH=260
    cap=Image.new('RGBA',(W,CH),(0,0,0,0)); cd=ImageDraw.Draw(cap); shd=Image.new('RGBA',(W,CH),(0,0,0,0)); sd=ImageDraw.Draw(shd)
    prev=max(0,act-1); bt=expo((t-WORDS[g[act]]['s'])/0.07) if act>0 else 1
    bx0=lerp(xs[prev],xs[act],bt)-16; bx1=lerp(xs[prev]+wd[prev],xs[act]+wd[act],bt)+16
    for k,(w_,x_) in enumerate(zip(ws,xs)): sd.text((x_+4,44),w_,font=fn,fill=(0,0,0,220))
    cap.alpha_composite(shd.filter(ImageFilter.GaussianBlur(6)))
    lit_bar(cd,bx0,40+size*0.02,bx1,40+size*0.98,RED)
    for k,(w_,x_) in enumerate(zip(ws,xs)):
        col=ACCENT.get(w_,CREAM) if k!=act else CREAM
        cd.text((x_,40),w_,font=fn,fill=col,stroke_width=0 if k==act else 3,stroke_fill=(0,0,0))
    oy0=int(cy-40-size/2)
    if abs(s-1)>0.002:
        cap=cap.resize((int(W*s),int(CH*s)),Image.BICUBIC); ox=int((W-cap.width)/2); oy=int(oy0-(cap.height-CH)/2)
    else: ox,oy=0,oy0
    im.alpha_composite(cap,(ox,oy))

# ---------------- frame ----------------
def frame(src,t):
    global GL
    im,mode,p,win=place_footage(src,t)
    glow=Image.new('RGBA',(W,H),(0,0,0,0)); GL=ImageDraw.Draw(glow,'RGBA')
    d=ImageDraw.Draw(im,'RGBA')
    if mode=='split':
        d.line([(0,win[3]),(W,win[3])],fill=A(VGOLD,p),width=4); GL.line([(0,win[3]),(W,win[3])],fill=A(VGOLD,p),width=10)
        lay=Image.new('RGBA',(W,H),(0,0,0,0)); ld=ImageDraw.Draw(lay,'RGBA')
        if t<60: sc_future(ld,t,1)
        else: sc_steps(ld,t,1)
        off=int((1-p)*500); lay2=Image.new('RGBA',(W,H),(0,0,0,0)); lay2.alpha_composite(lay,(0,off)) if off<H else None
        lay2.putalpha(lay2.split()[3].point(lambda v:int(v*p))); im.alpha_composite(lay2)
    if mode=='pip':
        d=ImageDraw.Draw(im,'RGBA')
        x0,y0,x1,y1=win
        if p>0.05:
            d.rounded_rectangle([x0-3,y0-3,x1+3,y1+3],radius=30,outline=A(VGOLD,p),width=4); GL.rounded_rectangle([x0-3,y0-3,x1+3,y1+3],radius=30,outline=A(VGOLD,p*0.7),width=10)
            d.ellipse([x0+18,y0+18,x0+34,y0+34],fill=A(RED,p if int(t*2)%2==0 else p/3)); txt(d,x0+42,y0+12,'COACH AGZ',f(MONOB,20),WHITE,p)
        lay=Image.new('RGBA',(W,H),(0,0,0,0)); ld=ImageDraw.Draw(lay,'RGBA'); sc_lab(ld,lay,t,1)
        lay.putalpha(lay.split()[3].point(lambda v:int(v*p))); im.alpha_composite(lay)
    # floating overlays on footage
    sc_stack(im,t); sc_bodyfat(im,t); sc_dms(im,t); sc_weekly(im,t); sc_pillars(im,t); sc_energy(im,t); sc_stamp(im,t); sc_gauge(im,t); sc_cta(im,t)
    GLd=GL; GL=None
    if glow.getbbox():
        sm=glow.resize((W//4,H//4),Image.BILINEAR)
        g1=np.asarray(sm.filter(ImageFilter.GaussianBlur(3.5))).astype(np.float32)/255; g2=np.asarray(sm.filter(ImageFilter.GaussianBlur(10))).astype(np.float32)/255
        prem=np.clip(g1[...,:3]*g1[...,3:]*2.0+g2[...,:3]*g2[...,3:]*1.6,0,1)
        prem=np.asarray(Image.fromarray((prem*255).astype(np.uint8)).resize((W,H),Image.BILINEAR)).astype(np.float32)/255
        b=np.asarray(im.convert('RGB')).astype(np.float32)/255
        im=Image.fromarray(((1-(1-b)*(1-prem))*255).astype(np.uint8)).convert('RGBA')
    d=ImageDraw.Draw(im,'RGBA'); d.rectangle([0,0,7,H],fill=GOLD)
    # vertical handle along the gold rule
    if not hasattr(frame,'_hd'):
        fn=f(MONOB,22); tw=int(d.textlength('@coach.agz',font=fn)); hd=Image.new('RGBA',(tw+8,34),(0,0,0,0)); ImageDraw.Draw(hd).text((4,2),'@coach.agz',font=fn,fill=GOLD+(230,),stroke_width=2,stroke_fill=(0,0,0,160)); frame._hd=hd.rotate(90,expand=True)
    im.alpha_composite(frame._hd,(14,1180))
    cy={'full':1528,'split':lerp(1528,1150,p),'pip':1528}[mode]
    captions(im,t,cy)
    return im.convert('RGB')

def new_to_old(tn):
    acc=0
    for a,b in KEEP:
        if tn < acc+(b-a)-1e-9: return a+(tn-acc)
        acc+=b-a
    return KEEP[-1][1]-1/FPS
NNEW=int(round(sum(b-a for a,b in KEEP)*FPS))
if __name__=='__main__':
    if sys.argv[1]=='stills':
        out=sys.argv[2]; os.makedirs(out,exist_ok=True)
        for tt in [float(x) for x in sys.argv[3:]]:
            subprocess.run(['ffmpeg','-v','error','-y','-ss',f'{tt:.3f}','-i',SRC,'-frames:v','1',out+'/_src.png'])
            frame(Image.open(out+'/_src.png').convert('RGB'),tt).save(out+f'/st_{tt:07.2f}.jpg',quality=88)
        sys.exit()
    n0,n1,out=int(sys.argv[1]),int(sys.argv[2]),sys.argv[3]; n1=min(n1,NNEW)
    olds=[min(3620,int(round(new_to_old(n/FPS)*FPS))) for n in range(n0,n1)]
    first,last=olds[0],olds[-1]
    dec=subprocess.Popen(['ffmpeg','-v','error','-ss',f'{max(0,first-15)/FPS:.4f}','-i',SRC,'-vf',f'select=gte(n\\,{first-max(0,first-15)})','-vsync','0','-frames:v',str(last-first+1),'-f','rawvideo','-pix_fmt','rgb24','-'],stdout=subprocess.PIPE)
    enc=subprocess.Popen(['ffmpeg','-v','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-','-c:v','libx264','-crf','12','-preset','veryfast','-pix_fmt','yuv420p',out],stdin=subprocess.PIPE)
    cur=first-1; buf=None
    for n,o in zip(range(n0,n1),olds):
        while cur<o:
            buf=dec.stdout.read(W*H*3); cur+=1
            if len(buf)<W*H*3: raise SystemExit(f'short read at {cur}')
        enc.stdin.write(frame(Image.frombuffer('RGB',(W,H),buf),o/FPS).tobytes())
    enc.stdin.close(); enc.wait(); dec.kill(); print('done',n0,n1)
