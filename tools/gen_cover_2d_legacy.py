#!/usr/bin/env python3
"""Cover 16:9 (1920x1080): desa tropis Nusantara saat golden hour. Jalankan: python3 tools/gen_cover.py"""
import numpy as np, math, random
from PIL import Image, ImageDraw, ImageFilter
W, H = 1920, 1080; random.seed(7); np.random.seed(7)
lerp = lambda a, b, t: tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))
y = np.linspace(0, 1, H)[:, None, None]; x = np.linspace(0, 1, W)[None, :, None]
stops = [(0, (22, 52, 110)), (.30, (70, 110, 170)), (.52, (255, 170, 110)), (.64, (255, 214, 140))]
sky = np.zeros((H, W, 3))
for (a, ca), (b, cb) in zip(stops, stops[1:] + [(1, stops[-1][1])]):
    m = ((y >= a) & (y < b)) if b < 1 else (y >= a)
    t = np.clip((y - a) / max(b - a, 1e-6), 0, 1); sky += m * (np.array(ca) * (1 - t) + np.array(cb) * t)
sx, sy = .70, .50                                           # matahari + cahaya
d = np.hypot((x - sx) * 1.78, y - sy)
sky += np.exp(-d * 5.5) * np.array([255, 190, 90]) * .55 + np.exp(-d * 22) * np.array([255, 240, 190]) * .9
img = Image.fromarray(np.clip(sky, 0, 255).astype("uint8")).convert("RGBA")

def layer(fn):
    l = Image.new("RGBA", (W, H), (0, 0, 0, 0)); fn(ImageDraw.Draw(l)); return l
def glow(r, col, a, blur):
    return layer(lambda g: g.ellipse([W * sx - r, H * sy - r, W * sx + r, H * sy + r], fill=col + (a,))).filter(ImageFilter.GaussianBlur(blur))

img.alpha_composite(glow(70, (255, 250, 220), 255, 4)); img.alpha_composite(glow(190, (255, 200, 120), 120, 60))
def rays(g):                                                # sinar matahari
    for i in range(14):
        a = math.radians(-170 + i * 14 + random.uniform(-3, 3)); s = random.uniform(.03, .07)
        g.polygon([(W * sx, H * sy)] + [(W * sx + math.cos(a + k) * 2600, H * sy + math.sin(a + k) * 2600) for k in (-s, s)], fill=(255, 220, 150, 26))
img.alpha_composite(layer(rays).filter(ImageFilter.GaussianBlur(8)))
def clouds(g):
    for _ in range(26):
        cx, cy = random.randint(-100, W), random.randint(40, 480); w = random.randint(220, 560)
        g.ellipse([cx, cy, cx + w, cy + w // 9], fill=(255, 205, 170, 95))
        g.ellipse([cx + w // 8, cy - 8, cx + w - w // 8, cy + w // 12], fill=(255, 235, 215, 70))
img.alpha_composite(layer(clouds).filter(ImageFilter.GaussianBlur(10)))

haze = (255, 190, 130)
def ridge(base, amp, col, hz, seed, fr=(1, 2.3, 5.1)):      # bukit berlapis + kabut udara
    rnd = random.Random(seed); ph = [rnd.uniform(0, 6.28) for _ in fr]; pts = []
    for px in range(0, W + 8, 8):
        yy = base + sum(amp / (i + 1) * math.sin(px / W * f * 6.28 + ph[i]) for i, f in enumerate(fr)); pts.append((px, yy))
    c = lerp(col, haze, hz); l = layer(lambda g: g.polygon(pts + [(W, H), (0, H)], fill=c + (255,))); img.alpha_composite(l); return pts

vx, vy = 330, 600                                           # gunung berapi jauh
img.alpha_composite(layer(lambda g: g.polygon([(vx - 420, 700), (vx - 40, vy), (vx + 40, vy), (vx + 480, 700)], fill=(120, 110, 150, 255))).filter(ImageFilter.GaussianBlur(2)))
ridge(640, 36, (90, 120, 120), .55, 1); ridge(700, 46, (60, 140, 90), .38, 2); mid = ridge(770, 50, (40, 150, 70), .22, 3)

def turbine(px, py, s, ang):                                # kincir angin
    def f(g):
        g.line([(px, py), (px, py - 150 * s)], fill=(250, 245, 240, 255), width=max(2, int(6 * s)))
        for k in range(3):
            a = math.radians(ang + k * 120); g.line([(px, py - 150 * s), (px + math.cos(a) * 80 * s, py - 150 * s + math.sin(a) * 80 * s)], fill=(255, 255, 255, 255), width=max(2, int(5 * s)))
    img.alpha_composite(layer(f))
for px, s, a in [(1180, .7, 12), (1330, .85, 50), (1500, 1, 80), (1700, .75, 30)]:
    turbine(px, np.interp(px, [p[0] for p in mid], [p[1] for p in mid]), s, a)

fg = ridge(850, 30, (30, 120, 50), .10, 4)                  # petak sawah berundak
def terraces(g):
    for i in range(14):
        pts = [(px, yy + 30 + i * 22 + i * i * .8) for px, yy in fg[::2]]; c = lerp((70, 170, 60), (200, 190, 70), i / 14)
        g.line(pts, fill=c + (255,), width=10 + i); g.line([(p[0], p[1] + 10 + i) for p in pts], fill=(70, 50, 30, 200), width=3)
img.alpha_composite(layer(terraces))
def hut(px, py, s):                                         # rumah kecil bercahaya
    def f(g):
        g.rectangle([px - 30 * s, py - 28 * s, px + 30 * s, py], fill=(250, 235, 200, 255)); g.polygon([(px - 40 * s, py - 28 * s), (px, py - 62 * s), (px + 40 * s, py - 28 * s)], fill=(185, 70, 45, 255))
        g.rectangle([px - 8 * s, py - 22 * s, px + 8 * s, py - 6 * s], fill=(255, 215, 90, 255))
    img.alpha_composite(layer(f))
for px, s in [(1020, .8), (1110, 1), (1560, .9), (1810, .7)]: hut(px, np.interp(px, [p[0] for p in fg], [p[1] for p in fg]) + 55, s)

def palm(px, base, h, lean, s):                             # pohon palem siluet
    def f(g):
        pts = [(px + lean * (t / 20) ** 2, base - h * t / 20) for t in range(21)]; g.line(pts, fill=(28, 40, 30, 255), width=int(22 * s))
        tx, ty = pts[-1]
        for k in range(9):
            a = math.radians(-190 + k * 25 + random.uniform(-6, 6)); L = 230 * s
            fr = [(tx + math.cos(a) * L * t / 10, ty + math.sin(a) * L * t / 10 + (t / 10) ** 2 * 110 * s) for t in range(11)]; g.line(fr, fill=(22, 60, 34, 255), width=int(14 * s))
    img.alpha_composite(layer(f))
palm(120, 1120, 760, 70, 1.25); palm(300, 1130, 560, -60, .9); palm(1850, 1120, 700, -80, 1.15)
shade = layer(lambda g: g.rectangle([0, 940, W, H], fill=(18, 40, 26, 255))).filter(ImageFilter.GaussianBlur(40)); img.alpha_composite(shade)
def bokeh(g):                                               # kunang-kunang & debu cahaya
    for _ in range(90):
        r = random.randint(3, 12); px, py = random.randint(0, W), random.randint(380, 1000); g.ellipse([px - r, py - r, px + r, py + r], fill=(255, 235, 150, random.randint(40, 130)))
img.alpha_composite(layer(bokeh).filter(ImageFilter.GaussianBlur(2.2)))
a = np.array(img.convert("RGB")).astype(float); v = np.hypot((np.linspace(0, 1, W)[None] - .5) * 1.1, (np.linspace(0, 1, H)[:, None] - .5)); a *= (1 - np.clip(v - .35, 0, 1) * .75)[..., None]
Image.fromarray(np.clip(a, 0, 255).astype("uint8")).save("asset/cover_bg.png", optimize=True); print("asset/cover_bg.png", W, H)
