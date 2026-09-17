## Coding Standards (WAJIB)

Standards repo ini: `docs/coding-standards/` (git submodule).

**Aturan konsumsi:**

1. Sebelum menulis/mengubah kode, baca `docs/coding-standards/coding-rules/_INDEX.md`
2. Load HANYA rule file yang relevan dengan topik yang dikerjakan (mis. ubah model → `02-model.md`) — jangan baca semua
3. Istilah di rules pakai archetype (`Actor`, `Entity`, `Transaction`) — map ke domain project ini saat apply. Bila bingung mapping, baca `_GLOSSARY.md`
4. Deep-dive `../reference/` hanya bila rule file dirasa kurang jelas — opsional, bukan default
5. `DEFAULT COPY-PASTE` section di tiap rule = starting point snippet, sesuaikan naming domain

**Mapping archetype project ini:**

| Archetype       | Domain project ini                     |
| --------------- | -------------------------------------- |
| Actor           | `User` (pemilik keuangan, single-owner)|
| AdminRole       | `Admin` (fase multi-user, belum ada)   |
| Entity          | `Account`, `Category`                  |
| Transaction     | `Transaction`                          |
| TransactionLine | — (belum dipakai)                      |
| Report          | `Dashboard` (via `ReportService`)      |
| Notification    | `Reminder`/`BudgetAlert` (fase lanjut) |

Domain aplikasi: **pencatatan keuangan** (buku catatan + halaman Perencanaan
kalkulator terpisah). Rencana lengkap: `docs/2026-09-17 - rencana-cash-xsadev.md`.
