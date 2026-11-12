import subprocess,numpy as np,json,sys
import cv2
W,H=270,480
p=subprocess.Popen(['ffmpeg','-v','error','-i','src/src.mov','-vf',f'fps=10,scale={W}:{H}','-f','rawvideo','-pix_fmt','rgb24','-'],stdout=subprocess.PIPE)
cc=cv2.CascadeClassifier(cv2.data.haarcascades+'haarcascade_frontalface_default.xml')
out=[];i=0
while True:
    b=p.stdout.read(W*H*3)
    if len(b)<W*H*3: break
    im=np.frombuffer(b,np.uint8).reshape(H,W,3)
    g=cv2.cvtColor(im,cv2.COLOR_RGB2GRAY); r=cc.detectMultiScale(g,1.1,4,minSize=(50,50)); box=None
    if len(r):
        x,y,w,h=max(r,key=lambda q:q[2]*q[3]); box=[round(x/W,3),round(y/H,3),round(w/W,3),round(h/H,3)]
    out.append(dict(t=round(i/10,2),b=box)); i+=1
json.dump(out,open('faces.json','w'))
miss=sum(1 for o in out if o['b'] is None); print(len(out),'frames, missing',miss)
ys=[o['b'][1] for o in out if o['b']]; ye=[o['b'][1]+o['b'][3] for o in out if o['b']]
print('face top min/max',min(ys),max(ys),'bottom min/max',min(ye),max(ye))
