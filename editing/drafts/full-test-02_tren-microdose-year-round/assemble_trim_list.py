import json, subprocess, re
FPS=30; DUR=101.0
sil=[(11.7556,12.0877),(42.7232,42.9661),(47.5362,47.8367),(49.6604,49.8806),(55.2448,55.5634),(66.3276,66.7802),(67.2738,67.6984),(80.1225,80.3978),(97.6333,98.1324)]
fr=lambda t: round(t*FPS)/FPS
remove=[]
for s,e in sil:
    a,b=fr(s+0.06),fr(e-0.06)
    if b-a>=2/FPS: remove.append((a,b))
end=fr(100.95)
keep=[];cur=0.0
for a,b in remove: keep.append((cur,a)); cur=b
keep.append((cur,end))
json.dump({'remove':remove,'keep':keep,'newdur':sum(b-a for a,b in keep)},open('trim.json','w'),indent=1)
print(remove, sum(b-a for a,b in keep))
vf=[];af=[]
for i,(a,b) in enumerate(keep):
    vf.append(f"[0:v]trim=start={a:.4f}:end={b:.4f},setpts=PTS-STARTPTS,fps=30[v{i}]")
    af.append(f"[0:a]atrim=start={a:.4f}:end={b:.4f},asetpts=PTS-STARTPTS,afade=t=in:d=0.008,afade=t=out:st={b-a-0.008:.4f}:d=0.008[a{i}]")
n=len(keep)
fc=';'.join(vf+af)+';'+''.join(f'[v{i}][a{i}]' for i in range(n))+f'concat=n={n}:v=1:a=1[v][a]'
subprocess.run(['ffmpeg','-v','error','-y','-i','../src/tren.mov','-filter_complex',fc,'-map','[v]','-map','[a]','-c:v','libx264','-crf','12','-preset','fast','-pix_fmt','yuv420p','-c:a','pcm_s16le','-ar','48000','assembled.mov'],check=True)
