# Manfaat Daun Katuk v2 — edutainment 60 detik (9:16)

Versi kedua dari `projects/daun-katuk`, dibuat ulang setelah masukan: *v1 membosankan kalau hanya fakta,
suaranya datar*. v2 tetap 60 detik, 1080×1920, subtitle per kata, tetapi disusun seperti video
edukasi-hiburan (gaya kanal sains populer): **kuis → hitung mundur → jawaban mengejutkan → open loop →
4 manfaat dengan progress bar → twist → CTA yang memanggil balik kuis**.

| Berkas | Isi |
|---|---|
| `out/daun-katuk-v2.mp4` | video final — subtitle Indonesia, VO + efek suara + musik |
| `out/daun-katuk-v2-tanpa-bgm.mp4` | sama, tanpa musik (VO + efek) — untuk musik dari platform |
| `out/daun-katuk-v2-en.mp4` | sama, subtitle **bahasa Inggris** (suara tetap Indonesia) |
| `out/daun-katuk-v2.id.srt`, `.en.srt` | subtitle terpisah (YouTube / editor video) |
| `episode.json` | **data episode**: naskah VO + tag emosi, teks EN per halaman, angka fakta, suara |
| `index.html` | sumber animasi — buka langsung (autoplay + loop); `?debug=1` scrub, `?lang=en` subtitle Inggris |
| `DESIGN.md` | struktur retensi, style brief, rundown per detik, rencana suara |

## Apa yang berubah dari v1

| v1 | v2 |
|---|---|
| Fakta dibacakan berurutan | Kuis "Jeruk… atau daun ini?" di detik 0–3, hitung mundur 3-2-1, sorotan rolet A/B yang melambat, jawaban "DAUN INI!" |
| Suara TTS datar (Edge) | ElevenLabs `eleven_v3` (suara "Liam") dengan tag emosi per kalimat: penasaran, berbisik, kaget, tertawa, serius |
| Tidak ada alasan menonton sampai akhir | *Open loop* di detik 14: "Tapi ada satu hal yang wajib kamu tahu…" + layar meredup + kartu "?! di akhir video!"; segmen ke-5 progress bar merah sejak awal |
| Tanpa karakter | Maskot "Si Katuk": berpindah posisi, berganti ekspresi & pose, mulut mengikuti suara |
| Manfaat 1–5 tanpa penanda | Progress bar 4 manfaat (hijau) + 1 peringatan (merah) di atas layar |
| Musik terus berjalan | Musik berhenti saat hitung mundur, masuk lagi tepat di "DAUN INI!"; goresan piringan menghentikan musik di twist |
| Penutup biasa | Callback: "Kirim ke temanmu yang masih pilih jeruk!" + jeruk kecil membesar |

## Fakta & sumber

Angka gizi per 100 g: **Data Komposisi Pangan Indonesia, Kementerian Kesehatan RI** (https://www.panganku.org) —
daun katuk segar vitamin C 164 mg, kalsium 233 mg, karotenoid total 10.020 µg, besi 3,0 mg; jeruk manis
vitamin C 49 mg (164/49 ≈ 3,3 → "3x lipat"); susu sapi segar kalsium 143 mg; wortel karotenoid total 11.046 µg;
bayam besi 3,0 mg; daun katuk **rebus** vitamin C 66 mg (masih di atas jeruk; ditampilkan di label "masak dulu").
Angka "3x" di layar diberi keterangan "daun segar, per 100 g". Rinciannya sama dengan v1 (`projects/daun-katuk/README.md`).

- **Pelancar ASI** — tradisi turun-temurun; bukti ilmiah menjanjikan tetapi belum seragam, sehingga naskah
  berbunyi "beberapa penelitian bilang, hasilnya menjanjikan" dan kartu jurnal diberi catatan "masih diteliti".
- **Twist (Taiwan 1990-an)** — tren diet jus daun katuk mentah dalam jumlah besar dikaitkan dengan
  *bronchiolitis obliterans* (gangguan paru serius): [Hospital Authority Hong Kong](https://www3.ha.org.hk/toxicplant/en/sauropus_androgynus.html),
  [ulasan di PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC4564651/). Pesan penutupnya: masak dulu, jangan berlebihan.
- Frame terakhir memuat sumber gizi + disclaimer "Edukasi umum, bukan pengganti saran tenaga kesehatan".

## Kredit & lisensi

- **Suara: ElevenLabs** (`eleven_v3`, suara premade "Liam"). Dibuat dengan akun gratis → **non-komersial dan wajib
  atribusi** (tertulis di frame penutup). Untuk konten yang dimonetisasi, buat ulang VO dengan paket berbayar:
  `python3 tools/tts_el.py` lalu jalankan ulang langkah di bawah.
- Musik "Kids" — Michael Ramir C. (Mixkit Stock Music Free License); 44 efek suara Mixkit dari pustaka
  video-shotcraft — daftar & URL per berkas di `assets/audio/ATTRIBUTION.md`.
- Foto daun katuk: Forest & Kim Starr, CC BY 3.0 (Wikimedia Commons), kredit tampil di layar.
- Ilustrasi & maskot: SVG di `index.html`. Font: Fraunces, Plus Jakarta Sans, Kalam (SIL OFL).

## Membangun ulang (data → video, tanpa langkah manual)

```
python3 tools/tts_el.py          # episode.json -> VO per adegan + waktu per karakter (ElevenLabs, butuh API key)
python3 tools/vo_edit.py         # rapikan jeda, potong di titik sunyi, tempo -> assets/vo/*.edit.wav + words.edit.json
python3 tools/layout.py          # cut adegan di ketukan musik, halaman subtitle ID+EN, amplop mulut -> timeline.json
python3 tools/inject.py          # timeline.json -> index.html
node tools/dump-sfx.mjs          # tabel pin SFX (dihitung halaman dari waktu kata) -> sfx.json
python3 tools/collect_sfx.py <video-shotcraft>/assets/audio   # salin SFX terpakai + ATTRIBUTION.md
python3 tools/mix.py             # VO + SFX + musik (edit di ketukan, ducking, -14 LUFS) -> build/mix*.wav
node tools/export.mjs            # render frame-demi-frame -> build/video.mp4
URL="file://$PWD/index.html?clean=1&lang=en" OUT=build-en node tools/export.mjs   # versi subtitle EN
bash tools/finalize.sh           # encode + mux -> out/*.mp4 + .srt
```

Butuh Python 3 (`numpy`), Node (`puppeteer`), ffmpeg dengan `rubberband`. Di mesin tanpa Chrome bawaan puppeteer,
set `PUPPETEER_EXECUTABLE_PATH`.

## Menuju database (tanpa AI)

Semua yang spesifik episode sudah berupa data di `episode.json` (teks ID/EN per halaman, tag emosi, angka fakta)
dan semua turunan waktunya dihitung skrip (cut, subtitle, pin SFX, mix). Yang masih ditulis tangan untuk episode
ini adalah **koreografi visual** di `index.html` (posisi ilustrasi, gerak kamera per kata). Agar episode baru bisa
dibangkitkan otomatis dari database, langkah berikutnya: jadikan tiap jenis adegan (`quiz`, `reveal`, `intro`,
`benefit`, `twist`, `cta`) templat berparameter (gambar, angka, label dari database), sehingga satu baris data =
satu video. TTS tetap memanggil layanan suara (ElevenLabs), tetapi tidak ada langkah yang butuh model bahasa.
