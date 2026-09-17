"""models/__init__.py — SQLAlchemy instance + helper bersama."""
import uuid
from datetime import datetime, timezone

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def generate_uuid() -> str:
    """PK UUID string (konsisten lintas tabel)."""
    return str(uuid.uuid4())


def utcnow() -> datetime:
    """Waktu UTC naive — kompatibel kolom DATETIME MySQL."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


# Import di bawah agar semua tabel ter-register saat `models` di-load.
from models.user import User  # noqa: E402,F401
from models.account import Account  # noqa: E402,F401
from models.category import Category  # noqa: E402,F401
from models.transaction import Transaction  # noqa: E402,F401
from models.plan_item import PlanItem  # noqa: E402,F401
from models.plan_period import PlanPeriod  # noqa: E402,F401

__all__ = [
    "db",
    "generate_uuid",
    "utcnow",
    "User",
    "Account",
    "Category",
    "Transaction",
    "PlanItem",
    "PlanPeriod",
]
