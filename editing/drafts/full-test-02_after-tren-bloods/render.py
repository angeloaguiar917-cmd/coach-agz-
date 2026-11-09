# After Tren bloods — 1080x1920 30fps render. Usage:
#   python3 render.py <workdir> stills t1 t2 ...      -> <workdir>/qc/st_<t>.jpg
#   python3 render.py <workdir> chunk n0 n1 out.mp4   -> frames n0..n1-1 (silent)
# <workdir> holds assembled.mov, words_cap.json, logo.jpg; fonts in <workdir>/../fonts/
import json, subprocess, sys, math
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
S=sys.argv[1].rstrip('/')+'/'; F=S+'../fonts/'
W,H=1080,1920; FPS=30; DUR=102.4333
WORDS=json.load(open(S+'words_cap.json'))
CUTS=[7.8667,15.9333,21.3,44.7,59.5,77.7,89.1667,90.4,93.7667,100.1333]
GOLD=(201,169,110); CREAM=(244,241,234); NAVY=(14,17,23); MUTED=(150,150,158)
RED=(255,34,28); VGOLD=(255,194,26); CYAN=(0,229,255); GREEN=(30,255,110); DEEP=(2,3,8); INK=(6,8,14); WHITE=(255,255,255)
AMBER=(240,160,48); COARED=(210,10,20); PANEL=(10,14,24)
FONTS={'mono':('JBMono.ttf',500),'mono7':('JBMono.ttf',700),'beb':('BebasNeue.ttf',None),'bar':('BarlowCondensed-700.ttf',None),
       'bar6':('BarlowCondensed-600.ttf',None),'dm':('DMSans.ttf',400),'dm7':('DMSans.ttf',700)}
_fc={}
def f(n,s):
    k=(n,int(s))
    if k not in _fc:
        fn,wg=FONTS[n]; ft=ImageFont.truetype(F+fn,int(s))
        if wg:
            try:
                axes=ft.get_variation_axes(); vals=[]
                for ax in axes:
                    nm=ax.get('name',b'')
                    nm=nm.decode() if isinstance(nm,bytes) else str(nm)
                    vals.append(wg if 'eight' in nm.lower() or nm.lower()=='wght' else ax.get('default',min(max(int(s),ax['minimum']),ax['maximum'])))
                ft.set_variation_by_axes(vals)
            except Exception: pass
        _fc[k]=ft
    return _fc[k]
def clamp(x,a=0,b=1): return max(a,min(b,x))
def expo(x): x=clamp(x); return 1 if x>=1 else 1-2**(-10*x)
def ease_io(x): x=clamp(x); return 4*x**3 if x<.5 else 1-(-2*x+2)**3/2
def back(x,s=1.2): x=clamp(x); return 1+(s+1)*(x-1)**3+s*(x-1)**2   # slight settle for heavy needles only
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
    if x1<x0: x0,x1=x1,x0
    h=max(1,int(y1-y0))
    for i in range(h):
        k=i/h; c=tuple(int(min(255,v*(1.18-0.36*k)+(40 if k<0.12 else 0))) for v in col)
        d.line([(x0,y0+i),(x1,y0+i)],fill=c+(int(255*a),))
def tag(d,x,y,label,col=RED,size=32,a=1.0,glow=True):
    if a<=0: return x
    fn=f('mono7',size); tw=d.textlength(label,font=fn); h=size+16
    lit_bar(d,x,y,x+tw+24,y+h,col,a); d.text((x+12,y+6),label,font=fn,fill=A(INK if col in (VGOLD,GREEN,CYAN) else WHITE,a))
    if GL and glow: GL.rectangle([x-4,y-4,x+tw+28,y+h+4],outline=A(col,a),width=8)
    return x+tw+24
def tag_w(d,label,size): return d.textlength(label,font=f('mono7',size))+24
def chip(d,x,y,label,a=1.0,size=34):
    fn=f('bar',size); tw=d.textlength(label,font=fn)
    d.rounded_rectangle([x,y,x+tw+36,y+size+20],radius=8,fill=A((40,8,12),a),outline=A(RED,a),width=3)
    d.text((x+18,y+8),label,font=fn,fill=A((255,150,140),a)); return x+tw+36
def flag(d,box,label,t0,t,side='right',size=28):
    p=expo((t-t0)/0.14)
    if p<=0: return
    x0,y0,x1,y1=box; brackets(d,x0,y0,x1,y1,A(RED,1),26,6)
    if GL: brackets(GL,x0,y0,x1,y1,A(RED,1),26,12)
    q=clamp((p-0.3)/0.7)
    if q>0:
        for seg in [((x0,y0),(lerp(x0,x1,q),y0)),((x1,y1),(lerp(x1,x0,q),y1)),((x0,y1),(x0,lerp(y1,y0,q))),((x1,y0),(x1,lerp(y0,y1,q)))]:
            d.line(seg,fill=A(RED,1),width=3)
    if p>0.5 and label:
        if side=='right': tag(d,x1+12,(y0+y1)/2-22,label,size=size)
        elif side=='above': tag(d,x0,y0-size-26,label,size=size)
        elif side=='left': tag(d,x0-12-tag_w(d,label,size),(y0+y1)/2-22,label,size=size)
        else: tag(d,x0,y1+10,label,size=size)
def node(d,x0,y0,x1,y1,title,sub,col,a=1.0,dim=False,ts=44):
    c=col if not dim else tuple(int(v*0.3) for v in col)
    d.rounded_rectangle([x0,y0,x1,y1],radius=14,fill=A(PANEL,0.95*a),outline=A(c,a),width=4)
    if GL and not dim: GL.rounded_rectangle([x0,y0,x1,y1],radius=14,outline=A(col,a*0.8),width=8)
    fn=f('beb',ts); tw=d.textlength(title,font=fn); d.text(((x0+x1)/2-tw/2,y0+12),title,font=fn,fill=A(WHITE if not dim else (100,100,110),a))
    if sub:
        fs=f('mono',22); sw=d.textlength(sub,font=fs); d.text(((x0+x1)/2-sw/2,y1-36),sub,font=fs,fill=A(c,a))
def arrow(d,x0,y0,x1,y1,col,w=5,a=1.0,L=18):
    d.line([(x0,y0),(x1,y1)],fill=A(col,a),width=w)
    ang=math.atan2(y1-y0,x1-x0)
    d.polygon([(x1,y1),(x1-L*math.cos(ang-0.45),y1-L*math.sin(ang-0.45)),(x1-L*math.cos(ang+0.45),y1-L*math.sin(ang+0.45))],fill=A(col,a))
def tri_up(d,x,y,s,col,a=1.0,down=False):
    if down: d.polygon([(x,y),(x+s,y),(x+s/2,y+s*0.9)],fill=A(col,a))
    else: d.polygon([(x,y+s*0.9),(x+s,y+s*0.9),(x+s/2,y)],fill=A(col,a))
def flow(d,x0,y0,x1,y1,t,col,n=5,speed=0.9,a=1.0,r=7):
    for k in range(n):
        p=(t*speed+k/n)%1; x=lerp(x0,x1,p); y=lerp(y0,y1,p); fa=a*min(1,p*6,(1-p)*6)
        d.ellipse([x-r,y-r,x+r,y+r],fill=A(col,fa))
        if GL: GL.ellipse([x-r*2,y-r*2,x+r*2,y+r*2],fill=A(col,fa))
def meter(d,x0,y0,x1,y1,frac,col,label,value=None,a=1.0,vcol=None):
    if label: d.text((x0,y0-40),label,font=f('mono',26),fill=A(CREAM,a))
    d.rectangle([x0,y0,x1,y1],outline=A((70,74,90),a),width=2)
    xf=lerp(x0+3,x1-3,clamp(frac))
    if xf>x0+3:
        lit_bar(d,x0+3,y0+3,xf,y1-3,col,a)
        if GL: GL.rectangle([x0+3,y0+3,xf,y1-3],fill=A(col,a*0.7))
    if value:
        fn=f('beb',42); tw=d.textlength(value,font=fn); d.text((x1-tw,y0-50),value,font=fn,fill=A(vcol or col,a))
def check(d,x,y,col,s=1.0,a=1.0):
    d.line([(x,y+16*s),(x+10*s,y+28*s),(x+30*s,y+2*s)],fill=A(col,a),width=int(6*s))
    if GL: GL.line([(x,y+16*s),(x+10*s,y+28*s),(x+30*s,y+2*s)],fill=A(col,a),width=int(12*s))
def cross(d,x,y,col,s=1.0,a=1.0):
    d.line([(x,y),(x+28*s,y+28*s)],fill=A(col,a),width=int(6*s)); d.line([(x+28*s,y),(x,y+28*s)],fill=A(col,a),width=int(6*s))
    if GL: GL.line([(x,y),(x+28*s,y+28*s)],fill=A(col,a),width=12); GL.line([(x+28*s,y),(x,y+28*s)],fill=A(col,a),width=12)
def frosted(im,box,dark=0.86,blur=10):
    x0,y0,x1,y1=[int(v) for v in box]; x0=max(0,x0); y0=max(0,y0); x1=min(W,x1); y1=min(H,y1)
    if x1<=x0 or y1<=y0: return
    reg=im.crop((x0,y0,x1,y1)).convert('RGB').filter(ImageFilter.GaussianBlur(blur))
    im.paste(Image.blend(reg,Image.new('RGB',reg.size,DEEP),dark).convert('RGBA'),(x0,y0))
def fade_layer(lay,al):
    if al<1: lay.putalpha(lay.split()[3].point(lambda v:int(v*al)))
    return lay

# ======================= SCENES =======================
# ---- A. cycle strip (lower card) ----
def sc_cycle(d,t,b):
    x0,y0,x1,y1=b
    txt(d,x0+36,y0+70,'DOSE',f('mono',26),CREAM,appear(t,1.84))
    if t>=1.84: meter(d,x0+140,y0+74,x0+520,y0+104,lerp(0,0.95,expo((t-1.84)/0.4)),RED,None,None,1)
    if t>=2.0: tag(d,x0+544,y0+66,'HIGH',RED,26,appear(t,2.0))
    cw=(x1-x0-72-11*8)/12
    wk=int(clamp((t-2.56)/0.7)*12+0.0001)
    for i in range(12):
        cx=x0+36+i*(cw+8); cy=y0+136
        on=i<wk
        if on: lit_bar(d,cx,cy,cx+cw,cy+44,VGOLD,1)
        else: d.rectangle([cx,cy,cx+cw,cy+44],outline=A((80,84,100),1),width=2)
        if on and GL: GL.rectangle([cx,cy,cx+cw,cy+44],fill=A(VGOLD,0.5))
    txt(d,x0+36,y0+188,'WK 1',f('mono',22),MUTED); fn=f('mono',22); txt(d,x1-36-d.textlength('WK 12',font=fn),y0+188,'WK 12',fn,MUTED)
    if t>=2.56:
        fb=f('beb',64); s=f'{max(1,wk)} WEEKS'; txt(d,x1-36-d.textlength(s,font=fb),y0+48,s,fb,VGOLD)
    if t>=4.24:
        a=appear(t,4.24); xx=lerp(x0+36,x1-36,clamp((t-4.24)/0.45))
        d.line([(xx,y0+126),(xx,y0+190)],fill=A(CYAN,a),width=4)
        if GL: GL.line([(xx,y0+120),(xx,y0+196)],fill=A(CYAN,a),width=12)
# ---- B. mirror HUD (on footage) ----
def mirror_hud(im,t):
    if not (5.0<=t<12.05): return
    out=clamp((t-11.85)/0.2); a=appear(t,5.04,0.12)*(1-out)
    d=ImageDraw.Draw(im,'RGBA')
    x0,y0,x1,y1=120,540,960,1290
    brackets(d,x0,y0,x1,y1,A(CYAN,a),56,5)
    if GL: brackets(GL,x0,y0,x1,y1,A(CYAN,a),56,12)
    d.ellipse([x0+20,y0-50,x0+38,y0-32],fill=A(RED,a if int(t*4)%2==0 else a/3))
    txt(d,x0+50,y0-64,'MIRROR CHECK',f('mono7',36),CYAN,a)
    if t<6.1:   # scan sweep
        yy=lerp(y0,y1,clamp((t-5.1)/0.9)); d.line([(x0,yy),(x1,yy)],fill=A(CYAN,a*0.9),width=3)
        if GL: GL.line([(x0,yy),(x1,yy)],fill=A(CYAN,a),width=14)
    # callouts with leader lines
    for (lab,tt,tx,ty,px,py) in [('DRY',6.40,70,870,330,1110),('HARD',6.88,70,980,300,1215),('VASCULAR',7.20,700,1060,820,1230)]:
        p=appear(t,tt,0.14)*(1-out)
        if p<=0: continue
        fn=f('bar',46); tw=d.textlength(lab,font=fn); bw=tw+96
        bx=tx if tx<540 else tx
        anchor=(bx+bw,ty+36) if tx<540 else (bx,ty+36)
        e=(lerp(anchor[0],px,p),lerp(anchor[1],py,p))
        d.line([anchor,e],fill=A(GREEN,p),width=3); d.ellipse([px-8,py-8,px+8,py+8],outline=A(GREEN,p),width=3)
        if GL: GL.line([anchor,e],fill=A(GREEN,p*0.8),width=8)
        frosted(im,(bx,ty,bx+bw,ty+72),0.82,8); d=ImageDraw.Draw(im,'RGBA')
        d.rectangle([bx,ty,bx+bw,ty+72],outline=A(GREEN,p),width=2)
        check(d,bx+16,ty+20,GREEN,0.9,p); txt(d,bx+62,ty+10,lab,fn,WHITE,p)
    if t>=8.96:   # physique readout
        p=appear(t,8.96)*(1-out); bx,by=70,590
        frosted(im,(bx,by,bx+330,by+120),0.82,8); d=ImageDraw.Draw(im,'RGBA')
        d.rectangle([bx,by,bx+330,by+120],outline=A(GREEN,p*0.7),width=2)
        txt(d,bx+18,by+12,'PHYSIQUE',f('mono',24),CREAM,p)
        meter(d,bx+18,by+64,bx+312,by+96,lerp(0.2,1.0,expo((t-8.96)/0.5)),GREEN,None,None,p)
        if t>9.3: txt(d,bx+200,by+6,'PEAK',f('beb',44),GREEN,p)
    if t>=10.96:  # verdict stamp
        p=appear(t,10.96,0.1)*(1-out)
        bx=270; by=1170; tag(d,bx,by,'MIRROR  =  PASS',GREEN,40,p)
    if t>=11.76:
        p=appear(t,11.76,0.1)
        tag(d,270,1240-6,'BLOODWORK  =  ?',RED,40,p*(1-clamp((t-11.95)/0.1)))
# ---- C1. evidence card ----
def sc_research(d,t,b):
    x0,y0,x1,y1=b
    if t>=13.6:
        a=appear(t,13.6); fr=lerp(0,0.05,expo((t-13.6)/0.5))
        meter(d,x0+36,y0+110,x0+560,y0+146,fr,RED,'HUMAN RESEARCH',None,a)
        if t>=13.92: txt(d,x0+590,y0+92,'ALMOST NONE',f('beb',60),RED,appear(t,13.92))
    if t>=16.56:
        a=appear(t,16.56); x=chip(d,x0+36,y0+176,'ANECDOTAL',a)
        txt(d,x+24,y0+186,'= REAL-WORLD BLOODWORK',f('mono',26),CREAM,appear(t,17.2))
# ---- C2. 500+ panels ----
SHEET=None
def make_sheet():
    im=Image.new('RGBA',(230,300),(238,238,240,255)); d=ImageDraw.Draw(im)
    d.rectangle([0,0,230,34],fill=COARED); d.text((10,7),'LAB RESULTS',font=f('mono7',18),fill=WHITE)
    for i in range(9):
        y=50+i*26; d.rectangle([12,y,120,y+10],fill=(150,150,158)); d.rectangle([150,y,196,y+10],fill=(70,70,80))
    d.rectangle([6,44+4*26,224,44+4*26+22],outline=COARED,width=3); d.text((204,44+4*26),'H',font=f('mono7',18),fill=COARED)
    d.rectangle([6,44+7*26,224,44+7*26+22],outline=COARED,width=3); d.text((204,44+7*26),'L',font=f('mono7',18),fill=COARED)
    return im
def sc_panels(d,t,lay):
    global SHEET
    if SHEET is None: SHEET=make_sheet()
    # sheet stack fanning in (right)
    for i,ang in enumerate([-12,-6,0,6,12]):
        tt=18.40+i*0.16; p=appear(t,tt,0.14)
        if p<=0: continue
        r=SHEET.rotate(ang+(1-p)*8,expand=True,resample=Image.BICUBIC)
        r=fade_layer(r,p*(0.55+0.09*i))
        lay.alpha_composite(r,(int(600+i*44-r.width/2+120),int(lerp(600,560,p)+abs(ang)*1.5)))
    n=int(500*ease_io(clamp((t-18.32)/0.9)))
    fb=f('beb',290); s=f'{n}'; txt(d,100,560,s,fb,VGOLD)
    if GL: GL.text((100,560),s,font=fb,fill=A(VGOLD,0.55))
    if t>=19.24:
        p=appear(t,19.24,0.1); sw=d.textlength(s,font=fb); txt(d,100+sw+6,560,'+',fb,RED,p)
    txt(d,104,880,'BLOODWORK PANELS REVIEWED',f('mono7',32),CREAM,appear(t,19.36))
    if t>=20.72: txt(d,104,930,'OVER THE LAST FEW YEARS',f('mono',28),MUTED,appear(t,20.72))
    if t>=21.68:
        p=appear(t,21.68,0.1); tag(d,104,1010,'SAME PATTERN EVERY TIME',RED,40,p)
        flag(d,(640,560,980,920),'',21.68,t,'none')
# ---- D. HPTA axis ----
def sc_axis(d,t):
    load=appear(t,26.36,0.2) if t>=26.36 else 0
    off=t>=28.29
    bcol=RED if load>0.5 else CYAN
    node(d,100,560,600,670,'BRAIN','HYPOTHALAMUS · PITUITARY',bcol)
    lh=1.0-expo((t-23.64)/0.9) if t>=23.64 else 1.0
    fsh=1.0-expo((t-24.36)/0.8) if t>=24.36 else 1.0
    sig=max(lh,fsh)
    arrow(d,470,676,470,930,CYAN if sig>0.15 else (40,60,70),5)
    if sig>0.08: flow(d,470,680,470,920,t,CYAN,int(2+4*sig),0.9*sig+0.15,clamp(sig*1.4))
    txt(d,492,800,'LH · FSH',f('mono',26),CYAN if sig>0.15 else (70,80,90))
    node(d,100,940,600,1050,'TESTES','',CYAN,dim=off)
    txt(d,110,1074,'TESTOSTERONE PRODUCTION',f('mono',26),CREAM if not off else (90,90,100))
    if off:
        p=appear(t,28.29,0.1); flag(d,(90,930,610,1060),'',28.29,t,'none'); tag(d,110,1120,'OWN PRODUCTION  OFF',RED,32,p)
    # gauges
    for i,(lab,v,tt) in enumerate([('LH',lh,23.64),('FSH',fsh,24.36)]):
        gx=700+i*150; gy0,gy1=600,1020
        d.rounded_rectangle([gx,gy0,gx+90,gy1],radius=12,outline=A((90,94,110),1),width=3)
        hh=(gy1-gy0-10)*v*0.82
        if hh>2:
            col=CYAN if v>0.3 else RED; lit_bar(d,gx+6,gy1-5-hh,gx+84,gy1-5,col,1)
            if GL: GL.rectangle([gx+6,gy1-5-hh,gx+84,gy1-5],fill=A(col,0.6))
        fn=f('beb',48); txt(d,gx+45-d.textlength(lab,font=fn)/2,gy1+12,lab,fn,WHITE)
        if t>=25.16:
            p=appear(t,25.16,0.12); fz=f('beb',64); txt(d,gx+45-d.textlength('0',font=fz)/2,gy0+20,'0',fz,RED,p)
    if t>=26.05:   # androgen load entering brain
        p=appear(t,26.05,0.2); x=lerp(1000,620,expo((t-26.05)/0.35))
        tag(d,110,760,'TOTAL ANDROGEN LOAD',RED,26,p)
        arrow(d,200,756,200,676,RED,5,p)
# ---- E. HDL bars (lower card) ----
def sc_hdl(d,t,b):
    x0,y0,x1,y1=b; bx0=x0+250; bx1=x1-150; scale=(bx1-bx0)/60
    # baseline
    if t>=31.6:
        a=appear(t,31.6); txt(d,x0+36,y0+92,'BASELINE',f('bar',44),CREAM,a)
        v=52*expo((t-32.2)/0.5) if t>=32.2 else 0
        if v>0: lit_bar(d,bx0,y0+92,bx0+v*scale,y0+142,GREEN,a)
        if GL and v>0: GL.rectangle([bx0,y0+92,bx0+v*scale,y0+142],fill=A(GREEN,0.5))
        if t>=32.2: txt(d,bx0+v*scale+16,y0+84,f'{int(round(v))}',f('beb',64),GREEN,a)
    if t>=33.3:
        a=appear(t,33.3); txt(d,x0+36,y0+176,'ON TREN',f('bar',44),CREAM,a)
        v=lerp(52,18,expo((t-33.65)/0.6)) if t>=33.65 else 52
        col=RED if t>=33.65 else (90,94,110)
        lit_bar(d,bx0,y0+176,bx0+v*scale,y0+226,col,a)
        if GL and t>=33.65: GL.rectangle([bx0,y0+176,bx0+v*scale,y0+226],fill=A(RED,0.6))
        if t>=33.65: txt(d,bx0+v*scale+16,y0+168,f'{int(round(v))}',f('beb',64),RED,a)
        if t>=34.3:
            p=appear(t,34.3); tag(d,x1-170,y0+246,'-65%',RED,34,p); tri_up(d,x1-200,y0+256,26,RED,p,down=True)
    if t>=36.92:
        a=appear(t,36.92); bx=x0+36; by=y0+262
        x=tag(d,bx,by,'HEPATIC LIPASE',VGOLD,30,a); tri_up(d,x+12,by+8,30,VGOLD,a)
        if t>=38.84:
            p=appear(t,38.84); txt(d,x+60,by+6,'CLEARS HDL',f('mono7',30),RED,p)
    if 37.4<=t<39.8:   # HDL particles pulled off the bar into the enzyme
        for k in range(7):
            q=((t-37.4)*0.9+k/7)%1; sx=bx0+(k*67)%int(18*scale+1); sy=y0+200
            ex,ey=x0+150,y0+282; x=lerp(sx,ex,q**1.6); y=lerp(sy,ey,q)
            al=min(1,q*5,(1-q)*5); d.ellipse([x-7,y-7,x+7,y+7],fill=A(GREEN,al))
            if GL: GL.ellipse([x-12,y-12,x+12,y+12],fill=A(GREEN,al))
# ---- F. ApoB line chart + artery ----
def sc_apob(d,t):
    cx0,cy0,cx1,cy1=150,560,960,890
    vmin,vmax=60,145
    Y=lambda v: cy1-(v-vmin)/(vmax-vmin)*(cy1-cy0)
    d.line([(cx0,cy1),(cx1,cy1)],fill=A((90,94,110),1),width=2); d.line([(cx0,cy0),(cx0,cy1)],fill=A((90,94,110),1),width=2)
    for v in (80,100,120,140):
        d.line([(cx0,Y(v)),(cx1,Y(v))],fill=A((36,40,54),1),width=1); txt(d,cx0-60,Y(v)-14,str(v),f('mono',22),MUTED)
    if t>=43.19:   # 100+ zone
        a=appear(t,43.19,0.3); d.rectangle([cx0+2,cy0,cx1,Y(100)],fill=A(RED,0.16*a))
        d.line([(cx0,Y(100)),(cx1,Y(100))],fill=A(RED,a),width=3); txt(d,cx1-110,Y(100)+6,'100+',f('mono7',26),RED,a)
    pts=[(300,88,41.88),(560,100,43.19),(840,132,45.19)]
    for i,(x,v,tt) in enumerate(pts):
        if t<tt: continue
        if i>0:
            px,pv,_=pts[i-1]; q=expo((t-tt+0.25)/0.35)
            e=(lerp(px,x,q),lerp(Y(pv),Y(v),q)); col=RED if v>=100 else CYAN
            d.line([(px,Y(pv)),e],fill=A(col,1),width=6)
            if GL: GL.line([(px,Y(pv)),e],fill=A(col,1),width=14)
        p=appear(t,tt,0.12); col=CYAN if v<100 else RED
        d.ellipse([x-12,Y(v)-12,x+12,Y(v)+12],fill=A(WHITE,p),outline=A(col,p),width=4)
        fb=f('beb',60); s=str(v); txt(d,x-d.textlength(s,font=fb)/2,Y(v)-78,s,fb,col,p)
    # artery
    if t>=46.78:
        a=appear(t,46.78,0.25); ay0,ay1=970,1160
        txt(d,100,940,'ARTERY · CROSS-SECTION',f('mono',26),CREAM,a)
        plug=clamp((t-48.23)/1.6)
        d.rounded_rectangle([100,ay0,980,ay0+26],radius=12,fill=A((120,60,64),a)); d.rounded_rectangle([100,ay1-26,980,ay1],radius=12,fill=A((120,60,64),a))
        for k,(px,top) in enumerate([(260,1),(420,0),(600,1),(760,0),(880,1)]):
            r=lerp(0,26+8*(k%2),ease_io(plug-k*0.08) if plug>0 else 0)
            if r>1:
                cy=ay0+26 if top else ay1-26
                box=[px-r*2.6,cy-r,px+r*2.6,cy+r]
                d.chord(box,0 if top else 180,180 if top else 360,fill=A((150,96,40),a),outline=A(VGOLD,a),width=3)
                if GL: GL.chord(box,0 if top else 180,180 if top else 360,outline=A(VGOLD,a*0.8),width=6)
        n=int(lerp(6,22,clamp((t-47.59)/1.0)))
        for k in range(n):
            q=(t*0.35+k*0.618)%1; x=lerp(110,970,q); y=ay0+40+((k*53)%140)
            d.ellipse([x-6,y-6,x+6,y+6],fill=A(VGOLD,a*min(1,q*8,(1-q)*8)))
        if t>=48.23: tag(d,560,1180,'PLAQUE BUILD-UP',RED,28,appear(t,48.23))
        if t>=49.98: tag(d,100,1180,'LONG-TERM RISK',RED,28,appear(t,49.98))
# ---- G. hematocrit dial + ECG (lower card) ----
def sc_hct(d,t,b):
    x0,y0,x1,y1=b; cx,cy,R=x0+250,y0+300,180
    def ang(v): return math.radians(180+(clamp(v,40,60)-40)/20*180)
    for v0,v1,col in [(40,50,(70,90,110)),(50,54,AMBER),(54,60,RED)]:
        d.arc([cx-R,cy-R,cx+R,cy+R],180+(v0-40)*9,180+(v1-40)*9,fill=A(col,1),width=22)
        if GL and col!=(70,90,110): GL.arc([cx-R,cy-R,cx+R,cy+R],180+(v0-40)*9,180+(v1-40)*9,fill=A(col,0.7),width=30)
    for v in range(40,61,5):
        a_=ang(v); d.line([(cx+(R-34)*math.cos(a_),cy+(R-34)*math.sin(a_)),(cx+(R-14)*math.cos(a_),cy+(R-14)*math.sin(a_))],fill=A(WHITE,1),width=3)
        s=str(v); fn=f('mono',22); txt(d,cx+(R-62)*math.cos(a_)-d.textlength(s,font=fn)/2,cy+(R-62)*math.sin(a_)-12,s,fn,MUTED)
    v=46
    for tt,tv in [(52.78,54),(53.34,55),(53.91,56)]:
        if t>=tt: v=lerp(v,tv,back((t-tt)/0.35,0.9))
    a_=ang(v); col=RED if v>=54 else (AMBER if v>=50 else CYAN)
    d.line([(cx,cy),(cx+(R-30)*math.cos(a_),cy+(R-30)*math.sin(a_))],fill=A(WHITE,1),width=6)
    if GL: GL.line([(cx,cy),(cx+(R-30)*math.cos(a_),cy+(R-30)*math.sin(a_))],fill=A(col,1),width=12)
    d.ellipse([cx-16,cy-16,cx+16,cy+16],fill=A(col,1))
    if t>=52.78:
        fb=f('beb',96); s=f'{int(round(v))}%'; txt(d,cx-d.textlength(s,font=fb)/2,cy+22,s,fb,col)
    rx=x0+520
    for i,(lab,tt,col) in enumerate([('EPO',55.91,VGOLD),('RED BLOOD CELLS',57.19,VGOLD)]):
        if t>=tt:
            p=appear(t,tt); y=y0+80+i*66; txt(d,rx,y,lab,f('bar',46),WHITE,p); fn=f('bar',46)
            tri_up(d,rx+d.textlength(lab,font=fn)+16,y+12,30,col,p)
    if t>=58.70: tag(d,rx,y0+220,'THICKER BLOOD',RED,32,appear(t,58.70))
    if t>=60.38:   # ECG trace
        p=appear(t,60.38,0.2); ex0,ex1,ey=rx,x1-30,y0+360
        pts=[]
        for k in range(160):
            x=lerp(ex0,ex1,k/159); ph=((k/159)*3.2 - (t-60.38)*2.4)%1
            yv=-70*math.exp(-((ph-0.5)/0.018)**2)+22*math.exp(-((ph-0.56)/0.02)**2)-14*math.exp(-((ph-0.3)/0.05)**2)-18*math.exp(-((ph-0.75)/0.06)**2)
            pts.append((x,ey+yv))
        d.line(pts,fill=A(RED,p),width=4)
        if GL: GL.line(pts,fill=A(RED,p),width=10)
        txt(d,rx,ey+40,'HEART WORKLOAD',f('mono7',28),CREAM,appear(t,60.87)); tri_up(d,rx+300,ey+44,24,RED,appear(t,60.87))
# ---- H1. lab order document ----
DOC=None
ROWS=['LH','FSH','HDL','ApoB','HEMATOCRIT','PROLACTIN']
def make_doc(hl=0.0):
    im=Image.new('RGBA',(760,640),(242,242,244,255)); d=ImageDraw.Draw(im)
    d.rectangle([0,0,760,74],fill=(16,24,48)); d.text((26,18),'LAB ORDER · REQUISITION',font=f('mono7',32),fill=WHITE)
    d.text((26,92),'Patient: ____________   Panel: ON-CYCLE',font=f('mono',22),fill=(110,110,120))
    for i,r in enumerate(ROWS):
        y=150+i*78
        if r=='PROLACTIN' and hl>0: d.rectangle([92,y-6,92+lerp(0,330,hl),y+48],fill=(255,214,90))
        d.rectangle([30,y,72,y+42],outline=(60,60,70),width=3)
        d.text((100,y-2),r,font=f('dm7',38),fill=INK); d.line([(26,y+62),(734,y+62)],fill=(215,215,220),width=2)
        if r!='PROLACTIN':
            d.line([(36,y+22),(48,y+34),(68,y+6)],fill=(20,120,60),width=6)
    return im
def sc_doc(d,t,lay):
    global DOC
    DOC=make_doc(clamp((t-66.70)/0.3) if t>=66.70 else 0)
    p=expo((t-62.62)/0.35); x=lerp(1100,160,p); ang=lerp(-9,-2,p)
    r=DOC.rotate(ang,expand=True,resample=Image.BICUBIC); lay.alpha_composite(r,(int(x-20),540))
    ox,oy=int(x-20),540
    py=oy+150+5*78+int((x-160)*math.sin(math.radians(2)))+18
    if t>=64.55:
        flag(d,(ox+20,py-14,ox+760,py+58),'MOST GUYS SKIP',64.55,t,'below',30)
    if t>=67.0: tag(d,ox+470,py-2,'LIBIDO MARKER',VGOLD,26,appear(t,67.0))
# ---- H2. receptor binding ----
def cup(d,x,y,col,filled,fcol,a=1.0,s=1.0):
    w=int(90*s)
    d.arc([x,y,x+w,y+w],0,180,fill=A(col,a),width=6); d.line([(x,y+w/2),(x,y-6)],fill=A(col,a),width=6); d.line([(x+w,y+w/2),(x+w,y-6)],fill=A(col,a),width=6)
    if filled>0:
        r=w*0.36*filled; cx=x+w/2; cy=y+w*0.42
        d.ellipse([cx-r,cy-r,cx+r,cy+r],fill=A(fcol,a))
        if GL: GL.ellipse([cx-r*1.4,cy-r*1.4,cx+r*1.4,cy+r*1.4],fill=A(fcol,a*0.8))
def sc_receptor(d,t):
    a=appear(t,67.6,0.2)
    node(d,390,560,690,660,'TREN','TRENBOLONE',VGOLD,a)
    # receptors
    for i,(nm,sub,x,tt,col) in enumerate([('ANDROGEN','AR',150,71.34,VGOLD),('PROGESTERONE','PR',620,68.86,RED)]):
        lit=appear(t,tt,0.2) if t>=tt else 0
        txt(d,x,880,nm,f('beb',50),WHITE if lit else (150,150,160),a); txt(d,x,936,'RECEPTOR · '+sub,f('mono',24),col,a)
        cup(d,x+60,1000,col if lit else (90,94,110),lit,col,a,1.3)
        if t>=tt-0.4:   # molecule travels down
            q=expo((t-(tt-0.4))/0.4); sx,sy=540,665; ex,ey=x+60+58,1000+48
            if q<1:
                mx,my=lerp(sx,ex,q),lerp(sy,ey,q); d.ellipse([mx-18,my-18,mx+18,my+18],fill=A(col,1))
                if GL: GL.ellipse([mx-26,my-26,mx+26,my+26],fill=A(col,1))
            arrow(d,sx,sy,lerp(sx,ex-0,min(q,1)*0.82),lerp(sy,ey-60,min(q,1)*0.82),col,4,0.7)
    if t>=69.4:
        p=appear(t,69.4); tag(d,620,1150,'PROLACTIN',RED,32,p); fn=f('mono7',32); tri_up(d,620+tag_w(d,'PROLACTIN',32)+14,1158,32,RED,p)
    if t>=70.39: txt(d,150,1160,'NOT JUST AR',f('mono7',30),VGOLD,appear(t,70.39))
# ---- I. libido curve (lower card) ----
def lib(w): return 0.82+0.08*math.exp(-((w-3.5)/1.6)**2) if w<6 else 0.82*(0.5+0.5*math.cos(math.pi*clamp((w-6)/5.2)))+0.06+0.0*w
def sc_libido(d,t,b):
    x0,y0,x1,y1=b; cx0,cy0,cx1,cy1=x0+60,y0+90,x1-40,y1-70
    X=lambda w: lerp(cx0,cx1,(w-1)/11); Y=lambda v: cy1-v*(cy1-cy0)
    d.line([(cx0,cy1),(cx1,cy1)],fill=A((90,94,110),1),width=2)
    for w in range(1,13):
        d.line([(X(w),cy1),(X(w),cy1+8)],fill=A((90,94,110),1),width=2)
        if w in (1,4,8,12): s=f'WK {w}'; fn=f('mono',20); txt(d,X(w)-d.textlength(s,font=fn)/2,cy1+14,s,fn,MUTED)
    if t>=80.12:   # later weeks zone
        a=appear(t,80.12,0.3); d.rectangle([X(8),cy0,X(12),cy1],fill=A(RED,0.14*a)); txt(d,X(8)+10,cy0+4,'LATER WEEKS',f('mono7',24),RED,a)
    w1=1+5*clamp((t-73.34)/2.2); w2=6+6*clamp((t-78.12)/1.7) if t>=78.12 else 6
    def seg(wa,wb,col):
        pts=[(X(w),Y(lib(w))) for w in np.linspace(wa,wb,max(2,int((wb-wa)*14)))]
        d.line(pts,fill=A(col,1),width=7)
        if GL: GL.line(pts,fill=A(col,1),width=14)
    if t>=73.34: seg(1,w1,GREEN)
    if t>=78.12: seg(6,w2,RED)
    if t>=77.03:
        p=appear(t,77.03); tag(d,X(2.3),Y(lib(3.5))-62,'EVERY 10 MIN',GREEN,26,p)
    if t>=79.48: tag(d,X(9.2)-40,Y(lib(9.6))-70,'FALLS APART',RED,26,appear(t,79.48))
# ---- J. roadmap ----
ROUTE=[(150,1090),(300,1060),(420,980),(420,900),(560,840),(760,840),(880,770),(880,690),(760,620),(600,600)]
def _route_len():
    L=[0]
    for a_,b_ in zip(ROUTE,ROUTE[1:]): L.append(L[-1]+math.dist(a_,b_))
    return L
RL=_route_len()
def route_pt(fr):
    s=fr*RL[-1]
    for i in range(len(ROUTE)-1):
        if s<=RL[i+1]: q=(s-RL[i])/(RL[i+1]-RL[i]+1e-9); return (lerp(ROUTE[i][0],ROUTE[i+1][0],q),lerp(ROUTE[i][1],ROUTE[i+1][1],q))
    return ROUTE[-1]
def pin(d,x,y,num,col,a=1.0):
    d.ellipse([x-26,y-78,x+26,y-26],fill=A(col,a)); d.polygon([(x-20,y-42),(x+20,y-42),(x,y)],fill=A(col,a))
    fn=f('beb',40); s=str(num); txt(d,x-d.textlength(s,font=fn)/2,y-74,s,fn,INK,a)
    if GL: GL.ellipse([x-30,y-82,x+30,y-22],fill=A(col,a*0.7))
STOPS=[(0.00,'BIOMARKERS','what they mean',85.17,(10,-20)),(0.40,'HOW YOU FEEL','cross-reference',88.53,(30,-10)),(0.70,'SIDE EFFECTS','your profile',89.56,(-330,-10)),(1.00,'DOSAGE','what you take',90.77,(-360,-20))]
def sc_road(d,t):
    fr=clamp((t-82.6)/(90.9-82.6))
    # dashed road
    n=80
    for k in range(n):
        a0=k/n; a1=(k+0.55)/n
        if a0>fr: break
        p0=route_pt(a0); p1=route_pt(min(a1,fr)); d.line([p0,p1],fill=A(VGOLD,1),width=8)
        if GL: GL.line([p0,p1],fill=A(VGOLD,0.7),width=14)
    if t>=87.33:   # cross-reference lines from biomarkers to every landed stop
        b0=route_pt(0)
        for (sfr,_,_,tt,_) in STOPS[1:]:
            if t>=max(tt,87.33):
                q=expo((t-max(tt,87.33))/0.3); e=route_pt(sfr); e=(lerp(b0[0],e[0],q),lerp(b0[1]-50,e[1]-50,q))
                d.line([(b0[0],b0[1]-50),e],fill=A(CYAN,0.8),width=3)
                if GL: GL.line([(b0[0],b0[1]-50),e],fill=A(CYAN,0.8),width=8)
    for i,(sfr,lab,sub,tt,(ox,oy)) in enumerate(STOPS):
        if t<tt: continue
        p=appear(t,tt,0.14); x,y=route_pt(sfr); yy=y-lerp(30,0,p)
        pin(d,x,yy,i+1,VGOLD if i==0 else CYAN,p)
        lx=x+40+ox; ly=y-70+oy
        fl=f('bar',48); bw=max(d.textlength(lab,font=fl),d.textlength(sub.upper(),font=f('mono',22)))+20
        d.rectangle([lx-10,ly-2,lx+bw,ly+80],fill=A(PANEL,0.88*p))
        txt(d,lx,ly,lab,fl,WHITE,p); txt(d,lx,ly+50,sub.upper(),f('mono',22),MUTED,p)
# ---- K. CTA ----
LOGO=None
def cta(im,t):
    if t<93.85: return
    global LOGO
    a=appear(t,93.9,0.25); y=1010; yy=y+lerp(40,0,a)
    frosted(im,(56,yy,1024,yy+290),0.84,16); d=ImageDraw.Draw(im,'RGBA')
    d.rectangle([56,yy,1024,yy+290],outline=A(VGOLD,0.5*a),width=2); brackets(d,56,yy,1024,yy+290,A(VGOLD,a),30,5)
    if GL: brackets(GL,56,yy,1024,yy+290,A(VGOLD,a),30,10)
    if LOGO is None:
        lg=Image.open(S+'logo.jpg').convert('RGB'); s=min(lg.size); lg=lg.crop(((lg.width-s)//2,(lg.height-s)//2,(lg.width+s)//2,(lg.height+s)//2)).resize((170,170),Image.LANCZOS)
        m=Image.new('L',(170,170),0); ImageDraw.Draw(m).ellipse([0,0,169,169],fill=255); lg.putalpha(m); LOGO=lg
    im.alpha_composite(fade_layer(LOGO.copy(),a),(84,int(yy+30))); d=ImageDraw.Draw(im,'RGBA')
    txt(d,280,yy+26,'FREE  ·  FULL BLOODWORK BIBLE',f('mono7',28),VGOLD,a)
    if t>=95.6: txt(d,280,yy+66,'The markers I run for every enhanced athlete',f('dm',28),CREAM,appear(t,95.6))
    if t>=98.66:
        b=expo((t-98.66)/0.12); s=lerp(1.12,1.0,b)
        fn=f('beb',int(88*s)); label='COMMENT  "PANEL"'; tw=d.textlength(label,font=fn)
        lit_bar(d,280,yy+118,280+tw+40,yy+118+int(104*s),VGOLD,b); d.text((300,yy+124),label,font=fn,fill=A(INK,b))
        if GL: GL.rectangle([276,yy+114,284+tw+40,yy+122+int(104*s)],outline=A(VGOLD,b),width=12)
    txt(d,84,yy+250,'FOR RESEARCH & EDUCATIONAL PURPOSES ONLY',f('mono',18),MUTED,a*0.9)
# ======================= containers =======================
P=(64,470,1016,1260)
def full_panel(t):     # (content, header_l, header_r) for full-frame panels with background push
    if 17.9<=t<22.62: return sc_panels,'COACH AGZ FILES','EVIDENCE'
    if 22.62<=t<29.45: return sc_axis,'HPTA AXIS','SUPPRESSION'
    if 40.5<=t<50.5: return sc_apob,'ApoB  ·  mg/dL','TREND'
    if 62.55<=t<67.6: return sc_doc,'WHAT GUYS ORDER','LAB ORDER'
    if 67.6<=t<71.98: return sc_receptor,'PROLACTIN','BINDING'
    if 82.3<=t<93.0: return sc_road,'BLOODWORK','ROADMAP'
    return None
PANEL_RUNS=[(17.9,29.45),(40.5,50.5),(62.55,71.98),(82.3,93.0)]
CARDS=[  # t_in, t_out, box, content, header_l, header_r, accent
 (1.75,5.0,(64,1010,1016,1250),sc_cycle,'TREN CYCLE','PROTOCOL',VGOLD),
 (11.95,17.75,(64,1000,1016,1262),sc_research,'TRENBOLONE','EVIDENCE BASE',RED),
 (31.0,39.75,(64,880,1016,1262),sc_hdl,'HDL  ·  mg/dL','LIPIDS',GREEN),
 (50.65,61.9,(64,820,1016,1262),sc_hct,'HEMATOCRIT','RBC',RED),
 (72.05,80.9,(64,840,1016,1262),sc_libido,'LIBIDO ON TREN','WEEKS 1-12',GREEN),
]
def run_of(t):
    for r in PANEL_RUNS:
        if r[0]<=t<r[1]+0.2: return r
    return None
def draw_header(d,x0,y0,x1,hl,hr,al,acc=VGOLD):
    d.ellipse([x0+26,y0+26,x0+42,y0+42],fill=A(RED,al if int(t_global*4)%2==0 else al/3))
    txt(d,x0+56,y0+18,hl,f('mono7',28),WHITE,al); fr=f('mono7',28); tw=d.textlength(hr,font=fr); txt(d,x1-30-tw,y0+18,hr,fr,acc,al)
t_global=0
def draw_full_panel(im,t):
    r=run_of(t)
    if not r: return 0
    pin=expo((t-r[0])/0.22); pout=clamp((t-r[1])/0.18)
    if pout>=1: return 0
    s=lerp(1.05,1.0,pin)*lerp(1.0,1.03,pout); w=(P[2]-P[0])*s; h=(P[3]-P[1])*s; cx=(P[0]+P[2])/2; cy=(P[1]+P[3])/2
    x0,y0,x1,y1=cx-w/2,cy-h/2,cx+w/2,cy+h/2
    frosted(im,(x0,y0,x1,y1),0.92,8)
    fp=full_panel(min(t,r[1]-0.001))
    lay=Image.new('RGBA',(W,H),(0,0,0,0)); d=ImageDraw.Draw(lay,'RGBA')
    fn,hl,hr=fp
    if fn in (sc_panels,sc_doc): fn(d,t,lay)
    else: fn(d,t)
    # content handoff inside a run: quick blur-in of new content
    starts=[17.9,22.62,40.5,62.55,67.6,82.3]
    for st in starts:
        if st>r[0]+0.01 and st<=t<st+0.2: lay=lay.filter(ImageFilter.GaussianBlur(10*(1-expo((t-st)/0.2))))
    if pin<1: lay=lay.filter(ImageFilter.GaussianBlur(8*(1-pin)))
    al=pin*(1-pout); im.alpha_composite(fade_layer(lay,al)); d=ImageDraw.Draw(im,'RGBA')
    d.rectangle([x0,y0,x1,y1],outline=A(VGOLD,0.8*al),width=3); brackets(d,x0,y0,x1,y1,A(VGOLD,al),48,7)
    GL.rectangle([x0,y0,x1,y1],outline=A(VGOLD,0.5*al),width=6); brackets(GL,x0,y0,x1,y1,A(VGOLD,al),48,14)
    draw_header(d,x0,y0,x1,hl,hr,al)
    return pin*(1-pout)
def draw_cards(im,t):
    for (t0,t1,box,fn,hl,hr,acc) in CARDS:
        if not (t0<=t<t1+0.2): continue
        pin=expo((t-t0)/0.24); pout=clamp((t-t1)/0.18)
        if pout>=1: continue
        dy=lerp(46,0,pin)+lerp(0,-20,pout); x0,y0,x1,y1=box[0],box[1]+dy,box[2],box[3]+dy
        frosted(im,(x0,y0,x1,y1),0.88,12)
        lay=Image.new('RGBA',(W,H),(0,0,0,0)); d=ImageDraw.Draw(lay,'RGBA')
        fn(d,t,(x0,y0,x1,y1))
        if pin<1: lay=lay.filter(ImageFilter.GaussianBlur(6*(1-pin)))
        al=pin*(1-pout); im.alpha_composite(fade_layer(lay,al)); d=ImageDraw.Draw(im,'RGBA')
        d.rounded_rectangle([x0,y0,x1,y1],radius=18,outline=A(acc,0.55*al),width=2)
        d.rectangle([x0,y0+14,x0+7,y1-14],fill=A(acc,al))   # accent edge bar leads the card
        GL.rectangle([x0,y0+14,x0+7,y1-14],fill=A(acc,al*0.8))
        draw_header(d,x0,y0,x1,hl,hr,al,acc)
# ======================= hook text + band =======================
HOOK_END=5.5
def hook_text(im,t):
    if t>=HOOK_END+0.15: return
    a=1-clamp((t-HOOK_END)/0.15); d=ImageDraw.Draw(im,'RGBA')
    f1=f('bar',122); f2=f('bar6',84)
    parts=[('500+ ',WHITE),('TREN',VGOLD),(' panels',WHITE)]; l2='same red flags every time'
    w1=sum(d.textlength(s,font=f1) for s,_ in parts); w2=d.textlength(l2,font=f2)
    bw=max(w1,w2)+80; bx0=(W-bw)/2; by0=268; bh=268
    lay=Image.new('RGBA',(W,H),(0,0,0,0)); ld=ImageDraw.Draw(lay,'RGBA')
    ld.rounded_rectangle([bx0,by0,bx0+bw,by0+bh],radius=26,fill=(2,3,8,224))
    x=(W-w1)/2
    for s,c in parts: ld.text((x,by0+14),s,font=f1,fill=c+(255,)); x+=ld.textlength(s,font=f1)
    ld.text(((W-w2)/2,by0+150),l2,font=f2,fill=WHITE+(255,))
    im.alpha_composite(fade_layer(lay,a))
    GL.text(((W-w1)/2+d.textlength('500+ ',font=f1),by0+14),'TREN',font=f1,fill=A(VGOLD,0.6*a))
BAND_END=51.2
def topic_band(d,t):
    if not (HOOK_END+0.15<=t<BAND_END+0.15): return
    a=min(clamp((t-HOOK_END-0.15)/0.15),1-clamp((t-BAND_END)/0.15))
    d.rectangle([8,212,W,372],fill=NAVY+(int(228*a),)); d.line([(64,244),(108,244)],fill=A(GOLD,a),width=4); txt(d,122,228,'@coach.agz',f('mono',28),GOLD,a)
    fn=f('bar',72); parts=[('Bloodwork after 12 weeks on ',CREAM),('TREN',VGOLD)]; x=64
    for s,c in parts: txt(d,x,268,s,fn,c,a); x+=d.textlength(s,font=fn)
# ======================= captions =======================
def build_groups():
    G=[];cur=[]
    for i,x in enumerate(WORDS):
        if cur:
            prev=WORDS[cur[-1]]
            if len(cur)>=3 or x['s']-prev['e']>0.28 or prev['w'][-1] in '.,?!' or any(prev['e']<c<=x['s']+0.01 for c in CUTS): G.append(cur); cur=[]
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
    ws=[WORDS[i]['w'].upper().rstrip(',.?!') for i in g]
    size=128
    while True:
        fn=f('beb',size); sp=d.textlength(' ',font=fn)+14; wd=[d.textlength(w,font=fn) for w in ws]; tot=sum(wd)+sp*(len(ws)-1)
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
    for k,(w_,x_) in enumerate(zip(ws,xs)): cd.text((x_,40),w_,font=fn,fill=CREAM,stroke_width=0 if k==act else 3,stroke_fill=(0,0,0))
    if abs(s-1)>0.002:
        cap=cap.resize((int(W*s),int(300*s)),Image.BICUBIC); ox=int((W-cap.width)/2); oy=int(CAP_Y-40-(cap.height-300)/2)
    else: ox,oy=0,CAP_Y-40
    im.alpha_composite(cap,(ox,oy))
# ======================= frame =======================
def zoom_at(t):
    k=sum(1 for c in CUTS if c<=t+1e-6)
    if k==0: return 1.0 if t<0.88 else 1.08     # first punch lands on "Tren"
    return 1.0 if k%2==1 else 1.08
VERDICTS=[(91.9,92.0,'4 INPUTS','ONE ROADMAP')]
def frame(src,t):
    global GL,t_global
    t_global=t
    z=zoom_at(t)
    if z!=1.0:
        big=src.resize((int(W*z),int(H*z)),Image.BICUBIC); ox=(big.width-W)//2; oy=int((big.height-H)*0.35); src=big.crop((ox,oy,ox+W,oy+H))
    r=run_of(t); g=0
    if r: g=min(ease_io((t-r[0]+0.05)/0.30),1-ease_io((t-r[1])/0.22))
    bg=src
    if g>0: bg=Image.blend(src.filter(ImageFilter.GaussianBlur(18*g)),Image.new('RGB',(W,H),(5,8,16)),0.68*g)
    im=bg.convert('RGBA')
    yy=np.arange(H); a=np.where(yy>1180,np.clip((yy-1180)/260,0,1)*110,0); a=np.maximum(a,np.where(yy<420,(1-yy/420)*120,0)); scr=(a*(1-g)).astype(np.uint8)
    im.alpha_composite(Image.merge('RGBA',[Image.new('L',(W,H),c) for c in NAVY]+[Image.fromarray(np.repeat(scr[:,None],W,1))]))
    glow=Image.new('RGBA',(W,H),(0,0,0,0)); GL=ImageDraw.Draw(glow,'RGBA')
    mirror_hud(im,t)
    draw_cards(im,t)
    draw_full_panel(im,t)
    for (t0,t1,a1,a2) in VERDICTS:
        if t>=t0 and r is not None and r[0]<=t0<r[1]:
            p=expo((t-t0)/(t1-t0)); d=ImageDraw.Draw(im,'RGBA'); y=1162; x0=P[0]; x1=lerp(x0,P[2],p)
            al=1-clamp((t-r[1])/0.16)
            if al>0:
                GL.rectangle([x0-4,y-8,x1+4,y+100],outline=A(RED,al),width=10)
                lit_bar(d,x0,y,x1,y+92,RED,al); d.rectangle([x0,y+88,x1,y+92],fill=A((140,0,0),al))
                if p>0.6: fn=f('beb',74); d.text((x0+30,y+8),a1,font=fn,fill=A(WHITE,al)); tw=d.textlength(a1,font=fn); d.text((x0+30+tw+24,y+30),'= '+a2,font=f('mono7',30),fill=A(WHITE,al))
    cta(im,t)
    hook_text(im,t)
    GL=None
    if glow.getbbox():
        sm=glow.resize((W//4,H//4),Image.BILINEAR)
        g1=np.asarray(sm.filter(ImageFilter.GaussianBlur(3.5))).astype(np.float32)/255; g2=np.asarray(sm.filter(ImageFilter.GaussianBlur(10))).astype(np.float32)/255
        prem=np.clip(g1[...,:3]*g1[...,3:]*2.3+g2[...,:3]*g2[...,3:]*1.8,0,1)
        prem=np.asarray(Image.fromarray((prem*255).astype(np.uint8)).resize((W,H),Image.BILINEAR)).astype(np.float32)/255
        b=np.asarray(im.convert('RGB')).astype(np.float32)/255
        im=Image.fromarray(((1-(1-b)*(1-prem))*255).astype(np.uint8)).convert('RGBA')
    d=ImageDraw.Draw(im,'RGBA'); d.rectangle([0,0,7,H],fill=GOLD)
    topic_band(d,t)
    captions(im,t)
    out=im.convert('RGB')
    for (t0,t1,_,_) in VERDICTS:
        k=round((t-t1)*FPS)
        if k in (0,1):
            dx=[9,-5][k]; zz=1.025; big=out.resize((int(W*zz),int(H*zz)),Image.BICUBIC); ox=(big.width-W)//2-dx; oy=(big.height-H)//2
            out=big.crop((ox,oy,ox+W,oy+H)); ImageDraw.Draw(out).rectangle([0,0,7,H],fill=GOLD)
    return out
if __name__=='__main__':
    mode=sys.argv[2]
    if mode=='stills':
        import os; os.makedirs(S+'qc',exist_ok=True)
        for tt in [float(x) for x in sys.argv[3:]]:
            subprocess.run(['ffmpeg','-v','error','-y','-ss',f'{tt:.4f}','-i',S+'assembled.mov','-frames:v','1',S+'qc/_src.png'])
            frame(Image.open(S+'qc/_src.png').convert('RGB'),tt).resize((540,960),Image.LANCZOS).save(S+f'qc/st_{tt:06.2f}.jpg',quality=88)
        sys.exit()
    n0,n1=int(sys.argv[3]),int(sys.argv[4]); out=sys.argv[5]
    dec=subprocess.Popen(['ffmpeg','-v','error','-ss',f'{n0/FPS:.4f}','-i',S+'assembled.mov','-frames:v',str(n1-n0),'-f','rawvideo','-pix_fmt','rgb24','-'],stdout=subprocess.PIPE)
    enc=subprocess.Popen(['ffmpeg','-v','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-','-c:v','libx264','-crf','14','-preset','medium','-pix_fmt','yuv420p',out],stdin=subprocess.PIPE)
    for n in range(n0,n1):
        buf=dec.stdout.read(W*H*3)
        if len(buf)<W*H*3: print('short',n); break
        enc.stdin.write(frame(Image.frombuffer('RGB',(W,H),buf),n/FPS).tobytes())
    enc.stdin.close(); enc.wait(); dec.kill(); print('done',n0,n1)
