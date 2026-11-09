# Daun Katuk v2 — desain (struktur retensi, style brief, rundown, suara)

60 detik, 9:16 (1080×1920, 30 fps). Bang Motion (HTML + GSAP, rig kamera kolase, render = fungsi murni dari
`tl.time()`) + video-shotcraft (kartu shot, pustaka audio, aturan estetika S1–S5).

## Masalah v1 → prinsip v2

Masukan: *"lumayan tapi membosankan kalau hanya fakta… pembawaan suaranya datar… intonasi ditinggikan
setiap mau sampai fakta unik, biar penonton betah"* (acuan: gaya Kok Bisa?).

1. **Setiap fakta dibungkus pertanyaan dulu** — penonton menebak sebelum diberi tahu (kuis, "lebih tinggi dari…").
2. **Jeda sebelum fakta** — suara naik ("Jawabannya…", "dari…", "Hasilnya?") lalu diam sebentar; gambar ikut
   menahan (rolet, dorong kamera ke batang "???", detak jantung), baru fakta dihantam (crash zoom + impact).
3. **Ada utang cerita** — open loop di detik 14 ("satu hal yang wajib kamu tahu…" + kartu "?! di akhir video!") dibayar di twist.
4. **Wajah yang bereaksi** — maskot Si Katuk menunjukkan emosi yang diharapkan dari penonton (kaget, tertawa, serius).
5. **Peta kemajuan** — progress bar 4 hijau + 1 merah (segmen merah terlihat sejak manfaat pertama): penonton tahu masih ada "yang merah" di akhir.
6. **Penutup memanggil pembuka** — "yang masih pilih jeruk!" menutup lingkaran kuis (dorongan berbagi & menonton ulang).

## Suara (VO)

ElevenLabs `eleven_v3`, suara "Liam" (dipilih user setelah uji beberapa suara Edge & ElevenLabs), `language_code: id`,
stability 0,5. Intonasi diarahkan dengan tag di `episode.json`: `[curious]` untuk pertanyaan, `[excited]` saat jawaban,
`[whispers]` untuk open loop, `[surprised]`/`[laughs]` untuk "susu sapi! — Iya, susu!", `[serious]`/`[dramatically]`
untuk twist, `[playful]` untuk CTA. `vo_edit.py`: jeda antarfrase dibatasi 0,24 dtk kecuali jeda tegang yang disengaja
(0,42–0,48 dtk setelah "Jawabannya…", "dari…", "Hasilnya?"), potongan hanya di titik sunyi (RMS 10 ms), tempo 1,17×
(rubberband, transien terjaga) supaya 9 adegan muat 60 dtk. Demi durasi, tiga potong frasa dibuang dari audio:
"nanti di akhir." (janjinya dipindah ke kartu "di akhir video!"), "Bagus buat mata!" (judul adegan sudah "Mata"), dan "Nah," di awal twist.

## Style brief

- **Rasa**: buku catatan dapur/herbarium yang jenaka — kertas krem, spesimen daun, kartu kuis bergaris tebal,
  stiker, selotip; satu karakter daun.
- **Palet**: kertas `#F2E8D3`, tinta `#1E2A22`, daun `#2F5D3A`/`#7DAF4B`, spidol kuning `#F3C64E` (sorotan,
  starburst), jeruk `#EE7A2B`, merah peringatan `#E5533D`, halaman gelap twist `#1F3D2B`.
- **Tipografi**: Fraunces (judul), Plus Jakarta Sans 800 (angka, subtitle 70 px), Kalam (tulisan tangan).
- **Subtitle**: kotak gelap di y≈1488 (di atas zona UI platform), lebar maks. 840 px berpusat di x=520 (bebas dari
  tombol kanan TikTok/Reels), kata aktif kuning, muncul 120 ms sebelum kata pertamanya; halaman berikutnya langsung
  mengganti teks di kotak yang sama (tanpa kedip, tanpa tumpang tindih).
- **Zona aman**: bagian bawah ±20 % dikosongkan untuk keterangan/tombol TikTok-Reels-Shorts.

## Rundown (detik)

| Waktu | Adegan | Gambar & gerak | Suara |
|---|---|---|---|
| 0,0–3,3 | **Kuis (hook)** | Kartu A jeruk & B "daun ini" sudah ada sejak frame 0 (sampul) lalu menepuk masuk, stiker KUIS!, judul "Siapa juara vitamin C?", maskot berpikir | "Jeruk… atau daun ini? Mana yang vitamin C-nya lebih banyak?" + musik penuh |
| 3,3–4,55 | Hitung mundur | Cincin VS → 3-2-1, kartu bergetar, maskot gugup | musik berhenti; satu tik jam tepat di tiap angka |
| 4,6–6,25 | Rolet | Sorotan kuning lompat A↔B, makin lambat, berhenti di B; pupil maskot mengikuti | "Jawabannya…" + klik saklar bergantian, sapuan cahaya naik |
| 6,25–9,8 | **Reveal** | B membesar, A memudar abu-abu, konfeti daun, stempel MENANG!, crash zoom #1, 49 mg vs 164 mg ("daun segar, per 100 g"), starburst + riso "3x" | "DAUN INI! Vitamin C-nya 3x lipat jeruk!" + impact, tepuk tangan, musik masuk di ketukan |
| 9,8–17,1 | Kenalan + open loop | Kamera menembus kartu B; tangkai membuka daun, foto spesimen ditempel selotip; "dicuekin" → abu-abu, wortel & bayam "si populer"; chip gizi; layar meredup + kartu "?! di akhir video!" | "Kenalin, daun katuk… Tapi ada satu hal yang wajib kamu tahu…" (berbisik) |
| 17,1–26,5 | Manfaat 1: ASI | Daun #1 terbang jadi lencana, progress bar muncul; kamera mendekat ke ibu & bayi; resep nenek + dorongan kamera pelan; jurnal + grafik naik + catatan "masih diteliti" | "Pertama: sahabat ibu menyusui!…" |
| 26,5–32,5 | Manfaat 2: kalsium | Menyelam lewat tetes ASI; gigi & tulang; batang arsir katuk vs "???"; kamera mendorong ke "???" saat jeda; crash zoom #2 → "Susu sapi segar", gelas susu; maskot tertawa | "kalsiumnya lebih tinggi dari… susu sapi! Iya, susu!" |
| 32,5–36,3 | Manfaat 3: mata | Whip turun; pena menggambar mata (draw-svg-trace), kedip; kamera mundur, daun ≈ wortel | "Ketiga: karotenoidnya hampir nyamain wortel." |
| 36,3–41,9 | Manfaat 4: zat besi | Tile Fe; bayam = katuk; bayam layu, katuk membesar, stiker "cadangan ✓"; maskot mengedip | "zat besinya setara bayam… nih, cadangannya!" |
| 41,9–54,1 | **Twist** | Goresan piringan: layar membeku abu-abu, kilat merah, crash zoom #3; tetes tinta merembes jadi halaman gelap; kliping koran "Taiwan 1990-an" (dilingkari merah di "Taiwan", stabilo di "jus daun katuk mentah", kamera merayap mendekat), kamera berdenyut di detak jantung; paru-paru + stempel BAHAYA!; kliping keluar, kamera turun: panci ✓ "masak dulu (direbus: vit C 66 mg)" vs jus mentah ✗ | jeda 0,38 dtk, lalu "ini yang wajib kamu tahu…"; musik jadi versi break teredam; detak jantung setelah "Hasilnya?" |
| 54,1–60,0 | CTA | Daun raksasa melintas lensa; 4 daun bernomor kembali ke tangkai; "Daun katuk" + spidol; tagline; "kirim ke temanmu" + jeruk membesar; sumber & kredit | "Murah, gampang ditanam, kaya manfaat! Kirim video ini ke temanmu yang masih pilih jeruk!" + akor penutup lagu di 59,38 dtk |

## Kartu shot (video-shotcraft) yang dipakai

riso-print-hits (misregistration "3x"), paper-craft-moves (masking-tape-slap foto spesimen), marker-underline-title
(ASI, Kalsium, katuk), hatch-depth (batang arsir → padat), draw-svg-trace (mata), print-texture-transitions
(ink-bleed-reveal ke halaman gelap), line-boil (judul penutup). Baru di v2: kartu kuis + rolet sorotan, starburst,
konfeti daun deterministik, maskot dengan IK dua ruas & lip-sync dari amplop suara, progress bar.

## Rencana suara

- **Musik**: "Kids" (171,8 BPM), −24 LUFS saat tidak ada suara, turun 10 dB di bawah suara (tahan 0,45 dtk antarkata,
  lepas 0,5 dtk) kecuali 0,5–0,7 dtk "drop" di reveal dan CTA. Video ketukan 0 = bar 8 lagu; semua cut adegan jatuh di ketukan. Musik keluar saat
  hitung mundur (3,30 dtk), masuk lagi dari bar 8 di ketukan pertama setelah "DAUN" (6,287 dtk) sehingga grid ketukan
  tetap sama; berhenti dengan goresan piringan di twist; bagian break di-low-pass (700 Hz) di bawah cerita Taiwan;
  segmen penutup ditempatkan agar akor terakhir jatuh di ketukan setelah kata terakhir. Ducking −8 dB di bawah suara.
- **SFX**: 95 pin dalam satu tabel (`sfxTable()` di `index.html` → `sfx.json`), tiap pin dihitung dari waktu kata
  dan diberi catatan aksinya (S2). Bunyi perkusif disejajarkan di puncaknya (S5: berkas punya jeda 50–900 ms
  dari awal ke puncak). Klik rolet memakai dua sampel saklar asli bergantian dengan volume naik saat melambat (S1/S2).
- **Level**: VO −16 LUFS, musik ±−34 LUFS di bawah suara (median suara 16 dB di atas musik), SFX dinormalisasi puncak;
  master −14 LUFS / −1,5 dBTP. Tik hitung mundur = satu transien yang dipotong dari berkasnya (berkas aslinya rentetan tik).
  Dua versi dari timeline yang sama: dengan musik dan tanpa musik (A8).
