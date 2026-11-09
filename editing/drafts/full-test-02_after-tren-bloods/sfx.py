import sys
import numpy as np, wave
SR=48000; DUR=102.4333; n=int(SR*DUR); L=np.zeros(n); R=np.zeros(n)
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
hit=lambda t,g=-17: place(thud(1.4),t,gain=dB(g))
sw=lambda t,d=0.32,g=-29: place(scan(d),t,gain=dB(g))
tk=lambda t,g=-28: place(tick(),t,gain=dB(g))
imp=lambda t,g=-14: place(impact(),t,gain=dB(g))
wh=lambda t_land,d=0.26,g=-28: place(whoosh(d),t_land-d*0.7,gain=dB(g))
# A. hook / cycle strip
hit(0.88,-22); wh(1.99); tk(2.0,-27); sw(2.56,0.7,-31); tk(4.24,-28); sw(4.24,0.45,-31)
# B. mirror HUD
sw(5.1,0.9,-29); tk(6.40); tk(6.88); tk(7.20); tk(8.96,-30); hit(10.96,-19); place(thud(1.0),11.76,gain=dB(-18))
# C1 / C2 evidence
wh(12.19); tk(13.6); tk(16.56)
hit(17.9); [tk(18.32+i*0.11,-34+i*0.6) for i in range(8)]; imp(19.24,-15); hit(21.68,-18)
# D axis
sw(22.62,0.3); tk(25.16,-26); wh(26.4,0.3); imp(28.29,-15)
# E HDL
wh(31.24); tk(32.2); place(thud(1.0),33.65,gain=dB(-19)); tk(34.3); tk(36.92); sw(38.84,0.4,-31)
# F ApoB
hit(40.5); tk(41.88); tk(43.19); place(thud(1.0),45.19,gain=dB(-19)); sw(46.78,0.4); hit(48.23,-19); tk(49.98)
# G hematocrit
wh(50.89); tk(52.78); tk(53.34); imp(53.91,-16); tk(55.91); tk(57.19); hit(58.70,-19); [tk(60.38+i*0.42,-33) for i in range(3)]
# H lab order / receptor
hit(62.55); place(paper(0.35),62.62,gain=dB(-30)); imp(64.55,-16); place(marker(0.3),66.70,gain=dB(-31)); sw(67.6,0.3); tk(68.86); tk(69.4); tk(71.34)
# I libido curve
wh(72.29); tk(77.03); hit(79.48,-19)
# J roadmap
hit(82.3); tk(85.17); tk(88.53); tk(89.56); tk(90.77); imp(92.0,-14)
# K CTA
wh(94.15); place(thud(1.2),98.66,gain=dB(-18))
out=np.stack([L,R],1); pk=np.max(np.abs(out)); print('sfx peak dBFS',20*np.log10(pk))
w=wave.open(sys.argv[1],'wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
w.writeframes((np.clip(out,-1,1)*32767).astype(np.int16).tobytes()); w.close()
