import numpy as np, wave
SR=48000; DUR=95.6667; n=int(SR*DUR); L=np.zeros(n); R=np.zeros(n)
rng=np.random.default_rng(7)
import json as _j
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
hit=lambda t,g=-17: place(thud(1.4),t,gain=dB(g))
sw=lambda t,d=0.32,g=-29: place(scan(d),t,gain=dB(g))
tk=lambda t,g=-30: place(tick(),t,gain=dB(g))
imp=lambda t,g=-15: place(impact(),t,gain=dB(g))
wh=lambda tend,d=0.32,g=-27: place(whoosh(d),tend-d*0.7,gain=dB(g))
# S1 cadence grid
sw(3.20,0.28); hit(3.32,-21)
for i in range(7): tk(4.30+i*0.07,-35)
sw(6.28,0.5,-32)
for t in (7.70,8.64,9.52): tk(t,-30)
# S2 check-in form
wh(10.40,0.3,-28); tk(10.74); tk(11.02); tk(12.58,-33); tk(14.26,-32); imp(15.30,-16)
# S4/S5 radar -> bell curve
hit(21.85)
for t in (22.06,22.56,23.06,23.72,24.26): tk(t,-31)
sw(25.46,1.2,-31); wh(28.9,0.4,-29); tk(31.02,-28); sw(32.44,0.35); hit(35.06,-19)
# S6 monitor
tk(36.40,-26); sw(36.42,0.25,-30)
for t in (37.16,38.36,39.50): tk(t,-30)
# S7 dial
wh(40.98,0.36,-26); hit(40.98,-18); tk(41.76); tk(42.50); imp(44.88,-17)
# S8 split window + lab
wh(46.20,0.32,-28); hit(46.54,-22)
for i in range(4): tk(50.32+i*0.22,-32)
tk(52.64,-29); wh(53.69,0.3,-30); sw(55.70,0.45,-29); hit(57.24,-19)
# punch-in on "shit"
hit(61.84,-22)
# S10 dashboard
hit(65.35); tk(66.70,-28)
for i in range(4): tk(67.70+i*0.12,-31)
wh(69.77,0.3,-28); tk(69.82,-30); tk(73.64,-28); sw(75.64,0.8,-31); tk(78.0,-28)
# S11 for life
sw(81.40,0.6,-31)
for t in (81.60,86.04,86.70): tk(t,-28)
hit(88.38,-19)
# S12 CTA
imp(89.56,-15); tk(90.90,-27); tk(93.32,-29); hit(94.40,-17)
out=np.stack([L,R],1); pk=np.max(np.abs(out)); print('sfx peak dBFS',20*np.log10(pk))
w=wave.open('sfx.wav','wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
w.writeframes((np.clip(out,-1,1)*32767).astype(np.int16).tobytes()); w.close()
