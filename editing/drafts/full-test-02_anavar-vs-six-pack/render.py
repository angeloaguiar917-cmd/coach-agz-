# Anavar vs six pack — full render (1080x1920, 30 fps)
# usage: python3 render.py <build_dir> <fonts_dir> stills t1 t2 ...   |   python3 render.py <build_dir> <fonts_dir> range n0 n1 out.mp4
import json, subprocess, sys, math
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
# Pillow 12 ignores the alpha of a text fill when blending (RGBA draw on RGB), so text
# never faded. Route translucent text through a coverage mask instead.
_orig_text=ImageDraw.ImageDraw.text
def _text(self,xy,text,fill=None,font=None,anchor=None,*args,**kw):
    if isinstance(fill,tuple) and len(fill)==4 and fill[3]<255 and not kw.get('stroke_width'):
        if fill[3]<=2: return
        img=self._image; l,t_,r,b=self.textbbox(xy,text,font=font,anchor=anchor)
        l,t_=int(l)-2,int(t_)-2; r,b=int(r)+3,int(b)+3
        if r<=l or b<=t_: return
        m=Image.new('L',(r-l,b-t_),0); ImageDraw.Draw(m).text((xy[0]-l,xy[1]-t_),text,font=font,fill=fill[3],anchor=anchor)
        if img.mode=='RGBA':
            lay=Image.new('RGBA',m.size,fill[:3]+(0,)); lay.putalpha(m); img.alpha_composite(lay,(l,t_)) if l>=0 and t_>=0 else img.paste(lay,(l,t_),lay)
        else: img.paste(fill[:3],(l,t_,r,b),m)
        return
    return _orig_text(self,xy,text,fill,font,anchor,*args,**kw)
ImageDraw.ImageDraw.text=_text
B=sys.argv[1].rstrip('/')+'/'; F=sys.argv[2].rstrip('/')+'/'
W,H=1080,1920; FPS=30
WORDS=json.load(open(B+'words_final.json')); FR=json.load(open(B+'frames.json'))
CUTS=list(np.cumsum(FR)[:-1]/FPS)          # piece boundaries (jump cuts)
GOLD=(201,169,110); CREAM=(244,241,234); NAVY=(14,17,23); MUTED=(184,184,188); LABEL=(124,124,130)
RED=(255,34,28); VGOLD=(255,194,26); CYAN=(0,229,255); GREEN=(30,255,110); DEEP=(2,3,8); INK=(6,8,14); WHITE=(255,255,255)
CRIM=(200,16,46); CRIM2=(224,36,63); AMBER=(240,160,48); COARED=(210,10,20)
BEB='BebasNeue.ttf'; MONO='JBMono-500.ttf'; MONOB='JBMono-700.ttf'; DMB='DMSans-700.ttf'; DMR='DMSans-400.ttf'; BAR='Barlow-600.ttf'; BARX='Barlow-800.ttf'
_fc={}
def f(n,s):
    k=(n,int(s))
    if k not in _fc: _fc[k]=ImageFont.truetype(F+n,int(s))
    return _fc[k]
def clamp(x,a=0,b=1): return max(a,min(b,x))
def expo(x): x=clamp(x); return 1 if x>=1 else 1-2**(-10*x)
def ease_io(x): x=clamp(x); return 4*x**3 if x<.5 else 1-(-2*x+2)**3/2
def back(x):  # firm settle, tiny overshoot (heavy objects only)
    x=clamp(x); c=1.2; return 1+(c+1)*(x-1)**3+c*(x-1)**2
def lerp(a,b,t): return a+(b-a)*t
def A(c,a): return tuple(c[:3])+(int(clamp(a)*255),)
def ap(t,t0,d=0.16): return expo((t-t0)/d)
def win(t,t0,t1,fi=0.18,fo=0.16):   # alpha for an element living t0..t1
    if t<t0 or t>t1+fo: return 0
    return min(expo((t-t0)/fi), 1-clamp((t-t1)/fo))
GL=None
# ---------------- primitives ----------------
def comp(im,x,pos=(0,0)):
    im.paste(x,(int(pos[0]),int(pos[1])),x)
def txt(d,x,y,s,font,col,a=1.0,anchor='la'): d.text((x,y),s,font=font,fill=A(col,a),anchor=anchor)
def tw(d,s,font): return d.textlength(s,font=font)
def brackets(d,x0,y0,x1,y1,col,L=34,w=4):
    for (cx,cy,sx,sy) in [(x0,y0,1,1),(x1,y0,-1,1),(x0,y1,1,-1),(x1,y1,-1,-1)]:
        d.line([(cx,cy),(cx+sx*L,cy)],fill=col,width=w); d.line([(cx,cy),(cx,cy+sy*L)],fill=col,width=w)
def lit_bar(d,x0,y0,x1,y1,col,a=1.0):
    if x1<=x0: return
    h=max(1,int(y1-y0))
    for i in range(h):
        k=i/h; c=tuple(int(min(255,v*(1.18-0.36*k)+(40 if k<0.12 else 0))) for v in col)
        d.line([(x0,y0+i),(x1,y0+i)],fill=c+(int(255*a),))
def vbar(d,x0,y0,x1,y1,col,a=1.0):   # lit vertical-gradient column (lit from left)
    if y1<=y0: return
    w_=max(1,int(x1-x0))
    for i in range(w_):
        k=i/w_; c=tuple(int(min(255,v*(1.2-0.45*k)+(35 if k<0.12 else 0))) for v in col)
        d.line([(x0+i,y0),(x0+i,y1)],fill=c+(int(255*a),))
def tag(d,x,y,label,col=RED,size=30,a=1.0,glow=True,font=MONOB,anchor='l'):
    fn=f(font,size); w_=tw(d,label,fn); h=size+16
    if anchor=='c': x=x-(w_+24)/2
    if anchor=='r': x=x-(w_+24)
    lit_bar(d,x,y,x+w_+24,y+h,col,a); d.text((x+12,y+h/2),label,font=fn,fill=A(INK if col in (VGOLD,GREEN,CYAN,AMBER) else WHITE,a),anchor='lm')
    if GL and glow and a>0: GL.rectangle([x-4,y-4,x+w_+28,y+h+4],outline=A(col,a),width=8)
    return x+w_+24
def arrow(d,x0,y0,x1,y1,col,w=5,a=1.0,L=20):
    d.line([(x0,y0),(x1,y1)],fill=A(col,a),width=w); ang=math.atan2(y1-y0,x1-x0)
    d.polygon([(x1+4*math.cos(ang),y1+4*math.sin(ang)),(x1-L*math.cos(ang-0.5),y1-L*math.sin(ang-0.5)),(x1-L*math.cos(ang+0.5),y1-L*math.sin(ang+0.5))],fill=A(col,a))
def tri(d,x,y,s,col,a=1,up=True):
    if up: d.polygon([(x,y+s),(x+s,y+s),(x+s/2,y)],fill=A(col,a))
    else: d.polygon([(x,y),(x+s,y),(x+s/2,y+s)],fill=A(col,a))
def check(d,x,y,col,s=1.0,a=1.0):
    pts=[(x,y+16*s),(x+10*s,y+28*s),(x+30*s,y+2*s)]; d.line(pts,fill=A(col,a),width=int(6*s),joint='curve')
    if GL: GL.line(pts,fill=A(col,a),width=int(12*s))
def cross(d,x,y,col,s=1.0,a=1.0):
    d.line([(x,y),(x+28*s,y+28*s)],fill=A(col,a),width=int(6*s)); d.line([(x+28*s,y),(x,y+28*s)],fill=A(col,a),width=int(6*s))
    if GL: GL.line([(x,y),(x+28*s,y+28*s)],fill=A(col,a),width=12); GL.line([(x+28*s,y),(x,y+28*s)],fill=A(col,a),width=12)
def glow_line(d,pts,col,w=5,a=1.0):
    d.line(pts,fill=A(col,a),width=w,joint='curve')
    if GL: GL.line(pts,fill=A(col,a),width=w*2+4)
def frost(im,box,dark=0.86,blur=12,a=1.0,radius=0,tint=DEEP):
    x0,y0,x1,y1=[int(v) for v in box]; x0=max(0,x0); y0=max(0,y0); x1=min(W,x1); y1=min(H,y1)
    if x1<=x0 or y1<=y0 or a<=0: return
    reg=im.crop((x0,y0,x1,y1)).convert('RGB'); fr=Image.blend(reg.filter(ImageFilter.GaussianBlur(blur)),Image.new('RGB',reg.size,tint),dark)
    m=Image.new('L',reg.size,0); ImageDraw.Draw(m).rounded_rectangle([0,0,reg.width-1,reg.height-1],radius=radius,fill=int(255*clamp(a)))
    im.paste(fr,(x0,y0),m)
def card(im,box,a,bar=CRIM,radius=26,edge=None):   # Reel overlay look B: charcoal glass + coloured left bar
    if a<=0: return
    frost(im,box,0.88,14,a,radius,(12,12,14)); d=ImageDraw.Draw(im,'RGBA'); x0,y0,x1,y1=box
    d.rounded_rectangle(box,radius=radius,outline=A(edge or (60,58,62),a*0.9),width=2)
    d.rounded_rectangle([x0,y0+18,x0+10,y1-18],radius=4,fill=A(bar,a))
    if GL: GL.rounded_rectangle([x0-2,y0+16,x0+12,y1-16],radius=4,fill=A(bar,a*0.9))
def shadow_layer(im,lay,off=(0,8),blur=14,op=0.55):
    al=lay.split()[3].point(lambda v:int(v*op)); sh=Image.new('RGBA',lay.size,(0,0,0,0)); sh.putalpha(al)
    sh=sh.filter(ImageFilter.GaussianBlur(blur)); comp(im,sh,off)
def darken_top(im,a,y1=700):
    if a<=0: return
    g=np.zeros((H,),np.float32); yy=np.arange(H); g=np.clip(1-(yy-260)/(y1-260),0,1); g[yy<260]=1
    al=(g*170*a).astype(np.uint8)
    comp(im,Image.merge('RGBA',[Image.new('L',(W,H),c) for c in (4,6,12)]+[Image.fromarray(np.repeat(al[:,None],W,1))]))
# ---------------- icons ----------------
def can(d,x,y,w_,h_,a=1.0,col=VGOLD):
    d.rounded_rectangle([x,y+8,x+w_,y+h_],radius=10,fill=A((30,24,10),a))
    vbar(d,x+2,y+14,x+w_-2,y+h_-6,col,a)
    d.rectangle([x+2,y+h_*0.42,x+w_-2,y+h_*0.62],fill=A((20,20,24),a));
    fn=f(BEB,int(w_*0.32)); txt(d,x+w_/2,y+h_*0.52,'LAGER',fn,CREAM,a,'mm')
    d.ellipse([x+4,y,x+w_-4,y+18],fill=A((210,210,216),a),outline=A((120,120,130),a))
def tablet(d,cx,cy,r,a=1.0):
    d.ellipse([cx-r,cy-r*0.8,cx+r,cy+r*0.8],fill=A((236,234,228),a),outline=A((150,150,150),a),width=2); d.line([(cx,cy-r*0.7),(cx,cy+r*0.7)],fill=A((150,150,150),a),width=2)
def heart(d,cx,cy,s,col,a=1.0):
    r=s*0.3; d.ellipse([cx-2*r,cy-r,cx,cy+r],fill=A(col,a)); d.ellipse([cx,cy-r,cx+2*r,cy+r],fill=A(col,a))
    d.polygon([(cx-2*r+2,cy+r*0.3),(cx+2*r-2,cy+r*0.3),(cx,cy+s*0.75)],fill=A(col,a))
    if GL: GL.ellipse([cx-2.3*r,cy-1.3*r,cx+2.3*r,cy+s*0.8],fill=A(col,a*0.6))
LIVER_N=[(0,0.38),(0.12,0.12),(0.45,0.0),(0.8,0.02),(1.0,0.18),(0.95,0.36),(0.7,0.55),(0.45,0.78),(0.28,0.92),(0.14,0.8),(0.03,0.6)]
def liver_pts(x,y,w_,h_): return [(x+px*w_,y+py*h_) for px,py in LIVER_N]
def hexa(d,cx,cy,r,col,a=1.0,w=4):
    pts=[(cx+r*math.cos(math.pi/3*i+math.pi/6),cy+r*math.sin(math.pi/3*i+math.pi/6)) for i in range(6)]
    d.line(pts+[pts[0]],fill=A(col,a),width=w)
def droplet(d,cx,cy,r,col,a=1.0):
    d.ellipse([cx-r,cy-r*0.4,cx+r,cy+r*1.2],fill=A(col,a)); d.polygon([(cx-r*0.86,cy+r*0.1),(cx+r*0.86,cy+r*0.1),(cx,cy-r*1.3)],fill=A(col,a))
# ---------------- TOP DOCK geometry ----------------
DX0,DY0,DX1,DY1=48,284,1032,664
# ---------- A. HOOK: VS contender cards (sides, below eyes) ----------
def hook_cards(im,t):
    if not (1.48<=t<7.75): return
    for side in (0,1):
        t0=1.48 if side==0 else 3.44
        if t<t0: continue
        pin=expo((t-t0)/0.22); pout=clamp((t-7.40)/0.2)
        x0=(22 if side==0 else 800); w_=258; y0=1010; y1=1352
        dx=(-1 if side==0 else 1)*(lerp(300,0,pin)+420*pout**2); x0+=dx
        a=clamp(pin*1.4)*(1-pout); col=VGOLD if side==0 else RED
        card(im,(x0,y0,x0+w_,y1),a,bar=col,radius=22)
        d=ImageDraw.Draw(im,'RGBA')
        txt(d,x0+28,y0+20,'CONTENDER '+('A' if side==0 else 'B'),f(MONOB,22),col,a)
        if side==0:
            txt(d,x0+28,y0+52,'ANAVAR',f(BEB,74),CREAM,a); txt(d,x0+28,y0+128,'50 MG',f(BEB,64),VGOLD,a); txt(d,x0+28,y0+192,'EVERY DAY',f(MONOB,24),MUTED,a)
            for i in range(5):
                q=ap(t,t0+0.18+i*0.06,0.12); tablet(d,x0+44+i*44,y0+268+lerp(-30,0,q),17,a*q)
        else:
            txt(d,x0+28,y0+52,'SIX PACK',f(BEB,74),CREAM,a); txt(d,x0+28,y0+128,'OF BEER',f(BEB,64),RED,a); txt(d,x0+28,y0+192,'EVERY NIGHT',f(MONOB,24),MUTED,a)
            for i in range(6):
                q=ap(t,t0+0.18+i*0.05,0.12); can(d,x0+26+i*36,y0+232+lerp(-30,0,q),30,64,a*q)
        if t>=6.36:
            q=ap(t,6.36+side*0.08,0.12)*(1-pout); y=y1+12
            tag(d,x0+w_/2,y,'WORSE ?',RED,28,q,anchor='c')
    # versus slash between the cards on "versus"
# ---------- B. agenda tracker ----------
AG=[('01','SCIENCE + MECHANICS'),('02','SIMPLIFY'),('03','OPTIMIZE')]
def agenda(im,t):
    for (t0,t1,lit) in [(7.70,10.95,[8.26,9.46,10.42]),(70.92,76.50,[None,71.26,None])]:
        a=win(t,t0,t1)
        if a<=0: continue
        darken_top(im,a*0.6,560); d=ImageDraw.Draw(im,'RGBA')
        txt(d,DX0+12,DY0+6,'—— THE BREAKDOWN',f(MONOB,24),GOLD,a)
        x=DX0+12; y=DY0+60
        for i,(n,lab) in enumerate(AG):
            fn=f(BARX,40); w_=tw(d,lab,fn)+96; on=False; done=False
            if t0<20:
                on = t>=lit[i]; act = on and (i==2 or t<lit[i+1] if i<2 else on)
            else:
                done = i==0; on = (i==1 and t>=lit[1]); act=on
            q=ap(t,lit[i]) if (lit[i] and on) else (1 if done else 0)
            col=VGOLD if act else (GREEN if done else (90,92,104))
            if act: lit_bar(d,x,y,x+w_,y+68,VGOLD,a*q);
            else: frost(im,(x,y,x+w_,y+68),0.8,8,a,10); d=ImageDraw.Draw(im,'RGBA'); d.rounded_rectangle([x,y,x+w_,y+68],radius=10,outline=A(col,a),width=3)
            if act and GL: GL.rectangle([x-4,y-4,x+w_+4,y+72],outline=A(VGOLD,a*q),width=10)
            txt(d,x+18,y+34,n,f(MONOB,26),INK if act else col,a,'lm')
            txt(d,x+70,y+36,lab,fn,INK if act else (CREAM if (on or done) else (130,132,144)),a,'lm')
            if done: check(d,x+w_-44,y+20,GREEN,0.9,a)
            if i<2:
                nx=x+w_+14
                if nx+40>DX1:  # wrap
                    pass
            x=x+w_+18
            if i==0: x=DX0+12; y=y+86
# ---------- C. three systems ring triad ----------
RINGS=[(220,'LIVER',16.86),(540,'LIPIDS',17.70),(860,'TESTOSTERONE',19.34)]
def ring_icon(d,cx,cy,k,col,a):
    if k==0: d.polygon(liver_pts(cx-52,cy-34,104,70),fill=A(col,a))
    elif k==1:
        for (dx,dy,r) in [(-22,8,18),(18,-6,22),(8,26,14),(-8,-24,12)]: d.ellipse([cx+dx-r,cy+dy-r,cx+dx+r,cy+dy+r],fill=A(col,a))
    else: hexa(d,cx,cy,38,col,a,6); txt(d,cx,cy+2,'T',f(BEB,52),col,a,'mm')
def triad(im,t,t0=10.98,t1=22.80):
    a=win(t,t0,t1)
    if a<=0: return
    darken_top(im,a*0.9,720); d=ImageDraw.Draw(im,'RGBA')
    txt(d,DX0+12,DY0+4,'—— SAME 3 SYSTEMS',f(MONOB,24),GOLD,a*ap(t,t0))
    # attackers
    for j,(lab,col,tt) in enumerate([('VAR',VGOLD,14.16),('ALCOHOL',RED,14.42)]):
        if t<tt: continue
        q=ap(t,tt)*a; dim = (j==1 and t>=20.48)
        x=640 if j==0 else 780
        tag(d,x,DY0-2,lab,col if not dim else (70,40,40),26,q*(0.35 if dim else 1))
    cy=446; r=82
    for k,(cx,lab,tl) in enumerate(RINGS):
        q=ap(t,t0+0.25+k*0.12,0.22)*a
        if q<=0: continue
        hit=t>=tl; h=ap(t,tl,0.25)
        d.ellipse([cx-r,cy-r,cx+r,cy+r],fill=A((10,12,18),0.9*q),outline=A((70,72,84),q),width=6)
        if hit:
            d.arc([cx-r,cy-r,cx+r,cy+r],-90,-90+360*h,fill=A(RED,q),width=10)
            if GL: GL.arc([cx-r-4,cy-r-4,cx+r+4,cy+r+4],-90,-90+360*h,fill=A(RED,q),width=18)
        # attack lines from tags
        if t>=14.6:
            p=clamp((t-14.6-k*0.1)/0.35)
            for j,sx in enumerate((690,850)):
                if j==1 and t>=20.48: continue
                ex,ey=cx+(-26 if j==0 else 26),cy-r-6
                d.line([(sx,DY0+44),(lerp(sx,ex,p),lerp(DY0+44,ey,p))],fill=A(VGOLD if j==0 else RED,q*0.7),width=3)
        ring_icon(d,cx,cy,k,RED if hit else (150,152,164),q)
        txt(d,cx,cy+r+30,lab,f(BARX,38),CREAM if hit else MUTED,q,'mm')
    if t>=20.48:
        q=ap(t,20.48)*a; x0,y0,x1,y1=RINGS[2][0]-r-14,cy-r-14,RINGS[2][0]+r+14,cy+r+14
        brackets(d,x0,y0,x1,y1,A(RED,q),26,6)
    if t>=21.66:
        q=ap(t,21.66)*a; tag(d,860,cy+r+64,'VAR SOLO · NO TEST BASE',RED,24,q,anchor='c')
# ---------- D/E/F. lipid card: reputation dial -> liver ranking -> HDL/ApoB chart + ECG ----------
def dial(d,t,a):
    cx,cy,R=540,620,250
    for i in range(60):
        k=i/59; ang=math.pi*(1+k)
        col=tuple(int(lerp(c1,c2,k)) for c1,c2 in zip(GREEN,RED)) if k<1 else RED
        x0=cx+R*math.cos(ang); y0=cy+R*math.sin(ang); x1=cx+(R-26)*math.cos(ang); y1=cy+(R-26)*math.sin(ang)
        d.line([(x0,y0),(x1,y1)],fill=A(col,a*(0.85 if i%2==0 else 0.5)),width=7)
    txt(d,cx-R+10,cy-12,'MILD',f(BARX,34),GREEN,a,'ls'); txt(d,cx+R-10,cy-12,'HARSH',f(BARX,34),RED,a,'rs')
    for (lab,col,t0,v0,v1,dur) in [('REPUTATION',VGOLD,24.36,0.0,0.16,0.6),('LIPIDS',RED,25.80,0.16,0.93,0.9)]:
        if t<t0: continue
        q=ap(t,t0)*a; v=lerp(v0,v1,back((t-t0)/dur) if col==RED else expo((t-t0)/dur)); ang=math.pi*(1+v)
        ex=cx+(R-40)*math.cos(ang); ey=cy+(R-40)*math.sin(ang)
        d.line([(cx,cy),(ex,ey)],fill=A(col,q),width=8)
        if GL: GL.line([(cx,cy),(ex,ey)],fill=A(col,q),width=16)
        lx=cx+(R+6)*math.cos(ang); ly=cy+(R+6)*math.sin(ang)
        if col==VGOLD: tag(d,lx-10,ly-58,lab,VGOLD,22,q,anchor='c')
        elif t>t0+0.5: tag(d,min(lx,980),ly-56,lab,RED,22,q*ap(t,t0+0.5),anchor='r')
    d.ellipse([cx-18,cy-18,cx+18,cy+18],fill=A(CREAM,a))
ORALS=[('ANADROL',0.94),('DBOL',0.80),('WINSTROL',0.64),('ANAVAR',0.22)]
def ranking(d,t,a):
    for i,(nm,v) in enumerate(ORALS):
        tt=27.98+i*0.14 if i<3 else 28.94
        q=ap(t,tt,0.2)*a
        if q<=0: continue
        y=DY0+92+i*64; x0=300; x1=x0+lerp(0,640*v,expo((t-tt)/0.45))
        txt(d,DX0+40,y+26,nm,f(BARX,40),CREAM if i==3 else MUTED,q,'lm')
        col=GREEN if i==3 else (RED if i<2 else AMBER)
        lit_bar(d,x0,y+4,x1,y+48,col,q)
        if GL: GL.rectangle([x0,y+4,x1,y+48],fill=A(col,q*0.45))
    if t>=29.3: tag(d,x0+640*0.22+18,DY0+92+3*64+2,'BARELY TOUCHES IT',GREEN,22,ap(t,29.3)*a)
def lipids(d,t,a):
    base=DY0+330; x0=DX0+64
    for k,(nm,col,t0,v0,v1) in enumerate([('HDL',CYAN,30.96,0.82,0.22),('APOB',RED,32.28,0.30,0.95)]):
        bx=x0+k*190; q=ap(t,30.62+k*0.1)*a
        v=v0 if t<t0 else lerp(v0,v1,expo((t-t0)/0.55)); hgt=lerp(0,190,v)
        d.rectangle([bx,base-190,bx+130,base],outline=A((60,62,72),q),width=2)
        vbar(d,bx+4,base-hgt,bx+126,base-2,col,q)
        if GL: GL.rectangle([bx+4,base-hgt,bx+126,base-2],fill=A(col,q*0.5))
        txt(d,bx+65,base+28,nm,f(BARX,38),CREAM,q,'mm')
        if t>=t0+0.2:
            p=ap(t,t0+0.2)*a; tri(d,bx+40,base-hgt-62,46,RED if k==0 else RED,p,up=(k==1))
    # ApoB -> heart -> ECG
    if t>=35.02:
        q=ap(t,35.02)*a; hx,hy=560,DY0+150
        arrow(d,x0+190+130+10,DY0+120,hx-60,hy,RED,5,q)
        heart(d,hx,hy-10,90,RED,q)
        txt(d,hx+70,hy-30,'HEART DISEASE',f(BARX,38),CREAM,q,'lm'); txt(d,hx+70,hy+12,'APOB PREDICTS IT',f(MONOB,22),RED,q,'lm')
    if t>=36.6:
        p=clamp((t-36.6)/1.6); q=a
        pts=[]; xs=np.linspace(500,990,90)
        for i,xx in enumerate(xs):
            u=(i%30)/30; y=DY0+290
            if 0.35<u<0.4: y-=20
            elif 0.4<=u<0.45: y+=40
            elif 0.45<=u<0.5: y-=110
            elif 0.5<=u<0.55: y+=30
            pts.append((xx,y))
        n=max(2,int(len(pts)*p)); glow_line(d,pts[:n],RED,4,q)
        d.ellipse([pts[n-1][0]-7,pts[n-1][1]-7,pts[n-1][0]+7,pts[n-1][1]+7],fill=A(WHITE,q))
def lipid_card(im,t):
    t0,t1=23.40,38.45; a=win(t,t0,t1,0.22,0.18)
    if a<=0: return
    pin=expo((t-t0)/0.25); dy=lerp(-40,0,pin)
    box=(DX0,DY0-10+dy,DX1,DY1+40+dy); card(im,box,a,CRIM)
    d=ImageDraw.Draw(im,'RGBA')
    # stage + kicker
    if t<27.55: st,kick=0,'ANAVAR · THE "MILD" ORAL'
    elif t<30.55: st,kick=1,'LIVER STRAIN · ORALS (RELATIVE)'
    else: st,kick=2,'LIPID PANEL · ON ANAVAR'
    sw=[23.40,27.55,30.55][st]; sa=a*ap(t,sw,0.18) if st>0 else a
    txt(d,DX0+40,DY0+18+dy,kick,f(MONOB,26),CRIM2,sa)
    txt(d,DX1-24,DY1+18+dy,'@COACH.AGZ',f(MONOB,18),(110,110,116),a,'rs')
    lay=Image.new('RGBA',(W,H),(0,0,0,0)); dl=ImageDraw.Draw(lay,'RGBA')
    if st==0: dial(dl,t,1)
    elif st==1: ranking(dl,t,1)
    else: lipids(dl,t,1)
    if st>0 and t<sw+0.2:   # wipe in new content
        p=expo((t-sw)/0.2); m=Image.new('L',(W,H),0); ImageDraw.Draw(m).rectangle([0,0,int(lerp(DX0,DX1,p)),H],fill=255)
        lay.putalpha(Image.fromarray(np.minimum(np.asarray(lay.split()[3]),np.asarray(m))))
    lay.putalpha(lay.split()[3].point(lambda v:int(v*sa)))
    comp(im,lay,(0,int(dy)))
# ---------- G. side monitor tiles (BP / natural T / test base) ----------
def monitor_tiles(im,t):
    tiles=[(38.52,44.90,640,'BLOOD PRESSURE','bp'),(39.95,44.90,880,'NATURAL TEST','t'),(41.74,44.90,1120,'TEST BASE','base'),
           (65.76,67.30,880,'NATURAL TEST','t2')]
    for (t0,t1,y0,lab,kind) in tiles:
        a=win(t,t0,t1,0.2,0.18)
        if a<=0: continue
        p=expo((t-t0)/0.22); x0=lerp(-280,20,p); x1=x0+262; y1=y0+214 if kind!='base' else y0+150
        frost(im,(x0,y0,x1,y1),0.9,10,a,16,(6,8,10)); d=ImageDraw.Draw(im,'RGBA')
        d.rounded_rectangle([x0,y0,x1,y1],radius=16,outline=A((80,84,92),a),width=2)
        txt(d,x0+20,y0+18,lab,f(MONOB,22),MUTED,a)
        if kind=='bp':
            n=int(clamp((t-38.68)/0.7)*10+0.5) if t>=38.68 else 3
            for i in range(10):
                col=GREEN if i<4 else (AMBER if i<7 else RED); on=i<max(3,n)
                yy=y1-30-i*14; d.rectangle([x0+22,yy,x0+150,yy+9],fill=A(col if on else (34,36,40),a))
                if on and GL: GL.rectangle([x0+22,yy,x0+150,yy+9],fill=A(col,a*0.6))
            if n>=8: tri(d,x0+180,y0+70,44,RED,a*ap(t,39.2)); txt(d,x0+178,y0+150,'RISING',f(MONOB,20),RED,a*ap(t,39.2))
        elif kind in ('t','t2'):
            tsw=40.12 if kind=='t' else 66.02; off=t>=tsw; p2=expo((t-tsw)/0.18)
            sx,sy=x0+22,y0+62
            d.rounded_rectangle([sx,sy,sx+120,sy+56],radius=28,fill=A(GREEN if not off else (60,20,20),a))
            kx=lerp(sx+92,sx+28,p2) if off else sx+92
            d.ellipse([kx-24,sy+4,kx+24,sy+52],fill=A(WHITE,a))
            txt(d,sx+140,sy+28,'OFF' if off else 'ON',f(BEB,56),RED if off else GREEN,a,'lm')
            pts=[(x0+22+i*11, y0+180-(40 if (not off or i<10) else lerp(40,0,clamp((i-10)/6))*1)) for i in range(20)]
            if off: pts=[(x0+22+i*11, y0+150+lerp(0,44,clamp((i-8)/6)*p2)) for i in range(20)]
            else: pts=[(x0+22+i*11, y0+150+4*math.sin(i*0.9+t*4)) for i in range(20)]
            glow_line(d,pts,RED if off else GREEN,4,a)
            if kind=='t' and off: txt(d,x0+20,y1-6,'SHUT DOWN',f(MONOB,20),RED,a*p2,'ls')
            if kind=='t2' and off: txt(d,x0+20,y1-6,'ALCOHOL · SUPPRESSED',f(MONOB,18),RED,a*p2,'ls')
        else:
            q=ap(t,43.76); d.rounded_rectangle([x0+22,y0+56,x1-22,y0+118],radius=10,outline=A((120,120,130),a),width=3)
            for k in range(0,int(x1-x0-60),18): d.line([(x0+30+k,y0+112),(x0+44+k,y0+62)],fill=A((50,52,60),a),width=2)
            txt(d,(x0+x1)/2,y0+87,'EMPTY',f(BEB,44),RED,a*q,'mm')
            if GL and q>0: GL.rounded_rectangle([x0+22,y0+56,x1-22,y0+118],radius=10,outline=A(RED,a*q),width=8)
            d.rounded_rectangle([x0+22,y0+56,x1-22,y0+118],radius=10,outline=A(RED,a*q),width=4)
# ---------- H. six pack pictogram -> 80 g -> Rx label -> liver queue ----------
RX=None
def make_rx():
    im=Image.new('RGBA',(560,250),(0,0,0,0)); d=ImageDraw.Draw(im)
    d.rectangle([0,0,559,249],fill=(240,238,232)); d.rectangle([0,0,559,54],fill=COARED)
    d.text((20,27),'Rx  ·  DISPENSED NIGHTLY',font=f(MONOB,26),fill=WHITE,anchor='lm')
    d.text((20,72),'ETHANOL',font=f(BEB,72),fill=INK); d.text((250,82),'80 g',font=f(BEB,60),fill=COARED)
    d.text((20,150),'SIG: TAKE 6 BY MOUTH AFTER WORK',font=f(MONOB,22),fill=(60,60,66))
    d.text((20,184),'REFILLS: UNLIMITED  ·  NO LABS',font=f(MONOB,22),fill=(60,60,66))
    d.line([(20,222),(540,222)],fill=(200,198,190),width=2)
    for k in range(0,560,7): d.point((k,(k*13)%250),fill=(200,198,190))
    return im
def sixpack(im,t):
    a=win(t,46.95,55.20,0.18,0.18)
    if a<=0: return
    darken_top(im,a*0.9,720); d=ImageDraw.Draw(im,'RGBA')
    global RX
    if t<53.25:
        txt(d,DX0+12,DY0+4,'—— ONE SIX PACK · ONE NIGHT',f(MONOB,24),GOLD,a)
        cz=expo((t-49.10)/0.3) if t>=49.10 else 0
        for i in range(6):
            q=ap(t,47.08+i*0.07,0.14)*a
            if q<=0: continue
            cw=lerp(120,72,cz); ch=lerp(250,150,cz); gap=lerp(36,14,cz)
            x=lerp(78,DX0+24,cz)+i*(cw+gap); y=DY0+70+lerp(-60,0,expo((t-47.08-i*0.07)/0.18))
            can(d,x,y,cw,ch,q)
        if t>=49.26:
            q=ap(t,49.26)*a; v=int(lerp(0,80,expo((t-49.26)/0.6)))
            txt(d,600,DY0+40,'≈',f(BEB,120),VGOLD,q) if False else None
            txt(d,620,DY0+30,f'{v}',f(BEB,210),VGOLD,q); txt(d,620+tw(d,'80',f(BEB,210))+14,DY0+120,'G',f(BEB,110),VGOLD,q)
            txt(d,624,DY0+250,'PURE ALCOHOL / NIGHT',f(MONOB,24),CREAM,q*ap(t,49.6))
            if GL: GL.rectangle([620,DY0+60,900,DY0+230],outline=A(VGOLD,q*0.5),width=10)
        if t>=51.72:
            if RX is None: RX=make_rx()
            p=expo((t-51.72)/0.16); s=lerp(1.25,1.0,p); rot=lerp(-9,-4,p)
            r=RX.resize((int(560*s),int(250*s)),Image.BICUBIC).rotate(rot,expand=True,resample=Image.BICUBIC)
            r.putalpha(r.split()[3].point(lambda v:int(v*a*clamp(p*2))))
            ox=int(DX0+36-(r.width-560)/2); oy=int(DY0+190-(r.height-250)/2)
            shadow_layer(im,Image.new('RGBA',(W,H),(0,0,0,0)),(0,0)) if False else None
            sh=Image.new('RGBA',r.size,(0,0,0,0)); sh.putalpha(r.split()[3].point(lambda v:int(v*0.6))); sh=sh.filter(ImageFilter.GaussianBlur(12))
            comp(im,sh,(ox+6,oy+14)); comp(im,r,(ox,oy))
    else:
        q=a*ap(t,53.25,0.2); d=ImageDraw.Draw(im,'RGBA')
        txt(d,DX0+12,DY0+4,'—— LIVER · PROCESSING QUEUE',f(MONOB,24),GOLD,q)
        rows=[('ALCOHOL','PROCESSING',RED),('FAT BURNING','ON HOLD',(110,112,124)),('EVERYTHING ELSE','WAITING',(110,112,124))]
        jump=expo((t-53.70)/0.35)
        for i,(nm,stt,col) in enumerate(rows):
            slot=[2,0,1][i]; slot=lerp(slot,i,jump)
            y=DY0+64+slot*96; x0=DX0+12; x1=DX1-12
            frost(im,(x0,y,x1,y+80),0.86,8,q,12); d=ImageDraw.Draw(im,'RGBA')
            d.rounded_rectangle([x0,y,x1,y+80],radius=12,outline=A(col,q),width=3)
            txt(d,x0+24,y+40,f'0{round(slot)+1}',f(MONOB,30),col,q,'lm'); txt(d,x0+100,y+42,nm,f(BARX,46),CREAM if i==0 else MUTED,q,'lm')
            if i==0:
                lit_bar(d,x1-300,y+16,x1-20,y+64,RED,q); txt(d,x1-160,y+40,stt,f(MONOB,26),WHITE,q,'mm')
                if GL: GL.rounded_rectangle([x0,y,x1,y+80],radius=12,outline=A(RED,q),width=10)
            else: txt(d,x1-24,y+40,stt,f(MONOB,26),col,q,'rm')
# ---------- I. fatty liver X-ray + marker tickers ----------
RNG=np.random.default_rng(3); FAT=[(RNG.uniform(0.15,0.85),RNG.uniform(0.15,0.7),RNG.uniform(6,15)) for _ in range(42)]
def fatty_liver(im,t):
    t0,t1=55.26,61.95; a=win(t,t0,t1)
    if a<=0: return
    box=(DX0,DY0-6,DX1,DY1+30); frost(im,box,0.92,14,a,8,(1,6,10)); d=ImageDraw.Draw(im,'RGBA')
    x0,y0,x1,y1=box
    d.rectangle(box,outline=A(CYAN,a*0.35),width=2); brackets(d,x0,y0,x1,y1,A(VGOLD,a),40,6)
    if GL: brackets(GL,x0,y0,x1,y1,A(VGOLD,a),40,12)
    d.ellipse([x0+24,y0+24,x0+40,y0+40],fill=A(RED,a if int(t*4)%2==0 else a/3))
    txt(d,x0+54,y0+18,'LIVER · SCAN',f(MONOB,24),WHITE,a); txt(d,x1-24,y0+18,'EVIDENCE',f(MONOB,24),VGOLD,a,'ra')
    for yy in range(int(y0)+60,int(y1),6): d.line([(x0+2,yy),(x0+440,yy)],fill=A(CYAN,a*0.05),width=1)
    lp=liver_pts(x0+40,y0+90,380,260)
    d.polygon(lp,fill=A((0,60,80),a*0.35)); d.line(lp+[lp[0]],fill=A(CYAN,a),width=4)
    if GL: GL.line(lp+[lp[0]],fill=A(CYAN,a),width=12)
    n=int(len(FAT)*clamp((t-55.96)/1.6)) if t>=55.96 else 0
    from PIL import ImageDraw as _ID
    msk=Image.new('L',(W,H),0); _ID.Draw(msk).polygon(lp,fill=255)
    fl=Image.new('RGBA',(W,H),(0,0,0,0)); fd=ImageDraw.Draw(fl,'RGBA')
    for (u,v,r) in FAT[:n]:
        cx=x0+40+u*380; cy=y0+90+v*260; fd.ellipse([cx-r,cy-r,cx+r,cy+r],fill=A((255,224,120),a*0.9),outline=A((255,200,60),a),width=2)
    fl.putalpha(Image.fromarray(np.minimum(np.asarray(fl.split()[3]),np.asarray(msk)))); comp(im,fl); d=ImageDraw.Draw(im,'RGBA')
    if n>6: tag(d,x0+60,y1-62,'FAT BUILDING INSIDE',VGOLD,22,a*ap(t,56.8))
    # tickers
    for k,(nm,tt) in enumerate([('GGT',58.08),('TRIGLYCERIDES',59.60),('VISCERAL FAT',60.86)]):
        if t<tt: continue
        q=ap(t,tt)*a; y=y0+80+k*104; tx=x0+480
        d.line([(tx,y+92),(x1-24,y+92)],fill=A((40,44,56),q),width=2)
        txt(d,tx,y+10,nm,f(BARX,40),CREAM,q)
        p=clamp((t-tt)/0.7); pts=[(tx+i*16, y+80-((i/14)**1.6)*44-3*math.sin(i*1.7)) for i in range(15)]
        m=max(2,int(15*p)); glow_line(d,pts[:m],RED,4,q)
        tri(d,x1-120,y+16,36,RED,q); txt(d,x1-74,y+36,'UP',f(BEB,52),RED,q,'lm')
# ---------- J. hazard placard ----------
def hazard(im,t):
    t0,t1=62.95,66.95; a=win(t,t0,t1,0.14)
    if a<=0: return
    p=expo((t-t0)/0.18); s=lerp(1.12,1.0,p)
    x0,y0,x1,y1=DX0+60,DY0+10,DX1-60,DY1-10
    cx,cy=(x0+x1)/2,(y0+y1)/2; w_=(x1-x0)*s; h_=(y1-y0)*s; x0,x1,y0,y1=cx-w_/2,cx+w_/2,cy-h_/2,cy+h_/2
    lay=Image.new('RGBA',(W,H),(0,0,0,0)); d=ImageDraw.Draw(lay,'RGBA')
    d.rectangle([x0,y0,x1,y1],fill=A(VGOLD,1))
    for k in range(-400,1400,56): d.polygon([(x0+k,y0),(x0+k+28,y0),(x0+k+28-(y1-y0),y1),(x0+k-(y1-y0),y1)],fill=A(INK,1))
    d.rectangle([x0+22,y0+22,x1-22,y1-22],fill=A((12,12,14),1))
    # diamond symbol
    dx,dy=x0+130,(y0+y1)/2; r=86
    d.polygon([(dx,dy-r),(dx+r,dy),(dx,dy+r),(dx-r,dy)],fill=A(RED,1)); d.polygon([(dx,dy-r+12),(dx+r-12,dy),(dx,dy+r-12),(dx-r+12,dy)],outline=A(WHITE,1),width=4)
    txt(d,dx,dy-6,'!',f(BEB,110),WHITE,1,'mm')
    tx=x0+250
    txt(d,tx,y0+44,'WHO · IARC CLASSIFICATION',f(MONOB,24),VGOLD,1)
    txt(d,tx,y0+80,'GROUP 1',f(BEB,96),CREAM,1); txt(d,tx,y0+170,'CARCINOGEN',f(BEB,96),RED,1)
    txt(d,tx,y0+272,'SAME GROUP: TOBACCO · ASBESTOS',f(MONOB,22),MUTED,1)
    lay.putalpha(lay.split()[3].point(lambda v:int(v*a)))
    sh=Image.new('RGBA',(W,H),(0,0,0,0)); sh.putalpha(lay.split()[3].point(lambda v:int(v*0.6))); comp(im,sh.filter(ImageFilter.GaussianBlur(16)),(0,10))
    comp(im,lay)
    if GL: GL.rectangle([x0,y0,x1,y1],outline=A(VGOLD,a*0.8),width=10)
    d=ImageDraw.Draw(im,'RGBA')
    if t>=64.92:
        q=ap(t,64.92,0.1)*a; tag(d,x1-30,y1-74,'POISON',RED,34,q,anchor='r')
# ---------- K. damage-profile radar ----------
AX=[('LIVER',-90),('TESTOSTERONE',30),('LIPIDS',150)]
def radar(im,t):
    t0,t1=67.36,70.85; a=win(t,t0,t1)
    if a<=0: return
    darken_top(im,a*0.95,740); d=ImageDraw.Draw(im,'RGBA')
    cx,cy,R=540,478,158
    txt(d,DX0+12,DY0+4,'—— DAMAGE PROFILE',f(MONOB,24),GOLD,a)
    for k in (0.33,0.66,1.0):
        pts=[(cx+R*k*math.cos(math.radians(an)),cy+R*k*math.sin(math.radians(an))) for _,an in AX]; d.line(pts+[pts[0]],fill=A((70,74,88),a),width=2)
    for i,(lab,an) in enumerate(AX):
        q=ap(t,t0+i*0.1)*a; ex,ey=cx+R*math.cos(math.radians(an)),cy+R*math.sin(math.radians(an))
        d.line([(cx,cy),(ex,ey)],fill=A((90,94,110),q),width=2)
        d.ellipse([ex-16,ey-16,ex+16,ey+16],outline=A(RED,q),width=5)
        lx,ly=cx+(R+44)*math.cos(math.radians(an)),cy+(R+44)*math.sin(math.radians(an))
        txt(d,lx,ly,lab,f(BARX,36),CREAM,q,'mm' if i==0 else ('lm' if i==1 else 'rm'))
    for (nm,col,vals,tt) in [('VAR',VGOLD,[0.22,0.82,0.92],69.08),('ALCOHOL',RED,[0.96,0.62,0.58],69.32)]:
        if t<tt: continue
        p=expo((t-tt)/0.4); q=a
        pts=[(cx+R*v*p*math.cos(math.radians(an)),cy+R*v*p*math.sin(math.radians(an))) for v,(_,an) in zip(vals,AX)]
        d.polygon(pts,fill=A(col,0.22*q)); d.line(pts+[pts[0]],fill=A(col,q),width=5)
        if GL: GL.line(pts+[pts[0]],fill=A(col,q),width=12)
    if t>=69.08: tag(d,DX0+12,DY1-40,'VAR',VGOLD,26,ap(t,69.08)*a)
    if t>=69.32: tag(d,DX1-12,DY1-40,'ALCOHOL',RED,26,ap(t,69.32)*a,anchor='r')
# ---------- M. PiP scene: two timelines ----------
PIP=(76.55,93.00)
def pip_geom(t):
    t0,t1=PIP; pin=ease_io((t-t0)/0.45); pout=ease_io((t-t1)/0.4)
    return pin*(1-pout)
def timelines(im,t,a):
    d=ImageDraw.Draw(im,'RGBA')
    txt(d,64,300,'—— WHO IS ACTUALLY',f(MONOB,24),GOLD,a); txt(d,64,336,'TRACKING',f(BEB,96),CREAM,a); txt(d,64,428,'IT?',f(BEB,96),VGOLD,a)
    # lane A
    LA=(64,700,1016,1000); x0,y0,x1,y1=LA
    qa=ap(t,77.02,0.25)*a
    if qa>0:
        d.rounded_rectangle(LA,radius=18,fill=A((24,26,34),qa),outline=A((58,54,48),qa),width=2)
        txt(d,x0+24,y0+20,'MAN A · ANAVAR',f(BARX,40),CREAM,qa); txt(d,x1-24,y0+26,'PANEL EVERY 8 WEEKS',f(MONOB,22),VGOLD,qa,'ra')
        gx0,gx1,gy=x0+60,x1-60,y0+190
        d.line([(gx0,gy+60),(gx1,gy+60)],fill=A((80,84,98),qa),width=2)
        ws=[0,8,16,24,32,40]; hv=[0.7,0.68,0.3,0.62,0.7,0.72]
        for i,w_ in enumerate(ws):
            x=lerp(gx0,gx1,i/5); tt=78.54+i*0.12
            if t>=tt:
                q=ap(t,tt,0.1)*qa; d.line([(x,gy+54),(x,gy+66)],fill=A(MUTED,q),width=2); txt(d,x,gy+86,f'W{w_}',f(MONOB,20),MUTED,q,'mm')
                d.ellipse([x-7,gy+53,x+7,gy+67],fill=A(VGOLD,q))
        # HDL line
        prog=clamp((t-79.5)/2.8)
        pts=[(lerp(gx0,gx1,i/5),gy+30-hv[i]*120) for i in range(6)]
        n=prog*5
        for i in range(5):
            if n>i:
                k=min(1,n-i); e=(lerp(pts[i][0],pts[i+1][0],k),lerp(pts[i][1],pts[i+1][1],k))
                glow_line(d,[pts[i],e],CYAN,5,qa)
        txt(d,gx0-40,y0+90,'HDL',f(MONOB,20),CYAN,qa*ap(t,79.5))
        if t>=80.30:
            q=ap(t,80.30)*qa; x,y=pts[2]; d.ellipse([x-12,y-12,x+12,y+12],outline=A(RED,q),width=5); tag(d,x+20,y-8,'HDL DROP · CAUGHT',RED,24,q)
        if t>=82.22:
            q=ap(t,82.22)*qa; x,y=pts[3]; check(d,x-14,y-58,GREEN,1.0,q); tag(d,x+20,y-52,'CORRECTED',GREEN,24,q)
    # lane B
    LB=(64,1030,1016,1340); x0,y0,x1,y1=LB
    qb=ap(t,84.32,0.25)*a
    if qb>0:
        d.rounded_rectangle(LB,radius=18,fill=A((24,26,34),qb),outline=A((90,30,30),qb),width=2)
        txt(d,x0+24,y0+20,'MAN B · 6 PACKS NIGHTLY',f(BARX,40),CREAM,qb); txt(d,x1-24,y0+26,'LABS: NONE',f(MONOB,22),RED,qb*ap(t,87.42),'ra')
        gx0,gx1,gy=x0+60,x1-60,y0+200
        d.line([(gx0,gy+60),(gx1,gy+60)],fill=A((80,84,98),qb),width=2)
        # fog / no data hatch
        for k in range(0,int(gx1-gx0),22): d.line([(gx0+k,gy+50),(gx0+k+40,gy-70)],fill=A((60,62,72),qb*0.6),width=2)
        txt(d,(gx0+gx1)/2-40,gy-10,'NO DATA',f(MONOB,36),(120,122,134),qb,'mm')
        yrs=clamp((t-87.9)/0.7)*5 if t>=87.9 else 0
        for i in range(6):
            x=lerp(gx0,gx1,i/5)
            if i<=yrs+0.01: d.line([(x,gy+54),(x,gy+66)],fill=A(MUTED,qb),width=2); txt(d,x,gy+86,f'YR {i}',f(MONOB,20),MUTED,qb,'mm')
        if t>=87.9:
            xx=lerp(gx0,gx1,yrs/5); d.line([(gx0,gy+60),(xx,gy+60)],fill=A(RED,qb),width=5)
        if t>=89.54:
            q=ap(t,89.54)*qb; hx,hy=gx1,gy-20
            d.rounded_rectangle([hx-40,hy-40,hx+40,hy+40],radius=12,fill=A(RED,q)); d.rectangle([hx-8,hy-26,hx+8,hy+26],fill=A(WHITE,q)); d.rectangle([hx-26,hy-8,hx+26,hy+8],fill=A(WHITE,q))
            if GL: GL.rounded_rectangle([hx-44,hy-44,hx+44,hy+44],radius=12,outline=A(RED,q),width=10)
        if t>=92.38:
            p=expo((t-92.38)/0.12); vx1=lerp(x0,x1,p); vy=y1-86
            lit_bar(d,x0,vy,vx1,vy+86,RED,qb); d.rectangle([x0,vy+82,vx1,vy+86],fill=A((140,0,0),qb))
            if GL: GL.rectangle([x0-4,vy-6,vx1+4,vy+90],outline=A(RED,qb),width=10)
            if p>0.6: txt(d,x0+28,vy+44,'FIRST DATA POINT:',f(MONOB,26),WHITE,qb,'lm'); txt(d,x0+360,vy+46,'LIVER FAILURE',f(BEB,70),WHITE,qb,'lm')
def pip_scene(src,t):
    g=pip_geom(t)
    if g<=0: return None
    # navy carousel background
    bg=Image.new('RGBA',(W,H),NAVY+(255,))
    yy,xx=np.mgrid[0:H:4,0:W:4]; glow=np.clip(1-np.hypot(xx-W,yy-0)/900,0,1)*28
    gl=Image.fromarray(np.dstack([np.full_like(glow,29),np.full_like(glow,29),np.full_like(glow,30),glow]).astype(np.uint8),'RGBA').resize((W,H))
    bg.alpha_composite(gl); bg=bg.convert('RGB')
    TL=pip_target=(640,560,380)  # circle cx,cy,d? (x,y,diam)
    cx,cy,dm=790,462,436
    # interpolate full frame -> circle
    sx0,sy0,sx1,sy1=220,360,1000,1140   # face crop in source (square)
    fx0,fy0,fx1,fy1=lerp(0,cx-dm/2,g),lerp(0,cy-dm/2,g),lerp(W,cx+dm/2,g),lerp(H,cy+dm/2,g)
    cx0,cy0,cx1,cy1=lerp(0,sx0,g),lerp(0,sy0,g),lerp(W,sx1,g),lerp(H,sy1,g)
    crop=src.crop((int(cx0),int(cy0),int(cx1),int(cy1))).resize((max(2,int(fx1-fx0)),max(2,int(fy1-fy0))),Image.BICUBIC).convert('RGBA')
    m=Image.new('L',crop.size,0); rad=int(lerp(0,crop.width/2,g)); ImageDraw.Draw(m).rounded_rectangle([0,0,crop.width-1,crop.height-1],radius=rad,fill=255)
    out=Image.blend(src.convert('RGB'),bg,clamp(g*1.6)) if g<1 else bg.copy()
    a=clamp((g-0.6)/0.4)
    if a>0: timelines(out,t,a)
    out.paste(crop,(int(fx0),int(fy0)),m)
    d=ImageDraw.Draw(out,'RGBA')
    if g>0.5:
        q=clamp((g-0.5)/0.5); d.ellipse([fx0-6,fy0-6,fx1+6,fy1+6],outline=A(GOLD,q),width=6)
        if GL: GL.ellipse([fx0-6,fy0-6,fx1+6,fy1+6],outline=A(VGOLD,q*0.7),width=12)
    return out
# ---------- N. receipt vs schedule III ----------
RCPT=None; LEGAL=None
def make_receipt():
    im=Image.new('RGBA',(400,430),(0,0,0,0)); d=ImageDraw.Draw(im)
    pts=[(0,0),(400,0),(400,410)]+[(400-k*20,410+(10 if k%2 else 0)) for k in range(21)]+[(0,410)]
    d.polygon(pts,fill=(246,244,238))
    y=20
    for s,fn,col in [('GAS & GO  #2214',f(MONOB,26),INK),('OPEN 24 HRS',f(MONO,22),(90,90,96))]: d.text((200,y),s,font=fn,fill=col,anchor='ma'); y+=36
    d.line([(20,y+6),(380,y+6)],fill=(150,150,150),width=2); y+=24
    for l,r in [('6PK LAGER 12OZ','12.99'),('QTY','1'),('ID CHECK','21+'),('PRESCRIPTION','NONE'),('BLOODWORK','NONE'),('DAILY LIMIT','NONE')]:
        d.text((24,y),l,font=f(MONO,22),fill=(40,40,46)); d.text((376,y),r,font=f(MONOB,22),fill=(40,40,46),anchor='ra'); y+=36
    d.line([(20,y+6),(380,y+6)],fill=(150,150,150),width=2); y+=22
    d.text((200,y),'THANK YOU · SEE YOU TOMORROW',font=f(MONO,18),fill=(90,90,96),anchor='ma')
    return im
def make_legal():
    im=Image.new('RGBA',(430,430),(0,0,0,0)); d=ImageDraw.Draw(im)
    d.rectangle([0,0,429,429],fill=(232,230,222)); d.rectangle([0,0,429,58],fill=(30,34,48))
    d.text((20,29),'CONTROLLED SUBSTANCES ACT',font=f(MONOB,22),fill=WHITE,anchor='lm')
    d.text((22,80),'SCHEDULE',font=f(BEB,56),fill=INK); d.text((210,80),'III',font=f(BEB,56),fill=COARED)
    y=150
    for s in ['ANABOLIC STEROIDS','INCL. OXANDROLONE','POSSESSION WITHOUT','A PRESCRIPTION:']:
        d.text((22,y),s,font=f(MONO,24),fill=(50,50,56)); y+=36
    for k in range(5): d.line([(22,y+16+k*22),(lerp(400,260,k/5),y+16+k*22)],fill=(190,188,180),width=6)
    return im
def receipts(im,t):
    t0,t1=97.60,101.85; a=win(t,t0,t1)
    if a<=0: return
    global RCPT,LEGAL
    if RCPT is None: RCPT=make_receipt(); LEGAL=make_legal()
    darken_top(im,a*0.7,720)
    # receipt + stack behind on "every single day"
    stack=int(clamp((t-98.64)/0.6)*3+0.5) if t>=98.64 else 0
    for k in range(stack,-1,-1):
        p=expo((t-t0-k*0.05)/0.25); rot=[3,-5,7,-9][k]; dx=[0,-14,10,-22][k]; dy=[0,8,14,20][k]
        r=RCPT.rotate(rot,expand=True,resample=Image.BICUBIC); r=r.resize((int(r.width*0.86),int(r.height*0.86)))
        al=a*(1 if k==0 else 0.92)*clamp(p*1.5); r.putalpha(r.split()[3].point(lambda v:int(v*al)))
        ox=int(DX0+30+dx); oy=int(lerp(DY0+180,DY0-30,p)+dy)
        if k==0 and t<98.64 or k>0 and p<1 or True:
            sh=Image.new('RGBA',r.size,(0,0,0,0)); sh.putalpha(r.split()[3].point(lambda v:int(v*0.55))); comp(im,sh.filter(ImageFilter.GaussianBlur(10)),(ox+8,oy+14))
        comp(im,r,(ox,oy))
    d=ImageDraw.Draw(im,'RGBA')
    if stack>0: tag(d,DX0+60,DY1+10,f'EVERY DAY',VGOLD,24,a*ap(t,98.64))
    if t>=100.36:
        p=expo((t-100.36)/0.25); r=LEGAL.rotate(-4,expand=True,resample=Image.BICUBIC); r=r.resize((int(r.width*0.86),int(r.height*0.86)))
        r.putalpha(r.split()[3].point(lambda v:int(v*a*clamp(p*1.5)))); ox=int(lerp(1100,600,p)); oy=DY0-24
        sh=Image.new('RGBA',r.size,(0,0,0,0)); sh.putalpha(r.split()[3].point(lambda v:int(v*0.55))); comp(im,sh.filter(ImageFilter.GaussianBlur(10)),(ox+8,oy+14))
        comp(im,r,(ox,oy))
        if t>=101.34:
            q=expo((t-101.34)/0.1); s=lerp(1.4,1.0,q)
            st=Image.new('RGBA',(330,90),(0,0,0,0)); sd=ImageDraw.Draw(st); sd.rounded_rectangle([3,3,326,86],radius=8,outline=(220,20,30,255),width=6)
            sd.text((165,46),'ILLEGAL',font=f(BEB,74),fill=(220,20,30,255),anchor='mm')
            st=st.resize((int(330*s),int(90*s))).rotate(-12,expand=True,resample=Image.BICUBIC); st.putalpha(st.split()[3].point(lambda v:int(v*a*q*0.92)))
            comp(im,st,(int(ox+190-st.width/2),int(oy+310-st.height/2)))
# ---------- O. body scan tile (visible vs invisible) ----------
def body_tile(im,t):
    t0,t1=102.46,113.95; a=win(t,t0,t1,0.22)
    if a<=0: return
    p=expo((t-t0)/0.25); x0=lerp(-320,16,p); x1=x0+300; y0,y1=590,1390
    frost(im,(x0,y0,x1,y1),0.9,12,a,20,(1,6,10)); d=ImageDraw.Draw(im,'RGBA')
    d.rounded_rectangle([x0,y0,x1,y1],radius=20,outline=A(CYAN,a*0.5),width=2); brackets(d,x0,y0,x1,y1,A(CYAN,a),30,5)
    mode = 0 if t<105.28 else 1
    txt(d,x0+20,y0+18,'BODY · SCAN',f(MONOB,22),CYAN,a)
    # torso outline
    cx=(x0+x1)/2; T=[(cx-60,y0+120),(cx-120,y0+170),(cx-125,y0+340),(cx-100,y0+520),(cx-95,y0+640),(cx+95,y0+640),(cx+100,y0+520),(cx+125,y0+340),(cx+120,y0+170),(cx+60,y0+120)]
    d.line(T,fill=A(CYAN,a*0.8),width=3); d.ellipse([cx-40,y0+50,cx+40,y0+125],outline=A(CYAN,a*0.8),width=3)
    if GL: GL.line(T,fill=A(CYAN,a*0.6),width=8)
    lp=liver_pts(cx-92,y0+300,124,80); kid=[(cx-62,y0+420,cx-22,y0+490),(cx+22,y0+420,cx+62,y0+490)]
    bad_l=t>=112.96; bad_k=t>=113.56
    d.polygon(lp,fill=A(RED if bad_l else (0,90,110),a*(0.9 if bad_l else 0.5)),outline=A(RED if bad_l else CYAN,a))
    for k_ in kid: d.ellipse(k_,fill=A(RED if bad_k else (0,90,110),a*(0.9 if bad_k else 0.5)),outline=A(RED if bad_k else CYAN,a),width=3)
    if GL and bad_l: GL.polygon(lp,fill=A(RED,a))
    if GL and bad_k:
        for k_ in kid: GL.ellipse(k_,fill=A(RED,a))
    if mode==0:
        q=ap(t,104.36)*a
        if q>0:
            for i in range(5): d.ellipse([x0+40+i*48-8,y1-112-8,x0+40+i*48+8,y1-112+8],fill=A(GREEN,q))
            d.line([(x0+40,y1-112),(x0+232,y1-112)],fill=A(GREEN,q),width=3)
            tag(d,cx,y1-80,'VAR · VISIBLE',GREEN,22,q,anchor='c')
    else:
        # fog until scan
        reveal = clamp((t-110.40)/1.2) if t>=110.40 else 0
        fog=Image.new('RGBA',(W,H),(0,0,0,0)); fd=ImageDraw.Draw(fog,'RGBA')
        fy=lerp(y0+60,y0+660,reveal)
        rr=np.random.default_rng(int(t*10))
        for _ in range(90):
            fx_=rr.uniform(x0+20,x1-20); fyy=rr.uniform(fy,y0+660)
            if fyy<y0+660: fd.ellipse([fx_-26,fyy-18,fx_+26,fyy+18],fill=(70,74,86,int(110*a)))
        comp(im,fog.filter(ImageFilter.GaussianBlur(8))); d=ImageDraw.Draw(im,'RGBA')
        if 0<reveal<1: d.line([(x0+10,fy),(x1-10,fy)],fill=A(CYAN,a),width=4); GL and GL.line([(x0+10,fy),(x1-10,fy)],fill=A(CYAN,a),width=14)
        yrs=int(clamp((t-107.46)/1.3)*6+0.999) if t>=107.46 else 0
        if reveal<=0:
            txt(d,cx,y1-120,'ALCOHOL',f(MONOB,22),RED,a,'mm')
            txt(d,cx,y1-60,f'YEAR {max(1,yrs)}' if yrs else 'NO LABS',f(BEB,64),CREAM,a,'mm')
        else:
            if bad_l: tag(d,cx,y1-120,'LIVER',RED,24,ap(t,112.96)*a,anchor='c')
            if bad_k: tag(d,cx,y1-66,'KIDNEYS',RED,24,ap(t,113.56)*a,anchor='c')
# ---------- P. roadmap ----------
STEPS=[('GUESS',117.78,RED),('TEST',118.73,VGOLD),('ANALYZE',119.43,VGOLD),('PIVOT',120.19,VGOLD),('OPTIMIZE',120.91,GREEN)]
def roadmap(im,t):
    t0,t1=115.90,121.35; a=win(t,t0,t1)
    if a<=0: return
    darken_top(im,a*0.95,740); d=ImageDraw.Draw(im,'RGBA')
    txt(d,DX0+12,DY0+4,'—— BLOODWORK IS THE ROADMAP',f(MONOB,24),GOLD,a)
    pts=[(lerp(110,980,i/80),470+70*math.sin(i/80*math.pi*2.2)) for i in range(81)]
    p=clamp((t-116.2)/0.9); n=max(2,int(81*p))
    d.line(pts[:n],fill=A((60,62,72),a),width=26,joint='curve')
    for i in range(0,n-1,4): d.line([pts[i],pts[min(i+2,n-1)]],fill=A(VGOLD,a*0.8),width=4)
    for k,(lab,tt,col) in enumerate(STEPS):
        idx=int(k/4*80); x,y=pts[idx]
        if t<tt:
            if p*80>=idx: d.ellipse([x-10,y-10,x+10,y+10],fill=A((90,94,108),a))
            continue
        q=ap(t,tt,0.14)*a; up = k%2==0
        r_=lerp(30,20,q); d.ellipse([x-20,y-20,x+20,y+20],fill=A(col,q))
        if GL: GL.ellipse([x-26,y-26,x+26,y+26],fill=A(col,q))
        ly=y-70 if up else y+70
        fn=f(BARX,46 if k<4 else 54);
        txt(d,x,ly,lab,fn,CREAM if k>0 else (160,160,170),q,'mm')
        if k==0:
            w_=tw(d,lab,fn); d.line([(x-w_/2-6,ly),(x+w_/2+6,ly)],fill=A(RED,q),width=6); cross(d,x-14,y-14,WHITE,1.0,q)
        else: check(d,x-15,y-15,INK,1.0,q)
# ---------- Q. CTA ----------
LOGO=None
MARKERS=['HDL','LDL','APOB','TRIGLYCERIDES','ALT · AST','GGT','BLOOD PRESSURE','TOTAL TEST']
def cta(im,t):
    t0=122.43; a=ap(t,t0,0.25)
    if t<t0: return
    global LOGO
    if LOGO is None:
        lg=Image.open(B+'logo.jpg').convert('RGB'); s=min(lg.size); lg=lg.crop(((lg.width-s)//2,(lg.height-s)//2,(lg.width+s)//2,(lg.height+s)//2)).resize((96,96),Image.LANCZOS)
        m=Image.new('L',(96,96),0); ImageDraw.Draw(m).ellipse([0,0,95,95],fill=255); lg.putalpha(m); LOGO=lg
    box=(DX0,DY0-10,DX1,DY1+50); card(im,box,a,bar=GOLD,edge=(90,80,60))
    lg=LOGO.copy(); lg.putalpha(lg.split()[3].point(lambda v:int(v*a))); comp(im,lg,(DX0+34,DY0+6))
    d=ImageDraw.Draw(im,'RGBA')
    txt(d,DX0+146,DY0+16,'ORAL CYCLE',f(MONOB,24),GOLD,a); txt(d,DX0+146,DY0+44,'BLOODWORK PANEL',f(BEB,62),CREAM,a)
    if t>=128.81: tag(d,DX1-30,DY0+26,'FREE',VGOLD,40,ap(t,128.81),anchor='r')
    sw=expo((t-130.03)/0.2) if t>=130.03 else 0
    if sw<1:
        for i,mk in enumerate(MARKERS):
            tt=125.45+i*0.16
            if t<tt: continue
            q=ap(t,tt,0.12)*a*(1-clamp(sw*4)); x=DX0+60+(i%2)*470; y=DY0+140+(i//2)*58
            check(d,x,y,GREEN,0.85,q); txt(d,x+46,y+14,mk,f(BARX,38),CREAM,q,'lm')
    if sw>0.25:
        sw=clamp((sw-0.25)/0.75); s=lerp(1.15,1.0,sw); fn=f(BEB,int(118*s)); label='COMMENT  "PANEL"'; w_=tw(d,label,fn)
        x0=(DX0+DX1)/2-w_/2-36; y0=DY0+170
        lit_bar(d,x0,y0,x0+w_+72,y0+int(132*s),VGOLD,sw); d.text((x0+36,y0+int(66*s)),label,font=fn,fill=A(INK,sw),anchor='lm')
        if GL: GL.rectangle([x0-4,y0-4,x0+w_+76,y0+int(132*s)+4],outline=A(VGOLD,sw),width=14)
        txt(d,(DX0+DX1)/2,y0+int(132*s)+40,"I'LL SEND IT TO YOU",f(MONOB,24),CREAM,sw*ap(t,131.0),'mm')
# ---------------- text hook (frame 0) + topic band ----------------
def text_hook(im,t):
    if t>=6.15: return
    a=1-clamp((t-6.0)/0.15); d=ImageDraw.Draw(im,'RGBA')
    s=lerp(1.0,1.04,clamp(t/6.0))   # slow 100->104% over the hold
    l1=[('50mg ',CREAM),('ANAVAR',VGOLD),(' vs 6 beers',CREAM)]; l2=[('both hit the same 3 systems',CREAM)]
    fn=f(BEB,int(104*s)); y=300
    for li,line in enumerate((l1,l2)):
        full=''.join(p for p,_ in line); w_=tw(d,full,fn); x=W/2-w_/2; yy=y+li*int(112*s)
        d.rounded_rectangle([x-28,yy-10,x+w_+28,yy+int(104*s)+2],radius=16,fill=A((4,5,8),0.86*a))
        for p,c in line:
            d.text((x,yy),p,font=fn,fill=A(c,a));
            x+=tw(d,p,fn)
def topic_band(im,t):
    if not (6.0<=t<67.45) or (PIP[0]<=t): return
    a=min(clamp((t-6.0)/0.15),1-clamp((t-67.3)/0.15)); d=ImageDraw.Draw(im,'RGBA')
    fn=f(BEB,50); parts=[('ANAVAR',VGOLD),(' vs a six pack',CREAM)]; w_=sum(tw(d,p,fn) for p,_ in parts)
    x0=64; y0=196
    d.rectangle([8,y0,x0+w_+150,y0+64],fill=A(NAVY,0.9*a)); d.line([(x0-30,y0+32),(x0-6,y0+32)],fill=A(GOLD,a),width=4)
    x=x0
    for p,c in parts: d.text((x,y0+8),p,font=fn,fill=A(c,a)); x+=tw(d,p,fn)
    txt(d,x+22,y0+34,'@coach.agz',f(MONO,20),GOLD,a,'lm')
# ---------------- captions ----------------
FIX={'fucking':'F*CKING','anovar':'ANAVAR','eyes':'SCIENCE','var':'VAR','apob':'APOB'}
def build_groups():
    G=[];cur=[]
    for i,x in enumerate(WORDS):
        if cur:
            prev=WORDS[cur[-1]]
            if len(cur)>=3 or x['s']-prev['e']>0.28 or prev['w'][-1] in '.,?!' or any(prev['s']<c<=x['s']+0.01 for c in CUTS): G.append(cur); cur=[]
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
CAP_Y=1392
def captions(im,t):
    g=group_at(t)
    if not g: return
    d=ImageDraw.Draw(im,'RGBA')
    ws=[FIX.get(WORDS[i]['w'].lower().strip('.,?!'),WORDS[i]['w'].strip(',.?!') if WORDS[i]['w'][-1] in ',.' else WORDS[i]['w']).upper() for i in g]
    size=116
    while True:
        fn=f(BEB,size); sp=tw(d,' ',fn)+14; wd=[tw(d,w,fn) for w in ws]; tot=sum(wd)+sp*(len(ws)-1)
        if tot<=900: break
        size-=4
    xs=[];x=(W-tot)/2
    for w_ in wd: xs.append(x); x+=w_+sp
    act=0
    for k,i in enumerate(g):
        if WORDS[i]['s']<=t: act=k
    g0=WORDS[g[0]]['s']; s=lerp(0.9,1,expo((t-g0)/0.10))
    cap=Image.new('RGBA',(W,280),(0,0,0,0)); cd=ImageDraw.Draw(cap); shd=Image.new('RGBA',(W,280),(0,0,0,0)); sd=ImageDraw.Draw(shd)
    prev=max(0,act-1); bt=expo((t-WORDS[g[act]]['s'])/0.07) if act>0 else 1
    bx0=lerp(xs[prev],xs[act],bt)-18; bx1=lerp(xs[prev]+wd[prev],xs[act]+wd[act],bt)+18
    for k,(w_,x_) in enumerate(zip(ws,xs)):
        if k!=act: sd.text((x_+4,46),w_,font=fn,fill=(0,0,0,220))
    cap.alpha_composite(shd.filter(ImageFilter.GaussianBlur(6)))
    lit_bar(cd,bx0,40+size*0.02,bx1,40+size*0.98,RED)
    for k,(w_,x_) in enumerate(zip(ws,xs)): cd.text((x_,40),w_,font=fn,fill=CREAM,stroke_width=0 if k==act else 3,stroke_fill=(0,0,0))
    if abs(s-1)>0.002:
        cap=cap.resize((int(W*s),int(280*s)),Image.BICUBIC); ox=int((W-cap.width)/2); oy=int(CAP_Y-40-(cap.height-280)/2)
    else: ox,oy=0,CAP_Y-40
    comp(im,cap,(ox,oy))
# ---------------- camera ----------------
def piece_of(t):
    k=0
    for c in CUTS:
        if t>=c-1e-6: k+=1
    return k
def zoom_at(t):
    if t<CUTS[0]:   # visual hook: punch to 110% on "Anavar", release on "six"
        if t<1.48: return 1.0
        if t<3.44: return lerp(1.0,1.10,expo((t-1.48)/0.12))
        return lerp(1.10,1.0,expo((t-3.44)/0.12))
    return 1.0 if piece_of(t)%2==0 else 1.08
# ---------------- frame ----------------
def frame(src,t):
    global GL
    z=zoom_at(t)
    if z!=1.0:
        big=src.resize((int(W*z),int(H*z)),Image.BICUBIC); ox=(big.width-W)//2; oy=int((big.height-H)*0.4); src=big.crop((ox,oy,ox+W,oy+H))
    glow=Image.new('RGBA',(W,H),(0,0,0,0)); GL=ImageDraw.Draw(glow,'RGBA')
    pipim=pip_scene(src,t)
    im=pipim if pipim is not None else src.convert('RGB')
    # caption legibility gradient (bottom) — footage itself untouched elsewhere
    yy=np.arange(H); al=np.where(yy>1300,np.clip((yy-1300)/200,0,1)*90,0).astype(np.uint8)
    comp(im,Image.merge('RGBA',[Image.new('L',(W,H),c) for c in (4,6,12)]+[Image.fromarray(np.repeat(al[:,None],W,1))]))
    if pipim is None:
        hook_cards(im,t); agenda(im,t); triad(im,t); lipid_card(im,t); monitor_tiles(im,t); sixpack(im,t)
        fatty_liver(im,t); hazard(im,t); radar(im,t); receipts(im,t); body_tile(im,t); roadmap(im,t); cta(im,t)
    text_hook(im,t)
    GL_=GL; GL=None
    if glow.getbbox():
        sm=glow.resize((W//4,H//4),Image.BILINEAR)
        g1=np.asarray(sm.filter(ImageFilter.GaussianBlur(3.5))).astype(np.float32)/255; g2=np.asarray(sm.filter(ImageFilter.GaussianBlur(10))).astype(np.float32)/255
        prem=np.clip(g1[...,:3]*g1[...,3:]*2.3+g2[...,:3]*g2[...,3:]*1.8,0,1)
        prem=np.asarray(Image.fromarray((prem*255).astype(np.uint8)).resize((W,H),Image.BILINEAR)).astype(np.float32)/255
        b=np.asarray(im.convert('RGB')).astype(np.float32)/255
        im=Image.fromarray(((1-(1-b)*(1-prem))*255).astype(np.uint8))
    topic_band(im,t)
    d=ImageDraw.Draw(im,'RGBA'); d.rectangle([0,0,7,H],fill=GOLD)
    # static disclaimer along the gold rule
    if DISC is not None: comp(im,DISC,(12,1560-DISC.height))
    captions(im,t)
    return im.convert('RGB')
def make_disc():
    s='FOR RESEARCH & EDUCATIONAL PURPOSES ONLY'; fn=f(MONO,17)
    tmp=Image.new('RGBA',(int(ImageDraw.Draw(Image.new('L',(1,1))).textlength(s,font=fn))+8,26),(0,0,0,0)); ImageDraw.Draw(tmp).text((4,3),s,font=fn,fill=(200,200,206,150))
    return tmp.rotate(90,expand=True)
DISC=make_disc()
if __name__=='__main__':
    mode=sys.argv[3]
    if mode=='stills':
        import os; os.makedirs(B+'qc',exist_ok=True)
        for tt in [float(x) for x in sys.argv[4:]]:
            subprocess.run(['ffmpeg','-v','error','-y','-ss',f'{tt:.3f}','-i',B+'assembled.mov','-frames:v','1',B+'qc/_src.png'])
            frame(Image.open(B+'qc/_src.png').convert('RGB'),tt).resize((540,960),Image.LANCZOS).save(B+f'qc/st_{tt:07.2f}.jpg',quality=85)
        sys.exit()
    n0,n1=int(sys.argv[4]),int(sys.argv[5]); out=sys.argv[6]
    dec=subprocess.Popen(['ffmpeg','-v','error','-ss',f'{n0/FPS:.4f}','-i',B+'assembled.mov','-frames:v',str(n1-n0),'-f','rawvideo','-pix_fmt','rgb24','-'],stdout=subprocess.PIPE)
    enc=subprocess.Popen(['ffmpeg','-v','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-','-c:v','libx264','-crf','14','-preset','medium','-pix_fmt','yuv420p',out],stdin=subprocess.PIPE)
    for n in range(n0,n1):
        buf=dec.stdout.read(W*H*3)
        if len(buf)<W*H*3: print('short',n); break
        enc.stdin.write(frame(Image.frombuffer('RGB',(W,H),buf),n/FPS).tobytes())
    enc.stdin.close(); enc.wait(); dec.kill(); print('done',n0,n1)
