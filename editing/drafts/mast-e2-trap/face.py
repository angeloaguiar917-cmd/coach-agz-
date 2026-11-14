import cv2,json,subprocess,numpy as np
W,H=1080,1920; s=4
cas=cv2.CascadeClassifier(cv2.data.haarcascades+'haarcascade_frontalface_default.xml')
p=subprocess.Popen(['ffmpeg','-v','error','-i','assembled.mov','-vf',f'select=not(mod(n\\,3)),scale={W//s}:{H//s},format=gray','-vsync','0','-f','rawvideo','-'],stdout=subprocess.PIPE)
out=[];n=0
while True:
    b=p.stdout.read((W//s)*(H//s))
    if len(b)<(W//s)*(H//s): break
    g=np.frombuffer(b,np.uint8).reshape(H//s,W//s)
    f=cas.detectMultiScale(g,1.1,5,minSize=(60,60))
    if len(f): x,y,w,h=max(f,key=lambda r:r[2]*r[3]); out.append([n*3/30,int(x*s),int(y*s),int(w*s),int(h*s)])
    else: out.append([n*3/30,None,None,None,None])
    n+=1
json.dump(out,open('faces.json','w'))
ok=[o for o in out if o[1] is not None]; print(len(out),len(ok))
import statistics as st
for lo,hi in [(0,8),(8,23),(23,123)]:
    seg=[o for o in ok if lo<=o[0]<hi]
    if seg: print(lo,hi,'cx',st.median(o[1]+o[3]/2 for o in seg),'cy',st.median(o[2]+o[4]/2 for o in seg),'w',st.median(o[3] for o in seg),'top',min(o[2] for o in seg),'bot',max(o[2]+o[4] for o in seg))
