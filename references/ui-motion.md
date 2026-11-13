# Komponen UI bergerak — Dynamic Island, Card Stack, Morph Button

Dibaca bila konsep memakai antarmuka (app/SaaS, tur produk, explainer dengan kartu sumber
atau penanda status), atau bila user mengeluh hasilnya "kaku", "kurang smooth", "seperti
template". Perkakasnya ada di `assets/ui-kit.html`: blok CSS + JS yang ditempel ke
`index.html` hasil starter mana pun, plus peraga ±20 dtk (`?debug=1` untuk scrub).

Komponen ini perkakas, bukan kerangka. Ia dipakai bila konsep menuntut UI yang BEKERJA
(`opener-konsep.md` → "Animasi UI untuk app & SaaS"), bukan ditempel ke setiap video.

## Kenapa terasa kaku — periksa ini dulu

Rasa kaku jarang datang dari kurang efek. Biasanya dari cara benda mulai, berhenti, dan
berganti. Cek kode sebelum menambah apa pun:

| Gejala | Sebab | Obat |
|---|---|---|
| Semua gerak `power4.out` 0,8 dtk; geser 40 px terasa lamban, geser 900 px menyentak | durasi tidak mengikuti jarak dan massa | pegas: durasi lahir dari fisikanya (`UI.spring`) |
| Elemen A hilang, elemen B muncul di tempat yang sama | ganti, bukan morph; mata kehilangan pegangan | satu wadah berubah ukuran/bentuk, isinya blur-crossfade ≤ 10 px |
| Gerak berhenti mati, gerak berikut mulai dari nol | tween berurutan tanpa irisan | gerak berikut mulai saat yang lama di 60–80 %; isi menyusul wadah 40–100 ms (cascade) |
| Masuk dan keluar sama cepat | simetri | keluar ±60 % durasi masuk dengan ease-in; masuk dengan pegas/ease-out |
| Semua benda memantul (`back.out(1.9)`) | pantul di mana-mana terasa murah | pantul hanya untuk benda "fisik" (pil, lencana, island) 0–30 %; teks dan isi tanpa pantul |
| Isi UI di-blur 14–34 px saat masuk | kabur → lembek | blur isi UI ≤ 10 px (aturan beUI); motion blur berarah tetap untuk teks besar yang melesat (`techniques.md` §2) |
| Close-up buram di MP4; frame scrub ≠ frame ekspor | `will-change` mengunci skala raster; dua tween properti sama beririsan | starter mematikan `will-change` saat `?clean=1`; kit memotong tween lama di titik tween baru (lintasan per properti) |
| Video tidak mengulang, berhenti di frame akhir | tween `repeat:-1` membuat durasi timeline tak berujung | penjaga loop di ticker (sudah ada di semua starter); kit tidak memakai `repeat:-1` |

## Tiga bahan, satu bahasa

User boleh meminta "gabungkan shadcn, beUI, Arc UI". Gabungan yang benar adalah tiap
pustaka menyumbang SATU lapisan, bukan tiga kulit yang ditumpuk:

| Bahan | Menyumbang | Wujud di kit |
|---|---|---|
| shadcn/ui | struktur: token semantik, garis tipis, ring fokus, kartu/badge/tombol yang rapi | `--ui-card/-fg/-muted/-border/-ring`, `--ui-r` (radius .625rem × skala panggung = 28 px), material `solid` |
| beUI | gerak: pegas fisik dengan angka sumbernya, isi berganti lewat blur-crossfade ≤ 10 px, keluar lebih cepat dari masuk, isi mengembang dari pusat wadah, kaca 20 px | `UI.spring('press'…)`, `faceIn/faceOut`, `swapText`, material `glass` |
| Arc UI | cahaya: permukaan gelap berlapis, rim gradien dua aksen, glow aksen, kurva ease Arc, bayangan tema terang di-tint aksen | `UI.EASE.out/in/std`, material `glow`, `--ui-accent-2` |

**Memilih material** — satu keluarga per video (`techniques.md` §7e), kecuali pergantiannya
dijadikan momen:
- `solid` (shadcn): mockup UI produk yang realistis, tema terang, default.
- `glass` (beUI): di atas foto, footage, gradien, atau blob yang bergerak; kaca tanpa latar
  bergerak di belakangnya tidak terbaca.
- `glow` (Arc): arah sinematik gelap, grainy gradient, garis neon. BUKAN untuk mockup
  realistis: makin realistis elemennya, makin salah glow-nya (`techniques.md` §6).
- `ink`: permukaan hampir hitam untuk Dynamic Island (boleh juga `glass`/`glow`).

**Warna dan font** — komponen membaca brand dari style brief: `--accent` → `--ui-primary`
(aksi, ring, glow), `--accent-2` atau `--accent-lit` → rim kedua. Permukaan netral (zinc ala
shadcn, lapisan gelap ala Arc) boleh diganti warna UI produk user. `--ui-font` = font UI
PRODUK, bukan font display. Hijau/merah (`--ui-ok`, `--ui-err`) hanya untuk makna status.

## Mesin gerak

**Pegas** (`UI.spring(nama)` → `{ease, duration}`, di-spread ke tween GSAP biasa). Solusi
analitik pegas teredam; durasi = waktu sampai sisa < 0,05 %, bukan ditebak. Angka
press/swap/panel/layout/stack diambil dari token pegas beUI (stiffness/damping/mass, sama
dengan Framer Motion):

| Nama | Parameter | ζ | 90 % tercapai | Tenang penuh | Pantul | Untuk |
|---|---|---|---|---|---|---|
| `press` | 500 / 30 / 0,6 | 0,87 | 0,11 dtk | 0,33 dtk | 0,4 % | tombol ditekan |
| `swap` | 460 / 30 / 0,55 | 0,94 | 0,13 dtk | 0,27 dtk | — | label/ikon/angka berganti |
| `panel` | 420 / 40 / 0,5 | 1,38 | 0,20 dtk | 0,63 dtk | — | kartu/panel masuk |
| `layout` | 360 / 32 / 0,6 | 1,09 | 0,18 dtk | 0,51 dtk | — | wadah berubah ukuran (morph) |
| `stack` | 420 / 34 / 0,75 | 0,96 | 0,16 dtk | 0,35 dtk | — | tumpukan menata ulang |
| `island` | durasi 0,5 · bounce 0,28 | 0,72 | 0,22 dtk | 0,87 dtk | 3,8 % | Dynamic Island (kenyal tipis) |
| `pop` | durasi 0,55 · bounce 0,42 | 0,58 | 0,20 dtk | 1,15 dtk | 10,7 % | lencana, stiker, titik yang meletup |
| `expand` | durasi 0,62 · bounce 0,18 | 0,82 | 0,30 dtk | 0,89 dtk | 1,1 % | wadah berubah ukuran BESAR (tombol ↔ panel); dipilih otomatis oleh Morph Button bila ukuran berubah > 2,2× |
| `calm` | durasi 0,9 · bounce 0 | 1,00 | 0,56 dtk | 1,43 dtk | — | benda besar, kamera |

Pegas sendiri: `UI.spring({k, c, m})` atau `UI.spring({dur, bounce})` (pemetaan SwiftUI).
`uiKit(tl, {tempo: 1.15})` memperlambat semua pegas secara fisik (bentuk sama, durasi lebih
panjang) — pakai 1,1–1,3 bila komponen kecil di frame atau VO lambat; di atas 1,4 kembali
terasa lamban.

**Kurva** (`UI.EASE`, cubic-bezier tanpa plugin): `out` (.16,1,.3,1 — Arc/beUI, masuk dan
mekar), `in` (.7,0,.84,0 — Arc, keluar), `std` (.4,0,.2,1 — Arc, ganti keadaan di tempat),
`inOut` (.77,0,.175,1 — beUI), `drawer` (.32,.72,0,1 — beUI, laci/sheet), `flick` (.25,.85,.3,1 —
lemparan: kencang lalu melambat tanpa loncatan di frame pertama).

**Pegas di luar komponen** — sah dipakai untuk benda apa pun yang punya massa:
```js
tl.to('#stiker', {scale:1, rotation:0, ...UI.spring('pop')}, 6.2);         // stiker meletup
tl.to('#kartu',  {y:0, ...UI.spring('panel')}, 7.0);                        // kartu mendarat tanpa pantul
UI.go('#ikon', 8.1, {x:420, y:-60}, UI.spring('layout'));                     // lewat lintasan kit (lihat di bawah)
```

**Lintasan per properti (determinisme)** — `UI.go(el, at, {prop: nilai}, {ease, duration})`
adalah tween yang dimulai dari nilai TERHITUNG lintasan di detik `at`, bukan nilai DOM saat
itu. Bila tween lama pada properti yang sama masih berjalan, kit memotongnya tepat di `at`.
Hasilnya: tidak ada dua tween menulis properti yang sama bersamaan, sehingga frame identik
dari jalur scrub mana pun (lompat langsung, diputar berurutan seperti ekspor, atau mundur
dari akhir). Konsekuensinya:
- panggil operasi tiap komponen URUT WAKTU (kit memperingatkan di konsol bila tidak);
- jangan mencampur `tl.to` manual dan kit pada properti yang sama di elemen yang sama
  (pakai `UI.go`, atau gerakkan pembungkusnya);
- `UI.put(el, at, {...})` = lompat (set) yang tercatat di lintasan;
- blur memakai variabel `--bm-blur` (angka), bukan string `filter`.

## Morph, bukan ganti

Prinsip yang membuat ketiga komponen terasa halus, dan berlaku juga di luar kit:
1. **Wadah adalah benang merah.** Saat keadaan berubah, satu wadah yang sama berubah ukuran,
   radius, dan warna. Elemen baru tidak muncul dari kosong di tempat yang sama.
2. **Isi keluar dulu, cepat**: 0,16 dtk, ease-in, blur 6 px, mengecil ke .86, tersedot ke
   pusat wadah.
3. **Wadah berubah dengan pegas**, mulai 30–40 ms setelah isi lama mulai keluar.
4. **Isi baru mengembang dari pusat**: bagian `lead` datang dari arah tengah ke kiri, `trail`
   dari tengah ke kanan, `main` naik 10 px; blur 8 → 0, stagger 45 ms, mulai saat wadah
   kira-kira sepertiga jalan.
5. **Warna berganti lewat lapisan** (`.bm-fill`) yang di-crossfade di atas lapisan lama,
   bukan tween warna. Gradien dan `color-mix` tetap aman, dan tidak ada warna antara yang
   keruh.
6. **Isi berukuran tetap** (ukuran keadaan tujuannya), wadah yang memotongnya. Teks tidak
   reflow selama morph; saat wadah menyusut, isi terpotong masuk (bahasa "wadah menyusut"
   di `opener-konsep.md`).

## Dynamic Island

Satu pil gelap di tepi atas layar yang berubah wujud untuk menyampaikan **status yang
berubah**: proses berjalan, angka bertambah, rekaman aktif, langkah selesai. Bukan
subtitle, bukan judul, bukan logo.

- **Lapisan layar**: anak langsung `#stage`, di luar rig kamera (`#world`). Tidak ikut zoom,
  tidak tertutup vignette (z-index 30).
- **Isi**: ≤ 3 kata atau satu angka + ikon per tampilan; teks ≥ 34 px (sub 30 px).
- **Ukuran** (panggung 1080): pil 252×74 · ringkas 360–460×74 · lebar 560–660×74 ·
  terbuka 720–820 × 190–220 (radius 56–64). Di 9:16, `--island-top` 56–72 px.
- **Gerak**: titik jatuh dari tepi atas (`pop`) → melebar jadi pil (`island`) → tiap ganti
  tampilan memakai urutan "morph, bukan ganti" → `bump` 1,05 saat angka di dalamnya berubah
  → `hide` menyusut jadi titik lalu naik keluar.

```html
<!-- di dalam #stage, SETELAH #world -->
<div class="bm-island" id="isl" data-mat="ink">
  <div data-view="langkah" class="isl-row">           <!-- class layout bebas; ukuran diisi kit -->
    <span data-part="lead" class="ico">…</span>
    <span data-part="main" class="bm-t">Langkah</span>
    <span data-part="trail" class="bm-t" id="nLangkah">1</span>
  </div>
  <div data-view="proses">…<span data-part="trail" class="bm-t" id="pct">0%</span>
    <span data-part="main" class="bm-bar" id="bar"><i></i></span></div>
</div>
```
```js
const isl = UI.island('#isl', {views:{langkah:{w:420,h:74}, proses:{w:780,h:204}}});
isl.show(.4);                          // titik → pil
isl.to(1.2, 'langkah');                // pil → ringkas, isi mengembang
UI.swapText('#nLangkah', 2.6, '2');  isl.bump(2.6);
isl.to(4.0, 'proses');  UI.fill('#bar', 4.3, 1.8);   UI.count('#pct', 4.3, 1.8, {fmt:v=>Math.round(v)+'%'});
isl.to(6.4, 'pill');    isl.hide(9.0);
```

**Menu pakai** (pilih yang dituntut konsep):
- Opener app: notifikasi masuk, unggah/proses dengan progres, timer, sedang merekam atau
  memutar (`UI.wave`), AI "berpikir" lalu selesai, pembayaran berhasil.
- Explainer: penanda bab ("Bab 2 · Penyebab"), status narasi, sumber terverifikasi, hitung
  mundur atau angka yang berjalan, kuis "Benar atau salah?".

**Jangan**: subtitle atau kalimat panjang di dalam island; island diam di setiap adegan
tanpa status yang berubah (hiasan diam = template); dua island; island di dalam `#world`;
ikon/teks di bawah 30 px.

## Card Stack

Tumpukan kartu berkedalaman. Kartu baru masuk di atas, kartu lama mundur satu slot (naik
30 px, mengecil 6 %, meredup 30 %). Kartu teratas bisa dilempar lalu diselipkan ke belakang
(dikocok), dibentangkan menjadi daftar yang terbaca, lalu ditumpuk lagi.

- **Lapisan dunia**: di dalam `#world`; kamera boleh mendekat (ukuran shot, `techniques.md`
  §3b). Posisikan lewat `.bm-anchor` (titik pusat) dengan ukuran kartu tetap
  (`--card-w`, `--card-h`) — `spread` mengukur tinggi kartu.
- **Isi kartu ≤ 3 baris pendek** (badge + judul + satu meta) supaya dibaca sebagai objek,
  bukan tingkat teks (`explainer.md` "Satu adegan = 3–5 elemen", aturan 7). Judul ≥ 40 px,
  meta ≥ 30 px.
- **Gerak**: kartu baru turun dari atas (`panel`) dengan blur 8 → 0; yang lama menata ulang
  (`stack`, stagger 35 ms); lemparan `EASE.flick` 0,5 dtk dengan blur 4 px sesaat di kecepatan
  puncak, diselipkan ke belakang dengan `stack` mulai 0,4 dtk; bentang memakai `layout` dengan
  stagger 50 ms.

```html
<div class="bm-anchor" style="left:600px;top:600px">
  <div class="bm-stack" id="stk" style="--card-w:600px;--card-h:250px">
    <article class="bm-card" data-mat="solid">…</article>   <!-- urutan DOM = urutan push -->
    <article class="bm-card" data-mat="solid">…</article>
  </div>
</div>
```
```js
const stk = UI.stack('#stk', {gap:30, step:.06, depth:3});        // peek:'down' = kartu belakang mengintip di bawah
stk.push(2.0); stk.push(3.4);           // satu kartu per frasa VO (akresi)
stk.next(5.1, {dir:1});                  // kocok: lempar ke kanan, selip ke belakang
stk.spread(6.4);                         // daftar terbaca (kamera boleh mendekat)
stk.collapse(8.6);
stk.next(9.8, {cycle:false});            // buang kartu teratas
```

**Menu pakai**: akresi bukti per frasa VO (kartu sumber, kliping, data), fitur yang dikocok
satu per satu, testimoni bergiliran, langkah proses, "tiga fakta" yang dibentangkan menjadi
rangkuman di akhir babak.

**Jangan**: tiga kartu berjejer diam (itu "tiga tile", komponen kanonik); mengocok terus
tanpa makna baru; kartu berisi paragraf; lebih dari 5 kartu.

## Morph Button

Satu tombol yang berubah wujud mengikuti hasil aksinya: label → bulat dengan spinner →
sukses (centang digambar) → bisa mekar menjadi panel langkah berikutnya → menyusut kembali.

- **Lapisan dunia**, di dalam UI produk (`.bm-anchor` membuatnya tumbuh simetris dari titik
  pusat; di dalam layout flex/grid ia juga bisa in-flow).
- **Klik yang terasa** (`techniques.md` §8): kamera mendekat 0,3–0,5 dtk sebelum klik →
  `press` (scale .94 → 1 dengan pegas press + ring ala shadcn) → baru tombol berubah →
  kamera mundur atau bergeser ke hasilnya. Tidak setiap klik mendapat zoom.
- **Keadaan**: `states` berurutan, yang pertama = keadaan awal. Tiap keadaan punya ukuran,
  radius (bawaan pil = h/2), dan lapisan warna (`fill`). Perubahan kecil memakai pegas `layout`;
  perubahan besar (> 2,2×, mis. tombol ↔ panel) otomatis memakai `expand` supaya tidak
  terburu-buru. `to(at, nama, {spring:'…'})` untuk memilih sendiri.

```html
<div class="bm-anchor" style="left:1330px;top:600px">
  <div class="bm-mbtn" id="kirim" data-mat="solid">
    <i class="bm-ring"></i>
    <div class="bm-clip">
      <i class="bm-fill" data-fill="primary"></i><i class="bm-fill" data-fill="ok"></i><i class="bm-fill" data-fill="card"></i>
      <span data-view="idle"><span data-part="main" class="bm-label">Kirim</span></span>
      <span data-view="busy"><svg data-part="main" class="bm-spin" id="spin" viewBox="0 0 48 48">
        <circle class="trk" cx="24" cy="24" r="19"/><circle class="arc" cx="24" cy="24" r="19"/></svg></span>
      <span data-view="done"><svg data-part="lead" class="bm-check" viewBox="0 0 48 48"><path id="ok" d="M11 25.5l8.5 8.5L37 15"/></svg>
        <span data-part="main" class="bm-label">Terkirim</span></span>
      <div data-view="panel">…baris panel, masing-masing data-part="main"…</div>
    </div>
  </div>
</div>
```
```js
const kirim = UI.morphButton('#kirim', {states:{
  idle :{w:360, h:112, fill:'primary'},
  busy :{w:112, h:112, fill:'primary'},
  done :{w:380, h:112, fill:'ok'},
  panel:{w:640, h:480, r:44, fill:'card'}}});
kirim.press(9.4);  kirim.to(9.55, 'busy');  UI.spin('#spin', 9.6, 1.8);
kirim.to(11.4, 'done');  UI.draw('#ok', 11.55);
kirim.press(13.0); kirim.to(13.15, 'panel');   // panel mekar ke langkah berikut — transisi tanpa cut
kirim.to(16.0, 'idle');
```

**Menu pakai**: CTA diegetik di penutup (tombol di UI ditekan, bukan teks CTA melayang),
"Kirim / Bayar / Unggah / Terbitkan" di demo produk, "Cek fakta" → "Terverifikasi" di
explainer, panel yang mekar ke langkah berikut, kuis yang dijawab.

**Jangan**: tombol berubah tanpa klik atau sebab yang terlihat; spinner lebih dari ±2 dtk
tanpa progres; warna sukses/gagal untuk makna yang bukan status.

## Menempel ke starter

1. Salin blok `UI-KIT CSS` ke `<style>` dan blok `UI-KIT JS` ke `<script>` setelah
   `const tl = gsap.timeline({paused:true})`, lalu `const UI = uiKit(tl);`. Beri nama variabel
   komponen yang tidak bentrok dengan starter (starter opener sudah memakai `btn`, `clock`,
   `scrub`, `stage`; explainer memakai `rig`, `C`, `q`, `vo`).
2. Island = anak langsung `#stage` setelah `#world`; stack dan tombol di dalam `#world`
   (opener: di `#dom`).
3. Turunkan token dari style brief: `--accent`, `--accent-2`, permukaan (`--ui-card`, `--ui-fg`,
   …) bila UI produk punya warna sendiri, `--ui-font`; `data-ui="light"` pada `#stage` atau
   pembungkus untuk tema terang.
4. Semua tulis-ke-timeline: `OPENER.seek`, `snap.mjs`, dan `export-frames.mjs` tidak butuh
   perubahan. Jangan menambah `will-change` pada elemen yang di-zoom kamera.
5. Potret detik kunci (`snap.mjs`): tepat sebelum klik, puncak morph, island terbuka, tumpukan
   terbentang — teks tidak terpotong, island tidak menimpa isi dunia.

## Cek sebelum menyerahkan

- [ ] Komponen dipakai karena konsep menuntut UI yang bekerja, bukan hiasan di setiap video
- [ ] Satu material per video (solid / glass / glow), glow tidak pada mockup realistis
- [ ] Warna dari `--accent`/`--accent-2` style brief; font UI = font produk; status hijau/merah
      hanya untuk makna status
- [ ] Keadaan berganti lewat morph satu wadah, bukan elemen baru di tempat yang sama
- [ ] Isi keluar lebih cepat dari masuk; blur isi ≤ 10 px; pantul hanya pada benda fisik
- [ ] Island di lapisan layar, ≤ 3 kata per tampilan, statusnya berubah (bukan hiasan diam)
- [ ] Kartu ≤ 3 baris pendek, ukuran tetap; tumpukan tidak menjadi tiga tile berjejer
- [ ] Klik penting: kamera mendekat sebelum `press`, tombol berubah sesudahnya
- [ ] Operasi tiap komponen dipanggil urut waktu; tidak ada `tl.to` manual pada properti yang
      sama dengan kit; tidak ada `repeat:-1`
- [ ] Teks ≥ 30 px di semua komponen; dipotret di detik kunci
