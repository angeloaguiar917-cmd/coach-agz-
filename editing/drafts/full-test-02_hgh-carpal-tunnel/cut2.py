import json,subprocess,numpy as np,wave
W=json.load(open('../src/words_raw.json'))
FPS=30; r=lambda x: round(x*FPS)/FPS
# speech energy to refine boundaries
a=np.frombuffer(open('../src/a16.wav','rb').read()[44:],np.int16).astype(np.float32)
hop=160; e=np.sqrt(np.convolve(a**2,np.ones(hop)/hop,'same')[::hop]); thr=np.percentile(e,30)*2.2
def silent(t0,t1):
    i0,i1=int(t0*100),int(t1*100); return np.mean(e[i0:i1]<thr)>=0.85 if i1>i0 else True
keep=[tuple(k) for k in json.load(open('keep.json'))['keep']]
print(len(keep))
# build per segment
import os
os.makedirs('seg',exist_ok=True); lst=open('seg/list.txt','w')
for i,(a_,b_) in enumerate(keep):
    subprocess.run(['ffmpeg','-v','error','-y','-ss',f'{a_:.4f}','-i','../src/src.mov','-t',f'{b_-a_:.4f}','-vf','fps=30','-af',f'asetpts=PTS-STARTPTS,afade=t=in:d=0.008,afade=t=out:st={b_-a_-0.008:.4f}:d=0.008','-c:v','libx264','-crf','12','-preset','fast','-pix_fmt','yuv420p','-c:a','pcm_s16le','-ar','48000',f'seg/{i:02d}.mov'],check=True)
    lst.write(f"file '{i:02d}.mov'\n")
lst.close()
subprocess.run(['ffmpeg','-v','error','-y','-f','concat','-i','seg/list.txt','-c','copy','assembled.mov'],check=True)
