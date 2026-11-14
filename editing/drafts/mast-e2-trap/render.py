# @coach.agz Reel renderer — "Masteron & the E2 trap" (1080x1920, 30 fps)
# usage: render.py <workdir> stills t1 t2 ...   |   render.py <workdir> chunk n0 n1 out.mp4
import json, subprocess, sys, math, re
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
WD=sys.argv[1].rstrip('/')+'/'; F=WD+'../fonts/'
W,H=1080,1920; FPS=30
WORDS=json.load(open(WD+'words_final.json'))
CUTS=json.load(open(WD+'cuts.json'))
DUR=float(subprocess.run(['ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0',WD+'assembled.mov'],capture_output=True,text=True).stdout)
GOLD=(201,169,110); CREAM=(244,241,234); NAVY=(14,17,23); MUTED=(184,184,188)
RED=(255,34,28); VGOLD=(255,194,26); CYAN=(0,229,255); GREEN=(30,255,110); DEEP=(2,3,8); INK=(6,8,14); WHITE=(255,255,255)
BLUE=(79,163,224); AMBER=(240,160,48); SGREEN=(60,203,106); DIM=(70,74,90); GRID=(34,38,52)
MONO='JBMono-500.ttf'; MONOB='JBMono-700.ttf'; BEB='BebasNeue.ttf'; DMB='DMSans-700.ttf'; DMR='DMSans-400.ttf'; BAR='Barlow-600.ttf'; BARX='Barlow-800.ttf'
_fc={}
def f(n,s):
    k=(n,int(s))
    if k not in _fc: _fc[k]=ImageFont.truetype(F+n,int(s))
    return _fc[k]
def clamp(x,a=0,b=1): return max(a,min(b,x))
def expo(x): x=clamp(x); return 1 if x>=1 else 1-2**(-10*x)
def ease_io(x): x=clamp(x); return 4*x**3 if x<.5 else 1-(-2*x+2)**3/2
def lerp(a,b,t): return a+(b-a)*t
def A(c,a): return tuple(c[:3])+(int(clamp(a)*255),)
def appear(t,t0,dur=0.16): return expo((t-t0)/dur)

# ---------------- word anchors ----------------
def norm(s): return re.sub(r"[^a-z0-9']","",s.lower())
def K(key,near,off=0.0):
    """start time of the word containing `key` closest to `near` (cut timeline)"""
    ks=norm(key); best=None
    for w in WORDS:
        if ks in norm(w['w']):
            if best is None or abs(w['s']-near)<abs(best['s']-near): best=w
    if best is None or abs(best['s']-near)>3.0: raise SystemExit(f'anchor {key}@{near} not found (best {best})')
    return best['s']+off
def KE(key,near): return [w for w in WORDS if w['s']==K(key,near)][0]['e']

# ---------------- face track ----------------
FT=json.load(open(WD+'faces.json'))
def _face_arrays():
    ts=np.array([r[0] for r in FT]); ok=np.array([r[1] is not None for r in FT])
    vals=np.array([[r[1]+r[3]/2,r[2]+r[4]/2,r[4]] if r[1] is not None else [np.nan]*3 for r in FT],float)
    bounds=[0]+CUTS+[DUR+1]; out=np.zeros_like(vals)
    for a,b in zip(bounds,bounds[1:]):
        m=(ts>=a)&(ts<b); idx=np.where(m)[0]
        if not len(idx): continue
        seg=vals[idx]; good=~np.isnan(seg[:,0])
        if good.sum()==0: seg[:]=[600,950,470]
        else:
            for c in range(3): seg[:,c]=np.interp(np.arange(len(seg)),np.where(good)[0],seg[good,c])
        k=7; pad=np.pad(seg,((k,k),(0,0)),mode='edge')
        med=np.array([np.median(pad[i:i+2*k+1],axis=0) for i in range(len(seg))])
        pad=np.pad(med,((k,k),(0,0)),mode='edge'); sm=np.array([pad[i:i+2*k+1].mean(axis=0) for i in range(len(seg))])
        out[idx]=sm
    return ts,out
FTS,FV=_face_arrays()
def face(t):
    i=int(np.clip(np.searchsorted(FTS,t),0,len(FTS)-1)); cx,cy,h=FV[i]
    return cx,cy,h   # chin ~ cy+0.6h, cap-top ~ cy-1.05h

# ---------------- primitives ----------------
GL=None
def brackets(d,x0,y0,x1,y1,col,L=34,w=4):
    for (cx,cy,sx,sy) in [(x0,y0,1,1),(x1,y0,-1,1),(x0,y1,1,-1),(x1,y1,-1,-1)]:
        d.line([(cx,cy),(cx+sx*L,cy)],fill=col,width=w); d.line([(cx,cy),(cx,cy+sy*L)],fill=col,width=w)
def lit_bar(d,x0,y0,x1,y1,col,a=1.0):
    h=max(1,int(y1-y0))
    for i in range(h):
        k=i/h; c=tuple(int(min(255,v*(1.18-0.36*k)+(40 if k<0.12 else 0))) for v in col)
        d.line([(x0,y0+i),(x1,y0+i)],fill=c+(int(255*clamp(a)),))
def tag(d,x,y,label,col=RED,size=30,a=1.0,glow=True,anchor='l'):
    if a<=0: return x
    fn=f(MONOB,size); tw=d.textlength(label,font=fn); h=size+16
    if anchor=='r': x=x-tw-24
    if anchor=='c': x=x-(tw+24)/2
    lit_bar(d,x,y,x+tw+24,y+h,col,a); d.text((x+12,y+6),label,font=fn,fill=A(INK if col in (VGOLD,GREEN,CYAN) else WHITE,a))
    if GL and glow: GL.rectangle([x-4,y-4,x+tw+28,y+h+4],outline=A(col,a),width=8)
    return x+tw+24
def txt(d,x,y,s,font,col,a=1.0,anchor=None):
    if a>0: d.text((x,y),s,font=font,fill=A(col,a),anchor=anchor)
def arrow(d,x0,y0,x1,y1,col,w=5,a=1.0,L=18):
    d.line([(x0,y0),(x1,y1)],fill=A(col,a),width=w); ang=math.atan2(y1-y0,x1-x0)
    d.polygon([(x1,y1),(x1-L*math.cos(ang-0.45),y1-L*math.sin(ang-0.45)),(x1-L*math.cos(ang+0.45),y1-L*math.sin(ang+0.45))],fill=A(col,a))
def flow(d,x0,y0,x1,y1,t,col,n=5,speed=0.9,a=1.0,r=7):
    for k in range(n):
        p=(t*speed+k/n)%1; x=lerp(x0,x1,p); y=lerp(y0,y1,p); fa=a*min(1,p*6,(1-p)*6)
        d.ellipse([x-r,y-r,x+r,y+r],fill=A(col,fa))
        if GL: GL.ellipse([x-r*2,y-r*2,x+r*2,y+r*2],fill=A(col,fa))
def check(d,x,y,col,s=1.0,a=1.0):
    pts=[(x,y+16*s),(x+10*s,y+28*s),(x+30*s,y+2*s)]
    d.line(pts,fill=A(col,a),width=int(6*s))
    if GL: GL.line(pts,fill=A(col,a),width=int(12*s))
def cross(d,x,y,col,s=1.0,a=1.0):
    d.line([(x,y),(x+28*s,y+28*s)],fill=A(col,a),width=int(6*s)); d.line([(x+28*s,y),(x,y+28*s)],fill=A(col,a),width=int(6*s))
    if GL: GL.line([(x,y),(x+28*s,y+28*s)],fill=A(col,a),width=12); GL.line([(x+28*s,y),(x,y+28*s)],fill=A(col,a),width=12)
def gline(d,pts,col,w=6,a=1.0,gw=14):
    if len(pts)<2: return
    d.line(pts,fill=A(col,a),width=w,joint='curve')
    if GL: GL.line(pts,fill=A(col,a),width=gw,joint='curve')
def partial(pts,p):
    """first fraction p of a polyline (by index-length)"""
    if p<=0: return pts[:1]
    segs=[math.dist(a,b) for a,b in zip(pts,pts[1:])]; tot=sum(segs); want=tot*clamp(p); out=[pts[0]]; acc=0
    for (a,b),s in zip(zip(pts,pts[1:]),segs):
        if acc+s>=want: q=(want-acc)/s if s else 0; out.append((lerp(a[0],b[0],q),lerp(a[1],b[1],q))); return out
        out.append(b); acc+=s
    return out
def node(d,x0,y0,x1,y1,title,col,a=1.0,dim=False,size=42):
    c=col if not dim else tuple(int(v*0.3) for v in col)
    d.rounded_rectangle([x0,y0,x1,y1],radius=12,fill=A((10,14,24),0.95*a),outline=A(c,a),width=4)
    if GL and not dim: GL.rounded_rectangle([x0,y0,x1,y1],radius=12,outline=A(col,a*0.8),width=8)
    txt(d,(x0+x1)/2,(y0+y1)/2+2,title,f(BEB,size),WHITE if not dim else (100,100,110),a,'mm')
def hexagon(d,cx,cy,r,col,a=1.0,label='',dim=False,size=26):
    c=col if not dim else tuple(int(v*0.3) for v in col)
    pts=[(cx+r*math.cos(math.pi/3*i+math.pi/6),cy+r*math.sin(math.pi/3*i+math.pi/6)) for i in range(6)]
    d.polygon(pts,fill=A((10,14,24),0.95*a)); d.line(pts+[pts[0]],fill=A(c,a),width=5)
    if GL and not dim: GL.line(pts+[pts[0]],fill=A(c,a*0.9),width=10)
    if label: txt(d,cx,cy+2,label,f(BEB,size),WHITE if not dim else (100,100,110),a,'mm')
def frosted(im,box,dark=0.86,blur=10):
    x0,y0,x1,y1=[int(v) for v in box]; x0=max(0,x0); y0=max(0,y0); x1=min(W,x1); y1=min(H,y1)
    if x1<=x0 or y1<=y0: return
    reg=im.crop((x0,y0,x1,y1)).convert('RGB').filter(ImageFilter.GaussianBlur(blur))
    im.paste(Image.blend(reg,Image.new('RGB',reg.size,DEEP),dark).convert('RGBA'),(x0,y0))
def grid_bg(d,x0,y0,x1,y1,step=40,a=1.0):
    for x in range(int(x0),int(x1),step): d.line([(x,y0),(x,y1)],fill=A(GRID,0.55*a),width=1)
    for y in range(int(y0),int(y1),step): d.line([(x0,y),(x1,y)],fill=A(GRID,0.55*a),width=1)
def header(d,x0,y0,x1,left,right,t,a=1.0,col=VGOLD):
    d.ellipse([x0,y0+8,x0+16,y0+24],fill=A(RED,a if int(t*4)%2==0 else a/3))
    txt(d,x0+28,y0,left,f(MONO,27),WHITE,a); fr=f(MONOB,27); txt(d,x1-d.textlength(right,font=fr),y0,right,fr,col,a)

# ---------------- timeline (anchors on the edited cut) ----------------
C=CUTS
def cut_near(t): return min(C,key=lambda c:abs(c-t))
T={}
def build_T():
    T['masteron0']=K('masteron',0.8); T['climbing0']=K('climbing',3.6); T['blind']=K('blindsided',7.0)
    T['panel1']=K('panel',10.6); T['feel1']=K('feel',12.0); T['hides']=K('hides',14.6); T['number1']=K('number',16.6)
    T['mech']=K('mechanics',24.7); T['drost']=K('drostanolone',29.0); T['dht']=K('dht',30.0); T['arom1']=K('aromatize',31.3)
    T['water']=K('water',32.5); T['harder']=K('harder',34.0); T['grain']=K('grainier',34.6); T['sep']=K('separation',35.3)
    T['notai']=K('aromatase',39.6); T['convert']=K('converting',42.4); T['serm']=K('serm',44.8); T['tissue']=K('tissue',47.6)
    T['rises']=K('rises',51.4); T['goneup']=K('gone',53.5); T['didnt']=K("didn't",55.0); T['blindfold']=K('blindfold',58.0); T['bw1']=K('blood',59.3)
    T['comingoff']=K('coming',62.6); T['block']=K('block',64.6); T['high']=K('high',66.2); T['land']=K('land',69.6); T['once']=K('once',70.5)
    T['control']=K('control',73.4); T['notafter']=K('after',75.0); T['step1']=K('one',78.6); T['sens']=K('sensitive',80.4)
    T['drop']=K('drop',82.0); T['clean']=K('clean',84.6); T['step2']=K('two',87.6); T['lag']=K('lag',88.6); T['esters']=K('esters',89.8)
    T['days']=K('days',91.7); T['behind']=K('behind',96.0); T['step3']=K('three',97.3); T['lastpin3']=K('pin',99.0)
    T['coach']=K('coach',101.7); T['twoam']=K('2',103.5); T['itch']=K('itching',104.6); T['sensitive2']=K('sensitive',105.7)
    T['freak']=K('freaking',106.6); T['bw2']=K('blood',108.2); T['roadmap']=K('roadmap',109.9); T['comment']=K('comment',110.9)
    T['panel3']=K('panel',113.6); T['titr']=K('titration',114.2)
build_T()
HOOK_END=6.0
MID=cut_near(DUR/2)

# ---------------- scenes ----------------
# layout: rail | deck | side_r (card right, footage left) | side_l | pip | strip (upper strip) | end
def sc_rail(d,t,a):  # E2 thermometer on the left rail
    x0,x1,y0,y1=56,150,600,1150
    fr=lerp(0.22,0.9,ease_io((t-T['climbing0']+0.1)/2.6))
    d.rounded_rectangle([x0-12,y0-70,x1+12,y1+70],radius=20,fill=A(DEEP,0.82*a),outline=A(VGOLD,0.6*a),width=2)
    txt(d,(x0+x1)/2,y0-38,'E2',f(BEB,52),WHITE,a,'mm')
    tube=[x0+24,y0+10,x1-24,y1-60]; d.rounded_rectangle(tube,radius=22,outline=A(WHITE,0.85*a),width=4)
    bx=(x0+x1)/2; d.ellipse([bx-40,y1-90,bx+40,y1-10],outline=A(WHITE,0.85*a),width=4)
    lvl=lerp(tube[3]-4,tube[1]+8,fr)
    lit_bar(d,tube[0]+8,lvl,tube[2]-8,tube[3]+10,RED,a); d.ellipse([bx-30,y1-80,bx+30,y1-20],fill=A(RED,a))
    if GL: GL.rectangle([tube[0]+6,lvl,tube[2]-6,tube[3]],fill=A(RED,0.8*a)); GL.ellipse([bx-38,y1-88,bx+38,y1-12],fill=A(RED,a))
    for k in range(9):
        yy=lerp(tube[3]-10,tube[1]+16,k/8); d.line([(tube[2]+6,yy),(tube[2]+(18 if k%2==0 else 12),yy)],fill=A(WHITE,0.7*a),width=2)
    # level pointer
    d.polygon([(x1+14,lvl),(x1+34,lvl-12),(x1+34,lvl+12)],fill=A(RED,a))
    if t>=T['climbing0']+0.9: tag(d,x0-10,y1+86,'RISING',RED,26,a*appear(t,T['climbing0']+0.9))
    if t>=T['blind']: tag(d,x0-10,y1+138,'UNFELT',CYAN,26,a*appear(t,T['blind']))

def sc_graph(d,t,a,ox,oy):   # dual line: panel E2 vs felt symptoms
    x0,y0,x1,y1=ox+70,oy+80,ox+930,oy+330
    header(d,ox+10,oy+6,ox+950,'E2 · PANEL vs FEEL','WEEKS ON CYCLE →',t,a)
    for k in range(5): d.line([(x0,y1-k*(y1-y0)/4),(x1,y1-k*(y1-y0)/4)],fill=A(GRID,a),width=1)
    d.line([(x0,y0-10),(x0,y1)],fill=A(DIM,a),width=3); d.line([(x0,y1),(x1,y1)],fill=A(DIM,a),width=3)
    N=40; p=clamp((t-(T['panel1']-1.2))/3.2)
    e2=[(lerp(x0,x1,i/N),y1-(y1-y0)*(0.12+0.80*((i/N)**1.6))) for i in range(N+1)]
    sy=[(lerp(x0,x1,i/N),y1-(y1-y0)*(0.13+0.025*math.sin(i*1.3)+0.02*math.sin(i*0.55))) for i in range(N+1)]
    if p>=0.999 and t>=T['hides']:   # hidden gap fill
        q=appear(t,T['hides'],0.35); poly=e2+sy[::-1]
        d.polygon(poly,fill=A(RED,0.22*q*a))
        for i in range(2,N,3):
            xa=e2[i][0]; d.line([(xa,e2[i][1]+6),(xa,sy[i][1]-6)],fill=A(RED,0.45*q*a),width=2)
        tag(d,lerp(x0,x1,0.62),lerp(e2[25][1],sy[25][1],0.45)-20,'HIDDEN',RED,30,q*a)
    gline(d,partial(sy,p),CYAN,6,a); gline(d,partial(e2,p),RED,7,a)
    if p>0:
        e=partial(e2,p)[-1]; s=partial(sy,p)[-1]
        d.ellipse([e[0]-11,e[1]-11,e[0]+11,e[1]+11],fill=A(WHITE,a)); d.ellipse([s[0]-9,s[1]-9,s[0]+9,s[1]+9],fill=A(WHITE,a))
    if t>=T['feel1']: tag(d,x1,sy[-1][1]+14,'FLAT',CYAN,24,a*appear(t,T['feel1']),anchor='r')
    if t>=T['number1']: tag(d,x1-6,e2[-1][1]-56,'STILL CLIMBING',RED,24,a*appear(t,T['number1']),anchor='r')
    ly=oy+352
    d.rectangle([x0,ly+8,x0+26,ly+22],fill=A(RED,a)); txt(d,x0+38,ly,'E2 ON YOUR BLOODWORK',f(MONO,24),CREAM,a)
    d.rectangle([x0+470,ly+8,x0+496,ly+22],fill=A(CYAN,a)); txt(d,x0+508,ly,'SIDES YOU FEEL',f(MONO,24),CREAM,a)

def steroid(d,cx,cy,s,p,col,a):
    """4-ring steroid skeleton (A-B-C hexagons + D pentagon), drawn on with p"""
    def hexpts(x,y): return [(x+s*math.cos(math.radians(30+60*i)),y+s*math.sin(math.radians(30+60*i))) for i in range(6)]
    w=s*math.sqrt(3)
    rings=[hexpts(cx-w,cy+s*0.5*1.0),hexpts(cx,cy),hexpts(cx+w,cy+s*0.5*1.0)]
    rings=[hexpts(cx-w*1.0,cy+s*1.5*0+0),hexpts(cx,cy),hexpts(cx+w*0.5,cy-s*1.5)]
    A_=hexpts(cx-w,cy); B_=hexpts(cx,cy); C_=hexpts(cx+w/2,cy-1.5*s)
    # pentagon fused to C ring's right edge
    p1=C_[5]; p2=C_[0]; mx,my=(p1[0]+p2[0])/2,(p1[1]+p2[1])/2; ang=math.atan2(p2[1]-p1[1],p2[0]-p1[0])-math.pi/2
    D_=[p1,(mx+math.cos(ang+0.0)*0+s*1.0*math.cos(ang-0.6)+ (p1[0]-mx)*0.3, my+s*1.0*math.sin(ang-0.6)+(p1[1]-my)*0.3)]
    nrm=(math.cos(ang+math.pi),math.sin(ang+math.pi))
    nrm=(-(p2[1]-p1[1]),(p2[0]-p1[0])); L=math.hypot(*nrm); nrm=(nrm[0]/L,nrm[1]/L)
    if nrm[0]<0: nrm=(-nrm[0],-nrm[1])
    tip=(mx+nrm[0]*s*1.25,my+nrm[1]*s*1.25)
    side=((p2[0]-p1[0])/s,(p2[1]-p1[1])/s)
    D_=[p1,(lerp(p1[0],tip[0],0.62)-side[0]*s*0.42,lerp(p1[1],tip[1],0.62)-side[1]*s*0.42),tip,(lerp(p2[0],tip[0],0.62)+side[0]*s*0.42,lerp(p2[1],tip[1],0.62)+side[1]*s*0.42),p2]
    D_=[p1,(p1[0]+nrm[0]*s*0.95-side[0]*s*0.15,p1[1]+nrm[1]*s*0.95-side[1]*s*0.15),tip,(p2[0]+nrm[0]*s*0.95+side[0]*s*0.15,p2[1]+nrm[1]*s*0.95+side[1]*s*0.15),p2]
    shapes=[A_+[A_[0]],B_+[B_[0]],C_+[C_[0]],D_]
    for i,sh in enumerate(shapes):
        q=clamp(p*4-i)
        if q>0: gline(d,partial(sh,q),col,4,a,10)
    return A_,B_,C_,D_

def sc_dossier(d,t,a,x0,y0,x1,y1):
    d.rounded_rectangle([x0,y0,x1,y1],radius=18,fill=A((6,8,14),0.93*a),outline=A(VGOLD,0.7*a),width=3)
    brackets(d,x0,y0,x1,y1,A(VGOLD,a),36,6)
    if GL: brackets(GL,x0,y0,x1,y1,A(VGOLD,a),36,12)
    cx=(x0+x1)/2
    txt(d,x0+26,y0+22,'COMPOUND FILE',f(MONO,24),VGOLD,a); txt(d,x1-26,y0+22,'CLASS: DHT',f(MONOB,24),CYAN,a,'ra')
    txt(d,x0+26,y0+62,'MASTERON',f(BEB,92),CREAM,a)
    if t>=T['drost']: txt(d,x0+28,y0+156,'drostanolone',f(DMB,34),MUTED,a*appear(t,T['drost'],0.2))
    # molecule
    p=clamp((t-T['drost'])/1.1)
    if p>0:
        rings=steroid(d,cx-30,y0+300,40,p,CYAN,a)
    if t>=T['dht']: tag(d,x0+26,y0+382,'DHT-DERIVED',VGOLD,26,a*appear(t,T['dht']))
    # property rows
    rows=[(T['arom1'],'AROMATIZES',False),(T['water'],'WATER',False)]
    for i,(tt,lab,ok) in enumerate(rows):
        if t<tt: continue
        aa=a*appear(t,tt); y=y0+460+i*56
        d.line([(x0+24,y-10),(x1-24,y-10)],fill=A(DIM,aa),width=2)
        txt(d,x0+26,y,lab,f(BAR,36),WHITE,aa); cross(d,x1-80,y+6,RED,1.0,aa); txt(d,x1-122,y+2,'NO' if i==0 else '0',f(MONOB,30),RED,aa,'ra')
    if t>=T['harder']-0.4:
        aa=a*appear(t,T['harder']-0.4); y=y0+582
        d.line([(x0+24,y-10),(x1-24,y-10)],fill=A(DIM,aa),width=2); txt(d,x0+26,y,'LEAN LOOK',f(MONO,24),VGOLD,aa)
        for i,(tt,lab) in enumerate([(T['harder'],'HARDER'),(T['grain'],'GRAINIER'),(T['sep'],'SEPARATION')]):
            if t>=tt:
                q=appear(t,tt,0.14); xx=x0+26+lerp(-40,0,q)
                tag(d,xx,y+40+i*0,lab,VGOLD,24,a*q) if False else None
        xs=x0+26
        for i,(tt,lab) in enumerate([(T['harder'],'HARDER'),(T['grain'],'GRAINIER'),(T['sep'],'SEPARATION')]):
            if t>=tt:
                q=appear(t,tt,0.14); yy=y+38+i*48
                check(d,xs,yy+2,GREEN,0.8,a*q); txt(d,xs+40,yy-2,lab,f(BARX,36),WHITE,a*q)

def sc_ai(d,t,a,ox,oy):   # two lanes: AI vs Masteron
    header(d,ox+10,oy+6,ox+950,'AROMATASE · TWO WAYS','MECHANISM',t,a)
    lanes=[('AROMATASE INHIBITOR',oy+120,True),('MASTERON',oy+290,False)]
    for lab,y,blocked in lanes:
        aa=a*(appear(t,T['notai']-1.6) if not blocked else 1)
        if aa<=0: continue
        txt(d,ox+60,y-58,lab,f(MONOB,26),RED if blocked else VGOLD,aa)
        node(d,ox+60,y-20,ox+220,y+60,'TEST',CYAN,aa)
        hexagon(d,ox+420,y+20,56,VGOLD if not blocked else DIM,aa,'AROMATASE',size=22,dim=False)
        e2dim=blocked
        node(d,ox+620,y-20,ox+780,y+60,'E2',CYAN,aa,dim=e2dim)
        arrow(d,ox+226,y+20,ox+356,y+20,CYAN,5,aa); flow(d,ox+226,y+20,ox+356,y+20,t,CYAN,3,a=aa)
        if blocked:
            arrow(d,ox+484,y+20,ox+612,y+20,(40,48,60),5,aa)
            d.rounded_rectangle([ox+390,y-14,ox+450,y+54],radius=8,fill=A(RED,aa)); txt(d,ox+420,y+20,'✕',f(DMB,40),WHITE,aa,'mm')
            if GL: GL.rounded_rectangle([ox+386,y-18,ox+454,y+58],radius=10,outline=A(RED,aa),width=10)
            tag(d,ox+800,y,'STOPPED',RED,24,aa)
        else:
            arrow(d,ox+484,y+20,ox+612,y+20,CYAN,6,aa); flow(d,ox+484,y+20,ox+612,y+20,t,CYAN,4,a=aa)
            on=0.5+0.5*math.sin(t*9); d.ellipse([ox+470,y-50,ox+488,y-32],fill=A(GREEN,aa*(0.6+0.4*on)))
            if t>=T['convert']: tag(d,ox+800,y,'RUNNING',GREEN,24,aa*appear(t,T['convert']))
    # verdict stamp on Masteron lane
    if t>=T['notai']:
        q=expo((t-T['notai'])/0.10); s=lerp(1.5,1.0,q); aa=a*q
        st=Image.new('RGBA',(420,110),(0,0,0,0)); sd=ImageDraw.Draw(st)
        sd.rectangle([4,4,415,105],outline=A(RED,1),width=7); sd.text((210,58),'NOT AN AI',font=f(BEB,82),fill=A(RED,1),anchor='mm')
        st=st.rotate(-7,expand=True,resample=Image.BICUBIC); s*=0.72; st=st.resize((int(st.width*s),int(st.height*s)),Image.BICUBIC)
        st.putalpha(st.split()[3].point(lambda v:int(v*aa)))
        d._image.alpha_composite(st,(int(ox+830-st.width/2),int(oy+210-st.height/2)))
        if GL: GL.rectangle([ox+830-205*s,oy+210-55*s,ox+830+205*s,oy+210+55*s],outline=A(RED,aa*0.8),width=10)

def sc_shield(d,t,a,ox,oy):   # SERM-like: blocked at tissue, systemic still rises
    header(d,ox+10,oy+6,ox+950,'BLOOD vs TISSUE','SERM-LIKE',t,a)
    # blood vessel channel (left)
    vx0,vx1,vy0,vy1=ox+40,ox+200,oy+70,oy+400
    d.rounded_rectangle([vx0,vy0,vx1,vy1],radius=60,outline=A(RED,0.7*a),width=4,fill=A((30,4,8),0.6*a))
    txt(d,(vx0+vx1)/2,vy1+26,'BLOOD',f(MONOB,24),RED,a,'mm')
    for k in range(9):
        p=(t*0.35+k/9)%1; yy=lerp(vy1-20,vy0+20,p); xx=(vx0+vx1)/2+28*math.sin(k*2.1+t*2)
        d.ellipse([xx-9,yy-9,xx+9,yy+9],fill=A(VGOLD,a));
        if GL: GL.ellipse([xx-14,yy-14,xx+14,yy+14],fill=A(VGOLD,a))
    # particles travelling to tissue and bouncing off shield
    sx=ox+560; shield_on=t>=T['tissue']-0.3; sp=appear(t,T['tissue']-0.3,0.25)
    for k in range(6):
        p=(t*0.7+k/6)%1; yy=oy+120+k*45
        if not shield_on or p<0.55:
            xx=lerp(vx1+10,ox+640,p if not shield_on else p/0.55*0.55*((sx-12-vx1-10)/(0.55*(ox+640-vx1-10)))) if False else lerp(vx1+10,ox+640,p)
            if shield_on and xx>sx-14:  # bounce
                back=(xx-(sx-14)); xx=sx-14-back*1.4; yy+= -back*0.3
        else:
            q=(p-0.55)/0.45; xx=sx-14-(lerp(vx1+10,ox+640,p)-(sx-14))*1.4; yy+=-(lerp(vx1+10,ox+640,p)-(sx-14))*0.3
        if xx<vx1+4: continue
        d.ellipse([xx-8,yy-8,xx+8,yy+8],fill=A(VGOLD,a*0.95))
    # tissue / receptors (right)
    tx0=ox+600; d.rounded_rectangle([tx0,oy+70,ox+930,oy+400],radius=24,outline=A(CYAN,0.6*a),width=3,fill=A((0,30,40),0.35*a))
    txt(d,(tx0+ox+930)/2,oy+426,'TISSUE · RECEPTORS',f(MONOB,24),CYAN,a,'mm')
    for i in range(4):
        ry=oy+105+i*72; rx=tx0+40
        d.arc([rx,ry,rx+58,ry+58],90,270,fill=A(CYAN,a),width=5)
        filled = (not shield_on) and (int(t*3+i)%2==0)
        if filled: d.ellipse([rx+14,ry+14,rx+44,ry+44],fill=A(VGOLD,a))
    if shield_on:
        d.arc([sx-120,oy+60,sx+40,oy+410],-70,70,fill=A(CYAN,a*sp),width=10)
        if GL: GL.arc([sx-120,oy+60,sx+40,oy+410],-70,70,fill=A(CYAN,a*sp),width=26)
        tag(d,tx0+130,oy+140,'BLOCKED',CYAN,24,a*sp)
    # meters
    mx=tx0+130;
    sym=0.7 if not shield_on else lerp(0.7,0.12,expo((t-T['tissue'])/0.5))
    txt(d,mx,oy+230,'SIDES',f(MONO,22),CREAM,a); d.rectangle([mx,oy+262,ox+910,oy+290],outline=A(DIM,a),width=2); lit_bar(d,mx+3,oy+265,lerp(mx+3,ox+907,sym),oy+287,CYAN,a)
    sysv=lerp(0.45,0.95,expo((t-T['rises']+0.3)/0.8)) if t>=T['rises']-0.3 else 0.45
    txt(d,mx,oy+310,'SYSTEMIC E2',f(MONO,22),CREAM,a); d.rectangle([mx,oy+342,ox+910,oy+370],outline=A(DIM,a),width=2); lit_bar(d,mx+3,oy+345,lerp(mx+3,ox+907,sysv),oy+367,RED,a)
    if GL: GL.rectangle([mx+3,oy+345,lerp(mx+3,ox+907,sysv),oy+367],fill=A(RED,a*0.7))
    if t>=T['rises']: txt(d,ox+910,oy+300,'▲ RISING',f(MONOB,24),RED,a*appear(t,T['rises']),'ra')

def gauge(d,cx,cy,r,val,label,a,t,needle_col=WHITE):
    # spectrum arc: blue → green → amber → red
    stops=[(0,BLUE),(0.35,SGREEN),(0.65,AMBER),(1.0,RED)]
    def col_at(v):
        for (p0,c0),(p1,c1) in zip(stops,stops[1:]):
            if v<=p1: q=(v-p0)/(p1-p0); return tuple(int(lerp(c0[i],c1[i],q)) for i in range(3))
        return RED
    for k in range(60):
        v0=k/60; a0=180+v0*180; a1=180+(k+1)/60*180+0.6
        d.arc([cx-r,cy-r,cx+r,cy+r],a0,a1,fill=A(col_at(v0),a),width=26)
    if GL: GL.arc([cx-r,cy-r,cx+r,cy+r],180+val*180-8,180+val*180+8,fill=A(col_at(val),a),width=40)
    for k in range(11):
        ang=math.radians(180+k*18); d.line([(cx+(r-40)*math.cos(ang),cy+(r-40)*math.sin(ang)),(cx+(r-54 if k%5 else r-64)*math.cos(ang),cy+(r-54 if k%5 else r-64)*math.sin(ang))],fill=A(WHITE,0.7*a),width=3)
    ang=math.radians(180+val*180); L=r-30
    d.line([(cx,cy),(cx+L*math.cos(ang),cy+L*math.sin(ang))],fill=A(needle_col,a),width=7)
    d.ellipse([cx-16,cy-16,cx+16,cy+16],fill=A(needle_col,a))
    txt(d,cx,cy+44,label,f(MONOB,26),CREAM,a,'mm')

def sc_gauges(d,t,a,ox,oy):
    header(d,ox+10,oy+6,ox+950,'READOUT','PANEL vs FEEL',t,a)
    ga=appear(t,T['goneup']-0.6)
    v1=lerp(0.3,0.9,expo((t-T['goneup'])/0.7)) if t>=T['goneup'] else 0.3
    jit=0.01*math.sin(t*23) if t>=T['goneup']+0.7 else 0
    gauge(d,ox+250,oy+300,190,v1+jit,'E2 · BLOODWORK',a*ga,t)
    v2=0.18+0.01*math.sin(t*5)
    gauge(d,ox+710,oy+300,190,v2,'SIDES · FELT',a*appear(t,T['didnt']-0.5),t)
    if t>=T['goneup']+0.5: tag(d,ox+250,oy+100,'HIGH',RED,28,a*appear(t,T['goneup']+0.5),anchor='c')
    if t>=T['didnt']: tag(d,ox+710,oy+100,'LOW',BLUE,28,a*appear(t,T['didnt']),anchor='c')
    if t>=T['blindfold']:
        q=expo((t-T['blindfold'])/0.14); x1=lerp(ox+510,ox+920,q)
        lit_bar(d,ox+510,oy+190,x1,oy+262,(20,20,24),a); d.rectangle([ox+510,oy+190,x1,oy+262],outline=A(RED,a),width=3)
        if q>0.6: txt(d,ox+715,oy+226,'BLIND SPOT',f(BEB,52),RED,a,'mm')
        if GL: GL.rectangle([ox+506,oy+186,x1+4,oy+266],outline=A(RED,a*q),width=10)
    if t>=T['bw1']:
        tag(d,ox+480,oy+392,'READ THE PANEL, NOT THE FEEL',VGOLD,26,a*appear(t,T['bw1']),anchor='c')

def sc_offcycle(d,t,a,ox,oy):   # PiP takeover chart: block comes off, symptoms land
    header(d,ox+10,oy+6,ox+950,'COMING OFF MASTERON','TIMELINE',t,a)
    x0,y0,x1,y1=ox+70,oy+80,ox+930,oy+380; xp=lerp(x0,x1,0.55)
    for k in range(5): d.line([(x0,y1-k*(y1-y0)/4),(x1,y1-k*(y1-y0)/4)],fill=A(GRID,a),width=1)
    d.line([(x0,y0-10),(x0,y1)],fill=A(DIM,a),width=3); d.line([(x0,y1),(x1,y1)],fill=A(DIM,a),width=3)
    # masteron block band
    boff=appear(t,T['block'],0.6)
    bx1=lerp(xp+80,xp,boff)
    d.rectangle([x0+3,y0,bx1,y1-3],fill=A(CYAN,0.12*a));
    for xx in range(int(x0)+10,int(bx1),26): d.line([(xx,y0),(xx-30 if xx-30>x0 else x0,y0+30)],fill=A(CYAN,0.25*a),width=2)
    txt(d,x0+16,y0+8,'MASTERON BLOCK',f(MONOB,24),CYAN,a)
    # last pin marker
    d.line([(xp,y0-20),(xp,y1)],fill=A(VGOLD,a),width=4); tag(d,xp,y1+12,'LAST PIN',VGOLD,24,a,anchor='c')
    if GL: GL.line([(xp,y0-20),(xp,y1)],fill=A(VGOLD,a),width=10)
    if t>=T['block']: tag(d,xp+16,y0+8,'BLOCK OFF',RED,24,a*appear(t,T['block']))
    # E2 line (high, stays high)
    N=40; prog=clamp((t-(T['comingoff']-1.0))/2.4)
    e2=[(lerp(x0,x1,i/N),y1-(y1-y0)*(0.70+0.04*math.sin(i*0.7))) for i in range(N+1)]
    hi=t>=T['high']; gline(d,partial(e2,prog),RED,8 if hi else 6,a,18 if hi else 12)
    if hi: tag(d,x0+16,e2[3][1]+26,'E2 STILL HIGH · FROM TEST',RED,24,a*appear(t,T['high']))
    # symptoms: low under block, then spike after last pin
    land=T['land']; sp=expo((t-land)/0.22) if t>=land else 0
    sym=[]
    for i in range(N+1):
        x=lerp(x0,x1,i/N); base=0.12+0.015*math.sin(i*1.4)
        if x>xp+20: k=clamp((x-xp-20)/60); base=lerp(base,0.86,k*sp)
        sym.append((x,y1-(y1-y0)*base))
    gline(d,partial(sym,prog),CYAN,6,a)
    if sp>0:
        tag(d,x1,sym[-1][1]-58,'ALL AT ONCE',RED,26,a*sp,anchor='r')
    lg=oy+440
    d.rectangle([x0,lg+8,x0+26,lg+22],fill=A(RED,a)); txt(d,x0+38,lg,'E2',f(MONO,24),CREAM,a)
    d.rectangle([x0+120,lg+8,x0+146,lg+22],fill=A(CYAN,a)); txt(d,x0+158,lg,'SIDES YOU FEEL',f(MONO,24),CREAM,a)

def sc_window(d,t,a,ox,oy):    # upper strip: control window bar
    x0,x1=ox+40,ox+960; y=oy+70
    txt(d,x0,oy,'E2 CONTROL WINDOW',f(MONOB,26),VGOLD,a)
    xp=lerp(x0,x1,0.6); p=expo((t-T['control']+0.2)/0.5)
    lit_bar(d,x0,y,lerp(x0,xp,p),y+44,GREEN,a)
    if GL: GL.rectangle([x0,y,lerp(x0,xp,p),y+44],outline=A(GREEN,a),width=8)
    txt(d,x0+16,y+8,'BEFORE',f(MONOB,26),INK,a*p)
    if t>=T['notafter']:
        q=expo((t-T['notafter'])/0.15)
        lit_bar(d,xp,y,lerp(xp,x1,q),y+44,RED,a)
        if GL: GL.rectangle([xp,y,lerp(xp,x1,q),y+44],outline=A(RED,a),width=8)
        txt(d,xp+16,y+8,'AFTER = LATE',f(MONOB,26),WHITE,a*q)
    d.line([(xp,y-16),(xp,y+60)],fill=A(WHITE,a),width=4); txt(d,xp,y+82,'LAST PIN',f(MONOB,22),WHITE,a,'mm')

LABDOC=None
def make_lab():
    im=Image.new('RGBA',(380,520),(236,236,232,255)); d=ImageDraw.Draw(im)
    for yy in range(0,520,4): d.line([(0,yy),(380,yy)],fill=(226,226,222,255))
    d.rectangle([0,0,380,62],fill=(210,10,20,255)); d.text((16,14),'LAB ORDER',font=f(MONOB,30),fill=WHITE)
    d.text((16,76),'HORMONE PANEL · REQ',font=f(MONO,20),fill=(90,90,100))
    rows=[('Estradiol, Sensitive','LC/MS-MS'),('Testosterone, Total',''),('SHBG',''),('CBC','')]
    for i,(k,s) in enumerate(rows):
        y=120+i*70; d.rectangle([16,y+4,40,y+28],outline=(60,60,70),width=3)
        d.text((54,y),k,font=f(DMB if i==0 else DMR,26),fill=(30,30,40))
        if s: d.text((54,y+32),s,font=f(MONO,18),fill=(110,110,120))
        d.line([(16,y+60),(364,y+60)],fill=(200,200,205),width=2)
    d.text((16,410),'DRAW TIMING',font=f(MONO,20),fill=(90,90,100)); d.rectangle([16,438,364,496],outline=(150,150,160),width=2)
    return im
def sc_lab(d,t,a,x0,y0,x1,y1,im):
    global LABDOC
    if LABDOC is None: LABDOC=make_lab()
    d.rounded_rectangle([x0,y0,x1,y1],radius=18,fill=A((6,8,14),0.93*a),outline=A(VGOLD,0.7*a),width=3)
    brackets(d,x0,y0,x1,y1,A(VGOLD,a),36,6)
    tag(d,x0+24,y0+24,'STEP 01',VGOLD,30,a)
    txt(d,x0+24,y0+92,'PULL THE NUMBER',f(BEB,58),CREAM,a)
    q=appear(t,T['step1']+0.2,0.3); doc=LABDOC.copy(); doc=doc.rotate(lerp(-6,-2,q),expand=True,resample=Image.BICUBIC)
    doc.putalpha(doc.split()[3].point(lambda v:int(v*a*q)))
    dx,dy=int(x0+(x1-x0-doc.width)/2), int(y0+170+lerp(40,0,q)); im.alpha_composite(doc,(dx,dy))
    d=ImageDraw.Draw(im,'RGBA')
    if t>=T['sens']:
        p=appear(t,T['sens'],0.14); bx0,by0=dx+14,dy+128
        brackets(d,bx0,by0,bx0+352,by0+70,A(RED,a*p),22,6)
        if GL: brackets(GL,bx0,by0,bx0+352,by0+70,A(RED,a*p),22,12)
        check(d,bx0+8,by0+6,(210,10,20),0.9,a*p)
    if t>=T['drop']:
        p=expo((t-T['drop'])/0.10); s=lerp(1.4,1.0,p)
        fn=f(BEB,int(40*s)); lab='BEFORE LAST MAST PIN'; tw=d.textlength(lab,font=fn)
        cx,cy=dx+doc.width/2,dy+doc.height-62
        d.rectangle([cx-tw/2-14,cy-28*s,cx+tw/2+14,cy+28*s],outline=A((210,10,20),a*p),width=5)
        d.text((cx,cy),lab,font=fn,fill=A((210,10,20),a*p),anchor='mm')
    if t>=T['clean']: tag(d,x0+24,y1-74,'CLEAN READ',GREEN,30,a*appear(t,T['clean']))
    return d

def sc_lag(d,t,a,ox,oy):    # step 2: ester clearance + lag
    header(d,ox+10,oy+6,ox+950,'STEP 02 · EXPECT THE LAG','DAYS AFTER LAST PIN →',t,a)
    x0,y0,x1,y1=ox+70,oy+90,ox+930,oy+370
    for k in range(5): d.line([(x0,y1-k*(y1-y0)/4),(x1,y1-k*(y1-y0)/4)],fill=A(GRID,a),width=1)
    d.line([(x0,y0-10),(x0,y1)],fill=A(DIM,a),width=3); d.line([(x0,y1),(x1,y1)],fill=A(DIM,a),width=3)
    for k in range(8): xx=lerp(x0,x1,k/7); d.line([(xx,y1),(xx,y1+10)],fill=A(DIM,a),width=2)
    N=50; prog=clamp((t-T['step2']-0.2)/2.0)
    mast=[(lerp(x0,x1,i/N),y1-(y1-y0)*(0.88*math.exp(-3.2*i/N)+0.04)) for i in range(N+1)]
    lag_i=int(N*0.42)
    sym=[(lerp(x0,x1,i/N),y1-(y1-y0)*(0.08 if i<lag_i else 0.08+0.78*(1-math.exp(-(i-lag_i)/6)))) for i in range(N+1)]
    poly=partial(mast,prog);
    if len(poly)>1: d.polygon(poly+[(poly[-1][0],y1),(x0,y1)],fill=A(VGOLD,0.16*a))
    gline(d,poly,VGOLD,6,a);
    if t>=T['lag']: gline(d,partial(sym,clamp((t-T['lag'])/1.6)),RED,7,a)
    txt(d,x0+18,y0-4,'MASTERON LEVEL',f(MONOB,24),VGOLD,a*appear(t,T['step2']))
    d.line([(x0,y0-30),(x0,y1)],fill=A(WHITE,a),width=4); txt(d,x0+6,y1+28,'LAST PIN',f(MONOB,22),WHITE,a)
    xl=sym[lag_i][0]
    if t>=T['esters']: tag(d,x0+470,y0-6,'CLEARS ON ITS ESTER',VGOLD,24,a*appear(t,T['esters']))
    if t>=T['days']:
        q=appear(t,T['days'],0.3); yb=y1-26
        d.line([(x0+6,yb),(lerp(x0+6,xl,q),yb)],fill=A(CYAN,a),width=4)
        if q>0.95: arrow(d,x0+6,yb,xl,yb,CYAN,4,a); txt(d,(x0+xl)/2,yb-26,'THE LAG',f(MONOB,24),CYAN,a,'mm')
        d.line([(xl,y0),(xl,y1)],fill=A(RED,a*q),width=3); txt(d,xl+12,y0+40,'SIDES SHOW UP',f(MONOB,22),RED,a*q)
    if t>=T['behind']:
        q=appear(t,T['behind']);
        tag(d,xl+10,y1-150,'REACT HERE = BEHIND',RED,22,a*q)

def sc_plan(d,t,a,ox,oy):   # step 3: plan vs 2am improvisation
    header(d,ox+10,oy+6,ox+950,'STEP 03 · DECIDE IT EARLY','PLAN vs PANIC',t,a)
    # left column: clipboard plan
    lx0,ly0,lx1,ly1=ox+20,oy+60,ox+470,oy+440
    d.rounded_rectangle([lx0,ly0,lx1,ly1],radius=16,fill=A((8,22,14),0.9*a),outline=A(GREEN,a),width=3)
    if GL: GL.rounded_rectangle([lx0,ly0,lx1,ly1],radius=16,outline=A(GREEN,a),width=8)
    txt(d,lx0+24,ly0+20,'E2 PLAN',f(BEB,58),WHITE,a)
    items=[(T['step3']+0.4,'WRITTEN DOWN'),(T['lastpin3'],'BEFORE LAST PIN'),(T['coach'],'COACH OR YOU')]
    for i,(tt,lab) in enumerate(items):
        if t>=tt:
            q=appear(t,tt); y=ly0+110+i*72
            check(d,lx0+24,y,GREEN,1.0,a*q); txt(d,lx0+70,y-2,lab,f(BARX,38),WHITE,a*q)
    # right column: 2 AM clock
    rx0,ry0,rx1,ry1=ox+490,oy+60,ox+940,oy+440
    ra=a*appear(t,T['twoam']-0.4)
    if ra>0:
        d.rounded_rectangle([rx0,ry0,rx1,ry1],radius=16,fill=A((30,4,6),0.9*ra),outline=A(RED,ra),width=3)
        if GL: GL.rounded_rectangle([rx0,ry0,rx1,ry1],radius=16,outline=A(RED,ra),width=8)
        cx,cy,r=rx0+110,ry0+120,80
        d.ellipse([cx-r,cy-r,cx+r,cy+r],outline=A(RED,ra),width=6)
        for k in range(12):
            an=math.radians(k*30-90); d.line([(cx+(r-14)*math.cos(an),cy+(r-14)*math.sin(an)),(cx+(r-4)*math.cos(an),cy+(r-4)*math.sin(an))],fill=A(WHITE,ra),width=3)
        an=math.radians(2*30-90); d.line([(cx,cy),(cx+44*math.cos(an),cy+44*math.sin(an))],fill=A(WHITE,ra),width=7)
        an=math.radians(-90+ (t*40 if t<T['twoam'] else 0)); d.line([(cx,cy),(cx+64*math.cos(an),cy+64*math.sin(an))],fill=A(WHITE,ra),width=4)
        txt(d,rx0+214,ry0+60,'2:00',f(BEB,96),RED,ra); txt(d,rx0+380,ry0+108,'AM',f(BEB,46),RED,ra)
        if GL: GL.ellipse([cx-r,cy-r,cx+r,cy+r],outline=A(RED,ra),width=12)
        for i,(tt,lab) in enumerate([(T['itch'],'ITCHY NIPPLES'),(T['sensitive2'],'SENSITIVITY'),(T['freak']+0.3,'FREAK-OUT')]):
            if t>=tt:
                q=appear(t,tt); y=ry0+232+i*62; cross(d,rx0+24,y+4,RED,0.9,ra*q); txt(d,rx0+66,y-2,lab,f(BARX,36),WHITE,ra*q)

def sc_route(d,t,a,ox,oy):   # upper strip: bloodwork roadmap
    x0,x1=ox+40,ox+960; y=oy+90
    txt(d,x0,oy,'BLOODWORK = ROADMAP',f(MONOB,26),VGOLD,a)
    pts=[(x0+20,y+20),(x0+250,y-10),(x0+470,y+40),(x0+690,y+0),(x1-30,y+30)]
    p=clamp((t-T['bw2']+0.2)/1.6)
    path=partial(pts,p)
    for i in range(len(path)-1):
        a0,b0=path[i],path[i+1]; L=math.dist(a0,b0); n=int(L/22)
        for k in range(n):
            if k%2==0: d.line([(lerp(a0[0],b0[0],k/n),lerp(a0[1],b0[1],k/n)),(lerp(a0[0],b0[0],(k+1)/n),lerp(a0[1],b0[1],(k+1)/n))],fill=A(VGOLD,a),width=5)
    if GL and len(path)>1: GL.line(path,fill=A(VGOLD,a*0.6),width=10)
    for i,pt in enumerate(pts[:-1]):
        if p*4>=i:
            d.ellipse([pt[0]-16,pt[1]-16,pt[0]+16,pt[1]+16],fill=A(DEEP,a),outline=A(CYAN,a),width=4)
            txt(d,pt[0],pt[1]+40,f'PANEL {i+1}',f(MONOB,20),CYAN,a,'mm')
    end=pts[-1]
    if p>=1:
        q=appear(t,T['bw2']+1.4); d.polygon([(end[0],end[1]+18),(end[0]-18,end[1]-12),(end[0]+18,end[1]-12)],fill=A(RED,a*q)); d.ellipse([end[0]-18,end[1]-34,end[0]+18,end[1]+2],fill=A(RED,a*q))
        if GL: GL.ellipse([end[0]-22,end[1]-38,end[0]+22,end[1]+6],fill=A(RED,a*q))

LOGO=None
def sc_cta(d,t,a,ox,oy,im):
    global LOGO
    if LOGO is None:
        lg=Image.open(WD+'../logo.jpg').convert('RGB'); s=min(lg.size); lg=lg.crop(((lg.width-s)//2,(lg.height-s)//2,(lg.width+s)//2,(lg.height+s)//2)).resize((170,170),Image.LANCZOS)
        m=Image.new('L',(170,170),0); ImageDraw.Draw(m).ellipse([0,0,169,169],fill=255); lg.putalpha(m); LOGO=lg
    lg=LOGO.copy(); lg.putalpha(lg.split()[3].point(lambda v:int(v*a))); im.alpha_composite(lg,(int(ox+30),int(oy+40)))
    d=ImageDraw.Draw(im,'RGBA')
    txt(d,ox+230,oy+46,'FREE · MASTERON EXIT PLAN',f(MONOB,28),VGOLD,a)
    for i,(tt,lab) in enumerate([(T['panel3'],'FULL PANEL'),(T['titr'],'TITRATION PLAN')]):
        if t>=tt: q=appear(t,tt); check(d,ox+232,oy+96+i*52,GREEN,0.85,a*q); txt(d,ox+276,oy+90+i*52,lab,f(BARX,38),WHITE,a*q)
    if t>=T['comment']:
        b=expo((t-T['comment'])/0.12); s=lerp(1.15,1.0,b)
        fn=f(BEB,int(92*s)); label='COMMENT  "MASTERON"'; tw=d.textlength(label,font=fn); x=ox+480-tw/2-24; y=oy+230
        lit_bar(d,x,y,x+tw+48,y+int(108*s),VGOLD,a*b); d.text((x+24,y+8),label,font=fn,fill=A(INK,a*b))
        if GL: GL.rectangle([x-4,y-4,x+tw+52,y+int(108*s)+4],outline=A(VGOLD,a*b),width=12)
    txt(d,ox+480,oy+392,'FOR RESEARCH & EDUCATIONAL PURPOSES ONLY',f(MONO,20),(124,124,130),a,'mm')
    return d

def sc_chapter(d,t,a,ox,oy):   # small chapter marker before the mechanism file
    q=expo((t-T['mech']+0.3)/0.3)
    d.line([(8,oy+22),(lerp(8,ox+300,q),oy+22)],fill=A(GOLD,a),width=4)
    if q>0.5: tag(d,ox+320,oy,'PART 01 · MECHANISM',VGOLD,28,a*clamp((q-0.5)*2))

# scene list: (t0, t1, layout, fn, params)
def S():
    L=[]
    L.append((T['climbing0']-0.35, cut_near(7.97), 'rail', sc_rail))
    L.append((cut_near(7.97), cut_near(17.33), 'deck', sc_graph))
    L.append((T['mech']-0.4, cut_near(27.53), 'strip_low', sc_chapter))
    L.append((cut_near(27.53), cut_near(36.43), 'side_r', sc_dossier))
    L.append((cut_near(36.43), T['serm']-0.5, 'deck', sc_ai))
    L.append((T['serm']-0.5, cut_near(52.6), 'deck', sc_shield))
    L.append((cut_near(52.6), cut_near(60.6), 'deck', sc_gauges))
    L.append((cut_near(60.6), cut_near(71.27), 'pip', sc_offcycle))
    L.append((T['control']-0.4, cut_near(78.17), 'strip', sc_window))
    L.append((cut_near(78.17), cut_near(87.23), 'side_l', sc_lab))
    L.append((cut_near(87.23), cut_near(97.07), 'deck', sc_lag))
    L.append((cut_near(97.07), T['bw2']-0.3, 'deck', sc_plan))
    L.append((T['bw2']-0.3, T['comment']-0.25, 'strip', sc_route))
    L.append((T['comment']-0.25, DUR+1, 'deck', sc_cta))
    return L
SCENES=S()
def active(t):
    for sc in SCENES:
        if sc[0]<=t<sc[1]: return sc
    return None

# ---------------- captions ----------------
FIX={'mastron':'MASTERON','masteron':'MASTERON','drostanolone':'DROSTANOLONE','serm':'SERM','e2':'E2','2am':'2AM'}
def build_groups():
    G=[];cur=[]
    for i,x in enumerate(WORDS):
        if cur:
            prev=WORDS[cur[-1]]
            if len(cur)>=3 or x['s']-prev['e']>0.28 or prev['w'][-1] in '.,?!' or any(prev['e']<=c<=x['s']+0.02 for c in CUTS): G.append(cur); cur=[]
        cur.append(i)
    if cur: G.append(cur)
    return G
GROUPS=build_groups()
def group_at(t):
    lo=None
    for g in GROUPS:
        if WORDS[g[0]]['s']<=t+1e-6: lo=g
        else: break
    if lo is None: return None
    end=WORDS[lo[-1]]['e']+0.5
    nxt=[g for g in GROUPS if WORDS[g[0]]['s']>WORDS[lo[0]]['s']]
    if t>end and (not nxt or WORDS[nxt[0][0]]['s']>t): return None
    return lo
def cap_word(w):
    k=norm(w);
    if k in FIX: return FIX[k]
    return w.upper().rstrip(',.!?')
def captions(im,t,lane_y,maxsize=124):
    g=group_at(t)
    if not g: return
    d=ImageDraw.Draw(im,'RGBA')
    ws=[cap_word(WORDS[i]['w']) for i in g]
    size=maxsize
    while True:
        fn=f(BEB,size); sp=d.textlength(' ',font=fn)+14; wd=[d.textlength(w,font=fn) for w in ws]; tot=sum(wd)+sp*(len(ws)-1)
        if tot<=900: break
        size-=4
    xs=[];x=(W-tot)/2
    for w_ in wd: xs.append(x); x+=w_+sp
    act=0
    for k,i in enumerate(g):
        if WORDS[i]['s']<=t: act=k
    g0=WORDS[g[0]]['s']; s=lerp(0.9,1,expo((t-g0)/0.10))
    CH=int(size*1.5)
    cap=Image.new('RGBA',(W,CH),(0,0,0,0)); cd=ImageDraw.Draw(cap); shd=Image.new('RGBA',(W,CH),(0,0,0,0)); sd=ImageDraw.Draw(shd)
    prev=max(0,act-1); bt=expo((t-WORDS[g[act]]['s'])/0.07) if act>0 else 1
    bx0=lerp(xs[prev],xs[act],bt)-16; bx1=lerp(xs[prev]+wd[prev],xs[act]+wd[act],bt)+16
    for k,(w_,x_) in enumerate(zip(ws,xs)): sd.text((x_+4,size*0.22+6),w_,font=fn,fill=(0,0,0,220))
    cap.alpha_composite(shd.filter(ImageFilter.GaussianBlur(7)))
    lit_bar(cd,bx0,size*0.22,bx1,size*0.22+size*0.96,RED)
    for k,(w_,x_) in enumerate(zip(ws,xs)): cd.text((x_,size*0.22),w_,font=fn,fill=CREAM,stroke_width=0 if k==act else 3,stroke_fill=(0,0,0))
    if abs(s-1)>0.002:
        c2=cap.resize((int(W*s),int(CH*s)),Image.BICUBIC); ox=int((W-c2.width)/2); oy=int(lane_y-(c2.height-CH)/2); im.alpha_composite(c2,(ox,max(0,oy)))
    else: im.alpha_composite(cap,(0,int(lane_y)))

# ---------------- text hook + band ----------------
HOOK=[('','MASTERON',' hides symptoms'),('not the E2 number','','')]
def text_hook(im,t):
    if t>=HOOK_END+0.15: return
    a=1.0 if t<HOOK_END else 1-(t-HOOK_END)/0.15
    d=ImageDraw.Draw(im,'RGBA'); fn=f(DMB,68); fs=f(DMB,68)
    l1=[('MASTERON',VGOLD),(' hides symptoms',WHITE)]; l2=[('not the E2 number',WHITE)]
    def wid(parts): return sum(d.textlength(s,font=fn) for s,_ in parts)
    w1,w2=wid(l1),wid(l2); bw=max(w1,w2)+64; y=286
    bx0=(W-bw)/2; d.rounded_rectangle([bx0,y,bx0+bw,y+204],radius=26,fill=A((0,0,0),0.86*a))
    d.rounded_rectangle([bx0,y,bx0+bw,y+204],radius=26,outline=A(VGOLD,0.55*a),width=3)
    for parts,yy,w_ in [(l1,y+20,w1),(l2,y+106,w2)]:
        x=(W-w_)/2
        for s,c in parts:
            d.text((x,yy),s,font=fn,fill=A(c,a)); x+=d.textlength(s,font=fn)
    if GL: GL.rounded_rectangle([bx0,y,bx0+bw,y+204],radius=26,outline=A(VGOLD,0.5*a),width=8)
def topic_band(im,t):
    if not (HOOK_END<=t<MID+0.15): return
    a=min(clamp((t-HOOK_END)/0.15),1-clamp((t-MID)/0.15))
    if a<=0: return
    d=ImageDraw.Draw(im,'RGBA')
    d.rectangle([8,212,W,330],fill=A(NAVY,0.9*a)); d.line([(8,212),(W,212)],fill=A(GOLD,0.6*a),width=2)
    d.line([(64,244),(108,244)],fill=A(GOLD,a),width=4); txt(d,122,228,'@coach.agz',f(MONO,26),GOLD,a)
    fb=f(BEB,74); txt(d,64,254,'MASTERON',fb,VGOLD,a); x=64+d.textlength('MASTERON',font=fb)+18
    txt(d,x,266,'& the hidden E2 climb',f(DMB,46),CREAM,a)

# ---------------- footage transform ----------------
def seg_of(t): return sum(1 for c in CUTS if c<=t+1e-6)
def zoom_at(t):
    if t<CUTS[0]: return 1.0 if t<T['masteron0'] else lerp(1.0,1.06,expo((t-T['masteron0'])/0.14))
    return 1.0 if seg_of(t)%2==0 else 1.09
def place_footage(src,z,ax,ay,dx,dy,fill=DEEP):
    a=1/z; c=ax-(ax+dx)/z; e=1/z; fy=ay-(ay+dy)/z
    return src.transform((W,H),Image.AFFINE,(a,0,c,0,e,fy),resample=Image.BICUBIC,fillcolor=fill)

DECK_TOP=1080; CHIN_TARGET=880
def layout_params(t,sc):
    """returns (dx,dy, extra) for current layout with eased in/out"""
    if sc is None: return 0,0
    t0,t1,lay,fn=sc
    pin=ease_io((t-t0)/0.30); pout=ease_io((t-(t1-0.30))/0.30) if t1<DUR else 0
    k=pin*(1-pout)
    on_cut_in=any(abs(t0-c)<0.02 for c in CUTS); on_cut_out=any(abs(t1-c)<0.02 for c in CUTS)
    i=SCENES.index(sc)
    if i>0 and SCENES[i-1][2]==lay and abs(SCENES[i-1][1]-t0)<0.02: on_cut_in=True
    if i+1<len(SCENES) and SCENES[i+1][2]==lay and abs(SCENES[i+1][0]-t1)<0.02: on_cut_out=True
    if on_cut_in: k=1-pout if not on_cut_out else 1.0
    if on_cut_out and not on_cut_in: k=pin
    cx,cy,h=face(t); chin=cy+0.62*h
    if lay=='deck':
        top_min=345 if t<MID+0.15 else 150
        dy=max(min(0,(DECK_TOP-170)-chin), top_min-(cy-0.5*h))
        return 0, k*min(0,dy), k
    if lay=='side_r': return -k*max(0,cx-360), 0, k
    if lay=='side_l': return k*max(0,720-cx), 0, k
    return 0,0,k

def frame(src,t):
    global GL
    sc=active(t); lay=sc[2] if sc else None
    dx,dy,k=(0,0,0) if sc is None else layout_params(t,sc)
    z=zoom_at(t); cx,cy,h=face(t)
    if lay=='deck': z=lerp(z,1.0,k)
    glow=Image.new('RGBA',(W,H),(0,0,0,0)); GL=ImageDraw.Draw(glow,'RGBA')
    if lay=='pip':
        # full takeover background, face in a framed window
        bg=Image.new('RGBA',(W,H),DEEP+(255,)); bd=ImageDraw.Draw(bg,'RGBA'); grid_bg(bd,0,0,W,H,48)
        p=k; wx0,wy0,wx1,wy1=lerp(0,230,p),lerp(0,240,p),lerp(W,850,p),lerp(H,880,p)
        full=place_footage(src,z,cx,cy,0,0)
        # crop region centred on the face, aspect of the window
        ww,wh=wx1-wx0,wy1-wy0; ch=lerp(H,h*2.75,p); cw=ch*ww/wh
        cx0=clamp(cx-cw/2,0,W-cw); cy0=clamp(cy-0.12*h-ch/2,0,H-ch)
        win=full.crop((int(cx0),int(cy0),int(cx0+cw),int(cy0+ch))).resize((int(ww),int(wh)),Image.BICUBIC)
        m=Image.new('L',win.size,0); ImageDraw.Draw(m).rounded_rectangle([0,0,win.width-1,win.height-1],radius=int(28*p),fill=255)
        bg.paste(win,(int(wx0),int(wy0)),m); im=bg
        d=ImageDraw.Draw(im,'RGBA'); brackets(d,wx0-8,wy0-8,wx1+8,wy1+8,A(VGOLD,p),40,6); brackets(GL,wx0-8,wy0-8,wx1+8,wy1+8,A(VGOLD,p),40,12)
        d.ellipse([wx0+22,wy0+22,wx0+40,wy0+40],fill=A(RED,p if int(t*4)%2==0 else p/3)); txt(d,wx0+50,wy0+18,'@coach.agz',f(MONO,24),WHITE,p)
        lay_im=Image.new('RGBA',(W,H),(0,0,0,0)); ld=ImageDraw.Draw(lay_im,'RGBA')
        sc[3](ld,t,1.0,60,1000);
        if p<1: lay_im.putalpha(lay_im.split()[3].point(lambda v:int(v*p)))
        im.alpha_composite(lay_im)
        cap_lane=wy1+6; cap_max=100
    else:
        im=place_footage(src,z,cx,cy,dx,dy).convert('RGBA')
        # soft top/bottom scrims for legibility (no grade on the footage)
        scr=np.zeros(H); yy=np.arange(H); a_=np.where(yy>1200,np.clip((yy-1200)/300,0,1)*100,0); a_=np.maximum(a_,np.where(yy<400,(1-yy/400)*110,0))
        im.alpha_composite(Image.merge('RGBA',[Image.new('L',(W,H),c) for c in NAVY]+[Image.fromarray(np.repeat(a_.astype(np.uint8)[:,None],W,1))]))
        chin=cy+0.62*h*z
        cap_lane=clamp(chin+30,1220,1330); cap_max=118
        if lay=='deck':
            chin_o=cy+dy+0.62*h*z; dtop=clamp(chin_o+170,DECK_TOP,1200)
            top=lerp(H+20,dtop,k)
            frosted(im,(0,top,W,H),0.9,14); d=ImageDraw.Draw(im,'RGBA')
            d.line([(8,top),(lerp(8,W,clamp(k*1.4)),top)],fill=A(VGOLD,1),width=4); GL.line([(8,top),(lerp(8,W,clamp(k*1.4)),top)],fill=A(VGOLD,1),width=10)
            lay_im=Image.new('RGBA',(W,H),(0,0,0,0)); ld=ImageDraw.Draw(lay_im,'RGBA')
            r=sc[3](ld,t,1.0,60,top+22) if sc[3] is not sc_cta else sc[3](ld,t,1.0,60,top+22,lay_im)
            sc_s=min(1.0,(1580-dtop)/480)
            if sc_s<0.999:
                lay_im=lay_im.resize((int(W*sc_s),int(H*sc_s)),Image.BICUBIC); pad=Image.new('RGBA',(W,H),(0,0,0,0)); pad.alpha_composite(lay_im,(int((W-lay_im.width)/2),int(top-top*sc_s))); lay_im=pad
            al=clamp(k*1.3)*appear(t,sc[0]-0.02,0.22)
            if al<1: lay_im.putalpha(lay_im.split()[3].point(lambda v:int(v*al)))
            im.alpha_composite(lay_im)
            cap_lane=clamp(cy+dy+0.62*h*z+14,600,top-140); cap_max=100
        elif lay in ('side_r','side_l'):
            x0,x1=(640,1040) if lay=='side_r' else (40,440); y0,y1=420,1190
            sl=(1-k)*(420 if lay=='side_r' else -420); x0+=sl; x1+=sl
            frosted(im,(x0,y0,x1,y1),0.9,10)
            lay_im=Image.new('RGBA',(W,H),(0,0,0,0)); ld=ImageDraw.Draw(lay_im,'RGBA')
            if sc[3] is sc_lab: sc[3](ld,t,1.0,x0,y0,x1,y1,lay_im)
            else: sc[3](ld,t,1.0,x0,y0,x1,y1)
            im.alpha_composite(lay_im)
        elif lay=='rail':
            lay_im=Image.new('RGBA',(W,H),(0,0,0,0)); ld=ImageDraw.Draw(lay_im,'RGBA'); sc[3](ld,t,1.0)
            al=clamp(k*1.5) if t<sc[1]-0.3 else k
            sl=(1-k)*-200
            if al<1: lay_im.putalpha(lay_im.split()[3].point(lambda v:int(v*al)))
            im.alpha_composite(lay_im,(int(sl),0))
        elif lay in ('strip','strip_low'):
            yb=250 if lay=='strip' else 1500-200
            if lay=='strip': frosted(im,(8,yb-20,W,yb+150),0.84*k,10)
            lay_im=Image.new('RGBA',(W,H),(0,0,0,0)); ld=ImageDraw.Draw(lay_im,'RGBA'); sc[3](ld,t,1.0,24,yb if lay=='strip' else 400)
            if k<1: lay_im.putalpha(lay_im.split()[3].point(lambda v:int(v*k)))
            im.alpha_composite(lay_im)
    text_hook(im,t); topic_band(im,t)
    if t>=MID+0.15 and lay not in ('pip','strip'):
        d=ImageDraw.Draw(im,'RGBA'); txt(d,64,236,'@coach.agz',f(MONO,26),GOLD,0.75)
    GL_=GL; GL=None
    if glow.getbbox():
        sm=glow.resize((W//4,H//4),Image.BILINEAR)
        g1=np.asarray(sm.filter(ImageFilter.GaussianBlur(3.5))).astype(np.float32)/255; g2=np.asarray(sm.filter(ImageFilter.GaussianBlur(10))).astype(np.float32)/255
        prem=np.clip(g1[...,:3]*g1[...,3:]*2.3+g2[...,:3]*g2[...,3:]*1.8,0,1)
        prem=np.asarray(Image.fromarray((prem*255).astype(np.uint8)).resize((W,H),Image.BILINEAR)).astype(np.float32)/255
        b=np.asarray(im.convert('RGB')).astype(np.float32)/255
        im=Image.fromarray(((1-(1-b)*(1-prem))*255).astype(np.uint8)).convert('RGBA')
    d=ImageDraw.Draw(im,'RGBA'); d.rectangle([0,0,7,H],fill=GOLD)
    if not (t<HOOK_END+0.15): captions(im,t,cap_lane,cap_max)
    else: captions(im,t,cap_lane,cap_max)
    out=im.convert('RGB')
    # impact shake on the heavy beats
    for tt in IMPACTS:
        kk=round((t-tt)*FPS)
        if kk in (0,1,2):
            dxs=[10,-6,3][kk]; zz=1.02; big=out.resize((int(W*zz),int(H*zz)),Image.BICUBIC); ox=(big.width-W)//2-dxs; oy=(big.height-H)//2
            out=big.crop((ox,oy,ox+W,oy+H)); ImageDraw.Draw(out).rectangle([0,0,7,H],fill=GOLD)
    return out
IMPACTS=[T['notai'],T['land'],T['comment']]

if __name__=='__main__':
    mode=sys.argv[2]
    if mode=='stills':
        import os; os.makedirs(WD+'qc',exist_ok=True)
        for tt in [float(x) for x in sys.argv[3:]]:
            subprocess.run(['ffmpeg','-v','error','-y','-ss',f'{tt:.4f}','-i',WD+'assembled.mov','-frames:v','1',WD+'qc/_src.png'])
            frame(Image.open(WD+'qc/_src.png').convert('RGB'),tt).resize((540,960),Image.LANCZOS).save(WD+f'qc/st_{tt:07.2f}.jpg',quality=88)
        sys.exit()
    if mode=='times':
        print(json.dumps({k:round(v,2) for k,v in T.items()})); print('MID',MID,'DUR',DUR)
        for s in SCENES: print(round(s[0],2),round(s[1],2),s[2],s[3].__name__)
        sys.exit()
    n0,n1=int(sys.argv[3]),int(sys.argv[4]); out=sys.argv[5]
    dec=subprocess.Popen(['ffmpeg','-v','error','-ss',f'{n0/FPS:.4f}','-i',WD+'assembled.mov','-frames:v',str(n1-n0),'-f','rawvideo','-pix_fmt','rgb24','-'],stdout=subprocess.PIPE)
    enc=subprocess.Popen(['ffmpeg','-v','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-','-c:v','libx264','-crf','16','-preset','medium','-pix_fmt','yuv420p',out],stdin=subprocess.PIPE)
    for n in range(n0,n1):
        buf=dec.stdout.read(W*H*3)
        if len(buf)<W*H*3: print('short',n); break
        enc.stdin.write(frame(Image.frombuffer('RGB',(W,H),buf),n/FPS).tobytes())
    enc.stdin.close(); enc.wait(); dec.kill(); print('done',n0,n1)
