# Daun Katuk — desain video (style brief + rundown)

Konten edukasi 60 detik, 9:16 (1080×1920, 30 fps), voice-over + subtitle bahasa Indonesia,
hook di 3 detik pertama. Dibangun dengan **Bang Motion** (HTML + GSAP, rig kamera kolase,
hukum anti-PPT) dan **video-shotcraft** (kartu shot, aset audio, aturan estetika, review
independen). Mode video-shotcraft: *autonomous free creation* — keputusan dicatat di sini.

## Brief → keputusan

| Kebutuhan | Keputusan |
|---|---|
| Topik | Manfaat daun katuk (*Sauropus androgynus*), fakta bersumber |
| Durasi | 60,0 dtk = 122 ketukan BGM (122 BPM) |
| Hook ≤ 3 dtk | "Daun ini, vitamin C-nya tiga kali lipat jeruk!" — selesai di 2,78 dtk; cut ke adegan 2 di 2,95 dtk |
| Rasio | 9:16 (konten Reels/TikTok/Shorts — "hook 3 detik" = format pendek vertikal) |
| Suara | VO TTS neural `id-ID-ArdiNeural` (+5%) — Gadis terlalu lambat untuk hook ≤ 3 dtk |
| Subtitle | Bahasa Indonesia, per kata (kata aktif menyala), angka ditulis digit (164 mg, 233 mg) |
| Musik | `house-vibez.mp3` (video-shotcraft, Mixkit free license), di-edit di batas bar: breakdown di bawah segmen "Tapi ingat", drop kembali tepat di CTA |
| Fakta | Data Komposisi Pangan Indonesia (Kemenkes RI), per 100 g — lihat README |
| Keamanan | Peringatan: masak dulu, jangan terlalu lama; hindari jus mentah berlebihan |

## Style brief (Bang Motion Hukum #3)

- **Tema & rasa**: buku catatan dapur/herbarium — *segar, hangat, bisa dipercaya*.
- **Konsep** (3 kandidat): (1) **herbarium dapur kolase** — kertas krem, spesimen daun,
  catatan tangan, pembanding ditempel ← *dipilih*: topik pangan/edukasi, butuh bukti
  (foto spesimen, angka resmi) dan pembanding benda sehari-hari; (2) timbangan gizi aksi
  kontinu (katuk vs jeruk/susu/wortel di satu timbangan) — kuat tapi monoton untuk 5 manfaat;
  (3) kartun panggung ibu di dapur — tanpa caption, bertentangan dengan permintaan subtitle.
- **Sidik jari struktur**: kolase kertas · 9 adegan · objek utama tiap adegan = katuk + satu
  pembanding (jeruk, susu, wortel, bayam) · pembuka close-up daun + "3×" cetak riso ·
  penutup daun-daun bernomor kembali ke tangkai.
- **Palet** (tanpa brand → dari subjek):
  `--leaf #2F5D3A` (hijau tua daun katuk, dari foto) · `--leaf-lit #7DAF4B` (pucuk muda) ·
  `--paper #F2E8D3` (turunan: kertas buku catatan) · `--ink #1E2A22` (tinta hijau-hitam) ·
  aksen `--orange #EE7A2B` (jeruk, pembanding vitamin C) · `--maroon #8E2B36` (bunga katuk,
  untuk peringatan) · `--marker #F3C64E` (stabilo).
- **Font**: display **Fraunces** (serif lembut berkarakter), subtitle/label **Plus Jakarta Sans**
  (font buatan Indonesia), catatan tangan **Kalam**. Bukan font starter (Bricolage/Caveat).
- **Penekanan**: satu bentuk — `marker` (coretan stabilo miring, kartu *marker-underline-title*).
- **Tanda tangan gerak**: daun lepas dari tangkai → melayang berputar → mendarat jadi lencana
  bernomor manfaat.
- **Gerak latar** (§7c #4): butiran kertas hidup (offset dari t, 12×/dtk) + kamera bernapas +
  cahaya hangat bergeser pelan.
- **Permukaan latar** (§7d f): kertas krem + garis buku tipis + butiran multiply + cahaya radial.
- **Latar per segmen**: krem sepanjang video; segmen "Tapi ingat" pindah ke halaman hijau tua
  (pemicu: tinta merembes, kartu *ink-bleed-reveal*); kembali krem di CTA (pemicu: daun besar
  melewati lensa).
- **Gaya render objek** (§7e): flat solid + garis tinta ber-offset ala cetak riso, satu keluarga.
- **Foto**: satu foto spesimen asli (Forest & Kim Starr, CC BY 3.0), kredit di layar.
- **Transisi**: tarik mundur (S1→2), whip mengikuti daun (2→3), tembus tetes ASI (3→4),
  whip turun (4→5), koreografi beririsan (5→6), rack focus (6→7), tinta merembes (7→8),
  daun melewati lensa (8→9).
- **Momen istimewa**: penutup — lima daun bernomor terbang kembali menyusun tangkai, tepat di drop musik.

## Kartu shot video-shotcraft yang dipakai (sekali sebagai pemeran utama)

| Kartu · gaya | Dipakai di | Parameter kunci yang dipertahankan |
|---|---|---|
| riso-print-hits · misregistration-hit | S1 "3×" | masuk 8f ease-in, pelat pecah di frame tabrakan, A=(16,7)px, ω=2π/18, τ=60, snap keras + pulse 1,03 4f |
| paper-title-card | S2 "Daun katuk" | per kata scale 1,28→1 + blur 7→0, 9f, jeda 4f, satu kata aksen italik, garis 16→34f |
| paper-craft-moves · masking-tape-slap | S2 foto spesimen | goyang ±1,5°/±5px, selotip 6f scale 1,45→1, rot −16°→+7°→0, squash 0,72; tempelan ke-2 = mati (shadow 34→8) |
| marker-underline-title | kata kunci tiap judul | stroke 10f ease-out, naik kiri-rendah→kanan-tinggi, lebar tengah, tepi kasar, mulai +4~8f setelah judul |
| odometer-digit-roll | S4 "164" | strip 0–9, laju 0,85 baris/f, digit i mulai lambat 20+7i f, 16f out-cubic ke +0,5, 6f balik, 2 bayangan 0,25/0,12, pulse 1,035 |
| hatch-depth | S5 kalsium vs susu | batang arsir 45° tumbuh out-cubic, morph silang 0,14·dur, geometri sama, getar ±2% |
| draw-svg-trace | S6 mata | pena (dash 0,045, 7px) di depan garis, 40f in-out cubic, kilat tutup 2f + 6f, isi muncul 8f |
| print-texture-transitions · ink-bleed-reveal | S7→S8 | mask lingkaran + feTurbulence(0,02, 3 oktaf, seed tetap) + displacement 60→160, wobble ±8% |
| line-boil | hold judul akhir | feTurbulence 0,015, displacement 8, seed = floor(f/3), filter dilepas di luar segmen |

## Rundown (detik video; cut = ketukan musik)

| # | Waktu | Kalimat VO | Visual |
|---|---|---|---|
| 1 | 0,00–2,95 | Daun ini, vitamin C-nya tiga kali lipat jeruk! | close-up tangkai katuk; irisan jeruk; "3×" dihantam cetak riso di ketukan 4 |
| 2 | 2,95–10,33 | Ini daun katuk. Murah, gampang ditanam, gizinya luar biasa. Apa saja manfaatnya? | tarik mundur ke halaman; judul ditekan; foto spesimen ditempel selotip; stempel "kaya gizi"; 5 daun diberi nomor |
| 3 | 10,33–17,70 | Pertama, pelancar ASI. Turun-temurun… penelitian hasilnya menjanjikan. | daun 1 mendarat; ibu & bayi; kartu resep turun-temurun; kartu jurnal + garis naik |
| 4 | 17,70–25,08 | Kedua, daya tahan tubuh. Vitamin C-nya 164 mg, jeruk manis cuma 49. | tembus tetes; odometer 164 mg; jeruk 49 mg kecil di sampingnya |
| 5 | 25,08–32,46 | Ketiga, tulang dan gigi. Kalsiumnya 233 mg, lebih tinggi dari susu sapi segar. | tulang & gigi; batang arsir → padat: katuk 233 vs susu 143 |
| 6 | 32,46–37,87 | Keempat, kesehatan mata. Karotenoidnya hampir menyamai wortel. | mata digambar pena; daun ≈ wortel |
| 7 | 37,87–43,28 | Kelima, zat besinya setara bayam, penting untuk membentuk sel darah merah. | tile Fe; katuk = bayam; sel darah merah berlipat |
| 8 | 43,28–51,15 | Tapi ingat, masak dulu, jangan terlalu lama… Hindari jus daun katuk mentah berlebihan. | halaman hijau tua; panci berasap ✓; timer; jus mentah ✗ |
| 9 | 51,15–60,00 | Murah, mudah ditanam, kaya manfaat. Simpan video ini, dan bagikan ke orang tersayang! | daun kembali ke tangkai; judul + tagline; ikon simpan & bagikan; sumber + disclaimer; hold ≥ 1 dtk |
