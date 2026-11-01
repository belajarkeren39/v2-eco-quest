#!/usr/bin/env python3
"""
gen_assets3d.py — membuat ulang SEMUA aset PNG (v4) sebagai render 3D.

  python3 tools/gen_assets3d.py            # semua aset
  python3 tools/gen_assets3d.py chars      # hanya karakter  (char_bima, char_piko, npc_*)
  python3 tools/gen_assets3d.py crops eco  # tanaman & ikon energi
  python3 tools/gen_assets3d.py tiles      # tileset_village
  python3 tools/gen_assets3d.py cover      # cover_bg (butuh aset lain sudah ada)

Tata letak sprite sheet sama persis dengan v2/v3, sehingga kode game tidak berubah.
Mesin: tools/render3d.py (raymarching SDF, numpy). Tanpa dependensi 3D eksternal.
"""
import os
import sys
import time
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
OUT = os.path.join(HERE, '..', 'asset')
os.makedirs(OUT, exist_ok=True)

from render3d import render, save_png  # noqa: E402


def paste(sheet, arr, x, y):
    sheet.alpha_composite(Image.fromarray(arr, 'RGBA'), (x, y))


def log(m):
    print(f'[{time.strftime("%H:%M:%S")}] {m}', flush=True)


def gen_chars():
    import chars3d as c
    kw = dict(elev=c.ELEV, ss=3, bounds=c.CH_B, outline=1.5, light=dict(L=(-0.42, 0.62, 0.66), amb_i=0.54, key_i=0.78))
    # Bima: 4 baris arah (bawah, atas, kiri, kanan) x 4 frame jalan
    sheet = Image.new('RGBA', (512, 512), (0, 0, 0, 0))
    for row, yaw in enumerate((0, 180, -90, 90)):
        for f in range(4):
            paste(sheet, render(c.bima(f), 128, 128, 31, 64, 114, yaw=yaw, **kw), f * 128, row * 128)
    save_png(np.array(sheet), f'{OUT}/char_bima.png'); log('char_bima.png')
    # Piko 2x2 (menghadap kiri)
    sheet = Image.new('RGBA', (256, 256), (0, 0, 0, 0))
    for k in range(4):
        paste(sheet, render(c.piko(k), 128, 128, 36, 64, 112, **kw), (k % 2) * 128, (k // 2) * 128)
    save_png(np.array(sheet), f'{OUT}/char_piko.png'); log('char_piko.png')
    # NPC
    for name, fn, S_ in (('npc_ratna', c.ratna, 28), ('npc_surya', c.surya, 30)):
        sheet = Image.new('RGBA', (256, 128), (0, 0, 0, 0))
        for f in range(2):
            paste(sheet, render(fn(f), 128, 128, S_, 64, 110, **kw), f * 128, 0)
        save_png(np.array(sheet), f'{OUT}/{name}.png'); log(name + '.png')


def gen_crops():
    import crops3d as c
    sheet = Image.new('RGBA', (512, 512), (0, 0, 0, 0))
    for r, fn in enumerate(c.CROPS):
        for st in range(4):
            paste(sheet, render(fn(st), 128, 128, 38, 64, 112, elev=c.ELEV, ss=3, bounds=((-2.0, 2.0), (0, 4.4), (-2.0, 2.0)), outline=1.4), st * 128, r * 128)
    save_png(np.array(sheet), f'{OUT}/crops_stages.png'); log('crops_stages.png')


def gen_eco():
    import crops3d as c
    sheet = Image.new('RGBA', (384, 128), (0, 0, 0, 0))
    for i, fn in enumerate((c.solar_pump, c.biogas, c.hydro)):
        paste(sheet, render(fn(), 128, 128, 31, 64, 112, elev=c.ELEV, ss=3, bounds=((-2.2, 2.2), (0, 3.2), (-1.6, 1.6)), outline=1.4), i * 128, 0)
    save_png(np.array(sheet), f'{OUT}/eco_tech_icons.png'); log('eco_tech_icons.png')


def gen_tiles():
    import world3d as w
    sheet = Image.new('RGBA', (1024, 1024), (0, 0, 0, 0))
    for k in range(3):
        paste(sheet, w.render_soil(k), k * 256, 0)
    paste(sheet, w.tile_grass(), 3 * 256, 0)
    log('tanah & rumput')
    obj = lambda P, S_, oy=226, bounds=w.CB, **k: render(P, 256, 256, S_, 128, oy, elev=w.ELEV, ss=2, bounds=bounds, outline=2.2, **k)
    paste(sheet, obj(w.house(), 60, oy=198), 0 * 256, 256)
    paste(sheet, obj(w.shop(), 62, oy=186), 1 * 256, 256)
    paste(sheet, obj(w.station(), 54, oy=202), 2 * 256, 256)
    paste(sheet, obj(w.well(), 62, oy=202, bounds=((-2.3, 2.3), (0, 3.2), (-2.0, 2.0))), 3 * 256, 256)
    log('bangunan')
    paste(sheet, obj(w.tree(), 54, bounds=((-2.4, 2.4), (0, 4.4), (-2.4, 2.4))), 0, 512)
    paste(sheet, obj(w.bush(), 80, oy=214, bounds=((-1.9, 1.9), (0, 2.0), (-1.7, 1.7))), 256, 512)
    paste(sheet, obj(w.flowers(), 92, oy=216, bounds=((-1.5, 1.5), (0, 2.4), (-1.5, 1.5))), 512, 512)
    paste(sheet, obj(w.rocks(), 92, oy=214, bounds=((-1.7, 1.7), (0, 1.6), (-1.5, 1.5))), 768, 512)
    log('dekorasi')
    paste(sheet, w.tile_path(), 0, 768)
    paste(sheet, w.tile_water(), 256, 768)
    paste(sheet, obj(w.fence(), 85, oy=190, bounds=((-1.6, 1.6), (0, 1.6), (-.7, .7)), edge_fade=0, shadow_margin=1.0), 512, 768)
    paste(sheet, obj(w.sign(), 72, oy=222, bounds=((-1.6, 1.6), (0, 2.8), (-1.2, 1.2))), 768, 768)
    save_png(np.array(sheet), f'{OUT}/tileset_village.png'); log('tileset_village.png')


def gen_cover():
    import cover3d
    cover3d.make(f'{OUT}/cover_bg.png'); log('cover_bg.png')


JOBS = {'chars': gen_chars, 'crops': gen_crops, 'eco': gen_eco, 'tiles': gen_tiles, 'cover': gen_cover}

if __name__ == '__main__':
    todo = sys.argv[1:] or ['chars', 'crops', 'eco', 'tiles', 'cover']
    for j in todo:
        JOBS[j]()
    log('selesai')
