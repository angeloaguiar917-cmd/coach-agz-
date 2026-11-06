# Reel: "E2 same 80" (same estradiol, opposite symptoms): full edit, native 1080x1920, brand-neon overlay set
# Built on the saved setup: test-06 look + full-test-02 workflow (dead air trimmed, misspeak cut, 108% punch-in per jump cut,
# captions from the trimmed audio). Usage: python render.py <scratch> [--events|--groups|--still t..|--range n0 n1 out.mp4]
import json, subprocess, sys, math, re
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
S=sys.argv[1]; F=S+'/fonts/'; T=S+'/r14/work/'
W,H=1080,1920; FPS=30; N=3925; DUR=N/FPS
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
FIX={}
for i,n_,s_ in ((411,2,'SIDE-EFFECT'),(406,2,'CROSS-REFERENCE'),(369,3,'WEEK-TO-WEEK')): words[i]['w']=s_; words[i]['e']=words[i+n_-1]['e']; del words[i+1:i+n_]   # descending so indices hold
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
CUTS=[6.8333,18.3833,33.1667,56.1667,82.7167]   # no trims: the source's own jump cuts (scene detect) drive the punch-ins
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
HOOK_LINES=[[('Same ',CREAM),('E2',VGOLD),(' of 80',CREAM)],[('opposite symptoms',CREAM)]]
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
        for s,c in [('E2',VGOLD),(' is not just a number',CREAM)]: d.text((x,y),s,font=fn,fill=c+(a,)); x+=d.textlength(s,font=fn)
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



# ======================= "E2 same 80" overlay set (brand neon: v-gold, v-red, cyan, green, amber on deep navy) =======================
EVB=[]
def sfxb(t,kind,**k): EVB.append(dict(t=round(t,3),kind=kind,**k))
import re as _re2
def at(word,near):
    n=lambda s:_re2.sub(r'[^a-z0-9]','',s.lower()); best=None
    for w in words:
        if n(w['w']).startswith(n(word)) and abs(w['s']-near)<3.5 and (best is None or abs(w['s']-near)<abs(best-near)): best=w['s']
    if best is None: raise SystemExit('word not found: %s @%s'%(word,near))
    return best
VRED=(255,34,28); ECYAN=(0,229,255); NGREEN=(30,255,110); AMBER=(255,150,20); SBLUE=(60,160,255); DEEPV=(2,3,8)
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
def person(d,cx,cy,s,col,a):
    d.ellipse([cx-s*0.32,cy-s,cx+s*0.32,cy-s*0.36],fill=col+(a,)); d.rounded_rectangle([cx-s*0.55,cy-s*0.28,cx+s*0.55,cy+s*0.7],radius=int(s*0.3),fill=col+(a,))
C1,C2,C3,C4,C5=CUTS
S_PORTAL=(at('misled',12.8)-0.05, C2-0.06)
S_CLIFF=(C2+0.03, at('and',24.3)-0.05)
S_AROM=(at('when',26.6)-0.05, at("here's",35.7)-0.05)
S_FADER=(at("here's",35.7)-0.05, at('quite',44.4)-0.05)
S_STRIP=(at('quite',44.4)-0.05, C4-0.06)
S_DASH=(at("that's",59.2)-0.05, at("how's",70.0)-0.05)
S_FORM=(at("how's",70.0)-0.05, at('and',77.5)-0.05)
S_ICE=(at('and',77.5)-0.05, C5-0.06)
S_MIST=(C5+0.03, at('goal',96.9)-0.1)
S_MOLD=(at('goal',96.9)-0.1, at("that's",104.5)-0.05)
S_PAGE=(at('stop',111.4)-0.05, at('with',117.3)-0.05)
SCENES=[S_PORTAL,S_CLIFF,S_AROM,S_FADER,S_STRIP,S_DASH,S_FORM,S_ICE,S_MIST,S_MOLD,S_PAGE]
def B_push(t):
    g=0
    for a_,b_ in SCENES: g=max(g,clamp((t-a_)/0.22)*clamp((b_-t)/0.22))
    return ease_io(g)
for i,(a_,b_) in enumerate(SCENES):
    if i==0 or abs(a_-SCENES[i-1][1])>0.3: sfxb(a_,'whoosh',d=0.22,g=-28); sfxb(a_+0.2,'thud',w=1.2,g=-18)
    else: sfxb(a_,'scan',d=0.35,g=-29)

# 1) floating: two ID badges, same E2 80, opposite status lights
VS0=HOOK_END+0.1; VS1=at('so',8.9)-0.05; VS_Q=at('problem',8.2)
sfxb(VS0+0.05,'tick',g=-25); sfxb(VS0+0.25,'tick',g=-25); sfxb(VS_Q,'thud',w=1.1,g=-18)
def versus(L,d,t):
    a=int(255*float_a(t,VS0,VS1))
    if a<=0: return
    for k,(x0,lab,col,st) in enumerate(((50,'GUY A',NGREEN,'PHENOMENAL'),(570,'GUY B',VRED,'TOTAL GARBAGE'))):
        q=expo((t-VS0-k*0.2)/0.25); aa=int(a*q); dy=40*(1-q)
        if aa<=0: continue
        gpanel(d,(x0,392+dy,x0+460,700+dy),col,aa,0.88)
        d.text((x0+28,410+dy),lab,font=f(MONOB,26),fill=MUTED+(aa,))
        person(d,x0+90,560+dy,80,(60,66,80),aa)
        d.text((x0+190,420+dy),'ESTRADIOL',font=f(MONOB,22),fill=LABEL+(aa,))
        d.text((x0+186,440+dy),'80',font=f(BEB,150),fill=VGOLD+(aa,))
        if GL: GL.text((x0+186,440+dy),'80',font=f(BEB,150),fill=VGOLD+(int(aa*0.5),))
        lx,ly=x0+40,650+dy; pul=0.75+0.25*math.sin(t*9+k)
        d.ellipse([lx-12,ly-12,lx+12,ly+12],fill=col+(int(aa*pul),))
        if GL: GL.ellipse([lx-18,ly-18,lx+18,ly+18],fill=col+(int(aa*0.8*pul),))
        d.text((lx+26,ly-16),st,font=f(MONOB,26),fill=col+(aa,))
    if t>=VS_Q:
        s=expo((t-VS_Q)/0.18); r=66*lerp(1.6,1,s)
        d.ellipse([540-r,546-r,540+r,546+r],fill=VGOLD+(int(a*s),))
        if GL: GL.ellipse([540-r-6,546-r-6,540+r+6,546+r+6],outline=VGOLD+(int(a*s*0.8),),width=12)
        ctext(d,'?',f(BEB,int(r*1.5)),540,546-r*0.72,DEEP,int(a*s))

# 2) lab-portal phone: the number in red, the abnormal-result push
PT_REF=at('reference',14.1); PT_HI=at('highlighted',15.9); PT_RED=at('red',16.6); PT_DG=at('danger',17.3)
sfxb(PT_REF,'tick',g=-25); sfxb(PT_RED,'tick',g=-22); sfxb(PT_DG,'impact',g=-16)
def portal(L,d,t):
    if t<S_PORTAL[0] or t>S_PORTAL[1]+0.25: return
    a=int(255*scene_a(t,S_PORTAL))
    kinetic(d,'THE LAB PORTAL',f(BEB,104),70,400,S_PORTAL[0]+0.08,t,CREAM,-1)
    q=expo((t-S_PORTAL[0]-0.1)/0.35); dy=80*(1-q); aa=int(a*q)
    x0,y0,x1,y1=270,540+dy,810,1330+dy
    d.rounded_rectangle([x0,y0,x1,y1],radius=56,fill=(14,16,22,aa),outline=(90,96,110,aa),width=6)
    d.rounded_rectangle([x0+22,y0+22,x1-22,y1-22],radius=40,fill=(238,240,244,aa))
    d.rounded_rectangle([490,y0+34,590,y0+52],radius=9,fill=(14,16,22,aa))
    d.text((x0+56,y0+80),'MY HEALTH',font=f(MONOB,24),fill=(90,96,110,aa)); d.text((x0+56,y0+112),'Lab results',font=f(BAR,48),fill=(20,22,30,aa))
    rows=[('TESTOSTERONE, TOTAL',False),('ESTRADIOL',True),('SHBG',False),('HEMATOCRIT',False)]
    for k,(lab,hot) in enumerate(rows):
        y=y0+200+k*120; red=hot and t>=PT_RED
        d.rounded_rectangle([x0+44,y,x1-44,y+100],radius=16,fill=((255,232,230,aa) if red else (252,252,253,aa)),outline=((230,30,40,aa) if red else (215,218,224,aa)),width=3 if red else 2)
        d.text((x0+70,y+16),lab,font=f(MONOB,22),fill=(40,44,56,aa))
        if hot:
            d.text((x0+70,y+44),'80',font=f(BEB,56),fill=((220,20,30,aa) if red else (20,22,30,aa)))
            if red:
                pul=0.6+0.4*math.sin(t*12); d.rounded_rectangle([x1-150,y+30,x1-66,y+70],radius=10,fill=(230,20,40,int(aa*pul)))
                d.text((x1-136,y+34),'H ▲'.replace('▲',''),font=f(MONOB,28),fill=(255,255,255,aa)); tri(d,x1-104,y+40,20,True,(255,255,255,aa))
                if GL: GL.rounded_rectangle([x0+44,y,x1-44,y+100],radius=16,outline=VRED+(int(aa*0.7*pul),),width=10)
        else: d.rectangle([x0+70,y+56,x0+200,y+78],fill=(200,204,212,aa))
        if t>=PT_REF:
            s=clamp((t-PT_REF)/0.25); d.text((x0+300,y+58),'REF RANGE',font=f(MONO,18),fill=(130,136,150,int(aa*s))); d.rectangle([x0+410,y+62,x0+470,y+74],fill=(200,204,212,int(aa*s)))
    if t>=PT_DG:     # push notification drops in from the top of the screen
        s=expo((t-PT_DG)/0.25); ny=lerp(y0-40,y0+64,s)
        d.rounded_rectangle([x0+36,ny,x1-36,ny+96],radius=20,fill=(28,30,38,int(aa*s)),outline=VRED+(int(aa*s),),width=3)
        tri(d,x0+60,ny+26,40,True,VRED+(int(aa*s),)); d.text((x0+77,ny+34),'!',font=f(BEB,34),fill=(255,255,255,int(aa*s)))
        d.text((x0+120,ny+14),'ABNORMAL RESULT',font=f(MONOB,28),fill=(255,255,255,int(aa*s))); d.text((x0+120,ny+52),'Estradiol flagged HIGH',font=f(BAR,30),fill=MUTED+(int(aa*s),))
        if GL and t<PT_DG+0.6: GL.rounded_rectangle([x0+36,ny,x1-36,ny+96],radius=20,outline=VRED+(int(220*(1-(t-PT_DG)/0.6)),),width=12)

# 3) where the range comes from: population strip + the "magic cutoff" that isn't
CF_POP=at('population',19.6); CF_MAG=at('magical',21.1); CF_SUD=at('suddenly',23.1); CF_DNG=at('dangerous',23.8)
sfxb(CF_POP,'scan',d=0.6,g=-30); sfxb(CF_MAG,'tick',g=-24); sfxb(CF_DNG,'impact',g=-16)
def cliff(L,d,t):
    if t<S_CLIFF[0] or t>S_CLIFF[1]+0.25: return
    a=int(255*scene_a(t,S_CLIFF))
    kinetic(d,'WHERE THE RANGE COMES FROM',f(BEB,80),70,410,S_CLIFF[0]+0.08,t,ECYAN,-1)
    x0,x1=90,990; yb=1120
    d.line([(x0,yb),(x1,yb)],fill=MUTED+(a,),width=3); d.text((x1-150,yb+16),'E2 LEVEL →',font=f(MONOB,22),fill=LABEL+(a,))
    if t>=CF_POP-0.2:
        n=int(170*clamp((t-CF_POP+0.2)/0.8)); rng=np.random.default_rng(11)
        for k in range(n):
            u=float(np.clip(rng.normal(0.5,0.17),0.03,0.97)); y=yb-24-rng.random()*230*math.exp(-((u-0.5)/0.2)**2/2)
            d.ellipse([lerp(x0,x1,u)-5,y-5,lerp(x0,x1,u)+5,y+5],fill=ECYAN+(int(a*0.75),))
        s=ease_io((t-CF_POP)/0.6)
        if s>0:
            r0,r1=lerp(x0,x1,0.5-0.32*s),lerp(x0,x1,0.5+0.32*s)
            d.rectangle([r0,yb+8,r1,yb+26],fill=VGOLD+(a,))
            if GL: GL.rectangle([r0,yb+8,r1,yb+26],fill=VGOLD+(int(a*0.5),))
            ctext(d,'REFERENCE POPULATION',f(MONOB,26),540,yb+44,VGOLD,int(a*s))
    if t>=CF_MAG:     # the imagined cliff: flat, then a wall
        s=ease_io((t-CF_MAG)/0.5); cx=lerp(x0,x1,0.82); yl,yh=780,560
        pts=[(x0,yl),(lerp(x0,cx,min(1,s*1.4)),yl)]
        if s>0.7: pts+=[(cx,yl),(cx,lerp(yl,yh,(s-0.7)/0.3)),(lerp(cx,x1,(s-0.7)/0.3),yh)] if s<1 else [(cx,yl),(cx,yh),(x1,yh)]
        fade=1-0.6*clamp((t-CF_SUD)/0.3)
        dashed(d,pts,VRED+(int(a*fade),),6,18,12)
        ctext(d,'"MAGIC CUTOFF"',f(MONOB,28),cx-10,yh-50,VRED,int(a*s*fade))
    if t>=CF_SUD:
        s=expo((t-CF_SUD)/0.16); cx=lerp(x0,x1,0.82)
        d.line([(cx-60,560),(cx+60,800)],fill=VRED+(int(a*s),),width=10); d.line([(cx+60,560),(cx-60,800)],fill=VRED+(int(a*s),),width=10)
        if GL: GL.line([(cx-60,560),(cx+60,800)],fill=VRED+(int(a*s*0.7),),width=20)
    if t>=CF_DNG: pill(d,540,1260,'NO MAGIC LINE',f(MONOB,40),VRED,(255,255,255),int(a*clamp((t-CF_DNG)/0.2)))

# 4) aromatization flow: T particles through the aromatase gate become E2
AR_RUN=at('running',26.9); AR_SUB=at('substrate',28.6); AR_MORE=at('more',30.5); AR_CONV=at('converting',31.9); AR_INC=at('increase',35.2)
sfxb(AR_SUB,'tick',g=-25); sfxb(AR_MORE,'scan',d=0.6,g=-30); sfxb(AR_CONV,'tick',g=-24); sfxb(AR_INC,'thud',w=1.1,g=-18)
def arom(L,d,t):
    if t<S_AROM[0] or t>S_AROM[1]+0.25: return
    a=int(255*scene_a(t,S_AROM))
    kinetic(d,'AROMATIZATION',f(BEB,120),70,400,S_AROM[0]+0.08,t,AMBER,-1)
    lv_t=0.45+0.4*ease_io((t-AR_SUB)/0.6) if t>=AR_SUB else 0.45
    lv_e=0.2+0.55*ease_io((t-AR_INC)/0.8) if t>=AR_INC else 0.2+0.15*clamp((t-AR_CONV)/3.0)
    for (x0,lab,col,lv) in ((80,'TESTOSTERONE',VGOLD,lv_t),(770,'ESTRADIOL',ECYAN,lv_e)):
        yb,yt=1200,700
        d.rounded_rectangle([x0,yt,x0+230,yb],radius=26,outline=col+(a,),width=5)
        d.rounded_rectangle([x0+10,yb-(yb-yt-20)*lv,x0+220,yb-10],radius=18,fill=col+(int(a*0.75),))
        if GL: GL.rounded_rectangle([x0,yt,x0+230,yb],radius=26,outline=col+(int(a*0.7),),width=12)
        ctext(d,lab,f(BEB,48),x0+115,yb+16,col,a)
    gx0,gx1,gy0,gy1=430,650,820,980
    d.rounded_rectangle([gx0,gy0,gx1,gy1],radius=20,fill=DEEPV+(a,),outline=AMBER+(a,),width=5)
    if GL: GL.rounded_rectangle([gx0,gy0,gx1,gy1],radius=20,outline=AMBER+(int(a*(0.6+0.4*clamp((t-AR_CONV)/0.3))),),width=14)
    ctext(d,'AROMATASE',f(BEB,48),540,gy0+56,AMBER,a)
    nline(d,[(310,900),(430,900)],(60,66,80),18,a); nline(d,[(650,900),(770,900)],(60,66,80),18,a)
    n=10 if t<AR_MORE else 22; spd=0.55 if t<AR_MORE else 0.8
    if t>=AR_RUN:
        for k in range(n):
            p=((t-AR_RUN)*spd+k/n)%1.0; x=lerp(300,780,p); y=900+8*math.sin(p*20+k)
            col=VGOLD if x<540 else ECYAN
            if gx0<x<gx1: continue
            d.ellipse([x-9,y-9,x+9,y+9],fill=col+(a,))
            if GL: GL.ellipse([x-13,y-13,x+13,y+13],fill=col+(int(a*0.6),))
    if t>=AR_SUB: ctext(d,'MORE SUBSTRATE',f(MONOB,28),195,640,VGOLD,int(a*clamp((t-AR_SUB)/0.2)))
    if t>=AR_INC:
        s=expo((t-AR_INC)/0.18); ctext(d,'E2',f(BEB,96),885,560+10*(1-s),ECYAN,int(a*s),True); tri(d,940,590,40,True,ECYAN+(int(a*s),))

# 5) mixing console: genetics, tissue sensitivity, physiology -> your response
FD=[('GENETICS','',at('genetics',37.5),VGOLD,0.7),('TISSUE','SENSITIVITY',at('tissue',38.3),ECYAN,0.35),('INDIVIDUAL','PHYSIOLOGY',at('individual',39.7),AMBER,0.58)]
FD_DIF=at('differently',41.8)
for *_,tt,_c,_v in FD: sfxb(tt,'tick',g=-24)
sfxb(FD_DIF,'thud',w=1.0,g=-19)
def faders(L,d,t):
    if t<S_FADER[0] or t>S_FADER[1]+0.25: return
    a=int(255*scene_a(t,S_FADER))
    kinetic(d,'WHY RESPONSES DIFFER',f(BEB,100),70,400,S_FADER[0]+0.08,t,CREAM,-1)
    gpanel(d,(60,540,1020,1330),VGOLD,a,0.7)
    yt,yb=620,1120; outv=0
    for k,(l1,l2,tt,col,v) in enumerate(FD):
        x=190+k*230; on=t>=tt
        d.rounded_rectangle([x-8,yt,x+8,yb],radius=8,fill=(40,44,56,a))
        for j in range(11): yy=lerp(yt,yb,j/10); d.line([(x-34,yy),(x-20,yy)],fill=(70,74,86,a),width=2)
        q=ease_io((t-tt)/0.5) if on else 0; vv=lerp(0.15,v,q)+(0.03*math.sin(t*2+k) if on else 0); outv+=vv
        ky=lerp(yb,yt,vv)
        d.rounded_rectangle([x,yt+(yb-yt)*(1-vv),x+0.1,yb],radius=4,fill=col+(a,))
        d.line([(x,ky),(x,yb)],fill=col+(a if on else int(a*0.3),),width=12)
        if GL and on: GL.line([(x,ky),(x,yb)],fill=col+(int(a*0.6),),width=22)
        d.rounded_rectangle([x-46,ky-24,x+46,ky+24],radius=8,fill=(200,204,212,a),outline=col+(a if on else int(a*0.3),),width=4)
        ctext(d,l1,f(BEB,44),x,1150,col if on else MUTED,a);
        if l2: ctext(d,l2,f(BEB,44),x,1196,col if on else MUTED,a)
    mx=880; lvl=clamp(outv/2.0)
    d.text((mx-70,580),'YOUR',font=f(MONOB,24),fill=CREAM+(a,)); d.text((mx-70,608),'RESPONSE',font=f(MONOB,24),fill=CREAM+(a,))
    for j in range(16):
        yy=yb-j*30; lit=j/16<lvl; col=NGREEN if j<9 else (AMBER if j<13 else VRED)
        d.rectangle([mx-40,yy-22,mx+40,yy],fill=col+(int(a*(0.95 if lit else 0.15)),))
        if GL and lit: GL.rectangle([mx-40,yy-22,mx+40,yy],fill=col+(int(a*0.35),))
    if t>=FD_DIF: pill(d,540,1250,'SAME NUMBER · DIFFERENT RESPONSE',f(MONOB,30),VGOLD,DEEP,int(a*clamp((t-FD_DIF)/0.2)))

# 6) strip plot: who feels great at 80/90 vs who struggles at 80
SP_80=at('80',48.5); SP_90=at('90',49.0); SP_OTH=at('other',50.0); SP_SYM=[('LIBIDO ISSUES',at('libido',51.5)),('MOOD CHANGES',at('mood',52.5)),('NIPPLE SENSITIVITY',at('nipple',53.2))]; SP_T80=at('80',55.4)
sfxb(SP_80,'tick',g=-24); sfxb(SP_90,'tick',g=-24); sfxb(SP_OTH,'tick',g=-24)
for _,tt in SP_SYM: sfxb(tt,'tick',g=-23)
sfxb(SP_T80,'impact',g=-16)
def strip(L,d,t):
    if t<S_STRIP[0] or t>S_STRIP[1]+0.25: return
    a=int(255*scene_a(t,S_STRIP))
    kinetic(d,'SAME RANGE · TWO STORIES',f(BEB,92),70,400,S_STRIP[0]+0.08,t,CREAM,-1)
    x0,x1=170,990; X=lambda v:lerp(x0,x1,(v-60)/40); ya,yb_,yax=680,1000,1200
    d.line([(x0,yax),(x1,yax)],fill=MUTED+(a,),width=3)
    for v in (60,70,80,90,100):
        d.line([(X(v),yax-8),(X(v),yax+8)],fill=MUTED+(a,),width=3); ctext(d,str(v),f(MONO,24),X(v),yax+16,LABEL,a)
    ctext(d,'ESTRADIOL',f(MONOB,22),540,yax+50,LABEL,a)
    for y,lab,col in ((ya,'FEEL',NGREEN),(yb_,'STRUGGLE',VRED)):
        d.line([(x0,y),(x1,y)],fill=(40,44,56,a),width=2); d.text((60,y-58),lab,font=f(BEB,48),fill=col+(a,))
    for v,tt in ((80,SP_80),(90,SP_90)):
        if t<tt: continue
        s=expo((t-tt)/0.2); r=26*s
        d.ellipse([X(v)-r,ya-r,X(v)+r,ya+r],fill=NGREEN+(a,))
        if GL: GL.ellipse([X(v)-r-8,ya-r-8,X(v)+r+8,ya+r+8],fill=NGREEN+(int(a*0.6),))
        ctext(d,'FANTASTIC',f(MONOB,22),X(v),ya-70,NGREEN,int(a*s))
    if t>=SP_OTH:
        s=expo((t-SP_OTH)/0.2); r=26*s; px=X(80)
        d.ellipse([px-r,yb_-r,px+r,yb_+r],fill=VRED+(a,))
        if GL: GL.ellipse([px-r-8,yb_-r-8,px+r+8,yb_+r+8],fill=VRED+(int(a*0.6),))
        for k,(lab,tt) in enumerate(SP_SYM):
            if t<tt: continue
            q=expo((t-tt)/0.18); fn=f(MONOB,24); w=d.textlength(lab,font=fn)
            cx=[X(80)-230,X(80)+230,X(80)+250][k]; cy=[yb_-120,yb_-120,yb_+50][k]; cx=min(max(cx,70+w/2+16),1010-w/2-16)
            nline(d,[(px,yb_),(cx,cy+24)],VRED,2,int(a*q*0.7))
            d.rounded_rectangle([cx-w/2-16,cy,cx+w/2+16,cy+48],radius=10,fill=(40,10,10,int(a*q)),outline=VRED+(int(a*q),),width=3)
            d.text((cx-w/2,cy+10),lab,font=fn,fill=(255,200,195,int(a*q)))
    if t>=SP_T80:
        s=ease_io((t-SP_T80)/0.35); dashed(d,[(X(80),ya-30),(X(80),lerp(ya-30,yax,s))],VGOLD+(a,),4,14,10)
        pill(d,X(80),yax-90,'SAME 80',f(MONOB,30),VGOLD,DEEP,int(a*s))

# 7) floating verdict: neither 80 is proof on its own
VD0=C4+0.05; VD1=S_DASH[0]-0.05; VD_PR=at('proves',57.2)
sfxb(VD_PR,'impact',g=-15)
def verdict(L,d,t):
    a=int(255*float_a(t,VD0,VD1))
    if a<=0: return
    gpanel(d,(40,392,1040,700),VRED,a,0.88)
    for k,x in enumerate((200,520)):
        d.text((x,404),'80',font=f(BEB,180),fill=VGOLD+(a,))
        d.text((x+150,430),'GUY A' if k==0 else 'GUY B',font=f(MONOB,22),fill=MUTED+(a,))
    ctext(d,'=',f(BEB,140),450,420,MUTED,a)
    if t>=VD_PR:
        s=expo((t-VD_PR)/0.14); w=lerp(0,960,s)
        lit_bar(d,60,600,60+w,680,VRED,a)
        if GL: GL.rectangle([60,600,60+w,680],outline=VRED+(int(a*0.7),),width=10)
        if s>0.7: ctext(d,'NEITHER ONE IS PROOF',f(BEB,74),540,604,(255,255,255),a)

# 8) dashboard assembling: E2 with T, free T, SHBG, symptoms, side effects
DS=[('SENSITIVE E2',at('sensitive',61.6),ECYAN,(-1,0)),('TOTAL T',at('testosterone',62.8),VGOLD,(1,0)),('FREE T',at('free',63.7),AMBER,(-1,0)),('SHBG',at('shbg',64.7),SBLUE,(1,0))]
DS_IMP=at('importantly',65.9); DS_SYM=at('symptom',67.0); DS_SIDE=at('side',68.5)
for _,tt,_c,_v in DS: sfxb(tt,'thud',w=0.8,g=-21)
sfxb(DS_SYM,'thud',w=1.1,g=-18); sfxb(DS_SIDE,'thud',w=1.0,g=-19)
def spark(d,x0,y0,x1,y1,col,a,seed):
    rng=np.random.default_rng(seed); v=np.cumsum(rng.normal(0,1,24)); v=(v-v.min())/(np.ptp(v)+1e-6)
    pts=[(lerp(x0,x1,i/23),y1-(y1-y0)*float(v[i])) for i in range(24)]; nline(d,pts,col,3,a)
def dash(L,d,t):
    if t<S_DASH[0] or t>S_DASH[1]+0.25: return
    a=int(255*scene_a(t,S_DASH))
    kinetic(d,'CROSS-REFERENCE THE DATA',f(BEB,88),70,400,S_DASH[0]+0.08,t,CREAM,-1)
    boxes=[(60,530,530,730),(550,530,1020,730),(60,750,530,950),(550,750,1020,950)]
    for k,((lab,tt,col,(dx,_)),(x0,y0,x1,y1)) in enumerate(zip(DS,boxes)):
        q=expo((t-tt)/0.25)
        if q<=0: continue
        off=dx*(1-q)*600; aa=int(a*q)
        gpanel(d,(x0+off,y0,x1+off,y1),col,aa,0.8)
        d.text((x0+off+26,y0+18),lab,font=f(BEB,54),fill=col+(aa,))
        spark(d,x0+off+30,y0+96,x1+off-30,y1-26,col,aa,k+3)
    for k,(lab,tt,col,y0) in enumerate((('SYMPTOM PROFILE',DS_SYM,NGREEN,975),('SIDE-EFFECT RESPONSE',DS_SIDE,VRED,1105))):
        q=expo((t-tt)/0.25)
        if q<=0: continue
        aa=int(a*q); yy=y0+60*(1-q)
        gpanel(d,(60,yy,1020,yy+110),col,aa,0.85); d.text((90,yy+22),lab,font=f(BEB,64),fill=col+(aa,))
        for j in range(5): d.ellipse([720+j*56,yy+40,750+j*56,yy+70],fill=col+(int(aa*(0.9 if j<3+k else 0.2)),))
    if t>=DS_SYM: pill(d,780,958,'MOST IMPORTANT',f(MONOB,26),NGREEN,DEEP,int(a*clamp((t-DS_SYM)/0.2)))

# 9) check-in form: the questions he asks
FM=[('LIBIDO',at('libido',70.2)),('ERECTIONS',at('erections',70.9)),('MOOD',at('mood',71.6)),('JOINT COMFORT',at('joint',72.1)),('BREAST TENDERNESS',at('breast',73.6)),('BLOOD PRESSURE',at('blood',75.5))]
FM_CON=at('consistent',76.3)
for _,tt in FM: sfxb(tt,'tick',g=-24)
def form(L,d,t):
    if t<S_FORM[0] or t>S_FORM[1]+0.25: return
    a=int(255*scene_a(t,S_FORM))
    kinetic(d,'THE CHECK-IN',f(BEB,110),70,400,S_FORM[0]+0.08,t,VGOLD,-1)
    q=expo((t-S_FORM[0]-0.1)/0.3); dy=60*(1-q); aa=int(a*q)
    x0,y0,x1,y1=130,560+dy,950,1330+dy
    d.rectangle([x0+10,y0+12,x1+10,y1+12],fill=(0,0,0,int(aa*0.4)))
    d.rectangle([x0,y0,x1,y1],fill=(240,238,232,aa))
    d.rounded_rectangle([450,y0-30,630,y0+30],radius=12,fill=(150,150,156,aa),outline=(90,90,96,aa),width=4)
    d.text((x0+40,y0+44),'WEEKLY CHECK-IN',font=f(MONOB,30),fill=(30,30,36,aa)); d.line([(x0+40,y0+92),(x1-40,y0+92)],fill=(170,170,176,aa),width=2)
    for k,(lab,tt) in enumerate(FM):
        y=y0+120+k*100
        d.rectangle([x0+40,y,x0+86,y+46],outline=(60,60,70,aa),width=4)
        d.text((x0+110,y+4),lab,font=f(BAR,44),fill=(30,30,36,aa))
        d.line([(x0+520,y+40),(x1-40,y+40)],fill=(180,180,186,aa),width=2)
        if t>=tt:
            s=ease_io((t-tt)/0.25); px=x0+44; py=y+20
            pts=[(px,py),(px+14,py+20),(px+46,py-18)]; seg=pts[:2] if s<0.4 else pts
            if s<0.4: seg=[pts[0],(lerp(pts[0][0],pts[1][0],s/0.4),lerp(pts[0][1],pts[1][1],s/0.4))]
            elif s<1: seg=[pts[0],pts[1],(lerp(pts[1][0],pts[2][0],(s-0.4)/0.6),lerp(pts[1][1],pts[2][1],(s-0.4)/0.6))]
            d.line(seg,fill=(20,150,70,aa),width=7,joint='curve')
            if k==5 and t>=FM_CON: d.text((x0+540,y+2),'CONSISTENTLY',font=f(MONOB,24),fill=(200,30,40,aa))

# 10) iceberg: feeling great is the tip
IC_FG=at('feeling',79.1); IC_DS=at("doesn't",79.7); IC_SAFE=at('safe',81.9)
sfxb(IC_FG,'tick',g=-24); sfxb(IC_DS,'scan',d=0.6,g=-30); sfxb(IC_SAFE,'thud',w=1.2,g=-18)
def iceberg(L,d,t):
    if t<S_ICE[0] or t>S_ICE[1]+0.25: return
    a=int(255*scene_a(t,S_ICE))
    kinetic(d,'BELOW THE SURFACE',f(BEB,100),70,400,S_ICE[0]+0.08,t,ECYAN,-1)
    wl=760
    sh=Image.new('RGBA',(W,H),(0,0,0,0)); sd=ImageDraw.Draw(sh)
    sd.rectangle([0,wl,W,1360],fill=(0,60,90,int(a*0.35)))
    reveal=ease_io((t-IC_DS)/0.6) if t>=IC_DS else 0
    sd.polygon([(420,wl),(540,600),(660,wl)],fill=(225,245,255,int(a*0.95)))
    sd.polygon([(300,wl),(780,wl),(900,1000),(700,1300),(360,1310),(180,1050)],fill=(40,150,200,int(a*(0.25+0.45*reveal))))
    L.alpha_composite(sh)
    for x in range(0,W,40): d.line([(x,wl+6*math.sin(x/60+t*3)),(x+40,wl+6*math.sin((x+40)/60+t*3))],fill=ECYAN+(a,),width=4)
    if GL: GL.line([(0,wl),(W,wl)],fill=ECYAN+(int(a*0.5),),width=10)
    if t>=IC_FG: pill(d,540,520,'FEELING GREAT',f(MONOB,36),NGREEN,DEEP,int(a*clamp((t-IC_FG)/0.2)))
    for k,(lab,col) in enumerate((('BLOOD PRESSURE',VRED),('BLOODWORK MARKERS',AMBER),('SIDE-EFFECT DATA',VGOLD))):
        q=clamp((reveal-k*0.25)/0.5)
        if q>0: ctext(d,lab,f(BEB,64),540,850+k*110,col,int(a*q),True)
    if t>=IC_SAFE: pill(d,540,1250,'NOT AUTOMATICALLY SAFE',f(MONOB,36),VRED,(255,255,255),int(a*clamp((t-IC_SAFE)/0.2)))

# 11) the biggest mistake: E2 flagged -> AI -> crash -> new problems
MS_BIG=at('biggest',83.0); MS_EL=at('elevated',86.5); MS_AI=at('aromatase',90.2); MS_FAN=at('fantastic',92.2); MS_CR=at('crashing',93.7); MS_NEW=at('problems',95.9)
sfxb(MS_EL,'tick',g=-23); sfxb(MS_AI,'thud',w=1.0,g=-19); sfxb(MS_FAN,'tick',g=-24); sfxb(MS_CR,'impact',g=-15); sfxb(MS_NEW,'tick',g=-22)
def mistake(L,d,t):
    if t<S_MIST[0] or t>S_MIST[1]+0.25: return
    a=int(255*scene_a(t,S_MIST))
    kinetic(d,'THE BIGGEST MISTAKE',f(BEB,110),70,400,MS_BIG-0.1,t,VRED,-1)
    x0,x1,yt,yb=100,990,620,1180; ylo=yb-90
    gpanel(d,(60,580,1020,1240),VRED,a,0.55)
    d.rectangle([x0,ylo,x1,yb],fill=VRED+(int(a*0.12),)); d.text((x0+10,yb-40),'TOO LOW',font=f(MONOB,22),fill=VRED+(a,))
    def E(u):
        if u<0.55: return 0.62+0.04*math.sin(u*12)
        return lerp(0.62,0.05,ease_io((u-0.55)/0.2)) if u<0.75 else 0.05+0.02*math.sin(u*30)
    ux=lambda tt: clamp((tt-S_MIST[0]-0.4)/(MS_NEW-S_MIST[0]-0.2))
    # timeline position: ELEVATED->AI at u 0.4-0.55, crash 0.55-0.75 timed on the words
    def u_at(tt):
        if tt<MS_EL: return 0.3*clamp((tt-S_MIST[0])/(MS_EL-S_MIST[0]))
        if tt<MS_AI: return lerp(0.3,0.5,clamp((tt-MS_EL)/(MS_AI-MS_EL)))
        if tt<MS_CR: return lerp(0.5,0.55,clamp((tt-MS_AI)/(MS_CR-MS_AI)))
        if tt<MS_NEW: return lerp(0.55,0.8,clamp((tt-MS_CR)/(MS_NEW-MS_CR)))
        return lerp(0.8,1.0,clamp((tt-MS_NEW)/0.6))
    u=u_at(t); n=int(200*u)
    pts=[(lerp(x0,x1,k/200),yb-(yb-yt)*E(k/200)) for k in range(n+1)]
    col_pts=[p for p in pts if p[0]<=lerp(x0,x1,0.55)]; red_pts=[p for p in pts if p[0]>=lerp(x0,x1,0.55)-1]
    nline(d,col_pts,ECYAN,6,a); nline(d,red_pts,VRED,6,a)
    def flag(u_,lab,col,above=True):
        px=lerp(x0,x1,u_); py=yb-(yb-yt)*E(u_); ty=py-90 if above else py+30
        d.ellipse([px-12,py-12,px+12,py+12],fill=col+(a,)); fn=f(MONOB,24); w=d.textlength(lab,font=fn); tx=min(max(px-w/2,80),1000-w)
        d.rounded_rectangle([tx-12,ty,tx+w+12,ty+44],radius=10,fill=DEEPV+(a,),outline=col+(a,),width=3); d.text((tx,ty+9),lab,font=fn,fill=col+(a,))
    if t>=MS_EL: flag(0.3,'ELEVATED E2 FLAG',VGOLD)
    if t>=MS_FAN: flag(0.12,'FEELS FANTASTIC',NGREEN,False)
    if t>=MS_AI:
        s=expo((t-MS_AI)/0.2); px=lerp(x0,x1,0.53); py=lerp(560,yb-(yb-yt)*E(0.53)-40,s)
        d.rounded_rectangle([px-46,py-22,px+46,py+22],radius=22,fill=AMBER+(a,)); ctext(d,'AI',f(BEB,40),px,py-20,DEEP,a)
        if GL: GL.rounded_rectangle([px-50,py-26,px+50,py+26],radius=24,outline=AMBER+(int(a*0.7),),width=8)
    if t>=MS_CR: flag(0.7,'E2 CRASHED',VRED,False) if t<MS_NEW else None
    if t>=MS_NEW: pill(d,700,940,'NEW SET OF PROBLEMS',f(MONOB,32),VRED,(255,255,255),int(a*clamp((t-MS_NEW)/0.2)))

# 12) no one-size number: bars forced to one line, then the three moves
MD_FORCE=at('force',97.5); MD_NUM=at('estrogenic',98.9); MD_STEPS=[('INTERPRET','BLOODWORK',at('interpret',100.9),ECYAN),('INVESTIGATE','SYMPTOMS',at('investigate',102.0),AMBER),('INFORMED','DECISIONS',at('informed',103.5),NGREEN)]
sfxb(MD_FORCE,'thud',w=1.2,g=-18); sfxb(MD_NUM,'impact',g=-16)
for *_,tt,_c in MD_STEPS: sfxb(tt,'thud',w=0.9,g=-20)
def mold(L,d,t):
    if t<S_MOLD[0] or t>S_MOLD[1]+0.25: return
    a=int(255*scene_a(t,S_MOLD))
    kinetic(d,'NO ONE-SIZE NUMBER',f(BEB,110),70,400,S_MOLD[0]+0.08,t,CREAM,-1)
    hs=[0.55,0.8,0.42,0.7,0.62,0.9,0.5,0.74]; yb=860; tgt=0.62
    sq=ease_io((t-MD_FORCE)/0.35) if t>=MD_FORCE else 0
    back=ease_io((t-MD_NUM)/0.4) if t>=MD_NUM else 0; f_=sq*(1-back)
    for k,h in enumerate(hs):
        x=110+k*112; hh=lerp(h,tgt,f_)*300
        d.rounded_rectangle([x,yb-hh,x+80,yb],radius=10,fill=(ECYAN if k%2 else VGOLD)+(int(a*0.85),))
    if t>=MD_FORCE-0.2:
        yl=yb-tgt*300; dashed(d,[(90,yl),(1000,yl)],VRED+(a,),5,16,10); d.text((830,yl-40),'ONE NUMBER',font=f(MONOB,22),fill=VRED+(a,))
    if t>=MD_NUM:
        s=expo((t-MD_NUM)/0.16); cx,cy=540,yb-150
        for dd in ((-90,-90,90,90),(90,-90,-90,90)): d.line([(cx+dd[0]*s,cy+dd[1]*s),(cx+dd[2]*s,cy+dd[3]*s)],fill=VRED+(a,),width=18)
        if GL: GL.line([(cx-90*s,cy-90*s),(cx+90*s,cy+90*s)],fill=VRED+(int(a*0.6),),width=30)
        if t>MD_NUM+0.9: pass
    for k,(l1,l2,tt,col) in enumerate(MD_STEPS):
        q=expo((t-tt)/0.22)
        if q<=0: continue
        x0=60+k*325; y0=1090-k*80-40*(1-q); aa=int(a*q)
        gpanel(d,(x0,y0,x0+305,1300),col,aa,0.85)
        ctext(d,l1,f(BEB,52),x0+152,y0+14,col,aa,True); ctext(d,l2,f(BEB,40),x0+152,y0+70,CREAM,aa)

# 13) floating: the weekly loop (analyze, pivot, optimize)
LP0=S_MOLD[1]; LP1=S_PAGE[0]-0.05
LP=[('ANALYZE',at('analyze',105.1),ECYAN),('PIVOT',at('pivot',105.9),AMBER),('OPTIMIZE',at('optimize',106.5),NGREEN)]
LP_WK=at('week',110.1)
for _,tt,_c in LP: sfxb(tt,'tick',g=-24)
sfxb(LP_WK,'scan',d=0.5,g=-30)
def loop(L,d,t):
    a=int(255*float_a(t,LP0,LP1))
    if a<=0: return
    gpanel(d,(40,392,1040,700),VGOLD,a,0.88)
    cx,cy,r=190,546,104; rot=(t-LP0)*120
    for k in range(3):
        st=rot+k*120+12; en=st+96
        d.arc([cx-r,cy-r,cx+r,cy+r],start=st,end=en,fill=LP[k][2]+(a,),width=12)
        ang=math.radians(en); hx,hy=cx+r*math.cos(ang),cy+r*math.sin(ang); tg=ang+math.pi/2
        d.polygon([(hx+20*math.cos(tg),hy+20*math.sin(tg)),(hx+16*math.cos(ang),hy+16*math.sin(ang)),(hx-16*math.cos(ang),hy-16*math.sin(ang))],fill=LP[k][2]+(a,))
    if GL: GL.ellipse([cx-r,cy-r,cx+r,cy+r],outline=VGOLD+(int(a*0.4),),width=14)
    wk=1+int(max(0,t-LP_WK)/0.35)%9 if t>=LP_WK else 1
    ctext(d,'WEEK',f(MONOB,20),cx,cy-36,MUTED,a); ctext(d,str(wk),f(BEB,72),cx,cy-14,VGOLD,a)
    for k,(lab,tt,col) in enumerate(LP):
        q=expo((t-tt)/0.18)
        if q<=0: continue
        y=420+k*90; d.text((350+30*(1-q),y),lab,font=f(BEB,80),fill=col+(int(a*q),))
        if GL: GL.text((350+30*(1-q),y),lab,font=f(BEB,80),fill=col+(int(a*q*0.5),))
    if t>=LP_WK: d.text((700,640),'WEEK-TO-WEEK',font=f(MONOB,28),fill=CREAM+(int(a*clamp((t-LP_WK)/0.2)),))

# 14) page vs person
PG_PAGE=at('page',113.7); PG_YOU=at('individual',115.7)
sfxb(PG_PAGE,'impact',g=-16); sfxb(PG_YOU,'thud',w=1.2,g=-18)
def page(L,d,t):
    if t<S_PAGE[0] or t>S_PAGE[1]+0.25: return
    a=int(255*scene_a(t,S_PAGE))
    kinetic(d,'THE PAGE',f(BEB,96),70,396,S_PAGE[0]+0.05,t,MUTED,-1)
    if t>=at('start',114.4): kinetic(d,'VS. YOUR RESPONSE',f(BEB,96),70,486,at('start',114.4),t,VGOLD,1)
    q=expo((t-S_PAGE[0]-0.1)/0.3); aa=int(a*q)
    d.rectangle([70,620,510,1300],fill=(236,234,230,aa))
    d.text((100,650),'REFERENCE RANGE',font=f(MONOB,24),fill=(60,60,66,aa))
    for k in range(5):
        y=720+k*110; d.text((100,y),['ESTRADIOL','TESTOSTERONE','FREE T','SHBG','HCT'][k],font=f(MONOB,20),fill=(60,60,66,aa)); d.rectangle([100,y+36,480,y+52],fill=(200,200,206,aa)); d.rectangle([200+k*20,y+36,360+k*12,y+52],fill=(150,150,156,aa))
    if t>=PG_PAGE:
        s=expo((t-PG_PAGE)/0.16); d.line([(60,1300),(lerp(60,520,s),lerp(1300,620,s))],fill=VRED+(a,),width=14)
        if GL: GL.line([(60,1300),(lerp(60,520,s),lerp(1300,620,s))],fill=VRED+(int(a*0.6),),width=26)
    if t>=PG_YOU-0.4:
        s=expo((t-PG_YOU+0.4)/0.3); aa2=int(a*s)
        gpanel(d,(570,620,1010,1300),VGOLD,aa2,0.85)
        person(d,790,880,150,VGOLD,aa2)
        if GL: person(GL,790,880,150,VGOLD,int(aa2*0.4))
        pts=[(600+k*4,1120-60*math.sin(k*0.35+t*4)*math.exp(-((k-50)/40)**2)) for k in range(101)]; nline(d,pts,ECYAN,4,aa2)
        ctext(d,'YOUR RESPONSE',f(BEB,56),790,1210,VGOLD,aa2)

def overlays_b(im,t):
    L,d=newL()
    versus(L,d,t); portal(L,d,t); cliff(L,d,t); arom(L,d,t); faders(L,d,t); strip(L,d,t); verdict(L,d,t)
    dash(L,d,t); form(L,d,t); iceberg(L,d,t); mistake(L,d,t); mold(L,d,t); loop(L,d,t); page(L,d,t)
    im.alpha_composite(L)

# 15) end card: the full framework, COMMENT "ESTROGEN"
T_END=S_PAGE[1]; E_FW=at('framework',118.5)
E_ROWS=[('MANAGE YOUR E2',at('manage',119.4)),('CROSS-REFERENCE YOUR BLOODWORK',at('cross',120.5)),('YOUR SIDE-EFFECT PROFILE',at('side',122.2)),('YOUR SYMPTOMS',at('symptoms',123.3)),('HOW YOU SHOULD FEEL DAILY',at('feel',124.4))]
E_C=at('comment',125.9); E_W=at('estrogen',126.3); E_SEND=at('send',127.8)
sfxb(T_END,'whoosh',d=0.25,g=-28); sfxb(E_FW,'thud',w=1.3,g=-17); sfxb(E_W,'impact',g=-15); sfxb(E_SEND,'tick',g=-26)
for _,tt in E_ROWS: sfxb(tt,'tick',g=-25)
def end_b(im,t):
    if t<T_END: return
    q=ease_io((t-T_END)/0.35); im.alpha_composite(scene_bg(q)); L,d=newL(); a=int(255*q)
    lg=logo().copy(); lg.putalpha(lg.split()[3].point(lambda v:int(v*q))); L.alpha_composite(lg.resize((130,130)),(70,250))
    d.text((222,262),'COACH AGZ',font=f(BAR,52),fill=GOLD+(a,)); d.text((224,326),'@coach.agz',font=f(MONO,28),fill=MUTED+(a,))
    if t>=E_FW-0.3:
        s=expo((t-E_FW+0.3)/0.2); aa=int(a*s)
        d.text((80,440),'THE FULL',font=f(BEB,72),fill=CREAM+(aa,)); d.text((80,510),'E2 FRAMEWORK',font=f(BEB,130),fill=VGOLD+(aa,))
        if GL: GL.text((80,510),'E2 FRAMEWORK',font=f(BEB,130),fill=VGOLD+(int(aa*0.5),))
    for k,(lab,tt) in enumerate(E_ROWS):
        if t<tt: continue
        r=expo((t-tt)/0.18); y=680+k*70; aa=int(a*r)
        d.polygon([(96,y+18),(108,y+6),(120,y+18),(108,y+30)],fill=VGOLD+(aa,))
        d.text((140+20*(1-r),y),lab,font=f(BAR,48),fill=CREAM+(aa,))
    if t>=E_C:
        s=expo((t-E_C)/0.16); sc=lerp(1.5,1,s); fn=f(MONOB,int(56*sc)); txt='COMMENT "ESTROGEN"'; w=d.textlength(txt,font=fn)
        lit_bar(d,540-w/2-30,1060,540+w/2+30,1060+fn.size+40,VGOLD,int(a*s)); d.text((540-w/2,1080),txt,font=fn,fill=DEEP+(int(a*s),))
        if GL and t<E_C+0.7: GL.rectangle([540-w/2-34,1056,540+w/2+34,1064+fn.size+40],outline=VGOLD+(int(220*(1-(t-E_C)/0.7)),),width=12)
    if t>=E_SEND: ctext(d,'SENT TO YOU',f(MONOB,34),540,1196,CREAM,int(a*clamp((t-E_SEND)/0.15)))
    ctext(d,DISC,f(MONO,20),540,1262,LABEL,a)
    ctext(d,'NOT MEDICAL ADVICE · WORK WITH YOUR DOCTOR',f(MONO,20),540,1292,LABEL,a)
    im.alpha_composite(L)

# ---------------- frame ----------------
SUBJECT_T=1.14      # visual hook: first punch-in lands on the spoken subject "estradiol"
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
