import json,subprocess
SRC='../src/reel.mp4'; END=123.85
VREM=[(17.3333,17.5),(96.0667,96.2),(119.3,120.6)]
AREM=[(17.3333,17.5),(96.0667,96.2),(119.2833,120.5833)]
def keep(rem):
    k=[];a=0
    for r0,r1 in rem: k.append((a,r0)); a=r1
    k.append((a,END)); return k
VK,AK=keep(VREM),keep(AREM)
L=open('parts.txt','w')
for i,((a,b),(c,d)) in enumerate(zip(VK,AK)):
    n=round((b-a)*30)
    subprocess.run(['ffmpeg','-v','error','-y','-ss',str(max(0,a-2)),'-i',SRC,'-ss',str(a-max(0,a-2)),'-vf','fps=30','-frames:v',str(n),'-an','-c:v','libx264','-crf','12','-preset','fast','-g','15','-pix_fmt','yuv420p',f'pv{i}.mp4'],check=True)
    subprocess.run(['ffmpeg','-v','error','-y','-ss',str(c),'-t',str(n/30),'-i',SRC,'-vn','-af','afade=t=in:d=0.008,afade=t=out:st=%f:d=0.008'%(n/30-0.008),'-ac','2','-ar','48000','-c:a','pcm_s16le',f'pa{i}.wav'],check=True)
    L.write(f"file 'pv{i}.mp4'\n")
L.close()
subprocess.run(['ffmpeg','-v','error','-y','-f','concat','-i','parts.txt','-c','copy','v.mp4'],check=True)
subprocess.run(['ffmpeg','-v','error','-y']+sum([['-i',f'pa{i}.wav'] for i in range(len(AK))],[])+['-filter_complex',''.join(f'[{i}:a]' for i in range(len(AK)))+f'concat=n={len(AK)}:v=0:a=1[a]','-map','[a]','-c:a','pcm_s16le','a.wav'],check=True)
subprocess.run(['ffmpeg','-v','error','-y','-i','v.mp4','-i','a.wav','-c','copy','assembled.mov'],check=True)
cuts=[];acc=0
for a,b in VK[:-1]: acc+=round((b-a)*30)/30; cuts.append(round(acc,4))
json.dump({'vkeep':VK,'akeep':AK,'trim_cuts_new':cuts},open('trim.json','w'),indent=1); print(cuts)
