from PIL import Image, ImageDraw, ImageFilter
import random, math
S = 4
OUT = (0x3E, 0x27, 0x23, 255)
def C(h, a=255):
    h = h.lstrip('#'); return (int(h[0:2],16), int(h[2:4],16), int(h[4:6],16), a)
def sh(c, f):  # shade / lighten
    return tuple(max(0,min(255,int(v*f))) if i<3 else v for i,v in enumerate(c))
GREEN=C('16A34A'); GOLD=C('F59E0B'); BLUE=C('0284C7'); BROWN=C('78350F'); CREAM=C('FEFCE8'); SKIN=C('FDDCA5')

class D:
    def __init__(s, w, h, scale=S):
        s.k = scale; s.im = Image.new('RGBA', (w*scale, h*scale), (0,0,0,0)); s.d = ImageDraw.Draw(s.im)
    def b(s, box): return [v*s.k for v in box]
    def rr(s, box, r, fill, ow=3, out=OUT):
        s.d.rounded_rectangle(s.b(box), r*s.k, fill=fill, outline=out if ow else None, width=int(ow*s.k))
    def el(s, box, fill, ow=3, out=OUT):
        s.d.ellipse(s.b(box), fill=fill, outline=out if ow else None, width=int(ow*s.k))
    def poly(s, pts, fill, ow=3, out=OUT):
        p = [(x*s.k, y*s.k) for x,y in pts]
        s.d.polygon(p, fill=fill)
        if ow: s.d.line(p+[p[0]], fill=out, width=int(ow*s.k), joint='curve')
    def line(s, pts, col, w):
        s.d.line([(x*s.k,y*s.k) for x,y in pts], fill=col, width=int(w*s.k), joint='curve')
    def shadow(s, cx, cy, rx, ry, a=70):
        l = Image.new('RGBA', s.im.size, (0,0,0,0)); ImageDraw.Draw(l).ellipse(s.b([cx-rx,cy-ry,cx+rx,cy+ry]), fill=(30,20,10,a))
        s.im.alpha_composite(l); s.d = ImageDraw.Draw(s.im)
    def done(s):
        return s.im.resize((s.im.width//s.k, s.im.height//s.k), Image.LANCZOS)

def paste(sheet, cell, col, row, cw, ch): sheet.alpha_composite(cell, (col*cw, row*ch))

# ---------------------------------------------------------------- BIMA
def bima(dirn, f):
    g = D(128,128); bob = [0,-2,0,-2][f]; sw = [0,6,0,-6][f]
    g.shadow(64,116,27,8)
    skin=SKIN; hatc=C('F4C14D'); 
    def legs():
        if dirn in ('down','up'):
            for x,lift in ((50,max(0,sw)),(74,max(0,-sw))):
                g.rr((x,94-lift+bob*0,x+14,114-lift),5,C('F59E0B'))
                g.rr((x,92-lift,x+14,102-lift),3,BROWN)
        else:
            for x,off in ((54,sw),(66,-sw)):
                g.rr((x+off*0.6,92,x+off*0.6+14,102),3,BROWN)
                g.rr((x+off*0.6-(2 if dirn=='left' else -2),98,x+off*0.6+14+(0 if dirn=='left' else 4),114),5,C('F59E0B'))
    legs()
    # arms behind for side
    if dirn in ('left','right'):
        ax = 64 + (-sw*0.8)
        g.el((ax-6,74+bob,ax+8,90+bob),skin,2.5)
    # torso: shirt + vest
    g.rr((44,64+bob,84,98+bob),10,CREAM)
    g.rr((44,64+bob,60,98+bob),9,GREEN); g.rr((68,64+bob,84,98+bob),9,GREEN)
    g.rr((44,86+bob,84,100+bob),6,BROWN)
    g.line([(64,68+bob),(64,86+bob)],OUT,2)
    g.el((60,80+bob,68,88+bob),GOLD,2)
    if dirn in ('down','up'):
        for x,sg in ((36,sw),(82,-sw)):
            g.el((x,72+bob+sg*0.5,x+12,88+bob+sg*0.5),skin,2.5)
    else:
        ax = 64 + (sw*0.8)
        g.el((ax-6,74+bob,ax+8,90+bob),skin,2.5)
    # head
    hx = 64 + (-3 if dirn=='left' else 3 if dirn=='right' else 0)
    g.el((hx-23,26+bob,hx+23,70+bob),skin)
    hair=C('3B2314')
    if dirn=='up':
        g.el((hx-23,28+bob,hx+23,70+bob),hair)
    else:
        g.d.pieslice(g.b((hx-23,26+bob,hx+23,70+bob)),180,360,fill=hair)
        g.d.arc(g.b((hx-23,26+bob,hx+23,70+bob)),0,360,fill=OUT,width=3*S)
    if dirn=='down':
        for x in (-9,9): g.el((hx+x-3.5,50+bob,hx+x+3.5,58+bob),OUT,0); g.el((hx+x-1.5,51+bob,hx+x+1,54+bob),(255,255,255,255),0)
        g.el((hx-17,57+bob,hx-10,62+bob),C('FCA5A5'),0); g.el((hx+10,57+bob,hx+17,62+bob),C('FCA5A5'),0)
        g.d.arc(g.b((hx-5,56+bob,hx+5,64+bob)),20,160,fill=OUT,width=2*S)
    elif dirn in ('left','right'):
        d=-1 if dirn=='left' else 1
        g.el((hx+d*10-3.5,50+bob,hx+d*10+3.5,58+bob),OUT,0); g.el((hx+d*10-1,51+bob,hx+d*10+1.5,54+bob),(255,255,255,255),0)
        g.el((hx+d*5-4,58+bob,hx+d*5+3,63+bob),C('FCA5A5'),0)
        g.poly([(hx+d*22,56+bob),(hx+d*26,60+bob),(hx+d*22,62+bob)],skin,2)
    # straw hat
    g.el((hx-34,28+bob,hx+34,46+bob),hatc)
    g.d.pieslice(g.b((hx-21,8+bob,hx+21,44+bob)),180,360,fill=hatc); g.d.arc(g.b((hx-21,8+bob,hx+21,44+bob)),180,360,fill=OUT,width=3*S)
    g.line([(hx-21,32+bob),(hx+21,32+bob)],C('D97706'),3)
    g.rr((hx-8,16+bob,hx+8,28+bob),3,BLUE,2); g.line([(hx,16+bob),(hx,28+bob)],C('BAE6FD'),1); g.line([(hx-8,22+bob),(hx+8,22+bob)],C('BAE6FD'),1)
    g.el((hx-28,30+bob,hx-14,35+bob),sh(hatc,1.2),0)
    return g.done()

# ---------------------------------------------------------------- PIKO
def piko(kind):
    g = D(128,128); fur=GOLD; dark=C('D97706')
    bob = -6 if kind==3 else 0
    g.shadow(64,112,30 if kind!=3 else 22,7)
    tail_w = 6*math.sin(kind*1.6)
    g.line([(86,96+bob),(104,86+bob+tail_w),(108,66+bob+tail_w)],OUT,13); g.line([(86,96+bob),(104,86+bob+tail_w),(108,66+bob+tail_w)],fur,8)
    legs = {0:[(46,0),(80,0)],1:[(44,-6),(82,0)],2:[(48,0),(78,-6)],3:[(46,-4),(80,-4)]}[kind]
    if kind==0:
        g.el((32,70,98,112),fur)
    else:
        g.rr((30,70,98,106+bob),22,fur)
        for x,l in legs: g.rr((x-6,96+l+bob,x+10,112+l+(bob if kind==3 else 0)),5,fur)
    g.el((46,84+bob,84,108+bob) if kind==0 else (48,82+bob,80,102+bob),CREAM,0)
    for x in (44,56,68): g.line([(x,74+bob),(x+3,82+bob)],dark,3)
    g.el((24,36+bob,78,86+bob),fur)  # head
    g.poly([(28,50+bob),(30,24+bob),(46,40+bob)],fur); g.poly([(74,50+bob),(72,24+bob),(56,40+bob)],fur)
    g.poly([(32,44+bob),(33,32+bob),(41,41+bob)],C('FCA5A5'),0); g.poly([(70,44+bob),(69,32+bob),(61,41+bob)],C('FCA5A5'),0)
    if kind==3:
        g.d.arc(g.b((36,54+bob,48,64+bob)),200,340,fill=OUT,width=3*S); g.d.arc(g.b((54,54+bob,66,64+bob)),200,340,fill=OUT,width=3*S)
    else:
        for x in (42,60): g.el((x-4,54+bob,x+4,64+bob),OUT,0); g.el((x-1.5,55+bob,x+1.5,59+bob),(255,255,255,255),0)
    g.poly([(48,66+bob),(54,66+bob),(51,70+bob)],C('FB7185'),1.5)
    g.d.arc(g.b((44,66+bob,51,74+bob)),20,160,fill=OUT,width=2*S); g.d.arc(g.b((51,66+bob,58,74+bob)),20,160,fill=OUT,width=2*S)
    for y in (66,70): g.line([(26,y+bob),(14,y-2+bob)],OUT,1.5); g.line([(76,y+bob),(88,y-2+bob)],OUT,1.5)
    g.rr((34,78+bob,70,88+bob),5,GREEN,2.5); g.poly([(50,86+bob),(60,86+bob),(58,100+bob),(50,98+bob)],sh(GREEN,0.85),2)
    return g.done()

# ---------------------------------------------------------------- NPC
def npc(kind, pose):
    g = D(128,128); g.shadow(64,116,26,8)
    if kind=='ratna':
        g.rr((48,94,60,114),4,SKIN); g.rr((68,94,80,114),4,SKIN)
        g.el((44,108,62,118),C('92400E')); g.el((66,108,84,118),C('92400E'))
        g.rr((40,62,88,102),14,GREEN)
        g.poly([(52,70),(76,70),(84,102),(44,102)],GOLD,2.5)  # apron
        sx,sy=64,86; g.el((sx-6,sy-6,sx+6,sy+6),C('FDE047'),1.5); g.el((sx-2.5,sy-2.5,sx+2.5,sy+2.5),BROWN,0)
        if pose==0:
            g.rr((28,78,48,92),3,C('B45309'),2.5); g.line([(28,78),(48,78)],C('FDE68A'),2)
            for x,c in ((33,'EF4444'),(41,'FACC15')): g.el((x-4,72,x+4,80),C(c),1.5)
            g.el((30,82,42,94),SKIN,2.5); g.el((84,76,96,90),SKIN,2.5)
        else:
            g.el((38,80,50,92),SKIN,2.5); g.rr((86,48,98,80),6,GREEN); g.el((84,38,100,54),SKIN,2.5)
        g.el((41,24,87,68),SKIN)
        g.el((38,20,90,46),C('1F1411')); g.el((46,6,70,28),C('1F1411')); g.el((50,22,82,46),SKIN,0)
        g.d.arc(g.b((40,22,88,66)),180,360,fill=C('1F1411'),width=10*S)
        g.el((52,52,60,60),OUT,0); g.el((68,52,76,60),OUT,0); g.d.arc(g.b((57,57,71,68)),10,170,fill=OUT,width=2*S)
        g.el((46,58,54,64),C('FCA5A5'),0); g.el((74,58,82,64),C('FCA5A5'),0)
        g.el((84,34,92,42),C('FDE047'),1.5)
    else:
        g.rr((46,92,60,114),4,BROWN); g.rr((68,92,82,114),4,BROWN)
        g.rr((44,110,62,118),4,C('1F2937')); g.rr((66,110,84,118),4,C('1F2937'))
        g.rr((40,62,88,100),12,BLUE); g.rr((40,70,56,100),8,BROWN); g.rr((72,70,88,100),8,BROWN)
        if pose==0:
            g.rr((30,70,52,98),3,C('F8FAFC'),2.5); g.rr((36,66,46,72),2,C('94A3B8'),2)
            for y in (78,84,90): g.line([(34,y),(48,y)],C('94A3B8'),1.5)
            g.line([(40,92),(46,78),(40,80)],GREEN,1.5)
            g.el((30,88,42,100),SKIN,2.5); g.el((84,80,96,94),SKIN,2.5)
        else:
            g.el((34,82,46,94),SKIN,2.5); g.rr((88,56,100,82),6,BLUE); g.rr((86,38,102,60),7,SKIN)
            g.rr((92,30,98,46),3,SKIN,2); g.line([(92,60),(100,60)],OUT,1.5)
        g.el((41,24,87,68),SKIN)
        g.d.arc(g.b((41,56,87,76)),20,160,fill=C('5C4033'),width=8*S)
        g.el((52,48,60,57),OUT,0); g.el((68,48,76,57),OUT,0); g.d.arc(g.b((57,54,71,66)),10,170,fill=OUT,width=2*S)
        g.el((46,56,54,62),C('FCA5A5'),0); g.el((74,56,82,62),C('FCA5A5'),0)
        g.d.pieslice(g.b((38,6,90,52)),180,360,fill=C('F8FAFC')); g.d.arc(g.b((38,6,90,52)),180,360,fill=OUT,width=3*S)
        g.rr((34,28,94,38),5,C('F8FAFC'))
        g.poly([(66,12),(58,24),(64,24),(60,34),(72,20),(65,20)],C('22C55E'),1.5)
    return g.done()

# ---------------------------------------------------------------- CROPS
def leaf(g, x, y, ang, L, col):
    a = math.radians(ang); dx, dy = math.cos(a), -math.sin(a); px, py = -dy, dx
    ex, ey = x+dx*L, y+dy*L; mx, my = x+dx*L*0.5, y+dy*L*0.5; w = L*0.34
    g.poly([(x,y),(mx+px*w,my+py*w),(ex,ey),(mx-px*w,my-py*w)],col,2.5)
    g.line([(x,y),(ex*0.9+x*0.1,ey*0.9+y*0.1)],sh(col,0.75),1.5)
def mound(g):
    g.shadow(64,108,34,8,60); g.el((34,96,94,114),C('92522B')); g.el((38,97,88,108),sh(C('92522B'),1.2),0)
def crop(kind, st):
    g = D(128,128); mound(g); lg=C('22C55E'); dg=C('15803D')
    if st==0:
        for x,y in ((52,100),(64,103),(76,100)): g.el((x-5,y-4,x+5,y+4),C('FEF08A'),2)
        return g.done()
    h = [0,22,44,60][st]
    if kind=='tomat':
        g.line([(64,104),(64,104-h)],OUT,8); g.line([(64,104),(64,104-h)],dg,4)
        for i in range(st*2):
            y=100-i*(h/(st*2+1))*1.0; leaf(g,64,y,(40 if i%2 else 140),12+st*4,lg)
        if st==3:
            for x,y in ((46,66),(80,62),(58,48),(72,80)): g.el((x-9,y-9,x+9,y+9),C('EF4444')); g.el((x-5,y-6,x-1,y-2),C('FCA5A5'),0); leaf(g,x,y-8,90,6,dg)
    elif kind=='jagung':
        g.line([(64,104),(64,104-h-10)],OUT,10); g.line([(64,104),(64,104-h-10)],C('65A30D'),6)
        for i in range(st+1):
            y=100-i*(h/3.5); leaf(g,64,y,(25 if i%2 else 155),18+st*6,lg)
        if st==3:
            for x,y,d in ((70,62,1),(58,50,-1)):
                g.poly([(x-7,y+12),(x+7,y+12),(x+6,y-12),(x,y-18),(x-6,y-12)],C('FACC15'),2.5)
                g.poly([(x-8,y+14),(x,y+4),(x,y-10),(x-8,y-2)],lg,2); g.poly([(x+8,y+14),(x,y+4),(x,y-10),(x+8,y-2)],dg,2)
            g.line([(64,40),(60,32)],C('FDE68A'),2); g.line([(64,40),(70,32)],C('FDE68A'),2)
    elif kind=='kentang':
        n=[0,3,5,7][st]
        for i in range(n):
            a=20+i*(140/max(1,n-1)); leaf(g,64,100,a,14+st*7,lg if i%2 else dg)
        if st==3:
            g.el((38,96,56,110),C('D4A056')); g.el((70,98,92,112),C('D4A056')); 
            for x,y in ((45,102),(80,105)): g.el((x-1,y-1,x+2,y+2),C('92400E'),0)
            for x,y in ((60,52),(52,58)): g.el((x-5,y-5,x+5,y+5),C('FEF3C7'),1.5)
    else:  # padi
        n=[0,4,6,8][st]
        for i in range(n):
            a=45+i*(90/max(1,n-1)); L=18+st*9
            g.line([(64,104),(64+math.cos(math.radians(a))*L,104-math.sin(math.radians(a))*L)],OUT,6)
            g.line([(64,104),(64+math.cos(math.radians(a))*L,104-math.sin(math.radians(a))*L)],lg if st<3 else C('A3E635'),3)
        if st==3:
            for i,(dx) in enumerate((-18,-8,4,14,24)):
                x=64+dx*0.9; y=62-abs(dx)*0.2
                g.line([(64+dx*0.3,100),(x,y)],C('A16207'),2); g.el((x-3,y-3,x+9,y+14),C('FACC15'),2)
    return g.done()

# ---------------------------------------------------------------- ECO ICONS
def eco(kind):
    g = D(128,128); g.shadow(64,112,40,9)
    if kind==0:  # solar pump
        g.rr((50,86,78,112),5,C('94A3B8')); g.rr((54,92,74,100),2,C('475569'),1.5)
        g.poly([(24,78),(100,78),(112,50),(36,50)],BLUE,3)
        for t in (0.33,0.66): g.line([(24+(100-24)*t,78),(36+(112-36)*t,50)],C('BAE6FD'),1.5)
        g.line([(30,64),(106,64)],C('BAE6FD'),1.5); g.line([(36,50),(24,78)],C('7DD3FC'),0)
        g.line([(64,78),(64,88)],OUT,5)
        g.poly([(94,86),(100,98),(88,98)],C('38BDF8'),2); g.el((88,94,100,104),C('38BDF8'),2)
        g.el((12,8,34,30),C('FDE047')); 
        for a in range(0,360,45): g.line([(23+math.cos(math.radians(a))*13,19+math.sin(math.radians(a))*13),(23+math.cos(math.radians(a))*19,19+math.sin(math.radians(a))*19)],C('F59E0B'),3)
    elif kind==1:  # biogas
        g.rr((28,66,100,112),10,C('E2E8F0')); g.d.pieslice(g.b((28,28,100,104)),180,360,fill=GREEN); g.d.arc(g.b((28,28,100,104)),180,360,fill=OUT,width=3*S)
        g.rr((28,66,100,112),10,None,3)
        g.d.pieslice(g.b((34,34,70,70)),180,270,fill=sh(GREEN,1.35))
        g.rr((38,86,62,112),4,C('92400E')); g.rr((74,80,92,96),3,C('94A3B8'),2.5)
        g.rr((98,60,106,90),3,C('94A3B8'),2.5); g.rr((98,56,118,66),3,C('94A3B8'),2.5)
        g.poly([(108,56),(102,44),(108,38),(113,46),(118,40),(116,52),(112,56)],C('FB923C'),2); g.poly([(109,54),(106,48),(111,44),(112,52)],C('FDE047'),0)
        g.el((60,8,76,24),C('F8FAFC'),2); g.el((70,2,88,18),C('F8FAFC'),2)
        g.d.arc(g.b((48,74,64,90)),0,360,fill=C('FDE047'),width=3*S)
    else:  # water wheel
        g.rr((6,92,122,116),8,C('38BDF8'))
        for x in (12,40,70,96): g.d.arc(g.b((x,98,x+22,110)),200,340,fill=C('E0F2FE'),width=2*S)
        g.rr((58,44,70,100),3,BROWN); g.rr((18,98,38,112),3,C('94A3B8'),2); 
        cx,cy=64,60
        g.el((cx-42,cy-42,cx+42,cy+42),None,5,BROWN)
        for a in range(0,360,45):
            r=math.radians(a); g.line([(cx,cy),(cx+math.cos(r)*40,cy+math.sin(r)*40)],OUT,6); g.line([(cx,cy),(cx+math.cos(r)*40,cy+math.sin(r)*40)],C('B45309'),3)
            px,py=cx+math.cos(r)*42,cy+math.sin(r)*42; g.poly([(px-6,py-4),(px+6,py-4),(px+6,py+6),(px-6,py+6)],GOLD,2)
        g.el((cx-9,cy-9,cx+9,cy+9),GOLD); g.poly([(cx-1,cy-6),(cx-6,cy+1),(cx,cy+1),(cx-2,cy+7),(cx+6,cy-2),(cx,cy-2)],C('FEF9C3'),0)
    return g.done()

# ---------------------------------------------------------------- TILESET (256 cells)
def soil(kind):
    g = D(256,256); fill={0:C('D6A374'),1:C('9A5B32'),2:C('5C3A21')}[kind]
    g.rr((14,14,242,242),34,fill,5)
    g.rr((24,22,232,60),24,sh(fill,1.18),0)
    if kind>0:
        for i in range(4):
            y=62+i*46; g.rr((38,y,218,y+16),8,sh(fill,0.78),0); g.line([(40,y+2),(216,y+2)],sh(fill,1.2),3)
    else:
        random.seed(3)
        for _ in range(26):
            x,y=random.randint(34,220),random.randint(34,220); g.el((x,y,x+8,y+5),sh(fill,0.85),0)
    if kind==2:
        for x,y in ((60,70),(150,150),(190,70),(90,190)): g.el((x,y,x+16,y+10),C('38BDF8',150),0)
    return g.done()
def grass():
    g = D(256,256); g.d.rectangle(g.b((0,0,256,256)),fill=C('4ADE80'))
    random.seed(7)
    for _ in range(90):
        x,y=random.randint(0,255),random.randint(0,255); c=random.choice([C('22C55E'),C('86EFAC'),C('16A34A')])
        for dx in (-256,0,256):
            for dy in (-256,0,256):
                g.line([(x+dx,y+dy),(x+dx-4,y+dy-12)],c,3); g.line([(x+dx,y+dy),(x+dx+5,y+dy-10)],c,3)
    for _ in range(10):
        x,y=random.randint(10,245),random.randint(10,245); g.el((x-3,y-3,x+3,y+3),C('FEF9C3'),0)
    return g.done()
def path():
    g = D(256,256); g.d.rectangle(g.b((0,0,256,256)),fill=C('FDE9B0'))
    random.seed(11)
    for _ in range(40):
        x,y=random.randint(0,240),random.randint(0,240); g.el((x,y,x+random.randint(8,16),y+random.randint(5,9)),random.choice([C('E7C77C'),C('F5D68A'),C('D8B565')]),0)
    return g.done()
def water():
    g = D(256,256); g.d.rectangle(g.b((0,0,256,256)),fill=C('0EA5E9'))
    for y in (30,100,170,230):
        for x in (0,128): g.d.arc(g.b((x-10,y-10,x+70,y+16)),200,340,fill=C('7DD3FC'),width=5*S); g.d.arc(g.b((x+50,y+40,x+120,y+62)),200,340,fill=C('BAE6FD'),width=4*S)
    return g.done()
def house():
    g = D(256,256); g.shadow(128,236,100,14,60)
    g.rr((38,110,218,228),10,C('FDE9B0'))
    for x in range(46,218,30): g.line([(x,114),(x,224)],C('F5D68A'),2)
    g.rr((166,40,190,92),4,C('A8A29E'),3); g.rr((162,34,194,50),4,C('78716C'),3)
    g.poly([(18,120),(128,34),(238,120)],C('C2410C'),4)
    g.poly([(30,118),(128,44),(226,118)],C('EA580C'),0)
    for i in range(5): g.line([(40+i*24,112-i*2),(128,48+0)],C('9A3412'),0)
    g.poly([(62,108),(120,66),(150,66),(150,108)],BLUE,3)
    for t in (0.34,0.67): g.line([(62+ (150-62)*t,108),(120+(150-120)*t,66)],C('BAE6FD'),2)
    g.line([(106,87),(150,87)],C('BAE6FD'),2)
    g.rr((60,148,116,228),8,C('92400E')); g.line([(88,150),(88,226)],C('78350F'),3); g.el((100,186,108,194),GOLD,2)
    g.rr((132,150,202,204),8,C('FDE047')); g.line([(167,152),(167,202)],OUT,3); g.line([(134,177),(200,177)],OUT,3)
    g.rr((126,204,208,218),4,C('92400E'))
    for x,c in ((138,'F43F5E'),(158,'FDE047'),(178,'FB7185'),(196,'F43F5E')): g.el((x-8,194,x+8,210),C('22C55E'),2); g.el((x-5,192,x+5,202),C(c),2)
    return g.done()
def shop():
    g = D(256,256); g.shadow(128,236,104,14,60)
    g.rr((36,108,220,228),10,C('FEF9C3'))
    g.rr((30,50,226,122),12,GREEN)
    for i in range(7):
        x=34+i*28; g.poly([(x,118),(x+28,118),(x+26,142),(x+14,150),(x+2,142)],C('F8FAFC') if i%2 else GREEN,3)
    g.rr((72,70,184,104),8,C('FACC15'),3); g.el((122,76,134,88),C('F97316'),0)
    for x in (92,152): g.el((x,78,x+10,92),BROWN,0)
    g.rr((54,164,126,228),6,C('92400E')); g.rr((60,170,120,200),4,C('FDE68A'),2.5)
    g.rr((140,176,208,228),6,C('B45309'))
    for x,y,c in ((148,168,'EF4444'),(166,166,'FACC15'),(186,168,'F97316')): g.el((x,y,x+20,y+20),C(c))
    g.rr((138,196,210,230),5,C('D97706'),3)
    g.line([(148,196),(148,230)],OUT,2); g.line([(174,196),(174,230)],OUT,2)
    return g.done()
def station():
    g = D(256,256); g.shadow(128,236,104,14,60)
    g.rr((36,110,220,228),10,C('E0F2FE'))
    g.poly([(24,120),(128,52),(232,120)],BLUE,4); g.poly([(42,118),(128,62),(214,118)],C('38BDF8'),0)
    g.rr((120,14,128,60),2,C('94A3B8'),2.5)
    for a in (20,140,260):
        r=math.radians(a); g.line([(124,14),(124+math.cos(r)*30,14-math.sin(r)*30)],OUT,8); g.line([(124,14),(124+math.cos(r)*30,14-math.sin(r)*30)],C('F8FAFC'),4)
    g.el((118,8,130,20),GOLD,2)
    g.poly([(138,84),(118,118),(130,118),(122,142),(150,104),(137,104),(146,84)],C('FDE047'),3)
    g.rr((54,150,112,228),8,C('0369A1')); g.rr((62,158,104,196),4,C('BAE6FD'),2.5)
    g.rr((132,150,204,206),8,C('1E293B')); g.rr((140,158,196,198),4,C('0F172A'),0)
    for i,hgt in enumerate((14,24,32,22)): g.rr((146+i*12,194-hgt,154+i*12,194),2,C('4ADE80'),1.5)
    g.rr((60,208,100,226),4,GOLD,2.5)
    return g.done()
def well():
    g = D(256,256); g.shadow(128,232,92,14,60)
    g.el((50,140,206,226),C('94A3B8')); g.rr((50,150,206,208),22,C('CBD5E1'))
    for x in range(58,200,28): g.line([(x,152),(x,206)],C('94A3B8'),2)
    g.el((60,134,196,184),C('94A3B8')); g.el((74,142,182,176),C('0369A1'),3); g.el((92,150,160,168),C('38BDF8'),0)
    g.rr((54,70,70,170),4,C('92400E')); g.rr((186,70,202,170),4,C('92400E'))
    g.rr((50,64,206,78),4,C('B45309'))
    g.poly([(36,70),(128,16),(220,70)],C('B45309'),4); g.poly([(52,68),(128,26),(204,68)],C('D97706'),0)
    g.line([(128,70),(128,112)],OUT,3); g.rr((116,108,140,130),4,C('A16207'),2.5)
    g.rr((208,170,236,210),6,C('94A3B8'),3); g.rr((228,190,248,204),4,C('94A3B8'),3)
    return g.done()
def tree():
    g = D(256,256); g.shadow(128,236,70,12,60)
    g.rr((108,140,148,232),12,C('92400E')); g.line([(122,150),(122,220)],C('78350F'),3)
    for (x,y,r,c) in ((128,78,60,'16A34A'),(80,116,46,'22C55E'),(176,116,46,'22C55E'),(128,128,52,'16A34A')): g.el((x-r,y-r,x+r,y+r),C(c))
    for (x,y,r) in ((104,56,18),(70,100,13),(160,96,12)): g.el((x-r,y-r,x+r,y+r),C('4ADE80'),0)
    for x,y in ((100,100),(150,80),(176,128),(86,134),(128,120)): g.el((x-8,y-8,x+8,y+8),C('EF4444'),2)
    return g.done()
def bush():
    g = D(256,256); g.shadow(128,214,76,12,60)
    for (x,y,r) in ((90,170,44),(168,170,44),(128,148,56)): g.el((x-r,y-r,x+r,y+r),C('22C55E'))
    for (x,y) in ((90,160),(140,128),(170,168),(116,176)): g.el((x-8,y-8,x+8,y+8),C('F9A8D4'),2)
    return g.done()
def flowers():
    g = D(256,256); random.seed(5)
    for x,y,c in ((70,180,'F43F5E'),(120,150,'FACC15'),(170,185,'A78BFA'),(100,210,'FB923C'),(150,120,'F472B6'),(190,150,'FDE047')):
        g.line([(x,y),(x,y+40)],C('15803D'),5)
        for a in range(0,360,72): r=math.radians(a); g.el((x+math.cos(r)*12-8,y+math.sin(r)*12-8,x+math.cos(r)*12+8,y+math.sin(r)*12+8),C(c),2.5)
        g.el((x-7,y-7,x+7,y+7),C('FEF08A'),2)
    return g.done()
def rocks():
    g = D(256,256); g.shadow(128,214,70,12,60)
    for (x,y,w,h,c) in ((70,150,86,60,'A8A29E'),(140,130,80,76,'CBD5E1'),(110,186,60,36,'94A3B8')):
        g.rr((x,y,x+w,y+h),24,C(c)); g.rr((x+8,y+6,x+w*0.5,y+h*0.35),10,sh(C(c),1.15),0)
    return g.done()
def fence():
    g = D(256,256)
    for x in (30,110,190): g.rr((x,100,x+28,230),8,C('B45309')); g.el((x+4,92,x+24,112),C('D97706'),2.5)
    for y in (130,180): g.rr((14,y,242,y+22),6,C('D97706'))
    return g.done()
def sign():
    g = D(256,256); g.shadow(128,232,50,10,60)
    g.rr((116,110,140,232),6,C('92400E')); g.rr((50,56,206,124),12,C('FDE68A')); g.rr((60,66,196,114),8,C('FEF3C7'),2)
    g.poly([(70,90),(86,76),(86,84),(120,84),(120,96),(86,96),(86,104)],GREEN,2)
    return g.done()

# ---------------------------------------------------------------- COVER
def cover():
    W,H,K = 1920,1080,2
    g = D(W,H,K)
    sky = Image.new('RGBA',(W*K,H*K)); sd = ImageDraw.Draw(sky)
    for y in range(H*K):
        t=y/(H*K*0.75); t=min(1,t); c=tuple(int(a+(b-a)*t) for a,b in zip((56,160,230),(254,226,160)))
        sd.line([(0,y),(W*K,y)],fill=c+(255,))
    g.im.alpha_composite(sky)
    glow = Image.new('RGBA',(W*K,H*K),(0,0,0,0)); gd=ImageDraw.Draw(glow)
    for r,a in ((520,10),(420,14),(320,20),(240,30),(180,45)): gd.ellipse([(1480-r)*K,(220-r)*K,(1480+r)*K,(220+r)*K],fill=(255,240,180,a))
    glow = glow.filter(ImageFilter.GaussianBlur(90)); g.im.alpha_composite(glow); g.d = ImageDraw.Draw(g.im)
    g.el((1400,140,1560,300),C('FDE047'),0)
    random.seed(2)
    for cx,cy,s in ((300,150,1.2),(820,100,0.9),(1180,240,0.8),(1700,90,1.0)):
        for dx,dy,r in ((0,0,48),(-48,14,36),(52,16,40),(100,26,30),(-90,28,26)):
            g.el(((cx+dx-r*s),(cy+dy-r*0.8*s),(cx+dx+r*s),(cy+dy+r*0.8*s)),(255,255,255,235),0)
    # hills
    def hill(y0,amp,col,ph):
        pts=[(0,H)]+[(x,y0+math.sin(x/260+ph)*amp+math.sin(x/90+ph*2)*amp*0.25) for x in range(0,W+20,20)]+[(W,H)]
        g.poly(pts,col,0)
    hill(560,50,C('86EFAC'),0.5); hill(620,60,C('4ADE80'),2.0)
    # windmill & solar farm on far hill
    def windmill(x,y,s=1.0):
        g.poly([(x-18*s,y),(x+18*s,y),(x+10*s,y-110*s),(x-10*s,y-110*s)],C('F8FAFC'),3)
        t=(pygame_t:=0.4)
        for a in (20,140,260):
            r=math.radians(a); g.line([(x,y-112*s),(x+math.cos(r)*70*s,y-112*s-math.sin(r)*70*s)],OUT,10*s); g.line([(x,y-112*s),(x+math.cos(r)*70*s,y-112*s-math.sin(r)*70*s)],C('E2E8F0'),5*s)
        g.el((x-9*s,y-121*s,x+9*s,y-103*s),GOLD,3)
    windmill(1180,640,1.1); windmill(1330,625,0.8); windmill(1030,650,0.9)
    for i in range(6):
        x=1480+i*70; g.poly([(x,640),(x+60,640),(x+72,600),(x+12,600)],BLUE,3); g.line([(x+30,640),(x+30,660)],OUT,4)
    # village houses
    def hut(x,y,s,wall,roof):
        g.rr((x,y,x+130*s,y+90*s),6,wall,3); g.poly([(x-14*s,y+4),(x+65*s,y-62*s),(x+144*s,y+4)],roof,3)
        g.rr((x+14*s,y+30*s,x+50*s,y+90*s),4,C('92400E'),3); g.rr((x+76*s,y+26*s,x+112*s,y+58*s),4,C('FDE047'),3)
    hut(900,690,0.9,C('FDE9B0'),C('C2410C')); hut(1090,700,0.8,C('FEF9C3'),GREEN); hut(1560,690,0.9,C('E0F2FE'),BLUE)
    # river
    g.poly([(0,1000),(300,960)]+[(x,950+math.sin(x/160)*14) for x in range(300,W+20,20)]+[(W,H),(0,H)],C('0EA5E9'),0)
    for x,y in ((220,1030),(620,1010),(1020,1040),(1420,1015),(1760,1040)): g.d.arc(g.b((x,y,x+160,y+28)),200,340,fill=C('BAE6FD'),width=6*K)
    # fields
    g.poly([(0,860),(W,820),(W,960),(0,1000)],C('A16207'),0)
    for r in range(4):
        y0=830+r*30
        g.poly([(0,y0+40),(W,y0),(W,y0+16),(0,y0+56)],C('78350F'),0)
    for r in range(4):
        for i in range(24):
            x=60+i*80+ (r%2)*40; y=855+r*28 - (x/W)*38
            c=[C('EF4444'),C('FACC15'),C('D4A056'),C('FDE047')][ (i+r)%4]
            g.el((x-10,y-30,x+10,y-4),C('22C55E'),2); g.el((x-6,y-26,x+6,y-12),c,2)
    # tree + fence + flowers foreground
    def tree_(x,y,s):
        g.rr((x-16*s,y-70*s,x+16*s,y),8,C('92400E'),3)
        for dx,dy,r in ((0,-130,80),(-60,-90,60),(60,-90,60),(0,-80,66)): g.el((x+dx*s-r*s,y+dy*s-r*s,x+dx*s+r*s,y+dy*s+r*s),C('16A34A') if dy>-100 else C('22C55E'),3)
    tree_(1000,740,0.9); tree_(1850,770,1.3)
    for x in range(1050,1700,38): g.rr((x,775,x+14,830),3,C('D97706'),2)
    g.rr((1050,796,1706,808),3,C('B45309'),2)
    random.seed(9)
    for _ in range(40):
        x,y=random.randint(40,860),random.randint(735,800); cc=random.choice(['F43F5E','FACC15','A78BFA','F472B6'])
        g.line([(x,y),(x,y+14)],C('15803D'),3); g.el((x-6,y-6,x+6,y+6),C(cc),2)
    # soft vignette for text readability
    im = g.done()
    return im.convert('RGBA')

if __name__ == '__main__':
    import os; os.makedirs('asset', exist_ok=True)
    sheet = Image.new('RGBA',(512,512),(0,0,0,0))
    for r,d in enumerate(('down','up','left','right')):
        for c in range(4): paste(sheet, bima(d,c), c, r, 128,128)
    sheet.save('asset/char_bima.png')
    sheet = Image.new('RGBA',(256,256),(0,0,0,0))
    for i in range(4): paste(sheet, piko(i), i%2, i//2, 128,128)
    sheet.save('asset/char_piko.png')
    for k in ('ratna','surya'):
        sheet = Image.new('RGBA',(256,128),(0,0,0,0))
        for p in range(2): paste(sheet, npc(k,p), p, 0, 128,128)
        sheet.save(f'asset/npc_{k}.png')
    sheet = Image.new('RGBA',(512,512),(0,0,0,0))
    for r,k in enumerate(('tomat','jagung','kentang','padi')):
        for st in range(4): paste(sheet, crop(k,st), st, r, 128,128)
    sheet.save('asset/crops_stages.png')
    sheet = Image.new('RGBA',(384,128),(0,0,0,0))
    for i in range(3): paste(sheet, eco(i), i, 0, 128,128)
    sheet.save('asset/eco_tech_icons.png')
    cells = [soil(0),soil(1),soil(2),grass(), house(),shop(),station(),well(), tree(),bush(),flowers(),rocks(), path(),water(),fence(),sign()]
    sheet = Image.new('RGBA',(1024,1024),(0,0,0,0))
    for i,c in enumerate(cells): paste(sheet, c, i%4, i//4, 256,256)
    sheet.save('asset/tileset_village.png')
    cover().convert('RGB').save('asset/cover_bg.png')
    print('ok')
