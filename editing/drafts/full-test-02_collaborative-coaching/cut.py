import json
FPS=30; runs=json.load(open('sil.json'))['runs']
rem=[(0,0.2)]
for a,b in runs:
    keep=0.30 if a>95.5 else 0.12
    if b-a-keep<0.06: continue
    m=(a+b)/2; ra=round((a+0.06)*FPS)/FPS; rb=round((b-(keep-0.06))*FPS)/FPS
    if a>95.5: ra=round((a+0.1)*FPS)/FPS; rb=round((b-0.2)*FPS)/FPS
    if rb>ra: rem.append((ra,rb))
rem[0]=(0,round(0.2*FPS)/FPS)
END=round(98.13*FPS)/FPS
keep=[];cur=0
for a,b in rem:
    if a>cur: keep.append((cur,a))
    cur=b
keep.append((cur,END))
keep=[(round(a,4),round(b,4)) for a,b in keep if b-a>1e-6]
nd=sum(b-a for a,b in keep)
json.dump({'remove':rem,'keep':keep,'newdur':nd},open('trim.json','w'),indent=1)
print(len(keep),'segments; new dur',round(nd,3),'removed',round(98.13-nd,3)); print(rem)
