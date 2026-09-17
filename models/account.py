"""models/account.py — Model Account (dompet/akun keuangan)."""
from decimal import Decimal

from models import db, generate_uuid, utcnow

VALID_ACCOUNT_TYPES = ("cash", "bank", "ewallet")


class Account(db.Model):
    __tablename__ = "account"

    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    user_id = db.Column(
        db.String(36), db.ForeignKey("user.id"), nullable=False, index=True
    )
    name = db.Column(db.String(100), nullable=False)
    type = db.Column(db.String(20), nullable=False, default="cash")
    balance = db.Column(
        db.Numeric(18, 2), nullable=False, default=Decimal("0.00")
    )

    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow, nullable=False)
    deleted_at = db.Column(db.DateTime, nullable=True)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type,
            "balance": float(self.balance or 0),
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self) -> str:
        return f"<Account {self.name} ({self.type}) balance={self.balance}>"
