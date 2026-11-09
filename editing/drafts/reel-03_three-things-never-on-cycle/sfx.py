import numpy as np, wave
SR=48000; DUR=99.367; n=int(SR*DUR); L=np.zeros(n); R=np.zeros(n)
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
hit=lambda t: place(thud(1.4),t,gain=dB(-17))
sw=lambda t,d=0.32: place(scan(d),t,gain=dB(-29))
tk=lambda t,g=-28: place(tick(),t,gain=dB(g))
imp=lambda t,g=-14: place(impact(),t,gain=dB(g))
wh=lambda t,d=0.35,g=-27: place(whoosh(d),t-d*0.7,gain=dB(g))   # whoosh peaks into the landing
# 0-12 hook + year log
wh(4.30,0.3); sw(5.60,0.75); imp(7.58,-17); tk(9.56,-26)
# bumpers
for t in (12.24,25.02,57.22): wh(t,0.25,-25); imp(t)
place(thud(1.0),27.94,gain=dB(-17)); tk(26.36); tk(27.16,-30); tk(27.56); tk(58.42,-30); tk(59.62,-26)
# 01 bars
hit(15.70); sw(19.24,0.45); tk(20.24); tk(22.08,-30); place(thud(1.0),23.96,gain=dB(-19))
# 02 hub
sw(29.62,0.3)
for t in (31.36,31.84,32.46,33.28,35.74): tk(t,-29)
# split: spectrum, AI stack, crash, trend
wh(36.40,0.36); tk(37.34,-30); tk(39.0,-26); tk(41.20,-25); tk(41.40,-25)
for t in (42.40,42.84,43.20,43.62): tk(t,-27)
wh(44.58+0.3,0.3,-24); place(thud(1.2),44.88,gain=dB(-18)); tk(46.18,-28); tk(47.10,-26)
sw(48.40,0.3); sw(52.38,1.0); tk(54.62,-30); tk(55.88,-28)
# 03 hematocrit
hit(63.30); sw(63.62,0.45); imp(64.07,-15); tk(65.68,-26)
for t in (66.70,67.34,68.76,69.64): tk(t,-28)
tk(69.96,-30); sw(71.24,0.8)
# push-aside ladder
wh(72.50,0.34); 
for t in (72.66,73.30,74.06): tk(t,-27)
tk(75.66,-26); place(thud(1.1),77.72,gain=dB(-18)); tk(79.30,-30); imp(79.90,-16)
# roadmap
hit(80.56); tk(82.36,-26); place(thud(0.8),83.42,gain=dB(-21)); sw(84.66,0.9); tk(85.84,-25)
# CTA
wh(86.24,0.3); place(thud(1.2),87.36,gain=dB(-17))
for t in (91.78,92.53,93.26): tk(t,-29)
out=np.stack([L,R],1); pk=np.max(np.abs(out)); print('sfx peak dBFS',20*np.log10(pk))
w=wave.open('sfx.wav','wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
w.writeframes((np.clip(out,-1,1)*32767).astype(np.int16).tobytes()); w.close()
