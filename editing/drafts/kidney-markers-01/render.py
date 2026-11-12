# Kidney markers — full render (1080x1920, 30 fps). Usage:
#   python3 render.py <scratch> stills t1 t2 ...
#   python3 render.py <scratch> chunk n0 n1 out.mp4
import json, subprocess, sys, math
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
S=sys.argv[1]; F=S+'/fonts/'; T=S+'/k/'
W,H=1080,1920; FPS=30
WORDS=json.load(open(T+'words.json'))
DUR=78.70
GOLD=(201,169,110); CREAM=(244,241,234); NAVY=(14,17,23); MUTED=(184,184,188); DIM=(124,124,130)
RED=(255,34,28); VGOLD=(255,194,26); CYAN=(0,229,255); GREEN=(30,255,110); AMBER=(240,160,48); BLUE=(79,163,224)
DEEP=(2,3,8); INK=(6,8,14); WHITE=(255,255,255); PANEL=(16,19,27)
MONO='JBMono-500.ttf'; MONOB='JBMono-700.ttf'; BEB='BebasNeue.woff'; BAR='Barlow-700.woff'; DMB='DMSans-700.woff'; DMR='DMSans-400.woff'
_fc={}
def f(n,s):
    k=(n,int(s))
    if k not in _fc: _fc[k]=ImageFont.truetype(F+n,int(s))
    return _fc[k]
def clamp(x,a=0,b=1): return max(a,min(b,x))
def expo(x): x=clamp(x); return 1 if x>=1 else 1-2**(-10*x)
def ease_io(x): x=clamp(x); return 4*x**3 if x<.5 else 1-(-2*x+2)**3/2
def back_out(x,s=1.2): x=clamp(x); return 1+(s+1)*(x-1)**3+s*(x-1)**2   # small settle, used only on heavy blocks
def lerp(a,b,t): return a+(b-a)*t
def A(c,a): return tuple(c[:3])+(int(clamp(a)*255),)
def appear(t,t0,dur=0.16): return expo((t-t0)/dur)
def win(t,t0,t1,fi=0.16,fo=0.14):   # alpha for an element living t0..t1
    if t<t0 or t>t1+fo: return 0
    return min(expo((t-t0)/fi), 1-clamp((t-t1)/fo))
GL=None
# ---------------- primitives ----------------
def txt(d,x,y,s,font,col,a=1.0,anchor=None):
    if a>0: d.text((x,y),s,font=font,fill=A(col,a),anchor=anchor)
def brackets(d,x0,y0,x1,y1,col,L=34,w=4):
    for (cx,cy,sx,sy) in [(x0,y0,1,1),(x1,y0,-1,1),(x0,y1,1,-1),(x1,y1,-1,-1)]:
        d.line([(cx,cy),(cx+sx*L,cy)],fill=col,width=w); d.line([(cx,cy),(cx,cy+sy*L)],fill=col,width=w)
def lit_bar(d,x0,y0,x1,y1,col,a=1.0):
    h=max(1,int(y1-y0))
    if x1<=x0: return
    for i in range(h):
        k=i/h; c=tuple(int(min(255,v*(1.18-0.36*k)+(40 if k<0.12 else 0))) for v in col)
        d.line([(x0,y0+i),(x1,y0+i)],fill=c+(int(255*a),))
def tag(d,x,y,label,col=RED,size=30,a=1.0,glow=True,anchor='l'):
    if a<=0: return x
    fn=f(MONO,size); tw=d.textlength(label,font=fn); h=size+16
    if anchor=='r': x=x-tw-24
    if anchor=='c': x=x-(tw+24)/2
    lit_bar(d,x,y,x+tw+24,y+h,col,a); d.text((x+12,y+5),label,font=fn,fill=A(INK if col in (VGOLD,GREEN,CYAN,AMBER) else WHITE,a))
    if GL and glow: GL.rectangle([x-4,y-4,x+tw+28,y+h+4],outline=A(col,a),width=8)
    return x+tw+24
def flag(d,box,t0,t,col=RED):
    p=expo((t-t0)/0.14)
    if p<=0: return
    x0,y0,x1,y1=box; brackets(d,x0,y0,x1,y1,A(col,p),26,6)
    if GL: brackets(GL,x0,y0,x1,y1,A(col,p),26,12)
    q=clamp((p-0.3)/0.7)
    if q>0:
        for seg in [((x0,y0),(lerp(x0,x1,q),y0)),((x1,y1),(lerp(x1,x0,q),y1)),((x0,y1),(x0,lerp(y1,y0,q))),((x1,y0),(x1,lerp(y0,y1,q)))]:
            d.line(seg,fill=A(col,1),width=3)
def arrow(d,x0,y0,x1,y1,col,w=5,a=1.0,L=18):
    d.line([(x0,y0),(x1,y1)],fill=A(col,a),width=w)
    ang=math.atan2(y1-y0,x1-x0)
    d.polygon([(x1,y1),(x1-L*math.cos(ang-0.45),y1-L*math.sin(ang-0.45)),(x1-L*math.cos(ang+0.45),y1-L*math.sin(ang+0.45))],fill=A(col,a))
def flow(d,x0,y0,x1,y1,t,col,n=5,speed=0.9,a=1.0,r=7):
    for k in range(n):
        p=(t*speed+k/n)%1
        x=lerp(x0,x1,p); y=lerp(y0,y1,p); fa=a*min(1,p*6,(1-p)*6)
        d.ellipse([x-r,y-r,x+r,y+r],fill=A(col,fa))
        if GL: GL.ellipse([x-r*2,y-r*2,x+r*2,y+r*2],fill=A(col,fa))
def check(d,x,y,col,s=1.0,a=1.0):
    d.line([(x,y+16*s),(x+10*s,y+28*s),(x+30*s,y+2*s)],fill=A(col,a),width=int(6*s))
    if GL: GL.line([(x,y+16*s),(x+10*s,y+28*s),(x+30*s,y+2*s)],fill=A(col,a),width=int(12*s))
def cross(d,x,y,col,s=1.0,a=1.0):
    d.line([(x,y),(x+28*s,y+28*s)],fill=A(col,a),width=int(6*s)); d.line([(x+28*s,y),(x,y+28*s)],fill=A(col,a),width=int(6*s))
    if GL: GL.line([(x,y),(x+28*s,y+28*s)],fill=A(col,a),width=12); GL.line([(x+28*s,y),(x,y+28*s)],fill=A(col,a),width=12)
def node(d,x0,y0,x1,y1,title,sub,col,a=1.0,dim=False,size=44):
    c=col if not dim else tuple(int(v*0.35) for v in col)
    d.rounded_rectangle([x0,y0,x1,y1],radius=14,fill=A((10,14,24),0.95*a),outline=A(c,a),width=4)
    if GL and not dim: GL.rounded_rectangle([x0,y0,x1,y1],radius=14,outline=A(col,a*0.8),width=8)
    fn=f(BEB,size); tw=d.textlength(title,font=fn); d.text(((x0+x1)/2-tw/2,y0+12),title,font=fn,fill=A(WHITE if not dim else (110,110,120),a))
    if sub:
        fs=f(MONO,22); sw=d.textlength(sub,font=fs); d.text(((x0+x1)/2-sw/2,y1-36),sub,font=fs,fill=A(c,a))
def kidney(d,cx,cy,s,col,a=1.0,fill=None):
    pts=[]
    for i in range(64):
        th=2*math.pi*i/64
        r=1.0-0.38*max(0,math.cos(th))**3      # notch on the right (hilum)
        pts.append((cx+s*0.62*r*math.cos(th), cy+s*0.95*r*math.sin(th)))
    if fill: d.polygon(pts,fill=A(fill,a))
    d.line(pts+[pts[0]],fill=A(col,a),width=5)
    if GL: GL.line(pts+[pts[0]],fill=A(col,a),width=10)
def frosted(im,box,dark=0.86,blur=10):
    x0,y0,x1,y1=[int(v) for v in box]; x0=max(0,x0); y0=max(0,y0); x1=min(W,x1); y1=min(H,y1)
    if x1<=x0 or y1<=y0: return
    reg=im.crop((x0,y0,x1,y1)).convert('RGB').filter(ImageFilter.GaussianBlur(blur))
    im.paste(Image.blend(reg,Image.new('RGB',reg.size,DEEP),dark).convert('RGBA'),(x0,y0))
def card(im,box,a,col=VGOLD,title=None,right=None,t=0,dark=0.9):
    """frosted inspection panel with brackets, header row"""
    if a<=0: return
    frosted(im,box,dark*a,10)
    d=ImageDraw.Draw(im,'RGBA'); x0,y0,x1,y1=box
    d.rectangle([x0,y0,x1,y1],outline=A(col,0.55*a),width=2); brackets(d,x0,y0,x1,y1,A(col,a),36,6)
    if GL: brackets(GL,x0,y0,x1,y1,A(col,a),36,12)
    if title:
        d.ellipse([x0+24,y0+24,x0+38,y0+38],fill=A(RED,a if int(t*4)%2==0 else a/3))
        txt(d,x0+52,y0+16,title,f(MONO,26),WHITE,a)
    if right:
        fr=f(MONO,26); tw=d.textlength(right,font=fr); txt(d,x1-26-tw,y0+16,right,fr,col,a)
# ---------------- background canvas (shown where footage moves away) ----------------
def make_bg():
    yy,xx=np.mgrid[0:H,0:W].astype(np.float32)
    g=np.exp(-(((xx-900)/700)**2+((yy-300)/700)**2))
    base=np.array(NAVY,np.float32)[None,None,:]+g[...,None]*np.array([22,14,4],np.float32)[None,None,:]
    rng=np.random.default_rng(3); base+=rng.normal(0,2.2,(H,W,1)).astype(np.float32)
    return Image.fromarray(np.clip(base,0,255).astype(np.uint8)).convert('RGBA')
BG=make_bg()
# ---------------- footage layout ----------------
FACE=(540,1060)
# (t, z, dx, dy, ease)   ease 0 = hard step (reads like a cut), >0 = move duration
KEYS=[(0,1.0,0,0,0),(4.60,1.08,0,0,0),(10.62,1.0,0,0,0),
      (15.40,1.0,0,170,0.35),(19.62,1.0,0,0,0.30),
      (34.42,1.10,0,0,0),(36.44,1.18,0,0,0),(37.32,1.0,0,0,0),
      (40.50,1.0,0,-400,0.40),(46.62,1.0,250,0,0.40),(51.22,1.0,0,0,0.32),
      (54.28,1.06,0,0,0),(59.56,1.0,0,0,0),(68.06,1.08,0,0,0),(71.54,1.0,0,0,0)]
def layout(t):
    cur=KEYS[0][1:4]
    for i,(tk,z,dx,dy,e) in enumerate(KEYS):
        if t<tk: break
        prev=cur
        if e>0 and t<tk+e:
            p=ease_io((t-tk)/e); cur=tuple(lerp(a,b,p) for a,b in zip(prev,(z,dx,dy)))
        else: cur=(z,dx,dy)
    return cur
PIP_IN,PIP_OUT=28.15,34.30   # footage shrinks into a circle during the eGFR scene
def pip_q(t):
    if t<PIP_IN or t>PIP_OUT+0.35: return 0
    return min(ease_io((t-PIP_IN)/0.38), 1-ease_io((t-PIP_OUT)/0.32))
def place_footage(src,t):
    z,dx,dy=layout(t); q=pip_q(t)
    if q>0:
        im=BG.copy()
        # stage 1: iris closes on full-size footage; stage 2: circle + footage shrink together (circle stays inside footage)
        if q<0.35: k=ease_io(q/0.35); zc=1.0; r=lerp(1150,540,k); cx,cy=FACE[0]+dx,FACE[1]+dy
        else: k=ease_io((q-0.35)/0.65); zc=lerp(1.0,0.46,k); r=lerp(540,178,k); cx,cy=lerp(FACE[0]+dx,835,k),lerp(FACE[1]+dy,640,k)
        sm=src.resize((int(W*zc),int(H*zc)),Image.BICUBIC)
        ox=int(cx-FACE[0]*zc); oy=int(cy-FACE[1]*zc)
        m=Image.new('L',(W,H),0); ImageDraw.Draw(m).ellipse([cx-r,cy-r,cx+r,cy+r],fill=255)
        lay=Image.new('RGBA',(W,H),(0,0,0,0)); lay.paste(sm.convert('RGBA'),(ox,oy))
        im.paste(lay,(0,0),Image.composite(lay.split()[3],Image.new('L',(W,H),0),m))
        d=ImageDraw.Draw(im,'RGBA')
        if q>0.6:
            a=(q-0.6)/0.4; d.ellipse([cx-r-4,cy-r-4,cx+r+4,cy+r+4],outline=A(VGOLD,a),width=5)
            if GL: GL.ellipse([cx-r-6,cy-r-6,cx+r+6,cy+r+6],outline=A(VGOLD,a),width=12)
        return im
    if abs(z-1)<1e-4 and dx==0 and dy==0: return src.convert('RGBA')
    im=BG.copy()
    sm=src.resize((int(round(W*z)),int(round(H*z))),Image.BICUBIC) if abs(z-1)>1e-4 else src
    ox=int(round(FACE[0]-FACE[0]*z+dx)); oy=int(round(FACE[1]-FACE[1]*z+dy))
    im.paste(sm.convert('RGB'),(ox,oy)); return im
def cap_y(t):
    z,dx,dy=layout(t)
    if dy>0: return lerp(1450,975,dy/170)
    if dy<0: return lerp(1450,1232,-dy/400)
    return 1450
# ================= scenes =================
TOP=(56,392,1024,880)     # the free zone over the headliner (face starts ~900)
# --- 0. red alert pulse (frame edge) ---
def s_alert(im,d,t):
    if not 1.55<=t<3.1: return
    k=t-1.60; a=max(0,math.cos(k*math.pi/0.55))**2 if k<1.1 else 0
    a=max(a,0.0); fade=1-clamp((t-2.8)/0.3)
    a=a*fade
    if a<=0.01: return
    for i,w_ in enumerate([10,22]):
        d.rectangle([8+i*0,0,W-1,H-1],outline=A(RED,a*(0.9 if i==0 else 0.25)),width=w_)
    GL.rectangle([8,0,W-1,H-1],outline=A(RED,a),width=40)
    brackets(d,40,400,W-40,H-440,A(RED,a),70,8)
    tag(d,W-60,1300,'RESULT FLAGGED',RED,28,a*1.4,anchor='r')
# --- 1. lab document (top card) ---
DOC=None
def make_doc():
    im=Image.new('RGB',(860,330),(250,250,248)); d=ImageDraw.Draw(im)
    d.rectangle([0,0,860,66],fill=(16,24,48)); d.text((22,14),'LAB REPORT · RENAL PANEL',font=f(MONO,30),fill=WHITE)
    d.text((838,20),'EXAMPLE',font=f(MONO,22),fill=(150,160,190),anchor='ra')
    d.text((22,80),'TEST',font=f(MONO,20),fill=(130,130,140)); d.text((440,80),'RESULT',font=f(MONO,20),fill=(130,130,140)); d.text((640,80),'REF RANGE',font=f(MONO,20),fill=(130,130,140))
    rows=[('BUN','17','mg/dL','7–25',''),('Creatinine, Serum','1.6','mg/dL','0.6–1.3','H')]
    for i,(k,v,u,rr,fl) in enumerate(rows):
        y=118+i*100
        d.text((22,y),k,font=f(DMR,34),fill=(60,64,76)); d.text((22,y+44),'S' if i==0 else 'SERUM · ENZYMATIC',font=f(MONO,18),fill=(140,140,150))
        d.text((440,y),v,font=f(DMB,48),fill=INK if not fl else (210,10,20)); d.text((440+d.textlength(v,font=f(DMB,48))+8,y+18),u,font=f(DMR,24),fill=(100,100,110))
        d.text((640,y+10),rr,font=f(DMR,30),fill=(90,90,100))
        if fl: d.text((806,y+2),fl,font=f(DMB,48),fill=(210,10,20))
        d.line([(16,y+88),(844,y+88)],fill=(222,222,226),width=2)
    return im.convert('RGBA')
def s_doc(im,d,t):
    global DOC
    T0,T1=10.62,15.40
    if not T0<=t<T1+0.3: return
    if DOC is None: DOC=make_doc()
    p=expo((t-T0)/0.30); out=clamp((t-T1)/0.25)
    y=lerp(250,470,p)-out*80; a=p*(1-out)
    sh=Image.new('RGBA',(900,370),(0,0,0,0)); ImageDraw.Draw(sh).rectangle([20,24,880,354],fill=(0,0,0,int(150*a))); sh=sh.filter(ImageFilter.GaussianBlur(14))
    im.alpha_composite(sh,(90,int(y)-4))
    doc=DOC.copy(); doc.putalpha(int(255*a));
    if p<1: doc=doc.rotate(lerp(-3,0,p),resample=Image.BICUBIC,expand=False)
    im.alpha_composite(doc,(110,int(y)))
    d=ImageDraw.Draw(im,'RGBA')
    if t>=11.38 and out<1:
        flag(d,(118,y+208,970,y+312),11.38,t); tag(d,970,y-50,'FLAGGED HIGH',RED,28,appear(t,11.42)*(1-out),anchor='r')
    if t>=14.44 and out<1:
        a2=appear(t,14.44)*(1-out); tag(d,130,y+346,'FLAG ≠ FAILURE',VGOLD,30,a2)
        tag(d,470,y+346,'NOT A DIAGNOSIS',RED,30,appear(t,14.88)*(1-out))
# --- 2. mechanism (split screen top) ---
def s_mech(im,d,t):
    T0,T1=15.40,19.62
    q=0
    if T0<=t<T1+0.30: q=min(ease_io((t-T0)/0.35),1-ease_io((t-T1)/0.30))
    if q<=0: return
    yb=lerp(0,885,q)       # panel bottom edge slides down with the footage
    im.alpha_composite(BG.crop((0,0,W,int(yb))),(0,0)) if yb>2 else None
    d=ImageDraw.Draw(im,'RGBA'); d.line([(0,yb),(W,yb)],fill=A(VGOLD,1),width=4); GL.line([(0,yb),(W,yb)],fill=A(VGOLD,1),width=10)
    o=yb-885     # content rides with the panel
    a=clamp((q-0.5)*2)
    txt(d,64,410+o,'MECHANISM · WHERE CREATININE COMES FROM',f(MONO,28),VGOLD,a)
    # nodes
    c1=appear(t,16.46); c2=appear(t,15.50); c3=appear(t,17.90)
    node(d,64,480+o,330,610+o,'CREATINE','MUSCLE',CYAN,a*max(0.35,c1),dim=c1<0.5)
    node(d,410,480+o,700,610+o,'CREATININE','WASTE PRODUCT',VGOLD,a*max(0.35,c2))
    cx,cy=880,545+o; kidney(d,cx-50,cy,70,CYAN if c3>0.5 else (60,70,80),a,fill=(10,14,24)); kidney(d,cx+50,cy,70,CYAN if c3>0.5 else (60,70,80),a,fill=(10,14,24))
    txt(d,cx,cy+88,'KIDNEYS',f(MONO,22),CYAN if c3>0.5 else DIM,a,anchor='ma')
    if t>=16.88:
        b=appear(t,16.88); arrow(d,336,545+o,402,545+o,CYAN,5,a*b); flow(d,336,545+o,398,545+o,t,CYAN,3,a=a*b)
        txt(d,369,620+o,'METABOLISM',f(MONO,20),CYAN,a*b,anchor='ma')
    if t>=17.90:
        b=appear(t,17.90); arrow(d,706,545+o,786,545+o,VGOLD,5,a*b); flow(d,706,545+o,780,545+o,t,VGOLD,3,a=a*b)
    if t>=18.42:
        b=appear(t,18.42); arrow(d,880,650+o,880,760+o,VGOLD,5,a*b); flow(d,880,650+o,880,756+o,t*1.3,VGOLD,4,a=a*b)
        tag(d,880,770+o,'CLEARED FROM BLOOD',VGOLD,26,a*b,anchor='c')
    # blood level line
    if t>=18.98:
        b=appear(t,18.98,0.3); txt(d,64,700+o,'IN BLOOD',f(MONO,24),MUTED,a*b)
        lv=lerp(0.5,0.5,0); d.rectangle([64,740+o,620,770+o],outline=A((70,74,90),a*b),width=2); lit_bar(d,67,743+o,lerp(67,617,0.45),767+o,VGOLD,a*b)
        txt(d,64,790+o,'= WHAT YOUR LAB MEASURES',f(MONO,24),CREAM,a*b)
# --- 3. side rails + vertical gauge ---
def s_rails(im,d,t):
    T0,T1=20.10,27.98
    if not T0<=t<T1+0.3: return
    out=clamp((t-T1)/0.22)
    chips=[('MUSCLE MASS',21.40,'+'),('CREATINE',22.16,'+'),('HARD TRAINING',23.00,'+')]
    lvl=0.42
    for i,(nm,tt,_) in enumerate(chips):
        if t<tt: continue
        p=expo((t-tt)/0.18); x=lerp(-280,44,p)-out*320; y=1000+i*118
        frosted(im,(max(0,x),y,x+260,y+92),0.85,8); d=ImageDraw.Draw(im,'RGBA')
        d.rectangle([x,y,x+7,y+92],fill=A(VGOLD,1));
        txt(d,x+24,y+10,'0'+str(i+1),f(MONO,22),VGOLD,1); txt(d,x+24,y+38,nm,f(BEB,46),WHITE,1)
        if GL: GL.rectangle([x,y,x+7,y+92],fill=A(VGOLD,1))
        lvl+=0.15*expo((t-tt-0.1)/0.5)
    d=ImageDraw.Draw(im,'RGBA')
    # gauge (right rail)
    ga=appear(t,T0,0.25)*(1-out); gx0,gx1,gy0,gy1=900,990,1000,1370
    if ga>0:
        frosted(im,(gx0-30,gy0-70,gx1+40,gy1+20),0.85*ga,8); d=ImageDraw.Draw(im,'RGBA')
        txt(d,(gx0+gx1)/2,gy0-60,'CREATININE',f(MONO,20),CREAM,ga,anchor='ma')
        d.rectangle([gx0,gy0,gx1,gy1],outline=A((90,94,110),ga),width=3)
        ref=gy1-(gy1-gy0)*0.62
        d.rectangle([gx0+3,ref,gx1-3,gy1-3],fill=A((30,255,110),0.10*ga))
        d.line([(gx0-14,ref),(gx1+14,ref)],fill=A(WHITE,ga),width=3); txt(d,gx0-18,ref-12,'REF',f(MONO,18),WHITE,ga,anchor='ra')
        lv=lvl if t<24.22 else lvl+0.04*expo((t-24.22)/0.4)
        top=gy1-(gy1-gy0)*min(0.95,lv); col=RED if top<ref else VGOLD
        lit_bar(d,gx0+6,top,gx1-6,gy1-6,col,ga)
        if GL: GL.rectangle([gx0+6,top,gx1-6,gy1-6],fill=A(col,ga*0.7))
        if t>=24.22 and top<ref: tag(d,gx1+8,top-8,'H',RED,30,appear(t,24.22)*(1-out),anchor='r') if False else tag(d,gx0-6,top-56,'HIGH',RED,26,appear(t,24.3)*(1-out),anchor='r')
        if t>=25.28:
            b=appear(t,25.28)*(1-out); arrow(d,(gx0+gx1)/2,top+90,(gx0+gx1)/2,top+20,WHITE,6,b)
    if t>=27.42:
        b=appear(t,27.42)*(1-out); x=lerp(1100,560,expo((t-27.42)/0.2))
        frosted(im,(x-20,1250,x+330,1360),0.85*b,8) if b>0 else None; d=ImageDraw.Draw(im,'RGBA')
        kidney(d,x+20,1305,30,GREEN,b); kidney(d,x+62,1305,30,GREEN,b)
        txt(d,x+100,1262,'KIDNEY DAMAGE',f(MONO,22),CREAM,b); txt(d,x+100,1292,'NOT SHOWN',f(BEB,52),GREEN,b)
# --- 4. eGFR calculator (full graphic + PiP face) ---
def s_egfr(im,d,t):
    q=pip_q(t)
    if q<=0: return
    a=clamp((q-0.55)/0.45)
    if a<=0: return
    txt(d,64,410,'eGFR · ESTIMATED, NOT MEASURED',f(MONO,28),VGOLD,a*appear(t,28.5))
    # formula box
    fa=a*appear(t,29.44,0.2)
    if fa>0:
        d.rounded_rectangle([64,470,640,700],radius=16,fill=A((10,14,24),0.95*fa),outline=A(CYAN,fa),width=4)
        if GL: GL.rounded_rectangle([64,470,640,700],radius=16,outline=A(CYAN,fa),width=8)
        txt(d,92,486,'eGFR =',f(BEB,70),WHITE,fa)
        txt(d,92,566,'FORMULA (',f(MONO,30),MUTED,fa)
        ca=appear(t,31.92,0.12)
        cr_col=VGOLD if ca>0.5 else (120,110,80)
        x=92+d.textlength('FORMULA (',font=f(MONO,30))
        tag(d,x+4,560,'CREATININE',cr_col,30,fa,glow=ca>0.5); txt(d,92,620,'   + age + sex )',f(MONO,30),MUTED,fa)
    # creatinine input counter
    if t>=31.92:
        b=appear(t,31.92); v=lerp(1.0,1.6,ease_io((t-31.95)/1.2))
        txt(d,64,724,'INPUT',f(MONO,24),MUTED,b*a); txt(d,64,752,f'CREATININE {v:.1f}',f(BEB,58),VGOLD,b*a); txt(d,330,770,'mg/dL',f(MONO,22),MUTED,b*a)
    # semicircle gauge
    ga=a*appear(t,30.24,0.25)
    if ga>0:
        cx,cy,R=540,1180,300
        zones=[(0,60,RED),(60,90,AMBER),(90,120,GREEN)]
        for z0,z1,c in zones:
            a0=180+z0/120*180; a1=180+z1/120*180
            d.arc([cx-R,cy-R,cx+R,cy+R],a0,a1,fill=A(c,ga),width=34)
            if GL: GL.arc([cx-R,cy-R,cx+R,cy+R],a0,a1,fill=A(c,ga*0.8),width=40)
        for v,lab in [(0,'0'),(60,'60'),(90,'90'),(120,'120')]:
            ang=math.radians(180+v/120*180); x=cx+(R+40)*math.cos(ang); y=cy+(R+40)*math.sin(ang)
            txt(d,x,y-14,lab,f(MONO,24),MUTED,ga,anchor='ma')
        val=98 if t<32.0 else lerp(98,58,ease_io((t-32.0)/1.6))
        ang=math.radians(180+val/120*180)
        d.line([(cx,cy),(cx+(R-50)*math.cos(ang),cy+(R-50)*math.sin(ang))],fill=A(WHITE,ga),width=8)
        GL.line([(cx,cy),(cx+(R-50)*math.cos(ang),cy+(R-50)*math.sin(ang))],fill=A(WHITE,ga*0.6),width=12)
        d.ellipse([cx-18,cy-18,cx+18,cy+18],fill=A(WHITE,ga))
        col=GREEN if val>=90 else (AMBER if val>=60 else RED)
        txt(d,cx,cy-150,f'{int(round(val))}',f(BEB,120),col,ga,anchor='ma')
        txt(d,cx,cy+30,'eGFR',f(MONO,26),MUTED,ga,anchor='ma')
        txt(d,cx-R,cy+40,'EXAMPLE',f(MONO,20),DIM,ga)
    if t>=33.56: tag(d,540,1330,'LOOKS WORSE',RED,32,a*appear(t,33.56),anchor='c')
# --- 5. one marker in isolation (top card) ---
ROWS=['CREATININE','eGFR','CYSTATIN C','URINE ALB : CREAT','BLOOD PRESSURE']
def s_iso(im,d,t):
    T0,T1=37.40,40.80
    if not T0<=t<T1+0.3: return
    z,dx,dy=layout(t); o=dy  # rides up with the footage on the hand-off
    a=appear(t,T0,0.2)*(1-clamp((t-T1)/0.2))
    box=(56,392+o,1024,880+o); card(im,box,a,VGOLD,'YOUR KIDNEY PANEL','1 / 5' if t<40.3 else '5 / 5',t)
    d=ImageDraw.Draw(im,'RGBA')
    iso=t>=37.82 and t<40.30
    for i,nm in enumerate(ROWS):
        y=460+o+i*80; ra=a*appear(t,T0+0.06*i,0.15)
        dim=iso and i>0
        col=(70,72,80) if dim else (WHITE if i>0 else VGOLD)
        txt(d,96,y,nm,f(BEB,54),col,ra)
        # mini bar
        d.rectangle([600,y+16,960,y+40],outline=A((60,64,80),ra),width=2)
        if not dim: lit_bar(d,603,y+19,lerp(603,957,[0.82,0.45,0.5,0.4,0.55][i]),y+37,[RED,AMBER,GREEN,GREEN,GREEN][i],ra)
    if t>=38.40 and iso: tag(d,1000,460+o-6,'ONLY ONE READ',RED,26,appear(t,38.40),anchor='r') if False else None
    if t>=39.90 and iso:
        flag(d,(80,452+o,980,524+o),39.90,t); tag(d,980,530+o,'IN ISOLATION',RED,28,appear(t,39.95),anchor='r')
# --- 6. dashboard (split screen bottom) ---
def s_dash(im,d,t):
    T0,T1=40.50,46.62
    q=0
    if T0<=t<T1+0.22: q=min(ease_io((t-T0)/0.40),1-ease_io((t-(T1-0.12))/0.22))
    if q<=0: return
    yt=lerp(H,1150,q)
    im.alpha_composite(BG.crop((0,int(yt),W,H)),(0,int(yt)))
    d=ImageDraw.Draw(im,'RGBA'); d.line([(0,yt),(W,yt)],fill=A(VGOLD,1),width=4); GL.line([(0,yt),(W,yt)],fill=A(VGOLD,1),width=10)
    o=yt-1150
    tiles=[('CYSTATIN C',41.06,CYAN),('ALB : CREAT',42.12,VGOLD),('BLOOD PRESS.',44.60,RED),('TRENDS',45.56,GREEN)]
    for i,(nm,tt,col) in enumerate(tiles):
        x0=40+i*252; y0=1300+o; x1=x0+236; y1=y0+200
        p=expo((t-tt)/0.2) if t>=tt else 0
        on=p>0
        c=col if on else (50,54,66)
        yy=y0+lerp(30,0,p)
        d.rounded_rectangle([x0,yy,x1,yy+200],radius=14,fill=A((10,14,24),0.96),outline=A(c,1),width=3)
        if GL and on: GL.rounded_rectangle([x0,yy,x1,yy+200],radius=14,outline=A(col,p),width=8)
        txt(d,x0+16,yy+14,nm,f(MONO,22),c if on else (90,92,104),1)
        if not on: continue
        cx=(x0+x1)/2; cy=yy+120
        if i==0:   # filtration funnel
            d.polygon([(cx-60,cy-50),(cx+60,cy-50),(cx+12,cy+10),(cx-12,cy+10)],outline=A(col,p)); d.line([(cx-60,cy-50),(cx+60,cy-50),(cx+12,cy+10),(cx+12,cy+50)],fill=A(col,p),width=4); d.line([(cx-60,cy-50),(cx-12,cy+10),(cx-12,cy+50)],fill=A(col,p),width=4)
            flow(d,cx,cy-40,cx,cy+56,t,col,4,1.2,p,5)
        elif i==1: # ratio
            txt(d,cx,cy-62,'ALBUMIN',f(BEB,40),WHITE,p,anchor='ma'); d.line([(cx-80,cy-12),(cx+80,cy-12)],fill=A(col,p),width=5)
            txt(d,cx,cy-2,'CREATININE',f(BEB,40),WHITE,p,anchor='ma')
            if t>=43.86: tag(d,cx,cy+44,'RATIO',col,22,appear(t,43.86),anchor='c')
        elif i==2: # pressure trace
            pts=[]
            for k in range(60):
                xx=x0+18+k*(200/59); ph=(k/59*3+t*1.2)%1
                yv=cy+20-(46*math.exp(-((ph-0.2)/0.06)**2)+18*math.exp(-((ph-0.45)/0.08)**2))
                pts.append((xx,yv))
            n=int(60*clamp((t-tt)/0.6))
            if n>1: d.line(pts[:n],fill=A(col,p),width=4); GL.line(pts[:n],fill=A(col,p),width=8)
        else:      # sparkline
            vals=[0.35,0.5,0.42,0.62,0.58]; pts=[(x0+28+k*45,cy+40-v*90) for k,v in enumerate(vals)]
            m=clamp((t-tt)/0.8)*4
            for k in range(4):
                if m>k:
                    e=min(1,m-k); b_=(lerp(pts[k][0],pts[k+1][0],e),lerp(pts[k][1],pts[k+1][1],e)); d.line([pts[k],b_],fill=A(col,1),width=4); GL.line([pts[k],b_],fill=A(col,1),width=8)
            for k in range(5):
                if m>=k: d.ellipse([pts[k][0]-6,pts[k][1]-6,pts[k][0]+6,pts[k][1]+6],fill=A(WHITE,1))
            if t>=45.88: txt(d,x0+18,yy+168,'OVER TIME',f(MONO,20),col,appear(t,45.88))
# --- 7. side panel bar chart ---
def s_bars(im,d,t):
    T0,T1=46.62,51.22
    q=0
    if T0<=t<T1+0.32: q=min(ease_io((t-T0)/0.40),1-ease_io((t-T1)/0.32))
    if q<=0: return
    xr=lerp(0,490,q)
    im.alpha_composite(BG.crop((0,0,int(xr),H)),(0,0)) if xr>2 else None
    d=ImageDraw.Draw(im,'RGBA'); d.rectangle([xr-4,0,xr,H],fill=A(VGOLD,1)); GL.rectangle([xr-6,0,xr+2,H],fill=A(VGOLD,1))
    o=xr-490; a=clamp((q-0.5)*2)
    txt(d,56+o,410,'WHICH MARKER',f(MONO,26),VGOLD,a); txt(d,56+o,444,'MOVES WITH MUSCLE?',f(MONO,26),VGOLD,a)
    # muscle slider
    mu=0.15 if t<49.0 else lerp(0.15,0.95,ease_io((t-49.0)/1.6))
    txt(d,56+o,520,'MUSCLE MASS',f(BEB,44),WHITE,a)
    d.rectangle([56+o,580,440+o,596],fill=A((50,54,66),a)); lit_bar(d,56+o,580,lerp(56,440,mu)+o,596,VGOLD,a)
    kx=lerp(56,440,mu)+o; d.ellipse([kx-16,572,kx+16,604],fill=A(WHITE,a))
    base=1300; top=700
    bars=[('CREATININE',47.70,0.32+0.5*clamp((mu-0.15)/0.8),RED),('CYSTATIN C',46.82,0.40,CYAN)]
    d.line([(56+o,base),(440+o,base)],fill=A((90,94,110),a),width=3)
    for i,(nm,tt,v,col) in enumerate(bars):
        if t<tt: continue
        p=expo((t-tt)/0.35); x0=80+o+i*190; x1=x0+140
        c=col if not (i==0 and v<0.45) else AMBER
        h=(base-top)*v*p; lit_bar(d,x0,base-h,x1,base,c,a); GL.rectangle([x0,base-h,x1,base],fill=A(c,a*0.6))
        txt(d,(x0+x1)/2,base+16,nm,f(MONO,22),CREAM,a,anchor='ma')
    if t>=50.38: tag(d,82+o,base-(base-top)*0.82-64,'RISES',RED,26,a*appear(t,50.38))
    if t>=49.6: tag(d,272+o,base-(base-top)*0.40-64,'STABLE',CYAN,26,a*appear(t,49.6))
    if t>=48.16: txt(d,56+o,1360,'CYSTATIN C = FILTRATION',f(MONO,22),CYAN,a*appear(t,48.16)); txt(d,56+o,1392,'WITHOUT THE MUSCLE BIAS',f(MONO,22),CYAN,a*appear(t,48.4))
# --- 8. floating urine test strip ---
def s_strip(im,d,t):
    T0,T1=51.36,54.20
    if not T0<=t<T1+0.25: return
    p=expo((t-T0)/0.28); out=clamp((t-T1)/0.22); a=p*(1-out)
    x0=lerp(1100,120,p)-out*200; y0=560; x1=x0+840
    # shadow + strip
    sh=Image.new('RGBA',(900,140),(0,0,0,0)); ImageDraw.Draw(sh).rounded_rectangle([30,40,870,110],radius=10,fill=(0,0,0,int(170*a))); sh=sh.filter(ImageFilter.GaussianBlur(12))
    im.alpha_composite(sh,(int(x0)-30,y0-10)); d=ImageDraw.Draw(im,'RGBA')
    d.rounded_rectangle([x0,y0+30,x1,y0+100],radius=8,fill=A((236,236,230),a))
    txt(d,x0+20,y0-30,'URINE · ALBUMIN SCREEN',f(MONO,26),VGOLD,a)
    pads=[('GLU',(150,190,210)),('BIL',(230,220,180)),('KET',(230,190,180)),('ALB',(206,214,90)),('pH',(240,170,90)),('BLD',(240,200,70))]
    for i,(nm,c) in enumerate(pads):
        px=x0+300+i*86; col=c
        if nm=='ALB' and t>=52.62: col=tuple(int(lerp(a_,b_,expo((t-52.62)/0.6))) for a_,b_ in zip(c,(40,150,120)))
        d.rectangle([px,y0+42,px+60,y0+88],fill=A(col,a)); txt(d,px+30,y0+108,nm,f(MONO,20),CREAM if nm!='ALB' else VGOLD,a,anchor='ma')
    # scan sweep
    if 51.90<=t<52.70:
        sx=lerp(x0+280,x1,clamp((t-51.9)/0.7)); d.line([(sx,y0+10),(sx,y0+120)],fill=A(CYAN,a),width=4); GL.line([(sx,y0+10),(sx,y0+120)],fill=A(CYAN,a),width=16)
    if t>=52.62:
        px=x0+300+3*86; flag(d,(px-10,y0+32,px+70,y0+98),52.62,t)
    if t>=53.56: tag(d,x1,y0+150,'POTENTIAL DAMAGE SIGNAL',RED,28,appear(t,53.56)*(1-out),anchor='r')
# --- 9. spectrum ---
def s_spec(im,d,t):
    T0,T1=54.30,59.50
    if not T0<=t<T1+0.25: return
    a=appear(t,T0,0.2)*(1-clamp((t-T1)/0.2))
    frosted(im,(56,430,1024,760),0.84*a,10); d=ImageDraw.Draw(im,'RGBA')
    x0,x1,y=110,970,560
    cols=[RED,AMBER,GREEN,AMBER,RED]
    for i in range(x1-x0):
        k=i/(x1-x0)*4; j=min(3,int(k)); e=k-j; c=tuple(int(lerp(cols[j][m],cols[j+1][m],e)) for m in range(3))
        d.line([(x0+i,y),(x0+i,y+30)],fill=A(c,a))
    GL.rectangle([x0,y,x1,y+30],outline=A(WHITE,a*0.3),width=4)
    txt(d,x0,y-64,'PANIC',f(BEB,52),RED,a); txt(d,(x0+x1)/2,y-64,'VERIFY',f(BEB,52),GREEN,a,anchor='ma'); txt(d,x1,y-64,'IGNORE',f(BEB,52),RED,a,anchor='ra')
    txt(d,x0,y+50,'"MY KIDNEYS ARE DONE"',f(MONO,20),MUTED,a); txt(d,x1-240,y+50,'"IT\'S JUST MUSCLE"',f(MONO,20),MUTED,a,anchor='ra')
    m=0.04 if t<54.68 else lerp(0.04,0.96,ease_io((t-54.68)/0.9))
    mx=lerp(x0,x1,m); d.polygon([(mx-16,y-12),(mx+16,y-12),(mx,y+8)],fill=A(WHITE,a)); d.line([(mx,y-2),(mx,y+40)],fill=A(WHITE,a),width=4)
    GL.line([(mx,y-14),(mx,y+40)],fill=A(WHITE,a),width=10)
    if t>=57.62: flag(d,(x1-200,y-74,x1+20,y+44),57.62,t)
    if t>=57.62: tag(d,x1+20,y+92,'SAME MISTAKE',RED,28,appear(t,57.66)*a,anchor='r')
# --- 10. flag vs diagnosis comparison ---
def s_cmp(im,d,t):
    T0,T1=59.56,67.95
    if not T0<=t<T1+0.25: return
    a=appear(t,T0,0.2)*(1-clamp((t-T1)/0.2))
    card(im,(56,392,1024,880),a,VGOLD,'LAB FLAG  vs  DIAGNOSIS',None,t)
    d=ImageDraw.Draw(im,'RGBA')
    # columns
    for i,(hdr,col,tt) in enumerate([('LAB FLAG',RED,60.50),('DIAGNOSIS',VGOLD,64.24)]):
        x0=86+i*470; p=expo((t-tt)/0.3) if t>=tt else 0
        d.line([(x0,460),(lerp(x0,x0+430,p),460)],fill=A(col,a),width=5)
        if GL and p>0: GL.line([(x0,460),(lerp(x0,x0+430,p),460)],fill=A(col,a),width=10)
        txt(d,x0,476,hdr,f(MONO,26),col,a*p)
    if t>=60.50:
        b=a*appear(t,60.50); txt(d,86,516,'CREATININE',f(BEB,62),WHITE,b); tag(d,404,522,'H',RED,40,b)
    if t>=61.56:
        b=a*appear(t,61.56); txt(d,86,600,'REFERENCE RANGE',f(MONO,22),MUTED,b)
        d.rectangle([86,636,470,660],outline=A((90,94,110),b),width=2); d.rectangle([150,639,370,657],fill=A(GREEN,0.35*b))
        mx=lerp(150,440,expo((t-61.9)/0.5)); d.polygon([(mx-12,624),(mx+12,624),(mx,644)],fill=A(RED,b))
        txt(d,86,676,'OUTSIDE A POPULATION RANGE',f(MONO,20),CREAM,b)
    if t>=64.24:
        b=a*appear(t,64.24); txt(d,556,516,'KIDNEY FAILURE',f(BEB,62),(120,120,130),b)
        txt(d,556,600,'NEEDS: REPEAT LABS',f(MONO,22),MUTED,b); txt(d,556,632,'CYSTATIN C · UACR · TREND',f(MONO,22),MUTED,b); txt(d,556,664,'+ A CLINICIAN',f(MONO,22),MUTED,b)
    if t>=64.90:
        b=a*appear(t,64.90,0.1); cross(d,920,520,RED,1.4,b); tag(d,556,700,'NOT MADE FROM ONE FLAG',RED,24,b)
    # don't ignore row
    if t>=67.40:
        b=a*appear(t,67.40,0.12)
        d.line([(86,770),(994,770)],fill=A((70,74,90),b),width=2)
        x=tag(d,86,792,'IGNORE IT',(90,90,100),30,b,glow=False); d.line([(80,814),(x+6,814)],fill=A(RED,b),width=5)
        tag(d,x+30,792,'RETEST · FULL PANEL',GREEN,30,a*appear(t,67.56))
# --- 11. radar: all markers at once ---
RAD=['CREATININE','eGFR','CYSTATIN C','UACR','BP','TREND']
def s_radar(im,d,t):
    T0,T1=68.06,71.50
    if not T0<=t<T1+0.25: return
    a=appear(t,T0,0.2)*(1-clamp((t-T1)/0.2))
    frosted(im,(56,392,1024,880),0.86*a,10); d=ImageDraw.Draw(im,'RGBA')
    brackets(d,56,392,1024,880,A(VGOLD,a),36,6); GL and brackets(GL,56,392,1024,880,A(VGOLD,a),36,12)
    txt(d,86,410,'FULL PICTURE',f(MONO,26),VGOLD,a)
    cx,cy,R=560,640,170
    ax=[(cx+R*math.cos(-math.pi/2+i*math.pi/3),cy+R*math.sin(-math.pi/2+i*math.pi/3)) for i in range(6)]
    g=clamp((t-68.42)/0.5)
    for ring in (0.33,0.66,1.0):
        pts=[(cx+(x-cx)*ring*g,cy+(y-cy)*ring*g) for x,y in ax]; d.line(pts+[pts[0]],fill=A((70,74,90),a),width=2)
    for i,(x,y) in enumerate(ax):
        d.line([(cx,cy),(lerp(cx,x,g),lerp(cy,y,g))],fill=A((70,74,90),a),width=2)
        lx=cx+(x-cx)*1.28; ly=cy+(y-cy)*1.22-14
        lit=t>=69.80+0.12*i
        txt(d,lx,ly,RAD[i],f(MONO,22),VGOLD if lit else MUTED,a*g,anchor='ma')
    vals=[0.78,0.55,0.5,0.45,0.5,0.6]
    pg=clamp((t-68.94)/0.6)
    if pg>0:
        pts=[(cx+(x-cx)*v*pg,cy+(y-cy)*v*pg) for (x,y),v in zip(ax,vals)]
        fa=0.16 if t<70.78 else lerp(0.16,0.30,expo((t-70.78)/0.3))
        d.polygon(pts,fill=A(VGOLD,fa*a)); d.line(pts+[pts[0]],fill=A(VGOLD,a),width=4); GL.line(pts+[pts[0]],fill=A(VGOLD,a),width=10)
        for i,p_ in enumerate(pts):
            if t>=69.80+0.12*i: d.ellipse([p_[0]-9,p_[1]-9,p_[0]+9,p_[1]+9],fill=A(WHITE,a))
    if t>=70.78: tag(d,994,830,'READ TOGETHER',VGOLD,28,a*appear(t,70.78),anchor='r')
    if t>=68.94: tag(d,86,830,'RATIOS',CYAN,28,a*appear(t,68.94))
# --- 12. CTA: checklist + comment pill ---
LOGO=None
CHK=['CREATININE · IN CONTEXT','eGFR · HOW IT\'S CALCULATED','CYSTATIN C','URINE ALBUMIN : CREATININE','BLOOD PRESSURE','TRENDS OVER TIME']
def s_cta(im,d,t):
    global LOGO
    T0=71.54
    if t<T0: return
    a=appear(t,T0,0.25)
    frosted(im,(56,392,1024,880),0.88*a,10); d=ImageDraw.Draw(im,'RGBA')
    brackets(d,56,392,1024,880,A(VGOLD,a),36,6); brackets(GL,56,392,1024,880,A(VGOLD,a),36,12)
    if LOGO is None:
        lg=Image.open(T+'logo.jpg').convert('RGB'); s=min(lg.size); lg=lg.crop(((lg.width-s)//2,(lg.height-s)//2,(lg.width+s)//2,(lg.height+s)//2)).resize((110,110),Image.LANCZOS)
        m=Image.new('L',(110,110),0); ImageDraw.Draw(m).ellipse([0,0,109,109],fill=255); lg.putalpha(m); LOGO=lg
    lg=LOGO.copy(); lg.putalpha(lg.split()[3].point(lambda v:int(v*a))); im.alpha_composite(lg,(84,414)); d=ImageDraw.Draw(im,'RGBA')
    txt(d,214,420,'FREE · ENHANCED ATHLETE',f(MONO,26),VGOLD,a)
    txt(d,214,452,'KIDNEY BIOMARKER CHECKLIST',f(BEB,58),WHITE,a*appear(t,73.66))
    for i,nm in enumerate(CHK):
        tt=74.30+0.11*i
        if t<tt: continue
        b=appear(t,tt,0.12); x=84+(i%2)*470; y=546+(i//2)*54
        check(d,x,y,GREEN,0.8,a*b); txt(d,x+38,y-2,nm,f(MONO,22),CREAM,a*b)
    if t>=74.76:
        b=expo((t-74.76)/0.14); s=lerp(1.14,1.0,b)
        fn=f(BEB,int(92*s)); label='COMMENT  "KIDNEY"'; tw=d.textlength(label,font=fn)
        x0=540-(tw+48)/2; y0=726
        lit_bar(d,x0,y0,x0+tw+48,y0+int(110*s),VGOLD,b*a); d.text((x0+24,y0+8),label,font=fn,fill=A(INK,b*a))
        GL.rectangle([x0-4,y0-4,x0+tw+52,y0+int(110*s)+4],outline=A(VGOLD,b),width=12)
    if t>=77.26: tag(d,1000,420-2,'100% FREE',GREEN,24,a*appear(t,77.26),anchor='r') if False else None
    txt(d,540,896,'FOR RESEARCH & EDUCATIONAL PURPOSES ONLY',f(MONO,18),(150,150,156),a*0.9,anchor='ma')
SCENES=[s_alert,s_doc,s_mech,s_rails,s_egfr,s_iso,s_dash,s_bars,s_strip,s_spec,s_cmp,s_radar,s_cta]
# ---------------- text hook (frame 0) & topic band ----------------
HOOK_END=5.0; MID=39.35
def hook(im,t):
    if t>=HOOK_END+0.15: return
    a=1-clamp((t-HOOK_END)/0.15)
    sc=lerp(1.0,1.04,clamp(t/HOOK_END))
    lay=Image.new('RGBA',(W,420),(0,0,0,0)); d=ImageDraw.Draw(lay)
    l1a,l1b='High ','CREATININE'; l2='before you panic'
    f1=f(BAR,124); f2=f(BAR,108)
    w1=d.textlength(l1a,font=f1)+d.textlength(l1b,font=f1); w2=d.textlength(l2,font=f2)
    sh=Image.new('RGBA',(W,420),(0,0,0,0)); sd=ImageDraw.Draw(sh)
    x=(W-w1)/2; sd.text((x+4,34),l1a+l1b,font=f1,fill=(0,0,0,230)); sd.text(((W-w2)/2+4,170),l2,font=f2,fill=(0,0,0,230))
    lay.alpha_composite(sh.filter(ImageFilter.GaussianBlur(9)))
    d.text((x,28),l1a,font=f1,fill=WHITE,stroke_width=3,stroke_fill=(0,0,0)); d.text((x+d.textlength(l1a,font=f1),28),l1b,font=f1,fill=VGOLD,stroke_width=3,stroke_fill=(0,0,0))
    d.text(((W-w2)/2,164),l2,font=f2,fill=WHITE,stroke_width=3,stroke_fill=(0,0,0))
    if abs(sc-1)>1e-3: lay=lay.resize((int(W*sc),int(420*sc)),Image.BICUBIC)
    if a<1: lay.putalpha(lay.split()[3].point(lambda v:int(v*a)))
    im.alpha_composite(lay,(int((W-lay.width)/2),int(270-(lay.height-420)/2)))
def band(im,t):
    if not (HOOK_END<=t<MID+0.15): return
    a=min(clamp((t-HOOK_END)/0.15),1-clamp((t-MID)/0.15))
    d=ImageDraw.Draw(im,'RGBA')
    d.rectangle([8,212,W,340],fill=A(NAVY,0.88*a)); d.line([(8,340),(W,340)],fill=A(GOLD,0.6*a),width=2)
    d.line([(64,240),(108,240)],fill=A(GOLD,a),width=4); txt(d,122,224,'@coach.agz',f(MONO,26),GOLD,a)
    fn=f(BAR,66); s1='Lifters with high '; s2='CREATININE'
    txt(d,64,258,s1,fn,CREAM,a); txt(d,64+d.textlength(s1,font=fn),258,s2,fn,VGOLD,a)
# ---------------- captions ----------------
FIX={'axe':'AGZ'}
def build_groups():
    G=[];cur=[]
    for i,x in enumerate(WORDS):
        if cur:
            prev=WORDS[cur[-1]]
            if len(cur)>=3 or x['s']-prev['e']>0.28 or prev['w'][-1] in '.,?!': G.append(cur); cur=[]
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
    if t>WORDS[lo[-1]]['e']+0.6: return None
    return lo
def captions(im,t):
    if t<HOOK_END-0.0 and t<0: return
    g=group_at(t)
    if not g: return
    CY=cap_y(t); z_,dx_,dy_=layout(t); k_=clamp(dx_/250); CX=lerp(W/2,(490+W)/2,k_); MAXW=lerp(900,540,k_)
    d=ImageDraw.Draw(im,'RGBA')
    ws=[FIX.get(WORDS[i]['w'].lower().strip('.,?!'),WORDS[i]['w'].strip('.?!')).upper().rstrip(',') for i in g]
    size=118
    while True:
        fn=f(BEB,size); sp=d.textlength(' ',font=fn)+14; wd=[d.textlength(w,font=fn) for w in ws]; tot=sum(wd)+sp*(len(ws)-1)
        if tot<=MAXW: break
        size-=4
    xs=[];x=CX-tot/2
    for w_ in wd: xs.append(x); x+=w_+sp
    act=0
    for k,i in enumerate(g):
        if WORDS[i]['s']<=t: act=k
    g0=WORDS[g[0]]['s']; s=lerp(0.9,1,expo((t-g0)/0.10))
    cap=Image.new('RGBA',(W,300),(0,0,0,0)); cd=ImageDraw.Draw(cap); shd=Image.new('RGBA',(W,300),(0,0,0,0)); sd=ImageDraw.Draw(shd)
    prev=max(0,act-1); bt=expo((t-WORDS[g[act]]['s'])/0.07) if act>0 else 1
    bx0=lerp(xs[prev],xs[act],bt)-16; bx1=lerp(xs[prev]+wd[prev],xs[act]+wd[act],bt)+16
    for k,(w_,x_) in enumerate(zip(ws,xs)): sd.text((x_+4,46),w_,font=fn,fill=(0,0,0,220))
    cap.alpha_composite(shd.filter(ImageFilter.GaussianBlur(6)))
    lit_bar(cd,bx0,40+size*0.02,bx1,40+size*0.98,RED)
    for k,(w_,x_) in enumerate(zip(ws,xs)): cd.text((x_,40),w_,font=fn,fill=CREAM,stroke_width=0 if k==act else 3,stroke_fill=(0,0,0))
    top=CY-size/2-40
    if abs(s-1)>0.002:
        cap=cap.resize((int(W*s),int(300*s)),Image.BICUBIC); ox=int((W-cap.width)/2); oy=int(top-(cap.height-300)/2)
    else: ox,oy=0,int(top)
    im.alpha_composite(cap,(ox,oy))
# ---------------- frame ----------------
IMPACTS=[33.56,64.90,74.76]   # 2-frame shake on the heaviest landings
def frame(src,t):
    global GL
    glow=Image.new('RGBA',(W,H),(0,0,0,0)); GL=ImageDraw.Draw(glow,'RGBA')
    im=place_footage(src,t)
    # soft top/bottom scrims for legibility (footage itself untouched in colour)
    d=ImageDraw.Draw(im,'RGBA')
    for sc in SCENES: sc(im,ImageDraw.Draw(im,'RGBA'),t)
    if glow.getbbox():
        sm=glow.resize((W//4,H//4),Image.BILINEAR)
        g1=np.asarray(sm.filter(ImageFilter.GaussianBlur(3.5))).astype(np.float32)/255; g2=np.asarray(sm.filter(ImageFilter.GaussianBlur(10))).astype(np.float32)/255
        prem=np.clip(g1[...,:3]*g1[...,3:]*2.3+g2[...,:3]*g2[...,3:]*1.8,0,1)
        prem=np.asarray(Image.fromarray((prem*255).astype(np.uint8)).resize((W,H),Image.BILINEAR)).astype(np.float32)/255
        b=np.asarray(im.convert('RGB')).astype(np.float32)/255
        im=Image.fromarray(((1-(1-b)*(1-prem))*255).astype(np.uint8)).convert('RGBA')
    GL=None
    d=ImageDraw.Draw(im,'RGBA'); d.rectangle([0,0,7,H],fill=GOLD)
    band(im,t); hook(im,t); captions(im,t)
    out=im.convert('RGB')
    for t0 in IMPACTS:
        k=round((t-t0)*FPS)
        if k in (0,1):
            dx=[9,-5][k]; z=1.022; big=out.resize((int(W*z),int(H*z)),Image.BICUBIC); ox=(big.width-W)//2-dx; oy=(big.height-H)//2
            out=big.crop((ox,oy,ox+W,oy+H)); ImageDraw.Draw(out).rectangle([0,0,7,H],fill=GOLD)
    return out
if __name__=='__main__':
    mode=sys.argv[2]
    if mode=='stills':
        import os; os.makedirs(S+'/qc',exist_ok=True)
        for tt in [float(x) for x in sys.argv[3:]]:
            subprocess.run(['ffmpeg','-v','error','-y','-ss',str(tt),'-i',T+'assembled.mov','-frames:v','1',S+'/qc/_src.png'])
            frame(Image.open(S+'/qc/_src.png').convert('RGB'),tt).resize((540,960)).save(S+f'/qc/st_{tt:.2f}.jpg',quality=85)
        sys.exit()
    n0,n1=int(sys.argv[3]),int(sys.argv[4]); out=sys.argv[5]
    dec=subprocess.Popen(['ffmpeg','-v','error','-ss',f'{n0/FPS:.4f}','-i',T+'assembled.mov','-frames:v',str(n1-n0),'-f','rawvideo','-pix_fmt','rgb24','-'],stdout=subprocess.PIPE)
    enc=subprocess.Popen(['ffmpeg','-v','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-','-c:v','libx264','-crf','14','-preset','medium','-pix_fmt','yuv420p',out],stdin=subprocess.PIPE)
    for n in range(n0,n1):
        buf=dec.stdout.read(W*H*3)
        if len(buf)<W*H*3: print('short',n); break
        enc.stdin.write(frame(Image.frombuffer('RGB',(W,H),buf),n/FPS).tobytes())
    enc.stdin.close(); enc.wait(); dec.kill(); print('done',n0,n1)
