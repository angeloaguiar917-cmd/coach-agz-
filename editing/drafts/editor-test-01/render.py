import json, subprocess, sys, math
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
S=sys.argv[1]; F=S+'/fonts/'; T=S+'/test1/'
W,H=1080,1920; FPS=30; DUR=9.40; N=int(round(DUR*FPS))
GOLD=(201,169,110); CREAM=(244,241,234); RED=(231,71,42); NAVY=(14,17,23); PANEL=(24,26,34); MUTED=(184,184,188); GREEN=(91,183,122)
_fc={}
def f(n,s):
    k=(n,int(s))
    if k not in _fc: _fc[k]=ImageFont.truetype(F+n,int(s))
    return _fc[k]
def clamp(x,a=0,b=1): return max(a,min(b,x))
def ease_out(x): x=clamp(x); return 1-(1-x)**3
def ease_io(x): x=clamp(x); return 4*x**3 if x<.5 else 1-(-2*x+2)**3/2
def ease_back(x,s=1.7): x=clamp(x); return 1+(s+1)*(x-1)**3+s*(x-1)**2
def lerp(a,b,t): return a+(b-a)*t
def lc(a,b,t): return tuple(int(lerp(a[i],b[i],t)) for i in range(3))

words=json.load(open(T+'words.json'))
# caption groups by phrasing (indices into words)
G=[(0,3),(3,5),(5,8),(8,11),(11,14),(14,17),(17,20),(20,22),(22,24),(24,27),(27,29),(29,32)]
def gstart(g): return words[G[g][0]]['s']
HAND={5:dict(t0=4.36,t1=4.70,card=0),9:dict(t0=7.38,t1=7.70,card=1)}
def group_at(t):
    cur=None
    for gi,(a,b) in enumerate(G):
        if words[a]['s']<=t+1e-6: cur=gi
    if cur is None: return None
    if cur in HAND and t>=HAND[cur]['t0']: return None   # handed off
    if cur-1 in HAND and t<HAND[cur-1]['t0']+0.067: return None
    return cur
def active_word(t,gi):
    a,b=G[gi]; act=a
    for i in range(a,b):
        if words[i]['s']<=t: act=i
    return act
def clean(w): return w.upper().rstrip(',')

CAP_Y=1335; CAP_MAX=920
def cap_layout(gi,d):
    a,b=G[gi]; ws=[clean(words[i]['w']) for i in range(a,b)]
    size=128
    while True:
        fn=f('BebasNeue.ttf',size); sp=d.textlength(' ',font=fn)+14
        wd=[d.textlength(w,font=fn) for w in ws]; tot=sum(wd)+sp*(len(ws)-1)
        if tot<=CAP_MAX: break
        size-=4
    x=(W-tot)/2; xs=[]
    for w_ in wd: xs.append(x); x+=w_+sp
    return ws,wd,xs,size

CARDS=[dict(y=520,h=280,head='USA BIG PHARMA',hc=GOLD,bar=GOLD,rise=(4.40,4.72),rows=[(4.95,'x','Don\'t trust it.')]),
       dict(y=840,h=370,head="CHINA'S BIG PHARMA",hc=RED,bar=RED,rise=(7.30,7.62),rows=[(7.95,'v','Order everything.')])]
HEAD_SIZE=108; HEAD_X=100
STAMP_T=8.66

def draw_mark(d,kind,x,y,col,p):
    if kind=='v':
        pts=[(x,y+18),(x+12,y+32),(x+36,y+2)]
    else:
        d.line([(x+2,y+2),(x+32,y+32)],fill=col,width=7)
        if p>0.5: d.line([(x+32,y+2),(x+2,y+32)],fill=col,width=7)
        return
    if p<=0.5: d.line([pts[0],(lerp(pts[0][0],pts[1][0],p*2),lerp(pts[0][1],pts[1][1],p*2))],fill=col,width=7)
    else: d.line([pts[0],pts[1],(lerp(pts[1][0],pts[2][0],(p-.5)*2),lerp(pts[1][1],pts[2][1],(p-.5)*2))],fill=col,width=7,joint='curve')

def frame(src,t):
    # --- background layer: footage, pushed back during graphic scene
    g=ease_io((t-4.30)/0.35)
    bg=src
    if g>0:
        b=src.filter(ImageFilter.GaussianBlur(18*g))
        dim=Image.new('RGB',(W,H),NAVY); bg=Image.blend(b,dim,0.55*g)
    im=bg.convert('RGBA')
    ov=Image.new('RGBA',(W,H),(0,0,0,0)); d=ImageDraw.Draw(ov)
    # light scrim behind caption zone + top (lighter grade per feedback)
    sc=Image.new('L',(1,H))
    for y in range(H):
        a=0
        if y>1180: a=min(1,(y-1180)/260)*110
        if y<420: a=max(a,(1-y/420)*120)
        sc.putpixel((0,y),int(a*(1-g)))
    im.alpha_composite(Image.merge('RGBA',[Image.new('L',(W,H),c) for c in NAVY]+[sc.resize((W,H))]))
    # --- gold edge rule
    d.rectangle([0,0,7,H],fill=GOLD+(255,))
    # --- pinned title: slides down, small overshoot
    p=ease_back((t-0.0)/0.35,1.2); ty=lerp(-180,0,p)
    d.rectangle([8,212+ty,W,372+ty],fill=NAVY+(228,))
    d.line([(64,244+ty),(108,244+ty)],fill=GOLD,width=4); d.text((122,228+ty),'@coach.agz',font=f('JBMono-500.ttf',28),fill=GOLD)
    a1,a2='BIG PHARMA',' DOUBLE STANDARD'
    fn=f('BebasNeue.ttf',80); d.text((64,266+ty),a1,font=fn,fill=CREAM); d.text((64+d.textlength(a1,font=fn),266+ty),a2,font=fn,fill=GOLD)
    # --- cards (layered: shadow + panel + bar + header + rows)
    sh=Image.new('RGBA',(W,H),(0,0,0,0)); sd=ImageDraw.Draw(sh); any_card=False
    for ci,c in enumerate(CARDS):
        r=ease_out((t-c['rise'][0])/(c['rise'][1]-c['rise'][0]))
        if r<=0: continue
        any_card=True; off=lerp(70,0,r); al=int(255*r)
        y=c['y']+off
        sd.rounded_rectangle([64+10,y+22,1016+10,y+c['h']+22],radius=18,fill=(0,0,0,int(150*r)))
        c['_y']=y; c['_al']=al
    if any_card: im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(22)))
    for ci,c in enumerate(CARDS):
        if '_y' not in c or ease_out((t-c['rise'][0])/(c['rise'][1]-c['rise'][0]))<=0: continue
        y=c['_y']; al=c['_al']
        d.rounded_rectangle([64,y,1016,y+c['h']],radius=18,fill=PANEL+(int(al*0.96),))
        h=HAND[5 if ci==0 else 9]
        bp=ease_out((t-h['t1'])/0.22)                      # top bar draws on after header lands
        if bp>0: d.rectangle([64,y,64+952*bp,y+8],fill=c['bar']+(255,))
        if t>=h['t1']: d.text((HEAD_X,y+34),c['head'],font=f('BebasNeue.ttf',HEAD_SIZE),fill=c['hc'])
        for (rt,kind,txt) in c['rows']:
            rp=ease_out((t-rt)/0.18)
            if rp<=0: continue
            ry=y+160; rx=HEAD_X+lerp(-24,0,rp)
            col=GREEN if kind=='v' else RED
            draw_mark(d,kind,rx,ry+12,col+(int(255*rp),),clamp((t-rt)/0.15))
            d.text((rx+58,ry),txt,font=f('DMSans-700.ttf',54),fill=CREAM+(int(255*rp),))
    # --- stamp: heavy slam with recoil
    if t>=STAMP_T-0.10:
        sp_=clamp((t-(STAMP_T-0.10))/0.10)  # 3 frames in
        sc_=lerp(1.6,1.0,ease_out(sp_)) if sp_<1 else 1.0+0.05*math.exp(-(t-STAMP_T)*14)*math.cos((t-STAMP_T)*40)
        st=Image.new('RGBA',(560,120),(0,0,0,0)); s2=ImageDraw.Draw(st)
        s2.rounded_rectangle([0,0,559,119],radius=10,fill=RED+(255,))
        fn=f('BebasNeue.ttf',84); tw=s2.textlength('NO QUESTIONS ASKED',font=fn); s2.text(((560-tw)/2,14),'NO QUESTIONS ASKED',font=fn,fill=CREAM)
        st=st.resize((int(560*sc_),int(120*sc_)),Image.LANCZOS).rotate(4,expand=True,resample=Image.BICUBIC)
        a=st.split()[3].point(lambda v:int(v*clamp(sp_*1.5)))
        st.putalpha(a)
        cx,cy=700,1185
        ov.alpha_composite(st,(int(cx-st.width/2),int(cy-st.height/2)))
    # --- captions (every word, red block on active word)
    gi=group_at(t)
    if gi is not None:
        ws,wd,xs,size=cap_layout(gi,d); g0=gstart(gi)
        g0=max(g0,HAND[gi-1]['t0']+0.067) if gi-1 in HAND else g0
        pop=clamp((t-g0)/0.13); s=1+0.08*math.sin(pop*math.pi)*(1-pop*0.3) if pop<1 else 1
        s=lerp(0.86,1,ease_out(pop/0.6)) if pop<0.6 else s
        cap=Image.new('RGBA',(W,300),(0,0,0,0)); cd=ImageDraw.Draw(cap); shd=Image.new('RGBA',(W,300),(0,0,0,0)); sdd=ImageDraw.Draw(shd)
        aw=active_word(t,gi)-G[gi][0]
        fn=f('BebasNeue.ttf',size)
        # red block slides between words over 3 frames
        ws_t=[words[i]['s'] for i in range(G[gi][0],G[gi][1])]
        prev=max(0,aw-1); bt=ease_out((t-ws_t[aw])/0.08) if aw>0 else 1
        bx0=lerp(xs[prev],xs[aw],bt)-18; bx1=lerp(xs[prev]+wd[prev],xs[aw]+wd[aw],bt)+18
        for i,(w_,x_) in enumerate(zip(ws,xs)):
            if i!=aw: sdd.text((x_+4,40+6),w_,font=fn,fill=(0,0,0,210))
        cap.alpha_composite(shd.filter(ImageFilter.GaussianBlur(6)))
        cd.rounded_rectangle([bx0,40+size*0.02,bx1,40+size*0.98],radius=12,fill=RED+(255,))
        for i,(w_,x_) in enumerate(zip(ws,xs)):
            cd.text((x_,40),w_,font=fn,fill=CREAM,stroke_width=0 if i==aw else 3,stroke_fill=(0,0,0))
        if abs(s-1)>0.002:
            cap=cap.resize((int(W*s),int(300*s)),Image.BICUBIC); ox=int((W-cap.width)/2); oy=int(CAP_Y-40-(cap.height-300)/2)
        else: ox,oy=0,CAP_Y-40
        ov.alpha_composite(cap,(max(0,ox),oy)) if ox>=0 else ov.alpha_composite(cap.crop((-ox,0,-ox+W,cap.height)),(0,oy))
    # --- handoffs: caption phrase flies into card header
    for gi_,h in HAND.items():
        if h['t0']<=t<h['t1']:
            c=CARDS[h['card']]; p=ease_io((t-h['t0'])/(h['t1']-h['t0']))
            ws,wd,xs,size=cap_layout(gi_,d)
            r=ease_out((t-c['rise'][0])/(c['rise'][1]-c['rise'][0])); cy_=c['y']+lerp(70,0,r)
            hf=f('BebasNeue.ttf',HEAD_SIZE); hsp=d.textlength(' ',font=hf)
            hx=[]; xx=HEAD_X
            for w_ in ws: hx.append(xx); xx+=d.textlength(w_,font=hf)+hsp
            sz=lerp(size,HEAD_SIZE,p); arc=-90*math.sin(p*math.pi); col=lc(CREAM,c['hc'],p)
            fa=1-clamp((t-h['t0'])/0.10)
            pv=ease_out((t-h['t0'])/(h['t1']-h['t0']))
            if fa>0:   # red block travels with the last word and fades over 3 frames
                li=len(ws)-1; lx=lerp(xs[li],hx[li],p); ly=lerp(CAP_Y,cy_+34,pv)+arc*(1-pv)
                lw=d.textlength(ws[li],font=f('BebasNeue.ttf',sz))
                d.rounded_rectangle([lx-18,ly+sz*0.02,lx+lw+18,ly+sz*0.98],radius=12,fill=RED+(int(255*fa),))
            for i,w_ in enumerate(ws):
                pv=ease_out((t-h['t0'])/(h['t1']-h['t0']))
                d.text((lerp(xs[i],hx[i],p),lerp(CAP_Y,cy_+34,pv)+arc*(1-pv)),w_,font=f('BebasNeue.ttf',sz),fill=col+(255,),stroke_width=int(round(3*(1-p))),stroke_fill=(0,0,0))
    im.alpha_composite(ov)
    out=im.convert('RGB')
    # 2-frame shake on stamp impact (object hit, frame jolts slightly)
    k=round((t-STAMP_T)*FPS)
    if k in (0,1):
        dx=[8,-5][k]; z=1.025; big=out.resize((int(W*z),int(H*z)),Image.BICUBIC); ox=(big.width-W)//2-dx; oy=(big.height-H)//2; out=big.crop((ox,oy,ox+W,oy+H)); ImageDraw.Draw(out).rectangle([0,0,7,H],fill=GOLD)
    return out

dec=subprocess.Popen(['ffmpeg','-v','error','-i',T+'raw.mp4','-t',str(DUR),'-vf',f'fps={FPS},scale={W}:{H}','-f','rawvideo','-pix_fmt','rgb24','-'],stdout=subprocess.PIPE)
enc=subprocess.Popen(['ffmpeg','-v','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-','-vf','scale=720:1280:flags=lanczos','-c:v','libx264','-crf','18','-preset','medium','-pix_fmt','yuv420p',T+'video_only.mp4'],stdin=subprocess.PIPE)
for n in range(N):
    buf=dec.stdout.read(W*H*3)
    if len(buf)<W*H*3: print('short at',n); break
    src=Image.frombuffer('RGB',(W,H),buf)
    enc.stdin.write(frame(src,n/FPS).tobytes())
enc.stdin.close(); enc.wait(); dec.kill()
print('frames',N)
