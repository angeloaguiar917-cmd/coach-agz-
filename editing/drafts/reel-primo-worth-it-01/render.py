# Reel: "Primo Ai edit" (Primo: holy grail or placebo): full edit, 720p30 preview. Opens with the TEXT_HOOK_ENGINE frame-0 hook.
# Built on the saved setup: test-06 look + full-test-02 workflow (dead air trimmed, misspeak cut, 108% punch-in per jump cut,
# captions from the trimmed audio). Usage: python render.py <scratch> [--events|--groups|--still t..|--range n0 n1 out.mp4]
import json, subprocess, sys, math, re
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
S=sys.argv[1]; F=S+'/fonts/'; T=S+'/r5/work/'
W,H=1080,1920; FPS=30; N=2808; DUR=N/FPS
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
FIX={1:'PRIMOBOLAN',49:'PRIMOBOLAN,',64:'SO',236:'VIAL',179:'SH*T',313:'PRIMOBOLAN',113:'PRIMO',224:'PRIMO,',245:'PRIMO',254:'PRIMO',297:'PRIMO',330:'PRIMO',
     125:'COMPOUNDS,',137:'SIGNAL.',146:'WAYS.',166:'LOW.',185:'COMPOUND.',211:'THERE.',229:'MYSTERY.',248:'TIMES.',256:'IT?',295:'TRANSFORMATION,',300:'YOU.',305:'SAID,',326:'EFFICIENTLY,'}
# 64: one pass hears "until", the other "so"; "so there's no water" is the sense -> SO
for i,w in FIX.items(): words[i]['w']=w
words[313]['e']=words[314]['e']; del words[314]                          # "primo bowling" -> PRIMOBOLAN
k=[i for i,w in enumerate(words) if w['w'].lower()=='send' and 86<w['s']<87][0]   # cut transcript dropped "it": "I'll send [it] out" (heard by the source and final passes)
words.insert(k+1,{'w':'IT','s':round(words[k]['s']+0.07,3),'e':round(words[k+1]['s']-0.01,3)})
for w in words: w['w']=w['w'].upper()
CAP_Y=1335; CAP_MAX=900



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
            weak=disp(w['w']) in WEAK and len(cur)>=2 and disp(words[cur[-1]]['w']) not in ('FREES','LOOK','SOLD')
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
PANELS=[dict(o=11.48,c=34.62,hdr='EVIDENCE 01',st=[(11.48,'COMPOUND PROFILE'),(24.08,'THE CATCH')],hdr2={24.08:'EVIDENCE 02'}),
        dict(o=37.02,c=47.24,hdr='WAY 01 / 02',st=[(37.02,'ESTROGEN CRASH')]),
        dict(o=51.04,c=63.40,hdr='WAY 02 / 02',st=[(51.04,'COUNTERFEIT RISK')]),
        dict(o=63.48,c=78.90,hdr='VERDICT',st=[(63.48,'IS PRIMO WORTH IT')])]

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

# ---- EVIDENCE 01: compound profile (DHT-derived, no aromatization -> no water, no oral liver hit, binds SHBG -> frees T) ----
def status_row(d,y,label,t0,tstat,stat,col,sub=None,a_mul=1.0):
    q=expo((t_now-t0)/0.14)
    if q<=0: return
    a=int(255*q*a_mul); d.text((X0,y),label,font=f(BAR,44),fill=CREAM+(a,))
    d.line([(X0,y+66),(XR,y+66)],fill=MUTED+(int(a*0.25),),width=2)
    if t_now>=tstat:
        s=expo((t_now-tstat)/0.12)
        if col==GREEN: green_tag(d,XR,y+8,stat,int(255*s))
        elif col==VGOLD: gold_tag(d,XR,y+2,stat,26,right=True)
        else: red_tag(d,XR,y+2,stat,26,right=True)
        if sub: d.text((X0,y+36),sub,font=f(MONO,22),fill=MUTED+(int(255*s),))
t_now=0
def evA(d,t):
    global t_now; t_now=t
    q=expo((t-11.66)/0.16)
    if q>0:
        fn=f(BAR,44); s='PRIMOBOLAN'; tw=d.textlength(s,font=fn); a=int(255*q)
        d.rectangle([X0,566,X0+tw+40,628],outline=CREAM+(a,),width=3); d.text((X0+20,572),s,font=fn,fill=CREAM+(a,))
        if t>=12.92: d.text((X0+tw+64,584),'METHENOLONE',font=f(MONO,26),fill=MUTED+(int(255*clamp((t-12.92)/0.15)),))
        if t>=13.70: gold_tag(d,XR,574,'DHT-DERIVED',26,right=True)
    status_row(d,680,'AROMATIZATION',15.08,15.60,'NONE',GREEN)
    if t>=16.62: d.text((X0+330,692),'NO WATER',font=f(MONO,24),fill=GREEN+(int(255*clamp((t-16.62)/0.15)),))
    status_row(d,790,'LIVER STRAIN',17.28,17.54,'NONE',GREEN)
    if t>=18.24: d.text((X0+330,802),'NOT AN ORAL',font=f(MONO,24),fill=GREEN+(int(255*clamp((t-18.24)/0.15)),))
    status_row(d,900,'SHBG',19.44,20.14,'BOUND HARD',VGOLD)
    if t>=20.88:
        a=int(255*clamp((t-20.88)/0.15)); d.text((X0,1020),'FREE TESTOSTERONE',font=f(BAR,40),fill=CREAM+(a,))
        meter(d,X0,1076,XR-44,lerp(0.40,0.72,ease_io((t-21.18)/0.6)),VGOLD,26)
        if t>=21.78: tri(d,XR-30,1072,28,True,VGOLD+(255,))
        if t>=22.30: d.text((X0,1116),'ALREADY IN YOUR SYSTEM',font=f(MONO,22),fill=MUTED+(int(255*clamp((t-22.30)/0.15)),))
# ---- EVIDENCE 02: the catch (weak signal per mg vs stronger compounds, premium price) ----
def evB(d,t):
    d.text((X0,566),'SIGNAL',font=f(MONO,24),fill=LABEL)
    rows=[('PRIMO',26.02,0.30,VGOLD),('STRONGER COMPOUNDS',30.30,0.86,CREAM)]
    for i,(lab,tt,v,col) in enumerate(rows):
        if t<tt-0.05: continue
        a=int(255*clamp((t-tt+0.05)/0.15)); y=610+i*120
        d.text((X0,y),lab,font=f(BAR,42),fill=col+(a,))
        g=ease_io((t-tt)/0.45); d.rectangle([X0,y+56,X0+(XR-X0)*v*g,y+92],fill=col+(int(a*0.95),))
        if GL and col==VGOLD: GL.rectangle([X0,y+56,X0+(XR-X0)*v*g,y+92],outline=VGOLD+(150,),width=6)
    if t>=26.20: d.text((X0+(XR-X0)*0.30+20,668),'WEAK PER MG',font=f(MONO,24),fill=VGOLD+(int(255*clamp((t-26.20)/0.15)),))
    if t>=27.48:
        a=int(255*clamp((t-27.48)/0.15)); d.text((X0,866),'MG NEEDED',font=f(BAR,40),fill=CREAM+(a,))
        meter(d,X0+300,878,XR-44,lerp(0.2,0.88,ease_io((t-27.64)/0.8)),RED,26)
        if t>=28.94: tri(d,XR-30,874,28,True,RED+(255,))
    if t>=32.04:
        a=int(255*clamp((t-32.04)/0.15)); d.text((X0,966),'COST',font=f(BAR,40),fill=CREAM+(a,))
        meter(d,X0+300,978,XR-44,lerp(0.2,0.92,ease_io((t-32.04)/0.5)),RED,26)
        if t>=32.54: tri(d,XR-30,974,28,True,RED+(255,))
    if t>=34.28:
        p=expo((t-34.28)/0.10); y=1160; x1=lerp(P[0],P[2],p)
        if GL: GL.rectangle([P[0]-4,y-8,x1+4,y+96],outline=RED+(255,),width=10)
        lit_bar(d,P[0],y,x1,y+88,RED); d.rectangle([P[0],y+84,x1,y+88],fill=(140,0,0))
        if p>0.6:
            fn=f(BEB,72); d.text((P[0]+40,y+8),'PREMIUM PRICE',font=fn,fill=(255,255,255))
            d.text((P[0]+40+d.textlength('PREMIUM PRICE',font=fn)+26,y+30),'MILD SIGNAL',font=f(MONO,28),fill=(255,255,255))
sfx(13.70,'tick',g=-28); sfx(15.60,'tick',g=-29); sfx(17.54,'tick',g=-29); sfx(20.14,'tick',g=-27); sfx(21.18,'scan',d=0.6,g=-33)
sfx(26.02,'scan',d=0.45,g=-32); sfx(30.30,'scan',d=0.45,g=-32); sfx(28.94,'tick',g=-27); sfx(32.54,'tick',g=-26); sfx(34.38,'impact',g=-13)

# ---- WAY 01: no aromatization -> E2 drops below range -> joints, libido, mood -> blamed on the wrong compound ----
def evC(d,t):
    x0,x1=X0,XR; y=640
    a=int(255*clamp((t-37.10)/0.15))
    d.text((x0,566),'ESTRADIOL',font=f(BAR,44),fill=CREAM+(a,))
    d.rectangle([x0,y,x1,y+60],outline=MUTED+(int(a*0.5),),width=2)
    lo,hi=x0+(x1-x0)*0.35,x0+(x1-x0)*0.70
    d.rectangle([lo,y+4,hi,y+56],fill=(30,255,110,int(40*a/255)),outline=GREEN+(int(a*0.8),),width=2)
    d.text((lo,y+70),'TARGET RANGE',font=f(MONO,22),fill=GREEN+(a,))
    u=lerp(0.52,0.10,ease_io((t-39.44)/2.4)); mx=x0+(x1-x0)*u
    col=RED if u<0.35 else CREAM
    d.polygon([(mx-16,y-24),(mx+16,y-24),(mx,y-2)],fill=col+(a,)); d.line([(mx,y),(mx,y+60)],fill=col+(a,),width=4)
    if GL and u<0.35: GL.line([(mx,y),(mx,y+60)],fill=RED+(200,),width=10)
    if t>=41.96: red_tag(d,mx+20,y+70,'TOO LOW',26)
    x=x0; yc=820
    if t>=42.40: d.text((x0,yc-40),'SYMPTOMS',font=f(MONO,22),fill=LABEL)
    for lab,tt in [('JOINTS',42.56),('LIBIDO',43.24),('MOOD',44.20)]:
        q=expo((t-tt)/0.14)
        if q<=0: continue
        fn=f(BAR,40); tw=d.textlength(lab,font=fn); aa=int(255*q)
        d.rectangle([x,yc,x+tw+40,yc+60],fill=CHIP+(int(240*q),),outline=RED+(aa,),width=2); d.text((x+20,yc+6),lab,font=fn,fill=(255,150,140,aa)); x+=tw+60
    if t>=46.00:
        q=expo((t-46.00)/0.14); aa=int(255*q); y2=960
        d.text((x0,y2),'BLAMED ON',font=f(MONO,24),fill=LABEL+(aa,)); s='ANOTHER COMPOUND'; fn=f(BAR,42); d.text((x0+180,y2-8),s,font=fn,fill=MUTED+(aa,))
        w=d.textlength(s,font=fn); d.line([(x0+170,y2+16),(x0+190+w,y2+16)],fill=RED+(aa,),width=5)
        if t>=46.42: d.text((x0,y2+70),'ACTUAL CAUSE',font=f(MONO,24),fill=LABEL+(aa,)); gold_tag(d,x0+220,y2+60,'LOW E2',30)
sfx(39.44,'scan',d=1.4,g=-33); sfx(41.96,'tick',g=-24); sfx(42.56,'tick',g=-31); sfx(43.24,'tick',g=-31); sfx(44.20,'tick',g=-31); sfx(46.42,'thud',w=1.2,g=-18)

# ---- WAY 02: counterfeit risk (label says Primo; contents unknown; test + AI found) ----
def vial_xray(d,cx,cy,a,unknown):
    C=CYAN+(a,)
    d.rectangle([cx-50,cy-210,cx+50,cy-170],outline=C,width=5); d.rounded_rectangle([cx-90,cy-170,cx+90,cy+170],radius=26,outline=C,width=6)
    if GL: GL.rounded_rectangle([cx-90,cy-170,cx+90,cy+170],radius=26,outline=CYAN+(int(a*0.6),),width=12)
    d.rectangle([cx-84,cy-60,cx+84,cy+40],fill=(250,249,246,int(a*0.9)))
    d.text((cx-d.textlength('PRIMOBOLAN',font=f(BEB,40))/2,cy-52),'PRIMOBOLAN',font=f(BEB,40),fill=(12,14,20,a))
    d.text((cx-d.textlength('100 MG/ML',font=f(MONO,20))/2,cy-6),'100 MG/ML',font=f(MONO,20),fill=(80,80,90,a))
    if unknown>0:
        fn=f(BEB,120); s='?'; d.text((cx-d.textlength(s,font=fn)/2,cy+44),s,font=fn,fill=CYAN+(int(a*unknown),))
def evD(d,t):
    cx,cy=280,860; a=int(255*clamp((t-51.10)/0.15))
    unk=clamp((t-53.68)/0.2)*(1-clamp((t-59.30)/0.2))
    vial_xray(d,cx,cy,a,unk)
    if t>=51.92: red_tag(d,XR,570,'ONE OF THE MOST FAKED',26,right=True)
    if t>=50.56 or t>=51.10: d.text((500,640),'SOURCE TRUST · 10 YRS',font=f(MONO,24),fill=MUTED+(a,))
    if t>=57.84: d.text((500,690),'CONTENTS UNVERIFIED',font=f(MONO,24),fill=CYAN+(int(255*clamp((t-57.84)/0.15)),))
    if t>=59.30:
        d.text((500,760),'ASSAY',font=f(MONO,24),fill=LABEL)
    rows=[('TESTOSTERONE',59.30,'DETECTED',RED),('AROMATASE INHIBITOR',60.68,'DETECTED',RED),('METHENOLONE',62.02,'NOT FOUND',RED)]
    for i,(lab,tt,res,col) in enumerate(rows):
        q=expo((t-tt)/0.14)
        if q<=0: continue
        y=800+i*80; aa=int(255*q); d.text((500,y),lab,font=f(BAR,36),fill=CREAM+(aa,))
        d.text((XR-d.textlength(res,font=f(MONOB,24)),y+44),res,font=f(MONOB,24),fill=col+(aa,))
        d.line([(500,y+76),(XR,y+76)],fill=MUTED+(50,),width=2)
    if t>=62.38:
        p=expo((t-62.38)/0.10); y=1160; x1=lerp(P[0],P[2],p)
        if GL: GL.rectangle([P[0]-4,y-8,x1+4,y+96],outline=RED+(255,),width=10)
        lit_bar(d,P[0],y,x1,y+88,RED); d.rectangle([P[0],y+84,x1,y+88],fill=(140,0,0))
        if p>0.6: d.text((P[0]+40,y+8),'LABEL ≠ CONTENTS',font=f(BEB,72),fill=(255,255,255))
sfx(51.92,'tick',g=-25); sfx(53.68,'scan',d=0.5,g=-32); sfx(59.30,'tick',g=-26); sfx(60.68,'tick',g=-26); sfx(62.02,'tick',g=-25); sfx(62.48,'impact',g=-13)

# ---- VERDICT: worth it only if every box is checked ----
CHECK=[('TRAINING HARD',66.92),('EATING CORRECTLY',68.46),('STRONG FOUNDATION',69.86),('WANT THE CLEAN DRY LOOK',70.92),('OK WITH THE COST',73.32),('PATIENT · NOT A FAST TRANSFORMATION',74.38)]
def evE(d,t):
    q=expo((t-65.88)/0.14)
    if q>0: gold_tag(d,X0,560,'YES · IF',28)
    for i,(lab,tt) in enumerate(CHECK):
        q=expo((t-tt)/0.14)
        if q<=0: continue
        y=640+i*82; aa=int(255*q); dx=-24*(1-q)
        d.rectangle([X0+dx,y+4,X0+dx+40,y+44],outline=GREEN+(aa,),width=3); check(d,X0+dx+8,y+12,GREEN+(aa,),5,1.0)
        if GL and t<tt+0.4: check(GL,X0+dx+8,y+12,GREEN+(aa,),10,1.0)
        fn=f(BAR,40); s=lab
        if d.textlength(s,font=fn)>800: fn=f(BAR,34)
        d.text((X0+64+dx,y+2),s,font=fn,fill=CREAM+(aa,))
    if t>=77.68:
        p=expo((t-77.68)/0.10); y=1160; x1=lerp(P[0],P[2],p)
        if GL: GL.rectangle([P[0]-4,y-8,x1+4,y+96],outline=VGOLD+(255,),width=10)
        lit_bar(d,P[0],y,x1,y+88,VGOLD); d.rectangle([P[0],y+84,x1,y+88],fill=(150,110,0))
        if p>0.6:
            fn=f(BEB,72); d.text((P[0]+40,y+8),'WORTH IT',font=fn,fill=DEEP)
            d.text((P[0]+40+d.textlength('WORTH IT',font=fn)+26,y+30),'IF EVERY BOX IS CHECKED',font=f(MONOB,26),fill=DEEP)
for _,tt in CHECK: sfx(tt,'tick',g=-30)
sfx(65.88,'tick',g=-27); sfx(77.78,'thud',w=1.6,g=-14)
CONTENT={0:[(11.48,evA),(24.08,evB)],1:[(37.02,evC)],2:[(51.04,evD)],3:[(63.48,evE)]}
SHAKES=[34.38,62.48]


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
HOOK_LINES=[[('PRIMO',VGOLD),(' holy grail',CREAM)],[('both camps got it wrong',CREAM)]]
HOOK_END=5.12; HOOK_FADE=0.15; HOOK_Y=262
THO=(HOOK_END,HOOK_END+HOOK_FADE)
_mid=DUR/2; BAND_OUT=min(CUTS,key=lambda c:abs(c-_mid))      # exits on the jump cut nearest the midpoint
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
        for s,c in [('PRIMO',VGOLD),(' holy grail or placebo',CREAM)]: d.text((x,y),s,font=fn,fill=c+(a,)); x+=d.textlength(s,font=fn)
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
END=78.70; PILL=84.52; FREE=87.78; VS=88.98; HEAR=91.30
sfx(END,'scan',d=0.30,g=-29); sfx(80.18,'tick',g=-30); sfx(PILL-0.05,'whoosh',d=0.22,g=-27); sfx(PILL+0.10,'thud',w=1.6,g=-14); sfx(FREE,'tick',g=-27); sfx(VS,'thud',w=1.1,g=-19)
def end_card(im,t):
    if t<END: return
    a=ease_io((t-END)/0.30); im.alpha_composite(scene_bg(a))
    q=expo((t-END-0.15)/0.25)
    if q<=0: return
    lg=logo().copy(); lg.putalpha(lg.split()[3].point(lambda v:int(v*q))); im.alpha_composite(lg,(540-120,214))
    L,d=newL(); A=int(255*q)
    fn=f(BAR,40); s='COACH AGZ'; w=tracked_w(d,s,fn,10); tracked(d,(540-w/2,466),s,fn,GOLD+(A,),10)
    fn=f(MONO,28); s='@coach.agz'; d.text((540-d.textlength(s,font=fn)/2,522),s,font=fn,fill=MUTED+(A,))
    kq=expo((t-79.96)/0.2)
    if kq>0: fn=f(BAR,36); s='THE FULL'; w=tracked_w(d,s,fn,8); tracked(d,(540-w/2,610),s,fn,GOLD+(int(255*kq),),8)
    for s,tt,y,sz,col in [('PRIMO',80.96,652,130,VGOLD),('FRAMEWORK',80.18,776,96,CREAM)]:
        hq=expo((t-tt)/0.16)
        if hq<=0: continue
        fn=f(BEB,sz); d.text((540-d.textlength(s,font=fn)/2,y+12*(1-hq)),s,font=fn,fill=col+(int(255*hq),))
    oq=expo((t-82.80)/0.16)
    if oq>0: fn=f(MONOB,28); s='WHAT TO LOOK FOR IN YOUR BLOODS · HOW TO OPTIMIZE'; d.text((540-d.textlength(s,font=fn)/2,884),s,font=fn,fill=MUTED+(int(255*oq),))
    im.alpha_composite(L); L,d=newL()
    pq=expo((t-PILL)/0.20)
    if pq>0:
        fn=f(MONOB,58); s='COMMENT "PRIMO"'; tw=d.textlength(s,font=fn); bw=tw+80; x0=540-bw/2; y0=940+lerp(-40,0,pq)
        if GL and t<PILL+0.6: GL.rectangle([x0,y0,x0+bw,y0+120],outline=VGOLD+(int(220*(1-(t-PILL)/0.6)),),width=10)
        lit_bar(d,x0,y0,x0+bw,y0+120,VGOLD,int(255*min(1,pq*1.5)))
        im.alpha_composite(L); L,d=newL()
        tq=clamp((t-PILL-0.08)/0.12)
        if tq>0: d.text((540-tw/2,y0+24),s,font=fn,fill=DEEP+(int(255*tq),))
    fq=expo((t-FREE)/0.14)
    if fq>0:
        fn=f(MONOB,36); s='SENT TO YOU · '; s2='FREE'; tw=d.textlength(s+s2,font=fn); x=540-tw/2
        d.text((x,1080),s,font=fn,fill=CREAM+(int(255*fq),)); d.text((x+d.textlength(s,font=fn),1080),s2,font=fn,fill=VGOLD+(int(255*fq),))
    vq=expo((t-VS)/0.16)
    if vq>0:
        fn=f(BEB,64); s1='PRIMO'; s2=' VS '; s3='MAST'; tw=d.textlength(s1+s2+s3,font=fn); x=540-tw/2; y=1136
        d.text((x,y),s1,font=fn,fill=VGOLD+(int(255*vq),)); x+=d.textlength(s1,font=fn); d.text((x,y),s2,font=fn,fill=MUTED+(int(255*vq),)); x+=d.textlength(s2,font=fn); d.text((x,y),s3,font=fn,fill=CREAM+(int(255*vq),))
        if t>=HEAR: fs=f(MONO,24); s='TELL ME IN THE COMMENTS'; d.text((540-d.textlength(s,font=fs)/2,1208),s,font=fs,fill=CREAM+(int(255*clamp((t-HEAR)/0.15)),))
    fn=f(MONO,20); d.text((540-d.textlength(DISC,font=fn)/2,1250),DISC,font=fn,fill=LABEL+(A,))
    im.alpha_composite(L)


# ---------------- frame ----------------
SUBJECT_T=0.40      # visual hook: first punch-in lands on the spoken subject word "Primobolan"
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
