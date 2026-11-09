# Reel 03 — "3 compounds for E2" (Primo · Masteron · EQ). 1080x1920, 30 fps.
# Usage: python3 render.py <scratch> stills t1 t2 ...   |   python3 render.py <scratch> <n0> <n1> <out.mp4>
# All graphics are authored on the RAW take timeline; output frames are mapped through trim.json.
import json, subprocess, sys, math, os
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
HERE=os.path.dirname(os.path.abspath(__file__)); S=sys.argv[1]; F=S+'/fonts/'; WK=S+'/work/'
W,H,FPS=1080,1920,30
WORDS=json.load(open(HERE+'/words_raw.json')); TR=json.load(open(HERE+'/trim.json')); KEEP=TR['keep']
CUTS=[a for a,b in TR['remove']]
GOLD=(201,169,110); CREAM=(244,241,234); NAVY=(14,17,23); MUTED=(184,184,188); LBL=(124,124,130)
RED=(255,34,28); VGOLD=(255,194,26); CYAN=(0,229,255); GREEN=(30,255,110); DEEP=(2,3,8); INK=(6,8,14); WHITE=(255,255,255)
CRIM=(200,16,46); CRIM2=(224,36,63); CHIP=(40,12,18); BLUE=(79,163,224); SGREEN=(60,203,106); AMBER=(240,160,48)
MONO='JBMono-500.ttf'; MONOB='JBMono-700.ttf'; BEB='BebasNeue.ttf'; DMB='DMSans-700.ttf'; DMR='DMSans-400.ttf'; BAR='Barlow-800.ttf'; BAR6='Barlow-600.ttf'
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
def appear(t,t0,dur=0.16): return expo((t-t0)/dur)
def norm(w): return w.lower().strip('.,?!"\'')
def T(key,near):
    """start time of the spoken word matching key nearest to `near` (raw timeline)"""
    c=[w for w in WORDS if norm(w['w']).startswith(key)]
    if not c: raise KeyError(key)
    w=min(c,key=lambda w:abs(w['s']-near))
    if abs(w['s']-near)>2.5: print('WARN T',key,near,w['s'],file=sys.stderr)
    return w['s']
def TE(key,near):
    c=[w for w in WORDS if norm(w['w']).startswith(key)]; return min(c,key=lambda w:abs(w['s']-near))['e']
GL=None
# ---------------- primitives ----------------
def txt(d,x,y,s,font,col,a=1.0,anchor=None): d.text((x,y),s,font=font,fill=A(col,a),anchor=anchor)
def brackets(d,x0,y0,x1,y1,col,L=34,w=4):
    for (cx,cy,sx,sy) in [(x0,y0,1,1),(x1,y0,-1,1),(x0,y1,1,-1),(x1,y1,-1,-1)]:
        d.line([(cx,cy),(cx+sx*L,cy)],fill=col,width=w); d.line([(cx,cy),(cx,cy+sy*L)],fill=col,width=w)
def lit_bar(d,x0,y0,x1,y1,col,a=1.0):
    h=max(1,int(y1-y0))
    if x1<=x0: return
    for i in range(h):
        k=i/h; c=tuple(int(min(255,v*(1.18-0.36*k)+(40 if k<0.12 else 0))) for v in col)
        d.line([(x0,y0+i),(x1,y0+i)],fill=c+(int(255*clamp(a)),))
def tag(d,x,y,label,col=RED,size=30,a=1.0,glow=True,fg=None):
    fn=f(MONOB,size); tw=d.textlength(label,font=fn); h=size+16
    lit_bar(d,x,y,x+tw+24,y+h,col,a); d.text((x+12,y+6),label,font=fn,fill=A(fg or (INK if col in (VGOLD,GREEN,CYAN) else WHITE),a))
    if GL and glow: GL.rectangle([x-4,y-4,x+tw+28,y+h+4],outline=A(col,a),width=8)
    return x+tw+24
def tagw(d,label,size=30): return d.textlength(label,font=f(MONOB,size))+24
def chip(d,x,y,label,a=1.0,size=40,strike=0.0):
    fn=f(BAR,size); tw=d.textlength(label,font=fn)
    d.rounded_rectangle([x,y,x+tw+36,y+size+22],radius=8,fill=A(CHIP,0.95*a),outline=A(RED,a),width=3)
    d.text((x+18,y+6),label,font=fn,fill=A((255,150,150),a))
    if strike>0:
        d.line([(x+10,y+(size+22)/2),(x+10+lerp(0,tw+16,strike),y+(size+22)/2)],fill=A(RED,a),width=6)
        if GL: GL.line([(x+10,y+(size+22)/2),(x+10+lerp(0,tw+16,strike),y+(size+22)/2)],fill=A(RED,a),width=12)
    return x+tw+36
def flag(d,box,label,t0,t,side='right',size=28):
    p=expo((t-t0)/0.14)
    if p<=0: return
    x0,y0,x1,y1=box; brackets(d,x0,y0,x1,y1,A(RED,1),30,7)
    if GL: brackets(GL,x0,y0,x1,y1,A(RED,1),30,12)
    q=clamp((p-0.3)/0.7)
    if q>0:
        for seg in [((x0,y0),(lerp(x0,x1,q),y0)),((x1,y1),(lerp(x1,x0,q),y1)),((x0,y1),(x0,lerp(y1,y0,q))),((x1,y0),(x1,lerp(y0,y1,q)))]:
            d.line(seg,fill=A(RED,1),width=3)
    if p>0.5 and label:
        if side=='right': tag(d,x1+12,(y0+y1)/2-23,label,size=size)
        elif side=='above': tag(d,x0,y0-size-28,label,size=size)
        elif side=='aboveR': tag(d,x1-tagw(d,label,size),y0-size-28,label,size=size)
        else: tag(d,x0,y1+10,label,size=size)
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
def dashed(d,p0,p1,col,w=3,dash=14,gap=10,a=1.0):
    L=math.dist(p0,p1); n=int(L/(dash+gap))+1
    for i in range(n):
        s=i*(dash+gap)/L; e=min(1,(i*(dash+gap)+dash)/L)
        if s>=1: break
        d.line([(lerp(p0[0],p1[0],s),lerp(p0[1],p1[1],s)),(lerp(p0[0],p1[0],e),lerp(p0[1],p1[1],e))],fill=A(col,a),width=w)
def polyline_progress(d,pts,p,col,w=6,glow=True,a=1.0):
    """draw polyline up to fraction p of its length; return head point"""
    seg=[math.dist(pts[i],pts[i+1]) for i in range(len(pts)-1)]; tot=sum(seg); goal=tot*clamp(p); acc=0; head=pts[0]
    for i,L in enumerate(seg):
        if acc>=goal: break
        q=min(1,(goal-acc)/L) if L>0 else 1
        e=(lerp(pts[i][0],pts[i+1][0],q),lerp(pts[i][1],pts[i+1][1],q))
        d.line([pts[i],e],fill=A(col,a),width=w)
        if GL and glow: GL.line([pts[i],e],fill=A(col,a),width=w*2)
        head=e; acc+=L
    return head
def frosted(im,box,dark=0.86,blur=10,radius=0):
    x0,y0,x1,y1=[int(v) for v in box]
    x0=max(0,x0); y0=max(0,y0); x1=min(W,x1); y1=min(H,y1)
    if x1<=x0 or y1<=y0: return
    reg=im.crop((x0,y0,x1,y1)).convert('RGB').filter(ImageFilter.GaussianBlur(blur))
    reg=Image.blend(reg,Image.new('RGB',reg.size,DEEP),dark).convert('RGBA')
    if radius:
        m=Image.new('L',reg.size,0); ImageDraw.Draw(m).rounded_rectangle([0,0,reg.width-1,reg.height-1],radius=radius,fill=255)
        im.paste(reg,(x0,y0),m)
    else: im.paste(reg,(x0,y0))
_logo=None
def logo(size):
    global _logo
    if _logo is None:
        lg=Image.open(HERE+'/../../brand/logo/coach-agz-logo-round.jpg').convert('RGB'); s=min(lg.size)
        _logo=lg.crop(((lg.width-s)//2,(lg.height-s)//2,(lg.width+s)//2,(lg.height+s)//2))
    lg=_logo.resize((size,size),Image.LANCZOS).convert('RGBA'); m=Image.new('L',(size,size),0); ImageDraw.Draw(m).ellipse([0,0,size-1,size-1],fill=255); lg.putalpha(m); return lg
_bg=None
def carousel_bg():
    global _bg
    if _bg is None:
        yy,xx=np.mgrid[0:H,0:W]; r=np.sqrt((xx-W*0.95)**2+(yy-H*0.05)**2)/(H*0.7); g=np.clip(1-r,0,1)**2
        base=np.array(NAVY,np.float32)[None,None,:]*np.ones((H,W,1),np.float32); glow=np.array((52,44,34),np.float32)[None,None,:]
        arr=base+(glow-base*0.5)*g[...,None]*0.55
        noise=np.random.default_rng(3).normal(0,2.2,(H,W,1)); _bg=Image.fromarray(np.clip(arr+noise,0,255).astype(np.uint8)).convert('RGBA')
    return _bg.copy()
def carousel_header(d,a=1.0,page='03 / 03',im=None):
    if im is not None:
        lg=logo(64); lg.putalpha(lg.split()[3].point(lambda v:int(v*a))); im.alpha_composite(lg,(64,262))
    txt(d,142,262,'COACH AGZ',f(BEB,40),GOLD,a); txt(d,142,302,'@coach.agz',f(MONO,22),LBL,a)
    fn=f(MONO,26); tw=d.textlength(page,font=fn); txt(d,940-tw,272,page,fn,GOLD,a)
def kicker(d,x,y,label,t,t0,col=GOLD,size=30):
    p=expo((t-t0)/0.25)
    if p<=0: return
    d.line([(x,y+size*0.6),(x+lerp(0,56,p),y+size*0.6)],fill=A(col,1),width=4)
    q=clamp((t-t0-0.12)/0.3); n=int(len(label)*q)
    fn=f(BAR6,size); xx=x+74
    for ch in label[:n]:
        d.text((xx,y),ch,font=fn,fill=A(col,1)); xx+=d.textlength(ch,font=fn)+size*0.22
# ---------------- text hook (TEXT_HOOK_ENGINE) ----------------
HOOK=json.load(open(HERE+'/edit_log.json'))['text_hook']
HOOK_END=HOOK['end']
def text_hook(im,t):
    if t>=HOOK_END+0.15: return
    a=1-clamp((t-HOOK_END)/0.15)
    d=ImageDraw.Draw(im,'RGBA'); size=88; fn=f(BAR,size)
    l1,l2=HOOK['lines']; em=HOOK['emphasis']
    s=lerp(1.0,1.04,clamp(t/HOOK_END))   # slow 100->104% push over its hold
    lay=Image.new('RGBA',(W,330),(0,0,0,0)); ld=ImageDraw.Draw(lay)
    widths=[ld.textlength(l,font=fn) for l in (l1,l2)]; bw=max(widths)+70
    ld.rounded_rectangle([(W-bw)/2,10,(W+bw)/2,250],radius=22,fill=(6,8,14,225))
    for i,line in enumerate((l1,l2)):
        x=(W-widths[i])/2; y=24+i*112
        for k,word in enumerate(line.split(' ')):
            col=VGOLD if word in em else WHITE
            ld.text((x,y),word,font=fn,fill=col+(255,)); x+=ld.textlength(word+' ',font=fn)
    if s!=1: lay=lay.resize((int(W*s),int(330*s)),Image.BICUBIC)
    lay.putalpha(lay.split()[3].point(lambda v:int(v*a)))
    im.alpha_composite(lay,(int((W-lay.width)/2),int(HOOK['position']['y_px']-10-(lay.height-330)/2)))
def lineup(d,t):   # 3 numbered slots under the hook; #3 flags on "last one"
    if t>=HOOK_END+0.15: return
    a0=1-clamp((t-HOOK_END)/0.15); t3=T('three',0.6); tl=T('last',5.8)
    for i in range(3):
        a=appear(t,t3+0.08*i,0.14)*a0
        if a<=0: continue
        x0=246+i*204; y0=600; x1=x0+180; y1=y0+84
        bad=(i==2 and t>=tl)
        col=RED if bad else VGOLD
        d.rounded_rectangle([x0,y0,x1,y1],radius=10,fill=A((8,10,18),0.9*a),outline=A(col,a),width=3)
        if GL: GL.rounded_rectangle([x0,y0,x1,y1],radius=10,outline=A(col,a*0.7),width=6)
        txt(d,x0+16,y0+14,f'0{i+1}',f(BEB,58),col,a)
        d.rectangle([x0+82,y0+30,x1-18,y0+54],fill=A((70,74,90),a))
        if bad:
            b=appear(t,tl,0.1)*a0; cross(d,x1-50,y0+28,RED,0.9,b)
            tag(d,x0-6,y1+12,'NEW USERS',RED,24,b)
# ---------------- topic band (hook exit -> midpoint) ----------------
MID_RAW=None
def band(im,t,hide):
    """Locked lineup: names stay redacted until spoken, so the band never gives away the payoff."""
    if t<HOOK_END+0.15 or t>=MID_RAW+0.15: return
    a=min(appear(t,HOOK_END+0.15,0.15),1-clamp((t-MID_RAW)/0.15))*(1-hide)
    if a<=0: return
    d=ImageDraw.Draw(im,'RGBA')
    d.rectangle([8,212,W,392],fill=NAVY+(int(232*a),))
    fn=f(BAR,54); p1='3 compounds for '; txt(d,64,222,p1,fn,CREAM,a); txt(d,64+d.textlength(p1,font=fn),222,'E2',fn,VGOLD,a)
    hf=f(MONO,24); tw=d.textlength('@coach.agz',font=hf); txt(d,940-tw,240,'@coach.agz',hf,GOLD,a)
    slots=[('01','PRIMO',T('primobolan',12.0),VGOLD),('02','MASTERON',T('masteron',32.4),VGOLD),('03','EQUIPOISE',T('equipoise',56.8),RED)]
    for i,(n,name,tr,col) in enumerate(slots):
        x0=64+i*296; x1=x0+280; y0=302; y1=372; r=expo((t-tr)/0.22) if t>=tr else 0
        bad=(i==2)
        edge=col if (r>0 or bad) else (90,94,110)
        d.rectangle([x0,y0,x1,y1],fill=A((10,12,20),0.95*a),outline=A(edge,a),width=3)
        if GL and (r>0 or bad): GL.rectangle([x0,y0,x1,y1],outline=A(edge,a*(0.5+0.5*r)),width=6)
        txt(d,x0+12,y0+18,n,f(MONOB,26),col if (r>0 or bad) else LBL,a)
        if r<1:   # redaction bar wipes away on reveal
            rx0=x0+60+lerp(0,x1-x0-74,r); d.rectangle([rx0,y0+22,x1-14,y1-22],fill=A((60,64,80) if not bad else (110,20,24),a))
            if bad and r==0: cross(d,x1-46,y0+21,RED,0.9,a)
        if r>0:
            ff=f(BAR,46 if len(name)<9 else 42); txt(d,x0+60,y0+8,name,ff,CREAM if not bad else (255,120,110),a*r)
# ---------------- scenes ----------------
def sc_primo(im,d,t):     # SPEC CARD with aromatizer spectrum (top zone, crimson-bar glass card)
    x0,y0,x1,y1=60,400,940,868
    txt(d,96,420,'01',f(BEB,130),VGOLD); txt(d,226,430,'PRIMOBOLAN',f(BEB,104),CREAM)
    txt(d,230,532,'COMPOUND FILE · E2 PROFILE',f(MONO,24),LBL)
    # spectrum
    tl=T('low',12.9); ta=T('aromatizer',13.4)
    a=appear(t,tl-0.25,0.2); sx0,sx1,sy=100,900,640
    txt(d,sx0,sy-50,'YOUR AROMATIZATION',f(MONO,24),CREAM,a)
    if a>0:
        for i in range(sx1-sx0):
            k=i/(sx1-sx0); c=(tuple(int(lerp(BLUE[j],SGREEN[j],k*2)) for j in range(3)) if k<0.5 else tuple(int(lerp(SGREEN[j],AMBER[j],(k-0.5)*2)) for j in range(3)))
            d.line([(sx0+i,sy),(sx0+i,sy+26)],fill=A(c,a))
        for lbl,k in [('LOW',0.0),('MODERATE',0.5),('HIGH',1.0)]:
            fn=f(MONO,24); tw=d.textlength(lbl,font=fn); txt(d,lerp(sx0,sx1,k)-tw*k,sy+36,lbl,fn,LBL,a)
        mk=lerp(0.92,0.3,expo((t-tl)/0.45)); mx=lerp(sx0,sx1,mk)
        d.polygon([(mx-16,sy-30),(mx+16,sy-30),(mx,sy-4)],fill=A(WHITE,a))
        if t>=ta:
            b=appear(t,ta,0.14); bx0,bx1=sx0-6,lerp(sx0,sx1,0.55)
            d.rectangle([bx0,sy-8,bx1,sy+34],outline=A(GREEN,b),width=4)
            if GL: GL.rectangle([bx0,sy-8,bx1,sy+34],outline=A(GREEN,b),width=10)
            tag(d,bx1+14,sy-10,'BEST FIT',GREEN,26,b)
    # stat cells
    cells=[('CLASS','DHT-DERIVED',T('dht',17.3),VGOLD),('AROMATIZES','NO',T("doesn't",17.9),RED),('E2 EFFECT','LOWERS',T('lower',19.3),CYAN)]
    for i,(k,v,tt,col) in enumerate(cells):
        cx0=100+i*280; cy0=730; a=appear(t,tt-0.05,0.14)
        d.rounded_rectangle([cx0,cy0,cx0+262,cy0+112],radius=12,fill=A((24,26,34),0.9),outline=A((70,74,90) if a<=0 else col,max(0.4,a)),width=3)
        txt(d,cx0+16,cy0+12,k,f(MONO,22),LBL)
        if a>0:
            fn=f(BEB,56); txt(d,cx0+16,cy0+44,v,fn,col,a)
            if v=='NO': cross(d,cx0+212,cy0+58,RED,0.9,a)
            if v=='LOWERS':
                yy=cy0+44+lerp(0,26,expo((t-tt-0.1)/0.5)); arrow(d,cx0+226,cy0+40,cx0+226,yy+30,CYAN,6,a)
        if GL and a>0: GL.rounded_rectangle([cx0,cy0,cx0+262,cy0+112],radius=12,outline=A(col,a*0.7),width=6)
def sc_crash(im,d,t):     # LINE GRAPH: E2 crashes after a blind AI (frosted takeover panel)
    gx0,gx1,gy0,gy1=150,960,620,1010
    txt(d,96,560,'E2',f(BEB,48),CREAM)
    d.line([(gx0,gy1),(gx1,gy1)],fill=A((90,94,110),1),width=2); d.line([(gx0,gy0),(gx0,gy1)],fill=A((90,94,110),1),width=2)
    txt(d,gx1-260,gy1+14,'WEEKS ON CYCLE →',f(MONO,24),LBL)
    # dialed-in band
    d.rectangle([gx0+2,740,gx1,830],fill=A(SGREEN,0.13)); dashed(d,(gx0,740),(gx1,740),SGREEN,2); dashed(d,(gx0,830),(gx1,830),SGREEN,2)
    txt(d,gx1-200,748,'DIALED IN',f(MONO,22),SGREEN)
    xs=[lerp(gx0+10,gx1-10,i/10) for i in range(11)]
    pre=[(xs[0],800),(xs[1],780),(xs[2],760),(xs[3],720),(xs[4],700)]
    tai=T('ais',23.6); xa=lerp(xs[4],xs[5],0.5)
    post=[pre[-1],(xa,694),(xs[5],760),(xs[6],930),(xs[7],968),(xs[8],960),(xs[9],972),(xs[10],966)]
    t0=T('generally',21.0)
    polyline_progress(d,pre,(t-t0-0.2)/2.2,CYAN,6)
    for p in pre:
        if (t-t0-0.2)/2.2*4>=pre.index(p)-0.01: d.ellipse([p[0]-8,p[1]-8,p[0]+8,p[1]+8],fill=A(WHITE,1))
    if t>=tai:
        yy=lerp(470,640,expo((t-tai)/0.14)); a=appear(t,tai,0.1)
        d.rounded_rectangle([xa-46,yy,xa+46,yy+60],radius=10,fill=A(RED,a)); txt(d,xa-24,yy+4,'AI',f(BEB,58),WHITE,a)
        if GL: GL.rounded_rectangle([xa-50,yy-4,xa+50,yy+64],radius=12,outline=A(RED,a),width=10)
        dashed(d,(xa,yy+64),(xa,gy1),RED,3,a=a)
        h=polyline_progress(d,post,(t-tai-0.35)/1.3,RED,7)
        if t>tai+0.35: d.ellipse([h[0]-10,h[1]-10,h[0]+10,h[1]+10],fill=A(WHITE,1))
    tw_=T('without',23.9)
    if t>=tw_:
        a=appear(t,tw_,0.12); x=xa+60; cross(d,x,628,RED,0.8,a); txt(d,x+34,622,'NO BLOODWORK',f(MONOB,26),RED,a)
    # symptom chips
    x=110
    for k,(lbl,near) in enumerate([('JOINTS',25.9),('LIBIDO',26.5),('MOOD',27.2)]):
        tt=T(lbl.lower(),near)
        if t>=tt:
            a=appear(t,tt,0.12); y=lerp(1100,1080,a); x=chip(d,x,y,lbl,a,44,strike=0)+20
    tg=T('garbage',28.4)
    if t>=tg: flag(d,(xs[6]-26,900,gx1+12,1000),'E2 CRASHED',tg,t,'aboveR',26)
def sc_mast(im,d,t):      # KINETIC TITLE: rank + name slam (top zone, no panel)
    ts=T('secondarily',29.4); tf=T('favorite',30.3); tm=T('masteron',32.0); tma=T('mass',33.5); tb=T('builder',33.8)
    a=appear(t,ts,0.12)
    # scrim for legibility over the roof
    sc=Image.new('RGBA',(W,560),(0,0,0,0)); sd=ImageDraw.Draw(sc)
    for y in range(560): sd.line([(0,y),(W,y)],fill=(4,6,12,int(170*a*(1-(y/560)**1.6))))
    im.alpha_composite(sc,(0,380))
    n='02'; fn=f(BEB,220); y=lerp(360,400,expo((t-ts)/0.25))
    txt(d,64,y,n,fn,VGOLD,a)
    if GL: GL.text((64,y),n,font=fn,fill=A(VGOLD,a*0.6))
    kicker(d,262,430,'ALL-TIME FAVOURITE',t,tf,GOLD,30)
    if t>=tm:
        p=expo((t-tm)/0.16); sp=lerp(26,4,p); fn=f(BEB,170); x=262
        for ch in 'MASTERON':
            d.text((x,lerp(520,486,p)),ch,font=fn,fill=A(CREAM,p)); x+=d.textlength(ch,font=fn)+sp
        q=expo((t-tm-0.12)/0.3); d.rectangle([262,664,262+lerp(0,x-262,q),670],fill=A(VGOLD,1))
        if GL: GL.rectangle([262,664,262+lerp(0,x-262,q),670],fill=A(VGOLD,1))
    if t>=tma:
        b=appear(t,tma,0.12); chip(d,262,700,'MASS BUILDER',b,40,strike=expo((t-tb)/0.2) if t>=tb else 0)
# PIP scene (mechanism -> bar chart). footage lives in a window top-right.
PIPWIN=(600,330,940,800)
def sc_mech(im,d,t):
    t0=T('anyways',35.0); kicker(d,80,370,'MASTERON · MECHANISM',t,t0+0.15,GOLD,28)
    ta=T('anti-estrogenic',38.7)
    if t>=ta:
        p=expo((t-ta)/0.18)
        txt(d,80,lerp(470,430,p),'ANTI-',f(BEB,118),CREAM,p); txt(d,80,lerp(580,540,p),'ESTROGENIC',f(BEB,118),VGOLD,p)
        if GL: GL.text((80,lerp(580,540,p)),'ESTROGENIC',font=f(BEB,118),fill=A(VGOLD,p*0.5))
    tr=T('androgen',40.6)
    if t>=tr:
        a=appear(t,tr,0.2); txt(d,82,676,'via androgen receptor',f(DMR,34),MUTED,a); txt(d,82,720,'signalling',f(DMB,34),CREAM,a)
    tb=T('blocking',48.9)
    sw=clamp((t-tb+0.1)/0.3)     # 0 = receptor diagram, 1 = bar chart
    if sw<1: receptor_diagram(d,t,1-sw)
    if sw>0: bar_chart(d,t,sw)
def receptor_diagram(d,t,a):
    y=1090; d.line([(80,y),(1000,y)],fill=A((120,124,140),a),width=3); d.line([(80,y+14),(1000,y+14)],fill=A((120,124,140),a),width=3)
    txt(d,400,y+28,'CELL MEMBRANE',f(MONO,24),LBL,a)
    def dock(cx,col,lit):
        d.arc([cx-46,y-60,cx+46,y+24],180,360,fill=A(col,a),width=7) if False else None
        d.line([(cx-60,y),(cx-60,y-80)],fill=A(col,a),width=9); d.line([(cx+60,y),(cx+60,y-80)],fill=A(col,a),width=9)
        d.arc([cx-60,y-40,cx+60,y+40],0,180,fill=A(col,a),width=9)
        if lit and GL: GL.line([(cx-44,y),(cx-44,y-56)],fill=A(col,a),width=14); GL.line([(cx+44,y),(cx+44,y-56)],fill=A(col,a),width=14)
    tr=T('androgen',40.6); tsg=T('signaling',41.3); top=T('oppose',42.1); tti=T('tissue',44.5); tse=T('serm',45.8)
    dock(290,VGOLD,t>=tr+0.4); txt(d,236,y+50,'AR',f(BEB,60),VGOLD,a)
    dock(760,CYAN,False); txt(d,706,y+50,'ER',f(BEB,60),CYAN,a)
    # masteron molecule docks into AR
    if t>=tr-0.3:
        p=expo((t-tr+0.3)/0.7); mx=lerp(120,290,p); my=lerp(840,y-48,p)
        pts=[(mx+42*math.cos(math.pi/3*i+math.pi/6),my+42*math.sin(math.pi/3*i+math.pi/6)) for i in range(6)]
        d.polygon(pts,fill=A(VGOLD,a)); txt(d,mx-16,my-22,'M',f(BEB,44),INK,a)
        if GL: GL.polygon(pts,fill=A(VGOLD,a*0.8))
        if p<0.98: txt(d,mx+40,my-50,'MASTERON',f(MONOB,22),VGOLD,a)
    # E2 molecule heading for ER
    ep=0.5+0.5*math.sin(t*3)
    ex,ey=760,870+10*ep
    d.ellipse([ex-38,ey-38,ex+38,ey+38],fill=A(CYAN,a)); txt(d,ex-24,ey-24,'E2',f(BEB,46),INK,a)
    if t>=tsg:   # signal pulses AR -> ER along membrane
        for k in range(4):
            q=((t-tsg)*0.9+k/4)%1; x=lerp(360,690,q)
            d.ellipse([x-7,y-14,x+7,y],fill=A(VGOLD,a*min(1,q*5,(1-q)*5)))
            if GL: GL.ellipse([x-12,y-19,x+12,y+5],fill=A(VGOLD,a))
    if t>=top:
        b=appear(t,top,0.12)*a; d.line([(690,950),(830,950)],fill=A(RED,b),width=8)
        if GL: GL.line([(690,950),(830,950)],fill=A(RED,b),width=16)
        tag(d,840,926,'OPPOSED',RED,28,b)
        txt(d,600,1222,'E2-DRIVEN EFFECTS',f(MONOB,28),(255,150,150),b); cross(d,930,1222,RED,0.9,b)
    if t>=tti: tag(d,80,1214,'TISSUE LEVEL',GREEN,28,appear(t,tti)*a)
    if t>=tse:
        b=appear(t,tse,0.14)*a; tag(d,380,930,'SERM-LIKE',VGOLD,34,b)
def bar_chart(d,t,a):
    tb=T('blocking',48.9); tsd=T('side',51.7); tn=T('not',53.8); te=T('e2',55.4)
    txt(d,80,880,'MASTERON · WHAT CHANGES',f(MONO,24),GOLD,a)
    # bar 1: estrogenic side effects at the receptor
    txt(d,80,936,'E2 SIDE EFFECTS · AT RECEPTOR',f(MONOB,26),CREAM,a)
    fr=lerp(0.95,0.28,expo((t-tsd)/0.8)) if t>=tsd else 0.95
    d.rectangle([80,980,1000,1036],outline=A((70,74,90),a),width=2); lit_bar(d,84,984,lerp(84,996,fr),1032,RED if fr>0.5 else SGREEN,a)
    if GL: GL.rectangle([84,984,lerp(84,996,fr),1032],fill=A(RED if fr>0.5 else SGREEN,a*0.5))
    if t>=tsd+0.5: tag(d,lerp(84,996,fr)+16,986,'BLOCKED',GREEN,24,appear(t,tsd+0.5)*a)
    # bar 2: systemic E2 on bloodwork
    txt(d,80,1068,'SYSTEMIC E2 · BLOODWORK',f(MONOB,26),CREAM,a)
    pulse=0.25*math.sin((t-te)*14)*math.exp(-(t-te)*3) if t>=te else 0
    d.rectangle([80,1112,1000,1168],outline=A((70,74,90),a),width=2); lit_bar(d,84,1116,lerp(84,996,0.82),1164,tuple(int(min(255,c*(1+pulse))) for c in CYAN),a)
    if GL: GL.rectangle([84,1116,lerp(84,996,0.82),1164],fill=A(CYAN,a*0.4))
    if t>=tn: tag(d,780,1180,'= UNCHANGED',VGOLD,26,appear(t,tn)*a)
def sc_eqbar(im,d,t):     # VERDICT BAR slams across the cap
    te=T('equipoise',56.7); tj=T("don't",58.0); tb=T('beginners',59.4)
    p=expo((t-te)/0.18); y=560; x1=lerp(8,1000,p)
    if GL: GL.rectangle([8,y-6,x1+4,y+112],outline=A(RED,1),width=10)
    lit_bar(d,8,y,x1,y+106,RED); d.rectangle([8,y+102,x1,y+106],fill=A((140,0,0),1))
    if p>0.6: txt(d,40,y+8,'03 · EQUIPOISE',f(BEB,96),WHITE,clamp((p-0.6)/0.4))
    if t>=tj: txt(d,40,y-46,'COACH VERDICT',f(MONOB,28),WHITE,appear(t,tj))
    if t>=tb:
        b=expo((t-tb)/0.12); s=lerp(1.15,1,b); fn=f(MONOB,int(34*s)); lab='BEGINNERS'; tw=d.textlength(lab,font=fn)
        bx=980-tw-70; d.rectangle([bx,y+24,980,y+84],fill=A(WHITE,b)); txt(d,bx+14,y+30,lab,fn,RED,b); cross(d,980-46,y+38,RED,0.9,b)
def sc_scatter(im,d,t):   # CAROUSEL CUTAWAY: scatter plot, no footage
    carousel_header(d,1.0,'03 / 03',im)
    t0=SC_SCATTER[0]; kicker(d,64,370,'EQUIPOISE AS AN E2 CONTROL',t,t0+0.05,GOLD,28)
    th=T('ability',64.4)
    if t>=th:
        p=expo((t-th)/0.2); txt(d,64,lerp(450,420,p),'SAME COMPOUND.',f(BEB,96),CREAM,p); txt(d,64,lerp(546,516,p),'DIFFERENT E2.',f(BEB,96),RED,p)
    gx0,gx1,gy0,gy1=130,960,660,1230; zy=(gy0+gy1)/2
    d.line([(gx0,gy0),(gx0,gy1)],fill=A((90,94,110),1),width=2); dashed(d,(gx0,zy),(gx1,zy),(110,114,130),2)
    txt(d,gx1-200,gy1+8,'EQ DOSE →',f(MONO,24),LBL); txt(d,gx0+12,gy0,'E2 ↑',f(MONO,24),LBL); txt(d,gx0+12,gy1-34,'E2 ↓',f(MONO,24),LBL)
    tex=T('estrogen',62.7)
    if t>=tex:
        p=clamp((t-tex)/0.8); a=1.0 if t<T('place',69.0) else lerp(1,0.35,clamp((t-T('place',69.0))/0.4))
        dashed(d,(gx0+20,zy-40),(lerp(gx0+20,gx1-20,p),lerp(zy-40,gy1-60,p)),VGOLD,4,a=a)
        if p>0.9: txt(d,gx1-210,gy1-110,'EXPECTED',f(MONOB,24),VGOLD,a)
    rng=np.random.default_rng(11); N=36; ts=T('ability',64.4); te=T('place',69.0)
    pts=[(lerp(gx0+40,gx1-30,rng.random()),zy+rng.normal(0,1)*150) for _ in range(N)]
    for i,(x,y) in enumerate(pts):
        y=min(gy1-14,max(gy0+14,y)); tt=lerp(ts,te-0.4,i/N)
        if t>=tt:
            a=appear(t,tt,0.1); r=lerp(16,9,a); col=RED if y>zy+60 else (AMBER if y<zy-60 else WHITE)
            d.ellipse([x-r,y-r,x+r,y+r],fill=A(col,a))
            if GL: GL.ellipse([x-r-4,y-r-4,x+r+4,y+r+4],fill=A(col,a*0.6))
    if t>=te: flag(d,(gx0+24,gy0+10,gx1-10,gy1-10),'NO RELIABLE PATTERN',te,t,'aboveR',26)
    txt(d,64,1262,'EACH DOT = ONE USER · ILLUSTRATIVE',f(MONO,20),LBL)
def sc_ester(im,d,t):     # SCAN MONITOR: undecylenate release tail after the last pin (full bleed)
    t0=SC_ESTER[0]
    for k in range(9): d.line([(64,430+k*100),(1016,430+k*100)],fill=A(CYAN,0.08),width=1)
    for k in range(10): d.line([(64+k*106,430),(64+k*106,1230)],fill=A(CYAN,0.08),width=1)
    sy=430+((t-t0)*260)%800; d.line([(64,sy),(1016,sy)],fill=A(CYAN,0.35),width=2)
    if GL: GL.line([(64,sy),(1016,sy)],fill=A(CYAN,0.6),width=6)
    tu=T('undecylenate',74.5)
    lbl='EQUIPOISE · BLOOD LEVEL' if t<tu else 'BOLDENONE UNDECYLENATE · RELEASE'
    txt(d,80,450,lbl,f(MONOB,30),CYAN); d.ellipse([960,456,980,476],fill=A(RED,1 if int(t*4)%2==0 else 0.3))
    gx0,gx1,gy0,gy1=100,980,560,1150
    d.line([(gx0,gy1),(gx1,gy1)],fill=A(CYAN,0.6),width=2)
    def xw(w): return lerp(gx0,gx1,w/20)
    curve=[]; lvl=0
    for i in range(0,201):
        w=i/10
        if w<=8:
            ph=w%1; base=0.85*(1-math.exp(-w/2.6)); lvl=base*(0.93+0.07*math.cos(2*math.pi*ph))
        else:
            lvl=curve[-1][2]*0.991 if curve else lvl
        curve.append((xw(w),gy1-lvl*480,lvl))
    pts=[(x,y) for x,y,_ in curve]
    p1=clamp((t-t0-0.3)/2.8)*0.4    # first 40% (= 8 weeks) builds
    tr=T('releasing',76.5)
    p=p1 if t<tr else 0.4+0.6*clamp((t-tr)/2.0)
    h=polyline_progress(d,pts,p,CYAN,5)
    d.ellipse([h[0]-8,h[1]-8,h[0]+8,h[1]+8],fill=A(WHITE,1))
    for k in range(9):
        if p*20>=k: d.line([(xw(k),gy1+4),(xw(k),gy1+24)],fill=A(CYAN,0.8),width=3)
    xl=xw(8); tl=T('last',79.0)
    if t>=t0+2.4:
        hot=t>=tl; a=appear(t,t0+2.4)
        dashed(d,(xl,gy0-10),(xl,gy1),RED,4 if hot else 3,a=a if hot else a*0.6)
        tag(d,xl-tagw(d,'LAST INJECTION',24)/2,gy0-62,'LAST INJECTION',RED,24,a if hot else 0.55*a,glow=hot)
    for lbl,wk,near in [('WEEKS',13,77.2),('MONTHS',19,78.1)]:
        tt=T(lbl.lower(),near)
        if t>=tt:
            a=appear(t,tt,0.12); d.line([(xl,gy1+40),(xw(wk),gy1+40)],fill=A(CYAN,a),width=4)
            arrow(d,xw(wk)-30,gy1+40,xw(wk),gy1+40,CYAN,4,a); fn=f(MONOB,26); tw=d.textlength(lbl,font=fn); txt(d,xw(wk)-tw,gy1+52,lbl,fn,CYAN,a)
    te=T('even',78.4)
    if t>=te: tag(d,xw(12),gy0+120,'STILL RELEASING',CYAN,26,appear(t,te))
def vial(d,x,y,col,a,s=1.0):
    d.rounded_rectangle([x,y+18*s,x+44*s,y+100*s],radius=8,outline=A(col,a),width=4); d.rectangle([x+8*s,y,x+36*s,y+18*s],outline=A(col,a),width=4)
    d.rectangle([x+6*s,y+56*s,x+38*s,y+94*s],fill=A(col,a*0.5))
def capsule(d,x,y,col,a):
    d.rounded_rectangle([x,y+30,x+90,y+76],radius=23,outline=A(col,a),width=4); d.rounded_rectangle([x+45,y+30,x+90,y+76],radius=23,fill=A(col,a*0.6))
def sc_fix(im,d,t):       # STACK BUILD + 12-week CALENDAR (top zone, gold-top card)
    ta=T('ancillaries',83.8); tsu=T('supplements',84.8); tc=T('compounds',86.0); tn=T('next',87.0); t8=T('8',87.3); t12=T('12',87.6); tw=T('weeks',88.0)
    txt(d,96,414,'ADDED TO FIX IT',f(MONOB,28),VGOLD)
    items=[('ANCILLARIES',ta,'vial'),('SUPPLEMENTS',tsu,'cap'),('MORE COMPOUNDS',tc,'vial2')]
    for i,(lbl,tt,kind) in enumerate(items):
        if t<tt: continue
        a=appear(t,tt,0.12); x=100+i*272; y=lerp(440,462,a)
        if kind=='vial': vial(d,x+40,y,CYAN,a,1.1)
        elif kind=='cap': capsule(d,x+30,y+10,CYAN,a)
        else: vial(d,x+20,y,AMBER,a,1.1); vial(d,x+84,y,AMBER,a,1.1)
        if GL: GL.rectangle([x+20,y+10,x+150,y+112],outline=A(CYAN if kind!='vial2' else AMBER,a*0.5),width=4)
        txt(d,x,y+124,lbl,f(BAR,38),CREAM,a)
        if i>0: txt(d,x-52,y+30,'+',f(BEB,72),VGOLD,a)
    if t>=tn-0.2:
        a=appear(t,tn-0.2,0.15); txt(d,96,646,'WEEKS SPENT CLEANING UP',f(MONOB,26),LBL,a)
        for k in range(12):
            cx=96+k*68; cy=688
            d.rectangle([cx,cy,cx+60,cy+100],outline=A((80,84,100),a),width=2); txt(d,cx+30,cy+76,f'{k+1}',f(MONOB,24),LBL,a,anchor='mm')
            tk=lerp(tn,t8,k/7) if k<8 else lerp(t8+0.05,t12+0.15,(k-8)/3)
            if t>=tk:
                b=appear(t,tk,0.08); col=RED if k<8 else AMBER
                lit_bar(d,cx+3,cy+3,cx+57,cy+56,col,b)
                if GL: GL.rectangle([cx+3,cy+3,cx+57,cy+56],fill=A(col,b*0.6))
        if t>=tw: tag(d,96+8*68-tagw(d,'8–12 WEEKS',30)/2,800,'8–12 WEEKS',RED,30,appear(t,tw))
def sc_hct(im,d,t):       # DIAL GAUGE: hematocrit needle into red (compact, top zone)
    cx,cy,R=540,800,250; tE=T('elevated',92.1); tH=T('hematocrit',92.6); tO=T('overnight',94.3)
    for i in range(180):
        ang=math.pi+math.pi*i/180; k=i/180
        col=SGREEN if k<0.55 else (AMBER if k<0.72 else RED)
        x0=cx+(R-34)*math.cos(ang); y0=cy+(R-34)*math.sin(ang); x1=cx+R*math.cos(ang); y1=cy+R*math.sin(ang)
        d.line([(x0,y0),(x1,y1)],fill=A(col,0.9),width=6)
    if GL: GL.arc([cx-R,cy-R,cx+R,cy+R],180+0.72*180,360,fill=A(RED,0.8),width=20)
    for lbl,k in [('NORMAL',0.25),('HIGH',0.85)]:
        ang=math.pi+math.pi*k; fn=f(MONO,22); tw=d.textlength(lbl,font=fn); txt(d,cx+(R+30)*math.cos(ang)-tw/2,cy+(R+30)*math.sin(ang)-14,lbl,fn,LBL)
    fn=f(BEB,60); tw=d.textlength('HEMATOCRIT',font=fn); txt(d,cx-tw/2,cy-R-96,'HEMATOCRIT',fn,CREAM)
    v=0.3 if t<tE else lerp(0.3,0.86,expo((t-tE)/0.7))
    ang=math.pi+math.pi*v; nx=cx+(R-50)*math.cos(ang); ny=cy+(R-50)*math.sin(ang)
    d.line([(cx,cy),(nx,ny)],fill=A(WHITE,1),width=8); d.ellipse([cx-18,cy-18,cx+18,cy+18],fill=A(WHITE,1))
    if GL: GL.line([(cx,cy),(nx,ny)],fill=A(RED if v>0.72 else WHITE,0.8),width=14)
    if t>=tH: tag(d,cx-tagw(d,'ELEVATED',34)/2,cy-120,'ELEVATED',RED,34,appear(t,tH))
    if t>=tO-0.6:
        a=appear(t,tO-0.6,0.2); y=cy+40; txt(d,cx-300,y,'RECOVERY',f(MONOB,24),LBL,a)
        d.rectangle([cx-140,y+4,cx+300,y+30],outline=A((80,84,100),a),width=2)
        crawl=0.04+0.06*clamp((t-tO+0.6)/3); lit_bar(d,cx-137,y+7,cx-137+crawl*434,y+27,AMBER,a)
        if t>=tO: tag(d,cx+80,y+44,'NOT OVERNIGHT',RED,24,appear(t,tO))
_doc=None
LAB=[('Testosterone, Total','1,120','ng/dL','total',97.9),('Testosterone, Free','246','pg/mL','free',98.4),('SHBG','21','nmol/L','shbg',99.1),
     ('Estradiol, Sensitive','38','pg/mL','sensitive',99.8),('Hematocrit','51.8','%','hematocrit',100.3)]
def make_doc():
    im=Image.new('RGB',(860,780),(250,250,247)); d=ImageDraw.Draw(im)
    d.rectangle([0,0,860,84],fill=(16,24,48)); d.text((28,22),'LAB REPORT · HORMONE + CBC',font=f(MONOB,32),fill=WHITE)
    d.text((28,100),'SAMPLE REPORT · VALUES FOR ILLUSTRATION',font=f(MONO,20),fill=(150,40,40))
    d.text((28,136),'TEST',font=f(MONOB,20),fill=(120,120,130)); d.text((560,136),'RESULT',font=f(MONOB,20),fill=(120,120,130))
    for i,(k,v,u,_,_) in enumerate(LAB):
        y=176+i*92
        d.text((28,y+18),k,font=f(DMR,36),fill=(50,54,66)); d.text((560,y+12),v,font=f(DMB,46),fill=INK)
        d.text((560+d.textlength(v,font=f(DMB,46))+10,y+28),u,font=f(DMR,26),fill=(100,100,110)); d.line([(20,y+86),(840,y+86)],fill=(222,222,226),width=2)
    return im
def sc_lab(im,d,t):       # PAPER DOCUMENT slides up; rows highlight as named; symptom row + cross-reference
    global _doc
    if _doc is None: _doc=make_doc()
    t0=SC_LAB[0]; p=expo((t-t0)/0.4); ang=lerp(-3,0,p)
    doc=_doc.copy(); dd=ImageDraw.Draw(doc,'RGBA')
    hl=[]
    for i,(k,v,u,key,near) in enumerate(LAB):
        tt=T(key,near)
        if t>=tt:
            q=expo((t-tt)/0.2); y=176+i*92; dd.rectangle([18,y+6,18+lerp(0,824,q),y+80],fill=(255,194,26,90)); hl.append(y+43)
    tf=T('feel',102.4)
    if t>=tf-0.5:
        q=expo((t-tf+0.5)/0.25); y=176+5*92
        dd.rectangle([18,y+6,842,y+80],fill=(255,240,200,int(255*q))); dd.rectangle([18,y+6,26,y+80],fill=(201,169,110,int(255*q)))
        dd.text((40,y+20),'How you feel',font=f(DMB,36),fill=(50,54,66,int(255*q))); dd.text((560,y+24),'SYMPTOM LOG',font=f(MONOB,26),fill=(150,110,30,int(255*q)))
        hl.append(y+43)
    doc=doc.convert('RGBA'); rot=doc.rotate(ang,resample=Image.BICUBIC,expand=True) if abs(ang)>0.05 else doc
    sh=Image.new('RGBA',rot.size,(0,0,0,0)); ImageDraw.Draw(sh).rectangle([10,14,rot.width-1,rot.height-1],fill=(0,0,0,150)); sh=sh.filter(ImageFilter.GaussianBlur(14))
    ox=110-(rot.width-860)//2; oy=int(lerp(1500,420,p))-(rot.height-780)//2
    im.alpha_composite(sh,(ox+8,oy+16)); im.alpha_composite(rot,(ox,oy))
    tc=T('cross-reference',102.6)
    if t>=tc and len(hl)>1:
        q=expo((t-tc)/0.35); x=1000; ys=[420+h for h in hl]
        d.line([(x,ys[0]),(x,lerp(ys[0],ys[-1],q))],fill=A(VGOLD,1),width=5)
        if GL: GL.line([(x,ys[0]),(x,lerp(ys[0],ys[-1],q))],fill=A(VGOLD,1),width=12)
        for yy in ys:
            if yy<=lerp(ys[0],ys[-1],q)+1: d.line([(972,yy),(x,yy)],fill=A(VGOLD,1),width=5); d.ellipse([964,yy-8,980,yy+8],fill=A(VGOLD,1))
        tag(d,700,lerp(ys[0],ys[-1],0.5)-23,'CROSS-REFERENCE',VGOLD,24,q) if q>0.6 else None
    tm=T('matters',104.3)
    if t>=tm-0.1:
        pp=expo((t-tm+0.1)/0.12); y=1200; x0=110; x1=lerp(x0,970,pp)
        if GL: GL.rectangle([x0-4,y-6,x1+4,y+94],outline=A(RED,1),width=10)
        lit_bar(d,x0,y,x1,y+88,RED); d.rectangle([x0,y+84,x1,y+88],fill=A((140,0,0),1))
        if pp>0.6: fn=f(BEB,70); txt(d,x0+26,y+10,'LABS + SYMPTOMS',fn,WHITE); txt(d,x0+26+d.textlength('LABS + SYMPTOMS',font=fn)+20,y+34,'= ROADMAP',f(MONOB,32),WHITE)
def sc_steps(im,d,t):     # PROCESS STEPPER (top zone)
    steps=[('01','MEASURE',T('measure',105.7)),('02','UNDERSTAND',T('understand',106.4)),('03','DECIDE',T('informed',107.6))]
    t0=SC_STEPS[0]; a0=appear(t,t0,0.2)
    sc=Image.new('RGBA',(W,330),(0,0,0,0)); sd=ImageDraw.Draw(sc)
    for y in range(330): sd.line([(0,y),(W,y)],fill=(4,6,12,int(150*a0*(1-(y/330)**2))))
    im.alpha_composite(sc,(0,400))
    x=64; wds=[270,330,250]
    for i,(n,lbl,tt) in enumerate(steps):
        on=t>=tt; a=a0; w=wds[i]; y=440
        pts=[(x,y),(x+w,y),(x+w+36,y+60),(x+w,y+120),(x,y+120),(x+36,y+60)] if i>0 else [(x,y),(x+w,y),(x+w+36,y+60),(x+w,y+120),(x,y+120)]
        if on:
            b=appear(t,tt,0.12); d.polygon(pts,fill=A(VGOLD,b));
            if GL: GL.polygon(pts,outline=A(VGOLD,b),width=10)
            txt(d,x+(44 if i else 22),y+12,n,f(MONOB,24),INK,b); txt(d,x+(44 if i else 22),y+40,lbl,f(BEB,64),INK,b)
        else:
            d.polygon(pts,fill=A((14,16,24),0.85*a),outline=A((90,94,110),a)); txt(d,x+(44 if i else 22),y+12,n,f(MONOB,24),LBL,a); txt(d,x+(44 if i else 22),y+40,lbl,f(BEB,64),(110,110,120),a)
        x+=w+20
    tf=T('forward',108.5)
    if t>=tf-0.2:
        q=expo((t-tf+0.2)/0.4); arrow(d,64,600,lerp(64,1000,q),600,VGOLD,6,1,22)
        if GL: GL.line([(64,600),(lerp(64,1000,q),600)],fill=A(VGOLD,1),width=12)
def sc_cta(im,d,t):       # END CARD
    t0=SC_CTA[0]; a=appear(t,t0,0.25)
    lg=logo(150); lg.putalpha(lg.split()[3].point(lambda v:int(v*a))); im.alpha_composite(lg,(90,420))
    txt(d,270,424,'FREE BREAKDOWN',f(MONOB,30),VGOLD,a)
    rows=[('Which compound fits you',T('compounds',111.8)),('How to read your labs',T('read',113.3))]
    for i,(lbl,tt) in enumerate(rows):
        if t>=tt: b=appear(t,tt,0.12); check(d,270,480+i*56,GREEN,0.9,b); txt(d,316,474+i*56,lbl,f(DMB,36),CREAM,b)
    tc=T('comment',114.8)
    if t>=tc:
        b=expo((t-tc)/0.12); s=lerp(1.12,1.0,b); fn=f(BEB,int(100*s)); label='COMMENT  "LABS"'; tw=d.textlength(label,font=fn)
        x0=(W-tw)/2-30
        if GL: GL.rectangle([x0-4,626,x0+tw+64,650+int(110*s)],outline=A(VGOLD,b),width=12)
        lit_bar(d,x0,630,x0+tw+60,646+int(110*s),VGOLD,b); d.text((x0+30,636),label,font=fn,fill=A(INK,b))
    txt(d,90,800,'FOR RESEARCH & EDUCATIONAL PURPOSES ONLY',f(MONO,20),LBL,a*0.9)
# scene table: (t_in, t_out, fn, mode, layout)  modes: none | push | pip | cut
def build_scenes():
    global SC_SCATTER,SC_ESTER,SC_LAB,SC_STEPS,SC_CTA,MID_RAW
    end_raw=KEEP[-1][1]
    SC_SCATTER=(T('i',60.1)+0.35, T('part',71.5)-0.05)
    SC_ESTER=(T('part',71.5)-0.05, T('so',80.0)-0.1)
    SC_LAB=(T('basic',95.0)-0.1, T('you',105.0)-0.1)
    SC_STEPS=(T('you',105.0)-0.05, T('with',109.0)-0.1)
    SC_CTA=(T('with',109.0)-0.05, end_raw+1)
    MID_RAW=new_to_old(TR['newdur']/2)
    return [
     (T('primobolan',11.7)-0.1, T('generally',21.0)-0.45, sc_primo,'none','card'),
     (T('generally',21.0)-0.05, 29.1, sc_crash,'push','panel'),
     (T('secondarily',29.4)-0.05, T('anyways',35.0)-0.1, sc_mast,'none','bare'),
     (T('anyways',35.0)-0.05, T('number',56.1)-0.2, sc_mech,'pip','bare'),
     (T('equipoise',56.7)-0.05, SC_SCATTER[0], sc_eqbar,'none','bare'),
     (SC_SCATTER[0],SC_SCATTER[1], sc_scatter,'cut','bare'),
     (SC_ESTER[0],SC_ESTER[1], sc_ester,'push','scan'),
     (T('sideways',81.7)-0.4, T('from',89.0)-0.1, sc_fix,'none','goldcard'),
     (T('elevated',92.1)-0.7, T('basic',95.0)-0.15, sc_hct,'none','bare'),
     (SC_LAB[0],SC_LAB[1], sc_lab,'push','bare'),
     (SC_STEPS[0],SC_STEPS[1], sc_steps,'none','bare'),
     (SC_CTA[0],SC_CTA[1], sc_cta,'none','ctacard'),
    ]
def new_to_old(tn):
    acc=0
    for a,b in KEEP:
        if tn<acc+(b-a)-1e-9: return a+(tn-acc)
        acc+=b-a
    return KEEP[-1][1]-1/FPS
SCENES=None
# ---------------- captions ----------------
CAP_Y=1392
CAPFIX={'gonna':'GONNA'}
def build_groups():
    G=[];cur=[]
    for i,x in enumerate(WORDS):
        if cur:
            prev=WORDS[cur[-1]]
            if len(cur)>=3 or x['s']-prev['e']>0.28 or prev['w'][-1] in '.,?!' or any(prev['e']<=c<=x['s']+0.01 for c in CUTS): G.append(cur); cur=[]
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
def captions(im,t):
    g=group_at(t)
    if not g: return
    d=ImageDraw.Draw(im,'RGBA')
    ws=[WORDS[i]['w'].upper().rstrip(',.?!') for i in g]
    size=116
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
    cap=Image.new('RGBA',(W,260),(0,0,0,0)); cd=ImageDraw.Draw(cap); shd=Image.new('RGBA',(W,260),(0,0,0,0)); sd=ImageDraw.Draw(shd)
    prev=max(0,act-1); bt=expo((t-WORDS[g[act]]['s'])/0.07) if act>0 else 1
    bx0=lerp(xs[prev],xs[act],bt)-16; bx1=lerp(xs[prev]+wd[prev],xs[act]+wd[act],bt)+16
    for k,(w_,x_) in enumerate(zip(ws,xs)):
        if k!=act: sd.text((x_+4,46),w_,font=fn,fill=(0,0,0,210))
    cap.alpha_composite(shd.filter(ImageFilter.GaussianBlur(6)))
    lit_bar(cd,bx0,40+size*0.02,bx1,40+size*0.98,RED)
    for k,(w_,x_) in enumerate(zip(ws,xs)): cd.text((x_,40),w_,font=fn,fill=CREAM,stroke_width=0 if k==act else 3,stroke_fill=(0,0,0))
    if abs(s-1)>0.002:
        cap=cap.resize((int(W*s),int(260*s)),Image.BICUBIC); ox=int((W-cap.width)/2); oy=int(CAP_Y-40-(cap.height-260)/2)
    else: ox,oy=0,CAP_Y-40
    im.alpha_composite(cap,(ox,oy))
# ---------------- frame ----------------
def seg_of(t): return sum(1 for c in CUTS if c<=t+1e-6)
def scene_env(sc,t,tin=0.20,tout=0.16):
    return expo((t-sc[0])/tin), clamp((t-sc[1])/tout)
def zoomed(src,t):
    z=1.0 if seg_of(t)%2==0 else 1.08
    t3=T('three',0.6)
    if t<HOOK_END+0.2: z*=lerp(1.0,1.05,ease_io((t-t3+0.05)/0.3))   # visual hook: punch on the subject count
    if abs(z-1)<1e-4: return src
    big=src.resize((int(W*z),int(H*z)),Image.BICUBIC); ox=(big.width-W)//2; oy=int((big.height-H)*0.52)
    return big.crop((ox,oy,ox+W,oy+H))
def frame(src,t):
    global GL
    src=zoomed(src,t)
    active=[sc for sc in SCENES if sc[0]<=t<sc[1]+0.2]
    mode='none'; g=0; pipp=0
    for sc in active:
        pin,pout=scene_env(sc,t)
        if sc[3]=='push': g=max(g,min(1.0 if sc[2] is sc_ester else ease_io((t-sc[0]+0.05)/0.30),1-ease_io((t-sc[1])/0.22)))
        if sc[3]=='pip': pipp=max(pipp,min(ease_io((t-sc[0])/0.35),1-ease_io((t-sc[1])/0.30)))
        if sc[3]=='cut' and sc[0]<=t<sc[1]: mode='cut'
    if mode=='cut': im=carousel_bg()
    elif pipp>0:
        im=carousel_bg(); x0,y0,x1,y1=[lerp(a,b,pipp) for a,b in zip((0,0,W,H),PIPWIN)]
        cx0,cy0,cx1,cy1=[lerp(a,b,pipp) for a,b in zip((0,0,W,H),(165,560,925,1573))]
        win=src.crop((int(cx0),int(cy0),int(cx1),int(cy1))).resize((max(1,int(x1-x0)),max(1,int(y1-y0))),Image.BILINEAR).convert('RGBA')
        m=Image.new('L',win.size,0); ImageDraw.Draw(m).rounded_rectangle([0,0,win.width-1,win.height-1],radius=int(28*pipp),fill=255)
        if pipp<1: bgf=Image.blend(carousel_bg().convert('RGB'),src,1-pipp).convert('RGBA'); im=bgf
        im.paste(win,(int(x0),int(y0)),m)
    else:
        bg=src
        if g>0: bg=Image.blend(src.filter(ImageFilter.GaussianBlur(16*g)),Image.new('RGB',(W,H),(5,8,16)),0.68*g)
        im=bg.convert('RGBA')
        yy=np.arange(H); a=np.where(yy>1250,np.clip((yy-1250)/260,0,1)*120,0); a=np.maximum(a,np.where(yy<420,(1-yy/420)*110,0)); scr=(a*(1-g)).astype(np.uint8)
        im.alpha_composite(Image.merge('RGBA',[Image.new('L',(W,H),c) for c in NAVY]+[Image.fromarray(np.repeat(scr[:,None],W,1))]))
    glow=Image.new('RGBA',(W,H),(0,0,0,0)); GL=ImageDraw.Draw(glow,'RGBA')
    d=ImageDraw.Draw(im,'RGBA')
    if pipp>0.05:
        x0,y0,x1,y1=[lerp(a,b,pipp) for a,b in zip((0,0,W,H),PIPWIN)]
        brackets(d,x0-10,y0-10,x1+10,y1+10,A(VGOLD,pipp),36,5); brackets(GL,x0-10,y0-10,x1+10,y1+10,A(VGOLD,pipp),36,10)
        d.ellipse([x0+18,y0+18,x0+34,y0+34],fill=A(RED,pipp if int(t*3)%2==0 else pipp/3)); txt(d,x0+42,y0+12,'COACH AGZ',f(MONOB,22),WHITE,pipp)
    lineup(d,t)
    hide_band=max([1.0 if mode=='cut' else 0.0, pipp, *[expo((t-sc[0])/0.15)*(1-clamp((t-sc[1])/0.15)) for sc in active if sc[4] in ('panel',)]] )
    for sc in active:
        pin,pout=scene_env(sc,t)
        if sc[3]=='cut' and t>=sc[1]: pout=1
        if pout>=1: continue
        al=pin*(1-pout)*(appear(t,sc[0]+0.3,0.2) if sc[3]=='pip' else 1); lay=Image.new('RGBA',(W,H),(0,0,0,0)); ld=ImageDraw.Draw(lay,'RGBA')
        kind=sc[4]
        if kind=='panel':
            P=(64,470,1016,1300); s=lerp(1.05,1.0,pin)*lerp(1.0,1.03,pout); w=(P[2]-P[0])*s; h=(P[3]-P[1])*s; cx=(P[0]+P[2])/2; cy=(P[1]+P[3])/2
            x0,y0,x1,y1=cx-w/2,cy-h/2,cx+w/2,cy+h/2
            frosted(im,(x0,y0,x1,y1),0.92,8)
            sc[2](lay,ld,t)
            if pin<1: lay=lay.filter(ImageFilter.GaussianBlur(8*(1-pin)))
            lay.putalpha(lay.split()[3].point(lambda v:int(v*al))); im.alpha_composite(lay); d=ImageDraw.Draw(im,'RGBA')
            d.rectangle([x0,y0,x1,y1],outline=A(VGOLD,0.8*al),width=3); brackets(d,x0,y0,x1,y1,A(VGOLD,al),48,7); brackets(GL,x0,y0,x1,y1,A(VGOLD,al),48,14)
            d.ellipse([x0+26,y0+26,x0+42,y0+42],fill=A(RED,al if int(t*4)%2==0 else al/3))
            txt(d,x0+56,y0+18,'AI WITHOUT LABS',f(MONO,28),WHITE,al); fr=f(MONO,28); lab='E2 · TREND'; tw=d.textlength(lab,font=fr); txt(d,x1-30-tw,y0+18,lab,fr,VGOLD,al)
            continue
        if kind=='card':     # glass card slides in from left, crimson bar leads
            dx=lerp(-80,0,expo((t-sc[0])/0.22))-lerp(0,1100,ease_io(pout)); x0,y0,x1,y1=60+dx,400,940+dx,868
            frosted(im,(x0,y0,x1,y1),0.86,14,24); d=ImageDraw.Draw(im,'RGBA')
            bar_h=lerp(0,y1-y0,expo((t-sc[0]+0.05)/0.15)); d.rounded_rectangle([x0,y0,x0+10,y0+bar_h],radius=4,fill=A(CRIM,1))
            GL.rectangle([x0,y0,x0+10,y0+bar_h],fill=A(CRIM,0.9))
            if abs(dx)>0.5: _g=GL; GL=ImageDraw.Draw(Image.new('RGBA',(8,8)),'RGBA')
            sc[2](lay,ld,t); txt(ld,770,836,'@COACH.AGZ',f(MONO,20),LBL)
            if abs(dx)>0.5: GL=_g
            im.alpha_composite(lay.transform((W,H),Image.AFFINE,(1,0,-dx,0,1,0)) if abs(dx)>0.5 else lay); continue
        if kind=='goldcard':   # card with gold top rule drawing across (rises in)
            dy=lerp(30,0,pin); x0,y0,x1,y1=60,390+dy,940,868+dy
            frosted(im,(x0,y0,x1,y1),0.86*al+0.0,14,20); d=ImageDraw.Draw(im,'RGBA')
            d.rectangle([x0,y0,x0+lerp(0,x1-x0,expo((t-sc[0])/0.3)),y0+5],fill=A(VGOLD,al)); GL.rectangle([x0,y0,x0+lerp(0,x1-x0,expo((t-sc[0])/0.3)),y0+5],fill=A(VGOLD,al))
            sc[2](lay,ld,t)
            lay.putalpha(lay.split()[3].point(lambda v:int(v*al))); im.alpha_composite(lay,(0,int(dy))); continue
        if kind=='ctacard':
            x0,y0,x1,y1=60,390,1020,850
            frosted(im,(x0,y0,x1,y1),0.86*al,14,20); d=ImageDraw.Draw(im,'RGBA')
            brackets(d,x0,y0,x1,y1,A(VGOLD,al),30,5); brackets(GL,x0,y0,x1,y1,A(VGOLD,al),30,10)
            sc[2](lay,ld,t); lay.putalpha(lay.split()[3].point(lambda v:int(v*al))); im.alpha_composite(lay); continue
        # bare / scan: content only, with its own entrance
        sc[2](lay,ld,t)
        if sc[2] is sc_hct:
            s=lerp(0.92,1.0,pin)
            if abs(s-1)>0.003: lay=_scale_about(lay,s,540,800)
        lay.putalpha(lay.split()[3].point(lambda v:int(v*al))); im.alpha_composite(lay)
    band(im,t,hide_band)
    GLs=GL; GL=None
    if glow.getbbox():
        sm=glow.resize((W//4,H//4),Image.BILINEAR)
        g1=np.asarray(sm.filter(ImageFilter.GaussianBlur(3.5))).astype(np.float32)/255; g2=np.asarray(sm.filter(ImageFilter.GaussianBlur(10))).astype(np.float32)/255
        prem=np.clip(g1[...,:3]*g1[...,3:]*2.0+g2[...,:3]*g2[...,3:]*1.6,0,1)
        prem=np.asarray(Image.fromarray((prem*255).astype(np.uint8)).resize((W,H),Image.BILINEAR)).astype(np.float32)/255
        b=np.asarray(im.convert('RGB')).astype(np.float32)/255
        im=Image.fromarray(((1-(1-b)*(1-prem))*255).astype(np.uint8)).convert('RGBA')
    text_hook(im,t)
    d=ImageDraw.Draw(im,'RGBA'); d.rectangle([0,0,7,H],fill=GOLD)
    captions(im,t)
    return im.convert('RGB')
def _scale_about(lay,s,cx,cy):
    sm=lay.resize((int(W*s),int(H*s)),Image.BICUBIC); out=Image.new('RGBA',(W,H),(0,0,0,0)); out.alpha_composite(sm,(int(cx-cx*s),int(cy-cy*s))); return out
SCENES=build_scenes()
if __name__=='__main__':
    mode=sys.argv[2]; os.makedirs(WK+'qc',exist_ok=True)
    if mode=='stills':
        for tt in [float(x) for x in sys.argv[3:]]:   # times on the OUTPUT timeline
            to=new_to_old(tt); subprocess.run(['ffmpeg','-v','error','-y','-ss',f'{to:.4f}','-i',WK+'a30.mp4','-frames:v','1',WK+'qc/_src.png'])
            frame(Image.open(WK+'qc/_src.png').convert('RGB'),to).resize((540,960)).save(WK+f'qc/st_{tt:06.2f}.jpg',quality=85)
        sys.exit()
    n0,n1,out=int(sys.argv[2]),int(sys.argv[3]),sys.argv[4]
    olds=[round(new_to_old(n/FPS)*FPS) for n in range(n0,n1)]
    first,last=olds[0],olds[-1]
    dec=subprocess.Popen(['ffmpeg','-v','error','-ss',f'{first/FPS:.4f}','-i',WK+'a30.mp4','-frames:v',str(last-first+1),'-f','rawvideo','-pix_fmt','rgb24','-'],stdout=subprocess.PIPE)
    enc=subprocess.Popen(['ffmpeg','-v','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-','-c:v','libx264','-crf','16','-preset','medium','-pix_fmt','yuv420p',out],stdin=subprocess.PIPE)
    cur=first-1; buf=None
    for n,o in zip(range(n0,n1),olds):
        while cur<o:
            buf=dec.stdout.read(W*H*3); cur+=1
            if len(buf)<W*H*3: raise SystemExit(f'short read at frame {cur}')
        enc.stdin.write(frame(Image.frombuffer('RGB',(W,H),buf),o/FPS).tobytes())
    enc.stdin.close(); enc.wait(); dec.kill(); print('done',n0,n1)
