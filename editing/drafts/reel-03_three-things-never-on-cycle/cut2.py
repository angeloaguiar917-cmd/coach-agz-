import json,subprocess,os
K=json.load(open('trim.json'))['keep']; os.makedirs('segs',exist_ok=True)
L=open('segs/list.txt','w')
for i,(a,b) in enumerate(K):
    d=b-a; o=f'segs/s{i:02d}.mov'
    subprocess.run(['ffmpeg','-v','error','-y','-ss',f'{a:.4f}','-i','../src/raw.mov','-t',f'{d:.4f}','-vf','fps=30','-af',f'afade=t=in:d=0.008,afade=t=out:st={d-0.008:.4f}:d=0.008','-c:v','libx264','-crf','12','-preset','fast','-pix_fmt','yuv420p','-c:a','pcm_s16le','-ar','48000','-ac','2',o],check=True)
    L.write(f"file 's{i:02d}.mov'\n")
L.close()
subprocess.run(['ffmpeg','-v','error','-y','-f','concat','-safe','0','-i','segs/list.txt','-c','copy','assembled.mov'],check=True)
