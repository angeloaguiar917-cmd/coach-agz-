# Reel 02 - "Anadrol vs Superdrol" - 1080x1920 30fps render
# usage: python3 -I render.py <scratch> stills t1 t2 ...   (raw-timeline seconds)
#        python3 -I render.py <scratch> chunk n0 n1 out.mp4 (OUTPUT frame range, trimmed timeline)
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
AMBER=(240,160,48)
C_ANA=CYAN; C_SUP=VGOLD          # compound colour-coding used everywhere
MONO='JBMono-500.ttf'; MONOB='JBMono-700.ttf'; BEB='BebasNeue.ttf'; DMB='DMSans-700.ttf'; DMR='DMSans-400.ttf'; BC='BC-700.ttf'; BCX='BC-800.ttf'
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
def ap(t,t0,d=0.16): return expo((t-t0)/d)
GL=None
# ---------- time mapping (trim) ----------
def new_to_old(tn):
    acc=0
    for a,b in KEEP:
        if tn<acc+(b-a)-1e-9: return a+(tn-acc)
        acc+=b-a
    return KEEP[-1][1]-1/FPS
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
    lit_bar(d,x,y,x+tw+24,y+h,col,a); d.text((x+12,y+6),label,font=fn,fill=A(INK if col in (VGOLD,GREEN,CYAN,AMBER) else WHITE,a))
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
    if len(pts)<2: return
    d.line(pts,fill=A(col,a),width=w,joint='curve')
    if GL: GL.line(pts,fill=A(col,a),width=gw,joint='curve')
def partial(pts,p):
    if p<=0: return pts[:1]
    if p>=1: return pts
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
    if a<=0: return
    if a>=0.999: return frosted(im,box,dark,blur,radius)
    x0,y0,x1,y1=[int(v) for v in box]
    tmp=im.copy(); frosted(tmp,box,dark,blur,radius)
    reg=Image.blend(im.crop((x0,y0,x1,y1)),tmp.crop((x0,y0,x1,y1)),a); im.paste(reg,(x0,y0))
# ---------- layouts (reframe footage so graphics get room; footage itself untouched) ----------
def L_full(z):
    return dict(s=z,fx=-(W*z-W)/2,fy=-(H*z-H)*0.35,r=0)
L_WIN=dict(s=0.70,fx=162,fy=-28,r=40)      # footage floats top; lower third free
L_SIDE=dict(s=0.66,fx=360,fy=60,r=40)      # footage right; left rail free
def L_pip(t):
    cx=float(np.interp(t,FT['t'],FT['cx'])); cy=float(np.interp(t,FT['t'],FT['cy']))-40; s=0.60
    return dict(s=s,fx=540-cx*s,fy=470-cy*s,r=250)
LAYOUTS=[(0,'full',0),(12.25,'win',0.42),(18.95,'side',0.40),(24.80,'full',0),(29.80,'win',0.42),(44.60,'full',0.40),(52.40,'win',0.42),(59.60,'pip',0.45),(72.90,'full',0.36)]
def zoom_at(t):
    k=sum(1 for c in CUTS if c<=t+1e-6)
    z=1.0 if k%2==0 else 1.07
    for a,b,zz in [(9.95,10.92,1.12),(77.95,81.55,1.06),(82.30,86.40,1.10)]:
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
    if idx==0 or dur==0 or t>=ts+dur: return cur,name,1.0,name
    pname=LAYOUTS[idx-1][1]; prev=L_named(pname,t); p=ease_io((t-ts)/dur)
    return {k:lerp(prev[k],cur[k],p) for k in cur},name,p,pname
def place_footage(src,t):
    L,name,p,pname=layout(t)
    s=L['s']; sw,sh=int(W*s),int(H*s)
    big=src.resize((max(1,sw),max(1,sh)),Image.BICUBIC)
    canvas=BG.copy()
    im=Image.new('RGBA',(W,H),(0,0,0,0)); im.paste(big,(int(round(L['fx'])),int(round(L['fy']))))
    r=int(L['r'])
    if r>0:
        # rounded frame for floating footage + gold edge
        mask=Image.new('L',(W,H),0); md=ImageDraw.Draw(mask)
        fx0,fy0=int(round(L['fx'])),int(round(L['fy'])); fx1,fy1=fx0+sw,fy0+sh
        if name=='pip':
            cx,cy=540,470; rad=int(250*(s/0.60))
            md.ellipse([cx-rad,cy-rad,cx+rad,cy+rad],fill=255)
        else:
            md.rounded_rectangle([fx0,fy0,fx1,fy1],radius=r,fill=255)
        canvas.paste(im,(0,0),Image.composite(im.split()[3],Image.new('L',(W,H),0),mask))
        d=ImageDraw.Draw(canvas,'RGBA')
        if name=='pip':
            d.ellipse([cx-rad,cy-rad,cx+rad,cy+rad],outline=A(VGOLD,0.9),width=4)
            d.ellipse([cx-rad-7,cy-rad-7,cx+rad+7,cy+rad+7],outline=A(VGOLD,0.3),width=2)
        else:
            d.rounded_rectangle([fx0,fy0,fx1,fy1],radius=r,outline=A(VGOLD,0.85),width=3)
            brackets(d,fx0,fy0,fx1,fy1,A(VGOLD,0.9),46,5)
    else:
        canvas.alpha_composite(im)
    return canvas,name,pname,p
def make_bg():
    yy,xx=np.mgrid[0:H,0:W].astype(np.float32)
    base=np.zeros((H,W,3),np.float32)+np.array(NAVY,np.float32)
    g1=np.exp(-(((xx-1000)/520)**2+((yy-170)/520)**2))[...,None]*np.array([58,42,12],np.float32)
    g2=np.exp(-(((xx-60)/560)**2+((yy-1770)/560)**2))[...,None]*np.array([70,6,14],np.float32)
    img=np.clip(base+g1+g2,0,255).astype(np.uint8)
    im=Image.fromarray(img).convert('RGBA'); d=ImageDraw.Draw(im,'RGBA')
    for y in range(22,H,46):
        for x in range(22,W,46): d.point((x,y),fill=(120,124,140,60))
    d.rectangle([0,0,6,H],fill=GOLD)                     # signature gold left rule
    return im
BG=None
# ---------- captions ----------
def build_groups():
    G=[];cur=[]
    for i,x in enumerate(WORDS):
        if cur:
            prev=WORDS[cur[-1]]
            cutb=any(prev['e']-0.05<=c<=x['s']+0.05 for c in CUTS)
            toolong=len(' '.join(WORDS[j]['w'] for j in cur+[i]))>18
            if len(cur)>=3 or x['s']-prev['e']>0.30 or prev['p'] or cutb or toolong: G.append(cur); cur=[]
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
ACCENT={'ANADROL':C_ANA,'OXYMETHOLONE':C_ANA,'SUPERDROL':C_SUP,'METHASTERONE':C_SUP,'ER':RED,'BANNED':RED,'ZERO':RED,'HDL':VGOLD,'F*CK':RED,'KILL':RED}
def cap_y(name,pname,p):
    Y={'full':1210,'win':900,'side':1210,'pip':1330}
    return lerp(Y.get(pname,1210),Y[name],p)
def captions(im,t,cy):
    g=group_at(t)
    if not g: return
    d=ImageDraw.Draw(im,'RGBA')
    ws=[WORDS[i]['w'] for i in g]
    size=108
    while True:
        fn=f(BEB,size); sp=d.textlength(' ',font=fn)+14; wd=[d.textlength(w,font=fn) for w in ws]; tot=sum(wd)+sp*(len(ws)-1)
        if tot<=900 or size<=56: break
        size-=4
    xs=[];x=(W-tot)/2
    for w_ in wd: xs.append(x); x+=w_+sp
    act=0
    for k,i in enumerate(g):
        if WORDS[i]['s']<=t: act=k
    g0=WORDS[g[0]]['s']; s=lerp(0.9,1,expo((t-g0)/0.10))
    CH=230; cap=Image.new('RGBA',(W,CH),(0,0,0,0)); cd=ImageDraw.Draw(cap); shd=Image.new('RGBA',(W,CH),(0,0,0,0)); sd=ImageDraw.Draw(shd)
    prev=max(0,act-1); bt=expo((t-WORDS[g[act]]['s'])/0.07) if act>0 else 1
    bx0=lerp(xs[prev],xs[act],bt)-16; bx1=lerp(xs[prev]+wd[prev],xs[act]+wd[act],bt)+16
    for k,(w_,x_) in enumerate(zip(ws,xs)): sd.text((x_+4,44),w_,font=fn,fill=(0,0,0,220))
    cap.alpha_composite(shd.filter(ImageFilter.GaussianBlur(7)))
    acc=ACCENT.get(ws[act].strip("'S")); boxc=RED if acc in (None,RED) else acc
    lit_bar(cd,bx0,36+size*0.02,bx1,36+size*0.97,boxc)
    for k,(w_,x_) in enumerate(zip(ws,xs)):
        col=CREAM
        if k!=act and ACCENT.get(w_) and WORDS[g[k]]['s']<=t: col=ACCENT[w_]
        if k==act: col=INK if boxc in (VGOLD,CYAN,GREEN) else WHITE
        cd.text((x_,36),w_,font=fn,fill=col,stroke_width=0 if k==act else 3,stroke_fill=(0,0,0))
    if abs(s-1)>0.002:
        cap=cap.resize((int(W*s),int(CH*s)),Image.BICUBIC); ox=int((W-cap.width)/2); oy=int(cy-36-(cap.height-CH)/2)
    else: ox,oy=0,int(cy-36)
    im.alpha_composite(cap,(ox,oy))
# =============== SCENES (raw-time) ===============
def layer():
    lay=Image.new('RGBA',(W,H),(0,0,0,0)); return lay,ImageDraw.Draw(lay,'RGBA')
def panel_head(d,x0,y0,x1,title,right,a):
    d.ellipse([x0+22,y0+20,x0+36,y0+34],fill=A(RED,a if int(T_NOW*4)%2==0 else a/3))
    txt(d,x0+50,y0+12,title,f(MONO,26),WHITE,a)
    if right: txt(d,x1-24-d.textlength(right,font=f(MONO,26)),y0+12,right,f(MONO,26),VGOLD,a)
T_NOW=0.0
LOW=(44,1322,1036,1566)
def lowbox(im,t,t0,t1,title,right,hard_out=False):
    pin=expo((t-t0)/0.22); pout=0 if hard_out else clamp((t-t1)/0.14)
    al=pin*(1-pout)
    if al<=0: return 0,None,None
    x0,y0,x1,y1=LOW; yo=lerp(40,0,pin)
    frosted_a(im,(x0,y0+yo,x1,y1+yo),al,0.82,10,18)
    lay,d=layer()
    d.rounded_rectangle([x0,y0+yo,x1,y1+yo],radius=18,outline=A(VGOLD,0.5*al),width=2)
    brackets(d,x0,y0+yo,x1,y1+yo,A(VGOLD,al),40,6); brackets(GL,x0,y0+yo,x1,y1+yo,A(VGOLD,al),40,12)
    panel_head(d,x0,y0+yo,x1,title,right,al)
    return al,lay,(0,yo)
def flush(im,lay,al):
    if al<0.999: lay.putalpha(lay.split()[3].point(lambda v:int(v*al)))
    im.alpha_composite(lay)

# S1 risk-over-time dual line chart (1.8-9.1, FULL low strip)
def s1(im,t):
    T0,T1=1.80,9.10
    if not (T0<=t<T1+0.2): return
    al,lay,off=lowbox(im,t,T0,T1,'RISK OVER TIME','2 ORALS',hard_out=True)
    if not al: return
    d=ImageDraw.Draw(lay,'RGBA'); _,yo=off
    X0,X1,Y0,Y1=120,980,1388+yo,1528+yo
    a0=ap(t,T0+0.1,0.2)
    d.line([(X0,Y1),(X1,Y1)],fill=A((120,124,140),a0),width=2); d.line([(X0,Y0-6),(X0,Y1)],fill=A((120,124,140),a0),width=2)
    txt(d,X0,Y1+6,'DAYS',f(MONO,20),MUTED,a0); txt(d,X1,Y1+6,'YEARS',f(MONO,20),MUTED,a0,'ra')
    thr=Y0+22
    if t>2.9:
        p=ap(t,2.9,0.3); x=X0
        while x<lerp(X0,X1,p): d.line([(x,thr),(min(x+16,X1),thr)],fill=A(RED,0.7),width=2); x+=28
        txt(d,X1-4,thr-24,'DANGER LINE',f(MONO,18),RED,p,'ra')
    ptsA=[(lerp(X0,X1,i/59),Y1-(Y1-Y0+8)*(1-math.exp(-(i/59)*15))) for i in range(60)]
    if t>2.50:
        glow_line(d,partial(ptsA,expo((t-2.50)/1.3)),RED,6,1,14)
        if t>3.25:
            q=ap(t,3.25); px,py=ptsA[11]; tag(d,px+30,py-8,'ER - FAST',RED,24,q)
    ptsB=[(lerp(X0,X1,i/59),Y1-(Y1-Y0)*0.82*((i/59)**2.4)) for i in range(60)]
    if t>4.96:
        glow_line(d,partial(ptsB,ease_io(clamp((t-4.96)/2.4))),VGOLD,6,1,14)
        if t>7.30:
            q=ap(t,7.30); px,py=ptsB[-1]; tag(d,px-tagw(d,'QUIET - YEARS',24)-8,py+2,'QUIET - YEARS',VGOLD,24,q)
    flush(im,lay,al)

# S2 compound ID cards + 17a core (12.48-18.92, WIN lower third)
def ringpts(cx,cy,r,n,rot): return [(cx+r*math.cos(rot+2*math.pi*i/n),cy+r*math.sin(rot+2*math.pi*i/n)) for i in range(n)]
def card(d,x0,y0,x1,y1,col,kicker,name,chem,ac,an,ach,cp):
    if ac<=0: return
    yo=lerp(30,0,ac)
    d.rounded_rectangle([x0,y0+yo,x1,y1+yo],radius=16,fill=A((8,10,18),0.95*ac),outline=A(col,0.9*ac),width=3)
    if GL: GL.rounded_rectangle([x0,y0+yo,x1,y1+yo],radius=16,outline=A(col,0.8*ac),width=8)
    lit_bar(d,x0+3,y0+yo+3,x1-3,y0+yo+11,col,ac)
    txt(d,x0+24,y0+yo+24,kicker,f(MONO,22),col,ac)
    if an>0: txt(d,x0+22,y0+yo+lerp(54,48,cp),name,f(BEB,lerp(90,62,cp)),WHITE,an)
    if ach>0:
        n=int(len(chem)*clamp(ach*1.4)); txt(d,x0+24,y1+yo-lerp(52,42,cp),chem[:n],f(MONO,24),MUTED,ach)
def s2(im,t):
    T0,T1=12.48,18.92
    if not (T0-0.1<=t<T1+0.25): return
    al=1-clamp((t-T1)/0.18)
    lay,d=layer()
    cp=ease_io((t-17.04)/0.35)
    y0=lerp(1052,1030,cp); y1=lerp(1300,1172,cp)
    card(d,60,y0,522,y1,C_ANA,'COMPOUND A','ANADROL','OXYMETHOLONE',ap(t,12.86,0.2),ap(t,14.12,0.14),ap(t,12.86,0.5),cp)
    card(d,558,y0,1020,y1,C_SUP,'COMPOUND B','SUPERDROL','METHASTERONE',ap(t,15.16,0.2),ap(t,16.40,0.14),ap(t,15.16,0.5),cp)
    if t>14.48:
        q=ap(t,14.48,0.12); cy=(y0+y1)/2
        d.ellipse([540-34,cy-34,540+34,cy+34],fill=A(RED,q)); txt(d,540,cy,'VS',f(BEB,44),WHITE,q,'mm')
        if GL: GL.ellipse([540-38,cy-38,540+38,cy+38],outline=A(RED,q),width=10)
    if t>17.04:
        a=ap(t,17.10,0.25); r=44; cx0,cy0=320,1332
        rings=[ringpts(cx0,cy0,r,6,math.pi/6),ringpts(cx0+r*math.sqrt(3),cy0,r,6,math.pi/6),ringpts(cx0+r*math.sqrt(3)*1.5,cy0-r*1.5,r,6,math.pi/6)]
        pc=(cx0+r*math.sqrt(3)*1.5+r*1.62,cy0-r*1.5-r*0.1); pent=ringpts(pc[0],pc[1],r*0.86,5,math.pi)
        dp=clamp((t-17.10)/0.6)
        for k,rg in enumerate(rings+[pent]):
            p=clamp(dp*4-k)
            if p>0: glow_line(d,partial(rg+[rg[0]],p),CYAN,4,a,10)
        c17=max(pent,key=lambda q:q[0]-q[1]*0.2)
        if t>17.36:
            q=ap(t,17.36,0.12); d.line([c17,(c17[0]+50,c17[1]-44)],fill=A(RED,q),width=5); d.ellipse([c17[0]+42,c17[1]-54,c17[0]+62,c17[1]-34],fill=A(RED,q))
        if t>17.82: tag(d,690,1232,'17a-METHYL',RED,30,ap(t,17.82))
        if t>18.24: tag(d,690,1298,'ALKYLATED',RED,30,ap(t,18.24))
        txt(d,110,1452,'SHARED 17a-ALKYLATED CORE = LIVER STRESS',f(MONO,22),MUTED,a)
    flush(im,lay,al)

# S3 strength ramp -> cycle block (19.0-24.8, SIDE left rail)
def s3(im,t):
    T0,T1=19.0,24.8
    if not (T0<=t<T1): return
    al=1-clamp((t-T1+0.14)/0.14); lay,d=layer()
    X0,X1=48,330; a=ap(t,19.16,0.2)
    txt(d,X0,286,'STRENGTH',f(MONO,26),VGOLD,a); d.line([(X0,324),(X0+282*a,324)],fill=A(VGOLD,a),width=3)
    morph=ease_io((t-22.04)/0.45)
    if morph<1:
        for i in range(10):
            y=356+i*52; tt=19.62+i*0.18; p=expo((t-tt)/0.2)
            if p<=0: continue
            L=(0.2+0.8*((i+1)/10)**0.85)*(X1-X0-50)
            col=VGOLD if i<9 else RED
            lit_bar(d,X0+46,y,X0+46+L*p*(1-morph),y+30,col,1-morph)
        if t>21.55:
            q=ap(t,21.55,0.12)*(1-morph); txt(d,X0,900,'10',f(BEB,160),RED,q); txt(d,X0+128,944,'DAYS',f(BEB,60),WHITE,q)
            if GL: GL.text((X0,900),'10',font=f(BEB,160),fill=A(RED,q*0.7))
    if morph>0:
        txt(d,X0,320,'CYCLE - WEEKS',f(MONO,22),MUTED,morph)
        for i in range(6):
            y=360+i*72
            d.rounded_rectangle([X0,y,X0+230,y+56],radius=12,outline=A(VGOLD,morph),width=3)
            lit_bar(d,X0+4,y+4,X0+226,y+52,VGOLD,0.85*morph)
            txt(d,X0+115,y+28,f'W{i+1}',f(BEB,42),INK,morph,'mm')
        if t>23.7:
            q=ap(t,23.7); txt(d,X0,812,'4-6 WK BLOCK',f(BEB,66),VGOLD,q); txt(d,X0,878,'PEAKING ONLY',f(MONO,24),MUTED,q)
    flush(im,lay,al)

# S4 build vs peak select (25.08-29.5, FULL low strip)
def s4(im,t):
    T0,T1=25.08,29.60
    if not (T0<=t<T1): return
    al,lay,off=lowbox(im,t,T0,T1,'WHAT THEY DO',None)
    if not al: return
    d=ImageDraw.Draw(lay,'RGBA'); _,yo=off
    rows=[('BUILD PHYSIQUE',26.04,False),('PEAKING TOOL',28.08,True)]
    for i,(lab,tt,good) in enumerate(rows):
        y=1372+yo+i*92; p=ap(t,tt,0.18)
        if p<=0: continue
        col=GREEN if good else RED
        d.rounded_rectangle([90,y,990,y+74],radius=12,fill=A((12,16,24),0.9*p),outline=A(col,p),width=3)
        if good and t>28.4:
            q=ap(t,28.4); lit_bar(d,93,y+3,987,y+71,(16,40,24),0.6*q); d.rounded_rectangle([90,y,990,y+74],radius=12,outline=A(GREEN,q),width=4)
            if GL: GL.rounded_rectangle([90,y,990,y+74],radius=12,outline=A(GREEN,q),width=10)
        if good: check(d,120,y+22,GREEN,1.3,p)
        else: cross(d,122,y+22,RED,1.1,p)
        txt(d,196,y+14,lab,f(BEB,56),WHITE if good else (150,150,158),p)
        if not good and t>tt+0.25:
            q=ap(t,tt+0.25); d.line([(196,y+42),(196+d.textlength(lab,font=f(BEB,56))*q,y+42)],fill=A(RED,q),width=4)
    flush(im,lay,al)

# S5 two-column legitimacy compare (29.80-44.6, WIN lower)
def colhead(d,x0,x1,y,col,title,a):
    lit_bar(d,x0,y,x1,y+54,col,a); txt(d,(x0+x1)/2,y+8,title,f(BEB,44),INK,a,'ma')
def s5(im,t):
    T0,T1=29.80,44.60
    if not (T0-0.1<=t<T1+0.2): return
    al=1-clamp((t-T1)/0.18); lay,d=layer()
    LX0,LX1,RX0,RX1=70,528,552,1010; TY=1016
    a0=ap(t,31.90,0.2)
    if a0>0:
        frosted_c=0  # columns are solid cards
        d.rounded_rectangle([LX0,TY,LX1,1540],radius=14,fill=A((8,12,20),0.92*a0),outline=A(C_ANA,0.8*a0),width=2)
        d.rounded_rectangle([RX0,TY,RX1,1540],radius=14,fill=A((8,12,20),0.92*ap(t,37.42,0.2)),outline=A(C_SUP,0.8*ap(t,37.42,0.2)),width=2)
        colhead(d,LX0+6,LX1-6,TY+6,C_ANA,'ANADROL',a0)
        if t>37.42: colhead(d,RX0+6,RX1-6,TY+6,C_SUP,'SUPERDROL',ap(t,37.42,0.2))
    # left rows
    L=[('APPROVED DRUG',33.44,'ok'),('PRESCRIBED',33.92,'ok'),('60 YRS HUMAN DATA',34.46,'num')]
    for i,(lab,tt,kind) in enumerate(L):
        y=TY+78+i*74; p=ap(t,tt,0.16)
        if p<=0: continue
        check(d,LX0+22,y+8,GREEN,1.0,p)
        if kind=='num' and t>34.98:
            cu=int(lerp(0,60,ease_io((t-34.98)/1.3))); txt(d,LX0+64,y-6,str(cu),f(BEB,56),C_ANA,p); txt(d,LX0+64+d.textlength(str(cu),font=f(BEB,56))+8,y+14,'YEARS DATA',f(MONO,20),MUTED,p)
        else: txt(d,LX0+64,y+2,lab,f(BC,38),CREAM,p)
    # right rows
    if t>37.42:
        # gas-station bottle depiction
        bx,by=RX0+180,TY+96; pb=ap(t,38.06,0.3)
        if pb>0:
            d.rounded_rectangle([bx-44,by,bx+44,by+120],radius=14,outline=A(MUTED,pb),width=3)
            d.rectangle([bx-20,by-26,bx+20,by],fill=A(MUTED,pb)); txt(d,bx,by+60,'GNC',f(BEB,40),MUTED,pb,'mm')
            txt(d,RX0+20,by+134,'GAS-STATION SUPP',f(MONO,20),MUTED,pb)
        if t>40.96:
            q=ap(t,40.96,0.14); sx,sy=RX0+40,TY+300
            d.rounded_rectangle([sx,sy,sx+420,sy+70],radius=8,outline=A(RED,q),width=4)
            txt(d,sx+210,sy+34,'BANNED 2012',f(BEB,52),RED,q,'mm')
            if GL: GL.rounded_rectangle([sx,sy,sx+420,sy+70],radius=8,outline=A(RED,q),width=10)
        if t>42.70:
            q=ap(t,42.70,0.14); cross(d,RX0+40,TY+394,RED,1.1,q); txt(d,RX0+86,TY+386,'0 HUMAN TRIALS',f(BC,40),RED,q)
    flush(im,lay,al)

# S6 Superdrol pros chips -> 3wk lab trend (44.6-59.6, FULL low strip)
def s6(im,t):
    T0,T1=44.62,52.30
    if not (T0<=t<T1): return
    al,lay,off=lowbox(im,t,T0,T1,'SUPERDROL - 3 WEEKS',None)
    if not al: return
    d=ImageDraw.Draw(lay,'RGBA'); _,yo=off
    chips=[('DRY',46.26),('HARD',46.96),('NO BLOAT',47.28),('NO GYNO',48.00)]
    morph=ease_io((t-48.98)/0.5)
    if morph<1:
        x=96
        for lab,tt in chips:
            p=ap(t,tt,0.14)
            if p>0:
                x2=tag(d,x,1376+yo,lab,GREEN,34,p*(1-morph))+18; x=x2
    if morph>0:
        # 3-week dual-trend: HDL down, liver enzymes up
        X0,X1,Y0,Y1=120,980,1372+yo,1548+yo
        d.line([(X0,Y1),(X1,Y1)],fill=A((120,124,140),morph),width=2)
        for i,w in enumerate(['WK1','WK2','WK3']): txt(d,lerp(X0,X1,i/2.0),Y1+6,w,f(MONO,20),MUTED,morph,'ma' if i==1 else ('la' if i==0 else 'ra'))
        hdl=[(lerp(X0,X1,i/2.0),lerp(Y0+10,Y1-6,i/2.0)) for i in range(3)]
        liv=[(lerp(X0,X1,i/2.0),lerp(Y1-6,Y0+10,i/2.0)) for i in range(3)]
        dp=clamp((t-49.78)/1.6)
        glow_line(d,partial(hdl,dp),RED,6,morph,14); glow_line(d,partial(liv,dp),AMBER,6,morph,14)
        if dp>0.5:
            tag(d,hdl[-1][0]-tagw(d,'HDL DOWN',22)-6,hdl[-1][1]+2,'HDL DOWN',RED,22,morph)
            tag(d,liv[-1][0]-tagw(d,'LIVER UP',22)-6,liv[-1][1]-40,'LIVER UP',AMBER,22,morph)
    flush(im,lay,al)

# S7 Anadrol dials to red (52.52-59.6, FULL low strip over s6? -> use side-less overlay top)
def gauge(d,cx,cy,r,frac,col,label,a):
    import math as m
    d.arc([cx-r,cy-r,cx+r,cy+r],150,390,fill=A((70,74,90),a),width=8)
    a0=150; a1=150+240*clamp(frac)
    steps=max(2,int((a1-a0)/8))
    pts=[(cx+r*m.cos(m.radians(a0+(a1-a0)*k/steps)),cy+r*m.sin(m.radians(a0+(a1-a0)*k/steps))) for k in range(steps+1)]
    glow_line(d,pts,col,8,a,16)
    ang=m.radians(a1); d.line([(cx,cy),(cx+r*0.8*m.cos(ang),cy+r*0.8*m.sin(ang))],fill=A(WHITE,a),width=4)
    d.ellipse([cx-7,cy-7,cx+7,cy+7],fill=A(WHITE,a))
    txt(d,cx,cy+r+14,label,f(MONO,22),CREAM,a,'ma')
def s7(im,t):
    T0,T1=52.52,59.60
    if not (T0<=t<T1): return
    al=1-clamp((t-T1)/0.16); lay,d=layer()
    hp=ap(t,52.70,0.25)
    txt(d,540,1356,'ANADROL - WATER SIDE',f(MONO,26),VGOLD,hp,'ma'); d.line([(360,1398),(720,1398)],fill=A(VGOLD,hp*0.5),width=2)
    gs=[('WATER',54.60,0.74),('HEMATOCRIT',57.92,0.9),('BLOOD PRESSURE',58.52,0.86)]
    cxs=[196,540,884]
    for (lab,tt,fr),cx in zip(gs,cxs):
        p=ap(t,tt,0.2)
        if p<=0: continue
        fr_now=fr*ease_io(clamp((t-tt)/0.7))
        col=RED if fr_now>0.66 else AMBER
        gauge(d,cx,1520,86,fr_now,col,lab,p)
        if fr_now>0.66: tag(d,cx-tagw(d,'HIGH',20)/2,1664,'HIGH',RED,20,ap(t,tt+0.5))
    flush(im,lay,al)

# S8 decision tree (59.6-72.9, PIP) left+right branches around circle
def s8(im,t):
    T0,T1=59.60,72.90
    if not (T0<=t<T1): return
    al=1-clamp((t-T1)/0.16); lay,d=layer()
    a=ap(t,59.80,0.25)
    txt(d,540,250,'WHICH ONE FOR YOU',f(BC,40),VGOLD,a,'ma')
    # branch A (left): meet -> Anadrol
    if t>60.1:
        p=ap(t,60.1,0.3)
        glow_line(d,partial([(290,470),(150,560),(150,700)],p),C_ANA,4,p,9)
    rows_A=[('PEAKING FOR A MEET',60.96),('STAY FULL',62.56),('HCT HAS ROOM',63.50)]
    for i,(lab,tt) in enumerate(rows_A):
        y=720+i*86; p=ap(t,tt,0.16)
        if p<=0: continue
        d.rounded_rectangle([40,y,470,y+70],radius=12,fill=A((8,12,20),0.92*p),outline=A(C_ANA,p),width=2)
        check(d,64,y+22,GREEN,0.95,p); txt(d,110,y+16,lab,f(BC,34),CREAM,p)
    if t>65.0:
        q=ap(t,65.0,0.14); y=720+3*86+6
        d.rounded_rectangle([40,y,470,y+86],radius=12,fill=A((10,24,30),0.95*q),outline=A(C_ANA,q),width=3)
        txt(d,255,y+26,'ANADROL',f(BEB,64),C_ANA,q,'ma')
        if GL: GL.rounded_rectangle([40,y,470,y+86],radius=12,outline=A(C_ANA,q),width=10)
    # branch B (right): beach recomp -> Superdrol
    if t>66.56:
        p=ap(t,66.56,0.3); glow_line(d,partial([(790,470),(930,560),(930,700)],p),C_SUP,4,p,9)
    rows_B=[('BEACH RECOMP',67.22),('STAY DRY',68.40),('LABS CLEAN',69.24)]
    for i,(lab,tt) in enumerate(rows_B):
        y=720+i*86; p=ap(t,tt,0.16)
        if p<=0: continue
        d.rounded_rectangle([610,y,1040,y+70],radius=12,fill=A((8,12,20),0.92*p),outline=A(C_SUP,p),width=2)
        check(d,634,y+22,GREEN,0.95,p); txt(d,680,y+16,lab,f(BC,34),CREAM,p)
    if t>71.02:
        q=ap(t,71.02,0.14); y=720+3*86+6
        d.rounded_rectangle([610,y,1040,y+86],radius=12,fill=A((26,22,6),0.95*q),outline=A(C_SUP,q),width=3)
        txt(d,825,y+26,'SUPERDROL',f(BEB,58),C_SUP,q,'ma')
        if GL: GL.rounded_rectangle([610,y,1040,y+86],radius=12,outline=A(C_SUP,q),width=10)
    flush(im,lay,al)

# S9 bloodwork AVOID BOTH (72.9-77.9, FULL low strip) ILLUSTRATIVE lab
def s9(im,t):
    T0,T1=72.92,77.95
    if not (T0<=t<T1): return
    al,lay,off=lowbox(im,t,T0,T1,'BASELINE BLOODWORK','ILLUSTRATIVE')
    if not al: return
    d=ImageDraw.Draw(lay,'RGBA'); _,yo=off
    rows=[('HEMATOCRIT','54 %','H',73.74),('HDL','28 mg/dL','L',74.08),('ALT','71 U/L','H',74.38)]
    y=1372+yo
    for lab,val,fl,tt in rows:
        p=ap(t,tt,0.14)
        if p<=0: continue
        txt(d,96,y,lab,f(BC,34),CREAM,p); txt(d,520,y,val,f(DMB,34),WHITE,p)
        tag(d,900,y-4,'FLAG '+fl,RED,24,p)
        d.line([(96,y+44),(96+840*p,y+44)],fill=A((60,64,80),p),width=1)
        y+=58
    if t>75.54:
        q=ap(t,75.54,0.14); x0=90; x1=lerp(90,990,expo((t-75.54)/0.3))
        lit_bar(d,x0,1548+yo,x1,1548+yo+46,RED,q)
        if x1>400: txt(d,540,1548+yo+22,'AVOID BOTH',f(BEB,48),WHITE,q,'mm')
        if GL: GL.rectangle([x0,1548+yo,x1,1548+yo+46],outline=A(RED,q),width=10)
    flush(im,lay,al)

# S10 acute-risk scale slam (77.98-86.4, FULL low strip)
def s10(im,t):
    T0,T1=77.98,86.40
    if not (T0<=t<T1): return
    al,lay,off=lowbox(im,t,T0,T1,'ACUTE RISK',None)
    if not al: return
    d=ImageDraw.Draw(lay,'RGBA'); _,yo=off
    X0,X1,Y=120,980,1440+yo
    a=ap(t,78.0,0.2)
    # gradient scale green->red
    for i in range(X0,X1):
        k=(i-X0)/(X1-X0); c=(int(lerp(40,255,k)),int(lerp(200,34,k)),int(lerp(90,28,k)))
        d.line([(i,Y),(i,Y+28)],fill=A(c,a))
    txt(d,X0,Y+36,'SAFER',f(MONO,20),MUTED,a); txt(d,X1,Y+36,'COULD KILL YOU',f(MONO,20),RED,a,'ra')
    if t>80.72:
        p=ease_io(clamp((t-80.72)/0.7)); x=lerp(X0+60,X1-40,p)
        d.polygon([(x,Y-18),(x-16,Y-44),(x+16,Y-44)],fill=A(VGOLD,1)); txt(d,x,Y-64,'SUPERDROL',f(BC,30),C_SUP,ap(t,81.08),'ma')
        if GL: GL.polygon([(x,Y-18),(x-16,Y-44),(x+16,Y-44)],fill=A(VGOLD,0.8))
    if t>84.82:
        q=ap(t,84.82); txt(d,540,1512+yo,'BETTER = DEPENDS ON THE JOB',f(BC,36),CREAM,q,'ma')
    flush(im,lay,al)

# S11 CTA end card (86.4-end) logo + COMMENT "HDL"
_LOGO=None
def s11(im,t):
    T0=86.40
    if t<T0: return
    global _LOGO
    a=ap(t,86.60,0.4)
    # frosted lower card keeps the face clear
    card_box=(70,980,1010,1560)
    frosted_a(im,card_box,a,0.84,12,26)
    lay,d=layer()
    x0,y0,x1,y1=card_box
    d.rounded_rectangle([x0,y0,x1,y1],radius=26,outline=A(GOLD,0.6*a),width=2)
    brackets(d,x0,y0,x1,y1,A(VGOLD,a),46,6); brackets(GL,x0,y0,x1,y1,A(VGOLD,a),46,12)
    if _LOGO is None and os.path.exists(LOGO_P):
        lg=Image.open(LOGO_P).convert('RGBA').resize((150,150),Image.LANCZOS)
        m=Image.new('L',(150,150),0); ImageDraw.Draw(m).ellipse([0,0,149,149],fill=255); lg.putalpha(m); _LOGO=lg
    if _LOGO is not None:
        tmp=_LOGO.copy(); tmp.putalpha(tmp.split()[3].point(lambda v:int(v*a))); lay.alpha_composite(tmp,(465,1012))
        d.ellipse([465,1012,615,1162],outline=A(GOLD,a),width=3)
    txt(d,540,1186,'FREE',f(MONO,24),VGOLD,a,'ma')
    txt(d,540,1218,'FULL PROTOCOL + FRAMEWORK',f(BC,46),CREAM,a,'ma')
    txt(d,540,1274,'HOW TO RUN BOTH SAFELY',f(MONO,24),MUTED,a,'ma')
    if t>92.34:
        q=ap(t,92.34,0.18); label='COMMENT  "HDL"'; fn=f(BEB,84); tw=d.textlength(label,font=fn)
        x=540-tw/2-26; y=1346
        lit_bar(d,x,y,x+tw+52,y+108,VGOLD,q); d.text((x+26,y+10),label,font=fn,fill=A(INK,q))
        if GL: GL.rectangle([x-6,y-6,x+tw+58,y+114],outline=A(VGOLD,q),width=12)
    txt(d,540,1494,'@coach.agz',f(MONO,28),GOLD,a,'ma')
    flush(im,lay,1.0)

SCENES=[s1,s2,s3,s4,s5,s6,s7,s8,s9,s10,s11]
# ---------- persistent overlays ----------
def disclaimer(im):
    d=ImageDraw.Draw(im,'RGBA'); txt(d,40,1876,'FOR RESEARCH & EDUCATIONAL PURPOSES ONLY',f(MONO,19),(150,150,158),0.8)
def watermark(im):
    d=ImageDraw.Draw(im,'RGBA'); txt(d,1040,1876,'@COACH.AGZ',f(MONO,20),GOLD,0.85,'ra')
def topic_band(im,t):
    # returns after hook per engine note; here no frame-0 text hook (user request). Small topic band 0-11.5 then clears.
    tn=old_to_new_cache(t)
    pass
def old_to_new(to):
    acc=0
    for a,b in KEEP:
        if to<b: return acc+max(0,to-a)
        acc+=b-a
    return acc
def old_to_new_cache(t): return old_to_new(t)
# ---------- frame ----------
def frame(src,t):
    global GL,BG,T_NOW
    T_NOW=t
    if BG is None: BG=make_bg()
    base,name,pname,p=place_footage(src,t)
    im=base
    glow=Image.new('RGBA',(W,H),(0,0,0,0)); GL=ImageDraw.Draw(glow,'RGBA')
    for sc in SCENES: sc(im,t)
    GL=None
    if glow.getbbox():
        sm=glow.resize((W//4,H//4),Image.BILINEAR)
        g1=np.asarray(sm.filter(ImageFilter.GaussianBlur(3.5))).astype(np.float32)/255
        g2=np.asarray(sm.filter(ImageFilter.GaussianBlur(10))).astype(np.float32)/255
        prem=np.clip(g1[...,:3]*g1[...,3:]*2.3+g2[...,:3]*g2[...,3:]*1.8,0,1)
        prem=np.asarray(Image.fromarray((prem*255).astype(np.uint8)).resize((W,H),Image.BILINEAR)).astype(np.float32)/255
        b=np.asarray(im.convert('RGB')).astype(np.float32)/255
        im=Image.fromarray(((1-(1-b)*(1-prem))*255).astype(np.uint8)).convert('RGBA')
    disclaimer(im); watermark(im)
    if t<86.55:                      # CTA card carries the closing message; no caption collision
        captions(im,t,cap_y(name,pname,p))
    return im.convert('RGB')
# ---------- drivers ----------
if __name__=='__main__':
    mode=sys.argv[2]
    QC=HERE+'/qc'; os.makedirs(QC,exist_ok=True)
    if mode=='stills':
        for tt in [float(x) for x in sys.argv[3:]]:
            subprocess.run(['ffmpeg','-v','error','-y','-ss',f'{tt:.4f}','-i',SRC,'-frames:v','1',QC+'/_s.png'],check=True)
            frame(Image.open(QC+'/_s.png').convert('RGB'),tt).resize((405,720)).save(QC+f'/st_{tt:.2f}.jpg',quality=86)
        print('stills done')
    else:
        n0,n1,out=int(sys.argv[3]),int(sys.argv[4]),sys.argv[5]
        olds=[round(new_to_old(n/FPS)*FPS) for n in range(n0,n1)]
        first,last=olds[0],olds[-1]
        dec=subprocess.Popen(['ffmpeg','-v','error','-i',SRC,'-vf',f'select=between(n\\,{first}\\,{last})','-vsync','0','-f','rawvideo','-pix_fmt','rgb24','-'],stdout=subprocess.PIPE)
        enc=subprocess.Popen(['ffmpeg','-v','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-','-an','-c:v','libx264','-crf','19','-preset','medium','-pix_fmt','yuv420p',out],stdin=subprocess.PIPE)
        cur=first-1; buf=None
        for n,o in zip(range(n0,n1),olds):
            while cur<o:
                buf=dec.stdout.read(W*H*3); cur+=1
                if len(buf)<W*H*3: raise SystemExit(f'short read {cur}')
            enc.stdin.write(frame(Image.frombuffer('RGB',(W,H),buf),o/FPS).tobytes())
        enc.stdin.close(); enc.wait(); dec.kill(); print('done',n0,n1)
