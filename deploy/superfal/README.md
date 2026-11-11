# superfal-dev.com di VPS

Satu skrip memasang semuanya di VPS (Ubuntu 22.04):

| Alamat | Isi |
|---|---|
| `https://superfal-dev.com/` | portofolio (`projects/portofolio/index.html`, versi terlindungi) |
| `https://superfal-dev.com/studio/` | **Content Creator** = panel mesin video (`projects/mesin-video`), terkunci |

Nginx melayani portofolio dan meneruskan `/studio/` ke panel (Flask di `127.0.0.1:5000`, layanan systemd
`superfal-studio`). HTTPS dari Let's Encrypt, diperpanjang otomatis. Pengunjung membuka studio lewat tab
**Innovation → Content Creator → Masukkan kunci**.

## Langkah 1: arahkan domain ke VPS (di Vercel)

Domain memakai nameserver Vercel, jadi record DNS-nya diatur di Vercel:

1. Buka proyek lama yang memakai superfal-dev.com → **Settings → Domains** → hapus `superfal-dev.com` dan
   `www.superfal-dev.com` dari proyek itu (situs Vercel sedang berhenti, "Payment required").
2. Buka **Domains** (tingkat akun/tim) → `superfal-dev.com` → **DNS Records**:
   - hapus record lama untuk `@` dan `www` (A / ALIAS / CNAME yang mengarah ke Vercel);
   - tambah `A`, nama `@`, nilai **IP publik VPS**;
   - tambah `A`, nama `www`, nilai **IP publik VPS**.
3. Tunggu beberapa menit. Cek dari komputer mana saja: `nslookup superfal-dev.com` harus menjawab IP VPS.

## Langkah 2: buka port 80 dan 443 (Tencent Cloud)

Di konsol Tencent Cloud, instance VPS → **Firewall** (Lighthouse) atau **Security Group** (CVM) → tambah aturan
masuk TCP **80** dan **443**, sumber `0.0.0.0/0`, izinkan. Port 5000 tidak perlu dibuka: panel hanya didengar di VPS.

## Langkah 3: jalankan skrip di VPS

```bash
cd ~/bang-motion && git pull
```

```bash
sudo bash ~/bang-motion/deploy/superfal/pasang.sh
```

Skrip akan:
- memasang nginx, certbot, rsync (dan Flask untuk panel bila belum ada);
- meminta **kunci Content Creator** (diketik dua kali, tidak tampil di layar). Inilah sandi yang diketik
  pengunjung di tab Innovation. Disimpan di `/etc/superfal/kunci` (hanya root), tidak pernah masuk repo;
- menawarkan menghentikan panel lama yang masih berjalan di port 5000 (panel untuk SSH tunnel);
- memasang layanan `superfal-studio` (jalan otomatis setelah VPS restart);
- menyalin portofolio ke `/var/www/superfal-dev` (tanpa folder `sumber/`);
- menulis konfigurasi Nginx (konfigurasi lama yang memakai domain yang sama dicadangkan ke `/etc/nginx/superfal-cadangan/`);
- bila DNS sudah mengarah ke VPS: meminta sertifikat HTTPS (boleh mengisi email untuk pemberitahuan, boleh kosong).
  Bila DNS belum mengarah, situs jalan di HTTP dulu; jalankan skrip ini lagi setelah DNS berubah.

## Langkah 4: cek

- `https://superfal-dev.com/` tampil, tab Innovation berisi **Content Creator · Live**.
- Ketik kunci → studio terbuka di `https://superfal-dev.com/studio/`. Kunci salah → "Wrong key." Salah 8 kali
  dalam 15 menit → IP itu ditahan 15 menit (Nginx juga membatasi 12 percobaan per menit).
- Tombol **Keluar** di kanan atas studio mengakhiri sesi (sesi berlaku 7 hari).

## Sehari-hari

| Keperluan | Perintah |
|---|---|
| Ada perubahan baru di GitHub | `sudo bash ~/bang-motion/deploy/superfal/perbarui.sh` |
| Ganti kunci Content Creator | `sudo bash ~/bang-motion/deploy/superfal/pasang.sh --ganti-kunci` (semua sesi lama keluar) |
| Lihat log studio | `journalctl -u superfal-studio -f` |
| Mulai ulang studio | `sudo systemctl restart superfal-studio` (render yang sedang jalan akan gagal; ulangi dari Antrean) |
| Status HTTPS | `sudo certbot certificates` |

`perbarui.sh` menolak menarik repo bila ada perubahan lokal di VPS (misalnya hasil tombol **Simpan ke JSON** di
panel). Simpan dulu perubahan itu (`git stash`, atau commit lalu push), lalu jalankan lagi.

## Pindah domain nanti

Isi situs tidak terikat ke satu domain. Untuk domain baru:
1. Arahkan DNS domain baru (A `@` dan `www`) ke IP VPS.
2. Bangun ulang portofolio untuk domain itu (alamat situs, formulir kunci, dan kunci domain skrip ikut berganti),
   lalu commit dan push:
   `cd projects/portofolio/sumber && npm install && DOMAIN=domainbaru.com npm run build`
   Ganti juga nama domain di `projects/portofolio/robots.txt` dan `sitemap.xml`.
3. Di VPS: `sudo DOMAIN=domainbaru.com bash ~/bang-motion/deploy/superfal/perbarui.sh`.

Penting: tanpa langkah 2, skrip portofolio yang terkunci ke superfal-dev.com akan mengalihkan pengunjung domain baru
kembali ke superfal-dev.com.

## Catatan jujur

- **Perlindungan portofolio** (klik kanan, seleksi teks, Ctrl+C / Ctrl+U / Ctrl+S / F12 diblokir, skrip diacak,
  perangkap devtools, terkunci ke domain superfal-dev.com) membuat penyalinan jauh lebih repot, tetapi tidak
  mustahil: apa pun yang tampil di peramban tetap terkirim ke peramban.
- **Repo `serfusion/bang-motion` bersifat publik** (fork). Kode portofolio dan panel bisa dibaca siapa pun di
  GitHub, termasuk versi lama yang belum diacak. Supaya benar-benar tertutup, pindahkan ke repo privat
  (VPS lalu menarik dari repo privat dengan deploy key).
- Kunci Content Creator memberi akses penuh ke studio (mengubah data, merender, mengatur kunci ElevenLabs).
  Bagikan hanya ke orang yang dipercaya, dan ganti kunci bila pernah tersebar.
- Panel memakai server bawaan Flask di belakang Nginx: cukup untuk satu pemilik dan beberapa tamu, bukan untuk
  ramai pengunjung. Render memakai CPU VPS.
