import numpy as np, wave
import json
import os; K=json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'trim.json')))['keep']
SR=48000; DUR=sum(b-a for a,b in K); n=int(SR*DUR); L=np.zeros(n); R=np.zeros(n)
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
def scan(d):
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
imp=lambda t: place(impact(),t,gain=dB(-14))
wh=lambda t,d=0.3: place(whoosh(d),t-d*0.7,gain=dB(-27))
# S1 line chart
hit(7.95); tk(12.7); tk(14.30,-24); tk(15.38); tk(16.00); sw(17.6,0.5); tk(19.12,-25)
# S2 clinic note + stamp
wh(19.95); [tk(x,-32) for x in (20.05,21.26,21.86)]; tk(23.58); imp(24.95)
# S3 scan
hit(25.58); sw(25.6,0.9); tk(29.1); tk(30.62); tk(35.0); [tk(38.40+i*0.07,-31) for i in range(5)]; tk(40.96,-24); tk(41.34)
# case files
[tk(43.25+0.18*i+(0.25 if i>=2 else 0),-33) for i in range(5)]; tk(44.18,-26)
# S4 dose chart
hit(45.65); place(thud(1.0),46.62,gain=dB(-21)); place(thud(1.0),49.60,gain=dB(-20)); tk(51.42); sw(53.4,0.6); tk(56.52); tk(57.74,-24)
# S5 loop
hit(59.66); tk(62.30,-26); imp(64.30)
# S6 roadmap -> S7 lab
hit(65.08); [tk(x) for x in (66.24,67.76,70.16,72.66,73.66,74.14)]; wh(75.05,0.28)
[tk(x,-31) for x in (75.40,75.52,75.64,75.76,75.88)]; tk(76.92,-25); tk(77.58,-26)
# S8 comparison
hit(78.90); tk(81.68); tk(84.0); tk(85.70); tk(87.64); place(thud(1.1),89.30,gain=dB(-19))
# CTA
hit(91.50); place(thud(1.3),94.40,gain=dB(-17))
out=np.stack([L,R],1); pk=np.max(np.abs(out)); print('sfx peak dBFS',20*np.log10(pk))
w=wave.open('sfx.wav','wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
w.writeframes((np.clip(out,-1,1)*32767).astype(np.int16).tobytes()); w.close()
