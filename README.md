# Cash Xsadev

Aplikasi pencatatan keuangan self-hosted: **satu aplikasi, semua catatan
keuangan.** Menggabungkan catatan uang masuk/keluar, transfer antar akun, dan
kalkulator perencanaan kebutuhan bulanan dalam satu tempat.

> **Status: local development — belum production.** MySQL berjalan lewat Docker,
> Flask memakai dev server, dan Tailwind dimuat via CDN.

## Fitur

**Buku Catatan**
- Auth single-owner (session + CSRF)
- Akun/dompet: tunai, bank, e-wallet + saldo berjalan
- Kategori berjenis pemasukan / pengeluaran
- Transaksi: masuk, keluar, transfer antar akun
- Saldo diperbarui real-time dalam satu DB transaction (ACID); hapus = reversal
- Dashboard ringkasan + filter bulan

**Halaman Perencanaan** (terpisah, tidak menyentuh saldo)
- Daftar item kebutuhan bulanan yang reusable
- Uang kotor per bulan
- 3 card: Uang Kotor → Total Kebutuhan → Sisa Uang Dingin

## Tech Stack

| Bagian   | Teknologi                          |
| -------- | ---------------------------------- |
| Bahasa   | Python 3.12                        |
| Web      | Flask 3 + Jinja2, WTForms          |
| ORM      | Flask-SQLAlchemy                   |
| Database | MySQL 8 (Docker)                   |
| Migrasi  | Flask-Migrate (Alembic)            |
| UI       | Tailwind CSS (CDN) + dark mode     |

## Struktur

```
app.py            application factory, error handler, CLI
config.py         config env-based (Config / TestConfig / ProductionConfig)
run.py            entry point
models/           User, Account, Category, Transaction, PlanItem, PlanPeriod
services/         business logic + aturan saldo (ACID)
controllers/      Blueprint per domain + decorator auth
templates/        Jinja2 (base.html, components/, per domain)
migrations/       migrasi Alembic
docs/             rencana + coding-standards (submodule)
```

Arsitektur: **controller tipis → service → model**. Controller tidak query ORM
langsung; validasi bisnis di service (`raise ValueError`), controller catch → flash.

## Prasyarat

- Python 3.12
- Docker + Docker Compose

## Setup

```bash
# 1. Virtualenv + dependencies
python3 -m venv venv
venv/bin/pip install -r requirements.txt

# 2. Konfigurasi environment
cp .env.example .env
#    - generate SECRET_KEY:
#      venv/bin/python -c "import secrets; print(secrets.token_hex(32))"
#    - ganti OWNER_USERNAME / OWNER_PASSWORD

# 3. Nyalakan MySQL
make mysql-up

# 4. Apply migrasi
make migrate-up

# 5. Buat akun owner awal
make seed-owner

# 6. Jalankan dev server (http://127.0.0.1:5000)
make dev
```

Login dengan `OWNER_USERNAME` / `OWNER_PASSWORD` dari `.env`
(default: `owner` / `gantipassword` — **wajib diganti**).

## Perintah (Makefile)

```
make help                              # daftar perintah
make dev                               # dev server (port 5000)
make migrate-up                        # apply migrasi
make migrate-revision MESSAGE="..."    # buat file migrasi baru
make migrate-down                      # rollback 1 langkah
make migrate-init                      # setup folder migrations (sekali saja)
make seed-owner                        # akun owner awal
make mysql-up / mysql-down / mysql-ps
make mysql-shell / mysql-logs
```

## Alur Migrasi

`db.create_all()` tidak dipakai — **satu-satunya sumber skema adalah `migrations/`.**

```bash
# setelah mengubah model
make migrate-revision MESSAGE="add tabel x"
make migrate-up
```

Catatan MySQL: `downgrade()` hasil autogenerate tidak boleh men-drop index yang
masih dipakai foreign key — cukup `op.drop_table()` (index & FK ikut terhapus).

## Aturan Saldo

```
income   : account.balance += amount
expense  : account.balance -= amount
transfer : account_from.balance -= amount ; account_to.balance += amount
```

Semua dibungkus satu commit; gagal di tengah → rollback, tidak ada partial write.

## Roadmap

Sudah: fondasi, buku catatan, dashboard, halaman Perencanaan, migrasi Alembic,
tema gelap.

Berikutnya: **laporan + export CSV**, edit transaksi, pagination, rekonsiliasi
saldo + alert, multi-user/admin, budget alert, utang–piutang, import CSV, lalu
hardening production (gunicorn, secure headers, rate limit, Tailwind compile).

Rencana lengkap & keputusan desain: `docs/2026-09-17 - rencana-cash-xsadev.md`.
