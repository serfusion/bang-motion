# Changelog

## 1.20.0 — 2026-11-13

**Komponen UI bergerak — supaya tidak kaku**
- `assets/ui-kit.html`: perkakas siap tempel (blok CSS + JS) dengan tiga komponen —
  **Dynamic Island** (pil status di lapisan layar yang berubah wujud), **Card Stack** (kartu
  bertumpuk yang masuk, dikocok, dibentangkan, ditumpuk lagi), dan **Morph Button** (tombol →
  spinner → sukses → panel) — plus peraga ±20 dtk (`?ui=light`, `?mat=solid|glass|glow`).
- Tiga bahan, satu bahasa: struktur dan token dari shadcn/ui (material `solid`), gerak dari
  beUI (angka pegas sumbernya, blur-crossfade ≤ 10 px, kaca 20 px — material `glass`), cahaya
  dari Arc UI (rim gradien dua aksen, glow, kurva ease — material `glow`). Warna tetap dari
  `--accent` style brief, font UI = font produk.
- Mesin gerak deterministik: pegas teredam analitik (`UI.spring`, durasi lahir dari fisika),
  kurva cubic-bezier tanpa plugin (`UI.EASE`), dan lintasan per properti (`UI.go`) yang
  memotong tween lama di titik tween baru — frame identik dari jalur scrub mana pun.
- `references/ui-motion.md`: diagnosis "kaku / kurang smooth", prinsip morph bukan ganti, tabel
  pegas, aturan dan larangan tiap komponen, cara menempel ke starter. SKILL.md (Hukum #1,
  style brief, alur kerja, checklist), `techniques.md` §2b, menu `opener-konsep.md`, dan
  `explainer.md` merujuk ke sana.

**Perbaikan starter**
- Explainer (enam starter) kini benar-benar mengulang: tween `repeat:-1` membuat durasi
  timeline tak berujung sehingga `onComplete` tak pernah terpanggil — loop dijaga di ticker.
- Render ekspor (`?clean=1`) mematikan `will-change`: sebelumnya skala raster terkunci sehingga
  close-up di MP4 lebih buram daripada di browser dan frame ekspor berbeda dari frame scrub.
- Jebakan baru di `techniques.md` §10 dan `architecture.md` (tween beririsan saat scrub mundur,
  `tl.fromTo()` mengembalikan timeline, `will-change`, `repeat:-1`).

## 1.19.0 — 2026-09-15

**Ukuran shot — kamera ke elemen**
- "Zoom in-out" dirumuskan sebagai pergantian ukuran shot (wide ↔ medium close-up ↔ close-up) ke
  elemen yang sedang bercerita, bukan napas kamera beberapa persen yang hampir tak terlihat.
- Panduan memilih target dan waktu, dua tempo gerak, rig kamera dengan skala dari ukuran elemen
  dan klem tepi dunia, label di lapisan layar (`references/techniques.md` §3b).

## 1.18.0 — 2026-09-15

**Video sebagai layer footage**
- Semua starter membawa helper `clip(el, {at, in, out, rate, hold})`: klip video mengikuti jam
  timeline — sinkron saat diputar, tepat saat scrub — dan bisa dipotong, diperlambat, ditahan,
  di-mask, serta dianimasikan bersama elemen lain.
- `scripts/snap.mjs` dan `scripts/export-frames.mjs` menunggu frame klip siap, sehingga ekspor MP4
  tetap presisi frame.
- Panduan pemakaian, sumber klip (file sendiri, generate lewat MCP, stok berlisensi), format, dan
  pola layout di `references/techniques.md` §9b.
- Deliverable tetap `index.html` (+ `assets/` bila memakai klip atau audio), tanpa file peluncur.

## 1.17.0 — 2026-09-14

**Opener dan promo**
- Kerangka dipilih, bukan diwarisi: tiga kandidat konsep dari menu 19 konsep, sidik jari
  struktur yang dibandingkan dengan proyek sebelumnya, komponen kanonik paling banyak dua,
  dan starter opener tanpa urutan adegan contoh (`references/opener-konsep.md`,
  `assets/starter-opener.html`).
- Contoh urutan tiap konsep adalah prinsip, bukan naskah: pembuka/penutup dan momen khas
  tidak disalin; palet, bentuk, dan properti diturunkan dari brand, tiap warna menyebut
  sumbernya.
- Panduan animasi UI untuk app/SaaS, kamera yang mengikuti klik penting, dan foto dalam
  opener (foto user, generate lewat MCP, atau stok berlisensi).

**Tipografi, latar, render**
- Sorotan kata opsional; judul dan klaim tanpa titik otomatis.
- Latar tidak pernah statis; warna latar boleh berganti kapan dibutuhkan dengan pemicu
  terlihat. Grainy gradient dengan jaga-jaga encode. Menu gaya render objek.

**Explainer**
- Enam gaya: aksi kontinu, kartun kolase, jurnalisme visual, katalog putih, sketsa vintage,
  dan kartun panggung (`references/explainer.md`, `references/kartun-panggung.md`).

**After Effects**
- Dibangun langsung lewat bridge/MCP Higgsfield (`references/ae-bridge-higgsfield.md`,
  `scripts/ae/bridge/`).

**Alat kerja**
- Verifikasi visual per detik kunci (`scripts/snap.mjs`), ekspor MP4
  (`scripts/export-frames.mjs`), pemotong jeda VO (`scripts/vo-pauses.html`).
