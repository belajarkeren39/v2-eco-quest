"""
cover3d.py — cover 1920x1080 bergaya 3D "golden hour".
Terrain sawah berundak dirender dengan raymarching heightfield (perspektif),
lalu diberi rumah, kincir angin, pohon, dan palem 3D dari mesin render3d.
Area kiri sengaja dibuat tenang untuk panel teks.
"""
import math
import numpy as np
import cv2
from scipy import ndimage as ndi
from render3d import *

W, H = 1280, 720
FOV = 40.0
F_PX = (H / 2) / math.tan(math.radians(FOV / 2))
CAM = np.array([0.0, 9.0, 0.0])
PITCH = math.radians(3.2)   # sedikit menengadah
CY0 = H / 2
SUN = np.array([0.30, 0.15, -0.94]); SUN = SUN / np.linalg.norm(SUN)


def sstep(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


# ----------------------------------------------------------------------------- terrain
def base_h(x, z):
    h = 1.9 * np.sin(x * .045 + 1.3) * np.cos(z * .03 + .5) + .6 * np.sin(x * .11 + z * .07) + .22 * np.sin(x * .23 - z * .19 + 2.0)
    h = h + 0.04 * np.maximum(-z - 8, 0)
    m = sstep(-70, -150, z)
    h = h + m * (11 + 7 * np.sin(x * .021 + 1.0) + 3.5 * np.sin(x * .053 + 2.0) + 2 * np.sin(x * .11 + z * .03) - 4 * sstep(0, 60, x))
    return h


STEP = 0.85


def terr(x, z):
    hb = base_h(x, z)
    tw = sstep(-16, -26, z) * (1 - sstep(70, 120, np.abs(x - 12))) * (1 - sstep(-95, -125, z))
    ramp = 0.085 * np.maximum(-z - 14, 0)
    u = (hb * .55 + ramp + .45 * np.sin(x * .06 + z * .045) + .25 * np.sin(x * .13 - z * .08)) / STEP
    q = np.floor(u); f = u - q
    hq = STEP * (q + sstep(.80, 1.0, f))
    hq = hq + 1.0
    h = hb * (1 - tw) + hq * tw
    return h, q, f, tw


def hfun(x, z):
    return terr(x, z)[0]


def sky_color(dx, dy, dz, with_sun=True):
    e = np.clip(dy, -0.2, 1.0)
    c0 = hexc('#FFC98A'); c1 = hexc('#F59B7A'); c2 = hexc('#9A7EB5'); c3 = hexc('#35559C'); c4 = hexc('#1F3677')
    t = e[..., None]
    col = np.where(t < .06, c0 + (c1 - c0) * (t / .06),
          np.where(t < .22, c1 + (c2 - c1) * ((t - .06) / .16),
          np.where(t < .55, c2 + (c3 - c2) * ((t - .22) / .33), c3 + (c4 - c3) * np.clip((t - .55) / .45, 0, 1))))
    ang = dx * SUN[0] + dy * SUN[1] + dz * SUN[2]
    if with_sun:
        glow = np.exp((ang - 1) * 70) * .6 + np.exp((ang - 1) * 10) * .24
        col = col + glow[..., None] * hexc('#FFC27A')
        disc = sstep(.99965, .99985, ang)
        col = col * (1 - disc[..., None]) + disc[..., None] * hexc('#FFF3CF') * 1.3
    return col


def camera_dirs():
    xs = (np.arange(W) + .5 - W / 2) / F_PX; ys = -(np.arange(H) + .5 - CY0) / F_PX
    X, Y = np.meshgrid(xs, ys)
    d = np.stack([X, Y, -np.ones_like(X)], -1)
    d = d / np.linalg.norm(d, axis=-1, keepdims=True)
    c, s = math.cos(PITCH), math.sin(PITCH)  # pitch ke atas
    dy = d[..., 1] * c + d[..., 2] * (-s) * -1 * 0
    y2 = d[..., 1] * c - d[..., 2] * s
    z2 = d[..., 1] * s + d[..., 2] * c
    d = np.stack([d[..., 0], y2, z2], -1)
    return d.astype(np.float32)


def project(x, y, z):
    dx, dy, dz = x - CAM[0], y - CAM[1], z - CAM[2]
    c, s = math.cos(PITCH), math.sin(PITCH)
    y2 = dy * c + dz * s * 1.0
    z2 = -dy * s + dz * c
    # kebalikan rotasi pitch di atas
    px = W / 2 + F_PX * dx / (-z2)
    py = CY0 - F_PX * y2 / (-z2)
    return px, py, -z2


def render_terrain():
    d = camera_dirs().reshape(-1, 3)
    n = d.shape[0]
    dx, dy, dz = d[:, 0].copy(), d[:, 1].copy(), d[:, 2].copy()
    T = np.full(n, -1.0, np.float32)
    idx = np.nonzero(dz < -1e-3)[0]
    t = np.full(idx.size, 2.0, np.float32)
    for it in range(260):
        if idx.size == 0:
            break
        x = CAM[0] + dx[idx] * t; y = CAM[1] + dy[idx] * t; z = CAM[2] + dz[idx] * t
        hh = hfun(x, z)
        gap = y - hh
        hit = gap < (0.03 + 0.0012 * t)
        T[idx[hit]] = t[hit]
        far = t > 380
        t = t + np.clip(gap * .5, .04 + .002 * t, 6.0)
        alive = (~hit) & (~far) & (y < 60)
        idx = idx[alive]; t = t[alive]
    hit = T > 0
    hi = np.nonzero(hit)[0]
    img = np.zeros((n, 3), np.float32)
    depth = np.full(n, 1e4, np.float32)
    # ---- langit
    sk = sky_color(dx, dy, dz)
    img[:] = sk
    t = T[hi]
    x = CAM[0] + dx[hi] * t; y = CAM[1] + dy[hi] * t; z = CAM[2] + dz[hi] * t
    h0, q, f, tw = terr(x, z)
    e = .06
    hx = (hfun(x + e, z) - hfun(x - e, z)) / (2 * e); hz = (hfun(x, z + e) - hfun(x, z - e)) / (2 * e)
    slope = np.sqrt(hx * hx + hz * hz)
    # ---- material
    nz_ = ((q * 37 + 11) % 5).astype(np.int32)
    flat = slope < .18
    noise = np.sin(x * .9) * np.sin(z * .8) * .5 + np.sin(x * 2.3 + z * 1.7) * .25
    grass = hexc('#58A73F') * (.85 + .15 * noise)[:, None] + hexc('#9CC24C') * (.18 + .18 * np.sin(x * .13 + z * .09))[:, None]
    slopec = hexc('#6C8E3A') * (.8 + .2 * noise)[:, None]
    col = np.where(flat[:, None], grass, slopec).astype(np.float32)
    sf = np.exp(-t * .025)
    stripes = (np.sin(z * 9.0 + x * .15) * .5 + .5) * sf + .5 * (1 - sf)
    stripes2 = np.sin(x * 6.0) * .5 + .5
    terr_flat = flat & (tw > .5)
    # tipe petak sawah
    young = terr_flat & (nz_ == 0)
    gold = terr_flat & (nz_ == 1)
    soil_ = terr_flat & (nz_ == 2)
    water = terr_flat & ((nz_ == 3) | (nz_ == 4))
    col[young] = (hexc('#6BC24A') * (.7 + .5 * stripes[young])[:, None])
    col[gold] = (hexc('#D9B245') * (.72 + .4 * stripes[gold])[:, None])
    col[soil_] = (hexc('#8C5A33') * (.7 + .5 * stripes[soil_])[:, None])
    # ladang depan (tiap petak berbeda)
    fg = flat & (tw < .5) & (z > -26) & (z < -2)
    cell = (np.floor(x / 9.0) * 3 + np.floor(z / 7.0) * 5).astype(np.int32) % 4
    fgrow = (np.sin(x * 2.6) * .5 + .5) * np.exp(-t * .02) + .5 * (1 - np.exp(-t * .02))
    for ci, base in enumerate(('#78C850', '#C9B04A', '#8A5A33', '#4FAE45')):
        m = fg & (cell == ci)
        col[m] = hexc(base) * (.74 + .4 * fgrow[m])[:, None]
    # ---- normal
    nx = -hx; ny = np.ones_like(hx); nz = -hz
    nn = np.sqrt(nx * nx + ny * ny + nz * nz); nx, ny, nz = nx / nn, ny / nn, nz / nn
    # alur tanaman pada normal
    ridge = np.where(fg, np.cos(x * 2.6) * .35, np.where(young | gold | soil_, np.cos(z * 9) * .12, 0.0))
    nx = nx + ridge * (fg); nz = nz + (np.cos(z * 9) * -.1) * (young | gold | soil_)
    nn = np.sqrt(nx * nx + ny * ny + nz * nz); nx, ny, nz = nx / nn, ny / nn, nz / nn
    # ---- bayangan lembut (marching ke arah matahari)
    vis = np.ones(hi.size, np.float32); tt = np.full(hi.size, .25, np.float32)
    for _ in range(26):
        sh = hfun(x + SUN[0] * tt, z + SUN[2] * tt)
        gap = (y + SUN[1] * tt + .05) - sh
        vis = np.minimum(vis, np.clip(7.0 * gap / tt, 0, 1))
        tt = tt + np.clip(gap * .6, .3, 4.0) * 1.0 + .15
    vis = vis * vis * (3 - 2 * vis)
    ndl = nx * SUN[0] + ny * SUN[1] + nz * SUN[2]
    diff = np.clip((ndl + .25) / 1.25, 0, 1)
    key = hexc('#FFB873') * 1.15
    sky_amb = hexc('#9C8FC4') * .5 + hexc('#FFC9A0') * .22
    hemi = np.clip(.5 + .5 * ny, 0, 1)[:, None]
    amb = (hexc('#6B5A4A') * (1 - hemi) + sky_amb * hemi) * 1.0
    lit = col * (amb * 1.45 + key * (diff * vis)[:, None] * 1.25)
    # rim cahaya dari belakang (kilau tepi bukit)
    V = -np.stack([dx[hi], dy[hi], dz[hi]], -1)
    ndv = np.clip(nx * V[:, 0] + ny * V[:, 1] + nz * V[:, 2], 0, 1)
    lit = lit + hexc('#FFC27A') * ((1 - ndv) ** 4 * vis * .22)[:, None] * col
    # ---- air sawah memantulkan langit
    if water.any():
        w = water
        rdx, rdy, rdz = dx[hi][w], -dy[hi][w], dz[hi][w]
        rdy = np.abs(rdy) + .02 * np.sin(x[w] * 3 + z[w] * 5)
        refl = sky_color(rdx, rdy, rdz)
        fres = .35 + .65 * (1 - np.abs(dy[hi][w])) ** 3
        deep = hexc('#28566B')
        wc = deep * (1 - fres[:, None]) + refl * fres[:, None]
        wc = wc * (.92 + .08 * np.sin(z[w] * 20))[:, None]
        lit[w] = wc
    # ---- kabut atmosfer
    dist = t
    fogd = 1 - np.exp(-dist * .0052)
    sunamt = np.clip((dx[hi] * SUN[0] + dz[hi] * SUN[2]), 0, 1) ** 8
    far_k = np.clip(dist / 160, 0, 1)[:, None]
    hz_col = hexc('#F4B88C') * (1 - far_k * .7) + hexc('#9D8CC0') * far_k * .7
    hz_col = hz_col + (hexc('#FFD7A0') * sunamt[:, None]) * .35
    ff = np.clip(fogd * (1 + (1 - np.clip(y / 14, 0, 1)) * .3), 0, .9)[:, None]
    lit = lit * (1 - ff) + hz_col * ff
    img[hi] = lit
    depth[hi] = t
    return img.reshape(H, W, 3), depth.reshape(H, W), d.reshape(H, W, 3)


# ----------------------------------------------------------------------------- awan 3D
def fbm(x, y, oct=5, seed=0):
    out = np.zeros_like(x); a = .5; fr = 1.0
    for i in range(oct):
        out += a * (np.sin(x * fr * 1.7 + seed + i * 3.1) * np.sin(y * fr * 1.3 + seed * 1.7 + i) +
                    np.sin((x + y) * fr * 2.1 + i * 1.9) * .5 + np.sin((x - y) * fr * 2.9 - i) * .35)
        fr *= 2.0; a *= .5
    return out


def clouds(img, d, depth):
    dyv = d[..., 1]
    mask = (dyv > .02) & (depth > 9000)
    t = 70.0 / np.maximum(dyv, .03)
    px = d[..., 0] * t * .012; pz = d[..., 2] * t * .012
    def dens(ox=0.0, oz=0.0):
        n = fbm(px + ox, pz + oz, 5, 1.3)
        return sstep(.15, .85, n * .62 + .15)
    c0 = dens()
    ofs = .035
    c1 = dens(SUN[0] * ofs * 3, SUN[2] * ofs * 3)
    edge = np.clip((c0 - c1) * 5 + .5, 0, 1)
    lit = hexc('#FFD7A5') * (.55 + .7 * edge)[..., None]
    shade = hexc('#8F6F9A') * (1 - edge)[..., None]
    cc = np.where(edge[..., None] > .5, lit, hexc('#C99AA0') * (.5 + edge)[..., None] + shade * .35)
    cc = cc * (.55 + .5 * np.clip(dyv[..., None] * 3 + .35, 0, 1))
    fade = sstep(.02, .22, dyv)[..., None]
    a = (c0[..., None] * .85 * fade * mask[..., None])
    return img * (1 - a) + cc * a


def god_rays(img, d):
    sx, sy, _ = (W / 2 + F_PX * (SUN[0] / -SUN[2]), CY0 - F_PX * (SUN[1] / -SUN[2]), 0)
    # koreksi pitch sederhana
    sx, sy, _ = project(CAM[0] + SUN[0] * 500, CAM[1] + SUN[1] * 500, CAM[2] + SUN[2] * 500)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    ang = np.arctan2(yy - sy, xx - sx); r = np.sqrt((xx - sx) ** 2 + (yy - sy) ** 2)
    rays = (np.sin(ang * 23 + 1.3) * .5 + .5) ** 3 * (np.sin(ang * 9 - 2.0) * .5 + .5)
    m = np.exp(-r / 520) * np.clip((sy + 40 - yy) / 200, 0, 1) * (d[..., 1] > 0)
    return img + (rays * m * .12)[..., None] * hexc('#FFC27A') * (1.0), (sx, sy)


# ----------------------------------------------------------------------------- sprite 3D
SPR_LIGHT = dict(L=(0.52, 0.42, -0.55), key=(1.0, .72, .42), key_i=1.0, sky=(.62, .68, .95), ground=(.55, .42, .30),
                 amb_i=.55, rim=(1.0, .78, .45), rim_i=.55)


def sprite(prims, S_px, bounds, elev, wu, hu, base_frac=.86, ss=2, **kw):
    """Render sprite; ukuran kanvas dari lebar/tinggi unit dunia. Kembalikan (rgba, ox, oy)."""
    Wc = int(wu * S_px) + 8; Hc = int(hu * S_px * math.cos(math.radians(elev))) + int(S_px * wu * .25) + 8
    ox = Wc / 2; oy = Hc * base_frac
    a = render(prims, Wc, Hc, S_px, ox, oy, elev=elev, ss=ss, bounds=bounds, light=SPR_LIGHT, outline=0, crease=False,
               shadow_strength=.55, edge_fade=10, shadow_col=(.16, .10, .20), **kw)
    return a, ox, oy


def blend(canvas, spr, ox, oy, px, py, haze=0.0, haze_col=None, scale=1.0):
    a = spr.astype(np.float32) / 255
    rgb, al = a[..., :3], a[..., 3:4]
    if haze > 0:
        rgb = rgb * (1 - haze) + haze_col * haze
    x0 = int(round(px - ox)); y0 = int(round(py - oy))
    h, w = al.shape[:2]
    X0, Y0 = max(0, x0), max(0, y0); X1, Y1 = min(canvas.shape[1], x0 + w), min(canvas.shape[0], y0 + h)
    if X1 <= X0 or Y1 <= Y0:
        return
    sub = (slice(Y0 - y0, Y1 - y0), slice(X0 - x0, X1 - x0))
    reg = canvas[Y0:Y1, X0:X1]
    canvas[Y0:Y1, X0:X1] = reg * (1 - al[sub]) + rgb[sub] * al[sub]


def turbine(angle, H_=7.5):
    P = [RC((0, 0, 0), (0, H_, 0), .22, .12, hexc('#F1F5F9'), spec=.5)]
    P.append(S((0, H_ + .05, .25), .24, hexc('#E2E8F0'), s=(1, 1, 1.5), spec=.5))
    hub = (0, H_ + .05, .55)
    P.append(S(hub, .17, hexc('#F8FAFC'), spec=.6))
    for i in range(3):
        a = math.radians(angle + i * 120)
        tip = (hub[0] + math.cos(a) * 4.2, hub[1] + math.sin(a) * 4.2, hub[2])
        P.append(RC(hub, tip, .13, .03, hexc('#F8FAFC'), spec=.5))
    return P


def palm(flip=1):
    P = []
    pts = []
    Ht = 12.0
    for i in range(9):
        t = i / 8
        pts.append((flip * (2.4 * t * t) * 1.0, Ht * t, 0))
    for i in range(8):
        P.append(RC(pts[i], pts[i + 1], .62 - .04 * i, .62 - .04 * (i + 1), hexc('#6B4A2B'), spec=.08, tex=_rings, k=.05))
    c = pts[-1]
    P.append(S((c[0], c[1] + .2, 0), .55, hexc('#5B3A1E'), spec=.1))
    rng = np.random.RandomState(2)
    for k in range(9):
        yaw = k * 40 + rng.uniform(-8, 8); th0 = rng.uniform(25, 60); L = rng.uniform(4.6, 6.2)
        dx, dz = math.cos(math.radians(yaw)), -math.sin(math.radians(yaw))
        seg = []
        for j in range(6):
            s = j / 5
            hor = L * s * math.cos(math.radians(th0))
            ver = L * (math.sin(math.radians(th0)) * s - .95 * s * s)
            seg.append((c[0] + dx * hor, c[1] + .3 + ver, dz * hor))
        for j in range(5):
            P.append(RC(seg[j], seg[j + 1], .1 * (1 - j * .14), .1 * (1 - (j + 1) * .14), hexc('#2F6B2A'), spec=.2))
            mid = ((seg[j][0] + seg[j + 1][0]) / 2, (seg[j][1] + seg[j + 1][1]) / 2, (seg[j][2] + seg[j + 1][2]) / 2)
            lenj = L / 5 * .62
            for sg in (-1, 1):
                R = rotm(0, yaw + sg * 62, -28 - j * 5) if False else yawtilt(yaw + sg * 70, -34 - 4 * j)
                dd = R @ np.array([1.0, 0, 0])
                cc = (mid[0] + dd[0] * lenj * .8, mid[1] + dd[1] * lenj * .8, mid[2] + dd[2] * lenj * .8)
                P.append(S(cc, lenj * 1.15, hexc('#2E8B3A') if (j + k) % 2 else hexc('#3AA047'), s=(1, .1, .42), rot=R, spec=.35, shin=30))
    return P, Ht


def _rings(x, y, z, col):
    return col * (.8 + .25 * (np.sin(y * 13) * .5 + .5))[:, None]


# ----------------------------------------------------------------------------- rakit
def make(path):
    np.random.seed(1)
    img, depth, dirs = render_terrain()
    img = clouds(img, dirs, depth)
    img, (sx, sy) = god_rays(img, dirs)
    # bloom matahari
    br = np.clip(img - .95, 0, None)
    bl = cv2.GaussianBlur(br, (0, 0), 30) * .8 + cv2.GaussianBlur(br, (0, 0), 9) * .4
    img = img + bl
    # --- skala ke 1920x1080
    k = 1.5
    img8 = np.clip(img, 0, 1.4)
    big = cv2.resize(img8, (1920, 1080), interpolation=cv2.INTER_CUBIC)
    big = np.clip(big, 0, 1.4)
    haze_c = hexc('#F2B98C')

    def place(prims, wx, wz, S_world, bounds, elev, wu, hu, ylift=0.0, hazek=.0085, **kw):
        gy = hfun(np.array([wx], np.float32), np.array([wz], np.float32))[0] + ylift
        px, py, dd = project(wx, gy, wz)
        S_px = F_PX / dd * S_world * k
        spr, ox, oy = sprite(prims, S_px, bounds, elev, wu, hu, **kw)
        hz = float(np.clip(1 - math.exp(-dd * hazek), 0, .9))
        blend(big, spr, ox, oy, px * k, py * k, haze=hz, haze_col=haze_c)
        return px, py, dd

    import world3d as w
    # turbin angin di punggung bukit (jauh -> dekat)
    for (wx, wz, ang) in ((38, -90, 20), (22, -78, 65), (8, -70, 100), (-16, -96, 40), (55, -84, 5)):
        place(turbine(ang), wx, wz, 1.3, ((-5, 5), (0, 12.6), (-3, 3)), 10, 11, 12.6, ylift=0.0)
    # bangunan desa (urut dari yang jauh ke dekat)
    village = [
        (w.house, 6.0, -44, 1.15, 13), (w.house, 14.5, -41, 1.1, 13), (w.shop, 9.5, -35, 1.15, 15), (w.station, 19.5, -37, 1.15, 15),
        (w.house, 13.0, -29, 1.2, 17), (w.well, 5.5, -29, 1.15, 17),
    ]
    trees = [(w.tree, 2.0, -42, 1.2), (w.tree, 18.5, -45, 1.3), (w.tree, 1.5, -34, 1.2), (w.tree, 19, -31, 1.2), (w.bush, 9.0, -27, 1.15), (w.bush, 16.5, -27, 1.1),
             (w.tree, 24, -46, 1.3), (w.bush, 24, -33, 1.1)]
    items = []
    for fn, wx, wz, sc, el in village:
        items.append((wz, 'b', fn, wx, wz, sc, el))
    for fn, wx, wz, sc in trees:
        items.append((wz, 't', fn, wx, wz, sc, 16))
    items.sort(key=lambda it: it[0])
    for _, kind, fn, wx, wz, sc, el in items:
        bnds = ((-2.4, 2.4), (0, 4.6), (-2.4, 2.4))
        place(fn(), wx, wz, sc * (1.0 if kind == 'b' else 1.0) * (1.0 if fn not in (w.well,) else 1.0), bnds, el, 5.2, 4.8, ylift=0.0, base_frac=.84)
    # palem latar depan
    palmP, Ht = palm(1)
    spr_big, ox, oy = sprite(palmP, 34 * k * .55, ((-5, 7), (0, 17), (-6, 6)), 6, 13, 17, ss=2, base_frac=.97)
    spr_big = cv2.GaussianBlur(spr_big.astype(np.float32), (0, 0), 1.0).astype(np.uint8)
    # palem kiri besar
    sc2 = 1.8
    sp2 = cv2.resize(spr_big, None, fx=sc2, fy=sc2, interpolation=cv2.INTER_CUBIC)
    blend(big, sp2, ox * sc2, oy * sc2, 70, 1180)
    sp3 = cv2.resize(spr_big, None, fx=1.15, fy=1.15, interpolation=cv2.INTER_CUBIC)
    blend(big, sp3, ox * 1.15, oy * 1.15, 360, 1010, haze=.18, haze_col=haze_c)
    # palem kanan (cermin)
    flipd = spr_big[:, ::-1].copy()
    sp4 = cv2.resize(flipd, None, fx=1.7, fy=1.7, interpolation=cv2.INTER_CUBIC)
    blend(big, sp4, (spr_big.shape[1] - ox) * 1.7 , oy * 1.7, 1900, 1160)
    # ---- partikel cahaya (bokeh) & kunang-kunang
    rng = np.random.RandomState(7)
    glow = np.zeros_like(big)
    for i in range(70):
        x, y = rng.uniform(0, 1920), rng.uniform(380, 1080); r = rng.uniform(3, 11)
        a = rng.uniform(.08, .35) * (1.0 if x > 520 else .5)
        cv2.circle(glow, (int(x), int(y)), int(r), (a * 1.0, a * .85, a * .45), -1, cv2.LINE_AA)
    glow = cv2.GaussianBlur(glow, (0, 0), 3.0)
    big = big + glow * .8
    # ---- grading: vinyet + filmis
    yy, xx = np.mgrid[0:1080, 0:1920].astype(np.float32)
    vg = 1 - .38 * (((xx - 1100) / 1300) ** 2 + ((yy - 520) / 760) ** 2)
    big = big * np.clip(vg, .45, 1)[..., None]
    # sisi kiri sedikit lebih gelap & tenang untuk panel teks
    lf = np.clip(1 - xx / 900, 0, 1) ** 1.5 * .22
    big = big * (1 - lf[..., None]) + hexc('#1C2A22') * lf[..., None]
    big = np.clip(big, 0, 1.2)
    big = big / (1 + .12 * np.maximum(big - .8, 0))
    lum = (big * np.array([.3, .59, .11], np.float32)).sum(-1, keepdims=True)
    big = np.clip(lum + (big - lum) * 1.12, 0, 1)
    grain = (rng.randn(1080, 1920).astype(np.float32) * .006)[..., None]
    big = np.clip(big + grain, 0, 1)
    out = (big * 255 + .5).astype(np.uint8)
    from PIL import Image
    Image.fromarray(out, 'RGB').save(path, optimize=True)


if __name__ == '__main__':
    import sys
    make(sys.argv[1] if len(sys.argv) > 1 else '/tmp/cover_test.png')
