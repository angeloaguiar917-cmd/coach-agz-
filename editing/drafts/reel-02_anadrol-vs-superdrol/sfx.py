# SFX bed for reel 02 (clinical: sub thuds on landings, ticks on rows, scan sweeps, heavy impacts)
# usage: python3 -I sfx.py <scratch>   -> writes <scratch>/out/sfx.wav (new timeline)
import sys, json, numpy as np, wave
HERE=__file__.rsplit('/',1)[0]; S=sys.argv[1]
TR=json.load(open(HERE+'/trim.json')); K=TR['keep']; DUR=TR['dur_new']
SR=48000; n=int(SR*(DUR+0.3)); L=np.zeros(n); R=np.zeros(n)
rng=np.random.default_rng(11)
def old_to_new(to):
    acc=0
    for a,b in K:
        if to<b: return acc+max(0,to-a)
        acc+=b-a
    return acc
def lp(x,a):
    y=np.zeros_like(x); acc=0.0
    for k in range(len(x)): acc+=a*(x[k]-acc); y[k]=acc
    return y
def place(sig,t,pan=0.0,g=1.0):
    i=int(t*SR); s=sig[:max(0,n-i)]*g
    L[i:i+len(s)]+=s*(1-max(0,pan)); R[i:i+len(s)]+=s*(1+min(0,pan))
def thud(weight=1.0,g=1.0):
    m=int(SR*0.34); t=np.arange(m)/SR; fr=54+58*np.exp(-t*26)
    body=np.sin(2*np.pi*np.cumsum(fr)/SR)*np.exp(-t*(13/weight))
    click=lp(rng.standard_normal(m),0.25)*np.exp(-t*150)*0.45
    y=body+click; return y/np.max(np.abs(y))*g
def impact(g=1.0):
    m=int(SR*0.6); t=np.arange(m)/SR; fr=46+92*np.exp(-t*30)
    body=np.sin(2*np.pi*np.cumsum(fr)/SR)*np.exp(-t*7)
    crack=lp(rng.standard_normal(m),0.6)*np.exp(-t*42)
    y=body+0.5*crack; return y/np.max(np.abs(y))*g
def tick(g=1.0):
    m=int(SR*0.045); t=np.arange(m)/SR
    y=np.sin(2*np.pi*2300*t)*np.exp(-t*150)+0.4*np.sin(2*np.pi*4000*t)*np.exp(-t*230)
    return y/np.max(np.abs(y))*g
def scan(d,g=1.0):
    m=int(SR*d); t=np.arange(m)/SR; nz=rng.standard_normal(m)
    cut=0.05+0.33*(t/d); y=np.zeros(m); acc=0.0
    for k in range(m): acc+=cut[k]*(nz[k]-acc); y[k]=acc
    y=y-lp(y,0.08)+0.12*np.sin(2*np.pi*(850+1500*t/d)*t)
    env=np.minimum(1,t/0.03)*np.minimum(1,(d-t)/0.05)
    return y*env/np.max(np.abs(y*env))*g
def whoosh(d,g=1.0):
    m=int(SR*d); t=np.arange(m)/SR; nz=rng.standard_normal(m)
    cut=0.02+0.22*np.sin(np.pi*np.clip(t/d,0,1))**2; y=np.zeros(m); acc=0.0
    for k in range(m): acc+=cut[k]*(nz[k]-acc); y[k]=acc
    env=np.sin(np.pi*np.clip(t/d,0,1)**0.7)**2
    return y*env/np.max(np.abs(y*env))*g
dB=lambda x:10**(x/20)
# (raw_time, fn) ; levels chosen to sit under speech
TH=dB(-15); TK=dB(-21); IM=dB(-11); SC=dB(-20); WH=dB(-22)
EV=[]
def add(tr,sig): EV.append((old_to_new(tr),sig))
# S1
add(1.80,thud(1.3,TH)); add(2.55,scan(0.9,SC)); add(5.0,scan(1.2,SC*0.8)); add(3.25,tick(TK))
# S2
add(12.86,thud(1,TH)); add(14.12,tick(TK)); add(14.48,tick(TK*1.2)); add(15.16,thud(1,TH)); add(16.40,tick(TK))
add(17.10,scan(0.7,SC)); add(17.36,tick(TK)); add(17.82,tick(TK)); add(18.24,tick(TK))
# S3
for i in range(10): add(19.62+i*0.18,tick(TK*0.8))
add(21.55,impact(IM*0.8)); add(22.04,whoosh(0.5,WH))
for i in range(6): add(22.5+i*0.12,tick(TK*0.7))
add(23.7,thud(1,TH))
# S4
add(25.08,thud(1,TH)); add(26.04,tick(TK*1.1)); add(28.08,tick(TK*1.1)); add(28.4,thud(1.2,TH))
# S5
add(31.90,thud(1,TH)); add(33.44,tick(TK)); add(33.92,tick(TK)); add(34.46,tick(TK))
add(37.42,thud(1,TH)); add(38.06,whoosh(0.4,WH)); add(40.96,impact(IM*0.9)); add(42.70,tick(TK*1.2))
# S6
for tt in (46.26,46.96,47.28,48.00): add(tt,tick(TK))
add(48.98,whoosh(0.4,WH)); add(49.78,scan(1.2,SC))
# S7 (gauges)
for tt in (54.60,57.92,58.52): add(tt,scan(0.5,SC*0.9))
# S8
add(60.10,whoosh(0.4,WH)); add(66.56,whoosh(0.4,WH))
for tt in (60.96,62.56,63.50,67.22,68.40,69.24): add(tt,tick(TK*0.9))
add(65.0,thud(1,TH)); add(71.02,thud(1,TH))
# S9
for tt in (73.74,74.08,74.38): add(tt,tick(TK))
add(75.54,impact(IM))
# S10
add(80.72,impact(IM*1.05)); add(84.82,tick(TK*1.2))
# S11
add(86.60,thud(1.1,TH)); add(92.34,impact(IM*0.9))
for tn,sig in EV: place(sig,tn)
mx=max(np.max(np.abs(L)),np.max(np.abs(R)),1e-6)
if mx>0.95: L*=0.95/mx; R*=0.95/mx
st=np.stack([L,R],1); pcm=(np.clip(st,-1,1)*32767).astype('<i2')
w=wave.open(S+'/out/sfx.wav','w'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes()); w.close()
print('sfx events',len(EV),'dur',round(DUR,2))
