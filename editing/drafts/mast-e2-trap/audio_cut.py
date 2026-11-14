# usage: python3 audio_cut.py <src48k.wav> <out.wav>  -> applies cut.json with 8 ms crossfades
import sys,json,wave,numpy as np
C=json.load(open(__file__.rsplit('/',1)[0]+'/cut.json')) if '/' in __file__ else json.load(open('cut.json'))
w=wave.open(sys.argv[1]);SR=w.getframerate();x=np.frombuffer(w.readframes(w.getnframes()),np.int16).reshape(-1,2).astype(np.float32)
keep=[];t=0
for a,b in C['remove']: keep.append((t,a)); t=b
keep.append((t,C['src_end']))
xf=int(SR*0.008); out=None
for a,b in keep:
    seg=x[int(a*SR):int(b*SR)].copy()
    if out is None: out=seg; continue
    r=np.linspace(0,1,xf)[:,None]; out[-xf:]=out[-xf:]*(1-r)+seg[:xf]*r; out=np.concatenate([out,seg[xf:]])
o=wave.open(sys.argv[2],'wb');o.setnchannels(2);o.setsampwidth(2);o.setframerate(SR);o.writeframes(np.clip(out,-32768,32767).astype(np.int16).tobytes());o.close()
print('dur',len(out)/SR)
