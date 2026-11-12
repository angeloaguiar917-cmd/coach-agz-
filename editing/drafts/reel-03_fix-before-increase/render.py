# Fix Before Increase — @coach.agz Reel render (1080x1920, 30 fps)
import json, subprocess, sys, math, os
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
HERE=os.path.dirname(os.path.abspath(__file__)); F=HERE+'/../fonts/'
W,H=1080,1920; FPS=30
TR=json.load(open(HERE+'/trim.json')); KEEP=TR['keep']
SRCF=[i for a,b in KEEP for i in range(a,b)]; N=len(SRCF); DUR=N/FPS
WORDS=json.load(open(HERE+'/words_cut.json'))
FACES=json.load(open(HERE+'/../faces.json'))
LOGO_PATH=HERE+'/../../../../../../home/user/coach-agz-/editing/brand/logo/coach-agz-logo-round.jpg'
LOGO_PATH='/home/user/coach-agz-/editing/brand/logo/coach-agz-logo-round.jpg'
GOLD=(201,169,110); CREAM=(244,241,234); NAVY=(14,17,23); PANEL=(24,26,34); MUTED=(184,184,188); MUTED2=(124,124,130)
RED=(255,34,28); VGOLD=(255,194,26); CYAN=(0,229,255); GREEN=(30,255,110); DEEP=(2,3,8); INK=(6,8,14); WHITE=(255,255,255)
CRIM=(200,16,46); CRIM2=(224,36,63); AMBER=(240,160,48); BLUE=(79,163,224); SGREEN=(60,203,106)
MONO='JBMono-500.ttf'; MONOB='JBMono-700.ttf'; BEB='BebasNeue.ttf'; DMB='DMSans-700.ttf'; DMR='DMSans-400.ttf'; DMM='DMSans-500.ttf'
BAR8='Barlow-800.ttf'; BAR7='Barlow-700.ttf'; BAR6='Barlow-600.ttf'
_fc={}
def f(n,s):
    k=(n,int(s))
    if k not in _fc: _fc[k]=ImageFont.truetype(F+n,int(s))
    return _fc[k]
def clamp(x,a=0,b=1): return max(a,min(b,x))
def expo(x): x=clamp(x); return 1 if x>=1 else 1-2**(-10*x)
def ease_io(x): x=clamp(x); return 4*x**3 if x<.5 else 1-(-2*x+2)**3/2
def cubic(x): x=clamp(x); return 1-(1-x)**3
def lerp(a,b,t): return a+(b-a)*t
def A(c,a): return tuple(c[:3])+(int(clamp(a)*255),)
def ap(t,t0,d=0.16): return expo((t-t0)/d)

# ---------- timeline helpers ----------
src_cuts=[3.6,11.567,16.133,21.2,27.833,30.167,38.583,45.867,61.9,74.133]
def out_of_src(ts):
    fr=round(ts*FPS); best=None
    for k,s in enumerate(SRCF):
        if s>=fr: return k/FPS
    return DUR
joins=[]; acc=0
for a,b in KEEP[:-1]: acc+=b-a; joins.append(acc/FPS)
_B=sorted(set([round(out_of_src(c)*FPS)/FPS for c in src_cuts]+[round(j*FPS)/FPS for j in joins]))
BOUNDS=[]
for b in _B:
    if BOUNDS and b-BOUNDS[-1]<0.25: BOUNDS[-1]=b; continue
    BOUNDS.append(b)
def seg_idx(t): return sum(1 for b in BOUNDS if b<=t+1e-6)
MID=DUR/2
TOPIC_END=min(BOUNDS,key=lambda b:abs(b-MID))

# face centre per output frame (smoothed, src time)
FT=np.array([o['t'] for o in FACES]); FB=[o['b'] for o in FACES]
def face_c(n):
    ts=SRCF[min(n,N-1)]/FPS
    xs=[];ys=[]
    for o in FACES:
        if abs(o['t']-ts)<=1.0 and o['b'] and o['b'][2]>0.25:
            b=o['b']; xs.append((b[0]+b[2]/2)*W); ys.append((b[1]+b[3]*0.45)*H)
    if not xs: return W/2,H*0.52
    return float(np.median(xs)),float(np.median(ys))
FACEC=None

# ---------- primitives ----------
GL=None
def brackets(d,x0,y0,x1,y1,col,L=34,w=4):
    for (cx,cy,sx,sy) in [(x0,y0,1,1),(x1,y0,-1,1),(x0,y1,1,-1),(x1,y1,-1,-1)]:
        d.line([(cx,cy),(cx+sx*L,cy)],fill=col,width=w); d.line([(cx,cy),(cx,cy+sy*L)],fill=col,width=w)
def lit_bar(d,x0,y0,x1,y1,col,a=1.0):
    h=max(1,int(y1-y0))
    if x1<=x0: return
    for i in range(h):
        k=i/h; c=tuple(int(min(255,v*(1.18-0.36*k)+(40 if k<0.12 else 0))) for v in col)
        d.line([(x0,y0+i),(x1,y0+i)],fill=c+(int(255*a),))
def tag(d,x,y,label,col=RED,size=32,a=1.0,glow=True,font=None):
    fn=f(font or MONOB,size); tw=d.textlength(label,font=fn); h=size+18
    lit_bar(d,x,y,x+tw+28,y+h,col,a); d.text((x+14,y+6),label,font=fn,fill=A(WHITE if col not in (VGOLD,GREEN,GOLD) else INK,a))
    if GL and glow: GL.rectangle([x-4,y-4,x+tw+32,y+h+4],outline=A(col,a),width=8)
    return x+tw+28
def txt(d,x,y,s,font,col,a=1.0,anchor=None):
    d.text((x,y),s,font=font,fill=A(col,a),anchor=anchor)
def check(d,x,y,col,s=1.0,a=1.0):
    pts=[(x,y+16*s),(x+10*s,y+28*s),(x+30*s,y+2*s)]
    d.line(pts,fill=A(col,a),width=int(6*s))
    if GL: GL.line(pts,fill=A(col,a),width=int(12*s))
def cross(d,x,y,col,s=1.0,a=1.0):
    for p in [[(x,y),(x+28*s,y+28*s)],[(x+28*s,y),(x,y+28*s)]]:
        d.line(p,fill=A(col,a),width=int(6*s))
        if GL: GL.line(p,fill=A(col,a),width=12)
def arrow(d,x0,y0,x1,y1,col,w=5,a=1.0):
    d.line([(x0,y0),(x1,y1)],fill=A(col,a),width=w)
    ang=math.atan2(y1-y0,x1-x0); L=18
    d.polygon([(x1,y1),(x1-L*math.cos(ang-0.45),y1-L*math.sin(ang-0.45)),(x1-L*math.cos(ang+0.45),y1-L*math.sin(ang+0.45))],fill=A(col,a))
def flow(d,x0,y0,x1,y1,t,col,n=5,speed=0.9,a=1.0,r=7):
    for k in range(n):
        p=(t*speed+k/n)%1
        x=lerp(x0,x1,p); y=lerp(y0,y1,p); fa=a*min(1,p*6,(1-p)*6)
        d.ellipse([x-r,y-r,x+r,y+r],fill=A(col,fa))
        if GL: GL.ellipse([x-r*2,y-r*2,x+r*2,y+r*2],fill=A(col,fa))
def hexagon(d,cx,cy,r,col,a=1.0,label='AROMATASE',glow=1.0):
    pts=[(cx+r*math.cos(math.pi/3*i+math.pi/6),cy+r*math.sin(math.pi/3*i+math.pi/6)) for i in range(6)]
    d.polygon(pts,fill=A((10,14,24),0.95*a)); d.line(pts+[pts[0]],fill=A(col,a),width=5)
    if GL: GL.line(pts+[pts[0]],fill=A(col,a*glow),width=12)
    fn=f(BEB,34); tw=d.textlength(label,font=fn); d.text((cx-tw/2,cy-20),label,font=fn,fill=A(WHITE,a))
def kicker(d,x,y,label,col,t,t0,a=1.0,size=30):
    p=ap(t,t0,0.18); d.line([(x,y+size*0.55),(x+lerp(0,46,p),y+size*0.55)],fill=A(col,a),width=4)
    q=clamp((t-t0-0.08)/0.25); n=int(len(label)*q)
    fn=f(BAR7,size); x2=x+62
    for ch in label[:n]:
        d.text((x2,y),ch,font=fn,fill=A(col,a)); x2+=d.textlength(ch,font=fn)+size*0.22
def frosted(im,box,dark=0.86,blur=10,col=DEEP,radius=0):
    x0,y0,x1,y1=[int(v) for v in box]
    x0=max(0,x0);y0=max(0,y0);x1=min(W,x1);y1=min(H,y1)
    if x1<=x0 or y1<=y0: return
    reg=im.crop((x0,y0,x1,y1)).convert('RGB').filter(ImageFilter.GaussianBlur(blur))
    reg=Image.blend(reg,Image.new('RGB',reg.size,col),dark).convert('RGBA')
    if radius:
        m=Image.new('L',reg.size,0); ImageDraw.Draw(m).rounded_rectangle([0,0,reg.size[0]-1,reg.size[1]-1],radius=radius,fill=255)
        im.paste(reg,(x0,y0),m)
    else: im.paste(reg,(x0,y0))
def wm(d,x1,y1,a,col=MUTED2):
    fn=f(MONO,22); s='@COACH.AGZ'; tw=d.textlength(s,font=fn); d.text((x1-tw-24,y1-40),s,font=fn,fill=A(col,a))

_logo=None
def logo(size):
    global _logo
    if _logo is None: _logo=Image.open(LOGO_PATH).convert('RGB')
    im=_logo.resize((size,size),Image.LANCZOS).convert('RGBA')
    m=Image.new('L',(size,size),0); ImageDraw.Draw(m).ellipse([0,0,size-1,size-1],fill=255); im.putalpha(m); return im

# ---------- containers ----------
PB=(60,360,1020,860)
def container(im,style,box,t,t0,t1,cut_out=False):
    """returns (alpha, offset_y). Draws background of container."""
    pin=expo((t-t0)/0.24); pout=0 if cut_out else clamp((t-t1)/0.15)
    al=pin*(1-pout)
    if al<=0: return 0,0
    dy=lerp(46,0,pin)
    x0,y0,x1,y1=box; y0+=dy; y1+=dy
    if style=='glass':
        frosted(im,(x0,y0,x1,y1),0.88*al,10)
        d=ImageDraw.Draw(im,'RGBA')
        d.rectangle([x0,y0,x1,y1],outline=A(VGOLD,0.7*al),width=3); brackets(d,x0,y0,x1,y1,A(VGOLD,al),46,7)
        if GL: GL.rectangle([x0,y0,x1,y1],outline=A(VGOLD,0.45*al),width=6); brackets(GL,x0,y0,x1,y1,A(VGOLD,al),46,14)
    elif style=='navy':
        frosted(im,(x0,y0,x1,y1),0.93*al,14,NAVY)
        d=ImageDraw.Draw(im,'RGBA')
        # warm glow top-right
        d.rectangle([x0,y0,x1,y1],outline=A((58,54,48),al),width=2)
        h=lerp(0,y1-y0,expo((t-t0-0.04)/0.3)); d.rectangle([x0,y0,x0+5,y0+h],fill=A(GOLD,al))
    elif style=='crimson':
        frosted(im,(x0,y0,x1,y1),0.90*al,10,(12,12,14),radius=26)
        d=ImageDraw.Draw(im,'RGBA')
        d.rounded_rectangle([x0,y0,x1,y1],radius=26,outline=A((60,60,66),al),width=2)
        h=lerp(0,y1-y0-40,expo((t-t0+0.06)/0.22)); d.rounded_rectangle([x0,y0+20,x0+10,y0+20+h],radius=4,fill=A(CRIM,al))
        if GL: GL.rectangle([x0,y0+20,x0+10,y0+20+h],fill=A(CRIM,al*0.6))
    return al,dy

def layer_blit(im,lay,al,blur=0):
    if blur>0.5: lay=lay.filter(ImageFilter.GaussianBlur(blur))
    if al<1: lay.putalpha(lay.split()[3].point(lambda v:int(v*al)))
    im.alpha_composite(lay)

# ================= SCENES (times in output seconds) =================
def S_gauge(d,t,dy):   # E2 gauge + symptoms (crimson card)
    x0,y0=PB[0],PB[1]+dy
    kicker(d,x0+44,y0+30,'ESTRADIOL  ·  E2',CRIM2,t,6.05)
    cx,cy,r=300,y0+330,190
    # spectrum arc
    segs=60
    for i in range(segs):
        a0=180+180*i/segs; a1=180+180*(i+1)/segs+0.6; k=i/(segs-1)
        if k<0.33: c=tuple(int(lerp(BLUE[j],SGREEN[j],k/0.33)) for j in range(3))
        elif k<0.66: c=tuple(int(lerp(SGREEN[j],AMBER[j],(k-0.33)/0.33)) for j in range(3))
        else: c=tuple(int(lerp(AMBER[j],RED[j],(k-0.66)/0.34)) for j in range(3))
        d.arc([cx-r,cy-r,cx+r,cy+r],a0,a1,fill=A(c,1),width=26)
    if GL: GL.arc([cx-r,cy-r,cx+r,cy+r],300,360,fill=A(RED,0.8),width=30)
    for k,lb in [(0.02,'LOW'),(0.5,'RANGE'),(0.98,'HIGH')]:
        ang=math.radians(180+180*k); tx=cx+(r+44)*math.cos(ang); ty=cy+(r+44)*math.sin(ang)
        txt(d,tx,ty,lb,f(MONO,22),MUTED,1,'mm')
    v=0.42 if t<6.3 else lerp(0.42,0.95,cubic((t-6.3)/1.1))
    if t>7.4: v=0.95+0.012*math.sin((t-7.4)*38)*math.exp(-(t-7.4)*5)
    ang=math.radians(180+180*v)
    nx=cx+(r-30)*math.cos(ang); ny=cy+(r-30)*math.sin(ang)
    d.line([(cx,cy),(nx,ny)],fill=A(WHITE,1),width=8); d.ellipse([cx-20,cy-20,cx+20,cy+20],fill=A(WHITE,1))
    if GL and v>0.8: GL.line([(cx,cy),(nx,ny)],fill=A(RED,0.9),width=14)
    if t>=7.4:
        tag(d,cx-80,cy+40,'E2  HIGH',RED,34,ap(t,7.4,0.1))
    else:
        txt(d,cx,cy+66,'READING…',f(MONO,26),MUTED,1,'mm')
    # symptoms
    sx=575
    txt(d,sx,y0+120,'SYMPTOMS',f(MONO,24),MUTED2,ap(t,6.2))
    d.line([(sx,y0+156),(980,y0+156)],fill=A((70,70,78),ap(t,6.2)),width=2)
    rows=[(8.4,'SORE NIPPLES','01'),(9.5,'WATER RETENTION','02')]
    for i,(tt,lb,n) in enumerate(rows):
        a=ap(t,tt,0.12)
        if a<=0: continue
        yy=y0+186+i*126; xx=sx+lerp(30,0,a)
        d.rectangle([xx,yy,980,yy+100],fill=A((40,10,16),a),outline=A(RED,a),width=3)
        if GL: GL.rectangle([xx,yy,980,yy+100],outline=A(RED,a*0.7),width=8)
        cross(d,xx+22,yy+36,RED,1.0,a)
        txt(d,xx+70,yy+14,lb,f(BEB,52),WHITE,a); txt(d,xx+72,yy+66,'FLAG '+n,f(MONO,20),(255,130,120),a)
    if t>=10.6:
        a=ap(t,10.6,0.12); tag(d,sx,y0+446,"WON'T RESOLVE",RED,26,a)
    wm(d,PB[2],PB[3]+dy,1)

def bottle(d,cx,cy,name,sub,cls,a,rot=0):
    w,h=190,270
    x0,y0=cx-w/2,cy-h/2
    d.rounded_rectangle([x0+18,y0-48,x0+w-18,y0+4],radius=10,fill=A((235,235,238),a))
    for k in range(5): d.line([(x0+30,y0-40+k*9),(x0+w-30,y0-40+k*9)],fill=A((190,190,196),a),width=2)
    d.rounded_rectangle([x0,y0,x0+w,y0+h],radius=26,fill=A((120,58,14),0.92*a),outline=A((200,120,40),a),width=3)
    d.rectangle([x0+8,y0+10,x0+16,y0+h-30],fill=A((255,190,110),0.35*a))
    d.rectangle([x0+12,y0+60,x0+w-12,y0+h-50],fill=A((242,240,234),a))
    d.rectangle([x0+12,y0+60,x0+w-12,y0+92],fill=A((210,10,20),a))
    txt(d,cx,y0+76,'Rx',f(MONOB,22),WHITE,a,'mm')
    fn=f(BEB,46 if len(name)<10 else 31); txt(d,cx,y0+124,name,fn,INK,a,'mm')
    txt(d,cx,y0+160,sub,f(MONO,17),(60,60,66),a,'mm')
    txt(d,cx,y0+192,cls,f(MONOB,20),(210,10,20),a,'mm')
def S_rx(d,t,dy):
    x0,y0=PB[0],PB[1]+dy
    txt(d,x0+40,y0+28,'THE FIRST REACH',f(MONOB,26),VGOLD,ap(t,12.4));
    for (tt,cx,nm,sb,cl) in [(12.55,330,'NOLVADEX','tamoxifen','SERM'),(14.35,750,'ANASTROZOLE','aromatase inhib.','AI')]:
        a=ap(t,tt,0.12)
        if a<=0: continue
        cy=y0+300+lerp(-60,0,expo((t-tt)/0.14))
        if t-tt>0.14 and t-tt<0.3: cy+=3*math.sin((t-tt-0.14)*60)*math.exp(-(t-tt-0.14)*20)
        d.ellipse([cx-90,y0+440,cx+90,y0+462],fill=A((0,0,0),0.5*a))
        bottle(d,cx,cy,nm,sb,cl,a)
    if t>=12.9: txt(d,540,y0+300,'OR',f(BEB,60),MUTED,ap(t,13.6),'mm')
    if t>=15.3:
        p=expo((t-15.3)/0.09); s=lerp(1.7,1.0,p)
        st=Image.new('RGBA',(620,170),(0,0,0,0)); sd=ImageDraw.Draw(st)
        sd.rectangle([6,6,614,164],outline=(255,34,28,255),width=10); sd.rectangle([20,20,600,150],outline=(255,34,28,255),width=3)
        sd.text((310,88),'WRONG FIX',font=f(BEB,130),fill=(255,34,28,255),anchor='mm')
        st=st.rotate(-7,expand=True,resample=Image.BICUBIC)
        st=st.resize((int(st.width*s),int(st.height*s)),Image.BICUBIC)
        return ('stamp',st,(540-st.width//2,int(y0+290-st.height//2)),p)
    wm(d,PB[2],PB[3]+dy,1)

def S_kinetic(d,t,dy):   # no container: kinetic type
    a=1.0
    kicker(d,90,400,'THE REAL PROBLEM',VGOLD,t,16.0,1,34)
    if t>=16.95:
        p=expo((t-16.95)/0.18); x=lerp(-500,90,p)
        txt(d,x,470,'NOT THE COMPOUND',f(BEB,96),CREAM,p)
        if t>=17.3:
            q=expo((t-17.3)/0.2); d.line([(90,525),(lerp(90,700,q),525)],fill=A(RED,1),width=9)
            if GL: GL.line([(90,525),(lerp(90,700,q),525)],fill=A(RED,1),width=16)
    if t>=17.0:
        a2=ap(t,17.0,0.12); tag(d,90,600,'THE DRIVE-THRU',RED,34,a2)
        if t>=18.4: tag(d,440,600,'TOO MUCH',RED,34,ap(t,18.4,0.12))
    if t>=20.2:
        p=expo((t-20.2)/0.10); s=lerp(1.35,1.0,p)
        fn=f(BEB,int(210*s)); txt(d,540,770,'BODY FAT',fn,RED,p,'mm')
        if GL: GL.text((540,770),'BODY FAT',font=fn,fill=A(RED,0.5*p),anchor='mm')

def adipocyte_cluster(d,cx,cy,a,t,scan=None):
    cells=[(0,0,62),(-96,-40,52),(92,-48,56),(-70,74,54),(70,72,58),(0,-112,46),(-150,32,40),(150,30,42)]
    for (dx,dy,r) in cells:
        x,y=cx+dx,cy+dy
        d.ellipse([x-r,y-r,x+r,y+r],fill=A((60,46,10),0.85*a),outline=A(VGOLD,a),width=3)
        d.ellipse([x+r*0.35,y+r*0.25,x+r*0.35+12,y+r*0.25+12],fill=A((255,220,120),a))
    if GL:
        for (dx,dy,r) in cells: GL.ellipse([cx+dx-r,cy+dy-r,cx+dx+r,cy+dy+r],outline=A(VGOLD,0.5*a),width=6)
    if scan is not None:
        y=cy-170+340*scan; d.line([(cx-210,y),(cx+210,y)],fill=A(CYAN,a),width=3)
        if GL: GL.line([(cx-210,y),(cx+210,y)],fill=A(CYAN,a),width=12)
def S_mech(d,t,dy):
    x0,y0=PB[0],PB[1]+dy
    txt(d,x0+40,y0+26,'MECHANISM',f(MONOB,26),WHITE,1); txt(d,PB[2]-40,y0+26,'ADIPOSE',f(MONOB,26),VGOLD,1,'ra')
    cx,cy=250,y0+300
    sc=None
    if 24.3<=t<25.3: sc=(t-24.3)/1.0
    adipocyte_cluster(d,cx,cy,ap(t,21.4,0.2),t,sc)
    txt(d,cx,y0+90,'FAT TISSUE',f(BEB,44),CREAM,ap(t,21.9)*(1-ap(t,24.3,0.1)),'mm')
    if t>=22.6:
        a=ap(t,22.6,0.12); x=tag(d,x0+40,y0+420,'STORAGE',(80,80,90),28,a,glow=False)
        if t>=23.05:
            q=expo((t-23.05)/0.12); d.line([(x0+34,y0+443),(lerp(x0+34,x+6,q),y0+443)],fill=A(RED,1),width=6)
    if t>=24.3:
        tag(d,x0+40,y0+68,'ACTIVE ENDOCRINE ORGAN',CYAN,26,ap(t,24.4,0.12))
    hx,hy=600,y0+300
    if t>=25.8:
        a=ap(t,25.8,0.14); g=1.0+0.6*math.sin(t*9) if t>26.8 else 1
        hexagon(d,hx,hy,92,VGOLD,a,glow=g)
        arrow(d,cx+200,hy,hx-100,hy,VGOLD,5,a)
        if t>=26.6: tag(d,hx-110,hy+112,'OVEREXPRESSED',RED,24,ap(t,26.6,0.1))
    # T -> E2
    if t>=27.0:
        a=ap(t,27.0,0.14)
        d.rounded_rectangle([hx-70,y0+70,hx+70,y0+140],radius=12,fill=A((10,14,24),a),outline=A(CYAN,a),width=4)
        txt(d,hx,y0+105,'T',f(BEB,52),WHITE,a,'mm'); arrow(d,hx,y0+142,hx,hy-96,CYAN,4,a)
        flow(d,hx,y0+146,hx,hy-96,t,CYAN,4,1.1,a)
        ex,ey=880,hy
        rate=1.0 if t<28.7 else 1.0+0.25*math.sin((t-28.7)*14)*math.exp(-(t-28.7)*3)
        d.rounded_rectangle([ex-80,ey-56,ex+80,ey+56],radius=12,fill=A((40,8,10),a),outline=A(RED,a),width=4)
        txt(d,ex,ey-4,'E2',f(BEB,62),WHITE,a,'mm')
        arrow(d,hx+96,hy,ex-86,ey,RED,5,a); flow(d,hx+96,hy,ex-86,ey,t,RED,6 if t>28.7 else 3,1.4,a,8)
        if GL: GL.rounded_rectangle([ex-80,ey-56,ex+80,ey+56],radius=12,outline=A(RED,a*rate*0.8),width=10)
    if t>=28.7:
        tag(d,780,y0+400,'MORE E2',RED,32,ap(t,28.7,0.1))
    wm(d,PB[2],PB[3]+dy,1)

def S_stat(d,t,dy):
    x0,y0=PB[0],PB[1]+dy
    kicker(d,x0+44,y0+34,'THE DOSE',GOLD,t,31.2)
    p=cubic((t-31.45)/0.55) if t>=31.45 else 0
    n=int(round(400*p))
    fn=f(BEB,300); txt(d,x0+40,y0+80,str(n),fn,GOLD,ap(t,31.45,0.1))
    if GL and p>0.95: GL.text((x0+40,y0+80),'400',font=fn,fill=A(VGOLD,0.25))
    if t>=32.1:
        a=ap(t,32.15,0.14); txt(d,x0+40+d.textlength('400',font=fn)+20,y0+190,'MG',f(BEB,130),CREAM,a)
        txt(d,x0+46,y0+384,'TESTOSTERONE  ·  INJECTED',f(MONO,24),MUTED,ap(t,32.6))
    # body fat meter (vertical)
    if t>=33.8:
        a=ap(t,33.8,0.14); mx0,mx1=800,880; my0,my1=y0+110,y0+400
        txt(d,(mx0+mx1)/2,y0+80,'BODY FAT',f(MONOB,22),CREAM,a,'mm')
        d.rectangle([mx0,my0,mx1,my1],outline=A((90,90,100),a),width=2)
        lev=cubic((t-34.0)/0.9)*0.82; yf=lerp(my1-3,my0+3,lev)
        for i in range(int(my1-3-yf)):
            yy=my1-3-i; k=i/(my1-my0)
            c=tuple(int(lerp(AMBER[j],RED[j],k)) for j in range(3)); d.line([(mx0+3,yy),(mx1-3,yy)],fill=A(c,a))
        if GL and lev>0.5: GL.rectangle([mx0+3,yf,mx1-3,my1-3],fill=A(RED,0.5*a))
        txt(d,mx1+16,yf-14,'HIGH',f(MONOB,22),RED,ap(t,34.9))
    if t>=36.9:
        p2=expo((t-36.9)/0.22); yb=y0+420; xa=x0+40; xb=lerp(xa,PB[2]-40,p2)
        lit_bar(d,xa,yb,xb,yb+62,RED);
        if GL: GL.rectangle([xa-4,yb-6,xb+4,yb+68],outline=A(RED,1),width=10)
        if p2>0.6: txt(d,xa+24,yb+4,'= AN ESTROGEN FACTORY',f(BEB,58),WHITE,clamp((p2-0.6)/0.4))
    wm(d,PB[2],PB[3]+dy,1) if t<36.9 else None

def S_graph(d,t,dy):
    x0,y0=PB[0],PB[1]+dy
    txt(d,x0+40,y0+26,'DOSE  VS  RETURN',f(MONOB,26),WHITE,1)
    gx0,gy0,gx1,gy1=x0+90,y0+90,PB[2]-60,y0+410
    a=ap(t,38.4,0.2)
    d.line([(gx0,gy1),(gx1,gy1)],fill=A(CREAM,a),width=3); d.line([(gx0,gy0),(gx0,gy1)],fill=A(CREAM,a),width=3)
    for k in range(1,5):
        yy=lerp(gy1,gy0,k/4); d.line([(gx0,yy),(gx1,yy)],fill=A((60,64,76),a),width=1)
    txt(d,gx1,gy1+48,'DOSE  →',f(MONOB,22),MUTED,a,'ra')
    for k,lb in enumerate(['LOW','','MID','','HIGH']):
        if lb: txt(d,lerp(gx0,gx1,k/4),gy1+16,lb,f(MONO,20),MUTED2,a,'ma')
    def curve(fn,p,col,w=6):
        pts=[]
        for i in range(int(80*p)+1):
            u=i/80; pts.append((lerp(gx0,gx1,u),lerp(gy1,gy0,fn(u))))
        if len(pts)>1:
            d.line(pts,fill=A(col,1),width=w,joint='curve')
            if GL: GL.line(pts,fill=A(col,0.9),width=w+8)
        return pts
    pa=ease_io((t-38.5)/1.5) if t>=38.5 else 0
    pr=curve(lambda u:0.04+0.92*u**2.1,pa,RED)
    if pr and pa>0.2:
        x,y=pr[-1]; d.ellipse([x-9,y-9,x+9,y+9],fill=A(RED,1))
    if pa>=1: tag(d,gx1-330,gy0-14,'AROMATIZATION',RED,24,ap(t,40.0,0.12))
    pb=ease_io((t-40.95)/0.8) if t>=40.95 else 0
    pg=curve(lambda u:0.62*(1-math.exp(-u*4.2))/(1-math.exp(-4.2)),pb,VGOLD)
    if pb>=0.98:
        tag(d,gx0+40,gy0+60,'GAINS',VGOLD,24,ap(t,41.6,0.1))
    return
    if t>=41.5:
        a2=ap(t,41.5,0.14); bx0,by0=lerp(gx0,gx1,0.55),lerp(gy1,gy0,0.68); bx1,by1=gx1,lerp(gy1,gy0,0.5)
        brackets(d,bx0,by0,bx1,by1,A(VGOLD,a2),24,5)
        txt(d,(bx0+bx1)/2,by1+12,'DIMINISHING RETURNS',f(MONOB,22),VGOLD,a2,'ma')
    wm(d,PB[2],PB[3]+dy,1)

def title_card(im,t):   # full-screen THE FIX
    T0,T1,T2=42.7,44.15,44.42
    if t<T0 or t>=T2: return False
    if t<T1:
        p=expo((t-T0)/0.12); box=(0,lerp(H*0.5,0,p),W,lerp(H*0.5,H,p))
    else:
        q=ease_io((t-T1)/(T2-T1)); box=(lerp(0,PB[0],q),lerp(0,PB[1],q),lerp(W,PB[2],q),lerp(H,PB[3],q))
    x0,y0,x1,y1=[int(v) for v in box]
    fa=1.0 if t<T1 else 1-ease_io((t-T1)/(T2-T1))
    ov=Image.new('RGBA',(W,H),(0,0,0,0)); od=ImageDraw.Draw(ov); od.rectangle([x0,y0,x1,y1],fill=NAVY+(int(255*fa),))
    if t>=T1: od.rectangle([x0,y0,x0+5,y1],fill=GOLD+(int(255*fa),))
    im.alpha_composite(ov); d=ImageDraw.Draw(im,'RGBA')
    # subtle glow
    if t<T1:
        g=Image.new('RGBA',(W,H),(0,0,0,0)); gd=ImageDraw.Draw(g); gd.ellipse([600,-200,1400,600],fill=(60,52,40,90)); g=g.filter(ImageFilter.GaussianBlur(120))
        m=Image.new('L',(W,H),0); ImageDraw.Draw(m).rectangle([x0,y0,x1,y1],fill=255); im.paste(Image.alpha_composite(im.crop((0,0,W,H)),g),(0,0),m)
        d=ImageDraw.Draw(im,'RGBA')
        a=clamp((T1-t)/0.12) if t>T1-0.12 else 1
        lg=logo(84); im.alpha_composite(lg,(90,330)) if a>0.5 else None
        txt(d,196,342,'COACH AGZ',f(BAR7,40),GOLD,a); txt(d,196,386,'@coach.agz',f(MONO,24),MUTED2,a)
        kicker(d,90,640,"HERE'S WHAT YOU DO",GOLD,t,T0+0.05,a,34)
        p=expo((t-T0-0.18)/0.14); s=lerp(1.12,1,p)
        txt(d,86,700,'THE',f(BEB,int(250*s)),CREAM,p*a);
        txt(d,86,930,'FIX',f(BEB,int(250*s)),VGOLD,p*a)
        if GL: GL.text((86,930),'FIX',font=f(BEB,int(250*s)),fill=A(VGOLD,0.35*p*a))
        txt(d,92,1200,'Before you raise the dose',f(DMM,50),MUTED,ap(t,T0+0.4)*a)
        txt(d,90,1460,'FOR RESEARCH & EDUCATIONAL PURPOSES ONLY',f(MONO,20),MUTED2,a)
    return True

def S_list(d,t,dy):
    x0,y0=PB[0],PB[1]+dy
    txt(d,x0+44,y0+28,'THE FIX',f(BEB,58),CREAM,1); txt(d,x0+44+d.textlength('THE FIX ',font=f(BEB,58)),y0+28,'· IN ORDER',f(BEB,58),GOLD,1)
    rows=[(45.15,'01','LOSE THE BODY FAT','Cut the drive-thru first'),(47.9,'02','GET LEAN FIRST','Then go higher on dose'),(49.9,'03',"CAN'T DROP IT YET?",'Lower the dose until you can')]
    for i,(tt,n,hd,sb) in enumerate(rows):
        a=ap(t,tt,0.14)
        if a<=0: continue
        yy=y0+112+i*124; xx=x0+44+lerp(-30,0,a)
        d.line([(x0+44,yy+112),(PB[2]-44,yy+112)],fill=A((58,54,48),a),width=2)
        xe=tag(d,xx,yy+14,n,VGOLD,40,a,font=MONOB)
        txt(d,xe+24,yy+6,hd,f(BEB,60),WHITE,a)
        txt(d,xe+26,yy+66,sb,f(DMR,28),MUTED,ap(t,tt+0.25))
        # tick when next row arrives / after spoken
        done=[47.8,49.8,53.4][i]
        if t>=done: check(d,PB[2]-90,yy+30,GREEN,1.3,ap(t,done,0.1))
    if t>=52.2:
        tag(d,PB[2]-330,y0+28,'DOSE ↓ TEMPORARY',RED,22,ap(t,52.2,0.1)) if False else None
    wm(d,PB[2],PB[3]+dy,1)

def S_slider(d,t,dy):
    x0,y0=PB[0],PB[1]+dy
    kicker(d,x0+44,y0+30,'DOSE WHILE YOU CUT',CRIM2,t,53.9)
    sx0,sx1,sy=x0+80,PB[2]-70,y0+200
    for i in range(int(sx1-sx0)):
        k=i/(sx1-sx0)
        c=tuple(int(lerp(SGREEN[j],AMBER[j],k/0.6)) for j in range(3)) if k<0.6 else tuple(int(lerp(AMBER[j],RED[j],(k-0.6)/0.4)) for j in range(3))
        d.line([(sx0+i,sy),(sx0+i,sy+30)],fill=A(c,0.9))
    for k in range(5):
        x=lerp(sx0,sx1,k/4); d.line([(x,sy+34),(x,sy+50)],fill=A(CREAM,1),width=3)
        txt(d,x,sy+58,str(k*100),f(MONOB,24),CREAM,1,'ma')
    txt(d,sx1,sy+92,'MG',f(MONO,20),MUTED2,1,'ra')
    # green band 100-150
    if t>=54.1:
        a=ap(t,54.1,0.2); bx0=lerp(sx0,sx1,0.25); bx1=lerp(bx0,lerp(sx0,sx1,0.375),expo((t-54.55)/0.2) if t>=54.55 else 0.1)
        d.rectangle([bx0,sy-14,bx1,sy+44],outline=A(GREEN,a),width=5)
        if GL: GL.rectangle([bx0,sy-14,bx1,sy+44],outline=A(GREEN,a),width=12)
    # marker 400 -> 125
    mv=1.0 if t<54.6 else lerp(1.0,0.3125,cubic((t-54.6)/0.6))
    mx=lerp(sx0,sx1,mv); col=RED if mv>0.6 else GREEN
    d.polygon([(mx-20,sy-56),(mx+20,sy-56),(mx,sy-20)],fill=A(col,1))
    if GL: GL.polygon([(mx-20,sy-56),(mx+20,sy-56),(mx,sy-20)],fill=A(col,0.8))
    lbl='YOUR DOSE' if mv>0.6 else '100–150 MG'
    txt(d,mx,sy-62,lbl,f(MONOB,24),col,1,'mb')
    # habit chips
    chips=[(56.85,'NUTRITION'),(58.05,'STEPS'),(59.05,'CARDIO'),(59.85,'EAT RIGHT')]
    cx=x0+44; cy=y0+360
    txt(d,cx,cy-46,'WHILE YOU DIAL IN',f(MONO,22),MUTED2,ap(t,56.5))
    for tt,lb in chips:
        a=ap(t,tt,0.12)
        fn=f(BAR7,38); tw=d.textlength(lb,font=fn); w=tw+90
        if a>0:
            d.rounded_rectangle([cx,cy+lerp(16,0,a),cx+w,cy+70+lerp(16,0,a)],radius=12,fill=A((10,40,22),a),outline=A(GREEN,a),width=3)
            check(d,cx+18,cy+20+lerp(16,0,a),GREEN,0.9,a); txt(d,cx+64,cy+12+lerp(16,0,a),lb,fn,WHITE,a)
        cx+=w+16
    wm(d,PB[2],PB[3]+dy,1)

def S_bars(d,t,dy):
    x0,y0=PB[0],PB[1]+dy
    txt(d,x0+40,y0+26,'SAME DOSE  ·  DIFFERENT BODY',f(MONOB,26),WHITE,1)
    base=y0+405; groups=[(x0+90,'HIGH BODY FAT',RED,60.5),(x0+520,'LEAN',GREEN,61.35)]
    for gi,(gx,lb,col,tt) in enumerate(groups):
        a=ap(t,tt,0.14)
        if a<=0: continue
        txt(d,gx+170,base+20,lb,f(BEB,46),col if gi==1 else CREAM,a,'ma')
        d.line([(gx-10,base),(gx+360,base)],fill=A(CREAM,a),width=3)
        # aromatase bar
        if gi==0: arom=0.85; e2=0.9 if t>=66.85 else 0.62
        else:
            arom=0.85 if t<62.95 else lerp(0.85,0.32,cubic((t-62.95)/0.7)); e2=0.0 if t<65.6 else 0.42*cubic((t-65.6)/0.5)
        grow=cubic((t-tt)/0.4)
        for bi,(v,c,nm) in enumerate([(arom*grow,VGOLD,'AROMATASE'),(e2 if gi==0 else e2,(RED if gi==0 else GREEN),'E2')]):
            if gi==0 and bi==1: v=v*grow
            bx=gx+bi*180; bh=v*235
            if bh>2:
                lit_bar(d,bx,base-bh,bx+140,base-2,c,a)
                if GL: GL.rectangle([bx,base-bh,bx+140,base-2],outline=A(c,0.7*a),width=8)
            txt(d,bx+70,base-bh-36,nm,f(MONOB,20),CREAM,a,'ma')
        if gi==1 and t>=63.0: txt(d,gx+70,base-0.32*300-80,'↓ DROPS',f(MONOB,22),GREEN,ap(t,63.0)) if False else None
    if t>=64.15:
        a=ap(t,64.15,0.12); tag(d,x0+560,y0+80,'SAME DOSE',VGOLD,30,a)
    if t>=65.7: tag(d,x0+720,base-0.42*235-56,'IN RANGE',GREEN,22,ap(t,65.7,0.1))
    if t>=66.85: tag(d,x0+90+180+150,base-0.9*235,'SPIKE',RED,26,ap(t,66.85,0.1))
    wm(d,PB[2],PB[3]+dy,1)

def block(d,cx,cy,w,h,depth,top_col,face_col,edge,a,title,sub,title_col,sub_col):
    dx,dyy=depth*0.9,-depth*0.55
    x0,y0,x1,y1=cx-w/2,cy-h/2,cx+w/2,cy+h/2
    d.polygon([(x0,y0),(x1,y0),(x1+dx,y0+dyy),(x0+dx,y0+dyy)],fill=A(top_col,a))
    d.polygon([(x1,y0),(x1+dx,y0+dyy),(x1+dx,y1+dyy),(x1,y1)],fill=A(tuple(int(v*0.55) for v in face_col),a))
    d.rectangle([x0,y0,x1,y1],fill=A(face_col,a),outline=A(edge,a),width=3)
    if GL: GL.rectangle([x0,y0,x1,y1],outline=A(edge,0.7*a),width=8)
    txt(d,cx,cy-18,title,f(BEB,64),title_col,a,'mm'); txt(d,cx,cy+32,sub,f(MONOB,24),sub_col,a,'mm')
def S_stack(d,t,dy):
    # floating blocks, no container
    a1=ap(t,68.45,0.16)
    land=70.25
    if t>=land-0.25:
        p=expo((t-land+0.25)/0.25)
    else: p=0
    ytop=lerp(620,470,ease_io((t-land+0.12)/0.3)) if t>=land-0.12 else 620
    if a1>0:
        block(d,520,ytop,620,120,40,(70,58,30),(18,20,28),VGOLD,a1,'BLOODWORK','THE ROADMAP',CREAM,VGOLD)
    if t>=land-0.25:
        yb=lerp(300,690,p) if p<1 else 690
        if t>=land+0.03 and t<land+0.2: yb+=4*math.sin((t-land)*90)*math.exp(-(t-land)*25)
        block(d,520,yb,800,150,48,(255,214,100),(201,160,60),VGOLD,clamp(p*1.5),'BODY COMPOSITION','THE FOUNDATION',INK,(60,40,0))
    if t>=71.3: tag(d,120,818,'BUILD THIS FIRST',RED,26,ap(t,71.3,0.1))

def S_cta(d,t,dy,im):
    x0,y0=PB[0],PB[1]+dy
    lg=logo(120); im.alpha_composite(lg,(x0+40,int(y0+40)))
    txt(d,x0+180,y0+52,'COACH AGZ',f(BAR7,40),GOLD,1); txt(d,x0+180,y0+98,'@coach.agz',f(MONO,24),MUTED2,1)
    if t>=73.55:
        a=ap(t,73.55,0.14); xe=tag(d,x0+40,y0+176,'FREE',RED,30,a)
        txt(d,x0+40,y0+236,'ESTROGEN FRAMEWORK',f(BEB,84),CREAM,a); txt(d,x0+40+d.textlength('ESTROGEN FRAMEWORK ',font=f(BEB,84)),y0+254,'+ PROTOCOL',f(BEB,60),GOLD,ap(t,74.75))
    if t>=75.3:
        p=expo((t-75.3)/0.12); s=lerp(1.25,1,p)
        st=Image.new('RGBA',(900,120),(0,0,0,0)); sd=ImageDraw.Draw(st)
        lit_bar(sd,0,0,900,120,VGOLD)
        sd.text((450,60),'COMMENT  "ESTROGEN"',font=f(BEB,86),fill=INK+(255,),anchor='mm')
        st=st.resize((int(900*s),int(120*s)),Image.BICUBIC)
        if GL: GL.rectangle([540-st.width/2-6,y0+390-st.height/2-6,540+st.width/2+6,y0+410+st.height/2+6],outline=A(VGOLD,p),width=12)
        al=st.split()[3].point(lambda v:int(v*p)); st.putalpha(al)
        im.alpha_composite(st,(int(540-st.width/2),int(y0+390-st.height/2)))
    txt(d,x0+40,PB[3]+dy-32,'FOR RESEARCH & EDUCATIONAL PURPOSES ONLY',f(MONO,18),MUTED2,1)

# scene table: (t0,t1,style,fn,box,cut_out)
SC=[(6.0,11.25,'crimson',S_gauge,PB,False),
    (12.35,15.95,'glass',S_rx,PB,True),
    (15.98,20.8,None,S_kinetic,PB,True),
    (21.3,29.9,'glass',S_mech,PB,True),
    (31.15,38.2,'navy',S_stat,PB,False),
    (38.35,42.6,'glass',S_graph,PB,False),
    (44.15,53.75,'navy',S_list,PB,False),
    (53.85,60.35,'crimson',S_slider,PB,False),
    (60.45,67.6,'glass',S_bars,PB,False),
    (68.3,72.35,None,S_stack,PB,False),
    (72.5,99,'navy',S_cta,PB,False)]

# ---------- text hook + topic band ----------
HOOK=dict(lines=[('ESTROGEN',' through the roof'),('','an AI won\'t fix it')],end=None)
def text_hook(im,t,end):
    if t>=end: return
    d=ImageDraw.Draw(im,'RGBA')
    s=lerp(1.0,1.04,clamp(t/end))
    l1a,l1b='ESTROGEN',' through the roof'; l2="an AI won't fix it"
    f1=f(BAR8,int(88*s)); f2=f(BAR8,int(88*s))
    w1=d.textlength(l1a,font=f1)+d.textlength(l1b,font=f1); w2=d.textlength(l2,font=f2)
    y=300; pad=34
    bw=max(w1,w2)+pad*2; bx0=(W-bw)/2
    # dark box for contrast (bright sky)
    d.rounded_rectangle([bx0,y-20,bx0+bw,y+2*int(98*s)+28],radius=22,fill=(6,8,14,214))
    d.rectangle([bx0,y-20,bx0+8,y+2*int(98*s)+28],fill=GOLD+(255,))
    x=(W-w1)/2; d.text((x,y),l1a,font=f1,fill=VGOLD); d.text((x+d.textlength(l1a,font=f1),y),l1b,font=f1,fill=WHITE)
    if GL: GL.text((x,y),l1a,font=f1,fill=A(VGOLD,0.45))
    d.text(((W-w2)/2,y+int(98*s)),l2,font=f2,fill=WHITE)
def topic_band(im,t,t0,t1,scene_on):
    if t<t0 or t>=t1: return
    a=1.0 if t-t0>0.15 else (t-t0)/0.15
    if scene_on: a*=0.0
    if a<=0: return
    d=ImageDraw.Draw(im,'RGBA')
    fn=f(BAR8,46); parts=[('Fix ',WHITE),('BODY FAT',VGOLD),(' before more ',WHITE),('TEST',VGOLD)]
    tw=sum(d.textlength(p,font=fn) for p,_ in parts); x=(W-tw)/2; y=262
    d.rounded_rectangle([x-26,y-12,x+tw+26,y+62],radius=14,fill=(6,8,14,int(200*a)))
    for p,c in parts: d.text((x,y),p,font=fn,fill=A(c,a)); x+=d.textlength(p,font=fn)

# ---------- captions ----------
FIX={'nolvodex':'NOLVADEX','fucking':'F*CKING','dose.':'DOSES','400':'400','150':'150','100':'100'}
GOLDW={'ESTROGEN','AROMATASE','LEAN','LEAN,','FOUNDATION','ROADMAP','400','100','150','TESTOSTERONE','NUTRITION','STEPS','CARDIO','AROMATIZATION'}
REDW={'FAT','FATTY','WRONG','SPIKE','ROOF',"MCDONALD'S",'SHIT','F*CKING','NIPPLES','RETENTION'}
def wtxt(i):
    raw=WORDS[i]['w']; k=raw.lower()
    if k in FIX: return FIX[k]
    return raw.upper().strip(',.!?')
def build_groups():
    G=[];cur=[]
    for i,x in enumerate(WORDS):
        if cur:
            prev=WORDS[cur[-1]]
            if len(cur)>=3 or x['s']-prev['e']>0.28 or prev['w'][-1] in '.,?!' or any(prev['e']<b<=x['s']+0.05 for b in BOUNDS): G.append(cur); cur=[]
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
    nxt=[g for g in GROUPS if WORDS[g[0]]['s']>WORDS[lo[0]]['s']]
    if t>WORDS[lo[-1]]['e']+0.5 and (not nxt or WORDS[nxt[0][0]]['s']>t): return None
    return lo
CAP_Y=1420
def captions(im,t):
    if 42.7<=t<44.55: return
    g=group_at(t)
    if not g: return
    d=ImageDraw.Draw(im,'RGBA')
    ws=[wtxt(i) for i in g]
    size=118
    while True:
        fn=f(BEB,size); sp=d.textlength(' ',font=fn)+12; wd=[d.textlength(w,font=fn) for w in ws]; tot=sum(wd)+sp*(len(ws)-1)
        if tot<=900: break
        size-=4
    xs=[];x=(W-tot)/2
    for w_ in wd: xs.append(x); x+=w_+sp
    act=0
    for k,i in enumerate(g):
        if WORDS[i]['s']<=t: act=k
    g0=WORDS[g[0]]['s']; s=lerp(0.92,1,expo((t-g0)/0.10))
    CH=size+90
    cap=Image.new('RGBA',(W,CH),(0,0,0,0)); cd=ImageDraw.Draw(cap); shd=Image.new('RGBA',(W,CH),(0,0,0,0)); sd=ImageDraw.Draw(shd)
    prev=max(0,act-1); bt=expo((t-WORDS[g[act]]['s'])/0.07) if act>0 else 1
    bx0=lerp(xs[prev],xs[act],bt)-16; bx1=lerp(xs[prev]+wd[prev],xs[act]+wd[act],bt)+16
    for k,(w_,x_) in enumerate(zip(ws,xs)): sd.text((x_+4,46),w_,font=fn,fill=(0,0,0,220))
    cap.alpha_composite(shd.filter(ImageFilter.GaussianBlur(7)))
    aw=ws[act]; boxcol=VGOLD if aw in GOLDW else RED
    lit_bar(cd,bx0,40+size*0.02,bx1,40+size*0.98,boxcol)
    for k,(w_,x_) in enumerate(zip(ws,xs)):
        if k==act: col=INK if boxcol==VGOLD else WHITE
        elif w_ in GOLDW and WORDS[g[k]]['s']<=t: col=VGOLD
        elif w_ in REDW and WORDS[g[k]]['s']<=t: col=(255,80,70)
        else: col=CREAM
        cd.text((x_,40),w_,font=fn,fill=col,stroke_width=0 if k==act else 3,stroke_fill=(0,0,0))
    if abs(s-1)>0.002:
        cap=cap.resize((int(W*s),int(CH*s)),Image.BICUBIC); ox=int((W-cap.width)/2); oy=int(CAP_Y-40-(cap.height-CH)/2)
    else: ox,oy=0,CAP_Y-40
    im.alpha_composite(cap,(ox,oy))

# ---------- frame ----------
def zoom_for(t):
    z=1.0 if seg_idx(t)%2==0 else 1.08
    if 20.15<=t<20.85: z=max(z,lerp(z,1.16,expo((t-20.15)/0.12)))
    if 75.25<=t: z=max(z,lerp(z,1.06,ease_io((t-75.25)/0.5))) if seg_idx(t)%2==0 else z
    return z
def frame(src,n):
    t=n/FPS
    z=zoom_for(t)
    if z!=1.0:
        fx,fy=face_c(n)
        big=src.resize((int(W*z),int(H*z)),Image.BICUBIC)
        ox=int(clamp(fx*z-fx,0,big.width-W)); oy=int(clamp(fy*z-fy,0,big.height-H)); src=big.crop((ox,oy,ox+W,oy+H))
    im=src.convert('RGBA')
    # top / bottom legibility scrim (light; footage untouched in face zone)
    yy=np.arange(H); a=np.where(yy>1300,np.clip((yy-1300)/300,0,1)*120,0); a=np.maximum(a,np.where(yy<360,(1-yy/360)*90,0)).astype(np.uint8)
    im.alpha_composite(Image.merge('RGBA',[Image.new('L',(W,H),c) for c in NAVY]+[Image.fromarray(np.repeat(a[:,None],W,1))]))
    global GL
    glow=Image.new('RGBA',(W,H),(0,0,0,0)); GL=ImageDraw.Draw(glow,'RGBA')
    hook_end=BOUNDS[0]
    text_hook(im,t,hook_end)
    scene_on=False; extra=None
    for (t0,t1,style,fn,box,cut_out) in SC:
        if t0<=t<t1+(0 if cut_out else 0.16):
            scene_on=True
            if style is None:
                al=expo((t-t0)/0.2)*(1-(0 if cut_out else clamp((t-t1)/0.15))); dy=0
                # soft dark backing for kinetic / blocks
                sh=Image.new('RGBA',(W,H),(0,0,0,0)); ImageDraw.Draw(sh).rectangle([0,340,W,880],fill=(4,6,12,int(150*al)))
                im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(40)))
            else:
                al,dy=container(im,style,box,t,t0,t1,cut_out)
            if al<=0: continue
            lay=Image.new('RGBA',(W,H),(0,0,0,0)); d=ImageDraw.Draw(lay,'RGBA')
            r=fn(d,t,dy,im) if fn is S_cta else fn(d,t,dy)
            layer_blit(im,lay,al,8*(1-expo((t-t0)/0.2)))
            if isinstance(r,tuple) and r[0]=='stamp':
                st,pos,p=r[1],r[2],r[3]; st.putalpha(st.split()[3].point(lambda v:int(v*p*al))); im.alpha_composite(st,(max(0,pos[0]),max(0,pos[1])))
                if GL: GL.rectangle([pos[0],pos[1],pos[0]+st.width,pos[1]+st.height],outline=A(RED,0.6*p),width=10)
    topic_band(im,t,hook_end,TOPIC_END,scene_on)
    title_card(im,t)
    GLd=GL; GL=None
    if glow.getbbox():
        sm=glow.resize((W//4,H//4),Image.BILINEAR)
        g1=np.asarray(sm.filter(ImageFilter.GaussianBlur(3.5))).astype(np.float32)/255; g2=np.asarray(sm.filter(ImageFilter.GaussianBlur(10))).astype(np.float32)/255
        prem=np.clip(g1[...,:3]*g1[...,3:]*2.0+g2[...,:3]*g2[...,3:]*1.6,0,1)
        prem=np.asarray(Image.fromarray((prem*255).astype(np.uint8)).resize((W,H),Image.BILINEAR)).astype(np.float32)/255
        b=np.asarray(im.convert('RGB')).astype(np.float32)/255
        im=Image.fromarray(((1-(1-b)*(1-prem))*255).astype(np.uint8)).convert('RGBA')
    captions(im,t)
    d=ImageDraw.Draw(im,'RGBA'); d.rectangle([0,0,6,H],fill=GOLD)
    out=im.convert('RGB')
    # impact shake on heavy hits
    for th in IMPACTS:
        k=round((t-th)*FPS)
        if k in (0,1):
            dx=[10,-5][k]; zz=1.022; big=out.resize((int(W*zz),int(H*zz)),Image.BICUBIC); ox=(big.width-W)//2-dx; oy=(big.height-H)//2
            out=big.crop((ox,oy,ox+W,oy+H))
    return out
IMPACTS=[7.4,15.3,20.2,36.9,70.25,75.3]

def decode(n0,n1):
    # read assembled cut frames n0..n1-1
    p=subprocess.Popen(['ffmpeg','-v','error','-ss',f'{n0/FPS:.4f}','-i',HERE+'/cut_v.mp4','-frames:v',str(n1-n0),'-f','rawvideo','-pix_fmt','rgb24','-'],stdout=subprocess.PIPE)
    fs=W*H*3
    for k in range(n1-n0):
        b=p.stdout.read(fs)
        if len(b)<fs: break
        yield n0+k,Image.frombytes('RGB',(W,H),b)
    p.stdout.close(); p.wait()

if __name__=='__main__':
    mode=sys.argv[1]
    if mode=='stills':
        os.makedirs(HERE+'/qc',exist_ok=True)
        for tt in [float(x) for x in sys.argv[2:]]:
            n=round(tt*FPS)
            for k,im in decode(n,n+1): frame(im,k).save(HERE+f'/qc/s_{tt:05.2f}.jpg',quality=88)
    elif mode=='info':
        print('DUR',DUR,'BOUNDS',BOUNDS,'TOPIC_END',TOPIC_END)
    elif mode=='chunk':
        n0,n1=int(sys.argv[2]),int(sys.argv[3]); out=sys.argv[4]
        enc=subprocess.Popen(['ffmpeg','-v','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-','-c:v','libx264','-crf','12','-preset','fast','-pix_fmt','yuv420p',out],stdin=subprocess.PIPE)
        for k,im in decode(n0,n1): enc.stdin.write(frame(im,k).tobytes())
        enc.stdin.close(); enc.wait()
