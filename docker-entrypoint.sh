#!/bin/sh
# Entrypoint production — jalankan migrasi DB sekali sebelum app serve.
#
# Migrasi TIDAK dijalankan saat build (build tidak punya akses DB), tapi di
# sini: saat container start, sebelum gunicorn. Idempoten — aman dijalankan
# setiap restart (no-op bila tak ada migrasi baru).
#
# Set AUTO_MIGRATE=0 untuk melewatinya (mis. saat scale >1 replica agar tidak
# ada dua proses upgrade bersamaan).
set -e

if [ "${AUTO_MIGRATE:-1}" = "1" ]; then
  echo "[entrypoint] Menjalankan migrasi database (flask db upgrade)..."
  flask db upgrade
  echo "[entrypoint] Migrasi selesai."
else
  echo "[entrypoint] AUTO_MIGRATE != 1 — migrasi dilewati."
fi

exec "$@"
