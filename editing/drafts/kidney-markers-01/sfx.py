import numpy as np, wave
SR=48000; DUR=78.70; n=int(SR*DUR); L=np.zeros(n); R=np.zeros(n)
rng=np.random.default_rng(7)
def _map(t): return t
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

hit=lambda t,g=-18: place(thud(1.3),t,gain=dB(g))
sw=lambda t,d=0.32,g=-29: place(scan(d),t,gain=dB(g))
tk=lambda t,g=-28: place(tick(),t,gain=dB(g))
imp=lambda t,g=-15: place(impact(),t,gain=dB(g))
wh=lambda t_land,d=0.35,g=-27: place(whoosh(d),max(0,t_land-d),gain=dB(g))
imp(1.60,-17)
hit(10.80); tk(11.38); tk(14.44,-30); tk(14.88)
wh(15.75); tk(15.50,-32); tk(16.46,-32); tk(17.90,-32); sw(18.42,0.4)
for t in (21.40,22.16,23.00): hit(t+0.12,-23)
tk(24.30); tk(27.50)
wh(28.53,0.38); tk(29.44,-31); tk(31.92); sw(32.0,1.6,-31); imp(33.56)
hit(36.44,-24)
hit(37.45,-21); tk(39.90)
wh(40.90,0.4); [tk(t,-30) for t in (41.06,42.12,44.60,45.56)]
wh(47.02,0.4); sw(49.0,1.6,-31); tk(50.38,-30)
wh(51.64,0.28,-28); sw(51.9,0.7); tk(52.62); tk(53.56)
hit(54.35,-21); wh(55.58,0.9,-29); tk(57.62)
hit(59.62,-20); tk(60.50); tk(61.9,-31); imp(64.90,-16); tk(67.40); tk(67.56,-30)
hit(68.10,-21); sw(68.94,0.6); tk(70.78)
hit(71.60,-20); [tk(74.30+0.11*i,-33) for i in range(6)]; place(thud(1.2),74.76,gain=dB(-16))
out=np.stack([L,R],1); pk=np.max(np.abs(out)); print('sfx peak dBFS',20*np.log10(pk))
w=wave.open('sfx.wav','wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
w.writeframes((np.clip(out,-1,1)*32767).astype(np.int16).tobytes()); w.close()
