import json,subprocess,sys,os
S=sys.argv[1]; seg=json.load(open(S+'/work/segments.json')); os.makedirs(S+'/work/segs',exist_ok=True)
L=[]
for i,(s,e) in enumerate(seg):
    n=round((e-s)*30); d=n/30; o=S+f'/work/segs/s{i:02d}.mov'
    subprocess.run(['ffmpeg','-v','error','-y','-ss',f'{s:.5f}','-i',S+'/src/gh2.mov','-t',f'{d:.5f}',
      '-vf','fps=30','-af',f'asetpts=PTS-STARTPTS,afade=t=in:d=0.008,afade=t=out:st={d-0.008:.5f}:d=0.008','-frames:v',str(n),
      '-c:v','libx264','-crf','10','-preset','fast','-pix_fmt','yuv420p','-c:a','pcm_s16le','-ar','48000',o],check=True)
    L.append(f"file '{o}'")
open(S+'/work/segs/list.txt','w').write('\n'.join(L))
subprocess.run(['ffmpeg','-v','error','-y','-f','concat','-safe','0','-i',S+'/work/segs/list.txt','-c','copy',S+'/work/assembled.mov'],check=True)
t=0;B=[]
for s,e in seg: n=round((e-s)*30); B.append([t/30,(t+n)/30]); t+=n
json.dump({'bounds':B,'dur':t/30,'segs':seg},open(S+'/work/timeline.json','w')); print('dur',t/30)
