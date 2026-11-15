import numpy as np, wave
SR=48000; DUR=110.40; n=int(SR*DUR); L=np.zeros(n); R=np.zeros(n)
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

    m=int(SR*0.12); t=np.arange(m)/SR
    y=np.sin(2*np.pi*(420+300*np.exp(-t*60))*t)*np.exp(-t*45)+0.3*lp(rng.standard_normal(m),0.5)*np.exp(-t*120)
    return y/np.max(np.abs(y))
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

W_=[(17.25,0.32),(20.9,0.4),(33.65,0.4),(49.85,0.4),(56.6,0.35),(66.35,0.3),(69.43,0.35),(73.95,0.4),(88.93,0.3),(89.15,0.4),(103.93,0.3)]
for t,d in W_: place(whoosh(d),t-d*0.7,0.0,dB(-20))
place(paper(0.35),82.85,0.3,dB(-20))
for t,d in [(14.95,0.4),(15.35,0.85),(58.8,0.6),(70.0,1.2),(75.8,0.5),(89.5,1.4),(104.3,0.6),(108.86,0.6)]: place(scan(d),t,0.0,dB(-27))
for t in [17.48,18.02,21.18,26.68,30.06,28.36,37.62,40.2,46.46,42.24,42.88,43.54,48.7,83.62,84.42,86.18,86.6,87.46,88.16,100.1,100.42,102.88,64.82,65.62,69.66,72.2,73.58,91.84,92.1,92.4,104.3,104.42,104.54,104.66,105.1,106.98]:
    place(tick(),t,0.15,dB(-24))
for t,w in [(16.16,0.8),(19.94,0.8),(22.16,1.0),(35.7,0.8),(53.36,1.0),(69.1,0.9),(77.68,1.1),(80.25,0.7),(97.08,0.7),(109.5,0.8),(61.56,0.8)]: place(thud(w),t,0.0,dB(-17))
for t in [55.72,76.3,81.82,93.84]: place(impact(),t,0.0,dB(-14))
st=np.stack([L,R],1); st=st/max(1.0,np.max(np.abs(st)))*0.9
with wave.open('sfx.wav','w') as wf:
    wf.setnchannels(2); wf.setsampwidth(2); wf.setframerate(SR); wf.writeframes((st*32767).astype(np.int16).tobytes())
print('sfx ok')
