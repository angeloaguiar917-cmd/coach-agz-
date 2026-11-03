# Reel: "Hearty health" (feel fine ≠ heart fine): full edit, 720p30 preview.
# Built on the saved setup: test-06 look + full-test-02 workflow (dead air trimmed, misspeak cut, 108% punch-in per jump cut,
# captions from the trimmed audio). Usage: python render.py <scratch> [--events|--groups|--still t..|--range n0 n1 out.mp4]
import json, subprocess, sys, math, re
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
S=sys.argv[1]; F=S+'/fonts/'; T=S+'/r4/work/'
W,H=1080,1920; FPS=30; N=3379; DUR=N/FPS
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
FIX={227:'EZETIMIBE.',230:'EZETIMIBE',298:'F*CKING',305:'SH*T',98:'APOB',102:'APOB',261:'APOB'}
for i,w in FIX.items(): words[i]['w']=w
words[227]['s']=words[226]['s']; words[230]['s']=words[229]['s']        # "a zetamide" -> EZETIMIBE
for i in (390,229,226): del words[i]                                     # 390: "(static)" hallucinated in the silent end hold
for w in words: w['w']=w['w'].upper()
CAP_Y=1470; CAP_MAX=900


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
            weak=disp(w['w']) in WEAK and len(cur)>=2 and disp(words[cur[-1]]['w']) not in ('TURN','GOES','PULLS')
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
PANELS=[dict(o=20.40,c=33.45,hdr='MECHANISM 01',st=[(20.40,'LDL CLEARANCE')]),
        dict(o=35.80,c=53.30,hdr='MECHANISM 02',st=[(35.80,'LEFT VENTRICLE')]),
        dict(o=61.10,c=82.10,hdr='TOOL 01 / 02',st=[(61.10,'EZETIMIBE'),(75.78,'TELMISARTAN')],hdr2={75.78:'TOOL 02 / 02'}),
        dict(o=87.75,c=95.30,hdr='MECHANISM 02',st=[(87.75,'LV MASS')])]

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

# -- MECHANISM 01: steroids down-regulate hepatic LDL receptors -> less clearance -> ApoB climbs -> plaque --
def evA(d,t):
    a=int(255*clamp((t-20.50)/0.15))
    d.rounded_rectangle([X0,580,430,800],radius=18,outline=CREAM+(a,),width=4); d.text((X0+24,592),'LIVER',font=f(BEB,64),fill=CREAM+(a,))
    for k in range(5):
        y=610+k*42; dn=k in (1,2,4); q=ease_io((t-20.90-k*0.06)/0.35) if dn else 0
        col=tuple(int(lerp(c1,c2,q)) for c1,c2 in zip(CREAM,RED)); receptor_y(d,430,y,col,a,1-0.75*q)
    if t>=22.06: d.text((X0+24,670),'LDL RECEPTORS',font=f(MONO,22),fill=MUTED+(a,)); red_tag(d,X0+24,712,'DOWN-REGULATED',24)
    d.text((500,566),'BLOOD',font=f(MONO,22),fill=LABEL+(a,)); d.rectangle([490,596,XR,790],outline=MUTED+(int(a*0.4),),width=2)
    n=int(lerp(8,26,ease_io((t-24.02)/2.6))); particles(d,490,596,XR,790,n,t,11,VGOLD,a,0.05)
    if t>=24.72: d.text((XR-d.textlength('LESS LDL CLEARED',font=f(MONO,22)),566),'LESS LDL CLEARED',font=f(MONO,22),fill=VGOLD+(int(255*clamp((t-24.72)/0.15)),))
    if t>=25.68:
        y=860; a2=int(255*clamp((t-25.68)/0.15)); d.text((X0,y),'APOB',font=f(BEB,72),fill=CREAM+(a2,))
        meter(d,300,y+26,XR-44,lerp(0.30,0.86,ease_io((t-26.12)/0.8)),RED,26);
        if t>=26.62: tri(d,XR-30,y+24,28,True,RED+(255,))
        if t>=27.90: d.text((300,y+64),'= PARTICLE COUNT',font=f(MONO,22),fill=MUTED+(int(255*clamp((t-27.90)/0.15)),))
    if t>=29.06:
        y=1020; a3=int(255*clamp((t-29.06)/0.15)); d.text((X0,y-6),'ARTERY',font=f(MONO,22),fill=LABEL+(a3,))
        d.line([(X0,y+30),(XR,y+30)],fill=CREAM+(a3,),width=4); d.line([(X0,y+130),(XR,y+130)],fill=CREAM+(a3,),width=4)
        g=ease_io((t-29.30)/1.1)
        for k,cx in enumerate((260,520,780)):
            h=(28+10*k)*g; d.pieslice([cx-90,y+30-h,cx+90,y+30+h],0,180,fill=RED+(int(220*a3/255),)); d.pieslice([cx-70+40,y+130-h*0.8,cx+70+40,y+130+h*0.8],180,360,fill=RED+(int(200*a3/255),))
        if t>=30.36: red_tag(d,XR,y+150,'PLAQUE BUILDS',26,right=True)
    if t>=31.08:
        q=expo((t-31.08)/0.16); fn=f(MONOB,24); s='STATIN'; tw=d.textlength(s,font=fn); x=X0; y=812
        d.rectangle([x,y,x+tw+24,y+38],fill=VGOLD+(int(255*q),)); d.text((x+12,y+5),s,font=fn,fill=DEEP+(int(255*q),))
        if t>=31.70: d.text((x+tw+40,y+8),'ACTS IN LIVER',font=f(MONO,22),fill=VGOLD+(int(255*clamp((t-31.70)/0.15)),))
    if t>=32.66:
        flag_box(d,(424,596,484,794),None,32.66,t)
        if t>32.74: red_tag(d,XR,810,"DOESN'T FIX RECEPTORS",24,right=True)
sfx(20.90,'scan',d=0.45,g=-31); sfx(22.06,'tick',g=-27); sfx(25.68,'tick',g=-26); sfx(29.30,'scan',d=1.0,g=-33); sfx(30.36,'tick',g=-25); sfx(31.08,'tick',g=-29); sfx(32.74,'thud',w=1.1,g=-19)

# -- MECHANISM 02: androgens raise vascular resistance -> pressure -> LV wall thickens, function falls, no symptoms; lowering BP alone doesn't undo the wall --
def lv_wall(t):
    return lerp(34,86,ease_io((t-41.24)/2.2))
def evB(d,t):
    a=int(255*clamp((t-35.95)/0.15)); cx,cy=300,830
    ro,ri=heart(d,cx,cy,lv_wall(t),t,a)
    if t>=42.86: d.text((cx-ro,cy+ro+18),'LV WALL THICKENING',font=f(MONO,22),fill=CYAN+(int(255*clamp((t-42.86)/0.15)),))
    x0=560
    if t>=38.24: meter_row(d,x0,580,'VASCULAR RESISTANCE',lerp(0.35,0.82,ease_io((t-38.46)/0.5)),RED,int(255*clamp((t-38.24)/0.15)),True if t>=38.92 else None)
    if t>=39.68:
        v=lerp(0.40,0.86,ease_io((t-39.82)/0.4)); dropped=ease_io((t-48.34)/1.2); v=lerp(v,0.42,dropped)
        col=RED if dropped<0.5 else VGOLD
        meter_row(d,x0,680,'BLOOD PRESSURE',v,col,int(255*clamp((t-39.68)/0.15)),(True if t>=40.14 else None) if dropped<0.5 else False)
    if t>=43.96: meter_row(d,x0,780,'FUNCTION',lerp(0.82,0.50,ease_io((t-44.42)/0.6)),RED,int(255*clamp((t-43.96)/0.15)),False if t>=45.0 else None)
    if t>=45.72:
        a4=int(255*clamp((t-45.72)/0.15)); d.text((x0,880),'SYMPTOMS',font=f(BAR,34),fill=CREAM+(a4,))
        if t>=46.42: red_tag(d,XR-44,880,'NONE',26,right=True)
    if t>=51.10:
        flag_box(d,(cx-ro-10,cy-ro-10,cx+ro+10,cy+ro+10),None,51.10,t)
        if t>51.18: red_tag(d,cx-ro,cy+ro+56,'WALL STAYS THICK',24)
    if t>=52.02:
        p=expo((t-52.02)/0.10); y=1160; x1=lerp(P[0],P[2],p)
        if GL: GL.rectangle([P[0]-4,y-8,x1+4,y+96],outline=RED+(255,),width=10)
        lit_bar(d,P[0],y,x1,y+88,RED); d.rectangle([P[0],y+84,x1,y+88],fill=(140,0,0))
        if p>0.6: d.text((P[0]+40,y+8),'BP DOWN ≠ WALL FIXED',font=f(BEB,72),fill=(255,255,255))
sfx(38.46,'tick',g=-28); sfx(39.82,'tick',g=-28); sfx(41.24,'scan',d=2.0,g=-34); sfx(44.42,'tick',g=-28); sfx(46.42,'tick',g=-25); sfx(48.34,'scan',d=1.0,g=-33); sfx(52.12,'impact',g=-13)

# -- TOOL 01: ezetimibe (blocks gut absorption -> liver pulls more LDL from blood -> LDL, ApoB down, no hormonal interference) --
def evC(d,t):
    q=expo((t-62.26)/0.18)
    if q>0: gold_tag(d,X0,560,'EZETIMIBE',30)
    a=int(255*clamp((t-61.25)/0.15)); y0,y1=640,820
    for (x0,x1,lab) in ((X0,330,'GUT'),(420,640,'LIVER')):
        d.rounded_rectangle([x0,y0,x1,y1],radius=16,outline=CREAM+(a,),width=4); d.text((x0+18,y0+10),lab,font=f(BEB,56),fill=CREAM+(a,))
    d.rectangle([700,y0,XR,y1],outline=MUTED+(int(a*0.4),),width=2); d.text((710,y0-30),'BLOOD',font=f(MONO,22),fill=LABEL+(a,))
    # cholesterol from the gut toward the liver; gate closes on "blocks"
    gate=expo((t-63.40)/0.14)
    for k in range(7):
        u=((t-61.3)*0.45+k/7)%1.0; x=lerp(X0+40,620,u); y=y0+120+((k*37)%40)
        if gate>0.5 and x>340: continue
        if x<330 or x>420 or gate<0.5: d.ellipse([x-9,y-9,x+9,y+9],fill=VGOLD+(a,))
    if gate>0:
        d.rectangle([360,y0-10,390,y1+10],fill=VGOLD+(int(255*gate),))
        if GL: GL.rectangle([360,y0-10,390,y1+10],fill=VGOLD+(int(180*gate),))
        d.text((X0,y1+14),'ABSORPTION BLOCKED',font=f(MONO,22),fill=VGOLD+(int(255*gate),))
    if t>=66.20: d.text((420,y1+14),'LESS REACHES LIVER',font=f(MONO,22),fill=MUTED+(int(255*clamp((t-66.20)/0.15)),))
    pull=ease_io((t-67.72)/2.2)
    for k in range(5):
        y=y0+30+k*30; receptor_y(d,640,y,VGOLD if pull>0 else CREAM,a,0.6+0.4*pull)
    n=int(lerp(22,5,pull)); particles(d,700,y0,XR,y1,n,t,17,VGOLD,a,0.04)
    if t>=68.46: d.text((700,y1+14),'LDL PULLED FROM BLOOD',font=f(MONO,22),fill=VGOLD+(int(255*clamp((t-68.46)/0.15)),))
    if t>=70.26: meter_row(d,X0,900,'LDL',lerp(0.78,0.36,ease_io((t-70.70)/0.6)),VGOLD,int(255*clamp((t-70.26)/0.15)),False if t>=71.10 else None)
    if t>=72.76: meter_row(d,X0,990,'APOB',lerp(0.80,0.40,ease_io((t-73.38)/0.6)),VGOLD,int(255*clamp((t-72.76)/0.15)),False if t>=73.70 else None)
    if t>=74.54: green_tag(d,XR,1110,'NO HORMONAL INTERFERENCE',int(255*clamp((t-74.54)/0.15)))
# -- TOOL 02: telmisartan (blocks angiotensin II -> vessels relax -> pressure + wall stress down) --
def evD(d,t):
    q=expo((t-76.28)/0.18)
    if q>0: gold_tag(d,X0,560,'TELMISARTAN',30)
    a=255; relax=ease_io((t-79.12)/0.6)
    gap=lerp(60,120,relax); cy=790
    d.line([(X0,cy-gap),(XR,cy-gap)],fill=CYAN+(a,),width=6); d.line([(X0,cy+gap),(XR,cy+gap)],fill=CYAN+(a,),width=6)
    if GL: GL.line([(X0,cy-gap),(XR,cy-gap)],fill=CYAN+(150,),width=12); GL.line([(X0,cy+gap),(XR,cy+gap)],fill=CYAN+(150,),width=12)
    blk=expo((t-77.26)/0.16)
    for k in range(4):
        x=X0+90+k*220
        for sgn in (-1,1):
            yy=cy+sgn*gap; d.rectangle([x-12,yy-12,x+12,yy+12],fill=(RED if blk<0.5 else VGOLD)+(255,))
    if t>=77.74: d.text((X0,622),'ANGIOTENSIN II RECEPTORS' if blk<0.5 else 'ANGIOTENSIN II · BLOCKED',font=f(MONO,22),fill=(RED if blk<0.5 else VGOLD)+(255,))
    if t>=79.46: s='RELAXED'; d.text((XR-d.textlength(s,font=f(MONO,22)),cy+gap+16),s,font=f(MONO,22),fill=CYAN+(int(255*clamp((t-79.46)/0.15)),))
    if t>=80.06: meter_row(d,X0,990,'BLOOD PRESSURE',lerp(0.84,0.46,ease_io((t-80.22)/0.4)),VGOLD,int(255*clamp((t-80.06)/0.15)),False if t>=80.54 else None)
    if t>=81.10: meter_row(d,X0,1090,'LV WALL STRESS',lerp(0.84,0.44,ease_io((t-81.26)/0.5)),VGOLD,int(255*clamp((t-81.10)/0.15)),False if t>=81.82 else None)
sfx(62.26,'tick',g=-27); sfx(63.40,'thud',w=1.2,g=-18); sfx(67.72,'scan',d=1.6,g=-33); sfx(71.10,'tick',g=-28); sfx(73.70,'tick',g=-28); sfx(74.54,'tick',g=-30)
sfx(76.28,'tick',g=-27); sfx(77.26,'thud',w=1.2,g=-18); sfx(79.12,'scan',d=0.6,g=-32); sfx(80.54,'tick',g=-28); sfx(81.82,'tick',g=-28)

# -- callback: telmisartan and existing LV mass (the heart from MECHANISM 02 returns) --
def evE(d,t):
    a=255; cx,cy=330,820
    d.text((X0,566),'HYPERTENSION STUDIES · TELMISARTAN',font=f(MONO,24),fill=MUTED+(int(255*clamp((t-88.40)/0.2)),))
    wall=lerp(86,58,ease_io((t-91.80)/1.6)); ro,ri=heart(d,cx,cy,wall,t,a,CYAN)
    if t>=92.24: d.text((560,700),'EXISTING LV MASS',font=f(BAR,40),fill=CREAM+(int(255*clamp((t-92.24)/0.15)),))
    if t>=91.80:
        s=ease_io((t-91.80)/1.6); meter(d,560,760,XR-44,lerp(0.86,0.62,s),VGOLD,26);
        if s>=1: tri(d,XR-30,756,28,False,VGOLD+(255,))
    if t>=93.62: gold_tag(d,560,820,'CAN REGRESS',30)
    if t>=94.14: d.text((560,900),'NOT JUST PREVENTION',font=f(MONO,26),fill=VGOLD+(int(255*clamp((t-94.14)/0.15)),))
sfx(91.80,'scan',d=1.6,g=-33); sfx(93.72,'thud',w=1.3,g=-17)
CONTENT={0:[(20.40,evA)],1:[(35.80,evB)],2:[(61.10,evC),(75.78,evD)],3:[(87.75,evE)]}
SHAKES=[52.12]

# ---- persistent TOOL strip under the pinned title: 2 empty slots -> mechanisms -> compounds -> linked ----
STRIP_IN=8.44; STRIP_OUT=100.55
SLOTS=[dict(mech=(56.48,'APOB / LDL'),name=(62.26,'EZETIMIBE')),dict(mech=(56.82,'LV WALL / BP'),name=(76.28,'TELMISARTAN'))]
LINK=96.40
sfx(STRIP_IN,'tick',g=-29); sfx(56.48,'tick',g=-30); sfx(56.82,'tick',g=-30); sfx(LINK,'thud',w=1.0,g=-19)
def strip(im,t):
    if t<STRIP_IN or t>STRIP_OUT+0.25: return
    out=ease_io((t-STRIP_OUT)/0.25)
    for i,sl in enumerate(SLOTS):
        q=expo((t-STRIP_IN-i*0.10)/0.16)
        if q<=0: continue
        x0=64+i*488; x1=x0+464; y0=398-12*(1-q)-30*out; y1=y0+64; a=int(255*q*(1-out))
        if a<=0: continue
        frosted(im,(x0,y0,x1,y1),0.88*(a/255),10); L,d=newL()
        lit=(t>=sl['name'][0])*1 + (t>=LINK)*1
        oc=VGOLD if lit else MUTED
        d.rectangle([x0,y0,x1,y1],outline=oc+(int(a*(0.9 if lit else 0.5)),),width=3 if t>=LINK else 2)
        d.text((x0+16,y0+16),f'0{i+1}',font=f(MONOB,26),fill=VGOLD+(a,))
        if t>=sl['name'][0]:
            nq=expo((t-sl['name'][0])/0.16); d.text((x0+66,y0+8+10*(1-nq)),sl['name'][1],font=f(BEB,50),fill=CREAM+(int(a*nq),))
        elif t>=sl['mech'][0]:
            d.text((x0+66,y0+18),'? · '+sl['mech'][1],font=f(MONO,24),fill=MUTED+(a,))
        else: d.text((x0+66,y0+18),'TOOL ?',font=f(MONO,24),fill=LABEL+(a,))
        if GL and t>=LINK and t<LINK+0.6: GL.rectangle([x0,y0,x1,y1],outline=VGOLD+(int(200*(1-(t-LINK)/0.6)),),width=8)
        im.alpha_composite(L)
    if t>=LINK:
        L,d=newL(); q=expo((t-LINK)/0.16); a=int(255*q*(1-out)); fn=f(BEB,64)
        d.text((540-d.textlength('+',font=fn)/2,388),'+',font=fn,fill=VGOLD+(a,)); im.alpha_composite(L)



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

# ---- hook: "FEEL FINE ≠ HEART FINE" + silent-status lines; headline hands off into the pinned title ----
TK=0.05; TL2=0.52; TRED=2.68; TS1=5.34; TS2=6.16; THO=(7.20,7.55)
sfx(TK,'tick',g=-30); sfx(TL2,'thud',w=1.3,g=-16); sfx(TS1,'tick',g=-26); sfx(TS2,'tick',g=-26); sfx(THO[0],'whoosh',d=0.30,g=-28)
PIN_WIN=[(THO[0],100.55)]
def pin_vis(t):
    v=0
    for i,(a,b_) in enumerate(PIN_WIN):
        if t<a: continue
        fin=1 if i==0 else clamp((t-a)/0.25); fout=clamp((b_+0.25-t)/0.25); v=max(v,fin*fout)
    return ease_io(v)
def headline(d,x,y,fn,a,t):
    d.text((x,y),'FEEL FINE ',font=fn,fill=CREAM+(a,)); x+=d.textlength('FEEL FINE ',font=fn)
    rc=ease_io((t-TRED)/0.10); col=tuple(int(lerp(c1,c2,rc)) for c1,c2 in zip(CREAM,RED))
    d.text((x,y),'≠',font=fn,fill=col+(a,)); x+=d.textlength('≠',font=fn)
    d.text((x,y),' HEART FINE',font=fn,fill=CREAM+(a,))
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
        lab='ON CYCLE · HEART HEALTH'; fn=f(BAR,lerp(38,30,h)); n=int(len(lab)*clamp((t-TK-0.12)/0.40)) if h<=0.5 else len(lab)
        tracked(d,(130,ky+lerp(0,3,h)),lab[:n],fn,GOLD,lerp(9,7,h))
    if h>0:
        a=int(255*h); fn=f(MONO,24); s='@coach.agz'; d.text((1016-d.textlength(s,font=fn),ky+6),s,font=fn,fill=GOLD+(a,))
        d.text((64,352+ty),DISC,font=f(MONO,18),fill=LABEL+(a,))
    q2=expo((t-TL2)/0.16)
    if q2>0:
        size=lerp(112,86,h); y=lerp(290,262,h)+ty+12*(1-q2); a=int(255*q2)
        headline(d,64,y,f(BEB,size),a,t)
    if h<1:
        for k,(lab,tt) in enumerate((('PAIN',TS1),('WARNING',TS2))):
            q=expo((t-tt)/0.14)
            if q<=0: continue
            a=int(255*q*(1-clamp(h*3))); y=418+k*48; fn=f(MONO,30)
            L2,d2=newL(); d2.text((64,y),lab,font=fn,fill=CREAM+(a,)); x=64+d2.textlength('WARNING ',font=fn)
            d2.text((x,y),'· NONE',font=f(MONOB,30),fill=RED+(a,))
            if GL and t<tt+0.4: GL.text((x,y),'· NONE',font=f(MONOB,30),fill=RED+(int(160*(1-(t-tt)/0.4)),))
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
END=100.62; PILL=107.96; SENT=109.82
sfx(END,'scan',d=0.30,g=-29); sfx(101.74,'tick',g=-30); sfx(PILL-0.05,'whoosh',d=0.22,g=-27); sfx(PILL+0.10,'thud',w=1.6,g=-14); sfx(SENT,'tick',g=-28)
def end_card(im,t):
    if t<END: return
    a=ease_io((t-END)/0.30); im.alpha_composite(scene_bg(a))
    q=expo((t-END-0.15)/0.25)
    if q<=0: return
    lg=logo().copy(); lg.putalpha(lg.split()[3].point(lambda v:int(v*q))); im.alpha_composite(lg,(540-120,300))
    L,d=newL(); A=int(255*q)
    fn=f(BAR,40); s='COACH AGZ'; w=tracked_w(d,s,fn,10); tracked(d,(540-w/2,566),s,fn,GOLD+(A,),10)
    fn=f(MONO,28); s='@coach.agz'; d.text((540-d.textlength(s,font=fn)/2,622),s,font=fn,fill=MUTED+(A,))
    kq=expo((t-101.46)/0.2)
    if kq>0: fn=f(BAR,36); s='THE FULL'; w=tracked_w(d,s,fn,8); tracked(d,(540-w/2,716),s,fn,GOLD+(int(255*kq),),8)
    for s,tt,y in [('HEART HEALTH',101.74,762),('PROTOCOL + FRAMEWORK',102.30,872)]:
        hq=expo((t-tt)/0.16)
        if hq<=0: continue
        fn=f(BEB,112 if y==762 else 84); col=RED if y==762 else CREAM
        d.text((540-d.textlength(s,font=fn)/2,y+12*(1-hq)),s,font=fn,fill=col+(int(255*hq),))
    im.alpha_composite(L); L,d=newL()
    pq=expo((t-PILL)/0.20)
    if pq>0:
        fn=f(MONOB,58); s='COMMENT "HEALTH"'; tw=d.textlength(s,font=fn); bw=tw+80; x0=540-bw/2; y0=1010+lerp(-40,0,pq)
        if GL and t<PILL+0.6: GL.rectangle([x0,y0,x0+bw,y0+120],outline=VGOLD+(int(220*(1-(t-PILL)/0.6)),),width=10)
        lit_bar(d,x0,y0,x0+bw,y0+120,VGOLD,int(255*min(1,pq*1.5)))
        im.alpha_composite(L); L,d=newL()
        tq=clamp((t-PILL-0.08)/0.12)
        if tq>0: d.text((540-tw/2,y0+24),s,font=fn,fill=DEEP+(int(255*tq),))
    fq=expo((t-SENT)/0.14)
    if fq>0: fn=f(MONOB,36); s='SENT TO YOU'; d.text((540-d.textlength(s,font=fn)/2,1160),s,font=fn,fill=CREAM+(int(255*fq),))
    fn=f(MONO,20); d.text((540-d.textlength(DISC,font=fn)/2,1240),DISC,font=fn,fill=LABEL+(A,))
    im.alpha_composite(L)


# ---------------- frame ----------------
def zoom_at(t):   # saved setup: 108% punch-in alternates at every jump cut
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
    title(im,t); strip(im,t)
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
