import json, subprocess, sys, math
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
S=sys.argv[1]; F=S+'/fonts/'; T=S+'/full1/'
W,H=1080,1920; FPS=30
TL=json.load(open(T+'timeline.json')); DUR=TL['dur']; N=int(DUR*FPS); BOUNDS=TL['bounds']
WORDS=json.load(open(T+'words_final.json'))
GOLD=(201,169,110); CREAM=(244,241,234); NAVY=(14,17,23)
RED=(255,34,28); VGOLD=(255,194,26); CYAN=(0,229,255); GREEN=(30,255,110); DEEP=(2,3,8); INK=(6,8,14); WHITE=(255,255,255)
MONO='JBMono-500.ttf'; BEB='BebasNeue.ttf'; DMB='DMSans-700.ttf'; DMR='DMSans-400.ttf'
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
GL=None
# ---------------- primitives ----------------
def brackets(d,x0,y0,x1,y1,col,L=34,w=4):
    for (cx,cy,sx,sy) in [(x0,y0,1,1),(x1,y0,-1,1),(x0,y1,1,-1),(x1,y1,-1,-1)]:
        d.line([(cx,cy),(cx+sx*L,cy)],fill=col,width=w); d.line([(cx,cy),(cx,cy+sy*L)],fill=col,width=w)
def lit_bar(d,x0,y0,x1,y1,col,a=1.0):
    h=max(1,int(y1-y0))
    for i in range(h):
        k=i/h; c=tuple(int(min(255,v*(1.18-0.36*k)+(40 if k<0.12 else 0))) for v in col)
        d.line([(x0,y0+i),(x1,y0+i)],fill=c+(int(255*a),))
def tag(d,x,y,label,col=RED,size=32,a=1.0,glow=True):
    fn=f(MONO,size); tw=d.textlength(label,font=fn); h=size+16
    lit_bar(d,x,y,x+tw+24,y+h,col,a); d.text((x+12,y+5),label,font=fn,fill=A(WHITE if col!=VGOLD else INK,a))
    if GL and glow: GL.rectangle([x-4,y-4,x+tw+28,y+h+4],outline=A(col,a),width=8)
    return x+tw+24
def flag(d,box,label,t0,t,side='right'):
    p=expo((t-t0)/0.14)
    if p<=0: return
    x0,y0,x1,y1=box; brackets(d,x0,y0,x1,y1,A(RED,1),30,7)
    if GL: brackets(GL,x0,y0,x1,y1,A(RED,1),30,12)
    q=clamp((p-0.3)/0.7)
    if q>0:
        for seg in [((x0,y0),(lerp(x0,x1,q),y0)),((x1,y1),(lerp(x1,x0,q),y1)),((x0,y1),(x0,lerp(y1,y0,q))),((x1,y0),(x1,lerp(y0,y1,q)))]:
            d.line(seg,fill=A(RED,1),width=4)
    if p>0.5 and label:
        fn=f(MONO,30); tw=d.textlength(label,font=fn)
        if side=='right': tag(d,x1+12,(y0+y1)/2-23,label,size=30)
        elif side=='above': tag(d,x0,y0-58,label,size=30)
        else: tag(d,x0,y1+10,label,size=30)
def node(d,x0,y0,x1,y1,title,sub,col,a=1.0,dim=False):
    c=col if not dim else tuple(int(v*0.35) for v in col)
    d.rounded_rectangle([x0,y0,x1,y1],radius=14,fill=A((10,14,24),0.95*a),outline=A(c,a),width=4)
    if GL and not dim: GL.rounded_rectangle([x0,y0,x1,y1],radius=14,outline=A(col,a*0.8),width=8)
    fn=f(BEB,46); tw=d.textlength(title,font=fn); d.text(((x0+x1)/2-tw/2,y0+14),title,font=fn,fill=A(WHITE if not dim else (110,110,120),a))
    if sub:
        fs=f(MONO,24); sw=d.textlength(sub,font=fs); d.text(((x0+x1)/2-sw/2,y1-40),sub,font=fs,fill=A(c,a))
def hexagon(d,cx,cy,r,col,a=1.0,label='AROMATASE',dim=False):
    c=col if not dim else tuple(int(v*0.35) for v in col)
    pts=[(cx+r*math.cos(math.pi/3*i+math.pi/6),cy+r*math.sin(math.pi/3*i+math.pi/6)) for i in range(6)]
    d.polygon(pts,fill=A((10,14,24),0.95*a),outline=A(c,a)); d.line(pts+[pts[0]],fill=A(c,a),width=5)
    if GL: GL.line(pts+[pts[0]],fill=A(c,a*0.9),width=10)
    fn=f(BEB,34); tw=d.textlength(label,font=fn); d.text((cx-tw/2,cy-20),label,font=fn,fill=A(WHITE,a))
def arrow(d,x0,y0,x1,y1,col,w=5,a=1.0):
    d.line([(x0,y0),(x1,y1)],fill=A(col,a),width=w)
    ang=math.atan2(y1-y0,x1-x0); L=18
    d.polygon([(x1,y1),(x1-L*math.cos(ang-0.45),y1-L*math.sin(ang-0.45)),(x1-L*math.cos(ang+0.45),y1-L*math.sin(ang+0.45))],fill=A(col,a))
def flow(d,x0,y0,x1,y1,t,col,n=5,speed=0.9,a=1.0,r=7):
    for k in range(n):
        p=(t*speed+k/n)%1
        x=lerp(x0,x1,p); y=lerp(y0,y1,p); fa=a*min(1,p*6,(1-p)*6)
        d.ellipse([x-r,y-r,x+r,y+r],fill=A(col,fa))
        if GL: GL.ellipse([x-r*2,y-r*2,x+r*2,y+r*2],fill=A(col,fa))
def meter(d,x0,y0,x1,y1,frac,col,label,value=None,a=1.0):
    d.text((x0,y0-40),label,font=f(MONO,28),fill=A(CREAM,a))
    d.rectangle([x0,y0,x1,y1],outline=A((70,74,90),a),width=2)
    xf=lerp(x0+3,x1-3,clamp(frac)); lit_bar(d,x0+3,y0+3,xf,y1-3,col,a)
    if GL: GL.rectangle([x0+3,y0+3,xf,y1-3],fill=A(col,a*0.7))
    if value:
        fn=f(BEB,40); tw=d.textlength(value,font=fn); d.text((x1-tw,y0-48),value,font=fn,fill=A(col,a))
def check(d,x,y,col,s=1.0,a=1.0):
    d.line([(x,y+16*s),(x+10*s,y+28*s),(x+30*s,y+2*s)],fill=A(col,a),width=int(6*s))
    if GL: GL.line([(x,y+16*s),(x+10*s,y+28*s),(x+30*s,y+2*s)],fill=A(col,a),width=int(12*s))
def cross(d,x,y,col,s=1.0,a=1.0):
    d.line([(x,y),(x+28*s,y+28*s)],fill=A(col,a),width=int(6*s)); d.line([(x+28*s,y),(x,y+28*s)],fill=A(col,a),width=int(6*s))
    if GL: GL.line([(x,y),(x+28*s,y+28*s)],fill=A(col,a),width=12); GL.line([(x+28*s,y),(x,y+28*s)],fill=A(col,a),width=12)
def appear(t,t0,dur=0.16): return expo((t-t0)/dur)
def txt(d,x,y,s,font,col,a=1.0,anchor=None):
    d.text((x,y),s,font=font,fill=A(col,a),anchor=anchor)

# ---------------- scenes (panel content), coords absolute ----------------
P=(64,470,1016,1260)
def scene_ai(d,t):        # MECHANISM 01
    ai_on = 10.52<=t<15.52; ai_p=appear(t,10.40,0.12) if t<15.52 else 1-clamp((t-15.52)/0.12)
    blocked = ai_on
    node(d,100,700,340,840,'TESTOSTERONE','T',CYAN)
    hexagon(d,540,770,100,VGOLD)
    node(d,740,700,980,840,'ESTRADIOL','E2',CYAN,dim=(blocked and t>10.7))
    arrow(d,345,770,436,770,CYAN); arrow(d,644,770,734,770,CYAN if not (blocked and t>10.7) else (40,60,70))
    flow(d,345,770,436,770,t,CYAN,4)
    if not (blocked and t>10.62): flow(d,644,770,734,770,t,CYAN,4)
    txt(d,100,590,'TESTOSTERONE CONVERTS TO ESTRADIOL',f(MONO,30),CREAM,appear(t,9.2))
    if ai_p>0:
        y=lerp(560,640,expo((t-10.40)/0.12)); 
        d.rounded_rectangle([480,y,600,y+70],radius=10,fill=A(RED,ai_p)); txt(d,510,y+8,'AI',f(BEB,56),WHITE,ai_p)
        if GL: GL.rounded_rectangle([476,y-4,604,y+74],radius=12,outline=A(RED,ai_p),width=10)
        if ai_on: flag(d,(430,660,650,880),'ENZYME BLOCKED',10.56,t,'below')
    e2 = 1.0 if t<10.7 else (lerp(1.0,0.18,expo((t-10.7)/0.4)) if t<15.6 else lerp(0.18,1.0,expo((t-15.6)/0.5)))
    if t>=12.2: meter(d,100,1040,980,1090,e2,RED if e2<0.5 else CYAN,'E2 OUTPUT',None,appear(t,12.2))
    if t>=15.6:
        a=appear(t,15.66); x=100
        for i,(nm,tt) in enumerate([('MASTERON',15.66),('PRIMO',16.42),('EQUIPOISE',16.84)]):
            aa=appear(t,tt); x=tag(d,x,1140,nm,VGOLD,32,aa,glow=True)+16
        if t>=17.64: tag(d,100,1196-6,'ENZYME UNTOUCHED',GREEN,30,appear(t,17.64)) if False else None
        if t>=17.64:
            aa=appear(t,17.64); check(d,660,1150,GREEN,1.0,aa); txt(d,706,1144,'ENZYME UNTOUCHED',f(MONO,30),GREEN,aa)
def receptor_row(d,x0,y0,title,sub,n_fill,col_fill,col,frac,a=1.0):
    txt(d,x0,y0,title,f(BEB,46),WHITE,a); txt(d,x0,y0+48,sub,f(MONO,24),col,a)
    for i in range(6):
        sx=x0+i*66; sy=y0+100
        d.arc([sx,sy,sx+52,sy+52],0,180,fill=A(col,a),width=5); d.line([(sx,sy+26),(sx,sy-4)],fill=A(col,a),width=5); d.line([(sx+52,sy+26),(sx+52,sy-4)],fill=A(col,a),width=5)
        if i<n_fill:
            fc=col_fill[i] if isinstance(col_fill,list) else col_fill
            d.ellipse([sx+8,sy+4,sx+44,sy+40],fill=A(fc,a))
            if GL: GL.ellipse([sx,sy-4,sx+52,sy+48],fill=A(fc,a*0.8))
    meter(d,x0,y0+214,x0+390,y0+246,frac,col,'OCCUPANCY',f'{int(frac*100)}%',a)
def scene_mp(d,t):        # MECHANISM 02
    on = 0.5+0.5*math.sin(t*8)
    node(d,100,560,300,650,'T','',CYAN); hexagon(d,450,605,62,VGOLD,label='AROM.'); node(d,600,560,800,650,'E2','',CYAN)
    arrow(d,305,605,386,605,CYAN); arrow(d,514,605,594,605,CYAN); flow(d,305,605,386,605,t,CYAN,3); flow(d,514,605,594,605,t,CYAN,3)
    d.ellipse([830,588,858,616],fill=A(GREEN,0.6+0.4*on)); 
    if GL: GL.ellipse([820,578,868,626],fill=A(GREEN,0.8))
    txt(d,870,584,'ON',f(MONO,32),GREEN)
    clr=1-clamp((t-41.5)/0.25)
    if t>=22.18 and clr>0:
        a=appear(t,22.18)*clr; x=tag(d,100,690,'MASTERON',VGOLD,30,a); x=tag(d,x+12,690,'PRIMO',VGOLD,30,a); txt(d,x+20,694,'= DHT-DERIVED',f(MONO,30),CREAM,a)
    if t>=23.54 and clr>0: a=appear(t,23.54)*clr; cross(d,100,758,RED,0.8,a); txt(d,136,752,"NO AROMATIZATION",f(MONO,28),RED,a)
    if t>=24.72 and clr>0: a=appear(t,24.72)*clr; cross(d,520,758,RED,0.8,a); txt(d,556,752,"NO ENZYME BLOCK",f(MONO,28),RED,a)
    if t>=26.66:
        a=appear(t,26.66,0.25); d.line([(100,822),(980,822)],fill=A((60,64,80),a),width=2); txt(d,100,836,'TISSUE LEVEL · TWO RECEPTORS',f(MONO,28),VGOLD,a)
        # occupancy over time
        ar = 0.30 if t<32.28 else lerp(0.30,0.84,expo((t-32.28)/0.9))
        er = 0.66 if t<34.62 else lerp(0.66,0.17,expo((t-34.62)/0.8))
        arA=appear(t,29.36) if t<29.36 else 1; erA=appear(t,30.60) if t<30.60 else 1
        receptor_row(d,100,890,'ANDROGEN','AR',int(round(ar*6)),VGOLD,VGOLD,ar,max(0.35,arA if t>=29.36 else 0.35))
        receptor_row(d,560,890,'ESTROGEN','ER',int(round(er*6)),CYAN,CYAN,er,max(0.35,erA if t>=30.60 else 0.35))
        if t>=35.0: flag(d,(552,880,976,1180),'UNDER-OCCUPIED',35.0,t,'above') if False else None
        if t>=35.0: tag(d,700,850,'UNDER-OCCUPIED',RED,30,appear(t,35.0))
    if t>=37.06:
        a=appear(t,37.06); tag(d,830,656,'STILL ON',GREEN,26,a)
    if t>=41.9: flag(d,(90,876,990,1150),'BINDING CHANGED',41.9,t,'below')
    if t>=43.08: flag(d,(90,550,990,664),'PRODUCTION UNCHANGED',43.08,t,'below')
def scene_eq(d,t):        # MECHANISM 03
    shift = 0 if t<48.48 else expo((t-48.48)/0.6)
    node(d,100,660,320,780,'T','',CYAN); hexagon(d,470,720,80,VGOLD,label='AROMATASE')
    node(d,700,560,960,670,'E1','ESTRONE',CYAN); node(d,700,770,960,880,'E2','ESTRADIOL',VGOLD,dim=shift>0.5)
    arrow(d,325,720,388,720,CYAN); flow(d,325,720,388,720,t,CYAN,3)
    w1=int(lerp(4,12,shift)); w2=int(lerp(10,3,shift))
    arrow(d,540,690,694,615,CYAN,w1); arrow(d,540,750,694,825,VGOLD,w2)
    flow(d,540,690,694,615,t,CYAN,int(lerp(2,6,shift))); flow(d,540,750,694,825,t,VGOLD,int(lerp(5,1,shift)),r=6)
    txt(d,100,580,'EQUIPOISE: AI?',f(MONO,30),CREAM,appear(t,48.12)); 
    cross(d,360,582,RED,0.9,appear(t,48.2))
    if t>=51.6: tag(d,700,682,'WEAKER',CYAN,26,appear(t,51.6))
    # bottom: panel reading vs total pool
    if t>=54.26:
        a=appear(t,54.26); d.line([(100,920),(980,920)],fill=A((60,64,80),a),width=2)
        txt(d,100,924,'E2 ON YOUR PANEL',f(MONO,28),CREAM,a)
        v = 1.0 if t<55.66 else lerp(1.0,0.3,expo((t-55.66)/0.4))
        d.rectangle([100,970,420,1170],outline=A((70,74,90),a),width=2)
        hgt=lerp(0,190,v); lit_bar(d,110,1165-hgt,410,1165,VGOLD,a)
        if t>=55.66:
            b=appear(t,55.7); d.polygon([(140,982),(176,982),(158,1032)],fill=A(RED,b)); txt(d,190,976,'LOW',f(BEB,64),WHITE,b)
    if t>=56.44:
        a=appear(t,56.44); txt(d,560,924,'TOTAL ESTROGEN POOL',f(MONO,28),CREAM,a)
        d.rectangle([560,970,980,1170],outline=A((70,74,90),a),width=2)
        e2h=lerp(0,190,0.3 if t>=55.66 else 1)*0.35; e1h=170-e2h
        lit_bar(d,570,1165-e2h,970,1165,VGOLD,a); lit_bar(d,570,1165-e2h-e1h,970,1165-e2h,CYAN,a)
        d.line([(560,1165-e2h-e1h-4),(980,1165-e2h-e1h-4)],fill=A(WHITE,a),width=3)
        txt(d,590,1010,'E1',f(BEB,48),INK,a)
    if t>=58.10: tag(d,700,1090,'STILL ELEVATED',RED,28,appear(t,58.10))
    if t>=59.40: flag(d,(94,984,426,1206),'MOVED',59.40,t,'below') if False else None
    if t>=60.16: tag(d,100,1186,'NUMBER MOVED',VGOLD,26,appear(t,60.16))
    if t>=61.18: tag(d,560,1186,'POOL UNCHANGED',RED,26,appear(t,61.18))
def scene_sum(d,t):       # SUMMARY + factory
    for i,(x0,hdr,big,tt,col) in enumerate([(100,'MASTERON · PRIMO','WHERE IT LANDS',65.02,VGOLD),(560,'EQUIPOISE','WHICH FORM',67.64,CYAN)]):
        a=appear(t,64.08 if i==0 else 66.78)
        if a<=0: continue
        d.rounded_rectangle([x0,560,x0+420,880],radius=14,fill=A((10,14,24),0.95*a),outline=A(col,a),width=4)
        if GL: GL.rounded_rectangle([x0,560,x0+420,880],radius=14,outline=A(col,a),width=8)
        txt(d,x0+24,580,hdr,f(MONO,28),col,a)
        if t>=tt:
            b=appear(t,tt); txt(d,x0+24,640,'CHANGES',f(BEB,50),CREAM,b); txt(d,x0+24,700,big,f(BEB,74),WHITE,b)
            txt(d,x0+24,800,'RECEPTOR BINDING' if i==0 else 'E1 vs E2',f(MONO,26),col,b)
    if t>=69.28:
        a=appear(t,69.28); hexagon(d,200,1060,95,VGOLD,a,'AROMATASE')
        txt(d,330,960,'ESTROGEN FACTORY',f(MONO,30),CREAM,a)
        on=0.5+0.5*math.sin(t*9)
        d.ellipse([330,1020,368,1058],fill=A(GREEN,(0.6+0.4*on)*a)); 
        if GL: GL.ellipse([318,1008,380,1070],fill=A(GREEN,a))
        txt(d,384,1008,'RUNNING',f(BEB,64),GREEN,a)
        for i in range(4): flow(d,300,1120+0*i,960,1120,t+i*0.2,CYAN,6,0.6,a,6) if i==0 else None
    if t>=70.76: tag(d,330,1150,'NOT TAKEN DOWN',RED,30,appear(t,70.76))
    if t>=71.42: tag(d,660,1150,'NOT TURNED OFF',RED,30,appear(t,71.42))
DOC=None
def make_lab():
    im=Image.new('RGB',(820,330),(255,255,255)); d=ImageDraw.Draw(im)
    d.rectangle([0,0,820,70],fill=(16,24,48)); d.text((24,14),'LAB REPORT · HORMONE PANEL',font=f(MONO,32),fill=WHITE)
    for i,(k,v,u,fl) in enumerate([('Estradiol, Sensitive','14','pg/mL','L'),('Testosterone, Total','1,850','ng/dL','H')]):
        y=100+i*104
        d.text((24,y),k,font=f(DMR,34),fill=(70,74,86)); d.text((24,y+42),'LC/MS-MS' if i==0 else 'Immunoassay',font=f(MONO,22),fill=(120,120,130))
        d.text((480,y+6),v,font=f(DMB,48),fill=INK); d.text((480+ImageDraw.Draw(im).textlength(v,font=f(DMB,48))+10,y+20),u,font=f(DMR,28),fill=(90,90,100))
        d.text((760,y+6),fl,font=f(DMB,48),fill=(210,10,20)); d.line([(20,y+94),(800,y+94)],fill=(220,220,225),width=2)
    return im.convert('RGBA')
def scene_lab(d,t,im):
    global DOC
    if DOC is None: DOC=make_lab()
    im.alpha_composite(DOC,(130,560))
    if t>=75.98: flag(d,(596,652,960,722),'',75.98,t,'none')
    if 75.98<=t<79.5: tag(d,610,904,'READS LOW',RED,30,appear(t,75.98))
    if t>=77.24:
        a=appear(t,77.24); fr=lerp(0.2,0.9,expo((t-77.3)/0.8))
        meter(d,130,960,560,1000,fr,RED,'ACTUAL OUTPUT','HIGH' if t>77.8 else '',a)
    if t>=79.5: tag(d,610,904,'NOT PROOF',RED,30,appear(t,79.5))
    if t>=82.98:
        p=expo((t-82.98)/0.35); x=lerp(1100,620,p)
        d.rounded_rectangle([x,1020-0,x+170,1084],radius=10,fill=A(RED,1)); txt(d,x+22,1026,'+ AI',f(BEB,58),WHITE)
        if GL: GL.rounded_rectangle([x-4,1016,x+174,1088],radius=12,outline=A(RED,1),width=10)
        if t>=84.64:
            a=appear(t,84.64); cross(d,x+180,1030,RED,1.4,a); txt(d,x+232,1030,'CONFIRM',f(MONO,26),WHITE,a); txt(d,x+232,1060,'FIRST',f(MONO,26),WHITE,a)
    items=[('DATA',85.76),('SYMPTOMS',86.48),('SIDE EFFECTS',87.48),('WATER RETENTION',88.12)]
    for i,(nm,tt) in enumerate(items):
        if t>=tt:
            a=appear(t,tt); x=130+(i%2)*430; y=1120+(i//2)*56
            check(d,x,y,GREEN,0.9,a); txt(d,x+44,y-4,nm,f(MONO,30),WHITE,a)
def scene_trend(d,t):
    txt(d,100,570,'E2 TREND · 6 PANELS',f(MONO,30),VGOLD,appear(t,90.76))
    x0,y0,x1,y1=120,640,960,960
    d.line([(x0,y1),(x1,y1)],fill=A((90,94,110),1),width=2); d.line([(x0,y0),(x0,y1)],fill=A((90,94,110),1),width=2)
    for k in range(1,4): d.line([(x0,y1-k*80),(x1,y1-k*80)],fill=A((40,44,60),1),width=1)
    vals=[0.30,0.42,0.38,0.55,0.62,0.74]
    pts=[(lerp(x0+40,x1-40,i/5),y1-20-v*280) for i,v in enumerate(vals)]
    p=clamp((t-91.0)/2.2)*5
    for i in range(5):
        if p>i:
            q=min(1,p-i); a_=pts[i]; b_=pts[i+1]; e=(lerp(a_[0],b_[0],q),lerp(a_[1],b_[1],q))
            d.line([a_,e],fill=A(CYAN,1),width=6)
            if GL: GL.line([a_,e],fill=A(CYAN,1),width=12)
    for i,pt in enumerate(pts):
        if p>=i: d.ellipse([pt[0]-10,pt[1]-10,pt[0]+10,pt[1]+10],fill=A(WHITE,1))
    if t>=93.44:
        a=appear(t,93.44); arrow(d,pts[0][0],pts[0][1]-40,pts[-1][0],pts[-1][1]-40,VGOLD,6,a); tag(d,640,610,'TREND ↑',VGOLD,28,a)
    if t>=94.46:
        a=appear(t,94.46)
        for i,nm in enumerate(['WATER','MOOD','LIBIDO','BP']):
            x=120+i*215; check(d,x,1000,GREEN,0.8,a); txt(d,x+36,996,nm,f(MONO,28),WHITE,a)
SCENES=[  # t_in, t_out, fn, header_left, header_right
 (8.95,18.55,scene_ai,'AROMATASE INHIBITOR','MECHANISM 01'),
 (20.85,43.95,scene_mp,'MASTERON · PRIMO','MECHANISM 02'),
 (48.05,62.62,scene_eq,'EQUIPOISE','MECHANISM 03'),
 (63.20,72.30,scene_sum,'IN BASIC TERMS','SUMMARY'),
 (73.70,88.55,scene_lab,'YOUR BLOODWORK','EVIDENCE'),
 (90.70,96.55,scene_trend,'THE ROADMAP','TREND'),
]
VERDICTS=[(95.16,95.26,'TREND + SYMPTOMS','THEN DECIDE')]
# ---------------- hook tag & CTA ----------------
def hook_tag(im,t):
    if not (0.7<=t<5.62): return
    pin=expo((t-0.70)/0.16); pout=clamp((t-5.45)/0.17); dx=lerp(-30,0,pin)-640*pout**2
    x0,y0,x1,y1=56+dx,980,640+dx,1290
    frosted(im,(max(8,x0),y0,x1,y1),0.82,18)
    d=ImageDraw.Draw(im,'RGBA'); a=pin*(1-pout)
    d.rectangle([x0,y0,x1,y1],outline=A(VGOLD,a*0.5),width=2); brackets(d,x0,y0,x1,y1,A(VGOLD,a),26,5)
    if GL: brackets(GL,x0,y0,x1,y1,A(VGOLD,a),26,10)
    txt(d,x0+22,y0+16,'COMPOUND · CLASS',f(MONO,28),VGOLD,a)
    for i,(nm,cl,tt) in enumerate([('MASTERON','DHT-DERIVED',0.84),('PRIMOBOLAN','DHT-DERIVED',1.24),('EQUIPOISE','TEST-DERIVED',1.62)]):
        ra=a*appear(t,tt,0.1)
        if ra<=0: continue
        y=y0+62+i*48; txt(d,x0+24,y,nm,f(MONO,30),WHITE,ra); txt(d,x0+290,y,cl,f(MONO,30),CYAN,ra)
    if t>=4.36:
        ra=a*appear(t,4.36,0.1); y=y0+214
        d.line([(x0+20,y-8),(x1-20,y-8)],fill=A((80,84,100),ra),width=2)
        txt(d,x0+24,y+6,'AROMATASE INHIBITOR?',f(MONO,28),CREAM,ra); tag(d,x0+400,y,'NONE',RED,28,ra)
def cta(im,t):
    if t<97.0: return
    d=ImageDraw.Draw(im,'RGBA'); a=appear(t,97.08,0.2)
    y=1050; frosted(im,(56,y,1024,y+230),0.82,18); d=ImageDraw.Draw(im,'RGBA')
    brackets(d,56,y,1024,y+230,A(VGOLD,a),30,5)
    if GL: brackets(GL,56,y,1024,y+230,A(VGOLD,a),30,10)
    global LOGO
    if LOGO is None:
        lg=Image.open(T+'logo.jpg').convert('RGB'); s=min(lg.size); lg=lg.crop(((lg.width-s)//2,(lg.height-s)//2,(lg.width+s)//2,(lg.height+s)//2)).resize((180,180),Image.LANCZOS)
        m=Image.new('L',(180,180),0); ImageDraw.Draw(m).ellipse([0,0,179,179],fill=255); lg.putalpha(m); LOGO=lg
    lg=LOGO.copy(); lg.putalpha(lg.split()[3].point(lambda v:int(v*a))); im.alpha_composite(lg,(80,y+25))
    d=ImageDraw.Draw(im,'RGBA')
    txt(d,290,y+28,'FREE · ESTROGEN MANAGEMENT FRAMEWORK',f(MONO,26),VGOLD,a)
    if t>=99.94:
        b=expo((t-99.94)/0.12); s=lerp(1.12,1.0,b)
        fn=f(BEB,int(84*s)); label='COMMENT  "ESTROGEN"'; tw=d.textlength(label,font=fn)
        lit_bar(d,290,y+80,290+tw+40,y+80+int(100*s),VGOLD,b); d.text((310,y+86),label,font=fn,fill=A(INK,b))
        if GL: GL.rectangle([286,y+76,294+tw+40,y+84+int(100*s)],outline=A(VGOLD,b),width=12)
LOGO=None
def frosted(im,box,dark=0.86,blur=10):
    x0,y0,x1,y1=[int(v) for v in box]
    if x1<=x0 or y1<=y0: return
    reg=im.crop((x0,y0,x1,y1)).convert('RGB').filter(ImageFilter.GaussianBlur(blur))
    im.paste(Image.blend(reg,Image.new('RGB',reg.size,DEEP),dark).convert('RGBA'),(x0,y0))
# ---------------- captions ----------------
FIX={'their':"THEY'RE"}
def build_groups():
    G=[];cur=[]
    for i,x in enumerate(WORDS):
        if cur:
            prev=WORDS[cur[-1]]
            if len(cur)>=3 or x['s']-prev['e']>0.28 or prev['w'][-1] in '.,?!' or x['s']>=nearest_bound(prev['e']): G.append(cur); cur=[]
        cur.append(i)
    if cur: G.append(cur)
    return G
def nearest_bound(t):
    for b0,b1 in BOUNDS:
        if b0>t+0.01: return b0
    return 1e9
GROUPS=None
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
    ws=[FIX.get(WORDS[i]['w'].lower().strip('.,?!'),WORDS[i]['w']).upper().rstrip(',') for i in g]
    size=128
    while True:
        fn=f(BEB,size); sp=d.textlength(' ',font=fn)+14; wd=[d.textlength(w,font=fn) for w in ws]; tot=sum(wd)+sp*(len(ws)-1)
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
# ---------------- frame ----------------
def seg_of(t):
    for i,(b0,b1) in enumerate(BOUNDS):
        if b0<=t<b1: return i
    return len(BOUNDS)-1
def active_scene(t):
    for sc in SCENES:
        if sc[0]-0.0<=t<sc[1]+0.16: return sc
    return None
def frame(src,t):
    # punch-in alternates per take on talking-head shots (hides jump cuts)
    z=1.0 if seg_of(t)%2==0 else 1.08
    if z!=1.0:
        big=src.resize((int(W*z),int(H*z)),Image.BICUBIC); ox=(big.width-W)//2; oy=int((big.height-H)*0.35); src=big.crop((ox,oy,ox+W,oy+H))
    sc=active_scene(t)
    g=0
    if sc: g=min(ease_io((t-sc[0]+0.05)/0.30), 1-ease_io((t-sc[1])/0.22))
    bg=src
    if g>0: bg=Image.blend(src.filter(ImageFilter.GaussianBlur(18*g)),Image.new('RGB',(W,H),(5,8,16)),0.68*g)
    im=bg.convert('RGBA')
    scr=np.zeros((H,1),np.uint8)
    yy=np.arange(H); a=np.where(yy>1180,np.clip((yy-1180)/260,0,1)*110,0); a=np.maximum(a,np.where(yy<420,(1-yy/420)*120,0)); scr=(a*(1-g)).astype(np.uint8)
    im.alpha_composite(Image.merge('RGBA',[Image.new('L',(W,H),c) for c in NAVY]+[Image.fromarray(np.repeat(scr[:,None],W,1))]))
    global GL
    glow=Image.new('RGBA',(W,H),(0,0,0,0)); GL=ImageDraw.Draw(glow,'RGBA')
    hook_tag(im,t)
    if sc:
        pin=expo((t-sc[0])/0.20); pout=clamp((t-sc[1])/0.16)
        if pout<1:
            s=lerp(1.05,1.0,pin)*lerp(1.0,1.03,pout); w=(P[2]-P[0])*s; h=(P[3]-P[1])*s; cx=(P[0]+P[2])/2; cy=(P[1]+P[3])/2
            x0,y0,x1,y1=cx-w/2,cy-h/2,cx+w/2,cy+h/2
            frosted(im,(x0,y0,x1,y1),0.92,8)
            lay=Image.new('RGBA',(W,H),(0,0,0,0)); d=ImageDraw.Draw(lay,'RGBA')
            GLsave=GL
            if sc[2] is scene_lab: sc[2](d,t,lay)
            else: sc[2](d,t)
            if pin<1: lay=lay.filter(ImageFilter.GaussianBlur(8*(1-pin)))
            al=pin*(1-pout); lay.putalpha(lay.split()[3].point(lambda v:int(v*al)))
            im.alpha_composite(lay); d=ImageDraw.Draw(im,'RGBA')
            d.rectangle([x0,y0,x1,y1],outline=A(VGOLD,0.8*al),width=3); brackets(d,x0,y0,x1,y1,A(VGOLD,al),48,7)
            GL.rectangle([x0,y0,x1,y1],outline=A(VGOLD,0.5*al),width=6); brackets(GL,x0,y0,x1,y1,A(VGOLD,al),48,14)
            d.ellipse([x0+26,y0+26,x0+42,y0+42],fill=A(RED,al if int(t*4)%2==0 else al/3))
            txt(d,x0+56,y0+18,sc[3],f(MONO,28),WHITE,al); fr=f(MONO,28); tw=d.textlength(sc[4],font=fr); txt(d,x1-30-tw,y0+18,sc[4],fr,VGOLD,al)
    for (t0,t1,a1,a2) in VERDICTS:
        if t>=t0 and (sc is not None):
            p=expo((t-t0)/(t1-t0)); d=ImageDraw.Draw(im,'RGBA'); y=1100; x0=P[0]; x1=lerp(x0,P[2],p)
            al=1-clamp((t-sc[1])/0.16)
            GL.rectangle([x0-4,y-8,x1+4,y+100],outline=A(RED,al),width=10)
            lit_bar(d,x0,y,x1,y+92,RED,al); d.rectangle([x0,y+88,x1,y+92],fill=A((140,0,0),al))
            if p>0.6: fn=f(BEB,74); d.text((x0+30,y+8),a1,font=fn,fill=A(WHITE,al)); tw=d.textlength(a1,font=fn); d.text((x0+30+tw+24,y+30),'= '+a2,font=f(MONO,30),fill=A(WHITE,al))
    cta(im,t)
    GL=None
    # screen-blend bloom (computed at 1/4 res for speed)
    if glow.getbbox():
        sm=glow.resize((W//4,H//4),Image.BILINEAR)
        g1=np.asarray(sm.filter(ImageFilter.GaussianBlur(3.5))).astype(np.float32)/255; g2=np.asarray(sm.filter(ImageFilter.GaussianBlur(10))).astype(np.float32)/255
        prem=np.clip(g1[...,:3]*g1[...,3:]*2.3+g2[...,:3]*g2[...,3:]*1.8,0,1)
        prem=np.asarray(Image.fromarray((prem*255).astype(np.uint8)).resize((W,H),Image.BILINEAR)).astype(np.float32)/255
        b=np.asarray(im.convert('RGB')).astype(np.float32)/255
        im=Image.fromarray(((1-(1-b)*(1-prem))*255).astype(np.uint8)).convert('RGBA')
    d=ImageDraw.Draw(im,'RGBA'); d.rectangle([0,0,7,H],fill=GOLD)
    p=expo(t/0.30); ty=lerp(-180,0,p)
    d.rectangle([8,212+ty,W,372+ty],fill=NAVY+(228,)); d.line([(64,244+ty),(108,244+ty)],fill=GOLD,width=4); d.text((122,228+ty),'@coach.agz',font=f(MONO,28),fill=GOLD)
    t1='MASTERON · PRIMO · EQ'; t2='  ARE NOT AN AI'; sz=80
    while d.textlength(t1+t2,font=f(BEB,sz))>952: sz-=2
    fn=f(BEB,sz); d.text((64,266+ty+(80-sz)*0.5),t1,font=fn,fill=CREAM); d.text((64+d.textlength(t1,font=fn),266+ty+(80-sz)*0.5),t2,font=fn,fill=GOLD)
    captions(im,t)
    out=im.convert('RGB')
    for (t0,t1,_,_) in VERDICTS:
        k=round((t-t1)*FPS)
        if k in (0,1):
            dx=[9,-5][k]; z=1.025; big=out.resize((int(W*z),int(H*z)),Image.BICUBIC); ox=(big.width-W)//2-dx; oy=(big.height-H)//2
            out=big.crop((ox,oy,ox+W,oy+H)); ImageDraw.Draw(out).rectangle([0,0,7,H],fill=GOLD)
    return out
GROUPS=build_groups()
if __name__=='__main__':
    mode=sys.argv[2]
    if mode=='stills':
        for tt in [float(x) for x in sys.argv[3:]]:
            subprocess.run(['ffmpeg','-v','error','-y','-ss',str(tt),'-i',T+'assembled.mov','-frames:v','1',T+f'qc/_src.png'])
            frame(Image.open(T+'qc/_src.png').convert('RGB'),tt).resize((360,640)).save(T+f'qc/st_{tt:.2f}.jpg',quality=85)
        sys.exit()
    n0,n1=int(sys.argv[3]),int(sys.argv[4]); out=sys.argv[5]
    dec=subprocess.Popen(['ffmpeg','-v','error','-ss',f'{n0/FPS:.4f}','-i',T+'assembled.mov','-frames:v',str(n1-n0),'-f','rawvideo','-pix_fmt','rgb24','-'],stdout=subprocess.PIPE)
    enc=subprocess.Popen(['ffmpeg','-v','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-','-vf','scale=720:1280:flags=lanczos','-c:v','libx264','-crf','18','-preset','medium','-pix_fmt','yuv420p',out],stdin=subprocess.PIPE)
    for n in range(n0,n1):
        buf=dec.stdout.read(W*H*3)
        if len(buf)<W*H*3: print('short',n); break
        enc.stdin.write(frame(Image.frombuffer('RGB',(W,H),buf),n/FPS).tobytes())
    enc.stdin.close(); enc.wait(); dec.kill(); print('done',n0,n1)
