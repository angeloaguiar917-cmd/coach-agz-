import json,subprocess,numpy as np,wave
FPS=30; SRC='../src/src.mov'; DUR=81.716
gaps=[(3.35,3.61),(35.51,35.85),(43.01,43.30),(52.99,53.30),(54.90,55.25),(61.75,62.02),(69.05,69.45),(78.73,79.09)]
rem=[(round((s+0.06)*FPS),round((e-0.06)*FPS)) for s,e in gaps]+[(round(44.95*FPS),round(45.27*FPS))]
rem.sort(); NF=int(DUR*FPS)
keep=[];c=0
for a,b in rem: keep.append((c,a)); c=b
keep.append((c,NF))
keep=[(a,b) for a,b in keep if b>a]
json.dump(dict(keep=keep,fps=FPS),open('trim.json','w'))
srcframes=[i for a,b in keep for i in range(a,b)]
print('out frames',len(srcframes),'dur',len(srcframes)/FPS)
# video: decode at 30fps, keep listed frames
sel=set(srcframes)
dec=subprocess.Popen(['ffmpeg','-v','error','-i',SRC,'-vf','fps=30','-f','rawvideo','-pix_fmt','rgb24','-'],stdout=subprocess.PIPE)
enc=subprocess.Popen(['ffmpeg','-v','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s','1080x1920','-r','30','-i','-','-c:v','libx264','-crf','10','-preset','fast','-pix_fmt','yuv420p','cut_v.mp4'],stdin=subprocess.PIPE)
fs=1080*1920*3;i=0
while True:
    b=dec.stdout.read(fs)
    if len(b)<fs: break
    if i in sel: enc.stdin.write(b)
    i+=1
enc.stdin.close(); enc.wait()
# audio 48k with 8ms crossfades at joins
subprocess.run(['ffmpeg','-v','error','-y','-i',SRC,'-ac','2','-ar','48000','src48.wav'])
w=wave.open('src48.wav'); a=np.frombuffer(w.readframes(w.getnframes()),np.int16).reshape(-1,2).astype(np.float32)
SR=48000; xf=int(0.008*SR); out=[]
for k,(f0,f1) in enumerate(keep):
    seg=a[int(f0/FPS*SR):int(f1/FPS*SR)].copy()
    if k>0: seg[:xf]*=np.linspace(0,1,xf)[:,None]
    if k<len(keep)-1: seg[-xf:]*=np.linspace(1,0,xf)[:,None]
    out.append(seg)
o=np.concatenate(out).astype(np.int16)
ww=wave.open('cut_a.wav','wb'); ww.setnchannels(2); ww.setsampwidth(2); ww.setframerate(SR); ww.writeframes(o.tobytes()); ww.close()
print('audio dur',len(o)/SR)
