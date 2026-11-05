# Reel: "E2 Grinch" (emotional on cycle != high E2): full edit, native 1080x1920; comedic open kept clean, deep-vibrant overlay set from the educational turn
# Built on the saved setup: test-06 look + full-test-02 workflow (dead air trimmed, misspeak cut, 108% punch-in per jump cut,
# captions from the trimmed audio). Usage: python render.py <scratch> [--events|--groups|--still t..|--range n0 n1 out.mp4]
import json, subprocess, sys, math, re
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
S=sys.argv[1]; F=S+'/fonts/'; T=S+'/r13/work/'
W,H=1080,1920; FPS=30; N=3337; DUR=N/FPS
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
FIX={22:'MOTHERF*CKER',99:'F*CKING'}
for i,w in FIX.items(): words[i]['w']=w
for i,n_,s_ in ((275,2,'CROSS-REFERENCING'),(172,2,'3-POINT'),(6,3,'11-YEAR-OLD')): words[i]['w']=s_; words[i]['e']=words[i+n_-1]['e']; del words[i+1:i+n_]   # descending so indices hold
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
CUTS=[24.1167,26.9667,92.7667]   # no trims: the source's own jump cuts (scene detect) drive the punch-ins
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
HOOK_LINES=[[('Crying over the Grinch',CREAM)],[('blame your ',CREAM),('E2',VGOLD)]]
HOOK_END=6.00; HOOK_FADE=0.15; HOOK_Y=262
THO=(HOOK_END,HOOK_END+HOOK_FADE)
_mid=DUR/2; _nc=min(CUTS,key=lambda c:abs(c-_mid)); BAND_OUT=_nc if abs(_nc-_mid)<=1.5 else _mid      # nearest jump cut if within 1.5 s, else fade at the midpoint
BAND_IN=11.21      # band waits for the turn ("And naturally the first thing I think is..."): the comedic open stays clean
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
        for s,c in [('E2',VGOLD),(' is not your enemy',CREAM)]: d.text((x,y),s,font=fn,fill=c+(a,)); x+=d.textlength(s,font=fn)
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



# ======================= "E2 Grinch" overlay set (deep vibrant; comedic open stays clean) =======================
EVB=[]
def sfxb(t,kind,**k): EVB.append(dict(t=round(t,3),kind=kind,**k))
import re as _re2
def at(word,near):
    n=lambda s:_re2.sub(r'[^a-z0-9]','',s.lower()); best=None
    for w in words:
        if n(w['w']).startswith(n(word)) and abs(w['s']-near)<3.5 and (best is None or abs(w['s']-near)<abs(best-near)): best=w['s']
    if best is None: raise SystemExit('word not found: %s @%s'%(word,near))
    return best
# brand neon set (BRAND.md overlay accents): v-gold, v-red, cyan, green, amber; deep navy push
VIO=(255,194,26); MAG=(255,34,28); EBLU=(40,130,255); ECYAN=(0,229,255); CORAL=(255,150,20); ACID=(30,255,110); DEEPV=(2,3,8)
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
def gpanel(d,box,col,a,fill_a=0.55):     # deep glass panel with a coloured rim
    d.rounded_rectangle(box,radius=22,fill=DEEPV+(int(a*fill_a),)); nrect(d,box,col,int(a*0.8),3,22)
def pill(d,cx,y,txt,fn,bg,fg,a):
    w=d.textlength(txt,font=fn); h=fn.size+18; lit_bar(d,cx-w/2-18,y,cx+w/2+18,y+h,bg,a); d.text((cx-w/2,y+8),txt,font=fn,fill=fg+(a,))
def float_a(t,t0,t1): return expo((t-t0)/0.25)*(1-ease_io((t-t1)/0.2)) if t0<=t<=t1+0.2 else 0
def scene_a(t,win): return clamp((t-win[0])/0.2)*(1-ease_io((t-win[1])/0.22))
CUT_A,CUT_B,CUT_C=CUTS
S_MYTH=(at('and',11.26)-0.05, CUT_A-0.06)
S_HUB=(CUT_B+0.03, at('when',33.1)-0.05)
S_CURVE=(at('when',33.1)-0.05, at('because',37.0)-0.05)
S_TRI=(at('the',42.7)-0.05, at('number',45.9)-0.05)
S_BW=(at('number',45.9)-0.05, at('number',51.4)-0.05)
S_BIO=(at('number',51.4)-0.05, at('and',57.1)-0.05)
S_PERF=(at('and',57.1)-0.05, at('can',62.4)-0.05)
S_VENN=(at('you',71.1)-0.05, at("don't",76.1)-0.05)
S_LAB=(at("don't",76.1)-0.05, at('optimization',82.9)-0.05)
S_PRINT=(at('optimization',82.9)-0.05, CUT_C-0.06)
SCENES=[S_MYTH,S_HUB,S_CURVE,S_TRI,S_BW,S_BIO,S_PERF,S_VENN,S_LAB,S_PRINT]
def B_push(t):
    g=0
    for a_,b_ in SCENES: g=max(g,clamp((t-a_)/0.22)*clamp((b_-t)/0.22))
    return ease_io(g)
for i,(a_,b_) in enumerate(SCENES):
    if i==0 or abs(a_-SCENES[i-1][1])>0.3: sfxb(a_,'whoosh',d=0.22,g=-28); sfxb(a_+0.2,'thud',w=1.2,g=-18)
    else: sfxb(a_,'scan',d=0.35,g=-29)

# 1) the backwards logic: two cause->effect chains that snap
MY_TOT=at('totally',17.2); MY_N1=at('necessarily',19.2); MY_N2=at('automatically',21.9); MY_AI=at('ai',23.6)
sfxb(MY_N1,'impact',g=-16); sfxb(MY_N2,'impact',g=-16)
def chain(d,y,la,lb,ca,cb,t_on,t_snap,t,a):
    q=expo((t-t_on)/0.25)
    if q<=0: return
    aa=int(a*q); fn=f(BEB,74)
    for x0,lab,col in ((60,la,ca),(620,lb,cb)):
        gpanel(d,(x0,y,x0+400,y+150),col,aa); ctext(d,lab,fn if d.textlength(lab,font=fn)<370 else f(BEB,60),x0+200,y+38,col,aa,True)
    snap=expo((t-t_snap)/0.18) if t>=t_snap else 0
    cy=y+75
    for k in range(3):          # chain links between the two boxes
        cx=490+k*50; dx=(-1 if k==0 else (1 if k==2 else 0))*snap*24; dy=(k==1)*snap*60
        col=CREAM if snap==0 else (MUTED if k!=1 else CORAL)
        d.ellipse([cx-30+dx,cy-18+dy,cx+30+dx,cy+18+dy],outline=col+(int(aa*(1-0.6*snap*(k==1))),),width=7)
    if snap>0:
        if GL and t<t_snap+0.5: GL.ellipse([520,cy-60,580,cy+60],outline=CORAL+(int(220*(1-(t-t_snap)/0.5)),),width=14)
        ctext(d,'NOT A GIVEN',f(MONOB,28),540,y+170,CORAL,int(aa*snap))
def myth(L,d,t):
    if t<S_MYTH[0] or t>S_MYTH[1]+0.25: return
    a=int(255*scene_a(t,S_MYTH))
    if t<MY_TOT: kinetic(d,'THE FIRST THOUGHT',f(BEB,100),70,420,S_MYTH[0]+0.1,t,CREAM,-1)
    else: kinetic(d,'THE BACKWARDS LOGIC',f(BEB,100),70,420,MY_TOT,t,MAG,1)
    chain(d,620,'EMOTIONAL','HIGH E2',VIO,MAG,at('what',12.8),MY_N1,t,a)
    chain(d,920,'HIGH E2','NEED AN AI',MAG,EBLU,at('high',21.3)-0.1,MY_N2,t,a)
    if t>=MY_AI: ctext(d,'ASSUMPTION ≠ DIAGNOSIS'.replace('≠','IS NOT A'),f(BEB,64),540,1230,CREAM,int(a*clamp((t-MY_AI)/0.2)))

# 2) radial hub: what estradiol does
HUB=[('SEXUAL FUNCTION',at('sexual',29.5),MAG,ic_flame),('BRAIN SIGNALING',at('brain',30.4),ECYAN,ic_pulse),('BONE HEALTH',at('bone',31.3),ACID,ic_shield),('MUSCLE GROWTH',at('muscle',32.1),CORAL,ic_muscle)]
H_ROLE=at('roles',28.9)
sfxb(H_ROLE,'thud',w=1.0,g=-20)
for _,tt,_c,_i in HUB: sfxb(tt,'tick',g=-24)
def hexagon(d,cx,cy,r,col,a,w=6):
    pts=[(cx+r*math.cos(math.radians(60*k+30)),cy+r*math.sin(math.radians(60*k+30))) for k in range(7)]
    d.polygon(pts[:6],fill=DEEPV+(int(a*0.8),)); nline(d,pts,col,w,a)
def hub(L,d,t):
    if t<S_HUB[0] or t>S_HUB[1]+0.25: return
    a=int(255*scene_a(t,S_HUB)); cx,cy=540,950
    kinetic(d,'WHAT E2 ACTUALLY RUNS',f(BEB,88),70,410,S_HUB[0]+0.1,t,VIO,-1)
    spots=[(250,720),(830,720),(250,1170),(830,1170)]
    rot=(t-S_HUB[0])*0.6
    for r_ in (170,230):
        for k in range(36):
            ang=k*10+rot*(1 if r_==170 else -1)*20
            if k%3==0: x=cx+r_*math.cos(math.radians(ang)); y=cy+r_*math.sin(math.radians(ang)); d.ellipse([x-3,y-3,x+3,y+3],fill=VIO+(int(a*0.6),))
    for (lab,tt,col,ic),(sx,sy) in zip(HUB,spots):
        q=expo((t-tt)/0.22)
        if q<=0: continue
        aa=int(a*q); ex=lerp(cx,sx,q); ey=lerp(cy,sy,q)
        nline(d,[(cx,cy),(ex,ey)],col,4,int(aa*0.8))
        d.ellipse([ex-78,ey-78,ex+78,ey+78],fill=DEEPV+(int(aa*0.85),)); d.ellipse([ex-78,ey-78,ex+78,ey+78],outline=col+(aa,),width=5)
        if GL: GL.ellipse([ex-78,ey-78,ex+78,ey+78],outline=col+(int(aa*0.8),),width=14)
        ic(d,ex,ey,42,col,aa)
        ty=ey+96 if sy>cy else ey-140
        ctext(d,lab,f(BEB,50),ex,ty,col,aa)
    pulse=1+0.04*math.sin(t*6); hexagon(d,cx,cy,120*pulse,VGOLD,a,7)
    ctext(d,'E2',f(BEB,120),cx,cy-70,VGOLD,a,True)
    if t>=H_ROLE: ctext(d,'ESTRADIOL',f(MONOB,22),cx,cy+48,CREAM,int(a*clamp((t-H_ROLE)/0.2)))

# 3) U-curve: crush it too low
CU_CR=at('crush',33.3); CU_LOW=at('low',33.9); CU_PR=at('problems',35.6)
sfxb(CU_CR,'scan',d=0.6,g=-29); sfxb(CU_PR,'impact',g=-16)
def ucurve(L,d,t):
    if t<S_CURVE[0] or t>S_CURVE[1]+0.25: return
    a=int(255*scene_a(t,S_CURVE))
    kinetic(d,'E2 HAS A SWEET SPOT',f(BEB,92),70,410,S_CURVE[0]+0.08,t,ECYAN,-1)
    x0,x1,yb,yt=110,980,1180,620
    Y=lambda u: yb-(yb-yt)*((u-0.55)/0.55)**2*1.0 if u<0.55 else yb-(yb-yt)*((u-0.55)/0.45)**2
    d.line([(x0,yb+30),(x1,yb+30)],fill=MUTED+(a,),width=3); d.line([(x0,yt-20),(x0,yb+30)],fill=MUTED+(a,),width=3)
    d.text((x1-210,yb+44),'E2 LEVEL →',font=f(MONOB,24),fill=LABEL+(a,))
    d.text((x0+12,yt-62),'PROBLEMS ↑',font=f(MONOB,24),fill=LABEL+(a,))
    q=ease_io((t-S_CURVE[0]-0.15)/0.6); n=int(140*q)
    pts=[(lerp(x0,x1,k/140),Y(k/140)) for k in range(n+1)]
    # optimal band
    d.rectangle([lerp(x0,x1,0.42),yt,lerp(x0,x1,0.68),yb+28],fill=ACID+(int(a*0.10),))
    ctext(d,'OPTIMAL',f(MONOB,26),lerp(x0,x1,0.55),yb-60,ACID,a)
    if t>=CU_PR:
        s=ease_io((t-CU_PR)/0.3); d.rectangle([x0+4,yt,lerp(x0,x1,0.2),yb+28],fill=CORAL+(int(a*0.22*s),))
        ctext(d,'TOO LOW',f(BEB,64),lerp(x0,x1,0.12)+20,yb-80,CORAL,int(a*s),True)
    nline(d,pts,ECYAN,6,a)
    u=0.55
    if t>=CU_CR: u=lerp(0.55,0.08,ease_io((t-CU_CR)/0.9))
    if q>=1:
        px,py=lerp(x0,x1,u),Y(u); d.ellipse([px-18,py-18,px+18,py+18],fill=VGOLD+(a,))
        if GL: GL.ellipse([px-26,py-26,px+26,py+26],fill=VGOLD+(int(a*0.6),))
        ctext(d,'YOU',f(MONOB,24),px,py-52,VGOLD,a)
    if t>=CU_PR: pill(d,540,1290,'NEW SET OF PROBLEMS',f(MONOB,36),CORAL,(255,255,255),int(a*clamp((t-CU_PR)/0.2)))

# 4) floating top card: decade + 500+ panels odometer
PN0=S_CURVE[1]; PN1=S_TRI[0]-0.05; PN_DEC=at('decade',38.6); PN_500=at('500',39.6); PN_YRS=at('years',40.9)
sfxb(PN_DEC,'tick',g=-25); sfxb(PN_500,'scan',d=0.7,g=-30); sfxb(PN_500+0.75,'thud',w=1.0,g=-19)
def panels500(L,d,t):
    a=int(255*float_a(t,PN0,PN1))
    if a<=0: return
    gpanel(d,(40,392,1040,700),VIO,a,0.85)
    for k in range(5):      # fanned lab sheets
        q=expo((t-PN_500-k*0.06)/0.25) if t>=PN_500 else 0
        ang=lerp(0,-14+k*7,q); x=150+k*8; y=560-k*6
        sh=Image.new('RGBA',(150,190),(0,0,0,0)); sd=ImageDraw.Draw(sh)
        sd.rectangle([0,0,149,189],fill=(238,236,232,int(a*0.95)),outline=VIO+(a,),width=3)
        for r in range(6): sd.line([(14,22+r*26),(136-(r%3)*24,22+r*26)],fill=(120,122,130,a),width=5)
        sh=sh.rotate(ang,expand=True,resample=Image.BICUBIC); L.alpha_composite(sh,(int(x-sh.width/2+60),int(y-sh.height/2+0)))
    if t>=PN_DEC: d.text((330,420),'10+ YEARS',font=f(BEB,84),fill=ECYAN+(int(a*clamp((t-PN_DEC)/0.2)),))
    if t>=PN_500:
        v=int(500*ease_io((t-PN_500)/0.75)); s=f'{v}' + ('+' if v>=500 else '')
        d.text((330,500),s,font=f(BEB,150),fill=VGOLD+(a,))
        if GL: GL.text((330,500),s,font=f(BEB,150),fill=VGOLD+(int(a*0.6),))
        d.text((330+d.textlength('500+',font=f(BEB,150))+24,560),'PANELS',font=f(BEB,72),fill=CREAM+(a,))
    if t>=PN_YRS: d.text((334,654),'IN THE LAST COUPLE OF YEARS',font=f(MONOB,24),fill=MUTED+(int(a*clamp((t-PN_YRS)/0.2)),))

# 5) framework triangle + mini-map; three pillar scenes
TRI_PTS=lambda cx,cy,r:[(cx,cy-r),(cx+r*0.866,cy+r*0.5),(cx-r*0.866,cy+r*0.5)]
PILLARS=[('BLOODWORK',MAG),('BIOFEEDBACK',ECYAN),('PERFORMANCE',ACID)]
TR_FREE=at('free',45.5); TR_3=at('3-point',42.9)
sfxb(TR_FREE,'impact',g=-15)
def tri_graph(d,cx,cy,r,a,active=None,labels=True,t=0,t0=0):
    pts=TRI_PTS(cx,cy,r)
    q=ease_io((t-t0)/0.5) if t0 else 1
    for k in range(3):
        p0,p1=pts[k],pts[(k+1)%3]; e=(lerp(p0[0],p1[0],q),lerp(p0[1],p1[1],q))
        nline(d,[p0,e],VIO,5 if r>150 else 3,int(a*0.8))
    for k,(p,(lab,col)) in enumerate(zip(pts,PILLARS)):
        on=active is None or active==k; aa=int(a*(1 if on else 0.35)); rr=r*0.26
        d.ellipse([p[0]-rr,p[1]-rr,p[0]+rr,p[1]+rr],fill=DEEPV+(a,),outline=col+(aa,),width=6 if r>150 else 4)
        if GL and on: GL.ellipse([p[0]-rr,p[1]-rr,p[0]+rr,p[1]+rr],outline=col+(int(aa*0.8),),width=16 if r>150 else 8)
        ctext(d,str(k+1),f(BEB,int(rr*1.3)),p[0],p[1]-rr*0.7,col,aa)
        if labels: ctext(d,lab,f(BEB,56),p[0],p[1]+(rr+12 if k else -rr-70),col,aa)
def tri_scene(L,d,t):
    if t<S_TRI[0] or t>S_TRI[1]+0.25: return
    a=int(255*scene_a(t,S_TRI))
    kinetic(d,'3-POINT HORMONE',f(BEB,104),70,400,S_TRI[0]+0.05,t,CREAM,-1)
    kinetic(d,'INTELLIGENT FRAMEWORK',f(BEB,80),70,508,S_TRI[0]+0.2,t,VIO,-1)
    tri_graph(d,540,1010,240,a,None,True,t,S_TRI[0]+0.3)
    if t>=TR_FREE:
        s=expo((t-TR_FREE)/0.14); sc=lerp(1.6,1,s); fn=f(BEB,int(90*sc)); w=d.textlength('FREE',font=fn)
        lit_bar(d,540-w/2-30,1296,540+w/2+30,1296+fn.size+20,VGOLD,int(a*s)); d.text((540-w/2,1308),'FREE',font=fn,fill=DEEP+(int(a*s),))
def mini(d,k,a):
    tri_graph(d,930,470,70,a,k,False)
def head(d,k,t,t0,a):
    lab,col=PILLARS[k]; kinetic(d,f'0{k+1}',f(BEB,90),70,400,t0+0.05,t,col,-1); kinetic(d,lab,f(BEB,110),190,392,t0+0.12,t,CREAM,-1)
    mini(d,k,a)
# 5a) bloodwork: lab rows with level bars + ratio brackets
BW=[('SENSITIVE E2',at('sensitive',47.3),MAG),('TOTAL T',at('total',48.2),VGOLD),('FREE T',at('free',48.8),CORAL),('SHBG',at('shbg',49.5),EBLU)]
BW_RAT=at('ratios',50.7)
for _,tt,_c in BW: sfxb(tt,'tick',g=-24)
sfxb(BW_RAT,'thud',w=1.0,g=-19)
def bloodwork(L,d,t):
    if t<S_BW[0] or t>S_BW[1]+0.25: return
    a=int(255*scene_a(t,S_BW)); head(d,0,t,S_BW[0],a)
    gpanel(d,(60,600,1020,1250),MAG,a,0.7)
    d.text((100,628),'LAB PANEL',font=f(MONOB,24),fill=LABEL+(a,)); d.text((760,628),'LEVEL',font=f(MONOB,24),fill=LABEL+(a,))
    lv=[0.62,0.55,0.48,0.58]
    for k,(lab,tt,col) in enumerate(BW):
        q=expo((t-tt)/0.2)
        if q<=0: continue
        y=690+k*130; aa=int(a*q)
        d.text((100,y),lab,font=f(BEB,64),fill=col+(aa,))
        d.rounded_rectangle([520,y+18,900,y+50],radius=16,outline=col+(int(aa*0.6),),width=3)
        e=520+380*lv[k]*ease_io((t-tt)/0.5); d.rounded_rectangle([524,y+22,max(530,e),y+46],radius=12,fill=col+(aa,))
        if GL: GL.rounded_rectangle([524,y+22,max(530,e),y+46],radius=12,fill=col+(int(aa*0.5),))
    if t>=BW_RAT:
        s=ease_io((t-BW_RAT)/0.4); aa=int(a*s)
        for k0,k1,off in ((0,1,0),(1,3,40)):
            y0=690+k0*130+34; y1=690+k1*130+34; x=930+off
            nline(d,[(905,y0),(x,y0),(x,lerp(y0,y1,s)),(905 if s>=1 else x,lerp(y0,y1,s))],VGOLD,4,aa)
        pill(d,540,1270,'READ THE RATIOS',f(MONOB,36),VGOLD,DEEP,aa)
# 5b) biofeedback: radar chart
RD=[('LIBIDO',at('libido',53.1),MAG,0.78),('MOOD',at('mood',53.8),ECYAN,0.66),('SLEEP',at('sleep',54.2),VIO,0.72),('SIDE EFFECTS',at('side',54.8),CORAL,0.5)]
RD_RESP=at('response',56.4)
for _,tt,_c,_v in RD: sfxb(tt,'tick',g=-24)
sfxb(RD_RESP,'thud',w=1.0,g=-19)
def radar(L,d,t):
    if t<S_BIO[0] or t>S_BIO[1]+0.25: return
    a=int(255*scene_a(t,S_BIO)); head(d,1,t,S_BIO[0],a)
    cx,cy,R=540,900,270
    angs=[-90,0,90,180]
    for ring in (0.25,0.5,0.75,1.0):
        pts=[(cx+R*ring*math.cos(math.radians(g)),cy+R*ring*math.sin(math.radians(g))) for g in angs]; d.polygon(pts,outline=(70,74,86,a))
    for g in angs: d.line([(cx,cy),(cx+R*math.cos(math.radians(g)),cy+R*math.sin(math.radians(g)))],fill=(70,74,86,a),width=2)
    vals=[]
    for (lab,tt,col,v),g in zip(RD,angs):
        q=ease_io((t-tt)/0.45) if t>=tt else 0; vals.append(v*q)
        lx=cx+(R+40)*math.cos(math.radians(g)); ly=cy+(R+40)*math.sin(math.radians(g))
        aa=int(a*(0.35+0.65*clamp((t-tt)/0.2)))
        fn=f(BEB,58); w=d.textlength(lab,font=fn)
        tx=lx-w/2 if g in (-90,90) else (lx-w if g==180 else lx); tx=min(max(tx,50),1030-w); ty=ly-(70 if g==-90 else (0 if g==90 else 30))
        if g==180: tx=max(50,cx-R-w+40); ty=ly-110
        if g==0: tx=min(1030-w,cx+R-w+40); ty=ly-110
        d.text((tx,ty),lab,font=fn,fill=col+(aa,))
    pts=[(cx+R*v*math.cos(math.radians(g)),cy+R*v*math.sin(math.radians(g))) for v,g in zip(vals,angs)]
    if max(vals)>0:
        sh=Image.new('RGBA',(W,H),(0,0,0,0)); ImageDraw.Draw(sh).polygon(pts,fill=ECYAN+(int(a*0.28),)); L.alpha_composite(sh)
        nline(d,pts+[pts[0]],ECYAN,5,a)
        for (lab,tt,col,v),p in zip(RD,pts):
            if t>=tt: d.ellipse([p[0]-12,p[1]-12,p[0]+12,p[1]+12],fill=col+(a,))
    if t>=RD_RESP: pill(d,540,1320,'HOW YOU RESPOND',f(MONOB,36),ECYAN,DEEP,int(a*clamp((t-RD_RESP)/0.2)))
# 5c) performance: three lines across the whole day
PF=[('STRENGTH',at('strength',58.9),CORAL,0.70),('RECOVERY',at('recovery',59.5),ACID,0.60),('MENTAL CLARITY',at('mental',60.2),ECYAN,0.82)]
PF_DAY=at('entire',61.4)
for _,tt,_c,_v in PF: sfxb(tt,'tick',g=-24)
sfxb(PF_DAY,'scan',d=0.6,g=-30)
def perf(L,d,t):
    if t<S_PERF[0] or t>S_PERF[1]+0.25: return
    a=int(255*scene_a(t,S_PERF)); head(d,2,t,S_PERF[0],a)
    x0,x1,yb,yt=110,990,1180,690
    gpanel(d,(60,590,1020,1260),ACID,a,0.55)
    for k,h in enumerate(('6AM','12PM','6PM','10PM')):
        x=lerp(x0,x1,k/3); d.line([(x,yt),(x,yb)],fill=(48,52,62,a),width=1); ctext(d,h,f(MONO,22),x,yb+20,LABEL,a)
    for k,(lab,tt,col,lv) in enumerate(PF):
        if t<tt: continue
        span=ease_io((t-tt)/0.6) if t<PF_DAY else 1.0
        if t<PF_DAY: span=min(span,0.45)
        else: span=lerp(0.45,1.0,ease_io((t-PF_DAY)/0.8))
        n=int(80*span); pts=[]
        for i in range(n+1):
            u=i/80; base=lv+0.05*math.sin(u*6+k*2)-(0.02 if k==2 else 0.08)*u
            pts.append((lerp(x0,x1,u),yb-(yb-yt)*base))
        nline(d,pts,col,6,a)
        lx=100+k*300; d.rounded_rectangle([lx,616,lx+28,632],radius=6,fill=col+(a,)); d.text((lx+40,604),lab,font=f(BEB,40),fill=col+(a,))
    if t>=PF_DAY: pill(d,540,1290,'ALL DAY LONG',f(MONOB,36),ACID,DEEP,int(a*clamp((t-PF_DAY)/0.2)))

# 6) floating top card: life tiles (business decisions, family time)
LF0=S_PERF[1]; LF1=at('utilizing',66.7)-0.1
LIFE=[('BUSINESS','DECISIONS',at('business',63.1),EBLU),('TIME WITH','FAMILY',at('family',66.0)-0.6,MAG)]
for *_,tt,_c in LIFE: sfxb(tt,'tick',g=-25)
def brief(d,cx,cy,col,a):
    d.rounded_rectangle([cx-44,cy-24,cx+44,cy+34],radius=8,outline=col+(a,),width=5); d.rectangle([cx-16,cy-40,cx+16,cy-24],outline=col+(a,),width=5); d.line([(cx-44,cy),(cx+44,cy)],fill=col+(a,),width=4)
def house(d,cx,cy,col,a):
    d.polygon([(cx-50,cy-4),(cx,cy-46),(cx+50,cy-4)],outline=col+(a,)); d.line([(cx-50,cy-4),(cx,cy-46),(cx+50,cy-4)],fill=col+(a,),width=5)
    d.rectangle([cx-36,cy-4,cx+36,cy+40],outline=col+(a,),width=5); d.rectangle([cx-10,cy+12,cx+10,cy+40],fill=col+(a,))
def life(L,d,t):
    a=int(255*float_a(t,LF0,LF1))
    if a<=0: return
    for k,(l1,l2,tt,col) in enumerate(LIFE):
        q=expo((t-tt)/0.2)
        if q<=0: continue
        x0=40+k*510; aa=int(a*q); dy=30*(1-q)
        gpanel(d,(x0,400+dy,x0+490,640+dy),col,aa,0.86)
        (brief if k==0 else house)(d,x0+90,520+dy,col,aa)
        d.text((x0+170,440+dy),l1,font=f(BEB,60),fill=CREAM+(aa,)); d.text((x0+170,510+dy),l2,font=f(BEB,76),fill=col+(aa,))
        if GL: GL.text((x0+170,510+dy),l2,font=f(BEB,76),fill=col+(int(aa*0.6),))

# 7) Venn: cross-reference all three + other markers
VN_CR=at('cross',71.9); VN_PAT=at('patterns',72.6); VN_ALL=at('three',73.6); VN_OTH=at('alongside',73.9)
sfxb(VN_CR,'scan',d=0.6,g=-30); sfxb(VN_PAT,'thud',w=1.2,g=-18); sfxb(VN_OTH,'tick',g=-25)
def venn(L,d,t):
    if t<S_VENN[0] or t>S_VENN[1]+0.25: return
    a=int(255*scene_a(t,S_VENN))
    kinetic(d,'CROSS-REFERENCE',f(BEB,110),70,400,S_VENN[0]+0.08,t,CREAM,-1)
    cx,cy=540,930; r=210; q=ease_io((t-S_VENN[0]-0.2)/0.6)
    cen=[(cx,cy-130*q),(cx+120*q,cy+80*q),(cx-120*q,cy+80*q)]
    sh=Image.new('RGBA',(W,H),(0,0,0,0)); sd=ImageDraw.Draw(sh)
    for (x,y),(lab,col) in zip(cen,PILLARS): sd.ellipse([x-r,y-r,x+r,y+r],fill=col+(int(a*0.16),))
    L.alpha_composite(sh)
    for (x,y),(lab,col) in zip(cen,PILLARS):
        d.ellipse([x-r,y-r,x+r,y+r],outline=col+(a,),width=5)
        if GL: GL.ellipse([x-r,y-r,x+r,y+r],outline=col+(int(a*0.7),),width=12)
    if q>=1:
        for (x,y),(lab,col),(ox,oy) in zip(cen,PILLARS,((0,-120),(70,70),(-70,70))): ctext(d,lab,f(BEB,44),x+ox,y+oy-20,col,a)
    if t>=VN_PAT:
        s=expo((t-VN_PAT)/0.2); rr=46+6*math.sin(t*7)
        d.ellipse([cx-rr,cy+10-rr,cx+rr,cy+10+rr],fill=VGOLD+(int(a*s),))
        if GL: GL.ellipse([cx-rr-10,cy+10-rr-10,cx+rr+10,cy+10+rr+10],fill=VGOLD+(int(a*s*0.7),))
        ctext(d,'PATTERN',f(MONOB,22),cx,cy-4,DEEP,int(a*s))
    if t>=VN_OTH:
        s=clamp((t-VN_OTH)/0.4); R=420
        for k in range(14):
            ang=k*360/14+(t-VN_OTH)*25; x=cx+R*math.cos(math.radians(ang)); y=cy+20+R*0.86*math.sin(math.radians(ang))
            if y<1300: d.ellipse([x-9,y-9,x+9,y+9],fill=EBLU+(int(a*s),))
        pill(d,540,1300,'+ ALL OTHER HEALTH MARKERS',f(MONOB,32),EBLU,(255,255,255),int(a*s))

# 8) lab report scan: one number, red alert, average-guy range
LB_ONE=at('one',77.2); LB_NUM=at('number',78.6); LB_RED=at('red',80.7); LB_AVG=at('average',81.9)
sfxb(LB_ONE,'tick',g=-25); sfxb(LB_NUM,'tick',g=-25); sfxb(LB_RED,'impact',g=-15); sfxb(LB_AVG,'tick',g=-24)
def labscan(L,d,t):
    if t<S_LAB[0] or t>S_LAB[1]+0.25: return
    a=int(255*scene_a(t,S_LAB))
    q=expo((t-S_LAB[0]-0.1)/0.3); x0,y0,x1,y1=90,440+40*(1-q),990,1180+40*(1-q); aa=int(a*q)
    d.rectangle([x0,y0,x1,y1],fill=(236,234,230,aa))
    d.text((x0+40,y0+30),'LABORATORY REPORT',font=f(MONOB,34),fill=(36,36,40,aa))
    d.line([(x0+40,y0+86),(x1-40,y0+86)],fill=(150,150,156,aa),width=2)
    for k,(c,xx) in enumerate((('TEST',x0+40),('RESULT',x0+470),('FLAG',x0+650),('RANGE',x0+760))): d.text((xx,y0+104),c,font=f(MONOB,22),fill=(110,110,118,aa))
    rows=['TESTOSTERONE, TOTAL','TESTOSTERONE, FREE','ESTRADIOL, SENSITIVE','SHBG']
    for k,r in enumerate(rows):
        y=y0+160+k*92; hot=k==2
        d.text((x0+40,y),r,font=f(MONOB,26),fill=(28,28,32,aa))
        d.rectangle([x0+470,y+4,x0+590,y+30],fill=(150,150,156,int(aa*0.5)))        # values are blurred out on purpose: no lab values shown
        d.rectangle([x0+760,y+4,x0+860,y+30],fill=(150,150,156,int(aa*0.35)))
        if hot and t>=LB_RED:
            s=expo((t-LB_RED)/0.14); d.text((x0+660,y-4),'H',font=f(MONOB,34),fill=(220,20,40,int(aa*s)))
    yr=y0+160+2*92
    if t>=LB_ONE:   # single-moment snapshot brackets around the one row
        s=ease_io((t-LB_ONE)/0.3); brackets(d,x0+20,yr-18,x1-20,yr+54,VIO+(aa,),30,6,s)
        if GL: GL.rectangle([x0+20,yr-18,x1-20,yr+54],outline=VIO+(int(aa*0.5),),width=10)
        ctext(d,'ONE MOMENT · ONE NUMBER' if t>=LB_NUM else 'ONE MOMENT',f(MONOB,26),540,yr-54,VIO,aa)
    if t>=LB_RED:
        s=expo((t-LB_RED)/0.16); sc=lerp(1.6,1,s)
        st=Image.new('RGBA',(560,150),(0,0,0,0)); sd=ImageDraw.Draw(st)
        sd.rectangle([6,6,553,143],outline=(230,20,50,int(aa*s)),width=10); fn=f(BEB,110); sd.text((280-sd.textlength('RED ALERT',font=fn)/2,16),'RED ALERT',font=fn,fill=(230,20,50,int(aa*s)))
        st=st.rotate(-8,expand=True,resample=Image.BICUBIC); st=st.resize((int(st.width*sc),int(st.height*sc)),Image.BICUBIC)
        L.alpha_composite(st,(int(540-st.width/2),int(y1-175-st.height/2)))
    if t>=LB_AVG:
        s=clamp((t-LB_AVG)/0.2); d.text((x0+40,y1-60),'* RANGE BUILT ON THE AVERAGE GUY',font=f(MONOB,26),fill=(200,30,60,int(aa*s)))
    if t>=at('guy',82.3)-0.05: pill(d,540,1230,'NOT A DIAGNOSIS',f(MONOB,40),MAG,(255,255,255),int(a*clamp((t-at('guy',82.3))/0.2)))

# 9) fingerprint scan: your biology, your ratios, nobody's the same
FP=[('YOUR BIOLOGY',at('biology',84.5),VIO),('WHEN TO PIVOT',at('pivot',86.1),CORAL),('WHEN TO OPTIMIZE',at('optimize',87.0),ACID),('YOUR RATIOS',at('ratios',88.5),VGOLD)]
FP_NB=at('nobody',90.8); FP_SAME=at('same',92.3)
for _,tt,_c in FP: sfxb(tt,'tick',g=-24)
sfxb(FP_NB,'scan',d=0.5,g=-30); sfxb(FP_SAME,'thud',w=1.1,g=-18)
def fprint(d,cx,cy,s,col,a,seed=0,prog=1.0,w=4):
    rng=np.random.default_rng(seed)
    for k in range(int(11*prog)):
        rx=s*(0.18+k*0.075); ry=rx*1.28; st=20+rng.integers(0,60); en=st+260+rng.integers(-40,40)
        d.arc([cx-rx,cy-ry,cx+rx,cy+ry],start=int(st),end=int(en),fill=col+(a,),width=w)
def fingerprint(L,d,t):
    if t<S_PRINT[0] or t>S_PRINT[1]+0.25: return
    a=int(255*scene_a(t,S_PRINT))
    kinetic(d,'OPTIMIZATION IS PERSONAL',f(BEB,88),70,400,S_PRINT[0]+0.08,t,ECYAN,-1)
    many=ease_io((t-FP_NB)/0.5) if t>=FP_NB else 0
    cx,cy=540,900
    if many<1:
        aa=int(a*(1-many)); prog=ease_io((t-S_PRINT[0]-0.15)/1.0)
        fprint(d,cx,cy,300,ECYAN,aa,3,prog,5)
        if GL: fprint(GL,cx,cy,300,ECYAN,int(aa*0.6),3,prog,10)
        sy=cy-260+((t-S_PRINT[0])*300)%520; d.line([(cx-260,sy),(cx+260,sy)],fill=MAG+(int(aa*0.9),),width=4)
        if GL: GL.line([(cx-260,sy),(cx+260,sy)],fill=MAG+(int(aa*0.8),),width=12)
        spots=[(90,600),(640,600),(90,1170),(640,1170)]
        for (lab,tt,col),(x,y) in zip(FP,spots):
            q=expo((t-tt)/0.2)
            if q<=0: continue
            fn=f(BEB,54); w_=d.textlength(lab,font=fn)
            gpanel(d,(x,y,x+w_+40,y+80),col,int(aa*q),0.85); d.text((x+20,y+10),lab,font=fn,fill=col+(int(aa*q),))
    if many>0:
        aa=int(a*many)
        for k in range(9):
            gx=230+(k%3)*310; gy=640+(k//3)*250; me=k==4
            fprint(d,gx,gy,100,(VGOLD if me else MUTED),int(aa*(1 if me else 0.55)),k+7,1.0,3)
            if me and GL: fprint(GL,gx,gy,100,VGOLD,int(aa*0.7),k+7,1.0,8)
        ctext(d,'YOU',f(MONOB,26),540,770,VGOLD,aa)
        if t>=FP_SAME: pill(d,540,1270,'NO TWO ALIKE',f(MONOB,40),VGOLD,DEEP,int(a*clamp((t-FP_SAME)/0.2)))

def overlays_b(im,t):
    L,d=newL()
    myth(L,d,t); hub(L,d,t); ucurve(L,d,t); panels500(L,d,t); tri_scene(L,d,t); bloodwork(L,d,t); radar(L,d,t); perf(L,d,t)
    life(L,d,t); venn(L,d,t); labscan(L,d,t); fingerprint(L,d,t)
    im.alpha_composite(L)

# 10) end card: deep blueprint, COMMENT "E2", free estrogen optimization blueprint
T_END=CUT_C; E_PAN=at('panicking',95.7); E_RED=at('red',97.6); E_C=at('comment',98.6); E_E2=at('e2',99.0); E_BP=at('blueprint',102.1)
E_ROWS=[('BLOOD MARKERS',at('blood',103.8)),('SYMPTOMS',at('symptoms',104.7)),('PHYSIOLOGICAL FACTORS',at('physiological',105.5))]
E_AI=at('before',107.6)
sfxb(T_END,'whoosh',d=0.25,g=-28); sfxb(E_RED,'tick',g=-23); sfxb(E_E2,'impact',g=-15); sfxb(E_BP,'thud',w=1.4,g=-17)
for _,tt in E_ROWS: sfxb(tt,'tick',g=-25)
sfxb(E_AI,'tick',g=-24)
_BP=None
def bp_bg(a):
    global _BP
    if _BP is None:
        yy,xx=np.mgrid[0:H,0:W]
        r=np.sqrt(((xx-540)/(W*0.8))**2+((yy-760)/(H*0.55))**2)
        bg=np.zeros((H,W,3),np.float32)+np.array(DEEPV,np.float32)
        bg+=np.array(NAVY,np.float32)-np.array(DEEPV,np.float32)
        bg+=(np.clip(1-r,0,1)**2)[...,None]*np.array([34,24,6],np.float32)
        grid=((xx%60)<2)|((yy%60)<2); bg[grid]+=np.array([10,14,22],np.float32)
        bg+=np.random.default_rng(5).standard_normal((H,W,1)).astype(np.float32)*1.4
        _BP=Image.fromarray(np.clip(bg,0,255).astype(np.uint8)).convert('RGBA')
    l=_BP.copy(); l.putalpha(int(255*a*0.95)); return l
def end_b(im,t):
    if t<T_END: return
    q=ease_io((t-T_END)/0.35); im.alpha_composite(bp_bg(q)); L,d=newL(); a=int(255*q)
    lg=logo().copy(); lg.putalpha(lg.split()[3].point(lambda v:int(v*q))); L.alpha_composite(lg.resize((130,130)),(70,250))
    d.text((222,262),'COACH AGZ',font=f(BAR,52),fill=GOLD+(a,)); d.text((224,326),'@coach.agz',font=f(MONO,28),fill=MUTED+(a,))
    if t>=E_PAN:      # the panic: an E2 result flagged red
        s=expo((t-E_PAN)/0.2); sh=6*math.sin(t*40)*max(0,1-(t-E_RED)/0.5) if t>=E_RED else 0
        gpanel(d,(170+sh,430,910+sh,540),CORAL if t>=E_RED else MUTED,int(a*s),0.9)
        d.text((210+sh,452),'ESTRADIOL, SENSITIVE',font=f(MONOB,32),fill=CREAM+(int(a*s),))
        if t>=E_RED:
            pill(d,800+sh,452,'RED ALERT',f(MONOB,26),(230,20,50),(255,255,255),a)
    if t>=E_BP-0.5:     # blueprint document
        s=ease_io((t-E_BP+0.5)/0.5); aa=int(a*s); bx0,by0,bx1,by1=150,590+40*(1-s),930,1000+40*(1-s)
        d.rectangle([bx0,by0,bx1,by1],fill=(16,40,110,int(aa*0.92)),outline=ECYAN+(aa,),width=4)
        if GL: GL.rectangle([bx0,by0,bx1,by1],outline=ECYAN+(int(aa*0.6),),width=12)
        for gx in range(int(bx0)+30,int(bx1),30): d.line([(gx,by0+4),(gx,by1-4)],fill=(60,110,200,int(aa*0.35)),width=1)
        for gy in range(int(by0)+30,int(by1),30): d.line([(bx0+4,gy),(bx1-4,gy)],fill=(60,110,200,int(aa*0.35)),width=1)
        ctext(d,'FREE',f(MONOB,24),(bx0+bx1)/2,by0+24,VGOLD,aa)
        ctext(d,'ESTROGEN OPTIMIZATION',f(BEB,64),(bx0+bx1)/2,by0+58,CREAM,aa)
        ctext(d,'BLUEPRINT',f(BEB,104),(bx0+bx1)/2,by0+122,ECYAN,aa,True)
        for k,(lab,tt) in enumerate(E_ROWS):
            if t<tt: continue
            r=expo((t-tt)/0.16); y=by0+262+k*44
            check(d,bx0+60,y+4,ACID+(int(aa*r),),5,0.95); d.text((bx0+110,y),lab,font=f(MONOB,30),fill=CREAM+(int(aa*r),))
    if t>=E_C:
        s=expo((t-E_C)/0.16); sc=lerp(1.5,1,s); fn=f(MONOB,int(58*sc)); txt='COMMENT "E2"'; w=d.textlength(txt,font=fn)
        lit_bar(d,540-w/2-34,1050,540+w/2+34,1050+fn.size+40,VGOLD,int(a*s)); d.text((540-w/2,1070),txt,font=fn,fill=DEEP+(int(a*s),))
        if GL and t<E_C+0.7: GL.rectangle([540-w/2-38,1046,540+w/2+38,1054+fn.size+40],outline=VGOLD+(int(220*(1-(t-E_C)/0.7)),),width=12)
    if t>=E_AI: ctext(d,'BEFORE YOU EVER TOUCH AN AI',f(BEB,56),540,1192,CREAM,int(a*clamp((t-E_AI)/0.2)))
    ctext(d,DISC,f(MONO,20),540,1270,LABEL,a)
    ctext(d,'NOT MEDICAL ADVICE · WORK WITH YOUR DOCTOR',f(MONO,20),540,1300,LABEL,a)
    im.alpha_composite(L)

# ---------------- frame ----------------
SUBJECT_T=2.28      # visual hook: punch-in on "Grinch" (E2 is not spoken until 14.3 s; flagged)
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
