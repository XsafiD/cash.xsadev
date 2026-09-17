"""services/account_service.py — Business logic Account."""
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import func

from models import db
from models.account import Account, VALID_ACCOUNT_TYPES


class AccountService:
    """CRUD + business rules untuk Account."""

    def get_all(self, user_id: str) -> List[Account]:
        return (
            Account.query
            .filter(Account.user_id == user_id, Account.deleted_at.is_(None))
            .order_by(Account.created_at.asc())
            .all()
        )

    def get_by_id(self, user_id: str, account_id: str) -> Optional[Account]:
        return Account.query.filter(
            Account.id == account_id,
            Account.user_id == user_id,
            Account.deleted_at.is_(None),
        ).first()

    def total_balance(self, user_id: str) -> Decimal:
        total = (
            db.session.query(
                func.coalesce(func.sum(Account.balance), 0)
            )
            .filter(Account.user_id == user_id, Account.deleted_at.is_(None))
            .scalar()
        )
        return Decimal(total or 0)

    def create(self, user_id: str, name: str, type: str) -> Account:
        name = (name or "").strip()
        if len(name) < 2:
            raise ValueError("Nama akun minimal 2 karakter")
        if type not in VALID_ACCOUNT_TYPES:
            raise ValueError(
                f"Tipe akun tidak valid. Pilihan: {', '.join(VALID_ACCOUNT_TYPES)}"
            )
        account = Account(user_id=user_id, name=name, type=type,
                          balance=Decimal("0.00"))
        db.session.add(account)
        db.session.commit()
        return account

    def update(self, user_id: str, account_id: str, name: str, type: str) -> Account:
        account = self.get_by_id(user_id, account_id)
        if account is None:
            raise ValueError("Akun tidak ditemukan")
        name = (name or "").strip()
        if len(name) < 2:
            raise ValueError("Nama akun minimal 2 karakter")
        if type not in VALID_ACCOUNT_TYPES:
            raise ValueError(
                f"Tipe akun tidak valid. Pilihan: {', '.join(VALID_ACCOUNT_TYPES)}"
            )
        account.name = name
        account.type = type
        db.session.commit()
        return account

    def delete(self, user_id: str, account_id: str) -> None:
        account = self.get_by_id(user_id, account_id)
        if account is None:
            raise ValueError("Akun tidak ditemukan")
        if account.transaction_list or account.transfer_in_list:
            raise ValueError(
                "Akun punya riwayat transaksi — tidak bisa dihapus. "
                "Ganti nama atau arsipkan bila sudah tidak dipakai."
            )
        from models import utcnow

        account.deleted_at = utcnow()
        db.session.commit()
