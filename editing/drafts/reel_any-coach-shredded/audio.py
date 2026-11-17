import numpy as np, json, wave
SR=48000; TR=json.load(open('trim.json')); KEEP=TR['keep']; REM=TR['remove']
sp=np.fromfile('speech.f32',np.float32).reshape(-1,2).astype(np.float64)
XF=int(0.008*SR)
parts=[]
for a,b in KEEP:
    seg=sp[int(round(a*SR)):int(round(b*SR))].copy(); parts.append(seg)
out=parts[0]
for seg in parts[1:]:
    r=np.linspace(0,1,XF)[:,None]
    tail=out[-XF:]*(1-r)+seg[:XF]*r
    out=np.concatenate([out[:-XF],tail,seg[XF:]])
n=len(out); FX=np.zeros((n,2))
rng=np.random.default_rng(7)
def mp(t):
    for a,b in REM:
        if a<=t<b: return None
    return t-sum(min(b,t)-a for a,b in REM if a<t)
def place(sig,t,gain,pan=0):
    t=mp(t)
    if t is None: print('dropped',t); return
    i=int(t*SR); s=sig[:max(0,n-i)]*gain; FX[i:i+len(s),0]+=s*(1-max(0,pan)); FX[i:i+len(s),1]+=s*(1+min(0,pan))
def lp(x,a):
    y=np.zeros_like(x); acc=0
    for k in range(len(x)): acc+=a*(x[k]-acc); y[k]=acc
    return y
def thud(w=1.0):
    m=int(SR*0.35); t=np.arange(m)/SR; fr=55+60*np.exp(-t*28)
    y=np.sin(2*np.pi*np.cumsum(fr)/SR)*np.exp(-t*(14/w))+lp(rng.standard_normal(m),0.25)*np.exp(-t*160)*0.5; return y/np.abs(y).max()
def tick():
    m=int(SR*0.05); t=np.arange(m)/SR; y=np.sin(2*np.pi*2400*t)*np.exp(-t*140)+0.4*np.sin(2*np.pi*4100*t)*np.exp(-t*220); return y/np.abs(y).max()
def impact():
    m=int(SR*0.6); t=np.arange(m)/SR; fr=48+90*np.exp(-t*30)
    y=np.sin(2*np.pi*np.cumsum(fr)/SR)*np.exp(-t*7)+0.55*lp(rng.standard_normal(m),0.6)*np.exp(-t*45); return y/np.abs(y).max()
def scan(d):
    m=int(SR*d); t=np.arange(m)/SR; nz=rng.standard_normal(m); cut=0.05+0.35*(t/d); y=np.zeros(m); acc=0
    for k in range(m): acc+=cut[k]*(nz[k]-acc); y[k]=acc
    y=y-lp(y,0.08)+0.15*np.sin(2*np.pi*(900+1400*t/d)*t); e=np.minimum(1,t/0.03)*np.minimum(1,(d-t)/0.05); return y*e/np.abs(y*e).max()
def whoosh(d):
    m=int(SR*d); t=np.arange(m)/SR; nz=rng.standard_normal(m); cut=0.02+0.25*np.sin(np.pi*np.clip(t/d,0,1))**2; y=np.zeros(m); acc=0
    for k in range(m): acc+=cut[k]*(nz[k]-acc); y[k]=acc
    e=np.sin(np.pi*np.clip(t/d,0,1)**0.7)**2; return y*e/np.abs(y*e).max()
dB=lambda x:10**(x/20)
T=thud(1.4); TK=tick(); IM=impact()
hit=lambda t:place(T,t,dB(-18)); tk=lambda t,g=-30:place(TK,t,dB(g)); sw=lambda t,d=0.35:place(scan(d),t,dB(-30)); wh=lambda t,d=0.4:place(whoosh(d),t-d*0.7,dB(-27))
hit(2.0)
for t in (3.90,5.36,6.38,7.46,13.78,15.70): tk(t,-27)
tk(8.52); tk(10.36,-26)
wh(16.30); sw(16.9,1.6); tk(18.36); tk(20.04,-26)
wh(21.70,0.45); sw(22.1,0.5); [tk(t) for t in (24.52,26.76,29.26,30.48)]
hit(31.50); [tk(t,-31) for t in (31.88,32.78,33.24)]
wh(37.20,0.5); place(thud(1.0),38.98,dB(-19)); hit(40.2)
for t in (41.90,43.54,45.40,46.62,47.64,49.10,50.70,52.30): tk(t,-28)
place(IM,59.82,dB(-15)); wh(60.05,0.45)
hit(60.45); [tk(61.30+i*0.52,-33) for i in range(8)]; sw(67.36,0.4)
wh(69.42); [place(thud(0.9),t,dB(-21)) for t in (71.90,72.82,74.52)]; tk(75.90); sw(78.04,0.3)
hit(79.70); sw(85.66,2.3); place(thud(1.0),88.02,dB(-19)); tk(89.08,-26); tk(90.36,-26)
place(IM,92.88,dB(-14)); sw(93.36,0.18)
hit(94.80); sw(95.42,0.9); tk(99.48,-26)
wh(100.30,0.45); [place(thud(1.0),t,dB(-21)) for t in (105.00,105.74,106.86,109.22,112.12)]; tk(114.30)
place(thud(1.2),115.76,dB(-17))
mix=out+FX
import subprocess
mix.astype(np.float32).tofile('mix.f32'); print('dur',n/SR)
