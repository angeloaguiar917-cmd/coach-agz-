# Full test 02 — "Realistic muscle gain" (1080x1920, 30 fps)
# usage: python3 render.py <scratch> stills t1 t2 ...   |   python3 render.py <scratch> chunk n0 n1 out.mp4
import json, subprocess, sys, math, random
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
S=sys.argv[1]; F=S+'/fonts/'; T=S+'/cut/'; HERE=__file__.rsplit('/',1)[0]+'/'
W,H=1080,1920; FPS=30
WORDS_RAW=json.load(open(HERE+'words_cut.json'))
CUTS=[8.9,32.2,55.933,56.467,79.4,95.167,97.667,102.0,103.833,105.6,111.267]
DUR=3440/FPS
GOLD=(201,169,110); CREAM=(244,241,234); NAVY=(14,17,23)
RED=(255,34,28); VGOLD=(255,194,26); CYAN=(0,229,255); GREEN=(30,255,110); DEEP=(2,3,8); INK=(6,8,14); WHITE=(255,255,255)
GREY=(110,114,128); DIM=(52,56,70)
MONO='JBMono-500.ttf'; MONOB='JBMono-700.ttf'; BEB='BebasNeue.ttf'; DMB='DMSans-700.ttf'; DMR='DMSans-400.ttf'; BAR='Barlow-800.ttf'; BAR7='Barlow-700.ttf'
_fc={}
def f(n,s):
    k=(n,int(s))
    if k not in _fc: _fc[k]=ImageFont.truetype(F+n,int(s))
    return _fc[k]
def clamp(x,a=0,b=1): return max(a,min(b,x))
def expo(x): x=clamp(x); return 1 if x>=1 else 1-2**(-10*x)
def ease_io(x): x=clamp(x); return 4*x**3 if x<.5 else 1-(-2*x+2)**3/2
def back(x): x=clamp(x); c=1.4; return 1+(c+1)*(x-1)**3+c*(x-1)**2
def lerp(a,b,t): return a+(b-a)*t
def A(c,a): return tuple(c[:3])+(int(clamp(a)*255),)
def ap(t,t0,dur=0.16): return expo((t-t0)/dur)
GL=None
# ---------------- primitives ----------------
def txt(d,x,y,s,font,col,a=1.0,anchor=None): d.text((x,y),s,font=font,fill=A(col,a),anchor=anchor)
def brackets(d,x0,y0,x1,y1,col,L=34,w=4):
    for (cx,cy,sx,sy) in [(x0,y0,1,1),(x1,y0,-1,1),(x0,y1,1,-1),(x1,y1,-1,-1)]:
        d.line([(cx,cy),(cx+sx*L,cy)],fill=col,width=w); d.line([(cx,cy),(cx,cy+sy*L)],fill=col,width=w)
def lit_bar(d,x0,y0,x1,y1,col,a=1.0):
    if x1<x0: x0,x1=x1,x0
    h=max(1,int(y1-y0))
    for i in range(h):
        k=i/h; c=tuple(int(min(255,v*(1.18-0.36*k)+(40 if k<0.12 else 0))) for v in col)
        d.line([(x0,y0+i),(x1,y0+i)],fill=c+(int(255*a),))
def lit_vbar(d,x0,y0,x1,y1,col,a=1.0):  # vertical bar lit from the left edge
    if y1<y0: y0,y1=y1,y0
    w=max(1,int(x1-x0))
    for i in range(w):
        k=i/w; c=tuple(int(min(255,v*(1.15-0.4*k)+(40 if k<0.1 else 0))) for v in col)
        d.line([(x0+i,y0),(x0+i,y1)],fill=c+(int(255*a),))
def tag(d,x,y,label,col=RED,size=32,a=1.0,glow=True,anchor='l'):
    if a<=0: return x
    fn=f(MONO,size); tw=d.textlength(label,font=fn); h=size+16
    if anchor=='r': x=x-tw-24
    if anchor=='c': x=x-(tw+24)/2
    lit_bar(d,x,y,x+tw+24,y+h,col,a); d.text((x+12,y+5),label,font=fn,fill=A(INK if col in (VGOLD,GREEN,CYAN) else WHITE,a))
    if GL and glow: GL.rectangle([x-4,y-4,x+tw+28,y+h+4],outline=A(col,a),width=8)
    return x+tw+24
def check(d,x,y,col,s=1.0,a=1.0):
    pts=[(x,y+16*s),(x+10*s,y+28*s),(x+30*s,y+2*s)]
    d.line(pts,fill=A(col,a),width=int(6*s))
    if GL: GL.line(pts,fill=A(col,a),width=int(12*s))
def cross(d,x,y,col,s=1.0,a=1.0):
    for p in [[(x,y),(x+28*s,y+28*s)],[(x+28*s,y),(x,y+28*s)]]:
        d.line(p,fill=A(col,a),width=int(6*s))
        if GL: GL.line(p,fill=A(col,a),width=int(12*s))
def arrow(d,x0,y0,x1,y1,col,w=5,a=1.0):
    d.line([(x0,y0),(x1,y1)],fill=A(col,a),width=w)
    ang=math.atan2(y1-y0,x1-x0); L=18
    d.polygon([(x1,y1),(x1-L*math.cos(ang-0.45),y1-L*math.sin(ang-0.45)),(x1-L*math.cos(ang+0.45),y1-L*math.sin(ang+0.45))],fill=A(col,a))
def dashed(d,pts,col,w=3,dash=16,gap=12,a=1.0):
    for (x0,y0),(x1,y1) in zip(pts,pts[1:]):
        L=math.hypot(x1-x0,y1-y0); k=0
        while k<L:
            e=min(L,k+dash); d.line([(lerp(x0,x1,k/L),lerp(y0,y1,k/L)),(lerp(x0,x1,e/L),lerp(y0,y1,e/L))],fill=A(col,a),width=w); k+=dash+gap
def frosted(im,box,dark=0.86,blur=10,radius=0):
    x0,y0,x1,y1=[int(v) for v in box]; x0=max(0,x0); y0=max(0,y0); x1=min(W,x1); y1=min(H,y1)
    if x1<=x0 or y1<=y0: return
    reg=im.crop((x0,y0,x1,y1)).convert('RGB').filter(ImageFilter.GaussianBlur(blur))
    reg=Image.blend(reg,Image.new('RGB',reg.size,DEEP),dark).convert('RGBA')
    if radius:
        m=Image.new('L',reg.size,0); ImageDraw.Draw(m).rounded_rectangle([0,0,reg.width-1,reg.height-1],radius=radius,fill=255); im.paste(reg,(x0,y0),m)
    else: im.paste(reg,(x0,y0))
def panel_frame(d,x0,y0,x1,y1,al,left,right,col=VGOLD,t=0):
    d.rectangle([x0,y0,x1,y1],outline=A(col,0.8*al),width=3); brackets(d,x0,y0,x1,y1,A(col,al),48,7)
    if GL: GL.rectangle([x0,y0,x1,y1],outline=A(col,0.5*al),width=6); brackets(GL,x0,y0,x1,y1,A(col,al),48,14)
    d.ellipse([x0+26,y0+26,x0+42,y0+42],fill=A(RED,al if int(t*4)%2==0 else al/3))
    txt(d,x0+56,y0+18,left,f(MONO,28),WHITE,al); fr=f(MONO,28); tw=d.textlength(right,font=fr); txt(d,x1-30-tw,y0+18,right,fr,col,al)
def stamp(im,cx,cy,label,col,t,t0,size=96,rot=-8):
    p=clamp((t-t0)/0.12)
    if p<=0: return
    s=lerp(1.6,1.0,expo(p)); fn=f(BEB,size); tmp=Image.new('RGBA',(900,260),(0,0,0,0)); d=ImageDraw.Draw(tmp)
    tw=d.textlength(label,font=fn); x0=450-tw/2-30; x1=450+tw/2+30
    d.rectangle([x0,130-size*0.62,x1,130+size*0.62],outline=A(col,p),width=8)
    d.text((450,130),label,font=fn,fill=A(col,p),anchor='mm')
    tmp=tmp.rotate(rot,resample=Image.BICUBIC).resize((int(900*s),int(260*s)),Image.BICUBIC)
    im.alpha_composite(tmp,(int(cx-tmp.width/2),int(cy-tmp.height/2)))
    if GL: GL.rectangle([cx-tw/2-34,cy-size*0.66,cx+tw/2+34,cy+size*0.66],outline=A(col,p),width=10)
def count(a,b,t,t0,dur=0.45):
    return lerp(a,b,expo((t-t0)/dur))

# ---------------- WORDS / captions ----------------
def clean_words():
    out=[]; skip=set()
    for i,w in enumerate(WORDS_RAW):
        if i in skip: continue
        s=w['w']; x=dict(w)
        if s=='%' and out: out[-1]['w']+='%'; out[-1]['e']=w['e']; continue
        if s.startswith('-') and out: out[-1]['w']+=s; out[-1]['e']=w['e']; continue
        if s=="It's" and abs(w['s']-87.10)<0.05: continue        # unclear lead-in before "stop", dropped from captions
        if s=='to' and abs(w['s']-87.28)<0.05: continue
        if s=='stop' and abs(w['s']-87.56)<0.05: x['s']=87.20
        if s=='were': x['w']="we're"
        if s=='and' and abs(w['s']-26.26)<0.05: x['w']='and'
        out.append(x)
    # spread zero/overlapping onsets
    for i in range(1,len(out)):
        if out[i]['s']<=out[i-1]['s']+0.06: out[i]['s']=out[i-1]['s']+0.08
    return out
WORDS=clean_words()
def build_groups():
    G=[];cur=[]
    for i,x in enumerate(WORDS):
        if cur:
            prev=WORDS[cur[-1]]
            if len(cur)>=3 or x['s']-prev['e']>0.28 or prev['w'][-1] in '.,?!' or any(prev['s']<c<=x['s']+0.02 for c in CUTS): G.append(cur); cur=[]
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
CAP_Y=1335
def cap_word(s):
    s=s.upper().strip(',.?!')
    return s.replace('FUCKING','F*CKING').replace('FUCK','F*CK')
EMPH={'MUSCLE':VGOLD,'GROWTH':VGOLD,'KEEPING':VGOLD,'REALISTIC':VGOLD,'SUBOPTIMAL':RED,'LINEAR':RED,'RISK':RED,'DIE':RED,'DISPOSABLE':RED,'FREAK':RED,'MUTANT':RED}
def captions(im,t):
    g=group_at(t)
    if not g: return
    d=ImageDraw.Draw(im,'RGBA')
    ws=[cap_word(WORDS[i]['w']) for i in g]
    size=122
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
    for k,(w_,x_) in enumerate(zip(ws,xs)): sd.text((x_+4,46),w_,font=fn,fill=(0,0,0,220))
    cap.alpha_composite(shd.filter(ImageFilter.GaussianBlur(6)))
    acol=EMPH.get(ws[act].strip("'"),RED)
    lit_bar(cd,bx0,40+size*0.02,bx1,40+size*0.98,acol)
    for k,(w_,x_) in enumerate(zip(ws,xs)):
        c=INK if (k==act and acol in (VGOLD,)) else CREAM
        cd.text((x_,40),w_,font=fn,fill=c,stroke_width=0 if k==act else 3,stroke_fill=(0,0,0))
    if abs(s-1)>0.002:
        cap=cap.resize((int(W*s),int(300*s)),Image.BICUBIC); ox=int((W-cap.width)/2); oy=int(CAP_Y-40-(cap.height-300)/2)
    else: ox,oy=0,CAP_Y-40
    im.alpha_composite(cap,(ox,oy))

# ---------------- LAYOUT timeline ----------------
# modes: push (full panel), split (footage top / graphic bottom), pip (footage window), scope (grid, no frame)
LAYOUTS=[(12.00,26.22,'push'),(26.26,40.10,'split'),(41.30,57.30,'push'),(66.38,70.20,'scope'),
         (82.20,86.98,'push'),(87.00,95.08,'pip'),(101.80,108.62,'push'),(108.70,DUR+1,'cta')]
def layout_at(t):
    for t0,t1,m in LAYOUTS:
        if t0-0.02<=t<t1+0.3:
            g=min(ease_io((t-t0+0.05)/0.30),1-ease_io((t-t1)/0.25)); return m,clamp(g),t0,t1
    return None,0,0,0
SPLIT_Y=850
PIP=(668,250,1016,869)   # 348x619 window (9:16)
def seg_index(t): return sum(1 for c in CUTS if c<=t+1e-6)
PUNCH=[(62.74,63.9),(102.40,103.80)]   # key-line punch-ins: "suboptimal", "die in 10 years"
def footage(src,t):
    z=1.0 if seg_index(t)%2==0 else 1.08
    for a,b in PUNCH:
        if a<=t<b: z=max(z,1.0)+0.10*expo((t-a)/0.12)
    if z!=1.0:
        big=src.resize((int(W*z),int(H*z)),Image.BICUBIC); ox=(big.width-W)//2; oy=int((big.height-H)*0.4); src=big.crop((ox,oy,ox+W,oy+H))
    return src
def bg_grid(t,col=(18,24,40)):
    im=Image.new('RGB',(W,H),(5,8,16)); d=ImageDraw.Draw(im)
    for x in range(0,W,60): d.line([(x,0),(x,H)],fill=col,width=1)
    for y in range(0,H,60): d.line([(0,y),(W,y)],fill=col,width=1)
    return im
_BGG=None

# ---------------- SCENES ----------------
# 1. side rail: lean-mass readout (2.3-5.7) expands into the starting-conditions spec sheet (5.78-12.0)
def side_rail(im,t):
    if not (2.30<=t<12.2): return
    pin=expo((t-2.30)/0.18); pout=clamp((t-11.95)/0.2)
    grow=ease_io((t-5.70)/0.35)
    x0,y0,x1=720,560,1030; y1=lerp(760,1150,grow)
    dx=lerp(60,0,pin)+380*pout**2; x0+=dx; x1+=dx; a=pin*(1-pout)
    frosted(im,(x0,y0,x1,y1),0.84,14,16)
    d=ImageDraw.Draw(im,'RGBA')
    d.rounded_rectangle([x0,y0,x1,y1],radius=16,outline=A(VGOLD,0.6*a),width=3); brackets(d,x0,y0,x1,y1,A(VGOLD,a),26,5)
    if GL: brackets(GL,x0,y0,x1,y1,A(VGOLD,a),26,10)
    txt(d,x0+22,y0+18,'LEAN MASS Δ',f(MONO,24),VGOLD,a)
    # rolling digits: fast, then slow, then lock on ??
    if t<5.1:
        rng=random.Random(int(t*FPS*(1 if t<4.4 else 0.4))); val=f'+{rng.randint(3,40):02d}'
    else: val='+??'
    txt(d,x0+22,y0+52,val,f(BEB,118),WHITE,a); txt(d,x0+200,y0+128,'LB',f(MONO,30),VGOLD,a)
    if GL and t<5.1: GL.text((x0+22,y0+52),val,font=f(BEB,118),fill=A(VGOLD,0.35*a))
    if grow>0:
        b=a*grow; yy=y0+214
        d.line([(x0+20,yy),(x1-20,yy)],fill=A(GREY,b),width=2)
        txt(d,x0+22,yy+14,'ASSUMPTIONS',f(MONO,24),CYAN,b)
        rows=[('START','UNTRAINED',7.54),('GENETICS','AVERAGE',9.18),('ADHERENCE','LOCKED IN',11.06)]
        for i,(k,v,tt) in enumerate(rows):
            ra=b*ap(t,tt,0.12); y=yy+60+i*104
            if ra<=0: continue
            txt(d,x0+22,y,k,f(MONO,22),GREY,ra); txt(d,x0+22,y+28,v,f(BAR,46),WHITE,ra); check(d,x1-62,y+30,GREEN,1.0,ra)

# 2. range-bar chart (push) 12.0-26.2
CH=dict(x0=170,x1=960,y0=600,y1=1160,vmax=40)
def vy(v): return lerp(CH['y1'],CH['y0'],v/CH['vmax'])
BARS=[('3 MO',12.54,3,8,14.12,14.58,300),('6 MO',17.30,5,12,19.24,19.74,500),('1 YR',22.20,10,20,23.64,24.04,700)]
def axes(d,a,ticks=(0,10,20,30,40)):
    x0,x1,y0,y1=CH['x0'],CH['x1'],CH['y0'],CH['y1']
    for v in ticks:
        y=vy(v); d.line([(x0,y),(x1,y)],fill=A((40,44,60) if v else (110,114,128),a),width=2 if v==0 else 1)
        fn=f(MONO,24); tw=d.textlength(str(v),font=fn); txt(d,x0-18-tw,y-14,str(v),fn,GREY,a)
    txt(d,x0-80,y0-60,'LB',f(MONO,24),VGOLD,a)
def range_bar(d,cx,lo,hi,t,tlo,thi,col,label,tl,w=120,a=1.0,showlabel=True):
    la=ap(t,tl)
    if la>0 and showlabel:
        fn=f(BEB,48); tw=d.textlength(label,font=fn); txt(d,cx-tw/2,CH['y1']+14,label,fn,WHITE,la*a)
    if t<tlo: return None
    l=lerp(0,lo,expo((t-tlo)/0.3)); h=lerp(l,hi,expo((t-thi)/0.45)) if t>=thi else l+0.6
    yl=vy(l); yh=vy(h)
    lit_vbar(d,cx-w/2,yh,cx+w/2,yl,col,a)
    if GL: GL.rectangle([cx-w/2,yh,cx+w/2,yl],outline=A(col,0.7*a),width=6)
    d.line([(cx-w/2-10,yl),(cx+w/2+10,yl)],fill=A(WHITE,a),width=3); d.line([(cx-w/2-10,yh),(cx+w/2+10,yh)],fill=A(WHITE,a),width=3)
    if t>=thi:
        b=ap(t,thi+0.25,0.2); s=f'{int(round(count(lo,hi,t,thi,0.45)))}'
        lab=f'{lo}–{s}'; fn=f(BEB,64); tw=d.textlength(lab,font=fn); txt(d,cx-tw/2,yh-74,lab,fn,col,a)
    return (cx,(yl+yh)/2)
def scene_bars(d,t,im):
    a=1
    axes(d,a)
    mids=[]
    for lab,tl,lo,hi,tlo,thi,cx in BARS:
        m=range_bar(d,cx,lo,hi,t,tlo,thi,VGOLD if lab!='1 YR' else VGOLD,lab,tl)
        if m and t>=thi+0.3: mids.append(m)
    # placeholder 5-year slot
    if t>=22.4:
        b=ap(t,22.4,0.3)*0.8; dashed(d,[(830,vy(0)),(830,vy(40)),(930,vy(40)),(930,vy(0))],GREY,2,10,10,b)
        txt(d,880,vy(20)-30,'?',f(BEB,80),GREY,b,anchor='mt'); txt(d,880,CH['y1']+14,'5 YR',f(BEB,48),GREY,b,anchor='mt')
    for p,q in zip(mids,mids[1:]): dashed(d,[p,q],WHITE,3,10,8,0.8)
    for m in mids: d.ellipse([m[0]-9,m[1]-9,m[0]+9,m[1]+9],fill=A(WHITE,1))
    if t>=15.58: tag(d,180,1222,'LEAN TISSUE ONLY',CYAN,28,ap(t,15.58))
    if t>=24.78: tag(d,560,1222,'CUMULATIVE',VGOLD,28,ap(t,24.78))

# 3. split screen 26.26-40.1: inputs stack + 5-year growth curve
def scene_split(d,t,im,g):
    oy=lerp(400,0,g); y0=SPLIT_Y+oy
    a=g
    txt(d,64,y0+24,'5 YEARS · LOCKED IN',f(MONO,30),VGOLD,a*ap(t,26.48))
    # year pips
    for i in range(5):
        pa=a*ap(t,26.48+i*0.16,0.1); x=64+i*74; y=y0+70
        d.rectangle([x,y,x+62,y+40],outline=A(VGOLD,pa),width=2)
        if pa>0.5: lit_bar(d,x+3,y+3,x+59,y+37,VGOLD,pa)
        txt(d,x+31,y+8,f'Y{i+1}',f(MONOB,22),INK,pa,anchor='mt')
    # input stack (bottom-up)
    inputs=[('TRAINING',30.90,CYAN),('NUTRITION',31.50,CYAN),('PROTOCOLS',32.58,VGOLD),('SIDE-FX MITIGATION',33.56,GREEN)]
    base=y0+430
    for i,(nm,tt,col) in enumerate(inputs):
        p=expo((t-tt)/0.22)
        if p<=0: continue
        yb=base-i*76; ytop=yb-66; drop=(1-p)*-120
        x0,x1=64,470
        d.rectangle([x0,ytop+drop,x1,yb+drop],fill=A((10,14,24),a*p),outline=A(col,a*p),width=3)
        lit_vbar(d,x0,ytop+drop,x0+10,yb+drop,col,a*p)
        txt(d,x0+26,ytop+10+drop,nm,f(BAR,44),WHITE,a*p)
        if GL: GL.rectangle([x0,ytop+drop,x1,yb+drop],outline=A(col,0.6*a*p),width=6)
    if t>=34.4:
        p=ap(t,34.4,0.3); arrow(d,480,base-150,lerp(480,540,p),base-150,VGOLD,6,a*p)
    # growth curve (right) — x is linear in time 0..5 years
    gx0,gx1,gy0,gy1=600,1010,y0+120,y0+420
    def X(yr): return lerp(gx0,gx1,yr/5)
    def Y(v): return lerp(gy1,gy0,v/40)
    txt(d,gx0-40,y0+24,'CUMULATIVE LB',f(MONO,30),CREAM,a)
    d.line([(gx0,gy1),(gx1,gy1)],fill=A(GREY,a),width=2); d.line([(gx0,gy0),(gx0,gy1)],fill=A(GREY,a),width=2)
    for v in (10,20,30,40): d.line([(gx0,Y(v)),(gx1,Y(v))],fill=A((34,38,52),a),width=1); txt(d,gx0-10,Y(v)-14,str(v),f(MONO,24),GREY,a,anchor='rt')
    for yr in (1,2,3,4,5): txt(d,X(yr),gy1+8,f'{yr}Y',f(MONO,24),GREY,a,anchor='mt')
    pts=[(0,0,0),(0.25,3,8),(0.5,5,12),(1,10,20)]
    five=0 if t<35.58 else expo((t-35.58)/0.5)
    if five>0: pts.append((5,lerp(10,20,five),lerp(20,40,five)))
    poly_hi=[(X(p[0]),Y(p[2])) for p in pts]; poly_lo=[(X(p[0]),Y(p[1])) for p in pts]
    band=Image.new('RGBA',(W,H),(0,0,0,0)); bd=ImageDraw.Draw(band); bd.polygon(poly_hi+poly_lo[::-1],fill=A(VGOLD,0.30*a)); im.alpha_composite(band)
    mid=[(X(p[0]),Y((p[1]+p[2])/2)) for p in pts]
    d.line(mid,fill=A(VGOLD,a),width=5)
    if GL: GL.line(mid,fill=A(VGOLD,a),width=10)
    for m in mid[1:]: d.ellipse([m[0]-7,m[1]-7,m[0]+7,m[1]+7],fill=A(WHITE,a))
    if five>0:
        b=ap(t,35.9,0.2); txt(d,X(5)-6,Y(40)-4,'20–40 LB',f(BEB,84),VGOLD,a*b,anchor='rb')
        if GL: GL.ellipse([X(5)-18,Y(30)-18,X(5)+18,Y(30)+18],fill=A(VGOLD,a))
    if t>=38.66: tag(d,gx0+150,gy1-56,'VS DAY 1',CYAN,26,a*ap(t,38.66))

# 4. bell curve (push) 41.3-57.3
def scene_bell(d,t,im):
    x0,x1,yb,yp=110,970,1090,650; mu=470; sg=140
    def yv(x): return yb-(yb-yp)*math.exp(-((x-mu)/sg)**2/2)
    p=clamp((t-41.3)/1.0)
    xs=list(range(x0,int(lerp(x0,x1,ease_io(p)))+1,4))
    if len(xs)>1:
        # fills
        if t>=51.54:
            b=ap(t,51.54,0.3); pts=[(x,yv(x)) for x in range(mu-sg,mu+sg+1,4)]
            lay=Image.new('RGBA',(W,H),(0,0,0,0)); ld=ImageDraw.Draw(lay); ld.polygon(pts+[(mu+sg,yb),(mu-sg,yb)],fill=A(VGOLD,0.40*b)); im.alpha_composite(lay)
        if t>=45.08:
            b=ap(t,45.08,0.25)*(1-0.6*ap(t,56.38,0.2)); tx=mu+int(2.2*sg); pts=[(x,yv(x)) for x in range(tx,x1+1,4)]
            lay=Image.new('RGBA',(W,H),(0,0,0,0)); ld=ImageDraw.Draw(lay); ld.polygon(pts+[(x1,yb),(tx,yb)],fill=A(RED,0.85*b)); im.alpha_composite(lay)
            if GL: GL.polygon(pts+[(x1,yb),(tx,yb)],fill=A(RED,0.5*b))
        d.line([(x,yv(x)) for x in xs],fill=A(CYAN,1),width=5)
        if GL: GL.line([(x,yv(x)) for x in xs],fill=A(CYAN,1),width=10)
    d.line([(x0,yb),(x1,yb)],fill=A(GREY,1),width=2)
    for k,lab in [(-2,'−2σ'),(-1,'−1σ'),(0,'AVG'),(1,'+1σ'),(2,'+2σ'),(3,'+3σ')]:
        x=mu+k*sg
        if x0<=x<=x1: d.line([(x,yb),(x,yb+12)],fill=A(GREY,1),width=2); txt(d,x,yb+18,lab,f(MONO,22),GREY,ap(t,41.6),anchor='mt')
    txt(d,x0,560,'RESPONSE TO THE SAME PROTOCOL',f(MONO,28),CREAM,ap(t,41.4)*(1-ap(t,53.2,0.2)))
    # outlier marker
    ox=mu+int(2.3*sg)
    if t>=41.96:
        b=ap(t,41.96); oy=yv(ox)
        d.line([(ox,oy-10),(ox,700)],fill=A(RED,b),width=3); d.ellipse([ox-10,oy-10,ox+10,oy+10],fill=A(RED,b))
        tag(d,ox+24,700,'240 LB',RED,30,b)
    if t>=45.08: tag(d,ox+24,760,'1% OF 1%',RED,30,ap(t,45.08))
    if t>=48.14: tag(d,ox+24,820,'+40 LB',RED,30,ap(t,48.14)); tag(d,ox+24,880,'CYCLE 1',RED,30,ap(t,48.30))
    if t>=53.44:
        b=ap(t,53.44); d.line([(mu,yp-10),(mu,yp-70)],fill=A(VGOLD,b),width=3)
        tag(d,mu,yp-110,'AVERAGE MALE · THE BENCHMARK',VGOLD,28,b,anchor='c')
    if t>=54.70:  # outlier dims out of the comparison
        b=ap(t,54.70,0.3); d.rectangle([mu+int(2.2*sg)-6,690,x1+6,yb+4],outline=A(RED,b),width=3)
def scene_bell_post(im,t):
    if 56.38<=t<57.6: stamp(im,640,1200,'OUTLIER',RED,t,56.38,80,-6)

# 5. top shelf: 10-year on/off strip + result spectrum (57.54-66.2)
def top_card(im,t,t0,t1,h=400):
    pin=expo((t-t0)/0.22); pout=clamp((t-t1)/0.18)
    if pin<=0 or pout>=1: return None
    y0=250-lerp(40,0,pin)-60*pout**2; box=(56,y0,1024,y0+h)
    frosted(im,box,0.86,14,18); a=pin*(1-pout)
    d=ImageDraw.Draw(im,'RGBA'); x0,y0,x1,y1=box
    d.rounded_rectangle(box,radius=18,outline=A(VGOLD,0.55*a),width=3); brackets(d,x0,y0,x1,y1,A(VGOLD,a),30,5)
    if GL: brackets(GL,x0,y0,x1,y1,A(VGOLD,a),30,10)
    return d,a,x0,y0,x1,y1
def scene_gantt(im,t):
    r=top_card(im,t,57.54,66.10,350)
    if not r: return
    d,a,x0,y0,x1,y1=r
    txt(d,x0+28,y0+20,'COACH AGZ · GEAR HISTORY',f(MONO,28),VGOLD,a); txt(d,x1-28,y0+20,'10 YRS',f(MONO,28),CREAM,a,anchor='rt')
    pattern=[1,1,0,1,0,1,1,0,1,1]
    sw=clamp((t-59.48)/1.8); gx0,gx1=x0+28,x1-28; cw=(gx1-gx0)/10
    for i,on in enumerate(pattern):
        if sw*10<=i: break
        q=min(1,sw*10-i); xa=gx0+i*cw+3; xb=xa+(cw-6)*q; y=y0+72
        if on: lit_bar(d,xa,y,xb,y+54,VGOLD,a)
        else: d.rectangle([xa,y,xb,y+54],outline=A(GREY,a),width=2)
        if q>=1: txt(d,xa+(cw-6)/2,y+14,'ON' if on else 'OFF',f(MONOB,22),INK if on else GREY,a,anchor='mt')
    # spectrum
    sy=y0+250; sx0,sx1=x0+28,x1-28
    if t>=61.9:
        b=a*ap(t,61.9,0.25)
        segs=[(0,0.33,(70,90,120),'BASELINE'),(0.33,0.66,(0,150,170),'GOOD'),(0.66,1.0,GREEN,'OPTIMAL')]
        for s0,s1,c,lab in segs:
            d.rectangle([lerp(sx0,sx1,s0)+2,sy,lerp(sx0,sx1,s1)-2,sy+26],fill=A(c,b*0.85)); txt(d,lerp(sx0,sx1,(s0+s1)/2),sy+36,lab,f(MONO,22),GREY,b,anchor='mt')
        txt(d,sx0,sy-60,'PHYSIQUE RESULT',f(MONO,26),CREAM,b)
        pos=lerp(0.1,0.58,expo((t-62.42)/0.6))
        if t>=64.86: pos=lerp(0.58,0.62,expo((t-64.86)/0.3))
        mx=lerp(sx0,sx1,pos); d.polygon([(mx-16,sy-18),(mx+16,sy-18),(mx,sy+6)],fill=A(WHITE,b))
        if GL: GL.polygon([(mx-16,sy-18),(mx+16,sy-18),(mx,sy+6)],fill=A(WHITE,b))
        d.line([(mx,sy),(mx,sy+26)],fill=A(WHITE,b),width=4)
        if t>=63.04: tag(d,mx-30,sy-62,'NOT OPTIMAL',RED,28,a*ap(t,63.04),anchor='r')
        if t>=64.86: check(d,mx+34,sy-60,GREEN,0.9,a*ap(t,64.86)); txt(d,mx+74,sy-62,'SOLID',f(MONOB,30),GREEN,a*ap(t,64.86))

# 6. scope: expected straight line vs real non-linear growth (66.38-70.2)
def scene_scope(d,t,im):
    x0,x1,y0,y1=120,980,560,1150
    a=1
    txt(d,x0,y0-70,'GROWTH OVER TIME',f(MONO,26),CYAN,ap(t,66.5))
    d.line([(x0,y1),(x1,y1)],fill=A(CYAN,0.8),width=3); d.line([(x0,y0),(x0,y1)],fill=A(CYAN,0.8),width=3)
    txt(d,x1,y1+14,'TIME →',f(MONO,22),CYAN,1,anchor='rt'); txt(d,x0+10,y0-4,'MUSCLE',f(MONO,22),CYAN,1)
    pe=clamp((t-66.8)/0.7)
    if pe>0: dashed(d,[(x0,y1),(lerp(x0,x1,pe),lerp(y1,y0+40,pe))],WHITE,4,18,12,0.9)
    if t>=67.2: txt(d,x1-10,y0+10,'EXPECTED',f(MONO,22),WHITE,ap(t,67.2),anchor='rt')
    # real curve: fast early, plateaus, a dip, slow climbs
    knots=[(0,0),(0.12,0.30),(0.22,0.42),(0.30,0.43),(0.38,0.41),(0.45,0.50),(0.58,0.53),(0.66,0.53),(0.74,0.60),(0.86,0.62),(1.0,0.68)]
    pr=clamp((t-67.4)/2.0)
    pts=[]
    for (u0,v0),(u1,v1) in zip(knots,knots[1:]):
        for k in range(8):
            u=lerp(u0,u1,k/8)
            if u>pr: break
            pts.append((lerp(x0,x1,u),lerp(y1,y0+40,lerp(v0,v1,k/8))))
    if len(pts)>1:
        d.line(pts,fill=A(VGOLD,1),width=6)
        if GL: GL.line(pts,fill=A(VGOLD,1),width=12)
        hx,hy=pts[-1]; d.ellipse([hx-9,hy-9,hx+9,hy+9],fill=A(WHITE,1))
    if pr>0.3: tag(d,lerp(x0,x1,0.24),lerp(y1,y0+40,0.43)+20,'PLATEAU',CYAN,22,ap(t,67.4+0.3*2))
    if pr>0.62: tag(d,lerp(x0,x1,0.56),lerp(y1,y0+40,0.53)+20,'PLATEAU',CYAN,22,ap(t,67.4+0.62*2))
    if t>=69.44:
        b=ap(t,69.44); xm,ym=lerp(x0,x1,0.75),lerp(y1,y0+40,0.75); cross(d,xm-20,ym-20,RED,1.4,b)
        tag(d,x0+30,y0+20,'NON-LINEAR',RED,30,b)

# 7. top shelf: bloodwork monitored vs cardiovascular risk (70.3-76.2)
def scene_risk(im,t):
    r=top_card(im,t,70.30,76.15,380)
    if not r: return
    d,a,x0,y0,x1,y1=r
    txt(d,x0+28,y0+20,'BLOODWORK',f(MONO,28),CYAN,a)
    # ECG trace scrolling
    ex0,ex1,ey=x0+28,x0+520,y0+110
    pts=[]
    for i in range(0,int(ex1-ex0),3):
        u=(i/120+t*1.4)%1; v=0
        if 0.40<u<0.44: v=-8
        elif 0.46<u<0.48: v=34
        elif 0.48<u<0.51: v=-62
        elif 0.51<u<0.54: v=22
        elif 0.62<u<0.70: v=-12*math.sin((u-0.62)/0.08*math.pi)
        pts.append((ex0+i,ey+v))
    d.line(pts,fill=A(CYAN,a),width=4)
    if GL: GL.line(pts,fill=A(CYAN,a),width=8)
    if t>=71.28: check(d,x0+560,y0+86,GREEN,1.1,a*ap(t,71.28)); txt(d,x0+606,y0+84,'MONITORED',f(BAR,48),GREEN,a*ap(t,71.28))
    # risk meter
    my=y0+250; mx0,mx1=x0+28,x1-28
    txt(d,mx0,my-50,'CARDIOVASCULAR RISK',f(MONO,28),CREAM,a*ap(t,70.6))
    level=0.78
    if 72.16<=t<73.92: level=lerp(0.78,0.30,ease_io((t-72.16)/0.8))    # the hoped-for drop
    if t>=73.92: level=lerp(0.30,0.80,expo((t-73.92)/0.35))
    n=12
    for i in range(n):
        xa=lerp(mx0,mx1,i/n)+3; xb=lerp(mx0,mx1,(i+1)/n)-3; on=(i+0.5)/n<=level
        c=GREEN if i<4 else (VGOLD if i<8 else RED)
        if on: lit_bar(d,xa,my,xb,my+46,c,a)
        else: d.rectangle([xa,my,xb,my+46],outline=A(DIM,a),width=2)
    if 72.16<=t<73.92: txt(d,mx0+lerp(mx1-mx0,0,0)*0,my+60,'EXPECTED: ELIMINATED',f(MONO,28),WHITE,a*ap(t,72.16))
    if t>=73.38: tag(d,mx0,my+60,'NOT ELIMINATED',RED,28,a*ap(t,73.92))
    if t>=75.02: tag(d,mx1,my+60,'LONG-TERM',RED,28,a*ap(t,75.02),anchor='r')

# 8. expectation vs reality (push) 78.4-86.98
def scene_expect(d,t,im):
    x0,x1=200,960
    def X(v): return lerp(x0,x1,v/30)
    ya,yb=760,1010
    for v in (0,10,20,30):
        d.line([(X(v),640),(X(v),1150)],fill=A((40,44,60) if v else GREY,1),width=1 if v else 2); txt(d,X(v),1160,f'{v}',f(MONO,24),GREY,1,anchor='mt')
    txt(d,x1,1196,'LB · FIRST 6 MONTHS',f(MONO,22),GREY,1,anchor='rt')
    txt(d,96,560,'CLIENT INTAKE',f(MONO,28),CREAM,ap(t,82.3))
    if t>=82.44:
        b=ap(t,82.44); txt(d,96,ya-80,'GOAL',f(BAR,52),WHITE,b); txt(d,96,ya-28,'NEW CLIENT',f(MONO,20),GREY,b)
    if t>=84.70:
        lo=20; hi=lerp(20,30,expo((t-85.04)/0.4)) if t>=85.04 else 20.6
        l=lerp(0,lo,expo((t-84.70)/0.3))
        lit_bar(d,X(l),ya,X(hi),ya+90,RED,1)
        if GL: GL.rectangle([X(l),ya,X(hi),ya+90],fill=A(RED,0.5))
        if t>=85.3: txt(d,X(hi)-10,ya+8,'20–30',f(BEB,76),WHITE,ap(t,85.3),anchor='rt')
    if t>=86.38:
        b=ap(t,86.38); txt(d,96,yb-80,'REALITY',f(BAR,52),WHITE,b); txt(d,96,yb-28,'AVG MALE · 6 MO',f(MONO,20),GREY,b)
        l=lerp(0,5,expo((t-86.38)/0.25)); h=lerp(l,12,expo((t-86.62)/0.3)) if t>=86.62 else l+0.5
        lit_bar(d,X(l),yb,X(h),yb+90,VGOLD,1)
        if GL: GL.rectangle([X(l),yb,X(h),yb+90],fill=A(VGOLD,0.5))
        if t>=86.8: txt(d,X(h)+14,yb+8,'5–12',f(BEB,76),VGOLD,ap(t,86.8))
    if t>=86.84:
        b=ap(t,86.84); xa,xb=X(12),X(20)
        d.line([(xa,yb-24),(xb,yb-24)],fill=A(RED,b),width=3); d.line([(xa,yb-36),(xa,yb-12)],fill=A(RED,b),width=3); d.line([(xb,yb-36),(xb,yb-12)],fill=A(RED,b),width=3)
        tag(d,(xa+xb)/2,yb-80,'GAP',RED,24,b,anchor='c')

# 9. PIP 87.0-95.08: time on gear (day 90 vs year 5) + feed post, then the speedometer
def scene_pip(d,t,im,g):
    a=g
    lx0,lx1=64,640
    if t<91.9:
        q=1-clamp((t-91.76)/0.15)
        txt(d,lx0,262,'TIME ON GEAR',f(MONO,30),VGOLD,a*q)
        def tbar(y,lab,frac,col,t0,val):
            b=a*q*ap(t,t0)
            if b<=0: return
            txt(d,lx0,y,lab,f(BAR,44),WHITE,b); d.rectangle([lx0,y+56,lx1,y+100],outline=A(DIM,b),width=2)
            fr=frac*expo((t-t0)/0.6); lit_bar(d,lx0+3,y+59,lx0+3+(lx1-lx0-6)*fr,y+97,col,b)
            if GL: GL.rectangle([lx0+3,y+59,lx0+3+(lx1-lx0-6)*fr,y+97],fill=A(col,0.5*b))
            txt(d,lx1,y+8,val,f(BEB,52),col,b,anchor='rt')
        tbar(320,'YOU',90/1825,VGOLD,88.20,'DAY 90')
        tbar(480,'THEIR FEED',1.0,CYAN,90.20,'YEAR 5')
        if t>=90.2: tag(d,lx0,640,'20× THE TIME',RED,30,a*q*ap(t,90.5))
    # feed post (forensic)
    if 89.38<=t<92.1:
        p=expo((t-89.38)/0.25); q=clamp((t-91.76)/0.25); x0=lerp(1100,150,p)-900*q**2; y0=900
        d.rounded_rectangle([x0,y0,x0+780,y0+390],radius=26,fill=A((14,16,24),a),outline=A(GREY,a),width=3)
        d.ellipse([x0+24,y0+20,x0+70,y0+66],fill=A(DIM,a)); txt(d,x0+86,y0+28,'@someone_else',f(DMB,28),WHITE,a)
        post_img(im,x0+24,y0+84,a)
        for i,(lb,xx,yy) in enumerate([('5 YRS IN',x0+60,y0+110),('LIGHTING',x0+300,y0+100),('PUMP',x0+520,y0+170)]):
            bb=a*ap(t,90.20+i*0.43,0.1); brackets(d,xx,yy,xx+170,yy+70,A(RED,bb),20,5); tag(d,xx,yy+76,lb,RED,24,bb)
        pass
    # speedometer
    if t>=91.76:
        b=a*ap(t,91.76,0.25); cx,cy,R=352,640,260
        txt(d,lx0,262,'GAIN RATE',f(MONO,30),VGOLD,b)
        for i in range(60):
            ang=math.pi+math.pi*i/59; c=GREEN if i<20 else (VGOLD if i<40 else RED)
            r0=R-30 if i%5 else R-50
            d.line([(cx+r0*math.cos(ang),cy+r0*math.sin(ang)),(cx+R*math.cos(ang),cy+R*math.sin(ang))],fill=A(c,b),width=4 if i%5 else 6)
        lv=0.25 if t<93.40 else lerp(0.25,0.98,expo((t-93.40)/0.9))
        if t>=94.1: lv=0.98+0.015*math.sin(t*60)
        ang=math.pi+math.pi*lv
        d.line([(cx,cy),(cx+(R-60)*math.cos(ang),cy+(R-60)*math.sin(ang))],fill=A(WHITE,b),width=8)
        if GL: GL.line([(cx,cy),(cx+(R-60)*math.cos(ang),cy+(R-60)*math.sin(ang))],fill=A(RED if lv>0.7 else WHITE,b),width=14)
        d.ellipse([cx-22,cy-22,cx+22,cy+22],fill=A(VGOLD,b))
        txt(d,cx,cy+40,'LB / MONTH',f(MONO,26),GREY,b,anchor='mt')
    if t>=94.66:
        p=expo((t-94.66)/0.14); y=930; x0=64; x1=lerp(x0,1016,p)
        lit_bar(d,x0,y,x1,y+100,RED,a)
        if GL: GL.rectangle([x0-4,y-6,x1+4,y+106],outline=A(RED,a),width=10)
        if p>0.6: txt(d,x0+30,y+10,'FASTEST ≠ THE GOAL',f(BEB,84),WHITE,a)

def post_img(im,x,y,a):
    w,h=732,236; yy,xx=np.mgrid[0:h,0:w]
    r=np.clip(1-np.hypot((xx-w*0.62)/(w*0.5),(yy-h*0.25)/(h*0.9)),0,1)
    base=np.stack([20+120*r**1.6,22+90*r**1.6,30+60*r**1.6],-1)
    img=Image.fromarray(base.astype(np.uint8)).convert('RGBA'); dd=ImageDraw.Draw(img)
    dd.text((w-24,h-10),'YEAR 5',font=f(BEB,150),fill=(255,255,255,40),anchor='rb')
    img.putalpha(int(255*a)); im.alpha_composite(img,(int(x),int(y)))
# 10. top shelf: muscle kept + long-term health battery (95.18-101.7)
def scene_battery(im,t):
    r=top_card(im,t,95.45,101.65,370)
    if not r: return
    d,a,x0,y0,x1,y1=r
    txt(d,x0+28,y0+20,'MUSCLE BUILT vs KEPT',f(MONO,28),VGOLD,a)
    for i,(lab,tt,col) in enumerate([('BUILT',95.64,VGOLD),('KEPT',97.04,GREEN)]):
        y=y0+76+i*92; b=a*ap(t,tt)
        if b<=0: continue
        txt(d,x0+28,y+6,lab,f(BAR,40),WHITE,b); fr=expo((t-tt)/0.5)
        lit_bar(d,x0+150,y,x0+150+300*fr,y+60,col,b)
        if GL: GL.rectangle([x0+150,y,x0+150+300*fr,y+60],fill=A(col,0.4*b))
    if t>=97.4: check(d,x0+470,y0+168,GREEN,1.0,a*ap(t,97.4))
    # battery
    bx0,by0,bx1,by1=x0+560,y0+80,x1-60,y0+250
    if t>=98.92:
        b=a*ap(t,98.92); txt(d,bx0,y0+20,'LONG-TERM HEALTH',f(MONO,28),CREAM,b)
        d.rounded_rectangle([bx0,by0,bx1,by1],radius=14,outline=A(WHITE,b),width=5); d.rectangle([bx1+4,by0+50,bx1+22,by1-50],fill=A(WHITE,b))
        lvl=1.0 if t<100.16 else lerp(1.0,0.12,expo((t-100.16)/0.9))
        col=GREEN if lvl>0.5 else (VGOLD if lvl>0.25 else RED)
        lit_vbar(d,bx0+10,by0+10,bx0+10+(bx1-bx0-20)*lvl,by1-10,col,b)
        if GL: GL.rectangle([bx0+10,by0+10,bx0+10+(bx1-bx0-20)*lvl,by1-10],fill=A(col,0.5*b))
        txt(d,(bx0+bx1)/2,by1+14,f'{int(lvl*100)}%',f(BEB,56),col,b,anchor='mt')
        if t>=100.16:
            c=a*ap(t,100.3,0.1); xs=(bx0+bx1)/2
            d.line([(xs-10,by0),(xs+16,by0+60),(xs-14,by0+100),(xs+8,by1)],fill=A(INK,c),width=6)
            tag(d,bx0-130,by1+20,'DISPOSABLE',RED,28,a*ap(t,100.64),anchor='l')

# 11. lifespan (push) 101.8-108.62
def scene_life(d,t,im):
    x0,x1=110,970
    def X(y): return lerp(x0,x1,y/40)
    rows=[('YOU',700,101.9),('YOUR KIDS',920,104.16)]
    for lab,y,tt in rows:
        b=ap(t,tt,0.2)
        if b<=0: continue
        txt(d,x0,y-70,lab,f(BAR,48),WHITE,b)
        fr=expo((t-tt)/0.6); lit_bar(d,x0,y,x0+(x1-x0)*fr,y+60,GREEN if lab=='YOU' else CYAN,b*0.9)
    for yr in range(0,41,10):
        txt(d,X(yr),1010,f'+{yr}',f(MONO,26),GREY,ap(t,101.9),anchor='mt'); d.line([(X(yr),1000),(X(yr),990)],fill=A(GREY,ap(t,101.9)),width=2)
    txt(d,x1,1050,'YEARS FROM NOW',f(MONO,26),GREY,ap(t,101.9),anchor='rt')
    if t>=102.56:
        b=ap(t,103.22,0.2); xc=X(10)
        lay=Image.new('RGBA',(W,H),(0,0,0,0)); ld=ImageDraw.Draw(lay)
        ld.rectangle([xc,690,x1+4,770],fill=A((20,6,8),0.92*b))
        for k in range(int(xc),x1,22): ld.line([(k,770),(k+40,690)],fill=A((90,16,20),b),width=3)
        im.alpha_composite(lay)
        d.line([(xc,640),(xc,1000)],fill=A(RED,b),width=5)
        if GL: GL.line([(xc,640),(xc,1000)],fill=A(RED,b),width=10)
        tag(d,xc+16,624,'+10 YRS · CUT SHORT',RED,30,b)
    if t>=105.18:
        b=ap(t,105.18); xc=X(10)
        lay=Image.new('RGBA',(W,H),(0,0,0,0)); ld=ImageDraw.Draw(lay)
        ld.rectangle([xc,910,x1+4,990],fill=A((20,6,8),0.85*b)); im.alpha_composite(lay)
        tag(d,xc+16,926,'NO FATHER',RED,30,b)
    if t>=106.92: tag(d,x0,1110,'EVERYTHING AROUND YOU',RED,28,ap(t,107.1))
def glitch(img,t):
    k=round((t-106.92)*FPS)
    if not (0<=k<5): return img
    arr=np.asarray(img).copy(); rng=np.random.default_rng(k)
    for _ in range(9):
        y=rng.integers(0,H-80); h=rng.integers(12,70); dx=int(rng.integers(-60,60))
        arr[y:y+h]=np.roll(arr[y:y+h],dx,axis=1)
    arr[...,0]=np.roll(arr[...,0],8,axis=1)
    if k<2: arr=np.clip(arr.astype(np.int16)+np.array([60,-10,-10]),0,255).astype(np.uint8)
    return Image.fromarray(arr)

# 12. CTA 108.78-end
LOGO=None
def cta(im,t):
    if t<108.78: return
    global LOGO
    a=ap(t,108.80,0.25); y=720; x0,x1=56,1024; y1=1270
    frosted(im,(x0,y,x1,y1),0.84,16,22); d=ImageDraw.Draw(im,'RGBA')
    d.rounded_rectangle([x0,y,x1,y1],radius=22,outline=A(VGOLD,0.6*a),width=3); brackets(d,x0,y,x1,y1,A(VGOLD,a),30,5)
    if GL: brackets(GL,x0,y,x1,y1,A(VGOLD,a),30,10)
    if LOGO is None:
        lg=Image.open(T+'logo.jpg').convert('RGB'); s=min(lg.size); lg=lg.crop(((lg.width-s)//2,(lg.height-s)//2,(lg.width+s)//2,(lg.height+s)//2)).resize((150,150),Image.LANCZOS)
        m=Image.new('L',(150,150),0); ImageDraw.Draw(m).ellipse([0,0,149,149],fill=255); lg.putalpha(m); LOGO=lg
    lg=LOGO.copy(); lg.putalpha(lg.split()[3].point(lambda v:int(v*a))); im.alpha_composite(lg,(84,y+28))
    d=ImageDraw.Draw(im,'RGBA')
    txt(d,260,y+36,'FREE · MUSCLE GROWTH',f(MONO,28),VGOLD,a*ap(t,109.3)); txt(d,260,y+74,'TRACKING FRAMEWORK',f(BAR,64),WHITE,a*ap(t,109.78))
    # mini tracker sheet preview
    ty=y+190; cols=['WEEK','WEIGHT','WAIST','STRENGTH','TREND']
    for i,c in enumerate(cols): txt(d,96+i*186,ty,c,f(MONO,22),GREY,a*ap(t,110.12))
    for r in range(3):
        ra=a*ap(t,110.2+r*0.12,0.1)
        if ra<=0: continue
        yy=ty+34+r*40; d.line([(90,yy-6),(990,yy-6)],fill=A(DIM,ra),width=1)
        txt(d,96,yy,f'{(r+1)*4:02d}',f(MONO,22),WHITE,ra)
        for i in range(1,4): d.rounded_rectangle([96+i*186,yy+4,96+i*186+120,yy+24],radius=6,fill=A((60,64,80),ra))
        pts=[(96+4*186+k*18,yy+22-((k*7+r*5)%13)) for k in range(5)]; d.line(pts,fill=A(GREEN,ra),width=3)
    if t>=111.20:
        b=expo((t-111.20)/0.12); s=lerp(1.12,1.0,b)
        fn=f(BEB,int(92*s)); label='COMMENT  "GROWTH"'; tw=d.textlength(label,font=fn)
        bx=(W-tw-60)/2; by=1130
        lit_bar(d,bx,by,bx+tw+60,by+int(110*s),VGOLD,b); d.text((bx+30,by+8),label,font=fn,fill=A(INK,b))
        if GL: GL.rectangle([bx-4,by-4,bx+tw+64,by+int(110*s)+4],outline=A(VGOLD,b),width=12)

# ---------------- text hook + topic band ----------------
HOOK=[[('Realistic ',WHITE),('MUSCLE',VGOLD),(' gain',WHITE)],[('3 months to 5 years',WHITE)]]
HOOK_END=6.0
def hook(im,t):
    if t>=HOOK_END: return
    a=1-clamp((t-(HOOK_END-0.15))/0.15); s=lerp(1.0,1.04,clamp(t/HOOK_END))
    lay=Image.new('RGBA',(W,420),(0,0,0,0)); d=ImageDraw.Draw(lay)
    size=104; fn=f(BAR,size)
    widths=[sum(d.textlength(p,font=fn) for p,_ in line) for line in HOOK]
    while max(widths)>840: size-=2; fn=f(BAR,size); widths=[sum(d.textlength(p,font=fn) for p,_ in line) for line in HOOK]
    lh=int(size*1.02); top=40; bw=max(widths)+70
    d.rounded_rectangle([(W-bw)/2,top-18,(W+bw)/2,top+lh*2+22],radius=22,fill=(2,3,8,205))
    for i,line in enumerate(HOOK):
        x=(W-widths[i])/2; y=top+i*lh-size*0.12
        for p,c in line:
            d.text((x,y),p,font=fn,fill=c+(255,)); x+=d.textlength(p,font=fn)
    lay=lay.resize((int(W*s),int(420*s)),Image.BICUBIC)
    if a<1: lay.putalpha(lay.split()[3].point(lambda v:int(v*a)))
    im.alpha_composite(lay,(int((W-lay.width)/2),int(255-(lay.height-420)*0.5)))
BAND_IN=6.0; BAND_OUT=57.45
def band(im,t):
    if not (BAND_IN-0.15<=t<BAND_OUT+0.15): return
    a=min(clamp((t-(BAND_IN-0.15))/0.15),1-clamp((t-BAND_OUT)/0.15))
    if layout_at(t)[0]=='split': a*=1   # band stays on split (sits over footage)
    d=ImageDraw.Draw(im,'RGBA'); y0,y1=262,352
    d.rectangle([8,y0,W,y1],fill=A(NAVY,0.88*a)); d.line([(64,y0+20),(100,y0+20)],fill=A(GOLD,a),width=4)
    txt(d,112,y0+6,'@coach.agz',f(MONO,24),GOLD,a)
    fn=f(BAR,58); x=64; y=y0+30
    for p,c in [('Realistic ',CREAM),('MUSCLE',VGOLD),(' gain · 3 months to 5 years',CREAM)]:
        txt(d,x,y-8,p,fn,c,a); x+=d.textlength(p,font=fn)

# ---------------- frame ----------------
def frame(src,t):
    global GL
    src=footage(src,t)
    mode,g,t0,t1=layout_at(t)
    glow=Image.new('RGBA',(W,H),(0,0,0,0)); GL=ImageDraw.Draw(glow,'RGBA')
    if mode in ('push','cta','scope'):
        dark={'push':0.68,'cta':0.45,'scope':0.74}[mode]; bl={'push':18,'cta':6,'scope':10}[mode]
        im=Image.blend(src.filter(ImageFilter.GaussianBlur(bl*g)),Image.new('RGB',(W,H),(5,8,16)),dark*g).convert('RGBA')
        if mode=='scope' and g>0:
            d=ImageDraw.Draw(im,'RGBA')
            for x in range(0,W,54): d.line([(x,0),(x,H)],fill=A(CYAN,0.07*g),width=1)
            for y in range(0,H,54): d.line([(0,y),(W,y)],fill=A(CYAN,0.07*g),width=1)
            sy=int((t*700)%H); d.rectangle([0,sy,W,sy+3],fill=A(CYAN,0.25*g))
    elif mode=='split':
        im=bg_grid(t).convert('RGBA'); oy=int(lerp(0,330,g)); sp=int(lerp(H,SPLIT_Y,g))
        im.paste(src.crop((0,oy,W,oy+sp)).convert('RGBA'),(0,0))
        d=ImageDraw.Draw(im,'RGBA'); d.line([(0,sp),(W,sp)],fill=A(VGOLD,1),width=4); GL.line([(0,sp),(W,sp)],fill=A(VGOLD,1),width=10)
    elif mode=='pip':
        im=bg_grid(t).convert('RGBA')
        bx0,by0,bx1,by1=[lerp(a_,b_,g) for a_,b_ in zip((0,0,W,H),PIP)]
        fw,fh=int(bx1-bx0),int(by1-by0)
        if fw>4 and fh>4:
            fr=src.resize((fw,fh),Image.BICUBIC).convert('RGBA'); m=Image.new('L',(fw,fh),0); ImageDraw.Draw(m).rounded_rectangle([0,0,fw-1,fh-1],radius=int(24*g),fill=255)
            im.paste(fr,(int(bx0),int(by0)),m)
            d=ImageDraw.Draw(im,'RGBA'); d.rounded_rectangle([bx0,by0,bx1,by1],radius=int(24*g),outline=A(VGOLD,g),width=4)
            GL.rounded_rectangle([bx0,by0,bx1,by1],radius=int(24*g),outline=A(VGOLD,0.7*g),width=8)
            if g>0.8: d.ellipse([bx0+20,by0+20,bx0+36,by0+36],fill=A(RED,1 if int(t*3)%2==0 else 0.3)); txt(d,bx0+46,by0+14,'LIVE',f(MONOB,22),WHITE,1)
    else:
        im=src.convert('RGBA')
    # light scrims top/bottom for text legibility (footage untouched otherwise)
    if mode not in ('pip','split'):
        yy=np.arange(H); a_=np.where(yy>1200,np.clip((yy-1200)/260,0,1)*110,0); a_=np.maximum(a_,np.where(yy<440,(1-yy/440)*110,0)); scr=(a_*(1-g)).astype(np.uint8)
        im.alpha_composite(Image.merge('RGBA',[Image.new('L',(W,H),c) for c in NAVY]+[Image.fromarray(np.repeat(scr[:,None],W,1))]))
    # panel scenes
    if mode=='push' and g>0:
        P=(64,450,1016,1290)
        pin=expo((t-t0)/0.20); pout=clamp((t-t1)/0.16)
        if pout<1:
            s=lerp(1.05,1.0,pin)*lerp(1.0,1.03,pout); w=(P[2]-P[0])*s; h=(P[3]-P[1])*s; cx=(P[0]+P[2])/2; cy=(P[1]+P[3])/2
            x0,y0,x1,y1=cx-w/2,cy-h/2,cx+w/2,cy+h/2
            frosted(im,(x0,y0,x1,y1),0.92,8)
            lay=Image.new('RGBA',(W,H),(0,0,0,0)); d=ImageDraw.Draw(lay,'RGBA')
            fn,hl,hr={12.0:(scene_bars,'LEAN MUSCLE GAINED','AVG MALE · LB'),41.3:(scene_bell,'GENETIC RESPONSE','POPULATION'),
                      82.2:(scene_expect,'EXPECTATION vs REALITY','FIRST 6 MO'),101.8:(scene_life,'THE REAL COST','TIMELINE')}[t0]
            fn(d,t,lay)
            if pin<1: lay=lay.filter(ImageFilter.GaussianBlur(8*(1-pin)))
            al=pin*(1-pout); lay.putalpha(lay.split()[3].point(lambda v:int(v*al)))
            im.alpha_composite(lay); d=ImageDraw.Draw(im,'RGBA')
            panel_frame(d,x0,y0,x1,y1,al,hl,hr,VGOLD,t)
    if mode=='scope' and g>0:
        lay=Image.new('RGBA',(W,H),(0,0,0,0)); d=ImageDraw.Draw(lay,'RGBA'); scene_scope(d,t,lay)
        lay.putalpha(lay.split()[3].point(lambda v:int(v*g))); im.alpha_composite(lay)
    if mode=='split' and g>0:
        d=ImageDraw.Draw(im,'RGBA'); scene_split(d,t,im,g)
    if mode=='pip' and g>0:
        d=ImageDraw.Draw(im,'RGBA'); scene_pip(d,t,im,g)
    side_rail(im,t); scene_gantt(im,t); scene_risk(im,t); scene_battery(im,t); scene_bell_post(im,t)
    cta(im,t)
    GL=None
    if glow.getbbox():
        sm=glow.resize((W//4,H//4),Image.BILINEAR)
        g1=np.asarray(sm.filter(ImageFilter.GaussianBlur(3.5))).astype(np.float32)/255; g2=np.asarray(sm.filter(ImageFilter.GaussianBlur(10))).astype(np.float32)/255
        prem=np.clip(g1[...,:3]*g1[...,3:]*2.3+g2[...,:3]*g2[...,3:]*1.8,0,1)
        prem=np.asarray(Image.fromarray((prem*255).astype(np.uint8)).resize((W,H),Image.BILINEAR)).astype(np.float32)/255
        b=np.asarray(im.convert('RGB')).astype(np.float32)/255
        im=Image.fromarray(((1-(1-b)*(1-prem))*255).astype(np.uint8)).convert('RGBA')
    d=ImageDraw.Draw(im,'RGBA'); d.rectangle([0,0,7,H],fill=GOLD)
    band(im,t); hook(im,t)
    captions(im,t)
    out=im.convert('RGB')
    out=glitch(out,t)
    # impact shakes on slams
    for ts in (35.9,56.38,94.66,111.20):
        k=round((t-ts)*FPS)
        if k in (0,1):
            dx=[9,-5][k]; z=1.025; big=out.resize((int(W*z),int(H*z)),Image.BICUBIC); ox=(big.width-W)//2-dx; oy=(big.height-H)//2
            out=big.crop((ox,oy,ox+W,oy+H)); ImageDraw.Draw(out).rectangle([0,0,7,H],fill=GOLD)
    return out

if __name__=='__main__':
    mode=sys.argv[2]
    if mode=='stills':
        import os; os.makedirs(S+'/qc',exist_ok=True)
        for tt in [float(x) for x in sys.argv[3:]]:
            subprocess.run(['ffmpeg','-v','error','-y','-ss',f'{tt:.4f}','-i',T+'assembled.mov','-frames:v','1',S+'/qc/_src.png'])
            frame(Image.open(S+'/qc/_src.png').convert('RGB'),tt).resize((540,960),Image.LANCZOS).save(S+f'/qc/st_{tt:06.2f}.jpg',quality=88)
        sys.exit()
    n0,n1=int(sys.argv[3]),int(sys.argv[4]); out=sys.argv[5]
    dec=subprocess.Popen(['ffmpeg','-v','error','-i',T+'assembled.mov','-vf',f'select=between(n\\,{n0}\\,{n1-1})','-vsync','0','-f','rawvideo','-pix_fmt','rgb24','-'],stdout=subprocess.PIPE)
    enc=subprocess.Popen(['ffmpeg','-v','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-','-c:v','libx264','-crf','14','-preset','medium','-pix_fmt','yuv420p',out],stdin=subprocess.PIPE)
    for n in range(n0,n1):
        buf=dec.stdout.read(W*H*3)
        if len(buf)<W*H*3: print('short',n); break
        enc.stdin.write(frame(Image.frombuffer('RGB',(W,H),buf),n/FPS).tobytes())
    enc.stdin.close(); enc.wait(); dec.kill(); print('done',n0,n1)
