import numpy as np, wave
import json,sys
S=sys.argv[1]; TL=json.load(open(S+'/build/timeline.json')); KEEP=TL['keep']
SR=48000; DUR=TL['dur']+0.5; n=int(SR*DUR); L=np.zeros(n); R=np.zeros(n)
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

def scan(d):   # scanner sweep: band-limited noise with rising centre + faint carrier
    m=int(SR*d); t=np.arange(m)/SR; nz=rng.standard_normal(m)
    cut=0.05+0.35*(t/d); y=np.zeros(m); acc=0
    for k in range(m): acc+=cut[k]*(nz[k]-acc); y[k]=acc
    y=y-lp(y,0.08)+0.15*np.sin(2*np.pi*(900+1400*t/d)*t)
    env=np.minimum(1,t/0.03)*np.minimum(1,(d-t)/0.05)
    return y*env/np.max(np.abs(y*env))
dB=lambda x:10**(x/20)
def c(t):
    o=0
    for a,b in KEEP:
        if t<a: return o
        if t<=b: return o+t-a
        o+=b-a
    return o
hit=lambda t,g=-17: place(thud(1.4),c(t),gain=dB(g))
sw=lambda t,d=0.32,g=-29: place(scan(d),c(t),gain=dB(g))
tk=lambda t,g=-28: place(tick(),c(t),gain=dB(g))
imp=lambda t,g=-15: place(impact(),c(t),gain=dB(g))
wh=lambda t,d=0.38: place(whoosh(d),max(0,c(t)-d*0.7),gain=dB(-27))
# lineup + hook
for t in (3.4,4.0,4.7): tk(t,-27)
sw(6.7,0.9,-31)
# split: cypionate dossier
wh(9.83); hit(9.83); imp(11.9,-19); sw(14.2,0.5); tk(16.4); hit(19.1,-19); tk(21.0,-26)
# takeover chart
wh(22.38); hit(22.38); sw(27.7,0.9,-31); sw(28.7,0.9,-31); sw(31.2,0.9,-30); tk(34.8,-27)
# side rail
wh(38.16); hit(38.16); hit(40.2,-20); sw(41.3,0.4); tk(44.6); tk(49.4,-30); tk(49.8,-30); tk(52.7,-27)
# propionate takeover
wh(54.58); hit(54.58); sw(57.8,0.7); imp(58.3,-18); hit(59.1,-18)
for i in range(3): tk(61.2+0.18*i+0.3,-29)
imp(62.0,-17)
# trough monitor
sw(63.6,0.5); tk(68.5,-26); place(thud(0.7),c(69.6),gain=dB(-17)); imp(70.1,-16)
# molecule + table
hit(71.2,-19); tk(74.1,-24); hit(75.6,-19); sw(77.0,0.35)
for i in range(3): tk(77.1+0.25*i,-30)
# selector + verdict
tk(81.1,-31); tk(81.9,-31); imp(83.0,-16)
# streak
sw(84.6,1.2,-33); tk(87.1,-27)
# CTA
hit(88.75); 
for i in range(3): tk(89.5+0.12*i,-29)
imp(91.1,-15)
out=np.stack([L,R],1); pk=np.max(np.abs(out)); print('sfx peak dBFS',20*np.log10(pk))
w=wave.open(S+'/build/sfx.wav','wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
w.writeframes((np.clip(out,-1,1)*32767).astype(np.int16).tobytes()); w.close()
