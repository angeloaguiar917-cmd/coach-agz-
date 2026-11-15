import json, subprocess, sys, math, os
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops
B=os.path.dirname(os.path.abspath(__file__)); F=os.path.join(B,'..','fonts')+'/'
W,H=1080,1920; FPS=30
WORDS=json.load(open(B+'/words_final.json'))
KEEP=json.load(open(B+'/keep.json'))
BOUNDS=[];_t=0
for a,b in KEEP: BOUNDS.append((_t,_t+b-a)); _t+=b-a
DUR=_t
GOLD=(201,169,110); CREAM=(244,241,234); NAVY=(14,17,23); MUTED=(184,184,188)
RED=(255,34,28); VGOLD=(255,194,26); CYAN=(0,229,255); GREEN=(30,255,110); DEEP=(2,3,8); INK=(6,8,14); WHITE=(255,255,255)
AMBER=(255,140,20); COARED=(210,10,20); PAPER=(236,233,226)
BEB='BebasNeue-Regular.ttf'; BAR='BarlowCondensed-Bold.ttf'; BARS='BarlowCondensed-SemiBold.ttf'
_fc={}
def f(n,s,var=None):
    k=(n,int(s),var)
    if k not in _fc:
        if n=='MONO': fo=ImageFont.truetype(F+'JBMono.ttf',int(s)); fo.set_variation_by_name(var or 'Bold')
        elif n=='DM': fo=ImageFont.truetype(F+'DMSans.ttf',int(s)); fo.set_variation_by_name(var or 'Bold')
        else: fo=ImageFont.truetype(F+n,int(s))
        _fc[k]=fo
    return _fc[k]
def clamp(x,a=0,b=1): return max(a,min(b,x))
def expo(x): x=clamp(x); return 1 if x>=1 else 1-2**(-10*x)
def ease_io(x): x=clamp(x); return 4*x**3 if x<.5 else 1-(-2*x+2)**3/2
def back(x):  # firm settle, tiny overshoot (heavy objects only)
    x=clamp(x); c=1.2; return 1+(c+1)*(x-1)**3+c*(x-1)**2
def lerp(a,b,t): return a+(b-a)*t
def A(c,a): return tuple(c[:3])+(int(clamp(a)*255),)
def ap(t,t0,d=0.16): return expo((t-t0)/d)
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
def tag(d,x,y,label,col=RED,size=30,a=1.0,glow=True,fg=None):
    if a<=0: return x
    fn=f('MONO',size); tw=d.textlength(label,font=fn); h=size+16
    lit_bar(d,x,y,x+tw+24,y+h,col,a); d.text((x+12,y+6),label,font=fn,fill=A(fg or (INK if col in (VGOLD,GREEN,CYAN,GOLD) else WHITE),a))
    if GL and glow: GL.rectangle([x-4,y-4,x+tw+28,y+h+4],outline=A(col,a),width=8)
    return x+tw+24
def txt(d,x,y,s,font,col,a=1.0,anchor=None):
    if a<=0: return
    d.text((x,y),s,font=font,fill=A(col,a),anchor=anchor)
def check(d,x,y,col,s=1.0,a=1.0,w=6):
    d.line([(x,y),(x+10*s,y+11*s),(x+28*s,y-12*s)],fill=A(col,a),width=w,joint='curve')
    if GL: GL.line([(x,y),(x+10*s,y+11*s),(x+28*s,y-12*s)],fill=A(col,a),width=w+6)
def cross(d,x,y,col,s=1.0,a=1.0,w=7):
    d.line([(x-12*s,y-12*s),(x+12*s,y+12*s)],fill=A(col,a),width=w); d.line([(x-12*s,y+12*s),(x+12*s,y-12*s)],fill=A(col,a),width=w)
    if GL: GL.line([(x-12*s,y-12*s),(x+12*s,y+12*s)],fill=A(col,a),width=w+6); GL.line([(x-12*s,y+12*s),(x+12*s,y-12*s)],fill=A(col,a),width=w+6)
def gline(d,pts,col,w=4,a=1.0,glow=True):
    d.line(pts,fill=A(col,a),width=w,joint='curve')
    if GL and glow: GL.line(pts,fill=A(col,a),width=w+8,joint='curve')
def kicker(d,x,y,label,t,t0,col=VGOLD,size=26):
    p=ap(t,t0,0.18);
    if p<=0: return
    d.line([(x,y+size//2+2),(x+lerp(0,44,p),y+size//2+2)],fill=A(col,1),width=4)
    if p>0.4:
        fn=f('MONO',size); n=int(len(label)*clamp((t-t0-0.06)/0.22))
        d.text((x+58,y),label[:max(1,n)],font=fn,fill=A(col,1))
def panel(im,box,a=1.0,dark=0.88,blur=12,frame=VGOLD,r=26):
    x0,y0,x1,y1=[int(v) for v in box]
    if x1<=x0+2 or y1<=y0+2 or a<=0: return
    reg=im.crop((x0,y0,x1,y1)).convert('RGB').filter(ImageFilter.GaussianBlur(blur))
    reg=Image.blend(reg,Image.new('RGB',reg.size,DEEP),dark)
    m=Image.new('L',reg.size,0); ImageDraw.Draw(m).rounded_rectangle([0,0,reg.width-1,reg.height-1],r,fill=int(255*a))
    im.paste(reg,(x0,y0),m)
    d=ImageDraw.Draw(im,'RGBA')
    d.rounded_rectangle([x0,y0,x1,y1],r,outline=A(frame,0.55*a),width=2)
    d.rounded_rectangle([x0,y0+r,x0+6,y1-r],2,fill=A(RED,a))   # crimson edge bar leads
    if GL: GL.rounded_rectangle([x0,y0,x1,y1],r,outline=A(frame,0.35*a),width=5); GL.rectangle([x0-2,y0+r,x0+8,y1-r],fill=A(RED,a))
def ring(d,cx,cy,r,frac,col,w=18,a=1.0):
    d.ellipse([cx-r,cy-r,cx+r,cy+r],outline=A((40,44,56),a),width=w)
    if frac>0:
        d.arc([cx-r,cy-r,cx+r,cy+r],-90,-90+360*frac,fill=A(col,a),width=w)
        if GL: GL.arc([cx-r,cy-r,cx+r,cy+r],-90,-90+360*frac,fill=A(col,a),width=w+10)
def dashed(d,x0,y,x1,col,w=3,dash=16,gap=10,a=1.0):
    x=x0
    while x<x1: d.line([(x,y),(min(x+dash,x1),y)],fill=A(col,a),width=w); x+=dash+gap
def pulse_dots(d,pts,t,col,speed=0.8,n=4,r=6):
    # small dots travelling along a polyline
    segs=[(pts[i],pts[i+1]) for i in range(len(pts)-1)]; L=[math.dist(a,b) for a,b in segs]; T=sum(L)
    for k in range(n):
        u=((t*speed+k/n)%1)*T
        for (a,b),l in zip(segs,L):
            if u<=l:
                x=a[0]+(b[0]-a[0])*u/l; y=a[1]+(b[1]-a[1])*u/l
                d.ellipse([x-r,y-r,x+r,y+r],fill=A(col,1))
                if GL: GL.ellipse([x-r-6,y-r-6,x+r+6,y+r+6],fill=A(col,1))
                break
            u-=l
# ---------------- layouts (footage transform) ----------------
# source anchor (face centre) maps to (cx,cy) at scale s; mask = rounded rect (x0,y0,x1,y1,r)
AX,AY=565,950
def L_full(z=1.0): return (z,540+25*z,672+278*z,(0,0,W,H,0))
LAY={
 'TOPBAND':  None,  # = full
 'CHEST':    (1.0,565,780,(0,0,W,H-170,0)),
 'SIDE_R':   (0.80,700,900,(248,140,W,1676,40)),
 'SIDE_L':   (0.80,380,900,(0,140,792,1676,40)),
 'SPLIT':    (0.78,540,610,(99,220,941,960,34)),
 'PIP_TR':   (0.46,795,560,(560,240,1030,820,30)),
 'PIP_TL':   (0.46,285,560,(50,240,520,820,30)),
 'BUBBLE':   (0.40,225,420,(60,255,390,585,165)),
}
def lay_lerp(a,b,p):
    return (lerp(a[0],b[0],p),lerp(a[1],b[1],p),lerp(a[2],b[2],p),tuple(lerp(x,y,p) for x,y in zip(a[3],b[3])))
# ---------------- scenes ----------------
def sc_gauge(im,d,t):  # S1 radial gauge, top band
    T0=14.9; x0,y0,x1,y1=60,250,1020,480
    cx,cy=200,365; v=expo((t-15.35)/0.85)
    ring(d,cx,cy,88,v,RED,20)
    fn=f(BEB,74); txt(d,cx,cy+4,f'{int(round(v*100))}%',fn,CREAM,1,'mm')
    txt(d,cx,cy+66,'RESPONSE',f('MONO',18),MUTED,1,'mm')
    kicker(d,330,285,'PROLACTIN · LACTATION RESPONSE',t,T0+0.15,VGOLD,24)
    p=ap(t,15.58,0.2)
    if p>0: txt(d,330,330,'MALE BREAST TISSUE',f(BEB,int(66)),CREAM,p)
    if t>=16.16:
        b=expo((t-16.16)/0.12); xx=tag(d,330,410,'STATUS: ACTIVE',RED,28,b)
        txt(d,xx+18,416,'· output confirmed',f('DM',26,'Medium'),MUTED,b)
def sc_circuit(im,d,t):  # S2 wiring schematic, chest band
    T0=17.3
    kicker(d,100,1212,'SIGNAL PATH',t,T0+0.1,VGOLD,22)
    chips=[('TREN',17.48,1262,RED),('NPP',18.02,1382,VGOLD)]
    node=(640,1270,990,1440)
    for lab,tt,y,col in chips:
        p=ap(t,tt,0.14)
        if p<=0: continue
        xo=lerp(-30,0,p)
        d.rounded_rectangle([100+xo,y,300+xo,y+66],12,fill=A((40,8,10) if col==RED else (40,30,4),p),outline=A(col,p),width=3)
        txt(d,200+xo,y+35,lab,f(BEB,52),col,p,'mm')
        if GL: GL.rounded_rectangle([100+xo,y,300+xo,y+66],12,outline=A(col,p),width=8)
        w=expo((t-tt-0.15)/0.45)
        pts=[(300,y+33),(470,y+33),(470,1355),(640,1355)]
        # draw progressively
        tot=sum(math.dist(pts[i],pts[i+1]) for i in range(3)); u=w*tot; drawn=[pts[0]]
        for i in range(3):
            l=math.dist(pts[i],pts[i+1])
            if u>=l: drawn.append(pts[i+1]); u-=l
            else:
                a,b=pts[i],pts[i+1]; drawn.append((a[0]+(b[0]-a[0])*u/l,a[1]+(b[1]-a[1])*u/l)); break
        if len(drawn)>1: gline(d,drawn,(90,110,130),4,p,False)
        if w>=1: gline(d,pts,CYAN,3,0.9); pulse_dots(d,pts,t,CYAN,0.9,3,6)
    p=ap(t,18.76,0.2)
    if p>0:
        x0,y0,x1,y1=node
        d.rounded_rectangle([x0,y0,x1,y1],18,fill=A((8,14,22),0.95*p),outline=A(CYAN,p),width=3)
        if GL: GL.rounded_rectangle([x0,y0,x1,y1],18,outline=A(CYAN,p),width=10)
        txt(d,x0+28,y0+20,'CHEST TISSUE',f(BEB,50),CREAM,p)
        txt(d,x0+28,y0+76,'RECEPTOR SITES',f('MONO',20),MUTED,p)
        for k in range(7):
            on=t>18.94+0.08*k; c=CYAN if on else (60,70,80)
            x=x0+40+k*44; d.ellipse([x-9,y0+128,x+9,y0+146],fill=A(c,p))
            if on and GL: GL.ellipse([x-14,y0+123,x+14,y0+151],fill=A(c,p))
    if t>=19.94:
        b=expo((t-19.94)/0.12); tag(d,700,1206,'SAME WIRING',VGOLD,26,b)
def sc_severity(im,d,t):  # S3 vertical severity meter, left column
    T0=20.95; x=60
    kicker(d,x,272,'SEVERITY',t,T0+0.1,VGOLD,26)
    top,bot=360,1430; bx0,bx1=x+10,x+46
    gp=expo((t-T0-0.1)/0.5); yb=lerp(bot,top,gp)
    d.rounded_rectangle([bx0,top,bx1,bot],18,fill=A((24,26,34),1),outline=A((70,70,80),1),width=2)
    # gradient fill amber -> red
    for yy in range(int(yb),bot,3):
        k=(bot-yy)/(bot-top); c=tuple(int(lerp(a_,b_,k)) for a_,b_ in zip(AMBER,RED))
        d.line([(bx0+5,yy),(bx1-5,yy)],fill=c+(255,),width=3)
    if GL and gp>0: GL.rounded_rectangle([bx0,yb,bx1,bot],18,outline=A(RED,0.8),width=8)
    rungs=[(420,'LACTATION','LEVEL 3 · EXTREME',21.18,RED),(820,'GYNO','LEVEL 2 · WON\'T SHRINK',26.68,AMBER),(1210,'LIBIDO','LEVEL 1 · OFFLINE',30.06,VGOLD)]
    mk=None
    for y,name,sub,tt,col in rungs:
        p=ap(t,tt,0.16)
        d.line([(bx1+4,y),(bx1+24,y)],fill=A(WHITE,0.6),width=3)
        if p<=0: continue
        xo=lerp(20,0,p)
        txt(d,x+86+xo,y-44,name,f(BEB,70),CREAM,p)
        txt(d,x+88+xo,y+26,sub,f('MONO',19),col,p)
        mk=(y,col,tt)
    if mk:
        # marker arrow slides to newest rung
        prev=[r for r in rungs if r[3]<mk[2]]
        y_prev=prev[-1][0] if prev else bot
        my=lerp(y_prev,mk[0],expo((t-mk[2])/0.35))
        d.polygon([(bx0-6,my),(bx0-30,my-16),(bx0-30,my+16)],fill=A(WHITE,1))
        if GL: GL.polygon([(bx0-6,my),(bx0-30,my-16),(bx0-30,my+16)],fill=A(WHITE,1))
    if t>=22.16:  # "extreme" flare on top rung
        b=expo((t-22.16)/0.12); brackets(d,x+70,370,x+330,480,A(RED,b),22,5)
        if GL: brackets(GL,x+70,370,x+330,480,A(RED,b),22,10)
    if t>=28.36:
        b=expo((t-28.36)/0.12); tag(d,x+86,858,'PERMANENT',AMBER,20,b)
    if t>=32.06:  # libido flatline
        b=expo((t-32.06)/0.3); y=1300
        pts=[(x+86,y),(x+150,y),(x+168,y-30),(x+186,y+20),(x+204,y),(lerp(x+204,x+330,b),y)]
        gline(d,pts,VGOLD,4,1)
    if t>=32.9:
        b=expo((t-32.9)/0.14); xx=tag(d,x+86,1340,'TOTAL T ↑',GOLD,20,b)
def sc_stack(im,d,t):  # S4 build stack under framed footage
    T0=33.7; X0,X1=70,1010
    kicker(d,X0,1100,'WHAT BUILDS THE TISSUE',t,T0+0.15,VGOLD,24)
    rows=[(1150,'ESTROGEN','DUCTS',37.62,39.22,CYAN),(1270,'PROGESTIN','GLAND',40.2,45.22,VGOLD),(1390,'PROLACTIN','SWITCH',46.46,47.34,RED)]
    for y,name,res,t1,t2,col in rows:
        p=ap(t,t1,0.16)
        if p<=0: continue
        yo=lerp(18,0,p)
        d.rounded_rectangle([X0,y+yo,X1,y+104+yo],16,fill=A((10,12,18),0.92*p),outline=A((70,66,58),p),width=2)
        d.rectangle([X0,y+yo+14,X0+6,y+90+yo],fill=A(col,p))
        txt(d,X0+30,y+18+yo,name,f(BEB,64),col,p)
        nw=d.textlength(name,font=f(BEB,64))
        # arrow
        q=expo((t-t1-0.12)/0.3); ax0=X0+60+nw; ax1=X0+60+nw+lerp(0,120,q)
        if q>0: gline(d,[(ax0,y+54+yo),(ax1,y+54+yo)],WHITE,4,p,False); d.polygon([(ax1+14,y+54+yo),(ax1,y+44+yo),(ax1,y+64+yo)],fill=A(WHITE,p*q))
        r=ap(t,t2,0.16); rx=ax0+150
        if r>0:
            txt(d,rx,y+18+yo,res,f(BEB,64),CREAM,r)
            iw=d.textlength(res,font=f(BEB,64)); ix=rx+iw+30
            if res=='DUCTS':  # branching ducts icon
                g=expo((t-t2)/0.5)
                br=[((ix,y+52),(ix+40,y+52)),((ix+40,y+52),(ix+80,y+26)),((ix+40,y+52),(ix+80,y+78)),((ix+80,y+26),(ix+120,y+14)),((ix+80,y+26),(ix+120,y+38)),((ix+80,y+78),(ix+120,y+66)),((ix+80,y+78),(ix+120,y+90))]
                for k,(a_,b_) in enumerate(br[:max(1,int(g*len(br)))]): gline(d,[(a_[0],a_[1]+yo),(b_[0],b_[1]+yo)],CYAN,4,r)
            elif res=='GLAND':
                for k,(dx,dy) in enumerate([(0,0),(34,-18),(34,18),(68,0),(68,-36),(68,36),(102,-18),(102,18)]):
                    on=expo((t-t2-0.05*k)/0.12); cx,cy=ix+20+dx,y+52+dy+yo
                    d.ellipse([cx-15,cy-15,cx+15,cy+15],outline=A(VGOLD,r),width=3,fill=A(VGOLD,0.85*on))
                    if GL and on>0: GL.ellipse([cx-18,cy-18,cx+18,cy+18],fill=A(VGOLD,on))
            elif res=='SWITCH':
                on=t>=48.7; sx=ix; sy=y+30+yo
                d.rounded_rectangle([sx,sy,sx+110,sy+48],24,fill=A(RED if on else (50,50,60),r))
                kx=sx+86 if on else sx+24; kx=lerp(sx+24,sx+86,expo((t-48.7)/0.14)) if t>=48.7 else sx+24
                d.ellipse([kx-20,sy+4,kx+20,sy+44],fill=A(WHITE,r))
                if on and GL: GL.rounded_rectangle([sx,sy,sx+110,sy+48],24,outline=A(RED,1),width=10)
                if on: txt(d,sx+130,sy+6,'GROW + PRODUCE',f('MONO',22),RED,expo((t-48.7)/0.2))
        if name=='PROGESTIN':
            txt(d,X0+32+nw+0,y+12+yo,'',f('MONO',18),MUTED,p)
            for k,(c,tt) in enumerate([('TREN',42.24),('NPP',42.88),('DECA',43.54)]):
                b=ap(t,tt,0.12)
                if b>0 and t<t2+0.01:
                    tag(d,rx+k*128,y+30+yo,c,RED,24,b,glow=True)
            if t>=41.4 and t<t2: txt(d,X0+30,y+80+yo,'19-NOR',f('MONO',18),MUTED,ap(t,41.4))
    # opening: prolactin is NOT the builder (flag sits where row 3 will land)
    if 34.9<=t<37.4:
        p=ap(t,34.9,0.16)*(1-clamp((t-37.1)/0.3)); y=1150
        d.rounded_rectangle([X0,y,X1,y+104],16,fill=A((22,6,8),0.92*p),outline=A(RED,p),width=3)
        txt(d,X0+30,y+18,'PROLACTIN',f(BEB,64),RED,p)
        txt(d,X0+330,y+30,'BUILDS TISSUE?',f('MONO',30),CREAM,p)
        if t>=35.7: cross(d,X0+690,y+52,RED,1.6,ap(t,35.7,0.1),9); tag(d,X0+730,y+30,'NO',RED,30,ap(t,35.7,0.1))
def sc_switch(im,d,t):  # S5 big lever switch, face-cam bubble
    T0=49.9
    kicker(d,430,300,'GLAND STATUS',t,T0+0.15,VGOLD,26)
    p=ap(t,52.46,0.16)
    if p>0:
        txt(d,430,350,'TISSUE',f(BEB,96),CREAM,p)
    if t>=53.36:
        b=expo((t-53.36)/0.10); s=lerp(1.3,1.0,b)
        fn=f(BEB,int(64*s)); lab='ALREADY BUILT'; tw=d.textlength(lab,font=fn)
        d.rectangle([430,462,430+tw+30,462+int(74*s)],outline=A(VGOLD,b),width=5); txt(d,445,466,lab,fn,VGOLD,b)
        if GL: GL.rectangle([430,462,430+tw+30,462+int(74*s)],outline=A(VGOLD,b),width=12)
    # housing
    hx0,hy0,hx1,hy1=330,650,750,1280
    p=ap(t,T0+0.2,0.25)
    if p<=0: return
    yo=lerp(40,0,p)
    d.rounded_rectangle([hx0,hy0+yo,hx1,hy1+yo],34,fill=A((14,16,22),p),outline=A((90,90,100),p),width=3)
    for (sx,sy) in [(hx0+26,hy0+26),(hx1-26,hy0+26),(hx0+26,hy1-26),(hx1-26,hy1-26)]:
        d.ellipse([sx-8,sy-8+yo,sx+8,sy+8+yo],fill=A((70,70,80),p))
    txt(d,(hx0+hx1)/2,hy0+54+yo,'PROLACTIN',f('MONO',30),CREAM,p,'mm')
    on=clamp((t-55.72)/0.16); onb=expo(on)
    # labels
    txt(d,(hx0+hx1)/2,hy0+130+yo,'ON',f(BEB,70),RED if on>=1 else (90,90,96),p,'mm')
    txt(d,(hx0+hx1)/2,hy1-70+yo,'OFF',f(BEB,70),(90,90,96) if on>=1 else CREAM,p,'mm')
    if on>=1 and GL: GL.text(((hx0+hx1)/2,hy0+130+yo),'ON',font=f(BEB,70),fill=A(RED,1),anchor='mm')
    # slot + lever
    cx=(hx0+hx1)/2; s0,s1=hy0+200,hy1-140
    d.rounded_rectangle([cx-22,s0+yo,cx+22,s1+yo],22,fill=A((4,4,6),p))
    ky=lerp(s1-40,s0+40,onb)+yo
    if 0<on<1: ky+=0
    d.rounded_rectangle([cx-110,ky-44,cx+110,ky+44],22,fill=A(RED if on>=1 else (120,120,128),p))
    lit=RED if on>=1 else (120,120,128)
    if on>=1:
        lit_bar(d,cx-110,ky-44,cx+110,ky+44,RED,p)
        if GL: GL.rounded_rectangle([cx-118,ky-52,cx+118,ky+52],26,outline=A(RED,1),width=14)
    d.line([(cx-80,ky),(cx+80,ky)],fill=A(WHITE,0.5*p),width=3)
    # output readout to the right
    if on>=1:
        b=expo((t-55.85)/0.2)
        for k in range(3):
            yy=760+k*60; xx=790
            d.ellipse([xx+30*k-10,yy-14+lerp(-10,0,b),xx+30*k+10,yy+14],fill=A(CYAN,b))
            if GL: GL.ellipse([xx+30*k-16,yy-20,xx+30*k+16,yy+20],fill=A(CYAN,b))
        tag(d,780,960,'OUTPUT ON',RED,24,b)
def sc_scope(im,d,t):  # S6 oscilloscope, top band
    T0=58.6; x0,x1,yc=330,990,370
    kicker(d,90,268,'SAME SWITCH · 2ND TARGET',t,T0+0.1,VGOLD,22)
    p=ap(t,T0+0.2,0.25)
    txt(d,90,312,'DOPAMINE',f(BEB,72),CYAN if t<61.56 else RED,ap(t,T0+0.25))
    txt(d,90,390,'SIGNAL',f('MONO',22),MUTED,ap(t,T0+0.3))
    # scope window
    d.rectangle([x0,300,x1,450],fill=A((4,10,14),0.9*p),outline=A((40,80,90),p),width=2)
    for gx in range(x0,x1,66): d.line([(gx,302),(gx,448)],fill=A((20,50,60),p),width=1)
    d.line([(x0,yc),(x1,yc)],fill=A((30,70,80),p),width=1)
    sup=expo((t-61.56)/0.8)
    amp=lerp(52,6,sup); col=tuple(int(lerp(a_,b_,sup)) for a_,b_ in zip(CYAN,RED))
    pts=[]
    for x in range(x0,int(lerp(x0,x1,expo((t-T0-0.2)/0.6))),4):
        ph=(x-x0)/60+t*5; y=yc+amp*math.sin(ph)*(0.6+0.4*math.sin(ph*0.37))
        pts.append((x,y))
    if len(pts)>1: gline(d,pts,col,4,p)
    if t>=61.56: tag(d,x0+12,312,'SUPPRESSED',RED,22,expo((t-61.56)/0.12))
    for lab,tt,xx in [('MINDSET',64.82,640),('MOTIVATION',65.62,820)]:
        if t>=tt: tag(d,xx,410,lab,VGOLD,20,expo((t-tt)/0.12))
def sc_leash(im,d,t):  # S7 tether, chest band
    T0=66.4; y=1340
    kicker(d,100,1212,'NORMAL CONTROL',t,T0+0.05,VGOLD,22)
    a=ap(t,66.64,0.16); b=ap(t,67.98,0.16)
    if a>0:
        d.rounded_rectangle([100,y-60,400,y+60],60,fill=A((4,20,26),a),outline=A(CYAN,a),width=4)
        txt(d,250,y,'DOPAMINE',f(BEB,58),CYAN,a,'mm')
        if GL: GL.rounded_rectangle([100,y-60,400,y+60],60,outline=A(CYAN,a),width=10)
    if b>0:
        jit=0 if t>=69.1 else 10*math.sin(t*23)*(1-clamp((t-68.6)/0.5))
        px0=660+jit
        d.rounded_rectangle([px0,y-60,px0+320,y+60],60,fill=A((26,4,6),b),outline=A(RED,b),width=4)
        txt(d,px0+160,y,'PROLACTIN',f(BEB,58),RED,b,'mm')
        if GL: GL.rounded_rectangle([px0,y-60,px0+320,y+60],60,outline=A(RED,b),width=10)
        # chain links
        taut=expo((t-69.1)/0.15); n=9
        for k in range(n):
            u=(k+0.5)/n; x=lerp(400,px0,u); sag=(1-taut)*28*math.sin(math.pi*u)
            col=VGOLD if t>=69.1 else (150,150,160)
            if k%2==0: d.ellipse([x-18,y-10+sag,x+18,y+10+sag],outline=A(col,b),width=4)
            else: d.ellipse([x-10,y-16+sag,x+10,y+16+sag],outline=A(col,b),width=4)
            if t>=69.1 and GL: GL.ellipse([x-18,y-14+sag,x+18,y+14+sag],outline=A(VGOLD,1),width=8)
    if t>=69.1: tag(d,580,1212,'HELD IN CHECK',VGOLD,22,expo((t-69.1)/0.12))
def chart_axes(d,x0,y0,x1,y1,p):
    d.line([(x0,y0),(x0,y1),(x1,y1)],fill=A(WHITE,0.85*p),width=3)
    for k in range(1,4):
        yy=lerp(y1,y0,k/4); d.line([(x0+4,yy),(x1,yy)],fill=A((60,64,74),0.6*p),width=1)
def sc_linegraph(im,d,t):  # S8 line graph, PiP top-right
    T0=69.5; X0,Y0,X1,Y1=110,900,1010,1290
    kicker(d,60,262,'WHEN PROLACTIN RUNS HIGH',t,T0+0.1,VGOLD,20)
    leg=[('PROLACTIN',RED,69.66),('LH',CYAN,72.2),('LIBIDO',VGOLD,73.58)]
    for k,(lab,col,tt) in enumerate(leg):
        a=ap(t,tt,0.14); y=330+k*92
        if a<=0: continue
        d.rectangle([60,y+18,104,y+26],fill=A(col,a)); txt(d,122,y,lab,f(BEB,60),col,a)
        arrow='↑' if col==RED else '↓'
        txt(d,124+d.textlength(lab,font=f(BEB,60))+12,y+12,arrow,f('DM',44,'Bold'),col,a)
    p=ap(t,T0+0.2,0.3)
    if p<=0: return
    chart_axes(d,X0,Y0,X1,Y1,p)
    txt(d,X0-10,Y0-8,'LEVEL',f('MONO',18),MUTED,p,'rt'); txt(d,X1,Y1+12,'TIME →',f('MONO',18),MUTED,p,'ra')
    def curve(fn,t1,dur,col):
        g=clamp((t-t1)/dur)
        if g<=0: return
        n=60; pts=[]
        for i in range(int(n*g)+1):
            u=i/n; pts.append((lerp(X0,X1,u),lerp(Y1,Y0,fn(u))))
        if len(pts)>1: gline(d,pts,col,6,1); x,y=pts[-1]; d.ellipse([x-9,y-9,x+9,y+9],fill=A(col,1))
    curve(lambda u:0.3+0.62/(1+math.exp(-(u-0.45)*12)),70.0,1.2,RED)
    curve(lambda u:0.62-0.48/(1+math.exp(-(u-0.5)*12)),71.5,1.0,CYAN)
    curve(lambda u:max(0.04,0.55-0.6*clamp((u-0.35)/0.4)),72.76,0.9,VGOLD)
    if t>=73.7: tag(d,X1-150,Y1-80,'FLAT',VGOLD,24,expo((t-73.7)/0.12))
def sc_bars(im,d,t):  # S9 bar chart + verdict, PiP top-left
    T0=74.0; X0,Y0,X1,Y1=110,880,1010,1290
    kicker(d,560,262,'ON TREN',t,T0+0.1,VGOLD,24)
    p=ap(t,T0+0.1,0.25)
    if p<=0: return
    txt(d,560,320,'SAME GUY',f(BEB,80),CREAM,ap(t,74.78))
    txt(d,560,402,'two readings',f('DM',30,'Medium'),MUTED,ap(t,74.9))
    chart_axes(d,X0,Y0,X1,Y1,p)
    roof=Y0+120
    dashed(d,X0,roof,X1,(170,170,180),3,a=p); txt(d,X1,roof-34,'ROOF',f('MONO',18),MUTED,p,'ra')
    # TEST bar breaks through the roof
    g=clamp((t-75.8)/0.7); h=lerp(0,Y1-858,ease_io(g))
    bx0,bx1=X0+120,X0+340
    if g>0:
        top=Y1-h
        lit_bar(d,bx0,top,bx1,Y1,VGOLD,1)
        if GL: GL.rectangle([bx0-4,top-4,bx1+4,Y1],outline=A(VGOLD,1),width=10)
        if top<roof:  # crack shards at roof
            c=expo((t-76.3)/0.2)
            for k,(dx,dy) in enumerate([(-30,-20),(250,-30),(-10,-50),(230,-60),(60,-24)]):
                d.polygon([(bx0+dx,roof+dy*c),(bx0+dx+18,roof+dy*c-10),(bx0+dx+10,roof+dy*c+8)],fill=A(WHITE,1-0.5*c))
        txt(d,(bx0+bx1)/2,top+44 if top<roof else top-50,'TOTAL T',f(BEB,52),INK if top<roof else VGOLD,1,'mm')
    txt(d,(bx0+bx1)/2,Y1+30,'TESTOSTERONE',f('MONO',20),MUTED,p,'mm')
    lx0,lx1=X0+520,X0+740
    a=ap(t,77.38,0.2)
    if a>0:
        hh=lerp(0,14,a); d.rectangle([lx0,Y1-hh,lx1,Y1],fill=A(RED,a))
        if t>=77.68:
            b=expo((t-77.68)/0.12); s=lerp(1.4,1,b)
            txt(d,(lx0+lx1)/2,Y1-170,'0',f(BEB,int(150*s)),RED,b,'mm')
            if GL: GL.text(((lx0+lx1)/2,Y1-170),'0',font=f(BEB,int(150*s)),fill=A(RED,b),anchor='mm')
    txt(d,(lx0+lx1)/2,Y1+30,'SEX DRIVE',f('MONO',20),MUTED,a,'mm')
    # verdict: not a T problem -> prolactin problem
    if t>=80.0:
        b=expo((t-80.0)/0.12); y=1160
        d.rectangle([X0-50,y,X1+10,y+110],fill=A((6,8,12),0.96*b))
        fn=f(BEB,74); lab='TESTOSTERONE'; tw=d.textlength(lab,font=fn)
        txt(d,X0-20,y+18,lab,fn,(150,150,156),b)
        s=expo((t-80.25)/0.18); d.line([(X0-30,y+58),(X0-30+(tw+20)*s,y+58)],fill=A(RED,b),width=8)
        if s>0 and GL: GL.line([(X0-30,y+58),(X0-30+(tw+20)*s,y+58)],fill=A(RED,b),width=14)
        if t>=81.82:
            v=expo((t-81.82)/0.10); vx0=X0-20+tw+40; vx1=lerp(vx0,X1,v)
            lit_bar(d,vx0,y+8,vx1,y+102,RED,1)
            if GL: GL.rectangle([vx0-4,y+4,vx1+4,y+106],outline=A(RED,1),width=12)
            if v>0.6: txt(d,vx0+24,y+16,'PROLACTIN',fn,WHITE,1)
def sc_laborder(im,d,t):  # S10 lab requisition document, right column
    T0=82.9; x0,y0,x1,y1=812,300,1046,1480
    p=ap(t,T0+0.05,0.28)
    if p<=0: return
    xo=lerp(260,0,p); x0+=xo; x1+=xo
    x0=812-110+xo;
    d.rectangle([x0+8,y0+10,x1+8,y1+10],fill=(0,0,0,int(120*p)))
    d.rectangle([x0,y0,x1,y1],fill=A(PAPER,p))
    lit_bar(d,x0,y0,x1,y0+70,COARED,p); txt(d,x0+20,y0+16,'LAB ORDER',f(BEB,48),WHITE,p)
    txt(d,x0+20,y0+90,'PANEL · ENDOCRINE',f('MONO',18),(90,90,96),p)
    d.line([(x0+20,y0+122),(x1-20,y0+122)],fill=A((150,150,150),p),width=2)
    items=[('PROLACTIN',83.62,y0+150),('ESTRADIOL',84.42,y0+250)]
    for lab,tt,y in items:
        d.rectangle([x0+20,y,x0+60,y+40],outline=A((40,40,46),p),width=3)
        txt(d,x0+78,y-4,lab,f(BEB,52),(20,20,24),p)
        if t>=tt: check(d,x0+26,y+20,COARED,1.0,ap(t,tt,0.08),6)
    txt(d,x0+78,y0+300,'SENSITIVE (LC/MS)',f('MONO',16),(90,90,96),ap(t,84.42))
    if t>=85.08:
        b=expo((t-85.08)/0.15); d.line([(x0+8,y0+150),(x0+8,y0+330)],fill=A(COARED,b),width=5)
        tag(d,x0+20,y0+350,'SAME DRAW',COARED,20,b,glow=False)
    txt(d,x0+20,y0+440,'CONDITIONS',f('MONO',18),(90,90,96),p)
    d.line([(x0+20,y0+470),(x1-20,y0+470)],fill=A((150,150,150),p),width=2)
    cond=[('AM DRAW',86.18),('RESTED',86.6),('NO SEX',87.46),('NO TRAINING',88.16)]
    for k,(lab,tt) in enumerate(cond):
        y=y0+500+k*92
        d.rectangle([x0+20,y,x0+60,y+40],outline=A((40,40,46),p),width=3)
        txt(d,x0+78,y-2,lab,f(BEB,46),(20,20,24),p)
        if t>=tt: check(d,x0+26,y+20,COARED,1.0,ap(t,tt,0.08),6)
    txt(d,x0+20,y1-50,'FASTED · BEFORE TRAINING',f('MONO',14),(110,110,116),p)
def sc_spike(im,d,t):  # S11 spike chart in split frame
    T0=89.2; X0,Y0,X1,Y1=110,1150,1010,1470
    kicker(d,70,1100,'PROLACTIN READING',t,T0+0.1,VGOLD,22)
    p=ap(t,T0+0.15,0.25)
    if p<=0: return
    if t>=89.9: tag(d,640,1094,'CLINICAL STUDIES',CYAN,20,ap(t,89.9,0.12))
    chart_axes(d,X0,Y0,X1,Y1,p)
    rlo,rhi=Y1-70,Y1-170
    d.rectangle([X0+4,rhi,X1,rlo],fill=A((30,255,110),0.10*p)); dashed(d,X0,rhi,X1,GREEN,2,a=0.8*p); dashed(d,X0,rlo,X1,GREEN,2,a=0.8*p)
    txt(d,X0+12,rhi-30,'REFERENCE RANGE',f('MONO',16),GREEN,p)
    g=clamp((t-T0-0.3)/1.4)
    base=lambda u:(rhi+rlo)/2+8*math.sin(u*40)
    spikes=[(0.45,'SEX',91.84),(0.62,'TRAINING',92.1),(0.80,'NO SLEEP',92.4)]
    pts=[]
    for i in range(int(120*g)+1):
        u=i/120; y=base(u)
        for (c,lab,tt) in spikes:
            s=expo((t-tt)/0.25); y-=s*175*math.exp(-((u-c)/0.025)**2)
        pts.append((lerp(X0,X1*0.9,u),y))
    if len(pts)>1: gline(d,pts,CYAN,5,1)
    for (c,lab,tt) in spikes:
        if t>=tt:
            b=expo((t-tt)/0.15); x=lerp(X0,X1*0.9,c); tag(d,x-50,rhi-160,lab,RED,18,b,glow=False)
    if t>=93.84:
        b=expo((t-93.84)/0.12); x=X1*0.9+40; y=rhi-120
        d.ellipse([x-14,y-14,x+14,y+14],fill=A(RED,b))
        if GL: GL.ellipse([x-22,y-22,x+22,y+22],fill=A(RED,b))
        brackets(d,x-46,y-46,x+46,y+46,A(RED,b),16,5)
        tag(d,x-170,y+56,'FALSE HIGH',RED,28,b)
def sc_fork(im,d,t):  # S12 treatment fork in split frame
    T0=94.8; X0,X1=70,1010
    kicker(d,X0,1100,'MATCH THE FIX',t,T0+0.05,VGOLD,22)
    lanes=[(1160,'PROLACTIN',RED,94.98),(1350,'E2',CYAN,98.02)]
    for y,lab,col,tt in lanes:
        a=ap(t,tt,0.16)
        if a<=0: continue
        d.rounded_rectangle([X0,y,X0+250,y+100],18,fill=A((20,6,8) if col==RED else (4,18,24),a),outline=A(col,a),width=4)
        txt(d,X0+125,y+52,lab,f(BEB,58 if lab!='E2' else 72),col,a,'mm')
        if GL: GL.rounded_rectangle([X0,y,X0+250,y+100],18,outline=A(col,a),width=10)
    a=ap(t,95.94,0.3)
    if a>0:
        ax=lerp(X0+260,X0+340,a); gline(d,[(X0+260,1210),(ax,1210)],WHITE,4,a,False); d.polygon([(ax+16,1210),(ax,1198),(ax,1222)],fill=A(WHITE,a))
        d.rounded_rectangle([X0+370,1160,X1,1260],18,fill=A((12,14,20),a),outline=A((90,86,76),a),width=2)
        txt(d,X0+396,1172,'DOPAMINE AGONIST',f(BEB,52),CREAM,a)
        if t>=97.08: tag(d,X0+396,1226-6,'e.g. CABERGOLINE',VGOLD,18,ap(t,97.08,0.12),glow=False)
    opts=[('AI',100.1),('LOWER DOSE',100.42),('SYNERGISTIC COMPOUND',102.88)]
    if t>=98.9:
        a=ap(t,98.9,0.3); gline(d,[(X0+260,1400),(lerp(X0+260,X0+330,a),1400)],WHITE,4,a,False)
        d.line([(X0+330,1370),(X0+330,1480)],fill=A(WHITE,a),width=4)
    for k,(lab,tt) in enumerate(opts):
        b=ap(t,tt,0.14)
        if b<=0: continue
        y=1342+k*62 if k<2 else 1342+2*62
        x=X0+370 if k<2 else X0+370
        yy=[1340,1396,1452][k]
        d.line([(X0+330,yy+20),(X0+366,yy+20)],fill=A(WHITE,b),width=4)
        tag(d,x,yy,lab,CYAN,26,b)
    if t>=104.0: pass
def sc_network(im,d,t):  # S13 cross-reference network, top band
    T0=104.0
    kicker(d,90,268,'YOUR BLOODWORK',t,T0+0.1,VGOLD,22)
    nodes=[('PRL',330,370,RED),('E2',520,300,CYAN),('T',720,370,VGOLD),('LH',910,300,GREEN)]
    nodes=[('PRL',360,390,RED),('E2',540,310,CYAN),('T',720,390,VGOLD),('LH',900,310,CYAN)]
    if t>=105.1: tag(d,90,330,'COACH',VGOLD,22,ap(t,105.1,0.12))
    if t>=106.98: tag(d,90,384,'YOUR CONTEXT',RED,20,ap(t,106.98,0.12))
    g=clamp((t-108.86)/0.6)
    pairs=[(0,1),(1,2),(2,3),(0,2),(1,3),(0,3)]
    for k,(i,j) in enumerate(pairs):
        q=clamp(g*len(pairs)-k)
        if q<=0: continue
        a_,b_=nodes[i],nodes[j]
        gline(d,[(a_[1],a_[2]),(lerp(a_[1],b_[1],q),lerp(a_[2],b_[2],q))],WHITE,3,0.8)
    for k,(lab,x,y,col) in enumerate(nodes):
        a=ap(t,T0+0.3+0.12*k,0.16)
        if a<=0: continue
        d.ellipse([x-46,y-46,x+46,y+46],fill=A(DEEP,a),outline=A(col,a),width=5)
        if GL: GL.ellipse([x-50,y-50,x+50,y+50],outline=A(col,a),width=10)
        txt(d,x,y+2,lab,f(BEB,44),col,a,'mm')
    if t>=109.5:
        b=expo((t-109.5)/0.12); tag(d,560,420,'PRL : E2',VGOLD,18,b,glow=False); tag(d,740,420,'T : E2',VGOLD,18,b,glow=False)
# scene list: (start, end, layout, drawfn, panel box or None)
SCENES=[
 (14.9,17.30,'TOPBAND',sc_gauge,(60,250,1020,480)),
 (17.30,20.85,'CHEST',sc_circuit,(60,1190,1020,1480)),
 (20.95,33.60,'SIDE_R',sc_severity,None),
 (33.70,49.70,'SPLIT',sc_stack,None),
 (49.90,56.62,'BUBBLE',sc_switch,None),
 (58.55,66.40,'TOPBAND',sc_scope,(60,250,1020,480)),
 (66.40,69.48,'CHEST',sc_leash,(60,1190,1020,1480)),
 (69.48,74.00,'PIP_TR',sc_linegraph,None),
 (74.00,82.80,'PIP_TL',sc_bars,None),
 (82.90,88.95,'SIDE_L',sc_laborder,None),
 (89.20,94.80,'SPLIT',sc_spike,None),
 (94.80,103.95,'SPLIT',sc_fork,None),
 (104.00,DUR,'TOPBAND',sc_network,(60,250,1020,480)),
]
TRANS=0.40
def lay_of(name): return LAY[name] if LAY.get(name) else None
def seg_of(t):
    for i,(b0,b1) in enumerate(BOUNDS):
        if b0<=t<b1: return i
    return len(BOUNDS)-1
# punch-in alternation; very short trims inherit the previous zoom so there is no flicker
ZOOM=[];_z=1.0;_last=-1
for i,(b0,b1) in enumerate(BOUNDS):
    if i==0: ZOOM.append(1.0); continue
    if b1-b0>=0.8 and BOUNDS[i-1][1]-BOUNDS[i-1][0]>=0.0: _z=1.0 if ZOOM[-1]!=1.0 else 1.09
    else: _z=ZOOM[-1]
    ZOOM.append(_z)
def footage_layout(t):
    z=ZOOM[seg_of(t)]; full=L_full(z)
    # find current/next scenes
    cur=None
    for k,sc in enumerate(SCENES):
        if sc[0]<=t<sc[1]: cur=k
    def L(k):
        if k is None: return full
        l=lay_of(SCENES[k][2]); return l if l else full
    if cur is None:
        # after a scene ends: ease back to full
        prev=[k for k,sc in enumerate(SCENES) if sc[1]<=t]
        if prev and t-SCENES[prev[-1]][1]<TRANS: return lay_lerp(L(prev[-1]),full,ease_io((t-SCENES[prev[-1]][1])/TRANS))
        return full
    s0=SCENES[cur][0]
    prevk=cur-1 if cur>0 and abs(SCENES[cur-1][1]-s0)<0.12 else None
    base=L(prevk) if prevk is not None else full
    if t-s0<TRANS: return lay_lerp(base,L(cur),ease_io((t-s0)/TRANS))
    return L(cur)
# ---------------- background (exposed areas) ----------------
def make_bg():
    yy,xx=np.mgrid[0:H,0:W].astype(np.float32)
    base=np.zeros((H,W,3),np.float32)+np.array([7,9,15],np.float32)
    g=np.exp(-(((xx-900)/700)**2+((yy-200)/700)**2))[...,None]*np.array([40,30,18],np.float32)
    g2=np.exp(-(((xx-150)/600)**2+((yy-1700)/600)**2))[...,None]*np.array([30,4,8],np.float32)
    rng=np.random.default_rng(3); nz=rng.normal(0,3.0,(H,W,1)).astype(np.float32)
    im=np.clip(base+g+g2+nz,0,255).astype(np.uint8)
    out=Image.fromarray(im); d=ImageDraw.Draw(out)
    for y in range(0,H,6): d.line([(0,y),(W,y)],fill=(10,12,19))
    return out
BG=make_bg()
_mcache={}
def mask_img(box):
    key=tuple(int(round(v)) for v in box)
    if key not in _mcache:
        if len(_mcache)>64: _mcache.clear()
        x0,y0,x1,y1,r=key; m=Image.new('L',(W,H),0); ImageDraw.Draw(m).rounded_rectangle([x0,y0,x1,y1],r,fill=255); _mcache[key]=m
    return _mcache[key]
def place_footage(src,lay):
    s,cx,cy,box=lay
    ox=cx-AX*s; oy=cy-AY*s
    if abs(s-1)<1e-4 and abs(ox)<0.5 and abs(oy)<0.5 and box==(0,0,W,H,0): return src.copy(),False
    canvas=BG.copy()
    sw,sh=int(round(W*s)),int(round(H*s))
    sc=src.resize((sw,sh),Image.BICUBIC)
    lay_im=Image.new('RGB',(W,H)); lay_im.paste(BG,(0,0)); lay_im.paste(sc,(int(round(ox)),int(round(oy))))
    boxed=box!=(0,0,W,H,0)
    m=mask_img(box)
    if boxed:  # soft shadow under framed footage
        sh_=m.filter(ImageFilter.GaussianBlur(18)).point(lambda v:int(v*0.6))
        canvas.paste((0,0,0),(0,0),sh_.transform((W,H),Image.AFFINE,(1,0,0,0,1,-12)))
    # footage only where it exists
    fm=Image.new('L',(W,H),0); fm.paste(255,(int(round(ox)),int(round(oy)),int(round(ox))+sw,int(round(oy))+sh))
    canvas.paste(lay_im,(0,0),ImageChops.multiply(m,fm))
    return canvas,boxed
# ---------------- captions ----------------
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
ACCENT={'PROLACTIN':RED,'LACTATED':RED,'LACTATING':RED,'LACTATION':RED,'GYNO':RED,'ESTROGEN':CYAN,'E2':CYAN,'DOPAMINE':CYAN,'TREN':VGOLD,'NPP':VGOLD,'DECA':VGOLD,'CABERGOLINE':VGOLD,'LIBIDO':VGOLD,'ZERO':RED,'FALSE':RED,'SWITCH':VGOLD}
CAPPOS={'CHEST':(540,262,920),'SIDE_R':(700,1290,700),'SIDE_L':(380,1290,640),'SPLIT':(520,955,880)}
def _raw(t):
    cur=None
    for sc in SCENES:
        if sc[0]<=t<sc[1]: cur=sc[2]
    return CAPPOS.get(cur,(540,1335,920))
_BND=sorted(set([sc[0] for sc in SCENES]+[sc[1] for sc in SCENES]))
def cap_params(t):
    tb=max([b for b in _BND if b<=t],default=None)
    if tb is None or t-tb>=TRANS: return _raw(t)
    a=_raw(tb-0.001); b=_raw(t); q=ease_io((t-tb)/TRANS)
    return tuple(lerp(x,y,q) for x,y in zip(a,b))
def captions(im,t):
    g=group_at(t)
    if not g: return
    cx,cy,maxw=cap_params(t); cy=int(cy)
    d=ImageDraw.Draw(im,'RGBA')
    ws=[WORDS[i]['w'].upper().rstrip(',.?!') for i in g]
    size=124
    while True:
        fn=f(BEB,size); sp=d.textlength(' ',font=fn)+14; wd=[d.textlength(w,font=fn) for w in ws]; tot=sum(wd)+sp*(len(ws)-1)
        if tot<=maxw: break
        size-=4
    xs=[];x=cx-tot/2
    for w_ in wd: xs.append(x); x+=w_+sp
    act=0
    for k,i in enumerate(g):
        if WORDS[i]['s']<=t: act=k
    g0=WORDS[g[0]]['s']; s=lerp(0.9,1,expo((t-g0)/0.10))
    cap=Image.new('RGBA',(W,300),(0,0,0,0)); cd=ImageDraw.Draw(cap); shd=Image.new('RGBA',(W,300),(0,0,0,0)); sd=ImageDraw.Draw(shd)
    prev=max(0,act-1); bt=expo((t-WORDS[g[act]]['s'])/0.07) if act>0 else 1
    bx0=lerp(xs[prev],xs[act],bt)-18; bx1=lerp(xs[prev]+wd[prev],xs[act]+wd[act],bt)+18
    for k,(w_,x_) in enumerate(zip(ws,xs)):
        sd.text((x_+4,46),w_,font=fn,fill=(0,0,0,210))
    cap.alpha_composite(shd.filter(ImageFilter.GaussianBlur(6)))
    lit_bar(cd,bx0,40+size*0.02,bx1,40+size*0.98,RED)
    for k,(w_,x_) in enumerate(zip(ws,xs)):
        col=CREAM
        acc=ACCENT.get(w_.replace("'S",''))
        spoken=WORDS[g[k]]['s']<=t
        if acc and spoken and k!=act: col=acc
        cd.text((x_,40),w_,font=fn,fill=col,stroke_width=0 if k==act else 3,stroke_fill=(0,0,0))
    if abs(s-1)>0.002:
        cap=cap.resize((int(W*s),int(300*s)),Image.BICUBIC); ox=int((W-cap.width)/2+(cx-540)*(s-1)); oy=int(cy-40-(cap.height-300)/2)
    else: ox,oy=0,cy-40
    im.alpha_composite(cap,(ox,oy))
# ---------------- frame ----------------
def frame(src,t):
    global GL
    lay=footage_layout(t)
    base,boxed=place_footage(src,lay)
    im=base.convert('RGBA')
    # subtle bottom/top shade for caption legibility only in full layouts
    glow=Image.new('RGBA',(W,H),(0,0,0,0)); GL=ImageDraw.Draw(glow,'RGBA')
    d=ImageDraw.Draw(im,'RGBA')
    s,cx,cy,box=lay
    if box!=(0,0,W,H,0) and box[2]-box[0]<W-2:
        x0,y0,x1,y1,r=box
        d.rounded_rectangle([x0,y0,x1,y1],r,outline=A(VGOLD,0.9),width=3)
        GL.rounded_rectangle([x0,y0,x1,y1],r,outline=A(VGOLD,0.6),width=8)
        if r<100: brackets(d,x0-10,y0-10,x1+10,y1+10,A(VGOLD,1),40,6)
    for sc in SCENES:
        t0,t1,ln,fn,pbox=sc
        if t0-0.01<=t<t1+0.2:
            pin=expo((t-t0-0.05)/0.25); pout=clamp((t-t1)/0.18)
            al=pin*(1-pout)
            if al<=0: continue
            if pbox:
                x0,y0,x1,y1=pbox; hh=(y1-y0)
                panel(im,(x0,y0,x0+lerp(0.0,1,expo((t-t0)/0.22))*(x1-x0),y1),al)
            lay_=Image.new('RGBA',(W,H),(0,0,0,0)); dl=ImageDraw.Draw(lay_,'RGBA')
            fn(lay_,dl,t)
            if pin<1: lay_=lay_.filter(ImageFilter.GaussianBlur(6*(1-pin)))
            if al<1: lay_.putalpha(lay_.split()[3].point(lambda v:int(v*al)))
            im.alpha_composite(lay_)
    GLd=glow
    GL=None
    if GLd.getbbox():
        sm=GLd.resize((W//4,H//4),Image.BILINEAR)
        g1=np.asarray(sm.filter(ImageFilter.GaussianBlur(3.5))).astype(np.float32)/255; g2=np.asarray(sm.filter(ImageFilter.GaussianBlur(10))).astype(np.float32)/255
        prem=np.clip(g1[...,:3]*g1[...,3:]*2.0+g2[...,:3]*g2[...,3:]*1.6,0,1)
        prem=np.asarray(Image.fromarray((prem*255).astype(np.uint8)).resize((W,H),Image.BILINEAR)).astype(np.float32)/255
        b=np.asarray(im.convert('RGB')).astype(np.float32)/255
        im=Image.fromarray(((1-(1-b)*(1-prem))*255).astype(np.uint8)).convert('RGBA')
    d=ImageDraw.Draw(im,'RGBA'); d.rectangle([0,0,7,H],fill=GOLD)
    # static disclaimer + handle (never animate)
    d.text((40,1496),'FOR RESEARCH & EDUCATIONAL PURPOSES ONLY',font=f('MONO',17,'Medium'),fill=(200,200,204,150))
    d.text((1040,1496),'@coach.agz',font=f('MONO',19,'Bold'),fill=GOLD+(210,),anchor='ra')
    captions(im,t)
    return im.convert('RGB')
VERDICT_SHAKE=[81.82,55.72,76.3]
def shake(out,t):
    for tv in VERDICT_SHAKE:
        k=round((t-tv)*FPS)
        if k in (0,1):
            dx=[9,-5][k]; z=1.02; big=out.resize((int(W*z),int(H*z)),Image.BICUBIC); ox=(big.width-W)//2-dx; oy=(big.height-H)//2
            out=big.crop((ox,oy,ox+W,oy+H)); ImageDraw.Draw(out).rectangle([0,0,7,H],fill=GOLD)
    return out
if __name__=='__main__':
    mode=sys.argv[1]; SRC=B+'/assembled.mov'
    if mode=='stills':
        os.makedirs(B+'/qc',exist_ok=True)
        for tt in [float(x) for x in sys.argv[2:]]:
            subprocess.run(['ffmpeg','-v','error','-y','-ss',f'{tt:.3f}','-i',SRC,'-frames:v','1',B+'/qc/_src.png'])
            shake(frame(Image.open(B+'/qc/_src.png').convert('RGB'),tt),tt).resize((540,960)).save(B+f'/qc/st_{tt:06.2f}.jpg',quality=88)
        sys.exit()
    n0,n1=int(sys.argv[2]),int(sys.argv[3]); out=sys.argv[4]
    dec=subprocess.Popen(['ffmpeg','-v','error','-ss',f'{n0/FPS:.4f}','-i',SRC,'-frames:v',str(n1-n0),'-f','rawvideo','-pix_fmt','rgb24','-'],stdout=subprocess.PIPE)
    enc=subprocess.Popen(['ffmpeg','-v','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-','-c:v','libx264','-crf','16','-preset','medium','-pix_fmt','yuv420p',out],stdin=subprocess.PIPE)
    for n in range(n0,n1):
        buf=dec.stdout.read(W*H*3)
        if len(buf)<W*H*3: print('short',n); break
        t=n/FPS
        enc.stdin.write(shake(frame(Image.frombuffer('RGB',(W,H),buf),t),t).tobytes())
    enc.stdin.close(); enc.wait(); dec.kill(); print('done',n0,n1)
