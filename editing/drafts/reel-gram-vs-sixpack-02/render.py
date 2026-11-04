# Reel: "Gram vs 6pack" take 2 (outdoor, 42 drinks a week): full edit, 720p30 preview. Opens with the TEXT_HOOK_ENGINE frame-0 hook.
# Built on the saved setup: test-06 look + full-test-02 workflow (dead air trimmed, misspeak cut, 108% punch-in per jump cut,
# captions from the trimmed audio). Usage: python render.py <scratch> [--events|--groups|--still t..|--range n0 n1 out.mp4]
import json, subprocess, sys, math, re
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
S=sys.argv[1]; F=S+'/fonts/'; T=S+'/r7/work/'
W,H=1080,1920; FPS=30; N=2674; DUR=N/FPS
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


# ---------------- words / captions (windowed medium.en transcript of the trimmed cut) ----------------
words=json.load(open(T+'words_asm.json'))   # = words_captions.json in this folder
FIX={32:'OF',129:'SH*T',150:'F*CKING',153:'IN',221:'END OF',155:'TERMS,'}
# 153: heard "On basic terms" -> IN (Coach AGZ's usual phrase "in basic terms")
# 221: heard "On the day" / "In the day" (clipped) -> "END OF the day": flagged for Coach AGZ to confirm
for i,w in FIX.items(): words[i]['w']=w
words[62]['w']='LONG-TERM'; words[62]['e']=words[63]['e']; del words[63]
k=[i for i,w in enumerate(words) if w['w'].lower().startswith('cardiovascular') and 41<w['s']<42][0]   # cut transcript dropped "system" (heard by the final-audio pass)
words.insert(k+1,{'w':'SYSTEM,','s':round(words[k]['s']+0.62,3),'e':round(words[k+1]['s']-0.04,3)})
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
            weak=disp(w['w']) in WEAK and len(cur)>=2 and disp(words[cur[-1]]['w']) not in ('GET','KILL','DONE')
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
PANELS=[dict(o=6.76,c=21.40,hdr='SIDE A',st=[(6.76,'1 GRAM TEST / WEEK')]),
        dict(o=25.36,c=38.20,hdr='SIDE B',st=[(25.36,'6 BEERS / NIGHT')]),
        dict(o=40.08,c=63.98,hdr='A vs B',st=[(40.08,'SAME HEART'),(47.36,'WHICH KILLS FASTER')],hdr2={47.36:'VERDICT'}),
        dict(o=68.20,c=81.60,hdr='WHAT MATTERS',st=[(68.20,'GET YOUR BLOODWORK DONE')])]

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

# ---- marker rows: label lands on its word, status snaps in on the verb ----
def marker_row(d,t,y,label,t0,t1,stat,up,col=RED):
    q=expo((t-t0)/0.14)
    if q<=0: return
    a=int(255*q); dx=-24*(1-q); d.text((X0+dx,y),label,font=f(BAR,40),fill=CREAM+(a,))
    d.line([(X0,y+58),(XR,y+58)],fill=MUTED+(int(a*0.22),),width=2)
    if t>=t1:
        s=expo((t-t1)/0.12); fn=f(MONOB,24); tw=d.textlength(stat,font=fn); x=XR-tw-60
        if up is not None: tri(d,XR-34,y+12,26,up,col+(int(255*s),))
        d.text((x,y+10),stat,font=fn,fill=col+(int(255*s),))
        if GL and t<t1+0.35: GL.text((x,y+10),stat,font=fn,fill=col+(int(150*(1-(t-t1)/0.35)),))
def verdict_bar(d,t,t0,big,small,col=RED):
    if t<t0: return
    p=expo((t-t0)/0.10); y=1160; x1=lerp(P[0],P[2],p)
    if GL: GL.rectangle([P[0]-4,y-8,x1+4,y+96],outline=col+(255,),width=10)
    lit_bar(d,P[0],y,x1,y+88,col); d.rectangle([P[0],y+84,x1,y+88],fill=(140,0,0) if col==RED else (150,110,0))
    if p>0.6:
        fn=f(BEB,72); tc=(255,255,255) if col==RED else DEEP; d.text((P[0]+40,y+8),big,font=fn,fill=tc)
        if small: d.text((P[0]+40+d.textlength(big,font=fn)+26,y+30),small,font=f(MONO,26) if col==RED else f(MONOB,26),fill=tc)

# -- SIDE A: 1 gram of test a week; then long-term risk --
ROWS_A=[('HEMATOCRIT',8.02,8.54,'CLIMBS',True),('BLOOD PRESSURE',9.16,9.60,'RISES',True),('HDL',10.20,10.62,'CRASHES',False),
        ('APOB',11.34,12.20,'CAN INCREASE',True),('NATURAL PRODUCTION',13.02,14.72,'SUPPRESSED',False)]
ROWS_A2=[('CARDIAC REMODELING',18.44,18.82,'RISK',True),('CARDIOVASCULAR DISEASE',20.54,21.18,'RISK',True)]
def evA(d,t):
    for i,(lab,t0,t1,st,up) in enumerate(ROWS_A): marker_row(d,t,556+i*74,lab,t0,t1,st,up)
    if t>=16.36:
        a=int(255*clamp((t-16.36)/0.15)); y=940
        d.text((X0,y),'LONG-TERM',font=f(MONO,24),fill=VGOLD+(a,)); d.line([(X0+170,y+14),(XR,y+14)],fill=VGOLD+(int(a*0.5),),width=2)
    for i,(lab,t0,t1,st,up) in enumerate(ROWS_A2): marker_row(d,t,990+i*74,lab,t0,t1,st,up)
for _,t0,t1,_,_ in ROWS_A+ROWS_A2: sfx(t1,'tick',g=-30)
sfx(16.36,'scan',d=0.4,g=-32); sfx(21.18,'thud',w=1.2,g=-18)

# -- SIDE B: 6 beers a night = 42 drinks a week --
ROWS_B=[('LIVER DISEASE',27.20,27.36,'RISK',True),('TRIGLYCERIDES',27.92,28.28,'ELEVATED',True),('HYPERTENSION',29.12,29.12,'RISK',True),
        ('SLEEP',29.84,30.18,'DISRUPTED',False),('CANCER RISK',31.14,31.54,'INCREASED',True)]
def evB(d,t):
    q=expo((t-25.74)/0.16)
    if q>0:
        a=int(255*q); s=lerp(1.12,1,q); fn=f(BEB,int(150*s)); d.text((X0,546+(1-s)*60),'42',font=fn,fill=VGOLD+(a,))
        if GL and t<26.3: GL.text((X0,546+(1-s)*60),'42',font=fn,fill=VGOLD+(int(140*(1-(t-25.74)/0.56)),))
        if t>=26.10: d.text((X0+180,580),'DRINKS A WEEK',font=f(BAR,54),fill=CREAM+(int(255*clamp((t-26.10)/0.15)),))
        if t>=26.48: d.text((X0+182,646),'6 A NIGHT × 7',font=f(MONO,24),fill=MUTED+(int(255*clamp((t-26.48)/0.15)),))
    for i,(lab,t0,t1,st,up) in enumerate(ROWS_B): marker_row(d,t,730+i*74,lab,t0,t1,st,up)
    verdict_bar(d,t,34.56,'GROUP 1 CARCINOGEN',None)
# (no separate thud for the 42: the SIDE B panel lands 0.26 s earlier and carries the beat)
for _,t0,t1,_,_ in ROWS_B: sfx(t1,'tick',g=-30)
sfx(34.66,'impact',g=-13)

# -- A vs B stage 1: same heart, two standards --
def evC(d,t):
    cA,cB=640,860
    for x,lab,tt in ((cA,'1 GRAM',40.08),(cB,'6 BEERS',40.28)):
        q=expo((t-tt)/0.16)
        if q>0: fn=f(BEB,56); d.text((x-d.textlength(lab,font=fn)/2,556),lab,font=fn,fill=VGOLD+(int(255*q),))
    d.line([(750,560),(750,820)],fill=MUTED+(60,),width=2)
    q=expo((t-41.48)/0.14)
    if q>0:
        y=650; a=int(255*q); d.text((X0,y),'CARDIOVASCULAR',font=f(BAR,40),fill=CREAM+(a,)); d.text((X0,y+44),'DAMAGE',font=f(BAR,40),fill=CREAM+(a,))
        for k,x in enumerate((cA,cB)):
            s=expo((t-41.48-k*0.06)/0.12); r=16; d.ellipse([x-r,y+30,x+r,y+30+2*r],fill=RED+(int(255*s),))
            if GL and t<41.9: GL.ellipse([x-r-6,y+24,x+r+6,y+36+2*r],fill=RED+(int(170*(1-(t-41.48)/0.42)),))
    if t>=43.50: red_tag(d,cA-110,860,'STIGMATIZED',26)
    if t>=46.34:
        q=expo((t-46.34)/0.14); fn=f(MONOB,24); s='SUPER BOWL AD'; tw=d.textlength(s,font=fn); x=cB-tw/2
        lit_bar(d,x-12,860,x+tw+12,900,VGOLD,int(255*q)); d.text((x,866),s,font=fn,fill=DEEP+(int(255*q),))
    verdict_bar(d,t,46.76,'SAME BODY · TWO STANDARDS',None)
sfx(41.48,'tick',g=-27); sfx(43.50,'tick',g=-26); sfx(46.34,'tick',g=-27); sfx(46.86,'impact',g=-14)

# -- A vs B stage 2: which kills faster? can't tell without 3 things; what IS known: drinkers skip bloodwork for years --
def evD(d,t):
    a=int(255*clamp((t-48.60)/0.15))
    d.text((X0,566),"CAN'T BE CALLED WITHOUT",font=f(MONO,26),fill=MUTED+(a,))
    x=X0
    for lab,tt in [('DURATION',52.10),('INDIVIDUAL RISK',53.00),('HEALTH OUTCOMES',53.84)]:
        q=expo((t-tt)/0.14)
        if q<=0: continue
        fn=f(BAR,38); tw=d.textlength(lab,font=fn); aa=int(255*q)
        d.rectangle([x,612,x+tw+36,670],outline=VGOLD+(aa,),width=3); d.text((x+18,616),lab,font=fn,fill=VGOLD+(aa,)); x+=tw+50
    if t>=54.50:
        a2=int(255*clamp((t-54.50)/0.15)); d.line([(X0,720),(XR,720)],fill=MUTED+(int(a2*0.3),),width=2)
        d.text((X0,744),'WHAT IS KNOWN',font=f(MONO,26),fill=GREEN+(a2,))
    if t>=55.60:
        a3=int(255*clamp((t-55.60)/0.15)); d.text((X0,800),'6 BEERS A NIGHT · LAST BLOODWORK',font=f(BAR,40),fill=CREAM+(a3,))
    yrs=None
    for v,tt in ((3,59.36),(4,59.64),(5,59.98)):
        if t>=tt: yrs=v
    if yrs:
        fn=f(BEB,150); s=f'{yrs}'; d.text((X0,860),s,font=fn,fill=RED+(255,)); w=d.textlength(s,font=fn)
        d.text((X0+w+24,920),'YEARS AGO' if t<60.28 else 'YEARS AGO',font=f(BEB,72),fill=CREAM+(255,))
        if GL and t<60.6: GL.text((X0,860),s,font=fn,fill=RED+(140,))
    if t>=62.04: red_tag(d,XR,1060,'ONLY A BASIC PANEL · WHEN SICK',26,right=True)
sfx(52.10,'tick',g=-28); sfx(53.00,'tick',g=-28); sfx(53.84,'tick',g=-28); sfx(54.50,'scan',d=0.3,g=-31)
sfx(59.36,'tick',g=-25); sfx(59.64,'tick',g=-25); sfx(59.98,'thud',w=1.3,g=-17); sfx(62.04,'tick',g=-27)

# -- what matters: get your bloodwork done (checklist) --
CHK=[("WHAT'S HAPPENING IN YOUR SYSTEM",73.64),('SIDE EFFECT MITIGATION',76.04),('YOUR BIOMARKERS',77.82),('HOW TO OPTIMIZE',79.14)]
def evE(d,t):
    a=int(255*clamp((t-68.40)/0.15))
    d.text((X0,566),'RUNNING',font=f(MONO,24),fill=LABEL+(a,))
    if t>=69.86: gold_tag(d,X0+130,556,'1 GRAM',24)
    if t>=71.28: d.text((X0+300,566),'OR DRINKING',font=f(MONO,24),fill=LABEL+(int(255*clamp((t-71.28)/0.15)),)); gold_tag(d,X0+500,556,'EVERY NIGHT',24)
    q=expo((t-72.58)/0.16)
    if q>0:
        fn=f(BEB,96); d.text((X0,630+10*(1-q)),'GET YOUR BLOODWORK',font=fn,fill=CREAM+(int(255*q),))
        q2=expo((t-73.06)/0.16)
        if q2>0: d.text((X0,722),'DONE.',font=fn,fill=VGOLD+(int(255*q2),))
    d.text((X0,836),'UNDERSTAND',font=f(MONO,24),fill=LABEL+(int(255*clamp((t-73.64)/0.15)),))
    for i,(lab,tt) in enumerate(CHK):
        q=expo((t-tt)/0.14)
        if q<=0: continue
        y=876+i*72; aa=int(255*q); dx=-24*(1-q)
        d.rectangle([X0+dx,y+4,X0+dx+40,y+44],outline=GREEN+(aa,),width=3); check(d,X0+dx+8,y+12,GREEN+(aa,),5,1.0)
        if GL and t<tt+0.4: check(GL,X0+dx+8,y+12,GREEN+(aa,),10,1.0)
        d.text((X0+64+dx,y+2),lab,font=f(BAR,40),fill=CREAM+(aa,))
for _,tt in CHK: sfx(tt,'tick',g=-29)
sfx(72.58,'thud',w=1.3,g=-17)
CONTENT={0:[(6.76,evA)],1:[(25.36,evB)],2:[(40.08,evC),(47.36,evD)],3:[(68.20,evE)]}
SHAKES=[34.66,46.86]






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
HOOK_LINES=[[('1 GRAM',VGOLD),(' vs ',CREAM),('42 DRINKS',VGOLD)],[('your heart pays either way',CREAM)]]
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
    bin_=clamp((t-HOOK_END)/HOOK_FADE); bout=1-clamp((t-BAND_OUT)/0.15); v=bin_*bout
    if v>0 and t>=HOOK_END:
        B,bd=newL(); bd.rectangle([8,212,W,372],fill=NAVY+(int(235*v),)); im.alpha_composite(B)
        a=int(255*v); fn=f(BAR,64); x=64; y=236
        for s,c in [('1 GRAM',VGOLD),(' a week vs ',CREAM),('6 BEERS',VGOLD),(' a night',CREAM)]: d.text((x,y),s,font=fn,fill=c+(a,)); x+=d.textlength(s,font=fn)
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
END=81.68; NO1=82.86; NO2=84.10
sfx(END,'scan',d=0.30,g=-29); sfx(NO1,'tick',g=-24); sfx(NO2+0.6,'thud',w=1.4,g=-16)
def end_card(im,t):
    if t<END: return
    a=ease_io((t-END)/0.30); im.alpha_composite(scene_bg(a))
    q=expo((t-END-0.15)/0.25)
    if q<=0: return
    lg=logo().copy(); lg.putalpha(lg.split()[3].point(lambda v:int(v*q))); im.alpha_composite(lg,(540-120,214))
    L,d=newL(); A=int(255*q)
    fn=f(BAR,40); s='COACH AGZ'; w=tracked_w(d,s,fn,10); tracked(d,(540-w/2,466),s,fn,GOLD+(A,),10)
    fn=f(MONO,28); s='@coach.agz'; d.text((540-d.textlength(s,font=fn)/2,522),s,font=fn,fill=MUTED+(A,))
    fn=f(BAR,36); s='NOT THE WAY'; w=tracked_w(d,s,fn,8); tracked(d,(540-w/2,620),s,fn,GOLD+(A,),8)
    for lab,tt,y in (('6 BEERS A NIGHT',NO1,676),('1 GRAM EVERY WEEK FOR LIFE',NO2,786)):
        hq=expo((t-tt)/0.16)
        if hq<=0: continue
        fn=f(BEB,92); tw=d.textlength(lab,font=fn)
        if tw>900: fn=f(BEB,int(92*900/tw)); tw=d.textlength(lab,font=fn)
        x=540-tw/2; d.text((x,y+10*(1-hq)),lab,font=fn,fill=CREAM+(int(255*hq),))
        sq=expo((t-tt-0.35)/0.18)
        if sq>0:
            d.line([(x-10,y+50),(lerp(x-10,x+tw+10,sq),y+50)],fill=RED+(255,),width=8)
            if GL: GL.line([(x-10,y+50),(lerp(x-10,x+tw+10,sq),y+50)],fill=RED+(200,),width=14)
    bq=expo((t-86.84)/0.2)
    if bq>0:
        fn=f(MONOB,34); s='GET YOUR BLOODWORK DONE'; d.text((540-d.textlength(s,font=fn)/2,920),s,font=fn,fill=VGOLD+(int(255*bq),))
    fn=f(MONO,20); d.text((540-d.textlength(DISC,font=fn)/2,1000),DISC,font=fn,fill=LABEL+(A,))
    im.alpha_composite(L)


# ---------------- frame ----------------
SUBJECT_T=0.26      # visual hook: first punch-in lands on the spoken subject "a thousand milligrams"
def zoom_at(t):   # saved setup: 108% punch-in alternates at every jump cut
    if t<CUTS[0]: return 1.08 if t>=SUBJECT_T else 1.0
    return 1.0 if seg_of(t)%2==1 else 1.08

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
