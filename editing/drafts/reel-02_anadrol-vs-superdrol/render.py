# Reel 02 — "Anadrol vs Superdrol" — 1080x1920 30fps render
# usage: python3 -I render.py <scratch> stills t1 t2 ...        (raw-timeline seconds)
#        python3 -I render.py <scratch> chunk n0 n1 out.mp4      (output frame range)
import json, subprocess, sys, math, os
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
HERE=os.path.dirname(os.path.abspath(__file__))
S=sys.argv[1]; F=S+'/fonts/'; SRC=S+'/src/raw.mp4'
W,H=1080,1920; FPS=30
TR=json.load(open(HERE+'/trim.json')); KEEP=TR['keep']; REM=TR['remove']
WORDS=json.load(open(HERE+'/words_final.json'))
FT=json.load(open(HERE+'/face_track_pip.json'))
LOGO_P=HERE+'/../../brand/logo/coach-agz-logo-round.jpg'
# ---------- palette (BRAND.md overlay accents) ----------
GOLD=(201,169,110); CREAM=(244,241,234); NAVY=(14,17,23); MUTED=(160,160,168)
RED=(255,34,28); VGOLD=(255,194,26); CYAN=(0,229,255); GREEN=(30,255,110); DEEP=(2,3,8); INK=(6,8,14); WHITE=(255,255,255)
AMBER=(240,160,48); SPGREEN=(60,203,106)
C_ANA=CYAN; C_SUP=VGOLD          # compound colour-coding used in every scene
MONO='JBMono-500.ttf'; MONOB='JBMono-700.ttf'; BEB='BebasNeue.ttf'; DMB='DMSans-700.ttf'; DMR='DMSans-400.ttf'; BC='BC-700.ttf'; BCX='BC-800.ttf'
_fc={}
def f(n,s):
    k=(n,int(s))
    if k not in _fc: _fc[k]=ImageFont.truetype(F+n,int(s))
    return _fc[k]
def clamp(x,a=0,b=1): return max(a,min(b,x))
def expo(x): x=clamp(x); return 1 if x>=1 else 1-2**(-10*x)
def ease_io(x): x=clamp(x); return 4*x**3 if x<.5 else 1-(-2*x+2)**3/2
def back(x,k=1.2): x=clamp(x); return 1+(k+1)*(x-1)**3+k*(x-1)**2   # small settle, used sparingly
def lerp(a,b,t): return a+(b-a)*t
def A(c,a): return tuple(c[:3])+(int(clamp(a)*255),)
def ap(t,t0,d=0.16): return expo((t-t0)/d)
GL=None
# ---------- time mapping (trim) ----------
def new_to_old(tn):
    acc=0
    for a,b in KEEP:
        if tn<acc+(b-a)-1e-9: return a+(tn-acc)
        acc+=b-a
    return KEEP[-1][1]-1/FPS
def old_to_new(to):
    acc=0
    for a,b in KEEP:
        if to<b: return acc+max(0,to-a)
        acc+=b-a
    return acc
CUTS=[b for a,b in REM]            # raw times where a jump cut lands
N_OUT=int(round(TR['dur_new']*FPS))
# ---------- primitives ----------
def brackets(d,x0,y0,x1,y1,col,L=34,w=4):
    for (cx,cy,sx,sy) in [(x0,y0,1,1),(x1,y0,-1,1),(x0,y1,1,-1),(x1,y1,-1,-1)]:
        d.line([(cx,cy),(cx+sx*L,cy)],fill=col,width=w); d.line([(cx,cy),(cx,cy+sy*L)],fill=col,width=w)
def lit_bar(d,x0,y0,x1,y1,col,a=1.0):
    h=max(1,int(y1-y0))
    if x1<=x0: return
    for i in range(h):
        k=i/h; c=tuple(int(min(255,v*(1.18-0.36*k)+(40 if k<0.12 else 0))) for v in col)
        d.line([(x0,y0+i),(x1,y0+i)],fill=c+(int(255*a),))
def tag(d,x,y,label,col=RED,size=30,a=1.0,glow=True,font=MONO):
    fn=f(font,size); tw=d.textlength(label,font=fn); h=size+16
    lit_bar(d,x,y,x+tw+24,y+h,col,a); d.text((x+12,y+6),label,font=fn,fill=A(INK if col in (VGOLD,GREEN,CYAN) else WHITE,a))
    if GL and glow: GL.rectangle([x-4,y-4,x+tw+28,y+h+4],outline=A(col,a),width=8)
    return x+tw+24
def tagw(d,label,size=30,font=MONO): return d.textlength(label,font=f(font,size))+24
def txt(d,x,y,s,font,col,a=1.0,anchor='la'): d.text((x,y),s,font=font,fill=A(col,a),anchor=anchor)
def check(d,x,y,col,s=1.0,a=1.0):
    pts=[(x,y+16*s),(x+10*s,y+28*s),(x+30*s,y+2*s)]
    d.line(pts,fill=A(col,a),width=int(6*s))
    if GL: GL.line(pts,fill=A(col,a),width=int(12*s))
def cross(d,x,y,col,s=1.0,a=1.0):
    for p in ([(x,y),(x+28*s,y+28*s)],[(x+28*s,y),(x,y+28*s)]):
        d.line(p,fill=A(col,a),width=int(6*s))
        if GL: GL.line(p,fill=A(col,a),width=int(12*s))
def glow_line(d,pts,col,w=5,a=1.0,gw=12):
    d.line(pts,fill=A(col,a),width=w,joint='curve')
    if GL: GL.line(pts,fill=A(col,a),width=gw,joint='curve')
def partial(pts,p):
    """first fraction p of a polyline"""
    if p<=0: return pts[:1]
    L=[0]
    for i in range(1,len(pts)): L.append(L[-1]+math.dist(pts[i-1],pts[i]))
    tgt=L[-1]*clamp(p); out=[pts[0]]
    for i in range(1,len(pts)):
        if L[i]<=tgt: out.append(pts[i])
        else:
            k=(tgt-L[i-1])/max(1e-6,L[i]-L[i-1]); out.append((lerp(pts[i-1][0],pts[i][0],k),lerp(pts[i-1][1],pts[i][1],k))); break
    return out
def frosted(im,box,dark=0.86,blur=10,radius=0):
    x0,y0,x1,y1=[int(v) for v in box]; x0=max(0,x0); y0=max(0,y0); x1=min(W,x1); y1=min(H,y1)
    if x1<=x0 or y1<=y0: return
    reg=im.crop((x0,y0,x1,y1)).convert('RGB').filter(ImageFilter.GaussianBlur(blur))
    reg=Image.blend(reg,Image.new('RGB',reg.size,DEEP),dark).convert('RGBA')
    if radius:
        m=Image.new('L',reg.size,0); ImageDraw.Draw(m).rounded_rectangle([0,0,reg.size[0]-1,reg.size[1]-1],radius=radius,fill=255)
        im.paste(reg,(x0,y0),m)
    else: im.paste(reg,(x0,y0))
def frosted_a(im,box,a,dark=0.86,blur=10,radius=0):
    """frosted panel faded by alpha a"""
    if a<=0: return
    if a>=0.999: return frosted(im,box,dark,blur,radius)
    x0,y0,x1,y1=[int(v) for v in box]
    tmp=im.copy(); frosted(tmp,box,dark,blur,radius)
    reg=Image.blend(im.crop((x0,y0,x1,y1)),tmp.crop((x0,y0,x1,y1)),a); im.paste(reg,(x0,y0))
# ---------- background canvas for reframed layouts ----------
def make_bg():
    yy,xx=np.mgrid[0:H,0:W].astype(np.float32)
    base=np.zeros((H,W,3),np.float32)+np.array(NAVY,np.float32)
    g1=np.exp(-(((xx-1000)/520)**2+((yy-160)/520)**2))[...,None]*np.array([60,44,12],np.float32)     # warm gold glow top-right
    g2=np.exp(-(((xx-40)/560)**2+((yy-1780)/560)**2))[...,None]*np.array([70,6,14],np.float32)       # crimson glow bottom-left
    img=np.clip(base+g1+g2,0,255).astype(np.uint8)
    im=Image.fromarray(img).convert('RGBA'); d=ImageDraw.Draw(im,'RGBA')
    for y in range(20,H,48):
        for x in range(20,W,48): d.point((x,y),fill=(120,124,140,70))
    return im
BG=None
# ---------- layouts ----------
def L_full(z):
    return dict(s=z,fx=-(W*z-W)/2,fy=-(H*z-H)*0.35,x0=0,y0=0,x1=W,y1=H,r=0)
L_WIN=dict(s=0.70,fx=162,fy=-20,x0=162,y0=236,x1=918,y1=1000,r=40)
L_SIDE=dict(s=0.64,fx=352,fy=40,x0=352,y0=250,x1=1043,y1=1110,r=40)
def L_pip(t):
    cx=float(np.interp(t,FT['t'],FT['cx'])); cy=float(np.interp(t,FT['t'],FT['cy']))-60; s=0.62
    return dict(s=s,fx=540-cx*s,fy=500-cy*s,x0=290,y0=250,x1=790,y1=750,r=250)
# (raw time, layout, transition seconds; 0 = instant on a jump cut)
LAYOUTS=[(0,'full',0),(12.25,'win',0.42),(18.92,'side',0.40),(24.8,'full',0),(29.80,'win',0.42),(44.62,'full',0.40),(59.62,'pip',0.45),(72.92,'full',0.36)]
def zoom_at(t):
    k=sum(1 for c in CUTS if c<=t+1e-6)
    z=1.0 if k%2==0 else 1.07
    # purposeful punch-ins on emphasis lines
    for a,b,zz in [(9.95,10.95,1.12),(77.95,81.55,1.06),(82.40,86.3,1.10)]:
        if a<=t<b: z=zz
    return z
def L_named(name,t):
    if name=='full': return L_full(zoom_at(t))
    if name=='win': return dict(L_WIN)
    if name=='side': return dict(L_SIDE)
    if name=='pip': return L_pip(t)
def layout(t):
    idx=max(i for i,(ts,_,_) in enumerate(LAYOUTS) if ts<=t)
    ts,name,dur=LAYOUTS[idx]; cur=L_named(name,t)
    if idx==0 or dur==0 or t>=ts+dur: return cur,name,1.0
    prev=L_named(LAYOUTS[idx-1][1],t); p=ease_io((t-ts)/dur)
    return {k:lerp(prev[k],cur[k],p) for k in cur},name,p
# ---------- captions ----------
def build_groups():
    G=[];cur=[]
    for i,x in enumerate(WORDS):
        if cur:
            prev=WORDS[cur[-1]]
            cutb=any(prev['e']-0.05<=c<=x['s']+0.05 for c in CUTS)
            if len(cur)>=3 or x['s']-prev['e']>0.28 or prev['p'] or cutb or len(' '.join(WORDS[j]['w'] for j in cur+[i]))>18: G.append(cur); cur=[]
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
    if t>WORDS[lo[-1]]['e']+0.5: return None
    return lo
ACCENT={'ANADROL':C_ANA,'OXYMETHOLONE':C_ANA,'SUPERDROL':C_SUP,'METHASTERONE':C_SUP,'ER':RED,'BANNED IT':RED,'ZERO':RED,'HDL':VGOLD,'F*CK':RED}
def cap_y(name,p,prevname):
    Y={'full':1188,'win':886,'side':1150,'pip':790}
    return lerp(Y.get(prevname,1188),Y[name],p)
def captions(im,t,cy):
    g=group_at(t)
    if not g: return
    d=ImageDraw.Draw(im,'RGBA')
    ws=[WORDS[i]['w'] for i in g]
    size=112
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
    CH=240; cap=Image.new('RGBA',(W,CH),(0,0,0,0)); cd=ImageDraw.Draw(cap); shd=Image.new('RGBA',(W,CH),(0,0,0,0)); sd=ImageDraw.Draw(shd)
    prev=max(0,act-1); bt=expo((t-WORDS[g[act]]['s'])/0.07) if act>0 else 1
    bx0=lerp(xs[prev],xs[act],bt)-16; bx1=lerp(xs[prev]+wd[prev],xs[act]+wd[act],bt)+16
    for k,(w_,x_) in enumerate(zip(ws,xs)): sd.text((x_+4,44),w_,font=fn,fill=(0,0,0,220))
    cap.alpha_composite(shd.filter(ImageFilter.GaussianBlur(7)))
    acc=ACCENT.get(ws[act]); boxc=RED if acc in (None,RED) else acc
    lit_bar(cd,bx0,36+size*0.02,bx1,36+size*0.97,boxc)
    for k,(w_,x_) in enumerate(zip(ws,xs)):
        col=CREAM
        if k!=act and ACCENT.get(w_) and WORDS[g[k]]['s']<=t: col=ACCENT[w_]
        if k==act: col=INK if boxc in (VGOLD,CYAN) else WHITE
        cd.text((x_,36),w_,font=fn,fill=col,stroke_width=0 if k==act else 3,stroke_fill=(0,0,0))
    if abs(s-1)>0.002:
        cap=cap.resize((int(W*s),int(CH*s)),Image.BICUBIC); ox=int((W-cap.width)/2); oy=int(cy-36-(cap.height-CH)/2)
    else: ox,oy=0,int(cy-36)
    im.alpha_composite(cap,(ox,oy))
# =============== SCENES (raw-time) ===============
LOW=(44,1322,1036,1566)       # lower strip panel in FULL layout (chest; face clear)
def low_panel(im,t,t0,t1,title,right,hard_out=False,box=LOW):
    pin=expo((t-t0)/0.22); pout=0 if hard_out else clamp((t-t1)/0.14)
    al=pin*(1-pout)
    if al<=0: return 0
    x0,y0,x1,y1=box; yo=lerp(40,0,pin)
    frosted_a(im,(x0,y0+yo,x1,y1+yo),al,0.84,10,18)
    d=ImageDraw.Draw(im,'RGBA')
    d.rounded_rectangle([x0,y0+yo,x1,y1+yo],radius=18,outline=A(VGOLD,0.55*al),width=2)
    brackets(d,x0,y0+yo,x1,y1+yo,A(VGOLD,al),40,6); brackets(GL,x0,y0+yo,x1,y1+yo,A(VGOLD,al),40,12)
    d.ellipse([x0+24,y0+yo+24,x0+38,y0+yo+38],fill=A(RED,al if int(t*4)%2==0 else al/3))
    txt(d,x0+52,y0+yo+16,title,f(MONO,26),WHITE,al)
    if right:
        fr=f(MONO,26); txt(d,x1-26-d.textlength(right,font=fr),y0+yo+16,right,fr,VGOLD,al)
    return al
def layer_alpha(lay,al):
    if al<0.999: lay.putalpha(lay.split()[3].point(lambda v:int(v*al)))
    return lay

# ---- S1: risk over time — dual line chart (lower strip) ----
def s1(im,t):
    T0,T1=1.80,9.10
    if not (T0<=t<T1+0.2): return
    al=low_panel(im,t,T0,T1,'RISK OVER TIME','2 ORALS',hard_out=True)
    if al<=0: return
    lay=Image.new('RGBA',(W,H),(0,0,0,0)); d=ImageDraw.Draw(lay,'RGBA')
    X0,X1,Y0,Y1=110,990,1388,1520
    a0=ap(t,T0+0.1,0.2)
    d.line([(X0,Y1),(X1,Y1)],fill=A((120,124,140),a0),width=2); d.line([(X0,Y0-6),(X0,Y1)],fill=A((120,124,140),a0),width=2)
    txt(d,X0,Y1+8,'DAYS',f(MONO,20),MUTED,a0); txt(d,X1,Y1+8,'YEARS',f(MONO,20),MUTED,a0,'ra'); txt(d,X0-14,Y0-4,'RISK',f(MONO,18),MUTED,a0,'ra')
    # alarm threshold
    thr=Y0+26
    if t>2.9:
        p=ap(t,2.9,0.3); x=X0
        while x<lerp(X0,X1,p):
            d.line([(x,thr),(min(x+16,X1),thr)],fill=A(RED,0.7),width=2); x+=28
        txt(d,X1-4,thr-24,'ALARM',f(MONO,18),RED,p,'ra')
    # curve A: fast spike
    ptsA=[]
    for i in range(60):
        u=i/59; x=lerp(X0,X1,u)
        y=Y1-(Y1-Y0+10)*(1-math.exp(-u*14))*(0.92+0.08*math.sin(u*40))
        ptsA.append((x,y))
    if t>2.50:
        p=expo((t-2.50)/1.4)
        glow_line(d,partial(ptsA,p),RED,6,1,14)
        if t>3.20:
            q=ap(t,3.20); px,py=ptsA[12]
            brackets(d,px-30,py-30,px+30,py+30,A(RED,q),12,4); tag(d,px+40,py-6,'ER · FAST',RED,24,q)
    # curve B: slow quiet creep
    ptsB=[]
    for i in range(60):
        u=i/59; x=lerp(X0,X1,u); y=Y1-(Y1-Y0)*0.86*(u**2.4)
        ptsB.append((x,y))
    if t>4.96:
        p=clamp((t-4.96)/2.6)
        glow_line(d,partial(ptsB,ease_io(p)),VGOLD,6,1,14)
        if t>7.20:
            q=ap(t,7.20); px,py=ptsB[-1]
            tag(d,px-tagw(d,'QUIET · YEARS',24)-10,py+4,'QUIET · YEARS',VGOLD,24,q)
        if t>8.02:
            q=ap(t,8.02); px,py=ptsB[36]
            txt(d,px,py-40,'NO ALARM',f(MONO,22),MUTED,q,'ma'); d.line([(px,py-14),(px,py-2)],fill=A(MUTED,q),width=2)
    im.alpha_composite(layer_alpha(lay,al))

# ---- S2: compound ID cards + 17α molecule (WIN layout) ----
def card(d,x0,y0,x1,y1,col,kicker,name,chem,a_card,a_name,a_chem,compact=0):
    if a_card<=0: return
    yo=lerp(30,0,a_card)
    d.rounded_rectangle([x0,y0+yo,x1,y1+yo],radius=16,fill=A((8,10,18),0.94*a_card),outline=A(col,0.9*a_card),width=3)
    if GL: GL.rounded_rectangle([x0,y0+yo,x1,y1+yo],radius=16,outline=A(col,0.8*a_card),width=8)
    lit_bar(d,x0+3,y0+yo+3,x1-3,y0+yo+12,col,a_card)
    txt(d,x0+24,y0+yo+26,kicker,f(MONO,22),col,a_card)
    sz=lerp(92,64,compact)
    if a_name>0: txt(d,x0+22,y0+yo+lerp(56,50,compact),name,f(BEB,sz),WHITE,a_name)
    if a_chem>0:
        n=int(len(chem)*clamp(a_chem*1.4)); txt(d,x0+24,y1+yo-lerp(54,44,compact),chem[:n],f(MONO,26),MUTED,a_chem)
def ring_pts(cx,cy,r,n,rot):
    return [(cx+r*math.cos(rot+2*math.pi*i/n),cy+r*math.sin(rot+2*math.pi*i/n)) for i in range(n)]
def s2(im,t):
    T0,T1=12.48,18.92
    if not (T0-0.1<=t<T1+0.25): return
    out=clamp((t-T1)/0.18); al=1-out
    lay=Image.new('RGBA',(W,H),(0,0,0,0)); d=ImageDraw.Draw(lay,'RGBA')
    cp=ease_io((t-17.04)/0.35)            # cards compact upward when the molecule arrives
    y0=lerp(1056,1040,cp); y1=lerp(1300,1176,cp)
    card(d,60,y0,522,y1,C_ANA,'COMPOUND A','ANADROL','OXYMETHOLONE',ap(t,12.86,0.2),ap(t,14.12,0.14),ap(t,12.86,0.5),cp)
    card(d,558,y0,1020,y1,C_SUP,'COMPOUND B','SUPERDROL','METHASTERONE',ap(t,15.16,0.2),ap(t,16.40,0.14),ap(t,15.16,0.5),cp)
    if t>14.48:
        q=ap(t,14.48,0.12); cy=(y0+y1)/2
        d.ellipse([540-34,cy-34,540+34,cy+34],fill=A(RED,q)); txt(d,540,cy+2,'VS',f(BEB,44),WHITE,q,'mm')
        if GL: GL.ellipse([540-38,cy-38,540+38,cy+38],outline=A(RED,q),width=10)
    if t>17.04:
        a=ap(t,17.10,0.25)
        # steroid nucleus line schematic: 3 hexagons + 1 pentagon (cyan X-ray)
        r=46; cx0,cy0=330,1330
        rings=[ring_pts(cx0,cy0,r,6,math.pi/6), ring_pts(cx0+r*math.sqrt(3),cy0,r,6,math.pi/6),
               ring_pts(cx0+r*math.sqrt(3)*1.5,cy0-r*1.5,r,6,math.pi/6)]
        pc=(cx0+r*math.sqrt(3)*1.5+r*1.62,cy0-r*1.5-r*0.12)
        pent=ring_pts(pc[0],pc[1],r*0.86,5,math.pi)
        draw_p=clamp((t-17.10)/0.6)
        for k,rg in enumerate(rings+[pent]):
            p=clamp(draw_p*4-k)
            if p>0: glow_line(d,partial(rg+[rg[0]],p),CYAN,4,a,10)
        c17=max(pent,key=lambda q:q[0]-q[1]*0.2)
        if t>17.36:
            q=ap(t,17.36,0.12)
            d.line([c17,(c17[0]+52,c17[1]-46)],fill=A(RED,q),width=5); d.ellipse([c17[0]+44,c17[1]-56,c17[0]+64,c17[1]-36],fill=A(RED,q))
            bx=(c17[0]-36,c17[1]-82,c17[0]+92,c17[1]+30); brackets(d,*bx,A(RED,q),16,4)
            if GL: brackets(GL,*bx,A(RED,q),16,8)
        if t>17.82: tag(d,700,1236,'17α-METHYL',RED,30,ap(t,17.82))
        if t>18.18: tag(d,700,1300,'ALKYLATED',RED,30,ap(t,18.18))
        if t>18.68:
            q=ap(t,18.68); x=700; y=1372
            d.rounded_rectangle([x,y,x+120,y+46],radius=23,outline=A(WHITE,q),width=3); d.rounded_rectangle([x,y,x+60,y+46],radius=23,fill=A(WHITE,q))
            txt(d,x+138,y+4,'ORAL',f(BEB,48),WHITE,q)
        # both cards link down to the C17 site
        if t>17.20:
            p=clamp((t-17.20)/0.4)
            for xx,col in ((291,C_ANA),(789,C_SUP)):
                pts=[(xx,y1),(xx,y1+24),(c17[0]+(-20 if xx<540 else 20),y1+24),(c17[0]+(-20 if xx<540 else 20),c17[1]-90)]
                glow_line(d,partial(pts,p),col,3,0.8*a,8)
        txt(d,110,1460,'SHARED 17α-ALKYLATED CORE',f(MONO,22),MUTED,a)
    im.alpha_composite(layer_alpha(lay,al))

# ---- S3: strength bar ramp → 4–6 week block (SIDE layout, left rail) ----
def s3(im,t):
    T0,T1=19.0,24.8
    if not (T0<=t<T1): return
    lay=Image.new('RGBA',(W,H),(0,0,0,0)); d=ImageDraw.Draw(lay,'RGBA')
    X0,X1=48,330
    a=ap(t,19.16,0.2)
    txt(d,X0,300,'STRENGTH',f(MONO,26),VGOLD,a); d.line([(X0,340),(X0+lerp(0,282,a),340)],fill=A(VGOLD,a),width=3)
    morph=ease_io((t-22.04)/0.4)
    if morph<1:
        for i in range(10):
            y=372+i*58; tt=19.62+i*0.19; p=expo((t-tt)/0.22)
            if p<=0: continue
            L=(0.18+0.82*((i+1)/10)**0.8)*(X1-X0-56)
            txt(d,X0,y+4,f'D{i+1}',f(MONO,20),MUTED,p*(1-morph))
            col=VGOLD if i<9 else RED
            lit_bar(d,X0+52,y,X0+52+L*p*(1-morph*0.6),y+34,col,(1-morph))
            if GL: GL.rectangle([X0+52,y,X0+52+L*p,y+34],fill=A(col,0.35*(1-morph)))
        if t>21.50:
            q=ap(t,21.50,0.12)*(1-morph)
            txt(d,X0,960,'10',f(BEB,lerp(150,170,ap(t,21.5,0.12))),RED,q); txt(d,X0+120,1000,'DAYS',f(BEB,64),WHITE,q)
            if GL: GL.text((X0,960),'10',font=f(BEB,170),fill=A(RED,q*0.8))
    if morph>0:
        txt(d,X0,372+lerp(20,0,morph)-0,'CYCLE · WEEKS',f(MONO,22),MUTED,morph)
        for i in range(8):
            y=420+i*76; p=morph
            on4= t>23.66