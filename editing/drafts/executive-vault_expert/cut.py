import numpy as np,wave,json,subprocess
w=wave.open('audio16.wav');x=np.frombuffer(w.readframes(w.getnframes()),np.int16)/32768
db=np.array([20*np.log10(np.sqrt(np.mean(x[i:i+320]**2))+1e-9) for i in range(0,len(x)-320,160)])
low=db<-43; runs=[];i=0
while i<len(low):
    if low[i]:
        j=i
        while j<len(low) and low[j]: j+=1
        if (j-i)>=22: runs.append((i/100,j/100))
        i=j
    else: i+=1
FPS=30; DUR=61.5
rem=[]
for a,b in runs:
    if a<0.3: a=0.0; rem.append((0.0,round((b-0.06)*FPS)/FPS)); continue
    ra=round((a+0.06)*FPS)/FPS; rb=round((b-0.06)*FPS)/FPS
    if rb-ra>=2/FPS: rem.append((ra,rb))
rem=[r for r in rem if r[0]<61.3]
keep=[];c=0.0
for a,b in rem:
    if a>c: keep.append((c,a))
    c=b
end=61.5; keep.append((c,end))
print('runs',runs);print('remove',rem);print('removed',round(sum(b-a for a,b in rem),2))
json.dump({'keep':keep,'remove':rem},open('trim.json','w'),indent=1)
fc=[];n=len(keep)
for k,(a,b) in enumerate(keep):
    fc.append(f"[0:v]trim=start={a:.4f}:end={b:.4f},setpts=PTS-STARTPTS,fps=30[v{k}]")
    fc.append(f"[0:a]atrim=start={a:.4f}:end={b:.4f},asetpts=PTS-STARTPTS,afade=t=in:d=0.008,afade=t=out:st={b-a-0.008:.4f}:d=0.008[a{k}]")
fc.append(''.join(f'[v{k}][a{k}]' for k in range(n))+f'concat=n={n}:v=1:a=1[v][a]')
subprocess.run(['ffmpeg','-v','error','-y','-i','src/Expert.MOV','-filter_complex',';'.join(fc),'-map','[v]','-map','[a]','-c:v','libx264','-crf','12','-preset','fast','-pix_fmt','yuv420p','-c:a','pcm_s16le','assembled.mov'],check=True)
