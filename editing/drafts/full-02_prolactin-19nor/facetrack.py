import cv2, json, numpy as np
cap=cv2.VideoCapture('mezz30.mp4'); casc=cv2.CascadeClassifier(cv2.data.haarcascades+'haarcascade_frontalface_default.xml')
res=[];n=0
while True:
    ok,fr=cap.read()
    if not ok: break
    if n%6==0:
        g=cv2.cvtColor(cv2.resize(fr,(270,480)),cv2.COLOR_BGR2GRAY)
        fs=casc.detectMultiScale(g,1.1,5,minSize=(60,60))
        if len(fs):
            x,y,w,h=max(fs,key=lambda r:r[2]*r[3]); res.append((n/30,float(x+w/2)*4,float(y+h/2)*4,float(w)*4))
    n+=1
json.dump(res,open('face.json','w')); a=np.array(res); print(len(res),'/',n//6, a[:,1:].min(0), a[:,1:].max(0), np.median(a[:,1:],0))
