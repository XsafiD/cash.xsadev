# Rencana Aplikasi Cash Xsadev

status: draft kerja
tanggal: 2026-09-17
stack: Python + Flask + MySQL + Docker

## 1. Latar Belakang

Fitur pencatatan keuangan yang ada sekarang tersebar di banyak aplikasi dan
spesifik per aplikasi. Tujuan proyek ini: **satu aplikasi, semua catatan
keuangan** — self-hosted, satu database, tanpa perlu berpindah aplikasi.

## 2. Keputusan yang Disepakati

| #   | Topik              | Keputusan                                                                                                   |
| --- | ------------------ | ----------------------------------------------------------------------------------------------------------- |
| 1   | User model         | Single-owner dulu (multi-user menyusul)                                                                     |
| 2   | Model transfer     | Opsi (a) — satu `Transaction` `type=transfer` dengan `account_id` (asal) + `account_to_id` (tujuan)         |
| 3   | UI                 | Tailwind + dark mode                                                                                        |
| 4   | Balance            | Di-update real-time di dalam DB transaction (ACID). Audit/rekonsiliasi terjadwal menyusul sebagai hardening |
| 5   | Transaksi berulang | **Bukan** recurring engine. Cukup halaman Perencanaan terpisah (kalkulator, tidak menyentuh ledger)         |
| 6   | Item kebutuhan     | Daftar reusable, terbawa tiap bulan                                                                         |
| 7   | Uang kotor         | Disimpan per bulan (`PlanPeriod`) agar tidak input ulang                                                    |

## 3. Scope

### 3.1 Buku Catatan (core)

- Auth pemilik (session-based)
- Akun/Dompet: cash, bank, e-wallet + saldo berjalan
- Kategori berjenis (pemasukan / pengeluaran)
- Transaksi: masuk, keluar, transfer antar akun
- Dashboard: saldo total, arus kas bulan berjalan
- Laporan: per periode, per kategori

### 3.2 Halaman Perencanaan (terpisah, read-only ke ledger)

- Input **Uang Kotor Bulanan** (per periode, tersimpan)
- Daftar **Item Kebutuhan Bulanan** (reusable)
- 3 card:
  1. Uang Kotor
  2. Total Kebutuhan (Σ item aktif)
  3. **Sisa Uang Dingin** = Uang Kotor − Total Kebutuhan

Halaman ini tidak mengubah saldo maupun transaksi. Saat item jatuh tempo,
user mencatatnya manual di buku catatan.

### 3.3 Belum masuk scope (fase lanjut)

- Multi-user & admin role
- Budget alert & notifikasi
- Utang–piutang
- Import CSV / rekening koran
- Skrip rekonsiliasi saldo + alert developer
- Export laporan

## 4. Arsitektur

Mengikuti `docs/coding-standards/` (controller tipis → service → model):

```
controllers (Blueprint)  →  services (business logic + ACID)  →  models (SQLAlchemy)
templates (Jinja2)       ←  controllers
```

Aturan yang dipegang:

- Controller tidak query ORM langsung — semua lewat service.
- Validasi bisnis di service (`raise ValueError`), controller catch → flash.
- Form di file controller (WTForms) + CSRF.
- Auth via decorator `@login_required` dengan `@wraps`.
- PK UUID string + `created_at` / `updated_at`.
- Soft delete (`deleted_at`) untuk Account & Category.

### Struktur folder

```
config.py
run.py                     # entry point
app.py                     # create_app(), error handlers
models/
  __init__.py              # db, generate_uuid, utcnow
  user.py account.py category.py transaction.py
  plan_item.py plan_period.py
services/
  auth_service.py account_service.py category_service.py
  transaction_service.py plan_service.py report_service.py
controllers/
  decorators.py auth_controller.py dashboard_controller.py
  account_controller.py category_controller.py
  transaction_controller.py plan_controller.py
templates/
  base.html error.html
  components/ auth/ account/ category/ transaction/
  dashboard/ plan/
static/css/style.css static/js/app.js
```

## 5. Skema Data

### user

| kolom                  | tipe               | keterangan                        |
| ---------------------- | ------------------ | --------------------------------- |
| id                     | CHAR(36) PK        | UUID                              |
| username               | VARCHAR(50) unique |                                   |
| password_hash          | VARCHAR(255)       | hash werkzeug, tidak pernah plain |
| created_at, updated_at | DATETIME           |                                   |

### account

| kolom                  | tipe          | keterangan                     |
| ---------------------- | ------------- | ------------------------------ |
| id                     | CHAR(36) PK   |                                |
| user_id                | FK user       |                                |
| name                   | VARCHAR(100)  |                                |
| type                   | VARCHAR(20)   | cash / bank / ewallet          |
| balance                | DECIMAL(18,2) | saldo berjalan, di-update ACID |
| deleted_at             | DATETIME null | soft delete                    |
| created_at, updated_at | DATETIME      |                                |

### category

| kolom                  | tipe          | keterangan       |
| ---------------------- | ------------- | ---------------- |
| id                     | CHAR(36) PK   |                  |
| user_id                | FK user       |                  |
| name                   | VARCHAR(100)  |                  |
| kind                   | VARCHAR(10)   | income / expense |
| deleted_at             | DATETIME null | soft delete      |
| created_at, updated_at | DATETIME      |                  |

### transaction

| kolom                  | tipe              | keterangan                                |
| ---------------------- | ----------------- | ----------------------------------------- |
| id                     | CHAR(36) PK       |                                           |
| user_id                | FK user           |                                           |
| type                   | VARCHAR(10)       | income / expense / transfer               |
| amount                 | DECIMAL(18,2)     | selalu positif                            |
| account_id             | FK account        | income/expense: akun; transfer: akun asal |
| account_to_id          | FK account null   | hanya transfer: akun tujuan               |
| category_id            | FK category null  | income/expense; null untuk transfer       |
| note                   | VARCHAR(255) null |                                           |
| occurred_on            | DATE              | tanggal transaksi                         |
| created_at, updated_at | DATETIME          |                                           |

Aturan validasi:

- `amount > 0`.
- income/expense: `account_id` wajib, `category_id` wajib & `kind` cocok, `account_to_id` null.
- transfer: `account_to_id` wajib, `account_id != account_to_id`, `category_id` null.

### plan_item (reusable)

| kolom                  | tipe              | keterangan     |
| ---------------------- | ----------------- | -------------- |
| id                     | CHAR(36) PK       |                |
| user_id                | FK user           |                |
| name                   | VARCHAR(100)      |                |
| amount                 | DECIMAL(18,2)     |                |
| note                   | VARCHAR(255) null |                |
| position               | INT               | urutan tampil  |
| is_active              | BOOL              | ikut dihitung? |
| created_at, updated_at | DATETIME          |                |

### plan_period

| kolom                  | tipe          | keterangan                 |
| ---------------------- | ------------- | -------------------------- |
| id                     | CHAR(36) PK   |                            |
| user_id                | FK user       |                            |
| period                 | CHAR(7)       | "YYYY-MM", unique per user |
| gross_income           | DECIMAL(18,2) | uang kotor bulanan         |
| created_at, updated_at | DATETIME      |                            |

## 6. Aturan Saldo (ACID)

Semua operasi yang mengubah saldo dibungkus satu transaksi DB:

```
income   : account.balance += amount
expense  : account.balance -= amount
transfer : account_from.balance -= amount ; account_to.balance += amount
```

- `db.session.flush()` untuk menambah row, `db.session.commit()` sekali di akhir.
- Gagal di tengah → `rollback()` → tidak ada partial write.
- Edit/hapus transaksi: saldo lama dikembalikan dulu (reversal), lalu terapkan yang baru, dalam satu commit.
- Reconciliation terjadwal (fase lanjut): bandingkan `account.balance` vs `SUM(transaction)`, kirim alert bila selisih — **tidak pernah menimpa saldo**.

## 7. Mapping Archetype (untuk coding-rules)

| Archetype    | Domain project ini                      |
| ------------ | --------------------------------------- |
| Actor        | `User`                                  |
| AdminRole    | `Admin` (fase multi-user)               |
| Entity       | `Account`, `Category`                   |
| Transaction  | `Transaction`                           |
| Report       | `Dashboard`, `Report`                   |
| Notification | `Reminder`, `BudgetAlert` (fase lanjut) |

## 8. Environment & Operasional

- MySQL dev via `docker-compose.yml` → host `127.0.0.1:3307`, db/user `cashxsadev`.
- Flask service app ditambahkan ke compose saat fase deployment.
- Config env-based (`config.py`), rahasia di `.env` (gitignored).
- **Migrasi skema: Flask-Migrate (Alembic).** `db.create_all()` tidak dipakai lagi —
  satu-satunya sumber skema adalah `migrations/`.
- Perintah harian lewat `Makefile`:

```
make help            # daftar perintah
make dev             # jalankan dev server (port 5000)
make migrate-up      # apply migrasi
make migrate-revision MESSAGE="..."
make migrate-down    # rollback 1 langkah
make seed-owner      # akun owner awal
make mysql-up / mysql-ps / mysql-shell / mysql-logs
```

Catatan: `downgrade()` hasil autogenerate MySQL tidak boleh men-drop index yang
masih dipakai FK — cukup `op.drop_table()` (index & FK ikut terhapus).

## 9. Status & Roadmap

> Fase saat ini: **local development — belum production.** MySQL jalan via Docker,
> Flask via dev server, Tailwind via CDN.

**Sudah selesai:**
- [x] Diskusi & keputusan konsep
- [x] Fondasi: config env-based, application factory, error handler global, CLI
- [x] Model (UUID + timestamps): User, Account, Category, Transaction, PlanItem, PlanPeriod
- [x] Auth single-owner (session + CSRF di semua POST)
- [x] Buku catatan: akun, kategori, transaksi (masuk/keluar/transfer), saldo di-update ACID
- [x] Dashboard ringkasan + filter bulan
- [x] Halaman Perencanaan (3 card kalkulator, terpisah dari ledger)
- [x] Migrasi Alembic (Flask-Migrate) + Makefile
- [x] Tema gelap Tailwind (responsif)

**Belum — fitur berikutnya:**
- [ ] **Laporan terpisah + export (CSV)** ← next
- [ ] Edit transaksi (sekarang hanya catat + hapus)
- [ ] Pagination daftar transaksi
- [ ] Rekonsiliasi saldo terjadwal + alert ke developer
- [ ] Multi-user / admin role
- [ ] Budget alert & notifikasi
- [ ] Utang–piutang
- [ ] Import CSV / rekening koran
- [ ] Hardening production: rate limit login, secure headers, gunicorn,
      compose service app, Tailwind compile (lepas CDN)
