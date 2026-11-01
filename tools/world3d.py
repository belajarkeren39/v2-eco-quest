"""Tileset desa 3D: ubin tanah/rumput/jalan/air + bangunan & dekorasi (SDF)."""
import math
import numpy as np
import cv2
from scipy import ndimage as ndi
from render3d import *

ELEV = 30
N = 256


def _vor(x, z, pts):
    d = np.full(x.shape, 9.0, F); d2 = np.full(x.shape, 9.0, F)
    for (px, pz) in pts:
        dd = np.sqrt((x - px) ** 2 + (z - pz) ** 2)
        d2 = np.minimum(d2, np.maximum(d, dd)); d = np.minimum(d, dd)
    return d2 - d


# ------------------------------------------------------------------ petak tanah (kamera hampir tegak lurus)
def soil(kind):
    rng = np.random.RandomState(11 + kind)
    base = {0: '#D9A66E', 1: '#A8602B', 2: '#5B3418'}[kind]
    P = []
    pts = [(rng.uniform(-1, 1), rng.uniform(-1, 1)) for _ in range(16)]

    def tex(x, y, z, col):
        out = col.copy()
        side = y < 0.2
        out[side] = out[side] * 0.62
        top = ~side
        if kind == 0 and top.any():
            e = _vor(x[top], z[top], pts)
            cr = np.clip(1 - e / 0.07, 0, 1)
            out[top] = out[top] * (1 - 0.55 * cr)[:, None]
        n = np.sin(x * 37 + z * 21) * np.sin(z * 33 - x * 17)
        out[top] = out[top] * (1 + 0.05 * n[top])[:, None]
        return out
    P.append(B((0, .14, 0), (.98, .14, .98), base, rr=.2, spec=.08 if kind < 2 else .45, shin=30, tex=tex))
    if kind == 0:
        for i in range(10):
            P.append(S((rng.uniform(-.8, .8), .3, rng.uniform(-.8, .8)), rng.uniform(.04, .08), hexc('#B98550') if i % 2 else hexc('#EBC088'), s=(1, .7, 1), spec=.05))
    else:
        col = hexc('#B0662B') if kind == 1 else hexc('#3F2410')
        for i, z in enumerate((-.66, -.33, 0, .33, .66)):
            P.append(CAP((-.78, .33, z), (.78, .33, z), .125, col, spec=.08 if kind == 1 else .5, shin=30, k=.04))
            P.append(B((0, .27, z + .165), (.8, .03, .03), hexc('#2C1708'), rr=.01, bias=-.01, spec=0))
        for i in range(8 if kind == 1 else 5):
            P.append(S((rng.uniform(-.7, .7), .43, rng.choice([-.66, -.33, 0, .33, .66])), rng.uniform(.04, .075), hexc('#D88B3E') if kind == 1 else hexc('#6B4021'), s=(1, .7, 1), spec=.1))
        if kind == 2:
            for (x, z) in ((-.5, -.33), (.35, .33), (.1, 0), (-.2, .66), (.55, -.66)):
                P.append(S((x, .43, z), .08, hexc('#7DD3FC'), s=(1.4, .55, 1.2), spec=1.0, shin=80, emit=.2, bias=-.02))
    return P


def render_soil(kind):
    return render(soil(kind), 256, 256, 120, 128, 142, elev=70, ss=2, bounds=((-1.2, 1.2), (0, .8), (-1.2, 1.2)),
                  outline=2.2, shadow_strength=.0, contact=.0, ground_shadow=False)


# ------------------------------------------------------------------ ubin berulang (heightfield 3D)
def _wrapblur(a, s):
    return ndi.gaussian_filter(a, s, mode='wrap')


def _shade(H, col, sun=(-0.55, -0.6), k=1.0, ao_s=7, ao_k=1.2, spec=0.0):
    gy, gx = np.gradient(H)
    gx = np.roll(gx, 0, 0); 
    nx, ny, nz = -gx * k, -gy * k, np.ones_like(H)
    nl = np.sqrt(nx * nx + ny * ny + nz * nz); nx, ny, nz = nx / nl, ny / nl, nz / nl
    L = np.array([sun[0], sun[1], 0.62]); L = L / np.linalg.norm(L)
    d = np.clip(nx * L[0] + ny * L[1] + nz * L[2], 0, 1)
    ao = np.clip(1.0 + ao_k * (H - _wrapblur(H, ao_s)) * 3, 0.55, 1.15)
    li = (0.52 + 0.62 * d) * ao
    out = col * li[..., None]
    if spec > 0:
        hh = L + np.array([0, 0, 1.0]); hh /= np.linalg.norm(hh)
        s = np.clip(nx * hh[0] + ny * hh[1] + nz * hh[2], 0, 1) ** 40 * spec
        out = out + s[..., None]
    return np.clip(out, 0, 1)


def _stamp(H, C, cx, cy, R, h, col, prof):
    Nn = H.shape[0]
    xs = np.arange(int(cx) - R, int(cx) + R + 1); ys = np.arange(int(cy) - R, int(cy) + R + 1)
    X, Y = np.meshgrid(xs - cx, ys - cy)
    r = np.sqrt(X * X + Y * Y) / R
    m = r < 1
    prof_v = prof(np.clip(r, 0, 1)) * h * m
    ix = xs % Nn; iy = ys % Nn
    sub = H[np.ix_(iy, ix)]
    upd = prof_v > sub
    H[np.ix_(iy, ix)] = np.where(upd, prof_v, sub)
    cs = C[np.ix_(iy, ix)]
    C[np.ix_(iy, ix)] = np.where(upd[..., None], col * (0.82 + 0.3 * np.clip(prof_v / max(h, 1e-6), 0, 1))[..., None] if np.ndim(col) == 1 else col, cs)


def tile_grass():
    n = N * 2; rng = np.random.RandomState(5)
    H = np.zeros((n, n), np.float32); C = np.ones((n, n, 3), np.float32) * hexc('#2E9E4A')
    for _ in range(170):
        R = rng.randint(30, 52); h = rng.uniform(.35, .8)
        g = rng.uniform(0, 1)
        col = hexc('#3AA853') * (1 - g) + hexc('#74E07C') * g
        _stamp(H, C, rng.randint(0, n), rng.randint(0, n), R, h, col, lambda r: (1 - r) ** .9)
    # kelopak bunga kecil
    for i in range(18):
        col = [hexc('#FFFFFF'), hexc('#FDE047'), hexc('#F9A8D4'), hexc('#FCA5A5')][i % 4]
        cx, cy = rng.randint(0, n), rng.randint(0, n)
        _stamp(H, C, cx, cy, 6, 1.25, col, lambda r: np.sqrt(np.clip(1 - r * r, 0, 1)))
    img = _shade(H, C, k=6, ao_s=14, ao_k=.5)
    # helai rumput
    canvas = (img * 255).astype(np.uint8).copy()
    ov = np.zeros((n, n, 4), np.uint8)
    for _ in range(1100):
        x, y = rng.randint(0, n), rng.randint(0, n); l = rng.randint(7, 15); a = math.radians(rng.uniform(-100, -80) + rng.uniform(-18, 18))
        light = rng.rand() > .45
        col = (150, 235, 120, 200) if light else (20, 90, 50, 170)
        for ox in (-n, 0, n):
            for oy in (-n, 0, n):
                cv2.line(ov, (x + ox, y + oy), (int(x + ox + math.cos(a) * l), int(y + oy + math.sin(a) * l)), col, 2, cv2.LINE_AA)
    a = ov[..., 3:4].astype(np.float32) / 255
    out = canvas * (1 - a * .5) + ov[..., :3] * a * .5
    out = cv2.resize(out.astype(np.uint8), (N, N), interpolation=cv2.INTER_AREA)
    return np.dstack([out, np.full((N, N), 255, np.uint8)])


def tile_path():
    n = N * 2; rng = np.random.RandomState(8)
    H = np.zeros((n, n), np.float32); C = np.ones((n, n, 3), np.float32) * hexc('#EACB8C')
    yy, xx = np.mgrid[0:n, 0:n] / n * math.tau
    for i in range(6):
        kx, ky = rng.randint(1, 6), rng.randint(1, 6)
        H += (rng.uniform(.08, .2) / (1 + i * .4)) * np.sin(kx * xx + ky * yy + rng.uniform(0, 6))
    C *= (1 + 0.08 * np.sin(2 * xx + yy * 3))[..., None]
    for _ in range(42):
        R = rng.randint(7, 14); h = rng.uniform(.3, .6)
        tone = rng.choice([0, 1, 2])
        col = [hexc('#B8926A'), hexc('#CDB188'), hexc('#9C7B58')][tone]
        _stamp(H, C, rng.randint(0, n), rng.randint(0, n), R, h + .25, col, lambda r: np.sqrt(np.clip(1 - r * r, 0, 1)))
    for _ in range(30):
        _stamp(H, C, rng.randint(0, n), rng.randint(0, n), rng.randint(4, 7), .5, hexc('#D6B16C'), lambda r: np.sqrt(np.clip(1 - r * r, 0, 1)))
    img = _shade(H, C, k=6, ao_s=10, ao_k=.8)
    img = cv2.resize((img * 255).astype(np.uint8), (N, N), interpolation=cv2.INTER_AREA)
    return np.dstack([img, np.full((N, N), 255, np.uint8)])


def tile_water():
    n = N * 2
    yy, xx = np.mgrid[0:n, 0:n].astype(np.float32) / n * math.tau
    waves = [(2, 1, .9, 0.3), (3, -1, .55, 1.7), (1, 3, .45, 4.0), (4, -2, .12, 2.2)]
    H = np.zeros((n, n), np.float32); gx = np.zeros_like(H); gy = np.zeros_like(H)
    for kx, ky, a, ph in waves:
        arg = kx * xx + ky * yy + ph
        H += a * np.sin(arg); gx += a * kx * np.cos(arg); gy += a * ky * np.cos(arg)
    Hn = (H - H.min()) / (H.max() - H.min())
    deep, mid, light = hexc('#0369A1'), hexc('#0EA5E9'), hexc('#7DD3FC')
    t = Hn[..., None]
    col = np.where(t < .5, deep + (mid - deep) * (t / .5), mid + (light - mid) * ((t - .5) / .5))
    nx, ny = -gx * .15, -gy * .15
    nl = np.sqrt(nx * nx + ny * ny + 1); nx, ny, nz = nx / nl, ny / nl, 1 / nl
    L = np.array([-.5, -.55, .67]); L /= np.linalg.norm(L)
    dif = np.clip(nx * L[0] + ny * L[1] + nz * L[2], 0, 1)
    hh = L + np.array([0, 0, 1.0]); hh /= np.linalg.norm(hh)
    sp = np.clip(nx * hh[0] + ny * hh[1] + nz * hh[2], 0, 1) ** 90
    col = col * (.72 + .5 * dif)[..., None] + sp[..., None] * .85
    # buih / kilau pada puncak gelombang
    foam = np.clip((Hn - .84) * 8, 0, 1) * (0.5 + 0.5 * np.sin(xx * 6 + yy * 4))
    col = col + (foam * .22)[..., None]
    # garis kaustik halus
    c = np.abs(np.sin(xx * 6 + 2 * np.sin(yy * 3))) * np.abs(np.sin(yy * 7 - 2 * np.sin(xx * 2)))
    col = col + (np.clip(c - .86, 0, 1) * 1.0)[..., None] * hexc('#BAE6FD') * .3
    img = cv2.resize((np.clip(col, 0, 1) * 255).astype(np.uint8), (N, N), interpolation=cv2.INTER_AREA)
    return np.dstack([img, np.full((N, N), 255, np.uint8)])


# ------------------------------------------------------------------ bangunan & dekorasi
CREAM = hexc('#FEF3C7'); WOOD = hexc('#7C3F1D'); WOOD_L = hexc('#B7791F'); STONE = hexc('#CBD5E1')
CB = ((-2.3, 2.3), (0, 4.4), (-2.3, 2.3))


def _roof_tiles(x, y, z, col):
    s = np.sin(z * 17) * .5 + .5
    return col * (0.86 + 0.18 * s)[:, None]


def _planks(x, y, z, col):
    s = (np.sin(x * 26) > .86) | (np.sin(y * 3.5 * 6) > .92)
    out = col.copy(); out[s] = out[s] * .86
    return out


def _stripe_awn(x, y, z, col):
    m = np.sin(x * 7.2) > 0
    out = col.copy(); out[m] = hexc('#F8FAFC')
    return out


def house():
    P = []
    P.append(B((0, .1, 0), (1.35, .1, 1.15), hexc('#94A3B8'), rr=.04, spec=.1))
    P.append(B((0, .95, 0), (1.2, .85, 1.0), CREAM, rr=.05, spec=.08, tex=_planks))
    P.append(G((0, 1.78, 0), 1.5, 1.0, 1.28, hexc('#EA580C'), rr=.06, spec=.25, tex=_roof_tiles))
    P.append(B((0, 1.82, 1.25), (.04, .04, .04), hexc('#EA580C')))
    # panel surya di sisi kiri atap
    P.append(B((-.8, 2.2, .0), (.5, .035, .75), hexc('#1D4ED8'), rr=.02, rot=(0, 0, 33.7), spec=.9, shin=60, tex=_grid2, bias=-.03))
    P.append(B((-.8, 2.21, .0), (.54, .03, .79), hexc('#E5E7EB'), rr=.015, rot=(0, 0, 33.7), spec=.6, bias=-.01))
    # cerobong
    P.append(B((.78, 2.6, -.35), (.17, .42, .17), hexc('#9CA3AF'), rr=.03, tex=_bricks2))
    P.append(B((.78, 3.05, -.35), (.23, .05, .23), hexc('#6B7280'), rr=.02))
    # pintu & jendela
    P.append(B((-.45, .72, 1.02), (.3, .52, .04), WOOD, rr=.03, tex=_planks, spec=.15))
    P.append(S((-.28, .7, 1.08), .035, hexc('#FDE047'), spec=.9, shin=60))
    P.append(B((.55, .98, 1.02), (.36, .32, .035), hexc('#FDE68A'), rr=.02, emit=.5, spec=.7, shin=60))
    P.append(B((.55, .98, 1.045), (.38, .02, .02), WOOD, rr=.01))
    P.append(B((.55, .98, 1.045), (.02, .34, .02), WOOD, rr=.01))
    P.append(B((.55, .98, 1.04), (.41, .35, .02), hexc('#F8FAFC'), rr=.02, bias=.015))
    P.append(B((.55, .6, 1.1), (.4, .1, .12), hexc('#92400E'), rr=.03))
    for i, c in enumerate(('#EF4444', '#F472B6', '#FDE047', '#F472B6', '#EF4444')):
        P.append(S((.28 + i * .13, .76, 1.12), .08, hexc(c), spec=.3))
        P.append(S((.28 + i * .13, .68, 1.14), .06, hexc('#22A94B'), s=(1, .6, 1), spec=.1))
    return P


def _grid2(x, y, z, col):
    g = (np.sin((x + y * .6) * 22) > .78) | (np.sin(z * 22) > .8)
    out = col.copy(); out[g] = out[g] * .5 + .42
    return out


def _bricks2(x, y, z, col):
    l = (np.sin(y * 26) > .75) | (np.sin((x + z) * 18 + np.floor(y * 4.1) * 1.4) > .9)
    out = col.copy(); out[l] = out[l] * .8
    return out


def shop():
    P = []
    P.append(B((0, .1, 0), (1.5, .1, 1.2), hexc('#94A3B8'), rr=.04, spec=.1))
    P.append(B((0, 1.1, 0), (1.35, 1.0, 1.08), hexc('#FEF9C3'), rr=.05, spec=.08, tex=_planks))
    P.append(B((0, 2.18, 0), (1.5, .1, 1.22), hexc('#15803D'), rr=.06, spec=.3))
    # papan nama kuning
    P.append(B((0, 2.7, .7), (.82, .3, .07), hexc('#FACC15'), rr=.1, spec=.4))
    P.append(B((0, 2.7, .66), (.88, .34, .04), hexc('#78350F'), rr=.1, bias=.03))
    for sx in (-.4, .4):
        P.append(S((sx, 2.7, .78), .1, hexc('#7C2D12'), s=(.7, 1.2, .5), rot=(0, 0, 20 * (1 if sx < 0 else -1)), bias=-.03, spec=.3))
    P.append(S((0, 2.7, .79), .09, hexc('#F97316'), s=(1, 1, .5), bias=-.03, spec=.3))
    # tenda belang
    P.append(B((0, 1.72, 1.3), (1.4, .045, .5), hexc('#16A34A'), rr=.03, rot=(24, 0, 0), tex=_stripe_awn, spec=.15))
    for i in range(8):
        P.append(S((-1.3 + i * .372, 1.45, 1.74), .17, hexc('#F8FAFC') if i % 2 else hexc('#16A34A'), s=(1, .8, .5), spec=.15))
    # pintu & jendela
    P.append(B((-.65, .78, 1.1), (.34, .6, .04), hexc('#7C3F1D'), rr=.03, tex=_planks))
    P.append(B((-.65, .98, 1.14), (.2, .22, .02), hexc('#FDE68A'), rr=.02, emit=.3, bias=-.01))
    P.append(B((.5, 1.0, 1.1), (.5, .4, .035), hexc('#BAE6FD'), rr=.03, spec=.9, shin=60))
    P.append(B((.5, 1.0, 1.095), (.54, .44, .02), hexc('#F8FAFC'), rr=.02, bias=.02))
    # peti buah
    P.append(B((.45, .25, 1.55), (.62, .2, .24), hexc('#B7791F'), rr=.04, tex=_planks, spec=.1))
    for i, c in enumerate(('#EF4444', '#EF4444', '#F97316', '#FACC15', '#F97316', '#EF4444', '#FACC15')):
        P.append(S((-.05 + i * .18, .5, 1.52 + (i % 2) * .08), .13, hexc(c), spec=.6, shin=40))
    return P


def station():
    P = []
    P.append(B((0, .1, 0), (1.3, .1, 1.1), hexc('#94A3B8'), rr=.04, spec=.1))
    P.append(B((0, .95, 0), (1.15, .85, .95), hexc('#F8FAFC'), rr=.05, spec=.12))
    P.append(G((0, 1.78, 0), 1.35, .85, 1.15, hexc('#38BDF8'), rr=.06, spec=.5, shin=40))
    # petir kuning di atap depan
    P.append(B((-.05, 2.15, 1.2), (.09, .26, .03), hexc('#FACC15'), rr=.02, rot=(0, 0, 22), emit=.25, spec=.6, bias=-.02))
    P.append(B((.08, 1.95, 1.21), (.09, .22, .03), hexc('#FACC15'), rr=.02, rot=(0, 0, -25), emit=.25, spec=.6, bias=-.02))
    # pintu kaca & monitor
    P.append(B((-.55, .72, .98), (.3, .5, .035), hexc('#075985'), rr=.03, spec=.7))
    P.append(B((-.55, .8, 1.0), (.2, .26, .02), hexc('#BAE6FD'), rr=.02, spec=.9, shin=60, bias=-.01))
    P.append(B((.5, .95, .98), (.4, .3, .035), hexc('#0F172A'), rr=.03, spec=.5))
    for i, h in enumerate((.1, .18, .27, .2, .12)):
        P.append(B((.3 + i * .1, .75 + h * .5, 1.0), (.03, h, .02), hexc('#4ADE80'), rr=.01, emit=.8, bias=-.01))
    P.append(B((-.55, .26, 1.0), (.2, .07, .04), hexc('#F59E0B'), rr=.02, bias=-.01))
    # turbin angin kecil
    P.append(RC((.65, 2.5, -.4), (.65, 3.55, -.4), .09, .05, hexc('#E5E7EB'), spec=.5))
    hub = (.65, 3.6, -.28)
    P.append(S(hub, .1, hexc('#F8FAFC'), spec=.6))
    for i in range(3):
        a = math.radians(i * 120 + 25)
        P.append(RC(hub, (hub[0] + math.cos(a) * .6, hub[1] + math.sin(a) * .6, hub[2]), .06, .02, hexc('#F8FAFC'), spec=.5))
    return P


def well():
    P = []
    P.append(C((0, .42, 0), .98, .42, hexc('#CBD5E1'), rr=.08, spec=.1, tex=_bricks3))
    P.append(T((0, .84, 0), .93, .08, hexc('#94A3B8'), spec=.2))
    P.append(C((0, .78, 0), .78, .03, hexc('#0EA5E9'), rr=.01, emit=.15, spec=1.0, shin=60))
    for sx in (-.88, .88):
        P.append(B((sx, 1.55, 0), (.08, .85, .08), hexc('#7C3F1D'), rr=.03, tex=_planks))
    P.append(B((0, 2.3, 0), (1.0, .07, .07), hexc('#7C3F1D'), rr=.03))
    P.append(Y((0, 2.38, 0), 1.35, .75, hexc('#C2410C'), spec=.25, tex=_roof_tiles2))
    P.append(CAP((0, 2.28, 0), (0, 1.55, 0), .02, hexc('#E5D5B0'), spec=.1))
    P.append(C((0, 1.4, 0), .16, .13, hexc('#92400E'), rr=.03))
    # keran & pipa
    P.append(CAP((.95, .55, 0), (1.55, .55, 0), .1, hexc('#9CA3AF'), spec=.6))
    P.append(CAP((1.55, .55, 0), (1.55, .3, 0), .09, hexc('#9CA3AF'), spec=.6))
    P.append(S((1.55, .27, 0), .1, hexc('#0EA5E9'), s=(.8, 1.2, .8), spec=.9, emit=.2))
    return P


def _bricks3(x, y, z, col):
    l = (np.sin(y * 24) > .78) | (np.sin((np.arctan2(z, x)) * 9 + np.floor(y * 3.8) * 1.5) > .9)
    out = col.copy(); out[l] = out[l] * .8
    return out


def _roof_tiles2(x, y, z, col):
    s = np.sin(y * 26) * .5 + .5
    return col * (.85 + .2 * s)[:, None]


def tree():
    P = []
    P.append(RC((0, 0, 0), (0, 1.9, 0), .38, .24, hexc('#78350F'), spec=.08, tex=_bark, k=.1))
    for (x, y, z, r) in ((0, 2.5, 0, 1.15), (-.8, 2.2, .1, .8), (.85, 2.25, -.1, .82), (.1, 3.2, -.1, .8), (-.25, 2.5, .7, .75), (.35, 2.7, .55, .6)):
        P.append(S((x, y, z), r, hexc('#2FAE4F') * (.92 + .12 * ((x * 7 + y * 3) % 3) / 3), spec=.25, shin=20, k=.12, tex=_foliage))
    rng = np.random.RandomState(3)
    for (x, y, z) in ((-.5, 2.0, 1.2), (.55, 2.45, 1.25), (1.15, 2.0, .55), (-1.2, 2.5, .5), (.1, 3.0, .95), (-.35, 3.45, .75), (.3, 1.95, 1.2)):
        P.append(S((x, y, z), .2, hexc('#EF3B2D'), spec=.8, shin=50, bias=-.02))
    return P


def _bark(x, y, z, col):
    s = np.sin(np.arctan2(z, x) * 7 + y * 2) * .5 + .5
    return col * (.82 + .3 * s)[:, None]


def _foliage(x, y, z, col):
    s = np.sin(x * 11) * np.sin(y * 13 + z * 5) * .5 + .5
    return col * (.86 + .2 * s)[:, None]


def bush():
    P = []
    for (x, y, z, r) in ((-.55, .62, 0, .72), (.5, .6, .05, .68), (0, .85, -.1, .8), (.05, .6, .5, .6)):
        P.append(S((x, y, z), r, hexc('#2FB454'), spec=.25, shin=20, k=.1, tex=_foliage))
    for i, (x, y, z) in enumerate(((-.6, .95, .55), (.55, 1.0, .5), (0, 1.5, .3), (.1, .75, .98), (-.9, .65, .4), (.95, .62, .3), (.2, 1.3, .6))):
        P.append(S((x, y, z), .11, hexc('#F9A8D4') if i % 2 else hexc('#FCE7F3'), spec=.4, bias=-.02))
    return P


def flowers():
    P = []
    P.append(S((0, 0, 0), 1.0, hexc('#3FB760'), s=(1, .22, 1), spec=.1, k=.1))
    rng = np.random.RandomState(7)
    cols = ['#EF4444', '#FDE047', '#F472B6', '#A78BFA', '#FB923C', '#F8FAFC']
    pos = [(-.6, -.2, 1.5), (-.15, .3, 1.9), (.4, -.1, 1.6), (.7, .45, 1.2), (-.45, .55, 1.15), (.1, -.5, 1.0)]
    for i, (x, z, h) in enumerate(pos):
        c = hexc(cols[i])
        P.append(CAP((x, .1, z), (x + .03, h, z), .035, hexc('#15803D'), spec=.1))
        P.append(S((x + .2, h * .5, z), .17, hexc('#22A94B'), s=(1.2, .25, .55), rot=(0, 0, 25), spec=.2))
        for k in range(6):
            a = k * math.tau / 6
            P.append(S((x + math.cos(a) * .17, h + .02, z + math.sin(a) * .17), .115, c, s=(1, .5, 1), spec=.3))
        P.append(S((x, h + .04, z), .09, hexc('#7C2D12') if i != 1 else hexc('#92400E'), spec=.4, bias=-.01))
    return P


def rocks():
    P = []
    P.append(S((-.5, .42, 0), .62, hexc('#9CA3AF'), s=(1.2, .8, 1), rot=(0, 20, 0), spec=.25, shin=30, tex=_rock))
    P.append(S((.5, .55, -.1), .7, hexc('#CBD5E1'), s=(1.1, .85, .95), rot=(0, -25, 0), spec=.3, shin=30, tex=_rock))
    P.append(S((.1, .25, .65), .38, hexc('#94A3B8'), s=(1.3, .75, 1), rot=(0, 40, 0), spec=.25, shin=30, tex=_rock))
    P.append(S((.45, 1.03, -.1), .3, hexc('#3FA95A'), s=(1.4, .35, 1.1), spec=.15, bias=-.02))
    P.append(S((-.55, .88, 0), .2, hexc('#3FA95A'), s=(1.3, .3, 1), spec=.15, bias=-.02))
    return P


def _rock(x, y, z, col):
    s = np.sin(x * 14) * np.sin(y * 17 + z * 6) * np.sin(z * 12)
    return col * (.9 + .12 * s)[:, None]


def fence():
    P = []
    for px in (-256 / 6 / 85 * 2, 0, 256 / 6 / 85 * 2):
        pass
    sp = 256 / 85 / 3
    for i in (-1, 0, 1):
        P.append(RC((i * sp, 0, 0), (i * sp, 1.25, 0), .17, .17, hexc('#B7791F'), spec=.12, tex=_planks2))
        P.append(S((i * sp, 1.27, 0), .17, hexc('#D97706'), spec=.2))
    for y in (.5, .92):
        P.append(B((0, y, .03), (1.7, .09, .06), hexc('#D97706'), rr=.03, spec=.15, tex=_planks2))
    return P


def _planks2(x, y, z, col):
    s = np.sin(y * 28 + x * 2) * .5 + .5
    return col * (.88 + .16 * s)[:, None]


def sign():
    P = []
    P.append(RC((0, 0, 0), (0, 2.1, 0), .12, .1, hexc('#92400E'), spec=.1, tex=_planks2))
    P.append(B((0, 2.15, .12), (.95, .45, .07), hexc('#FEF3C7'), rr=.1, spec=.2))
    P.append(B((0, 2.15, .08), (1.0, .5, .05), hexc('#92400E'), rr=.1, bias=.02))
    P.append(B((.12, 2.15, .21), (.38, .08, .03), hexc('#16A34A'), rr=.03, bias=-.02, spec=.4))
    P.append(G((-.42, 2.15, .21), .27, .3, .035, hexc('#16A34A'), rr=.02, rot=(0, 0, 90), bias=-.02, spec=.4))
    P.append(S((0, 0, 0.0), .5, hexc('#3FB760'), s=(1, .25, 1), spec=.1))
    return P
