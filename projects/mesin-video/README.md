# Mesin video: database → video edukasi 9:16, otomatis

Satu baris episode di database (naskah + angka fakta + sumber) menjadi video pendek 9:16 lengkap:
suara ekspresif, subtitle per kata (Indonesia + Inggris), maskot yang bereaksi, efek suara, musik yang diedit di
ketukan, dan tiga berkas MP4 (subtitle ID, tanpa musik, subtitle EN). **Tidak ada langkah yang memakai model AI**
saat membuat video; hanya suara yang memanggil layanan TTS (ElevenLabs).

Contoh yang sudah jadi (dibangkitkan dari `db/data/episode/*.json`):

| Episode | Kategori | Durasi | Adegan |
|---|---|---|---|
| `mitos-air-es` — Minum air es bikin gendut? | Mitos vs Fakta | 44 dtk | kuis MITOS/FAKTA → jawaban + open loop → langkah (4 °C → 37 °C → ±16 kkal) → twist "pelakunya gula" → CTA |
| `gizi-tempe-telur` — Tempe vs telur | Makanan & Gizi | 46 dtk | kuis A/B → jawaban + angka → rantai "rahasia tempe" → banding "jebakan angka" per porsi → CTA |
| `sains-bawang` — Kenapa motong bawang bikin nangis? | Sains | 54 dtk | kuis 3 pilihan → jawaban → rantai 4 langkah kimia → tips → twist kejutan (Nature 2002) → CTA |

Hasil ada di `episodes/<id>/out/` (MP4 + SRT); `episodes/<id>/index.html` bisa dibuka langsung di browser
(`?debug=1` untuk menggeser waktu, `?lang=en` untuk subtitle Inggris).

## Cara pakai

```bash
npm install                          # puppeteer, gsap, ikon Fluent Emoji
python3 tools/db.py init             # buat db/konten.db dari db/schema.sql
python3 tools/db.py import           # isi dari db/data/*.json
python3 tools/db.py musik            # analisis BPM lagu baru (sekali per lagu)
python3 tools/db.py validate         # cek naskah, isyarat, ikon, jumlah halaman subtitle
python3 tools/make_video.py mitos-air-es          # satu perintah: database -> MP4
```

Butuh Python 3 (numpy; librosa untuk `db.py musik`), Node 18+, ffmpeg dengan filter `rubberband`, dan Chromium
(set `PUPPETEER_EXECUTABLE_PATH` bila puppeteer tidak membawa Chrome). Kunci ElevenLabs lewat variabel `XI_API_KEY`.

`make_video.py` menjalankan langkah berikut dan bisa dilanjutkan dari mana saja (`--dari LANGKAH`,
`--sampai LANGKAH`, `--tanpa-en`):

| Langkah | Alat | Hasil |
|---|---|---|
| export | `tools/db.py` | `episode.json` (episode + adegan + fakta + sumber + suara + musik), divalidasi |
| voice | `tools/voice.py` | TTS per adegan (di-cache: hanya adegan yang teksnya berubah yang dibuat ulang), jeda dirapikan, tempo |
| layout | `tools/layout.py` | `timeline.json`: potongan adegan di ketukan musik, waktu kata, isyarat visual, halaman subtitle ID/EN, amplop mulut maskot |
| page | `tools/build_page.py` | `index.html` satu berkas (mesin + data + ikon) |
| sfx | `tools/dump_sfx.mjs` | `sfx.json`: pin efek suara dihitung halaman dari waktu yang sama dengan visual |
| mix | `tools/mix.py` | suara −16 LUFS + efek + musik (diedit, ducking) → master −14 LUFS |
| render | `tools/export.mjs` | render frame-demi-frame 30 fps (ID dan EN) |
| final | `tools/finalize.py` | `out/<id>.mp4`, `<id>-tanpa-musik.mp4`, `<id>-en.mp4`, `.srt`; status `dirender` di database |

Waktu proses di 4 CPU: TTS ±30 dtk, render ±5 menit per bahasa, encode ±3 menit.

## Database (`db/schema.sql`)

| Tabel | Isi |
|---|---|
| `kategori` | mitos-fakta, gizi, sains, tubuh, intermezo, ... |
| `sumber` | judul, penerbit, URL, tanggal cek, `singkat` (nama pendek untuk kredit di layar) |
| `fakta` | klaim (ID/EN), nilai, satuan, basis (per 100 g, per porsi), status (fakta / mitos / sebagian / perkiraan), sumber, catatan cara hitung |
| `aset` | ikon kustom (SVG di `engine/icons`) yang tidak ada di Fluent Emoji, mis. `tempe`, `kedelai` |
| `suara` | penyedia, model, voice_id, pengaturan, tempo, catatan lisensi |
| `musik` | berkas di `engine/audio/bgm`, judul, artis, lisensi, `bpm`, `mulai` (diisi `db.py musik`) |
| `episode` | judul (ID/EN), kategori, suara, musik, status (`draf` → `siap` → `dirender` → `terbit`) |
| `adegan` | urutan, jenis, `vo` (naskah ID), `vo_en` (subtitle EN), `param` (JSON) |
| `episode_fakta` | fakta yang dipakai episode (sumbernya otomatis masuk kredit penutup) |
| `render` | berkas hasil per bahasa + durasi |

File JSON di `db/data/` adalah sumber yang mudah diedit dan di-diff; web/aplikasi bisa langsung menulis ke
SQLite (atau Postgres dengan skema yang sama), lalu memanggil `make_video.py <id>` dari antrean kerja.

## Menulis naskah (`vo`)

```
[curious] Minum air es... | bikin gendut? | {p0}Mitos... | atau {p1}fakta?
```

- `[tag]` arahan intonasi ElevenLabs v3: `curious`, `excited`, `whispers`, `surprised`, `laughs`, `serious`,
  `dramatically`, `mischievously`, `playful`, `warm`. Tag yang sama otomatis mengatur ekspresi & pose maskot.
- `|` batas halaman subtitle. `vo_en` harus punya jumlah `|` yang sama.
- `{nama}` tepat sebelum sebuah kata = isyarat waktu untuk visual (lihat tabel di bawah).
- Kata yang berakhir `...` mendapat jeda tegang 0,42 dtk, `?` di tengah adegan 0,34 dtk; jeda lain dipotong ke 0,24 dtk.
- Tulis angka sebagai kata di `vo` ("dua puluh gram") supaya dibaca benar; tulis angkanya di `param` untuk layar.

## Jenis adegan dan `param`

| Jenis | Param | Isyarat |
|---|---|---|
| `kuis` | `judul`, `pilihan` (2–3: `label`, `ikon`), `jawaban` (indeks), `ikon` (opsional, gambar utama bila pilihan berupa teks seperti MITOS/FAKTA), `stiker` | `{p0}` `{p1}` `{p2}` saat pilihan disebut |
| `jawaban` | `stempel` (MITOS!/BENAR!/MENANG!), `label` (angka di bawah tiap kartu), `catatan`, `besar` (teks riso besar), `teaser` (open loop) | `{jawab}` wajib, `{label}`, `{besar}`, `{teaser}` |
| `langkah` | `judul`, `gaya` (`rantai` = sebab-akibat berpanah, `daftar` = tips bernomor), `item` (2–4: `ikon`, `teks`, `sub`) | `{l0}`..`{l3}` |
| `banding` | `judul`, `sub`, `tema` (`kejutan` = halaman kuning), `item` (2–3: `label`, `ikon`, `nilai`, `teks`, `juara`) | `{b0}`..`{b2}` |
| `twist` | `nada` (`peringatan` = goresan piringan + halaman gelap, `kejutan` = halaman biru), `judul`, `kicker`, `headline` (kata di antara `*bintang*` diberi stabilo), `baris` (`ikon`, `teks`, `nilai`, `ok`), `angka` (`teks`, `sub`) | `{k}` kartu berita, `{i0}`.. baris, `{angka}`, `{stabilo}` |
| `cta` | `judul`, `ikon`, `tagline` (chip), `ajakan`, `ikon_ajakan` (callback yang membesar di kata terakhir) | — |

Isyarat yang tidak ditulis diisi merata sepanjang ucapan adegan (validasi memberi peringatan).
Ikon: nama dari [Fluent Emoji Flat](https://icon-sets.iconify.design/fluent-emoji-flat/) (MIT, 3.181 ikon,
mis. `onion`, `egg`, `ice`, `thermometer`) atau `id` dari tabel `aset` untuk SVG kustom.

Yang otomatis dikerjakan mesin untuk setiap episode: hitung mundur 3-2-1 dan rolet sorotan sebelum jawaban,
musik berhenti saat hitung mundur lalu masuk lagi di ketukan jawaban, crash zoom ke kartu jawaban, konfeti,
open loop (layar meredup + kartu "di akhir video!"), progress bar (hijau per adegan isi, merah untuk twist),
transisi antar-area (menembus kartu, whip, tinta merembes, daun melintas lensa), maskot (posisi, ekspresi dari tag,
mulut mengikuti suara), subtitle per kata, kredit sumber + suara di penutup.

## Menambah episode

1. Tambah fakta + sumbernya di `db/data/fakta.json` dan `sumber.json` (angka harus bersumber).
2. Buat `db/data/episode/<id>.json` (salin salah satu contoh), tulis naskah dengan isyarat.
3. `python3 tools/db.py import && python3 tools/db.py validate <id>`
4. `python3 tools/make_video.py <id>`

## Lisensi & kredit

- Suara ElevenLabs dari akun gratis: **non-komersial dan wajib atribusi** ("Suara: ElevenLabs" tampil di penutup).
  Untuk monetisasi, ganti ke paket berbayar lalu jalankan ulang (TTS di-cache per teks).
- Musik Mixkit (Stock Music Free License), efek suara Mixkit dari pustaka video-shotcraft, ikon Fluent Emoji (MIT):
  daftar per berkas di `engine/audio/ATTRIBUTION.md`.
- Mesin visual: Bang Motion (HTML + GSAP, render = fungsi murni waktu) dan kartu shot video-shotcraft
  (riso-print-hits, hatch-depth, ink-bleed-reveal, marker-underline); maskot dan efek inti dipakai ulang dari
  `projects/daun-katuk-v2`.
