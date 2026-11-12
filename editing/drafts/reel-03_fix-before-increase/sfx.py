import numpy as np, wave, sys
SR=48000; DUR=79.7334; n=int(SR*DUR); L=np.zeros(n); R=np.zeros(n)
rng=np.random.default_rng(7)
def place(sig,t,gain=1.0):
    i=int(t*SR); s=sig[:max(0,n-i)]*gain; L[i:i+len(s)]+=s; R[i:i+len(s)]+=s
def lpf(x,a):
    y=np.zeros_like(x); acc=0
    for k in range(len(x)): acc+=a*(x[k]-acc); y[k]=acc
    return y
def thud(weight=1.0):
    m=int(SR*0.35); t=np.arange(m)/SR; f=55+60*np.exp(-t*28)
    y=np.sin(2*np.pi*np.cumsum(f)/SR)*np.exp(-t*(14/weight))+lpf(rng.standard_normal(m),0.25)*np.exp(-t*160)*0.5
    return y/np.max(np.abs(y))
def tick():
    m=int(SR*0.05); t=np.arange(m)/SR
    y=np.sin(2*np.pi*2400*t)*np.exp(-t*140)+0.4*np.sin(2*np.pi*4100*t)*np.exp(-t*220); return y/np.max(np.abs(y))
def impact():
    m=int(SR*0.6); t=np.arange(m)/SR; f=48+90*np.exp(-t*30)
    y=np.sin(2*np.pi*np.cumsum(f)/SR)*np.exp(-t*7)+0.55*lpf(rng.standard_normal(m),0.6)*np.exp(-t*45); return y/np.max(np.abs(y))
def scan(d):
    m=int(SR*d); t=np.arange(m)/SR; nz=rng.standard_normal(m); cut=0.05+0.35*(t/d); y=np.zeros(m); acc=0
    for k in range(m): acc+=cut[k]*(nz[k]-acc); y[k]=acc
    y=y-lpf(y,0.08)+0.15*np.sin(2*np.pi*(900+1400*t/d)*t); env=np.minimum(1,t/0.03)*np.minimum(1,(d-t)/0.05)
    return y*env/np.max(np.abs(y*env))
def riser(d):  # gauge needle climb
    m=int(SR*d); t=np.arange(m)/SR; f=180+900*(t/d)**2
    y=np.sin(2*np.pi*np.cumsum(f)/SR)*(t/d)**1.5; return y/np.max(np.abs(y))
dB=lambda x:10**(x/20)
TH=lambda t,g=-17: place(thud(1.4),t,dB(g))
SW=lambda t,d=0.3,g=-29: place(scan(d),t-d*0.7,dB(g))
TK=lambda t,g=-28: place(tick(),t,dB(g))
IM=lambda t,g=-14: place(impact(),t,dB(g))
# hook: none (clean open). Scenes landing:
SW(6.0); TH(6.24,-20); place(riser(1.1),6.3,dB(-30)); IM(7.4,-15); TK(8.4,-24); TK(9.5,-24); TK(10.6,-26)
SW(12.35); TH(12.69,-19); TH(14.49,-19); IM(15.3,-12)
TK(16.0,-26); SW(16.95,0.2,-30); TK(17.0,-25); TK(18.4,-25); IM(20.2,-13)
SW(21.3); TK(22.6,-27); TK(23.05,-27); SW(24.6,0.9,-30); TK(24.4,-25); TH(25.8,-21); TK(26.6,-26); TK(27.0,-27); TH(28.7,-20)
SW(31.15)
for k in range(8): TK(31.45+k*0.07,-31)
TH(32.15,-20); TK(33.8,-27); IM(36.9,-14)
SW(38.35); TK(40.0,-26); TK(41.5,-24)
SW(42.7,0.25,-26); IM(42.82,-15); SW(44.4,0.3,-30)
TH(45.15,-19); TH(47.9,-19); TH(49.9,-19); TK(47.8,-27); TK(49.8,-27); TK(53.4,-27)
SW(53.85); TK(54.1,-25); SW(54.6,0.6,-31); TK(56.85,-26); TK(58.05,-26); TK(59.05,-26); TK(59.85,-26)
SW(60.45); TK(61.35,-26); SW(62.95,0.7,-31); TH(64.15,-20); TK(65.7,-25); TH(66.85,-18)
TH(68.45,-20); IM(70.25,-13); TK(71.3,-26)
SW(72.5); TK(73.55,-25); IM(75.3,-13)
o=np.stack([L,R],1); o=np.clip(o,-1,1)
w=wave.open('sfx.wav','wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((o*32767).astype(np.int16).tobytes()); w.close()
