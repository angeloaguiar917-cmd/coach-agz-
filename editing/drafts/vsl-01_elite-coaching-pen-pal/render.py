# @coach.agz VSL "Elite coaching vs a pen pal" — 1080x1920 30fps render
# usage: python3 render.py <vsl_dir> stills t1 t2 ...   (t = OUTPUT seconds)
#        python3 render.py <vsl_dir> chunk n0 n1 out.mp4
import json, subprocess, sys, math, re
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
S=sys.argv[1].rstrip('/')+'/'; F=S+'fonts/'; AS=S+'assets/'
W,H=1080,1920; FPS=30
EDIT=json.load(open(S+'edit.json'))
WORDS=json.load(open(S+'words_final.json'))      # source-time words
KEEP=EDIT['keep']; SRC_DUR=EDIT['src_dur']
OUT_DUR=sum(b-a for a,b in KEEP); NOUT=int(round(OUT_DUR*FPS))
CUTS_SRC=[a for a,b in KEEP[1:]]                   # source times where a jump happens
GOLD=(201,169,110); CREAM=(244,241,234); NAVY=(14,17,23); MUTED=(184,184,188)
RED=(255,34,28); VGOLD=(255,194,26); CYAN=(0,229,255); GREEN=(30,255,110); DEEP=(2,3,8); INK=(6,8,14); WHITE=(255,255,255)
BLUE=(79,163,224); AMBER=(240,160,48); SGREEN=(60,203,106)
MONO='JBMono-500.ttf'; MONOB='JBMono-700.ttf'; BEB='BebasNeue.ttf'; DMB='DMSans-700.ttf'; DMR='DMSans-400.ttf'; DMX='DMSans-800.ttf'; BAR='BarlowCond-700.ttf'
_fc={}
def f(n,s):
    k=(n,int(s))
    if k not in _fc: _fc[k]=ImageFont.truetype(F+n,int(s))
    return _fc[k]
def clamp(x,a=0,b=1): return max(a,min(b,x))
def expo(x): x=clamp(x); return 1 if x>=1 else 1-2**(-10*x)
def ease_io(x): x=clamp(x); return 4*x**3 if x<.5 else 1-(-2*x+2)**3/2
def cubic(x): x=clamp(x); return 1-(1-x)**3
def lerp(a,b,t): return a+(b-a)*t
def A(c,a): return tuple(c[:3])+(int(clamp(a)*255),)
def appear(t,t0,dur=0.16): return expo((t-t0)/dur)
def tl(d,s,fn): return d.textlength(s,font=fn)
GL=None
# ---------------- words / cues ----------------
_n=lambda s: re.sub(r"[^a-z0-9']","",s.lower())
WN=[_n(w['w']) for w in WORDS]
def cue(phrase,after=0.0,end=False):
    tgt=''.join(_n(x) for x in phrase.split())
    for exact in (True,False):
      for i in range(len(WN)):
        if WORDS[i]['s']<after-1e-6 or not WN[i] or not (tgt.startswith(WN[i]) or (not exact and WN[i].startswith(tgt))): continue
        acc='';j=i
        while j<len(WN) and len(acc)<len(tgt): acc+=WN[j]; j+=1
        if acc==tgt or (not exact and acc.startswith(tgt)):
            return WORDS[j-1]['e'] if end else WORDS[i]['s']
    raise KeyError(phrase)
# ---------------- primitives ----------------
def brackets(d,x0,y0,x1,y1,col,L=34,w=4):
    for (cx,cy,sx,sy) in [(x0,y0,1,1),(x1,y0,-1,1),(x0,y1,1,-1),(x1,y1,-1,-1)]:
        d.line([(cx,cy),(cx+sx*L,cy)],fill=col,width=w); d.line([(cx,cy),(cx,cy+sy*L)],fill=col,width=w)
def lit_bar(d,x0,y0,x1,y1,col,a=1.0):
    if x1<=x0: return
    h=max(1,int(y1-y0))
    for i in range(h):
        k=i/h; c=tuple(int(min(255,v*(1.18-0.36*k)+(40 if k<0.12 else 0))) for v in col)
        d.line([(x0,y0+i),(x1,y0+i)],fill=c+(int(255*a),))
def tag(d,x,y,label,col=RED,size=32,a=1.0,glow=True,font=None):
    fn=f(font or MONO,size); tw=tl(d,label,fn); h=size+16
    lit_bar(d,x,y,x+tw+24,y+h,col,a); d.text((x+12,y+5),label,font=fn,fill=A(WHITE if col not in (VGOLD,GREEN,CYAN) else INK,a))
    if GL and glow: GL.rectangle([x-4,y-4,x+tw+28,y+h+4],outline=A(col,a),width=8)
    return x+tw+24
def tagw(d,label,size=32,font=None): return tl(d,label,f(font or MONO,size))+24
def flag(d,box,label,t0,t,side='right',col=RED):
    p=expo((t-t0)/0.14)
    if p<=0: return
    x0,y0,x1,y1=box; brackets(d,x0,y0,x1,y1,A(col,1),30,7)
    if GL: brackets(GL,x0,y0,x1,y1,A(col,1),30,12)
    q=clamp((p-0.3)/0.7)
    if q>0:
        for seg in [((x0,y0),(lerp(x0,x1,q),y0)),((x1,y1),(lerp(x1,x0,q),y1)),((x0,y1),(x0,lerp(y1,y0,q))),((x1,y0),(x1,lerp(y0,y1,q)))]:
            d.line(seg,fill=A(col,1),width=4)
    if p>0.5 and label:
        if side=='right': tag(d,x1+12,(y0+y1)/2-23,label,col,size=30)
        elif side=='above': tag(d,x0,y0-58,label,col,size=30)
        else: tag(d,x0,y1+10,label,col,size=30)
def arrow(d,x0,y0,x1,y1,col,w=5,a=1.0,L=18):
    d.line([(x0,y0),(x1,y1)],fill=A(col,a),width=w)
    ang=math.atan2(y1-y0,x1-x0)
    d.polygon([(x1,y1),(x1-L*math.cos(ang-0.45),y1-L*math.sin(ang-0.45)),(x1-L*math.cos(ang+0.45),y1-L*math.sin(ang+0.45))],fill=A(col,a))
def flow(d,x0,y0,x1,y1,t,col,n=5,speed=0.9,a=1.0,r=7):
    for k in range(n):
        p=(t*speed+k/n)%1
        x=lerp(x0,x1,p); y=lerp(y0,y1,p); fa=a*min(1,p*6,(1-p)*6)
        d.ellipse([x-r,y-r,x+r,y+r],fill=A(col,fa))
        if GL: GL.ellipse([x-r*2,y-r*2,x+r*2,y+r*2],fill=A(col,fa))
def check(d,x,y,col,s=1.0,a=1.0):
    d.line([(x,y+16*s),(x+10*s,y+28*s),(x+30*s,y+2*s)],fill=A(col,a),width=int(6*s))
    if GL: GL.line([(x,y+16*s),(x+10*s,y+28*s),(x+30*s,y+2*s)],fill=A(col,a),width=int(12*s))
def cross(d,x,y,col,s=1.0,a=1.0):
    d.line([(x,y),(x+28*s,y+28*s)],fill=A(col,a),width=int(6*s)); d.line([(x+28*s,y),(x,y+28*s)],fill=A(col,a),width=int(6*s))
    if GL: GL.line([(x,y),(x+28*s,y+28*s)],fill=A(col,a),width=12); GL.line([(x+28*s,y),(x,y+28*s)],fill=A(col,a),width=12)
def txt(d,x,y,s,font,col,a=1.0,anchor=None):
    d.text((x,y),s,font=font,fill=A(col,a),anchor=anchor)
def ctext(d,cx,y,s,font,col,a=1.0):
    d.text((cx-tl(d,s,font)/2,y),s,font=font,fill=A(col,a))
def node(d,x0,y0,x1,y1,title,sub,col,a=1.0,dim=False,tsize=46):
    c=col if not dim else tuple(int(v*0.35) for v in col)
    d.rounded_rectangle([x0,y0,x1,y1],radius=14,fill=A((10,14,24),0.95*a),outline=A(c,a),width=4)
    if GL and not dim: GL.rounded_rectangle([x0,y0,x1,y1],radius=14,outline=A(col,a*0.8),width=8)
    fn=f(BEB,tsize); ctext(d,(x0+x1)/2,y0+(y1-y0)/2-tsize*0.55-(12 if sub else 0),title,fn,WHITE if not dim else (110,110,120),a)
    if sub: fs=f(MONO,22); ctext(d,(x0+x1)/2,y1-36,sub,fs,c,a)
def blur_fast(img,r):
    if r<=0.5: return img
    w,h=img.size; sm=img.resize((max(1,w//4),max(1,h//4)),Image.BILINEAR).filter(ImageFilter.GaussianBlur(r/4))
    return sm.resize((w,h),Image.BILINEAR)
def frosted(im,box,dark=0.86,blur=10,col=DEEP):
    x0,y0,x1,y1=[int(v) for v in box]; x0=max(0,x0); y0=max(0,y0); x1=min(W,x1); y1=min(H,y1)
    if x1<=x0 or y1<=y0: return
    reg=blur_fast(im.crop((x0,y0,x1,y1)).convert('RGB'),blur*3)
    im.paste(Image.blend(reg,Image.new('RGB',reg.size,col),dark).convert('RGBA'),(x0,y0))
def counter_str(v): return f'{int(round(v)):,}'
# image assets (loaded lazily)
_img={}
def IMG(name):
    if name not in _img: _img[name]=Image.open(AS+name).convert('RGBA')
    return _img[name]
_rs={}
def resized(name,w):
    k=(name,int(w))
    if k not in _rs:
        im=IMG(name); _rs[k]=im.resize((int(w),int(im.height*w/im.width)),Image.LANCZOS)
    return _rs[k]
def round_mask(w,h,r):
    m=Image.new('L',(w,h),0); ImageDraw.Draw(m).rounded_rectangle([0,0,w-1,h-1],radius=r,fill=255); return m
def paste(lay,img,x,y,a=1.0,rot=0,radius=18,shadow=True):
    img=img.copy()
    if radius:
        m=round_mask(img.width,img.height,radius); al=img.split()[3]
        img.putalpha(Image.fromarray(np.minimum(np.asarray(m),np.asarray(al))))
    if shadow:
        sh=Image.new('RGBA',(img.width+80,img.height+80),(0,0,0,0)); sd=ImageDraw.Draw(sh)
        sd.rounded_rectangle([40,52,40+img.width,52+img.height],radius=radius+6,fill=(0,0,0,170)); sh=blur_fast(sh,22)
        if rot: sh=sh.rotate(rot,resample=Image.BICUBIC,expand=True)
        if a<1: sh.putalpha(sh.split()[3].point(lambda v:int(v*a)))
        lay.alpha_composite(sh,(int(x-40-(sh.width-img.width-80)/2),int(y-40-(sh.height-img.height-80)/2)))
    if rot:
        w0,h0=img.size; img=img.rotate(rot,resample=Image.BICUBIC,expand=True); x-= (img.width-w0)/2; y-=(img.height-h0)/2
    if a<1: img.putalpha(img.split()[3].point(lambda v:int(v*a)))
    lay.alpha_composite(img,(int(x),int(y)))
def highlight(lay,x,y,w,scale,boxes,t0,t,col=VGOLD,a=1.0):
    # marker sweep (multiply) over lines of a pasted screenshot; boxes in source-pixel coords
    if isinstance(lay,ImageDraw.ImageDraw): lay=lay._image
    for k,(bx0,by0,bx1,by1) in enumerate(boxes):
        p=cubic((t-t0-k*0.22)/0.30)
        if p<=0: continue
        X0=int(x+bx0*scale-4); X1=int(x+lerp(bx0,bx1,p)*scale+4); Y0=int(y+by0*scale+2); Y1=int(y+by1*scale-2)
        if X1<=X0+2 or Y1<=Y0: continue
        reg=lay.crop((X0,Y0,X1,Y1)); arr=np.asarray(reg).astype(np.float32)
        m=np.array([255,206,40],np.float32)/255
        if arr[...,:3].mean()<110: arr[...,:3]=arr[...,:3]*0.55+m*255*0.45*a
        else: arr[...,:3]=arr[...,:3]*(1-a*(1-m))
        lay.paste(Image.fromarray(arr.astype(np.uint8),'RGBA'),(X0,Y0))
        d=ImageDraw.Draw(lay,'RGBA'); d.line([(X0,Y1),(X1,Y1)],fill=A(col,a),width=5)
        if GL: GL.line([(X0,Y1),(X1,Y1)],fill=A(col,a),width=10)

# ================= SCENES =================
# Each scene: dict(t0,t1,lay,fn,hl,hr). lay: 'panel' | 'lower' | 'phone' | 'top' | 'full' | 'free'
SC=[]
def scene(t0,t1,lay,hl='',hr=''):
    def deco(fn): SC.append(dict(t0=t0,t1=t1,lay=lay,fn=fn,hl=hl,hr=hr)); return fn
    return deco
P=(64,470,1016,1260)          # panel
LO=(64,985,1016,1290)         # lower stage

# ---- 01 invoice: "thousands upon thousands of dollars" (lower stage)
c_thou=cue('thousands'); c_dollars=cue('dollars'); c_elite=cue('elite coaching')
@scene(c_thou-0.15, cue('your coaches')-0.05,'lower','ELITE COACHING','INVOICE')
def s_invoice(lay,d,t):
    x0,y0,x1,y1=LO
    rows=[('COACHING · MONTH 01',c_thou),('COACHING · MONTH 02',c_thou+0.45),('COACHING · MONTH 03',cue('thousands',c_thou+0.1)),('BLOODWORK REVIEW',c_dollars)]
    for i,(lab,tt) in enumerate(rows):
        a=appear(t,tt,0.12)
        if a<=0: continue
        y=y0+74+i*44; dy=lerp(-14,0,expo((t-tt)/0.14))
        txt(d,x0+40,y+dy,lab,f(MONO,28),CREAM,a)
        d.rectangle([x1-330,y+dy+6,x1-190,y+dy+30],fill=A((90,94,110),a))   # redacted amount
        tag(d,x1-170,y+dy-4,'PAID',GREEN,24,a,glow=False)
    if t>=c_elite:
        a=appear(t,c_elite,0.14); y=y0+74+4*44+8
        d.line([(x0+40,y),(x1-40,y)],fill=A(VGOLD,a),width=3)
        txt(d,x0+40,y+12,'TOTAL',f(BEB,58),WHITE,a);
        s='THOUSANDS'; fn=f(BEB,58); txt(d,x1-40-tl(d,s,fn),y+12,s,fn,VGOLD,a)

# ---- 02 phone chat: "coaches taking five to six days to respond" (phone)
c_taking=cue('taking'); c_five=cue('five to six'); c_six=cue('six days'); c_resp=cue('respond')
@scene(cue('your coaches'), cue('and then you send')-0.02,'phone')
def s_noreply(lay,d,t):
    ph=PHONE_BOX; x0,y0,x1,y1=ph
    txt(d,x0+40,y0+92,'COACH',f(DMB,30),WHITE); txt(d,x0+40,y0+128,'last seen 6 days ago' if t>=c_six else 'last seen recently',f(DMR,22),(150,150,160))
    # client message bubble (right)
    bx1=x1-26; bw=300; by=y0+230
    d.rounded_rectangle([bx1-bw,by,bx1,by+118],radius=22,fill=A((32,96,72),1))
    txt(d,bx1-bw+20,by+16,"Bloods are back.",f(DMR,28),WHITE); txt(d,bx1-bw+20,by+52,"Can you look?",f(DMR,28),WHITE)
    txt(d,bx1-110,by+90,'Delivered',f(DMR,18),(170,200,190))
    # day counter
    dn=1 if t<c_five else (5 if t<c_six else 6)
    if t>=c_taking:
        a=appear(t,c_taking)
        for k in range(6):
            cx=x0+56+k*62; cy=by+200
            on=k<dn
            d.rounded_rectangle([cx,cy,cx+50,cy+60],radius=8,fill=A(RED if on else (40,40,48),a))
            ctext(d,cx+25,cy+10,str(k+1),f(BEB,40),WHITE,a)
        txt(d,x0+56,by+270,'DAYS · NO REPLY',f(MONO,26),RED,a)
        ctext(d,(x0+x1)/2,by+330,f'DAY {dn}',f(BEB,150),WHITE,a)
    if t>=c_resp:
        a=appear(t,c_resp); tag(d,x0+40,y1-140,'UNANSWERED',RED,34,a)

# ---- 03 lab report + "LOOKS GOOD" stamp (panel)
c_send=cue('and then you send'); c_blood=cue('bloodwork'); c_looks=cue('looks good'); c_goodtogo=cue("you're good to go")
c_real=cue('realistically'); c_paying=cue('what are you even paying')
@scene(c_send, cue("that's literally")-0.04,'panel','YOUR BLOODWORK','REVIEW')
def s_lab(lay,d,t):
    doc=LABDOC(); p=expo((t-c_blood+0.1)/0.3); y=lerp(1300,560,p)
    if p>0: paste(lay,doc,128,y,1,rot=-1.2,radius=8)
    if t>=c_looks-0.05:
        q=expo((t-c_looks+0.05)/0.10); s=lerp(1.6,1.0,q); a=q
        st=STAMP('LOOKS GOOD',GREEN); w=int(st.width*s); h=int(st.height*s)
        sti=st.resize((w,h),Image.BICUBIC).rotate(-9,expand=True,resample=Image.BICUBIC)
        sti.putalpha(sti.split()[3].point(lambda v:int(v*a*0.92)))
        lay.alpha_composite(sti,(int(560-sti.width/2+120),int(900-sti.height/2)))
    if t>=c_real:
        flag(d,(140,606,960,690),'',c_real,t,'none')
        flag(d,(140,700,960,784),'',c_real+0.18,t,'none')
        flag(d,(140,794,960,878),'',c_real+0.36,t,'none')
    if t>=c_paying:
        a=appear(t,c_paying); x=tag(d,128,1110,'NO CONTEXT',RED,30,a); x=tag(d,x+14,1110,'NO PLAN',RED,30,appear(t,c_paying+0.3)); tag(d,x+14,1110,'NO WHY',RED,30,appear(t,c_paying+0.6))
_lab=None
def LABDOC():
    global _lab
    if _lab is None:
        im=Image.new('RGB',(820,420),(250,250,252)); d=ImageDraw.Draw(im)
        d.rectangle([0,0,820,70],fill=(16,24,48)); d.text((24,16),'LAB REPORT · HORMONE PANEL',font=f(MONO,30),fill=WHITE)
        rows=[('Estradiol, Sensitive','31','pg/mL','8–35'),('Testosterone, Total','912','ng/dL','264–916'),('Hematocrit','49.8','%','38.5–50'),('Total Cholesterol','188','mg/dL','<200')]
        for i,(k,v,u,r) in enumerate(rows):
            y=86+i*82
            d.text((24,y+4),k,font=f(DMR,32),fill=(60,64,76)); d.text((24,y+44),'Ref '+r,font=f(MONO,20),fill=(130,130,140))
            d.text((470,y+6),v,font=f(DMB,44),fill=INK); d.text((470+d.textlength(v,font=f(DMB,44))+10,y+20),u,font=f(DMR,26),fill=(90,90,100))
            d.text((740,y+6),'✓' if False else 'OK',font=f(DMB,34),fill=(20,150,70)); d.line([(20,y+78),(800,y+78)],fill=(220,220,225),width=2)
        _lab=im.convert('RGBA')
    return _lab
_stamps={}
def STAMP(s,col):
    if s not in _stamps:
        fn=f(BEB,120); w=int(ImageDraw.Draw(Image.new('L',(1,1))).textlength(s,font=fn))+80; h=170
        im=Image.new('RGBA',(w,h),(0,0,0,0)); d=ImageDraw.Draw(im)
        d.rounded_rectangle([6,6,w-6,h-6],radius=16,outline=col+(255,),width=10); d.text((40,22),s,font=fn,fill=col+(255,))
        rng=np.random.default_rng(3); a=np.asarray(im).copy(); m=rng.random(a.shape[:2])<0.12; a[...,3][m]=(a[...,3][m]*0.35).astype(np.uint8)
        _stamps[s]=Image.fromarray(a)
    return _stamps[s]

# ---- 04 verdict: "not elite coaching ... just a pen pal" (free, centre)
c_notelite=cue('not elite coaching'); c_penpal=cue('pen pal')
@scene(cue("that's literally"), cue('you know what')-0.02,'free')
def s_penpal(lay,d,t):
    a=appear(t,cue("that's literally"),0.14); y=1020
    frosted(lay,(64,y-20,1016,y+250),0.8,10)
    txt(d,96,y,'WHAT YOU PAID FOR',f(MONO,28),VGOLD,a)
    fn=f(BEB,120); txt(d,96,y+40,'ELITE COACHING',fn,WHITE,a)
    if t>=c_notelite:
        p=expo((t-c_notelite)/0.22); x1=lerp(90,96+tl(d,'ELITE COACHING',fn)+10,p)
        d.line([(90,y+104),(x1,y+104)],fill=A(RED,1),width=12)
        if GL: GL.line([(90,y+104),(x1,y+104)],fill=A(RED,1),width=20)
    if t>=c_penpal:
        p=expo((t-c_penpal)/0.10); y2=y+170; x1=lerp(96,1000,p)
        lit_bar(d,90,y2,x1,y2+84,RED);
        if GL: GL.rectangle([86,y2-4,x1+4,y2+88],outline=A(RED,1),width=10)
        if p>0.6: txt(d,120,y2+8,'WHAT YOU GOT',f(MONO,30),WHITE); txt(d,520,y2-2,'A PEN PAL',f(BEB,86),WHITE)

# ---- 05 pipeline: break down -> simplify -> optimize (top card)
c_break=cue('break this down'); c_simp=cue('simplify'); c_opt=cue('optimize')
@scene(c_break-0.1, cue('so your blood')-0.02,'top')
def s_pipe(lay,d,t):
    labs=[('BREAK IT DOWN','01',c_break),('SIMPLIFY','02',c_simp),('OPTIMIZE','03',c_opt)]
    x=84; y=430
    for i,(s,n,tt) in enumerate(labs):
        on=t>=tt; a=appear(t,tt) if on else 0.25
        col=VGOLD if i<2 else GREEN
        w=290 if i<2 else 300
        pts=[(x,y),(x+w-30,y),(x+w,y+60),(x+w-30,y+120),(x,y+120),(x+30,y+60)] if i>0 else [(x,y),(x+w-30,y),(x+w,y+60),(x+w-30,y+120),(x,y+120)]
        d.polygon(pts,fill=A((10,14,24),0.94),outline=A(col if on else (80,80,90),1))
        d.line(pts+[pts[0]],fill=A(col if on else (80,80,90),1),width=4)
        if GL and on: GL.line(pts+[pts[0]],fill=A(col,a),width=9)
        txt(d,x+44,y+12,n,f(MONO,24),col if on else (120,120,130),1); txt(d,x+44,y+42,s,f(BEB,58 if i else 52),WHITE if on else (110,110,120),1)
        x+=w+16

# ---- 06 radial hub: what coaching must cover (panel)
c_sob=cue('so your blood')
HUB=[('BLOODWORK',c_sob+0.35),('GENETICS',cue('genetics')),('HORMONES',cue('hormones')),('TRAINING',cue('training')),('NUTRITION',cue('nutrition')),('RECOVERY',cue('recovery')),('YOUR LIFE',cue('everything that happens'))]
c_sust=cue('sustainability of coaching')
@scene(c_sob-0.1, cue("it's like")-0.04,'panel','COACHING SCOPE','FULL PICTURE')
def s_hub(lay,d,t):
    cx,cy,R=540,880,285
    a0=appear(t,c_sob)
    d.ellipse([cx-95,cy-95,cx+95,cy+95],fill=A((10,14,24),1),outline=A(VGOLD,a0),width=6)
    if GL: GL.ellipse([cx-95,cy-95,cx+95,cy+95],outline=A(VGOLD,a0),width=12)
    ctext(d,cx,cy-38,'YOU',f(BEB,80),WHITE,a0)
    for i,(s,tt) in enumerate(HUB):
        ang=-math.pi/2+i*2*math.pi/len(HUB); nx=cx+R*math.cos(ang); ny=cy+R*math.sin(ang)*0.95
        if t<tt:
            d.ellipse([nx-8,ny-8,nx+8,ny+8],fill=A((70,74,90),1)); continue
        p=expo((t-tt)/0.18)
        ex=lerp(cx+100*math.cos(ang),nx,p); ey=lerp(cy+100*math.sin(ang),ny,p)
        d.line([(cx+100*math.cos(ang),cy+100*math.sin(ang)),(ex,ey)],fill=A(CYAN,1),width=4)
        if GL: GL.line([(cx+100*math.cos(ang),cy+100*math.sin(ang)),(ex,ey)],fill=A(CYAN,0.8),width=8)
        flow(d,cx+100*math.cos(ang),cy+100*math.sin(ang),nx,ny,t+i*0.3,CYAN,3,0.7,p,5)
        fn=f(BEB,40); w=tl(d,s,fn)+36
        d.rounded_rectangle([nx-w/2,ny-30,nx+w/2,ny+30],radius=10,fill=A((8,12,22),p),outline=A(CYAN if i<6 else VGOLD,p),width=3)
        ctext(d,nx,ny-22,s,fn,WHITE,p)
    if t>=c_sust:
        p=expo((t-c_sust)/0.3); r=lerp(150,R+80,p)
        d.ellipse([cx-r,cy-r*0.95,cx+r,cy+r*0.95],outline=A(VGOLD,0.9),width=5)
        if GL: GL.ellipse([cx-r,cy-r*0.95,cx+r,cy+r*0.95],outline=A(VGOLD,0.9),width=12)
        tag(d,P[0]+30,P[3]-80,'ALL OF IT = COACHING',VGOLD,30,appear(t,c_sust+0.2))

# ---- 07 reference range vs how you feel (panel)
c_e2=cue('your estradiol'); c_within=cue('within range'); c_feel=cue('you might feel'); c_shit=cue('complete shit')
c_most=cue('and most coaches'); c_yourgood=cue("oh you're good"); c_exactly=cue("that's exactly why"); c_dive=cue('dive deep')
@scene(c_e2-0.2, cue("that's why we crossreference")-0.04,'panel','ESTRADIOL','RANGE vs REALITY')
def s_range(lay,d,t):
    x0,x1=110,970; y=600
    txt(d,x0,y-50,'LAB REFERENCE RANGE · E2',f(MONO,28),CREAM,appear(t,c_e2))
    # spectrum
    for i in range(int(x1-x0)):
        k=i/(x1-x0); col=(BLUE if k<0.25 else (SGREEN if k<0.72 else AMBER))
        d.line([(x0+i,y),(x0+i,y+40)],fill=A(col,0.9))
    for k,lab in [(0.0,'LOW'),(0.72,'HIGH')]: txt(d,x0+k*(x1-x0)+8,y+50,lab,f(MONO,22),MUTED)
    m=lerp(0.05,0.48,expo((t-c_within)/0.6)) if t>=c_within else 0.05
    mx=x0+m*(x1-x0)
    d.polygon([(mx-16,y-26),(mx+16,y-26),(mx,y-2)],fill=A(WHITE,1)); d.line([(mx,y),(mx,y+40)],fill=A(WHITE,1),width=4)
    if t>=c_within+0.5: a=appear(t,c_within+0.5); check(d,mx+24,y+80,GREEN,1,a); txt(d,mx+66,y+76,'IN RANGE ON PAPER',f(MONO,28),GREEN,a)
    # how you feel meters
    if t>=c_feel:
        a=appear(t,c_feel); txt(d,x0,y+150,'HOW YOU ACTUALLY FEEL',f(MONO,28),CREAM,a)
        for i,lab in enumerate(['ENERGY','LIBIDO','MOOD','SLEEP']):
            yy=y+210+i*72; v=lerp(0.85,0.18+0.06*i,expo((t-c_shit-i*0.08)/0.5)) if t>=c_shit else 0.85
            txt(d,x0,yy,lab,f(BEB,44),WHITE,a)
            d.rectangle([x0+200,yy+6,x1,yy+42],outline=A((70,74,90),a),width=2)
            col=GREEN if v>0.5 else RED; lit_bar(d,x0+203,yy+9,x0+203+(x1-x0-206)*v,yy+39,col,a)
            if GL: GL.rectangle([x0+203,yy+9,x0+203+(x1-x0-206)*v,yy+39],fill=A(col,a*0.5))
    if c_most<=t<c_exactly+0.3:
        a=appear(t,c_yourgood) if t>=c_yourgood else 0; out=clamp((t-c_exactly)/0.3)
        if a>0:
            bx=170; by=1110; d.rounded_rectangle([bx,by,bx+640,by+92],radius=30,fill=A((44,44,52),a*(1-out)))
            txt(d,bx+28,by+12,"you're good dude",f(DMR,30),WHITE,a*(1-out)); txt(d,bx+28,by+50,"don't worry about it",f(DMR,26),(190,190,200),a*(1-out))
            if t>=c_exactly-0.05: cross(d,bx+660,by+14,RED,2.1,appear(t,c_exactly-0.05)*(1-out))
    if t>=c_dive:
        a=appear(t,c_dive); tag(d,P[0]+40,1130,'DIVE DEEP · EVERY CLIENT',VGOLD,34,a)

# ---- 08 cross-reference web (panel)
c_xref=cue("that's why we crossreference"); c_bio=cue('biomarkers')
XR=[('SYMPTOMS',cue('symptoms')),('PERFORMANCE',cue('performance')),('LIFESTYLE',cue('lifestyle')),('HOME',cue('at home')),('FAMILY',cue('family',cue('at home'))),('KIDS',cue('kids')),('BUSINESS',cue('business decisions')),('FOCUS',cue('focus')),('COGNITION',cue('cognition'))]
@scene(c_xref-0.1, cue('brother you have a business')-0.04,'panel','CROSS-REFERENCE','BIOMARKERS × LIFE')
def s_xref(lay,d,t):
    bx0,by0,bx1,by1=100,690,400,1040
    a=appear(t,c_bio-0.2)
    d.rounded_rectangle([bx0,by0,bx1,by1],radius=16,fill=A((8,12,22),a),outline=A(VGOLD,a),width=4)
    if GL: GL.rounded_rectangle([bx0,by0,bx1,by1],radius=16,outline=A(VGOLD,a),width=9)
    txt(d,bx0+24,by0+18,'BIOMARKERS',f(BEB,52),WHITE,a)
    for i,(k,v) in enumerate([('E2','31'),('HCT','49.8'),('LDL','112'),('ALT','28'),('TT','912')]):
        txt(d,bx0+24,by0+86+i*48,k,f(MONO,28),CYAN,a); txt(d,bx1-24-tl(d,v,f(MONO,28)),by0+86+i*48,v,f(MONO,28),CREAM,a)
    for i,(s,tt) in enumerate(XR):
        y=560+i*72
        if t<tt-0.02: continue
        p=expo((t-tt)/0.16); sx,sy=bx1,lerp(by0+40,by1-40,i/8)
        ex=lerp(sx,600,p)
        d.line([(sx,sy),(ex,lerp(sy,y+28,p))],fill=A(CYAN,0.85),width=3)
        if GL: GL.line([(sx,sy),(ex,lerp(sy,y+28,p))],fill=A(CYAN,0.6),width=7)
        flow(d,sx,sy,600,y+28,t+i*0.2,CYAN,2,0.8,p,4)
        d.rounded_rectangle([600,y,960,y+56],radius=10,fill=A((8,12,22),p),outline=A(CYAN,p),width=3)
        txt(d,622,y+6,s,f(BEB,46),WHITE,p); check(d,912,y+12,GREEN,0.85,p)

# ---- 09 weekly calendar: business, work, people, vacation, family (full carousel look)
c_biz=cue('brother you have a business')
CAL=[('BUSINESS',cue('a business to run'),0,0,2,RED),('WORK',cue('work to get to'),2,0,2,AMBER),('LEAD THE TEAM',cue('people to lead'),0,1,3,BLUE),('VACATION',cue('vacations'),3,1,2,SGREEN),('RESPONSIBILITIES',cue('responsibilities'),0,2,4,(170,120,255)),('FAMILY',cue('a family to raise'),4,2,1,VGOLD)]
c_horm=cue('and hormones cannot'); c_holding=cue('holding you back')
@scene(c_biz, c_horm+1.25,'full','YOUR WEEK','LIFE LOAD')
def s_cal(lay,d,t):
    full_bg(d,t,'YOUR LIFE · THIS WEEK','BUILT AROUND','',' YOUR WEEK.')
    gx0,gy0,gx1=96,780,984; cw=(gx1-gx0)/5; ch=128
    for i,day in enumerate(['MON','TUE','WED','THU','FRI']):
        ctext(d,gx0+cw*i+cw/2,gy0-46,day,f(MONO,26),MUTED)
    for r in range(3):
        for c in range(5): d.rectangle([gx0+c*cw+3,gy0+r*ch+3,gx0+(c+1)*cw-3,gy0+(r+1)*ch-3],outline=(40,44,58,255),width=2)
    for s,tt,c,r,span,col in CAL:
        if t<tt: continue
        p=expo((t-tt)/0.16); yy=lerp(gy0+r*ch-60,gy0+r*ch,p)
        X0=gx0+c*cw+8; X1=gx0+(c+span)*cw-8
        lit_bar(d,X0,yy+8,X1,yy+ch-8,tuple(int(v*0.55) for v in col),p); d.rectangle([X0,yy+8,X0+8,yy+ch-8],fill=A(col,p))
        fn=f(BEB,46 if span>1 else 38); txt(d,X0+22,yy+ch/2-24,s,fn,WHITE,p)
    if t>=c_horm:
        a=appear(t,c_horm); yy=gy0+3*ch+22
        d.rounded_rectangle([gx0,yy,gx1,yy+100],radius=12,fill=A((40,6,10),a),outline=A(RED,a),width=4)
        txt(d,gx0+30,yy+16,'HORMONES',f(BEB,70),WHITE,a)
        if t>=c_holding: tag(d,gx0+330,yy+30,'CANNOT HOLD YOU BACK',RED,32,appear(t,c_holding))

# ---- 10 step graph: "optimizing you every step of the way" (lower stage)
c_shouldopt=cue('they should be optimizing'); c_step=cue('every step of the way')
@scene(c_horm+1.25, cue('so what does that mean')-0.03,'lower','OPTIMIZATION','TRAJECTORY')
def s_steps(lay,d,t):
    x0,y0,x1,y1=LO[0]+50,LO[1]+80,LO[2]-60,LO[3]-30
    d.line([(x0,y1),(x1,y1)],fill=A((90,94,110),1),width=2); d.line([(x0,y0),(x0,y1)],fill=A((90,94,110),1),width=2)
    n=7; pts=[]
    for i in range(n+1):
        x=lerp(x0,x1,i/n); yv=lerp(y1-10,y0+10,(i/n)**0.9); pts.append((x,yv))
    p=clamp((t-c_shouldopt)/ (c_step+0.8-c_shouldopt))*n
    path=[]
    for i in range(n):
        if p<=i: break
        q=min(1,p-i); a_=pts[i]; b_=pts[i+1]
        path+= [a_,(lerp(a_[0],b_[0],min(1,q*2)),a_[1])]
        if q>0.5: path.append((b_[0],lerp(a_[1],b_[1],(q-0.5)*2)))
    if len(path)>1:
        d.line(path,fill=A(GREEN,1),width=6,joint='curve')
        if GL: GL.line(path,fill=A(GREEN,1),width=12)
    for i in range(1,n+1):
        if p>=i: d.ellipse([pts[i][0]-9,pts[i][1]-9,pts[i][0]+9,pts[i][1]+9],fill=A(WHITE,1))
    if t>=c_step: tag(d,x1-300,y0-10,'EVERY STEP ↑',GREEN,30,appear(t,c_step))

# ---- 11 built around you + response-time bar chart (panel)
c_mean=cue('that means that'); c_around=cue('revolve around you'); c_indiv=cue('individual responses'); c_side=cue('side effects'); c_nutr2=cue('around your nutrition')
c_weekly=cue('weekly basis'); c_comm=cue('communicating'); c_everyday=cue('every single day'); c_damn=cue('make damn sure')
@scene(c_mean, c_damn-0.05,'panel','COACHING','BUILT AROUND YOU')
def s_resp(lay,d,t):
    txt(d,100,550,'AROUND YOUR',f(MONO,26),CREAM,appear(t,c_around))
    for i,(s,tt) in enumerate([('RESPONSES',c_indiv),('SIDE EFFECTS',c_side),('NUTRITION',c_nutr2)]):
        if t>=tt: tag(d,100+i*292,592,s,CYAN,30,appear(t,tt))
    if t>=c_weekly:
        a=appear(t,c_weekly); tag(d,100,660,'TWEAKS · WEEKLY',VGOLD,30,a)
    if t>=c_comm-0.2:
        a=appear(t,c_comm-0.2); y0=740
        txt(d,100,y0,'TIME TO A REPLY',f(MONO,30),CREAM,a); d.line([(100,y0+50),(980,y0+50)],fill=A((60,64,80),a),width=2)
        # bars
        p1=expo((t-c_comm)/0.6); p2=expo((t-c_everyday)/0.35)
        txt(d,100,y0+80,'TYPICAL COACH',f(BEB,48),WHITE,a)
        lit_bar(d,100,y0+140,100+860*p1,y0+210,RED,a)
        if GL: GL.rectangle([100,y0+140,100+860*p1,y0+210],fill=A(RED,0.5*a))
        if p1>0.5: txt(d,120,y0+148,'5–6 DAYS',f(BEB,58),WHITE,a)
        if t>=c_everyday:
            txt(d,100,y0+250,'COACH AGZ',f(BEB,48),VGOLD,a)
            lit_bar(d,100,y0+310,100+150*p2,y0+380,VGOLD,a)
            if GL: GL.rectangle([100,y0+310,100+150*p2,y0+380],fill=A(VGOLD,0.6*a))
            if p2>0.5: txt(d,272,y0+318,'EVERY DAY',f(BEB,58),VGOLD,a)

# ---- 12 testimonial card: "gone to the limits and beyond" (top-tilted card over footage)
@scene(c_damn, cue('honestly')-0.03,'free')
def s_tlimits(lay,d,t):
    t0=c_damn; p=expo((t-t0)/0.32); w=900; sc=w/1030
    im=resized('q_limits.png',w); x=lerp(1100,90,p); y=600
    paste(lay,im,x,y,1,rot=lerp(-6,0,p),radius=26)
    d2=ImageDraw.Draw(lay,'RGBA')
    if p>0.98: highlight(lay,x,y,w,sc,[(20,232,935,296),(20,296,560,360)],t0+0.4,t)
    if t>=t0+0.25: tag(d2,90,y-62,'CLIENT · UNEDITED',VGOLD,28,appear(t,t0+0.25))

# ---- 13 tweak frequency histogram (lower) + shoulder quote (phone)
c_hon=cue('honestly'); c_crush=cue('fucking crushing'); c_tiny=cue('tweak tiny'); c_other=cue('other times'); c_eod=cue('every other day')
@scene(c_hon, c_tiny-0.05,'free')
def s_tshoulder(lay,d,t):
    w=940; sc=w/1030; im=resized('q_shoulder.png',w); im=im.crop((0,0,w,int(625*sc)))
    p=expo((t-c_hon)/0.3); x=70; y=lerp(640,560,p)
    paste(lay,im,x,y,p,radius=24)
    if p>0.5: tag(ImageDraw.Draw(lay,'RGBA'),x,y-60,'CLIENT · 5 WEEKS IN',VGOLD,28,p)
    if t>=c_crush and p>0.98: highlight(lay,x,y,w,sc,[(20,355,660,420),(20,485,1020,550),(20,550,500,615)],c_crush,t)
@scene(c_tiny, cue('the truth is')-0.04,'lower','ADJUSTMENTS','PER WEEK')
def s_hist(lay,d,t):
    x0,y0,x1,y1=LO[0]+50,LO[1]+70,LO[2]-50,LO[3]-50
    vals=[1,0,1,0,1,1,0,1,4,6,5,7,6,3,2,1]
    d.line([(x0,y1),(x1,y1)],fill=A((90,94,110),1),width=2)
    bw=(x1-x0)/len(vals)
    for i,v in enumerate(vals):
        tt=c_tiny+i*0.08 if i<8 else c_eod-0.4+(i-8)*0.12
        if t<tt: continue
        p=expo((t-tt)/0.2); h=v*24*p+6
        col=GREEN if i<8 else VGOLD
        lit_bar(d,x0+i*bw+5,y1-h,x0+(i+1)*bw-5,y1,col)
        if GL: GL.rectangle([x0+i*bw+5,y1-h,x0+(i+1)*bw-5,y1],fill=A(col,0.5))
    txt(d,x0,y1+8,'WK 1',f(MONO,20),MUTED); txt(d,x1-60,y1+8,'WK 16',f(MONO,20),MUTED)
    if t>=c_tiny: tag(d,x0,y0-20,'CRUSHING · TINY TWEAKS',GREEN,24,appear(t,c_tiny))
    if t>=c_eod: tag(d,x0+470,y0-20,'EVERY OTHER DAY',VGOLD,24,appear(t,c_eod))

# ---- 14 protocol gantt: Tren 16 weeks -> what happens after (panel)
c_truth=cue('the truth is'); c_proto=cue('send you a protocol'); c_16=cue('16 weeks'); c_unit=cue('complete unit'); c_after=cue('what happens afterwards')
c_17=cue('17 weeks'); c_20=cue('20 weeks'); c_2y=cue('two years later'); c_edu=cue("haven't been educated"); c_noidea=cue('no idea why')
@scene(c_truth, cue("that's why we have to break")-0.04,'panel','THE PROTOCOL','NOW WHAT')
def s_gantt(lay,d,t):
    if t>=c_proto:
        a=appear(t,c_proto); d.rounded_rectangle([100,560,980,690],radius=12,fill=A((240,240,244),a))
        txt(d,124,574,'PROTOCOL.PDF',f(MONO,26),(90,90,100),a); txt(d,124,610,'TREN · 16 WEEKS',f(BEB,62),INK,a)
        if t>=c_unit: tag(d,700,600,'LOOK THE PART',GREEN,26,appear(t,c_unit))
    x0,x1=100,980; y=800
    zoom=expo((t-c_2y)/0.5) if t>=c_2y else 0
    span=lerp(26,110,zoom)        # weeks visible
    wx=lambda wk: x0+(x1-x0)*wk/span
    if t>=c_16-0.4:
        a=appear(t,c_16-0.4)
        d.line([(x0,y+90),(x1,y+90)],fill=A((90,94,110),a),width=2)
        for wk in range(0,int(span)+1,4 if span<40 else 26):
            X=wx(wk); d.line([(X,y+90),(X,y+102)],fill=A((90,94,110),a),width=2)
        p=expo((t-c_16)/0.7); X=wx(16*p)
        lit_bar(d,x0,y+10,X,y+80,GREEN,a);
        if GL: GL.rectangle([x0,y+10,X,y+80],fill=A(GREEN,0.4))
        txt(d,x0+16,y+18,'ON CYCLE · WK 1–16',f(BEB,46),INK,a*(1-zoom) if p>0.9 else 0)
    if t>=c_after:
        X16=wx(16); p=expo((t-c_after)/0.4)
        for k in range(int((x1-X16)/26*p)):
            d.line([(X16+k*26,y+45),(X16+k*26+14,y+45)],fill=A(RED,0.9),width=4)
        ctext(d,(X16+x1)/2,y-46,'NO PLAN',f(MONO,28),RED,p)
    for wk,tt,lab in [(17,c_17,'WK 17'),(20,c_20,'WK 20'),(104,c_2y,'YEAR 2')]:
        if t<tt: continue
        a=appear(t,tt); X=wx(wk) if wk<=span else x1
        d.line([(X,y+110),(X,y+190)],fill=A(RED,a),width=4)
        if wk<104: a*=1-zoom
        ctext(d,X,y+196,lab,f(MONO,24),CREAM,a); ctext(d,X,y+230,'?',f(BEB,80),RED,a)
    if t>=c_edu: tag(d,100,1150,'NOT EDUCATED',RED,32,appear(t,c_edu))
    if t>=c_noidea: tag(d,460,1150,'NO IDEA WHY',RED,32,appear(t,c_noidea))

# ---- 15 mechanistic feedback loop (panel)
c_mech=cue('mechanistically'); c_cmpd=cue('what the compound'); c_bloods=cue('your bloods'); c_within2=cue('happening within your body'); c_titr=cue('titrate')
c_loop=cue('feedback loop'); INP=[('NUTRITION',cue('from nutrition')),('CARBS',cue('carbs')),('PROTEIN',cue('protein')),('TRAINING',cue('training',cue('protein')))]
@scene(cue("that's why we have to break"), cue('at the end of the day')-0.04,'panel','MECHANISTIC','FEEDBACK LOOP')
def s_loop(lay,d,t):
    cx,cy,R=540,830,215
    NODES=[('COMPOUND',c_cmpd,-90),('BLOODS',c_bloods,0),('YOUR BODY',c_within2,90),('TITRATE',c_titr,180)]
    for i,(s,tt,deg) in enumerate(NODES):
        ang=math.radians(deg); nx=cx+R*math.cos(ang)*1.45; ny=cy+R*math.sin(ang)
        on=t>=tt; a=appear(t,tt) if on else 0.3
        nxt=NODES[(i+1)%4]; a2=math.radians(nxt[2]); mx=cx+R*math.cos(a2)*1.45; my=cy+R*math.sin(a2)
        if t>=nxt[1] and (i<3 or t>=c_loop):
            arc_pts=[(cx+R*1.45*math.cos(ang+(a2-ang if i<3 else math.pi/2)*k/20),cy+R*math.sin(ang+(a2-ang if i<3 else math.pi/2)*k/20)) for k in range(4,17)]
            d.line(arc_pts,fill=A(CYAN,1),width=5); arrow(d,arc_pts[-2][0],arc_pts[-2][1],arc_pts[-1][0],arc_pts[-1][1],CYAN,5)
            if GL: GL.line(arc_pts,fill=A(CYAN,0.8),width=10)
        node(d,nx-140,ny-50,nx+140,ny+50,s,'',VGOLD if s=='TITRATE' else CYAN,a,dim=not on,tsize=48)
    if t>=c_titr:
        k=int((t-c_titr)*6)%8; a=appear(t,c_titr)
        txt(d,cx-150,cy-30,'± TINIEST CHANGE',f(MONO,26),VGOLD,a)
    for i,(s,tt) in enumerate(INP):
        if t<tt: continue
        a=appear(t,tt); x=100+i*222; y=1130
        d.rounded_rectangle([x,y,x+204,y+60],radius=10,fill=A((8,12,22),a),outline=A(GREEN,a),width=3)
        ctext(d,x+102,y+8,s,f(BEB,44),WHITE,a); arrow(d,x+102,y-4,lerp(x+102,cx,0.35),lerp(y-4,cy+R*0.6+60,0.6),GREEN,3,a)

# ---- 16 testimonial "structure" (top card, tilted)
c_eod2=cue('at the end of the day'); c_find=cue('find yourself a coach'); c_build=cue('build out the sustainability')
@scene(c_eod2, cue("it doesn't matter")-0.04,'free')
def s_tdyn(lay,d,t):
    p=expo((t-c_find+0.2)/0.35); w=880; sc=w/1030
    im=resized('q_dynamic.png',w); x=100; y=lerp(300,440,p)
    if p>0: paste(lay,im,x,y,p,rot=lerp(4,0,p),radius=26)
    if t>=c_build and p>0.98: highlight(lay,x,y,w,sc,[(20,25,930,93),(380,159,1010,225),(20,225,520,288)],c_build,t)

# ---- 17 chips: built around wife / kids / family / business / vacation (lower)
c_dm=cue("it doesn't matter"); CH=[('WIFE',cue('a wife')),('KIDS',cue('a kids')),('FAMILY',cue('family',c_dm)),('BUSINESS',cue('a business',c_dm)),('VACATION',cue('vacation',c_dm))]
c_cust=cue('customizing')
@scene(c_dm, cue('because at the end')-0.04,'lower','CUSTOMIZED','AROUND YOUR LIFE')
def s_chips(lay,d,t):
    x=LO[0]+40; y=LO[1]+80
    for i,(s,tt) in enumerate(CH):
        if t<tt: continue
        p=expo((t-tt)/0.12); s2=lerp(1.25,1,p)
        fn=f(BEB,int(56*s2)); w=tl(d,s,fn)+44
        if x+w>LO[2]-30: x=LO[0]+40; y+=88
        d.rounded_rectangle([x,y,x+w,y+72],radius=10,fill=A((40,8,14),p),outline=A(RED,p),width=3)
        txt(d,x+22,y+6,s,fn,(255,190,190),p); x+=w+16
    if t>=c_cust:
        p=expo((t-c_cust)/0.2); y2=LO[3]-80; x1=lerp(LO[0]+40,LO[2]-40,p)
        lit_bar(d,LO[0]+40,y2,x1,y2+64,VGOLD)
        if p>0.6: txt(d,LO[0]+64,y2+4,'PROTOCOL BUILT AROUND ALL OF IT',f(BEB,54),INK)

# ---- 18 the rule: comparison columns (full carousel)
c_bec=cue('because at the end'); c_nota=cue('should not be a protocol'); c_fits=cue('fits your life'); c_never=cue('never should it'); c_otherway=cue('other way around')
@scene(c_bec, cue('and this my friends')-0.03,'full')
def s_rule(lay,d,t):
    full_bg(d,t,'THE RULE','IT FITS YOUR ','',' LIFE.',hl_col=VGOLD)
    cols=[(96,'PROTOCOL FIRST','You bend your life',' around a PDF',RED,c_nota),(560,'LIFE FIRST','The protocol bends',' around your life',GREEN,c_fits)]
    for x,h,l1,l2,col,tt in cols:
        if t<tt: continue
        a=appear(t,tt,0.2); y=760
        d.rectangle([x,y,x+424,y+440],fill=A((24,26,34),a),outline=A((58,54,48),a),width=2)
        p=expo((t-tt)/0.3); d.line([(x,y),(x+424*p,y)],fill=A(col,1),width=6)
        if GL: GL.line([(x,y),(x+424*p,y)],fill=A(col,1),width=10)
        txt(d,x+28,y+40,h,f(BEB,62),WHITE,a); txt(d,x+28,y+130,l1,f(DMR,32),MUTED,a); txt(d,x+28,y+172,l2,f(DMR,32),MUTED,a)
        if col==GREEN: check(d,x+30,y+300,GREEN,2.4,appear(t,tt+0.25))
        else:
            cross(d,x+34,y+300,RED,2.4,appear(t,tt+0.25))
    if t>=c_never:
        q=expo((t-c_otherway)/0.1) if t>=c_otherway else 0
        st=STAMP('NEVER',RED); s=lerp(1.5,1.0,q)
        if q>0:
            sti=st.resize((int(st.width*s*0.8),int(st.height*s*0.8)),Image.BICUBIC).rotate(12,expand=True,resample=Image.BICUBIC)
            sti.putalpha(sti.split()[3].point(lambda v:int(v*q)))
            lay.alpha_composite(sti,(int(308-sti.width/2),int(1020-sti.height/2)))

# ---- 19 transformation wall (full)
c_rant=cue('and this my friends'); c_dozens=cue('dozens upon dozens'); c_prev=cue('previous coaching'); c_sour=cue('sour taste')
TF=['1.png','2.png','3.png','4.png','5.png','6.png']
@scene(c_rant, cue("it's a different level")-0.15,'full')
def s_wall(lay,d,t):
    full_bg(d,t,'CLIENT RESULTS','DOZENS OF ','',' CLIENTS.',hl_col=VGOLD,head_t=c_dozens)
    tw=294; th=int(tw*788/940)
    for i,nm in enumerate(TF):
        tt=c_dozens-0.3+i*0.22
        if t<tt: continue
        p=expo((t-tt)/0.25); r,c=divmod(i,3)
        x=64+c*(tw+16); y=740+r*(th+16)+lerp(60,0,p)
        im=resized(nm,tw); paste(lay,im,x,y,p,radius=12,shadow=False)
        dd=ImageDraw.Draw(lay,'RGBA')
        dd.rectangle([x,y,x+tw,y+th],outline=A(VGOLD,p*0.8),width=3)
        tag(dd,x+8,y+th-40,'BEFORE · AFTER',VGOLD,16,p,glow=False)

# ---- 20 "different level": quote + bar chart from client's words (panel)
c_diff=cue("it's a different level"); c_comp=cue('completely different level')
@scene(c_diff-0.15, cue('ridiculous reports')-0.3,'panel','CLIENT RESULT','IN HIS WORDS')
def s_level(lay,d,t):
    w=880; sc=w/1025; im=resized('q_level.png',w)
    crop=im.crop((0,0,w,int(292*sc)))
    p=expo((t-c_diff+0.15)/0.3)
    paste(lay,crop,100,lerp(620,540,p),p,radius=20,shadow=False)
    dd=ImageDraw.Draw(lay,'RGBA')
    if t>=c_diff+0.1: highlight(lay,100,540,w,sc,[(15,26,1010,96),(15,96,300,160)],c_diff+0.1,t)
    if t>=c_diff+0.5:
        a=appear(t,c_diff+0.5); y=900
        txt(dd,100,y,'SAME GOAL · HOW LONG IT TOOK',f(MONO,26),CREAM,a)
        p1=expo((t-c_diff-0.6)/0.5); p2=expo((t-c_comp)/0.4)
        txt(dd,100,y+50,'ON HIS OWN · 10 YRS AGO',f(BEB,40),MUTED,a)
        lit_bar(dd,100,y+96,100+860*p1,y+150,(120,124,140),a);
        if p1>0.5: txt(dd,118,y+100,'6 MONTHS',f(BEB,48),WHITE,a)
        txt(dd,100,y+168,'WITH COACH AGZ',f(BEB,40),VGOLD,a)
        lit_bar(dd,100,y+214,100+860*0.27*p2,y+268,VGOLD,a)
        if GL: GL.rectangle([100,y+214,100+860*0.27*p2,y+268],fill=A(VGOLD,0.6*a))
        if p2>0.5: txt(dd,350,y+218,'7 WEEKS · AND BETTER',f(BEB,48),VGOLD,a)

# ---- 21 reports phone: report + "most in-depth feedback" (phone)
c_send2=cue('like i send out'); c_reports=cue('ridiculous reports'); c_love=cue('absolutely love it')
@scene(cue('ridiculous reports')-0.27, cue("some guys don't give")+0.5,'phone')
def s_reports(lay,d,t):
    x0,y0,x1,y1=PHONE_BOX; w=x1-x0-40
    im=resized('q_report.png',w); paste(lay,im,x0+20,y0+150,1,radius=16,shadow=False)
    if t>=c_reports: flag(d,(x0+30,y0+150,x1-30,y0+150+im.height*0.62),'',c_reports,t,'none',VGOLD)
    if t>=c_love-0.25:
        p=expo((t-c_love+0.25)/0.3); w2=520; sc=w2/377; im2=resized('q_email.png',w2)
        x=lerp(-600,x0+40,p); y=y0+560
        paste(lay,im2,x,y,1,rot=lerp(-8,0,p),radius=20)
        if p>0.98: highlight(lay,x,y,w2,sc,[(8,34,372,62),(8,62,178,90)],c_love+0.1,t)

# ---- 22 "I trust you" -> client's absolute-trust message (top card)
c_some=cue('some guys just want'); c_tell=cue('just tell me what to do'); c_trust=cue('i trust you')
@scene(c_tell, cue('other guys want')-0.03,'free')
def s_trust(lay,d,t):
    w=900; sc=w/1025; im=resized('q_level.png',w)
    crop=im.crop((0,int(488*sc),w,int(860*sc)))
    p=expo((t-c_tell)/0.3); x=90; y=lerp(250,400,p)
    paste(lay,crop,x,y,p,radius=22)
    if t>=c_trust-0.1 and p>0.98: highlight(lay,x,y-488*sc,w,sc,[(594,557,905,625),(20,625,440,691)],c_trust-0.1,t)
    if t>=c_tell+0.3: tag(ImageDraw.Draw(lay,'RGBA'),x,y+crop.height+16,'TRUST → HE WORKS HARDER',VGOLD,28,appear(t,c_tell+0.3))

# ---- 23 learn -> healthy until 70/80/90: client before/after + healthspan graph (panel)
c_learn=cue('other guys want'); c_themselves=cue('do it themselves'); c_healthy=cue('healthy happy family'); c_70=cue('70'); c_80=cue('80'); c_90=cue('90 years')
@scene(c_learn, cue('with that being said')-0.03,'panel','LEARN IT','FOR LIFE')
def s_life(lay,d,t):
    tw=430; th=int(tw*788/940); im=resized('5.png',tw)
    p=expo((t-c_learn)/0.3); paste(lay,im,100,lerp(620,560,p),p,radius=12,shadow=False)
    dd=ImageDraw.Draw(lay,'RGBA')
    if p>0.5: tag(dd,110,560+th-50,'CLIENT',VGOLD,22,p,glow=False)
    # healthspan graph on right
    gx0,gy0,gx1,gy1=570,580,980,900
    if t>=c_themselves:
        a=appear(t,c_themselves); txt(dd,gx0,gy0-10,'HEALTHSPAN',f(MONO,26),CREAM,a)
        dd.line([(gx0,gy1),(gx1,gy1)],fill=A((90,94,110),a),width=2)
        for k,age in enumerate([40,50,60,70,80,90]):
            X=lerp(gx0,gx1,k/5); dd.text((X-14,gy1+8),str(age),font=f(MONO,20),fill=A(MUTED,a))
    ages=[(c_70,3),(c_80,4),(c_90,5)]
    if t>=c_healthy:
        pp=clamp((t-c_healthy)/(c_90+0.4-c_healthy))
        ptsA=[(lerp(gx0,gx1,k/50),gy0+40+(k/50)**3*45) for k in range(51)]
        ptsB=[(lerp(gx0,gx1,k/50),gy0+60+(k/50)**1.6*230) for k in range(51)]
        n=max(2,int(51*pp))
        dd.line(ptsB[:n],fill=A(RED,0.7),width=4); dd.line(ptsA[:n],fill=A(VGOLD,1),width=6)
        if GL: GL.line(ptsA[:n],fill=A(VGOLD,1),width=12)
        if pp>0.98: txt(dd,gx0+10,gy0+18,'EDUCATED',f(MONO,22),VGOLD); txt(dd,gx1-150,gy1-50,'GUESSING',f(MONO,22),RED)
    for tt,k in ages:
        if t>=tt:
            a=appear(t,tt); X=lerp(gx0,gx1,k/5); dd.ellipse([X-11,gy0+40+(k/5)**3*45-11,X+11,gy0+40+(k/5)**3*45+11],fill=A(WHITE,a))
    if t>=c_70:
        a=appear(t,c_70); y=1000
        txt(dd,100,y,'STILL HERE · STILL STRONG',f(MONO,28),CREAM,a)
        x=100
        for tt,lab in [(c_70,'AT 70'),(c_80,'AT 80'),(c_90,'AT 90')]:
            if t>=tt: x=tag(dd,x,y+50,lab,VGOLD,40,appear(t,tt),font=MONOB)+18

# ---- 24 questions lower-third + CTA end card
c_quest=cue('any questions'); c_nerd=cue('nerd out'); c_reach=cue('reach out'); c_happy=cue("so i'm happy to help")
@scene(c_quest-0.1, c_happy+3.0,'free')
def s_q(lay,d,t):
    a=appear(t,c_quest-0.1,0.2)*(1-clamp((t-c_happy-2.8)/0.2)); y=1010
    frosted(lay,(64,y,800,y+190),0.82,10)
    brackets(d,64,y,800,y+190,A(VGOLD,a),26,5)
    txt(d,96,y+24,'QUESTIONS · COACHING · DIRECTION',f(MONO,26),VGOLD,a)
    txt(d,96,y+78,'DM @coach.agz',f(DMX,72),WHITE,a)
@scene(cue('make sure you reach out')-0.05, 999,'free')
def s_cta(lay,d,t):
    t0=cue('make sure you reach out')-0.05; a=appear(t,t0,0.2); y=980
    frosted(lay,(56,y,1024,y+300),0.84,12)
    brackets(d,56,y,1024,y+300,A(VGOLD,a),30,5)
    lg=LOGO(); lg2=lg.copy(); lg2.putalpha(lg2.split()[3].point(lambda v:int(v*a))); lay.alpha_composite(lg2,(84,y+40))
    txt(d,300,y+40,'REACH OUT · 1:1 COACHING',f(MONO,26),VGOLD,a)
    txt(d,300,y+80,'Bloodwork. Protocol. Your life.',f(DMB,34),CREAM,a)
    if t>=c_reach:
        b=expo((t-c_reach)/0.12); s=lerp(1.12,1.0,b); fn=f(DMX,int(60*s)); label='DM @coach.agz'
        while tl(d,label,fn)>650: fn=f(BEB,fn.size-2)
        w=tl(d,label,fn)
        lit_bar(d,300,y+150,300+w+40,y+150+int(104*s),VGOLD,b); d.text((320,y+164),label,font=fn,fill=A(INK,b))
        if GL: GL.rectangle([296,y+146,304+w+40,y+154+int(104*s)],outline=A(VGOLD,b),width=12)
_logo=None
def LOGO():
    global _logo
    if _logo is None:
        lg=Image.open(AS+'logo.jpg').convert('RGB'); s=min(lg.size); lg=lg.crop(((lg.width-s)//2,(lg.height-s)//2,(lg.width+s)//2,(lg.height+s)//2)).resize((190,190),Image.LANCZOS)
        m=Image.new('L',(190,190),0); ImageDraw.Draw(m).ellipse([0,0,189,189],fill=255); lg.putalpha(m); _logo=lg.convert('RGBA')
    return _logo

# ---------------- full-screen carousel background ----------------
def full_bg(d,t,kicker,h1,h1b,h2,hl_col=VGOLD,head_t=None):
    d.rectangle([0,0,W,H],fill=A(NAVY,1))
    # warm glow top-right
    d.rectangle([8,0,W,H],fill=None)
    txt(d,64,520,'——',f(BEB,40),GOLD); txt(d,140,522,kicker,f(BAR,40),GOLD)
    fn=f(BEB,118); x=64; y=576
    for s,col in [(h1,CREAM),(h1b,CREAM),(h2,hl_col)]:
        if s: d.text((x,y),s,font=fn,fill=A(col,1)); x+=tl(d,s,fn)
    txt(d,64,1560,'FOR RESEARCH & EDUCATIONAL PURPOSES ONLY',f(MONO,20),(124,124,130))
    txt(d,W-64-tl(d,'@coach.agz',f(MONO,22)),1556,'@coach.agz',f(MONO,22),GOLD)
_glowbg=None
def glow_bg():
    global _glowbg
    if _glowbg is None:
        yy,xx=np.mgrid[0:H//4,0:W//4]; r=np.sqrt(((xx-W//4)/(W/4))**2+((yy)/(H/4))**2)
        a=np.clip(1-r/0.9,0,1)**2*70
        _glowbg=Image.fromarray(np.dstack([np.full_like(a,48),np.full_like(a,40),np.full_like(a,30),a]).astype(np.uint8),'RGBA').resize((W,H),Image.BILINEAR)
    return _glowbg

PHONE_BOX=(40,540,520,1290)
def phone_frame(im,t,sc,al):
    x0,y0,x1,y1=PHONE_BOX
    frosted(im,(x0,y0,x1,y1),0.9,8,col=(10,10,14))
    d=ImageDraw.Draw(im,'RGBA')
    d.rounded_rectangle([x0,y0,x1,y1],radius=54,outline=A((70,70,80),al),width=10)
    d.rounded_rectangle([x0+150,y0+20,x1-150,y0+52],radius=16,fill=A((0,0,0),al))
    GL.rounded_rectangle([x0,y0,x1,y1],radius=54,outline=A(VGOLD,0.5*al),width=6)

# ================= hook / band / captions =================
HOOK=EDIT['hook']; HOOK_END=HOOK['end']
def text_hook(im,t):
    if t>=HOOK_END+0.15: return
    a=1-clamp((t-HOOK_END)/0.15); s=1+0.04*clamp(t/HOOK_END)
    lay=Image.new('RGBA',(W,700),(0,0,0,0)); d=ImageDraw.Draw(lay)
    fn=f(DMX,74); lines=HOOK['lines']; emph=HOOK['emphasis']
    y=40
    for ln in lines:
        parts=[]; rest=ln
        for e in emph:
            if e in rest: i=rest.index(e); parts=[(rest[:i],WHITE),(e,VGOLD),(rest[i+len(e):],WHITE)]; break
        if not parts: parts=[(ln,WHITE)]
        w=sum(tl(d,p,fn) for p,_ in parts); x=(W-w)/2
        d.rounded_rectangle([x-30,y-10,x+w+30,y+98],radius=20,fill=(0,0,0,215))
        for p,c in parts: d.text((x,y),p,font=fn,fill=c+(255,)); x+=tl(d,p,fn)
        y+=118
    if s!=1: lay=lay.resize((int(W*s),int(700*s)),Image.BICUBIC)
    if a<1: lay.putalpha(lay.split()[3].point(lambda v:int(v*a)))
    im.alpha_composite(lay,(int((W-lay.width)/2),int(HOOK['y_px']-40*s)))
BAND_END=EDIT['band_end']
def band(im,t):
    if t<HOOK_END or t>=BAND_END+0.15: return
    a=min(clamp((t-HOOK_END)/0.15),1-clamp((t-BAND_END)/0.15))
    d=ImageDraw.Draw(im,'RGBA')
    d.rectangle([8,236,W,340],fill=A(NAVY,0.88*a)); d.line([(64,262),(108,262)],fill=A(GOLD,a),width=4); txt(d,122,248,'@coach.agz',f(MONO,24),GOLD,a)
    fn=f(DMX,46); x=64; y=278
    for p,c in [('ELITE COACHING',VGOLD),('  not a pen pal',WHITE)]:
        d.text((x,y),p,font=fn,fill=A(c,a)); x+=tl(d,p,fn)
FIX={'trend':'TREN','consistently':'CONSISTENCY','bloodwork':'BLOODWORK'}
def build_groups():
    G=[];cur=[]
    for i,x in enumerate(WORDS):
        if cur:
            prev=WORDS[cur[-1]]
            if len(cur)>=3 or x['s']-prev['e']>0.28 or prev['w'][-1] in '.,?!' or any(prev['s']<c<=x['s']+0.01 for c in CUTS_SRC): G.append(cur); cur=[]
        cur.append(i)
    if cur: G.append(cur)
    return G
GROUPS=build_groups(); GSTART=[WORDS[g[0]]['s'] for g in GROUPS]
import bisect
def group_at(t):
    k=bisect.bisect_right(GSTART,t+1e-6)-1
    if k<0: return None
    g=GROUPS[k]; end=WORDS[g[-1]]['e']+0.6
    if t>end and (k+1>=len(GROUPS) or GSTART[k+1]>t): return None
    return g
CAP_Y=1335
def cap_word(w):
    k=_n(w)
    return FIX.get(k, w.upper().strip('",.?!').replace('"',''))
def captions(im,t):
    g=group_at(t)
    if not g: return
    d=ImageDraw.Draw(im,'RGBA')
    ws=[cap_word(WORDS[i]['w']) for i in g]
    size=128
    while True:
        fn=f(BEB,size); sp=tl(d,' ',fn)+14; wd=[tl(d,w,fn) for w in ws]; tot=sum(wd)+sp*(len(ws)-1)
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
    cap.alpha_composite(blur_fast(shd,8))
    lit_bar(cd,bx0,40+size*0.02,bx1,40+size*0.98,RED)
    for k,(w_,x_) in enumerate(zip(ws,xs)): cd.text((x_,40),w_,font=fn,fill=CREAM,stroke_width=0 if k==act else 3,stroke_fill=(0,0,0))
    if abs(s-1)>0.002:
        cap=cap.resize((int(W*s),int(300*s)),Image.BICUBIC); ox=int((W-cap.width)/2); oy=int(CAP_Y-40-(cap.height-300)/2)
    else: ox,oy=0,CAP_Y-40
    im.alpha_composite(cap,(ox,oy))

# ================= frame compositor =================
PUNCH=EDIT['punch']   # list of [src_t0, src_t1, zoom]
def zoom_at(ts):
    z=1.0
    for a,b,zz in PUNCH:
        if a<=ts<b: z=zz
    return z
def active(ts):
    return [s for s in SC if s['t0']<=ts<s['t1']+0.2]
def frame(src,ts):
    global GL
    z=zoom_at(ts)
    if z!=1.0:
        big=src.resize((int(W*z),int(H*z)),Image.BICUBIC); ox=(big.width-W)//2; oy=int((big.height-H)*0.38); src=big.crop((ox,oy,ox+W,oy+H))
    act=active(ts)
    # background push for panel/full scenes
    g=0
    for s in act:
        if s['lay'] in ('panel','full'):
            g=max(g,min(ease_io((ts-s['t0']+0.05)/0.30),1-ease_io((ts-s['t1'])/0.22)))
    im=src
    if g>0: im=Image.blend(blur_fast(src,18*g),Image.new('RGB',(W,H),(5,8,16)),0.68*g)
    im=im.convert('RGBA')
    yy=np.arange(H); a=np.where(yy>1180,np.clip((yy-1180)/260,0,1)*110,0); a=np.maximum(a,np.where(yy<420,(1-yy/420)*120,0)); scr=(a*(1-g)).astype(np.uint8)
    im.alpha_composite(Image.merge('RGBA',[Image.new('L',(W,H),c) for c in NAVY]+[Image.fromarray(np.repeat(scr[:,None],W,1))]))
    glow=Image.new('RGBA',(W,H),(0,0,0,0)); GL=ImageDraw.Draw(glow,'RGBA')
    for s in act:
        pin=expo((ts-s['t0'])/0.20); pout=clamp((ts-s['t1'])/0.18)
        if pout>=1: continue
        al=pin*(1-pout); L=s['lay']
        lay=Image.new('RGBA',(W,H),(0,0,0,0)); d=ImageDraw.Draw(lay,'RGBA')
        if L=='full':
            lay.alpha_composite(glow_bg()); s['fn'](lay,d,ts)
            d=ImageDraw.Draw(lay,'RGBA'); d.rectangle([0,0,7,H],fill=A(GOLD,1))
            lay.putalpha(lay.split()[3].point(lambda v:int(v*al))); im.alpha_composite(lay); continue
        if L in ('panel','lower'):
            box=P if L=='panel' else LO
            sc=lerp(1.04,1.0,pin)*lerp(1.0,1.03,pout); w=(box[2]-box[0])*sc; h=(box[3]-box[1])*sc; cx=(box[0]+box[2])/2; cy=(box[1]+box[3])/2
            x0,y0,x1,y1=cx-w/2,cy-h/2,cx+w/2,cy+h/2
            if L=='lower': y0+=lerp(40,0,pin); y1+=lerp(40,0,pin)
            frosted(im,(x0,y0,x1,y1),0.92 if L=='panel' else 0.86,8)
        if L=='phone':
            dx=lerp(-560,0,ease_io(pin*1.0))-560*ease_io(pout)
            ph=Image.new('RGBA',(W,H),(0,0,0,0))
            # draw phone onto im at offset by temporarily shifting box
            global PHONE_BOX
            base=(40,540,520,1290); PHONE_BOX=(base[0]+dx,base[1],base[2]+dx,base[3])
            phone_frame(im,ts,1,1)
            lay=Image.new('RGBA',(W,H),(0,0,0,0)); d=ImageDraw.Draw(lay,'RGBA')
        if L=='top':
            frosted(im,(64,410,1016,570),0.9,8)
        s['fn'](lay,d,ts)
        if L=='phone': PHONE_BOX=(40,540,520,1290)
        if pin<1 and L!='phone': lay=blur_fast(lay,8*(1-pin))
        if al<1: lay.putalpha(lay.split()[3].point(lambda v:int(v*al)))
        im.alpha_composite(lay); d=ImageDraw.Draw(im,'RGBA')
        if L in ('panel','lower'):
            d.rectangle([x0,y0,x1,y1],outline=A(VGOLD,0.8*al),width=3); brackets(d,x0,y0,x1,y1,A(VGOLD,al),44,7)
            GL.rectangle([x0,y0,x1,y1],outline=A(VGOLD,0.5*al),width=6); brackets(GL,x0,y0,x1,y1,A(VGOLD,al),44,14)
            d.ellipse([x0+26,y0+26,x0+42,y0+42],fill=A(RED,al if int(ts*4)%2==0 else al/3))
            txt(d,x0+56,y0+18,s['hl'],f(MONO,28),WHITE,al); fr=f(MONO,28); twd=tl(d,s['hr'],fr); txt(d,x1-30-twd,y0+18,s['hr'],fr,VGOLD,al)
    # bloom
    if glow.getbbox():
        sm=glow.resize((W//4,H//4),Image.BILINEAR)
        g1=np.asarray(sm.filter(ImageFilter.GaussianBlur(3.5))).astype(np.float32)/255; g2=np.asarray(sm.filter(ImageFilter.GaussianBlur(10))).astype(np.float32)/255
        prem=np.clip(g1[...,:3]*g1[...,3:]*2.3+g2[...,:3]*g2[...,3:]*1.8,0,1)
        prem=np.asarray(Image.fromarray((prem*255).astype(np.uint8)).resize((W,H),Image.BILINEAR)).astype(np.float32)/255
        b=np.asarray(im.convert('RGB')).astype(np.float32)/255
        im=Image.fromarray(((1-(1-b)*(1-prem))*255).astype(np.uint8)).convert('RGBA')
    GL=None
    d=ImageDraw.Draw(im,'RGBA'); d.rectangle([0,0,7,H],fill=GOLD)
    band(im,ts); text_hook(im,ts)
    captions(im,ts)
    out=im.convert('RGB')
    for tk in EDIT['shakes']:
        k=round((ts-tk)*FPS)
        if k in (0,1):
            dx=[9,-5][k]; zz=1.025; big=out.resize((int(W*zz),int(H*zz)),Image.BICUBIC); ox=(big.width-W)//2-dx; oy=(big.height-H)//2
            out=big.crop((ox,oy,ox+W,oy+H)); ImageDraw.Draw(out).rectangle([0,0,7,H],fill=GOLD)
    return out

def out_to_src(to):
    acc=0
    for a,b in KEEP:
        if to < acc+(b-a)-1e-9: return a+(to-acc)
        acc+=b-a
    return KEEP[-1][1]-1/FPS
if __name__=='__main__':
    mode=sys.argv[2]
    if mode=='cues':
        for s in SC: print(f"{s['t0']:7.2f}-{s['t1']:7.2f} {s['lay']:6s} {s['fn'].__name__}")
        sys.exit()
    if mode=='stills':
        import os; os.makedirs(S+'qc/st',exist_ok=True)
        for tt in [float(x) for x in sys.argv[3:]]:
            ts=out_to_src(tt); sf=round(ts*FPS)/FPS
            subprocess.run(['ffmpeg','-v','error','-y','-ss',f'{sf:.4f}','-i',S+'src/raw.mov','-frames:v','1',S+'qc/_src.png'])
            fr=frame(Image.open(S+'qc/_src.png').convert('RGB'),ts); fr.resize((540,960)).save(S+f'qc/st/o{tt:07.2f}.jpg',quality=88)
        sys.exit()
    n0,n1,out=int(sys.argv[3]),int(sys.argv[4]),sys.argv[5]
    srcf=[round(out_to_src(n/FPS)*FPS) for n in range(n0,n1)]
    first=srcf[0]
    dec=subprocess.Popen(['ffmpeg','-v','error','-ss',f'{max(0,first/FPS-0.0):.4f}','-i',S+'src/raw.mov','-vf','fps=30','-f','rawvideo','-pix_fmt','rgb24','-'],stdout=subprocess.PIPE)
    enc=subprocess.Popen(['ffmpeg','-v','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-','-c:v','libx264','-crf','14','-preset','veryfast','-pix_fmt','yuv420p',out],stdin=subprocess.PIPE)
    cur=first-1; buf=None
    for n,o in zip(range(n0,n1),srcf):
        while cur<o:
            buf=dec.stdout.read(W*H*3); cur+=1
            if len(buf)<W*H*3: raise SystemExit(f'short read at src frame {cur}')
        enc.stdin.write(frame(Image.frombuffer('RGB',(W,H),buf),o/FPS).tobytes())
    enc.stdin.close(); enc.wait(); dec.kill(); print('done',n0,n1)
