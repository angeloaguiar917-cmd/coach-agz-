import numpy as np, json, subprocess, wave
SR=48000; FPS=30
a=np.fromfile('src/a48.f32',np.float32).reshape(-1,2); mono=a.mean(1)
hop=int(SR*0.01); n=len(mono)//hop
rms=np.sqrt((mono[:n*hop].reshape(n,hop)**2).mean(1)+1e-12); db=20*np.log10(rms)
thr=np.percentile(db,10)+8
print('noise floor ~',np.percentile(db,10),'thr',thr)
# new order (source seconds): hook, intro, BP+telmi+bonus, lipids, simplify, why+CTA
SEG=[(0.00,10.80,'hook'),(10.86,16.82,'intro'),(49.38,83.66,'bp'),(23.50,48.52,'lipids'),(85.56,93.30,'simplify'),(93.40,123.96,'why_cta')]
def snap(t,r=0.07):
    i0=max(0,int((t-r)*100)); i1=min(n-1,int((t+r)*100)); k=i0+np.argmin(db[i0:i1+1]); return k/100
fr=lambda t: round(t*FPS)/FPS
keep=[]
for s0,s1,name in SEG:
    s0=fr(snap(s0)) if s0>0 else 0.0; s1=fr(snap(s1))
    # silent runs inside
    i0,i1=int(s0*100),int(s1*100); q=db[i0:i1]<thr
    cur=s0; runs=[]; k=0
    while k<len(q):
        if q[k]:
            j=k
            while j<len(q) and q[j]: j+=1
            if (j-k)>=22 and k>0 and j<len(q): runs.append(((i0+k)/100,(i0+j)/100))
            k=j
        else: k+=1
    for r0,r1 in runs:
        c0=fr(r0+0.06); c1=fr(r1-0.06)
        if c1-c0>=2/FPS: keep.append([cur,c0,name]); cur=c1
    keep.append([cur,s1,name])
tot=sum(b-a_ for a_,b,_ in keep); print('pieces',len(keep),'dur',round(tot,2))
json.dump(keep,open('keep.json','w'))
# audio with 8ms crossfades
xf=int(SR*0.008); out=[]
for a0,a1,_ in keep:
    seg=a[int(round(a0*SR)):int(round(a1*SR))].copy()
    if out:
        prev=out[-1]; r=np.linspace(0,1,xf)[:,None]
        tail=prev[-xf:]*(1-r)+seg[:xf]*r; out[-1]=prev[:-xf]; seg=np.concatenate([tail,seg[xf:]])
    out.append(seg)
au=np.concatenate(out); 
# pad to exact frame count
nf=sum(round((b-a_)*FPS) for a_,b,_ in keep); need=int(nf/FPS*SR)
au=np.pad(au,((0,max(0,need-len(au))),(0,0)))[:need]
au.astype(np.float32).tofile('cut_a48.f32'); print('frames',nf)
# video: select frames
idx=[]
for a0,a1,_ in keep: idx+=list(range(round(a0*FPS),round(a1*FPS)))
sel='+'.join(f'between(n\\,{round(a0*FPS)}\\,{round(a1*FPS)-1})' for a0,a1,_ in keep)
open('sel.txt','w').write(f"select='{sel}',setpts=N/{FPS}/TB")
subprocess.run(['ffmpeg','-v','error','-y','-i','src/raw.mp4','-filter_script:v','sel.txt','-an','-c:v','libx264','-crf','10','-preset','fast','-pix_fmt','yuv420p','-r','30','cut_v.mp4'],check=True)
subprocess.run(['ffmpeg','-v','error','-y','-f','f32le','-ar','48000','-ac','2','-i','cut_a48.f32','-c:a','pcm_s16le','cut_a.wav'],check=True)
subprocess.run(['ffmpeg','-v','error','-y','-i','cut_a.wav','-ac','1','-ar','16000','cut_a16.wav'],check=True)
