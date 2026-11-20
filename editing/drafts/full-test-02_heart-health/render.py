# Heart health (ezetimibe + telmisartan) — @coach.agz full edit, 1080x1920 30fps
# Built on the saved full-test pipeline (primitives, bloom, captions, punch-ins), with a
# per-scene FOOTAGE LAYOUT so the face stays visible: full / split / side / pip / iris / avatar.
import json, subprocess, sys, math
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops
S=sys.argv[1]; F=S+'/fonts/'
W,H=1080,1920; FPS=30
TL=json.load(open(S+'/timeline.json')); DUR=TL['dur']; CUTS=TL['cuts']
WORDS=json.load(open(S+'/words_final.json'))
for w in WORDS:
    if w['w'] in ('LIVER','THING','FRIENDS','SIGNALING','INTESTINES','GOOD','FREE'): w['end']=True
GOLD=(201,169,110); CREAM=(244,241,234); NAVY=(14,17,23); PANEL=(24,26,34); PBORD=(58,54,48); MUTED=(184,184,188); MLAB=(124,124,130)
RED=(255,34,28); VGOLD=(255,194,26); CYAN=(0,229,255); GREEN=(30,255,110); DEEP=(2,3,8); INK=(6,8,14); WHITE=(255,255,255)
BLUE=(79,163,224); AMBER=(240,160,48); SGREEN=(60,203,106)
MONO='JBMono-500.ttf'; MONOB='JBMono-800.ttf'; BEB='BebasNeue.ttf'; DMB='DMSans-700.ttf'; DMR='DMSans-400.ttf'; BAR='Barlow-600.ttf'; BARB='Barlow-800.ttf'
_fc={}
def f(n,s):
    k=(n,int(s))
    if k not in _fc: _fc[k]=ImageFont.truetype(F+n,int(s))
    return _fc[k]
def clamp(x,a=0,b=1): return max(a,min(b,x))
def expo(x): x=clamp(x); return 1 if x>=1 else 1-2**(-10*x)
def ease_io(x): x=clamp(x); return 4*x**3 if x<.5 else 1-(-2*x+2)**3/2
def back(x,k=1.2): x=clamp(x); return 1+(k+1)*(x-1)**3+k*(x-1)**2   # used sparingly (heavy panels only, tiny overshoot)
def lerp(a,b,t): return a+(b-a)*t
def A(c,a): return tuple(c[:3])+(max(1,int(clamp(a)*255)),)
def mix(c1,c2,t): return tuple(int(lerp(a,b,clamp(t))) for a,b in zip(c1,c2))
def appear(t,t0,dur=0.16): return expo((t-t0)/dur)
def txt(d,x,y,s,font,col,a=1.0,anchor=None): d.text((x,y),s,font=font,fill=A(col,a),anchor=anchor)
GL=None
# ---------------- primitives (from full-test pipeline) ----------------
def brackets(d,x0,y0,x1,y1,col,L=34,w=4):
    for (cx,cy,sx,sy) in [(x0,y0,1,1),(x1,y0,-1,1),(x0,y1,1,-1),(x1,y1,-1,-1)]:
        d.line([(cx,cy),(cx+sx*L,cy)],fill=col,width=w); d.line([(cx,cy),(cx,cy+sy*L)],fill=col,width=w)
def lit_bar(d,x0,y0,x1,y1,col,a=1.0):
    h=max(1,int(y1-y0))
    if x1<=x0: return
    for i in range(h):
        k=i/h; c=tuple(int(min(255,v*(1.18-0.36*k)+(40 if k<0.12 else 0))) for v in col)
        d.line([(x0,y0+i),(x1,y0+i)],fill=c+(int(255*a),))
def tag(d,x,y,label,col=RED,size=32,a=1.0,glow=True):
    if a<=0: return x
    fn=f(MONO,size); tw=d.textlength(label,font=fn); h=size+16
    lit_bar(d,x,y,x+tw+24,y+h,col,a); d.text((x+12,y+5),label,font=fn,fill=A(WHITE if col not in (VGOLD,GREEN,CYAN) else INK,a))
    if GL and glow: GL.rectangle([x-4,y-4,x+tw+28,y+h+4],outline=A(col,a),width=8)
    return x+tw+24
def flag(d,box,t0,t,col=RED):
    p=expo((t-t0)/0.14)
    if p<=0: return
    x0,y0,x1,y1=box; brackets(d,x0,y0,x1,y1,A(col,p),26,6)
    if GL: brackets(GL,x0,y0,x1,y1,A(col,p),26,12)
def arrow(d,x0,y0,x1,y1,col,w=5,a=1.0,L=18):
    d.line([(x0,y0),(x1,y1)],fill=A(col,a),width=w)
    ang=math.atan2(y1-y0,x1-x0)
    d.polygon([(x1,y1),(x1-L*math.cos(ang-0.45),y1-L*math.sin(ang-0.45)),(x1-L*math.cos(ang+0.45),y1-L*math.sin(ang+0.45))],fill=A(col,a))
def check(d,x,y,col,s=1.0,a=1.0):
    d.line([(x,y+16*s),(x+10*s,y+28*s),(x+30*s,y+2*s)],fill=A(col,a),width=int(6*s))
    if GL: GL.line([(x,y+16*s),(x+10*s,y+28*s),(x+30*s,y+2*s)],fill=A(col,a),width=int(12*s))
def cross(d,x,y,col,s=1.0,a=1.0):
    d.line([(x,y),(x+28*s,y+28*s)],fill=A(col,a),width=int(6*s)); d.line([(x+28*s,y),(x,y+28*s)],fill=A(col,a),width=int(6*s))
    if GL: GL.line([(x,y),(x+28*s,y+28*s)],fill=A(col,a),width=12); GL.line([(x+28*s,y),(x,y+28*s)],fill=A(col,a),width=12)
def glass(im,box,dark=0.86,blur=12,radius=22):
    x0,y0,x1,y1=[int(v) for v in box]
    x0=max(0,x0); y0=max(0,y0); x1=min(W,x1); y1=min(H,y1)
    if x1-x0<4 or y1-y0<4: return
    reg=im.crop((x0,y0,x1,y1)).convert('RGB').filter(ImageFilter.GaussianBlur(blur))
    reg=Image.blend(reg,Image.new('RGB',reg.size,DEEP),dark)
    m=Image.new('L',reg.size,0); ImageDraw.Draw(m).rounded_rectangle([0,0,reg.width-1,reg.height-1],radius=radius,fill=255)
    im.paste(reg,(x0,y0),m)
def kicker(d,x,y,label,col,t,t0,size=28):
    p=expo((t-t0)/0.18);
    if p<=0: return
    d.line([(x,y+size*0.55),(x+lerp(0,46,p),y+size*0.55)],fill=A(col,1),width=4)
    q=clamp((t-t0-0.08)/0.25); n=int(len(label)*q)
    fn=f(BAR,size); x2=x+60
    for ch in label[:n]:
        d.text((x2,y),ch,font=fn,fill=A(col,1)); x2+=d.textlength(ch,font=fn)+size*0.22
def panel_card(im,d,box,a,col=VGOLD,radius=22,dark=0.88):
    glass(im,box,dark,14,radius)
    x0,y0,x1,y1=box
    d.rounded_rectangle([x0,y0,x1,y1],radius=radius,outline=A(col,0.55*a),width=2)
    brackets(d,x0,y0,x1,y1,A(col,a),30,5)
    if GL: brackets(GL,x0,y0,x1,y1,A(col,a),30,10)
def flow_dots(d,pts,t,col,n=5,speed=0.6,a=1.0,r=7):
    (x0,y0),(x1,y1)=pts
    for k in range(n):
        p=(t*speed+k/n)%1; x=lerp(x0,x1,p); y=lerp(y0,y1,p); fa=a*min(1,p*6,(1-p)*6)
        d.ellipse([x-r,y-r,x+r,y+r],fill=A(col,fa))
        if GL: GL.ellipse([x-r*2,y-r*2,x+r*2,y+r*2],fill=A(col,fa*0.8))

# ---------------- background for non-footage areas ----------------
def make_bg():
    yy,xx=np.mgrid[0:H,0:W].astype(np.float32)
    g=np.exp(-(((xx-900)/700)**2+((yy-250)/600)**2))
    base=np.zeros((H,W,3),np.float32)+np.array(NAVY,np.float32)
    base+=g[...,None]*np.array([22,18,8],np.float32)
    rng=np.random.default_rng(3); base+=rng.normal(0,2.2,(H,W,1))
    base[::4]*=0.94   # faint scanlines
    return Image.fromarray(np.clip(base,0,255).astype(np.uint8))
BG=make_bg()
CAR_BG=None
def make_carousel_bg():
    yy,xx=np.mgrid[0:H,0:W].astype(np.float32)
    g=np.exp(-(((xx-1000)/600)**2+((yy-120)/520)**2))
    base=np.zeros((H,W,3),np.float32)+np.array(NAVY,np.float32)+g[...,None]*np.array([15,12,8],np.float32)
    return Image.fromarray(np.clip(base,0,255).astype(np.uint8))
CAR_BG=make_carousel_bg()

# ---------------- footage layouts ----------------
FACE=(550,870)            # face anchor in source frame
LAYOUT={
 'full':  dict(s=1.0, fx=550,fy=870, box=(0,0,W,H,0)),
 'split': dict(s=1.0, fx=550,fy=470, box=(0,0,W,1000,0)),
 'side':  dict(s=0.70,fx=745,fy=760, box=(372,250,1048,1290,34)),
 'pip':   dict(s=0.40,fx=860,fy=420, box=(860-170,420-170,860+170,420+170,170)),
 'iris':  dict(s=0.92,fx=540,fy=690, box=(540-300,690-300,540+300,690+300,300)),
 'avatar':dict(s=0.30,fx=205,fy=455, box=(205-125,455-125,205+125,455+125,125)),
}
def lay_interp(a,b,p):
    A_,B_=LAYOUT[a],LAYOUT[b]
    return dict(s=lerp(A_['s'],B_['s'],p),fx=lerp(A_['fx'],B_['fx'],p),fy=lerp(A_['fy'],B_['fy'],p),
                box=tuple(lerp(x,y,p) for x,y in zip(A_['box'],B_['box'])),bgk=p)

# ---------------- scene content ----------------
def heart_pts(cx,cy,sc):
    P=[]
    for i in range(80):
        u=2*math.pi*i/80
        x=16*math.sin(u)**3; y=13*math.cos(u)-5*math.cos(2*u)-2*math.cos(3*u)-math.cos(4*u)
        P.append((cx+x*sc,cy-y*sc))
    return P
def sc_reversible(im,d,t,T0,T1,a):          # TOP CARD (glass) — heart X-ray, wall thickens then remodels back
    box=(60,400,1020,700); panel_card(im,d,box,a,CYAN)
    kicker(d,90,418,'LEFT VENTRICLE · WALL',CYAN,t,T0+0.05,26)
    cx,cy=230,560
    P=heart_pts(cx,cy,6.2); d.line(P+[P[0]],fill=A(CYAN,a),width=4)
    if GL: GL.line(P+[P[0]],fill=A(CYAN,a),width=9)
    dmg=clamp((t-9.00)/0.35) ; rev=expo((t-9.50)/0.9)
    th=lerp(10,34,dmg); th=lerp(th,13,rev) if t>=9.5 else th
    col=mix(CYAN,RED,dmg*(1-rev))
    # LV chamber: ellipse with wall ring
    ex,ey,rx,ry=cx+18,cy+10,38,58
    d.ellipse([ex-rx-th,ey-ry-th,ex+rx+th,ey+ry+th],fill=A(col,0.85*a)); d.ellipse([ex-rx,ey-ry,ex+rx,ey+ry],fill=A((8,12,22),a))
    if GL: GL.ellipse([ex-rx-th,ey-ry-th,ex+rx+th,ey+ry+th],outline=A(col,a),width=8)
    # meter
    x0,x1=420,980; y=600
    txt(d,x0,470,'WALL THICKNESS',f(MONO,28),CREAM,a)
    d.rectangle([x0,y,x1,y+40],outline=A((70,74,90),a),width=2)
    fr=lerp(0.35,0.92,dmg); fr=lerp(fr,0.42,rev) if t>=9.5 else fr
    lit_bar(d,x0+3,y+3,lerp(x0+3,x1-3,fr),y+37,col,a)
    for k in range(1,10): d.line([(x0+k*(x1-x0)/10,y+40),(x0+k*(x1-x0)/10,y+50)],fill=A((90,94,110),a),width=2)
    if t>=9.06 and t<9.5: tag(d,x0,520,'DAMAGE',RED,28,appear(t,9.06)*a)
    if t>=9.5: tag(d,x0,520,'REVERSIBLE',GREEN,28,appear(t,9.5)*a)
    if t>=9.5: arrow(d,lerp(x0,x1,0.92),y+62,lerp(x0,x1,fr)+8,y+62,GREEN,4,a*appear(t,9.6),14)
def sc_dossier(im,d,t,T0,T1,a):            # TOP CARD (terminal) — two redacted compounds
    box=(60,400,1020,705); panel_card(im,d,box,a,VGOLD)
    kicker(d,90,418,'HEART PROTOCOL',VGOLD,t,T0+0.05,26)
    fn=f(MONO,28)
    txt(d,760,420,'CLASSIFIED',fn,RED,a*(0.5+0.5*(int(t*3)%2)))
    for i,(tt,wid) in enumerate([(11.64,330),(11.84,290)]):
        p=appear(t,tt,0.2)*a
        if p<=0: continue
        y=480+i*84
        txt(d,90,y+6,f'0{i+1}',f(BEB,56),VGOLD,p)
        d.rectangle([160,y+12,160+wid*expo((t-tt)/0.35),y+56],fill=A((230,230,232),p))   # redaction bar
        txt(d,520,y+16,'TARGET',f(MONO,24),MLAB,p); txt(d,632,y+12,'HEART',f(BEB,44),WHITE,p)
        sy=y+30
        d.ellipse([760,sy-9,778,sy+9],fill=A(GREEN,p*(0.5+0.5*math.sin(t*7+i))))
        txt(d,790,y+16,'ACTIVE',f(MONO,24),GREEN,p)
    if t>=12.88:
        p=appear(t,12.88)*a; txt(d,90,654,'CLASS',f(MONO,24),MLAB,p); tag(d,180,646,'HEALTH COMPOUND',CYAN,24,p)
    if t>=15.44:
        p=expo((t-15.44)/0.12)*a; s=lerp(1.25,1.0,p)
        fn=f(BEB,int(58*s)); lab='DAY 1'; tw=d.textlength(lab,font=fn)
        x=900-tw/2; y=640-int(29*s)
        d.rectangle([x-16,y-4,x+tw+16,y+int(62*s)],outline=A(RED,p),width=5); txt(d,x,y,lab,fn,RED,p)
        if GL: GL.rectangle([x-20,y-8,x+tw+20,y+int(66*s)],outline=A(RED,p),width=10)
def gauge(d,cx,cy,r,val,a,label='SYSTOLIC',ticks=True):
    # 180-degree spectrum gauge; val 0..1
    segs=[(0,0.30,BLUE),(0.30,0.55,SGREEN),(0.55,0.75,AMBER),(0.75,1.0,RED)]
    for s0,s1,c in segs:
        d.arc([cx-r,cy-r,cx+r,cy+r],180+s0*180,180+s1*180,fill=A(c,a),width=22)
        if GL: GL.arc([cx-r,cy-r,cx+r,cy+r],180+s0*180,180+s1*180,fill=A(c,a*0.6),width=30)
    if ticks:
        for k in range(11):
            ang=math.pi+k/10*math.pi; r0,r1=r-34,r-(48 if k%5==0 else 40)
            d.line([(cx+r0*math.cos(ang),cy+r0*math.sin(ang)),(cx+r1*math.cos(ang),cy+r1*math.sin(ang))],fill=A((150,150,160),a),width=3)
    ang=math.pi+clamp(val)*math.pi; L=r-30
    d.line([(cx,cy),(cx+L*math.cos(ang),cy+L*math.sin(ang))],fill=A(WHITE,a),width=7)
    if GL: GL.line([(cx,cy),(cx+L*math.cos(ang),cy+L*math.sin(ang))],fill=A(WHITE,a*0.6),width=10)
    d.ellipse([cx-16,cy-16,cx+16,cy+16],fill=A(WHITE,a)); d.ellipse([cx-7,cy-7,cx+7,cy+7],fill=A(INK,a))
    fn=f(MONO,24); tw=d.textlength(label,font=fn); txt(d,cx-tw/2,cy+18,label,fn,CREAM,a)
def sc_bp(im,d,t,T0,T1,a):                 # SPLIT SCREEN — BP gauge + LV cross-section
    d.line([(0,1000),(W,1000)],fill=A(VGOLD,a),width=4)
    if GL: GL.line([(0,1000),(W,1000)],fill=A(VGOLD,a),width=10)
    tag(d,60,1022,'01',VGOLD,28,a); kicker(d,124,1028,'BLOOD PRESSURE',VGOLD,t,T0+0.15,28)
    # gauge (left)
    v=0.42
    if t>=19.18: v=lerp(0.42,0.86,expo((t-19.18)/0.7))+0.012*math.sin(t*23)*(t>19.9)
    gauge(d,290,1330,205,v,a)
    if t>=19.18: tag(d,150,1092,'ELEVATED',RED,26,appear(t,19.3)*a)
    # LV cross-section (right): load arrows on "workload", wall thickens on "hypertrophy"
    cx,cy=800,1235
    thick=lerp(16,46,expo((t-23.22)/0.9)) if t>=23.22 else 16
    col=RED if t>=23.22 else CYAN
    R=118
    d.ellipse([cx-R,cy-R,cx+R,cy+R],fill=A(mix(CYAN,RED,clamp((t-23.22)/0.5)) if t>=23.22 else CYAN,0.9*a))
    d.ellipse([cx-R+thick,cy-R+thick,cx+R-thick,cy+R-thick],fill=A((6,10,20),a))
    if GL: GL.ellipse([cx-R,cy-R,cx+R,cy+R],outline=A(col,a),width=10)
    txt(d,cx-40,cy-14,'LV',f(BEB,44),WHITE,a)
    txt(d,640,1088,'HEART · CROSS-SECTION',f(MONO,22),CREAM,a)
    if t>=20.60:
        p=appear(t,20.6,0.2)*a; pulse=6*math.sin(t*10)
        for ang in range(0,360,45):
            r0=R+60+pulse; r1=R+16
            x0=cx+r0*math.cos(math.radians(ang)); y0=cy+r0*math.sin(math.radians(ang)); x1=cx+r1*math.cos(math.radians(ang)); y1=cy+r1*math.sin(math.radians(ang))
            arrow(d,x0,y0,x1,y1,AMBER,4,p,12)
    if t>=23.22:
        flag(d,(cx-R-10,cy-R-10,cx+R+10,cy+R+10),23.22,t)
        tag(d,cx+R-30,cy+R-6,'LVH',RED,28,appear(t,23.4)*a)
    if t>=24.46:
        p=appear(t,24.46)*a
        for i,nm in enumerate(['STIFFNESS','RHYTHM']):
            txt(d,640+i*0,1395+0,'',f(MONO,1),WHITE,0)
def receptor(d,x,y,up,col,a,w=5):
    s=1 if up else -1
    d.line([(x,y),(x,y-26*s)],fill=A(col,a),width=w); d.line([(x,y-26*s),(x-16,y-48*s)],fill=A(col,a),width=w); d.line([(x,y-26*s),(x+16,y-48*s)],fill=A(col,a),width=w)
def rx_label(d,x,y,name,t,t_reveal,a,cls,col=VGOLD,w=640):
    d.rounded_rectangle([x,y,x+w,y+150],radius=16,fill=A((236,232,224),a))
    d.rectangle([x,y,x+w,y+40],fill=A((210,10,20),a)); txt(d,x+18,y+6,'Rx',f(BEB,34),WHITE,a); txt(d,x+70,y+10,cls,f(MONO,20),WHITE,a)
    fn=f(BEB,82); tw=d.textlength(name,font=fn); txt(d,x+20,y+50,name,fn,INK,a)
    p=expo((t-t_reveal)/0.30)
    if p<1: d.rectangle([x+20+tw*p,y+56,x+20+tw+8,y+132],fill=A((20,20,24),a))   # redaction wipes off
def sc_telmi(im,d,t,T0,T1,a):              # FULL SCENE + PiP — AT1 blocked, vessel relaxes, BP falls
    rx_label(d,60,290,'TELMISARTAN',t,28.72,a,'ARB · AT1 RECEPTOR BLOCKER')
    txt(d,60,455,'COMPOUND 01',f(MONO,24),VGOLD,a)
    # vessel
    relax=expo((t-33.86)/0.7) if t>=33.86 else 0
    gap=lerp(150,230,relax); cy=800
    yt,yb=cy-gap/2,cy+gap/2
    for yy,up in [(yt,False),(yb,True)]:
        h=44
        y0=yy-h if not up else yy; y1=yy if not up else yy+h
        lit_bar(d,40,y0,1040,y1,(170,40,52),a)
        d.line([(40,yy),(1040,yy)],fill=A((255,120,120),a),width=3)
    txt(d,44,yt-90,'BLOOD VESSEL',f(MONO,22),CREAM,a)
    # receptors on inner wall
    rec=[160,330,500,670,840,1000-40]
    blk=t>=29.86
    for i,x in enumerate(rec):
        for yy,up in [(yt,False),(yb,True)]:
            receptor(d,x,yy,up,CYAN,a)
            yb_=yy+(48 if not up else -48)
            if blk and t>=29.86+i*0.06:
                p=appear(t,29.86+i*0.06,0.12)*a
                d.rounded_rectangle([x-20,yb_-12 if not up else yb_-12,x+20,yb_+12],radius=6,fill=A(VGOLD,p))
                if GL: GL.rounded_rectangle([x-24,yb_-16,x+24,yb_+16],radius=6,outline=A(VGOLD,p),width=6)
    if t>=31.5: txt(d,820,yt-90,'AT1',f(BEB,44),CYAN,appear(t,31.5)*a)
    # angiotensin II particles travelling; once blocked they bounce
    for k in range(7):
        p=(t*0.35+k/7)%1; x=lerp(60,1020,p); yy=cy+math.sin(k*2.1+t*2)*(gap/2-70)
        col=RED; dd=11
        d.polygon([(x-dd,yy),(x,yy-dd),(x+dd,yy),(x,yy+dd)],fill=A(col,a));
        if GL: GL.ellipse([x-18,yy-18,x+18,yy+18],fill=A(col,a*0.7))
    ly_=cy+gap/2+84; d.polygon([(64,ly_),(74,ly_-10),(84,ly_),(74,ly_+10)],fill=A(RED,a)); txt(d,96,ly_-14,'ANGIOTENSIN II',f(MONO,24),CREAM,a)
    if t>=29.86: d.rounded_rectangle([384,ly_-9,410,ly_+9],radius=4,fill=A(VGOLD,a*appear(t,29.86))); txt(d,420,ly_-14,'TELMISARTAN',f(MONO,24),CREAM,a*appear(t,29.86))
    if t>=29.86: tag(d,690,cy+gap/2+64,'AT1 BLOCKED',RED,26,appear(t,30.0)*a)
    if t>=33.86:
        p=appear(t,33.86)*a; arrow(d,1000,cy-20,1000,yt+6,GREEN,4,p,14); arrow(d,1000,cy+20,1000,yb-6,GREEN,4,p,14); tag(d,700,cy-26,'RELAXED',GREEN,26,p)
    # BP gauge: handoff from section 01 — needle falls on "falls"
    v=0.86 if t<35.22 else lerp(0.86,0.45,expo((t-35.22)/0.5))
    gauge(d,260,1290,170,v,a*appear(t,34.4,0.25),ticks=False)
    if t>=35.22: tag(d,470,1210,'BP ↓',GREEN,30,appear(t,35.3)*a)
    txt(d,60,1700,'FOR RESEARCH & EDUCATIONAL PURPOSES ONLY',f(MONO,20),MLAB,a)
def sc_study(im,d,t,T0,T1,a):              # PAPER DOCUMENT — study chart, LV mass regression
    x0,y0,x1,y1=70,395,1010,705
    sh=Image.new('RGBA',(W,H),(0,0,0,0)); ImageDraw.Draw(sh).rectangle([x0+10,y0+14,x1+10,y1+14],fill=(0,0,0,int(150*a)))
    shb=sh.filter(ImageFilter.GaussianBlur(12)); im.paste(shb,(0,0),shb)
    d.rectangle([x0,y0,x1,y1],fill=A((226,224,218),a))
    for yy in range(y0+8,y1,6): d.line([(x0,yy),(x1,yy)],fill=A((214,212,206),a),width=1)   # paper grain
    d.rectangle([x0,y0,x1,y0+44],fill=A((16,24,48),a)); txt(d,x0+18,y0+9,'CLINICAL STUDY · HYPERTENSIVE PATIENTS',f(MONO,22),WHITE,a)
    txt(d,x0+20,y0+60,'LEFT VENTRICULAR MASS',f(BARB,32),(30,30,40),a); txt(d,x0+20,y0+96,'on telmisartan',f(DMR,24),(90,90,100),a)
    # chart
    cx0,cy0,cx1,cy1=x0+420,y0+64,x1-30,y1-30
    d.line([(cx0,cy1),(cx1,cy1)],fill=A((60,60,70),a),width=2); d.line([(cx0,cy0),(cx0,cy1)],fill=A((60,60,70),a),width=2)
    txt(d,cx0-6,cy1+2,'',f(MONO,16),(80,80,90),a)
    for k in range(1,4): d.line([(cx0,cy1-k*50),(cx1,cy1-k*50)],fill=A((196,194,188),a),width=1)
    txt(d,cx1-90,cy1+4,'TIME →',f(MONO,16),(80,80,90),a)
    vals=[0.86,0.84,0.76,0.66,0.58,0.52,0.48]
    pts=[(lerp(cx0+20,cx1-20,i/6),cy1-10-v*(cy1-cy0-20)) for i,v in enumerate(vals)]
    p=clamp((t-38.0)/1.9)*6
    for i in range(6):
        if p>i:
            q=min(1,p-i); e=(lerp(pts[i][0],pts[i+1][0],q),lerp(pts[i][1],pts[i+1][1],q))
            d.line([pts[i],e],fill=A((200,16,30),a),width=6)
    for i,pt in enumerate(pts):
        if p>=i: d.ellipse([pt[0]-7,pt[1]-7,pt[0]+7,pt[1]+7],fill=A((200,16,30),a))
    if t>=39.78:
        hp=expo((t-39.78)/0.4)   # highlighter swipe over the regression label
        d.rectangle([x0+18,y0+160,x0+18+lerp(0,330,hp),y0+214],fill=A((255,214,10),0.75*a))
        txt(d,x0+24,y0+162,'REGRESSION',f(BEB,52),(20,20,26),a*appear(t,39.8))
        arrow(d,pts[2][0],pts[2][1]-40,pts[6][0]-6,pts[6][1]-30,(30,150,70),5,a*appear(t,40.2),16)
    if t>=40.52: txt(d,x0+24,y0+226,'LV MASS ↓',f(MONOB,30),(30,120,60),a*appear(t,40.52))
    if t>=42.30:   # red-pen circle around the regression end of the curve, drawn on "huge"
        q=expo((t-42.30)/0.25); ex,ey=pts[5]; n=int(48*q)
        ring=[(ex+12+92*math.cos(-2.2+k/40*2*math.pi*1.05),ey+4+44*math.sin(-2.2+k/40*2*math.pi*1.05)) for k in range(n)]
        if len(ring)>1: d.line(ring,fill=A((215,10,20),a),width=6)
def badge(d,x,y,w,title,sub,icon,col,a):
    d.rounded_rectangle([x,y,x+w,y+108],radius=54,fill=A((6,10,20),0.92*a),outline=A(col,a),width=3)
    if GL: GL.rounded_rectangle([x,y,x+w,y+108],radius=54,outline=A(col,a),width=8)
    d.ellipse([x+12,y+12,x+96,y+96],fill=A(col,a))
    icon(d,x+54,y+54,a)
    txt(d,x+116,y+16,title,f(BARB,40),WHITE,a); txt(d,x+116,y+64,sub,f(MONO,22),col,a)
def ic_insulin(d,cx,cy,a):
    d.polygon([(cx,cy-30),(cx-20,cy+2),(cx+20,cy+2)],fill=A(INK,a)); d.ellipse([cx-20,cy-14,cx+20,cy+26],fill=A(INK,a))
def ic_receptor(d,cx,cy,a):
    receptor(d,cx,cy+28,True,INK,a,6); d.ellipse([cx-11,cy-24,cx+11,cy-2],fill=A(INK,a))
def sc_bonus(im,d,t,T0,T1,a):              # BADGE RACK — slide-in pills
    tag(d,60,400,'BONUS · TELMISARTAN',VGOLD,26,a*appear(t,T0+0.05))
    for i,(tt,title,sub,ic,col) in enumerate([(45.0,'INSULIN SENSITIVITY','IMPROVED',ic_insulin,GREEN),(48.04,'ANDROGEN RECEPTORS','UPREGULATED · SOME STUDIES',ic_receptor,CYAN)]):
        if t<tt: continue
        p=expo((t-tt)/0.28); x=lerp(1100,60,p); y=462+i*128
        badge(d,x,y,900,title,sub,ic,col,a)
        if i==0:   # sparkline: glucose response flattening
            sx=x+720; pts=[(sx+k*14,y+70-18*math.exp(-((k-4)/2.2)**2)*(1-0.6*appear(t,45.72,0.5))) for k in range(11)]
            d.line(pts,fill=A(GREEN,a),width=4)
        if i==1:
            for k in range(4):
                on=appear(t,48.5+k*0.12)
                d.ellipse([x+730+k*36,y+40,x+756+k*36,y+66],outline=A(CYAN,a),width=3,fill=A(CYAN,a*on))
def sc_lipids(im,d,t,T0,T1,a):             # SIDE-BY-SIDE — bar chart then crossing lines
    x0,y0,x1,y1=40,250,352,1290
    d.rounded_rectangle([x0,y0,x1,y1],radius=26,fill=A((10,13,22),0.96*a),outline=A(VGOLD,0.6*a),width=2)
    brackets(d,x0,y0,x1,y1,A(VGOLD,a),26,5)
    tag(d,x0+18,y0+20,'02',VGOLD,26,a); txt(d,x0+76,y0+24,'LIPIDS',f(BEB,44),WHITE,a)
    phase2=expo((t-54.56)/0.35) if t>=54.56 else 0
    # bars
    if phase2<1:
        ba=a*(1-phase2)
        bars=[('HDL',0.78,0.22,50.84,GREEN,RED),('LDL',0.42,0.80,53.42,CYAN,RED),('APOB',0.40,0.84,54.12,CYAN,RED)]
        base=1150; top=430
        for i,(nm,v0,v1,tt,c0,c1) in enumerate(bars):
            bx=x0+30+i*96; p=expo((t-tt)/0.45) if t>=tt else 0
            v=lerp(v0,v1,p); c=mix(c0,c1,p)
            d.rectangle([bx,top,bx+70,base],outline=A((50,54,70),ba),width=2)
            lit_bar(d,bx+3,base-v*(base-top),bx+67,base,c,ba)
            if GL and p>0: GL.rectangle([bx,base-v*(base-top),bx+70,base],outline=A(c,ba*p),width=8)
            fn=f(BEB,40); tw=d.textlength(nm,font=fn); txt(d,bx+35-tw/2,base+12,nm,fn,WHITE,ba)
            if p>0.3:
                txt(d,bx+18,base-v*(base-top)-44,'↓' if v1<v0 else '↑',f(DMB,36),RED,ba)
        if t>=50.84: flag(d,(x0+22,top-10,x0+108,base+6),50.84,t)
    if phase2>0:
        pa=a*phase2; cx0,cy0,cx1,cy1=x0+30,420,x1-24,1130
        d.line([(cx0,cy1),(cx1,cy1)],fill=A((90,94,110),pa),width=2); d.line([(cx0,cy0),(cx0,cy1)],fill=A((90,94,110),pa),width=2)
        txt(d,cx0,cy1+14,'WEEKS ON CYCLE →',f(MONO,18),MLAB,pa)
        for nm,col,tt,curve,ly in [('CV RISK',RED,55.86,lambda u:0.15+0.75*u**1.6,1190),('PHYSIQUE',VGOLD,56.98,lambda u:0.25+0.65*(1-(1-u)**2),1228)]:
            q=clamp((t-tt+0.4)/1.3)
            n=int(q*30)
            pts=[(lerp(cx0,cx1,k/30),cy1-curve(k/30)*(cy1-cy0)) for k in range(n+1)]
            if len(pts)>1:
                d.line(pts,fill=A(col,pa),width=7)
                if GL: GL.line(pts,fill=A(col,pa),width=12)
                d.ellipse([pts[-1][0]-9,pts[-1][1]-9,pts[-1][0]+9,pts[-1][1]+9],fill=A(WHITE,pa))
            d.rectangle([cx0,ly+4,cx0+22,ly+20],fill=A(col,pa*appear(t,tt-0.4))); txt(d,cx0+32,ly,nm,f(MONO,22),CREAM,pa*appear(t,tt-0.4))
        if t>=58.08: tag(d,x0+20,cy0-6,'HIDDEN',RED,24,appear(t,58.08)*a)
def sc_ezetimibe(im,d,t,T0,T1,a):          # IRIS — intestine schematic around the face window
    rx_label(d,60,250,'EZETIMIBE',t,59.96,a,'CHOLESTEROL ABSORPTION INHIBITOR',w=560)
    txt(d,640,262,'COMPOUND 02',f(MONO,24),VGOLD,a)
    # iris ring
    d.ellipse([540-306,690-306,540+306,690+306],outline=A(VGOLD,a),width=4)
    if GL: GL.ellipse([540-306,690-306,540+306,690+306],outline=A(VGOLD,a),width=10)
    # intestine wall (lumen above, blood below)
    ly0,ly1=1010,1080; wy0,wy1=1080,1112; by0,by1=1180,1250
    txt(d,40,ly0-40,'INTESTINE',f(MONO,22),CREAM,a); txt(d,40,by1+10,'BLOODSTREAM',f(MONO,22),CREAM,a)
    d.rectangle([40,ly0,1040,ly1],fill=A((40,34,20),0.7*a))
    lit_bar(d,40,wy0,1040,wy1,(70,90,120),a)
    lit_bar(d,40,by0,820,by1,(150,24,36),a)
    gates=[150,320,490,660]
    blocked=t>=60.94
    for i,gx in enumerate(gates):
        d.rectangle([gx-20,wy0-4,gx+20,wy1+4],fill=A((6,10,20),a),outline=A(CYAN,a),width=3)
        if blocked and t>=60.94+i*0.08:
            p=appear(t,60.94+i*0.08,0.12)
            d.rectangle([gx-16,wy0,gx+16,wy1],fill=A(VGOLD,a*p))
            if GL: GL.rectangle([gx-22,wy0-6,gx+22,wy1+6],outline=A(VGOLD,a*p),width=6)
    if t>=61.38: txt(d,gates[0]-30,wy1+12,'NPC1L1',f(MONO,20),CYAN,appear(t,61.38)*a)
    # cholesterol particles: fall through gates before block, slide along lumen after
    for k in range(10):
        ph=(t*0.5+k/10)%1; gx=gates[k%4]
        if not blocked or ph>0.999:
            y=lerp(ly0+10,by0+30,ph); x=gx
        else:
            x=lerp(60,1020,(ph+k*0.07)%1); y=ly0+20+(k%3)*18
        d.ellipse([x-8,y-8,x+8,y+8],fill=A(VGOLD,a))
    # liver clearing LDL (right)
    if t>=67.62:
        p=appear(t,67.62,0.25)*a
        lx,ly=930,1215
        d.ellipse([lx-90,ly-60,lx+100,ly+50],fill=A((90,30,30),p),outline=A(VGOLD,p),width=3); txt(d,lx-42,ly-22,'LIVER',f(BEB,40),WHITE,p)
        for k in range(4):
            ph=(t*0.7+k/4)%1; x=lerp(520,lx-90,ph); y=by0+35+math.sin(k)*14
            d.ellipse([x-9,y-9,x+9,y+9],fill=A(RED,p*min(1,(1-ph)*5)))
        txt(d,520,by1+10,'LDL CLEARED',f(MONO,22),GREEN,p)
    if t>=66.16:
        p=appear(t,66.16)*a; txt(d,40,1300-6,'',f(MONO,1),WHITE,0)
        tag(d,700,wy1+10,'ABSORBED ↓',GREEN,24,p)
    # handoff from lipid bars: LDL + APOB mini bars drop
    for i,(nm,tt) in enumerate([('LDL',70.02),('APOB',71.0)]):
        if t<tt-0.2: continue
        p=appear(t,tt-0.2)*a; v=lerp(0.84,0.38,expo((t-tt-0.25)/0.5)) if t>=tt else 0.84
        bx=40+i*0; by=440+i*130
        txt(d,bx,by,nm,f(BEB,40),WHITE,p); d.rectangle([bx,by+48,bx+190,by+82],outline=A((60,64,80),p),width=2)
        lit_bar(d,bx+2,by+50,bx+2+186*v,by+80,mix(RED,GREEN,clamp((t-tt)/0.5)),p)
    if t>=72.78: check(d,200,700,GREEN,1.4,appear(t,72.78)*a)
    txt(d,60,1700,'FOR RESEARCH & EDUCATIONAL PURPOSES ONLY',f(MONO,20),MLAB,a)
def sc_compare(im,d,t,T0,T1,a):            # BRAND CAROUSEL SLIDE — two columns, live avatar header
    # header (avatar = live face circle drawn by layout)
    d.ellipse([205-131,455-131,205+131,455+131],outline=A(GOLD,a),width=5)
    txt(d,360,370,'COACH AGZ',f(BEB,64),GOLD,a); txt(d,362,440,'@coach.agz',f(MONO,26),MUTED,a)
    txt(d,910,300,'01 / 01',f(MONO,24),MLAB,a)
    kicker(d,360,500,'IN SIMPLE TERMS',GOLD,t,T0+0.1,26)
    hp=appear(t,T0+0.3,0.3)
    fn=f(BEB,96); txt(d,60,620,'TWO TARGETS.',fn,CREAM,a*hp); tw=d.textlength('TWO TARGETS. ',font=fn); txt(d,60+tw,620,'ONE HEART.',fn,GOLD,a*hp)
    cols=[(60,'EZETIMIBE',74.94,[('Cholesterol absorption',76.68)]),(555,'TELMISARTAN',77.50,[('Blood pressure',78.88),('Angiotensin signaling',80.24)])]
    for x,nm,tt,rows in cols:
        p=appear(t,tt-0.15,0.25)*a
        if p<=0: continue
        y=760+lerp(30,0,p)
        d.rectangle([x,y,x+465,y+470],fill=A(PANEL,p),outline=A(PBORD,p),width=2)
        d.line([(x,y),(x+465*p,y)],fill=A(GOLD,p),width=4)
        txt(d,x+28,y+26,'TARGETS',f(BAR,24),GOLD,p); txt(d,x+28,y+60,nm,f(BEB,66),CREAM,p)
        for j,(row,rt) in enumerate(rows):
            if t<rt: continue
            q=appear(t,rt)*p; yy=y+170+j*120
            d.polygon([(x+32,yy+22),(x+44,yy+10),(x+56,yy+22),(x+44,yy+34)],fill=A(GOLD,q))
            fnb=f(DMB,34)
            words=row.split(' ');
            txt(d,x+70,yy,words[0],fnb,CREAM,q); txt(d,x+70,yy+44,' '.join(words[1:]),f(DMR,32),MUTED,q)
            check(d,x+400,yy+10,GREEN,1.0,q)
    txt(d,60,1265,'FOR RESEARCH & EDUCATIONAL PURPOSES ONLY',f(MONO,20),MLAB,a)
    for k in range(5): d.line([(820+k*40,1275),(850+k*40,1275)],fill=A(GOLD if k==4 else (70,70,76),a),width=4)
def sc_ecg(im,d,t,T0,T1,a):                # HEART MONITOR STRIP — calm, no panel
    y0=430; x0,x1=60,1020
    d.rectangle([x0,y0-60,x1,y0+70],fill=A((2,4,10),0.55*a))
    d.line([(x0,y0+70),(x1,y0+70)],fill=A((40,60,60),a),width=1)
    head=((t-T0)*320)%(x1-x0)
    pts=[]
    for k in range(0,int(x1-x0),3):
        ph=(k%240)/240
        v=0
        if 0.30<ph<0.34: v=-12
        elif 0.36<ph<0.39: v=70*(1-abs(ph-0.375)/0.015)
        elif 0.39<ph<0.42: v=-28
        elif 0.55<ph<0.65: v=14*math.sin((ph-0.55)/0.1*math.pi)
        pts.append((x0+k,y0-v))
    vis=[p for p in pts if p[0]-x0<=head]
    if len(vis)>1:
        d.line(vis,fill=A(GREEN,a),width=4)
        if GL: GL.line(vis,fill=A(GREEN,a),width=9)
        d.ellipse([vis[-1][0]-7,vis[-1][1]-7,vis[-1][0]+7,vis[-1][1]+7],fill=A(WHITE,a))
    rest=[p for p in pts if p[0]-x0>head+40]
    if len(rest)>1: d.line(rest,fill=A(GREEN,0.25*a),width=3)
    hp_=heart_pts(x0+24,y0-38,1.0+0.12*abs(math.sin(t*3.2))); d.polygon(hp_,fill=A(RED,a))
    txt(d,x0+44,y0-52,'HEART · PROTECTED',f(MONO,22),GREEN,a)
def sc_cta(im,d,t,T0,T1,a):                # CTA card
    box=(56,300,1024,760); panel_card(im,d,box,a,VGOLD)
    global LOGO
    if LOGO is None:
        lg=Image.open(S+'/logo.jpg').convert('RGB'); s=min(lg.size); lg=lg.crop(((lg.width-s)//2,(lg.height-s)//2,(lg.width+s)//2,(lg.height+s)//2)).resize((150,150),Image.LANCZOS)
        m=Image.new('L',(150,150),0); ImageDraw.Draw(m).ellipse([0,0,149,149],fill=255); lg.putalpha(m); LOGO=lg
    lg=LOGO.copy(); lg.putalpha(lg.split()[3].point(lambda v:int(v*a))); im.paste(lg,(84,326),lg)
    txt(d,256,334,'FREE',f(MONO,26),VGOLD,a); txt(d,256,368,'CARDIOVASCULAR',f(BEB,62),WHITE,a); txt(d,256,428,'BLOODWORK BREAKDOWN',f(BEB,62),VGOLD,a)
    for i,(nm,tt) in enumerate([('DOSAGES',100.84),('TIMING',101.52),('BEST COMPOUNDS',102.62)]):
        if t>=tt:
            q=appear(t,tt)*a; x=90+[0,250,470][i]; y=520
            check(d,x,y,GREEN,0.9,q); txt(d,x+42,y-4,nm,f(MONO,28),WHITE,q)
    if t>=104.84:
        b=expo((t-104.84)/0.12); s=lerp(1.12,1.0,b)
        fn=f(BEB,int(92*s)); label='COMMENT  "HEALTH"'; tw=d.textlength(label,font=fn)
        x=540-(tw+48)/2; y=590
        lit_bar(d,x,y,x+tw+48,y+int(110*s),VGOLD,b*a); d.text((x+24,y+8),label,font=fn,fill=A(INK,b*a))
        if GL: GL.rectangle([x-4,y-4,x+tw+52,y+int(110*s)+4],outline=A(VGOLD,b*a),width=12)
    txt(d,84,730,'FOR RESEARCH & EDUCATIONAL PURPOSES ONLY',f(MONO,18),MLAB,a)
LOGO=None
# scenes: t_in, t_out, draw, layout, band_ok, caption_y
SCENES=[
 (7.80,10.80,sc_reversible,'full'),
 (11.40,16.35,sc_dossier,'full'),
 (16.40,25.05,sc_bp,'split'),
 (28.20,35.75,sc_telmi,'pip'),
 (35.95,42.75,sc_study,'full'),
 (43.00,49.38,sc_bonus,'full'),
 (49.70,58.45,sc_lipids,'side'),
 (59.30,72.98,sc_ezetimibe,'iris'),
 (73.30,80.80,sc_compare,'avatar'),
 (86.10,95.55,sc_ecg,'full'),
 (95.85,DUR+1,sc_cta,'full'),
]
BG_FOR={'split':'bg','side':'bg','pip':'bg','iris':'bg','avatar':'car','full':None}
def active(t):
    for sc in SCENES:
        if sc[0]<=t<sc[1]+0.3: return sc
    return None

# ---------------- text hook (engine) + topic band ----------------
HOOK_END=6.0; BAND_END=54.633
def text_hook(im,t):
    if t>=HOOK_END+0.15: return
    a=1-clamp((t-HOOK_END)/0.15)
    d=ImageDraw.Draw(im,'RGBA'); fn=f(DMB,66)
    lines=[[('2 ',WHITE),('HEART',VGOLD),(' compounds',WHITE)],[('Your cardiologist skips',WHITE)]]
    s=lerp(1.0,1.04,clamp(t/HOOK_END))   # slow 100->104% on the text over its hold
    fn=f(DMB,int(66*s)); y=300
    for ln in lines:
        tw=sum(d.textlength(p,font=fn) for p,_ in ln); x=(W-tw)/2
        d.rounded_rectangle([x-28,y-10,x+tw+28,y+int(84*s)],radius=18,fill=(0,0,0,int(225*a)))
        for p,c in ln: d.text((x,y),p,font=fn,fill=A(c,a)); x+=d.textlength(p,font=fn)
        y+=int(98*s)
def band(im,t,hide):
    if t<HOOK_END or t>=BAND_END+0.15 or hide>=1: return
    a=min(appear(t,HOOK_END,0.15),1-clamp((t-BAND_END)/0.15))*(1-hide)
    if a<=0: return
    d=ImageDraw.Draw(im,'RGBA')
    d.rectangle([8,212,W,300],fill=NAVY+(int(220*a),)); d.line([(64,232),(100,232)],fill=A(GOLD,a),width=4); txt(d,112,218,'@coach.agz',f(MONO,24),GOLD,a)
    fn=f(DMB,40); x=64; y=246
    for p,c in [('Protect your ',CREAM),('HEART',VGOLD),(' on gear',CREAM)]: txt(d,x,y,p,fn,c,a); x+=d.textlength(p,font=fn)

# ---------------- captions (every word; red lit block on active word) ----------------
def build_groups():
    G=[];cur=[]
    for i,x in enumerate(WORDS):
        if cur:
            prev=WORDS[cur[-1]]
            if len(cur)>=3 or x['s']-prev['e']>0.28 or prev.get('end') or any(prev['e']<=c<=x['s']+0.01 for c in CUTS if abs(c-x['s'])<0.2): G.append(cur); cur=[]
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
def captions(im,t,cap_y,size0=124,maxw=920):
    g=group_at(t)
    if not g: return
    d=ImageDraw.Draw(im,'RGBA')
    ws=[WORDS[i]['w'] for i in g]
    size=size0
    while True:
        fn=f(BEB,size); sp=d.textlength(' ',font=fn)+14; wd=[d.textlength(w,font=fn) for w in ws]; tot=sum(wd)+sp*(len(ws)-1)
        if tot<=maxw: break
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
        cap=cap.resize((int(W*s),int(CH*s)),Image.BICUBIC); ox=int((W-cap.width)/2); oy=int(cap_y-40-(cap.height-CH)/2)
    else: ox,oy=0,cap_y-40
    im.paste(cap,(ox,oy),cap)

# ---------------- frame ----------------
def seg_of(t): return sum(1 for c in CUTS if c<=t+1e-6)
def place_footage(src,s,fx,fy):
    # scale source about the face anchor, then move anchor to (fx,fy)
    if abs(s-1)<1e-3:
        ox=FACE[0]-fx; oy=FACE[1]-fy
        out=Image.new('RGB',(W,H),(0,0,0)); out.paste(src,(int(-ox),int(-oy))); return out
    sw,sh=int(W*s),int(H*s); sm=src.resize((sw,sh),Image.BICUBIC)
    out=Image.new('RGB',(W,H),(0,0,0)); out.paste(sm,(int(fx-FACE[0]*s),int(fy-FACE[1]*s))); return out
def frame(src,t):
    # punch-in: alternate per jump cut; first punch lands on "gear" (0.48s); 114% hold on "protecting your heart"
    z=1.0 if seg_of(t)%2==0 else 1.08
    if t<CUTS[0]: z=1.0 if t<0.48 else lerp(1.0,1.06,expo((t-0.48)/0.12))
    if 86.22<=t<89.9: z=lerp(z,1.14,expo((t-86.22)/0.12))
    sc=active(t)
    lay='full'; p=0
    if sc and sc[3]!='full':
        pin=ease_io((t-sc[0])/0.38); pout=ease_io((t-sc[1])/0.30); p=pin*(1-pout); lay=sc[3]
    L=lay_interp('full',lay,p) if lay!='full' else dict(LAYOUT['full'],bgk=0)
    s=L['s']*lerp(z,1.0,p)
    foot=place_footage(src,s,L['fx'],L['fy']+ (0 if p>0 else 0))
    if p>0:
        base=(CAR_BG if BG_FOR[lay]=='car' else BG).copy()
        # blend: background shows behind; dim footage-derived blur fades in
        x0,y0,x1,y1,r=L['box']
        m=Image.new('L',(W,H),0); ImageDraw.Draw(m).rounded_rectangle([x0,y0,x1,y1],radius=max(0,r),fill=255)
        fb=foot.filter(ImageFilter.GaussianBlur(24)); base=Image.blend(fb,base,clamp(p*1.6))
        base.paste(foot,(0,0),m)
        im=base
        dd=ImageDraw.Draw(im,'RGBA')
        dd.rounded_rectangle([x0,y0,x1,y1],radius=max(0,r),outline=A(VGOLD,p*0.9),width=4)
    else:
        im=foot
    # top/bottom readability scrims on full footage
    yy=np.arange(H); sa=np.where(yy>1180,np.clip((yy-1180)/260,0,1)*110,0); sa=np.maximum(sa,np.where(yy<480,(1-yy/480)*130,0)); sa=(sa*(1-p)).astype(np.uint8)
    im.paste(Image.new('RGB',(W,H),NAVY),(0,0),Image.fromarray(np.repeat(sa[:,None],W,1)))
    global GL
    glow=Image.new('RGBA',(W,H),(0,0,0,0)); GL=ImageDraw.Draw(glow,'RGBA')
    text_hook(im,t)
    hide=p if (sc and sc[3] in ('pip','iris','avatar')) else 0
    band(im,t,hide)
    cap_y=1335; cap_size=124
    if sc:
        a=min(appear(t,sc[0],0.22),1-clamp((t-sc[1])/0.22))
        if a>0:
            layer=im.copy(); d=ImageDraw.Draw(layer,'RGBA')
            sc[2](layer,d,t,sc[0],sc[1],1.0)
            if a<1:
                im=Image.blend(im,layer,a)
            else: im=layer
        if sc[3]=='split': cap_y=int(lerp(1335,1400,p)); cap_size=int(lerp(124,104,p))
    captions(im,t,cap_y,cap_size)
    GL=None
    if glow.getbbox():
        sm=glow.resize((W//4,H//4),Image.BILINEAR)
        g1=np.asarray(sm.filter(ImageFilter.GaussianBlur(3.5))).astype(np.float32)/255; g2=np.asarray(sm.filter(ImageFilter.GaussianBlur(10))).astype(np.float32)/255
        prem=np.clip(g1[...,:3]*g1[...,3:]*2.3+g2[...,:3]*g2[...,3:]*1.8,0,1)
        prem=np.asarray(Image.fromarray((prem*255).astype(np.uint8)).resize((W,H),Image.BILINEAR)).astype(np.float32)/255
        b=np.asarray(im.convert('RGB')).astype(np.float32)/255
        im=Image.fromarray(((1-(1-b)*(1-prem))*255).astype(np.uint8))
    d=ImageDraw.Draw(im,'RGBA'); d.rectangle([0,0,7,H],fill=GOLD)
    out=im.convert('RGB')
    # impact shake on "huge" (study stamp) and the CTA pill
    for t1 in (42.30,104.84):
        k=round((t-t1)*FPS)
        if k in (0,1):
            dx=[9,-5][k]; zz=1.025; big=out.resize((int(W*zz),int(H*zz)),Image.BICUBIC); ox=(big.width-W)//2-dx; oy=(big.height-H)//2
            out=big.crop((ox,oy,ox+W,oy+H)); ImageDraw.Draw(out).rectangle([0,0,7,H],fill=GOLD)
    return out
if __name__=='__main__':
    mode=sys.argv[2]
    if mode=='stills':
        for tt in [float(x) for x in sys.argv[3:]]:
            subprocess.run(['ffmpeg','-v','error','-y','-ss',str(tt),'-i',S+'/cut_v.mp4','-frames:v','1',S+'/qc/_src.png'])
            frame(Image.open(S+'/qc/_src.png').convert('RGB'),tt).save(S+f'/qc/st_{tt:06.2f}.jpg',quality=88)
        sys.exit()
    n0,n1=int(sys.argv[3]),int(sys.argv[4]); out=sys.argv[5]
    dec=subprocess.Popen(['ffmpeg','-v','error','-ss',f'{n0/FPS:.4f}','-i',S+'/cut_v.mp4','-frames:v',str(n1-n0),'-f','rawvideo','-pix_fmt','rgb24','-'],stdout=subprocess.PIPE)
    enc=subprocess.Popen(['ffmpeg','-v','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-','-c:v','libx264','-crf','12','-preset','fast','-pix_fmt','yuv420p',out],stdin=subprocess.PIPE)
    for n in range(n0,n1):
        buf=dec.stdout.read(W*H*3)
        if len(buf)<W*H*3: print('short',n); break
        enc.stdin.write(frame(Image.frombuffer('RGB',(W,H),buf),n/FPS).tobytes())
    enc.stdin.close(); enc.wait(); dec.kill(); print('done',n0,n1)
