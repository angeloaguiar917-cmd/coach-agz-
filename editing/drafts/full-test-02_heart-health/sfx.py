import numpy as np, wave, json
from sfx_lib import *
DUR=json.load(open('cutlist.json'))['dur']; n=int(SR*(DUR+0.5)); L=np.zeros(n); R=np.zeros(n)
def place(sig,t,pan=0.0,gain=1.0):
    i=int(t*SR); s=sig[:max(0,n-i)]*gain
    L[i:i+len(s)]+=s*(1-max(0,pan)); R[i:i+len(s)]+=s*(1+min(0,pan))
hit=lambda t,g=-18: place(thud(1.3),t,gain=dB(g))
imp=lambda t,g=-14: place(impact(),t,gain=dB(g))
tk=lambda t,g=-29: place(tick(),t,gain=dB(g))
sw=lambda t,d=0.35,g=-29: place(scan(d),t,gain=dB(g))
def wh(t_land,d=0.34,g=-27): place(whoosh(d),t_land-d*0.75,gain=dB(g))
# stage window moves (whoosh lands as the window settles)
for t in (5.45,20.0,29.1,47.2,57.9,79.9,102.4): wh(t+0.2)
for t in (13.62,43.75,53.2,70.95,95.0,111.4): wh(t+0.15,0.28,-31)
wh(1.9,0.3,-30)                                   # visual-hook punch-in
for t in (6.94,7.86,11.2,11.4,12.62,15.12,16.26,17.26,19.26,23.76,24.44,30.26,33.84,36.36,43.22,44.58,45.56,
          54.42,59.18,62.04,63.06,73.58,76.26,78.58,81.88,82.2,84.16,84.88,89.42,90.6,91.4,99.26,99.96,101.6,
          107.56,108.3,109.3,113.22): tk(t)
for t in (9.78,10.14): hit(t,-21)
for t in (17.96,21.18,40.62,41.76,43.9,50.74,58.02,92.84,103.5,105.46): hit(t)
sw(25.1,1.2,-33); sw(29.15,0.45); sw(47.3,0.8,-32); sw(64.05,0.3); sw(67.74,0.35)
imp(31.24,-16); imp(56.90); imp(70.18); hit(111.86,-15)
out=np.stack([L,R],1); pk=np.max(np.abs(out)); print('sfx peak dBFS',20*np.log10(pk))
w=wave.open('sfx.wav','wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
w.writeframes((np.clip(out,-1,1)*32767).astype(np.int16).tobytes()); w.close()
