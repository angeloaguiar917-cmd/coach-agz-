import json, subprocess, sys, math
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
S=sys.argv[1]; F=S+'/fonts/'; T=S+'/test1/'
W,H=1080,1920; FPS=30; DUR=9.40; N=int(round(DUR*FPS))
GOLD=(201,169,110); CREAM=(244,241,234); RED=(231,71,42); NAVY=(14,17,23); INK=(28,32,44); PAPER=(243,239,230)
_fc={}
def f(n,s):
    k=(n,int(s))
    if k not in _fc: _fc[k]=ImageFont.truetype(F+n,int(s))
    return _fc[k]
def clamp(x,a=0,b=1): return max(a,min(b,x))
def ease_out(x): x=clamp(x); return 1-(1-x)**3
def ease_in(x): x=clamp(x); return x*x
def ease_io(x): x=clamp(x); return 4*x**3 if x<.5 else 1-(-2*x+2)**3/2
def ease_back(x,s=1.7): x=clamp(x); return 1+(s+1)*(x-1)**3+s*(x-1)**2
def lerp(a,b,t): return a+(b-a)*t
def shadow_of(sprite,blur=18,alpha=150):
    a=sprite.split()[3].point(lambda v:int(v*alpha/255)); sh=Image.new('RGBA',sprite.size,(0,0,0,0)); sh.putalpha(a)
    pad=blur*3; big=Image.new('RGBA',(sprite.width+pad*2,sprite.height+pad*2),(0,0,0,0)); big.alpha_composite(sh,(pad,pad))
    return big.filter(ImageFilter.GaussianBlur(blur)),pad
def place(base,sprite,cx,cy,scale=1.0,rot=0.0,alpha=1.0,shadow=True,sx=1.0,sy=1.0,sh_off=(10,24)):
    if alpha<=0.01 or scale<=0.01: return
    sp=sprite
    if scale!=1 or sx!=1 or sy!=1: sp=sp.resize((max(1,int(sp.width*scale*sx)),max(1,int(sp.height*scale*sy))),Image.BICUBIC)
    if rot: sp=sp.rotate(rot,expand=True,resample=Image.BICUBIC)
    if alpha<1: sp=sp.copy(); sp.putalpha(sp.split()[3].point(lambda v:int(v*alpha)))
    if shadow:
        sh,pad=shadow_of(sp)
        base.alpha_composite(sh,(int(cx-sp.width/2-pad+sh_off[0]),int(cy-sp.height/2-pad+sh_off[1])))
    base.alpha_composite(sp,(int(cx-sp.width/2),int(cy-sp.height/2)))

# ---------- sprites ----------
def make_bottle():
    w,h=300,470; im=Image.new('RGBA',(w,h),(0,0,0,0)); d=ImageDraw.Draw(im)
    d.rounded_rectangle([40,0,260,80],radius=14,fill=(236,236,232)); 
    for x in range(52,250,16): d.line([(x,8),(x,72)],fill=(205,205,200),width=4)
    d.rounded_rectangle([20,70,280,465],radius=34,fill=(150,72,18))
    d.rounded_rectangle([20,70,280,465],radius=34,outline=(110,50,10),width=4)
    d.rounded_rectangle([44,96,72,440],radius=12,fill=(196,118,52))              # glass sheen
    d.rectangle([20,170,280,380],fill=(250,248,242))
    d.text((44,176),'Rx',font=f('BebasNeue.ttf',104),fill=INK)
    d.text((140,190),'PHARMACY',font=f('JBMono-500.ttf',26),fill=INK); d.text((140,222),'DISPENSED',font=f('JBMono-500.ttf',26),fill=INK)
    for i,(txt) in enumerate(['LOT  A41927','EXP  09/2027','QTY  30']):
        d.text((44,290+i*28),txt,font=f('JBMono-500.ttf',22),fill=(70,74,86))
    d.line([(44,282),(256,282)],fill=(200,196,186),width=2)
    return im
def make_box_front():
    w,h=520,380; im=Image.new('RGBA',(w,h),(0,0,0,0)); d=ImageDraw.Draw(im)
    d.rectangle([0,0,w-1,h-1],fill=(182,138,90)); d.rectangle([0,0,w-1,h-1],outline=(140,100,60),width=5)
    d.rectangle([0,0,w-1,26],fill=(160,118,74))
    d.rectangle([228,0,292,h-1],fill=(205,175,130,200))                          # tape
    lx,ly=96,70; d.rectangle([lx,ly,lx+330,ly+250],fill=(250,248,242)); d.rectangle([lx,ly,lx+330,ly+250],outline=(60,60,60),width=2)
    m=f('JBMono-500.ttf',27)
    d.text((lx+16,ly+12),'FROM: GUANGZHOU, CN',font=m,fill=INK)
    d.text((lx+16,ly+48),'TO:   USA',font=m,fill=INK)
    d.line([(lx+14,ly+88),(lx+316,ly+88)],fill=(160,160,160),width=2)
    d.text((lx+16,ly+98),'CONTENTS:',font=m,fill=INK); d.text((lx+16,ly+130),'"LAB SUPPLIES"',font=f('JBMono-500.ttf',30),fill=RED)
    d.text((lx+16,ly+168),'VALUE: $15',font=m,fill=INK)
    rng=np.random.default_rng(3); x=lx+200
    while x<lx+318:
        bw=int(rng.integers(2,6)); d.rectangle([x,ly+170,x+bw,ly+236],fill=INK); x+=bw+int(rng.integers(2,5))
    return im
def make_vial():
    w,h=96,180; im=Image.new('RGBA',(w,h),(0,0,0,0)); d=ImageDraw.Draw(im)
    d.rounded_rectangle([14,0,82,30],radius=6,fill=(196,48,40)); d.rectangle([20,28,76,46],fill=(180,184,190))
    d.rounded_rectangle([8,44,88,178],radius=14,fill=(210,226,236,150),outline=(235,245,250,230),width=3)
    d.rounded_rectangle([12,140,84,174],radius=10,fill=(250,250,250,255))               # powder
    d.rectangle([8,82,88,124],fill=(250,248,242,255)); d.text((16,86),'10MG',font=f('BebasNeue.ttf',34),fill=INK)
    d.line([(20,56),(20,132)],fill=(255,255,255,190),width=5)
    return im
COA_W,COA_H=860,840
FIELDS=[('Product','Peptide · 10 mg vial'),('Batch No.','P-240613'),('Purity (HPLC)','99.9%'),
        ('Tested by','Supplier in-house lab'),('Independent lab','—'),('Approved','')]
FIELD_Y0=230; FIELD_DY=88
def make_coa():
    im=Image.new('RGBA',(COA_W,COA_H),PAPER+(255,)); d=ImageDraw.Draw(im)
    rng=np.random.default_rng(5); n=(rng.standard_normal((COA_H,COA_W))*5).astype(np.int16)
    arr=np.array(im).astype(np.int16); arr[...,:3]+=n[...,None]; im=Image.fromarray(np.clip(arr,0,255).astype(np.uint8)); d=ImageDraw.Draw(im)
    d.rectangle([22,22,COA_W-23,COA_H-23],outline=(170,160,140),width=3)
    d.text((56,52),'CERTIFICATE OF ANALYSIS',font=f('BebasNeue.ttf',84),fill=INK)
    d.text((58,146),'SUPPLIER CO., LTD.  ·  SHENZHEN, CHINA',font=f('JBMono-500.ttf',26),fill=(96,96,104))
    d.line([(56,196),(COA_W-56,196)],fill=INK,width=3)
    for i,(k,v) in enumerate(FIELDS):
        y=FIELD_Y0+i*FIELD_DY
        d.text((58,y),k,font=f('DMSans-400.ttf',36),fill=(90,92,104))
        d.text((370,y),v,font=f('DMSans-700.ttf',40 if k!='Purity (HPLC)' else 46),fill=INK)
        d.line([(56,y+64),(COA_W-56,y+64)],fill=(214,206,190),width=2)
    y=FIELD_Y0+5*FIELD_DY   # signature scribble
    pts=[(380+i*7,y+30+14*math.sin(i*0.9)+6*math.sin(i*2.3)) for i in range(40)]
    d.line(pts,fill=(40,60,140),width=4,joint='curve')
    return im
BOTTLE=make_bottle(); BOXF=make_box_front(); VIAL=make_vial(); COA=make_coa()

words=json.load(open(T+'words.json'))
G=[(0,3),(3,5),(5,8),(8,11),(11,14),(14,17),(17,20),(20,22),(22,24),(24,27),(27,29),(29,32)]
def gstart(g): return words[G[g][0]]['s']
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
        fn=f('BebasNeue.ttf',size); sp=d.textlength(' ',font=fn)+14
        wd=[d.textlength(w,font=fn) for w in ws]; tot=sum(wd)+sp*(len(ws)-1)
        if tot<=CAP_MAX: break
        size-=4
    x=(W-tot)/2; xs=[]
    for w_ in wd: xs.append(x); x+=w_+sp
    return ws,wd,xs,size

# ---------- timeline ----------
BOT_IN=(3.20,3.48); BOT_OUT=(4.40,4.68)
BG=(4.36,4.70)
BOX_DROP=(4.66,4.92)            # gravity drop, lands 4.92
FLAPS=(5.60,5.82); VIALS=[5.72,5.82,5.92]
COA_RISE=(6.44,7.00); BOX_EXIT=(6.50,6.85)
HL=[(7.75,3),(8.20,4)]          # highlighter on field idx
STAMP_T=8.66
COA_CX,COA_CY=540,850
def coa_state(t):
    p=(t-COA_RISE[0])/(COA_RISE[1]-COA_RISE[0])
    if p<=0: return None
    e=ease_back(p,0.9)                              # light paper: gentle overshoot
    sc=lerp(0.22,1.0,e); cy=lerp(905,COA_CY,ease_out(p))
    rot=lerp(-8,0,ease_out(p))+ (1.2*math.exp(-(t-COA_RISE[1])*5)*math.sin((t-COA_RISE[1])*14) if t>COA_RISE[1] else 0)
    return sc,cy,rot,clamp(p*12)

def draw_box(base,t):
    if t<BOX_DROP[0]: return
    p=(t-BOX_DROP[0])/(BOX_DROP[1]-BOX_DROP[0])
    cy_land=1050
    if p<1: cy=lerp(-300,cy_land,ease_in(p)); sx=sy=1
    else:
        k=t-BOX_DROP[1]; sq=0.07*math.exp(-k*18)*math.cos(k*34)   # squash & settle
        cy=cy_land+190*sq; sx=1+sq; sy=1-sq
    ex=clamp((t-BOX_EXIT[0])/(BOX_EXIT[1]-BOX_EXIT[0])); a=1-ease_in(ex); cy+=260*ease_in(ex)
    if a<=0: return
    # flaps (behind front) open
    fp=ease_out((t-FLAPS[0])/(FLAPS[1]-FLAPS[0]))
    top=cy-190*sy; lay=Image.new('RGBA',(W,H),(0,0,0,0)); ld=ImageDraw.Draw(lay)
    if fp>0:
        lift=150*fp; spread=60*fp
        ld.polygon([(280,top),(540,top),(540-spread*0.3,top-lift),(280-spread,top-lift*0.8)],fill=(168,126,80,int(255*a)))
        ld.polygon([(540,top),(800,top),(800+spread,top-lift*0.8),(540+spread*0.3,top-lift)],fill=(160,118,74,int(255*a)))
    # vials rise out of the box (between flaps and front)
    for i,vt in enumerate(VIALS):
        vp=(t-vt)/0.30
        if vp>0:
            vy=lerp(top+60,top-110,ease_back(vp,1.4)); place(lay,VIAL,440+i*100,vy,alpha=a,shadow=False)
    base.alpha_composite(lay)
    place(base,BOXF,540,cy,sx=sx,sy=sy,alpha=a)

def frame(src,t):
    g=ease_io((t-BG[0])/(BG[1]-BG[0])); bg=src
    if g>0:
        b=src.filter(ImageFilter.GaussianBlur(18*g)); bg=Image.blend(b,Image.new('RGB',(W,H),NAVY),0.55*g)
    im=bg.convert('RGBA')
    sc=Image.new('L',(1,H))
    for y in range(H):
        a=0
        if y>1180: a=min(1,(y-1180)/260)*110
        if y<420: a=max(a,(1-y/420)*120)
        sc.putpixel((0,y),int(a*(1-g)))
    im.alpha_composite(Image.merge('RGBA',[Image.new('L',(W,H),c) for c in NAVY]+[sc.resize((W,H))]))
    # bottle beside him (medium weight: rises, small overshoot); pushed out left when the box arrives
    pin=(t-BOT_IN[0])/(BOT_IN[1]-BOT_IN[0]); pout=ease_in((t-BOT_OUT[0])/(BOT_OUT[1]-BOT_OUT[0]))
    if pin>0 and pout<1:
        place(im,BOTTLE,lerp(205,205-420,pout),lerp(1250,1130,ease_back(pin,1.3)),scale=0.60,rot=lerp(-4,0,ease_out(pin))-14*pout,alpha=clamp(pin*3)*(1-pout))
    draw_box(im,t)
    cs=coa_state(t)
    if cs:
        sc_,cy,rot,al=cs; place(im,COA,COA_CX,cy,scale=sc_,rot=rot,alpha=al,sh_off=(12,28))
    d=ImageDraw.Draw(im,'RGBA')
    # highlighter marks on the COA (marker wipe left→right)
    top=COA_CY-COA_H/2; left=COA_CX-COA_W/2
    for ht,idx in HL:
        hp=ease_out((t-ht)/0.28)
        if hp>0:
            y=top+FIELD_Y0+idx*FIELD_DY-6; x0=left+360; x1=left+COA_W-60
            ov=Image.new('RGBA',(W,H),(0,0,0,0)); od=ImageDraw.Draw(ov)
            od.rounded_rectangle([x0,y,lerp(x0,x1,hp),y+60],radius=8,fill=(240,196,60,110))
            im.alpha_composite(ov)
            d=ImageDraw.Draw(im,'RGBA')
    # stamp: heavy rubber stamp, slams on purity claim
    if t>=STAMP_T-0.10:
        sp_=clamp((t-(STAMP_T-0.10))/0.10)
        s_=lerp(1.7,1.0,ease_out(sp_)) if sp_<1 else 1.0+0.04*math.exp(-(t-STAMP_T)*14)*math.cos((t-STAMP_T)*40)
        st=Image.new('RGBA',(520,170),(0,0,0,0)); s2=ImageDraw.Draw(st)
        s2.rounded_rectangle([4,4,515,165],radius=14,outline=RED,width=9)
        fn=f('BebasNeue.ttf',104); tw=s2.textlength('SELF-ISSUED',font=fn); s2.text(((520-tw)/2,10),'SELF-ISSUED',font=fn,fill=RED)
        fs=f('JBMono-500.ttf',24); t2='NOT INDEPENDENTLY VERIFIED'; tw=s2.textlength(t2,font=fs); s2.text(((520-tw)/2,124),t2,font=fs,fill=RED)
        # worn ink texture
        a=np.array(st); rng=np.random.default_rng(11); m=rng.random(a.shape[:2])<0.12; a[...,3][m]=(a[...,3][m]*0.35).astype(np.uint8); st=Image.fromarray(a)
        place(im,st,COA_CX+175,top+FIELD_Y0+5*FIELD_DY+62,scale=s_*0.84,rot=-9,alpha=clamp(sp_*1.5),shadow=False)
        d=ImageDraw.Draw(im,'RGBA')
    # gold edge rule + pinned title
    d.rectangle([0,0,7,H],fill=GOLD)
    p=ease_back(t/0.35,1.2); ty=lerp(-180,0,p)
    d.rectangle([8,212+ty,W,372+ty],fill=NAVY+(228,))
    d.line([(64,244+ty),(108,244+ty)],fill=GOLD,width=4); d.text((122,228+ty),'@coach.agz',font=f('JBMono-500.ttf',28),fill=GOLD)
    fn=f('BebasNeue.ttf',80); d.text((64,266+ty),'BIG PHARMA',font=fn,fill=CREAM); d.text((64+d.textlength('BIG PHARMA',font=fn),266+ty),' DOUBLE STANDARD',font=fn,fill=GOLD)
    # captions
    gi=group_at(t)
    if gi is not None:
        ws,wd,xs,size=cap_layout(gi,d); g0=gstart(gi); pop=clamp((t-g0)/0.13)
        s=lerp(0.86,1,ease_out(pop/0.6)) if pop<0.6 else (1+0.08*math.sin(pop*math.pi)*(1-pop*0.3) if pop<1 else 1)
        cap=Image.new('RGBA',(W,300),(0,0,0,0)); cd=ImageDraw.Draw(cap); shd=Image.new('RGBA',(W,300),(0,0,0,0)); sdd=ImageDraw.Draw(shd)
        aw=active_word(t,gi)-G[gi][0]; fn=f('BebasNeue.ttf',size)
        ws_t=[words[i]['s'] for i in range(G[gi][0],G[gi][1])]
        prev=max(0,aw-1); bt=ease_out((t-ws_t[aw])/0.08) if aw>0 else 1
        bx0=lerp(xs[prev],xs[aw],bt)-18; bx1=lerp(xs[prev]+wd[prev],xs[aw]+wd[aw],bt)+18
        for i,(w_,x_) in enumerate(zip(ws,xs)):
            if i!=aw: sdd.text((x_+4,46),w_,font=fn,fill=(0,0,0,210))
        cap.alpha_composite(shd.filter(ImageFilter.GaussianBlur(6)))
        cd.rounded_rectangle([bx0,40+size*0.02,bx1,40+size*0.98],radius=12,fill=RED+(255,))
        for i,(w_,x_) in enumerate(zip(ws,xs)):
            cd.text((x_,40),w_,font=fn,fill=CREAM,stroke_width=0 if i==aw else 3,stroke_fill=(0,0,0))
        if abs(s-1)>0.002:
            cap=cap.resize((int(W*s),int(300*s)),Image.BICUBIC); ox=int((W-cap.width)/2); oy=int(CAP_Y-40-(cap.height-300)/2)
        else: ox,oy=0,CAP_Y-40
        im.alpha_composite(cap,(ox,oy)) if ox>=0 else im.alpha_composite(cap.crop((-ox,0,-ox+W,cap.height)),(0,oy))
    out=im.convert('RGB')
    k=round((t-STAMP_T)*FPS)
    if k in (0,1):
        dx=[8,-5][k]; z=1.025; big=out.resize((int(W*z),int(H*z)),Image.BICUBIC); ox=(big.width-W)//2-dx; oy=(big.height-H)//2
        out=big.crop((ox,oy,ox+W,oy+H)); ImageDraw.Draw(out).rectangle([0,0,7,H],fill=GOLD)
    return out

if __name__=='__main__':
    only=[float(x) for x in sys.argv[2:]]
    if only:   # still-frame preview mode
        for tt in only:
            subprocess.run(['ffmpeg','-v','error','-y','-ss',str(tt),'-i',T+'raw.mp4','-frames:v','1','-vf',f'scale={W}:{H}',T+'qc/_src.png'])
            frame(Image.open(T+'qc/_src.png').convert('RGB'),tt).resize((360,640)).save(T+f'qc/still_{tt:.2f}.jpg',quality=85)
        sys.exit()
    dec=subprocess.Popen(['ffmpeg','-v','error','-i',T+'raw.mp4','-t',str(DUR),'-vf',f'fps={FPS},scale={W}:{H}','-f','rawvideo','-pix_fmt','rgb24','-'],stdout=subprocess.PIPE)
    enc=subprocess.Popen(['ffmpeg','-v','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-','-vf','scale=720:1280:flags=lanczos','-c:v','libx264','-crf','18','-preset','medium','-pix_fmt','yuv420p',T+'video2_only.mp4'],stdin=subprocess.PIPE)
    for n in range(N):
        buf=dec.stdout.read(W*H*3)
        if len(buf)<W*H*3: print('short at',n); break
        enc.stdin.write(frame(Image.frombuffer('RGB',(W,H),buf),n/FPS).tobytes())
    enc.stdin.close(); enc.wait(); dec.kill(); print('frames',N)
