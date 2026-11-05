# Reel: "HCT no Donation" (dropping hematocrit without blood donation): full edit, native 1080x1920, neon overlay set
# Built on the saved setup: test-06 look + full-test-02 workflow (dead air trimmed, misspeak cut, 108% punch-in per jump cut,
# captions from the trimmed audio). Usage: python render.py <scratch> [--events|--groups|--still t..|--range n0 n1 out.mp4]
import json, subprocess, sys, math, re
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
S=sys.argv[1]; F=S+'/fonts/'; T=S+'/r12/work/'
W,H=1080,1920; FPS=30; N=3277; DUR=N/FPS
GOLD=(201,169,110); CREAM=(244,241,234); MUTED=(184,184,188); LABEL=(124,124,130)
RED=(255,34,28); NAVY=(14,17,23); VGOLD=(255,194,26); CYAN=(0,229,255); GREEN=(30,255,110); DEEP=(2,3,8)
INNER=(29,29,33); CHIP=(40,12,18)
GL=None; EVENTS=[]
NEWTL=False
def sfx(t,kind,**k): EVENTS.append(dict(t=round(t,3),kind=kind,nt=NEWTL,**k))

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


# ---------------- words / captions: source transcript (gap-guarded windows) mapped through the trim ----------------
words=json.load(open(T+'words_cut.json'))   # = words_captions.json in this folder
FIX={104:'FERRITIN,',235:'PRO MUSCLE',243:'DIHYDROQUERCETIN.',254:'OF 57',340:'F*CKING'}
for i,w in FIX.items(): words[i]['w']=w
for i,s_ in ((270,'54%'),(11,'49%'),(7,'57%')): words[i]['w']=s_; words[i]['e']=words[i+1]['e']; del words[i+1]   # "57 %" -> "57%" (descending so indices hold)
for w in words: w['w']=w['w'].upper()
CAP_Y=1450; CAP_MAX=900
import difflib as _dl
def _warp_build():
    import re as _re
    prev=json.load(open(T+'prev_take_words.json')); n=lambda w:_re.sub(r'[^a-z0-9]','',w['w'].lower())
    A=[n(w) for w in prev]; B=[n(w) for w in words]
    pairs=[(words[j]['s'],prev[i]['s']) for bl in _dl.SequenceMatcher(None,A,B,autojunk=False).get_matching_blocks()
           for i,j in zip(range(bl.a,bl.a+bl.size),range(bl.b,bl.b+bl.size)) if prev[i]['s']>=8.0 and bl.size>=3]
    pairs.sort(); out=[]
    for nt,ot in pairs:
        if not out or (nt>out[-1][0]+0.05 and ot>out[-1][1]+0.05): out.append((nt,ot))
    return np.array([p[0] for p in out]),np.array([p[1] for p in out])
WN,WO=_warp_build()
def WARP(t):   # new-take time -> previous-take time (for the carried-over v2 overlays)
    if t<=WN[0]: return float(t-(WN[0]-WO[0]))
    if t>=WN[-1]: return float(t-(WN[-1]-WO[-1]))
    return float(np.interp(t,WN,WO))
def UNWARP(t):
    if t<=WO[0]: return t+(WN[0]-WO[0])
    if t>=WO[-1]: return t+(WN[-1]-WO[-1])
    return float(np.interp(t,WO,WN))







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
            weak=disp(w['w']) in WEAK and len(cur)>=2 and disp(words[cur[-1]]['w']) not in ('BINDS','GET','KEEP')
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
PANELS=[dict(o=8.29,c=18.30,hdr='HISTORY',st=[(8.29,'DASHBOARD · THE OLD WAY')]),
        dict(o=33.33,c=43.70,hdr='THE QUESTION',st=[(33.33,'DOSE-RESPONSE')]),
        dict(o=63.03,c=80.95,hdr='MECHANISM',st=[(63.03,'WHY A LITTLE IS A LOT')]),
        dict(o=83.59,c=105.30,hdr='PROTOCOL',st=[(83.59,'THE MICRODOSE')])]
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

# ---- shared schematic pieces ----
def particles(d,x0,y0,x1,y1,n,t,seed,col,a,drift=0.0):
    rng=np.random.default_rng(seed)
    for k in range(n):
        u=(rng.random()+drift*t*(0.6+0.4*rng.random()))%1.0; v=rng.random()
        x=lerp(x0+14,x1-14,u); y=lerp(y0+14,y1-14,v); r=9
        d.ellipse([x-r,y-r,x+r,y+r],fill=col+(a,))
def receptor_y(d,x,y,col,a,out=1.0):
    # an LDL receptor on the liver surface; out<1 = retracted (down-regulated)
    L_=34*out; d.line([(x,y),(x+L_,y)],fill=col+(a,),width=5)
    if out>0.3: d.line([(x+L_,y),(x+L_+14,y-14)],fill=col+(a,),width=5); d.line([(x+L_,y),(x+L_+14,y+14)],fill=col+(a,),width=5)
def heart(d,cx,cy,wall,t,a,col=CYAN,lit=None):
    ro=190; ri=ro-wall
    d.ellipse([cx-ro,cy-ro,cx+ro,cy+ro],outline=col+(a,),width=5); d.ellipse([cx-ri,cy-ri,cx+ri,cy+ri],outline=col+(a,),width=4)
    ring=Image.new('L',(W,H),0); rd=ImageDraw.Draw(ring); rd.ellipse([cx-ro,cy-ro,cx+ro,cy+ro],fill=70); rd.ellipse([cx-ri,cy-ri,cx+ri,cy+ri],fill=0)
    if GL: GL.ellipse([cx-ro,cy-ro,cx+ro,cy+ro],outline=col+(int(a*0.6),),width=10)
    for k in range(0,360,30):
        r1,r2=ri+4,ro-4; ang=math.radians(k); d.line([(cx+r1*math.cos(ang),cy+r1*math.sin(ang)),(cx+r2*math.cos(ang),cy+r2*math.sin(ang))],fill=col+(int(a*0.35),),width=2)
    d.text((cx-d.textlength('LV',font=f(BEB,64))/2,cy-36),'LV',font=f(BEB,64),fill=col+(a,))
    return ro,ri
def meter_row(d,x0,y,label,v,col,a,arrow=None):
    d.text((x0,y),label,font=f(BAR,34),fill=CREAM+(a,))
    meter(d,x0,y+46,XR-44,v,col,22)
    if arrow is not None: tri(d,XR-30,y+42,28,arrow,col+(a,))

# ================= v2 overlays: graphs, gauges, docking schematics, cards, full-screen scene =================
ORANGE=(255,122,26); MAGENTA=(255,46,140)
def grad_rect(lay,box,c_top,c_bot,a=255):
    x0,y0,x1,y1=[int(v) for v in box]
    if x1<=x0 or y1<=y0: return
    h=y1-y0; g=np.zeros((h,1,4),np.uint8)
    for i in range(h):
        k=i/max(1,h-1); g[i,0,:3]=[int(lerp(c_top[j],c_bot[j],k)) for j in range(3)]; g[i,0,3]=a
    lay.alpha_composite(Image.fromarray(np.repeat(g,x1-x0,1),'RGBA'),(x0,y0))
def glow_line(d,pts,col,w=6,a=255):
    d.line(pts,fill=col+(a,),width=w,joint='curve')
    if GL: GL.line(pts,fill=col+(int(a*0.8),),width=w*3,joint='curve')
def illus(d,x,y):
    d.text((x,y),'ILLUSTRATIVE',font=f(MONO,18),fill=LABEL+(200,))
# ---- tiny vector icons (line art, brand colours) ----
def ic_drop(d,cx,cy,s,col,a):
    d.polygon([(cx,cy-s),(cx+s*0.62,cy+s*0.15),(cx,cy+s*0.75),(cx-s*0.62,cy+s*0.15)],fill=col+(a,))
    d.ellipse([cx-s*0.62,cy-s*0.2,cx+s*0.62,cy+s*0.78],fill=col+(a,))
def ic_zz(d,cx,cy,s,col,a):
    fn=f(BEB,int(s*1.6)); d.text((cx-s*0.8,cy-s*0.9),'Z',font=fn,fill=col+(a,)); d.text((cx+s*0.05,cy-s*1.35),'z',font=f(BEB,int(s*1.1)),fill=col+(a,))
def ic_pulse(d,cx,cy,s,col,a):
    pts=[(cx-s,cy),(cx-s*0.4,cy),(cx-s*0.2,cy-s*0.7),(cx+s*0.1,cy+s*0.7),(cx+s*0.35,cy-s*0.3),(cx+s*0.5,cy),(cx+s,cy)]
    d.line(pts,fill=col+(a,),width=max(3,int(s*0.16)),joint='curve')
def ic_bolt(d,cx,cy,s,col,a):
    d.polygon([(cx+s*0.15,cy-s),(cx-s*0.5,cy+s*0.1),(cx-s*0.02,cy+s*0.1),(cx-s*0.2,cy+s),(cx+s*0.55,cy-s*0.15),(cx+s*0.05,cy-s*0.15)],fill=col+(a,))
def ic_flame(d,cx,cy,s,col,a):
    d.polygon([(cx,cy-s),(cx+s*0.6,cy+s*0.1),(cx+s*0.45,cy+s*0.8),(cx-s*0.45,cy+s*0.8),(cx-s*0.6,cy+s*0.1),(cx-s*0.15,cy-s*0.2)],fill=col+(a,))
    d.polygon([(cx,cy-s*0.1),(cx+s*0.28,cy+s*0.4),(cx,cy+s*0.75),(cx-s*0.28,cy+s*0.4)],fill=(255,230,150,a))
def ic_arrows_in(d,cx,cy,s,col,a):
    for ang in (0,90,180,270):
        r=math.radians(ang); x1,y1=cx+math.cos(r)*s,cy+math.sin(r)*s; x2,y2=cx+math.cos(r)*s*0.35,cy+math.sin(r)*s*0.35
        d.line([(x1,y1),(x2,y2)],fill=col+(a,),width=6); d.ellipse([x2-7,y2-7,x2+7,y2+7],fill=col+(a,))
    d.ellipse([cx-s*0.22,cy-s*0.22,cx+s*0.22,cy+s*0.22],outline=col+(a,),width=5)
def ic_N(d,cx,cy,s,col,a):
    d.ellipse([cx-s,cy-s,cx+s,cy+s],outline=col+(a,),width=6); fn=f(BEB,int(s*1.5)); d.text((cx-d.textlength('N',font=fn)/2,cy-s*0.78),'N',font=fn,fill=col+(a,))
def ic_shield(d,cx,cy,s,col,a):
    d.polygon([(cx,cy-s),(cx+s*0.8,cy-s*0.6),(cx+s*0.7,cy+s*0.3),(cx,cy+s),(cx-s*0.7,cy+s*0.3),(cx-s*0.8,cy-s*0.6)],outline=col+(a,),width=6)
def ic_muscle(d,cx,cy,s,col,a):
    for k in range(-2,3): d.ellipse([cx-s,cy+k*s*0.22-s*0.11,cx+s,cy+k*s*0.22+s*0.11],outline=col+(a,),width=3)
ICONS=[(ic_drop,CYAN),(ic_zz,(180,140,255)),(ic_pulse,RED),(ic_bolt,VGOLD)]

# -- HISTORY: dose bars (gradient) + side-effect load line with icon markers --
DOSES=[(400,10.51),(500,11.27),(600,11.79)]; SIDES=[('NIGHT SWEATS',13.55),('DESTROYED SLEEP',14.29),('TERRIBLE CARDIO',15.35),('MOOD CHANGES',16.79)]
def evA(d,t):    # dashboard: LED dose counter clicks 400 -> 500 -> 600, redline fills, warning lights come on
    lay=d._image; a=int(255*clamp((t-8.71)/0.15))
    d.rounded_rectangle([X0,560,XR,830],radius=26,fill=(8,8,12,int(a*0.9)),outline=MUTED+(int(a*0.5),),width=2)
    val=None
    for mg,tt in DOSES:
        if t>=tt: val=(mg,tt)
    d.text((X0+30,580),'DOSE · MG / WEEK · FOR YEARS',font=f(MONO,22),fill=LABEL+(a,))
    fn=f(MONOB,170)
    d.text((X0+30,600),'888',font=fn,fill=(40,12,8,a))
    if val:
        mg,tt=val; pop=1+0.08*math.exp(-(t-tt)*14); col=ORANGE if mg==400 else (RED if mg==600 else (255,80,30))
        d.text((X0+30,600),str(mg),font=fn,fill=col+(a,))
        if GL: GL.text((X0+30,600),str(mg),font=fn,fill=col+(int(170*math.exp(-(t-tt)*3)),))
    bx0,bx1=X0+30,XR-30; by=800
    d.rectangle([bx0,by-14,bx1,by],outline=MUTED+(int(a*0.4),),width=2)
    fill=0 if not val else {400:0.66,500:0.83,600:1.0}[val[0]]
    fq=ease_io((t-(val[1] if val else 0))/0.3) if val else 0
    prev={400:0.0,500:0.66,600:0.83}[val[0]] if val else 0
    f_=lerp(prev,fill,fq)
    for k in range(40):
        u=k/40
        if u>f_: break
        c=(255,int(lerp(190,20,u)),int(lerp(40,20,u))); d.rectangle([bx0+2+u*(bx1-bx0-4),by-12,bx0+2+(u+1/40)*(bx1-bx0-4)-3,by-2],fill=c+(a,))
    d.text((bx1-d.textlength('REDLINE',font=f(MONOB,20)),760),'REDLINE',font=f(MONOB,20),fill=RED+(a,))
    d.text((X0,862),'WARNING LIGHTS',font=f(MONO,24),fill=VGOLD+(int(255*clamp((t-13.40)/0.15)),))
    for i,(lab,tt) in enumerate(SIDES):
        q=expo((t-tt)/0.16); x0=X0+i*((XR-X0)/4)+8; x1=x0+(XR-X0)/4-16; y0,y1=904,1090
        on=q>0; aa=int(255*max(0.25,q)) if t>=13.0 else 0
        if aa<=0: continue
        lit=RED if i>=2 else (255,170,20)
        d.rounded_rectangle([x0,y0,x1,y1],radius=18,fill=((lit[0]//6,lit[1]//6,lit[2]//6) if on else (14,14,18))+(aa,),outline=(lit if on else MUTED)+(aa,),width=3)
        if on and GL: GL.rounded_rectangle([x0,y0,x1,y1],radius=18,outline=lit+(int(200*(0.6+0.4*math.sin(t*8+i))),),width=10)
        fn_,col=ICONS[i]; fn_(d,(x0+x1)/2,y0+70,30,lit if on else MUTED,aa)
        fw=f(MONOB,20); w1,w2=lab.split(' ',1)
        d.text(((x0+x1)/2-d.textlength(w1,font=fw)/2,y0+122),w1,font=fw,fill=CREAM+(aa,)); d.text(((x0+x1)/2-d.textlength(w2,font=fw)/2,y0+148),w2,font=fw,fill=CREAM+(aa,))

# -- THE QUESTION: dose-response curves; a marker slides from high dose to low dose --
def evC(d,t):
    gx0,gx1,gy0,gy1=X0+40,XR-20,600,1060
    a=int(255*clamp((t-33.45)/0.15))
    d.line([(gx0,gy0),(gx0,gy1),(gx1,gy1)],fill=MUTED+(a,),width=2)
    d.text((gx0,gy1+12),'LOW',font=f(MONO,20),fill=LABEL+(a,)); s='HIGH DOSE'; d.text((gx1-d.textlength(s,font=f(MONO,20)),gy1+12),s,font=f(MONO,20),fill=LABEL+(a,))
    eff=lambda u: 0.92*(1-math.exp(-7*u)); side=lambda u: 0.06+0.88*u**2.4
    P_=lambda fn,u:(lerp(gx0,gx1,u),gy1-(gy1-gy0)*fn(u))
    qe=ease_io((t-33.60)/0.8); qs=ease_io((t-33.90)/0.8)
    if qe>0: glow_line(d,[P_(eff,k/80*qe) for k in range(81)],VGOLD,6)
    if qs>0: glow_line(d,[P_(side,k/80*qs) for k in range(81)],RED,6)
    if qe>=1: d.text((gx0+20,gy0-6),'ANDROGENIC EFFECT',font=f(MONOB,22),fill=VGOLD+(255,))
    if qs>=1: s='SIDE EFFECTS'; d.text((gx1-d.textlength(s,font=f(MONOB,22)),gy0+60),s,font=f(MONOB,22),fill=RED+(255,))
    if t>=34.35:
        u=lerp(0.95,0.12,ease_io((t-34.35)/1.9)); x=lerp(gx0,gx1,u)
        d.line([(x,gy0-10),(x,gy1)],fill=CYAN+(255,),width=3)
        if GL: GL.line([(x,gy0-10),(x,gy1)],fill=CYAN+(200,),width=8)
        for fn_,col in ((eff,VGOLD),(side,RED)):
            xx,yy=P_(fn_,u); d.ellipse([xx-11,yy-11,xx+11,yy+11],fill=col+(255,))
        d.text((x+10,gy1-40),'DOSE',font=f(MONOB,22),fill=CYAN+(255,))
    if t>=38.99: gold_tag(d,X0,1110,'EFFECT HOLDS?',26)
    if t>=41.91: red_tag(d,XR,1110,'SIDES DROP',26,right=True)
    illus(d,XR-150,1200)

# -- MECHANISM: rating gauge, lock-and-key AR dock, glucocorticoid shield --
def gauge(d,cx,cy,r,val,col,a,label):
    d.arc([cx-r,cy-r,cx+r,cy+r],180,360,fill=MUTED+(int(a*0.4),),width=16)
    end=180+180*clamp(val/600)
    d.arc([cx-r,cy-r,cx+r,cy+r],180,end,fill=col+(a,),width=16)
    if GL: GL.arc([cx-r,cy-r,cx+r,cy+r],180,end,fill=col+(int(a*0.7),),width=30)
    ang=math.radians(end); d.line([(cx,cy),(cx+math.cos(ang)*(r-30),cy+math.sin(ang)*(r-30))],fill=CREAM+(a,),width=6); d.ellipse([cx-12,cy-12,cx+12,cy+12],fill=CREAM+(a,))
    fn=f(BEB,64); s=str(int(val)); d.text((cx-d.textlength(s,font=fn)/2,cy+10),s,font=fn,fill=col+(a,))
    fn=f(MONO,22); d.text((cx-d.textlength(label,font=fn)/2,cy+80),label,font=fn,fill=CREAM+(a,))
def dock(d,cx,cy,col,a,q,ripples=0,label='',blocked=False):
    # receptor socket (U) + ligand key dropping in
    d.line([(cx-70,cy-60),(cx-70,cy+40),(cx-24,cy+40),(cx-24,cy),(cx+24,cy),(cx+24,cy+40),(cx+70,cy+40),(cx+70,cy-60)],fill=col+(a,),width=6)
    ky=lerp(cy-150,cy-4,q)
    d.rectangle([cx-20,ky-60,cx+20,ky],fill=(VGOLD if not blocked else RED)+(a,))
    for k in range(ripples):
        rr=60+k*26; d.arc([cx-rr,cy-20-rr,cx+rr,cy-20+rr],200,340,fill=VGOLD+(int(a*(1-k/5)),),width=3)
    fn=f(MONOB,20); d.text((cx-d.textlength(label,font=fn)/2,cy+56),label,font=fn,fill=col+(a,))
def evD(d,t):
    q=expo((t-63.85)/0.14)
    if q>0: gold_tag(d,X0,556,'19-NOR',26)
    if t>=65.39:
        a=int(255*clamp((t-65.39)/0.15)); d.text((540-d.textlength('ANDROGENIC RATING',font=f(MONO,22))/2,560),'ANDROGENIC RATING',font=f(MONO,22),fill=LABEL+(a,))
        gauge(d,300,780,150,lerp(0,100,ease_io((t-65.6)/0.4)),CREAM,a,'TESTOSTERONE')
        gauge(d,720,780,150,lerp(0,500,ease_io((t-66.49)/0.8)),VGOLD,a,'TREN')
        if t>=67.49: fn=f(BEB,80); d.text((540-d.textlength('5×',font=fn)/2,640),'5×',font=fn,fill=VGOLD+(int(255*clamp((t-67.49)/0.15)),))
    if t>=70.47:
        a=int(255*clamp((t-70.47)/0.15)); d.line([(X0,905),(XR,905)],fill=MUTED+(int(a*0.3),),width=2)
        rp=int(clamp((t-72.19)/0.5)*5)
        dock(d,300,1060,VGOLD,a,ease_io((t-70.47)/0.5),rp,'ANDROGEN RECEPTOR · 5× AFFINITY')
    if t>=75.19:
        a=int(255*clamp((t-75.19)/0.15))
        dock(d,780,1060,CYAN,a,ease_io((t-75.19)/0.5),0,'GLUCOCORTICOID RECEPTOR')
        if t>=78.41:
            s=expo((t-78.41)/0.2); ic_shield(d,920,960,48*s,GREEN,int(255*s)); ic_muscle(d,920,962,26*s,GREEN,int(255*s))
            if GL: GL.ellipse([870,910,970,1010],outline=GREEN+(int(160*s),),width=8)
            gold_tag(d,XR,1140,'ANTI-CATABOLIC',24,right=True)

# -- PROTOCOL: dose tube 600 -> 25-50 window, receptor-activation donut, icon tiles, callback of the sides struck out --
def evE(d,t):
    a=int(255*clamp((t-83.65)/0.15)); cx=X0+95
    R6=88; R50=R6*math.sqrt(50/600); R25=R6*math.sqrt(25/600)
    q6=ease_io((t-83.65)/0.35)
    if q6>0:
        d.ellipse([cx-R6*q6,690-R6*q6,cx+R6*q6,690+R6*q6],fill=(120,10,10,int(a*0.55)),outline=RED+(a,),width=4)
        fn=f(BEB,64); d.text((cx-d.textlength('600',font=fn)/2,656),'600',font=fn,fill=CREAM+(a,))
        d.text((cx-d.textlength('THE OLD WAY',font=f(MONO,18))/2,792),'THE OLD WAY',font=f(MONO,18),fill=RED+(a,))
    if t>=84.15:
        q=expo((t-84.15)/0.25); cy=960
        d.line([(cx,830),(cx,cy-R50-16)],fill=MUTED+(int(a*0.6),),width=3); d.polygon([(cx-10,cy-R50-24),(cx+10,cy-R50-24),(cx,cy-R50-8)],fill=MUTED+(a,))
        d.ellipse([cx-R50*q,cy-R50*q,cx+R50*q,cy+R50*q],outline=VGOLD+(a,),width=3)
        d.ellipse([cx-R25*q,cy-R25*q,cx+R25*q,cy+R25*q],fill=VGOLD+(a,))
        if GL: GL.ellipse([cx-R50-8,cy-R50-8,cx+R50+8,cy+R50+8],outline=VGOLD+(int(200*q),),width=10)
        fs=f(MONOB,22); d.text((cx-d.textlength('25–50',font=fs)/2,cy+R50+12),'25–50',font=fs,fill=VGOLD+(a,))
        d.text((cx-d.textlength('AREA TO SCALE',font=f(MONO,16))/2,cy+R50+42),'AREA TO SCALE',font=f(MONO,16),fill=LABEL+(a,))
    q=expo((t-83.59)/0.18)
    if q>0:
        fn=f(BEB,120); d.text((330,560),'25–50',font=fn,fill=VGOLD+(int(255*q),)); d.text((330,676),'MG / WEEK · TO START',font=f(MONOB,24),fill=CREAM+(int(255*q),))
    if t>=87.09:   # receptor activation donut
        s=ease_io((t-87.09)/0.8); cx,cy,r=470,830,80
        d.ellipse([cx-r,cy-r,cx+r,cy+r],outline=MUTED+(80,),width=18)
        d.arc([cx-r,cy-r,cx+r,cy+r],-90,-90+300*s,fill=GREEN+(255,),width=18)
        if GL: GL.arc([cx-r,cy-r,cx+r,cy+r],-90,-90+300*s,fill=GREEN+(180,),width=34)
        d.text((cx+110,cy-44),'AR ACTIVATION',font=f(MONOB,24),fill=CREAM+(255,)); d.text((cx+110,cy-8),'MEANINGFUL',font=f(MONO,22),fill=GREEN+(255,))
        if t>=91.25: d.text((cx+110,cy+26),'FROM TRACE AMOUNTS',font=f(MONO,22),fill=CYAN+(int(255*clamp((t-91.25)/0.15)),))
    AX=[('PARTITIONING',97.07),('NITROGEN',98.61),('FAT OXIDATION',100.11),('LOW SIDES',102.43)]
    cx,cy,R=610,1040,110
    if t>=96.9:
        a0=int(255*clamp((t-96.9)/0.2))
        for ring in (0.33,0.66,1.0):
            pts=[(cx+R*ring*math.cos(math.radians(-90+90*k)),cy+R*ring*math.sin(math.radians(-90+90*k))) for k in range(5)]
            d.line(pts,fill=MUTED+(int(a0*0.35),),width=2)
        for k,(lab,tt) in enumerate(AX):
            ang=math.radians(-90+90*k); ex,ey=cx+R*math.cos(ang),cy+R*math.sin(ang); d.line([(cx,cy),(ex,ey)],fill=MUTED+(int(a0*0.35),),width=2)
            on=t>=tt; fn=f(MONOB,18); tw=d.textlength(lab,font=fn)
            lx=ex-tw/2+(0 if k%2==0 else (14+tw/2 if k==1 else -14-tw/2)); ly=ey+(-28 if k==0 else 8 if k==2 else -10)
            d.text((lx,ly),lab,font=fn,fill=(GREEN if on else LABEL)+(a0,))
        def poly(vals,col,fill_a,line_a,grow):
            pts=[(cx+R*v*grow*math.cos(math.radians(-90+90*k)),cy+R*v*grow*math.sin(math.radians(-90+90*k))) for k,v in enumerate(vals)]
            d.polygon(pts,fill=col+(fill_a,)); d.line(pts+[pts[0]],fill=col+(line_a,),width=4)
            if GL: GL.line(pts+[pts[0]],fill=col+(int(line_a*0.7),),width=10)
        poly([0.92,0.9,0.88,0.14],RED,50,int(220*a0/255),ease_io((t-96.9)/0.5))
        n=sum(1 for _,tt in AX if t>=tt); mv=[0.88 if k<n else 0.12 for k in range(3)]+[0.9 if n>=4 else 0.12]
        poly(mv,VGOLD,70,a0,1.0)
        d.rectangle([846,940,864,958],fill=RED+(a0,)); d.text((870,936),'600 MG',font=f(MONOB,20),fill=CREAM+(a0,))
        d.rectangle([846,972,864,990],fill=VGOLD+(a0,)); d.text((870,968),'25–50',font=f(MONOB,20),fill=CREAM+(a0,))
        illus(d,846,1004)
    if t>=102.43:   # callback: the history icons, struck out
        q=expo((t-102.43)/0.16); y=1196
        d.text((300,y+8),"NOT GETTING",font=f(MONOB,22),fill=RED+(int(255*q),))
        for i,(fn_,col) in enumerate(ICONS):
            cx=520+i*110; fn_(d,cx,y+20,20,col,int(200*q))
            sq=expo((t-102.43-0.08*i)/0.14); d.line([(cx-26,y+46),(lerp(cx-26,cx+26,sq),y-6)],fill=RED+(255,),width=6)
CONTENT={0:[(8.29,evA)],1:[(33.33,evC)],2:[(63.03,evD)],3:[(83.59,evE)]}
SHAKES=[]
for _,tt in DOSES: sfx(tt,'tick',g=-26)
for _,tt in SIDES: sfx(tt,'tick',g=-30)
sfx(13.40,'scan',d=1.2,g=-34)
sfx(33.60,'scan',d=0.8,g=-32); sfx(34.35,'scan',d=1.9,g=-33); sfx(38.99,'tick',g=-27); sfx(41.91,'tick',g=-27)
sfx(63.85,'tick',g=-28); sfx(66.49,'scan',d=0.8,g=-31); sfx(67.49,'thud',w=1.4,g=-17); sfx(70.97,'thud',w=1.1,g=-19); sfx(72.19,'scan',d=0.5,g=-32); sfx(75.69,'thud',w=1.0,g=-20); sfx(78.41,'tick',g=-26)
sfx(83.69,'scan',d=1.0,g=-31); sfx(84.15,'thud',w=1.4,g=-17); sfx(87.09,'scan',d=0.8,g=-32); sfx(97.07,'tick',g=-29); sfx(98.61,'tick',g=-29); sfx(100.11,'tick',g=-29); sfx(102.43,'tick',g=-24)

# ---- full-screen EVIDENCE scene (18.29-27.95): report sheets stack, 500+ counter, 10+ yr ring ----
EV_IN,EV_OUT=17.92,27.95
sfx(EV_IN,'whoosh',d=0.25,g=-28); sfx(20.09,'thud',w=1.2,g=-19); sfx(21.77,'tick',g=-29); sfx(23.21,'tick',g=-29); sfx(25.53,'scan',d=0.6,g=-31); sfx(26.05,'impact',g=-15); sfx(EV_OUT-0.05,'whoosh',d=0.2,g=-30)
_SHEET=None
def sheet():
    global _SHEET
    if _SHEET is None:
        im=Image.new('RGBA',(300,390),(250,249,246,255)); d=ImageDraw.Draw(im)
        d.rectangle([0,0,299,46],fill=(210,10,20,255)); d.text((14,8),'BLOODWORK PANEL',font=f(BEB,34),fill=(255,255,255,255))
        rng=np.random.default_rng(9)
        for k in range(9):
            y=66+k*34; d.rectangle([16,y,16+int(rng.integers(90,150)),y+12],fill=(70,72,80,255)); d.rectangle([200,y,200+int(rng.integers(30,70)),y+12],fill=(150,150,156,255))
        d.rectangle([0,0,299,389],outline=(150,148,140,255),width=2); _SHEET=im
    return _SHEET
def evidence_scene(im,t):
    if t<EV_IN or t>EV_OUT+0.25: return
    a=ease_io((t-EV_IN)/0.25)*(1-ease_io((t-EV_OUT)/0.25))
    im.alpha_composite(scene_bg(a)); L,d=newL(); A=int(255*a)
    # 10+ years ring
    s=ease_io((t-20.09)/0.7)
    if s>0:
        cx,cy,r=230,560,110; d.ellipse([cx-r,cy-r,cx+r,cy+r],outline=MUTED+(int(60*a),),width=14)
        d.arc([cx-r,cy-r,cx+r,cy+r],-90,-90+360*s,fill=VGOLD+(A,),width=14)
        if GL: GL.arc([cx-r,cy-r,cx+r,cy+r],-90,-90+360*s,fill=VGOLD+(int(170*a),),width=28)
        fn=f(BEB,96); d.text((cx-d.textlength('10+',font=fn)/2,cy-56),'10+',font=fn,fill=CREAM+(A,)); fs=f(MONOB,22); d.text((cx-d.textlength('YEARS',font=fs)/2,cy+34),'YEARS',font=fs,fill=VGOLD+(A,))
        d.text((cx+150,cy-40),'COACHING',font=f(BEB,72),fill=CREAM+(A,))
    for i,(lab,tt) in enumerate((('ANECDOTAL EVIDENCE',21.77),('CLINICAL RESEARCH',23.21))):
        q=expo((t-tt)/0.16)
        if q<=0: continue
        x=380+i*0; y=520+80+i*56; check(d,x,y+8,GREEN+(int(A*q),),5,1.0); d.text((x+40,y),lab,font=f(BAR,40),fill=CREAM+(int(A*q),))
    im.alpha_composite(L)
    # sheets fan in from the right and stack
    n=int(clamp((t-24.40)/1.6)*14)
    for k in range(n):
        p=clamp((t-24.40-k*0.11)/0.25); pe=1-(1-p)**3
        sh=sheet().rotate(-14+k*2.1,expand=True,resample=Image.BICUBIC)
        x=int(lerp(1150,180+k*26,pe)); y=int(lerp(820,800-k*10,pe)); sh.putalpha(sh.split()[3].point(lambda v:int(v*a*min(1,p*2))))
        im.alpha_composite(sh,(x,y))
    L,d=newL()
    q=expo((t-25.53)/0.18)
    if q>0:
        nn=int(lerp(0,500,ease_io((t-25.53)/0.6))); fn=f(BEB,300); s=f'{nn}+' if nn>=500 else str(nn)
        tw=d.textlength('500+',font=fn); x=1016-tw
        d.text((x,1000),s,font=fn,fill=VGOLD+(int(A*q),))
        if GL: GL.text((x,1000),s,font=fn,fill=VGOLD+(int(150*a*q),))
        if t>=25.95: fs=f(BEB,72); d.text((1016-d.textlength('BLOODWORK PANELS',font=fs),1300),'BLOODWORK PANELS',font=fs,fill=CREAM+(int(A*clamp((t-25.95)/0.15)),))
    im.alpha_composite(L)

# ---- side cards: frosted, gold brackets, slide in from the edge ----
def card(im,t,box,t0,t1,draw,frm='left'):
    if t<t0 or t>t1+0.2: return
    q=expo((t-t0)/0.22); o=ease_io((t-t1)/0.2); x0,y0,x1,y1=box; w=x1-x0
    dx=(-(w+60) if frm=='left' else (w+60) if frm=='right' else 0)*(1-q)+(-(w+60) if frm=='left' else (w+60) if frm=='right' else 0)*o
    dy=(-40 if frm=='top' else 0)*(1-q)
    bx=(x0+dx,y0+dy,x1+dx,y1+dy); a=int(255*min(q,1-o))
    if a<=0: return
    frosted(im,bx,0.88*a/255,12); L,d=newL()
    d.rectangle(bx,outline=VGOLD+(int(a*0.7),),width=2); brackets(d,*bx,VGOLD+(a,),26,5)
    if GL: brackets(GL,*bx,VGOLD+(a,),24,10)
    draw(d,bx,t,a); im.alpha_composite(L)
def draw_mol(d,bx,t,a):
    x0,y0,x1,y1=bx; cx,cy,r=x0+120,(y0+y1)/2+4,26
    hexes=[(cx-3*r,cy),(cx-1.3*r,cy-r*0.98),(cx+0.4*r,cy),(cx+2.1*r,cy-r*0.55)]
    for i,(hx,hy) in enumerate(hexes):
        n=6 if i<3 else 5; pts=[(hx+r*math.cos(math.radians(60*k+30 if n==6 else 72*k-90)),hy+r*math.sin(math.radians(60*k+30 if n==6 else 72*k-90))) for k in range(n+1)]
        d.line(pts,fill=CYAN+(a,),width=4)
        if GL: GL.line(pts,fill=CYAN+(int(a*0.7),),width=9)
    q=expo((t-31.53)/0.16)
    if q>0:
        mx,my=cx-1.3*r,cy-r*0.98-r; d.ellipse([mx-12,my-12,mx+12,my+12],outline=RED+(int(a*q),),width=4); d.line([(mx-14,my-14),(mx+14,my+14)],fill=RED+(int(a*q),),width=4)
        d.text((x0+260,y0+22),'19-NOR',font=f(BEB,64),fill=VGOLD+(int(a*q),))
        d.text((x0+262,y0+88),'ANABOLIC STEROID · EXTREMELY POTENT',font=f(MONO,20),fill=CREAM+(int(a*clamp((t-32.15)/0.15)),))
def draw_sleep(d,bx,t,a):
    x0,y0,x1,y1=bx; cx,cy,r=(x0+x1)/2,y0+150,95
    d.text((x0+24,y0+18),'SLEEP',font=f(MONOB,24),fill=CREAM+(a,)); d.text((x1-24-d.textlength('LAST NIGHT',font=f(MONO,20)),y0+22),'LAST NIGHT',font=f(MONO,20),fill=LABEL+(a,))
    d.ellipse([cx-r,cy-r,cx+r,cy+r],outline=MUTED+(int(a*0.3),),width=16)
    s=ease_io((t-49.40)/0.6); d.arc([cx-r,cy-r,cx+r,cy+r],-90,-90+360*(0.5/8)*s,fill=RED+(a,),width=16)
    if GL: GL.arc([cx-r,cy-r,cx+r,cy+r],-90,-90+360*(0.5/8)*s,fill=RED+(int(a*0.8),),width=30)
    fn=f(BEB,72); s_='0H 30M'; d.text((cx-d.textlength(s_,font=fn)/2,cy-40),s_,font=fn,fill=RED+(a,))
    d.text((cx-d.textlength('A NIGHT',font=f(MONO,20))/2,cy+38),'A NIGHT',font=f(MONO,20),fill=LABEL+(a,))
    if t>=48.89: red_tag(d,(x0+x1)/2+70,y1-62,'NO GROWTH',22,right=True)
def draw_dna(d,bx,t,a):
    x0,y0,x1,y1=bx; cx=(x0+x1)/2; ph=t*3
    for k in range(26):
        y=y0+40+k*(y1-y0-90)/25; w=70*math.sin(k*0.5+ph)
        xa,xb=cx-w,cx+w; d.ellipse([xa-6,y-6,xa+6,y+6],fill=CYAN+(a,)); d.ellipse([xb-6,y-6,xb+6,y+6],fill=MAGENTA+(a,))
        if k%2==0: d.line([(xa,y),(xb,y)],fill=MUTED+(int(a*0.5),),width=2)
    fn=f(MONOB,22); s='GENETIC'; d.text((cx-d.textlength(s,font=fn)/2,y1-46),s,font=fn,fill=CREAM+(a,))
def cards(im,t):
    card(im,t,(64,392,1016,532),30.10,33.20,draw_mol,'top')
    card(im,t,(40,600,410,1000),49.20,53.60,draw_sleep,'left')
    card(im,t,(40,560,300,960),61.00,62.95,draw_dna,'left')
sfx(30.10,'whoosh',d=0.2,g=-30); sfx(31.53,'tick',g=-26); sfx(49.20,'whoosh',d=0.2,g=-30); sfx(49.40,'tick',g=-25); sfx(61.0,'whoosh',d=0.2,g=-31)










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

# ---- TEXT HOOK (editing/TEXT_HOOK_ENGINE.md): fully visible on frame 0, no entry animation, 0.15 s fade out;
#      then a compact topic band until the midpoint (nearest jump cut), then the top stays clear ----
NEWTL=True
HOOK_LINES=[[('HEMATOCRIT',VGOLD),(' 57% to 49%',CREAM)],[('no blood donation',CREAM)]]
HOOK_END=6.00; HOOK_FADE=0.15; HOOK_Y=262
THO=(HOOK_END,HOOK_END+HOOK_FADE)
_mid=DUR/2; _nc=min(CUTS,key=lambda c:abs(c-_mid)); BAND_OUT=_nc if abs(_nc-_mid)<=1.5 else _mid      # nearest jump cut if within 1.5 s, else fade at the midpoint
sfx(HOOK_END,'whoosh',d=0.25,g=-30)
def hook_lines(d,y0,fn,a):
    lh=fn.size+18
    for k,parts in enumerate(HOOK_LINES):
        tw=sum(d.textlength(s,font=fn) for s,_ in parts); x=500-tw/2; y=y0+k*(lh+10)
        d.rounded_rectangle([x-24,y-6,x+tw+24,y+lh-4],radius=14,fill=(0,0,0,int(a*0.78)))
        for s,c in parts: d.text((x,y),s,font=fn,fill=c+(a,)); x+=d.textlength(s,font=fn)
def hook_band(im,t):
    L,d=newL()
    if t<HOOK_END+HOOK_FADE:
        a=int(255*(1-clamp((t-HOOK_END)/HOOK_FADE))); hook_lines(d,HOOK_Y,f(BAR,84),a)
    bin_=clamp((t-HOOK_END)/HOOK_FADE); bout=1-clamp((t-BAND_OUT)/0.15); v=bin_*bout*(1-B_push(t))
    if v>0 and t>=HOOK_END:
        B,bd=newL(); bd.rectangle([8,212,W,372],fill=NAVY+(int(235*v),)); im.alpha_composite(B)
        a=int(255*v); fn=f(BAR,64); x=64; y=236
        for s,c in [('HEMATOCRIT',VGOLD),(' without donating',CREAM)]: d.text((x,y),s,font=fn,fill=c+(a,)); x+=d.textlength(s,font=fn)
        fs=f(MONO,24); s='@coach.agz'; d.text((1016-d.textlength(s,font=fs),226),s,font=fs,fill=GOLD+(a,))
        d.text((64,334),DISC,font=f(MONO,18),fill=LABEL+(a,))
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
NEWTL=False
END=105.87; PILL=113.05; FREE=116.49
sfx(END,'scan',d=0.30,g=-29); sfx(107.07,'tick',g=-30); sfx(PILL-0.05,'whoosh',d=0.22,g=-27); sfx(PILL+0.10,'thud',w=1.6,g=-14); sfx(FREE,'tick',g=-27)
def end_card(im,t):
    if t<END: return
    a=ease_io((t-END)/0.30); im.alpha_composite(scene_bg(a))
    q=expo((t-END-0.15)/0.25)
    if q<=0: return
    lg=logo().copy(); lg.putalpha(lg.split()[3].point(lambda v:int(v*q))); im.alpha_composite(lg,(540-120,214))
    L,d=newL(); A=int(255*q)
    fn=f(BAR,40); s='COACH AGZ'; w=tracked_w(d,s,fn,10); tracked(d,(540-w/2,466),s,fn,GOLD+(A,),10)
    fn=f(MONO,28); s='@coach.agz'; d.text((540-d.textlength(s,font=fn)/2,522),s,font=fn,fill=MUTED+(A,))
    kq=expo((t-106.73)/0.2)
    if kq>0: fn=f(BAR,36); s='MY FULL'; w=tracked_w(d,s,fn,8); tracked(d,(540-w/2,610),s,fn,GOLD+(int(255*kq),),8)
    for s,tt,y,sz,col in [('TREN MICRODOSE',107.07,652,112,VGOLD),('PROTOCOL',107.85,766,96,CREAM)]:
        hq=expo((t-tt)/0.16)
        if hq<=0: continue
        fn=f(BEB,sz); d.text((540-d.textlength(s,font=fn)/2,y+12*(1-hq)),s,font=fn,fill=col+(int(255*hq),))
    x0=540; parts=[('COMPOUND SELECTION',108.53),('ANCILLARIES',109.53),('BLOODWORK MARKERS',110.61)]
    fn=f(MONOB,26); sep='  ·  '; full=sep.join(p for p,_ in parts); x=540-d.textlength(full,font=fn)/2
    for i,(p,tt) in enumerate(parts):
        if t>=tt: d.text((x,880),p,font=fn,fill=MUTED+(int(255*clamp((t-tt)/0.15)),))
        x+=d.textlength(p+(sep if i<2 else ''),font=fn)
    im.alpha_composite(L); L,d=newL()
    pq=expo((t-PILL)/0.20)
    if pq>0:
        fn=f(MONOB,58); s='COMMENT "MICRO"'; tw=d.textlength(s,font=fn); bw=tw+80; x0=540-bw/2; y0=940+lerp(-40,0,pq)
        if GL and t<PILL+0.6: GL.rectangle([x0,y0,x0+bw,y0+120],outline=VGOLD+(int(220*(1-(t-PILL)/0.6)),),width=10)
        lit_bar(d,x0,y0,x0+bw,y0+120,VGOLD,int(255*min(1,pq*1.5)))
        im.alpha_composite(L); L,d=newL()
        tq=clamp((t-PILL-0.08)/0.12)
        if tq>0: d.text((540-tw/2,y0+24),s,font=fn,fill=DEEP+(int(255*tq),))
    fq=expo((t-FREE)/0.14)
    if fq>0:
        fn=f(MONOB,36); s='SENT TO YOU · '; s2='FREE'; tw=d.textlength(s+s2,font=fn); x=540-tw/2
        d.text((x,1084),s,font=fn,fill=CREAM+(int(255*fq),)); d.text((x+d.textlength(s,font=fn),1084),s2,font=fn,fill=VGOLD+(int(255*fq),))
    fn=f(MONO,20); d.text((540-d.textlength(DISC,font=fn)/2,1150),DISC,font=fn,fill=LABEL+(A,))
    im.alpha_composite(L)


# ---- NEW (take 3): opening card, "instead of running 500 mg a week ... while maximizing the growth effects" ----
NEWTL=True
OC_IN,OC_OUT=6.05,8.05
sfx(OC_IN,'whoosh',d=0.2,g=-29); sfx(6.30,'thud',w=1.1,g=-19); sfx(6.68,'tick',g=-24)
def open_card(im,t):
    if t<OC_IN or t>OC_OUT+0.2: return
    q=expo((t-OC_IN)/0.22); o=ease_io((t-OC_OUT)/0.2); a=int(255*min(q,1-o))
    if a<=0: return
    L,d=newL()
    for side,(x0,x1,mg,lab,col,good,tt) in enumerate(((40,500,'25','UPSIDE',VGOLD,True,6.05),(580,1040,'400','NIGHTMARE',RED,False,6.30))):
        qq=expo((t-tt)/0.2); dx=(-1 if side==0 else 1)*500*(1-qq)+(-1 if side==0 else 1)*500*o; aa=int(a*qq)
        if aa<=0: continue
        bx=(x0+dx,396,x1+dx,606)   # under the topic band, over the top of the cap: clear of eyes, mouth and the bottom UI zone
        frosted(im,bx,0.9*aa/255,10)
        d.rectangle(bx,outline=col+(aa,),width=3)
        if GL: GL.rectangle(bx,outline=col+(int(aa*0.7),),width=10)
        fn=f(BEB,104); cx=(bx[0]+bx[2])/2; s_=mg; w_=d.textlength(s_,font=fn)+d.textlength(' MG',font=f(BEB,52))
        d.text((cx-w_/2,bx[1]+12),s_,font=fn,fill=col+(aa,)); d.text((cx-w_/2+d.textlength(s_,font=fn),bx[1]+48),' MG',font=f(BEB,52),fill=CREAM+(aa,))
        fl=f(MONOB,30); lw=d.textlength(lab,font=fl)+44
        d.text((cx-lw/2,bx[1]+142),lab,font=fl,fill=CREAM+(aa,))
        if good: tri(d,cx+lw/2-30,bx[1]+146,30,True,GREEN+(aa,))
        else:
            xx=cx+lw/2-20; yy=bx[1]+162; d.line([(xx-14,yy-14),(xx+14,yy+14)],fill=RED+(aa,),width=6); d.line([(xx+14,yy-14),(xx-14,yy+14)],fill=RED+(aa,),width=6)
    fv=f(BEB,90); vq=expo((t-6.30)/0.16)
    if vq>0: d.text((540-d.textlength('VS',font=fv)/2,450),'VS',font=fv,fill=CREAM+(int(a*vq),))
    im.alpha_composite(L)
NEWTL=False



# ======================= "HCT no Donation" overlay set (neon) =======================
EVB=[]
def sfxb(t,kind,**k): EVB.append(dict(t=round(t,3),kind=kind,**k))
import re as _re2
def at(word,near):
    n=lambda s:_re2.sub(r'[^a-z0-9]','',s.lower()); best=None
    for w in words:
        if n(w['w']).startswith(n(word)) and abs(w['s']-near)<3.5 and (best is None or abs(w['s']-near)<abs(best-near)): best=w['s']
    if best is None: raise SystemExit('word not found: %s @%s'%(word,near))
    return best
MINT=(40,255,200); HOT=(255,50,110); LIME=(190,255,60); SKY=(70,170,255); PURP=(170,90,255); AMBER=(255,170,20)
def kinetic(d,txt,fn,x,y,t0,t,col,frm=-1,dur=0.22):
    q=expo((t-t0)/dur)
    if q<=0: return 0
    w=d.textlength(txt,font=fn); xx=x+frm*(1-q)*(W+w)
    d.text((xx,y),txt,font=fn,fill=col+(int(255*min(1,q*1.4)),))
    if GL: GL.text((xx,y),txt,font=fn,fill=col+(int(120*min(1,q)),))
    return q
def ctext(d,txt,fn,cx,y,col,a,glow=False):
    x=cx-d.textlength(txt,font=fn)/2; d.text((x,y),txt,font=fn,fill=col+(a,))
    if glow and GL: GL.text((x,y),txt,font=fn,fill=col+(int(a*0.7),))
def nline(d,pts,col,w,a):
    if len(pts)<2: return
    d.line(pts,fill=col+(a,),width=w,joint='curve')
    if GL: GL.line(pts,fill=col+(int(a*0.9),),width=w*3,joint='curve')
def nrect(d,box,col,a,w=4,r=18):
    d.rounded_rectangle(box,radius=r,outline=col+(a,),width=w)
    if GL: GL.rounded_rectangle(box,radius=r,outline=col+(int(a*0.9),),width=w*3)
def pill(d,cx,y,txt,fn,bg,fg,a):
    w=d.textlength(txt,font=fn); h=fn.size+18; lit_bar(d,cx-w/2-18,y,cx+w/2+18,y+h,bg,a); d.text((cx-w/2,y+8),txt,font=fn,fill=fg+(a,))
def float_a(t,t0,t1): return expo((t-t0)/0.25)*(1-ease_io((t-t1)/0.2)) if t0<=t<=t1+0.2 else 0
def scene_a(t,win): return clamp((t-win[0])/0.2)*(1-ease_io((t-win[1])/0.22))
S_FLOW=(at('most',17.1)-0.05, at('realistically',23.5)-0.05)
S_PROB=(at('realistically',23.5)-0.05, at('that',37.2)-0.05)
S_TUBE=(at('very',41.5)-0.05, at('secondarily',51.9)-0.05)
S_ECG=(at('secondarily',51.9)-0.05, at('and',60.5)-0.05)
S_GAUGE=(at('here',69.0)-0.05, at('to',79.9)-0.05)
S_EQ=(at('lowering',85.0)-0.05, at('because',88.6)-0.05)
S_AGE=(at('because',88.6)-0.05, at('now',97.5)-0.05)
SCENES=[S_FLOW,S_PROB,S_TUBE,S_ECG,S_GAUGE,S_EQ,S_AGE]
def B_push(t):
    g=0
    for a_,b_ in SCENES: g=max(g,clamp((t-a_)/0.22)*clamp((b_-t)/0.22))
    return ease_io(g)
for i,(a_,b_) in enumerate(SCENES):
    if i==0 or abs(a_-SCENES[i-1][1])>0.3: sfxb(a_,'whoosh',d=0.22,g=-28)
    sfxb(a_+0.2,'thud',w=1.2,g=-18)

# 1) mirror vs bloodwork (floating, top)
MB0=at('because',12.4); MB1=S_FLOW[0]-0.05; MB_BEAST=at('beast',13.5); MB_BW=at('bloodwork',14.6); MB_DIFF=at('different',16.2)
sfxb(MB_BEAST,'tick',g=-26); sfxb(MB_BW,'tick',g=-26); sfxb(MB_DIFF,'tick',g=-23)
def mirror(L,d,t):
    a=int(255*float_a(t,MB0,MB1))
    if a<=0: return
    d.rounded_rectangle([40,392,1040,700],radius=22,fill=(4,6,14,int(a*0.86)))
    nrect(d,(70,420,520,640),MINT,a); nrect(d,(560,420,1010,640),HOT,a)
    ctext(d,'THE MIRROR',f(MONOB,26),295,438,MINT,a)
    if t>=MB_BEAST: ctext(d,'LOOKS GREAT',f(BEB,84),295,500,MINT,a,True)
    ctext(d,'THE BLOODWORK',f(MONOB,26),785,438,HOT,a)
    if t>=MB_BW: ctext(d,'HCT  HIGH',f(BEB,84),785,500,HOT,a,True)
    if t>=MB_DIFF: pill(d,540,648,'TOTALLY DIFFERENT STORY',f(MONOB,24),HOT,(255,255,255),a)

# 2) flowchart: HCT up -> clinic -> donate
F_SEE=at('elevated',19.6); F_DON=at('donate',22.6)
sfxb(F_SEE,'tick',g=-25); sfxb(F_DON,'thud',w=1.4,g=-17)
def flow(L,d,t):
    if t<S_FLOW[0] or t>S_FLOW[1]+0.25: return
    a=int(255*scene_a(t,S_FLOW))
    kinetic(d,'THE USUAL PLAYBOOK',f(BEB,96),80,400,S_FLOW[0]+0.1,t,SKY,-1)
    nodes=[('HCT UP',620,HOT,F_SEE),('TRT CLINIC',860,SKY,F_SEE+0.5),('DONATE BLOOD',1100,AMBER,F_DON)]
    for k,(lab,cy,col,tt) in enumerate(nodes):
        q=expo((t-tt)/0.2)
        if q<=0: continue
        fn=f(BEB,86); w=d.textlength(lab,font=fn)+90
        nrect(d,(540-w/2,cy-62,540+w/2,cy+62),col,int(a*q),6,26); ctext(d,lab,fn,540,cy-44,col,int(a*q),True)
        if k>0:
            y0=nodes[k-1][1]+66; y1=cy-66; s=ease_io((t-tt+0.4)/0.4)
            nline(d,[(540,y0),(540,lerp(y0,y1,s))],CREAM,5,a)
            py=lerp(y0,y1,(t*2.5)%1.0); d.ellipse([530,py-10,550,py+10],fill=col+(a,))
# 3) problem scene: repeated donations -> three neon meters drain
PR_REP=at('repeated',25.0); PR_IRON=at('iron',26.9); PR_FER=at('ferritin',28.5); PR_FAT=at('fatigue',30.0); PR_UND=at('underlying',35.5)
for tt in (PR_IRON,PR_FER,PR_FAT): sfxb(tt,'tick',g=-24)
sfxb(PR_UND,'impact',g=-16)
def prob(L,d,t):
    if t<S_PROB[0] or t>S_PROB[1]+0.25: return
    a=int(255*scene_a(t,S_PROB))
    kinetic(d,'REPEATED DONATIONS',f(BEB,104),80,400,PR_REP-0.15,t,HOT,-1)
    d.text((84,520),'WHAT IT CAN COST YOU',font=f(MONOB,26),fill=LABEL+(int(a*clamp((t-PR_REP)/0.2)),))
    rows=[('IRON STORES',PR_IRON,AMBER),('FERRITIN',PR_FER,PURP),('ENERGY · PERFORMANCE',PR_FAT,LIME)]
    for k,(lab,tt,col) in enumerate(rows):
        q=expo((t-tt+0.35)/0.25)
        if q<=0: continue
        y=620+k*190; aa=int(a*q)
        d.text((80,y),lab,font=f(BEB,64),fill=col+(aa,))
        lvl=lerp(0.92,0.18,ease_io((t-tt)/0.9)) if t>=tt else 0.92
        x0,x1=80,1000; d.rounded_rectangle([x0,y+80,x1,y+124],radius=22,outline=col+(int(aa*0.6),),width=3)
        d.rounded_rectangle([x0+6,y+86,x0+6+(x1-x0-12)*lvl,y+118],radius=16,fill=col+(aa,))
        if GL: GL.rounded_rectangle([x0+6,y+86,x0+6+(x1-x0-12)*lvl,y+118],radius=16,fill=col+(int(aa*0.55),))
        if t>=tt: tri(d,940,y+8,40,False,HOT+(aa,))
    if t>=PR_UND:
        s=expo((t-PR_UND)/0.18); pill(d,540,1210+20*(1-s),"DOESN'T FIX THE CAUSE",f(MONOB,40),HOT,(255,255,255),int(a*s))

# 4) floating top card: BLOOD DONATION != YOUR FIRST MOVE
NF0=S_PROB[1]; NF1=S_TUBE[0]-0.05; NF_BD=at('blood',38.6); NF_FIRST=at('first',40.3)
sfxb(NF_BD,'tick',g=-25); sfxb(NF_FIRST,'thud',w=1.0,g=-19)
def notfirst(L,d,t):
    a=int(255*float_a(t,NF0,NF1))
    if a<=0: return
    d.rounded_rectangle([40,392,1040,690],radius=22,fill=(4,6,14,int(a*0.86)))
    nrect(d,(70,420,1010,660),PURP,a,4,20)
    ctext(d,'BLOOD DONATION',f(BEB,104),540,440,CREAM,a)
    if t>=NF_FIRST:
        s=expo((t-NF_FIRST)/0.16); ctext(d,'NOT YOUR FIRST MOVE',f(BEB,96),540,548+18*(1-s),HOT,int(a*s),True)

# 5) tube scene: STEP 1 HYDRATION, plasma vs red cells
TB_PCT=at('percentage',44.6); TB_DEH=at('dehydrated',45.6); TB_PL=at('plasma',46.4); TB_HI=at('higher',47.9); TB_RBC=at('producing',49.6)
sfxb(TB_PCT,'tick',g=-25); sfxb(TB_DEH,'scan',d=0.6,g=-30); sfxb(TB_HI,'thud',w=1.0,g=-19); sfxb(TB_RBC,'tick',g=-25)
def tube_shape(d,x0,y0,x1,y1,col,a):
    d.rounded_rectangle([x0,y0,x1,y1],radius=(x1-x0)//2,outline=col+(a,),width=6)
    if GL: GL.rounded_rectangle([x0,y0,x1,y1],radius=(x1-x0)//2,outline=col+(int(a*0.8),),width=14)
def tube(L,d,t):
    if t<S_TUBE[0] or t>S_TUBE[1]+0.25: return
    a=int(255*scene_a(t,S_TUBE))
    kinetic(d,'STEP 1',f(BEB,70),80,400,S_TUBE[0]+0.05,t,MINT,-1)
    kinetic(d,'HYDRATION',f(BEB,130),80,460,S_TUBE[0]+0.15,t,SKY,-1)
    x0,x1,y0,y1=150,390,640,1300; inner=(x0+10,y0+10,x1-10,y1-10)
    rbc_h=300                                   # red-cell column never changes
    pl=lerp(1.0,0.45,ease_io((t-TB_PL)/0.9)) if t>=TB_PL else 1.0
    pl_h=(y1-y0-20-rbc_h)*pl
    ry0=y1-10-rbc_h; py0=ry0-pl_h
    d.rounded_rectangle([inner[0],py0,inner[2],ry0+30],radius=24,fill=AMBER+(int(a*0.55),))
    d.rounded_rectangle([inner[0],ry0,inner[2],inner[3]],radius=(inner[2]-inner[0])//2,fill=HOT+(a,))
    for k in range(14):
        cx=inner[0]+26+(k*53)%(inner[2]-inner[0]-50); cy=ry0+30+((k*97)%(rbc_h-70))
        d.ellipse([cx-16,cy-10,cx+16,cy+10],outline=(255,170,190,a),width=3)
    tube_shape(d,x0,y0,x1,y1,CREAM,a)
    def lab(y,txt,col,aa):
        d.line([(x1+14,y),(x1+70,y)],fill=col+(aa,),width=4); d.text((x1+84,y-30),txt,font=f(BEB,58),fill=col+(aa,))
    lab((py0+ry0)/2,'PLASMA',AMBER,a); lab((ry0+y1)/2,'RED CELLS',HOT,a)
    if t>=TB_PCT:
        s=clamp((t-TB_PCT)/0.2); d.text((x1+84,680),'HCT = % OF BLOOD',font=f(MONOB,30),fill=CREAM+(int(a*s),))
        d.text((x1+84,722),'THAT IS RED CELLS',font=f(MONOB,30),fill=CREAM+(int(a*s),))
    if t>=TB_DEH: pill(d,700,800,'DEHYDRATED',f(MONOB,36),SKY,DEEP,int(a*clamp((t-TB_DEH)/0.2)))
    if t>=TB_HI:
        s=expo((t-TB_HI)/0.18); ctext(d,'HCT READS',f(BEB,70),720,960,CREAM,int(a*s)); ctext(d,'HIGHER',f(BEB,120),700,1030,HOT,int(a*s),True)
        tri(d,880,1050,60,True,HOT+(int(a*s),))
    if t>=TB_RBC:
        s=clamp((t-TB_RBC)/0.2); ctext(d,'SAME RED CELLS',f(MONOB,34),720,1190,MINT,int(a*s))

# 6) ECG scene: STEP 2 CONSISTENT CARDIO, plasma expands, HCT down
EC_AER=at('aerobic',53.7); EC_EXP=at('expand',55.0); EC_LOW=at('lowers',57.5); EC_REM=at('removing',59.0)
sfxb(EC_AER,'scan',d=0.7,g=-31); sfxb(EC_EXP,'tick',g=-24); sfxb(EC_LOW,'thud',w=1.2,g=-18); sfxb(EC_REM,'tick',g=-25)
def ecg_y(u):
    p=u%1.0
    if 0.40<p<0.44: return -0.25
    if 0.44<=p<0.48: return 1.0
    if 0.48<=p<0.52: return -0.45
    if 0.62<p<0.74: return 0.18*math.sin((p-0.62)/0.12*math.pi)
    return 0
def ecg(L,d,t):
    if t<S_ECG[0] or t>S_ECG[1]+0.25: return
    a=int(255*scene_a(t,S_ECG))
    kinetic(d,'STEP 2',f(BEB,70),80,400,S_ECG[0]+0.05,t,LIME,-1)
    kinetic(d,'CONSISTENT CARDIO',f(BEB,110),80,460,S_ECG[0]+0.15,t,MINT,-1)
    gx0,gx1,gy=60,1020,760; ph=t*0.9
    for x in range(gx0,gx1,60): d.line([(x,620),(x,900)],fill=(30,60,55,int(a*0.6)),width=1)
    pts=[(x,gy-120*ecg_y(x/320-ph)) for x in range(gx0,gx1,4)]
    hx=gx0+((t-S_ECG[0])*420)%(gx1-gx0)
    nline(d,[p for p in pts if p[0]<=hx],LIME,5,a)
    nline(d,[p for p in pts if p[0]>hx+60],LIME,5,int(a*0.35))
    d.ellipse([hx-10,gy-120*ecg_y(hx/320-ph)-10,hx+10,gy-120*ecg_y(hx/320-ph)+10],fill=(255,255,255,a))
    # plasma volume bar
    if t>=EC_EXP-0.3:
        q=clamp((t-EC_EXP+0.3)/0.25); y=960; aa=int(a*q)
        d.text((80,y),'PLASMA VOLUME',font=f(MONOB,30),fill=AMBER+(aa,))
        v=lerp(0.45,0.85,ease_io((t-EC_EXP)/1.2)) if t>=EC_EXP else 0.45
        d.rounded_rectangle([80,y+50,1000,y+100],radius=24,outline=AMBER+(int(aa*0.6),),width=3)
        d.rounded_rectangle([86,y+56,86+908*v,y+94],radius=18,fill=AMBER+(aa,))
        if GL: GL.rounded_rectangle([86,y+56,86+908*v,y+94],radius=18,fill=AMBER+(int(aa*0.5),))
        if t>=EC_EXP: ctext(d,'EXPANDS',f(BEB,56),900,y-14,AMBER,aa)
    if t>=EC_LOW:
        s=expo((t-EC_LOW)/0.18); d.text((80,1110+16*(1-s)),'HCT',font=f(BEB,120),fill=CREAM+(int(a*s),))
        tri(d,290,1150,70,False,MINT+(int(a*s),)); d.text((380,1135),'LOWER',font=f(BEB,96),fill=MINT+(int(a*s),))
    if t>=EC_REM: pill(d,540,1260,'NO RED CELLS REMOVED',f(MONOB,36),MINT,DEEP,int(a*clamp((t-EC_REM)/0.2)))

# 7) floating top card: STEP 3 nutrition + supplements, ingredient chips as spoken
N0=S_ECG[1]; N1=S_GAUGE[0]-0.05; N_NUT=at('nutrition',61.4); N_SUP=at('supplements',62.4)
ING=[('NATTOKINASE',at('nattokinase',66.1),MINT),('GRAPE SEED EXTRACT',at('grape',67.0),PURP),('DIHYDROQUERCETIN',at('dihydroquercetin',67.8),AMBER)]
sfxb(N_NUT,'tick',g=-26); sfxb(N_SUP,'tick',g=-26)
for _,tt,_c in ING: sfxb(tt,'thud',w=0.8,g=-21)
def step3(L,d,t):
    a=int(255*float_a(t,N0,N1))
    if a<=0: return
    d.rounded_rectangle([40,392,1040,700],radius=22,fill=(4,6,14,int(a*0.86)))
    d.text((70,410),'STEP 3',font=f(MONOB,28),fill=AMBER+(a,))
    x=70
    for s_,tt,col in (('NUTRITION',N_NUT,LIME),('  +  ',N_SUP,CREAM),('SUPPLEMENTS',N_SUP,SKY)):
        if t>=tt: d.text((x,446),s_,font=f(BEB,86),fill=col+(int(a*clamp((t-tt)/0.15)),))
        x+=d.textlength(s_,font=f(BEB,86))
    for k,(lab,tt,col) in enumerate(ING):
        q=expo((t-tt)/0.18)
        if q<=0: continue
        fn=f(MONOB,30); w=d.textlength(lab,font=fn); y=[566,566,636][k]; x=70 if k!=1 else 70+d.textlength(ING[0][0],font=fn)+70
        nrect(d,(x,y-8,x+w+36,y+46),col,int(a*q),3,14); d.text((x+18,y),lab,font=fn,fill=col+(int(a*q),))

# 8) gauge scene: HCT scale with the 54 and 57 lines, as stated
G_57=at('prompt',72.4); G_ANA=at('anabolics',75.6); G_54=at('54',76.7); G_DIV=at('diving',78.5)
sfxb(G_57,'impact',g=-16); sfxb(G_54,'thud',w=1.2,g=-18); sfxb(G_DIV,'tick',g=-25)
def gauge_s(L,d,t):
    if t<S_GAUGE[0] or t>S_GAUGE[1]+0.25: return
    a=int(255*scene_a(t,S_GAUGE))
    kinetic(d,'KNOW YOUR LINES',f(BEB,110),80,400,S_GAUGE[0]+0.1,t,CREAM,-1)
    d.text((84,530),'HEMATOCRIT · %',font=f(MONOB,28),fill=LABEL+(a,))
    x0,x1,y=80,1000,860; X=lambda v:x0+(x1-x0)*(v-40)/20
    q=ease_io((t-S_GAUGE[0]-0.2)/0.6)
    segs=[(40,54,MINT),(54,57,AMBER),(57,60,HOT)]
    for lo,hi,col in segs:
        e=min(X(hi),lerp(x0,x1,q))
        if e>X(lo): d.rectangle([X(lo)+2,y,e-2,y+50],fill=col+(int(a*(0.95 if (lo==54 and t>=G_54) or (lo==57 and t>=G_57) else 0.35)),))
    if GL and q>0: GL.rectangle([x0,y,lerp(x0,x1,q),y+50],outline=MINT+(int(a*0.4),),width=6)
    for v in (40,45,50,55,60):
        if q>=1: ctext(d,str(v),f(MONO,24),X(v),y+64,LABEL,a)
    if t>=G_57:
        s=expo((t-G_57)/0.16); aa=int(a*s); xx=X(57)
        nline(d,[(xx,y-150),(xx,y+50)],HOT,6,aa); ctext(d,'57%',f(BEB,96),xx,y-260,HOT,aa,True)
        pill(d,540,1000,'PROMPT MEDICAL EVALUATION',f(MONOB,34),HOT,(255,255,255),aa)
    if t>=G_ANA: ctext(d,'ESPECIALLY ON ANABOLICS',f(MONOB,28),540,1090,CREAM,int(a*clamp((t-G_ANA)/0.2)))
    if t>=G_54:
        s=expo((t-G_54)/0.16); aa=int(a*s); xx=X(54)
        nline(d,[(xx,y-150),(xx,y+50)],AMBER,6,aa); ctext(d,'54%',f(BEB,96),xx-70,y-260,AMBER,aa,True)
        ctext(d,'THRESHOLD',f(MONOB,26),xx-70,y-150,AMBER,aa)
    if t>=G_DIV: pill(d,540,1170,'START DIGGING IN',f(MONOB,36),AMBER,DEEP,int(a*clamp((t-G_DIV)/0.2)))

# 9) floating 2x2 tiles: what to investigate
IV0=S_GAUGE[1]; IV1=S_EQ[0]-0.05
TILES=[('ANDROGEN','EXPOSURE',at('androgen',80.4),PURP),('SLEEP','APNEA',at('sleep',81.6),SKY),('HYDRATION','',at('hydration',82.3),MINT),('CARDIO','RISK',at('cardiovascular',83.6),HOT)]
for *_,tt,_c in TILES: sfxb(tt,'tick',g=-24)
def investigate(L,d,t):
    a=int(255*float_a(t,IV0,IV1))
    if a<=0: return
    d.rounded_rectangle([40,392,1040,730],radius=22,fill=(4,6,14,int(a*0.86)))
    d.text((70,404),'INVESTIGATE',font=f(MONOB,28),fill=CREAM+(a,))
    for k,(l1,l2,tt,col) in enumerate(TILES):
        q=expo((t-tt)/0.18)
        if q<=0: continue
        cx=70+(k%2)*480; cy=450+(k//2)*136; aa=int(a*q)
        nrect(d,(cx,cy+10*(1-q),cx+460,cy+120+10*(1-q)),col,aa,4,16)
        txt=l1+(' '+l2 if l2 else ''); fn=f(BEB,64)
        while d.textlength(txt,font=fn)>420: fn=f(BEB,fn.size-4)
        ctext(d,txt,fn,cx+230,cy+28,col,aa,True)

# 10) equation scene: LOWERING THE NUMBER != FIXING THE PROBLEM
EQ_FIX=at('fixing',86.0); EQ_TWO=at('two',87.3)
sfxb(EQ_FIX,'tick',g=-24); sfxb(EQ_TWO,'impact',g=-15)
def equation(L,d,t):
    if t<S_EQ[0] or t>S_EQ[1]+0.25: return
    a=int(255*scene_a(t,S_EQ))
    kinetic(d,'LOWERING',f(BEB,150),80,440,S_EQ[0]+0.05,t,MINT,-1,0.18)
    kinetic(d,'THE NUMBER',f(BEB,110),80,600,S_EQ[0]+0.15,t,CREAM,-1,0.18)
    if t>=EQ_FIX-0.3:
        s=expo((t-EQ_FIX+0.3)/0.16); aa=int(a*s); cx,cy=540,790
        for dy in (-24,24): d.line([(cx-80,cy+dy),(cx+80,cy+dy)],fill=HOT+(aa,),width=14)
        d.line([(cx+40,cy-74),(cx-40,cy+74)],fill=HOT+(aa,),width=14)
        if GL: GL.line([(cx+40,cy-74),(cx-40,cy+74)],fill=HOT+(int(aa*0.5),),width=20)
    kinetic(d,'FIXING',f(BEB,150),80,880,EQ_FIX,t,AMBER,1,0.18)
    kinetic(d,'THE PROBLEM',f(BEB,110),80,1040,EQ_FIX+0.1,t,CREAM,1,0.18)
    if t>=EQ_TWO: pill(d,540,1190,'TWO DIFFERENT THINGS',f(MONOB,40),HOT,(255,255,255),int(a*clamp((t-EQ_TWO)/0.18)))

# 11) age scene: 40 for six more months vs strong at 60
AG_40=at('40',91.8); AG_6=at('six',92.9); AG_STR=at('strong',94.0); AG_60=at('60',96.9); AG_UNIT=at('unit',95.8)
sfxb(AG_40,'tick',g=-24); sfxb(AG_6,'thud',w=0.9,g=-20); sfxb(AG_STR,'scan',d=0.6,g=-30); sfxb(AG_60,'impact',g=-15)
def age(L,d,t):
    if t<S_AGE[0] or t>S_AGE[1]+0.25: return
    a=int(255*scene_a(t,S_AGE))
    kinetic(d,'THE REAL GOAL',f(BEB,110),80,400,S_AGE[0]+0.1,t,CREAM,-1)
    x0,x1=80,1000; X=lambda age_:x0+(x1-x0)*(age_-35)/30
    ya,yb=700,1000
    if t>=AG_40-0.3:
        q=clamp((t-AG_40+0.3)/0.2); aa=int(a*q)
        d.text((80,ya-110),'LOOK GREAT AT 40',font=f(BEB,72),fill=MUTED+(aa,))
        e=X(40.5)*1 if t<AG_6 else lerp(X(40),X(40.5),ease_io((t-AG_6)/0.5))
        d.rounded_rectangle([X(40),ya,max(X(40)+30,e),ya+56],radius=28,fill=MUTED+(aa,))
        if t>=AG_6: d.text((X(40.5)+30,ya+2),'+ 6 MONTHS',font=f(BEB,56),fill=MUTED+(aa,))
    if t>=AG_STR-0.2:
        q=clamp((t-AG_STR+0.2)/0.2); aa=int(a*q)
        d.text((80,yb-110),'STRONG + HEALTHY',font=f(BEB,72),fill=LIME+(aa,))
        e=lerp(X(40),X(60),ease_io((t-AG_STR)/(AG_60-AG_STR)))
        d.rounded_rectangle([X(40),yb,e,yb+56],radius=28,fill=LIME+(aa,))
        if GL: GL.rounded_rectangle([X(40),yb,e,yb+56],radius=28,fill=LIME+(int(aa*0.55),))
    for v in (40,50,60):
        if t>=AG_40: ctext(d,str(v),f(MONO,26),X(v),yb+76,LABEL,a)
    if t>=AG_UNIT:
        s=expo((t-AG_UNIT)/0.18); ctext(d,'STILL A UNIT AT 60',f(BEB,100),540,1180+16*(1-s),LIME,int(a*s),True)

def overlays_b(im,t):
    L,d=newL()
    mirror(L,d,t); flow(L,d,t); prob(L,d,t); notfirst(L,d,t); tube(L,d,t); ecg(L,d,t); step3(L,d,t)
    gauge_s(L,d,t); investigate(L,d,t); equation(L,d,t); age(L,d,t)
    im.alpha_composite(L)

# 12) neon end card: the right way first, donation last resort, COMMENT "BLOODS"
T_END=S_AGE[1]; E_DROP=at('drop',99.8); E_LAST=at('last',104.0); E_C=at('comment',104.7); E_BL=at('bloods',105.2); E_SEND=at('send',106.3)
sfxb(T_END,'whoosh',d=0.25,g=-28); sfxb(E_DROP,'thud',w=1.3,g=-17); sfxb(E_LAST,'tick',g=-24); sfxb(E_BL,'impact',g=-15); sfxb(E_SEND,'tick',g=-26)
def end_b(im,t):
    if t<T_END: return
    q=ease_io((t-T_END)/0.35); im.alpha_composite(scene_bg(q)); L,d=newL(); a=int(255*q)
    lg=logo().copy(); lg.putalpha(lg.split()[3].point(lambda v:int(v*q))); L.alpha_composite(lg.resize((140,140)),(70,250))
    d.text((230,268),'COACH AGZ',font=f(BAR,52),fill=GOLD+(a,)); d.text((232,332),'@coach.agz',font=f(MONO,28),fill=MUTED+(a,))
    if t>=E_DROP-0.3:
        s=expo((t-E_DROP+0.3)/0.2); aa=int(a*s)
        ctext(d,'DROP YOUR',f(BEB,96),540,470,CREAM,aa)
        ctext(d,'HEMATOCRIT',f(BEB,150),540,560,MINT,aa,True)
        ctext(d,'THE RIGHT WAY FIRST',f(BEB,80),540,720,CREAM,aa)
    if t>=E_LAST-0.3:
        s=expo((t-E_LAST+0.3)/0.18); aa=int(a*s)
        nrect(d,(150,840,930,960),AMBER,aa,4,20); ctext(d,'DONATION = LAST RESORT',f(BEB,76),540,862,AMBER,aa,True)
    if t>=E_C:
        s=expo((t-E_C)/0.16); sc=lerp(1.5,1,s); fn=f(MONOB,int(56*sc)); txt='COMMENT "BLOODS"'; w=d.textlength(txt,font=fn)
        lit_bar(d,540-w/2-30,1010,540+w/2+30,1010+fn.size+40,HOT,int(a*s)); d.text((540-w/2,1030),txt,font=fn,fill=(255,255,255,int(a*s)))
        if GL and t<E_C+0.6: GL.rectangle([540-w/2-34,1006,540+w/2+34,1014+fn.size+40],outline=HOT+(int(220*(1-(t-E_C)/0.6)),),width=12)
    if t>=E_SEND: ctext(d,'SENT TO YOU',f(MONOB,34),540,1150,CREAM,int(a*clamp((t-E_SEND)/0.15)))
    ctext(d,DISC,f(MONO,20),540,1210,LABEL,a)
    ctext(d,'NOT MEDICAL ADVICE · WORK WITH YOUR DOCTOR',f(MONO,20),540,1242,LABEL,a)
    im.alpha_composite(L)

# ---------------- frame ----------------
SUBJECT_T=1.04      # visual hook: first punch-in lands on the spoken subject "hematocrit"
def zoom_at(t):   # saved setup: 108% punch-in alternates at every jump cut
    if t<CUTS[0]: return 1.08 if t>=SUBJECT_T else 1.0
    return 1.0 if seg_of(t)%2==1 else 1.08

_PT=None
def frame(src,t):
    z=zoom_at(t)
    if z>1.001:
        cx,cy=540,1000; w,h=W/z,H/z; src=src.crop((cx-w/2,cy-h/2,cx+w/2,cy+h/2)).resize((W,H),Image.BICUBIC)
    tw=WARP(t)
    g=float(B_push(t)); bg=src
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
    overlays_b(im,t); end_b(im,t)
    GL=None
    if glow.getbbox():
        gb=np.asarray(glow.filter(ImageFilter.GaussianBlur(14))).astype(np.float32)/255
        g2=np.asarray(glow.filter(ImageFilter.GaussianBlur(40))).astype(np.float32)/255
        prem=np.clip(gb[...,:3]*gb[...,3:]*2.3+g2[...,:3]*g2[...,3:]*1.8,0,1)
        base_=np.asarray(im.convert('RGB')).astype(np.float32)/255
        im=Image.fromarray(((1-(1-base_)*(1-prem))*255).astype(np.uint8)).convert('RGBA')
    hook_band(im,t)
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
        ev=[dict(e,t=round(e['t'],3)) for e in EVB]+[dict(t=round(HOOK_END,3),kind='whoosh',d=0.25,g=-30)]; json.dump(sorted(ev,key=lambda e:e['t']),open(T+'events.json','w'),indent=0); print(len(ev),'events'); sys.exit()
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
        enc=subprocess.Popen(['ffmpeg','-v','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-','-c:v','libx264','-crf','16','-preset','medium','-profile:v','high','-level','4.2','-pix_fmt','yuv420p',outp],stdin=subprocess.PIPE)
        for n in range(n0,n1):
            buf=dec.stdout.read(W*H*3)
            if len(buf)<W*H*3: print('short at',n); break
            enc.stdin.write(frame(Image.frombuffer('RGB',(W,H),buf),n/FPS).tobytes())
        enc.stdin.close(); enc.wait(); dec.kill(); print('done',n0,n1)
