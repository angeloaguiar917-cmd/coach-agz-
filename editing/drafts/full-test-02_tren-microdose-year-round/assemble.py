import json, subprocess, numpy as np, wave
TR=json.load(open('trim.json')); keep=TR['keep']
sel='+'.join(f'between(t,{a-0.0005:.4f},{b-0.0005:.4f})' for a,b in keep)
subprocess.run(['ffmpeg','-v','error','-y','-i','../src/tren.mov','-an','-vf',f"fps=30,select='{sel}',setpts=N/30/TB",'-c:v','libx264','-crf','12','-preset','fast','-pix_fmt','yuv420p','-r','30','vid.mp4'],check=True)
subprocess.run(['ffmpeg','-v','error','-y','-i','../src/tren.mov','-vn','-ac','2','-ar','48000','-f','s16le','raw.pcm'],check=True)
x=np.fromfile('raw.pcm',np.int16).reshape(-1,2).astype(np.float32); SR=48000; X=int(0.008*SR)
out=[]
for a,b in keep:
    seg=x[int(round(a*SR)):int(round(b*SR))].copy(); r=np.linspace(0,1,X)[:,None]
    seg[:X]*=r; seg[-X:]*=r[::-1]; out.append(seg)
y=np.concatenate(out); print('audio s',len(y)/SR)
w=wave.open('aud.wav','wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(np.clip(y,-32768,32767).astype(np.int16).tobytes()); w.close()
subprocess.run(['ffmpeg','-v','error','-y','-i','vid.mp4','-i','aud.wav','-c','copy','assembled.mov'],check=True)
