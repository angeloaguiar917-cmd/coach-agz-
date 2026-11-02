import sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter
S=sys.argv[1]; F=S+'/fonts/'
GOLD=(201,169,110); CREAM=(244,241,234); RED=(231,71,42); MUTED=(184,184,188); NAVY=(14,17,23); PANEL=(24,26,34); GREEN=(91,183,122)
def f(n,s): return ImageFont.truetype(F+n,s)
W,H=1080,1920
def grade(im):
    return _grade(im)
def _grade(im):
    im=im.convert('RGBA'); band=im.crop((0,1280,W,1640)).filter(ImageFilter.GaussianBlur(40)); im.paste(band,(0,1280))
    # gentle dark navy tint at bottom + vignette to unify footage with brand
    g=Image.new('RGBA',(W,H),(0,0,0,0)); d=ImageDraw.Draw(g)
    for y in range(H):
        a=0
        if y>H*0.46: a=int(min(1,(y-H*0.46)/(H*0.20))**1.1*245)
        if y<420: a=max(a,int((1-y/420)**1.5*215))
        d.line([(0,y),(W,y)],fill=NAVY+(a,))
    return Image.alpha_composite(im.convert('RGBA'),g)
def words(d,x,y,parts,font,track=0):
    for txt,col in parts:
        d.text((x,y),txt,font=font,fill=col); x+=d.textlength(txt,font=font)
    return x
def rule(d): d.rectangle([0,0,7,H],fill=GOLD)
def topbar(d,title,accent):
    d.rectangle([8,212,W,390],fill=NAVY+(235,))
    k=f('JBMono-500.ttf',30); d.line([(64,250),(112,250)],fill=GOLD,width=4)
    d.text((128,232),'@COACH.AGZ',font=k,fill=GOLD)
    words(d,64,276,[(title+' ',CREAM),(accent,GOLD)],f('BebasNeue.ttf',84))
def save(im,n): im.convert('RGB').save(S+'/mock/'+n,quality=92)

# A: hook
im=grade(Image.open(S+'/mock/src_1.0.png')); d=ImageDraw.Draw(im,'RGBA'); rule(d)
d.line([(64,1060),(124,1060)],fill=GOLD,width=5)
d.text((144,1040),'T H E   G Y N O   Q U E S T I O N',font=f('Barlow-600.ttf',40),fill=GOLD)
h=f('BebasNeue.ttf',200)
words(d,58,1095,[('CAN YOU',CREAM)],h)
words(d,58,1270,[('REVERSE ',GOLD),('IT?',CREAM)],h)
d.text((64,1470),'Surgery isn\'t your only option.',font=f('DMSans-400.ttf',46),fill=MUTED)
save(im,'A_hook.jpg')

# B: caption
im=grade(Image.open(S+'/mock/src_12.5.png')); d=ImageDraw.Draw(im,'RGBA'); rule(d); topbar(d,'CAN YOU REVERSE','GYNO?')
c=f('BebasNeue.ttf',122)
words(d,64,1130,[("IT'S REAL",CREAM)],c)
words(d,64,1252,[('GLANDULAR TISSUE.',GOLD)],c)
d.text((66,1395),'Not fat. Not water.',font=f('DMSans-700.ttf',50),fill=CREAM)
save(im,'B_caption.jpg')

# C: comparison panel over dimmed footage
src=Image.open(S+'/mock/src_64.5.png').convert('RGBA')
im=grade(src.filter(ImageFilter.GaussianBlur(18))); dim=Image.new('RGBA',(W,H),NAVY+(185,)); im=Image.alpha_composite(im,dim); d=ImageDraw.Draw(im,'RGBA'); rule(d); topbar(d,'CAN YOU REVERSE','GYNO?')
y0=820; bw=460; gap=32; x1=64; x2=x1+bw+gap
for x,top,head,rows,mark,mc in [(x1,GREEN,'SOFT + TENDER',['Active tissue','Still responds','Reversible'],'✓',GREEN),(x2,RED,'HARD + PAINLESS',['Fibrous scar','Won\'t respond','Surgery'],'✕',RED)]:
    d.rectangle([x,y0,x+bw,y0+560],fill=PANEL+(245,)); d.rectangle([x,y0,x+bw,y0+8],fill=top)
    d.text((x+36,y0+40),head,font=f('BebasNeue.ttf',72),fill=top)
    for i,r in enumerate(rows):
        yy=y0+160+i*120; (d.line([(x+38,yy+28),(x+50,yy+42),(x+72,yy+14)],fill=mc,width=6) if mark=='✓' else (d.line([(x+40,yy+14),(x+68,yy+42)],fill=mc,width=6),d.line([(x+68,yy+14),(x+40,yy+42)],fill=mc,width=6))); d.text((x+90,yy),r,font=f('DMSans-400.ttf',44),fill=CREAM)
        d.line([(x+36,yy+90),(x+bw-36,yy+90)],fill=(50,52,60),width=2)
d.text((64,1430),'If it\'s hard and painless, the tissue has fibrosed.',font=f('DMSans-400.ttf',40),fill=MUTED)
save(im,'C_compare.jpg')

# sheet with safe-zone guide on B
b=Image.open(S+'/mock/B_caption.jpg').copy(); g=ImageDraw.Draw(b,'RGBA')
g.rectangle([0,0,W,210],fill=(255,0,0,60)); g.rectangle([0,H-420,W,H],fill=(255,0,0,60)); g.rectangle([W-140,900,W,H-420],fill=(255,0,0,60))
g.text((20,170),'IG UI zone',font=f('JBMono-500.ttf',28),fill=(255,255,255)); g.text((20,H-400),'IG caption / buttons zone',font=f('JBMono-500.ttf',28),fill=(255,255,255))
b.save(S+'/mock/B_safezones.jpg',quality=88)
sheet=Image.new('RGB',(W*4//2,H//2))
for i,n in enumerate(['A_hook.jpg','B_caption.jpg','C_compare.jpg','B_safezones.jpg']):
    sheet.paste(Image.open(S+'/mock/'+n).resize((W//2,H//2)),(i*W//2,0))
sheet.save(S+'/mock/sheet.jpg',quality=88)
