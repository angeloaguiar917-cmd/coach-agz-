import sys
import numpy as np, wave
SR=48000; DUR=102.50; n=int(SR*DUR); L=np.zeros(n); R=np.zeros(n)
rng=np.random.default_rng(7)
def place(sig,t,pan=0.0,gain=1.0):
    i=int(t*SR); s=sig[:max(0,n-i)]*gain
    L[i:i+len(s)]+=s*(1-max(0,pan)); R[i:i+len(s)]+=s*(1+min(0,pan))
def lp(x,a):  # one-pole lowpass
    y=np.zeros_like(x); acc=0
    for k in range(len(x)): acc+= a*(x[k]-acc); y[k]=acc
    return y
def whoosh(d):
    m=int(SR*d); t=np.arange(m)/SR; nz=rng.standard_normal(m)
    # sweep: brighten then darken, envelope peaks at 70% (arrives into the landing)
    cut=0.02+0.25*np.sin(np.pi*np.clip(t/d,0,1))**2
    y=np.zeros(m); acc=0
    for k in range(m): acc+=cut[k]*(nz[k]-acc); y[k]=acc
    env=np.sin(np.pi*np.clip(t/d,0,1)**0.7)**2
    return y*env/np.max(np.abs(y*env))
def thud(weight=1.0):
    m=int(SR*0.35); t=np.arange(m)/SR
    f=55+60*np.exp(-t*28)                     # pitch drop = mass
    body=np.sin(2*np.pi*np.cumsum(f)/SR)*np.exp(-t*(14/weight))
    click=lp(rng.standard_normal(m),0.25)*np.exp(-t*160)*0.5
    y=body+click; return y/np.max(np.abs(y))
def tick():
    m=int(SR*0.05); t=np.arange(m)/SR
    y=np.sin(2*np.pi*2400*t)*np.exp(-t*140)+0.4*np.sin(2*np.pi*4100*t)*np.exp(-t*220)
    return y/np.max(np.abs(y))
def impact():
    m=int(SR*0.6); t=np.arange(m)/SR
    f=48+90*np.exp(-t*30); body=np.sin(2*np.pi*np.cumsum(f)/SR)*np.exp(-t*7)
    crack=lp(rng.standard_normal(m),0.6)*np.exp(-t*45)
    y=body+0.55*crack; return y/np.max(np.abs(y))

def tock():   # light plastic bottle set down
    m=int(SR*0.12); t=np.arange(m)/SR
    y=np.sin(2*np.pi*(420+300*np.exp(-t*60))*t)*np.exp(-t*45)+0.3*lp(rng.standard_normal(m),0.5)*np.exp(-t*120)
    return y/np.max(np.abs(y))
def clink():  # small glass vials: inharmonic partials
    m=int(SR*0.5); t=np.arange(m)/SR; y=np.zeros(m)
    for fr,dc,a in [(3150,9,1),(4870,13,.6),(6920,18,.4),(2210,7,.35)]: y+=a*np.sin(2*np.pi*fr*t)*np.exp(-t*dc)
    y2=np.zeros(m); off=int(SR*0.07); y2[off:]=y[:m-off]*0.6
    return (y+y2)/np.max(np.abs(y+y2))
def paper(d):  # paper slide: bright soft noise swell
    m=int(SR*d); t=np.arange(m)/SR; nz=rng.standard_normal(m)
    hp=nz-lp(nz,0.15); env=np.sin(np.pi*np.clip(t/d,0,1))**1.5
    return hp*env/np.max(np.abs(hp*env))
def marker(d):
    m=int(SR*d); t=np.arange(m)/SR; nz=lp(rng.standard_normal(m),0.35)
    env=np.minimum(1,t/0.02)*np.exp(-np.maximum(0,t-d*0.6)*30)
    return nz*env/np.max(np.abs(nz*env))

def scan(d):   # scanner sweep: band-limited noise with rising centre + faint carrier
    m=int(SR*d); t=np.arange(m)/SR; nz=rng.standard_normal(m)
    cut=0.05+0.35*(t/d); y=np.zeros(m); acc=0
    for k in range(m): acc+=cut[k]*(nz[k]-acc); y[k]=acc
    y=y-lp(y,0.08)+0.15*np.sin(2*np.pi*(900+1400*t/d)*t)
    env=np.minimum(1,t/0.03)*np.minimum(1,(d-t)/0.05)
    return y*env/np.max(np.abs(y*env))
dB=lambda x:10**(x/20)
hit=lambda t,g=-18: place(thud(1.4),t,gain=dB(g))
sw=lambda t,d=0.32,g=-29: place(scan(d),t,gain=dB(g))
tk=lambda t,g=-29: place(tick(),t,gain=dB(g))
imp=lambda t,g=-15: place(impact(),t,gain=dB(g))
wh=lambda t,d=0.4,g=-28: place(whoosh(d),max(0,t-d*0.7),gain=dB(g))
for t in (6.30,14.16,27.66,66.42,73.70,93.38): wh(t+0.4); hit(t+0.4,-19)
hit(47.24,-20); hit(86.58,-22); hit(90.0,-22)
for t in (11.62,12.88,13.86,18.58,19.12,23.74,37.96,38.38,38.92,40.30,43.74,53.92,54.58,55.28,60.96,62.22,63.32,67.52,68.64,71.50,75.10,75.90,90.14,91.18,92.44): tk(t)
for k in range(9): tk(34.2+k*1.3/9,-33)
sw(7.92,1.5,-31); sw(30.88,1.0,-29); sw(49.6,1.4,-32); sw(80.9,1.8,-32)
place(thud(1.0),33.30,gain=dB(-19)); place(thud(1.0),36.24,gain=dB(-21)); place(thud(1.0),9.42,gain=dB(-20))
imp(65.80); imp(82.72,-16); place(thud(1.2),98.68,gain=dB(-17)); imp(51.6,-19)
out=np.stack([L,R],1); pk=np.max(np.abs(out)); print('sfx peak dBFS',20*np.log10(pk))
w=wave.open(sys.argv[1],'wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
w.writeframes((np.clip(out,-1,1)*32767).astype(np.int16).tobytes()); w.close()
