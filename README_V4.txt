ECOQUEST: Petualangan Desa Hijau — v4 (aset 3D + layar penuh)

PERUBAHAN
- Semua PNG di asset/ dirender ulang sebagai gambar 3D (karakter, NPC, tanaman, ikon energi,
  tileset, cover). Ukuran dan tata letak grid sama persis dengan v3, jadi kode game tidak berubah.
- Tombol Layar Penuh (pojok kanan atas) + tombol keyboard F. Panggung 1280x720 otomatis
  diskalakan ulang. iPhone Safari tidak punya Fullscreen API: muncul petunjuk "Tambah ke Layar Utama".

MEMBUAT ULANG ASET (butuh Python 3 + numpy + scipy + opencv-python + pillow)
  python3 tools/gen_assets3d.py            # semua
  python3 tools/gen_assets3d.py chars      # char_bima, char_piko, npc_*
  python3 tools/gen_assets3d.py crops eco  # tanaman, ikon energi
  python3 tools/gen_assets3d.py tiles      # tileset_village
  python3 tools/gen_assets3d.py cover      # cover_bg (render terrain, beberapa menit)
Semua render memakai mesin tools/render3d.py (raymarching SDF murni numpy, tanpa Blender).
Skrip 2D lama disimpan sebagai tools/*_2d_legacy.py.

CATATAN
- Cover dan karakter 3D di layar cover (three.js) tidak diubah.
- index.html belum diuji di browser; hanya sintaks JavaScript yang dicek.

MISI UTAMA & PERMAINAN SELESAI (pembaruan)
- Tujuan akhir jelas: (1) pasang 3 teknologi hijau, (2) selesaikan 6 pesanan warga,
  (3) jawab benar 8 tantangan IPAS, (4) panen 4 jenis tanaman (tomat, jagung, kentang, padi).
- Progres tampil di: chip HUD "Misi Utama x/4", kartu di panel kanan, dan bagian atas Pos Misi Pak Surya.
- Saat keempat tugas tuntas, permainan selesai dan muncul pop up pencapaian: bintang (3 jika tuntas
  paling lambat Hari 10), statistik, lencana, dan tombol Simpan Kartu Pencapaian (PNG), Main Lagi, Menu Utama.
- Pop up menunggu sampai soal/modal yang sedang terbuka ditutup. Save yang sudah tamat menampilkan
  pop up lagi saat dibuka. Save lama tetap bisa dipakai (hitungan pesanan dimulai dari 0).
- Setelah Hari 10, game tidak lagi menyatakan menang/kalah; hanya mengingatkan misi masih berlanjut.

--- v5: Kunci rasio 16:9 ---
Seluruh game berjalan di panggung tetap 1280x720 yang diskalakan ke layar (letterbox).
Tidak ada scroll di layar game maupun pop up; pop up yang terlalu tinggi otomatis diskalakan.
Editor bank soal berhalaman, dokumen aset berupa tab. Kode: blok #stage-fit-css / #stage-fit-js di index.html.
