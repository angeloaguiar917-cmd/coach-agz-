# Scenes A: pedestal, stepper, microscope lens, dual graph, radial gauge.
import math, numpy as np
from PIL import Image, ImageDraw, ImageFilter
import r_core as C
from r_core import (W,H,f,A,txt,stxt,tag,check,cross,arrow,brackets,litbar,line,
                    shade,clamp,expo,ease,land,lerp,ap,win,
                    BEB,BAR,DMR,DMB,MONO,GOLD,CREAM,NAVY,MUTED,RED,VGOLD,CYAN,GREEN,AMBER,DEEP,INK,WHITE)

# 1 · EQ on a pedestal: x-ray vial on a gold plinth that cracks on "overrated"
def s_pedestal(im,d,t):
    a=win(t,1.06,9.70,0.2,0.18)
    if a<=0: return
    shade(im,(20,470,440,1320),0.60*a,70); d=ImageDraw.Draw(im,'RGBA')
    dx=-470*clamp((t-9.70)/0.16)**2
    # plinth lands on "pedestal"
    q=land((t-1.80)/0.26)
    if t>=1.80:
        py=lerp(1250,1060,q)
        d.polygon([(90+dx,py+120),(360+dx,py+120),(330+dx,py),(120+dx,py)],fill=A((30,26,18),a),outline=A(VGOLD,a))
        line(d,[(120+dx,py),(330+dx,py),(360+dx,py+120),(90+dx,py+120),(120+dx,py)],VGOLD,4,a)
        if C.GL: C.GL.line([(120+dx,py),(330+dx,py)],fill=A(VGOLD,a),width=10)
        txt(d,225+dx,py+60,'EQ',f(BEB,84),VGOLD,a,'mm')
        if t>=6.02:
            c=clamp((t-6.02)/0.2); pts=[(225+dx,py),(208+dx,py+30),(240+dx,py+58),(214+dx,py+92),(234+dx,py+120)]
            n=1+int(c*(len(pts)-1)); d.line(pts[:n+1],fill=A(RED,a),width=6)
            if C.GL: C.GL.line(pts[:n+1],fill=A(RED,a),width=12)
    # vial (schematic) drops onto the plinth
    p=expo((t-1.06)/0.22); va=a*p; x0,x1=150+dx,300+dx; yt=lerp(760,800,q if t>=1.8 else 0); yb=yt+230
    d.rounded_rectangle([x0,yt,x1,yb],radius=18,outline=A(CYAN,va),width=5)
    d.rounded_rectangle([x0+28,yt-82,x1-28,yt-40],radius=6,fill=A((40,50,60),va),outline=A(CYAN,va),width=4)
    d.rectangle([x0+40,yt-40,x1-40,yt],outline=A(CYAN,va),width=5)
    d.rectangle([x0+8,yt+96,x1-8,yb-8],fill=A(CYAN,0.20*va))
    d.rectangle([x0+8,yt+40,x1-8,yt+92],fill=A((235,235,230),0.92*va))
    txt(d,(x0+x1)/2,yt+66,'EQ 300',f(BAR,30),INK,va,'mm')
    if C.GL: C.GL.rounded_rectangle([x0,yt,x1,yb],radius=18,outline=A(CYAN,va),width=10)
    # spec rows strike through on "overrated"
    for i,(lab,tt) in enumerate([('LEAN GAINS',2.88),('VASCULARITY',3.60),('ENDURANCE',4.46)]):
        if t<tt: continue
        ra=a*ap(t,tt,0.12); y=512+i*58; x=48+dx+lerp(-24,0,ra)
        check(d,x,y+6,GREEN,0.85,ra); stxt(d,x+44,y,lab,f(BAR,42),WHITE,ra)
        if t>=6.02+i*0.06:
            sgo=clamp((t-6.02-i*0.06)/0.1); tw=d.textlength(lab,font=f(BAR,42)); d.line([(x-4,y+26),(lerp(x-4,x+48+tw,sgo),y+26)],fill=A(RED,ra),width=6)
    # hype vs real return bars
    if t>=6.02:
        ba=a*ap(t,6.02,0.14)
        for j,(lab,fr,col,tt) in enumerate([('HYPE',1.0,VGOLD,6.02),('PAYOFF',0.26,RED,6.62)]):
            y=1200+j*52; frac=fr*expo((t-tt)/0.35); txt(d,48+dx,y,lab,f(MONO,24),CREAM,ba)
            d.rectangle([180+dx,y+2,410+dx,y+30],outline=A((80,84,96),ba),width=2)
            if frac>0.01: litbar(d,183+dx,y+5,183+dx+224*frac,y+27,col,ba)
    # first-cycle warning
    if t>=8.84:
        wa=a*ap(t,8.84,0.12); bl=1 if (int((t-8.84)*6)%2==0 or t>9.3) else 0.4; x=48+dx; y=452
        d.polygon([(x,y+44),(x+25,y),(x+50,y+44)],fill=A(RED,wa*bl)); txt(d,x+25,y+30,'!',f(BEB,34),WHITE,wa,'mm')
        tag(d,x+62,y+2,'1ST CYCLE',RED,30,wa)

# 2 · three-step flow: SCIENCE -> SIMPLIFY -> OPTIMIZE (top band)
def s_stepper(im,d,t):
    a=win(t,10.06,13.55,0.18,0.16)
    if a<=0: return
    dy=-250*clamp((t-13.55)/0.16)**2
    shade(im,(40,236+dy,1040,478+dy),0.6*a,50); d=ImageDraw.Draw(im,'RGBA')
    txt(d,80,250+dy,'THE BREAKDOWN',f(MONO,26),VGOLD,a)
    nodes=[('01','SCIENCE',10.80),('02','SIMPLIFY',12.16),('03','OPTIMIZE',13.10)]; xs=[210,540,870]; y=352+dy
    line(d,[(xs[0],y),(xs[-1],y)],(70,74,90),4,a)
    prog=0
    if t>=10.80: prog=lerp(0,0.5,expo((t-10.80)/0.9)) if t<12.16 else lerp(0.5,1.0,expo((t-12.16)/0.8))
    xe=lerp(xs[0],xs[-1],prog); line(d,[(xs[0],y),(xe,y)],VGOLD,6,a)
    if C.GL: C.GL.line([(xs[0],y),(xe,y)],fill=A(VGOLD,a),width=12)
    for (n,lab,tt),x in zip(nodes,xs):
        on=t>=tt; k=ap(t,tt,0.12) if on else 0; r=lerp(30,38,k)
        d.ellipse([x-r,y-r,x+r,y+r],fill=A(VGOLD if on else (30,32,42),a),outline=A(VGOLD,a),width=4)
        if C.GL and on: C.GL.ellipse([x-r-4,y-r-4,x+r+4,y+r+4],outline=A(VGOLD,a),width=10)
        txt(d,x,y+2,n,f(BEB,40),INK if on else MUTED,a,'mm')
        stxt(d,x,y+76,lab,f(BAR,40),WHITE if on else (130,130,140),a,'mm')

# 3 · microscope lens: red cells multiply under a scope
_RBC=[((math.sin(i*12.9898)*43758.5453)%1,(math.sin(i*78.233)*12345.678)%1) for i in range(60)]
def s_lens(im,d,t):
    a=win(t,14.20,18.95,0.22,0.0)
    if a<=0: return
    cx,cy,R=252,430,170
    hk=clamp((t-18.68)/0.28)
    if hk>0: cx=lerp(cx,120,ease(hk)); cy=lerp(cy,610,ease(hk)); R=lerp(R,10,ease(hk))
    lay=Image.new('RGBA',(W,H),(0,0,0,0)); ld=ImageDraw.Draw(lay,'RGBA')
    ld.ellipse([cx-R,cy-R,cx+R,cy+R],fill=(12,2,6,235))
    n=8 if t<16.14 else int(lerp(8,60,expo((t-16.14)/1.4)))
    for i in range(n):
        u,v=_RBC[i]; ang=u*6.283+t*0.25*(1 if i%2 else -1); rr=math.sqrt(v)*(R-24)
        x=cx+rr*math.cos(ang); y=cy+rr*math.sin(ang); s=R/170*(18+6*((i*7)%3)); born=1 if i<8 else clamp((n-i)/3)
        ld.ellipse([x-s,y-s*0.86,x+s,y+s*0.86],fill=(200,20,34,int(255*born)))
        ld.ellipse([x-s*0.45,y-s*0.38,x+s*0.45,y+s*0.38],fill=(240,80,80,int(200*born)))
    m=Image.new('L',(W,H),0); ImageDraw.Draw(m).ellipse([cx-R,cy-R,cx+R,cy+R],fill=255)
    lay.putalpha(Image.fromarray(np.minimum(np.asarray(lay.split()[3]),np.asarray(m))))
    lay.putalpha(lay.split()[3].point(lambda q:int(q*a)))
    im.alpha_composite(lay); d=ImageDraw.Draw(im,'RGBA')
    d.ellipse([cx-R,cy-R,cx+R,cy+R],outline=A(CYAN,a),width=5)
    if C.GL: C.GL.ellipse([cx-R-4,cy-R-4,cx+R+4,cy+R+4],outline=A(CYAN,a),width=12)
    for k in range(24):
        ang=k/24*6.283; r0=R+6; r1=R+(18 if k%6==0 else 11)
        line(d,[(cx+r0*math.cos(ang),cy+r0*math.sin(ang)),(cx+r1*math.cos(ang),cy+r1*math.sin(ang))],CYAN,3,a*(1-hk))
    sa=(t*1.6)%6.283; line(d,[(cx,cy),(cx+R*math.cos(sa),cy+R*math.sin(sa))],CYAN,2,0.5*a*(1-hk))
    if hk<1:
        b=a*(1-hk); txt(d,70,232,'RBC · 400×',f(MONO,24),CYAN,b); y=646
        if t>=16.14:
            ba=b*ap(t,16.14); stxt(d,82,y-2,'RBC OUTPUT',f(MONO,24),CREAM,ba)
            d.rectangle([250,y,430,y+26],outline=A((90,94,110),ba),width=2)
            fr=lerp(0.1,0.55,expo((t-16.14)/0.8)) if t<17.64 else lerp(0.55,1.0,expo((t-17.64)/0.3))
            litbar(d,253,y+3,253+174*fr,y+23,RED,ba); tx=253+174*0.55
            for yy in range(y-10,y+40,8): d.line([(tx,yy),(tx,yy+4)],fill=A(WHITE,ba),width=2)
            if t>=17.64: txt(d,tx,y+50,'TYPICAL',f(MONO,18),MUTED,ba,'mm')

# 4 · dual-trace graph over weeks: hematocrit climbs vs gains crawl (top panel slides down)
GX0,GX1,GY0,GY1=110,990,330,600
def _wx(w): return lerp(GX0,GX1,w/20)
def _hct(w): return 0.92*(1-math.exp(-w/2.6))
def _gain(w): return 0.30*(w/20)**1.25
def _vy(v): return lerp(GY1,GY0,v)
def s_graph(im,d,t,k):
    if k<=0: return
    oy=lerp(-730,0,k)
    d.rectangle([0,oy,W,oy+724],fill=A(NAVY,1))
    for gx in range(0,W,54): d.line([(gx,oy),(gx,oy+724)],fill=A((26,30,40),1),width=1)
    for gy in range(0,724,54): d.line([(0,oy+gy),(W,oy+gy)],fill=A((26,30,40),1),width=1)
    d.rectangle([0,oy+718,W,oy+724],fill=A(VGOLD,1))
    if C.GL: C.GL.rectangle([0,oy+714,W,oy+726],fill=A(VGOLD,0.8))
    txt(d,GX0-40,250+oy,'WEEKS ON EQ',f(MONO,24),MUTED)
    d.rectangle([520,256+oy,548,266+oy],fill=A(RED,1)); txt(d,558,248+oy,'HEMATOCRIT',f(MONO,24),WHITE)
    if t>=23.74: d.rectangle([800,256+oy,828,266+oy],fill=A(VGOLD,1)); txt(d,838,248+oy,'GAINS',f(MONO,24),WHITE)
    for j in range(1,4): d.line([(GX0,_vy(j/4)+oy),(GX1,_vy(j/4)+oy)],fill=A((44,48,62),1),width=1)
    d.line([(GX0,GY1+oy),(GX1,GY1+oy)],fill=A((120,124,140),1),width=3); d.line([(GX0,GY0+oy),(GX0,GY1+oy)],fill=A((120,124,140),1),width=3)
    lit={10:27.02,12:27.66,13:27.98,14:28.52,20:29.00}
    for w in (0,5,10,12,13,14,20):
        x=_wx(w); on=w in lit and t>=lit[w]; d.line([(x,GY1+oy),(x,GY1+10+oy)],fill=A((120,124,140),1),width=2)
        if w in(0,5) or on or w==20:
            if not (w in(12,13) and not on):
                col=VGOLD if on else (130,134,150); txt(d,x,GY1+30+oy,str(w),f(BEB if on else MONO,36 if on else 22),col,1,'mm')
    hp=clamp((t-19.34)/1.1)*20
    if hp>0:
        pts=[(_wx(w),_vy(_hct(w))+oy) for w in np.linspace(0,hp,50)]
        if t>=21.74:
            fa=ap(t,21.74,0.3)
            grad=Image.new('RGBA',(W,H),(0,0,0,0)); gd=ImageDraw.Draw(grad,'RGBA')
            gd.polygon(pts+[(pts[-1][0],GY1+oy),(pts[0][0],GY1+oy)],fill=A(RED,1))
            ga=np.asarray(grad.split()[3]).astype(np.float32)
            yy=np.arange(H)[:,None]; topy=min(p[1] for p in pts)
            fade=np.clip(1-(yy-topy)/150,0.18,1.0)        # bright near the line, fades down
            grad.putalpha(Image.fromarray((ga*fade*0.5*fa).astype(np.uint8)))
            im.alpha_composite(grad); d=ImageDraw.Draw(im,'RGBA')
        wdt=6 if t<21.74 else int(lerp(6,9,ap(t,21.74,0.3)))
        d.line(pts,fill=A(RED,1),width=wdt,joint='curve')
        if C.GL: C.GL.line(pts,fill=A(RED,1),width=4)        # keep the bloom tight to the line
        ex,ey=pts[-1]; d.ellipse([ex-9,ey-9,ex+9,ey+9],fill=A(WHITE,1))
    if t>=20.36: tag(d,_wx(1.2)+40,_vy(0.78)+oy-18,'CLIMBS FAST',RED,24,ap(t,20.36))
    if t>=21.74: tag(d,_wx(10.6),_vy(0.98)+oy-30,'THICK BLOOD',RED,24,ap(t,21.74))
    if t>=22.48 and t<23.74:
        ha=ap(t,22.48,0.2); x0,x1,yb=760,1000,300+oy; d.rectangle([x0-10,244+oy,x1+10,312+oy],fill=A(NAVY,1))
        txt(d,x0-210,254+oy,'HEART LOAD',f(MONO,24),RED,ha); pts=[]
        for i in range(90):
            u=i/89; x=lerp(x0,x1,u); ph=(u*5-t*4.5)%1; yy=yb-(34 if 0.46<ph<0.5 else -14 if 0.5<=ph<0.54 else 0); pts.append((x,yy-14))
        d.line(pts,fill=A(RED,ha),width=4)
        if C.GL: C.GL.line(pts,fill=A(RED,ha),width=9)
    gp=clamp((t-23.74)/5.4)*20
    if gp>0:
        pts=[(_wx(w),_vy(_gain(w))+oy) for w in np.linspace(0,gp,50)]; d.line(pts,fill=A(VGOLD,1),width=7,joint='curve')
        if C.GL: C.GL.line(pts,fill=A(VGOLD,1),width=4)
        ex,ey=pts[-1]; d.ellipse([ex-9,ey-9,ex+9,ey+9],fill=A(WHITE,1))
    if t>=25.16:
        ga=ap(t,25.16,0.2); w=7; x=_wx(w); y0=_vy(_hct(w))+oy+12; y1=_vy(_gain(w))+oy-12; y1v=lerp(y0,y1,expo((t-25.16)/0.35))
        d.line([(x,y0),(x,y1v)],fill=A(WHITE,ga),width=3); d.line([(x-12,y0),(x+12,y0)],fill=A(WHITE,ga),width=3)
        if t>=25.5: d.line([(x-12,y1),(x+12,y1)],fill=A(WHITE,ga),width=3)
        if t>=26.40: tag(d,x+18,(y0+y1)/2-22,'THE GAP',VGOLD,24,ap(t,26.40))
    cw=None
    for w,tt in lit.items():
        if t>=tt: cw=w
    if cw is not None:
        x=_wx(cw); d.line([(x,GY0+oy),(x,GY1+oy)],fill=A(VGOLD,0.8),width=3); gy=_vy(_gain(cw))+oy
        d.ellipse([x-12,gy-12,x+12,gy+12],outline=A(VGOLD,1),width=4)

# 5 · radial gauge: E2 reading unstable until steady state (right side)
def s_gauge(im,d,t):
    a=win(t,32.42,40.05,0.22,0.18)
    if a<=0: return
    cx,cy,R=838,392,132; shade(im,(540,228,1062,566),0.6*a,60); d=ImageDraw.Draw(im,'RGBA')
    R*=lerp(0.85,1.0,expo((t-32.42)/0.25))
    d.ellipse([cx-R,cy-R,cx+R,cy+R],fill=A((8,10,16),0.9*a)); d.arc([cx-R,cy-R,cx+R,cy+R],135,405,fill=A((50,54,68),a),width=16)
    if t<36.92: wk=lerp(0,3.5,clamp((t-32.6)/4.3))
    elif t<39.14: wk=lerp(3.5,7.2,clamp((t-36.92)/2.2))
    else: wk=lerp(7.2,10,expo((t-39.14)/0.6))
    locked=t>=39.52; col=GREEN if locked else (VGOLD if wk>5 else AMBER); end=135+270*wk/10
    d.arc([cx-R,cy-R,cx+R,cy+R],135,end,fill=A(col,a),width=16)
    if C.GL: C.GL.arc([cx-R-4,cy-R-4,cx+R+4,cy+R+4],135,end,fill=A(col,a),width=24)
    for wm in (8,10):
        ang=math.radians(135+270*wm/10); d.line([(cx+(R-26)*math.cos(ang),cy+(R-26)*math.sin(ang)),(cx+(R+14)*math.cos(ang),cy+(R+14)*math.sin(ang))],fill=A(WHITE,a),width=3)
    txt(d,cx,cy-58,'E2',f(BEB,52),WHITE,a,'mm')
    if not locked:
        seed=int(t*12); val=f'{(seed*37)%90+10:02d}' if t>=32.9 else '--'
        txt(d,cx,cy+4,val,f(BEB,80),AMBER,a*(0.6+0.4*((seed%3)>0)),'mm'); txt(d,cx,cy+60,'UNSTABLE',f(MONO,22),AMBER,a,'mm')
    else:
        la=ap(t,39.52,0.12); txt(d,cx,cy+4,'TRUE',f(BEB,80),GREEN,a*la,'mm'); txt(d,cx,cy+60,'STEADY STATE',f(MONO,22),GREEN,a*la,'mm')
    stxt(d,566,300,'WEEK',f(MONO,24),MUTED,a); stxt(d,566,330,f'{int(wk) if wk<9.95 else 10}',f(BEB,96),WHITE,a)
    if t>=35.44:
        ra=ap(t,35.44); stxt(d,566,448,'READING',f(MONO,22),MUTED,a*ra); tag(d,566,478,'LOCKED' if locked else 'UNKNOWN',GREEN if locked else AMBER,22,a*ra)
