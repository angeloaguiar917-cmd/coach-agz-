import json, subprocess, sys, math, os
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
S='/tmp/claude-0/-home-user-coach-agz-/21389a83-a8e0-52d1-b0a2-5fe73e4f7c77/scratchpad/'
B=S+'build/'; F=S+'fonts/'
W,H=1080,1920; FPS=30
WORDS=json.load(open(B+'words_cut.json'))
FACE=json.load(open(B+'faceband.json'))
SRCMAP=json.load(open(B+'srcmap.json'))
MASKS=None   # face-track was precomputed to faceband.json; masks.npy (414MB) not committed
NF=len(SRCMAP)
# ---- palette ----
GOLD=(201,169,110); CREAM=(244,241,234); NAVY=(14,17,23)
RED=(255,34,28); VGOLD=(255,194,26); CYAN=(0,229,255); GREEN=(30,255,110)
AMBER=(240,160,48); DEEP=(2,3,8); INK=(6,8,14); WHITE=(255,255,255); MUT=(150,154,168)
MONO='JBMono-500.ttf'; MONOB='JBMono-700.ttf'; BEB='BebasNeue.ttf'
DMB='DMSans-700.ttf'; DMR='DMSans-400.ttf'; BAR='Barlow-800.ttf'; BARM='Barlow-600.ttf'
_fc={}
def f(n,s):
    k=(n,int(s))
    if k not in _fc: _fc[k]=ImageFont.truetype(F+n,int(s))
    return _fc[k]
def clamp(x,a=0,b=1): return max(a,min(b,x))
def expo(x): x=clamp(x); return 1 if x>=1 else 1-2**(-10*x)
def ease(x): x=clamp(x); return 4*x**3 if x<.5 else 1-(-2*x+2)**3/2
def back(x):  # small overshoot then settle
    x=clamp(x); c=1.70158; return 1+2.2*(x-1)**3+1.2*(x-1)**2
def lerp(a,b,t): return a+(b-a)*t
def A(c,a): return tuple(int(v) for v in c[:3])+(int(clamp(a)*255),)
def appear(t,t0,dur=0.16): return expo((t-t0)/dur)
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
def lit_vbar(d,x0,y0,x1,y1,col,a=1.0):   # vertical lit gradient (hot top)
    wdt=max(1,int(x1-x0))
    for i in range(wdt):
        k=i/wdt; c=tuple(int(min(255,v*(1.14-0.3*k))) for v in col)
        d.line([(x0+i,y0),(x0+i,y1)],fill=c+(int(255*a),))
def txt(d,x,y,s,font,col,a=1.0,anchor=None,sw=0,sc=(0,0,0)):
    d.text((x,y),s,font=font,fill=A(col,a),anchor=anchor,stroke_width=sw,stroke_fill=A(sc,a) if sw else None)
def frosted(im,box,dark=0.86,blur=10):
    x0,y0,x1,y1=[int(v) for v in box]
    x0=max(0,x0);y0=max(0,y0);x1=min(W,x1);y1=min(H,y1)
    if x1<=x0 or y1<=y0: return
    reg=im.crop((x0,y0,x1,y1)).convert('RGB').filter(ImageFilter.GaussianBlur(blur))
    im.paste(Image.blend(reg,Image.new('RGB',reg.size,DEEP),dark).convert('RGBA'),(x0,y0))
def card(im,d,x0,y0,x1,y1,a=1.0,bar=VGOLD,r=26,dark=0.9):
    frosted(im,(x0,y0,x1,y1),dark,9)
    dd=ImageDraw.Draw(im,'RGBA')
    dd.rounded_rectangle([x0,y0,x1,y1],radius=r,outline=A(bar,0.55*a),width=2)
    dd.rounded_rectangle([x0,y0,x0+10,y1],radius=4,fill=A(bar,a))  # left bar
    if GL: GL.rounded_rectangle([x0,y0,x1,y1],radius=r,outline=A(bar,0.5*a),width=6)
def tag(d,x,y,label,col=RED,size=32,a=1.0,glow=True,pad=14):
    fn=f(MONOB,size); tw=d.textlength(label,font=fn); h=size+16
    lit_bar(d,x,y,x+tw+pad*2,y+h,col,a); txt(d,x+pad,y+6,label,fn,(WHITE if col not in (VGOLD,GREEN,CYAN) else INK),a)
    if GL and glow: GL.rounded_rectangle([x-3,y-3,x+tw+pad*2+3,y+h+3],radius=4,outline=A(col,a),width=7)
    return x+tw+pad*2
def kicker(d,x,y,label,col=VGOLD,a=1.0,size=28):
    d.line([(x,y+size*0.55),(x+40,y+size*0.55)],fill=A(col,a),width=4)
    txt(d,x+54,y,label,f(MONO,size),col,a)
def check(d,x,y,col,s=1.0,a=1.0):
    d.line([(x,y+16*s),(x+10*s,y+28*s),(x+30*s,y+2*s)],fill=A(col,a),width=int(6*s))
    if GL: GL.line([(x,y+16*s),(x+10*s,y+28*s),(x+30*s,y+2*s)],fill=A(col,a),width=int(11*s))
def cross(d,x,y,col,s=1.0,a=1.0):
    d.line([(x,y),(x+26*s,y+26*s)],fill=A(col,a),width=int(6*s)); d.line([(x+26*s,y),(x,y+26*s)],fill=A(col,a),width=int(6*s))
def arrow(d,x0,y0,x1,y1,col,w=5,a=1.0):
    d.line([(x0,y0),(x1,y1)],fill=A(col,a),width=w)
    ang=math.atan2(y1-y0,x1-x0); L=16+w
    d.polygon([(x1,y1),(x1-L*math.cos(ang-0.5),y1-L*math.sin(ang-0.5)),(x1-L*math.cos(ang+0.5),y1-L*math.sin(ang+0.5))],fill=A(col,a))
def flow(d,x0,y0,x1,y1,t,col,n=5,speed=0.9,a=1.0,r=7):
    for k in range(n):
        p=(t*speed+k/n)%1; x=lerp(x0,x1,p); y=lerp(y0,y1,p); fa=a*min(1,p*6,(1-p)*6)
        d.ellipse([x-r,y-r,x+r,y+r],fill=A(col,fa))
        if GL: GL.ellipse([x-r*1.8,y-r*1.8,x+r*1.8,y+r*1.8],fill=A(col,fa*0.9))

# ---------------- GRAPH TYPES (variety) ----------------
def ring_gauge(d,cx,cy,r,frac,col,label,value,a=1.0,warn=0.0,wd=22):
    # full track
    d.arc([cx-r,cy-r,cx+r,cy+r],135,45,fill=A((60,64,78),a),width=wd)
    sweep=270*clamp(frac)
    # draw colored arc in steps for glow
    steps=max(2,int(sweep/6))
    for i in range(steps):
        a0=135+i/steps*sweep; a1=135+(i+1)/steps*sweep
        d.arc([cx-r,cy-r,cx+r,cy+r],a0,a1+1,fill=A(col,a),width=wd)
    if GL and frac>0.02: GL.arc([cx-r,cy-r,cx+r,cy+r],135,135+sweep,fill=A(col,a*0.8),width=wd+4)
    # needle tick at end
    ang=math.radians(135+sweep); ex=cx+math.cos(ang)*r; ey=cy+math.sin(ang)*r
    d.ellipse([ex-9,ey-9,ex+9,ey+9],fill=A(WHITE,a))
    txt(d,cx,cy-20,value,f(BEB,70),col,a,anchor='mm')
    txt(d,cx,cy+34,label,f(MONO,24),CREAM,a,anchor='mm')
def vbars(d,x0,ybase,specs,t,a=1.0,bw=96,gap=58,maxh=300):
    # specs: list of (label,frac,col,flag,t0)
    x=x0
    for (lab,frac,col,flag,t0) in specs:
        p=ease(clamp((t-t0)/0.5)); h=maxh*frac*p
        d.rectangle([x,ybase-maxh,x+bw,ybase],outline=A((54,58,72),a),width=2)
        lit_vbar(d,x+3,ybase-h,x+bw-3,ybase-1,col,a)
        if GL and h>4: GL.rectangle([x+3,ybase-h,x+bw-3,ybase],fill=A(col,a*0.6))
        txt(d,x+bw/2,ybase+10,lab,f(MONO,24),CREAM,a,anchor='ma')
        if flag and p>0.8:
            tag(d,x+bw/2-26,ybase-h-56,flag,RED if flag in('H','HIGH') else (GREEN if flag=='OK' else VGOLD),26,a)
        x+=bw+gap
    return x
def line_crash(d,x0,y0,x1,y1,t,t0,a=1.0,label='HDL',v0=62,v1=21):
    # axes
    d.line([(x0,y0),(x0,y1)],fill=A((80,84,100),a),width=2)
    d.line([(x0,y1),(x1,y1)],fill=A((80,84,100),a),width=2)
    for k in range(1,4): d.line([(x0,lerp(y1,y0,k/4)),(x1,lerp(y1,y0,k/4))],fill=A((34,38,52),a),width=1)
    # curve: flat-ish then cliff
    pts=[]
    N=48
    for i in range(N+1):
        u=i/N
        # plateau to ~0.4 then steep fall
        yy=1-(0 if u<0.38 else ((u-0.38)/0.62)**1.7)
        pts.append((lerp(x0,x1,u), lerp(y1-14,y0+10,yy)))
    p=clamp((t-t0)/1.6)
    nshow=int(p*N)
    if nshow>=1:
        seg=pts[:nshow+1]
        # red zone fill under danger part
        d.line(seg,fill=A(RED,a),width=7,joint='curve')
        if GL: GL.line(seg,fill=A(RED,a*0.9),width=12,joint='curve')
        ex,ey=seg[-1]
        d.ellipse([ex-10,ey-10,ex+10,ey+10],fill=A(WHITE,a))
    # value readout counts down
    val=int(lerp(v0,v1,clamp((p-0.3)/0.7)))
    txt(d,x1-4,y0-4,str(val),f(BEB,92),RED if val<v0*0.6 else CREAM,a,anchor='ra')
    txt(d,x1-4,y0+92,'mg/dL',f(MONO,24),MUT,a,anchor='ra')
    txt(d,x0,y0-44,label,f(MONO,28),VGOLD,a)
def molecule(d,cx,cy,t,t0,a=1.0):
    # three fused hexagon rings (steroid nucleus) schematic
    R=58
    centers=[(cx-R*1.5,cy),(cx-R*0.0,cy-R*0.3),(cx+R*1.5,cy),(cx+R*0.75,cy+R*1.3)]
    pb=ease(clamp((t-t0)/0.6))
    for ci,(hx,hy) in enumerate(centers[:4]):
        pts=[(hx+R*0.62*math.cos(math.pi/3*i+math.pi/6),hy+R*0.62*math.sin(math.pi/3*i+math.pi/6)) for i in range(6)]
        col=WHITE
        d.line(pts+[pts[0]],fill=A(col,a*pb),width=4)
    # 17-alpha methyl highlight (top-right node)
    hx,hy=centers[2]
    nx,ny=hx+R*0.62*math.cos(-math.pi/6), hy+R*0.62*math.sin(-math.pi/6)
    ph=appear(t,t0+0.5)
    if ph>0:
        d.line([(nx,ny),(nx+34,ny-30)],fill=A(VGOLD,a),width=5)
        d.ellipse([nx+28,ny-44,nx+54,ny-18],fill=A(VGOLD,a))
        if GL: GL.ellipse([nx+24,ny-48,nx+58,ny-14],outline=A(VGOLD,a),width=6)
        txt(d,nx+60,ny-44,'C-17',f(MONO,26),VGOLD,a*ph)
def roadmap(d,x0,y,t,a=1.0):
    steps=[('ANALYZE',CYAN,88.4),('PIVOT',VGOLD,88.95),('OPTIMIZE',GREEN,89.8)]
    cw=300; x=x0
    for i,(lab,col,t0) in enumerate(steps):
        p=ease(appear(t,t0,0.4))
        bx0=x; bx1=x+cw-30; by0=y; by1=y+96
        # chevron block
        pts=[(bx0,by0),(bx1,by0),(bx1+34,(by0+by1)/2),(bx1,by1),(bx0,by1),(bx0+34 if i>0 else bx0,(by0+by1)/2)]
        d.polygon(pts,fill=A((16,20,30),0.92*a*p),outline=A(col,a*p))
        if GL and p>0.3: GL.line(pts+[pts[0]],fill=A(col,a*p*0.8),width=5)
        txt(d,(bx0+bx1)/2+12,(by0+by1)/2,lab,f(BEB,56),col if p>0.5 else CREAM,a*p,anchor='mm')
        x+=cw
def lab_card(im,d,x0,y0,t,a=1.0):
    rows=[('HDL CHOLESTEROL','21','mg/dL','LOW',RED,54.9),
          ('ALT (SGPT)','88','U/L','HIGH',RED,55.6),
          ('AST (SGOT)','74','U/L','HIGH',RED,56.1),
          ('TRIGLYCERIDES','210','mg/dL','HIGH',AMBER,56.6)]
    wx=W-2*x0
    card(im,d,x0,y0,x0+wx,y0+92+len(rows)*94+18,a,bar=VGOLD,r=22,dark=0.9)
    d=ImageDraw.Draw(im,'RGBA')
    txt(d,x0+34,y0+24,'LIPID / CMP PANEL',f(BEB,58),CREAM,a)
    txt(d,x0+wx-34,y0+44,'NOT ORDERED',f(MONO,24),MUT,a,anchor='ra')
    yy=y0+104
    for i,(nm,v,u,flag,col,t0) in enumerate(rows):
        p=appear(t,t0,0.25)
        if p<=0: yy+=94; continue
        txt(d,x0+34,yy,nm,f(DMB,38),CREAM,a*p)
        txt(d,x0+34,yy+46,'flagged out of range',f(MONO,20),MUT,a*p)
        txt(d,x0+wx-250,yy-4,v,f(BEB,64),col,a*p)
        txt(d,x0+wx-158,yy+18,u,f(MONO,22),MUT,a*p)
        if p>0.6: tag(d,x0+wx-150,yy+4,flag,col,28,a)
        d.line([(x0+30,yy+84),(x0+wx-30,yy+84)],fill=A((48,52,66),a*p),width=2)
        yy+=94

# ---------------- persistent corner HUD (visual hook, varied, non-text-headline) ----------------
def hud(im,d,t):
    # three diagnostic chips top area; appears as cold-open visual hook, then stays faint
    intro = clamp((t-0.2)/0.5)
    fade = 1.0 if t<5.4 else lerp(1.0,0.0,clamp((t-5.4)/0.6))
    if fade<=0: return
    chips=[('HDL',RED,'CRASH'),('LIVER',AMBER,'STRESS'),('LIPIDS',VGOLD,'OFF')]
    bw=300; x=60; y=250
    for i,(lab,col,st) in enumerate(chips):
        p=ease(clamp((t-0.2-i*0.18)/0.5))
        if p<=0: continue
        dx=lerp(-40,0,p); al=p*fade*(0.95 if t<5.4 else 0.5+0.5*fade)
        bx=x+i*bw+dx
        d.rounded_rectangle([bx,y,bx+bw-24,y+70],radius=12,fill=A((10,13,20),0.82*al),outline=A(col,al))
        d.ellipse([bx+16,y+24,bx+40,y+48],fill=A(col,al*(0.6+0.4*math.sin(t*6+i))))
        if GL: GL.ellipse([bx+12,y+20,bx+44,y+52],fill=A(col,al*0.7))
        txt(d,bx+52,y+8,lab,f(BEB,40),CREAM,al)
        txt(d,bx+52,y+44,st,f(MONO,20),col,al)
    # scan reticle sweep on hook
    if t<3.0:
        sp=ease(clamp(t/2.4)); sy=lerp(360,1500,sp); al=(1-clamp((t-2.2)/0.8))*intro
        d.line([(50,sy),(W-50,sy)],fill=A(CYAN,0.5*al),width=3)
        if GL: GL.line([(50,sy),(W-50,sy)],fill=A(CYAN,0.6*al),width=5)
        brackets(d,56,360,W-56,1520,A(CYAN,0.35*al),40,3)

# ---------------- SCENES (lower-third / behind-head graphics) ----------------
STG0,STG1=1246,1858   # graphics stage (below the face)
def sc_crash(im,d,t):   # HDL line crash  ~20.6-31.5
    card(im,d,56,STG0,W-56,STG1,a=1.0,bar=RED,r=26,dark=0.9); d=ImageDraw.Draw(im,'RGBA')
    kicker(d,96,STG0+26,'MARKER 01 · CARDIOVASCULAR',RED)
    line_crash(d,160,STG0+104,W-160,1746,t,20.9,label='HDL (GOOD CHOLESTEROL)',v0=58,v1=21)
    if t>27.2: tag(d,160,1766,'TOTAL COLLAPSE',RED,30,appear(t,27.2))
    if t>29.4: tag(d,560,1766,'SYSTEM DEFENSELESS',RED,30,appear(t,29.4))
def sc_mol(im,d,t):     # 17aa oral molecule ~31.8-39.8
    card(im,d,56,STG0,W-56,STG1,a=1.0,bar=VGOLD,r=26,dark=0.9); d=ImageDraw.Draw(im,'RGBA')
    kicker(d,96,STG0+26,'WHY IT HAPPENS · THE MECHANISM',VGOLD)
    molecule(d,250,1486,t,33.0)
    if t>34.4:
        a1=appear(t,34.4); txt(d,636,1392,'17AA',f(BEB,96),VGOLD,a1); txt(d,636,1486,'ORAL',f(BEB,96),CREAM,appear(t,35.2))
        txt(d,636,1588,'17-alpha-alkylated',f(DMR,30),MUT,a1)
    if t>37.3: tag(d,636,1632,'SURVIVES THE LIVER',CYAN,30,appear(t,37.3))
    if t>38.6: tag(d,636,1696,'STAYS ACTIVE',GREEN,28,appear(t,38.6))
    if t>36.0: txt(d,96,1792,'the armor that beats your liver is what makes it toxic',f(DMR,28),MUT,appear(t,36.0))
def sc_liver(im,d,t):   # liver load + enzyme bars ~40.0-53.4
    card(im,d,56,STG0,W-56,STG1,a=1.0,bar=RED,r=26,dark=0.9); d=ImageDraw.Draw(im,'RGBA')
    kicker(d,96,STG0+26,'MARKER 02 · LIVER ENZYMES',RED)
    lx,ly=130,1420
    pts=[(lx,ly+70),(lx+46,ly),(lx+170,ly-8),(lx+280,ly+34),(lx+258,ly+172),(lx+100,ly+196),(lx+22,ly+150)]
    frac=ease(clamp((t-41.0)/2.0))
    miny=min(p[1] for p in pts); maxy=max(p[1] for p in pts); fy=lerp(maxy,miny,frac)
    clip=Image.new('L',(W,H),0); ImageDraw.Draw(clip).polygon(pts,fill=255)
    lay=Image.new('RGBA',(W,H),(0,0,0,0)); ld=ImageDraw.Draw(lay,'RGBA')
    lit_bar(ld,lx-20,fy,lx+300,maxy, RED if frac>0.6 else AMBER)
    lay.putalpha(Image.composite(lay.split()[3],Image.new('L',(W,H),0),clip))
    im.alpha_composite(lay); d=ImageDraw.Draw(im,'RGBA')
    d.polygon(pts,outline=A(WHITE,1),width=4)
    if GL and frac>0.3: GL.polygon(pts,outline=A(RED,frac),width=5)
    txt(d,lx+60,ly-74,'TOXIC LOAD',f(MONO,26),CREAM,appear(t,41.0))
    txt(d,lx+70,maxy+14,f'{int(frac*100)}%',f(BEB,54),RED if frac>0.6 else AMBER,appear(t,41.4))
    if t>47.0:
        specs=[('ALT',0.86,RED,'H',47.1),('AST',0.74,RED,'H',47.5)]
        vbars(d,560,1716,specs,t,maxh=300,bw=130,gap=96)
    if t>50.3: tag(d,96,1792,'ELEVATED ENZYMES = THE MECHANISM',RED,30,appear(t,50.3))
def sc_lab(im,d,t):     # lab panel ~53.5-62.1
    lab_card(im,d,56,STG0,t,a=1.0)
    d=ImageDraw.Draw(im,'RGBA')
    if t>59.6: txt(d,W/2,STG1-42,'MOST NEVER RUN THIS PANEL',f(BEB,56),RED,appear(t,59.6),anchor='mm')
def sc_measure(im,d,t): # ring gauge ~65.8-71.7
    card(im,d,56,STG0,W-56,STG1,a=1.0,bar=VGOLD,r=26,dark=0.9); d=ImageDraw.Draw(im,'RGBA')
    kicker(d,96,STG0+26,'THE PART NOBODY POSTS',VGOLD)
    frac=ease(clamp((t-66.6)/2.0))
    ring_gauge(d,300,1570,128,frac,RED,'ORGAN DAMAGE', f'{int(frac*100)}%',warn=1)
    if t>68.2:
        txt(d,540,1440,'MEASURABLE',f(BEB,88),RED,appear(t,68.2))
        txt(d,540,1524,'& SILENT',f(BEB,88),CREAM,appear(t,69.0))
    if t>69.6: tag(d,540,1620,'GYM LIGHTING LIES',AMBER,28,appear(t,69.6))
    if t>70.6: tag(d,540,1684,'BLOODWORK DOESNT',GREEN,28,appear(t,70.6))
def sc_road(im,d,t):    # roadmap ~85.9-92.3
    card(im,d,56,STG0,W-56,STG1,a=1.0,bar=GREEN,r=26,dark=0.9); d=ImageDraw.Draw(im,'RGBA')
    kicker(d,96,STG0+26,'BLOODWORK IS THE ROADMAP',GREEN)
    roadmap(d,118,1430,t)
    if t>90.6: tag(d,118,1600,'THE COACH AGZ WAY',VGOLD,32,appear(t,90.6))
    if t>87.5: txt(d,118,1720,'you read it · you adjust · you get your look AND your health',f(DMR,28),MUT,appear(t,87.5))

SCENES=[(20.6,31.5,sc_crash),(31.8,39.8,sc_mol),(40.0,53.4,sc_liver),
        (53.5,62.1,sc_lab),(65.8,71.7,sc_measure),(85.9,92.3,sc_road)]
def active_scene(t):
    for s0,s1,fn in SCENES:
        if s0<=t<s1+0.2: return (s0,s1,fn)
    return None

# ---------------- CTA ----------------
LOGO=None
def cta(im,t):
    if t<98.6: return
    d=ImageDraw.Draw(im,'RGBA'); a=appear(t,98.7,0.25)
    y=1300; card(im,d,56,y,W-56,y+372,a,bar=VGOLD,r=28,dark=0.9); d=ImageDraw.Draw(im,'RGBA')
    global LOGO
    if LOGO is None:
        lg=Image.open(B+'logo.jpg').convert('RGB'); s=min(lg.size)
        lg=lg.crop(((lg.width-s)//2,(lg.height-s)//2,(lg.width+s)//2,(lg.height+s)//2)).resize((150,150),Image.LANCZOS)
        m=Image.new('L',(150,150),0); ImageDraw.Draw(m).ellipse([0,0,149,149],fill=255); lg.putalpha(m); LOGO=lg
    lg=LOGO.copy(); lg.putalpha(lg.split()[3].point(lambda v:int(v*a))); im.alpha_composite(lg,(96,y+40))
    d=ImageDraw.Draw(im,'RGBA')
    txt(d,270,y+44,'FREE · WINSTROL SAFETY',f(MONO,28),VGOLD,a)
    txt(d,270,y+82,'FRAMEWORK & PROTOCOL',f(MONO,28),CREAM,a)
    if t>=99.9:
        b=ease(appear(t,99.9,0.18)); fn=f(BEB,96)
        label='COMMENT  "WIN"'; tw=d.textlength(label,font=fn)
        bx=(W-tw-48)/2
        lit_bar(d,bx,y+180,bx+tw+48,y+300,VGOLD,b); txt(d,bx+24,y+188,label,fn,INK,b)
        if GL: GL.rounded_rectangle([bx-3,y+177,bx+tw+51,y+303],radius=6,outline=A(VGOLD,b),width=10)

# ---------------- captions ----------------
CORR={'alkalated':'ALKYLATED','antibiotics':'ANABOLICS','bloodworks':'BLOODWORK',
 "ag's":'AGZ','winstrel':'WINSTROL',"i":'I',"i'm":"I'M","i'll":"I'LL"}
def norm(w):
    raw=w.strip().lstrip('-')
    key=raw.lower().strip('.,?!-')
    base=CORR.get(key,raw)
    return base.upper().rstrip('.,')
def build_groups():
    G=[];cur=[]
    for i,x in enumerate(WORDS):
        if cur:
            prev=WORDS[cur[-1]]
            if len(cur)>=3 or x['s']-prev['e']>0.42 or prev['w'][-1] in '.?!': G.append(cur);cur=[]
        cur.append(i)
    if cur:G.append(cur)
    return G
GROUPS=build_groups()
# accent map: color a key word when spoken
ACCENT={'WINSTROL':VGOLD,'HDL':RED,'CRASHES':RED,'COLLAPSE':RED,'DEFENSELESS':RED,'TORCHED':RED,
 'HEPATOTOXIC':RED,'POISON':RED,'LIVER':AMBER,'ENZYME':RED,'MECHANISM':VGOLD,'DAMAGE':RED,
 'MEASURABLE':RED,'BLOODWORK':CYAN,'BLOODWORKS':CYAN,'ROADMAP':GREEN,'WIN':VGOLD,'LABS':CYAN,
 'DESTROYS':RED,'LIPIDS':VGOLD,'CMP':VGOLD,'OPTIMIZE':GREEN,'ENHANCED':VGOLD,'ORAL':AMBER}
CAP_Y=1110
def group_at(t):
    lo=None
    for g in GROUPS:
        if WORDS[g[0]]['s']<=t+1e-6: lo=g
        else: break
    if lo is None: return None
    if t>WORDS[lo[-1]]['e']+0.55: return None
    return lo
def captions(im,t):
    g=group_at(t)
    if not g: return
    d=ImageDraw.Draw(im,'RGBA')
    ws=[norm(WORDS[i]['w']) for i in g]
    size=118
    while True:
        fn=f(BEB,size); sp=d.textlength(' ',font=fn)+16; wd=[d.textlength(w,font=fn) for w in ws]; tot=sum(wd)+sp*(len(ws)-1)
        if tot<=940 or size<60: break
        size-=4
    xs=[];x=(W-tot)/2
    for w_ in wd: xs.append(x);x+=w_+sp
    act=0
    for k,i in enumerate(g):
        if WORDS[i]['s']<=t: act=k
    g0=WORDS[g[0]]['s']; s=lerp(0.92,1,expo((t-g0)/0.09))
    cap=Image.new('RGBA',(W,300),(0,0,0,0)); cd=ImageDraw.Draw(cap)
    shd=Image.new('RGBA',(W,300),(0,0,0,0)); sd=ImageDraw.Draw(shd)
    aw=norm(WORDS[g[act]]['w']); acol=ACCENT.get(aw,RED)
    prev=max(0,act-1); bt=expo((t-WORDS[g[act]]['s'])/0.07) if act>0 else 1
    bx0=lerp(xs[prev],xs[act],bt)-20; bx1=lerp(xs[prev]+wd[prev],xs[act]+wd[act],bt)+20
    for k,(w_,x_) in enumerate(zip(ws,xs)):
        if k!=act: sd.text((x_+4,48),w_,font=fn,fill=(0,0,0,220))
    cap.alpha_composite(shd.filter(ImageFilter.GaussianBlur(6)))
    lit_bar(cd,bx0,42+size*0.02,bx1,42+size*0.99,acol)
    for k,(w_,x_) in enumerate(zip(ws,xs)):
        cd.text((x_,42),w_,font=fn,fill=A(CREAM if k==act else CREAM,1),stroke_width=0 if k==act else 3,stroke_fill=(0,0,0,255))
    if abs(s-1)>0.002:
        cap=cap.resize((int(W*s),int(300*s)),Image.BICUBIC); ox=int((W-cap.width)/2); oy=int(CAP_Y-42-(cap.height-300)/2)
    else: ox,oy=0,CAP_Y-42
    im.alpha_composite(cap,(ox,oy))

# ---------------- person cutout (depth: head over graphics) ----------------
def person_mask(n):
    si=SRCMAP[n]
    m=np.asarray(MASKS[si])  # 480x270
    im=Image.fromarray(m,'L').resize((W,H),Image.BILINEAR).filter(ImageFilter.GaussianBlur(2))
    return im

# ---------------- frame ----------------
def frame(src,n):
    t=n/FPS
    base=src.convert('RGB')
    im=base.convert('RGBA')
    sc=active_scene(t)
    graphic_on = sc is not None or t>=98.6
    # vignette scrim to seat graphics (kept off the face area lightly)
    global GL
    glow=Image.new('RGBA',(W,H),(0,0,0,0)); GL=ImageDraw.Draw(glow,'RGBA')
    gl=Image.new('RGBA',(W,H),(0,0,0,0)); d=ImageDraw.Draw(gl,'RGBA')
    # top + bottom gradient scrims for text legibility (applied to im directly, subtle)
    sc_arr=np.zeros((H,),np.float32)
    yy=np.arange(H)
    sc_arr=np.where(yy>1300,np.clip((yy-1300)/300,0,1)*150,0)
    sc_arr=np.maximum(sc_arr,np.where(yy<470,(1-yy/470)*120,0))
    scrim=Image.merge('RGBA',[Image.new('L',(W,H),c) for c in DEEP]+[Image.fromarray(np.repeat((sc_arr).astype(np.uint8)[:,None],W,1))])
    im.alpha_composite(scrim)
    # HUD + scenes draw into gl (behind head)
    hud(im,ImageDraw.Draw(im,'RGBA'),t)  # chips are above head region, ok on top
    if sc:
        s0,s1,fn=sc; pin=ease(clamp((t-s0)/0.22)); pout=clamp((t-s1)/0.2)
        # draw scene onto im (frosted cards need im); then re-cover with head
        fn(im,ImageDraw.Draw(im,'RGBA'),t)
    cta(im,t)
    # composite glow (screen blend) at quarter res
    if glow.getbbox():
        sm=glow.resize((W//4,H//4),Image.BILINEAR)
        g1=np.asarray(sm.filter(ImageFilter.GaussianBlur(3.2))).astype(np.float32)/255
        g2=np.asarray(sm.filter(ImageFilter.GaussianBlur(9))).astype(np.float32)/255
        prem=np.clip(g1[...,:3]*g1[...,3:]*2.1+g2[...,:3]*g2[...,3:]*1.6,0,1)
        prem=np.asarray(Image.fromarray((prem*255).astype(np.uint8)).resize((W,H),Image.BILINEAR)).astype(np.float32)/255
        b=np.asarray(im.convert('RGB')).astype(np.float32)/255
        im=Image.fromarray(((1-(1-b)*(1-prem))*255).astype(np.uint8)).convert('RGBA')
    # gold edge rule + watermark (always)
    d=ImageDraw.Draw(im,'RGBA'); d.rectangle([0,0,7,H],fill=GOLD+(255,))
    # small persistent topic band after hook (brand anchor, upper-left, clear of face)
    if 5.8<t<98.4:
        a=clamp((t-5.8)/0.3)*(1-clamp((t-97.8)/0.5))
        fn=f(BEB,46); t1='WINSTROL'; t2=' · BIOMARKERS'
        bw=78+d.textlength(t1,font=fn)+d.textlength(t2,font=fn)+24
        d.rounded_rectangle([40,250,40+bw,314],radius=10,fill=A((9,12,19),0.78*a),outline=A(GOLD,0.5*a))
        d.rounded_rectangle([40,250,50,314],radius=4,fill=A(VGOLD,a))
        txt(d,70,258,t1,fn,VGOLD,a); txt(d,70+d.textlength(t1,font=fn),258,t2,fn,CREAM,a)
    txt(d,W-40,1872,'@coach.agz',f(MONO,26),GOLD,0.92,anchor='ra')
    txt(d,40,1880,'FOR RESEARCH & EDUCATIONAL PURPOSES ONLY',f(MONO,16),MUT,0.78)
    captions(im,t)
    GL=None
    return im.convert('RGB')

if __name__=='__main__':
    mode=sys.argv[1]
    if mode=='stills':
        import os; os.makedirs(B+'qc',exist_ok=True)
        for ts in [float(x) for x in sys.argv[2:]]:
            n=int(round(ts*FPS))
            subprocess.run(['ffmpeg','-v','error','-y','-ss',f'{n/FPS:.4f}','-i',B+'assembled_v.mp4','-frames:v','1',B+'qc/_s.png'])
            frame(Image.open(B+'qc/_s.png'),n).save(B+f'qc/win_{ts:.1f}.jpg',quality=88)
        sys.exit()
    n0,n1,out=int(sys.argv[2]),int(sys.argv[3]),sys.argv[4]
    dec=subprocess.Popen(['ffmpeg','-v','error','-ss',f'{n0/FPS:.4f}','-i',B+'assembled_v.mp4','-frames:v',str(n1-n0),'-f','rawvideo','-pix_fmt','rgb24','-'],stdout=subprocess.PIPE)
    enc=subprocess.Popen(['ffmpeg','-v','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-','-an','-c:v','libx264','-crf','17','-preset','medium','-pix_fmt','yuv420p',out],stdin=subprocess.PIPE)
    for n in range(n0,n1):
        buf=dec.stdout.read(W*H*3)
        if len(buf)<W*H*3: break
        enc.stdin.write(frame(Image.frombuffer('RGB',(W,H),buf),n).tobytes())
    enc.stdin.close();enc.wait();dec.kill();print('done',n0,n1)
