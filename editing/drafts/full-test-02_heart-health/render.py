# Full test 02 — Heart health (ezetimibe + telmisartan). 1080x1920 30 fps.
# usage: python3 render.py <scratch> stills t1 t2 ...   |   python3 render.py <scratch> chunk n0 n1 out.mp4
import json, subprocess, sys, math
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
S=sys.argv[1]; F=S+'/fonts/'; WK=S+'/work/'
W,H=1080,1920; FPS=30
TR=json.load(open(WK+'trim.json')); N=int(round(TR['dur']*FPS))
WORDS=json.load(open(WK+'words_final.json'))
def T(i): return WORDS[i]['s']
# jump cuts on the new timeline
CUTS=[];acc=0
for a,b in TR['keep_frames'][:-1]: acc+=b-a; CUTS.append(acc/FPS)
# ---------------- palette (brand + test-06 overlay accents) ----------------
GOLD=(201,169,110); CREAM=(244,241,234); NAVY=(14,17,23); MUTED=(124,124,130)
RED=(255,34,28); VGOLD=(255,194,26); CYAN=(0,229,255); GREEN=(30,255,110); AMBER=(240,160,48)
DEEP=(2,3,8); INK=(6,8,14); WHITE=(255,255,255); COARED=(210,10,20); XRAY=(2,12,26)
MONO='JBMono-500.ttf'; MONOB='JBMono-700.ttf'; BEB='BebasNeue-Regular.ttf'; BAR='BarlowCondensed-Bold.ttf'; BARX='BarlowCondensed-ExtraBold.ttf'
_fc={}
def f(n,s):
    k=(n,int(s))
    if k not in _fc: _fc[k]=ImageFont.truetype(F+n,int(s))
    return _fc[k]
def clamp(x,a=0,b=1): return max(a,min(b,x))
def expo(x): x=clamp(x); return 1 if x>=1 else 1-2**(-10*x)
def ease_io(x): x=clamp(x); return 4*x**3 if x<.5 else 1-(-2*x+2)**3/2
def lerp(a,b,t): return a+(b-a)*t
def A(c,a=1.0): return tuple(int(v) for v in c[:3])+(int(clamp(a)*255),)
def appear(t,t0,dur=0.16): return expo((t-t0)/dur)
def window(t,t0,t1,fi=0.16,fo=0.14): return appear(t,t0,fi)*(1-clamp((t-t1)/fo))
GL=None   # glow layer draw (bloom)
# ---------------- primitives ----------------
def txt(d,x,y,s,font,col,a=1.0,anchor=None):
    # Pillow 12 ignores fill alpha for text, so blend through a coverage mask
    a=clamp(a)
    if a<=0.004 or not s: return
    if a>=0.996: d.text((x,y),s,font=font,fill=A(col,1),anchor=anchor); return
    im=d._image; bx0,by0,bx1,by1=[int(v) for v in d.textbbox((x,y),s,font=font,anchor=anchor)]
    bx0-=2; by0-=2; bx1+=2; by1+=2
    if bx1<=bx0 or by1<=by0: return
    m=Image.new('L',(bx1-bx0,by1-by0),0); ImageDraw.Draw(m).text((x-bx0,y-by0),s,font=font,fill=int(255*a),anchor=anchor)
    im.paste(Image.new(im.mode,m.size,tuple(int(v) for v in col[:3])+((255,) if im.mode=='RGBA' else ())),(bx0,by0),m)
def brackets(d,x0,y0,x1,y1,col,L=34,w=4):
    for (cx,cy,sx,sy) in [(x0,y0,1,1),(x1,y0,-1,1),(x0,y1,1,-1),(x1,y1,-1,-1)]:
        d.line([(cx,cy),(cx+sx*L,cy)],fill=col,width=w); d.line([(cx,cy),(cx,cy+sy*L)],fill=col,width=w)
def lit_bar(d,x0,y0,x1,y1,col,a=1.0):
    h=max(1,int(y1-y0))
    for i in range(h):
        k=i/h; c=tuple(int(min(255,v*(1.18-0.36*k)+(40 if k<0.12 else 0))) for v in col)
        d.line([(x0,y0+i),(x1,y0+i)],fill=c+(int(255*clamp(a)),))
def tag(d,x,y,label,col=RED,size=30,a=1.0,glow=True,anchor='l'):
    if a<=0: return x
    fn=f(MONOB,size); tw=d.textlength(label,font=fn); h=size+16
    if anchor=='r': x=x-tw-24
    elif anchor=='c': x=x-(tw+24)/2
    lit_bar(d,x,y,x+tw+24,y+h,col,a); txt(d,x+12,y+6,label,fn,INK if col in (VGOLD,GREEN,CYAN,AMBER) else WHITE,a)
    if GL and glow: GL.rectangle([x-4,y-4,x+tw+28,y+h+4],outline=A(col,a),width=8)
    return x+tw+24
def check(d,x,y,col,s=1.0,a=1.0):
    pts=[(x,y+16*s),(x+10*s,y+28*s),(x+30*s,y+2*s)]
    d.line(pts,fill=A(col,a),width=int(6*s),joint='curve')
    if GL: GL.line(pts,fill=A(col,a),width=int(12*s))
def cross(d,x,y,col,s=1.0,a=1.0):
    d.line([(x,y),(x+28*s,y+28*s)],fill=A(col,a),width=int(6*s)); d.line([(x+28*s,y),(x,y+28*s)],fill=A(col,a),width=int(6*s))
    if GL: GL.line([(x,y),(x+28*s,y+28*s)],fill=A(col,a),width=12); GL.line([(x+28*s,y),(x,y+28*s)],fill=A(col,a),width=12)
def arrow(d,x0,y0,x1,y1,col,w=5,a=1.0,L=18):
    d.line([(x0,y0),(x1,y1)],fill=A(col,a),width=w); ang=math.atan2(y1-y0,x1-x0)
    d.polygon([(x1,y1),(x1-L*math.cos(ang-0.45),y1-L*math.sin(ang-0.45)),(x1-L*math.cos(ang+0.45),y1-L*math.sin(ang+0.45))],fill=A(col,a))
def tri(d,x,y,col,up=True,s=22,a=1.0):
    if up: d.polygon([(x,y+s),(x+s,y+s),(x+s/2,y)],fill=A(col,a))
    else: d.polygon([(x,y),(x+s,y),(x+s/2,y+s)],fill=A(col,a))
def flag(d,box,label,t0,t,side='right',col=RED):
    p=expo((t-t0)/0.14)
    if p<=0: return
    x0,y0,x1,y1=box; brackets(d,x0,y0,x1,y1,A(col,1),26,6)
    if GL: brackets(GL,x0,y0,x1,y1,A(col,1),26,12)
    q=clamp((p-0.3)/0.7)
    if q>0:
        for seg in [((x0,y0),(lerp(x0,x1,q),y0)),((x1,y1),(lerp(x1,x0,q),y1)),((x0,y1),(x0,lerp(y1,y0,q))),((x1,y0),(x1,lerp(y0,y1,q)))]:
            d.line(seg,fill=A(col,1),width=3)
    if p>0.5 and label:
        if side=='right': tag(d,x1+12,(y0+y1)/2-23,label,col,28)
        elif side=='above': tag(d,x0,y0-54,label,col,28)
        elif side=='aboveR': tag(d,x1,y0-54,label,col,28,anchor='r')
        else: tag(d,x0,y1+8,label,col,28)
def frosted(im,box,dark=0.86,blur=10,radius=0):
    x0,y0,x1,y1=[int(v) for v in box]; x0=max(0,x0); y0=max(0,y0); x1=min(W,x1); y1=min(H,y1)
    if x1<=x0+2 or y1<=y0+2: return
    reg=im.crop((x0,y0,x1,y1)).convert('RGB').filter(ImageFilter.GaussianBlur(blur))
    reg=Image.blend(reg,Image.new('RGB',reg.size,DEEP),dark)
    if radius:
        m=Image.new('L',reg.size,0); ImageDraw.Draw(m).rounded_rectangle([0,0,reg.width-1,reg.height-1],radius=radius,fill=255)
        im.paste(reg,(x0,y0),m)
    else: im.paste(reg,(x0,y0))
def card(im,box,a,col=VGOLD,dark=0.88,label_l=None,label_r=None,t=0,rec=True):
    """clinical inspection card: frosted fill, thin frame, gold corner brackets, mono header"""
    if a<=0: return
    frosted(im,box,dark*a,10,14)
    d=ImageDraw.Draw(im,'RGBA'); x0,y0,x1,y1=box
    d.rounded_rectangle(box,radius=14,outline=A(col,0.55*a),width=2); brackets(d,x0,y0,x1,y1,A(col,a),30,6)
    if GL: brackets(GL,x0,y0,x1,y1,A(col,a),30,12)
    if label_l:
        if rec: d.ellipse([x0+22,y0+22,x0+36,y0+36],fill=A(RED,a if int(t*4)%2==0 else a/3))
        txt(d,x0+(48 if rec else 24),y0+14,label_l,f(MONO,26),WHITE,a)
    if label_r:
        fn=f(MONO,26); txt(d,x1-24-d.textlength(label_r,font=fn),y0+14,label_r,fn,col,a)
def kicker(d,x,y,label,t,t0,col=VGOLD,size=28):
    p=appear(t,t0,0.18)
    if p<=0: return
    d.line([(x,y+size*0.55),(x+lerp(0,48,p),y+size*0.55)],fill=A(col,1),width=4)
    q=appear(t,t0+0.08,0.2)
    if q>0:
        fn=f(MONOB,size); s=''
        n=int(len(label)*q+0.999); txt(d,x+62,y,label[:n],fn,col)
def redaction(d,box,t,a=1.0,reveal=0.0):
    """black redaction bar with hatch; reveal (0..1) wipes it away left->right"""
    x0,y0,x1,y1=box; xr=lerp(x0,x1,reveal)
    if xr>=x1 or a<=0: return
    d.rectangle([xr,y0,x1,y1],fill=A((8,8,10),a));
    for k in range(int(x0)-400,int(x1),22):
        xa=max(xr,k); xb=min(x1,k+(y1-y0))
        if xb>xa: d.line([(xa,y0+(xa-k)),(xb,y0+(xb-k))],fill=A((40,40,46),a),width=3)
    d.rectangle([xr,y0,x1,y1],outline=A(RED,0.8*a),width=2)
    if reveal>0 and reveal<1:   # scan edge
        d.rectangle([xr-3,y0-8,xr+3,y1+8],fill=A(CYAN,a))
        if GL: GL.rectangle([xr-8,y0-14,xr+8,y1+14],fill=A(CYAN,a))
def ring(d,cx,cy,ro,ri,col,a=1.0,fill=XRAY):
    d.ellipse([cx-ro,cy-ro,cx+ro,cy+ro],fill=A(col,0.35*a),outline=A(col,a),width=4)
    d.ellipse([cx-ri,cy-ri,cx+ri,cy+ri],fill=A(fill,a),outline=A(col,a),width=3)
    if GL: GL.ellipse([cx-ro,cy-ro,cx+ro,cy+ro],outline=A(col,a),width=8)
def ecg_y(u,amp=1.0):
    """one heartbeat over u in [0,1)"""
    u=u%1
    if 0.10<u<0.18: return -0.12*math.sin((u-0.10)/0.08*math.pi)          # P
    if 0.24<u<0.27: return 0.18*(u-0.24)/0.03                              # Q
    if 0.27<=u<0.30: return lerp(0.18,-1.0*amp,(u-0.27)/0.03)             # R up
    if 0.30<=u<0.335: return lerp(-1.0*amp,0.42*amp,(u-0.30)/0.035)      # S
    if 0.335<=u<0.37: return lerp(0.42*amp,0,(u-0.335)/0.035)
    if 0.48<u<0.64: return -0.25*math.sin((u-0.48)/0.16*math.pi)           # T
    return 0
# ---------------- layouts: footage window that morphs between scenes ----------------
# s = scale, (tx,ty) = where the face anchor (540,1000) lands, rect = visible mask, r = corner radius,
# fr = frame strength, cy = caption top
LAY={
 'FULL':   dict(s=1.00,tx=540,ty=1000,rect=(0,0,W,H),r=0,  fr=0,cy=1385),
 'UP':     dict(s=1.00,tx=540,ty=560, rect=(0,0,W,1040),r=0,fr=1,cy=918),
 'PIP_BR': dict(s=0.50,tx=845,ty=1160,rect=(650,955,1040,1345),r=195,fr=1,cy=1385),
 'WINDOW': dict(s=0.80,tx=540,ty=700, rect=(70,390,1010,1010),r=28,fr=1,cy=1385),
 'RIGHT':  dict(s=0.62,tx=800,ty=880, rect=(560,420,1040,1330),r=26,fr=1,cy=1385),
 'LEFT':   dict(s=0.62,tx=280,ty=880, rect=(40,420,520,1330),r=26,fr=1,cy=1385),
 'PIP_TOP':dict(s=0.45,tx=540,ty=575, rect=(370,390,710,730),r=170,fr=1,cy=1385),
}
KEYS=[(0,'FULL'),(T(22)+0.12,'UP'),(T(51)-0.12,'FULL'),(T(83),'PIP_BR'),(T(116)-0.1,'WINDOW'),(T(153),'RIGHT'),
      (T(183)-0.05,'FULL'),(T(199),'UP'),(T(217),'FULL'),(T(240)+0.2,'LEFT'),(T(269),'PIP_TOP'),(T(287)-0.3,'FULL'),(T(353)-0.25,'UP')]
MORPH=0.45
def layout(t):
    cur=KEYS[0]; prev=None
    for k in KEYS:
        if k[0]<=t: prev,cur=cur,k
    a=LAY[cur[1]]
    if prev is None or t-cur[0]>=MORPH: return dict(a)
    b=LAY[prev[1]]; p=ease_io((t-cur[0])/MORPH)
    o={}
    for k in a:
        if k=='rect': o[k]=tuple(lerp(b[k][i],a[k][i],p) for i in range(4))
        else: o[k]=lerp(b[k],a[k],p)
    return o
def seg_of(t): return sum(1 for c in CUTS if c<=t+1e-6)
def zoom(t):
    sg=seg_of(t)
    if sg==0: return lerp(1.0,1.06,expo((t-T(6))/0.22))       # visual hook: punch-in on "blood pressure"
    return 1.08 if sg%2==1 else 1.0
BG=None
def make_bg():
    im=Image.new('RGB',(W,H),(5,8,16)); a=np.asarray(im).astype(np.float32)
    yy,xx=np.mgrid[0:H,0:W]; g=np.exp(-(((xx-W)/700)**2+((yy-300)/700)**2))[...,None]
    a=a+g*np.array([22,18,10]); im=Image.fromarray(np.clip(a,0,255).astype(np.uint8))
    d=ImageDraw.Draw(im)
    for x in range(0,W,60): d.line([(x,0),(x,H)],fill=(12,16,28),width=1)
    for y in range(0,H,60): d.line([(0,y),(W,y)],fill=(12,16,28),width=1)
    return im
def place_footage(src,t):
    L=layout(t); s=L['s']*zoom(t)
    x0,y0,x1,y1=[int(round(v)) for v in L['rect']]; r=int(L['r'])
    full=(x0<=0 and y0<=0 and x1>=W and y1>=H and r==0 and abs(s-1)<1e-4)
    if full: return src.convert('RGBA'),L
    # crop only what the mask needs
    sw,sh=int(W*s),int(H*s); ox=L['tx']-540*s; oy=L['ty']-1000*s
    base=BG.copy().convert('RGBA')
    big=src.resize((sw,sh),Image.BICUBIC) if abs(s-1)>1e-4 else src
    lay=Image.new('RGBA',(W,H),(0,0,0,0)); lay.paste(big.convert('RGBA'),(int(round(ox)),int(round(oy))))
    m=Image.new('L',(W,H),0); ImageDraw.Draw(m).rounded_rectangle([x0,y0,x1-1,y1-1],radius=r,fill=255)
    if L['fr']>0.01:   # soft drop shadow under the window
        sh_=Image.new('RGBA',(W,H),(0,0,0,0)); ImageDraw.Draw(sh_).rounded_rectangle([x0+6,y0+14,x1+6,y1+14],radius=r,fill=(0,0,0,int(150*L['fr'])))
        base.alpha_composite(sh_.filter(ImageFilter.GaussianBlur(14)))
    base.paste(lay,(0,0),m)
    return base,L
def window_frame(im,L,t):
    a=L['fr']
    if a<0.02: return
    d=ImageDraw.Draw(im,'RGBA'); x0,y0,x1,y1=L['rect']; r=L['r']
    if y0<2 and x0<2 and x1>W-2:    # split: seam line only
        d.rectangle([0,y1-3,W,y1+1],fill=A(VGOLD,a));
        if GL: GL.rectangle([0,y1-6,W,y1+4],fill=A(VGOLD,a))
        return
    d.rounded_rectangle([x0,y0,x1,y1],radius=r,outline=A(VGOLD,0.9*a),width=3)
    if GL: GL.rounded_rectangle([x0,y0,x1,y1],radius=r,outline=A(VGOLD,a),width=8)
    if r<60: brackets(d,x0-8,y0-8,x1+8,y1+8,A(VGOLD,a),34,5)
# ---------------- scenes ----------------
def sc_hook(im,d,t):        # frame-0 text hook (TEXT_HOOK_ENGINE): static, visible on frame 0
    a=1-clamp((t-6.0)/0.15)
    if a<=0: return
    l1a,l1b,l2='Silent ','HEART WALL',' damage'; line2='your bloodwork misses'
    sz=92
    while ImageDraw.Draw(im).textlength('Silent HEART WALL damage',font=f(BARX,sz))>800: sz-=2
    s=lerp(1.0,1.04,clamp(t/6.0))      # slow 100->104% on the text over its hold
    fn=f(BARX,int(sz*s))
    w1=d.textlength(l1a+l1b+l2,font=fn); w2=d.textlength(line2,font=fn)
    cx=500; y=258; lh=int(sz*s*1.02)
    bw=max(w1,w2)+70; frosted(im,(cx-bw/2,y-18,cx+bw/2,y+2*lh+30),0.62*a,12,18)
    d=ImageDraw.Draw(im,'RGBA')
    d.rectangle([cx-bw/2,y-18,cx-bw/2+7,y+2*lh+30],fill=A(RED,a))
    x=cx-w1/2; lay=Image.new('RGBA',(W,int(y+2*lh+60)),(0,0,0,0)); ld=ImageDraw.Draw(lay)
    for part,col in [(l1a,WHITE),(l1b,VGOLD),(l2,WHITE)]:
        ld.text((x,y),part,font=fn,fill=col,stroke_width=2,stroke_fill=(0,0,0)); x+=d.textlength(part,font=fn)
    ld.text((cx-w2/2,y+lh),line2,font=fn,fill=WHITE,stroke_width=2,stroke_fill=(0,0,0))
    if a<1: lay.putalpha(lay.split()[3].point(lambda v:int(v*a)))
    im.paste(lay,(0,0),lay)
def sc_band(im,d,t):        # topic band 6.0 -> telmisartan reveal (~midpoint)
    t0=6.0; t1=T(198)
    if t<t0 or t>t1+0.15: return
    a=window(t,t0,t1,0.15,0.15)
    d.rectangle([8,212,W,350],fill=A(NAVY,0.89*a)); d.line([(64,242),(108,242)],fill=A(GOLD,a),width=4)
    txt(d,122,226,'@coach.agz',f(MONO,28),GOLD,a)
    fn=f(BARX,76); x=64; y=262
    for part,col in [('Protect your ',CREAM),('HEART',VGOLD),(' on cycle',CREAM)]:
        txt(d,x,y,part,fn,col,a); x+=d.textlength(part,font=fn)
def sc_s1(im,d,t):          # UP split: standard panel vs EKG, silent timeline
    t0,t1=T(22)+0.12+0.40,T(51)-0.12
    if not (t0<=t<t1+0.2): return
    ga=window(t,t0,t1,0.25,0.2); yo=30+lerp(60,0,expo((t-t0)/0.3))
    # header
    d.ellipse([70,1040+yo,84,1054+yo],fill=A(RED,ga if int(t*4)%2==0 else ga/3)); txt(d,96,1032+yo,'SCREENING · ON CYCLE',f(MONO,26),WHITE,ga)
    fn=f(MONO,26); lab='EVIDENCE 01'; txt(d,1010-d.textlength(lab,font=fn),1032+yo,lab,fn,VGOLD,ga)
    # standard panel (paper)
    pa=window(t,max(T(24),t0),t1)
    if pa>0:
        dim=lerp(1,0.55,appear(t,T(33),0.3))
        x0,y0=70,1080+yo; d.rectangle([x0,y0,x0+430,y0+300],fill=A((246,246,242),pa*dim)); d.rectangle([x0,y0,x0+430,y0+48],fill=A(COARED,pa*dim))
        txt(d,x0+16,y0+9,'STANDARD PANEL',f(MONOB,26),WHITE,pa*dim)
        for i,nm in enumerate(['CBC','CMP','LIPIDS','HORMONES']):
            ra=pa*dim*appear(t,T(28)+i*0.16,0.12); yy=y0+64+i*56
            txt(d,x0+18,yy,nm,f(BAR,38),INK,ra); txt(d,x0+230,yy+8,'IN RANGE',f(MONO,22),(90,90,100),ra)
            check(d,x0+370,yy+4,(10,160,70),0.9,ra) if ra>0 else None
            d.line([(x0+14,yy+50),(x0+416,yy+50)],fill=A((220,220,225),ra),width=2)
        if t>=T(31): flag(d,(x0-6,y0-6,x0+436,y0+306),'',T(31),t,'none',col=VGOLD) if t<T(33) else None
    # EKG monitor
    ma=window(t,T(37),t1)
    if ma>0:
        x0,y0,x1,y1=530,1080+yo,1010,1380+yo
        d.rectangle([x0,y0,x1,y1],fill=A(XRAY,0.96*ma),outline=A(CYAN,0.6*ma),width=2)
        for gx in range(x0,x1,30): d.line([(gx,y0),(gx,y1)],fill=A((10,40,60),ma),width=1)
        for gy in range(int(y0),int(y1),30): d.line([(x0,gy),(x1,gy)],fill=A((10,40,60),ma),width=1)
        txt(d,x0+14,y0+10,'EKG · LEAD V5',f(MONO,24),CYAN,ma)
        prog=clamp((t-T(37))/1.0); base=y0+190; pts=[]
        for k in range(0,int((x1-x0-20)*prog)):
            u=(k/150.0-(t-T(37))*0.0)
            pts.append((x0+10+k,base+ecg_y(u,1.45)*120))
        if len(pts)>1:
            d.line(pts,fill=A(CYAN,ma),width=4)
            if GL: GL.line(pts,fill=A(CYAN,ma),width=9)
            hx,hy=pts[-1]; d.ellipse([hx-6,hy-6,hx+6,hy+6],fill=A(WHITE,ma))
        if t>=T(39):   # tall R wave flagged
            u0=0.285; k0=int(u0*150)+150; bx=x0+10+k0
            flag(d,(bx-24,base-185,bx+30,base+70),'LVH SIGNS',T(39),t,'right' if bx<800 else 'above')
    # silent-phase timeline
    ta=window(t,T(40),t1)
    if ta>0:
        x0,x1,y=70,1010,1418+yo
        txt(d,x0,y-4,'SILENT',f(MONOB,24),MUTED,ta)
        bx0=200; p=lerp(0.05,1.0,clamp((t-T(40))/(T(47)-T(40)+0.2)))
        d.rectangle([bx0,y,x1,y+26],outline=A((70,74,90),ta),width=2)
        d.rectangle([bx0+3,y+3,lerp(bx0+3,x1-3,p),y+23],fill=A((60,66,84),ta))
        if t>=T(47):
            b=appear(t,T(47)); tag(d,x1,y-6,'SYMPTOMS',RED,24,b*ta,anchor='r')
    if t>=T(50):    # verdict slam
        p=expo((t-T(50))/0.10); va=1-clamp((t-t1)/0.14); x0=60; x1=lerp(60,1020,p); y=1392+yo
        if GL: GL.rectangle([x0-4,y-6,x1+4,y+86],outline=A(RED,va),width=10)
        lit_bar(d,x0,y,x1,y+80,RED,va); d.rectangle([x0,y+76,x1,y+80],fill=A((140,0,0),va))
        if p>0.6:
            fn=f(BEB,66); txt(d,x0+26,y+8,'SYMPTOMS',fn,WHITE,va); tw=d.textlength('SYMPTOMS',font=fn)
            txt(d,x0+26+tw+22,y+26,'= LATE STAGE',f(MONOB,34),WHITE,va)
def slot(im,box,label,t,a,reveal=0.0,name=None,name_col=CREAM,status=None):
    card(im,box,a,VGOLD,0.86,None,None,t,False)
    d=ImageDraw.Draw(im,'RGBA'); x0,y0,x1,y1=box
    txt(d,x0+22,y0+14,label,f(MONOB,26),VGOLD,a)
    if status:
        d.ellipse([x1-120,y0+22,x1-106,y0+36],fill=A(GREEN,status)); txt(d,x1-96,y0+14,'ACTIVE',f(MONO,22),GREEN,status)
    if name and reveal>0:
        fn=f(BEB,int((y1-y0)*0.52)); txt(d,x0+22,y0+52,name,fn,name_col,a)
    redaction(d,(x0+22,y0+58,x1-22,y1-18),t,a,reveal)
    return d
def sc_s2(im,d,t):          # FULL: two redacted compound slots + method stepper
    t0,t1=T(54),T(83)-0.05
    if not (t0-0.01<=t<t1+0.2): return
    out=expo((t-t1)/0.2)
    for i,(x0,x1,tt) in enumerate([(60,520,T(54)),(560,1020,T(55))]):
        p=expo((t-tt)/0.22)
        if p<=0: continue
        dx=lerp(-560 if i==0 else 560,0,p); dy=-260*out
        slot(im,(x0+dx,395+dy,x1+dx,540+dy),f'COMPOUND 0{i+1}',t,1-out,status=appear(t,T(59))*(1-out))
    d=ImageDraw.Draw(im,'RGBA')
    st=[('MECHANISM',T(72)),('SIMPLIFY',T(77)),('OPTIMIZE',T(82))]
    sa=appear(t,T(70)-0.1,0.2)*(1-out)
    if sa>0:
        xs=[60,400,740]; y=568-260*out
        frosted(im,(50,y-10,1030,y+66),0.7*sa,8,12); d=ImageDraw.Draw(im,'RGBA')
        for k,(nm,tt) in enumerate(st):
            on=appear(t,tt,0.12)
            col=VGOLD if on>0.5 else (90,94,110)
            d.rounded_rectangle([xs[k],y,xs[k]+280,y+56],radius=10,outline=A(col,sa),width=3,fill=A(VGOLD,0.18*on*sa))
            if GL and on>0: GL.rounded_rectangle([xs[k],y,xs[k]+280,y+56],radius=10,outline=A(VGOLD,on*sa),width=8)
            fn=f(MONOB,28); txt(d,xs[k]+140-d.textlength(f'0{k+1} {nm}',font=fn)/2,y+12,f'0{k+1} {nm}',fn,WHITE if on>0.5 else MUTED,sa)
            if k<2: arrow(d,xs[k]+286,y+28,xs[k+1]-8,y+28,col,3,sa,12)
def sc_s3(im,d,t):          # PIP_BR full-screen: lipids bar chart -> donut -> dual line chart
    t0,t1=T(83)+0.2,T(116)-0.32
    if not (t0<=t<t1+0.3): return
    ga=window(t,t0,t1,0.25,0.25)
    kicker(d,70,388,'NO. 01 · LIPIDS',t,T(85))
    txt(d,70,430,'LIPID PANEL',f(BEB,92),CREAM,appear(t,T(88))*ga)
    if appear(t,T(89))>0: tag(d,1010,446,'ON CYCLE',VGOLD,28,appear(t,T(89))*ga,anchor='r')
    x0,x1,yb,yt=90,1000,860,570
    sw=clamp((t-T(103))/0.3)     # bars -> line chart handoff
    ca=appear(t,T(89)-0.1,0.25)*ga
    if ca>0:
        d.line([(x0,yb),(x1,yb)],fill=A((110,114,130),ca),width=3)
        for k in range(1,4): d.line([(x0,yb-k*85),(x1,yb-k*85)],fill=A((30,34,50),ca),width=1)
    if sw<1 and ca>0:
        base=yb-0.5*(yb-yt)
        for xx in range(x0,x1,28): d.line([(xx,base),(xx+14,base)],fill=A(MUTED,ca*(1-sw)),width=2)
        txt(d,x0,base-34,'BASELINE',f(MONO,22),MUTED,ca*(1-sw))
        bars=[('HDL',0.70,0.16,T(92),GREEN),('LDL',0.50,0.88,T(99),CYAN),('ApoB',0.48,0.82,T(102),CYAN)]
        for k,(nm,v0,v1,tt,c0) in enumerate(bars):
            bx=150+k*290; up=expo((t-T(89)-k*0.08)/0.4)
            v=lerp(0,v0,up); ch=expo((t-tt)/0.35); v=lerp(v,v1,ch)
            col=c0 if ch<0.3 else RED
            h=v*(yb-yt)*(1-sw)
            if h>1:
                lit_bar(d,bx,yb-h,bx+200,yb,col,ca)
                if GL: GL.rectangle([bx,yb-h,bx+200,yb],outline=A(col,ca),width=8)
            fn=f(BEB,54); txt(d,bx+100-d.textlength(nm,font=fn)/2,yb+10,nm,fn,WHITE,ca*(1-sw))
            if ch>0.3 and sw<0.5:
                tri(d,bx+170,yb-h-40,RED,up=(v1>v0),s=26,a=ca*(1-sw))
    if sw>0:
        la=sw*ga
        def curve(u,k): return yb-24-((0.06+0.90*u**2.3) if k==0 else (0.10+0.50*u**0.8))*(yb-yt-30)
        for k,(nm,tt,col) in enumerate([('CV RISK',T(105),RED),('PHYSIQUE',T(110),VGOLD)]):
            p=clamp((t-tt)/1.3)
            if p<=0: continue
            pts=[(lerp(x0+20,x1-20,u/60),curve(u/60*1.0,k)) for u in range(0,int(60*p)+1)]
            if len(pts)>1:
                d.line(pts,fill=A(col,la),width=7,joint='curve')
                if GL: GL.line(pts,fill=A(col,la),width=14)
            ex,ey=pts[-1]; d.ellipse([ex-9,ey-9,ex+9,ey+9],fill=A(WHITE,la))
            if p>0.98: tag(d,ex-20,ey-(62 if k==0 else -18),nm+' ↑',col,26,la*appear(t,tt+1.3),anchor='r')
        txt(d,x0,yb+14,'WEEKS ON CYCLE →',f(MONO,24),MUTED,la)
    # risk donut (bottom-left)
    da=appear(t,T(92)-0.05,0.25)*ga
    if da>0:
        cx,cy,r=215,1150,135
        steps=[(T(92),0.42),(T(99),0.60),(T(102),0.72),(T(107),0.90)]
        v=0.18
        for tt,vv in steps: v=lerp(v,vv,expo((t-tt)/0.4)) if t>=tt else v
        d.arc([cx-r,cy-r,cx+r,cy+r],0,360,fill=A((40,44,60),da),width=34)
        d.arc([cx-r,cy-r,cx+r,cy+r],-90,-90+360*v,fill=A(RED if v>0.5 else AMBER,da),width=34)
        if GL: GL.arc([cx-r,cy-r,cx+r,cy+r],-90,-90+360*v,fill=A(RED,da),width=40)
        fn=f(BEB,64); txt(d,cx,cy-8,'CV RISK',fn,WHITE,da,anchor='mm'); tri(d,cx-13,cy+30,RED,True,26,da)
        txt(d,385,1100,'CARDIO-',f(MONO,24),MUTED,da); txt(d,385,1130,'VASCULAR',f(MONO,24),MUTED,da); txt(d,385,1160,'RISK LOAD',f(MONO,24),MUTED,da)
def sc_s4(im,d,t):          # WINDOW: ezetimibe reveal + X-ray schematic of the gut wall
    t0,t1=T(116),T(153)-0.05
    if not (t0<=t<t1+0.2): return
    ga=window(t,T(116)-0.1+0.42,t1,0.2,0.2)
    L=layout(t)
    # window header strip
    x0,y0,x1,_=L['rect']
    if L['fr']>0.5:
        d.rectangle([x0+3,y0+3,x1-3,y0+52],fill=A(DEEP,0.75*ga)); d.ellipse([x0+20,y0+20,x0+34,y0+34],fill=A(RED,ga if int(t*4)%2==0 else ga/3))
        txt(d,x0+46,y0+12,'LIVE · @coach.agz',f(MONO,24),WHITE,ga)
        hdr='EZETIMIBE · COMPOUND 01' if t>=T(119)+0.9 else 'COMPOUND 01'; fn=f(MONOB,24); txt(d,x1-20-d.textlength(hdr,font=fn),y0+12,hdr,fn,VGOLD,ga)
    # name reveal (the redacted slot from 0:13 returns and is wiped open)
    na=window(t,T(116)+0.32,T(121)-0.1,0.2,0.2)
    if na>0:
        rv=clamp((t-T(119))/0.35); box=(70,1040,1010,1240)
        card(im,box,na,VGOLD,0.9); d=ImageDraw.Draw(im,'RGBA'); txt(d,94,1054,'COMPOUND 01',f(MONOB,26),VGOLD,na)
        if rv>0: txt(d,94,1088,'EZETIMIBE',f(BEB,140),CREAM,na)
        redaction(d,(94,1096,986,1222),t,na,rv)
    # schematic
    sa=window(t,T(121),t1,0.2,0.2)
    if sa<=0: return
    X0,Y0,X1,Y1=70,1035,1010,1365
    d.rounded_rectangle([X0,Y0,X1,Y1],radius=12,fill=A(XRAY,0.97*sa),outline=A(CYAN,0.7*sa),width=2)
    for gy in range(Y0+20,Y1,26): d.line([(X0+4,gy),(X1-4,gy)],fill=A((8,30,48),sa),width=1)
    sc_y=Y0+((t*260)%(Y1-Y0)); d.line([(X0+4,sc_y),(X1-4,sc_y)],fill=A(CYAN,0.25*sa),width=2)
    wx=400; LX=860
    # zones
    for (lx,lab,tt) in [(X0+20,'INTESTINE',T(130)),(wx+60,'BLOOD',T(133)),(LX-10,'LIVER',T(143)-0.6)]:
        txt(d,lx,Y0+12,lab,f(MONOB,22),CYAN,sa*appear(t,tt))
    # intestinal wall with 3 NPC1L1 gates
    d.line([(wx,Y0+48),(wx,Y1-12)],fill=A(CYAN,sa),width=5); d.line([(wx+26,Y0+48),(wx+26,Y1-12)],fill=A(CYAN,sa),width=5)
    if GL: GL.line([(wx,Y0+48),(wx,Y1-12)],fill=A(CYAN,sa),width=10); GL.line([(wx+26,Y0+48),(wx+26,Y1-12)],fill=A(CYAN,sa),width=10)
    blocked=appear(t,T(123),0.12)
    gates=[Y0+100,Y0+190,Y0+280]
    for gy in gates:
        d.rectangle([wx-3,gy-22,wx+29,gy+22],fill=A(XRAY,sa)); d.rectangle([wx-3,gy-22,wx+29,gy+22],outline=A(VGOLD,sa),width=3)
        if blocked>0:
            d.rectangle([wx-6,gy-25,wx+32,gy+25],fill=A(RED,blocked*sa)); cross(d,wx+1,gy-14,WHITE,0.85,blocked*sa)
    if blocked>0: flag(d,(wx-30,Y0+60,wx+56,Y1-20),'NPC1L1 BLOCKED',T(123),t,'right')
    if t>=T(126): tag(d,X0+16,Y1-58,'TRANSPORTER',VGOLD,22,sa*appear(t,T(126)),glow=False)
    # cholesterol particles from gut
    for k in range(14):
        ph=(t*0.55+k/14)%1; gy=gates[k%3]+((k*37)%30-15)
        if blocked<0.5:
            x=lerp(X0+30,LX-60,ph); y=gy+math.sin(ph*9+k)*8
        else:
            q=ph*2; x=lerp(X0+30,wx-14,min(1,q)) if q<1 else lerp(wx-14,wx-90,(q-1)); y=gy+math.sin(ph*9+k)*8
        aa=sa*min(1,ph*8,(1-ph)*8)
        d.ellipse([x-8,y-8,x+8,y+8],fill=A(VGOLD,aa))
    # blood LDL -> liver clearance
    cl=appear(t,T(140),0.3)
    d.polygon([(LX-30,Y0+90),(X1-20,Y0+70),(X1-20,Y1-40),(LX+20,Y1-70),(LX-60,Y1-130)],outline=A(CYAN if cl<0.5 else GREEN,sa),fill=A((10,40,40),sa*0.5))
    if GL and cl>0: GL.polygon([(LX-30,Y0+90),(X1-20,Y0+70),(X1-20,Y1-40),(LX+20,Y1-70),(LX-60,Y1-130)],outline=A(GREEN,cl*sa))
    nb=8 if t<T(132) else int(lerp(8,3,clamp((t-T(132))/1.2)))
    for k in range(nb):
        ph=(t*(0.18+0.5*cl)+k/8)%1
        x=lerp(wx+60,LX+10 if cl>0.3 else LX-70,ph if cl>0.3 else 0.5+0.45*math.sin(ph*6.28+k)); y=Y0+120+(k*53)%170
        d.ellipse([x-13,y-13,x+13,y+13],outline=A(CYAN,sa),width=3); txt(d,x,y,'L',f(MONOB,16),CYAN,sa,anchor='mm')
    if cl>0: arrow(d,wx+150,Y1-36,LX-40,Y1-36,GREEN,4,sa*cl)
    if t>=T(143): tag(d,X1-16,Y1-60,'CLEARANCE ↑',GREEN,22,sa*appear(t,T(143)),anchor='r')
    # result tags
    ry=936; rx=94
    if t>=T(145): rx=tag(d,rx,ry,'LDL ↓',GREEN,28,sa*appear(t,T(145)))+12
    if t>=T(147): rx=tag(d,rx,ry,'ApoB ↓',GREEN,28,sa*appear(t,T(147)))+12
    if t>=T(151):
        b=appear(t,T(151)); tag(d,rx,ry,'✓ GOOD',GREEN,28,sa*b)
def gauge(d,cx,cy,r,v,a,label):
    segs=[(GREEN,0,0.45),(AMBER,0.45,0.7),(RED,0.7,1.0)]
    for col,u0,u1 in segs:
        d.arc([cx-r,cy-r,cx+r,cy+r],180+u0*180,180+u1*180,fill=A(col,a),width=26)
        if GL: GL.arc([cx-r,cy-r,cx+r,cy+r],180+u0*180,180+u1*180,fill=A(col,0.6*a),width=30)
    for k in range(11):
        an=math.pi+k/10*math.pi; d.line([(cx+(r-40)*math.cos(an),cy+(r-40)*math.sin(an)),(cx+(r-58)*math.cos(an),cy+(r-58)*math.sin(an))],fill=A(MUTED,a),width=3)
    an=math.pi+v*math.pi; d.line([(cx,cy),(cx+(r-30)*math.cos(an),cy+(r-30)*math.sin(an))],fill=A(WHITE,a),width=7)
    d.ellipse([cx-16,cy-16,cx+16,cy+16],fill=A(WHITE,a))
    txt(d,cx,cy+28,label,f(MONOB,24),CREAM,a,anchor='mt')
def sc_s5(im,d,t):          # RIGHT column face: BP gauge, workload, LV wall thickening
    t0,t1=T(153),T(183)-0.05
    if not (t0<=t<t1+0.2): return
    ga=window(t,t0+0.40,t1,0.2,0.2)
    kicker(d,60,428,'NO. 02',t,max(T(156),T(153)+0.42))
    txt(d,60,470,'BLOOD PRESSURE',f(BEB,74),CREAM,appear(t,T(158))*ga)
    gv=0.32;
    if t>=T(163): gv=lerp(gv,0.68,expo((t-T(163))/0.5))
    if t>=T(165): gv=lerp(gv,0.9,expo((t-T(165))/0.5))
    gv+=0.012*math.sin(t*23)*(gv>0.6)
    ga2=appear(t,T(159)-0.1,0.25)*ga
    if ga2>0: gauge(d,295,790,205,gv,ga2,'ARTERIAL PRESSURE')
    if t>=T(163): tag(d,40,575,'ELEVATED',RED,26,appear(t,T(165))*ga) if t>=T(165) else None
    wa=appear(t,T(167)-0.1)*ga
    if wa>0:
        txt(d,60,872,'CARDIAC WORKLOAD',f(MONOB,24),CREAM,wa)
        fr=lerp(0.35,0.92,expo((t-T(167))/0.6)); d.rectangle([60,908,530,944],outline=A((70,74,90),wa),width=2)
        lit_bar(d,63,911,lerp(63,527,fr),941,RED if fr>0.6 else AMBER,wa)
        if GL: GL.rectangle([63,911,lerp(63,527,fr),941],fill=A(RED,0.6*wa))
    ra=appear(t,T(170)-0.1,0.25)*ga
    if ra>0:
        txt(d,60,972,'LEFT VENTRICLE · X-SECTION',f(MONO,22),CYAN,ra)
        th=expo((t-T(174))/1.0)
        ro=lerp(118,150,th); ri=lerp(78,48,th); col=CYAN if th<0.4 else RED
        cx,cy=230,1170; ring(d,cx,cy,ro,ri,col,ra)
        d.line([(cx+ri,cy),(cx+ro,cy)],fill=A(WHITE,ra),width=3)
        for xx in (cx+ri,cx+ro): d.line([(xx,cy-12),(xx,cy+12)],fill=A(WHITE,ra),width=3)
        txt(d,cx+ro+20,cy-46,'WALL',f(MONOB,26),WHITE,ra)
        if th>0.05: tri(d,cx+ro+100,cy-46,RED,True,24,ra)
        if t>=T(176): tag(d,cx+ro+18,cy-4,'LVH',RED,30,appear(t,T(176))*ga)
def sc_s6a(im,d,t):         # FULL: slot 02 returns, telmisartan reveal slam
    t0,t1=T(190)-0.1,T(199)+0.05
    if not (t0<=t<t1+0.25): return
    p=expo((t-t0)/0.22); out=clamp((t-t1)/0.22)
    if out>=1: return
    rv=clamp((t-T(198))/0.18)
    s=1.0 if t<T(198) else lerp(1.06,1.0,expo((t-T(198))/0.12))
    w,h=700*s,170*s; cx=540; cy=lerp(300,470,p)+lerp(0,500,out**2)
    box=(cx-w/2,cy-h/2,cx+w/2,cy+h/2)
    card(im,box,p*(1-out),VGOLD,0.9)
    d=ImageDraw.Draw(im,'RGBA'); x0,y0,x1,y1=box
    txt(d,x0+24,y0+14,'COMPOUND 02',f(MONOB,26),VGOLD,1-out)
    if rv>0:
        txt(d,x0+24,y0+46,'TELMISARTAN',f(BEB,int(118*s)),VGOLD,1-out)
        if GL: GL.text((x0+24,y0+46),'TELMISARTAN',font=f(BEB,int(118*s)),fill=A(VGOLD,0.6*(1-out)))
        tag(d,x1-20,y0+10,'ALL-TIME #1',RED,24,appear(t,T(198)+0.15)*(1-out),anchor='r')
    redaction(d,(x0+24,y0+58,x1-24,y1-16),t,(1-out),rv)
def sc_s6b(im,d,t):         # UP split: AT1 lock & key, vessel relaxes, BP falls
    t0,t1=T(199)+0.42,T(217)-0.05
    if not (t0<=t<t1+0.2): return
    ga=window(t,t0,t1,0.25,0.2); yo=30+lerp(60,0,expo((t-t0)/0.3))
    d.ellipse([70,1040+yo,84,1054+yo],fill=A(RED,ga if int(t*4)%2==0 else ga/3)); txt(d,96,1032+yo,'TELMISARTAN · MECHANISM',f(MONO,26),WHITE,ga)
    fn=f(MONO,26); lab='EVIDENCE 02'; txt(d,1010-d.textlength(lab,font=fn),1032+yo,lab,fn,VGOLD,ga)
    # receptor
    X0,Y0,X1,Y1=70,1080+yo,520,1470+yo
    d.rounded_rectangle([X0,Y0,X1,Y1],radius=12,fill=A(XRAY,0.96*ga),outline=A(CYAN,0.6*ga),width=2)
    my=Y1-80; d.line([(X0+10,my),(X1-10,my)],fill=A(CYAN,ga),width=4);
    for xx in range(X0+20,X1-10,24): d.ellipse([xx-6,my-6,xx+6,my+6],outline=A(CYAN,0.6*ga),width=2)
    cx=X0+225
    d.line([(cx-60,my-6),(cx-60,my-120),],fill=A(VGOLD,ga),width=8); d.line([(cx+60,my-6),(cx+60,my-120)],fill=A(VGOLD,ga),width=8)
    d.arc([cx-60,my-60,cx+60,my+20],0,180,fill=A(VGOLD,0),width=1)
    if GL: GL.line([(cx-60,my-6),(cx-60,my-120)],fill=A(VGOLD,ga),width=14); GL.line([(cx+60,my-6),(cx+60,my-120)],fill=A(VGOLD,ga),width=14)
    if t>=T(205): txt(d,cx,my+18,'AT1 RECEPTOR',f(MONOB,24),VGOLD,ga*appear(t,T(205)),anchor='mt')
    # telmisartan plug drops in on "blocks"
    pp=expo((t-T(200))/0.22)
    if pp>0:
        py=lerp(Y0+40,my-112,pp); d.rounded_rectangle([cx-50,py,cx+50,py+100],radius=10,fill=A(VGOLD,ga)); txt(d,cx,py+50,'TELMI',f(MONOB,24),INK,ga,anchor='mm')
        if GL: GL.rounded_rectangle([cx-54,py-4,cx+54,py+104],radius=12,outline=A(VGOLD,ga),width=10)
    # angiotensin II key arrives and bounces
    ka=appear(t,T(201)-0.1,0.2)
    if ka>0:
        u=clamp((t-T(201))/0.7); hit=T(201)+0.7
        if t<hit: kx,ky=lerp(X1-120,cx+70,expo(u)),lerp(Y0+70,my-170,expo(u))
        else: b=expo((t-hit)/0.4); kx,ky=lerp(cx+70,X1-130,b),lerp(my-170,Y0+90,b)
        d.polygon([(kx,ky),(kx+70,ky-36),(kx+70,ky+36)],fill=A(RED,ga*ka)); txt(d,kx+4,ky-74,'ANG II',f(MONOB,24),RED,ga*ka)
        if t>=hit: cross(d,cx+60,my-210,RED,1.0,ga*appear(t,hit))
    if t>=T(206): tag(d,X0+16,Y0+14,'AT1 BLOCKED',RED,26,ga*appear(t,T(206)))
    # vessel
    X0,X1=550,1010
    d.rounded_rectangle([X0,Y0,X1,Y1],radius=12,fill=A(XRAY,0.96*ga),outline=A(CYAN,0.6*ga),width=2)
    txt(d,X0+16,Y0+14,'VESSEL · X-SECTION',f(MONOB,22),CYAN,ga*appear(t,T(209)-0.4))
    rx=expo((t-T(212))/0.8); vx,vy=X0+170,Y0+175; ro=118; ri=lerp(46,92,rx)
    col=RED if rx<0.4 else GREEN
    ring(d,vx,vy,ro,ri,col,ga)
    for k in range(10):
        an=t*(1.5+3*rx)+k*0.63; rr=ri*0.6*((k*0.37)%1)
        x=vx+rr*math.cos(an); y=vy+rr*math.sin(an); d.ellipse([x-6,y-6,x+6,y+6],fill=A(RED,ga))
    if rx>0.05:
        for an in range(0,360,45):
            a_=math.radians(an); d.line([(vx+(ri-6)*math.cos(a_),vy+(ri-6)*math.sin(a_)),(vx+(ri+16)*math.cos(a_),vy+(ri+16)*math.sin(a_))],fill=A(WHITE,ga*rx*0.8),width=3)
        tag(d,X1-14,Y0+120,'RELAXED',GREEN,22,ga*appear(t,T(212)),anchor='r')
    # BP trace falls
    if t>=T(214)-0.2:
        ba=appear(t,T(214)-0.2)*ga; bx0,bx1,by=X0+70,X1-20,Y1-20
        p=clamp((t-T(215))/0.9)
        pts=[(lerp(bx0,bx1,u/40),by-60+ (0 if u<14 else lerp(0,50,min(1,(u-14)/20)*1.0))*min(1,p*1.6)) for u in range(41)]
        d.line(pts,fill=A(GREEN,ba),width=5)
        if GL: GL.line(pts,fill=A(GREEN,ba),width=10)
        txt(d,X0+16,by-74,'BP',f(MONOB,24),CREAM,ba)
        if t>=T(216): tag(d,bx1,by-110,'BP ↓',GREEN,26,appear(t,T(216))*ga,anchor='r')
def sc_s7(im,d,t):          # FULL + top card: LV mass regression before/after
    t0,t1=T(226)-0.05,T(240)+0.25
    if not (t0<=t<t1+0.2): return
    p=expo((t-t0)/0.22); out=clamp((t-t1)/0.18); a=p*(1-out)
    if a<=0: return
    yo=lerp(-40,0,p)
    box=(60,250+yo,1020,640+yo); card(im,box,a,VGOLD,0.9,'STUDIES · HYPERTENSIVE PATIENTS',None,t)
    d=ImageDraw.Draw(im,'RGBA')
    ra=appear(t,T(228),0.2)*a
    if ra>0:
        cy=418+yo
        ring(d,290,cy,96,34,RED,ra); txt(d,290,cy+100,'BEFORE',f(MONOB,24),MUTED,ra,anchor='mt')
        th=expo((t-T(232))/1.2); col=RED if th<0.4 else GREEN
        ring(d,770,cy,lerp(96,84,th),lerp(34,56,th),col,ra); txt(d,770,cy+100,'AFTER',f(MONOB,24),MUTED,ra,anchor='mt')
        arrow(d,430,cy,620,cy,VGOLD,5,ra*appear(t,T(232)),22)
        txt(d,525,cy-50,'LV MASS',f(MONOB,24),CREAM,ra*appear(t,T(232)),anchor='mm')
        if t>=T(236): tag(d,1000,300+yo,'LV MASS ↓',GREEN,28,appear(t,T(236))*a,anchor='r')
    if t>=T(239):   # verdict slam
        q=expo((t-T(239))/0.10); x0=box[0]; x1=lerp(x0,box[2],q); y=box[3]-74
        if GL: GL.rectangle([x0-4,y-6,x1+4,y+70],outline=A(VGOLD,a),width=10)
        lit_bar(d,x0,y,x1,y+66,VGOLD,a)
        if q>0.6: txt(d,x0+24,y+6,'REGRESSION DOCUMENTED',f(BEB,62),INK,a)
def sc_s8(im,d,t):          # LEFT column face: insulin sensitivity curve + AR grid
    t0,t1=T(240)+0.2,T(269)-0.05
    if not (t0<=t<t1+0.2): return
    ga=window(t,t0+0.42,t1,0.2,0.2)
    kicker(d,560,428,'BEYOND BP',t,max(T(241),T(240)+0.62))
    # card 1: glucose response
    c1=appear(t,T(249)-0.15,0.22)*ga
    if c1>0:
        X0,Y0,X1,Y1=560,480,1040,870; card(im,(X0,Y0,X1,Y1),c1,CYAN,0.9); d=ImageDraw.Draw(im,'RGBA')
        txt(d,X0+24,Y0+16,'INSULIN',f(BEB,58),CREAM,c1); txt(d,X0+24,Y0+70,'SENSITIVITY',f(BEB,58),CREAM,c1)
        txt(d,X0+24,Y0+132,'GLUCOSE AFTER A MEAL',f(MONO,20),MUTED,c1)
        gx0,gx1,gb=X0+30,X1-30,Y1-40
        d.line([(gx0,gb),(gx1,gb)],fill=A((90,94,110),c1),width=2)
        for k,(col,amp,tt) in enumerate([(RED,170,T(249)),(GREEN,80,T(250))]):
            p=clamp((t-tt)/0.8)
            pts=[(lerp(gx0,gx1,u/50),gb-10-amp*math.exp(-((u/50-0.32)/0.16)**2)) for u in range(int(50*p)+1)]
            if len(pts)>1:
                d.line(pts,fill=A(col,c1*(0.55 if (k==0 and t>T(250)) else 1)),width=5)
                if GL and k==1: GL.line(pts,fill=A(col,c1),width=10)
        if t>=T(250)+0.6: tag(d,X1-20,Y0+150,'FLATTER',GREEN,22,appear(t,T(250)+0.6)*ga,anchor='r')
    # card 2: androgen receptors
    c2=appear(t,T(253)-0.15,0.22)*ga
    if c2>0:
        X0,Y0,X1,Y1=560,900,1040,1320; card(im,(X0,Y0,X1,Y1),c2,VGOLD,0.9); d=ImageDraw.Draw(im,'RGBA')
        txt(d,X0+24,Y0+16,'ANDROGEN',f(BEB,58),CREAM,c2); txt(d,X0+24,Y0+70,'RECEPTORS',f(BEB,58),CREAM,c2)
        tag(d,X1-20,Y0+20,'SOME STUDIES',AMBER,20,c2,anchor='r',glow=False)
        lit=3 if t<T(257) else 3+int(clamp((t-T(257))/0.9)*3.999)
        for k in range(6):
            sx=X0+40+(k%3)*140; sy=Y0+160+(k//3)*110
            on=k<lit; col=VGOLD if on else (70,74,90)
            d.arc([sx,sy,sx+70,sy+70],0,180,fill=A(col,c2),width=6); d.line([(sx,sy+35),(sx,sy-6)],fill=A(col,c2),width=6); d.line([(sx+70,sy+35),(sx+70,sy-6)],fill=A(col,c2),width=6)
            if on:
                d.ellipse([sx+14,sy+6,sx+56,sy+48],fill=A(VGOLD,c2))
                if GL: GL.ellipse([sx+6,sy-2,sx+64,sy+56],fill=A(VGOLD,0.7*c2))
        if t>=T(264): tag(d,X0+24,Y1-58,'FULL VIDEO · SOON',VGOLD,22,appear(t,T(264))*ga)
def sc_s9(im,d,t):          # PIP_TOP: two-column comparison table
    t0,t1=T(269),T(287)-0.3
    if not (t0<=t<t1+0.2): return
    ga=window(t,t0+0.42,t1,0.2,0.2)
    kicker(d,60,420,'SIMPLIFIED',t,T(273)-0.2)
    txt(d,60,470,'2',f(BEB,150),VGOLD,appear(t,T(273))*ga); txt(d,150,500,'COMPOUNDS',f(MONOB,26),CREAM,appear(t,T(273))*ga); txt(d,150,540,'2 TARGETS',f(MONOB,26),CREAM,appear(t,T(273)+0.2)*ga)
    txt(d,1020,470,'HEART',f(BEB,64),CREAM,appear(t,T(273)+0.1)*ga,anchor='ra'); txt(d,1020,535,'PROTOCOL',f(BEB,64),VGOLD,appear(t,T(273)+0.2)*ga,anchor='ra')
    cols=[(60,525,'EZETIMIBE',CYAN,T(274),[('TARGET','CHOLESTEROL ABSORPTION',T(277)),('SITE','GUT · NPC1L1',T(278)),('MARKERS','LDL ↓  ApoB ↓',T(278)+0.45)]),
          (555,1020,'TELMISARTAN',VGOLD,T(280),[('TARGET','BLOOD PRESSURE',T(282)),('SITE','AT1 · ANGIOTENSIN II',T(285)),('MARKERS','BP ↓  LV MASS ↓',T(286))])]
    for (x0,x1,hdr,col,th,rows) in cols:
        da=clamp((t-(T(273)))/0.35)
        d.line([(x0,770),(lerp(x0,x1,da),770)],fill=A(col,ga),width=5)
        if GL: GL.line([(x0,770),(lerp(x0,x1,da),770)],fill=A(col,ga),width=10)
        ha=appear(t,th)*ga
        if ha<=0: continue
        d.rectangle([x0,776,x1,1350],fill=A((24,26,34),0.92*ha),outline=A((58,54,48),ha),width=1)
        txt(d,x0+20,790,hdr,f(BEB,66),col,ha)
        for k,(lab,val,tt) in enumerate(rows):
            ra=appear(t,tt,0.12)*ga
            if ra<=0: continue
            y=880+k*155; txt(d,x0+20,y,lab,f(MONO,22),MUTED,ra)
            fn=f(MONOB,32) if '↓' in val else f(BAR,44 if len(val)<17 else 36);
            # wrap long values onto 2 lines
            words=val.split(' '); line=''; lines=[]
            for w_ in words:
                if d.textlength((line+' '+w_).strip(),font=fn)>x1-x0-90: lines.append(line); line=w_
                else: line=(line+' '+w_).strip()
            lines.append(line)
            for j,l in enumerate(lines): txt(d,x0+20,y+32+j*44,l,fn,WHITE,ra)
            check(d,x1-52,y+40,GREEN,0.9,ra)
            d.line([(x0+16,y+140),(x1-16,y+140)],fill=A((50,52,62),ra),width=1)
def sc_s10(im,d,t):         # FULL calm: heartbeat line, 6PM clock, week strip
    # heartbeat line above captions
    t0,t1=T(308),T(344)
    if t0<=t<t1+0.3:
        a=window(t,t0,t1,0.3,0.3); y=1312
        p=clamp((t-t0)/1.4); n=int(W*p)
        pts=[(x,y+ecg_y(x/360-t*0.8*0,1.0)*42) for x in range(14,max(15,n),3)]
        col=RED
        if len(pts)>1:
            d.line(pts,fill=A(col,0.9*a),width=4)
            if GL: GL.line(pts,fill=A(col,a),width=9)
        # travelling bright head
        hx=(t*420)%W; d.ellipse([hx-7,y-7+ecg_y(hx/360,1)*42,hx+7,y+7+ecg_y(hx/360,1)*42],fill=A(WHITE,a*p))
    # clock + week strip card
    c0,c1=T(332)-0.1,T(343)+0.35
    if not (c0<=t<c1+0.2): return
    p=expo((t-c0)/0.22); out=clamp((t-c1)/0.18); a=p*(1-out)
    if a<=0: return
    box=(60,250,1020,540); card(im,box,a,VGOLD,0.88); d=ImageDraw.Draw(im,'RGBA')
    cx,cy,r=200,395,104
    d.ellipse([cx-r,cy-r,cx+r,cy+r],outline=A(CREAM,a),width=5)
    for k in range(12):
        an=k/12*2*math.pi; d.line([(cx+(r-8)*math.sin(an),cy-(r-8)*math.cos(an)),(cx+(r-22)*math.sin(an),cy-(r-22)*math.cos(an))],fill=A(CREAM,a),width=3)
    q=expo((t-c0)/((T(334)-c0)+0.05)); hh=lerp(0,6,q); mm=lerp(0,12*6,q)%12
    for (val,L_,w_,col) in [(hh/12,58,9,VGOLD),(mm/12,86,5,WHITE)]:
        an=val*2*math.pi; d.line([(cx,cy),(cx+L_*math.sin(an),cy-L_*math.cos(an))],fill=A(col,a),width=w_)
    if GL: GL.ellipse([cx-r,cy-r,cx+r,cy+r],outline=A(VGOLD,a),width=8)
    d.ellipse([cx-9,cy-9,cx+9,cy+9],fill=A(VGOLD,a))
    if t>=T(334): txt(d,350,272,'6:00 PM',f(BEB,96),VGOLD,a*appear(t,T(334)))
    days='MTWTFSS'
    for k,ch in enumerate(days):
        x=350+k*92; y=400
        on=appear(t,T(335)+k*0.07,0.1); pulse=appear(t,T(342)+k*0.05,0.1)*(1-clamp((t-T(342)-k*0.05-0.25)/0.3))
        col=GREEN if on>0.5 else (70,74,90)
        d.rounded_rectangle([x,y,x+76,y+96],radius=10,outline=A(col,a),width=3,fill=A(GREEN,(0.18*on+0.35*pulse)*a))
        txt(d,x+38,y+24,ch,f(BEB,50),WHITE,a,anchor='mt')
        if on>0.5:
            check(d,x+24,y+64,GREEN,0.55,a)
def sc_cta(im,d,t):         # UP split: free breakdown + COMMENT "HEALTH"
    t0=T(353)-0.25+0.42
    if t<t0: return
    ga=appear(t,t0,0.3); yo=30+lerp(60,0,expo((t-t0)/0.3))
    global LOGO
    if LOGO is None:
        lg=Image.open(S+'/work/logo.jpg').convert('RGB'); s=min(lg.size); lg=lg.crop(((lg.width-s)//2,(lg.height-s)//2,(lg.width+s)//2,(lg.height+s)//2)).resize((190,190),Image.LANCZOS)
        m=Image.new('L',(190,190),0); ImageDraw.Draw(m).ellipse([0,0,189,189],fill=255); lg.putalpha(m); LOGO=lg
    lg=LOGO.copy(); lg.putalpha(lg.split()[3].point(lambda v:int(v*ga))); im.paste(lg,(70,int(1040+yo)),lg)
    d=ImageDraw.Draw(im,'RGBA')
    d.ellipse([68,1038+yo,262,1232+yo],outline=A(GOLD,ga),width=3)
    txt(d,290,1040+yo,'FREE · CARDIOVASCULAR',f(MONOB,32),VGOLD,appear(t,T(354))*ga)
    txt(d,290,1080+yo,'BLOODWORK BREAKDOWN',f(MONOB,32),VGOLD,appear(t,T(357))*ga)
    for k,(nm,tt) in enumerate([('DOSAGES',T(364)),('TIMING',T(365)),('HEART COMPOUNDS',T(369))]):
        ra=appear(t,tt,0.12)*ga
        if ra<=0: continue
        y=1132+yo+k*52; check(d,290,y+4,GREEN,0.9,ra); txt(d,338,y-2,nm,f(BAR,46),WHITE,ra)
    if t>=T(376):
        b=expo((t-T(376))/0.12); s=lerp(1.12,1.0,b)
        fn=f(BEB,int(92*s)); label='COMMENT  "HEALTH"'; tw=d.textlength(label,font=fn)
        x0=540-(tw+60)/2; y=1300+yo
        lit_bar(d,x0,y,x0+tw+60,y+int(104*s),VGOLD,b); txt(d,x0+30,y+8,label,fn,INK,b)
        if GL: GL.rectangle([x0-4,y-4,x0+tw+64,y+int(104*s)+4],outline=A(VGOLD,b),width=12)
    fn=f(MONO,20); s_='FOR RESEARCH & EDUCATIONAL PURPOSES ONLY'; txt(d,540-d.textlength(s_,font=fn)/2,1426+yo,s_,fn,MUTED,ga)
LOGO=None
SCENES=[sc_s1,sc_s2,sc_s3,sc_s4,sc_s5,sc_s6a,sc_s6b,sc_s7,sc_s8,sc_s9,sc_s10,sc_cta]
SHAKES=[T(50)+0.10,T(198)+0.0,T(239)+0.10]
# ---------------- captions (saved setup: Bebas, 1-3 words, red block on the active word) ----------------
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
    end=WORDS[lo[-1]]['e']+0.6
    nxt=[g for g in GROUPS if WORDS[g[0]]['s']>WORDS[lo[0]]['s']]
    if t>end and (not nxt or WORDS[nxt[0][0]]['s']>t): return None
    return lo
def cap_word(w):
    w=w.strip().rstrip(',.?!')
    if w in ('ApoB','NPC1L1','AT1','6PM'): return w.upper() if w!='ApoB' else 'APOB'
    return w.upper()
def captions(im,t,cy):
    g=group_at(t)
    if not g: return
    d=ImageDraw.Draw(im,'RGBA')
    ws=[cap_word(WORDS[i]['w']) for i in g]
    size=112
    while True:
        fn=f(BEB,size); sp=d.textlength(' ',font=fn)+14; wd=[d.textlength(w,font=fn) for w in ws]; tot=sum(wd)+sp*(len(ws)-1)
        if tot<=900: break
        size-=4
    xs=[];x=(W-tot)/2
    for w_ in wd: xs.append(x); x+=w_+sp
    act=0
    for k,i in enumerate(g):
        if WORDS[i]['s']<=t: act=k
    g0=WORDS[g[0]]['s']; s=lerp(0.9,1,expo((t-g0)/0.10))
    CH=size+80
    cap=Image.new('RGBA',(W,CH),(0,0,0,0)); cd=ImageDraw.Draw(cap); shd=Image.new('RGBA',(W,CH),(0,0,0,0)); sd=ImageDraw.Draw(shd)
    prev=max(0,act-1); bt=expo((t-WORDS[g[act]]['s'])/0.07) if act>0 else 1
    bx0=lerp(xs[prev],xs[act],bt)-18; bx1=lerp(xs[prev]+wd[prev],xs[act]+wd[act],bt)+18
    for k,(w_,x_) in enumerate(zip(ws,xs)):
        if k!=act: sd.text((x_+4,46),w_,font=fn,fill=(0,0,0,210))
    cap.alpha_composite(shd.filter(ImageFilter.GaussianBlur(6)))
    lit_bar(cd,bx0,40+size*0.02,bx1,40+size*0.98,RED)
    for k,(w_,x_) in enumerate(zip(ws,xs)): cd.text((x_,40),w_,font=fn,fill=CREAM,stroke_width=0 if k==act else 3,stroke_fill=(0,0,0))
    if abs(s-1)>0.002:
        cap=cap.resize((int(W*s),int(CH*s)),Image.BICUBIC); ox=int((W-cap.width)/2); oy=int(cy-40-(cap.height-CH)/2)
    else: ox,oy=0,int(cy-40)
    im.paste(cap,(ox,oy),cap)
# ---------------- frame ----------------
_scrim=None
def frame(src,t):
    global GL,BG,_scrim
    if BG is None: BG=make_bg()
    im,L=place_footage(src,t)
    # readability scrim on full-frame footage only (graphics layer, footage itself is not graded)
    full=1-L['fr']
    if full>0.01:
        if _scrim is None:
            yy=np.arange(H); a=np.where(yy>1250,np.clip((yy-1250)/240,0,1)*120,0); a=np.maximum(a,np.where(yy<400,(1-yy/400)*110,0))
            _scrim=a
        sc=(np.repeat(_scrim[:,None],W,1)*full).astype(np.uint8)
        im.alpha_composite(Image.merge('RGBA',[Image.new('L',(W,H),c) for c in NAVY]+[Image.fromarray(sc)]))
    im=im.convert('RGB')   # draw on RGB so ImageDraw 'RGBA' mode alpha-blends (on RGBA it overwrites)
    glow=Image.new('RGBA',(W,H),(0,0,0,0)); GL=ImageDraw.Draw(glow,'RGBA')
    d=ImageDraw.Draw(im,'RGBA')
    window_frame(im,L,t)
    for fn_ in SCENES:
        fn_(im,ImageDraw.Draw(im,'RGBA'),t)
    sc_band(im,ImageDraw.Draw(im,'RGBA'),t)
    sc_hook(im,ImageDraw.Draw(im,'RGBA'),t)
    GL=None
    if glow.getbbox():
        sm=glow.resize((W//4,H//4),Image.BILINEAR)
        g1=np.asarray(sm.filter(ImageFilter.GaussianBlur(3.5))).astype(np.float32)/255; g2=np.asarray(sm.filter(ImageFilter.GaussianBlur(10))).astype(np.float32)/255
        prem=np.clip(g1[...,:3]*g1[...,3:]*2.3+g2[...,:3]*g2[...,3:]*1.8,0,1)
        prem=np.asarray(Image.fromarray((prem*255).astype(np.uint8)).resize((W,H),Image.BILINEAR)).astype(np.float32)/255
        b=np.asarray(im.convert('RGB')).astype(np.float32)/255
        im=Image.fromarray(((1-(1-b)*(1-prem))*255).astype(np.uint8))
    d=ImageDraw.Draw(im,'RGBA'); d.rectangle([0,0,7,H],fill=GOLD)
    captions(im,t,L['cy'])
    out=im.convert('RGB')
    for ts in SHAKES:
        k=round((t-ts)*FPS)
        if k in (0,1):
            dx=[9,-5][k]; z=1.025; big=out.resize((int(W*z),int(H*z)),Image.BICUBIC); ox=(big.width-W)//2-dx; oy=(big.height-H)//2
            out=big.crop((ox,oy,ox+W,oy+H)); ImageDraw.Draw(out).rectangle([0,0,7,H],fill=GOLD)
    return out
if __name__=='__main__':
    mode=sys.argv[2]; SRC=WK+'assembled.mp4'
    if mode=='stills':
        import os; os.makedirs(WK+'qc',exist_ok=True)
        for tt in [float(x) for x in sys.argv[3:]]:
            n=int(round(tt*FPS))
            buf=subprocess.run(['ffmpeg','-v','error','-i',SRC,'-vf',f'select=eq(n\\,{n})','-frames:v','1','-f','rawvideo','-pix_fmt','rgb24','-'],capture_output=True).stdout
            frame(Image.frombuffer('RGB',(W,H),buf),n/FPS).resize((540,960),Image.LANCZOS).save(WK+f'qc/st_{tt:07.2f}.jpg',quality=88)
        sys.exit()
    n0,n1,out=int(sys.argv[3]),int(sys.argv[4]),sys.argv[5]
    dec=subprocess.Popen(['ffmpeg','-v','error','-i',SRC,'-vf',f'select=between(n\\,{n0}\\,{n1-1})','-fps_mode','passthrough','-f','rawvideo','-pix_fmt','rgb24','-'],stdout=subprocess.PIPE)
    enc=subprocess.Popen(['ffmpeg','-v','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-','-c:v','libx264','-crf','14','-preset','fast','-pix_fmt','yuv420p',out],stdin=subprocess.PIPE)
    for n in range(n0,n1):
        buf=dec.stdout.read(W*H*3)
        if len(buf)<W*H*3: print('short',n); break
        enc.stdin.write(frame(Image.frombuffer('RGB',(W,H),buf),n/FPS).tobytes())
    enc.stdin.close(); enc.wait(); dec.kill(); print('done',n0,n1)
