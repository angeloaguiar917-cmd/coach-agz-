# @coach.agz — "Prolactin / 19-nor lactation" Reel renderer (1080x1920, 30 fps)
# Graphics are timed in SOURCE time; each output frame is drawn at its source moment (trim map).
import json, subprocess, sys, math, os
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
WK=os.path.dirname(os.path.abspath(__file__))+'/'
FD=WK+'../F/'
W,H=1080,1920; FPS=30
TR=json.load(open(WK+'trim.json')); KEEP=TR['keep']; REMOVE=TR['remove']
OUT_N=int(round(sum(b-a for a,b in KEEP)*FPS))
CUTS=sorted(set(round(b,4) for a,b in REMOVE if a>0))
def new_to_old(tn):
    acc=0
    for a,b in KEEP:
        if tn < acc+(b-a)-1e-9: return a+(tn-acc)
        acc+=b-a
    return KEEP[-1][1]-1/FPS
def old_to_new(to):
    acc=0
    for a,b in KEEP:
        if to<b: return acc+max(0,to-a)
        acc+=b-a
    return acc
# ---------------- palette / fonts ----------------
GOLD=(201,169,110); CREAM=(244,241,234); NAVY=(14,17,23); MUTED=(184,184,188); MUTED2=(124,124,130)
RED=(255,34,28); VGOLD=(255,194,26); CYAN=(0,229,255); GREEN=(30,255,110); DEEP=(2,3,8); INK=(6,8,14); WHITE=(255,255,255)
AMBER=(240,160,48); BLUE=(79,163,224); PAPER=(232,226,212); PINK=(255,90,140)
BEB='bebas-neue-latin-400-normal.woff'; BAR='barlow-condensed-latin-800-normal.woff'; BAR7='barlow-condensed-latin-700-normal.woff'
DMB='dm-sans-latin-700-normal.woff'; DMR='dm-sans-latin-400-normal.woff'; MONO='jetbrains-mono-latin-500-normal.woff'; MONOB='jetbrains-mono-latin-800-normal.woff'
_fc={}
def f(n,s):
    k=(n,int(s))
    if k not in _fc: _fc[k]=ImageFont.truetype(FD+n,int(s))
    return _fc[k]
def clamp(x,a=0,b=1): return max(a,min(b,x))
def expo(x): x=clamp(x); return 1 if x>=1 else 1-2**(-10*x)
def ease_io(x): x=clamp(x); return 4*x**3 if x<.5 else 1-(-2*x+2)**3/2
def back(x,s=1.2): x=clamp(x); return 1+(s+1)*(x-1)**3+s*(x-1)**2   # heavy settle (small)
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
    if x1<=x0: return
    for i in range(h):
        k=i/h; c=tuple(int(min(255,v*(1.18-0.36*k)+(40 if k<0.12 else 0))) for v in col)
        d.line([(x0,y0+i),(x1,y0+i)],fill=c+(int(255*a),))
def tag(d,x,y,label,col=RED,size=30,a=1.0,glow=True,tc=None):
    fn=f(MONOB,size); tw=d.textlength(label,font=fn); h=size+18
    lit_bar(d,x,y,x+tw+28,y+h,col,a)
    d.text((x+14,y+6),label,font=fn,fill=A(tc or (WHITE if col not in (VGOLD,GREEN,CYAN) else INK),a))
    if GL and glow: GL.rectangle([x-4,y-4,x+tw+32,y+h+4],outline=A(col,a),width=8)
    return x+tw+28
def tag_w(d,label,size=30): return d.textlength(label,font=f(MONOB,size))+28
def txt(d,x,y,s,font,col,a=1.0,anchor=None):
    d.text((x,y),s,font=font,fill=A(col,a),anchor=anchor)
def arrow(d,x0,y0,x1,y1,col,w=5,a=1.0,L=20):
    d.line([(x0,y0),(x1,y1)],fill=A(col,a),width=w)
    ang=math.atan2(y1-y0,x1-x0)
    d.polygon([(x1,y1),(x1-L*math.cos(ang-0.45),y1-L*math.sin(ang-0.45)),(x1-L*math.cos(ang+0.45),y1-L*math.sin(ang+0.45))],fill=A(col,a))
    if GL: GL.line([(x0,y0),(x1,y1)],fill=A(col,a*0.7),width=w+6)
def draw_arrow_prog(d,x0,y0,x1,y1,p,col,w=5,a=1.0):
    if p<=0: return
    xe,ye=lerp(x0,x1,p),lerp(y0,y1,p); arrow(d,x0,y0,xe,ye,col,w,a)
def flow(d,x0,y0,x1,y1,t,col,n=5,speed=0.9,a=1.0,r=7):
    for k in range(n):
        p=(t*speed+k/n)%1
        x=lerp(x0,x1,p); y=lerp(y0,y1,p); fa=a*min(1,p*6,(1-p)*6)
        d.ellipse([x-r,y-r,x+r,y+r],fill=A(col,fa))
        if GL: GL.ellipse([x-r*2,y-r*2,x+r*2,y+r*2],fill=A(col,fa))
def check(d,x,y,col,s=1.0,a=1.0,w=7):
    d.line([(x,y),(x+12*s,y+12*s),(x+34*s,y-14*s)],fill=A(col,a),width=w,joint='curve')
    if GL: GL.line([(x,y),(x+12*s,y+12*s),(x+34*s,y-14*s)],fill=A(col,a),width=w+6)
def kicker(d,x,y,label,t,t0,col=GOLD,size=28,right=False):
    p=ap(t,t0,0.22)
    if p<=0: return
    fn=f(MONOB,size); tw=d.textlength(label,font=fn)
    L=56*p
    if not right:
        d.line([(x,y+size*0.55),(x+L,y+size*0.55)],fill=A(col,1),width=4)
        n=int(len(label)*clamp((t-t0-0.08)/0.25)); d.text((x+72,y),label[:n],font=fn,fill=A(col,1))
    else:
        d.line([(x-L,y+size*0.55),(x,y+size*0.55)],fill=A(col,1),width=4)
        n=int(len(label)*clamp((t-t0-0.08)/0.25)); d.text((x-72-tw,y),label[:n],font=fn,fill=A(col,1))
def frosted(im,box,dark=0.86,blur=10,radius=0):
    x0,y0,x1,y1=[int(v) for v in box]
    x0=max(0,x0); y0=max(0,y0); x1=min(W,x1); y1=min(H,y1)
    if x1<=x0 or y1<=y0: return
    reg=im.crop((x0,y0,x1,y1)).convert('RGB')
    sm=reg.resize((max(1,reg.width//4),max(1,reg.height//4))).filter(ImageFilter.GaussianBlur(blur/4)).resize(reg.size)
    out=Image.blend(sm,Image.new('RGB',reg.size,DEEP),dark).convert('RGBA')
    if radius:
        m=Image.new('L',reg.size,0); ImageDraw.Draw(m).rounded_rectangle([0,0,reg.width-1,reg.height-1],radius=radius,fill=255)
        im.paste(out,(x0,y0),m)
    else: im.paste(out,(x0,y0))
def scene_alpha(t,t0,t1,din=0.20,dout=0.16):
    return min(ap(t,t0,din), 1-clamp((t-t1)/dout))
# ---------------- face track ----------------
_FT=np.array(json.load(open(WK+'face.json')))
def _smooth():
    ts=np.arange(0,105,1/30)
    cx=np.interp(ts,_FT[:,0],_FT[:,1]); cy=np.interp(ts,_FT[:,0],_FT[:,2]); fw=np.interp(ts,_FT[:,0],_FT[:,3])
    k=np.ones(31)/31
    sm=lambda v: np.convolve(np.pad(v,15,mode='edge'),k,'valid')
    return ts,sm(cx),sm(cy),sm(fw)
_TS,_CX,_CY,_FW=_smooth()
def face_at(t):
    i=int(clamp(t*30,0,len(_TS)-1)); return _CX[i],_CY[i]+30,max(520,_FW[i])
# ---------------- shared bg for full-screen scenes ----------------
def pushed_bg(src,g):
    sm=src.resize((W//6,H//6),Image.BILINEAR).filter(ImageFilter.GaussianBlur(3*g+0.01)).resize((W,H),Image.BILINEAR)
    b=Image.blend(src,sm,min(1,g*1.6))
    return Image.blend(b,Image.new('RGB',(W,H),(5,8,16)),0.70*g)
def pip(im,src,t,g,shape,center,R):
    """Footage collapses into a framed PiP; face stays big and recognizable."""
    fx,fy,fw=face_at(t)
    side=fw*1.45
    if shape=='circle': tw_,th_=2*R,2*R
    else: tw_,th_=R[0],R[1]
    s=lerp(1.0,max(tw_,th_)/ (side if shape=='circle' else side*th_/tw_*0.92),ease_io(g))
    cx=lerp(fx,center[0],ease_io(g)); cy=lerp(fy,center[1],ease_io(g))
    big=src.resize((max(1,int(W*s)),max(1,int(H*s))),Image.BICUBIC)
    ox=int(cx-fx*s); oy=int(cy-fy*s)
    lay=Image.new('RGB',(W,H),(0,0,0)); lay.paste(big,(ox,oy))
    m=Image.new('L',(W,H),0); md=ImageDraw.Draw(m)
    if shape=='circle':
        r=lerp(1500,R,ease_io(g)); md.ellipse([cx-r,cy-r,cx+r,cy+r],fill=255)
        box=(cx-r,cy-r,cx+r,cy+r)
    else:
        hw=lerp(1500,tw_/2,ease_io(g)); hh=lerp(1500,th_/2,ease_io(g)); md.rounded_rectangle([cx-hw,cy-hh,cx+hw,cy+hh],radius=int(lerp(0,30,g)),fill=255)
        box=(cx-hw,cy-hh,cx+hw,cy+hh)
    # drop shadow
    sh=Image.new('RGBA',(W,H),(0,0,0,0)); ImageDraw.Draw(sh).ellipse([box[0]+10,box[1]+22,box[2]+10,box[3]+22],fill=(0,0,0,int(150*g))) if shape=='circle' else ImageDraw.Draw(sh).rounded_rectangle([box[0]+10,box[1]+22,box[2]+10,box[3]+22],radius=30,fill=(0,0,0,int(150*g)))
    im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(18)))
    im.paste(lay.convert('RGBA'),(0,0),m)
    d=ImageDraw.Draw(im,'RGBA')
    if g>0.6:
        a=clamp((g-0.6)/0.4)
        if shape=='circle':
            d.ellipse(box,outline=A(VGOLD,a),width=6)
            if GL: GL.ellipse(box,outline=A(VGOLD,a*0.9),width=12)
        else:
            d.rounded_rectangle(box,radius=30,outline=A(VGOLD,a),width=6)
            if GL: GL.rounded_rectangle(box,radius=30,outline=A(VGOLD,a*0.9),width=12)
    return box
# =====================================================================
# 1  SOCIAL POST MOCKUP (callback later)
# =====================================================================
POSTBOX=(96,262,984,632)
def post_card(im,t,t0,a_in=1.0,yoff=0,verdict=None):
    x0,y0,x1,y1=POSTBOX; y0+=yoff; y1+=yoff
    frosted(im,(x0,y0,x1,y1),0.80,10,radius=30)
    lay=Image.new('RGBA',(W,H),(0,0,0,0)); d=ImageDraw.Draw(lay,'RGBA')
    d.rounded_rectangle([x0,y0,x1,y1],radius=30,outline=A((90,92,104),1),width=2)
    # header
    d.ellipse([x0+30,y0+26,x0+90,y0+86],fill=A((70,74,88),1)); d.ellipse([x0+48,y0+36,x0+72,y0+60],fill=A((150,150,160),1)); d.pieslice([x0+38,y0+56,x0+82,y0+100],180,360,fill=A((150,150,160),1))
    txt(d,x0+108,y0+30,'@anon.lifter',f(DMB,34),WHITE); txt(d,x0+108,y0+68,'Original audio',f(DMR,22),MUTED2)
    for k in range(3): d.ellipse([x1-70+k*16,y0+52,x1-62+k*16,y0+60],fill=A(MUTED,1))
    # thumbnail
    tx0,ty0,tx1,ty1=x0+30,y0+112,x0+250,y1-26
    d.rounded_rectangle([tx0,ty0,tx1,ty1],radius=16,fill=A((22,26,36),1))
    cx,cy=(tx0+tx1)/2,(ty0+ty1)/2
    d.polygon([(cx-22,cy-30),(cx-22,cy+30),(cx+30,cy)],fill=A(WHITE,0.85))
    # milk droplet (depiction)
    dx,dy=tx1-46,ty0+46
    d.ellipse([dx-16,dy,dx+16,dy+32],fill=A(WHITE,0.9)); d.polygon([(dx-14,dy+10),(dx+14,dy+10),(dx,dy-18)],fill=A(WHITE,0.9))
    # caption = part of the object
    cfn=f(DMB,66); txt(d,x0+282,y0+128,'elite gains',cfn,WHITE)
    cw=d.textlength('elite gains',font=cfn)
    txt(d,x0+284,y0+214,'#enhanced  #bulk  #gains',f(DMR,26),BLUE)
    # engagement row (icons only)
    ey=y1-82
    hx=x0+290; d.ellipse([hx,ey,hx+22,ey+22],fill=A(RED,1)); d.ellipse([hx+18,ey,hx+40,ey+22],fill=A(RED,1)); d.polygon([(hx+1,ey+14),(hx+39,ey+14),(hx+20,ey+40)],fill=A(RED,1))
    d.rounded_rectangle([hx+60,ey+8,hx+150,ey+26],radius=8,fill=A((70,74,88),1))
    bx=hx+200; d.ellipse([bx,ey,bx+40,ey+36],outline=A(WHITE,1),width=4); d.polygon([(bx+4,ey+30),(bx+2,ey+44),(bx+16,ey+34)],fill=A(WHITE,1))
    d.rounded_rectangle([bx+60,ey+8,bx+130,ey+26],radius=8,fill=A((70,74,88),1))
    sx=bx+180; d.polygon([(sx,ey+18),(sx+40,ey),(sx+28,ey+40)],outline=A(WHITE,1),width=4)
    if GL: GL.ellipse([hx-6,ey-6,hx+46,ey+46],fill=A(RED,0.4*a_in))
    # forensic flag on the caption
    fb=(x0+266,y0+122,x0+300+cw,y0+206)
    if verdict is None:
        p=ap(t,2.26,0.14)
        if p>0:
            brackets(d,*fb,A(RED,1),26,7)
            if GL: brackets(GL,*fb,A(RED,1),26,12)
            if t>2.70: tag(d,fb[2]-tag_w(d,'MISLABELED',26),fb[3]+8,'MISLABELED',size=26)
    al=a_in
    if al<1: lay.putalpha(lay.split()[3].point(lambda v:int(v*al)))
    im.alpha_composite(lay)
    return fb
def s_post(im,t):
    t0,t1=0.90,3.55
    if not (t0<=t<t1+0.16): return
    pin=ap(t,t0,0.24); pout=clamp((t-t1)/0.16)
    post_card(im,t,t0,a_in=pin*(1-pout),yoff=int(lerp(40,0,pin)-24*pout))
def s_verdict(im,t):
    t0,t1=83.92,87.55
    if not (t0<=t<t1+0.16): return
    pin=ap(t,t0,0.18); pout=clamp((t-t1)/0.16); a=pin*(1-pout)
    fb=post_card(im,t,t0,a_in=a,yoff=int(lerp(-60,0,pin)),verdict=True)
    d=ImageDraw.Draw(im,'RGBA')
    p=expo((t-84.40)/0.12)
    if p>0:
        x0,x1=POSTBOX[0]-14,lerp(POSTBOX[0]-14,POSTBOX[2]+14,p); y=POSTBOX[1]+150
        GL.rectangle([x0-4,y-8,x1+4,y+108],outline=A(RED,a),width=10)
        lit_bar(d,x0,y,x1,y+100,RED,a); d.rectangle([x0,y+96,x1,y+100],fill=A((140,0,0),a))
        if p>0.6:
            fn=f(BEB,92); txt(d,x0+34,y+6,'NOT ELITE GAINS',fn,WHITE,a)
    if t>=85.96:
        q=ap(t,85.96,0.18); x=POSTBOX[0]+lerp(-40,0,q)
        tag(d,x,POSTBOX[3]+14,'UNMANAGED 19-NOR',VGOLD,30,a*q)
VERDICT_T=84.40+0.12

# =====================================================================
# 1b VIDEO TILES (prior uploads) + ENGAGEMENT METER
# =====================================================================
def s_tiles(im,t):
    t0,t1=4.40,9.90
    if not (t0<=t<t1+0.16): return
    a=scene_alpha(t,t0,t1,0.2)
    lay=Image.new('RGBA',(W,H),(0,0,0,0)); d=ImageDraw.Draw(lay,'RGBA')
    kicker(d,70,270,'ALREADY POSTED',t,t0,VGOLD,26)
    tiles=[(4.64,'TROLL VIDEO',-4,90),(5.40,'REACTION VIDEO',3,330)]
    for ts,lab,rot,x in tiles:
        if t<ts: continue
        p=expo((t-ts)/0.2)
        tw_,th_=210,300
        tl=Image.new('RGBA',(tw_+40,th_+40),(0,0,0,0)); td=ImageDraw.Draw(tl,'RGBA')
        td.rounded_rectangle([20,20,20+tw_,20+th_],radius=18,fill=(14,16,24,240),outline=(90,92,104,255),width=3)
        td.rounded_rectangle([34,34,6+tw_,20+th_-80],radius=12,fill=(30,34,46,255))
        cx,cy=20+tw_/2,20+(th_-80)/2+8
        td.polygon([(cx-20,cy-26),(cx-20,cy+26),(cx+26,cy)],fill=(255,255,255,220))
        td.text((34,th_-44),lab,font=f(BAR,30),fill=(255,255,255,255))
        td.rounded_rectangle([34,th_-6,34+90,th_+8],radius=7,fill=(70,74,88,255))
        tl=tl.rotate(rot,resample=Image.BICUBIC,expand=True)
        yo=int(lerp(-50,0,p))
        al=tl.split()[3].point(lambda v:int(v*p)); tl.putalpha(al)
        lay.alpha_composite(tl,(x,316+yo))
        if t>=ts+0.25:
            q=ap(t,ts+0.25,0.12); check(d,x+tw_-10,330+yo,GREEN,1.0,q)
            if GL: GL.ellipse([x+tw_-20,300+yo,x+tw_+40,360+yo],fill=A(GREEN,0.4*q*a))
    # engagement meter
    if t>=7.70:
        q=ap(t,7.70,0.2); mx0,my0,mx1,my1=620,360,1000,620
        d.rounded_rectangle([mx0,my0,mx1,my1],radius=18,fill=A((2,3,8),0.88*q),outline=A(VGOLD,q),width=3)
        if GL: GL.rounded_rectangle([mx0,my0,mx1,my1],radius=18,outline=A(VGOLD,0.6*q*a),width=8)
        txt(d,mx0+24,my0+20,'ENGAGEMENT',f(MONOB,26),VGOLD,q)
        bars=[0.35,0.5,0.42,0.7,0.62,0.9,1.0]
        g=ease_io((t-8.32)/0.8)
        for k,b in enumerate(bars):
            bx=mx0+30+k*48; hh=150*b*max(0.15,g)
            lit_bar(d,bx,my1-30-hh,bx+34,my1-30,VGOLD if k<6 else RED,q)
        if t>=8.70: tag(d,mx0+150,my0+64,'BAIT',RED,26,ap(t,8.70,0.14))
    lay.putalpha(lay.split()[3].point(lambda v:int(v*a)))
    im.alpha_composite(lay)
# =====================================================================
# 2  TOGGLE SWITCH  flex -> warning sign
# =====================================================================
def s_toggle(im,t):
    t0,t1=13.25,16.70
    if not (t0<=t<t1+0.16): return
    a=scene_alpha(t,t0,t1,0.22)
    lay=Image.new('RGBA',(W,H),(0,0,0,0)); d=ImageDraw.Draw(lay,'RGBA')
    # soft dark strip (no panel)
    sh=Image.new('RGBA',(W,H),(0,0,0,0)); ImageDraw.Draw(sh).rounded_rectangle([140,300,940,600],radius=80,fill=(2,3,8,190))
    im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(30)))
    kicker(d,150,300,'SIGNAL CHECK',t,t0)
    x0,y0,x1,y1=150,380,930,520; r=(y1-y0)/2
    sw=ease_io((t-14.70)/0.20)
    tc=tuple(int(lerp(a_,b_,sw)) for a_,b_ in zip((34,36,46),(0,0,0)))
    d.rounded_rectangle([x0,y0,x1,y1],radius=r,fill=A(tc,1),outline=A((90,92,104) if sw<0.5 else RED,1),width=4)
    if sw>0:
        lay2=Image.new('RGBA',(W,H),(0,0,0,0)); d2=ImageDraw.Draw(lay2,'RGBA')
        xr=lerp(x0+r,x1,sw); lit_bar(d2,x0,y0,xr,y1,RED,1)
        m=Image.new('L',(W,H),0); ImageDraw.Draw(m).rounded_rectangle([x0,y0,x1,y1],radius=r,fill=255)
        lay.paste(lay2,(0,0),m); d=ImageDraw.Draw(lay,'RGBA')
        GL.rounded_rectangle([x0,y0,x1,y1],radius=r,outline=A(RED,sw*a),width=12)
    fl=f(BEB,80)
    fw=d.textlength('FLEX',font=fl); ws='WARNING SIGN'; ww=d.textlength(ws,font=fl)
    if sw<1: txt(d,(x0+2*r+x1)/2-fw/2,y0+26,'FLEX',fl,WHITE,1-sw)
    if sw>0: txt(d,(x0+x1-2*r)/2-ww/2,y0+26,ws,fl,WHITE,sw)
    lf=f(MONOB,24)
    txt(d,x0+10,y1+16,'FLEX',lf,(150,150,160)); lw=d.textlength('WARNING SIGN',font=lf); txt(d,x1-10-lw,y1+16,'WARNING SIGN',lf,RED if sw>0.5 else (150,150,160))
    if t>=16.02:
        p=ap(t,16.02,0.14); mw=d.textlength('FLEX',font=lf)
        d.line([(x0+4,y1+31),(x0+4+(mw+14)*p,y1+31)],fill=A(RED,1),width=5)
        tag(d,x0+mw+30,y1+8,'NOT A FLEX',RED,22,p)
    # knob with hazard icon
    kx=lerp(x0+r,x1-r,sw); ky=y0+r
    d.ellipse([kx-r+10,ky-r+10,kx+r-10,ky+r-10],fill=A(WHITE if sw>0.5 else (150,150,160),1))
    hz=1 if sw>0.5 else 0.4
    d.polygon([(kx,ky-34),(kx-36,ky+28),(kx+36,ky+28)],fill=A(RED if sw>0.5 else (90,90,100),1))
    d.rectangle([kx-4,ky-14,kx+4,ky+10],fill=A(WHITE,hz)); d.rectangle([kx-4,ky+15,kx+4,ky+22],fill=A(WHITE,hz))
    if sw>0.5 and GL: GL.ellipse([kx-r,ky-r,kx+r,ky+r],fill=A(RED,0.6*a))
    lay.putalpha(lay.split()[3].point(lambda v:int(v*a)))
    im.alpha_composite(lay)
SWITCH_T=14.70+0.20
# =====================================================================
# 3  STEPPER  (01 mechanism -> 02 simple version), callback at 74.8
# =====================================================================
def stepper(im,t,t0,t1,phase):
    if not (t0<=t<t1+0.16): return
    a=scene_alpha(t,t0,t1,0.20)
    lay=Image.new('RGBA',(W,H),(0,0,0,0)); d=ImageDraw.Draw(lay,'RGBA')
    y=350; x0=8; grow=ap(t,t0,0.30)
    # the gold edge rule grows out into the track (handoff from the brand rule)
    xe=lerp(x0,980,grow)
    d.rounded_rectangle([40,y-92,1000,y+112],radius=26,fill=A((2,3,8),0.82))
    d.line([(x0,y+30),(xe,y+30)],fill=A((70,64,48),1),width=6)
    n1,n2=(120,y+30),(920,y+30)
    if phase==1:
        p1=ap(t,18.44,0.2); lit=lerp(0,1,p1)
        prog=clamp((t-19.30)/0.45)
    else:
        lit=1; prog=1
    d.line([(n1[0],y+30),(lerp(n1[0],n2[0],ease_io(prog)),y+30)],fill=A(VGOLD,1),width=8)
    if GL: GL.line([(n1[0],y+30),(lerp(n1[0],n2[0],ease_io(prog)),y+30)],fill=A(VGOLD,0.8*a),width=14)
    R=40
    d.ellipse([n1[0]-R,n1[1]-R,n1[0]+R,n1[1]+R],fill=A(VGOLD if (lit>0.5 and phase==1) else ((10,40,22) if phase==2 else (30,30,36)),1),outline=A(VGOLD if phase==1 else GREEN,1),width=5)
    if phase==2: check(d,n1[0]-18,n1[1]+2,GREEN,1.0)
    else: txt(d,n1[0],n1[1],'01',f(BEB,48),INK if lit>0.5 else WHITE,anchor='mm')
    on2 = phase==2 and t>=75.58
    if phase==2:
        p2=ap(t,75.58,0.18)
        d.ellipse([n2[0]-R-6*p2,n2[1]-R-6*p2,n2[0]+R+6*p2,n2[1]+R+6*p2],fill=A(VGOLD if on2 else (30,30,36),1),outline=A(VGOLD,1),width=5)
        if on2 and GL: GL.ellipse([n2[0]-R-12,n2[1]-R-12,n2[0]+R+12,n2[1]+R+12],fill=A(VGOLD,0.6*a))
    else:
        pulse=0.5+0.5*math.sin(t*9) if prog>=1 else 0
        d.ellipse([n2[0]-R,n2[1]-R,n2[0]+R,n2[1]+R],fill=A((30,30,36),1),outline=A(VGOLD,0.35+0.5*pulse*(prog>=1)),width=5)
    txt(d,n2[0],n2[1],'02',f(BEB,48),INK if on2 else WHITE,anchor='mm')
    lf=f(BAR,50)
    txt(d,n1[0]-R,y-84,'MECHANISM',lf,WHITE if phase==1 else (150,150,160))
    txt(d,n1[0]+R+18,y+52,'STEP 01 · '+('NOW' if phase==1 else 'DONE'),f(MONO,22),VGOLD if phase==1 else GREEN)
    txt(d,n2[0]-R-10,y-38,'SIMPLE VERSION',lf,(WHITE if (phase==2) else (150,150,160)),anchor='ra' if False else None) if False else None
    sv='SIMPLE VERSION'; svw=d.textlength(sv,font=lf)
    txt(d,n2[0]+R-svw,y-84,sv,lf,(WHITE if phase==2 else (150,150,160)))
    st='STEP 02 · '+('NOW' if phase==2 else 'NEXT'); stw=d.textlength(st,font=f(MONO,22))
    txt(d,n2[0]-R-18-stw,y+52,st,f(MONO,22),VGOLD if phase==2 else MUTED2)
    lay.putalpha(lay.split()[3].point(lambda v:int(v*a)))
    im.alpha_composite(lay)
def s_step1(im,t): stepper(im,t,17.30,20.70,1)
def s_step2(im,t): stepper(im,t,74.86,76.80,2)
# =====================================================================
# 4  BAR CHART  (relative prolactin output)
# =====================================================================
def evidence_frame(im,t,box,a,title,fig):
    x0,y0,x1,y1=box
    d=ImageDraw.Draw(im,'RGBA')
    d.rectangle([x0,y0,x1,y1],outline=A(VGOLD,0.75*a),width=3); brackets(d,x0,y0,x1,y1,A(VGOLD,a),46,7)
    GL.rectangle([x0,y0,x1,y1],outline=A(VGOLD,0.45*a),width=6); brackets(GL,x0,y0,x1,y1,A(VGOLD,a),46,14)
    d.ellipse([x0+26,y0+26,x0+42,y0+42],fill=A(RED,a if int(t*4)%2==0 else a/3))
    txt(d,x0+56,y0+18,title,f(MONO,26),WHITE,a); fr=f(MONO,26); tw=d.textlength(fig,font=fr); txt(d,x1-30-tw,y0+18,fig,fr,VGOLD,a)
def s_bars(im,t):
    t0,t1=21.00,28.00
    if not (t0<=t<t1+0.16): return
    box=(60,252,1020,668)
    pin=ap(t,t0,0.22); pout=clamp((t-t1)/0.16); a=pin*(1-pout)
    frosted(im,box,0.90,10)
    lay=Image.new('RGBA',(W,H),(0,0,0,0)); d=ImageDraw.Draw(lay,'RGBA')
    bx0,bx1=450,980
    rows=[(350,'NURSING MOTHER','MILK PRODUCTION ON',22.42,0.97,CYAN,23.10),(498,'ADULT MALE','WAY SMALLER',25.46,0.13,VGOLD,27.20)]
    for y,lab,note,ts,frac,col,tn in rows:
        if t<ts-0.3: continue
        la=ap(t,ts-0.3,0.18)
        txt(d,100,y+8,lab,f(BAR,46),WHITE,la)
        d.rectangle([bx0,y,bx1,y+70],fill=A((20,22,30),la),outline=A((60,62,74),la),width=2)
        g=ease_io((t-ts)/0.9)*frac
        if g>0:
            lit_bar(d,bx0+3,y+3,lerp(bx0+3,bx1-3,g),y+67,col,la)
            GL.rectangle([bx0+3,y+3,lerp(bx0+3,bx1-3,g),y+67],fill=A(col,0.55*la*a))
        if t>=tn:
            q=ap(t,tn,0.16); w_=tag_w(d,note,24)
            xx=lerp(bx0+3,bx1-3,frac)+16 if frac<0.5 else bx1-w_
            yy=y+11 if frac<0.5 else y+80
            tag(d,xx,yy,note,RED if frac<0.5 else CYAN,24,q)
    # axis
    d.line([(bx0,630),(bx1,630)],fill=A((90,92,104),1),width=2)
    for k in range(6): xx=lerp(bx0,bx1,k/5); d.line([(xx,624),(xx,636)],fill=A((90,92,104),1),width=2)
    txt(d,bx0,640-4,'LOW',f(MONO,20),MUTED2); txt(d,bx1-46,640-4,'HIGH',f(MONO,20),MUTED2)
    lay.putalpha(lay.split()[3].point(lambda v:int(v*a)))
    if pin<1: lay=lay.filter(ImageFilter.GaussianBlur(6*(1-pin)))
    im.alpha_composite(lay)
    evidence_frame(im,t,box,a,'PROLACTIN · RELATIVE OUTPUT','FIG 01')
# =====================================================================
# 5  COMPOUND CHIPS (heavy tag blocks)
# =====================================================================
CHIPS=[('DECA',29.66),('NPP',30.12),('TREN',30.90)]
def s_chips(im,t):
    t0,t1=28.55,32.52
    if not (t0<=t<t1+0.2): return
    lay=Image.new('RGBA',(W,H),(0,0,0,0)); d=ImageDraw.Draw(lay,'RGBA')
    sh=Image.new('RGBA',(W,H),(0,0,0,0)); ImageDraw.Draw(sh).rectangle([40,280,1040,600],fill=(2,3,8,150))
    a=1-clamp((t-t1)/0.2)
    im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(36)).point(lambda v:v) if a>=1 else Image.blend(Image.new('RGBA',(W,H),(0,0,0,0)),sh.filter(ImageFilter.GaussianBlur(36)),a))
    kicker(d,70,300,'19-NOR CLASS',t,t0,VGOLD,30)
    x=70; fn=f(BEB,124)
    for k,(nm,ts) in enumerate(CHIPS):
        if t<ts: break
        p=expo((t-ts)/0.16); tw=d.textlength(nm,font=fn); wch=tw+64
        xo=lerp(-wch-60,0,p)
        # exit: chips fly right into the mechanism (handoff)
        if t>t1: xo+= (t-t1)/0.2*1200*(1+k*0.3)
        y=372
        lit_bar(d,x+xo,y,x+xo+wch,y+140,RED,1)
        d.rectangle([x+xo,y+134,x+xo+wch,y+140],fill=A((120,0,0),1))
        txt(d,x+xo+32,y+12,nm,fn,WHITE)
        GL.rectangle([x+xo-4,y-4,x+xo+wch+4,y+144],outline=A(RED,0.9*a),width=10)
        if t>=31.70:
            pl=0.5+0.5*math.cos((t-31.70)*14)
            d.rectangle([x+xo-6,y-6,x+xo+wch+6,y+146],outline=A(VGOLD,pl),width=4)
        x+=wch+30
    if t>=31.70:
        q=ap(t,31.70,0.16); tag(d,70,540,'THE PROBLEM CLASS',VGOLD,28,q*a)
    lay.putalpha(lay.split()[3].point(lambda v:int(v*a)))
    im.alpha_composite(lay)
CHIP_TS=[c[1] for c in CHIPS]
# =====================================================================
# 6  MECHANISM 01 (full-screen, circle PiP top-right)
# =====================================================================
def mammary_schematic(d,t,ox,oy,p,col=CYAN):
    """Line schematic: ducts branching from the nipple to lobule clusters (X-ray look)."""
    nip=(ox+520,oy+150)
    branches=[(-140,-100),(-170,-10),(-150,90),(-90,150)]
    segs=[]
    for k,(bx,by) in enumerate(branches):
        mid=(nip[0]+bx*0.9,nip[1]+by*0.5); end=(nip[0]+bx*2.2,nip[1]+by*1.1)
        segs.append((nip,mid)); segs.append((mid,end))
        for j,(ux,uy) in enumerate([(-40,-30),(-50,20),(-10,-45)]):
            segs.append((end,(end[0]+ux,end[1]+uy)))
    n=len(segs); m=p*n
    for i,(s0,s1) in enumerate(segs):
        q=clamp(m-i)
        if q<=0: break
        e=(lerp(s0[0],s1[0],q),lerp(s0[1],s1[1],q))
        d.line([s0,e],fill=A(col,1),width=4)
        if GL: GL.line([s0,e],fill=A(col,0.9),width=10)
        if q>=1 and i%4>=1:
            r=13; d.ellipse([s1[0]-r,s1[1]-r,s1[0]+r,s1[1]+r],outline=A(col,1),width=3)
            if GL: GL.ellipse([s1[0]-r,s1[1]-r,s1[0]+r,s1[1]+r],outline=A(col,0.8),width=6)
    # chest wall outline
    if p>0:
        d.ellipse([nip[0]-10,nip[1]-10,nip[0]+10,nip[1]+10],fill=A(col,1))
    return nip
def s_mech(im,src,t):
    t0,t1=32.55,43.78
    if not (t0<=t<t1+0.30): return False
    g=min(ease_io((t-t0)/0.36),1-ease_io((t-t1)/0.28))
    bg=pushed_bg(src,g); im.paste(bg.convert('RGBA'),(0,0))
    pip(im,src,t,g,'circle',(842,446),186)
    if g<0.5: return True
    a=clamp((g-0.5)/0.5)
    lay=Image.new('RGBA',(W,H),(0,0,0,0)); d=ImageDraw.Draw(lay,'RGBA')
    kicker(d,70,276,'MECHANISM 01',t,t0+0.25,VGOLD,28)
    hf=f(BEB,118); txt(d,70,326,'19-NOR',hf,CREAM)
    txt(d,70,436,'PROLACTIN',hf,RED if t>=36.04 else CREAM)
    d.line([(70,560),(70+ lerp(0,520,ap(t,t0+0.4,0.4)),560)],fill=A(VGOLD,1),width=4)
    txt(d,70,580,'RECEPTOR ROUTE · SIGNAL CHAIN',f(MONO,24),MUTED)
    # --- phase A: compound -> PR -> prolactin
    ya=730
    if t>=32.66:
        q=ap(t,32.66,0.2)
        d.rounded_rectangle([60,ya,350,ya+190],radius=18,fill=A((12,10,16),0.95),outline=A(RED,q),width=4)
        GL.rounded_rectangle([60,ya,350,ya+190],radius=18,outline=A(RED,0.8*q),width=8)
        txt(d,205,ya+62,'19-NOR',f(BEB,76),WHITE,q,anchor='mm')
        for k,nm in enumerate(['DECA','NPP','TREN']):
            cx=92+k*88; d.rounded_rectangle([cx,ya+118,cx+80,ya+160],radius=8,fill=A((60,6,10),q),outline=A(RED,q),width=2)
            txt(d,cx+40,ya+139,nm,f(MONOB,20),(255,170,160),q,anchor='mm')
    # receptor dock
    dx,dy=560,ya+40
    if t>=33.60:
        q=ap(t,33.60,0.2); dock=ap(t,34.30,0.10)
        col=CYAN
        d.line([(dx-80,dy),(dx-80,dy+110),(dx+80,dy+110),(dx+80,dy)],fill=A(col,q),width=6,joint='curve')
        d.line([(dx-80,dy),(dx-30,dy)],fill=A(col,q),width=6); d.line([(dx+30,dy),(dx+80,dy)],fill=A(col,q),width=6)
        d.polygon([(dx-30,dy),(dx,dy+50),(dx+30,dy)],outline=A(col,q),width=5) if False else d.line([(dx-30,dy),(dx,dy+50),(dx+30,dy)],fill=A(col,q),width=6)
        GL.line([(dx-80,dy),(dx-80,dy+110),(dx+80,dy+110),(dx+80,dy)],fill=A(col,q*0.9),width=12)
        txt(d,dx,dy+150,'PROGESTERONE',f(MONOB,24),WHITE,q,anchor='mm'); txt(d,dx,dy+180,'RECEPTOR',f(MONOB,24),WHITE,q,anchor='mm')
        # ligand travels in and docks
        lp=ease_io((t-33.86)/0.44)
        if lp>0:
            lx=lerp(352,dx,lp); ly=lerp(ya+95,dy+22,lp)
            d.polygon([(lx,ly-28),(lx+28,ly),(lx,ly+28),(lx-28,ly)],fill=A(RED,1)); GL.polygon([(lx,ly-34),(lx+34,ly),(lx,ly+34),(lx-34,ly)],fill=A(RED,0.8))
        if dock>0:
            fl=max(0,1-(t-34.30)/0.35)
            GL.rectangle([dx-90,dy-10,dx+90,dy+120],fill=A(CYAN,0.6*fl))
            tag(d,dx-62,dy-62,'BOUND',CYAN,24,dock)
    # signal -> prolactin meter
    mx0,my0,mx1,my1=850,ya-10,1000,ya+196
    if t>=35.06:
        q=ap(t,35.06,0.18)
        flow(d,dx+90,dy+55,mx0-10,dy+55,t,RED,5,1.6,q,8)
        arrow(d,dx+90,dy+55,mx0-10,dy+55,RED,4,q*0.6)
    if t>=34.9:
        q=ap(t,34.9,0.2)
        d.rectangle([mx0,my0,mx1,my1],fill=A((10,10,16),0.9*q),outline=A((80,80,90),q),width=2)
        fill=lerp(0.18,0.94,ease_io((t-35.36)/1.2))
        yy=lerp(my1-4,my0+4,fill)
        lit_bar(d,mx0+4,yy,mx1-4,my1-4,RED,q); GL.rectangle([mx0+4,yy,mx1-4,my1-4],fill=A(RED,0.5*q*a))
        txt(d,(mx0+mx1)/2,my1+28,'PROLACTIN',f(MONOB,24),WHITE,q,anchor='mm')
        if t>=36.40:
            arrow(d,(mx0+mx1)/2,my0+120,(mx0+mx1)/2,my0+40,WHITE,8,ap(t,36.40,0.14),26)
    # --- phase B: X-ray of mammary tissue
    yb=1010
    if t>=37.24:
        q=ap(t,37.24,0.2)
        d.rectangle([60,yb-20,1020,1262],fill=A((0,14,20),0.55*q),outline=A((0,90,110),q),width=2)
        txt(d,80,yb-8,'SCAN · TARGET TISSUE',f(MONO,22),CYAN,q)
        sp=clamp((t-37.40)/0.9)
        if sp<1:
            ys=lerp(yb-20,1262,sp); d.line([(60,ys),(1020,ys)],fill=A(CYAN,1),width=3); GL.line([(60,ys),(1020,ys)],fill=A(CYAN,1),width=14)
        nip=mammary_schematic(d,t,180,yb+10,clamp((t-39.8)/1.7))
        if t>=40.74:
            q2=ap(t,40.74,0.2)
            flow(d,(mx0+mx1)/2,my1+50,nip[0]+90,yb+150,t,RED,4,1.4,q2,7)
            draw_arrow_prog(d,(mx0+mx1)/2,my1+50,nip[0]+60,yb+140,ease_io((t-40.74)/0.3),RED,4,0.7)
        if t>=42.62:
            fb=(150,yb+20,700,yb+250); p=ap(t,42.62,0.14)
            brackets(d,*fb,A(RED,p),30,7); GL and brackets(GL,*fb,A(RED,p),30,12)
            if t>=43.10: tag(d,1004-tag_w(d,'MAMMARY GLAND TISSUE',26),1262-62,'MAMMARY GLAND TISSUE',RED,26,ap(t,43.1,0.14))
    lay.putalpha(lay.split()[3].point(lambda v:int(v*a)))
    im.alpha_composite(lay)
    return True
# =====================================================================
# 7  LINE GRAPH (prolactin trend crosses threshold)
# =====================================================================
def s_graph(im,t):
    t0,t1=44.62,55.30
    if not (t0<=t<t1+0.16): return
    box=(60,248,1020,690)
    pin=ap(t,t0,0.22); pout=clamp((t-t1)/0.16); a=pin*(1-pout)
    frosted(im,box,0.90,10,radius=22)
    lay=Image.new('RGBA',(W,H),(0,0,0,0)); d=ImageDraw.Draw(lay,'RGBA')
    x0,y0,x1,y1=box
    d.rounded_rectangle(box,radius=22,outline=A((0,120,140),1),width=3)
    txt(d,x0+28,y0+18,'PROLACTIN · TREND',f(MONOB,26),CYAN)
    rec='LIVE'; d.ellipse([x1-118,y0+28,x1-102,y0+44],fill=A(RED,1 if int(t*4)%2==0 else 0.3)); txt(d,x1-90,y0+18,rec,f(MONOB,26),WHITE)
    px0,py0,px1,py1=x0+90,y0+80,x1-40,y1-60
    for k in range(1,6): xx=lerp(px0,px1,k/6); d.line([(xx,py0),(xx,py1)],fill=A((0,70,84),0.7),width=1)
    for k in range(1,4): yy=lerp(py0,py1,k/4); d.line([(px0,yy),(px1,yy)],fill=A((0,70,84),0.7),width=1)
    d.line([(px0,py0),(px0,py1),(px1,py1)],fill=A((120,130,150),1),width=3)
    txt(d,px0,py1+14,'TIME ON 19-NOR  →',f(MONO,22),MUTED2)
    txt(d,x0+24,py0-4,'HIGH',f(MONO,20),MUTED2); txt(d,x0+24,py1-24,'LOW',f(MONO,20),MUTED2)
    thy=lerp(py1,py0,0.55)
    for xx in range(int(px0),int(px1),28): d.line([(xx,thy),(xx+16,thy)],fill=A(AMBER,1),width=3)
    tl='LACTATION THRESHOLD'; tw=d.textlength(tl,font=f(MONOB,22)); txt(d,px1-tw,thy-34,tl,f(MONOB,22),AMBER)
    def yv(u):
        s=clamp((u-0.18)/0.72); s=s*s*(3-2*s)
        return lerp(py1-30,py0+18,s)
    u_end=ease_io((t-45.10)/2.4)
    N=90; pts=[(lerp(px0,px1,u_end*i/N),yv(u_end*i/N)) for i in range(N+1)]
    cross=None
    for i in range(1,len(pts)):
        c=VGOLD if pts[i][1]>thy else RED
        d.line([pts[i-1],pts[i]],fill=A(c,1),width=7)
        GL.line([pts[i-1],pts[i]],fill=A(c,0.9*a),width=12)
        if cross is None and pts[i][1]<=thy: cross=pts[i]
    hx,hy=pts[-1]
    d.ellipse([hx-12,hy-12,hx+12,hy+12],fill=A(WHITE,1)); GL.ellipse([hx-24,hy-24,hx+24,hy+24],fill=A(RED if hy<thy else VGOLD,0.8*a))
    if cross and t>=46.30:
        q=ap(t,46.30,0.14); cx,cy=cross
        d.ellipse([cx-20,cy-20,cx+20,cy+20],outline=A(RED,q),width=5)
        if t>=47.62:
            pl=(t-47.62)%0.8/0.8
            d.ellipse([cx-20-40*pl,cy-20-40*pl,cx+20+40*pl,cy+20+40*pl],outline=A(RED,(1-pl)*q),width=3)
    # droplets = fluid produced
    if cross and t>=49.86:
        cx,cy=cross
        for k in range(4):
            ph=((t-49.86)*0.9+k*0.25)%1
            dx_=cx+60+k*70; dy_=lerp(thy+20,py1-10,ph)
            al=min(1,ph*5,(1-ph)*4)
            d.ellipse([dx_-11,dy_,dx_+11,dy_+22],fill=A(CYAN,al)); d.polygon([(dx_-10,dy_+7),(dx_+10,dy_+7),(dx_,dy_-14)],fill=A(CYAN,al))
            GL.ellipse([dx_-16,dy_-6,dx_+16,dy_+28],fill=A(CYAN,0.7*al*a))
    if t>=51.94:
        q=expo((t-51.94)/0.12)
        sx=lerp(1.25,1.0,q)
        fn=f(BEB,int(76*sx)); lab='GALACTORRHEA'; tw=d.textlength(lab,font=fn)
        bx0=px0+16; by0=py0+4
        lit_bar(d,bx0,by0,bx0+tw+48,by0+fn.size+12,RED,q); txt(d,bx0+24,by0+6,lab,fn,WHITE,q)
        GL.rectangle([bx0-4,by0-4,bx0+tw+52,by0+fn.size+16],outline=A(RED,q*a),width=10)
        if t>=53.38: tag(d,bx0,by0+fn.size+24,'MALE LACTATION',WHITE,24,ap(t,53.38,0.16),tc=INK)
    lay.putalpha(lay.split()[3].point(lambda v:int(v*a)))
    if pin<1: lay=lay.filter(ImageFilter.GaussianBlur(6*(1-pin)))
    im.alpha_composite(lay)
GALAC_T=51.94
# =====================================================================
# 8  GYNO CHAIN (full-screen, circle PiP top-left): dials + balance + target
# =====================================================================
def dial(d,cx,cy,r,val,label,t,a=1.0,state=None,scol=RED):
    segs=[(BLUE,180,225),(GREEN,225,292),(AMBER,292,330),(RED,330,360)]
    for col,s0,s1 in segs:
        d.arc([cx-r,cy-r,cx+r,cy+r],s0,s1,fill=A(col,a),width=22)
        if GL: GL.arc([cx-r,cy-r,cx+r,cy+r],s0,s1,fill=A(col,0.55*a),width=30)
    for k in range(11):
        ang=math.radians(180+k*18); d.line([(cx+(r-40)*math.cos(ang),cy+(r-40)*math.sin(ang)),(cx+(r-28)*math.cos(ang),cy+(r-28)*math.sin(ang))],fill=A(WHITE,0.6*a),width=3)
    ang=math.radians(180+180*val)
    d.line([(cx,cy),(cx+(r-34)*math.cos(ang),cy+(r-34)*math.sin(ang))],fill=A(WHITE,a),width=8)
    d.ellipse([cx-16,cy-16,cx+16,cy+16],fill=A(WHITE,a))
    txt(d,cx,cy+44,label,f(BAR,48),WHITE,a,anchor='mm')
    if state: tag(d,cx-tag_w(d,state,24)/2,cy+80,state,scol,24,a)
def s_gyno(im,src,t):
    t0,t1=55.36,65.86
    if not (t0<=t<t1+0.30): return False
    g=min(ease_io((t-t0)/0.36),1-ease_io((t-t1)/0.28))
    bg=pushed_bg(src,g); im.paste(bg.convert('RGBA'),(0,0))
    pip(im,src,t,g,'circle',(238,446),186)
    if g<0.5: return True
    a=clamp((g-0.5)/0.5)
    lay=Image.new('RGBA',(W,H),(0,0,0,0)); d=ImageDraw.Draw(lay,'RGBA')
    kicker(d,1010,276,'MECHANISM 02',t,t0+0.25,VGOLD,28,right=True)
    hf=f(BEB,150); gw=d.textlength('GYNO',font=hf)
    txt(d,1010-gw,318,'GYNO',hf,RED if t>=57.64 else CREAM)
    if t>=57.64: GL.rectangle([1010-gw,340,1010,450],fill=A(RED,0.25*a))
    pw=d.textlength('PATHWAY',font=f(BEB,80)); txt(d,1010-pw,470,'PATHWAY',f(BEB,80),CREAM)
    txt(d,1010-d.textlength('DOMINO · 4 STEPS',font=f(MONO,24)),570,'DOMINO · 4 STEPS',f(MONO,24),MUTED)
    # row 1 dials
    cy=850
    if t>=58.6:
        q=ap(t,58.6,0.2)
        v=lerp(0.45,0.93,ease_io((t-58.98)/0.5))
        dial(d,280,cy,170,v,'PROLACTIN',t,q,'ELEVATED' if t>=59.3 else None)
    if t>=59.6:
        q=ap(t,59.6,0.2)
        draw_arrow_prog(d,490,cy-60,590,cy-60,ease_io((t-59.6)/0.3),RED,6,q)
        v=lerp(0.62,0.10,ease_io((t-59.98)/0.6))
        dial(d,800,cy,170,v,'DOPAMINE',t,q,'SUPPRESSED' if t>=60.56 else None,BLUE)
    # row 2: balance scale + tissue target
    y2=1150
    if t>=60.95:
        q=ap(t,60.95,0.2)
        draw_arrow_prog(d,700,cy+140,520,y2-80,ease_io((t-60.95)/0.3),RED,5,q)
        tilt=lerp(0,-14,ease_io((t-61.92)/0.5))
        px_,py_=300,y2-40; L=200
        ang=math.radians(tilt)
        lx,ly=px_-L*math.cos(ang),py_+L*math.sin(ang)*-1
        rx,ry=px_+L*math.cos(ang),py_-L*math.sin(ang)*-1
        lx,ly=px_-L*math.cos(ang),py_-L*math.sin(-ang)
        rx,ry=px_+L*math.cos(ang),py_+L*math.sin(-ang)
        d.polygon([(px_-30,py_+120),(px_+30,py_+120),(px_,py_)],fill=A((60,62,74),q))
        d.line([(lx,ly),(rx,ry)],fill=A(WHITE,q),width=8)
        for (xx,yy,lab,col) in [(lx,ly,'E',PINK),(rx,ry,'A',BLUE)]:
            d.line([(xx,yy),(xx,yy+46)],fill=A(WHITE,q*0.7),width=3)
            d.chord([xx-62,yy+20,xx+62,yy+110],0,180,fill=A(col,q))
            GL.chord([xx-62,yy+20,xx+62,yy+110],0,180,fill=A(col,0.5*q*a))
            txt(d,xx,yy+62,lab,f(BEB,52),INK,q,anchor='mm')
        txt(d,px_,py_+150,'ESTROGEN : ANDROGEN',f(MONOB,22),WHITE,q,anchor='mm')
        if t>=63.42: tag(d,px_-tag_w(d,'OFF BALANCE',24)/2,py_-110,'OFF BALANCE',RED,24,ap(t,63.42,0.14))
    if t>=63.76:
        q=ap(t,63.76,0.2)
        draw_arrow_prog(d,560,y2+20,680,y2+20,ease_io((t-63.76)/0.3),RED,6,q)
        tx,ty=860,y2+12
        sens=ap(t,64.06,0.3)
        for k,rr in enumerate([100,74,48,22]):
            col=tuple(int(lerp(c1,c2,sens)) for c1,c2 in zip(CYAN,RED))
            d.ellipse([tx-rr,ty-rr,tx+rr,ty+rr],outline=A(col,q),width=5)
            GL.ellipse([tx-rr,ty-rr,tx+rr,ty+rr],outline=A(col,0.7*q*a),width=10)
        if t>=65.4:
            gr=ease_io((t-65.4)/0.5)
            for k in range(8):
                an=k*math.pi/4; r0=110; r1=110+40*gr
                arrow(d,tx+r0*math.cos(an),ty+r0*math.sin(an),tx+r1*math.cos(an),ty+r1*math.sin(an),RED,4,gr,14)
        txt(d,tx,ty+128,'BREAST TISSUE',f(MONOB,22),WHITE,q,anchor='mm')
        if t>=64.84: tag(d,tx-tag_w(d,'SENSITIZED',24)/2,ty-158,'SENSITIZED',RED,24,ap(t,64.84,0.14))
    lay.putalpha(lay.split()[3].point(lambda v:int(v*a)))
    im.alpha_composite(lay)
    return True
# =====================================================================
# 9  LAB DOCUMENT -> scan wipe -> two-lane PATHWAYS
# =====================================================================
_DOC=None
def make_doc():
    w,h=860,400
    im=Image.new('RGB',(w,h),PAPER); d=ImageDraw.Draw(im)
    rng=np.random.default_rng(3); nz=(rng.standard_normal((h,w))*7).astype(np.int16)
    arr=np.asarray(im).astype(np.int16)+nz[...,None]; im=Image.fromarray(np.clip(arr,0,255).astype(np.uint8)); d=ImageDraw.Draw(im)
    d.rectangle([0,0,w,64],fill=(28,30,38)); d.text((24,16),'LAB REPORT · HORMONE PANEL',font=f(MONOB,26),fill=(240,236,226))
    d.text((w-210,20),'SAMPLE · GENERIC',font=f(MONO,18),fill=(170,170,176))
    d.text((24,84),'BLOODWORK',font=f(MONOB,20),fill=(120,110,96)); d.line([(24,112),(w-24,112)],fill=(170,160,140),width=2)
    d.text((24,128),'Estradiol, sensitive',font=f(MONOB,30),fill=(30,30,34)); d.text((w-260,128),'IN RANGE',font=f(MONOB,30),fill=(20,120,60))
    d.text((24,236),'PHYSICAL EXAM',font=f(MONOB,20),fill=(120,110,96)); d.line([(24,264),(w-24,264)],fill=(170,160,140),width=2)
    d.text((24,280),'Glandular tissue',font=f(MONOB,30),fill=(30,30,34)); d.text((w-260,280),'PALPABLE',font=f(MONOB,30),fill=(150,20,20))
    d.text((24,340),'Under the nipple · firm · growing',font=f(MONO,22),fill=(90,86,80))
    return im
def s_doc(im,t):
    global _DOC
    t0,t1=66.24,74.50
    if not (t0<=t<t1+0.16): return
    if _DOC is None: _DOC=make_doc()
    pout=clamp((t-t1)/0.16)
    wipe=clamp((t-70.96)/0.45)          # doc -> pathways
    box=(110,262,970,662)
    if wipe<1:
        p=expo((t-t0)/0.26)
        doc=_DOC.copy().convert('RGBA'); dd=ImageDraw.Draw(doc,'RGBA')
        if t>=66.70:
            q=ap(t,66.70,0.14); check(dd,780,150,(20,140,70),1.0,q)
            if t>=67.72:
                brackets(dd,14,120,846,186,A((20,160,70),q),22,6)
                tag(dd,520,190,'OPTIMAL ON PAPER',GREEN,22,ap(t,67.72,0.14),glow=False)
        if t>=68.52:
            q=ap(t,68.52,0.14); brackets(dd,14,272,846,376,A(RED,q),22,6)
            if t>=69.14: tag(dd,560,226,'STILL GROWING',RED,22,ap(t,69.14,0.14),glow=False)
        rot=lerp(-7,-2,p); xo=lerp(700,0,p)
        rd=doc.rotate(rot,resample=Image.BICUBIC,expand=True)
        if p<1: rd=rd.filter(ImageFilter.BoxBlur(int(10*(1-p))))
        sh=Image.new('RGBA',(W,H),(0,0,0,0)); ImageDraw.Draw(sh).rectangle([box[0]+xo+14,box[1]+24,box[2]+xo+14,box[3]+24],fill=(0,0,0,150))
        im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(16)))
        ox=int(box[0]+xo-(rd.width-860)/2); oy=int(box[1]-(rd.height-400)/2)
        if wipe>0:
            m=Image.new('L',rd.size,255); ImageDraw.Draw(m).rectangle([0,0,rd.width,int(rd.height*wipe)],fill=0)
            al=rd.split()[3]; rd.putalpha(Image.fromarray(np.minimum(np.asarray(al),np.asarray(m))))
        im.alpha_composite(rd,(ox,oy))
    if wipe>0:
        a=1-pout
        lay=Image.new('RGBA',(W,H),(0,0,0,0)); d=ImageDraw.Draw(lay,'RGBA')
        x0,y0,x1,y1=60,252,1020,672
        yc=lerp(y0,y1,wipe)
        frosted(im,(x0,y0,x1,yc),0.9,10)
        d.rectangle([x0,y0,x1,y1],outline=A((70,72,84),1),width=2)
        txt(d,x0+28,y0+20,'TWO PATHWAYS · SAME BODY',f(MONOB,26),VGOLD)
        # lane A (E2) calm green
        ya=y0+110
        txt(d,x0+30,ya-8,'E2',f(BEB,84),WHITE); txt(d,x0+30,ya+74,'ESTRADIOL',f(MONO,20),MUTED2)
        flow(d,x0+190,ya+36,x1-280,ya+36,t,GREEN,5,0.5,1,7); arrow(d,x0+190,ya+36,x1-280,ya+36,(60,120,80),3)
        tag(d,x1-262,ya+12,'IN RANGE',GREEN,26)
        # lane B (prolactin) hot red
        yb=y0+290
        txt(d,x0+30,yb-8,'PRL',f(BEB,84),RED); txt(d,x0+30,yb+74,'PROLACTIN',f(MONO,20),MUTED2)
        flow(d,x0+190,yb+36,x1-280,yb+36,t,RED,7,1.6,1,9); arrow(d,x0+190,yb+36,x1-280,yb+36,RED,4,0.6)
        tag(d,x1-262,yb+12,'GROWTH',RED,26)
        if t>=73.08:
            q=ap(t,73.08,0.16); ym=(ya+yb)/2+36
            d.line([(x0+20,ym),(lerp(x0+20,x1-20,q),ym)],fill=A(VGOLD,1),width=4); GL.line([(x0+20,ym),(lerp(x0+20,x1-20,q),ym)],fill=A(VGOLD,a),width=10)
            if t>=73.74:
                lw=tag_w(d,'SEPARATE PATHWAY',26); tag(d,(x0+x1)/2-lw/2,ym-24,'SEPARATE PATHWAY',VGOLD,26,ap(t,73.74,0.14))
        if wipe<1:
            d.rectangle([x0,yc,x1,y1],fill=A((0,0,0),0))
            m=Image.new('L',(W,H),0); ImageDraw.Draw(m).rectangle([x0-6,y0-6,x1+6,yc],fill=255)
            lay.putalpha(Image.fromarray(np.minimum(np.asarray(lay.split()[3]),np.asarray(m))))
            ImageDraw.Draw(im).line([(x0,yc),(x1,yc)],fill=CYAN,width=4); GL.line([(x0,yc),(x1,yc)],fill=A(CYAN,1),width=16)
        lay.putalpha(lay.split()[3].point(lambda v:int(v*a)))
        im.alpha_composite(lay)
# =====================================================================
# 11 FORK (one hormone -> two outcomes), free-floating
# =====================================================================
def factory_icon(d,x,y,col,a,on):
    d.rectangle([x,y+40,x+120,y+100],outline=A(col,a),width=4)
    d.polygon([(x,y+40),(x+40,y+14),(x+40,y+40),(x+80,y+14),(x+80,y+40)],outline=A(col,a))
    d.line([(x,y+40),(x+40,y+14),(x+40,y+40),(x+80,y+14),(x+80,y+40),(x+120,y+40)],fill=A(col,a),width=4)
    d.rectangle([x+92,y-14,x+110,y+40],outline=A(col,a),width=4)
    if on:
        for k in range(3):
            ph=(on*1.2+k*0.33)%1; d.ellipse([x+96-8*ph,y-30-40*ph,x+106+8*ph,y-20-40*ph+10*ph],outline=A(col,a*(1-ph)),width=3)
def s_fork(im,t):
    t0,t1=76.70,83.70
    if not (t0<=t<t1+0.16): return
    a=scene_alpha(t,t0,t1,0.2)
    sh=Image.new('RGBA',(W,H),(0,0,0,0)); ImageDraw.Draw(sh).rounded_rectangle([40,250,1040,690],radius=60,fill=(2,3,8,int(200*a)))
    im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(28)))
    lay=Image.new('RGBA',(W,H),(0,0,0,0)); d=ImageDraw.Draw(lay,'RGBA')
    p=back((t-t0)/0.28,0.6)
    fn=f(MONOB,40); lab='PROLACTIN'; tw=d.textlength(lab,font=fn)
    nx=540; ny=lerp(230,272,p)
    lit_bar(d,nx-tw/2-30,ny,nx+tw/2+30,ny+68,VGOLD,1); txt(d,nx,ny+34,lab,fn,INK,anchor='mm')
    GL.rectangle([nx-tw/2-34,ny-4,nx+tw/2+34,ny+72],outline=A(VGOLD,a),width=10)
    if t>=82.70:
        q=ap(t,82.70,0.16); tag(d,nx+tw/2+46,ny+14,'1 HORMONE',WHITE,24,q,tc=INK)
    cards=[(77.92,'LACTATION',CYAN,(70,430,520,672),81.40,'factory'),(78.86,'GYNO',RED,(560,430,1010,672),82.12,'tissue')]
    for ts,lab2,col,(x0,y0,x1,y1),tf,ic in cards:
        if t<ts: continue
        lp=ease_io((t-ts)/0.3)
        sx,sy=nx,ny+68; ex,ey=(x0+x1)/2,y0
        mx,my=sx,sy+40
        d.line([(sx,sy),(sx,lerp(sy,my,min(1,lp*2)))],fill=A(col,1),width=6)
        if lp>0.5:
            k=(lp-0.5)*2; d.line([(mx,my),(lerp(mx,ex,k),my)],fill=A(col,1),width=6);
            if k>=1: arrow(d,ex,my,ex,y0-4,col,6,1,18)
        GL.line([(sx,sy),(sx,my),(lerp(mx,ex,clamp((lp-0.5)*2)),my)],fill=A(col,0.8*a),width=12)
        cp=expo((t-ts-0.18)/0.2)
        if cp>0:
            flash=max(0,1-(t-tf)/0.4) if t>=tf else 0
            d.rounded_rectangle([x0,y0,x1,y1],radius=20,fill=A((8,10,16),0.94*cp),outline=A(col,cp),width=4+int(4*flash))
            GL.rounded_rectangle([x0,y0,x1,y1],radius=20,outline=A(col,(0.6+0.4*flash)*cp*a),width=10+int(14*flash))
            if ic=='factory':
                factory_icon(d,x0+24,y0+70,col,cp,(t-ts))
                txt(d,x0+40,y0+20,'MILK FACTORY',f(MONOB,22),col,cp)
                d.rounded_rectangle([x0+30,y0+190,x0+150,y0+224],radius=17,fill=A(col,cp)); txt(d,x0+90,y0+207,'ON',f(MONOB,22),INK,cp,anchor='mm')
            else:
                tx,ty=x0+100,y0+140
                for rr in (70,48,26): d.ellipse([tx-rr,ty-rr,tx+rr,ty+rr],outline=A(col,cp),width=4)
                for k in range(6):
                    an=k*math.pi/3; arrow(d,tx+76*math.cos(an),ty+76*math.sin(an),tx+(76+22*cp)*math.cos(an),ty+(76+22*cp)*math.sin(an),col,3,cp,10)
                txt(d,x0+40,y0+20,'TISSUE PRIMED',f(MONOB,22),col,cp)
            fb=f(BEB,80); bw=d.textlength(lab2,font=fb)
            txt(d,x1-26-bw,y1-104,lab2,fb,WHITE if flash==0 else col,cp)
    lay.putalpha(lay.split()[3].point(lambda v:int(v*a)))
    im.alpha_composite(lay)
# =====================================================================
# 13 PROTOCOL CHECKLIST (full-screen, portrait PiP right)
# =====================================================================
ROWS=[(88.56,'PULL PROLACTIN','BLOODWORK FIRST'),(89.72,'P5P','ACTIVE VITAMIN B6'),(90.76,'CABERGOLINE','DOPAMINE AGONIST')]
def s_proto(im,src,t):
    t0,t1=88.00,93.70
    if not (t0<=t<t1+0.30): return False
    g=min(ease_io((t-t0)/0.36),1-ease_io((t-t1)/0.28))
    bg=pushed_bg(src,g); im.paste(bg.convert('RGBA'),(0,0))
    pip(im,src,t,g,'rect',(818,520),(372,500))
    if g<0.5: return True
    a=clamp((g-0.5)/0.5)
    lay=Image.new('RGBA',(W,H),(0,0,0,0)); d=ImageDraw.Draw(lay,'RGBA')
    kicker(d,70,276,'THE FIX',t,t0+0.2,VGOLD,28)
    txt(d,64,320,'MANAGE',f(BEB,120),CREAM); txt(d,64,430,'THE',f(BEB,120),CREAM); txt(d,64,540,'19-NOR',f(BEB,120),VGOLD)
    txt(d,70,670,'PROTOCOL · 3 STEPS',f(MONO,24),MUTED)
    y=800
    for k,(ts,lab,sub) in enumerate(ROWS):
        if t<ts-0.25: break
        p=expo((t-ts+0.25)/0.2); yy=y+k*150; xo=lerp(-60,0,p)
        d.rounded_rectangle([60+xo,yy,1020+xo,yy+128],radius=18,fill=A((8,10,16),0.92*p),outline=A((70,72,84),p),width=2)
        d.rectangle([60+xo,yy,68+xo,yy+128],fill=A(VGOLD,p))
        txt(d,96+xo,yy+64,f'0{k+1}',f(BEB,70),VGOLD,p,anchor='lm')
        txt(d,180+xo,yy+12,lab,f(BAR,66),WHITE,p); txt(d,182+xo,yy+86,sub,f(MONO,22),MUTED,p)
        bx=930+xo; d.rounded_rectangle([bx-36,yy+30,bx+36,yy+98],radius=10,outline=A((150,150,160),p),width=4)
        if t>=ts+0.12:
            q=ap(t,ts+0.12,0.12); d.rounded_rectangle([bx-36,yy+30,bx+36,yy+98],radius=10,fill=A((6,40,20),q),outline=A(GREEN,q),width=4)
            check(d,bx-24,yy+66,GREEN,1.3*q+0.01,q,8)
    if t>=92.38:
        q=ap(t,92.38,0.2); w_=tag_w(d,'NON-NEGOTIABLE',30); tag(d,1020-w_,1258,'NON-NEGOTIABLE',VGOLD,30,q)
    lay.putalpha(lay.split()[3].point(lambda v:int(v*a)))
    im.alpha_composite(lay)
    return True
# =====================================================================
# 14 CTA: protocol cover card + COMMENT pill
# =====================================================================
_LOGO=None
def logo_round(sz):
    global _LOGO
    if _LOGO is None:
        lg=Image.open(WK+'logo.jpg').convert('RGB'); s=min(lg.size); lg=lg.crop(((lg.width-s)//2,(lg.height-s)//2-40,(lg.width+s)//2,(lg.height+s)//2-40)).resize((sz,sz),Image.LANCZOS)
        m=Image.new('L',(sz,sz),0); ImageDraw.Draw(m).ellipse([0,0,sz-1,sz-1],fill=255); lg.putalpha(m); _LOGO=lg
    return _LOGO
CTA_CARD=94.92; CTA_PILL=100.56
def s_cta(im,t):
    if t<CTA_CARD: return
    p=expo((t-CTA_CARD)/0.3)
    x0,y0,x1,y1=60,262,1020,600
    yo=lerp(60,0,p)
    lay=Image.new('RGBA',(W,H),(0,0,0,0)); d=ImageDraw.Draw(lay,'RGBA')
    d.rounded_rectangle([x0,y0+yo,x1,y1+yo],radius=24,fill=A(NAVY,0.95),outline=A((58,54,48),1),width=2)
    d.rectangle([x0,y0+yo+24,x0+8,y1+yo-24],fill=A(GOLD,1))
    lay.alpha_composite(logo_round(150),(x0+40,int(y0+yo+40)))
    kicker(d,x0+220,y0+yo+40,'FREE · FULL GUIDE',t,CTA_CARD+0.1,GOLD,26)
    txt(d,x0+220,y0+yo+86,'19-NOR',f(BEB,96),CREAM); nw=d.textlength('19-NOR ',font=f(BEB,96)); txt(d,x0+220+nw,y0+yo+86,'MANAGEMENT',f(BEB,96),GOLD)
    txt(d,x0+220,y0+yo+180,'PROTOCOL',f(BEB,96),CREAM)
    txt(d,x0+40,y1+yo-44,'@coach.agz',f(MONO,22),GOLD); dt='FOR RESEARCH & EDUCATIONAL PURPOSES ONLY'; txt(d,x1-30-d.textlength(dt,font=f(MONO,18)),y1+yo-40,dt,f(MONO,18),MUTED2)
    if t>=CTA_PILL:
        q=back((t-CTA_PILL)/0.26,0.5); fn=f(BEB,104)
        l1='COMMENT '; l2='"PROLACTIN"'; w1=d.textlength(l1,font=fn); w2=d.textlength(l2,font=fn)
        pw=w1+w2+80; px=540-pw/2; py=lerp(760,632,q)
        lit_bar(d,px,py,px+pw,py+128,VGOLD,clamp(q*2)); d.rectangle([px,py+122,px+pw,py+128],fill=A((150,100,0),clamp(q*2)))
        txt(d,px+40,py+14,l1,fn,INK,clamp(q*2)); txt(d,px+40+w1,py+14,l2,fn,(120,0,0),clamp(q*2))
        GL.rectangle([px-4,py-4,px+pw+4,py+132],outline=A(VGOLD,clamp(q*2)),width=12)
    lay.putalpha(lay.split()[3].point(lambda v:int(v*clamp(p*1.5))))
    im.alpha_composite(lay)
# ---------------- captions ----------------
WORDS=json.load(open(WK+'words_caption.json'))
def nearest_cut(t):
    for c in CUTS:
        if c>t+0.01: return c
    return 1e9
def build_groups():
    G=[];cur=[]
    for i,x in enumerate(WORDS):
        if cur:
            prev=WORDS[cur[-1]]
            if len(cur)>=3 or x['s']-prev['e']>0.30 or prev['w'][-1] in '.,?!' or len(' '.join(WORDS[j]['c'] for j in cur+[i]))>17: G.append(cur); cur=[]
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
CAP_Y=1335
def captions(im,t):
    g=group_at(t)
    if not g: return
    d=ImageDraw.Draw(im,'RGBA')
    ws=[WORDS[i]['c'] for i in g]
    size=128
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
# ---------------- frame ----------------
def seg_of(t): return sum(1 for c in CUTS if c<=t+1e-6)
UPPER=[s_post,s_tiles,s_toggle,s_step1,s_bars,s_chips,s_graph,s_doc,s_step2,s_fork,s_verdict,s_cta]
FULL=[s_mech,s_gyno,s_proto]
SHAKES=[VERDICT_T,GALAC_T+0.12]
def frame(src,t):
    global GL
    z=1.0 if seg_of(t)%2==0 else 1.08
    if z!=1.0:
        big=src.resize((int(W*z),int(H*z)),Image.BICUBIC); ox=(big.width-W)//2; oy=int((big.height-H)*0.40); src=big.crop((ox,oy,ox+W,oy+H))
    im=src.convert('RGBA')
    glow=Image.new('RGBA',(W,H),(0,0,0,0)); GL=ImageDraw.Draw(glow,'RGBA')
    full=False
    for fn_ in FULL:
        if fn_(im,src,t): full=True; break
    if not full:
        # gentle top scrim for overlay legibility (graphics layer only, footage colours untouched)
        if any_upper(t):
            yy=np.arange(H); al=np.where(yy<760,np.clip((760-yy)/520,0,1)*120,0).astype(np.uint8)
            im.alpha_composite(Image.merge('RGBA',[Image.new('L',(W,H),c) for c in (2,3,8)]+[Image.fromarray(np.repeat(al[:,None],W,1))]))
        for fn_ in UPPER: fn_(im,t)
    if glow.getbbox():
        sm=glow.resize((W//4,H//4),Image.BILINEAR)
        g1=np.asarray(sm.filter(ImageFilter.GaussianBlur(3.5))).astype(np.float32)/255; g2=np.asarray(sm.filter(ImageFilter.GaussianBlur(10))).astype(np.float32)/255
        prem=np.clip(g1[...,:3]*g1[...,3:]*2.3+g2[...,:3]*g2[...,3:]*1.8,0,1)
        prem=np.asarray(Image.fromarray((prem*255).astype(np.uint8)).resize((W,H),Image.BILINEAR)).astype(np.float32)/255
        b=np.asarray(im.convert('RGB')).astype(np.float32)/255
        im=Image.fromarray(((1-(1-b)*(1-prem))*255).astype(np.uint8)).convert('RGBA')
    GL=None
    d=ImageDraw.Draw(im,'RGBA'); d.rectangle([0,0,7,H],fill=GOLD)
    captions(im,t)
    if t<CTA_CARD:
        d=ImageDraw.Draw(im,'RGBA'); hfn=f(MONO,22); txt(d,64,1468,'@coach.agz',hfn,GOLD,0.9)
        dt='FOR RESEARCH & EDUCATIONAL PURPOSES ONLY'; dfn=f(MONO,16); txt(d,64+d.textlength('@coach.agz  ',font=hfn),1473,dt,dfn,(200,200,205),0.75)
    out=im.convert('RGB')
    for ts in SHAKES:
        k=round((t-ts)*FPS)
        if k in (0,1):
            dx=[9,-5][k]; zz=1.025; big=out.resize((int(W*zz),int(H*zz)),Image.BICUBIC); ox=(big.width-W)//2-dx; oy=(big.height-H)//2
            out=big.crop((ox,oy,ox+W,oy+H)); ImageDraw.Draw(out).rectangle([0,0,7,H],fill=GOLD)
    return out
UPPER_WIN=[(0.9,3.75),(4.4,10.1),(13.25,16.9),(17.3,20.9),(21.0,28.2),(28.55,32.75),(44.62,55.5),(66.24,74.7),(74.86,77.0),(76.96,83.9),(83.92,87.75),(94.92,999)]
def any_upper(t): return any(a<=t<b for a,b in UPPER_WIN)
if __name__=='__main__':
    mode=sys.argv[1]
    if mode=='stills':
        os.makedirs(WK+'qc',exist_ok=True)
        for tt in [float(x) for x in sys.argv[2:]]:
            subprocess.run(['ffmpeg','-v','error','-y','-ss',f'{tt:.4f}','-i',WK+'mezz30.mp4','-frames:v','1',WK+'qc/_src.png'])
            frame(Image.open(WK+'qc/_src.png').convert('RGB'),tt).resize((540,960),Image.LANCZOS).save(WK+f'qc/st_{tt:06.2f}.jpg',quality=88)
        sys.exit()
    n0,n1,out=int(sys.argv[2]),int(sys.argv[3]),sys.argv[4]
    olds=[min(int(round(new_to_old(n/FPS)*FPS)),3128) for n in range(n0,n1)]
    first,last=olds[0],olds[-1]
    dec=subprocess.Popen(['ffmpeg','-v','error','-ss',f'{max(0,first-30)/FPS:.4f}','-i',WK+'mezz30.mp4','-f','rawvideo','-pix_fmt','rgb24','-'],stdout=subprocess.PIPE)
    enc=subprocess.Popen(['ffmpeg','-v','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-','-c:v','libx264','-crf','14','-preset','fast','-pix_fmt','yuv420p',out],stdin=subprocess.PIPE)
    cur=max(0,first-30)-1; buf=None   # accurate input seek: first decoded frame == seek frame
    for n,o in zip(range(n0,n1),olds):
        while cur<o:
            buf=dec.stdout.read(W*H*3); cur+=1
            if len(buf)<W*H*3: raise SystemExit(f'short read at {cur}')
        enc.stdin.write(frame(Image.frombuffer('RGB',(W,H),buf),o/FPS).tobytes())
    enc.stdin.close(); enc.wait(); dec.kill(); print('done',n0,n1)
