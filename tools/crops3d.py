"""Model 3D tanaman (4 jenis x 4 fase) dan ikon teknologi hijau."""
import math
import numpy as np
from render3d import *

SOIL = hexc('#7A4421'); SOIL_D = hexc('#5E3217'); LEAF = hexc('#22A94B'); LEAF_L = hexc('#4ADE80'); LEAF_D = hexc('#15803D')
ELEV = 30


def mound(r=1.25, wet=False):
    c = hexc('#5A3317') if wet else SOIL
    P = [S((0, 0, 0), r, c, s=(1, .34, 1), spec=.3 if wet else .08, shin=30)]
    rng = np.random.RandomState(4)
    for i in range(7):
        a = rng.uniform(0, math.tau); rr = rng.uniform(.35, r * .85)
        P.append(S((math.cos(a) * rr, .07 + (1 - rr / r) * .3, math.sin(a) * rr), rng.uniform(.07, .14), SOIL_D if i % 2 else hexc('#A0622F'), s=(1, .7, 1), spec=.05))
    return P


def leaf(base, yaw, tilt, L, w, col=LEAF, droop=0.0):
    """Daun lonjong: pangkal di base, arah yaw (derajat), naik tilt derajat."""
    R = yawtilt(yaw, tilt)
    d = R @ np.array([1.0, 0, 0])
    c = (base[0] + d[0] * L * .5, base[1] + d[1] * L * .5, base[2] + d[2] * L * .5)
    return S(c, L * .5, col, s=(1, .2, w / L * 1.35), rot=R, spec=.3, shin=30)


def blade(base, yaw, L, lean, r, col, segs=3):
    """Helai daun melengkung (rantai round-cone)."""
    out = []
    dx, dz = math.cos(math.radians(yaw)), -math.sin(math.radians(yaw))
    pts = []
    for i in range(segs + 1):
        t = i / segs
        h = L * (t - .25 * t * t * lean)
        o = L * lean * t * t
        pts.append((base[0] + dx * o, base[1] + h, base[2] + dz * o))
    for i in range(segs):
        out.append(RC(pts[i], pts[i + 1], r * 1.5 * (1 - i / segs * .75), r * 1.5 * (1 - (i + 1) / segs * .75), col, spec=.25, k=.02))
    return out


def stem(a, b, r1, r2, col=LEAF_D):
    return RC(a, b, r1, r2, col, spec=.2, k=.04)


# ------------------------------------------------------------------ TOMAT
def tomat(st):
    P = mound()
    top = (0, .3, 0)
    if st == 0:
        P += [leaf((0, .32, 0), 20, 25, .5, .3, LEAF_L), leaf((0, .32, 0), 200, 25, .5, .3, LEAF_L)]
        P.append(S((.5, .22, .35), .09, hexc('#F5DEB3'), s=(1.3, .7, 1)))
        return P
    if st == 1:
        P.append(stem(top, (0, 1.3, 0), .1, .07))
        for i, h in enumerate((.6, .85, 1.1, 1.3)):
            P.append(leaf((0, h, 0), i * 100 + 20, 28, .62, .34, LEAF if i % 2 else LEAF_L))
            P.append(leaf((0, h, 0), i * 100 + 200, 28, .62, .34, LEAF if i % 2 == 0 else LEAF_L))
        return P
    P.append(CAP((.45, .15, .0), (.45, 2.7, .0), .055, hexc('#B7791F'), spec=.1))  # ajir
    P.append(stem(top, (0, 2.1, 0), .13, .08))
    for i, h in enumerate((.7, 1.0, 1.3, 1.6, 1.9)):
        P.append(leaf((0, h, 0), i * 77 + 10, 25, .85 - .05 * i, .45, LEAF if i % 2 else LEAF_L))
        P.append(leaf((0, h, 0), i * 77 + 190, 25, .85 - .05 * i, .45, LEAF_L if i % 2 else LEAF))
    if st == 2:
        for (x, y, z) in ((.35, 1.4, .3), (-.4, 1.15, .25), (.15, 1.7, -.35)):
            P.append(S((x, y, z), .22, hexc('#86B83A'), spec=.5, shin=40))
        for (x, y, z) in ((.2, 1.95, .3), (-.3, 1.75, -.2)):
            P.append(S((x, y, z), .09, hexc('#FDE047'), spec=.3))
    else:
        for (x, y, z) in ((.38, 1.25, .38), (-.42, 1.0, .32), (.12, 1.55, -.42), (-.3, 1.55, .15), (.55, .85, -.1)):
            P.append(S((x, y, z), .36, hexc('#EF3B2D'), s=(1, .92, 1), spec=.7, shin=45))
            P.append(S((x, y + .33, z), .15, LEAF_D, s=(1.3, .35, 1.3), spec=.1, bias=-.01))
    return P


# ------------------------------------------------------------------ JAGUNG
def jagung(st):
    P = mound()
    if st == 0:
        P += blade((0, .3, 0), 30, .75, .6, .06, LEAF_L, 2)
        return P
    if st == 1:
        for i in range(4):
            P += blade((0, .3, 0), i * 90 + 10, 1.35, .85, .095, LEAF_L if i % 2 else LEAF, 3)
        return P
    H = 2.4 if st == 2 else 3.0
    P.append(stem((0, .3, 0), (0, H, 0), .17, .1, hexc('#6BBF59')))
    n = 6 if st == 2 else 8
    for i in range(n):
        h = .7 + (H - 1.1) * i / (n - 1)
        P += blade((0, h, 0), i * 137 + 20, 1.3 - .03 * i, 1.0, .1, LEAF if i % 2 else LEAF_L, 3)
    if st == 2:
        P.append(S((0, H + .08, 0), .1, hexc('#D9F99D'), s=(1, 1.6, 1)))
    else:
        for sx, hy in ((1, 1.6), (-1, 1.95)):
            P.append(S((sx * .26, hy, .1), .21, hexc('#FACC15'), s=(.9, 1.9, .9), rot=(0, 0, -sx * 14), spec=.5, shin=36, tex=_kernel))
            for k in range(3):
                a = k * 2.1 + (0 if sx > 0 else 1)
                P.append(leaf((sx * .25, hy - .3, .1), a * 57, 70, .85, .3, hexc('#4D9F3A')))
        for i in range(6):
            P.append(CAP((0, H, 0), (math.cos(i * 1.05) * .42, H + .5 - .08 * (i % 2), math.sin(i * 1.05) * .42), .035, hexc('#EAB308'), spec=.15))
    return P


def _kernel(x, y, z, col):
    g = (np.sin(y * 42) * np.sin((x + z) * 40 + y * 10) > .1)
    out = col.copy(); out[g] = out[g] * .84
    return out


# ------------------------------------------------------------------ KENTANG
def kentang(st):
    P = mound()
    if st == 0:
        P += [leaf((0, .3, 0), 0, 35, .4, .25, LEAF_L), leaf((0, .3, 0), 160, 35, .4, .25, LEAF)]
        return P
    n = [0, 4, 9, 9][st]
    base_h = .35
    for i in range(n):
        a = i * 137.5; rad = .22 + .12 * (i % 3)
        h = base_h + (.35 + .12 * (i % 4)) * (1 if st == 1 else 1.7)
        P.append(stem((0, .3, 0), (math.cos(math.radians(a)) * rad, h, -math.sin(math.radians(a)) * rad), .05, .04))
        col = LEAF if st < 3 else hexc('#A3A33A')
        P.append(leaf((math.cos(math.radians(a)) * rad, h, -math.sin(math.radians(a)) * rad), a, 20 if st < 3 else -10, .6 if st > 1 else .45, .34, col if i % 2 else (LEAF_L if st < 3 else hexc('#C9B83A'))))
        P.append(leaf((math.cos(math.radians(a)) * rad, h, -math.sin(math.radians(a)) * rad), a + 40, 30 if st < 3 else 0, .5, .3, col))
    if st == 2:
        for (x, y, z) in ((.2, 1.35, .25), (-.3, 1.1, -.1), (.1, 1.2, -.35)):
            for k in range(5):
                a = k * 1.256
                P.append(S((x + math.cos(a) * .09, y + .02, z + math.sin(a) * .09), .06, hexc('#F5F3FF'), s=(1, .5, 1), spec=.1))
            P.append(S((x, y + .04, z), .045, hexc('#FDE047'), spec=.1))
    if st == 3:
        for (x, z, a) in ((.55, .5, 20), (-.6, .35, -30), (.1, .8, 70), (-.35, -.5, 10)):
            P.append(S((x, .2, z), .31, hexc('#D6A25A'), s=(1.3, .85, 1), rot=(0, a, 0), spec=.3, shin=30))
            P.append(S((x + .1, .3, z + .22), .03, hexc('#7B4A1E'), bias=-.01))
            P.append(S((x - .12, .27, z + .24), .03, hexc('#7B4A1E'), bias=-.01))
    return P


# ------------------------------------------------------------------ PADI
def padi(st):
    P = []
    P.append(S((0, 0, 0), 1.3, hexc('#8A5A33'), s=(1, .25, 1), spec=.1))
    P.append(S((0, .06, 0), 1.2, hexc('#6BC4F0'), s=(1, .06, 1), spec=.9, shin=60))  # genangan sawah
    if st == 0:
        for a in (30, 200, 110):
            P += blade((math.cos(math.radians(a)) * .25, .05, math.sin(math.radians(a)) * .25), a, .6, .4, .045, LEAF_L, 2)
        return P
    n, L = {1: (7, 1.1), 2: (12, 1.7), 3: (10, 1.8)}[st]
    for i in range(n):
        a = i * 137.5
        rad = .12 + .2 * ((i * 37) % 10) / 10
        bx, bz = math.cos(math.radians(a)) * rad, -math.sin(math.radians(a)) * rad
        col = LEAF_L if (st < 3 and i % 2) else (LEAF if st < 3 else (hexc('#A3C23A') if i % 2 else hexc('#C8B53A')))
        lean = .55 + .15 * (i % 3) + (.05 if st == 3 else 0)
        P += blade((bx, .1, bz), a, L * (.85 + .15 * ((i * 7) % 5) / 5), lean, .07, col, 3)
        if st == 3 and i % 2 == 0:  # malai padi merunduk
            dxn, dzn = math.cos(math.radians(a)), -math.sin(math.radians(a))
            Lh = L * (.85 + .15 * ((i * 7) % 5) / 5)
            tip = (bx + dxn * Lh * lean * .85, .1 + Lh * (.85 - .25 * .72), bz + dzn * Lh * lean * .85)
            for g in range(7):
                t = g / 6
                P.append(S((tip[0] + dxn * .36 * t, tip[1] - .5 * t * t - .02, tip[2] + dzn * .36 * t), .1, hexc('#FBBF24'), s=(1.5, 1, 1), rot=(0, a, -50 * t), spec=.35, shin=30))
    return P


CROPS = [tomat, jagung, kentang, padi]


# ------------------------------------------------------------------ IKON TEKNOLOGI HIJAU
def _grid(x, y, z, col):
    g = (np.sin(x * 34) > .82) | (np.sin((y + z) * 30) > .82)
    out = col.copy(); out[g] = out[g] * .5 + .45
    return out


def solar_pump():
    P = []
    P.append(B((0, .08, 0), (1.5, .08, 1.2), hexc('#9CA3AF'), rr=.05, spec=.1))
    # panel surya di belakang
    for sx in (-1, 1):
        P.append(CAP((sx * .8, .15, -.55), (sx * .8, 1.7, -.75), .07, hexc('#6B7280'), spec=.4))
    P.append(B((0, 1.95, -.7), (1.15, .06, .75), hexc('#1D4ED8'), rr=.04, rot=(-52, 0, 0), spec=.8, shin=60, tex=_grid))
    P.append(B((0, 1.95, -.7), (1.2, .04, .8), hexc('#E5E7EB'), rr=.03, rot=(-52, 0, 0), spec=.6, bias=.02))
    # unit pompa
    P.append(C((.55, .55, .45), .42, .42, hexc('#0EA5E9'), rr=.09, spec=.5))
    P.append(C((.55, 1.05, .45), .3, .1, hexc('#075985'), rr=.04, spec=.5))
    P.append(B((.55, .5, .88), (.18, .14, .03), hexc('#FDE047'), rr=.02, emit=.12, bias=-.02))
    # pipa
    P.append(CAP((.55, 1.1, .45), (.55, 1.55, .45), .1, hexc('#9CA3AF'), spec=.6))
    P.append(CAP((.55, 1.55, .45), (-.5, 1.55, .5), .1, hexc('#9CA3AF'), spec=.6))
    P.append(CAP((-.5, 1.55, .5), (-.5, .55, .55), .1, hexc('#9CA3AF'), spec=.6))
    P.append(S((-.5, .5, .56), .13, hexc('#9CA3AF'), spec=.6))
    # tetesan air & genangan
    P.append(S((-.5, .28, .6), .1, hexc('#38BDF8'), s=(.8, 1.3, .8), spec=.9, shin=60, emit=.15))
    P.append(S((-.5, .02, .62), .62, hexc('#38BDF8'), s=(1, .06, 1), spec=.9, shin=60))
    # kabel
    P.append(CAP((.2, 1.5, -.5), (.4, .9, .1), .035, hexc('#FACC15'), spec=.3))
    return P


def biogas():
    P = []
    P.append(C((0, .45, 0), 1.0, .45, hexc('#A8A29E'), rr=.08, spec=.1, tex=_bricks))
    P.append(S((0, .88, 0), 1.0, hexc('#22A94B'), cut=(0, -1, 0, 0), spec=.55, shin=40))
    P.append(T((0, .92, 0), .98, .06, hexc('#6B7280'), spec=.6))
    P.append(T((0, 1.5, 0), .74, .045, hexc('#6B7280'), spec=.6))
    P.append(C((0, 1.97, 0), .17, .12, hexc('#6B7280'), rr=.04, spec=.7))
    # pipa gas & manometer
    P.append(CAP((0, 2.05, 0), (0, 2.5, 0), .075, hexc('#9CA3AF'), spec=.6))
    P.append(CAP((0, 2.5, 0), (1.05, 2.5, 0), .075, hexc('#9CA3AF'), spec=.6))
    P.append(CAP((1.05, 2.5, 0), (1.05, 1.0, .45), .075, hexc('#9CA3AF'), spec=.6))
    P.append(C((0, 2.35, .0), .22, .06, hexc('#F8FAFC'), rr=.02, rot=(90, 0, 0), spec=.6))
    P.append(CAP((0, 2.35, .08), (.1, 2.43, .08), .02, hexc('#DC2626'), bias=-.02))
    # kompor + api biru
    P.append(B((1.05, .55, .5), (.34, .5, .3), hexc('#64748B'), rr=.06, spec=.3))
    P.append(S((1.05, 1.15, .5), .17, hexc('#60A5FA'), s=(1, 1.5, 1), emit=.9, spec=0))
    P.append(S((1.05, 1.1, .5), .1, hexc('#F8FAFC'), s=(1, 1.4, 1), emit=.9, spec=0))
    # inlet kotoran
    P.append(C((-1.0, .7, .1), .26, .45, hexc('#92400E'), rr=.05, rot=(0, 0, 38), spec=.15))
    return P


def _bricks(x, y, z, col):
    l = (np.sin(y * 22) > .78) | (np.sin((x + z) * 14 + np.floor(y * 3.5) * 1.5) > .88)
    out = col.copy(); out[l] = out[l] * .78
    return out


def hydro():
    P = []
    # dasar & rangka kayu
    P.append(B((0, .06, .0), (1.6, .06, .9), hexc('#92400E'), rr=.03, spec=.1))
    for sx in (-1, 1):
        P.append(B((sx * 1.0, 1.0, -.3), (.1, 1.0, .1), hexc('#B7791F'), rr=.03, spec=.1))
        P.append(CAP((sx * 1.0, 1.9, -.3), (sx * 1.0, 1.15, .1), .0001, hexc('#B7791F')))
    P.append(B((0, 1.95, -.3), (1.1, .08, .1), hexc('#B7791F'), rr=.03))
    # roda air (sumbu z)
    wc = (0, 1.15, .1)
    P.append(T(wc, .98, .09, hexc('#B7791F'), rot=(90, 0, 0), spec=.2))
    P.append(T((0, 1.15, .24), .92, .06, hexc('#92400E'), rot=(90, 0, 0)))
    P.append(T((0, 1.15, -.04), .92, .06, hexc('#92400E'), rot=(90, 0, 0)))
    for i in range(8):
        a = math.radians(i * 45 + 12)
        P.append(CAP((wc[0], wc[1], wc[2] + .1), (math.cos(a) * .95, wc[1] + math.sin(a) * .95, wc[2] + .1), .05, hexc('#B7791F')))
        px, py = math.cos(a) * .98, wc[1] + math.sin(a) * .98
        P.append(B((px, py, wc[2] + .1), (.2, .075, .26), hexc('#D97706'), rr=.03, rot=(0, 0, math.degrees(a) + 90), spec=.15))
    P.append(C((wc[0], wc[1], wc[2] + .1), .17, .3, hexc('#FACC15'), rr=.05, rot=(90, 0, 0), spec=.6))
    # aliran air
    P.append(B((0, .13, .5), (1.5, .09, .6), hexc('#0EA5E9'), rr=.07, spec=.9, shin=70, emit=.12))
    P.append(B((-1.15, 1.95, .1), (.6, .09, .22), hexc('#B7791F'), rr=.03, rot=(0, 0, -12)))
    P.append(B((-.55, 1.65, .1), (.3, .55, .17), hexc('#38BDF8'), rr=.1, rot=(0, 0, -8), spec=.9, shin=60, emit=.18))
    # generator
    P.append(B((1.45, .5, -.15), (.4, .45, .4), hexc('#E2E8F0'), rr=.07, spec=.5))
    P.append(B((1.45, .55, .26), (.18, .26, .03), hexc('#16A34A'), rr=.02, rot=(0, 0, 18), emit=.15, bias=-.02))
    P.append(CAP((1.1, .35, .0), (.3, .2, .1), .04, hexc('#FACC15')))
    return P
