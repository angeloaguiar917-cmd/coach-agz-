import json,subprocess,numpy as np,wave,sys
S=sys.argv[1]; TR=json.load(open('trim.json')); KEEP=TR['keep']; FPS=30; W,H=1080,1920
# video
keepf=set()
for a,b in KEEP:
    for k in range(round(a*FPS),round(b*FPS)): keepf.add(k)
dec=subprocess.Popen(['ffmpeg','-v','error','-i',S+'/src/raw.mp4','-vf','fps=30','-f','rawvideo','-pix_fmt','rgb24','-'],stdout=subprocess.PIPE)
enc=subprocess.Popen(['ffmpeg','-v','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s','1080x1920','-r','30','-i','-','-c:v','libx264','-crf','10','-preset','veryfast','-pix_fmt','yuv444p','assembled.mp4'],stdin=subprocess.PIPE)
k=0;out=0
while True:
    b=dec.stdout.read(W*H*3)
    if len(b)<W*H*3: break
    if k in keepf: enc.stdin.write(b); out+=1
    k+=1
enc.stdin.close(); enc.wait(); print('frames',out,'src',k)
# audio 48k with 8ms crossfades
subprocess.run(['ffmpeg','-v','error','-y','-i',S+'/src/raw.mp4','-ac','2','-ar','48000','src48.wav'])
w=wave.open('src48.wav'); x=np.frombuffer(w.readframes(w.getnframes()),np.int16).reshape(-1,2).astype(np.float32)
SR=48000; xf=int(0.008*SR); parts=[]
for a,b in KEEP:
    seg=x[int(round(a*SR)):int(round(b*SR))].copy()
    r=np.linspace(0,1,xf)[:,None]; seg[:xf]*=r; seg[-xf:]*=r[::-1]; parts.append(seg)
y=np.concatenate(parts); o=wave.open('trim_audio.wav','wb'); o.setnchannels(2); o.setsampwidth(2); o.setframerate(SR); o.writeframes(np.clip(y,-32768,32767).astype(np.int16).tobytes()); o.close()
print('audio s',len(y)/SR)
