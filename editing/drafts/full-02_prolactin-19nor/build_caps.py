import json, re, sys
sys.argv=['x','stills']
src=open('render.py').read().split('# ---------------- palette')[0]
exec(src)
W_=json.load(open('words_cut.json'))
merge={(110,111):'19-NORS',(276,277):'ELITE',(282,283):'19-NORS',(289,291):'PROLACTIN',(312,313):'19-NOR',(332,334):'PROLACTIN',(68,69):None}
rep={101:'IN',60:'FLEX',69:'ITS',71:'AND',103:'WAY',113:'DECA',116:'TREN',177:'GALACTORRHEA',293:'P5P',295:'CABERGOLINE',54:'F*CKING',136:'F*CK',264:'F*CKING',300:'SH*T',324:'SH*T'}
out=[];i=0;skip=set()
spans={a:b for (a,b) in merge if merge[(a,b)]}
while i<len(W_):
    w=W_[i]
    if i in spans:
        b=spans[i]; c=merge[(i,b)]; s,e=w['s'],W_[b]['e']; i=b+1
    else:
        c=rep.get(i, re.sub(r"[^\w'\-\*]","",w['w']).upper()); s,e=w['s'],w['e']; i+=1
    out.append({'w':w['w'],'c':c,'s':round(new_to_old(s),3),'e':round(new_to_old(max(s,e-0.001)),3),'sn':s})
json.dump(out,open('words_caption.json','w'),indent=0)
print(len(out)); print(' '.join(o['c'] for o in out))
