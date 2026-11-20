# Synthesised clinical SFX bed for the heart-health edit. usage: python3 sfx.py <workdir>  -> <workdir>/sfx.wav (48k stereo float)
import numpy as np, sys, subprocess
WD=sys.argv[1]; SR=48000; DUR=115.9
rng=np.random.default_rng(7)
def env(n,a=0.002,d=0.2):
    t=np.arange(n)/SR; return np.minimum(1,t/a)*np.exp(-t/d)
def sub(dur=0.6,f0=58,amp=0.55):
    n=int(dur*SR); t=np.arange(n)/SR; f=f0*(1+1.6*np.exp(-t/0.03))
    return amp*np.sin(2*np.pi*np.cumsum(f)/SR)*env(n,0.001,0.18)
def click(amp=0.25):
    n=int(0.012*SR); return amp*rng.standard_normal(n)*env(n,0.0005,0.002)
def impact(amp=0.7):
    a=sub(0.8,52,amp); n=int(0.25*SR); nz=rng.standard_normal(n); nz=np.convolve(nz,np.ones(18)/18,'same')*env(n,0.001,0.04)*amp*0.9
    a[:n]+=nz; a[:len(click())]+=click(0.35); return a
def tick(f=2400,amp=0.16,dur=0.035):
    n=int(dur*SR); t=np.arange(n)/SR; return amp*np.sin(2*np.pi*f*t)*env(n,0.0008,0.008)
def sweep(dur=0.45,f0=300,f1=3200,amp=0.12):
    n=int(dur*SR); t=np.arange(n)/SR; nz=rng.standard_normal(n)
    fc=f0*(f1/f0)**(t/dur); out=np.zeros(n); y1=y2=0.0
    # simple resonant band-pass sweep
    for i in range(n):
        w=2*np.pi*fc[i]/SR; r=0.985; a1=-2*r*np.cos(w); a2=r*r
        y=nz[i]*(1-r)-a1*y1-a2*y2; y2=y1; y1=y; out[i]=y
    out/=np.max(np.abs(out))+1e-9
    e=np.sin(np.pi*np.clip(t/dur,0,1))**1.5
    return amp*out*e
def beep(f=1000,dur=0.09,amp=0.09):
    n=int(dur*SR); t=np.arange(n)/SR; return amp*np.sin(2*np.pi*f*t)*np.minimum(1,np.minimum(t/0.004,(dur-t)/0.01))
def flat(dur=0.65,amp=0.08):
    n=int(dur*SR); t=np.arange(n)/SR; return amp*np.sin(2*np.pi*1000*t)*np.minimum(1,t/0.004)*np.clip((dur-t)/0.25,0,1)
def whoosh(dur=0.35,amp=0.14):
    n=int(dur*SR); t=np.arange(n)/SR; nz=np.convolve(rng.standard_normal(n),np.ones(30)/30,'same')
    return amp*3*nz*np.sin(np.pi*t/dur)**2
EV=[]
def at(t,x,pan=0.0): EV.append((t,x,pan))
at(0.70,sub(0.5,60,0.45))
at(3.22,sweep(0.3,500,2600,0.08),-0.4)
for tt in (3.44,4.16): at(tt,tick(2600,0.12),-0.4)
for tt in (5.06,5.72): at(tt,tick(900,0.18),-0.4)
at(6.68,sub(0.4,70,0.35))
k=0
while True:
    tt=(k+0.5)/1.15; k+=1
    if tt<8.6: continue
    if tt>=11.0: break
    at(tt,beep())
at(11.0,flat())
for tt in (12.32,12.54): at(tt,tick(1800,0.14))
for tt in (16.48,17.36,18.36): at(tt,tick(2400,0.12))
at(19.02,impact(0.6)); at(44.50,impact(0.6))
at(20.85,sweep(0.4,250,2800,0.10))   # lift in
at(22.30,sub(0.6,48,0.55)); at(24.78,sweep(0.5,400,2400,0.08),0.2); at(25.48,tick(2000,0.14),0.4)
at(25.80,sweep(0.35,600,3600,0.08)); at(29.38,tick(2400,0.12)); at(29.70,tick(1600,0.14))
at(29.95,sweep(0.45,3000,300,0.10)); at(31.20,tick(3000,0.12),-0.3); at(32.18,impact(0.55)); at(38.70,sweep(0.4,300,2000,0.08),0.4)
at(41.54,sub(0.35,80,0.3)); at(42.62,sub(0.35,80,0.3)); at(43.92,tick(2600,0.1))
at(47.75,sweep(0.4,250,2800,0.10)); at(48.44,tick(1200,0.16),-0.3); at(52.06,sub(0.6,50,0.5)); at(52.2,tick(900,0.14),0.4)
at(54.55,whoosh(0.32,0.12),0.5); at(57.46,impact(0.75))
at(58.45,sweep(0.45,3000,300,0.10)); at(58.72,impact(0.5)); at(59.6,tick(1000,0.14),0.3); at(62.72,sweep(0.6,2000,250,0.08)); at(63.74,tick(700,0.14))
at(64.75,whoosh(0.3,0.16),-0.4); at(66.74,sweep(0.45,1500,4000,0.05)); at(68.38,sweep(0.8,1500,4000,0.06)); at(68.5,tick(2400,0.12))
at(70.74,sub(0.6,55,0.5))
for tt in (73.92,76.62,79.24): at(tt,tick(2000,0.14),-0.4)
at(80.05,sweep(0.4,250,2800,0.10)); at(82.06,tick(2200,0.12),-0.3); at(84.42,tick(2200,0.12),0.3)
for tt in (83.18,85.64): at(tt,tick(3000,0.09))
at(89.40,sweep(0.3,500,2600,0.08),-0.4); at(93.16,impact(0.5))
for tt in (99.5,99.75,100.0): at(tt,tick(3200,0.06,0.02),-0.4)
at(103.35,sweep(0.45,250,2800,0.10))
for tt in (107.66,108.30,109.44): at(tt,tick(2400,0.12))
at(111.68,impact(0.8))
N=int(DUR*SR)+SR; out=np.zeros((N,2))
for t,x,pan in EV:
    i=int(t*SR); x=x[:N-i]; l=np.sqrt((1-pan)/2); r=np.sqrt((1+pan)/2)
    out[i:i+len(x),0]+=x*l*1.2; out[i:i+len(x),1]+=x*r*1.2
out=out[:int(DUR*SR)].astype(np.float32)
out.tofile(WD+'/sfx.f32')
subprocess.run(['ffmpeg','-v','error','-y','-f','f32le','-ar','48000','-ac','2','-i',WD+'/sfx.f32',WD+'/sfx.wav'],check=True)
print(len(EV),'events')
