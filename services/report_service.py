"""services/report_service.py — Agregasi dashboard & laporan."""
from datetime import date
from decimal import Decimal
from typing import List

from sqlalchemy import func

from models import db
from models.account import Account
from models.transaction import Transaction
from services.transaction_service import month_range


def current_month() -> str:
    today = date.today()
    return f"{today.year:04d}-{today.month:02d}"


class ReportService:
    """Query agregat — semua perhitungan di database."""

    def total_balance(self, user_id: str) -> Decimal:
        total = (
            db.session.query(func.coalesce(func.sum(Account.balance), 0))
            .filter(Account.user_id == user_id, Account.deleted_at.is_(None))
            .scalar()
        )
        return Decimal(total or 0)

    def cashflow(self, user_id: str, month: str) -> dict:
        """Total pemasukan & pengeluaran satu bulan."""
        start, end = month_range(month)
        rows = (
            db.session.query(
                Transaction.type,
                func.coalesce(func.sum(Transaction.amount), 0),
            )
            .filter(
                Transaction.user_id == user_id,
                Transaction.type.in_(("income", "expense")),
                Transaction.occurred_on >= start,
                Transaction.occurred_on < end,
            )
            .group_by(Transaction.type)
            .all()
        )
        totals = {row[0]: Decimal(row[1] or 0) for row in rows}
        income = totals.get("income", Decimal("0"))
        expense = totals.get("expense", Decimal("0"))
        return {"income": income, "expense": expense, "net": income - expense}

    def recent_transactions(self, user_id: str, limit: int = 8) -> List[Transaction]:
        return (
            Transaction.query
            .filter(Transaction.user_id == user_id)
            .order_by(Transaction.occurred_on.desc(), Transaction.created_at.desc())
            .limit(limit)
            .all()
        )

    def dashboard(self, user_id: str, month: str = None) -> dict:
        month = month or current_month()
        return {
            "month": month,
            "total_balance": self.total_balance(user_id),
            "cashflow": self.cashflow(user_id, month),
            "recent": self.recent_transactions(user_id),
        }
