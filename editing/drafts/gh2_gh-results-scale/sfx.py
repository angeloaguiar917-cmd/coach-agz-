import sys
OUT=sys.argv[1]
import numpy as np, wave
SR=48000; DUR=106.534; n=int(SR*DUR); L=np.zeros(n); R=np.zeros(n)
rng=np.random.default_rng(7)
_TR=[]
def _map(t):
    for a,b in _TR:
        if a<=t<b: return None
    return t-sum(min(b,t)-a for a,b in _TR if a<t)
def place(sig,t,pan=0.0,gain=1.0):
    t=_map(t)
    if t is None: print('SFX dropped (inside cut)'); return
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
hit=lambda t: place(thud(1.4),t,gain=dB(-17))
card=lambda t,g=-19: place(thud(1.0),t,gain=dB(g))
sw=lambda t,d=0.5,g=-29: place(scan(d),t,gain=dB(g))
tk=lambda t,g=-28: place(tick(),t,gain=dB(g))
imp=lambda t: place(impact(),t,gain=dB(-14))
wh=lambda t_land,d=0.32,g=-26: place(whoosh(d),t_land-d*0.7,gain=dB(g))
card(6.92); tk(7.62,-26); tk(8.56,-30)
hit(9.4667); sw(9.9,0.6); tk(12.54); tk(16.06,-26)
wh(16.86); tk(17.08); tk(18.76,-26); tk(21.16)
card(22.38); tk(24.96,-26); card(26.44,-21); sw(26.5,0.8,-31)
hit(30.30); tk(30.6); tk(31.62); place(thud(1.2),33.98,gain=dB(-18)); tk(35.12,-31); tk(36.74,-31); tk(38.38)
hit(45.30); tk(46.3,-26); wh(47.6,0.3,-28); sw(50.06,0.6); tk(52.38); tk(54.0); imp(55.70)
hit(56.06); sw(56.2,1.2,-31); tk(59.38); wh(62.6,0.4,-26); imp(65.52)
hit(66.62)
for t in (68.42,69.64,70.72,72.32,72.90,73.40,73.90): tk(t,-32)
tk(75.34,-26); tk(76.08,-24)
wh(77.07,0.35,-24)
for t in (79.96,83.60,84.56,85.18,85.82,86.60): tk(t,-32)
for t in (81.48,88.42): place(thud(0.8),t,gain=dB(-23))
wh(89.40,0.25,-28); card(89.66,-20); place(thud(1.4),91.94,gain=dB(-16))
wh(95.54,0.3,-27)
for t in (95.72,97.54,98.66,99.52): tk(t,-28)
card(100.65); place(thud(1.2),102.80,gain=dB(-17))
out=np.stack([L,R],1); pk=np.max(np.abs(out)); print('sfx peak dBFS',20*np.log10(pk))
w=wave.open(OUT,'wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
w.writeframes((np.clip(out,-1,1)*32767).astype(np.int16).tobytes()); w.close()
