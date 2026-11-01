"""Model 3D karakter (SDF): Bima, Piko, Bu Ratna, Pak Surya."""
import math
import numpy as np
from render3d import *

SKIN = hexc('#F7C99B'); SKIN_D = hexc('#E9A97A')
DARK = hexc('#2B1B14'); BLUSH = hexc('#F29A8A')
GREEN = hexc('#16A34A'); GREEN_D = hexc('#15803D'); YEL = hexc('#F59E0B'); CREAM = hexc('#FEFCE8')
BROWN = hexc('#78350F'); BLUE = hexc('#0284C7'); STRAW = hexc('#F5B83A'); STRAW_D = hexc('#D99A1E')
ELEV = 30
CH_B = ((-2.4, 2.4), (0.0, 4.2), (-2.4, 2.4))


def limb(a, b, r1, r2, col, **kw):
    return RC(a, b, r1, r2, col, **kw)


def face(cy, z, eye_dx=0.27, eye_y=-0.03, blush=True, smile=True, scale=1.0, cheek_dx=0.47):
    """Wajah menghadap +z, pusat kepala (0,cy,0), radius z."""
    out = []
    for sx in (-1, 1):
        out.append(S((sx * eye_dx * scale, cy + eye_y, z * 0.93), .095 * scale, DARK, s=(.78, 1.25, .55), spec=.5, shin=40, bias=-.03))
        out.append(S((sx * (eye_dx - .035) * scale, cy + eye_y + .055, z * 0.93 + .055), .034 * scale, hexc('#FFFFFF'), spec=0, bias=-.05))
        if blush:
            out.append(S((sx * cheek_dx * scale, cy - .2, z * .76), .115 * scale, BLUSH, s=(1.1, .65, .45), spec=0, bias=-.02))
    out.append(S((0, cy - .12, z * 0.985), .07 * scale, SKIN_D, s=(1, .85, .9), spec=.1))
    if smile:
        out.append(CAP((-.11 * scale, cy - .3, z * .9), (.11 * scale, cy - .3, z * .9), .028 * scale, hexc('#8B2E1F'), bias=-.05))
        out.append(CAP((-.11 * scale, cy - .3, z * .9), (-.15 * scale, cy - .26, z * .88), .026 * scale, hexc('#8B2E1F'), bias=-.05))
        out.append(CAP((.11 * scale, cy - .3, z * .9), (.15 * scale, cy - .26, z * .88), .026 * scale, hexc('#8B2E1F'), bias=-.05))
    return out


# --------------------------------------------------------------------------- Bima
def bima(phase):
    """phase: 0..3 (frame jalan). 0 = diam/netral."""
    sw = [0.0, 1.0, 0.0, -1.0][phase]
    bob = [0.0, 0.05, 0.0, 0.05][phase]
    lift = lambda s: max(0.0, s) * 0.14
    P = []
    # kaki
    for sx, side in ((-1, 1), (1, -1)):
        s = sw * side
        hip = (sx * .3, .98 + bob, 0)
        zf = .36 * s
        foot = (sx * .3, .34 + lift(s) + bob * .3, zf)
        P.append(limb(hip, foot, .22, .2, BROWN, k=.05))
        P.append(B((sx * .3, .16 + lift(s) + bob * .3, zf + .09), (.23, .17, .31), YEL, rr=.11, spec=.35))
        P.append(B((sx * .3, .06 + lift(s) + bob * .3, zf + .09), (.235, .05, .315), hexc('#B45309'), rr=.04, spec=.05))
    # badan
    P.append(S((0, 1.5 + bob, 0), .66, GREEN, s=(1.0, .95, .78), spec=.3))  # rompi
    P.append(B((0, 1.55 + bob, .5), (.19, .52, .1), CREAM, rr=.08, bias=-.02))  # kaus krem di tengah rompi
    P.append(C((0, 1.05 + bob, 0), .57, .06, BROWN, rr=.025, k=.0, bias=-.02))  # sabuk
    P.append(B((0, 1.05 + bob, .55), (.12, .09, .05), STRAW, rr=.025, spec=.6, bias=-.03))  # gesper
    # lengan
    for sx, side in ((-1, 1), (1, -1)):
        s = -sw * side
        sh = (sx * .66, 1.86 + bob, 0)
        hand = (sx * (.78 + .05 * abs(s)), 1.1 + bob + .06 * abs(s), .34 * s)
        P.append(limb(sh, hand, .17, .15, CREAM, k=.06))
        P.append(S(hand, .17, SKIN, spec=.2))
    # kepala
    cy = 2.5 + bob
    P.append(S((0, cy, 0), .82, SKIN, spec=.25, shin=30))
    P.append(S((0, cy + .06, -.12), .85, hexc('#4A2A15'), s=(1.0, .95, .96), cut=(0, -1, 0, -.15 + 0.0)))  # rambut (sebelah belakang)
    for sx in (-1, 1):
        P.append(S((sx * .81, cy - .02, -.02), .14, SKIN, s=(.55, 1, .9)))
    P += face(cy, .82)
    # topi jerami
    P.append(C((0, cy + .62, 0), 1.18, .045, STRAW, rr=.04, rot=(-4, 0, 0), spec=.2, tex=_straw))
    P.append(T((0, cy + .64, 0), 1.17, .05, STRAW_D, rot=(-4, 0, 0)))
    P.append(S((0, cy + .64, 0), .68, STRAW, s=(1, .76, 1), cut=(0, -1, 0, -.06), spec=.25, tex=_straw))
    P.append(C((0, cy + .70, 0), .685, .07, hexc('#2F8F46'), rr=.02, bias=-.01))  # pita hijau
    # pin panel surya
    P.append(B((0, cy + .85, .64), (.19, .13, .035), hexc('#0284C7'), rr=.02, rot=(-20, 0, 0), spec=.7, shin=50, tex=_solar, bias=-.02))
    return P


def _straw(x, y, z, col):
    n = np.sin(np.sqrt(x * x + z * z) * 38.0) * 0.5 + 0.5
    return col * (0.88 + 0.14 * n)[:, None]


def _solar(x, y, z, col):
    g = (np.sin(x * 70) > 0.75) | (np.sin(y * 90 + z * 40) > 0.8)
    out = col.copy()
    out[g] = out[g] * 0.55 + 0.35
    return out


# --------------------------------------------------------------------------- Piko (menghadap kiri -x)
ORANGE = hexc('#F59E0B'); ORANGE_D = hexc('#D97706')


def _tabby(x, y, z, col):
    s = np.clip((np.sin(z * 7.0 + 1.0 * np.sin(x * 3)) - 0.55) * 4, 0, 1) * np.clip((y - .35) * 3, 0, 1)
    return col * (1 - 0.28 * s)[:, None]


def piko(k):
    """k: 0 duduk, 1 jalan1, 2 jalan2, 3 lompat."""
    P = []
    sc = hexc('#16A34A')
    tail_pts = None
    if k == 0:  # duduk tegak
        P.append(S((.28, .5, 0), .72, ORANGE, s=(1, .78, .8), tex=_tabby, spec=.2))  # pantat
        P.append(S((-.05, 1.0, 0), .64, ORANGE, s=(.82, 1.15, .78), tex=_tabby, k=.12))  # dada
        P.append(S((-.28, .95, 0), .4, CREAM, s=(.6, 1.1, .8), bias=-.03, spec=.1))
        for sz in (-.27, .27):
            P.append(CAP((-.3, 1.0, sz), (-.34, .13, sz * .95), .15, ORANGE, k=.05))
            P.append(S((-.38, .12, sz * .95), .17, CREAM, s=(1.2, .6, 1), spec=.1))
        hc = (-.2, 1.85, 0)
        tail_pts = [(.75, .15, .45), (.35, .12, .78), (-.15, .13, .85), (-.5, .16, .62), (-.58, .35, .45)]
        P.append(S((.35, .15, .0), .3, ORANGE, s=(1.3, .5, 1)))
    elif k == 3:  # melompat gembira
        yo = .45
        P.append(S((.1, .85 + yo, 0), .66, ORANGE, s=(1.35, .8, .85), rot=(0, 0, 14), tex=_tabby, spec=.2))
        P.append(S((-.55, 1.0 + yo, 0), .4, CREAM, s=(.7, .8, .8), bias=-.03))
        for sz in (-.3, .3):
            P.append(CAP((-.55, .95 + yo, sz), (-1.15, 1.25 + yo, sz * 1.15), .13, ORANGE, k=.04))
            P.append(S((-1.18, 1.27 + yo, sz * 1.15), .15, CREAM, s=(1, .8, 1)))
            P.append(CAP((.7, .8 + yo, sz), (1.2, .55 + yo, sz * 1.1), .15, ORANGE, k=.04))
            P.append(S((1.24, .53 + yo, sz * 1.1), .17, CREAM, s=(1.2, .7, 1)))
        hc = (-.85, 1.5 + yo, 0)
        tail_pts = [(.75, 1.0 + yo, 0), (1.05, 1.35 + yo, 0), (1.15, 1.75 + yo, 0), (1.0, 2.1 + yo, 0), (.8, 2.25 + yo, 0)]
    else:
        ph = 1 if k == 1 else -1
        P.append(S((.15, .78, 0), .68, ORANGE, s=(1.3, .85, .82), tex=_tabby, spec=.2))
        P.append(S((-.5, .85, 0), .42, CREAM, s=(.7, .85, .85), bias=-.03))
        for sx, sz, s_ in ((-.55, -.3, ph), (-.55, .3, -ph), (.75, -.3, -ph), (.75, .3, ph)):
            ft = (sx + s_ * .34, .13 + max(0, s_) * .0, sz)
            P.append(CAP((sx, .65, sz), (sx + s_ * .3, .22, sz), .14, ORANGE, k=.04))
            P.append(S((sx + s_ * .34, .13, sz), .17, CREAM, s=(1.25, .62, 1)))
        hc = (-.82, 1.33 + .03 * ph, 0)
        tail_pts = [(.78, .85, 0), (1.12, 1.1, .1 * ph), (1.2, 1.5, .18 * ph), (1.0, 1.8, .1 * ph), (.8, 1.9, 0)]
    # kepala
    hx, hy, hz = hc
    P.append(S(hc, .6, ORANGE, s=(.95, .92, 1.08), tex=_tabby, spec=.25, k=.1))
    P.append(S((hx - .27, hy - .18, 0), .3, CREAM, s=(.9, .75, 1.0), bias=-.03, spec=.1))
    for sz in (-1, 1):
        P.append(RC((hx + .02, hy + .38, sz * .3), (hx - .05, hy + .88, sz * .42), .2, .05, ORANGE, spec=.15))
        P.append(RC((hx - .03, hy + .4, sz * .3), (hx - .09, hy + .78, sz * .4), .12, .03, hexc('#F9A8A8'), bias=-.02, spec=.05))
        P.append(S((hx - .55, hy + .08, sz * .27), .105, DARK, s=(.55, 1.2, .85), spec=.6, shin=40, bias=-.03))
        P.append(S((hx - .6, hy + .13, sz * .25), .03, hexc('#FFFFFF'), bias=-.05, spec=0))
        P.append(S((hx - .5, hy - .08, sz * .45), .09, BLUSH, s=(.5, .7, 1), bias=-.02, spec=0))
        for wy in (-.0, -.1):
            P.append(CAP((hx - .55, hy - .12 + wy, sz * .2), (hx - .85, hy - .06 + wy * 2, sz * .75), .012, hexc('#FEF3C7'), bias=-.03, spec=0))
    P.append(S((hx - .62, hy - .1, 0), .075, hexc('#F472B6'), s=(.7, .7, 1), bias=-.03))
    P.append(CAP((hx - .6, hy - .16, 0), (hx - .56, hy - .25, 0), .02, DARK, bias=-.05))
    # syal daun hijau
    P.append(T((hx + .32, hy - .55, 0), .38, .12, sc, rot=(0, 0, 70 if k != 3 else 55), spec=.3, k=.05))
    P.append(B((hx + .4, hy - .85, .26), (.07, .22, .05), hexc('#22C55E'), rr=.03, rot=(0, 0, 12 + (8 if k == 3 else 0))))
    # ekor
    for i in range(len(tail_pts) - 1):
        r = .15 - .02 * i
        P.append(CAP(tail_pts[i], tail_pts[i + 1], r, ORANGE_D if i % 2 else ORANGE, k=.05, spec=.15))
    P.append(S(tail_pts[-1], .13, hexc('#FEF3C7'), spec=.1))
    return P


# --------------------------------------------------------------------------- Bu Ratna
KEBAYA = hexc('#16A34A'); APRON = hexc('#FBBF24'); SARONG = hexc('#7C2D12'); HAIR = hexc('#1F1410')


def ratna(f):
    P = []
    bob = 0.0
    # sarong
    P.append(RC((0, 1.2, 0), (0, .12, 0), .56, .78, SARONG, k=.05, spec=.12, tex=_batik))
    P.append(CAP((-.3, .15, .5), (.3, .15, .5), .1, hexc('#8B5E3C'), bias=-.02))
    for sx in (-1, 1):
        P.append(B((sx * .3, .07, .52), (.2, .08, .26), hexc('#5B3A29'), rr=.07))
    P.append(S((0, 1.55, 0), .66, KEBAYA, s=(.95, .95, .78), spec=.3))
    P.append(B((0, 1.2, .46), (.34, .56, .1), APRON, rr=.1, bias=-.02, spec=.3))
    # bunga matahari di celemek
    for i in range(10):
        a = i * math.tau / 10
        P.append(S((math.cos(a) * .17, 1.34 + math.sin(a) * .17, .58), .075, hexc('#FDE047'), s=(1, 1, .45), bias=-.03, spec=.05))
    P.append(S((0, 1.34, .6), .1, hexc('#7C2D12'), s=(1, 1, .5), bias=-.04))
    P.append(B((0, 1.75, .5), (.2, .12, .08), hexc('#FDE68A'), rr=.05, bias=-.02))  # kerah emas
    # lengan
    keranjang = True
    for sx in (-1, 1):
        sh = (sx * .68, 1.9, 0)
        if f == 1 and sx == 1:  # melambai
            hand = (.98, 2.75 + .0, .1)
            P.append(limb(sh, (.95, 2.3, .06), .17, .15, KEBAYA, k=.05))
            P.append(limb((.95, 2.3, .06), hand, .15, .14, KEBAYA, k=.05))
            P.append(S(hand, .18, SKIN))
            continue
        hand = (sx * .5, 1.25, .5)
        P.append(limb(sh, hand, .17, .15, KEBAYA, k=.05))
        P.append(S(hand, .17, SKIN))
    # keranjang benih (frame 0 kedua tangan; frame 1 hanya tangan kiri)
    bx = -.15 if f == 1 else 0
    P.append(C((bx - (.15 if f == 1 else 0), 1.05, .62), .5, .17, hexc('#B7791F'), rr=.06, spec=.1, tex=_weave))
    P.append(C((bx - (.15 if f == 1 else 0), 1.2, .62), .44, .03, hexc('#5B3A12'), rr=.01))
    for i, (dx, dz) in enumerate([(-.2, .0), (.1, .12), (.2, -.08), (-.05, -.15), (0, 0), (.25, .1)]):
        P.append(S((bx - (.15 if f == 1 else 0) + dx, 1.27 + (i % 2) * .03, .62 + dz), .1, [hexc('#FDE047'), hexc('#7C2D12'), hexc('#EF4444')][i % 3], spec=.3))
    # kepala
    cy = 2.62
    P.append(S((0, cy, 0), .8, SKIN, spec=.25))
    P.append(S((0, cy + .08, -.15), .84, HAIR, s=(1.0, .98, .98), cut=(0, -1, 0, -.05 + 0.1), spec=.4, shin=40))
    P.append(S((0, cy + .62, -.1), .5, HAIR, s=(1, .85, 1), spec=.4, shin=40))  # sanggul
    P.append(S((0, cy + .45, .0), .62, HAIR, s=(1.1, .5, 1.0), spec=.4, shin=40, cut=(0, -1, 0, -.05)))
    P.append(S((.38, cy + .75, .05), .1, hexc('#F472B6'), spec=.3))  # bunga di rambut
    P.append(S((.45, cy + .75, .12), .06, hexc('#FDE047'), spec=.3))
    P += face(cy, .8, scale=.98)
    for sx in (-1, 1):
        P.append(S((sx * .8, cy - .05, -.02), .13, SKIN, s=(.55, 1, .9)))
        P.append(S((sx * .86, cy - .22, 0), .06, hexc('#FDE047'), spec=.8, shin=60))
    return P


def _batik(x, y, z, col):
    a = np.sin(x * 14) * np.sin(y * 14 + z * 0)
    m = np.clip(a * 3, 0, 1) * .5
    return col * (1 - .35 * m)[:, None] + hexc('#FBBF24') * (.18 * m)[:, None]


def _weave(x, y, z, col):
    a = (np.sin(x * 40) * np.sin((y + z) * 40) > 0).astype(F)
    return col * (0.8 + .25 * a)[:, None]


# --------------------------------------------------------------------------- Pak Surya
HELM = hexc('#F8FAFC'); SHIRT = hexc('#0284C7'); VEST = hexc('#78350F'); PANTS = hexc('#475569')


def surya(f):
    P = []
    for sx in (-1, 1):
        P.append(limb((sx * .3, 1.0, 0), (sx * .3, .3, 0), .22, .2, PANTS, k=.05))
        P.append(B((sx * .3, .16, .1), (.24, .17, .32), hexc('#3F3F46'), rr=.11, spec=.3))
    P.append(S((0, 1.52, 0), .68, SHIRT, s=(1.0, .95, .8), spec=.25))
    P.append(B((0, 1.5, .5), (.46, .5, .1), VEST, rr=.1, spec=.15, bias=-.01))
    P.append(B((0, 1.55, .58), (.08, .45, .05), SHIRT, rr=.03, bias=-.02))
    P.append(C((0, 1.04, 0), .6, .07, hexc('#3F3F46'), rr=.03, bias=-.02))
    P.append(B((.36, 1.0, .5), (.14, .12, .07), hexc('#A16207'), rr=.04, bias=-.02))
    # lengan
    for sx in (-1, 1):
        sh = (sx * .7, 1.88, 0)
        if f == 1 and sx == 1:  # acung jempol
            el = (.98, 1.6, .32); hand = (.92, 2.0, .65)
            P.append(limb(sh, el, .18, .16, SHIRT, k=.05))
            P.append(limb(el, hand, .16, .15, SHIRT, k=.05))
            P.append(S(hand, .2, SKIN))
            P.append(CAP((hand[0], hand[1] + .1, hand[2]), (hand[0], hand[1] + .38, hand[2] + .02), .08, SKIN, k=.04))
            continue
        if sx == 1:  # papan klip
            hand = (.62, 1.18, .55)
        else:
            hand = (-.52, 1.15, .42)
        P.append(limb(sh, hand, .18, .16, SHIRT, k=.05))
        P.append(S(hand, .17, SKIN))
    if f == 0:
        P.append(B((.5, 1.35, .72), (.36, .45, .035), hexc('#92400E'), rr=.03, rot=(-15, 12, 0)))
        P.append(B((.5, 1.37, .75), (.3, .39, .02), hexc('#F8FAFC'), rr=.015, rot=(-15, 12, 0), bias=-.01, tex=_paper))
        P.append(B((.5, 1.78, .73), (.12, .05, .04), hexc('#9CA3AF'), rr=.02, rot=(-15, 12, 0), spec=.6))
    else:
        P.append(B((-.55, 1.22, .55), (.28, .38, .03), hexc('#92400E'), rr=.03, rot=(-15, -12, 0)))
        P.append(B((-.55, 1.24, .58), (.23, .32, .02), hexc('#F8FAFC'), rr=.015, rot=(-15, -12, 0), bias=-.01, tex=_paper))
    cy = 2.55
    P.append(S((0, cy, 0), .8, SKIN, spec=.25))
    for sx in (-1, 1):
        P.append(S((sx * .79, cy - .03, 0), .14, SKIN, s=(.55, 1, .9)))
    P += face(cy, .8, blush=False)
    # kumis
    P.append(CAP((-.2, cy - .2, .76), (-.02, cy - .17, .8), .045, hexc('#2B1B14'), bias=-.04, spec=.1))
    P.append(CAP((.2, cy - .2, .76), (.02, cy - .17, .8), .045, hexc('#2B1B14'), bias=-.04, spec=.1))
    # helm
    P.append(S((0, cy + .3, 0), .9, HELM, s=(1, .85, 1), cut=(0, -1, 0, -.18), spec=.7, shin=50))
    P.append(B((0, cy + .75, 0), (.07, .1, .9), hexc('#E2E8F0'), rr=.05, spec=.6))
    P.append(C((0, cy + .1, 0), .93, .06, hexc('#E2E8F0'), rr=.03, spec=.5))
    P.append(B((0, cy + .1, .98), (.5, .05, .22), HELM, rr=.04, rot=(-8, 0, 0), spec=.6))  # lidah helm
    # ikon petir hijau
    P.append(B((-.03, cy + .5, .87), (.085, .2, .03), GREEN, rr=.02, rot=(-30, 0, 18), emit=.1, spec=.5, bias=-.02))
    P.append(B((.05, cy + .4, .9), (.085, .16, .03), GREEN, rr=.02, rot=(-30, 0, -22), emit=.1, spec=.5, bias=-.02))
    return P


def _paper(x, y, z, col):
    l = (np.sin(y * 55) > .55)
    out = col.copy()
    out[l] = out[l] * .72 + F([0.1, .3, .5]) * .25
    return out
