# Reel: "Tren builds the best illusion" — full edit, 720p30 preview.
# Built on the editor-test-06 setup (captions, pinned title, clinical evidence panels, high-pop overlay palette,
# original footage). Usage: python render.py <scratch> [--events] [--still t ...] [--range n0 n1 out.mp4]
import json, subprocess, sys, math, re
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
S=sys.argv[1]; F=S+'/fonts/'; T=S+'/work/'
W,H=1080,1920; FPS=30; DUR=102.28; N=int(DUR*FPS)
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

# ---------------- words / captions ----------------
words=json.load(open(T+'words.json'))
FIX={2:'TRENBOLONE',37:'TRENBOLONE',39:'TRENBOLONE',109:'TRENBOLONE',214:'TRENBOLONE',289:'TRENBOLONE',
     38:'ACETATE,',80:'SO',40:'ENANTHATE,',49:'ANDROGEN',123:'TREN',127:'F*CKING',237:'F*CKING',279:'SH*T',189:'RECOMPOSITION.'}
for i,w in FIX.items(): words[i]['w']=w
words[189]['e']=words[190]['e']; del words[190]
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
            weak=disp(w['w']) in WEAK and len(cur)>=2 and disp(words[cur[-1]]['w']) not in ('DIALED','EAT','SHOOT')
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
    ws=[disp(words[i]['w']) for i in G[gi]]; size=128
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

# ---------------- timeline ----------------
# punch-ins: (start, end, zoom). Only where no graphic is building (camera holds still while graphics build).
PUNCH=[(7.92,11.30,1.10),(24.30,25.30,1.16),(32.74,35.26,1.14),(53.88,56.45,1.10),(74.50,77.70,1.10),(85.58,87.10,1.18)]
for a,b,z in PUNCH: sfx(a,'sub',g=-26)
P=(64,470,1016,1260)
# panels: (open, close, number, stages)  stage switch times inside -> scan wipe
PANELS=[dict(o=11.42,c=24.12,n=1,st=[(11.42,'RECEPTOR BINDING'),(16.56,'ANABOLIC PROFILE')]),
        dict(o=25.30,c=32.62,n=3,st=[(25.30,'LITERATURE SEARCH')]),
        dict(o=36.72,c=53.72,n=4,st=[(36.72,'WHY IT LOOKS LIKE GROWTH')]),
        dict(o=56.48,c=71.92,n=5,st=[(56.48,'MUSCLE BUILDERS · ON CYCLE')])]
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
    # the panel grows out of the gold edge rule and collapses back into it (handoff between panels)
    x1=lerp(8,P[2],q); x0=lerp(8,P[0],min(1,q*1.6))
    return (x0,P[1],x1,P[3]),q

# ---- panel contents (drawn in absolute coords, clipped to the panel) ----
X0=110; XR=970
def ev1(d,t):        # receptor binding bars
    d.text((X0,560),'RELATIVE ANDROGEN-RECEPTOR BINDING',font=f(BAR,36),fill=MUTED)
    u=130; ax=X0; ay=1050
    a=int(255*clamp((t-11.70)/0.2))
    d.line([(ax,ay),(ax+6*u,ay)],fill=MUTED+(a,),width=2)
    for k in range(7):
        d.line([(ax+k*u,ay),(ax+k*u,ay+12)],fill=MUTED+(a,),width=2)
        lab='0' if k==0 else f'{k}×'; d.text((ax+k*u-d.textlength(lab,font=f(MONO,24))/2,ay+20),lab,font=f(MONO,24),fill=LABEL+(a,))
    # testosterone
    q=expo((t-11.90)/0.22)
    if q>0:
        d.text((ax,680),'TESTOSTERONE',font=f(MONO,30),fill=CREAM+(int(255*q),))
        d.rectangle([ax,730,ax+u*q,790],fill=(205,200,190,235))
        if q>0.6: d.text((ax+u+18,736),'1×',font=f(BEB,60),fill=CREAM)
    q1=expo((t-12.98)/0.22); q2=expo((t-13.42)/0.28)
    if t>12.80:
        d.text((ax,850),'TRENBOLONE',font=f(MONO,30),fill=VGOLD+(int(255*clamp((t-12.8)/0.15)),))
    if q1>0:
        d.rectangle([ax,900,ax+3*u*q1,960],fill=VGOLD+(255,))
        if GL: GL.rectangle([ax,900,ax+3*u*q1,960],outline=VGOLD+(220,),width=6)
    if q2>0:
        xe=ax+3*u+3*u*q2
        d.rectangle([ax+3*u,900,xe,960],outline=VGOLD+(255,),width=3)
        for xx in range(int(ax+3*u)-60,int(xe),18):
            x_a=max(xx,ax+3*u); x_b=min(xx+60,xe)
            if x_b>x_a: d.line([(x_a,960-(x_a-xx)),(x_b,960-(x_b-xx))],fill=VGOLD+(200,),width=3)
        if GL: GL.rectangle([ax+3*u,900,xe,960],outline=VGOLD+(200,),width=6)
    q3=expo((t-13.62)/0.16)
    if q3>0:
        fn=f(BEB,76); s='3–6×'; d.text((ax+6*u-d.textlength(s,font=fn),818-12*(1-q3)),s,font=fn,fill=VGOLD+(int(255*q3),))
    d.text((X0,1150),'AR = ANDROGEN RECEPTOR · VS TESTOSTERONE = 1×',font=f(MONO,22),fill=LABEL)
def ev2(d,t):        # anabolic profile
    rows=[('PROTEIN SYNTHESIS',600,17.30,17.78,0.42,0.90,True),('MUSCLE BREAKDOWN',720,18.14,18.58,0.58,0.16,False)]
    for lab,y,t0,t1,v0,v1,up in rows:
        a=int(255*clamp((t-16.80-(y-600)/1200)/0.15))
        d.text((X0,y),lab,font=f(BAR,46),fill=CREAM+(a,))
        v=lerp(v0,v1,ease_io((t-t0)/(t1-t0))); meter(d,600,y+16,900,v,VGOLD)
        if t>=t1: tri(d,922,y+12,32,up,VGOLD+(255,))
    # aromatisation schematic
    y=850; a=int(255*clamp((t-19.30)/0.15))
    if a>0:
        d.text((X0,y-6),'AROMATISATION',font=f(MONO,24),fill=LABEL+(a,))
        d.rounded_rectangle([X0,y+30,X0+220,y+100],radius=10,outline=CREAM+(a,),width=3); d.text((X0+30,y+38),'TREN',font=f(BEB,58),fill=CREAM+(a,))
        q=ease_io((t-19.76)/0.30); xa=X0+240; xb=X0+470
        d.line([(xa,y+65),(lerp(xa,xb,q),y+65)],fill=CREAM+(a,),width=4)
        if q>=1: d.polygon([(xb,y+52),(xb+20,y+65),(xb,y+78)],fill=CREAM+(a,))
        if t>19.94:
            b=int(255*clamp((t-19.94)/0.12)); bx=xb+40
            d.rounded_rectangle([bx,y+30,bx+170,y+100],radius=10,outline=CREAM+(b,),width=3); d.text((bx+34,y+38),'E2',font=f(BEB,58),fill=CREAM+(b,))
            flag_box(d,(bx-8,y+22,bx+178,y+108),'NONE',20.20,t)
            if t>20.20:
                cx=(xa+xb)/2; d.line([(cx-22,y+43),(cx+22,y+87)],fill=RED+(255,),width=7); d.line([(cx+22,y+43),(cx-22,y+87)],fill=RED+(255,),width=7)
    # resulting look chips
    y=1000
    if t>21.0:
        d.text((X0,y),'RESULTING LOOK',font=f(MONO,24),fill=LABEL)
        x=X0
        for w_,tt in [('DRY',21.08),('HARD',21.50),('GRAINY',21.88)]:
            q=expo((t-tt)/0.12)
            if q<=0: break
            fn=f(BAR,40); tw=d.textlength(w_,font=fn)
            d.rectangle([x,y+40,x+tw+36,y+96],outline=VGOLD+(int(255*q),),width=3); d.text((x+18,y+44-8*(1-q)),w_,font=fn,fill=VGOLD+(int(255*q),))
            x+=tw+56
    y=1130
    if t>23.10:
        a=int(255*clamp((t-23.10)/0.15)); d.text((X0,y),'WATER RETENTION',font=f(BAR,46),fill=CREAM+(a,))
        v=lerp(0.55,0.12,ease_io((t-23.40)/0.36)); meter(d,600,y+16,900,v,VGOLD)
        if t>=23.76: tri(d,922,y+12,32,False,VGOLD+(255,))
def ev3(d,t):        # literature search
    d.rounded_rectangle([X0,560,XR,636],radius=12,fill=INNER+(255,),outline=MUTED+(110,),width=2)
    d.ellipse([X0+22,578,X0+54,610],outline=CREAM,width=4); d.line([(X0+50,606),(X0+64,620)],fill=CREAM,width=5)
    q='trenbolone vs testosterone'; n=int(len(q)*clamp((t-25.50)/0.55)); d.text((X0+84,576),q[:n]+('▌' if int(t*5)%2==0 and n<len(q)+1 else ''),font=f(MONO,32),fill=CREAM)
    x=X0
    for lab,tt in [('CLINICAL',26.48),('HUMANS',27.36),('MUSCLE MASS',29.58)]:
        fn=f(MONO,26); tw=d.textlength(lab,font=fn); on=t>=tt
        if on:
            d.rectangle([x,662,x+tw+28,706],fill=VGOLD+(255,)); d.text((x+14,668),lab,font=fn,fill=DEEP)
            if GL and t<tt+0.4: GL.rectangle([x,662,x+tw+28,706],outline=VGOLD+(200,),width=6)
        else: d.rectangle([x,662,x+tw+28,706],outline=LABEL+(255,),width=2); d.text((x+14,668),lab,font=fn,fill=LABEL)
        x+=tw+44
    if t<26.80 and t>26.0:
        d.text((X0,760),'SEARCHING'+'.'*(int(t*6)%4),font=f(MONO,30),fill=LABEL)
    qz=expo((t-26.80)/0.16)
    if qz>0:
        s=lerp(1.12,1,qz); fn=f(BEB,int(300*s)); d.text((X0-10,720+(1-s)*120),'0',font=fn,fill=RED+(int(255*qz),))
        if GL: GL.text((X0-10,720+(1-s)*120),'0',font=fn,fill=RED+(int(170*qz),))
        ql=expo((t-26.94)/0.16)
        if ql>0:
            a=int(255*ql); d.text((X0+200,770),'HUMAN CLINICAL STUDIES',font=f(BAR,46),fill=CREAM+(a,))
            d.text((X0+200,830),'SHOWING TREN > TEST FOR MUSCLE',font=f(MONO,26),fill=MUTED+(a,))
    for i,(lab,tt) in enumerate([('LIVESTOCK GROWTH STUDIES',28.08),('RODENT STUDIES',28.38),('CELL / IN-VITRO',28.58)]):
        q=expo((t-tt)/0.14)
        if q<=0: continue
        y=1010+i*46; a=int(200*q)
        d.text((X0,y),'· '+lab,font=f(MONO,28),fill=MUTED+(a,))
        fn=f(MONO,22); tw=d.textlength('NOT HUMAN',font=fn); d.rectangle([XR-tw-20,y+2,XR,y+34],outline=LABEL+(a,),width=2); d.text((XR-tw-10,y+5),'NOT HUMAN',font=fn,fill=LABEL+(a,))
    if t>=31.44:
        p=expo((t-31.44)/0.10); y=1160; x1=lerp(P[0],P[2],p)
        if GL: GL.rectangle([P[0]-4,y-8,x1+4,y+96],outline=RED+(255,),width=10)
        lit_bar(d,P[0],y,x1,y+88,RED); d.rectangle([P[0],y+84,x1,y+88],fill=(140,0,0))
        if p>0.6:
            fn=f(BEB,72); d.text((P[0]+40,y+8),'UNPROVEN',font=fn,fill=(255,255,255))
            d.text((P[0]+40+d.textlength('UNPROVEN',font=fn)+26,y+30),'IN HUMANS · TREN VS TEST',font=f(MONO,28),fill=(255,255,255))
def ev4(d,t):        # why it looks like growth: what you see vs what's causing it
    rows=[('01','LOOKS LEANER + HARDER',37.02,[('FAT',38.18,False),('WATER',38.80,False)]),
          ('02','LOOKS BIGGER + FULLER',40.34,[('GLYCOGEN',40.84,True),('FULLNESS',41.60,True)]),
          ('03','FEELS LIKE GROWING',43.06,[('STRENGTH',43.94,True),('NERVOUS SYSTEM',44.72,None)])]
    for i,(num,lab,t0,reads) in enumerate(rows):
        y=580+i*160; q=expo((t-t0)/0.14)
        if q<=0: continue
        a=int(255*q); dx=-24*(1-q)
        d.text((X0+dx,y-6),num,font=f(BEB,72),fill=VGOLD+(a,))
        d.text((X0+90+dx,y+4),lab,font=f(BAR,46),fill=CREAM+(a,))
        x=X0+90
        for k,(r,tt,up) in enumerate(reads):
            qr=expo((t-tt)/0.12)
            if qr<=0: continue
            ar=int(255*qr)
            if up is None:
                txt='SOURCE: '+r; d.text((x,y+68),txt,font=f(MONO,28),fill=MUTED+(ar,)); x+=d.textlength(txt,font=f(MONO,28))+30
            else:
                d.text((x,y+68),r,font=f(MONO,30),fill=CREAM+(ar,)); x+=d.textlength(r,font=f(MONO,30))+12
                tri(d,x,y+76,24,up,VGOLD+(ar,)); x+=60
    y=1080
    if t>47.94:
        a=int(255*clamp((t-47.94)/0.15)); d.line([(X0,y),(XR,y)],fill=MUTED+(int(a*0.4),),width=2)
        d.text((X0,y+16),'WHAT ACTUALLY CHANGED',font=f(MONO,24),fill=LABEL+(a,))
    q=expo((t-49.32)/0.18)
    if q>0:
        x=lerp(X0-60,X0,q); fn=f(MONOB,34); tw=d.textlength('RECOMPOSITION',font=fn)
        d.rectangle([x,y+60,x+tw+40,y+124],fill=VGOLD+(int(255*q),)); d.text((x+20,y+72),'RECOMPOSITION',font=fn,fill=DEEP+(int(255*q),))
        if GL and t<49.9: GL.rectangle([x,y+60,x+tw+40,y+124],outline=VGOLD+(200,),width=6)
    q=expo((t-50.98)/0.14)
    if q>0:
        fn=f(MONO,30); s='+10 LB NEW MUSCLE'; x=XR-d.textlength(s,font=fn); a=int(255*q)
        d.text((x,y+62),s,font=fn,fill=CREAM+(a,)); d.text((XR-d.textlength('IN MONTH 1–2',font=f(MONO,24)),y+104),'IN MONTH 1–2',font=f(MONO,24),fill=MUTED+(a,))
        qs=expo((t-51.96)/0.12)
        if qs>0:
            d.line([(x-8,y+82),(lerp(x-8,XR+8,qs),y+82)],fill=RED+(255,),width=6)
            if GL: GL.line([(x-8,y+82),(lerp(x-8,XR+8,qs),y+82)],fill=RED+(255,),width=12)
def ev5(d,t):        # the three builders, on cycle
    rows=[('SLEEP',590,59.54,'DISRUPTED',[66.24]),('TRAINING',720,60.36,'CARDIO LIMITED',[67.36]),('NUTRITION',850,68.38,'OFF TRACK',[])]
    for i,(lab,y,tbad,bad,pulses) in enumerate(rows):
        q=expo((t-56.88-i*0.10)/0.14)
        if q<=0: continue
        a=int(255*q); d.text((X0,y),lab,font=f(BEB,96),fill=CREAM+(a,))
        d.line([(X0,y+110),(XR,y+110)],fill=MUTED+(int(a*0.3),),width=2)
        if t<tbad:
            fn=f(MONO,28); s='BASELINE'; tw=d.textlength(s,font=fn); check(d,XR-tw-50,y+34,GREEN+(a,)); d.text((XR-tw,y+28),s,font=fn,fill=GREEN+(a,))
        else:
            red_tag(d,XR,y+20,bad,32,right=True)
            for pt in [tbad]+pulses:
                if pt<=t<pt+0.45:
                    k=1-(t-pt)/0.45; brackets(d,X0-24,y-8,XR+24,y+100,RED+(int(255*k),),30,5)
                    if GL: brackets(GL,X0-24,y-8,XR+24,y+100,RED+(int(255*k),),30,10)
    x=X0; y=990
    for lab,tt in [('MOOD UNSTABLE',62.52),('BLOOD PRESSURE',63.10)]:
        q=expo((t-tt)/0.14)
        if q<=0: continue
        fn=f(BAR,36); tw=d.textlength(lab,font=fn)+(44 if 'PRESSURE' in lab else 0)
        d.rectangle([x,y,x+tw+36,y+56],fill=CHIP+(int(240*q),),outline=RED+(int(255*q),),width=2)
        d.text((x+18,y+6),lab,font=fn,fill=(255,150,140,int(255*q)))
        if 'PRESSURE' in lab: tri(d,x+18+tw-34,y+16,24,True,(255,150,140,int(255*q)))
        x+=tw+60
    y=1100
    if t>69.20:
        a=int(255*clamp((t-69.20)/0.15)); d.text((X0,y),'RECOVERY DEFICIT',font=f(MONO,26),fill=LABEL+(a,))
        bx0,bx1=X0,XR; d.rectangle([bx0,y+44,bx1,y+84],outline=MUTED+(int(a*0.6),),width=2)
        v=ease_io((t-69.38)/(71.08-69.38)); xe=bx0+4+(bx1-bx0-8)*v
        lit_bar(d,bx0+4,y+48,xe,y+80,RED)
        if GL: GL.rectangle([bx0+4,y+48,xe,y+80],outline=RED+(200,),width=6)
        for k in range(6):
            xx=bx0+(bx1-bx0)*k/5; d.line([(xx,y+84),(xx,y+96)],fill=MUTED+(a,),width=2)
            lab=f'WK {k*4}'; fn=f(MONO,22); d.text((min(max(xx-d.textlength(lab,font=fn)/2,bx0),bx1-d.textlength(lab,font=fn)),y+102),lab,font=fn,fill=LABEL+(a,))
        q=expo((t-71.08)/0.14)
        if q>0: fn=f(BEB,64); s='20 WEEKS'; d.text((XR-d.textlength(s,font=fn),y-22),s,font=fn,fill=RED+(int(255*q),))
CONTENT={1:[(11.42,ev1),(16.56,ev2)],3:[(25.30,ev3)],4:[(36.72,ev4)],5:[(56.48,ev5)]}
sfx(12.98,'tick',g=-28); sfx(13.42,'tick',g=-28); sfx(17.78,'tick',g=-30); sfx(18.58,'tick',g=-30); sfx(20.20,'tick',g=-25)
sfx(21.08,'tick',g=-33); sfx(21.88,'tick',g=-33)
sfx(25.50,'scan',d=0.55,g=-31); sfx(26.80,'thud',w=1.8,g=-14); sfx(27.36,'tick',g=-30); sfx(29.58,'tick',g=-30); sfx(31.54,'impact',g=-13)
sfx(38.18,'tick',g=-30); sfx(40.84,'tick',g=-30); sfx(43.94,'tick',g=-30); sfx(49.32+0.12,'thud',w=1.2,g=-18); sfx(51.96,'tick',g=-25)
sfx(59.54,'tick',g=-25); sfx(60.36,'tick',g=-25); sfx(68.38,'tick',g=-25); sfx(69.38,'scan',d=1.70,g=-32); sfx(71.08,'impact',g=-13)
SHAKES=[31.54,71.08]

def panels(im,t):
    for p in PANELS:
        box,q=panel_box(t,p)
        if box is None: continue
        x0,y0,x1,y1=box
        frosted(im,box,0.92,8)
        lay=Image.new('RGBA',(W,H),(0,0,0,0))
        # content: stages switched by a scan wipe inside the persistent frame
        stages=CONTENT[p['n']]; si=0
        for k,(st,_) in enumerate(stages):
            if t>=st: si=k
        def render_stage(k):
            l=Image.new('RGBA',(W,H),(0,0,0,0)); dd=ImageDraw.Draw(l,'RGBA'); stages[k][1](dd,t); return l
        ys=None
        cur=render_stage(si)
        if si>0 and t<stages[si][0]+0.30:
            wq=ease_io((t-stages[si][0])/0.30); ys=int(lerp(y0+70,y1,wq))
            prev=render_stage(si-1); m=Image.new('L',(W,H),0); ImageDraw.Draw(m).rectangle([0,0,W,ys],fill=255)
            cur=Image.composite(cur,prev,m)
        if q<1: cur.putalpha(cur.split()[3].point(lambda v:int(v*q)))
        clip=Image.new('L',(W,H),0); ImageDraw.Draw(clip).rectangle([x0,y0,x1,y1],fill=255)
        cur.putalpha(ImageChops_mul(cur.split()[3],clip))
        lay.alpha_composite(cur)
        d=ImageDraw.Draw(lay,'RGBA'); a=int(255*q)
        d.rectangle([x0,y0,x1,y1],outline=VGOLD+(int(a*0.8),),width=3); brackets(d,x0,y0,x1,y1,VGOLD+(a,),48,7)
        if GL: brackets(GL,x0,y0,x1,y1,VGOLD+(a,),44,14); GL.rectangle([x0,y0,x1,y1],outline=VGOLD+(int(a*0.5),),width=6)
        if x1-x0>600:
            stage=[s for st,s in p['st'] if t>=st][-1]; ev=p['n']+(1 if (p['n']==1 and t>=16.56) else 0)
            d.ellipse([x0+26,y0+26,x0+42,y0+42],fill=RED+(a if int(t*4)%2==0 else a//3,))
            d.text((x0+56,y0+18),stage,font=f(MONO,28),fill=CREAM+(a,))
            s=f'EVIDENCE 0{ev}'; d.text((x1-30-d.textlength(s,font=f(MONO,28)),y0+18),s,font=f(MONO,28),fill=VGOLD+(a,))
            d.line([(x0+20,y0+66),(x1-20,y0+66)],fill=MUTED+(int(a*0.25),),width=1)
        if ys:
            g=Image.new('RGBA',(W,H),(0,0,0,0)); gd=ImageDraw.Draw(g); gd.rectangle([x0+4,ys-3,x1-4,ys+3],fill=CYAN+(255,))
            if GL: GL.rectangle([x0+4,ys-10,x1-4,ys+10],fill=CYAN+(230,))
            lay.alpha_composite(g.filter(ImageFilter.GaussianBlur(8))); lay.alpha_composite(g)
        im.alpha_composite(lay)
from PIL import ImageChops
def ImageChops_mul(a,b): return ImageChops.multiply(a,b)

# ---- hook title card -> pinned title (handoff) ----
TK=0.30; TL1=1.14; TL2=2.74; TRED=3.52; THO=(4.10,4.45)
sfx(TK,'tick',g=-30); sfx(TL1,'thud',w=0.8,g=-20); sfx(TL2,'thud',w=1.3,g=-16); sfx(THO[0],'whoosh',d=0.30,g=-28)
PIN_HIDE=(87.05,87.30)
DISC='FOR RESEARCH & EDUCATIONAL PURPOSES ONLY'
def newL():
    l=Image.new('RGBA',(W,H),(0,0,0,0)); return l,ImageDraw.Draw(l,'RGBA')
def title(im,t):
    h=ease_io((t-THO[0])/(THO[1]-THO[0]))          # 0 = title card, 1 = pinned bar
    hide=ease_io((t-PIN_HIDE[0])/(PIN_HIDE[1]-PIN_HIDE[0])); ty=-220*hide
    if hide>=1: return
    # pinned bar background
    if h>0:
        B,bd=newL(); bd.rectangle([8,200+ty,W,388+ty],fill=NAVY+(int(240*h),)); im.alpha_composite(B)
    L,d=newL()
    # kicker
    kq=expo((t-TK)/0.25); ky=lerp(250,224,h)+ty
    if kq>0:
        d.line([(64,ky+20),(64+50*kq,ky+20)],fill=GOLD,width=4)
        fn=f(BAR,lerp(38,30,h)); n=int(len('TRENBOLONE')*clamp((t-TK-0.12)/0.25))
        tracked(d,(130,ky+lerp(0,3,h)),'TRENBOLONE'[:n],fn,GOLD,lerp(9,7,h))
    if h>0:
        a=int(255*h); fn=f(MONO,24); s='@coach.agz'; d.text((1016-d.textlength(s,font=fn),ky+6),s,font=fn,fill=GOLD+(a,))
        fn=f(MONO,18); d.text((64,352+ty),DISC,font=fn,fill=LABEL+(a,))
    # line 1 (title card only)
    q1=expo((t-TL1)/0.16)
    if q1>0 and h<1:
        h1=clamp(h*3); a=int(255*q1*(1-h1)); fn=f(BEB,100); y=282-40*h1+10*(1-q1)
        L1,d1=newL(); d1.text((64,y),'NOT THE MOST MUSCLE.',font=fn,fill=CREAM+(a,)); L.alpha_composite(L1)
    # line 2 travels into the pinned headline
    q2=expo((t-TL2)/0.16)
    if q2>0:
        size=lerp(124,86,h); y=lerp(380,262,h)+ty+12*(1-q2); fn=f(BEB,size); a=int(255*q2)
        txt=['THE BEST ','ILLUSION']
        d.text((64,y),txt[0],font=fn,fill=CREAM+(a,))
        rc=ease_io((t-TRED)/0.10); col=tuple(int(lerp(c1,c2,rc)) for c1,c2 in zip(CREAM,RED))
        d.text((64+d.textlength(txt[0],font=fn),y),txt[1],font=fn,fill=col+(a,))
        if h<1: d.text((64+d.textlength('THE BEST ILLUSION',font=fn),y),'.',font=fn,fill=CREAM+(int(a*(1-h)),))
    im.alpha_composite(L)

# ---- checklist chips under the pinned title (77.8 – 85.4) ----
CHK=[('HORMONES',77.82),('LIFESTYLE',79.64),('SLEEP',80.68),('FOOD',81.48)]; CHK_OUT=85.30
for _,tt in CHK: sfx(tt,'tick',g=-31)
def checklist(im,t):
    if t<CHK[0][1] or t>CHK_OUT+0.2: return
    out=ease_io((t-CHK_OUT)/0.2); d=ImageDraw.Draw(im,'RGBA')
    for i,(lab,tt) in enumerate(CHK):
        x=40-20*out
        q=expo((t-tt)/0.14)
        if q<=0: break
        fn=f(BAR,40); tw=d.textlength(lab,font=fn); bw=tw+88; y=640+i*80; x+=-24*(1-q); a=int(255*q*(1-out))
        if out<1: frosted(im,(x,y,x+bw,y+62),0.86*(1-out),10)
        L,d=newL()
        d.rectangle([x,y,x+bw,y+62],outline=GREEN+(int(a*0.55),),width=2)
        check(d,x+18,y+20,GREEN+(a,),4,0.95); d.text((x+58,y+8),lab,font=fn,fill=CREAM+(a,)); im.alpha_composite(L)
        if GL and t<tt+0.35: check(GL,x+18,y+20,GREEN+(a,),9,0.95)

# ---- stack build (87.3 – 98.5) and end card (98.5 – end) ----
STACK=[('01','TEST',87.32),('02','FOOD',88.08),('03','SLEEP',88.56),('04','PROGRESSIVE OVERLOAD',89.22),('05','TIME',90.38)]
SCN_IN=(87.05,87.35); EQ=93.88; END=98.50
for i,(_,_,tt) in enumerate(STACK): sfx(tt+0.12,'thud',w=0.9+0.25*i if i<4 else 1.8,g=-19 if i<4 else -14)
sfx(SCN_IN[0],'scan',d=0.30,g=-29); sfx(90.98,'tick',g=-30); sfx(EQ+0.16,'thud',w=1.2,g=-17)
sfx(END-0.05,'whoosh',d=0.25,g=-27); sfx(END+0.22,'thud',w=1.5,g=-15); sfx(100.98,'tick',g=-27)
BH=108; STEP=124; SB=1290
LOGO=None
def logo():
    global LOGO
    if LOGO is None:
        lg=Image.open(S+'/logo.jpg').convert('RGB').resize((240,240),Image.LANCZOS)
        m=Image.new('L',(240,240),0); ImageDraw.Draw(m).ellipse([0,0,239,239],fill=255); lg.putalpha(m); LOGO=lg
    return LOGO
_SB=None
def scene_bg(a):
    # carousel look: flat navy with a soft warm glow top-right and fine static grain
    global _SB
    if _SB is None:
        bg=np.zeros((H,W,3),np.float32)+np.array(NAVY,np.float32)
        yy,xx=np.mgrid[0:H,0:W]; r=np.sqrt(((xx-W)/(W*0.9))**2+(yy/(H*0.5))**2)
        bg+=(np.clip(1-r,0,1)**2)[...,None]*np.array([16,12,6],np.float32)
        bg+=np.random.default_rng(3).standard_normal((H,W,1)).astype(np.float32)*1.6
        _SB=Image.fromarray(np.clip(bg,0,255).astype(np.uint8)).convert('RGBA')
    l=_SB.copy(); l.putalpha(int(255*a*0.94)); return l
def stack_scene(im,t):
    if t<SCN_IN[0]: return
    a=ease_io((t-SCN_IN[0])/(SCN_IN[1]-SCN_IN[0]))
    im.alpha_composite(scene_bg(a)); L,d=newL()
    e=ease_io((t-END)/0.14)        # stack clears fast, before the end-card text arrives
    # kicker + headline
    if t>90.90 and e<1:
        kq=expo((t-90.90)/0.25); ae=int(255*(1-e))
        d.line([(64,250),(64+50*kq,250)],fill=GOLD+(ae,),width=4)
        lab='THE BUILD' if t<EQ-0.3 else 'THE REAL MUSCLE EQUATION'; t0=90.98 if t<EQ-0.3 else EQ-0.3
        n=int(len(lab)*clamp((t-t0-0.1)/0.3)); tracked(d,(130,232),lab[:n],f(BAR,36),GOLD+(ae,),8)
        hq=expo((t-91.20)/0.16)
        if hq>0:
            fn=f(BEB,132); y=278+10*(1-hq); ah=int(255*hq*(1-e)); d.text((64,y),'WHAT BUILDS ',font=fn,fill=CREAM+(ah,))
            rc=ease_io((t-91.92)/0.10); col=tuple(int(lerp(c1,c2,rc)) for c1,c2 in zip(CREAM,GOLD))
            d.text((64+d.textlength('WHAT BUILDS ',font=fn),y),'MUSCLE.',font=fn,fill=col+(ah,))
    im.alpha_composite(L)
    # heavy blocks land bottom-up (shadows first, then the blocks)
    blocks=[]; SH,shd=newL(); L,d=newL()
    for i,(num,lab,tt) in enumerate(STACK):
        q=clamp((t-tt)/0.14)
        if q<=0: continue
        land=1-(1-q)**3; yb=SB-i*STEP; y=yb-BH-lerp(70,0,land)
        rec=0
        if q>=1: k=(t-tt-0.14); rec=6*math.exp(-k*30)*math.sin(k*40) if k<0.3 else 0    # small settle on landing
        y+=rec+e*(60+i*14); ae=(1-e)
        x0,x1=64,1016
        shd.rectangle([x0+10,y+18,x1+10,y+BH+22],fill=(0,0,0,int(150*land*ae)))
        a=int(255*min(1,q*2)*ae)
        d.rectangle([x0,y,x1,y+BH],fill=(25,28,35,a),outline=(58,54,48,a),width=2)
        d.rectangle([x0,y,x0+10,y+BH],fill=GOLD+(a,))
        d.text((x0+40,y+30),num,font=f(MONO,36),fill=GOLD+(a,))
        d.text((x0+130,y+12),lab,font=f(BEB,92),fill=CREAM+(a,))
    if SH.getbbox(): im.alpha_composite(SH.filter(ImageFilter.GaussianBlur(14)))
    im.alpha_composite(L); L,d=newL()
    if t>=EQ and e<1:
        for i in range(1,5):
            pq=expo((t-EQ-i*0.05)/0.12); y=SB-i*STEP-BH+BH/2
            d.text((1016-78,y-46),'+',font=f(BEB,96),fill=GOLD+(int(255*pq*(1-e)),))
    # "= MUSCLE" bar -> becomes the COMMENT pill on the end card
    if t>=EQ:
        q=expo((t-EQ)/0.18); y_eq=SB+14
        fn_eq=f(BEB,96); s_eq='=  MUSCLE'
        if t<END:
            x=lerp(-200,64,q); d.rectangle([x,y_eq,x+952,y_eq+BH],fill=VGOLD+(255,))
            if GL and t<EQ+0.5: GL.rectangle([x,y_eq,x+952,y_eq+BH],outline=VGOLD+(200,),width=8)
            d.text((x+40,y_eq+8),s_eq,font=fn_eq,fill=DEEP+(255,))
        else:
            m=expo((t-END)/0.30)
            fn=f(MONOB,58); s='COMMENT "MUSCLE"'; tw=d.textlength(s,font=fn)
            bw=lerp(952,tw+80,m); bh=lerp(BH,120,m); cx=lerp(64+476,540,m); cy=lerp(y_eq+BH/2,1040,m)
            x0=cx-bw/2; y0=cy-bh/2
            if GL and t<END+0.7: GL.rectangle([x0,y0,x0+bw,y0+bh],outline=VGOLD+(int(200*(1-clamp((t-END-0.3)/0.4))),),width=10)
            d.rectangle([x0,y0,x0+bw,y0+bh],fill=VGOLD+(255,)); im.alpha_composite(L); L,d=newL()
            if m<0.5: d.text((x0+40,y0+8),s_eq,font=fn_eq,fill=DEEP+(int(255*(1-m*2)),))
            else: d.text((cx-tw/2,cy-36),s,font=fn,fill=DEEP+(int(255*(m-0.5)*2),))
            im.alpha_composite(L); L,d=newL()
            end_card(im,t)
    im.alpha_composite(L)

def end_card(im,t):
    q=expo((t-END-0.16)/0.25)
    if q<=0: return
    a=int(255*q)
    lg=logo().copy(); lg.putalpha(lg.split()[3].point(lambda v:int(v*q))); im.alpha_composite(lg,(540-120,330)); L,d=newL()
    fn=f(BAR,40); s='COACH AGZ'; w=tracked_w(d,s,fn,10); tracked(d,(540-w/2,600),s,fn,GOLD+(a,),10)
    fn=f(MONO,28); s='@coach.agz'; d.text((540-d.textlength(s,font=fn)/2,656),s,font=fn,fill=MUTED+(a,))
    fn=f(BEB,104); s='THE REAL MUSCLE EQUATION'; tw=d.textlength(s,font=fn)
    if tw>952: fn=f(BEB,int(104*952/tw)); tw=d.textlength(s,font=fn)
    d.text((540-tw/2,800+8*(1-q)),s,font=fn,fill=CREAM+(a,))
    fn=dm(34,500)
    s1='Healthiest and fastest way to build muscle.'; d.text((540-d.textlength(s1,font=fn)/2,920),s1,font=fn,fill=MUTED+(a,))
    qf=expo((t-100.98)/0.14)
    if qf>0:
        fn=f(MONOB,40); s='SENT TO YOU · '; s2='FREE'; tw=d.textlength(s+s2,font=fn); x=540-tw/2
        d.text((x,1130),s,font=fn,fill=CREAM+(int(255*qf),)); d.text((x+d.textlength(s,font=fn),1130),s2,font=fn,fill=VGOLD+(int(255*qf),))
    fn=f(MONO,20); d.text((540-d.textlength(DISC,font=fn)/2,1240),DISC,font=fn,fill=LABEL+(a,))
    im.alpha_composite(L)

# ---------------- frame ----------------
def punch_zoom(t):
    z=1.0
    for a,b,zz in PUNCH:
        if a<=t<b+0.12:
            zin=expo((t-a)/0.12); zout=expo((t-b)/0.12) if t>=b else 0
            z=lerp(1,zz,zin*(1-zout))
    return z
_PT=None
def frame(src,t):
    z=punch_zoom(t)
    if z>1.001:
        cx,cy=540,980; w,h=W/z,H/z; src=src.crop((cx-w/2,cy-h/2,cx+w/2,cy+h/2)).resize((W,H),Image.BICUBIC)
    g=push_amt(t); bg=src
    if g>0: bg=Image.blend(src.filter(ImageFilter.GaussianBlur(18*g)),Image.new('RGB',(W,H),(5,8,16)),0.68*g)
    im=bg.convert('RGBA')
    global _PT
    if _PT is None:
        sc=np.zeros(H,np.float32); y=np.arange(H)
        sc=np.maximum(np.where(y>1300,np.minimum(1,(y-1300)/260)*120,0),np.where(y<440,(1-y/440)*120,0))
        _PT=(sc,np.where(y<560,np.clip(1-(y-200)/360,0,1)*np.minimum(1,y/200+0.6)*95,0))
    tc=clamp(1-ease_io((t-THO[0])/(THO[1]-THO[0])))       # extra scrim behind the hook title card
    alpha=np.clip(np.maximum(_PT[0]*(1-g),_PT[1]*tc),0,255).astype(np.uint8)
    scr=Image.new('RGBA',(W,H),NAVY+(0,)); scr.putalpha(Image.fromarray(np.repeat(alpha[:,None],W,1)))
    im.alpha_composite(scr)
    global GL
    glow=Image.new('RGBA',(W,H),(0,0,0,0)); GL=ImageDraw.Draw(glow,'RGBA')
    panels(im,t); checklist(im,t); stack_scene(im,t)
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
            subprocess.run(['ffmpeg','-v','error','-y','-ss',str(tt),'-i',T+'raw.mov','-frames:v','1',T+'qc/_src.png'])
            frame(Image.open(T+'qc/_src.png').convert('RGB'),tt).resize((540,960),Image.LANCZOS).save(T+f'qc/s_{tt:06.2f}.jpg',quality=88)
        sys.exit()
    if a and a[0]=='--range':
        n0,n1,outp=int(a[1]),int(a[2]),a[3]
        dec=subprocess.Popen(['ffmpeg','-v','error','-ss',f'{n0/FPS:.4f}','-i',T+'raw.mov','-frames:v',str(n1-n0),'-f','rawvideo','-pix_fmt','rgb24','-'],stdout=subprocess.PIPE)
        enc=subprocess.Popen(['ffmpeg','-v','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-','-vf','scale=720:1280:flags=lanczos','-c:v','libx264','-crf','18','-preset','medium','-pix_fmt','yuv420p',outp],stdin=subprocess.PIPE)
        for n in range(n0,n1):
            buf=dec.stdout.read(W*H*3)
            if len(buf)<W*H*3: print('short at',n); break
            enc.stdin.write(frame(Image.frombuffer('RGB',(W,H),buf),n/FPS).tobytes())
        enc.stdin.close(); enc.wait(); dec.kill(); print('done',n0,n1)
