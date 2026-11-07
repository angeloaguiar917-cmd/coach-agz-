# Reel: "GH timelines" (what growth hormone does, and when): full edit, native 1080x1920, brand-neon overlay set
# Built on the saved setup: test-06 look + full-test-02 workflow (dead air trimmed, misspeak cut, 108% punch-in per jump cut,
# captions from the trimmed audio). Usage: python render.py <scratch> [--events|--groups|--still t..|--range n0 n1 out.mp4]
import json, subprocess, sys, math, re
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
S=sys.argv[1]; F=S+'/fonts/'; T=S+'/r17/work/'
W,H=1080,1920; FPS=30; N=3728; DUR=N/FPS
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
FIX={283:'F*CKING',329:'F*CKING'}
for i,w in FIX.items(): words[i]['w']=w
for i,n_,s_ in ((402,2,'IGF-1'),(339,2,'SELF-AWARE'),(159,2,'IGF-1'),(150,2,'IGF-1')): words[i]['w']=s_; words[i]['e']=words[i+n_-1]['e']; del words[i+1:i+n_]   # descending so indices hold
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
CUTS=[4.48,23.28,35.76,59.10,80.74,94.64]   # no jump cuts in the take: the punch-in alternates on each new timeline / section instead
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
HOOK_LINES=[[('GROWTH HORMONE',VGOLD),(' results',CREAM)],[('72 hours to years',CREAM)]]
HOOK_END=6.00; HOOK_FADE=0.15; HOOK_Y=262
THO=(HOOK_END,HOOK_END+HOOK_FADE)
_mid=DUR/2; _nc=min(CUTS,key=lambda c:abs(c-_mid)); BAND_OUT=_nc if abs(_nc-_mid)<=1.5 else _mid      # nearest jump cut if within 1.5 s, else fade at the midpoint
BAND_IN=HOOK_END
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
    bin_=clamp((t-BAND_IN)/0.15); bout=1-clamp((t-BAND_OUT)/0.15); v=bin_*bout*(1-B_push(t))
    if v>0 and t>=BAND_IN:
        B,bd=newL(); bd.rectangle([8,212,W,372],fill=NAVY+(int(235*v),)); im.alpha_composite(B)
        a=int(255*v); fn=f(BAR,64); x=64; y=236
        for s,c in [('GH',VGOLD),(' results timeline',CREAM)]: d.text((x,y),s,font=fn,fill=c+(a,)); x+=d.textlength(s,font=fn)
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



# ======================= "GH timelines" overlay set (brand neon: v-gold, v-red, cyan, green, amber on deep navy) =======================
EVB=[]
def sfxb(t,kind,**k): EVB.append(dict(t=round(t,3),kind=kind,**k))
import re as _re2
def at(word,near):
    n=lambda s:_re2.sub(r'[^a-z0-9]','',s.lower()); best=None
    for w in words:
        if n(w['w']).startswith(n(word)) and abs(w['s']-near)<3.5 and (best is None or abs(w['s']-near)<abs(best-near)): best=w['s']
    if best is None: raise SystemExit('word not found: %s @%s'%(word,near))
    return best
VRED=(255,34,28); ECYAN=(0,229,255); NGREEN=(30,255,110); AMBER=(255,150,20); DEEPV=(2,3,8)
PUSH_TINT=(5,8,16)
def kinetic(d,txt,fn,x,y,t0,t,col,frm=-1,dur=0.22):
    q=expo((t-t0)/dur)
    if q<=0: return 0
    w=d.textlength(txt,font=fn); xx=x+frm*(1-q)*(W+w)
    d.text((xx,y),txt,font=fn,fill=col+(int(255*min(1,q*1.4)),))
    if GL: GL.text((xx,y),txt,font=fn,fill=col+(int(110*min(1,q)),))
    return q
def ctext(d,txt,fn,cx,y,col,a,glow=False):
    x=cx-d.textlength(txt,font=fn)/2; d.text((x,y),txt,font=fn,fill=col+(a,))
    if glow and GL: GL.text((x,y),txt,font=fn,fill=col+(int(a*0.7),))
def nline(d,pts,col,w,a):
    if len(pts)<2: return
    d.line(pts,fill=col+(a,),width=w,joint='curve')
    if GL: GL.line(pts,fill=col+(int(a*0.9),),width=w*3,joint='curve')
def nrect(d,box,col,a,w=4,r=18):
    if box[2]<=box[0] or box[3]<=box[1]: return
    d.rounded_rectangle(box,radius=r,outline=col+(a,),width=w)
    if GL: GL.rounded_rectangle(box,radius=r,outline=col+(int(a*0.9),),width=w*3)
def gpanel(d,box,col,a,fill_a=0.6):
    if box[2]<=box[0] or box[3]<=box[1]: return
    d.rounded_rectangle(box,radius=22,fill=DEEPV+(int(a*fill_a),)); nrect(d,box,col,int(a*0.8),3,22)
def pill(d,cx,y,txt,fn,bg,fg,a):
    w=d.textlength(txt,font=fn); h=fn.size+18; lit_bar(d,cx-w/2-18,y,cx+w/2+18,y+h,bg,a); d.text((cx-w/2,y+8),txt,font=fn,fill=fg+(a,))
def float_a(t,t0,t1): return expo((t-t0)/0.25)*(1-ease_io((t-t1)/0.2)) if t0<=t<=t1+0.2 else 0
def scene_a(t,win): return clamp((t-win[0])/0.2)*(1-ease_io((t-win[1])/0.22))
def xmark(d,cx,cy,r,col,a,w=12):
    for dd in ((-r,-r,r,r),(r,-r,-r,r)): d.line([(cx+dd[0],cy+dd[1]),(cx+dd[2],cy+dd[3])],fill=col+(a,),width=w)
    if GL: GL.line([(cx-r,cy-r),(cx+r,cy+r)],fill=col+(int(a*0.6),),width=w*2)
# ---- connective element: the 4-step timeline ruler (active step lit) ----
STEPS=[('72 HRS',ECYAN),('1 WEEK',AMBER),('MONTHS',NGREEN),('MONTHS-YEARS',VGOLD)]
def ruler(d,k,a,y=566):
    x0,x1=90,990
    d.line([(x0,y),(x1,y)],fill=(60,64,78,a),width=4)
    if k>0: nline(d,[(x0,y),(lerp(x0,x1,k/3),y)],STEPS[k][1],4,a)
    for i,(lab,col) in enumerate(STEPS):
        x=lerp(x0,x1,i/3); on=i==k; done=i<k; r=22 if on else 14
        d.ellipse([x-r,y-r,x+r,y+r],fill=(col if (on or done) else (40,44,56))+(a,),outline=col+(a,),width=3)
        ctext(d,str(i+1),f(BEB,34 if on else 24),x,y-(19 if on else 13),DEEP if (on or done) else MUTED,a)
        fn=f(MONOB,22); w=d.textlength(lab,font=fn); tx=min(max(x-w/2,60),1020-w)
        d.text((tx,y+30),lab,font=fn,fill=(col if on else LABEL)+(a,))
C=CUTS
S_T1=(HOOK_END+0.05, at('the',23.28)-0.05)
S_T2=(at('the',23.28)-0.05, at('then',35.76)-0.05)
S_IGF=(at('then',35.76)-0.05, at('and',45.86)-0.02)
S_GATE=(at('and',45.86)-0.02, at('and',59.1)-0.05)
S_STRUCT=(at('and',59.1)-0.05, at('generally',70.06)-0.05)
S_BURN=(at('gh',75.7)-0.05, at("here's",80.74)-0.05)
S_SCALE=(at("here's",80.74)-0.05, at('the',94.64)-0.05)
S_MIRROR=(at('the',94.64)-0.05, at('as',109.1)-0.05)
SCENES=[S_T1,S_T2,S_IGF,S_GATE,S_STRUCT,S_BURN,S_SCALE,S_MIRROR]
def B_push(t):
    g=0
    for a_,b_ in SCENES: g=max(g,clamp((t-a_)/0.22)*clamp((b_-t)/0.22))
    return ease_io(g)
for i,(a_,b_) in enumerate(SCENES):
    if i==0 or abs(a_-SCENES[i-1][1])>0.3: sfxb(a_,'whoosh',d=0.22,g=-28); sfxb(a_+0.2,'thud',w=1.2,g=-18)
    else: sfxb(a_,'scan',d=0.35,g=-29)

# 1) timeline 1: muscle cell fills with glycogen + water in 72 hours (volumization, not new tissue)
T1_72=at('72',9.3); T1_GLY=at('glycogen',10.8); T1_WAT=at('water',11.6); T1_FULL=at('fuller',13.7); T1_ROUND=at('rounder',14.4); T1_NOT=at('tissue',19.5); T1_VOL=at('volumization',20.3)
sfxb(T1_72,'tick',g=-23); sfxb(T1_GLY,'tick',g=-25); sfxb(T1_WAT,'scan',d=0.6,g=-30); sfxb(T1_FULL,'thud',w=1.0,g=-19); sfxb(T1_NOT,'impact',g=-16)
def t1(L,d,t):
    if t<S_T1[0] or t>S_T1[1]+0.25: return
    a=int(255*scene_a(t,S_T1))
    kinetic(d,'WATER INTO MUSCLE',f(BEB,110),70,400,S_T1[0]+0.08,t,ECYAN,-1); ruler(d,0,a)
    cx,cy=540,900; base=170
    fill=ease_io((t-T1_WAT)/2.0) if t>=T1_WAT else 0
    R=base*(1+0.32*fill)
    d.ellipse([cx-R-24,cy-R-24,cx+R+24,cy+R+24],fill=(40,10,14,int(a*0.7)),outline=VRED+(a,),width=6)
    if GL: GL.ellipse([cx-R-24,cy-R-24,cx+R+24,cy+R+24],outline=VRED+(int(a*0.6),),width=14)
    dashed(d,[(cx+base*math.cos(math.radians(k*6)),cy+base*math.sin(math.radians(k*6))) for k in range(61)],CREAM+(int(a*0.7),),3,12,10)
    rng=np.random.default_rng(5)
    if t>=T1_GLY:
        n=int(46*clamp((t-T1_GLY)/1.2))
        for k in range(n):
            ang=rng.random()*6.283; rr=rng.random()**0.5*(R-10)
            x=cx+rr*math.cos(ang); y=cy+rr*math.sin(ang); d.rectangle([x-7,y-7,x+7,y+7],fill=VGOLD+(a,))
    rng=np.random.default_rng(9)
    if t>=T1_WAT:
        n=int(120*fill)
        for k in range(n):
            ang=rng.random()*6.283+t*0.2; rr=rng.random()**0.5*(R-8)
            x=cx+rr*math.cos(ang); y=cy+rr*math.sin(ang); d.ellipse([x-6,y-8,x+6,y+6],fill=ECYAN+(int(a*0.85),))
    lx=80
    if t>=T1_72-0.1:
        gpanel(d,(60,650,300,790),ECYAN,a,0.85); ctext(d,'72',f(BEB,96),180,660,ECYAN,a,True); ctext(d,'HOURS',f(MONOB,22),180,758,MUTED,a)
    for k,(lab,col,tt) in enumerate((('GLYCOGEN',VGOLD,T1_GLY),('WATER',ECYAN,T1_WAT))):
        if t>=tt: d.rectangle([800,670+k*50,824,694+k*50],fill=col+(a,)); d.text((838,662+k*50),lab,font=f(MONOB,26),fill=col+(a,))
    for k,(lab,tt) in enumerate((('FULLER',T1_FULL),('ROUNDER',T1_ROUND))):
        if t>=tt: pill(d,[300,780][k],1150,lab,f(MONOB,34),NGREEN,DEEP,int(a*clamp((t-tt)/0.2)))
    if t>=T1_NOT:
        s=expo((t-T1_NOT)/0.16); pill(d,540,1250,'NOT NEW TISSUE · VOLUMIZATION' if t>=T1_VOL else 'NOT NEW TISSUE',f(MONOB,32),VRED,(255,255,255),int(a*s))
        ctext(d,'SAME TISSUE',f(MONOB,22),cx,cy+base-34,CREAM,int(a*s))

# 2) timeline 2: fat to fuel inside week one; a shrinking fat droplet feeds a fuel gauge
T2_FAT=at('fat',24.5); T2_WK=at('week',26.6); T2_OX=at('oxidize',28.9); T2_FUEL=at('fuel',30.5); T2_LEAN=at('leaner',31.2); T2_LIP=at('lipolysis',34.8)
sfxb(T2_WK,'tick',g=-23); sfxb(T2_OX,'scan',d=0.8,g=-30); sfxb(T2_FUEL,'thud',w=1.0,g=-19); sfxb(T2_LEAN,'tick',g=-23); sfxb(T2_LIP,'tick',g=-24)
def t2(L,d,t):
    if t<S_T2[0] or t>S_T2[1]+0.25: return
    a=int(255*scene_a(t,S_T2))
    kinetic(d,'FAT BECOMES FUEL',f(BEB,110),70,400,S_T2[0]+0.08,t,AMBER,-1); ruler(d,1,a)
    sh=ease_io((t-T2_OX)/2.5) if t>=T2_OX else 0
    cx,cy=290,890; R=190*(1-0.45*sh)
    d.ellipse([cx-R,cy-R*1.08,cx+R,cy+R*0.92],fill=(255,200,60,int(a*0.85)))
    d.ellipse([cx-R*0.6,cy-R*0.8,cx-R*0.1,cy-R*0.35],fill=(255,240,180,int(a*0.7)))
    if GL: GL.ellipse([cx-R,cy-R*1.08,cx+R,cy+R*0.92],outline=AMBER+(int(a*0.8),),width=14)
    ctext(d,'STORED FAT',f(BEB,52),cx,cy+214,AMBER,a)
    gx,gy,gr=790,930,170
    d.arc([gx-gr,gy-gr,gx+gr,gy+gr],start=180,end=360,fill=(40,44,56,a),width=26)
    v=0.15+0.75*sh
    d.arc([gx-gr,gy-gr,gx+gr,gy+gr],start=180,end=180+180*v,fill=NGREEN+(a,),width=26)
    if GL: GL.arc([gx-gr,gy-gr,gx+gr,gy+gr],start=180,end=180+180*v,fill=NGREEN+(int(a*0.7),),width=40)
    ang=math.radians(180+180*v); d.line([(gx,gy),(gx+(gr-40)*math.cos(ang),gy+(gr-40)*math.sin(ang))],fill=CREAM+(a,),width=6); d.ellipse([gx-12,gy-12,gx+12,gy+12],fill=CREAM+(a,))
    ctext(d,'E',f(BEB,40),gx-gr+10,gy+10,MUTED,a); ctext(d,'F',f(BEB,40),gx+gr-10,gy+10,MUTED,a); ctext(d,'FUEL',f(BEB,60),gx,gy+30,NGREEN,a)
    if t>=T2_OX:
        for k in range(10):
            p=((t-T2_OX)*0.8+k/10)%1.0; x=lerp(cx+R*0.7,gx-gr+30,p); y=cy-40+math.sin(p*math.pi)*-120
            d.ellipse([x-8,y-8,x+8,y+8],fill=AMBER+(a,))
            if GL: GL.ellipse([x-12,y-12,x+12,y+12],fill=AMBER+(int(a*0.6),))
    if t>=T2_WK-0.1:
        gpanel(d,(640,650,1000,770),AMBER,a,0.85); ctext(d,'WEEK 1',f(BEB,80),820,660,AMBER,a,True)
    if t>=T2_LEAN: pill(d,540,1210,'LEANER BEFORE NEW MUSCLE',f(MONOB,32),NGREEN,DEEP,int(a*clamp((t-T2_LEAN)/0.2)))
    if t>=T2_LIP: ctext(d,'LIPOLYSIS',f(MONOB,30),540,1290,AMBER,int(a*clamp((t-T2_LIP)/0.2)))

# 3) timeline 3a: GH alone does not build muscle; it routes through IGF-1
I3_MUS=at('muscle',37.7); I3_ALONE=at('alone',41.1); I3_IGF=at('igf-1',43.4); I3_TIS=at('tissue',44.9)
sfxb(I3_MUS,'tick',g=-24); sfxb(I3_ALONE,'impact',g=-16); sfxb(I3_IGF,'thud',w=1.2,g=-18); sfxb(I3_TIS,'tick',g=-23)
def node(d,cx,cy,r,lab,col,a,sub=None):
    d.ellipse([cx-r,cy-r,cx+r,cy+r],fill=DEEPV+(a,),outline=col+(a,),width=6)
    if GL: GL.ellipse([cx-r,cy-r,cx+r,cy+r],outline=col+(int(a*0.7),),width=16)
    fn=f(BEB,int(r*0.62)); ctext(d,lab,fn,cx,cy-r*0.4,col,a)
    if sub: ctext(d,sub,f(MONOB,20),cx,cy+r*0.3,MUTED,a)
def igf(L,d,t):
    if t<S_IGF[0] or t>S_IGF[1]+0.25: return
    a=int(255*scene_a(t,S_IGF))
    kinetic(d,'MUSCLE NEEDS IGF-1',f(BEB,110),70,400,S_IGF[0]+0.08,t,NGREEN,-1); ruler(d,2,a)
    g=(220,750); m=(860,1090); i=(220,1090)
    node(d,*g,110,'GH',VGOLD,a,'GROWTH HORMONE')
    node(d,*m,110,'MUSCLE',NGREEN if t>=I3_TIS else MUTED,a,'TISSUE GROWTH')
    if t>=I3_MUS-0.2:
        s=ease_io((t-I3_MUS+0.2)/0.5); ex=lerp(g[0]+90,m[0]-90,s); ey=lerp(g[1]+70,m[1]-70,s)
        dashed(d,[(g[0]+90,g[1]+70),(ex,ey)],(MUTED if t<I3_ALONE else VRED)+(a,),5,16,12)
    if t>=I3_ALONE:
        s=expo((t-I3_ALONE)/0.14); xmark(d,540,920,int(50*s),VRED,a); ctext(d,'GH ALONE',f(MONOB,26),660,850,VRED,a)
    if t>=I3_IGF-0.1:
        s=expo((t-I3_IGF+0.1)/0.25); node(d,i[0],i[1],int(110*s)+1,'IGF-1',ECYAN,int(a*s),'THE DRIVER')
        p=ease_io((t-I3_IGF)/0.5)
        nline(d,[(g[0],g[1]+110),(g[0],lerp(g[1]+110,i[1]-110,p))],ECYAN,6,a)
        if t>=I3_TIS-0.4:
            p2=ease_io((t-I3_TIS+0.4)/0.5); nline(d,[(i[0]+110,i[1]),(lerp(i[0]+110,m[0]-110,p2),i[1])],NGREEN,6,a)
            d.polygon([(lerp(i[0]+110,m[0]-110,p2),i[1]-16),(lerp(i[0]+110,m[0]-110,p2)+24,i[1]),(lerp(i[0]+110,m[0]-110,p2),i[1]+16)],fill=NGREEN+(a,))

# 3b) timeline 3b: the IGF-1 response depends on four switches; if not dialed in, no mass
GT=[('LIVER HEALTH',at('liver',47.7)),('NUTRITION',at('nutrition',48.7)),('INSULIN SENSITIVITY',at('insulin',49.4)),('OTHER ANABOLIC?',at('another',51.4))]
GT_DIAL=at('dialed',54.3); GT_MASS=at('mass',55.9); GT_LONG=at('long',58.2)
for _,tt in GT: sfxb(tt,'tick',g=-23)
sfxb(GT_DIAL,'impact',g=-15); sfxb(GT_MASS,'thud',w=1.1,g=-18)
def switch(d,x,y,on,col,a):
    d.rounded_rectangle([x,y,x+110,y+56],radius=28,fill=((col if on else (60,64,78))+(a,)))
    kx=x+82 if on else x+28; d.ellipse([kx-22,y+6,kx+22,y+50],fill=CREAM+(a,))
    if on and GL: GL.rounded_rectangle([x,y,x+110,y+56],radius=28,outline=col+(int(a*0.7),),width=10)
def gate(L,d,t):
    if t<S_GATE[0] or t>S_GATE[1]+0.25: return
    a=int(255*scene_a(t,S_GATE))
    kinetic(d,'WHAT IGF-1 DEPENDS ON',f(BEB,96),70,400,S_GATE[0]+0.08,t,ECYAN,-1); ruler(d,2,a)
    bad=t>=GT_DIAL
    for k,(lab,tt) in enumerate(GT):
        if t<tt-0.15: continue
        q=expo((t-tt+0.15)/0.2); y=640+k*120; aa=int(a*q)
        gpanel(d,(60,y,1020,y+100),VRED if bad else NGREEN,aa,0.8)
        d.text((100,y+22),lab,font=f(BEB,60),fill=CREAM+(aa,))
        on=not bad or k%2==1 and t<GT_DIAL+0.3
        switch(d,860,y+22,on,NGREEN,aa)
    if bad:
        s=expo((t-GT_DIAL)/0.18); gpanel(d,(60,1130,1020,1240),VRED,int(a*s),0.9)
        ctext(d,'NOT DIALED IN = NO MASS FROM GH' if t>=GT_MASS else 'NOT DIALED IN',f(BEB,64),540,1146,VRED,int(a*s),True)
    if t>=GT_LONG: ctext(d,'NO MATTER HOW LONG YOU RUN IT',f(MONOB,26),540,1266,MUTED,int(a*clamp((t-GT_LONG)/0.2)))

# 4) timeline 4: structural remodeling, months to years
ST=[('BONE DENSITY',at('bone',62.3)),('TENDON THICKNESS',at('tendon',63.2)),('HAND SIZE',at('hand',64.0))]
ST_MON=at('months',67.8); ST_YRS=at('years',69.3)
for _,tt in ST: sfxb(tt,'tick',g=-23)
sfxb(ST_MON,'scan',d=1.2,g=-30); sfxb(ST_YRS,'thud',w=1.2,g=-18)
def ic_bone(d,cx,cy,s,col,a):
    d.rounded_rectangle([cx-s*0.7,cy-s*0.14,cx+s*0.7,cy+s*0.14],radius=int(s*0.14),fill=col+(a,))
    for ex in (-1,1):
        for ey in (-1,1): d.ellipse([cx+ex*s*0.72-s*0.2,cy+ey*s*0.14-s*0.2,cx+ex*s*0.72+s*0.2,cy+ey*s*0.14+s*0.2],fill=col+(a,))
def ic_tendon(d,cx,cy,s,col,a):
    for k in range(-2,3): d.line([(cx-s*0.8,cy+k*s*0.12),(cx+s*0.8,cy+k*s*0.12+math.sin(k)*4)],fill=col+(a,),width=6)
def ic_hand(d,cx,cy,s,col,a):
    d.rounded_rectangle([cx-s*0.45,cy-s*0.1,cx+s*0.4,cy+s*0.7],radius=int(s*0.18),fill=col+(a,))
    for k in range(4): d.rounded_rectangle([cx-s*0.45+k*s*0.22,cy-s*0.75+abs(k-1.5)*s*0.1,cx-s*0.29+k*s*0.22,cy],radius=int(s*0.08),fill=col+(a,))
    d.rounded_rectangle([cx+s*0.35,cy+s*0.05,cx+s*0.7,cy+s*0.25],radius=int(s*0.1),fill=col+(a,))
def struct(L,d,t):
    if t<S_STRUCT[0] or t>S_STRUCT[1]+0.25: return
    a=int(255*scene_a(t,S_STRUCT))
    kinetic(d,'STRUCTURAL REMODELING',f(BEB,96),70,400,S_STRUCT[0]+0.08,t,VGOLD,-1); ruler(d,3,a)
    for k,((lab,tt),ic) in enumerate(zip(ST,(ic_bone,ic_tendon,ic_hand))):
        q=expo((t-tt)/0.22)
        if q<=0: continue
        x0=60+k*325; aa=int(a*q); dy=40*(1-q)
        gpanel(d,(x0,640+dy,x0+305,940+dy),VGOLD,aa,0.85)
        ic(d,x0+152,760+dy,70,VGOLD,aa); ctext(d,lab,f(BEB,44 if len(lab)<12 else 36),x0+152,870+dy,CREAM,aa)
    yb=1080; d.text((70,yb-56),'TIME TO SEE IT',font=f(MONOB,24),fill=LABEL+(a,))
    for k in range(24):
        x=70+k*39; on=t>=ST_MON and k<int(24*ease_io((t-ST_MON)/1.6))
        col=VGOLD if k<12 else AMBER
        d.rectangle([x,yb,x+32,yb+70],fill=(col if on else (40,44,56))+(a,))
    d.text((70,yb+82),'MONTHS',font=f(MONOB,22),fill=LABEL+(a,)); d.text((870,yb+82),'YEARS',font=f(MONOB,22),fill=LABEL+(a,))
    if t>=ST_YRS: pill(d,540,1240,'MONTHS UPON MONTHS · IF NOT YEARS',f(MONOB,30),VGOLD,DEEP,int(a*clamp((t-ST_YRS)/0.2)))

# 5) floating: the bodybuilder-level changes ride on massive doses (dose dial into the red)
DS0=S_STRUCT[1]; DS1=S_BURN[0]-0.05; DS_ORG=at('organ',71.3); DS_MAS=at('massive',73.6)
sfxb(DS_ORG,'tick',g=-24); sfxb(DS_MAS,'impact',g=-15)
def dose(L,d,t):
    a=int(255*float_a(t,DS0,DS1))
    if a<=0: return
    gpanel(d,(40,392,1040,700),VRED,a,0.88)
    cx,cy,r=230,640,170
    for k in range(12):
        v0,v1=k/12,(k+1)/12; col=NGREEN if k<5 else (AMBER if k<8 else VRED)
        d.arc([cx-r,cy-r,cx+r,cy+r],start=180+180*v0+1,end=180+180*v1-1,fill=col+(int(a*0.85),),width=30)
    v=0.2+0.72*ease_io((t-DS_MAS)/0.4) if t>=DS_MAS else 0.2
    ang=math.radians(180+180*v); d.line([(cx,cy),(cx+(r-34)*math.cos(ang),cy+(r-34)*math.sin(ang))],fill=CREAM+(a,),width=7); d.ellipse([cx-14,cy-14,cx+14,cy+14],fill=CREAM+(a,))
    ctext(d,'GH DOSE',f(MONOB,22),cx,cy+20,MUTED,a)
    d.text((450,420),'ORGAN GROWTH ·',font=f(BEB,58),fill=CREAM+(a if t>=DS_ORG else int(a*0.4),))
    d.text((450,480),'BODYBUILDER STUFF',font=f(BEB,58),fill=CREAM+(a if t>=DS_ORG else int(a*0.4),))
    if t>=DS_MAS:
        s=expo((t-DS_MAS)/0.16); d.text((450,560),'MASSIVE DOSES',font=f(BEB,96),fill=VRED+(int(a*s),))
        if GL: GL.text((450,560),'MASSIVE DOSES',font=f(BEB,96),fill=VRED+(int(a*s*0.6),))

# 6) slow burn: consistency across real training blocks (segmented block bar + candle)
BU_SLOW=at('slow',76.2); BU_CON=at('consistency',78.1); BU_BLK=at('blocks',79.9)
sfxb(BU_SLOW,'tick',g=-24); sfxb(BU_CON,'scan',d=0.8,g=-30); sfxb(BU_BLK,'thud',w=1.0,g=-19)
def burn(L,d,t):
    if t<S_BURN[0] or t>S_BURN[1]+0.25: return
    a=int(255*scene_a(t,S_BURN))
    kinetic(d,'A SLOW BURN',f(BEB,120),70,400,S_BURN[0]+0.08,t,AMBER,-1)
    cx,cy=540,820; h=lerp(260,200,clamp((t-S_BURN[0])/5))
    d.rounded_rectangle([cx-60,cy-h/2+120,cx+60,cy+240],radius=14,fill=(236,232,220,a))
    fl=1+0.08*math.sin(t*14); fy=cy-h/2+120
    d.polygon([(cx,fy-110*fl),(cx+36,fy-30),(cx+20,fy),(cx-20,fy),(cx-36,fy-30)],fill=AMBER+(a,)); d.polygon([(cx,fy-60*fl),(cx+16,fy-16),(cx,fy),(cx-16,fy-16)],fill=(255,240,180,a))
    if GL: GL.ellipse([cx-70,fy-150,cx+70,fy+20],fill=AMBER+(int(a*0.6),))
    yb=1130
    for k in range(6):
        x=90+k*150; on=t>=BU_CON and k<int(6*ease_io((t-BU_CON)/1.6))+0
        gpanel(d,(x,yb,x+130,yb+90),NGREEN if on else (60,64,78),a,0.85 if on else 0.6)
        ctext(d,f'BLOCK {k+1}',f(MONOB,22),x+65,yb+30,NGREEN if on else MUTED,a)
    if t>=BU_BLK: ctext(d,'CONSISTENCY · REAL TRAINING BLOCKS',f(MONOB,28),540,yb+110,CREAM,int(a*clamp((t-BU_BLK)/0.2)))

# 7) waterfall: -8 lb fat, +6 lb muscle, scale shows 2
WF_LIE=at('scale',83.0); WF_8=at('eight',88.4); WF_6=at('6',90.4); WF_2=at('2',92.5); WF_SENSE=at('sense',94.0)
sfxb(WF_LIE,'tick',g=-24); sfxb(WF_8,'thud',w=1.0,g=-19); sfxb(WF_6,'thud',w=1.0,g=-19); sfxb(WF_2,'impact',g=-15)
def waterfall(L,d,t):
    if t<S_SCALE[0] or t>S_SCALE[1]+0.25: return
    a=int(255*scene_a(t,S_SCALE))
    kinetic(d,'THE SCALE LIES',f(BEB,120),70,400,S_SCALE[0]+0.08,t,VRED,-1)
    x0,x1=110,990; y0=700; U=48      # px per lb
    base=y0+8*U*0.15
    d.line([(x0,base),(x1,base)],fill=MUTED+(a,),width=2); d.text((x0,base-34),'START',font=f(MONOB,20),fill=LABEL+(a,))
    cols=[('FAT',-8,WF_8,VRED),('MUSCLE',+6,WF_6,NGREEN),('ON THE SCALE',-2,WF_2,VGOLD)]
    lvl=0
    for k,(lab,v,tt,col) in enumerate(cols):
        x=170+k*290; w=200
        if k<2: top=base+lvl*-U; bot=top+(-v)*U
        else: top=base; bot=base+(-v)*U
        if t>=tt:
            s=ease_io((t-tt)/0.4); y_a=top; y_b=lerp(top,bot,s)
            ya,yb_=min(y_a,y_b),max(y_a,y_b)
            d.rectangle([x,ya,x+w,yb_],fill=col+(int(a*0.9),))
            if GL: GL.rectangle([x,ya,x+w,yb_],outline=col+(int(a*0.7),),width=10)
            txt=(('+' if v>0 else '−')+f'{abs(v)} LB')
            ctext(d,txt,f(BEB,80),x+w/2,(yb_+10) if v<0 else (ya-90),col,int(a*s),True)
            ctext(d,lab,f(MONOB,24),x+w/2,base-40 if v<0 else base+14,col if k<2 else VGOLD,a)
        if k<2: lvl+=v
        if k==0 and t>=cols[1][2]: dashed(d,[(x+w,base+8*U),(x+w+90,base+8*U)],(120,124,136,a),3,10,8)
    if t>=WF_SENSE: pill(d,540,1290,'MAKES NO SENSE ON A SCALE',f(MONOB,32),VRED,(255,255,255),int(a*clamp((t-WF_SENSE)/0.2)))

# 8) mirror vs scale, then what matters more
MR_SELF=at('self-aware',96.1); MR_MIR=at('mirror',98.3); MR_DIF=at('different',100.2); MR_BAR=at('barely',102.4); MR_MAT=at('matter',105.5); MR_BW=at('weight',107.6)
sfxb(MR_MIR,'tick',g=-23); sfxb(MR_DIF,'thud',w=1.0,g=-19); sfxb(MR_BAR,'tick',g=-24); sfxb(MR_MAT,'thud',w=1.2,g=-18); sfxb(MR_BW,'impact',g=-16)
def mirror(L,d,t):
    if t<S_MIRROR[0] or t>S_MIRROR[1]+0.25: return
    a=int(255*scene_a(t,S_MIRROR))
    rank=t>=MR_MAT-0.2
    if not rank:
        kinetic(d,'MIRROR VS SCALE',f(BEB,110),70,400,S_MIRROR[0]+0.08,t,CREAM,-1)
        mx0,my0,mx1,my1=80,560,500,1220
        d.rounded_rectangle([mx0,my0,mx1,my1],radius=200,fill=(20,26,36,a),outline=VGOLD+(a,),width=8)
        if GL: GL.rounded_rectangle([mx0,my0,mx1,my1],radius=200,outline=VGOLD+(int(a*0.6),),width=16)
        ch=ease_io((t-MR_DIF)/0.8) if t>=MR_DIF else 0; cx=290
        sw=lerp(100,128,ch); ww=lerp(96,74,ch)
        d.ellipse([cx-40,700,cx+40,780],fill=(150,154,166,a))
        d.polygon([(cx-sw,800),(cx+sw,800),(cx+ww,1020),(cx-ww,1020)],fill=((150,154,166) if ch<0.5 else NGREEN)+(a,))
        d.rectangle([cx-ww+4,1020,cx+ww-4,1140],fill=(120,124,136,a))
        if t>=MR_MIR: ctext(d,'MIRROR',f(BEB,52),cx,1240,VGOLD,a)
        if t>=MR_DIF: ctext(d,'COMPLETELY DIFFERENT',f(MONOB,22),cx,1300,NGREEN,int(a*clamp((t-MR_DIF)/0.2)))
        sx,sy=780,900
        d.rounded_rectangle([sx-200,sy-200,sx+200,sy+260],radius=40,fill=(36,40,52,a),outline=(120,124,136,a),width=6)
        d.ellipse([sx-130,sy-160,sx+130,sy+100],fill=(236,234,230,a))
        for k in range(15):
            ang=math.radians(200+k*10); d.line([(sx+110*math.cos(ang),sy-30+110*math.sin(ang)),(sx+125*math.cos(ang),sy-30+125*math.sin(ang))],fill=(60,60,66,a),width=3)
        wig=0.4*math.sin(t*3) if t>=MR_BAR else 0; ang=math.radians(270+wig*4)
        d.line([(sx,sy-30),(sx+100*math.cos(ang),sy-30+100*math.sin(ang))],fill=VRED+(a,),width=6)
        ctext(d,'SCALE',f(BEB,52),sx,1240,MUTED,a)
        if t>=MR_BAR: ctext(d,'BARELY SHIFTED',f(MONOB,22),sx,1300,VRED,int(a*clamp((t-MR_BAR)/0.2)))
    else:
        kinetic(d,'WHAT MATTERS MORE',f(BEB,110),70,400,MR_MAT-0.2,t,VGOLD,1)
        for k,(lab,col,tt) in enumerate((('THE MIRROR',VGOLD,MR_MAT-0.1),('YOUR BLOODWORK',ECYAN,MR_MAT+0.15),('BODY WEIGHT',MUTED,MR_BW))):
            q=expo((t-tt)/0.22)
            if q<=0: continue
            y=600+k*190; aa=int(a*q)
            gpanel(d,(80,y,1000,y+160),col,aa,0.85)
            ctext(d,str(k+1),f(BEB,110),170,y+14,col,aa,True); d.text((260,y+36),lab,font=f(BEB,90),fill=(CREAM if k<2 else MUTED)+(aa,))
            if k==2 and t>=MR_BW+0.2: d.line([(250,y+86),(lerp(250,930,expo((t-MR_BW-0.2)/0.2)),y+86)],fill=VRED+(aa,),width=12)

# 9) floating: measure, analyze, pivot, optimize (chevron strip)
LP0=S_MIRROR[1]; LP1=at('if',113.0)-0.05
LP=[('MEASURE',at('measure',109.9),ECYAN),('ANALYZE',at('analyze',110.6),VGOLD),('PIVOT',at('pivot',111.4),AMBER),('OPTIMIZE',at('optimize',112.1),NGREEN)]
for _,tt,_c in LP: sfxb(tt,'tick',g=-24)
def chevrons(L,d,t):
    a=int(255*float_a(t,LP0,LP1))
    if a<=0: return
    for k,(lab,tt,col) in enumerate(LP):
        q=expo((t-tt)/0.2)
        if q<=0: continue
        x=40+k*250; y=420; aa=int(a*q)
        pts=[(x,y),(x+220,y),(x+250,y+70),(x+220,y+140),(x,y+140),(x+30,y+70)]
        d.polygon(pts,fill=DEEPV+(int(aa*0.9),)); d.line(pts+[pts[0]],fill=col+(aa,),width=5)
        if GL: GL.line(pts+[pts[0]],fill=col+(int(aa*0.7),),width=12)
        ctext(d,lab,f(BEB,46),x+130,y+44,col,aa)

def overlays_b(im,t):
    L,d=newL()
    t1(L,d,t); t2(L,d,t); igf(L,d,t); gate(L,d,t); struct(L,d,t); dose(L,d,t); burn(L,d,t); waterfall(L,d,t); mirror(L,d,t); chevrons(L,d,t)
    im.alpha_composite(L)

# 10) end card: IGF-1 response + GH timing breakdown, COMMENT "PANEL"
T_END=LP1; E_IGF=at('igf-1',114.3); E_TIME=at('time',116.0); E_PH=at('phases',117.8); E_C=at('comment',118.7); E_W=at('panel',119.2); E_FREE=at('free',121.7)
sfxb(T_END,'whoosh',d=0.25,g=-28); sfxb(E_IGF,'thud',w=1.2,g=-18); sfxb(E_TIME,'tick',g=-24); sfxb(E_W,'impact',g=-15); sfxb(E_FREE,'tick',g=-25)
def end_b(im,t):
    if t<T_END: return
    q=ease_io((t-T_END)/0.35); im.alpha_composite(scene_bg(q)); L,d=newL(); a=int(255*q)
    lg=logo().copy(); lg.putalpha(lg.split()[3].point(lambda v:int(v*q))); L.alpha_composite(lg.resize((130,130)),(70,250))
    d.text((222,262),'COACH AGZ',font=f(BAR,52),fill=GOLD+(a,)); d.text((224,326),'@coach.agz',font=f(MONO,28),fill=MUTED+(a,))
    d.text((80,440),'THE FULL BREAKDOWN',font=f(BEB,72),fill=CREAM+(a,))
    for k,(lab,sub,tt,col) in enumerate((('IGF-1 RESPONSE','what drives it',E_IGF,ECYAN),('GH TIMING','around growth phases',E_TIME,VGOLD))):
        if t<tt-0.2: continue
        s=expo((t-tt+0.2)/0.22); y=560+k*200; aa=int(a*s)
        gpanel(d,(80,y,1000,y+170),col,aa,0.88); d.text((120,y+24),lab,font=f(BEB,90),fill=col+(aa,)); d.text((122,y+118),sub.upper(),font=f(MONOB,24),fill=MUTED+(aa,))
        if GL: GL.text((120,y+24),lab,font=f(BEB,90),fill=col+(int(aa*0.5),))
    if t>=E_PH: ruler(d,3,int(a*clamp((t-E_PH)/0.3)),y=1000)
    if t>=E_C:
        s=expo((t-E_C)/0.16); sc=lerp(1.5,1,s); fn=f(MONOB,int(58*sc)); txt='COMMENT "PANEL"'; w=d.textlength(txt,font=fn)
        lit_bar(d,540-w/2-30,1090,540+w/2+30,1090+fn.size+40,VGOLD,int(a*s)); d.text((540-w/2,1110),txt,font=fn,fill=DEEP+(int(a*s),))
        if GL and t<E_C+0.7: GL.rectangle([540-w/2-34,1086,540+w/2+34,1094+fn.size+40],outline=VGOLD+(int(220*(1-(t-E_C)/0.7)),),width=12)
    if t>=E_FREE: ctext(d,'SENT TO YOU · FREE',f(MONOB,34),540,1222,CREAM,int(a*clamp((t-E_FREE)/0.15)))
    ctext(d,DISC,f(MONO,20),540,1284,LABEL,a)
    ctext(d,'NOT MEDICAL ADVICE · WORK WITH YOUR DOCTOR',f(MONO,20),540,1314,LABEL,a)
    im.alpha_composite(L)

# ---------------- frame ----------------
SUBJECT_T=1.76      # visual hook: first punch-in lands on the spoken subject "growth hormone"
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
    if g>0: bg=Image.blend(src.filter(ImageFilter.GaussianBlur(18*g)),Image.new('RGB',(W,H),PUSH_TINT),0.68*g)
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
        ev=[dict(e,t=round(e['t'],3)) for e in EVB]; json.dump(sorted(ev,key=lambda e:e['t']),open(T+'events.json','w'),indent=0); print(len(ev),'events'); sys.exit()
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
