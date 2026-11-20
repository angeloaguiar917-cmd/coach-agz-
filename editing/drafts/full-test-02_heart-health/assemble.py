import json, subprocess, sys
S=sys.argv[1]; W,H=1080,1920; FPS=30
K=json.load(open(S+'/work/cutlist.json'))['keeps']
keep=set()
for a,b in K:
    for n in range(round(a*FPS),round(b*FPS)): keep.add(n)
dec=subprocess.Popen(['ffmpeg','-v','error','-i',S+'/src/raw.mp4','-f','rawvideo','-pix_fmt','yuv420p','-'],stdout=subprocess.PIPE)
enc=subprocess.Popen(['ffmpeg','-v','error','-y','-f','rawvideo','-pix_fmt','yuv420p','-s',f'{W}x{H}','-r','30','-i','-','-c:v','libx264','-crf','12','-preset','veryfast','-g','15','-pix_fmt','yuv420p',S+'/work/assembled.mp4'],stdin=subprocess.PIPE)
fs=W*H*3//2; n=0; w=0
while True:
    buf=dec.stdout.read(fs)
    if len(buf)<fs: break
    if n in keep: enc.stdin.write(buf); w+=1
    n+=1
enc.stdin.close(); enc.wait(); print('src frames',n,'written',w,'expected',len(keep))
