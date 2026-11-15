# HGH / carpal tunnel Reel. 1080x1920, 30 fps.
# usage: python3 render.py <scratch_dir> frames <n0> <n1> <out.mp4> | stills <t> <t> ...
# The renderer reads the 30 fps intermediate <scratch>/src/v30.mp4 and the fonts in <scratch>/fonts.
import json, subprocess, sys, math, os
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
S=sys.argv[1]; HERE=os.path.dirname(os.path.abspath(__file__))
W,H=1080,1920; FPS=30
WORDS=json.load(open(HERE+'/words_final.json'))
GOLD=(201,169,110); CREAM=(244,241,234); NAVY=(14,17,23); MUTED=(150,150,158)
RED=(255,34,28); VGOLD=(255,194,26); CYAN=(0,229,255); GREEN=(30,255,110); DEEP=(2,3,8); INK=(6,8,14); WHITE=(255,255,255)
AMBER=(255,150,20); NERVE=(255,222,60); BLUE=(70,160,255)
FD=S+'/fonts/'
BEB=FD+'BebasNeue-Regular.ttf'; MONO='/usr/share/fonts/truetype/jetbrains-mono/JetBrainsMono-Bold.ttf'
BAR=FD+'BarlowCondensed-Bold.ttf'; DMS=FD+'DMSans%5Bopsz,wght%5D.ttf'
_fc={}
def f(n,s,wt=None):
    k=(n,int(s),wt)
    if k not in _fc:
        ft=ImageFont.truetype(n,int(s))
        if wt:
            try: ft.set_variation_by_axes([14,wt])
            except Exception: pass
        _fc[k]=ft
    return _fc[k]
def clamp(x,a=0,b=1): return max(a,min(b,x))
def expo(x): x=clamp(x); return 1 if x>=1 else 1-2**(-10*x)
def ease_io(x): x=clamp(x); return 4*x**3 if x<.5 else 1-(-2*x+2)**3/2
def back(x,s=1.2): x=clamp(x); return 1+(s+1)*(x-1)**3+s*(x-1)**2
def lerp(a,b,t): return a+(b-a)*t
def A(c,a): return tuple(c[:3])+(int(clamp(a)*255),)
def appear(t,t0,dur=0.16): return expo((t-t0)/dur)
def win(t,t0,t1,fi=0.16,fo=0.14): return appear(t,t0,fi)*(1-clamp((t-t1)/fo))
GL=None
# ---------------- primitives ----------------
def txt(d,x,y,s,font,col,a=1.0,anchor=None): d.text((x,y),s,font=font,fill=A(col,a),anchor=anchor)
def brackets(d,x0,y0,x1,y1,col,L=34,w=4):
    for (cx,cy,sx,sy) in [(x0,y0,1,1),(x1,y0,-1,1),(x0,y1,1,-1),(x1,y1,-1,-1)]:
        d.line([(cx,cy),(cx+sx*L,cy)],fill=col,width=w); d.line([(cx,cy),(cx,cy+sy*L)],fill=col,width=w)
def lit_bar(d,x0,y0,x1,y1,col,a=1.0):
    h=max(1,int(y1-y0))
    for i in range(h):
        k=i/h; c=tuple(int(min(255,v*(1.18-0.36*k)+(40 if k<0.12 else 0))) for v in col)
        d.line([(x0,y0+i),(x1,y0+i)],fill=c+(int(255*clamp(a)),))
def tag(d,x,y,label,col=RED,size=30,a=1.0,glow=True,anchor='l'):
    fn=f(MONO,size); tw=d.textlength(label,font=fn); h=size+16
    if anchor=='r': x=x-tw-24
    if anchor=='c': x=x-(tw+24)/2
    lit_bar(d,x,y,x+tw+24,y+h,col,a); d.text((x+12,y+5),label,font=fn,fill=A(INK if col in (VGOLD,GREEN,CYAN,NERVE,AMBER) else WHITE,a))
    if GL is not None and glow: GL.rectangle([x-4,y-4,x+tw+28,y+h+4],outline=A(col,a),width=8)
    return x+tw+24
def arrow(d,x0,y0,x1,y1,col,w=5,a=1.0,L=18):
    d.line([(x0,y0),(x1,y1)],fill=A(col,a),width=w)
    ang=math.atan2(y1-y0,x1-x0)
    d.polygon([(x1,y1),(x1-L*math.cos(ang-0.45),y1-L*math.sin(ang-0.45)),(x1-L*math.cos(ang+0.45),y1-L*math.sin(ang+0.45))],fill=A(col,a))
def gline(d,pts,col,w,a=1.0,gw=None):
    d.line(pts,fill=A(col,a),width=w,joint='curve')
    if GL is not None: GL.line(pts,fill=A(col,a*0.9),width=gw or w*2,joint='curve')
def check(d,x,y,col,s=1.0,a=1.0):
    pts=[(x,y+16*s),(x+10*s,y+28*s),(x+30*s,y+2*s)]; gline(d,pts,col,int(6*s),a)
def cross(d,x,y,col,s=1.0,a=1.0):
    gline(d,[(x,y),(x+28*s,y+28*s)],col,int(6*s),a); gline(d,[(x+28*s,y),(x,y+28*s)],col,int(6*s),a)
def kicker(d,x,y,label,a=1.0,col=VGOLD,num=None,x1=None):
    p=clamp(a); d.line([(x,y+16),(x+lerp(0,44,p),y+16)],fill=A(col,1),width=4)
    if p>0.4: txt(d,x+58,y,label,f(MONO,28),col,clamp((p-0.4)/0.6))
    if num and x1: fn=f(MONO,28); tw=d.textlength(num,font=fn); txt(d,x1-tw,y,num,fn,MUTED,p)
def dot(d,x,y,r,col,a=1.0,glow=1.0):
    d.ellipse([x-r,y-r,x+r,y+r],fill=A(col,a))
    if GL is not None and glow>0: GL.ellipse([x-r*1.8,y-r*1.8,x+r*1.8,y+r*1.8],fill=A(col,a*glow))
def na_ion(d,x,y,a=1.0,r=15):
    dot(d,x,y,r,VGOLD,a,0.7 if r<20 else 0)
    if r>=20 and GL is not None: GL.ellipse([x-r-4,y-r-4,x+r+4,y+r+4],outline=A(VGOLD,a),width=8)
    fn=f(BAR,int(r*1.25)); txt(d,x,y+1,'Na+' if r>=20 else 'Na',fn,INK,a,anchor='mm')
def droplet(d,x,y,s,col,a=1.0):
    pts=[(x,y-s*1.5)]
    for k in range(0,181,15):
        ang=math.radians(k); pts.append((x+s*math.cos(ang-math.pi/2+math.pi/2)*1.0* (1 if k<=180 else 1), y))
    pts=[(x,y-1.6*s)]+[(x+s*math.sin(math.radians(k)),y+s*0.15-s*math.cos(math.radians(k))*-1) for k in range(60,301,12)]
    pts=[(x,y-1.7*s)]+[(x+s*math.cos(math.radians(a_)),y+s*math.sin(math.radians(a_))) for a_ in range(-30,211,10)]
    d.polygon(pts,fill=A(col,a))
    if GL is not None: GL.polygon(pts,fill=A(col,a*0.6))
def frosted(im,box,dark=0.86,blur=10,radius=0):
    x0,y0,x1,y1=[int(v) for v in box]
    x0=max(0,x0); y0=max(0,y0); x1=min(W,x1); y1=min(H,y1)
    if x1<=x0 or y1<=y0: return
    reg=im.crop((x0,y0,x1,y1)).convert('RGB').filter(ImageFilter.GaussianBlur(blur))
    reg=Image.blend(reg,Image.new('RGB',reg.size,DEEP),dark).convert('RGBA')
    if radius:
        m=Image.new('L',reg.size,0); ImageDraw.Draw(m).rounded_rectangle([0,0,reg.width-1,reg.height-1],radius=radius,fill=255)
        im.paste(reg,(x0,y0),m)
    else: im.paste(reg,(x0,y0))
def panel_frame(d,box,a,col=VGOLD,label=None,num=None,L=40):
    x0,y0,x1,y1=box
    d.rounded_rectangle(box,radius=18,outline=A(col,0.55*a),width=2); brackets(d,x0,y0,x1,y1,A(col,a),L,6)
    if GL is not None: brackets(GL,x0,y0,x1,y1,A(col,a),L,12)
# ---------------- layouts (footage window geometry) ----------------
def zoom_rect(z): w=W/z; h=H/z; x=(W-w)/2; y=(H-h)*0.35; return (x,y,x+w,y+h)
LAYOUT={
 'bubble':dict(D=(690,392,1030,732),S=(120,560,960,1400),r=170,cap=1360,cs=128),
 'split': dict(D=(140,392,940,992),S=(0,560,1080,1370),r=26,cap=1018,cs=96),
 'card':  dict(D=(50,420,500,1000),S=(130,560,950,1618),r=26,cap=1360,cs=128),
 'end':   dict(D=(190,330,890,855),S=(0,560,1080,1370),r=26,cap=885,cs=92),
}
CUTS=[2.83,10.23,18.43,20.73,27.83,34.13,36.97,40.97,46.87,59.57,66.57,73.83,78.87,80.63,83.67,89.87,93.47]
def zoom_full(t):
    k=sum(1 for c in CUTS if c<=t+1e-6); return 1.0 if k%2==0 else 1.08
# timeline of layouts: (t_start, name). transitions TR seconds starting at t_start.
LT=[(0,'full'),(6.30,'bubble'),(14.16,'split'),(27.66,'card'),(46.72,'full'),(66.42,'split'),(73.70,'bubble'),(86.10,'full'),(93.38,'end')]
TR=0.40
def geom(name,t):
    if name=='full': return dict(D=(0,0,W,H),S=zoom_rect(zoom_full(t)),r=0,cap=1360,cs=128,g=0.0)
    L=dict(LAYOUT[name]); L['g']=1.0; return L
def layout_at(t):
    idx=max(i for i,(ts,_) in enumerate(LT) if ts<=t)
    cur=geom(LT[idx][1],t)
    if idx==0: return cur
    p=ease_io((t-LT[idx][0])/TR)
    if p>=1: return cur
    prv=geom(LT[idx-1][1],t)
    out={}
    for k in ('D','S'): out[k]=tuple(lerp(a,b,p) for a,b in zip(prv[k],cur[k]))
    for k in ('r','cap','cs','g'): out[k]=lerp(prv[k],cur[k],p)
    return out
def compose_footage(src,t):
    L=layout_at(t)
    if L['g']<=0.001:
        z=L['S'];
        if abs((z[2]-z[0])-W)<0.5: return src.convert('RGBA'),L
        return src.resize((W,H),Image.BICUBIC,box=z).convert('RGBA'),L
    # background: blurred, darkened footage (keeps texture + continuity)
    small=src.resize((W//8,H//8),Image.BILINEAR).filter(ImageFilter.GaussianBlur(4)).resize((W,H),Image.BILINEAR)
    bgfull=src.resize((W,H),Image.BICUBIC,box=zoom_rect(1.0))
    bg=Image.blend(bgfull,Image.blend(small,Image.new('RGB',(W,H),(5,8,16)),0.84),clamp(L['g']))
    im=bg.convert('RGBA')
    D=[int(round(v)) for v in L['D']]; dw=D[2]-D[0]; dh=D[3]-D[1]
    winimg=src.resize((dw,dh),Image.BICUBIC,box=L['S']).convert('RGBA')
    m=Image.new('L',(dw,dh),0); ImageDraw.Draw(m).rounded_rectangle([0,0,dw-1,dh-1],radius=int(min(L['r'],dw/2,dh/2)),fill=255)
    # soft shadow
    sh=Image.new('RGBA',(W,H),(0,0,0,0)); ImageDraw.Draw(sh).rounded_rectangle([D[0]+6,D[1]+14,D[2]+6,D[3]+14],radius=int(min(L['r'],dw/2)),fill=(0,0,0,int(170*L['g'])))
    im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(14)))
    im.paste(winimg,(D[0],D[1]),m)
    d=ImageDraw.Draw(im,'RGBA'); a=clamp(L['g'])
    d.rounded_rectangle(D,radius=int(min(L['r'],dw/2,dh/2)),outline=A(VGOLD,0.9*a),width=4)
    return im,L
def window_ring(t,L):   # glow ring for the window (drawn into GL)
    if L['g']>0.01 and GL is not None:
        D=L['D']; GL.rounded_rectangle(D,radius=int(min(L['r'],(D[2]-D[0])/2)),outline=A(VGOLD,0.7*L['g']),width=8)

# ---------------- scenes ----------------
def body_figure(d,cx,top,col,a):
    w=4
    d.ellipse([cx-46,top,cx+46,top+96],outline=A(col,a),width=w)
    sh=top+120
    torso=[(cx-92,sh+10),(cx+92,sh+10),(cx+70,sh+330),(cx-70,sh+330)]
    d.line(torso+[torso[0]],fill=A(col,a),width=w,joint='curve')
    d.line([(cx-20,top+96),(cx-20,sh+10)],fill=A(col,a),width=w); d.line([(cx+20,top+96),(cx+20,sh+10)],fill=A(col,a),width=w)
    LA=[(cx-92,sh+14),(cx-128,sh+170),(cx-150,sh+320)]; RA=[(cx+92,sh+14),(cx+128,sh+170),(cx+150,sh+320)]
    d.line(LA,fill=A(col,a),width=w,joint='curve'); d.line(RA,fill=A(col,a),width=w,joint='curve')
    d.ellipse([cx-168,sh+318,cx-132,sh+366],outline=A(col,a),width=w); d.ellipse([cx+132,sh+318,cx+168,sh+366],outline=A(col,a),width=w)
    d.line([(cx-50,sh+330),(cx-62,sh+700)],fill=A(col,a),width=w); d.line([(cx+50,sh+330),(cx+62,sh+700)],fill=A(col,a),width=w)
    if GL is not None:
        for seg in (torso+[torso[0]],LA,RA): GL.line(seg,fill=A(col,a*0.5),width=8)
    return dict(wrist=(cx+150,sh+318),elbow=(cx+128,sh+170),shoulder=(cx+92,sh+14),kidL=(cx-34,sh+200),kidR=(cx+34,sh+200))
def kidney_shape(d,cx,cy,s,col,a,fill=None,width=4):
    pts=[]
    for k in range(0,360,8):
        ang=math.radians(k); r=1.0-0.28*max(0,math.cos(ang))**6
        pts.append((cx+s*0.62*r*math.cos(ang),cy+s*r*math.sin(ang)))
    if fill: d.polygon(pts,fill=A(fill,a))
    d.line(pts+[pts[0]],fill=A(col,a),width=width,joint='curve')
    if GL is not None: GL.line(pts+[pts[0]],fill=A(col,a*0.8),width=width*2)
def scene_bodymap(d,t,a):
    x0,y0,x1=70,430,1010
    kicker(d,x0+20,y0,'SIGNAL PATH',a*appear(t,6.5,0.3))
    B=body_figure(d,300,520,CYAN,a*appear(t,6.45,0.25))
    # kidneys
    kp=appear(t,9.42,0.12)
    for k in ('kidL','kidR'):
        cx,cy=B[k]; kidney_shape(d,cx,cy,30,VGOLD if kp>0 else (60,90,110),a,fill=(VGOLD if kp>0 else None),width=3)
    # wrist pin
    if t>=7.12:
        p=appear(t,7.12); wx,wy=B['wrist']; r=lerp(70,34,p)
        d.ellipse([wx-r,wy-r,wx+r,wy+r],outline=A(RED,a*p),width=5)
        if GL is not None: GL.ellipse([wx-r,wy-r,wx+r,wy+r],outline=A(RED,a*p),width=10)
        pulse=(t*1.6)%1; rr=34+40*pulse; d.ellipse([wx-rr,wy-rr,wx+rr,wy+rr],outline=A(RED,a*(1-pulse)*0.6),width=3)
        tag(d,wx+44,wy-24,'WRIST',RED,28,a*p)
    # dashed path wrist -> elbow -> shoulder -> kidney
    if t>=7.92:
        pts=[B['wrist'],B['elbow'],B['shoulder'],(B['shoulder'][0]-40,B['shoulder'][1]+80),B['kidR']]
        segs=list(zip(pts,pts[1:])); lens=[math.dist(p,q) for p,q in segs]; tot=sum(lens)
        prog=ease_io((t-7.92)/1.5)*tot; acc=0
        for (p,q),l in zip(segs,lens):
            if prog<=acc: break
            k=min(1,(prog-acc)/l); n=int(l*k/18)
            for j in range(n):
                if j%2==0:
                    u0=j*18/l; u1=min(k,(j+1)*18/l)
                    gline(d,[(lerp(p[0],q[0],u0),lerp(p[1],q[1],u0)),(lerp(p[0],q[0],u1),lerp(p[1],q[1],u1))],VGOLD,5,a)
            acc+=l
    if t>=9.42:
        p=appear(t,9.42); cx,cy=B['kidR']
        d.ellipse([cx-120,cy-70,cx+60,cy+70],outline=A(VGOLD,a*p),width=3)
        tag(d,cx+80,cy-22,'ORIGIN ?',VGOLD,30,a*p)
    # method rail
    if t>=10.3:
        ra=a*appear(t,10.3,0.25); rx=640; ys=[880,1030,1180]
        txt(d,rx,800,'HOW WE BREAK IT DOWN',f(MONO,24),MUTED,ra)
        for i,(lab,tt) in enumerate([('MECHANISM',11.62),('SIMPLIFY',12.88),('OPTIMIZE',13.86)]):
            on=appear(t,tt,0.12); y=ys[i]; col=VGOLD if on>0 else (70,74,90)
            if i>0:
                fy=lerp(ys[i-1]+30,y-30,on); d.line([(rx+30,ys[i-1]+30),(rx+30,y-30)],fill=A((60,64,80),ra),width=3)
                if on>0: gline(d,[(rx+30,ys[i-1]+30),(rx+30,fy)],VGOLD,4,ra)
            d.ellipse([rx,y-30,rx+60,y+30],outline=A(col,ra),width=4,fill=A(VGOLD,ra*on) if on>0 else None)
            if GL is not None and on>0: GL.ellipse([rx-4,y-34,rx+64,y+34],outline=A(VGOLD,ra*on),width=10)
            txt(d,rx+30,y,f'0{i+1}',f(MONO,24),INK if on>0 else MUTED,ra,anchor='mm')
            txt(d,rx+84,y,lab,f(BEB,64),WHITE if on>0 else (90,94,110),ra,anchor='lm')
def scene_kidney(d,t,a):
    x0,y0,x1=80,1150,1000
    kicker(d,x0,y0,'KIDNEY · SODIUM BALANCE' if t<20.7 else 'KIDNEY · TUBULE WALL',a,num='02',x1=x1)
    # right: gauge (graph) shared by both phases
    gx0,gy0,gx1,gy1=820,1230,980,1600
    d.rectangle([gx0,gy0,gx1,gy1],outline=A((80,84,100),a),width=2)
    for k in range(1,4): d.line([(gx0,gy1-k*(gy1-gy0)/4),(gx0+14,gy1-k*(gy1-gy0)/4)],fill=A((80,84,100),a),width=2)
    if t<26.9:
        lvl=0.5 if t<19.8 else lerp(0.5,0.86,expo((t-19.8)/0.6)); lab='Na+ HELD'; col=VGOLD if t<19.8 else RED
    else:
        lvl=lerp(0.86,0.95,expo((t-26.94)/0.5)); lab='FLUID'; col=CYAN
    hh=(gy1-gy0-8)*lvl; lit_bar(d,gx0+4,gy1-4-hh,gx1-4,gy1-4,col,a)
    if GL is not None: GL.rectangle([gx0+4,gy1-4-hh,gx1-4,gy1-4],fill=A(col,a*0.5))
    txt(d,(gx0+gx1)/2,gy0-14,lab,f(MONO,24),CREAM,a,anchor='ms')
    txt(d,(gx0+gx1)/2,gy1-hh-10,f'{int(round(lvl*100))}%',f(BEB,52),WHITE,a,anchor='ms')
    if t<20.8:
        pa=a*(1-clamp((t-20.66)/0.14))
        kx,ky=200,1420
        kidney_shape(d,kx,ky,150,CYAN if t<14.62 else VGOLD,pa*appear(t,14.3,0.2),fill=(12,22,34),width=5)
        # boxes
        hb=(450,1236,760,1340); fb=(450,1490,760,1594)
        hold_on=appear(t,16.58,0.12); fl_on=appear(t,17.76,0.12)
        fl_dim = 1-0.65*clamp((t-19.8)/0.5)
        for bx,lab1,lab2,on,col,dm in [(hb,'HOLD','→ BLOOD',hold_on,VGOLD,1),(fb,'FLUSH','→ URINE',fl_on,BLUE,fl_dim)]:
            c=col if on>0 else (70,74,90)
            d.rounded_rectangle(bx,radius=12,fill=A((10,14,24),pa),outline=A(c,pa*dm),width=4)
            if GL is not None and on>0: GL.rounded_rectangle(bx,radius=12,outline=A(c,pa*dm),width=8)
            txt(d,bx[0]+20,bx[1]+10,lab1,f(BEB,58),WHITE,pa*dm); txt(d,bx[0]+20,bx[1]+70,lab2,f(MONO,22),c,pa*dm)
        # ion stream splitting
        if t>=15.72:
            ratio=0.5 if t<19.8 else lerp(0.5,0.88,expo((t-19.8)/0.6)); sa=pa*appear(t,15.72,0.3)
            for k in range(10):
                ph=(t*0.55+k/10)%1; up=((k*7)%10)/10<ratio
                tx,ty=(hb[0]-10,1290) if up else (fb[0]-10,1540)
                if ph<0.45: x=lerp(60,kx,ph/0.45); y=lerp(1250,ky,ph/0.45)
                else: q=(ph-0.45)/0.55; x=lerp(kx+60,tx,q); y=lerp(ky,ty,q)
                na_ion(d,x,y,sa*min(1,ph*8,(1-ph)*8),12)
        if t>=18.58:
            p=appear(t,18.58,0.14); tag(d,lerp(kx-140,kx-110,p),1290,'GH',VGOLD,30,pa*p)
        if t>=19.12:
            p=appear(t,19.12,0.14); tag(d,lerp(kx-60,kx-40,p),1290,'IGF-1',VGOLD,30,pa*p)
        if t>=19.8: tag(d,gx0-6,gy0+6,'↑',RED,30,pa*appear(t,19.8),anchor='r')
    else:
        pb=a*appear(t,20.8,0.2)
        wy0,wy1=1392,1440; xL,xR=80,770
        txt(d,xL,1236,'BLOOD SIDE',f(MONO,24),MUTED,pb); txt(d,xL,1604,'URINE SIDE (TUBULE)',f(MONO,24),MUTED,pb)
        chans=[180,340,500,660]
        opn=expo((t-23.34)/0.3)
        # wall segments
        xs=[xL]+sum([[c-34,c+34] for c in chans],[])+[xR]
        for i in range(0,len(xs),2):
            d.rounded_rectangle([xs[i],wy0,xs[i+1],wy1],radius=8,fill=A((24,34,52),pb),outline=A(CYAN,pb*0.8),width=3)
        for c in chans:
            g=lerp(4,26,opn)
            for sgn in (-1,1):
                gx=c+sgn*g; d.rounded_rectangle([gx-8 if sgn<0 else gx-4,wy0-14,gx+4 if sgn<0 else gx+8,wy1+14],radius=4,fill=A(VGOLD,pb))
            if GL is not None and opn>0: GL.ellipse([c-30,wy0-20,c+30,wy1+20],fill=A(VGOLD,pb*opn*0.6))
        # GH signal ripple along wall
        if 20.8<=t<22.6:
            rx=lerp(xL,xR,(t-20.8)/1.2);
            if rx<=xR: gline(d,[(max(xL,rx-80),wy0-24),(rx,wy0-24)],VGOLD,5,pb)
        if t>=23.74: tag(d,chans[2]+40,wy1+40,'ENaC CHANNELS',VGOLD,26,pb*appear(t,23.74))
        # sodium crossing
        if t>=22.18:
            sa=pb*appear(t,22.18,0.3); stays=clamp((t-25.18)/0.4)
            for k in range(12):
                c=chans[k%4]; ph=(t*0.6+k/12+0.13*(k%4))%1
                y=lerp(1580,1250,ph); x=c+12*math.sin(k*2.1+ph*6)
                if y<wy0-20 and opn<0.5: continue
                if stays>0 and y<1300: y=1300-((k*13)%40)
                na_ion(d,x,y,sa*min(1,ph*6,(1-ph)*6 if stays<=0 else 1),12)
        if t>=25.84:
            wa=pb*appear(t,25.84,0.3)
            for k in range(8):
                c=chans[(k+1)%4]+30; ph=(t*0.5+k/8)%1; y=lerp(1580,1270,ph)
                droplet(d,c,y,10,BLUE,wa*min(1,ph*6,(1-ph)*6))
            tag(d,xR-10,1236,'WATER FOLLOWS',BLUE,24,wa,anchor='r') if False else None
        if t>=27.14: tag(d,gx0-6,gy0+6,'SWELLING',CYAN,26,pb*appear(t,27.14),anchor='r')
def hand_shape(d,cx,cy,s,a,fills=None,outline=CYAN,ringhalf=None,pinky_col=None):
    # palm + 5 fingers (left hand, palm view: thumb on the right). returns finger tip points
    fingers=[('pinky',-0.62,-0.55,0.20,0.62),('ring',-0.24,-0.78,0.22,0.78),('middle',0.14,-0.86,0.23,0.86),('index',0.52,-0.74,0.22,0.74)]
    px0,py0,px1,py1=cx-0.82*s,cy-0.45*s,cx+0.82*s,cy+0.7*s
    d.rounded_rectangle([px0,py0,px1,py1],radius=int(0.3*s),fill=A((10,16,26),a),outline=A(outline,a),width=4)
    tips={}
    for nm,fx,fy,fw,fl in fingers:
        x0=cx+(fx-fw/2)*s*1.0-0.06*s; x1=x0+fw*s*1.0+0.04*s; y1=py0+0.25*s; y0=py0-fl*s*0.95
        col=(fills or {}).get(nm)
        d.rounded_rectangle([x0,y0,x1,y1],radius=int(fw*s*0.5),fill=A((10,16,26),a),outline=A(outline if nm!='pinky' or not pinky_col else pinky_col,a),width=4)
        if col:
            if nm=='ring' and ringhalf is not None:
                xm=(x0+x1)/2; d.rounded_rectangle([xm,y0,x1,y1],radius=int(fw*s*0.25),fill=A(col[0],a*ringhalf))
                if GL is not None: GL.rectangle([xm,y0,x1,y1],fill=A(col[0],a*0.5*ringhalf))
            else:
                d.rounded_rectangle([x0+5,y0+5,x1-5,y1],radius=int(fw*s*0.45),fill=A(col[0],a*col[1]))
                if GL is not None: GL.rounded_rectangle([x0,y0,x1,y1],radius=int(fw*s*0.5),fill=A(col[0],a*0.45*col[1]))
        tips[nm]=((x0+x1)/2,y0+0.08*s)
    # thumb (angled to the right)
    th=[(px1-0.05*s,cy+0.05*s),(px1+0.42*s,cy-0.42*s),(px1+0.58*s,cy-0.30*s),(px1+0.12*s,cy+0.40*s)]
    col=(fills or {}).get('thumb')
    d.polygon(th,fill=A((col[0] if col else (10,16,26)),a*(col[1] if col else 1)),outline=A(outline,a)); d.line(th+[th[0]],fill=A(outline,a),width=4,joint='curve')
    if GL is not None and col: GL.polygon(th,fill=A(col[0],a*0.45*col[1]))
    tips['thumb']=(px1+0.5*s,cy-0.36*s)
    # wrist
    d.line([(cx-0.62*s,py1),(cx-0.62*s,py1+0.5*s)],fill=A(outline,a),width=4); d.line([(cx+0.62*s,py1),(cx+0.62*s,py1+0.5*s)],fill=A(outline,a),width=4)
    if GL is not None: GL.rounded_rectangle([px0,py0,px1,py1],radius=int(0.3*s),outline=A(outline,a*0.5),width=8)
    return tips,(cx-0.62*s,py1-0.1*s,cx+0.62*s,py1+0.42*s)
def cross_section(d,cx,cy,rx,ry,a,t,n_tend=9,nerve_a=1.0,fluid=0.0,squeeze=0.0,rigid=0.0,flow=True,lig_label=True):
    d.ellipse([cx-rx,cy-ry,cx+rx,cy+ry],fill=A((10,16,26),a),outline=A(CYAN,a*0.6),width=3)
    # carpal bones (U shape, bottom)
    for k in range(8):
        ang=math.radians(200+k*(140/7)); bx=cx+rx*0.72*math.cos(ang); by=cy-ry*0.15-ry*0.72*math.sin(ang)*-1
        by=cy+ry*0.55*math.sin(math.radians(20+k*(140/7)))+ry*0.05
        bx=cx+rx*0.78*math.cos(math.radians(180-(20+k*(140/7))))
        d.ellipse([bx-rx*0.13,by-ry*0.14,bx+rx*0.13,by+ry*0.14],fill=A((200,200,210),a*0.85))
    # ligament roof
    lc=lerp(1,0,0) ; colL=RED if rigid>0.5 else VGOLD
    roof=[(cx-rx*0.78+k*(rx*1.56/20), cy-ry*0.52-math.sin(math.pi*k/20)*ry*0.12) for k in range(21)]
    gline(d,roof,colL,7,a)
    # tunnel interior
    tx0,ty0,tx1,ty1=cx-rx*0.62,cy-ry*0.46,cx+rx*0.62,cy+ry*0.34
    if fluid>0:
        d.ellipse([tx0,ty0,tx1,ty1],fill=A(BLUE,a*0.35*fluid))
        if GL is not None: GL.ellipse([tx0,ty0,tx1,ty1],fill=A(BLUE,a*0.25*fluid))
    pos=[(-0.42,0.05),(-0.22,-0.08),(0.0,-0.02),(0.22,-0.08),(0.42,0.05),(-0.30,0.22),(-0.08,0.22),(0.14,0.22),(0.34,0.22)]
    for i,(px,py) in enumerate(pos[:n_tend]):
        r=rx*0.085*(1+0.35*fluid); x=cx+px*rx; y=cy+py*ry*1.1
        d.ellipse([x-r,y-r,x+r,y+r],fill=A((235,235,240),a),outline=A((140,150,170),a),width=2)
        if fluid>0: d.ellipse([x-r-6*fluid,y-r-6*fluid,x+r+6*fluid,y+r+6*fluid],outline=A(BLUE,a*0.8*fluid),width=3)
    if nerve_a>0:
        ncol=tuple(int(lerp(c1,c2,squeeze)) for c1,c2 in zip(NERVE,RED))
        nw=rx*lerp(0.17,0.26,squeeze); nh=ry*lerp(0.15,0.055,squeeze); nx=cx+rx*0.08; ny=cy-ry*0.33+ry*0.05*squeeze
        d.ellipse([nx-nw,ny-nh,nx+nw,ny+nh],fill=A(ncol,a*nerve_a),outline=A(WHITE,a*nerve_a*0.6),width=2)
        if GL is not None: GL.ellipse([nx-nw,ny-nh,nx+nw,ny+nh],fill=A(ncol,a*nerve_a*0.8))
        if flow:
            sp=lerp(1.0,0.0,clamp(squeeze*1.25));
            for k in range(3):
                ph=(t*sp*0.8+k/3)%1; bx=lerp(nx-nw*0.7,nx+nw*0.7,ph)
                d.ellipse([bx-4,ny-4,bx+4,ny+4],fill=A((180,0,0),a*nerve_a))
        return (nx,ny,nw,nh)
    return None
def scene_wrist(d,t,a):
    rx0,ry0,rx1,ry1=530,420,1030,1000
    # Phase A: hand X-ray, tunnel location
    if t<34.3:
        pa=a*(1-clamp((t-34.14)/0.14))
        kicker(d,rx0+10,ry0,'WRIST · X-RAY',pa*appear(t,27.8,0.3))
        numb=appear(t,29.94,0.12)
        pulse=0.55+0.45*math.sin(t*9)
        fills={k:(RED,numb*pulse) for k in ('thumb','index','middle','ring')} if numb>0 else None
        tips,wb=hand_shape(d,770,690,200,pa*appear(t,27.8,0.25),fills=fills,ringhalf=numb*pulse if numb>0 else None)
        if numb>0: tag(d,560,470+50,'NUMB',RED,26,pa*numb)
        if t>=30.88:
            sy=lerp(470,wb[1]+60,ease_io((t-30.88)/1.0))
            if t<32.2:
                gline(d,[(rx0+20,sy),(rx1-20,sy)],CYAN,3,pa)
                if GL is not None: GL.rectangle([rx0+20,sy-16,rx1-20,sy],fill=A(CYAN,pa*0.25))
        if t>=33.30:
            p=appear(t,33.30); x0,y0,x1,y1=wb; x0-=20; x1+=20
            brackets(d,x0,y0,x1,y1,A(RED,pa*p),24,6)
            if GL is not None: brackets(GL,x0,y0,x1,y1,A(RED,pa*p),24,12)
            tag(d,(x0+x1)/2,y1+12,'CARPAL TUNNEL',RED,28,pa*p,anchor='c')
        # bottom row: water -> wrist path
        if t>=28.94:
            ba=pa*appear(t,28.94,0.2); droplet(d,140,1150,22,BLUE,ba); txt(d,180,1130,'H2O',f(BEB,56),WHITE,ba)
            arr=ease_io((t-29.3)/0.6);
            if arr>0: arrow(d,290,1160,lerp(290,560,arr),1160,BLUE,5,ba)
            if t>=29.94: txt(d,590,1130,'FINGERS',f(BEB,56),RED,pa*appear(t,29.94))
    elif t<37.06:
        pb=a*appear(t,34.2,0.18)*(1-clamp((t-36.96)/0.12))
        kicker(d,rx0+10,ry0,'CROSS-SECTION',pb)
        n=int(clamp((t-34.2)/1.3)*9+0.999) if t>=34.2 else 0
        cross_section(d,780,720,230,190,pb,t,n_tend=n,nerve_a=appear(t,36.24,0.14))
        if t>=36.24: tag(d,780,500,'MEDIAN NERVE',NERVE,26,pb*appear(t,36.24),anchor='c')
        txt(d,640,940,'LIGAMENT ROOF',f(MONO,22),VGOLD,pb*appear(t,34.4)) if False else None
        # bottom: counter
        txt(d,90,1240,str(max(n,0)),f(BEB,230),VGOLD,pb,anchor='ls')
        txt(d,230,1105,'TENDONS',f(BEB,70),WHITE,pb)
        if t>=36.24: txt(d,230,1178,'+ 1 NERVE',f(BEB,70),NERVE,pb*appear(t,36.24))
        if t>=35.34: tag(d,560,1120,'FIXED SPACE',RED,28,pb*appear(t,35.34))
    else:
        pc=a*appear(t,37.04,0.2)
        kicker(d,rx0+10,ry0,'MEDIAN NERVE MAP',pc)
        fills={}
        for nm,tt in [('thumb',37.96),('index',38.38),('middle',38.92),('ring',40.30)]:
            v=appear(t,tt,0.12)
            if v>0: fills[nm]=(NERVE,v)
        hit=appear(t,41.76,0.12)
        if hit>0:
            pulse=0.5+0.5*math.sin(t*10)
            for k in fills: fills[k]=(tuple(int(lerp(NERVE[i],RED[i],hit*pulse)) for i in range(3)),fills[k][1])
        sp=appear(t,43.74,0.14)
        tips,wb=hand_shape(d,770,700,200,pc,fills=fills,ringhalf=fills.get('ring',(0,0))[1] if 'ring' in fills else None,pinky_col=GREEN if sp>0 else None)
        if sp>0:
            px,py=tips['pinky']; d.ellipse([px-36,py-36,px+36,py+36],outline=A(GREEN,pc*sp),width=4)
        # bottom legend
        la=pc*appear(t,37.3,0.2)
        d.rectangle([90,1110,130,1150],fill=A(NERVE,la)); txt(d,146,1108,'MEDIAN NERVE ZONE',f(MONO,30),WHITE,la)
        txt(d,146,1150,'thumb · index · middle · ½ ring',f(DMS,30,600),MUTED,la)
        if hit>0: tag(d,560,1104,'SYMPTOM ZONE',RED,26,pc*hit) if False else None
        if sp>0:
            d.rectangle([90,1210,130,1250],outline=A(GREEN,pc*sp),width=4); txt(d,146,1208,'PINKY · ULNAR NERVE',f(MONO,30),GREEN,pc*sp)
        if t>=45.66: tag(d,1000,1206,'VARIES',AMBER,24,pc*appear(t,45.66),anchor='r')
        if hit>0: tag(d,560,450+0,'HIT ZONE',RED,26,pc*hit) if False else None
def scene_compress(d,im,t):
    # top card, footage stays full. card y 250..570
    a=win(t,47.04,55.96,0.2,0.18)
    if a<=0: return
    box=(60,250,1020,572); frosted(im,box,0.9,10,18); d=ImageDraw.Draw(im,'RGBA')
    panel_frame(d,box,a)
    txt(d,90,270,'INSIDE THE TUNNEL',f(MONO,24),VGOLD,a)
    rigid=appear(t,48.24,0.12); fluid=clamp((t-49.6)/1.4); sq=clamp((t-50.9)/1.0)
    nv=cross_section(d,240,436,150,110,a,t,fluid=fluid,squeeze=sq,rigid=rigid)
    if rigid>0 and t<53.4: tag(d,240,282+0,'RIGID',RED,22,a*rigid,anchor='c') if False else None
    gx0,gy0,gx1,gy1=440,320,990,540
    if t<53.42:
        ga=a*(1-clamp((t-53.30)/0.12))
        txt(d,gx0,280,'NERVE PRESSURE',f(MONO,24),CREAM,ga)
        d.line([(gx0,gy1),(gx1,gy1)],fill=A((90,94,110),ga),width=2); d.line([(gx0,gy0),(gx0,gy1)],fill=A((90,94,110),ga),width=2)
        thr=gy0+70;
        for xx in range(gx0,gx1,22): d.line([(xx,thr),(xx+11,thr)],fill=A(RED,ga*0.8),width=2)
        txt(d,gx1,thr-30,'NERVE LIMIT',f(MONO,20),RED,ga,anchor='ra')
        def pv(u):  # pressure curve over u in 0..1
            return 0.12 if u<0.25 else 0.12+0.8*ease_io((u-0.25)/0.6)
        prog=clamp((t-47.2)/5.6)
        pts=[(lerp(gx0,gx1,u/60),lerp(gy1-6,gy0,pv(u/60))) for u in range(0,int(60*prog)+1)]
        if len(pts)>1:
            for p_,q_ in zip(pts,pts[1:]):
                col=RED if q_[1]<thr else CYAN
                gline(d,[p_,q_],col,5,ga)
        if t>=52.04: tag(d,gx0+10,gy0+90,'BLOOD FLOW ↓',RED,24,ga*appear(t,52.04))
    else:
        sa=a*appear(t,53.42,0.15)
        for i,(lab,tt,col) in enumerate([('TINGLING',53.92,AMBER),('NUMBNESS',54.58,RED),('GRIP',55.28,RED)]):
            if t>=tt:
                p=appear(t,tt,0.14); x=470+(i%2)*260; y=300+(i//2)*120
                tag(d,lerp(x+30,x,p),y,lab,col,34,sa*p)
        if t>=55.28:
            p=appear(t,55.28,0.1); fr=lerp(0.9,0.3,expo((t-55.4)/0.5))
            x0,y0=730,436; d.rectangle([x0,y0,x0+250,y0+34],outline=A((90,94,110),sa*p),width=2); lit_bar(d,x0+3,y0+3,x0+3+244*fr,y0+31,RED,sa*p)
            txt(d,x0,y0+44,'GRIP STRENGTH',f(MONO,20),MUTED,sa*p)
def scene_stepper(d,im,t):
    a=win(t,60.9,66.30,0.2,0.18)
    if a<=0: return
    # dark scrim at top for legibility (no panel: floating icons)
    scr=Image.new('RGBA',(W,330),(0,0,0,0)); sd=ImageDraw.Draw(scr)
    for y in range(330): sd.line([(0,y),(W,y)],fill=(2,3,8,int(200*a*(1-max(0,y-200)/130 if y>200 else 1))))
    im.alpha_composite(scr,(0,232)); d=ImageDraw.Draw(im,'RGBA')
    xs=[190,540,890]; y=400
    # connectors
    for i,tt in enumerate([62.14,63.18]):
        p=ease_io((t-tt)/0.35)
        if p>0: gline(d,[(xs[i]+95,y),(lerp(xs[i]+95,xs[i+1]-95,p),y)],VGOLD,5,a)
        if p>=1: arrow(d,xs[i+1]-120,y,xs[i+1]-96,y,VGOLD,5,a)
    p1=appear(t,60.96,0.18)
    if p1>0:
        s=lerp(1.3,1,p1); na_ion(d,xs[0],y,a*p1,int(62*s)); tag(d,xs[0],y+84,'SODIUM HELD',VGOLD,24,a*p1,anchor='c')
    p2=appear(t,62.22,0.18)
    if p2>0:
        droplet(d,xs[1],y+20,int(52*lerp(1.3,1,p2)),BLUE,a*p2); tag(d,xs[1],y+80,'WATER',BLUE,24,a*p2,anchor='c')
    p3=appear(t,63.32,0.18)
    if p3>0:
        close=ease_io((t-64.46)/0.6); sq=appear(t,65.5,0.12)
        gap=lerp(70,34,close)
        for sgn in (-1,1):
            d.rounded_rectangle([xs[2]+sgn*gap-(14 if sgn<0 else -0)-(0 if sgn<0 else 0),y-70,xs[2]+sgn*gap+(0 if sgn<0 else 14),y+70],radius=6,fill=A((200,200,210),a*p3*appear(t,64.46)))
        nh=lerp(26,12,sq); nw=lerp(26,40,sq); col=tuple(int(lerp(NERVE[i],RED[i],sq)) for i in range(3))
        d.ellipse([xs[2]-nw,y-nh*2.4,xs[2]+nw,y+nh*2.4],fill=A(col,a*p3))
        if GL is not None: GL.ellipse([xs[2]-nw-6,y-nh*2.4-6,xs[2]+nw+6,y+nh*2.4+6],fill=A(col,a*p3))
        tag(d,xs[2],y+80,'NERVE' if sq<=0 else 'SQUEEZED',NERVE if sq<=0 else RED,24,a*p3,anchor='c')
def gauge(d,cx,cy,r,v,a,label):
    # semicircle, green -> amber -> red
    for k in range(60):
        u0=k/60; u1=(k+1)/60; col=GREEN if u0<0.4 else (AMBER if u0<0.7 else RED)
        a0=180+u0*180; a1=180+u1*180+0.5
        d.arc([cx-r,cy-r,cx+r,cy+r],a0,a1,fill=A(col,a*(1.0 if u0<=v else 0.25)),width=22)
    if GL is not None:
        GL.arc([cx-r,cy-r,cx+r,cy+r],180,180+v*180,fill=A(GREEN if v<0.4 else (AMBER if v<0.7 else RED),a),width=30)
    ang=math.radians(180+v*180); gline(d,[(cx,cy),(cx+(r-34)*math.cos(ang),cy+(r-34)*math.sin(ang))],WHITE,6,a)
    d.ellipse([cx-12,cy-12,cx+12,cy+12],fill=A(WHITE,a))
    txt(d,cx,cy+24,label,f(MONO,22),CREAM,a,anchor='ma')
def scene_risk(d,t,a):
    x0,y0,x1=80,1150,1000
    kicker(d,x0,y0,'WHAT DECIDES IF YOU GET IT',a,num='03',x1=x1)
    rows=[('FLUID HELD',67.52,0.75,BLUE),('NERVE SENSITIVITY',68.64,0.6,NERVE),('GH DOSE',71.50,0.92,RED)]
    tot=0
    for i,(lab,tt,val,col) in enumerate(rows):
        y=1250+i*125; ra=a*appear(t,66.7+i*0.1,0.2)
        txt(d,x0,y-6,lab,f(MONO,26),CREAM,ra)
        v=lerp(0.12,val,ease_io((t-tt)/0.5)); tot+=v
        bx0,bx1=x0,640; by=y+50
        d.rounded_rectangle([bx0,by-6,bx1,by+6],radius=6,fill=A((40,44,60),ra))
        lit_bar(d,bx0,by-6,lerp(bx0,bx1,v),by+6,col,ra)
        kx=lerp(bx0,bx1,v); d.ellipse([kx-18,by-18,kx+18,by+18],fill=A(WHITE,ra),outline=A(col,ra),width=5)
        if GL is not None and t>=tt: GL.ellipse([kx-22,by-22,kx+22,by+22],fill=A(col,ra*0.7))
    risk=clamp((tot-0.36)/(0.75+0.6+0.92-0.36))
    gauge(d,830,1470,150,risk,a*appear(t,66.8,0.2),'SYMPTOM RISK')
    if t>=73.12: tag(d,830,1270,'HIGH',RED,28,a*appear(t,73.12),anchor='c')
def scene_dose(d,t,a):
    kicker(d,90,432,'GH DOSE · TITRATION',a*appear(t,73.9,0.3))
    txt(d,148,476,'IU per day · illustrative shape',f(DMS,28,500),MUTED,a*appear(t,74.0,0.3))
    x0,y0,x1,y1=120,800,990,1180
    ga=a*appear(t,73.95,0.25)
    d.line([(x0,y1),(x1,y1)],fill=A((110,114,130),ga),width=3); d.line([(x0,y0-30),(x0,y1)],fill=A((110,114,130),ga),width=3)
    def Y(v): return y1-v*(y1-y0)
    def X(u): return lerp(x0,x1,u)
    # path keyframes (u, v) with reveal times
    path=[(0.0,0.86,73.95),(0.22,0.86,75.0),(0.24,0.62,77.14),(0.30,0.62,77.5),(0.31,0.46,77.8),(0.36,0.46,78.1),(0.37,0.34,78.38),(0.60,0.34,79.92),
          (0.61,0.42,80.95),(0.66,0.42,81.25),(0.67,0.50,81.52),(0.72,0.50,81.8),(0.73,0.58,82.05),(0.80,0.58,82.4),(0.81,0.66,82.72),(1.0,0.66,83.6)]
    # stabilize band
    if t>=79.04:
        sb=a*appear(t,79.04,0.3); d.rectangle([X(0.37),y0-30,X(0.60),y1],fill=A(GREEN,0.10*sb)); txt(d,X(0.485),y0-24,'STABILIZE',f(MONO,22),GREEN,sb,anchor='ma')
    # 4 IU target
    if t>=82.72:
        p=appear(t,82.72,0.12); yy=Y(0.66)
        for xx in range(x0,x1,24): d.line([(xx,yy),(xx+12,yy)],fill=A(VGOLD,a*p),width=3)
        tag(d,x1,yy-62,'4 IU',VGOLD,34,a*p,anchor='r')
    prev=None
    for i in range(len(path)-1):
        (u0,v0,t0),(u1,v1,t1)=path[i],path[i+1]
        if t<t0: break
        k=clamp((t-t0)/max(0.12,(t1-t0)*0.8)); k=ease_io(k)
        p0=(X(u0),Y(v0)); p1=(lerp(X(u0),X(u1),k),lerp(Y(v0),Y(v1),k))
        col=RED if v0>0.7 and u1<=0.24 else (GREEN if 0.36<=u0<0.6 else (VGOLD if u0>=0.6 else CYAN))
        gline(d,[p0,p1],col,7,a)
    # symptom markers on the high segment
    for (u,tt,lab) in [(0.07,75.10,'NUMB'),(0.16,75.90,'TIGHT')]:
        if t>=tt:
            p=appear(t,tt,0.14); fade=1-0.75*clamp((t-79.6)/0.5); col=RED if fade>0.5 else (110,110,120)
            x=X(u); y=Y(0.86)-34
            d.polygon([(x,y-36),(x-22,y),(x+22,y)],fill=A(col,a*p*fade)); txt(d,x,y-6,'!',f(BEB,30),WHITE,a*p*fade,anchor='ms')
            tag(d,x,y-92,lab,col,22,a*p*fade,anchor='c')
    for (u,lab,tt) in [(0.11,'HIGH',74.3),(0.30,'DROP',76.8),(0.485,'HOLD',79.04),(0.80,'REBUILD',80.9)]:
        if t>=tt: txt(d,X(u),y1+16,lab,f(MONO,24),CREAM,a*appear(t,tt),anchor='ma')
    if t>=85.18: tag(d,x0+10,y1+70,'SYMPTOMS = SIGNAL, NOT FAILURE',AMBER,24,a*appear(t,85.5)) if False else None
def scene_attention(d,im,t):
    a=win(t,86.40,89.62,0.18,0.15)
    if a<=0: return
    cx,cy=880,470; blink=1.0 if t<88.40 else (1.0 if int((t-88.40)*5)%2==0 else 0.35)
    frosted(im,(cx-120,cy-110,cx+120,cy+120),0.85,10,26); d=ImageDraw.Draw(im,'RGBA')
    panel_frame(d,(cx-120,cy-110,cx+120,cy+120),a,AMBER,L=26)
    tri=[(cx,cy-74),(cx-74,cy+50),(cx+74,cy+50)]
    d.polygon(tri,fill=A(AMBER,a*blink))
    if GL is not None: GL.polygon(tri,fill=A(AMBER,a*blink))
    txt(d,cx,cy+40,'!',f(BEB,96),INK,a,anchor='ms')
    txt(d,cx,cy+66,'CHECK',f(MONO,26),AMBER,a,anchor='ma')
def scene_checklist(d,im,t):
    a=win(t,89.80,93.30,0.2,0.16)
    if a<=0: return
    box=(60,400,520,700); frosted(im,box,0.88,10,18); d=ImageDraw.Draw(im,'RGBA')
    panel_frame(d,box,a,GREEN,L=30)
    txt(d,88,420,'PROTOCOL',f(MONO,24),GREEN,a)
    for i,(lab,tt) in enumerate([('TITRATE SLOW',90.14),('SODIUM + WATER',91.18),('WATCH SYMPTOMS',92.44)]):
        y=474+i*72; ra=a*appear(t,89.9+i*0.05,0.2)
        d.rounded_rectangle([88,y,128,y+40],radius=6,outline=A((120,124,140),ra),width=3)
        if t>=tt: check(d,93,y+4,GREEN,1.0,a*appear(t,tt,0.12))
        txt(d,146,y+2,lab,f(BEB,48),WHITE if t>=tt else (130,134,150),ra)
LOGO=None
def scene_cta(d,im,t):
    global LOGO
    a=appear(t,93.80,0.3)
    if a<=0: return
    box=(60,1010,1020,1400);
    d.rounded_rectangle(box,radius=20,fill=A((8,10,18),0.94*a)); panel_frame(d,box,a)
    if LOGO is None:
        lg=Image.open(HERE+'/../../brand/logo/coach-agz-logo-round.jpg').convert('RGB'); s=min(lg.size)
        lg=lg.crop(((lg.width-s)//2,(lg.height-s)//2,(lg.width+s)//2,(lg.height+s)//2)).resize((190,190),Image.LANCZOS)
        m=Image.new('L',(190,190),0); ImageDraw.Draw(m).ellipse([0,0,189,189],fill=255); lg.putalpha(m); LOGO=lg
    lg=LOGO.copy(); lg.putalpha(lg.split()[3].point(lambda v:int(v*a))); im.alpha_composite(lg,(90,1045))
    d=ImageDraw.Draw(im,'RGBA')
    if t>=94.40: txt(d,310,1050,'FREE · FULL GH PROTOCOL',f(MONO,30),VGOLD,appear(t,94.40))
    if t>=96.14: txt(d,310,1094,'+ water retention management',f(DMS,32,600),CREAM,appear(t,96.14))
    if t>=98.68:
        b=expo((t-98.68)/0.12); s=lerp(1.12,1.0,b)
        fn=f(BEB,int(96*s)); label='COMMENT  "GH"'; tw=d.textlength(label,font=fn)
        lit_bar(d,310,1150,310+tw+44,1150+int(112*s),VGOLD,b); d.text((332,1158),label,font=fn,fill=A(INK,b))
        if GL is not None: GL.rectangle([306,1146,314+tw+44,1154+int(112*s)],outline=A(VGOLD,b),width=12)
    txt(d,90,1300,'@coach.agz',f(MONO,26),GOLD,a)
    txt(d,90,1340,'FOR RESEARCH & EDUCATIONAL PURPOSES ONLY',f(MONO,20),(124,124,130),a)
# graphic scenes bound to layouts: (t0, t1, fn)
LAYOUT_SCENES=[(6.34,14.10,scene_bodymap),(14.3,27.62,scene_kidney),(27.80,46.70,scene_wrist),(66.58,73.62,scene_risk),(73.88,86.06,scene_dose)]
# ---------------- text hook + topic band ----------------
def text_hook(im,t):
    if t>=6.15: return
    a=1.0 if t<6.0 else 1-clamp((t-6.0)/0.15)
    s=lerp(1.0,1.04,clamp(t/6.0))
    lines=[[('HGH',VGOLD),(' hand numbness',WHITE)],[('starts in your kidneys',WHITE)]]
    fn=f(DMS,int(76*s),800)
    lay=Image.new('RGBA',(W,H),(0,0,0,0)); d=ImageDraw.Draw(lay)
    widths=[sum(d.textlength(sg,font=fn) for sg,_ in ln) for ln in lines]
    lh=int(96*s); y=300-int(10*(s-1)*100)
    bw=max(widths)+72; bx0=(W-bw)/2
    d.rounded_rectangle([bx0,y-22,bx0+bw,y+lh*2+14],radius=26,fill=(0,0,0,int(215)))
    for i,ln in enumerate(lines):
        x=(W-widths[i])/2
        for sg,col in ln:
            d.text((x,y+i*lh),sg,font=fn,fill=col+(255,)); x+=d.textlength(sg,font=fn)
    if a<1: lay.putalpha(lay.split()[3].point(lambda v:int(v*a)))
    im.alpha_composite(lay)
def topic_band(im,t):
    if not (6.0<=t<46.87): return
    a=appear(t,6.0,0.15)
    d=ImageDraw.Draw(im,'RGBA')
    d.rectangle([8,212,W,350],fill=NAVY+(int(228*a),)); d.line([(64,240),(108,240)],fill=A(GOLD,a),width=4); d.text((122,224),'@coach.agz',font=f(MONO,26),fill=A(GOLD,a))
    fn=f(DMS,60,800); x=64; y=262
    for sg,col in [('Why ',CREAM),('HGH',VGOLD),(' numbs your hands',CREAM)]:
        d.text((x,y),sg,font=fn,fill=A(col,a)); x+=d.textlength(sg,font=fn)
# ---------------- captions ----------------
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
    end=WORDS[lo[-1]]['e']+0.6
    nxt=[g for g in GROUPS if WORDS[g[0]]['s']>WORDS[lo[0]]['s']]
    if t>end and (not nxt or WORDS[nxt[0][0]]['s']>t): return None
    return lo
ACCENT={'HGH':VGOLD,'GH':VGOLD,'IGF-1':VGOLD,'KIDNEYS':VGOLD,'KIDNEY':VGOLD,'SODIUM':VGOLD,'4':VGOLD,'IUS':VGOLD,'CARPAL':VGOLD,'TUNNEL':VGOLD,'MEDIAN':VGOLD,
        'NUMB':RED,'NUMBING':RED,'NUMBNESS':RED,'TINGLING':RED,'SQUEEZED':RED,'COMPRESSES':RED,'CHOKES':RED,'WEAKNESS':RED,'SWELL':RED,'IGNORE':RED}
def captions(im,t,L):
    if t<6.0: return   # text hook owns the frame; spoken hook is short
    g=group_at(t)
    if not g: return
    d=ImageDraw.Draw(im,'RGBA')
    ws=[{'IUS':'IU'}.get(WORDS[i]['w'].upper().rstrip(',.?!'),WORDS[i]['w'].upper().rstrip(',.?!')) for i in g]
    size=int(L['cs']); CAP_Y=int(L['cap'])
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
    cap=Image.new('RGBA',(W,300),(0,0,0,0)); cd=ImageDraw.Draw(cap); shd=Image.new('RGBA',(W,300),(0,0,0,0)); sd=ImageDraw.Draw(shd)
    prev=max(0,act-1); bt=expo((t-WORDS[g[act]]['s'])/0.07) if act>0 else 1
    bx0=lerp(xs[prev],xs[act],bt)-18; bx1=lerp(xs[prev]+wd[prev],xs[act]+wd[act],bt)+18
    for k,(w_,x_) in enumerate(zip(ws,xs)):
        if k!=act: sd.text((x_+4,46),w_,font=fn,fill=(0,0,0,210))
    cap.alpha_composite(shd.filter(ImageFilter.GaussianBlur(6)))
    lit_bar(cd,bx0,40+size*0.02,bx1,40+size*0.98,RED)
    for k,(w_,x_) in enumerate(zip(ws,xs)):
        col=CREAM
        if k!=act and WORDS[g[k]]['s']<=t: col=ACCENT.get(w_,CREAM) if ACCENT.get(w_)!=RED else CREAM
        if k!=act and ACCENT.get(w_)==VGOLD and WORDS[g[k]]['s']<=t: col=VGOLD
        cd.text((x_,40),w_,font=fn,fill=col,stroke_width=0 if k==act else 3,stroke_fill=(0,0,0))
    if abs(s-1)>0.002:
        cap=cap.resize((int(W*s),int(300*s)),Image.BICUBIC); ox=int((W-cap.width)/2); oy=int(CAP_Y-40-(cap.height-300)/2)
    else: ox,oy=0,CAP_Y-40
    im.alpha_composite(cap,(ox,oy))
# ---------------- frame ----------------
IMPACTS=[65.80,82.72]   # 2-frame shake
def frame(src,t):
    global GL
    im,L=compose_footage(src,t)
    # gentle top/bottom scrim on full-frame footage for caption/band legibility
    g=L['g']
    if g<0.99:
        yy=np.arange(H); al=np.where(yy>1220,np.clip((yy-1220)/260,0,1)*100,0); al=np.maximum(al,np.where(yy<420,(1-yy/420)*110,0)); al=(al*(1-g)).astype(np.uint8)
        im.alpha_composite(Image.merge('RGBA',[Image.new('L',(W,H),c) for c in NAVY]+[Image.fromarray(np.repeat(al[:,None],W,1))]))
    glow=Image.new('RGBA',(W,H),(0,0,0,0)); GL=ImageDraw.Draw(glow,'RGBA')
    window_ring(t,L)
    d=ImageDraw.Draw(im,'RGBA')
    for (t0,t1,fn) in LAYOUT_SCENES:
        if t0<=t<t1+0.2:
            a=appear(t,t0,0.25)*(1-clamp((t-t1)/0.16))
            if a>0:
                lay=Image.new('RGBA',(W,H),(0,0,0,0)); ld=ImageDraw.Draw(lay,'RGBA'); fn(ld,t,1.0)
                if a<1: lay.putalpha(lay.split()[3].point(lambda v:int(v*a)))
                im.alpha_composite(lay)
    scene_compress(d,im,t); scene_stepper(d,im,t); scene_attention(d,im,t); scene_checklist(d,im,t)
    d=ImageDraw.Draw(im,'RGBA')
    if t>=93.38: scene_cta(d,im,t)
    GL=None
    if glow.getbbox():
        sm=glow.resize((W//4,H//4),Image.BILINEAR)
        g1=np.asarray(sm.filter(ImageFilter.GaussianBlur(3.5))).astype(np.float32)/255; g2=np.asarray(sm.filter(ImageFilter.GaussianBlur(10))).astype(np.float32)/255
        prem=np.clip(g1[...,:3]*g1[...,3:]*2.0+g2[...,:3]*g2[...,3:]*1.6,0,1)
        prem=np.asarray(Image.fromarray((prem*255).astype(np.uint8)).resize((W,H),Image.BILINEAR)).astype(np.float32)/255
        b=np.asarray(im.convert('RGB')).astype(np.float32)/255
        im=Image.fromarray(((1-(1-b)*(1-prem))*255).astype(np.uint8)).convert('RGBA')
    text_hook(im,t); topic_band(im,t)
    captions(im,t,L)
    d=ImageDraw.Draw(im,'RGBA'); d.rectangle([0,0,7,H],fill=GOLD)
    out=im.convert('RGB')
    for t1 in IMPACTS:
        k=round((t-t1)*FPS)
        if k in (1,2):
            dx=[9,-5][k-1]; z=1.02; big=out.resize((int(W*z),int(H*z)),Image.BICUBIC); ox=(big.width-W)//2-dx; oy=(big.height-H)//2
            out=big.crop((ox,oy,ox+W,oy+H)); ImageDraw.Draw(out).rectangle([0,0,7,H],fill=GOLD)
    return out
if __name__=='__main__':
    SRC=S+'/src/v30.mp4'
    mode=sys.argv[2]
    if mode=='stills':
        os.makedirs(S+'/qc',exist_ok=True)
        for tt in [float(x) for x in sys.argv[3:]]:
            n=round(tt*FPS)
            subprocess.run(['ffmpeg','-v','error','-y','-ss',f'{n/FPS:.4f}','-i',SRC,'-frames:v','1',S+'/qc/_src.png'])
            frame(Image.open(S+'/qc/_src.png').convert('RGB'),n/FPS).resize((540,960),Image.LANCZOS).save(S+f'/qc/st_{tt:06.2f}.jpg',quality=88)
        sys.exit()
    n0,n1=int(sys.argv[3]),int(sys.argv[4]); out=sys.argv[5]
    dec=subprocess.Popen(['ffmpeg','-v','error','-ss',f'{n0/FPS:.4f}','-i',SRC,'-frames:v',str(n1-n0),'-f','rawvideo','-pix_fmt','rgb24','-'],stdout=subprocess.PIPE)
    enc=subprocess.Popen(['ffmpeg','-v','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-','-c:v','libx264','-crf','14','-preset','fast','-pix_fmt','yuv420p',out],stdin=subprocess.PIPE)
    for n in range(n0,n1):
        buf=dec.stdout.read(W*H*3)
        if len(buf)<W*H*3: print('short',n); break
        enc.stdin.write(frame(Image.frombuffer('RGB',(W,H),buf),n/FPS).tobytes())
    enc.stdin.close(); enc.wait(); dec.kill(); print('done',n0,n1)
