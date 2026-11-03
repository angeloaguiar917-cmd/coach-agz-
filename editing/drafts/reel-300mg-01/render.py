# Reel: "300MG" (more mg isn't more growth): full edit, 720p30 preview.
# Built on the saved setup: test-06 look + full-test-02 workflow (dead air trimmed, misspeak cut, 108% punch-in per jump cut,
# captions from the trimmed audio). Usage: python render.py <scratch> [--events|--groups|--still t..|--range n0 n1 out.mp4]
import json, subprocess, sys, math, re
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
S=sys.argv[1]; F=S+'/fonts/'; T=S+'/r2/work/'
W,H=1080,1920; FPS=30; N=3572; DUR=N/FPS
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
FIX={11:'F*CK',90:'F*CKING',347:'F*CKING',104:'APOB,',217:'CABER',268:'CHECK-INS',300:'WEEKS,',311:'FELLAS,',310:'TERMS,',
     336:'RUNNING',337:'ANABOLICS',369:'SAID,',385:'LIST,',5:'300',6:'MILLIGRAMS'}
for i,w in FIX.items(): words[i]['w']=w
words[337]['e']=words[339]['e']; words[337]['s']=max(words[337]['s'],words[336]['s']+0.14)
words[268]['e']=words[269]['e']
for i in (339,338,269): del words[i]                      # "in a box" -> ANABOLICS ; "check" "-ins" -> CHECK-INS
k=[i for i,w in enumerate(words) if w['w']=='two' and 86<w['s']<87][0]   # heard "two [to] three": transcriber dropped "to"
words.insert(k+1,{'w':'TO','s':round(words[k]['s']+0.12,3),'e':round(words[k+1]['s']-0.02,3)})
for w in words: w['w']=w['w'].upper()
CAP_Y=1505; CAP_MAX=900
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
            weak=disp(w['w']) in WEAK and len(cur)>=2 and disp(words[cur[-1]]['w']) not in ('POPS','CRACK')
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
PANELS=[dict(o=6.22,c=12.95,hdr='CASE 01',st=[(6.22,'PLATEAU RESPONSE')]),
        dict(o=16.86,c=38.30,hdr='STEP 01 / 04',st=[(16.86,'FOUNDATION'),(27.80,'BLOODWORK')],hdr2={27.80:'STEP 02 / 04'}),
        dict(o=45.00,c=54.00,hdr='STEP 03 / 04',st=[(45.00,'STACK AUDIT')]),
        dict(o=55.40,c=69.95,hdr='STEP 04 / 04',st=[(55.40,'CONTINGENCY DRAWER')]),
        dict(o=80.90,c=88.95,hdr='STEP 04 / 04',st=[(80.90,'CONTINGENCY DRAWER'),(84.88,'EARLY CATCH')])]
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

# -- CASE 01: plateau chart (dose climbs, the curve doesn't care) --
def evA(d,t):
    cx0,cx1,cy0,cy1=150,940,600,930
    a=int(255*clamp((t-6.30)/0.15))
    d.text((cx0,560),'LEAN MASS',font=f(MONO,22),fill=LABEL+(a,))
    d.line([(cx0,cy0),(cx0,cy1),(cx1,cy1)],fill=MUTED+(a,),width=2)
    for k in range(5):
        x=cx0+(cx1-cx0)*k/4; d.line([(x,cy1),(x,cy1+10)],fill=MUTED+(a,),width=2)
        lab=f'WK {k*4}'; d.text((x-d.textlength(lab,font=f(MONO,22))/2,cy1+16),lab,font=f(MONO,22),fill=LABEL+(a,))
    g=lambda u: 0.78*(1-math.exp(-6*u))
    pt=lambda u: (cx0+(cx1-cx0)*u, cy1-(cy1-cy0)*g(min(u,0.6))-(cy1-cy0)*0.02*max(0,u-0.6))
    q=ease_io((t-6.40)/0.90)
    if q>0:
        pts=[pt(0.6*k/60*q) for k in range(61)]; d.line(pts,fill=CREAM+(255,),width=5,joint='curve')
        if GL: GL.line(pts,fill=CREAM+(110,),width=8)
    if t>=7.24:
        x0,y0=pt(0.36); x1,y1=pt(0.6); flag=(x0-10,y1-40,x1+10,y1+30)
        brackets(d,*flag,VGOLD+(255,),26,6)
        if GL: brackets(GL,*flag,VGOLD+(255,),26,10)
        if t>7.31: gold_tag(d,flag[0],flag[1]-64,'PLATEAU',28)
    # dose lane
    ly=1080; a2=int(255*clamp((t-6.50)/0.15))
    d.text((cx0,ly-6),'DOSE · MG / WK',font=f(MONO,22),fill=LABEL+(a2,))
    base=ly+110; sc=0.13
    if q>0:
        xe=cx0+(cx1-cx0)*0.6*q; d.rectangle([cx0,base-300*sc,xe,base],fill=VGOLD+(int(200*q),))
        if q>0.7: d.text((cx0+12,base-300*sc-34),'300',font=f(MONO,24),fill=VGOLD+(255,))
    for mg,tt in [(500,8.24),(600,8.70)]:
        s=expo((t-tt)/0.16)
        if s<=0: continue
        xs=cx0+(cx1-cx0)*0.6; xe=xs+(cx1-cx0)*0.4*ease_io((t-8.24)/1.0)
        h=lerp(300,mg,s)*sc
        if mg==600 or t<8.70:
            d.rectangle([xs,base-h,max(xs+4,xe),base],fill=RED+(230,))
            if GL: GL.rectangle([xs,base-h,max(xs+4,xe),base],outline=RED+(200,),width=6)
        d.text((xs+12,base-mg*sc-34),str(mg),font=f(MONO,24),fill=RED+(int(255*s),)) if mg==600 or t<8.70 else None
    # growth after the dose step: dashed, still flat
    q2=ease_io((t-8.90)/0.70)
    if q2>0:
        pts=[pt(0.6+0.4*k/40*q2) for k in range(41)]; dashed(d,pts,CREAM+(170,),4)
        if q2>=1: s='CAUSE NOT ADDRESSED'; fn=f(MONO,24); x,y=pt(1.0); d.text((cx1-d.textlength(s,font=fn),y-46),s,font=fn,fill=MUTED+(int(255*clamp((t-9.6)/0.2)),))
    if t>=11.36:
        p=expo((t-11.36)/0.10); y=1160; x1=lerp(P[0],P[2],p)
        if GL: GL.rectangle([P[0]-4,y-8,x1+4,y+96],outline=RED+(255,),width=10)
        lit_bar(d,P[0],y,x1,y+88,RED); d.rectangle([P[0],y+84,x1,y+88],fill=(140,0,0))
        if p>0.6:
            fn=f(BEB,72); d.text((P[0]+40,y+8),'IMPATIENCE',font=fn,fill=(255,255,255))
            d.text((P[0]+40+d.textlength('IMPATIENCE',font=fn)+26,y+30),'NOT OPTIMIZATION',font=f(MONO,28),fill=(255,255,255))
sfx(7.24,'tick',g=-28); sfx(8.24,'tick',g=-27); sfx(8.70,'tick',g=-25); sfx(11.46,'impact',g=-13)

# -- STEP 01: foundation -> gear amplifies the base, can't replace it --
TILES=[('OVERLOAD',19.06),('CALORIES',20.56),('PROTEIN',21.30),('RECOVERY',21.88)]
def evB(d,t):
    x=X0
    for lab,tt in [('TRAINING',17.70),('NUTRITION',18.30)]:
        q=expo((t-tt)/0.14)
        if q<=0: continue
        fn=f(BAR,38); tw=d.textlength(lab,font=fn); a=int(255*q)
        d.rectangle([x,566,x+tw+36,622],outline=VGOLD+(a,),width=3); d.text((x+18,570),lab,font=fn,fill=VGOLD+(a,)); x+=tw+56
    d.text((X0,652),'BASE',font=f(MONO,22),fill=LABEL)
    tw_=(XR-X0-3*16)/4; gone=0
    for i,(lab,tt) in enumerate(TILES):
        q=expo((t-tt)/0.16)
        if q<=0: continue
        rq=expo((t-25.54-i*0.08)/0.12)          # "doesn't replace": pull the base out tile by tile
        gone+=rq
        x0=X0+i*(tw_+16); y0=690+30*(1-q); a=int(255*q*(1-0.75*rq))
        d.rectangle([x0,y0,x0+tw_,y0+110],fill=INNER+(a,),outline=(58,54,48,a),width=2); d.rectangle([x0,y0,x0+tw_,y0+5],fill=VGOLD+(a,))
        fn=f(BAR,36); d.text((x0+(tw_-d.textlength(lab,font=fn))/2,y0+36),lab,font=fn,fill=CREAM+(a,))
        if rq>0: d.line([(x0+14,y0+55),(x0+14+(tw_-28)*rq,y0+55)],fill=RED+(255,),width=5)
    n=sum(1 for _,tt in TILES if t>=tt+0.1)-gone
    y=880; a=int(255*clamp((t-19.0)/0.2))
    if a>0:
        d.text((X0,y-30),'OUTPUT',font=f(MONO,22),fill=LABEL+(a,))
        d.rectangle([X0,y,XR,y+64],outline=MUTED+(int(a*0.5),),width=2)
        bw=(XR-X0-8)*0.12*max(0,n); d.rectangle([X0+4,y+4,X0+4+bw,y+60],fill=(220,214,204,a))
        gq=ease_io((t-23.28)/0.45)
        if gq>0:
            ext=bw*0.9*gq; d.rectangle([X0+4+bw,y+4,X0+4+bw+ext,y+60],fill=VGOLD+(255,))
            if GL: GL.rectangle([X0+4+bw,y+4,X0+4+bw+ext,y+60],outline=VGOLD+(200,),width=6)
    q=expo((t-22.86)/0.16)
    if q>0:
        a=int(255*q); s='× GEAR'; fn=f(BEB,64); x=XR-d.textlength(s,font=fn)
        d.text((x,y-74+10*(1-q)),s,font=fn,fill=VGOLD+(a,))
        if t>23.6: d.text((X0,y+80),'AMPLIFIES WHAT’S THERE',font=f(MONO,24),fill=MUTED+(int(255*clamp((t-23.6)/0.2)*(1-clamp((t-25.5)/0.2))),))
    if t>=26.48:
        p=expo((t-26.48)/0.14); red_tag(d,X0,1000,'NO BASE · NOTHING TO AMPLIFY',32)
        fn=f(BEB,120); d.text((XR-d.textlength('0',font=fn),1080-20*(1-p)),'0',font=fn,fill=RED+(int(255*p),))
for _,tt in TILES: sfx(tt+0.05,'tick',g=-33)
sfx(23.28,'scan',d=0.45,g=-31); sfx(26.48,'thud',w=1.8,g=-15)

# -- STEP 02: lab requisition (what to order, not values) --
REQ=None; REQ_W,REQ_H=860,690
REQ_ROWS=[('Estradiol (sensitive)',30.26),('Hematocrit',31.10),('ApoB',31.72),('Liver panel · ALT / AST',32.34),('Kidney · creatinine / eGFR',32.84)]
def make_req():
    im=Image.new('RGB',(REQ_W,REQ_H),(250,249,246))
    a=np.array(im).astype(np.int16)+(np.random.default_rng(5).standard_normal((REQ_H,REQ_W,1))*2).astype(np.int16)
    im=Image.fromarray(np.clip(a,0,255).astype(np.uint8)); d=ImageDraw.Draw(im); INK=(12,14,20)
    d.rectangle([0,0,REQ_W-1,REQ_H-1],outline=(150,148,140),width=2)
    d.rectangle([0,0,REQ_W-1,96],fill=(210,10,20))
    d.text((30,14),'LAB REQUISITION',font=f(BEB,64),fill=(255,255,255))
    s='PANEL · ENHANCED ATHLETE'; d.text((REQ_W-30-d.textlength(s,font=f(MONO,22)),40),s,font=f(MONO,22),fill=(255,205,200))
    for i,(lab,_) in enumerate(REQ_ROWS):
        y=126+i*64; d.rectangle([30,y+8,62,y+40],outline=INK,width=3); d.text((86,y+2),lab,font=dm(34,600),fill=INK)
        d.line([(30,y+56),(REQ_W-30,y+56)],fill=(215,210,200),width=2)
    y=126+5*64+12; d.text((30,y),'Blood pressure · daily',font=dm(34,600),fill=INK)
    for k,dd in enumerate('MTWTFSS'):
        x=REQ_W-30-7*50+k*50; d.rectangle([x,y+4,x+40,y+44],outline=INK,width=2); d.text((x+13,y+48),dd,font=f(MONO,18),fill=(90,90,96))
    y=REQ_H-110; d.line([(30,y-16),(REQ_W-30,y-16)],fill=INK,width=2)
    d.text((30,y+10),'Dose adjustment:',font=dm(34,700),fill=INK); d.line([(330,y+52),(REQ_W-30,y+52)],fill=(120,118,112),width=2)
    return im.convert('RGBA')
def evC_img(lay,t):
    global REQ
    if REQ is None: REQ=make_req()
    ox,oy=110,550; lay.alpha_composite(REQ,(ox,oy)); d=ImageDraw.Draw(lay,'RGBA'); INKC=(20,40,120,255)
    for i,(lab,tt) in enumerate(REQ_ROWS):
        q=clamp((t-tt)/0.12)
        if q<=0: continue
        y=oy+126+i*64; x=ox+30
        pts=[(x+4,y+24),(x+14,y+36),(x+38,y+2)]; k=q*2
        d.line(pts[:2] if k<1 else pts,fill=INKC,width=6)
        if t<tt+0.5 and GL: GL.rectangle([ox+20,y-2,ox+REQ_W-20,y+52],outline=VGOLD+(int(200*(1-(t-tt)/0.5)),),width=6)
    y=oy+126+5*64+12
    for k in range(7):
        tt=33.94+k*0.08
        if t<tt: break
        x=ox+REQ_W-30-7*50+k*50; d.line([(x+6,y+24),(x+15,y+35),(x+34,y+10)],fill=INKC,width=5)
    if t>=37.38:
        y=oy+REQ_H-110; box=(ox+320,y+6,ox+REQ_W-24,y+62); flag_box(d,box,None,37.38,t)
        if t>37.45: red_tag(d,ox+REQ_W-40,y+11,'HOLD · REVIEW FIRST',28,right=True)
for _,tt in REQ_ROWS: sfx(tt,'tick',g=-33)
sfx(33.94,'scan',d=0.6,g=-33); sfx(37.38,'tick',g=-24)

# -- STEP 03: stack audit (another compound: growth barely moves, risk stacks) --
RISK=[('CARDIOVASCULAR',49.34,0.62),('ENDOCRINE',50.46,0.55),('SIDE EFFECTS',52.14,0.70)]
def evD(d,t):
    x=X0; y=566
    for lab,tt,col in [('TESTOSTERONE',45.0,CREAM),('+ COMPOUND 2',45.36,VGOLD)]:
        q=expo((t-tt)/0.16)
        if q<=0: continue
        fn=f(BAR,40); tw=d.textlength(lab,font=fn); a=int(255*q); xx=x+40*(1-q)
        d.rectangle([xx,y,xx+tw+40,y+60],outline=col+(a,),width=3); d.text((xx+20,y+6),lab,font=fn,fill=col+(a,)); x+=tw+60
    y=700; d.text((X0,y),'GROWTH',font=f(BEB,64),fill=CREAM)
    v=lerp(0.46,0.50,ease_io((t-47.54)/0.4)); meter(d,420,y+20,XR,v,VGOLD,30)
    if t>=46.92:
        s='NOT AUTOMATIC'; fn=f(MONO,26); d.text((XR-d.textlength(s,font=fn),y+64),s,font=fn,fill=VGOLD+(int(255*clamp((t-46.92)/0.15)),))
    y=850; d.text((X0,y),'RISK',font=f(BEB,64),fill=CREAM)
    for i,(lab,tt,v1) in enumerate(RISK):
        q=ease_io((t-tt)/0.35)
        if t<tt: continue
        yy=y+10+i*72; a=int(255*clamp((t-tt)/0.12))
        d.text((420,yy),lab,font=f(MONO,26),fill=(255,150,140,a))
        bx=700; d.rectangle([bx,yy+2,XR,yy+30],outline=MUTED+(int(a*0.5),),width=2)
        lit_bar(d,bx+3,yy+5,bx+3+(XR-bx-6)*v1*q,yy+27,RED)
        if GL: GL.rectangle([bx+3,yy+5,bx+3+(XR-bx-6)*v1*q,yy+27],outline=RED+(160,),width=5)
    if t>=53.32:
        p=expo((t-53.32)/0.10); y=1160; x1=lerp(P[0],P[2],p)
        if GL: GL.rectangle([P[0]-4,y-8,x1+4,y+96],outline=RED+(255,),width=10)
        lit_bar(d,P[0],y,x1,y+88,RED); d.rectangle([P[0],y+84,x1,y+88],fill=(140,0,0))
        if p>0.6:
            fn=f(BEB,72); d.text((P[0]+40,y+8),'RISK ADDED',font=fn,fill=(255,255,255))
            d.text((P[0]+40+d.textlength('RISK ADDED',font=fn)+26,y+30),'NO GROWTH RETURN',font=f(MONO,28),fill=(255,255,255))
sfx(45.36,'tick',g=-28)
for _,tt,_ in RISK: sfx(tt,'tick',g=-26)
sfx(53.42,'impact',g=-13)

# -- STEP 04: contingency drawer --
DRAWER=[('AROMATASE INHIBITOR',61.88,62.44),('CABERGOLINE',64.50,65.14),('SUPPORT COMPOUND',66.36,67.76)]
def vial(d,x,y,col,a):
    d.rectangle([x+8,y,x+32,y+14],outline=col+(a,),width=3); d.rounded_rectangle([x,y+14,x+40,y+76],radius=8,outline=col+(a,),width=3)
    d.rectangle([x+6,y+40,x+34,y+66],fill=col+(int(a*0.35),))
def evE(d,t,callback=False):
    a0=int(255*clamp((t-57.30)/0.2)) if not callback else 255
    d.text((X0,566),'IF SOMETHING GOES WRONG',font=f(MONO,26),fill=MUTED+(a0,))
    q=expo((t-60.16)/0.14) if not callback else 1
    if q>0:
        y=620; d.text((X0,y),'WARNING SIGNS',font=f(BAR,44),fill=CREAM+(int(255*q),)); green_tag(d,XR,y+8,'KNOWN',int(255*q))
        d.line([(X0,y+70),(XR,y+70)],fill=MUTED+(70,),width=2)
    for i,(lab,t0,t1) in enumerate(DRAWER):
        q=expo((t-t0)/0.16) if not callback else 1
        if q<=0: continue
        y=730+i*130; a=int(255*q); dx=-30*(1-q)
        vial(d,X0+dx,y,CREAM,a); d.text((X0+70+dx,y+16),lab,font=f(BAR,46),fill=CREAM+(a,))
        if t>=t1 or callback: green_tag(d,XR,y+24,'ON HAND',a)
        if i==2 and (t>=69.12 or callback):
            s=expo((t-69.12)/0.14) if not callback else 1
            fn=f(MONOB,24); w=d.textlength('SEALED',font=fn); x=XR-260-w
            d.rectangle([x,y+70,x+w+24,y+104],fill=VGOLD+(int(255*s),)); d.text((x+12,y+73),'SEALED',font=fn,fill=DEEP+(int(255*s),))
        d.line([(X0,y+112),(XR,y+112)],fill=MUTED+(50,),width=2)
def evE2(d,t): evE(d,t,callback=True)
def evF(d,t):             # early catch: appears -> where it goes if missed -> caught early
    cx0,cx1,cy0,cy1=150,940,620,1060
    d.text((cx0,570),'SEVERITY',font=f(MONO,22),fill=LABEL)
    d.line([(cx0,cy0),(cx0,cy1),(cx1,cy1)],fill=MUTED,width=2)
    for k in range(4):
        x=cx0+(cx1-cx0)*k/3; d.line([(x,cy1),(x,cy1+10)],fill=MUTED,width=2)
        lab=f'WK {k}'; d.text((x-d.textlength(lab,font=f(MONO,22))/2,cy1+16),lab,font=f(MONO,22),fill=LABEL)
    pt=lambda u:(cx0+(cx1-cx0)*u, cy1-(cy1-cy0)*(0.10+0.80*u**1.8))
    q=expo((t-85.52)/0.16)
    if q>0:
        x,y=pt(0.12); r=14*q; d.ellipse([x-r,y-r,x+r,y+r],fill=RED+(255,))
        if GL: GL.ellipse([x-r-6,y-r-6,x+r+6,y+r+6],fill=RED+(200,))
        d.text((x+60,y-56),'SIDE EFFECT APPEARS',font=f(MONO,24),fill=(255,150,140,int(255*q)))
    pq=ease_io((t-86.42)/0.70); fade=1-0.65*clamp((t-87.94)/0.3)
    if pq>0:
        pts=[pt(0.12+0.88*k/50*pq) for k in range(51)]; dashed(d,pts,RED+(int(220*fade),),5)
        if pq>=1: x,y=pt(1.0); s='IF MISSED'; d.text((x-d.textlength(s,font=f(MONO,24)),y-44),s,font=f(MONO,24),fill=RED+(int(255*fade),))
    if t>=87.94:
        x,y=pt(0.12); box=(x-34,y-34,x+34,y+34); brackets(d,*box,VGOLD+(255,),20,6)
        if GL: brackets(GL,*box,VGOLD+(255,),20,10)
        if t>88.0: gold_tag(d,x+50,y-12,'CAUGHT EARLY',30)
CONTENT={0:[(6.22,evA)],1:[(16.86,evB),(27.80,'REQ')],2:[(45.00,evD)],3:[(55.40,evE)],4:[(80.90,evE2),(84.88,evF)]}
for _,t0,t1 in DRAWER: sfx(t0,'tick',g=-29); sfx(t1,'tick',g=-33)
sfx(60.16,'tick',g=-31); sfx(69.12,'tick',g=-27); sfx(85.52,'tick',g=-25); sfx(86.42,'scan',d=0.70,g=-32); sfx(87.94,'thud',w=1.3,g=-16)
SHAKES=[11.46,53.42]

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
            if fn_=='REQ': evC_img(l,t)
            else: fn_(ImageDraw.Draw(l,'RGBA'),t)
            return l
        ys=None; cur=render_stage(si)
        if si>0 and t<stages[si][0]+0.30:
            wq=ease_io((t-stages[si][0])/0.30); ys=int(lerp(y0+70,y1,wq))
            prev=render_stage(si-1); m=Image.new('L',(W,H),0); ImageDraw.Draw(m).rectangle([0,0,W,ys],fill=255)
            cur=Image.composite(cur,prev,m)
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

# ---- hook: dose stat climbs 300 -> 500 -> 600, headline lands, hands off into the pinned title ----
TK=0.20; TS=0.88; T500=4.00; T600=4.48; TL2=5.42; THO=(5.92,6.24)
sfx(TK,'tick',g=-30); sfx(TS,'thud',w=1.0,g=-19); sfx(T500,'tick',g=-24); sfx(T600,'thud',w=1.2,g=-18); sfx(TL2,'thud',w=1.4,g=-16); sfx(THO[0],'whoosh',d=0.30,g=-28)
PIN_WIN=[(THO[0],89.00),(98.95,108.25)]          # pinned title hides for the full-screen recap and the end card
def pin_vis(t):
    v=0
    for i,(a,b_) in enumerate(PIN_WIN):
        if t<a: continue
        fin=1 if i==0 else clamp((t-a)/0.25); fout=clamp((b_+0.25-t)/0.25); v=max(v,fin*fout)
    return ease_io(v)
def headline(d,x,y,fn,a):
    parts=[('MORE MG ',CREAM),('≠',RED),(' MORE GROWTH',CREAM)]
    for s,c in parts: d.text((x,y),s,font=fn,fill=c+(a,)); x+=d.textlength(s,font=fn)
    return x
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
        lab='TESTOSTERONE' if h>0.5 else 'TESTOSTERONE · WEEKLY DOSE'
        fn=f(BAR,lerp(38,30,h)); n=int(len(lab)*clamp((t-TK-0.12)/0.30)) if h<=0.5 else len(lab)
        tracked(d,(130,ky+lerp(0,3,h)),lab[:n],fn,GOLD,lerp(9,7,h))
    if h>0:
        a=int(255*h); fn=f(MONO,24); s='@coach.agz'; d.text((1016-d.textlength(s,font=fn),ky+6),s,font=fn,fill=GOLD+(a,))
        d.text((64,352+ty),DISC,font=f(MONO,18),fill=LABEL+(a,))
    # dose stat (title card only)
    qs=expo((t-TS)/0.16)
    if qs>0 and h<1:
        h1=clamp(h*3); a=int(255*qs*(1-h1))
        val,col=('300',VGOLD) if t<T500 else (('500',RED) if t<T600 else ('600',RED))
        tk=max(t-T500 if t>=T500 else -1, t-T600 if t>=T600 else -1); pop=1+0.06*math.exp(-tk*18) if tk>=0 else 1
        s=lerp(1.1,1,qs)*pop; fn=f(BEB,int(170*s)); y=268-40*h1+(1-s)*80
        L1,d1=newL(); d1.text((64,y),val,font=fn,fill=col+(a,)); x=64+d1.textlength(val,font=fn)+10
        d1.text((x,y+int(92*s)),'MG / WEEK',font=f(MONO,int(32*s)),fill=MUTED+(a,))
        if GL and val!='300' and tk<0.4: GL.text((64,y),val,font=fn,fill=RED+(int(160*(1-tk/0.4)),))
        L.alpha_composite(L1)
    q2=expo((t-TL2)/0.16)
    if q2>0:
        size=86; y=lerp(436,262,h)+ty+12*(1-q2); a=int(255*q2)
        headline(d,64,y,f(BEB,size),a)
    im.alpha_composite(L)

# ---- side chips over the wall (daily tracking, coaching cadence) ----
CHIPS=[dict(hdr='TRACK · DAILY',items=[('SIDE EFFECTS',70.54),('WATER RETENTION',71.66),('HOW YOU FEEL',73.26)],out=74.55),
       dict(hdr='COACHING',items=[('WEEKLY CHECK-IN',77.82),('DAILY COMMUNICATION',79.04)],out=80.25)]
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
RECAP=[('01','OPTIMIZE THE STIMULUS','TRAINING · NUTRITION · RECOVERY',90.24),
       ('02','UNDERSTAND YOUR BIOMARKERS','E2 · HCT · APOB · LIVER · KIDNEY · BP',91.64),
       ('03','EVALUATE THE EVIDENCE','SYNERGY, NOT JUST MORE',92.88),
       ('04','PREPARE FOR COMPLICATIONS','DRAWER STOCKED · TRACK DAILY',94.28)]
RC_IN=(89.05,89.35); RC_OUT=(98.80,99.05)
sfx(RC_IN[0],'scan',d=0.30,g=-29); sfx(89.36,'tick',g=-30)
for i,(_,_,_,tt) in enumerate(RECAP): sfx(tt+0.12,'thud',w=0.9+0.2*i,g=-19 if i<3 else -16)
sfx(97.20,'tick',g=-29)
def recap(im,t):
    if t<RC_IN[0] or t>RC_OUT[1]: return
    a=ease_io((t-RC_IN[0])/(RC_IN[1]-RC_IN[0]))*(1-ease_io((t-RC_OUT[0])/(RC_OUT[1]-RC_OUT[0])))
    e=ease_io((t-RC_OUT[0])/(RC_OUT[1]-RC_OUT[0]))
    im.alpha_composite(scene_bg(a)); L,d=newL()
    kq=expo((t-89.36)/0.25); ae=int(255*(1-e))
    if kq>0:
        d.line([(64,250),(64+50*kq,250)],fill=GOLD+(ae,),width=4)
        lab='IN BASIC TERMS'; n=int(len(lab)*clamp((t-89.46)/0.3)); tracked(d,(130,232),lab[:n],f(BAR,36),GOLD+(ae,),8)
    hq=expo((t-89.58)/0.16)
    if hq>0:
        fn=f(BEB,140); y=280+10*(1-hq); ah=int(255*hq*(1-e)); d.text((64,y),'THE ',font=fn,fill=CREAM+(ah,))
        d.text((64+d.textlength('THE ',font=fn),y),'4 STEPS.',font=fn,fill=GOLD+(ah,))
    im.alpha_composite(L)
    SH,shd=newL(); L,d=newL()
    for i,(num,lab,sub,tt) in enumerate(RECAP):
        q=clamp((t-tt)/0.14)
        if q<=0: continue
        land=1-(1-q)**3; y=560+i*170-lerp(60,0,land)+e*(50+i*12)
        if q>=1:
            k=t-tt-0.14
            if k<0.3: y+=5*math.exp(-k*30)*math.sin(k*40)
        x0,x1=64,1016; ae=1-e; aa=int(255*min(1,q*2)*ae)
        shd.rectangle([x0+10,y+18,x1+10,y+150],fill=(0,0,0,int(150*land*ae)))
        pulse=math.exp(-max(0,t-97.20)*4)*(1 if (i==3 and t>=97.20) else 0)
        d.rectangle([x0,y,x1,y+146],fill=(25,28,35,aa),outline=(58,54,48,aa) if pulse<0.05 else VGOLD+(int(255*pulse*ae),),width=2 if pulse<0.05 else 4)
        d.rectangle([x0,y,x0+10,y+146],fill=GOLD+(aa,))
        d.text((x0+40,y+36),num,font=f(MONO,36),fill=GOLD+(aa,))
        fn=f(BEB,80); tw=d.textlength(lab,font=fn)
        if tw>800: fn=f(BEB,int(80*800/tw))
        d.text((x0+130,y+14),lab,font=fn,fill=CREAM+(aa,))
        d.text((x0+132,y+100),sub,font=f(MONO,24),fill=MUTED+(aa,))
    if SH.getbbox(): im.alpha_composite(SH.filter(ImageFilter.GaussianBlur(14)))
    im.alpha_composite(L)

END=108.40; PILL=113.62; FREE=116.76
sfx(END,'scan',d=0.30,g=-29); sfx(109.42,'tick',g=-30); sfx(PILL-0.05,'whoosh',d=0.22,g=-27); sfx(PILL+0.10,'thud',w=1.6,g=-14); sfx(FREE,'tick',g=-27)
def end_card(im,t):
    if t<END: return
    a=ease_io((t-END)/0.30); im.alpha_composite(scene_bg(a))
    q=expo((t-END-0.15)/0.25)
    if q<=0: return
    lg=logo().copy(); lg.putalpha(lg.split()[3].point(lambda v:int(v*q))); im.alpha_composite(lg,(540-120,290))
    L,d=newL(); A=int(255*q)
    fn=f(BAR,40); s='COACH AGZ'; w=tracked_w(d,s,fn,10); tracked(d,(540-w/2,556),s,fn,GOLD+(A,),10)
    fn=f(MONO,28); s='@coach.agz'; d.text((540-d.textlength(s,font=fn)/2,612),s,font=fn,fill=MUTED+(A,))
    kq=expo((t-109.42)/0.2)
    if kq>0:
        fn=f(BAR,36); s='ENHANCED ATHLETE'; w=tracked_w(d,s,fn,8); tracked(d,(540-w/2,706),s,fn,GOLD+(int(255*kq),),8)
    for s,tt,y in [('BLOODWORK +',110.16,754),('RISK MANAGEMENT',110.76,846),('CHECKLIST',111.38,938)]:
        hq=expo((t-tt)/0.16)
        if hq<=0: continue
        fn=f(BEB,98); d.text((540-d.textlength(s,font=fn)/2,y+12*(1-hq)),s,font=fn,fill=CREAM+(int(255*hq),))
    oq=expo((t-112.46)/0.16)
    if oq>0:
        fn=f(MONOB,30); s='+ OPTIMIZATION LIST'; d.text((540-d.textlength(s,font=fn)/2,1050),s,font=fn,fill=VGOLD+(int(255*oq),))
    im.alpha_composite(L); L,d=newL()
    pq=expo((t-PILL)/0.20)
    if pq>0:
        fn=f(MONOB,58); s='COMMENT "OPTIMIZE"'; tw=d.textlength(s,font=fn); bw=tw+80; x0=540-bw/2; y0=1120+lerp(-40,0,pq)
        if GL and t<PILL+0.6: GL.rectangle([x0,y0,x0+bw,y0+120],outline=VGOLD+(int(220*(1-(t-PILL)/0.6)),),width=10)
        lit_bar(d,x0,y0,x0+bw,y0+120,VGOLD,int(255*min(1,pq*1.5)))
        im.alpha_composite(L); L,d=newL()
        tq=clamp((t-PILL-0.08)/0.12)
        if tq>0: d.text((540-tw/2,y0+24),s,font=fn,fill=DEEP+(int(255*tq),))
    fq=expo((t-FREE)/0.14)
    if fq>0:
        fn=f(MONOB,40); s='SENT TO YOU · '; s2='FREE'; tw=d.textlength(s+s2,font=fn); x=540-tw/2
        d.text((x,1272),s,font=fn,fill=CREAM+(int(255*fq),)); d.text((x+d.textlength(s,font=fn),1272),s2,font=fn,fill=VGOLD+(int(255*fq),))
    fn=f(MONO,20); d.text((540-d.textlength(DISC,font=fn)/2,1356),DISC,font=fn,fill=LABEL+(A,))
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
    panels(im,t); chips(im,t); recap(im,t); end_card(im,t)
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
