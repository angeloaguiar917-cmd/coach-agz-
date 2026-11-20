import numpy as np, wave
SR=48000; DUR=109.633; n=int(SR*DUR); L=np.zeros(n); R=np.zeros(n)
rng=np.random.default_rng(7)
def _map(t):
        if a<=t<b: return None
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

def beep():
    m=int(SR*0.09); t=np.arange(m)/SR; y=np.sin(2*np.pi*1046*t)*np.minimum(1,t/0.004)*np.exp(-t*30); return y/np.max(np.abs(y))
hit=lambda t,g=-17: place(thud(1.4),t,gain=dB(g))
sw=lambda t,d=0.32: place(scan(d),t,gain=dB(-29))
tk=lambda t,g=-28: place(tick(),t,gain=dB(g))
imp=lambda t,g=-14: place(impact(),t,gain=dB(g))
wh=lambda t_land,d=0.3,g=-27: place(whoosh(d),t_land-d*0.7,gain=dB(g))
sw(7.80); tk(9.06,-27); tk(9.50,-25)
sw(11.40); tk(11.64,-31); tk(11.84,-31); hit(15.44,-19)
hit(16.40); tk(19.18,-27); wh(19.6,0.5,-30); hit(23.22,-18)
hit(28.20,-18); tk(28.72,-25)
for i in range(6): tk(29.86+i*0.06,-33)
wh(34.3,0.45,-30); tk(35.22,-25)
sw(35.95,0.4); tk(39.78,-27); imp(42.30)
wh(45.28,0.28); wh(48.32,0.28)
hit(49.70); place(thud(1.0),50.84,gain=dB(-17)); tk(53.42); tk(54.12); sw(54.56)
hit(59.30); tk(59.96,-25)
for i in range(4): tk(60.94+i*0.08,-32)
tk(66.16,-30); tk(67.62,-30); tk(70.27,-28); tk(71.25,-28); tk(72.78,-26)
hit(73.30); tk(76.68,-28); tk(78.88,-28); tk(80.24,-28)
sw(86.10,0.4)
k=0
while True:
    bt=86.10+(k*240+90)/320
    if bt>95.4: break
    place(beep(),bt,gain=dB(-36)); k+=1
hit(95.85)
for t_ in (100.84,101.52,102.62): tk(t_,-30)
place(thud(1.2),104.84,gain=dB(-16)); imp(104.84,-20)
out=np.stack([L,R],1); pk=np.max(np.abs(out)); print('sfx peak dBFS',20*np.log10(pk))
w=wave.open('sfx.wav','wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
w.writeframes((np.clip(out,-1,1)*32767).astype(np.int16).tobytes()); w.close()
