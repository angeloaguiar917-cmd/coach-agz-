import json,subprocess,numpy as np,wave
S='/tmp/claude-0/-home-user-coach-agz-/21389a83-a8e0-52d1-b0a2-5fe73e4f7c77/scratchpad/'
keep=json.load(open(S+'build/trim.json'))['keep']
expr='+'.join(f'between(n,{round(a*30)},{round(b*30)-1})' for a,b in keep)
subprocess.run(['ffmpeg','-v','error','-y','-i',S+'src/src.mov','-vf',f"fps=30,select='{expr}',setpts=N/30/TB",'-an','-c:v','libx264','-crf','12','-preset','fast','-pix_fmt','yuv420p','-r','30',S+'build/assembled_v.mp4'],check=True)
subprocess.run(['ffmpeg','-v','error','-y','-i',S+'src/src.mov','-vn','-ac','2','-ar','48000','-f','s16le',S+'build/a.raw'],check=True)
a=np.fromfile(S+'build/a.raw',np.int16).reshape(-1,2).astype(np.float32)
SR=48000;fd=int(0.008*SR);out=[]
for s,e in keep:
    seg=a[int(round(s*SR)):int(round(e*SR))].copy()
    r=np.linspace(0,1,fd)[:,None]; seg[:fd]*=r; seg[-fd:]*=r[::-1]; out.append(seg)
o=np.concatenate(out); np.clip(o,-32768,32767).astype(np.int16).tofile(S+'build/cut_a.raw')
subprocess.run(['ffmpeg','-v','error','-y','-f','s16le','-ar','48000','-ac','2','-i',S+'build/cut_a.raw',S+'build/cut_a.wav'],check=True)
print(len(o)/SR, sum(b-a for a,b in keep))
