import json,subprocess,os
keep=json.load(open('build/keep.json')); os.makedirs('build/seg',exist_ok=True)
L=[]
for i,(a,b) in enumerate(keep):
    o=f'build/seg/{i:02d}.mov'; d=b-a
    subprocess.run(['ffmpeg','-v','error','-y','-ss',f'{a:.4f}','-i','src/src.mov','-t',f'{d:.4f}','-vf','fps=30','-af',f'afade=t=in:d=0.008,afade=t=out:st={d-0.008:.4f}:d=0.008','-c:v','libx264','-crf','12','-preset','fast','-pix_fmt','yuv420p','-c:a','pcm_s16le','-ar','48000',o],check=True)
    L.append(f"file 'seg/{i:02d}.mov'")
open('build/list.txt','w').write('\n'.join(L))
subprocess.run(['ffmpeg','-v','error','-y','-f','concat','-safe','0','-i','build/list.txt','-c','copy','build/assembled.mov'],check=True)
