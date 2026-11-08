"""GH Reel render: 1080x1920 30fps. Usage: render.py <scratch> stills t1 t2 ... | render.py <scratch> chunk n0 n1 out.mp4"""
import json, subprocess, sys, math
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
S=sys.argv[1]; F=S+'/fonts/'; T=S+'/work/'
W,H=1080,1920; FPS=30
TL=json.load(open(T+'timeline.json')); DUR=TL['dur']; BOUNDS=TL['bounds']
WORDS=json.load(open(T+'words_final.json'))
GOLD=(201,169,110); CREAM=(244,241,234); NAVY=(14,17,23); MUTED=(184,184,188); MUTED2=(124,124,130)
RED=(255,34,28); VGOLD=(255,194,26); CYAN=(0,229,255); GREEN=(30,255,110); DEEP=(2,3,8); INK=(6,8,14); WHITE=(255,255,255)
PANELF=(10,14,24)
_fc={}
def f(n,s):
    k=(n,int(s))
    if k not in _fc:
        if n=='MONO': fo=ImageFont.truetype(F+'JBMono-var.ttf',int(s)); fo.set_variation_by_axes([500])
        elif n=='MONOB': fo=ImageFont.truetype(F+'JBMono-var.ttf',int(s)); fo.set_variation_by_axes([800])
        elif n=='DMB': fo=ImageFont.truetype(F+'DMSans-var.ttf',int(s)); fo.set_variation_by_axes([14,700])
        elif n=='DMR': fo=ImageFont.truetype(F+'DMSans-var.ttf',int(s)); fo.set_variation_by_axes([14,400])
        elif n=='BEB': fo=ImageFont.truetype(F+'BebasNeue.ttf',int(s))
        elif n=='BC6': fo=ImageFont.truetype(F+'BarlowC-600.ttf',int(s))
        elif n=='BC8': fo=ImageFont.truetype(F+'BarlowC-800.ttf',int(s))
        _fc[k]=fo
    return _fc[k]
def clamp(x,a=0,b=1): return max(a,min(b,x))
def expo(x): x=clamp(x); return 1 if x>=1 else 1-2**(-10*x)
def ease_io(x): x=clamp(x); return 4*x**3 if x<.5 else 1-(-2*x+2)**3/2
def lerp(a,b,t): return a+(b-a)*t
def A(c,a): return tuple(c[:3])+(int(clamp(a)*255),)
def appear(t,t0,dur=0.16): return expo((t-t0)/dur)
GL=None
# ---------------- primitives ----------------
def txt(d,x,y,s,font,col,a=1.0,anchor=None): d.text((x,y),s,font=font,fill=A(col,a),anchor=anchor)
def brackets(d,x0,y0,x1,y1,col,L=34,w=4):
    for (cx,cy,sx,sy) in [(x0,y0,1,1),(x1,y0,-1,1),(x0,y1,1,-1),(x1,y1,-1,-1)]:
        d.line([(cx,cy),(cx+sx*L,cy)],fill=col,width=w); d.line([(cx,cy),(cx,cy+sy*L)],fill=col,width=w)
def lit_bar(d,x0,y0,x1,y1,col,a=1.0):
    if x1<=x0: return
    h=max(1,int(y1-y0))
    for i in range(h):
        k=i/h; c=tuple(int(min(255,v*(1.18-0.36*k)+(40 if k<0.12 else 0))) for v in col)
        d.line([(x0,y0+i),(x1,y0+i)],fill=c+(int(255*a),))
def vbar(d,x0,y0,x1,y1,col,a=1.0):   # vertical lit bar: hot left edge
    if y1<=y0 or x1<=x0: return
    w=max(1,int(x1-x0))
    for i in range(w):
        k=i/w; c=tuple(int(min(255,v*(1.15-0.4*k)+(35 if k<0.1 else 0))) for v in col)
        d.line([(x0+i,y0),(x0+i,y1)],fill=c+(int(255*a),))
def tag(d,x,y,label,col=RED,size=32,a=1.0,glow=True):
    fn=f('MONO',size); tw=d.textlength(label,font=fn); h=size+16
    lit_bar(d,x,y,x+tw+24,y+h,col,a); d.text((x+12,y+5),label,font=fn,fill=A(WHITE if col not in (VGOLD,GREEN,CYAN) else INK,a))
    if GL and glow and a>0: GL.rectangle([x-4,y-4,x+tw+28,y+h+4],outline=A(col,a),width=8)
    return x+tw+24
def tri(d,x,y,s,col,a=1.0,up=True):
    if up: d.polygon([(x,y+s),(x+s,y+s),(x+s/2,y)],fill=A(col,a))
    else: d.polygon([(x,y),(x+s,y),(x+s/2,y+s)],fill=A(col,a))
def arrow(d,x0,y0,x1,y1,col,w=5,a=1.0,head=18):
    d.line([(x0,y0),(x1,y1)],fill=A(col,a),width=w)
    ang=math.atan2(y1-y0,x1-x0); L=head
    d.polygon([(x1,y1),(x1-L*math.cos(ang-0.45),y1-L*math.sin(ang-0.45)),(x1-L*math.cos(ang+0.45),y1-L*math.sin(ang+0.45))],fill=A(col,a))
    if GL and a>0: GL.line([(x0,y0),(x1,y1)],fill=A(col,a*0.8),width=w*2)
def dashed(d,x0,y0,x1,y1,col,w=4,a=1.0,dash=16,gap=12,prog=1.0):
    L=math.hypot(x1-x0,y1-y0)
    if L<1: return
    n=0; ux,uy=(x1-x0)/L,(y1-y0)/L; s=0; Lp=L*prog
    while s<Lp:
        e=min(s+dash,Lp); d.line([(x0+ux*s,y0+uy*s),(x0+ux*e,y0+uy*e)],fill=A(col,a),width=w); s+=dash+gap
def flow(d,x0,y0,x1,y1,t,col,n=5,speed=0.9,a=1.0,r=7):
    for k in range(n):
        p=(t*speed+k/n)%1; x=lerp(x0,x1,p); y=lerp(y0,y1,p); fa=a*min(1,p*6,(1-p)*6)
        d.ellipse([x-r,y-r,x+r,y+r],fill=A(col,fa))
        if GL: GL.ellipse([x-r*2,y-r*2,x+r*2,y+r*2],fill=A(col,fa))
def check(d,x,y,col,s=1.0,a=1.0):
    d.line([(x,y+16*s),(x+10*s,y+28*s),(x+30*s,y+2*s)],fill=A(col,a),width=int(6*s))
    if GL: GL.line([(x,y+16*s),(x+10*s,y+28*s),(x+30*s,y+2*s)],fill=A(col,a),width=int(12*s))
def cross(d,x,y,col,s=1.0,a=1.0):
    d.line([(x,y),(x+28*s,y+28*s)],fill=A(col,a),width=int(6*s)); d.line([(x+28*s,y),(x,y+28*s)],fill=A(col,a),width=int(6*s))
    if GL: GL.line([(x,y),(x+28*s,y+28*s)],fill=A(col,a),width=12); GL.line([(x+28*s,y),(x,y+28*s)],fill=A(col,a),width=12)
def node(d,x0,y0,x1,y1,title,sub,col,a=1.0,dim=False,size=44):
    c=col if not dim else tuple(int(v*0.35) for v in col)
    d.rounded_rectangle([x0,y0,x1,y1],radius=14,fill=A(PANELF,0.95*a),outline=A(c,a),width=4)
    if GL and not dim and a>0: GL.rounded_rectangle([x0,y0,x1,y1],radius=14,outline=A(col,a*0.8),width=8)
    fn=f('BEB',size); tw=d.textlength(title,font=fn)
    ty=(y0+y1)/2-size*0.5-(12 if sub else 0)
    d.text(((x0+x1)/2-tw/2,ty),title,font=fn,fill=A(WHITE if not dim else (110,110,120),a))
    if sub:
        fs=f('MONO',22); sw=d.textlength(sub,font=fs); d.text(((x0+x1)/2-sw/2,y1-36),sub,font=fs,fill=A(c,a))
def frosted(im,box,dark=0.86,blur=10):
    x0,y0,x1,y1=[int(v) for v in box]; x0=max(0,x0); y0=max(0,y0); x1=min(W,x1); y1=min(H,y1)
    if x1<=x0 or y1<=y0: return
    reg=im.crop((x0,y0,x1,y1)).convert('RGB').filter(ImageFilter.GaussianBlur(blur))
    im.paste(Image.blend(reg,Image.new('RGB',reg.size,DEEP),dark).convert('RGBA'),(x0,y0))
def ring(d,cx,cy,r,frac,col,a=1.0,w=8):
    d.ellipse([cx-r,cy-r,cx+r,cy+r],outline=A((50,54,68),a),width=w)
    if frac>0.005:
        d.arc([cx-r,cy-r,cx+r,cy+r],-90,-90+360*clamp(frac),fill=A(col,a),width=w)
        if GL and a>0: GL.arc([cx-r,cy-r,cx+r,cy+r],-90,-90+360*clamp(frac),fill=A(col,a),width=w*2)
def grid_axes(d,x0,y0,x1,y1,a,rows=4):
    for k in range(1,rows+1): d.line([(x0,y1-k*(y1-y0)/rows),(x1,y1-k*(y1-y0)/rows)],fill=A((38,42,58),a),width=1)
    d.line([(x0,y1),(x1,y1)],fill=A((110,114,130),a),width=3); d.line([(x0,y0-10),(x0,y1)],fill=A((110,114,130),a),width=3)
def polyline_prog(d,pts,prog,col,w=6,a=1.0):
    """draw polyline up to fraction prog of total length; return head point"""
    segs=[math.hypot(pts[i+1][0]-pts[i][0],pts[i+1][1]-pts[i][1]) for i in range(len(pts)-1)]; L=sum(segs); acc=0; target=L*clamp(prog); head=pts[0]; drawn=[pts[0]]
    for i,sl in enumerate(segs):
        if acc+sl<=target: drawn.append(pts[i+1]); acc+=sl; head=pts[i+1]
        else:
            q=(target-acc)/sl if sl else 0; head=(lerp(pts[i][0],pts[i+1][0],q),lerp(pts[i][1],pts[i+1][1],q)); drawn.append(head); break
    if len(drawn)>1:
        d.line(drawn,fill=A(col,a),width=w,joint='curve')
        if GL and a>0: GL.line(drawn,fill=A(col,a),width=w*2,joint='curve')
    return head

# ---------------- scene content ----------------
def lcd_digits(d,x,y,s,col,size,a=1.0):
    fn=f('MONOB',size); d.text((x,y),s,font=fn,fill=A(col,a))
    if GL and a>0: GL.text((x,y),s,font=fn,fill=A(col,a*0.7))
def scale_card(d,t,x0,y0,x1,y1,mode):
    """Bathroom-scale LCD. mode 'watch' (scene 1) or 'flat' (scene 4)."""
    txt(d,x0+24,y0+20,'SCALE · DAILY WEIGH-IN',f('MONO',24),VGOLD)
    # lcd window
    lx0,ly0,lx1,ly1=x0+24,y0+58,x1-24,y0+156
    d.rounded_rectangle([lx0,ly0,lx1,ly1],radius=10,fill=A((4,14,18),1),outline=A((40,70,80),1),width=3)
    if mode=='watch':
        # digits flicker while settling, land on 214.6 at 7.62
        if t<7.62:
            r=int(t*30)%7; s='%5.1f'%(213.8+0.17*r)
        else: s='214.6'
        lcd_digits(d,lx0+22,ly0+6,s,CYAN,74); txt(d,lx1-60,ly1-44,'LB',f('MONO',26),CYAN)
        # muscle progress stuck
        if t>=8.56:
            a=appear(t,8.56); y=y1-96
            txt(d,x0+24,y,'MUSCLE',f('MONO',26),CREAM,a); txt(d,x1-24,y,'LOADING',f('MONO',26),RED if int(t*3)%2 else (120,30,30),a,anchor='ra')
            d.rectangle([x0+24,y+38,x1-24,y+66],outline=A((70,74,90),a),width=2)
            fr=0.04+0.02*math.sin(t*5); lit_bar(d,x0+27,y+41,lerp(x0+27,x1-27,fr),y+63,RED,a)
    else:
        s='214.6'; lcd_digits(d,lx0+22,ly0+6,s,CYAN,74); txt(d,lx1-60,ly1-44,'LB',f('MONO',26),CYAN)
        # flat trend line under display
        a=appear(t,24.24); y=y1-92
        txt(d,x0+24,y-14,'14-DAY TREND',f('MONO',20),MUTED,a)
        pts=[(lerp(x0+30,x1-30,i/13),y+26+3*math.sin(i*1.7)) for i in range(14)]
        polyline_prog(d,pts,clamp((t-24.3)/0.7),CYAN,4,a)
        if t>=24.96: tag(d,x0+24,y1-48,'NO CHANGE',RED,22,appear(t,24.96))

def scene_scale1(d,t,box):
    scale_card(d,t,*box,'watch')
def scene_water(d,t,box):  # left: scale flat; right card handled separately
    scale_card(d,t,*box,'flat')
def muscle_xsec(d,t,box):
    x0,y0,x1,y1=box; a=1
    txt(d,x0+24,y0+20,'MUSCLE · CROSS-SECTION',f('MONO',22),VGOLD)
    cx,cy=(x0+x1)/2,(y0+y1)/2-4; R=86
    d.ellipse([cx-R,cy-R,cx+R,cy+R],outline=A(WHITE,0.9),width=4)
    if GL: GL.ellipse([cx-R,cy-R,cx+R,cy+R],outline=A(CYAN,0.6),width=8)
    fill=clamp((t-26.5)/1.6)
    rng=np.random.default_rng(3)
    pts=[]
    for i in range(19):
        ang=rng.uniform(0,2*math.pi); rr=R*0.78*math.sqrt(rng.uniform(0,1)); pts.append((cx+rr*math.cos(ang),cy+rr*math.sin(ang)))
    for i,(px,py) in enumerate(pts):
        r0=17; sw=1+0.25*expo((fill*19-i)/1.0) if fill*19>i else 1
        rr=r0*sw*0.9
        d.ellipse([px-rr,py-rr,px+rr,py+rr],outline=A((200,200,210),0.8),width=2)
        if fill*19>i:
            w_=clamp(fill*19-i); d.ellipse([px-rr+4,py-rr+4,px+rr-4,py+rr-4],fill=A(CYAN,0.55*w_))
            if GL: GL.ellipse([px-rr,py-rr,px+rr,py+rr],fill=A(CYAN,0.35*w_))
    if t>=27.02: tag(d,x0+20,y1-48,'+ INTRAMUSCULAR WATER',CYAN,20,appear(t,27.02))

def scene_fatox(d,t,box):   # GRAPH 01 line graph
    x0,y0,x1,y1=box
    txt(d,x0+40,y0+80,'FAT OXIDATION RATE',f('BEB',58),CREAM,appear(t,9.6))
    txt(d,x0+40,y0+140,'ON GH · FIRST 4 WEEKS',f('MONO',24),MUTED,appear(t,9.7))
    gx0,gy0,gx1,gy1=x0+90,y0+230,x1-50,y1-120
    grid_axes(d,gx0,gy0,gx1,gy1,1)
    for i in range(5):
        x=lerp(gx0,gx1,i/4); txt(d,x,gy1+16,f'WK {i}',f('MONO',22),MUTED,anchor='ma')
    d.text((x0+30,gy0+120),'RATE',font=f('MONO',22),fill=A(MUTED,1))
    # highlight weeks 2-3 band
    if t>=12.54:
        a=appear(t,12.54,0.25); bx0=lerp(gx0,gx1,1.75/4); bx1=lerp(gx0,gx1,3/4)
        d.rectangle([bx0,gy0,bx1,gy1],fill=A(VGOLD,0.12*a)); d.line([(bx0,gy0),(bx0,gy1)],fill=A(VGOLD,a),width=2); d.line([(bx1,gy0),(bx1,gy1)],fill=A(VGOLD,a),width=2)
        tag(d,bx0+8,gy0+8,'WK 2–3',VGOLD,24,a)
    # curve: baseline then sharp rise (illustrative shape)
    def yv(w): return 0.18+0.70/(1+math.exp(-(w-1.4)*3.2))
    pts=[(lerp(gx0,gx1,w/4),gy1-yv(w)*(gy1-gy0)) for w in np.linspace(0,4,40)]
    prog=clamp((t-9.9)/2.6)
    if prog>0:
        # area fill
        n=max(2,int(len(pts)*prog)); poly=pts[:n]+[(pts[n-1][0],gy1),(pts[0][0],gy1)]
        d.polygon(poly,fill=A(CYAN,0.14))
        head=polyline_prog(d,pts,prog,CYAN,6)
        d.ellipse([head[0]-10,head[1]-10,head[0]+10,head[1]+10],fill=A(WHITE,1))
        if GL: GL.ellipse([head[0]-22,head[1]-22,head[0]+22,head[1]+22],fill=A(CYAN,1))
    # rising droplets during "oxidizing that stored fat"
    if t>=13.88:
        a=appear(t,13.88,0.3)
        for k in range(10):
            p=((t-13.88)*0.5+k/10)%1; x=lerp(gx0+250,gx1-30,(k*0.37)%1); y=lerp(gy1-20,gy0+40,p)
            r=6+3*((k*7)%3); d.ellipse([x-r,y-r,x+r,y+r],fill=A(VGOLD,a*min(1,(1-p)*3)*0.9))
            if GL: GL.ellipse([x-2*r,y-2*r,x+2*r,y+2*r],fill=A(VGOLD,a*min(1,(1-p)*3)*0.5))
    if t>=16.06:
        a=appear(t,16.06); x=gx1-260; y=gy0+70
        tri(d,x,y,30,GREEN,a); txt(d,x+44,y-12,'HIGHER RATE',f('BEB',50),GREEN,a)
    txt(d,x1-30,y1-44,'ILLUSTRATIVE CURVE',f('MONO',18),MUTED2,anchor='ra')

def scene_timeline(d,t,box):   # Gantt strip
    x0,y0,x1,y1=box
    txt(d,x0+28,y0+22,'WHAT CHANGES FIRST',f('MONO',24),VGOLD)
    tx0,tx1=x0+200,x1-40; ty=y1-44
    labels=[('WK 1',0.0),('MO 1',0.16),('MO 3',0.5),('MO 6+',1.0)]
    d.line([(tx0,ty),(tx1,ty)],fill=A((110,114,130),1),width=2)
    for lb,p in labels:
        x=lerp(tx0,tx1,p); d.line([(x,ty-8),(x,ty+8)],fill=A((110,114,130),1),width=2); txt(d,x,ty+12,lb,f('MONO',20),MUTED,anchor='ma')
    # rows
    r1y,r2y=y0+64,y0+140
    txt(d,x0+28,r1y+4,'FAT LOSS',f('BEB',44),CREAM)
    txt(d,x0+28,r2y+4,'MUSCLE',f('BEB',44),CREAM,appear(t,18.6) if t>=18.6 else 0.35)
    for ry in (r1y,r2y): d.rectangle([tx0,ry,tx1,ry+52],outline=A((50,54,68),1),width=2)
    if t>=17.08:
        p=expo((t-17.08)/0.7); lit_bar(d,tx0+3,r1y+3,lerp(tx0+3,lerp(tx0,tx1,0.42),p),r1y+49,VGOLD)
        if GL: GL.rectangle([tx0,r1y,lerp(tx0,lerp(tx0,tx1,0.42),p),r1y+52],outline=A(VGOLD,1),width=6)
        if p>0.8: txt(d,tx0+16,r1y+10,'LEANING OUT',f('MONO',24),INK)
    if t>=18.76:
        a=appear(t,18.76); tag(d,tx0+10,r2y+6,'NOT YET',RED,22,a)
    if t>=21.16:
        p=expo((t-21.16)/0.5); xs=lerp(tx0,tx1,0.86)
        for k in range(int(12*p)):
            x=xs+k*10
            if x<tx1-4: d.line([(x,r2y+48),(x+14,r2y+4)],fill=A(VGOLD,0.8),width=3)
        d.rectangle([xs,r2y,tx1,r2y+52],outline=A(VGOLD,p),width=3)
    # playhead
    if t>=19.88:
        p=clamp((t-19.88)/1.6); x=lerp(tx0,lerp(tx0,tx1,0.8),ease_io(p))
        d.line([(x,r1y-6),(x,ty)],fill=A(WHITE,0.9),width=3); tri(d,x-9,r1y-20,16,WHITE,1,up=False)

def scene_bodycomp(d,t,box):   # stacked bars GRAPH 02
    x0,y0,x1,y1=box
    txt(d,x0+40,y0+76,'BODY COMPOSITION',f('BEB',58),CREAM)
    txt(d,x0+40,y0+136,'SAME SCALE WEIGHT · DIFFERENT BODY',f('MONO',22),MUTED)
    bh=430; by1=y0+640; by0=by1-bh; bw=170
    cols=[(x0+90,'START'),(x0+330,'NOW')]
    fat0,fat1=0.30,lerp(0.30,0.17,expo((t-30.6)/0.8)) if t>=30.6 else 0.30
    water=0.0 if t<31.62 else 0.05*expo((t-31.62)/0.8)
    for i,(bx,lb) in enumerate(cols):
        fat=fat0 if i==0 else fat1
        w_=0 if i==0 else water
        lean=1-fat-w_
        yf=by0+fat*bh; yw=yf+w_*bh
        vbar(d,bx,by0,bx+bw,yf,RED);
        if w_>0: vbar(d,bx,yf,bx+bw,yw,CYAN)
        vbar(d,bx,yw,bx+bw,by1,VGOLD)
        if GL: GL.rectangle([bx,by0,bx+bw,by1],outline=A(VGOLD,0.6),width=6)
        d.rectangle([bx,by0,bx+bw,by1],outline=A(WHITE,0.9),width=2)
        txt(d,bx+bw/2,by1+14,lb,f('MONO',26),CREAM,anchor='ma')
        txt(d,bx+bw/2,by0+fat*bh/2-16,f'{int(round(fat*100))}%',f('BEB',40),WHITE,anchor='ma')
        txt(d,bx+bw/2,yw+(by1-yw)/2-16,f'{int(round(lean*100))}%',f('BEB',40),INK,anchor='ma')
    # top weight line connecting both (same height)
    dashed(d,x0+80,by0-14,x0+330+bw+10,by0-14,WHITE,3,0.8)
    # legend
    lx=x0+590; ly=by0
    for k,(c,nm,tt) in enumerate([(RED,'FAT',30.6),(VGOLD,'LEAN TISSUE',31.62),(CYAN,'WATER',31.9)]):
        a=appear(t,tt) if t>=tt else 0.3
        d.rectangle([lx,ly+k*52,lx+30,ly+k*52+30],fill=A(c,a)); txt(d,lx+44,ly+k*52-2,nm,f('MONO',26),CREAM,a)
    if t>=30.6: a=appear(t,30.6); tri(d,lx+250,ly+6,22,RED,a,up=False)
    if t>=31.62: a=appear(t,31.62); tri(d,lx+250+140,ly+52+4,22,GREEN,a,up=True) if False else tri(d,lx+290,ly+58,22,GREEN,a,up=True)
    # scale net change big stat
    if t>=33.98:
        a=appear(t,33.98,0.2); sy=by0+200
        txt(d,lx,sy,'SCALE · NET CHANGE',f('MONO',22),VGOLD,a)
        v='0.0'; s=lerp(1.25,1.0,expo((t-33.98)/0.18))
        fn=f('BEB',int(130*s)); txt(d,lx,sy+30,v,fn,WHITE,a);
        if GL: GL.text((lx,sy+30),v,font=fn,fill=A(VGOLD,a*0.6))
        txt(d,lx+d.textlength(v,font=fn)+12,sy+100,'LB',f('BEB',44),MUTED,a)
    if t>=35.12: tag(d,lx,by0+380,'+0 GAINED',VGOLD,24,appear(t,35.12))
    if t>=36.74: tag(d,lx,by0+430,'−0 LOST',VGOLD,24,appear(t,36.74))
    if t>=38.38:
        a=appear(t,38.38); check(d,x0+40,y1-74,GREEN,1.0,a); txt(d,x0+86,y1-80,'MIRROR: COMPLETELY DIFFERENT',f('MONO',30),GREEN,a)

def scene_path(d,t,box):   # PATHWAY schematic
    x0,y0,x1,y1=box
    # row 1: anabolics direct
    r1=y0+90
    a1=appear(t,47.28) if t>=47.28 else 0
    if a1>0:
        node(d,x0+40,r1,x0+330,r1+100,'TESTOSTERONE','+ ANABOLICS' if t>=48.92 else 'AR BINDING',VGOLD,a1,size=42)
        p=expo((t-47.5)/0.35); arrow(d,x0+336,r1+50,lerp(x0+336,x0+640,p),r1+50,VGOLD,6,a1)
        if p>0.7: tag(d,x0+400,r1-12,'DIRECT',VGOLD,22,a1)
    node(d,x0+650,r1+170,x1-40,r1+300,'MUSCLE','TISSUE',WHITE if t<55.3 else (120,120,130),1,dim=(t>=55.58),size=56)
    if a1>0: arrow(d,x0+640,r1+50,x0+760,r1+166,VGOLD,6,a1)
    # GH node
    gy=r1+180
    node(d,x0+40,gy,x0+250,gy+120,'GH','GROWTH HORMONE',CYAN,1,size=64)
    # dashed direct GH->muscle, crossed out
    if t>=45.78:
        p=clamp((t-45.78)/0.4); dashed(d,x0+256,gy+60,x0+644,gy+60,(160,160,170),4,0.9,prog=p)
        if t>=46.3: a=appear(t,46.3); cross(d,x0+430,gy+40,RED,1.4,a); tag(d,x0+340,gy+84,'NOT DIRECT',RED,22,a)
    # route via liver -> IGF-1 -> muscle
    ly=gy+180
    if t>=50.06:
        a=appear(t,50.06)
        arrow(d,x0+145,gy+126,x0+145,ly-6,CYAN,6,a)
        node(d,x0+40,ly,x0+250,ly+100,'LIVER','',CYAN,a,size=48)
        p=expo((t-50.3)/0.4); arrow(d,x0+256,ly+50,lerp(x0+256,x0+400,p),ly+50,CYAN,6,a)
        flow(d,x0+145,gy+130,x0+145,ly-10,t,CYAN,3,1.0,a)
        if p>0.5:
            igf_low = t>=52.38
            node(d,x0+406,ly,x0+620,ly+100,'IGF-1','SIGNAL',RED if igf_low else CYAN,a,size=56)
            arrow(d,x0+626,ly+50,x0+760,r1+306,CYAN if not (t>=55.3) else (60,60,70),6,a)
            if t<55.3: flow(d,x0+626,ly+50,x0+760,r1+310,t,CYAN,3,1.0,a)
    # gates
    gyb=ly+122
    if t>=52.38:
        a=appear(t,52.38); txt(d,x0+40,gyb,'IGF-1 ELEVATED?',f('MONO',26),CREAM,a)
        lvl=0.22+0.03*math.sin(t*6); d.rectangle([x0+40,gyb+40,x0+420,gyb+70],outline=A((70,74,90),a),width=2); lit_bar(d,x0+43,gyb+43,lerp(x0+43,x0+417,lvl),gyb+67,RED,a)
        tag(d,x0+300,gyb-6,'LOW',RED,22,a)
    if t>=54.0:
        a=appear(t,54.0); txt(d,x0+500,gyb,'TRAINING RIGHT?',f('MONO',26),CREAM,a)
        # toggle switch off
        sx,sy=x0+500,gyb+40; d.rounded_rectangle([sx,sy,sx+90,sy+40],radius=20,fill=A((40,10,14),a),outline=A(RED,a),width=3)
        d.ellipse([sx+4,sy+4,sx+36,sy+36],fill=A(RED,a)); txt(d,sx+110,sy+2,'OFF',f('MONO',28),RED,a)

def scene_expect(d,t,box):   # GRAPH 03 expectation vs reality
    x0,y0,x1,y1=box
    txt(d,x0+40,y0+76,'LEAN MUSCLE GAINED',f('BEB',58),CREAM)
    txt(d,x0+40,y0+136,'EXPECTED vs WHAT GH DELIVERS',f('MONO',22),MUTED)
    gx0,gy0,gx1,gy1=x0+90,y0+220,x1-60,y1-130
    grid_axes(d,gx0,gy0,gx1,gy1,1,5)
    for i in range(0,7):
        x=lerp(gx0,gx1,i/6); txt(d,x,gy1+14,f'MO {i}',f('MONO',20),MUTED,anchor='ma')
    for k,lb in [(1,'2'),(3,'6'),(5,'10')]:
        y=gy1-k*(gy1-gy0)/5; txt(d,gx0-14,y-12,lb,f('MONO',20),MUTED,anchor='ra')
    txt(d,gx0-14,gy0-46,'LB',f('MONO',20),MUTED,anchor='ra')
    # reality: slow burn
    def rv(m): return 0.06*m**2/(1+0.0*m)
    pts=[(lerp(gx0,gx1,m/6),gy1-min(1,0.012*m**2.3)*(gy1-gy0)) for m in np.linspace(0,6,40)]
    p=clamp((t-56.2)/2.4)
    if p>0:
        head=polyline_prog(d,pts,p,VGOLD,7)
        d.ellipse([head[0]-9,head[1]-9,head[0]+9,head[1]+9],fill=A(WHITE,1))
        tag(d,lerp(gx0,gx1,0.30),gy1-90,'SLOW BURN',VGOLD,22,appear(t,56.98))
    if t>=59.38:
        a=appear(t,59.38); x=gx1; d.line([(x,gy0),(x,gy1)],fill=A(GREEN,a),width=3)
        tag(d,x-268,gy0+20,'6 MO: NOTICEABLE',GREEN,22,a)
    if t>=62.0:
        p=clamp((t-62.0)/0.9); xe=lerp(gx0,gx1,1/6); ye=gy0
        dashed(d,gx0,gy1,lerp(gx0,xe,p),lerp(gy1,ye,p),RED,6,1,prog=1)
        if GL: GL.line([(gx0,gy1),(lerp(gx0,xe,p),lerp(gy1,ye,p))],fill=A(RED,0.8),width=10)
        if t>=62.68: tag(d,xe+16,ye-6,'EXPECTED: +10 LB / 1 MO',RED,22,appear(t,62.68))
    if t>=64.42:
        a=appear(t,64.42); xe=lerp(gx0,gx1,1/6)
        yr=gy1-0.012*1**2.3*(gy1-gy0)
        d.line([(xe,gy0+50),(xe,yr)],fill=A(WHITE,a),width=3); tri(d,xe-10,yr-22,20,WHITE,a,up=False)
        txt(d,xe+16,(gy0+yr)/2,'THE GAP',f('MONO',22),WHITE,a)

def scene_tiles(d,t,box):   # progress-ring tile grid
    x0,y0,x1,y1=box
    txt(d,x0+40,y0+76,'THE REAL LONG-TERM PLAY',f('BEB',56),CREAM)
    items=[('COLLAGEN','SYNTHESIS',68.42),('TENDON','DENSITY',69.64),('CONNECTIVE','TISSUE REMODEL',70.72),('SKIN','',72.32),('HAIR','',72.90),('NAILS','',73.40),('SLEEP','',73.90)]
    tw,th=(x1-x0-80-20)/2,118
    for i,(a1,a2,tt) in enumerate(items+[('TIMEFRAME','',74.88)]):
        cx=x0+40+(i%2)*(tw+20); cy=y0+150+(i//2)*(th+16)
        if t<tt:
            d.rounded_rectangle([cx,cy,cx+tw,cy+th],radius=12,outline=A((40,44,58),1),width=2); continue
        a=appear(t,tt,0.14); off=lerp(16,0,a)
        d.rounded_rectangle([cx,cy+off,cx+tw,cy+th+off],radius=12,fill=A((14,18,30),0.95*a),outline=A(VGOLD if i<7 else WHITE,a),width=3)
        if i<7:
            fr=clamp((t-tt)/9.0)*0.85   # rings fill slowly: months
            ring(d,cx+60,cy+th/2+off,36,fr,VGOLD,a,8)
            txt(d,cx+120,cy+(26 if a2 else 40)+off,a1,f('BEB',44),WHITE,a)
            if a2: txt(d,cx+120,cy+72+off,a2,f('MONO',20),MUTED,a)
        else:
            if t>=75.34:
                b=appear(t,75.34); check(d,cx+24,cy+20,GREEN,1.0,b); txt(d,cx+70,cy+14,'MONTHS',f('BEB',48),GREEN,b)
            if t>=76.08:
                b=appear(t,76.08); cross(d,cx+28,cy+74,RED,0.9,b); txt(d,cx+70,cy+64,'WEEKS',f('BEB',44),RED,b)
            if t<75.34: txt(d,cx+24,cy+40,'TIMEFRAME…',f('MONO',24),MUTED,a)

def scene_calendar(d,t,box):   # 6-month calendar dots + big stat
    x0,y0,x1,y1=box
    txt(d,x0+28,y0+22,'STRUCTURAL CHANGES · MINIMUM WINDOW',f('MONO',22),VGOLD)
    # big stat
    if t>=91.94:
        a=appear(t,91.94,0.12); s=lerp(1.3,1.0,expo((t-91.94)/0.16)); fn=f('BEB',int(170*s))
        txt(d,x0+50,y0+50-(s-1)*60,'6',fn,VGOLD,a)
        if GL: GL.text((x0+50,y0+50-(s-1)*60),'6',font=fn,fill=A(VGOLD,a*0.7))
        txt(d,x0+40,y0+214,'MONTHS',f('BEB',50),WHITE,appear(t,92.38))
    # dot calendar: 6 columns x 4 weeks
    gx=x0+260; gy=y0+56; cw=(x1-40-gx)/6
    p=clamp((t-90.54)/1.9)*24
    for m in range(6):
        txt(d,gx+m*cw+cw/2-6,gy,f'M{m+1}',f('MONO',20),MUTED,anchor='ma')
        for w in range(4):
            k=m*4+w; cx=gx+m*cw+cw/2; cy=gy+36+w*40
            on=p>k
            d.ellipse([cx-14,cy-14,cx+14,cy+14],fill=A(VGOLD if on else (34,38,50),1),outline=A((70,74,90),1),width=2)
            if on and GL: GL.ellipse([cx-15,cy-15,cx+15,cy+15],fill=A(VGOLD,0.35))
    if t>=93.42:
        a=appear(t,93.42); tag(d,gx+5*cw-150,y1-40,'THEN JUDGE IT',GREEN,22,a)

def scene_roadmap(d,t,box):   # route stepper
    x0,y0,x1,y1=box
    txt(d,x0+28,y0+22,'BLOODWORK = THE ROADMAP',f('MONO',24),VGOLD)
    pts=[(x0+190,y0+170),(x0+400,y0+100),(x0+610,y0+170),(x0+820,y0+100)]
    curve=[]
    for i in range(3):
        a_,b_=pts[i],pts[i+1]
        for s in np.linspace(0,1,16):
            curve.append((lerp(a_[0],b_[0],s),lerp(a_[1],b_[1],s)+(-24*math.sin(math.pi*s) if i%2==0 else 24*math.sin(math.pi*s))))
    steps=[('BLOODWORK',95.72,CYAN),('ANALYZE',97.54,WHITE),('PIVOT',98.66,VGOLD),('OPTIMIZE',99.52,GREEN)]
    # path progress follows the spoken steps
    prog=0
    for i,(_,tt,_) in enumerate(steps[1:]):
        if t>=tt-0.3: prog=lerp((i)/3,(i+1)/3,expo((t-tt+0.3)/0.3))
    dashed(d,curve[0][0],curve[0][1],curve[0][0]+1,curve[0][1],(60,64,80),3,1)
    for i in range(len(curve)-1):
        if i%2==0: d.line([curve[i],curve[i+1]],fill=A((60,64,80),1),width=3)
    if prog>0: polyline_prog(d,curve,prog,VGOLD,6)
    for i,(nm,tt,col) in enumerate(steps):
        px,py=pts[i]
        if t<tt: d.ellipse([px-14,py-14,px+14,py+14],outline=A((80,84,100),1),width=3); continue
        a=appear(t,tt); r=lerp(30,20,a)
        d.ellipse([px-r,py-r,px+r,py+r],fill=A(col,a));
        if GL: GL.ellipse([px-r-10,py-r-10,px+r+10,py+r+10],fill=A(col,a*0.8))
        txt(d,px,py-8,str(i) if i else '',f('BEB',30),INK,a,anchor='mm') if False else None
        txt(d,px,py+30,nm,f('BEB',40),col if col!=WHITE else CREAM,a,anchor='ma')
    if t>=95.72:
        a=appear(t,95.72); vx,vy=x0+40,y0+130  # test tube icon
        d.rounded_rectangle([vx+18,vy,vx+42,vy+78],radius=12,outline=A(WHITE,a),width=3); d.rectangle([vx+21,vy+40,vx+39,vy+74],fill=A(RED,a)); d.line([(vx+12,vy),(vx+48,vy)],fill=A(WHITE,a),width=4)

# ---------------- full-screen carousel scene (PiP) ----------------
LOGO=None
def get_logo(sz):
    global LOGO
    if LOGO is None or LOGO.size[0]!=sz:
        lg=Image.open(S+'/work/logo.jpg').convert('RGB'); s=min(lg.size); lg=lg.crop(((lg.width-s)//2,(lg.height-s)//2,(lg.width+s)//2,(lg.height+s)//2)).resize((sz,sz),Image.LANCZOS)
        m=Image.new('L',(sz,sz),0); ImageDraw.Draw(m).ellipse([0,0,sz-1,sz-1],fill=255); lg.putalpha(m); LOGO=lg
    return LOGO
CAR=(76.72,89.20)
def carousel(im,src,t):
    t0,t1=CAR
    if not (t0<=t<t1+0.2): return im,False
    pin=ease_io((t-t0)/0.35); pout=ease_io((t-t1)/0.2)
    # wipe: navy page slides in from the left edge (gold rule leads)
    wx=lerp(0,W,pin)*(1) ; wx_out=lerp(0,W,pout)
    page=Image.new('RGBA',(W,H),NAVY+(255,))
    pd=ImageDraw.Draw(page,'RGBA')
    # subtle warm glow top-right
    glow=Image.new('L',(W,H),0); ImageDraw.Draw(glow).ellipse([500,-400,1500,600],fill=60); glow=glow.filter(ImageFilter.GaussianBlur(160))
    page.alpha_composite(Image.merge('RGBA',[Image.new('L',(W,H),c) for c in (40,36,30)]+[glow]))
    pd=ImageDraw.Draw(page,'RGBA')
    # header
    page.alpha_composite(get_logo(84),(48,120))
    txt(pd,150,118,'COACH AGZ',f('BEB',54),GOLD); txt(pd,152,172,'@coach.agz',f('MONO',24),MUTED2)
    pd.line([(48,236),(W-48,236)],fill=A((40,44,56),1),width=2)
    # PiP of speaker
    px0,py0,px1,py1=700,262,1016,682
    crop=src.crop((200,420,880,1324)).resize((px1-px0,py1-py0),Image.LANCZOS)
    m=Image.new('L',crop.size,0); ImageDraw.Draw(m).rounded_rectangle([0,0,crop.width-1,crop.height-1],radius=22,fill=255)
    cr=crop.convert('RGBA'); cr.putalpha(m); page.alpha_composite(cr,(px0,py0))
    pd.rounded_rectangle([px0,py0,px1,py1],radius=22,outline=A(GOLD,1),width=3)
    pd.ellipse([px0+18,py0+18,px0+34,py0+34],fill=A(RED,1 if int(t*2)%2==0 else 0.3)); txt(pd,px0+42,py0+12,'LIVE',f('MONO',22),WHITE)
    # kicker + headline
    a=appear(t,t0+0.2,0.25); pd.line([(48,300),(110,300)],fill=A(GOLD,a),width=4); txt(pd,124,284,'WHAT TO TRACK ON GH',f('BC6',30),GOLD,a)
    txt(pd,48,340,'BODY COMP',f('BEB',128),GOLD if t>=79.96 else CREAM,appear(t,77.2))
    txt(pd,48,470,'NOT BODY WEIGHT',f('BEB',92),CREAM,appear(t,81.18))
    if t>=82.22:
        b=appear(t,82.22); fn=f('BEB',92); x=48+pd.textlength('NOT BODY ',font=fn); txt(pd,x,470,'WEIGHT',fn,RED,b)
    # columns
    cy0=630
    pd.rounded_rectangle([48,cy0+80,660,1250],radius=16,fill=A((24,26,34),1),outline=A((58,54,48),1),width=2)
    pd.rounded_rectangle([684,cy0+80,1032,1250],radius=16,fill=A((24,26,34),1),outline=A((58,54,48),1),width=2)
    pd.line([(48,cy0+80),(660,cy0+80)],fill=A(GREEN,1),width=4); pd.line([(684,cy0+80),(1032,cy0+80)],fill=A(RED,1),width=4)
    txt(pd,76,cy0+100,'TRACK',f('BC8',40),GREEN); txt(pd,712,cy0+100,'IGNORE',f('BC8',40),RED)
    rows=[('Body composition',79.96),('How your clothes fit',83.60),('How you look',84.56),('How you feel',85.18),('How you sleep',85.82),('How your skin looks',86.60)]
    for i,(nm,tt) in enumerate(rows):
        y=cy0+170+i*68
        if t>=tt:
            b=appear(t,tt,0.12); ox=lerp(-20,0,b)
            gd=ImageDraw.Draw(page,'RGBA'); check(gd,76+ox,y+4,GREEN,0.8,b); txt(pd,124+ox,y,nm,f('DMB',34),CREAM,b)
        else: pd.line([(76,y+22),(600,y+22)],fill=A((40,44,56),1),width=2)
    for i,(nm,tt) in enumerate([('Body weight',81.48),('Bench numbers',88.42)]):
        y=cy0+170+i*68
        if t>=tt:
            b=appear(t,tt,0.12); cross(pd,712,y+6,RED,0.8,b); txt(pd,756,y,nm,f('DMB',32),CREAM,b)
            pd.line([(756,y+24),(756+pd.textlength(nm,font=f('DMB',32))*clamp((t-tt-0.15)/0.25),y+24)],fill=A(RED,b),width=4)
    txt(pd,48,1272,'FOR RESEARCH & EDUCATIONAL PURPOSES ONLY',f('BC6',22),MUTED2)
    # composite with wipe
    if t<t1:
        mask=Image.new('L',(W,H),0); ImageDraw.Draw(mask).rectangle([0,0,int(wx),H],fill=255)
        im.paste(page,(0,0),mask)
        if pin<1: ImageDraw.Draw(im).rectangle([int(wx)-8,0,int(wx),H],fill=GOLD)
    else:
        mask=Image.new('L',(W,H),0); ImageDraw.Draw(mask).rectangle([int(wx_out),0,W,H],fill=255)
        im.paste(page,(0,0),mask); ImageDraw.Draw(im).rectangle([int(wx_out),0,int(wx_out)+8,H],fill=GOLD)
    return im,True

# ---------------- scene table ----------------
P=(64,470,1016,1260)
# (t_in, t_out, fn, kind, box, header_left, header_right, exit_hard)
SCENES=[
 (6.70, 9.45, scene_scale1, 'card', (610,995,1016,1265), None, None),
 (9.4667,16.55, scene_fatox, 'panel', P, 'FAT FIRST','GRAPH 01'),
 (16.62,21.95, scene_timeline,'strip', (64,985,1016,1265), None, None),
 (22.14,30.25, scene_water,'card', (64,995,500,1265), None, None),
 (26.20,30.25, muscle_xsec,'card', (540,995,1016,1265), None, None),
 (30.30,39.95, scene_bodycomp,'panel', P, 'SCALE vs MIRROR','GRAPH 02'),
 (45.30,55.95, scene_path,'panel', P, 'HOW GH BUILDS','PATHWAY'),
 (56.06,66.45, scene_expect,'panel', P, 'THE TIMELINE','GRAPH 03'),
 (66.62,76.60, scene_tiles,'panel', P, 'LONG-TERM PLAY','STRUCTURAL'),
 (89.42,95.15, scene_calendar,'strip', (64,975,1016,1265), None, None),
 (95.30,100.20, scene_roadmap,'strip', (64,985,1016,1265), None, None),
]
STAMPS=[(65.42,66.45,'WRONG TIMING',(140,1080))]   # rotated red stamp over graph 03
VERDICTS=[(55.58,55.70,'NO IGF-1 SIGNAL','NO GROWTH',55.95)]
VERD_Y=1158

def draw_box_scene(im,t,sc):
    t_in,t_out,fn,kind,box,hl,hr=sc
    if not (t_in<=t<t_out+0.2): return
    if fn is scene_scale1 and t>=t_out: return   # hard exit on the jump cut
    pin=expo((t-t_in)/(0.20 if kind=='panel' else 0.24)); pout=clamp((t-t_out)/0.16)
    if pout>=1: return
    x0,y0,x1,y1=box
    if kind=='panel':
        s=lerp(1.05,1.0,pin)*lerp(1.0,1.03,pout); w=(x1-x0)*s; h=(y1-y0)*s; cx=(x0+x1)/2; cy=(y0+y1)/2
        bx=(cx-w/2,cy-h/2,cx+w/2,cy+h/2); dy=0
    elif kind=='card':   # heavier card: rises with weight
        dy=lerp(60,0,pin)+lerp(0,40,pout); bx=(x0,y0+dy,x1,y1+dy)
    else:                # strip: slides in from left
        dx=lerp(-120,0,pin)-lerp(0,120,pout); bx=(x0+dx,y0,x1+dx,y1)
    al=pin*(1-pout)
    frosted(im,bx,0.92 if kind=='panel' else 0.86,8 if kind=='panel' else 14)
    lay=Image.new('RGBA',(W,H),(0,0,0,0)); d=ImageDraw.Draw(lay,'RGBA')
    ox,oy=bx[0]-x0,bx[1]-y0
    # draw content in a local layer at the box origin, then offset
    fn(d,t,box)
    if ox or oy: lay=lay.transform(lay.size,Image.AFFINE,(1,0,-ox,0,1,-oy))
    if pin<1: lay=lay.filter(ImageFilter.GaussianBlur(7*(1-pin)))
    lay.putalpha(lay.split()[3].point(lambda v:int(v*al)))
    im.alpha_composite(lay); d=ImageDraw.Draw(im,'RGBA')
    bx0,by0,bx1,by1=bx
    if kind=='panel':
        d.rectangle([bx0,by0,bx1,by1],outline=A(VGOLD,0.8*al),width=3); brackets(d,bx0,by0,bx1,by1,A(VGOLD,al),48,7)
        GL.rectangle([bx0,by0,bx1,by1],outline=A(VGOLD,0.5*al),width=6); brackets(GL,bx0,by0,bx1,by1,A(VGOLD,al),48,14)
        d.ellipse([bx0+26,by0+26,bx0+42,by0+42],fill=A(RED,al if int(t*4)%2==0 else al/3))
        txt(d,bx0+56,by0+18,hl,f('MONO',28),WHITE,al); fr=f('MONO',28); tw=d.textlength(hr,font=fr); txt(d,bx1-30-tw,by0+18,hr,fr,VGOLD,al)
    elif kind=='card':
        d.rounded_rectangle([bx0,by0,bx1,by1],radius=20,outline=A(CYAN if fn is muscle_xsec else VGOLD,0.9*al),width=3)
        GL.rounded_rectangle([bx0,by0,bx1,by1],radius=20,outline=A(CYAN if fn is muscle_xsec else VGOLD,0.6*al),width=8)
    else:
        d.rectangle([bx0,by0,bx0+8,by1],fill=A(VGOLD,al)); GL.rectangle([bx0,by0,bx0+8,by1],fill=A(VGOLD,al))
        d.line([(bx0,by0),(bx1,by0)],fill=A(VGOLD,0.7*al),width=2); d.line([(bx0,by1),(bx1,by1)],fill=A(VGOLD,0.7*al),width=2)

# ---------------- text hook + topic band ----------------
HOOK_END=4.90; MID=DUR/2
def text_hook(im,t):
    if t>=HOOK_END+0.15: return
    a=1-clamp((t-HOOK_END)/0.15); s=1+0.04*clamp(t/HOOK_END)   # slow 100->104% push
    lay=Image.new('RGBA',(W,500),(0,0,0,0)); d=ImageDraw.Draw(lay,'RGBA')
    l1=[('Your ',CREAM),('GH',VGOLD),(' results',CREAM)]; l2=[("aren't on the scale",CREAM)]
    fn=f('BEB',132)
    def width(parts): return sum(d.textlength(p,font=fn) for p,_ in parts)
    wmax=max(width(l1),width(l2)); bx0=(W-wmax)/2-40; bx1=(W+wmax)/2+40
    d.rounded_rectangle([bx0,20,bx1,330],radius=26,fill=(5,8,16,215))
    d.rectangle([bx0,20,bx0+10,330],fill=GOLD+(255,))
    for k,parts in enumerate([l1,l2]):
        x=(W-width(parts))/2; y=40+k*140
        for p,c in parts:
            d.text((x,y),p,font=fn,fill=c+(255,)); x+=d.textlength(p,font=fn)
    if s!=1: lay=lay.resize((int(W*s),int(500*s)),Image.BICUBIC); ox=int((W-lay.width)/2); oy=int(262-(lay.height-500)*0.3)
    else: ox,oy=0,262
    lay.putalpha(lay.split()[3].point(lambda v:int(v*a)))
    im.alpha_composite(lay,(ox,oy))
    if GL: GL.text((ox+ (W-0)/2,0),'',font=fn)
def topic_band(im,t,hide):
    if t<HOOK_END+0.15 or t>=MID+0.15 or hide: return
    a=clamp((t-HOOK_END-0.15)/0.15)*(1-clamp((t-MID)/0.15))
    d=ImageDraw.Draw(im,'RGBA')
    d.rectangle([8,212,W,372],fill=NAVY+(int(228*a),)); d.line([(64,244),(108,244)],fill=A(GOLD,a),width=4); txt(d,122,228,'@coach.agz',f('MONO',28),GOLD,a)
    fn=f('BEB',80); x=64
    for p,c in [('GH',VGOLD),(' results  ·  track the right thing',CREAM)]:
        if p.startswith(' '): fn2=f('BEB',62); txt(d,x,284,p,fn2,c,a); x+=d.textlength(p,font=fn2)
        else: txt(d,x,266,p,fn,c,a); x+=d.textlength(p,font=fn)

# ---------------- CTA ----------------
def cta(im,t):
    if t<100.36: return
    a=appear(t,100.40,0.25); y=1020; dy=lerp(50,0,a)
    frosted(im,(56,y+dy,1024,y+250+dy),0.84,18); d=ImageDraw.Draw(im,'RGBA')
    brackets(d,56,y+dy,1024,y+250+dy,A(VGOLD,a),30,5); brackets(GL,56,y+dy,1024,y+250+dy,A(VGOLD,a),30,10)
    lg=get_logo(180).copy(); lg.putalpha(lg.split()[3].point(lambda v:int(v*a))); im.alpha_composite(lg,(80,int(y+35+dy)))
    d=ImageDraw.Draw(im,'RGBA')
    txt(d,290,y+28+dy,'FREE · FULL HGH FRAMEWORK',f('MONO',28),VGOLD,a)
    if t>=102.80:
        b=expo((t-102.80)/0.12); s=lerp(1.12,1.0,b)
        fn=f('BEB',int(96*s)); label='COMMENT  "GH"'; tw=d.textlength(label,font=fn)
        lit_bar(d,290,y+80,290+tw+44,y+80+int(110*s),VGOLD,b); d.text((312,y+86),label,font=fn,fill=A(INK,b))
        GL.rectangle([286,y+76,294+tw+44,y+84+int(110*s)],outline=A(VGOLD,b),width=12)
    txt(d,290,y+206+dy,'FOR RESEARCH & EDUCATIONAL PURPOSES ONLY',f('BC6',22),MUTED,a)

# ---------------- captions ----------------
FIX={}
ACCENT={'gh':VGOLD,'hgh':VGOLD,'igf-1':VGOLD,'scale':RED,'wrong':RED,'six':VGOLD,'months':VGOLD,'fat':VGOLD,'zero':VGOLD,'bloodwork':VGOLD,'roadmap':VGOLD}
def nearest_bound(t):
    for b0,b1 in BOUNDS:
        if b0>t+0.01: return b0
    return 1e9
def build_groups():
    G=[];cur=[]
    for i,x in enumerate(WORDS):
        if cur:
            prev=WORDS[cur[-1]]
            if len(cur)>=3 or x['s']-prev['e']>0.28 or prev['w'][-1] in '.,?!' or x['s']>=nearest_bound(prev['e']): G.append(cur); cur=[]
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
    end=WORDS[lo[-1]]['e']+0.6
    nxt=[g for g in GROUPS if WORDS[g[0]]['s']>WORDS[lo[0]]['s']]
    if t>end and (not nxt or WORDS[nxt[0][0]]['s']>t): return None
    return lo
CAP_Y=1335
def captions(im,t):
    g=group_at(t)
    if not g: return
    d=ImageDraw.Draw(im,'RGBA')
    ws=[FIX.get(WORDS[i]['w'],WORDS[i]['w']).upper().strip(',.?!') for i in g]
    keys=[WORDS[i]['w'].lower().strip(',.?!') for i in g]
    size=128
    while True:
        fn=f('BEB',size); sp=d.textlength(' ',font=fn)+14; wd=[d.textlength(w,font=fn) for w in ws]; tot=sum(wd)+sp*(len(ws)-1)
        if tot<=920: break
        size-=4
    xs=[];x=(W-tot)/2
    for w_ in wd: xs.append(x); x+=w_+sp
    act=0
    for k,i in enumerate(g):
        if WORDS[i]['s']<=t: act=k
    g0=WORDS[g[0]]['s']; s=lerp(0.9,1,expo((t-g0)/0.10))
    cap=Image.new('RGBA',(W,300),(0,0,0,0)); cd=ImageDraw.Draw(cap); shd=Image.new('RGBA',(W,300),(0,0,0,0)); sd=ImageDraw.Draw(shd)
    prev=max(0,act-1); bt=expo((t-WORDS[g[act]]['s'])/0.07) if act>0 else 1
    bx0=lerp(xs[prev],xs[act],bt)-18; bx1=lerp(xs[prev]+wd[prev],xs[act]+wd[act],bt)+18
    for k,(w_,x_) in enumerate(zip(ws,xs)):
        if k!=act: sd.text((x_+4,46),w_,font=fn,fill=(0,0,0,210))
    cap.alpha_composite(shd.filter(ImageFilter.GaussianBlur(6)))
    lit_bar(cd,bx0,40+size*0.02,bx1,40+size*0.98,RED)
    for k,(w_,x_) in enumerate(zip(ws,xs)):
        spoken=WORDS[g[k]]['s']<=t
        col=CREAM
        if k!=act and spoken and keys[k] in ACCENT: col=ACCENT[keys[k]]
        cd.text((x_,40),w_,font=fn,fill=col,stroke_width=0 if k==act else 3,stroke_fill=(0,0,0))
    if abs(s-1)>0.002:
        cap=cap.resize((int(W*s),int(300*s)),Image.BICUBIC); ox=int((W-cap.width)/2); oy=int(CAP_Y-40-(cap.height-300)/2)
    else: ox,oy=0,CAP_Y-40
    im.alpha_composite(cap,(ox,oy))

# ---------------- frame ----------------
def seg_of(t):
    for i,(b0,b1) in enumerate(BOUNDS):
        if b0<=t<b1: return i
    return len(BOUNDS)-1
def panel_active(t):
    for sc in SCENES:
        if sc[3]=='panel' and sc[0]<=t<sc[1]+0.16: return sc
    return None
def frame(src,t):
    global GL
    z=1.0 if seg_of(t)%2==0 else 1.08
    if 40.0<=t<45.3: z=1.12 if t>=42.94 else z   # punch on 'where most guys get it wrong'
    if z!=1.0:
        big=src.resize((int(W*z),int(H*z)),Image.BICUBIC); ox=(big.width-W)//2; oy=int((big.height-H)*0.35); src=big.crop((ox,oy,ox+W,oy+H))
    raw=src
    sc=panel_active(t); g=0
    if sc: g=min(ease_io((t-sc[0]+0.05)/0.30), 1-ease_io((t-sc[1])/0.22))
    bg=src
    if g>0: bg=Image.blend(src.filter(ImageFilter.GaussianBlur(18*g)),Image.new('RGB',(W,H),(5,8,16)),0.68*g)
    im=bg.convert('RGBA')
    yy=np.arange(H); a=np.where(yy>1180,np.clip((yy-1180)/260,0,1)*110,0); a=np.maximum(a,np.where(yy<420,(1-yy/420)*120,0)); scr=(a*(1-g)).astype(np.uint8)
    im.alpha_composite(Image.merge('RGBA',[Image.new('L',(W,H),c) for c in NAVY]+[Image.fromarray(np.repeat(scr[:,None],W,1))]))
    glow=Image.new('RGBA',(W,H),(0,0,0,0)); GL=ImageDraw.Draw(glow,'RGBA')
    im,full=carousel(im,raw,t)
    if not full or t>=CAR[1]:
        for s_ in SCENES: draw_box_scene(im,t,s_)
    for (t0,t1,label,(sx,sy)) in STAMPS:
        if t0<=t<t1+0.16:
            p=expo((t-t0)/0.10); al=1-clamp((t-t1)/0.16); sc_=lerp(1.6,1.0,p)
            st=Image.new('RGBA',(800,200),(0,0,0,0)); sd=ImageDraw.Draw(st,'RGBA'); fn=f('BEB',120); tw=sd.textlength(label,font=fn)
            sd.rectangle([10,10,tw+60,180],outline=A(RED,al),width=10); sd.text((35,24),label,font=fn,fill=A(RED,al))
            st=st.rotate(-8,expand=True,resample=Image.BICUBIC); st=st.resize((int(st.width*sc_),int(st.height*sc_)),Image.BICUBIC)
            im.alpha_composite(st,(int(sx+(1-sc_)*300),int(sy+(1-sc_)*80)))
            GL.rectangle([sx+20,sy+40,sx+tw+60,sy+200],outline=A(RED,al*0.7),width=14)
    for (t0,t1,a1,a2,tend) in VERDICTS:
        if t0<=t<tend+0.16:
            p=expo((t-t0)/(t1-t0)); d=ImageDraw.Draw(im,'RGBA'); y=VERD_Y; x0=P[0]; x1=lerp(x0,P[2],p); al=1-clamp((t-tend)/0.16)
            GL.rectangle([x0-4,y-8,x1+4,y+100],outline=A(RED,al),width=10)
            lit_bar(d,x0,y,x1,y+92,RED,al); d.rectangle([x0,y+88,x1,y+92],fill=A((140,0,0),al))
            if p>0.6: fn=f('BEB',74); d.text((x0+30,y+8),a1,font=fn,fill=A(WHITE,al)); tw=d.textlength(a1,font=fn); d.text((x0+30+tw+24,y+30),'= '+a2,font=f('MONO',30),fill=A(WHITE,al))
    cta(im,t)
    text_hook(im,t)
    GL=None
    if glow.getbbox():
        sm=glow.resize((W//4,H//4),Image.BILINEAR)
        g1=np.asarray(sm.filter(ImageFilter.GaussianBlur(3.5))).astype(np.float32)/255; g2=np.asarray(sm.filter(ImageFilter.GaussianBlur(10))).astype(np.float32)/255
        prem=np.clip(g1[...,:3]*g1[...,3:]*2.3+g2[...,:3]*g2[...,3:]*1.8,0,1)
        prem=np.asarray(Image.fromarray((prem*255).astype(np.uint8)).resize((W,H),Image.BILINEAR)).astype(np.float32)/255
        b=np.asarray(im.convert('RGB')).astype(np.float32)/255
        im=Image.fromarray(((1-(1-b)*(1-prem))*255).astype(np.uint8)).convert('RGBA')
    d=ImageDraw.Draw(im,'RGBA'); d.rectangle([0,0,7,H],fill=GOLD)
    topic_band(im,t,full)
    captions(im,t)
    out=im.convert('RGB')
    # camera shake on verdict + stamp landings (2 frames)
    for tl in [VERDICTS[0][1],STAMPS[0][0]+0.10]:
        k=round((t-tl)*FPS)
        if k in (0,1):
            dx=[9,-5][k]; z=1.025; big=out.resize((int(W*z),int(H*z)),Image.BICUBIC); ox=(big.width-W)//2-dx; oy=(big.height-H)//2
            out=big.crop((ox,oy,ox+W,oy+H)); ImageDraw.Draw(out).rectangle([0,0,7,H],fill=GOLD)
    return out

if __name__=='__main__':
    mode=sys.argv[2]
    if mode=='stills':
        import os; os.makedirs(T+'qc',exist_ok=True)
        for tt in [float(x) for x in sys.argv[3:]]:
            n=round(tt*FPS)
            subprocess.run(['ffmpeg','-v','error','-y','-i',T+'assembled.mov','-vf',f'select=eq(n\\,{n})','-vsync','0','-frames:v','1',T+'qc/_src.png'])
            frame(Image.open(T+'qc/_src.png').convert('RGB'),n/FPS).resize((540,960)).save(T+f'qc/st_{tt:06.2f}.jpg',quality=85)
        sys.exit()
    n0,n1=int(sys.argv[3]),int(sys.argv[4]); out=sys.argv[5]
    dec=subprocess.Popen(['ffmpeg','-v','error','-i',T+'assembled.mov','-vf',f'select=gte(n\\,{n0})','-vsync','0','-frames:v',str(n1-n0),'-f','rawvideo','-pix_fmt','rgb24','-'],stdout=subprocess.PIPE)
    enc=subprocess.Popen(['ffmpeg','-v','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-','-c:v','libx264','-crf','14','-preset','medium','-pix_fmt','yuv420p',out],stdin=subprocess.PIPE)
    for n in range(n0,n1):
        buf=dec.stdout.read(W*H*3)
        if len(buf)<W*H*3: print('short',n); break
        enc.stdin.write(frame(Image.frombuffer('RGB',(W,H),buf),n/FPS).tobytes())
    enc.stdin.close(); enc.wait(); dec.kill(); print('done',n0,n1)
