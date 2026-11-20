# Heart health (ezetimibe + telmisartan) full edit, 1080x1920 30fps.
# usage: python3 render.py <workdir> stills t1 t2 ...   |   python3 render.py <workdir> chunk n0 n1 out.mp4
# <workdir> holds assembled.mp4, fonts/, logo.jpg; this folder holds words_final.json + segments.json
import json, subprocess, sys, math, os
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
HERE=os.path.dirname(os.path.abspath(__file__))
WD=sys.argv[1]; F=WD+'/fonts/'
W,H=1080,1920; FPS=30; DUR=115.9
WORDS=json.load(open(HERE+'/words_final.json'))
SEG=json.load(open(HERE+'/segments.json'))['keep']
BOUNDS=[];acc=0
for a,b in SEG: BOUNDS.append(acc/FPS); acc+=b-a
GOLD=(201,169,110); CREAM=(244,241,234); NAVY=(14,17,23)
RED=(255,34,28); VGOLD=(255,194,26); CYAN=(0,229,255); GREEN=(30,255,110); DEEP=(2,3,8); INK=(6,8,14); WHITE=(255,255,255)
COARED=(210,10,20); AMBER=(240,160,48); MUTED=(150,152,165)
MONO='JBMono-500.woff'; MONOB='JBMono-800.woff'; BEB='BebasNeue.woff'; DMB='DMSans-700.woff'; DMR='DMSans-400.woff'; BAR='Barlow-800.woff'
_fc={}
def f(n,s):
    k=(n,int(s))
    if k not in _fc: _fc[k]=ImageFont.truetype(F+n,int(s))
    return _fc[k]
def clamp(x,a=0,b=1): return max(a,min(b,x))
def expo(x): x=clamp(x); return 1 if x>=1 else 1-2**(-10*x)
def ease_io(x): x=clamp(x); return 4*x**3 if x<.5 else 1-(-2*x+2)**3/2
def lerp(a,b,t): return a+(b-a)*t
def A(c,a): return tuple(c[:3])+(int(clamp(a)*255),)
def ap(t,t0,dur=0.16): return expo((t-t0)/dur)
def win(t,t0,t1,fi=0.16,fo=0.14): return ap(t,t0,fi)*(1-clamp((t-t1)/fo))
GL=None
# PIL ignores fill alpha for text on RGB images: route translucent text through a layer.
_orig_text=ImageDraw.ImageDraw.text
def _text_alpha(self,xy,text,fill=None,font=None,anchor=None,**kw):
    if isinstance(fill,tuple) and len(fill)==4 and fill[3]<255:
        al=fill[3]
        if al<=2: return
        sw=kw.get('stroke_width',0)
        if 'stroke_fill' in kw and isinstance(kw['stroke_fill'],tuple) and len(kw['stroke_fill'])==4: kw['stroke_fill']=kw['stroke_fill'][:3]
        bb=self.textbbox(xy,text,font=font,anchor=anchor,stroke_width=sw)
        x0,y0=int(math.floor(bb[0]))-3,int(math.floor(bb[1]))-3; w=int(bb[2])-x0+6; h=int(bb[3])-y0+6
        if w<=0 or h<=0: return
        lay=Image.new('RGBA',(w,h),(0,0,0,0))
        _orig_text(ImageDraw.Draw(lay),(xy[0]-x0,xy[1]-y0),text,fill=fill[:3]+(255,),font=font,anchor=anchor,**kw)
        lay.putalpha(lay.split()[3].point(lambda v:v*al//255))
        self._image.paste(lay,(x0,y0),lay); return
    return _orig_text(self,xy,text,fill=fill,font=font,anchor=anchor,**kw)
ImageDraw.ImageDraw.text=_text_alpha
# ---------------- primitives ----------------
def txt(d,x,y,s,font,col,a=1.0,anchor=None): d.text((x,y),s,font=font,fill=A(col,a),anchor=anchor)
def brackets(d,x0,y0,x1,y1,col,L=34,w=4):
    for (cx,cy,sx,sy) in [(x0,y0,1,1),(x1,y0,-1,1),(x0,y1,1,-1),(x1,y1,-1,-1)]:
        d.line([(cx,cy),(cx+sx*L,cy)],fill=col,width=w); d.line([(cx,cy),(cx,cy+sy*L)],fill=col,width=w)
def lit_bar(d,x0,y0,x1,y1,col,a=1.0):
    if x1<=x0: return
    h=max(1,int(y1-y0))
    for i in range(h):
        k=i/h; c=tuple(int(min(255,v*(1.18-0.36*k)+(40 if k<0.12 else 0))) for v in col)
        d.line([(x0,y0+i),(x1,y0+i)],fill=c+(int(255*clamp(a)),))
def vbar(d,x0,y0,x1,y1,col,a=1.0):   # vertical lit bar (for bar charts)
    if y1<=y0: return
    w=max(1,int(x1-x0))
    for i in range(w):
        k=i/w; c=tuple(int(min(255,v*(1.15-0.4*abs(k-0.35))+(50 if 0.25<k<0.4 else 0))) for v in col)
        d.line([(x0+i,y0),(x0+i,y1)],fill=c+(int(255*clamp(a)),))
def tag(d,x,y,label,col=RED,size=30,a=1.0,glow=True,anchor_right=False):
    fn=f(MONO,size); tw=d.textlength(label,font=fn); h=size+16
    if anchor_right: x=x-tw-24
    lit_bar(d,x,y,x+tw+24,y+h,col,a); d.text((x+12,y+5),label,font=fn,fill=A(INK if col in (VGOLD,GREEN,CYAN) else WHITE,a))
    if GL and glow and a>0: GL.rectangle([x-4,y-4,x+tw+28,y+h+4],outline=A(col,a),width=8)
    return x+tw+24
def check(d,x,y,col,s=1.0,a=1.0):
    pts=[(x,y+16*s),(x+10*s,y+28*s),(x+30*s,y+2*s)]
    d.line(pts,fill=A(col,a),width=int(6*s))
    if GL: GL.line(pts,fill=A(col,a),width=int(12*s))
def cross(d,x,y,col,s=1.0,a=1.0):
    d.line([(x,y),(x+28*s,y+28*s)],fill=A(col,a),width=int(6*s)); d.line([(x+28*s,y),(x,y+28*s)],fill=A(col,a),width=int(6*s))
    if GL: GL.line([(x,y),(x+28*s,y+28*s)],fill=A(col,a),width=int(12*s)); GL.line([(x+28*s,y),(x,y+28*s)],fill=A(col,a),width=int(12*s))
def arrow(d,x0,y0,x1,y1,col,w=5,a=1.0,L=18):
    d.line([(x0,y0),(x1,y1)],fill=A(col,a),width=w)
    ang=math.atan2(y1-y0,x1-x0)
    d.polygon([(x1+3*math.cos(ang),y1+3*math.sin(ang)),(x1-L*math.cos(ang-0.5),y1-L*math.sin(ang-0.5)),(x1-L*math.cos(ang+0.5),y1-L*math.sin(ang+0.5))],fill=A(col,a))
    if GL: GL.line([(x0,y0),(x1,y1)],fill=A(col,a),width=w*2)
def bigarrow(d,cx,y0,y1,col,w=34,a=1.0):   # fat block arrow, y0 -> y1 (direction by sign)
    s=1 if y1>y0 else -1; hh=w*1.1
    d.rectangle([cx-w/2,min(y0,y1-s*hh),cx+w/2,max(y0,y1-s*hh)],fill=A(col,a))
    d.polygon([(cx-w*1.1,y1-s*hh),(cx+w*1.1,y1-s*hh),(cx,y1)],fill=A(col,a))
    if GL: GL.polygon([(cx-w*1.1,y1-s*hh),(cx+w*1.1,y1-s*hh),(cx,y1)],fill=A(col,a)); GL.rectangle([cx-w/2,min(y0,y1-s*hh),cx+w/2,max(y0,y1-s*hh)],fill=A(col,a*0.7))
def heart_shape(d,cx,cy,r,col,a=1.0,outline=None,w=4):
    pts=[]
    for i in range(60):
        th=i/60*2*math.pi; x=16*math.sin(th)**3; y=13*math.cos(th)-5*math.cos(2*th)-2*math.cos(3*th)-math.cos(4*th)
        pts.append((cx+x*r/16,cy-y*r/16))
    if outline: d.line(pts+[pts[0]],fill=A(outline,a),width=w)
    else: d.polygon(pts,fill=A(col,a))
    if GL: GL.line(pts+[pts[0]],fill=A(outline or col,a),width=w*2)
def frosted(im,box,dark=0.86,blur=10,radius=0,a=1.0):
    x0,y0,x1,y1=[int(v) for v in box]; x0=max(0,x0); y0=max(0,y0); x1=min(W,x1); y1=min(H,y1)
    if x1<=x0 or y1<=y0: return
    reg=im.crop((x0,y0,x1,y1)).convert('RGB').filter(ImageFilter.GaussianBlur(blur))
    reg=Image.blend(reg,Image.new('RGB',reg.size,DEEP),dark)
    if a<=0.01: return
    if a<1: reg=Image.blend(im.crop((x0,y0,x1,y1)).convert('RGB'),reg,a)
    if radius:
        m=Image.new('L',reg.size,0); ImageDraw.Draw(m).rounded_rectangle([0,0,reg.width-1,reg.height-1],radius=radius,fill=255); im.paste(reg,(x0,y0),m)
    else: im.paste(reg,(x0,y0))
def panel_frame(d,x0,y0,x1,y1,col=VGOLD,a=1.0,L=30,label=None,right=None):
    d.rectangle([x0,y0,x1,y1],outline=A(col,0.45*a),width=2); brackets(d,x0,y0,x1,y1,A(col,a),L,5)
    if GL: brackets(GL,x0,y0,x1,y1,A(col,a),L,10)
    if label: txt(d,x0+22,y0+14,label,f(MONO,28),col,a)
    if right: fn=f(MONO,24); tw=d.textlength(right,font=fn); txt(d,x1-22-tw,y0+16,right,fn,MUTED,a)
def redact(d,x,y,w,h,a=1.0,reveal=0.0):
    # black redaction bar wiping off to the right as reveal goes 0->1
    x0=x+w*reveal
    if x0<x+w: d.rectangle([x0,y,x+w,y+h],fill=A((0,0,0),a)); d.rectangle([x0,y,x+w,y+h],outline=A((60,60,70),a),width=2)
def flow(d,pts_from,pts_to,t,col,n=5,speed=0.9,a=1.0,r=7,phase=0):
    x0,y0=pts_from; x1,y1=pts_to
    for k in range(n):
        p=(t*speed+k/n+phase)%1; x=lerp(x0,x1,p); y=lerp(y0,y1,p); fa=a*min(1,p*6,(1-p)*6)
        d.ellipse([x-r,y-r,x+r,y+r],fill=A(col,fa))
        if GL: GL.ellipse([x-r*2,y-r*2,x+r*2,y+r*2],fill=A(col,fa))
def meter(d,x0,y0,x1,y1,frac,col,label,value=None,a=1.0,lsize=24):
    txt(d,x0,y0-34,label,f(MONO,lsize),CREAM,a)
    d.rectangle([x0,y0,x1,y1],outline=A((70,74,90),a),width=2)
    xf=lerp(x0+3,x1-3,clamp(frac)); lit_bar(d,x0+3,y0+3,xf,y1-3,col,a)
    if GL: GL.rectangle([x0+3,y0+3,xf,y1-3],fill=A(col,a*0.6))
    if value: fn=f(BEB,40); tw=d.textlength(value,font=fn); txt(d,x1-tw,y0-44,value,fn,col,a)
def layer_alpha(lay,al):
    if al<1: lay.putalpha(lay.split()[3].point(lambda v:int(v*al)))
    return lay

# ================= SCENES =================
# each scene: (t_in, t_out, layout, fn). layout: 'talk' | 'lift' | 'pipR' | 'pipL'
# ---- 1. health-plan checklist rail (talk) ----
def sc_plan(im,d,t):
    t0,t1=3.30,8.30; a=win(t,t0,t1,0.18,0.16)
    if a<=0: return
    dx=lerp(-360,0,expo((t-t0)/0.22))-380*clamp((t-t1)/0.16)**2
    x0,y0,x1,y1=36+dx,600,346+dx,1000
    frosted(im,(x0,y0,x1,y1),0.84,14,a=a); d=ImageDraw.Draw(im,'RGBA')
    d.rectangle([x0,y0,x0+6,y1],fill=A(VGOLD,a))
    if GL: GL.rectangle([x0,y0,x0+6,y1],fill=A(VGOLD,a))
    txt(d,x0+26,y0+18,'HEALTH PLAN',f(MONO,24),VGOLD,a); d.line([(x0+26,y0+56),(x1-20,y0+56)],fill=A((80,84,100),a),width=2)
    rows=[('ESTROGEN',3.44,True),('PROLACTIN',4.16,True),('LIPIDS',5.06,False),('BLOOD PRESS.',5.72,False)]
    for i,(nm,tt,ok) in enumerate(rows):
        ra=a*ap(t,tt,0.1)
        if ra<=0: continue
        y=y0+78+i*64
        (check if ok else cross)(d,x0+26,y+4,GREEN if ok else RED,0.9,ra)
        txt(d,x0+76,y,nm,f(MONO,28),WHITE if ok else (255,190,185),ra)
    if t>=6.68: tag(d,x0+26,y0+340,'UNMANAGED',RED,26,a*ap(t,6.68,0.1))
# ---- 2. ECG monitor strip (talk) ----
def ecg_y(ph):
    ph=ph%1
    if ph<0.40: return 0
    if ph<0.45: return -0.12*math.sin((ph-0.40)/0.05*math.pi)
    if ph<0.48: return 0.15*((ph-0.45)/0.03)
    if ph<0.51: return lerp(0.15,-1.0,(ph-0.48)/0.03)
    if ph<0.54: return lerp(-1.0,0.35,(ph-0.51)/0.03)
    if ph<0.57: return lerp(0.35,0,(ph-0.54)/0.03)
    if ph<0.72: return -0.22*math.sin((ph-0.57)/0.15*math.pi)
    return 0
def sc_ecg(im,d,t):
    t0,t1=8.50,11.62; a=win(t,t0,t1,0.14,0.14)
    if a<=0: return
    x0,y0,x1,y1=40,1196,1040,1352
    h=lerp(0,y1-y0,expo((t-t0)/0.2)); yc=(y0+y1)/2; y0_=yc-h/2; y1_=yc+h/2
    frosted(im,(x0,y0_,x1,y1_),0.82,12,a=a); d=ImageDraw.Draw(im,'RGBA')
    for gx in range(x0,x1,40): d.line([(gx,y0_),(gx,y1_)],fill=A((20,60,40),a),width=1)
    for gy in range(int(y0_),int(y1_),26): d.line([(x0,gy),(x1,gy)],fill=A((20,60,40),a),width=1)
    flat=t>=11.0; red=t>=9.26
    col=RED if red else GREEN
    head=x0+((t-t0)*520)%(x1-x0)  # sweep position
    pts=[]
    for x in range(x0+4,x1-4,3):
        # time this x was drawn
        age=((head-x)%(x1-x0))/520.0; tt=t-age
        beat_rate=1.15
        v=0 if tt>=11.0 else ecg_y(tt*beat_rate)
        pts.append((x,yc+v*58))
    # gap after head
    seg=[p for p in pts if not (head<p[0]<head+30)]
    lastx=None; run=[]
    for p in seg:
        if lastx is not None and p[0]-lastx>6:
            if len(run)>1: d.line(run,fill=A(col,a),width=4); GL and GL.line(run,fill=A(col,a),width=8)
            run=[]
        run.append(p); lastx=p[0]
    if len(run)>1: d.line(run,fill=A(col,a),width=4); GL and GL.line(run,fill=A(col,a),width=8)
    txt(d,x0+18,y0_+10,'HR',f(MONO,22),col,a*(1 if h>60 else 0))
    if flat: tag(d,x1-16,y0_+12,'NO WARNING SIGNS',RED,24,a*ap(t,11.0,0.08),anchor_right=True)
    else: txt(d,x1-110,y0_+10,'SINUS',f(MONO,22),col,a*(1 if h>60 else 0))
# ---- 3. two redacted compounds -> stepper (talk) ----
def sc_two(im,d,t):
    t0,t1=12.20,14.70; a=win(t,t0,t1,0.16,0.14)
    if a>0:
        for i,tt in enumerate([12.32,12.54]):
            ra=a*ap(t,tt,0.16)
            if ra<=0: continue
            x0=60+i*500; y0=1200+lerp(30,0,expo((t-tt)/0.2))
            frosted(im,(x0,y0,x0+460,y0+140),0.85,12,a=ra); d=ImageDraw.Draw(im,'RGBA')
            panel_frame(d,x0,y0,x0+460,y0+140,VGOLD,ra,22)
            txt(d,x0+24,y0+18,f'COMPOUND 0{i+1}',f(MONO,24),VGOLD,ra)
            redact(d,x0+24,y0+60,300,56,ra); txt(d,x0+340,y0+66,'?',f(BEB,58),RED,ra)
    t0,t1=14.80,18.85; a=win(t,t0,t1,0.16,0.14)
    if a>0:
        y=1236; frosted(im,(40,y-30,1040,y+110),0.84,12,a=a); d=ImageDraw.Draw(im,'RGBA')
        steps=[('MECHANICS',16.48),('SIMPLIFY',17.36),('OPTIMIZE',18.36)]
        xs=[120,500,880]
        for i,(nm,tt) in enumerate(steps):
            on=ap(t,tt,0.12)
            if i<2:
                p=clamp((t-tt)/0.5); d.line([(xs[i]+30,y+10),(xs[i+1]-30,y+10)],fill=A((70,74,90),a),width=4)
                if p>0: d.line([(xs[i]+30,y+10),(lerp(xs[i]+30,xs[i+1]-30,p),y+10)],fill=A(VGOLD,a),width=4)
            col=VGOLD if on>0.5 else (70,74,90)
            d.ellipse([xs[i]-20,y-10,xs[i]+20,y+30],fill=A(col if on>0.5 else (20,22,30),a),outline=A(col,a),width=4)
            if GL and on>0.5: GL.ellipse([xs[i]-26,y-16,xs[i]+26,y+36],outline=A(VGOLD,a*on),width=8)
            txt(d,xs[i],y+16,str(i+1),f(MONOB,22),INK if on>0.5 else MUTED,a,anchor='mm')
            txt(d,xs[i],y+70,nm,f(MONO,26),WHITE if on>0.5 else MUTED,a,anchor='mm')
# ---- chapter slabs (talk) ----
def sc_chapter(im,d,t,t0,t1,num,title,sub,sub_t):
    a=win(t,t0,t1,0.01,0.18)
    if a<=0: return
    p=expo((t-t0)/0.22); y0=1120
    yy=lerp(H,y0,p)-40*clamp((t-t1)/0.18)
    frosted(im,(0,yy,W,yy+240),0.9,16,a=a); d=ImageDraw.Draw(im,'RGBA')
    lit_bar(d,0,yy,W,yy+8,VGOLD,a)
    if GL: GL.rectangle([0,yy,W,yy+8],fill=A(VGOLD,a))
    txt(d,56,yy+14,num,f(BEB,230),VGOLD,a)
    if GL: GL.text((56,yy+14),num,font=f(BEB,230),fill=A(VGOLD,a*0.5))
    txt(d,300,yy+30,'CHAPTER',f(MONO,28),MUTED,a)
    fn=f(BEB,112); s=title
    while d.textlength(s,font=fn)>740: fn=f(BEB,fn.size-6)
    txt(d,300,yy+66,s,fn,CREAM,a)
    if sub and t>=sub_t: txt(d,302,yy+70+fn.size,sub,f(MONO,28),CYAN,a*ap(t,sub_t,0.12))
# ---- 4. lipid bar chart -> dual line chart (lift deck) ----
def sc_lipids(im,d,t,oy):
    a=1.0
    panel_frame(d,40,990+oy,1040,1570+oy,VGOLD,a,30,'LIPID PANEL · ON CYCLE','ILLUSTRATIVE')
    bars_a=1-clamp((t-25.80)/0.18)
    if bars_a>0:
        base=1490+oy; top=1070+oy; Hh=base-top-30
        d.line([(80,base),(1000,base)],fill=A((90,94,110),bars_a),width=2)
        yb=base-Hh*0.5;
        for x in range(80,1000,24): d.line([(x,yb),(x+12,yb)],fill=A(MUTED,bars_a*0.7),width=2)
        txt(d,1000,yb-34,'BASELINE',f(MONO,24),MUTED,bars_a,anchor='ra')
        spec=[('HDL',140,0.55,0.16,22.30,VGOLD,'CRASHED'),('LDL',440,0.50,0.86,24.78,RED,'UP'),('APOB',740,0.50,0.90,25.48,RED,'UP')]
        for nm,x,v0,v1,tt,col,lab in spec:
            ga=bars_a*ap(t,21.20+(x-140)/3000,0.2)
            p=expo((t-tt)/(0.35 if nm=='HDL' else 0.5)); v=lerp(v0,v1,p)
            c=col if p>0.05 else CYAN
            vbar(d,x,base-Hh*v,x+200,base,c,ga)
            if GL: GL.rectangle([x,base-Hh*v,x+200,base],outline=A(c,ga),width=6)
            txt(d,x+100,base+8,nm,f(BEB,50),WHITE,ga,anchor='ma')
            if p>0.3:
                if nm=='HDL': bigarrow(d,x+100,base-Hh*v-120,base-Hh*v-24,RED,26,bars_a)
                else: bigarrow(d,x+100,base-Hh*v-24,base-Hh*v-120,RED,26,bars_a)
                if nm=='HDL': tag(d,x+20,base-Hh*v-190,lab,RED,28,bars_a*ap(t,tt+0.2,0.1))
    la=ap(t,25.86,0.2)
    if la>0:
        x0,y0,x1,y1=110,1090+oy,1000,1490+oy
        d.line([(x0,y1),(x1,y1)],fill=A((90,94,110),la),width=2); d.line([(x0,y0),(x0,y1)],fill=A((90,94,110),la),width=2)
        for k in range(1,4): d.line([(x0,y1-k*85),(x1,y1-k*85)],fill=A((34,38,52),la),width=1)
        txt(d,x1,y1+12,'WEEKS ON CYCLE',f(MONO,24),MUTED,la,anchor='ra')
        def curve(p,kind):
            xs=lerp(x0,x1,p)
            if kind=='phys': v=0.18+0.62*(1-math.exp(-2.4*p))
            else: v=0.08+0.80*p**1.7
            return (xs,y1-v*(y1-y0))
        for kind,col,tt,dur,lab in [('phys',VGOLD,26.06,3.0,'PHYSIQUE'),('risk',RED,26.18,1.6,'CV RISK')]:
            p=clamp((t-tt)/dur)
            if p<=0: continue
            pts=[curve(i/60*p,kind) for i in range(61)]
            d.line(pts,fill=A(col,la),width=7,joint='curve')
            if GL: GL.line(pts,fill=A(col,la),width=14)
            ex,ey=pts[-1]; d.ellipse([ex-11,ey-11,ex+11,ey+11],fill=A(WHITE,la))
            # fill under the curve for punch
            poly=pts+[(pts[-1][0],y1),(pts[0][0],y1)]
            d.polygon(poly,fill=A(col,0.16*la))
            if p>0.15:
                if kind=='risk': tag(d,ex-14,ey+18,lab,RED,28,la,anchor_right=True)
                else: lx,ly=curve(min(p,0.42),'phys'); tag(d,lx-60,ly-62,lab,VGOLD,28,la)
        if t>=29.38:
            b=ap(t,29.38,0.12); tag(d,140,1090+oy,'WHAT YOU SEE',VGOLD,28,b)
        if t>=29.70:
            b=ap(t,29.70,0.12); tag(d,140,1146+oy,"WHAT YOU DON'T",RED,28,b)
# ---- 5. ezetimibe mechanism (PiP right) ----
def dossier(d,x0,y0,x1,y1,num,name,reveal_t,klass,target,target_t,t,a,col=CYAN):
    panel_frame(d,x0,y0,x1,y1,col,a,26)
    txt(d,x0+24,y0+18,f'COMPOUND {num}',f(MONO,24),col,a)
    rv=expo((t-reveal_t)/0.3)
    fn=f(BEB,96)
    if rv>0: txt(d,x0+22,y0+56,name,fn,WHITE,a)
    redact(d,x0+22,y0+62,min(x1-x0-44,d.textlength(name,font=fn)+10),84,a,rv)
    yy=y0+170
    for i,line in enumerate(klass): txt(d,x0+24,yy+i*32,line,f(MONO,24),CREAM,a*ap(t,reveal_t+0.25,0.2))
    if t>=target_t:
        b=ap(t,target_t,0.12); y=yy+len(klass)*32+18
        txt(d,x0+24,y+6,'TARGET',f(MONO,22),MUTED,b); tag(d,x0+140,y,target,col if col!=CYAN else VGOLD,26,b)
def sc_ezet(im,d,t):
    a=1.0
    dossier(d,40,150,570,560,'01','EZETIMIBE',31.20,['CHOLESTEROL','ABSORPTION INHIBITOR'],'NPC1L1',32.64,t,a,CYAN)
    # intestine schematic
    X0,Y0,X1,Y1=40,775,1040,1350
    panel_frame(d,X0,Y0,X1,Y1,CYAN,ap(t,30.3,0.2),26,'INTESTINE · CROSS-SECTION','SCHEMATIC')
    lum_y=850; wall0=990; wall1=1040; vessel0=1070; vessel1=1140
    txt(d,70,lum_y-20,'GUT LUMEN',f(MONO,24),MUTED,a)
    # wall with villi
    pts=[]
    for x in range(60,1021,6): pts.append((x,wall0-28*abs(math.sin((x-60)/58))))
    d.line(pts,fill=A(CYAN,a),width=4); GL and GL.line(pts,fill=A(CYAN,0.8),width=8)
    d.line([(60,wall1),(1020,wall1)],fill=A(CYAN,a),width=4)
    for x in range(60,1021,58): d.line([(x,wall0-2),(x,wall1)],fill=A((0,120,140),a),width=2)
    txt(d,1020,wall1+6,'INTESTINE WALL',f(MONO,20),CYAN,a*ap(t,36.34,0.12),anchor='ra')
    # blood vessel
    d.rounded_rectangle([60,vessel0,1020,vessel1],radius=40,outline=A((255,90,90),a),width=4)
    txt(d,70,vessel1+8,'BLOOD',f(MONO,20),(255,140,140),a)
    gates=[200,520,840]
    blocked=t>=32.18
    for i,gx in enumerate(gates):
        # NPC1L1 transporter: two pillars
        d.rectangle([gx-30,wall0-40,gx-18,wall1],fill=A(VGOLD,a)); d.rectangle([gx+18,wall0-40,gx+30,wall1],fill=A(VGOLD,a))
        if GL: GL.rectangle([gx-34,wall0-44,gx+34,wall1+4],outline=A(VGOLD,0.6),width=6)
        if blocked:
            bp=expo((t-32.18-i*0.08)/0.16); by=lerp(lum_y,wall0-60,bp)
            d.rectangle([gx-17,by,gx+17,by+70],fill=A(RED,1));
            if GL: GL.rectangle([gx-20,by-3,gx+20,by+73],fill=A(RED,0.9))
        # particles falling through gate
        for k in range(4):
            p=((t*0.55)+k/4+i*0.13)%1
            if not blocked or t<32.3:
                y=lerp(lum_y+40,vessel0+50,p); x=gx+math.sin(p*9+k)*6*(1-p)
            else:
                y=lerp(lum_y+40,wall0-80,min(1,p*1.6)); x=gx-50+k*30+math.sin(t*3+k)*8
            fa=min(1,p*5,(1-p)*5)
            d.ellipse([x-9,y-9,x+9,y+9],fill=A(VGOLD,fa)); GL and GL.ellipse([x-16,y-16,x+16,y+16],fill=A(VGOLD,fa*0.8))
    if t>=34.64: txt(d,gates[1]+44,wall0-74,'NPC1L1 · CHOLESTEROL TRANSPORTER',f(MONO,20),VGOLD,ap(t,34.64,0.12))
    if blocked: tag(d,gates[0]+40,lum_y-4,'EZETIMIBE',RED,24,ap(t,32.2,0.1))
    if t>=32.64: tag(d,1010,lum_y-4,'TRANSPORTER BLOCKED',RED,24,ap(t,32.64,0.1),anchor_right=True)
    # liver
    if t>=38.70:
        b=ap(t,38.70,0.2)
        lx,ly=820,1250
        liver=[(lx-160,ly-30),(lx-60,ly-70),(lx+90,ly-60),(lx+170,ly-20),(lx+120,ly+40),(lx-10,ly+60),(lx-140,ly+30)]
        d.polygon(liver,fill=A((60,14,20),b*0.9)); d.line(liver+[liver[0]],fill=A((255,110,110),b),width=4); GL and GL.line(liver+[liver[0]],fill=A((255,90,90),b),width=8)
        txt(d,lx-10,ly-12,'LIVER',f(BEB,48),WHITE,b,anchor='mm')
        for k in range(5): flow(d,(lx-120+k*50,vessel1-10),(lx-60+k*30,ly-40),t+k*0.17,(255,120,120),1,0.9,b,8)
        txt(d,lx-200,ly+58,'LDL PULLED FROM BLOOD',f(MONO,20),(255,150,150),b,anchor='ma')
    # meters
    if t>=37.10:
        b=ap(t,37.10,0.15); fr=lerp(1.0,0.32,expo((t-38.38)/0.5)) if t>=38.38 else 1.0
        meter(d,80,1250,520,1282,fr,RED if fr<0.6 else VGOLD,'CHOLESTEROL ABSORBED','LOW' if fr<0.6 else '',b,22)
# ---- 6. big stat tiles (talk) ----
def sc_stats(im,d,t):
    t1=44.40;
    for i,(nm,tt) in enumerate([('LDL',41.54),('APOB',42.62)]):
        a=win(t,tt,t1,0.16,0.14)
        if a<=0: continue
        x0=70+i*510; y0=1170+lerp(40,0,expo((t-tt)/0.2))
        frosted(im,(x0,y0,x0+430,y0+180),0.84,12,a=a); d=ImageDraw.Draw(im,'RGBA')
        panel_frame(d,x0,y0,x0+430,y0+180,GREEN,a,24)
        txt(d,x0+30,y0+30,nm,f(BEB,130),WHITE,a)
        p=expo((t-tt-0.1)/0.3); bigarrow(d,x0+340,y0+36,lerp(y0+60,y0+150,p),GREEN,30,a)
    if t>=43.92:
        a=win(t,43.92,t1,0.1,0.14); tag(d,380,1100,'LOWER = BETTER',GREEN,28,a)
# ---- 7. pressure gauge + LV hypertrophy (lift deck) ----
def lv(d,cx,cy,wall,a,beat):
    R=150*beat
    d.ellipse([cx-R,cy-R,cx+R,cy+R],fill=A((90,10,20),a*0.85),outline=A((255,80,80),a),width=4)
    r=R-wall
    d.ellipse([cx-r,cy-r,cx+r,cy+r],fill=A((18,4,8),a),outline=A((255,140,140),a),width=3)
    if GL: GL.ellipse([cx-R,cy-R,cx+R,cy+R],outline=A(RED,a),width=8)
def sc_bp(im,d,t,oy):
    panel_frame(d,40,990+oy,1040,1570+oy,RED,1,30,'PRESSURE · WORKLOAD · HEART','SCHEMATIC')
    # gauge
    cx,cy,R=290,1420+oy,220
    for i in range(60):
        k=i/60; c=GREEN if k<0.45 else (AMBER if k<0.7 else RED)
        a0=180+k*180; a1=180+(k+1/60)*180-1.2
        d.arc([cx-R,cy-R,cx+R,cy+R],a0,a1,fill=A(c,1),width=26)
    if GL: GL.arc([cx-R,cy-R,cx+R,cy+R],300,360,fill=A(RED,0.8),width=30)
    v=0.32 if t<48.02 else lerp(0.32,0.88,expo((t-48.02)/0.6))
    v+=0.015*math.sin(t*23)*(t>48.6)
    ang=math.pi+v*math.pi
    d.line([(cx,cy),(cx+(R-30)*math.cos(ang),cy+(R-30)*math.sin(ang))],fill=A(WHITE,1),width=8)
    d.ellipse([cx-18,cy-18,cx+18,cy+18],fill=A(WHITE,1))
    txt(d,cx,cy+28,'BLOOD PRESSURE',f(MONO,22),CREAM,1,anchor='ma')
    if t>=48.44: tag(d,cx-100,1050+oy,'ELEVATED',RED,26,ap(t,48.44,0.1))
    # workload meter
    if t>=49.40:
        b=ap(t,49.40,0.12); fr=lerp(0.3,0.92,expo((t-49.44)/0.6)); meter(d,560,1110+oy,1000,1140+oy,fr,RED,'HEART WORKLOAD','HIGH' if fr>0.8 else '',b,22)
    # LV
    if t>=50.10:
        b=ap(t,50.10,0.2); rate=2.2 if t<49.44 else 3.0
        beat=1+0.04*max(0,math.sin(t*rate*math.pi))**8
        wall=lerp(26,70,expo((t-52.06)/0.7)) if t>=52.06 else 26
        lv(d,780,1370+oy,wall,b,beat*0.86)
        if t>=51.38: txt(d,780,1370+oy,'LV',f(BEB,56),WHITE,ap(t,51.38,0.1),anchor='mm')
        if t>=52.06: tag(d,1020,1180+oy,'WALL THICKENS',RED,24,ap(t,52.2,0.1),anchor_right=True)
# ---- 8. telmisartan compound file (talk lower third) ----
def sc_file(im,d,t):
    t0,t1=54.60,58.62; a=win(t,t0,t1,0.2,0.14)
    if a<=0: return
    dx=lerp(W,0,expo((t-t0)/0.26))
    x0,y0,x1,y1=40+dx,1140,1040+dx,1350
    frosted(im,(x0,y0,x1,y1),0.86,14,a=a); d=ImageDraw.Draw(im,'RGBA')
    d.rectangle([x0,y0,x0+10,y1],fill=A(VGOLD,a)); GL and GL.rectangle([x0,y0,x0+10,y1],fill=A(VGOLD,a))
    panel_frame(d,x0,y0,x1,y1,VGOLD,a,26)
    txt(d,x0+36,y0+20,'COMPOUND 02 · FAVORITE',f(MONO,24),VGOLD,a)
    rv=expo((t-57.46)/0.25); s=lerp(1.12,1.0,rv) if rv>0 else 1
    fn=f(BEB,int(118*s))
    if rv>0: txt(d,x0+34,y0+58-(118*s-118)/2,'TELMISARTAN',fn,WHITE,a)
    redact(d,x0+34,y0+64,560,104,a,rv)
    if t>=57.7:
        b=ap(t,57.7,0.12); tag(d,x1-30,y0+70,'ARB',VGOLD,34,a*b,anchor_right=True); txt(d,x1-30,y0+140,'BLOOD PRESSURE',f(MONO,22),CREAM,a*b,anchor='ra')
# ---- 9. telmisartan mechanism (PiP left) ----
def sc_telmi(im,d,t):
    a=1.0
    X0,Y0,X1,Y1=510,150,1040,735
    panel_frame(d,X0,Y0,X1,Y1,VGOLD,a,26,'AT1 RECEPTOR','LOCK · KEY')
    # receptor cup on a membrane
    my=600; d.line([(X0+30,my),(X1-30,my)],fill=A((255,110,110),a),width=6)
    rx=775
    cup=[(rx-70,my),(rx-70,my-110),(rx-40,my-110),(rx-40,my-40),(rx+40,my-40),(rx+40,my-110),(rx+70,my-110),(rx+70,my)]
    d.line(cup,fill=A(CYAN,a),width=8); GL and GL.line(cup,fill=A(CYAN,a),width=14)
    if t>=60.36: txt(d,rx,my+14,'AT1',f(BEB,44),CYAN,ap(t,60.36,0.1),anchor='ma')
    # telmisartan plug
    if t>=58.72:
        p=expo((t-58.72)/0.25); py=lerp(220,my-104,p)
        d.rectangle([rx-36,py,rx+36,py+60],fill=A(VGOLD,1)); GL and GL.rectangle([rx-40,py-4,rx+40,py+64],fill=A(VGOLD,0.9))
        txt(d,rx,py+30,'T',f(BEB,44),INK,1,anchor='mm')
    # angiotensin II key approaching and bouncing
    if t>=58.9:
        q=(t-58.9)
        if t<58.72+0.3: kx,ky=lerp(560,700,clamp(q/0.6)),lerp(260,420,clamp(q/0.6))
        else:
            ph=clamp(q/0.7); kx=lerp(560,rx-30,min(1,ph*1.0)); ky=lerp(260,my-190,min(1,ph))
            if q>0.7: bq=q-0.7; kx=lerp(rx-30,620,expo(bq/0.4)); ky=lerp(my-190,330,expo(bq/0.4))
        d.polygon([(kx-26,ky-26),(kx+26,ky-26),(kx+10,ky+26),(kx-10,ky+26)],fill=A(RED,1)); GL and GL.ellipse([kx-36,ky-36,kx+36,ky+36],fill=A(RED,0.8))
        txt(d,kx+40,ky-24,'ANG II',f(MONO,24),(255,150,150),1)
    if t>=59.6: tag(d,X0+24,Y0+56,'ANGIOTENSIN II BLOCKED',RED,22,ap(t,59.6,0.1))
    # vessel (main area)
    V0,V1=780,1350
    panel_frame(d,40,V0,1040,V1,RED,ap(t,58.65,0.2),26,'BLOOD VESSEL','')
    relax=expo((t-62.72)/0.6) if t>=62.72 else 0
    gap=lerp(70,190,relax); vc=1000
    for sgn in (-1,1):
        y=vc+sgn*gap/2
        pts=[(x,y+sgn*6*math.sin(x/40+t*2)*(1-relax)) for x in range(70,1011,10)]
        d.line(pts,fill=A((255,90,90),1),width=10); GL and GL.line(pts,fill=A(RED,0.8),width=18)
        for x in range(70,1011,10):
            d.line([(x,y+sgn*5),(x,y+sgn*(5+lerp(40,18,relax)))],fill=A((120,20,30),0.9),width=6)
    sp=lerp(0.5,1.4,relax)
    for k in range(10):
        p=(t*sp*0.4+k/10)%1; x=lerp(80,1000,p); y=vc+math.sin(k*2.3)*gap*0.3
        d.ellipse([x-12,y-9,x+12,y+9],fill=A((255,70,70),min(1,p*6,(1-p)*6)))
    if t>=62.2: txt(d,70,vc+gap/2+40,'VESSEL RELAXES' if relax>0.2 else 'CONSTRICTED',f(MONO,24),GREEN if relax>0.2 else RED,ap(t,62.2,0.1))
    if t>=63.44:
        b=ap(t,63.44,0.15); x0,y0,x1,y1=70,1180,1010,1320
        txt(d,x0,y0-6,'BLOOD PRESSURE',f(MONO,22),CREAM,b)
        p=clamp((t-63.5)/0.8); pts=[]
        for i in range(41):
            u=i/40*p; v=0.85 if u<0.35 else lerp(0.85,0.35,ease_io((u-0.35)/0.65))
            pts.append((lerp(x0+250,x1,u),lerp(y1,y0+20,v)))
        if len(pts)>1: d.line(pts,fill=A(GREEN,b),width=6); GL and GL.line(pts,fill=A(GREEN,b),width=12)
        if p>0.9: bigarrow(d,x1-30,y0+30,y1-6,GREEN,22,b)
# ---- 10. study document (talk, tilted paper) ----
DOCIM=None
def make_doc():
    w,h=860,250; im=Image.new('RGB',(w,h),(236,234,226)); d=ImageDraw.Draw(im)
    for y in range(0,h,3): d.line([(0,y),(w,y)],fill=(230,228,220))
    d.rectangle([0,0,w,52],fill=COARED); d.text((22,10),'CLINICAL STUDIES · TELMISARTAN',font=f(MONO,26),fill=WHITE)
    d.text((22,72),'POPULATION',font=f(MONO,20),fill=(110,110,118)); d.text((22,98),'Hypertensive patients',font=f(DMB,34),fill=(20,22,30))
    d.text((22,152),'OUTCOME',font=f(MONO,20),fill=(110,110,118)); d.text((22,178),'Regression of left ventricular mass',font=f(DMB,34),fill=(20,22,30))
    return im
def sc_study(im,d,t):
    global DOCIM
    t0,t1=64.75,70.70; a=win(t,t0,t1,0.01,0.10)
    if a<=0: return
    if DOCIM is None: DOCIM=make_doc()
    doc=DOCIM.copy().convert('RGBA'); hl=Image.new('RGBA',doc.size,(0,0,0,0)); dd=ImageDraw.Draw(hl,'RGBA')
    if t>=66.74:   # population highlight
        p=clamp((t-66.74)/0.45); dd.rectangle([18,98,18+lerp(0,370,p),140],fill=(255,194,26,110))
    if t>=68.38:   # outcome highlight
        p=clamp((t-68.38)/0.8); dd.rectangle([18,178,18+lerp(0,600,p),220],fill=(255,194,26,130))
    doc=Image.alpha_composite(doc,hl); dd=ImageDraw.Draw(doc,'RGBA')
    if t>=69.36:
        b=ap(t,69.36,0.15); cx,cy=770,165; wall=lerp(52,26,expo((t-69.5)/0.7)); R=58
        dd.ellipse([cx-R,cy-R,cx+R,cy+R],fill=(200,40,50,int(255*b))); r=R-wall; dd.ellipse([cx-r,cy-r,cx+r,cy+r],fill=(236,234,226,int(255*b)))
        dd.text((cx,cy+R+2),'LV MASS',font=f(MONO,16),fill=(150,20,30,int(255*b)),anchor='ma')
    p=expo((t-t0)/0.3); ang=lerp(-14,-3,p)
    rot=doc.rotate(ang,resample=Image.BICUBIC,expand=True)
    sh=Image.new('RGBA',rot.size,(0,0,0,0)); sh.putalpha(rot.split()[3].point(lambda v:int(v*0.6))); sh=sh.filter(ImageFilter.GaussianBlur(14))
    x=int(lerp(-900,100,p)+lerp(0,-1200,clamp((t-t1)/0.10))); y=int(lerp(1500,1140,p))
    sh=layer_alpha(sh,a); rot=layer_alpha(rot,a); im.paste(sh,(x+12,y+18),sh); im.paste(rot,(x,y),rot)
    if t>=68.38:
        d2=ImageDraw.Draw(im,'RGBA'); tag(d2,x+40,y-40,'REGRESSION',GREEN,26,a*ap(t,68.5,0.1))
# ---- 11. stacked bonus chips (talk) ----
def sc_bonus(im,d,t):
    t1=80.20
    chips=[(73.92,'+ INSULIN SENSITIVITY',GREEN,None),(76.62,'+ ANDROGEN RECEPTORS',CYAN,'SOME STUDIES'),(79.24,'PART 2 · NEXT VIDEO',VGOLD,None)]
    n=sum(1 for c in chips if t>=c[0])
    for i,(tt,lab,col,note) in enumerate(chips):
        if t<tt: continue
        a=win(t,tt,t1,0.14,0.14)
        if a<=0: continue
        # stack: newest at the bottom, older pushed up
        later=[c for c in chips[i+1:] if t>=c[0]]
        push=sum(expo((t-c[0])/0.2) for c in later)
        y=1290-push*78; x=lerp(-700,48,expo((t-tt)/0.22))
        fn=f(MONOB,28); tw=d.textlength(lab,font=fn)
        frosted(im,(x,y,x+tw+70,y+62),0.84,10,12,a=a); d=ImageDraw.Draw(im,'RGBA')
        d.rounded_rectangle([x,y,x+tw+70,y+62],radius=12,outline=A(col,a),width=3); GL and GL.rounded_rectangle([x,y,x+tw+70,y+62],radius=12,outline=A(col,a),width=8)
        d.rectangle([x,y+10,x+8,y+52],fill=A(col,a))
        txt(d,x+30,y+14,lab,fn,col,a)
        if note: tag(d,x+tw+84,y+10,note,(70,74,90),20,a*ap(t,tt+0.4,0.1),glow=False)
# ---- 12. comparison columns (lift deck) ----
def sc_compare(im,d,t,oy):
    for i,(nm,col,th,rows) in enumerate([('EZETIMIBE',CYAN,82.16,[('TARGETS',83.18,'CHOLESTEROL'),('',83.58,'ABSORPTION'),('VIA',83.9,'NPC1L1 BLOCK')]),
                                         ('TELMISARTAN',VGOLD,84.52,[('TARGETS',85.64,'BLOOD PRESSURE'),('+',86.46,'ANGIOTENSIN'),('',87.18,'SIGNALING')])]):
        x0=60+i*500; x1=x0+460; y0=1000+oy
        a=ap(t,th-0.1,0.2)
        if a<=0: continue
        p=expo((t-th+0.1)/0.3)
        d.rectangle([x0,y0,x1,1560+oy],fill=A((10,14,24),0.6*a))
        lit_bar(d,x0,y0,lerp(x0,x1,p),y0+8,col,a); GL and GL.rectangle([x0,y0,lerp(x0,x1,p),y0+8],fill=A(col,a))
        txt(d,x0+22,y0+24,f'COMPOUND 0{i+1}',f(MONO,22),col,a)
        fn=f(BEB,88);
        while d.textlength(nm,font=fn)>420: fn=f(BEB,fn.size-4)
        txt(d,x0+20,y0+56,nm,fn,WHITE,a)
        for k,(lab,tt,val) in enumerate(rows):
            if t<tt: continue
            b=ap(t,tt,0.1); y=y0+180+k*118
            if lab: txt(d,x0+22,y,lab,f(MONO,24),MUTED,b)
            txt(d,x0+22,y+30,val,f(BEB,70),col,b)
            if k==0: check(d,x1-56,y+30,GREEN,1.0,b)
# ---- 13. priority re-rank (talk rail) ----
def sc_rank(im,d,t):
    t0,t1=89.40,96.80; a=win(t,t0,t1,0.2,0.16)
    if a<=0: return
    dx=lerp(-380,0,expo((t-t0)/0.24))
    x0,y0,x1,y1=36+dx,560,356+dx,1040
    frosted(im,(x0,y0,x1,y1),0.84,14,a=a); d=ImageDraw.Draw(im,'RGBA')
    d.rectangle([x0,y0,x0+6,y1],fill=A(VGOLD,a)); txt(d,x0+26,y0+18,'PRIORITY',f(MONO,24),VGOLD,a)
    d.line([(x0+26,y0+56),(x1-20,y0+56)],fill=A((80,84,100),a),width=2)
    swap=expo((t-93.16)/0.45) if t>=93.16 else 0
    items=[('BIGGER',89.70),('STRONGER',90.90),('LOOKS',91.72)]
    for i,(nm,tt) in enumerate(items):
        if t<tt: continue
        b=a*ap(t,tt,0.1); y=y0+86+i*76+swap*86
        txt(d,x0+26,y,str(i+1+(1 if swap>0.5 else 0)),f(BEB,52),MUTED,b*(1-0.5*swap))
        txt(d,x0+70,y+6,nm,f(BEB,52),(200,200,206) if swap<0.5 else (110,110,118),b)
        if swap>0: tw=d.textlength(nm,font=f(BEB,52)); d.line([(x0+66,y+32),(x0+66+(tw+10)*clamp(swap*1.5-0.2),y+32)],fill=A(RED,b),width=5)
    if swap>0:
        b=a*swap; y=lerp(y0+300,y0+80,swap)
        d.rectangle([x0+18,y-6,x1-14,y+70],fill=A((60,10,16),b*0.9),outline=A(RED,b),width=3)
        txt(d,x0+26,y,'1',f(BEB,58),VGOLD,b); heart_shape(d,x0+96,y+32,28,RED,b); txt(d,x0+138,y+4,'HEART',f(BEB,60),WHITE,b)
        if t>=94.76: txt(d,x0+28,y1-44,'+ STAY ALIVE',f(MONO,24),GREEN,a*ap(t,94.76,0.12))
# ---- 14. 6 PM clock (talk, calm) ----
def sc_clock(im,d,t):
    t0,t1=99.30,102.50; a=win(t,t0,t1,0.3,0.3)
    if a<=0: return
    cx,cy,R=150,1250,92
    frosted(im,(40,1140,520,1360),0.8,12,18,a=a); d=ImageDraw.Draw(im,'RGBA')
    d.ellipse([cx-R,cy-R,cx+R,cy+R],outline=A(VGOLD,a),width=5); GL and GL.ellipse([cx-R,cy-R,cx+R,cy+R],outline=A(VGOLD,a),width=10)
    for k in range(12):
        th=k/12*2*math.pi; d.line([(cx+(R-14)*math.sin(th),cy-(R-14)*math.cos(th)),(cx+(R-4)*math.sin(th),cy-(R-4)*math.cos(th))],fill=A(CREAM,a),width=3)
    p=expo((t-99.5)/0.6); hr=lerp(-0.6,6/12,p)*2*math.pi; mn=lerp(-0.6*12,0,p)*2*math.pi
    d.line([(cx,cy),(cx+50*math.sin(hr),cy-50*math.cos(hr))],fill=A(WHITE,a),width=8)
    d.line([(cx,cy),(cx+76*math.sin(mn),cy-76*math.cos(mn))],fill=A(WHITE,a),width=4)
    d.ellipse([cx-8,cy-8,cx+8,cy+8],fill=A(VGOLD,a))
    txt(d,270,1180,'6:00 PM',f(BEB,90),WHITE,a); txt(d,272,1276,'EVERY DAY',f(MONO,26),VGOLD,a*ap(t,100.12,0.2))
# ---- 15. CTA end card (lift deck) ----
LOGO=None
def sc_cta(im,d,t,oy):
    global LOGO
    panel_frame(d,40,990+oy,1040,1570+oy,VGOLD,1,30,'FREE · NO COST','@coach.agz')
    if LOGO is None:
        lg=Image.open(WD+'/logo.jpg').convert('RGB'); s=min(lg.size); lg=lg.crop(((lg.width-s)//2,(lg.height-s)//2,(lg.width+s)//2,(lg.height+s)//2)).resize((150,150),Image.LANCZOS)
        m=Image.new('L',(150,150),0); ImageDraw.Draw(m).ellipse([0,0,149,149],fill=255); lg.putalpha(m); LOGO=lg
    im.alpha_composite(LOGO,(70,int(1050+oy))); d=ImageDraw.Draw(im,'RGBA')
    txt(d,250,1052+oy,'CARDIOVASCULAR',f(BEB,74),WHITE,ap(t,103.94,0.15))
    txt(d,250,1124+oy,'BLOODWORK BREAKDOWN',f(BEB,62),VGOLD,ap(t,104.64,0.15))
    for i,(nm,tt) in enumerate([('PROPER DOSAGES',107.66),('TIMING',108.30),('BEST COMPOUNDS',109.44)]):
        if t<tt: continue
        b=ap(t,tt,0.1); x=80+[0,330,0][i]; y=1222+oy+(48 if i==2 else 0)
        x=[80,420,80][i]
        check(d,x,y+4,GREEN,0.9,b); txt(d,x+44,y,nm,f(MONO,28),WHITE,b)
    if t>=111.68:
        b=expo((t-111.68)/0.12); s=lerp(1.12,1.0,b)
        fn=f(BEB,int(96*s)); label='COMMENT  "HEALTH"'; tw=d.textlength(label,font=fn)
        x0=(W-tw-60)/2; y0=1360+oy
        lit_bar(d,x0,y0,x0+tw+60,y0+int(112*s),VGOLD,b); d.text((x0+30,y0+8),label,font=fn,fill=A(INK,b))
        GL and GL.rectangle([x0-4,y0-4,x0+tw+64,y0+int(112*s)+4],outline=A(VGOLD,b),width=12)
    txt(d,W/2,1530+oy,'FOR RESEARCH & EDUCATIONAL PURPOSES ONLY',f(MONO,18),MUTED,0.9,anchor='ma')

# scene timetable. layout scenes drive the footage layout.
LAYOUT=[ # (t_in, t_out, kind, fn)
 (21.00,29.98,'lift',sc_lipids),
 (30.10,41.36,'pipR',sc_ezet),
 (47.90,53.80,'lift',sc_bp),
 (58.60,64.62,'pipL',sc_telmi),
 (80.20,87.90,'lift',sc_compare),
 (103.50,DUR+1,'lift',sc_cta),
]
OVERLAYS=[sc_plan,sc_ecg,sc_two,sc_stats,sc_file,sc_study,sc_bonus,sc_rank,sc_clock]
CHAPTERS=[(19.02,20.95,'01','LIPIDS','HDL · LDL · APOB',20.30),(44.50,47.80,'02','BLOOD PRESSURE','+ CARDIOVASCULAR REMODELING',46.20)]
def layout_at(t):
    for (a,b,k,fn) in LAYOUT:
        if a-0.001<=t<b+0.30:
            e=min(ease_io((t-a)/0.30),1-ease_io((t-b)/0.30))
            return k,e,fn,a,b
    return 'talk',0,None,0,0
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
    idx=GROUPS.index(lo)
    if t>end and (idx+1>=len(GROUPS) or WORDS[GROUPS[idx+1][0]]['s']>t): return None
    return lo
def clean(w):
    s=w.upper().strip('.,?!')
    return {'APOB':'APOB','6':'6','PM':'PM'}.get(s,s)
def captions(im,t,cy,base=118):
    g=group_at(t)
    if not g: return
    d=ImageDraw.Draw(im,'RGBA')
    ws=[clean(WORDS[i]['w']) for i in g]
    size=base
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
    for k,(w_,x_) in enumerate(zip(ws,xs)): sd.text((x_+4,44),w_,font=fn,fill=(0,0,0,220))
    cap.alpha_composite(shd.filter(ImageFilter.GaussianBlur(6)))
    lit_bar(cd,bx0,40+size*0.02,bx1,40+size*0.98,RED)
    for k,(w_,x_) in enumerate(zip(ws,xs)): cd.text((x_,40),w_,font=fn,fill=CREAM,stroke_width=0 if k==act else 3,stroke_fill=(0,0,0))
    if abs(s-1)>0.002:
        cap=cap.resize((int(W*s),int(CH*s)),Image.BICUBIC); ox=int((W-cap.width)/2); oy=int(cy-40-(cap.height-CH)/2)
    else: ox,oy=0,int(cy-40)
    im.paste(cap,(ox,oy),cap)
# ---------------- text hook + topic band ----------------
def text_hook(im,t):
    if t>=5.45: return
    a=1-clamp((t-5.30)/0.15)
    d=ImageDraw.Draw(im,'RGBA'); s=lerp(1.0,1.04,clamp(t/5.3))
    fn=f(BAR,int(92*s))
    l1=[('2 compounds protecting',WHITE)]; l2=[('your ',WHITE),('HEART',VGOLD),(' on cycle',WHITE)]
    ys=[262,262+int(100*s)]
    widths=[sum(d.textlength(p,font=fn) for p,_ in L) for L in (l1,l2)]
    bw=max(widths)+70; bx0=(W-bw)/2
    d.rounded_rectangle([bx0,ys[0]-16,bx0+bw,ys[1]+int(104*s)],radius=22,fill=(4,6,12,int(185*a)))
    for L,y,wd in zip((l1,l2),ys,widths):
        x=(W-wd)/2
        for p,c in L:
            d.text((x,y),p,font=fn,fill=A(c,a),stroke_width=2,stroke_fill=(0,0,0,int(255*a)))
            if c==VGOLD and GL: GL.text((x,y),p,font=fn,fill=A(VGOLD,a*0.7))
            x+=d.textlength(p,font=fn)
def topic_band(im,t,vis):
    if t<5.30 or t>=58.10 or vis<=0: return
    a=clamp((t-5.30)/0.15)*(1-clamp((t-57.95)/0.15))*vis
    if a<=0: return
    d=ImageDraw.Draw(im,'RGBA')
    d.rectangle([8,212,W,330],fill=NAVY+(int(220*a),)); d.line([(64,240),(104,240)],fill=A(GOLD,a),width=4)
    txt(d,118,226,'@coach.agz',f(MONO,24),GOLD,a)
    fn=f(BAR,62); x=64; y=254
    for p,c in [('Your ',CREAM),('HEART',VGOLD),(' on cycle',CREAM)]:
        txt(d,x,y,p,fn,c,a); x+=d.textlength(p,font=fn)
    for (t0,t1,num,title,_,_) in CHAPTERS:
        end = 44.40 if num=='01' else 58.0
        if t>=t1-0.1 and t<end:
            b=a*ap(t,t1-0.1,0.2)*(1-clamp((t-end+0.15)/0.15))
            tag(d,W-40,262,f'{num} {title}',VGOLD,30,b,anchor_right=True)
# ---------------- frame ----------------
def seg_of(t):
    k=0
    for i,b in enumerate(BOUNDS):
        if b<=t+1e-6: k=i
    return k
PUNCH=[(70.74,71.40,1.12)]
def frame(src,t):
    global GL
    kind,e,lfn,la,lb=layout_at(t)
    # punch-in: alternate per jump cut; the opening snap lands on "anabolic" (0.70s)
    z=1.0 if seg_of(t)%2==0 else 1.07
    if t<BOUNDS[1]: z=lerp(1.0,1.06,expo((t-0.70)/0.12)) if t>=0.70 else 1.0
    for a,b,zz in PUNCH:
        if a<=t<b: z=zz
    if z!=1.0:
        big=src.resize((int(W*z),int(H*z)),Image.BICUBIC); ox=(big.width-W)//2; oy=int((big.height-H)*0.35); src=big.crop((ox,oy,ox+W,oy+H))
    glow=Image.new('RGBA',(W,H),(0,0,0,0)); GL=ImageDraw.Draw(glow,'RGBA')
    cap_y=1388; cap_size=112
    if kind=='lift' and e>0:
        sh=int(480*e); im=Image.new('RGB',(W,H),DEEP); im.paste(src,(0,-sh))
        ptop=lerp(H,960,e)
        frosted(im,(0,ptop,W,H),0.92,10); d=ImageDraw.Draw(im,'RGBA')
        lit_bar(d,0,ptop,W,ptop+6,VGOLD,1); GL.rectangle([0,ptop,W,ptop+6],fill=A(VGOLD,1))
        lay=Image.new('RGBA',(W,H),(0,0,0,0)); ld=ImageDraw.Draw(lay,'RGBA')
        lfn(lay,ld,t,ptop-960)
        im=im.convert('RGB'); lay=layer_alpha(lay,clamp((e-0.4)/0.6)); im.paste(lay,(0,0),lay)
        cap_y=lerp(1388,846,e); cap_size=int(lerp(112,96,e))
    elif kind in ('pipR','pipL') and e>0:
        bgim=Image.blend(src,src.filter(ImageFilter.GaussianBlur(26)),e)
        bgim=Image.blend(bgim,Image.new('RGB',(W,H),DEEP),0.9*e)
        im=bgim
        sr=(90,250,1000,1460); tr=(600,150,1040,735) if kind=='pipR' else (40,150,480,735)
        r=[lerp(s_,t_,e) for s_,t_ in zip(sr,tr)]
        card=src.crop(sr).resize((int(r[2]-r[0]),int(r[3]-r[1])),Image.LANCZOS).convert('RGBA')
        m=Image.new('L',card.size,0); ImageDraw.Draw(m).rounded_rectangle([0,0,card.width-1,card.height-1],radius=int(26*e),fill=255)
        im.paste(card,(int(r[0]),int(r[1])),m)
        d=ImageDraw.Draw(im,'RGBA')
        d.rounded_rectangle([r[0],r[1],r[2],r[3]],radius=int(26*e),outline=A(VGOLD,e),width=4); GL.rounded_rectangle([r[0],r[1],r[2],r[3]],radius=26,outline=A(VGOLD,e),width=8)
        lay=Image.new('RGBA',(W,H),(0,0,0,0)); ld=ImageDraw.Draw(lay,'RGBA')
        lfn(lay,ld,t)
        im=im.convert('RGB'); lay=layer_alpha(lay,clamp((e-0.5)/0.5)); im.paste(lay,(0,0),lay)
        if e>0.6:
            d=ImageDraw.Draw(im,'RGBA'); d.ellipse([r[0]+18,r[1]+18,r[0]+32,r[1]+32],fill=A(RED,1 if int(t*3)%2==0 else 0.35)); txt(d,r[0]+40,r[1]+12,'COACH',f(MONO,20),WHITE,1)
    else:
        im=src.copy()
    # soft bottom gradient for caption contrast (talk layout only)
    if kind=='talk' or e<0.5:
        yy=np.arange(H); a=np.clip((yy-1150)/300,0,1)*120*(1-e)
        im=im.convert('RGB'); im.paste(Image.new('RGB',(W,H),NAVY),(0,0),Image.fromarray(np.repeat(a.astype(np.uint8)[:,None],W,1)))
    im=im.convert('RGB'); d=ImageDraw.Draw(im,'RGBA')
    if e<0.05:
        for fn_ in OVERLAYS: fn_(im,d,t); d=ImageDraw.Draw(im,'RGBA')
        for (t0,t1,num,title,sub,st) in CHAPTERS: sc_chapter(im,d,t,t0,t1,num,title,sub,st); d=ImageDraw.Draw(im,'RGBA')
    text_hook(im,t)
    topic_band(im,t,1-e)
    GLd=GL; GL=None
    if glow.getbbox():
        sm=glow.resize((W//4,H//4),Image.BILINEAR)
        g1=np.asarray(sm.filter(ImageFilter.GaussianBlur(3.5))).astype(np.float32)/255; g2=np.asarray(sm.filter(ImageFilter.GaussianBlur(10))).astype(np.float32)/255
        prem=np.clip(g1[...,:3]*g1[...,3:]*2.0+g2[...,:3]*g2[...,3:]*1.6,0,1)
        prem=np.asarray(Image.fromarray((prem*255).astype(np.uint8)).resize((W,H),Image.BILINEAR)).astype(np.float32)/255
        b=np.asarray(im.convert('RGB')).astype(np.float32)/255
        im=Image.fromarray(((1-(1-b)*(1-prem))*255).astype(np.uint8))
    d=ImageDraw.Draw(im,'RGBA'); d.rectangle([0,0,7,H],fill=GOLD)
    captions(im,t,cap_y,cap_size)
    return im.convert('RGB')
if __name__=='__main__':
    mode=sys.argv[2]; SRC=WD+'/assembled.mp4'
    if mode=='stills':
        os.makedirs(WD+'/qc',exist_ok=True)
        for tt in [float(x) for x in sys.argv[3:]]:
            subprocess.run(['ffmpeg','-v','error','-y','-ss',f'{tt:.4f}','-i',SRC,'-frames:v','1',WD+'/qc/_src.png'])
            frame(Image.open(WD+'/qc/_src.png').convert('RGB'),tt).resize((540,960),Image.LANCZOS).save(WD+f'/qc/st_{tt:07.2f}.jpg',quality=88)
        sys.exit()
    n0,n1=int(sys.argv[3]),int(sys.argv[4]); out=sys.argv[5]
    dec=subprocess.Popen(['ffmpeg','-v','error','-ss',f'{n0/FPS:.4f}','-i',SRC,'-frames:v',str(n1-n0),'-f','rawvideo','-pix_fmt','rgb24','-'],stdout=subprocess.PIPE)
    enc=subprocess.Popen(['ffmpeg','-v','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-','-c:v','libx264','-crf','12','-preset','fast','-pix_fmt','yuv420p',out],stdin=subprocess.PIPE)
    for n in range(n0,n1):
        buf=dec.stdout.read(W*H*3)
        if len(buf)<W*H*3: print('short',n); break
        enc.stdin.write(frame(Image.frombuffer('RGB',(W,H),buf),n/FPS).tobytes())
    enc.stdin.close(); enc.wait(); dec.kill(); print('done',n0,n1)
