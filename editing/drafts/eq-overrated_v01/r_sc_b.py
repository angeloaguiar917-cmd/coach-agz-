# Scenes B: lab sheet, washout calendar, ancillary stack, responder verdict, CTA.
import math, numpy as np
from PIL import Image, ImageDraw, ImageFilter
import r_core as C
from r_core import (W,H,f,A,txt,stxt,tag,check,cross,arrow,brackets,litbar,line,
                    shade,frosted,clamp,expo,ease,land,lerp,ap,win,
                    BEB,BAR,DMR,DMB,MONO,GOLD,CREAM,NAVY,MUTED,RED,VGOLD,CYAN,GREEN,AMBER,DEEP,INK,WHITE)

# 6 · lab sheet slides in beside the footage; wk4-6 in range, wk10 crashes, stamp lands
_SHEET=None
def _mk_sheet():
    im=Image.new('RGBA',(560,470),(246,244,238,255)); d=ImageDraw.Draw(im)
    d.rectangle([0,0,560,64],fill=(210,10,20)); d.text((20,16),'HORMONE PANEL · E2 SENSITIVE',font=f(MONO,22),fill=WHITE)
    d.text((20,78),'DRAW',font=f(MONO,20),fill=(120,120,128)); d.text((150,78),'RANGE   LOW · · · · · HIGH',font=f(MONO,20),fill=(120,120,128))
    for i in range(5): d.line([(16,106+i*86),(544,106+i*86)],fill=(214,212,206),width=2)
    return im
def _row(d,i,label,mk,col,a,flag=None):
    y=106+i*86; d.text((20,y+24),label,font=f(BAR,36),fill=A((30,32,40),a))
    bx0,bx1=150,420; by=y+42; d.rectangle([bx0,by-6,bx1,by+6],fill=A((225,223,216),a))
    d.rectangle([lerp(bx0,bx1,0.35),by-6,lerp(bx0,bx1,0.7),by+6],fill=A((150,210,165),a))
    mx=lerp(bx0,bx1,mk); d.polygon([(mx,by-10),(mx-11,by-28),(mx+11,by-28)],fill=A(col,a)); d.rectangle([mx-2,by-10,mx+2,by+10],fill=A(col,a))
    if flag: d.text((436,y+20),flag,font=f(BEB,44),fill=A(col,a))
def s_lab(im,t,k):
    global _SHEET
    if k<=0 or t<41.40: return
    if _SHEET is None: _SHEET=_mk_sheet()
    p=expo((t-41.40)/0.3); sa=k*p; sh=_SHEET.copy(); d=ImageDraw.Draw(sh,'RGBA')
    for i,(lab,tt) in enumerate([('WK 4',43.96),('WK 5',44.72),('WK 6',45.40)]):
        if t>=tt:
            ra=ap(t,tt,0.12); _row(d,i,lab,0.52+0.04*(i%2),(20,150,70),ra); check(d,470,106+i*86+24,(20,150,70),1.0,ra)
    if t>=48.26:
        ra=ap(t,48.26,0.15); mk=0.55 if t<50.30 else lerp(0.55,0.05,expo((t-50.30)/0.35)); crashed=t>=50.60
        _row(d,3,'WK 10',mk,(210,10,20) if crashed else (60,60,70),ra,'LOW' if crashed else None)
        d.text((20,106+3*86+58),'STEADY STATE',font=f(MONO,16),fill=A((120,120,128),ra))
    rot=lerp(-9,-3.5,p)+(lerp(-1.6,0,expo((t-50.78)/0.25)) if t>=50.78 else 0)
    shr=sh.rotate(rot,resample=Image.BICUBIC,expand=True); x=lerp(-620,38,p); y=250
    shd=Image.new('RGBA',shr.size,(0,0,0,0)); shd.putalpha(shr.split()[3].point(lambda q:int(q*0.55*sa)))
    im.alpha_composite(shd.filter(ImageFilter.GaussianBlur(18)),(int(x+14),int(y+22)))
    shr.putalpha(shr.split()[3].point(lambda q:int(q*sa))); im.alpha_composite(shr,(int(x),int(y)))
    d=ImageDraw.Draw(im,'RGBA')
    if 46.50<=t<48.26:
        ga=ap(t,46.50)*sa; brackets(d,x+20,y+108,x+556,y+378,GREEN,28,5,ga)
        if C.GL: brackets(C.GL,x+20,y+108,x+556,y+378,GREEN,28,10,ga)
    if t>=50.78:
        sp=expo((t-50.78)/0.12); s=lerp(1.6,1.0,sp)
        st=Image.new('RGBA',(430,130),(0,0,0,0)); sd=ImageDraw.Draw(st)
        sd.rounded_rectangle([4,4,426,126],radius=12,outline=(255,34,28,255),width=8); sd.text((215,64),'CRASHED',font=f(BEB,100),fill=(255,34,28,255),anchor='mm')
        st=st.resize((int(430*s),int(130*s)),Image.BICUBIC).rotate(8,expand=True,resample=Image.BICUBIC)
        st.putalpha(st.split()[3].point(lambda q:int(q*sp*sa*0.95))); im.alpha_composite(st,(int(338-st.width/2),int(690-st.height/2)))
        if C.GL: C.GL.rounded_rectangle([120,625,530,760],radius=12,outline=A(RED,sp*sa),width=12)

# 7 · washout calendar: weeks fill red, 10/12/16 marked, padlock STUCK (top band)
def s_washout(im,d,t):
    a=win(t,55.66,62.25,0.18,0.18)
    if a<=0: return
    dy=-280*clamp((t-62.25)/0.18)**2; shade(im,(30,226+dy,1050,540+dy),0.66*a,50); d=ImageDraw.Draw(im,'RGBA')
    txt(d,70,240+dy,'CLEARANCE · WEEKS',f(MONO,24),VGOLD,a)
    if t>=56.32:
        la=ap(t,56.32,0.12)*a; lx,ly=880,232+dy
        d.arc([lx+8,ly-4,lx+40,ly+30],180,360,fill=A(RED,la),width=5); d.rounded_rectangle([lx,ly+12,lx+48,ly+44],radius=5,fill=A(RED,la)); tag(d,lx-128,ly+2,'STUCK',RED,22,la)
    cw,ch,gap=106,86,10; x0=70; y0=296+dy; marks={10:59.14,12:59.68,16:60.12}
    fill_n=0 if t<56.88 else int(clamp((t-56.88)/3.3)*16+0.001)
    for i in range(16):
        r,c=divmod(i,8); x=x0+c*(cw+gap); y=y0+r*(ch+gap); wk=i+1; filled=i<fill_n; ca=ap(t,56.88+i*0.2,0.1) if filled else 0
        d.rectangle([x,y,x+cw,y+ch],fill=A((40,10,14) if filled else (16,18,26),a*0.9),outline=A((70,74,90),a),width=2)
        if filled: d.rectangle([x+4,y+ch-10,x+4+(cw-8)*ca,y+ch-4],fill=A(RED,a))
        m=wk in marks and t>=marks[wk]; col=VGOLD if m else (110,114,130)
        if m and wk==16: col=RED
        txt(d,x+cw/2,y+ch/2-4,str(wk),f(BEB if m else MONO,52 if m else 26),col,a,'mm')
        if m:
            ma=ap(t,marks[wk],0.12); d.rectangle([x-2,y-2,x+cw+2,y+ch+2],outline=A(col,a*ma),width=4)
            if C.GL: C.GL.rectangle([x-4,y-4,x+cw+4,y+ch+4],outline=A(col,a*ma),width=10)

# 8 · ancillary stack: bottles pile up to manage E2 (left column)
def _bottle(d,x,y,w,h,label,a):
    d.rounded_rectangle([x+w*0.22,y,x+w*0.78,y+h*0.2],radius=6,fill=A((30,34,44),a),outline=A(WHITE,a*0.6),width=2)
    d.rounded_rectangle([x,y+h*0.18,x+w,y+h],radius=16,fill=A((150,82,20),a*0.92),outline=A((255,190,110),a),width=3)
    d.rectangle([x+10,y+h*0.36,x+w-10,y+h*0.84],fill=A((246,244,238),a)); d.rectangle([x+10,y+h*0.36,x+w-10,y+h*0.46],fill=A((210,10,20),a))
    txt(d,x+w/2,y+h*0.64,label,f(BAR,34),INK,a,'mm')
def s_stack(im,d,t):
    a=win(t,63.30,67.60,0.12,0.18)
    if a<=0: return
    shade(im,(20,620,420,1320),0.55*a,60); d=ImageDraw.Draw(im,'RGBA')
    items=[('ANCILLARY',63.50),('Rx',64.54),('COMPOUND',65.52)]; bw,bh=250,150; x=90; base=1280
    for i,(lab,tt) in enumerate(items):
        if t<tt-0.18: continue
        p=land((t-(tt-0.18))/0.24); y=lerp(560,base-(i+1)*(bh+4),p); _bottle(d,x+(i%2)*14-7,y,bw,bh,lab,a)
    if t>=66.64:
        ea=ap(t,66.64,0.14)*a; stxt(d,60,660,'JUST TO CONTROL',f(MONO,22),MUTED,ea); tag(d,310,648,'E2',CYAN,30,ea)
        brackets(d,70,base-3*154-16,370,base-6,CYAN,26,5,ea)
        if C.GL: brackets(C.GL,70,base-3*154-16,370,base-6,CYAN,26,10,ea)

# 9 · responder vs non-responder, full-cycle progress, verdict bar (top band)
def s_verdict(im,d,t):
    a=win(t,67.66,74.55,0.18,0.16)
    if a<=0: return
    shade(im,(30,228,1050,640),0.66*a,50); d=ImageDraw.Draw(im,'RGBA')
    unknown=t>=69.82
    for j,(lab,col,tt) in enumerate([('RESPONDER',GREEN,67.94),('NON-RESPONDER',RED,68.40)]):
        x0=70+j*480; x1=x0+460; y0,y1=248,448; ca=ap(t,tt,0.14)*a
        if ca<=0: continue
        lit_on=(not unknown) and j==0 and t>=68.20; dim=0.35 if unknown else 1
        d.rounded_rectangle([x0,y0,x1,y1],radius=16,fill=A((12,14,20),0.85*ca),outline=A(col,ca*dim),width=6 if lit_on else 4)
        if C.GL and lit_on: C.GL.rounded_rectangle([x0,y0,x1,y1],radius=16,outline=A(col,ca),width=12)
        fx=x0+90; fy=y0+58; d.ellipse([fx-30,fy-30,fx+30,fy+30],fill=A((90,94,110),ca*dim)); d.chord([fx-62,fy+36,fx+62,fy+150],180,360,fill=A((90,94,110),ca*dim))
        txt(d,x0+172,y0+44,lab,f(BAR,38),WHITE,ca*dim)
        if j==0: check(d,x0+178,y0+108,GREEN,1.3,ca*dim)
        else: cross(d,x0+182,y0+110,RED,1.2,ca*dim)
    if unknown:
        qa=ap(t,69.82,0.12)*a; s=lerp(1.4,1.0,expo((t-69.82)/0.14))
        d.ellipse([540-56*s,348-56*s,540+56*s,348+56*s],fill=A(VGOLD,qa))
        if C.GL: C.GL.ellipse([540-60*s,348-60*s,540+60*s,348+60*s],outline=A(VGOLD,qa),width=12)
        txt(d,540,352,'?',f(BEB,int(96*s)),INK,qa,'mm')
    if t>=71.02:
        pa=ap(t,71.02)*a; fr=clamp((t-71.02)/2.15); txt(d,70,472,'FULL CYCLE',f(MONO,22),CREAM,pa)
        d.rectangle([250,476,1010,500],outline=A((90,94,110),pa),width=2); litbar(d,253,479,253+754*fr,497,VGOLD,pa)
        if C.GL: C.GL.rectangle([253,479,253+754*fr,497],fill=A(VGOLD,pa*0.6))
        if fr>=0.999: txt(d,1016,462,'',f(MONO,20),VGOLD,pa)
    if t>=73.70:
        va=expo((t-73.70)/0.16)*a; d.rounded_rectangle([250,520,1010,600],radius=12,fill=A((40,8,8),0.9*va),outline=A(RED,va),width=4)
        txt(d,270,536,"THAT'S THE PROBLEM",f(BEB,56),WHITE,va)
        if C.GL: C.GL.rounded_rectangle([250,520,1010,600],radius=12,outline=A(RED,va),width=10)

# 10 · CTA end card (compact, below the face)
_LOGO=None
def s_cta(im,t):
    global _LOGO
    if t<74.90: return
    a=ap(t,74.98,0.2); y=1300
    frosted(im,(56,y,1024,y+360),0.82,16); d=ImageDraw.Draw(im,'RGBA'); brackets(d,56,y,1024,y+360,VGOLD,30,5,a)
    if C.GL: brackets(C.GL,56,y,1024,y+360,VGOLD,30,10,a)
    if _LOGO is None:
        lg=Image.open(C.WD+'/logo.jpg').convert('RGB'); s=min(lg.size)
        lg=lg.crop(((lg.width-s)//2,(lg.height-s)//2,(lg.width+s)//2,(lg.height+s)//2)).resize((150,150),Image.LANCZOS)
        m=Image.new('L',(150,150),0); ImageDraw.Draw(m).ellipse([0,0,149,149],fill=255); lg.putalpha(m); _LOGO=lg
    lg=_LOGO.copy(); lg.putalpha(lg.split()[3].point(lambda v:int(v*a))); im.alpha_composite(lg,(90,y+28)); d=ImageDraw.Draw(im,'RGBA')
    txt(d,266,y+36,'FREE · @COACH.AGZ',f(MONO,24),VGOLD,a); txt(d,266,y+70,'EQ PROTOCOL + BIOMARKERS',f(BAR,46),CREAM,a)
    if t>=80.16:
        ra=ap(t,80.16,0.14); txt(d,266,y+128,'lean mass · biomarkers · side-effect checklist',f(DMR,26),MUTED,ra)
    b=expo((t-75.46)/0.14) if t>=75.46 else 0
    if b>0:
        s=lerp(1.12,1.0,b); fn=f(BEB,int(84*s)); label='COMMENT  "EQ"'; tw=d.textlength(label,font=fn)
        bx=(W-tw-40)/2; litbar(d,bx,y+208,bx+tw+40,y+208+int(100*s),VGOLD,b); d.text((bx+20,y+214),label,font=fn,fill=A(INK,b))
        if C.GL: C.GL.rectangle([bx-4,y+204,bx+tw+44,y+216+int(100*s)],outline=A(VGOLD,b),width=12)
