# @coach.agz Reel 03 "3 things I'd never do on cycle again": 1080x1920 30fps render
# usage: python3 reel_render.py <build_dir> stills t1 t2 ...   |   <build_dir> chunk n0 n1 out.mp4
import json, subprocess, sys, math
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
B=sys.argv[1].rstrip('/')+'/'; F=B+'../fonts/'
W,H=1080,1920; FPS=30
TR=json.load(open(B+'trim.json')); KEEP=TR['keep']
CUTS=[]; _acc=0
for a,b in KEEP: _acc+=b-a; CUTS.append(_acc)
DUR=CUTS[-1]
WORDS=json.load(open(B+'words.json'))
GOLD=(201,169,110); CREAM=(244,241,234); NAVY=(14,17,23); MUTED=(184,184,188)
RED=(255,34,28); VGOLD=(255,194,26); CYAN=(0,229,255); GREEN=(30,255,110); DEEP=(2,3,8); INK=(6,8,14); WHITE=(255,255,255)
BLUE=(79,163,224); SGREEN=(60,203,106); AMBER=(240,160,48); CRIM=(224,36,63); CRIMBAR=(200,16,46)
MONO='JBMono-500.ttf'; MONOB='JBMono-700.ttf'; BEB='BebasNeue.ttf'; DMB='DMSans-700.ttf'; DMR='DMSans-400.ttf'; BAR='Barlow-700.ttf'
_fc={}
def f(n,s):
    k=(n,int(s))
    if k not in _fc: _fc[k]=ImageFont.truetype(F+n,int(s))
    return _fc[k]
def clamp(x,a=0,b=1): return max(a,min(b,x))
def expo(x): x=clamp(x); return 1 if x>=1 else 1-2**(-10*x)
def ease_io(x): x=clamp(x); return 4*x**3 if x<.5 else 1-(-2*x+2)**3/2
def back(x,s=1.2): x=clamp(x); return 1+(s+1)*(x-1)**3+s*(x-1)**2
def lerp(a,b,t): return a+(b-a)*t
def A(c,a): return tuple(c[:3])+(int(clamp(a)*255),)
def appear(t,t0,dur=0.16): return expo((t-t0)/dur)
def win(t,a,b,fi=0.2,fo=0.16): return min(expo((t-a)/fi),1-clamp((t-b)/fo))
GL=None
# ---------------- primitives (from the saved full-test pipeline) ----------------
def brackets(d,x0,y0,x1,y1,col,L=34,w=4):
    for (cx,cy,sx,sy) in [(x0,y0,1,1),(x1,y0,-1,1),(x0,y1,1,-1),(x1,y1,-1,-1)]:
        d.line([(cx,cy),(cx+sx*L,cy)],fill=col,width=w); d.line([(cx,cy),(cx,cy+sy*L)],fill=col,width=w)
def lit_bar(d,x0,y0,x1,y1,col,a=1.0):
    h=max(1,int(y1-y0))
    for i in range(h):
        k=i/h; c=tuple(int(min(255,v*(1.18-0.36*k)+(40 if k<0.12 else 0))) for v in col)
        d.line([(x0,y0+i),(x1,y0+i)],fill=c+(int(255*a),))
def tag(d,x,y,label,col=RED,size=32,a=1.0,glow=True):
    if a<=0: return x
    fn=f(MONO,size); tw=d.textlength(label,font=fn); h=size+16
    lit_bar(d,x,y,x+tw+24,y+h,col,a); d.text((x+12,y+5),label,font=fn,fill=A(WHITE if col not in (VGOLD,GREEN,CYAN) else INK,a))
    if GL and glow: GL.rectangle([x-4,y-4,x+tw+28,y+h+4],outline=A(col,a),width=8)
    return x+tw+24
def tagw(d,label,size): return d.textlength(label,font=f(MONO,size))+24
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
        if side=='right': tag(d,x1+12,(y0+y1)/2-23,label,col,30)
        elif side=='above': tag(d,x0,y0-58,label,col,30)
        else: tag(d,x0,y1+10,label,col,30)
def arrow(d,x0,y0,x1,y1,col,w=5,a=1.0,L=18):
    d.line([(x0,y0),(x1,y1)],fill=A(col,a),width=w)
    ang=math.atan2(y1-y0,x1-x0)
    d.polygon([(x1,y1),(x1-L*math.cos(ang-0.45),y1-L*math.sin(ang-0.45)),(x1-L*math.cos(ang+0.45),y1-L*math.sin(ang+0.45))],fill=A(col,a))
    if GL: GL.line([(x0,y0),(x1,y1)],fill=A(col,a*0.7),width=w+6)
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
        fn=f(BEB,44); tw=d.textlength(value,font=fn); d.text((x1-tw,y0-50),value,font=fn,fill=A(col,a))
def check(d,x,y,col,s=1.0,a=1.0):
    d.line([(x,y+16*s),(x+10*s,y+28*s),(x+30*s,y+2*s)],fill=A(col,a),width=int(6*s))
    if GL: GL.line([(x,y+16*s),(x+10*s,y+28*s),(x+30*s,y+2*s)],fill=A(col,a),width=int(12*s))
def cross(d,x,y,col,s=1.0,a=1.0):
    d.line([(x,y),(x+28*s,y+28*s)],fill=A(col,a),width=int(6*s)); d.line([(x+28*s,y),(x,y+28*s)],fill=A(col,a),width=int(6*s))
    if GL: GL.line([(x,y),(x+28*s,y+28*s)],fill=A(col,a),width=12); GL.line([(x+28*s,y),(x,y+28*s)],fill=A(col,a),width=12)
def txt(d,x,y,s,font,col,a=1.0,anchor=None):
    if a>0: d.text((x,y),s,font=font,fill=A(col,a),anchor=anchor)
def ctxt(d,cx,y,s,font,col,a=1.0):
    tw=d.textlength(s,font=font); txt(d,cx-tw/2,y,s,font,col,a)
def dashed_rect(d,x0,y0,x1,y1,col,a,dash=12,w=3):
    for (ax,ay,bx,by) in [(x0,y0,x1,y0),(x1,y0,x1,y1),(x1,y1,x0,y1),(x0,y1,x0,y0)]:
        L=math.hypot(bx-ax,by-ay); n=int(L//(dash*2))+1
        for k in range(n):
            s=k*dash*2/L; e=min(1,(k*dash*2+dash)/L)
            if s<1: d.line([(lerp(ax,bx,s),lerp(ay,by,s)),(lerp(ax,bx,e),lerp(ay,by,e))],fill=A(col,a),width=w)
def frosted(im,box,dark=0.86,blur=10):
    x0,y0,x1,y1=[int(v) for v in box]; x0=max(0,x0); y0=max(0,y0); x1=min(W,x1); y1=min(H,y1)
    if x1<=x0 or y1<=y0: return
    reg=im.crop((x0,y0,x1,y1)).convert('RGB').filter(ImageFilter.GaussianBlur(blur))
    im.paste(Image.blend(reg,Image.new('RGB',reg.size,DEEP),dark).convert('RGBA'),(x0,y0))
def panel_frame(d,x0,y0,x1,y1,al,hl,hr,col=VGOLD,t=0):
    d.rectangle([x0,y0,x1,y1],outline=A(col,0.8*al),width=3); brackets(d,x0,y0,x1,y1,A(col,al),48,7)
    if GL: GL.rectangle([x0,y0,x1,y1],outline=A(col,0.5*al),width=6); brackets(GL,x0,y0,x1,y1,A(col,al),48,14)
    d.ellipse([x0+26,y0+26,x0+42,y0+42],fill=A(RED,al if int(t*4)%2==0 else al/3))
    txt(d,x0+56,y0+18,hl,f(MONO,28),WHITE,al); fr=f(MONO,28); tw=d.textlength(hr,font=fr); txt(d,x1-30-tw,y0+18,hr,fr,col,al)
def drop(d,cx,cy,r,col,a=1.0):
    d.ellipse([cx-r,cy-r*0.2,cx+r,cy+r*1.8],fill=A(col,a)); d.polygon([(cx-r*0.95,cy+r*0.6),(cx,cy-r*1.4),(cx+r*0.95,cy+r*0.6)],fill=A(col,a))
    if GL: GL.ellipse([cx-r*1.3,cy-r*0.6,cx+r*1.3,cy+r*2.1],fill=A(col,a*0.6))
def lock(d,x,y,col,a=1.0,s=1.0):
    d.arc([x+6*s,y,x+30*s,y+28*s],180,360,fill=A(col,a),width=int(5*s)); d.rounded_rectangle([x,y+14*s,x+36*s,y+44*s],radius=5,fill=A(col,a))

# ---------------- footage transform ----------------
def seg_of(t): return sum(1 for c in CUTS[:-1] if c<=t+1e-6)
SPLIT=(36.40,56.95)       # face window + graph below
PUSH=(72.50,80.45)        # footage pushed aside, ladder card on the left
WIN=(190,380,890,940)     # split window dest
WSRC=(0,404,1080,1268)    # src crop for split window (same aspect as WIN)
def footage(src,t):
    z=1.0 if seg_of(t)%2==0 else 1.08
    if z!=1.0:
        big=src.resize((int(W*z),int(H*z)),Image.BICUBIC); ox=(big.width-W)//2; oy=int((big.height-H)*0.35); src=big.crop((ox,oy,ox+W,oy+H))
    sp=min(ease_io((t-SPLIT[0])/0.36),1-ease_io((t-SPLIT[1])/0.30)) if SPLIT[0]<=t<SPLIT[1]+0.3 else 0
    pp=min(ease_io((t-PUSH[0])/0.34),1-ease_io((t-PUSH[1])/0.28)) if PUSH[0]<=t<PUSH[1]+0.28 else 0
    if sp>0:
        bg=Image.blend(src.filter(ImageFilter.GaussianBlur(22)),Image.new('RGB',(W,H),(5,8,16)),0.78*sp)
        dx0=lerp(0,WIN[0],sp); dy0=lerp(0,WIN[1],sp); dx1=lerp(W,WIN[2],sp); dy1=lerp(H,WIN[3],sp)
        sx0=lerp(0,WSRC[0],sp); sy0=lerp(0,WSRC[1],sp); sx1=lerp(W,WSRC[2],sp); sy1=lerp(H,WSRC[3],sp)
        piece=src.crop((int(sx0),int(sy0),int(sx1),int(sy1))).resize((int(dx1-dx0),int(dy1-dy0)),Image.BICUBIC)
        m=Image.new('L',piece.size,0); ImageDraw.Draw(m).rounded_rectangle([0,0,piece.width-1,piece.height-1],radius=int(28*sp),fill=255)
        bg.paste(piece,(int(dx0),int(dy0)),m); return bg,sp,0
    if pp>0:
        sh=int(270*pp); bg=Image.blend(src.filter(ImageFilter.GaussianBlur(22)),Image.new('RGB',(W,H),(5,8,16)),0.8*pp)
        bg.paste(src.crop((0,0,W-sh,H)),(sh,0)); return bg,0,pp
    return src,0,0

# ---------------- text hook (TEXT_HOOK_ENGINE winner) + topic band ----------------
HOOK_END=6.0; BAND_END=48.533
def text_hook(im,t):
    if t>=HOOK_END+0.15: return
    a=1 if t<HOOK_END else 1-clamp((t-HOOK_END)/0.15)
    s=1.0+0.04*clamp(t/HOOK_END)                       # slow 100->104% push over the hold
    lay=Image.new('RGBA',(W,620),(0,0,0,0)); d=ImageDraw.Draw(lay,'RGBA')
    f1=f(BAR,112); f2=f(BAR,74)
    l1=[('3 ',WHITE),('CYCLE',VGOLD),(' mistakes',WHITE)]; l2="your clinic won't like #3"
    w1=sum(d.textlength(s_,font=f1) for s_,_ in l1); w2=d.textlength(l2,font=f2)
    bw=max(w1,w2)+80; x0=(W-bw)/2; y0=150
    d.rounded_rectangle([x0,y0,x0+bw,y0+228],radius=26,fill=(6,8,14,226))
    d.rectangle([x0,y0+22,x0+7,y0+206],fill=VGOLD+(255,))
    x=(W-w1)/2
    for s_,c in l1:
        d.text((x,y0+4),s_,font=f1,fill=c+(255,)); x+=d.textlength(s_,font=f1)
    d.text(((W-w2)/2,y0+124),l2,font=f2,fill=CREAM+(255,))
    if s!=1: lay=lay.resize((int(W*s),int(620*s)),Image.BICUBIC); lay=lay.crop(((lay.width-W)//2,int((lay.height-620)*0.3),(lay.width-W)//2+W,int((lay.height-620)*0.3)+620))
    lay.putalpha(lay.split()[3].point(lambda v:int(v*a)))
    im.alpha_composite(lay,(0,110))
SECT=[(12.24,25.02),(25.02,57.22),(57.22,99)]
def band(im,t):
    if t<HOOK_END or t>=BAND_END+0.15: return
    a=min(clamp((t-HOOK_END)/0.15),1-clamp((t-BAND_END)/0.15))
    d=ImageDraw.Draw(im,'RGBA'); y0,y1=236,352
    d.rectangle([8,y0,W,y1],fill=NAVY+(int(220*a),)); d.line([(64,y0+26),(108,y0+26)],fill=A(GOLD,a),width=4)
    txt(d,122,y0+10,'@coach.agz',f(MONO,26),GOLD,a)
    fn=f(BAR,64); x=64
    for s_,c in [('3 ',CREAM),('CYCLE',VGOLD),(' mistakes',CREAM)]:
        txt(d,x,y0+40,s_,fn,c,a); x+=d.textlength(s_,font=fn)
    for i in range(3):
        cx0=700+i*112; cy0=y0+30
        act=SECT[i][0]<=t<SECT[i][1]; done=t>=SECT[i][1]
        warn=(i==2 and 9.40<=t<12.0)
        col=RED if warn else (VGOLD if act else ((120,110,90) if done else (70,74,90)))
        if act or warn:
            lit_bar(d,cx0,cy0,cx0+96,cy0+62,col,a)
            if GL: GL.rectangle([cx0-4,cy0-4,cx0+100,cy0+66],outline=A(col,a),width=8)
            ctxt(d,cx0+48,cy0+6,f'0{i+1}',f(BEB,54),INK if not warn else WHITE,a)
        else:
            d.rectangle([cx0,cy0,cx0+96,cy0+62],outline=A(col,a),width=3); ctxt(d,cx0+48,cy0+6,f'0{i+1}',f(BEB,54),col,a)
    if 9.56<=t<12.0:
        b=appear(t,9.56,0.12)*(1-clamp((t-11.8)/0.2)); x1=924
        d.line([(x1,y1),(x1,y1+28)],fill=A(RED,b),width=3)
        tw=tagw(d,'DOCTORS ✕',26); tag(d,x1-tw+48,y1+28,'DOCTORS ✕',RED,26,b)

# ---------------- 1. year-on-Tren log card (lower third card) ----------------
def year_card(im,t):
    if not (4.30<=t<8.70): return
    pin=expo((t-4.30)/0.22); pout=ease_io((t-8.40)/0.26); dx=lerp(-60,0,pin)-700*pout
    x0,y0,x1,y1=56+dx,880,646+dx,1250
    frosted(im,(x0,y0,x1,y1),0.84,14); d=ImageDraw.Draw(im,'RGBA'); a=pin
    d.rectangle([x0,y0,x0+6,y1],fill=A(VGOLD,a)); brackets(d,x0,y0,x1,y1,A(VGOLD,a),26,5)
    if GL: brackets(GL,x0,y0,x1,y1,A(VGOLD,a),26,10)
    txt(d,x0+28,y0+18,'CYCLE LOG',f(MONO,26),VGOLD,a)
    if t>=4.56:
        b=appear(t,4.56); txt(d,x0+28,y0+52,'TREN',f(BEB,64),WHITE,b); tw=d.textlength('TREN ',font=f(BEB,64))
        cnt=int(lerp(0,500,expo((t-4.56)/0.5))); txt(d,x0+28+tw,y0+52,f'{cnt} MG',f(BEB,64),VGOLD,b)
    fill=clamp((t-5.6)/0.75)*52
    for i in range(52):
        c=i%13; r=i//13; cx=x0+30+c*42; cy=y0+150+r*42
        if i<fill:
            col=VGOLD if t<7.58 else lerp_col(VGOLD,(90,14,14),appear(t,7.58,0.3)); d.rectangle([cx,cy,cx+32,cy+32],fill=A(col,a))
            if GL: GL.rectangle([cx-2,cy-2,cx+34,cy+34],fill=A(col,0.35*a))
        else: d.rectangle([cx,cy,cx+32,cy+32],outline=A((70,74,90),a),width=2)
    wk=int(min(52,fill)); txt(d,x0+28,y0+326,f'WEEK {wk:02d} / 52',f(MONO,26),CREAM,a)
    if t>=6.18: b=appear(t,6.18); tag(d,x0+300,y0+316,'1 YEAR STRAIGHT',VGOLD,24,b)
    if t>=7.58:
        b=appear(t,7.58,0.1); s=lerp(1.4,1.0,b); fn=f(BEB,int(76*s)); lab='NEVER AGAIN'; tw=d.textlength(lab,font=fn)
        cx=(x0+x1)/2; cy=y0+214
        d.rectangle([cx-tw/2-20,cy-48*s,cx+tw/2+20,cy+44*s],fill=A((10,4,6),0.96*b),outline=A(RED,b),width=5)
        if GL: GL.rectangle([cx-tw/2-24,cy-52*s,cx+tw/2+24,cy+48*s],outline=A(RED,b),width=10)
        d.text((cx-tw/2,cy-42*s),lab,font=fn,fill=A(RED,b))
def lerp_col(a,b,t): return tuple(int(lerp(x,y,t)) for x,y in zip(a,b))

# ---------------- 2. section bumpers (giant numeral) ----------------
BUMPS=[(12.24,14.75,'01','NO BASELINE',VGOLD),(25.02,28.90,'02','E2 PANIC',VGOLD),(57.22,61.00,'03','THE CLINIC FIX',RED)]
def bumper_push(t):
    for t0,t1,*_ in BUMPS:
        if t0<=t<t1+0.2: return min(ease_io((t-t0)/0.12),1-ease_io((t-t1)/0.2))
    return 0
def bumper(im,t):
    for i,(t0,t1,num,lab,col) in enumerate(BUMPS):
        if not (t0<=t<t1+0.22): continue
        d=ImageDraw.Draw(im,'RGBA'); pin=expo((t-t0)/0.14); pout=ease_io((t-t1)/0.22)
        a=pin*(1-pout); s=lerp(1.35,1.0,pin)*lerp(1,0.6,pout)
        cy=lerp(760,700,pout) if i<2 else 760
        fn=f(BEB,int(520*s)); tw=d.textlength(num,font=fn)
        lay=Image.new('RGBA',(W,H),(0,0,0,0)); ld=ImageDraw.Draw(lay)
        ld.text((W/2-tw/2,cy-300*s),num,font=fn,fill=A(col,a))
        if pin<1: lay=lay.filter(ImageFilter.GaussianBlur(10*(1-pin)))
        im.alpha_composite(lay);
        if GL: GL.text((W/2-tw/2,cy-300*s),num,font=fn,fill=A(col,0.55*a))
        d=ImageDraw.Draw(im,'RGBA')
        k=appear(t,t0+0.08,0.2)*(1-pout); ky=cy-330
        d.line([(W/2-250,ky),(lerp(W/2-250,W/2-170,k),ky)],fill=A(col,k),width=4); txt(d,W/2-150,ky-22,'M I S T A K E',f(MONO,34),col,k)
        lb=appear(t,t0+0.22,0.18)*(1-pout); fl=f(BEB,96); lw=d.textlength(lab,font=fl); bx=W/2-lw/2-26; by=cy+250
        wx=lerp(bx,bx+lw+52,lb); lit_bar(d,bx,by,wx,by+104,col,lb)
        if GL: GL.rectangle([bx-4,by-4,wx+4,by+108],outline=A(col,lb),width=10)
        if lb>0.6: txt(d,W/2-lw/2,by+6,lab,fl,INK if col==VGOLD else WHITE,lb)
        if num=='02': bump02_extra(d,t,1-pout)
        if num=='03': bump03_extra(d,t,1-pout)
def bump02_extra(d,t,a):
    # one dot, one high E2 reading, an AI thrown straight at it
    y=cy_=1150
    if t>=26.36:
        p=expo((t-27.94)/0.16) if t>=27.94 else 0
        x=lerp(880,560,p); y=lerp(1230,1210,p)
        d.rounded_rectangle([x-56,y-34,x+56,y+34],radius=10,fill=A(RED,appear(t,26.36)*a)); ctxt(d,x,y-30,'AI',f(BEB,62),WHITE,appear(t,26.36)*a)
        if GL: GL.rounded_rectangle([x-60,y-38,x+60,y+38],radius=12,outline=A(RED,a),width=10)
    if t>=27.16:
        b=appear(t,27.16)*a; d.line([(300,1290),(780,1290)],fill=A((90,94,110),b),width=2)
        if t<27.94+0.05:
            d.ellipse([524,1194,556,1226],fill=A(WHITE,b)); txt(d,330,1196,'1 READING',f(MONO,26),CREAM,b)
        if t>=27.56 and t<27.94+0.05: tag(d,580,1150,'E2 · H',RED,26,appear(t,27.56)*a)
    if t>=27.94: flag(d,(470,1150,650,1270),'',27.94,t,'none')
def bump03_extra(d,t,a):
    if t>=58.42:
        b=appear(t,58.42)*a; tw=tagw(d,'TRT CLINIC DEFAULT',38); x=W/2-tw/2-30
        tag(d,x,1140,'TRT CLINIC DEFAULT',(70,74,92),38,b,glow=False)
    if t>=59.62:
        b=appear(t,59.62)*a; cross(d,W/2+tw/2-6,1150,RED,1.4,b)

# ---------------- 3. grouped bar chart: week 0 vs week 8 (full panel) ----------------
P=(64,470,1016,1260)
MARK=['TOTAL T','E2','HCT','LIPIDS']; W8=[0.92,0.70,0.62,0.55]
def scene_bars(d,t):
    x0,y0,x1,y1=130,640,960,1060
    txt(d,110,560,'YOUR PANEL',f(MONO,30),VGOLD)
    # legend
    d.rectangle([520,566,546,592],outline=A(CYAN,1),width=3); txt(d,556,560,'WEEK 0',f(MONO,26),CYAN)
    d.rectangle([730,566,756,592],fill=A(VGOLD,1)); txt(d,766,560,'WEEK 8',f(MONO,26),VGOLD)
    d.line([(x0,y1),(x1,y1)],fill=A((90,94,110),1),width=2)
    for k in range(1,4): d.line([(x0,y1-k*100),(x1,y1-k*100)],fill=A((34,38,52),1),width=1)
    gw=(x1-x0)/4
    for i,m in enumerate(MARK):
        gx=x0+i*gw+24
        ctxt(d,gx+gw/2-24,y1+14,m,f(MONO,26),CREAM)
        # week 0 ghost (no baseline)
        ga=appear(t,15.84+i*0.08,0.2)
        if ga>0:
            dashed_rect(d,gx,y1-300,gx+72,y1,CYAN,ga*(0.55+0.45*(0.5+0.5*math.sin(t*6))) if t<18.22 else ga,10,3)
            ctxt(d,gx+36,y1-200,'?',f(BEB,96),CYAN,ga)
        # week 8 bar
        if t>=19.24:
            p=expo((t-19.24-i*0.09)/0.45); h=W8[i]*360*p
            lit_bar(d,gx+90,y1-h,gx+162,y1,VGOLD,1)
            if GL: GL.rectangle([gx+90,y1-h,gx+162,y1],outline=A(VGOLD,0.9),width=6)
        if t>=20.24:
            b=appear(t,20.24+i*0.07,0.14); top=y1-W8[i]*360-50
            d.line([(gx+36,top),(gx+126,top)],fill=A(RED,b),width=4); d.line([(gx+36,top),(gx+36,top+18)],fill=A(RED,b),width=4); d.line([(gx+126,top),(gx+126,top+18)],fill=A(RED,b),width=4)
            ctxt(d,gx+81,top-50,'Δ ?',f(BEB,44),RED,b)
    if t>=18.22 and t<19.3: tag(d,110,1120,'WEEK 0 · NOT DRAWN',CYAN,28,appear(t,18.22))
    if t>=19.3: tag(d,110,1120,'CHANGE · UNKNOWN',RED,28,appear(t,20.30))
    if t>=22.08:
        b=appear(t,22.08); x=110
        for nm in ['COMPOUND A','COMPOUND B']: x=tag(d,x,1180,nm,(60,64,80),26,b,glow=False)+12
        txt(d,x+8,1184,'→ EFFECT ?',f(MONO,28),CREAM,b)
    if t>=23.96:
        b=appear(t,23.96,0.12); s=lerp(1.3,1,b); fn=f(BEB,int(120*s)); zx=860-d.textlength('0',font=fn)/2
        txt(d,zx,1100-30*(s-1)*4,'0',fn,RED,b); txt(d,920,1150,'DATA',f(MONO,26),RED,b); txt(d,920,1182,'POINTS',f(MONO,26),RED,b)
        if GL: GL.text((zx,1100-30*(s-1)*4),'0',font=fn,fill=A(RED,b))

# ---------------- 4. E2 hub with callouts around the subject ----------------
HUB=(540,1150)
SPOKES=[('JOINTS',31.36,(70,640),CYAN),('LIBIDO',31.84,(770,640),CYAN),('MOOD',32.46,(70,880),CYAN),('IGF-1',33.28,(770,880),VGOLD)]
def hub(im,t):
    if not (29.62<=t<36.40): return
    a=win(t,29.62,36.20,0.2,0.2)
    for nm,tt,(x,y),col in SPOKES:
        if t>=tt: frosted(im,(x,y,x+240,y+92),0.8,10)
    frosted(im,(HUB[0]-130,HUB[1]-70,HUB[0]+130,HUB[1]+70),0.8,10)
    d=ImageDraw.Draw(im,'RGBA')
    hx,hy=HUB
    for nm,tt,(x,y),col in SPOKES:
        if t<tt: continue
        b=appear(t,tt,0.14)*a; ex=x+120; ey=y+92 if y<1000 else y
        sx=lerp(hx,ex,0.0); p=expo((t-tt)/0.18)
        d.line([(hx,hy-70),(lerp(hx,ex,p),lerp(hy-70,ey,p))],fill=A(col,0.8*b),width=3)
        flow(d,hx,hy-70,ex,ey,t+tt,col,3,0.8,b,5)
        d.rectangle([x,y,x+240,y+92],outline=A(col,b),width=3); brackets(d,x,y,x+240,y+92,A(col,b),18,5)
        if GL: brackets(GL,x,y,x+240,y+92,A(col,b),18,10)
        ctxt(d,x+120,y+14,nm,f(BEB,66),WHITE,b)
        check(d,x+12,y+30,GREEN,0.7,b)
    d.rounded_rectangle([hx-130,hy-70,hx+130,hy+70],radius=16,outline=A(VGOLD,a),width=4)
    if GL: GL.rounded_rectangle([hx-130,hy-70,hx+130,hy+70],radius=16,outline=A(VGOLD,a),width=10)
    ctxt(d,hx,hy-62,'E2',f(BEB,96),VGOLD,a); ctxt(d,hx,hy+30,'ESTRADIOL',f(MONO,24),CREAM,a)
    if t>=35.74:
        b=appear(t,35.74)*a; x,y=770,880
        arrow(d,x+120,y+96,x+120,y+150,VGOLD,5,b); tag(d,x+40,y+156,'GROWTH ↑',VGOLD,28,b)

# ---------------- 5. split screen: spectrum -> crash, then trend ----------------
GY=968
def spectrum_pos(t):
    if t<39.0: return 0.52
    if t<44.58: return lerp(0.52,0.80,expo((t-39.0)/0.35)) - (0.06*clamp((t-42.4)/1.5) if t>=42.4 else 0)
    return lerp(0.74,0.05,expo((t-44.58)/0.30))
def split_graph(d,t):
    sp=min(ease_io((t-SPLIT[0]-0.15)/0.3),1-ease_io((t-SPLIT[1]+0.1)/0.25))
    if sp<=0: return
    x0,y0,x1,y1=WIN
    d.rounded_rectangle([x0-2,y0-2,x1+2,y1+2],radius=28,outline=A(VGOLD,0.85*sp),width=3); brackets(d,x0-12,y0-12,x1+12,y1+12,A(VGOLD,sp),40,6)
    if GL: brackets(GL,x0-12,y0-12,x1+12,y1+12,A(VGOLD,sp),40,12)
    d.ellipse([x0+22,y0+22,x0+38,y0+38],fill=A(RED,sp if int(t*4)%2==0 else sp/3)); txt(d,x0+48,y0+16,'REC',f(MONO,24),WHITE,sp)
    if t<48.40: spectrum(d,t,sp*(1-clamp((t-48.2)/0.2)))
    else: trend(d,t,sp*appear(t,48.40,0.2))
def spectrum(d,t,a):
    lx0,lx1=90,990; by=GY+70
    k=appear(t,36.90,0.25)*a
    ctxt(d,W/2,GY-14,'E2  ·  LAB REFERENCE RANGE',f(BAR,46),CRIM,k)
    # gradient bar
    n=180;
    for i in range(n):
        u=i/(n-1); c=lerp_col(BLUE,SGREEN,u/0.5) if u<0.5 else lerp_col(SGREEN,AMBER,(u-0.5)/0.5)
        xa=lerp(lx0,lx1,i/n); xb=lerp(lx0,lx1,(i+1)/n)+1
        if (i/n)<=k: d.rectangle([xa,by,xb,by+40],fill=A(c,a))
    if t>=37.62:
        b=appear(t,37.62)*a; rx0=lerp(lx0,lx1,0.30); rx1=lerp(lx0,lx1,0.70)
        for xx in (rx0,rx1): d.line([(xx,by-14),(xx,by+54)],fill=A(WHITE,b),width=3)
        txt(d,rx0+8,by+46,'REF',f(MONO,22),WHITE,b)
    if t>=37.34:
        mx=lerp(lx0,lx1,spectrum_pos(t)); b=appear(t,37.34)*a
        d.polygon([(mx-20,by-40),(mx+20,by-40),(mx,by-6)],fill=A(CREAM,b))
        if GL: GL.polygon([(mx-24,by-44),(mx+24,by-44),(mx,by-2)],fill=A(CREAM,0.6*b))
    # boxes
    boxes=[('TOO LOW',BLUE,90),('DIALED IN',SGREEN,390),('HIGH',AMBER,690)]
    pos=spectrum_pos(t) if t>=37.34 else 0.5
    state=0 if pos<0.3 else (1 if pos<0.7 else 2)
    alert = 41.20<=t<44.58
    for i,(nm,col,bx) in enumerate(boxes):
        b=appear(t,37.0+i*0.08)*a; on=(i==state and t>=37.34)
        c=col if not (alert and i==2) else RED
        d.rounded_rectangle([bx,by+80,bx+280,by+200],radius=14,fill=A((29,29,33),0.92*b),outline=A(c,b if on else 0.25*b),width=4 if on else 2)
        if on and GL: GL.rounded_rectangle([bx,by+80,bx+280,by+200],radius=14,outline=A(c,b),width=10)
        txt(d,bx+20,by+88,nm,f(BAR,56),c if on else lerp_col(c,(60,60,66),0.55),b)
    if alert:
        bl=a*(1 if int((t-41.2)*5)%2==0 else 0.35); tag(d,710,by+148,'RED ALERT',RED,24,bl)
    if 42.30<=t<44.70:
        for j,tt in enumerate([42.40,42.84,43.20,43.62]):
            if t>=tt:
                b=appear(t,tt,0.1)*a*(1-clamp((t-44.5)/0.2)); x=lerp(1080,912,expo((t-tt)/0.14)); y=GY-420+j*84
                d.rounded_rectangle([x,y-60,x+84,y-12],radius=24,fill=A(RED,b)); ctxt(d,x+42,y-58,'AI',f(BEB,44),WHITE,b)
                if GL: GL.rounded_rectangle([x-3,y-63,x+87,y-9],radius=26,outline=A(RED,b),width=8)
                if j==3: ctxt(d,954,y,'×4',f(MONOB,34),RED,b)
    if t>=44.58:
        b=appear(t,44.70)*a; tag(d,110,by+152,'CRASHED',BLUE,24,b)
    if t>=46.18: tag(d,390,by+216,'FLAT',BLUE,26,appear(t,46.18)*a)
    if t>=47.10: tag(d,390+tagw(d,'FLAT',26)+12,by+216,'LIBIDO ✕',RED,26,appear(t,47.10)*a)
TV=[0.25,0.45,0.32,0.86,0.40,0.48]
def trend(d,t,a):
    lx0,lx1,gy0,gy1=120,960,GY+70,GY+250
    ctxt(d,W/2,GY-14,'E2  ·  OVER TIME',f(BAR,46),VGOLD,a)
    d.line([(lx0,gy1),(lx1,gy1)],fill=A((90,94,110),a),width=2)
    ry0=lerp(gy1,gy0,0.68); ry1=lerp(gy1,gy0,0.16)
    d.rectangle([lx0,ry0,lx1,ry1],fill=A((30,80,50),0.13*a)); dashed_rect(d,lx0,ry0,lx1,ry1,SGREEN,0.5*a,10,2); txt(d,lx1-110,ry0+4,'RANGE',f(MONO,20),SGREEN,a)
    pts=[(lerp(lx0+30,lx1-30,i/5),lerp(gy1,gy0,v)) for i,v in enumerate(TV)]
    # single reading first (one number)
    single=pts[3]
    if t<52.38:
        b=appear(t,48.56)*a; d.ellipse([single[0]-12,single[1]-12,single[0]+12,single[1]+12],fill=A(WHITE,b))
        r=18+8*(0.5+0.5*math.sin(t*6)); d.ellipse([single[0]-r,single[1]-r,single[0]+r,single[1]+r],outline=A(RED,b),width=3)
        if t>=48.80: tag(d,single[0]-tagw(d,'1 HIGH NUMBER',26)-34,single[1]-24,'1 HIGH NUMBER',RED,26,appear(t,48.80)*a)
        if t>=50.78: tag(d,single[0]-tagw(d,'≠ REASON FOR AN AI',26)-34,single[1]+26,'≠ REASON FOR AN AI',RED,26,appear(t,50.78)*a)
    else:
        p=clamp((t-52.38)/1.0)*5
        for i in range(5):
            if p>i:
                q=min(1,p-i); a_=pts[i]; b_=pts[i+1]; e=(lerp(a_[0],b_[0],q),lerp(a_[1],b_[1],q))
                d.line([a_,e],fill=A(CYAN,a),width=6)
                if GL: GL.line([a_,e],fill=A(CYAN,a),width=12)
        for i,pt in enumerate(pts):
            if p>=i-0.01: d.ellipse([pt[0]-10,pt[1]-10,pt[0]+10,pt[1]+10],fill=A(WHITE,a))
        if t>=52.62: tag(d,lx0,GY+40,'TREND · 6 PANELS',CYAN,26,appear(t,52.62)*a)
    if t>=54.62:
        b=appear(t,54.62)*a; x=lx0
        for j,nm in enumerate(['HCT','LIPIDS','TOTAL T','SHBG']):
            bb=appear(t,54.62+j*0.1)*a; x=tag(d,x,GY+268,nm,(50,54,70),24,bb,glow=False)+10
        check(d,x+6,GY+272,GREEN,0.8,b)
    if t>=55.88:
        b=appear(t,55.88)*a; tag(d,700,GY+268,'HOW YOU FEEL ✓',GREEN,24,b)

# ---------------- 6. hematocrit gauge + EPO loop (full panel) ----------------
def scene_hct(d,t):
    cx,cy,r=540,880,220
    lo,hi=35,60
    def ang(v): return math.pi+math.pi*(v-lo)/(hi-lo)
    # arcs
    for v0,v1,col in [(35,50,(70,90,110)),(50,60,RED)]:
        d.arc([cx-r,cy-r,cx+r,cy+r],math.degrees(ang(v0)),math.degrees(ang(v1)),fill=A(col,1),width=34)
        if col==RED and GL: GL.arc([cx-r,cy-r,cx+r,cy+r],math.degrees(ang(v0)),math.degrees(ang(v1)),fill=A(RED,0.8),width=44)
    for v in (40,45,50,55):
        a_=ang(v); d.line([(cx+(r-48)*math.cos(a_),cy+(r-48)*math.sin(a_)),(cx+(r-30)*math.cos(a_),cy+(r-30)*math.sin(a_))],fill=A(WHITE,0.7),width=3)
        ctxt(d,cx+(r-80)*math.cos(a_),cy+(r-80)*math.sin(a_)-14,str(v),f(MONO,22),MUTED)
    txt(d,cx-r-130,cy+60,'HCT %',f(MONO,26),CREAM)
    val=lerp(42,52,expo((t-63.62)/0.45)) if t>=63.62 else 42
    a_=ang(val); nx,ny=cx+(r-20)*math.cos(a_),cy+(r-20)*math.sin(a_)
    d.line([(cx,cy),(nx,ny)],fill=A(WHITE,1),width=7); d.ellipse([cx-16,cy-16,cx+16,cy+16],fill=A(WHITE,1))
    if GL: GL.line([(cx,cy),(nx,ny)],fill=A(WHITE,0.6),width=12)
    fn=f(BEB,130); s=f'{int(round(val))}%'; ctxt(d,cx,cy+28,s,fn,RED if val>=50 else WHITE)
    if GL and val>=50: GL.text((cx-d.textlength(s,font=fn)/2,cy+28),s,font=fn,fill=A(RED,0.6))
    if t>=65.68:
        b=appear(t,65.68); tag(d,cx+170,cy-r-30,'DANGER ZONE',RED,28,b)
    # loop
    if t>=66.70:
        ly=1100
        nodes=[('ANDROGENS',66.70,110),('EPO',67.34,375),('RBC',68.76,600),('DONATE',69.64,800)]
        for i,(nm,tt,x) in enumerate(nodes):
            if t<tt: continue
            b=appear(t,tt); fn=f(BEB,48); tw=d.textlength(nm,font=fn); col=RED if nm=='DONATE' else (VGOLD if i==0 else CYAN)
            ex_=36 if nm in ('EPO','RBC') else 0
            d.rounded_rectangle([x,ly,x+tw+36+ex_,ly+68],radius=12,fill=A((10,14,24),0.95*b),outline=A(col,b),width=4)
            if GL: GL.rounded_rectangle([x,ly,x+tw+36+ex_,ly+68],radius=12,outline=A(col,b),width=8)
            txt(d,x+18,ly+8,nm,fn,WHITE,b)
            if nm in ('EPO','RBC'): d.polygon([(x+tw+20,ly+26),(x+tw+44,ly+26),(x+tw+32,ly+10)],fill=A(col,b)); d.rectangle([x+tw+28,ly+26,x+tw+36,ly+52],fill=A(col,b))
            if i>0:
                px=nodes[i-1][2]+d.textlength(nodes[i-1][0],font=fn)+36+(36 if nodes[i-1][0] in ('EPO','RBC') else 0); arrow(d,px+4,ly+34,x-6,ly+34,col,4,b,14); flow(d,px+4,ly+34,x-6,ly+34,t,col,2,1.2,b,5)
        if t>=69.96:
            b=appear(t,69.96)
            # loop back DONATE -> RBC
            d.line([(880,ly+70),(880,ly+108),(660,ly+108)],fill=A(RED,b),width=4); arrow(d,660,ly+108,660,ly+74,RED,4,b,14)
            txt(d,694,ly+114,'EVERY FEW WEEKS',f(MONO,22),RED,b)
        if t>=71.04:
            b=appear(t,71.04); fr=lerp(0.85,0.12,expo((t-71.24)/0.9)) if t>=71.24 else 0.85
            meter(d,110,ly+140,620,ly+170,fr,RED if fr<0.4 else VGOLD,'FERRITIN','DRAINING' if t>=72.02 else '',b)

# ---------------- 7. push-aside ladder card ----------------
def ladder(im,t):
    if not (PUSH[0]+0.05<=t<PUSH[1]+0.28): return
    a=min(expo((t-PUSH[0]-0.08)/0.26),1-ease_io((t-PUSH[1])/0.24)); dx=lerp(-80,0,a)
    x0,y0,x1,y1=36+dx,500,600+dx,1260
    frosted(im,(x0,y0,x1,y1),0.9,10); d=ImageDraw.Draw(im,'RGBA')
    d.rectangle([x0,y0,x0+6,y1],fill=A(VGOLD,a)); brackets(d,x0,y0,x1,y1,A(VGOLD,a),30,6)
    if GL: brackets(GL,x0,y0,x1,y1,A(VGOLD,a),30,12)
    txt(d,x0+30,y0+20,'HIGH HCT · FIX ORDER',f(MONO,26),VGOLD,a)
    rungs=[('HYDRATION',72.66,GREEN),('DOSE ADJUSTMENT',73.30,GREEN),('CARDIO',74.06,GREEN),('BLOOD DONATION',77.72,RED)]
    for i,(nm,tt,col) in enumerate(rungs):
        y=y0+76+i*112+(30 if i==3 else 0)
        if t<tt:
            d.rectangle([x0+30,y,x1-30,y+86],outline=A((50,54,70),a),width=2); continue
        b=appear(t,tt,0.14)*a; xs=lerp(x0-40,x0+30,expo((t-tt)/0.16))
        d.rectangle([xs,y,x1-30,y+86],fill=A((12,16,26),0.95*b),outline=A(col,b),width=3)
        ctxt(d,xs+44,y+12,f'0{i+1}',f(BEB,60),col,b); txt(d,xs+92,y+16,nm,f(BEB,56),WHITE,b)
        if i<3: check(d,x1-80,y+28,GREEN,0.9,b)
    if t>=75.66:
        b=appear(t,75.66)*a; d.line([(x1-16,y0+76),(x1-6,y0+76),(x1-6,y0+76+3*112-26),(x1-16,y0+76+3*112-26)],fill=A(GREEN,b),width=4)
        tag(d,x0+30,y0+76+3*112-12,'FIRST',GREEN,24,b)
    if t>=77.72: tag(d,x1-30-tagw(d,'LAST RESORT',24),y0+76+3*112+30+92,'LAST RESORT',RED,24,appear(t,78.04)*a)
    if t>=78.60:
        b=appear(t,78.60)*a; yy=y0+640
        txt(d,x0+30,yy-36,'12 MONTHS',f(MONO,22),CREAM,b)
        for m in range(12):
            cx=x0+30+m*42; d.rectangle([cx,yy,cx+34,yy+40],outline=A((70,74,90),b),width=2)
            if m%3==2 and t>=79.30: drop(d,cx+17,yy+12,9,RED,appear(t,79.30+m*0.02)*a)
        if t>=79.90:
            c=appear(t,79.90,0.12)*a; d.line([(x0+24,yy+20),(lerp(x0+24,x0+30+12*42,c),yy+20)],fill=A(RED,c),width=6)
            if GL: GL.line([(x0+24,yy+20),(lerp(x0+24,x0+30+12*42,c),yy+20)],fill=A(RED,c),width=12)

# ---------------- 8. roadmap route (full panel) ----------------
PINS=[('PANEL',82.36,(170,1100)),('TREND',84.66,(420,880)),('SYMPTOMS',84.90,(660,1080)),('DECIDE',85.30,(890,860))]
def route_pts():
    pts=[]
    c=[(140,1180),(170,1100),(300,860),(420,880),(560,920),(620,1100),(660,1080),(760,1040),(820,860),(890,860)]
    for i in range(len(c)-1):
        for k in range(12): pts.append((lerp(c[i][0],c[i+1][0],k/12),lerp(c[i][1],c[i+1][1],k/12)))
    pts.append(c[-1]); return pts
RP=route_pts()
def scene_road(d,t):
    txt(d,110,560,'BEFORE YOU TOUCH ANYTHING',f(MONO,28),VGOLD)
    for i in range(len(RP)-1): d.line([RP[i],RP[i+1]],fill=A((50,54,70),1),width=14)
    prog=0.06 if t<82.36 else (0.18 if t<84.66 else lerp(0.18,1.0,expo((t-84.66)/0.9)))
    n=int(prog*(len(RP)-1))
    for i in range(n): d.line([RP[i],RP[i+1]],fill=A(VGOLD,1),width=10)
    if GL and n>0: GL.line(RP[:n+1],fill=A(VGOLD,0.9),width=18)
    for nm,tt,(x,y) in PINS:
        on=t>=tt; col=GREEN if (nm=='PANEL' and on) else (VGOLD if on else (80,84,100))
        d.ellipse([x-22,y-22,x+22,y+22],fill=A(INK,1),outline=A(col,1),width=6)
        if on and GL: GL.ellipse([x-30,y-30,x+30,y+30],outline=A(col,1),width=10)
        fn=f(BEB,46); ctxt(d,x,y+34 if y>1000 else y-84,nm,fn,WHITE if on else (110,110,120))
    if t>=82.36: check(d,152,1086,GREEN,0.9,appear(t,82.36))
    if t>=83.42:
        b=appear(t,83.42); x=110
        for nm in ['AI','DOSE','DONATE']:
            lock(d,x,640,RED,b,0.8); txt(d,x+40,640,nm,f(BEB,44),WHITE,b); x+=40+d.textlength(nm,font=f(BEB,44))+40
        tag(d,x,642,'LOCKED UNTIL PANEL',RED,24,b)
    if t>=85.84:
        b=appear(t,85.84,0.12); x,y=890,860; r=30+40*b
        d.ellipse([x-r,y-r,x+r,y+r],outline=A(VGOLD,1-b*0.6),width=4)

SCENES=[ (15.70,24.90,scene_bars,'BASELINE BLOODWORK','EVIDENCE 01'),
         (63.30,72.42,scene_hct,'HEMATOCRIT','EVIDENCE 03'),
         (80.56,86.15,scene_road,'BLOODWORK','THE ROADMAP')]
def active_scene(t):
    for sc in SCENES:
        if sc[0]<=t<sc[1]+0.16: return sc
    return None

# ---------------- 9. CTA end card ----------------
LOGO=None
def cta(im,t):
    if t<86.20: return
    global LOGO
    a=appear(t,86.24,0.22); y=lerp(1110,1010,a)
    frosted(im,(56,y,1024,y+300),0.84,16); d=ImageDraw.Draw(im,'RGBA')
    brackets(d,56,y,1024,y+300,A(VGOLD,a),30,5); d.rectangle([56,y,62,y+300],fill=A(VGOLD,a))
    if GL: brackets(GL,56,y,1024,y+300,A(VGOLD,a),30,10)
    if LOGO is None:
        lg=Image.open(B+'logo.jpg').convert('RGB'); s=min(lg.size); lg=lg.crop(((lg.width-s)//2,(lg.height-s)//2,(lg.width+s)//2,(lg.height+s)//2)).resize((170,170),Image.LANCZOS)
        m=Image.new('L',(170,170),0); ImageDraw.Draw(m).ellipse([0,0,169,169],fill=255); lg.putalpha(m); LOGO=lg
    lg=LOGO.copy(); lg.putalpha(lg.split()[3].point(lambda v:int(v*a))); im.alpha_composite(lg,(84,int(y)+26))
    d=ImageDraw.Draw(im,'RGBA')
    txt(d,280,y+26,'THE EXACT LABS I RUN',f(MONO,26),VGOLD,a)
    if t>=87.36:
        b=expo((t-87.36)/0.12); s=lerp(1.15,1.0,b)
        fn=f(BEB,int(86*s)); label='COMMENT  "ROADMAP"'; tw=d.textlength(label,font=fn)
        lit_bar(d,280,y+70,280+tw+40,y+70+int(100*s),VGOLD,b); d.text((300,y+76),label,font=fn,fill=A(INK,b))
        if GL: GL.rectangle([276,y+66,284+tw+40,y+74+int(100*s)],outline=A(VGOLD,b),width=12)
    x=280
    for nm,tt in [('BEFORE',91.78),('DURING',92.53),('AFTER',93.26)]:
        if t>=tt:
            b=appear(t,tt); check(d,x,y+196,GREEN,0.8,b); txt(d,x+34,y+192,nm,f(MONO,28),WHITE,b)
        x+=200
    txt(d,84,y+258,'FOR RESEARCH & EDUCATIONAL PURPOSES ONLY',f(MONO,20),(124,124,130),a)
    txt(d,820,y+258,'@coach.agz',f(MONO,22),GOLD,a)

# ---------------- captions (saved style: red lit active-word block) ----------------
FIX={'their':"THEY'RE",'ais':'AIs','e2':'E2'}
def merged_words():
    out=[]
    for w in WORDS:
        if out and (w['w'].startswith('-') or w['w'] in ('%',)):
            out[-1]=dict(out[-1]); out[-1]['w']=out[-1]['w']+w['w']; out[-1]['e']=w['e']; continue
        out.append(dict(w))
    return out
WORDS=merged_words()
def build_groups():
    G=[];cur=[]
    for i,x in enumerate(WORDS):
        if cur:
            prev=WORDS[cur[-1]]
            if len(cur)>=3 or x['s']-prev['e']>0.28 or prev['w'][-1] in '.,?!' or any(prev['e']-0.02<=c<=x['s']+0.02 for c in CUTS): G.append(cur); cur=[]
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
    def fx(w):
        k=w.lower().strip('.,?!')
        return "THEY'RE" if k=='their' else w.upper().rstrip(',.?!')
    ws=[fx(WORDS[i]['w']) for i in g]
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
IMPACTS=[27.94,63.62+0.45,79.90]   # 2-frame camera shake on heavy hits
def frame(src,t):
    base,sp,pp=footage(src,t)
    sc=active_scene(t); g=0
    if sc: g=min(ease_io((t-sc[0]+0.05)/0.30),1-ease_io((t-sc[1])/0.22))
    bg_=bumper_push(t); g=max(g,bg_*0.85)
    if 29.62<=t<36.4: g=max(g,0.25*win(t,29.62,36.2,0.3,0.2))
    bg=base
    if g>0: bg=Image.blend(base.filter(ImageFilter.GaussianBlur(18*g)),Image.new('RGB',(W,H),(5,8,16)),0.70*g)
    im=bg.convert('RGBA')
    yy=np.arange(H); a=np.where(yy>1180,np.clip((yy-1180)/260,0,1)*110,0); a=np.maximum(a,np.where(yy<420,(1-yy/420)*120,0)); scr=(a*(1-g)).astype(np.uint8)
    im.alpha_composite(Image.merge('RGBA',[Image.new('L',(W,H),c) for c in NAVY]+[Image.fromarray(np.repeat(scr[:,None],W,1))]))
    global GL
    glow=Image.new('RGBA',(W,H),(0,0,0,0)); GL=ImageDraw.Draw(glow,'RGBA')
    year_card(im,t)
    hub(im,t)
    if sp>0: split_graph(ImageDraw.Draw(im,'RGBA'),t)
    ladder(im,t)
    if sc:
        pin=expo((t-sc[0])/0.20); pout=clamp((t-sc[1])/0.16)
        if pout<1:
            s=lerp(1.05,1.0,pin)*lerp(1.0,1.03,pout); w=(P[2]-P[0])*s; h=(P[3]-P[1])*s; cx=(P[0]+P[2])/2; cy=(P[1]+P[3])/2
            x0,y0,x1,y1=cx-w/2,cy-h/2,cx+w/2,cy+h/2
            frosted(im,(x0,y0,x1,y1),0.92,8)
            lay=Image.new('RGBA',(W,H),(0,0,0,0)); d=ImageDraw.Draw(lay,'RGBA')
            sc[2](d,t)
            if pin<1: lay=lay.filter(ImageFilter.GaussianBlur(8*(1-pin)))
            al=pin*(1-pout); lay.putalpha(lay.split()[3].point(lambda v:int(v*al)))
            im.alpha_composite(lay); panel_frame(ImageDraw.Draw(im,'RGBA'),x0,y0,x1,y1,al,sc[3],sc[4],VGOLD,t)
    bumper(im,t)
    cta(im,t)
    GL=None
    if glow.getbbox():
        sm=glow.resize((W//4,H//4),Image.BILINEAR)
        g1=np.asarray(sm.filter(ImageFilter.GaussianBlur(3.5))).astype(np.float32)/255; g2=np.asarray(sm.filter(ImageFilter.GaussianBlur(10))).astype(np.float32)/255
        prem=np.clip(g1[...,:3]*g1[...,3:]*2.3+g2[...,:3]*g2[...,3:]*1.8,0,1)
        prem=np.asarray(Image.fromarray((prem*255).astype(np.uint8)).resize((W,H),Image.BILINEAR)).astype(np.float32)/255
        b=np.asarray(im.convert('RGB')).astype(np.float32)/255
        im=Image.fromarray(((1-(1-b)*(1-prem))*255).astype(np.uint8)).convert('RGBA')
    d=ImageDraw.Draw(im,'RGBA'); d.rectangle([0,0,7,H],fill=GOLD)
    band(im,t)
    text_hook(im,t)
    captions(im,t)
    out=im.convert('RGB')
    for ti in IMPACTS:
        k=round((t-ti)*FPS)
        if k in (0,1):
            dx=[9,-5][k]; z=1.025; big=out.resize((int(W*z),int(H*z)),Image.BICUBIC); ox=(big.width-W)//2-dx; oy=(big.height-H)//2
            out=big.crop((ox,oy,ox+W,oy+H)); ImageDraw.Draw(out).rectangle([0,0,7,H],fill=GOLD)
    return out
if __name__=='__main__':
    mode=sys.argv[2]
    if mode=='stills':
        import os; os.makedirs(B+'qc',exist_ok=True)
        for tt in [float(x) for x in sys.argv[3:]]:
            subprocess.run(['ffmpeg','-v','error','-y','-ss',str(tt),'-i',B+'assembled.mov','-frames:v','1',B+'qc/_src.png'])
            frame(Image.open(B+'qc/_src.png').convert('RGB'),tt).resize((540,960)).save(B+f'qc/st_{tt:06.2f}.jpg',quality=85)
        sys.exit()
    n0,n1=int(sys.argv[3]),int(sys.argv[4]); out=sys.argv[5]
    dec=subprocess.Popen(['ffmpeg','-v','error','-ss',f'{n0/FPS:.4f}','-i',B+'assembled.mov','-frames:v',str(n1-n0),'-f','rawvideo','-pix_fmt','rgb24','-'],stdout=subprocess.PIPE)
    enc=subprocess.Popen(['ffmpeg','-v','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-','-c:v','libx264','-crf','17','-preset','medium','-pix_fmt','yuv420p',out],stdin=subprocess.PIPE)
    for n in range(n0,n1):
        buf=dec.stdout.read(W*H*3)
        if len(buf)<W*H*3: print('short',n); break
        enc.stdin.write(frame(Image.frombuffer('RGB',(W,H),buf),n/FPS).tobytes())
    enc.stdin.close(); enc.wait(); dec.kill(); print('done',n0,n1)
