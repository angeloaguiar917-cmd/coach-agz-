import json, math, subprocess, numpy as np, sys, re
S=sys.argv[1]; FPS=30; SRC=S+'/src/raw.mp4'; WK=S+'/work/'
txt=subprocess.run(['ffmpeg','-hide_banner','-i',WK+'raw16.wav','-af','silencedetect=noise=-30dB:d=0.22','-f','null','-'],capture_output=True,text=True).stderr
st=[float(x) for x in re.findall(r'silence_start: ([0-9.]+)',txt)]; en=[float(x) for x in re.findall(r'silence_end: ([0-9.]+)',txt)]
DUR=124.0667; END_KEEP=123.90
remove=[]
for a,b in zip(st,en):
    if a>=END_KEEP: continue
    if 12.3<a<12.5: ra,rb=a+0.12,b-0.18     # dramatic beat before "you're done": keep ~0.30 s
    else: ra,rb=a+0.06,b-0.06
    fa,fb=math.ceil(ra*FPS),math.floor(rb*FPS)
    if fb-fa>=2: remove.append([fa,fb])
remove.append([math.ceil(END_KEEP*FPS),int(DUR*FPS)])
keep=[];cur=0
for a,b in remove:
    if a>cur: keep.append([cur,a])
    cur=b
NF=sum(b-a for a,b in keep)
print('cuts',len(remove)-1,'removed s',sum(b-a for a,b in remove[:-1])/FPS,'new dur',NF/FPS)
json.dump({'fps':FPS,'keep_frames':keep,'remove_frames':remove,'dur':NF/FPS},open(WK+'trim.json','w'))
# audio: 48k stereo, cut at frame boundaries with 8 ms crossfades
a=subprocess.run(['ffmpeg','-v','error','-i',SRC,'-f','f32le','-ac','2','-ar','48000','-'],capture_output=True).stdout
x=np.frombuffer(a,np.float32).reshape(-1,2); SR=48000; xf=int(0.008*SR)
out=[]
for i,(fa,fb) in enumerate(keep):
    s=x[fa*SR//FPS:fb*SR//FPS].copy()
    if out and xf:
        prev=out[-1]; ramp=np.linspace(0,1,xf)[:,None]
        # overlap-add: fade tail of prev and head of current, keeping total length = sum of segments
        tail=x[fb*0+keep[i-1][1]*SR//FPS:keep[i-1][1]*SR//FPS+xf]
        s[:xf]=s[:xf]*ramp+tail[:xf]*(1-ramp)
    out.append(s)
y=np.concatenate(out); print('audio s',len(y)/SR)
subprocess.run(['ffmpeg','-v','error','-y','-f','f32le','-ac','2','-ar','48000','-i','-','-c:a','pcm_s16le',WK+'cut.wav'],input=y.astype(np.float32).tobytes())
subprocess.run(['ffmpeg','-v','error','-y','-i',WK+'cut.wav','-ac','1','-ar','16000',WK+'cut16.wav'])
