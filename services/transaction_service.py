"""services/transaction_service.py — Business logic Transaction + saldo (ACID)."""
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import List, Optional, Tuple

from sqlalchemy import func

from models import db
from models.account import Account
from models.category import Category
from models.transaction import Transaction, VALID_TRANSACTION_TYPES


def month_range(month: str) -> Tuple[date, date]:
    """'YYYY-MM' → (awal bulan, awal bulan berikutnya) — batas [start, end)."""
    year, mon = int(month[:4]), int(month[5:7])
    start = date(year, mon, 1)
    end = date(year + 1, 1, 1) if mon == 12 else date(year, mon + 1, 1)
    return start, end


class TransactionService:
    """Pintu masuk semua mutasi keuangan. Semua perubahan saldo atomic."""

    # ── Query ──
    def get_all(self, user_id: str, filters: Optional[dict] = None):
        query = Transaction.query.filter(Transaction.user_id == user_id)
        filters = filters or {}

        tx_type = filters.get("type")
        if tx_type:
            if tx_type not in VALID_TRANSACTION_TYPES:
                raise ValueError("Tipe transaksi tidak valid")
            query = query.filter(Transaction.type == tx_type)

        month = filters.get("month")
        if month:
            start, end = month_range(month)
            query = query.filter(
                Transaction.occurred_on >= start, Transaction.occurred_on < end
            )

        account_id = filters.get("account_id")
        if account_id:
            query = query.filter(Transaction.account_id == account_id)

        return query.order_by(
            Transaction.occurred_on.desc(), Transaction.created_at.desc()
        ).all()

    def get_by_id(self, user_id: str, transaction_id: str) -> Optional[Transaction]:
        return Transaction.query.filter(
            Transaction.id == transaction_id, Transaction.user_id == user_id
        ).first()

    def total_by_type(self, user_id: str, tx_type: str, month: str) -> Decimal:
        start, end = month_range(month)
        total = (
            db.session.query(func.coalesce(func.sum(Transaction.amount), 0))
            .filter(
                Transaction.user_id == user_id,
                Transaction.type == tx_type,
                Transaction.occurred_on >= start,
                Transaction.occurred_on < end,
            )
            .scalar()
        )
        return Decimal(total or 0)

    # ── Mutasi ──
    def create(
        self,
        user_id: str,
        type: str,
        amount,
        account_id: str,
        category_id: Optional[str] = None,
        account_to_id: Optional[str] = None,
        note: Optional[str] = None,
        occurred_on: Optional[date] = None,
    ) -> Transaction:
        """Buat transaksi + terapkan efeknya ke saldo dalam satu commit."""
        amount = self._parse_amount(amount)
        account, account_to, category = self._resolve(
            user_id, type, account_id, category_id, account_to_id
        )
        transaction = Transaction(
            user_id=user_id,
            type=type,
            amount=amount,
            account_id=account.id,
            account_to_id=account_to.id if account_to else None,
            category_id=category.id if category else None,
            note=(note or "").strip() or None,
            occurred_on=occurred_on or date.today(),
        )
        try:
            db.session.add(transaction)
            db.session.flush()
            self._apply_balance(account, account_to, type, amount, sign=1)
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise
        return transaction

    def delete(self, user_id: str, transaction_id: str) -> None:
        """Hapus transaksi + kembalikan efeknya ke saldo (reversal)."""
        transaction = self.get_by_id(user_id, transaction_id)
        if transaction is None:
            raise ValueError("Transaksi tidak ditemukan")
        try:
            self._apply_balance(
                transaction.account,
                transaction.account_to,
                transaction.type,
                transaction.amount,
                sign=-1,
            )
            db.session.delete(transaction)
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise

    # ── Internal ──
    @staticmethod
    def _parse_amount(amount) -> Decimal:
        try:
            value = Decimal(str(amount))
        except (InvalidOperation, TypeError):
            raise ValueError("Nominal tidak valid")
        if value <= 0:
            raise ValueError("Nominal harus lebih dari 0")
        return value.quantize(Decimal("0.01"))

    @staticmethod
    def _get_account(user_id: str, account_id: Optional[str]) -> Optional[Account]:
        if not account_id:
            return None
        return Account.query.filter(
            Account.id == account_id,
            Account.user_id == user_id,
            Account.deleted_at.is_(None),
        ).first()

    def _resolve(self, user_id, type, account_id, category_id, account_to_id):
        if type not in VALID_TRANSACTION_TYPES:
            raise ValueError(
                f"Tipe transaksi tidak valid. Pilihan: {', '.join(VALID_TRANSACTION_TYPES)}"
            )

        account = self._get_account(user_id, account_id)
        if account is None:
            raise ValueError("Akun tidak ditemukan")

        if type in ("income", "expense"):
            if account_to_id:
                raise ValueError("Transaksi masuk/keluar tidak punya akun tujuan")
            category = Category.query.filter(
                Category.id == category_id,
                Category.user_id == user_id,
                Category.deleted_at.is_(None),
            ).first()
            if category is None:
                raise ValueError("Kategori wajib dipilih")
            if category.kind != type:
                jenis = "pemasukan" if type == "income" else "pengeluaran"
                raise ValueError(f"Kategori harus berjenis {jenis}")
            return account, None, category

        if not account_to_id:
            raise ValueError("Transfer wajib punya akun tujuan")
        if account_to_id == account_id:
            raise ValueError("Akun asal dan tujuan tidak boleh sama")
        account_to = self._get_account(user_id, account_to_id)
        if account_to is None:
            raise ValueError("Akun tujuan tidak ditemukan")
        return account, account_to, None

    @staticmethod
    def _apply_balance(account, account_to, type, amount, sign: int) -> None:
        delta = Decimal(amount) * sign
        if type == "income":
            account.balance = Decimal(account.balance) + delta
        elif type == "expense":
            account.balance = Decimal(account.balance) - delta
        elif type == "transfer":
            account.balance = Decimal(account.balance) - delta
            account_to.balance = Decimal(account_to.balance) + delta
