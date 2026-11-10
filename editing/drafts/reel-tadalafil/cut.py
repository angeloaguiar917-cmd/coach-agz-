import json,subprocess,sys
S=sys.argv[1]; W=json.load(open(S+'/src/words_raw.json'))
FPS=30; fr=lambda t: round(t*FPS)/FPS
start=max(0,W[0]['s']-0.10); end=W[-1]['e']+0.45
keep=[]; cur=start
for a,b in zip(W,W[1:]):
    g=b['s']-a['e']
    if g>0.24:
        keep.append([fr(cur),fr(a['e']+0.07)]); cur=b['s']-0.06
keep.append([fr(cur),fr(min(end,100.45))])
tot=sum(b-a for a,b in keep); print(len(keep),'segments, dur',round(tot,3),'removed',round(100.45-start-tot,2))
json.dump({'keep':keep},open('cut.json','w'))
v=[];a=[]
for i,(s,e) in enumerate(keep):
    v.append(f"[0:v]trim={s}:{e},setpts=PTS-STARTPTS,fps=30[v{i}]")
    a.append(f"[0:a]atrim={s}:{e},asetpts=PTS-STARTPTS,afade=t=in:d=0.008,afade=t=out:st={e-s-0.008:.3f}:d=0.008[a{i}]")
fc=';'.join(v+a)+';'+''.join(f'[v{i}][a{i}]' for i in range(len(keep)))+f'concat=n={len(keep)}:v=1:a=1[v][a]'
subprocess.run(['ffmpeg','-v','error','-y','-i',S+'/src/tadalafil.mov','-filter_complex',fc,'-map','[v]','-map','[a]','-c:v','libx264','-crf','12','-preset','fast','-pix_fmt','yuv420p','-c:a','pcm_s16le','-ar','48000','assembled.mov'],check=True)
