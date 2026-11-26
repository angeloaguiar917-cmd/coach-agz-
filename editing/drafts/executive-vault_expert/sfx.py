import numpy as np, wave
SR=48000; DUR=58.567; n=int(SR*DUR); L=np.zeros(n); R=np.zeros(n)
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
hit=lambda t,g=-17: place(thud(1.4),t,gain=dB(g))
sw=lambda t,d=0.32,g=-29: place(scan(d),t,gain=dB(g))
tk=lambda t,g=-28: place(tick(),t,gain=dB(g))
imp=lambda t,g=-14: place(impact(),t,gain=dB(g))
wh=lambda t,d=0.3,g=-27: place(whoosh(d),t-d*0.7,gain=dB(g))   # peak arrives on the landing
pp=lambda t,d=0.22,g=-31,pan=0: place(paper(d),t-d*0.5,pan,gain=dB(g))
tk(0.68,-30)                                         # punch-in on "anabolic"
pp(5.98,pan=-0.4); pp(7.94,pan=-0.1); pp(9.20,pan=0.2); pp(9.42,pan=0.4,g=-33); tk(10.58,-27)
sw(11.58,0.3); wh(12.26,0.25,-30)
tk(13.5,-32); tk(14.46,-27); imp(15.98)               # needle slams into GAMBLING
for k in range(8): tk(18.30+k*0.056,-36)
hit(18.75)
sw(21.84,0.62,-30); hit(22.46,-19)
pp(23.30); pp(23.38,g=-33); pp(24.54); wh(25.6,0.4,-28); imp(26.86,-15)
wh(27.45,0.25,-31)
for k in range(13): tk(28.34+k*0.115,-38)            # typing
tk(31.48,-27); tk(33.24,-27); tk(34.84,-27)
for t_ in (36.40,37.34,38.06,38.66): tk(t_,-29)
sw(39.80,0.25,-31); sw(41.06,0.5,-31)
wh(42.30,0.4,-26); hit(42.85,-21); place(marker(0.14),42.98,gain=dB(-27)); imp(44.02,-15)
wh(44.84,0.28,-29); pp(46.70,0.25,-30); hit(48.40,-18); wh(49.95,0.28,-29); hit(51.36,-20); tk(51.80,-26)
wh(53.20,0.4,-27); tk(54.48,-28); place(thud(1.2),55.04,gain=dB(-17)); wh(56.70,0.25,-31)
out=np.stack([L,R],1); pk=np.max(np.abs(out)); print('sfx peak dBFS',20*np.log10(pk))
w=wave.open('sfx.wav','wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
w.writeframes((np.clip(out,-1,1)*32767).astype(np.int16).tobytes()); w.close()
