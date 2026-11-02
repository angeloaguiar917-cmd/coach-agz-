import json, subprocess, sys, math
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps, ImageChops
S=sys.argv[1]; F=S+'/fonts/'; T=S+'/test1/'
W,H=1080,1920; FPS=30; DUR=9.40; N=int(round(DUR*FPS))
GOLD=(201,169,110); CREAM=(244,241,234); RED=(255,48,40); NAVY=(14,17,23); INK=(16,20,34)
VGOLD=(255,184,48); CYAN=(40,220,255); GREEN=(46,230,110); DEEP=(5,8,16)
GL=None   # per-frame glow layer (ImageDraw)
_fc={}
def f(n,s):
    k=(n,int(s))
    if k not in _fc: _fc[k]=ImageFont.truetype(F+n,int(s))
    return _fc[k]
def clamp(x,a=0,b=1): return max(a,min(b,x))
def expo(x): x=clamp(x); return 1 if x>=1 else 1-2**(-10*x)       # hard snap, no overshoot
def ease_io(x): x=clamp(x); return 4*x**3 if x<.5 else 1-(-2*x+2)**3/2
def lerp(a,b,t): return a+(b-a)*t
MONO='JBMono-500.ttf'; BEB='BebasNeue.ttf'

def brackets(d,x0,y0,x1,y1,col,L=34,w=4,p=1.0):
    L=L*p
    for (cx,cy,sx,sy) in [(x0,y0,1,1),(x1,y0,-1,1),(x0,y1,1,-1),(x1,y1,-1,-1)]:
        d.line([(cx,cy),(cx+sx*L,cy)],fill=col,width=w); d.line([(cx,cy),(cx,cy+sy*L)],fill=col,width=w)

# ---------- documents ----------
LBL_W,LBL_H=800,440; LBL_FLAG=None
def make_label():
    global LBL_FLAG
    im=Image.new('RGB',(LBL_W,LBL_H),(250,249,246)); d=ImageDraw.Draw(im)
    rng=np.random.default_rng(2); a=np.array(im).astype(np.int16)+(rng.standard_normal((LBL_H,LBL_W,1))*6).astype(np.int16); im=Image.fromarray(np.clip(a,0,255).astype(np.uint8)); d=ImageDraw.Draw(im)
    d.rectangle([0,0,LBL_W-1,LBL_H-1],outline=(40,40,40),width=3)
    d.rectangle([0,0,LBL_W-1,64],fill=(30,30,30)); d.text((20,10),'INTL EXPRESS  ·  AIR',font=f(MONO,36),fill=(236,234,228))
    m=f(MONO,32)
    d.text((24,86),'SHIPPER   GUANGZHOU, CN',font=m,fill=INK)
    d.text((24,132),'CONSIGNEE USA',font=m,fill=INK)
    d.line([(20,182),(LBL_W-20,182)],fill=(120,120,120),width=2)
    d.text((24,198),'DECLARED  LAB SUPPLIES',font=m,fill=INK); LBL_FLAG=(12,190,int(24+d.textlength('DECLARED  LAB SUPPLIES',font=m))+14,244)
    d.text((24,244),'VALUE     USD 15.00',font=m,fill=INK)
    d.text((24,290),'WEIGHT    0.2 KG',font=m,fill=INK)
    x=470; rng=np.random.default_rng(4)
    while x<LBL_W-24:
        bw=int(rng.integers(2,7)); d.rectangle([x,300,x+bw,420],fill=INK); x+=bw+int(rng.integers(2,6))
    return im.convert('RGBA')
COA_W,COA_H=820,690
FIELDS=[('Product','Peptide · 10 mg vial'),('Batch No.','P-240613'),('Purity (HPLC)','99.9%'),('Tested by','In-house'),('Independent lab','—'),('Approved','')]
FY0=196; FDY=76
def make_coa():
    im=Image.new('RGB',(COA_W,COA_H),(250,249,246)); d=ImageDraw.Draw(im)
    rng=np.random.default_rng(5); a=np.array(im).astype(np.int16)+(rng.standard_normal((COA_H,COA_W,1))*5).astype(np.int16); im=Image.fromarray(np.clip(a,0,255).astype(np.uint8)); d=ImageDraw.Draw(im)
    d.rectangle([14,14,COA_W-15,COA_H-15],outline=(150,148,140),width=2)
    d.rectangle([14,14,COA_W-15,138],fill=(150,14,20))
    d.rectangle([44,40,104,100],outline=(255,255,255),width=3); d.text((58,46),'S',font=f(BEB,56),fill=(255,255,255))
    d.text((124,34),'CERTIFICATE OF ANALYSIS',font=f(BEB,70),fill=(255,255,255))
    d.text((126,104),'SUPPLIER CO., LTD. · SHENZHEN, CHINA',font=f(MONO,24),fill=(255,200,196))
    d.line([(44,160),(COA_W-44,160)],fill=INK,width=3)
    for i,(k,v) in enumerate(FIELDS):
        y=FY0+i*FDY
        d.text((46,y),k,font=f('DMSans-400.ttf',32),fill=(84,86,96))
        d.text((330,y),v,font=f('DMSans-700.ttf',36),fill=INK)
        d.line([(44,y+56),(COA_W-44,y+56)],fill=(205,200,190),width=2)
    y=FY0+5*FDY; pts=[(345+i*6,y+26+11*math.sin(i*0.9)+5*math.sin(i*2.3)) for i in range(38)]
    d.line(pts,fill=(30,40,90),width=3,joint='curve')
    return im.convert('RGBA')
LABEL=make_label(); COA=make_coa()

# ---------- panel ----------
P=(64,470,1016,1260)            # evidence panel (handoff frame persists label -> x-ray -> COA)
CX=(P[0]+P[2])//2; CY=(P[1]+P[3])//2+30
def doc_pos(img): return (CX-img.width//2, CY-img.height//2)
def xray_layer():
    lay=Image.new('RGBA',(P[2]-P[0],P[3]-P[1]-70),(2,12,26,255)); d=ImageDraw.Draw(lay)
    for y in range(0,lay.height,4): d.line([(0,y),(lay.width,y)],fill=(255,255,255,6))
    bx0,by0,bx1,by1=170,120,780,600; 
    for x in range(bx0,bx1,18): d.line([(x,by0),(x+9,by0)],fill=CYAN+(110,),width=2); d.line([(x,by1),(x+9,by1)],fill=CYAN+(110,),width=2)
    for y in range(by0,by1,18): d.line([(bx0,y),(bx0,y+9)],fill=CYAN+(110,),width=2); d.line([(bx1,y),(bx1,y+9)],fill=CYAN+(110,),width=2)
    for i in range(3):
        x=300+i*130; y=250
        g=Image.new('RGBA',lay.size,(0,0,0,0)); gd=ImageDraw.Draw(g)
        gd.rounded_rectangle([x,y+40,x+90,y+230],radius=14,outline=CYAN+(255,),width=4)
        gd.rectangle([x+12,y,x+78,y+40],outline=CYAN+(255,),width=4)
        gd.rounded_rectangle([x+8,y+180,x+82,y+226],radius=8,fill=CYAN+(190,))
        gb=g.filter(ImageFilter.GaussianBlur(9)); lay.alpha_composite(gb); lay.alpha_composite(gb); lay.alpha_composite(g)
    return lay
XRAY=xray_layer()

words=json.load(open(T+'words.json'))
G=[(0,3),(3,5),(5,8),(8,11),(11,14),(14,17),(17,20),(20,22),(22,24),(24,27),(27,29),(29,32)]
def group_at(t):
    cur=None
    for gi,(a,b) in enumerate(G):
        if words[a]['s']<=t+1e-6: cur=gi
    return cur
def active_word(t,gi):
    a,b=G[gi]; act=a
    for i in range(a,b):
        if words[i]['s']<=t: act=i
    return act
CAP_Y=1335; CAP_MAX=920
def cap_layout(gi,d):
    a,b=G[gi]; ws=[words[i]['w'].upper().rstrip(',') for i in range(a,b)]; size=128
    while True:
        fn=f(BEB,size); sp=d.textlength(' ',font=fn)+14
        wd=[d.textlength(w,font=fn) for w in ws]; tot=sum(wd)+sp*(len(ws)-1)
        if tot<=CAP_MAX: break
        size-=4
    x=(W-tot)/2; xs=[]
    for w_ in wd: xs.append(x); x+=w_+sp
    return ws,wd,xs,size

TAG_IN=(3.20,3.36); TAG_OUT=(4.36,4.52)
BG=(4.36,4.70); PANEL_IN=(4.62,4.82)
FLAG_LBL=5.30; XRAY_WIPE=(5.62,5.92); XR_CALL=[(5.98,0),(6.14,1)]
COA_WIPE=(6.44,6.80); FLAGS=[(7.75,3,'SAME SELLER'),(8.20,4,'NONE')]
VERDICT=(8.56,8.66)

def frosted(im,box,dark=0.72,blur=22):
    x0,y0,x1,y1=[int(v) for v in box]
    if x1<=x0 or y1<=y0: return
    reg=im.crop((x0,y0,x1,y1)).filter(ImageFilter.GaussianBlur(blur))
    reg=Image.blend(reg.convert('RGB'),Image.new('RGB',reg.size,DEEP),dark).convert('RGBA')
    im.paste(reg,(x0,y0))

def evidence_tag(im,t):
    pin=expo((t-TAG_IN[0])/(TAG_IN[1]-TAG_IN[0])); pout=clamp((t-TAG_OUT[0])/(TAG_OUT[1]-TAG_OUT[0]))
    if pin<=0 or pout>=1: return
    dx=lerp(-30,0,pin)-520*pout**2
    x0,y0,x1,y1=64+dx,1000,520+dx,1265
    if x1<10: return
    frosted(im,(max(8,x0),y0,x1,y1),0.80,18)
    d=ImageDraw.Draw(im,'RGBA'); a=int(255*pin*(1-pout))
    d.rectangle([x0,y0,x1,y1],outline=VGOLD+(int(a*0.4),),width=2); brackets(d,x0,y0,x1,y1,VGOLD+(a,),26,4,pin)
    if GL: brackets(GL,x0,y0,x1,y1,VGOLD+(int(a*0.8),),26,8,pin)
    d.text((x0+22,y0+16),'REF · US PHARMACY',font=f(MONO,26),fill=VGOLD+(a,))
    rows=['LOT-TRACKED','PHARMACIST-DISPENSED','REGULATED MFG','RECALL SYSTEM']
    for i,r in enumerate(rows):
        rp=clamp((t-TAG_IN[0]-0.08-i*0.05)/0.08)
        if rp<=0: continue
        y=y0+64+i*46; ra=int(a*rp)
        d.line([(x0+24,y+16),(x0+32,y+26),(x0+46,y+6)],fill=GREEN+(ra,),width=4)
        if GL: GL.line([(x0+24,y+16),(x0+32,y+26),(x0+46,y+6)],fill=GREEN+(ra,),width=8)
        d.text((x0+60,y),r,font=f(MONO,30),fill=CREAM+(ra,))

def flag_box(d,box,label,t0,t):
    p=expo((t-t0)/0.14)
    if p<=0: return
    x0,y0,x1,y1=box
    brackets(d,x0,y0,x1,y1,RED+(255,),30,5,1.0)
    if GL: brackets(GL,x0,y0,x1,y1,RED+(255,),30,10,1.0); GL.rectangle([x0,y0,x1,y1],outline=RED+(200,),width=6)
    if p>0.3:
        q=clamp((p-0.3)/0.7)
        d.line([(x0,y0),(lerp(x0,x1,q),y0)],fill=RED+(255,),width=3); d.line([(x1,y1),(lerp(x1,x0,q),y1)],fill=RED+(255,),width=3)
        d.line([(x0,y1),(x0,lerp(y1,y0,q))],fill=RED+(255,),width=3); d.line([(x1,y0),(x1,lerp(y0,y1,q))],fill=RED+(255,),width=3)
    if p>0.5:
        fn=f(MONO,28); tw=d.textlength(label,font=fn)
        tx=x1+12; ty=(y0+y1)/2-20
        d.rectangle([tx,ty,tx+tw+24,ty+40],fill=RED+(255,)); d.text((tx+12,ty+4),label,font=fn,fill=(255,255,255))
        if GL: GL.rectangle([tx,ty,tx+tw+24,ty+40],fill=RED+(220,))

def panel(im,t):
    pp=expo((t-PANEL_IN[0])/(PANEL_IN[1]-PANEL_IN[0]))
    if pp<=0: return
    s=lerp(1.05,1.0,pp); w=(P[2]-P[0])*s; h=(P[3]-P[1])*s
    x0,y0,x1,y1=CX-w/2,(P[1]+P[3])/2-h/2,CX+w/2,(P[1]+P[3])/2+h/2
    lay=Image.new('RGBA',(W,H),(0,0,0,0))
    frosted(im,(x0,y0,x1,y1),0.86,8)
    d=ImageDraw.Draw(lay,'RGBA')
    # content: label -> x-ray -> COA, switched by scan wipes inside the persistent frame
    cont=Image.new('RGBA',(W,H),(0,0,0,0))
    lx,ly=doc_pos(LABEL); cont.alpha_composite(LABEL,(lx,ly))
    def wipe(base,new,t0,t1,pos):
        q=ease_io((t-t0)/(t1-t0))
        if q<=0: return base,None
        top=P[1]+70; ys=int(lerp(top,P[3],q))
        nl=Image.new('RGBA',(W,H),(0,0,0,0)); nl.alpha_composite(new,pos)
        mask=Image.new('L',(W,H),0); ImageDraw.Draw(mask).rectangle([0,0,W,ys],fill=255)
        if q>=1: return nl,None
        clear=Image.new('L',(W,H),0); ImageDraw.Draw(clear).rectangle([0,0,W,ys],fill=255)
        b=base.copy(); b.putalpha(Image.composite(Image.new('L',(W,H),0),b.split()[3],clear))
        b.alpha_composite(Image.composite(nl,Image.new('RGBA',(W,H),(0,0,0,0)),mask))
        return b,ys
    cont,ys1=wipe(cont,XRAY,*XRAY_WIPE,(P[0],P[1]+70))
    cont,ys2=wipe(cont,COA,*COA_WIPE,doc_pos(COA))
    if pp<1: cont=cont.filter(ImageFilter.GaussianBlur(8*(1-pp)))
    cont.putalpha(cont.split()[3].point(lambda v:int(v*pp)))
    lay.alpha_composite(cont)
    d=ImageDraw.Draw(lay,'RGBA'); a=int(255*pp)
    d.rectangle([x0,y0,x1,y1],outline=VGOLD+(int(a*0.45),),width=2); brackets(d,x0,y0,x1,y1,VGOLD+(a,),40,5)
    if GL: brackets(GL,x0,y0,x1,y1,VGOLD+(a,),44,14); GL.rectangle([x0,y0,x1,y1],outline=VGOLD+(int(a*0.5),),width=6)
    stage='PARCEL SCAN' if t<XRAY_WIPE[0] else ('X-RAY' if t<COA_WIPE[0] else 'DOCUMENT REVIEW')
    d.ellipse([x0+26,y0+26,x0+42,y0+42],fill=RED+(a if int(t*4)%2==0 else a//3,))
    d.text((x0+56,y0+18),f'{stage}',font=f(MONO,28),fill=CREAM+(a,))
    d.text((x1-250,y0+18),f'EVIDENCE 0{1 if t<XRAY_WIPE[0] else (2 if t<COA_WIPE[0] else 3)}',font=f(MONO,28),fill=VGOLD+(a,))
    for ys in (ys1,ys2):
        if ys:
            g=Image.new('RGBA',(W,H),(0,0,0,0)); gd=ImageDraw.Draw(g); gd.rectangle([x0+4,ys-3,x1-4,ys+3],fill=CYAN+(255,))
            if GL: GL.rectangle([x0+4,ys-10,x1-4,ys+10],fill=CYAN+(230,))
            lay.alpha_composite(g.filter(ImageFilter.GaussianBlur(8))); lay.alpha_composite(g)
    d=ImageDraw.Draw(lay,'RGBA')
    # flags
    if t<XRAY_WIPE[0]:
        bx=(lx+LBL_FLAG[0],ly+LBL_FLAG[1],lx+LBL_FLAG[2],ly+LBL_FLAG[3]); flag_box(d,bx,'MISDECLARED',FLAG_LBL,t)
    if XRAY_WIPE[1]<=t<COA_WIPE[0]:
        for ct,i in XR_CALL:
            q=expo((t-ct)/0.12)
            if q<=0: continue
            txt=['3 × VIAL · NO PHARMACY LABEL','CONTENTS UNVERIFIED'][i]; y=[P[1]+130,P[3]-90][i]
            d.text((P[0]+40,y),txt,font=f(MONO,36),fill=(CYAN if i==0 else RED)+(int(255*q),))
    if t>=COA_WIPE[1]:
        cx0,cy0=doc_pos(COA)
        for ft,idx,lab in FLAGS:
            y=cy0+FY0+idx*FDY-10; vw=d.textlength(FIELDS[idx][1],font=f('DMSans-700.ttf',36)); flag_box(d,(cx0+316,y,cx0+330+vw+16,y+62),lab,ft,t)
    im.alpha_composite(lay)

def verdict(im,t):
    if t<VERDICT[0]: return
    p=expo((t-VERDICT[0])/(VERDICT[1]-VERDICT[0]))
    cx0,cy0=doc_pos(COA); y=cy0+FY0+5*FDY-16
    d=ImageDraw.Draw(im,'RGBA'); x0=P[0]; x1=lerp(x0,P[2],p)
    if GL: GL.rectangle([x0-4,y-8,x1+4,y+100],outline=RED+(255,),width=10)
    d.rectangle([x0,y,x1,y+92],fill=RED+(255,)); d.rectangle([x0,y+86,x1,y+92],fill=(150,10,10))
    if p>0.6:
        fn=f(BEB,74); txt='SELF-ISSUED'; d.text((x0+34,y+8),txt,font=fn,fill=(255,255,255))
        tw=d.textlength(txt,font=fn); d.text((x0+34+tw+26,y+30),'NOT INDEPENDENTLY VERIFIED',font=f(MONO,28),fill=(255,255,255))

def frame(src,t):
    g=ease_io((t-BG[0])/(BG[1]-BG[0])); bg=src
    if g>0: bg=Image.blend(src.filter(ImageFilter.GaussianBlur(18*g)),Image.new('RGB',(W,H),DEEP),0.68*g)
    im=bg.convert('RGBA'); bgsnap=None
    sc=Image.new('L',(1,H))
    for y in range(H):
        a=0
        if y>1180: a=min(1,(y-1180)/260)*110
        if y<420: a=max(a,(1-y/420)*120)
        sc.putpixel((0,y),int(a*(1-g)))
    im.alpha_composite(Image.merge('RGBA',[Image.new('L',(W,H),c) for c in NAVY]+[sc.resize((W,H))]))
    global GL
    glow=Image.new('RGBA',(W,H),(0,0,0,0)); GL=ImageDraw.Draw(glow,'RGBA')
    base=im.copy(); bgsnap=im.copy()
    evidence_tag(im,t); panel(im,t); verdict(im,t)
    GL=None
    if glow.getbbox():
        gb=np.asarray(glow.filter(ImageFilter.GaussianBlur(14))).astype(np.float32)/255
        g2=np.asarray(glow.filter(ImageFilter.GaussianBlur(40))).astype(np.float32)/255
        prem=np.clip(gb[...,:3]*gb[...,3:]*1.5+g2[...,:3]*g2[...,3:]*1.1,0,1)
        base_=np.asarray(im.convert('RGB')).astype(np.float32)/255
        out_=1-(1-base_)*(1-prem)                      # screen blend: light bloom
        im=Image.fromarray((out_*255).astype(np.uint8)).convert('RGBA')
    d=ImageDraw.Draw(im,'RGBA'); d.rectangle([0,0,7,H],fill=GOLD)
    p=expo(t/0.30); ty=lerp(-180,0,p)
    d.rectangle([8,212+ty,W,372+ty],fill=NAVY+(228,))
    d.line([(64,244+ty),(108,244+ty)],fill=GOLD,width=4); d.text((122,228+ty),'@coach.agz',font=f(MONO,28),fill=GOLD)
    fn=f(BEB,80); d.text((64,266+ty),'BIG PHARMA',font=fn,fill=CREAM); d.text((64+d.textlength('BIG PHARMA',font=fn),266+ty),' DOUBLE STANDARD',font=fn,fill=GOLD)
    gi=group_at(t)
    if gi is not None:
        ws,wd,xs,size=cap_layout(gi,d); g0=words[G[gi][0]]['s']; pop=expo((t-g0)/0.10); s=lerp(0.9,1,pop)
        cap=Image.new('RGBA',(W,300),(0,0,0,0)); cd=ImageDraw.Draw(cap); shd=Image.new('RGBA',(W,300),(0,0,0,0)); sdd=ImageDraw.Draw(shd)
        aw=active_word(t,gi)-G[gi][0]; fn=f(BEB,size); ws_t=[words[i]['s'] for i in range(G[gi][0],G[gi][1])]
        prev=max(0,aw-1); bt=expo((t-ws_t[aw])/0.07) if aw>0 else 1
        bx0=lerp(xs[prev],xs[aw],bt)-18; bx1=lerp(xs[prev]+wd[prev],xs[aw]+wd[aw],bt)+18
        for i,(w_,x_) in enumerate(zip(ws,xs)):
            if i!=aw: sdd.text((x_+4,46),w_,font=fn,fill=(0,0,0,210))
        cap.alpha_composite(shd.filter(ImageFilter.GaussianBlur(6)))
        cd.rounded_rectangle([bx0,40+size*0.02,bx1,40+size*0.98],radius=6,fill=RED+(255,))
        for i,(w_,x_) in enumerate(zip(ws,xs)): cd.text((x_,40),w_,font=fn,fill=CREAM,stroke_width=0 if i==aw else 3,stroke_fill=(0,0,0))
        if abs(s-1)>0.002:
            cap=cap.resize((int(W*s),int(300*s)),Image.BICUBIC); ox=int((W-cap.width)/2); oy=int(CAP_Y-40-(cap.height-300)/2)
        else: ox,oy=0,CAP_Y-40
        im.alpha_composite(cap,(ox,oy))
    out=im.convert('RGB'); k=round((t-VERDICT[1])*FPS)
    if k in (0,1):
        dx=[9,-5][k]; z=1.025; big=out.resize((int(W*z),int(H*z)),Image.BICUBIC); ox=(big.width-W)//2-dx; oy=(big.height-H)//2
        out=big.crop((ox,oy,ox+W,oy+H)); ImageDraw.Draw(out).rectangle([0,0,7,H],fill=GOLD)
    return out

if __name__=='__main__':
    only=[float(x) for x in sys.argv[2:]]
    if only:
        for tt in only:
            subprocess.run(['ffmpeg','-v','error','-y','-ss',str(tt),'-i',T+'raw.mp4','-frames:v','1','-vf',f'scale={W}:{H}',T+'qc/_src.png'])
            frame(Image.open(T+'qc/_src.png').convert('RGB'),tt).resize((360,640)).save(T+f'qc/s4_{tt:.2f}.jpg',quality=85)
        sys.exit()
    dec=subprocess.Popen(['ffmpeg','-v','error','-i',T+'raw.mp4','-t',str(DUR),'-vf',f'fps={FPS},scale={W}:{H}','-f','rawvideo','-pix_fmt','rgb24','-'],stdout=subprocess.PIPE)
    enc=subprocess.Popen(['ffmpeg','-v','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-','-vf','scale=720:1280:flags=lanczos','-c:v','libx264','-crf','18','-preset','medium','-pix_fmt','yuv420p',T+'video4_only.mp4'],stdin=subprocess.PIPE)
    for n in range(N):
        buf=dec.stdout.read(W*H*3)
        if len(buf)<W*H*3: print('short at',n); break
        enc.stdin.write(frame(Image.frombuffer('RGB',(W,H),buf),n/FPS).tobytes())
    enc.stdin.close(); enc.wait(); dec.kill(); print('frames',N)
