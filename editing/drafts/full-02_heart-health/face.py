import cv2,json,numpy as np
cc=cv2.CascadeClassifier('/usr/local/lib/python3.13/dist-packages/cv2/data/haarcascade_frontalface_default.xml')
cap=cv2.VideoCapture('assembled.mov'); n=0; out={}
while True:
    ok,fr=cap.read()
    if not ok: break
    if n%3==0:
        g=cv2.cvtColor(cv2.resize(fr,(270,480)),cv2.COLOR_BGR2GRAY)
        fs=cc.detectMultiScale(g,1.1,5,minSize=(80,80))
        if len(fs): x,y,w,h=max(fs,key=lambda r:r[2]*r[3]); out[n]=[float((x+w/2)*4),float((y+h/2)*4),float(w*4)]
    n+=1
json.dump({'n':n,'det':out},open('face.json','w')); print(n,len(out))
