import json,numpy as np,subprocess,wave
SR=48000
raw=np.frombuffer(subprocess.run(['ffmpeg','-v','error','-i','../src/src.mov','-ac','2','-ar',str(SR),'-f','s16le','-'],capture_output=True).stdout,np.int16).astype(np.float32).reshape(-1,2)
keep=json.load(open('keep.json'))['keep']; out=[]; fd=int(0.008*SR)
for a,b in keep:
    i0=round(a*30)*SR//30; i1=round(b*30)*SR//30
    s=raw[i0:i1].copy()
    if len(s)<i1-i0: s=np.vstack([s,np.zeros((i1-i0-len(s),2))])
    r=np.linspace(0,1,fd)[:,None]; s[:fd]*=r; s[-fd:]*=r[::-1]; out.append(s)
o=np.vstack(out); print(len(o)/SR)
w=wave.open('speech.wav','wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(np.clip(o,-32768,32767).astype(np.int16).tobytes()); w.close()
