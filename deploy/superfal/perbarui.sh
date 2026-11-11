#!/usr/bin/env bash
# Perbarui superfal-dev.com setelah ada perubahan di GitHub: tarik repo, lalu pasang ulang
# (portofolio disalin lagi, studio dimulai ulang, Nginx & HTTPS dicek). Kunci tidak ditanya lagi.
#   sudo bash ~/bang-motion/deploy/superfal/perbarui.sh
set -euo pipefail
SINI="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$SINI/../.." && pwd)"
PENGGUNA="${PENGGUNA:-$(stat -c %U "$REPO")}"
[ "$(id -u)" = 0 ] || { echo "Jalankan dengan sudo:  sudo bash $0"; exit 1; }
echo "== git pull ($REPO)"
if ! sudo -u "$PENGGUNA" -H git -C "$REPO" pull --ff-only; then
  echo "!! git pull gagal. Biasanya karena ada perubahan lokal di VPS (mis. tombol 'Simpan ke JSON' di panel):"
  sudo -u "$PENGGUNA" -H git -C "$REPO" status --short | head -20
  echo "   Simpan dulu perubahan itu (git stash, atau commit lalu push), kemudian jalankan skrip ini lagi."
  exit 1
fi
exec bash "$SINI/pasang.sh" "$@"
