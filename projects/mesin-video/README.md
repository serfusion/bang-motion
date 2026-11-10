# Mesin video: database → video edukasi 9:16, otomatis

Satu baris episode di database (naskah + angka fakta + sumber) menjadi video pendek 9:16 lengkap: suara ekspresif,
subtitle per kata, efek suara, musik yang diedit di ketukan, dan MP4 siap unggah. Ada **dua format** (tebakan dan
fakta), **dua bahasa** (suara + subtitle Indonesia, atau suara + subtitle English), dan **panel web** untuk mengelola
semuanya. Tidak ada langkah yang memakai model AI saat membuat video; hanya suara yang memanggil layanan TTS
(ElevenLabs), dengan sampai 4 kunci API yang dipakai bergiliran.

## Contoh yang sudah jadi

| Episode | Format | Bahasa | Durasi |
|---|---|---|---|
| `kesehatan-tanpa-tidur` — 11 hari tanpa tidur: apa yang terjadi? | fakta | ID, EN | 75 / 71 dtk |
| `mitos-air-es` — Minum air es bikin gendut? | tebakan | ID, EN | 43 / 46 dtk |
| `gizi-tempe-telur` — Tempe vs telur | tebakan | ID | 45 dtk |
| `sains-bawang` — Kenapa motong bawang bikin nangis? | tebakan | ID | 52 dtk |

Hasil ada di `episodes/<id>/<bahasa>/out/` (`<id>-<bahasa>.mp4`, `-tanpa-musik.mp4`, `.srt`).
`episodes/<id>/<bahasa>/index.html` bisa dibuka langsung di browser (`?debug=1` untuk menggeser waktu).

## Mulai cepat

```bash
npm install                          # puppeteer (render), gsap, ikon Fluent Emoji
pip install -r requirements.txt      # flask, numpy
python3 panel/app.py                 # buka http://127.0.0.1:5000
```

Saat pertama dijalankan panel membuat `db/konten.db` dari `db/data/*.json`. Buka **Kunci API**, isi kunci ElevenLabs,
lalu buka episode mana saja dan tekan **Pratinjau** atau **Render MP4**.

Butuh juga: ffmpeg dengan filter `rubberband`, dan Chromium (puppeteer mengunduhnya saat `npm install`; atau set
`PUPPETEER_EXECUTABLE_PATH`). Panel hanya mendengarkan di komputer ini; untuk dibuka dari perangkat lain:
`PANEL_PASSWORD=… python3 panel/app.py --host 0.0.0.0`.

## Panel web (`panel/app.py`)

| Halaman | Isi |
|---|---|
| Dasbor | jumlah episode / fakta / sumber per kategori (16 kategori: sains, kesehatan, gizi, intermezo, fakta unik, mitos vs fakta, pengetahuan umum, analogi, tumbuhan, hewan, alam, sejarah, teknologi, psikologi, uang, tubuh), antrean, status kunci, hasil terbaru |
| Episode | daftar + saring; **episode baru** dari kerangka format; editor: info (judul ID/EN, kategori, format, suara ID & EN, musik, tempo), adegan (naskah ID + EN, param JSON ID + EN, contoh per jenis, pratinjau halaman subtitle, cek isyarat), fakta yang dipakai, validasi, perkiraan karakter ElevenLabs, render per bahasa, video hasil + unduhan, pencari ikon |
| Fakta, Kategori, Sumber | tambah / ubah / hapus; fakta bersumber dengan status fakta / mitos / sebagian / perkiraan |
| Aset | unggah SVG (jadi ikon) atau foto PNG/JPG/WEBP (ilustrasi besar format fakta: `"ilustrasi": {"gambar": "<id>"}`) |
| Musik | unggah lagu; BPM dan ketukan mulai dianalisis otomatis (librosa) |
| Suara | voice ID ElevenLabs, model, pengaturan, bahasa |
| Kunci API | 4 kotak kunci ElevenLabs + tombol Tes |
| Antrean | tugas render berjalan satu per satu di latar belakang, progres per langkah, log, batal / ulangi |

Panel menulis ke SQLite. **Simpan ke JSON** menulis isi database ke `db/data/*.json` (untuk git / cadangan);
**Muat dari JSON** kebalikannya. Kunci API tidak pernah ikut keduanya.

## Kunci API ElevenLabs: 4 kotak, bergiliran

Kunci dipakai berurutan. Bila kunci 1 ditolak karena kuotanya habis, kunci salah, atau kena batas laju, mesin
menandai kunci itu lalu langsung memakai kunci berikutnya yang aktif, tanpa menghentikan render
(`tools/elevenlabs.py`). Batas laju sesaat ditunggu dan dicoba ulang dulu. Variabel `XI_API_KEY` dipakai sebagai
cadangan terakhir. Suara di-cache per adegan, jadi render ulang hanya memakai kuota untuk adegan yang naskahnya berubah;
editor menampilkan jumlah karakter yang akan terpakai sebelum render.

Aturan ElevenLabs yang perlu diingat:
- Satu orang hanya boleh punya **satu akun gratis**; banyak akun gratis untuk menambah kuota bisa membuat penggunaan
  gratisnya dinonaktifkan ([kebijakan](https://elevenlabs.io/docs/help-center/account/general/can-users-have-more-than-one-account)).
  Kotak 2–4 untuk akun berbayar / tim atau cadangan yang sah.
- Suara dari paket gratis: **non-komersial dan wajib atribusi** ("Suara: ElevenLabs" otomatis tampil di penutup).
  Untuk monetisasi, pakai paket berbayar lalu render ulang.

## Dua format

| | Tebakan | Fakta |
|---|---|---|
| Gaya | kuis cepat dan seru | penjelasan santai bergaya catatan dokumenter |
| Alur | kuis → hitung mundur → jawaban → penjelasan → twist → ajakan | pembuka → catatan (kartu angka) → ibarat (analogi) → … → pertanyaan untuk penonton |
| Tempo suara | dipercepat 1,12×, jeda dipadatkan (maks 0,24 dtk) | asli 1,0×, jeda wajar (sampai 0,42 dtk), napas 0,3 dtk antar-adegan |
| Visual | maskot bereaksi, progress bar, whip / crash zoom, kertas berpindah area | kartu kicker + angka bertumpuk, ilustrasi besar di atas noda cat air, caption besar di tengah, kamera bergeser pelan di satu lembar kertas panjang |
| Durasi khas | 40–55 dtk | 60–80 dtk |

## Menulis naskah

```
[serious] {b0}<11=Sebelas> hari. | {b1}Tanpa tidur, | sama sekali. | tahun <1964=seribu sembilan ratus enam puluh empat>.
```

| Tulisan | Arti |
|---|---|
| `[tag]` | arahan intonasi ElevenLabs v3: `curious`, `excited`, `whispers`, `surprised`, `laughs`, `serious`, `dramatically`, `mischievously`, `playful`, `warm` (di format tebakan juga mengatur ekspresi maskot) |
| `\|` | batas halaman subtitle |
| `{nama}` | isyarat waktu visual, ditulis tepat sebelum kata (lihat tabel jenis adegan) |
| `<tampil=ucapan>` | suara membaca *ucapan*, subtitle menampilkan *tampil*: angka ditulis sebagai kata supaya dibaca benar, tapi tampil sebagai angka (`<0,05%=nol koma nol lima persen>`) |
| `kata...` / `?` | jeda tegang / jeda tanya |

`vo` = naskah Indonesia, `vo_en` = naskah English (isyarat sama). `param` = teks layar & angka (JSON); `param_en`
cukup berisi teks layar yang berbeda untuk video English, sisanya diambil dari `param`.

## Jenis adegan dan `param`

| Jenis | Format | Param | Isyarat |
|---|---|---|---|
| `kuis` | tebakan | `judul`, `pilihan` (2–3: `label`, `ikon`), `jawaban` (indeks), `ikon`, `stiker` | `{p0}` `{p1}` `{p2}` |
| `jawaban` | tebakan | `stempel`, `label` (angka per pilihan), `catatan`, `besar`, `teaser` (open loop) | `{jawab}` wajib, `{label}`, `{besar}`, `{teaser}` |
| `langkah` | keduanya | `judul`, `gaya` (`rantai` / `daftar`), `item` (2–4: `ikon`, `teks`, `sub`) | `{l0}`..`{l3}` |
| `banding` | keduanya | `judul`, `sub`, `tema`, `item` (2–3: `label`, `ikon`, `nilai`, `teks`, `juara`) | `{b0}`..`{b2}` |
| `twist` | tebakan | `nada`, `judul`, `kicker`, `headline` (`*kata*` distabilo), `baris`, `angka` | `{k}`, `{i0}`.., `{angka}`, `{stabilo}` |
| `cta` | tebakan | `judul`, `ikon`, `tagline`, `ajakan`, `ikon_ajakan` | — |
| `pembuka` | fakta | `judul` (baris), `sorot` (angka merah), `kicker`, `ilustrasi` | `{b0}` `{b1}`, `{sorot}` |
| `catatan` | fakta | `kartu` (1–4: `kicker` + `nilai` [+ `warna: "merah"`] atau `teks`), `ilustrasi` | `{k0}`..`{k3}` |
| `ibarat` | fakta | `kutipan`, `kartu`, `ilustrasi` | `{kutip}`, `{k0}`.. |
| `tanya` | fakta | `kartu`, `pertanyaan`, `pilihan` (2), `ajakan` | `{k0}`, `{tanya}`, `{pilih}` |

`ilustrasi`: `{"ikon": ["utama", "satelit", …]}` (komposisi ikon) atau `{"gambar": "<id aset foto>"}`.
Ikon: nama dari [Fluent Emoji Flat](https://icon-sets.iconify.design/fluent-emoji-flat/) (MIT, 3.181 ikon) atau `id`
dari tabel `aset`. Isyarat yang tidak ditulis diisi merata sepanjang ucapan adegan.

## Pipeline (baris perintah)

```bash
python3 tools/db.py validate                                  # cek semua episode, kedua bahasa
python3 tools/make_video.py kesehatan-tanpa-tidur --bahasa id,en
python3 tools/make_video.py mitos-air-es --bahasa en --sampai mix    # pratinjau tanpa MP4
```

| Langkah | Alat | Hasil (`episodes/<id>/<bahasa>/`) |
|---|---|---|
| export | `tools/db.py` | `../episode.json`: episode + adegan + fakta + sumber + suara + musik, divalidasi |
| voice | `tools/voice.py` | TTS per adegan (cache per teks), awal kata dicocokkan ke suara, jeda dirapikan, tempo |
| layout | `tools/layout.py` | `timeline.json`: potongan adegan di ketukan musik, waktu kata, isyarat, halaman subtitle |
| page | `tools/build_page.py` | `index.html` satu berkas (mesin + data + ikon + foto) |
| sfx | `tools/dump_sfx.mjs` | `sfx.json`: pin efek suara dari waktu yang sama dengan visual |
| mix | `tools/mix.py` | suara −16 LUFS + efek + musik (diedit, ducking) → master −14 LUFS, puncak −3 dBTP |
| render | `tools/export.mjs` | render frame demi frame, 30 fps, 4 proses paralel |
| final | `tools/finalize.py` | `out/<id>-<bahasa>.mp4`, `-tanpa-musik.mp4`, `.srt` |

Waktu proses di 4 CPU: suara ±30 dtk, render ±3–5 menit per bahasa, encode ±1–2 menit.

## Database (`db/schema.sql`)

| Tabel | Isi |
|---|---|
| `kategori` | 16 kategori (ID + EN) |
| `fakta` | klaim ID/EN, nilai, satuan, basis, status (fakta / mitos / sebagian / perkiraan), sumber, catatan cara hitung |
| `sumber` | judul, penerbit, URL, tanggal cek, `singkat` (nama di kredit video) |
| `aset` | SVG kustom dan foto unggahan |
| `suara` | penyedia, model, voice_id, pengaturan (termasuk `language_code`), tempo |
| `musik` | berkas, judul, artis, lisensi, `bpm`, `mulai` |
| `episode` | `format` (tebakan / fakta), judul ID/EN, kategori, suara ID & EN, musik, tempo, status |
| `adegan` | urutan, jenis, `vo`, `vo_en`, `param`, `param_en` |
| `episode_fakta`, `render` | fakta per episode (sumbernya masuk kredit), berkas hasil |
| `kunci_api`, `tugas` | kunci ElevenLabs (tidak pernah diekspor), antrean render panel |

## Lisensi & kredit

- Suara: ElevenLabs (lihat aturan di atas).
- Musik Mixkit (Stock Music Free License), efek suara Mixkit dari pustaka video-shotcraft, ikon Fluent Emoji (MIT):
  daftar per berkas di `engine/audio/ATTRIBUTION.md`.
- Mesin visual: Bang Motion (HTML + GSAP, render = fungsi murni waktu) dan kartu shot video-shotcraft; maskot dan efek
  inti dipakai ulang dari `projects/daun-katuk-v2`.
