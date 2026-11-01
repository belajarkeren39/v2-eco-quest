#!/usr/bin/env python3
"""
render3d.py — mesin render 3D mini (raymarching SDF, murni numpy + OpenCV)
untuk membuat sprite 3D "ECOQUEST: Petualangan Desa Hijau".

Fitur: kamera ortografik 3/4, gabungan halus (smooth union), bayangan lembut,
ambient occlusion, cahaya pantul tanah, rim-light, specular, kontur tipis
dan bayangan tanah transparan (shadow catcher) di bawah objek.

Sistem koordinat dunia: x kanan, y atas, z menuju kamera. Titik (0,0,0) = kaki objek.
"""
import math
import numpy as np
import cv2

F = np.float32


def v3(a, b=None, c=None):
    if b is None:
        return np.array(a, dtype=F)
    return np.array([a, b, c], dtype=F)


def hexc(h):
    h = h.lstrip('#')
    return F([int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4)])


def rotm(rx=0.0, ry=0.0, rz=0.0):
    """Matriks rotasi lokal->dunia (derajat), urutan X lalu Y lalu Z."""
    ax, ay, az = [math.radians(v) for v in (rx, ry, rz)]
    cx, sx, cy, sy, cz, sz = math.cos(ax), math.sin(ax), math.cos(ay), math.sin(ay), math.cos(az), math.sin(az)
    Rx = np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])
    Ry = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
    Rz = np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]])
    return Rz @ Ry @ Rx


# ----------------------------------------------------------------------------
# Primitif
# ----------------------------------------------------------------------------
class Prim:
    def __init__(self, kind, pos, col, rot=None, k=0.0, spec=0.18, shin=24.0,
                 emit=0.0, tex=None, bias=0.0, cut=None, **p):
        self.kind = kind
        self.pos = F(pos)
        self.col = F(col) if not isinstance(col, str) else hexc(col)
        self.Ri = None
        if isinstance(rot, np.ndarray) and rot.shape == (3, 3):
            self.Ri = rot.T.astype(F)
        elif rot is not None and any(abs(v) > 1e-6 for v in rot):
            self.Ri = rotm(*rot).T.astype(F)
        self.k, self.spec, self.shin, self.emit, self.tex, self.bias = k, spec, shin, emit, tex, bias
        self.cut = cut  # (nx,ny,nz,off): buang bagian dengan dot(n,p_lokal) > off
        self.p = p
        if kind in ('cap', 'rcone'):
            self.a = F(p['a']); self.b = F(p['b'])

    def _loc(self, x, y, z):
        px = x - self.pos[0]; py = y - self.pos[1]; pz = z - self.pos[2]
        R = self.Ri
        if R is None:
            return px, py, pz
        return (R[0, 0] * px + R[0, 1] * py + R[0, 2] * pz,
                R[1, 0] * px + R[1, 1] * py + R[1, 2] * pz,
                R[2, 0] * px + R[2, 1] * py + R[2, 2] * pz)

    def dist(self, x, y, z):
        k = self.kind
        if k == 'cap':
            return self._cap(x, y, z)
        if k == 'rcone':
            return self._rcone(x, y, z)
        lx, ly, lz = self._loc(x, y, z)
        p = self.p
        if k == 'sph':
            r = p['r']; s = p.get('s')
            if s is None:
                d = np.sqrt(lx * lx + ly * ly + lz * lz) - r
            else:
                ax, ay, az = r * s[0], r * s[1], r * s[2]
                qx, qy, qz = lx / ax, ly / ay, lz / az
                k0 = np.sqrt(qx * qx + qy * qy + qz * qz)
                k1 = np.sqrt((qx / ax) ** 2 + (qy / ay) ** 2 + (qz / az) ** 2)
                d = k0 * (k0 - 1.0) / np.maximum(k1, 1e-4)
        elif k == 'box':
            bx, by, bz = p['h']; rr = p.get('rr', 0.0)
            qx = np.abs(lx) - bx + rr; qy = np.abs(ly) - by + rr; qz = np.abs(lz) - bz + rr
            d = (np.sqrt(np.maximum(qx, 0) ** 2 + np.maximum(qy, 0) ** 2 + np.maximum(qz, 0) ** 2)
                 + np.minimum(np.maximum(np.maximum(qx, qy), qz), 0) - rr)
        elif k == 'cyl':
            r, h, rr = p['r'], p['h'], p.get('rr', 0.0)
            dx = np.sqrt(lx * lx + lz * lz) - r + rr; dy = np.abs(ly) - h + rr
            d = np.minimum(np.maximum(dx, dy), 0) + np.sqrt(np.maximum(dx, 0) ** 2 + np.maximum(dy, 0) ** 2) - rr
        elif k == 'tor':
            q = np.sqrt(lx * lx + lz * lz) - p['R']
            d = np.sqrt(q * q + ly * ly) - p['r']
        elif k == 'gab':  # prisma atap pelana: dasar y=0, puncak y=hh, memanjang sumbu z
            hw, hh, hl, rr = p['hw'], p['hh'], p['hl'], p.get('rr', 0.03)
            ds = (np.abs(lx) * hh + ly * hw - hw * hh) / math.hypot(hh, hw)
            d2 = np.maximum(ds, -ly)
            dz = np.abs(lz) - hl
            d = (np.sqrt(np.maximum(d2 + rr, 0) ** 2 + np.maximum(dz + rr, 0) ** 2)
                 + np.minimum(np.maximum(d2 + rr, dz + rr), 0) - rr)
        elif k == 'pyr':  # limas persegi: dasar y=0, puncak y=hh
            hw, hh = p['hw'], p['hh']; n = math.hypot(hh, hw)
            dxx = (np.abs(lx) * hh + ly * hw - hw * hh) / n
            dzz = (np.abs(lz) * hh + ly * hw - hw * hh) / n
            m = np.maximum(dxx, dzz)
            m = np.maximum(m, -ly)
            d = m
        else:
            raise ValueError(k)
        if self.cut is not None:
            nx, ny, nz, off = self.cut
            d = np.maximum(d, nx * lx + ny * ly + nz * lz - off)
        return d

    def _cap(self, x, y, z):
        a, b, r = self.a, self.b, self.p['r']
        ba = b - a; l2 = float(ba @ ba)
        pax, pay, paz = x - a[0], y - a[1], z - a[2]
        h = np.clip((pax * ba[0] + pay * ba[1] + paz * ba[2]) / l2, 0, 1)
        dx, dy, dz = pax - ba[0] * h, pay - ba[1] * h, paz - ba[2] * h
        return np.sqrt(dx * dx + dy * dy + dz * dz) - r

    def _rcone(self, x, y, z):
        a, b, r1, r2 = self.a, self.b, self.p['r1'], self.p['r2']
        ba = b - a; l2 = float(ba @ ba); rr = r1 - r2; a2 = l2 - rr * rr; il2 = 1.0 / l2
        pax, pay, paz = x - a[0], y - a[1], z - a[2]
        yv = pax * ba[0] + pay * ba[1] + paz * ba[2]
        zv = yv - l2
        vx, vy, vz = pax * l2 - ba[0] * yv, pay * l2 - ba[1] * yv, paz * l2 - ba[2] * yv
        x2 = vx * vx + vy * vy + vz * vz
        y2 = yv * yv * l2; z2 = zv * zv * l2
        kk = np.sign(rr) * rr * rr * x2
        c1 = np.sign(zv) * a2 * z2 > kk
        c2 = np.sign(yv) * a2 * y2 < kk
        d1 = np.sqrt(x2 + z2) * il2 - r2
        d2 = np.sqrt(x2 + y2) * il2 - r1
        d3 = (np.sqrt(np.maximum(x2 * a2 * il2, 0)) + yv * rr) * il2 - r1
        return np.where(c1, d1, np.where(c2, d2, d3))


def yawtilt(yaw, tilt):
    """Miringkan sumbu +x ke atas sebesar tilt (derajat) lalu putar yaw di sekitar sumbu y."""
    return rotm(0, yaw, 0) @ rotm(0, 0, tilt)


# --- konstruktor singkat ------------------------------------------------------
def S(pos, r, col, s=None, **kw):
    return Prim('sph', pos, col, r=r, s=s, **kw)


def B(pos, h, col, rr=0.04, rot=None, **kw):
    return Prim('box', pos, col, rot=rot, h=h, rr=rr, **kw)


def C(pos, r, h, col, rr=0.03, rot=None, **kw):
    return Prim('cyl', pos, col, rot=rot, r=r, h=h, rr=rr, **kw)


def CAP(a, b, r, col, **kw):
    return Prim('cap', (0, 0, 0), col, a=a, b=b, r=r, **kw)


def RC(a, b, r1, r2, col, **kw):
    return Prim('rcone', (0, 0, 0), col, a=a, b=b, r1=r1, r2=r2, **kw)


def T(pos, R, r, col, rot=None, **kw):
    return Prim('tor', pos, col, rot=rot, R=R, r=r, **kw)


def G(pos, hw, hh, hl, col, rr=0.04, rot=None, **kw):
    return Prim('gab', pos, col, rot=rot, hw=hw, hh=hh, hl=hl, rr=rr, **kw)


def Y(pos, hw, hh, col, rot=None, **kw):
    return Prim('pyr', pos, col, rot=rot, hw=hw, hh=hh, **kw)


def smin(a, b, k):
    h = np.maximum(k - np.abs(a - b), 0) / k
    return np.minimum(a, b) - h * h * k * 0.25


def scene_dist(prims, x, y, z, clip=True):
    d = None
    for pr in prims:
        di = pr.dist(x, y, z)
        if d is None:
            d = di
        elif pr.k > 0:
            d = smin(d, di, pr.k)
        else:
            d = np.minimum(d, di)
    if clip:
        d = np.maximum(d, -y)
    return d


# ----------------------------------------------------------------------------
# Render
# ----------------------------------------------------------------------------
DEFAULT_LIGHT = dict(
    L=(-0.40, 0.88, 0.40),
    key=(1.0, 0.92, 0.76), key_i=0.82,
    sky=(0.80, 0.90, 1.0), ground=(0.62, 0.55, 0.34), amb_i=0.46,
    rim=(1.0, 0.86, 0.62), rim_i=0.20,
)


def _norm(v):
    v = np.array(v, dtype=np.float64)
    return v / np.linalg.norm(v)


def render(prims, W, H, S_px, ox, oy, elev=35.0, ss=3, yaw=0.0,
           bounds=((-2.2, 2.2), (0.0, 4.2), (-2.2, 2.2)), ground_shadow=True,
           shadow_strength=0.5, shadow_margin=2.6, outline=1.5, outline_col='#3E2723',
           crease=True, light=None, clip=True, shadow_col=(0.06, 0.13, 0.09),
           contact=0.55, grade=True, bg=None, edge_fade=14):
    """Kembalikan RGBA uint8 (H,W,4)."""
    Lc = dict(DEFAULT_LIGHT)
    if light:
        Lc.update(light)
    Wl, Hl = W * ss, H * ss
    e = math.radians(elev)
    right = np.array([1, 0, 0], np.float64)
    fwd = np.array([0, -math.sin(e), -math.cos(e)], np.float64)
    up = np.array([0, math.cos(e), -math.sin(e)], np.float64)
    # rotasi model oleh yaw == rotasi kamera & cahaya oleh -yaw
    ya = math.radians(-yaw)
    Ry = np.array([[math.cos(ya), 0, math.sin(ya)], [0, 1, 0], [-math.sin(ya), 0, math.cos(ya)]])
    right_m, fwd_m, up_m = Ry @ right, Ry @ fwd, Ry @ up
    Lv = _norm(Lc['L']); Lm = Ry @ Lv
    Vm = -fwd_m

    xs = (np.arange(Wl, dtype=np.float64) + 0.5) / ss
    ys = (np.arange(Hl, dtype=np.float64) + 0.5) / ss
    u = (xs - ox) / S_px
    v = (oy - ys) / S_px
    U, Vv = np.meshgrid(u, v)
    U = U.ravel(); Vv = Vv.ravel()
    Rb = 12.0
    Ox = (U * right_m[0] + Vv * up_m[0] - fwd_m[0] * Rb).astype(F)
    Oy = (U * right_m[1] + Vv * up_m[1] - fwd_m[1] * Rb).astype(F)
    Oz = (U * right_m[2] + Vv * up_m[2] - fwd_m[2] * Rb).astype(F)
    dx, dy, dz = [float(c) for c in fwd_m]
    n = Ox.size

    # AABB
    (x0, x1), (y0, y1), (z0, z1) = bounds
    tn = np.full(n, -1e9, F); tf = np.full(n, 1e9, F)
    ok = np.ones(n, bool)
    for O_, d_, lo, hi in ((Ox, dx, x0, x1), (Oy, dy, y0, y1), (Oz, dz, z0, z1)):
        if abs(d_) < 1e-8:
            ok &= (O_ >= lo) & (O_ <= hi)
        else:
            ta = (lo - O_) / d_; tb = (hi - O_) / d_
            tn = np.maximum(tn, np.minimum(ta, tb)); tf = np.minimum(tf, np.maximum(ta, tb))
    ok &= tf > tn
    ok &= tf > 0
    T_hit = np.full(n, -1.0, F)
    eps = 0.45 / (S_px * ss)
    idx = np.nonzero(ok)[0]
    t = np.maximum(tn[idx], 0).astype(F)
    tm = tf[idx].copy()
    ox_, oy_, oz_ = Ox[idx], Oy[idx], Oz[idx]
    for it in range(140):
        if idx.size == 0:
            break
        x = ox_ + dx * t; y = oy_ + dy * t; z = oz_ + dz * t
        dist = scene_dist(prims, x, y, z, clip)
        hit = dist < eps
        if hit.any():
            T_hit[idx[hit]] = t[hit]
        t = t + np.maximum(dist, eps * 0.6) * 0.88
        alive = (~hit) & (t < tm)
        if not alive.all():
            idx = idx[alive]; t = t[alive]; tm = tm[alive]
            ox_, oy_, oz_ = ox_[alive], oy_[alive], oz_[alive]

    hitm = T_hit >= 0
    hi_idx = np.nonzero(hitm)[0]
    rgb = np.zeros((n, 3), F)
    alpha = np.zeros(n, F)
    depth = np.full(n, 1e3, F)

    if hi_idx.size:
        t = T_hit[hi_idx]
        x = Ox[hi_idx] + dx * t; y = Oy[hi_idx] + dy * t; z = Oz[hi_idx] + dz * t
        h = 0.012
        k0 = scene_dist(prims, x + h, y - h, z - h, clip)
        k1 = scene_dist(prims, x - h, y - h, z + h, clip)
        k2 = scene_dist(prims, x - h, y + h, z - h, clip)
        k3 = scene_dist(prims, x + h, y + h, z + h, clip)
        nx = k0 - k1 - k2 + k3; ny = -k0 - k1 + k2 + k3; nz = -k0 + k1 - k2 + k3
        nl = np.sqrt(nx * nx + ny * ny + nz * nz) + 1e-9
        nx, ny, nz = nx / nl, ny / nl, nz / nl
        # material
        m = len(prims)
        Dm = np.empty((m, hi_idx.size), F)
        for i, pr in enumerate(prims):
            Dm[i] = pr.dist(x, y, z) + pr.bias
        mid = np.argmin(Dm, axis=0)
        del Dm
        cols = np.array([pr.col for pr in prims], F)
        alb = cols[mid].copy()
        spec = np.array([pr.spec for pr in prims], F)[mid]
        shin = np.array([pr.shin for pr in prims], F)[mid]
        emit = np.array([pr.emit for pr in prims], F)[mid]
        for i, pr in enumerate(prims):
            if pr.tex is not None:
                sel = mid == i
                if sel.any():
                    alb[sel] = pr.tex(x[sel], y[sel], z[sel], alb[sel])
        # AO
        ao = np.zeros(hi_idx.size, F); wgt = 1.0
        for hh_ in (0.05, 0.12, 0.22, 0.38):
            dd = scene_dist(prims, x + nx * hh_, y + ny * hh_, z + nz * hh_, clip)
            ao += wgt * np.clip(hh_ - dd, 0, None) / hh_
            wgt *= 0.62
        ao = np.clip(1.0 - 0.55 * ao, 0.25, 1.0)
        # bayangan lembut
        ro = (x + nx * 0.03, y + ny * 0.03, z + nz * 0.03)
        vis = np.ones(hi_idx.size, F); tt = np.full(hi_idx.size, 0.04, F)
        for _ in range(22):
            dd = scene_dist(prims, ro[0] + Lm[0] * tt, ro[1] + Lm[1] * tt, ro[2] + Lm[2] * tt, clip)
            vis = np.minimum(vis, np.clip(7.0 * dd / tt, 0, 1))
            tt = tt + np.clip(dd, 0.03, 0.45)
        vis = vis * vis * (3 - 2 * vis)
        ndl = nx * Lm[0] + ny * Lm[1] + nz * Lm[2]
        diff = np.clip((ndl + 0.22) / 1.22, 0, 1)
        diff = diff * diff * (3 - 2 * diff) * 0.55 + np.clip(ndl, 0, 1) * 0.45
        hemi = np.clip(0.5 + 0.5 * ny, 0, 1)[:, None]
        amb = (F(Lc['ground']) * (1 - hemi) + F(Lc['sky']) * hemi) * Lc['amb_i']
        keyc = F(Lc['key']) * Lc['key_i']
        # bayangan: agak biru-ungu
        shade_tint = F([0.86, 0.9, 1.08])
        direct = keyc * (diff * vis)[:, None]
        base = alb * (amb * ao[:, None] * (1 + (1 - vis)[:, None] * 0.0) + direct)
        base = base * (1.0 - (1 - vis)[:, None] * (1 - shade_tint) * 0.6 * np.clip(1 - diff, 0, 1)[:, None] * 0)
        Hv = Lm + Vm; Hv = Hv / np.linalg.norm(Hv)
        ndh = np.clip(nx * Hv[0] + ny * Hv[1] + nz * Hv[2], 0, 1)
        sp = (ndh ** shin) * spec * vis
        ndv = np.clip(nx * Vm[0] + ny * Vm[1] + nz * Vm[2], 0, 1)
        fres = (1 - ndv) ** 3
        rimv = F(Lc['rim']) * (Lc['rim_i'] * fres * (0.4 + 0.6 * ao))[:, None]
        # cahaya langit dari atas lembut
        colr = base + keyc * sp[:, None] + rimv * alb * 1.2 + rimv * 0.25
        colr = colr + alb * emit[:, None]
        rgb[hi_idx] = colr
        alpha[hi_idx] = 1.0
        depth[hi_idx] = t

    # bayangan tanah (shadow catcher)
    if ground_shadow:
        miss = ~hitm
        if abs(dy) > 1e-6:
            tg = -Oy / dy
            gx = Ox + dx * tg; gz = Oz + dz * tg
            m_ = miss & (tg > 0) & (gx > x0 - shadow_margin) & (gx < x1 + shadow_margin) & (gz > z0 - shadow_margin) & (gz < z1 + shadow_margin)
            gi = np.nonzero(m_)[0]
            if gi.size:
                px = gx[gi]; pz = gz[gi]; py = np.full(gi.size, 0.004, F)
                dd0 = scene_dist(prims, px, py + 0.0, pz, False)
                # kontak
                occ = np.clip(1.0 - dd0 / 0.55, 0, 1) ** 2
                vis = np.ones(gi.size, F); tt = np.full(gi.size, 0.05, F)
                for _ in range(26):
                    dd = scene_dist(prims, px + Lm[0] * tt, py + Lm[1] * tt, pz + Lm[2] * tt, False)
                    vis = np.minimum(vis, np.clip(6.0 * dd / tt, 0, 1))
                    tt = tt + np.clip(dd, 0.04, 0.5)
                a = np.clip((1 - vis) * shadow_strength + occ * contact, 0, 0.78)
                a = a * (a > 0.004)
                rgb[gi] = F(shadow_col)
                alpha[gi] = a.astype(F)

    # pudarkan bayangan dekat tepi sel agar tidak terpotong keras
    if edge_fade and edge_fade > 0:
        px_ = (np.arange(Wl) + 0.5) / ss; py_ = (np.arange(Hl) + 0.5) / ss
        ex = np.minimum(px_, W - px_)[None, :]; ey = np.minimum(py_, H - py_)[:, None]
        ef = np.clip(np.minimum(ex, ey) / edge_fade, 0, 1); ef = (ef * ef * (3 - 2 * ef)).astype(F).ravel()
        shadow_only = alpha > 0
        shadow_only &= ~hitm
        alpha = np.where(shadow_only, alpha * ef, alpha)
    # kontur & lipatan
    rgb = rgb.reshape(Hl, Wl, 3); alpha = alpha.reshape(Hl, Wl); depth = depth.reshape(Hl, Wl)
    objm = (depth < 900)
    if crease:
        dd = depth.copy(); dd[~objm] = 0
        gxd = np.abs(np.roll(dd, -1, 1) - np.roll(dd, 1, 1)); gyd = np.abs(np.roll(dd, -1, 0) - np.roll(dd, 1, 0))
        jump = (np.maximum(gxd, gyd) > 0.10) & objm & np.roll(objm, 1, 0) & np.roll(objm, 1, 1) & np.roll(objm, -1, 0) & np.roll(objm, -1, 1)
        if jump.any():
            kk = max(1, int(round(ss * 0.55)))
            jm = cv2.dilate(jump.astype(np.uint8), np.ones((kk, kk), np.uint8)) > 0
            jm &= objm
            oc = hexc(outline_col)
            rgb[jm] = rgb[jm] * 0.45 + oc * 0.55
    if outline and outline > 0:
        rad = max(1, int(round(outline * ss * 0.5)))
        ker = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * rad + 1, 2 * rad + 1))
        dil = cv2.dilate(objm.astype(np.uint8), ker) > 0
        ring = dil & ~objm
        oc = hexc(outline_col)
        rgb[ring] = oc
        alpha[ring] = 1.0

    # grade ringan
    if grade:
        rgb = np.clip(rgb, 0, 1.6)
        rgb = rgb / (1 + 0.22 * np.maximum(rgb - 0.75, 0))
        lum = (rgb * F([0.3, 0.59, 0.11])).sum(-1, keepdims=True)
        rgb = lum + (rgb - lum) * 1.10
        rgb = np.clip(rgb, 0, 1)

    pm = np.dstack([rgb * alpha[..., None], alpha]).astype(F)
    if ss > 1:
        pm = cv2.resize(pm, (W, H), interpolation=cv2.INTER_AREA)
    a = pm[..., 3:4]
    out = np.where(a > 1e-4, pm[..., :3] / np.maximum(a, 1e-4), 0)
    res = np.dstack([np.clip(out, 0, 1), np.clip(a, 0, 1)])
    return (res * 255 + 0.5).astype(np.uint8)


def save_png(arr, path):
    from PIL import Image
    Image.fromarray(arr, 'RGBA' if arr.shape[2] == 4 else 'RGB').save(path, optimize=True)
