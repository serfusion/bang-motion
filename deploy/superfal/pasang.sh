#!/usr/bin/env bash
# Pasang superfal-dev.com di VPS ini:
#   - portofolio statis (projects/portofolio) di https://superfal-dev.com/
#   - Content Creator (panel mesin video, projects/mesin-video) di https://superfal-dev.com/studio/, terkunci
#   - HTTPS Let's Encrypt begitu DNS domain sudah mengarah ke VPS ini
#
#   sudo bash ~/bang-motion/deploy/superfal/pasang.sh                 # pertama kali, dan aman diulang kapan saja
#   sudo bash ~/bang-motion/deploy/superfal/pasang.sh --ganti-kunci   # ganti kunci Content Creator
#
# Kunci Content Creator diketik di sini (tidak tampil di layar) dan disimpan di /etc/superfal/kunci (hanya root),
# diberikan ke panel lewat credential systemd. Kunci tidak pernah ditulis ke repo.
set -euo pipefail

DOMAIN="${DOMAIN:-superfal-dev.com}"
PORT="${PORT:-5000}"
WEB=/var/www/superfal-dev
SINI="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$SINI/../.." && pwd)"
PENGGUNA="${PENGGUNA:-$(stat -c %U "$REPO")}"
KUNCI=/etc/superfal/kunci
LAYANAN=superfal-studio
GANTI_KUNCI=0
for a in "$@"; do [ "$a" = "--ganti-kunci" ] && GANTI_KUNCI=1; done

[ "$(id -u)" = 0 ] || { echo "Jalankan dengan sudo:  sudo bash $0"; exit 1; }
[ "$PENGGUNA" != root ] || { echo "Repo dimiliki root; jalankan dengan PENGGUNA=<nama pengguna biasa>."; exit 1; }
echo "== superfal-dev: repo $REPO (pengguna $PENGGUNA), domain $DOMAIN"

# ---------------------------------------------------------------- 1. paket sistem
PAKET="nginx certbot python3-certbot-nginx rsync dnsutils curl psmisc python3-pip"
if ! dpkg -s $PAKET >/dev/null 2>&1; then
  echo "== memasang paket: $PAKET"
  apt-get update -qq
  DEBIAN_FRONTEND=noninteractive apt-get install -y -qq $PAKET >/dev/null
fi

# ---------------------------------------------------------------- 2. kebutuhan panel (dicek, dipasang bila kurang)
MV="$REPO/projects/mesin-video"
if ! sudo -u "$PENGGUNA" -H python3 -c 'import flask, numpy' 2>/dev/null; then
  echo "== memasang Flask & numpy untuk $PENGGUNA"
  sudo -u "$PENGGUNA" -H python3 -m pip install --user -q -r "$MV/requirements.txt"
fi
NODE="$(sudo -u "$PENGGUNA" -H bash -ic 'command -v node' 2>/dev/null | tail -1 || true)"
[ -n "$NODE" ] || echo "!! node tidak ditemukan untuk $PENGGUNA: render video butuh Node 18+ (lalu: cd $MV && npm install)"
[ -d "$MV/node_modules" ] || echo "!! $MV/node_modules belum ada: jalankan  cd $MV && npm install  (sebagai $PENGGUNA)"
command -v ffmpeg >/dev/null || echo "!! ffmpeg belum ada: sudo apt install ffmpeg rubberband-cli (render butuh ffmpeg)"

# ---------------------------------------------------------------- 3. kunci Content Creator
install -d -m 700 /etc/superfal
if [ ! -s "$KUNCI" ] || [ "$GANTI_KUNCI" = 1 ]; then
  echo "== Kunci Content Creator: sandi yang diketik pengunjung di tab Innovation untuk membuka studio."
  while :; do
    read -rsp "   Kunci baru: " K1; echo
    read -rsp "   Ulangi kunci: " K2; echo
    if [ -z "$K1" ]; then echo "   Kunci tidak boleh kosong."; elif [ "$K1" != "$K2" ]; then echo "   Tidak sama, ulangi."; else break; fi
  done
  ( umask 077; printf '%s' "$K1" > "$KUNCI" )
  unset K1 K2
  echo "   tersimpan di $KUNCI (hanya root). Semua sesi lama otomatis keluar."
fi
chown root:root "$KUNCI"; chmod 600 "$KUNCI"

# ---------------------------------------------------------------- 4. port panel: hentikan panel lama yang dijalankan manual
if systemctl is-active --quiet "$LAYANAN"; then
  JALAN="$(sudo -u "$PENGGUNA" python3 - "$MV/db/konten.db" <<'PY' 2>/dev/null || echo 0
import sqlite3, sys
try:
    print(sqlite3.connect(sys.argv[1]).execute("SELECT COUNT(*) FROM tugas WHERE status='jalan'").fetchone()[0])
except Exception:
    print(0)
PY
)"
  if [ "${JALAN:-0}" != 0 ]; then
    read -rp "!! Ada $JALAN render yang sedang berjalan; studio akan dimulai ulang dan render itu gagal. Lanjut? [y/N] " j
    [ "$j" = y ] || { echo "Dibatalkan. Jalankan lagi setelah render selesai."; exit 1; }
  fi
  systemctl stop "$LAYANAN"
fi
if ss -ltn "( sport = :$PORT )" | grep -q ":$PORT"; then
  echo "!! Port $PORT sudah dipakai (biasanya panel lama yang dijalankan manual untuk SSH tunnel):"
  ss -ltnp "( sport = :$PORT )" | tail -n +2
  read -rp "   Hentikan proses itu sekarang? [y/N] " j
  if [ "$j" = y ]; then fuser -k "$PORT/tcp" || true; sleep 1; else echo "Hentikan dulu (Ctrl+C di terminal panel), lalu jalankan skrip ini lagi."; exit 1; fi
fi

# ---------------------------------------------------------------- 5. layanan systemd untuk panel
UPATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
[ -n "$NODE" ] && UPATH="$(dirname "$NODE"):$UPATH"
sed -e "s|__DOMAIN__|$DOMAIN|g" -e "s|__USER__|$PENGGUNA|g" -e "s|__REPO__|$REPO|g" -e "s|__PORT__|$PORT|g" -e "s|__PATH__|$UPATH|g" \
  "$SINI/superfal-studio.service" > "/etc/systemd/system/$LAYANAN.service"
systemctl daemon-reload
systemctl enable --now "$LAYANAN" >/dev/null 2>&1 || true
systemctl restart "$LAYANAN"

# ---------------------------------------------------------------- 6. portofolio statis (tanpa bahan mentah sumber/)
install -d -m 755 "$WEB"
rsync -a --delete --exclude 'sumber/' --exclude 'README.md' --exclude '*.conf' --exclude '.gitignore' "$REPO/projects/portofolio/" "$WEB/"
chown -R root:root "$WEB"; chmod -R a+rX "$WEB"

# ---------------------------------------------------------------- 7. Nginx
SNIP=/etc/nginx/snippets; install -d "$SNIP"
sed -e "s|__WEB__|$WEB|g" -e "s|__PORT__|$PORT|g" "$SINI/nginx/lokasi.conf" > "$SNIP/superfal-lokasi.conf"
cp "$SINI/nginx/proxy.conf" "$SNIP/superfal-proxy.conf"
CERT="/etc/letsencrypt/live/$DOMAIN/fullchain.pem"
tulis_nginx() {
  if [ -s "$CERT" ]; then
    local nama="$DOMAIN"
    openssl x509 -in "$CERT" -noout -ext subjectAltName 2>/dev/null | grep -q "DNS:www.$DOMAIN" && nama="$DOMAIN www.$DOMAIN"
    sed -e "s|__DOMAIN__|$DOMAIN|g" -e "s|__NAMA__|$nama|g" "$SINI/nginx/https.conf" > /etc/nginx/sites-available/superfal-dev
  else
    sed -e "s|__DOMAIN__|$DOMAIN|g" "$SINI/nginx/http.conf" > /etc/nginx/sites-available/superfal-dev
  fi
  [ -e /proc/net/if_inet6 ] || sed -i '/listen \[::\]/d' /etc/nginx/sites-available/superfal-dev   # VPS tanpa IPv6
  ln -sf /etc/nginx/sites-available/superfal-dev /etc/nginx/sites-enabled/superfal-dev
}
# konfigurasi lain yang memakai nama domain yang sama dimatikan (dicadangkan), supaya tidak bentrok
CAD=/etc/nginx/superfal-cadangan; install -d "$CAD"
for f in /etc/nginx/sites-enabled/* /etc/nginx/conf.d/*.conf; do
  [ -e "$f" ] || continue
  [ "$(basename "$f")" = superfal-dev ] && continue
  if grep -Eq "server_name[^;]*\b$DOMAIN\b" "$f"; then
    echo "   konfigurasi lama $f memakai $DOMAIN: dipindah ke $CAD/"
    mv "$f" "$CAD/$(basename "$f").$(date +%s)"
  fi
done
tulis_nginx
nginx -t -q
systemctl reload nginx || systemctl restart nginx
if command -v ufw >/dev/null && ufw status | grep -q "Status: active"; then ufw allow 'Nginx Full' >/dev/null; fi

# ---------------------------------------------------------------- 8. HTTPS (bila DNS sudah mengarah ke VPS ini)
IP="$(curl -fsS4 --max-time 8 https://api.ipify.org 2>/dev/null || curl -fsS4 --max-time 8 https://ifconfig.me 2>/dev/null || true)"
dns() { dig +short A "$1" @1.1.1.1 2>/dev/null | grep -E '^[0-9.]+$' | tail -1; }
A_APEX="$(dns "$DOMAIN")"; A_WWW="$(dns "www.$DOMAIN")"
PERLU=0
if [ ! -s "$CERT" ]; then PERLU=1
elif [ -n "$IP" ] && [ "$A_WWW" = "$IP" ] && ! openssl x509 -in "$CERT" -noout -ext subjectAltName 2>/dev/null | grep -q "DNS:www.$DOMAIN"; then PERLU=1
fi
if [ "$PERLU" = 1 ]; then
  if [ -n "$IP" ] && [ "$A_APEX" = "$IP" ]; then
    NAMA=(-d "$DOMAIN"); [ "$A_WWW" = "$IP" ] && NAMA+=(-d "www.$DOMAIN")
    SUREL=(--register-unsafely-without-email)
    if [ -z "$(ls -A /etc/letsencrypt/accounts 2>/dev/null)" ]; then
      read -rp "== Email untuk pemberitahuan sertifikat HTTPS (boleh kosong): " em
      [ -n "$em" ] && SUREL=(--email "$em")
    fi
    echo "== meminta sertifikat HTTPS untuk: ${NAMA[*]}"
    if certbot certonly --nginx --non-interactive --agree-tos "${SUREL[@]}" --expand --keep-until-expiring \
         --deploy-hook "systemctl reload nginx" "${NAMA[@]}"; then
      tulis_nginx; nginx -t -q && systemctl reload nginx
    else
      echo "!! Sertifikat gagal. Cek port 80 terbuka di firewall Tencent Cloud, lalu jalankan skrip ini lagi."
    fi
  else
    echo "!! DNS $DOMAIN masih mengarah ke ${A_APEX:-(kosong)}, VPS ini ${IP:-(tidak diketahui)}."
    echo "   Ganti A record di Vercel (lihat deploy/superfal/README.md), tunggu beberapa menit, lalu jalankan skrip ini lagi."
  fi
fi

# ---------------------------------------------------------------- 9. cek
sleep 2
kode() { curl -s -o /dev/null -w '%{http_code}' -H "Host: $DOMAIN" "http://127.0.0.1$1"; }
SKEMA=http; [ -s "$CERT" ] && SKEMA=https
echo
echo "== Selesai"
echo "   panel (layanan $LAYANAN): $(systemctl is-active "$LAYANAN")   | cek lokal: / -> $(kode /)  /studio/masuk -> $(kode /studio/masuk)"
echo "   Portofolio : $SKEMA://$DOMAIN/"
echo "   Studio     : $SKEMA://$DOMAIN/studio/   (atau tab Innovation -> Content Creator -> masukkan kunci)"
echo "   Log panel  : journalctl -u $LAYANAN -f        Perbarui: sudo bash $SINI/perbarui.sh"
[ "$SKEMA" = https ] || echo "   HTTPS belum aktif: arahkan DNS dulu, lalu jalankan skrip ini lagi."
