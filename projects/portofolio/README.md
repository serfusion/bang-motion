# Portofolio superfal-dev.com

Situs statis satu halaman: `index.html`, folder `assets/`, dan `cv-naufal-aufa-afaf.pdf`.
`index.html` dibangun dari `sumber/portofolio.src.html` (lihat Build); situsnya sendiri tidak butuh database atau server aplikasi. Kartu profil + menu di kiri, isi per tab di kanan
(Tentang, Pengalaman, Proyek, Innovation, Kontak). Tiap tab punya alamat sendiri, mis. `superfal-dev.com/#innovation`
(alamat lama `#alat` otomatis diarahkan ke Innovation).

Gaya: permukaan netral ala shadcn, gerak pegas ala Arc UI (smooth, snappy, morph), transisi blur halus.
- **Dynamic Island** di atas: diam = "Open to Work", ganti tab = nama tab sesaat, diklik = kontak cepat.
- **Deretan berjalan**: logo "Pernah bekerja & berkolaborasi" di Tentang dan galeri proyek di Proyek (berhenti saat disentuh/disorot).
- **Daftar** semua proyek dan semua Innovation (berlambang), tanpa perlu klik berulang.
- **Tombol morph**: Unduh CV dan Salin email berubah label dengan lebar memegas.
- Tema terang/gelap lewat tombol matahari/bulan (sapuan melingkar di browser yang mendukung).

## Memasang di VPS

Lihat [`deploy/superfal/README.md`](../../deploy/superfal/README.md): satu skrip (`sudo bash deploy/superfal/pasang.sh`)
memasang portofolio ini di `superfal-dev.com`, Content Creator di `/studio/`, dan HTTPS. Pembaruan:
`sudo bash deploy/superfal/perbarui.sh`.

## Content Creator (tab Innovation)

Baris **Content Creator · Live** punya kolom **Masukkan kunci**. Di superfal-dev.com kunci dikirim ke
`/studio/masuk`; bila benar, studio (panel mesin video) terbuka di `/studio/`. Kunci diperiksa server dan hanya
tersimpan di VPS (`/etc/superfal/kunci`), tidak ada di halaman ini maupun di repo. Di luar domain itu (mis.
pratinjau) formulir membuka studio di tab baru.

## Perlindungan

- Klik kanan, seleksi teks, seret gambar, salin (Ctrl/Cmd+C, X, A), lihat sumber (Ctrl+U), simpan (Ctrl+S),
  cetak (Ctrl+P) dan pintasan devtools (F12, Ctrl+Shift+I/J/C/K, Cmd+Opt+I/J/C/U) diblokir, dengan pesan
  "Content is protected" di Dynamic Island. Kolom isian dan alamat email tetap bisa diseleksi; tombol salin email tetap jalan.
- Cetak halaman hanya menampilkan alamat situs dan tautan CV.
- `index.html` adalah hasil build: skrip diacak (javascript-obfuscator: string terenkripsi, alur diacak, perangkap
  debugger saat devtools terbuka, konsol dimatikan), HTML/CSS diperkecil, dan skrip terkunci ke domain
  superfal-dev.com (salinan di domain lain dialihkan ke superfal-dev.com).
- Batasnya: semua yang tampil tetap terkirim ke peramban, jadi orang yang gigih masih bisa menyalin tampilan.
  Repo ini publik; untuk benar-benar menutup kode sumber, pindahkan ke repo privat.

## Build

Sumber yang diubah adalah `sumber/portofolio.src.html` (terbaca, ikon ditulis `{{i:set:nama|kelas}}`), bukan `index.html`.

```bash
cd projects/portofolio/sumber
npm install            # sekali: ikon Iconify, javascript-obfuscator, html-minifier-terser
npm run build          # -> ../index.html (terlindungi)
node bangun.mjs --baca /tmp/portofolio-terbaca.html     # versi terbaca untuk diperiksa
```

## Mengubah isi

| Bagian | Tempat |
|---|---|
| Teks tiap tab | `sumber/portofolio.src.html`, cari `data-tab="tentang"`, `"pengalaman"`, `"proyek"`, `"innovation"`, `"kontak"`; terjemahan EN/ID/ZH di objek `I18N` (kunci `data-t`). Lalu `npm run build` |
| Proyek baru | tab `proyek`: tambah satu `<figure class="shot">` di galeri dan satu `<li class="prow">` di daftar (gambar 16:10 di `assets/`) |
| Innovation baru / yang sudah jadi | tab `innovation`: salin satu `<li class="irow">`; ganti label "Coming soon" dengan tautan atau lencana Live |
| Logo organisasi | deretan `marquee logos` di tab Tentang (`assets/logo-*.webp`, tinggi 96 px) |
| Foto | `assets/foto.webp` (persegi) |
| Gambar proyek | `assets/proyek-*.webp`, rasio 16:10 (mis. 1200 × 750) |
| CV PDF | sumber `sumber/cv.html`: buka di Chrome, Cetak → Simpan sebagai PDF, kertas A4, lalu ganti `cv-naufal-aufa-afaf.pdf` |
| Gambar pratinjau tautan (WhatsApp / LinkedIn) | `assets/og.jpg` 1200 × 630, sumbernya `sumber/og.html` |
