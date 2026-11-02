import sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter
S=sys.argv[1]; F=S+'/fonts/'; O=S+'/mock2/'
GOLD=(201,169,110); CREAM=(244,241,234); RED=(231,71,42); NAVY=(14,17,23)
W,H=1080,1920
def f(n,s): return ImageFont.truetype(F+n,s)
def prep(i):
    im=Image.open(O+f'bg{i}.png').convert('RGBA')
    # remove burned-in IG text (captions + old titles) for the mock only
    for y0,y1 in [(1280,1660)]+([(30,540)] if i>1 else []):
        im.paste(im.crop((0,y0,W,y1)).filter(ImageFilter.GaussianBlur(40)),(0,y0))
    g=Image.new('RGBA',(W,H)); d=ImageDraw.Draw(g)
    for y in range(H):  # light scrim: only behind caption zone, max ~45%
        a=0
        if y>1000: a=int(min(1,(y-1000)/500)*115)
        if y<400: a=max(a,int((1-y/400)*120))
        d.line([(0,y),(W,y)],fill=NAVY+(a,))
    return Image.alpha_composite(im,g)
def pinned(im,title,acc):
    d=ImageDraw.Draw(im,'RGBA'); d.rectangle([0,0,7,H],fill=GOLD)
    d.rectangle([8,212,W,372],fill=NAVY+(225,))
    d.line([(64,244),(108,244)],fill=GOLD,width=4); d.text((122,228),'@coach.agz',font=f('JBMono-500.ttf',28),fill=GOLD)
    fn=f('BebasNeue.ttf',80); d.text((64,266),title+' ',font=fn,fill=CREAM); d.text((64+d.textlength(title+' ',font=fn),266),acc,font=fn,fill=GOLD if acc!='ANAVAR' else RED)
def caption(im,ws,active,style):
    # every-word captions: 2-4 word group, centred, active word emphasised
    d=ImageDraw.Draw(im,'RGBA'); size=150
    while True:
        fn=f('BebasNeue.ttf',size); sp=d.textlength(' ',font=fn)
        tot=sum(d.textlength(w,font=fn) for w in ws)+sp*(len(ws)-1)+(44 if style!='text' else 0)
        if tot<=W-2*90: break
        size-=4
    big=f('BebasNeue.ttf',int(size*1.05))
    sp=d.textlength(' ',font=fn); widths=[d.textlength(w,font=fn) for w in ws]
    total=sum(widths)+sp*(len(ws)-1)+ (40 if style!='text' else 0)
    x=(W-total)/2; y=1230
    sh=Image.new('RGBA',(W,H)); sd=ImageDraw.Draw(sh)
    for w,wd in zip(ws,widths):
        if w!=active: sd.text((x+4,y+6),w,font=fn,fill=(0,0,0,200))
        x+=wd+sp+(40 if (w==active and style!='text') else 0)
    im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(6)))
    x=(W-total)/2
    for w,wd in zip(ws,widths):
        if w==active and style!='text':
            box=GOLD if style=='gold' else RED; tc=NAVY if style=='gold' else CREAM
            d.rounded_rectangle([x-4,y+size*0.04,x+wd+36,y+size],radius=10,fill=box)
            # slight scale-up implied: draw active word larger
            d.text((x+16,y-size*0.02),w,font=big,fill=tc); x+=wd+sp+40
        else:
            col=RED if (w==active and style=='text') else CREAM
            d.text((x,y),w,font=fn,fill=col,stroke_width=3,stroke_fill=(0,0,0)); x+=wd+sp
scenes=[(1,'CAN YOU REVERSE','GYNO?',['REAL','GLANDULAR','TISSUE.'],'GLANDULAR'),
        (2,'THE DARK TRUTH ABOUT','ANAVAR',["IT'S",'NOT','HARMLESS.'],'HARMLESS.'),
        (3,"BODYBUILDER'S WORST",'ENEMY',['MUTED','AND','CONFIDENT'],'CONFIDENT')]
cols=[]
for st in ['text','gold','red']:
    for i,t,a,ws,act in scenes:
        im=prep(i); pinned(im,t,a); caption(im,ws,act,st); im.convert('RGB').save(O+f'{st}_{i}.jpg',quality=90)
grid=Image.new('RGB',(W//3*3+20,(H//3)*3+20),(30,30,30))
for r,st in enumerate(['text','gold','red']):
    for c in range(3):
        grid.paste(Image.open(O+f'{st}_{c+1}.jpg').resize((W//3,H//3)),(c*(W//3+10),r*(H//3+10)))
grid.save(O+'grid.jpg',quality=88)
