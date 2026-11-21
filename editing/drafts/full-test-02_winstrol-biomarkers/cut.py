import json,subprocess
S='/tmp/claude-0/-home-user-coach-agz-/21389a83-a8e0-52d1-b0a2-5fe73e4f7c77/scratchpad/'
sil=[(10.6261,11.0642),(13.8594,14.0864),(23.6625,23.9496),(27.5111,27.8108),(29.2786,29.5534),(36.7321,37.0132),(47.8358,48.1262),(52.274,52.5814),(54.9935,55.3409),(57.7813,58.0368),(60.0512,60.3684),(62.1204,62.4211),(75.3294,75.5672),(88.3406,88.6963),(90.6007,90.8744),(99.0583,99.3787),(102.285,102.702),(103.743,103.982),(104.414,104.737)]
fr=lambda x: round(x*30)/30
END=fr(106.80)
rem=[]
for a,b in sil:
    a2=fr(a+0.06); b2=fr(b-0.06)
    if b2-a2>=0.1: rem.append((a2,b2))
keep=[];cur=0.0
for a,b in rem: keep.append((cur,a)); cur=b
keep.append((cur,END))
json.dump({'keep':keep,'remove':rem},open(S+'build/trim.json','w'),indent=1)
fc=[];n=len(keep)
for i,(a,b) in enumerate(keep):
    fc.append(f"[0:v]trim=start={a:.4f}:end={b:.4f},setpts=PTS-STARTPTS,fps=30[v{i}]")
    d=b-a
    fc.append(f"[0:a]atrim=start={a:.4f}:end={b:.4f},asetpts=PTS-STARTPTS,afade=t=in:d=0.008,afade=t=out:st={d-0.008:.4f}:d=0.008[a{i}]")
fc.append(''.join(f'[v{i}][a{i}]' for i in range(n))+f'concat=n={n}:v=1:a=1[v][a]')
subprocess.run(['ffmpeg','-v','error','-y','-i',S+'src/src.mov','-filter_complex',';'.join(fc),'-map','[v]','-map','[a]','-c:v','libx264','-crf','12','-preset','fast','-pix_fmt','yuv420p','-c:a','pcm_s16le',S+'build/assembled.mov'],check=True)
print(sum(b-a for a,b in keep), len(keep))
