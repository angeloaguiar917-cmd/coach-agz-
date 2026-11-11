# Reel 03 "Fat e2" - 1080x1920 30fps render. Usage:
#   python3 render.py <scratch> stills t1 t2 ...      (QC stills, cut-timeline seconds)
#   python3 render.py <scratch> chunk n0 n1 out.mp4   (frames n0..n1-1 of the cut)
import json, subprocess, sys, math
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
S=sys.argv[1]; F=S+'/fonts/'; HERE=__file__.rsplit('/',1)[0]+'/'
SRC=S+'/src/fat_e2.mov'; LOGO_P=HERE+'../../brand/logo/coach-agz-logo-round.jpg'
W,H=1080,1920; FPS=30
TR=json.load(open(HERE+'trim.json')); KEEP=TR['keep']
DUR=sum(b-a for a,b in KEEP); N=int(round(DUR*FPS))
CUTS=[]; acc=0
for a,b in KEEP[:-1]: acc+=b-a; CUTS.append(round(acc,4))
WORDS=json.load(open(HERE+'words_final.json'))
GOLD=(201,169,110); CREAM=(244,241,234); NAVY=(14,17,23); MUTED=(160,160,168)
RED=(255,34,28); VGOLD=(255,194,26); CYAN=(0,229,255); GREEN=(30,255,110); DEEP=(2,3,8); WHITE=(255,255,255)
AMBER=(255,140,20); COARED=(210,10,20); PAPER=(236,234,228); INK=(22,22,26)
MONO='JBMono-500.ttf'; MONOB='JBMono-700.ttf'; BEB='BebasNeue-Regular.ttf'; BAR='BarlowCondensed-ExtraBold.ttf'; BARS='BarlowCondensed-SemiBold.ttf'
_fc={}
def f(n,s):
    k=(n,int(s))
    if k not in _fc: _fc[k]=ImageFont.truetype(F+n,int(s))
    return _fc[k]
def clamp(x,a=0,b=1): return max(a,min(b,x))
def expo(x): x=clamp(x); return 1 if x>=1 else 1-2**(-10*x)
def ease_io(x): x=clamp(x); return 4*x**3 if x<.5 else 1-(-2*x+2)**3/2
def lerp(a,b,t): return a+(b-a)*t
def A(c,a=1.0): return tuple(c[:3])+(int(clamp(a)*255),)
def ap(t,t0,dur=0.16): return expo((t-t0)/dur)
GL=None
# ---------------- primitives ----------------
def brackets(d,x0,y0,x1,y1,col,L=34,w=4):
    for (cx,cy,sx,sy) in [(x0,y0,1,1),(x1,y0,-1,1),(x0,y1,1,-1),(x1,y1,-1,-1)]:
        d.line([(cx,cy),(cx+sx*L,cy)],fill=col,width=w); d.line([(cx,cy),(cx,cy+sy*L)],fill=col,width=w)
def lit_bar(d,x0,y0,x1,y1,col,a=1.0):
    h=max(1,int(y1-y0))
    for i in range(h):
        k=i/h; c=tuple(int(min(255,v*(1.18-0.36*k)+(40 if k<0.12 else 0))) for v in col)
        d.line([(x0,y0+i),(x1,y0+i)],fill=c+(int(255*a),))
def tag(d,x,y,label,col=RED,size=30,a=1.0,glow=True):
    if a<=0: return x
    fn=f(MONOB,size); tw=d.textlength(label,font=fn); h=size+16
    lit_bar(d,x,y,x+tw+24,y+h,col,a); d.text((x+12,y+6),label,font=fn,fill=A(WHITE if col not in (VGOLD,GREEN,CYAN) else (8,8,12),a))
    if GL and glow: GL.rectangle([x-4,y-4,x+tw+28,y+h+4],outline=A(col,a),width=8)
    return x+tw+24
def tag_w(d,label,size=30): return d.textlength(label,font=f(MONOB,size))+24
def flag(d,box,label,t0,t,side='right',col=RED):
    p=expo((t-t0)/0.14)
    if p<=0: return
    x0,y0,x1,y1=box; brackets(d,x0,y0,x1,y1,A(col),26,7)
    if GL: brackets(GL,x0,y0,x1,y1,A(col),26,12)
    q=clamp((p-0.3)/0.7)
    if q>0:
        for seg in [((x0,y0),(lerp(x0,x1,q),y0)),((x1,y1),(lerp(x1,x0,q),y1)),((x0,y1),(x0,lerp(y1,y0,q))),((x1,y0),(x1,lerp(y0,y1,q)))]:
            d.line(seg,fill=A(col),width=3)
    if p>0.5 and label:
        if side=='right': tag(d,x1+12,(y0+y1)/2-23,label,col)
        elif side=='left': tag(d,x0-12-tag_w(d,label),(y0+y1)/2-23,label,col)
        elif side=='above': tag(d,x0,y0-58,label,col)
        else: tag(d,x0,y1+10,label,col)
def arrow(d,x0,y0,x1,y1,col,w=5,a=1.0,L=18):
    d.line([(x0,y0),(x1,y1)],fill=A(col,a),width=w)
    ang=math.atan2(y1-y0,x1-x0)
    d.polygon([(x1,y1),(x1-L*math.cos(ang-0.45),y1-L*math.sin(ang-0.45)),(x1-L*math.cos(ang+0.45),y1-L*math.sin(ang+0.45))],fill=A(col,a))
def check(d,x,y,col,s=1.0,a=1.0):
    pts=[(x,y+16*s),(x+10*s,y+28*s),(x+30*s,y+2*s)]
    d.line(pts,fill=A(col,a),width=int(6*s))
    if GL: GL.line(pts,fill=A(col,a),width=int(12*s))
def cross(d,x,y,col,s=1.0,a=1.0):
    d.line([(x,y),(x+28*s,y+28*s)],fill=A(col,a),width=int(6*s)); d.line([(x+28*s,y),(x,y+28*s)],fill=A(col,a),width=int(6*s))
    if GL: GL.line([(x,y),(x+28*s,y+28*s)],fill=A(col,a),width=12); GL.line([(x+28*s,y),(x,y+28*s)],fill=A(col,a),width=12)
def txt(d,x,y,s,font,col,a=1.0,anchor=None):
    if a>0: d.text((x,y),s,font=font,fill=A(col,a),anchor=anchor)
def path_len(pts): return sum(math.dist(pts[i],pts[i+1]) for i in range(len(pts)-1))
def partial(pts,p):
    if p>=1: return pts
    L=path_len(pts)*clamp(p); out=[pts[0]]
    for i in range(len(pts)-1):
        s=math.dist(pts[i],pts[i+1])
        if L<=s:
            k=L/s if s else 0; out.append((lerp(pts[i][0],pts[i+1][0],k),lerp(pts[i][1],pts[i+1][1],k))); return out
        L-=s; out.append(pts[i+1])
    return out
def polyline(d,pts,col,w=5,a=1.0,glow=True):
    if len(pts)<2: return
    d.line(pts,fill=A(col,a),width=w,joint='curve')
    if GL and glow: GL.line(pts,fill=A(col,a),width=w*2+4,joint='curve')
def dashed(d,pts,col,w=3,a=1.0,on=14,off=10):
    for i in range(len(pts)-1):
        (x0,y0),(x1,y1)=pts[i],pts[i+1]; L=math.dist((x0,y0),(x1,y1)); k=0
        while k<L:
            e=min(L,k+on); d.line([(lerp(x0,x1,k/L),lerp(y0,y1,k/L)),(lerp(x0,x1,e/L),lerp(y0,y1,e/L))],fill=A(col,a),width=w); k+=on+off
def hexagon(d,cx,cy,r,col,a=1.0,label=None,fill=(10,14,24),w=4):
    pts=[(cx+r*math.cos(math.pi/3*i+math.pi/6),cy+r*math.sin(math.pi/3*i+math.pi/6)) for i in range(6)]
    d.polygon(pts,fill=A(fill,0.95*a)); d.line(pts+[pts[0]],fill=A(col,a),width=w)
    if GL: GL.line(pts+[pts[0]],fill=A(col,a*0.9),width=w*2+2)
    if label: txt(d,cx,cy,label,f(BEB,int(r*0.62)),WHITE,a,'mm')
def countup(v,t,t0,dur=0.45): return int(round(v*expo((t-t0)/dur)))
def kicker(d,x,y,label,t,t0,col=VGOLD,size=28):
    p=ap(t,t0,0.18)
    if p<=0: return
    d.line([(x,y+size*0.55),(x+lerp(0,44,p),y+size*0.55)],fill=A(col,p),width=4)
    q=clamp((t-t0-0.1)/0.25); n=int(len(label)*q)
    txt(d,x+60,y,label[:n],f(MONOB,size),col,1)

# ---------------- S1 line chart: the 3-week pattern ----------------
def feel(wk):
    if wk<1: return lerp(0.30,0.86,ease_io(wk))
    if wk<3: return 0.86+0.04*math.sin(wk*2.1)
    if wk<4: return lerp(0.88,0.24,ease_io(wk-3))
    return 0.24+0.03*math.sin(wk*2.7)
def water(wk): return 0.12 if wk<3 else lerp(0.12,0.92,1-math.exp(-(wk-3)*0.9))
CX0,CX1,CYB,CYT=170,950,1110,700
def cxy(wk,v,wmax=8): return (CX0+(CX1-CX0)*wk/wmax, CYB-(CYB-CYT)*v)
def scene_pattern(d,t):
    kicker(d,110,520,'HOW YOU FEEL · WEEK BY WEEK',t,7.96)
    a=ap(t,8.0,0.3)
    d.line([(CX0,CYB),(CX1,CYB)],fill=A((90,94,110),a),width=3); d.line([(CX0,CYT-30),(CX0,CYB)],fill=A((90,94,110),a),width=3)
    for wk in range(9):
        x,_=cxy(wk,0); d.line([(x,CYB),(x,CYB+10)],fill=A((90,94,110),a),width=2)
        txt(d,x,CYB+32,f'WK{wk}',f(MONOB,26),MUTED,a,'mm')
    for k in (0.25,0.5,0.75,1.0): d.line([(CX0,CYB-(CYB-CYT)*k),(CX1,CYB-(CYB-CYT)*k)],fill=A((40,44,56),a),width=1)
    # legend
    d.line([(600,612),(640,612)],fill=A(CREAM,a),width=5); txt(d,652,598,'FEEL',f(MONOB,24),CREAM,a)
    if t>=17.6: aa=ap(t,17.6); d.line([(760,612),(800,612)],fill=A(CYAN,aa),width=5); txt(d,812,598,'WATER',f(MONOB,24),CYAN,aa)
    # draw progress in weeks
    keys=[(8.76,0),(11.78,1.4),(13.54,3.0),(14.42,3.0),(15.6,4.1),(16.3,5.0),(19.15,8)]
    if t<keys[0][0]: return
    wd=8
    for (t0,w0),(t1,w1) in zip(keys,keys[1:]):
        if t<t1: wd=lerp(w0,w1,ease_io((t-t0)/(t1-t0)) if t1>t0 else 1); break
    # plateau band
    if t>=12.7:
        aa=ap(t,12.7,0.25); x0,_=cxy(1.6,0); x1,_=cxy(3,0)
        d.rectangle([x0,CYT-40,x1,CYB],fill=A(VGOLD,0.10*aa)); brackets(d,x0,CYT-40,x1,CYT+30,A(VGOLD,aa),22,5)
        txt(d,(x0+x1)/2,CYT-62,'PEAK · WK 2–3',f(MONOB,24),VGOLD,aa,'mm')
    good=[cxy(w/10,feel(w/10)) for w in range(0,int(min(wd,3)*10)+1)]
    polyline(d,good,CREAM,6)
    if wd>3:
        bad=[cxy(w/10,feel(w/10)) for w in range(30,int(wd*10)+1)]
        polyline(d,bad,RED,7)
        x,y=bad[-1]; d.ellipse([x-10,y-10,x+10,y+10],fill=A(RED))
    else:
        x,y=good[-1]; d.ellipse([x-9,y-9,x+9,y+9],fill=A(CREAM))
    if t>=17.6:
        p=clamp((t-17.6)/1.6); ww=lerp(3,8,ease_io(p))
        pts=[cxy(w/10,water(w/10)) for w in range(30,int(ww*10)+1)]
        polyline(d,pts,CYAN,6)
        if len(pts)>1: x,y=pts[-1]; d.ellipse([x-10,y-10,x+10,y+10],fill=A(CYAN))
    if t>=14.30:  # the break point
        x,y=cxy(3.05,feel(3.05)); flag(d,(x-26,y-26,x+26,y+26),None,14.30,t)
    if t>=15.38: x,y=cxy(4.1,feel(4.1)); tag(d,x-40,y+40,'BLOAT',RED,28,ap(t,15.38))
    if t>=16.00: x,y=cxy(5.4,feel(5.4)); tag(d,x-20,y+40,'MOOD ↓',RED,28,ap(t,16.0))
    if t>=19.12: x,y=cxy(8,water(8)); tag(d,x-tag_w(d,'WATER ↑↑',28)-10,y-70,'WATER ↑↑',CYAN,28,ap(t,19.12))

# ---------------- S2 clinic note (paper card) ----------------
def clinic_card(t):
    w,h=640,330; im=Image.new('RGBA',(w+40,h+40),(0,0,0,0)); d=ImageDraw.Draw(im,'RGBA')
    d.rectangle([20,20,20+w,20+h],fill=A(PAPER)); d.rectangle([20,20,20+w,74],fill=A(COARED))
    txt(d,40,32,'PATIENT FOLLOW-UP',f(MONOB,26),WHITE); txt(d,20+w-20,32,'WK 3',f(MONOB,26),WHITE,1,'ra')
    rows=[('Complaint','bloating · low mood · water',20.9),('Assessment','expected adjustment',21.6),('Plan','continue · reassure',22.3)]
    y=96
    for lab,val,t0 in rows:
        a=ap(t,t0,0.12)
        txt(d,40,y,lab.upper(),f(MONO,20),(110,110,116),a); txt(d,40,y+26,val,f(BARS,40),INK,a); y+=78
    d.line([(40,y+6),(20+w-20,y+6)],fill=A((180,178,170)),width=2)
    txt(d,40,y+14,'Signed · clinic provider',f(MONO,20),(120,120,126))
    return im
def card_clinic(im,t):
    t0,t1=19.82,25.45
    if not (t0<=t<t1+0.25): return
    pin=expo((t-t0)/0.22); pout=ease_io((t-t1)/0.22)
    c=clinic_card(t)
    hl=None
    if t>=23.58:  # bracket on the assessment line
        d=ImageDraw.Draw(c,'RGBA'); p=ap(t,23.58,0.15)
        brackets(d,30,186,520,256,A(VGOLD,p),20,6)
    c=c.rotate(-2.2,resample=Image.BICUBIC,expand=True)
    if pin<1: c=c.filter(ImageFilter.GaussianBlur(6*(1-pin)))
    x=70; y=int(lerp(1060,960,pin)+lerp(0,500,pout))
    sh=Image.new('RGBA',c.size,(0,0,0,0)); sh.putalpha(c.split()[3].point(lambda v:int(v*0.55)))
    sh=sh.filter(ImageFilter.GaussianBlur(14)); al=pin
    for L in (sh,c):
        if al<1: L.putalpha(L.split()[3].point(lambda v:int(v*al)))
    im.alpha_composite(sh,(x+10,y+18)); im.alpha_composite(c,(x,y))
    if t>=24.92:  # verdict stamp
        d=ImageDraw.Draw(im,'RGBA'); p=expo((t-24.92)/0.10); s=lerp(1.25,1.0,p)
        lab='DISMISSED'; fn=f(BEB,int(96*s)); tw=d.textlength(lab,font=fn); cx,cy=x+380,y+150
        a=p*(1-pout)
        lit_bar(d,cx-tw/2-26,cy-56*s,cx+tw/2+26,cy+56*s,RED,a); txt(d,cx,cy+4,lab,fn,WHITE,a,'mm')
        if GL: GL.rectangle([cx-tw/2-30,cy-60*s,cx+tw/2+30,cy+60*s],outline=A(RED,a),width=12)
        tag(d,cx-tw/2-26,cy+66*s,'SOURCE NOT CHECKED',RED,26,a*ap(t,25.1))

# ---------------- S3 x-ray scan: adipose as an endocrine organ ----------------
def torso_pts(cx=540,top=680,s=0.95):
    L=[(-38,0),(-40,40),(-150,72),(-196,120),(-214,240),(-222,420),(-200,420),(-176,250),(-160,170),(-150,300),(-140,420),(-150,520),(-120,560)]
    R=[(-x,y) for x,y in reversed(L)]
    return [(cx+x*s,top+y*s) for x,y in L+R]
def belly_pts(cx=540,top=680,k=1.0):
    L=[(-148,250),(-178+(-36*k),330),(-190+(-52*k),420),(-172+(-40*k),500),(-128,560)]
    R=[(-x,y) for x,y in reversed(L)]
    return [(cx+x,top+y) for x,y in L+R]
def scene_scan(d,t,lay):
    T0=25.54
    kicker(d,110,520,'SCAN · ADIPOSE TISSUE',t,T0+0.05,CYAN)
    # grid
    a=ap(t,T0,0.3)
    for gx in range(110,980,60): d.line([(gx,600),(gx,1230)],fill=A((0,60,80),0.35*a),width=1)
    for gy in range(600,1240,60): d.line([(110,gy),(970,gy)],fill=A((0,60,80),0.35*a),width=1)
    sweep=clamp((t-T0)/0.9)
    head=(540,600)
    tp=torso_pts();
    vis=[(x,y) for x,y in tp]
    clip_y=lerp(560,1240,sweep)
    # body outline (revealed by the scan sweep)
    lay2=Image.new('RGBA',(W,H),(0,0,0,0)); d2=ImageDraw.Draw(lay2,'RGBA')
    d2.ellipse([500,590,580,676],outline=A(CYAN),width=4)
    d2.line(vis+[vis[0]],fill=A(CYAN),width=4,joint='curve')
    # fat layer
    if t>=28.92:
        k=ap(t,28.92,0.6); bp=belly_pts(k=k)
        pul=0.5+0.5*math.sin(t*5) if t>=35.0 else 0
        d2.polygon(bp,fill=A(AMBER,0.22+0.18*pul))
        d2.line(bp+[bp[0]],fill=A(AMBER),width=4)
        for yy in range(910,1200,18): d2.line([(lerp(400,330,0.5),yy),(lerp(680,750,0.5),yy)],fill=A(AMBER,0.10),width=2)
    if sweep<1:
        m=Image.new('L',(W,H),0); ImageDraw.Draw(m).rectangle([0,0,W,clip_y],fill=255); lay2.putalpha(Image.fromarray(np.minimum(np.asarray(lay2.split()[3]),np.asarray(m))))
    lay.alpha_composite(lay2)
    if GL: GL.line(vis+[vis[0]],fill=A(CYAN,0.9*(1 if sweep>=1 else 0.6)),width=10)
    if sweep<1:
        d.line([(110,clip_y),(970,clip_y)],fill=A(CYAN),width=4)
        if GL: GL.line([(110,clip_y),(970,clip_y)],fill=A(CYAN),width=16)
    if t>=28.92:
        aa=ap(t,29.1); flag(d,(380,900,700,1200),None,29.1,t,col=AMBER)
        tag(d,110,1150,'EXCESS ADIPOSE',AMBER,28,aa)
    # dose stream into the body
    if t>=30.62:
        aa=ap(t,30.62)
        d.rounded_rectangle([140,640,200,740],radius=10,outline=A(CREAM,aa),width=4); d.rectangle([140,640,200,662],fill=A(CREAM,aa))
        txt(d,170,770,'DOSE',f(MONOB,22),CREAM,aa,'mm')
        path=[(205,700),(330,760),(450,960),(540,1040)]
        for kk in range(7):
            p=(t*0.55+kk/7)%1; pts=partial(path,p); x,y=pts[-1]
            conv = t>=38.40 and p>0.82
            col=RED if conv else CYAN
            r=13; d.ellipse([x-r,y-r,x+r,y+r],fill=A(col,aa)); txt(d,x,y,'E2' if conv else 'T',f(MONOB,16),(8,8,12),aa,'mm')
            if GL: GL.ellipse([x-r*2,y-r*2,x+r*2,y+r*2],fill=A(col,aa*0.7))
    if t>=35.0:
        aa=ap(t,35.0); tag(d,590,740,'ENDOCRINE · ACTIVE',VGOLD,26,aa)
        d.line([(640,784),(620,930)],fill=A(VGOLD,aa),width=3)
    if t>=38.40:  # aromatase enzymes inside the fat
        for i,(hx,hy) in enumerate([(430,1000),(650,990),(470,1120),(610,1130),(540,1180)]):
            aa=ap(t,38.40+i*0.07,0.12); r=lerp(10,26,aa)+2*math.sin(t*6+i)
            hexagon(d,hx,hy,r,VGOLD,aa,None,(40,24,0),3)
        tag(d,700,800,'AROMATASE ↑',VGOLD,26,ap(t,38.6))
        # E2 output meter
        lv=clamp((t-38.6)/3.0)
        d.rectangle([950,880,986,1200],outline=A((90,94,110)),width=2)
        yy=lerp(1196,900,ease_io(lv)); lit_bar(d,953,yy,983,1197,RED)
        if GL: GL.rectangle([953,yy,983,1197],fill=A(RED,0.7))
        txt(d,968,872,'E2',f(BEB,44),RED,1,'mb')
    if t>=41.34:  # the source is the tissue, not the protocol
        aa=ap(t,41.34); cross(d,156,676,RED,1.2,aa)
        tag(d,110,800,'NOT THE SOURCE',(90,94,110),24,aa,glow=False)
    if t>=40.96:
        flag(d,(372,896,708,1196),'SOURCE',40.96,t,'below')

# ---------------- S3b case-file flick (talking head) ----------------
def card_cases(im,t):
    t0,t1=43.25,45.35
    if not (t0<=t<t1+0.2): return
    d=ImageDraw.Draw(im,'RGBA'); pout=ease_io((t-t1)/0.2)
    for i in range(5):
        ti=t0+0.18*i+(0.25 if i>=2 else 0)
        p=ap(t,ti,0.16)
        if p<=0: continue
        x=int(lerp(1100,600+i*14,p)+lerp(0,520,pout)); y=1000+i*24
        d.rounded_rectangle([x,y,x+400,y+200],radius=10,fill=A((14,16,24),0.95),outline=A(VGOLD,0.85),width=3)
        d.rectangle([x,y,x+150,y+34],fill=A(VGOLD))
        txt(d,x+12,y+4,f'CASE {417+i*263:04d}',f(MONOB,20),(8,8,12))
        txt(d,x+16,y+48,'TRT · E2 HIGH',f(MONOB,22),CREAM); txt(d,x+16,y+80,'BF% HIGH',f(MONOB,22),AMBER)
        txt(d,x+16,y+112,'WK 3 · WATER',f(MONOB,22),RED)
    if t>=44.18: tag(d,600,1290-60,'SAME PATTERN',RED,28,ap(t,44.18)*(1-pout))

# ---------------- S4 bar + line chart: dose vs E2 ----------------
BX=[(260,'200',46.50),(520,'300',49.48),(780,'+?',51.42)]
BASE,TOPY=1110,700
def scene_dose(d,t):
    kicker(d,110,520,'DOSE vs E2 · EACH BUMP',t,45.6)
    a=ap(t,45.6,0.3); d.line([(150,BASE),(960,BASE)],fill=A((90,94,110),a),width=3)
    labs=['START','BUMP','BUMP']
    hs=[0.42,0.63,0.84]
    for i,(x,lab,t0) in enumerate(BX):
        txt(d,x,BASE+30,labs[i],f(MONO,22),MUTED,a,'mm')
        if t<t0: continue
        p=expo((t-t0)/0.35); h=hs[i]*(BASE-TOPY)*p; y=BASE-h
        if i<2:
            lit_bar(d,x-70,y,x+70,BASE,VGOLD,0.9)
            if GL: GL.rectangle([x-72,y-2,x+72,BASE],outline=A(VGOLD,0.8),width=6)
            txt(d,x,y-16,f'{countup(int(lab),t,t0)} MG',f(BEB,52),WHITE,1,'mb')
        else:
            dashed(d,[(x-70,BASE),(x-70,y),(x+70,y),(x+70,BASE)],VGOLD,3,0.9)
            txt(d,x,y-16,'+ ?',f(BEB,52),VGOLD,p,'mb')
    if t>=48.54: arrow(d,340,860,440,800,VGOLD,4,ap(t,48.54))
    if t>=51.42: arrow(d,600,820,690,770,VGOLD,4,ap(t,51.42))
    # how it feels under each bar
    if t>=47.70: check(d,244,BASE+56,GREEN,0.9,ap(t,47.70));
    if t>=51.74: txt(d,520,BASE+76,'CHASING',f(MONOB,22),VGOLD,ap(t,51.74),'mm')
    # E2 line climbing over every bar
    if t>=53.4:
        pts=[(340,850),(600,745),(860,650)]
        p=clamp((t-53.4)/2.4); pp=partial(pts,ease_io(p))
        polyline(d,pp,RED,7)
        for i,(x,y) in enumerate(pts[1:]):
            if math.dist(pp[-1],pts[0])>=math.dist((x,y),pts[0])-2 and len(pp)>i+1:
                d.ellipse([x-12,y-12,x+12,y+12],fill=A(RED))
        x,y=pp[-1]; d.ellipse([x-10,y-10,x+10,y+10],fill=A(RED))
        x,y=pp[-1]; txt(d,x+22,y-4,'E2',f(BEB,48),RED,ap(t,53.4),'lm')
    # aromatase activity: flat line that never drops
    if t>=56.52:
        p=clamp((t-56.52)/0.6); y=604
        polyline(d,[(150,y),(lerp(150,960,ease_io(p)),y)],AMBER,5)
        txt(d,150,y-44,'AROMATASE ACTIVITY',f(MONOB,22),AMBER,ap(t,56.52))
    if t>=57.74: flag(d,(600,582,960,626),'NEVER DROPS',57.74,t,'left')

# ---------------- S5 loop diagram (lower card) ----------------
def card_loop(im,t):
    t0,t1=59.62,64.95
    if not (t0<=t<t1+0.2): return
    pin=expo((t-t0)/0.2); pout=ease_io((t-t1)/0.18)
    box=(64,int(lerp(1010,950,pin)),1016,int(lerp(1010,950,pin))+330)
    frosted(im,box,0.9,10)
    lay=Image.new('RGBA',(W,H),(0,0,0,0)); d=ImageDraw.Draw(lay,'RGBA')
    x0,y0,x1,y1=box; cx,cy,r=300,(y0+y1)/2+6,112
    nodes=[(-90,'DOSE ↑',VGOLD),(30,'E2 ↑',RED),(150,'FEEL ↓',RED)]
    hot=t>=62.30
    for i in range(3):
        a0=nodes[i][0]+18; a1=nodes[(i+1)%3][0]-18+(360 if i==2 else 0)
        col=RED if hot and int(t*6)%2==0 else (120,124,140)
        d.arc([cx-r,cy-r,cx+r,cy+r],a0,a1,fill=A(col),width=5)
        if GL and hot: GL.arc([cx-r,cy-r,cx+r,cy+r],a0,a1,fill=A(RED,0.8),width=12)
        ang=math.radians(a1); ax,ay=cx+r*math.cos(ang),cy+r*math.sin(ang); tg=ang+math.pi/2
        d.polygon([(ax+14*math.cos(tg),ay+14*math.sin(tg)),(ax+12*math.cos(tg+2.3),ay+12*math.sin(tg+2.3)),(ax+12*math.cos(tg-2.3),ay+12*math.sin(tg-2.3))],fill=A(col))
    # particles circling (the chase)
    for k in range(5):
        ang=math.radians((t*140+k*72)%360); x,y=cx+r*math.cos(ang),cy+r*math.sin(ang)
        d.ellipse([x-7,y-7,x+7,y+7],fill=A(VGOLD));
        if GL: GL.ellipse([x-14,y-14,x+14,y+14],fill=A(VGOLD,0.7))
    for ang,lab,col in nodes:
        a=math.radians(ang); x,y=cx+r*math.cos(a),cy+r*math.sin(a)
        word,up=lab.split()[0],lab.endswith('↑')
        fn=f(BEB,40); tw=d.textlength(word,font=fn)+26
        d.rounded_rectangle([x-tw/2-14,y-26,x+tw/2+14,y+26],radius=8,fill=A((10,12,20)),outline=A(col),width=3)
        txt(d,x-13,y+2,word,fn,col,1,'mm'); ax=x+tw/2-12
        d.polygon([(ax-9,y+7),(ax+9,y+7),(ax,y-9)] if up else [(ax-9,y-7),(ax+9,y-7),(ax,y+9)],fill=A(col))
    if hot:
        aa=ap(t,62.30); hexagon(d,cx,cy,44,AMBER,aa,None,(40,20,0)); txt(d,cx,cy,'FAT',f(BEB,34),AMBER,aa,'mm')
        txt(d,600,y0+58,'MORE DOSE',f(BAR,58),CREAM,ap(t,62.30)); txt(d,600,y0+120,'MORE E2',f(BAR,58),RED,ap(t,62.62))
    if t>=64.26: tag(d,600,y0+214,'NO EXIT',RED,36,ap(t,64.26))
    txt(d,600,y0+24,'THE DOSE LOOP',f(MONOB,22),VGOLD,ap(t,59.8))
    al=pin*(1-pout); lay.putalpha(lay.split()[3].point(lambda v:int(v*al)))
    im.alpha_composite(lay); d=ImageDraw.Draw(im,'RGBA')
    d.rectangle(box,outline=A(VGOLD,0.7*al),width=3); brackets(d,*box,A(VGOLD,al),36,6)
    if GL: GL.rectangle(box,outline=A(VGOLD,0.5*al),width=6)

# ---------------- S6 roadmap ----------------
WP=[(240,1100),(620,900),(840,680)]
ROUTE=[(150,1190),(240,1100),(420,1060),(560,960),(620,900),(700,800),(840,680),(900,610)]
def scene_road(d,t):
    kicker(d,110,520,'THE ORDER THAT WORKS',t,65.1)
    dashed(d,ROUTE,(70,74,90),4,ap(t,65.1,0.3))
    keys=[(66.24,0.0),(66.6,0.12),(70.16,0.2),(70.8,0.52),(72.66,0.55),(73.3,0.85),(73.66,1.0)]
    p=0
    for (t0,p0),(t1,p1) in zip(keys,keys[1:]):
        if t<t0: break
        p=lerp(p0,p1,ease_io((t-t0)/(t1-t0)))
    if p>0: polyline(d,partial(ROUTE,p),VGOLD,7)
    lit=[66.24,70.16,72.66]
    labels=[('01','CUT BODY FAT'),('02','REASSESS T DOSE'),('03','BLOODWORK')]
    for i,((x,y),t0,(n,lab)) in enumerate(zip(WP,lit,labels)):
        on=t>=t0; aa=ap(t,t0)
        col=VGOLD if on else (80,84,100)
        d.ellipse([x-30,y-30,x+30,y+30],fill=A((10,12,20)),outline=A(col),width=5)
        if GL and on: GL.ellipse([x-34,y-34,x+34,y+34],outline=A(VGOLD,aa),width=10)
        txt(d,x,y+2,n,f(BEB,40),col,1,'mm')
        if on:
            lx,ly=(x+52,y-30) if i<2 else (x-420,y-24)
            txt(d,lx,ly,lab,f(BAR,48),CREAM,aa)
    # 01 icon: body-fat gauge draining
    if t>=66.24:
        aa=ap(t,66.24); gx,gy=120,1080
        lv=lerp(0.9,0.38,ease_io((t-66.6)/2.8))
        d.rounded_rectangle([gx,gy-150,gx+40,gy],radius=8,outline=A(CREAM,aa),width=3)
        col=AMBER if lv>0.55 else GREEN; yy=gy-4-(146*lv)
        lit_bar(d,gx+4,yy,gx+36,gy-4,col,aa)
        txt(d,gx+52,gy-150,'BF%',f(MONOB,24),col,aa)
        if t>=69.58: tag(d,gx+52,gy-110,'LEAN',GREEN,26,ap(t,69.58))
    if t>=67.76: tag(d,292,1128,'PRIORITY 01',VGOLD,26,ap(t,67.76))
    # 02 icon: dose dial turning down
    if t>=70.16:
        aa=ap(t,70.16); cx,cy,r=700,1000,58
        d.arc([cx-r,cy-r,cx+r,cy+r],180,360,fill=A(CREAM,aa),width=4)
        ang=math.radians(lerp(-40,-140,ease_io((t-71.0)/1.0)));
        d.line([(cx,cy),(cx+r*0.85*math.cos(ang),cy+r*0.85*math.sin(ang))],fill=A(VGOLD,aa),width=5)
        txt(d,cx,cy+28,'DOSE',f(MONOB,20),MUTED,aa,'mm')
    # 03 icon: tube filling + pin
    if t>=72.66:
        aa=ap(t,72.66); tx,ty=650,640
        d.rounded_rectangle([tx,ty,tx+34,ty+120],radius=16,outline=A(CREAM,aa),width=3)
        lv=clamp((t-72.8)/0.8); lit_bar(d,tx+4,ty+116-100*lv,tx+30,ty+116,RED,aa)
    if t>=73.66:
        aa=ap(t,73.66,0.2); px,py=900,610-lerp(40,0,aa)
        d.ellipse([px-22,py-60,px+22,py-16],fill=A(RED,aa)); d.polygon([(px-18,py-30),(px+18,py-30),(px,py)],fill=A(RED,aa))
        d.ellipse([px-8,py-46,px+8,py-30],fill=A((10,12,20),aa))
        if GL: GL.ellipse([px-26,py-64,px+26,py-12],fill=A(RED,aa*0.7))
    if t>=74.14:  # every single time: loop back
        aa=ap(t,74.14); dashed(d,[(800,720),(700,760),(660,860)],VGOLD,4,aa,10,8); arrow(d,664,850,656,872,VGOLD,4,aa)
        txt(d,700,770,'REPEAT',f(MONOB,22),VGOLD,aa)

# ---------------- S7 lab requisition (handoff from roadmap) ----------------
LABROWS=[('TOTAL T',75.40),('FREE T',75.52),('ESTRADIOL (SENS)',76.92),('SHBG',75.64),('CBC · HCT',75.76),('LIPID PANEL',75.88)]
def scene_lab(d,t):
    x0,y0=96,0  # relative to card origin, drawn by caller offset
def card_lab_draw(d,box,t,al):
    x0,y0,x1,y1=box
    d.rectangle([x0,y0,x1,y0+58],fill=A(COARED,al)); txt(d,x0+24,y0+12,'LAB REQUISITION · FULL PANEL',f(MONOB,26),WHITE,al)
    for i,(lab,t0) in enumerate(LABROWS):
        cx=x0+40+(i//3)*450; cy=y0+90+(i%3)*70
        d.rectangle([cx,cy,cx+36,cy+36],outline=A(CREAM,al),width=3)
        if t>=t0: check(d,cx+4,cy+2,GREEN if lab!='ESTRADIOL (SENS)' else VGOLD,0.9,al*ap(t,t0,0.08))
        txt(d,cx+56,cy-2,lab,f(BAR,40),CREAM if lab!='ESTRADIOL (SENS)' else VGOLD,al)
    if t>=76.92:
        flag(d,(x0+28,y0+214,x0+420,y0+268),None,76.92,t,'right',VGOLD); tag(d,x0+40,y0+284,'MUST CHECK',VGOLD,26,ap(t,77.0))
    if t>=77.58:
        p=expo((t-77.58)/0.10); s=lerp(1.2,1,p)
        tag(d,x1-260,y1-70,'NO GUESSING',GREEN,int(30*s),p*al)

# ---------------- S8 comparison area charts ----------------
def area(d,x0,y0,x1,y1,fn,upto,cut,colA,colB,al,wmax=12):
    pts=[(lerp(x0,x1,w/(wmax*4)),y1-(y1-y0)*fn(w/4)) for w in range(0,int(upto*4)+1)]
    if len(pts)<2: return pts
    good=[p for p,w in zip(pts,range(len(pts))) if w/4<=cut]; bad=[p for p,w in zip(pts,range(len(pts))) if w/4>=cut]
    for seg,col in ((good,colA),(bad,colB)):
        if len(seg)>1:
            d.polygon(seg+[(seg[-1][0],y1),(seg[0][0],y1)],fill=A(col,0.22*al)); polyline(d,seg,col,6,al)
    return pts
def steady(w): return 0.66+0.03*math.sin(w*1.7)
def blast(w):
    if w<1: return lerp(0.4,0.95,ease_io(w))
    if w<3: return 0.95
    if w<4: return lerp(0.95,0.18,ease_io(w-3))
    return 0.18+0.03*math.sin(w*2)
def scene_compare(d,t):
    kicker(d,110,520,'SAME 12 WEEKS · TWO APPROACHES',t,79.2)
    cols=[(110,'LOWER DOSE',81.68,steady,GREEN,GREEN,99),(560,'BLAST',85.70,blast,CREAM,RED,3)]
    for x,lab,t0,fn,cA,cB,cut in cols:
        a=ap(t,79.4,0.25)
        d.rounded_rectangle([x,600,x+410,1230],radius=14,fill=A((12,14,22),0.9*a),outline=A((70,74,90),a),width=2)
        if t<t0:
            txt(d,x+205,900,'—',f(BEB,60),(70,74,90),a,'mm'); continue
        aa=ap(t,t0)
        d.line([(x,600),(x+lerp(0,410,aa),600)],fill=A(cB if cut<99 else GREEN),width=5)
        txt(d,x+24,620,lab,f(BEB,64),cA if cut==99 else WHITE,aa)
        if cut==99: upto=lerp(0,12,ease_io((t-t0-0.2)/1.4))
        elif t<88.84: upto=lerp(0,3,ease_io((t-85.9)/1.8))
        else: upto=lerp(3,12,ease_io((t-88.84)/1.9))
        area(d,x+24,800,x+386,1120,fn,upto,cut,cA,cB,aa)
        txt(d,x+24,1140,'WK0',f(MONO,20),MUTED,aa); txt(d,x+386,1140,'WK12',f(MONO,20),MUTED,aa,'ra')
        txt(d,x+24,1176,'HOW YOU FEEL',f(MONOB,20),MUTED,aa)
    if t>=83.00: tag(d,110,700,'FEWER COMPOUNDS',VGOLD,24,ap(t,83.0))
    if t>=84.0: check(d,456,640,GREEN,1.1,ap(t,84.0))
    if t>=86.44: tag(d,560,700,'MASSIVE DOSE',RED,24,ap(t,86.44))
    if t>=87.64:
        aa=ap(t,87.64); xa=560+24; xb=xa+(386-24)*3/12
        brackets(d,xa,790,xb,1120,A(VGOLD,aa),20,5); txt(d,xb+16,1000,'WK 0–3',f(MONOB,24),VGOLD,aa,'lm')
    if t>=89.28:
        aa=ap(t,89.28); xb=560+24+(386-24)*3/12
        tag(d,xb+20,860,'REST OF CYCLE',RED,24,aa)

# ---------------- S9 CTA card ----------------
LOGO=None
def card_cta(im,t):
    global LOGO
    t0=91.45
    if t<t0: return
    if LOGO is None:
        lg=Image.open(LOGO_P).convert('RGB').resize((120,120),Image.LANCZOS); m=Image.new('L',(120,120),0); ImageDraw.Draw(m).ellipse([0,0,119,119],fill=255); lg.putalpha(m); LOGO=lg
    pin=expo((t-t0)/0.22); box=(64,int(lerp(1010,940,pin)),1016,int(lerp(1010,940,pin))+350)
    frosted(im,box,0.9,10)
    d=ImageDraw.Draw(im,'RGBA'); x0,y0,x1,y1=box; al=pin
    lg=LOGO.copy(); lg.putalpha(lg.split()[3].point(lambda v:int(v*al))); im.alpha_composite(lg,(x0+30,y0+30))
    txt(d,x0+170,y0+40,'COACH AGZ',f(BEB,56),GOLD,al); txt(d,x0+172,y0+100,'@coach.agz',f(MONO,26),GOLD,al)
    if t>=92.32:
        kicker(d,x0+30,y0+170,'FREE · ESTROGEN PROTOCOL + FRAMEWORK',t,92.32,VGOLD,24)
    if t>=94.30:
        p=expo((t-94.30)/0.16); xx=lerp(x1+40,x0+30,p)
        fn=f(BEB,92); lab='COMMENT  "E2"'; tw=d.textlength(lab,font=fn)
        lit_bar(d,xx,y0+214,xx+tw+60,y0+318,VGOLD)
        if GL: GL.rectangle([xx-4,y0+210,xx+tw+64,y0+322],outline=A(VGOLD),width=12)
        txt(d,xx+30,y0+268,lab,fn,(10,10,14),1,'lm')
    d.rectangle(box,outline=A(VGOLD,0.7*al),width=3); brackets(d,*box,A(VGOLD,al),36,6)
    txt(d,W/2,1880,'FOR RESEARCH & EDUCATIONAL PURPOSES ONLY',f(MONO,20),(170,170,176),al*0.9,'mm')

def frosted(im,box,dark=0.86,blur=10):
    x0,y0,x1,y1=[int(v) for v in box]
    if x1<=x0 or y1<=y0: return
    reg=im.crop((x0,y0,x1,y1)).convert('RGB').filter(ImageFilter.GaussianBlur(blur))
    im.paste(Image.blend(reg,Image.new('RGB',reg.size,DEEP),dark).convert('RGBA'),(x0,y0))

# full-screen panel scenes: (t_in, t_out, fn, header, fig, exit)  exit 'cut' = hard cut at a jump cut
P=(64,470,1016,1260)
SCENES=[(7.90,19.66,scene_pattern,'CASE PATTERN','FIG 01','cut'),
        (25.54,43.0,scene_scan,'ADIPOSE SCAN','FIG 02','fade'),
        (45.6,59.45,scene_dose,'DOSE LOG','FIG 03','fade'),
        (65.04,75.05,scene_road,'ROADMAP','FIG 04','handoff'),
        (78.85,91.30,scene_compare,'OUTCOME','FIG 05','fade')]
LAB=(75.05,78.75)
LABBOX=(64,930,1016,1290)

# ---------------- captions ----------------
def build_groups():
    G=[];cur=[]
    for i,x in enumerate(WORDS):
        if cur:
            prev=WORDS[cur[-1]]
            if len(cur)>=3 or x['s']-prev['e']>0.28 or prev['w'][-1] in '.,?!' or any(prev['e']<=c<x['s']+0.01 for c in CUTS): G.append(cur); cur=[]
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
CAP_Y=1335
def captions(im,t):
    g=group_at(t)
    if not g: return
    d=ImageDraw.Draw(im,'RGBA')
    ws=[WORDS[i]['w'].upper().rstrip(',.?!') for i in g]
    size=128
    while True:
        fn=f(BEB,size); sp=d.textlength(' ',font=fn)+14; wd=[d.textlength(w,font=fn) for w in ws]; tot=sum(wd)+sp*(len(ws)-1)
        if tot<=920: break
        size-=4
    xs=[];x=(W-tot)/2
    for w_ in wd: xs.append(x); x+=w_+sp
    act=0
    for k,i in enumerate(g):
        if WORDS[i]['s']<=t: act=k
    g0=WORDS[g[0]]['s']; s=lerp(0.9,1,expo((t-g0)/0.10))
    cap=Image.new('RGBA',(W,300),(0,0,0,0)); cd=ImageDraw.Draw(cap); shd=Image.new('RGBA',(W,300),(0,0,0,0)); sd=ImageDraw.Draw(shd)
    prev=max(0,act-1); bt=expo((t-WORDS[g[act]]['s'])/0.07) if act>0 else 1
    bx0=lerp(xs[prev],xs[act],bt)-18; bx1=lerp(xs[prev]+wd[prev],xs[act]+wd[act],bt)+18
    for k,(w_,x_) in enumerate(zip(ws,xs)):
        if k!=act: sd.text((x_+4,46),w_,font=fn,fill=(0,0,0,210))
    cap.alpha_composite(shd.filter(ImageFilter.GaussianBlur(6)))
    lit_bar(cd,bx0,40+size*0.02,bx1,40+size*0.98,RED)
    for k,(w_,x_) in enumerate(zip(ws,xs)): cd.text((x_,40),w_,font=fn,fill=CREAM,stroke_width=0 if k==act else 3,stroke_fill=(0,0,0))
    if abs(s-1)>0.002:
        cap=cap.resize((int(W*s),int(300*s)),Image.BICUBIC); ox=int((W-cap.width)/2); oy=int(CAP_Y-40-(cap.height-300)/2)
    else: ox,oy=0,CAP_Y-40
    im.alpha_composite(cap,(ox,oy))

# ---------------- text hook + topic band ----------------
HOOK_END=6.0; BAND_END=next(c for c in CUTS if c>DUR/2)
def hook(im,t):
    if t>=HOOK_END+0.15: return
    a=1-clamp((t-HOOK_END)/0.15); s=lerp(1.0,1.04,clamp(t/HOOK_END))
    lay=Image.new('RGBA',(W,420),(0,0,0,0)); d=ImageDraw.Draw(lay,'RGBA')
    l1='Puffy by week 3 on TRT'; l2a='BODY FAT'; l2b=' is the real cause'
    sz=96
    while max(d.textlength(l1,font=f(BAR,sz)),d.textlength(l2a+l2b,font=f(BAR,sz)))>880: sz-=2
    fn=f(BAR,sz); w1=d.textlength(l1,font=fn); w2=d.textlength(l2a+l2b,font=fn); bw=max(w1,w2)+80
    bx0=(W-bw)/2; by0=40; by1=by0+sz*2+70
    d.rounded_rectangle([bx0,by0,bx0+bw,by1],radius=22,fill=(8,10,16,215))
    d.rectangle([bx0,by0+18,bx0+8,by1-18],fill=A(VGOLD))
    txt(d,W/2,by0+30+sz*0.5,l1,fn,WHITE,1,'mm')
    x=(W-w2)/2; y=by0+40+sz*1.5
    d.text((x,y),l2a,font=fn,fill=A(VGOLD),anchor='lm'); d.text((x+d.textlength(l2a,font=fn),y),l2b,font=fn,fill=A(WHITE),anchor='lm')
    if s!=1: lay=lay.resize((int(W*s),int(420*s)),Image.BICUBIC)
    if a<1: lay.putalpha(lay.split()[3].point(lambda v:int(v*a)))
    im.alpha_composite(lay,(int((W-lay.width)/2),int(250-(lay.height-420)/2)))
def band(im,t):
    if t<HOOK_END or t>=BAND_END: return
    a=clamp((t-HOOK_END)/0.15); d=ImageDraw.Draw(im,'RGBA')
    d.rectangle([8,212,W,372],fill=NAVY+(int(228*a),)); d.line([(64,244),(108,244)],fill=A(GOLD,a),width=4); txt(d,122,228,'@coach.agz',f(MONO,28),GOLD,a)
    fn=f(BAR,74); x=64; y=266
    d.text((x,y),'BODY FAT',font=fn,fill=A(VGOLD,a)); d.text((x+d.textlength('BODY FAT',font=fn),y),' is making your E2',font=fn,fill=A(CREAM,a))

# ---------------- frame ----------------
def seg_of(t): return sum(1 for c in CUTS if c<=t+1e-6)
def active_scene(t):
    for sc in SCENES:
        if sc[0]<=t<sc[1]+(0.0 if sc[5] in ('cut','handoff') else 0.2): return sc
    return None
def shake_k(t):
    for ts in (24.95,64.30):
        k=round((t-ts)*FPS)
        if k in (0,1): return [9,-5][k]
    return 0
def frame(src,t):
    z=1.0 if seg_of(t)%2==0 else 1.08
    if t<1.5: z=lerp(1.0,1.0,0)
    if z!=1.0:
        big=src.resize((int(W*z),int(H*z)),Image.BICUBIC); ox=(big.width-W)//2; oy=int((big.height-H)*0.35); src=big.crop((ox,oy,ox+W,oy+H))
    sc=active_scene(t)
    inlab=LAB[0]<=t<LAB[1]+0.2
    g=0
    if sc:
        gi=ease_io((t-sc[0]+0.05)/0.30)
        go=0 if sc[5]=='cut' else (1-ease_io((t-sc[1])/0.22) if sc[5]=='fade' else 1)
        g=min(gi,go)
    if inlab: g=max(g,1-ease_io((t-LAB[0])/0.35))
    bg=src
    if g>0: bg=Image.blend(src.filter(ImageFilter.GaussianBlur(18*g)),Image.new('RGB',(W,H),(5,8,16)),0.68*g)
    im=bg.convert('RGBA')
    yy=np.arange(H); a=np.where(yy>1180,np.clip((yy-1180)/260,0,1)*110,0); a=np.maximum(a,np.where(yy<420,(1-yy/420)*120,0)); scr=(a*(1-g)).astype(np.uint8)
    im.alpha_composite(Image.merge('RGBA',[Image.new('L',(W,H),c) for c in NAVY]+[Image.fromarray(np.repeat(scr[:,None],W,1))]))
    global GL
    glow=Image.new('RGBA',(W,H),(0,0,0,0)); GL=ImageDraw.Draw(glow,'RGBA')
    if sc:
        pin=expo((t-sc[0])/0.20); pout=clamp((t-sc[1])/0.16) if sc[5]=='fade' else 0
        box=P
        if sc[5]=='handoff' and t>=sc[1]-0.3:  # roadmap panel collapses into the lab card
            k=ease_io((t-(sc[1]-0.3))/0.3); box=tuple(lerp(a_,b_,k) for a_,b_ in zip(P,LABBOX))
        if pout<1:
            s=lerp(1.05,1.0,pin)*lerp(1.0,1.03,pout); cx=(box[0]+box[2])/2; cy=(box[1]+box[3])/2; w=(box[2]-box[0])*s; h=(box[3]-box[1])*s
            x0,y0,x1,y1=cx-w/2,cy-h/2,cx+w/2,cy+h/2
            frosted(im,(x0,y0,x1,y1),0.92,8)
            lay=Image.new('RGBA',(W,H),(0,0,0,0)); d=ImageDraw.Draw(lay,'RGBA')
            if sc[2] is scene_scan: sc[2](d,t,lay)
            else: sc[2](d,t)
            fade_c=1.0
            if sc[5]=='handoff' and t>=sc[1]-0.3: fade_c=1-clamp((t-(sc[1]-0.3))/0.15)
            if pin<1: lay=lay.filter(ImageFilter.GaussianBlur(8*(1-pin)))
            al=pin*(1-pout)
            lay.putalpha(lay.split()[3].point(lambda v:int(v*al*fade_c)))
            m=Image.new('L',(W,H),0); ImageDraw.Draw(m).rectangle([x0,y0,x1,y1],fill=255)
            lay.putalpha(Image.fromarray(np.minimum(np.asarray(lay.split()[3]),np.asarray(m))))
            im.alpha_composite(lay); d=ImageDraw.Draw(im,'RGBA')
            d.rectangle([x0,y0,x1,y1],outline=A(VGOLD,0.8*al),width=3); brackets(d,x0,y0,x1,y1,A(VGOLD,al),48,7)
            GL.rectangle([x0,y0,x1,y1],outline=A(VGOLD,0.5*al),width=6); brackets(GL,x0,y0,x1,y1,A(VGOLD,al),48,14)
            d.ellipse([x0+26,y0+26,x0+42,y0+42],fill=A(RED,al if int(t*4)%2==0 else al/3))
            txt(d,x0+56,y0+18,sc[3],f(MONO,28),WHITE,al*fade_c); fr=f(MONO,28); tw=d.textlength(sc[4],font=fr); txt(d,x1-30-tw,y0+18,sc[4],fr,VGOLD,al*fade_c)
    if inlab:
        pout=ease_io((t-LAB[1])/0.2); box=LABBOX
        frosted(im,box,0.92,8); lay=Image.new('RGBA',(W,H),(0,0,0,0)); d=ImageDraw.Draw(lay,'RGBA')
        al=clamp((t-LAB[0])/0.15)*(1-pout); card_lab_draw(d,box,t,1)
        lay.putalpha(lay.split()[3].point(lambda v:int(v*al))); im.alpha_composite(lay)
        d=ImageDraw.Draw(im,'RGBA'); d.rectangle(box,outline=A(VGOLD,0.8*(1-pout)),width=3); brackets(d,*box,A(VGOLD,1-pout),40,7)
        GL.rectangle(box,outline=A(VGOLD,0.5*(1-pout)),width=6)
    card_clinic(im,t); card_cases(im,t); card_loop(im,t); card_cta(im,t)
    hook(im,t); band(im,t)
    GL=None
    if glow.getbbox():
        sm=glow.resize((W//4,H//4),Image.BILINEAR)
        g1=np.asarray(sm.filter(ImageFilter.GaussianBlur(3.5))).astype(np.float32)/255; g2=np.asarray(sm.filter(ImageFilter.GaussianBlur(10))).astype(np.float32)/255
        prem=np.clip(g1[...,:3]*g1[...,3:]*2.3+g2[...,:3]*g2[...,3:]*1.8,0,1)
        prem=np.asarray(Image.fromarray((prem*255).astype(np.uint8)).resize((W,H),Image.BILINEAR)).astype(np.float32)/255
        b=np.asarray(im.convert('RGB')).astype(np.float32)/255
        im=Image.fromarray(((1-(1-b)*(1-prem))*255).astype(np.uint8)).convert('RGBA')
    d=ImageDraw.Draw(im,'RGBA'); d.rectangle([0,0,7,H],fill=GOLD)
    captions(im,t)
    out=im.convert('RGB')
    dx=shake_k(t)
    if dx:
        zz=1.025; big=out.resize((int(W*zz),int(H*zz)),Image.BICUBIC); ox=(big.width-W)//2-dx; oy=(big.height-H)//2
        out=big.crop((ox,oy,ox+W,oy+H)); ImageDraw.Draw(out).rectangle([0,0,7,H],fill=GOLD)
    return out

def new_to_src(tn):
    acc=0
    for a,b in KEEP:
        if tn < acc+(b-a)-1e-9: return a+(tn-acc)
        acc+=b-a
    return KEEP[-1][1]-1/FPS
if __name__=='__main__':
    mode=sys.argv[2]
    if mode=='stills':
        import os; os.makedirs(S+'/qc',exist_ok=True)
        for tt in [float(x) for x in sys.argv[3:]]:
            st=new_to_src(tt)
            subprocess.run(['ffmpeg','-v','error','-y','-ss',f'{st:.4f}','-i',SRC,'-frames:v','1',S+'/qc/_src.png'])
            frame(Image.open(S+'/qc/_src.png').convert('RGB'),tt).resize((540,960),Image.LANCZOS).save(S+f'/qc/st_{tt:06.2f}.jpg',quality=88)
        sys.exit()
    n0,n1,out=int(sys.argv[3]),int(sys.argv[4]),sys.argv[5]
    srcf=[int(round(new_to_src(n/FPS)*FPS)) for n in range(n0,n1)]
    first,last=srcf[0],srcf[-1]
    dec=subprocess.Popen(['ffmpeg','-v','error','-ss',f'{max(0,first-2)/FPS:.4f}','-i',SRC,'-f','rawvideo','-pix_fmt','rgb24','-'],stdout=subprocess.PIPE)
    # -ss before -i is frame-accurate on re-encode; verify first frame index by counting from max(0,first-2)
    cur=max(0,first-2)-1; buf=None
    enc=subprocess.Popen(['ffmpeg','-v','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-','-c:v','libx264','-crf','17','-preset','medium','-pix_fmt','yuv420p',out],stdin=subprocess.PIPE)
    for n,o in zip(range(n0,n1),srcf):
        while cur<o:
            buf=dec.stdout.read(W*H*3); cur+=1
            if len(buf)<W*H*3: raise SystemExit(f'short read at src frame {cur}')
        enc.stdin.write(frame(Image.frombuffer('RGB',(W,H),buf),n/FPS).tobytes())
    enc.stdin.close(); enc.wait(); dec.kill(); print('done',n0,n1,flush=True)
