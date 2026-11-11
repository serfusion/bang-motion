# Portofolio superfal-dev.com

Situs statis satu halaman: `index.html`, folder `assets/`, dan `cv-naufal-aufa-afaf.pdf`.
Tidak butuh build, database, atau server aplikasi. Tema terang/gelap mengikuti perangkat dan bisa
diganti lewat tombol di pojok kanan atas.

## Memasang di VPS (Nginx)

```bash
sudo apt install -y nginx certbot python3-certbot-nginx
cd ~/bang-motion && git pull
sudo mkdir -p /var/www/superfal-dev
sudo rsync -a --delete projects/portofolio/ /var/www/superfal-dev/
sudo cp projects/portofolio/nginx-superfal-dev.conf /etc/nginx/sites-available/superfal-dev
sudo ln -sf /etc/nginx/sites-available/superfal-dev /etc/nginx/sites-enabled/superfal-dev
sudo nginx -t && sudo systemctl reload nginx
sudo certbot --nginx -d superfal-dev.com -d www.superfal-dev.com
```

DNS: A record `superfal-dev.com` dan `www` diarahkan ke IP VPS. Port 80 dan 443 harus terbuka.

Memperbarui isi: ubah berkas di repo, lalu `git pull` dan jalankan lagi baris `rsync` di atas.

## Pindah domain

Isi situs tidak terikat ke domain. Untuk domain baru: arahkan DNS-nya ke IP VPS, ganti nama di
`server_name` pada `/etc/nginx/sites-available/superfal-dev`, `sudo systemctl reload nginx`, lalu
`sudo certbot --nginx -d domainbaru.com -d www.domainbaru.com`. Ganti juga `superfal-dev.com`
di `index.html` (tag `canonical` dan `og:`), `robots.txt`, dan `sitemap.xml`.

## Mengubah isi

| Bagian | Tempat |
|---|---|
| Teks, pengalaman, proyek, keahlian, kontak | `index.html` (teks biasa, cari judul bagiannya) |
| Foto | `assets/foto.webp` (persegi), `assets/foto-kecil.jpg` (bilah atas) |
| Gambar proyek | `assets/proyek-*.webp`, rasio 16:10 (mis. 1200 × 750) |
| CV PDF | sumber `sumber/cv.html`: buka di Chrome, Cetak → Simpan sebagai PDF, kertas A4, lalu ganti `cv-naufal-aufa-afaf.pdf` |
| Gambar pratinjau tautan (WhatsApp / LinkedIn) | `assets/og.jpg` 1200 × 630, sumbernya `sumber/og.html` |
