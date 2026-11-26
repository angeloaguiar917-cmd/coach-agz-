# Compositor + main. Usage:
#   python3 r_main.py stills t1 t2 ...        -> qc/st_*.jpg
#   python3 r_main.py render n0 n1 out.mp4    -> encode frame range
import sys, subprocess, math, os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import r_core as C
from r_core import (W,H,FPS,CUTS,N_FRAMES,f,A,txt,stxt,litbar,brackets,captions,
                    clamp,expo,ease,lerp,ap,win,
                    BEB,BAR,DMR,DMB,MONO,GOLD,CREAM,NAVY,MUTED,RED,VGOLD,CYAN,GREEN,AMBER,DEEP,INK,WHITE)
import r_sc_a as SA
import r_sc_b as SB

SRC=C.WD+'/assembled.mp4'
# scene activation windows that need a footage de-focus push (graphics own the frame briefly)
SPLIT=(18.98,29.45)   # dual graph occupies the top band
def mode_k(t,rng,ti=0.3,to=0.28):
    a,b=rng
    if t<a or t>b+to: return 0.0
    return ease((t-a)/ti) if t<a+ti else 1-ease((t-b)/to)

def zoom_at(t):
    seg=sum(1 for c in CUTS if c<=t+1e-6); z=1.0 if seg%2==0 else 1.055
    for t0,t1,zz in [(6.02,7.9,1.12),(31.0,31.8,1.09),(51.5,52.3,1.11),(73.7,74.5,1.12)]:
        if t0<=t<t1+0.2:
            k=min(expo((t-t0)/0.14),1-ease((t-t1)/0.2)); z=lerp(z,zz,k)
    return z
def zoomed(src,z,cx=560,cy=820):
    if abs(z-1)<1e-3: return src
    big=src.resize((int(W*z),int(H*z)),Image.BICUBIC); ox=int(cx*z-cx); oy=int(cy*z-cy)
    ox=max(0,min(big.width-W,ox)); oy=max(0,min(big.height-H,oy))
    return big.crop((ox,oy,ox+W,oy+H))

def furniture(im,t):
    """gold left rule + @coach.agz handle chip + research/educational disclaimer (static)."""
    d=ImageDraw.Draw(im,'RGBA')
    d.rectangle([0,0,7,H],fill=A(GOLD,1))
    # handle chip top-left (brand watermark, not a title/hook)
    ca=expo(t/0.3)
    d.line([(26,70),(70,70)],fill=A(GOLD,ca),width=4); txt(d,86,52,'@coach.agz',f(MONO,30),GOLD,ca)
    # disclaimer footer, muted tracked caps
    txt(d,W/2,1858,'F O R   R E S E A R C H   &   E D U C A T I O N A L   P U R P O S E S   O N L Y',f(MONO,18),(150,150,156),0.8*ca,'mm')

def base_frame(src,t):
    z=zoom_at(t); src=zoomed(src,z)
    im=src.convert('RGBA')
    # subtle vignette top & bottom so overlays/captions read (footage itself untouched in colour)
    yy=np.arange(H); aA=np.where(yy>1180,np.clip((yy-1180)/320,0,1)*120,0); aA=np.maximum(aA,np.where(yy<300,(1-yy/300)*110,0))
    im.alpha_composite(Image.merge('RGBA',[Image.new('L',(W,H),c) for c in NAVY]+[Image.fromarray(np.repeat(aA[:,None].astype(np.uint8),W,1))]))
    return im

def frame(src,t):
    im=base_frame(src,t)
    glow=Image.new('RGBA',(W,H),(0,0,0,0)); C.GL=ImageDraw.Draw(glow,'RGBA')
    d=ImageDraw.Draw(im,'RGBA')
    # scene order (mostly non-overlapping in time)
    SA.s_pedestal(im,d,t); d=ImageDraw.Draw(im,'RGBA')
    SA.s_stepper(im,d,t)
    SA.s_lens(im,d,t); d=ImageDraw.Draw(im,'RGBA')
    k=mode_k(t,SPLIT);
    if k>0: SA.s_graph(im,d,t,k)
    SA.s_gauge(im,d,t); d=ImageDraw.Draw(im,'RGBA')
    SB.s_lab(im,t,1.0 if 41.40<=t<=51.55 else 0.0); d=ImageDraw.Draw(im,'RGBA')
    SB.s_washout(im,d,t)
    SB.s_stack(im,d,t); d=ImageDraw.Draw(im,'RGBA')
    SB.s_verdict(im,d,t)
    SB.s_cta(im,t)
    C.GL=None
    # screen-blend bloom (quarter-res)
    if glow.getbbox():
        sm=glow.resize((W//4,H//4),Image.BILINEAR)
        g1=np.asarray(sm.filter(ImageFilter.GaussianBlur(3.5))).astype(np.float32)/255
        g2=np.asarray(sm.filter(ImageFilter.GaussianBlur(10))).astype(np.float32)/255
        prem=np.clip(g1[...,:3]*g1[...,3:]*2.3+g2[...,:3]*g2[...,3:]*1.7,0,1)
        prem=np.asarray(Image.fromarray((prem*255).astype(np.uint8)).resize((W,H),Image.BILINEAR)).astype(np.float32)/255
        b=np.asarray(im.convert('RGB')).astype(np.float32)/255
        im=Image.fromarray(((1-(1-b)*(1-prem))*255).astype(np.uint8)).convert('RGBA')
    furniture(im,t)
    if t<75.3: captions(im,t)     # CTA card carries the closing copy
    return im.convert('RGB')

def read_frames(n0,n1):
    p=subprocess.Popen(['ffmpeg','-v','error','-ss',f'{n0/FPS:.4f}','-i',SRC,'-frames:v',str(n1-n0),'-f','rawvideo','-pix_fmt','rgb24','-'],stdout=subprocess.PIPE)
    for n in range(n0,n1):
        buf=p.stdout.read(W*H*3)
        if len(buf)<W*H*3: break
        yield n,Image.frombuffer('RGB',(W,H),buf)
    p.kill()

if __name__=='__main__':
    if sys.argv[1]=='stills':
        os.makedirs(C.WD+'/qc',exist_ok=True)
        for ts in [float(x) for x in sys.argv[2:]]:
            subprocess.run(['ffmpeg','-v','error','-y','-ss',f'{ts:.3f}','-i',SRC,'-frames:v','1',C.WD+'/qc/_s.png'],check=True)
            frame(Image.open(C.WD+'/qc/_s.png').convert('RGB'),ts).resize((432,768)).save(C.WD+f'/qc/st_{ts:.2f}.jpg',quality=88)
        sys.exit()
    n0,n1,out=int(sys.argv[2]),int(sys.argv[3]),sys.argv[4]
    enc=subprocess.Popen(['ffmpeg','-v','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-','-an','-c:v','libx264','-crf','17','-preset','medium','-pix_fmt','yuv420p',out],stdin=subprocess.PIPE)
    for n,src in read_frames(n0,n1):
        enc.stdin.write(frame(src,n/FPS).tobytes())
    enc.stdin.close(); enc.wait(); print('done',n0,n1)
