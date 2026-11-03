# Reel: "Mast primo ai" (Masteron + Primo are not AIs): full edit, 720p30 preview.
# Built on the saved setup: test-06 look + full-test-02 workflow (dead air trimmed, misspeak cut, 108% punch-in per jump cut,
# captions from the trimmed audio). Usage: python render.py <scratch> [--events|--groups|--still t..|--range n0 n1 out.mp4]
import json, subprocess, sys, math, re
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
S=sys.argv[1]; F=S+'/fonts/'; T=S+'/r3/work/'
W,H=1080,1920; FPS=30; N=1622; DUR=N/FPS
GOLD=(201,169,110); CREAM=(244,241,234); MUTED=(184,184,188); LABEL=(124,124,130)
RED=(255,34,28); NAVY=(14,17,23); VGOLD=(255,194,26); CYAN=(0,229,255); GREEN=(30,255,110); DEEP=(2,3,8)
INNER=(29,29,33); CHIP=(40,12,18)
GL=None; EVENTS=[]
def sfx(t,kind,**k): EVENTS.append(dict(t=round(t,3),kind=kind,**k))

_fc={}
def f(n,s,wght=None):
    k=(n,int(s),wght)
    if k not in _fc:
        fo=ImageFont.truetype(F+n,int(s))
        if wght: fo.set_variation_by_axes([14,wght])
        _fc[k]=fo
    return _fc[k]
BEB='BebasNeue.ttf'; MONO='JBMono-500.ttf'; MONOB='JBMono-700.ttf'; BAR='Barlow-600.ttf'
def dm(s,w=500): return f('DMSans.ttf',s,w)
def clamp(x,a=0,b=1): return max(a,min(b,x))
def expo(x): x=clamp(x); return 1 if x>=1 else 1-2**(-10*x)
def ease_io(x): x=clamp(x); return 4*x**3 if x<.5 else 1-(-2*x+2)**3/2
def lerp(a,b,t): return a+(b-a)*t
def win(t,a,b,fade=0.15): return clamp((t-a)/fade)*clamp((b-t)/fade)
def tracked(d,xy,s,fn,fill,sp):
    x,y=xy
    for ch in s: d.text((x,y),ch,font=fn,fill=fill); x+=d.textlength(ch,font=fn)+sp
    return x
def tracked_w(d,s,fn,sp): return sum(d.textlength(c,font=fn)+sp for c in s)-sp

def brackets(d,x0,y0,x1,y1,col,L=34,w=4,p=1.0):
    L=L*p
    for (cx,cy,sx,sy) in [(x0,y0,1,1),(x1,y0,-1,1),(x0,y1,1,-1),(x1,y1,-1,-1)]:
        d.line([(cx,cy),(cx+sx*L,cy)],fill=col,width=w); d.line([(cx,cy),(cx,cy+sy*L)],fill=col,width=w)
def lit_bar(d,x0,y0,x1,y1,col,a=255):
    h=max(1,int(y1-y0))
    for i in range(h):
        k=i/h; c=tuple(int(min(255,v*(1.18-0.36*k)+(40 if k<0.12 else 0))) for v in col)
        d.line([(x0,y0+i),(x1,y0+i)],fill=c+(a,))
def red_tag(d,x,y,label,size=32,right=False):
    fn=f(MONO,size); tw=d.textlength(label,font=fn); bh=int(size*1.5)
    if right: x=x-tw-24
    lit_bar(d,x,y,x+tw+24,y+bh,RED); d.text((x+12,y+bh*0.12),label,font=fn,fill=(255,255,255))
    if GL: GL.rectangle([x-4,y-4,x+tw+28,y+bh+4],outline=RED+(255,),width=8)
    return x
def flag_box(d,box,label,t0,t,tag_right=True):
    p=expo((t-t0)/0.14)
    if p<=0: return
    x0,y0,x1,y1=box
    brackets(d,x0,y0,x1,y1,RED+(255,),26,6,1.0)
    if GL: brackets(GL,x0,y0,x1,y1,RED+(255,),26,10,1.0); GL.rectangle([x0,y0,x1,y1],outline=RED+(200,),width=6)
    if p>0.3:
        q=clamp((p-0.3)/0.7)
        d.line([(x0,y0),(lerp(x0,x1,q),y0)],fill=RED+(255,),width=4); d.line([(x1,y1),(lerp(x1,x0,q),y1)],fill=RED+(255,),width=4)
        d.line([(x0,y1),(x0,lerp(y1,y0,q))],fill=RED+(255,),width=4); d.line([(x1,y0),(x1,lerp(y0,y1,q))],fill=RED+(255,),width=4)
    if p>0.5 and label: red_tag(d,x1+12,(y0+y1)/2-24,label)
def frosted(im,box,dark=0.72,blur=22):
    x0,y0,x1,y1=[int(v) for v in box]; x0=max(0,x0); y0=max(0,y0); x1=min(W,x1); y1=min(H,y1)
    if x1-x0<2 or y1-y0<2: return
    reg=im.crop((x0,y0,x1,y1)).filter(ImageFilter.GaussianBlur(blur))
    reg=Image.blend(reg.convert('RGB'),Image.new('RGB',reg.size,DEEP),dark).convert('RGBA')
    im.paste(reg,(x0,y0))
def tri(d,x,y,s,up,col):
    d.polygon([(x,y+s),(x+s,y+s),(x+s/2,y)] if up else [(x,y),(x+s,y),(x+s/2,y+s)],fill=col)
def check(d,x,y,col,w=4,s=1.0):
    d.line([(x,y+10*s),(x+8*s,y+20*s),(x+24*s,y)],fill=col,width=w)
def meter(d,x0,y,x1,v,col,h=22):
    d.rectangle([x0,y,x1,y+h],outline=MUTED+(120,),width=2)
    d.rectangle([x0+4,y+4,x0+4+(x1-x0-8)*clamp(v),y+h-4],fill=col+(255,))
    if GL: GL.rectangle([x0+4,y+4,x0+4+(x1-x0-8)*clamp(v),y+h-4],fill=col+(150,))


# ---------------- words / captions (transcript of the trimmed cut, medium.en, vocabulary-prompted) ----------------
words=json.load(open(T+'words_asm.json'))   # = words_captions.json in this folder
FIX={5:'AIS.',91:'NOTHING',113:'IMPORTANT',103:'ARIMIDEX.',128:'ARIMIDEX,',138:'MASTERON,',162:'MASTERON',42:'OUT-COMPETE',99:'ANTI-ESTROGEN'}
# 91: heard "Everything"/"thing" (the "No-" is swallowed); meaning is "Nothing actually got inhibited" -> flagged for Coach AGZ to confirm
# 113: heard "unimportant" by every pass; meaning is "it's important to understand these mechanics" -> flagged
for i,w in FIX.items(): words[i]['w']=w
for a_,b_ in ((99,100),(42,43)): words[a_]['e']=words[b_]['e']
for i in (100,43): del words[i]
for w in words: w['w']=w['w'].upper()
CAP_Y=1450; CAP_MAX=900

_d0=ImageDraw.Draw(Image.new('RGB',(4,4)))
def disp(w): return w.rstrip(',.')
WEAK={'THE','A','AN','AT','IN','TO','OF','AND','YOUR','ON','THAT','FOR','AS','WITHIN','UNTIL','WITHOUT','FROM','BUT','SO','IT'}
def build_groups():
    G=[]; cur=[]
    def width(ix):
        fn=f(BEB,128); return sum(_d0.textlength(disp(words[i]['w']),font=fn) for i in ix)+(len(ix)-1)*(_d0.textlength(' ',font=fn)+14)
    for i,w in enumerate(words):
        if cur:
            prev=words[cur[-1]]
            weak=disp(w['w']) in WEAK and len(cur)>=2 and disp(words[cur[-1]]['w']) not in ('SHUT','COMING')
            brk=weak or len(cur)>=3 or prev['w'][-1] in ',.?!' or w['s']-prev['e']>0.30 or width(cur+[i])>CAP_MAX*1.15
            if brk: G.append(cur); cur=[]
        cur.append(i)
    G.append(cur); return G
G=build_groups()
GSTART=[words[g[0]]['s'] for g in G]
def group_at(t):
    cur=None
    for gi,s in enumerate(GSTART):
        if s<=t+1e-6: cur=gi
        else: break
    if cur is not None and t>words[G[cur][-1]]['e']+0.9: return None   # clear after long pauses
    return cur
def cap_layout(gi):
    ws=[disp(words[i]['w']) for i in G[gi]]; size=116
    while True:
        fn=f(BEB,size); sp=_d0.textlength(' ',font=fn)+14
        wd=[_d0.textlength(w,font=fn) for w in ws]; tot=sum(wd)+sp*(len(ws)-1)
        if tot<=CAP_MAX: break
        size-=4
    x=(W-tot)/2; xs=[]
    for w_ in wd: xs.append(x); x+=w_+sp
    return ws,wd,xs,size
def draw_caption(im,t):
    gi=group_at(t)
    if gi is None: return
    ws,wd,xs,size=cap_layout(gi); idx=G[gi]; g0=GSTART[gi]; pop=expo((t-g0)/0.10); s=lerp(0.9,1,pop)
    cap=Image.new('RGBA',(W,300),(0,0,0,0)); cd=ImageDraw.Draw(cap); shd=Image.new('RGBA',(W,300),(0,0,0,0)); sdd=ImageDraw.Draw(shd)
    aw=0
    for k,i in enumerate(idx):
        if words[i]['s']<=t: aw=k
    fn=f(BEB,size); prev=max(0,aw-1); bt=expo((t-words[idx[aw]]['s'])/0.07) if aw>0 else 1
    bx0=lerp(xs[prev],xs[aw],bt)-18; bx1=lerp(xs[prev]+wd[prev],xs[aw]+wd[aw],bt)+18
    for k,(w_,x_) in enumerate(zip(ws,xs)):
        if k!=aw: sdd.text((x_+4,46),w_,font=fn,fill=(0,0,0,210))
    cap.alpha_composite(shd.filter(ImageFilter.GaussianBlur(6)))
    cd.rounded_rectangle([bx0,40+size*0.02,bx1,40+size*0.98],radius=6,fill=RED+(255,))
    for k,(w_,x_) in enumerate(zip(ws,xs)): cd.text((x_,40),w_,font=fn,fill=CREAM,stroke_width=0 if k==aw else 3,stroke_fill=(0,0,0))
    if abs(s-1)>0.002:
        cap=cap.resize((int(W*s),int(300*s)),Image.BICUBIC); ox=int((W-cap.width)/2); oy=int(CAP_Y-40-(cap.height-300)/2)
    else: ox,oy=0,CAP_Y-40
    im.alpha_composite(cap,(ox,oy))

# ---------------- timeline (all times on the TRIMMED timeline) ----------------
TRIM=json.load(open(T+'trim.json'))
_acc=0; CUTS=[]
for a,b in TRIM['keep_frames'][:-1]: _acc+=b-a; CUTS.append(_acc/FPS)      # jump-cut times in the trimmed cut
def seg_of(t): return sum(1 for c in CUTS if c<=t+1e-6)
P=(64,470,1016,1260)
PANELS=[dict(o=6.08,c=19.90,hdr='EVIDENCE 01',st=[(6.08,'RECEPTOR SITE')]),
        dict(o=21.52,c=32.70,hdr='EVIDENCE 02',st=[(21.52,'AROMATASE')]),
        dict(o=36.30,c=50.32,hdr='EVIDENCE 03',st=[(36.30,'SIMPLIFIED')])]

OPEN_D=0.22; CLOSE_D=0.18
for p in PANELS:
    sfx(p['o'],'whoosh',d=0.20,g=-27); sfx(p['o']+OPEN_D,'thud',w=1.4,g=-15); sfx(p['c']-0.02,'whoosh',d=0.18,g=-30)
    for st,_ in p['st'][1:]: sfx(st,'scan',d=0.30,g=-28)
def push_amt(t):
    g=0
    for p in PANELS: g=max(g,clamp((t-(p['o']-0.12))/0.28)*clamp((p['c']+0.10-t)/0.24))
    return ease_io(g)
def panel_box(t,p):
    if t<p['o'] or t>p['c']+CLOSE_D: return None,0
    if t<p['o']+OPEN_D: q=expo((t-p['o'])/OPEN_D)
    elif t>p['c']: q=1-ease_io((t-p['c'])/CLOSE_D)
    else: q=1
    x1=lerp(8,P[2],q); x0=lerp(8,P[0],min(1,q*1.6))        # grows out of / collapses into the gold edge rule
    return (x0,P[1],x1,P[3]),q
X0=110; XR=970
def gold_tag(d,x,y,label,size=30,right=False):
    fn=f(MONOB,size); tw=d.textlength(label,font=fn); bh=int(size*1.5)
    if right: x=x-tw-24
    lit_bar(d,x,y,x+tw+24,y+bh,VGOLD); d.text((x+12,y+bh*0.12),label,font=fn,fill=DEEP+(255,))
    if GL: GL.rectangle([x-4,y-4,x+tw+28,y+bh+4],outline=VGOLD+(220,),width=8)
def green_tag(d,x,y,label,a=255,right=True):
    fn=f(MONO,28); tw=d.textlength(label,font=fn)
    if right: x=x-tw-48
    check(d,x,y+8,GREEN+(a,),4,0.9); d.text((x+40,y),label,font=fn,fill=GREEN+(a,))
def dashed(d,pts,col,w=4,on=14,off=10):
    acc=0; draw=True
    for (xa,ya),(xb,yb) in zip(pts,pts[1:]):
        seg=math.hypot(xb-xa,yb-ya)
        if seg==0: continue
        pos=0
        while pos<seg:
            step=min((on if draw else off)-acc,seg-pos); x1=xa+(xb-xa)*(pos+step)/seg; y1=ya+(yb-ya)*(pos+step)/seg
            if draw: d.line([(xa+(xb-xa)*pos/seg,ya+(yb-ya)*pos/seg),(x1,y1)],fill=col,width=w)
            pos+=step; acc+=step
            if acc>=(on if draw else off): acc=0; draw=not draw

# -- EVIDENCE 01: receptor site (DHT-derived, bind the AR hard, estrogen pushed off, its signal drops) --
def evA(d,t):
    x=X0
    for lab,tt in [('MASTERON',6.38),('PRIMOBOLAN',7.16)]:
        q=expo((t-tt)/0.16)
        if q<=0: continue
        fn=f(BAR,42); tw=d.textlength(lab,font=fn); a=int(255*q); xx=x+30*(1-q)
        d.rectangle([xx,566,xx+tw+40,628],outline=CREAM+(a,),width=3); d.text((xx+20,572),lab,font=fn,fill=CREAM+(a,))
        qd=expo((t-7.68)/0.14)
        if qd>0: d.text((xx+2,640),'DHT-DERIVED',font=f(MONO,24),fill=VGOLD+(int(255*qd),))
        x+=tw+70
    a=int(255*clamp((t-9.50)/0.15))
    if a>0:
        d.text((X0,700),'ANDROGEN RECEPTOR',font=f(BAR,40),fill=CREAM+(a,))
        d.rounded_rectangle([X0,750,XR,850],radius=16,outline=MUTED+(int(a*0.7),),width=3)
        for k in range(6):
            cx=X0+70+k*((XR-X0-140)/5); d.ellipse([cx-30,770,cx+30,830],outline=MUTED+(int(a*0.6),),width=3)
            q=expo((t-9.62-k*0.07)/0.12)
            if q>0:
                yy=770-40*(1-q); d.rounded_rectangle([cx-22,yy+8,cx+22,yy+52],radius=8,fill=VGOLD+(int(255*q),))
                if GL: GL.rounded_rectangle([cx-22,yy+8,cx+22,yy+52],radius=8,fill=VGOLD+(int(140*q),))
        if t>=10.88: s='BOUND · HIGH AFFINITY'; d.text((XR-d.textlength(s,font=f(MONO,24)),710),s,font=f(MONO,24),fill=VGOLD+(int(255*clamp((t-10.88)/0.15)),))
    # estrogen pushed off ("out-compete")
    if t>=11.66:
        p=ease_io((t-11.66)/0.70)
        for k in range(3):
            cx=X0+200+k*230+40*p*(k-1); cy=900+60*p; a2=int(255*(1-0.6*p))
            d.ellipse([cx-26,cy-26,cx+26,cy+26],outline=RED+(a2,),width=4); d.text((cx-16,cy-18),'E2',font=f(BEB,40),fill=RED+(a2,))
        if t>=12.36: red_tag(d,XR,890,'OUT-COMPETED',28,right=True)
    if t>=14.22:
        y=1060; a3=int(255*clamp((t-14.22)/0.15)); d.text((X0,y),'ESTROGEN SIGNAL',font=f(BAR,44),fill=CREAM+(a3,))
        v=lerp(0.78,0.22,ease_io((t-15.42)/0.88)); meter(d,560,y+18,920,v,RED,26)
        if t>=16.30: tri(d,934,y+16,30,False,RED+(255,))
    if t>=18.02:     # what the lab then shows
        y=1150; a4=int(255*clamp((t-18.02)/0.15)); d.line([(X0,y-20),(XR,y-20)],fill=MUTED+(int(a4*0.3),),width=2)
        d.text((X0,y),'E2 LAB (SENSITIVE)',font=f(BAR,44),fill=CREAM+(a4,))
        if t>=19.04: red_tag(d,XR,y+2,'READS LOW',28,right=True)
sfx(7.68,'tick',g=-30); sfx(9.62,'scan',d=0.45,g=-31); sfx(12.36,'tick',g=-25); sfx(16.30,'tick',g=-27); sfx(19.04,'tick',g=-26)

# -- EVIDENCE 02: aromatase still running; an AI blocks the enzyme, Mast/Primo block the signal downstream --
def node_box(d,x0,y0,x1,y1,lab,col,a,size=36):
    d.rounded_rectangle([x0,y0,x1,y1],radius=12,outline=col+(a,),width=3)
    fn=f(BAR,size); d.text(((x0+x1)/2-d.textlength(lab,font=fn)/2,(y0+y1)/2-size*0.62),lab,font=fn,fill=col+(a,))
def arrow(d,xa,xb,y,col,a,q=1.0):
    xe=lerp(xa,xb,q); d.line([(xa,y),(xe,y)],fill=col+(a,),width=4)
    if q>=1: d.polygon([(xb,y-11),(xb+18,y),(xb,y+11)],fill=col+(a,))
def evB(d,t):
    y0,y1=600,700; ym=(y0+y1)/2
    qa=expo((t-21.60)/0.16); qb=expo((t-21.75)/0.16); qc=expo((t-21.90)/0.16)
    if qa>0: node_box(d,X0,y0,330,y1,'TESTOSTERONE',CREAM,int(255*qa),34)
    lit=clamp((t-22.62)/0.15)
    if qb>0:
        col=tuple(int(lerp(c1,c2,lit)) for c1,c2 in zip(MUTED,VGOLD)); node_box(d,420,y0,650,y1,'AROMATASE',col,int(255*qb),38)
        if GL and lit>0: GL.rounded_rectangle([420,y0,650,y1],radius=12,outline=VGOLD+(int(200*lit),),width=8)
        arrow(d,334,400,ym,MUTED,int(255*qb))
    if qc>0: node_box(d,760,y0,XR,y1,'E2',CREAM,int(255*qc),46); arrow(d,654,740,ym,MUTED,int(255*qc))
    if t>=23.02: d.text((420,y1+14),'STILL ACTIVE',font=f(MONO,24),fill=VGOLD+(int(255*clamp((t-23.02)/0.15)),))
    if t>=24.06:      # conversion keeps flowing
        for k in range(6):
            u=((t-24.06)*0.55+k/6)%1.0; x=lerp(X0+230,XR-60,u)
            if 330<x<420 or 650<x<760 or x>=760: pass
            dd=8; d.ellipse([x-dd,ym-dd-62,x+dd,ym+dd-62],fill=VGOLD+(int(255*clamp((t-24.06)/0.3)),))
        if t>=25.14: d.text((X0,y0-44),'T → E2 · CONVERTING',font=f(MONO,24),fill=MUTED+(int(255*clamp((t-25.14)/0.15)),))
    if t>=27.24:
        brackets(d,410,y0-10,660,y1+10,VGOLD+(255,),26,6)
        if GL: brackets(GL,410,y0-10,660,y1+10,VGOLD+(255,),26,10)
        if t>27.31: gold_tag(d,660,y1+10,'NOT INHIBITED',26,right=True)
    # comparison: where each one acts
    if t>=28.74:
        a=int(255*clamp((t-28.74)/0.15)); y=850
        d.line([(X0,y-26),(XR,y-26)],fill=MUTED+(int(a*0.3),),width=2)
        d.text((X0,y),'ARIMIDEX · AI',font=f(BAR,40),fill=CREAM+(a,))
        node_box(d,560,y-6,790,y+56,'AROMATASE',MUTED,a,32)
        if t>=29.90:
            q=expo((t-29.90)/0.12); cx,cy=675,y+25
            d.line([(cx-40*q,cy-30*q),(cx+40*q,cy+30*q)],fill=RED+(255,),width=7); d.line([(cx+40*q,cy-30*q),(cx-40*q,cy+30*q)],fill=RED+(255,),width=7)
            if q>0.5: d.text((560,y+70),'ENZYME BLOCKED',font=f(MONO,24),fill=RED+(255,))
    if t>=30.64:
        a=int(255*clamp((t-30.64)/0.15)); y=1030
        d.text((X0,y),'MASTERON · PRIMO',font=f(BAR,40),fill=CREAM+(a,))
        node_box(d,560,y-6,650,y+56,'E2',CREAM,a,38); arrow(d,654,700,y+25,MUTED,a)
        node_box(d,720,y-6,XR,y+56,'RECEPTOR',MUTED,a,32)
        if t>=31.80:
            q=expo((t-31.80)/0.14); d.rectangle([714,y-14,714+12,y+64],fill=VGOLD+(int(255*q),))
            if GL: GL.rectangle([714,y-14,714+12,y+64],fill=VGOLD+(int(200*q),))
            if t>=32.22: d.text((560,y+70),'SIGNAL BLOCKED DOWNSTREAM',font=f(MONO,24),fill=VGOLD+(int(255*clamp((t-32.22)/0.12)),))
sfx(22.62,'tick',g=-28); sfx(24.06,'scan',d=0.6,g=-33); sfx(27.31,'thud',w=1.2,g=-18); sfx(29.90,'tick',g=-24); sfx(31.80,'tick',g=-26)

# -- EVIDENCE 03: the faucet (Coach AGZ's own analogy), clinical line schematic --
def faucet(d,cx,t,flow_on,flow_from,valve_off_t,cover_t,level,a):
    C=CYAN+(a,)
    # supply pipe + valve + spout
    d.line([(cx-170,680),(cx+10,680)],fill=C,width=6); d.line([(cx+10,680),(cx+10,730)],fill=C,width=6)
    vx=cx-80; off=valve_off_t is not None and t>=valve_off_t
    vcol=(RED if off else CYAN)+(a,); d.rectangle([vx-18,664,vx+18,696],outline=vcol,width=5)
    ang=math.radians(90 if off else 0); hx=vx+30*math.cos(ang); hy=650-30*math.sin(ang)
    d.line([(vx,664),(vx,640)],fill=vcol,width=5); d.line([(vx-28,640),(vx+28,640)] if not off else [(vx,612),(vx,668)],fill=vcol,width=6)
    if GL: GL.line([(cx-170,680),(cx+10,680),(cx+10,730)],fill=CYAN+(int(a*0.6),),width=10)
    # basin
    bx0,bx1,by0,by1=cx-150,cx+150,860,1060
    d.line([(bx0,by0),(bx0,by1),(cx-24,by1)],fill=C,width=6); d.line([(cx+24,by1),(bx1,by1),(bx1,by0)],fill=C,width=6)
    d.line([(cx-24,by1),(cx-24,by1+70)],fill=C,width=6); d.line([(cx+24,by1),(cx+24,by1+70)],fill=C,width=6)
    if GL: GL.line([(bx0,by0),(bx0,by1),(bx1,by1),(bx1,by0)],fill=CYAN+(int(a*0.5),),width=10)
    # water level
    if level>0.01:
        top=by1-(by1-by0-10)*level; d.rectangle([bx0+5,top,bx1-5,by1-4],fill=(0,229,255,int(a*0.35)))
        d.line([(bx0+5,top),(bx1-5,top)],fill=C,width=3)
    # stream
    if flow_on>0:
        top=730; bot=by1-4-(by1-by0-10)*level
        for k in range(10):
            yy=top+((t*600+k*40)%max(1,(bot-top)))
            d.line([(cx+10,yy),(cx+10,min(bot,yy+22))],fill=CYAN+(int(a*flow_on),),width=5)
    # drain cover
    if cover_t is not None and t>=cover_t:
        q=expo((t-cover_t)/0.14); yc=by1-6-60*(1-q)
        d.rectangle([cx-46,yc-10,cx+46,yc+6],fill=VGOLD+(int(255*q),))
        if GL: GL.rectangle([cx-46,yc-10,cx+46,yc+6],fill=VGOLD+(int(200*q),))
def evC(d,t):
    L_,R_=315,765
    qa=clamp((t-37.00)/0.15)
    if qa>0:
        a=int(255*qa); s='AI · ARIMIDEX'; fn=f(BAR,40); d.text((L_-d.textlength(s,font=fn)/2,566),s,font=fn,fill=CREAM+(a,))
        stop=ease_io((t-38.52)/0.25); flow=1-stop
        faucet(d,L_,t,flow,37.0,38.52,None,0.08*flow,a)
        if t>=38.82: gold_tag(d,L_-110,1150,'SUPPLY OFF',28)
    qb=clamp((t-40.40)/0.15)
    if qb>0:
        a=int(255*qb); s='MAST · PRIMO · EQ'; fn=f(BAR,40); d.text((R_-d.textlength(s,font=fn)/2,566),s,font=fn,fill=CREAM+(a,))
        lev=0.10+0.72*ease_io((t-44.52)/3.4)
        faucet(d,R_,t,1.0,40.40,None,42.98,lev,a)
        if t>=43.84: d.text((R_-d.textlength('DRAIN COVERED',font=f(MONO,24))/2,1146),'DRAIN COVERED',font=f(MONO,24),fill=VGOLD+(int(255*clamp((t-43.84)/0.15)),))
        if t>=44.52: s2='STILL FLOWING'; d.text((R_-10-d.textlength(s2,font=f(MONO,24)),790),s2,font=f(MONO,24),fill=CYAN+(int(255*clamp((t-44.52)/0.15)),))
    d.line([(540,560),(540,1120)],fill=MUTED+(60,),width=2)
    if t>=49.52:
        p=expo((t-49.52)/0.10); y=1160; x1=lerp(P[0],P[2],p)
        if GL: GL.rectangle([P[0]-4,y-8,x1+4,y+96],outline=RED+(255,),width=10)
        lit_bar(d,P[0],y,x1,y+88,RED); d.rectangle([P[0],y+84,x1,y+88],fill=(140,0,0))
        if p>0.6:
            fn=f(BEB,72); d.text((P[0]+40,y+8),'E2 LOW ≠ PRODUCTION OFF',font=fn,fill=(255,255,255))
sfx(37.00,'scan',d=0.3,g=-32); sfx(38.52,'tick',g=-24); sfx(40.40,'scan',d=0.3,g=-32); sfx(42.98+0.1,'thud',w=1.3,g=-17); sfx(44.52,'scan',d=1.2,g=-34); sfx(49.62,'impact',g=-13)
CONTENT={0:[(6.08,evA)],1:[(21.52,evB)],2:[(36.30,evC)]}
SHAKES=[49.62]


from PIL import ImageChops
def panels(im,t):
    for pi,p in enumerate(PANELS):
        box,q=panel_box(t,p)
        if box is None: continue
        x0,y0,x1,y1=box
        frosted(im,box,0.92,8)
        lay=Image.new('RGBA',(W,H),(0,0,0,0))
        stages=CONTENT[pi]; si=0
        for k,(st,_) in enumerate(stages):
            if t>=st: si=k
        def render_stage(k):
            l=Image.new('RGBA',(W,H),(0,0,0,0)); fn_=stages[k][1]
            fn_(ImageDraw.Draw(l,'RGBA'),t)
            return l
        global GL
        mainGL=GL; pg=Image.new('RGBA',(W,H),(0,0,0,0)); GL=ImageDraw.Draw(pg,'RGBA')
        ys=None; cur=render_stage(si)
        if si>0 and t<stages[si][0]+0.30:
            wq=ease_io((t-stages[si][0])/0.30); ys=int(lerp(y0+70,y1,wq))
            prev=render_stage(si-1); m=Image.new('L',(W,H),0); ImageDraw.Draw(m).rectangle([0,0,W,ys],fill=255)
            cur=Image.composite(cur,prev,m)
        GL=mainGL
        if pg.getbbox() and mainGL is not None:
            gm=Image.new('L',(W,H),0); ImageDraw.Draw(gm).rectangle([x0-40,y0-40,x1+40,y1+40],fill=int(255*q))
            pg.putalpha(ImageChops.multiply(pg.split()[3],gm)); mainGL._image.alpha_composite(pg) if hasattr(mainGL,'_image') else None
        if q<1: cur.putalpha(cur.split()[3].point(lambda v:int(v*q)))
        clip=Image.new('L',(W,H),0); ImageDraw.Draw(clip).rectangle([x0,y0,x1,y1],fill=255)
        cur.putalpha(ImageChops.multiply(cur.split()[3],clip))
        lay.alpha_composite(cur)
        d=ImageDraw.Draw(lay,'RGBA'); a=int(255*q)
        d.rectangle([x0,y0,x1,y1],outline=VGOLD+(int(a*0.8),),width=3); brackets(d,x0,y0,x1,y1,VGOLD+(a,),48,7)
        if GL: brackets(GL,x0,y0,x1,y1,VGOLD+(a,),44,14); GL.rectangle([x0,y0,x1,y1],outline=VGOLD+(int(a*0.5),),width=6)
        if x1-x0>600:
            stage=[s for st,s in p['st'] if t>=st][-1]
            d.ellipse([x0+26,y0+26,x0+42,y0+42],fill=RED+(a if int(t*4)%2==0 else a//3,))
            d.text((x0+56,y0+18),stage,font=f(MONO,28),fill=CREAM+(a,))
            s=p['hdr']
            for tt_,h_ in p.get('hdr2',{}).items():
                if t>=tt_: s=h_
            d.text((x1-30-d.textlength(s,font=f(MONO,28)),y0+18),s,font=f(MONO,28),fill=VGOLD+(a,))
            d.line([(x0+20,y0+66),(x1-20,y0+66)],fill=MUTED+(int(a*0.25),),width=1)
        if ys:
            g=Image.new('RGBA',(W,H),(0,0,0,0)); gd=ImageDraw.Draw(g); gd.rectangle([x0+4,ys-3,x1-4,ys+3],fill=CYAN+(255,))
            if GL: GL.rectangle([x0+4,ys-10,x1-4,ys+10],fill=CYAN+(230,))
            lay.alpha_composite(g.filter(ImageFilter.GaussianBlur(8))); lay.alpha_composite(g)
        im.alpha_composite(lay)

def newL():
    l=Image.new('RGBA',(W,H),(0,0,0,0)); return l,ImageDraw.Draw(l,'RGBA')
DISC='FOR RESEARCH & EDUCATIONAL PURPOSES ONLY'

# ---- hook: kicker + "ARE NOT AIs." + synergist tag; headline hands off into the pinned title ----
TK=0.05; TL2=1.00; TRED=1.54; TPILL=4.32; THO=(5.50,5.84)
sfx(TK,'tick',g=-30); sfx(TL2,'thud',w=1.3,g=-16); sfx(TPILL+0.1,'thud',w=1.0,g=-20); sfx(THO[0],'whoosh',d=0.30,g=-28)
PIN_WIN=[(THO[0],50.15)]
def pin_vis(t):
    v=0
    for i,(a,b_) in enumerate(PIN_WIN):
        if t<a: continue
        fin=1 if i==0 else clamp((t-a)/0.25); fout=clamp((b_+0.25-t)/0.25); v=max(v,fin*fout)
    return ease_io(v)
def headline(d,x,y,fn,a,t,dot=0):
    d.text((x,y),'ARE NOT ',font=fn,fill=CREAM+(a,)); x+=d.textlength('ARE NOT ',font=fn)
    rc=ease_io((t-TRED)/0.10); col=tuple(int(lerp(c1,c2,rc)) for c1,c2 in zip(CREAM,RED))
    d.text((x,y),'AIs',font=fn,fill=col+(a,)); x+=d.textlength('AIs',font=fn)
    if dot>0: d.text((x,y),'.',font=fn,fill=CREAM+(int(a*dot),))
def title(im,t):
    h=ease_io((t-THO[0])/(THO[1]-THO[0]))
    if h>=1:
        v=pin_vis(t)
        if v<=0: return
        ty=-220*(1-v)
    else: ty=0
    if h>0:
        B,bd=newL(); bd.rectangle([8,200+ty,W,388+ty],fill=NAVY+(int(240*h),)); im.alpha_composite(B)
    L,d=newL()
    kq=expo((t-TK)/0.25); ky=lerp(250,224,h)+ty
    if kq>0:
        d.line([(64,ky+20),(64+50*kq,ky+20)],fill=GOLD,width=4)
        lab='MASTERON · PRIMO'; fn=f(BAR,lerp(40,30,h)); n=int(len(lab)*clamp((t-TK-0.12)/0.40)) if h<=0.5 else len(lab)
        tracked(d,(130,ky+lerp(0,3,h)),lab[:n],fn,GOLD,lerp(9,7,h))
    if h>0:
        a=int(255*h); fn=f(MONO,24); s='@coach.agz'; d.text((1016-d.textlength(s,font=fn),ky+6),s,font=fn,fill=GOLD+(a,))
        d.text((64,352+ty),DISC,font=f(MONO,18),fill=LABEL+(a,))
    q2=expo((t-TL2)/0.16)
    if q2>0:
        size=lerp(150,86,h); y=lerp(282,262,h)+ty+12*(1-q2); a=int(255*q2)
        headline(d,64,y,f(BEB,size),a,t,dot=1-h)
    qp=expo((t-TPILL)/0.18)
    if qp>0 and h<1:
        L2,d2=newL(); a=int(255*qp*(1-clamp(h*3))); fn=f(MONOB,30); s='TREAT AS: SYNERGISTIC COMPOUNDS'; tw=d2.textlength(s,font=fn)
        x=lerp(24,64,qp); y=440
        lit_bar(d2,x,y,x+tw+32,y+50,VGOLD,a); d2.text((x+16,y+8),s,font=fn,fill=DEEP+(a,))
        if GL and t<TPILL+0.5: GL.rectangle([x,y,x+tw+32,y+50],outline=VGOLD+(int(200*(1-(t-TPILL)/0.5)),),width=8)
        L.alpha_composite(L2)
    im.alpha_composite(L)


# ---- side chips over the wall (daily tracking, coaching cadence) ----
CHIPS=[]

for c in CHIPS:
    for _,tt in c['items']: sfx(tt,'tick',g=-31)
def chips(im,t):
    for c in CHIPS:
        t0=c['items'][0][1]
        if t<t0-0.15 or t>c['out']+0.2: continue
        out=ease_io((t-c['out'])/0.2)
        L,d=newL(); a=int(255*clamp((t-t0+0.15)/0.15)*(1-out))
        hw=d.textlength(c['hdr'],font=f(MONO,24))
        if a>0: frosted(im,(32,584,100+hw,628),0.88*a/255,10)
        d.line([(44,606),(80,606)],fill=VGOLD+(a,),width=4); d.text((92,592),c['hdr'],font=f(MONO,24),fill=VGOLD+(a,)); im.alpha_composite(L)
        for i,(lab,tt) in enumerate(c['items']):
            q=expo((t-tt)/0.14)
            if q<=0: break
            fn=f(BAR,40); tw=d.textlength(lab,font=fn); bw=tw+88; y=640+i*80; x=40-24*(1-q)-20*out; a=int(255*q*(1-out))
            if out<1: frosted(im,(x,y,x+bw,y+62),0.86*(1-out),10)
            L,d=newL()
            d.rectangle([x,y,x+bw,y+62],outline=GREEN+(int(a*0.55),),width=2)
            check(d,x+18,y+20,GREEN+(a,),4,0.95); d.text((x+58,y+8),lab,font=fn,fill=CREAM+(a,)); im.alpha_composite(L)
            if GL and t<tt+0.35: check(GL,x+18,y+20,GREEN+(a,),9,0.95)

# ---- full-screen scenes: 4-step recap, end card ----
LOGO=None
def logo():
    global LOGO
    if LOGO is None:
        lg=Image.open(S+'/logo.jpg').convert('RGB').resize((240,240),Image.LANCZOS)
        m=Image.new('L',(240,240),0); ImageDraw.Draw(m).ellipse([0,0,239,239],fill=255); lg.putalpha(m); LOGO=lg
    return LOGO
_SB=None
def scene_bg(a):
    global _SB
    if _SB is None:
        bg=np.zeros((H,W,3),np.float32)+np.array(NAVY,np.float32)
        yy,xx=np.mgrid[0:H,0:W]; r=np.sqrt(((xx-W)/(W*0.9))**2+(yy/(H*0.5))**2)
        bg+=(np.clip(1-r,0,1)**2)[...,None]*np.array([16,12,6],np.float32)
        bg+=np.random.default_rng(3).standard_normal((H,W,1)).astype(np.float32)*1.6
        _SB=Image.fromarray(np.clip(bg,0,255).astype(np.uint8)).convert('RGBA')
    l=_SB.copy(); l.putalpha(int(255*a*0.94)); return l
END=50.20; PILL=50.36; TELL=51.38
sfx(END-0.1,'whoosh',d=0.22,g=-27); sfx(PILL+0.12,'thud',w=1.6,g=-14); sfx(TELL,'tick',g=-28)
def end_card(im,t):
    if t<END: return
    a=ease_io((t-END)/0.25); im.alpha_composite(scene_bg(a))
    q=expo((t-END-0.10)/0.25)
    if q<=0: return
    lg=logo().copy(); lg.putalpha(lg.split()[3].point(lambda v:int(v*q))); im.alpha_composite(lg,(540-120,330))
    L,d=newL(); A=int(255*q)
    fn=f(BAR,40); s='COACH AGZ'; w=tracked_w(d,s,fn,10); tracked(d,(540-w/2,596),s,fn,GOLD+(A,),10)
    fn=f(MONO,28); s='@coach.agz'; d.text((540-d.textlength(s,font=fn)/2,652),s,font=fn,fill=MUTED+(A,))
    fn=f(BAR,36); s='MASTERON · PRIMO'; w=tracked_w(d,s,fn,8); tracked(d,(540-w/2,760),s,fn,GOLD+(A,),8)
    fn=f(BEB,130); s1='ARE NOT '; s2='AIs.'; tw=d.textlength(s1+s2,font=fn); x=540-tw/2
    d.text((x,806+8*(1-q)),s1,font=fn,fill=CREAM+(A,)); d.text((x+d.textlength(s1,font=fn),806+8*(1-q)),s2,font=fn,fill=RED+(A,))
    im.alpha_composite(L); L,d=newL()
    pq=expo((t-PILL)/0.20)
    if pq>0:
        fn=f(MONOB,58); s='SAVE + SHARE'; tw=d.textlength(s,font=fn); bw=tw+80; x0=540-bw/2; y0=1000+lerp(-40,0,pq)
        if GL and t<PILL+0.6: GL.rectangle([x0,y0,x0+bw,y0+120],outline=VGOLD+(int(220*(1-(t-PILL)/0.6)),),width=10)
        lit_bar(d,x0,y0,x0+bw,y0+120,VGOLD,int(255*min(1,pq*1.5)))
        im.alpha_composite(L); L,d=newL()
        tq=clamp((t-PILL-0.08)/0.12)
        if tq>0: d.text((540-tw/2,y0+24),s,font=fn,fill=DEEP+(int(255*tq),))
    fq=expo((t-TELL)/0.14)
    if fq>0:
        fn=f(MONOB,36); s='TELL ME WHAT YOU THINK · COMMENTS'; d.text((540-d.textlength(s,font=fn)/2,1158),s,font=fn,fill=CREAM+(int(255*fq),))
    fn=f(MONO,20); d.text((540-d.textlength(DISC,font=fn)/2,1240),DISC,font=fn,fill=LABEL+(A,))
    im.alpha_composite(L)


# ---------------- frame ----------------
def zoom_at(t):   # saved setup: 108% punch-in alternates at every jump cut; plus punch-ins on new points between cuts
    for a,b,z in ((19.98,21.48,1.08),(33.32,36.20,1.10)):
        if a<=t<b: return z
    return 1.08 if seg_of(t)%2==1 else 1.0

_PT=None
def frame(src,t):
    z=zoom_at(t)
    if z>1.001:
        cx,cy=540,1000; w,h=W/z,H/z; src=src.crop((cx-w/2,cy-h/2,cx+w/2,cy+h/2)).resize((W,H),Image.BICUBIC)
    g=push_amt(t); bg=src
    if g>0: bg=Image.blend(src.filter(ImageFilter.GaussianBlur(18*g)),Image.new('RGB',(W,H),(5,8,16)),0.68*g)
    im=bg.convert('RGBA')
    global _PT
    if _PT is None:
        y=np.arange(H)
        sc=np.maximum(np.where(y>1380,np.minimum(1,(y-1380)/240)*130,0),np.where(y<440,(1-y/440)*120,0))
        _PT=(sc,np.where(y<600,np.clip(1-(y-260)/340,0,1)*np.minimum(1,y/200+0.6)*150,0))
    tc=clamp(1-ease_io((t-THO[0])/(THO[1]-THO[0])))
    alpha=np.clip(np.maximum(_PT[0]*(1-g),_PT[1]*tc),0,255).astype(np.uint8)
    scr=Image.new('RGBA',(W,H),NAVY+(0,)); scr.putalpha(Image.fromarray(np.repeat(alpha[:,None],W,1)))
    im.alpha_composite(scr)
    global GL
    glow=Image.new('RGBA',(W,H),(0,0,0,0)); GL=ImageDraw.Draw(glow,'RGBA')
    panels(im,t); chips(im,t); end_card(im,t)
    GL=None
    if glow.getbbox():
        gb=np.asarray(glow.filter(ImageFilter.GaussianBlur(14))).astype(np.float32)/255
        g2=np.asarray(glow.filter(ImageFilter.GaussianBlur(40))).astype(np.float32)/255
        prem=np.clip(gb[...,:3]*gb[...,3:]*2.3+g2[...,:3]*g2[...,3:]*1.8,0,1)
        base_=np.asarray(im.convert('RGB')).astype(np.float32)/255
        im=Image.fromarray(((1-(1-base_)*(1-prem))*255).astype(np.uint8)).convert('RGBA')
    title(im,t)
    d=ImageDraw.Draw(im,'RGBA'); d.rectangle([0,0,7,H],fill=GOLD)
    draw_caption(im,t)
    out=im.convert('RGB')
    for st in SHAKES:
        k=round((t-st)*FPS)
        if k in (0,1):
            dx=[9,-5][k]; zz=1.025; big=out.resize((int(W*zz),int(H*zz)),Image.BICUBIC); ox=(big.width-W)//2-dx; oy=(big.height-H)//2
            out=big.crop((ox,oy,ox+W,oy+H)); ImageDraw.Draw(out).rectangle([0,0,7,H],fill=GOLD)
    return out

if __name__=='__main__':
    a=sys.argv[2:]
    if a and a[0]=='--events':
        json.dump(sorted(EVENTS,key=lambda e:e['t']),open(T+'events.json','w'),indent=0); print(len(EVENTS),'events'); sys.exit()
    if a and a[0]=='--groups':
        for g in G: print(f"{words[g[0]]['s']:6.2f} "+' '.join(words[i]['w'] for i in g))
        sys.exit()
    if a and a[0]=='--still':
        for tt in [float(x) for x in a[1:]]:
            subprocess.run(['ffmpeg','-v','error','-y','-ss',str(tt),'-i',T+'assembled.mov','-frames:v','1',T+'qc/_src.png'])
            frame(Image.open(T+'qc/_src.png').convert('RGB'),tt).resize((540,960),Image.LANCZOS).save(T+f'qc/s_{tt:06.2f}.jpg',quality=88)
        sys.exit()
    if a and a[0]=='--range':
        n0,n1,outp=int(a[1]),int(a[2]),a[3]
        dec=subprocess.Popen(['ffmpeg','-v','error','-i',T+'assembled.mov','-vf',f'select=between(n\\,{n0}\\,{n1-1})','-fps_mode','passthrough','-f','rawvideo','-pix_fmt','rgb24','-'],stdout=subprocess.PIPE)
        enc=subprocess.Popen(['ffmpeg','-v','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-','-vf','scale=720:1280:flags=lanczos','-c:v','libx264','-crf','18','-preset','medium','-pix_fmt','yuv420p',outp],stdin=subprocess.PIPE)
        for n in range(n0,n1):
            buf=dec.stdout.read(W*H*3)
            if len(buf)<W*H*3: print('short at',n); break
            enc.stdin.write(frame(Image.frombuffer('RGB',(W,H),buf),n/FPS).tobytes())
        enc.stdin.close(); enc.wait(); dec.kill(); print('done',n0,n1)
